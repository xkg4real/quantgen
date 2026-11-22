"""Parse supplied Massive ticker-news pages; no client, storage or scorer.

Contract: https://massive.com/docs/rest/stocks/news . An article's publication
time does not attest when Massive delivered it or assigned its sentiment. Each
observation retains the caller's receipt time. Article IDs may recur with
different metadata. Neither historical point-in-time nor usage rights are
inferred. Body, description, sentiment reasoning, raw JSON and full page URLs
are deliberately excluded.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from urllib.parse import parse_qsl, unquote, urlsplit


class MassiveNewsError(ValueError):
    """Invalid or unconfirmed supplied page. Messages contain no payload values."""


@dataclass(frozen=True)
class TickerInsight:
    ticker: str | None
    sentiment: str | None  # provider label, including unfamiliar categories


@dataclass(frozen=True)
class NewsArticle:
    article_id: str
    title: str
    author: str
    publisher_name: str | None
    article_url: str | None  # exact publisher link if it can be retained in full
    tickers: tuple[str, ...]
    published_utc_raw: str
    published_at_utc: datetime  # microsecond view; raw text retains finer precision
    received_at_utc: datetime
    insights: tuple[TickerInsight, ...] | None


@dataclass(frozen=True)
class NewsPage:
    articles: tuple[NewsArticle, ...]
    next_cursor: str | None = field(repr=False)


_STAMP = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2})"
                    r"(?:\.([0-9]+))?([Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])")
_CREDENTIAL_QUERY = re.compile(r"(?:^|[?&;])\s*api_?key\s*=", re.IGNORECASE)


def _text(value, name, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise MassiveNewsError(f"{name}: string required")
    return value


def _published(raw, received):
    match = _STAMP.fullmatch(raw)
    if not match or match[3] == "-00:00":
        raise MassiveNewsError("published_utc: RFC3339 timestamp with known offset required")
    frac = match[2] or ""
    offset = "+00:00" if match[3].upper() == "Z" else match[3]
    try:
        stamp = datetime.fromisoformat(match[1] + "." + frac[:6].ljust(6, "0") + offset)
        stamp = stamp.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        raise MassiveNewsError("published_utc: invalid instant") from None
    if stamp > received or (stamp == received and any(d != "0" for d in frac[6:])):
        raise MassiveNewsError("published_utc: follows receipt")
    return stamp


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


def _insights(values):
    if values is None:
        return None
    if not isinstance(values, list):
        raise MassiveNewsError("insights: array required")
    items = []
    for row in values:
        if not isinstance(row, Mapping):
            raise MassiveNewsError("insight: object required")
        ticker = _text(row.get("ticker"), "insight ticker", optional=True)
        label = _text(row.get("sentiment"), "sentiment", optional=True)
        items.append(TickerInsight(ticker, label))
    return tuple(items)


def _article(row, received):
    if not isinstance(row, Mapping):
        raise MassiveNewsError("article: object required")
    article_id = _text(row.get("id"), "id")
    if not article_id.strip():
        raise MassiveNewsError("id: empty identifier")
    publisher = row.get("publisher")
    if not isinstance(publisher, Mapping):
        raise MassiveNewsError("publisher: object required")
    tickers = row.get("tickers")
    if not isinstance(tickers, list):
        raise MassiveNewsError("tickers: array required")
    raw = _text(row.get("published_utc"), "published_utc")
    link = row.get("article_url")
    _url(link, "article_url")
    # A query can identify an article or carry access credentials. A fragment can
    # also carry private data. Avoid inventing a link by dropping those components.
    if "?" in link or "#" in link:
        link = None
    return NewsArticle(article_id, _text(row.get("title"), "title"), _text(row.get("author"), "author"),
                       _text(publisher.get("name"), "publisher name", optional=True), link,
                       tuple(_text(t, "ticker") for t in tickers), raw, _published(raw, received),
                       received, _insights(row.get("insights")))


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
    try:
        if not isinstance(received_at, datetime) or received_at.utcoffset() is None:
            raise ValueError
        received = received_at.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        raise MassiveNewsError("received_at: valid timezone-aware datetime required") from None
    if (not isinstance(seen_cursors, Collection) or isinstance(seen_cursors, (str, bytes, bytearray, Mapping))
            or not all(isinstance(s, str) for s in seen_cursors)):
        raise MassiveNewsError("seen_cursors: collection of strings required")
    next_cursor = _cursor(payload.get("next_url"))
    if next_cursor is not None and next_cursor in seen_cursors:
        raise MassiveNewsError("next_url: repeated cursor")
    return NewsPage(tuple(_article(row, received) for row in rows), next_cursor)
