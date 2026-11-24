"""Alpaca News REST client for DIDM (DS-5b, owner N0 2026-11-24). Parsing: core.didm.ingest.alpaca_news.

GET https://data.alpaca.markets/v1beta1/news with the key id and secret in headers (APCA-API-KEY-ID,
APCA-API-SECRET-KEY), never in the URL. Article bodies are not requested (include_content=false) and the
parser never keeps summary, content or images. Whether a free (Basic) account may use this REST endpoint
is unverified (2026-11-24 search: conflicting reports, one 403 "Subscription does not permit querying
news"); a refusal comes back as SourceError with Alpaca's own message, keys masked.
"""
from __future__ import annotations

import re

from data.didm.keys import SourceError, require, safe_detail

KEY_ID_NAME = "ALPACA_API_KEY_ID"
SECRET_NAME = "ALPACA_API_SECRET_KEY"
NEWS_URL = "https://data.alpaca.markets/v1beta1/news"
TIMEOUT_SECONDS = 30
MAX_LIMIT = 50
_SYMBOL = re.compile(r"^[A-Z0-9./\-]{1,20}$")


def fetch_page(symbols: list[str] | None = None, *, start: str | None = None, end: str | None = None,
               limit: int = MAX_LIMIT, page_token: str | None = None) -> dict:
    """One page, oldest first. Returns the JSON; parse with core.didm.ingest.alpaca_news.parse_page."""
    from data.net import session
    key_id, secret = require(KEY_ID_NAME), require(SECRET_NAME)
    if not 1 <= int(limit) <= MAX_LIMIT:
        raise ValueError("limit must be 1..50")
    params: dict = {"limit": int(limit), "sort": "asc", "include_content": "false"}
    if symbols:
        if not all(_SYMBOL.match(s) for s in symbols):
            raise ValueError("bad symbol")
        params["symbols"] = ",".join(symbols)
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if page_token:
        params["page_token"] = page_token
    resp = session.get(NEWS_URL, params=params, timeout=TIMEOUT_SECONDS,
                       headers={"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret})
    if resp.status_code != 200:
        try:
            detail = resp.json().get("message", "")
        except Exception:  # noqa: BLE001 - not JSON
            detail = ""
        raise SourceError(f"Alpaca news: HTTP {resp.status_code}"
                          + (f" ({safe_detail(detail, key_id, secret)})" if detail else ""))
    return resp.json()
