"""Serial score worker with cancellation and per-instrument cache; no calls from paint/render."""
from datetime import datetime, timezone
import threading
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from core.market.qscore_rankings import ScoreCache, FAILURE_RETRY_SECONDS
from .jobs import Jobs


class RankingScores(QObject):
    changed = pyqtSignal()

    def __init__(self, parent=None, *, load=None):
        super().__init__(parent)
        self.cache = ScoreCache(load)
        self.results = {}
        self._cancel = threading.Event()
        self._request = None
        self._last = None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._done)
        self.jobs.busy_changed.connect(lambda busy: self.changed.emit() if not busy else None)

    def ensure(self, group, records, now):
        key = (group, now.date(), tuple(r.member.code for r in records))
        if self.jobs.busy or not records or (self._last and self._last[0] == key and
                (now - self._last[1]).total_seconds() < FAILURE_RETRY_SECONDS):
            return
        self._cancel = cancel = threading.Event()
        self._last = key, now
        self.jobs.start(lambda: self.cache.run(records, cancel.is_set, now))

    def _done(self, results):
        self.results.update(results)
        self.changed.emit()

    def stop(self):
        self._cancel.set()
        self._last = None

    def result(self, instrument, now):
        key = (instrument.asset, instrument.exchange, instrument.code)
        cached = self.cache.entries.get(key)
        if cached:
            from zoneinfo import ZoneInfo
            zone = 'America/New_York' if instrument.asset == 'overseas_stock' else 'Asia/Seoul'
            if cached[0] == now.astimezone(ZoneInfo(zone)).date():
                return self.results.get(key)
        return None
