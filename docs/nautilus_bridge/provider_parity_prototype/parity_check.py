"""Provider parity for the two pilot price series and the cash rate: a PROTOTYPE for roadmap item 5-2.

Design and every rule this file follows: docs/nautilus_bridge/PROVIDER_PARITY_DESIGN_DRAFT_2026-11-04.md
(draft, awaiting the owner). Nothing here is approved; every threshold below is a proposal.

What it does
- `compare` lines up the md5-pinned series a pilot reads (A: yf_SPY.csv, yf_BTC-USD.csv or fred_DGS3MO.csv) with
  provider files (B) that the owner fetched on his own machine, and writes two new files into a new folder outside
  every git work tree:
  - `summary.json`: counts, outcomes, decade buckets and calendar dates only. `assert_summary_safe` refuses any
    other number. It is the only output that may leave the owner's machine.
  - `detail.json`: the per-date differences behind every count. It stays with the owner.
- Each provider has one fixed role and convention (PROVIDERS, the design draft's section 3 tables). `--pair` names
  only the provider and its file; every required provider of the series is either compared or declared unavailable
  with a reason (`--unavailable`), and the summary lists both. Any other provider is refused.
- It computes only the kinds COMPUTES names, the kinds the draft 3.9 exception names (design draft appendix A):
  calendar membership; day-by-day differences between two providers' closes, returns or rates, at lags -1, 0 and +1
  for the BTC day boundary, and counts, extremes, percentiles, ranges and per-year sums of those differences; of A
  alone, range and gap checks. No correlation, and no mean, volatility, Sharpe or drawdown of any one series.
- Exit codes: 0 PASS, 1 FAIL, 3 WITHHELD, 2 refused (nothing written), 4 error (any other exception: only its type
  is printed, nothing is written). The last console line is `PARITY <series> <outcome> exit=<n> summary=<path or ->`;
  read the outcome from that line, not from the exit code alone.

What it is not
- Not a tool of record: no fetcher, no network code, no ledger, no registration-table write, no QUANTGEN import.
- Never placed under tools/nautilus/, because spec 2026-10-26 section 6.6 puts tools/nautilus/** inside code_sha256.
  The formal tool goes to tools/provider_parity/ on the separate branch (design draft 8.4 step 1).
- Claude never runs `compare` on a real file. The path guard refuses any path under asset_expansion/cache unless the
  owner passes --owner-run, before the file is opened or hashed.

Provider file format (written by the owner's fetch step): UTF-8, header `date,value`, one ISO date per line, a blank
value for a published blank (DGS3MO on a bond-market holiday).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "provider-parity-summary/1"
DETAIL_SCHEMA = "provider-parity-detail/1"
SERIES = ("spy", "btc", "rf")
ROLES = ("independent", "cross", "vintage", "diagnostic")       # cross: total-return A against a split-only B
CONVENTIONS = ("total", "split", "none", "rate_pct")
# provider -> (role, convention, required), copied from the design draft's section 3 tables. The command line cannot
# choose a role or a convention; a required provider is compared or declared unavailable (design draft 5.5).
PROVIDERS = {
    "spy": {"fmp": ("independent", "total", True), "kis": ("cross", "split", True),
            "yahoo_now": ("vintage", "total", True)},
    "btc": {"coinbase": ("independent", "none", True), "bitstamp": ("independent", "none", False),
            "binance": ("diagnostic", "none", True)},
    "rf": {"treasury": ("independent", "rate_pct", True), "h15": ("independent", "rate_pct", False),
           "fred_now": ("vintage", "rate_pct", True)},
}
UNAVAILABLE_REASONS = ("no_key", "plan_or_access", "fetch_failed", "short_history")
# What each check computes; the 3.9 exception text (design draft appendix A) names exactly these kinds and the
# self-test holds the two together.
COMPUTES = {
    "coverage": "calendar membership",
    "calendar": "calendar membership",
    "blanks": "calendar membership",
    "integrity_a": "range and gap checks of A alone",
    "units": "range and gap checks of A alone",
    "seed": "range and gap checks of A alone",
    "returns_same_convention": "differences between providers: counts, extreme, range",
    "adjustment_convention": "differences between providers: counts, per-year sums",
    "day_boundary": "differences between providers at lags -1, 0 and +1: counts",
    "levels_and_returns": "differences between providers: counts, percentiles, extreme",
    "values": "differences between providers: counts, extreme",
}
EXIT = {"PASS": 0, "FAIL": 1, "WITHHELD": 3}
EXIT_REFUSED, EXIT_ERROR = 2, 4
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")                        # the runner's line filter (tools/nautilus/runner.py:119)

# Proposed, pre-registered thresholds (design draft section 5). The summary prints them next to every outcome.
THRESHOLDS = {
    "spy": {
        "coverage_min": 0.99,          # share of A's sessions inside B's span that B also has
        "edge_uncovered_max": 5,       # A's sessions outside B's span (B starts late or ends early)
        "ret_diff_max": 2e-3,          # largest allowed abs difference of one day's simple return
        "ret_diff_tol": 2e-4,          # a day above this counts as a disagreement day
        "ret_diff_share_max": 0.005,   # disagreement days allowed: max(floor, share x sessions)
        "ret_diff_floor_days": 5,
        "drift_range_max": 5e-3,       # range of log(P_A / P_B) over the window
        "jump_abs_max": 0.25,          # one-day abs simple return above this is a split-shaped error
        "ex_gap_min": 5e-4,            # cross pair: a day whose return gap exceeds this is an ex-dividend candidate
        "ex_gap_max": 2e-2,            # a gap above this is too large for a quarterly SPY dividend
        "ex_days_per_year": 4,         # full calendar years only; 3 or 5 is WARN, anything else FAIL
        "yield_band": [0.005, 0.04],   # per full year, the summed gaps; reported as one boolean only
    },
    "btc": {
        "coverage_min": 0.95,          # inside B's span
        "edge_uncovered_max": 471,     # A's days 2014-09-17..2015-12-31: B may start as late as 2016-01-01
        "late_from": "2017-01-01",     # level bands differ before and after this date
        "level_p50_max": 0.003,        # abs log(P_A / P_B), late segment
        "level_p99_max": 0.015,
        "level_max": 0.05,
        "early_level_p99_max": 0.03,   # early segment: WARN only
        "early_level_max": 0.10,
        "missing_days_warn_max": 5,    # missing UTC days in A: 0 PASS, 1..5 WARN, more FAIL
        "jump_log_abs_max": 0.7,
        "ret_diff_big": 0.02,          # a day whose log-return difference exceeds this is a disagreement day;
                                       # also the day_boundary tolerance at each lag
        "ret_diff_share_max": 0.005,
    },
    "rf": {
        "coverage_min": 0.99,          # share of A's published values inside B's span whose date B also has
        "edge_uncovered_max": 5,
        "value_tol_pct": 0.005,        # DGS3MO is published in percent with 2 decimals
        "range_pct": [-1.0, 20.0],     # data/macro/series_registry.yaml:69 (US_TREASURY range)
        "unit_max_at_least_pct": 1.0,  # the window maximum must be at least this, else the unit is not percent
        "seed_lookback_days": 31,
    },
}
_BUCKET_EDGES = (1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1)
DATE_KEYS = {"start", "end", "first_date", "last_date", "only_a", "only_b", "missing_a", "blank_a_value_b",
             "value_a_absent_b", "created_utc"}
INT_KEYS = {"lag"}
LIST_CAP = 100


class Refused(Exception):
    """Exit 2: an input the tool will not read, or a place it will not write. Nothing is written."""


@dataclass(frozen=True)
class Series:
    dates: tuple[str, ...]
    values: np.ndarray
    n_dropped_blank: int = 0
    n_dropped_nonpositive: int = 0


@dataclass
class Check:
    id: str
    kind: str                       # "hard" or "warn"
    outcome: str                    # PASS, FAIL, WARN or WITHHELD
    summary: dict = field(default_factory=dict)
    detail: dict = field(default_factory=dict)

    def public(self) -> dict:
        return {"id": self.id, "kind": self.kind, "outcome": self.outcome, **self.summary}


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def guard_path(path: Path, owner_run: bool) -> None:
    """Refuse a pinned cache path before it is opened or hashed, unless the owner says this is his machine."""
    parts = [p.lower() for p in Path(path).parts]
    pinned = any(parts[i:i + 2] == ["asset_expansion", "cache"] for i in range(len(parts) - 1))
    if pinned and not owner_run:
        raise Refused(f"{path}: a pinned cache file is read only on the owner's machine (--owner-run)")


def inside_git_worktree(path: Path) -> bool:
    p = Path(path).resolve()
    return any((q / ".git").exists() for q in (p, *p.parents))


def _window_frame(data: bytes, start: str, end: str) -> pd.Series:
    """Keep the header and the lines whose leading date text lies in [start, end], before any value is parsed
    (spec 2026-10-26 5.3.2 step 5), then read as the study reads (first column as index, first value column)."""
    lines = data.decode("utf-8").splitlines(keepends=True)
    if not lines:
        raise Refused("empty file")
    kept = "".join([lines[0]] + [x for x in lines[1:] if _DATE.fullmatch(x[:10]) and start <= x[:10] <= end])
    s = pd.read_csv(io.StringIO(kept), index_col=0, parse_dates=True).iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return pd.to_numeric(s, errors="raise").astype(float)


def _to_series(s: pd.Series, keep_blanks: bool) -> Series:
    n_blank = int(s.isna().sum())
    if not keep_blanks:
        s = s.dropna()
    n_nonpos = int((s <= 0).sum()) if not keep_blanks else 0
    if not keep_blanks:
        s = s[s > 0]
    if not (s.index.is_monotonic_increasing and s.index.is_unique):
        raise Refused("dates are not strictly increasing and unique")
    return Series(tuple(d.strftime("%Y-%m-%d") for d in s.index), s.to_numpy(dtype=float),
                  0 if keep_blanks else n_blank, n_nonpos)


def read_pinned(path: Path, *, md5: str, start: str, end: str, owner_run: bool, keep_blanks: bool = False) -> Series:
    guard_path(path, owner_run)
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Refused(f"{path}: cannot be read: {exc}") from exc
    found = hashlib.md5(data).hexdigest()
    if found != md5:
        raise Refused(f"{path}: md5 {found} differs from the pinned {md5}")
    try:
        return _to_series(_window_frame(data, start, end), keep_blanks)
    except (UnicodeDecodeError, ValueError, TypeError, IndexError, KeyError) as exc:
        # the exception's own text can quote a cell of the file, so only its type is printed
        raise Refused(f"{path}: cannot be read as the study reads it ({type(exc).__name__})") from None


def read_provider(path: Path, *, start: str, end: str, owner_run: bool, keep_blanks: bool = False) -> tuple[Series, str]:
    guard_path(path, owner_run)
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Refused(f"{path}: cannot be read: {exc}") from exc
    if not data.decode("utf-8", errors="replace").startswith("date,value"):
        raise Refused(f"{path}: the header must be `date,value`")
    try:
        return _to_series(_window_frame(data, start, end), keep_blanks), hashlib.sha256(data).hexdigest()
    except (UnicodeDecodeError, ValueError, TypeError, IndexError, KeyError) as exc:
        raise Refused(f"{path}: cannot be read ({type(exc).__name__})") from None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def bucket(x: float | None) -> str:
    """A decade label in place of a magnitude, so no exact difference leaves the owner's machine."""
    if x is None or not math.isfinite(x):
        return "n/a"
    x = abs(float(x))
    for edge in _BUCKET_EDGES:
        if x <= edge:
            return f"<={edge:.0e}"
    return f">{_BUCKET_EDGES[-1]:.0e}"


