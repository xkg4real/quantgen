"""Kalshi public market-data client for DIDM (owner answer Q4, 2026-11-18). Parsing: core.didm.ingest.kalshi.

Read-only public endpoints, no API key, no account, no trading. Base URL and paths
follow Kalshi's quick start as seen in a 2026-11-17 search summary (the docs host was
blocked from the cloud session): **unverified until the first owner-PC run**.
Terms and availability from Korea are not legally reviewed (not legal advice).
"""
from __future__ import annotations

import re
from collections.abc import Mapping

from data.didm.keys import SourceError
from data.net import session

BASE = "https://external-api.kalshi.com/trade-api/v2"
TIMEOUT_SECONDS = 30
_TICKER = re.compile(r"^[A-Z0-9][A-Z0-9_.\-]{0,99}$")


def _check(ticker: str) -> str:
    if not _TICKER.match(ticker or ""):
        raise ValueError(f"bad Kalshi ticker {ticker!r}")
    return ticker


def _get(path: str, params: dict | None = None) -> dict:
    resp = session.get(f"{BASE}{path}", params=params or {}, timeout=TIMEOUT_SECONDS)
    if resp.status_code != 200:
        raise SourceError(f"Kalshi {path.split('?')[0]}: HTTP {resp.status_code}")
    return resp.json()


STATUSES = ("open", "closed", "settled")


def fetch_markets(series_ticker: str, status: str = "open", limit: int = 200,
                  cursor: str | None = None, *, min_close_ts: int | None = None,
                  max_close_ts: int | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    params = {"series_ticker": _check(series_ticker), "status": status, "limit": int(limit)}
    if cursor:
        params["cursor"] = cursor
    if min_close_ts is not None:
        params["min_close_ts"] = int(min_close_ts)
    if max_close_ts is not None:
        params["max_close_ts"] = int(max_close_ts)
    return _get("/markets", params)


def fetch_all_markets(series_ticker: str, status: str = "open", max_pages: int = 20, *,
                      min_close_ts: int | None = None, max_close_ts: int | None = None) -> dict:
    """Follow the response cursor; returns {"markets": [...], "pages": n, "complete": bool}.
    D7: closed/settled markets and a close-time window for history (same cursor checks)."""
    markets, cursor = [], None
    seen_cursors = set()
    window = {k: v for k, v in (("min_close_ts", min_close_ts), ("max_close_ts", max_close_ts)) if v is not None}
    for page in range(1, max_pages + 1):
        payload = fetch_markets(series_ticker, status, cursor=cursor, **window)
        if not isinstance(payload, Mapping) or not isinstance(payload.get("markets"), list):
            raise SourceError("Kalshi /markets: expected a markets list")
        batch = payload["markets"]
        if any(not isinstance(market, Mapping) for market in batch):
            raise SourceError("Kalshi /markets: expected market objects")
        markets.extend(batch)
        cursor = payload.get("cursor")
        if cursor is None or cursor == "":
            return {"markets": markets, "pages": page, "complete": True}
        if not isinstance(cursor, str):
            raise SourceError("Kalshi /markets: cursor must be a string")
        if cursor in seen_cursors:
            raise SourceError("Kalshi /markets: repeated cursor")
        seen_cursors.add(cursor)
    return {"markets": markets, "pages": max_pages, "complete": False}


def fetch_candlesticks(series_ticker: str, ticker: str, start_ts: int, end_ts: int,
                       period_interval: int = 1440) -> dict:
    if period_interval not in (1, 60, 1440):
        raise ValueError("period_interval must be 1, 60 or 1440 minutes")
    return _get(f"/series/{_check(series_ticker)}/markets/{_check(ticker)}/candlesticks",
                {"start_ts": int(start_ts), "end_ts": int(end_ts), "period_interval": period_interval})
