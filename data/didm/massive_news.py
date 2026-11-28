"""Parse supplied Massive ticker-news pages without fetching or storing them.

Contract: https://massive.com/docs/rest/stocks/news . Retain only article
metadata and the cursor needed for continuation. Do not infer usage rights or
historical availability from a supplied response.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime
import re
import time as _time
from urllib.parse import parse_qsl, unquote, urlsplit

from core.didm.ingest.massive_news import MassiveNewsError, NewsArticle, NewsPage, build_article, receipt_utc
from data.didm.keys import SourceError, require, safe_detail


_CREDENTIAL_QUERY = re.compile(r"(?:^|[?&;])\s*api_?key\s*=", re.IGNORECASE)


def _url(value, name):
    if not isinstance(value, str) or any(ord(ch) <= 32 or ord(ch) == 127 for ch in value):
        raise MassiveNewsError(f"{name}: invalid URL")
    try:
        parts = urlsplit(value)
        if parts.scheme not in ("https", "http") or not parts.hostname or parts.username is not None:
            raise ValueError
        # urlsplit parses the port lazily; reject malformed and out-of-range ports here.
        _ = parts.port
    except ValueError:
        raise MassiveNewsError(f"{name}: invalid URL") from None
    return parts


def _cursor(value):
    if value is None:
        return None
    parts = _url(value, "next_url")
    if (parts.scheme != "https" or parts.netloc.lower() not in ("api.massive.com", "api.massive.com:443")
            or parts.path != "/v2/reference/news" or "#" in value):
        raise MassiveNewsError("next_url: unexpected origin, path or fragment")
    try:
        pairs = parse_qsl(parts.query, keep_blank_values=True, errors="strict")
    except ValueError:
        raise MassiveNewsError("next_url: invalid query") from None
    cursors = [v for k, v in pairs if k == "cursor"]
    if len(cursors) != 1 or not cursors[0].strip():
        raise MassiveNewsError("next_url: one nonempty cursor required")
    cursor = cursors[0]
    keys = [v for k, v in pairs if k.casefold() in ("apikey", "api_key") and v]
    # The token has no documented alphabet. Inspect nested escaping for credentials
    # but return the once-decoded query value verbatim.
    inspected = cursor
    for _ in range(4):
        if (any(ord(ch) < 32 or ord(ch) == 127 for ch in inspected)
                or _CREDENTIAL_QUERY.search(inspected) or "://" in inspected
                or any(key in inspected for key in keys)):
            raise MassiveNewsError("next_url: unsafe cursor")
        decoded = unquote(inspected)
        if decoded == inspected:
            return cursor
        inspected = decoded
    raise MassiveNewsError("next_url: excessive nested escaping")


def _article(row, received: datetime) -> NewsArticle:
    if not isinstance(row, Mapping):
        raise MassiveNewsError("article: object required")
    publisher = row.get("publisher")
    if not isinstance(publisher, Mapping):
        raise MassiveNewsError("publisher: object required")
    link = row.get("article_url")
    _url(link, "article_url")
    # A query can identify an article or carry access credentials. A fragment can
    # also carry private data. Avoid inventing a link by dropping those components.
    if "?" in link or "#" in link:
        link = None
    return build_article(
        article_id=row.get("id"),
        title=row.get("title"),
        author=row.get("author"),
        publisher_name=publisher.get("name"),
        article_url=link,
        tickers=row.get("tickers"),
        published_utc=row.get("published_utc"),
        received_at_utc=received,
        insights=row.get("insights"),
    )


def parse_page(payload: Mapping, received_at: datetime, *, seen_cursors: Collection[str] = ()) -> NewsPage:
    """Retain page order and repeated IDs. A missing results array is unconfirmed.

    A successful empty array is valid. Optional count never determines whether
    there is another page. Callers may pass prior cursors to reject a cycle.
    """
    if not isinstance(payload, Mapping):
        raise MassiveNewsError("page: object required")
    if ("error" in payload or "errors" in payload or ("message" in payload and "status" not in payload)
            or ("status" in payload and payload["status"] != "OK")):
        raise MassiveNewsError("page: unsuccessful or unrecognized status")
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise MassiveNewsError("results: explicit array required")
    received = receipt_utc(received_at)
    if (not isinstance(seen_cursors, Collection) or isinstance(seen_cursors, (str, bytes, bytearray, Mapping))
            or not all(isinstance(s, str) for s in seen_cursors)):
        raise MassiveNewsError("seen_cursors: collection of strings required")
    next_cursor = _cursor(payload.get("next_url"))
    if next_cursor is not None and next_cursor in seen_cursors:
        raise MassiveNewsError("next_url: repeated cursor")
    return NewsPage(tuple(_article(row, received) for row in rows), next_cursor)


# --------------------------------------------------------------------------------------------------------------
# HTTP (DS-5c, owner N0 2026-11-24). The key goes in the Authorization header, never in the URL; the parser above
# already refuses a next_url that carries a key. Free plan: 5 requests per minute (Massive knowledge base, 2026-11-24
# search summary, unverified), so pages are spaced by MIN_INTERVAL_S.
# --------------------------------------------------------------------------------------------------------------
KEY_NAME = "MASSIVE_API_KEY"
NEWS_URL = "https://api.massive.com/v2/reference/news"
TIMEOUT_SECONDS = 30
MIN_INTERVAL_S = 12.5
_TICKER_RE = re.compile(r"^[A-Z0-9.\-:]{1,20}$")
_last_call = [0.0]


def valid_ticker(ticker: str) -> bool:
    return _TICKER_RE.fullmatch(ticker) is not None


def fetch_page(ticker: str | None = None, *, published_gte: str | None = None, limit: int = 100,
               cursor: str | None = None, sleep=_time.sleep, clock=_time.monotonic, get=None) -> dict:
    """One page of /v2/reference/news (ascending by published_utc). Returns the JSON; parse with parse_page."""
    if get is None:
        from data.net import session
        get = session.get
    key = require(KEY_NAME)
    if ticker is not None and not valid_ticker(ticker):
        raise ValueError("bad ticker")
    if not 1 <= int(limit) <= 1000:
        raise ValueError("limit must be 1..1000")
    params = {"limit": int(limit), "order": "asc", "sort": "published_utc"}
    if ticker:
        params["ticker"] = ticker
    if published_gte:
        params["published_utc.gte"] = published_gte
    if cursor:
        params["cursor"] = cursor
    wait = _last_call[0] + MIN_INTERVAL_S - clock()
    if _last_call[0] and wait > 0:
        sleep(wait)
    _last_call[0] = clock()
    resp = get(NEWS_URL, params=params, timeout=TIMEOUT_SECONDS,
                       headers={"Authorization": f"Bearer {key}"})
    if resp.status_code != 200:
        try:
            body = resp.json()
            detail = body.get("message") or body.get("error") or ""
        except Exception:  # noqa: BLE001 - not JSON
            detail = ""
        raise SourceError(f"Massive news: HTTP {resp.status_code}" + (f" ({safe_detail(detail, key)})" if detail else ""))
    return resp.json()
