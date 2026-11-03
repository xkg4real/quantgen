"""The mouse wheel scrolls the page, not the selector under the pointer (owner UI-3).

Scrolling a page used to change combo boxes, spin boxes and tabs the pointer passed
over. Qt gives keyboard focus to a control on a wheel event when its focus policy
includes WheelFocus, so the selectors here take StrongFocus (click or Tab only) and
an unfocused selector hands the wheel to the nearest scroll area that can move.
A focused combo or spin box still changes by wheel; tabs never do.

`guard()` is applied to each widget once, by the window's LanguageController pass,
which also reaches widgets created later.
"""
from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QAbstractScrollArea, QAbstractSpinBox, QApplication, QComboBox, QTabBar

GUARDED = (QComboBox, QAbstractSpinBox, QTabBar)


def scroll_target(widget, event):
    """The nearest enclosing scroll bar that can move in the wheel's direction, or None."""
    delta = event.angleDelta()
    horizontal = abs(delta.x()) > abs(delta.y())
    step = delta.x() if horizontal else delta.y()
    if event.inverted():
        step = -step
    if not step:
        return None
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea):
            bar = parent.horizontalScrollBar() if horizontal else parent.verticalScrollBar()
            # A positive step scrolls toward the start, as QAbstractSlider does.
            if (step > 0 and bar.value() > bar.minimum()) or (step < 0 and bar.value() < bar.maximum()):
                return bar
        parent = parent.parentWidget()
    return None


class _WheelGuard(QObject):
    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.Wheel:
            return False
        if not isinstance(watched, QTabBar) and watched.hasFocus():
            return False  # the user chose this control; the wheel changes it
        bar = scroll_target(watched, event)
        if bar is not None:
            QApplication.sendEvent(bar, event)
        return True  # never change an unfocused selector, even when nothing can scroll


_FILTER = None


def guard(widget):
    """Make one selector wheel-safe. Other widgets and repeat calls are ignored."""
    global _FILTER
    if not isinstance(widget, GUARDED) or widget.property("qg_wheel_guard"):
        return
    if _FILTER is None:
        _FILTER = _WheelGuard()
    if not isinstance(widget, QTabBar):
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    widget.installEventFilter(_FILTER)
    widget.setProperty("qg_wheel_guard", True)
