"""M1 package B - effective-dated calendars, clocks, publication schedules, regime tags, signed-file store
(T-CLOSE-01, T-CLOSE-02, T-TZ-01, T-TZ-02, T-PRINT-01, T-CAL-01, T-CAL-02, T-REGIME-01, T-SAT-01, T-XMKT-01 and the
calendar halves of T-H15-01, T-H10-02, T-VIX-01, T-AVAIL-01, I-06b).

Hermetic: every calendar file is a synthetic fixture written into a tempfile directory and signed there by the
test itself (signer "TEST-FIXTURE (not an owner sign-off)"); the library never writes a signature. The shipped
files under core/calendars/data/ are read only to check their signing state (a draft is refused, an owner-signed file
is complete), and by the two REFDATA bodies on the KRX official closes (T-PRINT-01, T-SAT-01; look-ahead audit LA-02,
part 1): they read the listed fixture through `require_fixture` and use the shipped KRX clock files only when those load
and cover the fixture's dates (otherwise NotRun "OWNER: ...", computed from the files). T-CLOSE-02 on the signed files
(LA-02, part 2) runs its clauses on the shipped set once every file they read loads and covers their days, the
owner-signed kr_sessions rows they need exist and no kr_sessions `owner_must_sign` entry covers a row they read
(otherwise NotRun "OWNER: ...", computed from the files). No module global is patched.
"""
from __future__ import annotations

import copy
import csv
import dataclasses
import io
import math
import re
import statistics
import tempfile
import types
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from core.calendars import clocks, events, publication, regime, store
from core.calendars.store import CalendarCoverageError, CalendarSet, CalendarUnsigned, NotASession, content_md5
from tests.notrun import NotRun, require_fixture

SIGNER = "TEST-FIXTURE (not an owner sign-off)"
SIGNED_UTC = "2026-10-06T00:00:00Z"
NY, KST = "America/New_York", "Asia/Seoul"
UTC = timezone.utc
_CACHE: dict[str, tuple[tempfile.TemporaryDirectory, CalendarSet]] = {}


