"""Detached Strategy Lab configuration keys, compatible with the existing writer.

These are planned keys, not registered trials, counts, verdicts or claims of
scientific equivalence. No source/provider, family registry, cost lookup, default
directory or ledger is consulted. Callers supply the rule ID, pair ordering flag
and resolved numeric cost; unresolved cost belongs outside this helper.

The writer's JSON roundtrip with ``default=str`` is intentional: integer/float
distinctions, tuple conversion and JSON object-key coercion are retained. An
arbitrary object's string conversion may be unstable or have effects; this helper
does not sandbox caller objects or promise semantic identity for them. Its own
code performs no I/O. Nonfinite numbers are refused, unlike the event codec's
null conversion. MD5 here is compatibility identity, not authentication.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json


class KeyBuildError(ValueError):
    """Inputs cannot form a supported Lab configuration key."""


def lab_config_ids(rule: str, is_pairs: bool, symbols: Sequence[str],
                   grid: Sequence[Mapping], cost_bps: int | float) -> list[dict]:
    """Return one ``{theta_index, config_id}`` per input grid position.

    Symbols are stripped/uppercased and sorted except for ordered pairs; repeats
    remain. Explicit symbols/cost override those keys inside each theta. Missing
    top-level optional key fields are null, and timing is always COMPLIANT, as in
    the unchanged ``register_trials`` writer. Duplicate configurations retain
    their distinct input indices; this function does not count or register them.

    Rule and pair flag are explicit inputs, not a rule-registry lookup. Cost must
    already be resolved; its numeric type and value are not normalized or checked
    against a table/floor. Inputs are not modified by this helper.
    """
    if not isinstance(rule, str) or not rule:
        raise KeyBuildError("rule must be a nonempty rule ID string")
    if type(is_pairs) is not bool:
        raise KeyBuildError("is_pairs must be a bool")
    if (not isinstance(symbols, Sequence) or isinstance(symbols, (str, bytes))
            or not all(isinstance(symbol, str) for symbol in symbols)):
        raise KeyBuildError("symbols must be a sequence of strings")
    if not isinstance(grid, Sequence) or isinstance(grid, (str, bytes)):
        raise KeyBuildError("grid must be a sequence of parameter mappings")
    if isinstance(cost_bps, bool) or not isinstance(cost_bps, (int, float)):
        raise KeyBuildError("cost_bps must be an already resolved numeric cost")

    normalized = [symbol.strip().upper() for symbol in symbols]
    if not is_pairs:
        normalized.sort()
    result = []
    try:
        # Also refuse unresolved/nonfinite costs for an empty grid. This does not
        # impose any positive-cost, table-rate or trading-eligibility rule.
        json.dumps(cost_bps, allow_nan=False)
        for index, theta in enumerate(grid):
            if not isinstance(theta, Mapping):
                raise KeyBuildError("each grid entry must be a parameter mapping")
            params = json.loads(json.dumps(
                dict(theta, symbols=list(normalized), cost_bps=cost_bps), default=str))
            key = {"rule": rule, "params": params, "estimator": None,
                   "window": None, "cap": None, "instrument_book": None,
                   "rebalance": None, "timing_class": "COMPLIANT",
                   "start_convention": None}
            raw = json.dumps(key, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
            result.append({"theta_index": index,
                           "config_id": hashlib.md5(raw, usedforsecurity=False).hexdigest()})
    except (TypeError, ValueError, OverflowError, RecursionError, UnicodeError) as exc:
        raise KeyBuildError("configuration cannot be represented as canonical JSON") from exc
    return result
