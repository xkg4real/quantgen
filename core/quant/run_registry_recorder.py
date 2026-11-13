"""Detached R3 lifecycle recorder with explicit stores and supplied metadata.

This is the headless lifecycle child, not the Lab adapter or a production
registry. No default directory, environment/configuration discovery, strategy,
ledger, price, fingerprint, series or shadow computation is performed here.
The caller supplies two stores on the same trusted path, a clock, a token
source and an outage sink. The caller also owns sync-folder screening before
constructing these stores. See the product note for the remaining integration.

Public hooks contain Exception and disable the recorder after the first error.
BaseException is deliberately not caught. Their boolean result is diagnostic;
the strategy's control flow must never depend on it. One instance belongs to one
run and one calling thread. Different instances coordinate through the store.
"""
from datetime import datetime, timedelta, timezone
import math
import re

from . import run_registry_codec as codec
from .run_registry_fold import STAGES
from .run_registry_store import AppendOutcomeUncertain, DuplicateEvent, SingleSegmentStore


SOURCE_PATHS = (
    "core/quant/strategies.py", "core/quant/validate.py",
    "core/quant/history.py", "core/quant/gate_ledger.py",
    "core/research/strategy_workflow.py", "core/quant/optimize.py",
    "core/quant/risk.py",
)
START_FIELDS = frozenset((
    "family", "family_id", "symbols_typed", "source_requested",
    "cost_bps_requested", "days", "bootstrap_B", "seed", "intent",
    "declaration_id", "planned", "fn_qualname", "fn_source_sha256",
    "fn_source_sha256_raw", "repo_anchor", "files", "gate_version",
    "canonical_panel", "env", "grid", "grid_sha256",
))
_RESERVED = frozenset(("schema", "event", "run_id", "recorded_utc", "writer",
                       "person", "parent_run_id", "row_md5", "prev_row_md5",
                       "nonfinite"))
_RANK = {stage: i for i, stage in enumerate(STAGES)}
_PNL = _RANK["PNL_COMPUTED"]
_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_PNL_FIELDS = frozenset(("symbols_resolved", "per_symbol", "span", "sessions",
                         "data_md5", "synthetic", "holdout_touched", "cost",
                         "registered", "keys_changed_by_symbol_resolution"))
_CLOSING_FIELDS = frozenset(("ledger_file", "ledger_stage", "bytes_before",
    "bytes_after", "rows_before", "rows_after", "hash_before", "hash_after",
    "market", "rows", "interleaved", "skipped", "stats", "sr_sd_daily",
    "oos_moments", "per_config", "chosen_last", "wf_note", "results_sha256",
    "series_ref", "series_error", "existing"))


class RecorderError(ValueError):
    """The supplied lifecycle or metadata is outside this recorder's contract."""


def _error(exc):
    try:
        message = str(exc)[:500]
        message.encode("utf-8")
    except Exception:
        message = "Exception message unavailable"
    return {"type": type(exc).__name__, "message": message}


def _keys(value, *, nullable):
    if value is None and nullable:
        return
    if type(value) is not list:
        raise RecorderError("Keys must be a list")
    for key in value:
        if (type(key) is not dict or set(key) != {"theta_index", "config_id"}
                or type(key["theta_index"]) is not int or key["theta_index"] < 0
                or type(key["config_id"]) is not str
                or _HEX32.fullmatch(key["config_id"]) is None):
            raise RecorderError("Invalid configuration key")


def _payload(value):
    if type(value) is not dict or any(type(k) is not str for k in value):
        raise RecorderError("Supply a plain payload dictionary")
    if _RESERVED.intersection(value):
        raise RecorderError("Payload cannot replace envelope fields")