def _cap(dates: list[str]) -> list[str]:
    return sorted(dates)[:LIST_CAP]


def _common(a: Series, b: Series) -> tuple[list[str], np.ndarray, np.ndarray]:
    ib = {d: i for i, d in enumerate(b.dates)}
    keep = [(d, i) for i, d in enumerate(a.dates) if d in ib]
    days = [d for d, _ in keep]
    return days, a.values[[i for _, i in keep]], b.values[[ib[d] for d, _ in keep]]


def _overlap(a: Series, b: Series) -> tuple[str, str] | None:
    if not a.dates or not b.dates:
        return None
    lo, hi = max(a.dates[0], b.dates[0]), min(a.dates[-1], b.dates[-1])
    return (lo, hi) if lo <= hi else None


def _calendar_days(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(days=k)).isoformat() for k in range((d1 - d0).days + 1)]


def _demote(check: Check, role: str) -> Check:
    """A vintage or diagnostic pair never fails a series: its FAIL is reported as WARN."""
    if role in ("vintage", "diagnostic"):
        check.kind = "warn"
        if check.outcome == "FAIL":
            check.outcome = "WARN"
    return check


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
def _base_dates(series: str, a: Series) -> list[str]:
    """A's dates that coverage counts: every date, or for the cash rate every date with a published value."""
    return [d for d, v in zip(a.dates, a.values) if math.isfinite(v)] if series == "rf" else list(a.dates)


