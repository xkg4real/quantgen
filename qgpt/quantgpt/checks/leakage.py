"""Look-ahead check: dates and named events later than the request's as_of.

Text written "as of" a date must not mention a later date or an event that had
not happened yet. Dates are read in the forms the model is asked to write
(ISO, dotted, Korean, English month names, quarters, and plain years marked as
years). Events come from a list the host supplies: a name, optional other
names, and the date the event became known.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .schema import parse_as_of

_MONTHS = {name: i for i, names in enumerate((
    ("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"), ("may",), ("june", "jun"),
    ("july", "jul"), ("august", "aug"), ("september", "sep", "sept"), ("october", "oct"), ("november", "nov"),
    ("december", "dec")), start=1) for name in names}
_MONTH = "|".join(sorted(_MONTHS, key=len, reverse=True))
_Y = r"((?:19|20)\d{2})"

# Each pattern yields (year, month or None, day or None); the earliest moment the text could mean is used,
# so "2027" is late for an as_of in 2026 and "November 2026" is not late for 2026-11-24.
_PATTERNS = (
    (re.compile(rf"(?<!\d){_Y}-(\d{{2}})-(\d{{2}})(?!\d)"), lambda m: (m[1], m[2], m[3])),
    (re.compile(rf"(?<!\d){_Y}[./]\s?(\d{{1,2}})[./]\s?(\d{{1,2}})(?!\d)"), lambda m: (m[1], m[2], m[3])),
    (re.compile(rf"{_Y}년\s*(\d{{1,2}})월\s*(\d{{1,2}})일"), lambda m: (m[1], m[2], m[3])),
    (re.compile(rf"{_Y}년\s*(\d{{1,2}})월(?!\s*\d{{1,2}}일)"), lambda m: (m[1], m[2], None)),
    (re.compile(rf"{_Y}년\s*([1-4])분기"), lambda m: (m[1], 3 * int(m[2]) - 2, None)),
    (re.compile(rf"\bQ([1-4])\s*{_Y}\b", re.I), lambda m: (m[2], 3 * int(m[1]) - 2, None)),
    (re.compile(rf"\b{_Y}\s*Q([1-4])\b", re.I), lambda m: (m[1], 3 * int(m[2]) - 2, None)),
    (re.compile(rf"\b({_MONTH})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+{_Y}\b", re.I),
     lambda m: (m[3], _MONTHS[m[1].lower()], m[2])),
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH})\.?,?\s+{_Y}\b", re.I),
     lambda m: (m[3], _MONTHS[m[2].lower()], m[1])),
    (re.compile(rf"\b({_MONTH})\.?,?\s+{_Y}\b", re.I), lambda m: (m[2], _MONTHS[m[1].lower()], None)),
    (re.compile(rf"(?<!\d){_Y}-(\d{{2}})(?![\d-])"), lambda m: (m[1], m[2], None)),
    (re.compile(rf"{_Y}년(?!\s*\d)"), lambda m: (m[1], None, None)),
    (re.compile(rf"\b(?:in|by|during|since|until|for|of)\s+{_Y}\b(?!\s*(?:-|/|\.)\d)", re.I),
     lambda m: (m[1], None, None)),
)


@dataclass(frozen=True)
class LeakageCheck:
    late_dates: tuple      # date expressions later than as_of, as written, in text order
    late_events: tuple     # names of listed events dated after as_of that the text mentions

    @property
    def ok(self) -> bool:
        return not (self.late_dates or self.late_events)


def _earliest(year, month, day) -> datetime | None:
    try:
        return datetime(int(year), int(month or 1), int(day or 1))
    except ValueError:
        return None


def find_dates(text: str) -> list[tuple[int, str, datetime]]:
    """(position, expression as written, earliest moment it can mean), longest reading first."""
    taken: list[tuple[int, int]] = []
    found = []
    for pattern, parts in _PATTERNS:
        for match in pattern.finditer(text or ""):
            start, end = match.span()
            if any(start < right and left < end for left, right in taken):
                continue
            moment = _earliest(*parts(match))
            if moment is None:
                continue
            taken.append((start, end))
            found.append((start, match.group(0), moment))
    return sorted(found)


def check_leakage(text: str, as_of: str, events: Sequence[Mapping] = ()) -> LeakageCheck:
    limit = parse_as_of(as_of)
    late_dates = tuple(expr for _, expr, moment in find_dates(text) if moment > limit)
    lowered = (text or "").lower()
    late_events = []
    for event in events:
        if parse_as_of(event["date"]) <= limit:
            continue
        names = [event["name"], *event.get("aliases", ())]
        if any(name and name.lower() in lowered for name in names):
            late_events.append(event["name"])
    return LeakageCheck(late_dates, tuple(late_events))
