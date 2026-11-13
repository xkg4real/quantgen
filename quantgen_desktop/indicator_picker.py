"""Indicator picker of the stock detail view (owner request 2026-11-11, UI-D8).

Owner, with a TradingView screenshot: "트레이딩뷰 상세차트 목록 ui인데, 이런식으로 큼직큼직하게 하고 지표같은건 화살표로
접고펴고 할수잇게 해야하고, 우리는 이 ui를 기본으로 주린이들이 읽기 쉽게 하는 가이드를 화면에 잘 녹여야해".
Every study of core.education.indicators.STUDIES in its category; categories fold with the bundled chevrons;
56px rows that switch on and off with one click, a one-line description, where the study appears (on the price,
on the volume or in its own panel), its value at the latest candle, an ⓘ that unfolds the beginner guide and the
reason when a study cannot be drawn on this chart.

The guide is a card, not a stack of labelled sections (owner 2026-11-11, R-D9-3: "무엇인가요, 어떻게 보나요, 주의, 아 이게
뭔가 너무 이상한데 좀 더 센스있게 못하나? 지금 글밥이 너무 많아보이잖아. 여백도 똑바로 못쓰고잇고"): the reading now in one
short sentence with a state pill, a small gauge where it helps (the 0-100 zones, the close in its band, above or
below its line), one muted line of what it is, two or three cue chips and one short caution; the long texts sit
behind '자세히 ›'. `GuideCard` is also the right column's reading row. Display text: owner_ui_language/stock.py and
core.education.study_guide (SHORT, GAUGES, short_reading).
"""
from __future__ import annotations

from html import escape
import math

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy,
                             QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from .stock_detail_side import FoldHeader
from .stock_detail_style import ClampLabel, ElidedLabel, icon, label, numbers, polite, set_prop, text

STARTER = ("sma", "volume_ma", "rsi")
# Pill tones by one-word state (core.market.detail_model.study_state): red rise / blue fall (Korean convention).
UP_STATES = ("high", "above", "fast_above", "signal_above", "cloud_above", "dots_below", "band_above", "volume_more")
DOWN_STATES = ("low", "below", "fast_below", "signal_below", "cloud_below", "dots_above", "band_below", "volume_less")


def _lang(ctx):
    return "ko" if getattr(ctx, "language", "ko") == "ko" else "en"


def state_tone(code):
    return "up" if code in UP_STATES else "down" if code in DOWN_STATES else "flat" if code else ""


def state_word(key, code, lang):
    """The pill's word for a study_state code. The middle zone of a 0-100 style study is named by its edges
    ('30~70 사이'), not 'normal': beside a reading such as 'falls were much larger' a '보통' pill contradicts it."""
    if not code:
        return ""
    if code == "middle":
        from core.market.detail_model import level_marks
        marks = level_marks(key)
        if marks:
            low, high = (f"{mark:g}".replace("-", "−") for mark in marks)
            return text(lang, "word_between", low=low, high=high)
    return text(lang, f"word_{code}")


def paragraph(value, spacing=150):
    """Rich text of plain `value` with a comfortable line height (QLabel has no line-height property)."""
    body = escape(str(value or "")).replace("\n", "<br>")
    return f'<div style="line-height:{spacing}%">{body}</div>'


class NameLine(QWidget):
    """Line 1 of a picker row: name, place and the value with its one-word state ('89,902 · 선 아래'). The name
    keeps its whole width first: the value gives back its state word (down to the bare number), then the place chip
    leaves the line (the row names the place at the start of line 2), and only then is the name elided."""

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
        self.place_wanted = True
        self.place_moved = None     # called when the place chip or the value leaves or returns to the line
        self.value_moved = False    # the value went to line 2 (a long name in a narrow column)

    def fit(self):
        width = self.width()
        if width <= 0:
            return
        choices = self.value._choices or ("",)
        metrics = self.value.fontMetrics()
        full, bare = (metrics.horizontalAdvance(choices[0]) + 2, metrics.horizontalAdvance(choices[-1]) + 2)
        if not choices[0]:
            full = bare = 0
        spacing = self.row.spacing()
        name = self.name.fontMetrics().horizontalAdvance(self.name.text()) + 8   # + the label's own slack
        chip = self.place.sizeHint().width() + spacing
        value_on = bool(full) and name + spacing + bare <= width
        room = width - (spacing if value_on else 0)
        place = self.place_wanted and name + (bare if value_on else 0) + chip <= room
        if place:
            room -= chip
        value = (full if name + full <= room else max(bare, room - name)) if value_on else 0
        if self.value.width() != value or self.value.minimumWidth() != value:
            self.value.setFixedWidth(value)
        moved = (self.place.isHidden() == place) or (self.value.isHidden() == value_on and bool(full))
        self.place.setVisible(place)
        self.value.setVisible(value_on)
        self.value_moved = bool(full) and not value_on
        if moved and callable(self.place_moved):
            self.place_moved(not place)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


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


