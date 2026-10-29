"""Acceptance checks for the Bonds screen (owner's verification request, 2026-10-27).

Every number is checked against an independent implementation written in this
file from the textbook formula (`_ind_*`), never against the repository function
under test. The page is driven through a stand-in for `ft.Page`: `run_thread`
either runs the worker at once or queues it, so out-of-order Runs and edits
made while a Run waits can be replayed deterministically.

Hermetic: the page runs on `source="synthetic"`, or on a FRED fetch replaced by
a stub with the cache TTL at 0; nothing opens a socket or touches the disk cache
(the one cache test points `config.ficc_cache_dir` at a temporary directory).

Request coverage: 2.1 table rows and the 95/105 inversions (4: par, price
inversion, risk numbers), 2.2 and 3.A (price/yield exclusivity with blank, 0,
NaN/inf, negative, comma input; required fields), 2.3 and 3.C (P&L =
(new - base) x notional/face, signs, convexity asymmetry, zero-rate shocks),
2.4 and 3.D (798 x 0.8 / 65, side, rounding, residual), 3.E (synthetic vs FRED
labels, stale and carried-forward curves, unit errors), 3.F (stale result
marking, newest-Run-wins, one input snapshot per Run).
"""
from __future__ import annotations

import contextlib
import math
import tempfile
import time
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import flet as ft

import config
from core.ficc import bonds, curves, data, insights
from core.ficc.common import BP, KEY_TENORS, UST_TENORS, FICCError

# --------------------------------------------------------------------------- #
# Independent formulas (street convention: coupon c·100/f every 1/f year counted
# back from maturity T, discrete compounding at f with exponent t·f)
# --------------------------------------------------------------------------- #
def _ind_schedule(T: float, f: int) -> list[float]:
    n = max(1, math.ceil(T * f - 1e-9))
    return sorted(T - k / f for k in range(n))


def _ind_flows(c: float, T: float, f: int) -> list[tuple[float, float]]:
    ts = _ind_schedule(T, f)
    return [(t, c * 100.0 / f + (100.0 if i == len(ts) - 1 else 0.0)) for i, t in enumerate(ts)]


def _ind_price(c: float, T: float, f: int, y: float) -> float:
    return sum(cf / (1.0 + y / f) ** (t * f) for t, cf in _ind_flows(c, T, f))


def _ind_risk(c: float, T: float, f: int, y: float, notional: float = 1e6):
    """(price, Macaulay, modified, convexity, DV01) from the closed forms."""
    pv = [(t, cf / (1.0 + y / f) ** (t * f)) for t, cf in _ind_flows(c, T, f)]
    p = sum(v for _, v in pv)
    mac = sum(t * v for t, v in pv) / p
    mod = mac / (1.0 + y / f)
    cvx = sum(t * (t + 1.0 / f) * v for t, v in pv) / ((1.0 + y / f) ** 2 * p)
    return p, mac, mod, cvx, mod * p / 100.0 * notional * 1e-4


def _ind_ytm(c: float, T: float, f: int, price: float) -> float:
    """Bisection on [-0.49, 1.99]: no root finder shared with the repository."""
    lo, hi = -0.49, 1.99
    g = lambda y: _ind_price(c, T, f, y) - price        # noqa: E731
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if g(lo) * g(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def _ind_round(n: float) -> int:
    """Half away from zero, the decided rule for 'Rounded' contracts."""
    k = int(math.floor(abs(n)))
    k += 1 if abs(n) - k >= 0.5 else 0
    return k if n >= 0 else -k


# --------------------------------------------------------------------------- #
# Page harness
# --------------------------------------------------------------------------- #
class _Page:
    """Stand-in for ft.Page. queued=True holds workers until `step` runs them."""

    def __init__(self, queued: bool = False) -> None:
        self.queued, self.queue = queued, []

    def run_thread(self, fn) -> None:
        if self.queued:
            self.queue.append(fn)
        else:
            fn()

    def update(self) -> None:
        pass


def _walk(c, shown: bool = False):
    if shown and getattr(c, "visible", True) is False:
        return
    yield c
    for attr in ("controls", "rows", "cells", "columns"):
        for child in getattr(c, attr, None) or []:
            yield from _walk(child, shown)
    for attr in ("content", "label"):
        child = getattr(c, attr, None)
        if child is not None and not isinstance(child, str):
            yield from _walk(child, shown)


def _page(*, queued: bool = False, source: str = "synthetic"):
    from ui.bonds_page import build_bonds_page
    pg = _Page(queued)
    root = build_bonds_page(pg)
    ctl = list(_walk(root))
    h = SimpleNamespace(
        pg=pg, root=root,
        tf={t.label: t for t in ctl if isinstance(t, ft.TextField)},
        dd={d.label: d for d in ctl if isinstance(d, ft.Dropdown)},
        button=next(b for b in ctl if isinstance(b, ft.Button)),
        ring=next(c for c in ctl if isinstance(c, ft.ProgressRing)))
    h.dd["Curve source"].value = source
    return h


def _run(h) -> None:
    h.button.on_click(None)


def _step(h, i: int = 0) -> None:
    h.pg.queue.pop(i)()


def _set(h, label: str, value: str) -> None:
    """Type into a field the way Flet does: value, then on_change (when there is one;
    test_every_input_has_a_change_handler checks that there is)."""
    f = h.tf[label]
    f.value = value
    if f.on_change is not None:
        f.on_change(SimpleNamespace(control=f))


def _pick(h, label: str, value: str) -> None:
    d = h.dd[label]
    d.value = value
    if d.on_select is not None:
        d.on_select(SimpleNamespace(control=d))


def _texts(h) -> list[str]:
    return [t.value for t in _walk(h.root, True) if isinstance(t, ft.Text) and t.value]


def _stats(h) -> dict[str, str]:
    """{label: value} of every shown stat tile (a Column of two Texts)."""
    out = {}
    for c in _walk(h.root, True):
        if isinstance(c, ft.Column) and len(c.controls) == 2 and all(
                isinstance(x, ft.Text) for x in c.controls):
            out[c.controls[0].value] = c.controls[1].value
    return out


def _errors(h) -> list[str]:
    return [t for t in _texts(h) if t.startswith(("Fill exactly", "Coupon %", "Maturity",
                                                   "Price (per 100)", "Yield %", "Notional",
                                                   "CTD DV01", "Conversion factor",
                                                   "Position DV01", "FRED", "Give exactly"))]


def _calc(h, *, coupon="4.50", maturity="10", price="", ytm="4.50", notional="1000000",
          tool="calc") -> dict[str, str]:
    h.dd["Tool"].value = tool
    h.tf["Coupon %"].value, h.tf["Maturity (years)"].value = coupon, maturity
    h.tf["Price (per 100)"].value, h.tf["Yield %"].value = price, ytm
    h.tf["Notional"].value = notional
    _run(h)
    return _stats(h)


@contextlib.contextmanager
def _patched(obj, name: str, value):
    saved = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, saved)


