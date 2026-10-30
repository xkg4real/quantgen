"""ETF — NAV and premium, the basket, leveraged-fund drag, and the sleeve
rules (trend switch, volatility target) with the study's verdict beside them.

KRX ETFs come from the KIS ETF domain (`data.kis_markets`): quote with NAV,
tracking error and LP holdings, the daily price-versus-NAV history with the
premium, and the constituent basket. US ETFs come through the history router
(FMP closes adjusted for splits and dividends) without NAV. The sleeve rules
never run on the raw NAV-series close: for a KRX fund they use KIS 수정주가, so
a unit split is not booked as a crash. The leveraged-fund drag uses the app's
GARCH(1,1)-t variance term structure on the KOSPI200 index (Avellaneda–Zhang).
"""
from __future__ import annotations

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
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.components import card, chip, empty_state, notice, section, stat
import ui.xcharts as xc
from core.research.etf_workflow import _clean, analyze as _analyze, narrative, payload, LETF, _CARD_FOR

ROOT = Path(__file__).resolve().parents[1]


def analyze(code: str, *, days: int = 504, source: str = "auto") -> dict:
    """Retain the browser adapter's injectable provider boundary."""
    return _analyze(code, days=days, source=source,
                    history_loader=load_history, card_loader=load_cards)


def build_etf_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    code = ft.TextField(label="ETF code", value="069500", hint_text="069500, 122630, SPY", width=160, border_radius=RADII["md"])
    days = ft.TextField(label="Sessions", value="504", width=110, border_radius=RADII["md"])
    source = ft.Dropdown(label="Source", width=220, value="auto",
                         options=[ft.dropdown.Option("auto", "Auto (KIS for KRX codes)"), ft.dropdown.Option("synthetic", "Synthetic demo")])
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=14)

    def run(e=None) -> None:
        busy.visible = True; host.controls = []; page.update()

        def worker():
            try:
                a = analyze(code.value or "069500", days=int(float(days.value or "504")), source=source.value or "auto")
            except (HistoryError, ValueError) as exc:
                host.controls = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]; busy.visible = False; page.update(); return
            except Exception as exc:
                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            blocks: list[ft.Control] = []
            if a.get("data_source") == "SYNTHETIC":
                blocks.append(notice("Synthetic data: " + a.get("note", ""), "error", icon=ft.Icons.SCIENCE_OUTLINED))
            q = a.get("quote")
            if q:
                blocks.append(ft.Row([
                    stat("Price", f"{q['price']:,.0f}"), stat("NAV", f"{q['nav']:,.2f}"),
                    stat("Premium", f"{q['premium_pct']:+.2f}%", token="error" if abs(q["premium_pct"] or 0) > 0.5 else "text"),
                    stat("Tracking error", f"{q['tracking_error_pct']:.2f}%"), stat("AUM", f"{(q['aum'] or 0) / 1e8:,.0f}억"),
                    stat("CU shares", f"{q['cu_units']:,.0f}"), stat("LP holding", f"{q['lp_holding_pct']:.1f}%"),
                    stat("Listed", q["listed"]),
                ], spacing=10, wrap=True))
            ps = a.get("premium_stats")
            if ps:
                blocks.append(notice(decay_text(ps.get('decay')), "accent"))
                blocks.append(ft.Row([chip(f"premium z {ps['z']:+.2f}", "accent"), chip(f"|premium| mean {ps['abs_mean']:.2f}%"),
                                      chip(f"AR(1) amplitude half-life {decay_value(ps.get('decay'))} observations"), chip(f"ADF p {ps['adf_p']:.3f}"),
                                      chip(f"source: {a['data_source']}", "success" if a["data_source"] != "SYNTHETIC" else "muted")],
                                     spacing=6, wrap=True))
                blocks.append(card(xc.premium_chart(a["dates"], a["price"], a["nav"], a["premium_pct"],
                                                    title=f"{a['code']} price vs NAV")))
            lt = a.get("letf")
            if lt and "rows" in lt:
                blocks.append(ft.Row([stat(f"{lt['name']} drag, last-quarter vol", f"{lt['last_quarter_drag_bp']:+.0f} bp / qtr",
                                           token="error", tooltip=f"realised vol {lt['last_quarter_vol']:.1%}: the study's better reference")] +
                                     [stat(f"GARCH drag {r['sessions']}d", f"{r['drag_bp']:+.0f} bp",
                                           tooltip=f"variance {r['variance_bp']:+.0f} bp, fee {r['fee_bp']:+.0f} bp")
                                      for r in lt["rows"]] + [stat("Index cond. vol", f"{lt['cond_vol']:.1%}"),
                                                              stat("ν", f"{lt['nu']:.1f}"),
                                                              stat("Study verdict: GARCH drag", lt.get("verdict", "not run"),
                                                                   token="success" if lt.get("verdict") == "PASS" else "error",
                                                                   tooltip=lt.get("verdict_reason", ""))], spacing=10, wrap=True))
            sl = a.get("sleeves")
            if sl:
                blocks.append(ft.Row([
                    stat("Trend switch Sharpe", f"{sl['trend']['sharpe']:.2f}"), stat("Trend MDD", f"{sl['trend']['max_drawdown']:.0%}"),
                    stat("Vol-target Sharpe", f"{sl['vol_target']['sharpe']:.2f}"), stat("Buy & hold Sharpe", f"{sl['buy_hold']['sharpe']:.2f}"),
                    stat("B&H MDD", f"{sl['buy_hold']['max_drawdown']:.0%}"),
                    stat("Study verdict: trend", a["verdicts"]["trend"], token="success" if a["verdicts"]["trend"] == "PASS" else "error",
                         tooltip=a["verdict_reasons"]["trend"]),
                    stat("Study verdict: vol target", a["verdicts"]["vol"], token="success" if a["verdicts"]["vol"] == "PASS" else "error",
                         tooltip=a["verdict_reasons"]["vol"]),
                ], spacing=10, wrap=True))
                blocks.append(card(xc.equity_chart(a.get("sleeve_dates", a["dates"]), sl["equity_trend"], sl["equity_bh"],
                                                   title=f"10-month trend switch vs buy-and-hold ({sl['cost_bps']:.0f} bp per side)")))
            comps = a.get("components") or []
            if comps:
                top = sorted(comps, key=lambda c: -(c["weight_pct"] or 0))[:10]
                blocks.append(card(ft.Column([ft.Text("Top constituents", size=13, weight=ft.FontWeight.W_600, color=pal.text)] +
                                             [ft.Text(f"{c['code']}  {c['name']}  {c['weight_pct']:.2f}%", size=12, color=pal.text)
                                              for c in top], spacing=3)))
            blocks.append(analysis_panel(page, kind="etf_structure", narrative=narrative(a),
                                         payload_fn=lambda p=payload(a): p, deep_fn=insights.deep_analysis))
            host.controls = blocks; busy.visible = False; page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Pick an ETF", "NAV premium and its half-life, the basket, the leveraged-fund drag "
                                 "from the GARCH variance term structure, and the trend / vol-target sleeve rules with "
                                 "the validation study's verdict.", icon=ft.Icons.INVENTORY_2_OUTLINED,
                                 action=ft.Button("Open Settings", on_click=lambda e: on_open_settings()) if on_open_settings else None)]
    return ft.Column([
        section("ETF", subtitle="NAV premium, basket, leveraged-fund drag, sleeve rules."),
        ft.Row([code, days, source, ft.Button("Analyze", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy], spacing=10, wrap=True),
        ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=14, expand=True)


if __name__ == "__main__":
    a = analyze("122630", days=504, source="synthetic")
    assert a["data_source"] == "SYNTHETIC" and "sleeves" in a and "letf" in a
    assert "rows" in a["letf"] and a["letf"]["rows"][0]["drag_bp"] < 0
    t = narrative(a)
    assert "SYNTHETIC" in t and "drag" in t and payload(a)["letf"]["beta"] == 2.0
    print("ok")
