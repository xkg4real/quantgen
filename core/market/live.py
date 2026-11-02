"""Merge ordered trade events without turning a REST snapshot into fake ticks."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
import math
from zoneinfo import ZoneInfo

from .models import Candle, MarketQuote, MarketSnapshot, MarketTick


def _date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def bucket(timestamp: str, interval: str) -> str:
    at = _date(timestamp)
    if interval.endswith("m"):
        minutes = int(interval[:-1])
        at = at.replace(minute=(at.minute // minutes) * minutes, second=0, microsecond=0)
        return at.isoformat(timespec="seconds")
    day = at.date()
    if interval == "1w":
        day -= timedelta(days=day.weekday())
    elif interval == "1M":
        day = day.replace(day=1)
    return day.isoformat()


def apply_tick(snapshot: MarketSnapshot, tick: MarketTick) -> MarketSnapshot:
    """Update only the matching current candle; never fill missing time buckets.

    Accumulated session volume prevents reconnect replay from doubling volume.
    An initial REST session total is used when its observation is on the same
    market date. For adjusted history we keep bars on their REST price basis.
    """
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