def _bdays_back(k: int) -> str:
    return str(np.busday_offset(date.today().isoformat(), -k, roll="backward"))


_PAR_PCT = (4.30, 4.25, 4.20, 4.00, 3.80, 3.75, 3.80, 3.90, 4.05, 4.50, 4.45)
# The page's contract text (a literal, not imported, so a page without it fails on behaviour).
_STALE = "Inputs changed since this result was computed. Press Run to refresh it."


def _fred_stub(*, last: str | None = None, override: dict | None = None, n: int = 30,
               scale: float = 1.0):
    """A `_fred_fetch` stand-in: n business days per DGS id ending on `last` (default:
    the latest business day), percent values. `override` = {id: (last_date, value)}."""
    override = override or {}

    def fetch(ids, start):
        out = {}
        for i in ids:
            k = data._TREASURY_IDS.index(i)
            end, val = override.get(i, (last or _bdays_back(0), _PAR_PCT[k]))
            days = np.busday_offset(end, -np.arange(n)[::-1], roll="backward")
            out[i] = [(str(d), val * scale) for d in days]
        return out
    return fetch


@contextlib.contextmanager
def _fred(fetch):
    with _patched(data, "_fred_fetch", fetch), _patched(config, "FICC_CACHE_TTL_SECONDS", 0.0):
        yield


def _raise_fetch(*_a, **_k):
    raise FICCError("offline (bonds acceptance)")


def _chip(h, prefix: str):
    for c in _walk(h.root, True):
        if isinstance(c, ft.Container) and isinstance(c.content, ft.Text) \
                and (c.content.value or "").startswith(prefix):
            return c.content
    return None


def _token_of(text_control) -> str:
    from ui.components import colour_for
    for tok in ("success", "warning", "error", "muted"):
        if text_control.color == colour_for(tok):
            return tok
    return "?"


# --------------------------------------------------------------------------- #
# A. Price / yield input contract
# --------------------------------------------------------------------------- #
def test_price_yield_exclusive_with_field_errors():
    h = _page()
    s = _calc(h, price="100", ytm="4.5")
    assert "Price" not in s, "both filled must not compute"
    msg = [t for t in _texts(h) if t.startswith("Fill exactly one")]
    assert msg and "Price (per 100)" in msg[0] and "Yield %" in msg[0] and "both are filled" in msg[0]
    assert h.tf["Price (per 100)"].error and h.tf["Yield %"].error
    s = _calc(h, price="", ytm="")
    assert "Price" not in s and any("both are blank" in t for t in _texts(h))
    assert h.ring.visible is False
    s = _calc(h, price="", ytm="4.5")                    # yield given -> price computed
    assert s["Price"] == "100.000" and s["Yield"] == "4.500%"
    assert h.tf["Price (per 100)"].error is None and h.tf["Yield %"].error is None
    s = _calc(h, coupon="5.5", price="95", ytm="")       # price given -> yield computed
    assert s["Price"] == "95.000" and s["Yield"] == f"{_ind_ytm(0.055, 10, 2, 95.0) * 100:.3f}%"


def test_zero_negative_nan_inf_and_comma_inputs():
    h = _page()
    s = _calc(h, ytm="0")                                # 0% is a yield, not a blank
    assert s["Price"] == f"{_ind_price(0.045, 10, 2, 0.0):.3f}" == "145.000"
    s = _calc(h, ytm="-0")
    assert s["Yield"] == "0.000%", s["Yield"]
    s = _calc(h, ytm="-1")                               # a negative yield is valid
    assert s["Price"] == f"{_ind_price(0.045, 10, 2, -0.01):.3f}"
    cases = {
        ("Price (per 100)", "0"): "Price (per 100): must be > 0, got 0.",
        ("Price (per 100)", "-5"): "Price (per 100): must be > 0, got -5.",
        ("Price (per 100)", "-inf"): "Price (per 100): '-inf' is not a number.",
        ("Yield %", "nan"): "Yield %: 'nan' is not a number.",
        ("Yield %", "inf"): "Yield %: 'inf' is not a number.",
        ("Yield %", "4,5"): "Yield %: '4,5' is not a number.",
        ("Yield %", "250"): "Yield %: must be > -50 and <= 200, got 250.",
        ("Yield %", "-50"): "Yield %: must be > -50 and <= 200, got -50.",
        ("Coupon %", "-1"): "Coupon %: must be >= 0, got -1.",
        ("Coupon %", "1,2a"): "Coupon %: '1,2a' is not a number.",
        ("Notional", "1_000"): "Notional: '1_000' is not a number.",
        ("Maturity (years)", "0"): "Maturity (years): must be > 0 and <= 100, got 0.",
        ("Maturity (years)", "1e5"): "Maturity (years): must be > 0 and <= 100, got 1e5.",
    }
    arg = {"Price (per 100)": "price", "Yield %": "ytm", "Coupon %": "coupon",
           "Notional": "notional", "Maturity (years)": "maturity"}
    for (label, raw), want in cases.items():
        h = _page()
        kw = {"price": raw, "ytm": ""} if arg[label] == "price" else {arg[label]: raw}
        s = _calc(h, **kw)
        assert "Price" not in s, (label, raw, s)
        assert want in _texts(h), (label, raw, _errors(h))
        assert h.tf[label].error, (label, raw)
    h = _page()
    s = _calc(h, notional="1,000,000")                   # thousands separators are fine
    assert s["DV01"] == f"{_ind_risk(0.045, 10, 2, 0.045)[4]:,.0f}" == "798"


