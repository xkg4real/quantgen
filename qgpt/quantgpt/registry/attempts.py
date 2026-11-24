"""Attempt ledger: every training, evaluation or backtest run is counted once, before its result exists.

One attempt = objective + data version + hyperparameters + seed + model version.
Changing any of the five is a new attempt. The ledger is a JSON-lines file with
a SHA-256 chain: each line stores the hash of its own content and of the
previous line's bytes, so an edited, dropped, moved or reformatted line is
found on the next read, and a broken chain refuses every read and write.

There is no way around it inside this package:

* the ledger has no method that changes or removes a line;
* a result can only be recorded for an attempt that is already in the ledger,
  and only once;
* the deflated Sharpe ratio is computed here, with the trial count and the
  dispersion taken from the ledger, never from the caller.

What a chain cannot show is that lines were cut off the end. ``head()`` returns
the hash to pin somewhere else (a commit, a result file); ``verify_chain`` takes
that pin and fails when the ledger no longer reaches it.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..checks import schema as S
from ..checks.schema import SchemaError
from ..envelope import canonical_json
from . import dsr as _dsr

IDENTITY = ("objective", "data_version", "hyperparameters", "seed", "model_version")
ROW_KINDS = ("attempt", "result")
_UTC = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)"
_NAME = r"[A-Za-z0-9][A-Za-z0-9_.:\-/]{0,127}"
_ATTEMPT = S.obj({
    "family": S.string(pattern=_NAME),
    "objective": S.string(max_len=400),
    "data_version": S.string(max_len=200),
    "hyperparameters": S.json_object(max_depth=6),
    "seed": S.integer(lo=0),
    "model_version": S.string(max_len=200),
    "run_utc": S.string(pattern=_UTC),
}, {"note": S.string(max_len=400)})
_RESULT = S.obj({
    "attempt_id": S.string(pattern=r"[0-9a-f]{64}"),
    "metrics": S.json_object(max_depth=4),
    "run_utc": S.string(pattern=_UTC),
}, {"sharpe_per_period": S.number(), "n_periods": S.integer(lo=3), "artifact_sha256": S.string(pattern=r"[0-9a-f]{64}")})
_CHAIN = ("prev_sha256", "row_sha256")


class LedgerRefused(ValueError):
    """The ledger refuses the row, or its chain does not verify."""


@dataclass(frozen=True)
class LedgerCheck:
    ok: bool
    n_rows: int
    first_bad_line: int | None = None
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


def attempt_id(row: Mapping[str, Any]) -> str:
    """SHA-256 of the five identity fields in canonical JSON."""
    return _sha(canonical_json({name: row[name] for name in IDENTITY}).encode("utf-8"))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _content_sha(row: Mapping[str, Any]) -> str:
    return _sha(canonical_json({k: v for k, v in row.items() if k not in _CHAIN}).encode("utf-8"))


class AttemptLedger:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    # -- reading -------------------------------------------------------------
    def _lines(self) -> list[bytes]:
        if not self._path.exists():
            return []
        raw = self._path.read_bytes().split(b"\n")
        if raw and raw[-1] == b"":
            raw.pop()
        return raw

    def verify_chain(self, pinned_head: str | None = None) -> LedgerCheck:
        prev, n, seen_attempts, seen_results, pin_seen = None, 0, set(), set(), pinned_head is None
        for lineno, raw in enumerate(self._lines(), start=1):
            try:
                row = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                return LedgerCheck(False, n, lineno, "unreadable line")
            if not isinstance(row, dict):
                return LedgerCheck(False, n, lineno, "not an object")
            try:
                canonical = canonical_json(row).encode("utf-8")
            except ValueError:
                return LedgerCheck(False, n, lineno, "not strict JSON")
            if canonical != raw:
                return LedgerCheck(False, n, lineno, "line is not its canonical JSON")
            if row.get("prev_sha256") != prev:
                return LedgerCheck(False, n, lineno, "prev_sha256 does not match the previous line")
            if row.get("row_sha256") != _content_sha(row):
                return LedgerCheck(False, n, lineno, "row_sha256 does not match the row content")
            kind = row.get("kind")
            body = {k: v for k, v in row.items() if k not in _CHAIN + ("kind", "attempt_id") or
                    (k == "attempt_id" and kind == "result")}
            try:
                if kind == "attempt":
                    _ATTEMPT(body, "$")
                    if row.get("attempt_id") != attempt_id(row) or row["attempt_id"] in seen_attempts:
                        return LedgerCheck(False, n, lineno, "attempt_id does not recompute or repeats")
                    seen_attempts.add(row["attempt_id"])
                elif kind == "result":
                    _RESULT(body, "$")
                    if row["attempt_id"] not in seen_attempts or row["attempt_id"] in seen_results:
                        return LedgerCheck(False, n, lineno, "result without an earlier attempt, or a second result")
                    seen_results.add(row["attempt_id"])
                else:
                    return LedgerCheck(False, n, lineno, "unknown row kind")
            except SchemaError as exc:
                return LedgerCheck(False, n, lineno, str(exc))
            prev = _sha(raw)
            pin_seen = pin_seen or prev == pinned_head
            n += 1
        if not pin_seen:
            return LedgerCheck(False, n, None, "the pinned head is not in this ledger: lines were removed or replaced")
        return LedgerCheck(True, n)

    def rows(self) -> list[dict]:
        check = self.verify_chain()
        if not check:
            raise LedgerRefused(f"{self._path.name}: chain broken at line {check.first_bad_line}: {check.reason}")
        return [json.loads(raw.decode("utf-8")) for raw in self._lines()]

    def head(self) -> str | None:
        """Hash of the last line's bytes (None for an empty ledger); pin it outside the ledger."""
        self.rows()
        lines = self._lines()
        return _sha(lines[-1]) if lines else None

    def attempts(self, family: str | None = None) -> list[dict]:
        return [r for r in self.rows() if r["kind"] == "attempt" and (family is None or r["family"] == family)]

    def results(self, family: str | None = None) -> dict[str, dict]:
        rows = self.rows()
        families = {r["attempt_id"]: r["family"] for r in rows if r["kind"] == "attempt"}
        return {r["attempt_id"]: r for r in rows
                if r["kind"] == "result" and (family is None or families[r["attempt_id"]] == family)}

    def n_trials(self, family: str) -> int:
        """Every attempt of the family counts, with or without a result."""
        return len(self.attempts(family))

    # -- writing: append only ------------------------------------------------
    def _append(self, row: dict) -> dict:
        lines = self._lines()
        row["prev_sha256"] = _sha(lines[-1]) if lines else None
        row["row_sha256"] = _content_sha(row)
        try:
            line = canonical_json(row).encode("utf-8")
        except ValueError as exc:
            raise LedgerRefused(str(exc)) from None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self._path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line + b"\n")
            os.fsync(fd)
        finally:
            os.close(fd)
        return row

    def register(self, attempt: Mapping[str, Any]) -> tuple[dict, bool]:
        """Count an attempt before it runs. Returns (row, appended); the same five fields append nothing."""
        try:
            _ATTEMPT(dict(attempt), "$")
        except SchemaError as exc:
            raise LedgerRefused(str(exc)) from None
        identity = attempt_id(attempt)
        for row in self.attempts():
            if row["attempt_id"] == identity:
                return row, False
        return self._append({"kind": "attempt", "attempt_id": identity, **dict(attempt)}), True

    def record_result(self, result: Mapping[str, Any]) -> dict:
        """Attach one result to a registered attempt. A second result for the same attempt is refused."""
        try:
            _RESULT(dict(result), "$")
        except SchemaError as exc:
            raise LedgerRefused(str(exc)) from None
        known = {row["attempt_id"] for row in self.attempts()}
        if result["attempt_id"] not in known:
            raise LedgerRefused("no such attempt: register it before it runs")
        if result["attempt_id"] in self.results():
            raise LedgerRefused("this attempt already has a result; a re-run is a new attempt")
        return self._append({"kind": "result", **dict(result)})

    # -- statistics that depend on the count ---------------------------------
    def deflated_sharpe(self, attempt: str, returns: Sequence[float]) -> dict:
        """Deflated Sharpe ratio of one attempt's per-period returns, discounted by its whole family.

        The trial count is every attempt of the family; the dispersion is the population
        standard deviation of the per-period Sharpe ratios the family has recorded.
        """
        families = {row["attempt_id"]: row["family"] for row in self.attempts()}
        if attempt not in families:
            raise LedgerRefused("no such attempt: register it before it runs")
        family = families[attempt]
        results = self.results(family)
        if attempt not in results or "sharpe_per_period" not in results[attempt]:
            raise LedgerRefused("record the attempt's result (with sharpe_per_period) before asking for its DSR")
        observed = _dsr.per_period_sharpe(returns)
        if abs(observed - results[attempt]["sharpe_per_period"]) > 1e-9:
            raise LedgerRefused("the returns do not reproduce the recorded sharpe_per_period")
        n = self.n_trials(family)
        recorded = [r["sharpe_per_period"] for r in results.values() if "sharpe_per_period" in r]
        sr_sd = _dsr.population_sd(recorded)
        return {"dsr": _dsr.deflated_sharpe(returns, n_trials=n, sr_sd=sr_sd), "n_trials": n,
                "n_with_result": len(recorded), "sr_sd": sr_sd,
                "expected_max_sharpe": _dsr.expected_max_sharpe(n, sr_sd), "family": family,
                "ledger_head": self.head()}
