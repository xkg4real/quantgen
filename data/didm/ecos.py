"""Bank of Korea ECOS client for DIDM (owner answer Q3, 2026-11-18). Parsing: core.didm.ingest.ecos.

Needs ECOS_API_KEY (name only; value on the owner's PC). ECOS puts the key in the
URL path, so the URL is never logged or put in an error message.
"""
from __future__ import annotations

import os
from urllib.parse import quote

from data.net import session

KEY_NAME = "ECOS_API_KEY"
BASE = "https://ecos.bok.or.kr/api/StatisticSearch"
TIMEOUT_SECONDS = 30


class MissingKey(RuntimeError):
    pass


def has_key() -> bool:
    return bool(os.environ.get(KEY_NAME, "").strip())


def fetch_series(stat_code: str, cycle: str, start: str, end: str, *item_codes: str,
                 rows: int = 10000) -> dict:
    key = os.environ.get(KEY_NAME, "").strip()
    if not key:
        raise MissingKey(f"{KEY_NAME} is not set")
    if cycle not in ("A", "S", "Q", "M", "SM", "D"):
        raise ValueError(f"bad ECOS cycle {cycle!r}")
    parts = [BASE, quote(key, safe=""), "json", "kr", "1", str(int(rows)),
             quote(stat_code, safe=""), cycle, quote(start, safe=""), quote(end, safe="")]
    parts += [quote(c, safe="") for c in item_codes]
    resp = session.get("/".join(parts), timeout=TIMEOUT_SECONDS)
    if resp.status_code != 200:
        raise RuntimeError(f"ECOS {stat_code}: HTTP {resp.status_code}")
    return resp.json()
