"""Macro — a view selector over the cross-asset sheet and the v2 overlay state.

"Macro sheet" (default): press Refresh (the source is chosen automatically) and the page shows the
labelled descriptive-read summary (a descriptive read, not a regime model, P19), the headline levels, the indicator table (last, 1d/1w/1m changes, 1y z-score
and percentile), the z-score chart, and an analysis card. "Daily market
commentary" and "Weekly rates and FX note" swap that card for the report's
local narrative and a deep-analysis panel with the matching `kind`, routed
through `core.ficc.insights.deep_analysis` so the report-format instructions
are appended to whatever the operator asks.

Formatting happens here and nowhere else: the core hands over decimals, this
page prints percent, basis points, or raw levels according to each row's unit.
A sheet with SYNTHETIC rows says so loudly and hatches them in the chart.

"Overlay state" (`ui.macro_state_panel`), "Model cards" (`ui.macro_cards_view`) and
"Research register" (`ui.research_view`): the v2 views, each built on first selection
with its own Refresh; all four share the app's 180 ms switcher.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

import flet as ft
from ui.localization import table_header, literal_text

import config
from core.ficc import insights
from core.ficc.common import BP, FICCError
from core.ficc.macro import DESCRIPTIVE_READ_NOTE, MacroRow, MacroSheet, Regime, daily_brief, macro_sheet, weekly_brief
from core.theme import RADII, TRANSITION_MS, active
from core.ui_legacy_messages import static_text
from ui.ai_panel import analysis_panel
from ui.narrative_sections import localized, macro_text
from ui.charts_terms import (CURVE_WORDS, DOLLAR_WORDS, GROUP_NAMES, INDICATOR_NAMES, INFLATION_WORDS, REAL_WORDS,
                             RISK_WORDS, SHORT_NAMES, LocalTip, local_chip, local_notice, name, regime_evidence)
from ui.components import LocalText, card, chip, empty_state, notice, section
import ui.fcharts as fcharts
from ui.macro_cards_view import build_cards_view
from ui.macro_state_panel import build_overlay_view
from ui.research_view import build_research_view

_SOURCES = [("auto", "Auto (FRED + Yahoo, synthetic fallback)"),
            ("fred", "Live only (FRED + Yahoo, no fallback)"),
            ("synthetic", "Synthetic demo")]
_HEADLINE = ("DGS2", "DGS10", "DGS30", "T10Y2Y", "DFII10", "T10YIE",
             "VIXCLS", "BAMLH0A0HYM2", "DTWEXBGS")
_REGIME_TOKEN = {"risk-on": "success", "risk-off": "error"}
_HEADERS_KO = {'Group': '분류', 'Indicator': '지표', 'Last': '최근값',
               '1d': '1일', '1w': '1주', '1m': '1개월', '3m': '3개월',
               'z (1y)': 'z점수 (1년)', 'pct (1y)': '백분위 (1년)'}
_COLUMNS = ("Group", "Indicator", "Last", "1d", "1w", "1m", "3m", "z (1y)", "pct (1y)", "Source")
_VIEWS = (("sheet", "Macro sheet"), ("overlay", "Overlay state"), ("cards", "Model cards"),
          ("research", "Research register"))
_BUILDERS = {"overlay": build_overlay_view, "cards": build_cards_view,     # view key -> builder(page);
             "research": build_research_view}                             # "sheet" is built inline
DESCRIPTIVE_CAPTION = DESCRIPTIVE_READ_NOTE[:1].upper() + DESCRIPTIVE_READ_NOTE[1:]
# Korean shows the disclosure in words; the ruling id (P19) sits in the tooltip instead of the sentence.
DESCRIPTIVE_CAPTION_KO = "현재 상태를 설명하는 해석 — 국면 모형 아님"
_P19_TIP = ("운영 규칙 P19: 정해진 규칙으로 현재 상태를 설명할 뿐이며, 국면(레짐) 모형이나 예측이 아닙니다.",
            "Ruling P19: a rule-based description of the present, not a regime model or a forecast.")
_INSTALLED_TIP = ("설치 여부만 표시합니다. 이번 결과에 실제로 응답한 출처는 결과 위의 '데이터' 칩에 표시됩니다.",
                  "Shows only whether the client is installed. The Data chips above the result say which "
                  "provider actually answered.")
_REPORTS = {
    "daily": ("Daily market commentary", "daily_market_commentary"),
    "weekly": ("Weekly rates and FX note", "weekly_fi_fx_strategy"),
}


def _level(r: MacroRow) -> str:
    if r.unit == "pct":
        return f"{r.last * 100:.2f}%"
    if r.unit == "bp":
        return f"{r.last / BP:.0f}bp"
    if r.unit == "fx" and r.last < 20:
        return f"{r.last:.4f}"
    return f"{r.last:,.2f}"


def _chg(r: MacroRow, chg: float | None) -> str:
    if chg is None:
        return "-"
    if r.unit in ("pct", "bp"):
        return f"{chg / BP:+.1f}bp"
    if r.unit == "fx" and r.last < 20:
        return f"{chg:+.4f}"
    return f"{chg:+.2f}"


_READ_ITEMS = (  # (Regime field, label shown, evidence key, word table)
    ("curve", "Yield curve (20 sessions)", "curve", CURVE_WORDS),
    ("risk", "Risk appetite", "risk", RISK_WORDS),
    ("dollar", "Dollar", "dollar", DOLLAR_WORDS),
    ("inflation", "Inflation expectations (1 month)", "inflation", INFLATION_WORDS),
    ("real_rates", "Real yields (1 month)", "real", REAL_WORDS),
)


def _heading(text: str) -> ft.Text:
    return ft.Text(text, size=15, weight=ft.FontWeight.W_600, color=active().text)


def read_row(rg: Regime) -> ft.Control:
    """The rule-based read of the sheet as a labelled summary, captioned as what it is (rulings 3.9; P19).

    Each term carries its plain meaning and the numbers the core printed in `Regime.summary`; the
    full summary sentence stays one click away. Feeds nothing."""
    pal = active()
    evidence = regime_evidence(rg.summary)
    items = []
    for field, label, key, words in _READ_ITEMS:
        value = getattr(rg, field)
        word_ko, mean_ko, mean_en = words.get(value, (value, "", ""))
        token = _REGIME_TOKEN.get(value, "text") if field == "risk" else "text"
        body = [ft.Text(label, size=12, color=pal.muted),
                LocalText(word_ko, value, size=16, weight=ft.FontWeight.W_600, color=getattr(pal, token))]
        if mean_ko:
            body.append(LocalText(mean_ko, mean_en, size=12, color=pal.text))
        if key in evidence:
            body.append(LocalText(*evidence[key], size=12, color=pal.muted))
        items.append(ft.Container(ft.Column(body, spacing=4), padding=12, bgcolor=pal.surface_2,
                                  border=ft.Border.all(1, pal.border), border_radius=12,
                                  col={"xs": 12, "sm": 6, "lg": 4}))
    detail = ft.ExpansionTile(
        title=ft.Text("Rule calculation (original summary)", size=12, color=pal.muted),
        controls=[ft.Text(rg.summary, size=12, color=pal.muted, selectable=True)],
        expanded=False, tile_padding=ft.Padding(0, 0, 0, 0))
    return ft.Column([
        LocalTip(LocalText(DESCRIPTIVE_CAPTION_KO, DESCRIPTIVE_CAPTION, size=12, color=pal.muted), tips=_P19_TIP),
        ft.ResponsiveRow(items, spacing=12, run_spacing=12),
        detail,
    ], spacing=8)


_SOURCE_NAMES = {"FRED": ("FRED", "FRED"), "YFINANCE": ("Yahoo", "YFINANCE"), "SYNTHETIC": ("합성", "SYNTHETIC")}


def _synthetic_notice(sheet: MacroSheet) -> ft.Control:
    """The loud synthetic-data notice, in both languages; the English text is the core's own note."""
    ids = ", ".join(sheet.synthetic_ids)
    ko = (f"합성 데이터 사용 중: 지표 {len(sheet.rows)}개 중 {len(sheet.synthetic_ids)}개가 실제 관측이 아닌 "
          f"합성 시계열입니다 ({ids}). 차트에서는 빗금 막대로 표시됩니다.")
    short = re.search(r"Shortest series has (\d+) obs", sheet.note or "")
    if short:
        ko += f" 가장 짧은 시계열이 {short.group(1)}개 관측이라 z-점수·백분위는 252개보다 적은 관측으로 계산했습니다."
    return local_notice(ko, "Synthetic data: " + sheet.note, "error", icon=ft.Icons.SCIENCE_OUTLINED)


