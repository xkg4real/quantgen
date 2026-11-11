"""Indicator picker of the stock detail view (owner request 2026-11-11, UI-D8).

Owner, with a TradingView screenshot: "트레이딩뷰 상세차트 목록 ui인데, 이런식으로 큼직큼직하게 하고 지표같은건 화살표로
접고펴고 할수잇게 해야하고, 우리는 이 ui를 기본으로 주린이들이 읽기 쉽게 하는 가이드를 화면에 잘 녹여야해".
Every study of core.education.indicators.STUDIES in its category; categories fold with the bundled chevrons;
56px rows that switch on and off with one click, a one-line description, where the study appears (on the price,
on the volume or in its own panel), its value at the latest candle, an ⓘ that unfolds the beginner guide
(core.education.study_guide: what it is, how to read it, a caution and the reading now), and the reason when a
study cannot be drawn on this chart. Display text: owner_ui_language/stock.py and study_guide.
"""
from __future__ import annotations

import math

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy,
                             QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from .stock_detail_side import FoldHeader
from .stock_detail_style import ClampLabel, ElidedLabel, icon, label, numbers, polite, set_prop, text

STARTER = ("sma", "volume_ma", "rsi")


class NameLine(QWidget):
    """Line 1 of a picker row: name, place and the value with its one-word state ('89,902 · 선 아래'). The name
    keeps its whole width first; the value gives back its state word (down to the bare number) before the name
    is elided."""

    def __init__(self):
        super().__init__()
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(6)
        self.name = ElidedLabel("pickName")
        self.name.setMinimumWidth(40)
        self.row.addWidget(self.name, 1)
        self.place = label("place")
        self.row.addWidget(self.place, 0, Qt.AlignmentFlag.AlignVCenter)
        self.value = numbers(ElidedLabel("pickValue", align=Qt.AlignmentFlag.AlignRight))
        self.value.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)   # width set by fit()
        self.row.addWidget(self.value, 0, Qt.AlignmentFlag.AlignVCenter)

    def fit(self):
        choices = self.value._choices or ("",)
        metrics = self.value.fontMetrics()
        full, bare = (metrics.horizontalAdvance(choices[0]) + 2, metrics.horizontalAdvance(choices[-1]) + 2)
        spacing = self.row.spacing()
        room = self.width() - spacing - (self.place.sizeHint().width() + spacing if not self.place.isHidden() else 0)
        name = self.name.fontMetrics().horizontalAdvance(self.name.text()) + 2
        width = full if name + full <= room else max(bare, room - name)
        if self.value.width() != width or self.value.minimumWidth() != width:
            self.value.setFixedWidth(width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


def _lang(ctx):
    return "ko" if getattr(ctx, "language", "ko") == "ko" else "en"


class Switch(QAbstractButton):
    """A 38x22 on/off pill; Space toggles it."""

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(38, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.colors = ("#194C40", "#C9CCC2", "#FFFFFF")

    def sizeHint(self):
        return QSize(38, 22)

    def paintEvent(self, event):
        on, off, knob = (QColor(c) for c in self.colors)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        track = on if self.isChecked() else off
        if not self.isEnabled():
            track.setAlphaF(0.4)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 2, 38, 18), 9, 9)
        p.setBrush(knob)
        x = 20 if self.isChecked() else 3
        p.drawEllipse(QRectF(x, 4, 14, 14))
        if self.hasFocus():
            pen = p.pen()
            p.setPen(on)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 1.5, 37, 19), 9.5, 9.5)
        p.end()


class ColorBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(4)
        self.color = QColor("#896000")

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.color)
        p.drawRoundedRect(QRectF(0, 8, 4, self.height() - 16), 2, 2)
        p.end()


