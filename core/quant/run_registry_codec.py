"""Pure R3 event-envelope codec and LAB ID primitives (qg-run-registry/1).

This is envelope validation, not complete event-payload or lifecycle validation.
It has no store, clock, registry-key builder, recorder, owner-ruling lookup or
research integration. Human-event fields do not establish authority. Segment
payload field names are not specified in the design, so only a SEGMENT_START
envelope is supported here. No segment storage/recovery behavior is implemented.

MD5 detects inconsistent bytes; it is not authentication. A valid unanchored
prefix cannot reveal deletion of complete trailing records. Stream verification
checks only the supplied lines and optional preceding line, not their origin or
completeness. Nonfinite paths use RFC 6901 JSON Pointers (including array indices).
"""
from datetime import datetime, timedelta
import hashlib
import json
import math
import re


SCHEMA = "qg-run-registry/1"
_CHAIN = frozenset(("row_md5", "prev_row_md5"))
_COMMON = frozenset(("schema", "event", "run_id", "recorded_utc", "writer",
                     "person", "parent_run_id", "nonfinite")) | _CHAIN
_FIELDS = {
    "STARTED": frozenset(("family", "family_id", "symbols_typed", "source_requested",
        "cost_bps_requested", "days", "bootstrap_B", "seed", "intent", "declaration_id",
        "planned", "fn_qualname", "fn_source_sha256", "fn_source_sha256_raw", "repo_anchor",
        "files", "gate_version", "canonical_panel", "env", "grid", "grid_sha256")),
    "PROGRESS": frozenset(("stage", "symbols_resolved", "per_symbol", "span", "sessions",
        "data_md5", "synthetic", "holdout_touched", "cost", "registered",
        "keys_changed_by_symbol_resolution", "family_id", "ledger_file", "ledger_stage",
        "bytes_before", "bytes_after", "rows_before", "rows_after", "hash_before",
        "hash_after", "market", "rows", "interleaved", "skipped", "stats", "sr_sd_daily",
        "oos_moments", "per_config", "chosen_last", "wf_note", "results_sha256",
        "series_ref", "series_error", "existing", "displayed")),
    "FINGERPRINT": frozenset(("fingerprints", "cache_key")),
    "SHADOW": frozenset(("counts", "classes", "rows", "diagnostics", "error",
                          "classifier_version")),
    "FINISHED": frozenset(("status", "stage_reached", "error", "displayed", "duration_s",
                            "class_summary", "recorder_errors")),
    "SUPERSEDED": frozenset(("owner_ruling", "superseded_run_id", "superseded_by", "rule")),
    "DECLARATION": frozenset(("owner_ruling", "declaration_id", "family_id", "config_ids",
                              "fn_source_sha256", "pass_rule", "span", "anchor")),
    "ANNOTATION": frozenset(("owner_ruling", "theta_index", "claim", "test_ref", "why")),
    "BACKFILL": frozenset(("owner_ruling", "family_id", "params", "provenance", "why")),
    "SEGMENT_START": frozenset(),
}
EVENT_TYPES = frozenset(_FIELDS)
_HUMAN = frozenset(("SUPERSEDED", "DECLARATION", "ANNOTATION", "BACKFILL"))
_OPTIONAL_RUN_ID = frozenset(("DECLARATION", "BACKFILL", "SEGMENT_START"))
_HEX = re.compile(r"[0-9a-f]{32}")
_FAMILY = re.compile(r"[A-Z0-9][A-Z0-9-]{0,31}")
_TOKEN = re.compile(r"[0-9a-f]{8}")
_RUN = re.compile(r"LAB-([0-9]{8}T[0-9]{6}Z)-([A-Z0-9][A-Z0-9-]{0,31})-([0-9a-f]{8})")
_INSTANT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")


class CodecError(ValueError):
    """The supplied envelope or bytes do not satisfy this codec's contract."""


