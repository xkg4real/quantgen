"""Explicit, read-only home watchlist updates on one bounded KIS connection.

History retrieval and stream callbacks run outside the GUI thread. Signals are
generation tagged so stopping or changing pages cannot publish late results.
No historical candle is manufactured from a quote; adjusted daily history is
provided separately for Q-SCORE, while real executions retain their own times.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
import threading
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

from core.market.models import ChartRequest, Instrument, MarketSnapshot, MarketTick
from core.research.watchlist import KR_STOCK_SPECS


class _Bridge(QObject):
    history = pyqtSignal(int, str, object)
    history_error = pyqtSignal(int, str, str)
    loaded = pyqtSignal(int)
    tick = pyqtSignal(int, object)
    status = pyqtSignal(int, str)


class WatchlistLiveController(QObject):
    """One explicit session for the six home stocks, stopped when Home is hidden.

    ``history_ready`` carries adjusted daily data, not a live candle chart.
    ``tick_received`` emits only fresh, ordered, deduplicated real executions.
    A reconnect gap invalidates this session until the user restarts it.
    """
    history_ready = pyqtSignal(str, object)
    history_failed = pyqtSignal(str, str)
    tick_received = pyqtSignal(object)
    state_changed = pyqtSignal(str)

    def __init__(self, parent=None, *, service=None, stream_factory=None,
                 instruments=None, now=None):
        super().__init__(parent)
        if service is None:
            from data.kis_workspace import MarketDataService
            service = MarketDataService()
        if stream_factory is None:
            from data.kis_stream import KISStream
            stream_factory = lambda: KISStream(service.client)
        self.service, self.stream_factory = service, stream_factory
        self.instruments = tuple(instruments if instruments is not None else
                                 (Instrument(code=code) for _, code, _ in KR_STOCK_SPECS))
        if (not 1 <= len(self.instruments) <= 6
                or any(not isinstance(i, Instrument) or i.asset != "domestic_stock"
                       for i in self.instruments)
                or len(set(self.instruments)) != len(self.instruments)):
            raise ValueError("Use one to six unique domestic stocks")
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._epoch = 0
        self._active = False
        self._gap = False
        self._state = "idle"
        self._stream = None
        self._worker = None
        self._cancel = threading.Event()
        self._seen = {}
        self._last_received = None
        self.bridge = _Bridge(self)
        self.bridge.history.connect(self._history)
        self.bridge.history_error.connect(self._history_error)
        self.bridge.loaded.connect(self._loaded)
        self.bridge.tick.connect(self._tick)
        self.bridge.status.connect(self._status)
        self.age_timer = QTimer(self)
        self.age_timer.setInterval(1000)
        self.age_timer.timeout.connect(self._age)

    @property
    def active(self):
        return self._active

    @property
    def busy(self):
        return bool(self._worker and self._worker.is_alive())

    @property
    def state(self):
        return self._state

    def _set_state(self, state):
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)

    def start(self):
        if self._active or self.busy:
            return False
        self.stop()
        if not self.service.ready:
            for instrument in self.instruments:
                self.history_failed.emit(instrument.symbol, "KISUnavailable")
            self._set_state("error")
            return False
        self._active = True
        self._gap = False
        self._seen.clear()
        self._last_received = None
        epoch = self._epoch
        cancel = self._cancel = threading.Event()
        self._set_state("loading")
        self.age_timer.start()

        def load():
            for instrument in self.instruments:
                if cancel.is_set():
                    return
                try:
                    request = ChartRequest(instrument, "1d", 252, adjusted=True)
                    snapshot = self.service.load(request)
                    if not isinstance(snapshot, MarketSnapshot) or snapshot.request != request:
                        raise ValueError("Mismatched watchlist history")
                except Exception as exc:
                    if not cancel.is_set():
                        self._emit(self.bridge.history_error, epoch, instrument.symbol, type(exc).__name__)
                else:
                    if not cancel.is_set():
                        self._emit(self.bridge.history, epoch, instrument.symbol, snapshot)
            if not cancel.is_set():
                self._emit(self.bridge.loaded, epoch)

        # An in-flight REST request has its provider timeout. Cancellation stops
        # subsequent instruments; a daemon avoids blocking application shutdown.
        self._worker = threading.Thread(target=load, name="qg-watchlist-history", daemon=True)
        self._worker.start()
        return True

    @staticmethod
    def _emit(signal, *args):
        try:
            signal.emit(*args)
        except RuntimeError:
            pass  # The window was destroyed while a timed request completed.

    @pyqtSlot(int, str, object)
    def _history(self, epoch, symbol, snapshot):
        if epoch == self._epoch and self._active:
            self.history_ready.emit(symbol, snapshot)

    @pyqtSlot(int, str, str)
    def _history_error(self, epoch, symbol, code):
        if epoch == self._epoch and self._active:
            self.history_failed.emit(symbol, code)

    @pyqtSlot(int)
    def _loaded(self, epoch):
        if epoch != self._epoch or not self._active:
            return
        self._set_state("connecting")
        try:
            self._stream = self.stream_factory()
            self._stream.start_many(self.instruments,
                lambda tick: self._emit(self.bridge.tick, epoch, tick),
                lambda status: self._emit(self.bridge.status, epoch, str(status)))
        except Exception:
            self.stop()
            self._set_state("error")

    @pyqtSlot(int, object)
    def _tick(self, epoch, tick):
        if epoch != self._epoch or not self._active or self._gap:
            return
        if not isinstance(tick, MarketTick) or tick.instrument not in self.instruments:
            return
        try:
            observed = datetime.fromisoformat(tick.timestamp.replace("Z", "+00:00"))
            received = datetime.fromisoformat(tick.received_at.replace("Z", "+00:00"))
            now = self._now()
            if any(at.tzinfo is None for at in (observed, received, now)):
                return
            if (not -5 <= (now - observed).total_seconds() <= 60
                    or not -5 <= (now - received).total_seconds() <= 60
                    or (received - observed).total_seconds() < -5):
                self._set_state("stale")
                return
            numbers = (tick.price, tick.volume, tick.cumulative_volume)
            if (any(isinstance(v, bool) or v is None or not math.isfinite(v) for v in numbers)
                    or tick.price <= 0 or tick.volume < 0 or tick.cumulative_volume < 0
                    or any(v is not None and (isinstance(v, bool) or not math.isfinite(v))
                           for v in (tick.change, tick.change_pct))):
                return
            if tick.source != "KIS WebSocket":
                return
            previous = self._seen.get(tick.instrument.symbol)
            if previous:
                last_at, last_volume = previous
                if observed < last_at:
                    return
                zone = ZoneInfo("Asia/Seoul")
                if (observed.astimezone(zone).date() == last_at.astimezone(zone).date()
                        and tick.cumulative_volume <= last_volume):
                    return
        except (AttributeError, TypeError, ValueError, OverflowError):
            return
        self._seen[tick.instrument.symbol] = (observed, tick.cumulative_volume)
        self._last_received = received
        self._set_state("streaming")
        self.tick_received.emit(tick)

    @pyqtSlot(int, str)
    def _status(self, epoch, status):
        if epoch != self._epoch or not self._active:
            return
        if status.startswith("ERROR"):
            self.stop()
            self._set_state("error")
        elif status == "STOPPED":
            self.stop()
        elif status == "RECONNECTING":
            self._gap = True
            self._set_state("stale")
        elif self._gap:
            self._set_state("stale")
        elif status == "SUBSCRIBED" and self._last_received is None:
            self._set_state("subscribed")
        elif status == "CONNECTING":
            self._set_state("connecting")
        # LIVE is not evidence until _tick validates a fresh execution.

    def _age(self):
        if self._active and self._last_received and self._state == "streaming":
            if (self._now() - self._last_received).total_seconds() > 15:
                self._set_state("stale")

    def stop(self):
        self._epoch += 1
        self._active = False
        self._cancel.set()
        self.age_timer.stop()
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
        self._set_state("stopped")

    def close(self):
        self.stop()
        return not self.busy