class PickerRow(QFrame):
    """One study: colour, name, description or reason, placement, value now, ⓘ guide and the switch."""
    toggled = pyqtSignal(str, bool)

    def __init__(self, spec):
        super().__init__()
        self.spec = spec
        self.key = spec.key
        self.reason = ""
        self.setProperty("sd", "pickRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        # Spec 5.1: line 1 is the name, where it appears (가격 위 / 거래량 위 / 아래 패널) and the value now with a
        # one-word state; line 2, the full width beside ⓘ and the switch, is the description or the reason
        # (up to two lines, the rest in the tooltip).
        line = QWidget()
        line.setMinimumHeight(56)
        self.line = line
        row = QHBoxLayout(line)
        row.setContentsMargins(4, 7, 6, 7)
        row.setSpacing(10)
        self.bar = ColorBar()
        row.addWidget(self.bar)
        names = QVBoxLayout()
        names.setContentsMargins(0, 0, 0, 0)
        names.setSpacing(2)
        self.first = NameLine()
        self.name, self.place, self.value = self.first.name, self.first.place, self.first.value
        names.addWidget(self.first)
        self.desc = ClampLabel("pickDesc", lines=2)
        self.desc.setProperty("keepTip", True)
        names.addWidget(self.desc)
        row.addLayout(names, 1)
        self.info = QPushButton()
        self.info.setProperty("sd", "mini")
        self.info.setCheckable(True)
        self.info.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.info.toggled.connect(self._guide_toggled)
        self.guide_changed = None
        row.addWidget(self.info)
        self.switch = Switch()
        self.switch.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.switch.clicked.connect(lambda checked: self.toggled.emit(self.key, checked))
        row.addWidget(self.switch)
        outer.addWidget(line)
        self.guide = QFrame()
        self.guide.setProperty("sd", "guide")
        guide = QVBoxLayout(self.guide)
        guide.setContentsMargins(14, 10, 14, 12)
        guide.setSpacing(4)
        self.guide_parts = []
        for _ in range(5):
            head, body = label("guideHead"), numbers(label("guideText", wrap=True))
            guide.addWidget(head)
            guide.addWidget(body)
            self.guide_parts.append((head, body))
        self.guide.hide()
        wrap = QHBoxLayout()
        wrap.setContentsMargins(18, 0, 6, 8)
        wrap.addWidget(self.guide)
        outer.addLayout(wrap)

    def _guide_toggled(self, on):
        self.guide.setVisible(on)
        if on and callable(self.guide_changed):
            self.guide_changed()

    def open_guide(self, on=True):
        self.info.setChecked(on)

    def set_checked(self, on):
        self.switch.blockSignals(True)
        self.switch.setChecked(bool(on))
        self.switch.blockSignals(False)
        self.switch.update()

    def is_checked(self):
        return self.switch.isChecked()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.switch.isEnabled() and \
                event.position().y() <= self.line.height():
            self.switch.click()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.switch.isEnabled():
            self.switch.click()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            set_prop(self, "focusRing", True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        set_prop(self, "focusRing", False)

    def show_state(self, *, language, dark, color, value, reason, guide, reading, place, state=""):
        from core.education.study_guide import availability_text
        self.reason = reason
        self.bar.set_color(color)
        self.name.setText(self.spec.name(language))
        self.place.setText(place)
        what = polite(guide.what, language)
        why = polite(availability_text(reason, language), language) if reason else ""
        first = what.split(". ")[0]
        self.desc.setText(why or (first if first.endswith(".") else first + "."))
        self.desc.setToolTip(why or what)
        set_prop(self.desc, "reason", "true" if reason else "false")
        set_prop(self.name, "dim", "true" if reason else "false")
        shown = f"{value} · {state}" if value and value != "—" and state else value
        self.value.set_choices([shown, value] if shown != value else [value])
        self.value.setVisible(bool(shown))
        self.first.fit()
        self.switch.setEnabled(not reason or self.switch.isChecked())
        self.switch.colors = (color, "#C9CCC2" if not dark else "#4A5C52", "#FFFFFF")
        self.switch.update()
        self.info.setIcon(icon("info", "#A7B8AC" if dark else "#646E68", 16))
        name = self.spec.name(language)
        self.info.setToolTip(text(language, "picker_info", name=name))
        self.info.setAccessibleName(text(language, "picker_info", name=name))
        switched = text(language, "picker_state_on" if self.is_checked() else "picker_state_off")
        self.setAccessibleName(text(language, "picker_row_name", name=name, state=switched, place=place,
                                    value=shown or "—"))
        self.switch.setAccessibleName(name)
        heads = ("picker_guide_what", "picker_guide_how", "picker_guide_caution", "picker_guide_now",
                 "picker_guide_params")
        bodies = tuple(polite(part, language) for part in (guide.what, guide.how, guide.caution, reading,
                                                           guide.params))
        for (head, body), key, content in zip(self.guide_parts, heads, bodies):
            head.setText(text(language, key))
            body.setText(content)
            head.setVisible(bool(content))
            body.setVisible(bool(content))


class PickerGroup(QWidget):
    toggled = pyqtSignal(str, bool)

    def __init__(self, category, specs):
        super().__init__()
        self.category = category
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.head = FoldHeader()
        self.head.toggled.connect(self._fold)
        layout.addWidget(self.head)
        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(4, 0, 0, 6)
        body.setSpacing(0)
        self.rows = {}
        for spec in specs:
            row = PickerRow(spec)
            row.toggled.connect(self.toggled)
            body.addWidget(row)
            self.rows[spec.key] = row
        layout.addWidget(self.body)

    def _fold(self, is_open):
        self.body.setVisible(is_open)

    def set_open(self, is_open):
        self.head.set_open(is_open)
        self.body.setVisible(is_open)

    @property
    def is_open(self):
        return self.head.is_open


class IndicatorPicker(QWidget):
    """Grouped, folding list of every chart study; emits the new selection."""
    changed = pyqtSignal(tuple)

    def __init__(self, *, locale=None):
        super().__init__()
        from core.education.indicators import studies_by_category
        self.ctx, self.dark = locale or LocaleContext("ko_KR"), False
        self.selected = ()
        self.context = None       # (bars, asset, interval, supply, values) of the open chart
        self.panel_limit = None
        self.price_format = None  # the open instrument's price precision (the view sets it)
        self._opened_once = set()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        head = QHBoxLayout()
        head.setContentsMargins(6, 2, 4, 0)
        self.title = label("cardTitle")
        head.addWidget(self.title)
        head.addStretch(1)
        self.count = label("small")
        head.addWidget(self.count)
        self.off_button = QPushButton()
        self.off_button.setProperty("sd", "link")
        self.off_button.setProperty("qg_literal", True)
        self.off_button.clicked.connect(lambda: self._emit(()))
        head.addWidget(self.off_button)
        layout.addLayout(head)
        self.search = QLineEdit()
        self.search.setObjectName("sdPickerSearch")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)
        starter = QHBoxLayout()
        starter.setContentsMargins(6, 0, 0, 2)
        starter.setSpacing(8)
        self.starter_label = label("small")
        starter.addWidget(self.starter_label)
        self.starter_button = QPushButton()
        self.starter_button.setProperty("sd", "text")
        self.starter_button.setProperty("qg_literal", True)
        self.starter_button.clicked.connect(lambda: self._emit(tuple(dict.fromkeys((*self.selected, *STARTER)))))
        starter.addWidget(self.starter_button)
        starter.addStretch(1)
        layout.addLayout(starter)
        self.no_match = label("small", wrap=True)
        self.no_match.setContentsMargins(6, 6, 6, 6)
        self.no_match.hide()
        layout.addWidget(self.no_match)
        self.groups = {}
        for category, specs in studies_by_category():
            group = PickerGroup(category, specs)
            group.toggled.connect(self._row_toggled)
            group.set_open(False)
            for row in group.rows.values():
                row.guide_changed = self.render
            layout.addWidget(group)
            self.groups[category] = group
        self.limit_note = label("small", wrap=True)
        self.limit_note.setContentsMargins(6, 4, 6, 0)
        self.limit_note.hide()
        layout.addWidget(self.limit_note)
        self.disclaimer = label("small", wrap=True)
        self.disclaimer.setContentsMargins(6, 8, 6, 0)
        layout.addWidget(self.disclaimer)
        layout.addStretch(1)
        self.set_locale(self.ctx)

    def rows(self):
        return {key: row for group in self.groups.values() for key, row in group.rows.items()}

    def _row_toggled(self, key, on):
        chosen = [k for k in self.selected if k != key]
        if on:
            chosen.append(key)
        self._emit(tuple(chosen))

    def _emit(self, keys):
        self.set_selected(keys)
        self.changed.emit(self.selected)

    def set_selected(self, keys):
        from core.education.indicators import study
        out = []
        for key in keys:
            try:
                name = study(key).key
            except ValueError:
                continue
            if name not in out:
                out.append(name)
        self.selected = tuple(out)
        for group in self.groups.values():
            if not group.is_open and any(k in self.selected for k in group.rows) and group.category not in self._opened_once:
                group.set_open(True)
                self._opened_once.add(group.category)
        self.render()

    def set_context(self, bars, *, asset, interval, supply=None, panel_limit=None):
        self.context = (bars, asset, interval, supply)
        self.panel_limit = panel_limit
        if self.isVisible():
            self.render()

    def set_locale(self, ctx):
        self.ctx = ctx
        lang = _lang(ctx)
        self.title.setText(text(lang, "picker_title"))
        self.off_button.setText(text(lang, "picker_off_all"))
        self.search.setPlaceholderText(text(lang, "picker_search"))
        self.search.setAccessibleName(text(lang, "picker_search"))
        self.starter_label.setText(text(lang, "picker_starter_label"))
        self.starter_button.setText(text(lang, "picker_starter"))
        self.starter_button.setToolTip(text(lang, "picker_starter_tip"))
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        for group in self.groups.values():
            group.head.set_theme(dark)
        self.render()

    def showEvent(self, event):
        super().showEvent(event)
        self.render()

    def _filter(self, query):
        from core.education.study_guide import guide
        query = str(query or "").strip().lower()
        lang = _lang(self.ctx)
        any_shown = False
        for group in self.groups.values():
            shown = 0
            for key, row in group.rows.items():
                spec = row.spec
                words = " ".join((spec.key, spec.ko, spec.en, spec.short, *spec.aliases, guide(key, "ko").what[:40])).lower()
                match = not query or query in words or query.replace(" ", "") in words.replace(" ", "")
                row.setVisible(match)
                shown += match
            group.setVisible(shown > 0)
            if query and shown:
                group.set_open(True)
            any_shown = any_shown or shown > 0
        self.no_match.setText(text(lang, "picker_no_match", text=self.search.text().strip()))
        self.no_match.setVisible(not any_shown)

    def render(self):
        from core.education import indicators as engine
        from core.education.study_guide import category_name, disclaimer, format_value, guide, study_reading
        from core.market.detail_model import study_state
        from core.market.presentation import study_colors
        lang = _lang(self.ctx)
        self.count.setText(text(lang, "picker_on", count=len(self.selected)))
        self.off_button.setVisible(bool(self.selected))
        self.disclaimer.setText(polite(disclaimer(lang), lang))
        bars, asset, interval, supply = self.context if self.context else (None, "domestic_stock", "1d", None)
        has_volume = bool(bars is not None and any(math.isfinite(v) for v in bars.volume))
        visible = self.isVisible()
        for category, group in self.groups.items():
            group.head.title.setText(category_name(category, lang))
            on = sum(1 for k in group.rows if k in self.selected)
            group.head.count.setText(text(lang, "picker_group_count", on=on, total=len(group.rows)))
            for key, row in group.rows.items():
                spec = row.spec
                reason = engine.availability(key, asset=asset, interval=interval, supply=supply,
                                             has_volume=has_volume if bars is not None else True)
                colors = study_colors(key, self.dark)
                color = colors[spec.lines[0].id]
                place = text(lang, "place_price" if spec.panel == "price" else "place_volume"
                             if spec.panel == "volume" else "place_panel")
                value, reading, state = "", "", ""
                if visible and bars is not None and len(bars) and not reason:
                    try:
                        values = engine.compute_study(key, bars, supply=supply)
                        line = spec.lines[0]
                        raw = float(values[line.id][-1])
                        if not math.isfinite(raw):
                            value = "—"
                        elif line.kind == "price" and self.price_format is not None:
                            value = self.price_format(raw)
                        else:
                            value = format_value(line.kind, raw, lang)
                        code = study_state(key, values, bars)
                        state = text(lang, f"word_{code}") if code else ""
                        if row.guide.isVisible() or row.info.isChecked():
                            reading = study_reading(key, bars, -1, language=lang, values=values, supply=supply)
                    except Exception:
                        value = ""
                row.set_checked(key in self.selected)
                row.show_state(language=lang, dark=self.dark, color=color, value=value, reason=reason,
                               guide=guide(key, lang), reading=reading, place=place, state=state)
        panels = sum(1 for k in self.selected if not engine.study(k).overlay)
        if self.panel_limit is not None and panels > self.panel_limit:
            self.limit_note.setText(text(lang, "picker_panel_limit", count=self.panel_limit))
            self.limit_note.show()
        else:
            self.limit_note.hide()
        if self.search.text().strip():
            self._filter(self.search.text())


__all__ = ["IndicatorPicker", "PickerGroup", "PickerRow", "Switch", "STARTER"]
