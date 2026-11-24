"""DIDM-2 scorer contract: one interface for every scorer, and record assembly.

    request --> Scorer.judge() --> raw judgement --> validate_judgement()
                                                          |
    DIDM components (novelty, clustering, credibility,    v
    market confirmation, store timestamps) ----> assemble_record() --> ScoreRecord

A scorer is anything with ``info`` (a ScorerInfo) and ``judge(request)`` returning a
mapping in the ``didm-judgement-v0`` shape: an LLM wrapper, the in-house model, a
FinBERT or dictionary baseline. This module calls no model and reads no clock; the
caller injects the scorer and the DIDM-side values.

Rejected judgements are dropped and counted, never repaired (DIDM 9 "Schema enforcement").
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable

from core.didm.llm.judgement import (
    Judgement,
    JudgementError,
    ScoreRequest,
    check_record_ready,
    validate_judgement,
)
from core.didm.llm.schema import (
    SCHEMA_VERSION,
    ScoreRecord,
    SchemaError,
    TargetKind,
    entropy,
    ess_like,
    validate_record,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
UNCALIBRATED = "uncalibrated"

# Record fields DIDM supplies; the model never produces these.
ASSEMBLY_FIELDS = (
    "record_id",
    "source_id",
    "published_at",
    "received_at",
    "relevance_0_100",
    "novelty_0_100",
    "origin_cluster_id",
    "p_credibility",
    "market_confirmation",
)
# What an Assembly says it belongs to (not record fields of their own): checked against the judgement.
ASSEMBLY_KEYS = ("article_id", "target_kind", "entity_id")
# Record fields computed during assembly from the (calibrated) direction probabilities.
DERIVED_FIELDS = ("ess_like_0_100", "uncertainty_entropy")
# Record fields copied from the judgement or from the scorer's ScorerInfo.
JUDGEMENT_TO_RECORD = ("target_kind", "entity_id", "event_type", "direction_probs")
SCORER_INFO_FIELDS = ("model_version", "prompt_sha256")


@dataclass(frozen=True)
class ScorerInfo:
    """Fixed facts about a scorer, set by its wrapper (not model output).

    ``model_version`` is the pinned snapshot id and the key into
    docs/didm/MODEL_CUTOFFS.md. ``temperature`` must be 0 (PREREG_V0 5.7).
    Scorers with no prompt (dictionary, FinBERT) hash their fixed configuration text.
    """
    model_version: str
    prompt_sha256: str
    temperature: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.model_version, str) or not self.model_version.strip():
            raise JudgementError("model_version must be a non-empty string")
        if not isinstance(self.prompt_sha256, str) or not _SHA256.fullmatch(self.prompt_sha256):
            raise JudgementError("prompt_sha256 must be 64 lowercase hex characters")
        if isinstance(self.temperature, bool) or not isinstance(self.temperature, (int, float)) \
                or float(self.temperature) != 0.0:
            raise JudgementError("temperature must be 0")


@runtime_checkable
class Scorer(Protocol):
    info: ScorerInfo

    def judge(self, request: ScoreRequest) -> Mapping[str, Any]:
        """Return one raw judgement mapping for ``request`` (validated by the caller)."""


@dataclass(frozen=True)
class Assembly:
    """The DIDM-side values for one record (ASSEMBLY_FIELDS), and the article and target they were
    computed for (ASSEMBLY_KEYS). assemble_record refuses a judgement for another article or target."""
    article_id: str
    target_kind: str             # firm | macro | none
    entity_id: str | None
    record_id: str
    source_id: str
    published_at: str            # ISO 8601 with timezone
    received_at: str             # ISO 8601 with timezone; from the point-in-time store
    relevance_0_100: float       # relevance model (PREREG_V0 4.1, y = is_subject)
    novelty_0_100: float         # novelty model (core/didm/novelty.py)
    origin_cluster_id: str
    p_credibility: float
    market_confirmation: str


@dataclass(frozen=True)
class Assembled:
    record: ScoreRecord
    # PREREG_V0 5.7 asks for the calibration-map version with every record, and
    # didm-score-v0 has no field for it, so it travels next to the record.
    calibration_version: str
    raw_direction_probs: tuple[float, float, float]
    p_subject_raw: float
    claim_status: str


DirectionCalibrator = Callable[[tuple[float, float, float]], Sequence[float]]


def assemble_record(
    judgement: Judgement,
    info: ScorerInfo,
    assembly: Assembly,
    *,
    calibrate_direction: DirectionCalibrator | None = None,
    calibration_version: str = UNCALIBRATED,
) -> Assembled:
    """Join a validated judgement with DIDM's own values into a ``didm-score-v0`` record.

    ``calibrate_direction`` maps the raw direction probabilities to calibrated ones and
    must come with a ``calibration_version`` other than "uncalibrated"; without it the
    raw probabilities are used and the record is marked uncalibrated in the sidecar
    (uncalibrated probabilities are ranks only, PREREG_V0 1 A3). The assembled record is
    passed through ``validate_record``, so nothing leaves here that the schema rejects.
    """
    if not isinstance(judgement, Judgement):
        raise JudgementError("assemble_record needs a validated Judgement")
    if not isinstance(info, ScorerInfo) or not isinstance(assembly, Assembly):
        raise JudgementError("assemble_record needs a ScorerInfo and an Assembly")
    if not isinstance(calibration_version, str) or not calibration_version.strip():
        raise JudgementError("calibration_version must be a non-empty string")
    if (calibrate_direction is None) != (calibration_version == UNCALIBRATED):
        raise JudgementError("a calibrator needs a calibration_version, and a version needs a calibrator")

    if not isinstance(assembly.target_kind, str) or assembly.target_kind not in [k.value for k in TargetKind]:
        raise JudgementError("assembly target_kind must be firm, macro or none")
    if assembly.article_id != judgement.article_id:
        raise JudgementError("assembly is for another article")
    if assembly.target_kind != judgement.target_kind.value or assembly.entity_id != judgement.entity_id:
        raise JudgementError("assembly is for another target")

    direction = judgement.direction_probs
    if calibrate_direction is not None:
        direction = _checked_probs(calibrate_direction(direction))

    raw = {name: getattr(assembly, name) for name in ASSEMBLY_FIELDS}
    raw.update(
        target_kind=judgement.target_kind.value,
        entity_id=judgement.entity_id,
        event_type=judgement.event_type.value,
        direction_probs=list(direction),
        ess_like_0_100=ess_like(direction[0], direction[1]),
        uncertainty_entropy=entropy(direction),
        model_version=info.model_version,
        prompt_sha256=info.prompt_sha256,
        schema_version=SCHEMA_VERSION,
    )
    try:
        record = validate_record(raw)
    except OverflowError:            # an integer too large for a float among the DIDM-side values
        raise JudgementError("assembly values must be finite numbers") from None
    return Assembled(
        record=record,
        calibration_version=calibration_version,
        raw_direction_probs=judgement.direction_probs,
        p_subject_raw=judgement.p_subject,
        claim_status=judgement.claim_status,
    )


@dataclass(frozen=True)
class Batch:
    judgements: tuple[tuple[ScoreRequest, Judgement], ...]
    rejected: tuple[tuple[str, str], ...]     # (article_id, reason); the reason is a fixed rule text and
    #                                            never contains model output or article text

    @property
    def reject_counts(self) -> dict[str, int]:
        return dict(Counter(reason for _, reason in self.rejected))


SCORER_RAISED = "scorer raised a schema error"


def run_scorer(scorer: Scorer, requests: Sequence[ScoreRequest], *, calibrated: bool) -> Batch:
    """Judge each request once; keep valid judgements, count the rest. No retries.

    ``calibrated`` says how the batch will be assembled. False means the raw direction probabilities
    go into records unchanged, so a judgement the record schema would refuse (P(+1) + P(-1) above 1
    by more than 1e-9) is rejected and counted here, and everything kept can be assembled. True means
    a calibrator replaces the vector, and the raw vector only has to meet the documented 1e-6.

    A SchemaError raised by the scorer itself (for example output that was not JSON) is counted under
    one fixed reason; its message is not stored, since a wrapper may quote the model output there.
    Any other exception from the scorer is a failure of the run and propagates.
    """
    if not isinstance(calibrated, bool):
        raise JudgementError("calibrated must be True or False")
    if not isinstance(scorer, Scorer) or not isinstance(getattr(scorer, "info", None), ScorerInfo):
        raise JudgementError("scorer must have a ScorerInfo `info` and a `judge(request)` method")
    kept: list[tuple[ScoreRequest, Judgement]] = []
    rejected: list[tuple[str, str]] = []
    for request in requests:
        if not isinstance(request, ScoreRequest):
            raise JudgementError("requests must be ScoreRequest objects")
        try:
            raw = scorer.judge(request)
        except SchemaError:
            rejected.append((request.article_id, SCORER_RAISED))
            continue
        try:
            judgement = validate_judgement(raw, request)
            if not calibrated:
                check_record_ready(judgement)
        except JudgementError as exc:              # value-free rule text (core/didm/llm/judgement.py)
            rejected.append((request.article_id, str(exc)))
            continue
        kept.append((request, judgement))
    return Batch(tuple(kept), tuple(rejected))


def _checked_probs(value: Any) -> tuple[float, float, float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 3:
        raise JudgementError("calibrated direction_probs must be three numbers")
    out = []
    for p in value:
        try:
            ok = (not isinstance(p, bool) and isinstance(p, (int, float)) and math.isfinite(p)
                  and 0.0 <= p <= 1.0)
        except OverflowError:
            ok = False
        if not ok:
            raise JudgementError("calibrated direction_probs must be numbers in [0, 1]")
        out.append(float(p))
    if abs(sum(out) - 1.0) > 1e-6:
        raise JudgementError("calibrated direction_probs must sum to 1")
    return (out[0], out[1], out[2])
