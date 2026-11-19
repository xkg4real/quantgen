"""CryptoPanic posts client for DIDM (DS-4b, free plan). Parsing: core.didm.ingest.news.

CRYPTOPANIC_API_KEY via data.didm.keys; it is a query parameter, so URLs are never logged. The current
path (developer v2) and the older v1 path are both tried, newest first: which one a free key may use is
unverified. The free plan asks for a source credit where the feed is shown (we show nothing; research only).
"""
from __future__ import annotations

import re

from data.didm.keys import require
from data.net import session

KEY_NAME = "CRYPTOPANIC_API_KEY"
PATHS = ("https://cryptopanic.com/api/developer/v2/posts/", "https://cryptopanic.com/api/v1/posts/")
TIMEOUT_SECONDS = 30
_CODE = re.compile(r"^[A-Z0-9]{1,15}$")


def fetch_posts(currencies: list[str] | None = None) -> tuple[dict, str]:
    """Returns (payload, which path answered: 'v2' or 'v1')."""
    params = {"auth_token": require(KEY_NAME), "public": "true"}
    if currencies:
        if not all(_CODE.match(c) for c in currencies):
            raise ValueError("bad currency code")
        params["currencies"] = ",".join(currencies)
    last = None
    for url, label in zip(PATHS, ("v2", "v1")):
        resp = session.get(url, params=params, timeout=TIMEOUT_SECONDS)
        if resp.status_code == 200:
            return resp.json(), label
        last = resp.status_code
        if resp.status_code not in (404, 410):
            break
    raise RuntimeError(f"CryptoPanic posts: HTTP {last}")
