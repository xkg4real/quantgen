"""Settings: credential presence and live probes of the KRX, FICC, KIS and crypto providers.

Presence only — no value is ever read into a widget, and there is no field to
type a key into. Credentials come from `.env` or the process environment, which
keeps them out of QUANTGEN's own state and out of any screenshot.

The KRX row is a live probe rather than a presence check, because a KRX_API_KEY
that exists and a KRX_API_KEY that the exchange accepts are different things,
and the difference is worth one HTTP call.
"""
from __future__ import annotations

import flet as ft

import re

import config
from core.i18n import LocaleContext
from core.theme import RADII, active
from data.krx.krx_market_client import KRXMarketClient
from ui.build_widgets import local_chip
from ui.components import LocalText, chip, notice, section

_KO = LocaleContext("ko_KR").text          # the reviewed Korean caption of a static English string


def _note(text: str) -> ft.Text:
    """A provider note in both languages: the page catalogue for the fixed notes, plus the one
    note that interpolates the configured AI model name."""
    pal = active()
    ko = _KO(text)
    m = re.fullmatch(r"AI narrative analysis of quant results\. Model: (.+)\.", text or "")
    if m:
        ko = f"계산 결과를 AI가 글로 해설합니다. 사용 모형: {m[1]}."
    return LocalText(ko, text, size=12, color=pal.muted)

# KIS asset domains probed by data.kis_markets.KISMarkets.probe, by their display names.
_KIS_DOMAINS = {
    "etf": ("ETF", "ETF"), "index_futures": ("지수 선물", "Index futures"),
    "ktb_futures": ("국채 선물", "KTB futures"), "options": ("옵션", "Options"),
    "overseas_stock": ("해외 주식", "Overseas stock"), "krw_yields": ("원화 지표 금리", "KRW yields"),
    "overseas_futures": ("해외 선물", "Overseas futures"), "bonds": ("장내 채권", "Bonds"),
    "kis": ("KIS", "KIS"),
}


def _kis_state(result: dict) -> tuple[str, str, str]:
    """(Korean, English, token) for one KIS probe result. `KISUnavailable` naming KIS_APP_KEY is raised
    before any request when the key is not configured, so it reads 'key not set', not as a failed check."""
    detail = str(result.get("detail", ""))
    if result.get("ok"):
        return "정상", "ok", "success"
    if detail.startswith("KISUnavailable") and "KIS_APP_KEY" in detail:
        return "키 미설정", "Key not set", "muted"
    return "확인 실패", "Check failed", "error"


_SIGNUP = {
    "fred": "fred.stlouisfed.org (no key needed)",
    "yfinance": "finance.yahoo.com (no key needed)",
    "fmp": "financialmodelingprep.com",
    "kis": "apiportal.koreainvestment.com",
    "opendart": "opendart.fss.or.kr",
    "krx": "data.krx.co.kr",
    "upbit": "docs.upbit.com (no key needed)",
    "binance": "developers.binance.com (no key needed)",
    "upbit_account": "upbit.com → Open API 관리 (자산조회 only)",
}


def _ficc_status() -> list[dict]:
    fn = getattr(config, "ficc_provider_status", None)
    if fn is None:
        return [{"id": "fred", "label": "FRED (St. Louis Fed)", "ready": False,
                 "vars": (), "note": "config.ficc_provider_status is missing."}]
    try:
        return fn()
    except Exception as exc:
        return [{"id": "fred", "label": "FRED (St. Louis Fed)", "ready": False,
                 "vars": (), "note": f"{type(exc).__name__}: {exc}"}]