def check_coverage(series: str, a: Series, b: Series) -> Check:
    """Share of A's dates inside B's span that B also has, and, as its own count with its own cap, A's dates outside
    B's span (a provider that starts late or ends early; design draft 5.1 and D-5)."""
    t = THRESHOLDS[series]
    days, _, _ = _common(a, b)
    base = _base_dates(series, a)
    inside = [d for d in base if b.dates and b.dates[0] <= d <= b.dates[-1]]
    n_outside = len(base) - len(inside)
    in_b = set(b.dates)
    share = sum(1 for d in inside if d in in_b) / len(inside) if inside else 0.0
    ok = bool(inside) and share >= t["coverage_min"] and n_outside <= t["edge_uncovered_max"]
    return Check("coverage", "hard", "PASS" if ok else "WITHHELD",
                 {"n_a": len(a.dates), "n_b": len(b.dates), "n_common": len(days), "n_a_outside_b_span": n_outside,
                  "coverage_ok": ok,
                  "first_date": b.dates[0] if b.dates else None, "last_date": b.dates[-1] if b.dates else None},
                 {"share": share})


def check_calendar(series: str, a: Series, b: Series) -> Check:
    """Dates of A and B inside their overlap. Calendar dates are public facts and may be reported."""
    ov = _overlap(a, b)
    if ov is None:
        return Check("calendar", "hard", "WITHHELD", {"n_only_a": 0, "n_only_b": 0})
    sa = {d for d in a.dates if ov[0] <= d <= ov[1]}
    sb = {d for d in b.dates if ov[0] <= d <= ov[1]}
    only_a, only_b = sorted(sa - sb), sorted(sb - sa)
    summary = {"n_only_a": len(only_a), "n_only_b": len(only_b), "only_a": _cap(only_a), "only_b": _cap(only_b),
               "truncated": len(only_a) > LIST_CAP or len(only_b) > LIST_CAP}
    if series == "spy":
        weekend = [d for d in a.dates if date.fromisoformat(d).weekday() >= 5]
        summary["n_weekend_a"] = len(weekend)
        outcome = "FAIL" if (only_a or only_b or weekend) else "PASS"
    else:
        outcome = "WARN" if (only_a or only_b) else "PASS"
    return Check("calendar", "hard", outcome, summary)


