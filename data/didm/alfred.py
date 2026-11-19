"""ALFRED vintage HTTP client for DIDM. Parsing lives in core.didm.ingest.alfred.

Needs FRED_API_KEY (credential store or environment, via data.didm.keys; the value stays on the
owner's PC). Without it, use the manual-download route in tools/didm. The request URL carries the
key, so it is never logged or put into an exception message.
"""
from __future__ import annotations

from data.didm.keys import MissingKey, get_key, require
from data.net import session

KEY_NAME = "FRED_API_KEY"
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
TIMEOUT_SECONDS = 30


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
    }
    resp = session.get(OBSERVATIONS_URL, params=params, timeout=TIMEOUT_SECONDS)
    if resp.status_code != 200:
        # Do not include resp.url: it carries the key.
        raise RuntimeError(f"ALFRED {series_id}: HTTP {resp.status_code}")
    return resp.json()
