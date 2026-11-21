"""ALFRED vintage HTTP client for DIDM. Parsing lives in core.didm.ingest.alfred.

Needs FRED_API_KEY (credential store or environment, via data.didm.keys; the value stays on the
owner's PC). Without it, use the manual-download route in tools/didm. The request URL carries the
key, so it is never logged or put into an exception message.
"""
from __future__ import annotations

from requests.exceptions import RequestException

from data.didm.keys import MissingKey, SourceError, get_key, require
from data.net import session

KEY_NAME = "FRED_API_KEY"
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
TIMEOUT_SECONDS = 30
PAGE_LIMIT = 100_000


def has_key() -> bool:
    return bool(get_key(KEY_NAME))


def fetch_vintages(series_id: str) -> dict:
    """All vintages of one series (realtime period 1776-07-04 .. 9999-12-31)."""
    key = require(KEY_NAME, "use the manual ALFRED download route")
    params = {
        "series_id": series_id,
        "realtime_start": "1776-07-04",
        "realtime_end": "9999-12-31",
        "file_type": "json",
        "api_key": key,
        "limit": PAGE_LIMIT,
    }
    observations = []
    total = None
    first = None
    while total is None or len(observations) < total:
        offset = len(observations)
        try:
            resp = session.get(OBSERVATIONS_URL, params={**params, "offset": offset}, timeout=TIMEOUT_SECONDS)
        except RequestException:
            raise SourceError("ALFRED: transport failed") from None
        if resp.status_code != 200:
            # Do not include resp.url: it carries the key.
            raise SourceError(f"ALFRED {series_id}: HTTP {resp.status_code}")
        try:
            page = resp.json()
        except ValueError:
            raise SourceError("ALFRED: invalid JSON response") from None
        if not isinstance(page, dict) or not isinstance(page.get("observations"), list):
            raise SourceError("ALFRED: invalid observations page")
        count, page_offset = page.get("count"), page.get("offset")
        if type(count) is not int or count < 0 or type(page_offset) is not int or page_offset != offset:
            raise SourceError("ALFRED: invalid pagination metadata")
        if total is None:
            total, first = count, page
        elif count != total:
            raise SourceError("ALFRED: observation count changed during pagination; retry collection")
        batch = page["observations"]
        if len(batch) > PAGE_LIMIT or offset + len(batch) > total or (not batch and offset < total):
            raise SourceError("ALFRED: incomplete or inconsistent observations page")
        observations.extend(batch)
    return {**first, "observations": observations, "offset": 0, "limit": len(observations)}