class DetachedRecorder:
    """One guarded run, with no automatic integration or source collection.

    ``in_run_store`` and ``after_run_store`` are SingleSegmentStore instances
    for the same file, with lock budgets at most 2 and 10 seconds respectively.
    These bound lock acquisition only, not filesystem or callback execution.
    ``outage_sink(dict)`` is required; it must supply the durable outage writer
    in a future adapter. This class reports a sink failure in ``outage_error``.
    No sink is silently replaced with a default filesystem destination.
    """

    def __init__(self, *, in_run_store, after_run_store, clock, monotonic, token_source,
                 outage_sink, writer):
        if (type(in_run_store) is not SingleSegmentStore
                or type(after_run_store) is not SingleSegmentStore
                or in_run_store.path != after_run_store.path
                or not 0 <= in_run_store.lock_timeout <= 2
                or not 0 <= after_run_store.lock_timeout <= 10):
            raise RecorderError("Supply same-path stores with 2s/10s lock budgets")
        if not all(callable(x) for x in (clock, monotonic, token_source, outage_sink)):
            raise RecorderError("Clocks, token source and outage sink are required")
        if type(writer) is not str or not writer:
            raise RecorderError("Supply the actual writer identity")
        self._in_store, self._after_store = in_run_store, after_run_store
        self._clock, self._token, self._outage_sink = clock, token_source, outage_sink
        self._monotonic = monotonic
        self._last_tick = self._deadline = None
        self._writer = writer
        self._state = "NEW"
        self._run_id = None
        self._family_id = None
        self._symbols = []
        self._stage = "REQUESTED"
        self._start_at = self._last_at = None
        self._pnl_written = self._post_written = self._displayed = False
        self._run_error = None
        self._errors = []
        self._outage_error = None

    @property
    def state(self):
        return self._state

    @property
    def run_id(self):
        return self._run_id

    @property
    def stage(self):
        return self._stage

    @property
    def errors(self):
        return tuple(dict(e) for e in self._errors)

    @property
    def outage_error(self):
        return None if self._outage_error is None else dict(self._outage_error)

    def _now(self):
        at = self._clock()
        if type(at) is not datetime or at.utcoffset() != timedelta(0):
            raise RecorderError("Clock must return an aware UTC datetime")
        at = at.astimezone(timezone.utc)
        if self._last_at is not None and at < self._last_at:
            raise RecorderError("Clock moved backwards within this run")
        self._last_at = at
        return at

    def _guard(self, hook, action):
        if self._state in ("DISABLED", "FINISHED"):
            return False
        try:
            # One budget for the entire hook, including all duplicate-ID tries.
            # Neither clock is read implicitly: the adapter supplies both.
            self._deadline = self._tick() + (2 if hook in ("started", "pnl_computed") else 10)
            action()
            return True
        except Exception as exc:
            self._state = "DISABLED"
            error = {"hook": hook, **_error(exc)}
            self._errors.append(error)
            outage = {"recorded_utc": self._stamp(self._last_at),
                      "run_id": self._run_id, "family_id": self._family_id,
                      "symbols_typed": list(self._symbols), "stage": self._stage,
                      "error": dict(error)}
            try:
                self._outage_sink(outage)
            except Exception as failure:
                self._outage_error = _error(failure)
            return False

    @staticmethod
    def _stamp(at):
        return None if at is None else at.isoformat(timespec="microseconds").replace("+00:00", "Z")

    def _require_active(self):
        if self._state != "ACTIVE":
            raise RecorderError("STARTED must succeed first")

    def _tick(self):
        tick = self._monotonic()
        if (type(tick) not in (int, float) or not math.isfinite(tick)
                or (self._last_tick is not None and tick < self._last_tick)):
            raise RecorderError("Elapsed clock must be finite and monotonic")
        self._last_tick = tick
        return tick

    def _emit(self, kind, payload, *, inside, at=None, candidate_id=None):
        _payload(payload)
        at = self._now() if at is None else at
        event = dict(payload, schema=codec.SCHEMA, event=kind,
                     run_id=self._run_id if candidate_id is None else candidate_id,
                     recorded_utc=self._stamp(at), writer=self._writer)
        # Copy and normalise before a sink can retain or change the input.
        event = codec.decode_event_line(codec.encode_event_line(event))
        del event["row_md5"], event["prev_row_md5"]
        store = self._in_store if inside else self._after_store
        if not 0 <= store.lock_timeout <= (2 if inside else 10):
            raise RecorderError("Store lock budget changed")
        remaining = self._deadline - self._tick()
        if remaining < 0:
            raise RecorderError("Hook lock-acquisition budget exhausted")
        store.append(event, lock_timeout=min(store.lock_timeout, remaining))

    def started(self, payload):
        def action():
            if self._state != "NEW":
                raise RecorderError("STARTED is allowed once")
            _payload(payload)
            if set(payload) != START_FIELDS:
                raise RecorderError("STARTED needs the complete supplied metadata")
            family_id = payload["family_id"]
            symbols = payload["symbols_typed"]
            if type(family_id) is not str or type(symbols) is not list or any(type(s) is not str for s in symbols):
                raise RecorderError("Typed symbols must be strings")
            self._family_id, self._symbols = family_id, list(symbols)
            _keys(payload["planned"], nullable=True)
            files = payload["files"]
            if type(files) is not dict or set(files) != set(SOURCE_PATHS):
                raise RecorderError("Source identity must name the owner's seven Q12 paths")
            for digests in files.values():
                if (type(digests) is not dict or set(digests) != {"lf", "raw"}
                        or any(type(v) is not str or _HEX64.fullmatch(v) is None
                               for v in digests.values())):
                    raise RecorderError("Invalid supplied source digest")
            self._start_at = at = self._now()
            for _ in range(5):
                candidate = codec.make_run_id(family_id, at=at, token_source=self._token)
                try:
                    self._emit("STARTED", payload, inside=True, at=at, candidate_id=candidate)
                except DuplicateEvent:
                    # This ID belongs to another run. Do not name it as ours in
                    # an outage if every collision retry is exhausted.
                    self._run_id = None
                    continue
                except AppendOutcomeUncertain:
                    # The store attempted this append. Preserve the candidate
                    # for later inspection, without retrying it.
                    self._run_id = candidate
                    raise
                self._run_id = candidate
                self._state = "ACTIVE"
                return
            raise RecorderError("Five STARTED ID attempts collided")
        return self._guard("started", action)

    def advance(self, stage):
        """Remember an in-run stage without writing a PROGRESS event (ruling 9)."""
        def action():
            self._require_active()
            if (type(stage) is not str or stage not in _RANK
                    or stage in ("PNL_COMPUTED", "DISPLAYED") or self._post_written
                    or _RANK[stage] < _RANK[self._stage]
                    or (_RANK[stage] > _PNL and not self._pnl_written)):
                raise RecorderError("Invalid in-run stage transition")
            self._stage = stage
        return self._guard("advance", action)

    def pnl_computed(self, payload):
        def action():
            self._require_active()
            if self._pnl_written or self._post_written:
                raise RecorderError("PNL_COMPUTED is allowed once, inside the run")
            self._stage = "PNL_COMPUTED"
            _payload(payload)
            if set(payload) - _PNL_FIELDS:
                raise RecorderError("PNL payload has a field from another phase")
            _keys(payload.get("registered"), nullable=False)
            self._emit("PROGRESS", dict(payload, stage=self._stage), inside=True)
            self._pnl_written = True
        return self._guard("pnl_computed", action)

    def after_run(self, payload, *, displayed, error=None):
        """Write the closing PROGRESS after the calculation or its failure."""
        def action():
            self._require_active()
            if self._post_written or type(displayed) is not bool:
                raise RecorderError("Closing PROGRESS is allowed once")
            if error is not None and not isinstance(error, Exception):
                raise RecorderError("Supply an Exception or None")
            if displayed and not self._pnl_written:
                raise RecorderError("A displayed result needs PNL")
            _payload(payload)
            if set(payload) - _CLOSING_FIELDS:
                raise RecorderError("Closing payload has a field from another phase")
            self._displayed = displayed
            self._run_error = None if error is None else _error(error)
            if displayed:
                self._stage = "DISPLAYED"
            self._emit("PROGRESS", dict(payload, stage=self._stage, displayed=displayed), inside=False)
            self._post_written = True
        return self._guard("after_run", action)

    def _after_event(self, kind, payload):
        def action():
            self._require_active()
            if not self._post_written:
                raise RecorderError("Post-run events require the closing PROGRESS")
            self._emit(kind, payload, inside=False)
        return self._guard(kind.lower(), action)

    def fingerprint(self, payload):
        return self._after_event("FINGERPRINT", payload)

    def shadow(self, payload):
        return self._after_event("SHADOW", payload)

    def finish(self, *, error=None, aborted=False, class_summary=None):
        """Attempt FINISHED once; a missing closing PROGRESS is written first.

        Calling from a finally block cannot replace an ordinary run exception.
        Repeated calls after FINISHED or DISABLED are no-ops. A SHADOW payload's
        error does not change the original run's status.
        """
        def action():
            self._require_active()
            if type(aborted) is not bool or (error is not None and not isinstance(error, Exception)):
                raise RecorderError("Invalid terminal arguments")
            if error is not None:
                self._run_error = _error(error)
            if not self._post_written:
                self._emit("PROGRESS", {"stage": self._stage, "displayed": False}, inside=False)
                self._post_written = True
            status = ("ABORTED" if aborted else "COMPLETED" if self._displayed and self._run_error is None
                      else "FAILED_AFTER_STATS" if _RANK[self._stage] >= _PNL
                      else "FAILED_BEFORE_STATS")
            if class_summary is None:
                summary = {}
            else:
                if (type(class_summary) is not dict or any(type(k) is not str or type(v) is not int or v < 0
                                                         for k, v in class_summary.items())):
                    raise RecorderError("Class summary must contain nonnegative integer counts")
                summary = dict(class_summary)
            at = self._now()
            self._emit("FINISHED", {"status": status, "stage_reached": self._stage,
                       "error": self._run_error, "displayed": self._displayed,
                       "duration_s": (at - self._start_at).total_seconds(),
                       "class_summary": summary, "recorder_errors": list(self.errors)}, inside=False, at=at)
            self._state = "FINISHED"
        return self._guard("finish", action)
