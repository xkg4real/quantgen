"""Rates — the yield curve, swap and swaption pricers, and short-rate simulation.

Four tools on one screen, switched by a dropdown so the input row only shows
what the chosen tool reads:

  * **Yield curve** — UST par history from FRED (or SYNTHETIC), built by one of
    nine construction methods (`core.ficc.curves.CURVE_METHODS`: five exact,
    four parametric; the chosen method is explained under the dropdown):
    descriptors, shape and regime, the curve table, tenor history and PCA.
  * **Swap pricer** — spot or forward-start IRS off the same curve: par, PV,
    DV01, key-rate DV01, carry and roll-down, the forward-swap grid.
  * **Swaption / cap-floor** — Bachelier or Black-76 on the forward swap rate
    or on each caplet's forward.
  * **Rate simulation** — Vasicek / CIR / Hull-White calibrated on SOFR, fanned
    out to a horizon, optionally revaluing a bond or swap there.

All computation runs in `page.run_thread`. The page never touches the network
itself — `core.ficc.data` does, and says which source answered. The source is
chosen automatically (FRED, synthetic fallback; the selector stays in the tree,
hidden, for tests); the answering source is shown as a small chip. A SYNTHETIC
curve or rate series is announced with a loud notice, because a swaption priced
off simulated forwards is a demo, not a quote. Percent and basis-point
formatting happens here and nowhere in the core.

Captions are authored in English and shown in Korean through
`core/ui_page_messages/rates.py`; sentences with numbers use `LocalText`.
"""
from __future__ import annotations

import math
from typing import Callable, Optional

import flet as ft

from core.ficc import insights
from core.ficc.bonds import Bond
from core.ficc.common import BP, FICCError, parse_forward_tenor, parse_tenor, tenor_label
from core.ficc.curves import (CURVE_METHODS, EXACT_METHODS, METHOD_NAMES, analyze_curve,
                              curve_from_snapshot, curve_pca)
from core.ficc.data import load_short_rate, load_treasury_curve
from core.ficc.ratesim import MODELS, calibrate, horizon_pv_distribution, simulate
from core.ficc.swaps import Swap, Swaption, analyze_swap, price_cap_floor, price_swaption
from core.i18n import LocaleContext
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.components import (LocalText, card, chip, empty_state, notice, number_field, section,
                           stat)
import ui.fcharts as fcharts
from ui.localization import table_header, literal_text, translate_controls

_TOOLS = [("curve", "Yield curve"), ("swap", "Swap pricer"),
          ("option", "Swaption / cap-floor"), ("sim", "Rate simulation")]
_SOURCES = [("auto", "Auto (FRED, synthetic fallback)"), ("fred", "FRED"),
            ("synthetic", "Synthetic demo")]
_METHODS = [(m, METHOD_NAMES[m]) for m in CURVE_METHODS]
_MODEL_LABELS = {"vasicek": "Vasicek", "cir": "CIR", "hull_white": "Hull-White"}
_OPTION_MODELS = {"bachelier": "Bachelier (normal)", "black": "Black-76"}
_VOL_LABELS = {"bachelier": "Normal vol (bp)", "black": "Black vol (%)"}
_VOL_DEFAULTS = {"bachelier": "80", "black": "30"}


def _vol_text_ko(model: str, vol_in: float) -> str:
    return f"정규 변동성 {vol_in:g}bp" if model == "bachelier" else f"Black 변동성 {vol_in:g}%"

# What each construction method assumes and when to use it (Korean in the catalogue).
_METHOD_TEXT = {
    "bootstrap": "Solves the zero rate at each quoted maturity in turn so every quoted yield is "
                 "repriced exactly; between maturities the forward rate is held flat. The standard "
                 "choice for pricing: the swap, option and simulation tools always use it.",
    "cubic_spline": "Draws a natural cubic spline through the quoted par yields, reads a yield at "
                    "every half-year and bootstraps them. Smooth and exact at every quote, but it "
                    "can swing between widely spaced long maturities.",
    "pchip": "Like the cubic spline, but with a shape-preserving monotone cubic (PCHIP) that never "
             "overshoots the quotes, so it adds no bumps the market does not show. A safe smooth "
             "choice for sparse or kinked curves.",
    "monotone_convex": "Hagan and West's method: forward rates are continuous and stay positive, and "
                       "a change in one quote moves the curve only nearby, while every quote is "
                       "repriced exactly. The U.S. Treasury has used it for its official par yield "
                       "curve since December 2021.",
    "smith_wilson": "The method insurance supervisors use (EIOPA, Solvency II): it passes exactly "
                    "through every quote and, beyond the last one, bends the forward rate toward an "
                    "assumed ultimate forward rate of 3.30% (convergence speed alpha 0.10). Both "
                    "values are assumptions, not estimates; use it to see a long-end extrapolation.",
    "nelson_siegel": "Fits three factors (level, slope and curvature) plus one decay parameter by "
                     "least squares. Smooth and easy to read, but it misses individual quotes; the "
                     "fit error is shown with the result.",
    "diebold_li": "Nelson-Siegel with the decay fixed at 0.0609 per month (Diebold and Li, 2006), so "
                  "the three factors come from a plain regression and can be compared from day to "
                  "day. Built for tracking and forecasting the curve; it fits single quotes more "
                  "loosely.",
    "svensson": "Nelson-Siegel with a second hump term (six parameters). It follows long-end shapes "
                "better; many central banks publish curves fitted this way.",
    "bjork_christensen": "Nelson-Siegel plus a second slope term that decays twice as fast (five "
                         "parameters, Björk and Christensen, 1999). It starts from the Nelson-Siegel "
                         "fit, so it never fits worse than Nelson-Siegel.",
}
_KIND_TEXT = {True: "Exact fit: reprices every quoted yield",
              False: "Smooth fit: the fit error is shown"}

