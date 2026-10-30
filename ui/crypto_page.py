"""Crypto — the kimchi premium, funding as carry, the app's GARCH(1,1)-t on
Bitcoin, the ETH/BTC test, the weekday table and, when an Upbit read-only key
is configured, the holdings with their cost basis.

Everything is keyless public data (`data.crypto.crypto_client`) except the
balance read. Nothing here trades, and the page says so.
"""
from __future__ import annotations

import math
from typing import Callable, Optional

import flet as ft
import numpy as np

import config
from core.crypto import analytics as CA
from core.quant import insights
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.components import card, chip, empty_state, notice, section, stat
import ui.xcharts as xc
from core.research.crypto_workflow import _synthetic, _live, analyze, narrative, payload, CRYPTO_DAYS
from core.research.decay_disclosure import decay_value, decay_text


def build_crypto_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    source = ft.Dropdown(label="Source", width=260, value="live",
                         options=[ft.dropdown.Option("live", "Upbit + Binance (keyless)"), ft.dropdown.Option("synthetic", "Synthetic demo")])
    days = ft.TextField(label="Days", value="730", width=100, border_radius=RADII["md"])
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=14)

    def run(e=None) -> None:
        busy.visible = True; host.controls = []; page.update()

        def worker():
            try:
                a = analyze(days=int(float(days.value or "730")), source=source.value or "live")
            except Exception as exc:
                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
                busy.visible = False; page.update(); return
            kp, fc, g = a["kimchi"], a["funding"], a["garch"]
            blocks: list[ft.Control] = []
            blocks.append(notice(decay_text(getattr(kp, "decay", None)), "accent"))
            blocks.append(notice("ETH/BTC: " + decay_text(a['ethbtc'].get('decay')), "accent"))
            blocks.append(notice("Read-only: QUANTGEN never submits crypto orders, never holds a wallet key, and never assumes an "
                                 "account on an unregistered foreign exchange. Binance is public data only.", "accent",
                                 icon=ft.Icons.LOCK_OUTLINE))
            if a["source"] == "SYNTHETIC":
                blocks.append(notice("Synthetic data: every series here is simulated.", "error", icon=ft.Icons.SCIENCE_OUTLINED))
            blocks.append(ft.Row([chip(f"source: {a['source']}", "success" if a["source"] == "LIVE" else "muted"),
                                  chip(f"USD/KRW: {a['usdkrw_source']}"), chip(f"{kp.n} premium days")] +
                                 [chip(f"{k.split('_', 2)[-1]}: {v}", "success" if v == "PASS" else "muted") for k, v in a["verdicts"].items()],
                                 spacing=6, wrap=True))
            blocks.append(ft.Row([
                stat("Kimchi premium", f"{kp.last_pct:+.2f}%", token="error" if abs(kp.last_pct) > 3 else "text"),
                stat("Premium z (1y)", f"{kp.last_z:+.2f}"),
                stat("AR(1) amplitude half-life", decay_value(getattr(kp, "decay", None)), tooltip=decay_text(getattr(kp, "decay", None)) + " Unit: observations."),
                stat("Funding (ann.)", f"{fc.last_ann_pct:+.1f}%" if fc else "n/a", token="error" if fc and fc.flag != "normal" else "text",
                     tooltip=fc.flag if fc else ""),
                stat("Funding pct", f"{fc.percentile:.0%}" if fc else "n/a"),
                stat("Perp premium", f"{a['premium_index'].get('premium_pct', 0):+.3f}%"),
                stat("BTC cond. vol (365d)", f"{g['cond_vol_365']:.0%}"), stat("ν", f"{g['nu']:.1f}", token="error" if g["at_bound"] else "text"),
            ], spacing=10, wrap=True))
            blocks.append(card(xc.lines_chart(kp.dates, {"kimchi premium %": kp.premium_pct}, title="Kimchi premium (Upbit KRW-BTC vs Binance × USD/KRW)",
                                              hlines={"0": 0.0}, pct=True)))
            if fc:
                blocks.append(card(xc.lines_chart(fc.dates, {"funding (ann. %)": fc.carry_ann_pct}, title="Perpetual funding, 7-day mean annualised",
                                                  hlines={"0": 0.0}, pct=True)))
            px = a["btc"]
            sma50 = np.convolve(px, np.ones(50) / 50, mode="valid"); sma200 = np.convolve(px, np.ones(200) / 200, mode="valid")
            blocks.append(card(xc.lines_chart(a["btc_dates"], {"BTCUSDT": px, "SMA50": np.concatenate([np.full(49, np.nan), sma50]),
                                                              "SMA200": np.concatenate([np.full(199, np.nan), sma200])}, title="BTCUSDT with 50/200-day averages")))
            wt = a["weekday"]
            blocks.append(card(ft.Column([ft.Text("Weekday table (returns %, vol %, mean quote volume)", size=13, weight=ft.FontWeight.W_600, color=pal.text)] +
                                         [ft.Text(f"{r['day']}  n {r['n']}  mean {r['mean_ret_pct']:+.3f}  vol {r['vol_pct']:.2f}  volume {r['mean_volume']:,.0f}",
                                                  size=12, color=pal.text, font_family="Consolas, monospace") for r in wt["rows"]] +
                                         [ft.Text(f"weekday effect p (Bonferroni) {wt['return_effect_p_bonferroni']:.2f}; weekend volume ratio "
                                                  f"{wt['weekend_volume_ratio']:.2f} (p {wt['weekend_volume_p']:.1e})", size=11, color=pal.muted)], spacing=3)))
            if a.get("balances"):
                total = sum(b["krw_value"] for b in a["balances"])
                blocks.append(card(ft.Column([ft.Text(f"Upbit holdings (read-only): ₩{total:,.0f}", size=13, weight=ft.FontWeight.W_600, color=pal.text)] +
                                             [ft.Text(f"{b['currency']}  {b['total']:.6f}  avg buy {b['avg_buy_price']:,.0f}  value ₩{b['krw_value']:,.0f}",
                                                      size=12, color=pal.text, font_family="Consolas, monospace") for b in a["balances"]] +
                                             [ft.Text("avg_buy_price is the cost-basis record for the 2027 virtual-asset tax; this page computes no tax.",
                                                      size=11, color=pal.muted)], spacing=3)))
            elif a.get("balances_error"):
                blocks.append(notice(f"Upbit balance read failed: {a['balances_error']}", "error"))
            elif not config.upbit_ready():
                blocks.append(ft.Text("Set UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY (자산조회 scope only) to show holdings.", size=11, color=pal.muted))
            blocks.append(analysis_panel(page, kind="crypto_market", narrative=narrative(a),
                                         payload_fn=lambda p=payload(a): p, deep_fn=insights.deep_analysis))
            host.controls = blocks; busy.visible = False; page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Refresh the crypto sheet", "Kimchi premium, perpetual funding as carry, GARCH-t on Bitcoin, "
                                 "the ETH/BTC test and the weekday table, all from keyless Upbit and Binance data; Upbit "
                                 "holdings when a read-only key is set.", icon=ft.Icons.CURRENCY_BITCOIN,
                                 action=ft.Button("Open Settings", on_click=lambda e: on_open_settings()) if on_open_settings else None)]
    return ft.Column([
        section("Crypto", subtitle="Kimchi premium, funding carry, GARCH-t on Bitcoin — read-only."),
        ft.Row([source, days, ft.Button("Refresh", icon=ft.Icons.REFRESH, on_click=run), busy], spacing=10, wrap=True),
        ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=14, expand=True)


if __name__ == "__main__":
    a = analyze(source="synthetic")
    assert a["source"] == "SYNTHETIC" and a["kimchi"].n > 800 and "regime" not in a
    assert "MAJORS" not in globals() and "majors" not in _synthetic()
    assert not any(hasattr(CA, k) for k in ("regime_score", "RegimeScore", "RegimeComponent", "_sma"))
    assert a["garch"]["n"] == 730 and len(a["weekday"]["rows"]) == 7
    t = narrative(a)
    assert "Korea pays" in t and "regime" not in t.lower() and "SYNTHETIC" in t
    p = payload(a)
    assert "regime" not in p and p["kimchi"]["n"] == a["kimchi"].n
    print("ok")
