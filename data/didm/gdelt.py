"""GDELT 2.0 HTTP client for DIDM (keyless). Parsing lives in core.didm.ingest.gdelt.

Runs on the owner's PC or in an environment that allows data.gdeltproject.org
(the 2026-11-17 cloud session blocks it). Uses the shared retrying session.
"""
from __future__ import annotations

from data.net import session

LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
ALLOWED_PREFIXES = ("http://data.gdeltproject.org/gdeltv2/", "https://data.gdeltproject.org/gdeltv2/")
TIMEOUT_SECONDS = 60


def _check(url: str) -> None:
    if not url.startswith(ALLOWED_PREFIXES):
        raise ValueError(f"not a GDELT 2.0 file URL: {url}")


def fetch_text(url: str) -> str:
    _check(url)
    resp = session.get(url, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.text


def fetch_bytes(url: str) -> bytes:
    _check(url)
    resp = session.get(url, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content
