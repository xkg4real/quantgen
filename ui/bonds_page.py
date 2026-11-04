"""Bonds — calculator & risk, curve scenarios, futures hedge.

One bullet bond, described by coupon / maturity / frequency and quoted by
price or yield. The curve behind the key-rate DV01s, the z-spread, carry/roll
and the scenarios is the latest UST par curve from FRED (keyless), bootstrapped
as-is; when FRED cannot answer, the page runs on a loudly flagged synthetic
curve so every control works with zero keys. Percent and basis-point
formatting happens here and nowhere else — the core speaks decimals.

Inputs are parsed once, on the click: a Run never reads a field again, each Run
takes a token and only the newest Run may paint (result or error), and any edit
after a Run marks the result as belonging to the previous inputs.
"""
from __future__ import annotations

import math
import re
import threading
from typing import Callable, Optional

import flet as ft

from core.ficc import insights
from core.ficc.bonds import (Bond, analyze_bond, futures_hedge_ratio, round_contracts,
                             scenario_pnl, yield_from_price)
from core.ficc.common import FICCError, bp_text, pct_text, tenor_label
from core.ficc.curves import curve_from_snapshot
from core.ficc.data import load_treasury_curve
from core.theme import RADII, active
from ui import fcharts
from ui.ai_panel import analysis_panel
from ui.components import card, chip, empty_state, notice, section, stat

_TOOLS = [("calc", "Calculator & risk"), ("scenarios", "Scenarios"),
          ("hedge", "Futures hedge")]
_SOURCES = [("auto", "Auto (FRED, else synthetic)"), ("fred", "FRED"),
            ("synthetic", "Synthetic demo")]
_FREQS = [("1", "Annual"), ("2", "Semi-annual"), ("4", "Quarterly")]
_MAX_MATURITY = 100.0              # years; longer is a typo, and the schedule grows with T·freq
_YIELD_PCT = (-50.0, 200.0)        # yield_from_price's bracket [-0.5, 2.0], in the percent typed;
                                   # the z-spread bracket binds first for deep negative yields
                                   # (below about -33% to -45%, by frequency and curve)
# Digits with optional thousands groups of exactly three, a decimal point, an exponent:
# '1,000,000' is a number, '4,5' is not (it was read as 45).
_NUM_RE = re.compile(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d*)?(?:[eE][+-]?\d+)?")
STALE_TEXT = "Inputs changed since this result was computed. Press Run to refresh it."


def _money(x: float, *, signed: bool = False) -> str:
    return f"{x:{'+' if signed else ''},.0f}"


def _dv01_text(x: float) -> str:
    """Whole currency units, two decimals below 100 so a small book never reads 0."""
    return _money(x) if abs(x) >= 100 else f"{x:,.2f}"


def _qty(x: float) -> str:
    """A per-contract DV01, shown so the formula can be redone from the screen."""
    return f"{x:,.2f}" if 1.0 <= abs(x) < 1e9 else f"{x:.4g}"


class _FieldError(ValueError):
    """An input the page refuses before computing; `fields` show `msg` underneath."""

    def __init__(self, fields, msg: str, text: str = "") -> None:
        fields = tuple(fields) if isinstance(fields, (list, tuple)) else (fields,)
        super().__init__(text or f"{fields[0].label}: {msg}")
        self.fields, self.msg = fields, msg


def _num(field: ft.TextField, default: Optional[float] = None, *, required: bool = False,
         gt: Optional[float] = None, ge: Optional[float] = None,
         le: Optional[float] = None) -> Optional[float]:
    """Blank -> `default`, or a field error when `required`. A comma is only a
    thousands separator. Unparsable, non-finite or out-of-range input raises a
    _FieldError naming the field, in the units and text the user typed."""
    raw = (field.value or "").strip()
    if not raw:
        if required:
            raise _FieldError(field, "required.")
        return default
    v = float("nan")
    if _NUM_RE.fullmatch(raw):
        try:
            v = float(raw.replace(",", ""))
        except ValueError:
            pass
    if not math.isfinite(v):                      # 'abc', 'nan', 'inf', '1e400', '4,5', '1_000'
        raise _FieldError(field, f"{raw!r} is not a number.")
    need = [(v > b, f"> {b:g}") for b in (gt,) if b is not None]
    need += [(v >= b, f">= {b:g}") for b in (ge,) if b is not None]
    need += [(v <= b, f"<= {b:g}") for b in (le,) if b is not None]
    if not all(ok for ok, _ in need):
        raise _FieldError(field, f"must be {' and '.join(r for _, r in need)}, got {raw}.")
    return v + 0.0                                # '-0' -> 0.0, never '-0.000%'


