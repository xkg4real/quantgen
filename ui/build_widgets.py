"""Locale-authored chips and notices for the Build/Portfolio pages (owner UI review, 2026-11-10).

`ui.components.chip` and `notice` take a plain string, which the page catalogue can
only translate by exact match. A sentence with a number in it never matches, so
these twins carry both wordings through `LocalText` and keep the shared look
(same padding, border, palette tokens and sizes) of the originals.
"""
from __future__ import annotations

import re
from typing import Optional

import flet as ft

from core.theme import RADII, active
from ui.components import LocalText, colour_for


def local_chip(ko: str, en: str, token: str = "muted", *, tooltip: str = "") -> ft.Container:
    """`chip` with an authored Korean and English label."""
    pal = active()
    return ft.Container(
        content=LocalText(ko, en, size=11, color=colour_for(token), weight=ft.FontWeight.W_500),
        padding=ft.Padding(8, 3, 8, 3),
        bgcolor=pal.surface_2,
        border=ft.Border.all(1, colour_for(token)),
        border_radius=RADII["pill"],
        tooltip=tooltip or None,
    )


def local_notice(ko: str, en: str, token: str = "accent", *, icon: str = ft.Icons.INFO_OUTLINE,
                 action: Optional[ft.Control] = None, tooltip: str = "") -> ft.Container:
    """`notice` with an authored Korean and English sentence; `tooltip` keeps a longer
    provider/disclosure text one hover away when the visible sentence is shortened."""
    pal = active()
    row = [ft.Icon(icon, size=18, color=colour_for(token)),
           LocalText(ko, en, size=13, color=pal.text, expand=True, selectable=True)]
    if action is not None:
        row.append(action)
    return ft.Container(
        content=ft.Row(row, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=14,
        bgcolor=pal.surface_2,
        border=ft.Border.all(1, colour_for(token)),
        border_radius=RADII["md"],
        tooltip=tooltip or None,
    )


def local_stat(label: str, ko_value: str, en_value: str, *, token: str = "text",
               tooltip: str = "") -> ft.Container:
    """`stat` whose value carries words (e.g. 'normal', 'inf') authored in both languages."""
    pal = active()
    return ft.Container(
        ft.Column([
            ft.Text(label, size=10, color=pal.muted),
            LocalText(ko_value, en_value, size=16, weight=ft.FontWeight.W_600,
                      color=getattr(pal, token, pal.text)),
        ], spacing=2),
        padding=ft.Padding(14, 10, 14, 10), bgcolor=pal.surface_2,
        border=ft.Border.all(1, pal.border), border_radius=RADII["md"],
        tooltip=tooltip or None,
    )


_CHILD_FIELDS = ("controls", "content", "title", "subtitle", "actions", "leading", "trailing", "label")


def _texts(root):
    seen: set[int] = set()
    stack = [root]
    while stack:
        c = stack.pop()
        if not isinstance(c, ft.Control) or id(c) in seen:
            continue
        seen.add(id(c))
        if isinstance(c, ft.Text):
            yield c
        for name in _CHILD_FIELDS:
            v = getattr(c, name, None)
            if isinstance(v, (list, tuple)):
                stack.extend(v)
            elif isinstance(v, ft.Control):
                stack.append(v)


def make_bilingual(text: ft.Text, ko: str, en: Optional[str] = None) -> ft.Text:
    """Turn an existing Text into a LocalText-like one in place: `ko` in Korean, its own
    (or the given) English otherwise, and never rewritten again by the catalogue."""
    en = text.value if en is None else en
    data = dict(text.data) if isinstance(text.data, dict) else {}
    data["qg_literal_value"] = True
    text.data = data
    text.qg_ko, text.qg_en = ko, en

    def render_locale(ctx, t=text):
        t.ctx = ctx
        t.value = t.qg_ko if getattr(ctx, "language", "en") == "ko" else t.qg_en
    text.render_locale = render_locale
    return text


def localize_tree(root, patterns) -> None:
    """Give each Text under `root` whose whole English value matches one of `patterns` its Korean
    twin. `patterns` is a sequence of (regex, ko) where `ko` is a format string over the match
    groups ({1}, {2}, ...) or a callable taking the match. For pages whose sentences carry numbers
    and which must not be rewritten line by line (ui/trading_page.py is add-only, see
    tests/macro_m5_integration.py)."""
    compiled = [(re.compile(rx), ko) for rx, ko in patterns]
    for t in _texts(root):
        if isinstance(t, LocalText) or not isinstance(t.value, str) or callable(getattr(t, "render_locale", None)):
            continue
        for rx, ko in compiled:
            m = rx.fullmatch(t.value)
            if m:
                make_bilingual(t, ko(m) if callable(ko) else ko.format(m[0], *(g or "" for g in m.groups())))
                break


def provenance_chips(histories) -> ft.Row:
    """One small chip per loaded series: which provider actually answered.

    Secondary by design (the source selector is hidden; the app chooses the
    provider), but always present, and the provider's own note is the tooltip.
    """
    names = {"SYNTHETIC": ("합성 데이터", "synthetic"), "YFINANCE": ("Yahoo", "Yahoo"),
             "FMP": ("FMP", "FMP"), "KIS": ("KIS", "KIS"), "CRYPTO": ("가상자산 거래소", "crypto venue")}
    chips = []
    for h in histories:
        ko, en = names.get(str(h.source).upper(), (str(h.source), str(h.source)))
        cached = "cached" in (h.note or "")
        chips.append(local_chip(f"{h.symbol} · {ko}" + (" · 캐시" if cached else ""),
                                f"{h.symbol}: {h.source}" + (" · cached" if cached else ""),
                                "muted" if h.source == "SYNTHETIC" else "success",
                                tooltip=h.note or ""))
    return ft.Row([LocalText("데이터 출처", "Data from", size=11, color=active().muted)] + chips,
                  spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)
