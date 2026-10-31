"""Derivatives — KOSPI200 futures basis, the option board, the volatility
surface, the risk-neutral density, the box-spread funding rate, and the
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
from ui.components import card, chip, empty_state, notice, section, stat
import ui.xcharts as xc
from core.research.derivatives_workflow import synthetic_board, snapshot, narrative, payload
from core.research.quote_coverage import butterfly_display, quote_coverage_text

_SOURCES = [("kis", "KIS live (KOSPI200 board)"), ("synthetic", "Synthetic demo board")]
_ENGINES = [("gbm", "GBM at the ATM vol"), ("garch_t", "GARCH(1,1)-t on the index history")]


def build_derivatives_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    source = ft.Dropdown(label="Board", width=260, value="kis" if config.kis_ready() else "synthetic",
                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
    expiry = ft.TextField(label="Expiry YYYYMM", hint_text="blank = nearest", width=150, border_radius=RADII["md"])
    rate = ft.TextField(label="Rate % (blank = CD 91d)", width=170, border_radius=RADII["md"])
    engine = ft.Dropdown(label="Hedge-sim engine", width=260, value="gbm",
                         options=[ft.dropdown.Option(k, v) for k, v in _ENGINES])
    paths = ft.TextField(label="Paths", value="3000", width=100, border_radius=RADII["md"])
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=14)

    def run(e=None) -> None:
        busy.visible = True
        host.controls = []
        page.update()

        def worker():
            try:
                rp = float(rate.value) if (rate.value or "").strip() else None
                s = snapshot(source=source.value or "kis", expiry=expiry.value or "", rate_pct=rp,
                             engine=engine.value or "gbm", n_paths=int(float(paths.value or "3000")))
            except (FICCError, ValueError) as exc:
                host.controls = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            except Exception as exc:
                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            b, fit, sim, rec = s["basis"], s["svi"], s["hedge"], s["reconcile"]
            butterfly_value, butterfly_token = butterfly_display(s['quote_coverage'])
            blocks: list[ft.Control] = []
            if s["source"] != "kis":
                blocks.append(notice("Synthetic board: a smile-shaped demo chain, not market quotes.", "error",
                                     icon=ft.Icons.SCIENCE_OUTLINED))
            if not s.get("live_quotes", True):
                blocks.append(notice(f"Market closed: these are the last prints of {s['session']}, struck at different moments, "
                                     "not quotes. Checks requiring two-sided quotes remain NOT_RUN without sufficient coverage.",
                                     "error", icon=ft.Icons.NIGHTLIGHT_OUTLINED))
            blocks.append(ft.Row([chip(f"expiry {s['expiry']} → {s['expiry_date']}"), chip(f"as of {s['as_of']}"),
                                  chip(f"prices of {s.get('session', '?')}"), chip(f"rate {s['rate']:.2%} ({s['rate_source']})"),
                                  chip(f"{s['n_quotes']} strikes"),
                                  chip(f"{len(s['points'])} {'quoted' if s.get('live_quotes', True) else 'last-print'} near-ATM", "accent")],
                                 spacing=6, wrap=True))
            blocks.append(ft.Row([
                stat("Forward (parity)", f"{s['F']:.2f}"), stat("Front future", f"{s['futures']['price']:.2f}"),
                stat("Basis (pts)", f"{b.basis_pts:+.2f}"), stat("Fair value", f"{b.fair:.2f}"),
                stat("Mispricing", f"{b.mispricing_bp:+.0f} bp", token="error" if abs(b.mispricing_bp) > 20 else "text"),
                stat("Implied funding", f"{b.implied_rate:.2%}"),
                stat("KIS theo gap", f"{b.theo_gap_pts:+.2f} pts" if b.theo_gap_pts is not None else "n/a"),
            ], spacing=10, wrap=True))
            blocks.append(ft.Row([
                stat("ATM IV", f"{s['atm'].iv:.1%}"),
                stat("MFIV", f"{s['mfiv'].get('vol', float('nan')):.1%}" if s["mfiv"].get("n_strikes") else "n/a"),
                stat("SVI ρ", f"{fit.rho:+.2f}"), stat("SVI RMSE", f"{fit.rmse_volpts:.2f} pts",
                                                       token="error" if fit.rmse_volpts > 1.0 else "text"),
                stat("IV gap vs KIS", f"{rec['median_volpts']:.2f} pts", token="success" if rec["ok"] else "error",
                     tooltip="median |σ_app − σ_KIS| on quoted strikes within ±15 % of F; gate 0.5"),
                stat("Butterfly viol.", butterfly_value, token=butterfly_token,
                     tooltip=quote_coverage_text(s['quote_coverage'])),
                stat("Box rate", f"{s['box']['rate']:.2%}" if s["box"] else "n/a"),
                stat("RND ∫", f"{s['rnd']['integral']:.3f}"),
            ], spacing=10, wrap=True))
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
                stat("Hedge P&L (mean)", f"{sim.mean_pnl_bp:+.0f} bp", token="success" if sim.mean_pnl_bp > 0 else "error",
                     tooltip="short the ATM option at σ_h, delta-hedged daily; bp of notional"),
                stat("SE", f"{sim.se_bp:.0f} bp"), stat("CVaR95", f"{sim.cvar95_bp:+.0f} bp", token="error"),
                stat("σ_h", f"{sim.sigma_hedge:.1%}"), stat("Break-even realised vol", f"{sim.breakeven_vol:.1%}"),
                stat("Identity slope / R²", f"{sim.identity_slope:.2f} / {sim.identity_r2:.2f}"),
                stat("Engine", sim.engine),
            ], spacing=10, wrap=True))
            blocks.append(analysis_panel(page, kind="kospi200_derivatives", narrative=narrative(s),
                                         payload_fn=lambda p=payload(s): p, deep_fn=insights.deep_analysis))
            host.controls = blocks
            busy.visible = False
            page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Load the board",
                                 "The nearest KOSPI200 expiry from KIS (or a synthetic demo): futures basis and fair value, "
                                 "the Black-76 smile against the exchange's IV, an SVI fit with the butterfly check, the "
                                 "model-free variance, the risk-neutral density, the box-spread funding rate, and a hedge "
                                 "P&L simulation in bp of notional.", icon=ft.Icons.STACKED_LINE_CHART_OUTLINED,
                                 action=ft.Button("Open Settings", on_click=lambda e: on_open_settings())
                                 if on_open_settings else None)]
    return ft.Column([
        section("Derivatives", subtitle="KOSPI200 futures basis, option surface, risk-neutral density, box rate, hedge P&L."),
        ft.Row([source, expiry, rate, engine, paths, ft.Button("Load", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy],
               spacing=10, wrap=True),
        ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=14, expand=True)


if __name__ == "__main__":
    s = snapshot(source="synthetic", n_paths=800)
    assert abs(s["F"] - 1126.0) < 0.5 and s["reconcile"]["ok"] and s["svi"].rmse_volpts < 0.3
    assert 0.99 < s["rnd"]["integral"] < 1.01 and s["box"] and abs(s["box"]["rate"] - s["rate"]) < 1e-6
    assert abs(s["mfiv"]["vol"] - s["atm"].iv) < 0.05
    text = narrative(s)
    assert "forward" in text and "Hedge simulation" in text and payload(s)["svi"]["rmse_volpts"] < 0.3
    print("ok")