def check_spy_integrity(a: Series) -> Check:
    t = THRESHOLDS["spy"]
    r = a.values[1:] / a.values[:-1] - 1.0
    n_jump = int(np.sum(np.abs(r) > t["jump_abs_max"]))
    jumps = [a.dates[i + 1] for i in np.flatnonzero(np.abs(r) > t["jump_abs_max"])]
    ok = n_jump == 0 and a.n_dropped_nonpositive == 0
    return Check("integrity_a", "hard", "PASS" if ok else "FAIL",
                 {"n_rows": len(a.dates), "n_dropped_blank": a.n_dropped_blank,
                  "n_dropped_nonpositive": a.n_dropped_nonpositive, "no_split_shaped_jump": n_jump == 0},
                 {"jump_dates": jumps})


def check_spy_same_convention(a: Series, b: Series) -> Check:
    t = THRESHOLDS["spy"]
    days, pa, pb = _common(a, b)
    if len(days) < 2:
        return Check("returns_same_convention", "hard", "WITHHELD", {})
    d = (pa[1:] / pa[:-1] - 1.0) - (pb[1:] / pb[:-1] - 1.0)
    over = np.abs(d) > t["ret_diff_tol"]
    allowed = max(t["ret_diff_floor_days"], int(t["ret_diff_share_max"] * len(d)))
    log_ratio = np.log(pa / pb)
    drift = float(log_ratio.max() - log_ratio.min())
    max_abs = float(np.max(np.abs(d)))
    ok = max_abs <= t["ret_diff_max"] and int(over.sum()) <= allowed and drift <= t["drift_range_max"]
    rank = np.argsort(-np.abs(d))[:LIST_CAP]
    return Check("returns_same_convention", "hard", "PASS" if ok else "FAIL",
                 {"n_days": int(len(d)), "n_over_tol": int(over.sum()), "n_allowed": allowed,
                  "max_abs_bucket": bucket(max_abs), "drift_range_bucket": bucket(drift),
                  "max_ok": max_abs <= t["ret_diff_max"], "drift_ok": drift <= t["drift_range_max"]},
                 {"worst": [[days[i + 1], float(d[i])] for i in rank], "drift_range": drift, "max_abs": max_abs})


