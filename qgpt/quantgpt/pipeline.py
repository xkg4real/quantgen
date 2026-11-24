"""One request, one envelope.

    admit -> generate -> parse -> output contract -> policy -> numbers -> citations -> look-ahead -> envelope

Every step that fails ends in an envelope without a body. The order is fixed:
a blocked answer is reported as blocked even when it would also be an
abstention, and a malformed answer is an error before anything in it is read.

The model writes ``{"body": {...}, "citations": [{"source_id", "as_of"}]}``.
The numbers list, the policy record, the model record, the label and the
request hash are written here, never by the model.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from . import envelope as E
from .backends.base import FINISH_REASONS, BackendError
from .checks import numbers as N
from .checks import schema as S
from .checks.citations import check_citations
from .checks.leakage import check_leakage
from .checks.schema import SchemaError
from .contracts.tasks import CONTRACTS, validate_output
from .policy import Rules, decide, free_chat
from .router import admit

_MODEL_OUTPUT = S.obj({"body": S.json_object()},
                      {"citations": S.array(S.obj({"source_id": S.string(max_len=128), "as_of": S.iso_date()}),
                                            max_len=50)})
_REQUEST_TEXT = {"T-QA": "question", "T-CARD": "text", "T-RESEARCH": "topic"}


@dataclass(frozen=True)
class Settings:
    rules: Rules
    prompt_version: str = "p0"
    label_ko: str = N.LABEL["ko"]
    max_tokens: int = 4000
    enabled: bool = True
    evidence: Mapping[str, str] = field(default_factory=dict)      # source_id -> as_of of what was sent
    events: Sequence[Mapping] = ()                                  # dated events for the look-ahead check
    clock: Callable[[], float] = time.monotonic


def run(request: Any, backend: Any, settings: Settings) -> dict:
    """Answer one request. Always returns a valid ``qgpt-env-v1`` envelope."""
    started = settings.clock()
    task = request.get("task") if isinstance(request, dict) else None
    mode = request.get("mode") if isinstance(request, dict) else None
    payload = request.get("input") if isinstance(request, dict) else None
    known_task = task if isinstance(task, str) and task in E.TASKS else None
    known_mode = mode if mode in E.MODES else "tool"
    try:
        request_hash = E.request_sha256(str(task), str(mode), payload, backend.model_id, backend.adapter,
                                        settings.prompt_version)
    except (ValueError, TypeError):
        request_hash = E.request_sha256(str(task), str(mode), None, backend.model_id, backend.adapter,
                                        settings.prompt_version)

    def out(status: str, reason: str, violations: tuple = (), numbers: tuple = (), citations: tuple = ()) -> dict:
        env = E.refusal(known_task, known_mode, status, reason, request_hash=request_hash,
                        model_id=backend.model_id, adapter=backend.adapter,
                        prompt_version=settings.prompt_version, rules_version=settings.rules.version,
                        label_ko=settings.label_ko, violations=violations,
                        latency_ms=_elapsed(settings, started))
        env["numbers"], env["citations"] = list(numbers), list(citations)
        return E.validate_envelope(env)

    refused = admit(request, enabled=settings.enabled)
    if refused is not None:
        status, reason = refused
        return out(status, reason, free_chat(settings.rules).violations if reason == "no_task_code" else ())

    contract = CONTRACTS[task]
    try:
        generation = backend.generate(task, mode, payload, prompt_version=settings.prompt_version,
                                      max_tokens=settings.max_tokens)
    except BackendError:
        return out("error", "backend")
    if generation.finish_reason not in FINISH_REASONS:
        return out("error", "backend")
    if generation.finish_reason == "length":
        return out("error", "truncated")
    try:
        produced = json.loads(generation.text, parse_constant=_no_constants)
        _MODEL_OUTPUT(produced, "$")
        body = validate_output(task, produced["body"], payload)
    except (ValueError, SchemaError):
        return out("error", "invalid_output")
    citations = tuple(produced.get("citations", ()))
    text = N.text_of(body)

    policy = decide(text, mode, settings.rules)
    if policy.blocked:
        return out("blocked", "policy", policy.violations)

    data = payload.get(contract.numbers_from) if contract.numbers_from else {}
    question = payload.get(_REQUEST_TEXT.get(task, ""), "") if isinstance(payload, dict) else ""
    numbers = N.decide(text, data, question, mode=mode) if task != "T-NEWS" else N.NumberDecision(False, (), ())
    if numbers.abstain:
        return out("abstain", "number_not_in_payload", policy.violations, numbers.numbers, citations)

    as_of = payload.get("as_of") if isinstance(payload, dict) else None
    cited = check_citations(citations, settings.evidence, as_of=as_of, required=contract.needs_citation)
    if not cited.ok:                       # evidence and dates are checked in both modes
        return out("abstain", cited.reason_code, policy.violations, numbers.numbers)
    if as_of and not check_leakage(text, as_of, settings.events).ok:
        return out("abstain", "after_as_of", policy.violations, numbers.numbers, citations)

    return E.validate_envelope({
        "envelope_version": E.ENVELOPE_VERSION, "task": task, "mode": mode, "status": "ok", "body": body,
        "numbers": list(numbers.numbers), "citations": list(citations), "policy": policy.as_envelope(),
        "model": {"id": backend.model_id, "adapter": backend.adapter, "prompt_version": settings.prompt_version},
        "label_ko": settings.label_ko, "latency_ms": _elapsed(settings, started), "request_sha256": request_hash,
    }, contract.output)


def _elapsed(settings: Settings, started: float) -> int:
    return max(0, int(round((settings.clock() - started) * 1000)))


def _no_constants(token: str) -> None:
    raise ValueError(f"{token} is not strict JSON")
