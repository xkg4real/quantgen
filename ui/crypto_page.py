"""Crypto — the kimchi premium, funding as carry, the app's GARCH(1,1)-t on
Bitcoin, the ETH/BTC test, the weekday table and, when an Upbit read-only key
is configured, the holdings with their cost basis.

Everything is keyless public data (`data.crypto.crypto_client`) except the
balance read. Nothing here trades, and the page says so.
"""
from __future__ import annotations

from core.research.funding_disclosure import funding_text
import math
from typing import Callable, Optional

import flet as ft
import numpy as np

import config
from core.crypto import analytics as CA
from core.quant import insights
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.narrative_sections import korean, localized
from quantgen_desktop.market_narrative_language import crypto_korean
from ui.components import card, empty_state, notice, section, stat
from ui.ficc_widgets import action, form_row, hide_source, ko_notice, ko_stat, lchip, ltext, verdict_ko
from ui.localization import literal_text, table_header
import ui.xcharts as xc
from core.research.crypto_workflow import (_synthetic, _live, analyze, narrative, payload, CRYPTO_DAYS,
                                          cost_basis_text, holdings_summary, perp_premium_pct, z_short_window, z_text)
from core.research.decay_disclosure import decay_value, decay_text


_WEEKDAY_HEADERS_KO = {"Day": "요일", "n": "관측 수", "Mean return %": "평균 수익률 %", "Vol %": "변동성 %",
                       "Mean quote volume": "평균 거래대금"}
_DAY_KO = {"Mon": "월", "Tue": "화", "Wed": "수", "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"}


