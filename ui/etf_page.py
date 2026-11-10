"""ETF — NAV and premium, the basket, leveraged-fund drag, and the sleeve
rules (trend switch, volatility target) with the study's verdict beside them.

KRX ETFs come from the KIS ETF domain (`data.kis_markets`): quote with NAV,
tracking error and LP holdings, the daily price-versus-NAV history with the
premium, and the constituent basket. US ETFs come through the history router
(FMP closes adjusted for splits and dividends) without NAV. The sleeve rules
never run on the raw NAV-series close: for a KRX fund they use KIS 수정주가, so
a unit split is not booked as a crash. The leveraged-fund drag uses the app's
GARCH(1,1)-t variance term structure on the fund's mapped index (Avellaneda–Zhang).
"""
from __future__ import annotations

from core.research.letf_disclosure import letf_text, letf_unavailable_text
import math
from pathlib import Path
from typing import Callable, Optional

import flet as ft
import numpy as np

import config
from core.ficc.common import BP
from core.ficc.equity_deriv import letf_drag
from core.quant import insights
from core.quant import strategies as S
from core.quant.history import HistoryError, load_history, synthetic_history
from core.quant.validate import load_cards
from core.research.decay_disclosure import decay_value, decay_text
from core.research.sleeve_disclosure import (SHARPE_CONVENTIONS_POINTER, conventions_korean, conventions_text,
                                             sharpe_text, sharpe_tooltip)
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.narrative_sections import korean, localized
from quantgen_desktop.market_narrative_language import etf_korean
from ui.components import card, empty_state, notice, section, stat
from ui.ficc_widgets import action, form_row, hide_source, ko_notice, ko_stat, ko_verdict, lchip, synthetic_notice
import ui.xcharts as xc
from core.research.etf_workflow import _clean, analyze as _analyze, narrative, payload, LETF, _CARD_FOR

ROOT = Path(__file__).resolve().parents[1]


def analyze(code: str, *, days: int = 504, source: str = "auto", **letf_options) -> dict:
    """Retain the browser adapter's injectable provider boundary.

    The page shows no source selector, so a history the workflow asks for with
    `auto` is fetched with `best`: the same route while FMP / KIS answer, but
    keyless Yahoo before a labelled synthetic series when their keys are
    missing. KIS ETF quote/NAV data still comes first for KRX codes when KIS
    is configured; an explicit source ('kis', 'synthetic') passes through."""
    def history(symbol, *, source, days):
        return load_history(symbol, source="best" if source == "auto" else source, days=days)
    return _analyze(code, days=days, source=source,
                    history_loader=history, card_loader=load_cards, **letf_options)


