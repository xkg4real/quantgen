"""Bounded native orchestration for the experimental, read-only Q-SCORE.

Adjusted history stays separate from raw live-chart candles. Network requests
run in Jobs; ordered executions are coalesced on the Qt thread once a second.
Nothing here writes research ledgers, executes orders or manufactures ticks.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import date, datetime, timezone
import math
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal, pyqtSlot

from core.market.models import ChartRequest, Instrument, MarketSnapshot, MarketTick
from core.research.qscore import compute_q_score
from .jobs import Jobs


_KST = ZoneInfo("Asia/Seoul")
_ACTIVE_STATES = {"connecting", "connected", "subscribed", "streaming", "live"}
_STATES = _ACTIVE_STATES | {"idle", "loading", "snapshot", "polling", "stale", "stopped", "error"}


def _instant(value):
    stamp = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Timezone required")
    return stamp.astimezone(timezone.utc)


def _history_day(value):
    text = str(value)
    return date.fromisoformat(text) if len(text) == 10 else _instant(text).astimezone(_KST).date()


class QScoreController(QObject):
    """One bounded REST worker and a maximum of 16 in-memory stock histories.

    Use separate instances for independently stopped Home and chart feeds.
    ``set_history`` accepts Home's authoritative adjusted daily snapshots;
    ``request_history`` selects one chart instrument and obtains its own basis.
    """
    score_changed = pyqtSignal(str, object)

    def __init__(self, parent=None, *, service=None, now=None):
        super().__init__(parent)
        if service is None:
            from data.kis_workspace import MarketDataService
            service = MarketDataService()
        self.service = service
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._histories = OrderedDict()
        self._scores = OrderedDict()
        self._pending_ticks = {}
        self._seen = {}
        self._last_scored = {}
        self._selected_symbol = None
        self._epoch = 0
        self._wanted_request = None
        self._running_request = None
        self._feed_state = "idle"
        self._stopped = False
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy_changed)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._flush_ticks)

    def scores(self):
        return deepcopy(self._scores)

    def _publish(self, symbol, score):
        result = deepcopy(score)
        result["feed_state"] = self._feed_state
        if self._feed_state not in _ACTIVE_STATES:
            result["live"] = False
        self._scores[symbol] = result
        self._scores.move_to_end(symbol)
        self._trim()
        self.score_changed.emit(symbol, deepcopy(result))

    def _freeze(self):
        for symbol, score in tuple(self._scores.items()):
            frozen = dict(score, live=False, feed_state=self._feed_state)
            if frozen != score:
                self._publish(symbol, frozen)

    def _trim(self):
        while len(self._histories) > 16:
            symbol, _ = self._histories.popitem(last=False)
            for cache in (self._scores, self._pending_ticks, self._seen, self._last_scored):
                cache.pop(symbol, None)
        while len(self._scores) > 16:
            symbol, _ = self._scores.popitem(last=False)
            for cache in (self._histories, self._pending_ticks, self._seen, self._last_scored):
                cache.pop(symbol, None)

    @pyqtSlot(str, object)
    def set_history(self, symbol, snapshot):
        if (self._stopped or not isinstance(snapshot, MarketSnapshot)
                or not isinstance(snapshot.request, ChartRequest)
                or not isinstance(snapshot.source, str)):
            return False
        instrument = snapshot.request.instrument
        if (instrument.asset != "domestic_stock" or instrument.symbol != symbol
                or snapshot.request.interval != "1d" or not snapshot.request.adjusted
                or snapshot.source not in {"KIS", "KIS REST"}):
            return False
        try:
            now = _instant(self._now())
            fetched = _instant(snapshot.fetched_at) if snapshot.fetched_at else None
            if fetched and (fetched - now).total_seconds() > 5:
                return False
            previous = self._histories.get(symbol)
            previous_fetched = _instant(previous.fetched_at) if previous and previous.fetched_at else None
            if previous_fetched and (fetched is None or fetched < previous_fetched):
                return False
            if previous and previous.candles and snapshot.candles:
                if _history_day(snapshot.candles[-1].timestamp) < _history_day(previous.candles[-1].timestamp):
                    return False
        except (AttributeError, TypeError, ValueError, OverflowError):
            return False
        self._histories[symbol] = snapshot
        self._histories.move_to_end(symbol)
        self._trim()
        current = self._scores.get(symbol)
        last_tick = self._seen.get(symbol)
        # A background history callback must not overwrite a newer valid trade
        # with a daily close. Re-evaluate that trade against the new basis later.
        if current and current.get("live") and last_tick:
            if 0 <= (now - _instant(last_tick.timestamp)).total_seconds() <= 120:
                self._pending_ticks[symbol] = last_tick
                self._start_timer()
                return True
        score = compute_q_score(snapshot, now=now)
        self._publish(symbol, score)
        return True

    def _fresh_history(self, symbol):
        snapshot = self._histories.get(symbol)
        if snapshot is None or not snapshot.fetched_at:
            return False
        try:
            fetched, now = _instant(snapshot.fetched_at), _instant(self._now())
            return fetched <= now and fetched.astimezone(_KST).date() == now.astimezone(_KST).date()
        except (TypeError, ValueError, OverflowError):
            return False

    def request_history(self, instrument):
        if not isinstance(instrument, Instrument) or instrument.asset != "domestic_stock":
            self.stop()
            self._selected_symbol = None
            return False
        symbol = instrument.symbol
        if self._selected_symbol != symbol:
            self._epoch += 1
            self._wanted_request = None
            self._pending_ticks.clear()
            self._freeze()
            self._selected_symbol = symbol
        self._stopped = False
        if self._fresh_history(symbol):
            self._histories.move_to_end(symbol)
            return True
        if not bool(getattr(self.service, "ready", True)):
            score = compute_q_score(None, now=self._now(), symbol=symbol)
            score["reason"] = "connection_not_configured"
            self._publish(symbol, score)
            return False
        request = ChartRequest(instrument, "1d", 252, adjusted=True)
        candidate = (self._epoch, request)
        if candidate == self._running_request or candidate == self._wanted_request:
            return True
        self._wanted_request = candidate
        self._launch_pending()
        return True

    def _launch_pending(self):
        if self._stopped or self.jobs.busy or self._wanted_request is None:
            return
        epoch, request = self._wanted_request
        self._wanted_request = None
        self._running_request = (epoch, request)
        service = self.service

        def load():
            return epoch, request, service.load(request)

        self.jobs.start(load)

    @pyqtSlot(object)
    def _loaded(self, payload):
        epoch, request, snapshot = payload
        if (self._stopped or epoch != self._epoch
                or request.instrument.symbol != self._selected_symbol):
            return
        if not isinstance(snapshot, MarketSnapshot) or snapshot.request != request:
            self._failed("InvalidHistory")
            return
        self.set_history(request.instrument.symbol, snapshot)

    @pyqtSlot(str)
    def _failed(self, _code):
        if self._stopped or self._running_request is None:
            return
        epoch, request = self._running_request
        symbol = request.instrument.symbol
        if epoch != self._epoch or symbol != self._selected_symbol:
            return
        score = compute_q_score(None, now=self._now(), symbol=symbol)
        score["reason"] = "history_unavailable"
        self._publish(symbol, score)

    @pyqtSlot(bool)
    def _busy_changed(self, busy):
        if not busy:
            self._running_request = None
            self._launch_pending()

    @pyqtSlot(object)
    def accept_tick(self, tick):
        if self._stopped or self._feed_state not in _ACTIVE_STATES or not isinstance(tick, MarketTick):
            return False
        instrument = tick.instrument
        if (not isinstance(instrument, Instrument) or instrument.asset != "domestic_stock"
                or tick.source != "KIS WebSocket"
                or (self._selected_symbol is not None and instrument.symbol != self._selected_symbol)
                or (instrument.symbol not in self._histories and instrument.symbol != self._selected_symbol)):
            return False
        try:
            observed, received, now = _instant(tick.timestamp), _instant(tick.received_at), _instant(self._now())
            if (not -5 <= (now - observed).total_seconds() <= 120
                    or not -5 <= (now - received).total_seconds() <= 120
                    or (received - observed).total_seconds() < -5):
                return False
            numbers = (tick.price, tick.volume, tick.cumulative_volume)
            if (any(value is None or isinstance(value, bool) or not math.isfinite(value) for value in numbers)
                    or tick.price <= 0 or tick.volume < 0 or tick.cumulative_volume < 0
                    or any(value is not None and (isinstance(value, bool) or not math.isfinite(value))
                           for value in (tick.change, tick.change_pct))):
                return False
            previous = self._seen.get(instrument.symbol)
            if previous:
                previous_at = _instant(previous.timestamp)
                if observed < previous_at:
                    return False
                if (observed.astimezone(_KST).date() == previous_at.astimezone(_KST).date()
                        and tick.cumulative_volume <= previous.cumulative_volume):
                    return False
        except (AttributeError, TypeError, ValueError, OverflowError):
            return False
        self._seen[instrument.symbol] = tick
        self._pending_ticks[instrument.symbol] = tick
        self._start_timer()
        return True

    def _start_timer(self):
        if not self.timer.isActive():
            self.timer.start()

    @pyqtSlot()
    def _flush_ticks(self):
        if self._stopped or self._feed_state not in _ACTIVE_STATES:
            self._pending_ticks.clear()
            self.timer.stop()
            return
        now = _instant(self._now())
        for symbol, tick in tuple(self._pending_ticks.items()):
            snapshot = self._histories.get(symbol)
            if snapshot is None:
                if (now - _instant(tick.timestamp)).total_seconds() > 120:
                    self._pending_ticks.pop(symbol, None)
                continue
            self._pending_ticks.pop(symbol, None)
            result = compute_q_score(snapshot, latest_price=tick.price, as_of=tick.timestamp,
                                     previous_as_of=self._last_scored.get(symbol), now=now)
            if result.get("status") == "ready":
                self._last_scored[symbol] = result["as_of"]
            self._publish(symbol, result)
        for symbol, score in tuple(self._scores.items()):
            if score.get("live") and (now - _instant(score["as_of"])).total_seconds() > 120:
                frozen = dict(score, live=False, feed_state="stale")
                self._scores[symbol] = frozen
                self.score_changed.emit(symbol, deepcopy(frozen))
        if not self._pending_ticks and not any(score.get("live") for score in self._scores.values()):
            self.timer.stop()

    @pyqtSlot(str)
    def set_feed_state(self, state):
        state = str(state).lower()
        if state not in _STATES:
            state = "error"
        if state == "stopped":
            self.stop()
            return
        self._feed_state = state
        self._stopped = False
        if state not in _ACTIVE_STATES:
            self._pending_ticks.clear()
            self.timer.stop()
            self._freeze()
        else:
            for symbol, score in tuple(self._scores.items()):
                self._publish(symbol, score)

    def stop(self):
        self._epoch += 1
        self._stopped = True
        self._feed_state = "stopped"
        self._selected_symbol = None
        self._wanted_request = None
        self._pending_ticks.clear()
        self.timer.stop()
        self._freeze()

    def close(self):
        self.stop()
        return not self.jobs.busy
