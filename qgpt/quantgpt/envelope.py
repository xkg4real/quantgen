"""Common output envelope ``qgpt-env-v1``.

Every QuantGPT answer leaves the package inside this envelope. The host shows
``body`` only when ``status`` is ``ok``; use ``display_body`` rather than reading
``body`` directly.

Rules beyond field shapes:

* ``ok`` needs an object body; any other status carries no body, only an
  optional ``reason_code``.
* In ``tool`` mode an ``ok`` envelope has no policy violation and no cited number
  that is missing from the payload. In ``owner`` mode both are recorded only.
* T-RESEARCH exists in ``owner`` mode only.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from .checks import schema as S
from .checks.schema import SchemaError

ENVELOPE_VERSION = "qgpt-env-v1"
TASKS = ("T-EXPLAIN", "T-CARD", "T-QA", "T-PORT", "T-RESEARCH", "T-REPORT", "T-NEWS")
OWNER_ONLY_TASKS = ("T-RESEARCH",)
MODES = ("tool", "owner")
STATUSES = ("ok", "abstain", "blocked", "error")
POLICY_RULES = ("PF-1", "PF-2", "PF-3", "PF-4", "PF-5", "PF-6")
REASON_CODES = (
    "no_evidence",            # abstain: nothing in the evidence store supports an answer
    "number_not_in_payload",  # abstain: a cited number is not in the data that was sent
    "citation_unknown",       # abstain: a cited source is not in the evidence that was sent
    "after_as_of",            # abstain: the answer refers to something later than as_of
    "policy",                 # blocked: a policy rule fired
    "no_task_code",           # blocked: a request without a task code (free chat)
    "task_not_allowed",       # blocked: the task is not offered in this mode
    "disabled",               # blocked: the feature is switched off in this build
    "invalid_input",          # error: the request does not satisfy the input contract
    "invalid_output",         # error: the model output does not satisfy the output contract
    "backend",                # error: the backend failed or timed out
    "truncated",              # error: generation stopped at the length limit
)
_STATUS_REASONS = {
    "abstain": ("no_evidence", "number_not_in_payload", "citation_unknown", "after_as_of"),
    "blocked": ("policy", "no_task_code", "task_not_allowed", "disabled"),
    "error": ("invalid_input", "invalid_output", "backend", "truncated"),
}

_SHA256 = r"[0-9a-f]{64}"
_ENVELOPE = S.obj(
    {
        "envelope_version": S.const(ENVELOPE_VERSION),
        "task": S.nullable(S.string(enum=TASKS)),       # null only for a request that named no task
        "mode": S.string(enum=MODES),
        "status": S.string(enum=STATUSES),
        "body": S.nullable(S.json_object()),
        "numbers": S.array(S.obj({"text": S.string(max_len=80), "found_in_payload": S.boolean()})),
        "citations": S.array(S.obj({"source_id": S.string(max_len=128, pattern=r"[A-Za-z0-9][A-Za-z0-9_.:\-/]*"),
                                    "as_of": S.iso_date()})),
        "policy": S.obj({"violations": S.array(S.string(enum=POLICY_RULES), unique=True),
                         "rules_version": S.string(max_len=64)}),
        "model": S.obj({"id": S.string(max_len=200), "adapter": S.nullable(S.string(max_len=200)),
                        "prompt_version": S.string(max_len=64)}),
        "label_ko": S.string(max_len=400),
        "latency_ms": S.integer(lo=0),
        "request_sha256": S.string(pattern=_SHA256),
    },
    {"reason_code": S.string(enum=REASON_CODES)},
)


def canonical_json(value: Any) -> str:
    """Deterministic strict JSON: sorted keys, no spaces, NaN refused."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def request_sha256(task: str, mode: str, payload: Any, model_id: str, adapter: str | None,
                   prompt_version: str) -> str:
    """Hash of everything that decides the answer, for replay and audit."""
    blob = canonical_json({"task": task, "mode": mode, "input": payload, "model": model_id,
                           "adapter": adapter, "prompt_version": prompt_version})
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate_envelope(env: Any, body_spec: Callable[[Any, str], None] | None = None) -> dict:
    """Return ``env`` when it is a valid envelope, else raise SchemaError.

    ``body_spec`` is the task's output contract; it is applied to an ``ok`` body.
    """
    _ENVELOPE(env, "$")
    status, mode, task = env["status"], env["mode"], env["task"]
    if task is None and (status != "blocked" or env.get("reason_code") != "no_task_code"):
        raise SchemaError("$.task: is null only when a request without a task code was blocked")
    if task in OWNER_ONLY_TASKS and mode != "owner" and status == "ok":
        raise SchemaError(f"$.task: {task} is not offered in {mode} mode")
    if status == "ok":
        if env["body"] is None:
            raise SchemaError("$.body: is required when status is ok")
        if "reason_code" in env:
            raise SchemaError("$.reason_code: is not allowed when status is ok")
        if mode == "tool":
            if env["policy"]["violations"]:
                raise SchemaError("$.policy.violations: an ok envelope in tool mode has none")
            if any(not n["found_in_payload"] for n in env["numbers"]):
                raise SchemaError("$.numbers: an ok envelope in tool mode cites only numbers found in the payload")
        if body_spec is not None:
            body_spec(env["body"], "$.body")
    else:
        if env["body"] is not None:
            raise SchemaError(f"$.body: must be null when status is {status}")
        reason = env.get("reason_code")
        if reason is not None and reason not in _STATUS_REASONS[status]:
            raise SchemaError(f"$.reason_code: {reason} does not belong to status {status}")
    return env


def display_body(env: dict) -> dict | None:
    """The only body a host may show: the body of a valid ``ok`` envelope."""
    try:
        validate_envelope(env)
    except SchemaError:
        return None
    return env["body"] if env["status"] == "ok" else None


def refusal(task: str | None, mode: str, status: str, reason_code: str, *, request_hash: str, model_id: str,
            adapter: str | None, prompt_version: str, rules_version: str, label_ko: str,
            violations: tuple[str, ...] = (), latency_ms: int = 0) -> dict:
    """Build an envelope that carries no body (abstain, blocked or error)."""
    if status == "ok":
        raise SchemaError("refusal() cannot build an ok envelope")
    return validate_envelope({
        "envelope_version": ENVELOPE_VERSION, "task": task, "mode": mode, "status": status, "body": None,
        "reason_code": reason_code, "numbers": [], "citations": [],
        "policy": {"violations": list(violations), "rules_version": rules_version},
        "model": {"id": model_id, "adapter": adapter, "prompt_version": prompt_version},
        "label_ko": label_ko, "latency_ms": latency_ms, "request_sha256": request_hash,
    })
