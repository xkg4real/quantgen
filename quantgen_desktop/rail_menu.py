"""The 시장 menu's rows and cascading flyouts (owner ruling UI-D11, 2026-11-12).

Owner: "주식 하부 유야이다 그러면 거기 마우스 휠 올려놓으면 더 하부로 국내, 미국, 글로벌 뭐 이런 식으로 볼수있고 거기서
국내에 마우스 올려놓으면 다시 거래대금 거래량 급상승 급하락 이렇게 누를수있게. 누르면 지금 ui랑 똑같이 저 화면으로 바로
넘어갈수잇게". Under 시장 the rail lists the big categories (`shell_rail.MARKET_CATEGORIES`) as `MarketRailRow`s with
a chevron; pointing at one (or Enter, →, a click) opens a flyout to its right (`FlyoutPanel`), and pointing at a row
of that flyout opens the next one, like a desktop menu bar's cascades. A leaf goes straight to what it names; so does
a click on a row that has one page of its own (국내 or 미국 under 주식 and ETF, 크립토, 선물, 회사채: `MenuNode.leaf`),
while pointing at it still opens its flyout (UI-D11 review).

The flyouts are children of the window's central widget drawn over the page, not popup windows: the pointer moves
freely between the rail and the flyouts (a popup would grab it), the window's captures include them, and the window
sheet's fonts and colours apply. `RailFlyouts` keeps the open chain (one panel per level) and closes it when the
pointer has left the rail rows and every flyout for `CLOSE_DELAY_MS`, on a click elsewhere, on Esc, when the window
moves, resizes or loses focus, and when the page changes. Moving to a sibling row switches the open flyout after
`SWITCH_DELAY_MS`, cancelled when the pointer reaches the flyout already open (a diagonal move to it does not flick
the menu over to the row it crosses). A switch still waiting when the pointer leaves the flyouts, or when the level it
targets closes, is dropped (UI-D11 review: it reopened a menu the pointer had left, and ran on a closed level).

Keyboard: in a flyout ↑/↓ (Home/End) move, → / Enter / Space open the next flyout and focus its first row, Enter /
Space on a leaf opens it, ← / Esc close the flyout and return to the row it came from, Tab closes them all. The rail
row opens its flyout with → / Enter / a click (`shell_rail.RailKeys`). Focus shows as a ring (`focusRing`, keyboard
focus only), the pointed row as a tint, the row whose flyout is open stays tinted, and the row of what the window
shows is in the accent colour.

No shadow effect (`QGraphicsDropShadowEffect` blurs text at fractional scaling, see `typography.PANEL_DEPTH`): each
panel paints its rounded 8 px box with the light line token, and a `FlyoutShadow` behind it paints the soft shadow.
The shadow lets the pointer through, so a click just outside the box reaches the page (UI-D11 review).
"""
from __future__ import annotations

import time

from PyQt6.QtCore import QEvent, QObject, QPoint, QPointF, QRectF, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from core.theme import LIGHT
from .localization import SKIP_PASS
from .shell_rail import KEYBOARD_FOCUS, set_focus_ring

ROW_HEIGHT = 38            # flyout rows (owner: roomy rows, 36-40 px)
PANEL_PADDING = 6          # inside the box, around the rows
PANEL_RADIUS = 8
SHADOW = 12                # how far the painted shadow reaches around a box
PANEL_GAP = 6              # between a row and the flyout it opens (a rail row, the strip button or a flyout's box)
PANEL_MIN_WIDTH = 168
PANEL_MAX_WIDTH = 320
EDGE_MARGIN = 8            # a flyout keeps this far from the window's edges
CHEVRON_RIGHT = 15         # the chevron's centre from a row's right edge
OPEN_DELAY_MS = 90         # pointing at a rail row opens its flyout after this (a pass over the rail opens nothing)
SWITCH_DELAY_MS = 160      # pointing at a sibling row replaces the open flyout after this
CLOSE_DELAY_MS = 420       # the pointer has left the rows and the flyouts this long: all close
SETTLE_MS = 150            # a flyout the keyboard opened under a resting pointer ignores the pointer this long


def _repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def set_flag(widget, name, value):
    """A boolean style property, repolished only when it changes."""
    value = bool(value)
    if bool(widget.property(name)) != value:
        widget.setProperty(name, value)
        _repolish(widget)


