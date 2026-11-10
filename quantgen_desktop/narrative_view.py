"""Analysis narratives as short headed bullet lists, in the window's language (owner UI review, 2026-11-10).

The owner found every "Analysis" panel to be one long paragraph (issue 11, "정리"). The Flet app fixed
it with `ui.narrative_sections.organise`; the native app shares that Flet-free logic here.

Presentation only: the narrative text is exactly what the caller passes (the English source and, where a
reviewed Korean twin exists, the Korean text). This view cuts it into sentences under short headings in
reading order; it never writes a number or a statement, never reorders sentences, and the caller keeps
the full English text for exports.

Both language variants are built once and the one matching the window language is shown, so a language
switch needs no rerun and no rebuild. `LanguageController.apply` calls `_reserve_text_space` on every
widget after a language change; that hook keeps the visible variant in step.
"""
from __future__ import annotations

from typing import Mapping, Sequence, Union

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

Sections = Sequence[tuple[str, Sequence[str]]]
Variant = Union[str, Sections]


def sections_for(text: str, language: str, *, terms: bool = True) -> list[tuple[str, list[str]]]:
    """Headed sentence bullets for one narrative (`ui.narrative_sections.organise`).

    In Korean, raw identifiers the native narratives leave in (`ma_cross`, `SYNTHETIC`, ...) are shown
    under their Korean display names first (`ko_terms`: whole tokens, particles agree). `terms=False`
    keeps a text that has no reviewed Korean twin exactly as written (only the headings follow the UI)."""
    from ui.narrative_sections import ko_terms, organise
    if language == "ko" and terms:
        text = ko_terms(text) or text
    return organise(text, language)


def _literal_label(text: str, role: str = ""):
    """A label whose text is already in its language: no catalogue lookup may rewrite it."""
    from .app import label
    widget = label(text, role)
    widget.localized_text = {"en": text, "ko": text}
    widget.retranslate()
    return widget


class NarrativeView(QWidget):
    """Headed bullets for each language variant; shows the one matching the window language.

    `variants` maps a language ('en', 'ko') to either the narrative text (organised automatically) or
    ready sections `[(heading, [line, ...]), ...]`. A language in LANGUAGES without its own variant shows
    the 'en' text as written, under that language's headings. `source_text` is the English text (or the
    first variant), for callers that export or test the full narrative."""

    LANGUAGES = ("en", "ko")

    def __init__(self, variants: Mapping[str, Variant], parent=None):
        super().__init__(parent)
        self.setObjectName("narrativeView")
        self.setProperty("reading_help_keep_visible", True)
        self.variants = {k: v for k, v in variants.items() if v}
        first = next(iter(self.variants.values()), "")
        english = self.variants.get("en", first)
        self.source_text = english if isinstance(english, str) else "\n".join(
            line for _, lines in english for line in lines)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._pages = {}
        own = dict(self.variants)
        for language in self.LANGUAGES:
            if language not in own and isinstance(english, str) and english:
                own[language] = None
        for language, value in own.items():
            if value is None:
                sections = sections_for(english, language, terms=False)
            else:
                sections = sections_for(value, language) if isinstance(value, str) else value
            page = QWidget()
            column = QVBoxLayout(page)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(6)
            for index, (heading, lines) in enumerate(sections):
                if heading:
                    title = _literal_label(heading, "cardTitle")
                    title.setProperty("narrative_heading", True)
                    if index:
                        column.addSpacing(8)
                    column.addWidget(title)
                for line in lines:
                    row = QHBoxLayout()
                    row.setSpacing(8)
                    row.setContentsMargins(0, 0, 0, 0)
                    if len(lines) > 1:
                        dot = _literal_label("•", "muted")
                        dot.setAlignment(Qt.AlignmentFlag.AlignTop)
                        row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
                    text = _literal_label(line)
                    text.setProperty("narrative_line", True)
                    row.addWidget(text, 1)
                    column.addLayout(row)
            layout.addWidget(page)
            page.hide()
            self._pages[language] = page
        self.sync_language()

    def language(self) -> str:
        window = self.window()
        language = getattr(window, "ui_language", None) if window is not None else None
        if language in self._pages:
            return language
        return "en" if "en" in self._pages else next(iter(self._pages), "en")

    def sync_language(self):
        current = self.language()
        for language, page in self._pages.items():
            page.setVisible(language == current)

    def lines(self, language: str | None = None) -> list[str]:
        """The shown bullets (tests and accessibility)."""
        from .localization import UiLabel
        page = self._pages.get(language or self.language())
        if page is None:
            return []
        return [w.text() for w in page.findChildren(UiLabel) if w.property("narrative_line")]

    def headings(self, language: str | None = None) -> list[str]:
        from .localization import UiLabel
        page = self._pages.get(language or self.language())
        if page is None:
            return []
        return [w.text() for w in page.findChildren(UiLabel) if w.property("narrative_heading")]

    # LanguageController.apply calls this hook on every widget after a language change.
    def _reserve_text_space(self):
        self.sync_language()

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.Type.ParentChange, QEvent.Type.Show):
            self.sync_language()
        return result


class FullTextFold(QWidget):
    """The complete narrative paragraph, folded under the bullets (closed by default).

    `widget` is the narrative's UiLabel: its source text is the export text and its per-language
    text is unchanged, so readers who want the paragraph (and existing callers) still have it."""

    def __init__(self, widget, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QToolButton
        self.setObjectName("narrativeFullText")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.toggle = QToolButton()
        self.toggle.setText("Full narrative paragraph")
        self.toggle.setAccessibleName("Full narrative paragraph")
        self.toggle.setCheckable(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.toggled.connect(self._toggled)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.body = widget
        layout.addWidget(widget)
        self._toggled(False)

    def _toggled(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)
