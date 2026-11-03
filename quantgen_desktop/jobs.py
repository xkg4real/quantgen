"""Keep computation off the GUI thread; deliver all UI updates by Qt signals."""
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class JobSignals(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()


class Job(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = JobSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.function()
        except Exception as exc:
            # Provider exception messages may contain credential-bearing URLs.
            self.signals.failed.emit(type(exc).__name__)
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class Jobs(QObject):
    """One bounded calculation at a time; retain signal owners until completion."""
    busy_changed = pyqtSignal(bool)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.job = None

    @property
    def busy(self):
        return self.job is not None

    def start(self, function):
        if self.busy:
            return False
        self.job = Job(function)
        self.job.signals.succeeded.connect(self._success)
        self.job.signals.failed.connect(self._failure)
        self.job.signals.finished.connect(self._finished)
        self.busy_changed.emit(True)
        self.pool.start(self.job)
        return True

    @pyqtSlot(object)
    def _success(self, value):
        self.succeeded.emit(value)

    @pyqtSlot(str)
    def _failure(self, code):
        self.failed.emit(code)

    @pyqtSlot()
    def _finished(self):
        self.job = None
        self.busy_changed.emit(False)