class Gauge(QWidget):
    """The guide card's small picture (core.education.study_guide.GAUGES): a track with the conventional zones
    tinted and their numbers under it ('scale'; 'level' for a value with no direction, such as ADX, in neutral
    tints only: a rise/fall colour there would read as a direction it does not have), a band in the middle third
    with the close as a dot ('band'), a centre line with the close left or right of it ('offset', 'zero'), or
    volume against its average ('ratio')."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(34)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.kind, self.position, self.marks, self.labels = None, None, (), ("", "")
        self.colors = {"track": "#ECEDE6", "up": "#C8343D", "down": "#2F6DB5", "up_tint": "#FDF0F0",
                       "down_tint": "#EEF4FB", "accent": "#194C40", "muted": "#646E68", "band": "#E5EEE8",
                       "bg": "#FFFFFF"}

    def set_value(self, kind, position, marks=(), labels=("", ""), colors=None):
        self.kind, self.position, self.marks, self.labels = kind, position, tuple(marks or ()), labels
        if colors:
            self.colors.update(colors)
        self.update()

    def paintEvent(self, event):
        if self.kind is None or self.position is None or not math.isfinite(self.position):
            return
        c = {k: QColor(v) for k, v in self.colors.items()}
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pad = 8
        left, right = pad, self.width() - pad
        span = right - left
        y, h = 9, 8
        x_of = lambda f: left + max(0.0, min(1.0, f)) * span
        font = QFont(self.font())
        font.setPixelSize(11)
        p.setFont(font)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c["track"])
        p.drawRoundedRect(QRectF(left, y, span, h), h / 2, h / 2)
        under = []    # (x, text) labels under the track
        level = self.kind == "level"
        if self.kind in ("scale", "level") and len(self.marks) == 2:
            (low, low_text), (high, high_text) = self.marks
            path = QPainterPath()
            path.addRoundedRect(QRectF(left, y, span, h), h / 2, h / 2)
            p.save()
            p.setClipPath(path)
            low_zone, high_zone = ((QColor(c["muted"]), QColor(c["accent"])) if level else
                                   (QColor(c["down"]), QColor(c["up"])))
            low_zone.setAlphaF(0.16 if level else 0.28)
            high_zone.setAlphaF(0.24)
            p.setBrush(low_zone)
            p.drawRect(QRectF(left, y, x_of(low) - left, h))
            p.setBrush(high_zone)
            p.drawRect(QRectF(x_of(high), y, right - x_of(high), h))
            p.restore()
            under = [(x_of(low), low_text), (x_of(high), high_text)]
        elif self.kind == "band":
            band = QColor(c["accent"])
            band.setAlphaF(0.22)
            p.setBrush(band)
            p.drawRoundedRect(QRectF(x_of(0.25), y - 1, x_of(0.75) - x_of(0.25), h + 2), 3, 3)
            under = [(x_of(0.25), self.labels[0]), (x_of(0.75), self.labels[1])]
        elif self.kind in ("offset", "zero", "ratio"):
            centre = x_of(self.marks[0][0]) if self.marks else x_of(0.5)
            p.setPen(QPen(c["muted"], 1.5))
            p.drawLine(QPointF(centre, y - 3), QPointF(centre, y + h + 3))
            p.setPen(Qt.PenStyle.NoPen)
            under = [(centre, self.labels[0])]
        # The dot: the value now (clamped to the track; past an end it sits on the end).
        x = x_of(self.position)
        tone = c["accent"]
        if self.kind == "scale" and len(self.marks) == 2:
            tone = c["down"] if self.position <= self.marks[0][0] else c["up"] if self.position >= self.marks[1][0] \
                else c["accent"]
        elif level and len(self.marks) == 2:
            tone = c["muted"] if self.position <= self.marks[0][0] else c["accent"]
        elif self.kind == "band":
            tone = c["up"] if self.position > 0.75 else c["down"] if self.position < 0.25 else c["accent"]
        elif self.kind in ("offset", "zero"):
            tone = c["up"] if self.position > 0.5 else c["down"] if self.position < 0.5 else c["accent"]
        p.setBrush(c["bg"])
        p.setPen(QPen(tone, 2.5))
        p.drawEllipse(QPointF(x, y + h / 2), 6.5, 6.5)
        p.setPen(c["muted"])
        metrics = p.fontMetrics()
        taken = None     # the right edge of the last label: close marks (ADX 20 and 25) never overprint
        for lx, value in sorted(under):
            if not value:
                continue
            w = metrics.horizontalAdvance(value)
            tx = min(max(lx - w / 2, 0), self.width() - w)
            if taken is not None and tx < taken + 4:
                tx = taken + 4
            p.drawText(QPointF(tx, self.height() - 3), value)
            taken = tx + w
        p.end()


class ChipRow(QWidget):
    """Cue chips that wrap onto a second line when the card is narrow."""

    def __init__(self):
        super().__init__()
        self.chips = []
        self.gap = 6
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_cues(self, cues):
        cues = tuple(cues)
        if tuple(chip.text() for chip in self.chips) == cues:
            return
        while len(self.chips) < len(cues):
            chip = label("cue")
            chip.setParent(self)
            self.chips.append(chip)
        for chip, cue in zip(self.chips, (*cues, *([""] * len(self.chips)))):
            chip.setText(cue)
            chip.setVisible(bool(cue))
        self.chips = [chip for chip in self.chips if chip.text()] + [chip for chip in self.chips if not chip.text()]
        self._place(self.width())
        self.updateGeometry()

    def _place(self, width):
        x = y = 0
        line = 0
        for chip in [chip for chip in self.chips if chip.text()]:
            size = chip.sizeHint()
            if x and x + size.width() > width:
                x, y = 0, y + line + self.gap
                line = 0
            chip.setGeometry(x, y, min(size.width(), max(40, width)), size.height())
            x += size.width() + self.gap
            line = max(line, size.height())
        return y + line

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._place(width) if any(chip.text() for chip in self.chips) else 0

    def sizeHint(self):
        return QSize(self.width() or 260, self.heightForWidth(self.width() or 260))

    def minimumSizeHint(self):
        return QSize(60, self.heightForWidth(self.width() or 260))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        height = self._place(self.width())
        if height != self.height():
            self.setMinimumHeight(height)
            self.setMaximumHeight(height)


class GuideCard(QFrame):
    """One study's guide as a card. compact=True (the right column's reading rows) keeps the reading, the pill,
    the gauge and '자세히' only."""
    more_toggled = pyqtSignal(bool)

    def __init__(self, *, compact=False):
        super().__init__()
        self.compact = compact
        self.setProperty("sd", "guideCard" if not compact else "guideCompact")
        layout = QVBoxLayout(self)
        if compact:
            layout.setContentsMargins(0, 2, 0, 2)
            layout.setSpacing(8)
        else:
            layout.setContentsMargins(16, 14, 16, 16)
            layout.setSpacing(10)
        # The state pill sits above the reading, so the reading keeps the card's whole width; in a reading row
        # (compact) it ends the reading's line.
        self.pill = label("pill")
        self.headline = numbers(label("guideReading" if not compact else "guideReadingSmall", wrap=True))
        if compact:
            top = QHBoxLayout()
            top.setContentsMargins(0, 0, 0, 0)
            top.setSpacing(8)
            top.addWidget(self.headline, 1)
            top.addWidget(self.pill, 0, Qt.AlignmentFlag.AlignTop)
            layout.addLayout(top)
        else:
            layout.addWidget(self.pill, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(self.headline)
        self.gauge = Gauge()
        layout.addWidget(self.gauge)
        self.context_note = label("guideCaution", wrap=True)
        self.context_note.setObjectName("indicatorContextNote")
        self.context_note.setProperty("qg_literal", True)
        layout.addWidget(self.context_note)
        self.context_note.hide()
        self.one_liner = label("guideOne", wrap=True)
        layout.addWidget(self.one_liner)
        self.cues = ChipRow()
        layout.addWidget(self.cues)
        self.caution = label("guideCaution", wrap=True)
        layout.addWidget(self.caution)
        self.more = QPushButton()
        self.more.setProperty("sd", "link")
        self.more.setProperty("qg_literal", True)
        self.more.setCheckable(True)
        self.more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more.toggled.connect(self._more_toggled)
        layout.addWidget(self.more, 0, Qt.AlignmentFlag.AlignLeft)
        self.details = QWidget()
        details = QVBoxLayout(self.details)
        details.setContentsMargins(0, 2, 0, 0)
        details.setSpacing(10)
        self.detail_labels = []
        for _ in range(4):
            part = QLabel()
            part.setTextFormat(Qt.TextFormat.RichText)
            part.setWordWrap(True)
            part.setProperty("sd", "guideLong")
            part.setProperty("qg_literal", True)
            part.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            details.addWidget(part)
            self.detail_labels.append(part)
        self.details.hide()
        layout.addWidget(self.details)
        self.language = "ko"
        self.long_texts = ()
        if compact:
            for widget in (self.one_liner, self.cues, self.caution):
                widget.hide()

    def _more_toggled(self, on):
        self.details.setVisible(on)
        self.more.setText(text(self.language, "guide_less" if on else "guide_more"))
        self.more_toggled.emit(on)

    def set_open(self, on):
        self.more.setChecked(bool(on))

    def show_guide(self, *, language, name, reading, state="", tone="", gauge=None, gauge_labels=("", ""),
                   short=None, long_texts=(), colors=None, context=""):
        """reading: the short sentence now ('' hides it); state: the pill's word; gauge: study_guide.gauge_value
        output or None; short: study_guide.ShortGuide (full card); long_texts: what sits behind 자세히, in order."""
        self.language = language
        self.headline.setText(reading)
        self.headline.setVisible(bool(reading))
        self.context_note.setText(context)
        self.context_note.setVisible(bool(context))
        self.pill.setText(state)
        set_prop(self.pill, "tone", tone or "flat")
        self.pill.setVisible(bool(state))
        if gauge is not None:
            kind, position, marks = gauge
            self.gauge.set_value(kind, position, marks, gauge_labels, colors)
        self.gauge.setVisible(gauge is not None)
        if not self.compact and short is not None:
            self.one_liner.setText(short.one_liner)
            self.cues.set_cues(short.cues)
            self.caution.setText(short.caution)
            for widget, shown in ((self.one_liner, short.one_liner), (self.cues, short.cues), (self.caution, short.caution)):
                widget.setVisible(bool(shown))
        self.long_texts = tuple(part for part in long_texts if part)
        for part, value in zip(self.detail_labels, (*self.long_texts, "", "", "", "")):
            part.setText(paragraph(value) if value else "")
            part.setVisible(bool(value))
        self.more.setVisible(bool(self.long_texts))
        self.more.setText(text(language, "guide_less" if self.more.isChecked() else "guide_more"))
        self.more.setAccessibleName(text(language, "guide_more_name", name=name))


class PickerRow(QFrame):
    """One study: colour, name, description or reason, placement, value now, ⓘ guide and the switch."""
    toggled = pyqtSignal(str, bool)

    def __init__(self, spec):
        super().__init__()
        self.spec = spec
        self.key = spec.key
        self.reason = ""
        self.hidden_panel = False
        self._desc = ""
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
        self.first.place_moved = lambda moved: self._show_desc()
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
        self._guide = None
        self.guide_box = QHBoxLayout()
        self.guide_box.setContentsMargins(8, 0, 4, 12)
        outer.addLayout(self.guide_box)

    @property
    def guide(self):
        """The guide card, built the first time it is asked for (27 rows: no idle cards for the window to walk)."""
        if self._guide is None:
            self._guide = GuideCard()
            self._guide.hide()
            self.guide_box.addWidget(self._guide)
        return self._guide

    def guide_open(self):
        return self._guide is not None and (self._guide.isVisible() or self.info.isChecked())

    def _guide_toggled(self, on):
        self.guide.setVisible(on)
        self._sync_open()
        if callable(self.guide_changed):
            self.guide_changed()

    def _sync_open(self):
        """While the guide is open, the card says what line 2 and the value said (the one-liner, the reading with
        its number and the pill): the row keeps only its name and place, so nothing is read twice (owner R-D9-3).
        A hidden panel's line stays: the card does not say it."""
        open_ = self.info.isChecked()
        self.desc.setVisible(not open_ or self.hidden_panel)
        self.first.fit()

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

    def _show_desc(self):
        """Line 2: the description or the reason, led by the value and the place when they left line 1 (the
        name is never cut while they can move)."""
        lead = []
        if self.first.value_moved and self.value._choices:
            lead.append(self.value._choices[0])
        if self.place.isHidden() and self.place.text():
            lead.append(self.place.text())
        self.desc.setText(" · ".join([*lead, self._desc]) if lead else self._desc)

    def show_state(self, *, language, dark, color, value, reason, place, state="", hidden="", short=None):
        """reason: the engine's availability code; hidden: the panel-limit line when the study is on but its
        sub-panel is not drawn in this window."""
        from core.education.study_guide import availability_text
        self.reason = reason
        self.hidden_panel = bool(hidden)
        self.bar.set_color(color)
        self.name.setText(self.spec.name(language))
        self.place.setText(place)
        why = polite(availability_text(reason, language), language) if reason else hidden
        self._desc = why or (short.one_liner if short is not None else "")
        self.desc.setToolTip(why or (short.one_liner if short is not None else ""))
        set_prop(self.desc, "reason", "true" if (reason or hidden) else "false")
        set_prop(self.name, "dim", "true" if reason else "false")
        shown = f"{value} · {state}" if value and value != "—" and state else value
        if self.info.isChecked():
            self.value.set_choices([""])         # the open card's reading carries the value and the pill
        else:
            self.value.set_choices([shown, value] if shown != value else [value])
        self.first.fit()
        self._show_desc()
        self._sync_open()
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


