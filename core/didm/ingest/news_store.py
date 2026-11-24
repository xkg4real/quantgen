"""Point-in-time store rows for Alpaca and Massive news pages (DS-5b/5c, owner N0 2026-11-24). No network.

Input: pages already parsed by ``core.didm.ingest.alpaca_news.parse_page`` and
``data.didm.massive_news.parse_page`` (their checks stay the only validation). Output: rows for
``core.didm.store.PointInTimeStore.append``.

* ``published_at`` = the provider's article clock (Alpaca ``created_at``, Massive ``published_utc``);
  ``received_at`` = our receipt (the parser's ``received_at_utc``); ``valid_at`` = ``published_at``.
* A revised article (Alpaca ``updated_at`` later, or a Massive repeat with new metadata) is a new store
  version of the same ``item_id``: the store keeps every version; nothing is overwritten.
* Kept: headline/title, author, provider/publisher, URL, tickers, and Massive's per-ticker sentiment labels.
  Never kept: bodies, summaries, images (the parsers already drop them).
"""
from __future__ import annotations

from typing import Iterable

SOURCE_ALPACA = "alpaca-news"
SOURCE_MASSIVE = "massive-news"
PARSER = "news-store-v0.1"


def alpaca_rows(articles: Iterable) -> list[dict]:
    out = []
    for a in articles:
        out.append({
            "source_id": SOURCE_ALPACA,
            "item_id": str(a.article_id),
            "kind": "news",
            "published_at": a.created.utc,
            "received_at": a.received_at_utc,
            "valid_at": a.created.utc,
            "payload": {
                "headline": a.headline, "author": a.author, "provider_source": a.source,
                "symbols": list(a.symbols), "url": a.url,
                "created_at_raw": a.created.raw, "updated_at_raw": a.updated.raw,
                "created_epoch_ns": a.created.epoch_nanoseconds,
                "updated_epoch_ns": a.updated.epoch_nanoseconds,
                "parser": PARSER,
            },
        })
    return out


def massive_rows(articles: Iterable) -> list[dict]:
    out = []
    for a in articles:
        insights = None if a.insights is None else [
            {"ticker": i.ticker, "sentiment": i.sentiment} for i in a.insights]
        out.append({
            "source_id": SOURCE_MASSIVE,
            "item_id": a.article_id,
            "kind": "news",
            "published_at": a.published_at_utc,
            "received_at": a.received_at_utc,
            "valid_at": a.published_at_utc,
            "payload": {
                "title": a.title, "author": a.author, "publisher": a.publisher_name,
                "url": a.article_url, "tickers": list(a.tickers),
                "published_utc_raw": a.published_utc_raw,
                "insights": insights, "has_insights": insights is not None,
                "parser": PARSER,
            },
        })
    return out
