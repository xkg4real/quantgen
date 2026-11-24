"""T-NEWS: the judgment part of a ``didm-score-v0`` record, and its assembly.

A ``didm-score-v0`` record has seventeen required fields. A language model can
produce five of them. The rest are either functions of the model's output
(the host computes them) or facts only the host pipeline knows (the model is
neither shown nor asked for them).

model       target_kind, entity_id, relevance_0_100, event_type, direction_probs
computed    ess_like_0_100, uncertainty_entropy
host only   novelty_0_100, origin_cluster_id, p_credibility, market_confirmation, received_at
copied      record_id, source_id, published_at, model_version, prompt_sha256

The rules below restate the public field rules of that schema so this package
does not import the host application; a test compares the two when both are
present.
"""
from __future__ import annotations

import math
from typing import Any

from ..checks import schema as S
from ..checks.schema import SchemaError

SCORE_SCHEMA_VERSION = "didm-score-v0"
EVENT_TYPES = ("monetary_policy", "inflation", "employment", "growth", "fiscal", "trade_tariffs",
               "geopolitics", "election_policy", "earnings", "mergers_acquisitions", "management",
               "regulation_litigation", "supply_chain", "crypto_regulation_hack", "none")
TARGET_KINDS = ("firm", "macro", "none")
MARKET_CONFIRMATION = ("CONFIRMED", "CONTRADICTED", "ALREADY_PRICED", "PENDING")

MODEL_FIELDS = ("target_kind", "entity_id", "relevance_0_100", "event_type", "direction_probs")
COMPUTED_FIELDS = ("ess_like_0_100", "uncertainty_entropy")
HOST_ONLY_FIELDS = ("novelty_0_100", "origin_cluster_id", "p_credibility", "market_confirmation", "received_at")
COPIED_FIELDS = ("record_id", "source_id", "published_at", "model_version", "prompt_sha256")
RECORD_FIELDS = ("record_id", "source_id", "target_kind", "entity_id", "published_at", "received_at",
                 "relevance_0_100", "ess_like_0_100", "novelty_0_100", "origin_cluster_id", "event_type",
                 "direction_probs", "uncertainty_entropy", "p_credibility", "market_confirmation",
                 "model_version", "prompt_sha256")

_ID = r"[A-Za-z0-9][A-Za-z0-9_.:\-/]{0,127}"
_ident = S.string(max_len=128, pattern=_ID)
_prob = S.number(lo=0.0, hi=1.0)
_score = S.number(lo=0.0, hi=100.0)
_target = S.obj({"target_kind": S.string(enum=("firm", "macro")), "entity_id": _ident})

INPUT = S.obj({
    "article": S.obj({"source_id": _ident, "title": S.string(max_len=500), "published_at": S.string(max_len=40)},
                     {"body": S.string(max_len=20000), "language": S.string(enum=("ko", "en"))}),
    "candidates": S.array(_target, max_len=50, unique=True),
})

_JUDGMENT = S.obj({
    "target_kind": S.string(enum=TARGET_KINDS),
    "entity_id": S.nullable(_ident),
    "relevance_0_100": _score,
    "event_type": S.string(enum=EVENT_TYPES),
    "direction_probs": S.array(_prob, min_len=3, max_len=3),
})
_OUTPUT = S.obj({"judgments": S.array(_JUDGMENT, min_len=1, max_len=50)})


def output_spec(value: Any, path: str) -> None:
    _OUTPUT(value, path)
    seen = set()
    for i, judgment in enumerate(value["judgments"]):
        here = f"{path}.judgments[{i}]"
        if (judgment["target_kind"] == "none") != (judgment["entity_id"] is None):
            raise SchemaError(f"{here}.entity_id: is null exactly when target_kind is none")
        if abs(sum(judgment["direction_probs"]) - 1.0) > 1e-6:
            raise SchemaError(f"{here}.direction_probs: must sum to 1")
        key = (judgment["target_kind"], judgment["entity_id"])
        if key in seen:
            raise SchemaError(f"{here}: the same target is judged twice")
        seen.add(key)


def check_against_input(body: dict, payload: dict) -> None:
    """A judgment may name only a target the host offered."""
    offered = {(c["target_kind"], c["entity_id"]) for c in payload["candidates"]}
    for i, judgment in enumerate(body["judgments"]):
        key = (judgment["target_kind"], judgment["entity_id"])
        if key[0] != "none" and key not in offered:
            raise SchemaError(f"$.judgments[{i}].entity_id: is not one of the candidates that were sent")


def ess_like(p_positive: float, p_negative: float) -> float:
    return 50.0 + 50.0 * (p_positive - p_negative)


def entropy(probabilities: list[float]) -> float:
    return -sum(p * math.log(p) for p in probabilities if p > 0)


_HOST = S.obj({
    "record_id": _ident, "source_id": _ident, "published_at": S.string(max_len=40),
    "received_at": S.string(max_len=40), "novelty_0_100": _score, "origin_cluster_id": _ident,
    "p_credibility": _prob, "market_confirmation": S.string(enum=MARKET_CONFIRMATION),
    "model_version": S.string(max_len=200), "prompt_sha256": S.string(pattern=r"[0-9a-f]{64}"),
})


def _timestamp(value: str, name: str) -> None:
    from datetime import datetime
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SchemaError(f"{name} is not ISO 8601") from None
    if ts.tzinfo is None:
        raise SchemaError(f"{name} must carry a timezone")


def assemble_score_record(judgment: dict, host_fields: dict) -> dict:
    """Join one model judgment with the host's fields into a ``didm-score-v0`` record.

    Nothing is defaulted: a missing host field is an error, so a record can never
    carry a novelty, credibility or confirmation value the pipeline did not set.
    """
    output_spec({"judgments": [judgment]}, "$")
    _HOST(host_fields, "$host")
    _timestamp(host_fields["published_at"], "published_at")
    _timestamp(host_fields["received_at"], "received_at")
    probs = [float(p) for p in judgment["direction_probs"]]
    values = {
        **{name: host_fields[name] for name in COPIED_FIELDS + HOST_ONLY_FIELDS},
        "target_kind": judgment["target_kind"],
        "entity_id": judgment["entity_id"],
        "relevance_0_100": judgment["relevance_0_100"],
        "event_type": judgment["event_type"],
        "direction_probs": probs,
        "ess_like_0_100": ess_like(probs[0], probs[1]),
        "uncertainty_entropy": entropy(probs),
    }
    record = {name: values[name] for name in RECORD_FIELDS}
    record["schema_version"] = SCORE_SCHEMA_VERSION
    return record