def build_crypto_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    # Keyless Upbit + Binance always; the selector stays for tests but is not shown.
    source = hide_source(ft.Dropdown(label="Source", width=260, value="live",
                                     options=[ft.dropdown.Option("live", "Upbit + Binance (keyless)"),
                                              ft.dropdown.Option("synthetic", "Synthetic demo")]), "live")
    days = ft.TextField(label="Days", value="730", width=140, border_radius=RADII["md"],
                        text_align=ft.TextAlign.RIGHT)
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    host = ft.Column(spacing=16)

    def run(e=None) -> None:
        busy.visible = True; host.controls = []; page.update()

        def worker():
            try:
                a = analyze(days=int(float(days.value or "730")), source=source.value or "live")
            except Exception as exc:
                host.controls = [ko_notice(notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE),
                                           "가상자산 데이터를 가져오지 못했습니다 (Upbit · Binance 공개 데이터). 네트워크 연결을 "
                                           f"확인한 뒤 다시 새로고침하세요. 원인: {type(exc).__name__}: {exc}")]
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
            src = {"LIVE": "실시간 (Upbit · Binance)", "SYNTHETIC": "합성 데이터"}.get(a["source"], a["source"])
            blocks.append(ft.Row([lchip(f"출처: {src}", f"source: {a['source']}", "success" if a["source"] == "LIVE" else "muted"),
                                  lchip(f"USD/KRW 환율 출처: {a['usdkrw_source']}", f"USD/KRW: {a['usdkrw_source']}"),
                                  lchip(f"프리미엄 관측 {kp.n}일", f"{kp.n} premium days")] +
                                 [lchip(f"{k.split('_', 2)[-1]}: {verdict_ko(v)}" + (" · 과거 연구 결과, 재검증 안 됨" if k == "M_C4_funding" else ""),
                                        f"{k.split('_', 2)[-1]}: {v}" + (" · historical, not revalidated" if k == "M_C4_funding" else ""),
                                        "success" if v == "PASS" and k != "M_C4_funding" else "muted")
                                  for k, v in a["verdicts"].items()],
                                 spacing=8, wrap=True))
            perp, z, zw = perp_premium_pct(a["premium_index"]), z_text(kp.last_z, 2), z_short_window(kp)
            blocks.append(ft.Row([
                stat("Kimchi premium", f"{kp.last_pct:+.2f}%", token="error" if abs(kp.last_pct) > 3 else "text"),
                ko_stat(stat(f"Premium z ({zw} obs)" if zw else "Premium z (1y)", z or "n/a",
                     tooltip=("Not computed: fewer than 91 observations or no variation in the window." if not z else
                              f"Less than a year of history: the z uses the {zw} earlier observations." if zw else "")),
                        f"프리미엄 z ({zw}개 관측)" if zw else "프리미엄 z (1년)"),
                stat("AR(1) amplitude half-life", decay_value(getattr(kp, "decay", None)), tooltip=decay_text(getattr(kp, "decay", None)) + " Unit: observations."),
                stat("Funding (ann.)", f"{fc.last_ann_pct:+.1f}%" if fc else "n/a", token="error" if fc and fc.flag != "normal" else "text",
                     tooltip=fc.flag if fc else ""),
                stat("Funding pct", f"{fc.percentile:.0%}" if fc else "n/a"),
                stat("Perp premium", f"{perp:+.3f}%" if perp is not None else "n/a",
                     tooltip="" if perp is not None else "Binance did not return both mark and index prices."),
                stat("BTC cond. vol (365d)", f"{g['cond_vol_365']:.0%}"), stat("ν", f"{g['nu']:.1f}", token="error" if g["at_bound"] else "text"),
            ], spacing=12, run_spacing=12, wrap=True))
            blocks.append(card(xc.lines_chart(kp.dates, {"kimchi premium %": kp.premium_pct}, title="Kimchi premium (Upbit KRW-BTC vs Binance × USD/KRW)",
                                              hlines={"0": 0.0}, pct=True)))
            if fc:
                blocks.append(notice(funding_text(fc), "accent"))
                blocks.append(card(xc.lines_chart(fc.dates, {"funding (ann. %)": fc.carry_ann_pct}, title="Perpetual funding, 7-day mean annualised",
                                                  hlines={"0": 0.0}, pct=True)))
            px = a["btc"]
            sma50 = np.convolve(px, np.ones(50) / 50, mode="valid"); sma200 = np.convolve(px, np.ones(200) / 200, mode="valid")
            blocks.append(card(xc.lines_chart(a["btc_dates"], {"BTCUSDT": px, "SMA50": np.concatenate([np.full(49, np.nan), sma50]),
                                                              "SMA200": np.concatenate([np.full(199, np.nan), sma200])}, title="BTCUSDT with 50/200-day averages")))
            wt = a["weekday"]
            effect = (f"{wt['return_effect_p_bonferroni']:.2f}", f"{wt['weekend_volume_ratio']:.2f}",
                      f"{wt['weekend_volume_p']:.1e}")
            # A real table: numbers right-aligned in their own columns, day names in the page language.
            weekday_table = ft.DataTable(
                columns=[ft.DataColumn(table_header(h, ko=_WEEKDAY_HEADERS_KO[h], size=12, color=pal.muted),
                                       numeric=i > 0) for i, h in enumerate(_WEEKDAY_HEADERS_KO)],
                rows=[ft.DataRow(cells=[ft.DataCell(ltext(_DAY_KO.get(r['day'], r['day']), r['day'], size=12, color=pal.text))] +
                                 [ft.DataCell(literal_text(v, size=12, color=pal.text)) for v in (
                                     f"{r['n']}", f"{r['mean_ret_pct']:+.3f}", f"{r['vol_pct']:.2f}", f"{r['mean_volume']:,.0f}")])
                      for r in wt["rows"]],
                column_spacing=24, heading_row_height=32, data_row_min_height=28, data_row_max_height=28)
            blocks.append(card(ft.Column([ft.Text("Weekday table (returns %, vol %, mean quote volume)", size=13, weight=ft.FontWeight.W_600, color=pal.text),
                                          ft.Row([weekday_table], scroll=ft.ScrollMode.AUTO),
                                          ltext(f"요일 효과 p (본페로니 보정) {effect[0]}; 주말 거래대금 비율 {effect[1]} (p {effect[2]})",
                                                f"weekday effect p (Bonferroni) {effect[0]}; weekend volume ratio {effect[1]} (p {effect[2]})",
                                                size=12, color=pal.muted)], spacing=8)))
            if a.get("balances"):
                held = holdings_summary(a["balances"])
                unvalued = ', '.join(held['unvalued'])
                title = f"Upbit holdings (read-only): ₩{held['total_krw']:,.0f}" + (
                    "" if held["complete"] else f" · partial, excludes {unvalued} (no KRW price)")
                title_ko = f"Upbit 보유 자산 (조회 전용): ₩{held['total_krw']:,.0f}" + (
                    "" if held["complete"] else f" · 일부만 합산, 원화 가격이 없는 {unvalued} 제외")

                def holding(b, ko):
                    value = (f"₩{b['krw_value']:,.0f}" if b["krw_value"] is not None
                             else ("해당 없음 (원화 가격 없음)" if ko else "n/a (no KRW price)"))
                    words = ("평균 매수가", "평가액") if ko else ("avg buy", "value")
                    return f"{b['currency']}  {b['total']:.6f}  {words[0]} {cost_basis_text(b)}  {words[1]} {value}"

                blocks.append(card(ft.Column([ltext(title_ko, title, size=13, weight=ft.FontWeight.W_600, color=pal.text)] +
                                             [ltext(holding(b, True), holding(b, False), size=12, color=pal.text,
                                                    selectable=True) for b in a["balances"]] +
                                             [ft.Text("avg_buy_price is the cost-basis record for the 2027 virtual-asset tax; this page computes no tax.",
                                                      size=12, color=pal.muted)], spacing=4)))
            elif a.get("balances_error"):
                blocks.append(ko_notice(notice(f"Upbit balance read failed: {a['balances_error']}", "error"),
                                        f"Upbit 잔고 조회 실패: {a['balances_error']}"))
            elif not config.upbit_ready():
                blocks.append(ft.Text("Set UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY (자산조회 scope only) to show holdings.", size=12, color=pal.muted))
            blocks.append(analysis_panel(page, kind="crypto_market", narrative=narrative(a),
                                         payload_fn=lambda p=payload(a): p, deep_fn=insights.deep_analysis,
                                         sections=localized(narrative(a), korean(crypto_korean, a))))
            host.controls = blocks; busy.visible = False; page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Refresh the crypto sheet", "Kimchi premium, perpetual funding as carry, GARCH-t on Bitcoin, "
                                 "the ETH/BTC test and the weekday table, all from keyless Upbit and Binance data; Upbit "
                                 "holdings when a read-only key is set.", icon=ft.Icons.CURRENCY_BITCOIN,
                                 action=ft.Button("Open Settings", on_click=lambda e: on_open_settings()) if on_open_settings else None)]
    return ft.Column([
        section("Crypto", subtitle="Kimchi premium, funding carry, GARCH-t on Bitcoin — read-only."),
        form_row([source, days, action(ft.Button("Refresh", icon=ft.Icons.REFRESH, on_click=run), busy)]),
        ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=16, expand=True)


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