def check_spy_cross_convention(a: Series, b: Series) -> Check:
    """A total-return A against a split-only B: the return gap should sit on four ex-dividend days a year, each
    positive and small, and be about zero elsewhere. Only counts and one boolean leave: the yearly gap sum is close
    to the dividend yield, which with public dividend amounts would give the price level."""
    t = THRESHOLDS["spy"]
    days, pa, pb = _common(a, b)
    if len(days) < 2:
        return Check("adjustment_convention", "hard", "WITHHELD", {})
    g = (pa[1:] / pa[:-1] - 1.0) - (pb[1:] / pb[:-1] - 1.0)
    gd = days[1:]
    ex = g > t["ex_gap_min"]
    neg = g < -t["ex_gap_min"]
    too_big = g > t["ex_gap_max"]
    # a full year has a compared day on or before 7 January and on or after 24 December
    full = [y for y in range(int(gd[0][:4]), int(gd[-1][:4]) + 1)
            if any(d[:4] == str(y) and d[5:] <= "01-07" for d in gd) and any(d[:4] == str(y) and d[5:] >= "12-24" for d in gd)]
    per_year = {y: int(sum(1 for i, d in enumerate(gd) if ex[i] and int(d[:4]) == y)) for y in full}
    sums = {y: float(sum(g[i] for i, d in enumerate(gd) if ex[i] and int(d[:4]) == y)) for y in full}
    want = t["ex_days_per_year"]
    n_ok = sum(1 for y in full if per_year[y] == want)
    n_warn = sum(1 for y in full if abs(per_year[y] - want) == 1)
    n_fail = len(full) - n_ok - n_warn
    lo, hi = t["yield_band"]
    band_ok = all(lo <= sums[y] <= hi for y in full)
    allowed = max(t["ret_diff_floor_days"], int(t["ret_diff_share_max"] * len(g)))
    if not full:
        outcome = "WITHHELD"
    elif n_fail or int(too_big.sum()) or int(neg.sum()) > allowed or not band_ok:
        outcome = "FAIL"
    else:
        outcome = "WARN" if n_warn else "PASS"
    return Check("adjustment_convention", "hard", outcome,
                 {"n_full_years": len(full), "n_years_expected_ex_days": n_ok, "n_years_off_by_one": n_warn,
                  "n_years_off_more": n_fail, "n_negative_gap_days": int(neg.sum()), "n_allowed": allowed,
                  "n_too_large_gap_days": int(too_big.sum()), "yield_band_ok": band_ok},
                 {"ex_days": [gd[i] for i in np.flatnonzero(ex)], "per_year": per_year, "gap_sum_per_year": sums,
                  "negative": [[gd[i], float(g[i])] for i in np.flatnonzero(neg)]})


def check_btc_integrity(a: Series) -> Check:
    t = THRESHOLDS["btc"]
    missing = sorted(set(_calendar_days(a.dates[0], a.dates[-1])) - set(a.dates)) if a.dates else []
    lr = np.diff(np.log(a.values))
    n_jump = int(np.sum(np.abs(lr) > t["jump_log_abs_max"]))
    if n_jump or len(missing) > t["missing_days_warn_max"] or a.n_dropped_nonpositive:
        outcome = "FAIL"
    else:
        outcome = "WARN" if missing else "PASS"
    return Check("integrity_a", "hard", outcome,
                 {"n_rows": len(a.dates), "n_dropped_blank": a.n_dropped_blank,
                  "n_dropped_nonpositive": a.n_dropped_nonpositive, "n_missing_days_a": len(missing),
                  "missing_a": _cap(missing), "no_implausible_jump": n_jump == 0})


def _daily_log_returns(s: Series, days: list[str]) -> np.ndarray:
    m = dict(zip(s.dates, s.values))
    p = np.array([m.get(d, np.nan) for d in days], dtype=float)
    return np.diff(np.log(p))


def check_btc_day_boundary(a: Series, b: Series) -> Check:
    """Which shift of B's labels lines its daily returns up with A's: 0 means both label a UTC day the same way
    (the bridge reads a BTC date D as the day that closes at 00:00 UTC on D+1, tools/nautilus/runner.py:629-634).
    Built from day-by-day differences only: for each shift k, the days on which |r_A(t) - r_B(t+k)| exceeds
    ret_diff_big. k = 0 must have strictly the fewest. No correlation and no statistic of one series alone."""
    t = THRESHOLDS["btc"]
    ov = _overlap(a, b)
    if ov is None:
        return Check("day_boundary", "hard", "WITHHELD", {})
    days = _calendar_days(*ov)
    ra, rb = _daily_log_returns(a, days), _daily_log_returns(b, days)
    n_over, n_used = {}, {}
    for k in (-1, 0, 1):
        x, y = (ra[:len(ra) - k], rb[k:]) if k >= 0 else (ra[-k:], rb[:len(rb) + k])
        ok = np.isfinite(x) & np.isfinite(y)
        n_used[k] = int(ok.sum())
        n_over[k] = int(np.sum(np.abs(x[ok] - y[ok]) > t["ret_diff_big"]))
    if min(n_used.values()) < 3:
        return Check("day_boundary", "hard", "WITHHELD", {})
    best = min(n_over, key=lambda k: (n_over[k], k != 0))         # the fewest; a tie keeps 0
    strict = n_over[0] < min(n_over[-1], n_over[1])
    return Check("day_boundary", "hard", "PASS" if best == 0 and strict else "FAIL",
                 {"lag": int(best), "lag0_strictly_fewest": bool(strict)},
                 {"n_over_by_lag": n_over, "n_compared_by_lag": n_used})


