"""QSS v0: one standard card for a strategy, a distribution model or a pricing/forecast model.

The fields come from the 34 stored research cards (three kinds: strategy,
distribution, model). A QSS document is strict JSON: the stored cards hold NaN
in a few statistics, and QSS writes those as ``{"$nonfinite": "NaN"}`` so that
any JSON parser reads the document.

Two stages:

* ``draft``    what a person or the language model writes: hypothesis, rules,
               market, data, costs, protocol, planned trials. A draft carries no
               evidence and no decision, so a model cannot hand itself a PASS.
* ``recorded`` a card the validation gate has run: evidence, decision and
               provenance are required.

``card_to_qss`` and ``qss_to_card`` are inverses on recorded cards, key order
included, so a stored card file is reproduced byte for byte.
"""
from __future__ import annotations

import json
import math
from typing import Any

from ..checks import schema as S
from ..checks.schema import SchemaError

QSS_VERSION = "qss-v0"
KINDS = ("strategy", "distribution", "model")
VERDICTS = ("PASS", "REVISE", "REJECT")
STAGES = ("draft", "recorded")
NONFINITE_KEY = "$nonfinite"
_NONFINITE = {"NaN": math.nan, "+Infinity": math.inf, "-Infinity": -math.inf}

# Top-level key order of a stored card (identical in all 34 files).
CARD_KEYS = ("card_id", "kind", "hypothesis", "rules", "universe", "data", "costs", "protocol", "trials",
             "seed", "stats", "tests", "decision", "decision_reason", "revise_target", "lines",
             "decay_haircut", "created", "author", "results_file", "results_md5", "citations")

_CARD_ID = r"[A-Za-z][A-Za-z0-9_]{1,63}"
_free = S.json_object()
_trials_draft = S.obj({"n_planned": S.integer(lo=1)})
_trials_recorded = S.obj({"n_planned": S.integer(lo=1), "n_total": S.integer(lo=1),
                          "ledger": S.array(S.string(max_len=2000))})

_COMMON = {
    "qss_version": S.const(QSS_VERSION),
    "stage": S.string(enum=STAGES),
    "card_id": S.string(pattern=_CARD_ID),
    "kind": S.string(enum=KINDS),
    "hypothesis": S.string(max_len=2000),
    "rules": _free,        # signal and risk rules
    "market": _free,       # symbols, venue, curve, board ...
    "data": _free,         # source, start/end or as_of, sessions
    "costs": _free,
    "protocol": _free,     # walk-forward windows, bootstrap, confidence level
    "seed": S.integer(lo=0),
}
_DRAFT = S.obj({**_COMMON, "stage": S.const("draft"), "trials": _trials_draft})
_RECORDED = S.obj({
    **_COMMON,
    "stage": S.const("recorded"),
    "trials": _trials_recorded,
    "evidence": S.obj({
        "stats": _free,
        "tests": _free,
        "lines": S.array(S.string(max_len=4000)),
        "results_file": S.string(max_len=400),
        "results_md5": S.string(pattern=r"[0-9a-f]{32}"),
    }),
    "decision": S.obj({
        "verdict": S.string(enum=VERDICTS),
        "reason": S.string(max_len=2000),
        "revise_target": S.nullable(S.string(max_len=2000)),
    }),
    "decay_haircut": S.obj({"factor": S.number(lo=0.0, hi=1.0), "source": S.string(max_len=400)}),
    "provenance": S.obj({
        "created": S.iso_date(),
        "author": S.string(max_len=200),
        "citations": S.array(S.string(max_len=400)),
    }),
})


def validate_qss(doc: Any, stage: str | None = None) -> dict:
    """Return ``doc`` when it is a valid QSS v0 document, else raise SchemaError."""
    if not isinstance(doc, dict):
        raise SchemaError("$: must be an object")
    actual = doc.get("stage")
    if actual not in STAGES:
        raise SchemaError(f"$.stage: must be one of {list(STAGES)}")
    if stage is not None and actual != stage:
        raise SchemaError(f"$.stage: must be {stage!r}")
    (_DRAFT if actual == "draft" else _RECORDED)(doc, "$")
    if actual == "recorded":
        trials = doc["trials"]
        if trials["n_total"] < trials["n_planned"]:
            raise SchemaError("$.trials.n_total: must be at least n_planned")
        _strategy_gate_fields(doc)
    return doc


def _strategy_gate_fields(doc: dict) -> None:
    """A PASS strategy card must show the trial-aware tests it passed."""
    if doc["kind"] != "strategy" or doc["decision"]["verdict"] != "PASS":
        return
    for name in ("dsr", "pbo"):
        if name not in doc["evidence"]["tests"]:
            raise SchemaError(f"$.evidence.tests.{name}: is required on a PASS strategy card")