def test_required_fields_have_no_silent_default():
    for label, kw in (("Coupon %", {"coupon": ""}), ("Maturity (years)", {"maturity": ""}),
                      ("Notional", {"notional": ""})):
        h = _page()
        s = _calc(h, **kw)
        assert "Price" not in s and f"{label}: required." in _texts(h), (label, _errors(h))
        assert h.tf[label].error == "required."
    for label in ("Conversion factor", "CTD DV01 / contract"):
        h = _page()
        h.tf[label].value = ""
        s = _calc(h, tool="hedge")
        assert not any(k.startswith("Contracts to") for k in s), (label, s)
        assert f"{label}: required." in _texts(h), (label, _errors(h))


def test_tiny_maturity_prices_instead_of_index_error():
    b = bonds.Bond(0.05, 1e-12)
    assert abs(bonds.price_from_yield(b, 0.045) - 102.5) < 1e-6
    h = _page()
    s = _calc(h, maturity="1e-10")
    assert not any("IndexError" in t for t in _texts(h)), _errors(h)
    assert s["Price"] == "102.250" and s["Breakeven"] == "n/a", s


# --------------------------------------------------------------------------- #
# B. Pricing and risk against independent formulas
# --------------------------------------------------------------------------- #
_TABLE_21 = (   # coupon, price input, yield input -> screen strings of the request's table 2.1
    (0.055, None, 0.045, ("107.982", "4.500%", "7.92y", "7.74", "73.0", "836")),
    (0.045, None, 0.055, ("92.386", "5.500%", "8.07y", "7.86", "74.4", "726")),
    (0.055, None, 0.055, ("100.000", "5.500%", "7.82y", "7.61", "71.2", "761")),
    (0.055, 95.0, None, ("95.000", "6.178%", "7.76y", "7.52", "69.9", "715")),
    (0.055, 105.0, None, ("105.000", "4.863%", "7.88y", "7.70", "72.3", "808")),
)


def test_request_table_21_rows_match_independent_formulas():
    h = _page()
    for c, px, y, screen in _TABLE_21:
        b = bonds.Bond(coupon=c, maturity=10.0, freq=2)
        yy = _ind_ytm(c, 10.0, 2, px) if y is None else y
        p, mac, mod, cvx, dv = _ind_risk(c, 10.0, 2, yy)
        repo_y = bonds.yield_from_price(b, px) if y is None else y
        assert abs(repo_y - yy) < 1e-10, (c, px, repo_y, yy)
        assert abs(bonds.price_from_yield(b, yy) - p) < 1e-6
        assert abs(bonds.macaulay_duration(b, yy) - mac) < 1e-6
        assert abs(bonds.modified_duration(b, yy) - mod) < 1e-6
        assert abs(bonds.convexity(b, yy) - cvx) < 1e-6
        assert abs(bonds.dv01(b, yy) - dv) < 1e-6
        mine = (f"{p:.3f}", f"{yy * 100:.3f}%", f"{mac:.2f}y", f"{mod:.2f}", f"{cvx:.1f}",
                f"{dv:,.0f}")
        assert mine == screen, (mine, screen)
        s = _calc(h, coupon=f"{c * 100:g}", price="" if px is None else f"{px:g}",
                  ytm="" if y is None else f"{y * 100:g}")
        got = tuple(s[k] for k in ("Price", "Yield", "Macaulay", "Modified", "Convexity", "DV01"))
        assert got == screen, (got, screen)


def test_par_premium_discount_and_ytm_inversion():
    for f in (1, 2, 4, 12):
        for T in (0.4, 1.0, 7.3, 10.0, 30.0):
            b = bonds.Bond(coupon=0.055, maturity=T, freq=f)
            assert abs(_ind_price(0.055, T, f, 0.055) - bonds.price_from_yield(b, 0.055)) < 1e-9
            if abs(T * f - round(T * f)) < 1e-9:      # whole periods: no stub, no accrued
                assert abs(bonds.price_from_yield(b, 0.055) - 100.0) < 1e-9, (f, T)
                assert bonds.price_from_yield(b, 0.045) > 100.0 > bonds.price_from_yield(b, 0.065)
            for px in (95.0, 105.0):
                assert abs(bonds.yield_from_price(b, px) - _ind_ytm(0.055, T, f, px)) < 1e-9
    b = bonds.Bond(0.055, 10.0)
    assert f"{bonds.yield_from_price(b, 95.0) * 100:.3f}" == "6.178"
    assert f"{bonds.yield_from_price(b, 105.0) * 100:.3f}" == "4.863"


def test_duration_convexity_dv01_by_finite_differences():
    for c, T, f, y in ((0.055, 10.0, 2, 0.045), (0.0, 10.0, 2, 0.05), (0.08, 3.3, 4, 0.02),
                       (0.03, 30.0, 1, 0.06), (0.05, 2.0, 12, 0.0)):
        b = bonds.Bond(coupon=c, maturity=T, freq=f, notional=1e6)
        hh = 1e-5
        p0, pu, pd = (_ind_price(c, T, f, v) for v in (y, y + hh, y - hh))
        num_mod = -(pu - pd) / (2 * hh) / p0
        num_cvx = (pu - 2 * p0 + pd) / hh ** 2 / p0
        num_dv01 = (_ind_price(c, T, f, y - BP) - _ind_price(c, T, f, y + BP)) / 2 * 1e4
        assert abs(bonds.modified_duration(b, y) - num_mod) < 1e-6, (c, T, f)
        assert abs(bonds.macaulay_duration(b, y) - num_mod * (1 + y / f)) < 1e-6
        assert abs(bonds.convexity(b, y) - num_cvx) < 1e-3 * max(1.0, num_cvx)
        assert abs(bonds.dv01(b, y) - num_dv01) < 1e-3 * num_dv01, (bonds.dv01(b, y), num_dv01)