def check_btc_levels(a: Series, b: Series) -> Check:
    t = THRESHOLDS["btc"]
    days, pa, pb = _common(a, b)
    if len(days) < 2:
        return Check("levels_and_returns", "hard", "WITHHELD", {})
    lv = np.abs(np.log(pa / pb))
    late = np.array([d >= t["late_from"] for d in days])
    out = {}
    fail = warn = False
    for name, mask in (("late", late), ("early", ~late)):
        if not mask.any():
            out[name] = {"n_days": 0}
            continue
        x = lv[mask]
        p50, p99, mx = float(np.percentile(x, 50)), float(np.percentile(x, 99)), float(x.max())
        if name == "late":
            ok = p50 <= t["level_p50_max"] and p99 <= t["level_p99_max"] and mx <= t["level_max"]
            fail |= not ok
        else:
            ok = p99 <= t["early_level_p99_max"] and mx <= t["early_level_max"]
            warn |= not ok
        out[name] = {"n_days": int(mask.sum()), "p50_bucket": bucket(p50), "p99_bucket": bucket(p99),
                     "max_bucket": bucket(mx), "within_band": bool(ok)}
    lr = np.diff(np.log(pa)) - np.diff(np.log(pb))
    n_big = int(np.sum(np.abs(lr) > t["ret_diff_big"]))
    allowed = int(t["ret_diff_share_max"] * len(lr))
    fail |= n_big > allowed
    outcome = "FAIL" if fail else ("WARN" if warn else "PASS")
    rank = np.argsort(-lv)[:LIST_CAP]
    return Check("levels_and_returns", "hard", outcome,
                 {**out, "n_big_return_diff_days": n_big, "n_allowed": allowed},
                 {"worst_level": [[days[i], float(lv[i])] for i in rank]})


def check_rf(a: Series, b: Series, role: str) -> list[Check]:
    """A is the pinned DGS3MO with its published blanks kept; B is another channel of the same series."""
    t = THRESHOLDS["rf"]
    av = dict(zip(a.dates, a.values))
    bv = dict(zip(b.dates, b.values))
    finite_a = a.values[np.isfinite(a.values)]
    lo, hi = t["range_pct"]
    units_ok = bool(finite_a.size) and bool(np.all((finite_a >= lo) & (finite_a <= hi))) and \
        float(finite_a.max()) >= t["unit_max_at_least_pct"]
    both = [d for d in a.dates if d in bv and math.isfinite(av[d]) and math.isfinite(bv[d])]
    diff = [abs(av[d] - bv[d]) for d in both]
    n_off = sum(1 for x in diff if x >= t["value_tol_pct"])
    blank_a_value_b = [d for d in a.dates if not math.isfinite(av[d]) and d in bv and math.isfinite(bv[d])]
    weekday = [d for d in a.dates if date.fromisoformat(d).weekday() < 5]
    value_a_absent_b = [d for d in weekday if math.isfinite(av[d]) and d not in bv and
                        b.dates and b.dates[0] <= d <= b.dates[-1]]
    checks = [
        Check("units", "hard", "PASS" if units_ok else "FAIL", {"percent_units_ok": units_ok}),
        Check("values", "hard", "FAIL" if n_off else "PASS",
              {"n_common_values": len(both), "n_off_by_tol": n_off, "max_abs_bucket": bucket(max(diff) if diff else None)},
              {"off": [[d, av[d], bv[d]] for d in both if abs(av[d] - bv[d]) >= t["value_tol_pct"]]}),
        Check("blanks", "warn", "WARN" if (blank_a_value_b or value_a_absent_b) else "PASS",
              {"n_blank_a_value_b": len(blank_a_value_b), "blank_a_value_b": _cap(blank_a_value_b),
               "n_value_a_absent_b": len(value_a_absent_b), "value_a_absent_b": _cap(value_a_absent_b)}),
    ]
    return [_demote(c, role) for c in checks]


# --------------------------------------------------------------------------- #
# Summary safety
# --------------------------------------------------------------------------- #
_DECIMAL = re.compile(r"\d\.\d")
_BUCKET = re.compile(r"^(<=1e-0\d|>1e-01|n/a)$")


