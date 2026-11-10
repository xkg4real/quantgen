"""Display helpers for the FICC and market pages (Structuring, FX, Bonds,
Derivatives, ETF, Crypto, KRX), owner UI review 2026-11-10.

One form-row shape so every input sits on the same top baseline and wraps
cleanly; a run button centred on the field height; a hidden data-source
selector that keeps a valid value (the app chooses the provider itself); and
Korean wording for tiles, chips and banners whose English text is built from
numbers (the exact-string catalogue cannot match an f-string).
"""
from __future__ import annotations

from typing import Iterable, Optional

import flet as ft

from ui.components import LocalText, chip

FIELD_HEIGHT = 48          # outlined TextField / Dropdown box height at the default density
GAP = 12                   # 8 px rhythm: 8 / 12 / 16 / 24


def form_row(controls: Iterable[ft.Control], *, visible: bool = True) -> ft.Row:
    """Inputs top-aligned on one baseline (a helper line under one field never
    shifts the others), 12 px apart, wrapping to the next line as a whole field.
    Children must have a fixed width: never `expand` inside a wrapping row."""
    return ft.Row(list(controls), spacing=GAP, run_spacing=GAP, wrap=True, visible=visible,
                  vertical_alignment=ft.CrossAxisAlignment.START)


def action(button: ft.Control, busy: Optional[ft.Control] = None) -> ft.Container:
    """The run button (and its progress ring) centred on the field box height.
    No `alignment` on the container: an aligned container fills the whole
    wrap width and would push the button onto a line of its own."""
    items = [button] + ([busy] if busy is not None else [])
    return ft.Container(ft.Row(items, spacing=GAP, tight=True,
                               vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        height=FIELD_HEIGHT)


def hide_source(dropdown: ft.Dropdown, value: str) -> ft.Dropdown:
    """Hide a data-source selector but keep the control: tests and self-checks
    still find it by label and set it (e.g. to 'synthetic'). Its value stays a
    member of its options. Results name the provider that actually answered."""
    keys = [o.key for o in dropdown.options or []]
    if value not in keys:
        raise ValueError(f"{value!r} is not one of {keys}")
    dropdown.value = value
    dropdown.visible = False
    return dropdown


def with_helper(field: ft.TextField, english: str) -> ft.TextField:
    """A short line under the box ('Optional', 'Blank = nearest') so the label
    itself stays short and never wraps inside the box. `translate_controls`
    does not visit `helper`, so the field translates it through the same
    exact-string catalogue when the page locale is applied."""
    field.helper = english

    def render_locale(ctx, f=field, source=english):
        f.ctx = ctx
        f.helper = ctx.text(source)

    field.render_locale = render_locale
    return field


def _local(text: ft.Text, ko: str) -> ft.Text:
    return LocalText(ko, text.value, size=text.size, color=text.color, weight=text.weight,
                     expand=text.expand, selectable=text.selectable, font_family=text.font_family)


def ko_stat(tile, ko: str):
    """Korean label for a `stat` tile whose English label is dynamic. Anything
    that is not a stat tile (a test double, for instance) is returned as is."""
    col = getattr(tile, "content", None)
    items = getattr(col, "controls", None)
    if isinstance(col, ft.Column) and items and isinstance(items[0], ft.Text) \
            and isinstance(items[0].value, str):
        items[0] = _local(items[0], ko)
    return tile


# Verdict codes never change (repository policy); Korean shows their meaning beside them.
VERDICT_KO = {"PASS": "통과", "REVISE": "보완 필요", "REJECT": "기각",
              "INSUFFICIENT_DATA": "데이터 부족", "NOT_RUN": "실행 안 됨"}


def verdict_ko(code) -> str:
    """'REJECT' -> '기각 · REJECT'; anything else comes back unchanged."""
    text = str(code)
    return f"{VERDICT_KO[text]} · {text}" if text in VERDICT_KO else text


def ko_verdict(tile):
    """A `stat` tile whose value is a verdict code reads '기각 · REJECT' in Korean."""
    col = getattr(tile, "content", None)
    items = getattr(col, "controls", None)
    if isinstance(col, ft.Column) and items and len(items) > 1 and isinstance(items[1], ft.Text) \
            and str(items[1].value) in VERDICT_KO:
        items[1] = _local(items[1], verdict_ko(items[1].value))
    return tile


def ko_notice(box, ko: str):
    """Korean wording for a `notice` banner whose English text is dynamic."""
    row = getattr(box, "content", None)
    items = getattr(row, "controls", None)
    if isinstance(row, ft.Row) and items and len(items) > 1 and isinstance(items[1], ft.Text) \
            and isinstance(items[1].value, str):
        items[1] = _local(items[1], ko)
    return box


def synthetic_notice(ko: str, en: str, detail: str = "") -> ft.Control:
    """The loud 'this is simulated data' banner, short enough to read, with the
    provider's own message (often a long chain of connection errors) folded
    underneath instead of filling the screen. Nothing is dropped: the detail
    stays one click away and selectable."""
    from ui.components import colour_for, notice
    box = ko_notice(notice(en, "error", icon=ft.Icons.SCIENCE_OUTLINED), ko)
    if not (detail or "").strip():
        return box
    more = ft.ExpansionTile(
        title=ft.Text("Provider message (why the data is simulated)", size=12, color=colour_for("muted")),
        controls=[ft.Container(ft.Text(detail.strip(), size=12, color=colour_for("muted"), selectable=True),
                               padding=ft.Padding(16, 0, 16, 12))],
        tile_padding=ft.Padding(16, 0, 16, 0), dense=True)
    return ft.Column([box, more], spacing=4)


def lchip(ko: str, en: str, token: str = "muted", *, tooltip: str = "") -> ft.Container:
    """A `chip` with authored Korean and English wording (dynamic values)."""
    c = chip(en, token, tooltip=tooltip)
    if isinstance(c.content, ft.Text):
        c.content = _local(c.content, ko)
    return c


def ltext(ko: str, en: str, **kwargs) -> LocalText:
    return LocalText(ko, en, **kwargs)
