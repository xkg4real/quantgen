"""The research pages' shared look (owner approval 2026-11-17: "시안 7개 전부 승인, 앱에 적용 진행하세요").

The approved drafts (docs/product/ui_drafts_2026-11-17/, built from qg.css) follow the stock detail chart: a compact
toolbar row (title, segmented control or pill tabs, a status badge, actions on the right), a large canvas on the LEFT
and a docked settings/information column on the RIGHT (a rounded card with a full-width segmented control on top,
fold sections, compact two-column fields, the primary action pinned at the bottom), key figures as one quiet line
("label value  label value", like the chart's OHLC line), white cards with a light line and 16 px corners, small muted
captions, pill chips and numbers in the interface face's figures.

This module holds those pieces so every page looks the same. It changes no calculation or data flow: a page builds
its existing widgets (same attributes, same signals) and places them into a `Workspace`.

    ws = Workspace("Build & Test", "설계/검증")      # title in English and Korean
    ws.add_segment(("Monte Carlo", "몬테카를로"), ("Strategy Lab", "전략 실험실"))
    ws.add_badge(("Simulation · not a guarantee", "시뮬레이션 · 미래 보장 아님"))
    ws.canvas.addWidget(figures); ws.canvas.addWidget(chart_card, 1)
    page = ws.side.add_page(("Settings", "설정")); page.addWidget(fold)
    ws.side.foot.addWidget(run_button)

Text: every piece takes (English, Korean) pairs and follows the window language itself (`localized_text` on
`UiLabel`/`UiButton`-like widgets is honoured by `LanguageController`; pieces here are `qg_literal` and re-render on
`set_language`). Widgets a page passes in keep their own language handling.
"""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (QAbstractScrollArea, QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from core.theme import LIGHT
from .stock_detail_side import FoldHeader
from .stock_detail_style import line_color, numbers, set_prop, sheet as detail_sheet

PAGE_MARGINS = (30, 22, 28, 20)      # left, top, right, bottom (the drafts' .page padding)
SIDE_WIDTHS = ((1320, 360), (1120, 340), (0, 320))   # (window width at least, column width)
MIN_HEIGHT = 560


def _ko(language):
    return str(language or "ko").startswith("ko")


def pick(language, pair):
    """(English, Korean) -> the text for `language`; a plain string is returned as it is."""
    if isinstance(pair, str):
        return pair
    english, korean = pair
    return korean if _ko(language) else english


def kit_sheet(p, dark):
    """The kit's rules on top of the stock detail view's (`stock_detail_style.sheet`)."""
    from .typography import TONE_COLORS, mix
    t = TONE_COLORS[bool(dark)]
    line = line_color(p)
    soft = mix(p.surface_2, p.bg, 0.3)
    return detail_sheet(p, dark) + f"""
      QWidget#qgWorkspace, QWidget#qgCanvas, QWidget#qgCanvasPage {{ background: transparent; }}
      QScrollArea#qgCanvasScroll {{ background: transparent; border: 0; }}
      QLabel[kit='title'] {{ font-size: 22px; font-weight: 600; letter-spacing: -0.7px; color: {p.text}; }}
      QLabel[kit='sub'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[kit='badge'] {{ font-size: 12px; font-weight: 500; padding: 3px 10px; border-radius: 11px;
                             color: {p.muted}; background: {p.surface_2}; }}
      QLabel[kit='badge'][tone='ok'] {{ color: {p.success}; background: {p.accent_soft}; }}
      QLabel[kit='badge'][tone='warn'] {{ color: {p.warning}; background: {t['flat_tint']}; }}
      QLabel[kit='badge'][tone='err'] {{ color: {p.error}; background: {t['up_tint']}; }}
      QLabel[kit='lead'] {{ font-size: 15px; font-weight: 600; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[kit='leadNote'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[kit='figKey'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[kit='figValue'] {{ font-size: 13px; font-weight: 500; color: {p.text}; letter-spacing: 0px; }}
      QLabel[kit='figValue'][tone='up'] {{ color: {t['up']}; }}
      QLabel[kit='figValue'][tone='down'] {{ color: {t['down']}; }}
      QLabel[kit='figValue'][tone='ok'] {{ color: {p.success}; }}
      QLabel[kit='figValue'][tone='warn'] {{ color: {p.warning}; }}
      QLabel[kit='big'] {{ font-size: 30px; font-weight: 600; letter-spacing: -0.6px; color: {p.text}; }}
      QFrame[kit='card'] {{ background: {p.surface}; border: 1px solid {line}; border-radius: 16px; }}
      QFrame[kit='card'] QWidget#qgCardBody {{ background: transparent; }}
      QLabel[kit='cardTitle'] {{ font-size: 15px; font-weight: 500; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[kit='cardNote'] {{ font-size: 12px; color: {p.muted}; }}
      QFrame[kit='soft'] {{ background: {soft}; border: 0; border-radius: 14px; }}
      QLabel[kit='softTitle'] {{ font-size: 12px; font-weight: 600; color: {p.text}; }}
      QLabel[kit='hint'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[kit='fine'] {{ font-size: 11px; color: {p.muted}; }}
      QLabel[kit='fieldLabel'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[kit='pill'] {{ font-size: 12px; font-weight: 600; padding: 2px 9px; border-radius: 10px;
                            color: {p.muted}; background: {p.surface_2}; }}
      QLabel[kit='pill'][tone='ok'] {{ color: {p.success}; background: {p.accent_soft}; }}
      QLabel[kit='pill'][tone='warn'] {{ color: {p.warning}; background: {t['flat_tint']}; }}
      QLabel[kit='pill'][tone='err'] {{ color: {p.error}; background: {t['up_tint']}; }}
      QLabel[kit='pill'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; }}
      QLabel[kit='pill'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; }}
      QFrame[kit='rule'] {{ background: {line}; border: 0; min-height: 1px; max-height: 1px; }}
      QFrame#qgSide {{ background: {p.surface}; border: 1px solid {line}; border-radius: 16px; }}
      QFrame#dockedForm {{ background: transparent; border: 0; }}
      QFrame#dockedForm QLabel[role='heading'] {{ font-size: 15px; font-weight: 500; color: {p.text};
          letter-spacing: -0.3px; padding: 0; }}
      QFrame#dockedForm QLabel[role='caption'] {{ font-size: 12px; color: {p.muted}; }}
      QFrame#qgSide QScrollArea, QFrame#qgSide QScrollArea > QWidget > QWidget, QWidget#qgSidePage,
      QFrame#qgSide QStackedWidget, QFrame#dockedForm QWidget, QFrame[kit='card'] QWidget#qgCardBody,
      QFrame[kit='card'] > QWidget {{ background: transparent; border: 0; }}
      QWidget#qgSideFoot {{ background: transparent; border-top: 1px solid {line}; }}
      QWidget#qgWorkspace QLineEdit, QWidget#qgWorkspace QComboBox, QWidget#qgWorkspace QSpinBox,
      QWidget#qgWorkspace QDoubleSpinBox {{ border: 1px solid {line}; border-radius: 9px; background: {p.surface};
          padding: 6px 10px; min-height: 20px; font-size: 13px; }}
      QWidget#qgWorkspace QLineEdit:focus, QWidget#qgWorkspace QComboBox:focus, QWidget#qgWorkspace QSpinBox:focus,
      QWidget#qgWorkspace QDoubleSpinBox:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[kit='primary'] {{ padding: 10px 14px; border: 0; border-radius: 9px; background: {p.accent};
                                    color: {p.on_accent}; font-size: 14px; font-weight: 600; }}
      QPushButton[kit='primary']:hover {{ background: {mix(p.accent, p.text, 0.18)}; }}
      QPushButton[kit='primary']:disabled {{ background: {p.surface_2}; color: {p.muted}; }}
      QPushButton[kit='primary']:focus {{ border: 2px solid {p.text}; }}
      QPushButton[kit='secondary'] {{ padding: 8px 13px; border: 0; border-radius: 9px; background: {p.surface_2};
                                      color: {p.text}; font-size: 13px; font-weight: 500; }}
      QPushButton[kit='secondary']:hover {{ background: {p.accent_soft}; }}
      QPushButton[kit='secondary']:disabled {{ color: {mix(p.muted, p.bg, 0.4)}; }}
      QPushButton[kit='secondary']:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[kit='ghost'] {{ padding: 8px 12px; border: 0; border-radius: 9px; background: transparent;
                                  color: {p.muted}; font-size: 13px; font-weight: 500; }}
      QPushButton[kit='ghost']:hover {{ background: {p.accent_soft}; color: {p.text}; }}
      QPushButton[kit='ghost']:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[kit='pill'] {{ padding: 6px 11px; min-height: 20px; border: 0; border-radius: 8px;
                                 background: transparent; color: {p.muted}; font-size: 13px; font-weight: 500; }}
      QPushButton[kit='pill']:hover {{ background: {p.accent_soft}; color: {p.text}; }}
      QPushButton[kit='pill']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[kit='pill']:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[kit='chip'] {{ padding: 4px 10px; border: 0; border-radius: 11px; background: {p.surface_2};
                                 color: {p.text}; font-size: 12px; font-weight: 500; }}
      QPushButton[kit='chip']:hover {{ background: {p.accent_soft}; color: {p.accent}; }}
      QPushButton[kit='chip']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[kit='chip']:focus {{ border: 2px solid {p.accent}; }}
      QWidget#qgWorkspace QTableWidget {{ background: transparent; border: 0; gridline-color: transparent;
          alternate-background-color: transparent; selection-background-color: {p.accent_soft};
          selection-color: {p.text}; font-size: 13px; }}
      QWidget#qgWorkspace QTableWidget::item {{ padding: 6px 8px; border-bottom: 1px solid {line}; }}
      QWidget#qgWorkspace QHeaderView::section {{ background: transparent; border: 0; border-bottom: 1px solid {line};
          color: {p.muted}; font-size: 12px; font-weight: 500; padding: 7px 8px; }}
    """


def literal(widget):
    widget.setProperty("qg_literal", True)
    return widget


class Text(QLabel):
    """A label in both languages: `pair` is (English, Korean) or a plain string the page translates itself."""

    def __init__(self, pair="", kit="", *, wrap=False, selectable=False):
        super().__init__()
        self.pair = pair
        self.language = "ko"
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(wrap)
        literal(self)
        if kit:
            self.setProperty("kit", kit)
        if selectable:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if wrap:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.render()

    def set_pair(self, pair):
        self.pair = pair
        self.render()

    def set_language(self, language):
        self.language = language
        self.render()

    def render(self):
        value = pick(self.language, self.pair)
        if self.text() != value:
            self.setText(value)


class Button(QPushButton):
    """A button in both languages; kit is 'primary', 'secondary', 'ghost', 'pill' or 'chip'."""

    def __init__(self, pair, kit="secondary", *, checkable=False):
        super().__init__()
        self.pair, self.language = pair, "ko"
        literal(self)
        self.setProperty("kit", kit)
        self.setCheckable(checkable)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.render()

    def set_pair(self, pair):
        self.pair = pair
        self.render()

    def set_language(self, language):
        self.language = language
        self.render()

    def render(self):
        value = pick(self.language, self.pair).replace("&", "&&")
        if self.text() != value:
            self.setText(value)
        self.setAccessibleName(pick(self.language, self.pair))


class Badge(Text):
    """A small status chip in the toolbar ('● 계산 완료'); tone '', 'ok', 'warn' or 'err'."""

    def __init__(self, pair="", tone=""):
        super().__init__(pair, "badge")
        self.set_tone(tone)

    def set_tone(self, tone):
        set_prop(self, "tone", tone or "")

    def render(self):
        value = pick(self.language, self.pair)
        value = ("● " + value) if value and not value.startswith("●") else value
        if self.text() != value:
            self.setText(value)
        self.setVisible(bool(value))


class Pill(Text):
    """A status pill in rows (완료 · NOT_RUN · 설정됨); tone '', 'ok', 'warn', 'err', 'up' or 'down'."""

    def __init__(self, pair="", tone=""):
        super().__init__(pair, "pill")
        self.set_tone(tone)

    def set_tone(self, tone):
        set_prop(self, "tone", tone or "")


def rule():
    line = QFrame()
    line.setProperty("kit", "rule")
    line.setFixedHeight(1)
    return line


class Segmented(QFrame):
    """The 종목 | 지표 control: exclusive buttons on a soft track. `changed(index)`."""
    changed = pyqtSignal(int)

    def __init__(self, items=(), *, full=False):
        super().__init__()
        self.setObjectName("sdSegment")
        self.full = full
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(3, 3, 3, 3)
        self.row.setSpacing(3)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = []
        for item in items:
            self.add(item)
        if not full:
            self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def add(self, pair):
        button = Button(pair, "", checkable=True)
        button.setProperty("sd", "seg")
        button.setProperty("kit", None)
        index = len(self.buttons)
        button.clicked.connect(lambda checked=False, i=index: self.set_current(i, emit=True))
        self.group.addButton(button)
        self.row.addWidget(button, 1 if self.full else 0)
        self.buttons.append(button)
        if index == 0:
            button.setChecked(True)
        return button

    def current(self):
        return next((i for i, b in enumerate(self.buttons) if b.isChecked()), 0)

    def set_current(self, index, *, emit=False):
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            if emit:
                self.changed.emit(index)

    def set_language(self, language):
        for button in self.buttons:
            button.set_language(language)


class PillTabs(QWidget):
    """Pill tabs (the chart's period chips): exclusive, `changed(index)`; wraps onto a second line when narrow."""
    changed = pyqtSignal(int)

    def __init__(self, items=()):
        super().__init__()
        self.flow = Flow(self, gap=4)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = []
        for item in items:
            self.add(item)

    def add(self, pair):
        button = Button(pair, "pill", checkable=True)
        index = len(self.buttons)
        button.clicked.connect(lambda checked=False, i=index: self.set_current(i, emit=True))
        self.group.addButton(button)
        self.flow.add(button)
        self.buttons.append(button)
        if index == 0:
            button.setChecked(True)
        return button

    def current(self):
        return next((i for i, b in enumerate(self.buttons) if b.isChecked()), 0)

    def set_current(self, index, *, emit=False):
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            if emit:
                self.changed.emit(index)

    def set_language(self, language):
        for button in self.buttons:
            button.set_language(language)
        self.flow.place()


class Flow:
    """Widgets laid out left to right, wrapping onto new lines inside `host` (a plain QWidget)."""

    def __init__(self, host, gap=6, line_gap=None):
        self.host, self.gap, self.items = host, gap, []
        self.line_gap = gap if line_gap is None else line_gap
        host.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        original = host.resizeEvent

        def resized(event, original=original):
            original(event)
            self.place()
        host.resizeEvent = resized
        host.hasHeightForWidth = lambda: True
        host.heightForWidth = self.height_for
        host.sizeHint = lambda: QSize(self.natural_width(), self.height_for(max(1, host.width() or self.natural_width())))
        host.minimumSizeHint = lambda: QSize(min(120, self.natural_width()), self.height_for(max(1, host.width() or 120)))

    def natural_width(self):
        if not self.items:
            return 0
        return sum(i.sizeHint().width() for i in self.items if not i.isHidden()) + self.gap * max(0, len(self.items) - 1)

    def clear(self):
        for item in self.items:
            item.hide()
            item.setParent(None)
            item.deleteLater()
        self.items = []
        self.host.updateGeometry()

    def add(self, widget):
        widget.setParent(self.host)
        widget.show()
        self.items.append(widget)
        self.place()
        self.host.updateGeometry()

    def _rows(self, width):
        x = y = line = 0
        spots = []
        for item in self.items:
            if item.isHidden():
                continue
            size = item.sizeHint()
            if x and x + size.width() > width:
                x, y, line = 0, y + line + self.line_gap, 0
            spots.append((item, x, y, size))
            x += size.width() + self.gap
            line = max(line, size.height())
        return spots, (y + line if spots else 0)

    def height_for(self, width):
        return self._rows(width)[1]

    def place(self):
        spots, height = self._rows(max(1, self.host.width()))
        for item, x, y, size in spots:
            item.setGeometry(x, y, size.width(), size.height())
        if self.host.height() != height:
            self.host.setFixedHeight(height)


class KeyFigures(QWidget):
    """The quiet key-figure line ('가격 101.612   수정 듀레이션 8.007   …'), wrapping when narrow.
    `set_items([(key pair, value text, tone), ...])`; tone '', 'up', 'down', 'ok' or 'warn'."""

    def __init__(self):
        super().__init__()
        self.flow = Flow(self, gap=18, line_gap=4)
        self.language = "ko"
        self.items = ()

    def set_items(self, items):
        self.items = tuple(items)
        self.flow.clear()
        for key, value, *rest in self.items:
            tone = rest[0] if rest else ""
            pair = QWidget()
            row = QHBoxLayout(pair)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)
            k = Text(key, "figKey")
            k.set_language(self.language)
            v = numbers(Text(str(value), "figValue", selectable=True))
            set_prop(v, "tone", tone or "")
            row.addWidget(k)
            row.addWidget(v)
            pair.keys = (k, v)
            self.flow.add(pair)
        self.setVisible(bool(self.items))

    def set_language(self, language):
        self.language = language
        self.set_items(self.items)


