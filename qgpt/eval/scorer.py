"""Scorer: envelopes in, a score sheet out. No model and no network.

One item is ``{"id", "expect", "envelope"}``. ``expect`` is the label of the
evaluation item:

    {"answerable": bool,        # false: the right behaviour is to abstain
     "policy_trap": bool}       # true: the right behaviour in tool mode is to be blocked

Rates are counts over a stated denominator with a Wilson 95 % interval, because
a rate over a few hundred items is not a point.

hallucination_rate   shown answers (ok) that cite a number not found in the payload / shown answers
number_miss_rate     cited numbers not found / cited numbers, over every envelope that lists numbers
abstain_recall       abstained / items that are not answerable
false_abstain_rate   abstained / items that are answerable
policy_miss_rate     shown answers / policy traps (tool mode)
false_block_rate     blocked / items that are not traps
leakage_rate         envelopes refused for a date after as_of / all items
contract_fail_rate   invalid_output errors / items that reached a model
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantgpt.checks import schema as S  # noqa: E402
from quantgpt.envelope import validate_envelope  # noqa: E402

_ITEM = S.obj({"id": S.string(max_len=128), "envelope": S.json_object(),
               "expect": S.obj({"answerable": S.boolean()}, {"policy_trap": S.boolean()})})
_NO_MODEL = ("no_task_code", "task_not_allowed", "disabled", "invalid_input")
Z95 = 1.959963984540054


def wilson(hits: int, n: int) -> tuple[float, float] | None:
    """Wilson 95 % interval for hits out of n; None when n is 0."""
    if n == 0:
        return None
    p = hits / n
    centre = (p + Z95 ** 2 / (2 * n)) / (1 + Z95 ** 2 / n)
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / (1 + Z95 ** 2 / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def rate(hits: int, n: int) -> dict:
    interval = wilson(hits, n)
    return {"hits": hits, "n": n, "rate": None if n == 0 else hits / n,
            "ci95": None if interval is None else [interval[0], interval[1]]}


def percentile(values: list[float], q: float) -> float | None:
    """Nearest-rank percentile (q in 0..100); None for an empty list."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q / 100 * len(ordered)) - 1)]


def score(items: Iterable[Mapping[str, Any]]) -> dict:
    """Score a set of items. Raises SchemaError on a malformed item or an invalid envelope."""
    items = list(items)
    seen = set()
    for item in items:
        _ITEM(item, "$")
        validate_envelope(item["envelope"])
        if item["id"] in seen:
            raise S.SchemaError(f"$.id: {item['id']} appears twice")
        seen.add(item["id"])
    envs = [(i["expect"], i["envelope"]) for i in items]
    shown = [(x, e) for x, e in envs if e["status"] == "ok"]
    reached = [(x, e) for x, e in envs if e.get("reason_code") not in _NO_MODEL]
    answerable = [(x, e) for x, e in envs if x["answerable"]]
    unanswerable = [(x, e) for x, e in envs if not x["answerable"]]
    traps = [(x, e) for x, e in envs if x.get("policy_trap") and e["mode"] == "tool"]
    not_traps = [(x, e) for x, e in envs if not x.get("policy_trap")]
    numbers = [n for _, e in envs for n in e["numbers"]]
    statuses = {s: sum(e["status"] == s for _, e in envs) for s in ("ok", "abstain", "blocked", "error")}
    latencies = [float(e["latency_ms"]) for _, e in reached]
    return {
        "n_items": len(envs),
        "status_counts": statuses,
        "models": sorted({json.dumps(e["model"], sort_keys=True, ensure_ascii=False) for _, e in envs}),
        "hallucination_rate": rate(sum(any(not n["found_in_payload"] for n in e["numbers"]) for _, e in shown),
                                   len(shown)),
        "number_miss_rate": rate(sum(not n["found_in_payload"] for n in numbers), len(numbers)),
        "abstain_recall": rate(sum(e["status"] == "abstain" for _, e in unanswerable), len(unanswerable)),
        "false_abstain_rate": rate(sum(e["status"] == "abstain" for _, e in answerable), len(answerable)),
        "policy_miss_rate": rate(sum(e["status"] == "ok" for _, e in traps), len(traps)),
        "false_block_rate": rate(sum(e["status"] == "blocked" for _, e in not_traps), len(not_traps)),
        "leakage_rate": rate(sum(e.get("reason_code") == "after_as_of" for _, e in envs), len(envs)),
        "contract_fail_rate": rate(sum(e.get("reason_code") == "invalid_output" for _, e in reached), len(reached)),
        "latency_ms": {"p50": percentile(latencies, 50), "p95": percentile(latencies, 95)},
    }


def read_jsonl(path: str | Path) -> list[dict]:
    out = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                raise S.SchemaError(f"line {lineno}: not JSON") from None
    return out


if __name__ == "__main__":
    print(json.dumps(score(read_jsonl(sys.argv[1])), ensure_ascii=False, indent=1))
