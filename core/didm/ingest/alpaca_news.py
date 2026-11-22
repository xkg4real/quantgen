"""Supplied Alpaca News REST metadata only; no acquisition or pipeline wiring.

Field lineage: https://docs.alpaca.markets/us/reference/news-3.md (OpenAPI
news/news_resp). Required fields and known field types are checked. This is not
a complete JSON-Schema validator or an SDK. Unknown fields are tolerated, while
content, summary, images and unknown fields are excluded from the output.
That selection is neither a licence grant nor a general secret-redaction claim.

created_at is the provider's article creation clock, updated_at its update clock,
and received_at the caller's actual observation clock. None authenticates the
original publisher's release, an immutable historical version, or research PIT.
The as-of helper only enforces local snapshot availability; it never backdates
receipt or validates the V0 study, entitlements, rights, or model/scoring inputs.

All clocks/payloads are caller supplied. No HTTP, keys, environment/config,
store, collector, scheduler, model, scorer or actual-data calls are provided.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

_STAMP = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?([Zz]|[+-]\d{2}:\d{2})$",
    re.ASCII,
)
_REQUIRED = ("id", "headline", "author", "created_at", "updated_at", "summary",
             "content", "images", "symbols", "source")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class AlpacaNewsError(ValueError):
    """Invalid supplied input; messages never echo payload values or page tokens."""


@dataclass(frozen=True)
class NewsTimestamp:
    """Exact supplied RFC3339 text and instant, with a microsecond display view.

    epoch_nanoseconds preserves up to nine fractional digits for ordering; the
    datetime view is rounded down to microseconds and must not replace it in
    sub-microsecond comparisons. Unsupported precision/leap seconds fail rather
    than silently truncating an input timestamp.
    """
    raw: str
    utc: datetime
    epoch_nanoseconds: int


@dataclass(frozen=True)
class NewsArticle:
    article_id: int
    headline: str
    author: str
    source: str
    symbols: tuple[str, ...]
    url: str | None
    url_present: bool
    created: NewsTimestamp
    updated: NewsTimestamp
    received_at_utc: datetime


@dataclass(frozen=True)
class NewsPage:
    articles: tuple[NewsArticle, ...]
    next_page_token: str | None


def _text(value: Any, name: str, *, empty: bool = True) -> str:
    if not isinstance(value, str) or (not empty and not value):
        raise AlpacaNewsError(f"{name}: string required")
    return value


def _aware(value: Any, name: str) -> datetime:
    try:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise AlpacaNewsError(f"{name}: timezone-aware datetime required")
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise AlpacaNewsError(f"{name}: valid timezone-aware datetime required") from None


def _nanoseconds(value: datetime) -> int:
    elapsed = value - _EPOCH
    return ((elapsed.days * 86400 + elapsed.seconds) * 1_000_000 + elapsed.microseconds) * 1000


def _timestamp(value: Any, name: str) -> NewsTimestamp:
    raw = _text(value, name)
    match = _STAMP.fullmatch(raw)
    if match is None:
        raise AlpacaNewsError(f"{name}: explicit RFC3339 offset and supported precision required")
    base, fraction, suffix = match.groups()
    if suffix == "-00:00":
        raise AlpacaNewsError(f"{name}: unknown local offset")
    if suffix not in ("Z", "z") and (int(suffix[1:3]) >= 24 or int(suffix[4:6]) >= 60):
        raise AlpacaNewsError(f"{name}: invalid offset")
    try:
        whole = datetime.fromisoformat(base.replace("t", "T") +
                                        ("+00:00" if suffix in ("Z", "z") else suffix))
        whole = whole.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise AlpacaNewsError(f"{name}: invalid timestamp") from None
    fraction_ns = int((fraction or "").ljust(9, "0"))
    return NewsTimestamp(raw, whole.replace(microsecond=fraction_ns // 1000),
                         _nanoseconds(whole) + fraction_ns)


def parse_article(payload: Mapping[str, Any], received_at: datetime) -> NewsArticle:
    """Validate one supplied row and retain metadata, preserving clocks/duplicates.

    Documented required body/image fields are checked for their known types but
    never copied into the result. Optional URL absence/null/string is preserved;
    a retained URL is data, not an approved or validated navigation target.
    Future or backwards source clocks are refused instead of being re-labelled.
    """
    if not isinstance(payload, Mapping):
        raise AlpacaNewsError("article: mapping required")
    if any(name not in payload for name in _REQUIRED):
        raise AlpacaNewsError("article: required field missing")
    received = _aware(received_at, "received_at")
    article_id = payload["id"]
    if isinstance(article_id, bool) or not isinstance(article_id, int) or not -(2**63) <= article_id < 2**63:
        raise AlpacaNewsError("id: int64 required")
    headline = _text(payload["headline"], "headline", empty=False)
    author = _text(payload["author"], "author")
    source = _text(payload["source"], "source", empty=False)
    _text(payload["summary"], "summary")
    _text(payload["content"], "content")
    images = payload["images"]
    if not isinstance(images, list):
        raise AlpacaNewsError("images: array required")
    for image in images:
        if not isinstance(image, Mapping) or "size" not in image or "url" not in image:
            raise AlpacaNewsError("images: image fields required")
        if image["size"] not in ("thumb", "small", "large"):
            raise AlpacaNewsError("images: unsupported size")
        _text(image["url"], "image url", empty=False)
    symbols = payload["symbols"]
    if not isinstance(symbols, list) or not all(isinstance(item, str) for item in symbols):
        raise AlpacaNewsError("symbols: string array required")
    url = payload.get("url")
    if url is not None:
        _text(url, "url")
    created = _timestamp(payload["created_at"], "created_at")
    updated = _timestamp(payload["updated_at"], "updated_at")
    if updated.epoch_nanoseconds < created.epoch_nanoseconds:
        raise AlpacaNewsError("updated_at: precedes creation")
    if updated.epoch_nanoseconds > _nanoseconds(received):
        raise AlpacaNewsError("updated_at: follows receipt")
    return NewsArticle(article_id, headline, author, source, tuple(symbols), url,
                       "url" in payload, created, updated, received)


def locally_available_as_of(article: NewsArticle, cutoff: datetime) -> bool:
    """Only this received snapshot's availability, not historical PIT/rights approval."""
    if not isinstance(article, NewsArticle):
        raise AlpacaNewsError("article: NewsArticle required")
    at = _aware(cutoff, "cutoff")
    return _nanoseconds(at) >= max(article.updated.epoch_nanoseconds,
                                  _nanoseconds(article.received_at_utc))