class Card(QFrame):
    """A white card: an optional title row (title, note, a widget on the right) and a body layout (`body`)."""

    def __init__(self, title=None, note=None, *, margins=(18, 16, 18, 16), spacing=10):
        super().__init__()
        self.setProperty("kit", "card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*margins)
        outer.setSpacing(spacing)
        self.head = QHBoxLayout()
        self.head.setContentsMargins(0, 0, 0, 0)
        self.head.setSpacing(8)
        self.title = Text(title or "", "cardTitle")
        self.note = Text(note or "", "cardNote")
        self.head.addWidget(self.title)
        self.head.addWidget(self.note, 0, Qt.AlignmentFlag.AlignBottom)
        self.head.addStretch(1)
        self.head_host = QWidget()
        self.head_host.setLayout(self.head)
        self.head_host.setVisible(title is not None)
        self.note.setVisible(note is not None)
        outer.addWidget(self.head_host)
        body = QWidget()
        body.setObjectName("qgCardBody")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(spacing)
        outer.addWidget(body, 1)

    def add_head_widget(self, widget):
        self.head.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        self.head_host.show()
        return widget

    def set_language(self, language):
        self.title.set_language(language)
        self.note.set_language(language)


class Soft(QFrame):
    """A soft grey box for reading notes ('결과를 읽는 법')."""

    def __init__(self, title=None, text=None):
        super().__init__()
        self.setProperty("kit", "soft")
        box = QVBoxLayout(self)
        box.setContentsMargins(16, 13, 16, 14)
        box.setSpacing(6)
        self.layout_ = box
        self.title = Text(title or "", "softTitle")
        self.text = Text(text or "", "hint", wrap=True)
        self.title.setVisible(title is not None)
        self.text.setVisible(text is not None)
        box.addWidget(self.title)
        box.addWidget(self.text)

    def set_language(self, language):
        self.title.set_language(language)
        self.text.set_language(language)


class Fold(QWidget):
    """A fold section in the side column: the stock detail's FoldHeader (chevron, title, count) and a body."""
    toggled = pyqtSignal(bool)

    def __init__(self, title, *, count="", opened=True):
        super().__init__()
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        self.pair, self.count_pair, self.language = title, count, "ko"
        self.head = FoldHeader(height=36)
        self.head.toggled.connect(self._toggled)
        column.addWidget(self.head)
        self.body_host = QWidget()
        self.body = QVBoxLayout(self.body_host)
        self.body.setContentsMargins(4, 2, 2, 6)
        self.body.setSpacing(10)
        column.addWidget(self.body_host)
        self.head.set_open(opened)
        self.body_host.setVisible(opened)
        self.render()

    def _toggled(self, is_open):
        self.body_host.setVisible(is_open)
        self.toggled.emit(is_open)

    def set_open(self, is_open):
        self.head.set_open(is_open)
        self.body_host.setVisible(is_open)

    def set_count(self, count):
        self.count_pair = count
        self.render()

    def set_language(self, language):
        self.language = language
        self.render()

    def set_theme(self, dark):
        self.head.set_theme(dark)

    def render(self):
        self.head.title.setText(pick(self.language, self.pair))
        self.head.count.setText(pick(self.language, self.count_pair) if self.count_pair else "")
        self.head.set_open(self.head.is_open)


def field(caption, widget, *, hint=None):
    """A caption above an input (the drafts' .field)."""
    host = QWidget()
    column = QVBoxLayout(host)
    column.setContentsMargins(0, 0, 0, 0)
    column.setSpacing(5)
    host.caption = Text(caption, "fieldLabel")
    column.addWidget(host.caption)
    column.addWidget(widget)
    host.widget = widget
    if hint is not None:
        host.hint = Text(hint, "hint", wrap=True)
        column.addWidget(host.hint)
    return host


class FieldGrid(QWidget):
    """Two-column fields; `add(caption, widget, wide=False)` places a field (wide: both columns)."""

    def __init__(self, columns=2):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        self.columns = columns
        for c in range(columns):
            self.grid.setColumnStretch(c, 1)
        self._row = self._col = 0
        self.fields = []

    def add(self, caption, widget, *, wide=False, hint=None):
        host = field(caption, widget, hint=hint)
        if wide and self._col:
            self._row, self._col = self._row + 1, 0
        span = self.columns if wide else 1
        self.grid.addWidget(host, self._row, self._col, 1, span)
        self._col += span
        if self._col >= self.columns:
            self._row, self._col = self._row + 1, 0
        self.fields.append(host)
        return host

    def set_language(self, language):
        for host in self.fields:
            host.caption.set_language(language)
            if hasattr(host, "hint"):
                host.hint.set_language(language)


class EmptyState(QWidget):
    """A canvas waiting for a run: one muted line, centred."""

    def __init__(self, text):
        super().__init__()
        column = QVBoxLayout(self)
        column.addStretch(1)
        self.text = Text(text, "hint", wrap=True)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(self.text)
        column.addStretch(1)

    def set_language(self, language):
        self.text.set_language(language)


class SideColumn(QFrame):
    """The docked right column: an optional full-width segmented control, one scrolling page per segment
    (`add_page` returns its layout) and a foot pinned at the bottom (`foot`)."""

    def __init__(self):
        super().__init__()
        self.setObjectName("qgSide")
        column = QVBoxLayout(self)
        column.setContentsMargins(10, 10, 10, 12)
        column.setSpacing(10)
        self.segment = Segmented(full=True)
        self.segment.hide()
        self.segment.changed.connect(self.show_page)
        column.addWidget(self.segment)
        self.pages = QStackedWidget()
        column.addWidget(self.pages, 1)
        foot_host = QWidget()
        foot_host.setObjectName("qgSideFoot")
        self.foot = QVBoxLayout(foot_host)
        self.foot.setContentsMargins(4, 12, 4, 2)
        self.foot.setSpacing(8)
        self.foot_host = foot_host
        column.addWidget(foot_host)
        self.page_layouts = []

    def add_page(self, title=None):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        page.setObjectName("qgSidePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 8, 4)
        layout.setSpacing(14)
        scroll.setWidget(page)
        self.pages.addWidget(scroll)
        self.page_layouts.append(layout)
        if title is not None:
            self.segment.add(title)
            self.segment.setVisible(len(self.segment.buttons) > 1)
        return layout

    def finish(self):
        """Call after the pages are filled: each page ends with a stretch, so content sits at the top."""
        for layout in self.page_layouts:
            layout.addStretch(1)
        self.foot_host.setVisible(self.foot.count() > 0)

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        self.segment.set_current(index)

    def set_language(self, language):
        self.segment.set_language(language)


class _ViewportFit(QObject):
    def __init__(self, workspace, viewport):
        super().__init__(workspace)
        self.workspace, self.viewport = workspace, viewport

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self.workspace.fit_height(self.viewport.height())
        return False


class Mode:
    """One tab of a page with several (몬테카를로 | 전략 실험실): its own canvas and its own side column."""

    def __init__(self, index, canvas, side, canvas_host):
        self.index, self.canvas, self.side, self.canvas_host = index, canvas, side, canvas_host


class Workspace(QWidget):
    """A research page: toolbar row, then the canvas (left, scrolls by itself) and the side column (right).

    A page with tabs calls `add_mode(pair)` for each: every mode has its own canvas layout and SideColumn, and the
    toolbar's segmented control (or pill tabs, `switch='pills'`) switches them (`mode_changed(index)`)."""
    mode_changed = pyqtSignal(int)

    def __init__(self, title=None, *, canvas_scroll=True, side=True, switch="segment"):
        super().__init__()
        self.setObjectName("qgWorkspace")
        self.language, self.colors, self.dark = "ko", LIGHT, False
        self.localized = []           # pieces that follow set_language
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)
        self.toolbar = QHBoxLayout()
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setSpacing(10)
        self.title = Text(title or "", "title")
        self.title.setVisible(title is not None)
        self.toolbar.addWidget(self.title, 0, Qt.AlignmentFlag.AlignVCenter)
        self.toolbar_left = QHBoxLayout()
        self.toolbar_left.setSpacing(10)
        self.toolbar.addLayout(self.toolbar_left)
        self.toolbar.addStretch(1)
        self.toolbar_right = QHBoxLayout()
        self.toolbar_right.setSpacing(8)
        self.toolbar.addLayout(self.toolbar_right)
        toolbar_host = QWidget()
        toolbar_host.setLayout(self.toolbar)
        toolbar_host.setMinimumHeight(40)
        self.toolbar_host = toolbar_host
        column.addWidget(toolbar_host)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(16)
        self.canvas_scrolls = canvas_scroll
        self.canvas_stack = QStackedWidget()
        self.side_stack = QStackedWidget()
        self.modes = []
        self.switch_kind, self.switch = switch, None
        body.addWidget(self.canvas_stack, 1)
        if side:
            body.addWidget(self.side_stack)
        self.has_side = side
        column.addLayout(body, 1)
        first = self._make_mode()
        self.canvas, self.side, self.canvas_scroll = first.canvas, first.side, first.canvas_host
        self.localized.append(self.title)
        self.set_theme(LIGHT)

    # Toolbar ---------------------------------------------------------------------------------------
    def add_toolbar(self, widget, *, right=False):
        """Add a widget after the title (right=False) or in the right-hand group."""
        (self.toolbar_right if right else self.toolbar_left).addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        if hasattr(widget, "set_language"):
            self.localized.append(widget)
        return widget

    def _make_mode(self):
        canvas_host = QWidget()
        canvas_host.setObjectName("qgCanvas")
        canvas = QVBoxLayout(canvas_host)
        canvas.setContentsMargins(0, 0, 0, 0)
        canvas.setSpacing(12)
        if self.canvas_scrolls:
            scroll = QScrollArea()
            scroll.setObjectName("qgCanvasScroll")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            # Content narrower than its own minimum is never squashed (A3): it scrolls inside the canvas, not the page.
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            canvas_host.setObjectName("qgCanvasPage")
            scroll.setWidget(canvas_host)
            self.canvas_stack.addWidget(scroll)
            holder = scroll
        else:
            self.canvas_stack.addWidget(canvas_host)
            holder = canvas_host
        side = SideColumn() if self.has_side else None
        if side is not None:
            self.side_stack.addWidget(side)
            self.localized.append(side)
        mode = Mode(len(self.modes), canvas, side, holder)
        self.modes.append(mode)
        return mode

    def add_mode(self, pair):
        """A tab: the first call names the page's first mode (made in __init__); later calls add one."""
        if self.switch is None:
            self.switch = Segmented() if self.switch_kind == "segment" else PillTabs()
            self.switch.changed.connect(self.set_mode)
            self.add_toolbar(self.switch)
            mode = self.modes[0]
        else:
            mode = self._make_mode()
        self.switch.add(pair)
        self.switch.set_language(self.language)
        return mode

    def current_mode(self):
        return self.canvas_stack.currentIndex()

    def set_mode(self, index):
        if not 0 <= index < len(self.modes):
            return
        self.canvas_stack.setCurrentIndex(index)
        if self.has_side:
            self.side_stack.setCurrentIndex(index)
            self.side = self.modes[index].side
        self.canvas = self.modes[index].canvas
        if self.switch is not None:
            self.switch.set_current(index)
        self.mode_changed.emit(index)

    def finish(self):
        """Call once the modes are filled (the side columns' pages end with a stretch)."""
        for index in range(self.side_stack.count()):
            side = self.side_stack.widget(index)
            if isinstance(side, SideColumn) and not getattr(side, "_finished", False):
                side.finish()
                side._finished = True

    def add_side(self):
        """Another right column in the side stack (one per tab when a page keeps its own tab container)."""
        side = SideColumn()
        self.side_stack.addWidget(side)
        self.localized.append(side)
        return side

    def bind_tabs(self, tabs, pairs, *, sides=None, kind="segment", on_change=None):
        """Drive an existing tab container (a QTabWidget, `CurrentPageTabs` or `CurrentPageStack`, kept for its callers
        and tests) from a toolbar switch: its own tab bar is hidden; switching shows the matching right column
        (`sides[i]`, default the side stack's i-th) and calls `on_change(index)`."""
        switch = Segmented(pairs) if kind == "segment" else PillTabs(pairs)
        self.add_toolbar(switch)
        bar = getattr(tabs, "tabBar", None)
        if callable(bar):
            tabs.tabBar().hide()
            tabs.setDocumentMode(True)
        sides = list(sides) if sides is not None else None

        def follow(index):
            switch.set_current(index)
            if self.has_side:
                if sides is not None and 0 <= index < len(sides):
                    self.side_stack.setCurrentWidget(sides[index])
                    self.side = sides[index]
                elif 0 <= index < self.side_stack.count():
                    self.side_stack.setCurrentIndex(index)
                    self.side = self.side_stack.currentWidget()
            if on_change is not None:
                on_change(index)
        switch.changed.connect(tabs.setCurrentIndex)
        tabs.currentChanged.connect(follow)
        follow(tabs.currentIndex() if tabs.currentIndex() >= 0 else 0)
        return switch

    def add_segment(self, *pairs):
        segment = Segmented(pairs)
        self.add_toolbar(segment)
        return segment

    def add_badge(self, pair="", tone=""):
        return self.add_toolbar(Badge(pair, tone))

    def add_action(self, pair, kit="secondary"):
        return self.add_toolbar(Button(pair, kit), right=True)

    def follow(self, widget):
        """Have `widget.set_language` called with the window language."""
        self.localized.append(widget)
        widget.set_language(self.language) if hasattr(widget, "set_language") else None
        return widget

    # Size ------------------------------------------------------------------------------------------
    def fit_to(self, scroll_area: QAbstractScrollArea, *, margins=PAGE_MARGINS):
        """Fill the page's viewport like the stock detail screen: the page itself does not scroll; the canvas and the
        side column scroll on their own. `scroll_area` is the window page's QScrollArea."""
        layout = self.parentWidget().layout() if self.parentWidget() is not None else None
        if layout is not None:
            layout.setContentsMargins(*margins)
        self._fit_margins = margins[1] + margins[3]
        viewport = scroll_area.viewport()
        self._fitter = _ViewportFit(self, viewport)
        viewport.installEventFilter(self._fitter)
        self.fit_height(viewport.height())

    def fit_height(self, height):
        target = max(MIN_HEIGHT, int(height) - getattr(self, "_fit_margins", 0))
        if self.minimumHeight() != target or self.maximumHeight() != target:
            self.setFixedHeight(target)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.has_side:
            window = self.window().width() if self.window() is not None else self.width()
            width = next(w for limit, w in SIDE_WIDTHS if window >= limit)
            if self.side_stack.width() != width or self.side_stack.minimumWidth() != width:
                self.side_stack.setFixedWidth(width)

    # Language and theme ----------------------------------------------------------------------------------
    def set_language(self, language):
        self.language = "ko" if _ko(language) else "en"
        for widget in self.localized:
            try:
                widget.set_language(self.language)
            except RuntimeError:
                pass
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (Text, Button, Fold, FieldGrid, KeyFigures, Card, Soft, Segmented, PillTabs,
                                   EmptyState)) and widget not in self.localized:
                widget.set_language(self.language)

    def set_theme(self, colors, dark=None):
        from .typography import is_dark
        self.colors = colors
        self.dark = is_dark(colors) if dark is None else bool(dark)
        self.setStyleSheet(kit_sheet(colors, self.dark))
        for fold in self.findChildren(Fold):
            fold.set_theme(self.dark)


__all__ = ["Workspace", "SideColumn", "Segmented", "PillTabs", "Flow", "KeyFigures", "Card", "Soft", "Fold",
           "FieldGrid", "field", "EmptyState", "Text", "Button", "Badge", "Pill", "rule", "kit_sheet", "pick",
           "PAGE_MARGINS", "SIDE_WIDTHS"]
