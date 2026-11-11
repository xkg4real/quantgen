"""Left rail chrome: the hide/show toggle, the Markets sub-menu and keyboard moves (owner 2026-11-11, UI-D7).

Owner points 2 and 3: clicking Markets shows sub-items to pick what to look at (the real-time chart
categories and stock search), and the rail can be hidden to give the page the full width. The window
(`app.ResearchWindow`) owns the state; this module holds the pieces that do not need the window:
the section list, the painted toggle icons and the rail's arrow-key handling.
"""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QPushButton, QScrollArea

# The Markets page's real-time chart categories (interface contract: markets_view.RANKING_CATEGORIES).
# Used only until that constant exists; the Korean display text is in owner_ui_language/common.py.
FALLBACK_CATEGORIES = (("value", "Trading value"), ("volume", "Volume"), ("gainers", "Top gainers"),
                       ("losers", "Top losers"), ("cap", "Market cap"))
SEARCH_SECTION = ("search", "Stock search")
SETTINGS_KEY = "ui/sidebar_collapsed"


def market_sections():
    """(key, English title) for each Markets sub-item: the five categories, then stock search."""
    try:
        from .markets_view import RANKING_CATEGORIES as categories
    except ImportError:
        categories = FALLBACK_CATEGORIES
    return tuple((row[0], row[1]) for row in categories) + (SEARCH_SECTION,)


def stored_flag(store, key=SETTINGS_KEY):
    """A remembered yes/no from a QSettings-like store; anything unreadable means no."""
    reader = getattr(store, "value", None)
    if not callable(reader):
        return False
    try:
        value = reader(key, False)
    except (TypeError, ValueError):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def _pixmaps(size, paint):
    icon = QIcon()
    for scale in (1, 2):
        pixmap = QPixmap(size * scale, size * scale)
        pixmap.setDevicePixelRatio(scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def toggle_icon(color, *, rail_open, size=18):
    """A panel outline with the rail column on the left and a chevron toward where the rail goes.

    Open rail: the column is shaded and the chevron points left (hide). Hidden rail: an empty column
    and a chevron pointing right (show). Painted, so no glyph or asset file is needed.
    """
    stroke = QColor(color)

    def paint(painter):
        pen = QPen(stroke, 1.4)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        frame = QRectF(1.7, 2.7, size - 3.4, size - 5.4)
        divider = frame.left() + 5.2
        if rail_open:
            shade = QColor(stroke)
            shade.setAlphaF(0.28)
            column = QPainterPath()
            column.addRoundedRect(QRectF(frame.left(), frame.top(), divider - frame.left(), frame.height()), 2.6, 2.6)
            painter.fillPath(column, shade)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(frame, 2.6, 2.6)
        painter.drawLine(QPointF(divider, frame.top()), QPointF(divider, frame.bottom()))
        middle_x = (divider + frame.right()) / 2
        middle_y = frame.center().y()
        reach = 1.9 if rail_open else -1.9
        chevron = QPainterPath(QPointF(middle_x + reach, middle_y - 3.2))
        chevron.lineTo(QPointF(middle_x - reach, middle_y))
        chevron.lineTo(QPointF(middle_x + reach, middle_y + 3.2))
        painter.drawPath(chevron)

    return _pixmaps(size, paint)


def stop_icon(color, size=16):
    """A filled rounded square: the paper engine's emergency stop in the hidden rail."""
    fill = QColor(color)

    def paint(painter):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        inset = size * 0.24
        painter.drawRoundedRect(QRectF(inset, inset, size - 2 * inset, size - 2 * inset), 2.2, 2.2)

    return _pixmaps(size, paint)


def icon_button(accessible_name, tooltip, size):
    """A square, text-free rail button (styled by QPushButton[railIcon='true'] in typography)."""
    button = QPushButton()
    button.setProperty("railIcon", True)
    button.setFixedSize(size, size)
    button.setAccessibleName(accessible_name)
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


KEYBOARD_FOCUS = (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
                  Qt.FocusReason.ShortcutFocusReason)


def set_focus_ring(button, shown):
    """The `focusRing` property the rail styles use instead of :focus (Qt has no :focus-visible)."""
    shown = bool(shown)
    if bool(button.property("focusRing")) == shown:
        return
    button.setProperty("focusRing", shown)
    style = button.style()
    style.unpolish(button)
    style.polish(button)
    button.update()


class RailKeys(QObject):
    """Up/Down (Home/End) move between the rail's visible buttons; Return/Enter press the focused one.

    The focus ring follows keyboard focus only: Tab, Backtab and these arrow moves show it; a mouse
    click or the window gaining focus does not, so no ring lingers on a clicked menu item.
    """

    def __init__(self, buttons, parent=None):
        super().__init__(parent)
        self.buttons = buttons  # callable returning the rail's buttons in visual order

    def watch(self, button):
        button.installEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Type.FocusIn:
            set_focus_ring(watched, event.reason() in KEYBOARD_FOCUS)
            scroll = watched.parentWidget()
            while scroll is not None and not isinstance(scroll, QScrollArea):
                scroll = scroll.parentWidget()
            if scroll is not None:  # a short window scrolls the rail; keep the focused item in view
                scroll.ensureWidgetVisible(watched, 0, 6)
            return False
        if kind == QEvent.Type.FocusOut:
            set_focus_ring(watched, False)
            return False
        if kind != QEvent.Type.KeyPress:
            return False
        if event.modifiers() not in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.KeypadModifier):
            return False
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            watched.click()
            return True
        if key not in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
            return False
        shown = [b for b in self.buttons() if b.isVisible() and b.isEnabled()]
        if watched not in shown:
            return False
        index = shown.index(watched)
        target = {Qt.Key.Key_Up: index - 1, Qt.Key.Key_Down: index + 1,
                  Qt.Key.Key_Home: 0, Qt.Key.Key_End: len(shown) - 1}[key]
        shown[max(0, min(len(shown) - 1, target))].setFocus(Qt.FocusReason.TabFocusReason)
        return True


__all__ = ["FALLBACK_CATEGORIES", "SEARCH_SECTION", "SETTINGS_KEY", "KEYBOARD_FOCUS", "market_sections",
           "stored_flag", "toggle_icon", "stop_icon", "icon_button", "set_focus_ring", "RailKeys"]
