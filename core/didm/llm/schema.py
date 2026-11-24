"""DIDM-1 score record schema, version 0 (docs/didm/SCORE_SCHEMA_V0.md).

One record = one article (or one GDELT/feed item) judged for one target entity.
Field names follow the DIDM page (Notion 02e5c916..., sections 5.1, 5.3, 9, 10.2)
and copy only the *public names* of RavenPack-style scores (relevance 0-100,
ESS-like 0-100 with 50 neutral, novelty). No vendor taxonomy or values are copied.

Pure standard library; no network, no clock reads. Validation rejects instead of
repairing: a record that fails is dropped and counted (DIDM 9 "Schema enforcement").
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "didm-score-v0"


class SchemaError(ValueError):
    """A record does not satisfy the V0 schema."""


class EventType(str, Enum):
    """Fixed event-type enum, V0 (K = 14 + none; owner decision P1, 2026-11-18).

    The 14 types refine the earlier 12-type proposal (two merged pairs split back:
    trade/tariffs vs supply chain, M&A vs management), so every 12-type label maps
    onto the 14. DIDM 5.1 says K <= 12 in V0; the owner chose 14 (PREREG_V0 2).
    Changing this enum is a new schema version.
    """
    MONETARY_POLICY = "monetary_policy"          # 통화정책
    INFLATION = "inflation"                      # 물가
    EMPLOYMENT = "employment"                    # 고용
    GROWTH = "growth"                            # 성장
    FISCAL = "fiscal"                            # 재정
    TRADE_TARIFFS = "trade_tariffs"              # 무역·관세
    GEOPOLITICS = "geopolitics"                  # 전쟁·지정학
    ELECTION_POLICY = "election_policy"          # 선거·정책
    EARNINGS = "earnings"                        # 실적
    MERGERS_ACQUISITIONS = "mergers_acquisitions"  # 인수합병
    MANAGEMENT = "management"                    # 경영진
    REGULATION_LITIGATION = "regulation_litigation"  # 규제·소송
    SUPPLY_CHAIN = "supply_chain"                # 공급망
    CRYPTO_REGULATION_HACK = "crypto_regulation_hack"  # 암호화폐 규제·해킹
    NONE = "none"                                # 해당 없음 (신호로 쓰지 않음)


class MarketConfirmation(str, Enum):
    CONFIRMED = "CONFIRMED"
    CONTRADICTED = "CONTRADICTED"
    ALREADY_PRICED = "ALREADY_PRICED"
    PENDING = "PENDING"


class TargetKind(str, Enum):
    FIRM = "firm"
    MACRO = "macro"
    NONE = "none"


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:\-/]{0,127}$")


def ess_like(p_positive: float, p_negative: float) -> float:
    """ESS-like direction score 0..100, 50 neutral: 50 + 50 * (P(+) - P(-))."""
    _prob(p_positive, "p_positive")
    _prob(p_negative, "p_negative")
    if p_positive + p_negative > 1 + 1e-9:
        raise SchemaError("p_positive + p_negative exceeds 1")
    return 50.0 + 50.0 * (p_positive - p_negative)


def cluster_decay(rank_in_cluster: int, delta: float) -> float:
    """Rank-in-cluster decay 0..100 (first = 100, k-th = 100 * delta**(k-1)).

    Since owner decision P2 (2026-11-18) this is one *feature* of the novelty model
    (core/didm/novelty.py), not the novelty score itself.
    """
    if isinstance(rank_in_cluster, bool) or not isinstance(rank_in_cluster, int) or rank_in_cluster < 1:
        raise SchemaError("rank_in_cluster must be an integer >= 1")
    if not (0.0 < delta < 1.0):
        raise SchemaError("delta must be in (0, 1)")
    return 100.0 * delta ** (rank_in_cluster - 1)


def entropy(probabilities: list[float] | tuple[float, ...]) -> float:
    """Shannon entropy in nats of a probability vector (sums to 1 within 1e-6)."""
    if not probabilities:
        raise SchemaError("empty probability vector")
    for p in probabilities:
        _prob(p, "probability")
    if abs(sum(probabilities) - 1.0) > 1e-6:
        raise SchemaError("probabilities must sum to 1")
    return -sum(p * math.log(p) for p in probabilities if p > 0)


@dataclass(frozen=True)
class ScoreRecord:
    """A validated V0 score record. Build with validate_record()."""
    record_id: str
    source_id: str
    target_kind: TargetKind
    entity_id: str | None
    published_at: datetime
    received_at: datetime
    relevance_0_100: float
    ess_like_0_100: float
    novelty_0_100: float          # 100 * P(new event | features), novelty model (PREREG_V0 4.1)
    origin_cluster_id: str
    event_type: EventType
    direction_probs: tuple[float, float, float]  # (P(+1), P(-1), P(0))
    uncertainty_entropy: float
    p_credibility: float
    market_confirmation: MarketConfirmation
    model_version: str
    prompt_sha256: str
    schema_version: str = SCHEMA_VERSION

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, Enum):
                v = v.value
            elif isinstance(v, datetime):
                v = v.isoformat()
            elif isinstance(v, tuple):
                v = list(v)
            out[f.name] = v
        return out


REQUIRED = tuple(f.name for f in fields(ScoreRecord) if f.name != "schema_version")


def validate_record(raw: Mapping[str, Any]) -> ScoreRecord:
    """Return a ScoreRecord or raise SchemaError naming the first problem."""
    if not isinstance(raw, Mapping):
        raise SchemaError("record must be a mapping")
    extra = set(raw) - set(REQUIRED) - {"schema_version"}
    if extra:
        raise SchemaError(f"unknown fields: {sorted(extra)}")
    for name in REQUIRED:
        if name not in raw:
            raise SchemaError(f"missing field: {name}")
    version = raw.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise SchemaError(f"schema_version must be {SCHEMA_VERSION}")

    target_kind = _enum(TargetKind, raw["target_kind"], "target_kind")
    entity_id = raw["entity_id"]
    if target_kind is TargetKind.NONE:
        if entity_id is not None:
            raise SchemaError("entity_id must be null when target_kind is none")
    else:
        _ident(entity_id, "entity_id")

    published_at = _timestamp(raw["published_at"], "published_at")
    received_at = _timestamp(raw["received_at"], "received_at")

    direction = raw["direction_probs"]
    if not isinstance(direction, (list, tuple)) or len(direction) != 3:
        raise SchemaError("direction_probs must be [P(+1), P(-1), P(0)]")
    direction = tuple(float(_num(p, "direction_probs")) for p in direction)
    unc = entropy(direction)

    ess = _score(raw["ess_like_0_100"], "ess_like_0_100")
    expected_ess = ess_like(direction[0], direction[1])
    if abs(ess - expected_ess) > 1e-6:
        raise SchemaError("ess_like_0_100 must equal 50 + 50*(P(+1) - P(-1))")
    reported_unc = _num(raw["uncertainty_entropy"], "uncertainty_entropy")
    if abs(reported_unc - unc) > 1e-6:
        raise SchemaError("uncertainty_entropy must equal the entropy of direction_probs")

    model_version = raw["model_version"]
    if not isinstance(model_version, str) or not model_version.strip():
        raise SchemaError("model_version must be a non-empty string")
    prompt_sha = raw["prompt_sha256"]
    if not isinstance(prompt_sha, str) or not _SHA256.fullmatch(prompt_sha):
        raise SchemaError("prompt_sha256 must be 64 lowercase hex characters")

    return ScoreRecord(
        record_id=_ident(raw["record_id"], "record_id"),
        source_id=_ident(raw["source_id"], "source_id"),
        target_kind=target_kind,
        entity_id=entity_id,
        published_at=published_at,
        received_at=received_at,
        relevance_0_100=_score(raw["relevance_0_100"], "relevance_0_100"),
        ess_like_0_100=ess,
        novelty_0_100=_score(raw["novelty_0_100"], "novelty_0_100"),
        origin_cluster_id=_ident(raw["origin_cluster_id"], "origin_cluster_id"),
        event_type=_enum(EventType, raw["event_type"], "event_type"),
        direction_probs=direction,  # type: ignore[arg-type]
        uncertainty_entropy=unc,
        p_credibility=_prob(raw["p_credibility"], "p_credibility"),
        market_confirmation=_enum(MarketConfirmation, raw["market_confirmation"], "market_confirmation"),
        model_version=model_version,
        prompt_sha256=prompt_sha,
    )


# --- Stage 1 gold-set label (DIDM 6.2 Stage 1: 1,000-1,500 human-labelled articles) ---

class Direction(str, Enum):
    POSITIVE = "+1"
    NEGATIVE = "-1"
    NEUTRAL = "0"


@dataclass(frozen=True)
class GoldLabel:
    article_id: str
    annotator_id: str
    market: str            # "EN" or "KR"
    source_tier: int       # 1 official/wire, 2 major outlet, 3 social/other
    target_kind: TargetKind
    entity_id: str | None
    is_subject: bool       # DIDM 9 question 1: is the entity the subject?
    event_type: EventType
    direction: Direction
    is_new_event: bool     # novelty ground truth
    claim_status: str      # "reported" or "confirmed" (DIDM 9 question 5)
    published_at: datetime
    received_at: datetime


def validate_gold(raw: Mapping[str, Any]) -> GoldLabel:
    names = [f.name for f in fields(GoldLabel)]
    extra = set(raw) - set(names)
    if extra:
        raise SchemaError(f"unknown fields: {sorted(extra)}")
    for name in names:
        if name not in raw:
            raise SchemaError(f"missing field: {name}")
    if raw["market"] not in ("EN", "KR"):
        raise SchemaError("market must be EN or KR")
    if raw["source_tier"] not in (1, 2, 3) or isinstance(raw["source_tier"], bool):
        raise SchemaError("source_tier must be 1, 2 or 3")
    if raw["claim_status"] not in ("reported", "confirmed"):
        raise SchemaError("claim_status must be reported or confirmed")
    for b in ("is_subject", "is_new_event"):
        if not isinstance(raw[b], bool):
            raise SchemaError(f"{b} must be a boolean")
    kind = _enum(TargetKind, raw["target_kind"], "target_kind")
    entity = raw["entity_id"]
    if kind is TargetKind.NONE:
        if entity is not None:
            raise SchemaError("entity_id must be null when target_kind is none")
    else:
        _ident(entity, "entity_id")
    return GoldLabel(
        article_id=_ident(raw["article_id"], "article_id"),
        annotator_id=_ident(raw["annotator_id"], "annotator_id"),
        market=raw["market"],
        source_tier=raw["source_tier"],
        target_kind=kind,
        entity_id=entity,
        is_subject=raw["is_subject"],
        event_type=_enum(EventType, raw["event_type"], "event_type"),
        direction=_enum(Direction, raw["direction"], "direction"),
        is_new_event=raw["is_new_event"],
        claim_status=raw["claim_status"],
        published_at=_timestamp(raw["published_at"], "published_at"),
        received_at=_timestamp(raw["received_at"], "received_at"),
    )


# --- helpers ---

def _num(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value):
        raise SchemaError(f"{name} must be finite")
    return value


def _prob(value: Any, name: str) -> float:
    value = _num(value, name)
    if not 0.0 <= value <= 1.0:
        raise SchemaError(f"{name} must be in [0, 1]")
    return value


def _score(value: Any, name: str) -> float:
    value = _num(value, name)
    if not 0.0 <= value <= 100.0:
        raise SchemaError(f"{name} must be in [0, 100]")
    return value


def _ident(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise SchemaError(f"{name} must be an identifier string")
    return value


def _enum(enum: type[Enum], value: Any, name: str) -> Any:
    try:
        return enum(value)
    except ValueError:
        raise SchemaError(f"unknown {name}: {value!r}") from None


def _timestamp(value: Any, name: str) -> datetime:
    if value is None:
        raise SchemaError(f"{name} is required")
    if not isinstance(value, str):
        raise SchemaError(f"{name} must be an ISO 8601 string")
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SchemaError(f"{name} is not ISO 8601") from None
    if ts.tzinfo is None:
        raise SchemaError(f"{name} must carry a timezone")
    return ts
