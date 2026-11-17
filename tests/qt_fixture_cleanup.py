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


def dispose_market_fixture(widget):
    """Stop a market fixture's producers and dispose its own window, not unrelated test windows."""
    from PyQt6.QtWidgets import QApplication
    from quantgen_desktop.jobs import Jobs
    if sip.isdeleted(widget):
        return
    for owner in (widget, *(getattr(widget, name, None) for name in (
            "market_chart", "markets_view", "home_view", "home_feed", "q_scores", "chart_scores"))):
        stop = getattr(owner, "stop", None)
        if callable(stop):
            stop()
    widget.hide()
    for jobs in widget.findChildren(Jobs):
        if not jobs.pool.waitForDone(6000):
            raise AssertionError("The owned market fixture worker did not stop")
    QApplication.processEvents()
    delete_owned_widget(widget)
