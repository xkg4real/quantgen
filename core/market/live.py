"""Merge ordered trade events without turning a REST snapshot into fake ticks."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
import math
from zoneinfo import ZoneInfo

from .models import Candle, LIVE_INTERVALS, TICK_INTERVALS, MarketQuote, MarketSnapshot, MarketTick


def _date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def bucket(timestamp: str, interval: str) -> str:
    at = _date(timestamp)
    if interval in TICK_INTERVALS:
        return at.isoformat()
    if interval.endswith("s"):
        seconds = int(interval[:-1])
        return at.replace(second=(at.second // seconds) * seconds, microsecond=0).isoformat(timespec="seconds")
    if interval.endswith("m"):
        minutes = int(interval[:-1])
        at = at.replace(minute=(at.minute // minutes) * minutes, second=0, microsecond=0)
        return at.isoformat(timespec="seconds")
    day = at.date()
    if interval == "1w":
        day -= timedelta(days=day.weekday())
    elif interval == "1M":
        day = day.replace(day=1)
    elif interval == "1Y":
        day = day.replace(month=1, day=1)
    return day.isoformat()


def _received_bar(snapshot: MarketSnapshot, tick: MarketTick) -> MarketSnapshot:
    """Build tick/second bars solely from received, identifiable executions.

    All supported KIS execution schemas contain cumulative session volume. It
    identifies replayed frames even when separate trades share a timestamp,
    price and trade size. A missing total cannot establish that identity and
    is rejected instead of guessing. REST quotes never seed a live-only bar.
    """
    if snapshot.request.adjusted or tick.instrument != snapshot.request.instrument:
        return snapshot
    if not isinstance(tick.source, str) or not tick.source.startswith("KIS WebSocket"):
        return snapshot
    try:
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                   for v in (tick.price, tick.volume, tick.cumulative_volume)):
            return snapshot
        if tick.price <= 0 or tick.volume <= 0 or tick.cumulative_volume < tick.volume:
            return snapshot
        at = _date(tick.timestamp)
        if at.tzinfo is None:
            return snapshot
        zones = {"NAS": "America/New_York", "NYS": "America/New_York", "AMS": "America/New_York",
                 "HKS": "Asia/Hong_Kong", "TSE": "Asia/Tokyo", "SHS": "Asia/Shanghai",
                 "SZS": "Asia/Shanghai", "HSX": "Asia/Ho_Chi_Minh", "HNX": "Asia/Ho_Chi_Minh"}
        zone = ZoneInfo(zones.get(tick.instrument.exchange, "Asia/Seoul"))
        at = at.astimezone(zone)
        last_at = _date(snapshot.last_tick_at).astimezone(zone) if snapshot.last_tick_at else None
        if last_at is not None and at < last_at:
            return snapshot
        new_session = last_at is not None and last_at.date() != at.date()
        previous = None if new_session else snapshot.last_cumulative_volume
        if previous is not None and tick.cumulative_volume <= previous:
            return snapshot
        delta = tick.cumulative_volume - previous if previous is not None else None
        if delta is not None and delta < tick.volume:
            return snapshot
        gap = delta is not None and delta > tick.volume
        interval = snapshot.request.interval
        stamp = bucket(at.isoformat(), interval)
    except (ValueError, TypeError, OverflowError):
        return snapshot

    candles = list(snapshot.candles)
    is_ticks = interval in TICK_INTERVALS
    last = candles[-1] if candles else None
    if last is not None and last.sequence is None:
        # REST OHLC does not establish execution count/order for live-only bars.
        return snapshot
    partial_tick_bar = bool(is_ticks and last and (last.trade_count or 0) < int(interval[:-4]))
    same = bool(last and not new_session and (
        (partial_tick_bar and not gap) if is_ticks else last.timestamp == stamp))
    if gap and partial_tick_bar:
        candles[-1] = replace(last, volume=None)
    if same:
        candles[-1] = replace(last, high=max(last.high, tick.price), low=min(last.low, tick.price),
                             close=tick.price, trade_count=(last.trade_count or 0) + 1,
                             volume=last.volume + tick.volume if last.volume is not None and not gap else None)
    else:
        sequence = (last.sequence + 1) if last is not None else 1
        volume = None if gap and not is_ticks else tick.volume
        candles.append(Candle(stamp, tick.price, tick.price, tick.price, tick.price,
                              volume, sequence=sequence, trade_count=1))
    old_quote = snapshot.quote
    if old_quote is None:
        currencies = {"NAS": "USD", "NYS": "USD", "AMS": "USD", "HKS": "HKD", "TSE": "JPY",
                      "SHS": "CNY", "SZS": "CNY", "HSX": "VND", "HNX": "VND"}
        old_quote = MarketQuote(tick.instrument, currency=("quote units" if tick.instrument.asset == "domestic_future"
                                                         else currencies.get(tick.instrument.exchange, "KRW")))
    quote = replace(old_quote, price=tick.price, market_time=tick.timestamp,
                    received_at=tick.received_at, source=tick.source,
                    change=tick.change if tick.change is not None else old_quote.change,
                    change_pct=tick.change_pct if tick.change_pct is not None else old_quote.change_pct,
                    volume=tick.cumulative_volume)
    note = snapshot.note
    if gap and "Live gap" not in note:
        note += " Live gap: some executions were not received; affected bars are partial. No missing trades are reconstructed."
    return replace(snapshot, candles=tuple(candles[-snapshot.request.limit:]), quote=quote, note=note,
                   source=tick.source, last_tick_at=at.isoformat(), last_cumulative_volume=tick.cumulative_volume)


def apply_tick(snapshot: MarketSnapshot, tick: MarketTick) -> MarketSnapshot:
    """Update only the matching current candle; never fill missing time buckets.

    Accumulated session volume prevents reconnect replay from doubling volume.
    An initial REST session total is used when its observation is on the same
    market date. For adjusted history we keep bars on their REST price basis.
    """
    if snapshot.request.interval in LIVE_INTERVALS:
        return _received_bar(snapshot, tick)
    if tick.instrument != snapshot.request.instrument:
        return snapshot
    if not math.isfinite(tick.price) or tick.price <= 0:
        return snapshot
    try:
        at = _date(tick.timestamp)
        if at.tzinfo is None:
            return snapshot
        zones = {"NAS":"America/New_York", "NYS":"America/New_York", "AMS":"America/New_York",
                 "HKS":"Asia/Hong_Kong", "TSE":"Asia/Tokyo", "SHS":"Asia/Shanghai",
                 "SZS":"Asia/Shanghai", "HSX":"Asia/Ho_Chi_Minh", "HNX":"Asia/Ho_Chi_Minh"}
        zone = ZoneInfo(zones.get(tick.instrument.exchange, "Asia/Seoul"))
        at = at.astimezone(zone)
        if snapshot.last_tick_at and at < _date(snapshot.last_tick_at):
            return snapshot
        stamp = bucket(at.isoformat(), snapshot.request.interval)
    except (TypeError, ValueError):
        return snapshot
    previous = snapshot.last_cumulative_volume
    old_quote = snapshot.quote
    if not snapshot.last_tick_at and previous is None and old_quote and old_quote.volume is not None and old_quote.market_time:
        observed = old_quote.market_time
        try:
            if _date(observed).astimezone(at.tzinfo).date() == at.date():
                previous = old_quote.volume
        except (ValueError, TypeError):
            pass
    new_session = bool(snapshot.last_tick_at and _date(snapshot.last_tick_at).astimezone(zone).date() != at.date())
    if new_session:
        previous = None
    cumulative = tick.cumulative_volume
    if cumulative is not None and (not math.isfinite(cumulative) or cumulative < 0):
        return snapshot
    if cumulative is not None and previous is not None and cumulative <= previous:
        return snapshot
    amount = tick.volume
    if amount is not None and (not math.isfinite(amount) or amount < 0):
        return snapshot
    interval = snapshot.request.interval
    same_bucket = bool(snapshot.last_tick_at and bucket(_date(snapshot.last_tick_at).astimezone(zone).isoformat(), interval) == stamp)
    intraday = interval.endswith("m")
    if cumulative is not None and previous is not None and (same_bucket or not intraday):
        amount = cumulative - previous
    elif cumulative is not None and new_session and not intraday:
        amount = cumulative
    quote = replace(old_quote, price=tick.price, market_time=tick.timestamp,
                    received_at=tick.received_at, source=tick.source,
                    change=tick.change if tick.change is not None else old_quote.change,
                    change_pct=tick.change_pct if tick.change_pct is not None else old_quote.change_pct,
                    volume=cumulative if cumulative is not None else old_quote.volume) if old_quote else MarketQuote(
                        tick.instrument, price=tick.price, change=tick.change, change_pct=tick.change_pct,
                        volume=cumulative, market_time=tick.timestamp, received_at=tick.received_at, source=tick.source)
    candles = list(snapshot.candles)
    gap = False
    if intraday and snapshot.last_tick_at:
        last_bucket = _date(bucket(_date(snapshot.last_tick_at).astimezone(zone).isoformat(), interval))
        gap = at - last_bucket >= timedelta(minutes=int(interval[:-1]) * 2)
        if cumulative is not None and previous is not None and tick.volume is not None:
            gap = gap or cumulative - previous > tick.volume
    # Already adjusted candles cannot be mixed with raw executions.
    if not snapshot.request.adjusted:
        if candles and stamp == candles[-1].timestamp:
            c = candles[-1]
            if interval == "1d" and cumulative is not None:
                volume = cumulative
            elif (not snapshot.last_tick_at and previous is None) or gap:
                volume = None
            else:
                volume = c.volume + amount if c.volume is not None and amount is not None else None
            candles[-1] = Candle(stamp, c.open, max(c.high, tick.price), min(c.low, tick.price), tick.price,
                                 volume)
        elif not candles or stamp > candles[-1].timestamp:
            volume = (cumulative if not intraday and cumulative is not None else
                      amount if cumulative is not None and cumulative == tick.volume else
                      None if gap or not snapshot.last_tick_at else amount)
            candles.append(Candle(stamp, tick.price, tick.price, tick.price, tick.price, volume))
        else:
            return snapshot
    note = snapshot.note
    if gap and "Live gap" not in note:
        note += " Live gap: missing trades may affect OHLC and minute-bar volume. Reload history to reconcile."
    return replace(snapshot, candles=tuple(candles[-snapshot.request.limit:]), quote=quote, note=note,
                   source="KIS REST + WebSocket",
                   last_tick_at=at.isoformat(timespec="seconds"), last_cumulative_volume=cumulative)
