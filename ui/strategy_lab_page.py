"""Strategy Lab — the validation scorecard and a live run of any strategy
family through the same gate.

Section one reads the model cards the study wrote (`docs/asset_expansion/
cards/*.json`): a verdict summary first, then one readable row per card (what
was tested, the verdict, why, the key numbers) and a detail view that keeps
every recorded line. Section two runs a family (trend switch, vol target,
cross-sectional momentum, TSMOM, crypto trend, risk parity, pairs) on symbols
the operator names, through the purged walk-forward and the full gate, and
shows the verdict in plain words before the statistics. N trials equals the
grid size; the card ledger says so. The app chooses the data provider itself
(`load_history(source="best")`); the provider that answered is shown with the
result.

Sentences built from numbers are authored in Korean and English
(core/research/strategy_display.py) and switch with the page language.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Callable, Optional

import flet as ft

from core.quant import insights
from core.quant import validate as V
from core.quant.history import HistoryError, load_history
from core.research import strategy_display as D
from core.theme import RADII, active
from ui.ai_panel import analysis_panel
from ui.components import LocalText, card, colour_for, empty_state, notice, number_field, parse_number, section
import ui.xcharts as xc
from core.research.strategy_workflow import FAMILIES, FAMILY_ID, _MARKET, register_trials, narrative, payload, _study_card  # noqa: F401
from core.research.strategy_workflow import narrative_sections
from core.research.strategy_workflow import run_family as _run_family
from core.research.strategy_exposure import EXPOSURE_HELP, exposure_lines

ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = ROOT / "docs" / "asset_expansion" / "cards"
_TOKEN = D.VERDICT_TOKEN
# The data-source selector is hidden (owner UI review 2026-11-10, as UI-8 did for Markets): the app asks
# load_history(source="best"). The control stays so scripts can still pick a provider.
SOURCE_OPTIONS = ("best", "auto", "yfinance", "kis", "fmp", "crypto", "synthetic")
MACRO_NOTE = ("v2 macro model cards (CARD-O / CARD-P) are under Macro → Model cards; this scorecard lists the "
              "asset-expansion study cards only.")
_DETAIL_KEY = "strategy-lab-card-detail"
_W600 = ft.FontWeight.W_600


def run_family(family: str, symbols: list[str], *, source: str = "best", cost_bps: Optional[float] = None,
               days: int = 5000, bootstrap_B: int = 1000) -> dict:
    return _run_family(family, symbols, source=source, cost_bps=cost_bps, days=days,
                       bootstrap_B=bootstrap_B, history_loader=load_history, trial_registrar=register_trials)


# --------------------------------------------------------------------------- #
# Small presentation helpers (this page only)
# --------------------------------------------------------------------------- #
def _language(ctx) -> str:
    return "ko" if getattr(ctx, "language", "en") == "ko" else "en"


def _page_language(page) -> str:
    return _language(getattr(page, "qg_locale", None))


def _text(value: str, *, size: int = 13, color: Optional[str] = None, weight=None, italic: bool = False,
          selectable: bool = False, height: Optional[float] = None, **kwargs) -> ft.Text:
    """Text already written in the page language: the static catalogue must not rewrite it."""
    return ft.Text(value, size=size, color=color or active().text, weight=weight, italic=italic,
                   selectable=selectable, data={"qg_literal_value": True},
                   style=ft.TextStyle(height=height) if height else None, **kwargs)


def _pill(value: str, token: str = "muted", *, size: int = 12, tooltip: str = "") -> ft.Container:
    pal = active()
    return ft.Container(_text(value, size=size, color=colour_for(token), weight=ft.FontWeight.W_500),
                        padding=ft.Padding(10, 4, 10, 4), bgcolor=pal.surface_2,
                        border=ft.Border.all(1, colour_for(token)), border_radius=RADII["pill"],
                        tooltip=tooltip or None)


class _Localized(ft.Container):
    """A display block rebuilt in the page language whenever the locale changes."""

    def __init__(self, build: Callable[[str], ft.Control], page=None, **kwargs):
        super().__init__(**kwargs)
        self.qg_build = build
        self.content = build(_page_language(page))

    def render_locale(self, ctx) -> None:
        self.ctx = ctx
        self.content = self.qg_build(_language(ctx))

    def refresh(self, page) -> None:
        self.content = self.qg_build(_page_language(page))


def _step(number: int, ko: str, en: str, intro_ko: str, intro_en: str) -> ft.Control:
    pal = active()
    badge = ft.Container(_text(str(number), size=13, color=pal.surface, weight=ft.FontWeight.BOLD),
                         width=26, height=26, bgcolor=pal.accent, border_radius=13, alignment=ft.Alignment.CENTER)
    return ft.Column([
        ft.Row([badge, LocalText(ko, en, size=17, weight=_W600, color=pal.text)], spacing=10,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        LocalText(intro_ko, intro_en, size=13, color=pal.muted),
    ], spacing=6)


def _labelled(label: str, body: list[ft.Control]) -> ft.Control:
    return ft.Column([_text(label, size=12, color=active().muted, weight=_W600), *body], spacing=4)


def _rows_header(labels: list[str], cols: list[dict]) -> ft.Control:
    pal = active()
    return ft.Container(
        ft.ResponsiveRow([ft.Container(_text(t, size=12, color=pal.muted, weight=_W600), col=c)
                          for t, c in zip(labels, cols)], columns=24, spacing=12, run_spacing=2),
        padding=ft.Padding(4, 0, 4, 8), border=ft.Border(bottom=ft.BorderSide(1, pal.border)))


def _row(cells: list[ft.Control], cols: list[dict], *, on_click=None, tooltip: str = "") -> ft.Container:
    return ft.Container(
        ft.ResponsiveRow([ft.Container(cell, col=c) for cell, c in zip(cells, cols)], columns=24, spacing=12,
                         run_spacing=6, vertical_alignment=ft.CrossAxisAlignment.START),
        padding=ft.Padding(4, 12, 4, 12), border=ft.Border(bottom=ft.BorderSide(1, active().border)),
        on_click=on_click, ink=on_click is not None, tooltip=tooltip or None)


# --------------------------------------------------------------------------- #
# Section 1 and 2: the study scorecard
# --------------------------------------------------------------------------- #
def _summary(cards: list[dict], lang: str) -> ft.Control:
    pal = active()
    counts = Counter(c["decision"] for c in cards)
    order = ["PASS", "REVISE", "REJECT"] + [k for k in ("INSUFFICIENT_DATA", "UNKNOWN") if counts.get(k)]
    span = max(3, 12 // len(order))
    tiles = []
    for code in order:
        colour = colour_for(D.VERDICT_TOKEN[code])
        tiles.append(ft.Container(
            ft.Column([
                ft.Row([_text(str(counts.get(code, 0)), size=36, weight=ft.FontWeight.BOLD, color=colour),
                        ft.Column([_text(D.pick(D.VERDICT[code], lang), size=16, weight=_W600),
                                   _text(code, size=12, weight=_W600, color=colour)], spacing=0)],
                       spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                _text(D.pick(D.VERDICT_MEANING[code], lang), size=13, color=pal.muted, height=1.4),
            ], spacing=8),
            col={"xs": 12, "sm": 6, "md": span}, padding=16, bgcolor=pal.surface,
            border=ft.Border.all(1.5, colour), border_radius=RADII["lg"]))
    total = (f"검증 카드 {len(cards)}개 · 연구 보고서의 판정을 그대로 보여 줍니다" if lang == "ko" else
             f"{len(cards)} study cards · the verdicts as the study recorded them")
    policy = ("PASS는 기본으로 제공하고, REVISE는 보완 목표와 함께 제공하며, REJECT와 INSUFFICIENT_DATA는 거절 사실이 "
              "보이도록 목록에 남깁니다. 모든 기록에는 수치, 기준, 표본이 함께 적혀 있습니다." if lang == "ko" else
              "PASS is offered by default; REVISE is offered with its revise target shown; REJECT and "
              "INSUFFICIENT_DATA are listed so the refusal is visible. Every line states the number, the threshold "
              "and the sample behind it.")
    return ft.Column([
        ft.ResponsiveRow(tiles, spacing=12, run_spacing=12),
        ft.Container(_text(total, size=12, color=pal.muted), tooltip=f"docs/asset_expansion/cards\n{policy}"),
    ], spacing=10)


_TABLE_COLS = [{"xs": 24, "md": 6}, {"xs": 8, "md": 2}, {"xs": 16, "md": 4}, {"xs": 24, "md": 7}, {"xs": 24, "md": 5}]


def _scorecard_rows(cards: list[dict], lang: str, on_pick) -> ft.Control:
    pal = active()
    heads = (["카드", "종류", "판정", "이유", "핵심 수치"] if lang == "ko" else
             ["Card", "Kind", "Verdict", "Why", "Key numbers"])
    rows: list[ft.Control] = [_rows_header(heads, _TABLE_COLS)]
    for c in cards:
        t = D.card_text(c)
        (reason, _) = D.reason_text(c["decision_reason"], c)
        numbers = [n for n in D.key_numbers(c, lang).split(" · ") if n]
        rows.append(_row([
            ft.Column([_text(D.pick(t.name, lang), size=13, weight=_W600),
                       _text(c["card_id"], size=11, color=pal.muted)], spacing=2),
            _text(D.pick(D.kind_label(c["kind"]), lang), size=12, color=pal.muted),
            ft.Row([_pill(D.pick(D.verdict_label(c["decision"]), lang), _TOKEN.get(c["decision"], "muted"))]),
            _text(D.pick(reason, lang), size=13, height=1.35),
            ft.Column([_text(n, size=12, color=pal.muted) for n in numbers], spacing=2),
        ], _TABLE_COLS, on_click=lambda e, cid=c["card_id"]: on_pick(cid)))
    return ft.Column(rows, spacing=0)


def _option_text(c: dict, lang: str) -> str:
    return f"{D.pick(D.card_text(c).name, lang)} — {D.pick(D.verdict_label(c['decision']), lang)}"


class _CardPicker(ft.Dropdown):
    """Card picker: human names and verdicts, the card id as secondary text in the menu."""

    def __init__(self, cards: list[dict], page=None, **kwargs):
        super().__init__(label="Card", options=[ft.dropdown.Option(c["card_id"], c["card_id"]) for c in cards],
                         **kwargs)
        self.qg_cards = cards
        self.paint(_page_language(page))

    def paint(self, lang: str) -> None:
        pal = active()
        self.label = "검증 카드 선택" if lang == "ko" else "Card"
        for option, c in zip(self.options, self.qg_cards):
            option.text = _option_text(c, lang)
            option.content = ft.Column([
                _text(D.pick(D.card_text(c).name, lang), size=14),
                _text(f"{c['card_id']} · {D.pick(D.verdict_label(c['decision']), lang)}", size=11, color=pal.muted),
            ], spacing=0)

    def render_locale(self, ctx) -> None:
        self.ctx = ctx
        self.paint(_language(ctx))


def _card_detail(c: Optional[dict], lang: str) -> ft.Control:
    pal = active()
    ko = lang == "ko"
    if not c:
        return _text("카드를 고르면 자세한 내용이 여기에 나옵니다." if ko else "Pick a card to see its details.",
                     size=13, color=pal.muted)
    t = D.card_text(c)
    (reason, _) = D.reason_text(c["decision_reason"], c)
    target = D.revise_target_text(c.get("revise_target"))
    code = c["decision"]
    blocks: list[ft.Control] = [
        ft.Row([
            ft.Column([_text(D.pick(t.name, lang), size=18, weight=_W600, selectable=True),
                       _text(f"{c['card_id']} · {D.pick(D.kind_label(c['kind']), lang)}", size=12, color=pal.muted)],
                      spacing=2, expand=True),
            _pill(D.pick(D.verdict_label(code), lang), _TOKEN.get(code, "muted"), size=13),
        ], vertical_alignment=ft.CrossAxisAlignment.START),
        _labelled("무엇을 검증했나" if ko else "What was tested",
                  [_text(D.pick(t.what, lang), size=13, selectable=True, height=1.4)]),
        _labelled("결과와 이유" if ko else "Verdict and why",
                  [_text(D.pick(D.VERDICT_MEANING.get(code, D.VERDICT_MEANING["UNKNOWN"]), lang), size=13,
                         color=pal.muted, height=1.4),
                   _text(D.pick(reason, lang), size=14, weight=ft.FontWeight.W_500, selectable=True, height=1.4)]),
    ]
    if target:
        blocks.append(_labelled("다음 단계" if ko else "Next step", [_text(D.pick(target, lang), size=13, height=1.4)]))
    numbers = [n for n in D.key_numbers(c, lang).split(" · ") if n and n != "—"]
    if numbers:
        blocks.append(_labelled("핵심 수치" if ko else "Key numbers",
                                [ft.Row([_pill(n, "text") for n in numbers], spacing=8, run_spacing=8, wrap=True)]))
    if isinstance(c.get("stats", {}).get("sr_oos"), (int, float)):
        checks = D.strategy_checks({**c["stats"], "ci90": (c.get("tests") or {}).get("ci90")})
        blocks.append(_labelled("검증 기준별 결과" if ko else "Result per criterion", [_checklist(checks, lang)]))
    evidence = [_text(c["hypothesis"], size=12, italic=True, selectable=True, height=1.4)] if c["hypothesis"] else []
    evidence += [_text("• " + ln, size=12, selectable=True, height=1.4) for ln in c.get("lines", [])]
    evidence.append(ft.Row([_pill(f"seed {c.get('seed')}"),
                            _pill(f"results md5 {str(c.get('results_md5', ''))[:8]}")], spacing=6, wrap=True))
    blocks.append(ft.ExpansionTile(
        title=_text((f"검증 기록 원문 보기 (영문 {len(c.get('lines', []))}줄)" if ko else
                     f"Recorded evidence ({len(c.get('lines', []))} lines)"), size=13, weight=ft.FontWeight.W_500),
        controls=[ft.Container(ft.Column(evidence, spacing=6), padding=ft.Padding(16, 0, 16, 12))],
        tile_padding=ft.Padding(0, 0, 0, 0), expanded_cross_axis_alignment=ft.CrossAxisAlignment.START))
    if c.get("citations"):
        blocks.append(_labelled("출처" if ko else "Sources",
                                [_text("; ".join(c["citations"]), size=12, color=pal.muted, selectable=True)]))
    return ft.Container(ft.Column(blocks, spacing=14), padding=20, bgcolor=pal.surface,
                        border=ft.Border.all(1, pal.border), border_radius=RADII["lg"])


# --------------------------------------------------------------------------- #
# Section 3: a run result
# --------------------------------------------------------------------------- #
_VERDICT_ICON = {"PASS": ft.Icons.CHECK_CIRCLE_OUTLINE, "REVISE": ft.Icons.BUILD_CIRCLE_OUTLINED,
                 "REJECT": ft.Icons.CANCEL_OUTLINED, "INSUFFICIENT_DATA": ft.Icons.HELP_OUTLINE,
                 "WITHHELD": ft.Icons.REMOVE_CIRCLE_OUTLINE}
_STATUS_ICON = {"pass": ft.Icons.CHECK_CIRCLE_OUTLINE, "fail": ft.Icons.CANCEL_OUTLINED,
                "info": ft.Icons.INFO_OUTLINE, "na": ft.Icons.REMOVE_CIRCLE_OUTLINE}


def _verdict_banner(v: dict, lang: str) -> ft.Control:
    pal = active()
    colour = colour_for(v["token"])
    code = v["code"] if v["decision"] != "WITHHELD" else "NO VERDICT"
    label = (f"{D.pick(D.VERDICT.get(v['decision'], ('판정 없음', 'No verdict')), lang)} · {code}"
             if lang == "ko" else code)
    body: list[ft.Control] = [
        ft.Row([ft.Icon(_VERDICT_ICON.get(v["decision"], ft.Icons.HELP_OUTLINE), size=30, color=colour),
                ft.Column([_text(D.pick(v["title"], lang), size=20, weight=ft.FontWeight.BOLD, height=1.3),
                           ft.Row([_pill(label, v["token"], size=12)])], spacing=6, expand=True)],
               spacing=14, vertical_alignment=ft.CrossAxisAlignment.START),
        ft.Column([ft.Row([_text("•", size=14, color=colour, weight=ft.FontWeight.BOLD),
                           _text(D.pick(x, lang), size=14, selectable=True, height=1.45, expand=True)],
                          spacing=8, vertical_alignment=ft.CrossAxisAlignment.START) for x in v["reasons"]],
                  spacing=6),
    ]
    if v["next"]:
        body.append(ft.Row([ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=pal.muted),
                            _text(("다음 단계: " if lang == "ko" else "Next step: ") + D.pick(v["next"], lang),
                                  size=13, color=pal.muted, height=1.4, expand=True)],
                           spacing=8, vertical_alignment=ft.CrossAxisAlignment.START))
    return ft.Container(ft.Column(body, spacing=12), padding=20, bgcolor=pal.surface,
                        border=ft.Border.all(2, colour), border_radius=RADII["lg"])


def _metric_tile(c: D.Check, lang: str) -> ft.Control:
    pal = active()
    token = D.STATUS_TOKEN[c.status]
    colour = colour_for(token)
    detail = D.pick(c.detail, lang)
    threshold = D.pick(c.threshold, lang)
    if c.gated:
        threshold = ("기준 " if lang == "ko" else "Needs ") + threshold
    rows: list[ft.Control] = [
        _text(D.pick(c.label, lang), size=12, color=pal.muted, height=1.3),
        _text(c.value, size=22, weight=_W600, color=colour if c.status in ("pass", "fail") else pal.text),
        ft.Row([ft.Icon(_STATUS_ICON[c.status], size=14, color=colour),
                _text(D.pick(D.STATUS[c.status], lang), size=12, weight=_W600, color=colour)], spacing=4),
        _text(threshold, size=11, color=pal.muted),
    ]
    if detail:
        rows.append(_text(detail, size=11, color=pal.muted))
    return ft.Container(ft.Column(rows, spacing=4), col={"xs": 12, "sm": 6, "md": 4, "lg": 3, "xl": 2},
                        padding=ft.Padding(14, 12, 14, 12), bgcolor=pal.surface_2,
                        border=ft.Border.all(1, colour if c.status == "fail" else pal.border),
                        border_radius=RADII["md"], tooltip=D.pick(c.help, lang))


def _metric_grid(checks: list[D.Check], lang: str) -> ft.Control:
    return ft.ResponsiveRow([_metric_tile(c, lang) for c in checks], spacing=10, run_spacing=10)


_CHECK_COLS = [{"xs": 24, "md": 7}, {"xs": 12, "md": 7}, {"xs": 12, "md": 6}, {"xs": 24, "md": 4}]


def _checklist(checks: list[D.Check], lang: str) -> ft.Control:
    pal = active()
    heads = ["검증 항목", "결과", "기준", "판정"] if lang == "ko" else ["Criterion", "Result", "Needs", "Verdict"]
    rows: list[ft.Control] = [_rows_header(heads, _CHECK_COLS)]
    for c in checks:
        colour = colour_for(D.STATUS_TOKEN[c.status])
        detail = D.pick(c.detail, lang)
        rows.append(_row([
            ft.Row([_text(D.pick(c.label, lang), size=13, weight=ft.FontWeight.W_500),
                    ft.Icon(ft.Icons.HELP_OUTLINE, size=14, color=pal.muted, tooltip=D.pick(c.help, lang))],
                   spacing=6, wrap=True),
            _text(c.value + (f"  ({detail})" if detail else ""), size=13),
            _text(D.pick(c.threshold, lang), size=12, color=pal.muted),
            ft.Row([ft.Icon(_STATUS_ICON[c.status], size=16, color=colour),
                    _text(D.pick(D.STATUS[c.status], lang), size=13, weight=_W600, color=colour)], spacing=4),
        ], _CHECK_COLS))
    return ft.Column(rows, spacing=0)


def _provenance(r: dict, lang: str) -> ft.Control:
    ko = lang == "ko"
    chips = [_pill(("데이터: " if ko else "Data: ") + f"{D.pick(D.source_label(src), lang)} · {s}"
                   + ((" · 캐시" if ko else " · cached") if "cached" in note else ""),
                   "success" if src != "SYNTHETIC" else "muted", size=11, tooltip=note)
             for s, src, note in zip(r["symbols"], r["sources"], r["notes"])]
    chips.append(_pill(D.pick(D.walk_forward_text(r["wf"].note), lang), "muted", size=11, tooltip=r["wf"].note))
    if r.get("ledger_n"):
        chips.append(_pill((f"{FAMILY_ID[r['family']]} 계열 누적 설정 {r['ledger_n']}개" if ko else
                            f"{FAMILY_ID[r['family']]} ledger: {r['ledger_n']} configurations"), "muted", size=11,
                           tooltip=("이 계열에서 지금까지 실행한 모든 설정 수입니다. 위의 보정 샤프는 이번 실행의 설정만 셉니다."
                                    if ko else "Every configuration ever run in this family. The deflated Sharpe "
                                               "above counts only this run's grid.")))
    return ft.Row(chips, spacing=6, run_spacing=6, wrap=True)


def _exposure_block(r: dict) -> Optional[ft.Control]:
    en = exposure_lines(r.get("exposure"))
    if not en:
        return None
    ko = D.exposure_lines_ko(r.get("exposure"))
    pal = active()
    return ft.Container(
        ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=pal.accent),
                ft.Column([LocalText(k, e, size=13, color=pal.text, selectable=True,
                                     style=ft.TextStyle(height=1.4)) for k, e in zip(ko, en)],
                          spacing=6, expand=True)], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
        padding=14, bgcolor=pal.surface_2, border=ft.Border.all(1, pal.accent), border_radius=RADII["md"])


def _plain_notice(text: str, token: str, icon=ft.Icons.ERROR_OUTLINE) -> ft.Control:
    pal = active()
    return ft.Container(
        ft.Row([ft.Icon(icon, size=18, color=colour_for(token)),
                _text(text, size=13, selectable=True, height=1.4, expand=True)], spacing=10,
               vertical_alignment=ft.CrossAxisAlignment.START),
        padding=14, bgcolor=pal.surface_2, border=ft.Border.all(1, colour_for(token)), border_radius=RADII["md"])


def build_strategy_lab_page(page: ft.Page, on_open_settings: Optional[Callable] = None) -> ft.Control:
    pal = active()
    cards = load_cards()
    body = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=16)

    # ---- sections 1 and 2: the study scorecard ------------------------------------
    picker = _CardPicker(cards, page, value=cards[0]["card_id"] if cards else None, menu_height=420, width=600)
    detail = _Localized(lambda lang: _card_detail(next((x for x in cards if x["card_id"] == picker.value), None),
                                                  lang), page, key=ft.ScrollKey(_DETAIL_KEY))

    def show_card(e=None) -> None:
        detail.refresh(page)
        page.update()

    def pick_card(card_id: str) -> None:
        picker.value = card_id
        show_card()
        try:
            page.run_task(body.scroll_to, scroll_key=_DETAIL_KEY, duration=300)
        except Exception:                         # a page without a session (tests) has nothing to scroll
            pass

    picker.on_select = show_card
    macro_note = ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=pal.muted),
                         ft.Text(MACRO_NOTE, size=12, color=pal.muted, expand=True)], spacing=8)
    if cards:
        study = [
            _step(1, "검증 결과 요약", "Validation summary",
                  "연구에서 검증한 전략과 모형이 어떤 판정을 받았는지 한눈에 봅니다.",
                  "How the strategies and models of the validation study were judged, at a glance."),
            _Localized(lambda lang: _summary(cards, lang), page),
            macro_note,
            ft.Divider(color=pal.border),
            _step(2, "카드별 결과", "Result per card",
                  "카드마다 무엇을 검증했고, 왜 그 판정이 나왔는지 쉬운 말로 정리했습니다. 줄을 누르면 아래에서 자세히 볼 수 있습니다.",
                  "What each card tested and why it got its verdict, in plain words. Click a row for the details below."),
            _Localized(lambda lang: _scorecard_rows(cards, lang, pick_card), page),
            LocalText("선택한 카드 자세히 보기", "Card details", size=15, weight=_W600, color=pal.text),
            picker,
            detail,
        ]
    else:
        study = [
            _step(1, "검증 결과 요약", "Validation summary",
                  "연구에서 검증한 전략과 모형이 어떤 판정을 받았는지 한눈에 봅니다.",
                  "How the strategies and models of the validation study were judged, at a glance."),
            notice("No cards yet: run python docs/asset_expansion_study.py", "accent"),
            macro_note,
        ]

    # ---- section 3: run a family -----------------------------------------------------
    # A Dropdown sizes to its own width, not its grid column: give it room for the longest family name.
    family = ft.Dropdown(label="Strategy family", value="trend_switch", width=420,
                         options=[ft.dropdown.Option(k, v[0]) for k, v in FAMILIES.items()])
    symbols = ft.TextField(label="Symbols (comma-separated)", value="SPY, QQQ, TLT, GLD", border_radius=RADII["md"],
                           hint_text="069500, 152380 · BTC-USD · KRW-BTC · 005935.KS, 005930.KS",
                           col={"xs": 12, "md": 6})
    source = ft.Dropdown(label="Source", value="best", visible=False,
                         options=[ft.dropdown.Option(k, k) for k in SOURCE_OPTIONS])
    cost = number_field("Cost per side (bp)", "", hint_text="table rate", col={"xs": 6, "md": 3},
                        tooltip="Blank charges QUANTGEN's table rate. A lower cost runs as a sensitivity with no verdict.")
    days = number_field("Sessions", "5000", col={"xs": 6, "md": 3},
                        tooltip="How many recent trading days to load for each symbol.")
    busy = ft.Row([ft.ProgressRing(width=20, height=20),
                   LocalText("검증하는 중입니다… 30초 정도 걸릴 수 있습니다.",
                             "Validating… this can take about 30 seconds.", size=13, color=pal.muted)],
                  spacing=10, visible=False)
    host = ft.Column(spacing=16)

    def run(e=None) -> None:
        busy.visible = True; host.controls = []; page.update()

        def failed(exc: Exception) -> None:
            message = str(exc) if isinstance(exc, (HistoryError, ValueError)) else f"{type(exc).__name__}: {exc}"
            host.controls = [_Localized(lambda lang: _plain_notice(
                (f"검증을 실행하지 못했습니다. 입력과 연결을 확인하세요. ({message})" if lang == "ko" else message),
                "error"), page)]
            busy.visible = False; page.update()

        def worker():
            try:
                syms = [s.strip() for s in (symbols.value or "").split(",") if s.strip()]
                r = run_family(family.value or "trend_switch", syms, source=source.value or "best",
                               cost_bps=parse_number(cost.value) if (cost.value or "").strip() else None,
                               days=int(parse_number(days.value or "5000")))
            except Exception as exc:
                failed(exc); return
            sc = r["score"]
            verdict = D.run_verdict(r)
            blocks: list[ft.Control] = [_Localized(lambda lang: _verdict_banner(verdict, lang), page)]
            if "SYNTHETIC" in r["sources"]:
                blocks.append(notice("Synthetic data in the panel: the verdict below is a toy.", "error",
                                     icon=ft.Icons.SCIENCE_OUTLINED))
            if r.get("convention"):
                blocks.append(_Localized(lambda lang: _plain_notice(D.pick(D.convention_text(r["convention"]), lang),
                                                                    "error"), page))
            exposure = _exposure_block(r)
            if exposure is not None:
                blocks.append(exposure)
            blocks.append(_Localized(lambda lang: _provenance(r, lang), page))
            blocks.append(_Localized(lambda lang: _metric_grid(verdict["checks"], lang), page))
            # equity_curve includes initial wealth 1 before the first OOS return.
            # Give that point its preceding price date; never drop an OOS return.
            first = r["panel"].dates.index(r["wf"].dates[0])
            equity_dates = (r["panel"].dates[first - 1], *r["wf"].dates)
            blocks.append(card(ft.Column([
                LocalText("처음 보는 구간(표본 외)의 누적 수익: 전략과 벤치마크(동일 비중 보유)",
                          "Out-of-sample growth of 1: strategy and benchmark (equal-weight hold)",
                          size=15, weight=_W600, color=pal.text),
                xc.equity_chart(equity_dates, r["equity"], r["bench_equity"],
                                title=f"{r['label']}: out-of-sample equity"),
            ], spacing=10)))
            blocks.append(card(ft.Column([
                LocalText("검증 항목별 결과", "Result per criterion", size=15, weight=_W600, color=pal.text),
                _Localized(lambda lang: _checklist(verdict["checks"], lang), page),
                ft.ExpansionTile(
                    title=LocalText("검증 기록 원문 보기 (영문)", "Full gate lines", size=13,
                                    weight=ft.FontWeight.W_500),
                    controls=[ft.Container(ft.Column([ft.Text("• " + ln, size=12, color=pal.text, selectable=True,
                                                              data={"qg_literal_value": True})
                                                      for ln in sc.lines], spacing=6),
                                           padding=ft.Padding(16, 0, 16, 12))],
                    tile_padding=ft.Padding(0, 0, 0, 0), expanded_cross_axis_alignment=ft.CrossAxisAlignment.START),
            ], spacing=10)))
            blocks.append(analysis_panel(page, kind="strategy_gate", narrative=narrative(r),
                                         payload_fn=lambda p=payload(r): p, deep_fn=insights.deep_analysis,
                                         sections=lambda ctx, r=r: narrative_sections(r, _language(ctx))))
            host.controls = blocks; busy.visible = False; page.update()

        page.run_thread(worker)

    host.controls = [empty_state("Pick a family and symbols, then press Run",
                                 "The same gate as the study: purged walk-forward (train 756 / test 126 sessions), "
                                 "a block-bootstrap Sharpe interval, deflated Sharpe, PBO, 2× costs, parameter "
                                 "plateau and a benchmark test.",
                                 icon=ft.Icons.SCIENCE_OUTLINED)]
    lab = [
        _step(3, "직접 검증해 보기", "Test a strategy yourself",
              "전략 종류와 종목을 고르고 실행을 누르면 연구와 같은 기준으로 검증합니다. 가격 자료는 앱이 알맞은 "
              "제공처에서 자동으로 가져오고, 결과에 어디서 가져왔는지 표시합니다.",
              "Choose a strategy family and symbols and press Run: the same criteria as the study apply. The app "
              "fetches prices from a suitable provider itself and shows which one answered."),
        ft.ExpansionTile(
            title=LocalText("변동성 목표·암호화폐 추세 전략은 자산마다 따로 비중을 정해, 자산이 N개면 총 노출이 최대 "
                            "N배가 될 수 있습니다.",
                            "Volatility target and Crypto trend size each asset separately: with N assets, total "
                            "exposure can reach N×.", size=13, color=pal.text),
            leading=ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=pal.accent),
            controls=[ft.Container(ft.Text(EXPOSURE_HELP, size=13, color=pal.text, selectable=True),
                                   padding=ft.Padding(16, 0, 16, 12))],
            tile_padding=ft.Padding(4, 0, 4, 0), expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
            bgcolor=pal.surface_2, collapsed_bgcolor=pal.surface_2,
            shape=ft.RoundedRectangleBorder(radius=RADII["md"])),
        ft.Container(ft.Column([
            ft.ResponsiveRow([ft.Container(family, col={"xs": 12}), symbols, cost, days, source],
                             spacing=12, run_spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            LocalText("예: 미국 SPY, QQQ · 국내 ETF 069500 · 코인 BTC-USD, KRW-BTC · 페어 전략은 두 종목(y, x 순서). "
                      "거래비용을 비워 두면 QUANTGEN 기준 비용을 씁니다.",
                      "Examples: US SPY, QQQ · Korean ETF 069500 · crypto BTC-USD, KRW-BTC · pairs take two symbols "
                      "(y then x). A blank cost charges QUANTGEN's table rate.", size=12, color=pal.muted),
            ft.Row([ft.Button("Run", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=run), busy], spacing=14,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=12), padding=16, bgcolor=pal.surface, border=ft.Border.all(1, pal.border),
            border_radius=RADII["lg"]),
        host,
    ]
    body.controls = [*study, ft.Divider(color=pal.border), *lab]
    return ft.Column([
        section("Strategy Lab", subtitle="See which strategies and models passed validation and why, then test a "
                                         "strategy yourself against the same criteria."),
        body,
    ], spacing=14, expand=True)


def load_cards() -> list[dict]:
    cards = [_study_card(c) for c in V.load_cards(CARDS_DIR) if isinstance(c, dict)]
    return sorted(cards, key=lambda c: ({"PASS": 0, "REVISE": 1, "REJECT": 2}.get(c["decision"], 3), c["card_id"]))


if __name__ == "__main__":
    r = run_family("trend_switch", ["AAA", "BBB", "CCC"], source="synthetic", cost_bps=5.0, days=1500, bootstrap_B=200)
    assert r["score"].decision in V.DECISIONS and r["equity"].size > 100 and len(r["score"].lines) >= 8
    assert "decision" in narrative(r) and payload(r)["grid_size"] == 12
    assert r["withheld"] and payload(r)["decision"] == "WITHHELD", "5 bp is below the 50 bp US row: no verdict"
    assert "decision" not in payload(r)["stats"] and payload(r)["revise_target"] is None, "no verdict in the payload"
    assert D.run_verdict(r)["code"] == "NO VERDICT", "a withheld run shows no verdict"
    t = run_family("trend_switch", ["AAA", "BBB", "CCC"], source="synthetic", days=1500, bootstrap_B=200)
    assert t["cost_bps"] == 50.0 and not t["withheld"], "blank cost charges the table rate and keeps the verdict"
    assert D.run_verdict(t)["code"] == t["score"].decision
    p = run_family("pairs", ["AAA", "BBB"], source="synthetic", cost_bps=5.0, days=1500, bootstrap_B=200)
    assert p["bench_equity"] is None and p["score"].decision in V.DECISIONS
    print("ok", r["score"].decision, p["score"].decision)
