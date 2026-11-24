"""DIDM-9 credibility state (Notion DIDM 5.3): the probability pi that an event is true, updated in log-odds
as reports arrive.

    logit pi_{e,t} = logit pi_{e,0} + sum over reports j received by t of  c_j * LLR(tier_j, stance_j)

* LLR weights are LEARNED by logistic regression on resolved events (confirmed versus debunked):
  ``fit_weights``. Until a resolved set exists, ``PLACEHOLDER`` weights are used; their version says
  "placeholder" and they are not estimates.
* c_j discounts copies: a report from an origin cluster that has already been counted for this event
  adds nothing by default (PREREG_V0 4: the same origin_cluster_id counts once).
* An official confirmation resolves pi to 1 and an official denial to 0. Otherwise pi stays inside
  [0.01, 0.99]: unresolved reports never make an event certain.
* Point in time: ``pi_at`` uses only reports received at or before the asked time, in order of receipt.

    impulse on asset i when pi changes: delta pi * D  (D = impact if true); a debunk gives -pi_before * D.

No model, no network, no clock. The caller supplies the reports (from records, clusters and links).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence

import numpy as np

from core.didm import novelty

TIERS = (1, 2, 3)                  # 1 official or wire, 2 major outlet, 3 social or other
PI_FLOOR, PI_CEILING = 0.01, 0.99


class CredibilityError(ValueError):
    pass


@dataclass(frozen=True)
class Report:
    article_id: str
    event_id: str                  # the claim this report is about (set by the caller: entity + event + origin)
    received_at: datetime
    source_tier: int
    origin_cluster_id: str
    stance: int                    # +1 supports the claim, -1 contradicts it
    official: bool = False         # an official statement by the party itself or a regulator (filing, release)

    def __post_init__(self) -> None:
        if not isinstance(self.received_at, datetime) or self.received_at.tzinfo is None:
            raise CredibilityError("received_at must be a timezone-aware datetime")
        if self.source_tier not in TIERS or isinstance(self.source_tier, bool):
            raise CredibilityError("source_tier must be 1, 2 or 3")
        if self.stance not in (-1, 1) or isinstance(self.stance, bool):
            raise CredibilityError("stance must be +1 or -1")
        if not isinstance(self.official, bool):
            raise CredibilityError("official must be a boolean")


@dataclass(frozen=True)
class Weights:
    """Log-likelihood ratios per source tier for a supporting report (a contradicting one gets the
    negative), the prior log-odds, and how much a repeated origin counts."""
    llr_by_tier: tuple[float, float, float]
    prior_logit: float
    copy_weight: float = 0.0       # weight of a report whose origin was already counted for this event
    fitted_on: int = 0             # number of resolved events the weights were learned from (0 = placeholder)
    # Readings that are a choice (docs/didm/CREDIBILITY_V0.md C1, C2; proposal questions 12 and 13):
    #   copy_weight 0 = a repeated origin adds nothing; above 0 = each copy adds that share of a report.
    #   official_resolves True = an official statement sets pi to 1 or 0 at once and ends the updating;
    #   False = it counts as one tier-1 report.
    official_resolves: bool = True

    def __post_init__(self) -> None:
        values = (*self.llr_by_tier, self.prior_logit, self.copy_weight)
        if len(self.llr_by_tier) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
            raise CredibilityError("weights must be finite numbers, one LLR per tier")
        if not 0.0 <= self.copy_weight <= 1.0:
            raise CredibilityError("copy_weight must be in [0, 1]")

    @property
    def version(self) -> str:
        payload = json.dumps([list(self.llr_by_tier), self.prior_logit, self.copy_weight, self.fitted_on,
                              self.official_resolves])
        kind = "fitted" if self.fitted_on > 0 else "placeholder"
        return f"cred-{kind}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"


# NOT estimates. Order only: an official or wire report moves belief more than a major outlet, which
# moves it more than a social post; the prior is even odds. Replace with fit_weights() output.
PLACEHOLDER = Weights(llr_by_tier=(2.0, 1.0, 0.3), prior_logit=0.0)


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, x))))


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


@dataclass(frozen=True)
class Step:
    received_at: datetime
    article_id: str
    pi_before: float
    pi_after: float
    counted: float                 # c_j actually applied (1, copy_weight, or 0 after resolution)
    resolved: str | None           # "confirmed", "debunked" or None


def _ordered(reports: Sequence[Report], event_id: str) -> list[Report]:
    mine = [r for r in reports if r.event_id == event_id]
    ids = [r.article_id for r in mine]
    if len(set(ids)) != len(ids):
        raise CredibilityError("an article reports the same event twice")
    return sorted(mine, key=lambda r: (r.received_at.astimezone(timezone.utc), r.article_id))


def path(reports: Sequence[Report], event_id: str, weights: Weights = PLACEHOLDER) -> list[Step]:
    """The credibility of one event after each report, in order of receipt."""
    logit = weights.prior_logit
    pi = min(PI_CEILING, max(PI_FLOOR, _logistic(logit)))
    seen: set[str] = set()
    resolved: str | None = None
    steps: list[Step] = []
    for report in _ordered(reports, event_id):
        before = pi
        if resolved is not None:
            counted = 0.0                                         # nothing moves a resolved event
        elif report.official and weights.official_resolves:
            counted = 1.0
            resolved = "confirmed" if report.stance > 0 else "debunked"
            pi = 1.0 if report.stance > 0 else 0.0
        else:
            counted = weights.copy_weight if report.origin_cluster_id in seen else 1.0
            logit += counted * report.stance * weights.llr_by_tier[report.source_tier - 1]
            pi = min(PI_CEILING, max(PI_FLOOR, _logistic(logit)))
        seen.add(report.origin_cluster_id)
        steps.append(Step(report.received_at, report.article_id, before, pi, counted, resolved))
    return steps


def pi_at(reports: Sequence[Report], event_id: str, when: datetime, weights: Weights = PLACEHOLDER) -> float | None:
    """Credibility of the event as known at ``when``: reports received later are not read. None if there
    was no report yet."""
    if not isinstance(when, datetime) or when.tzinfo is None:
        raise CredibilityError("when must be a timezone-aware datetime")
    known = [r for r in reports if r.event_id == event_id and r.received_at <= when]
    steps = path(known, event_id, weights)
    return steps[-1].pi_after if steps else None


def impulses(steps: Sequence[Step], impact_if_true: float) -> list[tuple[datetime, float]]:
    """delta pi * D at each report. A debunk gives -pi_before * D: the reversal of what had been priced."""
    if not isinstance(impact_if_true, (int, float)) or not math.isfinite(impact_if_true):
        raise CredibilityError("impact_if_true must be a finite number")
    out = []
    for i, step in enumerate(steps):
        # before the first report nothing about the event was known, so nothing was priced: the first
        # impulse is pi * D, later ones are the change in pi times D
        base = step.pi_before if i > 0 else 0.0
        out.append((step.received_at, (step.pi_after - base) * impact_if_true))
    return out


def design_row(reports: Sequence[Report], event_id: str, copy_weight: float = 0.0) -> list[float]:
    """Regressors of one resolved event for fit_weights: intercept, then the signed, copy-discounted
    count of non-official reports per tier, using only reports received before the resolution."""
    counts = [0.0, 0.0, 0.0]
    seen: set[str] = set()
    for report in _ordered(reports, event_id):
        if report.official:
            break
        c = copy_weight if report.origin_cluster_id in seen else 1.0
        counts[report.source_tier - 1] += c * report.stance
        seen.add(report.origin_cluster_id)
    return [1.0, *counts]


def fit_weights(resolved_events: Mapping[str, bool], reports: Sequence[Report], copy_weight: float = 0.0) -> Weights:
    """Learn the LLRs from resolved events (event_id -> True if confirmed, False if debunked).

    Logistic regression of the outcome on the per-tier report counts (small ridge, as in the novelty
    model). Needs both outcomes and at least 30 events.
    """
    events = sorted(resolved_events)
    outcomes = [bool(resolved_events[e]) for e in events]
    if len(events) < 30 or len(set(outcomes)) < 2:
        raise CredibilityError("need at least 30 resolved events with both outcomes")
    x = np.array([design_row(reports, e, copy_weight) for e in events])
    beta = novelty.fit_logistic(x, np.array(outcomes, dtype=int))
    return Weights(llr_by_tier=(float(beta[1]), float(beta[2]), float(beta[3])), prior_logit=float(beta[0]),
                   copy_weight=copy_weight, fitted_on=len(events))
