"""Kalshi prediction-market probabilities for DIDM (owner answer Q4, 2026-11-18:
Kalshi instead of Polymarket). No network here.

Field names: the current API returns prices as dollar strings with four decimals
(``yes_bid_dollars`` "0.5600") and contract counts as fixed-point strings
(``volume_fp`` "10.00"); older integer fields (``yes_bid`` in cents, ``volume``) are
legacy (Kalshi Get Market reference and SDK models, 2026-11-18 search summary).
The first owner-PC run (2026-11-18) read only the legacy names, so every market got
no price and volume 0; those 200 rows stay in the append-only store without
``parser`` and are superseded by rows carrying ``parser = PARSER``.
Both forms are read; a missing volume is recorded as missing (None), never as 0.

v0.3 (integration reviews DS-7/DS-8 and DSF-2/DSF-3/DSF-10, 2026-11-24): a side quoted at bid 0 or
ask 100 cents is read as an empty side (no resting orders); whether Kalshi really writes an empty side as
0.0000 / 1.0000 is **unverified** until an owner-PC run. ``p_yes``:
* both sides quoted (and not crossed): the mid;
* one side quoted: the last price only if it respects that side (last >= bid when a bid stands, last <= ask
  when an ask stands), else None -- never pulled into range;
* no side quoted: the last price, else None.
Flags record what the response said, and say nothing when it did not report: ``book_empty`` / ``one_sided``
are None when the bid or ask field is absent (``quotes_missing`` True), so a renamed field is not stored as
"no resting orders". Tickers must fully match the client's ticker pattern (``fullmatch``, no trailing
newline); a market or candle that is not an object raises KalshiError; -0.0 is stored as 0.0.
Reading stored kalshi-v0.2 rows: they have no book_empty/one_sided/quotes_missing keys and a p_yes taken
from the mid even for 0/100 quotes; recompute p_yes from their stored yes_bid/yes_ask/last_price with the
rule above before use.

Prices are kept in cents (0-100) = implied probability x 100. Thin markets are noisy:
each row carries volume and open interest, and ``liquid`` is set against a
pre-registered minimum (PREREG_V0, default 1,000 contracts of volume).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any, Mapping

SOURCE_ID = "kalshi"
PARSER = "kalshi-v0.3"
MIN_VOLUME = 1_000
_TICKER = re.compile(r"[A-Z0-9][A-Z0-9_.\-]{0,99}")     # data/didm/kalshi.py pattern, used with fullmatch


class KalshiError(ValueError):
    pass


def _aware(received_at: datetime) -> None:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise KalshiError("received_at must be timezone-aware")


def _ticker(value: Any) -> str:
    if not isinstance(value, str) or not _TICKER.fullmatch(value):
        raise KalshiError(f"bad ticker {str(value)[:40]!r}")
    return value


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
    return float(value) + 0.0


def _price(obj: Mapping[str, Any], name: str) -> float | None:
    """Cents 0..100 from '<name>_dollars' (string dollars) or legacy '<name>' (int cents)."""
    dollars = obj.get(f"{name}_dollars")
    if dollars in (None, ""):
        return _cents(obj.get(name), name)
    try:
        # Check the original decimal before either float conversion or cent rounding.
        amount = Decimal(dollars) if isinstance(dollars, str) else dollars
        if isinstance(amount, bool) or not 0 <= amount <= 1:
            raise ValueError
        return round(float(amount) * 100, 6) + 0.0      # + 0.0 turns -0.0 into 0.0
    except (TypeError, ValueError, OverflowError, InvalidOperation):
        raise KalshiError(f"{name}_dollars: price must be 0..1 dollars") from None


def _count(obj: Mapping[str, Any], name: str) -> float | None:
    """Contracts from '<name>_fp' (fixed-point string) or legacy '<name>' (int); None if absent."""
    for key in (f"{name}_fp", name):
        raw = obj.get(key)
        if raw in (None, ""):
            continue
        if isinstance(raw, bool):
            raise KalshiError(f"{key}: boolean is not a contract count")
        try:
            value = float(raw)
            # A nonzero fixed-point string can be too small for the stored float.
            underflow = value == 0 and isinstance(raw, str) and not Decimal(raw).is_zero()
        except (TypeError, ValueError, OverflowError, InvalidOperation):
            raise KalshiError(f"{key}: invalid contract count") from None
        if not isfinite(value) or underflow:
            raise KalshiError(f"{key}: contract count cannot be represented")
        if value < 0:
            raise KalshiError(f"{key}: negative")
        return value + 0.0
    return None


def _book(bid: float | None, ask: float | None, last: float | None):
    """(p_yes in cents or None, book_empty, one_sided, quotes_missing) -- see the module docstring."""
    has_bid = bid is not None and bid > 0
    has_ask = ask is not None and ask < 100
    if has_bid and has_ask:
        prob = (bid + ask) / 2 if ask >= bid else None
    elif has_bid or has_ask:
        ok = last is not None and (not has_bid or last >= bid) and (not has_ask or last <= ask)
        prob = last if ok else None
    else:
        prob = last
    if bid is None and ask is None:
        return prob, None, None, True
    if bid is None or ask is None:
        # one field absent: a quoted side still proves the book is not empty; anything else is unknown
        return prob, (False if has_bid or has_ask else None), None, True
    return prob, not has_bid and not has_ask, has_bid != has_ask, False


def market_snapshot_rows(payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """GET /markets response -> one snapshot row per market (probability as of receipt)."""
    _aware(received_at)
    markets = payload.get("markets")
    if not isinstance(markets, list):
        raise KalshiError("payload has no markets list")
    out = []
    for m in markets:
        if not isinstance(m, Mapping):
            raise KalshiError("market is not an object")
        ticker = _ticker(m.get("ticker"))
        bid, ask = _price(m, "yes_bid"), _price(m, "yes_ask")
        last = _price(m, "last_price")
        prob, book_empty, one_sided, quotes_missing = _book(bid, ask, last)
        volume = _count(m, "volume")
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
                "book_empty": book_empty, "one_sided": one_sided, "quotes_missing": quotes_missing,
                "volume": volume, "volume_24h": _count(m, "volume_24h"),
                "open_interest": _count(m, "open_interest"),
                "liquid": volume is not None and volume >= MIN_VOLUME,
                "parser": PARSER,
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
    ticker = _ticker(ticker)
    out = []
    for c in candles:
        if not isinstance(c, Mapping) or not isinstance(c.get("price") or {}, Mapping):
            raise KalshiError("candle is not an object")
        end = _ts(c.get("end_period_ts"), "end_period_ts")
        price = c.get("price") or {}
        close = _price(price, "close")
        volume = _count(c, "volume")
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
                "volume": volume, "open_interest": _count(c, "open_interest"),
                "liquid": volume is not None and volume >= MIN_VOLUME,
                "parser": PARSER,
            },
        })
    return out