def draw_chevron(painter, x, y, color, size=3.8):
    """A thin '›' centred at (x, y)."""
    pen = QPen(QColor(color), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath(QPointF(x - size / 2, y - size))
    path.lineTo(QPointF(x + size / 2, y))
    path.lineTo(QPointF(x - size / 2, y + size))
    painter.drawPath(path)


class ChevronButton(QPushButton):
    """A text button with a '›' painted at its right edge when it opens a flyout. `tones` (rest, pointed,
    current) come from the theme; the chevron follows the text's state."""

    def __init__(self, text="", *, chevron=True):
        super().__init__(text)
        self.chevron = chevron
        self.open = False
        self.tones = (LIGHT.muted, LIGHT.text, LIGHT.accent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoDefault(False)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_open(self, value):
        """Its flyout is open (a style property in a flyout; `RailAnchor` paints it instead)."""
        self.open = bool(value)
        set_flag(self, "open", self.open)

    def chevron_color(self):
        rest, pointed, current = self.tones
        if self.isChecked() or self.property("current"):
            return current
        if self.underMouse() or self.open or self.property("focusRing"):
            return pointed
        return rest

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.chevron:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            draw_chevron(painter, self.width() - CHEVRON_RIGHT, self.height() / 2, self.chevron_color())
            painter.end()


class RailAnchor:
    """A rail widget a first flyout opens from: its open state is painted (a tint behind it), not a style property.
    A property change re-polishes the widget, which re-lays out the rail and so starts a language pass over the
    whole window (`localization.LanguageController`), too slow to follow a pointer."""
    tint = "#00000000"
    guide = ""          # a colour for the left guide line while open ('' for none)

    def set_open(self, value):
        self.open = bool(value)
        self.update()

    def paint_open(self, painter):
        if not getattr(self, "open", False):
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.tint))
        left = 2 if self.guide else 0
        area = QRectF(self.rect()).adjusted(left, 0, 0, 0)
        painter.drawRoundedRect(area, 6, 6)
        if self.guide:
            painter.fillRect(QRectF(0, 0, 2, self.height()), QColor(self.guide))


class MarketRailRow(RailAnchor, ChevronButton):
    """One big category under 시장 in the rail (지수, 주식, …): opens its flyout; checked while the window shows
    something of that category. Styled by `QPushButton[marketRow='true']` in `typography.rail_stylesheet`; while
    its flyout is open it sits on the flyout tint with an accent guide line."""

    def __init__(self, key):
        super().__init__()
        self.key = key
        self.setCheckable(True)
        for name in ("subnav", "marketRow", "flyout", "qg_literal"):
            self.setProperty(name, True)
        from .typography import MARKET_ROW_HEIGHT
        # Its height is its size hint (the vertical policy is Fixed), not a fixed size: a re-polish (the focus ring,
        # a theme) applies the sheet's min-height again, which a fixed size would not survive.
        self.row_height = MARKET_ROW_HEIGHT

    def sizeHint(self):
        size = super().sizeHint()
        size.setHeight(self.row_height)
        return size

    def set_row_height(self, height):
        if height != self.row_height:
            self.row_height = int(height)
            self.updateGeometry()

    def set_open(self, value):
        RailAnchor.set_open(self, value)

    def paintEvent(self, event):
        if self.open:
            painter = QPainter(self)
            self.paint_open(painter)
            painter.end()
        super().paintEvent(event)