def build_etf_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    code = ft.TextField(label="ETF code", value="069500", hint_text="069500, 122630, SPY", width=160, border_radius=RADII["md"])
    days = ft.TextField(label="Sessions", value="504", width=140, border_radius=RADII["md"],
                        text_align=ft.TextAlign.RIGHT)
    # The app chooses the provider itself (KIS for KRX codes, then keyless
    # Yahoo, else a labelled synthetic series); the selector stays for tests.
    source = hide_source(ft.Dropdown(label="Source", width=220, value="auto",
                                     options=[ft.dropdown.Option("auto", "Auto (KIS for KRX codes)"),
                                              ft.dropdown.Option("synthetic", "Synthetic demo")]), "auto")
    benchmark = ft.Dropdown(label="LETF comparison", width=280, value="zero_rate_reference",
                           options=[ft.dropdown.Option("zero_rate_reference", "Zero-rate reference (legacy)"),
                                    ft.dropdown.Option("total_return", "Total-return scenario"),
                                    ft.dropdown.Option("price_return", "Price-return scenario")])
    funding = ft.TextField(label="Annual funding rate (%)", value="", width=220, disabled=True,
                          hint_text="Explicit assumption, e.g. 3.21", border_radius=RADII["md"],
                          text_align=ft.TextAlign.RIGHT)
    fee = ft.TextField(label="Annual fee (%)", value="", width=180, disabled=True,
                      hint_text="Explicit assumption", border_radius=RADII["md"], text_align=ft.TextAlign.RIGHT)
    dividend = ft.TextField(label="Annual dividend yield (%)", value="", width=240, disabled=True,
                           hint_text="Required for price return", border_radius=RADII["md"],
                           text_align=ft.TextAlign.RIGHT)

    def comparison_changed(_event=None):
        funding.disabled = fee.disabled = benchmark.value == "zero_rate_reference"
        dividend.disabled = benchmark.value != "price_return"
        page.update()

    benchmark.on_select = comparison_changed
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=16)

    def run(e=None) -> None:
        busy.visible = True; host.controls = []; page.update()

        def worker():
            try:
                options = {}
                if benchmark.value != "zero_rate_reference":
                    def annual(field):
                        if not (field.value or "").strip():
                            raise ValueError("Enter explicit funding and fee assumptions; price-return also needs a dividend yield.")
                        return float(field.value) / 100.0
                    options = {"letf_benchmark": benchmark.value, "letf_funding_rate": annual(funding),
                               "letf_annual_fee": annual(fee),
                               "letf_dividend_yield": annual(dividend) if benchmark.value == "price_return" else None}
                a = analyze(code.value or "069500", days=int(float(days.value or "504")), source=source.value or "auto", **options)
            except (HistoryError, ValueError) as exc:
                host.controls = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]; busy.visible = False; page.update(); return
            except Exception as exc:
                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            blocks: list[ft.Control] = []
            if a.get("data_source") == "SYNTHETIC":
                blocks.append(synthetic_notice(
                    "합성 데이터: 가격 이력을 제공처에서 받지 못해 시뮬레이션한 시계열로 계산했습니다. "
                    "아래 숫자는 계산 방식의 시연이며 시장 시세가 아닙니다.",
                    "Synthetic data: the price history is simulated because no provider answered; the numbers "
                    "below demonstrate the mechanics, not a market read.", a.get("note", "")))
            q = a.get("quote")
            if q:
                blocks.append(ft.Row([
                    stat("Price", f"{q['price']:,.0f}"), stat("NAV", f"{q['nav']:,.2f}"),
                    ko_stat(stat("Premium", f"{q['premium_pct']:+.2f}%", token="error" if abs(q["premium_pct"] or 0) > 0.5 else "text"),
                            "괴리율 (시장가격 vs NAV)"),
                    stat("Tracking error", f"{q['tracking_error_pct']:.2f}%"), stat("AUM", f"{(q['aum'] or 0) / 1e8:,.0f}억"),
                    stat("CU shares", f"{q['cu_units']:,.0f}"), stat("LP holding", f"{q['lp_holding_pct']:.1f}%"),
                    stat("Listed", q["listed"]),
                ], spacing=12, run_spacing=12, wrap=True))
            ps = a.get("premium_stats")
            if ps:
                blocks.append(notice(decay_text(ps.get('decay')), "accent"))
                half_life = decay_value(ps.get('decay'))
                src = a['data_source']
                blocks.append(ft.Row([
                    lchip(f"괴리율 z {ps['z']:+.2f}", f"premium z {ps['z']:+.2f}", "accent"),
                    lchip(f"|괴리율| 평균 {ps['abs_mean']:.2f}%", f"|premium| mean {ps['abs_mean']:.2f}%"),
                    lchip(f"AR(1) 진폭 반감기 {half_life} 관측치", f"AR(1) amplitude half-life {half_life} observations"),
                    lchip(f"ADF p {ps['adf_p']:.3f}", f"ADF p {ps['adf_p']:.3f}"),
                    lchip(f"출처: {'합성 데이터' if src == 'SYNTHETIC' else src}", f"source: {src}",
                          "success" if src != "SYNTHETIC" else "muted")],
                    spacing=8, wrap=True))
                blocks.append(card(xc.premium_chart(a["dates"], a["price"], a["nav"], a["premium_pct"],
                                                    title=f"{a['code']} price vs NAV")))
            lt = a.get("letf")
            if lt and "rows" in lt:
                blocks.append(notice(letf_text(lt), "accent"))
                blocks.append(ft.Row([ko_stat(stat(f"{lt['name']} AZ proxy · prior-quarter variance", f"{lt['last_quarter_drag_bp']:+.0f} bp / qtr",
                                           token="error" if lt['last_quarter_drag_bp'] < 0 else "text", tooltip=letf_text(lt)),
                                              f"{lt['name']} AZ 근사 · 직전 분기 분산")] +
                                     [ko_stat(stat(f"GARCH variance proxy {r['sessions']} sessions", f"{r['drag_bp']:+.0f} bp",
                                           tooltip=f"variance {r['variance_bp']:+.2f} bp, funding {r.get('funding_bp', 0):+.2f} bp, "
                                                   f"fee {r['fee_bp']:+.2f} bp, dividend {r.get('dividend_bp', 0):+.2f} bp; "
                                                   f"zero-rate reference {r.get('reference_drag_bp', r['drag_bp']):+.2f} bp"),
                                              f"GARCH 분산 근사 {r['sessions']}거래일")
                                      for r in lt["rows"]] + [stat("Index cond. vol", f"{lt['cond_vol']:.1%}"),
                                                              stat("ν", f"{lt['nu']:.1f}"),
                                                              ko_verdict(stat("Historical 122630 study · not current validation", lt.get("verdict", "not run"),
                                                                   token="muted",
                                                                   tooltip=letf_text(lt) + " " + lt.get("verdict_reason", "")))],
                                     spacing=12, run_spacing=12, wrap=True))
            elif lt:
                blocks.append(notice(letf_unavailable_text(lt), "error"))
            sl = a.get("sleeves")
            if sl:
                # §10 NEW-M6-04: an undefined Sharpe shows "n/a" and says why; NEW-M6-05: a defined one carries the
                # conventions it was computed under, and a notice under the row states them.
                conventions = conventions_text(sl["conventions"]) if sl.get("conventions") else ""

                def sharpe_stat(label, key):
                    return stat(label, sharpe_text(sl[key]) or "n/a",
                                tooltip=sharpe_tooltip(sl[key]) or (SHARPE_CONVENTIONS_POINTER if conventions else ""))

                blocks.append(ft.Row([
                    sharpe_stat("Trend switch Sharpe", "trend"), stat("Trend MDD", f"{sl['trend']['max_drawdown']:.0%}"),
                    sharpe_stat("Vol-target Sharpe", "vol_target"), sharpe_stat("Buy & hold Sharpe", "buy_hold"),
                    stat("B&H MDD", f"{sl['buy_hold']['max_drawdown']:.0%}"),
                    ko_verdict(stat("Study verdict: trend", a["verdicts"]["trend"], token="success" if a["verdicts"]["trend"] == "PASS" else "error",
                                    tooltip=a["verdict_reasons"]["trend"])),
                    ko_verdict(stat("Study verdict: vol target", a["verdicts"]["vol"], token="success" if a["verdicts"]["vol"] == "PASS" else "error",
                                    tooltip=a["verdict_reasons"]["vol"])),
                ], spacing=12, run_spacing=12, wrap=True))
                if conventions:
                    blocks.append(ko_notice(notice(conventions, "accent"), conventions_korean(sl["conventions"])))
                blocks.append(card(xc.equity_chart(a.get("sleeve_dates", a["dates"]), sl["equity_trend"], sl["equity_bh"],
                                                   title=f"10-month trend switch vs buy-and-hold ({sl['cost_bps']:.0f} bp per side)")))
            comps = a.get("components") or []
            if comps:
                top = sorted(comps, key=lambda c: -(c["weight_pct"] or 0))[:10]
                blocks.append(card(ft.Column([ft.Text("Top constituents", size=13, weight=ft.FontWeight.W_600, color=pal.text)] +
                                             [ft.Text(f"{c['code']}  {c['name']}  {c['weight_pct']:.2f}%", size=12, color=pal.text)
                                              for c in top], spacing=3)))
            blocks.append(analysis_panel(page, kind="etf_structure", narrative=narrative(a),
                                         payload_fn=lambda p=payload(a): p, deep_fn=insights.deep_analysis,
                                         sections=localized(narrative(a), korean(etf_korean, a))))
            host.controls = blocks; busy.visible = False; page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Pick an ETF", "NAV premium and its half-life, the basket, the leveraged-fund drag "
                                 "from the GARCH variance term structure, and the trend / vol-target sleeve rules with "
                                 "the validation study's verdict.", icon=ft.Icons.INVENTORY_2_OUTLINED,
                                 action=ft.Button("Open Settings", on_click=lambda e: on_open_settings()) if on_open_settings else None)]
    return ft.Column([
        section("ETF", subtitle="NAV premium, basket, leveraged-fund drag, sleeve rules."),
        form_row([code, days, source, action(ft.Button("Analyze", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy)]),
        form_row([benchmark, funding, fee, dividend]),
        ft.Text("LETF inputs are annual continuous-rate assumptions, not live market observations. "
                "Price-return comparison requires dividends; total-return already includes them. "
                "The zero-rate reference preserves the previous calculation.", size=12, color=pal.muted),
        ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)


if __name__ == "__main__":
    a = analyze("122630", days=504, source="synthetic")
    assert a["data_source"] == "SYNTHETIC" and "sleeves" in a and "letf" in a
    assert "rows" in a["letf"] and a["letf"]["rows"][0]["drag_bp"] < 0
    t = narrative(a)
    assert "SYNTHETIC" in t and "drag" in t and payload(a)["letf"]["beta"] == 2.0
    print("ok")