# Same Korean words as the native app (quantgen_desktop/rates_narrative.py).
_SHAPES_KO = {"normal": "정상 우상향", "inverted": "역전", "humped": "중간 만기 돌출", "flat": "평탄"}
_REGIMES_KO = {"bull steepener": "금리 하락·기울기 확대", "bull flattener": "금리 하락·기울기 축소",
               "bear steepener": "금리 상승·기울기 확대", "bear flattener": "금리 상승·기울기 축소",
               "parallel up": "평행 상승", "parallel down": "평행 하락", "unchanged": "변화 없음"}

_SYNTHETIC_TEXT = {
    "curve": "Synthetic curve, not market data: a simulated demo curve stands in for the FRED "
             "Treasury curve. The reason is under Details.",
    "short rate": "Synthetic short rate, not market data: a simulated series stands in for SOFR. "
                  "The reason is under Details.",
}
_KO_CTX = LocaleContext("ko_KR")


# --------------------------------------------------------------------------- #
# Formatting and small helpers (UI only — the core stays in decimals)
# --------------------------------------------------------------------------- #
def _pct(x: float, d: int = 2) -> str:
    return f"{x * 100:.{d}f}%"


def _bp(x: float) -> str:
    return f"{x / BP:+.1f}bp"


def _money(x: float) -> str:
    return f"{x:,.0f}"


def _num(text: str | None, default: float | None, what: str) -> float | None:
    """Float from a text field; blank -> default; commas tolerated."""
    s = (text or "").strip().replace(",", "")
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"{what}: cannot read {text!r} as a number.") from None


_CURVE_HEADERS_KO = {'Tenor': '만기', 'Zero': '무이표 금리', 'DF': '할인계수',
                     'Par': '파 금리', '1y fwd': '1년 선도금리'}


def _ko(text: str) -> str:
    """The catalogue's Korean caption for an authored English source."""
    return _KO_CTX.text(text)


def _table(columns: list[str], rows: list[list[str]], *, headers_ko=None) -> ft.Control:
    # Only the approved table surfaces opt into source-preserving localization.
    # Numbers are right-aligned (every column after the first label column).
    text_cell = literal_text if headers_ko is not None else ft.Text
    return ft.Row([ft.DataTable(
        columns=[ft.DataColumn(table_header(c, ko=headers_ko.get(c), size=12)
                               if headers_ko is not None else ft.Text(c, size=12),
                               numeric=headers_ko is not None and i > 0)
                 for i, c in enumerate(columns)],
        rows=[ft.DataRow(cells=[ft.DataCell(text_cell(v, size=12)) for v in r]) for r in rows],
        column_spacing=24, heading_row_height=36, data_row_max_height=36,
    )], scroll=ft.ScrollMode.AUTO)


def _local_chip(ko: str, en: str, token: str = "muted", *, tooltip: str = "") -> ft.Control:
    """`chip` whose wording is authored in both languages (numbers inside)."""
    box = chip(en, token, tooltip=tooltip)
    old = getattr(box, "content", None)
    if isinstance(old, ft.Text):
        box.content = LocalText(ko, en, size=old.size, color=old.color, weight=old.weight)
    return box


def _local_stat(label_ko: str, label_en: str, value: str, *, value_ko: str | None = None,
                token: str = "text") -> ft.Control:
    """`stat` whose label (and optionally value) is authored in both languages."""
    tile = stat(label_en, value, token=token)
    column = getattr(tile, "content", None)
    if isinstance(column, ft.Column) and len(column.controls) == 2:
        label, shown = column.controls
        column.controls[0] = LocalText(label_ko, label_en, size=label.size, color=label.color)
        if value_ko is not None:
            column.controls[1] = LocalText(value_ko, value, size=shown.size, color=shown.color,
                                           weight=shown.weight)
    return tile


def _synthetic_notice(source: str, note: str, what: str) -> list[ft.Control]:
    """The loud synthetic notice, with the provider's full reason kept under Details."""
    if source != "SYNTHETIC":
        return []
    pal = active()
    details = ft.ExpansionTile(
        title=ft.Text("Details", size=12, weight=ft.FontWeight.W_500, color=pal.muted),
        controls=[ft.Container(literal_text(note, size=12, color=pal.muted, selectable=True),
                               padding=ft.Padding(12, 0, 12, 8))],
        tile_padding=ft.Padding(12, 0, 12, 0), dense=True, min_tile_height=32,
        expanded_cross_axis_alignment=ft.CrossAxisAlignment.START)
    return [ft.Column([notice(_SYNTHETIC_TEXT[what], "error", icon=ft.Icons.SCIENCE_OUTLINED),
                       details], spacing=2)]


def _src_chip(label: str, source: str) -> ft.Control:
    """Which provider answered: secondary, a small chip."""
    ko = {"source": "출처", "curve": "곡선 출처"}.get(label, label)
    shown = f"{source} (합성)" if source == "SYNTHETIC" else source
    return _local_chip(f"{ko}: {shown}", f"{label}: {source}",
                       "muted" if source == "SYNTHETIC" else "success")


