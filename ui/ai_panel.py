"""The AI analysis block every quant page ends with.

Layout contract, same on all pages:

  * The **local narrative** is always present — written the moment results
    exist, engine-labeled "local", no network involved.
  * The **deep analysis** button sends the computed payload to the Claude API
    and shows the written result in the same card. Unconfigured or failed,
    the card says exactly why and the page loses nothing else.

The payload the button sends contains the caller's computed market results — this module
never reaches back into the app for more context, so what the model saw is
the computed results with private account fields excluded.

The local read is shown as a scannable list (owner UI review, 2026-11-10): a page may pass
`sections` (headings with bullet lines, or a callable that writes them for the page's
language); otherwise the narrative is split into sentences, one bullet each. The full
narrative text is never dropped: it is the block's `value`, and with sections it stays
available in an expandable list under them.
"""
from __future__ import annotations

from typing import Callable, Sequence, Union

import flet as ft

from core.quant import insights
from core.i18n import LocaleContext
from core.research.ai_connection import error_message
from core.research.ai_output_check import AI_LABEL, NumberCheck, check_line
from core.research.ai_payload import filter_analysis_fields
from core.theme import RADII, active
from ui.components import LocalText, chip, notice

Sections = Sequence[tuple[str, Sequence[str]]]

# The sentence splitter lives in the Flet-free ui.narrative_sections so the native app can share it;
# it is re-exported here for existing callers.
from ui.narrative_sections import split_sentences  # noqa: E402,F401


def _literal(value: str, **kwargs) -> ft.Text:
    """Text already in the page language; the static catalogue must not rewrite it again."""
    return ft.Text(value, data={"qg_literal_value": True}, **kwargs)


def _bullets(lines: Sequence[str]) -> list[ft.Control]:
    pal = active()
    style = ft.TextStyle(height=1.45)
    if len(lines) == 1:
        return [_literal(lines[0], size=13, color=pal.text, selectable=True, style=style)]
    return [ft.Row([_literal("•", size=13, color=pal.accent, weight=ft.FontWeight.BOLD),
                    _literal(line, size=13, color=pal.text, selectable=True, style=style, expand=True)],
                   spacing=8, vertical_alignment=ft.CrossAxisAlignment.START) for line in lines]


class _NarrativeBlock(ft.Column):
    """The local read as headed bullet lists. `value` is the full narrative, unchanged."""

    def __init__(self, narrative: str, sections, page):
        super().__init__(spacing=12)
        self.qg_narrative = narrative
        self.qg_sections = sections
        ctx = getattr(page, "qg_locale", None)
        self.paint(ctx if isinstance(ctx, LocaleContext) else None)

    @property
    def value(self) -> str:
        return self.qg_narrative

    def render_locale(self, ctx) -> None:
        self.ctx = ctx
        self.paint(ctx)

    def paint(self, ctx) -> None:
        pal = active()
        # The paragraph is the old single Text: the catalogue translates it as before, and it stays
        # selectable as one piece under the list.
        paragraph = ft.Text(self.qg_narrative, size=13, color=pal.text, selectable=True,
                            style=ft.TextStyle(height=1.45))
        # The bullets read the same translation, sentence by sentence.
        text = ctx.text(self.qg_narrative) if ctx is not None else str(self.qg_narrative)
        sentences = split_sentences(text)
        if self.qg_sections is None and len(sentences) <= 1:
            self.controls = [paragraph]
            return
        korean = getattr(ctx, "language", "en") == "ko"
        blocks: list[ft.Control] = []
        if self.qg_sections is None:
            blocks.append(ft.Column(_bullets(sentences), spacing=6))
            more = "한 문단으로 보기" if korean else "Show as one paragraph"
        else:
            sections = (self.qg_sections(ctx or LocaleContext("en_US")) if callable(self.qg_sections)
                        else self.qg_sections)
            for heading, items in sections:
                blocks.append(ft.Column([_literal(str(heading), size=14, weight=ft.FontWeight.W_600, color=pal.text),
                                         *_bullets([str(x) for x in items])], spacing=6))
            # The full paragraph is the engine's English write-up unless the catalogue translated it.
            hangul = any("\uac00" <= ch <= "\ud7a3" for ch in text)
            more = ("전체 해설 원문 보기" if hangul else "영문 원문 보기") if korean else "Full local commentary"
        blocks.append(ft.ExpansionTile(
            title=_literal(more, size=13, weight=ft.FontWeight.W_500, color=pal.text),
            controls=[ft.Container(paragraph, padding=ft.Padding(0, 0, 0, 8))],
            tile_padding=ft.Padding(0, 0, 0, 0), expanded_cross_axis_alignment=ft.CrossAxisAlignment.START))
        self.controls = blocks


def _local_chip(ko: str, en: str, token: str = "muted") -> ft.Container:
    pal = active()
    colour = getattr(pal, token, pal.muted)
    return ft.Container(LocalText(ko, en, size=11, color=colour, weight=ft.FontWeight.W_500),
                        padding=ft.Padding(8, 3, 8, 3), bgcolor=pal.surface_2,
                        border=ft.Border.all(1, colour), border_radius=RADII["pill"])