def test_carry_roll_for_a_bond_maturing_inside_the_horizon():
    flat = curves.flat_curve(0.045)
    for T in (1 / 12, 0.1, 0.2, 0.25):
        b = bonds.Bond(coupon=0.055, maturity=T, freq=2)
        px = bonds.price_from_yield(b, 0.045)
        cr = bonds.carry_roll(b, flat, px)
        cash = sum(cf for _, cf in _ind_flows(0.055, T, 2))
        want = cash - px - 0.045 * px * T              # all cash in hand, funding to maturity
        assert abs(cr.total - want) < 1e-9, (T, cr.total, want)
        assert cr.horizon == T and math.isnan(cr.breakeven_bp), (T, cr)
    totals = [bonds.carry_roll(b, flat, bonds.price_from_yield(b, 0.045)).total
              for b in (bonds.Bond(0.055, 0.25 + d, 2) for d in (-1e-7, 0.0, 1e-7))]
    assert max(totals) - min(totals) < 1e-4, totals   # no jump at maturity = horizon
    h = _page()
    s = _calc(h, coupon="5.5", maturity="0.0833333333333", ytm="4.5")
    assert s["Breakeven"] == "n/a" and "Carry (1m)" in s, s
    assert not any("must fall" in t for t in _texts(h))


# --------------------------------------------------------------------------- #
# C. Scenarios
# --------------------------------------------------------------------------- #
def test_scenario_pnl_is_reprice_times_notional_with_zero_rate_shocks():
    """The owner's 2.3 numbers came off the FRED curve of that day and cannot be reproduced
    offline. Their shape matches what this test pins: rises lose, falls gain more than rises
    lose, and the +-100bp rows bracket DV01 x 100 the way a zero-rate shock (not a yield
    shock) does (c 5.5%, y 4.5%: -81,597 / +89,400 around DV01 836 x 100; y 5.5%: -74,657 /
    +81,766 around 761 x 100)."""
    c = y = 0.055
    r = 2 * math.log1p(y / 2)                           # flat cc zero at the bond's own yield
    b = bonds.Bond(coupon=c, maturity=10.0, freq=2)
    flows = _ind_flows(c, 10.0, 2)
    rows = {x.name: x for x in bonds.scenario_pnl(b, curves.flat_curve(r), 100.0)}
    for name, bp in (("+25bp parallel", 25), ("-25bp parallel", -25), ("+100bp parallel", 100),
                     ("-100bp parallel", -100)):
        new = sum(cf * math.exp(-(r + bp * BP) * t) for t, cf in flows)
        row = rows[name]
        assert abs(row.new_price - new) < 1e-9, name
        assert abs(row.pnl - (new - 100.0) * 1e6 / 100.0) < 1e-6, name
        assert abs(row.pnl_pct - (new / 100.0 - 1.0)) < 1e-12
    assert f"{rows['+100bp parallel'].pnl:,.1f}" == "-74,780.1"
    assert f"{rows['-100bp parallel'].pnl:,.1f}" == "81,906.3"
    # signs and convexity asymmetry; parallel rows are zero shifts, not yield shifts
    up, dn = rows["+100bp parallel"].pnl, rows["-100bp parallel"].pnl
    dv = _ind_risk(c, 10.0, 2, y)[4]
    assert rows["+25bp parallel"].pnl < 0 < rows["-25bp parallel"].pnl and abs(dn) > abs(up)
    assert abs(up) < dv * 100 < (1 + y / 2) * dv * 100 < dn
    one = (rows["+25bp parallel"].pnl, rows["-25bp parallel"].pnl)
    assert abs(-(one[0] - one[1]) / 2 / 25 / dv - (1 + y / 2)) < 2e-3
    # the screen: every row's P&L is (new - base) x notional / 100 off the page's own base price
    h = _page()
    _calc(h, coupon="5.5", ytm="4.5", tool="scenarios")
    texts = _texts(h)
    assert "Shock (bp, cc zero rates)" in texts and "P&L % of MV" in texts
    note = next(t for t in texts if t.startswith("Shocks move"))
    assert "zero rates" in note and "exceed" not in note and "of market value" in note
    assert any("-12.5" in t and "7y +0.0" in t for t in texts), "fly shows every key tenor"


def test_named_shocks_bite_at_their_own_tenors_on_a_partial_curve():
    full = curves.bootstrap_par_curve(UST_TENORS, [v / 100 for v in _PAR_PCT])
    keep = [i for i, t in enumerate(UST_TENORS) if t not in (7.0, 20.0, 30.0)]
    part = curves.bootstrap_par_curve([UST_TENORS[i] for i in keep],
                                      [_PAR_PCT[i] / 100 for i in keep])
    for crv in (full, part):
        for name, shock in bonds.SCENARIO_SHOCKS.items():
            if isinstance(shock, float):
                continue
            sc = bonds.shocked_curve(crv, shock)
            for k, bp in shock.items():
                assert abs((float(sc.zero(k)) - float(crv.zero(k))) / BP - bp) < 1e-6, \
                    (name, k, bp)
    # on the full grid the result equals the old knot-only rule (no number moved)
    b = bonds.Bond(0.045, 30.0)
    for name, shock in bonds.SCENARIO_SHOCKS.items():
        if isinstance(shock, float):
            continue
        keys = sorted(shock)
        old = curves.YieldCurve(full.date, full.source, full.tenors, tuple(
            z + float(np.interp(t, keys, [shock[k] for k in keys])) * BP
            for t, z in zip(full.tenors, full.zeros)))
        new = bonds.shocked_curve(full, shock)
        assert abs(bonds.price_from_curve(b, old) - bonds.price_from_curve(b, new)) < 1e-9, name


