"""DIDM-8/a: an append-only side record of market confirmations, format ``didm-confirmation-v0``.

A score record is fixed when it is assembled, and at that moment the event window cannot be over, so
its ``market_confirmation`` is PENDING. The verdict arrives days later. Instead of rewriting the record,
each verdict is appended here with the time it became known:

    record_id, judgement_sha256, status, known_at, rule_version, window, schema

A reader asks for the verdict "as known at" a decision time and gets the latest entry whose ``known_at``
is at or before that time. An entry that became known later is never returned, so a verdict cannot
leak into a shock or a feature computed for an earlier decision.

This module builds, checks and selects entries. It does not open files: the caller reads and writes
the lines (``dumps`` / ``loads`` give one JSON object per line) wherever the point-in-time store
keeps them. No network, no clock.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from core.didm.llm.schema import MarketConfirmation, _ID
from core.didm.models import confirmation as cf

SCHEMA = "didm-confirmation-v0"
FIELDS = ("schema", "record_id", "judgement_sha256", "status", "known_at", "rule_version", "window")
WINDOW_KINDS = ("daily", "intraday")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_RULE = re.compile(r"^conf-rule-[0-9a-f]{16}$")


class ConfirmationLogError(ValueError):
    pass


def rule_version(config: cf.ConfirmationConfig = cf.DEFAULT_CONFIG) -> str:
    """Identifies the rule an entry was decided under: the registered numbers and the chosen readings."""
    payload = {"estimation": [cf.ESTIMATION_FIRST, cf.ESTIMATION_LAST], "event": [cf.EVENT_FIRST, cf.EVENT_LAST],
               "pre": [cf.PRE_FIRST, cf.PRE_LAST], "sigma_multiple": cf.SIGMA_MULTIPLE,
               "intraday_minutes": cf.INTRADAY_WINDOW_MINUTES, "already_priced": config.already_priced}
    return "conf-rule-" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Entry:
    record_id: str
    judgement_sha256: str
    status: MarketConfirmation
    known_at: datetime
    rule_version: str
    window: tuple[str, int, int]          # (kind, first, last): ("daily", 0, 1) or ("intraday", 0, 60)
    schema: str = SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "record_id": self.record_id, "judgement_sha256": self.judgement_sha256,
                "status": self.status.value, "known_at": self.known_at.isoformat(), "rule_version": self.rule_version,
                "window": {"kind": self.window[0], "first": self.window[1], "last": self.window[2]}}


def daily_window() -> tuple[str, int, int]:
    return ("daily", cf.EVENT_FIRST, cf.EVENT_LAST)


def intraday_window() -> tuple[str, int, int]:
    return ("intraday", 0, cf.INTRADAY_WINDOW_MINUTES)


def make_entry(*, record_id: str, judgement_sha256: str, status: MarketConfirmation, known_at: datetime,
               config: cf.ConfirmationConfig = cf.DEFAULT_CONFIG, window: tuple[str, int, int] | None = None) -> Entry:
    return validate_entry({"schema": SCHEMA, "record_id": record_id, "judgement_sha256": judgement_sha256,
                           "status": status.value if isinstance(status, MarketConfirmation) else status,
                           "known_at": known_at.isoformat() if isinstance(known_at, datetime) else known_at,
                           "rule_version": rule_version(config),
                           "window": dict(zip(("kind", "first", "last"), window or daily_window()))})


def validate_entry(raw: Mapping[str, Any]) -> Entry:
    """Reject instead of repairing: unknown or missing fields, a naive time, an unknown status."""
    if not isinstance(raw, Mapping):
        raise ConfirmationLogError("entry must be a mapping")
    if set(raw) != set(FIELDS):
        raise ConfirmationLogError("entry must have exactly the didm-confirmation-v0 fields")
    if raw["schema"] != SCHEMA:
        raise ConfirmationLogError(f"schema must be {SCHEMA}")
    if not isinstance(raw["record_id"], str) or not _ID.fullmatch(raw["record_id"]):
        raise ConfirmationLogError("record_id must be an identifier string")
    if not isinstance(raw["judgement_sha256"], str) or not _SHA.fullmatch(raw["judgement_sha256"]):
        raise ConfirmationLogError("judgement_sha256 must be 64 lowercase hex characters")
    try:
        status = MarketConfirmation(raw["status"])
    except ValueError:
        raise ConfirmationLogError("unknown status") from None
    if not isinstance(raw["known_at"], str):
        raise ConfirmationLogError("known_at must be an ISO 8601 string")
    try:
        known_at = datetime.fromisoformat(raw["known_at"].replace("Z", "+00:00"))
    except ValueError:
        raise ConfirmationLogError("known_at is not ISO 8601") from None
    if known_at.tzinfo is None:
        raise ConfirmationLogError("known_at must carry a timezone")
    if not isinstance(raw["rule_version"], str) or not _RULE.fullmatch(raw["rule_version"]):
        raise ConfirmationLogError("rule_version must be a conf-rule identifier")
    window = raw["window"]
    if not isinstance(window, Mapping) or set(window) != {"kind", "first", "last"} or window["kind"] not in WINDOW_KINDS:
        raise ConfirmationLogError("window must be {kind: daily|intraday, first, last}")
    for name in ("first", "last"):
        if isinstance(window[name], bool) or not isinstance(window[name], int):
            raise ConfirmationLogError("window bounds must be integers")
    if window["last"] < window["first"]:
        raise ConfirmationLogError("window ends before it starts")
    return Entry(raw["record_id"], raw["judgement_sha256"], status, known_at, raw["rule_version"],
                 (window["kind"], window["first"], window["last"]))


def dumps(entry: Entry) -> str:
    """One line for an append-only JSON Lines file."""
    return json.dumps(entry.as_dict(), sort_keys=True, ensure_ascii=True)


def loads(line: str) -> Entry:
    try:
        raw = json.loads(line)
    except (TypeError, ValueError):
        raise ConfirmationLogError("line is not JSON") from None
    return validate_entry(raw)


def append(log: Sequence[Entry], entry: Entry) -> tuple[Entry, ...]:
    """The log with ``entry`` added at the end. Nothing already in the log is changed or removed.

    Refused: an entry that became known before the record's last entry (the log is in order of
    knowledge), an entry for another judgement of the same record, and a change of a final verdict
    under the same rule version (a different rule version is a re-evaluation and is allowed).
    """
    if not isinstance(entry, Entry):
        raise ConfirmationLogError("only validated entries can be appended")
    for old in reversed(log):
        if old.record_id != entry.record_id:
            continue
        if old.judgement_sha256 != entry.judgement_sha256:
            raise ConfirmationLogError("the record already has entries for another judgement")
        if entry.known_at < old.known_at:
            raise ConfirmationLogError("an entry cannot become known before the record's last entry")
        if (old.rule_version == entry.rule_version and old.status is not MarketConfirmation.PENDING
                and entry.status is not old.status):
            raise ConfirmationLogError("a final verdict cannot change under the same rule version")
        break
    return (*log, entry)


def as_of(log: Sequence[Entry], record_id: str, when: datetime, *, rule: str | None = None) -> Entry | None:
    """The verdict of ``record_id`` as known at ``when``: the last appended entry with known_at <= when
    (optionally only entries of one rule version). None if nothing was known yet."""
    if not isinstance(when, datetime) or when.tzinfo is None:
        raise ConfirmationLogError("when must be a timezone-aware datetime")
    found = None
    for entry in log:
        if entry.record_id == record_id and entry.known_at <= when and (rule is None or entry.rule_version == rule):
            found = entry
    return found


def status_as_of(log: Sequence[Entry], record_id: str, when: datetime, *, rule: str | None = None) -> MarketConfirmation:
    """PENDING when nothing is known yet: an unknown verdict is never read as a confirmation."""
    entry = as_of(log, record_id, when, rule=rule)
    return entry.status if entry is not None else MarketConfirmation.PENDING
