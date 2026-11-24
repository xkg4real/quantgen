"""ALFRED vintage ingest assembly (no network here).

Two inputs, same output rows:

1. FRED API ``series/observations`` JSON fetched with realtime_start/realtime_end
   covering all vintages (``data.didm.alfred`` does the HTTP; needs FRED_API_KEY).
2. Rows from the owner's manual ALFRED download "Observations by Real-Time Period"
   (period, value, realtime_start, realtime_end), read by tools/didm with openpyxl
   -- the same route as docs/audit/2026-10-27/calendar_batch5/extract_alfred.py.
   Raw downloads are never committed (FRED terms).

One row = one (series, observation date, vintage). ``valid_at`` = observation date,
``published_at`` = the vintage's realtime_start (date only, taken as 00:00 UTC --
the release clock time is not in ALFRED; DIDM uses dates for macro vintages in V0),
``received_at`` = when we fetched it (caller supplies).
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping

SOURCE_ID = "alfred"
ATTRIBUTION = "Source: ALFRED, Federal Reserve Bank of St. Louis (https://alfred.stlouisfed.org/)."
_SERIES = re.compile(r"^[A-Z0-9_]{1,30}$")


class AlfredError(ValueError):
    pass


def _day(value: Any, name: str) -> datetime:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        d = value
    elif isinstance(value, str):
        try:
            if len(value) <= 10:
                d = date.fromisoformat(value)
            else:
                if value[10] not in ("T", "t", " "):
                    raise ValueError
                timestamp = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
                d = datetime.fromisoformat(timestamp).date()
        except ValueError:
            raise AlfredError(f"{name}: bad date {value!r}") from None
    else:
        raise AlfredError(f"{name}: bad date {value!r}")
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _vintage_period(start, end) -> tuple[datetime, datetime]:
    first = _day(start, "realtime_start")
    last = _day(end, "realtime_end")
    if last < first:
        raise AlfredError("realtime_end precedes realtime_start")
    return first, last


def _value(raw: Any) -> float | None:
    if raw is None or raw == "." or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise AlfredError(f"bad observation value {raw!r}") from None


def _row(series_id: str, obs_date, value, rt_start, rt_end, received_at: datetime) -> dict:
    valid = _day(obs_date, "date")
    vintage, end = _vintage_period(rt_start, rt_end)
    return {
        "source_id": SOURCE_ID,
        "item_id": f"{series_id}:{valid.date().isoformat()}:{vintage.date().isoformat()}",
        "kind": "alfred_vintage",
        "published_at": vintage,
        "received_at": received_at,
        "valid_at": valid,
        "payload": {
            "series_id": series_id,
            "date": valid.date().isoformat(),
            "realtime_start": vintage.date().isoformat(),
            "realtime_end": end.date().isoformat(),
            "value": _value(value),
        },
    }


def _check(series_id: str, received_at: datetime) -> None:
    if not _SERIES.match(series_id or ""):
        raise AlfredError(f"bad series id {series_id!r}")
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise AlfredError("received_at must be timezone-aware")


def rows_from_api(series_id: str, payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    """FRED API observations JSON (with real-time period) -> store rows."""
    _check(series_id, received_at)
    obs = payload.get("observations") if isinstance(payload, Mapping) else None
    if not isinstance(obs, list):
        raise AlfredError("payload has no observations list")
    return [_row(series_id, o["date"], o.get("value"), o["realtime_start"], o["realtime_end"], received_at)
            for o in obs]


def rows_from_manual(series_id: str, rows: Iterable[tuple], received_at: datetime) -> list[dict]:
    """(period, value, realtime_start, realtime_end) tuples from a manual download -> store rows."""
    _check(series_id, received_at)
    out = []
    for r in rows:
        if not r or r[0] is None:
            continue
        period, value, rt_start, rt_end = r[:4]
        out.append(_row(series_id, period, value, rt_start, rt_end if rt_end is not None else "9999-12-31",
                        received_at))
    return out


def value_as_known_on(rows: Iterable[Mapping[str, Any]], obs_date, known_on) -> float | None:
    """The value for obs_date as it stood on known_on (vintage realtime window contains known_on).

    Both dates accept the same forms (date, datetime, ISO date, basic YYYYMMDD, timestamp string). An aware
    datetime or an offset string counts by its **written** calendar date, not its UTC date: ALFRED periods
    and vintages are calendar dates without a clock (review DSF-11)."""
    cutoff = _day(known_on, "known_on")
    obs = _day(obs_date, "obs_date").date().isoformat()   # same accepted forms as known_on (review DS-9)
    hits = []
    for row in rows:
        payload = row["payload"]
        if payload["date"] == obs:
            start, end = _vintage_period(payload["realtime_start"], payload["realtime_end"])
            if start <= cutoff <= end:
                hits.append(payload)
    if len(hits) > 1:
        raise AlfredError(f"overlapping vintages for {obs_date} on {known_on}")
    return hits[0]["value"] if hits else None