def guide_parts(key, bars, *, language, interval, supply=None, values=None, price_format=None, index=-1):
    """Everything a guide card shows for `key` on this chart: (reading, state word code, gauge, short guide,
    long texts). bars may be None (no chart yet): the card then shows only what the study is."""
    from core.education import indicators as engine
    from core.education.study_guide import gauge_value, guide, short_guide, short_reading, study_reading
    from core.market.detail_model import study_state
    spec = engine.study(key)
    short = short_guide(key, language)
    full = guide(key, language, interval)
    reading, state, gauge, now = "", "", None, ""
    if bars is not None and len(bars):
        try:
            if values is None:
                values = engine.compute_study(key, bars, supply=supply)
            reading = short_reading(key, bars, index, language=language, values=values, supply=supply)
            now = polite(study_reading(key, bars, index, language=language, values=values, supply=supply), language)
            state = study_state(key, values, bars, index)
            gauge = gauge_value(key, values, bars, index)
        except Exception:
            reading, state, gauge, now = "", "", None, ""
    if gauge is not None and gauge[0] == "scale" and gauge[1] < 0.5:
        short = short_guide(key, language, low=True)    # the caution speaks of the side the value is on
    params = text(language, "guide_params", params=full.params) if full.params else ""
    long_texts = (now, polite(f"{full.what} {full.how}", language), polite(full.caution, language), params)
    return reading, state, gauge, short, long_texts


