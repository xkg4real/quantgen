"""SEC EDGAR submissions client for DIDM (owner answer Q3, 2026-11-18). Parsing: core.didm.ingest.filings.

SEC fair-access rules: at most 10 requests per second, and a User-Agent that names
the requester with a contact. The User-Agent comes from the environment variable
SEC_EDGAR_USER_AGENT, set on the owner's PC to a generic organisation contact (no
personal data in the repository). Without it the client refuses to call.
"""
from __future__ import annotations

import threading
import time

from data.didm.keys import MissingKey, SourceError, get_key, require
from data.net import session

UA_NAME = "SEC_EDGAR_USER_AGENT"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
MIN_INTERVAL_S = 0.125  # 8 requests per second, under the SEC's 10
TIMEOUT_SECONDS = 30
_lock = threading.Lock()
_last = [0.0]


MissingUserAgent = MissingKey


def _throttle() -> None:
    with _lock:
        wait = _last[0] + MIN_INTERVAL_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def fetch_submissions(cik: int) -> dict:
    ua = require(UA_NAME, "a generic contact, required by the SEC")
    _throttle()
    resp = session.get(SUBMISSIONS_URL.format(cik=int(cik)), timeout=TIMEOUT_SECONDS,
                       headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
    if resp.status_code != 200:
        raise SourceError(f"EDGAR CIK {int(cik)}: HTTP {resp.status_code}")
    return resp.json()
