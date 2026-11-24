"""Input and output contracts for the seven task types.

Each contract is a pair of specs. An output contract lists every field the
model may write; anything else is rejected, so there is no place for an order,
a recommended action or a target price to ride along.

Free text inside a body is still checked afterwards by the policy filter and by
the number, citation and look-ahead checks; a contract only fixes the shape.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..checks import schema as S
from ..checks.schema import SchemaError, Spec
from . import news, qss

LANGUAGES = ("ko", "en")
_lang = S.string(enum=LANGUAGES)
_para = S.string(max_len=4000)
_line = S.string(max_len=600)
_lines = S.array(_line, max_len=12)
_points = S.array(_line, min_len=1, max_len=12)
_ident = S.string(max_len=128, pattern=r"[A-Za-z0-9][A-Za-z0-9_.:\-/]*")
_payload = S.json_object(max_depth=10)


@dataclass(frozen=True)
class Contract:
    task: str
    modes: tuple[str, ...]
    input: Spec
    output: Spec
    needs_citation: bool = False      # an ok answer must cite at least one source
    numbers_from: str | None = None   # input field whose values the cited numbers are compared with


# T-EXPLAIN: explain a report the application has already calculated.
_explain_in = S.obj({"report": _payload, "language": _lang}, {"focus": S.string(max_len=200)})
_explain_out = S.obj({"summary": _para, "points": _points}, {"caveats": _lines})

# T-CARD: a strategy described in words -> a draft strategy card (QSS v0, no evidence, no decision).
_card_in = S.obj({"text": S.string(max_len=6000), "language": _lang}, {"kind": S.string(enum=qss.KINDS)})


def _card_out(value: Any, path: str) -> None:
    S.obj({"card": S.json_object(), "open_fields": S.array(S.string(max_len=80), max_len=20, unique=True)},
          {"assumptions": _lines})(value, path)
    try:
        qss.validate_qss(value["card"], "draft")
    except SchemaError as exc:
        raise SchemaError(f"{path}.card: {exc}") from None


# T-QA: a general concept question answered from the evidence store, or an abstention.
_qa_in = S.obj({"question": S.string(max_len=1000), "as_of": S.iso_date(), "language": _lang})
_qa_out = S.obj({"answer": _para}, {"caveats": _lines})

# T-PORT: explain portfolio diagnostics the application calculated. Observations only.
_port_in = S.obj({"diagnostics": _payload, "language": _lang})
_port_out = S.obj({"summary": _para, "observations": _points}, {"caveats": _lines})

# T-RESEARCH (owner mode only): a research hypothesis as a pre-registration file, nothing else.
_research_in = S.obj({"topic": S.string(max_len=2000), "as_of": S.iso_date(), "language": _lang},
                     {"context": _payload})
_research_out = S.obj({"prereg": S.obj({
    "title": _line,
    "hypothesis": S.string(max_len=2000),
    "null_hypothesis": S.string(max_len=2000),
    "data": S.obj({"sources": S.array(_line, min_len=1, max_len=20), "start": S.iso_date(),
                   "end": S.iso_date()}),
    "primary_metric": _line,
    "test": _line,
    "n_trials_planned": S.integer(lo=1, hi=100000),
    "stop_rule": _line,
    "as_of": S.iso_date(),
})}, {"prior_work": _lines})

# T-REPORT: summarise ledger rows and experiment records the host passes in.
_report_in = S.obj({"rows": S.array(_payload, min_len=1, max_len=2000),
                    "period": S.obj({"start": S.iso_date(), "end": S.iso_date()}), "language": _lang},
                   {"title": _line})
_report_out = S.obj({"summary": _para,
                     "sections": S.array(S.obj({"title": _line, "text": _para}), min_len=1, max_len=12)},
                    {"caveats": _lines})

CONTRACTS: dict[str, Contract] = {c.task: c for c in (
    Contract("T-EXPLAIN", ("tool", "owner"), _explain_in, _explain_out, numbers_from="report"),
    Contract("T-CARD", ("tool", "owner"), _card_in, _card_out),
    Contract("T-QA", ("tool", "owner"), _qa_in, _qa_out, needs_citation=True),
    Contract("T-PORT", ("tool", "owner"), _port_in, _port_out, numbers_from="diagnostics"),
    Contract("T-RESEARCH", ("owner",), _research_in, _research_out),
    Contract("T-REPORT", ("tool", "owner"), _report_in, _report_out, numbers_from="rows"),
    Contract("T-NEWS", ("tool", "owner"), news.INPUT, news.output_spec, numbers_from=None),
)}


def validate_input(task: str, payload: Any) -> Any:
    contract = _contract(task)
    contract.input(payload, "$")
    _cross_input(task, payload)
    return payload


def validate_output(task: str, body: Any, payload: Any | None = None) -> Any:
    contract = _contract(task)
    contract.output(body, "$")
    if task == "T-NEWS" and payload is not None:
        news.check_against_input(body, payload)
    if task == "T-RESEARCH":
        _ordered(body["prereg"]["data"], "$.prereg.data")
    return body


def _contract(task: str) -> Contract:
    if task not in CONTRACTS:
        raise SchemaError(f"unknown task code: {task!r}")
    return CONTRACTS[task]


def _ordered(period: dict, path: str) -> None:
    if S.parse_as_of(period["start"]) > S.parse_as_of(period["end"]):
        raise SchemaError(f"{path}: start is after end")


def _cross_input(task: str, payload: dict) -> None:
    if task == "T-REPORT":
        _ordered(payload["period"], "$.period")
