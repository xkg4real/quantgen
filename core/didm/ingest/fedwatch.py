"""CME FedWatch end-of-day FOMC target-range probabilities for DIDM (DS-4c, D9). No network here.

Design: docs/didm/DS4C_FEDWATCH_DESIGN_2026-11-24.md. CME's own API field names, auth and update
time are **unverified** (owner answer OA-31 pending), so this module works on an internal format
only:

* ``FedWatchDay`` / ``MeetingDist`` -- one trade date, one probability distribution per FOMC meeting.
* ``read_csv`` -- the owner's file in the documented column layout (``CSV_COLUMNS``); a file exported
  from CME is converted to this layout by hand or by a later vendor adapter, never guessed here.
* ``rows`` -- point-in-time store rows, one per (trade date, meeting).

Checks (design section 2; a failing day is refused whole, never repaired, and counted):
1. each probability in 0..1 and each meeting's sum = 1 (+-1e-4); a meeting given in percent
   (sum 100) is divided by 100;
2. ranges 25 bp wide, ascending, not overlapping;
3. meeting date after trade date;
4. ``published_at`` timezone-aware and not before the trade date.

Times (design section 3): ``valid_at`` = trade date 00:00 UTC; ``published_at`` = the supplied
publication time, else the next day 00:00 UTC (conservative, no look-ahead); ``received_at`` = caller.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Mapping

SOURCE_ID = "cme-fedwatch"
KIND = "fedwatch_meeting_dist"
PARSER = "fedwatch-v0.1"
SUM_TOL = 1e-4
WIDTH_BP = 25
CSV_COLUMNS = ("trade_date", "meeting_date", "lower_bp", "upper_bp", "probability")
OPTIONAL_COLUMNS = ("published_at", "current_lower_bp", "current_upper_bp")


class FedWatchError(ValueError):
    pass


@dataclass(frozen=True)
class MeetingDist:
    meeting_date: date
    buckets: tuple[tuple[int, int, float], ...]   # (lower_bp, upper_bp, p)


@dataclass(frozen=True)
class FedWatchDay:
    trade_date: date
    published_at: datetime
    meetings: tuple[MeetingDist, ...]
    current_range: tuple[int, int] | None = None
    source_variant: str = "eod"


def default_published_at(trade_date: date) -> datetime:
    return datetime.combine(trade_date + timedelta(days=1), time(0), tzinfo=timezone.utc)


def _midnight(d: date) -> datetime:
    return datetime.combine(d, time(0), tzinfo=timezone.utc)


def validate(day: FedWatchDay) -> FedWatchDay:
    """Checks 1-4. Returns the day with percent meetings scaled to 0..1."""
    if day.source_variant != "eod":
        raise FedWatchError("only the end-of-day variant is in V0")
    if not isinstance(day.published_at, datetime) or day.published_at.tzinfo is None:
        raise FedWatchError("published_at must be timezone-aware")
    if day.published_at < _midnight(day.trade_date):
        raise FedWatchError("published_at precedes the trade date")
    if not day.meetings:
        raise FedWatchError("no meetings")
    if day.current_range is not None and day.current_range[1] - day.current_range[0] != WIDTH_BP:
        raise FedWatchError("current range must be 25 bp wide")
    seen, out = set(), []
    for m in day.meetings:
        if m.meeting_date <= day.trade_date:
            raise FedWatchError(f"meeting {m.meeting_date} is not after trade date {day.trade_date}")
        if m.meeting_date in seen:
            raise FedWatchError(f"meeting {m.meeting_date} twice")
        seen.add(m.meeting_date)
        if not m.buckets:
            raise FedWatchError(f"meeting {m.meeting_date}: no ranges")
        total = sum(p for _, _, p in m.buckets)
        scale = 100.0 if abs(total - 100.0) <= 100 * SUM_TOL else 1.0
        buckets, prev_upper = [], None
        for lo, hi, p in m.buckets:
            if isinstance(p, bool) or not isinstance(p, (int, float)):
                raise FedWatchError(f"meeting {m.meeting_date}: probability must be a number")
            p = p / scale
            if not 0.0 <= p <= 1.0:
                raise FedWatchError(f"meeting {m.meeting_date}: probability {p} outside 0..1")
            if hi - lo != WIDTH_BP:
                raise FedWatchError(f"meeting {m.meeting_date}: range {lo}-{hi} is not 25 bp")
            if prev_upper is not None and lo < prev_upper:
                raise FedWatchError(f"meeting {m.meeting_date}: ranges overlap or are out of order")
            prev_upper = hi
            buckets.append((int(lo), int(hi), float(p)))
        if abs(sum(p for _, _, p in buckets) - 1.0) > SUM_TOL:
            raise FedWatchError(f"meeting {m.meeting_date}: probabilities sum to {total}, not 1 (or 100)")
        out.append(MeetingDist(m.meeting_date, tuple(buckets)))
    out.sort(key=lambda m: m.meeting_date)
    return FedWatchDay(day.trade_date, day.published_at, tuple(out), day.current_range, day.source_variant)


def derived(meeting: MeetingDist, current_range: tuple[int, int] | None) -> dict:
    """expected_mid_bp always; p_hike/p_hold/p_cut against the current range when it is known."""
    out = {"expected_mid_bp": round(sum(p * (lo + hi) / 2 for lo, hi, p in meeting.buckets), 6),
           "p_hike": None, "p_hold": None, "p_cut": None}
    if current_range is not None:
        lo0 = current_range[0]
        out["p_hike"] = round(sum(p for lo, _, p in meeting.buckets if lo > lo0), 9)
        out["p_hold"] = round(sum(p for lo, _, p in meeting.buckets if lo == lo0), 9)
        out["p_cut"] = round(sum(p for lo, _, p in meeting.buckets if lo < lo0), 9)
    return out


def rows(day: FedWatchDay, received_at: datetime) -> list[dict]:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise FedWatchError("received_at must be timezone-aware")
    day = validate(day)
    out = []
    for m in day.meetings:
        out.append({
            "source_id": SOURCE_ID,
            "item_id": f"{m.meeting_date.isoformat()}@{day.trade_date.isoformat()}",
            "kind": KIND,
            "published_at": day.published_at,
            "received_at": received_at,
            "valid_at": _midnight(day.trade_date),
            "payload": {
                "meeting_date": m.meeting_date.isoformat(),
                "trade_date": day.trade_date.isoformat(),
                "buckets": [[lo, hi, p] for lo, hi, p in m.buckets],
                "current_range": list(day.current_range) if day.current_range else None,
                **derived(m, day.current_range),
                "source_variant": day.source_variant,
                "parser": PARSER,
            },
        })
    return out


def _date(value: str, name: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except (AttributeError, ValueError):
        raise FedWatchError(f"{name}: bad date {value!r}") from None


def _int(value: str, name: str) -> int:
    try:
        return int(str(value).strip())
    except ValueError:
        raise FedWatchError(f"{name}: bad integer {value!r}") from None


def _float(value: str, name: str) -> float:
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        raise FedWatchError(f"{name}: bad number {value!r}") from None


def _published(value: str | None, trade: date) -> datetime:
    if value is None or not value.strip():
        return default_published_at(trade)
    try:
        t = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise FedWatchError(f"published_at: bad time {value!r}") from None
    if t.tzinfo is None:
        raise FedWatchError("published_at must carry a timezone")
    return t


def days_from_records(records: Iterable[Mapping[str, str]]) -> tuple[list[FedWatchDay], list[tuple[str, str]]]:
    """Group CSV records by trade date. Returns (valid days, [(trade_date, reason), ...] refused)."""
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for r in records:
        grouped.setdefault(str(r.get("trade_date") or "").strip(), []).append(r)
    days, refused = [], []
    for key in sorted(grouped):
        try:
            trade = _date(key, "trade_date")
            recs = grouped[key]
            pubs = {(r.get("published_at") or "").strip() for r in recs}
            if len(pubs) > 1:
                raise FedWatchError("published_at differs within one trade date")
            currents = {((r.get("current_lower_bp") or "").strip(), (r.get("current_upper_bp") or "").strip())
                        for r in recs}
            if len(currents) > 1:
                raise FedWatchError("current range differs within one trade date")
            cur_lo, cur_hi = currents.pop()
            current = (_int(cur_lo, "current_lower_bp"), _int(cur_hi, "current_upper_bp")) if cur_lo or cur_hi else None
            meetings: dict[date, list[tuple[int, int, float]]] = {}
            for r in recs:
                meetings.setdefault(_date(r.get("meeting_date") or "", "meeting_date"), []).append(
                    (_int(r.get("lower_bp"), "lower_bp"), _int(r.get("upper_bp"), "upper_bp"),
                     _float(r.get("probability"), "probability")))
            day = FedWatchDay(trade, _published(pubs.pop(), trade),
                              tuple(MeetingDist(d, tuple(sorted(b))) for d, b in meetings.items()), current)
            days.append(validate(day))
        except FedWatchError as exc:
            refused.append((key, str(exc)))
    return days, refused


def read_csv(text: str) -> tuple[list[FedWatchDay], list[tuple[str, str]]]:
    """The owner's file in the CSV_COLUMNS layout (plus optional OPTIONAL_COLUMNS)."""
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise FedWatchError(f"missing columns: {', '.join(missing)} (expected {', '.join(CSV_COLUMNS)})")
    return days_from_records(reader)
