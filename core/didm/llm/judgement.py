"""DIDM-2 model judgement, version 0 (``didm-judgement-v0``).

A ``didm-score-v0`` record (core/didm/llm/schema.py) carries fields no language model
can produce: the novelty-model output, the origin cluster, the credibility state, the
market confirmation and the time we received the article. So the contract is split:

* the **judgement** is the part a scorer (LLM, FinBERT wrapper, dictionary, the in-house
  model) returns for one article and one target;
* the **record** is assembled by DIDM from that judgement plus its own components
  (core/didm/llm/scorer.py ``assemble_record``).

Every scorer returns the same judgement shape, so baselines and LLMs are compared on
one footing (PREREG_V0 6, ablation order). Validation rejects instead of repairing:
unknown fields, missing fields and out-of-range values raise ``JudgementError``.

Error messages name the rule and the field, never the offending value: a scorer's output may
quote the article, and reject reasons are stored and counted (core/didm/llm/scorer.py).

Pure standard library; no network, no clock reads, no model calls.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from core.didm.llm.schema import (
    EventType,
    SchemaError,
    TargetKind,
    _enum,
    ess_like,
    _ident,
    _prob,
)

JUDGEMENT_VERSION = "didm-judgement-v0"
CLAIM_STATUSES = ("reported", "confirmed")
LANGUAGES = ("en", "ko")
SUM_TOLERANCE = 1e-6

# Field order is the contract: the JSON Schema export and the conformance fixtures follow it.
JUDGEMENT_REQUIRED = (
    "judgement_version",
    "article_id",
    "target_kind",
    "entity_id",
    "p_subject",
    "event_type",
    "event_type_probs",
    "direction_probs",
    "claim_status",
)

REQUEST_REQUIRED = ("article_id", "language", "title", "body", "target_kind", "entity_id", "entity_name")


class JudgementError(SchemaError):
    """A scorer's judgement (or a score request) does not satisfy the V0 contract."""


@dataclass(frozen=True)
class ScoreRequest:
    """What DIDM hands a scorer: one article and one candidate target.

    ``body`` may be None (headline-only feeds). ``entity_name`` is the display name
    shown to the model; a name-masked prompt passes the masked value (PREREG_V0 5.4).
    Article text lives only in memory here: it is never written into a judgement or a record.
    """
    article_id: str
    language: str
    title: str
    body: str | None
    target_kind: TargetKind
    entity_id: str | None
    entity_name: str | None


@dataclass(frozen=True)
class Judgement:
    """A validated V0 judgement. Build with validate_judgement()."""
    article_id: str
    target_kind: TargetKind
    entity_id: str | None
    p_subject: float                                # raw P(target is the subject), before calibration
    event_type: EventType
    event_type_probs: tuple[tuple[str, float], ...]  # (type value, probability) in EventType order
    direction_probs: tuple[float, float, float]     # raw (P(+1), P(-1), P(0)), before calibration
    claim_status: str
    judgement_version: str = JUDGEMENT_VERSION
    # Set by validate_judgement only; not part of the JSON shape (as_dict) and not compared. It ties the
    # object to the values that were validated, so a hand-built or edited copy is not "validated".
    seal: str = field(default="", repr=False, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "judgement_version": self.judgement_version,
            "article_id": self.article_id,
            "target_kind": self.target_kind.value,
            "entity_id": self.entity_id,
            "p_subject": self.p_subject,
            "event_type": self.event_type.value,
            "event_type_probs": dict(self.event_type_probs),
            "direction_probs": list(self.direction_probs),
            "claim_status": self.claim_status,
        }


def validate_request(raw: Mapping[str, Any]) -> ScoreRequest:
    if not isinstance(raw, Mapping):
        raise JudgementError("request must be a mapping")
    _exact_fields(raw, REQUEST_REQUIRED, "request")
    if raw["language"] not in LANGUAGES:
        raise JudgementError(f"language must be one of {list(LANGUAGES)}")
    title = raw["title"]
    if not isinstance(title, str) or not title.strip():
        raise JudgementError("title must be a non-empty string")
    body = raw["body"]
    if body is not None and not isinstance(body, str):
        raise JudgementError("body must be a string or null")
    kind, entity = _target(raw)
    name = raw["entity_name"]
    if kind is TargetKind.NONE:
        if name is not None:
            raise JudgementError("entity_name must be null when target_kind is none")
    elif not isinstance(name, str) or not name.strip():
        raise JudgementError("entity_name must be a non-empty string")
    return ScoreRequest(
        article_id=_wrap(_ident, raw["article_id"], "article_id"),
        language=raw["language"],
        title=title,
        body=body,
        target_kind=kind,
        entity_id=entity,
        entity_name=name,
    )


