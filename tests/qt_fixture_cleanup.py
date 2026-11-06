"""Dispose only a test fixture's owned widget before QApplication finalization."""
from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent


def delete_owned_widget(widget):
    """processEvents alone does not deliver DeferredDelete outside app.exec()."""
    # A chart can register this cleanup for multiple paint passes.
    if sip.isdeleted(widget):
        return
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(widget, QEvent.Type.DeferredDelete)
    if not sip.isdeleted(widget):
        raise AssertionError("The owned Qt fixture survived DeferredDelete cleanup")