def U(y, m, d, hh=0, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


# --------------------------------------------------------------------------- #
# Fixture calendars (synthetic; signed in the temp dir by the test)
# --------------------------------------------------------------------------- #
def _row(**kw) -> dict:
    base = {"effective_from": None, "effective_to": None, "source_url": "fixture", "retrieved_at_utc": SIGNED_UTC,
            "signed_off_by": SIGNER}
    base.update(kw)
    return base


def _hol(d: date, kind="closed", close_local=None, name="fixture") -> dict:
    r = _row(date=d.isoformat(), kind=kind, name=name, effective_from=d.isoformat(), effective_to=d.isoformat())
    if close_local:
        r["close_local"] = close_local
    return r


def _nth(year, month, weekday, n):
    d = date(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d + timedelta(days=7 * (n - 1))


def _last(year, month, weekday):
    d = date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def _easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e, f = b // 4, b % 4, (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    return date(year, (h + l - 7 * m + 114) // 31, ((h + l - 7 * m + 114) % 31) + 1)


def _observed(d, sat_to_fri=True):
    if d.weekday() == 5 and sat_to_fri:
        return d - timedelta(days=1)
    return d + timedelta(days=1) if d.weekday() == 6 else d


def _federal(year) -> set[date]:
    out = {_observed(date(year, 1, 1)), _nth(year, 1, 0, 3), _nth(year, 2, 0, 3), _last(year, 5, 0),
           _observed(date(year, 7, 4)), _nth(year, 9, 0, 1), _nth(year, 10, 0, 2), _observed(date(year, 11, 11)),
           _nth(year, 11, 3, 4), _observed(date(year, 12, 25))}
    if year >= 2021:
        out.add(_observed(date(year, 6, 19)))
    return out


def _nyse(year) -> tuple[set[date], dict[date, str]]:
    ny = date(year, 1, 1)
    closed = {_nth(year, 1, 0, 3), _nth(year, 2, 0, 3), _easter(year) - timedelta(days=2), _last(year, 5, 0),
              _observed(date(year, 7, 4)), _nth(year, 9, 0, 1), _nth(year, 11, 3, 4), _observed(date(year, 12, 25))}
    if ny.weekday() < 5:
        closed.add(ny)
    elif ny.weekday() == 6:
        closed.add(ny + timedelta(days=1))
    if year >= 2022:
        closed.add(_observed(date(year, 6, 19)))
    early = {_nth(year, 11, 3, 4) + timedelta(days=1): "13:00"}
    if date(year, 7, 3).weekday() < 4 and date(year, 7, 4).weekday() < 5:
        early[date(year, 7, 3)] = "13:00"
    if date(year, 12, 24).weekday() < 4:
        early[date(year, 12, 24)] = "13:00"
    return closed, early


# KRX fixture: fixed-date holidays every year (closed on Saturdays too), Dec 31, plus the real 2015/16/25/26/27 lists.
_KRX_EXTRA = {
    2015: ["02-18", "02-19", "02-20", "05-01", "05-25", "08-14", "09-28", "09-29", "10-09"],
    2016: ["02-08", "02-09", "02-10", "04-13", "05-06", "09-14", "09-15", "09-16"],
    2025: ["01-27", "01-28", "01-29", "01-30", "03-03", "05-01", "05-06", "06-03", "10-06", "10-07", "10-08", "10-09"],
    2026: ["02-16", "02-17", "02-18", "03-02", "05-01", "05-25", "08-17", "09-24", "09-25", "10-05", "10-09"],
    2027: ["02-08", "02-09", "05-13", "08-16", "09-14", "09-15", "09-16", "10-04", "10-11", "12-27"],
}


def _krx_closed() -> set[date]:
    out = set()
    for y in range(1995, 2028):
        for md in ((1, 1), (3, 1), (5, 5), (6, 6), (8, 15), (10, 3), (12, 25), (12, 31)):
            out.add(date(y, *md))
        for md in _KRX_EXTRA.get(y, ()):
            out.add(date.fromisoformat(f"{y}-{md}"))
    return out


def _doc(file_id, covers, calendar, rows, version="1.0.0-fixture") -> dict:
    return {"file_id": file_id, "version": version, "covers": {"from": covers[0], "to": covers[1]},
            "coverage_calendar": calendar, "signed_off_by": SIGNER, "signed_utc": SIGNED_UTC, "md5": None, "rows": rows}


def _sign(doc: dict) -> dict:
    doc["md5"] = content_md5(doc)
    return doc


def _write_set(root: Path, docs: dict[str, dict], *, manifest_version="1.0.0-fixture", unsigned_manifest=False) -> None:
    rows = []
    for name, doc in docs.items():
        _sign(doc)
        (root / f"{name}.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        rows.append({"file": f"{name}.yaml", "version": doc["version"], "md5": doc["md5"],
                     "signed_off_by": None if unsigned_manifest else doc["signed_off_by"], "test_ids": ["T-CAL-01"]})
    manifest = {"version": manifest_version, "signed_off_by": SIGNER, "signed_utc": SIGNED_UTC, "rows": rows}
    (root / "MANIFEST.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def fixture_docs() -> dict[str, dict]:
    docs = {}
    span = ("1995-01-01", "2027-12-31")
    docs["holidays_KRX"] = _doc("holidays_KRX", span, "KRX", [_hol(d) for d in sorted(_krx_closed())])
    docs["holidays_ECOS"] = _doc("holidays_ECOS", span, "ECOS", [_hol(d) for d in sorted(_krx_closed()) if d.weekday() < 5])
    closed, early = set(), {}
    for y in range(2006, 2028):
        c, e = _nyse(y)
        closed |= c
        early.update(e)
    closed.add(date(2025, 1, 9))
    nyse_rows = [_hol(d) for d in sorted(closed)] + [_hol(d, "early_close", t) for d, t in sorted(early.items())]
    docs["holidays_NYSE"] = _doc("holidays_NYSE", ("2006-01-01", "2027-12-31"), "NYSE", nyse_rows)
    docs["holidays_CBOE"] = _doc("holidays_CBOE", ("2006-01-01", "2027-12-31"), "CBOE", [_hol(d) for d in sorted(closed)])
    fed = set()
    for y in range(2015, 2028):
        fed |= _federal(y)
    docs["holidays_FED"] = _doc("holidays_FED", ("2015-01-01", "2027-12-31"), "FED", [_hol(d) for d in sorted(fed)])
    sifma = {d for d in fed} | {_easter(y) - timedelta(days=2) for y in range(2015, 2028)}
    sifma_rows = [_hol(d) for d in sorted(sifma)] + [_hol(_nth(y, 11, 3, 4) + timedelta(days=1), "early_close", "14:00")
                                                     for y in range(2015, 2028)]
    docs["holidays_SIFMA"] = _doc("holidays_SIFMA", ("2015-01-01", "2027-12-31"), "SIFMA", sifma_rows)
    docs["holidays_CME"] = _doc("holidays_CME", ("2015-01-01", "2027-12-31"), "CME", [_hol(d) for d in sorted(fed)])
    asia = ("2015-01-01", "2027-12-31")
    jpx = [_hol(date(y, m, d)) for y in range(2015, 2028) for m, d in ((1, 1), (1, 2), (1, 3), (2, 11), (4, 29), (5, 3), (5, 4), (5, 5),
                                                                       (8, 11), (11, 3), (11, 23), (12, 31))]
    docs["holidays_JPX"] = _doc("holidays_JPX", asia, "JPX", jpx)
    sse = [_hol(date(y, m, d)) for y in range(2015, 2028) for m, d in ((1, 1), (5, 1), (5, 2), (10, 1), (10, 2), (10, 3), (10, 6), (10, 7))]
    docs["holidays_SSE"] = _doc("holidays_SSE", asia, "SSE", sse)
    hk = [_hol(date(y, m, d)) for y in range(2015, 2028) for m, d in ((1, 1), (7, 1), (10, 1), (12, 25), (12, 26))]
    docs["holidays_HKEX"] = _doc("holidays_HKEX", asia, "HKEX", hk)
    tw = [_hol(date(y, m, d)) for y in range(2015, 2028) for m, d in ((1, 1), (2, 28), (4, 4), (4, 5), (10, 10))]
    docs["holidays_TWSE"] = _doc("holidays_TWSE", asia, "TWSE", tw)
    docs["market_closes"] = _doc("market_closes", asia, "WEEKDAYS", [
        _row(kind="close", market="CN", open_local="09:30", close_local="15:00", tz="Asia/Shanghai"),
        _row(kind="close", market="HK", open_local="09:30", close_local="16:00", tz="Asia/Hong_Kong"),
        _row(kind="close", market="TW", open_local="09:00", close_local="13:30", tz="Asia/Taipei")])
    docs["kr_sessions"] = _doc("kr_sessions", span, "KRX", [
        _row(kind="regular_open", open_kst="09:00"),
        _row(kind="lunch_break", window_kst=["12:00", "13:00"], effective_to="2000-05-21"),
        _row(kind="csat_day", date="2015-11-12", effective_from="2015-11-12", effective_to="2015-11-12"),
        _row(kind="csat_day", date="2025-11-13", effective_from="2025-11-13", effective_to="2025-11-13"),
        _row(kind="saturday_close", close_kst="11:30", effective_to="1998-12-11"),
        _row(kind="random_end_extension", session_date="2014-06-02", extension_s=45)])
    docs["publication_schedules"] = _doc("publication_schedules", span, "WEEKDAYS", [
        _row(schedule_id="H15", rule="next_bday_after_obs", calendar="FED", time="16:15", tz=NY),
        _row(schedule_id="H10", rule="monday_after_week", calendar="FED", time="16:15", tz=NY),
        _row(schedule_id="TREASURY_PAR", rule="same_day", calendar="SIFMA", time="18:00", tz=NY),
        _row(schedule_id="BLS", rule="release_calendar", calendar="FED", time="08:30", tz=NY),
        _row(schedule_id="VIXCLS_CBOE", rule="same_day", calendar="CBOE", time="16:15", tz=NY),
        _row(schedule_id="VIXCLS_FRED", rule="channel_posting_time", calendar="NYSE", time="16:15", tz=NY,
             declared_lag_bdays=1, declared_time="09:00"),
        _row(schedule_id="ECOS_USDKRW", rule="same_day", calendar="ECOS", time="15:00", tz=KST, effective_to="2016-07-31"),
        _row(schedule_id="ECOS_USDKRW", rule="same_day", calendar="ECOS", time="15:30", tz=KST, effective_from="2016-08-01"),
        _row(schedule_id="KODEX200_PDF", rule="next_bday_after_obs", calendar="KRX", time="08:00", tz=KST),
    ] + [_row(schedule_id=f"MARKET_CLOSE_{m}", rule="market_close", market=m) for m in clocks.M1_MARKETS])
    docs["source_skipped"] = _doc("source_skipped", span, "WEEKDAYS", [
        _row(series="DEXKOUS", date=d, effective_from=d, effective_to=d, reason="H.10 not published")
        for d in ("2017-01-20", "2018-12-05", "2020-11-27", "2020-12-24")
    ] + [_row(series="DTWEXBGS", date=d, effective_from=d, effective_to=d, reason="DC storm") for d in ("2016-01-22", "2018-03-02")])
    docs["kr_regime_tags"] = _doc("kr_regime_tags", span, "KRX", _regime_rows())
    return docs


def _regime_rows() -> list[dict]:
    spans = {
        "price_limit": [("1995-01-01", "1995-03-31", 0.046), ("1995-04-01", "1996-11-24", 0.06), ("1996-11-25", "1998-03-01", 0.08),
                        ("1998-03-02", "1998-12-06", 0.12), ("1998-12-07", "2015-06-14", 0.15), ("2015-06-15", None, 0.30)],
        "saturday_session": [("1995-01-01", "1998-12-11", True), ("1998-12-12", None, False)],
        "close_time_kst": [("1995-01-01", "2016-07-31", "15:00"), ("2016-08-01", None, "15:30")],
        "closing_call": [("1995-01-01", "2016-07-31", "14:50-15:00"), ("2016-08-01", None, "15:20-15:30")],
        "random_end": [("1995-01-01", "2015-06-14", "conditional"), ("2015-06-15", None, "unconditional_le_30s")],
        "lunch_break": [("1995-01-01", "2000-05-21", "12:00-13:00"), ("2000-05-22", None, "none")],
        "fx_regime": [("1995-01-01", "1997-09-21", "market_average_rate"), ("1997-09-22", "1997-10-17", "peg_1997"),
                      ("1997-10-18", None, "free_float")],
        "etf_available": [("1995-01-01", "2002-10-13", False), ("2002-10-14", None, True)],
        "short_sale_ban": [("1995-01-01", "2008-09-30", False), ("2008-10-01", "2009-05-31", True), ("2009-06-01", "2011-08-10", False),
                           ("2011-08-11", "2011-11-09", True), ("2011-11-10", "2020-03-15", False), ("2020-03-16", "2021-05-02", True),
                           ("2021-05-03", "2023-11-05", False), ("2023-11-06", "2025-03-30", True), ("2025-03-31", None, False)],
        "short_sale_regime": [("1995-01-01", "2020-03-15", "none"), ("2020-03-16", "2021-05-02", "full_ban"),
                              ("2021-05-03", "2023-11-05", "partial_ban_non_index"), ("2023-11-06", "2025-03-30", "full_ban"),
                              ("2025-03-31", None, "none")],
        "sell_tax_pct": [("1995-01-01", "2019-05-29", 0.30), ("2019-05-30", "2020-12-31", 0.25), ("2021-01-01", "2022-12-31", 0.23),
                         ("2023-01-01", "2023-12-31", 0.20), ("2024-01-01", "2024-12-31", 0.18), ("2025-01-01", "2025-12-31", 0.15),
                         ("2026-01-01", None, 0.20)],
        "tick_regime": [("1995-01-01", "2023-01-24", "pre_2023"), ("2023-01-25", "2023-12-10", "stocks_2023_01_25"),
                        ("2023-12-11", None, "etf_w1_2023_12_11")],
        "letf_rules": [("1995-01-01", "2026-05-26", "none"), ("2026-05-27", "2026-07-15", "rule_2026_05_27"), ("2026-07-16", None, "rule_2026_07_16")],
        "usdkrw_onshore_hours": [("1995-01-01", "2016-07-31", "close_15:00"), ("2016-08-01", "2024-06-30", "close_15:30"),
                                 ("2024-07-01", "2026-07-05", "close_02:00_next_day"), ("2026-07-06", None, "24h")],
        "value_up": [("1995-01-01", "2024-02-25", "pre"), ("2024-02-26", None, "post_2024_02_26")],
    }
    assert set(spans) == set(regime.TAGS)
    return [_row(tag=t, value=v, effective_from=lo, effective_to=hi) for t, s in spans.items() for lo, hi, v in s]


def fixture_set(key: str = "main", docs: dict | None = None) -> CalendarSet:
    """A signed temp-dir calendar set (cached per key for the process; the temp dir lives with the cache)."""
    if key not in _CACHE:
        tmp = tempfile.TemporaryDirectory(prefix="quantgen_cal_")
        _write_set(Path(tmp.name), docs if docs is not None else fixture_docs())
        _CACHE[key] = (tmp, CalendarSet(Path(tmp.name)))
    return _CACHE[key][1]


def _raises(fn, exc) -> Exception:
    try:
        fn()
    except exc as e:
        return e
    raise AssertionError(f"expected {exc.__name__}")


# --------------------------------------------------------------------------- #
# REFDATA bodies on the KRX official closes (look-ahead audit LA-02, part 1: T-PRINT-01, T-SAT-01)
# --------------------------------------------------------------------------- #
# F01 is written by docs/macro_fixtures.py: the reference file's own columns, then the section 4.1 provenance columns.
# ACQUISITION.csv and the spec name no reference column, so the layout is declared here: the official close is the
# column `close`; obs_date and session_date are ISO dates (equal); obs_utc and available_at_utc are UTC instants written
# YYYY-MM-DDTHH:MM:SSZ; every row is KOSPI_OFFICIAL_CLOSE / official_close / calendar_bound (the F01 row of
# docs/macro_fixtures.REFERENCE_FILES); rows are in date order. Other columns are ignored.
F01 = "krx_kospi_official_close_1997-01-03_2026-10-02.csv"
F01_SPAN = (date(1997, 1, 3), date(2026, 10, 2))
F01_COLUMNS = ("close", "series_id", "obs_date", "session_date", "obs_utc", "available_at_utc", "available_at_source",
               "value_status")
# T-PRINT-01 (spec L5631; L1382): "The KOSPI close on 2026-03-09 is 5,251.87 (-5.96%). The intraday -8.11% is never
# stored as a close." The close is a price (Level 1 `price`, exact); the returns are checked at their printed precision.
PRINT01_DATE, PRINT01_CLOSE, PRINT01_RETURN_PCT, PRINT01_INTRADAY_PCT = date(2026, 3, 9), 5251.87, -5.96, -8.11
PRINTED_PCT = 0.005
# T-SAT-01 (spec L2097): Saturday sessions before 1998-12-12 (rules calendars.KR.saturday_sessions_before); the Monday /
# Tue-Fri variance ratio of 1997-98 (2.30, EX2) is printed, not asserted.
SAT01_BEFORE, SAT01_RATIO_SPAN = date(1998, 12, 12), (date(1997, 1, 1), date(1998, 12, 31))


def _utc_z(text: str) -> datetime:
    if not text.endswith("Z"):
        raise AssertionError(f"{F01}: instant {text!r} is not written YYYY-MM-DDTHH:MM:SSZ")
    return datetime.fromisoformat(text[:-1]).replace(tzinfo=UTC)


def _kospi_closes(text: str) -> list[dict]:
    """F01 rows in the declared layout as {date, close, obs_utc, available_at_utc}; AssertionError on any departure."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in F01_COLUMNS if c not in (reader.fieldnames or ())]
    assert not missing, f"{F01}: declared columns {missing} absent (header {reader.fieldnames})"
    rows: list[dict] = []
    for line, raw in enumerate(reader, start=2):
        where = f"{F01} line {line}"
        assert (raw["series_id"], raw["value_status"], raw["available_at_source"]) == (
            "KOSPI_OFFICIAL_CLOSE", "official_close", "calendar_bound"), f"{where}: not an official KOSPI close row"
        d = date.fromisoformat(raw["session_date"])
        assert date.fromisoformat(raw["obs_date"]) == d, f"{where}: obs_date != session_date"
        close = float(raw["close"])
        assert math.isfinite(close) and close > 0, f"{where}: close {raw['close']!r}"
        assert not rows or rows[-1]["date"] <= d, f"{where}: rows out of date order"
        rows.append({"date": d, "close": close, "obs_utc": _utc_z(raw["obs_utc"]),
                     "available_at_utc": _utc_z(raw["available_at_utc"])})
    assert rows, f"{F01}: no rows"
    return rows


# The declared close layout of the LA-02 part 2 REFDATA bodies, read by one reader. F13 (yahoo_KS11), F14
# (yahoo_GSPC), F16 (yahoo_KRWX) and F27 (krx_005930_000660, long form) are declared in F01's layout above, and F01 is
# read in it where G-POST-01 reads it: the close in `close`, then the section 4.1 provenance columns docs/macro_fixtures.py
# writes, with the series_id (F27: either of its two ids), value_status and available_at_source its REFERENCE_FILES row
# gives the file; F27 adds `code`, one of its two ids. Every part 2 body that reads one of these files
# (tests/macro_m1_pit.py, tests/macro_m1_fixtures.py, tests/macro_m2_risk.py, tests/macro_m3_estimators.py) calls
# `read_close_layout`, so one rule holds for all of them:
#   - a close is a finite number > 0; a blank or "." cell (FRED's missing-value marker) is no close, and the file is
#     refused at that line: the generator writes one row per reference row, so a close file has no missing-value row;
#   - no date repeats (in F27, no date and code pair) and rows are in date order;
#   - obs_date = session_date, written YYYY-MM-DD;
#   - obs_utc and available_at_utc are written YYYY-MM-DDTHH:MM:SSZ, and available_at_utc is not before obs_utc.
# What each body then reads (point-in-time visibility, the dates up to its decision) stays with the body. Part 1's F01
# reader `_kospi_closes` above is not this reader: T-PRINT-01 and T-SAT-01 on F01 count a repeated date's rows themselves.
CLOSE_LAYOUT_FILES = ("F01", "F13", "F14", "F16", "F27")
CLOSE_LAYOUT_KEYS = {"F27": "code"}
CLOSE_LAYOUT_INSTANT = "%Y-%m-%dT%H:%M:%SZ"


def close_layout_file(fid: str) -> tuple[str, tuple[str, ...], str, str]:
    """(file name, series ids, value_status, available_at_source) of `fid`, from docs/macro_fixtures.REFERENCE_FILES."""
    from docs import macro_fixtures as MF
    assert fid in CLOSE_LAYOUT_FILES, f"{fid}: not a file of the declared close layout {CLOSE_LAYOUT_FILES}"
    found = [(Path(rel).name, tuple(series.split(";")), status, source)
             for f, rel, series, status, source, *_rest in MF.REFERENCE_FILES if f == fid]
    assert len(found) == 1, f"{fid}: {len(found)} rows in docs/macro_fixtures.REFERENCE_FILES"
    return found[0]


def _layout_instant(where: str, text: str) -> datetime:
    try:
        return datetime.strptime(text or "", CLOSE_LAYOUT_INSTANT).replace(tzinfo=UTC)
    except ValueError:
        raise AssertionError(f"{where}: instant {text!r} is not written YYYY-MM-DDTHH:MM:SSZ") from None


def read_close_layout(fid: str, text: str) -> list[dict]:
    """`fid` (F01, F13, F14, F16 or F27) in the declared close layout, as {date, close, series_id, obs_utc,
    available_at_utc[, code]} rows in file order; AssertionError naming the file and line on any departure from it."""
    name, series, status, source = close_layout_file(fid)
    key = CLOSE_LAYOUT_KEYS.get(fid)
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in F01_COLUMNS + ((key,) if key else ()) if c not in (reader.fieldnames or ())]
    assert not missing, f"{name}: declared columns {missing} absent (header {reader.fieldnames})"
    rows: list[dict] = []
    seen: set = set()
    for line, raw in enumerate(reader, start=2):
        where = f"{name} line {line}"
        assert raw["series_id"] in series and (raw["value_status"], raw["available_at_source"]) == (status, source), (
            f"{where}: not a {'/'.join(series)} / {status} / {source} row (series_id {raw['series_id']!r}, "
            f"value_status {raw['value_status']!r}, available_at_source {raw['available_at_source']!r})")
        try:
            d = date.fromisoformat(raw["session_date"] or "")
        except ValueError:
            d = None
        assert d is not None and raw["session_date"] == raw["obs_date"] == d.isoformat(), (
            f"{where}: obs_date != session_date or not written YYYY-MM-DD ({raw['obs_date']!r}, "
            f"{raw['session_date']!r})")
        try:
            close = float((raw["close"] or "").strip())
        except ValueError:
            close = math.nan
        assert math.isfinite(close) and close > 0, (
            f"{where}: close {raw['close']!r} is not a finite number > 0 (a blank or '.' close is no close)")
        obs, avail = _layout_instant(where, raw["obs_utc"]), _layout_instant(where, raw["available_at_utc"])
        assert avail >= obs, f"{where}: available_at_utc {raw['available_at_utc']} before obs_utc {raw['obs_utc']}"
        if key:
            assert raw[key] in series, f"{where}: {key} {raw[key]!r} not in {series}"
        k = (d, raw[key]) if key else d
        assert (not rows or rows[-1]["date"] <= d) and k not in seen, f"{where}: rows out of date order or repeated"
        seen.add(k)
        rows.append({"date": d, "close": close, "series_id": raw["series_id"], "obs_utc": obs, "available_at_utc": avail,
                     **({key: raw[key]} if key else {})})
    assert rows, f"{name}: no rows"
    return rows


def close_layout_text(fid: str, rows) -> str:
    """(date, close, obs_utc, available_at_utc[, code]) rows written in memory in the declared close layout of `fid`,
    as docs/macro_fixtures.py writes the file: a `date` reference column (and `code` for F27), then F01_COLUMNS, every
    row carrying the file's first series id. A close given as a string is written verbatim (a demonstration's blank or
    "." cell). For the demonstrations."""
    _name, series, status, source = close_layout_file(fid)
    key = CLOSE_LAYOUT_KEYS.get(fid)
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow(("date",) + ((key,) if key else ()) + F01_COLUMNS)
    for d, close, obs, avail, *code in rows:
        cell = close if isinstance(close, str) else repr(float(close))
        out.writerow((d.isoformat(), *code, cell, series[0], d.isoformat(), d.isoformat(),
                      obs.astimezone(UTC).strftime(CLOSE_LAYOUT_INSTANT), avail.astimezone(UTC).strftime(CLOSE_LAYOUT_INSTANT),
                      source, status))
    return buf.getvalue()


def _official_calendar(lo: date, hi: date, live: CalendarSet | None = None) -> CalendarSet:
    """The shipped owner-signed KRX clock files (`live`, default `CalendarSet()`) when each loads and covers [lo, hi];
    otherwise NotRun("OWNER: ...") naming every refusal and coverage gap, computed from the files as
    test_close02_on_the_real_signed_files does. Both branches are pinned by the T-PRINT-01 and T-SAT-01 demonstrations
    on synthetic sets."""
    live = CalendarSet() if live is None else live
    waiting = []
    for f in store.MARKET_FILES["KR"]:
        why = live.refusal(f)
        if why is not None:
            waiting.append(f"{f}.yaml refused ({why})")
        elif not (live.file(f).covers(lo) and live.file(f).covers(hi)):
            cf = live.file(f)
            waiting.append(f"{f}.yaml v{cf.version} covers {cf.covers_from}..{cf.covers_to}")
    if waiting:
        raise NotRun(f"OWNER: the signed KRX clock files must cover {lo}..{hi}: " + "; ".join(waiting))
    return live


def _official_calendar_on(lo: date, hi: date, live: CalendarSet) -> CalendarSet:
    """`_official_calendar` on a set that covers [lo, hi], for the demonstrations: a NotRun there is a FAIL."""
    try:
        return _official_calendar(lo, hi, live=live)
    except NotRun as exc:
        raise AssertionError(f"_official_calendar refused a covering set: {exc.reason}") from None


def _check_print01(rows: list[dict], cal: CalendarSet) -> float:
    """T-PRINT-01 on official closes: exactly one row on 2026-03-09, stamped at the scheduled close and inside the
    close-print bound (`clocks.close_stamp`: an intraday print is refused), close 5,251.87, -5.96% against the previous
    session's row, and not the -8.11% print. Returns the return in percent."""
    d = PRINT01_DATE
    on_day = [r for r in rows if r["date"] == d]
    assert len(on_day) == 1, f"T-PRINT-01: {len(on_day)} rows on {d}; exactly one official close is stored"
    row = on_day[0]
    try:
        stamp = clocks.close_stamp("KR", d, row["available_at_utc"], cal=cal)
    except (clocks.IntradayPrint, clocks.CloseAfterBound) as exc:
        raise AssertionError(f"T-PRINT-01: the {d} row is not an official close: {exc}") from None
    assert row["obs_utc"] == stamp.obs_utc, f"T-PRINT-01: obs_utc {row['obs_utc']} != scheduled close {stamp.obs_utc}"
    assert row["close"] == PRINT01_CLOSE, f"T-PRINT-01: close {row['close']!r} != {PRINT01_CLOSE} (spec L5631)"
    before = [r for r in rows if r["date"] < d]
    prev_day = clocks.prev_session("KR", d, cal=cal)
    assert before and before[-1]["date"] == prev_day, f"T-PRINT-01: no row for the previous session {prev_day}"
    ret_pct = 100.0 * (row["close"] / before[-1]["close"] - 1.0)
    assert abs(ret_pct - PRINT01_RETURN_PCT) <= PRINTED_PCT + 1e-9, f"T-PRINT-01: return {ret_pct:.4f}% != -5.96%"
    assert abs(ret_pct - PRINT01_INTRADAY_PCT) > PRINTED_PCT, "T-PRINT-01: the -8.11% intraday print is stored as the close"
    return ret_pct


def _check_sat01(rows: list[dict], cal: CalendarSet, start: date, end: date) -> dict:
    """T-SAT-01 on official closes: no row lies outside [start, end]; every `is_session` date of it has exactly one close
    row and no row falls on a non-session (`clocks.completeness_check`); no Saturday row lies on or after 1998-12-12;
    and, when the span starts before 1998-12-12, the same rows without their Saturday closes fail the completeness check
    with exactly those Saturdays missing (spec L2097: "A KOSPI fixture that lacks those Saturdays fails the completeness
    check"). On a calendar consistent with the rows, the last two clauses fail only when the calendar's Saturday rule
    is wrong (no Saturday sessions, or Saturday sessions past 1998-12-11); the demonstrations show both. Returns the
    counts and the Monday / Tue-Fri variance ratio of the 1997-98 close-to-close returns (None outside that span)."""
    dates = [r["date"] for r in rows]
    assert start <= dates[0] and dates[-1] <= end, f"T-SAT-01: rows span {dates[0]}..{dates[-1]}, outside {start}..{end}"
    rep = clocks.completeness_check("KR", dates, start, end, cal=cal)
    assert rep.ok, (f"T-SAT-01: completeness fails: missing {list(rep.missing[:8])} of {len(rep.missing)}, "
                    f"duplicates {list(rep.duplicates[:8])}, extra {list(rep.extra[:8])}")
    sats = tuple(d for d in dates if d.weekday() == 5)
    late = [d for d in sats if d >= SAT01_BEFORE]
    assert not late, f"T-SAT-01: a Saturday close on or after 1998-12-12 ({late[0]}; spec L2097)"
    if start < SAT01_BEFORE:
        gap = clocks.completeness_check("KR", [d for d in dates if d.weekday() != 5], start, end, cal=cal)
        assert sats and not gap.ok and gap.missing == sats and not gap.duplicates and not gap.extra, (
            f"T-SAT-01: the rows without their Saturday closes do not fail the completeness check with exactly those "
            f"Saturdays missing ({len(sats)} Saturday rows, missing {list(gap.missing[:8])}; spec L2097)")
    mon, tue_fri = [], []
    for a, b in zip(rows, rows[1:]):
        if SAT01_RATIO_SPAN[0] <= b["date"] <= SAT01_RATIO_SPAN[1] and b["date"].weekday() < 5:
            (mon if b["date"].weekday() == 0 else tue_fri).append(b["close"] / a["close"] - 1.0)
    ratio = statistics.variance(mon) / statistics.variance(tue_fri) if len(mon) > 1 and len(tue_fri) > 1 else None
    return {"sessions": len(dates), "saturdays": len(sats), "ratio": ratio}


def _invented_closes(cal: CalendarSet, lo: date, hi: date, last=(), stamped: bool = True) -> list[tuple]:
    """Invented closes (not KRX data) on every KR session of [lo, hi] of `cal`, stamped as docs/macro_fixtures stamps F01
    (obs_utc the scheduled close, available_at_utc the close-print bound); `last` replaces the final closes.
    `stamped=False` writes 00:00Z on the session date instead (well-formed instants; the T-SAT-01 body reads no stamp)."""
    days = clocks.sessions_between("KR", lo, hi, cal=cal)
    closes = [700.0 + (i % 23) * 1.5 - (i % 7) for i in range(len(days))]
    closes[len(days) - len(last):] = list(last)
    if not stamped:
        return [(d, c, U(d.year, d.month, d.day), U(d.year, d.month, d.day)) for d, c in zip(days, closes)]
    stamps = [clocks.close_stamp("KR", d, cal=cal) for d in days]
    return [(d, c, s.obs_utc, s.available_at_utc) for d, c, s in zip(days, closes, stamps)]


def _f01_text(rows) -> str:
    """(date, close, obs_utc, available_at_utc) rows written in the declared F01 layout, in memory."""
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow(("date",) + F01_COLUMNS)
    z = lambda t: t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")                     # noqa: E731
    for d, close, obs, avail in rows:
        out.writerow((d.isoformat(), repr(close), "KOSPI_OFFICIAL_CLOSE", d.isoformat(), d.isoformat(), z(obs), z(avail),
                      "calendar_bound", "official_close"))
    return buf.getvalue()


def krx_short_set() -> CalendarSet:
    """The synthetic set with holidays_KRX cut to 2026-01-01..2027-12-31, the span of the shipped signed file, so every
    earlier KRX date is a coverage gap (the OWNER branch of `_official_calendar` and of T-AVAIL-01's waiting list)."""
    docs = fixture_docs()
    krx = docs["holidays_KRX"]
    krx["covers"] = {"from": "2026-01-01", "to": "2027-12-31"}
    krx["rows"] = [r for r in krx["rows"] if r["date"] >= "2026-01-01"]
    return fixture_set("krx_2026_2027", docs)


def drafts_set() -> CalendarSet:
    """The synthetic set with holidays_KRX and kr_regime_tags unsigned, so both are refused at load."""
    docs = fixture_docs()
    for f in ("holidays_KRX", "kr_regime_tags"):
        docs[f]["signed_off_by"] = None
    return fixture_set("krx_drafts", docs)


def _saturday_rule_set(before: str) -> CalendarSet:
    """fixture_set()'s files under a calendars config whose KR `saturday_sessions_before` is `before`: a wrong Saturday
    rule, for the T-SAT-01 FAIL demonstrations (the config is injected into a new CalendarSet; nothing is patched)."""
    base = fixture_set()
    cfg = copy.deepcopy(base.config)
    cfg["KR"]["saturday_sessions_before"] = before
    return CalendarSet(base.data_dir, config=cfg)


# --------------------------------------------------------------------------- #
# T-CLOSE-01 / T-CLOSE-02 / T-PRINT-01
# --------------------------------------------------------------------------- #
def test_close01_decision_time_and_bound():
    """KR 2026-10-02: 06:30Z / 06:30:30Z; a print at 06:30:20Z accepted, one at 06:31Z rejected; US 2026-10-01 20:00Z /
    20:00:30Z (EDT); US 2026-01-15 21:00Z (EST); the legacy v1.2 API still answers."""
    cal = fixture_set()
    d = date(2026, 10, 2)
    assert clocks.decision_time_utc("KR", d, cal=cal) == U(2026, 10, 2, 6, 30)
    assert clocks.close_print_bound_utc("KR", d, cal=cal) == U(2026, 10, 2, 6, 30, 30)
    ok = clocks.close_stamp("KR", d, U(2026, 10, 2, 6, 30, 20), cal=cal)
    assert ok.available_at_utc == U(2026, 10, 2, 6, 30, 20) and ok.available_at_source == "exchange_print"
    assert ok.obs_utc == U(2026, 10, 2, 6, 30)
    _raises(lambda: clocks.close_stamp("KR", d, U(2026, 10, 2, 6, 31), cal=cal), clocks.CloseAfterBound)
    bound = clocks.close_stamp("KR", d, None, cal=cal)
    assert bound.available_at_utc == U(2026, 10, 2, 6, 30, 30) and bound.available_at_source == "calendar_bound"
    assert clocks.decision_time_utc("US", date(2026, 10, 1), cal=cal) == U(2026, 10, 1, 20, 0)
    assert clocks.close_print_bound_utc("US", date(2026, 10, 1), cal=cal) == U(2026, 10, 1, 20, 0, 30)
    assert clocks.close_stamp("US", date(2026, 10, 1), U(2026, 10, 1, 20, 0, 2), cal=cal).available_at_source == "exchange_print"
    assert clocks.decision_time_utc("US", date(2026, 1, 15), cal=cal) == U(2026, 1, 15, 21, 0)
    # quarantine anchor used by the data layer: bound + 10 min
    assert clocks.close_print_bound_utc("KR", d, cal=cal) + timedelta(minutes=10) == U(2026, 10, 2, 6, 40, 30)
    # the legacy API is unchanged by the package conversion (spec L1991 "API unchanged from v1.2")
    from core import calendars as legacy
    assert legacy.is_trading_day("US", date(2026, 11, 26)) is False and legacy.get("KRX").source["library"] == "exchange_calendars"
    covers = legacy.coverage("US")
    assert legacy.is_trading_day("US", date(covers[1].year + 5, 6, 15)) is None
    assert legacy.decision_time_utc is clocks.decision_time_utc        # lazy re-export


test_close01_decision_time_and_bound.test_ids = ["T-CLOSE-01"]


def test_close02_effective_dated_clocks():
    cal = fixture_set()
    D = clocks.decision_time_utc
    B = clocks.close_print_bound_utc
    assert D("KR", date(2016, 7, 29), cal=cal) == U(2016, 7, 29, 6, 0)
    assert D("KR", date(2016, 8, 1), cal=cal) == U(2016, 8, 1, 6, 30)
    assert B("KR", date(2016, 7, 29), cal=cal) == U(2016, 7, 29, 6, 0, 30)
    assert B("KR", date(2016, 8, 1), cal=cal) == U(2016, 8, 1, 6, 30, 30)
    assert B("KR", date(2015, 6, 15), cal=cal) == U(2015, 6, 15, 6, 0, 30)      # first unconditional day
    assert B("KR", date(2015, 6, 12), cal=cal) == U(2015, 6, 12, 6, 0, 30)      # conditional era: + 30 s tolerance, no extension row
    assert B("KR", date(2014, 6, 2), cal=cal) == U(2014, 6, 2, 6, 1, 15)        # + 30 s + the signed 45 s extension
    assert D("KR", date(2025, 11, 13), cal=cal) == U(2025, 11, 13, 7, 30) and B("KR", date(2025, 11, 13), cal=cal) == U(2025, 11, 13, 7, 30, 30)
    # pre-2016 CSAT and a pre-1998-12-12 Saturday: assert against the fixture file, not a hard-coded hour
    kr = cal.file("kr_sessions")
    csat_cfg = store.effective_config(cal.market_config("KR")["csat_session_kst"], date(2015, 11, 12), "csat")["window"][1]
    hh, mm = map(int, csat_cfg.split(":"))
    want = datetime.combine(date(2015, 11, 12), time(hh, mm), tzinfo=ZoneInfo(KST)).astimezone(UTC)
    assert D("KR", date(2015, 11, 12), cal=cal) == want and B("KR", date(2015, 11, 12), cal=cal) == want + timedelta(seconds=30)
    sat = date(1997, 6, 7)
    assert sat.weekday() == 5 and clocks.is_session("KR", sat, cal=cal)
    sat_close = next(r["close_kst"] for r in kr.rows if r["kind"] == "saturday_close")
    hh, mm = map(int, sat_close.split(":"))
    want = datetime.combine(sat, time(hh, mm), tzinfo=ZoneInfo(KST)).astimezone(UTC)
    assert D("KR", sat, cal=cal) == want and B("KR", sat, cal=cal) == want + timedelta(seconds=30)
    assert "saturday" in clocks.session("KR", sat, cal=cal).flags
    _raises(lambda: D("KR", date(2026, 10, 5), cal=cal), NotASession)
    _raises(lambda: D("KR", date(2026, 10, 4), cal=cal), NotASession)                   # Sunday
    assert D("US", date(2026, 11, 27), cal=cal) == U(2026, 11, 27, 18, 0)
    assert D("US", date(2025, 7, 3), cal=cal) == U(2025, 7, 3, 17, 0)
    assert B("US", date(2026, 10, 1), cal=cal) == U(2026, 10, 1, 20, 0, 30)
    _raises(lambda: D("US", date(2026, 11, 26), cal=cal), NotASession)
    assert clocks.regime_tags if False else regime.regime_tags("KR", date(1997, 6, 7), cal=cal)["saturday_session"] is True
    # a Saturday without a signed close never falls back to the weekday close
    docs = fixture_docs()
    docs["kr_sessions"]["rows"] = [r for r in docs["kr_sessions"]["rows"] if r["kind"] != "saturday_close"]
    bare = fixture_set("no_saturday_close", docs)
    assert clocks.is_session("KR", sat, cal=bare)
    _raises(lambda: D("KR", sat, cal=bare), CalendarUnsigned)
    # session() content
    s = clocks.session("KR", date(2026, 10, 2), cal=cal)
    assert s.open_local == time(9, 0) and s.close_local == time(15, 30) and s.closing_call_local == (time(15, 20), time(15, 30))
    assert s.lunch_break_local is None and s.random_end["kind"] == "unconditional" and s.open_utc == U(2026, 10, 2, 0, 0)
    first = clocks.session("KR", date(2026, 1, 2), cal=cal)
    assert "first_trading_day" in first.flags and first.open_local == time(10, 0)
    old = clocks.session("KR", date(1999, 3, 2), cal=cal)
    assert old.lunch_break_local == (time(12, 0), time(13, 0)) and old.closing_call_local == (time(14, 50), time(15, 0))
    csat = clocks.session("KR", date(2025, 11, 13), cal=cal)
    assert "csat" in csat.flags and csat.open_local == time(10, 0) and csat.closing_call_local == (time(16, 20), time(16, 30))
    assert clocks.session("US", date(2026, 11, 27), cal=cal).flags == frozenset({"early_close"})
    # other markets' scheduled closes (today's hours)
    assert D("JP", date(2024, 11, 4), cal=cal) == U(2024, 11, 4, 6, 0) and D("JP", date(2024, 11, 5), cal=cal) == U(2024, 11, 5, 6, 30)
    assert D("CN", date(2026, 10, 8), cal=cal) == U(2026, 10, 8, 7, 0) and D("HK", date(2026, 10, 8), cal=cal) == U(2026, 10, 8, 8, 0)
    assert D("TW", date(2026, 10, 8), cal=cal) == U(2026, 10, 8, 5, 30)
    assert B("JP", date(2026, 10, 8), cal=cal) == D("JP", date(2026, 10, 8), cal=cal)       # close_print_bound_s 0
    _raises(lambda: D("KR", date(1990, 1, 2), cal=cal), CalendarCoverageError)
    assert D("CRYPTO", date(2026, 10, 2), cal=cal) == U(2026, 10, 3, 0, 0)     # M10 R-17 branch (T-CRYPTO-01, tests/macro_m9_lab.py)
    _raises(lambda: D("EU", date(2026, 10, 2), cal=cal), KeyError)


test_close02_effective_dated_clocks.test_ids = ["T-CLOSE-02"]


# T-CLOSE-02 on the owner-signed files (look-ahead audit LA-02, part 2). The signed files each clause of `_check_close02`
# reads (core.calendars.clocks and regime), the days it reads them on, the kr_sessions rows that must exist, and the
# kr_sessions rows it reads, as (kind, session date). A KR clause reads holidays_KRX from 1 January of its year (the
# first trading day check, clocks._is_first_trading_day). The kr_sessions reads follow core.calendars.clocks: every KR
# weekday decision reads the CSAT date list (`_is_csat`: every csat_day row) and, on a CSAT day, the csat_window row
# (`_kr_csat_window`); a Saturday reads its saturday_close row; a bound before 2015-06-15 (the conditional random end)
# reads the session's random_end_extension rows (`_bound_seconds`); `session()` also reads regular_open (not on the
# first session of a year or a CSAT day), lunch_break and, on a CSAT day, csat_closing_call. The demonstration traces
# them on the synthetic set and pins them. The spec gives neither the pre-2016 CSAT window nor the Saturday close: both
# come from the KRX notice and are owner-signed at M1 (spec L2013, L2015, L2063, L2067), so those two clauses also wait
# until their row exists. The conditional-era bounds (2015-06-12, 2014-06-02 and the 1997-06-07 Saturday) are close +
# 30 s + the extension the file signs for the session. A clause waits while the file's `owner_must_sign` (read through
# core.calendars, as the shipped file states it) holds any entry covering a row it reads: the shipped file lists the
# saturday_close rows, the random_end_extension rows before 2015-06-15, the csat_window / csat_closing_call rows before
# 2016-08-01 and "the CSAT date list", so today every KR clause but the regime tag waits (question 14 of
# docs/product/LOOKAHEAD_LA02_PART2_2026-11-10.md: the owner removes an entry when its rows are signed as final, a list
# that may be empty). CRYPTO and an unknown market read no file.
_CLOSE02_KR = ("kr_sessions", "holidays_KRX")
# The kr_sessions row kinds (the shipped file's `notes`: "row kinds: csat_day{date}; saturday_close{close_kst};
# random_end_extension{session_date, extension_s}; lunch_break{window_kst}; regular_open{open_kst}; csat_window{window_kst};
# csat_closing_call{window_kst}"). An owner_must_sign entry covers the kinds it names (and "the CSAT date list" the
# csat_day rows), only on dates before the date it gives ("... before 2015-06-15"); an entry naming no kind covers every
# kr_sessions row (fail closed).
CLOSE02_KR_KINDS = ("csat_day", "saturday_close", "random_end_extension", "lunch_break", "regular_open", "csat_window",
                    "csat_closing_call")
CLOSE02_KIND_NAMES = {"csat_day": ("CSAT date list",)}


def _reads(*pairs) -> tuple[tuple[str, date], ...]:
    """(kind, session date) pairs from ("kind kind ...", date) pairs."""
    return tuple((kind, d) for kinds, d in pairs for kind in kinds.split())


CLOSE02_NEEDS = (
    ("KR 2016-07-29 / 2016-08-01 close and bound", _CLOSE02_KR, date(2016, 1, 1), date(2016, 8, 1), (),
     _reads(("csat_day", date(2016, 7, 29)), ("csat_day", date(2016, 8, 1)))),
    ("KR 2026-01-02 .. 2026-10-05 sessions and non-sessions", _CLOSE02_KR, date(2026, 1, 1), date(2026, 10, 5), (),
     _reads(("csat_day regular_open lunch_break", date(2026, 10, 2)), ("csat_day lunch_break", date(2026, 1, 2)))),
    ("KR 2015-06-12 / 2015-06-15 random-end bound", _CLOSE02_KR, date(2015, 1, 1), date(2015, 6, 15), (),
     _reads(("csat_day random_end_extension", date(2015, 6, 12)), ("csat_day", date(2015, 6, 15)))),
    ("KR 2014-06-02 conditional random-end bound", _CLOSE02_KR, date(2014, 1, 1), date(2014, 6, 2), (),
     _reads(("csat_day random_end_extension", date(2014, 6, 2)))),
    ("KR CSAT 2025-11-13", _CLOSE02_KR, date(2025, 1, 1), date(2025, 11, 13), (),
     _reads(("csat_day csat_window csat_closing_call lunch_break", date(2025, 11, 13)))),
    ("KR pre-2016 CSAT 2015-11-12", _CLOSE02_KR, date(2015, 1, 1), date(2015, 11, 12), ("csat_window",),
     _reads(("csat_day csat_window", date(2015, 11, 12)))),
    ("KR Saturday 1997-06-07", _CLOSE02_KR, date(1997, 1, 1), date(1997, 6, 7), ("saturday_close",),
     _reads(("saturday_close random_end_extension regular_open lunch_break", date(1997, 6, 7)))),
    ("KR regime tag 1997-06-07", ("kr_regime_tags",), date(1997, 6, 7), date(1997, 6, 7), (), ()),
    ("KR 1999-03-02 lunch break and closing call", _CLOSE02_KR, date(1999, 1, 1), date(1999, 3, 2), (),
     _reads(("csat_day random_end_extension regular_open lunch_break", date(1999, 3, 2)))),
    ("US 2025-07-03 .. 2026-11-27 closes", ("holidays_NYSE",), date(2025, 7, 3), date(2026, 11, 27), (), ()),
    ("JP 2024-10-28 .. 2024-11-05 close", ("holidays_JPX",), date(2024, 10, 28), date(2024, 11, 5), (), ()),
    ("JP / CN / HK / TW 2026-10-08 closes", ("holidays_JPX", "holidays_SSE", "holidays_HKEX", "holidays_TWSE",
                                             "market_closes"), date(2026, 10, 8), date(2026, 10, 8), (), ()),
)
CLOSE02_FILES = tuple(dict.fromkeys(f for _clause, files, *_rest in CLOSE02_NEEDS for f in files))


def _owner_entry_covers(entry: str, kind: str, d: date) -> bool:
    """Whether the kr_sessions `owner_must_sign` entry `entry` covers the `kind` row read on `d` (see above)."""
    named = [k for k in CLOSE02_KR_KINDS if re.search(rf"(?<![A-Za-z_]){k}(?![A-Za-z_])", entry)
             or any(alias in entry for alias in CLOSE02_KIND_NAMES.get(k, ()))]
    before = re.search(r"\bbefore (\d{4}-\d{2}-\d{2})\b", entry)
    return (not named or kind in named) and (before is None or d < date.fromisoformat(before.group(1)))


def _close02_waiting(live: CalendarSet) -> list[str]:
    """Each refusal, coverage gap, missing owner-signed kr_sessions row and kr_sessions `owner_must_sign` entry
    covering a row a T-CLOSE-02 clause reads (CLOSE02_NEEDS), computed from `live`; empty when the clauses can run."""
    out = []
    for clause, files, lo, hi, kinds, reads in CLOSE02_NEEDS:
        for f in files:
            why = live.refusal(f)
            if why is not None:
                out.append(f"{clause}: {f}.yaml refused ({why})")
            elif not (live.file(f).covers(lo) and live.file(f).covers(hi)):
                cf = live.file(f)
                out.append(f"{clause}: {f}.yaml v{cf.version} covers {cf.covers_from}..{cf.covers_to}, needs {lo}..{hi}")
        if (kinds or reads) and live.refusal("kr_sessions") is None:
            kr = live.file("kr_sessions")
            on_day = store.effective_rows(kr.rows, hi)
            out += [f"{clause}: kr_sessions.yaml v{kr.version} has no signed {kind} row effective on {hi}"
                    for kind in kinds if not any(r.get("kind") == kind for r in on_day)]
            for entry in (str(item) for item in (kr.doc.get("owner_must_sign") or [])):
                if any(_owner_entry_covers(entry, kind, d) for kind, d in reads):
                    head = re.split(r" \(|: ", entry, maxsplit=1)[0]
                    out.append(f"{clause}: kr_sessions.yaml v{kr.version} lists {head!r} under owner_must_sign")
    return out


def _close02_is(got, want, what: str) -> None:
    assert got == want, f"T-CLOSE-02: {what} is {got}, not {want}"


def _close02_raises(fn, exc, what: str) -> None:
    try:
        fn()
    except exc:
        return
    except Exception as other:                          # noqa: BLE001
        raise AssertionError(f"T-CLOSE-02: {what} raised {type(other).__name__} ({other}), not {exc.__name__}") from None
    raise AssertionError(f"T-CLOSE-02: {what} did not raise {exc.__name__}")


def _at(d: date, hhmm: str, tz: str) -> datetime:
    return datetime.combine(d, time.fromisoformat(hhmm), tzinfo=ZoneInfo(tz)).astimezone(UTC)


def _check_close02(cal: CalendarSet, clk=clocks) -> None:
    """T-CLOSE-02 (spec L2096 and the refined row L5618; rule 1 at L2010-L2016 and L1289; other markets L2021-L2023) on
    `cal`: the clauses of test_close02_effective_dated_clocks, plus the 2026-10-02 bound of L2096. A clause the spec
    states by value is asserted at that value. Where the spec defers to the signed calendar (the pre-2016 CSAT window,
    the Saturday close, a conditional random-end extension, the lunch-break window, the HKEX close), the expected value
    is read from `cal`'s signed rows, as the synthetic test reads its fixture file. `clk` is core.calendars.clocks; the
    FAIL demonstrations pass a wrong clock. Run once nothing is waiting (`_close02_waiting`): a CalendarCoverageError or
    CalendarUnsigned raised here is a FAIL."""
    D, B = clk.decision_time_utc, clk.close_print_bound_utc
    kr = cal.file("kr_sessions")

    def signed(kind: str, d: date) -> list[dict]:
        return [r for r in store.effective_rows(kr.rows, d) if r.get("kind") == kind]

    def extension(d: date):
        """The signed random_end_extension of session d, from the rows effective on d whose session_date is d: 0 s
        without one (the file: "no extension is assumed"; the clause has waited until owner_must_sign no longer lists
        the rows), the row's extension_s with exactly one, and no expected value (the text) with two or more."""
        ext = [r for r in signed("random_end_extension", d) if r.get("session_date") == d.isoformat()]
        if len(ext) > 1:
            return f"one signed random_end_extension row ({len(ext)})"
        return int(ext[0]["extension_s"]) if ext else 0

    def bound(close, ext):
        """close + 30 s + the extension, or the text naming the missing expected value."""
        return close if isinstance(close, str) else ext if isinstance(ext, str) else close + timedelta(seconds=30 + ext)

    def ext_text(ext) -> str:
        return ext if isinstance(ext, str) else f"{ext} s signed"

    # KRX close 15:00 KST (06:00Z) through 2016-07-31 and 15:30 KST (06:30Z) from 2016-08-01; the bound is the close
    # + 30 s from 2015-06-15: 06:00:30Z through 2016-07-29, 06:30:30Z from 2016-08-01 (spec L2096, L5618, L2010, L2012)
    _close02_is(D("KR", date(2016, 7, 29), cal=cal), U(2016, 7, 29, 6, 0), "decision_time_utc('KR', 2016-07-29) (spec L2096)")
    _close02_is(D("KR", date(2016, 8, 1), cal=cal), U(2016, 8, 1, 6, 30), "decision_time_utc('KR', 2016-08-01) (spec L2096)")
    _close02_is(B("KR", date(2016, 7, 29), cal=cal), U(2016, 7, 29, 6, 0, 30),
                "close_print_bound_utc('KR', 2016-07-29) (spec L2096)")
    _close02_is(B("KR", date(2016, 8, 1), cal=cal), U(2016, 8, 1, 6, 30, 30),
                "close_print_bound_utc('KR', 2016-08-01) (spec L5618)")
    _close02_is(B("KR", date(2026, 10, 2), cal=cal), U(2026, 10, 2, 6, 30, 30),
                "close_print_bound_utc('KR', 2026-10-02) (spec L2096)")
    _close02_is(B("KR", date(2015, 6, 15), cal=cal), U(2015, 6, 15, 6, 0, 30),
                "close_print_bound_utc('KR', 2015-06-15), the first unconditional random-end day (spec L5618)")
    # before 2015-06-15: the scheduled close (06:00Z) + the 30 s print tolerance, plus any extension the KRX notice
    # records for the session, read from the signed file (spec L5618, L2012)
    for d in (date(2015, 6, 12), date(2014, 6, 2)):
        ext = extension(d)
        _close02_is(B("KR", d, cal=cal), bound(U(d.year, d.month, d.day, 6, 0), ext),
                    f"close_print_bound_utc('KR', {d}), conditional random end with {ext_text(ext)} (spec L5618)")
    # CSAT day: close 07:30Z, bound 07:30:30Z (spec L2096, L5618)
    _close02_is(D("KR", date(2025, 11, 13), cal=cal), U(2025, 11, 13, 7, 30),
                "decision_time_utc('KR', 2025-11-13), a CSAT day (spec L2096)")
    _close02_is(B("KR", date(2025, 11, 13), cal=cal), U(2025, 11, 13, 7, 30, 30),
                "close_print_bound_utc('KR', 2025-11-13), a CSAT day (spec L2096)")
    # a pre-2016 CSAT date returns the signed calendar's close and bound (spec L2096): the close of the one signed
    # csat_window row (the config window where the set has none, as on the synthetic set; the shipped set waits for the
    # row; two rows are no expected value, as for the Saturday close below), and that close + 30 s (spec L5618)
    d = date(2015, 11, 12)
    window = [r["window_kst"] for r in signed("csat_window", d)] or [
        store.effective_config(cal.market_config("KR")["csat_session_kst"], d, "calendars.KR.csat_session_kst")["window"]]
    want = _at(d, window[0][1], KST) if len(window) == 1 else f"one signed csat_window row ({len(window)})"
    _close02_is(D("KR", d, cal=cal), want, "decision_time_utc('KR', 2015-11-12), a pre-2016 CSAT date (spec L2096)")
    _close02_is(B("KR", d, cal=cal), bound(want, 0),
                "close_print_bound_utc('KR', 2015-11-12), a pre-2016 CSAT date (spec L2096, L5618)")
    # a non-holiday Saturday before 1998-12-12 is a session with the signed Saturday close; its bound is that close
    # + 30 s + any signed extension (conditional era); the regime tag says so (spec L2096, L2015, L5618, L2039)
    sat = date(1997, 6, 7)
    assert sat.weekday() == 5 and clk.is_session("KR", sat, cal=cal), \
        "T-CLOSE-02: the Saturday 1997-06-07 is not a KR session (spec L2015, L5618)"
    closes = [r["close_kst"] for r in signed("saturday_close", sat)]
    want = _at(sat, closes[0], KST) if len(closes) == 1 else f"one signed saturday_close row ({len(closes)})"
    _close02_is(D("KR", sat, cal=cal), want, "decision_time_utc('KR', 1997-06-07), the signed Saturday close (spec L2015)")
    ext = extension(sat)
    _close02_is(B("KR", sat, cal=cal), bound(want, ext),
                f"close_print_bound_utc('KR', 1997-06-07), a Saturday with {ext_text(ext)} (spec L2096, L5618)")
    _close02_is("saturday" in clk.session("KR", sat, cal=cal).flags, True, "session('KR', 1997-06-07) flag 'saturday'")
    _close02_is(regime.regime_tags("KR", sat, cal=cal)["saturday_session"], True,
                "regime_tags('KR', 1997-06-07)['saturday_session'] (spec L2039)")
    # a non-session raises NotASession and never rolls forward (spec L2087): the 2026-10-05 holiday (L2096), a Sunday
    _close02_raises(lambda: D("KR", date(2026, 10, 5), cal=cal), NotASession,
                    "decision_time_utc('KR', 2026-10-05) (spec L2096)")
    _close02_raises(lambda: D("KR", date(2026, 10, 4), cal=cal), NotASession,
                    "decision_time_utc('KR', 2026-10-04), a Sunday (spec L2087)")
    # NYSE: early closes at 13:00 ET (18:00Z in EST on 2026-11-27, 17:00Z in EDT on 2025-07-03), the bound + 30 s
    # (spec L2096, L2021); Thanksgiving 2026-11-26 is no session (L1340: the NYSE is closed on that weekday)
    _close02_is(D("US", date(2026, 11, 27), cal=cal), U(2026, 11, 27, 18, 0), "decision_time_utc('US', 2026-11-27) (spec L2096)")
    _close02_is(D("US", date(2025, 7, 3), cal=cal), U(2025, 7, 3, 17, 0), "decision_time_utc('US', 2025-07-03) (spec L2096)")
    _close02_is(B("US", date(2026, 10, 1), cal=cal), U(2026, 10, 1, 20, 0, 30),
                "close_print_bound_utc('US', 2026-10-01) (spec L2096)")
    _close02_raises(lambda: D("US", date(2026, 11, 26), cal=cal), NotASession,
                    "decision_time_utc('US', 2026-11-26), Thanksgiving (spec L1340, L2087)")
    # sessions: KRX 09:00-15:30, closing auction 15:20-15:30, no lunch break after 2000-05, unconditional random end
    # (spec L1289, L2010-L2012, L2016); the first session of the year opens at 10:00 (L2014); before 2016-08-01 the
    # closing call is 14:50-15:00 (L2011) and a 1999 session has the signed lunch break (L2016: until May-2000); a CSAT
    # day from 2016-08-01 opens at 10:00 with the 16:20-16:30 closing call (L2013, L2064)
    s = clk.session("KR", date(2026, 10, 2), cal=cal)
    _close02_is((s.open_local, s.close_local, s.closing_call_local, s.lunch_break_local, (s.random_end or {}).get("kind"),
                 s.open_utc), (time(9, 0), time(15, 30), (time(15, 20), time(15, 30)), None, "unconditional",
                               U(2026, 10, 2, 0, 0)),
                "session('KR', 2026-10-02) (open, close, closing call, lunch break, random end, open_utc; spec L1289)")
    first = clk.session("KR", date(2026, 1, 2), cal=cal)
    _close02_is(("first_trading_day" in first.flags, first.open_local), (True, time(10, 0)),
                "session('KR', 2026-01-02), the first session of 2026 (spec L2014)")
    old = clk.session("KR", date(1999, 3, 2), cal=cal)
    lunch = [tuple(time.fromisoformat(t) for t in r["window_kst"]) for r in signed("lunch_break", date(1999, 3, 2))]
    _close02_is((old.lunch_break_local, old.closing_call_local),
                (lunch[0] if len(lunch) == 1 else "one signed lunch break", (time(14, 50), time(15, 0))),
                "session('KR', 1999-03-02) (lunch break, closing call; spec L2016, L2011)")
    csat = clk.session("KR", date(2025, 11, 13), cal=cal)
    _close02_is(("csat" in csat.flags, csat.open_local, csat.closing_call_local),
                (True, time(10, 0), (time(16, 20), time(16, 30))), "session('KR', 2025-11-13), a CSAT day (spec L2013, L2064)")
    _close02_is(clk.session("US", date(2026, 11, 27), cal=cal).flags, frozenset({"early_close"}),
                "session('US', 2026-11-27) flags (spec L2021)")
    # other markets: TSE 15:00 JST (06:00Z) through 2024-11-04 and 15:30 JST (06:30Z) from 2024-11-05, bound + 0 s
    # (spec L2022, L2070); SSE 15:00 CST (07:00Z) and TWSE 13:30 TST (05:30Z) (L2023, L1967); HKEX from its signed notice
    # row, at 16:00 HKT (08:00Z) or later (L2023, L1967). The old TSE close is read on the last TSE session of
    # 2024-10-28..2024-11-04 in `cal` (2024-11-04 on the synthetic set; the synthetic test's date, which may be a TSE
    # holiday on the signed file)
    jp_old = next((day for day in (date(2024, 11, 4) - timedelta(days=k) for k in range(8))
                   if clk.is_session("JP", day, cal=cal)), None)
    _close02_is(D("JP", jp_old, cal=cal) if jp_old else "no TSE session in 2024-10-28..2024-11-04",
                U(jp_old.year, jp_old.month, jp_old.day, 6, 0) if jp_old else "a TSE session",
                f"decision_time_utc('JP', {jp_old}), the last TSE session through 2024-11-04 (spec L2022)")
    _close02_is(D("JP", date(2024, 11, 5), cal=cal), U(2024, 11, 5, 6, 30), "decision_time_utc('JP', 2024-11-05) (spec L2022)")
    d = date(2026, 10, 8)
    _close02_is(B("JP", d, cal=cal), D("JP", d, cal=cal), "close_print_bound_utc('JP', 2026-10-08) (spec L2070: + 0 s)")
    _close02_is(D("CN", d, cal=cal), U(2026, 10, 8, 7, 0), "decision_time_utc('CN', 2026-10-08) (spec L2023)")
    _close02_is(D("TW", d, cal=cal), U(2026, 10, 8, 5, 30), "decision_time_utc('TW', 2026-10-08) (spec L2023)")
    hk = [r for r in store.effective_rows(cal.file("market_closes").rows, d) if r.get("kind") == "close"
          and r.get("market") == "HK"]
    hk_close = D("HK", d, cal=cal)
    _close02_is(hk_close, _at(d, hk[0]["close_local"], hk[0]["tz"]) if len(hk) == 1 else f"one signed HK row ({len(hk)})",
                "decision_time_utc('HK', 2026-10-08), the signed HKEX close (spec L2023)")
    assert hk_close >= U(2026, 10, 8, 8, 0), \
        f"T-CLOSE-02: decision_time_utc('HK', 2026-10-08) is {hk_close}, before 16:00 HKT (08:00Z; spec L1967)"
    # outside the signed coverage: CalendarCoverageError (an OPS HALT), never NotASession (spec L2090)
    before = min(kr.covers_from, cal.file("holidays_KRX").covers_from) - timedelta(days=1)
    _close02_raises(lambda: D("KR", before, cal=cal), CalendarCoverageError,
                    f"decision_time_utc('KR', {before}), before the signed coverage (spec L2090)")
    # CRYPTO closes its daily bar at 00:00:00Z on d+1 (spec L5505, T-CRYPTO-01); an unknown market is refused
    _close02_is(D("CRYPTO", date(2026, 10, 2), cal=cal), U(2026, 10, 3),
                "decision_time_utc('CRYPTO', 2026-10-02) (spec L5505)")
    _close02_raises(lambda: D("EU", date(2026, 10, 2), cal=cal), KeyError, "decision_time_utc('EU', 2026-10-02)")


def test_close02_on_the_real_signed_files_is_owner_input():
    """T-CLOSE-02 on the owner-signed files (core.calendars CalendarSet over core/calendars/data): NOT_RUN (OWNER) names
    every refusal, coverage gap, missing owner-signed kr_sessions row and kr_sessions `owner_must_sign` entry covering a
    row its clauses read (CLOSE02_NEEDS), computed from the files; once none is waiting, the clauses run on the signed
    set and PASS or FAIL on `_check_close02` (look-ahead audit LA-02, part 2: it used to be NOT_RUN whatever the files
    held). A coverage or signing error raised inside the clauses is then a FAIL."""
    live = CalendarSet()
    waiting = _close02_waiting(live)
    if waiting:
        raise NotRun("OWNER: T-CLOSE-02 on the signed calendars waits for " + "; ".join(waiting))
    _check_close02(live)


test_close02_on_the_real_signed_files_is_owner_input.test_ids = ["T-CLOSE-02"]


def close02_signed_set() -> CalendarSet:
    """Only the files CLOSE02_NEEDS names, from fixture_docs(), plus a signed csat_window row for the pre-2016 CSAT date
    2015-11-12 (10:00-16:10 KST, invented, so that the signed row and not the config window must govern): nothing that
    T-CLOSE-02 reads is waiting. A file the clauses read that the list does not name is missing here."""
    docs = {k: v for k, v in fixture_docs().items() if k in CLOSE02_FILES}
    docs["kr_sessions"]["rows"].append(_row(kind="csat_window", window_kst=["10:00", "16:10"], effective_from="2015-11-12",
                                            effective_to="2015-11-12"))
    return fixture_set("close02_signed", docs)


def _close02_docs_set(key: str, edit) -> CalendarSet:
    """The CLOSE02_FILES of fixture_docs() with `edit(docs)` applied, signed in a temp dir: a wrong calendar file."""
    docs = {k: v for k, v in fixture_docs().items() if k in CLOSE02_FILES}
    edit(docs)
    return fixture_set(f"close02_{key}", docs)


def _close02_config_set(market: str, key: str, value) -> CalendarSet:
    """fixture_set()'s files under a calendars config whose `market.key` is `value`: a wrong config (nothing patched)."""
    base = fixture_set()
    cfg = copy.deepcopy(base.config)
    cfg[market][key] = value
    return CalendarSet(base.data_dir, config=cfg)


def _clocks_with(**fns) -> types.SimpleNamespace:
    """core.calendars.clocks with the named functions replaced: a wrong clock, for the FAIL demonstrations."""
    names = ("decision_time_utc", "close_print_bound_utc", "is_session", "session")
    return types.SimpleNamespace(**{**{n: getattr(clocks, n) for n in names}, **fns})


def _close02_traced_reads(base: CalendarSet) -> set[tuple[str, date]]:
    """The (kind, session date) kr_sessions reads core.calendars.clocks makes while `_check_close02` runs on `base`,
    traced without patching anything: a CalendarSet over the same files whose kr_sessions rows carry a kind that records
    every kind it is compared with, and a clock (`_clocks_with`) that names the session date of each call. The
    clauses' own reads of the signed rows are not traced."""
    log: set = set()
    day: list = []

    class Kind(str):
        __hash__ = str.__hash__

        def __eq__(self, other):
            if day and isinstance(other, str):
                log.add((other, day[-1]))
            return str.__eq__(self, other)

        def __ne__(self, other):
            return not self.__eq__(other)

    class Traced(CalendarSet):
        _kr = None

        def file(self, file_id):
            f = super().file(file_id)
            if file_id != "kr_sessions":
                return f
            if self._kr is None:
                self._kr = dataclasses.replace(f, rows=tuple({**r, "kind": Kind(r["kind"])} if "kind" in r else r
                                                             for r in f.rows))
            return self._kr

    def traced(name):
        fn = getattr(clocks, name)

        def call(m, d, cal=None):
            day.append(d)
            try:
                return fn(m, d, cal=cal)
            finally:
                day.pop()
        return call

    names = ("decision_time_utc", "close_print_bound_utc", "is_session", "session")
    _check_close02(Traced(base.data_dir, config=base.config), _clocks_with(**{n: traced(n) for n in names}))
    return log


def test_close02_body_passes_and_fails_on_invented_calendars():
    """LA-02 part 2: the T-CLOSE-02 body on the signed files can PASS and can FAIL. `_check_close02` passes on the
    synthetic set (signed in a temp dir by this module; not the owner's files) and on a set holding only the files
    CLOSE02_NEEDS names plus a signed pre-2016 csat_window row, where nothing is waiting (and that row, not the config
    window, sets the close); with a TSE holiday on 2024-11-04 the old TSE close is read on 2024-11-01. It fails, naming
    the clause, on a calendar config, a calendar file or a clock that is wrong for that clause: each KR close and bound, the
    conditional-era bound with and without the signed extension, the CSAT and pre-2016 CSAT close and bound, the
    Saturday session, close, bound, flag and regime tag, the two KR non-sessions, the NYSE early closes, bound and
    holiday, the session contents, the TSE, SSE, TWSE and HKEX closes, the coverage error, CRYPTO and an unknown market;
    two overlapping signed csat_window rows read by a clock that takes the first; two signed random_end_extension rows
    for one session read by a clock that adds them; and an extension row not effective on its own session, which the
    shipped clock still applies. The kr_sessions reads CLOSE02_NEEDS declares are the ones core.calendars.clocks makes,
    traced on the synthetic set. The waiting list is exact on the synthetic sets (a KR clause needs holidays_KRX from
    1 January of its year; a clause waits while any kr_sessions owner_must_sign entry covers a row it reads: the shipped
    file's four entries, each alone, a dated entry and an entry naming no row kind), and the real test's NOT_RUN reason
    is the list computed from the shipped files."""
    cal = fixture_set()
    _check_close02(cal)
    assert _close02_waiting(cal) == ["KR pre-2016 CSAT 2015-11-12: kr_sessions.yaml v1.0.0-fixture has no signed "
                                     "csat_window row effective on 2015-11-12"], _close02_waiting(cal)
    signed = close02_signed_set()
    assert _close02_waiting(signed) == [], _close02_waiting(signed)
    _check_close02(signed)
    assert clocks.decision_time_utc("KR", date(2015, 11, 12), cal=signed) == U(2015, 11, 12, 7, 10)    # the row governs
    # a TSE holiday on 2024-11-04: the old TSE close is read on 2024-11-01, the last session through 2024-11-04
    _check_close02(_close02_docs_set("jpx1104", lambda docs: docs["holidays_JPX"]["rows"].append(_hol(date(2024, 11, 4)))))
    # the kr_sessions reads of each clause, traced through core.calendars.clocks on the synthetic set, are exactly the
    # ones CLOSE02_NEEDS declares (the owner_must_sign rule below rests on them)
    declared = {pair for *_head, reads in CLOSE02_NEEDS for pair in reads}
    traced = _close02_traced_reads(cal)
    assert traced == declared, (sorted(traced - declared), sorted(declared - traced))
    # the signed set with kr_sessions `owner_must_sign` entries: a clause waits while any entry covers a row it reads.
    # The shipped file's four entries, verbatim: every KR clause but the regime tag waits, each naming its entries
    shipped = ["saturday_close rows (saturday_session_close_kst, from_krx_notice): without them decision_time_utc on a "
               "pre-1998-12-12 Saturday raises CalendarUnsigned (never the weekday close)",
               "random_end_extension rows for sessions before 2015-06-15 whose conditional random end was triggered",
               "csat_window / csat_closing_call rows for CSAT days before 2016-08-01", "the CSAT date list"]

    def entries(key, *listed):
        def edit(docs):
            docs["kr_sessions"]["rows"].append(_row(kind="csat_window", window_kst=["10:00", "16:10"],
                                                    effective_from="2015-11-12", effective_to="2015-11-12"))
            docs["kr_sessions"]["owner_must_sign"] = list(listed)
        return _close02_waiting(_close02_docs_set(key, edit))

    sat, ext, csat, dates = (f"lists {e!r} under owner_must_sign" for e in (
        "saturday_close rows", shipped[1], shipped[2], shipped[3]))
    c16, c26, c15, c14, c25, c1511, c97, c99 = (
        f"{c}: kr_sessions.yaml v1.0.0-fixture" for c, *_rest in CLOSE02_NEEDS if c.startswith("KR ") and "regime" not in c)
    assert entries("oms_shipped", *shipped) == [
        f"{c16} {dates}", f"{c26} {dates}", f"{c15} {ext}", f"{c15} {dates}", f"{c14} {ext}", f"{c14} {dates}",
        f"{c25} {dates}", f"{c1511} {csat}", f"{c1511} {dates}", f"{c97} {sat}", f"{c97} {ext}", f"{c99} {ext}",
        f"{c99} {dates}"], entries("oms_shipped", *shipped)
    # one entry at a time: the extensions wait the four clauses that read a pre-2015-06-15 bound (the 1999 session
    # too); the pre-2016 CSAT rows wait the 2015 CSAT clause only (2025-11-13 is after 2016-08-01); an entry dated
    # before 1999 covers only the 1997 Saturday's lunch-break read; an entry naming no row kind covers every one
    assert entries("oms_ext", shipped[1]) == [f"{c} {ext}" for c in (c15, c14, c97, c99)]
    assert entries("oms_csat", shipped[2]) == [f"{c1511} {csat}"]
    lunch = "lunch_break rows before 1999-01-01"
    assert entries("oms_lunch", lunch) == [f"{c97} lists {lunch!r} under owner_must_sign"]
    vague = "the session hours from the KRX notices"
    assert entries("oms_vague", vague) == [f"{c} lists {vague!r} under owner_must_sign"
                                          for c in (c16, c26, c15, c14, c25, c1511, c97, c99)]
    # the waiting list: holidays_KRX cut to 2026-27 (the shipped span), and holidays_KRX / kr_regime_tags unsigned
    gap = "holidays_KRX.yaml v1.0.0-fixture covers 2026-01-01..2027-12-31, needs"
    assert _close02_waiting(krx_short_set()) == [
        f"KR 2016-07-29 / 2016-08-01 close and bound: {gap} 2016-01-01..2016-08-01",
        f"KR 2015-06-12 / 2015-06-15 random-end bound: {gap} 2015-01-01..2015-06-15",
        f"KR 2014-06-02 conditional random-end bound: {gap} 2014-01-01..2014-06-02",
        f"KR CSAT 2025-11-13: {gap} 2025-01-01..2025-11-13",
        f"KR pre-2016 CSAT 2015-11-12: {gap} 2015-01-01..2015-11-12",
        "KR pre-2016 CSAT 2015-11-12: kr_sessions.yaml v1.0.0-fixture has no signed csat_window row effective on 2015-11-12",
        f"KR Saturday 1997-06-07: {gap} 1997-01-01..1997-06-07",
        f"KR 1999-03-02 lunch break and closing call: {gap} 1999-01-01..1999-03-02"], _close02_waiting(krx_short_set())
    # a KR clause reads holidays_KRX from 1 January of its year (the first-session check): a file from 2016-06-01 is a
    # gap for the 2016 clause, and the clauses on it raise CalendarCoverageError
    def from_june_2016(docs):
        krx = docs["holidays_KRX"]
        krx["covers"]["from"] = "2016-06-01"
        krx["rows"] = [r for r in krx["rows"] if r["date"] >= "2016-06-01"]
    june = _close02_docs_set("krx_2016_06", from_june_2016)
    assert ("KR 2016-07-29 / 2016-08-01 close and bound: holidays_KRX.yaml v1.0.0-fixture covers 2016-06-01..2027-12-31, "
            "needs 2016-01-01..2016-08-01") in _close02_waiting(june), _close02_waiting(june)
    _raises(lambda: _check_close02(june), CalendarCoverageError)
    refused = [w for w in _close02_waiting(drafts_set()) if " refused (" in w]
    assert [w.split(": ")[0] for w in refused] == [c for c, files, *_ in CLOSE02_NEEDS
                                                  if {"holidays_KRX", "kr_regime_tags"} & set(files)], refused
    assert all("signed_off_by is empty" in w for w in refused), refused
    live = CalendarSet()
    waiting = _close02_waiting(live)
    if waiting:
        reason = _raises(test_close02_on_the_real_signed_files_is_owner_input, NotRun).reason
        assert reason == "OWNER: T-CLOSE-02 on the signed calendars waits for " + "; ".join(waiting), reason
    # FAIL: one wrong config, file or clock per clause; the message names the clause
    cond, unc = copy.deepcopy(cal.config["KR"]["random_end"])

    def span(entry, lo=None, hi=None, **kw):
        out = {k: v for k, v in entry.items() if k not in ("from", "to")}
        out.update({k: v for k, v in (("from", lo), ("to", hi)) if v}, **kw)
        return out

    def random_end(*entries):
        return _close02_config_set("KR", "random_end", list(entries))

    def drop(file_id, pred):
        def edit(docs):
            docs[file_id]["rows"] = [r for r in docs[file_id]["rows"] if not pred(r)]
        return edit

    def set_close(market, hhmm):
        def edit(docs):
            for r in docs["market_closes"]["rows"]:
                if r.get("market") == market:
                    r["close_local"] = hhmm
        return edit

    def regime_sat(docs):
        for r in docs["kr_regime_tags"]["rows"]:
            if r["tag"] == "saturday_session":
                r.update({"effective_from": "1995-01-01", "effective_to": "1997-06-06"} if r["value"] else
                         {"effective_from": "1997-06-07"})

    def regular_open(docs):
        for r in docs["kr_sessions"]["rows"]:
            if r["kind"] == "regular_open":
                r["open_kst"] = "09:10"

    def open_sunday(docs):
        docs["holidays_KRX"]["rows"].append(_hol(date(2026, 10, 4), "open"))

    def weekday_close_on_saturday(m, d, cal=None):                  # a clock that falls back to the weekday close
        return U(d.year, d.month, d.day, 6, 0) if m == "KR" and d.weekday() == 5 else clocks.decision_time_utc(m, d, cal=cal)

    def no_flags(market):
        def session(m, d, cal=None):
            s = clocks.session(m, d, cal=cal)
            return dataclasses.replace(s, flags=frozenset()) if m == market else s
        return session

    def coverage_as_not_a_session(m, d, cal=None):
        try:
            return clocks.decision_time_utc(m, d, cal=cal)
        except CalendarCoverageError as exc:
            raise NotASession(str(exc)) from None

    def wrong_markets(m, d, cal=None):
        if m in ("CRYPTO", "EU"):
            return U(d.year, d.month, d.day)
        return clocks.decision_time_utc(m, d, cal=cal)

    def two_csat_windows(docs):                                     # two overlapping signed rows on 2015-11-12
        docs["kr_sessions"]["rows"] += [_row(kind="csat_window", window_kst=["10:00", close],
                                             effective_from="2015-11-12", effective_to="2015-11-12")
                                        for close in ("16:10", "16:20")]

    def first_csat_row(fn, s):                                      # a clock that takes the first of them
        return lambda m, d, cal=None: (U(2015, 11, 12, 7, 10, s) if (m, d) == ("KR", date(2015, 11, 12))
                                       else fn(m, d, cal=cal))

    def two_extensions(docs):                                       # a second signed row for the 2014-06-02 session
        docs["kr_sessions"]["rows"].append(_row(kind="random_end_extension", session_date="2014-06-02", extension_s=30))

    def summing(m, d, cal=None):                                    # a clock that adds both rows (45 s + 30 s)
        return U(2014, 6, 2, 6, 1, 45) if (m, d) == ("KR", date(2014, 6, 2)) else clocks.close_print_bound_utc(m, d, cal=cal)

    def extension_not_effective(docs):                              # the 45 s row, effective only from 2015-01-01
        for r in docs["kr_sessions"]["rows"]:
            if r["kind"] == "random_end_extension":
                r["effective_from"] = "2015-01-01"

    hol = lambda d: lambda r: r["date"] == d                        # noqa: E731
    cases = (
        (_close02_config_set("KR", "close_kst", [{"to": "2016-07-28", "time": "15:00"}, {"from": "2016-07-29", "time": "15:30"}]),
         clocks, "decision_time_utc('KR', 2016-07-29) (spec L2096) is 2016-07-29 06:30:00+00:00"),
        (_close02_config_set("KR", "close_kst", [{"to": "2016-08-01", "time": "15:00"}, {"from": "2016-08-02", "time": "15:30"}]),
         clocks, "decision_time_utc('KR', 2016-08-01) (spec L2096) is 2016-08-01 06:00:00+00:00"),
        (random_end(cond, span(unc, "2015-06-15", max_s=45)), clocks, "close_print_bound_utc('KR', 2016-07-29) (spec L2096)"),
        (random_end(cond, span(unc, "2015-06-15", "2016-07-31"), span(unc, "2016-08-01", max_s=45)), clocks,
         "close_print_bound_utc('KR', 2016-08-01) (spec L5618)"),
        (random_end(cond, span(unc, "2015-06-15", "2026-09-30"), span(unc, "2026-10-01", max_s=45)), clocks,
         "close_print_bound_utc('KR', 2026-10-02) (spec L2096)"),
        (random_end(span(cond, None, "2015-06-15", print_tolerance_s=20), span(unc, "2015-06-16")), clocks,
         "close_print_bound_utc('KR', 2015-06-15), the first unconditional"),
        (random_end(span(cond, None, "2015-06-14", print_tolerance_s=20), unc), clocks,
         "close_print_bound_utc('KR', 2015-06-12), conditional random end with 0 s signed"),
        (random_end(span(cond, None, "2013-12-31"), span(unc, "2014-01-01")), clocks,
         "close_print_bound_utc('KR', 2014-06-02), conditional random end with 45 s signed (spec L5618) is "
         "2014-06-02 06:00:30+00:00, not 2014-06-02 06:01:15+00:00"),
        (_close02_docs_set("ext_two", two_extensions), _clocks_with(close_print_bound_utc=summing),
         "close_print_bound_utc('KR', 2014-06-02), conditional random end with one signed random_end_extension row (2) "
         "(spec L5618) is 2014-06-02 06:01:45+00:00, not one signed random_end_extension row (2)"),
        (_close02_docs_set("ext_not_effective", extension_not_effective), clocks,
         "close_print_bound_utc('KR', 2014-06-02), conditional random end with 0 s signed (spec L5618) is "
         "2014-06-02 06:01:15+00:00, not 2014-06-02 06:00:30+00:00"),
        (_close02_docs_set("csat2025", drop("kr_sessions", lambda r: r.get("date") == "2025-11-13")), clocks,
         "decision_time_utc('KR', 2025-11-13), a CSAT day"),
        (random_end(cond, span(unc, "2015-06-15", "2025-11-12"), span(unc, "2025-11-13", "2025-11-13", max_s=45),
                    span(unc, "2025-11-14")), clocks, "close_print_bound_utc('KR', 2025-11-13), a CSAT day"),
        (_close02_docs_set("csat2015", drop("kr_sessions", lambda r: r.get("date") == "2015-11-12")), clocks,
         "decision_time_utc('KR', 2015-11-12), a pre-2016 CSAT date"),
        (_close02_docs_set("csat2015_two", two_csat_windows),
         _clocks_with(decision_time_utc=first_csat_row(clocks.decision_time_utc, 0),
                      close_print_bound_utc=first_csat_row(clocks.close_print_bound_utc, 30)),
         "decision_time_utc('KR', 2015-11-12), a pre-2016 CSAT date (spec L2096) is 2015-11-12 07:10:00+00:00, not one "
         "signed csat_window row (2)"),
        (random_end(cond, span(unc, "2015-06-15", "2015-11-11"), span(unc, "2015-11-12", "2015-11-12", max_s=45),
                    span(unc, "2015-11-13")), clocks, "close_print_bound_utc('KR', 2015-11-12), a pre-2016 CSAT date"),
        (_close02_config_set("KR", "saturday_sessions_before", "1995-01-01"), clocks,
         "the Saturday 1997-06-07 is not a KR session"),
        (cal, _clocks_with(decision_time_utc=weekday_close_on_saturday),
         "decision_time_utc('KR', 1997-06-07), the signed Saturday close (spec L2015) is 1997-06-07 06:00:00+00:00"),
        (random_end(span(cond, None, "1997-06-06"), span(cond, "1997-06-07", "1997-06-07", print_tolerance_s=20),
                    span(cond, "1997-06-08", "2015-06-14"), unc), clocks, "close_print_bound_utc('KR', 1997-06-07)"),
        (cal, _clocks_with(session=no_flags("KR")), "session('KR', 1997-06-07) flag 'saturday' is False"),
        (_close02_docs_set("regime_sat", regime_sat), clocks, "regime_tags('KR', 1997-06-07)['saturday_session']"),
        (_close02_docs_set("hol1005", drop("holidays_KRX", hol("2026-10-05"))), clocks,
         "decision_time_utc('KR', 2026-10-05) (spec L2096) did not raise NotASession"),
        (_close02_docs_set("sun1004", open_sunday), clocks, "decision_time_utc('KR', 2026-10-04), a Sunday (spec L2087) did not"),
        (_close02_docs_set("nyse1127", drop("holidays_NYSE", hol("2026-11-27"))), clocks,
         "decision_time_utc('US', 2026-11-27) (spec L2096) is 2026-11-27 21:00:00+00:00"),
        (_close02_docs_set("nyse0703", drop("holidays_NYSE", hol("2025-07-03"))), clocks,
         "decision_time_utc('US', 2025-07-03) (spec L2096) is 2025-07-03 20:00:00+00:00"),
        (_close02_config_set("US", "close_print_bound_s", 45), clocks, "close_print_bound_utc('US', 2026-10-01)"),
        (_close02_docs_set("nyse1126", drop("holidays_NYSE", hol("2026-11-26"))), clocks,
         "decision_time_utc('US', 2026-11-26), Thanksgiving (spec L1340, L2087) did not raise NotASession"),
        (_close02_docs_set("open0910", regular_open), clocks, "session('KR', 2026-10-02) (open, close"),
        (_close02_config_set("KR", "first_trading_day_open_kst", "10:30"), clocks, "session('KR', 2026-01-02)"),
        (_close02_docs_set("nolunch", drop("kr_sessions", lambda r: r["kind"] == "lunch_break")), clocks,
         "session('KR', 1999-03-02) (lunch break, closing call; spec L2016, L2011) is (None,"),
        (_close02_config_set("KR", "closing_call_kst", [{"to": "2016-07-31", "window": ["14:40", "15:00"]},
                                                         {"from": "2016-08-01", "window": ["15:20", "15:30"]}]), clocks,
         "session('KR', 1999-03-02) (lunch break, closing call"),
        (_close02_config_set("KR", "csat_closing_call_kst", [{"to": "2016-07-31", "window": "from_krx_notice"},
                                                             {"from": "2016-08-01", "window": ["16:10", "16:30"]}]), clocks,
         "session('KR', 2025-11-13), a CSAT day"),
        (cal, _clocks_with(session=no_flags("US")), "session('US', 2026-11-27) flags (spec L2021) is frozenset()"),
        (_close02_config_set("JP", "close_jst", [{"to": "2024-11-03", "time": "15:00"}, {"from": "2024-11-04", "time": "15:30"}]),
         clocks, "decision_time_utc('JP', 2024-11-04), the last TSE session through 2024-11-04 (spec L2022)"),
        (_close02_config_set("JP", "close_jst", [{"to": "2024-11-05", "time": "15:00"}, {"from": "2024-11-06", "time": "15:30"}]),
         clocks, "decision_time_utc('JP', 2024-11-05) (spec L2022)"),
        (_close02_config_set("JP", "close_print_bound_s", 30), clocks, "close_print_bound_utc('JP', 2026-10-08)"),
        (_close02_docs_set("cn1530", set_close("CN", "15:30")), clocks, "decision_time_utc('CN', 2026-10-08) (spec L2023)"),
        (_close02_docs_set("tw1345", set_close("TW", "13:45")), clocks, "decision_time_utc('TW', 2026-10-08) (spec L2023)"),
        (_close02_docs_set("hk1550", set_close("HK", "15:50")), clocks,
         "decision_time_utc('HK', 2026-10-08) is 2026-10-08 07:50:00+00:00, before 16:00 HKT"),
        (cal, _clocks_with(decision_time_utc=coverage_as_not_a_session),
         "decision_time_utc('KR', 1994-12-31), before the signed coverage (spec L2090) raised NotASession"),
        (cal, _clocks_with(decision_time_utc=wrong_markets), "decision_time_utc('CRYPTO', 2026-10-02) (spec L5505)"),
    )
    for wrong, clk, needle in cases:
        e = _raises(lambda: _check_close02(wrong, clk), AssertionError)
        assert f"T-CLOSE-02: {needle}" in str(e), (needle, str(e))
    eu = _clocks_with(decision_time_utc=lambda m, d, cal=None: U(d.year, d.month, d.day) if m == "EU"
                      else clocks.decision_time_utc(m, d, cal=cal))
    e = _raises(lambda: _check_close02(cal, eu), AssertionError)
    assert "T-CLOSE-02: decision_time_utc('EU', 2026-10-02) did not raise KeyError" in str(e), str(e)


def test_print01_intraday_print_is_never_a_close():
    """2026-03-09: a 10:31 KST print (01:31Z) precedes the scheduled close and is refused as a close; the official close
    is stamped obs_utc 06:30Z with available_at <= 06:30:30Z."""
    cal = fixture_set()
    d = date(2026, 3, 9)
    _raises(lambda: clocks.close_stamp("KR", d, U(2026, 3, 9, 1, 31), cal=cal), clocks.IntradayPrint)
    stamp = clocks.close_stamp("KR", d, U(2026, 3, 9, 6, 30, 12), cal=cal)
    assert stamp.obs_utc == U(2026, 3, 9, 6, 30) and stamp.available_at_utc <= U(2026, 3, 9, 6, 30, 30)
    _raises(lambda: clocks.close_stamp("KR", d, datetime(2026, 3, 9, 6, 30), cal=cal), ValueError)   # naive instant


test_print01_intraday_print_is_never_a_close.test_ids = ["T-PRINT-01"]


def test_print01_real_kospi_close_2026_03_09():
    """T-PRINT-01 on the KRX official closes (F01): NOT_RUN (REFDATA) until F01 is listed with its md5, NOT_RUN (OWNER)
    while the signed KRX clock files do not cover the week of 2026-03-09; then PASS or FAIL on `_check_print01`."""
    text = require_fixture(F01).read_text(encoding="utf-8")
    rows = _kospi_closes(text)
    _check_print01(rows, _official_calendar(PRINT01_DATE - timedelta(days=14), PRINT01_DATE))


test_print01_real_kospi_close_2026_03_09.test_ids = ["T-PRINT-01"]


def test_print01_body_passes_and_fails_on_invented_closes():
    """LA-02 part 1: the T-PRINT-01 body can PASS and can FAIL. Invented closes in the F01 layout on the synthetic
    calendars (no KRX data): the close 5,251.87 after 5,584.71 passes. It fails when the 10:31 KST print (5,131.12,
    -8.11%) is stored as the 2026-03-09 close or beside it; when the close is 5,251.88 with correct stamps; when the
    previous close is 5,560 (-5.54%); and when the previous session's row is missing. The owner-calendar gate returns a
    covering set and refuses a set whose KRX holiday file is unsigned."""
    cal = fixture_set()
    lo = date(2026, 2, 23)
    good = _invented_closes(cal, lo, PRINT01_DATE, last=(5584.71, PRINT01_CLOSE))
    assert abs(_check_print01(_kospi_closes(_f01_text(good)), cal) - PRINT01_RETURN_PCT) <= PRINTED_PCT
    cb_print = (PRINT01_DATE, 5131.12, U(2026, 3, 9, 1, 31), U(2026, 3, 9, 1, 31))
    as_close = _raises(lambda: _check_print01(_kospi_closes(_f01_text(good[:-1] + [cb_print])), cal), AssertionError)
    assert "not an official close" in str(as_close)
    beside = _raises(lambda: _check_print01(_kospi_closes(_f01_text(good + [cb_print])), cal), AssertionError)
    assert "2 rows on 2026-03-09" in str(beside)
    for last, needle in (((5584.71, 5251.88), "close 5251.88 != 5251.87 (spec L5631)"),
                         ((5560.0, PRINT01_CLOSE), "return -5.5419% != -5.96%")):
        rows = _invented_closes(cal, lo, PRINT01_DATE, last=last)
        e = _raises(lambda: _check_print01(_kospi_closes(_f01_text(rows)), cal), AssertionError)
        assert needle in str(e), e
    assert good[-2][0] == date(2026, 3, 6)
    gap = _raises(lambda: _check_print01(_kospi_closes(_f01_text(good[:-2] + good[-1:])), cal), AssertionError)
    assert "no row for the previous session 2026-03-06" in str(gap), gap
    hi = PRINT01_DATE
    assert _official_calendar_on(hi - timedelta(days=14), hi, cal) is cal
    owner = _raises(lambda: _official_calendar(hi - timedelta(days=14), hi, live=drafts_set()), NotRun)
    assert owner.reason.startswith("OWNER: the signed KRX clock files must cover 2026-02-23..2026-03-09: "
                                   "holidays_KRX.yaml refused (holidays_KRX.yaml: signed_off_by is empty"), owner.reason


# --------------------------------------------------------------------------- #
# T-TZ-01 / T-TZ-02
# --------------------------------------------------------------------------- #
def test_tz01_cross_time_zone():
    cal = fixture_set()
    assert clocks.latest_usable_close("US", "KR", date(2026, 10, 1), cal=cal) == date(2026, 9, 30)
    assert clocks.latest_usable_close("US", "KR", date(2026, 9, 30), cal=cal) == date(2026, 9, 29)
    kst = ZoneInfo(KST)
    assert clocks.decision_time_utc("US", date(2026, 1, 15), cal=cal).astimezone(kst) == datetime(2026, 1, 16, 6, 0, tzinfo=kst)
    assert clocks.decision_time_utc("US", date(2026, 7, 15), cal=cal).astimezone(kst) == datetime(2026, 7, 16, 5, 0, tzinfo=kst)
    assert clocks.decision_time_utc("US", date(2006, 3, 20), cal=cal) == U(2006, 3, 20, 21, 0)
    assert clocks.decision_time_utc("US", date(2006, 4, 3), cal=cal) == U(2006, 4, 3, 20, 0)
    bound = clocks.close_print_bound_utc("KR", date(2026, 10, 8), cal=cal)
    assert not clocks.cross_market_usable("CN", date(2026, 10, 8), bound, cal=cal)
    assert not clocks.cross_market_usable("HK", date(2026, 10, 8), bound, cal=cal)
    assert not clocks.cross_market_usable("JP", date(2026, 10, 8), bound, cal=cal)
    assert clocks.cross_market_usable("TW", date(2026, 10, 8), bound, cal=cal)
    assert clocks.cross_market_usable("JP", date(2020, 6, 1), clocks.close_print_bound_utc("KR", date(2020, 6, 1), cal=cal), cal=cal)
    # the US session dated K never enters the KRX decision of K (usable_at of a US close at a KR decision)
    us_close = {"schedule_id": "MARKET_CLOSE_US"}
    assert publication.usable_at(us_close, date(2026, 10, 1), "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2026, 10, 2), cal=cal)
    assert publication.usable_at(us_close, date(2026, 10, 2), "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2026, 10, 6), cal=cal)
    assert publication.usable_at(us_close, date(2026, 10, 2), "US", cal=cal) == U(2026, 10, 2, 20, 0, 30)


test_tz01_cross_time_zone.test_ids = ["T-TZ-01"]


def test_tz02_event_to_kr_open_gap_session():
    cal = fixture_set()
    fomc = datetime(2026, 9, 16, 14, 0, tzinfo=ZoneInfo(NY))
    assert fomc.astimezone(UTC) == U(2026, 9, 16, 18, 0)
    assert fomc.astimezone(ZoneInfo(KST)) == datetime(2026, 9, 17, 3, 0, tzinfo=ZoneInfo(KST))
    assert clocks.kr_open_gap_session(fomc, cal=cal) == date(2026, 9, 17)
    nfp = datetime(2026, 10, 2, 8, 30, tzinfo=ZoneInfo(NY))
    assert nfp.astimezone(UTC) == U(2026, 10, 2, 12, 30)
    assert clocks.kr_open_gap_session(nfp, cal=cal) == date(2026, 10, 6)
    assert clocks.kr_open_gap_session(datetime(2026, 10, 28, 14, 0, tzinfo=ZoneInfo(NY)), cal=cal) == date(2026, 10, 29)
    # effective_session (t+1) and the next/prev helpers
    assert clocks.next_session("KR", date(2026, 10, 2), cal=cal) == date(2026, 10, 6)
    assert clocks.prev_session("KR", date(2026, 10, 12), cal=cal) == date(2026, 10, 8)


test_tz02_event_to_kr_open_gap_session.test_ids = ["T-TZ-02"]


def test_gap_sessions_values():
    cal = fixture_set()
    assert clocks.gap_sessions("KR", date(2026, 10, 6), cal=cal) == 2
    assert clocks.gap_sessions("KR", date(2026, 10, 12), cal=cal) == 2
    assert clocks.gap_sessions("KR", date(2026, 11, 27), cal=cal) == 0
    assert clocks.gap_sessions("KR", date(2026, 10, 8), cal=cal) == 1


test_gap_sessions_values.test_ids = ["I-06b"]


# --------------------------------------------------------------------------- #
# T-CAL-01 / T-CAL-02
# --------------------------------------------------------------------------- #
def test_cal01_unsigned_refused_signed_accepted():
    cal = fixture_set()
    assert cal.file("kr_sessions").signed_off_by == SIGNER and cal.version == "1.0.0-fixture"
    base = fixture_docs()

    def variant(key, mutate, unsigned_manifest=False):
        docs = {k: v for k, v in fixture_docs().items() if k in ("kr_sessions", "holidays_KRX")}
        mutate(docs)
        return fixture_set(key, docs) if not unsigned_manifest else _unsigned_manifest_set(key, docs)

    def set_unsigned(docs):
        docs["kr_sessions"]["signed_off_by"] = None

    def set_empty(docs):
        docs["holidays_KRX"]["signed_off_by"] = "   "

    def row_unsigned(docs):
        docs["kr_sessions"]["rows"][0]["signed_off_by"] = ""

    def no_signed_utc(docs):
        docs["kr_sessions"]["signed_utc"] = None

    for key, mut in (("u1", set_unsigned), ("u2", set_empty), ("u3", row_unsigned), ("u4", no_signed_utc)):
        bad = variant(key, mut)
        exc = _raises(lambda: clocks.decision_time_utc("KR", date(2026, 10, 2), cal=bad), CalendarUnsigned)
        assert "sign" in str(exc).lower(), exc
    # an unquoted date scalar (PyYAML 1.1 reads it as a date object) is refused before any signature check
    unq = variant("u5", lambda d: None)
    path = unq.data_dir / "holidays_KRX.yaml"
    text = path.read_text(encoding="utf-8")
    assert "date: '1995-01-01'" in text
    path.write_text(text.replace("date: '1995-01-01'", "date: 1995-01-01", 1), encoding="utf-8")
    assert "quote" in str(_raises(lambda: CalendarSet(unq.data_dir).file("holidays_KRX"), CalendarUnsigned))
    # an edit under an old signature (md5 mismatch) and a manifest that names no test are unsigned changes
    tampered = variant("u6", lambda d: None)
    path = tampered.data_dir / "kr_sessions.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["rows"].append(_row(kind="csat_day", date="2026-11-19", effective_from="2026-11-19", effective_to="2026-11-19"))
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    fresh = CalendarSet(tampered.data_dir)
    assert "md5" in str(_raises(lambda: fresh.file("kr_sessions"), CalendarUnsigned))
    assert fresh.file("holidays_KRX").version == "1.0.0-fixture"            # the other file still loads
    m = tampered.data_dir / "MANIFEST.yaml"
    mdoc = yaml.safe_load(m.read_text(encoding="utf-8"))
    for r in mdoc["rows"]:
        r["test_ids"] = []
    m.write_text(yaml.safe_dump(mdoc, sort_keys=False), encoding="utf-8")
    assert "test id" in str(_raises(lambda: CalendarSet(tampered.data_dir).file("holidays_KRX"), CalendarUnsigned))
    m.unlink()
    assert "MANIFEST" in str(_raises(lambda: CalendarSet(tampered.data_dir).file("holidays_KRX"), CalendarUnsigned))
    unsigned_m = variant("u7", lambda d: None, unsigned_manifest=True)
    assert "signer" in str(_raises(lambda: unsigned_m.file("holidays_KRX"), CalendarUnsigned))
    # the fail-closed consequence: status and the ARM precondition say so; the regime file is independent
    bad = variant("u8", set_unsigned)
    st = store.status("KR", date(2026, 10, 2), cal=bad)
    assert st["signed"] is False and "kr_sessions" in st["refused"]
    assert store.arm_precondition(date(2026, 10, 2), "KR", cal=bad) is False
    assert store.arm_precondition(date(2026, 10, 2), "KR", cal=cal) is True
    assert base["kr_sessions"]["md5"] is None            # the fixture builder, not the library, signs


test_cal01_unsigned_refused_signed_accepted.test_ids = ["T-CAL-01"]


def _unsigned_manifest_set(key, docs):
    tmp = tempfile.TemporaryDirectory(prefix="quantgen_cal_")
    _write_set(Path(tmp.name), docs, unsigned_manifest=True)
    _CACHE[key] = (tmp, CalendarSet(Path(tmp.name)))
    return _CACHE[key][1]


def test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed():
    """Every shipped file is either a draft (signed_off_by, signed_utc and md5 null on the file and its MANIFEST row ->
    refused) or a complete owner sign-off (loads); a half-signed file fails here. A market whose clock files are not
    all signed raises CalendarUnsigned, which the data layer maps to MissingInput('missing') with fail_closed (brief
    F-5), and no book of it can ARM. No shipped signer is a test or simulation placeholder (the build never signs)."""
    live = store.default()
    assert live.data_dir == store.DATA_DIR
    manifest = store.read_yaml(store.DATA_DIR / "MANIFEST.yaml")
    rows = {r["file"]: r for r in manifest["rows"]}
    assert set(rows) == {f"{f}.yaml" for f in live.file_ids()}
    signed = set()
    for fid in live.file_ids():
        raw, row, reason = store.read_yaml(live.data_dir / f"{fid}.yaml"), rows[f"{fid}.yaml"], live.refusal(fid)
        if reason is None:
            f = live.file(fid)
            assert row["signed_off_by"] == f.signed_off_by and row["md5"] == f.md5, fid
            assert not any(tag in f.signed_off_by for tag in ("TEST-FIXTURE", "SIMULATION")), (fid, f.signed_off_by)
            signed.add(fid)
            continue
        assert "signed_off_by is empty" in reason, (fid, reason)
        assert raw.get("signed_off_by") is None and raw.get("signed_utc") is None and raw.get("md5") is None, fid
        assert row["md5"] is None and row["signed_off_by"] is None, fid
        assert raw.get("unverified") and raw.get("owner_must_sign"), fid
    for market in ("KR", "US", "JP", "CN", "HK", "TW"):
        if set(store.MARKET_FILES[market]) <= signed:
            continue
        _raises(lambda: clocks.decision_time_utc(market, date(2026, 10, 2), cal=live), CalendarUnsigned)
        _raises(lambda: clocks.is_session(market, date(2026, 10, 2), cal=live), CalendarUnsigned)
        assert store.arm_precondition(date(2026, 10, 2), market, cal=live) is False
    if "kr_regime_tags" not in signed:
        _raises(lambda: regime.regime_tags("KR", date(2026, 10, 2), cal=live), CalendarUnsigned)
    if not {"publication_schedules", "holidays_FED"} <= signed:
        _raises(lambda: publication.publication_instant({"schedule_id": "H15"}, date(2026, 10, 2), cal=live), CalendarUnsigned)
    if not set(store.COVERAGE_FILES["KR"]) <= signed:
        assert store.status("KR", date(2026, 10, 2), cal=live)["signed"] is False
    if manifest.get("signed_off_by") is None:
        assert live.version == "unsigned"
    else:       # a signed set: every file in it is signed, and the set version is what event_calendar stamps
        assert signed == set(live.file_ids()), sorted(set(live.file_ids()) - signed)
        assert manifest.get("signed_utc") and live.version == str(manifest["version"]) != "unsigned"
        assert not any(tag in manifest["signed_off_by"] for tag in ("TEST-FIXTURE", "SIMULATION"))
    # the rules-store paths of section 7 resolve to these files
    from core.rules.macro_rules import load_store
    s = load_store()
    assert s.get("calendars.regime_tags_file") == "core/calendars/data/kr_regime_tags.yaml"
    assert s.get("data_contracts.source_exceptions") == "core/calendars/data/source_skipped.yaml"
    assert (store.DATA_DIR.parents[2] / s.get("calendars.regime_tags_file")).is_file()


test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed.test_ids = ["T-CAL-01"]


def test_cal01_owner_sign_tool_on_a_copy():
    """tools/sign_calendars on a signature-stripped copy of the shipped files: the signed files load with the signer
    on every row, md5 and MANIFEST row in step; a placeholder signer, a re-sign and a wrong fingerprint are refused
    and leave the files untouched."""
    import shutil
    from tools import sign_calendars as T
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        for path in data_dir.glob("*.yaml"):
            doc = store.read_yaml(path)
            if path.name == store.MANIFEST:
                for row in doc["rows"]:
                    row["md5"] = row["signed_off_by"] = None
            else:
                doc["signed_off_by"] = doc["signed_utc"] = doc["md5"] = None
            path.write_text(T._dump(doc), encoding="utf-8")
        before = {p.name: p.read_bytes() for p in data_dir.glob("*.yaml")}
        _raises(lambda: T.sign(T.CAL02_FILES, "SIMULATION - not a signature", data_dir=data_dir), T.SignRefused)
        _raises(lambda: T.sign(["holidays_KRX"], "owner:test", data_dir=data_dir, expect={"holidays_KRX": "0" * 32}),
                T.SignRefused)
        assert {p.name: p.read_bytes() for p in data_dir.glob("*.yaml")} == before
        done = T.sign(T.CAL02_FILES, "owner:test", data_dir=data_dir, now=lambda: U(2026, 10, 29, 3))
        assert [r["signed_utc"] for r in done] == ["2026-10-29T03:00:00Z"] * 4
        cal, manifest = CalendarSet(data_dir), store.read_yaml(data_dir / store.MANIFEST)
        rows = {r["file"]: r for r in manifest["rows"]}
        for fid in T.CAL02_FILES:
            f = cal.file(fid)
            assert f.signed_off_by == "owner:test" and all(r["signed_off_by"] == "owner:test" for r in f.rows)
            assert rows[f"{fid}.yaml"]["md5"] == f.md5 and rows[f"{fid}.yaml"]["version"] == f.version
        assert cal.refusal("kr_sessions") is not None                               # unnamed files stay unsigned
        _raises(lambda: T.sign(["holidays_KRX"], "owner:test", data_dir=data_dir), T.SignRefused)


test_cal01_owner_sign_tool_on_a_copy.test_ids = ["T-CAL-01", "T-CAL-02"]


def test_cal01_calendar_change_governance_event():
    from core.rules.governance import read_events, verify_chain
    cal = fixture_set()
    clock = lambda: U(2026, 10, 6, 7, 0)
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "governance_events.jsonl"
        first = store.record_calendar_changes(log, ("kr_sessions", "holidays_KRX"), clock, cal=cal)
        assert len(first) == 2 and verify_chain(log).ok
        assert store.record_calendar_changes(log, ("kr_sessions", "holidays_KRX"), clock, cal=cal) == []
        docs = fixture_docs()
        docs["kr_sessions"]["version"] = "1.0.1-fixture"
        docs["kr_sessions"]["rows"].append(_row(kind="csat_day", date="2026-11-19", effective_from="2026-11-19", effective_to="2026-11-19"))
        revised = fixture_set("revised", docs)
        again = store.record_calendar_changes(log, ("kr_sessions", "holidays_KRX"), clock, cal=revised)
        assert len(again) == 1
        ev = read_events(log)[-1]
        assert ev["kind"] == "calendar_change" and ev["key"] == "kr_sessions" and ev["rule_id"] == "R-20"
        assert ev["old"]["version"] == "1.0.0-fixture" and ev["new"]["version"] == "1.0.1-fixture" and ev["actor"] == "owner"
        unsigned = {k: v for k, v in fixture_docs().items() if k in ("kr_sessions", "holidays_KRX")}
        unsigned["kr_sessions"]["signed_off_by"] = None
        assert store.record_calendar_changes(log, ("kr_sessions",), clock, cal=fixture_set("gov_unsigned", unsigned)) == []


test_cal01_calendar_change_governance_event.test_ids = ["T-CAL-01"]


def test_cal02_coverage_warn_page_halt():
    """A file ending N sessions after the decision date: N=61 no alert, 60 warn, 20 page, 0 page; outside -> OPS HALT
    calendar_coverage through the injected runtime hook, never a NotASession."""
    base = fixture_set()
    decision = date(2026, 10, 6)
    sessions = clocks.sessions_between("KR", decision + timedelta(days=1), date(2027, 6, 30), cal=base)
    halts: list[tuple] = []

    def halt(book_id, cls, reason):
        halts.append((book_id, cls, reason))

    for n, severity in ((61, None), (60, "warn"), (20, "page"), (0, "page")):
        hi = sessions[n - 1] if n else decision
        docs = fixture_docs()
        docs["holidays_KRX"]["covers"]["to"] = hi.isoformat()
        cal = fixture_set(f"cov{n}", docs)
        assert store.sessions_left(cal, cal.file("holidays_KRX"), decision) == n
        alerts = store.check_coverage(decision, ("holidays_KRX",), cal=cal, now_utc=U(2026, 10, 6, 6, 41))
        if severity is None:
            assert alerts == []
        else:
            assert len(alerts) == 1 and alerts[0]["severity"] == severity and alerts[0]["code"] == "calendar_coverage"
            assert alerts[0]["component"] == "core/calendars" and alerts[0]["count"] == 1 and alerts[0]["first_seen_utc"] == "2026-10-06T06:41:00Z"
        st = store.status("KR", decision, cal=cal)
        assert st["sessions_left"] == n and st["signed"] is True
        assert store.arm_precondition(decision, "KR", cal=cal) is (n >= 60)
    cal = fixture_set("cov0")
    beyond = decision + timedelta(days=1)
    exc = _raises(lambda: store.check_coverage(beyond, ("holidays_KRX",), cal=cal, now_utc=U(2026, 10, 7),
                                               book_ids=("recommended:KR", "specification:KR"), halt=halt), CalendarCoverageError)
    assert "calendar_coverage" in str(exc) or "outside" in str(exc)
    assert halts == [("recommended:KR", "OPS", "calendar_coverage"), ("specification:KR", "OPS", "calendar_coverage")]
    _raises(lambda: clocks.decision_time_utc("KR", beyond, cal=cal), CalendarCoverageError)      # never NotASession
    assert store.status("KR", beyond, cal=cal)["alerts"][0]["severity"] == "page"
    # the shipped config values drive the thresholds
    cov = base.config["coverage"]
    assert (cov["min_sessions_ahead"], cov["warn_at_sessions_left"], cov["page_at_sessions_left"], cov["outside_coverage"]) == (60, 60, 20, "OPS_HALT")


test_cal02_coverage_warn_page_halt.test_ids = ["T-CAL-02"]


CAL02_FILES = ("holidays_KRX", "holidays_NYSE", "holidays_FED", "holidays_SIFMA")


def test_cal02_2027_files_signed_before_2026_11_01():
    """Deadline clause (spec L2101): the shipped 2027 KRX, NYSE, Fed and SIFMA files are signed before 2026-11-01 UTC
    and cover 2027 to its last day. Not run while any of the four is still an unsigned draft (owner input)."""
    live = CalendarSet()
    unsigned = [f"{fid}.yaml" for fid in CAL02_FILES if live.refusal(fid) is not None]
    if unsigned:
        raise NotRun("OWNER: the 2027 KRX, NYSE, Fed and SIFMA files must be signed before 2026-11-01 (spec L2101); "
                     f"unsigned: core/calendars/data/{', '.join(unsigned)}")
    for fid in CAL02_FILES:
        f = live.file(fid)
        assert f.covers_to >= date(2027, 12, 31), (fid, f.covers_to)
        signed_at = datetime.fromisoformat(f.signed_utc.replace("Z", "+00:00"))
        assert signed_at.tzinfo is not None and signed_at < U(2026, 11, 1), (fid, f.signed_utc)


test_cal02_2027_files_signed_before_2026_11_01.test_ids = ["T-CAL-02"]


# --------------------------------------------------------------------------- #
# T-REGIME-01
# --------------------------------------------------------------------------- #
def test_regime01_point_clauses_and_fail_closed():
    cal = fixture_set()
    R = lambda d: regime.regime_tags("KR", d, cal=cal)
    assert R(date(1997, 6, 2))["price_limit"] == 0.08 and R(date(1998, 6, 1))["price_limit"] == 0.12
    assert R(date(1999, 6, 1))["price_limit"] == 0.15 and R(date(2015, 6, 15))["price_limit"] == 0.30
    assert R(date(2015, 6, 14))["price_limit"] == 0.15
    assert R(date(1997, 10, 1))["fx_regime"] == "peg_1997" and R(date(1997, 9, 21))["fx_regime"] != "peg_1997"
    assert R(date(2002, 1, 2))["etf_available"] is False and R(date(2003, 1, 2))["etf_available"] is True
    assert R(date(2024, 6, 3))["short_sale_ban"] is True and R(date(2022, 6, 3))["short_sale_ban"] is False
    assert R(date(2022, 6, 3))["short_sale_regime"] == "partial_ban_non_index"
    assert R(date(2026, 10, 2))["sell_tax_pct"] == 0.20 and R(date(2025, 6, 2))["sell_tax_pct"] == 0.15
    assert R(date(2024, 2, 26))["value_up"] == "post_2024_02_26" and R(date(2024, 2, 25))["value_up"] == "pre"
    assert R(date(1997, 6, 7))["saturday_session"] is True and R(date(1998, 12, 12))["saturday_session"] is False
    tags = R(date(2026, 10, 2))
    assert tuple(tags) == regime.TAGS and all(v is not None for v in tags.values())
    assert tags["close_time_kst"] == "15:30" and tags["random_end"] == "unconditional_le_30s" and tags["usdkrw_onshore_hours"] == "24h"
    # every date of the fixture span returns a full tag set (the committed expected-values comparison is OWNER)
    d = date(1995, 1, 1)
    while d <= date(2026, 12, 31):
        assert tuple(R(d)) == regime.TAGS
        d += timedelta(days=37)
    _raises(lambda: R(date(1994, 12, 31)), CalendarCoverageError)
    _raises(lambda: R(date(2028, 1, 1)), CalendarCoverageError)
    _raises(lambda: regime.regime_tags("US", date(2026, 10, 2), cal=cal), KeyError)
    assert regime.regime_span_covered(date(1997, 1, 3), date(2026, 10, 2), cal=cal)
    _raises(lambda: regime.require_regime_span(date(1997, 1, 3), date(2028, 3, 1), cal=cal), CalendarCoverageError)
    # a gap or an overlap in one tag is a load-time error
    docs = {k: v for k, v in fixture_docs().items() if k == "kr_regime_tags"}
    docs["kr_regime_tags"]["rows"] = [r for r in docs["kr_regime_tags"]["rows"] if not (r["tag"] == "etf_available" and r["value"] is True)]
    _raises(lambda: regime.regime_tags("KR", date(2026, 10, 2), cal=fixture_set("regime_gap", docs)), CalendarUnsigned)
    docs = {k: v for k, v in fixture_docs().items() if k == "kr_regime_tags"}
    docs["kr_regime_tags"]["rows"].append(_row(tag="etf_available", value=True, effective_from="2010-01-01", effective_to=None))
    _raises(lambda: regime.regime_tags("KR", date(2026, 10, 2), cal=fixture_set("regime_overlap", docs)), CalendarUnsigned)


test_regime01_point_clauses_and_fail_closed.test_ids = ["T-REGIME-01"]


def test_regime01_full_range_expected_values_file():
    """The full-range clause needs the committed expected-values file, an owner deliverable that no ACQUISITION.csv or
    MANIFEST.csv row lists yet (a `require_fixture` on it would fail T-HERM-01). The reason states the shipped tag
    file's signing state as read now (look-ahead audit LA-02: the old text still called the signed file a draft)."""
    raise NotRun("OWNER: tests/fixtures/macro/kr_regime_tags_expected.csv (1995-01-01..2026-12-31, built from the official "
                 "notices incl. the pre-Apr-1995 price limit, sell-tax steps, BoK fx regimes) is an owner deliverable with "
                 f"no ACQUISITION.csv or MANIFEST.csv row yet; {_regime01_tag_state(CalendarSet())}")


test_regime01_full_range_expected_values_file.test_ids = ["T-REGIME-01"]


def _regime01_tag_state(live: CalendarSet) -> str:
    """The signing state of `live`'s kr_regime_tags.yaml, as the T-REGIME-01 full-range reason states it."""
    why = live.refusal("kr_regime_tags")
    if why is None:
        f = live.file("kr_regime_tags")
        return (f"kr_regime_tags.yaml v{f.version} is signed ({f.signed_utc}, covers {f.covers_from}..{f.covers_to}); "
                "only the expected-values file is missing")
    return f"kr_regime_tags.yaml is refused at load ({why})"


def test_regime01_full_range_reason_reads_the_signing_state():
    """LA-02 part 1: the T-REGIME-01 full-range NotRun reason ends with the tag file's signing state as read now and,
    while the shipped file loads, never carries the stale "unsigned draft" clause. The state text is shown on a signed
    and on a refused synthetic set."""
    live = CalendarSet()
    reason = _raises(test_regime01_full_range_expected_values_file, NotRun).reason
    assert reason.startswith("OWNER: ") and reason.endswith(_regime01_tag_state(live)), reason
    if live.refusal("kr_regime_tags") is None:
        assert "unsigned draft" not in reason and " is signed (" in reason, reason
    assert _regime01_tag_state(fixture_set()).startswith("kr_regime_tags.yaml v1.0.0-fixture is signed (")
    assert _regime01_tag_state(drafts_set()).startswith("kr_regime_tags.yaml is refused at load (")


# --------------------------------------------------------------------------- #
# T-SAT-01
# --------------------------------------------------------------------------- #
def test_sat01_saturday_sessions_and_completeness():
    cal = fixture_set()
    closed = cal.holiday_set("KRX")[0]
    d, n_before, n_after = date(1995, 1, 7), 0, 0
    assert d.weekday() == 5
    while d <= date(2001, 12, 29):
        want = d < date(1998, 12, 12) and d not in closed
        assert clocks.is_session("KR", d, cal=cal) is want, d
        n_before += want
        n_after += d >= date(1998, 12, 12)
        d += timedelta(days=7)
    assert n_before > 150 and n_after > 150
    assert clocks.is_session("KR", date(1997, 3, 1), cal=cal) is False          # a Saturday holiday
    assert clocks.is_session("KR", date(1997, 6, 8), cal=cal) is False          # Sunday never
    # completeness: a close list without the Saturdays fails; one with every session passes
    start, end = date(1997, 1, 3), date(1998, 12, 31)
    sessions = clocks.sessions_between("KR", start, end, cal=cal)
    weekdays_only = [s for s in sessions if s.weekday() < 5]
    rep = clocks.completeness_check("KR", weekdays_only, start, end, cal=cal)
    assert not rep.ok and rep.missing and all(m.weekday() == 5 for m in rep.missing) and not rep.extra
    assert clocks.completeness_check("KR", sessions, start, end, cal=cal).ok
    dup = clocks.completeness_check("KR", sessions + [sessions[0]], start, end, cal=cal)
    assert dup.duplicates == (sessions[0],)
    extra = clocks.completeness_check("KR", sessions + [date(1997, 6, 8)], start, end, cal=cal)
    assert extra.extra == (date(1997, 6, 8),)


test_sat01_saturday_sessions_and_completeness.test_ids = ["T-SAT-01"]


def test_sat01_real_kospi_completeness_and_variance_ratio():
    """T-SAT-01 on the KRX official closes (F01, 1997-01-03..2026-10-02): NOT_RUN (REFDATA) until F01 is listed with its
    md5, NOT_RUN (OWNER) while the signed KRX clock files do not cover that span (holidays_KRX starts in 2026); then PASS
    or FAIL on `_check_sat01`. The 1997-98 Monday / Tue-Fri variance ratio is printed (spec L2097: 2.30, EX2)."""
    text = require_fixture(F01).read_text(encoding="utf-8")
    rows = _kospi_closes(text)
    out = _check_sat01(rows, _official_calendar(*F01_SPAN), *F01_SPAN)
    ratio = "n/a" if out["ratio"] is None else f"{out['ratio']:.2f}"
    print(f"PRINTED T-SAT-01 F01: {out['sessions']} sessions, {out['saturdays']} Saturday sessions; Monday / Tue-Fri "
          f"variance ratio 1997-98 {ratio} (spec L2097 prints 2.30, EX2; not asserted)")


test_sat01_real_kospi_completeness_and_variance_ratio.test_ids = ["T-SAT-01"]


def test_sat01_body_passes_and_fails_on_invented_closes():
    """LA-02 part 1: the T-SAT-01 body can PASS and can FAIL. Invented closes in the F01 layout on the synthetic
    calendars (no KRX data), 1997-01-03..1998-12-31: one close per session, Saturdays included, passes. It fails when
    the Saturday closes are dropped, when a row lies outside the span, and, on a calendar with a wrong Saturday rule,
    when there are no Saturday sessions or a Saturday session falls on 1998-12-12 or later. The owner-calendar gate
    returns a covering set and names the coverage gap of a set whose KRX holiday file covers 2026-27 only."""
    cal = fixture_set()
    start, end = date(1997, 1, 3), date(1998, 12, 31)
    rows = _invented_closes(cal, start, end)
    out = _check_sat01(_kospi_closes(_f01_text(rows)), cal, start, end)
    assert out["saturdays"] > 0 and out["ratio"] is not None and out["sessions"] == len(rows)
    weekdays = [r for r in rows if r[0].weekday() != 5]
    e = _raises(lambda: _check_sat01(_kospi_closes(_f01_text(weekdays)), cal, start, end), AssertionError)
    assert "completeness fails: missing" in str(e)
    span = _raises(lambda: _check_sat01(_kospi_closes(_f01_text(rows)), cal, start, date(1998, 6, 30)), AssertionError)
    assert "outside 1997-01-03..1998-06-30" in str(span), span
    # the Saturday clauses fail on a calendar whose Saturday rule is wrong (rows consistent with that calendar)
    no_sat = _saturday_rule_set("1995-01-01")
    plain = _invented_closes(no_sat, start, end)
    e = _raises(lambda: _check_sat01(_kospi_closes(_f01_text(plain)), no_sat, start, end), AssertionError)
    assert "do not fail the completeness check" in str(e) and "0 Saturday rows" in str(e), e
    late_sat = _saturday_rule_set("1999-07-03")
    lo, hi = date(1998, 11, 2), date(1999, 1, 29)
    late = _invented_closes(late_sat, lo, hi, stamped=False)
    e = _raises(lambda: _check_sat01(_kospi_closes(_f01_text(late)), late_sat, lo, hi), AssertionError)
    assert "a Saturday close on or after 1998-12-12 (1998-12-12" in str(e), e
    # the owner-calendar gate: a covering set is returned; the shipped span of holidays_KRX (2026-27) is a gap
    assert _official_calendar_on(*F01_SPAN, cal) is cal
    owner = _raises(lambda: _official_calendar(*F01_SPAN, live=krx_short_set()), NotRun)
    assert owner.reason == ("OWNER: the signed KRX clock files must cover 1997-01-03..2026-10-02: holidays_KRX.yaml "
                            "v1.0.0-fixture covers 2026-01-01..2027-12-31"), owner.reason


# --------------------------------------------------------------------------- #
# T-XMKT-01
# --------------------------------------------------------------------------- #
def test_xmkt01_same_instant_closes():
    cal = fixture_set()
    csat = {date(2015, 11, 12), date(2025, 11, 13)}
    checked = {"jp_late": 0, "jp_mid": 0, "jp_early": 0, "tw": 0, "hk": 0}
    d = date(2015, 1, 5)
    while d <= date(2027, 6, 30):
        if clocks.is_session("KR", d, cal=cal) and d not in csat:
            bound = clocks.close_print_bound_utc("KR", d, cal=cal)
            if clocks.is_session("JP", d, cal=cal):
                usable = clocks.cross_market_usable("JP", d, bound, cal=cal)
                if d >= date(2024, 11, 5):
                    assert not usable, d
                    checked["jp_late"] += 1
                elif d >= date(2016, 8, 1):
                    assert usable, d
                    checked["jp_mid"] += 1
                else:
                    assert not usable, d
                    checked["jp_early"] += 1
            if d.weekday() < 5 and clocks.is_session("TW", d, cal=cal):
                assert clocks.cross_market_usable("TW", d, bound, cal=cal), d
                checked["tw"] += 1
            if clocks.is_session("HK", d, cal=cal):
                assert not clocks.cross_market_usable("HK", d, bound, cal=cal), d
                checked["hk"] += 1
            if clocks.is_session("CN", d, cal=cal):
                assert not clocks.cross_market_usable("CN", d, bound, cal=cal), d
        d += timedelta(days=1)
    assert all(v > 100 for v in checked.values()), checked
    b = clocks.close_print_bound_utc("KR", date(2025, 11, 13), cal=cal)
    assert b == U(2025, 11, 13, 7, 30, 30)
    assert clocks.cross_market_usable("JP", date(2025, 11, 13), b, cal=cal) and clocks.cross_market_usable("CN", date(2025, 11, 13), b, cal=cal)
    assert not clocks.cross_market_usable("HK", date(2025, 11, 13), b, cal=cal)
    b15 = clocks.close_print_bound_utc("KR", date(2015, 11, 12), cal=cal)      # configured 16:00 KST close -> 07:00:30Z
    assert b15 == U(2015, 11, 12, 7, 0, 30)
    assert clocks.cross_market_usable("JP", date(2015, 11, 12), b15, cal=cal) and not clocks.cross_market_usable("CN", date(2015, 11, 12), b15, cal=cal)
    # the worked boundary: 06:00Z + 60 s vs the 06:00:30Z bound before 2016-08-01
    assert clocks.close_print_bound_utc("JP", date(2016, 7, 29), cal=cal) + timedelta(seconds=cal.buffer_s) == U(2016, 7, 29, 6, 1)
    assert cal.buffer_s == 60
    # a Saturday session follows its signed close: the TW close is a weekday-only fact, the JP market is closed
    sat = date(1997, 6, 7)
    _raises(lambda: clocks.is_session("JP", sat, cal=cal), CalendarCoverageError)      # JPX fixture starts 2015


test_xmkt01_same_instant_closes.test_ids = ["T-XMKT-01"]


# --------------------------------------------------------------------------- #
# Publication calendars: T-H15-01, T-H10-02, T-VIX-01, T-AVAIL-01 (calendar halves)
# --------------------------------------------------------------------------- #
def test_publication_h15_h10_vix_avail_timing():
    cal = fixture_set()
    H15 = {"series_id": "DGS10", "schedule_id": "H15", "obs_calendar": "SIFMA"}
    H10 = {"series_id": "DEXKOUS", "schedule_id": "H10", "obs_calendar": "WEEKDAYS"}
    PI, UA = publication.publication_instant, publication.usable_at
    ny = ZoneInfo(NY)
    # separate sets: Columbus Day 2026-10-12 is a NYSE session and a Fed holiday
    assert clocks.is_session("US", date(2026, 10, 12), cal=cal) and not publication.fed_business_day(date(2026, 10, 12), cal=cal)
    assert not publication.nyse_holiday(date(2026, 10, 12), cal=cal) and publication.nyse_holiday(date(2026, 11, 26), cal=cal)
    assert publication.sifma_status(date(2026, 11, 27), cal=cal) == "early_close" and publication.sifma_status(date(2026, 4, 3), cal=cal) == "closed"
    assert publication.sifma_status(date(2026, 10, 8), cal=cal) == "open" and publication.sifma_status(date(2026, 10, 10), cal=cal) == "closed"
    # H.15: DGS10 Fri 2015-01-02 -> posted Mon 2015-01-05 16:15 ET -> KRX Tue 2015-01-06, not Mon
    assert PI(H15, date(2015, 1, 2), cal=cal) == datetime(2015, 1, 5, 16, 15, tzinfo=ny).astimezone(UTC)
    assert UA(H15, date(2015, 1, 2), "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2015, 1, 6), cal=cal)
    assert UA(H15, date(2015, 1, 2), "KR", cal=cal) != clocks.close_print_bound_utc("KR", date(2015, 1, 5), cal=cal)
    assert UA(H15, date(2026, 10, 9), "US", cal=cal) == clocks.close_print_bound_utc("US", date(2026, 10, 14), cal=cal)
    assert UA(H15, date(2026, 10, 8), "US", cal=cal) == clocks.close_print_bound_utc("US", date(2026, 10, 12), cal=cal)
    # R4b state row timing: data dated 2026-09-23 -> posted 09-24 16:15 ET -> first US close 09-25 -> earns from 09-28
    first_us = UA(H15, date(2026, 9, 23), "US", cal=cal)
    assert first_us == clocks.close_print_bound_utc("US", date(2026, 9, 25), cal=cal)
    assert clocks.next_session("US", date(2026, 9, 25), cal=cal) == date(2026, 9, 28)
    # Treasury par channel with a logged posting time: usable + 1 business day at a US close
    par = {"series_id": "TREASURY_PAR_10Y", "schedule_id": "TREASURY_PAR", "obs_calendar": "SIFMA"}
    assert UA(par, date(2026, 9, 23), "US", cal=cal) == clocks.close_print_bound_utc("US", date(2026, 9, 24), cal=cal)
    # H.10: DEXKOUS Fri 2026-09-25 -> Mon 09-28 16:15 ET -> KRX Tue 09-29 and not before
    assert UA(H10, date(2026, 9, 25), "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2026, 9, 29), cal=cal)
    assert publication.latest_usable_obs(H10, "KR", date(2026, 10, 2), cal=cal) == date(2026, 9, 25)
    assert publication.latest_usable_obs(H10, "KR", date(2026, 9, 28), cal=cal) == date(2026, 9, 18)
    for d in (date(2026, 10, 5), date(2026, 10, 9)):
        assert PI(H10, d, cal=cal) == datetime(2026, 10, 13, 16, 15, tzinfo=ny).astimezone(UTC)
        assert UA(H10, d, "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2026, 10, 14), cal=cal)
    # VIX: official close 16:15 ET on D is not usable at the US close of D; usable at D+1 and at KRX K >= D+1
    vix = {"series_id": "VIXCLS", "schedule_id": "VIXCLS_CBOE", "obs_calendar": "CBOE"}
    D = date(2026, 9, 23)
    assert PI(vix, D, cal=cal) > clocks.close_print_bound_utc("US", D, cal=cal)
    assert UA(vix, D, "US", cal=cal) == clocks.close_print_bound_utc("US", date(2026, 9, 24), cal=cal)
    assert UA(vix, D, "KR", cal=cal) == clocks.close_print_bound_utc("KR", clocks.next_session("KR", D, cal=cal), cal=cal)
    assert clocks.next_session("KR", D, cal=cal) == date(2026, 9, 28)                       # Chuseok in the fixture
    assert UA(vix, date(2026, 9, 21), "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2026, 9, 22), cal=cal)
    assert UA(vix, date(2026, 9, 21), "KR", cal=cal) != clocks.close_print_bound_utc("KR", date(2026, 9, 21), cal=cal)
    fred = {"series_id": "VIXCLS", "schedule_id": "VIXCLS_FRED", "obs_calendar": "CBOE", "channel": "FRED"}
    assert UA(fred, D, "US", cal=cal) == clocks.close_print_bound_utc("US", date(2026, 9, 24), cal=cal)       # declared lag
    logged = dict(fred, posting_utc="2026-09-24T21:05:00Z")
    assert PI(logged, D, cal=cal) == U(2026, 9, 24, 21, 5)
    assert UA(logged, D, "US", cal=cal) == clocks.close_print_bound_utc("US", date(2026, 9, 25), cal=cal)
    # T-AVAIL-01 rows + the injected registry error (H.15 posted at D) changes the KRX answer -> the golden would fail
    assert clocks.decision_time_utc("KR", date(2025, 11, 13), cal=cal) == U(2025, 11, 13, 7, 30)
    wrong = dict(H15, rule="same_day")
    assert UA(wrong, date(2015, 1, 2), "KR", cal=cal) == clocks.close_print_bound_utc("KR", date(2015, 1, 5), cal=cal)
    assert UA(wrong, date(2015, 1, 2), "KR", cal=cal) != UA(H15, date(2015, 1, 2), "KR", cal=cal)
    # next_expected_obs skips source-exception dates; add_publication_bdays keeps the wall time across DST
    assert publication.next_expected_obs(H10, date(2017, 1, 19), cal=cal) == date(2017, 1, 23)
    assert publication.next_expected_obs(H10, date(2017, 1, 18), cal=cal) == date(2017, 1, 19)
    assert publication.next_expected_obs(H15, date(2026, 4, 2), cal=cal) == date(2026, 4, 6)       # Good Friday on SIFMA
    assert publication.source_skipped("DEXKOUS", cal=cal) >= {date(2017, 1, 20), date(2020, 12, 24)}
    due = PI(H15, date(2026, 3, 6), cal=cal)                                     # Mon 2026-03-09 16:15 EDT (DST started 03-08)
    assert due == U(2026, 3, 9, 20, 15)
    assert publication.add_publication_bdays(H15, due, 1, cal=cal) == U(2026, 3, 10, 20, 15)
    before = PI(H15, date(2026, 3, 5), cal=cal)                                  # Fri 2026-03-06 16:15 EST
    assert before == U(2026, 3, 6, 21, 15) and publication.add_publication_bdays(H15, before, 1, cal=cal) == U(2026, 3, 9, 20, 15)
    # ECOS USD/KRW effective-dated same-day close; KODEX 200 basket next KRX session 08:00 KST
    ecos = {"series_id": "ECOS_USDKRW", "schedule_id": "ECOS_USDKRW", "obs_calendar": "ECOS"}
    assert PI(ecos, date(2016, 7, 29), cal=cal) == U(2016, 7, 29, 6, 0) and PI(ecos, date(2016, 8, 1), cal=cal) == U(2016, 8, 1, 6, 30)
    assert PI({"schedule_id": "KODEX200_PDF"}, date(2026, 10, 2), cal=cal) == U(2026, 10, 5, 23, 0)
    # a release event that is cancelled removes the expected instant; a delayed one moves it
    bls = {"series_id": "CPIAUCSL", "schedule_id": "BLS", "release_event_type": "US_CPI", "obs_calendar": "WEEKDAYS",
           "release_dates": {"2025-10-01": "2025-11-13"}}
    cancelled = [{"type": "US_CPI", "scheduled_utc": "2025-11-13T13:30:00Z", "status": "cancelled", "released_utc": None}]
    _raises(lambda: PI(bls, date(2025, 10, 1), cal=cal, events=cancelled), publication.NoExpectedObservation)
    delayed = [{"type": "US_CPI", "scheduled_utc": "2025-11-13T13:30:00Z", "status": "delayed", "released_utc": "2025-11-20T13:30:00Z"}]
    assert PI(bls, date(2025, 10, 1), cal=cal, events=delayed) == U(2025, 11, 20, 13, 30)
    assert PI(bls, date(2025, 10, 1), cal=cal) == U(2025, 11, 13, 13, 30)
    _raises(lambda: PI({"schedule_id": "BLS"}, date(2025, 10, 1), cal=cal), KeyError)
    # a bare series id resolves through the registry (core.calendars.adapter, integration): H.15 of Fri 2026-01-02 posts Mon 16:15 ET
    assert PI("DGS10", date(2026, 1, 2), cal=cal) == U(2026, 1, 5, 21, 15)
    _raises(lambda: PI("NO_SUCH_SERIES", date(2026, 1, 2), cal=cal), KeyError)


test_publication_h15_h10_vix_avail_timing.test_ids = ["T-H15-01", "T-H10-02", "T-VIX-01", "T-AVAIL-01"]


# --------------------------------------------------------------------------- #
# Section 6.3 event store shape (M1: shape and loader only)
# --------------------------------------------------------------------------- #
def test_event_store_shape_and_artifact():
    from core.ficc.macro_artifacts import provenance
    cal = fixture_set()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.yaml"
        path.write_text(yaml.safe_dump([{
            "event_id": "FOMC-2026-10-28", "type": "FOMC", "region": "US", "scheduled_utc": "2026-10-28T18:00:00Z",
            "status": "scheduled", "released_utc": None, "source": "federalreserve.gov FOMC calendar",
            "windows": [{"market": "US", "action": "evaluator_block_new_intraday_entries", "start_utc": "2026-10-28T17:45:00Z",
                         "end_utc": "2026-10-28T19:00:00Z", "resume_condition": "VIX < pre-14:00 ET level else 19:30Z"}],
            "kr_open_gap_session": "2026-10-29", "gap_sessions": None, "var_display_scale": None, "scenario_tag": None,
            "notes": "KR opening-gap event night"}], sort_keys=False), encoding="utf-8")
        loaded = events.load_events(path)
    assert len(loaded) == 1 and loaded[0].type == "FOMC" and loaded[0].kr_open_gap_session == "2026-10-29"
    assert clocks.kr_open_gap_session(events.utc(loaded[0].scheduled_utc), cal=cal).isoformat() == loaded[0].kr_open_gap_session
    prov = provenance(clock=lambda: U(2026, 10, 2, 6, 41, 7), knowledge_utc="2026-10-02T06:40:50Z", config_hash="c" * 32,
                      data_snapshot_id="d" * 32)
    art = events.event_calendar(loaded, provenance=prov, calendar_version=cal.version)
    assert art["schema"] == "quantgen.event_calendar" and art["read_only"] is True and art["calendar_version"] == "1.0.0-fixture"
    assert art["events"][0]["windows"][0]["action"] == "evaluator_block_new_intraday_entries"
    bad = dict(loaded[0].to_dict(), type="FOMC", status="done")
    _raises(lambda: events.Event.from_dict(bad), ValueError)
    _raises(lambda: events.event_calendar([dict(loaded[0].to_dict(), gap_sessions=-1)], provenance=prov, calendar_version="x"), ValueError)
    assert "KRX_HOLIDAY_GAP" in events.EVENT_TYPES and "annotate_only" in events.WINDOW_ACTIONS


test_event_store_shape_and_artifact.test_ids = ["I-06"]


# --------------------------------------------------------------------------- #
# Market ids
# --------------------------------------------------------------------------- #
def test_market_ids_and_venue_maps():
    from core import markets
    from core.ficc.macro_schema import enum_of
    assert markets.MACRO_MARKETS == enum_of("macro_state", "/market")
    assert markets.market_to_venue("KR") == "KRX" and markets.market_to_venue("JP") == "TSE" and markets.venue_to_market("HKEX") == "HK"
    assert markets.venue_to_market("SZSE") == "CN" and markets.venue_to_market(markets.market_to_venue("TW")) == "TW"
    _raises(lambda: markets.market_to_venue("CRYPTO"), KeyError)
    _raises(lambda: markets.market_to_venue("KRX"), KeyError)
    assert all(markets.market_to_venue(m) in markets.codes() for m in clocks.M1_MARKETS)
    assert set(clocks.M1_MARKETS) == set(store.MARKET_FILES) == set(store.MARKET_HOLIDAY_SET)


test_market_ids_and_venue_maps.test_ids = ["T-XMKT-01"]


if __name__ == "__main__":
    from tests.macro_acceptance import run_module
    raise SystemExit(run_module(globals()))
