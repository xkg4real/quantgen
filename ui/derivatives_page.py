"""Derivatives — KOSPI200 futures basis, the option board, the volatility
surface, the risk-neutral density, the adjacent-strike box as a quote check, and the
hedger's P&L simulation for the structuring pages.

Live data comes from the KIS asset domains (`data.kis_markets`): the whole
option chain of one expiry (paged), the front futures quote with KIS's own
theoretical price, the CD 91-day rate, and the KOSPI200 index history for the
GARCH fit. Without KIS the page runs on a synthetic board and says so.

Every quantity is computed by `core.ficc.equity_deriv` and printed here in
the desk's units: index points, vol points, basis points of notional.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Callable, Optional

import flet as ft
import numpy as np

import config
from core.ficc import equity_deriv as ED
from core.ficc.common import BP, FICCError
from core.ficc.swaps import black76
from core.quant import insights
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.components import card, empty_state, notice, number_field, parse_number, section, stat
from ui.ficc_widgets import action, form_row, hide_source, ko_notice, ko_verdict, lchip, with_helper
import ui.xcharts as xc
from core.research.derivatives_workflow import synthetic_board, snapshot, narrative, payload
from core.research.quote_coverage import butterfly_display, quote_coverage_text
from core.research.option_disclosure import box_tooltip, hedge_korean, hedge_text, mfiv_strip, mfiv_text, same_vol

_SOURCES = [("kis", "KIS live (KOSPI200 board)"), ("synthetic", "Synthetic demo board")]
_ENGINES = [("gbm", "GBM at the ATM vol"), ("garch_t", "GARCH(1,1)-t on the index history")]


def build_derivatives_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    # The app picks the board itself: KIS when its keys are set, else the
    # labelled synthetic demo board. The selector stays for tests but is not shown.
    board = "kis" if config.kis_ready() else "synthetic"
    source = hide_source(ft.Dropdown(label="Board", width=260, value=board,
                                     options=[ft.dropdown.Option(k, v) for k, v in _SOURCES]), board)
    expiry = with_helper(ft.TextField(label="Expiry (YYYYMM)", hint_text="blank = nearest", width=170,
                                      border_radius=RADII["md"]), "Blank = nearest expiry")
    rate = with_helper(ft.TextField(label="Risk-free rate %", width=170, border_radius=RADII["md"],
                                    text_align=ft.TextAlign.RIGHT), "Blank = CD 91-day rate")
    engine = ft.Dropdown(label="Hedge-sim engine", width=300, value="gbm",
                         options=[ft.dropdown.Option(k, v) for k, v in _ENGINES])
    paths = number_field("Paths", "3000", width=140)
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=16)

    def run(e=None) -> None:
        busy.visible = True
        host.controls = []
        page.update()

        def worker():
            try:
                rp = parse_number(rate.value) if (rate.value or "").strip() else None
                s = snapshot(source=source.value or "kis", expiry=expiry.value or "", rate_pct=rp,
                             engine=engine.value or "gbm", n_paths=int(parse_number(paths.value or "3000")))
            except (FICCError, ValueError) as exc:
                host.controls = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            except Exception as exc:
                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            b, fit, sim, rec = s["basis"], s["svi"], s["hedge"], s["reconcile"]
            butterfly_value, butterfly_token = butterfly_display(s['quote_coverage'])
            strip = mfiv_strip(s)
            blocks: list[ft.Control] = []
            if s["source"] != "kis":
                blocks.append(notice("Synthetic board: a smile-shaped demo chain, not market quotes.", "error",
                                     icon=ft.Icons.SCIENCE_OUTLINED))
            if not s.get("live_quotes", True):
                blocks.append(ko_notice(notice(
                    f"Market closed: these are the last prints of {s['session']}, struck at different moments, "
                    "not quotes. Checks requiring two-sided quotes remain NOT_RUN without sufficient coverage.",
                    "error", icon=ft.Icons.NIGHTLIGHT_OUTLINED),
                    f"장 마감: {s['session']}의 마지막 체결가이며 서로 다른 시각에 체결된 값이라 호가가 아닙니다. "
                    "매수·매도 양방향 호가가 필요한 점검은 호가가 충분하지 않으면 NOT_RUN으로 남습니다."))
            quoted = s.get("live_quotes", True)
            near = len(s['points'])
            blocks.append(ft.Row([
                lchip(f"만기 {s['expiry']} → {s['expiry_date']}", f"expiry {s['expiry']} → {s['expiry_date']}"),
                lchip(f"기준 {s['as_of']}", f"as of {s['as_of']}"),
                lchip(f"{s.get('session', '?')} 가격", f"prices of {s.get('session', '?')}"),
                lchip(f"금리 {s['rate']:.2%} ({s['rate_source']})", f"rate {s['rate']:.2%} ({s['rate_source']})"),
                lchip(f"행사가격 {s['n_quotes']}개", f"{s['n_quotes']} strikes"),
                lchip(f"ATM 근처 {'호가' if quoted else '마지막 체결가'} {near}개",
                      f"{near} {'quoted' if quoted else 'last-print'} near-ATM", "accent")],
                spacing=8, wrap=True))
            blocks.append(ft.Row([
                stat("Forward (parity)", f"{s['F']:.2f}"), stat("Front future", f"{s['futures']['price']:.2f}"),
                stat("Basis (pts)", f"{b.basis_pts:+.2f}"), stat("Fair value", f"{b.fair:.2f}"),
                stat("Mispricing", f"{b.mispricing_bp:+.0f} bp", token="error" if abs(b.mispricing_bp) > 20 else "text"),
                stat("Implied funding", f"{b.implied_rate:.2%}"),
                stat("KIS theo gap", f"{b.theo_gap_pts:+.2f} pts" if b.theo_gap_pts is not None else "n/a"),
            ], spacing=12, run_spacing=12, wrap=True))
            blocks.append(ft.Row([
                stat("ATM IV", f"{s['atm'].iv:.1%}"),
                stat("MFIV", f"{s['mfiv'].get('vol', float('nan')):.1%}" if s["mfiv"].get("n_strikes") else "n/a",
                     tooltip=mfiv_text(strip) or "Model-free variance not computed"),
                stat("MFIV strike range", f"{strip['lower_moneyness']:+.1%} / {strip['upper_moneyness']:+.1%} of F"
                     if strip["status"] == "COMPUTED" else "n/a", token="muted",
                     tooltip="Options outside this range are omitted; the omitted wings bias MFIV downward (truncated strip)."),
                stat("SVI ρ", f"{fit.rho:+.2f}"), stat("SVI RMSE", f"{fit.rmse_volpts:.2f} pts",
                                                       token="error" if fit.rmse_volpts > 1.0 else "text"),
                stat("IV gap vs KIS", f"{rec['median_volpts']:.2f} pts", token="success" if rec["ok"] else "error",
                     tooltip="median |σ_app − σ_KIS| on quoted strikes within ±15 % of F; gate 0.5"),
                ko_verdict(stat("Butterfly viol.", butterfly_value, token=butterfly_token,
                                tooltip=quote_coverage_text(s['quote_coverage']))),
                stat("Box rate (quote check)", f"{s['box']['rate']:.2%}" if s["box"] else "n/a", tooltip=box_tooltip(s)),
                stat("RND ∫", f"{s['rnd']['integral']:.3f}"),
            ], spacing=12, run_spacing=12, wrap=True))
            blocks.append(notice(quote_coverage_text(s['quote_coverage']), "accent"))
            blocks.append(card(xc.smile_chart(s["points"], fit, s["F"], title=f"KOSPI200 {s['expiry']} smile")))
            p_samples = None
            if s.get("garch") is not None:
                from core.quant.garch import simulate_returns
                shocks, _ = simulate_returns(s["garch"], n_paths=3000, horizon=max(int(round(s["T"] * 252)), 2), seed=3,
                                             drift_daily=0.0)
                p_samples = s["futures"]["underlying_level"] * np.exp(shocks.sum(axis=1))
            blocks.append(card(xc.density_chart(s["rnd"], p_samples=p_samples)))
            blocks.append(ft.Row([
                # §10 M4-N7: at σ_true = σ_h the expected mean is 0 by construction; its sign is not coloured.
                stat("Hedge P&L (mean)", f"{sim.mean_pnl_bp:+.0f} bp",
                     token="text" if same_vol(s) else "success" if sim.mean_pnl_bp > 0 else "error",
                     tooltip="short the ATM option at σ_h, delta-hedged daily; bp of notional"
                     + ("; GBM engine at σ_true = σ_h: expected mean 0 bp by construction, the sign is Monte Carlo noise"
                        if same_vol(s) else "")),
                stat("SE", f"{sim.se_bp:.0f} bp"), stat("CVaR95", f"{sim.cvar95_bp:+.0f} bp", token="error"),
                stat("σ_h", f"{sim.sigma_hedge:.1%}"),
                stat("Break-even realised vol", f"{sim.breakeven_vol:.1%}",
                     tooltip="GBM engine: equals σ_h by construction, up to Monte Carlo noise" if same_vol(s) else ""),
                stat("Identity slope / R²", f"{sim.identity_slope:.2f} / {sim.identity_r2:.2f}"),
                stat("Engine", sim.engine),
            ], spacing=12, run_spacing=12, wrap=True))
            hedge_note = hedge_text(s)
            if hedge_note:
                blocks.append(ko_notice(notice(hedge_note, "accent"), hedge_korean(s)))
            blocks.append(analysis_panel(page, kind="kospi200_derivatives", narrative=narrative(s),
                                         payload_fn=lambda p=payload(s): p, deep_fn=insights.deep_analysis))
            host.controls = blocks
            busy.visible = False
            page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Load the board",
                                 "The nearest KOSPI200 expiry from KIS (or a synthetic demo): futures basis and fair value, "
                                 "the Black-76 smile against the exchange's IV, an SVI fit with the butterfly check, the "
                                 "model-free variance, the risk-neutral density, the box-spread quote check, and a hedge "
                                 "P&L simulation in bp of notional.", icon=ft.Icons.STACKED_LINE_CHART_OUTLINED,
                                 action=ft.Button("Open Settings", on_click=lambda e: on_open_settings())
                                 if on_open_settings else None)]
    return ft.Column([
        section("Derivatives", subtitle="KOSPI200 futures basis, option surface, risk-neutral density, box rate, hedge P&L."),
        form_row([source, expiry, rate, engine, paths,
                  action(ft.Button("Load", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy)]),
        ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)


if __name__ == "__main__":
    s = snapshot(source="synthetic", n_paths=800)
    assert abs(s["F"] - 1126.0) < 0.5 and s["reconcile"]["ok"] and s["svi"].rmse_volpts < 0.3
    assert 0.99 < s["rnd"]["integral"] < 1.01 and s["box"] and abs(s["box"]["rate"] - s["rate"]) < 1e-6
    assert abs(s["mfiv"]["vol"] - s["atm"].iv) < 0.05
    text = narrative(s)
    assert "forward" in text and "Hedge simulation" in text and payload(s)["svi"]["rmse_volpts"] < 0.3
    print("ok")