# --------------------------------------------------------------------------- #
# D. Futures hedge
# --------------------------------------------------------------------------- #
def test_hedge_798_x_08_over_65_side_rounding_and_residual():
    assert f"{798 * 0.8 / 65:.2f}" == "9.82"            # the request's own arithmetic
    pos = _ind_risk(0.045, 10.0, 2, 0.045)[4]           # 798.1856: the calculator's DV01
    n = pos * 0.8 / 65.0
    k = _ind_round(n)
    resid = pos - k * 65.0 / 0.8
    assert abs(bonds.futures_hedge_ratio(pos, 65.0, 0.8) - n) < 1e-12
    assert (f"{n:.2f}", k, f"{resid:+.2f}") == ("9.82", 10, "-14.31")
    h = _page()
    s = _calc(h, tool="hedge")
    assert s["Position DV01 (calculator)"] == "798.19" and s["Futures DV01"] == "81.25"
    assert s["Contracts to sell"] == "9.82" and s["Rounded"] == "10"
    assert s["Net DV01 after hedge"] == "-14.31"
    note = next(t for t in _texts(h) if t.startswith("contracts = position DV01"))
    assert "798.19 x 0.8000 / 65.00 = 9.82: sell 10" in note and "over-hedged" in note
    assert "not modelled" in note and "per contract face" in note
    h.tf["Position DV01 (blank = calculator)"].value = "-798.19"     # a short book buys
    s = _calc(h, tool="hedge")
    assert "Contracts to sell" not in s and s["Contracts to buy"] == "9.82"
    assert s["Rounded"] == "10" and s["Net DV01 after hedge"] == "+14.31"
    assert s["Position DV01 (override)"] == "-798.19"
    for bad in ((pos, 0.0, 0.8), (pos, -65.0, 0.8), (pos, 65.0, 0.0), (pos, math.nan, 0.8),
                (pos, 65.0, math.inf), (1e308, 1e-300, 2.0)):
        try:
            bonds.futures_hedge_ratio(*bad)
        except ValueError:
            continue
        raise AssertionError(f"futures_hedge_ratio{bad} must raise")


def test_rounding_is_half_away_from_zero_as_decided():
    assert round(10.5) == 10 and round(9.5) == 10        # Python's half-to-even, not used
    for n, k in ((10.5, 11), (-10.5, -11), (9.5, 10), (8.5, 9), (10.49, 10),
                 (0.49999999999999994, 0), (2.0 ** 52 + 1, 2 ** 52 + 1), (-0.0, 0)):
        assert bonds.round_contracts(n) == _ind_round(n) == k, (n, bonds.round_contracts(n))
    h = _page()
    h.tf["Position DV01 (blank = calculator)"].value = "682.5"
    h.tf["Conversion factor"].value = "1"
    s = _calc(h, tool="hedge")
    assert s["Contracts to sell"] == "10.50" and s["Rounded"] == "11"
    assert s["Net DV01 after hedge"] == "-32.50"


def test_hedge_override_is_named_and_warned():
    h = _page()
    h.tf["Position DV01 (blank = calculator)"].value = "798"
    s = _calc(h, tool="hedge", coupon="4.5", notional="2,000,000")
    assert s["Position DV01 (override)"] == "798.00"
    assert any(t.startswith("Position DV01 798.00 is your override") for t in _texts(h))
    h.tf["CTD DV01 / contract"].value = "0.065"          # per 100 face instead of per contract
    s = _calc(h, tool="hedge")
    units = next(t for t in _texts(h) if t.startswith("Check the units"))
    assert "not exchange data" in units and "ZN" not in units and "lie between" not in units
    assert s["CTD DV01 / contract"] == "0.065" and s["Futures DV01"] == "0.08125"


# --------------------------------------------------------------------------- #
# E. Curve source labels
# --------------------------------------------------------------------------- #
def test_synthetic_and_fred_are_labelled_apart_with_a_mocked_fetch():
    with _fred(_fred_stub()):
        h = _page(source="auto")
        s = _calc(h)
        chip_ = _chip(h, "curve:")
        assert "FRED" in chip_.value and "newest obs" in chip_.value and _token_of(chip_) == "success"
        assert not any(t.startswith(("Synthetic data", "Curve check")) for t in _texts(h))
        assert "z-spread" in s
    with _fred(_raise_fetch):
        h = _page(source="auto")
        s = _calc(h)
        chip_ = _chip(h, "curve:")
        assert "SYNTHETIC" in chip_.value and _token_of(chip_) == "error"
        banner = next(t for t in _texts(h) if t.startswith("Synthetic data"))
        assert "FRED failed" in banner and banner.count("offline (bonds acceptance)") == 1
        assert any("SYNTHETIC" in t and "not the market" in t for t in _texts(h))  # narrative
        h = _page(source="fred")
        s = _calc(h)
        assert "Price" not in s and any(t.startswith("FRED served 0/11") for t in _texts(h))


def test_stale_carried_forward_and_bad_unit_curves_are_flagged():
    with _fred(_fred_stub(last=_bdays_back(80))):
        h = _page(source="fred")
        _calc(h)
        banner = next(t for t in _texts(h) if t.startswith("Curve check"))
        assert "Stale" in banner and _token_of(_chip(h, "curve:")) == "warning"
        assert any(_bdays_back(80) in t and "newest observation" in t for t in _texts(h))
    with _fred(_fred_stub(override={"DGS30": (_bdays_back(50), 4.95)})):
        h = _page(source="fred")
        _calc(h)
        banner = next(t for t in _texts(h) if t.startswith("Curve check"))
        assert f"DGS30 last observed {_bdays_back(50)}" in banner
    with _fred(_fred_stub(scale=0.01)):                  # decimals where FRED serves percent
        h = _page(source="auto")
        _calc(h)
        assert _token_of(_chip(h, "curve:")) == "error"
        assert any(t.startswith("Synthetic data") and "outside" in t for t in _texts(h))
        h = _page(source="fred")
        s = _calc(h)
        assert "Price" not in s and any("outside" in t for t in _texts(h))


