"""DIDM-9/e2e: a synthetic newsroom. A small world of firms, claims and articles with every truth known,
used to check that the pipeline pieces fit together (core/didm/sim/pipeline.py).

Everything is drawn from one seeded generator: firm names are made-up syllables, headlines are filled
templates, returns and volatility are simulated. Nothing here is a real company, a real article or a
market price, and nothing reads a file, a clock or the network.

One claim (event) = one firm, one event type, one day. Its articles are
  * independent reports: different outlets, different wording, different origins;
  * re-publications of one of them: the same wording with a trailing note (same origin);
  * for a rumour: one social post, many re-posts, then an official denial the same day or a later day.
The world also plants articles that must NOT reach any shock: a passing mention in the body, an alias
that is no longer valid, and a name two firms share.

Truth: the claim is real with probability pi (the credibility as known at that day's decision) and its
direction follows the stated probabilities, so E[realised impact | what DIDM knows] equals the shock.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import numpy as np

from core.didm.entities.linker import Alias
from core.didm.llm.schema import EventType, TargetKind

START = datetime(2026, 10, 1, tzinfo=timezone.utc)        # decision time of day d is START + (d + 1) days
TYPES = [e.value for e in EventType if e is not EventType.NONE]
_SYLLABLES = ("ba", "ce", "di", "fo", "gu", "ha", "ke", "li", "mo", "nu", "pa", "re", "si", "to", "vu", "za")
_OUTLETS = (
    (1, "{name} said in a filing that its {topic} review, case {token}, is complete and gave figures for the quarter"),
    (2, "Analysts weigh what case {token} means for {name}: the {topic} question, the timing and the likely response"),
    (2, "Inside {name}: people familiar with case {token} describe how the {topic} matter came to light this week"),
    (3, "Hearing chatter that {name} has a {topic} problem again, reference {token}, anyone else seeing the same thing"),
)
_RUMOUR = "Unconfirmed post claims {name} faces a sudden {topic} shock, tag {token}, source not named and not verified"
_DENIAL = "{name} issues an official statement on tag {token}: the {topic} claim circulating online is false, it says"
_PASSING = "Weekly sector note {token}: broad moves, little firm news, readers ask about valuation and currency effects"


@dataclass(frozen=True)
class Article:
    article_id: str
    received_at: datetime
    published_at: datetime
    title: str
    body: str | None
    source_tier: int
    # truth and caller-supplied marks (not produced by the scorer; see CREDIBILITY_V0.md C10)
    claim: int | None              # index of the claim this article reports, None for planted noise
    origin: str                    # true origin: article_id of the first copy
    stance: int                    # +1 supports, -1 denies
    official: bool


@dataclass(frozen=True)
class Claim:
    index: int
    firm: int
    day: int
    event_type: str
    probs: tuple[float, float, float]        # P(+1), P(-1), P(0): what a calibrated scorer reports
    kind: str                                # "reports", "rumour", "rumour_denied_same_day", "rumour_denied_later"


@dataclass(frozen=True)
class World:
    n_firms: int
    n_days: int
    entity_ids: tuple[str, ...]
    aliases: tuple[Alias, ...]
    claims: tuple[Claim, ...]
    articles: tuple[Article, ...]
    returns: np.ndarray            # (days, firms) abnormal returns
    market: np.ndarray             # (days,) market returns
    log_rv: np.ndarray             # (days, firms)
    theta0: float
    gamma: float
    planted: dict = field(default_factory=dict)       # article ids of the traps, by kind

    def decision(self, day: int) -> datetime:
        return START + timedelta(days=day + 1)


def _name(i: int) -> str:
    a, b, c = _SYLLABLES[i % 16], _SYLLABLES[(i // 16) % 16], _SYLLABLES[(i * 7 + 3) % 16]
    return f"{a}{b}{c}".capitalize() + f"x{i:02d} Holdings"


def _token(rng: np.random.Generator) -> str:
    return "".join(rng.choice(list("bcdfghjklmnpqrstvwz")) + rng.choice(list("aeiou")) for _ in range(6))


def build(*, n_firms: int = 40, n_days: int = 400, seed: int = 7, event_rate: float = 0.08, theta0: float = 0.01,
          gamma: float = 0.5, prior_logit: float = 0.0, llr: tuple[float, float, float] = (2.0, 1.0, 0.3)) -> World:
    rng = np.random.default_rng(seed)
    entity_ids = tuple(f"SYN:{i:03d}" for i in range(n_firms))
    names = [_name(i) for i in range(n_firms)]
    first_day = START.date()
    aliases = [Alias(names[i], entity_ids[i], TargetKind.FIRM, date(2000, 1, 1)) for i in range(n_firms)]
    # firm 3 changes its name half-way: the old name is valid up to that day, the new one from the next
    rename_day = n_days // 2
    renamed = "Novaquill Partners"
    aliases[3] = Alias(names[3], entity_ids[3], TargetKind.FIRM, date(2000, 1, 1), first_day + timedelta(days=rename_day))
    aliases.append(Alias(renamed, entity_ids[3], TargetKind.FIRM, first_day + timedelta(days=rename_day + 1)))
    # traps for the linker: a name retired before the sample and a name two firms share
    aliases.append(Alias("Oldcrest Works", entity_ids[0], TargetKind.FIRM, date(2000, 1, 1), first_day - timedelta(days=30)))
    aliases.append(Alias("Twinmark Group", entity_ids[1], TargetKind.FIRM, date(2000, 1, 1)))
    aliases.append(Alias("Twinmark Group", entity_ids[2], TargetKind.FIRM, date(2000, 1, 1)))

    claims: list[Claim] = []
    articles: list[Article] = []
    planted = {"passing": [], "expired_alias": [], "ambiguous_alias": []}
    last_day: dict[tuple[int, str], int] = {}
    counter = 0

    def add(day: int, minute: int, title: str, tier: int, claim: int | None, origin: str | None = None, stance: int = 1,
            official: bool = False, body: str | None = None) -> str:
        nonlocal counter
        counter += 1
        article_id = f"art-{counter:06d}"
        when = START + timedelta(days=day, minutes=minute)
        articles.append(Article(article_id, when, when - timedelta(minutes=3), title, body, tier, claim,
                                origin or article_id, stance, official))
        return article_id

    for day in range(n_days):
        for firm in range(n_firms):
            if rng.random() >= event_rate:
                continue
            etype = TYPES[int(rng.integers(len(TYPES)))]
            # one claim per firm and type per window: claims of a firm and type are at least 9 days apart
            if day - last_day.get((firm, etype), -100) < 9:
                continue
            last_day[(firm, etype)] = day
            p = rng.dirichlet((0.6, 0.6, 0.3))
            probs = (float(p[0]), float(p[1]), float(1.0 - p[0] - p[1]))
            draw = rng.random()
            kind = ("reports" if draw < 0.80 else "rumour" if draw < 0.87 else
                    "rumour_denied_same_day" if draw < 0.94 else "rumour_denied_later")
            if kind != "reports" and day >= n_days - 3:
                kind = "reports"
            index = len(claims)
            claims.append(Claim(index, firm, day, etype, probs, kind))
            token, topic = _token(rng), etype.replace("_", " ")
            name = renamed if firm == 3 and day > rename_day else names[firm]
            minute = 30 + int(rng.integers(0, 300))
            if kind == "reports":
                outlets = rng.permutation(len(_OUTLETS))[: int(rng.integers(1, 4))]
                for k, o in enumerate(outlets):
                    tier, template = _OUTLETS[int(o)]
                    # an outlet's filing is a report here, not an "official statement" (C10): no resolution
                    title = template.format(name=name, topic=topic, token=token)
                    first = add(day, minute + 7 * k, title, tier, index)
                    for r in range(int(rng.integers(0, 3))):
                        add(day, minute + 7 * k + 2 + r, title + (" (update)", " (repost)")[r], tier, index, origin=first)
            else:
                first = add(day, minute, _RUMOUR.format(name=name, topic=topic, token=token), 3, index)
                for r in range(int(rng.integers(5, 31))):
                    add(day, minute + 1 + r, _RUMOUR.format(name=name, topic=topic, token=token) + f" rt{r % 3}", 3, index,
                        origin=first)
                if kind != "rumour":
                    denial_day = day if kind == "rumour_denied_same_day" else day + int(rng.integers(1, 3))
                    add(denial_day, minute + 60 if denial_day == day else 20,
                        _DENIAL.format(name=name, topic=topic, token=token), 1, index, stance=-1, official=True)
        # planted noise, a few per day
        if day % 5 == 0:
            pick = int(rng.integers(n_firms))
            other = renamed if pick == 3 and day > rename_day else names[pick]
            planted["passing"].append(add(day, 10, _PASSING.format(token=_token(rng)), 2, None,
                                          body=f"Among the names mentioned in passing was {other}."))
        if day % 23 == 0:
            planted["expired_alias"].append(add(day, 12, f"Oldcrest Works wins a surprise order, tag {_token(rng)}", 2, None))
            planted["ambiguous_alias"].append(add(day, 14, f"Twinmark Group shares jump on bid talk, tag {_token(rng)}", 2, None))

    # truth: credibility at each day's decision, realised impact, returns and volatility
    oracle = oracle_shocks(World(n_firms, n_days, entity_ids, tuple(aliases), tuple(claims), tuple(articles),
                                 np.zeros((1, 1)), np.zeros(1), np.zeros((1, 1)), theta0, gamma), prior_logit, llr)
    impact = np.zeros((n_days, n_firms))
    by_claim = {c.index: c for c in claims}
    for (day, firm, _etype, index), (count, pi, _sign) in oracle["parts"].items():
        c = by_claim[index]
        real = rng.random() < pi
        d = rng.random()
        direction = 1.0 if d < c.probs[0] else (-1.0 if d < c.probs[0] + c.probs[1] else 0.0)
        impact[day, firm] += count * (direction if real else 0.0)
    shock = oracle["shock"]
    level = math.log(0.01 ** 2)
    x = np.full((n_days, n_firms), level)
    noise = 0.3 * rng.standard_normal((n_days, n_firms))
    for t in range(21, n_days - 1):
        x[t + 1] = (0.2 * level + 0.35 * x[t] + 0.25 * x[t - 4: t + 1].mean(axis=0) + 0.20 * x[t - 21: t + 1].mean(axis=0)
                    + gamma * np.abs(shock[t]) + noise[t + 1])
    market = 0.008 * rng.standard_normal(n_days)
    returns = (0.005 * rng.standard_normal(n_days)[:, None] + theta0 * impact
               + np.exp(0.5 * x) * rng.standard_normal((n_days, n_firms)))
    planted["rename_day"] = rename_day
    return World(n_firms, n_days, entity_ids, tuple(aliases), tuple(claims), tuple(articles), returns, market, x,
                 theta0, gamma, planted)


def oracle_shocks(world: World, prior_logit: float = 0.0, llr: tuple[float, float, float] = (2.0, 1.0, 0.3)) -> dict:
    """The shock each decision day SHOULD see, computed from the world's own truth with plain arithmetic
    (no pipeline code): per claim and day, (number of distinct origins received that day) x (credibility
    of the claim at that day's decision) x (P(+1) - P(-1))."""
    shock = np.zeros((world.n_days, world.n_firms))
    by_claim: dict[int, list[Article]] = {}
    for a in world.articles:
        if a.claim is not None:
            by_claim.setdefault(a.claim, []).append(a)
    parts: dict[tuple[int, int, str, int], tuple[int, float, float]] = {}
    for claim in world.claims:
        reports = sorted(by_claim[claim.index], key=lambda a: (a.received_at, a.article_id))
        days = sorted({(a.received_at - START).days for a in reports})
        for day in days:
            cut = world.decision(day)
            logit, seen, pi = prior_logit, set(), None
            for a in reports:
                if a.received_at > cut:
                    break
                if a.official:
                    pi = 1.0 if a.stance > 0 else 0.0
                    break
                if a.origin not in seen:
                    logit += a.stance * llr[a.source_tier - 1]
                    seen.add(a.origin)
            if pi is None:
                pi = min(0.99, max(0.01, 1.0 / (1.0 + math.exp(-logit))))
            todays = {a.origin for a in reports if (a.received_at - START).days == day}
            sign = claim.probs[0] - claim.probs[1]
            parts[(day, claim.firm, claim.event_type, claim.index)] = (len(todays), pi, sign)
            shock[day, claim.firm] += len(todays) * pi * sign
    return {"shock": shock, "parts": parts}
