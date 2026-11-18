"""Bank of Korea ECOS statistics for DIDM (owner answer Q3, 2026-11-18). No network here.

ECOS ``StatisticSearch`` returns the current value of each period; it has no
vintages (unlike ALFRED) and no release time. So:
* ``valid_at`` = the period start (TIME: YYYY, YYYYMM, YYYYQn or YYYYMMDD),
* ``published_at`` = ``received_at`` (we only know the value as of when we got it)
  and ``release_time_known`` = False.
Historical use therefore needs the release calendar separately (not built here);
values collected from now on are point-in-time by construction.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

SOURCE_ID = "ecos"
KST = timezone(timedelta(hours=9))
_Q = re.compile(r"^(\d{4})Q([1-4])$")


class EcosError(ValueError):
    pass


def period_start(time: str) -> datetime:
    t = str(time)
    if re.fullmatch(r"\d{8}", t):
        y, m, d = int(t[:4]), int(t[4:6]), int(t[6:])
    elif re.fullmatch(r"\d{6}", t):
        y, m, d = int(t[:4]), int(t[4:]), 1
    elif re.fullmatch(r"\d{4}", t):
        y, m, d = int(t), 1, 1
    elif _Q.match(t):
        y, q = int(t[:4]), int(t[-1])
        m, d = 3 * (q - 1) + 1, 1
    else:
        raise EcosError(f"unknown ECOS TIME {time!r}")
    return datetime(y, m, d, tzinfo=KST)


def rows(payload: Mapping[str, Any], received_at: datetime) -> list[dict]:
    if not isinstance(received_at, datetime) or received_at.tzinfo is None:
        raise EcosError("received_at must be timezone-aware")
    if "RESULT" in payload and "StatisticSearch" not in payload:
        code = (payload.get("RESULT") or {}).get("CODE", "")
        if code == "INFO-200":  # no data for the query
            return []
        raise EcosError(f"ECOS returned {code or 'an error'}")
    body = payload.get("StatisticSearch")
    if not isinstance(body, Mapping) or not isinstance(body.get("row"), list):
        raise EcosError("payload has no StatisticSearch.row list")
    out = []
    for r in body["row"]:
        stat, time = str(r.get("STAT_CODE") or ""), str(r.get("TIME") or "")
        items = [str(r.get(f"ITEM_CODE{k}") or "") for k in (1, 2, 3, 4)]
        if not stat or not time:
            raise EcosError("row without STAT_CODE or TIME")
        raw = r.get("DATA_VALUE")
        try:
            value = None if raw in (None, "", "-") else float(str(raw).replace(",", ""))
        except ValueError:
            raise EcosError(f"bad DATA_VALUE {raw!r}") from None
        key = ":".join([stat, *[i for i in items if i], time])
        out.append({
            "source_id": SOURCE_ID,
            "item_id": key,
            "kind": "ecos_observation",
            "published_at": received_at,
            "received_at": received_at,
            "valid_at": period_start(time),
            "payload": {
                "stat_code": stat, "stat_name": r.get("STAT_NAME"),
                "item_codes": [i for i in items if i], "item_name": r.get("ITEM_NAME1"),
                "unit": r.get("UNIT_NAME"), "time": time, "value": value,
                "release_time_known": False,
            },
        })
    return out
