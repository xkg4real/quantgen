"""Tiingo News client for DIDM (DS-4b). Parsing: core.didm.ingest.news.

TIINGO_API_KEY via data.didm.keys, sent in the Authorization header (not the URL). Whether the free plan
includes the news endpoint is unverified: a 403 here answers that question.
"""
from __future__ import annotations

import re

from data.didm.keys import require
from data.net import session

KEY_NAME = "TIINGO_API_KEY"
URL = "https://api.tiingo.com/tiingo/news"
TIMEOUT_SECONDS = 30
_TICKER = re.compile(r"^[a-zA-Z0-9._\-]{1,20}$")


def fetch_news(tickers: list[str] | None = None, start_date: str | None = None, limit: int = 100) -> list:
    params: dict = {"limit": int(limit)}
    if tickers:
        if not all(_TICKER.match(t) for t in tickers):
            raise ValueError("bad ticker")
        params["tickers"] = ",".join(t.lower() for t in tickers)
    if start_date:
        params["startDate"] = start_date
    resp = session.get(URL, params=params, timeout=TIMEOUT_SECONDS,
                       headers={"Authorization": f"Token {require(KEY_NAME)}", "Content-Type": "application/json"})
    if resp.status_code != 200:
        raise RuntimeError(f"Tiingo news: HTTP {resp.status_code}")
    return resp.json()
