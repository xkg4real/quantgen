"""Minimal lifetime repro (did NOT reproduce the crash on 2026-11-17: both bindings ok, 30 rounds x 4 variants) for D9 group 9/10 (no app code). Run under each binding:
    python tools/qt_port/repro/delegate_lifetime.py PyQt6|PySide6 [rounds]
Each round builds a window like the watchlist (a table with a delegate created inline, parented to the
table, plus an application-wide event filter owned by the window), shows and repaints it, then disposes
it the way tests/qt_fixture_cleanup.py does (deleteLater + sendPostedEvents(DeferredDelete)) and churns
Python objects so freed memory is reused. A healthy binding prints 'ok' for every round."""
import faulthandler, gc, importlib, os, sys
faulthandler.enable()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
binding = sys.argv[1] if len(sys.argv) > 1 else "PySide6"
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 30
core = importlib.import_module(binding + ".QtCore")
widgets = importlib.import_module(binding + ".QtWidgets")
QEvent, QCoreApplication, QObject = core.QEvent, core.QCoreApplication, core.QObject
QApplication, QWidget, QTableWidget, QTableWidgetItem, QStyledItemDelegate, QVBoxLayout, QPushButton = (
    widgets.QApplication, widgets.QWidget, widgets.QTableWidget, widgets.QTableWidgetItem,
    widgets.QStyledItemDelegate, widgets.QVBoxLayout, widgets.QPushButton)
calls = {"init": 0, "filter": 0}


class Identity(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        calls["init"] += 1
        option.text = ""


class AppFilter(QObject):
    """Installed on the QApplication, parented to the window (like localization/market_menu filters)."""
    def eventFilter(self, watched, event):
        calls["filter"] += 1
        return False


class Window(QWidget):
    def __init__(self, inline_delegate=True, filter_parent=True):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(20, 3)
        for r in range(20):
            for c in range(3):
                self.table.setItem(r, c, QTableWidgetItem(f"{r},{c}"))
        if inline_delegate:
            self.table.setItemDelegateForColumn(0, Identity(self.table))   # watchlist.py form
        else:
            self.kept = Identity(self.table)                                 # reference kept on self
            self.table.setItemDelegateForColumn(0, self.kept)
        layout.addWidget(self.table)
        for i in range(5):
            b = QPushButton(f"save {i}")
            b.clicked.connect(lambda checked=False, i=i: None)               # like ReportActions
            layout.addWidget(b)
        self.filter = AppFilter(self if filter_parent else None)
        QApplication.instance().installEventFilter(self.filter)


def run(inline_delegate, filter_parent):
    app = QApplication.instance() or QApplication([])
    for n in range(rounds):
        w = Window(inline_delegate, filter_parent)
        w.resize(400, 500); w.show()
        for _ in range(5):
            app.processEvents()
        w.table.viewport().repaint()
        w.hide(); w.deleteLater()
        QCoreApplication.sendPostedEvents(w, QEvent.Type.DeferredDelete)
        del w
        junk = [lambda a=0, b=1: (a, b) for _ in range(2000)]               # reuse freed memory
        gc.collect(); del junk
    print(f"{binding} inline_delegate={inline_delegate} filter_parent={filter_parent}: ok {rounds} rounds, "
          f"initStyleOption calls={calls['init']}, filter calls={calls['filter']}", flush=True)


if __name__ == "__main__":
    for inline in (True, False):
        for parent in (True, False):
            run(inline, parent)