class IndicatorPicker(QWidget):
    """Grouped, folding list of every chart study; emits the new selection."""
    changed = pyqtSignal(tuple)

    def __init__(self, *, locale=None):
        super().__init__()
        from core.education.indicators import studies_by_category
        self.ctx, self.dark = locale or LocaleContext("ko_KR"), False
        self.selected = ()
        self.context = None       # (bars, asset, interval, supply) of the open chart
        self.panel_limit = None
        self.hidden_panels = ()   # sub-panels that are on but not drawn in this window
        self.price_format = None  # the open instrument's price precision (the view sets it)
        self.volume_format = None # volume in the OHLC strip's unit (the view sets it)
        self.gauge_colors = None  # the view sets the palette's colours for the gauges
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
        # The panel limit is said where it matters (line 2 of each hidden row) and summed up here, at the top.
        self.limit_note = label("limitNote", wrap=True)
        self.limit_note.setContentsMargins(10, 6, 10, 6)
        self.limit_note.hide()
        layout.addWidget(self.limit_note)
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

    def set_context(self, bars, *, asset, interval, supply=None, panel_limit=None, hidden_panels=()):
        self.context = (bars, asset, interval, supply)
        self.panel_limit = panel_limit
        self.hidden_panels = tuple(hidden_panels or ())
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

    def gauge_labels(self, key, gauge, lang):
        if gauge is None:
            return "", ""
        kind = gauge[0]
        if kind == "band":
            if key == "ichimoku":
                return text(lang, "gauge_cloud_lower"), ""
            return text(lang, "gauge_lower"), text(lang, "gauge_upper")
        if kind in ("offset", "zero", "ratio"):
            return text(lang, f"gauge_name_{key}") if f"gauge_name_{key}" in _GAUGE_NAMES else text(lang, "gauge_line"), ""
        return "", ""

    def render(self):
        from core.education import indicators as engine
        from core.education.study_guide import category_name, disclaimer, format_value, short_guide
        from core.market.detail_model import study_state
        from core.market.presentation import study_colors
        lang = _lang(self.ctx)
        self.count.setText(text(lang, "picker_on", count=len(self.selected)))
        self.off_button.setVisible(bool(self.selected))
        self.disclaimer.setText(polite(disclaimer(lang), lang))
        bars, asset, interval, supply = self.context if self.context else (None, "domestic_stock", "1d", None)
        has_volume = bool(bars is not None and any(math.isfinite(v) for v in bars.volume))
        visible = self.isVisible()
        hidden_line = text(lang, "picker_row_hidden", count=self.panel_limit) if self.panel_limit is not None else ""
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
                value, state, values = "", "", None
                if visible and bars is not None and len(bars) and not reason:
                    try:
                        values = engine.compute_study(key, bars, supply=supply)
                        line = spec.lines[0]
                        raw = float(values[line.id][-1])
                        if not math.isfinite(raw):
                            value = "—"
                        elif line.kind == "price" and self.price_format is not None:
                            value = self.price_format(raw)
                        elif key == "volume_ma" and self.volume_format is not None:
                            value = self.volume_format(raw)
                        else:
                            value = format_value(line.kind, raw, lang)
                        code = study_state(key, values, bars)
                        state = state_word(key, code, lang)
                    except Exception:
                        value, values = "", None
                row.set_checked(key in self.selected)
                hidden = hidden_line if key in self.hidden_panels and key in self.selected else ""
                row.show_state(language=lang, dark=self.dark, color=color, value=value, reason=reason, place=place,
                               state=state, hidden=hidden, short=short_guide(key, lang))
                if row.guide_open():
                    self.fill_guide(row.guide, key, lang, bars if not reason else None, interval, supply, values)
        hidden = [k for k in self.hidden_panels if k in self.selected]
        if self.panel_limit is not None and hidden:
            self.limit_note.setText(text(lang, "picker_panel_limit", count=self.panel_limit))
            self.limit_note.show()
        else:
            self.limit_note.hide()
        if self.search.text().strip():
            self._filter(self.search.text())

    def fill_guide(self, card, key, lang, bars, interval, supply, values=None, index=-1):
        from core.education.signal_context import signal_note
        reading, code, gauge, short, long_texts = guide_parts(key, bars, language=lang, interval=interval,
                                                              supply=supply, values=values, index=index)
        from core.education.indicators import availability, study
        reason = availability(key, asset=(self.context or (None, "domestic_stock"))[1], interval=interval,
                              supply=supply, has_volume=True)
        if reason:
            from core.education.study_guide import availability_short
            reading = polite(availability_short(reason, lang), lang)
        card.show_guide(language=lang, name=study(key).name(lang), reading=reading,
                        state=state_word(key, code, lang), tone=state_tone(code), gauge=gauge,
                        gauge_labels=self.gauge_labels(key, gauge, lang), short=short, long_texts=long_texts,
                        colors=self.gauge_colors,
                        context="" if reason else signal_note(key, bars, index, language=lang, values=values))


_GAUGE_NAMES = ("gauge_name_sma", "gauge_name_ema", "gauge_name_vwap", "gauge_name_psar", "gauge_name_macd",
                "gauge_name_roc", "gauge_name_volume_ma")


__all__ = ["IndicatorPicker", "PickerGroup", "PickerRow", "GuideCard", "Gauge", "ChipRow", "Switch", "STARTER",
           "guide_parts", "state_tone", "state_word"]