def _curve_summary(report) -> ft.Control:
    """What the curve says, first and in words: shape, recent move, method fit."""
    pal = active()
    d, curve = report.descriptors, report.curve
    shape, regime = report.shape, report.regime
    slope = d["2s10s"] / BP
    headline_ko = (f"곡선 형태: {_SHAPES_KO.get(shape, shape)} · 최근 {report.lookback}거래일: "
                   f"{_REGIMES_KO.get(regime, regime)}")
    headline_en = f"Curve shape: {shape} · last {report.lookback} sessions: {regime}"
    if abs(slope) < 0.05:
        slope_ko, slope_en = "10년물과 2년물 금리가 같습니다.", "The 10-year and 2-year yields are equal."
    else:
        slope_ko = (f"10년물 금리가 2년물보다 {abs(slope):.1f}bp "
                    f"{'높습니다' if slope > 0 else '낮습니다'}.")
        slope_en = (f"The 10-year yield is {abs(slope):.1f}bp "
                    f"{'above' if slope > 0 else 'below'} the 2-year.")
    name = METHOD_NAMES.get(curve.method, curve.method)
    if curve.method in EXACT_METHODS:
        fit_ko = f"{_ko(name)} 방법은 모든 고시 금리를 정확히 재현합니다."
        fit_en = f"The {name} curve reprices every quoted yield exactly."
    else:
        rmse = report.ns.rmse / BP
        fit_ko = f"{_ko(name)} 적합은 고시 금리와 평균 {rmse:.1f}bp(RMS) 차이가 납니다."
        fit_en = f"The {name} fit misses the quoted yields by {rmse:.1f}bp on average (RMS)."
    return card(ft.Column([
        LocalText(headline_ko, headline_en, size=16, weight=ft.FontWeight.W_600, color=pal.text),
        LocalText(f"{slope_ko} {fit_ko}", f"{slope_en} {fit_en}", size=13, color=pal.muted),
    ], spacing=6))


def _curve(source: str, method: str = "bootstrap"):
    panel = load_treasury_curve(source=source)
    return panel, curve_from_snapshot(panel.latest(), method=method)


# --------------------------------------------------------------------------- #
# Tool workers: inputs in, result blocks out. Module-level so the self-check
# can drive them without a Flet page.
# --------------------------------------------------------------------------- #
def _run_curve(page, *, source: str, method: str, lookback: int) -> list[ft.Control]:
    panel = load_treasury_curve(source=source)
    report = analyze_curve(panel, lookback=lookback, method=method)
    try:
        pca = curve_pca(panel)
    except FICCError:                                 # panel too short for PCA
        pca = None
    d, curve = report.descriptors, report.curve
    from core.ficc.forward_conventions import (FIVE_YEAR_SIMPLE_LABEL, FIVE_YEAR_SIMPLE_LABEL_KO,
        FIVE_YEAR_SIMPLE_NOTE, FIVE_YEAR_SIMPLE_NOTE_KO, curve_descriptor_conventions)
    ko = getattr(getattr(page, "qg_locale", None), "language", None) == "ko"
    blocks = _synthetic_notice(panel.source, panel.note, "curve")
    blocks.append(_curve_summary(report))
    blocks.append(ft.Row([
        _local_stat("곡선 형태", "Shape", report.shape,
                    value_ko=_SHAPES_KO.get(report.shape, report.shape)),
        _local_stat("최근 변화", "Regime", report.regime, token="accent",
                    value_ko=_REGIMES_KO.get(report.regime, report.regime)),
        stat("2s10s", _bp(d["2s10s"])), stat("5s30s", _bp(d["5s30s"])),
        stat("3m10y", _bp(d["3m10y"])), stat("2s5s10s fly", _bp(d["2s5s10s_fly"])),
        stat("Level (2/5/10y)", _pct(d["level"])),
        stat("1y1y", _pct(d["1y1y"])), stat("2y1y", _pct(d["2y1y"])),
        stat(FIVE_YEAR_SIMPLE_LABEL_KO if ko else FIVE_YEAR_SIMPLE_LABEL, _pct(d["5y5y"])),
        stat("1y fwd vs 1y", _bp(d["1y_fwd_1y_ahead"])),
    ], spacing=8, run_spacing=8, wrap=True))
    name = METHOD_NAMES.get(curve.method, curve.method)
    fit = METHOD_NAMES.get(report.ns.method, report.ns.method)
    rmse = f"{report.ns.rmse / BP:.1f}bp"
    blocks.append(ft.Row([
        _src_chip("source", panel.source),
        _local_chip(f"기준일 {report.snapshot.date}", f"as of {report.snapshot.date}"),
        _local_chip(f"관측 {len(panel)}거래일", f"{len(panel)} sessions"),
        _local_chip(f"방법: {_ko(name)}", f"method: {name}", "accent"),
        (_local_chip(f"{_ko(fit)} 적합 오차 {rmse} (RMS)", f"{fit} fit error {rmse} (RMS)")
         if curve.method == report.ns.method else
         _local_chip(f"참고용 {_ko(fit)} 적합 오차 {rmse}", f"reference {fit} fit error {rmse}")),
        _local_chip(f"변화 비교: 최근 {report.lookback}거래일",
                    f"changes over {report.lookback} sessions"),
    ], spacing=6, run_spacing=6, wrap=True))
    blocks.append(notice(FIVE_YEAR_SIMPLE_NOTE_KO if ko else FIVE_YEAR_SIMPLE_NOTE))
    blocks.append(card(fcharts.curve_chart(report)))
    rows = []
    for r in curve.table():
        chg = report.changes.get(r["label"])
        rows.append([r["label"], _pct(r["zero"], 3), f"{r['df']:.4f}", _pct(r["par"], 3),
                     _pct(r["fwd_1y"], 3), _bp(chg) if chg is not None else "—"])
    blocks.append(_table(["Tenor", "Zero", "DF", "Par", "1y fwd", f"Chg {report.lookback}d"],
                         rows, headers_ko={**_CURVE_HEADERS_KO,
                             f"Chg {report.lookback}d": f"{report.lookback}거래일 변화"}))
    blocks.append(card(fcharts.curve_history_chart(panel)))
    if pca is not None:
        blocks.append(card(fcharts.pca_chart(pca)))
    payload = {
        "as_of": report.snapshot.date, "source": panel.source, "method": curve.method,
        "shape": report.shape, "regime": report.regime, "lookback": report.lookback,
        "descriptors": {k: float(v) for k, v in d.items()},
        "descriptor_conventions": curve_descriptor_conventions(),
        "changes": {k: float(v) for k, v in report.changes.items()},
        "ns": {"method": report.ns.method, "params": [float(x) for x in report.ns.params],
               "rmse": float(report.ns.rmse)},
        "pca_explained": ([float(x) for x in pca.explained] if pca is not None else None),
        "table": [{k: (float(v) if isinstance(v, float) else v) for k, v in r.items()}
                  for r in curve.table()],
        "note": panel.note,
    }
    blocks.append(analysis_panel(page, kind="rates_curve",
                                 narrative=insights.narrate_curve(report, pca),
                                 payload_fn=lambda p=payload: p))
    return blocks