class StripMenuButton(RailAnchor, QPushButton):
    """The hidden rail's 시장 button (styled as the strip's other icon buttons, `railIcon`)."""

    def __init__(self, accessible_name, size):
        super().__init__()
        self.open = False
        for name in ("railIcon", "flyout"):
            self.setProperty(name, True)
        self.setFixedSize(size, size)
        self.setAccessibleName(accessible_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoDefault(False)

    def paintEvent(self, event):
        if self.open:
            painter = QPainter(self)
            self.paint_open(painter)
            painter.end()
        super().paintEvent(event)


class FlyoutRow(ChevronButton):
    """One row of a flyout: a sub-market or category that opens the next flyout, or a leaf. Where a leaf opens is
    its tooltip (UI-D11 review: a muted '분석' on every row named another rail page)."""

    def __init__(self, node, level, flyouts):
        super().__init__(node.text.replace("&", "&&"), chevron=bool(node.children))  # '&' is not a mnemonic here
        self.node, self.level, self.flyouts = node, level, flyouts
        self.setProperty("flyoutRow", True)
        self.setProperty("qg_literal", True)  # already in the window language (`shell_rail.market_menu`)
        self.setFixedHeight(ROW_HEIGHT)
        self.setAccessibleName(node.text)
        if node.tip:
            self.setToolTip(node.tip)
        self.clicked.connect(lambda: flyouts.row_clicked(self))

    def enterEvent(self, event):
        super().enterEvent(event)
        self.flyouts.row_entered(self)

    def event(self, event):
        # Tab and Backtab reach QWidget.event's focus chain before keyPressEvent: the flyouts take them first.
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            if self.flyouts.row_key(self, event):
                return True
        return super().event(event)

    def keyPressEvent(self, event):
        if not self.flyouts.row_key(self, event):
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        set_focus_ring(self, event.reason() in KEYBOARD_FOCUS)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        set_focus_ring(self, False)
        super().focusOutEvent(event)


class FlyoutShadow(QWidget):
    """The soft shadow under a flyout's box: rings that add up toward the box, a little lower than it. It lets the
    pointer through (a click beside the box reaches the page) and follows its panel (`FlyoutPanel.moveEvent`)."""

    def __init__(self, flyouts, parent=None):
        super().__init__(parent)
        self.flyouts = flyouts
        self.setObjectName("railFlyoutShadow")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def follow(self, panel):
        self.setGeometry(panel.geometry().adjusted(-SHADOW, -SHADOW, SHADOW, SHADOW))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        box = QRectF(self.rect()).adjusted(SHADOW, SHADOW, -SHADOW, -SHADOW)
        step = 10 if self.flyouts.dark else 3
        for spread in range(SHADOW, 0, -1):
            painter.setBrush(QColor(0, 0, 0, step))
            painter.drawRoundedRect(box.adjusted(-spread, -spread + 4, spread, spread + 4),
                                    PANEL_RADIUS + spread, PANEL_RADIUS + spread)
        painter.end()


class FlyoutPanel(QWidget):
    """One flyout: a rounded box of rows. The widget is the box itself, so the pointer is inside the menu exactly
    where the box is drawn; its shadow is a separate `FlyoutShadow` behind it."""

    def __init__(self, flyouts, nodes, level, parent=None):
        super().__init__(parent)
        self.setObjectName("railFlyout")
        self.flyouts, self.level = flyouts, level
        self.shadow = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PANEL_PADDING, PANEL_PADDING, PANEL_PADDING, PANEL_PADDING)
        layout.setSpacing(2)
        self.rows = []
        for node in nodes:
            row = FlyoutRow(node, level, flyouts)
            row.panel = self
            layout.addWidget(row)
            self.rows.append(row)

    def fit(self):
        """Size to the widest row, within PANEL_MIN_WIDTH..PANEL_MAX_WIDTH."""
        self.ensurePolished()
        widths = [row.sizeHint().width() for row in self.rows]
        inner = max(PANEL_MIN_WIDTH, min(PANEL_MAX_WIDTH, max(widths or [0])))
        for row in self.rows:
            row.setFixedWidth(inner)
        self.layout().activate()
        self.setFixedSize(inner + 2 * PANEL_PADDING, self.layout().sizeHint().height())

    def box(self):
        """The visible box, in this widget's coordinates (the whole widget)."""
        return QRectF(self.rect())

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.shadow is not None:
            self.shadow.follow(self)

    def paintEvent(self, event):
        palette, dark = self.flyouts.palette, self.flyouts.dark
        from .typography import mix
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(QColor(palette.surface))
        painter.setPen(QPen(QColor(mix(palette.border, palette.surface, 0.15 if dark else 0.0)), 1))
        painter.drawRoundedRect(self.box().adjusted(0.5, 0.5, -0.5, -0.5), PANEL_RADIUS, PANEL_RADIUS)
        painter.end()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.flyouts.pointer_in(self)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.flyouts.pointer_out(self)