def test_curve_lagging_in_a_shared_cache_is_refetched():
    today, before = _bdays_back(0), _bdays_back(2)     # older than the file's write day
    fresh = _fred_stub(last=today)
    old = _fred_stub(last=before)(["DGS2", "DGS10", "DGS30"], "")
    old = {i: [(d, v - 0.08) for d, v in r] for i, r in old.items()}   # earlier prints
    with tempfile.TemporaryDirectory() as tmp, \
            _patched(config, "ficc_cache_dir", lambda: Path(tmp)), \
            _patched(config, "FICC_CACHE_TTL_SECONDS", 21600.0), \
            _patched(data, "_fred_fetch", fresh):
        keys = [data._cache_key("FRED", i, 504) for i in data._TREASURY_IDS]
        saved = {k: data._MEM.pop(k) for k in keys if k in data._MEM}
        try:
            for i, r in old.items():                     # written an hour ago by another screen
                data._MEM[data._cache_key("FRED", i, 504)] = (time.time() - 3600, r)
            snap = data.load_treasury_curve(source="fred").latest()
        finally:
            for k in keys:
                data._MEM.pop(k, None)
            data._MEM.update(saved)
    k10 = snap.tenors.index(10.0)
    assert snap.date == today and abs(snap.par_yields[k10] - 0.0405) < 1e-12, snap


def test_fred_fetch_is_bounded_and_a_hung_batch_is_not_retried_per_id():
    seen = []

    class FakeReader:
        def __init__(self, ids, **kw):
            seen.append(kw)

        def read(self):
            import pandas as pd
            return pd.DataFrame({"DGS10": [4.0]}, index=pd.to_datetime(["2026-10-23"]))
    def no_timeout(*_a, **_k):
        raise AssertionError("DataReader takes no timeout")
    import pandas_datareader.fred as pf
    if data._pdr is None:
        raise AssertionError("pandas_datareader is required (requirements.txt)")
    with _patched(pf, "FredReader", FakeReader), _patched(data._pdr, "DataReader", no_timeout):
        out = data._fred_fetch(["DGS10"], "2026-01-01")
    assert out == {"DGS10": [("2026-10-23", 4.0)]}
    assert seen and seen[0]["timeout"] == config.HTTP_TIMEOUT_SECONDS and seen[0]["retry_count"] == 0
    calls = []

    def hung(ids, start):
        calls.append(list(ids))
        time.sleep(0.25)
        raise ConnectionError("timed out")

    def fast(ids, start):
        calls.append(list(ids))
        raise ConnectionError("refused")
    ids = ["DGS2", "DGS5", "DGS10"]
    with _patched(config, "HTTP_TIMEOUT_SECONDS", 0.2), \
            _patched(config, "FICC_CACHE_TTL_SECONDS", 0.0):
        with _patched(data, "_fred_fetch", hung):
            rows, errors = data._provider_rows("FRED", ids, 504)
        assert len(calls) == 1 and not rows and set(errors) == set(ids), calls
        calls.clear()
        with _patched(data, "_fred_fetch", fast):
            data._provider_rows("FRED", ids, 504)
        assert len(calls) == 1 + len(ids), calls        # a fast failure is still retried per id


def test_slow_batch_with_an_http_error_is_still_retried_per_id():
    """A slow but alive network: the batch outlasts HTTP_TIMEOUT_SECONDS and fails on one
    retired id with an HTTP error (an answer, not a stall), so the ids are retried one by one."""
    calls = []

    def slow_404(ids, start):
        calls.append(list(ids))
        if len(ids) > 1:
            time.sleep(0.25)                             # alive but slower than the timeout
            raise FICCError("FRED answered HTTP 404 for DGS20.")
        if ids == ["DGS20"]:
            raise FICCError("FRED answered HTTP 404 for DGS20.")
        return _fred_stub()(ids, start)
    with _patched(config, "HTTP_TIMEOUT_SECONDS", 0.2), _fred(slow_404):
        panel = data.load_treasury_curve(source="fred")
    assert panel.source == "FRED" and len(panel.tenors) == 10 and "DGS20" in panel.note
    assert len(calls) == 1 + 11, calls


def test_missing_tenor_note_describes_the_interpolation():
    """A middle tenor missing is interpolated across (log-linear DF), not 'held flat'."""
    def no_20y(ids, start):
        return _fred_stub()([i for i in ids if i != "DGS20"], start)
    with _fred(no_20y):
        panel = data.load_treasury_curve(source="fred")
    assert 20.0 not in panel.tenors and panel.note.startswith("Missing tenors: DGS20;"), panel.note
    assert "interpolates across a gap (log-linear DF)" in panel.note
    assert "beyond the longest served tenor the curve is held flat" not in panel.note


def test_failed_fred_reasons_keep_the_cause_once():
    """pandas_datareader puts the URL on the first line and the cause after '\nException:\n';
    the reason shown is the cause, once for all ids. The real FredReader runs; only
    requests.Session.get is replaced (no socket)."""
    import requests
    if data._pdr is None:
        raise AssertionError("pandas_datareader is required (requirements.txt)")

    def get(self, url, params=None, headers=None, timeout=None, **kw):
        raise requests.exceptions.ProxyError(
            "HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Max retries exceeded "
            f"with url: /graph/fredgraph.csv?id={url.rsplit('=', 1)[-1]} (Caused by ProxyError("
            "'Unable to connect to proxy', OSError('Tunnel connection failed: 403 Forbidden')))")
    with _patched(requests.Session, "get", get), \
            _patched(config, "FICC_CACHE_TTL_SECONDS", 0.0):
        try:
            data.load_treasury_curve(source="fred")
        except FICCError as exc:
            msg = str(exc)
        else:
            raise AssertionError("an unreachable FRED must not serve a curve")
    assert msg.startswith("FRED served 0/11 tenors (DGS1MO, DGS3MO, ") and "DGS30: " in msg, msg
    assert msg.count("Unable to read URL") == 1 and "\n" not in msg, msg
    assert msg.endswith("Tunnel connection failed: 403 Forbidden')))).") and "?id=DGS1MO" not in msg, msg