def _run_swap(page, *, source: str, tenor_text: str, fixed_pct: float | None,
              notional: float, pay_fixed: bool) -> list[ft.Control]:
    panel, curve = _curve(source)
    try:
        start, tenor = parse_forward_tenor(tenor_text)     # "5y5y"
    except FICCError:
        start, tenor = 0.0, parse_tenor(tenor_text)        # "10y"
    swap = Swap(tenor=tenor, fixed_rate=None if fixed_pct is None else fixed_pct / 100.0,
                notional=notional, pay_fixed=pay_fixed, start=start)
    rep = analyze_swap(swap, curve)
    k = rep.par_rate if swap.fixed_rate is None else swap.fixed_rate
    blocks = _synthetic_notice(panel.source, panel.note, "curve")
    blocks.append(ft.Row([
        stat("Par rate", _pct(rep.par_rate, 3)),
        stat("Fixed rate (par)" if swap.fixed_rate is None else "Fixed rate", _pct(k, 3)),
        stat("PV", _money(rep.pv), token="success" if rep.pv >= 0 else "error"),
        stat("DV01 (+1bp P&L)", _money(rep.dv01)),
        stat("Annuity", f"{rep.annuity:.4f}"),
        stat("Carry (first period)", _money(rep.carry_1y)),
        stat("Roll-down 1y", _money(rep.rolldown_1y)),
    ], spacing=8, run_spacing=8, wrap=True))
    side_ko = "고정금리 지급" if pay_fixed else "고정금리 수취"
    name_ko = f"{tenor_label(start) if start > 0 else ''}{tenor_label(tenor)} {side_ko} 스왑"
    blocks.append(ft.Row([
        _local_chip(name_ko, swap.label, "accent"),
        _src_chip("curve", panel.source),
        _local_chip(f"곡선 기준일 {curve.date}", f"curve {curve.date}"),
        _local_chip(f"명목금액 {_money(swap.notional)}", f"notional {_money(swap.notional)}"),
        _local_chip(f"양쪽 다리 연 {swap.freq}회 지급", f"{swap.freq}/yr both legs"),
    ], spacing=6, run_spacing=6, wrap=True))
    blocks.append(card(fcharts.krd_chart(rep.krd, f"Key-rate DV01 — {swap.label}")))
    blocks.append(_table(["Forward swap", "Par rate"],
                         [[n, _pct(v, 3)] for n, v in rep.fwd_rates.items()],
                         headers_ko={"Forward swap": "선도 스왑", "Par rate": "파 스왑금리"}))
    payload = {
        "swap": swap.label, "tenor": tenor, "start": start, "pay_fixed": pay_fixed,
        "notional": notional, "fixed_rate": k, "par_rate": rep.par_rate, "pv": rep.pv,
        "dv01": rep.dv01, "annuity": rep.annuity, "carry_first_period": rep.carry_1y,
        "rolldown_1y": rep.rolldown_1y,
        "krd": {tenor_label(t): float(v) for t, v in rep.krd.items()},
        "fwd_rates": dict(rep.fwd_rates), "curve_date": curve.date,
        "curve_source": panel.source, "note": rep.note,
    }
    blocks.append(analysis_panel(page, kind="rates_swap",
                                 narrative=insights.narrate_swap(rep),
                                 payload_fn=lambda p=payload: p))
    return blocks


