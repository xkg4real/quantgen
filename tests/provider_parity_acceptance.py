"""Suite `provider_parity`: tools/provider_parity/parity_check.py (spec 2026-10-26 section 10.5, roadmap item 5-2).

Synthetic series and mocked HTTP only: every test runs with socket connects and the tool's own HTTP layer patched to
raise, so a test that reached the network would fail (the one case that runs the tool's HTTP function replaces
`urlopen`). No real price, rate, pilot table or key is read; every file is written into a fresh folder under the
system temp dir. In the repository the suite reads the tool, its guide and its section of docs/compliance/FACTS.md
(the documents are held to the tool), and the root README.md and tests/run_all.py (to see that they do not name it).

    python -B -m unittest tests.provider_parity_acceptance -v     # `load_tests` below hands unittest the same cases
    python -B -m tests.provider_parity_acceptance                 # the same cases, one PASS or FAIL line each

The suite is not registered in tests/run_all.py (the owner has not asked for that); CI runs the unittest command.

Covered: every outcome (PASS, FAIL, WARN, WITHHELD, REFUSED, ERROR) for SPY, BTC-USD and DGS3MO; each threshold of
10.5.1 on both sides (a case inside it and a case outside it); the late-starting provider rule (P-D5); the 2027-01-01
cut-off in fetch and compare; md5 refusal; the 10.5.2 summary allow-list; that no key value is ever printed or
written; every fetcher over a fake transport, against request parameters, epoch seconds and rows typed by hand; the
tool's own HTTP function with `urlopen` replaced; COMPUTES against the checks (selftest); where the tool may write
(letter case, links, nested folders, OneDrive); a fetch record's sha256; what a failed run prints and leaves; a cp949
console; UTF-8 and LF in every file the tool writes; the tool run as the owner runs it (`python -B -m ...`).
"""
from __future__ import annotations

import calendar
import contextlib
import email.message
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.provider_parity import parity_check as pc  # noqa: E402

NOW = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
REAL_URLLIB_GET = pc.urllib_get            # the tool's own HTTP function, kept before `no_network` replaces it
GUIDE = ROOT / "tools" / "provider_parity" / "README.md"
FACTS = ROOT / "docs" / "compliance" / "FACTS.md"
FMP_KEY, KIS_KEY, KIS_SECRET = "fmpKEY-7f3a9c", "kisAPPKEY-51d2", "kisSECRET-88e0"


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #
@contextlib.contextmanager
def no_network():
    """Socket connects and the tool's default HTTP layer raise for the duration of one test."""
    def refuse(*_a, **_k):
        raise AssertionError("a provider_parity test reached for the network")
    saved = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection, pc.urllib_get)
    socket.socket.connect = socket.socket.connect_ex = refuse
    socket.create_connection = refuse
    pc.urllib_get = refuse
    try:
        yield
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.create_connection, pc.urllib_get = saved


@contextlib.contextmanager
def env_without(*names):
    """The named keys out of the process environment (config.py's load_dotenv may have put them there)."""
    saved = {n: os.environ.pop(n, None) for n in names}
    try:
        yield
    finally:
        for n, v in saved.items():
            if v is not None:
                os.environ[n] = v


def tmp() -> Path:
    root = Path(tempfile.mkdtemp(prefix="pp_test_")).resolve()
    assert not pc.inside_git_worktree(root), f"{root} lies inside a git work tree; set TMPDIR elsewhere"
    assert not pc.in_synced_folder(root), f"{root} lies inside a OneDrive folder; set TMPDIR elsewhere"
    return root


def capture(fn) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn()
    return code, buf.getvalue()


def weekdays(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(k)).isoformat() for k in range((d1 - d0).days + 1) if (d0 + timedelta(k)).weekday() < 5]


def alldays(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(k)).isoformat() for k in range((d1 - d0).days + 1)]


def spy_like(seed: int = 7, lo: str = "2009-06-01", hi: str = "2016-12-30", *, rate: float = 0.0045,
             special: dict | None = None):
    """Weekday sessions, a 2-decimal raw close with four dividends a year, and the backward total-return adjustment a
    Yahoo-style adjusted close applies (factor 1 - D / P_prev before each ex-date). `rate` is each dividend as a share
    of the prior close; `special` gives single ex-dates their own rate. Synthetic: no real SPY value."""
    rng = np.random.default_rng(seed)
    days = weekdays(lo, hi)
    ex = set()
    for y in range(int(lo[:4]), int(hi[:4]) + 1):
        for m in (3, 6, 9, 12):
            later = [d for d in days if d >= f"{y}-{m:02d}-15"]
            if later:
                ex.add(later[0])
    raw, div, p = np.empty(len(days)), np.zeros(len(days)), 100.0
    for i, d in enumerate(days):
        if i:
            p = p * (1.0 + rng.normal(0.0003, 0.011))
            if d in ex:
                div[i] = round((special or {}).get(d, rate) * raw[i - 1], 2)
                p -= div[i]
        raw[i] = round(p, 2)
    return days, raw, adjust(raw, div), div


def adjust(raw, div):
    factor, f = np.ones(len(raw)), 1.0
    for i in range(len(raw) - 1, -1, -1):
        factor[i] = f
        if div[i] > 0:
            f *= 1.0 - div[i] / raw[i - 1]
    return raw * factor


def btc_like(seed: int = 11, lo: str = "2015-01-01", hi: str = "2019-12-31"):
    rng = np.random.default_rng(seed)
    days = alldays(lo, hi)
    p = 300.0 * np.exp(np.cumsum(rng.normal(0.001, 0.04, len(days))))
    return days, p, p * np.exp(rng.normal(0.0, 0.001, len(days)))


def rf_like(seed: int = 5, lo: str = "2009-04-01", hi: str = "2016-12-30"):
    rng = np.random.default_rng(seed)
    days = weekdays(lo, hi)
    vals = np.round(np.clip(np.cumsum(rng.normal(0.0, 0.03, len(days))) + 1.2, 0.0, 6.0), 2)
    return days, vals, set(rng.choice(len(days), size=60, replace=False).tolist())


SPY, BTC, RF = spy_like(), btc_like(), rf_like()
SPY_WIN, BTC_WIN, RF_WIN = ("2010-01-04", "2016-12-30"), ("2015-01-01", "2019-12-31"), ("2010-01-04", "2016-12-30")


def pinned_text(header: str, days, vals) -> str:
    """The shape pandas writes for the study's cache: a header, then date,value with repr floats; NaN blank."""
    rows = [header] + [f"{d},{'' if not np.isfinite(v) else repr(float(v))}" for d, v in zip(days, vals)]
    return "\n".join(rows) + "\n"


def provider_text(days, vals, decimals: int | None = None) -> str:
    fmt = (lambda v: f"{v:.{decimals}f}") if decimals is not None else (lambda v: repr(float(v)))
    return "date,value\n" + "".join(f"{d},{fmt(v)}\n" for d, v in zip(days, vals))


class World:
    """A fake research clone (a .git folder, a pilot table, a synthetic pinned file) and provider files, in temp."""

    def __init__(self, series: str, a_text: str, *, start: str, end: str, table_extra: dict | None = None):
        self.root = tmp()
        self.repo = self.root / "repo"
        (self.repo / ".git").mkdir(parents=True)
        symbol, fkey, mkey, name = pc.PINNED[series]
        rel = f"synthetic/{name}"
        (self.repo / "synthetic").mkdir()
        (self.repo / rel).write_bytes(a_text.encode("utf-8"))
        table = {"schema": pc.TABLE_SCHEMA, "symbol": symbol, "start": start, "end": end,
                 "prices_file": None, "prices_md5": None, "rf_file": None, "rf_md5": None,
                 fkey: rel, mkey: hashlib.md5(a_text.encode("utf-8")).hexdigest(), **(table_extra or {})}
        self.table = self.repo / "docs" / "nautilus_bridge" / "registration" / f"{series}.json"
        self.table.parent.mkdir(parents=True)
        self.table.write_text(json.dumps(table), encoding="utf-8")
        self.series, self.n = series, 0

    def file(self, name: str, text: str) -> Path:
        path = self.root / "providers" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def out(self) -> Path:
        self.n += 1
        return self.root / "out" / f"run{self.n:02d}"

    def compare(self, pairs, unavailable=None, *, out: Path | None = None, extra=()):
        argv = ["compare", "--series", self.series, "--table", str(self.table), "--repo", str(self.repo)]
        for p, f in pairs:
            argv += ["--pair", p, str(f)]
        argv += account(self.series, [p for p, _ in pairs]) if unavailable is None else unavailable
        out = out or self.out()
        code, text = capture(lambda: pc.run([*argv, "--out", str(out), *extra], now=NOW))
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8")) if (out / "summary.json").exists() \
            else None
        return code, text, summary, out


def account(series: str, given: list[str]) -> list[str]:
    """`--unavailable <p> fetch_failed` for each required provider a case does not compare."""
    out = []
    for p, (_, _, required) in pc.PROVIDERS[series].items():
        if required and p not in given:
            out += ["--unavailable", p, "fetch_failed"]
    return out


def check_of(summary: dict, provider: str, cid: str) -> dict:
    pair = next(p for p in summary["pairs"] if p["provider"] == provider)
    return next(c for c in pair["checks"] if c["id"] == cid)


def last_line(text: str) -> str:
    return text.strip().splitlines()[-1]


def spy_world(adj=None, days=None, a_extra: str = "") -> World:
    d0, _, adj0, _ = SPY
    text = pinned_text("Date,yf_SPY", d0 if days is None else days, adj0 if adj is None else adj)
    if a_extra:
        lines = text.splitlines(keepends=True)
        text = lines[0] + a_extra + "".join(lines[1:])
    return World("spy", text, start=SPY_WIN[0], end=SPY_WIN[1])


def spy_b(w: World):
    d0, raw0, adj0, _ = SPY
    return (w.file("spy_fmp.csv", provider_text(d0, adj0 * 0.987, 6)),
            w.file("spy_kis.csv", provider_text(d0, raw0, 2)),
            w.file("spy_yahoo_now.csv", provider_text(d0, adj0 * 0.99, 6)))


# --------------------------------------------------------------------------- #
# SPY
# --------------------------------------------------------------------------- #
def test_spy_clean_pairs_pass():
    w = spy_world()
    fmp, kis, yahoo = spy_b(w)
    code, out, s, _ = w.compare([("fmp", fmp), ("kis", kis), ("yahoo_now", yahoo)])
    assert code == 0 and s["outcome"] == "PASS" and last_line(out).startswith("PARITY spy PASS exit=0 summary="), out
    adj = check_of(s, "kis", "adjustment_convention")
    assert adj["outcome"] == "PASS" and adj["n_full_years"] == 7 and adj["n_years_expected_ex_days"] == 7, adj
    same = check_of(s, "fmp", "returns_same_convention")
    assert same["n_over_tol"] == 0 and same["max_ok"] and same["drift_ok"], same
    assert s["withheld_reasons"] == [] and s["n_a_outside_evidence_spans"] == 0, s
    assert {p["provider"]: p["role"] for p in s["pairs"]} == {"fmp": "independent", "kis": "cross",
                                                             "yahoo_now": "vintage"}


def test_spy_price_only_file_as_total_fails():
    d0, raw0, _, _ = SPY
    w = spy_world()
    b = w.file("price_as_total.csv", provider_text(d0, raw0, 2))
    code, out, s, _ = w.compare([("fmp", b)])
    same = check_of(s, "fmp", "returns_same_convention")
    assert code == 1 and s["outcome"] == "FAIL" and same["n_over_tol"] >= 20 and not same["drift_ok"], same
    assert last_line(out).startswith("PARITY spy FAIL exit=1"), out


def test_spy_missing_session_in_a_fails_with_its_date():
    d0, _, adj0, _ = SPY
    drop = d0.index("2013-05-15")
    w = spy_world(adj=np.delete(adj0, drop), days=d0[:drop] + d0[drop + 1:])
    fmp, _, _ = spy_b(w)
    code, _, s, _ = w.compare([("fmp", fmp)])
    cal = check_of(s, "fmp", "calendar")
    assert code == 1 and cal["outcome"] == "FAIL" and cal["only_b"] == ["2013-05-15"] and cal["n_only_a"] == 0, cal


def test_spy_bad_tick_in_provider_fails():
    d0, _, adj0, _ = SPY
    bt = adj0 * 0.987
    bt[d0.index("2014-02-12")] *= 1.02
    w = spy_world()
    code, _, s, _ = w.compare([("fmp", w.file("tick.csv", provider_text(d0, bt, 6)))])
    same = check_of(s, "fmp", "returns_same_convention")
    assert code == 1 and same["n_over_tol"] == 2 and same["max_abs_bucket"] == "<=1e-01" and not same["max_ok"], same


def test_spy_two_missed_dividend_adjustments_in_one_year_fail():
    d0, raw0, _, div0 = SPY
    div = div0.copy()
    for i in [i for i, d in enumerate(d0) if d.startswith("2012") and div[i] > 0][:2]:
        div[i] = 0.0
    w = spy_world(adj=adjust(raw0, div))
    _, kis, _ = spy_b(w)
    code, _, s, _ = w.compare([("kis", kis)])
    adj = check_of(s, "kis", "adjustment_convention")
    assert code == 1 and adj["n_years_off_more"] == 1 and adj["outcome"] == "FAIL", adj


def test_spy_one_missed_dividend_adjustment_warns_the_pair_and_passes_the_series():
    """ex_days_per_year 4: three (or five) in one year is WARN, and a WARN never fails the series."""
    d0, raw0, _, div0 = SPY
    div = div0.copy()
    div[next(i for i, d in enumerate(d0) if d.startswith("2012") and div[i] > 0)] = 0.0
    w = spy_world(adj=adjust(raw0, div))
    _, kis, _ = spy_b(w)
    code, out, s, _ = w.compare([("kis", kis)])
    adj = check_of(s, "kis", "adjustment_convention")
    assert adj["outcome"] == "WARN" and adj["n_years_off_by_one"] == 1 and adj["n_years_off_more"] == 0, adj
    assert code == 0 and s["outcome"] == "PASS" and s["pairs"][0]["outcome"] == "WARN", out


def spy_cross(rate: float = 0.0045, special: dict | None = None):
    """A total-return file and its split-only twin from one synthetic path with the given dividends, compared."""
    days, raw, adj, _ = spy_like(rate=rate, special=special)
    w = World("spy", pinned_text("Date,yf_SPY", days, adj), start=SPY_WIN[0], end=SPY_WIN[1])
    code, out, s, _ = w.compare([("kis", w.file("spy_kis.csv", provider_text(days, raw, 2)))])
    return code, out, s, check_of(s, "kis", "adjustment_convention")


def test_spy_ex_dividend_gap_above_ex_gap_max_fails():
    """ex_gap_max 2e-2: one dividend of 2.2% of the price is too large for a quarterly SPY dividend. That year's gap
    sum stays inside the yield band, so the too-large gap alone fails the pair; 1.5% is inside the limit."""
    ex_day = next(d for d in SPY[0] if d >= "2013-06-15")
    code, out, s, adj = spy_cross(special={ex_day: 0.022})
    assert adj["n_too_large_gap_days"] == 1 and adj["yield_band_ok"] is True and adj["n_years_off_more"] == 0, adj
    assert code == 1 and adj["outcome"] == "FAIL" and s["outcome"] == "FAIL", out
    code, out, s, adj = spy_cross(special={ex_day: 0.015})
    assert code == 0 and adj["outcome"] == "PASS" and adj["n_too_large_gap_days"] == 0 and adj["yield_band_ok"], adj


def test_spy_yearly_gap_sum_outside_the_yield_band_fails():
    """yield_band [0.005, 0.04]: four dividends of 1.2% a year sum above it and four of 0.1% below it. No single gap
    is above ex_gap_max and every year has its four ex-dates, so the band alone fails the pair. Only the boolean
    leaves the machine, never the sum."""
    for rate in (0.012, 0.001):
        code, out, s, adj = spy_cross(rate=rate)
        assert adj["yield_band_ok"] is False and adj["n_too_large_gap_days"] == 0, (rate, adj)
        assert adj["n_years_expected_ex_days"] == adj["n_full_years"] == 7 and adj["outcome"] == "FAIL", (rate, adj)
        assert code == 1 and s["outcome"] == "FAIL", out


def test_spy_negative_gaps_up_to_the_allowance_pass_one_more_fails():
    """A day on which the split-only provider's return is above the total-return file's by more than ex_gap_min is a
    negative gap day: up to max(ret_diff_floor_days, ret_diff_share_max x days) are allowed."""
    d0, raw0, _, div0 = SPY
    w = spy_world()
    _, kis, _ = spy_b(w)
    adj = check_of(w.compare([("kis", kis)])[2], "kis", "adjustment_convention")
    allowed = adj["n_allowed"]
    quiet = [i for i in range(200, len(d0), 97) if div0[i] == 0.0]       # sessions inside the window, not ex-dates
    assert allowed == 9 == int(0.005 * (len([d for d in d0 if d >= SPY_WIN[0]]) - 1)) and len(quiet) > allowed, adj
    for k, want, code_want in ((allowed, "PASS", 0), (allowed + 1, "FAIL", 1)):
        stepped = raw0.copy()
        for i in quiet[:k]:
            stepped[i:] *= 1.001                                         # a level step: one return 0.1% higher
        code, _, s, _ = w.compare([("kis", w.file(f"kis_{k}.csv", provider_text(d0, stepped, 6)))])
        adj = check_of(s, "kis", "adjustment_convention")
        assert adj["n_negative_gap_days"] == k and adj["outcome"] == want and code == code_want, (k, adj)
        assert adj["n_years_off_more"] == 0 and adj["n_years_off_by_one"] == 0 and adj["yield_band_ok"], adj