def parse_page(payload: Mapping[str, Any], received_at: datetime, *, limit: int,
               current_token: str | None = None, seen_tokens: tuple[str, ...] = ()) -> NewsPage:
    """Retain page order and every supplied version; do not acquire or deduplicate.

    Continuation uses only the documented string/null token, including an opaque
    empty string. An empty/short page with a token still has a next page. A null
    token is not proof of complete/stable acquisition: the caller must preserve
    request filters, prior-page consistency and all response/receipt versions.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise AlpacaNewsError("limit: integer in 1..50 required")
    if not isinstance(payload, Mapping) or "news" not in payload or "next_page_token" not in payload:
        raise AlpacaNewsError("page: news and next_page_token required")
    rows, next_token = payload["news"], payload["next_page_token"]
    if not isinstance(rows, list) or len(rows) > limit:
        raise AlpacaNewsError("news: array within requested limit required")
    for token in (current_token, next_token):
        if token is not None and not isinstance(token, str):
            raise AlpacaNewsError("page token: string or null required")
    if not isinstance(seen_tokens, tuple) or not all(isinstance(token, str) for token in seen_tokens):
        raise AlpacaNewsError("seen_tokens: string tuple required")
    if next_token is not None and (next_token == current_token or next_token in seen_tokens):
        raise AlpacaNewsError("page token: repeated continuation")
    received = _aware(received_at, "received_at")
    articles = tuple(parse_article(row, received) for row in rows)
    return NewsPage(articles, next_token)
