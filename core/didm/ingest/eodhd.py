"""Pure EODHD Economic Events input contracts; no acquisition or pipeline wiring.

Provider contract: https://eodhd.com/financial-apis/economic-events-data-api
The provider's ``date`` describes an event, not when its forecast was published.
Ordinary API rows have no forecast-publication/version evidence. Their estimates
therefore remain ineligible for historical forecast use. Receipt and event times
never substitute for that evidence. Eligibility here is an input-data condition,
not a DIDM research pass, licence grant, or change to the registered V0 schema.

Caller verification flags do not independently bind evidence to this estimate or
row. The caller must verify that association and the research as-of cutoff before
any integration. Forecast eligibility is not historical PIT approval of actual,
previous or the whole payload. raw_payload_json preserves unknown fields and is
not a secret-redaction function; callers must supply appropriately scoped input.

All clocks and evidence are supplied by the caller. No store rows, HTTP clients,
credentials, SDKs, scheduler, scorer or actual-data calls are provided here.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping

MAX_LIMIT = 1000
MAX_OFFSET = 1000
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(Z|[+-]\d{2}:\d{2})?$")
_OFFSET = re.compile(r"^([+-])(\d{2}):(\d{2})$")
_PUBLICATION_BASES = frozenset({"vendor_forecast_publication", "archived_forecast_publication"})


class EconomicEventError(ValueError):
    """Invalid supplied input, without echoing its payload or credentials."""


class PartitionExhausted(EconomicEventError):
    """A saturated single-date range cannot be proven complete by date splitting."""


@dataclass(frozen=True)
class ForecastProvenance:
    """Caller-reviewed provenance, separate from untrusted response fields.

    ``observed_at`` and ``event_time`` are intentionally not publication bases.
    A reference/version string alone does not assert verification: both explicit
    verification flags must also be true. No row-derived flags are promoted here.
    """
    published_at: datetime | None = None
    publication_basis: str = "unknown"
    publication_verified: bool = False
    version_id: str | None = None
    version_verified: bool = False
    evidence_reference: str | None = None


@dataclass(frozen=True)
class EconomicEvent:
    event_type: str
    country: str
    comparison: str | None
    period: str | None
    event_time_raw: str
    event_at_utc: datetime | None
    received_at_utc: datetime
    actual: int | float | None
    previous: int | float | None
    estimate: int | float | None
    change: int | float | None
    change_percentage: int | float | None
    raw_payload_json: str
    timezone_basis: str
    forecast_provenance: ForecastProvenance
    historical_forecast_eligible: bool
    historical_ineligibility_reasons: tuple[str, ...]


def _aware(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise EconomicEventError(f"{name}: timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _offset(value: str) -> timezone | None:
    if value == "Z":
        return timezone.utc
    match = _OFFSET.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise EconomicEventError("event_utc_offset: expected Z or signed HH:MM")
    hours, minutes = int(match[2]), int(match[3])
    if hours >= 24 or minutes >= 60:
        raise EconomicEventError("event_utc_offset: invalid offset")
    if value == "-00:00":
        return None  # RFC3339 unknown local offset is not verified UTC.
    amount = timedelta(hours=hours, minutes=minutes)
    return timezone(-amount if match[1] == "-" else amount)


def _text(value: Any, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or (not optional and not value.strip()):
        raise EconomicEventError(f"{name}: string required")
    return value


def _number(value: Any, name: str) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EconomicEventError(f"{name}: number or null required")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise EconomicEventError(f"{name}: finite number required")
    return value


def parse_event(payload: Mapping[str, Any], received_at: datetime, *,
                event_utc_offset: str | None = None,
                event_timezone_verified: bool = False,
                event_timezone_evidence: str | None = None,
                forecast_provenance: ForecastProvenance | None = None) -> EconomicEvent:
    """Preserve one supplied response row and assess forecast-time evidence.

    An explicit offset inside the row declares its time zone. A naive provider
    date may be located only using a separately supplied offset; its time zone
    remains unverified unless the caller also supplies verification and evidence.
    Missing or unknown offsets are retained as unknown, never guessed as UTC.
    Actual receipt time is preserved even for a historically verified forecast;
    this object never backdates the application's own knowledge or writes a store.
    """
    if not isinstance(payload, Mapping):
        raise EconomicEventError("payload: mapping required")
    received = _aware(received_at, "received_at")
    if not isinstance(event_timezone_verified, bool):
        raise EconomicEventError("event_timezone_verified: boolean required")
    if event_timezone_evidence is not None:
        _text(event_timezone_evidence, "event_timezone_evidence")
    event_type = _text(payload.get("type"), "type")
    country = _text(payload.get("country"), "country")
    if re.fullmatch(r"[A-Z]{2}", country) is None:
        raise EconomicEventError("country: two uppercase letters required")
    comparison = payload.get("comparison")
    if comparison not in (None, "mom", "qoq", "yoy"):
        raise EconomicEventError("comparison: unsupported value")
    period = _text(payload.get("period"), "period", optional=True)
    raw_time = _text(payload.get("date"), "date")
    match = _STAMP.fullmatch(raw_time)
    if match is None:
        raise EconomicEventError("date: timestamp with clock required")
    suffix = match[1]
    supplied_zone = _offset(event_utc_offset) if event_utc_offset is not None else None
    payload_zone = _offset(suffix) if suffix is not None else None
    try:
        stamp = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    except ValueError:
        raise EconomicEventError("date: invalid timestamp") from None
    zone_verified = False
    basis = "unknown"
    event_at = None
    if suffix is not None:
        if event_utc_offset is not None and supplied_zone != payload_zone:
            raise EconomicEventError("date: conflicting supplied offset")
        if payload_zone is not None:
            event_at = stamp.astimezone(timezone.utc)
            zone_verified, basis = True, "payload_explicit_offset"
        else:
            basis = "unknown_minus_zero_offset"
    elif supplied_zone is not None:
        event_at = stamp.replace(tzinfo=supplied_zone).astimezone(timezone.utc)
        zone_verified = event_timezone_verified and bool(event_timezone_evidence)
        basis = "verified_supplied_offset" if zone_verified else "unverified_supplied_offset"
    values = {key: _number(payload.get(key), key)
              for key in ("actual", "previous", "estimate", "change", "change_percentage")}
    try:
        raw_json = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError, OverflowError):
        raise EconomicEventError("payload: finite JSON-compatible values required") from None
    provenance = forecast_provenance if forecast_provenance is not None else ForecastProvenance()
    if not isinstance(provenance, ForecastProvenance):
        raise EconomicEventError("forecast_provenance: ForecastProvenance required")
    if not isinstance(provenance.publication_verified, bool) or not isinstance(provenance.version_verified, bool):
        raise EconomicEventError("forecast_provenance: boolean verification flags required")
    _text(provenance.publication_basis, "publication_basis")
    for key in ("version_id", "evidence_reference"):
        if getattr(provenance, key) is not None:
            _text(getattr(provenance, key), key)
    publication = (_aware(provenance.published_at, "forecast published_at")
                   if provenance.published_at is not None else None)
    provenance = ForecastProvenance(publication, provenance.publication_basis,
        provenance.publication_verified, provenance.version_id, provenance.version_verified,
        provenance.evidence_reference)
    reasons = []
    if values["estimate"] is None:
        reasons.append("missing_estimate")
    if not zone_verified:
        reasons.append("event_timezone_unverified")
    if publication is None:
        reasons.append("forecast_publication_missing")
    if not provenance.publication_verified:
        reasons.append("forecast_publication_unverified")
    if provenance.publication_basis not in _PUBLICATION_BASES:
        reasons.append("forecast_publication_basis_not_source")
    if not provenance.version_verified or not provenance.version_id:
        reasons.append("forecast_version_unverified")
    if not provenance.evidence_reference:
        reasons.append("forecast_evidence_missing")
    if publication is not None and event_at is not None and publication >= event_at:
        reasons.append("forecast_not_before_event")
    if publication is not None and publication > received:
        reasons.append("forecast_publication_after_receipt")
    return EconomicEvent(event_type, country, comparison, period, raw_time, event_at,
        received, values["actual"], values["previous"], values["estimate"], values["change"],
        values["change_percentage"], raw_json, basis, provenance, not reasons, tuple(reasons))


def _day(value: date | str) -> date:
    if isinstance(value, datetime):
        raise EconomicEventError("range: date rather than datetime required")
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise EconomicEventError("range: YYYY-MM-DD required")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise EconomicEventError("range: invalid date") from None


@dataclass(frozen=True)
class DateWindow:
    start: date
    end: date

    def __post_init__(self):
        if not isinstance(self.start, date) or isinstance(self.start, datetime) or not isinstance(self.end, date) or isinstance(self.end, datetime) or self.end < self.start:
            raise EconomicEventError("range: ordered date endpoints required")


def partition_dates(start: date | str, end: date | str, *, max_days: int) -> tuple[DateWindow, ...]:
    """Disjoint inclusive windows. max_days is caller policy, not a vendor limit."""
    lo, hi = _day(start), _day(end)
    if hi < lo or isinstance(max_days, bool) or not isinstance(max_days, int) or max_days < 1:
        raise EconomicEventError("range: ordered dates and positive max_days required")
    windows = []
    while lo <= hi:
        last = lo + timedelta(days=min(max_days - 1, (hi - lo).days))
        windows.append(DateWindow(lo, last))
        if last == hi:
            break
        lo = last + timedelta(days=1)
    return tuple(windows)


def split_window(window: DateWindow) -> tuple[DateWindow, DateWindow]:
    """Split a saturated range; a saturated single date is explicitly incomplete."""
    if not isinstance(window, DateWindow):
        raise EconomicEventError("range: DateWindow required")
    days = (window.end - window.start).days
    if days == 0:
        raise PartitionExhausted("saturated single-date range remains incomplete")
    mid = window.start + timedelta(days=days // 2)
    return DateWindow(window.start, mid), DateWindow(mid + timedelta(days=1), window.end)


@dataclass(frozen=True)
class PageDecision:
    action: str
    next_offset: int | None


def assess_page(*, offset: int, limit: int, returned: int) -> PageDecision:
    """Bounded planning only, not proof of whole-range acquisition completeness.

    An end_page requires the caller to verify all preceding pages and response
    consistency. A full last permitted page can hide more rows and requires a
    split; this function never emits an offset above the documented maximum.
    """
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit, returned)):
        raise EconomicEventError("page: integer parameters required")
    if not 0 <= offset <= MAX_OFFSET or not 1 <= limit <= MAX_LIMIT or not 0 <= returned <= limit:
        raise EconomicEventError("page: outside documented bounds")
    if returned < limit:
        return PageDecision("end_page", None)
    following = offset + limit
    if following > MAX_OFFSET:
        return PageDecision("split_range", None)
    return PageDecision("next_page", following)
