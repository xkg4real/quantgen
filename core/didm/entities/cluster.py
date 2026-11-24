"""Origin clustering: articles that repeat one original text get one ``origin_cluster_id``
(PREREG_V0 4: "같은 origin_cluster_id는 1건으로 셈"; the 2025-04 cascade was one origin re-posted many times).

Online and point-in-time: articles are processed in the order we received them, and an article joins
the cluster of the EARLIEST earlier article it is similar enough to, looking back a fixed window. An
article's cluster never depends on anything received after it, so adding later articles cannot change
an earlier assignment.

The threshold 0.80 is the registered "similar" value of the novelty features (PREREG_V0 4.1). Using the
same value for near-duplicates and the 7-day look-back are choices of this first version
(docs/didm/ENTITIES_V0.md); they are not registered values.

No model, no network, no clock.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from core.didm.entities import similarity as sim

NEAR_DUPLICATE = 0.80
LOOKBACK = timedelta(days=7)


class ClusterError(ValueError):
    pass


@dataclass(frozen=True)
class Item:
    article_id: str
    received_at: datetime
    text: str                       # headline, or headline plus lead; in memory only


@dataclass(frozen=True)
class Assignment:
    article_id: str
    origin_cluster_id: str
    rank_in_cluster: int            # 1 = the first article of the cluster (the origin as far as we saw)
    origin_article_id: str
    similarity_to_origin: float


def cluster_id(origin_article_id: str) -> str:
    """Stable identifier that satisfies the record schema's identifier rule."""
    return "cl-" + hashlib.sha256(origin_article_id.encode("utf-8")).hexdigest()[:20]


def assign(items: Sequence[Item], *, threshold: float = NEAR_DUPLICATE, lookback: timedelta = LOOKBACK,
           exact: bool = True) -> list[Assignment]:
    """One assignment per item, in the order received (ties by article_id).

    ``exact`` compares shingle sets (Jaccard). ``exact=False`` compares MinHash signatures, which is
    faster on large batches and approximate.
    """
    if not 0.0 < threshold <= 1.0 or lookback <= timedelta(0):
        raise ClusterError("threshold must be in (0, 1] and lookback positive")
    ids = [it.article_id for it in items]
    if len(set(ids)) != len(ids):
        raise ClusterError("duplicate article_id")
    for it in items:
        if not isinstance(it.received_at, datetime) or it.received_at.tzinfo is None:
            raise ClusterError("received_at must be a timezone-aware datetime")
    order = sorted(items, key=lambda it: (it.received_at.astimezone(timezone.utc), it.article_id))
    prepared = []
    for it in order:
        sh = sim.shingles(it.text)
        prepared.append((it, sh, sim.minhash(sh) if (sh and not exact) else None))
    origin_of: dict[str, str] = {}
    size: dict[str, int] = {}
    out: list[Assignment] = []
    for i, (item, sh, sig) in enumerate(prepared):
        when = item.received_at
        best: tuple[str, float] | None = None
        for other, osh, osig in prepared[:i]:                      # earlier items only, earliest first
            if when - other.received_at > lookback or not sh or not osh:
                continue
            score = sim.jaccard(sh, osh) if exact else sim.signature_similarity(sig, osig)
            if score >= threshold:
                best = (origin_of[other.article_id], score)
                break                                              # the earliest similar article decides
        if best is None:
            origin_of[item.article_id] = item.article_id
            size[item.article_id] = 1
            out.append(Assignment(item.article_id, cluster_id(item.article_id), 1, item.article_id, 1.0))
        else:
            origin, score = best
            origin_of[item.article_id] = origin
            size[origin] += 1
            out.append(Assignment(item.article_id, cluster_id(origin), size[origin], origin, score))
    return out
