"""Gold-set sampling rule for DIDM Stage 1 (docs/didm/GOLD_SET_V0.md).

Draws the articles to label from candidate metadata only (no text, no scores, no prices), so the
choice cannot depend on what a model said or how the market moved. Strata are market x source tier
x calendar month of receipt; each stratum gets a share proportional to its size with a floor, and
the draw inside a stratum is a seeded shuffle. Same candidates and seed give the same sample.

Standard library only; no network, no clock reads. Candidates are passed in by the caller, which
reads them from the point-in-time store.
"""
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

MARKETS = ("EN", "KR")
TIERS = (1, 2, 3)
TARGET_MIN, TARGET_MAX = 1000, 1500       # PREREG_V0 3, Stage 1: 1,000-1,500 labelled articles, EN and KR
MIN_PER_STRATUM = 5
MIN_MARKET_SHARE = 0.30                   # neither market below 30% of the sample
DOUBLE_LABEL_SHARE = 1.0                  # every article is labelled by two annotators (kappa needs both)


class SamplingError(ValueError):
    pass


@dataclass(frozen=True)
class Candidate:
    article_id: str
    market: str
    source_tier: int
    received_at: datetime

    def __post_init__(self) -> None:
        if self.market not in MARKETS or self.source_tier not in TIERS or isinstance(self.source_tier, bool):
            raise SamplingError("market must be EN or KR and source_tier 1, 2 or 3")
        if not isinstance(self.received_at, datetime) or self.received_at.tzinfo is None:
            raise SamplingError("received_at must be a timezone-aware datetime")

    @property
    def stratum(self) -> tuple[str, int, str]:
        day = self.received_at.astimezone(timezone.utc)
        return (self.market, self.source_tier, f"{day.year:04d}-{day.month:02d}")


def draw(candidates: list[Candidate], n: int, seed: int) -> list[Candidate]:
    """A stratified sample of ``n`` candidates, ordered by article_id."""
    if not TARGET_MIN <= n <= TARGET_MAX:
        raise SamplingError(f"the gold set has {TARGET_MIN} to {TARGET_MAX} articles")
    ids = [c.article_id for c in candidates]
    if len(set(ids)) != len(ids):
        raise SamplingError("duplicate article_id among the candidates")
    if len(candidates) < n:
        raise SamplingError("fewer candidates than the sample size")
    by_market: dict[str, list[Candidate]] = defaultdict(list)
    for c in candidates:
        by_market[c.market].append(c)
    if set(by_market) != set(MARKETS):
        raise SamplingError("candidates must cover both EN and KR")

    # 1. split n between the markets in proportion to candidates, each market at least 30%
    floor = int(round(MIN_MARKET_SHARE * n))
    quota = {m: max(floor, int(round(n * len(by_market[m]) / len(candidates)))) for m in MARKETS}
    over = sum(quota.values()) - n
    biggest = max(MARKETS, key=lambda m: (quota[m], m))
    quota[biggest] -= over
    for m in MARKETS:
        if quota[m] > len(by_market[m]):
            raise SamplingError(f"not enough {m} candidates for a {MIN_MARKET_SHARE:.0%} share")

    rng = random.Random(seed)
    chosen: list[Candidate] = []
    for m in MARKETS:
        strata: dict[tuple, list[Candidate]] = defaultdict(list)
        for c in by_market[m]:
            strata[c.stratum].append(c)
        keys = sorted(strata)
        for key in keys:
            strata[key].sort(key=lambda c: c.article_id)
            rng.shuffle(strata[key])
        # 2. proportional allocation with a floor, by largest remainder
        size = {k: len(strata[k]) for k in keys}
        take = {k: min(size[k], MIN_PER_STRATUM) for k in keys}
        if sum(take.values()) > quota[m]:
            raise SamplingError("too many strata for the floor; shorten the window or lower the floor")
        left = quota[m] - sum(take.values())
        room = {k: size[k] - take[k] for k in keys}
        total_room = sum(room.values())
        shares = {k: left * room[k] / total_room if total_room else 0.0 for k in keys}
        for k in keys:
            take[k] += int(shares[k])
        short = quota[m] - sum(take.values())
        for k in sorted(keys, key=lambda k: (-(shares[k] - int(shares[k])), k)):
            if short <= 0:
                break
            if take[k] < size[k]:
                take[k] += 1
                short -= 1
        for k in keys:
            chosen += strata[k][: take[k]]
    if len(chosen) != n:
        raise SamplingError("allocation did not reach the sample size")
    return sorted(chosen, key=lambda c: c.article_id)