def _run_option(page, *, source: str, kind: str, expiry_text: str, tenor_text: str,
                strike_pct: float | None, payer: bool, model: str, vol_in: float,
                notional: float) -> list[ft.Control]:
    """kind: swaption | cap | floor. `vol_in` is bp for Bachelier, % for Black."""
    panel, curve = _curve(source)
    vol = vol_in * BP if model == "bachelier" else vol_in / 100.0
    vol_text = f"{vol_in:g}bp normal" if model == "bachelier" else f"{vol_in:g}% Black"
    strike = None if strike_pct is None else strike_pct / 100.0
    tenor = parse_tenor(tenor_text)
    blocks = _synthetic_notice(panel.source, panel.note, "curve")
    if kind == "swaption":
        sw = Swaption(expiry=parse_tenor(expiry_text), tenor=tenor, strike=strike,
                      payer=payer, notional=notional)
        rep = price_swaption(sw, curve, vol=vol, model=model)
        if not math.isfinite(rep.other_model_vol):
            other = "n/a"
        elif model == "bachelier":
            other = f"{_pct(rep.other_model_vol, 1)} Black"
        else:
            other = f"{rep.other_model_vol / BP:.0f}bp normal"
        side = "payer" if payer else "receiver"
        label = f"{tenor_label(sw.expiry)}x{tenor_label(sw.tenor)} {side}"
        side_ko = "지급자형 (payer)" if payer else "수취자형 (receiver)"
        blocks.append(ft.Row([
            stat("Forward", _pct(rep.forward, 3)),
            stat("Strike (ATM)" if strike is None else "Strike", _pct(rep.strike, 3)),
            stat("Premium", _money(rep.premium)),
            stat("Premium (bp of notional)", f"{rep.premium_bp:.1f}bp"),
            stat("Delta (per +1bp fwd)", _money(rep.delta)),
            stat("Gamma (per bp²)", f"{rep.gamma:,.2f}"),
            stat(f"Vega ({rep.vega_unit})", _money(rep.vega)),
            stat("Theta (1d)", _money(rep.theta_1d)),
            stat("Other-model vol", other),
        ], spacing=8, run_spacing=8, wrap=True))
        blocks.append(ft.Row([
            _local_chip(f"{tenor_label(sw.expiry)}x{tenor_label(sw.tenor)} 스왑션 · {side_ko}",
                        label, "accent"),
            _local_chip(f"{_ko(_OPTION_MODELS[model])}: {_vol_text_ko(model, vol_in)}",
                        f"{model}: {vol_text}"),
            _src_chip("curve", panel.source),
            _local_chip(f"곡선 기준일 {curve.date}", f"curve {curve.date}"),
            _local_chip(f"연금계수 {rep.annuity:.4f}", f"annuity {rep.annuity:.4f}"),
        ], spacing=6, run_spacing=6, wrap=True))
        if rep.note:
            blocks.append(notice(rep.note, "muted"))
        payload = {
            "instrument": label, "expiry": sw.expiry, "tenor": sw.tenor, "payer": payer,
            "notional": notional, "model": model, "vol": vol, "forward": rep.forward,
            "strike": rep.strike, "annuity": rep.annuity, "premium": rep.premium,
            "premium_bp": rep.premium_bp, "delta_per_bp": rep.delta, "gamma": rep.gamma,
            "vega": rep.vega, "vega_unit": rep.vega_unit, "theta_1d": rep.theta_1d,
            "other_model_vol": (rep.other_model_vol if math.isfinite(rep.other_model_vol)
                                else None),
            "other_model_status": rep.other_model_status,
            "other_model_reason": rep.other_model_reason,
            "curve_date": curve.date, "curve_source": panel.source, "note": rep.note,
        }
        blocks.append(analysis_panel(page, kind="rates_swaption",
                                     narrative=insights.narrate_swaption(rep),
                                     payload_fn=lambda p=payload: p))
        return blocks

    rep = price_cap_floor(curve, tenor, strike, vol=vol, model=model, cap=kind == "cap",
                          notional=notional)
    dearest = max(rep.caplets, key=lambda c: c[3]) if rep.caplets else None
    blocks.append(ft.Row([
        stat("Strike (ATM)" if strike is None else "Strike", _pct(rep.strike, 3)),
        stat("ATM (par swap)", _pct(rep.atm_strike, 3)),
        stat("Premium", _money(rep.premium)),
        stat("Premium (bp of notional)", f"{rep.premium_bp:.1f}bp"),
        stat("Caplets", str(len(rep.caplets))),
        stat("Dearest caplet",
             f"{tenor_label(dearest[0])}-{tenor_label(dearest[1])}: {_money(dearest[3])}"
             if dearest else "—"),
    ], spacing=8, run_spacing=8, wrap=True))
    kind_ko = {"cap": "캡", "floor": "플로어"}.get(kind, kind)
    blocks.append(ft.Row([
        _local_chip(f"{tenor_label(tenor)} {kind_ko}", f"{tenor_label(tenor)} {kind}", "accent"),
        _local_chip(f"{_ko(_OPTION_MODELS[model])}: {_vol_text_ko(model, vol_in)}",
                    f"{model}: {vol_text}"),
        _src_chip("curve", panel.source),
        _local_chip(f"곡선 기준일 {curve.date}", f"curve {curve.date}"),
        _local_chip(f"명목금액 {_money(rep.notional)}", f"notional {_money(rep.notional)}"),
    ], spacing=6, run_spacing=6, wrap=True))
    blocks.append(card(fcharts.caplet_chart(rep)))
    blocks.append(_table(["Start", "End", "Forward", "Premium"],
                         [[f"{a:.2f}y", f"{b:.2f}y", _pct(f, 3), _money(p)]
                          for a, b, f, p in rep.caplets],
                         headers_ko={"Start": "시작", "End": "종료", "Forward": "선도금리",
                                     "Premium": "프리미엄"}))
    if rep.note:
        blocks.append(notice(rep.note, "muted"))
    payload = {
        "instrument": f"{tenor_label(tenor)} {kind}", "tenor": tenor, "notional": notional,
        "model": model, "vol": vol, "strike": rep.strike, "atm_strike": rep.atm_strike,
        "premium": rep.premium, "premium_bp": rep.premium_bp,
        "caplets": [{"start": a, "end": b, "forward": f, "premium": p}
                    for a, b, f, p in rep.caplets],
        "curve_date": curve.date, "curve_source": panel.source, "note": rep.note,
    }
    blocks.append(analysis_panel(page, kind="rates_cap_floor",
                                 narrative=insights.narrate_cap_floor(rep),
                                 payload_fn=lambda p=payload: p))
    return blocks


