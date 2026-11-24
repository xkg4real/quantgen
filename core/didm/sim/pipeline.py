"""DIDM-9/e2e: the Version 0 pieces joined end to end on synthetic articles (a wiring check, not a
registered run and not a result about any market).

    articles -> entity links -> scorer -> validated judgements -> origin clusters -> events
             -> credibility state -> records (assembled, validated) -> shocks per decision day -> panel

Point in time by construction: links read the alias dictionary as of the article's day; clusters and
events only look back; a record's p_credibility is the credibility when the article was received
("assembly time"); a shock uses the credibility as known at that decision time, never the record's own
value and never a later report.

The scorer, the alias dictionary, the stance and "official" marks of each article and the decision
times are supplied by the caller. No model, no network, no clock, no market data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

import numpy as np

from core.didm.credibility import events, shock
from core.didm.credibility import state as cred
from core.didm.entities import cluster
from core.didm.entities.linker import Linker
from core.didm.llm import cutoffs
from core.didm.llm import scorer as sc
from core.didm.llm.judgement import ScoreRequest
from core.didm.llm.schema import MarketConfirmation, ScoreRecord


class PipelineError(ValueError):
    pass


@dataclass(frozen=True)
class Stages:
    """Everything the run produced, kept so that a test can compare stage by stage."""
    records: tuple[ScoreRecord, ...]
    record_article: dict[str, str]                       # record_id -> article_id
    origin_of: dict[str, str]                            # article_id -> origin article id
    event_of: dict[str, str]                             # record_id -> event id
    reports: tuple[cred.Report, ...]
    rejected_judgements: dict[str, int]                  # fixed reason -> count
    rejected_assembly: dict[str, int]
    unlinked_articles: int
    cells: dict[tuple[int, str, str], shock.Cell]        # (decision index, entity, event type value) -> cell
    dropped: dict[str, int]
    weights_version: str


def record_id(article_id: str, entity_id: str) -> str:
    return f"{article_id}/{entity_id}"


def run(articles: Sequence, *, linker: Linker, scorer: sc.Scorer, decisions: Sequence[datetime],
        weights: cred.Weights = cred.PLACEHOLDER, source_id: str = "synthetic-newsroom",
        event_key: events.EventKeyConfig | None = None) -> Stages:
    """``articles`` need: article_id, received_at, published_at, title, body, source_tier, stance, official."""
    if list(decisions) != sorted(set(decisions)) or len(decisions) < 2:
        raise PipelineError("decisions must be at least two increasing times")
    ordered = sorted(articles, key=lambda a: (a.received_at, a.article_id))
    by_id = {a.article_id: a for a in ordered}
    if len(by_id) != len(ordered):
        raise PipelineError("duplicate article_id")

    # 1. origin clusters (text only; earlier articles only)
    assignment = {a.article_id: a for a in cluster.assign(
        [cluster.Item(x.article_id, x.received_at, x.title) for x in ordered])}
    origin_of = {k: v.origin_article_id for k, v in assignment.items()}

    # 2. entity links, as of the article's day
    requests: list[ScoreRequest] = []
    mention_score: dict[tuple[str, str], int] = {}
    unlinked = 0
    for a in ordered:
        links = linker.link(article_id=a.article_id, as_of=a.received_at.date(), title=a.title, body=a.body)
        unlinked += not links
        for link in links:
            mention_score[(a.article_id, link.entity_id)] = link.mention_score
            requests.append(ScoreRequest(a.article_id, "en", a.title, a.body, link.target_kind, link.entity_id,
                                         link.entity_id))

    # 3. judgements (raw probabilities go into records here, so the batch is uncalibrated)
    batch = sc.run_scorer(scorer, requests, calibrated=False)

    # 4. events and credibility reports, in order of receipt
    mentions = [events.Mention(req.article_id, req.entity_id, jud.event_type.value, by_id[req.article_id].received_at,
                               assignment[req.article_id].origin_cluster_id) for req, jud in batch.judgements]
    event_of_pair = events.assign(mentions, config=event_key)
    reports = tuple(cred.Report(
        article_id=f"{req.article_id}/{req.entity_id}", event_id=event_of_pair[(req.article_id, req.entity_id)],
        received_at=by_id[req.article_id].received_at, source_tier=by_id[req.article_id].source_tier,
        origin_cluster_id=assignment[req.article_id].origin_cluster_id, stance=by_id[req.article_id].stance,
        official=by_id[req.article_id].official) for req, jud in batch.judgements)
    by_event: dict[str, list[cred.Report]] = {}
    for r in reports:
        by_event.setdefault(r.event_id, []).append(r)

    # 5. records: DIDM-side values as known when the article was received
    pairs = []
    for req, jud in batch.judgements:
        a = by_id[req.article_id]
        rid = record_id(req.article_id, req.entity_id)
        event = event_of_pair[(req.article_id, req.entity_id)]
        pi = cred.pi_at(by_event[event], event, a.received_at, weights)
        pairs.append((jud, sc.Assembly(
            article_id=req.article_id, target_kind=req.target_kind.value, entity_id=req.entity_id, record_id=rid,
            source_id=source_id, published_at=a.published_at.isoformat(), received_at=a.received_at.isoformat(),
            relevance_0_100=float(mention_score[(req.article_id, req.entity_id)]),   # pre-calibration rule value
            novelty_0_100=100.0 if assignment[req.article_id].rank_in_cluster == 1 else 0.0,   # stand-in, see E2E_V0
            origin_cluster_id=assignment[req.article_id].origin_cluster_id, p_credibility=pi,
            market_confirmation=MarketConfirmation.PENDING.value)))       # the event window cannot be over yet
    assembled = sc.assemble_batch(pairs, scorer.info)
    records = tuple(x.record for x in assembled.assembled)
    record_article = {r.record_id: r.record_id.split("/", 1)[0] for r in records}
    event_of = {record_id(req.article_id, req.entity_id): event_of_pair[(req.article_id, req.entity_id)]
                for req, _ in batch.judgements}

    # 6. shocks per decision, with the credibility as known at that decision
    cells: dict[tuple[int, str, str], shock.Cell] = {}
    dropped = {"late_or_early": 0, "not_subject": 0, "no_type_or_target": 0, "repeated_origin": 0}
    by_day: dict[int, list[ScoreRecord]] = {}
    position = 0
    for r in sorted(records, key=lambda r: r.received_at):
        while position + 1 < len(decisions) and r.received_at > decisions[position + 1]:
            position += 1
        if decisions[position] < r.received_at <= decisions[position + 1]:
            by_day.setdefault(position + 1, []).append(r)
    for index, group in by_day.items():
        when = decisions[index]
        known = {r.record_id: cred.pi_at(by_event[event_of[r.record_id]], event_of[r.record_id], when, weights)
                 for r in group}
        built, drop = shock.build(group, previous_decision=decisions[index - 1], decision=when, credibility=known)
        for (entity, etype), cell in built.items():
            cells[(index, entity, etype.value)] = cell
        for name in dropped:
            dropped[name] += getattr(drop, name)
    return Stages(records, record_article, origin_of, event_of, reports, batch.reject_counts,
                  assembled.reject_counts, unlinked, cells, dropped, weights.version)


def panel(stages: Stages, entity_ids: Sequence[str], n_decisions: int) -> dict[str, np.ndarray]:
    """(decision, entity) arrays, summed over event types: shock, |shock| and credibility-weighted entropy."""
    column = {e: i for i, e in enumerate(entity_ids)}
    out = {name: np.zeros((n_decisions, len(entity_ids))) for name in ("shock", "abs_shock", "uncertainty")}
    weight = np.zeros((n_decisions, len(entity_ids)))
    for (index, entity, _etype), cell in stages.cells.items():
        out["shock"][index, column[entity]] += cell.shock
        out["uncertainty"][index, column[entity]] += cell.uncertainty * cell.n_records
        weight[index, column[entity]] += cell.n_records
    out["abs_shock"] = np.abs(out["shock"])
    out["uncertainty"] = np.divide(out["uncertainty"], weight, out=np.zeros_like(weight), where=weight > 0)
    return out


def eligibility_summary(records: Sequence[ScoreRecord], registry: cutoffs.Registry) -> dict[str, int]:
    """How many records the training-cutoff rule allows for historical validation (model_version per record)."""
    ok = sum(registry.eligibility(r.model_version, published_at=r.published_at, received_at=r.received_at).eligible
             for r in records)
    return {"eligible": ok, "not_eligible": len(records) - ok}