# --------------------------------------------------------------------------- #
# Stored card <-> QSS
# --------------------------------------------------------------------------- #
def _encode(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        label = "NaN" if math.isnan(value) else ("+Infinity" if value > 0 else "-Infinity")
        return {NONFINITE_KEY: label}
    if isinstance(value, dict):
        if NONFINITE_KEY in value:
            raise SchemaError(f"a card may not use the reserved key {NONFINITE_KEY}")
        return {k: _encode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_encode(v) for v in value]
    return value


def _decode(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {NONFINITE_KEY}:
            label = value[NONFINITE_KEY]
            if label not in _NONFINITE:
                raise SchemaError(f"unknown {NONFINITE_KEY} label: {label!r}")
            return _NONFINITE[label]
        return {k: _decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_decode(v) for v in value]
    return value


def card_to_qss(card: dict) -> dict:
    """Convert a stored research card into a recorded QSS v0 document."""
    if not isinstance(card, dict):
        raise SchemaError("card must be an object")
    if tuple(card) != CARD_KEYS:
        missing = [k for k in CARD_KEYS if k not in card]
        extra = [k for k in card if k not in CARD_KEYS]
        raise SchemaError(f"card keys differ from the stored layout (missing {missing}, extra {extra}, "
                          "or a different order)")
    trials = card["trials"]
    if not isinstance(trials, dict) or tuple(trials) != ("N_planned", "N_total", "ledger"):
        raise SchemaError("card.trials must hold N_planned, N_total, ledger in that order")
    haircut = card["decay_haircut"]
    if not isinstance(haircut, dict) or tuple(haircut) != ("factor", "source"):
        raise SchemaError("card.decay_haircut must hold factor, source in that order")
    doc = {
        "qss_version": QSS_VERSION,
        "stage": "recorded",
        "card_id": card["card_id"],
        "kind": card["kind"],
        "hypothesis": card["hypothesis"],
        "rules": _encode(card["rules"]),
        "market": _encode(card["universe"]),
        "data": _encode(card["data"]),
        "costs": _encode(card["costs"]),
        "protocol": _encode(card["protocol"]),
        "trials": {"n_planned": trials["N_planned"], "n_total": trials["N_total"], "ledger": trials["ledger"]},
        "seed": card["seed"],
        "evidence": {
            "stats": _encode(card["stats"]),
            "tests": _encode(card["tests"]),
            "lines": card["lines"],
            "results_file": card["results_file"],
            "results_md5": card["results_md5"],
        },
        "decision": {"verdict": card["decision"], "reason": card["decision_reason"],
                     "revise_target": card["revise_target"]},
        "decay_haircut": _encode(haircut),
        "provenance": {"created": card["created"], "author": card["author"], "citations": card["citations"]},
    }
    return validate_qss(doc, "recorded")


def qss_to_card(doc: dict) -> dict:
    """Convert a recorded QSS v0 document back into the stored card layout."""
    validate_qss(doc, "recorded")
    evidence, decision, provenance, trials = doc["evidence"], doc["decision"], doc["provenance"], doc["trials"]
    return {
        "card_id": doc["card_id"],
        "kind": doc["kind"],
        "hypothesis": doc["hypothesis"],
        "rules": _decode(doc["rules"]),
        "universe": _decode(doc["market"]),
        "data": _decode(doc["data"]),
        "costs": _decode(doc["costs"]),
        "protocol": _decode(doc["protocol"]),
        "trials": {"N_planned": trials["n_planned"], "N_total": trials["n_total"], "ledger": trials["ledger"]},
        "seed": doc["seed"],
        "stats": _decode(evidence["stats"]),
        "tests": _decode(evidence["tests"]),
        "decision": decision["verdict"],
        "decision_reason": decision["reason"],
        "revise_target": decision["revise_target"],
        "lines": evidence["lines"],
        "decay_haircut": _decode(doc["decay_haircut"]),
        "created": provenance["created"],
        "author": provenance["author"],
        "results_file": evidence["results_file"],
        "results_md5": evidence["results_md5"],
        "citations": provenance["citations"],
    }


def card_text(card: dict) -> str:
    """Serialise a card exactly as the stored files are written."""
    return json.dumps(card, indent=1, ensure_ascii=False)


def qss_text(doc: dict) -> str:
    """Serialise a QSS document as strict JSON (NaN and Infinity are refused)."""
    return json.dumps(doc, indent=1, ensure_ascii=False, allow_nan=False)


def draft_from(card_id: str, kind: str, hypothesis: str, *, rules: dict, market: dict, data: dict,
               costs: dict | None = None, protocol: dict | None = None, n_planned: int = 1,
               seed: int = 0) -> dict:
    return validate_qss({
        "qss_version": QSS_VERSION, "stage": "draft", "card_id": card_id, "kind": kind,
        "hypothesis": hypothesis, "rules": rules, "market": market, "data": data,
        "costs": costs or {}, "protocol": protocol or {}, "trials": {"n_planned": n_planned}, "seed": seed,
    }, "draft")