def test_spy_disagreement_days_up_to_the_allowance_pass_one_more_fails():
    """ret_diff_tol 2e-4, ret_diff_floor_days 5, ret_diff_share_max 0.005: days above the tolerance are allowed up to
    max(5, 0.5% of the compared days). Each difference stays below ret_diff_max and the drift inside its range, so the
    count alone decides."""
    d0, _, adj0, _ = SPY
    w = spy_world()
    fmp, _, _ = spy_b(w)
    same = check_of(w.compare([("fmp", fmp)])[2], "fmp", "returns_same_convention")
    allowed = same["n_allowed"]
    quiet = list(range(200, len(d0), 97))
    assert allowed == 9 == int(0.005 * same["n_days"]) and same["n_days"] == 1824, same       # the share, not the floor
    for k, want, code_want in ((allowed // 2, "PASS", 0), (allowed // 2 + 1, "FAIL", 1)):
        b = adj0 * 0.987
        for i in quiet[:k]:
            b[i] *= 1.0005                                               # one close 0.05% off: two days above 2e-4
        code, _, s, _ = w.compare([("fmp", w.file(f"fmp_{k}.csv", provider_text(d0, b, 6)))])
        same = check_of(s, "fmp", "returns_same_convention")
        assert same["n_over_tol"] == 2 * k and same["max_ok"] and same["drift_ok"], (k, same)
        assert same["outcome"] == want and code == code_want, (k, same)


def test_spy_short_window_allows_the_floor_of_five_disagreement_days():
    """ret_diff_floor_days 5: on a one-year window 0.5% of the days is one day, so the floor of five decides."""
    d0, _, adj0, _ = SPY
    win = ("2012-01-03", "2012-12-31")
    w = World("spy", pinned_text("Date,yf_SPY", d0, adj0), start=win[0], end=win[1])
    inside = [i for i, d in enumerate(d0) if win[0] <= d <= win[1]]
    for k, want, code_want in ((2, "PASS", 0), (3, "FAIL", 1)):
        b = adj0 * 0.987
        for i in inside[40::40][:k]:
            b[i] *= 1.0005
        code, _, s, _ = w.compare([("fmp", w.file(f"fmp_short_{k}.csv", provider_text(d0, b, 6)))])
        same = check_of(s, "fmp", "returns_same_convention")
        assert same["n_allowed"] == 5 and int(0.005 * same["n_days"]) == 1 and same["n_over_tol"] == 2 * k, same
        assert same["outcome"] == want and code == code_want, (k, same)


def test_spy_gaps_below_ex_gap_min_are_rounding_noise_not_dividends():
    """ex_gap_min 5e-4: a return gap of 3e-4, the size a one-cent rounding makes, is neither an ex-dividend day nor a
    negative gap day, however many there are."""
    d0, raw0, _, div0 = SPY
    w = spy_world()
    noisy = raw0.copy()
    quiet = [i for i in range(200, len(d0), 61) if div0[i] == 0.0 and div0[i + 1] == 0.0]
    assert len(quiet) > 20
    for i in quiet:
        noisy[i] *= 1.0003                                               # gaps of -3e-4 and +3e-4 on two days
    code, out, s, _ = w.compare([("kis", w.file("kis_noisy.csv", provider_text(d0, noisy, 6)))])
    adj = check_of(s, "kis", "adjustment_convention")
    assert adj["n_negative_gap_days"] == 0 and adj["n_years_expected_ex_days"] == adj["n_full_years"] == 7, adj
    assert adj["outcome"] == "PASS" and code == 0 and s["outcome"] == "PASS", out


def test_spy_provider_lacking_half_a_percent_of_sessions_fails_the_calendar_not_coverage():
    """coverage_min 0.99 for SPY: a provider that has 99.5% of A's sessions inside its span is evaluated, and the
    sessions it lacks then fail the calendar check with their dates: FAIL, not WITHHELD."""
    d0, _, adj0, _ = SPY
    lacking = [i for i in range(len(d0)) if i % 200 == 100 and d0[i] >= SPY_WIN[0]]
    keep = [i for i in range(len(d0)) if i not in set(lacking)]
    w = spy_world()
    code, out, s, _ = w.compare([("fmp", w.file("fmp_gaps.csv", provider_text([d0[i] for i in keep],
                                                                               (adj0 * 0.987)[keep], 6)))])
    cov, cal = check_of(s, "fmp", "coverage"), check_of(s, "fmp", "calendar")
    assert cov["outcome"] == "PASS" and cov["coverage_ok"] and cov["n_a"] - cov["n_common"] == len(lacking) == 9, cov
    assert cal["outcome"] == "FAIL" and cal["only_a"] == [d0[i] for i in lacking] and cal["n_only_b"] == 0, cal
    assert code == 1 and s["outcome"] == "FAIL", out


def test_spy_split_shaped_jump_in_a_fails_the_series_by_integrity_alone():
    """jump_abs_max 0.25: a one-day move of A above it is a split-shaped error. The provider carries the same step, so
    the pair agrees and A's own integrity check is what fails the series (10.5.1)."""
    d0, _, adj0, _ = SPY
    j = d0.index("2013-05-15")
    for step, want, code_want in ((1.15, "PASS", 0), (1.40, "FAIL", 1)):
        a = adj0.copy()
        a[j:] *= step
        w = spy_world(adj=a)
        code, out, s, _ = w.compare([("fmp", w.file("fmp_step.csv", provider_text(d0, a * 0.987, 6)))])
        integ = s["integrity"][0]
        assert integ["id"] == "integrity_a" and integ["outcome"] == want, (step, integ)
        assert integ["no_split_shaped_jump"] is (want == "PASS") and s["pairs"][0]["outcome"] == "PASS", s
        assert code == code_want and s["outcome"] == want, out


def test_spy_weekend_date_in_a_fails_the_calendar():
    """A US equity session never falls on a weekend. The provider carries the same row, so neither side has a date
    the other lacks and the weekend rule alone fails the calendar check."""
    d0, _, adj0, _ = SPY
    f = d0.index("2013-05-17")
    assert date.fromisoformat(d0[f]).weekday() == 4
    days = d0[:f + 1] + ["2013-05-18"] + d0[f + 1:]
    vals = np.insert(adj0, f + 1, adj0[f])
    w = spy_world(adj=vals, days=days)
    code, out, s, _ = w.compare([("fmp", w.file("fmp_sat.csv", provider_text(days, vals * 0.987, 6)))])
    cal = check_of(s, "fmp", "calendar")
    assert cal["n_weekend_a"] == 1 and cal["n_only_a"] == 0 and cal["n_only_b"] == 0 and cal["outcome"] == "FAIL", cal
    assert code == 1 and s["outcome"] == "FAIL", out


def test_spy_late_starting_provider_five_sessions_pass_six_withheld():
    """edge_uncovered_max 5 for SPY: the whole window has to be compared, so a provider may lack at most five of A's
    sessions outside its own first-to-last span (P-D5)."""
    d0, _, adj0, _ = SPY
    first = d0.index(SPY_WIN[0])
    for skip, want, code_want in ((5, "PASS", 0), (6, "WITHHELD", 3)):
        w = spy_world()
        b = w.file("fmp_late.csv", provider_text(d0[first + skip:], adj0[first + skip:] * 0.987, 6))
        code, out, s, _ = w.compare([("fmp", b)])
        cov = check_of(s, "fmp", "coverage")
        assert cov["n_a_outside_b_span"] == skip and cov["outcome"] == want, cov
        assert cov["coverage_ok"] is (want == "PASS") and code == code_want and s["outcome"] == want, out
        if want == "PASS":
            assert s["n_a_outside_evidence_spans"] == skip and cov["first_date"] == d0[first + skip], s


def test_spy_vintage_disagreement_warns_and_never_fails_the_series():
    """10.5.1: a vintage pair reports FAIL as WARN. A re-fetch that disagrees with the pinned file shows in the
    summary, and the series outcome stays with the independent and cross pairs."""
    d0, raw0, _, _ = SPY
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    code, out, s, _ = w.compare([("fmp", fmp), ("kis", kis),
                                 ("yahoo_now", w.file("yahoo_price_only.csv", provider_text(d0, raw0, 2)))])
    same = check_of(s, "yahoo_now", "returns_same_convention")
    assert same["outcome"] == "WARN" and same["kind"] == "warn" and same["drift_ok"] is False, same
    assert code == 0 and s["outcome"] == "PASS", out
    assert {p["provider"]: p["outcome"] for p in s["pairs"]} == {"fmp": "PASS", "kis": "PASS", "yahoo_now": "WARN"}


def test_spy_provider_with_next_day_labels_is_never_evaluated_in_full():
    """Korean-date labels put about one A session in five off B's calendar: coverage falls below 0.99, the pair is
    WITHHELD before any return is compared, and with no other independent or cross pair the series is WITHHELD."""
    d0, _, adj0, _ = SPY
    shifted = [(date.fromisoformat(d) + timedelta(days=1)).isoformat() for d in d0]    # the next day's label
    w = spy_world()
    code, _, s, _ = w.compare([("fmp", w.file("kst.csv", provider_text(shifted, adj0 * 0.987, 6)))])
    cov = check_of(s, "fmp", "coverage")
    assert code == 3 and s["outcome"] == "WITHHELD" and cov["outcome"] == "WITHHELD" and cov["coverage_ok"] is False
    assert [c["id"] for c in s["pairs"][0]["checks"]] == ["coverage"], s["pairs"][0]


def test_spy_calendar_lists_are_capped_at_100_dates():
    d0, _, adj0, _ = SPY
    extra = sorted(set(alldays("2011-01-01", "2012-12-31")) - set(d0))[:150]      # weekend dates B also carries
    days = sorted(set(d0) | set(extra))
    vals = np.interp([date.fromisoformat(d).toordinal() for d in days],
                     [date.fromisoformat(d).toordinal() for d in d0], adj0 * 0.987)
    w = spy_world()
    code, _, s, _ = w.compare([("fmp", w.file("weekends.csv", provider_text(days, vals, 6)))])
    cal = check_of(s, "fmp", "calendar")
    assert code == 1 and cal["outcome"] == "FAIL" and cal["n_only_b"] == 150 and cal["truncated"] is True, cal
    assert cal["only_b"] == extra[:pc.LIST_CAP] and cal["n_only_a"] == 0, cal


def test_spy_lines_outside_the_window_are_never_parsed():
    w = spy_world(a_extra="2001-01-02,not_a_number\n")
    fmp, _, _ = spy_b(w)
    code, out, s, _ = w.compare([("fmp", fmp)])
    assert code == 0 and s["outcome"] == "PASS", out


def test_refusal_message_never_echoes_file_content():
    w = spy_world(a_extra="2013-05-15,123.45x\n")                 # a bad cell inside the window
    fmp, _, _ = spy_b(w)
    code, out, s, path = w.compare([("fmp", fmp)])
    assert code == 2 and s is None and not path.exists() and "123.45" not in out and "ValueError" in out, out
    assert last_line(out) == "PARITY spy REFUSED exit=2 summary=-", out


def test_spy_without_an_independent_or_cross_pair_is_withheld():
    w = spy_world()
    _, _, yahoo = spy_b(w)
    code, out, s, _ = w.compare([("yahoo_now", yahoo)])
    assert code == 3 and s["outcome"] == "WITHHELD" and last_line(out).startswith("PARITY spy WITHHELD exit=3"), out
    assert s["withheld_reasons"] == ["fmp not compared: fetch_failed", "kis not compared: fetch_failed",
                                     pc.NO_EVIDENCE], s["withheld_reasons"]


def test_md5_mismatch_is_refused_and_writes_nothing():
    w = spy_world()
    fmp, _, _ = spy_b(w)
    table = json.loads(w.table.read_text(encoding="utf-8"))
    table["prices_md5"] = "0" * 32
    w.table.write_text(json.dumps(table), encoding="utf-8")
    code, out, s, path = w.compare([("fmp", fmp)])
    assert code == 2 and s is None and not path.exists() and "md5" in out and "REFUSED" in out, out


def test_pinned_cache_path_is_refused_before_it_is_opened():
    w = spy_world()
    fmp, _, _ = spy_b(w)
    table = json.loads(w.table.read_text(encoding="utf-8"))
    table["prices_file"] = "docs/asset_expansion/cache/yf_SPY.csv"      # not created: the guard comes first
    w.table.write_text(json.dumps(table), encoding="utf-8")
    code, out, s, path = w.compare([("fmp", fmp)])
    assert code == 2 and "--owner-run" in out and not path.exists(), out
    code, out, _, _ = w.compare([("fmp", fmp)], extra=["--owner-run"])
    assert code == 2 and "cannot be read (FileNotFoundError)" in out, out


def test_out_folder_must_be_new_and_outside_every_git_work_tree():
    w = spy_world()
    fmp, _, _ = spy_b(w)
    code, out, _, _ = w.compare([("fmp", fmp)], out=w.repo / "pp_out")              # inside the fake clone
    assert code == 2 and not (w.repo / "pp_out").exists() and "git work tree" in out, out
    existing = w.out()
    existing.mkdir(parents=True)
    code, out, _, _ = w.compare([("fmp", fmp)], out=existing)
    assert code == 2 and "must be new" in out and not any(existing.iterdir()), out


def test_compare_writes_nothing_into_the_research_clone():
    w = spy_world()
    fmp, kis, _ = spy_b(w)

    def tree():
        return {p.relative_to(w.repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(w.repo.rglob("*")) if p.is_file()}
    before = tree()
    code, _, _, out = w.compare([("fmp", fmp), ("kis", kis)])
    assert code == 0 and tree() == before, "the research clone changed"
    assert sorted(p.name for p in out.iterdir()) == ["detail.json", "summary.json"]


def test_summary_never_carries_a_value_even_on_fail():
    d0, raw0, adj0, _ = SPY
    adj = adj0.copy()
    adj[d0.index("2015-07-01")] = 4321.123457                    # a planted marker
    w = spy_world(adj=adj)
    fmp, kis, _ = spy_b(w)
    code, _, s, out = w.compare([("fmp", fmp), ("kis", kis)])
    text = (out / "summary.json").read_text(encoding="utf-8")
    assert code == 1 and "4321.1" not in text, "marker leaked"
    body = {k: v for k, v in s.items() if k != "thresholds"}
    assert not re.search(r"\d\.\d", json.dumps(body)), "a decimal number outside the thresholds block"
    for v in list(adj0[:300]) + list(raw0[:300]):
        assert f"{v:.2f}" not in json.dumps(body), v
    detail = json.loads((out / "detail.json").read_text(encoding="utf-8"))
    assert detail["integrity"]["integrity_a"]["jump_dates"] == ["2015-07-01", d0[d0.index("2015-07-01") + 1]]


def test_summary_allow_list_refuses_anything_outside_10_5_2():
    w = spy_world()
    fmp, kis, yahoo = spy_b(w)
    _, _, good, _ = w.compare([("fmp", fmp), ("kis", kis), ("yahoo_now", yahoo)])
    pc.assert_summary_safe(good)                                  # what the tool wrote passes its own rule

    def refused(mutate) -> bool:
        s = json.loads(json.dumps(good))
        mutate(s)
        try:
            pc.assert_summary_safe(s)
        except pc.SummaryUnsafe:
            return True
        return False
    first = lambda s: s["pairs"][0]["checks"][0]                  # noqa: E731
    bad = {
        "a float in a check": lambda s: first(s).update(max_abs=0.0012),
        "an exact extreme": lambda s: first(s).update(max_abs_bucket="0.0012"),
        "a price key": lambda s: s.update(price=4321),
        "a date under another key": lambda s: first(s).update(worst_day="2015-07-01"),
        "a decimal in a reason": lambda s: s["withheld_reasons"].append("close 101.25"),
        "an integer outside n_*": lambda s: first(s).update(count=3),
        "a float under n_*": lambda s: first(s).update(n_a=3.5),
        "a lag of 2": lambda s: first(s).update(lag=2),
        "a per-lag count": lambda s: first(s).update(n_over_by_lag={"0": 3}),
        "101 dates": lambda s: first(s).update(only_a=[(date(2010, 1, 1) + timedelta(k)).isoformat()
                                                       for k in range(101)]),
        "a 2027 date": lambda s: first(s).update(only_a=["2027-01-04"]),
        "changed thresholds": lambda s: s["thresholds"].update(coverage_min=0.5),
        "a changed provider map": lambda s: s["providers"]["kis"].update(role="vintage"),
        "an unknown provider": lambda s: s["pairs"][0].update(provider="coinbase"),
        "a role outside ROLES": lambda s: s["pairs"][0].update(role="trusted"),
        "a missing top-level key": lambda s: s.pop("withheld_reasons"),
        "a numpy-free bool as int": lambda s: first(s).update(coverage_ok=1),
        "a free-text note": lambda s: s["pinned"].update(note="adjusted"),
    }
    accepted = [name for name, m in bad.items() if not refused(m)]
    assert not accepted, accepted


def test_unsafe_summary_is_refused_and_nothing_is_written():
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    real = pc.build_summary

    def leaky(*a, **k):
        s = real(*a, **k)
        s["pairs"][0]["checks"][0]["max_abs"] = 0.0012
        return s
    pc.build_summary = leaky
    try:
        code, out, s, path = w.compare([("fmp", fmp), ("kis", kis)])
    finally:
        pc.build_summary = real
    assert code == 2 and s is None and not path.exists() and "allow-list" in out and "0.0012" not in out, out


def test_providers_take_their_role_from_the_fixed_map():
    """10.5, Providers: the tool refuses any other provider, and every required provider is compared or declared
    unavailable with a listed reason. Each case is complete but for the one thing its refusal names."""
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    rest = ["--unavailable", "kis", "fetch_failed", "--unavailable", "yahoo_now", "no_key"]
    cases = [("provider 'coinbase' is not one of", ["--pair", "fmp", str(fmp), *rest, "--pair", "coinbase", str(fmp)]),
             ("required provider(s) kis, yahoo_now neither compared", ["--pair", "fmp", str(fmp)]),
             ("a provider is named twice", ["--pair", "fmp", str(fmp), *rest, "--pair", "fmp", str(fmp)]),
             ("a provider is named twice", ["--pair", "fmp", str(fmp), *rest, "--unavailable", "fmp", "no_key"]),
             ("reason 'busy' is not one of", ["--pair", "fmp", str(fmp), "--unavailable", "kis", "busy",
                                              "--unavailable", "yahoo_now", "no_key"])]
    for why, argv in cases:
        code, out, s, path = w.compare([], unavailable=argv)
        assert code == 2 and s is None and not path.exists() and why in out, (why, out)
        assert last_line(out) == "PARITY spy REFUSED exit=2 summary=-", out
    code, out, s, _ = w.compare([("fmp", fmp), ("kis", kis)], unavailable=["--unavailable", "yahoo_now", "no_key"])
    assert code == 0 and s["outcome"] == "PASS", out
    assert s["withheld_reasons"] == ["yahoo_now not compared: no_key"], s["withheld_reasons"]
    assert s["providers"] == {"fmp": {"role": "independent", "convention": "total", "required": True},
                              "kis": {"role": "cross", "convention": "split", "required": True},
                              "yahoo_now": {"role": "vintage", "convention": "total", "required": True}}


def test_a_fetch_folder_of_another_provider_is_refused():
    w = spy_world()
    fmp, _, _ = spy_b(w)
    (fmp.parent / "meta.json").write_text(json.dumps({"schema": pc.FETCH_SCHEMA, "provider": "kis", "series": "spy"}),
                                          encoding="utf-8")
    code, out, _, _ = w.compare([("fmp", fmp)])
    assert code == 2 and "another provider" in out, out


def test_table_checks_refuse_a_wrong_table_or_window():
    w = spy_world()
    fmp, _, _ = spy_b(w)
    original = w.table.read_text(encoding="utf-8")
    cases = {"SPY table for btc": ("btc", {}, "takes the BTC-USD table"),
             "table end in 2027": ("spy", {"end": "2027-01-04"}, "the window reaches 2027-01-01"),
             "another file name": ("spy", {"prices_file": "synthetic/yf_QQQ.csv"}, "relative path to yf_SPY.csv"),
             "a parent path": ("spy", {"prices_file": "../yf_SPY.csv"}, "relative path to yf_SPY.csv"),
             "rf without rf_file": ("rf", {}, "no rf_file"),
             "an md5 that is not one": ("spy", {"prices_md5": "d2164597"}, "prices_md5 is not an md5"),
             "dates out of order": ("spy", {"start": "2016-12-30", "end": "2010-01-04"}, "ISO dates in order"),
             "not a table": ("spy", {"schema": "something-else"}, "not a pilot table")}
    for name, (series, change, why) in cases.items():
        w.table.write_text(json.dumps({**json.loads(original), **change}), encoding="utf-8")
        w.series = series
        code, out, s, path = w.compare([], unavailable=account(series, []))
        assert code == 2 and s is None and not path.exists() and why in out, (name, out)
    w.series = "spy"
    w.table.write_text(original, encoding="utf-8")
    outside = w.root / "table.json"
    outside.write_text(original, encoding="utf-8")
    code, out, _, _ = capture_compare(w, table=outside)
    assert code == 2 and "inside --repo" in out, out
    (w.repo / ".git").rmdir()
    code, out, _, _ = capture_compare(w)
    assert code == 2 and "no .git" in out, out


def test_the_tool_refuses_a_research_clone_that_holds_the_tool_itself():
    """U5 and spec 10.5 (When and where): the tool runs from a separate clone. A --repo that contains the tool is
    refused before any table or file in it is read, so nothing is run from inside the research clone."""
    w = spy_world()
    fmp, _, _ = spy_b(w)
    out = w.out()
    argv = ["compare", "--series", "spy", "--table", str(ROOT / "no_such_table.json"), "--repo", str(ROOT), "--pair",
            "fmp", str(fmp), *account("spy", ["fmp"]), "--out", str(out)]
    code, text = capture(lambda: pc.run(argv, now=NOW))
    assert code == 2 and "separate clone" in text and not out.exists(), text
    assert last_line(text) == "PARITY spy REFUSED exit=2 summary=-", text


def capture_compare(w: World, *, table: Path | None = None):
    fmp = w.root / "providers" / "spy_fmp.csv"
    out = w.out()
    argv = ["compare", "--series", "spy", "--table", str(table or w.table), "--repo", str(w.repo), "--pair", "fmp",
            str(fmp), *account("spy", ["fmp"]), "--out", str(out)]
    code, text = capture(lambda: pc.run(argv, now=NOW))
    return code, text, None, out


def test_a_provider_file_with_a_2027_row_is_refused():
    d0, _, adj0, _ = SPY
    w = spy_world()
    text = provider_text(d0, adj0 * 0.987, 6) + "2027-01-04,123.0\n"
    code, out, s, path = w.compare([("fmp", w.file("late.csv", text))])
    assert code == 2 and s is None and not path.exists() and "2027-01-01" in out and "123.0" not in out, out


# --------------------------------------------------------------------------- #
# BTC-USD
# --------------------------------------------------------------------------- #
def btc_world(a_days=None, a_vals=None) -> World:
    d, p, _ = BTC
    return World("btc", pinned_text("Date,yf_BTC-USD", d if a_days is None else a_days, p if a_vals is None else a_vals),
                 start=BTC_WIN[0], end=BTC_WIN[1])


def btc_run(w: World, b_days, b_vals, provider="coinbase"):
    return w.compare([(provider, w.file(f"btc_{provider}_{w.n}.csv", provider_text(b_days, b_vals, 2)))])


def test_btc_clean_passes():
    d, _, v = BTC
    code, out, s, _ = btc_run(btc_world(), d, v)
    db = check_of(s, "coinbase", "day_boundary")
    assert code == 0 and s["outcome"] == "PASS" and db["lag"] == 0 and db["lag0_strictly_fewest"], out
    lv = check_of(s, "coinbase", "levels_and_returns")
    assert lv["late"]["within_band"] and lv["early"]["within_band"] and lv["late"]["p50_bucket"].startswith("<="), lv


def test_btc_labels_shifted_by_one_day_fail_the_boundary_check():
    d, _, v = BTC
    code, _, s, _ = btc_run(btc_world(), d[1:], v[:-1])          # B labels each day by its closing date
    db = check_of(s, "coinbase", "day_boundary")
    assert code == 1 and db["outcome"] == "FAIL" and db["lag"] == 1 and db["lag0_strictly_fewest"] is False, db


def test_btc_day_boundary_needs_lag_zero_strictly_fewest():
    """day_boundary passes only when shift 0 has strictly the fewest days above ret_diff_big. Two series so quiet that
    no shift has any such day give no evidence about the day boundary: the check fails rather than pass by default."""
    d = alldays(*BTC_WIN)
    rng = np.random.default_rng(12)
    quiet = 300.0 * np.exp(np.cumsum(rng.normal(0.0, 0.001, len(d))))
    code, out, s, _ = btc_run(btc_world(a_vals=quiet), d, quiet * np.exp(rng.normal(0.0, 0.0002, len(d))))
    db = check_of(s, "coinbase", "day_boundary")
    assert db["lag"] == 0 and db["lag0_strictly_fewest"] is False and db["outcome"] == "FAIL", db
    assert code == 1 and s["outcome"] == "FAIL", out


def test_btc_seven_missing_days_in_a_fail_two_warn():
    d, p, v = BTC
    rng = np.random.default_rng(3)
    for n, want, code_want in ((7, "FAIL", 1), (6, "FAIL", 1), (5, "WARN", 0), (2, "WARN", 0)):
        drop = set(rng.choice(np.arange(10, len(d) - 10), size=n, replace=False).tolist())
        keep = [i for i in range(len(d)) if i not in drop]
        code, _, s, _ = btc_run(btc_world([d[i] for i in keep], p[keep]), d, v)
        integ = s["integrity"][0]
        assert integ["outcome"] == want and integ["n_missing_days_a"] == n and code == code_want, integ
        assert integ["missing_a"] == sorted(d[i] for i in drop)


def test_btc_outage_days_of_a_provider_warn_the_pair_and_pass_the_series():
    d, _, v = BTC
    keep = [i for i in range(len(d)) if i not in (100, 400, 900)]
    code, _, s, _ = btc_run(btc_world(), [d[i] for i in keep], v[keep])
    cal = check_of(s, "coinbase", "calendar")
    pair = s["pairs"][0]
    assert code == 0 and s["outcome"] == "PASS" and pair["outcome"] == "WARN", pair
    assert cal["outcome"] == "WARN" and cal["only_a"] == [d[100], d[400], d[900]], cal


def test_btc_level_dislocations_fail():
    d, _, v = BTC
    v2 = v.copy()
    rng = np.random.default_rng(4)
    late = [i for i, x in enumerate(d) if x >= "2017-01-01"]
    for i in rng.choice(late, size=len(late) // 30, replace=False):
        v2[i] *= 1.03
    code, _, s, _ = btc_run(btc_world(), d, v2)
    lv = check_of(s, "coinbase", "levels_and_returns")
    assert code == 1 and lv["late"]["within_band"] is False and lv["early"]["within_band"] is True, lv


def test_btc_each_late_level_band_fails_alone():
    """level_p50_max 0.003, level_p99_max 0.015 and level_max 0.05 apply from late_from (2017-01-01). Each case
    breaks one of them and keeps the count of big return differences inside its allowance."""
    d, _, v = BTC
    late = [i for i, x in enumerate(d) if x >= pc.THRESHOLDS["btc"]["late_from"]]
    rng = np.random.default_rng(6)
    cases = {"the median: every late day 0.4% off": (late, 0.004),
             "the 99th percentile: 2% of the late days 1.8% off":
                 (sorted(rng.choice(late[5:-5], size=len(late) // 50, replace=False).tolist()), 0.018),
             "the maximum: one late day 6% off": ([late[300]], 0.06)}
    for name, (idx, off) in cases.items():
        b = v.copy()
        b[idx] *= np.exp(off)
        code, _, s, _ = btc_run(btc_world(), d, b)
        lv = check_of(s, "coinbase", "levels_and_returns")
        assert lv["late"]["within_band"] is False and lv["early"]["within_band"] is True, (name, lv)
        assert lv["n_big_return_diff_days"] <= lv["n_allowed"] and lv["outcome"] == "FAIL" and code == 1, (name, lv)


def test_btc_early_segment_dislocation_only_warns():
    """early_level_p99_max 0.03 and early_level_max 0.10 are WARN only: before late_from a venue may sit far from the
    pinned file without failing the pair. One case breaks the maximum, the other the 99th percentile."""
    d, _, v = BTC
    t = d.index("2015-08-20")
    cases = {"the maximum: one early day 12% off": ([t], 0.12),
             "the 99th percentile: 15 early days in a row 4% off": (list(range(t, t + 15)), 0.04)}
    for name, (idx, off) in cases.items():
        b = v.copy()
        b[idx] *= np.exp(off)
        code, out, s, _ = btc_run(btc_world(), d, b)
        lv = check_of(s, "coinbase", "levels_and_returns")
        assert lv["early"]["within_band"] is False and lv["late"]["within_band"] is True, (name, lv)
        assert lv["outcome"] == "WARN" and lv["n_big_return_diff_days"] == 2 <= lv["n_allowed"], (name, lv)
        assert code == 0 and s["outcome"] == "PASS" and s["pairs"][0]["outcome"] == "WARN", (name, out)


def test_btc_big_return_differences_up_to_the_share_pass_above_it_fail():
    """ret_diff_big 0.02 with ret_diff_share_max 0.005: days whose log-return difference is above 2% are allowed up to
    0.5% of the compared days. The dislocations sit before late_from and inside the early bands, so the count alone
    decides."""
    d, _, v = BTC
    w = btc_world()
    allowed = check_of(btc_run(w, d, v)[2], "coinbase", "levels_and_returns")["n_allowed"]
    early = list(range(60, 700, 37))                                     # isolated days before 2017
    assert allowed == 9 == int(0.005 * (len(d) - 1)) and d[early[-1]] < pc.THRESHOLDS["btc"]["late_from"]
    for k, want, code_want in ((allowed // 2, "PASS", 0), (allowed // 2 + 1, "FAIL", 1)):
        b = v.copy()
        b[early[:k]] *= np.exp(0.025)                                    # one close 2.5% off: two days above 2%
        code, _, s, _ = btc_run(w, d, b)
        lv = check_of(s, "coinbase", "levels_and_returns")
        assert lv["n_big_return_diff_days"] == 2 * k and lv["early"]["within_band"] and lv["late"]["within_band"], lv
        assert lv["outcome"] == want and code == code_want, (k, lv)


def test_btc_implausible_jump_in_a_fails_the_series_by_integrity_alone():
    """jump_log_abs_max 0.7: a one-day log move of A above it is implausible. The provider carries the same step, so
    the pair agrees and A's own integrity check is what fails the series."""
    d, p, v = BTC
    t = d.index("2018-03-01")
    for step, want, code_want in ((1.6, "PASS", 0), (2.5, "FAIL", 1)):
        a, b = p.copy(), v.copy()
        a[t:] *= step
        b[t:] *= step
        code, out, s, _ = btc_run(btc_world(a_vals=a), d, b)
        integ = s["integrity"][0]
        assert integ["no_implausible_jump"] is (want == "PASS") and integ["outcome"] == want, (step, integ)
        assert s["pairs"][0]["outcome"] == "PASS" and code == code_want and s["outcome"] == want, out


def test_btc_provider_missing_days_inside_its_span():
    """coverage_min 0.95 for BTC-USD: outage days are allowed up to 5% of A's days inside the provider's span; the
    dates show as a calendar WARN. Above that the pair is not evaluated."""
    d, _, v = BTC
    for every, want, code_want in ((25, "PASS", 0), (16, "WITHHELD", 3)):
        keep = [i for i in range(len(d)) if i % every != every // 2]
        code, out, s, _ = btc_run(btc_world(), [d[i] for i in keep], v[keep])
        cov = check_of(s, "coinbase", "coverage")
        assert cov["coverage_ok"] is (want == "PASS") and cov["n_a_outside_b_span"] == 0, (every, cov)
        assert code == code_want and s["outcome"] == want, out
        if want == "PASS":
            cal = check_of(s, "coinbase", "calendar")
            assert cal["outcome"] == "WARN" and cal["n_only_a"] == len(d) - len(keep), cal
            assert s["pairs"][0]["outcome"] == "WARN"
        else:
            assert [c["id"] for c in s["pairs"][0]["checks"]] == ["coverage"], s["pairs"][0]


def test_btc_late_starting_provider_is_compared_on_its_own_span():
    """P-D5: coverage inside the provider's span; A's days before it count against edge_uncovered_max (471)."""
    d, _, v = BTC
    code, out, s, _ = btc_run(btc_world(), d[120:], v[120:])
    cov = check_of(s, "coinbase", "coverage")
    assert code == 0 and s["outcome"] == "PASS" and cov["n_a_outside_b_span"] == 120 and cov["coverage_ok"], out
    assert cov["first_date"] == d[120] and s["n_a_outside_evidence_spans"] == 120, s
    code, out, s, _ = btc_run(btc_world(), d[471:], v[471:])          # exactly the cap
    assert code == 0 and check_of(s, "coinbase", "coverage")["n_a_outside_b_span"] == 471, out
    code, _, s, _ = btc_run(btc_world(), d[500:], v[500:])           # 500 days late: above the cap
    cov = check_of(s, "coinbase", "coverage")
    assert code == 3 and cov["outcome"] == "WITHHELD" and s["outcome"] == "WITHHELD", s
    assert s["withheld_reasons"][-1] == pc.NO_EVIDENCE and len(s["pairs"][0]["checks"]) == 1, s


def test_btc_diagnostic_pair_never_fails_the_series():
    d, _, v = BTC
    code, _, s, _ = btc_run(btc_world(), d[1:], v[:-1], provider="binance")
    db = check_of(s, "binance", "day_boundary")
    assert code == 3 and db["outcome"] == "WARN" and db["kind"] == "warn" and s["outcome"] == "WITHHELD", s


# --------------------------------------------------------------------------- #
# DGS3MO
# --------------------------------------------------------------------------- #
def rf_world(a_vals=None, *, start: str = RF_WIN[0]) -> World:
    days, vals, hol = RF
    a_vals = vals if a_vals is None else a_vals
    text = pinned_text("DATE,DGS3MO", days, [np.nan if i in hol else x for i, x in enumerate(a_vals)])
    return World("rf", text, start=start, end=RF_WIN[1])


def rf_b(vals, *, drop_holidays=True):
    days, _, hol = RF
    keep = [i for i in range(len(days)) if not (drop_holidays and i in hol)]
    return [days[i] for i in keep], np.asarray(vals)[keep]


def rf_run(w: World, b_days, b_vals, decimals=2, provider="treasury"):
    return w.compare([(provider, w.file(f"rf_{provider}_{w.n}.csv", provider_text(b_days, b_vals, decimals)))])


def test_rf_clean_passes():
    _, vals, _ = RF
    code, out, s, _ = rf_run(rf_world(), *rf_b(vals))
    assert code == 0 and s["outcome"] == "PASS", out
    assert [c["id"] for c in s["integrity"]] == ["units", "seed"] and all(c["outcome"] == "PASS" for c in s["integrity"])
    assert check_of(s, "treasury", "values")["n_off_by_tol"] == 0


def test_rf_fraction_units_fail_as_an_integrity_check_of_a():
    _, vals, _ = RF
    code, _, s, _ = rf_run(rf_world(vals / 100.0), *rf_b(vals / 100.0), decimals=4)
    units = s["integrity"][0]
    assert code == 1 and units["id"] == "units" and units["outcome"] == "FAIL" and units["percent_units_ok"] is False


def test_rf_one_value_off_by_a_basis_point_fails():
    _, vals, _ = RF
    b_days, b_vals = rf_b(vals)
    b_vals = b_vals.copy()
    b_vals[b_days.index(next(d for d in b_days if d >= "2013-03-01"))] += 0.01
    code, _, s, _ = rf_run(rf_world(), b_days, b_vals)
    v = check_of(s, "treasury", "values")
    assert code == 1 and v["n_off_by_tol"] == 1 and v["max_abs_bucket"] in ("<=1e-02", "<=1e-01"), v


def test_rf_difference_below_value_tol_passes_above_it_fails():
    """value_tol_pct 0.005: a provider that publishes a third decimal may differ by 0.004 percentage points; 0.006 is
    a different value."""
    _, vals, _ = RF
    b_days, b_vals = rf_b(vals)
    at = b_days.index(next(d for d in b_days if d >= "2013-03-01"))
    for off, n_off, want, code_want in ((0.004, 0, "PASS", 0), (0.006, 1, "FAIL", 1)):
        b = b_vals.copy()
        b[at] += off
        code, out, s, _ = rf_run(rf_world(), b_days, b, decimals=3)
        v = check_of(s, "treasury", "values")
        assert v["n_off_by_tol"] == n_off and v["outcome"] == want and v["max_abs_bucket"] == "<=1e-02", (off, v)
        assert code == code_want and s["outcome"] == want, out


def test_rf_blank_in_a_where_b_has_a_value_warns_with_the_date():
    days, vals, hol = RF
    code, _, s, _ = rf_run(rf_world(), *rf_b(vals, drop_holidays=False))
    bl = check_of(s, "treasury", "blanks")
    want = sorted(days[i] for i in hol if "2009-12-04" <= days[i] <= RF_WIN[1])    # read from start - 31 days
    assert code == 0 and bl["outcome"] == "WARN" and bl["n_blank_a_value_b"] == len(want) > 0, bl
    assert bl["blank_a_value_b"] == want[:pc.LIST_CAP] and s["pairs"][0]["outcome"] == "WARN", bl


def test_rf_without_a_value_before_the_window_start_fails_the_seed():
    days, vals, hol = RF
    a = np.array([np.nan if d < "2010-01-05" else x for d, x in zip(days, vals)])
    w = rf_world(a)
    code, _, s, _ = rf_run(w, *rf_b(vals))
    seed = s["integrity"][1]
    assert code == 1 and seed["id"] == "seed" and seed["seed_before_start"] is False and s["outcome"] == "FAIL", seed


def test_rf_provider_file_of_blanks_covers_nothing():
    days, _, _ = RF
    w = rf_world()
    code, _, s, _ = w.compare([("treasury", w.file("blank.csv", "date,value\n" + "".join(f"{d},\n" for d in days)))])
    cov = check_of(s, "treasury", "coverage")
    assert code == 3 and cov["outcome"] == "WITHHELD" and cov["first_date"] is None, cov
    code, out, folder = fetch("rf", "fred_now", start=RF_WIN[0], end=RF_WIN[1], http=FakeHttp(
        lambda u, p: pc.Response(200, ("observation_date,DGS3MO\n" + "".join(f"{d},.\n" for d in days)).encode())))
    assert code == 4 and last_line(out) == "FETCH rf fred_now UNAVAILABLE fetch_failed exit=4 csv=-", out


def test_rf_late_provider_beyond_five_values_is_withheld_and_vintage_only_too():
    _, vals, _ = RF
    b_days, b_vals = rf_b(vals)
    later = [i for i, d in enumerate(b_days) if d >= "2010-01-15"]
    code, _, s, _ = rf_run(rf_world(), [b_days[i] for i in later], b_vals[later])
    assert code == 3 and check_of(s, "treasury", "coverage")["n_a_outside_b_span"] > 5, s
    code, _, s, _ = rf_run(rf_world(), *rf_b(vals), provider="fred_now")
    assert code == 3 and s["outcome"] == "WITHHELD" and s["pairs"][0]["role"] == "vintage", s


def test_rf_values_outside_the_percent_range_fail_the_units_check():
    """range_pct [-1, 20]: a file in basis points, or one value far outside the range, is not a percent series. The
    provider carries the same values, so A's own units check is what fails the series."""
    days, vals, hol = RF
    spike = vals.copy()
    spike[next(i for i, d in enumerate(days) if d >= "2013-03-01" and i not in hol)] = 25.0
    for a_vals in (vals * 100.0, spike):
        code, out, s, _ = rf_run(rf_world(a_vals), *rf_b(a_vals))
        units = s["integrity"][0]
        assert units["id"] == "units" and units["percent_units_ok"] is False and units["outcome"] == "FAIL", units
        assert check_of(s, "treasury", "values")["n_off_by_tol"] == 0 and code == 1 and s["outcome"] == "FAIL", out


def test_rf_provider_missing_published_values_inside_its_span():
    """coverage_min 0.99 for DGS3MO: a provider that lacks 2% of A's published values inside its span is not
    evaluated; one that lacks 0.5% is, and the dates it lacks are listed as a WARN."""
    _, vals, _ = RF
    b_days, b_vals = rf_b(vals)
    for every, want, code_want in ((200, "PASS", 0), (50, "WITHHELD", 3)):
        keep = [i for i in range(len(b_days)) if i % every != every // 2]
        lacking = [b_days[i] for i in range(len(b_days)) if i % every == every // 2 and b_days[i] >= "2009-12-04"]
        code, out, s, _ = rf_run(rf_world(), [b_days[i] for i in keep], b_vals[keep])
        cov = check_of(s, "treasury", "coverage")
        assert cov["coverage_ok"] is (want == "PASS") and code == code_want and s["outcome"] == want, (every, cov)
        if want == "PASS":
            bl = check_of(s, "treasury", "blanks")
            assert bl["outcome"] == "WARN" and bl["value_a_absent_b"] == lacking and len(lacking) > 0, bl
            assert s["pairs"][0]["outcome"] == "WARN"


def test_rf_blank_in_b_where_a_has_a_value_is_listed_like_a_missing_row():
    """A provider that carries the row but no value (H.15 prints ND, FRED a dot) lacks that value as much as one
    without the row: both are listed under value_a_absent_b, as a WARN."""
    days, vals, hol = RF
    b_days, b_vals = rf_b(vals)
    nd = [i for i, d in enumerate(b_days) if d >= "2012-06-01"][:3]
    cells = ["" if i in nd else f"{v:.2f}" for i, v in enumerate(b_vals)]
    text = "date,value\n" + "".join(f"{d},{c}\n" for d, c in zip(b_days, cells))
    w = rf_world()
    code, out, s, _ = w.compare([("treasury", w.file("rf_nd.csv", text))])
    bl = check_of(s, "treasury", "blanks")
    assert bl["outcome"] == "WARN" and bl["value_a_absent_b"] == [b_days[i] for i in nd], bl
    assert bl["n_blank_a_value_b"] == 0 and check_of(s, "treasury", "coverage")["coverage_ok"], s["pairs"][0]
    assert code == 0 and s["outcome"] == "PASS" and s["pairs"][0]["outcome"] == "WARN", out


def test_rf_late_starting_provider_five_values_pass():
    """edge_uncovered_max 5 for DGS3MO: a provider may lack at most five of A's published values outside its span
    (A is read from the window start - seed_lookback_days)."""
    _, vals, _ = RF
    b_days, b_vals = rf_b(vals)
    inside = [i for i, d in enumerate(b_days) if d >= "2009-12-04"]
    code, out, s, _ = rf_run(rf_world(), [b_days[i] for i in inside[5:]], b_vals[inside[5:]])
    cov = check_of(s, "treasury", "coverage")
    assert cov["n_a_outside_b_span"] == 5 and cov["coverage_ok"] and code == 0 and s["outcome"] == "PASS", out
    code, out, s, _ = rf_run(rf_world(), [b_days[i] for i in inside[6:]], b_vals[inside[6:]])
    cov = check_of(s, "treasury", "coverage")
    assert cov["n_a_outside_b_span"] == 6 and cov["coverage_ok"] is False and code == 3, out


# --------------------------------------------------------------------------- #
# The tool as a whole
# --------------------------------------------------------------------------- #
def test_unexpected_exception_is_error_exit_4_and_writes_nothing():
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    real = pc.assert_summary_safe

    def boom(*_a, **_k):
        raise ValueError("close 4321.12 leaked")                 # an exception whose text quotes a value
    pc.assert_summary_safe = boom
    try:
        code, out, s, path = w.compare([("fmp", fmp), ("kis", kis)])
    finally:
        pc.assert_summary_safe = real
    assert code == 4 and s is None and not path.exists(), out
    assert last_line(out) == "PARITY spy ERROR exit=4 summary=-" and "4321" not in out, out


def test_selftest_holds_COMPUTES_and_the_checks_together():
    assert pc.selftest() == []
    code, out = capture(lambda: pc.run(["selftest"]))
    assert code == 0 and last_line(out) == "SELFTEST PASS checks=11 failures=0", out
    seen = set()
    for summary in (spy_clean_summary(), btc_clean_summary(), rf_clean_summary()):
        seen |= {c["id"] for c in summary["integrity"]} | {c["id"] for p in summary["pairs"] for c in p["checks"]}
    assert seen == set(pc.COMPUTES), sorted(seen ^ set(pc.COMPUTES))
    source = Path(pc.__file__).read_text(encoding="utf-8")
    assert pc.forbidden_statistics(source) == []
    assert pc.forbidden_statistics("x.mean()\nnp.corrcoef(a, b)\npd.Series(a).std()\n") == \
        ["mean@1", "corrcoef@2", "std@3"]


def test_selftest_fails_when_COMPUTES_and_the_checks_differ():
    """10.5: the self-test holds COMPUTES and the checks together, so a kind no check computes (or a check COMPUTES
    does not name) ends SELFTEST FAIL with exit 1, and a planted correlation call is found."""
    saved = dict(pc.COMPUTES)
    try:
        pc.COMPUTES["turnover"] = "a kind no check computes"
        failures = pc.selftest()
        code, out = capture(lambda: pc.run(["selftest"]))
    finally:
        pc.COMPUTES.clear()
        pc.COMPUTES.update(saved)
    assert any("differ from COMPUTES" in f for f in failures), failures
    assert code == 1 and last_line(out) == "SELFTEST FAIL checks=12 failures=1", out
    planted = Path(pc.__file__).read_text(encoding="utf-8") + "\n\ndef _planted(x, y):\n    return np.corrcoef(x, y)\n"
    assert [h.split("@")[0] for h in pc.forbidden_statistics(planted)] == ["corrcoef"]
    assert pc.selftest() == []


def spy_clean_summary():
    w = spy_world()
    fmp, kis, yahoo = spy_b(w)
    return w.compare([("fmp", fmp), ("kis", kis), ("yahoo_now", yahoo)])[2]


def btc_clean_summary():
    d, _, v = BTC
    return btc_run(btc_world(), d, v)[2]


def rf_clean_summary():
    _, vals, _ = RF
    return rf_run(rf_world(), *rf_b(vals))[2]


def test_providers_and_thresholds_are_those_of_spec_10_5_1():
    """Typed here from the spec's table, independently of the tool's constants."""
    assert pc.PROVIDERS == {
        "spy": {"fmp": ("independent", "total", True), "kis": ("cross", "split", True),
                "yahoo_now": ("vintage", "total", True)},
        "btc": {"coinbase": ("independent", "none", True), "bitstamp": ("independent", "none", False),
                "binance": ("diagnostic", "none", True)},
        "rf": {"treasury": ("independent", "rate_pct", True), "h15": ("independent", "rate_pct", False),
               "fred_now": ("vintage", "rate_pct", True)}}
    assert pc.THRESHOLDS == {
        "spy": {"coverage_min": 0.99, "edge_uncovered_max": 5, "ret_diff_tol": 2e-4, "ret_diff_max": 2e-3,
                "ret_diff_share_max": 0.005, "ret_diff_floor_days": 5, "drift_range_max": 5e-3, "jump_abs_max": 0.25,
                "ex_gap_min": 5e-4, "ex_gap_max": 2e-2, "ex_days_per_year": 4, "yield_band": [0.005, 0.04]},
        "btc": {"coverage_min": 0.95, "edge_uncovered_max": 471, "late_from": "2017-01-01", "level_p50_max": 0.003,
                "level_p99_max": 0.015, "level_max": 0.05, "early_level_p99_max": 0.03, "early_level_max": 0.10,
                "missing_days_warn_max": 5, "jump_log_abs_max": 0.7, "ret_diff_big": 0.02,
                "ret_diff_share_max": 0.005},
        "rf": {"coverage_min": 0.99, "edge_uncovered_max": 5, "value_tol_pct": 0.005, "range_pct": [-1.0, 20.0],
               "unit_max_at_least_pct": 1.0, "seed_lookback_days": 31}}
    assert pc.UNAVAILABLE_REASONS == ("no_key", "plan_or_access", "fetch_failed", "short_history")
    assert (pc.EXIT, pc.EXIT_REFUSED, pc.EXIT_ERROR) == ({"PASS": 0, "FAIL": 1, "WITHHELD": 3}, 2, 4)
    assert set(pc.FETCHERS) == {p for table in pc.PROVIDERS.values() for p in table}


# --------------------------------------------------------------------------- #
# fetch over fake transports
# --------------------------------------------------------------------------- #
class FakeHttp:
    """Records every request; `handler(url, params)` answers with a pc.Response."""

    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def __call__(self, url, params, headers):
        self.calls.append((url, dict(params or {})))
        return self.handler(url, dict(params or {}))


def ok_json(obj) -> pc.Response:
    return pc.Response(200, json.dumps(obj).encode("utf-8"))


def in_span(days, lo, hi):
    return [i for i, d in enumerate(days) if lo <= d <= hi]


def fmp_handler(url, params):
    assert url == pc.FMP_URL and params["apikey"] == FMP_KEY and params["to"] <= pc.LAST_REQUEST_DAY, params
    d0, _, adj0, _ = SPY
    return ok_json([{"date": d0[i], "adjClose": round(float(adj0[i]) * 0.987, 6), "adjOpen": 1.0}
                    for i in reversed(in_span(d0, params["from"], params["to"]))])


def fake_kis(calls: list, labels: list | None = None):
    """The app's KIS getter over the synthetic SPY path; `labels` gives each bar another date (a provider that
    labels its days differently)."""
    d0, raw0, _, _ = SPY
    d0 = d0 if labels is None else labels

    def get(path, tr_id, params):
        assert (path, tr_id) == (pc.KIS_PATH, pc.KIS_TR_ID) and re.fullmatch(r"\d{8}", params["BYMD"]), params
        assert os.environ.get("KIS_APP_KEY") == KIS_KEY, "the app's client reads the key from the environment"
        assert os.environ.get("FMP_API_KEY") != FMP_KEY, "only the KIS names enter the environment"
        calls.append(params["BYMD"])
        end = f"{params['BYMD'][:4]}-{params['BYMD'][4:6]}-{params['BYMD'][6:]}"
        idx = [i for i, d in enumerate(d0) if d <= end][-100:]
        return {"rt_cd": "0", "output2": [{"xymd": d0[i].replace("-", ""), "clos": f"{raw0[i]:.4f}"}
                                          for i in reversed(idx)]}
    return get


def fake_yf(calls: list):
    d0, _, adj0, _ = SPY

    def download(symbol, start, end):
        calls.append((symbol, start, end))
        idx = [i for i, d in enumerate(d0) if start <= d < end]
        cols = pd.MultiIndex.from_tuples([("Close", "SPY"), ("Open", "SPY")], names=["Price", "Ticker"])
        return pd.DataFrame([[adj0[i] * 0.99, 1.0] for i in idx], index=pd.to_datetime([d0[i] for i in idx]),
                            columns=cols)
    return download


def coinbase_handler(url, params):
    d, _, v = BTC
    assert url == pc.COINBASE_URL and params["granularity"] == "86400"
    lo, hi = params["start"][:10], params["end"][:10]
    assert (date.fromisoformat(hi) - date.fromisoformat(lo)).days < 300 and hi <= pc.LAST_REQUEST_DAY
    return ok_json([[pc._unix(d[i]), 0, 0, 0, round(float(v[i]), 2), 1.0] for i in reversed(in_span(d, lo, hi))])


def bitstamp_handler(url, params):
    d, _, v = BTC
    lo, hi = pc._iso_from_unix(int(params["start"])), pc._iso_from_unix(int(params["end"]))
    return ok_json({"data": {"pair": "BTC/USD", "ohlc": [{"timestamp": str(pc._unix(d[i])), "close": f"{v[i]:.2f}"}
                                                         for i in in_span(d, lo, hi)]}})


def binance_handler(url, params):
    if url == pc.BINANCE_URLS[0]:
        return pc.Response(451, b'{"code":0,"msg":"restricted"}')    # the data host refuses: the main host answers
    d, _, v = BTC
    lo, hi = pc._iso_from_unix(int(params["startTime"]) / 1000), pc._iso_from_unix(int(params["endTime"]) / 1000)
    return ok_json([[pc._unix(d[i]) * 1000, "0", "0", "0", f"{v[i] * 1.001:.2f}", "1"] for i in in_span(d, lo, hi)])


def treasury_handler(url, params):
    days, vals, hol = RF
    year = params["field_tdr_date_value"]
    entries = "".join(
        f'<entry><content type="application/xml"><m:properties><d:Id m:type="Edm.Int32">{i}</d:Id>'
        f'<d:NEW_DATE m:type="Edm.DateTime">{days[i]}T00:00:00</d:NEW_DATE>'
        f'<d:BC_1MONTH m:type="Edm.Double">9.99</d:BC_1MONTH>'
        f'<d:BC_3MONTH m:type="Edm.Double">{vals[i]:.2f}</d:BC_3MONTH></m:properties></content></entry>'
        for i in range(len(days)) if days[i].startswith(year) and i not in hol)
    return pc.Response(200, ('<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom" '
                             'xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" '
                             'xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices">'
                             + entries + "</feed>").encode("utf-8"))


def h15_text(identifier: str) -> bytes:
    days, vals, hol = RF
    head = ['"Series Description","Market yield on U.S. Treasury securities at 3-month constant maturity"',
            '"Unit:","Percent:_Per_Year"', '"Multiplier:","1"', '"Currency:","NA"',
            f'"Unique Identifier:","H15/H15/{identifier}"', '"Time Period","RIFLGFCM03_N.B"']
    rows = [f"{d},{'ND' if i in hol else f'{vals[i]:.2f}'}" for i, d in enumerate(days)]
    return ("\n".join(head + rows) + "\n").encode("utf-8")


def fred_handler(url, params):
    days, vals, hol = RF
    assert params["id"] == "DGS3MO" and params["coed"] <= pc.LAST_REQUEST_DAY
    rows = [f"{d},{'.' if i in hol else f'{vals[i]:.2f}'}" for i, d in enumerate(days)
            if params["cosd"] <= d <= params["coed"]]
    return pc.Response(200, ("observation_date,DGS3MO\n" + "\n".join(rows) + "\n").encode("utf-8"))


def key_file(root: Path) -> Path:
    path = root / "keys.txt"                               # any name; the owner points --env-file at his .env
    path.write_text(f"# synthetic\nFMP_API_KEY={FMP_KEY}\nexport KIS_APP_KEY=\"{KIS_KEY}\"\nKIS_APP_SECRET='{KIS_SECRET}'\n"
                    "OPENAI_API_KEY=never-read\nKIS_BASE_URL=https://kis.invalid:9443\n", encoding="utf-8")
    return path


def fetch(series, provider, *, start, end, http=None, yf=None, kis=None, env_file=None, root=None):
    root = root or tmp()
    out = root / f"fetch_{series}_{provider}"
    argv = ["fetch", "--series", series, "--provider", provider, "--start", start, "--end", end, "--out", str(out)]
    if env_file:
        argv += ["--env-file", str(env_file)]
    code, text = capture(lambda: pc.run(argv, now=NOW, http=http, yf_download=yf, kis_get=kis))
    return code, text, out


def all_text(folder: Path) -> str:
    return "\n".join(p.read_bytes().decode("utf-8", errors="replace") for p in sorted(folder.rglob("*")) if p.is_file())


def read_csv_rows(path: Path) -> list[tuple[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "date,value"
    return [tuple(x.split(",")) for x in lines[1:]]


def test_fetch_fmp_writes_raw_csv_and_meta_and_never_a_key():
    root = tmp()
    http = FakeHttp(fmp_handler)
    code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=http, env_file=key_file(root),
                              root=root)
    assert code == 0 and last_line(out).startswith("FETCH spy fmp OK exit=0 csv="), out
    assert len(http.calls) == 1 and http.calls[0][1]["from"] == "2009-12-04" and http.calls[0][1]["to"] == "2017-01-06"
    rows = read_csv_rows(folder / "spy_fmp.csv")
    assert rows[0][0] == "2009-12-04" and rows[-1][0] == "2016-12-30" and len(rows) > 1800, rows[:2]
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert (meta["role"], meta["convention"], meta["quote_currency"]) == ("independent", "total", "USD"), meta
    assert meta["requests"] == [{"symbol": "SPY", "from": "2009-12-04", "to": "2017-01-06"}], meta["requests"]
    assert meta["keys_read_by_name"] == ["FMP_API_KEY", "KIS_APP_KEY", "KIS_APP_SECRET", "KIS_BASE_URL"]
    raw = folder / meta["raw"][0]["file"]
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == meta["raw"][0]["sha256"]
    for secret in (FMP_KEY, KIS_KEY, KIS_SECRET, "never-read"):
        assert secret not in out and secret not in all_text(folder), secret


def test_fetch_kis_pages_back_from_an_explicit_date_and_restores_the_environment():
    root = tmp()
    calls: list = []
    with env_without(*pc.KEY_NAMES):
        code, out, folder = fetch("spy", "kis", start=SPY_WIN[0], end=SPY_WIN[1], kis=fake_kis(calls),
                                  env_file=key_file(root), root=root)
        left = [n for n in pc.KEY_NAMES if n in os.environ]
    assert code == 0 and left == [], (out, left)
    assert calls[0] == "20170106" and all(c <= "20261230" for c in calls) and len(calls) >= 18, calls
    rows = read_csv_rows(folder / "spy_kis.csv")
    assert rows[0][0] == "2009-12-04" and rows[-1][0] == "2016-12-30"
    for secret in (KIS_KEY, KIS_SECRET):
        assert secret not in out and secret not in all_text(folder)
    with env_without(*pc.KEY_NAMES):
        code, out, folder = fetch("spy", "kis", start=SPY_WIN[0], end=SPY_WIN[1], kis=fake_kis([]))
    assert code == 4 and last_line(out) == "FETCH spy kis UNAVAILABLE no_key exit=4 csv=-" and not folder.exists(), out


def test_fetch_yahoo_now_coinbase_bitstamp_binance_treasury_h15_fred():
    yf_calls: list = []
    cases = [("spy", "yahoo_now", SPY_WIN, dict(yf=fake_yf(yf_calls))),
             ("btc", "coinbase", BTC_WIN, dict(http=FakeHttp(coinbase_handler))),
             ("btc", "bitstamp", BTC_WIN, dict(http=FakeHttp(bitstamp_handler))),
             ("btc", "binance", BTC_WIN, dict(http=FakeHttp(binance_handler))),
             ("rf", "treasury", RF_WIN, dict(http=FakeHttp(treasury_handler))),
             ("rf", "h15", RF_WIN, dict(http=FakeHttp(lambda u, p: pc.Response(200, h15_text("RIFLGFCM03_N.B"))))),
             ("rf", "fred_now", RF_WIN, dict(http=FakeHttp(fred_handler)))]
    for series, provider, (start, end), kw in cases:
        code, out, folder = fetch(series, provider, start=start, end=end, **kw)
        assert code == 0, (provider, out)
        rows = read_csv_rows(folder / f"{series}_{provider}.csv")
        first = (date.fromisoformat(start) - timedelta(days=31)).isoformat()
        assert first <= rows[0][0] and rows[-1][0] <= (date.fromisoformat(end) + timedelta(days=7)).isoformat()
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        assert meta["provider"] == provider and meta["role"] == pc.PROVIDERS[series][provider][0]
        assert len(meta["raw"]) == len(meta["requests"]) >= 1, meta
        if series == "rf" and provider != "treasury":
            assert any(v == "" for _, v in rows), f"{provider}: a published blank kept as a blank cell"
        if provider == "binance":
            assert meta["quote_currency"] == "USDT" and all(c[0] == pc.BINANCE_URLS[1] for c in kw["http"].calls[1::2])
        if "http" in kw:
            for _, params in kw["http"].calls:
                assert not any(isinstance(x, str) and _DATE_LIKE.search(x) and x[:10] >= pc.CUTOFF
                               for x in params.values()), params
    assert yf_calls == [("SPY", "2009-12-04", "2017-01-07")], yf_calls


_DATE_LIKE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def test_fetch_failures_end_unavailable_with_a_reason_and_no_key():
    root = tmp()
    keys = key_file(root)
    with env_without(*pc.KEY_NAMES):
        http = FakeHttp(fmp_handler)
        code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=http)
    assert code == 4 and last_line(out) == "FETCH spy fmp UNAVAILABLE no_key exit=4 csv=-" and not folder.exists(), out
    assert http.calls == [], "a request went out without a key"
    code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys,
                              http=FakeHttp(lambda u, p: pc.Response(402, b'{"Error Message":"plan"}')), root=root)
    assert code == 4 and last_line(out) == "FETCH spy fmp UNAVAILABLE plan_or_access exit=4 csv=-", out

    def transport_error(url, params):
        raise ConnectionError(f"cannot reach {url}?apikey={params.get('apikey')}")    # quotes the key
    code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys,
                              http=FakeHttp(transport_error), root=root)
    assert code == 4 and "ERROR: ConnectionError" in out and FMP_KEY not in out and not folder.exists(), out
    code, out, _ = fetch("rf", "h15", start=RF_WIN[0], end=RF_WIN[1],
                         http=FakeHttp(lambda u, p: pc.Response(200, h15_text("RIFLGFCM06_N.B"))))
    assert code == 4 and last_line(out) == "FETCH rf h15 UNAVAILABLE fetch_failed exit=4 csv=-", out
    code, out, _ = fetch("btc", "fmp", start=BTC_WIN[0], end=BTC_WIN[1], http=FakeHttp(fmp_handler))
    assert code == 2 and "not one of" in out, out


def test_fetch_never_requests_stores_or_keeps_an_observation_from_2027():
    http = FakeHttp(coinbase_handler)
    code, out, folder = fetch("btc", "coinbase", start=BTC_WIN[0], end="2027-01-04", http=http)
    assert code == 2 and http.calls == [] and not folder.exists() and "2027-01-01" in out, out
    http = FakeHttp(fred_handler)
    code, out, folder = fetch("rf", "fred_now", start="2026-06-01", end="2026-12-29", http=http)
    assert http.calls and http.calls[0][1]["coed"] == pc.LAST_REQUEST_DAY, http.calls

    def with_2027(url, params):
        return pc.Response(200, b"observation_date,DGS3MO\n2016-12-29,0.51\n2027-01-04,0.52\n")
    code, out, folder = fetch("rf", "fred_now", start=RF_WIN[0], end=RF_WIN[1], http=FakeHttp(with_2027))
    assert code == 2 and not folder.exists() and "2027-01-01" in out and "0.52" not in out, out


def test_fetch_refuses_a_response_that_echoes_a_key():
    root = tmp()

    def echo(url, params):
        return ok_json([{"date": "2010-01-04", "adjClose": 1.0, "note": f"key {params['apikey']}"}])
    code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=FakeHttp(echo),
                              env_file=key_file(root), root=root)
    assert code == 2 and not folder.exists() and FMP_KEY not in out and "holds a key value" in out, out


def test_fetch_and_compare_write_nothing_outside_their_new_folders():
    root = tmp()
    home, cwd = root / "home", root / "cwd"
    home.mkdir()
    cwd.mkdir()
    keys = key_file(root)
    saved_env = {n: os.environ.get(n) for n in ("HOME", "USERPROFILE")}
    saved_cwd = os.getcwd()
    os.environ["HOME"] = os.environ["USERPROFILE"] = str(home)
    os.chdir(cwd)
    try:
        before = sorted(p for p in root.rglob("*"))
        made = []
        for provider, kw in (("fmp", dict(http=FakeHttp(fmp_handler))), ("kis", dict(kis=fake_kis([]))),
                             ("yahoo_now", dict(yf=fake_yf([])))):
            code, out, folder = fetch("spy", provider, start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys, root=root,
                                      **kw)
            assert code == 0, out
            made.append(folder)
        w = spy_world()
        code, out, s, out_folder = w.compare([(p, f / f"spy_{p}.csv") for p, f in zip(("fmp", "kis", "yahoo_now"),
                                                                                       made)])
        assert code == 0 and s["outcome"] == "PASS", out
        after = sorted(p for p in root.rglob("*"))
        new = [p for p in after if p not in before]
        assert all(any(p == f or f in p.parents for f in made) for p in new), new
        assert list(home.iterdir()) == [] and list(cwd.iterdir()) == []
        assert {p["provider"]: p["outcome"] for p in s["pairs"]} == {"fmp": "PASS", "kis": "PASS",
                                                                     "yahoo_now": "PASS"}, s["pairs"]
    finally:
        os.chdir(saved_cwd)
        for n, v in saved_env.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v


def test_output_folder_under_asset_expansion_nextgen_or_ledgers_is_refused():
    """Spec 10.5, Writes: nothing the tool writes enters docs/asset_expansion/, a ledger or ~/.nextgen (the kis token
    aside, which the app's client writes). Such a folder is refused before anything is fetched or read."""
    w = spy_world()
    fmp, _, _ = spy_b(w)
    for part in pc.NO_WRITE_PARTS:
        base = w.root / "elsewhere"
        code, text, s, _ = w.compare([("fmp", fmp)], out=base / part / "run")
        assert code == 2 and s is None and not base.exists() and part in text, (part, text)
        http = FakeHttp(fmp_handler)
        code, text, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=http, root=base / part)
        assert code == 2 and http.calls == [] and not base.exists(), (part, text)
        assert last_line(text) == "FETCH spy fmp REFUSED exit=2 csv=-", text
    assert pc.NO_WRITE_PARTS == ("asset_expansion", ".nextgen", "ledgers")


def test_a_failed_write_leaves_no_folder_behind():
    """A REFUSED or ERROR run writes nothing: when a file cannot be written, the folder made for the run is removed."""
    out = tmp() / "partial"
    try:
        pc._write_new_folder(out, {"summary.json": "{}\n", "bad\x00name": "x"})
    except (ValueError, OSError):
        pass
    else:
        raise AssertionError("a file name with a NUL was written")
    assert not out.exists()


def test_console_lines_print_on_a_cp949_console_and_on_utf8():
    """The owner's console is cp949 or UTF-8. A path character cp949 lacks is written as an escape, Hangul as it is,
    and the run ends with its PARITY line either way: no UnicodeEncodeError turns a finished run into an ERROR."""
    for encoding in ("cp949", "utf-8"):
        w = spy_world()
        fmp, kis, _ = spy_b(w)
        out = w.root / "out" / "\uacb0\uacfc \u00e9"                    # Hangul, a space and an e-acute
        argv = ["compare", "--series", "spy", "--table", str(w.table), "--repo", str(w.repo), "--pair", "fmp",
                str(fmp), "--pair", "kis", str(kis), "--unavailable", "yahoo_now", "fetch_failed", "--out", str(out)]
        raw = io.BytesIO()
        console = io.TextIOWrapper(raw, encoding=encoding, errors="strict", newline="\n")
        with contextlib.redirect_stdout(console):
            code = pc.run(argv, now=NOW)
        console.flush()
        text = raw.getvalue().decode(encoding)
        console.detach()
        line = last_line(text)
        assert code == 0 and (out / "summary.json").is_file() and (out / "detail.json").is_file(), text
        assert line.startswith("PARITY spy PASS exit=0 summary=") and "\uacb0\uacfc" in line, line
        assert ("\\xe9" in line and "\u00e9" not in line) if encoding == "cp949" else ("\u00e9" in line), line


def test_every_file_the_tool_writes_is_utf8_with_lf_only():
    """Every text file is UTF-8 with LF on every platform, never the platform's line ending, so a summary's bytes and
    a fetch record's sha256 are the same on Windows and Linux; and each record's sha256 is its file's."""
    root = tmp()
    keys = key_file(root)
    folders = []
    with env_without(*pc.KEY_NAMES):
        for provider, kw in (("fmp", dict(http=FakeHttp(fmp_handler))), ("kis", dict(kis=fake_kis([]))),
                             ("yahoo_now", dict(yf=fake_yf([])))):
            code, out, folder = fetch("spy", provider, start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys, root=root, **kw)
            assert code == 0, out
            folders.append(folder)
    w = spy_world()
    code, out, _, compared = w.compare([(q, f / f"spy_{q}.csv") for q, f in zip(("fmp", "kis", "yahoo_now"), folders)])
    assert code == 0, out
    files = [x for f in (*folders, compared) for x in sorted(f.rglob("*")) if x.is_file()]
    assert sorted(x.name for x in compared.iterdir()) == ["detail.json", "summary.json"] and len(files) >= 11, files
    for path in files:
        data = path.read_bytes()
        assert b"\r" not in data, path
        assert data.endswith(b"\n") or path.parent.name == "raw", path        # a raw response is kept byte for byte
        data.decode("utf-8")
    for folder in folders:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        assert hashlib.sha256((folder / meta["csv"]["file"]).read_bytes()).hexdigest() == meta["csv"]["sha256"]
        for raw in meta["raw"]:
            data = (folder / raw["file"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == raw["sha256"] and b"\r" not in data, raw["file"]


def test_env_file_with_a_bom_and_a_cp949_comment_is_read_by_name():
    """A .env saved by a Windows editor: a UTF-8 BOM, CRLF and a comment in cp949. The key lines are still read by
    name; a missing file is a typed refusal that names no value."""
    root = tmp()
    path = root / "env.txt"
    path.write_bytes(b"\xef\xbb\xbf" + "# \ud0a4 \uba54\ubaa8\r\n".encode("cp949")
                     + f"FMP_API_KEY={FMP_KEY}\r\nOTHER_SECRET=never-read\r\n".encode("ascii"))
    assert pc.load_keys(path, environ={}) == {"FMP_API_KEY": FMP_KEY}
    http = FakeHttp(fmp_handler)
    with env_without(*pc.KEY_NAMES):
        code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=http,
                                  env_file=root / "absent.txt", root=root)
    assert code == 2 and http.calls == [] and not folder.exists(), out
    assert "--env-file cannot be read (FileNotFoundError)" in out and "Traceback" not in out, out


_ABSENT = object()


def test_kis_without_the_app_client_ends_unavailable_not_error():
    """Missing provider access is a typed, readable line, never a traceback: when the app's KIS client cannot be
    imported (a clone without the app's packages), the fetch ends UNAVAILABLE fetch_failed and writes nothing. The
    import is stopped before any app module runs, so no .env and no ~/.nextgen file is touched here."""
    root = tmp()
    keys = key_file(root)
    blocked = ("data.krx", "data.krx.kis_client")
    saved = {n: sys.modules.get(n, _ABSENT) for n in blocked}
    for n in blocked:
        sys.modules[n] = None
    try:
        with env_without(*pc.KEY_NAMES):
            code, out, folder = fetch("spy", "kis", start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys, root=root)
    finally:
        for n, m in saved.items():
            if m is _ABSENT:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
    assert code == 4 and last_line(out) == "FETCH spy kis UNAVAILABLE fetch_failed exit=4 csv=-", out
    assert "the app's KIS client cannot be loaded" in out and "Traceback" not in out and not folder.exists(), out
    for secret in (KIS_KEY, KIS_SECRET):
        assert secret not in out


def test_the_tool_runs_as_a_module_from_the_clone_root():
    """`python -B -m tools.provider_parity.parity_check ...` from the repository root, as the README tells the owner,
    with the console encoding forced to cp949 (the Korean Windows default for redirected output) and the key names
    out of the child's environment: a result line and its exit code, a refusal, and a typed line for a missing key."""
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    env = {k: v for k, v in os.environ.items() if k not in pc.KEY_NAMES}
    env.update(PYTHONIOENCODING="cp949", PYTHONDONTWRITEBYTECODE="1")

    def cli(*args):
        done = subprocess.run([sys.executable, "-B", "-m", "tools.provider_parity.parity_check", *args],
                              cwd=str(ROOT), env=env, capture_output=True, timeout=600)
        return done.returncode, done.stdout.decode("cp949"), done.stderr.decode("cp949", errors="replace")
    code, out, err = cli("selftest")
    assert code == 0 and last_line(out) == "SELFTEST PASS checks=11 failures=0" and "Traceback" not in err, (out, err)
    folder = w.out()
    argv = ["compare", "--series", "spy", "--table", str(w.table), "--repo", str(w.repo), "--pair", "fmp", str(fmp),
            "--pair", "kis", str(kis), "--unavailable", "yahoo_now", "no_key", "--out", str(folder)]
    code, out, err = cli(*argv)
    assert code == 0 and last_line(out) == f"PARITY spy PASS exit=0 summary={folder / 'summary.json'}", (out, err)
    assert "Traceback" not in err, err
    assert json.loads((folder / "summary.json").read_text(encoding="utf-8"))["outcome"] == "PASS"
    code, out, err = cli(*argv)                                           # the folder exists now
    assert code == 2 and last_line(out) == "PARITY spy REFUSED exit=2 summary=-" and "Traceback" not in err, (out, err)
    code, out, err = cli("fetch", "--series", "spy", "--provider", "fmp", "--start", SPY_WIN[0], "--end", SPY_WIN[1],
                         "--out", str(w.root / "fetch_no_key"))
    assert code == 4 and last_line(out) == "FETCH spy fmp UNAVAILABLE no_key exit=4 csv=-", (out, err)
    assert "FMP_API_KEY is not set" in out and "Traceback" not in out + err and not (w.root / "fetch_no_key").exists()
    # a usage error goes to stderr, where Python itself escapes a character cp949 lacks: exit 2, no traceback
    code, out, err = cli("compare", "--series", "spy\u00e9")
    assert code == 2 and "invalid choice" in err and "Traceback" not in err, (out, err)


def test_load_keys_reads_only_the_named_keys():
    root = tmp()
    keys = pc.load_keys(key_file(root), environ={})
    assert keys == {"FMP_API_KEY": FMP_KEY, "KIS_APP_KEY": KIS_KEY, "KIS_APP_SECRET": KIS_SECRET,
                    "KIS_BASE_URL": "https://kis.invalid:9443"}
    assert pc.load_keys(None, environ={"FMP_API_KEY": "<your key>", "KIS_APP_KEY": " x1234 "}) == {"KIS_APP_KEY": "x1234"}
    assert pc._redact(f"a {FMP_KEY} b", [FMP_KEY]) == "a <redacted> b"
    say = pc._Say()                                        # the console's last guard: a loaded key value never prints
    say.secrets[:] = [FMP_KEY]
    _, out = capture(lambda: say(f"request to x?apikey={FMP_KEY} failed") or 0)
    assert out == "request to x?apikey=<redacted> failed\n", out


# --------------------------------------------------------------------------- #
# Review of 2026-11-11, part 1: fetchers against values typed by hand, not made with the tool's own helpers
# --------------------------------------------------------------------------- #
E_2017_01_02 = 1483315200              # 2017-01-02T00:00:00Z, typed by hand
E_2017_01_01, E_2016_12_01, E_2017_01_27, E_2026_12_30 = 1483228800, 1480550400, 1485475200, 1798588800
DAY = 86400
assert [calendar.timegm((y, m, d, 0, 0, 0)) for y, m, d in
        ((2017, 1, 2), (2017, 1, 1), (2016, 12, 1), (2017, 1, 27), (2026, 12, 30))] == \
    [E_2017_01_02, E_2017_01_01, E_2016_12_01, E_2017_01_27, E_2026_12_30]      # the stdlib's own UTC clock agrees


def fetch_rows(series, provider, start, end, **kw):
    with env_without(*pc.KEY_NAMES):
        code, out, folder = fetch(series, provider, start=start, end=end, **kw)
    return code, out, read_csv_rows(folder / f"{series}_{provider}.csv") if code == 0 else None


def test_utc_helpers_do_not_follow_the_machine_time_zone():
    """`_unix` and `_iso_from_unix` label days in UTC whatever the machine's zone is (the owner's PC is on KST). The
    zone is switched with `time.tzset`, which POSIX has and Windows lacks; there the case runs in the machine's own
    zone only."""
    saved = os.environ.get("TZ")
    zones = ("America/New_York", "Asia/Seoul", "UTC") if hasattr(time, "tzset") else (None,)
    try:
        for tz in zones:
            if tz is not None:
                os.environ["TZ"] = tz
                time.tzset()
            assert pc._unix("2017-01-02") == E_2017_01_02, (tz, pc._unix("2017-01-02"))
            assert pc._iso_from_unix(E_2017_01_02) == "2017-01-02", tz
            assert pc._iso_from_unix(E_2017_01_02 + DAY - 1) == "2017-01-02", tz
            assert pc._iso_from_unix(E_2017_01_02 - 1) == "2017-01-01", tz
    finally:
        if hasattr(time, "tzset"):
            if saved is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = saved
            time.tzset()


def test_coinbase_rows_are_the_candle_start_date_and_the_close():
    seen = []

    def handler(url, params):
        seen.append(params)
        # [time, low, high, open, close, volume]; two candles, newest first, as the exchange answers
        return ok_json([[E_2017_01_02 + DAY, 5.0, 6.0, 7.0, 951.25, 9.0], [E_2017_01_02, 1.0, 2.0, 3.0, 950.5, 4.0]])
    code, out, rows = fetch_rows("btc", "coinbase", "2017-01-01", "2017-01-20", http=FakeHttp(handler))
    assert code == 0 and rows == [("2017-01-02", "950.5"), ("2017-01-03", "951.25")], (out, rows)
    assert seen == [{"granularity": "86400", "start": "2016-12-01T00:00:00Z", "end": "2017-01-27T00:00:00Z"}], seen


def test_binance_rows_are_the_open_time_date_and_the_close_of_btcusdt_daily():
    seen = []

    def handler(url, params):
        seen.append((url, params))
        # [open time, open, high, low, close, volume, close time]
        return ok_json([[E_2017_01_02 * 1000, "3.0", "2.0", "1.0", "950.5", "4", (E_2017_01_02 + DAY) * 1000 - 1],
                        [(E_2017_01_02 + DAY) * 1000, "7.0", "6.0", "5.0", "951.25", "9",
                         (E_2017_01_02 + 2 * DAY) * 1000 - 1]])
    code, out, rows = fetch_rows("btc", "binance", "2017-01-01", "2017-01-20", http=FakeHttp(handler))
    assert code == 0 and rows == [("2017-01-02", "950.5"), ("2017-01-03", "951.25")], (out, rows)
    assert seen == [("https://data-api.binance.vision/api/v3/klines",
                     {"symbol": "BTCUSDT", "interval": "1d", "limit": "1000", "startTime": str(E_2016_12_01 * 1000),
                      "endTime": str((E_2017_01_27 + DAY) * 1000 - 1)})], seen


def test_bitstamp_rows_are_the_candle_start_date_and_the_close_daily():
    seen = []

    def handler(url, params):
        seen.append((url, params))
        return ok_json({"data": {"pair": "BTC/USD", "ohlc": [
            {"timestamp": str(E_2017_01_02), "open": "3.0", "high": "2.0", "low": "1.0", "close": "950.5"},
            {"timestamp": str(E_2017_01_02 + DAY), "open": "7.0", "high": "6.0", "low": "5.0", "close": "951.25"}]}})
    code, out, rows = fetch_rows("btc", "bitstamp", "2017-01-01", "2017-01-20", http=FakeHttp(handler))
    assert code == 0 and rows == [("2017-01-02", "950.5"), ("2017-01-03", "951.25")], (out, rows)
    assert seen == [("https://www.bitstamp.net/api/v2/ohlc/btcusd/",
                     {"step": "86400", "limit": "1000", "start": str(E_2016_12_01), "end": str(E_2017_01_27)})], seen


def test_treasury_rows_are_the_three_month_column_of_each_yearly_file():
    seen = []

    def handler(url, params):
        seen.append((url, params))
        body = ('<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom" '
                'xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" '
                'xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices">')
        if params["field_tdr_date_value"] == "2017":
            body += ('<entry><content type="application/xml"><m:properties>'
                     '<d:NEW_DATE m:type="Edm.DateTime">2017-01-03T00:00:00</d:NEW_DATE>'
                     '<d:BC_1MONTH m:type="Edm.Double">0.52</d:BC_1MONTH>'
                     '<d:BC_3MONTH m:type="Edm.Double">0.53</d:BC_3MONTH>'
                     '<d:BC_6MONTH m:type="Edm.Double">0.65</d:BC_6MONTH></m:properties></content></entry>')
        return pc.Response(200, (body + "</feed>").encode("utf-8"))
    code, out, rows = fetch_rows("rf", "treasury", "2017-01-01", "2017-01-20", http=FakeHttp(handler))
    assert code == 0 and rows == [("2017-01-03", "0.53")], (out, rows)
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
    assert seen == [(url, {"data": "daily_treasury_yield_curve", "field_tdr_date_value": y})
                    for y in ("2016", "2017")], seen


def test_kis_asks_for_daily_split_adjusted_spy_bars():
    d0, raw0, _, _ = SPY
    seen = []
    inner = fake_kis([])

    def get(path, tr_id, params):
        seen.append((path, tr_id, dict(params)))
        return inner(path, tr_id, params)
    root = tmp()
    code, out, rows = fetch_rows("spy", "kis", SPY_WIN[0], SPY_WIN[1], kis=get, env_file=key_file(root), root=root)
    assert code == 0 and len(seen) >= 18, out
    for path, tr_id, params in seen:
        assert (path, tr_id) == ("/uapi/overseas-price/v1/quotations/dailyprice", "HHDFS76240000"), (path, tr_id)
        assert {k: v for k, v in params.items() if k != "BYMD"} == \
            {"AUTH": "", "EXCD": "AMS", "SYMB": "SPY", "GUBN": "0", "MODP": "1"}, params
    i = d0.index("2013-05-15")
    assert dict(rows)["2013-05-15"] == repr(float(f"{raw0[i]:.4f}")), dict(rows)["2013-05-15"]


def test_fetch_refuses_one_date_with_two_values_and_a_date_that_is_not_a_date():
    def two(url, params):
        return pc.Response(200, b"observation_date,DGS3MO\n2016-12-28,0.51\n2016-12-28,0.52\n")
    code, out, rows = fetch_rows("rf", "fred_now", *RF_WIN, http=FakeHttp(two))
    assert code == 4 and last_line(out) == "FETCH rf fred_now UNAVAILABLE fetch_failed exit=4 csv=-", out
    assert "a date with two different values" in out and "0.51" not in out, out

    def bad(url, params):
        return ok_json([{"date": "2016-13-45", "adjClose": 1.0}])
    root = tmp()
    code, out, rows = fetch_rows("spy", "fmp", *SPY_WIN, http=FakeHttp(bad), env_file=key_file(root), root=root)
    assert code == 4 and last_line(out) == "FETCH spy fmp UNAVAILABLE fetch_failed exit=4 csv=-", out
    assert "a row without an ISO date" in out, out


class _Answer:
    """What `urlopen` hands back: a context manager with a status and a body."""

    def __init__(self, status: int, body: bytes):
        self.status, self._body = status, body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def test_the_tool_s_own_http_function_types_every_failure_and_never_prints_the_url():
    """`urllib_get` is the one network function the tool owns, and every other case replaces it. Here it runs with
    `urlopen` replaced: an answer comes back as it is, an HTTP error status is returned with its body, and a
    transport failure becomes `fetch_failed` with the exception type only, because the text of such an error quotes
    the URL and FMP's URL holds the key."""
    root = tmp()
    keys = key_file(root)
    seen = []
    saved_open, saved_gap = urllib.request.urlopen, pc._MIN_GAP_S
    pc._MIN_GAP_S = 0.0
    try:
        def answer(request, timeout=None):
            seen.append((request.full_url, dict(request.header_items()), timeout))
            return _Answer(200, b"observation_date,DGS3MO\n2016-12-28,0.51\n")
        urllib.request.urlopen = answer
        resp = REAL_URLLIB_GET("https://example.invalid/x", {"id": "DGS3MO", "coed": "2017-01-06"}, {})
        assert (resp.status, resp.body) == (200, b"observation_date,DGS3MO\n2016-12-28,0.51\n"), resp
        url, headers, timeout = seen[0]
        assert url == "https://example.invalid/x?id=DGS3MO&coed=2017-01-06" and timeout == 30.0, seen[0]
        assert headers.get("User-agent") == "provider-parity-check/1", headers     # says nothing of the owner

        def forbidden(request, timeout=None):
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", email.message.Message(),
                                         io.BytesIO(b"no"))
        urllib.request.urlopen = forbidden
        resp = REAL_URLLIB_GET("https://example.invalid/x", {"a": "1"}, {})
        assert (resp.status, resp.body) == (403, b"no"), resp

        def unreachable(request, timeout=None):
            raise urllib.error.URLError(f"cannot reach {request.full_url}")
        urllib.request.urlopen = unreachable
        with env_without(*pc.KEY_NAMES):
            code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys, root=root,
                                      http=REAL_URLLIB_GET)
        assert code == 4 and last_line(out) == "FETCH spy fmp UNAVAILABLE fetch_failed exit=4 csv=-", out
        assert out.splitlines()[-2] == "UNAVAILABLE: request failed (URLError)" and not folder.exists(), out
        assert "apikey" not in out and "financialmodelingprep" not in out and FMP_KEY not in out, out

        def slow(request, timeout=None):
            raise TimeoutError(f"timed out reading {request.full_url}")
        urllib.request.urlopen = slow
        try:
            REAL_URLLIB_GET("https://example.invalid/x", {"apikey": FMP_KEY}, {})
        except pc.FetchFailed as exc:
            assert (exc.reason, str(exc)) == ("fetch_failed", "request failed (TimeoutError)"), (exc.reason, str(exc))
        else:
            raise AssertionError("a timeout was not typed")
    finally:
        urllib.request.urlopen, pc._MIN_GAP_S = saved_open, saved_gap


def facts_section() -> str:
    """The tool's own section of docs/compliance/FACTS.md, from its anchor to the next one."""
    text = FACTS.read_text(encoding="utf-8")
    start = text.index('<a id="provider-parity-2026-11-11"></a>')
    end = text.find('<a id="', start + 10)
    return text[start:] if end < 0 else text[start:end]


def test_every_request_is_bounded_before_2027_and_the_documents_say_how():
    """No observation dated on or after 2027-01-01 is requested (spec 10.5). With a window that ends on 2026-12-29
    the fetch would run 7 days on, and each provider's request stops short of 2027 in its own way: an explicit last
    date of 2026-12-30 (an exclusive end of 2026-12-31 for yfinance, the last millisecond of 2026-12-30 for Binance)
    or, for the Treasury's yearly file, the calendar year 2026. The tool's docstring, the owner guide and the
    compliance facts say that, and no longer that every request names a last date."""
    root = tmp()
    keys = key_file(root)
    kis_calls, yf_calls, seen = [], [], {}

    def kis(path, tr_id, params):
        kis_calls.append(dict(params))
        return {"rt_cd": "0", "output2": []}

    def yf(symbol, start, end):
        yf_calls.append((symbol, start, end))
        return pd.DataFrame()
    empty = {"fmp": ok_json([]), "coinbase": ok_json([]), "bitstamp": ok_json({"data": {"ohlc": []}}),
             "binance": ok_json([]), "h15": pc.Response(200, b""),
             "treasury": pc.Response(200, b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'),
             "fred_now": pc.Response(200, b"observation_date,DGS3MO\n")}
    for series, table in pc.PROVIDERS.items():
        for provider in table:
            http = FakeHttp(lambda url, params, provider=provider: empty[provider])
            with env_without(*pc.KEY_NAMES):
                code, out, folder = fetch(series, provider, start="2025-06-01", end="2026-12-29", http=http, yf=yf,
                                          kis=kis, env_file=keys, root=root)
            assert code == 4 and not folder.exists(), (provider, out)        # an empty answer: nothing is written
            seen[provider] = [params for _, params in http.calls]
    assert seen["fmp"] == [{"symbol": "SPY", "from": "2025-05-01", "to": "2026-12-30", "apikey": FMP_KEY}], seen["fmp"]
    assert [c["BYMD"] for c in kis_calls] == ["20261230"], kis_calls
    assert yf_calls == [("SPY", "2025-05-01", "2026-12-31")], yf_calls
    assert len(seen["coinbase"]) == 3 and seen["coinbase"][-1]["end"] == "2026-12-30T00:00:00Z", seen["coinbase"]
    assert [p["end"] for p in seen["bitstamp"]] == [str(E_2026_12_30)], seen["bitstamp"]
    assert [p["endTime"] for p in seen["binance"]] == [str((E_2026_12_30 + DAY) * 1000 - 1)], seen["binance"]
    assert seen["treasury"] == [{"data": "daily_treasury_yield_curve", "field_tdr_date_value": y}
                                for y in ("2025", "2026")], seen["treasury"]
    assert (seen["h15"][0]["from"], seen["h15"][0]["to"]) == ("05/01/2025", "12/30/2026"), seen["h15"]
    assert seen["fred_now"] == [{"id": "DGS3MO", "cosd": "2025-05-01", "coed": "2026-12-30"}], seen["fred_now"]
    for name, text, old, new in (
            ("docstring", pc.__doc__, "Every request names an explicit last date", "calendar year of at most 2026"),
            ("guide", GUIDE.read_text(encoding="utf-8"), "Every request names its last date",
             "calendar year of at most 2026"),
            ("facts", facts_section(), "모든 요청이 끝 날짜", "달력 연도")):
        flat = " ".join(text.split())
        assert old not in flat and new in flat, name


# --------------------------------------------------------------------------- #
# Review of 2026-11-11, part 2: rules no case held, and guards from their other side
# --------------------------------------------------------------------------- #
def test_duplicated_or_unsorted_dates_are_refused_on_both_sides():
    d0, _, adj0, _ = SPY
    b = provider_text(d0, adj0 * 0.987, 6).splitlines(keepends=True)
    for name, text in (("a date twice", "".join(b[:500] + [b[499]] + b[500:])),
                       ("two dates swapped", "".join(b[:500] + [b[501], b[500]] + b[502:]))):
        w = spy_world()
        code, out, s, path = w.compare([("fmp", w.file("dup.csv", text))])
        assert code == 2 and s is None and not path.exists() and "strictly increasing and unique" in out, (name, out)
        assert last_line(out) == "PARITY spy REFUSED exit=2 summary=-", out
    a = pinned_text("Date,yf_SPY", d0, adj0).splitlines(keepends=True)
    for name, text in (("a date twice", "".join(a[:900] + [a[899]] + a[900:])),
                       ("two dates swapped", "".join(a[:900] + [a[901], a[900]] + a[902:]))):
        w = World("spy", text, start=SPY_WIN[0], end=SPY_WIN[1])
        code, out, s, path = w.compare([("fmp", w.file("ok.csv", "".join(b)))])
        assert code == 2 and s is None and not path.exists() and "strictly increasing and unique" in out, (name, out)


def test_a_close_that_is_not_positive_in_a_fails_its_integrity_check():
    """A zero or negative close is dropped as the study drops it, and the dropped row fails A's integrity check."""
    d0, _, adj0, _ = SPY
    vals = adj0.copy()
    vals[d0.index("2013-05-15")] = 0.0
    w = spy_world(adj=vals)
    fmp, _, _ = spy_b(w)
    code, out, s, _ = w.compare([("fmp", fmp)])
    integ = s["integrity"][0]
    assert code == 1 and integ["outcome"] == "FAIL" and integ["no_split_shaped_jump"] is True, integ
    assert integ["n_dropped_nonpositive"] == 1 and integ["n_rows"] == 1824, integ
    d, p, v = BTC
    bp = p.copy()
    bp[900] = -1.0
    code, out, s, _ = btc_run(btc_world(a_vals=bp), d, v)
    integ = s["integrity"][0]
    assert code == 1 and integ["outcome"] == "FAIL" and integ["n_dropped_nonpositive"] == 1, integ
    assert integ["no_implausible_jump"] is True and integ["n_missing_days_a"] == 1, integ


def test_summary_hashes_are_the_files_own():
    """10.5: a run with other tool bytes must be recognisable, so `tool.sha256` is the sha256 of the tool file that
    ran and each pair's `file_sha256` is that of the file compared."""
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    code, out, s, _ = w.compare([("fmp", fmp), ("kis", kis)])
    assert code == 0 and s["tool"]["sha256"] == hashlib.sha256(Path(pc.__file__).read_bytes()).hexdigest(), out
    assert {p["provider"]: p["file_sha256"] for p in s["pairs"]} == {
        "fmp": hashlib.sha256(fmp.read_bytes()).hexdigest(), "kis": hashlib.sha256(kis.read_bytes()).hexdigest()}
    assert s["pinned"]["md5"] == hashlib.md5((w.repo / "synthetic" / "yf_SPY.csv").read_bytes()).hexdigest()


def test_out_folder_deep_inside_a_work_tree_and_names_in_another_case_are_refused():
    w = spy_world()
    fmp, _, _ = spy_b(w)
    code, out, _, _ = w.compare([("fmp", fmp)], out=w.repo / "a" / "b" / "c" / "pp_out")
    assert code == 2 and "git work tree" in out and not (w.repo / "a").exists(), out
    code, out, _, _ = w.compare([("fmp", fmp)], out=w.root / "x" / "Asset_Expansion" / "run")
    assert code == 2 and "asset_expansion" in out and not (w.root / "x").exists(), out
    table = json.loads(w.table.read_text(encoding="utf-8"))
    for rel, why in (("docs/Asset_Expansion/CACHE/yf_SPY.csv", "--owner-run"),
                     ("synthetic\\..\\..\\elsewhere/yf_SPY.csv", "relative path to yf_SPY.csv"),
                     (str((w.repo / "synthetic" / "yf_SPY.csv").resolve()), "relative path to yf_SPY.csv")):
        table["prices_file"] = rel
        w.table.write_text(json.dumps(table), encoding="utf-8")
        code, out, s, path = w.compare([("fmp", fmp)])
        assert code == 2 and s is None and not path.exists() and why in out, (rel, out)


def test_spy_drift_alone_and_one_day_maximum_alone_each_fail_the_pair():
    """drift_range_max 5e-3 and ret_diff_max 2e-3 each decide alone: a provider that drifts away by 1e-5 a day has no
    day above the tolerance, and one tick 0.3% off moves two days above ret_diff_max without moving the drift."""
    d0, _, adj0, _ = SPY
    w = spy_world()
    steady = adj0 * np.exp(-1e-5 * np.arange(len(d0)))
    code, out, s, _ = w.compare([("fmp", w.file("drift.csv", provider_text(d0, steady, 8)))])
    same = check_of(s, "fmp", "returns_same_convention")
    assert same["n_over_tol"] == 0 and same["max_ok"] is True and same["drift_ok"] is False, same
    assert code == 1 and same["outcome"] == "FAIL" and s["outcome"] == "FAIL", out
    tick = adj0 * 0.987
    tick[d0.index("2014-02-12")] *= 1.003
    w = spy_world()
    code, out, s, _ = w.compare([("fmp", w.file("tick.csv", provider_text(d0, tick, 8)))])
    same = check_of(s, "fmp", "returns_same_convention")
    assert same["n_over_tol"] == 2 <= same["n_allowed"] and same["drift_ok"] is True and same["max_ok"] is False, same
    assert code == 1 and same["outcome"] == "FAIL" and s["outcome"] == "FAIL", out


def test_env_file_whose_first_line_is_a_key_after_a_bom():
    root = tmp()
    path = root / "env.txt"
    path.write_bytes(b"\xef\xbb\xbf" + f"FMP_API_KEY={FMP_KEY}\r\n".encode("ascii"))
    assert pc.load_keys(path, environ={}) == {"FMP_API_KEY": FMP_KEY}


def test_a_provider_file_needs_the_date_value_header():
    d0, _, adj0, _ = SPY
    w = spy_world()
    text = provider_text(d0, adj0 * 0.987, 6).replace("date,value", "Date,Close", 1)
    code, out, s, path = w.compare([("fmp", w.file("hdr.csv", text))])
    assert code == 2 and s is None and not path.exists() and "the header must be `date,value`" in out, out


def test_a_pinned_file_with_one_value_in_the_window_is_refused():
    d0, _, adj0, _ = SPY
    w = World("spy", pinned_text("Date,yf_SPY", d0, adj0), start="2013-05-15", end="2013-05-15")
    code, out, s, path = w.compare([("fmp", w.file("spy_fmp.csv", provider_text(d0, adj0 * 0.987, 6)))])
    assert code == 2 and s is None and not path.exists() and "fewer than two values" in out, out


def test_kis_and_yfinance_failures_print_the_exception_type_never_its_text():
    root = tmp()
    keys = key_file(root)

    def kis_boom(path, tr_id, params):
        raise RuntimeError("request with close 4321.12 failed")

    class KISUnavailable(RuntimeError):
        pass

    def kis_unset(path, tr_id, params):
        raise KISUnavailable("no key; last close 4321.12")
    for getter, said, reason in ((kis_boom, "RuntimeError", "fetch_failed"), (kis_unset, "KISUnavailable", "no_key")):
        with env_without(*pc.KEY_NAMES):
            code, out, folder = fetch("spy", "kis", start=SPY_WIN[0], end=SPY_WIN[1], kis=getter, env_file=keys,
                                      root=root)
        assert code == 4 and out.splitlines()[-2] == f"UNAVAILABLE: kis request failed ({said})", out
        assert last_line(out) == f"FETCH spy kis UNAVAILABLE {reason} exit=4 csv=-" and "4321" not in out, out
        assert not folder.exists()

    def yf_boom(symbol, start, end):
        raise ValueError("SPY close 4321.12 could not be parsed")
    code, out, folder = fetch("spy", "yahoo_now", start=SPY_WIN[0], end=SPY_WIN[1], yf=yf_boom, root=root)
    assert code == 4 and out.splitlines()[-2] == "UNAVAILABLE: yfinance failed (ValueError)", out
    assert last_line(out) == "FETCH spy yahoo_now UNAVAILABLE fetch_failed exit=4 csv=-" and "4321" not in out, out


def test_a_key_value_in_the_fetch_record_is_refused():
    """A fetcher that let the key into the request parameters it records: the fetch record would carry it, so the
    fetch is refused and nothing is written."""
    root = tmp()
    real = pc.FETCHERS["fmp"]

    def leaky(ctx):
        got = real(ctx)
        return pc.Fetched([{**got.requests[0], "apikey": ctx.key("FMP_API_KEY")}], got.pages, got.rows)
    pc.FETCHERS["fmp"] = leaky
    try:
        with env_without(*pc.KEY_NAMES):
            code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=FakeHttp(fmp_handler),
                                      env_file=key_file(root), root=root)
    finally:
        pc.FETCHERS["fmp"] = real
    assert code == 2 and not folder.exists() and "a key value reached the fetch record" in out, out
    assert FMP_KEY not in out and last_line(out) == "FETCH spy fmp REFUSED exit=2 csv=-", out


def test_yfinance_is_asked_for_adjusted_closes_with_its_cache_in_a_temporary_folder():
    """`yahoo_now` is today's vintage of the pinned file, which was made with auto_adjust=True. A stand-in module
    named yfinance takes the call `_yf_default` makes: the adjusted series, the dates as given, no progress bar and no
    threads, and a cache folder that exists for the call only (never under the home folder)."""
    calls, located, existed = [], [], []
    stand_in = types.ModuleType("yfinance")

    def download(symbol, **kw):
        calls.append((symbol, kw))
        existed.append(Path(located[-1]).is_dir())
        return "frame"
    stand_in.download = download
    stand_in.set_tz_cache_location = located.append
    saved = sys.modules.get("yfinance", _ABSENT)
    sys.modules["yfinance"] = stand_in
    try:
        got = pc._yf_default("SPY", "2016-12-01", "2017-01-28")
    finally:
        if saved is _ABSENT:
            sys.modules.pop("yfinance", None)
        else:
            sys.modules["yfinance"] = saved
    assert got == "frame" and calls == [("SPY", {"start": "2016-12-01", "end": "2017-01-28", "auto_adjust": True,
                                                 "progress": False, "threads": False})], calls
    assert len(located) == 1 and existed == [True] and not Path(located[0]).exists(), located
    assert Path(located[0]).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), located


def test_text_files_keep_lf_where_text_mode_would_write_crlf():
    """Windows text mode writes CRLF for every newline unless a file is opened with newline="\\n", and pandas'
    to_csv ends its lines with os.linesep. On Windows that is the platform's own behaviour, and the case
    test_every_file_the_tool_writes_is_utf8_with_lf_only meets it. Elsewhere it is simulated here: `_pyio.open`, the
    pure Python `open` that takes its line ending from os.linesep, in place of the tool's `open`, with os.linesep set
    to CRLF."""
    if os.linesep == "\r\n":
        return
    import _pyio
    root = tmp()
    keys = key_file(root)
    saved = os.linesep
    pc.open = _pyio.open
    os.linesep = "\r\n"
    try:
        folders = []
        with env_without(*pc.KEY_NAMES):
            for provider, kw in (("fmp", dict(http=FakeHttp(fmp_handler))), ("kis", dict(kis=fake_kis([]))),
                                 ("yahoo_now", dict(yf=fake_yf([])))):
                code, out, folder = fetch("spy", provider, start=SPY_WIN[0], end=SPY_WIN[1], env_file=keys,
                                          root=root, **kw)
                assert code == 0, out
                folders.append(folder)
        w = spy_world()
        code, out, _, compared = w.compare([(q, f / f"spy_{q}.csv")
                                            for q, f in zip(("fmp", "kis", "yahoo_now"), folders)])
        assert code == 0, out
    finally:
        os.linesep = saved
        del pc.open
    files = [x for f in (*folders, compared) for x in sorted(f.rglob("*")) if x.is_file()]
    assert len(files) >= 11 and not [x.name for x in files if b"\r" in x.read_bytes()], files
    for folder in folders:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        assert hashlib.sha256((folder / meta["csv"]["file"]).read_bytes()).hexdigest() == meta["csv"]["sha256"]


# --------------------------------------------------------------------------- #
# Review of 2026-11-11, part 3: what the review changed in the tool
# --------------------------------------------------------------------------- #
def test_a_pinned_cache_path_is_judged_as_spelled_and_as_it_resolves():
    """Without --owner-run a file under a folder named asset_expansion/cache is refused before it is opened, in any
    letter case, as the pinned file or as a provider file, and also when the path only leads there through a link (a
    junction on Windows). The folder here is a synthetic one in the temp dir."""
    w = spy_world()
    fmp, _, _ = spy_b(w)
    cache = w.repo / "docs" / "Asset_Expansion" / "Cache"
    cache.mkdir(parents=True)
    (cache / "yf_SPY.csv").write_bytes((w.repo / "synthetic" / "yf_SPY.csv").read_bytes())
    held = cache / "spy_fmp.csv"
    held.write_bytes(fmp.read_bytes())
    code, out, s, path = w.compare([("fmp", held)])                 # a provider file kept in the cache folder
    assert code == 2 and s is None and "--owner-run" in out and not path.exists(), out
    code, out, s, _ = w.compare([("fmp", held)], extra=["--owner-run"])
    assert code == 0 and s["outcome"] == "PASS", out
    try:
        (w.repo / "alias").symlink_to(cache, target_is_directory=True)
    except (OSError, NotImplementedError):                          # no right to make a link on this machine
        return
    code, out, s, path = w.compare([("fmp", w.repo / "alias" / "spy_fmp.csv")])
    assert code == 2 and s is None and "--owner-run" in out and not path.exists(), out
    elsewhere = w.root / "elsewhere"                                # and a `cache` that is itself a link out
    elsewhere.mkdir()
    (elsewhere / "spy_fmp.csv").write_bytes(fmp.read_bytes())
    (w.root / "data" / "asset_expansion").mkdir(parents=True)
    (w.root / "data" / "asset_expansion" / "cache").symlink_to(elsewhere, target_is_directory=True)
    code, out, s, path = w.compare([("fmp", w.root / "data" / "asset_expansion" / "cache" / "spy_fmp.csv")])
    assert code == 2 and s is None and "--owner-run" in out and not path.exists(), out
    table = json.loads(w.table.read_text(encoding="utf-8"))
    table["prices_file"] = "alias/yf_SPY.csv"
    w.table.write_text(json.dumps(table), encoding="utf-8")
    code, out, s, path = w.compare([("fmp", fmp)])
    assert code == 2 and s is None and "--owner-run" in out and not path.exists(), out
    assert last_line(out) == "PARITY spy REFUSED exit=2 summary=-", out
    code, out, s, _ = w.compare([("fmp", fmp)], extra=["--owner-run"])
    assert code == 0 and s["outcome"] == "PASS", out


def test_a_provider_file_must_be_the_one_its_fetch_record_describes():
    """A fetch folder records its CSV's name and sha256. A file changed, renamed or replaced after its fetch is
    refused; a file with no fetch record beside it is compared, and the summary says so for each pair."""
    root = tmp()
    keys = key_file(root)
    with env_without(*pc.KEY_NAMES):
        code, out, f_fmp = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=FakeHttp(fmp_handler),
                                 env_file=keys, root=root)
        code2, out2, f_yahoo = fetch("spy", "yahoo_now", start=SPY_WIN[0], end=SPY_WIN[1], yf=fake_yf([]), root=root)
    assert code == 0 and code2 == 0, (out, out2)
    w = spy_world()
    _, kis, _ = spy_b(w)                                             # a loose file: no fetch record beside it
    code, out, s, _ = w.compare([("fmp", f_fmp / "spy_fmp.csv"), ("kis", kis),
                                 ("yahoo_now", f_yahoo / "spy_yahoo_now.csv")])
    assert code == 0 and s["outcome"] == "PASS", out
    assert {p["provider"]: p["has_fetch_record"] for p in s["pairs"]} == {"fmp": True, "kis": False,
                                                                          "yahoo_now": True}, s["pairs"]
    # the yahoo_now file is refused as fmp where its record is; copied elsewhere it is compared, without a record
    code, out, s, _ = w.compare([("fmp", f_yahoo / "spy_yahoo_now.csv")])
    assert code == 2 and "another provider" in out, out
    loose = root / "loose" / "spy_fmp.csv"
    loose.parent.mkdir()
    loose.write_bytes((f_yahoo / "spy_yahoo_now.csv").read_bytes())
    code, out, s, _ = w.compare([("fmp", loose)])
    assert code == 0 and s["pairs"][0]["has_fetch_record"] is False, out
    # the fetched file under another name in its folder, then one value changed by hand
    csv = f_fmp / "spy_fmp.csv"
    renamed = f_fmp / "spy_fmp_edited.csv"
    renamed.write_bytes(csv.read_bytes())
    lines = csv.read_text(encoding="utf-8").splitlines()
    lines[900] = lines[900].split(",")[0] + "," + lines[899].split(",")[1]
    csv.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    for path in (renamed, csv):
        code, out, s, folder = w.compare([("fmp", path)])
        assert code == 2 and s is None and not folder.exists(), (path.name, out)
        assert "not the file its fetch record describes" in out, out
        assert last_line(out) == "PARITY spy REFUSED exit=2 summary=-", out


def test_rf_infinite_value_is_a_value_outside_the_range_and_is_refused_in_a_provider_file():
    """For the cash rate only a missing value is a published blank. An infinite value in the pinned file is a value
    outside range_pct (the runner's dropna keeps it too), so the units check fails; a provider file never holds one
    (a fetch writes a finite number or a blank cell), so such a file is refused, for every series."""
    days, vals, hol = RF
    m = next(i for i, d in enumerate(days) if d >= "2013-05-15" and i not in hol)
    for cell in ("inf", "-inf"):
        a = pinned_text("DATE,DGS3MO", days, [np.nan if i in hol else x for i, x in enumerate(vals)])
        a = a.splitlines(keepends=True)
        a[m + 1] = f"{days[m]},{cell}\n"
        w = World("rf", "".join(a), start=RF_WIN[0], end=RF_WIN[1])
        code, out, s, _ = rf_run(w, *rf_b(vals, drop_holidays=False))
        units = s["integrity"][0]
        assert units["id"] == "units" and units["outcome"] == "FAIL" and units["percent_units_ok"] is False, (cell, s)
        assert code == 1 and s["outcome"] == "FAIL", (cell, out)
        blanks = check_of(s, "treasury", "blanks")
        assert blanks["n_blank_a_value_b"] > 0 and days[m] not in blanks["blank_a_value_b"], (cell, blanks)
        assert check_of(s, "treasury", "values")["n_off_by_tol"] == 1, cell
    b_days, b_vals = rf_b(vals)
    b = provider_text(b_days, b_vals, 2).splitlines(keepends=True)
    k = b_days.index(days[m]) + 1
    d0, _, adj0, _ = SPY
    spy_lines = provider_text(d0, adj0 * 0.987, 6).splitlines(keepends=True)
    j = d0.index("2013-05-15") + 1
    for cell in ("inf", "-inf"):
        w = rf_world()
        code, out, s, path = w.compare([("treasury", w.file("rf_inf.csv", "".join(b[:k] + [f"{days[m]},{cell}\n"]
                                                                                 + b[k + 1:])))])
        assert code == 2 and s is None and not path.exists() and "not a finite number" in out, (cell, out)
        w = spy_world()
        code, out, s, path = w.compare([("fmp", w.file("spy_inf.csv", "".join(spy_lines[:j] + [f"2013-05-15,{cell}\n"]
                                                                              + spy_lines[j + 1:])))])
        assert code == 2 and s is None and not path.exists() and "not a finite number" in out, (cell, out)


def test_a_failed_write_never_leaves_a_summary_and_names_a_folder_it_cannot_remove():
    """detail.json is written first and summary.json last. When a write fails and the folder cannot be removed
    either (a file held by a scanner or a sync client), what is left is never a summary without its detail, and the
    line above the ERROR line names the folder; when the folder can be removed, nothing is left and nothing is said."""
    real_rmtree, real_open = shutil.rmtree, open

    def held(path, ignore_errors=False, **_k):                      # the removal changes nothing
        if not ignore_errors:
            raise PermissionError(13, "sharing violation")
    for blocked, removable in (("detail.json", False), ("summary.json", False), ("summary.json", True)):
        def failing_open(file, mode="r", *a, blocked=blocked, **k):
            if Path(file).name == blocked and "x" in mode:
                raise PermissionError(13, "used by another process")
            return real_open(file, mode, *a, **k)
        w = spy_world()
        fmp, kis, _ = spy_b(w)
        pc.open = failing_open
        if not removable:
            pc.shutil.rmtree = held
        try:
            code, out, s, folder = w.compare([("fmp", fmp), ("kis", kis)])
        finally:
            pc.shutil.rmtree = real_rmtree
            del pc.open
        lines = out.strip().splitlines()
        assert code == 4 and s is None and lines[-1] == "PARITY spy ERROR exit=4 summary=-", out
        assert lines[-2].startswith("ERROR: PermissionError at parity_check.py lines "), out
        if removable:
            assert "LEFT BEHIND" not in out and not folder.exists(), out
            continue
        assert lines[-3] == f"LEFT BEHIND: {folder} could not be removed; it is not a result, delete it by hand", out
        assert sorted(p.name for p in folder.iterdir()) == ([] if blocked == "detail.json" else ["detail.json"])


def test_fetch_prints_one_calendar_fact_of_the_provider_s_own_dates():
    """A date label one calendar day off (a Korean date, or UTC midnight read in local time) shows at fetch, before
    compare makes the run of record: `weekend dates` for SPY and DGS3MO, whose dates have none when they are session
    dates, and `missing days` inside the file's own span for BTC-USD. Counts of dates only."""
    d0, _, _, _ = SPY
    root = tmp()
    keys = key_file(root)
    next_day = [(date.fromisoformat(x) + timedelta(days=1)).isoformat() for x in d0]
    for name, labels in (("session", d0), ("next_day", next_day)):
        with env_without(*pc.KEY_NAMES):
            code, out, folder = fetch("spy", "kis", start=SPY_WIN[0], end=SPY_WIN[1], kis=fake_kis([], labels),
                                      env_file=keys, root=root / name)
        assert code == 0, out
        rows = read_csv_rows(folder / "spy_kis.csv")
        weekend = sum(1 for x, _ in rows if date.fromisoformat(x).weekday() >= 5)
        assert (weekend == 0) if name == "session" else (weekend > 300), (name, weekend)
        assert out.splitlines()[-2] == f"rows {len(rows)}, first {rows[0][0]}, last {rows[-1][0]}, " \
                                       f"weekend dates {weekend}", out
        assert json.loads((folder / "meta.json").read_text(encoding="utf-8"))["csv"]["n_weekend_dates"] == weekend
    d, _, v = BTC
    gone = {d[200], d[201], d[900]}

    def coinbase_with_an_outage(url, params):
        lo, hi = params["start"][:10], params["end"][:10]
        return ok_json([[calendar.timegm(date.fromisoformat(d[i]).timetuple()), 0, 0, 0, round(float(v[i]), 2), 1.0]
                        for i in reversed(in_span(d, lo, hi)) if d[i] not in gone])
    code, out, folder = fetch("btc", "coinbase", start=BTC_WIN[0], end=BTC_WIN[1],
                              http=FakeHttp(coinbase_with_an_outage), root=root)
    rows = read_csv_rows(folder / "btc_coinbase.csv")
    assert code == 0 and out.splitlines()[-2] == f"rows {len(rows)}, first {d[0]}, last {d[-1]}, missing days 3", out
    assert json.loads((folder / "meta.json").read_text(encoding="utf-8"))["csv"]["n_missing_days"] == 3
    code, out, folder = fetch("rf", "fred_now", start=RF_WIN[0], end=RF_WIN[1], http=FakeHttp(fred_handler), root=root)
    assert code == 0 and out.splitlines()[-2].endswith(", weekend dates 0"), out


def test_an_error_answer_is_quoted_for_a_provider_without_a_key_and_never_for_fmp():
    """A first run that fails has to be diagnosed from the two lines the owner sends back. For the providers that
    take no key, the line above the result quotes the start of the provider's error answer: at most 200 bytes,
    printable ASCII only (anything else, and the backslash, as \\xNN) and every decimal number masked. Not for fmp,
    whose URL holds the key, and not for an answer that is not an error."""
    body = b'{"message":"granularity too small for the requested time range"}'
    code, out, folder = fetch("btc", "coinbase", start="2017-01-01", end="2017-01-20",
                              http=FakeHttp(lambda u, p: pc.Response(400, body)))
    assert out.splitlines()[-2] == ('UNAVAILABLE: coinbase: HTTP 400, the answer starts: '
                                    '{"message":"granularity too small for the requested time range"}'), out
    assert code == 4 and last_line(out) == "FETCH btc coinbase UNAVAILABLE fetch_failed exit=4 csv=-", out
    head = "<html>접근 \\ last 43210.55 at 1.5\r\n".encode("utf-8")
    code, out, folder = fetch("rf", "fred_now", start=RF_WIN[0], end=RF_WIN[1],
                              http=FakeHttp(lambda u, p: pc.Response(403, head + b"x" * 400)))
    line = out.splitlines()[-2]
    kept = 200 - len(head)
    assert line.startswith("UNAVAILABLE: fred_now: HTTP 403, the answer starts: <html>\\xec\\xa0\\x91\\xea\\xb7\\xbc "
                           "\\x5c last #.# at #.#\\x0d\\x0a"), line
    assert line.isascii() and "43210" not in line and line.endswith("\\x0a" + "x" * kept), line
    assert code == 4 and last_line(out) == "FETCH rf fred_now UNAVAILABLE plan_or_access exit=4 csv=-", out
    code, out, folder = fetch("btc", "coinbase", start="2017-01-01", end="2017-01-20",
                              http=FakeHttp(lambda u, p: pc.Response(204, b"close 43210.55")))
    assert out.splitlines()[-2] == "UNAVAILABLE: coinbase: HTTP 204" and "43210" not in out, out
    root = tmp()
    code, out, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], env_file=key_file(root), root=root,
                              http=FakeHttp(lambda u, p: pc.Response(402, b'{"Error Message":"upgrade the plan"}')))
    assert out.splitlines()[-2] == "UNAVAILABLE: fmp: HTTP 402", out
    assert code == 4 and last_line(out) == "FETCH spy fmp UNAVAILABLE plan_or_access exit=4 csv=-", out
    assert pc.KEYLESS == {"coinbase", "bitstamp", "binance", "treasury", "h15", "fred_now"}


def test_kis_failure_line_gives_the_status_and_the_message_code_only():
    """The app's KIS client raises KISError with a message of its own making. The line names what fixed patterns
    find in it (the token step, the HTTP status, KIS's message code, a transport error's type) and never the text,
    which can hold the provider's free wording."""
    class KISError(RuntimeError):
        pass
    root = tmp()
    keys = key_file(root)
    cases = {"HHDFS76240000: HTTP 500 (EGW00123: 기간이 만료된 token 4321.12)":
             "KISError; HTTP 500, msg_cd EGW00123",
             "token rejected (HTTP 403)": "KISError; token, HTTP 403",
             "token request failed: ConnectionError": "KISError; token, ConnectionError",
             "HHDFS76240000: ConnectTimeout": "KISError; ConnectTimeout",
             "HHDFS76240000: 해당 종목정보가 없습니다 4321.12": "KISError"}
    for n, (text, said) in enumerate(cases.items()):
        def getter(path, tr_id, params, text=text):
            raise KISError(text)
        with env_without(*pc.KEY_NAMES):
            code, out, folder = fetch("spy", "kis", start=SPY_WIN[0], end=SPY_WIN[1], kis=getter, env_file=keys,
                                      root=root / str(n))
        assert code == 4 and out.splitlines()[-2] == f"UNAVAILABLE: kis request failed ({said})", (text, out)
        assert last_line(out) == "FETCH spy kis UNAVAILABLE fetch_failed exit=4 csv=-", out
        assert "4321" not in out and "종목" not in out and "만료" not in out, out


def test_an_unexpected_exception_names_the_tool_s_own_lines_and_nothing_else():
    """ERROR prints the exception type and where in the tool it passed: line numbers only, outermost first. The
    numbers are real lines of the tool file; the exception's text is never printed."""
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    real = pc.assert_summary_safe

    def boom(*_a, **_k):
        raise ValueError("close 4321.12 leaked")
    pc.assert_summary_safe = boom
    try:
        code, out, s, path = w.compare([("fmp", fmp), ("kis", kis)])
    finally:
        pc.assert_summary_safe = real
    found = re.fullmatch(r"ERROR: ValueError at parity_check\.py lines (\d+(?: > \d+)*)", out.splitlines()[-2])
    assert code == 4 and s is None and not path.exists() and found, out
    assert "4321.12" not in out and "leaked" not in out, out
    source = Path(pc.__file__).read_text(encoding="utf-8").splitlines()
    numbers = [int(x) for x in found.group(1).split(" > ")]
    assert "run_compare(" in source[numbers[0] - 1], numbers
    assert "assert_summary_safe(summary)" in source[numbers[-1] - 1], numbers


def test_an_output_folder_inside_onedrive_is_refused():
    """OneDrive uploads what is written into its folder, and detail.json and the raw responses stay on the owner's
    machine (spec 10.5, Outputs). A folder whose path has a part starting with OneDrive is refused, in any letter
    case, and so is one inside the folder a OneDrive environment variable names, before anything is fetched."""
    w = spy_world()
    fmp, _, _ = spy_b(w)
    base = w.root / "Users" / "사용자"
    for part in ("OneDrive", "onedrive - Example Org"):
        code, text, s, _ = w.compare([("fmp", fmp)], out=base / part / "문서" / "pp" / "C-1")
        assert code == 2 and s is None and "OneDrive" in text and not base.exists(), (part, text)
        assert last_line(text) == "PARITY spy REFUSED exit=2 summary=-", text
        http = FakeHttp(fmp_handler)
        code, text, folder = fetch("spy", "fmp", start=SPY_WIN[0], end=SPY_WIN[1], http=http, root=base / part / "pp")
        assert code == 2 and http.calls == [] and "OneDrive" in text and not base.exists(), (part, text)
    assert pc.SYNCED_ROOT_NAMES == ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")
    moved = w.root / "CloudFiles"                                   # a OneDrive folder under another name
    saved = {n: os.environ.get(n) for n in pc.SYNCED_ROOT_NAMES}
    try:
        for k, name in enumerate(pc.SYNCED_ROOT_NAMES):
            for n in pc.SYNCED_ROOT_NAMES:
                os.environ.pop(n, None)
            os.environ[name] = str(moved)
            code, text, s, _ = w.compare([("fmp", fmp)], out=moved / "pp" / "C-1")
            assert code == 2 and s is None and "OneDrive" in text and not moved.exists(), (name, text)
            code, text, s, _ = w.compare([("fmp", fmp)], out=w.root / "CloudFilesToo" / f"C-{k}")
            assert code == 0 and s["outcome"] == "PASS", (name, text)     # a sibling whose name only starts alike
        for n in pc.SYNCED_ROOT_NAMES:
            os.environ.pop(n, None)
        code, text, s, _ = w.compare([("fmp", fmp)], out=moved / "pp" / "C-1")       # no variable names it now
        assert code == 0 and s["outcome"] == "PASS", text
    finally:
        for n, value in saved.items():
            if value is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = value


# --------------------------------------------------------------------------- #
# Review of 2026-11-11, part 4: the documents and the files this branch leaves alone
# --------------------------------------------------------------------------- #
def test_the_guide_matches_the_tool_and_says_what_is_not_settled():
    """The owner follows the guide, so it is held to the tool: the number of cases; the tool's sha256 once an owner
    ruling has fixed it (until then both lines say so, and the guide says it is not ready and why); and the notes a
    reader needs on what the tool leaves out and what a WITHHELD or a failed run means."""
    guide = GUIDE.read_text(encoding="utf-8")
    flat = " ".join(guide.split())
    assert f"{len(tests())} cases on synthetic series" in flat, len(tests())
    fixed = dict(re.findall(r"^Tool (commit|sha256) fixed by the owner ruling: (.+)$", guide, flags=re.M))
    assert set(fixed) == {"commit", "sha256"}, fixed
    unset = "not fixed yet"
    assert fixed["sha256"] in (unset, hashlib.sha256(Path(pc.__file__).read_bytes()).hexdigest()), \
        "the guide fixes a sha256 that is not this tool file's"
    assert (fixed["commit"] == unset) == (fixed["sha256"] == unset), fixed
    assert fixed["commit"] == unset or re.fullmatch(r"[0-9a-f]{40}", fixed["commit"]), fixed
    if fixed["sha256"] == unset:
        assert "not ready to be followed" in flat and "777fc5b" in flat, "the guide must say why it cannot be run yet"
    for phrase in ("signed NYSE calendar. That check is not built",             # the draft's 4.1 clause, left out
                   "`n_common` near 80 % of `n_a`",                             # a date label one day off
                   "`weekend dates` must be 0", "`has_fetch_record`", "LEFT BEHIND", "OneDrive",
                   "is not registered in `tests/run_all.py`"):
        assert phrase in flat, phrase


def test_the_root_readme_and_run_all_do_not_name_this_suite():
    """The root README.md and tests/run_all.py stay as they are on main. A README edit without a regenerated
    qa/research_status.json fails `python -m tools.status.snapshot --check` in CI, and both files are where the
    research branch adds its own rows, so an edit here would hand the owner conflicts in the Step 10 merge.
    Registering the suite is the owner's decision; when he makes it, this case goes with that edit."""
    for rel in ("README.md", "tests/run_all.py"):
        assert "provider_parity" not in (ROOT / rel).read_text(encoding="utf-8"), rel


# --------------------------------------------------------------------------- #
# Collection
# --------------------------------------------------------------------------- #
def _guarded(fn):
    def run():
        with no_network():
            fn()
    run.__name__ = fn.__name__
    run.__doc__ = fn.__doc__
    return run


def tests():
    return [(n, _guarded(v)) for n, v in sorted(globals().items())
            if n.startswith("test_") and callable(v)]


def load_tests(loader, standard_tests, pattern):
    """`python -m unittest tests.provider_parity_acceptance`: the same cases, each under the network guard."""
    suite = unittest.TestSuite()
    for name, fn in tests():
        suite.addTest(unittest.FunctionTestCase(fn, description=name))
    return suite


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    bad = 0
    for name, fn in tests():
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:
            bad += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"{len(tests()) - bad}/{len(tests())} passed")
    raise SystemExit(1 if bad else 0)