def validate_judgement(raw: Mapping[str, Any], request: ScoreRequest) -> Judgement:
    """Return a Judgement or raise JudgementError naming the first problem.

    ``request`` is required: the echoed ``article_id`` and target must equal the request's.
    A judgement for another article or another entity is rejected, never re-attached, so the
    entity in a record is always the one DIDM asked about and never one the model chose.
    """
    if not isinstance(request, ScoreRequest):
        raise JudgementError("validate_judgement needs the ScoreRequest the judgement answers")
    if not isinstance(raw, Mapping):
        raise JudgementError("judgement must be a mapping")
    _exact_fields(raw, JUDGEMENT_REQUIRED, "judgement")
    if raw["judgement_version"] != JUDGEMENT_VERSION:
        raise JudgementError(f"judgement_version must be {JUDGEMENT_VERSION}")

    article_id = _wrap(_ident, raw["article_id"], "article_id")
    kind, entity = _target(raw)
    if article_id != request.article_id:
        raise JudgementError("article_id does not match the request")
    if kind is not request.target_kind or entity != request.entity_id:
        raise JudgementError("target does not match the request")

    p_subject = _wrap(_prob, raw["p_subject"], "p_subject")
    if kind is TargetKind.NONE and p_subject != 0.0:
        raise JudgementError("p_subject must be 0 when target_kind is none")

    event_type = _wrap(_enum, EventType, raw["event_type"], "event_type")
    type_probs = _type_probs(raw["event_type_probs"])
    top = max(p for _, p in type_probs)
    if dict(type_probs)[event_type.value] < top:      # exact comparison; only an exact tie leaves a choice
        raise JudgementError("event_type must be a most probable key of event_type_probs")

    direction = raw["direction_probs"]
    if isinstance(direction, (str, bytes)) or not isinstance(direction, (list, tuple)) or len(direction) != 3:
        raise JudgementError("direction_probs must be [P(+1), P(-1), P(0)]")
    direction = tuple(_wrap(_prob, p, "direction_probs") for p in direction)
    if abs(sum(direction) - 1.0) > SUM_TOLERANCE:
        raise JudgementError("direction_probs must sum to 1")
    # The raw vector is held to the documented 1e-6 only. The record schema's tighter bound on
    # P(+1) + P(-1) (1e-9) applies where a raw vector goes into a record unchanged: see
    # check_record_ready(), used by run_scorer for batches assembled without a calibrator.

    claim = raw["claim_status"]
    if not isinstance(claim, str) or claim not in CLAIM_STATUSES:
        raise JudgementError(f"claim_status must be one of {list(CLAIM_STATUSES)}")

    checked = Judgement(
        article_id=article_id,
        target_kind=kind,
        entity_id=entity,
        p_subject=p_subject,
        event_type=event_type,
        event_type_probs=type_probs,
        direction_probs=direction,  # type: ignore[arg-type]
        claim_status=claim,
    )
    return replace(checked, seal=_seal(checked))


def _seal(judgement: Judgement) -> str:
    text = json.dumps(judgement.as_dict(), sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(("didm-judgement-validated|" + text).encode("utf-8")).hexdigest()


def is_validated(judgement: Any) -> bool:
    """True only for an object that validate_judgement returned and nobody has altered since.

    A Judgement built by hand, or changed with dataclasses.replace, has no matching seal. This guards
    against a caller's mistake (assembling something that skipped the request and sum checks); it is
    not a security boundary.
    """
    return isinstance(judgement, Judgement) and bool(judgement.seal) and judgement.seal == _seal(judgement)


def check_record_ready(judgement: Judgement) -> None:
    """Raise JudgementError if the RAW direction probabilities could not go into a record as they are.

    The record schema allows P(+1) + P(-1) to exceed 1 by 1e-9 only, tighter than the 1e-6 a raw
    vector may miss a sum of 1 by (a float32 softmax typically misses by about 3e-8). When a
    calibrator replaces the vector this does not matter; without one it does.
    """
    _wrap(ess_like, judgement.direction_probs[0], judgement.direction_probs[1])


# --- helpers ---

def _exact_fields(raw: Mapping[str, Any], required: tuple[str, ...], what: str) -> None:
    extra = set(raw) - set(required)
    if extra:
        raise JudgementError(f"unknown {what} fields")
    for name in required:
        if name not in raw:
            raise JudgementError(f"missing {what} field: {name}")


def _wrap(fn, *args):
    """Run a schema helper and re-raise its SchemaError as a JudgementError."""
    try:
        return fn(*args)
    except JudgementError:
        raise
    except SchemaError as exc:
        message = str(exc)
        if message.startswith("unknown "):          # schema._enum quotes the value; keep the rule only
            message = message.split(":", 1)[0]
        raise JudgementError(message) from None
    except OverflowError:                           # an integer too large for a float (schema._num)
        raise JudgementError(f"{args[-1]} must be finite") from None


def _target(raw: Mapping[str, Any]) -> tuple[TargetKind, str | None]:
    kind = _wrap(_enum, TargetKind, raw["target_kind"], "target_kind")
    entity = raw["entity_id"]
    if kind is TargetKind.NONE:
        if entity is not None:
            raise JudgementError("entity_id must be null when target_kind is none")
    else:
        _wrap(_ident, entity, "entity_id")
    return kind, entity


def _type_probs(value: Any) -> tuple[tuple[str, float], ...]:
    names = [e.value for e in EventType]
    if not isinstance(value, Mapping):
        raise JudgementError("event_type_probs must be an object keyed by event type")
    extra = set(value) - set(names)
    if extra:
        raise JudgementError("unknown event_type_probs keys")
    missing = [n for n in names if n not in value]
    if missing:
        raise JudgementError("missing event_type_probs keys")
    out = tuple((n, _wrap(_prob, value[n], "event_type_probs value")) for n in names)
    if abs(sum(p for _, p in out) - 1.0) > SUM_TOLERANCE:
        raise JudgementError("event_type_probs must sum to 1")
    return out


__all__ = [
    "CLAIM_STATUSES", "JUDGEMENT_REQUIRED", "JUDGEMENT_VERSION", "LANGUAGES", "REQUEST_REQUIRED",
    "Judgement", "JudgementError", "ScoreRequest", "check_record_ready", "is_validated", "validate_judgement", "validate_request",
]
