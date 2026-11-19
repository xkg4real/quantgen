"""Alpha Vantage NEWS_SENTIMENT client for DIDM (DS-4b, free key, 25 requests a day). Parsing: core.didm.ingest.news.

ALPHAVANTAGE_API_KEY via data.didm.keys. The key is a query parameter, so URLs are never logged.
"""
from __future__ import annotations

import re

from data.didm.keys import require
from data.net import session

KEY_NAME = "ALPHAVANTAGE_API_KEY"
URL = "https://www.alphavantage.co/query"
TIMEOUT_SECONDS = 30
_TICKER = re.compile(r"^[A-Z0-9:._\-]{1,20}$")


def fetch_news(tickers: list[str] | None = None, topics: list[str] | None = None, limit: int = 50) -> dict:
    params = {"function": "NEWS_SENTIMENT", "limit": int(limit), "apikey": require(KEY_NAME)}
    if tickers:
        if not all(_TICKER.match(t) for t in tickers):
            raise ValueError("bad ticker")
        params["tickers"] = ",".join(tickers)
    if topics:
        params["topics"] = ",".join(topics)
    resp = session.get(URL, params=params, timeout=TIMEOUT_SECONDS)
    if resp.status_code != 200:
        raise RuntimeError(f"Alpha Vantage NEWS_SENTIMENT: HTTP {resp.status_code}")
    return resp.json()