def validate_run_id(value: str) -> str:
    """Validate the exact ASCII LAB format and its calendar instant."""
    match = _RUN.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise CodecError("Invalid LAB run ID")
    try:
        datetime.strptime(match[1], "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise CodecError("Invalid LAB run ID date") from exc
    return value


def make_run_id(family_id: str, *, at: datetime, token_source) -> str:
    """Use supplied UTC time/token only; no collision reservation or retries.

    ``token_source`` is called once with no arguments and must return eight
    lowercase hex characters. Time is represented at whole-second precision.
    The caller owns that callback; this utility does not constrain its effects.
    """
    if not isinstance(family_id, str) or _FAMILY.fullmatch(family_id) is None:
        raise CodecError("Invalid family ID")
    if not isinstance(at, datetime) or at.utcoffset() != timedelta(0):
        raise CodecError("Run ID time must be an aware UTC datetime")
    token = token_source()
    if not isinstance(token, str) or _TOKEN.fullmatch(token) is None:
        raise CodecError("Invalid run ID token")
    stamp = (f"{at.year:04d}{at.month:02d}{at.day:02d}T"
             f"{at.hour:02d}{at.minute:02d}{at.second:02d}Z")
    return validate_run_id(f"LAB-{stamp}-{family_id}-{token}")


def validate_envelope(event: dict, *, chained: bool = False) -> None:
    """Check allowed fields and basic identity types, not payload semantics.

    Event-specific fields are optional here. Their nested statistical/request
    meanings, event ordering, human authority and lifecycle are outside scope.
    ``chained=False`` accepts only unchained input; ``True`` requires both hashes.
    """
    if type(event) is not dict or any(type(k) is not str for k in event):
        raise CodecError("Event must be an object with string keys")
    if event.get("schema") != SCHEMA:
        raise CodecError("Unknown event schema")
    kind = event.get("event")
    if type(kind) is not str or kind not in _FIELDS:
        raise CodecError("Unknown event type")
    if set(event) - (_COMMON | _FIELDS[kind]):
        raise CodecError("Unknown top-level event field")
    for name in ("recorded_utc", "writer"):
        if type(event.get(name)) is not str or not event[name]:
            raise CodecError(f"Missing or invalid {name}")
    instant = event["recorded_utc"]
    if _INSTANT.fullmatch(instant) is None:
        raise CodecError("Invalid recorded_utc format")
    try:
        datetime.strptime(instant, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise CodecError("Invalid recorded_utc date") from exc
    if kind not in _OPTIONAL_RUN_ID or "run_id" in event:
        validate_run_id(event.get("run_id"))
    if event.get("parent_run_id") is not None:
        validate_run_id(event["parent_run_id"])
    if kind in _HUMAN or event["writer"] == "tools/r3/registry_segment.py":
        if "person" not in event:
            raise CodecError("Person events require a person field")
    if "person" in event and event["person"] is not None and type(event["person"]) is not str:
        raise CodecError("Invalid person field")
    if "nonfinite" in event and (type(event["nonfinite"]) is not list or
            any(type(path) is not str for path in event["nonfinite"])):
        raise CodecError("nonfinite must be a list of JSON Pointers")
    if chained:
        if type(event.get("row_md5")) is not str or _HEX.fullmatch(event["row_md5"]) is None:
            raise CodecError("Invalid row_md5")
        if "prev_row_md5" not in event:
            raise CodecError("Missing prev_row_md5")
        prev = event["prev_row_md5"]
        if prev is not None and (type(prev) is not str or _HEX.fullmatch(prev) is None):
            raise CodecError("Invalid prev_row_md5")
    elif _CHAIN & set(event):
        raise CodecError("Encoding input must not contain chain fields")


def _pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _copy_json(value, path: str, nonfinite: list[str], active: set[int], *, convert: bool):
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise CodecError("String is not valid UTF-8") from exc
        return value
    if type(value) is float:
        if math.isfinite(value):
            return value
        if not convert:
            raise CodecError("Nonfinite JSON number")
        nonfinite.append(path)
        return None
    if type(value) not in (dict, list):
        raise CodecError("Unsupported JSON value")
    if id(value) in active:
        raise CodecError("Cyclic JSON input")
    active.add(id(value))
    try:
        if type(value) is list:
            return [_copy_json(v, f"{path}/{i}", nonfinite, active, convert=convert)
                    for i, v in enumerate(value)]
        if any(type(k) is not str for k in value):
            raise CodecError("JSON object keys must be strings")
        result = {}
        for key in sorted(value):
            _copy_json(key, "", nonfinite, active, convert=False)
            result[key] = _copy_json(value[key], path + "/" + _pointer_part(key),
                                     nonfinite, active, convert=convert)
        return result
    finally:
        active.remove(id(value))


def _validate_markers(event: dict) -> None:
    if "nonfinite" not in event:
        return
    paths = event["nonfinite"]
    if type(paths) is not list or any(type(p) is not str for p in paths):
        raise CodecError("nonfinite must be a list of JSON Pointers")
    if paths != sorted(set(paths)):
        raise CodecError("nonfinite paths must be unique and sorted")
    for path in paths:
        if not path.startswith("/"):
            raise CodecError("Invalid nonfinite JSON Pointer")
        parts = path[1:].split("/")
        decoded = []
        for part in parts:
            key = part.replace("~1", "/").replace("~0", "~")
            if _pointer_part(key) != part:
                raise CodecError("Invalid JSON Pointer escape")
            decoded.append(key)
        if decoded[0] in _CHAIN | {"nonfinite"}:
            raise CodecError("nonfinite cannot mark codec metadata")
        target = event
        try:
            for key in decoded:
                if type(target) is list:
                    if re.fullmatch(r"0|[1-9][0-9]*", key) is None:
                        raise CodecError("Invalid array index in nonfinite path")
                    target = target[int(key)]
                elif type(target) is dict:
                    target = target[key]
                else:
                    raise CodecError("Invalid nonfinite path")
        except (KeyError, IndexError, ValueError) as exc:
            raise CodecError("Invalid nonfinite path") from exc
        if target is not None:
            raise CodecError("nonfinite path must identify null")


def _canonical(event: dict) -> bytes:
    return json.dumps(event, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _md5(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def _row_hash(event: dict) -> str:
    return _md5(_canonical({k: v for k, v in event.items() if k not in _CHAIN}))


def encode_event_line(event: dict, *, previous_line: bytes | None = None) -> bytes:
    """Encode an unchained envelope, using the full preceding line including LF.

    Existing nonfinite markers must identify null (or a newly converted number).
    A preceding line is validated individually, not against its own predecessor.
    No duplicate-run/lifecycle checks or authenticity claims are made.
    """
    validate_envelope(event)
    generated = []
    try:
        copied = _copy_json(event, "", generated, set(), convert=True)
        _validate_markers(copied)
        if generated:
            copied["nonfinite"] = sorted(set(copied.get("nonfinite", []) + generated))
        _validate_markers(copied)
        previous_hash = None
        if previous_line is not None:
            decode_event_line(previous_line)
            previous_hash = _md5(previous_line)
        copied["row_md5"] = _row_hash(copied)
        copied["prev_row_md5"] = previous_hash
        return _canonical(copied) + b"\n"
    except CodecError:
        raise
    except (ValueError, RecursionError, OverflowError, UnicodeError) as exc:
        raise CodecError("Event cannot be encoded") from exc


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CodecError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise CodecError("Nonfinite JSON constant")


def decode_event_line(line: bytes) -> dict:
    """Validate one canonical LF-terminated line and its row MD5.

    Link continuity requires ``verify_event_lines``. Return detached JSON data;
    this does not validate full event semantics, human authority or lifecycle.
    """
    if type(line) is not bytes or not line.endswith(b"\n") or line.count(b"\n") != 1:
        raise CodecError("Expected exactly one LF-terminated bytes line")
    try:
        event = json.loads(line[:-1].decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
        validate_envelope(event, chained=True)
        _copy_json(event, "", [], set(), convert=False)
        _validate_markers(event)
        if _canonical(event) + b"\n" != line:
            raise CodecError("Event line is not canonical")
        if _row_hash(event) != event["row_md5"]:
            raise CodecError("Event row MD5 mismatch")
        return event
    except CodecError:
        raise
    except (ValueError, RecursionError, OverflowError, UnicodeError) as exc:
        raise CodecError("Malformed event line") from exc


def verify_event_lines(lines, *, previous_line: bytes | None = None) -> tuple[dict, ...]:
    """Verify only a supplied stream and optional preceding canonical line.

    An omitted predecessor requires a null first link. Removing a valid complete
    suffix cannot be detected without an independently supplied tail anchor.
    """
    expected = None
    if previous_line is not None:
        decode_event_line(previous_line)
        expected = _md5(previous_line)
    result = []
    for line in lines:
        event = decode_event_line(line)
        if event["prev_row_md5"] != expected:
            raise CodecError("Event previous-line MD5 mismatch")
        result.append(event)
        expected = _md5(line)
    return tuple(result)
