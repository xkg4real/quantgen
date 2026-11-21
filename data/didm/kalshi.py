"""Kalshi public market-data client for DIDM (owner answer Q4, 2026-11-18). Parsing: core.didm.ingest.kalshi.

Read-only public endpoints, no API key, no account, no trading. Base URL and paths
follow Kalshi's quick start as seen in a 2026-11-17 search summary (the docs host was
blocked from the cloud session): **unverified until the first owner-PC run**.
Terms and availability from Korea are not legally reviewed (not legal advice).
"""
from __future__ import annotations

import re

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


def fetch_markets(series_ticker: str, status: str = "open", limit: int = 200,
                  cursor: str | None = None) -> dict:
    params = {"series_ticker": _check(series_ticker), "status": status, "limit": int(limit)}
    if cursor:
        params["cursor"] = cursor
    return _get("/markets", params)


def fetch_all_markets(series_ticker: str, status: str = "open", max_pages: int = 20) -> dict:
    """Follow the response cursor; returns {"markets": [...], "pages": n, "complete": bool}."""
    markets, cursor = [], None
    for page in range(1, max_pages + 1):
        payload = fetch_markets(series_ticker, status, cursor=cursor)
        markets += payload.get("markets") or []
        cursor = payload.get("cursor")
        if not cursor:
            return {"markets": markets, "pages": page, "complete": True}
    return {"markets": markets, "pages": max_pages, "complete": False}


def fetch_candlesticks(series_ticker: str, ticker: str, start_ts: int, end_ts: int,
                       period_interval: int = 1440) -> dict:
    if period_interval not in (1, 60, 1440):
        raise ValueError("period_interval must be 1, 60 or 1440 minutes")
    return _get(f"/series/{_check(series_ticker)}/markets/{_check(ticker)}/candlesticks",
                {"start_ts": int(start_ts), "end_ts": int(end_ts), "period_interval": period_interval})