def test_lagging_refetch_is_tried_once_per_cache_entry():
    """FRED's own lag (DGS30 one day behind) or a dead network must not cost a refetch on
    every Run; a cache entry written before the others is refetched once."""
    today, before = _bdays_back(0), _bdays_back(1)
    lag30 = _fred_stub(override={"DGS30": (before, 4.45)})
    calls = []

    def counted(fetch):
        def f(ids, start):
            calls.append(list(ids))
            return fetch(ids, start)
        return f
    keys = [data._cache_key("FRED", i, 504) for i in data._TREASURY_IDS]
    with tempfile.TemporaryDirectory() as tmp, \
            _patched(config, "ficc_cache_dir", lambda: Path(tmp)), \
            _patched(config, "FICC_CACHE_TTL_SECONDS", 21600.0):
        saved = {k: data._MEM.pop(k) for k in keys if k in data._MEM}
        try:
            with _patched(data, "_fred_fetch", counted(lag30)):    # all written together
                data.load_treasury_curve(source="fred")
                data.load_treasury_curve(source="fred")
            assert calls == [list(data._TREASURY_IDS)], calls       # no refetch for FRED's lag
            calls.clear()
            k30 = data._cache_key("FRED", "DGS30", 504)
            data._MEM[k30] = (time.time() - 3600, data._MEM[k30][1])   # written earlier
            with _patched(data, "_fred_fetch", counted(lag30)):    # FRED has nothing newer
                data.load_treasury_curve(source="fred")
                data.load_treasury_curve(source="fred")
            assert calls == [["DGS30"]], calls
            calls.clear()
            data._MEM[k30] = (time.time() - 1800, data._MEM[k30][1])   # another earlier entry
            with _patched(data, "_fred_fetch", counted(_raise_fetch)):  # network gone
                p1 = data.load_treasury_curve(source="fred")
                data.load_treasury_curve(source="fred")
            assert calls == [["DGS30"]], calls
            assert p1.latest().date == today and f"DGS30 last observed {before}" in p1.note
        finally:
            for k in keys:
                data._MEM.pop(k, None)
            data._MEM.update(saved)
    with _fred(_fred_stub()):                                   # TTL 0: nothing is a cache hit
        old = {k: (time.time() - 3600, [("2000-01-03", 1.0)] * 5) for k in keys}
        saved = {k: data._MEM.pop(k) for k in keys if k in data._MEM}
        data._MEM.update(old)
        calls.clear()
        try:
            with _patched(data, "_fred_fetch", counted(lag30)):
                data.load_treasury_curve(source="fred")
            assert calls == [list(data._TREASURY_IDS)], calls
        finally:
            for k in keys:
                data._MEM.pop(k, None)
            data._MEM.update(saved)


# --------------------------------------------------------------------------- #
# F. State: stale marking, one snapshot per Run, newest Run wins
# --------------------------------------------------------------------------- #
def test_every_input_has_a_change_handler():
    h = _page()
    for label, f in h.tf.items():
        assert f.on_change is not None, f"{label} has no on_change handler"
    for label, d in h.dd.items():
        assert d.on_select is not None, f"{label} has no on_select handler"


def test_edit_after_run_marks_the_result_and_revert_unmarks():
    STALE_TEXT = _STALE
    h = _page()
    _calc(h)
    echo = next(t for t in _texts(h) if t.startswith("Computed for:"))
    assert "coupon 4.5%" in echo and "yield 4.5% (price computed)" in echo
    assert "curve requested Synthetic demo" in echo and "served SYNTHETIC (simulated" in echo
    assert STALE_TEXT not in _texts(h)
    _set(h, "Coupon %", "4.25")
    assert STALE_TEXT in _texts(h), "an edit without Run marks the result"
    _set(h, "Coupon %", "4.50")
    assert STALE_TEXT not in _texts(h), "back to the inputs the result used"
    _pick(h, "Tool", "hedge")
    assert STALE_TEXT in _texts(h), "a calc result under the hedge tool is marked"
    _pick(h, "Tool", "calc")
    _pick(h, "Curve source", "fred")
    assert STALE_TEXT in _texts(h)
    _pick(h, "Curve source", "synthetic")
    _set(h, "Yield %", "4,5")
    _run(h)
    assert STALE_TEXT not in _texts(h) and "Yield %: '4,5' is not a number." in _texts(h)


def test_newest_run_wins_when_runs_finish_out_of_order():
    h = _page(queued=True)
    h.tf["Coupon %"].value = "5.5"
    _run(h)                                              # A: 5.5% -> 107.982
    _set(h, "Coupon %", "4.5")
    _run(h)                                              # B: 4.5% -> 100.000
    assert h.ring.visible is True
    _step(h, 0)                                          # A finishes first: discarded
    assert "107.982" not in _texts(h) and h.ring.visible is True
    _step(h, 0)                                          # B
    assert _stats(h)["Price"] == "100.000" and h.ring.visible is False
    h = _page(queued=True)
    h.tf["Coupon %"].value = "5.5"
    _run(h)
    _set(h, "Coupon %", "4.5")
    _run(h)
    _step(h, 1)                                          # B first
    _step(h, 0)                                          # then the stale A
    assert _stats(h)["Price"] == "100.000" and "107.982" not in _texts(h)