def _run_sim(page, *, source: str, model: str, horizon: float, n_paths: int,
             threshold_pct: float | None, instrument: str, instr_tenor_text: str,
             coupon_pct: float) -> list[ft.Control]:
    """instrument: none | bond | swap — what to revalue at the horizon."""
    series = load_short_rate("USD", source=source)
    panel, curve = _curve(source)
    params = calibrate(series, model=model)
    thr = None if threshold_pct is None else threshold_pct / 100.0
    sim = simulate(params, horizon=horizon, n_paths=n_paths, threshold=thr, curve=curve)
    hpv, what = None, "none"
    if instrument == "bond":
        bond = Bond(coupon=coupon_pct / 100.0, maturity=parse_tenor(instr_tenor_text))
        hpv = horizon_pv_distribution(sim.params, sim, kind="bond", bond=bond, curve=curve)
        what = f"{_pct(bond.coupon)} {tenor_label(bond.maturity)} bond"
    elif instrument == "swap":
        swap = Swap(tenor=parse_tenor(instr_tenor_text))
        hpv = horizon_pv_distribution(sim.params, sim, kind="swap", swap=swap, curve=curve)
        what = swap.label
    p = sim.params
    sigma = f"{p.sigma:.3f} (sqrt-r)" if model == "cir" else f"{p.sigma / BP:.0f}bp/yr"
    blocks = (_synthetic_notice(series.source, series.note, "short rate")
              + _synthetic_notice(panel.source, panel.note, "curve"))
    blocks.append(ft.Row([
        stat("Model", _MODEL_LABELS.get(model, model)),
        stat("Mean reversion (kappa)", f"{p.kappa:.2f}/yr"),
        stat("Half-life", f"{math.log(2) / p.kappa:.1f}y"),
        stat("Long-run mean (theta)", _pct(p.theta)), stat("Volatility (sigma)", sigma),
        stat("Current rate (r0)", _pct(p.r0)),
        _local_stat(f"{horizon:g}년 후 평균", f"Mean at {horizon:g}y", _pct(sim.mean_terminal)),
        stat("90% range", f"{_pct(sim.p05)} – {_pct(sim.p95)}"),
    ] + ([_local_stat(f"{_pct(thr)} 초과 확률", f"P(> {_pct(thr)})",
                      f"{sim.prob_above * 100:.0f}%", token="accent")]
         if sim.prob_above is not None else []), spacing=8, run_spacing=8, wrap=True))
    blocks.append(ft.Row([
        _src_chip(series.id, series.source),
        _local_chip(f"{series.first_date} → {series.last_date}",
                    f"{series.first_date} → {series.last_date}"),
        _local_chip(f"관측 {len(series)}개", f"{len(series)} obs"), _src_chip("curve", panel.source),
        _local_chip(f"경로 {sim.n_paths:,}개", f"{sim.n_paths:,} paths"),
        _local_chip("난수 시드 7", "seed 7"),
    ], spacing=6, run_spacing=6, wrap=True))
    blocks.append(card(fcharts.rate_fan_chart(sim)))
    zero_header = f"Model zero at {horizon:g}y (median path)"
    blocks.append(_table(["Tenor", zero_header],
                         [[tenor_label(t), _pct(z, 3)] for t, z in sim.model_curve_at_horizon],
                         headers_ko={"Tenor": "만기",
                                     zero_header: f"{horizon:g}년 후 모형 무이표 금리 (중앙 경로)"}))
    if hpv is not None:
        length = tenor_label(parse_tenor(instr_tenor_text))
        what_ko = (f"{_pct(coupon_pct / 100.0)} {length} 채권" if instrument == "bond"
                   else f"{length} 고정금리 지급 스왑")
        blocks.append(ft.Row([
            _local_stat("재평가 상품", "Revalued", what, value_ko=what_ko, token="accent"),
            stat("Mean PV", _money(hpv.mean)),
            stat("90% range", f"{_money(hpv.p05)} – {_money(hpv.p95)}"),
            stat("VaR 95 (loss)", _money(hpv.var95), token="error" if hpv.var95 > 0 else "text"),
            stat("CVaR 95", _money(hpv.cvar95)),
        ], spacing=8, run_spacing=8, wrap=True))
        blocks.append(card(fcharts.horizon_pv_hist(hpv)))
    payload = {
        "model": model, "horizon": horizon, "n_paths": sim.n_paths,
        "params": {"kappa": p.kappa, "theta": p.theta, "sigma": p.sigma, "r0": p.r0,
                   "note": p.note},
        "series": {"id": series.id, "source": series.source, "first": series.first_date,
                   "last": series.last_date, "n": len(series), "note": series.note},
        "mean_terminal": sim.mean_terminal, "p05": sim.p05, "p95": sim.p95,
        "threshold": thr, "prob_above": sim.prob_above,
        "model_curve_at_horizon": {tenor_label(t): float(z)
                                   for t, z in sim.model_curve_at_horizon},
        "revalued": what,
        "horizon_pv": ({"mean": hpv.mean, "p05": hpv.p05, "p95": hpv.p95,
                        "var95": hpv.var95, "cvar95": hpv.cvar95, "note": hpv.note}
                       if hpv is not None else None),
        "curve_source": panel.source, "note": sim.note,
    }
    blocks.append(analysis_panel(page, kind="rates_simulation",
                                 narrative=insights.narrate_ratesim(sim, hpv),
                                 payload_fn=lambda p=payload: p))
    return blocks


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
def build_rates_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()

    def localize(control: ft.Control) -> None:
        """Re-apply the page language to captions changed after the first translation."""
        ctx = getattr(page, "qg_locale", None)
        if isinstance(ctx, LocaleContext):
            translate_controls(control, ctx)

    def tf(label: str, width: int, value: str = "", hint: str = ""):
        return ft.TextField(label=label, width=width, value=value, hint_text=hint or None,
                            border_radius=RADII["md"])

    def nf(label: str, width: int, value: str = "", hint: str = ""):
        return number_field(label, value, width=width, hint_text=hint or None)

    def dd(label: str, width: int, value: str, options: list[tuple[str, str]], on_select=None):
        return ft.Dropdown(label=label, width=width, value=value, on_select=on_select,
                           border_radius=RADII["md"],
                           options=[ft.dropdown.Option(k, v) for k, v in options])

    def fields(*controls: ft.Control) -> ft.Row:
        # Every input is one height (no helper lines), so the boxes share one baseline.
        return ft.Row(list(controls), spacing=12, run_spacing=12, wrap=True,
                      vertical_alignment=ft.CrossAxisAlignment.START)

    def tool_block(row: ft.Row, below: ft.Control, visible: bool) -> ft.Column:
        return ft.Column([row, below], spacing=8, visible=visible)

    def how_to(text: str) -> ft.Text:
        return ft.Text(text, size=12, color=pal.muted)

    # The provider is chosen automatically (FRED, synthetic fallback). The selector stays in the
    # tree, hidden, so tests and self-checks can still pin it; the result chips say who answered.
    source = dd("Curve source", 250, "auto", _SOURCES)
    source.visible = False

    # Yield curve: the method dropdown and what the chosen method assumes.
    method_name = ft.Text(size=15, weight=ft.FontWeight.W_600, color=pal.text)
    method_kind = ft.Container()
    method_text = ft.Text(size=13, color=pal.text)
    method_info = ft.Container(
        ft.Column([ft.Row([method_name, method_kind], spacing=10, wrap=True,
                          vertical_alignment=ft.CrossAxisAlignment.CENTER),
                   method_text], spacing=6),
        padding=ft.Padding(16, 12, 16, 12), bgcolor=pal.surface_2,
        border=ft.Border.all(1, pal.border), border_radius=RADII["md"])

    def describe(e=None) -> None:
        chosen = method.value or "bootstrap"
        exact = chosen in EXACT_METHODS
        method_name.value = METHOD_NAMES.get(chosen, chosen)
        method_kind.content = chip(_KIND_TEXT[exact], "success" if exact else "accent")
        method_text.value = _METHOD_TEXT.get(chosen, "")
        if e is not None:
            localize(method_info)
            page.update()

    method = dd("Curve method", 300, "bootstrap", _METHODS, on_select=describe)
    describe()
    lookback = nf("Lookback (sessions)", 190, "20")
    curve_block = tool_block(fields(method, lookback), method_info, True)
    # Swap pricer
    swap_tenor = tf("Swap tenor", 150, "10y", hint="10y or 5y5y")
    swap_fixed = nf("Fixed rate %", 150, hint="blank = par")
    swap_notional = nf("Notional", 180, "1000000")
    swap_side = dd("Side", 190, "pay", [("pay", "Pay fixed"), ("receive", "Receive fixed")])
    swap_block = tool_block(
        fields(swap_tenor, swap_fixed, swap_notional, swap_side),
        how_to("Tenor: 10y for a spot swap, 5y5y for a 5-year swap starting in 5 years. "
               "Leave the fixed rate blank to price at the par rate."), False)
    # Swaption / cap-floor

    def vol_unit(e=None) -> None:
        # The unit follows the model; a default left in place follows too, so 80bp never
        # silently becomes 80% (typed values are kept).
        chosen = opt_model.value or "bachelier"
        other = "black" if chosen == "bachelier" else "bachelier"
        opt_vol.label = _VOL_LABELS[chosen]
        if (opt_vol.value or "").strip() in ("", _VOL_DEFAULTS[other]):
            opt_vol.value = _VOL_DEFAULTS[chosen]
        if e is not None:
            localize(opt_vol)
            page.update()

    opt_kind = dd("Instrument", 140, "swaption",
                  [("swaption", "Swaption"), ("cap", "Cap"), ("floor", "Floor")])
    opt_expiry = tf("Option expiry", 130, "1y")
    opt_tenor = tf("Swap / cap length", 150, "5y")
    opt_strike = nf("Strike %", 120, hint="blank = ATM")
    opt_side = dd("Swaption side", 170, "payer", [("payer", "Payer"), ("receiver", "Receiver")])
    opt_model = dd("Option model", 180, "bachelier", list(_OPTION_MODELS.items()),
                   on_select=vol_unit)
    opt_vol = nf(_VOL_LABELS["bachelier"], 150, _VOL_DEFAULTS["bachelier"])
    opt_notional = nf("Notional", 160, "1000000")
    opt_block = tool_block(
        fields(opt_kind, opt_expiry, opt_tenor, opt_strike, opt_side, opt_model, opt_vol,
               opt_notional),
        how_to("Option expiry applies to swaptions only. Length is the underlying swap, or the "
               "whole cap or floor. Leave the strike blank for at-the-money."), False)
    # Rate simulation
    sim_model = dd("Rate model", 170, "vasicek", [(m, _MODEL_LABELS[m]) for m in MODELS])
    sim_horizon = nf("Horizon (years)", 150, "1")
    sim_paths = nf("Paths", 130, "5000")
    sim_threshold = nf("Threshold % (optional)", 200)
    sim_instr = dd("Revalue", 180, "none", [("none", "Nothing"), ("bond", "Bond"),
                                            ("swap", "Payer swap")])
    sim_tenor = tf("Instrument tenor", 160, "10y")
    sim_coupon = nf("Bond coupon %", 150, "4")
    sim_block = tool_block(
        fields(sim_model, sim_horizon, sim_paths, sim_threshold, sim_instr, sim_tenor, sim_coupon),
        how_to("The model is calibrated on the SOFR history. The threshold (optional) adds the "
               "probability of ending above it; tenor and coupon are used only when an "
               "instrument is revalued."), False)
    blocks_by_tool = {"curve": curve_block, "swap": swap_block, "option": opt_block,
                      "sim": sim_block}

    def switch(e=None) -> None:
        for key, block in blocks_by_tool.items():
            block.visible = key == (tool.value or "curve")
        if e is not None:                       # a real switch, not the initial layout
            result_host.controls = []           # the old tool's results would mislead
        page.update()

    tool = ft.Dropdown(label="Tool", width=240, value="curve", on_select=switch,
                       border_radius=RADII["md"],
                       options=[ft.dropdown.Option(k, v) for k, v in _TOOLS])
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    result_host = ft.Column(spacing=16)

    def compute() -> list[ft.Control]:
        src, which = source.value or "auto", tool.value or "curve"
        if which == "curve":
            return _run_curve(page, source=src, method=method.value or "bootstrap",
                              lookback=int(_num(lookback.value, 20, "Lookback")))
        if which == "swap":
            return _run_swap(page, source=src, tenor_text=swap_tenor.value or "10y",
                             fixed_pct=_num(swap_fixed.value, None, "Fixed rate"),
                             notional=_num(swap_notional.value, 1e6, "Notional"),
                             pay_fixed=(swap_side.value or "pay") == "pay")
        if which == "option":
            model = opt_model.value or "bachelier"
            return _run_option(page, source=src, kind=opt_kind.value or "swaption",
                               expiry_text=opt_expiry.value or "1y",
                               tenor_text=opt_tenor.value or "5y",
                               strike_pct=_num(opt_strike.value, None, "Strike"),
                               payer=(opt_side.value or "payer") == "payer", model=model,
                               vol_in=_num(opt_vol.value, 80.0 if model == "bachelier" else 30.0,
                                           "Vol"),
                               notional=_num(opt_notional.value, 1e6, "Notional"))
        return _run_sim(page, source=src, model=sim_model.value or "vasicek",
                        horizon=_num(sim_horizon.value, 1.0, "Horizon"),
                        n_paths=int(_num(sim_paths.value, 5000, "Paths")),
                        threshold_pct=_num(sim_threshold.value, None, "Threshold"),
                        instrument=sim_instr.value or "none",
                        instr_tenor_text=sim_tenor.value or "10y",
                        coupon_pct=_num(sim_coupon.value, 4.0, "Coupon"))

    def run(e=None) -> None:
        busy.visible = True
        result_host.controls = []
        page.update()

        def worker():
            try:
                blocks = compute()
            except (FICCError, ValueError) as exc:
                blocks = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]
            except Exception as exc:
                blocks = [notice(f"{type(exc).__name__}: {exc}", "error",
                                 icon=ft.Icons.ERROR_OUTLINE)]
            result_host.controls = blocks
            localize(result_host)
            busy.visible = False
            page.update()

        page.run_thread(worker)

    result_host.controls = [empty_state(
        "Pick a tool and press Run",
        "The curve comes from FRED (keyless); with no connection every tool runs on a "
        "clearly labeled synthetic curve, so everything here works immediately.",
        icon=ft.Icons.SSID_CHART_OUTLINED)]

    return ft.Column([
        section("Rates", subtitle="Yield curve, swaps, swaptions and caps, short-rate "
                                  "simulation — single-curve, ACT/365F, decimals inside."),
        ft.Row([tool, source, ft.Button("Run", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run),
                busy], spacing=12, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        curve_block, swap_block, opt_block, sim_block,
        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)


if __name__ == "__main__":
    class _Page:                                      # enough of ft.Page for the workers
        def update(self) -> None:
            pass

        def run_thread(self, fn) -> None:
            fn()

    pg = _Page()

    def _is_error(block) -> bool:
        return (isinstance(block, ft.Container) and isinstance(block.content, ft.Row)
                and getattr(block.content.controls[0], "icon", "") == ft.Icons.ERROR_OUTLINE)

    def _has_chart(block) -> bool:
        content = getattr(block, "content", None)
        return isinstance(content, ft.Image) or isinstance(getattr(content, "image", None), ft.Image)

    results = [
        _run_curve(pg, source="synthetic", method="nelson_siegel", lookback=20),
        _run_swap(pg, source="synthetic", tenor_text="5y5y", fixed_pct=None, notional=1e6,
                  pay_fixed=True),
        _run_swap(pg, source="synthetic", tenor_text="10y", fixed_pct=4.0, notional=2.5e6,
                  pay_fixed=False),
        _run_option(pg, source="synthetic", kind="swaption", expiry_text="1y", tenor_text="5y",
                    strike_pct=None, payer=True, model="bachelier", vol_in=80, notional=1e6),
        _run_option(pg, source="synthetic", kind="cap", expiry_text="1y", tenor_text="5y",
                    strike_pct=4.5, payer=True, model="black", vol_in=30, notional=1e6),
        _run_sim(pg, source="synthetic", model="vasicek", horizon=1.0, n_paths=500,
                 threshold_pct=5.0, instrument="bond", instr_tenor_text="10y", coupon_pct=4.0),
        _run_sim(pg, source="synthetic", model="hull_white", horizon=0.5, n_paths=300,
                 threshold_pct=None, instrument="swap", instr_tenor_text="5y", coupon_pct=4.0),
    ] + [_run_curve(pg, source="synthetic", method=m, lookback=20) for m in CURVE_METHODS]
    for i, blocks in enumerate(results):
        assert len(blocks) >= 4, len(blocks)
        assert not any(_is_error(b) for b in blocks)
        loud, reason = blocks[0].controls                  # the loud synthetic notice ...
        assert loud.content.controls[1].value.startswith("Synthetic"), loud
        assert isinstance(reason, ft.ExpansionTile)        # ... and the provider's reason, kept
        assert isinstance(blocks[-1], ft.Container)        # analysis panel closes every result
        if i != 3:                                         # the swaption has no chart of its own
            assert any(_has_chart(b) for b in blocks), i
    # Bad numbers surface as ValueError (caught by the page), never a crash.
    try:
        _num("abc", None, "Notional")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    # Wiring: the built page runs end to end on the fake page with the synthetic source.
    col = build_rates_page(pg)
    top = col.controls[1].controls                        # [tool, source (hidden), Run, busy]
    assert top[1].visible is False and top[1].value == "auto"
    assert [o.key for o in col.controls[2].controls[0].controls[0].options] == list(CURVE_METHODS)
    top[1].value = "synthetic"
    top[0].value = "swap"
    top[2].on_click(None)
    host = col.controls[-1].controls[0]
    assert len(host.controls) >= 4 and not _is_error(host.controls[0]), host.controls
    top[0].value = "curve"
    col.controls[3].controls[0].controls[0].value = "abc"  # swap tenor is irrelevant now
    col.controls[2].controls[0].controls[1].value = "abc"  # lookback: bad number
    top[2].on_click(None)
    assert _is_error(host.controls[0])
    print("ok")