def build_settings_page(page: ft.Page) -> ft.Control:
    pal = active()

    probe_host = ft.Row(spacing=8)

    def provider_row(entry: dict) -> ft.Container:
        ready = bool(entry.get("ready"))
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(entry["label"], size=13, weight=ft.FontWeight.W_600,
                            color=pal.text, expand=True),
                    chip("configured" if ready else "not set",
                         "success" if ready else "muted"),
                ], spacing=8),
                _note(entry.get("note", "")),
                ft.Row([ft.Text(" · ".join(entry["vars"]), size=11, color=pal.muted,
                                selectable=True, expand=True),
                        ft.Text(_SIGNUP.get(entry["id"], ""), size=11, color=pal.accent,
                                selectable=True)], spacing=8),
            ], spacing=5),
            padding=12, bgcolor=pal.surface_2,
            border=ft.Border.all(1, pal.border), border_radius=RADII["md"],
        )

    def run_probe(e=None) -> None:
        probe_host.controls = [ft.ProgressRing(width=16, height=16),
                               ft.Text("contacting KRX…", size=12, color=pal.muted)]
        page.update()

        def worker():
            result = KRXMarketClient().probe()
            probe_host.controls = [
                chip("reachable" if result["ready"] else "unavailable",
                     "success" if result["ready"] else "error"),
                LocalText(f"경로: {result['path']}", f"path: {result['path']}", size=11, color=pal.muted),
                ft.Text(result["reason"], size=11, color=pal.muted, selectable=True,
                        expand=True),
            ]
            page.update()
        page.run_thread(worker)

    probe_host.controls = [ft.Button("Test KRX access", icon=ft.Icons.NETWORK_CHECK,
                                     on_click=run_probe)]

    ficc_probe_host = ft.Row(spacing=8, wrap=True)

    def run_ficc_probe(e=None) -> None:
        ficc_probe_host.controls = [ft.ProgressRing(width=16, height=16),
                                    ft.Text("contacting FRED and Yahoo…", size=12,
                                            color=pal.muted)]
        page.update()

        def worker():
            try:
                from core.ficc.data import probe as ficc_probe
                result = ficc_probe()
            except Exception as exc:                       # never take the page down
                result = {"fred": {"ok": False, "detail": f"{type(exc).__name__}: {exc}"},
                          "yfinance": {"ok": False, "detail": "probe failed"}}
            rows = []
            for key, label in (("fred", "FRED"), ("yfinance", "Yahoo Finance")):
                r = result.get(key) or {}
                rows.append(local_chip(f"{_KO(label)}: " + ("연결됨" if r.get("ok") else "연결 안 됨"),
                                       f"{label}: " + ("reachable" if r.get("ok") else "unavailable"),
                                       "success" if r.get("ok") else "error"))
                rows.append(ft.Text(str(r.get("detail", "")), size=11, color=pal.muted,
                                    selectable=True))
            ficc_probe_host.controls = rows
            page.update()
        page.run_thread(worker)

    ficc_probe_host.controls = [ft.Button("Test FICC data access", icon=ft.Icons.NETWORK_CHECK,
                                          on_click=run_ficc_probe)]

    kis_probe_host = ft.Row(spacing=8, wrap=True)

    def run_kis_probe(e=None) -> None:
        kis_probe_host.controls = [ft.ProgressRing(width=16, height=16),
                                   ft.Text("one read-only call per KIS asset domain…", size=12, color=pal.muted)]
        page.update()

        def worker():
            try:
                from data.kis_markets import KISMarkets
                result = KISMarkets().probe()
            except Exception as exc:
                result = {"kis": {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}}
            rows = []
            states = {key: _kis_state(r) for key, r in result.items()}
            if states and all(s[1] == "Key not set" for s in states.values()):
                # No request was sent for any domain: one chip and the one reason, not the same line per domain.
                detail = str(next(iter(result.values())).get("detail", ""))
                rows += [local_chip("KIS: 키 미설정 (요청을 보내지 않음)", "KIS: Key not set (no request sent)", "muted"),
                         ft.Text(detail, size=11, color=pal.muted, selectable=True)]
            for key, r in (() if rows else result.items()):
                ko, en, token = states[key]
                name_ko, name_en = _KIS_DOMAINS.get(key, (key, key))
                rows.append(local_chip(f"{name_ko}: {ko}", f"{name_en}: {en}", token))
                # The detail is visible, not hover-only: a missing key and a refused request read differently.
                rows.append(ft.Text(str(r.get("detail", "")), size=11, color=pal.muted, selectable=True))
            kis_probe_host.controls = rows
            page.update()
        page.run_thread(worker)

    kis_probe_host.controls = [ft.Button("Test KIS asset domains", icon=ft.Icons.NETWORK_CHECK, on_click=run_kis_probe)]

    crypto_probe_host = ft.Row(spacing=8, wrap=True)

    def run_crypto_probe(e=None) -> None:
        crypto_probe_host.controls = [ft.ProgressRing(width=16, height=16),
                                      ft.Text("contacting Upbit and Binance…", size=12, color=pal.muted)]
        page.update()

        def worker():
            try:
                from data.crypto.crypto_client import probe as cprobe
                result = cprobe()
            except Exception as exc:
                result = {"crypto": {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}}
            rows = []
            for key, r in result.items():
                rows.append(local_chip(f"{key}: " + ("연결됨" if r.get("ok") else "연결 안 됨"),
                                       f"{key}: " + ("reachable" if r.get("ok") else "unavailable"),
                                       "success" if r.get("ok") else "error"))
                rows.append(ft.Text(str(r.get("detail", "")), size=11, color=pal.muted, selectable=True))
            crypto_probe_host.controls = rows
            page.update()
        page.run_thread(worker)

    crypto_probe_host.controls = [ft.Button("Test crypto data access", icon=ft.Icons.NETWORK_CHECK, on_click=run_crypto_probe)]

    env_help = (
        "# .env\n"
        "FMP_API_KEY=\n"
        "KIS_APP_KEY=\nKIS_APP_SECRET=\n"
        "OPENDART_API_KEY=\n"
        "KRX_API_KEY=\n"
        "UPBIT_ACCESS_KEY=\nUPBIT_SECRET_KEY=\n"
        "ANTHROPIC_API_KEY=\n"
        "QUANTGEN_AI_MODEL=claude-sonnet-5\n"
        "GS_CLIENT_ID=\nGS_CLIENT_SECRET=\n"
    )

    controls: list[ft.Control] = [
        section("Settings", subtitle="Credential presence only. No key is ever displayed here."),
    ]

    def gs_row() -> ft.Control:
        from core.quant import gsq
        st = gsq.status()
        bits = []
        bits.append(chip(f"gs-quant {st.version}" if st.installed else "not installed",
                         "success" if st.installed else "error"))
        bits.append(chip("offline analytics " + ("active" if st.offline_analytics else "unavailable"),
                         "success" if st.offline_analytics else "muted"))
        bits.append(chip("Marquee session " + ("active" if st.session_active else "off"),
                         "success" if st.session_active else "muted"))
        return ft.Column([ft.Row(bits, spacing=6, wrap=True),
                          ft.Text(st.detail, size=12, color=pal.muted)], spacing=6)

    controls += [
        ft.Text("Quant analysis providers", size=15, weight=ft.FontWeight.W_600,
                color=pal.text),
        ft.ResponsiveRow([ft.Container(provider_row(p), col={"xs": 12, "md": 6})
                          for p in config.quant_provider_status()],
                         spacing=10, run_spacing=10),
        gs_row(),

        ft.Text("FICC data providers", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        notice("The Rates, Bonds, FX, Macro and Structuring pages read the Treasury "
               "curve, SOFR, credit spreads and FX fixings from FRED and Yahoo Finance. "
               "Both are keyless; fetches are cached on disk for a few hours.",
               "accent", icon=ft.Icons.INFO_OUTLINE),
        ft.ResponsiveRow([ft.Container(provider_row(p), col={"xs": 12, "md": 6})
                          for p in _ficc_status()],
                         spacing=10, run_spacing=10),
        ft.Container(ficc_probe_host, padding=ft.Padding(0, 4, 0, 4)),

        ft.Text("Korean market providers", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        notice("KRX closed its keyless CSV export; a free KRX_API_KEY is now required "
               "for whole-market snapshots. KIS and OpenDART registration is also free.",
               "accent", icon=ft.Icons.INFO_OUTLINE),
        ft.ResponsiveRow([ft.Container(provider_row(p), col={"xs": 12, "md": 6})
                          for p in config.krx_provider_status()],
                         spacing=10, run_spacing=10),
        ft.Container(probe_host, padding=ft.Padding(0, 4, 0, 4)),
        notice("The same KIS key serves ETF NAV, KOSPI200 / KTB / USD futures, the option board, overseas stocks, "
               "KRW benchmark yields and exchange-traded bonds — quotations only, no derivatives account needed "
               "(probed 2026-09-25). CME ES/NQ/ZN/6E/GC/CL history answers HTTP 500 on a stock-account key.",
               "accent", icon=ft.Icons.INFO_OUTLINE),
        ft.Container(kis_probe_host, padding=ft.Padding(0, 4, 0, 4)),

        ft.Text("Crypto providers", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        notice("Upbit and Binance public data are keyless. An Upbit key is optional and must be issued with 자산조회 "
               "(balance) scope only; QUANTGEN never submits orders, withdrawals or transfers and never holds a wallet key.",
               "accent", icon=ft.Icons.LOCK_OUTLINE),
        ft.ResponsiveRow([ft.Container(provider_row(p), col={"xs": 12, "md": 6})
                          for p in config.crypto_provider_status()],
                         spacing=10, run_spacing=10),
        ft.Container(crypto_probe_host, padding=ft.Padding(0, 4, 0, 4)),

        ft.Divider(color=pal.border),
        ft.Text("Environment template", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        ft.Text("QUANTGEN reads these from this machine only.", size=12, color=pal.muted),
        ft.Container(ft.Text(env_help, size=11, color=pal.muted, selectable=True,
                             font_family="Consolas, monospace"),
                     padding=12, bgcolor=pal.bg, border=ft.Border.all(1, pal.border),
                     border_radius=RADII["md"]),
    ]

    return ft.Column(controls, spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)