class RailFlyouts(QObject):
    """The open chain of flyouts over the window (see the module docstring)."""
    activated = pyqtSignal(object)   # a leaf: ('market', page, category), ('home', symbol) or ('tool', pane, sub)
    opened = pyqtSignal(int)         # a flyout opened at this level
    closed = pyqtSignal()            # every flyout closed

    def __init__(self, host, window):
        super().__init__(window)
        self.host, self.window = host, window
        self.panels, self.anchors = [], []   # one panel per level, and the widget it opened from
        self.roots = {}                      # anchor (rail row, strip button) -> () -> its flyout's nodes
        self.current = lambda: frozenset()   # () -> the `MenuNode.mark`s of what the window shows
        self.palette, self.dark, self.sheet = LIGHT, False, ""
        self._pending = None                 # (level it replaces or closes, action)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._run_pending)
        self._closer = QTimer(self)
        self._closer.setSingleShot(True)
        self._closer.setInterval(CLOSE_DELAY_MS)
        self._closer.timeout.connect(self.close_all)
        self._listening = False
        window.installEventFilter(self)

    # Setup ------------------------------------------------------------------------------------
    def watch_root(self, anchor, nodes):
        """A rail row or strip button that opens a first flyout; `nodes()` gives its rows' `MenuNode`s."""
        self.roots[anchor] = nodes
        anchor.installEventFilter(self)

    def set_theme(self, palette, dark):
        from .typography import flyout_stylesheet, flyout_tint
        self.palette, self.dark = palette, bool(dark)
        self.sheet = flyout_stylesheet(palette, self.dark)
        self.close_all()
        for anchor in self.roots:
            if isinstance(anchor, RailAnchor):
                anchor.tint = flyout_tint(palette, self.dark)
                anchor.guide = palette.accent if isinstance(anchor, MarketRailRow) else ""
                if isinstance(anchor, ChevronButton):
                    anchor.tones = self.tones()
                anchor.update()

    def tones(self):
        p = self.palette
        return (p.muted, p.text, p.accent)

    # State ------------------------------------------------------------------------------------
    def is_open(self):
        return bool(self.panels)

    def open_path(self):
        """The texts of the rows whose flyouts are open, from the rail down ('주식', '국내')."""
        return tuple(anchor.node.text if isinstance(anchor, FlyoutRow) else anchor.text() for anchor in self.anchors)

    def _focus_inside(self):
        focus = QApplication.focusWidget()
        return focus is not None and any(panel.isAncestorOf(focus) for panel in self.panels)

    def _hit(self, point):
        """Whether a global point is on a flyout's box or on a rail row that opens one (by position: a press a row
        ignores, a right click, reaches its parents too). A flyout's shadow is not the flyout."""
        widgets = [*self.panels, *(root for root in self.roots if root.isVisible())]
        return any(widget.rect().contains(widget.mapFromGlobal(point)) for widget in widgets)

    # Opening and closing ----------------------------------------------------------------------
    def open_root(self, anchor, *, focus=False):
        return self.open(0, anchor, self.roots[anchor](), focus=focus)

    def open_child(self, row, *, focus=False):
        """The flyout of a row in the open chain; nothing when its panel has closed meanwhile (a switch the pointer
        scheduled, run after ← / Esc closed that level)."""
        if row.level >= len(self.panels) or self.panels[row.level] is not getattr(row, "panel", None):
            return None
        return self.open(row.level + 1, row, row.node.children, focus=focus)

    def open(self, level, anchor, nodes, *, focus=False):
        self._cancel()
        self.close(level)
        self._closer.stop()  # after the close: hiding a flyout under the pointer reports a leave
        if level > len(self.panels):
            return None  # its parent flyout is gone: nothing to open beside
        shadow = FlyoutShadow(self)
        panel = FlyoutPanel(self, nodes, level)
        panel.shadow = shadow
        for widget in (shadow, panel):
            widget.setProperty(SKIP_PASS, True)  # rows already in the window language: no window-wide language pass
            widget.setParent(self.host)
        panel.setStyleSheet(self.sheet)
        current, tones = self.current(), self.tones()
        for row in panel.rows:
            row.tones = tones
            set_flag(row, "current", row.node.mark in current)
        panel.fit()
        self._place(panel, anchor, level)
        self.panels.append(panel)
        self.anchors.append(anchor)
        anchor.set_open(True)
        self._quiet()
        panel.keyboard, panel.opened_at = bool(focus), time.monotonic()
        shadow.follow(panel)
        shadow.show()
        shadow.raise_()
        panel.show()
        panel.raise_()
        self._listen(True)
        if focus and panel.rows:
            panel.rows[0].setFocus(Qt.FocusReason.TabFocusReason)
        self.opened.emit(level)
        return panel

    def _place(self, panel, anchor, level):
        """PANEL_GAP right of the row it came from (a rail row or the strip button at level 0, the parent flyout's
        box deeper: UI-D11 review, the first flyout sat 19 px off its row), its first row level with that row,
        kept inside the window."""
        host = self.host
        if level == 0:
            left = anchor.mapTo(host, QPoint(anchor.width(), 0)).x()
        else:
            parent = self.panels[level - 1]
            left = parent.x() + parent.width()
        left += PANEL_GAP
        middle = anchor.mapTo(host, QPoint(0, 0)).y() + anchor.height() / 2
        top = round(middle - (PANEL_PADDING + ROW_HEIGHT / 2))
        lowest = host.height() - EDGE_MARGIN - panel.height()
        top = max(EDGE_MARGIN, min(top, lowest))
        x = min(left, host.width() - EDGE_MARGIN - panel.width())
        panel.move(x, top)

    def close(self, level=0, *, keyboard=False):
        """Close the flyouts at `level` and deeper. Focus inside them returns to the row they came from (with its
        ring when the keyboard closed them)."""
        if len(self.panels) <= level:
            return
        self._cancel()  # a switch waiting on the pointer targets a level that is closing (UI-D11 review)
        returning = self._focus_inside() or keyboard
        target = self.anchors[level]
        while len(self.panels) > level:
            panel, anchor = self.panels.pop(), self.anchors.pop()
            anchor.set_open(False)
            focus = QApplication.focusWidget()
            if returning and focus is not None and panel.isAncestorOf(focus):
                if target.isVisible():
                    reason = Qt.FocusReason.TabFocusReason if keyboard else Qt.FocusReason.OtherFocusReason
                    target.setFocus(reason)
                else:
                    focus.clearFocus()
            self._quiet()
            for widget in (panel, panel.shadow):
                if widget is not None:
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()
        if keyboard and target.isVisible() and not target.hasFocus():
            target.setFocus(Qt.FocusReason.TabFocusReason)
        if not self.panels:
            self._cancel()
            self._closer.stop()
            self._listen(False)
            self.closed.emit()

    def close_all(self, *_args):
        self.close(0)

    def _quiet(self):
        """Showing or hiding a flyout asks its host for a layout pass, which would start a window-wide language
        pass (`localization.LanguageController`, about 0.1 s): tell it this one is ours."""
        localizer = getattr(self.window, "localizer", None)
        if localizer is not None and hasattr(localizer, "quiet"):
            localizer.quiet(self.host)
            localizer.quiet(self.window)  # the host's request reaches the window's own layout too

    # Pointer ----------------------------------------------------------------------------------
    def _schedule(self, level, action, delay):
        self._pending = (level, action)
        self._timer.start(delay)

    def _cancel(self, level=None):
        if self._pending is not None and (level is None or self._pending[0] == level):
            self._pending = None
            self._timer.stop()

    def _run_pending(self):
        pending, self._pending = self._pending, None
        if pending is not None:
            pending[1]()

    def root_entered(self, anchor):
        self._closer.stop()
        if self.panels and self.anchors[0] is anchor:
            self._cancel()
            return
        self._schedule(0, lambda: self.open_root(anchor), SWITCH_DELAY_MS if self.panels else OPEN_DELAY_MS)

    def root_clicked(self, anchor, *, keyboard=False):
        """A rail row clicked (or Enter / Space / → on it): its flyout opens, with focus in it from the keyboard."""
        if self.panels and self.anchors[0] is anchor:
            self.close(1)
            if keyboard and self.panels[0].rows:
                self.panels[0].rows[0].setFocus(Qt.FocusReason.TabFocusReason)
            return self.panels[0]
        return self.open_root(anchor, focus=keyboard)

    def row_entered(self, row):
        self._closer.stop()
        level = row.level
        if level >= len(self.panels) or self.panels[level] is not getattr(row, "panel", None):
            return
        panel = self.panels[level]
        if panel.keyboard and time.monotonic() - panel.opened_at < SETTLE_MS / 1000:
            return  # it opened under a resting pointer: the keyboard's first row keeps the focus
        if self._focus_inside() and not row.hasFocus():
            row.setFocus(Qt.FocusReason.MouseFocusReason)  # one highlighted row: the focus follows the pointer
        child_open = len(self.panels) > level + 1
        if row.node.children:
            if child_open and self.anchors[level + 1] is row:
                self._cancel()
                return
            if child_open:
                self._schedule(level + 1, lambda: self.open_child(row), SWITCH_DELAY_MS)
            else:
                self._cancel()
                self.open_child(row)
        elif child_open:
            self._schedule(level + 1, lambda: self.close(level + 1), SWITCH_DELAY_MS)
        else:
            self._cancel()

    def pointer_in(self, panel):
        self._closer.stop()
        self._cancel(panel.level)  # reached the flyout already open: no switch away from it

    def pointer_out(self, _panel=None):
        """The pointer left a rail row or a flyout: a switch it scheduled is dropped (a quick swipe out over a lower
        row must not open that row's flyout after the pointer has gone, UI-D11 review), and unless it comes back
        everything closes after CLOSE_DELAY_MS."""
        self._cancel()
        if self.panels:
            self._closer.start()

    # Activation and keys ----------------------------------------------------------------------
    def row_clicked(self, row):
        """A click, Enter or Space: a row with a page of its own (a leaf, or 국내 / 미국 under 주식 and ETF) opens it;
        a row with only a flyout opens that, with focus in it from the keyboard."""
        if row.node.leaf:
            self.activate(row)
        elif row.node.children:
            self.descend(row)

    def descend(self, row):
        """The row's flyout, open (from the keyboard, with focus on its first row)."""
        keyboard = bool(row.property("focusRing"))
        if len(self.panels) > row.level + 1 and self.anchors[row.level + 1] is row:
            if keyboard and self.panels[row.level + 1].rows:
                self.panels[row.level + 1].rows[0].setFocus(Qt.FocusReason.TabFocusReason)
            return
        self.open_child(row, focus=keyboard)

    def activate(self, row):
        """A leaf: every flyout closes, then the window opens it (`activated`). From the keyboard, focus goes
        back to the rail row the chain started from, with its ring."""
        keyboard = bool(row.property("focusRing"))
        root = self.anchors[0] if self.anchors else None
        leaf = row.node.leaf
        self.close(0, keyboard=keyboard)
        self.activated.emit(leaf)
        if keyboard and root is not None and root.isVisible() and not root.hasFocus():
            root.setFocus(Qt.FocusReason.TabFocusReason)

    def row_key(self, row, event):
        if event.modifiers() not in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.KeypadModifier,
                                     Qt.KeyboardModifier.ShiftModifier):
            return False
        key, level = event.key(), row.level
        rows = [each for each in row.panel.rows if each.isEnabled()]
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
            index = rows.index(row)
            target = {Qt.Key.Key_Up: (index - 1) % len(rows), Qt.Key.Key_Down: (index + 1) % len(rows),
                      Qt.Key.Key_Home: 0, Qt.Key.Key_End: len(rows) - 1}[key]
            self._cancel()
            self.close(level + 1)
            rows[target].setFocus(Qt.FocusReason.TabFocusReason)
            return True
        if key == Qt.Key.Key_Right:
            if row.node.children:
                set_focus_ring(row, True)
                self.descend(row)
            return True
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            set_focus_ring(row, True)
            self.row_clicked(row)
            return True
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Escape):
            self.close(level, keyboard=True)
            return True
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            root = self.anchors[0] if self.anchors else None
            self.close_all()
            if root is not None and root.isVisible():
                root.setFocus(Qt.FocusReason.TabFocusReason)
            return True
        return False

    # Window and application events -------------------------------------------------------------
    def _listen(self, on):
        if on == self._listening:
            return
        self._listening = on
        app = QApplication.instance()
        if on:
            app.installEventFilter(self)
        else:
            app.removeEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if watched in self.roots:
            if kind == QEvent.Type.Enter:
                self.root_entered(watched)
            elif kind == QEvent.Type.Leave:
                self.pointer_out()  # passing over a rail row opens nothing
            return False
        if watched is self.window:
            if kind in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.WindowDeactivate, QEvent.Type.Hide):
                self.close_all()
            return False
        if not self.panels or not isinstance(watched, QWidget):
            return False
        if kind == QEvent.Type.MouseButtonPress and not self._hit(event.globalPosition().toPoint()):
            self.close_all()  # a click elsewhere closes the menu and still does what it does
        elif kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape and not self._focus_inside():
            if not (watched in self.roots):
                self.close_all()
                return True
        return False


__all__ = ["RailFlyouts", "FlyoutPanel", "FlyoutShadow", "FlyoutRow", "MarketRailRow", "StripMenuButton", "RailAnchor",
           "ChevronButton",
           "draw_chevron", "set_flag",
           "ROW_HEIGHT", "PANEL_PADDING", "PANEL_RADIUS", "SHADOW", "PANEL_GAP", "OPEN_DELAY_MS", "SWITCH_DELAY_MS",
           "CLOSE_DELAY_MS"]
