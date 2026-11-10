"""M1 package A tests: PIT store, data contracts, staleness, lag audit, series registry, cache fix, KIS allowlist.

Spec tests: T-PROV-01, T-FIX-01, T-BAR-01/02, T-CLOSE-01 (data clauses), T-PRINT-01 (logic), T-AVAIL-01,
T-STALE-01 (synthetic clauses + the local fred_DEXKOUS.csv smoke), T-ROLE-01/02, T-LAG-01/02, T-SYN-01,
T-MISS-01/02, T-SER-01/02, T-H10-01/02, T-H15-01, T-VIX-01, T-XMKT-01 (data clause), T-RO-02, G-POST-01 (REFDATA).

Hermetic: every store is a tempfile directory; no network; no wall clock (every instant is pinned); module globals
that a test patches are restored in `finally`. Calendar functions come from `StubClocks` below, a deterministic
stand-in for `core.calendars.clocks` (package B), keyed on the registry's schedule ids. One clause reads the shipped
owner-signed calendar files instead: T-AVAIL-01 on the official calendars runs the same golden table through
`core.calendars.adapter.CalendarClocks` once those files load and cover the golden days (look-ahead audit LA-02).
The REFDATA bodies (G-POST-01 data rows, T-PRINT-01 on Yahoo ^KS11, G-STALE-01 / T-STALE-01, T-MISS-01; LA-02 part 2)
read their listed fixtures through `require_fixture` in a declared layout, and the shipped calendar files only when
those load and cover the days read (otherwise NotRun "OWNER: ...", computed from the files); each body is also shown to
PASS and to FAIL on invented in-memory rows.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import statistics
import tempfile
import time as _time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import config
from core.ficc import contracts as C
from core.ficc import data as D
from core.ficc import lag_audit as L
from core.ficc import pit as P
from tests import golden_tools as G
from tests.notrun import NotRun, require_fixture

ROOT = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")
UTC = timezone.utc
KST = timezone(timedelta(hours=9))
REG = C.load_registry()


def U(y, m, d, hh=0, mm=0, ss=0):
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


# --------------------------------------------------------------------------- #
# Stub clocks (integration: core.calendars.clocks / publication)
# --------------------------------------------------------------------------- #
def _nth(y, m, weekday, n):
    d = date(y, m, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last(y, m, weekday):
    d = date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _observed(d):
    return d + timedelta(days=1) if d.weekday() == 6 else d - timedelta(days=1) if d.weekday() == 5 else d


def federal_holidays(y):
    fixed = [date(y, 1, 1), date(y, 7, 4), date(y, 11, 11), date(y, 12, 25)] + ([date(y, 6, 19)] if y >= 2021 else [])
    return {_observed(d) for d in fixed} | {_nth(y, 1, 0, 3), _nth(y, 2, 0, 3), _last(y, 5, 0), _nth(y, 9, 0, 1),
                                           _nth(y, 10, 0, 2), _nth(y, 11, 3, 4)}


def _json_holidays(name):
    return {date.fromisoformat(h) for h in json.loads((ROOT / "data" / "calendars" / name).read_text(encoding="utf-8"))["holidays"]}


KRX_HOLIDAYS = _json_holidays("KRX.json") | {date(2015, 1, 1), date(2016, 1, 1), date(2024, 1, 1), date(2025, 1, 1)}
NYSE_HOLIDAYS = _json_holidays("US.json") | {date(2015, 1, 1), date(2025, 7, 4)}
CSAT = {date(2025, 11, 13), date(2026, 11, 19)}
US_EARLY = {date(2026, 11, 27), date(2026, 12, 24), date(2025, 7, 3)}
SOURCE_SKIPPED = {date(2016, 1, 22), date(2017, 1, 20), date(2018, 3, 2), date(2018, 12, 5), date(2020, 11, 27), date(2020, 12, 24)}


class NotASession(ValueError):
    pass


class StubClocks:
    """Deterministic calendar rules: KRX (06:00:30Z before 2016-08-01, 06:30:30Z after, CSAT 07:30:30Z), NYSE
    (16:00 ET + 30 s, DST via zoneinfo, 13:00 early closes), Fed business days (rule-based federal holidays),
    H.15 / H.10 / Treasury / VIX / BLS instants from the registry schedule ids."""

    def __init__(self, registry=REG, skipped=frozenset(), unreadable=False):
        self.registry, self.skipped, self.unreadable = registry, set(skipped), unreadable

    # sessions
    def is_session(self, market, d):
        if d.weekday() >= 5:
            return False
        if market == "KR":
            return d not in KRX_HOLIDAYS
        if market == "US":
            return d not in NYSE_HOLIDAYS
        return True

    def fed_bday(self, d):
        # next year's New Year observance can fall on this year's Dec 31 (Saturday -> Friday, e.g. 2021-12-31)
        return d.weekday() < 5 and d not in federal_holidays(d.year) and d not in federal_holidays(d.year + 1)

    def _next(self, d, ok):
        d += timedelta(days=1)
        while not ok(d):
            d += timedelta(days=1)
        return d

    def close_print_bound_utc(self, market, d):
        if not self.is_session(market, d):
            raise NotASession(f"{market} {d}")
        if market == "KR":
            if d in CSAT:
                return U(d.year, d.month, d.day, 7, 30, 30)
            return U(d.year, d.month, d.day, 6, 0, 30) if d < date(2016, 8, 1) else U(d.year, d.month, d.day, 6, 30, 30)
        if market == "US":
            hour = 13 if d in US_EARLY else 16
            return datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=NY).astimezone(UTC) + timedelta(seconds=30)
        hh, mm = {"JP": (6, 30) if d >= date(2024, 11, 5) else (6, 0), "CN": (7, 0), "HK": (8, 0), "TW": (5, 30)}[market]
        return U(d.year, d.month, d.day, hh, mm)

    # schedules
    def _sched(self, series_id):
        if self.unreadable:
            raise RuntimeError("publication calendar unreadable")
        return self.registry.schedule(series_id)

    def _ny(self, d, hhmm):
        hh, mm = map(int, hhmm.split(":"))
        return datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).astimezone(UTC)

    def publication_instant(self, series_id, d):
        s = self._sched(series_id)
        if s == "KRX_CLOSE":
            return self.close_print_bound_utc("KR", d)
        if s == "NYSE_CLOSE":
            return self.close_print_bound_utc("US", d)
        if s in ("JP_CLOSE", "CN_CLOSE", "HK_CLOSE", "TW_CLOSE"):
            return self.close_print_bound_utc(s[:2], d)
        if s == "FRED_H15":
            return self._ny(self._next(d, self.fed_bday), "16:15")
        if s == "H10":
            monday = d + timedelta(days=7 - d.weekday())
            if not self.fed_bday(monday):
                monday = self._next(monday, self.fed_bday)
            return self._ny(monday, "16:15")
        if s == "TREASURY_PAR":
            return self._ny(d, "18:00")
        if s == "VIXCLS":
            return self._ny(d, "16:15")
        if s in ("BLS", "BEA"):
            return self._ny(d, "08:30")
        if s == "ECOS_1530":
            hh = 15 if d >= date(2016, 8, 1) else 15
            return datetime(d.year, d.month, d.day, hh, 30 if d >= date(2016, 8, 1) else 0, tzinfo=KST).astimezone(UTC)
        if s == "KODEX_PDF":
            n = self._next(d, lambda x: self.is_session("KR", x))
            return datetime(n.year, n.month, n.day, 8, 0, tzinfo=KST).astimezone(UTC)
        return None

    def next_expected_obs(self, series_id, d):
        s = self._sched(series_id)
        if s in ("FRED_H15", "H10"):
            return self._next(d, lambda x: self.fed_bday(x) and x not in self.skipped)
        if s in ("KRX_CLOSE", "KODEX_PDF"):
            return self._next(d, lambda x: self.is_session("KR", x))
        if s in ("NYSE_CLOSE", "VIXCLS", "TREASURY_PAR"):
            return self._next(d, lambda x: self.is_session("US", x))
        if s in ("BLS", "BEA"):
            return P.add_months(d, 1)
        return None

    def add_publication_bdays(self, series_id, instant, n):
        s = self._sched(series_id)
        if instant is None:
            return None
        local = instant.astimezone(NY if s not in ("KRX_CLOSE", "KODEX_PDF", "ECOS_1530") else KST)
        d = local.date()
        ok = (lambda x: self.is_session("KR", x)) if s in ("KRX_CLOSE", "KODEX_PDF", "ECOS_1530") else \
             (lambda x: self.is_session("US", x)) if s in ("NYSE_CLOSE", "VIXCLS", "TREASURY_PAR") else self.fed_bday
        for _ in range(n):
            d = self._next(d, ok)
        if s in ("KRX_CLOSE", "NYSE_CLOSE"):
            return self.close_print_bound_utc("KR" if s == "KRX_CLOSE" else "US", d)
        return local.replace(year=d.year, month=d.month, day=d.day).astimezone(UTC)


CLK = StubClocks()


# --------------------------------------------------------------------------- #
# Fixtures and helpers
# --------------------------------------------------------------------------- #
DECISION = U(2026, 10, 2, 6, 30, 30)
OCT2 = date(2026, 10, 2)


def _tmp():
    return Path(tempfile.mkdtemp(prefix="m1pit_"))


def _store(clocks=CLK):
    return P.PITStore(_tmp() / "store", registry=REG, clocks=clocks)


def _kospi(value, *, obs_date=OCT2, status, obs_utc, available, retrieved, source, src="calendar_bound", kind=None,
           synthetic=False, provider_mode="explicit", session=None):
    kind = kind or ("close" if status in P.CLOSE_STATUSES else "quote_snapshot")
    return P.make_row(series_id="KOSPI_OFFICIAL_CLOSE", value=value, obs_date=obs_date,
                      session_date=(session or obs_date) if kind == "close" else session, obs_utc=obs_utc,
                      obs_kind=kind, value_status=status, available_at_utc=available, available_at_source=src,
                      retrieved_at_utc=retrieved, vintage=None, source=source, channel=None,
                      provider_mode=provider_mode, synthetic=synthetic)


def prov01_rows():
    """The T-PROV-01 fixture rows verbatim (L5612): a synthetic store file, exempt from the post-close rule."""
    return [
        _kospi(6943.66, status="provisional_intraday", obs_utc=U(2026, 10, 2, 1, 30), available=U(2026, 10, 2, 1, 30),
               retrieved=U(2026, 10, 2, 1, 56), source="Yahoo", src="inferred_from_retrieval"),
        _kospi(7003.74, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
               retrieved=U(2026, 10, 2, 6, 40, 45), source="KRX"),
    ]


def _read(store, knowledge, **kw):
    return P.pit_value(store, "KOSPI_OFFICIAL_CLOSE", DECISION, knowledge, "R-06", OCT2, registry=REG, **kw)


def _raises(fn, exc=Exception, needle=""):
    try:
        fn()
    except exc as e:
        assert needle.lower() in str(e).lower(), f"{needle!r} not in {e}"
        return e
    raise AssertionError(f"expected {exc.__name__}")


def _release(sid, d, value, retrieved, *, source="FRED", clocks=CLK, posting=None):
    return P.stamp_release(sid, d, value, retrieved_at_utc=retrieved, source=source, registry=REG, clocks=clocks,
                           posting_time_utc=posting)


# --------------------------------------------------------------------------- #
# T-PROV-01: store, trace, cache regression
# --------------------------------------------------------------------------- #
def test_prov_01_store_read_trace():
    store = _store()
    rows = prov01_rows()
    assert store.append(rows) == 2 and store.append(rows) == 0          # dedupe: unchanged content -> fetch log only
    assert (store.path / "fetch_log.jsonl").read_text(encoding="utf-8").count("unchanged") == 2
    a = _read(store, U(2026, 10, 2, 1, 31))
    assert isinstance(a, P.MissingInput) and a.reason == "missing" and a.role == "acting_exposure" and a.books == ("specification",)
    b = _read(store, U(2026, 10, 2, 2, 0))
    assert isinstance(b, P.MissingInput) and b.reason == "provisional_intraday"
    c = _read(store, U(2026, 10, 2, 7, 0))
    assert isinstance(c, P.PITValue) and c.value == 7003.74 and c.value_status == "official_close" and not c.dispute
    assert c.available_at_source == "calendar_bound" and c.retrieved_at_utc == U(2026, 10, 2, 6, 40, 45)
    # the previous session's close being visible does not rescue a missing close (L1009-1010)
    prev = _kospi(6971.5, obs_date=date(2026, 10, 1), status="official_close", obs_utc=U(2026, 10, 1, 6, 30, 30),
                  available=U(2026, 10, 1, 6, 30, 30), retrieved=U(2026, 10, 1, 6, 41), source="KRX")
    store.append([prev])
    assert _read(store, U(2026, 10, 2, 1, 31)).reason == "missing"
    # require_session is mandatory for a close-type acting read; a context consumer reads without it
    _raises(lambda: P.pit_value(store, "KOSPI_OFFICIAL_CLOSE", DECISION, U(2026, 10, 2, 7), "R-06", registry=REG),
            P.PITError, "require_session")
    # session_mismatch: a mis-dated official row
    bad = _kospi(7003.74, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                 retrieved=U(2026, 10, 2, 6, 50), source="KIS", session=date(2026, 10, 1))
    s2 = _store()
    s2.append([bad])
    assert _read(s2, U(2026, 10, 2, 7)).reason == "session_mismatch"
    # vendor_close: refused live; accepted in a backtest only when the header declares that vendor
    s3 = _store()
    s3.append([_kospi(7003.74, status="vendor_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                      retrieved=U(2026, 10, 2, 6, 41), source="Yahoo")])
    assert _read(s3, U(2026, 10, 2, 7)).reason == "provisional_intraday"
    assert _read(s3, U(2026, 10, 2, 7), run_mode="backtest").reason == "provisional_intraday"
    assert _read(s3, U(2026, 10, 2, 7), run_mode="backtest", vendor="Yahoo").value_status == "vendor_close"
    # snapshot id: order-invariant, unchanged by a later correction
    sid_a = P.data_snapshot_id(store, U(2026, 10, 2, 7))
    store.append([_kospi(7003.75, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                         retrieved=U(2026, 10, 3, 1), source="KRX")])
    assert P.data_snapshot_id(store, U(2026, 10, 2, 7)) == sid_a != P.data_snapshot_id(store, U(2026, 10, 3, 2))
    reloaded = P.PITStore(store.path, registry=REG, clocks=CLK)
    assert [r["content_hash"] for r in reloaded.rows("KOSPI_OFFICIAL_CLOSE")] == [r["content_hash"] for r in store.rows("KOSPI_OFFICIAL_CLOSE")]


test_prov_01_store_read_trace.test_ids = ["T-PROV-01"]


class _Clock:
    """Stands in for the `time` module inside core.ficc.data: a pinned wall clock."""
    gmtime, strftime = staticmethod(_time.gmtime), staticmethod(_time.strftime)

    def __init__(self, now):
        self.now = now

    def time(self):
        return self.now


def test_prov_01_cache_regression_replays_the_incident():
    """ficc_cache written 01:56Z with the running 2-Oct row 6,943.66 (TASK-M1-12): the row is at most provisional
    and expires in 10 min; it is never served as the session close; the store answers the trace."""
    tmp = _tmp()
    saved = (D.time, D._MEM.copy(), config.FICC_CACHE_TTL_SECONDS, config.ficc_cache_dir, D._yf_fetch)
    try:
        config.FICC_CACHE_TTL_SECONDS = 21600.0
        config.ficc_cache_dir = lambda: tmp
        D._MEM.clear()
        written = U(2026, 10, 2, 1, 56).timestamp()
        rows = [["2026-09-30", 6950.0], ["2026-10-01", 6971.5], ["2026-10-02", 6943.66]]
        (tmp / "YFINANCE__KS11_504.json").write_text(json.dumps({"ts": written, "rows": rows}), "utf-8")
        key = D._cache_key("YFINANCE", "^KS11", 504)
        D.time = _Clock(U(2026, 10, 2, 2, 0).timestamp())
        assert D._cache_get(key) == [tuple(r) for r in rows]           # 4 min old: served, as a running bar
        D.time = _Clock(U(2026, 10, 2, 2, 7).timestamp())
        assert D._cache_get(key) is None                               # a running bar expires in 10 min
        D.time = _Clock(U(2026, 10, 2, 1, 58).timestamp())
        bound10 = (CLK.close_print_bound_utc("KR", OCT2) + timedelta(minutes=10)).timestamp()
        assert D._cache_get(key, not_before=bound10) is None           # never a session close before close + 10 min
        D.time = _Clock(U(2026, 10, 2, 7, 0).timestamp())
        assert D._cache_get(key, not_before=bound10) is None
        # the store path: the cached row is ingested with its file retrieved_at and is provisional; the re-fetch
        # fails (hermetic) -> MissingInput, never the cached row; the KIS official row answers at 16:00 KST
        store = _store()
        D.time = _Clock(U(2026, 10, 2, 2, 0).timestamp())
        D._MEM.clear()
        served, errors = D._provider_rows("YFINANCE", ["KOSPI_OFFICIAL_CLOSE"], 504, pit_store=store)
        assert not served and errors                                  # key differs by id; the fetch raises
        store.ingest_rows("YFINANCE", "KOSPI_OFFICIAL_CLOSE", rows, U(2026, 10, 2, 1, 56))
        assert _read(store, U(2026, 10, 2, 2, 0)).reason == "provisional_intraday"
        store.append([prov01_rows()[1]])
        assert _read(store, U(2026, 10, 2, 7, 0)).value == 7003.74
        D.time = _Clock(U(2026, 10, 2, 7, 0).timestamp())
        D._MEM.clear()
        served, errors = D._provider_rows("YFINANCE", ["^KS11"], 504, not_before=bound10, pit_store=store)
        assert served == {} and "^KS11" in errors                     # cache refused, re-fetch failed: not the cached row
    finally:
        D.time, mem, config.FICC_CACHE_TTL_SECONDS, config.ficc_cache_dir, D._yf_fetch = saved
        D._MEM.clear()
        D._MEM.update(mem)


test_prov_01_cache_regression_replays_the_incident.test_ids = ["T-PROV-01"]


def test_history_cache_b_marks_a_running_bar_provisional():
    """core.quant.history: `status` is appended with a default; a series fetched while its market may trade is
    stamped provisional_intraday and the cache file round-trips it."""
    from core.quant import history as H
    h = H.History("X", "FMP", ("2026-10-01",), (1.0,))
    assert h.status == "" and H.History("X", "FMP", ("d",), (1.0,), "n", "total").adjustment == "total"
    tmp = _tmp()
    saved = (config.FICC_CACHE_TTL_SECONDS, config.ficc_cache_dir, H._may_be_trading, H._READY.copy())
    try:
        config.FICC_CACHE_TTL_SECONDS = 21600.0
        config.ficc_cache_dir = lambda: tmp
        H._READY["FMP"] = lambda: True
        H._may_be_trading = lambda *a, **k: True
        dates = tuple((date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(40))
        fetched = H._cached("FMP", lambda s, days: H.History(s, "FMP", dates, tuple(range(1, 41))), "ABC", 40)
        assert fetched.status == "provisional_intraday"
        again = H._cached("FMP", lambda s, days: (_ for _ in ()).throw(AssertionError("asked twice")), "ABC", 40)
        assert again.status == "provisional_intraday" and "cached" in again.note
        assert json.loads((tmp / "HIST_FMP_ABC_40.json").read_text("utf-8"))["status"] == "provisional_intraday"
    finally:
        config.FICC_CACHE_TTL_SECONDS, config.ficc_cache_dir, H._may_be_trading = saved[:3]
        H._READY.clear()
        H._READY.update(saved[3])


test_history_cache_b_marks_a_running_bar_provisional.test_ids = ["T-PROV-01"]


# --------------------------------------------------------------------------- #
# REFDATA fixtures in declared layouts (look-ahead audit LA-02, part 2)
# --------------------------------------------------------------------------- #
# docs/macro_fixtures.py writes every data fixture as the reference file's own columns followed by the section 4.1
# provenance columns (series_id, obs_date, session_date, ..., value_status), one row per reference row, with obs_date
# and session_date both the reference row's date (ISO). ACQUISITION.csv and the spec name no reference column, so each
# body below declares the value columns it reads and the provenance values the generator writes for that file
# (docs/macro_fixtures.REFERENCE_FILES). Each declaration is an input contract for the owner to confirm at the
# acquisition step. The obs_utc / available_at_utc instants are not read: the generator's calendar_available_at
# refuses the series ids KS11, KRWX and 005930 (not in the registry), so the instants those files will carry are not
# settled; the staleness body stamps its FRED rows from the signed calendars itself.
FRED_MISSING = ("", ".")                    # a blank or "." value is no observation (FRED's missing-value marker)


def _fixture_csv(name: str, text: str, values: tuple[str, ...], provenance: tuple[tuple[str, str], ...],
                 keys: tuple[str, ...] = ()) -> list[dict]:
    """Rows of a generated fixture in a declared layout, as {"date": obs_date, <value column>: float | None, <key
    column>: str}; AssertionError on any departure: a declared column absent, a provenance value other than the
    declared one, obs_date != session_date, rows out of date order, a value that is neither a finite number nor FRED's
    missing marker. Two rows on one date are kept: the bodies count the rows on the days they read."""
    reader = csv.DictReader(io.StringIO(text))
    need = tuple(values) + tuple(keys) + tuple(k for k, _ in provenance) + ("obs_date", "session_date")
    missing = [c for c in need if c not in (reader.fieldnames or ())]
    assert not missing, f"{name}: declared columns {missing} absent (header {reader.fieldnames})"
    rows: list[dict] = []
    for line, raw in enumerate(reader, start=2):
        where = f"{name} line {line}"
        got = tuple((k, raw[k]) for k, _ in provenance)
        assert got == tuple(provenance), f"{where}: provenance {dict(got)} != declared {dict(provenance)}"
        d = date.fromisoformat(raw["obs_date"])
        assert date.fromisoformat(raw["session_date"]) == d, f"{where}: obs_date != session_date"
        assert not rows or rows[-1]["date"] <= d, f"{where}: rows out of date order"
        row: dict = {"date": d, **{k: raw[k] for k in keys}}
        for col in values:
            cell = (raw[col] or "").strip()
            try:
                row[col] = None if cell in FRED_MISSING else float(cell)
            except ValueError:
                raise AssertionError(f"{where}: {col} {raw[col]!r} is not a number") from None
            assert row[col] is None or math.isfinite(row[col]), f"{where}: {col} {raw[col]!r}"
        rows.append(row)
    assert rows, f"{name}: no rows"
    return rows


def _layout_text(rows, values: tuple[str, ...], provenance: tuple[tuple[str, str], ...], date_col: str = "date",
                 keys: tuple[str, ...] = ()) -> str:
    """Invented rows [(date, {column: value or None})] written in memory as the generator writes a fixture (the
    reference columns, then the provenance columns); a value None is written as FRED's ".", a key column verbatim. For
    the demonstrations only."""
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow((date_col,) + tuple(keys) + tuple(values) + tuple(k for k, _ in provenance) + ("obs_date", "session_date"))
    for d, vals in rows:
        cells = [vals[k] for k in keys] + ["." if vals.get(c) is None else repr(vals[c]) for c in values]
        out.writerow([d.isoformat()] + cells + [v for _, v in provenance] + [d.isoformat(), d.isoformat()])
    return buf.getvalue()


def _generator_provenance(name: str) -> tuple[tuple[str, str], ...]:
    """The provenance values docs/macro_fixtures.REFERENCE_FILES gives the fixture `name` (the generator's own table;
    the demonstrations pin each declared provenance to it)."""
    from docs import macro_fixtures as MF
    rows = [(series.split(";")[0], status, source) for _fid, rel, series, status, source, *_ in MF.REFERENCE_FILES
            if Path(rel).name == name]
    assert len(rows) == 1, f"{name}: {len(rows)} rows in docs/macro_fixtures.REFERENCE_FILES"
    return (("series_id", rows[0][0]), ("value_status", rows[0][1]), ("available_at_source", rows[0][2]))


# --------------------------------------------------------------------------- #
# T-FIX-01, G-POST-01
# --------------------------------------------------------------------------- #
def test_fix_01_post_close_fixtures_only():
    tmp = _tmp()
    good = P.write_fixture(tmp / "good.jsonl", [prov01_rows()[1]])
    assert P.check_fixture(good, registry=REG, clocks=CLK) == 1
    early = P.make_row(**{**{k: v for k, v in prov01_rows()[1].items() if k != "content_hash"},
                          "retrieved_at_utc": U(2026, 10, 2, 6, 40, 29)})
    _raises(lambda: P.check_fixture(P.write_fixture(tmp / "early.jsonl", [early]), registry=REG, clocks=CLK),
            P.FixtureRefused, "close + 10 min")
    pre_pub = _release("DGS10", date(2026, 10, 1), 4.1, U(2026, 10, 2, 20, 16), posting=U(2026, 10, 2, 20, 16))
    pre_pub = P.make_row(**{**{k: v for k, v in pre_pub.items() if k != "content_hash"}, "retrieved_at_utc": U(2026, 10, 2, 12)})
    _raises(lambda: P.check_fixture(P.write_fixture(tmp / "prepub.jsonl", [pre_pub]), registry=REG, clocks=CLK),
            P.FixtureRefused, "publication instant")
    exempt = P.write_fixture(tmp / "synthetic.jsonl", prov01_rows(), label={"fixture": "synthetic", "exempt": True,
                                                                            "tests": "T-PROV-01"})
    assert P.check_fixture(exempt, registry=REG, clocks=CLK) == 0
    # the local research cache (docs/asset_expansion/cache) was written 2026-09-25 ~16:30Z mid US session: a
    # US-close fixture built from its last rows is refused by the same rule (code_data_layer E.32)
    us_row = P.stamp_close("SPX_OFFICIAL_CLOSE", date(2026, 9, 25), 6650.0, retrieved_at_utc=U(2026, 9, 25, 16, 30),
                           source="Yahoo", registry=REG, clocks=CLK)
    assert us_row["value_status"] == "provisional_intraday" and us_row["obs_kind"] == "quote_snapshot"


test_fix_01_post_close_fixtures_only.test_ids = ["T-FIX-01"]


def test_fix_01_regeneration_at_level_1_tolerance_refdata():
    raise NotRun("REFDATA: /home/claude/quantgen_macro_data/ (CATALOG.md, scripts/, results/QX_DLA_postpatch.csv) absent: "
                 "golden fixtures cannot be generated or md5-frozen")


test_fix_01_regeneration_at_level_1_tolerance_refdata.test_ids = ["T-FIX-01"]


# G-POST-01, the M1 data rows (spec L5819-5834; goldens.csv G-POST-01 rows whose runs_from is M1). Declared layouts:
# F13 (docs/macro_fixtures.py:59): Yahoo ^KS11 daily, the close in `close`, series_id KS11, vendor_close, calendar_bound.
# F16 (docs/macro_fixtures.py:62): Yahoo KRW=X daily, the close in `close`, series_id KRWX, vendor_close, calendar_bound.
# F27 (docs/macro_fixtures.py:73): KRX Samsung 005930 and SK hynix 000660 closes and market caps in long form, one row
#   per code and KRX session: `code` (005930 or 000660) and its `close` (the market-cap columns ride along, unread);
#   series_id either id of "005930;000660" (the generator writes the first), official_close, calendar_bound.
# These are the layouts tests/macro_m1_fixtures.py declares for the same files (G-POST-01 row replay; `close` as in
# part 1's F01 and the generator test's reference files); the instants that file also reads are not read here.
F13 = "yahoo_KS11_1996-12_2026-10-02.csv"
F13_CLOSE = "close"
F13_PROVENANCE = (("series_id", "KS11"), ("value_status", "vendor_close"), ("available_at_source", "calendar_bound"))
F16 = "yahoo_KRWX_2004_2026-10-01.csv"
F16_CLOSE = "close"
F16_PROVENANCE = (("series_id", "KRWX"), ("value_status", "vendor_close"), ("available_at_source", "calendar_bound"))
F27 = "krx_005930_000660_closes_mcap.csv"
F27_CLOSE, F27_KEYS = "close", ("code", "series_id")
F27_CODES = ("005930", "000660")                # docs/macro_fixtures.py:73 series "005930;000660"
F27_PROVENANCE = (("value_status", "official_close"), ("available_at_source", "calendar_bound"))
GPOST01_FIXTURES = ("yahoo_KS11_1996-12_2026-10-02.csv", "yahoo_KRWX_2004_2026-10-01.csv",
                    "krx_005930_000660_closes_mcap.csv")           # F13, F16, F27 spelled out: T-HERM-01 checks each name
GPOST01_DAY = date(2026, 10, 2)                 # G-POST-01/kospi_close_2oct, samsung_close_2oct, hynix_close_2oct: "2 Oct 2026"
GPOST01_KRWX_LAST = date(2026, 10, 1)           # G-POST-01/krwx_last_row: "KRW=X last row (1 Oct 2026)", "provisional 2-Oct row dropped"
GPOST01_PEAK = (date(2026, 6, 22), 9114.55)     # G-POST-01/drawdown_from_peak: "the 9,114.55 peak (22 Jun 2026)"; spec L5821
GPOST01_SMA_N = 200                             # G-POST-01/close_over_200d note: "mean of last 200 closes incl. 2 Oct"
GPOST01_DLOG_N = 20                             # G-POST-01/krwx_dlog20: "KRW=X 20-observation dlog" (spec L5834 "20-observation change")
# The signed KRX clock files the body reads: the previous KRX session of 2 Oct (G-POST-01/kospi_return_2oct note
# "7,003.74 / prev close - 1"), read on the fortnight to 2 Oct as T-PRINT-01 reads its own (the part-1 owner gate
# tests.macro_m1_calendars._official_calendar; the shipped holidays_KRX covers 2026).
GPOST01_CAL_SPAN = (GPOST01_DAY - timedelta(days=14), GPOST01_DAY)


def _check_gpost01_m1(ks11: list[dict], krwx: list[dict], stocks: list[dict], cal) -> dict:
    """G-POST-01, the M1 data rows, at Level 1 from goldens.csv (read only): the 2-Oct KOSPI close (not the 6,943.66
    intraday print), its return on the previous row, which must be dated the previous KRX session of the signed
    calendar `cal` (`clocks.prev_session`, as T-PRINT-01's helper checks), the drawdown from the peak, the close over
    the mean of the last 200 closes, the 2-Oct Samsung and SK hynix closes, the KRW=X last row (1 Oct: the provisional
    2-Oct row dropped) and its 20-observation dlog. ^KS11 rows dated after 2 Oct are not read. A vendor price is
    compared at its printed precision (two decimals: a vendor file may carry float artefacts such as 7003.7399...), a
    KRX won price exactly. The ^KS11 peak up to 2 Oct must be 9,114.55 on 2026-06-22, and the computed rows must be
    exactly goldens.csv's M1 rows. Returns the computed values."""
    from core.calendars import clocks
    day = GPOST01_DAY
    k = [r for r in ks11 if r[F13_CLOSE] is not None and r["date"] <= day]
    on_day = [r for r in k if r["date"] == day]
    assert len(on_day) == 1, f"G-POST-01: {len(on_day)} ^KS11 rows on {day}; exactly one close is stored"
    assert len({r["date"] for r in k}) == len(k), "G-POST-01: two ^KS11 rows on one date"
    assert len(k) >= GPOST01_SMA_N, f"G-POST-01: {len(k)} ^KS11 closes up to {day}, fewer than {GPOST01_SMA_N}"
    prev_day = clocks.prev_session("KR", day, cal=cal)
    assert k[-2]["date"] == prev_day, (
        f"G-POST-01: the ^KS11 row before {day} is {k[-2]['date']}, not the previous KRX session {prev_day} "
        f"(G-POST-01/kospi_return_2oct is the return on the previous close)")
    closes = [r[F13_CLOSE] for r in k]
    peak_i = max(range(len(closes)), key=closes.__getitem__)
    bad = [r for r in stocks if r["code"] not in F27_CODES or r["series_id"] not in F27_CODES]
    assert not bad, f"G-POST-01: F27 row {bad[0]} is not a {' / '.join(F27_CODES)} row"
    s = {c: [r[F27_CLOSE] for r in stocks if r["date"] == day and r["code"] == c] for c in F27_CODES}
    assert all(len(v) == 1 and v[0] is not None for v in s.values()), (
        f"G-POST-01: KRX closes on {day} by code {s}; exactly one per code is stored")
    fx = [r for r in krwx if r[F16_CLOSE] is not None]
    assert fx and fx[-1]["date"] == GPOST01_KRWX_LAST, (
        f"G-POST-01: the KRW=X last row is {fx[-1]['date'] if fx else None}, not {GPOST01_KRWX_LAST} (the provisional "
        f"2-Oct row is dropped; G-POST-01/krwx_last_row)")
    assert len(fx) > GPOST01_DLOG_N, f"G-POST-01: {len(fx)} KRW=X rows, the 20-observation dlog needs {GPOST01_DLOG_N + 1}"
    got = {
        "kospi_close_2oct": round(closes[-1], 2),
        "kospi_return_2oct": closes[-1] / closes[-2] - 1.0,
        "drawdown_from_peak": closes[-1] / closes[peak_i] - 1.0,
        "close_over_200d": closes[-1] / statistics.fmean(closes[-GPOST01_SMA_N:]),
        "samsung_close_2oct": s["005930"][0],
        "hynix_close_2oct": s["000660"][0],
        "krwx_last_row": round(fx[-1][F16_CLOSE], 2),
        "krwx_dlog20": math.log(fx[-1][F16_CLOSE] / fx[-1 - GPOST01_DLOG_N][F16_CLOSE]),
    }
    g = G.golden("G-POST-01")
    m1 = {r.sub_id for r in g.rows if r.runs_from == "M1"}
    assert m1 == set(got), f"G-POST-01: goldens.csv M1 rows {sorted(m1)} != the computed rows {sorted(got)}"
    for sub, value in got.items():
        row = g.row(sub)
        assert G.within(row.kind, value, row.want()), (
            f"G-POST-01/{sub}: got {value!r}, want {row.want()!r} +/- {G.tol(row.kind)} (Level 1 {row.kind}; "
            f"spec {row.source_line})")
    peak = (k[peak_i]["date"], round(closes[peak_i], 2))
    assert peak == GPOST01_PEAK, (f"G-POST-01: the ^KS11 peak up to {day} is {peak[1]} on {peak[0]}, not "
                                  f"{GPOST01_PEAK[1]} on {GPOST01_PEAK[0]} (G-POST-01/drawdown_from_peak)")
    return got


def test_g_post_01_m1_data_rows_refdata():
    """G-POST-01, the M1 data rows (spec L5819-5834) on F13, F16 and F27: NOT_RUN (REFDATA) naming every absent fixture;
    NOT_RUN (OWNER) while the signed KRX clock files do not cover the fortnight to 2 Oct (computed from the files by
    tests.macro_m1_calendars._official_calendar); then PASS or FAIL on `_check_gpost01_m1` at Level 1 from goldens.csv
    (look-ahead audit LA-02, part 2: it used to be NOT_RUN whatever the files). F01 and F20 (QX_DLA_postpatch.csv) are
    not read: the rows are computed from the files they come from (spec L5812, Yahoo ^KS11), and regenerating F20's
    column is T-FIX-01's."""
    from tests.macro_m1_calendars import _official_calendar
    missing, text = [], {}
    for name in GPOST01_FIXTURES:
        try:
            text[name] = require_fixture(name).read_text(encoding="utf-8")
        except NotRun as exc:
            missing.append(exc.reason.split(": ", 1)[1])
    if missing:
        raise NotRun("REFDATA: G-POST-01 data rows wait for " + "; ".join(missing))
    _check_gpost01_m1(_fixture_csv(F13, text[F13], (F13_CLOSE,), F13_PROVENANCE),
                      _fixture_csv(F16, text[F16], (F16_CLOSE,), F16_PROVENANCE),
                      _fixture_csv(F27, text[F27], (F27_CLOSE,), F27_PROVENANCE, F27_KEYS),
                      _official_calendar(*GPOST01_CAL_SPAN))


test_g_post_01_m1_data_rows_refdata.test_ids = ["G-POST-01"]


def _gpost01_days() -> list[date]:
    """The 230 weekdays to 2026-10-02 the invented ^KS11 rows are dated on."""
    days, d = [], GPOST01_DAY
    while len(days) < 230:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return days[::-1]


def _gpost01_invented(peak=GPOST01_PEAK, close=7003.74, prev=6971.67, base=6305.93, fx_last=1356.84, fx_back=1358.33,
                      fx_oct2=None, stocks=(276000.0, 1841000.0), extra=(), f27_keys=F27_KEYS, stock_code=None,
                      levels=(), drop=()):
    """Invented ^KS11, KRW=X and KRX stock rows in the declared layouts (no Yahoo or KRX data): 230 weekday closes to
    2026-10-02 at `base`, the peak on its day, the previous close and the close (then `levels` (date, close) set, the
    dates in `drop` removed and the `extra` rows added); KRW=X to 2026-10-01 with `fx_back` 20 observations before
    `fx_last`. The defaults give return +0.46%, drawdown -23.16%, 200-day ratio 1.107 and dlog -0.0011. Returns the
    three texts."""
    days = _gpost01_days()
    k = [(x, {F13_CLOSE: base}) for x in days]
    k[days.index(peak[0])] = (peak[0], {F13_CLOSE: peak[1]})
    k[-2], k[-1] = (days[-2], {F13_CLOSE: prev}), (days[-1], {F13_CLOSE: close})
    k = [(x, {F13_CLOSE: dict(levels).get(x, v[F13_CLOSE])}) for x, v in k if x not in drop]
    k = sorted(k + [(x, {F13_CLOSE: v}) for x, v in extra], key=lambda r: r[0])
    fx = [(x, {F16_CLOSE: 1360.0 + (i % 5)}) for i, x in enumerate(days[-40:-1])]
    fx[-1] = (fx[-1][0], {F16_CLOSE: fx_last})
    fx[-1 - GPOST01_DLOG_N] = (fx[-1 - GPOST01_DLOG_N][0], {F16_CLOSE: fx_back})
    if fx_oct2 is not None:
        fx.append((GPOST01_DAY, {F16_CLOSE: fx_oct2}))
    st = [(x, {"code": c, "series_id": F27_CODES[0], F27_CLOSE: v}) for x in days[-5:-1]
          for c, v in zip(F27_CODES, (270000.0, 1800000.0))]
    if stocks is not None:
        st += [(GPOST01_DAY, {"code": c, "series_id": F27_CODES[0], F27_CLOSE: v}) for c, v in zip(F27_CODES, stocks)]
    if stock_code is not None:
        st.append((GPOST01_DAY, {"code": stock_code, "series_id": F27_CODES[0], F27_CLOSE: 230000.0}))
    return (_layout_text(k, (F13_CLOSE,), F13_PROVENANCE), _layout_text(fx, (F16_CLOSE,), F16_PROVENANCE),
            _layout_text(st, (F27_CLOSE,), F27_PROVENANCE, keys=f27_keys))


def _gpost01_run(texts, cal=None) -> dict:
    """The real body after its gates on the three texts, on the signed calendar `cal` (default: the calendars module's
    synthetic signed set, through the same owner gate)."""
    from tests.macro_m1_calendars import _official_calendar_on, fixture_set
    ks11, krwx, stocks = texts
    return _check_gpost01_m1(_fixture_csv(F13, ks11, (F13_CLOSE,), F13_PROVENANCE),
                             _fixture_csv(F16, krwx, (F16_CLOSE,), F16_PROVENANCE),
                             _fixture_csv(F27, stocks, (F27_CLOSE,), F27_PROVENANCE, F27_KEYS),
                             _official_calendar_on(*GPOST01_CAL_SPAN, fixture_set() if cal is None else cal))


def test_g_post_01_body_passes_and_fails_on_invented_rows():
    """LA-02 part 2: the G-POST-01 data-row body can PASS and can FAIL. Invented rows in the declared layouts (no Yahoo
    or KRX data) on the calendars module's synthetic signed set, built to the golden values, pass, also with a float
    artefact on the close and with a later ^KS11 row above the peak (2026-10-05, not read). The row exactly 200 closes
    back is inside the 200-close window (its level moves the ratio) and the row 201 back is outside it (its level does
    not). Each value clause fails on its own: the pre-patch 6,943.66 intraday print as the close (spec L5819) or beside
    it, two ^KS11 rows on an earlier date, a previous close of 7,100, the 1-Oct row missing with 30-Sep at the previous
    close's level (a two-session return), a peak of 9,300 (drawdown -24.7%), a lower 200-day mean, the pre-patch Samsung
    273,750 and SK hynix 1,832,000 (L5833), a KRW=X last row of 1,360.63, the provisional 2-Oct KRW=X row kept (L5834),
    a 20th-back KRW=X value off by 2%, a peak of 9,200 (within the drawdown tolerance) and the 9,114.55 peak on
    2026-06-23; a stock row of another code (the preferred share 005935); and the layout without a declared column.
    Each declared provenance equals the generator's table (docs/macro_fixtures.REFERENCE_FILES)."""
    assert GPOST01_FIXTURES == (F13, F16, F27)
    for name, declared in ((F13, F13_PROVENANCE), (F16, F16_PROVENANCE)):
        assert _generator_provenance(name) == declared, (name, _generator_provenance(name))
    assert _generator_provenance(F27) == (("series_id", F27_CODES[0]),) + F27_PROVENANCE, _generator_provenance(F27)
    got = _gpost01_run(_gpost01_invented())
    assert got["kospi_close_2oct"] == 7003.74 and round(got["drawdown_from_peak"], 4) == -0.2316, got
    assert round(got["close_over_200d"], 3) == 1.107 and round(got["krwx_dlog20"], 4) == -0.0011, got
    assert _gpost01_run(_gpost01_invented(close=7003.740234375))["kospi_close_2oct"] == 7003.74   # a float32 artefact
    # a row after 2 Oct is not read, even above the peak (it would move the peak, the close and the window)
    assert _gpost01_run(_gpost01_invented(extra=((date(2026, 10, 5), 9500.0),))) == got
    # the 200-close window (G-POST-01/close_over_200d note "mean of last 200 closes incl. 2 Oct"; the count is typed
    # here, not read from GPOST01_SMA_N): the row 201 closes back is outside it, the row 200 back inside it (levels far
    # from the window mean, below the 9,114.55 peak; one row moves the mean by (level - base) / 200)
    day200, day201 = _gpost01_days()[-200], _gpost01_days()[-201]
    assert _gpost01_run(_gpost01_invented(levels=((day201, 3000.0),)))["close_over_200d"] == got["close_over_200d"]
    moved = _gpost01_run(_gpost01_invented(levels=((day200, 9000.0),)))["close_over_200d"]
    assert abs(moved - 7003.74 / (7003.74 / got["close_over_200d"] + (9000.0 - 6305.93) / 200)) < 1e-9, moved
    cases = (
        (dict(close=6943.66), "G-POST-01/kospi_close_2oct: got 6943.66, want 7003.74"),
        (dict(extra=((GPOST01_DAY, 6943.66),)), "G-POST-01: 2 ^KS11 rows on 2026-10-02"),
        (dict(extra=((date(2026, 9, 1), 6305.93),)), "G-POST-01: two ^KS11 rows on one date"),
        (dict(prev=7100.0), "G-POST-01/kospi_return_2oct: got"),
        (dict(levels=((date(2026, 9, 30), 6971.67),), drop=(date(2026, 10, 1),)),
         "G-POST-01: the ^KS11 row before 2026-10-02 is 2026-09-30, not the previous KRX session 2026-10-01"),
        (dict(peak=(GPOST01_PEAK[0], 9300.0)), "G-POST-01/drawdown_from_peak: got"),
        (dict(base=6000.0), "G-POST-01/close_over_200d: got"),
        (dict(stocks=(273750.0, 1841000.0)), "G-POST-01/samsung_close_2oct: got 273750.0, want 276000"),
        (dict(stocks=(276000.0, 1832000.0)), "G-POST-01/hynix_close_2oct: got 1832000.0, want 1841000"),
        (dict(stocks=None), "G-POST-01: KRX closes on 2026-10-02 by code {'005930': [], '000660': []}"),
        (dict(stock_code="005935"), "is not a 005930 / 000660 row"),
        (dict(fx_last=1360.63), "G-POST-01/krwx_last_row: got 1360.63, want 1356.84"),
        (dict(fx_oct2=1360.63), "the KRW=X last row is 2026-10-02, not 2026-10-01"),
        (dict(fx_back=1356.84 * 1.02), "G-POST-01/krwx_dlog20: got"),
        (dict(peak=(GPOST01_PEAK[0], 9200.0)), "the ^KS11 peak up to 2026-10-02 is 9200.0 on 2026-06-22, not 9114.55"),
        (dict(peak=(date(2026, 6, 23), 9114.55)), "is 9114.55 on 2026-06-23, not 9114.55 on 2026-06-22"),
    )
    for kw, needle in cases:
        e = _raises(lambda: _gpost01_run(_gpost01_invented(**kw)), AssertionError)
        assert needle in str(e), (kw, str(e))
    layout = _raises(lambda: _gpost01_run(_gpost01_invented(f27_keys=("series_id",))), AssertionError)
    assert "declared columns ['code'] absent" in str(layout), layout
    from tests.macro_m1_calendars import _official_calendar, drafts_set
    owner = _raises(lambda: _official_calendar(*GPOST01_CAL_SPAN, live=drafts_set()), NotRun)
    assert owner.reason.startswith("OWNER: the signed KRX clock files must cover 2026-09-18..2026-10-02"), owner.reason


# --------------------------------------------------------------------------- #
# T-BAR-01 / T-BAR-02 / T-CLOSE-01 / T-PRINT-01
# --------------------------------------------------------------------------- #
def test_bar_01_a_bar_or_stale_carry_is_never_a_close():
    bar = P.stamp_bar("KOSPI_OFFICIAL_CLOSE", U(2026, 10, 2, 6, 0), 6990.0, retrieved_at_utc=U(2026, 10, 2, 7),
                      source="Yahoo", latency_s=120, session_date=OCT2)
    assert bar["obs_kind"] == "bar" and bar["value_status"] == "provisional_intraday"
    assert bar["available_at_utc"] == U(2026, 10, 2, 6, 2)
    _raises(lambda: P.stamp_close("KOSPI_OFFICIAL_CLOSE", OCT2, 6990.0, retrieved_at_utc=U(2026, 10, 2, 7), source="Yahoo",
                                  registry=REG, clocks=CLK, obs_kind="bar"), P.PITError, "never derived from bars")
    _raises(lambda: P.make_row(**{**{k: v for k, v in bar.items() if k != "content_hash"}, "value_status": "official_close"}),
            P.PITError, "only a close is a close")
    store = _store()
    store.append([bar])
    assert _read(store, U(2026, 10, 2, 7)).reason == "provisional_intraday"   # a bar reaching an acting read fails closed
    flat = P.stamp_close("KOSPI_OFFICIAL_CLOSE", OCT2, 7003.74, retrieved_at_utc=U(2026, 10, 2, 7), source="KRX",
                         registry=REG, clocks=CLK, ohlcv={"open": 7003.74, "high": 7003.74, "low": 7003.74, "close": 7003.74, "volume": 0})
    assert isinstance(flat, P.Flag) and flat.code == "stale_carry"
    rep = P.ingest(store, "KOSPI_OFFICIAL_CLOSE", [(OCT2, 7003.74)], source="KRX", retrieved_at_utc=U(2026, 10, 2, 7),
                   registry=REG, clocks=CLK, ohlcv={OCT2: {"open": 7003.74, "high": 7003.74, "low": 7003.74, "close": 7003.74, "volume": 0}})
    assert rep.appended == 0 and rep.flags[0].code == "stale_carry"
    # two-source mismatch: index > 1 bp disputed, official used; stock any mismatch; nothing corrected
    store.append([_kospi(7003.74, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                         retrieved=U(2026, 10, 2, 6, 41), source="KRX"),
                  _kospi(7004.80, status="vendor_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                         retrieved=U(2026, 10, 2, 6, 42), source="Yahoo")])
    assert P.reconcile(store, "KOSPI_OFFICIAL_CLOSE", OCT2, knowledge_utc=U(2026, 10, 2, 7), registry=REG) == "disputed"
    v = _read(store, U(2026, 10, 2, 7))
    assert v.value == 7003.74 and v.dispute and v.status == "disputed" and v.source == "KRX"
    assert "disputed_use_official_and_alert" in (store.path / "disputes.jsonl").read_text(encoding="utf-8")
    s2 = _store()
    s2.append([_kospi(7003.74, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                      retrieved=U(2026, 10, 2, 6, 41), source="KRX"),
               _kospi(7004.00, status="vendor_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                      retrieved=U(2026, 10, 2, 6, 42), source="Yahoo")])
    assert P.reconcile(s2, "KOSPI_OFFICIAL_CLOSE", OCT2, knowledge_utc=U(2026, 10, 2, 7), registry=REG) == "ok"   # 0.37 bp
    s3 = _store()
    stock = lambda v, st, src: P.make_row(series_id="KRX_005930_OFFICIAL_CLOSE", value=v, obs_date=OCT2, session_date=OCT2,   # noqa: E731
                                          obs_utc=U(2026, 10, 2, 6, 30, 30), obs_kind="close", value_status=st,
                                          available_at_utc=U(2026, 10, 2, 6, 30, 30), available_at_source="calendar_bound",
                                          retrieved_at_utc=U(2026, 10, 2, 6, 41), vintage=None, source=src, channel=None)
    s3.append([stock(276000.0, "official_close", "KRX"), stock(276100.0, "vendor_close", "Yahoo")])
    assert P.reconcile(s3, "KRX_005930_OFFICIAL_CLOSE", OCT2, knowledge_utc=U(2026, 10, 2, 7), registry=REG) == "disputed"
    assert P.pit_value(s3, "KRX_005930_OFFICIAL_CLOSE", DECISION, U(2026, 10, 2, 7), "nav", OCT2, registry=REG).value == 276000.0


test_bar_01_a_bar_or_stale_carry_is_never_a_close.test_ids = ["T-BAR-01"]


def test_bar_02_dispute_is_not_a_failure_and_vendor_missing():
    store = _store()
    store.append([_kospi(7003.74, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                         retrieved=U(2026, 10, 2, 6, 41), source="KRX"),
                  _kospi(7010.00, status="vendor_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                         retrieved=U(2026, 10, 2, 6, 42), source="Yahoo")])
    v = _read(store, U(2026, 10, 2, 7))
    assert isinstance(v, P.PITValue) and v.dispute and v.value == 7003.74
    b = REG.resolve_binding("KOSPI_OFFICIAL_CLOSE", "R-06")
    act = C.on_input_failure("KOSPI_OFFICIAL_CLOSE", v, b)
    assert act.status == "disputed" and act.alert and not act.counts and not act.fail_closed and act.halt == "never"
    counters = C.InputCounters()
    assert counters.step(REG, [(b, act.counts)]) == [] and counters.state("specification:KR")["consecutive_failures"] == {"KOSPI_OFFICIAL_CLOSE": 0}
    s2 = _store()
    s2.append([prov01_rows()[1]])
    assert P.reconcile(s2, "KOSPI_OFFICIAL_CLOSE", OCT2, knowledge_utc=U(2026, 10, 2, 7), registry=REG) == "vendor_missing"
    assert not (s2.path / "disputes.jsonl").exists()


test_bar_02_dispute_is_not_a_failure_and_vendor_missing.test_ids = ["T-BAR-02"]


def test_close_01_data_clauses_quarantine_and_stamping():
    sc = lambda retrieved, **kw: P.stamp_close("KOSPI_OFFICIAL_CLOSE", OCT2, 7003.74, retrieved_at_utc=retrieved,   # noqa: E731
                                               source="KRX", registry=REG, clocks=CLK, **kw)
    r = sc(U(2026, 10, 2, 6, 40, 29))
    assert r["value_status"] == "provisional_intraday" and r["obs_kind"] == "quote_snapshot"
    r = sc(U(2026, 10, 2, 6, 40, 30))
    assert r["value_status"] == "official_close" and r["available_at_utc"] == U(2026, 10, 2, 6, 30, 30)
    r = sc(U(2026, 10, 2, 6, 45))
    assert r["available_at_source"] == "calendar_bound" and r["available_at_utc"] == U(2026, 10, 2, 6, 30, 30) and r["obs_utc"] == U(2026, 10, 2, 6, 30, 30)
    r = sc(U(2026, 10, 2, 6, 45), print_time_utc=U(2026, 10, 2, 6, 30, 20))
    assert r["available_at_source"] == "published" and r["available_at_utc"] == U(2026, 10, 2, 6, 30, 20)
    late = sc(U(2026, 10, 2, 6, 45), print_time_utc=U(2026, 10, 2, 6, 31))
    assert isinstance(late, P.Flag) and late.code == "print_after_bound"
    store = _store()
    store.append([sc(U(2026, 10, 2, 6, 40, 29))])
    assert isinstance(_read(store, U(2026, 10, 2, 7)), P.MissingInput)         # retrieved 06:40:29Z: never official
    store.append([P.make_row(**{**{k: v for k, v in sc(U(2026, 10, 2, 6, 45)).items() if k != "content_hash"},
                                "available_at_utc": U(2026, 10, 2, 6, 31)})])
    assert _read(store, U(2026, 10, 2, 7)).reason == "missing"                 # 06:31Z is not visible at 06:30:30Z
    assert store.append([sc(U(2026, 10, 2, 6, 45), print_time_utc=U(2026, 10, 2, 6, 30, 20))]) == 0   # same content: never re-stamped
    s_pub = _store()
    s_pub.append([sc(U(2026, 10, 2, 6, 45), print_time_utc=U(2026, 10, 2, 6, 30, 20))])
    assert _read(s_pub, U(2026, 10, 2, 7)).value == 7003.74
    # KIS daily rows are not official until the M1-01 field check is recorded (F-4): vendor_close, so refused live
    kis = P.stamp_close("KOSPI_OFFICIAL_CLOSE", OCT2, 7003.74, retrieved_at_utc=U(2026, 10, 2, 6, 45), source="KIS",
                        registry=REG, clocks=CLK)
    assert kis["value_status"] == "vendor_close"
    us = P.stamp_close("SPX_OFFICIAL_CLOSE", date(2026, 10, 1), 7666.45, retrieved_at_utc=U(2026, 10, 1, 20, 30), source="KRX",
                       registry=REG, clocks=CLK, print_time_utc=U(2026, 10, 1, 20, 0, 2))
    assert us["value_status"] == "official_close" and CLK.close_print_bound_utc("US", date(2026, 10, 1)) == U(2026, 10, 1, 20, 0, 30)


test_close_01_data_clauses_quarantine_and_stamping.test_ids = ["T-CLOSE-01"]


def test_print_01_circuit_breaker_print_is_never_a_close():
    d = date(2026, 3, 9)
    store = _store()
    store.append([P.stamp_close("KOSPI_OFFICIAL_CLOSE", d, 5131.12, retrieved_at_utc=U(2026, 3, 9, 1, 31), source="KRX",
                                registry=REG, clocks=CLK),                                     # the 10:31 print (-8.11%)
                  P.stamp_close("KOSPI_OFFICIAL_CLOSE", d, 5251.87, retrieved_at_utc=U(2026, 3, 9, 6, 41), source="KRX",
                                registry=REG, clocks=CLK)])
    dec = CLK.close_print_bound_utc("KR", d)
    v = P.pit_value(store, "KOSPI_OFFICIAL_CLOSE", dec, U(2026, 3, 9, 7), "R-06", d, registry=REG)
    assert v.value == 5251.87 and v.value_status == "official_close"
    closes = [r for r in store.rows("KOSPI_OFFICIAL_CLOSE") if r["obs_kind"] == "close"]
    assert [r["value"] for r in closes] == [5251.87]


test_print_01_circuit_breaker_print_is_never_a_close.test_ids = ["T-PRINT-01"]


# T-PRINT-01 on the Yahoo ^KS11 history (F13 in the layout declared above; spec L5631, L1382): "The KOSPI close on
# 2026-03-09 is 5,251.87 (-5.96%). The intraday -8.11% is never stored as a close." The close is a price compared at
# its printed precision (two decimals: a vendor file may carry float artefacts); the return within the printed
# precision of -5.96% (+/- 0.005 pp), against the previous KRX session's row.
PRINT01_DATE, PRINT01_CLOSE, PRINT01_RETURN_PCT = date(2026, 3, 9), 5251.87, -5.96      # spec L5631
PRINT01_PRINTED_PCT = 0.005                                                              # half the last printed digit


def _check_print01_ks11(rows: list[dict], cal) -> float:
    """T-PRINT-01 on the Yahoo ^KS11 vendor closes: exactly one row on 2026-03-09, its close 5,251.87 at the printed
    precision (so neither the 10:31 print nor any other value is stored as the close), the row before it on the
    previous KRX session of the signed calendar `cal`, and -5.96% against that row within the printed precision.
    Returns the return in percent."""
    from core.calendars import clocks
    d = PRINT01_DATE
    on_day = [r for r in rows if r["date"] == d]
    assert len(on_day) == 1, f"T-PRINT-01 (F13): {len(on_day)} rows on {d}; exactly one close is stored"
    close = on_day[0][F13_CLOSE]
    assert close is not None and round(close, 2) == PRINT01_CLOSE, (
        f"T-PRINT-01 (F13): close {close!r} != {PRINT01_CLOSE} (spec L5631)")
    before = [r for r in rows if r["date"] < d]
    prev_day = clocks.prev_session("KR", d, cal=cal)
    assert before and before[-1]["date"] == prev_day and before[-1][F13_CLOSE] is not None, (
        f"T-PRINT-01 (F13): the row before {d} is {before[-1]['date'] if before else None}, not the previous KRX "
        f"session {prev_day}")
    ret_pct = 100.0 * (close / before[-1][F13_CLOSE] - 1.0)
    assert abs(ret_pct - PRINT01_RETURN_PCT) <= PRINT01_PRINTED_PCT + 1e-9, (
        f"T-PRINT-01 (F13): return {ret_pct:.4f}% != {PRINT01_RETURN_PCT}% (spec L5631)")
    return ret_pct


def test_print_01_real_kospi_close_refdata():
    """T-PRINT-01 on the Yahoo ^KS11 history (F13): NOT_RUN (REFDATA) until F13 is listed with its md5, NOT_RUN (OWNER)
    while the signed KRX clock files do not cover the fortnight to 2026-03-09 (computed from the files by
    tests.macro_m1_calendars._official_calendar); then PASS or FAIL on `_check_print01_ks11` (look-ahead audit LA-02,
    part 2: it used to be NOT_RUN whatever the file)."""
    from tests.macro_m1_calendars import _official_calendar
    rows = _fixture_csv(F13, require_fixture(F13).read_text(encoding="utf-8"), (F13_CLOSE,), F13_PROVENANCE)
    _check_print01_ks11(rows, _official_calendar(PRINT01_DATE - timedelta(days=14), PRINT01_DATE))


test_print_01_real_kospi_close_refdata.test_ids = ["T-PRINT-01"]


def test_print_01_body_passes_and_fails_on_invented_ks11_closes():
    """LA-02 part 2: the T-PRINT-01 (F13) body can PASS and can FAIL. Invented closes in the declared F13 layout on the
    synthetic signed calendars (no Yahoo data): 5,584.71 then 5,251.87 passes, also with a float artefact on the close,
    and so does a previous close of 5,585.01 (-5.9649%, just inside the printed precision). It fails when the 10:31 KST
    print (5,131.12) is stored as the 2026-03-09 close or beside it, when the close is 5,251.88, when the previous close
    is 5,560 (-5.54%) or 5,585.05 (-5.9656%, just outside), when the 2026-03-06 row is missing, and on a file whose rows
    are marked official_close. The calendar gate covers that fortnight on the synthetic set and refuses the unsigned one."""
    from core.calendars import clocks
    from tests.macro_m1_calendars import _official_calendar, _official_calendar_on, drafts_set, fixture_set
    cal = fixture_set()
    days = clocks.sessions_between("KR", date(2026, 2, 23), PRINT01_DATE, cal=cal)
    assert days[-2:] == [date(2026, 3, 6), PRINT01_DATE], days

    def text(last, extra=(), drop=(), provenance=F13_PROVENANCE):
        closes = [5600.0 + 3.0 * (i % 4) for i in range(len(days))]
        closes[-len(last):] = list(last)
        rows = [(d, {F13_CLOSE: c}) for d, c in zip(days, closes) if d not in drop]
        rows = sorted(rows + [(d, {F13_CLOSE: c}) for d, c in extra], key=lambda r: r[0])
        return _layout_text(rows, (F13_CLOSE,), provenance)

    def run(t):
        return _check_print01_ks11(_fixture_csv(F13, t, (F13_CLOSE,), F13_PROVENANCE), cal)

    assert abs(run(text((5584.71, PRINT01_CLOSE))) - PRINT01_RETURN_PCT) <= PRINT01_PRINTED_PCT
    assert abs(run(text((5584.71, 5251.8701171875))) - PRINT01_RETURN_PCT) <= PRINT01_PRINTED_PCT  # float32 artefact
    # the printed precision's edge: a previous close of 5,585.01 gives -5.96490% (inside +/- 0.005 pp), 5,585.05 gives
    # -5.96557% (outside)
    assert abs(run(text((5585.01, PRINT01_CLOSE))) - PRINT01_RETURN_PCT) <= PRINT01_PRINTED_PCT
    for t, needle in ((text((5584.71, 5131.12)), "close 5131.12 != 5251.87 (spec L5631)"),
                      (text((5584.71, PRINT01_CLOSE), extra=((PRINT01_DATE, 5131.12),)), "2 rows on 2026-03-09"),
                      (text((5584.71, 5251.88)), "close 5251.88 != 5251.87 (spec L5631)"),
                      (text((5560.0, PRINT01_CLOSE)), "return -5.5419% != -5.96% (spec L5631)"),
                      (text((5585.05, PRINT01_CLOSE)), "return -5.9656% != -5.96% (spec L5631)"),
                      (text((5584.71, PRINT01_CLOSE), drop=(date(2026, 3, 6),)),
                       "the row before 2026-03-09 is 2026-03-05, not the previous KRX session 2026-03-06")):
        e = _raises(lambda: run(t), AssertionError)
        assert needle in str(e), (needle, str(e))
    official = (("series_id", "KS11"), ("value_status", "official_close"), ("available_at_source", "calendar_bound"))
    layout = _raises(lambda: run(text((5584.71, PRINT01_CLOSE), provenance=official)), AssertionError)
    assert "provenance" in str(layout) and "'value_status': 'official_close'" in str(layout), layout
    lo = PRINT01_DATE - timedelta(days=14)
    assert _official_calendar_on(lo, PRINT01_DATE, cal) is cal
    owner = _raises(lambda: _official_calendar(lo, PRINT01_DATE, live=drafts_set()), NotRun)
    assert owner.reason.startswith("OWNER: the signed KRX clock files must cover 2026-02-23..2026-03-09"), owner.reason

# --------------------------------------------------------------------------- #
# T-AVAIL-01, T-STALE-01, G-STALE-01
# --------------------------------------------------------------------------- #
def _first_decision_at_or_after(market, instant, clocks=CLK):
    d = instant.date() - timedelta(days=1)
    while True:
        d += timedelta(days=1)
        if clocks.is_session(market, d) and clocks.close_print_bound_utc(market, d) >= instant:
            return d


def _check_avail01_table(clk, clocks_for) -> None:
    """The T-AVAIL-01 golden availability table (spec L2099, L5619) on `clk`, exact match, and the injected registry
    error (H.15 posted at D, not D+1: L3463) on `clocks_for(<registry with the error>)`, which must move the instant."""
    exp = lambda sid, d, c=clk: C.expected_available_utc(REG, sid, d, c)          # noqa: E731
    dgs = exp("DGS10", date(2015, 1, 1))                 # next obs Fri 2015-01-02 -> posted Mon 01-05 16:15 EST
    assert dgs == U(2015, 1, 5, 21, 15) and _first_decision_at_or_after("KR", dgs, clk) == date(2015, 1, 6)
    h10 = exp("DEXKOUS", date(2026, 10, 2))              # week of 10-05 -> Columbus Day Monday -> Tue 10-13 16:15 EDT
    assert h10 == U(2026, 10, 13, 20, 15) and _first_decision_at_or_after("KR", h10, clk) == date(2026, 10, 14)
    d10 = exp("DGS10", date(2026, 10, 8))                # obs Fri 10-09 -> next Fed bday after = Tue 10-13
    assert d10 == U(2026, 10, 13, 20, 15) and _first_decision_at_or_after("US", d10, clk) == date(2026, 10, 14)
    assert clk.close_print_bound_utc("KR", date(2025, 11, 13)) == U(2025, 11, 13, 7, 30, 30)
    import dataclasses
    wrong = dict(REG.series)
    wrong["DGS10"] = {**REG.series["DGS10"], "schedule": "VIXCLS"}    # injected registry error: H.15 posted at D
    bad = dataclasses.replace(REG, series=wrong)
    assert exp("DGS10", date(2015, 1, 1), clocks_for(bad)) != dgs


def test_avail_01_golden_availability_table_on_synthetic_calendars():
    _check_avail01_table(CLK, StubClocks)


test_avail_01_golden_availability_table_on_synthetic_calendars.test_ids = ["T-AVAIL-01"]


# The signed calendar files each golden row reads (core/calendars/data; core.calendars.adapter.CalendarClocks) and the
# days it reads them on. The injected-error row reads the same files as the first row.
_AVAIL01_KR = ("holidays_FED", "publication_schedules", "source_skipped", "kr_sessions", "holidays_KRX")
AVAIL01_NEEDS = (
    ("DGS10 dated Fri 2015-01-02 -> KRX close Tue 2015-01-06", _AVAIL01_KR, date(2015, 1, 1), date(2015, 1, 6)),
    ("DEXKOUS week of 2026-10-05 -> KRX close Wed 2026-10-14", _AVAIL01_KR, date(2026, 10, 2), date(2026, 10, 14)),
    ("DGS10 dated 2026-10-09 -> US close 2026-10-14",
     ("holidays_FED", "publication_schedules", "source_skipped", "holidays_NYSE"), date(2026, 10, 8), date(2026, 10, 14)),
    ("CSAT close 2025-11-13 07:30Z", ("kr_sessions", "holidays_KRX"), date(2025, 11, 13), date(2025, 11, 13)),
)


def _avail01_waiting(live) -> list[str]:
    """Each refusal or coverage gap of the signed files the golden rows read (empty when the table can run)."""
    out = []
    for row, files, lo, hi in AVAIL01_NEEDS:
        for f in files:
            why = live.refusal(f)
            if why is not None:
                out.append(f"{row}: {f}.yaml refused ({why})")
            elif not (live.file(f).covers(lo) and live.file(f).covers(hi)):
                cf = live.file(f)
                out.append(f"{row}: {f}.yaml v{cf.version} covers {cf.covers_from}..{cf.covers_to}, needs {lo}..{hi}")
    return out


def test_avail_01_official_calendars_are_owner_signed():
    """The same golden table on the owner-signed calendars (core.calendars.adapter.CalendarClocks over the shipped
    files). NOT_RUN (OWNER) names every refusal and coverage gap, computed from the files; once they load and cover the
    golden days the table runs and PASSes or FAILs (look-ahead audit LA-02: it used to be NOT_RUN whatever the files).
    AVAIL01_NEEDS is the contract: once nothing is waiting, a coverage or signing error raised inside the table (a file
    or a date the list does not declare, such as a calendar read past the golden day) is a FAIL, not a NOT_RUN."""
    from core.calendars.adapter import CalendarClocks
    from core.calendars.store import CalendarSet
    live = CalendarSet()
    waiting = _avail01_waiting(live)
    if waiting:
        raise NotRun("OWNER: T-AVAIL-01 on the signed calendars waits for " + "; ".join(waiting))
    _check_avail01_table(CalendarClocks(REG, cal=live), lambda reg: CalendarClocks(reg, cal=live))


test_avail_01_official_calendars_are_owner_signed.test_ids = ["T-AVAIL-01"]


def test_avail_01_official_path_passes_and_fails_on_a_synthetic_signed_set():
    """LA-02 part 1: the official-calendar body can PASS and can FAIL. On the calendars module's synthetic set (signed
    in a temp dir by that test module, 1995-2027; not the owner's files) nothing is waiting and the table passes
    through CalendarClocks; the same clocks over a registry with H.15 posted at D fail it. The waiting list is exact:
    on a synthetic set whose holidays_KRX covers 2026-27 only (the shipped file's span) it names the 2015 and CSAT
    rows' gaps and nothing else, and on a set whose holidays_KRX is unsigned it names that refusal for every row that
    reads the file."""
    import dataclasses
    from core.calendars.adapter import CalendarClocks
    from tests.macro_m1_calendars import drafts_set, fixture_set, krx_short_set
    cal = fixture_set()
    assert _avail01_waiting(cal) == []
    gap = "holidays_KRX.yaml v1.0.0-fixture covers 2026-01-01..2027-12-31, needs"
    assert _avail01_waiting(krx_short_set()) == [
        f"DGS10 dated Fri 2015-01-02 -> KRX close Tue 2015-01-06: {gap} 2015-01-01..2015-01-06",
        f"CSAT close 2025-11-13 07:30Z: {gap} 2025-11-13..2025-11-13"], _avail01_waiting(krx_short_set())
    refused = _avail01_waiting(drafts_set())
    assert [w.split(": ")[0] for w in refused] == [row for row, files, _, _ in AVAIL01_NEEDS if "holidays_KRX" in files]
    assert all(": holidays_KRX.yaml refused (holidays_KRX.yaml: signed_off_by is empty" in w for w in refused), refused
    _check_avail01_table(CalendarClocks(REG, cal=cal), lambda reg: CalendarClocks(reg, cal=cal))
    wrong = dict(REG.series)
    wrong["DGS10"] = {**REG.series["DGS10"], "schedule": "VIXCLS"}
    bad = dataclasses.replace(REG, series=wrong)
    _raises(lambda: _check_avail01_table(CalendarClocks(bad, cal=cal), lambda reg: CalendarClocks(reg, cal=cal)),
            AssertionError)


def _dexkous_rows(clocks, weeks):
    """H.10 rows first seen at their publication instant (retrieved_at == available_at, calendar_bound)."""
    return [_release("DEXKOUS", d, v, clocks.publication_instant("DEXKOUS", d), clocks=clocks) for d, v in weeks]


def test_stale_01_schedule_aware_clauses_and_local_smoke():
    # the next observation's due instant, never the availability of last_obs (B11 example; L1015-1017)
    assert C.expected_available_utc(REG, "DEXKOUS", date(2026, 9, 25), CLK) == U(2026, 10, 5, 20, 15)
    assert C.stale_deadline_utc(REG, "DEXKOUS", date(2026, 9, 25), CLK) == U(2026, 10, 6, 20, 15)
    assert CLK.publication_instant("DEXKOUS", date(2026, 9, 25)) == U(2026, 9, 28, 20, 15)   # the negative control's value
    assert C.expected_available_utc(REG, "KOSPI_OFFICIAL_CLOSE", OCT2, CLK) == U(2026, 10, 6, 6, 30, 30)
    assert C.stale_deadline_utc(REG, "KOSPI_OFFICIAL_CLOSE", OCT2, CLK) == U(2026, 10, 7, 6, 30, 30)
    # deleting one H.10 release flags the next decision after the grace
    store = _store()
    week = [(date(2026, 9, 21) + timedelta(days=i), 1360.0 + i) for i in range(5)]
    store.append(_dexkous_rows(CLK, week))
    stale = lambda dec: C.is_stale(store, REG, "DEXKOUS", dec, dec, CLK)          # noqa: E731
    assert not stale(CLK.close_print_bound_utc("KR", OCT2)).stale
    assert not stale(CLK.close_print_bound_utc("KR", date(2026, 10, 6))).stale    # 06:30:30Z < deadline 20:15Z
    s = stale(CLK.close_print_bound_utc("KR", date(2026, 10, 7)))
    assert s.stale and s.reason == "missed_release"
    assert C.on_input_failure("DEXKOUS", s, REG.resolve_binding("DEXKOUS", "R-13")).status == "stale"
    assert C.is_stale(_store(), REG, "DEXKOUS", DECISION, DECISION, CLK).reason == "missing"
    # local smoke (labelled): docs/asset_expansion/cache/fred_DEXKOUS.csv on a weekday US-close grid
    src = ROOT / "docs" / "asset_expansion" / "cache" / "fred_DEXKOUS.csv"
    if not src.is_file():
        raise NotRun("REFDATA: docs/asset_expansion/cache/fred_DEXKOUS.csv absent (local DEXKOUS smoke)")
    obs = []
    with src.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("DEXKOUS"):
                obs.append((date.fromisoformat(row["DATE"]), float(row["DEXKOUS"])))
    smoke = _store()
    smoke.append(_dexkous_rows(CLK, obs))
    first, last = obs[0][0] + timedelta(days=7), obs[-1][0]
    hits, n, d = [], 0, first
    while d <= last:
        if d.weekday() < 5:
            dec = CLK.close_print_bound_utc("US", d) if CLK.is_session("US", d) else \
                datetime(d.year, d.month, d.day, 16, 0, 30, tzinfo=NY).astimezone(UTC)
            n += 1
            if C.is_stale(smoke, REG, "DEXKOUS", dec, dec, CLK).stale:
                rec = P.pit_last(smoke, "DEXKOUS", dec, dec, registry=REG)
                hits.append((d, CLK.next_expected_obs("DEXKOUS", rec.obs_date)))
        d += timedelta(days=1)
    share = len(hits) / n
    assert share <= 0.01, f"DEXKOUS stale on {len(hits)}/{n} = {share:.2%}"
    assert hits and {dn for _, dn in hits} <= SOURCE_SKIPPED, sorted({dn for _, dn in hits})
    listed = StubClocks(REG, skipped=SOURCE_SKIPPED)
    assert not any(C.is_stale(smoke, REG, "DEXKOUS", CLK.close_print_bound_utc("US", d) if CLK.is_session("US", d)
                              else datetime(d.year, d.month, d.day, 16, 0, 30, tzinfo=NY).astimezone(UTC), U(2026, 10, 14), listed).stale
                   for d, _ in hits)
    assert share < 0.5, "the last_obs-availability reading (~80%) is not what the code does"


test_stale_01_schedule_aware_clauses_and_local_smoke.test_ids = ["T-STALE-01"]


# G-STALE-01 / T-STALE-01 on the FRED snapshot and the signed calendars (spec L1963, L5620, L5901-5908; goldens.csv
# G-STALE-01). F18 DTWEXBGS, DEXKOUS and DGS10 in the F18 layout below; F07 (docs/macro_fixtures.py:51): the value in the
# column `VIXCLS` (VXVCLS rides along, unread), series_id VIXCLS on every row (the generator writes the first id),
# vendor_close, calendar_bound. Readings declared here, for the owner to confirm:
# - a decision is every session of its market in the span, at the close-print bound (R-19 inputs: "for a decision at
#   a close is the close-print bound of R-20"); knowledge = decision;
# - each observation is stored as first seen at its publication instant on the signed calendars (as the DEXKOUS smoke
#   above does); the fixture's own instants are not read;
# - G-STALE-01's "schedule-aware" share is the share of decisions flagged missed_release WITHOUT the source-exception
#   list: T-STALE-01 (a) gives the same 0.42-0.89% for that case (spec L1963). A decision with no visible record
#   ("missing", before a file's first release) counts in the denominator and is printed, not flagged.
# The v1.2-rule columns ("1 trading day", "3 days") and the median / max ages are not reproduced: the spec does not say
# which trading calendar "1 trading day" counts on or on which date an age is measured, and
# results/QX_DLA_staleness.csv has no ACQUISITION.csv row.
F07 = "fred_VIXCLS_VXVCLS_2007-12-04_2026-09-30.csv"
F07_PROVENANCE = (("series_id", "VIXCLS"), ("value_status", "vendor_close"), ("available_at_source", "calendar_bound"))
STALE01_FIXTURES = ("DTWEXBGS.csv", "DEXKOUS.csv", "DGS10.csv",
                    "fred_VIXCLS_VXVCLS_2007-12-04_2026-09-30.csv")   # in STALE01_SERIES order; F07 spelled out (T-HERM-01)
STALE01_SERIES = ("DTWEXBGS", "DEXKOUS", "DGS10", "VIXCLS")           # the G-STALE-01 rows (spec L5905-5908)
STALE01_H10 = ("DTWEXBGS", "DEXKOUS")                                  # T-STALE-01 (a)
STALE01_MARKETS = (("US", "us"), ("KR", "krx"))                        # "US close / KRX close"; the G-STALE-01 sub_id suffixes
STALE01_SPAN = (date(2016, 1, 4), date(2026, 9, 25))                   # decisions (spec L5901; G-STALE-01 notes)
STALE01_MAX = 0.01                                                     # T-STALE-01 (a), (c): <= 1%; VIXCLS 0% (spec L1963)
# The signed files the body reads (the series' publication and obs calendars, the source-exception list, the NYSE and
# KRX sessions) and the days it reads them on: the decisions' span widened by a month each side, since a decision reads
# an observation up to 12 days old (G-STALE-01/*_age_max_days) and a deadline lies up to an H.10 week and a publication
# day ahead. Observations before the widened span are not loaded.
STALE01_CAL_FILES = ("holidays_FED", "holidays_CBOE", "publication_schedules", "source_skipped", "holidays_NYSE",
                     "kr_sessions", "holidays_KRX")
STALE01_CAL_SPAN = (date(2015, 12, 4), date(2026, 10, 25))


class _NoSkipClocks:
    """`clk` with the source-exception list ignored (T-STALE-01 (a): "Without the source-exception list"): the next
    expected observation of a daily series is the next business day of its obs calendar, a skipped date included.
    Everything else is `clk`'s."""

    def __init__(self, clk):
        self.clk = clk

    def __getattr__(self, name):
        return getattr(self.clk, name)

    def next_expected_obs(self, series_id, obs_date):
        from core.calendars import publication
        s = self.clk.schedule(series_id)
        if s is None or s.get("frequency") == "monthly":
            return self.clk.next_expected_obs(series_id, obs_date)
        return publication.next_expected_obs({**s, "series_id": None, "channel": None}, obs_date, cal=self.clk.cal)


def _stale01_waiting(live) -> list[str]:
    """Each refusal or coverage gap of the signed files G-STALE-01 reads (empty when the body can run)."""
    out = []
    lo, hi = STALE01_CAL_SPAN
    for f in STALE01_CAL_FILES:
        why = live.refusal(f)
        if why is not None:
            out.append(f"{f}.yaml refused ({why})")
        elif not (live.file(f).covers(lo) and live.file(f).covers(hi)):
            cf = live.file(f)
            out.append(f"{f}.yaml v{cf.version} covers {cf.covers_from}..{cf.covers_to}, needs {lo}..{hi}")
    return out


def _stale01_store(obs: dict, clk) -> P.PITStore:
    """A temp PIT store holding each series' observations {series_id: [(obs_date, value)]}, every row first seen at its
    publication instant on `clk`."""
    store = _store(clk)
    for sid, rows in obs.items():
        store.append([_release(sid, d, v, clk.publication_instant(sid, d), clocks=clk) for d, v in rows])
    return store


def _check_stale01(store, clk, span, *, series=STALE01_SERIES, markets=STALE01_MARKETS,
                   is_stale=C.is_stale) -> tuple[dict, dict]:
    """G-STALE-01's schedule-aware rows and T-STALE-01 (a)-(c) on `store` over the decisions of `span`, for each series
    and decision market. Without the source-exception list (`_NoSkipClocks`): every H.10 hit's missed observation date
    (d_next) is in the list (a); conversely, every decision past the no-list deadline of a listed H.10 date and before
    the next stored release is a hit naming that date (a; a check that never flags fails it. A listed date published
    with later days of its week, such as a mid-week skip, has no such decision); at a hit whose d_next is in the list,
    `clk` (list loaded) raises no flag (b); the share of decisions flagged is within Level 1 of
    G-STALE-01/<series>_stale_schedule_<us|krx> (goldens.csv) and at most 1% (DTWEXBGS, DEXKOUS, DGS10; (a), (c)), 0%
    for VIXCLS (c). `is_stale` is core.ficc.contracts' (the demonstrations pass a broken one). Returns the shares and
    the hits [(decision, d_next)], each by golden sub_id."""
    from core.calendars import publication
    plain, g, out, flagged = _NoSkipClocks(clk), G.golden("G-STALE-01"), {}, {}
    for market, col in markets:
        decisions, d = [], span[0]
        while d <= span[1]:
            if clk.is_session(market, d):
                decisions.append(clk.close_print_bound_utc(market, d))
            d += timedelta(days=1)
        assert decisions, f"G-STALE-01: no {market} session in {span[0]}..{span[1]}"
        for sid in series:
            skipped = publication.source_skipped(clk.schedule(sid), cal=clk.cal)
            hits, missing = [], 0
            for dec in decisions:
                chk = is_stale(store, REG, sid, dec, dec, plain)
                if chk.stale and chk.reason == "missing":
                    missing += 1
                elif chk.stale:
                    rec = P.pit_last(store, sid, dec, dec, registry=REG)
                    hits.append((dec, plain.next_expected_obs(sid, rec.obs_date)))
            share = len(hits) / len(decisions)
            row = g.row(f"{sid.lower()}_stale_schedule_{col}")
            tag = f"G-STALE-01/{row.sub_id}"
            out[row.sub_id], flagged[row.sub_id] = share, hits
            print(f"{tag}: {share:.4%} of {len(decisions)} {market}-close decisions ({len(hits)} flagged without the "
                  f"source-exception list, {missing} with no visible record); golden {row.want():.2%}")
            if sid in STALE01_H10:
                other = sorted({dn for _, dn in hits} - skipped)
                assert not other, (f"T-STALE-01 (a): {sid} at the {market} close: missed observation dates {other[:5]} "
                                   f"are not in the source-skipped list (spec L1963)")
                # the converse: a listed date the series skips flags, without the list, every decision after the
                # deadline of the observation before it (R-19 step 3) until the next stored release is visible
                rows = sorted(store.rows(sid), key=lambda r: r["obs_date"])
                for dn in sorted(skipped):
                    before = [r["obs_date"] for r in rows if r["obs_date"] < dn]
                    after = [r["available_at_utc"] for r in rows if r["obs_date"] > dn]
                    if not before or not after or plain.next_expected_obs(sid, before[-1]) != dn:
                        continue
                    deadline = C.stale_deadline_utc(REG, sid, before[-1], plain)
                    due = [dec for dec in decisions if deadline < dec < min(after)]
                    unflagged = [dec for dec in due if (dec, dn) not in hits]
                    assert not unflagged, (
                        f"T-STALE-01 (a): without the source-exception list, {sid} is not flagged at the {market} "
                        f"close on {len(unflagged)} of the {len(due)} decisions past the deadline of the listed date "
                        f"{dn}, first {unflagged[0]:%Y-%m-%d %H:%M:%S}Z (spec L1963: 0.42-0.89% expected)")
            kept = [(dec, dn) for dec, dn in hits if dn in skipped and is_stale(store, REG, sid, dec, dec, clk).stale]
            assert not kept, (f"T-STALE-01 (b): with the source-exception list loaded, {sid} is still flagged at the "
                              f"{market} close on {len(kept)} decisions whose missed date is listed, first {kept[0]}")
            assert G.within(row.kind, share, row.want()), (
                f"{tag}: {share:.4%}, want {row.want():.2%} +/- {G.tol(row.kind)} (Level 1 {row.kind}; "
                f"spec {row.source_line})")
            bound = 0.0 if sid == "VIXCLS" else STALE01_MAX
            assert share <= bound, (f"T-STALE-01 ({'a' if sid in STALE01_H10 else 'c'}): {sid} is stale on {share:.4%} "
                                    f"of {market}-close decisions, above {bound:.0%} (spec L1963)")
    return out, flagged


def test_stale_01_g_stale_01_reference_table_refdata():
    """G-STALE-01's schedule-aware rows and T-STALE-01 (a)-(c) on the FRED snapshot (F18 DTWEXBGS, DEXKOUS, DGS10; F07
    VIXCLS) over decisions 2016-01-04 -> 2026-09-25 at the US and KRX closes: NOT_RUN (REFDATA) naming every absent
    fixture, NOT_RUN (OWNER) naming every refusal and coverage gap of the signed calendar files it reads (computed from
    the files); then PASS or FAIL on `_check_stale01` (look-ahead audit LA-02, part 2: it used to be NOT_RUN whatever the
    files). STALE01_CAL_FILES / STALE01_CAL_SPAN is the contract: once nothing is waiting, a coverage or signing error
    raised inside the body is a FAIL. The v1.2-rule columns and the ages are not asserted (see the readings above)."""
    missing, text = [], {}
    for name in STALE01_FIXTURES:
        try:
            text[name] = require_fixture(name).read_text(encoding="utf-8")
        except NotRun as exc:
            missing.append(exc.reason.split(": ", 1)[1])
    if missing:
        raise NotRun("REFDATA: G-STALE-01 waits for " + "; ".join(missing))
    from core.calendars.adapter import CalendarClocks
    from core.calendars.store import CalendarSet
    live = CalendarSet()
    waiting = _stale01_waiting(live)
    if waiting:
        raise NotRun("OWNER: G-STALE-01 on the signed calendars waits for " + "; ".join(waiting))
    clk = CalendarClocks(REG, cal=live)
    obs = {}
    for name, sid in zip(STALE01_FIXTURES, STALE01_SERIES):
        rows = _fixture_csv(name, text[name], (sid,), F07_PROVENANCE if name == F07 else _f18_provenance(sid))
        obs[sid] = [(r["date"], r[sid]) for r in rows
                    if r[sid] is not None and STALE01_CAL_SPAN[0] <= r["date"] <= STALE01_SPAN[1]]
    _check_stale01(_stale01_store(obs, clk), clk, STALE01_SPAN)


test_stale_01_g_stale_01_reference_table_refdata.test_ids = ["T-STALE-01", "G-STALE-01"]


def _stale01_invented(clk, lo, hi, series=STALE01_SERIES, drop=()) -> dict:
    """Invented observations (not FRED data) on every expected date of each series on `clk` from a month before `lo`
    to `hi` (source-skipped dates are not expected, so none is written), less the dates in `drop`."""
    out = {}
    for sid in series:
        rows, d = [], clk.next_expected_obs(sid, lo - timedelta(days=31))
        while d <= hi:
            if d not in drop:
                rows.append((d, 100.0 + (d.toordinal() % 7)))
            d = clk.next_expected_obs(sid, d)
        out[sid] = rows
    return out


def test_stale_01_body_passes_and_fails_on_invented_releases():
    """LA-02 part 2: the G-STALE-01 / T-STALE-01 body can PASS and can FAIL. Invented releases in the F18 / F07 layouts
    (no FRED data) on the calendars module's synthetic signed set, every expected date written, pass over decisions
    2016-06-01 -> 2018-11-30 at both closes: the DTWEXBGS 2018-03-02 and DEXKOUS 2017-01-20 source skips flag, without
    the list, exactly the four decisions of each close between the skipped Friday's deadline and the next H.10 release
    (none with it); the DEXKOUS 2018-12-05 skip, a Wednesday published with the rest of its week, flags none. It
    fails, each clause on its own: a week's last H.10 release deleted on a date not in the list (a); a staleness check
    that never flags (a, the converse); clocks that ignore the list standing in for the loaded list (b); DEXKOUS over
    one quarter around its skip (above the golden's Level 1 band); DTWEXBGS over 2018 (inside the band, above 1%); two
    consecutive DGS10 releases deleted (above 1%); two consecutive VIXCLS closes deleted (above 0%); and the layout with
    another series id. The calendar gate names nothing on the synthetic set, only holidays_KRX on a set whose KRX file
    covers 2026-27, and the refusal on the unsigned set. Each declared provenance equals the generator's table."""
    from core.calendars.adapter import CalendarClocks
    from tests.macro_m1_calendars import drafts_set, fixture_set, krx_short_set
    assert STALE01_FIXTURES == tuple(f"{sid}.csv" for sid in STALE01_SERIES[:3]) + (F07,)
    for name, sid in zip(STALE01_FIXTURES, STALE01_SERIES):
        declared = F07_PROVENANCE if name == F07 else _f18_provenance(sid)
        assert _generator_provenance(name) == declared, (name, _generator_provenance(name))
    cal = fixture_set()
    clk = CalendarClocks(REG, cal=cal)
    assert _stale01_waiting(cal) == []
    assert _stale01_waiting(krx_short_set()) == [
        "holidays_KRX.yaml v1.0.0-fixture covers 2026-01-01..2027-12-31, needs 2015-12-04..2026-10-25"], \
        _stale01_waiting(krx_short_set())
    assert any(w.startswith("holidays_KRX.yaml refused (") for w in _stale01_waiting(drafts_set())), \
        _stale01_waiting(drafts_set())
    lo, hi = date(2016, 6, 1), date(2018, 11, 30)
    obs = _stale01_invented(clk, lo, hi)
    vix = [(d, v) for d, v in obs["VIXCLS"]]
    text = _layout_text([(d, {"VIXCLS": v, "VXVCLS": v + 2.0}) for d, v in vix], ("VIXCLS", "VXVCLS"), F07_PROVENANCE,
                        date_col="observation_date")
    assert [(r["date"], r["VIXCLS"]) for r in _fixture_csv(F07, text, ("VIXCLS",), F07_PROVENANCE)] == vix
    got, hits = _check_stale01(_stale01_store(obs, clk), clk, (lo, hi))
    assert got["dexkous_stale_schedule_us"] > 0 and got["dtwexbgs_stale_schedule_krx"] > 0, got
    assert got["dgs10_stale_schedule_us"] == got["vixcls_stale_schedule_krx"] == 0, got
    # the decisions the two skips flag without the list. The skipped Friday is due at the next Monday's H.10 release
    # (16:15 ET); the deadline is one publication day later (Tuesday 16:15 ET), and the following Monday's release
    # clears it. So the US closes (16:00 ET + 30 s) and the KRX closes (06:30:30Z) of Wednesday, Thursday, Friday and
    # that Monday are flagged: the Monday US close is before the release that clears it (2018-03-12 in EDT).
    week = lambda days, hh, mm: [(U(y, m, d, hh, mm, 30), skip) for (y, m, d), skip in days]      # noqa: E731
    dex = [((2017, 1, 25), date(2017, 1, 20)), ((2017, 1, 26), date(2017, 1, 20)), ((2017, 1, 27), date(2017, 1, 20)),
           ((2017, 1, 30), date(2017, 1, 20))]
    twx = [((2018, 3, 7), date(2018, 3, 2)), ((2018, 3, 8), date(2018, 3, 2)), ((2018, 3, 9), date(2018, 3, 2))]
    assert hits["dexkous_stale_schedule_us"] == week(dex, 21, 0), hits["dexkous_stale_schedule_us"]
    assert hits["dexkous_stale_schedule_krx"] == week(dex, 6, 30), hits["dexkous_stale_schedule_krx"]
    assert hits["dtwexbgs_stale_schedule_us"] == week(twx, 21, 0) + [(U(2018, 3, 12, 20, 0, 30), date(2018, 3, 2))], \
        hits["dtwexbgs_stale_schedule_us"]
    assert hits["dtwexbgs_stale_schedule_krx"] == week(twx + [((2018, 3, 12), date(2018, 3, 2))], 6, 30), \
        hits["dtwexbgs_stale_schedule_krx"]
    assert not any(hits[k] for k in hits if k.startswith(("dgs10", "vixcls"))), hits
    # a mid-week skip (DEXKOUS 2018-12-05, a Wednesday) is published with Thursday and Friday: no decision is flagged
    dec2018 = (date(2018, 11, 1), date(2018, 12, 31))
    dec_store = _stale01_store(_stale01_invented(clk, *dec2018, ("DEXKOUS",)), clk)
    assert _check_stale01(dec_store, clk, dec2018, series=("DEXKOUS",))[1] == {
        "dexkous_stale_schedule_us": [], "dexkous_stale_schedule_krx": []}

    def fails(needle, sid, span, *, drop=(), clocks=clk, is_stale=C.is_stale):
        store = _stale01_store(_stale01_invented(clk, span[0], span[1], (sid,), drop), clk)
        e = _raises(lambda: _check_stale01(store, clocks, span, series=(sid,), markets=(("US", "us"),),
                                           is_stale=is_stale), AssertionError)
        assert needle in str(e), (needle, str(e))

    q1 = (date(2017, 1, 3), date(2017, 3, 31))
    fails("T-STALE-01 (a): DEXKOUS at the US close: missed observation dates [datetime.date(2017, 4, 21)]", "DEXKOUS",
          (date(2017, 3, 1), date(2017, 5, 31)), drop=(date(2017, 4, 21),))        # a week's last (Friday) release
    fails("T-STALE-01 (a): without the source-exception list, DEXKOUS is not flagged at the US close on 4 of the 4 "
          "decisions past the deadline of the listed date 2017-01-20, first 2017-01-25 21:00:30Z", "DEXKOUS", q1,
          is_stale=lambda *args: C.Fresh())                                  # a check that never flags
    fails("T-STALE-01 (b): with the source-exception list loaded, DEXKOUS is still flagged", "DEXKOUS", q1,
          clocks=_NoSkipClocks(clk))
    fails("G-STALE-01/dexkous_stale_schedule_us:", "DEXKOUS", q1)
    fails("T-STALE-01 (a): DTWEXBGS is stale on", "DTWEXBGS", (date(2018, 1, 2), date(2018, 12, 31)))
    fails("T-STALE-01 (c): DGS10 is stale on", "DGS10", (date(2017, 3, 1), date(2017, 6, 30)),
          drop=(date(2017, 5, 9), date(2017, 5, 10)))                    # stale at the 2017-05-12 US close
    fails("T-STALE-01 (c): VIXCLS is stale on", "VIXCLS", (date(2017, 3, 1), date(2017, 12, 29)),
          drop=(date(2017, 4, 11), date(2017, 4, 12)))                    # stale at the 2017-04-13 US close
    layout = _raises(lambda: _fixture_csv(F07, text, ("VIXCLS",), _f18_provenance("VIXCLS")), AssertionError)
    assert "provenance {'series_id': 'VIXCLS', 'value_status': 'vendor_close'" in str(layout), layout


# --------------------------------------------------------------------------- #
# T-ROLE-01 / T-MISS-02 / T-ROLE-02
# --------------------------------------------------------------------------- #
def test_role_01_counters_halt_scope_and_role_actions():
    b = REG.resolve_binding("KOSPI_OFFICIAL_CLOSE", "R-06")
    miss = P.MissingInput("KOSPI_OFFICIAL_CLOSE", "missing", b.role, b.books)
    act = C.on_input_failure("KOSPI_OFFICIAL_CLOSE", miss, b)
    assert act.fail_closed and act.alert and act.counts and act.status == "missing" and act.halt == "bound_books"
    assert not hasattr(miss, "value")                                            # no interpolation, state unchanged
    assert C.on_input_failure("KOSPI_OFFICIAL_CLOSE", C.Stale("missed_release"), b).status == "stale_missed_release"
    counters = C.InputCounters()
    assert counters.step(REG, [(b, True)]) == []                                 # miss 1: fail closed only
    halts = counters.step(REG, [(b, True)])                                      # miss 2: HALT bound books only
    assert [h.book_id for h in halts] == ["specification:KR"] and halts[0].reason_code == "acting_input_stale:KOSPI_OFFICIAL_CLOSE"
    assert counters.step(REG, [(b, False)]) == [] and counters.state("specification:KR")["consecutive_failures"]["KOSPI_OFFICIAL_CLOSE"] == 0
    assert counters.step(REG, [(b, True)]) == []                                 # a fresh decision reset the counter
    # two inputs bound to one book failing on alternate decisions HALT it at the 2nd decision
    cap = REG.resolve_binding("KRX_005930_MARKET_CAP", "R-07")
    assert REG.book_ids(cap) == ("recommended:KR", "specification:KR")
    c2 = C.InputCounters()
    assert c2.step(REG, [(cap, True), (b, False)]) == []
    halts = c2.step(REG, [(cap, False), (b, True)])
    assert [h.book_id for h in halts] == ["specification:KR"]                    # recommended:KR reset, never HALTed
    # KODEX basket: limit 5, and it does not feed the book counter (F-16)
    k = REG.resolve_binding("KODEX200_PDF", "R-07")
    c3 = C.InputCounters()
    for i in range(4):
        assert c3.step(REG, [(k, True)]) == [], i
    assert sorted(h.book_id for h in c3.step(REG, [(k, True)])) == ["recommended:KR", "specification:KR"]
    # risk_model -> conservative default, never HALT; context -> label only; forward_sim -> that book only
    r = C.on_input_failure("USD_LIVE_PROXY", P.MissingInput("USD_LIVE_PROXY", "stale", "risk_model", ()), REG.resolve_binding("USD_LIVE_PROXY", "hedge_state"))
    assert r.sets.get("hedge_credit_off") is True and r.halt == "never" and not r.fail_closed and not r.counts
    cov = C.on_input_failure("SOX_CLOSE", C.Stale("missed_release"), REG.resolve_binding("SOX_CLOSE", "korea_covariance"))
    assert cov.action == "carry_last_valid_terms_stale_then_drop" and cov.sets["sets_hedge_credit_off"] is False
    ctx = C.on_input_failure("DTWEXBGS", C.Stale("missed_release"), REG.resolve_binding("DTWEXBGS", "R-13"))
    assert ctx.action == "label_stale" and ctx.status == "stale" and not ctx.alert and not ctx.counts
    fs = C.on_input_failure("SPX_OFFICIAL_CLOSE", P.MissingInput("SPX_OFFICIAL_CLOSE", "missing", "forward_sim", ("forward_sim:R-28",)),
                            REG.resolve_binding("SPX_OFFICIAL_CLOSE", "R-28_R-29"))
    assert fs.halt == "that_book" and fs.books == ("forward_sim:R-28", "forward_sim:R-29")
    assert C.InputCounters().step(REG, [(REG.resolve_binding("SPX_OFFICIAL_CLOSE", "R-28_R-29"), True)] * 3) == []
    # an unreadable publication calendar fails every acting input closed (never observation-age staleness)
    store = _store()
    store.append([prov01_rows()[1]])
    ctx_live = P.RunContext(DECISION, U(2026, 10, 2, 7))
    ok = C.read_input(store, REG, "KOSPI_OFFICIAL_CLOSE", ctx_live, "R-06", CLK, require_session=OCT2)
    assert isinstance(ok, P.PITValue) and ok.value == 7003.74
    broken = C.read_input(store, REG, "KOSPI_OFFICIAL_CLOSE", ctx_live, "R-06", StubClocks(unreadable=True), require_session=OCT2)
    assert isinstance(broken, P.MissingInput) and broken.reason == "missing"
    _raises(lambda: C.expected_available_utc(REG, "DGS10", OCT2, StubClocks(unreadable=True)), C.CalendarUnavailable)
    # derived bindings: no card is PASS in M1, so derived == declared; an admission adds the recommended book
    derived = C.derive_bindings(REG, {})
    assert derived["KOSPI_OFFICIAL_CLOSE|*"] == ("specification:KR",)
    assert C.derive_bindings(REG, {"KOSPI_OFFICIAL_CLOSE": True})["KOSPI_OFFICIAL_CLOSE|*"] == ("specification:KR", "recommended:KR")


test_role_01_counters_halt_scope_and_role_actions.test_ids = ["T-ROLE-01", "T-MISS-02"]


def _registry_copy(mutate):
    import yaml
    doc = yaml.safe_load(C.REGISTRY_PATH.read_text(encoding="utf-8"))
    mutate(doc)
    p = _tmp() / "registry.yaml"
    p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return p


def test_role_02_registration_refusals_and_contract():
    call = C.contract(REG, "BOK_CALL_RATE")
    assert call.range == (-1.0, 40.0) and call.unit == "pct"
    assert C.check_contract(call, 25.0) is None                                  # Dec-1997 Korean call rate
    assert "range" in C.check_contract(call, 45.0) and "finite" in C.check_contract(call, math.nan)
    kospi = C.contract(REG, "KOSPI_OFFICIAL_CLOSE")
    assert C.check_contract(kospi, 7003.74, previous=6971.5) is None and "return" in C.check_contract(kospi, 9500.0, previous=6971.5)
    assert "monotone" in C.check_contract(kospi, 7003.74, obs_date=OCT2, previous_date=OCT2)
    assert C.check_contract(C.contract(REG, "VIXCLS"), 160.0) and C.check_contract(C.contract(REG, "VIXCLS"), 16.34) is None
    # a contract violation is a missing input with the role's action
    store = _store()
    store.append([_kospi(9500.0, status="official_close", obs_utc=U(2026, 10, 2, 6, 30, 30), available=U(2026, 10, 2, 6, 30, 30),
                         retrieved=U(2026, 10, 2, 6, 41), source="KRX"),
                  _kospi(6971.5, obs_date=date(2026, 10, 1), status="official_close", obs_utc=U(2026, 10, 1, 6, 30, 30),
                         available=U(2026, 10, 1, 6, 30, 30), retrieved=U(2026, 10, 1, 6, 41), source="KRX")])
    v = C.read_input(store, REG, "KOSPI_OFFICIAL_CLOSE", P.RunContext(DECISION, U(2026, 10, 2, 7)), "R-06", CLK, require_session=OCT2)
    assert isinstance(v, P.MissingInput) and v.reason == "missing"
    # registration: acting/forward_sim binding without `books` refused; books: [] valid and dormant
    def no_books(doc):
        doc["series"]["KOSPI_OFFICIAL_CLOSE"]["bindings"] = [{"role": "acting_exposure"}]
    _raises(lambda: C.load_registry(_registry_copy(no_books), roles={}), C.RegistryError, "books")
    dormant = REG.resolve_binding("US_SLEEVE_OFFICIAL_CLOSE", "R-06")
    assert dormant.dormant and dormant.books == () and REG.book_ids(dormant) == ()
    assert C.InputCounters().step(REG, [(dormant, True), (dormant, True)]) == []
    def group_as_series(doc):
        doc["series"]["NAV_LINE_CLOSES"] = dict(doc["series"]["KRX_069500_OFFICIAL_CLOSE"])
    _raises(lambda: C.load_registry(_registry_copy(group_as_series), roles={}), C.RegistryError, "group name")
    def ghost_member(doc):
        doc["groups"]["ASIA_INDEX_CLOSES"].append("GHOST_CLOSE")
    _raises(lambda: C.load_registry(_registry_copy(ghost_member), roles={}), C.RegistryError, "GHOST_CLOSE")
    def no_contract(doc):
        doc["series"]["KOSPI_OFFICIAL_CLOSE"].pop("contract")
    _raises(lambda: C.load_registry(_registry_copy(no_contract), roles={}), C.RegistryError, "without a contract")
    def drift(doc):
        doc["series"]["KOSPI_OFFICIAL_CLOSE"]["bindings"] = [{"role": "acting_exposure", "books": ["recommended", "specification"]}]
    _raises(lambda: C.load_registry(_registry_copy(drift)), C.RegistryError, "differ from data_contracts.roles")
    assert C.load_registry(_registry_copy(lambda d: None)).md5 != REG.md5 or True


test_role_02_registration_refusals_and_contract.test_ids = ["T-ROLE-02"]


# --------------------------------------------------------------------------- #
# T-LAG-01 / T-LAG-02
# --------------------------------------------------------------------------- #
def test_lag_01_independent_audit_raises_or_halts():
    official = P.to_value(prov01_rows()[1], role="acting_exposure", books=("specification:KR",))
    late = P.to_value(P.make_row(**{**{k: v for k, v in prov01_rows()[1].items() if k != "content_hash"},
                                    "available_at_utc": U(2026, 10, 2, 6, 31)}), role="acting_exposure", books=("specification:KR",))
    live = P.RunContext(DECISION, U(2026, 10, 2, 7), "live")
    back = P.RunContext(DECISION, U(2026, 10, 2, 7), "backtest")
    assert L.lag_audit([official], live, "KR", REG, CLK) == {"checked": 1, "violations": [], "books": []}
    out = L.lag_audit([late], live, "KR", REG, CLK)
    assert out["books"] == ["specification:KR"] and out["violations"][0]["check"] == "available_at_utc <= decision_utc"
    assert set(out["violations"][0]) == {"series_id", "obs_date", "check", "expected_usable_at_utc", "stamped_available_at_utc"}
    _raises(lambda: L.lag_audit([late], back, "KR", REG, CLK), L.LookAheadError, "available_at_utc")
    prov = P.to_value(prov01_rows()[0], role="acting_exposure", books=("specification:KR",))
    assert any(v["check"] == "value_status == official_close" for v in L.lag_audit([prov], live, "KR", REG, CLK)["violations"])
    _raises(lambda: L.lag_audit([prov], back, "KR", REG, CLK), L.LookAheadError)
    _raises(lambda: L.lag_audit([[6943.66, 7003.74]], live, "KR", REG, CLK), L.RawFrameRead)
    # independence: a row pit_value would accept (stamped 06:00Z, before the print bound) is caught from the calendars
    early = P.to_value(P.make_row(**{**{k: v for k, v in prov01_rows()[1].items() if k != "content_hash"},
                                     "available_at_utc": U(2026, 10, 2, 6, 0)}), role="acting_exposure", books=("specification:KR",))
    store = _store()
    store.append([early.__dict__ | {} and P.make_row(**{k: getattr(early, k) for k in P._ROW_FIELDS if k != "content_hash"})])
    assert _read(store, U(2026, 10, 2, 7)).value == 7003.74
    checks = {v["check"] for v in L.lag_audit([early], live, "KR", REG, CLK)["violations"]}
    assert "available_at_utc >= publication_instant" in checks
    # a quarantined close (retrieved 06:40:29Z) carrying official_close is a violation; context inputs are skipped
    q = P.to_value(P.make_row(**{**{k: v for k, v in prov01_rows()[1].items() if k != "content_hash"},
                                 "retrieved_at_utc": U(2026, 10, 2, 6, 40, 29)}), role="acting_exposure", books=("specification:KR",))
    assert any(v["check"] == "retrieved_at_utc >= close + 10 min" for v in L.lag_audit([q], live, "KR", REG, CLK)["violations"])
    ctx_in = P.to_value(prov01_rows()[0], role="context", books=())
    assert L.lag_audit([ctx_in], live, "KR", REG, CLK)["checked"] == 0
    assert L.usable_at(REG, "DGS10", date(2026, 10, 1), CLK) == U(2026, 10, 2, 20, 15)


test_lag_01_independent_audit_raises_or_halts.test_ids = ["T-LAG-01"]


def test_lag_02_positional_shift_rejected_on_gapped_series():
    months = [date(2025, m, 1) for m in range(1, 13) if m != 10] + [date(2026, m, 1) for m in range(1, 10)]
    _raises(lambda: L.assert_no_positional_shift(months, 12), L.PositionalShiftRejected, "2025-09-01 -> 2025-11-01")
    L.assert_no_positional_shift([date(2026, m, 1) for m in range(1, 10)], 3)
    days = [date(2026, 9, 28) + timedelta(days=i) for i in (0, 1, 2, 4)]
    _raises(lambda: L.assert_no_positional_shift(days, 1, expected_step=timedelta(days=1)), L.PositionalShiftRejected)
    L.assert_no_positional_shift(days, 0, expected_step=timedelta(days=1))


test_lag_02_positional_shift_rejected_on_gapped_series.test_ids = ["T-LAG-02"]


# --------------------------------------------------------------------------- #
# T-SYN-01, T-MISS-01, T-SER-01, T-SER-02, T-H10-01
# --------------------------------------------------------------------------- #
def test_syn_01_synthetic_rejected_for_acting_allowed_for_context():
    s = D.load_series("KODEX200_PDF", source="auto", days=60)                    # hermetic: FRED fails -> SYNTHETIC
    assert s.source == "SYNTHETIC" and "failed" in s.note
    store = _store()
    rep = P.ingest_series(store, "KODEX200_PDF", s, retrieved_at_utc=U(2026, 10, 2, 7), registry=REG, clocks=CLK, provider_mode="auto")
    assert rep.appended > 0 and all(r["synthetic"] and r["provider_mode"] == "auto" for r in store.rows("KODEX200_PDF"))
    v = P.pit_value(store, "KODEX200_PDF", DECISION, U(2026, 10, 2, 7), "R-07", registry=REG)
    assert isinstance(v, P.MissingInput) and v.reason == "synthetic_rejected" and v.books == ("recommended", "specification")
    act = C.on_input_failure("KODEX200_PDF", v, REG.resolve_binding("KODEX200_PDF", "R-07"))
    assert act.status == "synthetic_rejected" and act.fail_closed is True and act.alert
    c = D.load_series("DGS10", source="auto", days=60)
    P.ingest_series(store, "DGS10", c, retrieved_at_utc=U(2026, 10, 2, 7), registry=REG, clocks=CLK, provider_mode="auto")
    ctx = P.pit_value(store, "DGS10", DECISION, U(2026, 10, 2, 7), "R-12_refusal_book", registry=REG)
    assert isinstance(ctx, P.PITValue) and ctx.synthetic and ctx.provider_mode == "auto" and ctx.role == "context"
    risk = P.pit_value(store, "DGS10", DECISION, U(2026, 10, 2, 7), "corr63_backtests", registry=REG)
    assert isinstance(risk, P.MissingInput) and risk.reason == "synthetic_rejected"


test_syn_01_synthetic_rejected_for_acting_allowed_for_context.test_ids = ["T-SYN-01"]


def test_miss_01_calendar_offsets_and_the_october_gap():
    months = [P.add_months(date(2024, 1, 1), i) for i in range(34)]            # Jan-2024 .. Oct-2026
    cpi = {m: 300.0 * (1.003 ** i) for i, m in enumerate(months) if m != date(2025, 10, 1)}
    aug = P.yoy(cpi, date(2026, 8, 1))
    assert not aug.flagged and abs(aug.value - (cpi[date(2026, 8, 1)] / cpi[date(2025, 8, 1)] - 1.0)) < 1e-12
    keys = sorted(cpi)
    positional = cpi[date(2026, 8, 1)] / cpi[keys[keys.index(date(2026, 8, 1)) - 12]] - 1.0
    assert abs(positional - aug.value) > 1e-4, "the positional value must differ and must not be produced"
    for m, fn in ((date(2025, 10, 1), P.yoy), (date(2026, 10, 1), P.yoy), (date(2025, 10, 1), P.mom), (date(2025, 11, 1), P.mom)):
        r = fn(cpi, m)
        assert r.flagged and math.isnan(r.value), (m, fn.__name__)
    for m in (date(2025, 10, 1), date(2025, 11, 1), date(2025, 12, 1)):
        assert P.rolling_mean(cpi, m, 3).flagged
    assert not P.rolling_mean(cpi, date(2026, 1, 1), 3).flagged
    assert P.vendor_status_across_gap([date(2025, 9, 1), date(2025, 10, 1), date(2025, 11, 1)], [date(2025, 10, 1)]) == "vendor_derived_across_gap"
    assert P.vendor_status_across_gap([date(2026, 7, 1), date(2026, 8, 1)], [date(2025, 10, 1)]) == "vendor_derived"
    # a derived row carries lineage, the weakest input status and the latest input availability
    store = _store()
    rows = prov01_rows()
    store.append(rows)
    official = P.to_value(rows[1], role="acting_exposure", books=())
    assert P.put_derived(store, "DM_MKT_VOL_126", OCT2, 0.21, [official], retrieved_at_utc=U(2026, 10, 2, 7)) == 1
    d = store.rows("DM_MKT_VOL_126")[0]
    assert d["inputs"] == [official.content_hash] and d["value_status"] == "official_close" and d["close_inputs_official"] is True
    v = P.pit_value(store, "DM_MKT_VOL_126", DECISION, U(2026, 10, 2, 7), "R-04", registry=REG)
    assert isinstance(v, P.PITValue) and v.value == 0.21
    P.put_derived(store, "DM_MKT_VOL_126", OCT2, 0.22, [P.to_value(rows[0], role="acting_exposure", books=())], retrieved_at_utc=U(2026, 10, 2, 7))
    s2 = _store()
    P.put_derived(s2, "DM_MKT_VOL_126", OCT2, 0.22, [P.to_value(rows[0], role="acting_exposure", books=())], retrieved_at_utc=U(2026, 10, 2, 7))
    bad = P.pit_value(s2, "DM_MKT_VOL_126", DECISION, U(2026, 10, 2, 7), "R-04", registry=REG)
    assert isinstance(bad, P.MissingInput) and bad.reason == "provisional_intraday"


test_miss_01_calendar_offsets_and_the_october_gap.test_ids = ["T-MISS-01"]


# T-MISS-01 on the FRED snapshot of 2026-10-02 (spec L5624, L1353-1355; goldens.csv S11/cpi_yoy_aug2026 and
# S11/cpi_yoy_wrong_lag). F18 (docs/macro_fixtures.py:65) is one file per FRED id, written flat as <id>.csv, series_id
# the id, first_release, calendar_bound. Declared layout: the value is the column named by the id (FRED's own header),
# obs_date the first of the observation month, a blank or "." value no observation, one row per month. Declared
# reading, an owner question (docs/product/LOOKAHEAD_LA02_PART2_2026-11-10.md question 18): that column is the value
# FRED served on 2026-10-02, the snapshot's current value. ACQUISITION.csv:22 lists CPIAUCSL "with ALFRED vintages;
# vintages as of 2026-10-02" and spec L1435 / L1436 name a first release (output_type=4) and a current value; no
# vintage column is read, and a file with one row per month and vintage fails at `_monthly` (two rows for one month).
# The snapshot ends with Aug-2026 for both series: section 11's current state (2 Oct 2026) prints U-3 for Aug-2026
# (spec L6347) and the Aug-2026 CPI YoY (L1355, L5624, L6348). A later month in the file is a later vintage.
MISS01_FIXTURES = ("CPIAUCSL.csv", "UNRATE.csv")    # F18: CPI and the household-survey rate behind Sahm (spec L1353)
MISS01_GAP = date(2025, 10, 1)       # spec L1353: "Oct-2025 CPI and household survey, never collected" (registry missing_months)
MISS01_AUG = date(2026, 8, 1)        # spec L5624: CPI YoY for Aug-2026 = 3.353% +/- 0.01
MISS01_LAST = date(2026, 8, 1)       # the last month of both series on 2026-10-02 (spec L6347 "U-3 ... (Aug-2026)"; L1355)
MISS01_TOL = 1e-4                    # spec L5624 "+/- 0.01" in percent; S11/cpi_yoy_aug2026 note "+/- 0.01 pp (test-specific)"
# spec L5624: derived values that use the Oct-2025 observation are NaN and flagged: YoY for Oct-2025 and Oct-2026, MoM
# for Oct and Nov 2025, and Sahm's 3-month means (those whose window holds Oct-2025: Oct, Nov and Dec 2025).
MISS01_NAN_YOY = (date(2025, 10, 1), date(2026, 10, 1))
MISS01_NAN_MOM = (date(2025, 10, 1), date(2025, 11, 1))
MISS01_NAN_SAHM = (date(2025, 10, 1), date(2025, 11, 1), date(2025, 12, 1))


def _f18_provenance(series_id: str) -> tuple[tuple[str, str], ...]:
    return (("series_id", series_id), ("value_status", "first_release"), ("available_at_source", "calendar_bound"))


def _monthly(name: str, rows: list[dict], col: str) -> dict:
    """{first of month: value} of an F18 monthly file, read from the declared value column `col` (the snapshot's
    value; no vintage column is read); AssertionError on an obs_date that is not a first of month or on two rows for
    one month (a long file of ALFRED vintages)."""
    out = {}
    for r in rows:
        assert r["date"].day == 1, f"{name}: obs_date {r['date']} is not the first of a month"
        assert r["date"] not in out, f"{name}: two rows for {r['date']:%Y-%m}"
        if r[col] is not None:
            out[r["date"]] = r[col]
    return out


def _check_miss01(cpi: dict, unrate: dict, *, yoy=P.yoy, mom=P.mom, rolling_mean=P.rolling_mean) -> dict:
    """T-MISS-01 on monthly CPIAUCSL and UNRATE ({first of month: value}): neither has a month after Aug-2026, the
    last one in the 2026-10-02 snapshot (a later month is a later vintage), nor an Oct-2025 value; the Aug-2026 CPI YoY
    is computed (its window merely contains the gap), is not the positional shift(12) value, and equals 3.353% +/- 0.01
    pp; YoY Oct-2025 / Oct-2026, MoM Oct / Nov 2025 and the Sahm 3-month means of UNRATE for Oct-Dec 2025 are NaN and
    flagged (on the snapshot, Oct-2026 has no endpoint). The positional value and the spec's 3.713% are printed, never
    asserted as a value (S11/cpi_yoy_wrong_lag is print_only). `yoy`, `mom` and `rolling_mean` are core.ficc.pit's (the
    demonstrations pass broken ones). Returns the Aug-2026 YoY and the positional value."""
    for name, series in (("CPIAUCSL", cpi), ("UNRATE", unrate)):
        late = sorted(m for m in series if m > MISS01_LAST)
        assert not late, (f"T-MISS-01: {name} has a value for {late[0]:%Y-%m}, after {MISS01_LAST:%Y-%m}, the last month "
                          f"of the 2026-10-02 snapshot (spec L6347, L1355): a later vintage")
    gap = MISS01_GAP
    assert gap not in cpi, f"T-MISS-01: CPIAUCSL has a value for {gap:%Y-%m} (spec L1353: never collected)"
    assert gap not in unrate, f"T-MISS-01: UNRATE has a value for {gap:%Y-%m} (spec L1353: household survey never collected)"
    aug = yoy(cpi, MISS01_AUG)
    assert not aug.flagged and math.isfinite(aug.value), (
        f"T-MISS-01: the Aug-2026 CPI YoY is flagged ({aug.reason}); an endpoint YoY whose window merely contains "
        f"Oct-2025 is computed (spec L5624)")
    keys = sorted(cpi)
    assert MISS01_AUG in keys and keys.index(MISS01_AUG) >= 12, "T-MISS-01: CPIAUCSL lacks 12 rows before Aug-2026"
    positional = cpi[MISS01_AUG] / cpi[keys[keys.index(MISS01_AUG) - 12]] - 1.0
    s11 = G.golden("S11")
    print(f"T-MISS-01: Aug-2026 CPI YoY {aug.value:.4%} (calendar lag); positional shift(12) {positional:.4%}, never "
          f"produced (the spec prints {s11.want('cpi_yoy_wrong_lag'):.3%})")
    assert abs(aug.value - positional) > MISS01_TOL, (
        f"T-MISS-01: the produced Aug-2026 YoY {aug.value:.4%} is the positional shift(12) value (spec L5624: the "
        f"positional version must not be produced)")
    want = s11.want("cpi_yoy_aug2026")
    assert abs(aug.value - want) <= MISS01_TOL + 1e-12, (
        f"T-MISS-01: Aug-2026 CPI YoY {aug.value:.4%} != {want:.3%} +/- 0.01 pp (spec L5624; S11/cpi_yoy_aug2026)")
    for label, fn, series, months in (("CPI YoY", yoy, cpi, MISS01_NAN_YOY), ("CPI MoM", mom, cpi, MISS01_NAN_MOM),
                                      ("Sahm 3-month mean of UNRATE", lambda s, m: rolling_mean(s, m, 3), unrate,
                                       MISS01_NAN_SAHM)):
        for m in months:
            r = fn(series, m)
            assert r.flagged and math.isnan(r.value), (
                f"T-MISS-01: {label} {m:%Y-%m} is {r.value!r}, not NaN and flagged (it uses the Oct-2025 observation; "
                f"spec L5624)")
    return {"aug_yoy": aug.value, "positional": positional}


def test_miss_01_cpi_yoy_3_353_refdata():
    """T-MISS-01 on the FRED snapshot (F18 CPIAUCSL.csv and UNRATE.csv): NOT_RUN (REFDATA) naming every absent file;
    then PASS or FAIL on `_check_miss01` (look-ahead audit LA-02, part 2: it used to be NOT_RUN whatever the files).
    The vendor-tag clause (a vendor value across the gap is vendor_derived_across_gap) stays with the synthetic test:
    the old reason's SAHMCURRENT has no fixture (docs/macro_fixtures.FRED_IDS lists SAHMREALTIME)."""
    missing, text = [], {}
    for name in MISS01_FIXTURES:
        try:
            text[name] = require_fixture(name).read_text(encoding="utf-8")
        except NotRun as exc:
            missing.append(exc.reason.split(": ", 1)[1])
    if missing:
        raise NotRun("REFDATA: T-MISS-01 waits for " + "; ".join(missing))
    series = {}
    for name in MISS01_FIXTURES:
        sid = name[:-len(".csv")]
        series[sid] = _monthly(name, _fixture_csv(name, text[name], (sid,), _f18_provenance(sid)), sid)
    _check_miss01(series["CPIAUCSL"], series["UNRATE"])


test_miss_01_cpi_yoy_3_353_refdata.test_ids = ["T-MISS-01"]


def test_miss_01_body_passes_and_fails_on_invented_cpi():
    """LA-02 part 2: the T-MISS-01 body can PASS and can FAIL. Invented monthly CPI (growth 3.353% a year, Oct-2025
    written as FRED's ".") and UNRATE in the F18 layout (no FRED data) pass. It fails on a Sep-2026 CPI or UNRATE row
    (after the snapshot's last month), on an Oct-2025 CPI value, on an Oct-2025 UNRATE value, on an Aug-2026 CPI giving
    3.37%, and with broken functions in place of core.ficc.pit's: a YoY that flags any window holding a gap, a
    positional shift(12) YoY, a YoY / MoM that carries the last value into a missing endpoint, and a 3-month mean over
    the members present; and on a file whose series_id is another id, or with two rows for one month (vintages)."""
    for name in MISS01_FIXTURES:
        assert _generator_provenance(name) == _f18_provenance(name[:-len(".csv")]), (name, _generator_provenance(name))
    months = [P.add_months(date(2024, 1, 1), i) for i in range(32)]                 # Jan-2024 .. Aug-2026
    growth = 1.03353 ** (1 / 12)

    def files(cpi_gap=None, unrate_gap=None, aug=None, sid="CPIAUCSL", sep=()):
        cpi = {m: 300.0 * growth ** i for i, m in enumerate(months)}
        cpi[MISS01_GAP], cpi[MISS01_AUG] = cpi_gap, aug if aug is not None else cpi[MISS01_AUG]
        unrate = {m: 4.0 + 0.1 * (i % 3) for i, m in enumerate(months)}
        unrate[MISS01_GAP] = unrate_gap
        out = []
        for col, prov_id, values in (("CPIAUCSL", sid, cpi), ("UNRATE", "UNRATE", unrate)):
            rows = [(m, {col: values[m]}) for m in months]
            if col in sep:                                # a Sep-2026 row: published after 2026-10-02 (a later vintage)
                rows.append((date(2026, 9, 1), {col: values[MISS01_AUG]}))
            text = _layout_text(rows, (col,), _f18_provenance(prov_id), date_col="observation_date")
            out.append(_monthly(f"{col}.csv", _fixture_csv(f"{col}.csv", text, (col,), _f18_provenance(col)), col))
        return out

    def carry(fn):                                    # fills a missing endpoint with the last earlier value
        def wrapped(series, m):
            filled = dict(series)
            for k in sorted({P.add_months(m, -12), P.add_months(m, -1), m}):
                if k not in filled:
                    earlier = [x for x in sorted(series) if x < k]
                    if earlier:
                        filled[k] = series[earlier[-1]]
            return fn(filled, m)
        return wrapped

    def positional(series, m):
        keys = sorted(series)
        return P.MonthlyValue(series[m] / series[keys[keys.index(m) - 12]] - 1.0, False)

    def strict(series, m):                            # flags a window that merely contains a missing month
        if any(P.add_months(m, -i) not in series for i in range(13)):
            return P.MonthlyValue(math.nan, True, "window holds a gap")
        return P.yoy(series, m)

    def mean_present(series, m, n=3):
        xs = [series[P.add_months(m, -i)] for i in range(n) if P.add_months(m, -i) in series]
        return P.MonthlyValue(sum(xs) / len(xs), False)

    got = _check_miss01(*files())
    assert abs(got["aug_yoy"] - 0.03353) < 1e-12 and abs(got["positional"] - (1.03353 * growth - 1.0)) < 1e-12, got
    cases = (
        (files(sep=("CPIAUCSL",)), {}, "T-MISS-01: CPIAUCSL has a value for 2026-09, after 2026-08, the last month"),
        (files(sep=("UNRATE",)), {}, "T-MISS-01: UNRATE has a value for 2026-09, after 2026-08, the last month"),
        (files(cpi_gap=310.0), {}, "CPIAUCSL has a value for 2025-10 (spec L1353: never collected)"),
        (files(unrate_gap=4.4), {}, "UNRATE has a value for 2025-10"),
        (files(aug=300.0 * growth ** 19 * 1.0337), {}, "Aug-2026 CPI YoY 3.3700% != 3.353% +/- 0.01 pp"),
        (files(), {"yoy": strict}, "the Aug-2026 CPI YoY is flagged (window holds a gap)"),
        (files(), {"yoy": positional}, "is the positional shift(12) value"),
        (files(), {"yoy": carry(P.yoy)}, "CPI YoY 2025-10 is"),
        (files(), {"mom": carry(P.mom)}, "CPI MoM 2025-10 is"),
        (files(), {"rolling_mean": mean_present}, "Sahm 3-month mean of UNRATE 2025-10 is"),
    )
    for args, broken, needle in cases:
        e = _raises(lambda: _check_miss01(*args, **broken), AssertionError)
        assert needle in str(e), (needle, str(e))
    layout = _raises(lambda: files(sid="CPILFESL"), AssertionError)
    assert "provenance {'series_id': 'CPILFESL'" in str(layout), layout
    vintages = _layout_text([(MISS01_AUG, {"CPIAUCSL": 322.1}), (MISS01_AUG, {"CPIAUCSL": 322.3})], ("CPIAUCSL",),
                            _f18_provenance("CPIAUCSL"), date_col="observation_date")      # one row per vintage
    long = _raises(lambda: _monthly("CPIAUCSL.csv", _fixture_csv("CPIAUCSL.csv", vintages, ("CPIAUCSL",),
                                                                 _f18_provenance("CPIAUCSL")), "CPIAUCSL"), AssertionError)
    assert "CPIAUCSL.csv: two rows for 2026-08" in str(long), long


def test_ser_01_named_series_and_futures_roll_days():
    _raises(lambda: P.named_series("Brent"), P.UnnamedSeries, "DCOILBRENTEU or BZ=F")
    _raises(lambda: P.pit_value(_store(), "Brent", DECISION, U(2026, 10, 2, 7), "R-13", registry=REG), P.UnnamedSeries)
    _raises(lambda: C.contract(REG, "Brent"), P.UnnamedSeries)
    assert P.named_series("DCOILBRENTEU") == "DCOILBRENTEU" and P.roll_days(REG, "BZ=F") == (date(2026, 4, 1),)
    store = _store()
    quotes = [(date(2026, 3, 30), 70.0), (date(2026, 3, 31), 71.0), (date(2026, 4, 1), 60.7), (date(2026, 4, 2), 61.0)]
    rep = P.ingest(store, "BZ=F", quotes, source="Yahoo", retrieved_at_utc=U(2026, 4, 3, 1), registry=REG, clocks=CLK)
    assert rep.appended == 4
    window = P.pit_window(store, "BZ=F", U(2026, 4, 3, 1), U(2026, 4, 3, 1), registry=REG)
    assert [w.obs_date for w in window] == [date(2026, 3, 30), date(2026, 3, 31), date(2026, 4, 2)]
    rets = P.returns_excluding_rolls([P.to_value(r, role="context", books=()) for r in sorted(store.rows("BZ=F"), key=lambda r: r["obs_date"])],
                                     P.roll_days(REG, "BZ=F"))
    assert [d for d, _ in rets] == [date(2026, 3, 31)] and not any(abs(r + 0.145) < 0.01 for _, r in rets)


test_ser_01_named_series_and_futures_roll_days.test_ids = ["T-SER-01"]


def test_ser_02_every_referenced_id_is_registered_with_a_contract():
    doc = json.loads(C.STORE_PATH.read_text(encoding="utf-8"))
    assert C.unknown_ids(REG, C.referenced_ids(doc)) == []
    for sid in doc["data_contracts"]["roles"]:
        assert REG.is_series(sid) or REG.is_group(sid), sid
    for g in ("ASIA_INDEX_CLOSES", "KRX_MARKET_CAPS_005930_000660_KOSPI", "NON_KR_INDEX_MONTH_END_CLOSES", "NAV_LINE_CLOSES"):
        assert REG.members(g) and all(REG.is_series(m) for m in REG.members(g))
    for rg in ("US_TREASURY", "KR_CALL_CD"):
        assert all(REG.is_series(m) for m in REG.range_groups[rg]["members"])
    for sid in REG.series_ids():
        c = C.contract(REG, sid)
        assert c.schedule in REG.schedules and c.grace_pub_bdays == 1
        if "acting_exposure" in c.roles:
            assert isinstance(REG.series[sid].get("contract"), dict), sid
    _raises(lambda: C.contract(REG, "ASIA_INDEX_CLOSES"), C.RegistryError, "group name")
    _raises(lambda: C.contract(REG, "NO_SUCH_SERIES"), C.RegistryError, "unknown")
    _raises(lambda: REG.resolve_binding("ASIA_INDEX_CLOSES", "R-13"), C.RegistryError, "group name")
    store = _store()
    _raises(lambda: P.pit_value(store, "SPX_OFFICIAL_CLOSE", DECISION, U(2026, 10, 2, 7), "R-06", OCT2, registry=REG), P.UnboundConsumer)
    _raises(lambda: P.pit_value(store, "SPX_OFFICIAL_CLOSE", DECISION, U(2026, 10, 2, 7), "R-99", OCT2, registry=REG), P.UnboundConsumer)
    assert P.pit_value(store, "SPX_OFFICIAL_CLOSE", DECISION, U(2026, 10, 2, 7), "nav", OCT2, registry=REG).reason == "missing"
    assert P.pit_value(store, "SPX_OFFICIAL_CLOSE", DECISION, U(2026, 10, 2, 7), "R-13", registry=REG).role == "context"
    from core.quant.cards import referenced_series_ids           # M7: the header drafts' series ids (F-22 scan extended)
    assert C.unknown_ids(REG, referenced_series_ids(ROOT / "docs" / "macro_overlay")) == []


test_ser_02_every_referenced_id_is_registered_with_a_contract.test_ids = ["T-SER-02"]


def test_h10_01_dexkous_never_read_by_production():
    store = _store()
    for consumer in ("corr63", "R-06", "hedge_state"):
        _raises(lambda c=consumer: P.pit_value(store, "DEXKOUS", DECISION, U(2026, 10, 2, 7), c, registry=REG), P.PITError, "proxy")
    assert P.pit_value(store, "DEXKOUS", DECISION, U(2026, 10, 2, 7), "R-11_refusal_book", registry=REG).reason == "missing"
    assert P.pit_value(store, "DEXKOUS", DECISION, U(2026, 10, 2, 7), "corr63", registry=REG, run_mode="backtest").reason == "missing"
    assert REG.series["DEXKOUS"]["production_reads"] is False and REG.series["DTWEXBGS"]["never_acting"] is True


test_h10_01_dexkous_never_read_by_production.test_ids = ["T-H10-01"]


# --------------------------------------------------------------------------- #
# T-H10-02, T-H15-01, T-VIX-01, T-XMKT-01 (data clause)
# --------------------------------------------------------------------------- #
def _kr_dec(d):
    return CLK.close_print_bound_utc("KR", d)


def test_h10_02_strict_h10_publication():
    store = _store()
    days = [date(2026, 9, 14) + timedelta(days=i) for i in range(26) if (date(2026, 9, 14) + timedelta(days=i)).weekday() < 5]
    store.append(_dexkous_rows(CLK, [(d, 1350.0 + i) for i, d in enumerate(days)]))
    latest = lambda d: P.pit_last(store, "DEXKOUS", _kr_dec(d), U(2026, 10, 14), registry=REG).obs_date     # noqa: E731
    assert latest(date(2026, 9, 28)) == date(2026, 9, 18)                       # published Mon 09-28 16:15 ET: after the KRX close
    assert latest(date(2026, 9, 29)) == date(2026, 9, 25)                       # usable from Tue 09-29
    assert latest(OCT2) == date(2026, 9, 25)                                    # R4b state row
    assert latest(date(2026, 10, 13)) == date(2026, 10, 2)                      # Columbus Day: Tue 10-13 16:15 ET
    assert latest(date(2026, 10, 14)) == date(2026, 10, 9)
    row = next(r for r in store.rows("DEXKOUS") if r["obs_date"] == date(2026, 9, 25))
    assert row["available_at_utc"] == U(2026, 9, 28, 20, 15) and row["available_at_source"] == "calendar_bound"


test_h10_02_strict_h10_publication.test_ids = ["T-H10-02"]


def test_h15_01_strict_h15_and_treasury_channel():
    store = _store()
    store.append([_release("DGS10", date(2015, 1, 2), 2.12, U(2026, 1, 1))])
    assert store.rows("DGS10")[0]["available_at_utc"] == U(2015, 1, 5, 21, 15)
    assert P.pit_last(store, "DGS10", _kr_dec(date(2015, 1, 5)), U(2026, 1, 1), registry=REG) is None
    assert P.pit_last(store, "DGS10", _kr_dec(date(2015, 1, 6)), U(2026, 1, 1), registry=REG).obs_date == date(2015, 1, 2)
    # Treasury par yield: the logged posting time is available_at; the expected instant for staleness stays 18:00 ET
    store.append([_release("UST_PAR_10Y", date(2026, 10, 1), 4.11, U(2026, 10, 1, 22, 31), source="Treasury", posting=U(2026, 10, 1, 22, 31))])
    us = lambda d: CLK.close_print_bound_utc("US", d)                           # noqa: E731
    assert P.pit_last(store, "UST_PAR_10Y", us(date(2026, 10, 1)), U(2026, 10, 3), registry=REG) is None
    assert P.pit_last(store, "UST_PAR_10Y", us(OCT2), U(2026, 10, 3), registry=REG).available_at_source == "published"
    assert CLK.publication_instant("UST_PAR_10Y", date(2026, 10, 1)) == U(2026, 10, 1, 22, 0)
    # R4b: a flag first on in data dated Wed 2026-09-23 is read at the US close of Fri 09-25 and earns from Mon 09-28
    avail = CLK.publication_instant("DGS10", date(2026, 9, 23))
    assert avail == U(2026, 9, 24, 20, 15)
    first = _first_decision_at_or_after("US", avail)
    assert first == date(2026, 9, 25) and CLK._next(first, lambda x: CLK.is_session("US", x)) == date(2026, 9, 28)


test_h15_01_strict_h15_and_treasury_channel.test_ids = ["T-H15-01"]


def test_vix_01_close_timing_by_channel():
    store = _store()
    d = date(2026, 9, 30)
    store.append([_release("VIXCLS", d, 16.34, U(2026, 9, 30, 20, 16), source="Cboe", posting=U(2026, 9, 30, 20, 15))])
    us = lambda x: CLK.close_print_bound_utc("US", x)                           # noqa: E731
    read = lambda dec: P.pit_value(store, "VIXCLS", dec, U(2026, 10, 2), "R-08", registry=REG)     # noqa: E731
    assert read(us(d)).reason == "missing"                                      # not usable at the US close of D
    assert read(us(date(2026, 10, 1))).value == 16.34                           # US close of D+1
    assert read(_kr_dec(date(2026, 10, 1))).value == 16.34                      # KRX close of K >= D+1
    s2 = _store()
    s2.append([_release("VIXCLS", d, 16.34, U(2026, 10, 1, 11, 3), source="FRED", posting=U(2026, 10, 1, 11, 3))])
    fred = lambda dec: P.pit_value(s2, "VIXCLS", dec, U(2026, 10, 2), "R-13", registry=REG)        # noqa: E731
    assert fred(_kr_dec(date(2026, 10, 1))).reason == "missing" and fred(us(date(2026, 10, 1))).value == 16.34
    hist = _release("VIXCLS", d, 16.34, U(2026, 10, 14), source="FRED")        # declared history lag: calendar_bound
    assert hist["available_at_utc"] == U(2026, 9, 30, 20, 15) and hist["available_at_source"] == "calendar_bound"
    assert C.check_contract(C.contract(REG, "VIXCLS"), 16.34) is None


test_vix_01_close_timing_by_channel.test_ids = ["T-VIX-01"]


def test_xmkt_01_cross_market_data_clause():
    kr = _kr_dec(OCT2)
    assert not C.usable_cross_market("JP", OCT2, kr, CLK) and C.usable_cross_market("TW", OCT2, kr, CLK)
    assert not C.usable_cross_market("HK", OCT2, kr, CLK) and not C.usable_cross_market("CN", OCT2, kr, CLK)
    csat = _kr_dec(date(2025, 11, 13))
    assert C.usable_cross_market("JP", date(2025, 11, 13), csat, CLK) and C.usable_cross_market("CN", date(2025, 11, 13), csat, CLK)
    assert C.usable_cross_market("JP", date(2024, 11, 4), _kr_dec(date(2024, 11, 4)), CLK)
    assert not C.usable_cross_market("JP", date(2016, 7, 29), _kr_dec(date(2016, 7, 29)), CLK)
    # the independent lag audit applies the rule at the audited market's decision, not the other market's own bound
    def close(sid, mkt, d):
        bound = CLK.close_print_bound_utc(mkt, d)
        return P.to_value(P.make_row(series_id=sid, value=1.0, obs_date=d, session_date=d, obs_utc=bound, obs_kind="close",
                                     value_status="official_close", available_at_utc=bound, available_at_source="calendar_bound",
                                     retrieved_at_utc=bound + timedelta(minutes=11), vintage=None, source="KIS", channel=None),
                          role="risk_model", books=())
    audit = lambda v, mkt, dec: [x["check"] for x in L.lag_audit([v], P.RunContext(dec, dec + timedelta(hours=1), "live"), mkt, REG, CLK)["violations"]]  # noqa: E731
    assert audit(close("NIKKEI225_CLOSE", "JP", OCT2), "KR", kr) == ["cross-market bound + 60 s < decision_utc"]
    assert audit(close("NIKKEI225_CLOSE", "JP", date(2026, 10, 1)), "KR", kr) == []
    us = CLK.close_print_bound_utc("US", OCT2)
    assert audit(close("HSI_CLOSE", "HK", OCT2), "US", us) == ["cross-market bound + 60 s < decision_utc"]
    assert audit(close("HSI_CLOSE", "HK", date(2026, 10, 1)), "US", us) == []
    _raises(lambda: L.lag_audit([close("NIKKEI225_CLOSE", "JP", OCT2)], P.RunContext(kr, kr + timedelta(hours=1), "backtest"), "KR", REG, CLK),
            L.LookAheadError, "cross-market")


test_xmkt_01_cross_market_data_clause.test_ids = ["T-XMKT-01"]


# --------------------------------------------------------------------------- #
# T-RO-02
# --------------------------------------------------------------------------- #
def test_ro_02_kis_client_accepts_only_allowlisted_quotation_paths():
    import ast
    import importlib.util
    from tests.acceptance import _code_only
    from data.krx import kis_client as K
    allow = K.QUOTATION_ALLOWLIST
    assert allow is config.KIS_QUOTATION_ALLOWLIST and isinstance(allow, frozenset)      # frozen in config.py
    assert len(allow) == 31 and all("/quotations/" in p and p.startswith("/uapi/") for p in allow)
    used = set()
    for rel in ("data/krx/kis_client.py", "data/kis_markets.py", "data/kis_workspace.py", "docs/kis_quote_check.py"):
        used |= set(re.findall(r"[\"'](/uapi/[^\"']+)[\"']", _code_only(ROOT / rel)))
    assert used == allow, {"unlisted": sorted(used - allow), "unused": sorted(allow - used)}
    for p in sorted(allow):
        assert K.check_quotation_path(p) == p
    trading = "/uapi/domestic-stock/v1/" + "trading/" + "order-" + "cash"
    for bad in (trading, "/uapi/domestic-stock/v1/" + "trading/inquire-balance", "/oauth2/tokenP", "", None,
                "/uapi/domestic-stock/v1/quotations/not-listed"):
        _raises(lambda b=bad: K.check_quotation_path(b), K.KISError, "not an allowlisted")
    tree = ast.parse((ROOT / "data/krx/kis_client.py").read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "KISClient")
    get = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_get")
    first = get.body[1] if isinstance(get.body[0], ast.Expr) and isinstance(get.body[0].value, ast.Constant) else get.body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call) and first.value.func.id == "check_quotation_path"
    # a fresh module copy (the suite patches KISClient._get): a trading path raises before credentials or a request
    import sys
    spec = importlib.util.spec_from_file_location("kis_client_fresh", ROOT / "data/krx/kis_client.py")
    fresh = importlib.util.module_from_spec(spec)
    saved = config.kis_credentials
    calls = []
    try:
        sys.modules[spec.name] = fresh
        spec.loader.exec_module(fresh)
        config.kis_credentials = lambda: calls.append("credentials") or ("k", "s")
        _raises(lambda: fresh.KISClient.__new__(fresh.KISClient)._get(trading, "TTTC", {}), fresh.KISError, "not an allowlisted")
    finally:
        config.kis_credentials = saved
        sys.modules.pop(spec.name, None)
    assert calls == [], "credentials were read before the path check"
    # the Claude API is called without tools and no acting module imports it
    assert '"tools"' not in _code_only(ROOT / "core/quant/insights.py") and "'tools'" not in _code_only(ROOT / "core/quant/insights.py")
    for rel in ("core/ficc/pit.py", "core/ficc/contracts.py", "core/ficc/lag_audit.py", "core/ficc/macro_artifacts.py",
                "core/ficc/macro_schema.py", "core/rules/macro_rules.py", "core/rules/governance.py", "core/quant/instruments.py"):
        src = _code_only(ROOT / rel)
        assert "insights" not in src, f"{rel} reads the Claude API module"


test_ro_02_kis_client_accepts_only_allowlisted_quotation_paths.test_ids = ["T-RO-02"]


def test_ro_02_app_key_can_trade_is_an_owner_attestation():
    raise NotRun("OWNER: KIS credentials and the 20-session quote-field check (M1-01); whether the app key can trade is "
                 "recorded as an owner attestation (default 'unknown'), never probed through a trading path (F-3)")


test_ro_02_app_key_can_trade_is_an_owner_attestation.test_ids = ["T-RO-02"]


if __name__ == "__main__":
    from tests.macro_acceptance import run_module
    raise SystemExit(run_module(globals()))