def build_macro_page(page: ft.Page,
                     on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    # The source is chosen automatically (owner decision 2026-11-10: no data-source selector on screens).
    # The control stays, hidden, so tests and self-checks can still pick "synthetic".
    source = ft.Dropdown(label="Data source", width=300, value="auto", visible=False,
                         options=[ft.dropdown.Option(k, v) for k, v in _SOURCES])
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    result_host = ft.Column(spacing=16)
    analysis_host = ft.Column(spacing=14)

    def provider_bar() -> list[ft.Control]:
        """Which provider clients are installed: presence only, so always muted. What actually answered is
        stated by the result's Data chips (FRED / Yahoo / 합성 with the indicator count)."""
        out = []
        for s in config.ficc_provider_status():
            label = {"fred": "FRED", "yfinance": "Yahoo"}.get(s["id"], s["id"])
            ready = bool(s.get("ready"))
            note = s.get("note", "")
            out.append(local_chip(f"{label} " + ("설치됨" if ready else "미설치"),
                                  f"{label}: " + ("installed" if ready else "not installed"), "muted",
                                  tips=(_INSTALLED_TIP[0] + (" " + static_text(note, "ko") if note else ""),
                                        _INSTALLED_TIP[1] + (" " + note if note else ""))))
        return out

    def cell(text: str, *, token: str = "text") -> ft.DataCell:
        return ft.DataCell(literal_text(text, size=12, color=getattr(pal, token)))

    def named(table: dict, key: str, fallback: str, *, token: str = "text") -> ft.DataCell:
        """Authored Korean/English name for a known id or group; anything else is shown as it came."""
        if key not in table:
            return cell(fallback, token=token)
        return ft.DataCell(LocalText(*table[key], size=12, color=getattr(pal, token)))

    def sign_token(x: float | None) -> str:
        return "text" if not x else ("success" if x > 0 else "error")

    def table(sheet: MacroSheet) -> ft.Control:
        rows = []
        for r in sheet.rows:
            rows.append(ft.DataRow(cells=[
                named(GROUP_NAMES, r.group, r.group, token="muted"), named(INDICATOR_NAMES, r.id, r.label),
                cell(_level(r)),
                cell(_chg(r, r.chg_1d), token=sign_token(r.chg_1d)),
                cell(_chg(r, r.chg_1w), token=sign_token(r.chg_1w)),
                cell(_chg(r, r.chg_1m), token=sign_token(r.chg_1m)),
                cell(_chg(r, r.chg_3m), token=sign_token(r.chg_3m)),
                cell(f"{r.z_1y:+.2f}", token="error" if abs(r.z_1y) >= 2 else "text"),
                cell(f"{r.pct_1y * 100:.0f}%"),
                named(_SOURCE_NAMES, r.source, r.source, token="error" if r.source == "SYNTHETIC" else "muted"),
            ]))
        dt = ft.DataTable(
            columns=[ft.DataColumn(table_header(c, ko=_HEADERS_KO.get(c), size=12, color=pal.muted),
                                   numeric=i >= 2 and c != "Source")
                     for i, c in enumerate(_COLUMNS)],
            rows=rows, column_spacing=16, heading_row_height=36, data_row_max_height=34)
        return ft.Row([dt], scroll=ft.ScrollMode.AUTO)

    def tile(r: MacroRow) -> ft.Control:
        token = "error" if abs(r.z_1y) >= 2 else "text"
        chg = _chg(r, r.chg_1d)
        return LocalTip(
            ft.Column([LocalText(*name(SHORT_NAMES, r.id, r.label), size=12, color=pal.muted),
                       literal_text(_level(r), size=16, weight=ft.FontWeight.W_600, color=getattr(pal, token))],
                      spacing=2),
            padding=ft.Padding(14, 10, 14, 10), bgcolor=pal.surface_2, border=ft.Border.all(1, pal.border),
            border_radius=RADII["md"],
            tips=(f"1일 변화 {chg} · 1년 z-점수 {r.z_1y:+.2f}", f"1d {chg} · z (1y) {r.z_1y:+.2f}"))

    def sheet_analysis(sheet: MacroSheet) -> ft.Control:
        payload = daily_brief(sheet)
        narrative = insights.narrate_macro(sheet)
        return analysis_panel(page, kind="macro_sheet", narrative=narrative,
                              payload_fn=lambda p=payload: p,
                              deep_fn=insights.deep_analysis,
                              sections=localized(narrative, macro_text(sheet, "sheet", narrative)))

    def report(sheet: MacroSheet, which: str) -> None:
        title, kind = _REPORTS[which]
        if which == "daily":
            text, payload = insights.narrate_daily_brief(sheet), daily_brief(sheet)
        else:
            text, payload = insights.narrate_weekly_strategy(sheet), weekly_brief(sheet)
        prompt = insights.report_prompt(kind)
        analysis_host.controls = [
            ft.Row([_heading(title), chip(sheet.as_of)], spacing=8, wrap=True,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.ExpansionTile(
                title=ft.Text("Deep-analysis format (instructions sent with a deep analysis)", size=12,
                              color=pal.muted),
                controls=[ft.Text(f"kind: {kind}", size=12, color=pal.muted, selectable=True),
                          ft.Text("Deep-analysis format: " + prompt, size=12, color=pal.muted, selectable=True)],
                expanded=False, tile_padding=ft.Padding(0, 0, 0, 0)),
            analysis_panel(page, kind=kind, narrative=text, payload_fn=lambda p=payload: p,
                           deep_fn=insights.deep_analysis,
                           sections=localized(text, macro_text(sheet, which, text))),
        ]
        page.update()

    def render(sheet: MacroSheet) -> list[ft.Control]:
        blocks: list[ft.Control] = []
        if sheet.synthetic_ids:
            blocks.append(_synthetic_notice(sheet))
        elif sheet.note:
            blocks.append(notice(sheet.note, "muted"))
        rg = sheet.regime
        provenance = [local_chip(f"기준일 {sheet.as_of}", f"as of {sheet.as_of}")]
        for src, n in sheet.sources.items():
            ko_src, en_src = _SOURCE_NAMES.get(src, (src, src))
            provenance.append(local_chip(f"{ko_src} {n}개 지표", f"{en_src}: {n}",
                                         "error" if src == "SYNTHETIC" else "success"))
        blocks.append(ft.Row([ft.Text("Data", size=12, color=pal.muted)] + provenance, spacing=6, wrap=True,
                             vertical_alignment=ft.CrossAxisAlignment.CENTER))
        blocks.append(_heading("Market summary"))
        blocks.append(read_row(rg))
        tiles = [tile(r) for r in (sheet.row(i) for i in _HEADLINE) if r is not None]
        blocks.append(_heading("Key levels"))
        blocks.append(ft.Row(tiles, spacing=10, run_spacing=10, wrap=True))
        blocks.append(card(ft.Column([
            LocalTip(LocalText(f"1년 z-점수 · {DESCRIPTIVE_CAPTION_KO}", f"1y z-scores · {DESCRIPTIVE_READ_NOTE}",
                               size=12, color=pal.muted), tips=_P19_TIP),
            fcharts.macro_z_chart(sheet)], spacing=8)))
        blocks.append(_heading("All indicators"))
        blocks.append(table(sheet))
        blocks.append(_heading("Reports"))
        blocks.append(ft.Row([
            ft.Button(_REPORTS["daily"][0], icon=ft.Icons.TODAY_OUTLINED,
                      on_click=lambda e: report(sheet, "daily")),
            ft.Button(_REPORTS["weekly"][0], icon=ft.Icons.DATE_RANGE_OUTLINED,
                      on_click=lambda e: report(sheet, "weekly")),
        ], spacing=10, wrap=True))
        analysis_host.controls = [sheet_analysis(sheet)]
        blocks.append(analysis_host)
        return blocks

    def refresh(e=None) -> None:
        busy.visible = True
        result_host.controls = []
        analysis_host.controls = []
        page.update()

        def worker():
            try:
                sheet = macro_sheet(source=source.value or "auto")
                result_host.controls = render(sheet)
            except (FICCError, ValueError) as exc:
                result_host.controls = [notice(str(exc), "error",
                                               icon=ft.Icons.ERROR_OUTLINE)]
            except Exception as exc:
                result_host.controls = [notice(f"{type(exc).__name__}: {exc}", "error",
                                               icon=ft.Icons.ERROR_OUTLINE)]
            busy.visible = False
            page.update()

        page.run_thread(worker)

    result_host.controls = [empty_state(
        "Press Refresh to load the macro sheet",
        "Treasuries, real and breakeven yields, policy rates, IG/HY spreads, the dollar, "
        "VIX, WTI, the 10y future and gold - FRED and Yahoo are keyless; without them the "
        "sheet runs on clearly labeled synthetic series.",
        icon=ft.Icons.PUBLIC_OUTLINED,
        action=ft.Button("Open Settings", on_click=lambda e: on_open_settings())
        if on_open_settings else None)]

    sheet_view = ft.Column([
        ft.Row([ft.Button("Refresh", icon=ft.Icons.REFRESH, on_click=refresh), busy, source,
                ft.Text("Data is fetched automatically (FRED and Yahoo, no key needed).", size=12,
                        color=pal.muted)] + provider_bar(),
               spacing=10, run_spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=14, expand=True)
    views: dict[str, ft.Control] = {"sheet": sheet_view}
    switcher = ft.AnimatedSwitcher(content=sheet_view, duration=TRANSITION_MS,
                                   reverse_duration=TRANSITION_MS, expand=True)

    def switch(e=None) -> None:
        key = view.value or "sheet"
        if key not in views:                    # built on first selection; reads artifacts on its own Refresh
            views[key] = _BUILDERS[key](page)
        switcher.content = views[key]
        page.update()

    view = ft.Dropdown(label="View", width=220, value="sheet", on_select=switch,
                       options=[ft.dropdown.Option(k, v) for k, v in _VIEWS])
    return ft.Column([
        section("Macro", subtitle="Cross-asset sheet (descriptive read), the v2 overlay state, model cards, "
                                  "the research register, and the daily / weekly rates-FX report inputs."),
        view,
        switcher,
    ], spacing=14, expand=True)


# --------------------------------------------------------------------------- #
# Self-check (synthetic only - no network, no running Flet page)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from core.ficc.data import Series
    from core.ficc.macro import _row, INDICATORS

    def _fred(ind, values):
        dates = tuple(f"2025-01-{i + 1:02d}" for i in range(len(values)))
        return _row(ind, Series(ind.id, ind.label, "FRED", dates, tuple(values)))

    ten = _fred(INDICATORS[1], [4.0, 4.1, 4.3])                 # DGS10, pct
    assert _level(ten) == "4.30%" and _chg(ten, ten.chg_1d) == "+20.0bp"
    hy = _fred(INDICATORS[9], [3.2, 3.5])                        # HY OAS, bp
    assert _level(hy) == "350bp" and _chg(hy, hy.chg_1d) == "+30.0bp"
    eur = _fred(INDICATORS[11], [1.08, 1.0850])                  # EUR/USD, fx < 20
    assert _level(eur) == "1.0850" and _chg(eur, eur.chg_1d) == "+0.0050"
    jpy = _fred(INDICATORS[12], [150.0, 149.5])                  # USD/JPY, fx >= 20
    assert _level(jpy) == "149.50" and _chg(jpy, jpy.chg_1d) == "-0.50"
    vix = _fred(INDICATORS[14], [18.0, 20.25])                   # level
    assert _level(vix) == "20.25" and _chg(vix, vix.chg_3m) == "-"
    assert _chg(vix, 1234.5) == "+1234.50"

    sheet = macro_sheet(source="synthetic", days=300)
    for r in sheet.rows:
        assert _level(r) and _chg(r, r.chg_1d)
    for which, (title, kind) in _REPORTS.items():
        assert insights.report_prompt(kind), kind
    assert build_macro_page.__name__ == "build_macro_page"
    print("ok")
