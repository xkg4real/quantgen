"""The AI analysis block every quant page ends with.

Layout contract, same on all pages:

  * The **local narrative** is always present — written the moment results
    exist, engine-labeled "local", no network involved.
  * The **deep analysis** button sends the computed payload to the Claude API
    and streams the written result into the same card. Unconfigured or failed,
    the card says exactly why and the page loses nothing else.

The payload the button sends contains the caller's computed market results — this module
never reaches back into the app for more context, so what the model saw is
the computed results with private account fields excluded.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from core.quant import insights
from core.i18n import LocaleContext
from core.research.ai_connection import error_message
from core.research.ai_payload import filter_analysis_fields
from core.theme import RADII, active
from ui.components import chip, notice


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


def analysis_panel(page: ft.Page, *, kind: str, narrative: str,
                   payload_fn: Callable[[], dict],
                   deep_fn: Callable[..., "insights.Analysis"] | None = None) -> ft.Control:
    """`deep_fn(kind, payload, question=...)` defaults to the equity engine's
    `deep_analysis`; the FICC pages pass `core.ficc.insights.deep_analysis`,
    which appends the report-format instructions for the daily/weekly reads."""
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
            result = deep(kind, filter_analysis_fields(payload_fn()), question=question.value or "")
            if result.error:
                deep_host.controls = [_ErrorNotice(result, page)]
            else:
                deep_host.controls = [
                    ft.Row([chip(f"engine: {result.engine}", "accent")], spacing=6),
                    ft.Text(result.text, size=13, color=pal.text, selectable=True),
                ]
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
                ft.Text("Analysis", size=15, weight=ft.FontWeight.W_600,
                        color=pal.text),
                chip("engine: local", "muted")], spacing=8),
        ft.Text(narrative, size=13, color=pal.text, selectable=True),
        ft.Divider(color=pal.border),
        ft.Row([question, button, busy], spacing=10),
        ft.Text("Deep analysis sends calculated results and your question to Anthropic. "
                "Account holdings and balances are excluded. Do not include private account details in your question.",
                size=11, color=pal.muted),
    ]
    if not ready:
        rows.append(ft.Text("Deep analysis needs ANTHROPIC_API_KEY in .env; "
                            "the local read above works without it.",
                            size=11, color=pal.muted))
    rows.append(deep_host)
    return ft.Container(ft.Column(rows, spacing=10), padding=16,
                        bgcolor=pal.surface, border=ft.Border.all(1, pal.border),
                        border_radius=RADII["lg"])
