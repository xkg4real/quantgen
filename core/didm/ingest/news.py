"""News feeds with free keys for DIDM (DS-4b): Alpha Vantage NEWS_SENTIMENT, Tiingo News, CryptoPanic.

No network here; ``data.didm.{alphavantage,tiingo,cryptopanic}`` fetch. One row = one article.

Kept: id, title, url, source, times, tickers/currencies, vendor scores (as *inputs and baselines*, not as
DIDM scores; PREREG_V0 6: a vendor's historical sentiment is not used for past validation until we know it
was computed at the time). Not kept: article bodies and vendor summaries (licences unverified; DIDM 8.3).

Field names come from public docs and third-party copies (2026-11-17/19 search summaries; the vendor hosts
were blocked from the cloud session) -- **unverified until the first owner-PC run**. Required fields fail
loudly; optional ones are recorded as missing (None), never as a made-up 0.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Mapping

SOURCE_ALPHAVANTAGE = "alphavantage-news"
SOURCE_TIINGO = "tiingo-news"
SOURCE_CRYPTOPANIC = "cryptopanic"
PARSER = "news-v0.1"


class NewsError(ValueError):
    pass


def _aware(received_at: datetime) -> None:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise NewsError("received_at must be timezone-aware")


def _iso(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise NewsError(f"{name}: missing time")
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise NewsError(f"{name}: bad time {value!r}") from None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise NewsError(f"bad number {value!r}") from None


def _url_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def alphavantage_rows(payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """NEWS_SENTIMENT JSON. ``time_published`` is 'YYYYMMDDTHHMMSS' without a zone; taken as UTC and marked
    ``tz_assumed`` (unverified). A 'Note'/'Information' reply (rate limit) raises with its key name only."""
    _aware(received_at)
    if "feed" not in payload:
        hint = next((k for k in ("Note", "Information", "Error Message") if k in payload), None)
        raise NewsError(f"Alpha Vantage reply without feed ({hint or 'unknown'})")
    out = []
    for a in payload["feed"] or []:
        url, stamp = a.get("url"), a.get("time_published")
        if not url or not stamp:
            raise NewsError("article without url or time_published")
        try:
            published = datetime.strptime(stamp[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            raise NewsError(f"bad time_published {stamp!r}") from None
        tickers = [{
            "ticker": t.get("ticker"),
            "relevance_score": _num(t.get("relevance_score")),
            "sentiment_score": _num(t.get("ticker_sentiment_score")),
            "sentiment_label": t.get("ticker_sentiment_label"),
        } for t in a.get("ticker_sentiment") or []]
        out.append({
            "source_id": SOURCE_ALPHAVANTAGE, "item_id": _url_id(url), "kind": "news",
            "published_at": published, "received_at": received_at, "valid_at": published,
            "payload": {
                "title": a.get("title"), "url": url, "source": a.get("source"),
                "topics": [{"topic": t.get("topic"), "relevance_score": _num(t.get("relevance_score"))}
                           for t in a.get("topics") or []],
                "overall_sentiment_score": _num(a.get("overall_sentiment_score")),
                "overall_sentiment_label": a.get("overall_sentiment_label"),
                "tickers": tickers,
                "has_relevance_field": any(t["relevance_score"] is not None for t in tickers),
                "tz_assumed": "UTC", "parser": PARSER,
            },
        })
    return out


def tiingo_rows(payload: Any, received_at: datetime) -> list[dict]:
    """Tiingo /tiingo/news list. ``crawlDate`` far after ``publishedDate`` marks a backfilled article."""
    _aware(received_at)
    if not isinstance(payload, list):
        detail = payload.get("detail") if isinstance(payload, Mapping) else None
        raise NewsError(f"Tiingo reply is not a list ({'detail' if detail else type(payload).__name__})")
    out = []
    for a in payload:
        if a.get("id") is None or not a.get("url"):
            raise NewsError("article without id or url")
        published = _iso(a.get("publishedDate"), "publishedDate")
        crawl = a.get("crawlDate")
        crawled = _iso(crawl, "crawlDate") if crawl else None
        lag_h = (crawled - published).total_seconds() / 3600 if crawled else None
        out.append({
            "source_id": SOURCE_TIINGO, "item_id": str(a["id"]), "kind": "news",
            "published_at": published, "received_at": received_at, "valid_at": published,
            "payload": {
                "title": a.get("title"), "url": a["url"], "source": a.get("source"),
                "tickers": list(a.get("tickers") or []), "tags": list(a.get("tags") or []),
                "crawl_date": crawled.isoformat() if crawled else None,
                "crawl_lag_hours": round(lag_h, 3) if lag_h is not None else None,
                "backfilled": lag_h is not None and lag_h > 24,
                "has_tags_field": "tags" in a, "parser": PARSER,
            },
        })
    return out


def cryptopanic_rows(payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """CryptoPanic posts JSON (``results`` list)."""
    _aware(received_at)
    results = payload.get("results") if isinstance(payload, Mapping) else None
    if not isinstance(results, list):
        raise NewsError("CryptoPanic reply has no results list")
    out = []
    for p in results:
        if p.get("id") is None:
            raise NewsError("post without id")
        published = _iso(p.get("published_at"), "published_at")
        votes = p.get("votes") if isinstance(p.get("votes"), Mapping) else None
        pos = _num(votes.get("positive")) if votes else None
        neg = _num(votes.get("negative")) if votes else None
        balance = (pos - neg) / (pos + neg) if pos is not None and neg is not None and pos + neg > 0 else None
        source = p.get("source") if isinstance(p.get("source"), Mapping) else {}
        out.append({
            "source_id": SOURCE_CRYPTOPANIC, "item_id": str(p["id"]), "kind": "news",
            "published_at": published, "received_at": received_at, "valid_at": published,
            "payload": {
                "title": p.get("title"), "url": p.get("url"), "kind": p.get("kind"),
                "source_domain": source.get("domain"),
                "currencies": [c.get("code") for c in p.get("currencies") or [] if isinstance(c, Mapping)],
                "votes": dict(votes) if votes else None,
                "vote_balance": balance,   # (pos - neg) / (pos + neg); ESS-like = 50 + 50 * balance
                "parser": PARSER,
            },
        })
    return out