def assert_summary_safe(obj, key: str = "", under_thresholds: bool = False) -> None:
    """Every number in the summary is a count, a lag, a boolean or a threshold; every date sits under a date key;
    no string carries a decimal number. Anything else raises before the file is written."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_summary_safe(v, k, under_thresholds or k == "thresholds")
        return
    if isinstance(obj, list):
        for v in obj:
            assert_summary_safe(v, key, under_thresholds)
        return
    if obj is None or isinstance(obj, bool) or under_thresholds:
        return
    if isinstance(obj, float):
        raise ValueError(f"float under {key!r} in the summary")
    if isinstance(obj, int):
        if not (key.startswith("n_") or key in INT_KEYS):
            raise ValueError(f"integer under {key!r} in the summary")
        return
    if isinstance(obj, str):
        if _BUCKET.match(obj):
            return
        if _DECIMAL.search(obj):
            raise ValueError(f"decimal number in the string under {key!r}")
        if _DATE.search(obj) and key not in DATE_KEYS:
            raise ValueError(f"date under {key!r}, which is not a date key")
        return
    raise ValueError(f"{type(obj).__name__} under {key!r} in the summary")


# --------------------------------------------------------------------------- #
# Compare
# --------------------------------------------------------------------------- #
PAIR_CHECKS = {
    "spy": {"total": (check_coverage, check_calendar, check_spy_same_convention),
            "split": (check_coverage, check_calendar, check_spy_cross_convention)},
    "btc": {"none": (check_coverage, check_calendar, check_btc_day_boundary, check_btc_levels)},
}


def compare(series: str, a: Series, pairs: list[tuple[str, str, str, Series, str]],
            unavailable: list[tuple[str, str]] = ()) -> tuple[dict, dict, str]:
    """pairs: (role, convention, provider, series, file sha256); unavailable: (provider, reason) for each provider the
    owner could not fetch. Returns (summary, detail, outcome)."""
    integrity = []
    if series == "spy":
        integrity.append(check_spy_integrity(a))
    elif series == "btc":
        integrity.append(check_btc_integrity(a))
    out_pairs, det_pairs = [], []
    for role, conv, provider, b, sha in pairs:
        checks: list[Check] = []
        cov = check_coverage(series, a, b)
        if series == "rf":
            checks.append(_demote(cov, role))
            if cov.outcome == "PASS":
                checks += check_rf(a, b, role)
        elif conv not in PAIR_CHECKS[series]:
            raise Refused(f"{series}: convention {conv!r} is not compared")
        else:
            checks.append(_demote(cov, role))
            if cov.outcome == "PASS":
                checks += [_demote(fn(series, a, b) if fn is check_calendar else fn(a, b), role)
                           for fn in PAIR_CHECKS[series][conv][1:]]
        hard = [c for c in checks if c.kind == "hard"]
        if any(c.outcome == "FAIL" for c in hard):
            p_out = "FAIL"
        elif cov.outcome != "PASS" or any(c.outcome == "WITHHELD" for c in hard):
            p_out = "WITHHELD"
        else:
            p_out = "WARN" if any(c.outcome == "WARN" for c in checks) else "PASS"
        out_pairs.append({"provider": provider, "role": role, "convention": conv, "file_sha256": sha,
                          "outcome": p_out, "checks": [c.public() for c in checks]})
        det_pairs.append({"provider": provider, "role": role, "checks": {c.id: c.detail for c in checks}})
    evidence = [p for p in out_pairs if p["role"] in ("independent", "cross")]
    withheld = [f"{provider} not compared: {reason}" for provider, reason in unavailable]
    if any(c.outcome == "FAIL" for c in integrity) or any(p["outcome"] == "FAIL" for p in evidence):
        outcome = "FAIL"
    elif not any(p["outcome"] in ("PASS", "WARN") for p in evidence):
        outcome = "WITHHELD"
        withheld.append("no independent or cross pair was evaluated in full")
    else:
        outcome = "PASS"
    # A's dates that no fully evaluated independent or cross pair spans: checked by A's own integrity check only
    spans = [(b.dates[0], b.dates[-1]) for (role, _, _, b, _), p in zip(pairs, out_pairs)
             if role in ("independent", "cross") and p["outcome"] in ("PASS", "WARN") and b.dates]
    n_uncovered = sum(1 for d in _base_dates(series, a) if not any(lo <= d <= hi for lo, hi in spans))
    summary = {"integrity": [c.public() for c in integrity], "pairs": out_pairs, "outcome": outcome,
               "n_a_outside_evidence_spans": n_uncovered, "withheld_reasons": withheld}
    detail = {"integrity": {c.id: c.detail for c in integrity}, "pairs": det_pairs}
    return summary, detail, outcome


def _json_default(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    raise TypeError(type(x).__name__)


def _accounted_pairs(series: str, pair_args: list[list[str]], unavailable_args: list[list[str]]):
    """The command line names providers only; their role and convention come from PROVIDERS. Every required provider
    is compared or declared unavailable with a reason from UNAVAILABLE_REASONS (design draft 5.5)."""
    table = PROVIDERS[series]
    named = [p for p, _ in pair_args] + [p for p, _ in unavailable_args]
    for p in named:
        if p not in table:
            raise Refused(f"{series}: provider {p!r} is not one of {tuple(table)}")
    if len(named) != len(set(named)):
        raise Refused(f"{series}: a provider is named twice")
    for _, reason in unavailable_args:
        if reason not in UNAVAILABLE_REASONS:
            raise Refused(f"{series}: reason {reason!r} is not one of {UNAVAILABLE_REASONS}")
    missing = [p for p, (_, _, required) in table.items() if required and p not in named]
    if missing:
        raise Refused(f"{series}: required provider(s) {missing} neither compared nor declared unavailable")
    return [(table[p][0], table[p][1], p, Path(path)) for p, path in pair_args], \
        [(p, reason) for p, reason in unavailable_args]


def run(argv: list[str] | None = None, *, now: datetime | None = None) -> int:
    ap = argparse.ArgumentParser(prog="parity_check.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--series", choices=SERIES, required=True)
    c.add_argument("--a", type=Path, required=True, help="the pinned file the pilot reads")
    c.add_argument("--a-md5", required=True, help="the table's prices_md5 or rf_md5")
    c.add_argument("--start", required=True)
    c.add_argument("--end", required=True)
    c.add_argument("--pair", nargs=2, action="append", default=[], metavar=("PROVIDER", "FILE"))
    c.add_argument("--unavailable", nargs=2, action="append", default=[], metavar=("PROVIDER", "REASON"))
    c.add_argument("--out", type=Path, required=True, help="a new folder outside every git work tree")
    c.add_argument("--owner-run", action="store_true", help="only on the owner's machine")
    args = ap.parse_args(argv)
    try:
        if args.out.exists() or inside_git_worktree(args.out.parent if not args.out.exists() else args.out):
            raise Refused(f"{args.out}: must be a new folder outside every git work tree")
        pair_specs, unavailable = _accounted_pairs(args.series, args.pair, args.unavailable)
        rf = args.series == "rf"
        start = args.start
        if rf:
            start = (date.fromisoformat(args.start) - timedelta(days=THRESHOLDS["rf"]["seed_lookback_days"])).isoformat()
        a = read_pinned(args.a, md5=args.a_md5, start=start, end=args.end, owner_run=args.owner_run, keep_blanks=rf)
        pairs = []
        for role, conv, provider, path in pair_specs:
            b, sha = read_provider(path, start=start, end=args.end, owner_run=args.owner_run, keep_blanks=rf)
            pairs.append((role, conv, provider, b, sha))
        body, detail, outcome = compare(args.series, a, pairs, unavailable)
        if rf:
            finite = [d for d, v in zip(a.dates, a.values) if math.isfinite(v)]
            body["integrity"].append({"id": "seed", "kind": "hard",
                                      "outcome": "PASS" if finite and finite[0] <= args.start else "FAIL",
                                      "seed_before_start": bool(finite and finite[0] <= args.start)})
            if body["integrity"][-1]["outcome"] == "FAIL":
                body["outcome"] = outcome = "FAIL"
        stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
        summary = {"schema": SCHEMA,
                   "tool": {"name": Path(__file__).name, "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                            "status": "prototype"},
                   "run_id": f"PP-{stamp}-{args.series}", "created_utc": stamp, "series": args.series,
                   "window": {"start": args.start, "end": args.end},
                   "pinned": {"file": args.a.name, "md5": args.a_md5, "md5_ok": True},
                   "providers": {p: {"role": r, "convention": cv, "required": req}
                                 for p, (r, cv, req) in PROVIDERS[args.series].items()},
                   "thresholds": THRESHOLDS[args.series], **body,
                   "never_in_this_file": "prices, returns, rates, per-date differences or exact magnitudes"}
        assert_summary_safe(summary)
        # both files are serialised before the folder exists, so a failure up to here leaves nothing behind
        s_text = json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False, default=_json_default) + "\n"
        d_text = json.dumps({"schema": DETAIL_SCHEMA, "run_id": summary["run_id"], **detail}, indent=1,
                            sort_keys=True, default=_json_default) + "\n"
        args.out.mkdir(parents=True, exist_ok=False)
        for name, text in (("summary.json", s_text), ("detail.json", d_text)):
            with open(args.out / name, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        print(f"PARITY {args.series} REFUSED exit={EXIT_REFUSED} summary=-")
        return EXIT_REFUSED
    except Exception as exc:                  # never FAIL by accident; the text can quote a value, so only the type
        print(f"ERROR: {type(exc).__name__}")
        print(f"PARITY {args.series} ERROR exit={EXIT_ERROR} summary=-")
        return EXIT_ERROR
    code = EXIT[outcome]
    print(f"PARITY {args.series} {outcome} exit={code} summary={args.out / 'summary.json'}")
    return code


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(run())
