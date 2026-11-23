"""Domain records and time validation for Massive ticker-news observations.

Publication time does not attest when Massive delivered an article or assigned
its sentiment. Observations retain the supplied receipt time and may repeat an
article ID with revised metadata.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re


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


def receipt_utc(received_at: datetime) -> datetime:
    """Require a receipt instant from the caller, including for empty pages."""
    try:
        if not isinstance(received_at, datetime) or received_at.utcoffset() is None:
            raise ValueError
        return received_at.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        raise MassiveNewsError("received_at: valid timezone-aware datetime required") from None


def build_article(*, article_id, title, author, publisher_name, article_url, tickers,
                  published_utc, received_at_utc: datetime, insights) -> NewsArticle:
    """Assemble one observation using the adapter's checked link and UTC receipt."""
    article_id = _text(article_id, "id")
    if not article_id.strip():
        raise MassiveNewsError("id: empty identifier")
    if not isinstance(tickers, list):
        raise MassiveNewsError("tickers: array required")
    raw = _text(published_utc, "published_utc")
    return NewsArticle(
        article_id=article_id,
        title=_text(title, "title"),
        author=_text(author, "author"),
        publisher_name=_text(publisher_name, "publisher name", optional=True),
        article_url=article_url,
        tickers=tuple(_text(ticker, "ticker") for ticker in tickers),
        published_utc_raw=raw,
        published_at_utc=_published(raw, received_at_utc),
        received_at_utc=received_at_utc,
        insights=_insights(insights),
    )