def _shock_text(shock) -> str:
    """Every key tenor with one decimal (the fly's -12.5 is not '-12'), in bp."""
    if isinstance(shock, (int, float)):
        return f"{shock:+.1f} at every tenor"
    return " / ".join(f"{tenor_label(t)} {shock[t]:+.1f}" for t in sorted(shock))


def build_bonds_page(page: ft.Page,
                     on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()

    coupon = ft.TextField(label="Coupon %", width=110, value="4.50",
                          border_radius=RADII["md"])
    maturity = ft.TextField(label="Maturity (years)", width=140, value="10",
                            border_radius=RADII["md"])
    freq = ft.Dropdown(label="Coupons / year", width=150, value="2",
                       options=[ft.dropdown.Option(k, v) for k, v in _FREQS])
    price = ft.TextField(label="Price (per 100)", width=140, helper="blank = from yield",
                         border_radius=RADII["md"])
    ytm = ft.TextField(label="Yield %", width=120, value="4.50", helper="blank = from price",
                       border_radius=RADII["md"])
    notional = ft.TextField(label="Notional", width=140, value="1000000",
                            border_radius=RADII["md"])
    source = ft.Dropdown(label="Curve source", width=240, value="auto",
                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
    ctd_dv01 = ft.TextField(label="CTD DV01 / contract", width=170, value="65",
                            hint_text="per bp, per contract", border_radius=RADII["md"],
                            tooltip="Your input, not market data: the CTD's DV01 in currency "
                                    "per bp for one contract's face (e.g. $100,000 for ZN/ZF/ZB, "
                                    "$200,000 for ZT).")
    cf = ft.TextField(label="Conversion factor", width=150, value="0.8",
                      border_radius=RADII["md"],
                      tooltip="Your input, not market data: the exchange's conversion factor "
                              "of the cheapest-to-deliver issue.")
    pos_dv01 = ft.TextField(label="Position DV01 (blank = calculator)", width=250,
                            border_radius=RADII["md"],
                            tooltip="Currency per bp; negative for a short position.")
    hedge_row = ft.Row([ctd_dv01, cf, pos_dv01], spacing=10, wrap=True, visible=False)
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    result_host = ft.Column(spacing=14)
    stale = notice(STALE_TEXT, "warning", icon=ft.Icons.HISTORY)
    stale.visible = False
    lock = threading.Lock()
    state = {"run": 0, "raw": None}     # newest Run's token; raw inputs of the shown result
    fields = (coupon, maturity, price, ytm, notional, ctd_dv01, cf, pos_dv01)

    def _raw() -> tuple:
        return tuple(c.value for c in (tool, coupon, maturity, freq, price, ytm, notional,
                                       source, ctd_dv01, cf, pos_dv01))

    def on_input(e=None) -> None:
        ctl = getattr(e, "control", None)
        if ctl is not None and getattr(ctl, "error", None):
            ctl.error = None                      # the user is fixing that field
            if ctl is price or ctl is ytm:        # the pair error belongs to both fields
                price.error = ytm.error = None    # (identity: Flet controls compare by value)
        with lock:
            stale.visible = state["raw"] is not None and _raw() != state["raw"]
        page.update()

    def on_tool(e=None) -> None:
        hedge_row.visible = tool.value == "hedge"
        on_input(e)

    tool = ft.Dropdown(label="Tool", width=200, value="calc", on_select=on_tool,
                       options=[ft.dropdown.Option(k, v) for k, v in _TOOLS])
    freq.on_select = on_input
    source.on_select = on_input
    for f in fields:
        f.on_change = on_input

    def _snapshot() -> dict:
        """Every input parsed once, on the click."""
        kind, src = tool.value or "calc", source.value or "auto"
        bond = Bond(coupon=_num(coupon, required=True, ge=0.0) / 100.0,
                    maturity=_num(maturity, required=True, gt=0.0, le=_MAX_MATURITY),
                    freq=int(freq.value or "2"), notional=_num(notional, required=True, gt=0.0))
        has_px, has_y = bool((price.value or "").strip()), bool((ytm.value or "").strip())
        if has_px == has_y:
            raise _FieldError(
                (price, ytm), "Fill only one of Price and Yield." if has_px else
                "Fill Price or Yield.",
                "Fill exactly one of Price (per 100) and Yield %: " + (
                    "both are filled. Clear one; the blank one is computed from the other."
                    if has_px else "both are blank."))
        px = _num(price, gt=0.0) if has_px else None
        y = _num(ytm, gt=_YIELD_PCT[0], le=_YIELD_PCT[1]) if has_y else None
        hedge = None
        if kind == "hedge":
            hedge = (_num(pos_dv01), _num(ctd_dv01, required=True, gt=0.0),
                     _num(cf, required=True, gt=0.0))
        return {"kind": kind, "source": src, "bond": bond, "price": px, "ytm": y,
                "hedge": hedge, "raw": _raw()}

    def _echo(inp: dict, served: str = "") -> str:
        """The inputs as parsed (12 significant digits, so 99.1234567 is not shown as 99.1235),
        the curve source asked for and, once known, the one actually used."""
        b = inp["bond"]
        quote = (f"price {inp['price']:.12g} (yield computed)" if inp["price"] is not None
                 else f"yield {inp['ytm']:.12g}% (price computed)")
        parts = [dict(_TOOLS)[inp["kind"]], f"coupon {b.coupon * 100:.12g}%",
                 f"maturity {b.maturity:.12g}y", f"{b.freq}x coupons", quote,
                 f"notional {_money(b.notional)}",
                 f"curve requested {dict(_SOURCES)[inp['source']]}"]
        if served:
            parts.append(f"served {served}")
        if inp["hedge"] is not None:
            pos, ctd, c = inp["hedge"]
            parts += ["position DV01 " + ("from the calculator" if pos is None
                                          else f"{pos:,.2f} (override)"),
                      f"CTD DV01 {_qty(ctd)}", f"CF {c:.4f}"]
        return "Computed for: " + " · ".join(parts)

    def run(e=None) -> None:
        for f in fields:
            f.error = None
        with lock:
            state["run"] += 1
            me = state["run"]
        try:
            inp = _snapshot()
        except ValueError as exc:                 # a _FieldError also flags its fields
            for f in getattr(exc, "fields", ()):
                f.error = exc.msg
            with lock:
                state["raw"], stale.visible, busy.visible = None, False, False
                result_host.controls = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]
            page.update()
            return
        with lock:
            state["raw"], stale.visible, busy.visible = inp["raw"], False, True
            result_host.controls = []
        page.update()

        def paint(controls: list) -> None:
            with lock:
                if me != state["run"]:            # a newer Run owns the screen
                    return
                stale.visible = _raw() != inp["raw"]          # edited while this ran
                result_host.controls = [stale] + controls
                busy.visible = False
            page.update()

        def fail(text: str) -> None:
            paint([notice(text, "error", icon=ft.Icons.ERROR_OUTLINE)])

        def worker():
            kind, bond = inp["kind"], inp["bond"]
            try:
                panel = load_treasury_curve(source=inp["source"])
                snap = panel.latest()
                curve = curve_from_snapshot(snap)
                y = inp["ytm"]
                try:
                    a = analyze_bond(bond, price=inp["price"],
                                     ytm=None if y is None else y / 100.0, curve=curve)
                except FICCError as exc:
                    if "z-spread" not in str(exc):
                        raise
                    q = (f"Yield % {y:.12g}" if y is not None
                         else f"Price (per 100) {inp['price']:.12g}")
                    raise FICCError(
                        f"{q} is too far from the {curve.source} curve for a z-spread in "
                        f"[-50%, 200%] (continuous, over the curve's zero rates), so the bond "
                        f"cannot be analysed on this curve. {exc}") from exc
                rows = scenario_pnl(bond, curve, a.price) if kind == "scenarios" else None
                hedge = None
                if kind == "hedge":
                    pos_in, ctd, c = inp["hedge"]
                    pos = a.dv01 if pos_in is None else pos_in
                    hedge = (pos, ctd, c, futures_hedge_ratio(pos, ctd, c))
                cr = a.carry_roll
                synthetic = panel.source == "SYNTHETIC"
                src_tag = (f"SYNTHETIC (simulated, dated {curve.date})" if synthetic
                           else f"{curve.source}, newest obs {curve.date}")
                echo = _echo(inp, src_tag)
                blocks: list[ft.Control] = [
                    ft.Text(echo, size=11, color=pal.muted, selectable=True)]
                if synthetic:
                    blocks.append(notice("Synthetic data: " + panel.note, "error",
                                         icon=ft.Icons.SCIENCE_OUTLINED))
                elif panel.note:
                    blocks.append(notice("Curve check: " + panel.note, "warning",
                                         icon=ft.Icons.WARNING_AMBER_ROUNDED))
                if bond.maturity > curve.tenors[-1] + 1e-9:
                    blocks.append(notice(
                        f"Maturity {bond.maturity:g}y is beyond the longest curve tenor "
                        f"({tenor_label(curve.tenors[-1])}): zero rates are held flat beyond it.",
                        "warning", icon=ft.Icons.WARNING_AMBER_ROUNDED))
                blocks.append(ft.Row([
                    chip(f"curve: {src_tag}",
                         "error" if synthetic else ("warning" if panel.note else "success")),
                    chip(f"{curve.method} (log-linear DF), {len(curve.tenors)} tenors "
                         f"{tenor_label(curve.tenors[0])}-{tenor_label(curve.tenors[-1])}"),
                    chip(f"{bond.freq}x coupons"),
                    chip(f"notional {_money(bond.notional)}"),
                ], spacing=6, wrap=True))
                blocks.append(ft.Row([
                    stat("Price", f"{a.price:.3f}",
                         tooltip="Full (dirty) PV per 100: no settlement date, no accrued split"),
                    stat("Yield", pct_text(a.ytm, decimals=3),
                         tooltip=f"Compounded {bond.freq}x a year"),
                    stat("Macaulay", f"{a.macaulay:.2f}y"),
                    stat("Modified", f"{a.modified:.2f}", tooltip="Years"),
                    stat("Convexity", f"{a.convexity:.1f}", tooltip="Years squared"),
                    stat("DV01", _dv01_text(a.dv01),
                         tooltip="Currency per bp of this bond's own yield, positive for a long"),
                    stat("z-spread", bp_text(a.z_spread),
                         tooltip=f"Continuous, over the curve's zero rates; curve price "
                                 f"{a.curve_price:.3f}"),
                ], spacing=10, wrap=True))
                narrative = insights.narrate_bond(a, rows) + (
                    f" The curve is SYNTHETIC (simulated, dated {curve.date}): z-spread, "
                    "carry/roll, key-rate DV01s and scenarios describe the generator, not the "
                    "market." if synthetic else
                    f" Curve: {curve.source} UST par curve, newest observation {curve.date}."
                    + (f" {panel.note}" if panel.note else ""))
                be_ok = math.isfinite(cr.breakeven_bp)
                payload = {
                    "tool": kind, "data_source": panel.source, "inputs": echo,
                    "bond": {"coupon": bond.coupon, "maturity": bond.maturity, "freq": bond.freq,
                             "notional": bond.notional},
                    "curve": {"source": curve.source, "date": curve.date, "method": curve.method,
                              "note": panel.note,
                              "par_yields": {tenor_label(t): v for t, v in
                                             zip(snap.tenors, snap.par_yields)}},
                    "price": a.price, "ytm": a.ytm, "macaulay": a.macaulay, "modified": a.modified,
                    "convexity": a.convexity, "dv01": a.dv01, "z_spread": a.z_spread,
                    "curve_price": a.curve_price,
                    "krd": {tenor_label(t): v for t, v in a.krd.items()},
                    "carry_roll": {"horizon": cr.horizon, "carry": cr.carry,
                                   "rolldown": cr.rolldown, "total": cr.total,
                                   "breakeven_bp": cr.breakeven_bp if be_ok else None},
                }
                if kind == "calc":
                    blocks.append(ft.Row([
                        stat(f"Carry ({tenor_label(cr.horizon)})", f"{cr.carry:+.3f}",
                             token="success" if cr.carry >= 0 else "error",
                             tooltip="Per 100 over the horizon, not annualised"),
                        stat("Roll-down", f"{cr.rolldown:+.3f}",
                             token="success" if cr.rolldown >= 0 else "error"),
                        stat("Carry + roll", f"{cr.total:+.3f}",
                             token="success" if cr.total >= 0 else "error"),
                        stat("Breakeven", f"{cr.breakeven_bp:+.1f}bp" if be_ok else "n/a",
                             tooltip=("Matures inside the horizon: held to maturity, no yield "
                                      "move changes the result" if not be_ok else
                                      "Parallel yield rise that wipes out carry + roll"
                                      if cr.total >= 0 else
                                      "Carry + roll is negative: yields must fall this much to "
                                      "break even")),
                    ], spacing=10, wrap=True))
                    blocks.append(card(fcharts.price_yield_chart(bond, a.ytm)))
                    blocks.append(card(fcharts.krd_chart(
                        a.krd, title=f"Zero-curve key-rate DV01 (z-spread {bp_text(a.z_spread)} "
                                     f"held)")))
                elif kind == "scenarios":
                    worst, best = min(rows, key=lambda r: r.pnl), max(rows, key=lambda r: r.pnl)
                    blocks.append(ft.Row([
                        stat("Worst", f"{worst.name}: {_money(worst.pnl, signed=True)}",
                             token="error"),
                        stat("Best", f"{best.name}: {_money(best.pnl, signed=True)}",
                             token="success"),
                    ], spacing=10, wrap=True))
                    blocks.append(card(fcharts.scenario_chart(rows)))
                    table = ft.DataTable(
                        columns=[ft.DataColumn(ft.Text(h, size=11)) for h in
                                 ("Scenario", "Shock (bp, cc zero rates)", "New price", "P&L",
                                  "P&L % of MV")],
                        rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(v, size=11)) for v in (
                            r.name, _shock_text(r.shock_bp), f"{r.new_price:.3f}",
                            _money(r.pnl, signed=True), f"{r.pnl_pct * 100:+.2f}%")])
                            for r in rows],
                        column_spacing=18, heading_row_height=34, data_row_max_height=34,
                    )
                    blocks.append(ft.Row([table], scroll=ft.ScrollMode.AUTO))
                    r100 = next((r for r in rows if r.name == "+100bp parallel"), None)
                    try:                          # the +100bp row's price, read back as a yield
                        dy = (yield_from_price(bond, r100.new_price) - a.ytm) * 1e4
                        moved = (f"on this curve the +100bp row moves its yield by "
                                 f"{dy:+.1f}bp (")
                    except (AttributeError, FICCError, ValueError):
                        moved = "("
                    blocks.append(notice(
                        "Shocks move the curve's continuously-compounded zero rates with the "
                        "z-spread held, not this bond's yield: " + moved +
                        f"+{(bond.freq + a.ytm) * (math.exp(0.01 / bond.freq) - 1) * 1e4:.1f}bp on a "
                        "curve flat at this yield, (f + y)(e^(0.01/f) - 1)); convexity then trims "
                        "losses and adds to gains. "
                        "The fly is a key-rate "
                        "fly: -12.5bp at 2y and 10y, +25bp at 5y, 0 at the other key tenors. "
                        "P&L = (new price - price) x notional / 100; P&L % is of market value "
                        "(price x notional / 100), not of notional.", "muted",
                        icon=ft.Icons.INFO_OUTLINE))
                    payload["scenarios"] = [{"name": r.name, "shock_bp": _shock_text(r.shock_bp),
                                             "new_price": r.new_price, "pnl": r.pnl,
                                             "pnl_pct": r.pnl_pct} for r in rows]
                else:
                    pos, ctd, c, n = hedge
                    fut, k = ctd / c, round_contracts(n)
                    resid = pos - k * fut
                    side = "sell" if n >= 0 else "buy"
                    how = ("flat" if abs(resid) < 0.005 else
                           "under-hedged" if resid * pos > 0 else "over-hedged")
                    override = inp["hedge"][0] is not None
                    blocks.append(ft.Row([
                        stat("Position DV01 (override)" if override else
                             "Position DV01 (calculator)", f"{pos:,.2f}",
                             tooltip="Typed in Position DV01, else the calculator's DV01; "
                                     "negative = short"),
                        stat("CTD DV01 / contract", _qty(ctd)),
                        stat("Conversion factor", f"{c:.4f}"),
                        stat("Futures DV01", _qty(fut), tooltip="CTD DV01 / CF"),
                        stat(f"Contracts to {side}", f"{abs(n):,.2f}", token="accent"),
                        stat("Rounded", f"{abs(k):,d}",
                             tooltip="Nearest whole contract; halves round away from zero"),
                        stat("Net DV01 after hedge", f"{resid:+,.2f}",
                             tooltip="Position DV01 - rounded x futures DV01 (per bp): positive "
                                     "= still net long duration"),
                    ], spacing=10, wrap=True))
                    blocks.append(notice(
                        f"contracts = position DV01 x CF / CTD DV01 = {pos:,.2f} x {c:.4f} / "
                        f"{_qty(ctd)} = {n:,.2f}: {side} {abs(k):,d}. Net DV01 after the hedge "
                        f"is {resid:+,.2f} per bp ({how}). A DV01 approximation: futures DV01 = "
                        f"CTD DV01 / CF, with CTD DV01 per contract face; CTD and CF are your "
                        f"inputs, not market data; CTD switches, basis, delivery options, "
                        f"invoice price and yield beta are not modelled.", "muted",
                        icon=ft.Icons.INFO_OUTLINE))
                    if override and abs(pos - a.dv01) > 0.01 * abs(a.dv01):
                        blocks.append(notice(
                            f"Position DV01 {pos:,.2f} is your override; this bond's calculator "
                            f"DV01 is {a.dv01:,.2f}. The hedge is sized on the override.",
                            "warning", icon=ft.Icons.WARNING_AMBER_ROUNDED))
                    if not (0.1 <= c <= 2.0 and 5.0 <= fut <= 1000.0):
                        blocks.append(notice(
                            f"Check the units: futures DV01 {_qty(fut)} per contract and CF "
                            f"{c:g} look unusual. A rough guide, not exchange data: a CF outside "
                            f"0.1-2 or a futures DV01 outside 5-1000 per contract usually means "
                            f"a per-100 input instead of one contract's face; CTD DV01 is per bp "
                            f"for one contract's face.",
                            "warning", icon=ft.Icons.WARNING_AMBER_ROUNDED))
                    narrative += (f" Hedging {pos:,.2f} per bp of DV01 with a future whose CTD "
                                  f"has DV01 {_qty(ctd)} per contract and conversion factor "
                                  f"{c:.4f} takes {abs(n):,.2f} contracts to {side} "
                                  f"({abs(k):,d} rounded, net DV01 {resid:+,.2f} per bp, {how}).")
                    payload["hedge"] = {"position_dv01": pos, "position_dv01_override": override,
                                        "ctd_dv01_per_contract": ctd, "conversion_factor": c,
                                        "futures_dv01": fut, "contracts": n, "side": side,
                                        "rounded": k, "net_dv01_after_hedge": resid}
                blocks.append(notice(
                    f"Conventions: price is the full PV per 100 of coupons paid every 1/{bond.freq} "
                    "year counted back from maturity (no settlement date; a clean quote plus "
                    "accrued interest is not supported); maturity in ACT/365F years; yield "
                    f"compounds {bond.freq}x a year; z-spread and curve zeros are continuous; "
                    "DV01 moves this bond's own yield by 1bp, key-rate DV01s move zero rates.",
                    "muted", icon=ft.Icons.RULE))
                if a.note:
                    blocks.append(notice(a.note, "muted", icon=ft.Icons.INFO_OUTLINE))
                blocks.append(analysis_panel(page, kind=f"bond_{kind}", narrative=narrative,
                                             payload_fn=lambda p=payload: p))
                paint(blocks)
            except (FICCError, ValueError) as exc:
                fail(str(exc))
            except Exception as exc:
                fail(f"{type(exc).__name__}: {exc}")

        page.run_thread(worker)

    result_host.controls = [empty_state(
        "Describe a bond and press Run",
        "Quote it by price or by yield: fill exactly one of Price (per 100) and Yield %; the "
        "blank one is computed. The curve comes from FRED without a key; without a "
        "connection the page runs on a labeled synthetic curve.",
        icon=ft.Icons.REQUEST_QUOTE_OUTLINED)]

    return ft.Column([
        section("Bonds", subtitle="Price, yield, duration and convexity; key-rate DV01s, "
                                  "z-spread and carry/roll off the UST curve; curve "
                                  "scenarios; a Treasury-futures hedge."),
        ft.Row([tool, coupon, maturity, freq, price, ytm, notional, source,
                ft.Button("Run", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy],
               spacing=10, wrap=True, vertical_alignment=ft.CrossAxisAlignment.START),
        hedge_row,
        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=14, expand=True)


# --------------------------------------------------------------------------- #
# Self-check: drive the page with a stand-in for ft.Page, synthetic curve only.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from types import SimpleNamespace

    def walk(c):
        yield c
        for attr in ("controls", "rows", "cells", "columns"):
            for child in getattr(c, attr, None) or []:
                yield from walk(child)
        for attr in ("content", "label"):
            child = getattr(c, attr, None)
            if child is not None and not isinstance(child, str):
                yield from walk(child)

    fake = SimpleNamespace(run_thread=lambda fn: fn(), update=lambda: None)
    root = build_bonds_page(fake)
    controls = list(walk(root))
    dd = {d.label: d for d in controls if isinstance(d, ft.Dropdown)}
    tf = {t.label: t for t in controls if isinstance(t, ft.TextField)}
    run_btn = next(b for b in controls if isinstance(b, ft.Button))
    dd["Curve source"].value = "synthetic"

    def texts() -> list[str]:
        return [t.value for t in walk(root) if isinstance(t, ft.Text) and t.value]

    for kind, n_img in (("calc", 2), ("scenarios", 1), ("hedge", 0)):
        dd["Tool"].value = kind
        run_btn.on_click(None)
        found = texts()
        assert not any(t.startswith(("ValueError", "FICCError", "TypeError")) for t in found), \
            (kind, found[:3])
        assert "DV01" in found and any(t.startswith("Synthetic data") for t in found), kind
        assert sum(isinstance(c, ft.Image) for c in walk(root)) == n_img, kind
        assert any(t.startswith("Analysis") for t in found), kind
    assert any(t.startswith("Contracts to sell") for t in texts())
    assert "Net DV01 after hedge" in texts() and "-14.31" in texts()   # 798.19 - 10 x 81.25
    assert any(isinstance(c, ft.DataTable) for c in walk(root)) is False   # hedge has no table

    dd["Tool"].value = "scenarios"
    run_btn.on_click(None)
    assert any(isinstance(c, ft.DataTable) for c in walk(root))
    assert any(t == "2y-5y-10y fly" for t in texts())

    tf["Price (per 100)"].value = "98"                    # both price and yield -> error
    run_btn.on_click(None)
    assert any("exactly one" in t for t in texts())
    tf["Yield %"].value = ""
    tf["Coupon %"].value = "abc"
    run_btn.on_click(None)
    assert any("Coupon %" in t and "not a number" in t for t in texts())
    tf["Coupon %"].value = "4"
    dd["Tool"].value = "calc"
    run_btn.on_click(None)
    assert "98.000" in texts() and "DV01" in texts()

    ring = next(c for c in controls if isinstance(c, ft.ProgressRing))
    for bad in ("nan", "inf", "1e400"):             # non-finite -> notice, not an exception
        tf["Notional"].value = bad
        run_btn.on_click(None)
        assert any("Notional" in t and "not a number" in t for t in texts()), bad
        assert ring.visible is False
    tf["Notional"].value = "1000000"

    def boom(*a, **k):                              # render helper failure -> same notice path
        raise RuntimeError("chart exploded")
    saved, fcharts.price_yield_chart = fcharts.price_yield_chart, boom
    try:
        run_btn.on_click(None)
    finally:
        fcharts.price_yield_chart = saved
    assert any(t == "RuntimeError: chart exploded" for t in texts()), texts()[:3]
    assert ring.visible is False
    run_btn.on_click(None)
    assert "98.000" in texts() and ring.visible is False
    print("ok")