def test_late_failure_does_not_replace_a_newer_result():
    """Same inputs for both Runs, so a page that reads the fields late cannot dodge the
    failure: the fetch answers Run B, then fails for the older Run A that finishes last."""
    calls = []

    def flaky(ids, start):
        calls.append(list(ids))
        if len(calls) > 1:
            raise FICCError("offline (late)")
        return _fred_stub()(ids, start)
    with _fred(flaky):
        h = _page(queued=True, source="fred")
        _run(h)                                          # A
        _run(h)                                          # B
        _step(h, 1)                                      # B first: a result
        _step(h, 0)                                      # A late: an error, discarded
    assert _stats(h).get("Price") == "100.000", _texts(h)[:4]
    assert not any(t.startswith("FRED served") for t in _texts(h))
    assert h.ring.visible is False


def test_a_run_uses_the_inputs_of_its_click():
    STALE_TEXT = _STALE
    h = _page(queued=True)
    _run(h)                                              # click: coupon 4.5, yield 4.5
    _set(h, "Price (per 100)", "95")                     # edits while the worker waits
    _set(h, "Yield %", "")
    _set(h, "Coupon %", "5.5")
    _step(h)
    s = _stats(h)
    assert s["Price"] == "100.000" and s["Yield"] == "4.500%", s
    assert not any("exactly one" in t for t in _texts(h))
    assert STALE_TEXT in _texts(h), "inputs changed during the Run: the result is marked"


def test_clearing_one_of_price_and_yield_clears_the_pair_error():
    h = _page()
    _calc(h, price="100", ytm="4.5")
    assert h.tf["Price (per 100)"].error and h.tf["Yield %"].error
    _set(h, "Yield %", "")
    assert h.tf["Price (per 100)"].error is None and h.tf["Yield %"].error is None


def test_a_quote_too_far_from_the_curve_names_the_field():
    h = _page()
    _calc(h, coupon="4.5", ytm="-45")
    msg = [t for t in _texts(h) if "z-spread" in t and "No z-spread" in t]
    assert msg and msg[0].startswith("Yield % -45 is too far from the SYNTHETIC curve"), _errors(h)
    s = _calc(h, coupon="4.5", ytm="-20")                 # inside both brackets: a result
    assert s["Price"] == f"{_ind_price(0.045, 10, 2, -0.20):.3f}", s


def test_echo_keeps_the_typed_digits_and_names_the_served_curve():
    with _fred(_raise_fetch):
        h = _page(source="auto")
        _calc(h, price="99.1234567", ytm="")
    echo = next(t for t in _texts(h) if t.startswith("Computed for:"))
    assert "price 99.1234567 (yield computed)" in echo, echo
    assert "curve requested Auto (FRED, else synthetic)" in echo and "served SYNTHETIC" in echo


def test_scenario_notice_reports_this_curves_yield_move():
    """Flat 4.5% semi-annual par curve, a 4.5% par bond: the +100bp zero row reprices to a
    yield of 2·(exp((r + 1%)/2) - 1) with r = 2·ln(1.0225), a move of (2 + y)(e^0.005 - 1)."""
    def flat_par(ids, start):
        days = np.busday_offset(_bdays_back(0), -np.arange(30)[::-1], roll="backward")
        return {i: [(str(d), 4.5) for d in days] for i in ids}
    with _fred(flat_par):
        h = _page(source="fred")
        _calc(h, coupon="4.5", ytm="4.5", tool="scenarios")
    note = next(t for t in _texts(h) if t.startswith("Shocks move"))
    dy = (2 + 0.045) * (math.exp(0.005) - 1) * 1e4
    assert f"the +100bp row moves its yield by {dy:+.1f}bp" in note and f"{dy:.1f}" == "102.5", note
    flat = f"+{dy:.1f}bp on a curve flat at this yield, (f + y)(e^(0.01/f) - 1)"
    assert flat in note and "100 x (1 + y/f)" not in note, note     # RP-01: the exact flat-curve move, not the 1st-order slope


def test_narrative_for_a_bond_maturing_inside_the_horizon():
    a = bonds.analyze_bond(bonds.Bond(0.055, 1 / 12), ytm=0.045, curve=curves.flat_curve(0.045))
    t = insights.narrate_bond(a)
    assert "in total, so no yield move changes this hold-to-maturity result: the bond matures " \
           "inside the horizon." in t, t
    assert "so the bond matures" not in t


# --------------------------------------------------------------------------- #
# Text and chart details
# --------------------------------------------------------------------------- #
def test_narrative_separates_yield_dv01_from_zero_curve_scenarios():
    crv = curves.flat_curve(2 * math.log1p(0.0275))
    b = bonds.Bond(0.055, 10.0)
    a = bonds.analyze_bond(b, ytm=0.055, curve=crv)
    t = insights.narrate_bond(a, bonds.scenario_pnl(b, crv, a.price))
    assert "per bp of the bond's own yield" in t and "zero-curve scenarios" in t
    small = bonds.analyze_bond(bonds.Bond(0.055, 10.0, notional=500.0), ytm=0.045, curve=crv)
    assert "DV01 is 0.42 per bp" in insights.narrate_bond(small)


def test_chart_left_titles_use_the_palette_text_colour():
    import matplotlib.colors as mc
    import matplotlib.pyplot as plt
    import matplotlib.text as mt
    from core.theme import active
    from ui.qcharts import _fig
    pal = active()
    fig, ax = _fig(2.0, 2.0, pal)
    ax.set_title("x", loc="left")
    try:
        t = [c for c in ax.get_children() if isinstance(c, mt.Text) and c.get_text() == "x"]
        assert t and mc.to_hex(t[0].get_color()) == mc.to_hex(pal.text), t[0].get_color()
    finally:
        plt.close(fig)


def tests():
    return [(name, fn) for name, fn in sorted(globals().items())
            if name.startswith("test_") and callable(fn)]


if __name__ == "__main__":
    import sys
    import traceback
    failed = 0
    for name, fn in tests():
        t0 = time.perf_counter()
        try:
            fn()
            print(f"PASS {name} ({time.perf_counter() - t0:.2f}s)")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"{len(tests()) - failed}/{len(tests())} passed")
    sys.exit(1 if failed else 0)
