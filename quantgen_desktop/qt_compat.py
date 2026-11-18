"""Small helpers that behave the same in PyQt6 and PySide6 (docs/platform/PYSIDE6_UI_CHECKLIST.md on the OS branch).

Deferred calls that never outlive their object (checklist item 6):
`QTimer.singleShot(ms, self.method)` behaves differently in the two bindings: PyQt6 drops the call once `self` is
deleted, PySide6 still makes it, and the method then touches a deleted object (PySide6 trial 2026-11-17,
docs/platform/PYSIDE6_UI_CHECKLIST.md item 6: segfaults and a memory blow-up). PySide6's
`singleShot(ms, context, fn)` would fix it but does not exist in PyQt6. Here the call belongs to a child of the
object, so it is deleted with it in both bindings and can no longer arrive late.
"""
from PyQt6.QtCore import QCoreApplication, QEvent, QObject, Qt, QTimer

_CALL = QEvent.Type(QEvent.registerEventType())


class _Deferred(QObject):
    """A one-shot call posted as an event to this child of the owner. Qt drops events posted to an object that is
    deleted, so the call never runs after the owner is gone. A posted event keeps the place of Qt 6's
    `singleShot(0, ...)` (a queued call at normal priority, ahead of the low-priority repaint); a zero QTimer would
    run only after the repaint on Linux and show one frame of the old state."""

    def __init__(self, owner, fn):
        super().__init__(owner)
        self._fn = fn

    def event(self, event):
        if event.type() == _CALL:
            self.deleteLater()
            self._fn()
            return True
        return super().event(event)


def call_later(owner, ms, fn):
    """Call `fn` once after `ms` milliseconds unless `owner` (a QObject) is deleted first.

    Like `QTimer.singleShot`, every call queues its own call (two calls, two runs). With `ms` 0 the call is posted
    like singleShot(0); otherwise a single-shot child timer of `owner` (precise below 2 s, as singleShot's) runs it
    and deletes itself."""
    if ms <= 0:
        call = _Deferred(owner, fn)
        QCoreApplication.postEvent(call, QEvent(_CALL))
        return call
    timer = QTimer(owner)
    timer.setSingleShot(True)
    timer.setTimerType(Qt.TimerType.PreciseTimer if ms < 2000 else Qt.TimerType.CoarseTimer)
    timer.timeout.connect(fn)
    timer.timeout.connect(timer.deleteLater)
    timer.start(ms)
    return timer


def is_one_of(obj, items):
    """`obj in items` by identity (checklist item 5). An event filter sees every kind of Qt object, and PySide6
    cannot hash some of them (QPointingDevice, ...), so `watched in some_set` or `some_dict.get(watched)` raises
    there; comparing with `is` never hashes."""
    return any(obj is item for item in items)


def lookup(mapping, obj, default=None):
    """`mapping.get(obj, default)` by identity, for a dict keyed by Qt objects (checklist item 5)."""
    for key, value in mapping.items():
        if key is obj:
            return value
    return default


def index_of(items, obj):
    """`items.index(obj)` by identity."""
    for index, item in enumerate(items):
        if item is obj:
            return index
    raise ValueError("not in the list")
