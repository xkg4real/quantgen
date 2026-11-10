"""Pure in-memory lifecycle and orphan fold over R3 run-registry events.

Bounded R3 child fold/1 of the approved design (revision 2, sections 3.12,
5.3 and 5.6). It turns a verified chain prefix of machine events into one
lifecycle record per run and a family-wide TOTAL. It classifies no trial, builds
no experiment key, counts no N_raw or N_eff, reads no ledger and changes no
verdict. Nothing consumes its output yet (shadow only, Q17).

Chain-trust boundary. The fold does not trust the order the caller supplies. It
re-encodes every event to its canonical line and verifies the lines with
``run_registry_codec.verify_event_lines`` from the first line of segment 0
(``prev_row_md5`` null). The input must therefore be a prefix, cut by position,
of one single-segment chain: the tuple ``SingleSegmentStore.read()`` returns, or
its first n events. Misordered, spliced, edited, interior-dropped, mid-chain and
unchained input is refused. A removed complete suffix cannot be detected; that is
how a caller cuts the chain at an earlier position, so ``Fold.events_folded`` and
``Fold.tail_line_md5`` name the prefix that was folded. MD5 detects inconsistent
bytes; it is not authentication.

Time. ``as_of`` is an aware UTC instant the caller supplies. The fold never cuts
by time: an event recorded after ``as_of`` inside the supplied prefix is refused
as a guard. Orphan age is ``as_of`` minus the STARTED ``recorded_utc``. The order
of ``recorded_utc`` values along the chain is not checked; chain order rules.

Only STARTED, PROGRESS, FINGERPRINT, SHADOW and FINISHED are folded. Human and
SEGMENT_START events are refused, so SUPERSEDED is never produced. A structural
lifecycle violation refuses the whole fold. Conflicts between FINISHED and
PROGRESS are flagged and never lower the effective status: a last PROGRESS stage
that differs from ``stage_reached`` is STATUS_STAGE_CONFLICT, and no PROGRESS at
or above ``stage_reached`` (the page's closing PROGRESS) is PROGRESS_MISSING.
An orphan's stage is its last PROGRESS stage even when an outage record names
it (design 5.6); see the product record's open question. The fold's own code
performs no I/O and reads no clock, environment, configuration or random source.
The codec it calls parses times with ``datetime.strptime``, whose standard-library
cache may call ``time.tzset`` when it is first built in a process.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from types import MappingProxyType

from . import run_registry_codec as codec


STAGES = ("REQUESTED", "COST_RESOLVED", "DATA_LOADED", "PNL_COMPUTED",
          "WALK_FORWARD_DONE", "LEDGER_REGISTERED", "SCORED", "DISPLAYED")
FINISHED_STATUSES = frozenset(("COMPLETED", "FAILED_BEFORE_STATS",
                               "FAILED_AFTER_STATS", "ABORTED"))
EFFECTIVE_STATUSES = frozenset(("COMPLETED", "FAILED_BEFORE_STATS",
                                "FAILED_AFTER_STATS", "OPEN"))
FOLD_EVENTS = frozenset(("STARTED", "PROGRESS", "FINGERPRINT", "SHADOW", "FINISHED"))
FLAGS = frozenset(("STAGE_INFERRED", "STAGE_UNKNOWN", "STATUS_STAGE_CONFLICT",
                   "PROGRESS_MISSING", "REGISTERED_KEYS_MISSING", "KEYS_UNAVAILABLE"))
ORPHAN_AGE = timedelta(hours=6)

_RANK = {stage: rank for rank, stage in enumerate(STAGES)}
_PNL = _RANK["PNL_COMPUTED"]
_BEFORE = "FAILED_BEFORE_STATS"
_AFTER = "FAILED_AFTER_STATS"
_KEY_FIELDS = frozenset(("theta_index", "config_id"))
_CONFIG_ID = re.compile(r"[0-9a-f]{32}")
_FAMILY_START = len("LAB-YYYYMMDDTHHMMSSZ-")
_FAMILY_END = -len("-0123abcd")


class FoldError(ValueError):
    """The supplied prefix, ``as_of`` or outage set cannot be folded."""


@dataclass(frozen=True)
class RunRecord:
    """The lifecycle of one run in the folded prefix (design 5.6).

    ``status`` is the FINISHED status, ``ABORTED`` when inferred, or ``OPEN``;
    ``status_source`` is ``FINISHED``, ``INFERRED`` or ``NONE``.
    ``effective_status`` is what later counting reads: ``COMPLETED``,
    ``FAILED_BEFORE_STATS``, ``FAILED_AFTER_STATS`` or ``OPEN``. ``keys`` are
    ``(theta_index, config_id)`` pairs as recorded (duplicates kept), from
    ``registered`` or ``planned`` as ``keys_source`` says, or None.
    """
    run_id: str
    family_id: str
    started_utc: str
    status: str
    status_source: str
    stage: str | None
    effective_status: str
    flags: tuple[str, ...]
    keys: tuple[tuple[int, str], ...] | None
    keys_source: str | None
    displayed: bool | None
    event_count: int


@dataclass(frozen=True)
class Fold:
    """The fold of one chain prefix at one ``as_of``.

    ``total_by_family`` counts STARTED events, OPEN runs included (3.12).
    ``open_by_family`` lists every family of the prefix, zero when none is open.
    Both are read-only mappings sorted by family ID. ``tail_line_md5`` is the MD5
    of the last folded line, the ``prev_row_md5`` the next event would carry.
    """
    as_of: datetime
    events_folded: int
    tail_line_md5: str | None
    runs: tuple[RunRecord, ...]
    total_by_family: Mapping[str, int]
    open_by_family: Mapping[str, int]
    open_run_ids: tuple[str, ...]
    unmatched_outage_run_ids: tuple[str, ...]


def _md5(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def _line(event) -> bytes:
    # The codec's canonical form; decode_event_line rejects any divergence.
    return json.dumps(event, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"


def _first_bad_line(lines) -> int | None:
    expected = None
    for index, line in enumerate(lines):
        try:
            event = codec.decode_event_line(line)
        except codec.CodecError:
            return index
        if event["prev_row_md5"] != expected:
            return index
        expected = _md5(line)
    return None


def _verified_prefix(events):
    if type(events) not in (list, tuple):
        raise FoldError("events must be a list or tuple of event dicts")
    lines = []
    for index, event in enumerate(events):
        if type(event) is not dict:
            raise FoldError(f"event {index}: not an event dict")
        try:
            lines.append(_line(event))
        except (TypeError, ValueError, RecursionError, OverflowError, UnicodeError) as exc:
            raise FoldError(f"event {index}: cannot be re-encoded as a canonical line") from exc
    try:
        decoded = codec.verify_event_lines(lines)
    except codec.CodecError as exc:
        where = _first_bad_line(lines)
        label = "chain" if where is None else f"event {where}"
        raise FoldError(f"{label}: not a verified prefix of segment 0 ({exc})") from exc
    return decoded, (_md5(lines[-1]) if lines else None)


def _check_as_of(as_of) -> datetime:
    if type(as_of) is not datetime or as_of.utcoffset() != timedelta(0):
        raise FoldError("as_of must be an aware datetime with UTC offset zero")
    return as_of.astimezone(timezone.utc)


def _check_outages(outage_run_ids) -> frozenset:
    if type(outage_run_ids) is not frozenset:
        raise FoldError("outage_run_ids must be a frozenset of LAB run IDs")
    for run_id in outage_run_ids:
        try:
            codec.validate_run_id(run_id)
        except codec.CodecError as exc:
            raise FoldError("outage_run_ids must hold valid LAB run IDs only") from exc
    return outage_run_ids


def _instant(text: str) -> datetime:
    # The codec has already checked the exact format and the calendar date.
    return datetime(int(text[0:4]), int(text[5:7]), int(text[8:10]), int(text[11:13]),
                    int(text[14:16]), int(text[17:19]), int(text[20:26]), tzinfo=timezone.utc)


def _keys(value, index: int, name: str):
    if value is None:
        return None
    if type(value) is not list:
        raise FoldError(f"event {index}: {name} must be null or a list of keys")
    result = []
    for item in value:
        if type(item) is not dict or set(item) != _KEY_FIELDS:
            raise FoldError(f"event {index}: each {name} entry must be {{theta_index, config_id}}")
        theta, config = item["theta_index"], item["config_id"]
        if type(theta) is not int or theta < 0:
            raise FoldError(f"event {index}: {name} theta_index must be an int >= 0")
        if type(config) is not str or _CONFIG_ID.fullmatch(config) is None:
            raise FoldError(f"event {index}: {name} config_id must be 32 lowercase hex")
        result.append((theta, config))
    return tuple(result)


def _stage(value, index: int, name: str) -> str:
    if type(value) is not str or value not in _RANK:
        raise FoldError(f"event {index}: {name} is not a known stage")
    return value


def _apply(index: int, event: dict, runs: dict) -> None:
    kind = event["event"]
    run_id = event["run_id"]
    state = runs.get(run_id)
    if kind == "STARTED":
        if state is not None:
            raise FoldError(f"event {index}: second STARTED for {run_id}")
        family = run_id[_FAMILY_START:_FAMILY_END]
        if event.get("family_id") != family:
            raise FoldError(f"event {index}: STARTED family_id is missing or differs from the run ID")
        runs[run_id] = {"family": family, "started": event["recorded_utc"],
                        "planned": _keys(event.get("planned"), index, "planned"),
                        "stage": None, "displayed_progress": False,
                        "registered_seen": False, "registered": None,
                        "finished": None, "count": 1}
        return
    if state is None:
        raise FoldError(f"event {index}: {kind} before STARTED for {run_id}")
    if state["finished"] is not None:
        raise FoldError(f"event {index}: {kind} after FINISHED for {run_id}")
    if "family_id" in event and event["family_id"] != state["family"]:
        raise FoldError(f"event {index}: family_id differs from the run's STARTED")
    state["count"] += 1
    if kind == "PROGRESS":
        stage = _stage(event.get("stage"), index, "PROGRESS stage")
        if state["stage"] is not None and _RANK[stage] < _RANK[state["stage"]]:
            raise FoldError(f"event {index}: PROGRESS stage decreases for {run_id}")
        state["stage"] = stage
        state["displayed_progress"] = state["displayed_progress"] or stage == "DISPLAYED"
        if "registered" in event:
            if stage != "PNL_COMPUTED":
                raise FoldError(f"event {index}: registered keys outside the PNL_COMPUTED PROGRESS")
            if state["registered_seen"]:
                raise FoldError(f"event {index}: second registered-key PROGRESS for {run_id}")
            state["registered_seen"] = True
            state["registered"] = _keys(event["registered"], index, "registered")
    elif kind == "FINISHED":
        status = event.get("status")
        if type(status) is not str or status not in FINISHED_STATUSES:
            raise FoldError(f"event {index}: FINISHED status is not a terminal status")
        reached = _stage(event.get("stage_reached"), index, "FINISHED stage_reached")
        displayed = event.get("displayed")
        if displayed is not None and type(displayed) is not bool:
            raise FoldError(f"event {index}: FINISHED displayed must be a bool")
        state["finished"] = (status, reached, displayed)


def _by_stage(stage: str) -> str:
    return _AFTER if _RANK[stage] >= _PNL else _BEFORE


def _record(run_id: str, state: dict, as_of: datetime, outages: frozenset) -> RunRecord:
    flags = set()
    last = state["stage"]
    displayed = None
    if state["finished"] is not None:
        status, reached, displayed = state["finished"]
        source = "FINISHED"
        if last is not None and last != reached:
            flags.add("STATUS_STAGE_CONFLICT")
        if last is None or _RANK[last] < _RANK[reached]:
            flags.add("PROGRESS_MISSING")
        stage = reached if last is None else max(reached, last, key=_RANK.__getitem__)
        if status == "COMPLETED":
            effective = "COMPLETED"
            if stage != "DISPLAYED":
                flags.add("STATUS_STAGE_CONFLICT")
            if not state["displayed_progress"]:
                flags.add("PROGRESS_MISSING")
        elif status == _BEFORE:
            effective = _by_stage(stage)
            if effective != _BEFORE:
                flags.add("STATUS_STAGE_CONFLICT")
        elif status == _AFTER:
            effective = _AFTER
            if _RANK[stage] < _PNL:
                flags.add("STATUS_STAGE_CONFLICT")
        else:
            effective = _by_stage(stage)
    elif as_of - _instant(state["started"]) <= ORPHAN_AGE:
        return RunRecord(run_id, state["family"], state["started"], "OPEN", "NONE", last,
                         "OPEN", (), None, None, None, state["count"])
    else:
        status, source, stage = "ABORTED", "INFERRED", last
        if last is not None:
            effective = _by_stage(last)
        elif run_id in outages:
            effective = _AFTER
            flags.add("STAGE_UNKNOWN")
        else:
            effective = _BEFORE
            flags.add("STAGE_INFERRED")
    keys = keys_source = None
    if effective != _BEFORE:
        if state["registered"] is not None:
            keys, keys_source = state["registered"], "registered"
        else:
            flags.add("REGISTERED_KEYS_MISSING")
            if state["planned"] is not None:
                keys, keys_source = state["planned"], "planned"
            else:
                flags.add("KEYS_UNAVAILABLE")
    return RunRecord(run_id, state["family"], state["started"], status, source, stage,
                     effective, tuple(sorted(flags)), keys, keys_source, displayed,
                     state["count"])


def fold_runs(events, *, as_of, outage_run_ids=frozenset()) -> Fold:
    """Fold a verified chain prefix of machine events into run lifecycles.

    ``events`` is a list or tuple of event dicts forming a prefix of segment 0
    (see the module docstring). ``as_of`` is an aware UTC datetime no earlier
    than any ``recorded_utc`` in the prefix. ``outage_run_ids`` is a frozenset of
    LAB run IDs whose outage record names them; IDs with no STARTED event in the
    prefix are returned in ``unmatched_outage_run_ids``. Raises FoldError, naming
    the event index, for any input or structural violation. Inputs are not
    modified; the result is immutable and deterministic.
    """
    cutoff = _check_as_of(as_of)
    outages = _check_outages(outage_run_ids)
    decoded, tail = _verified_prefix(events)
    runs = {}
    for index, event in enumerate(decoded):
        if event["event"] not in FOLD_EVENTS:
            raise FoldError(f"event {index}: {event['event']} is not a machine event this fold supports")
        if _instant(event["recorded_utc"]) > cutoff:
            raise FoldError(f"event {index}: recorded_utc is after as_of")
        _apply(index, event, runs)
    records = tuple(_record(run_id, state, cutoff, outages) for run_id, state in runs.items())
    total, open_count = {}, {}
    for record in records:
        total[record.family_id] = total.get(record.family_id, 0) + 1
        open_count[record.family_id] = (open_count.get(record.family_id, 0)
                                        + (record.effective_status == "OPEN"))
    return Fold(as_of=cutoff, events_folded=len(decoded), tail_line_md5=tail, runs=records,
                total_by_family=MappingProxyType(dict(sorted(total.items()))),
                open_by_family=MappingProxyType(dict(sorted(open_count.items()))),
                open_run_ids=tuple(r.run_id for r in records if r.effective_status == "OPEN"),
                unmatched_outage_run_ids=tuple(sorted(outages.difference(runs))))
