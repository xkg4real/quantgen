"""DIDM-9 Version 0 shock construction (Notion DIDM 5.1, Stage A; PREREG_V0 1 and 4).

    s^k_{i,t} = sum over articles a received in (t-1, t] of  pi_a * s_hat_a,      s_hat = P(+1) - P(-1)

from validated ``didm-score-v0`` records, with the registered filters:

* only records received after the previous decision time and at or before this one (PREREG_V0 1:
  ``received_at <= decision time``, no exception);
* only records whose target is the article's subject: ``relevance_0_100 >= 75`` (PREREG_V0 4);
* event type ``none`` is never a signal (PREREG_V0 2); records with no target are skipped;
* one record per origin cluster and target: re-publications count once, the first received (PREREG_V0 4).

pi is the record's ``p_credibility`` unless the caller passes a newer value per record (the state
as known at the decision time). The uncertainty u of a cell is the credibility-weighted mean entropy
of the direction probabilities of the records that entered it, and |s| is the absolute shock: the
two news regressors of the HAR-X equation.

No model, no network, no clock; the caller supplies the records and the two decision times.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from core.didm.llm.schema import EventType, ScoreRecord, TargetKind

RELEVANCE_MIN = 75.0              # PREREG_V0 4 (registered)


class ShockError(ValueError):
    pass


@dataclass(frozen=True)
class Cell:
    entity_id: str
    event_type: EventType
    shock: float                  # sum of pi * s_hat
    abs_shock: float
    uncertainty: float            # credibility-weighted mean entropy (nats); 0 if all weights are 0
    n_records: int                # records that entered (after the filters and the once-per-cluster rule)
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class Dropped:
    late_or_early: int = 0
    not_subject: int = 0
    no_type_or_target: int = 0
    repeated_origin: int = 0


def expected_sign(record: ScoreRecord) -> float:
    return record.direction_probs[0] - record.direction_probs[1]


def build(records: Sequence[ScoreRecord], *, previous_decision: datetime, decision: datetime,
          credibility: Mapping[str, float] | None = None) -> tuple[dict[tuple[str, EventType], Cell], Dropped]:
    """Shocks per (entity, event type) for the decision at ``decision``.

    ``credibility`` maps record_id to pi as known at the decision time; a record not in it uses its own
    ``p_credibility``. Records received before ``previous_decision`` or after ``decision`` are not read.
    """
    for name, value in (("previous_decision", previous_decision), ("decision", decision)):
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ShockError(f"{name} must be a timezone-aware datetime")
    if previous_decision >= decision:
        raise ShockError("previous_decision must be before decision")
    credibility = credibility or {}
    ids = [r.record_id for r in records]
    if len(set(ids)) != len(ids):
        raise ShockError("duplicate record_id")
    drop = dict(late_or_early=0, not_subject=0, no_type_or_target=0, repeated_origin=0)
    kept: dict[tuple[str, EventType], list[ScoreRecord]] = {}
    seen_origin: set[tuple[str, str]] = set()
    for record in sorted(records, key=lambda r: (r.received_at, r.record_id)):
        if not isinstance(record, ScoreRecord):
            raise ShockError("records must be validated ScoreRecord objects")
        if not previous_decision < record.received_at <= decision:
            drop["late_or_early"] += 1
            continue
        if record.target_kind is TargetKind.NONE or record.event_type is EventType.NONE:
            drop["no_type_or_target"] += 1
            continue
        if record.relevance_0_100 < RELEVANCE_MIN:
            drop["not_subject"] += 1
            continue
        origin = (record.entity_id, record.origin_cluster_id)
        if origin in seen_origin:
            drop["repeated_origin"] += 1
            continue
        seen_origin.add(origin)
        kept.setdefault((record.entity_id, record.event_type), []).append(record)
    cells = {}
    for key, group in kept.items():
        total = weight = entropy = 0.0
        for record in group:
            pi = credibility.get(record.record_id, record.p_credibility)
            if isinstance(pi, bool) or not isinstance(pi, (int, float)) or not 0.0 <= pi <= 1.0:
                raise ShockError("credibility must be a number in [0, 1]")
            total += pi * expected_sign(record)
            weight += pi
            entropy += pi * record.uncertainty_entropy
        cells[key] = Cell(key[0], key[1], total, abs(total), entropy / weight if weight > 0 else 0.0, len(group),
                          tuple(r.record_id for r in group))
    return cells, Dropped(**drop)
