"""ALFRED vintage HTTP client for DIDM. Parsing lives in core.didm.ingest.alfred.

Needs the environment variable FRED_API_KEY (name only; the value stays on the
owner's PC). Without it, use the manual-download route in tools/didm. The request
URL carries the key, so it is never logged or put into an exception message.
"""
from __future__ import annotations

import os

from data.net import session

KEY_NAME = "FRED_API_KEY"
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
TIMEOUT_SECONDS = 30


class MissingKey(RuntimeError):
    pass


def has_key() -> bool:
    return bool(os.environ.get(KEY_NAME, "").strip())


def fetch_vintages(series_id: str) -> dict:
    """All vintages of one series (realtime period 1776-07-04 .. 9999-12-31)."""
    key = os.environ.get(KEY_NAME, "").strip()
    if not key:
        raise MissingKey(f"{KEY_NAME} is not set; use the manual ALFRED download route")
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
