"""Kalshi prediction-market probabilities for DIDM (owner answer Q4, 2026-11-18:
Kalshi instead of Polymarket). No network here.

Field names follow Kalshi's public trade-api v2 market and candlestick objects as
described in the official quick start and third-party guides (2026-11-17 search
summary; the docs host was blocked from this session) -- **unverified until the
first owner-PC call**. The parser fails loudly on a missing field instead of guessing.

Prices are in cents (0-100) = implied probability x 100. Thin markets are noisy:
each row carries volume and open interest, and ``liquid`` is set against a
pre-registered minimum (PREREG_V0, default 1,000 contracts of volume).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

SOURCE_ID = "kalshi"
MIN_VOLUME = 1_000


class KalshiError(ValueError):
    pass


def _aware(received_at: datetime) -> None:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise KalshiError("received_at must be timezone-aware")


def _ts(value: Any, name: str) -> datetime:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise KalshiError(f"{name}: bad time {value!r}") from None
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    raise KalshiError(f"{name}: missing time")


def _cents(value: Any, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100:
        raise KalshiError(f"{name}: price must be 0..100 cents, got {value!r}")
    return float(value)


def market_snapshot_rows(payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """GET /markets response -> one snapshot row per market (probability as of receipt)."""
    _aware(received_at)
    markets = payload.get("markets")
    if not isinstance(markets, list):
        raise KalshiError("payload has no markets list")
    out = []
    for m in markets:
        ticker = m.get("ticker")
        if not ticker:
            raise KalshiError("market without ticker")
        bid, ask = _cents(m.get("yes_bid"), "yes_bid"), _cents(m.get("yes_ask"), "yes_ask")
        last = _cents(m.get("last_price"), "last_price")
        mid = (bid + ask) / 2 if bid is not None and ask is not None and ask >= bid else None
        prob = mid if mid is not None else last
        volume = int(m.get("volume") or 0)
        out.append({
            "source_id": SOURCE_ID,
            "item_id": f"{ticker}@{received_at.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}",
            "kind": "kalshi_snapshot",
            "published_at": received_at,
            "received_at": received_at,
            "valid_at": received_at,
            "payload": {
                "ticker": ticker, "event_ticker": m.get("event_ticker"), "title": m.get("title"),
                "status": m.get("status"), "close_time": m.get("close_time"),
                "yes_bid": bid, "yes_ask": ask, "last_price": last,
                "p_yes": prob / 100 if prob is not None else None,
                "volume": volume, "open_interest": int(m.get("open_interest") or 0),
                "liquid": volume >= MIN_VOLUME,
            },
        })
    return out


def candlestick_rows(ticker: str, payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """GET /series/{s}/markets/{t}/candlesticks -> one row per closed period.

    ``published_at`` = the period end (the close price was public then);
    ``received_at`` = when we fetched the history.
    """
    _aware(received_at)
    candles = payload.get("candlesticks")
    if not isinstance(candles, list):
        raise KalshiError("payload has no candlesticks list")
    out = []
    for c in candles:
        end = _ts(c.get("end_period_ts"), "end_period_ts")
        price = c.get("price") or {}
        close = _cents(price.get("close"), "price.close")
        volume = int(c.get("volume") or 0)
        out.append({
            "source_id": SOURCE_ID,
            "item_id": f"{ticker}:{int(end.timestamp())}",
            "kind": "kalshi_candle",
            "published_at": end,
            "received_at": received_at,
            "valid_at": end,
            "payload": {
                "ticker": ticker, "close": close,
                "p_yes": close / 100 if close is not None else None,
                "volume": volume, "open_interest": int(c.get("open_interest") or 0),
                "liquid": volume >= MIN_VOLUME,
            },
        })
    return out