class _SendNotice(ft.Text):
    """Explain the request contents before a click, including fixed instructions."""
    def __init__(self, page):
        super().__init__(size=11, color=active().muted)
        ctx = getattr(page, 'qg_locale', None)
        self.render_locale(ctx if isinstance(ctx, LocaleContext) else LocaleContext('en_US'))

    def render_locale(self, ctx):
        self.ctx = ctx
        self.value = (
            "Deep analysis sends the selected analysis type, calculated results and your question to Anthropic "
            "with QUANTGEN's fixed writing instructions. When needed, it also sends an explanation of missing, "
            "undefined or unbounded values. Account holdings and balances are excluded. "
            "Do not include private account details in your question."
            if ctx.language != 'ko' else
            '심층 분석은 선택한 분석 종류, 계산 결과와 질문을 QUANTGEN의 고정 작성 지침과 함께 Anthropic으로 보냅니다. '
            '누락되거나 정의되지 않은 값, 무한한 값이 있으면 그 표기 설명도 함께 보냅니다. '
            '계좌 보유 내역과 잔고는 제외됩니다. 질문에 비공개 계좌 정보를 넣지 마세요.'
        )


class _ErrorNotice(ft.Container):
    """Re-render diagnostics on language changes without sending another request."""
    def __init__(self, result, page):
        super().__init__()
        self.result = result
        ctx = getattr(page, 'qg_locale', None)
        self.render_locale(ctx if isinstance(ctx, LocaleContext) else LocaleContext('en_US'))

    def render_locale(self, ctx):
        self.ctx = ctx
        code = getattr(self.result, 'error_code', '')
        message = error_message(code, ctx.language, getattr(self.result, 'http_status', None)) if code else self.result.error
        self.content = notice(message, 'error', icon=ft.Icons.CLOUD_OFF_OUTLINED)


class _CheckNotice(ft.Container):
    """'Not verified' label and the advisory number check under a finished reply.
    Re-rendered on language changes without sending another request."""
    def __init__(self, result, page):
        super().__init__()
        self.result = result
        ctx = getattr(page, 'qg_locale', None)
        self.render_locale(ctx if isinstance(ctx, LocaleContext) else LocaleContext('en_US'))

    def render_locale(self, ctx):
        self.ctx = ctx
        language = 'ko' if ctx.language == 'ko' else 'en'
        check = getattr(self.result, 'number_check', None)
        check = check if isinstance(check, NumberCheck) else None
        muted = active().muted
        self.content = ft.Column([ft.Text(AI_LABEL[language], size=11, color=muted),
                                  ft.Text(check_line(check, language), size=11, color=muted)], spacing=2)


def analysis_panel(page: ft.Page, *, kind: str, narrative: str,
                   payload_fn: Callable[[], dict],
                   deep_fn: Callable[..., "insights.Analysis"] | None = None,
                   sections: Union[Sections, Callable[[LocaleContext], Sections], None] = None) -> ft.Control:
    """`deep_fn(kind, payload, question=...)` defaults to the equity engine's
    `deep_analysis`; the FICC pages pass `core.ficc.insights.deep_analysis`,
    which appends the report-format instructions for the daily/weekly reads.

    `sections` (optional) organises the local read: `[(heading, [line, ...]), ...]`, or a callable
    taking the page's LocaleContext and returning that, re-run when the language changes. The
    narrative is still what `payload_fn` and the deep analysis are about; it is kept under the sections."""
    pal = active()
    deep = deep_fn or insights.deep_analysis
    question = ft.TextField(label="Ask the analyst something specific (optional)",
                            hint_text="e.g. how sensitive is this to the drift assumption?",
                            border_radius=RADII["md"], expand=True, dense=True)
    deep_host = ft.Column(spacing=8)
    busy = ft.ProgressRing(visible=False, width=18, height=18)

    def run_deep(e=None) -> None:
        busy.visible = True
        deep_host.controls = []
        page.update()

        def worker():
            try:
                try:
                    result = deep(kind, filter_analysis_fields(payload_fn()), question=question.value or "")
                except Exception:
                    # payload_fn (or a custom runner) raised; deep_analysis itself fails closed
                    # before posting. The spinner must still clear and the card must say why.
                    result = insights.Analysis("", "none", error_message("PAYLOAD_INVALID"), "PAYLOAD_INVALID")
                if result.error:
                    deep_host.controls = [_ErrorNotice(result, page)]
                else:
                    deep_host.controls = [
                        ft.Row([_local_chip(f"해설 엔진: {result.engine}", f"engine: {result.engine}", "accent")],
                               spacing=6),
                        ft.Text(result.text, size=13, color=pal.text, selectable=True),
                        _CheckNotice(result, page),
                    ]
            finally:
                busy.visible = False
                page.update()

        page.run_thread(worker)

    ready = insights.ai_ready()
    button = ft.Button("Deep analysis", icon=ft.Icons.AUTO_AWESOME,
                       on_click=run_deep, disabled=not ready,
                       tooltip=None if ready else
                       "Set ANTHROPIC_API_KEY to enable Claude deep analysis.")

    rows: list[ft.Control] = [
        ft.Row([ft.Icon(ft.Icons.INSIGHTS_OUTLINED, size=18, color=pal.accent),
                LocalText("분석 요약", "Analysis", size=15, weight=ft.FontWeight.W_600,
                          color=pal.text),
                chip("engine: local", "muted")], spacing=8),
        _NarrativeBlock(narrative, sections, page),
        ft.Divider(color=pal.border),
        ft.Row([question, button, busy], spacing=10),
        _SendNotice(page),
    ]
    if not ready:
        rows.append(ft.Text("Deep analysis needs ANTHROPIC_API_KEY in .env; "
                            "the local read above works without it.",
                            size=11, color=pal.muted))
    rows.append(deep_host)
    return ft.Container(ft.Column(rows, spacing=10), padding=16,
                        bgcolor=pal.surface, border=ft.Border.all(1, pal.border),
                        border_radius=RADII["lg"])
