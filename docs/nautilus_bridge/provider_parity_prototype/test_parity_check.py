"""Synthetic self-test for parity_check.py (roadmap 5-2 prototype). Synthetic data only: no real price, no network.

Run: python -I -B docs/nautilus_bridge/provider_parity_prototype/test_parity_check.py
Every file goes into a fresh folder under the system temp dir; nothing in the repository is read or written except
parity_check.py itself. The last line is `SELFTEST PASS <n> cases` or the first failing case.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("parity_check_proto", HERE / "parity_check.py")
pc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = pc                                  # dataclasses look the module up while it loads
_spec.loader.exec_module(pc)
NOW = datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc)
ROOT = Path(tempfile.mkdtemp(prefix="pp_selftest_"))
assert not pc.inside_git_worktree(ROOT), f"{ROOT} sits inside a git work tree; set TMPDIR elsewhere"
_n = [0]


# --------------------------------------------------------------------------- #
# Synthetic series
# --------------------------------------------------------------------------- #
def weekdays(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(k)).isoformat() for k in range((d1 - d0).days + 1) if (d0 + timedelta(k)).weekday() < 5]


def alldays(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(k)).isoformat() for k in range((d1 - d0).days + 1)]


def spy_like(seed: int = 7, lo: str = "2009-06-01", hi: str = "2016-12-30"):
    """Weekday sessions, a 2-decimal raw close with four dividends a year, and the backward total-return
    adjustment a Yahoo-style adjusted close applies (factor 1 - D / P_prev before each ex-date)."""
    rng = np.random.default_rng(seed)
    days = weekdays(lo, hi)
    ex = set()
    for y in range(int(lo[:4]), int(hi[:4]) + 1):
        for m in (3, 6, 9, 12):
            later = [d for d in days if d >= f"{y}-{m:02d}-15"]
            if later:
                ex.add(later[0])
    raw = np.empty(len(days))
    div = np.zeros(len(days))
    p = 100.0
    for i, d in enumerate(days):
        if i:
            p = p * (1.0 + rng.normal(0.0003, 0.011))
            if d in ex:
                div[i] = round(0.0045 * raw[i - 1], 2)
                p -= div[i]
        raw[i] = round(p, 2)
    factor = np.ones(len(days))
    f = 1.0
    for i in range(len(days) - 1, -1, -1):
        factor[i] = f
        if div[i] > 0:
            f *= 1.0 - div[i] / raw[i - 1]
    adj = raw * factor
    return days, raw, adj, div


def btc_like(seed: int = 11, lo: str = "2015-01-01", hi: str = "2019-12-31"):
    rng = np.random.default_rng(seed)
    days = alldays(lo, hi)
    p = 300.0 * np.exp(np.cumsum(rng.normal(0.001, 0.04, len(days))))
    venue = p * np.exp(rng.normal(0.0, 0.001, len(days)))
    return days, p, venue


def rf_like(seed: int = 5, lo: str = "2009-04-01", hi: str = "2016-12-30"):
    rng = np.random.default_rng(seed)
    days = weekdays(lo, hi)
    level = np.clip(np.cumsum(rng.normal(0.0, 0.03, len(days))) + 1.2, 0.0, 6.0)
    vals = np.round(level, 2)
    holidays = set(rng.choice(len(days), size=60, replace=False).tolist())
    return days, vals, holidays


# --------------------------------------------------------------------------- #
# Files and runs
# --------------------------------------------------------------------------- #
def write(name: str, text: str) -> tuple[Path, str]:
    path = ROOT / "in" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    path.write_bytes(data)
    return path, hashlib.md5(data).hexdigest()


def pinned_text(header: str, days, vals) -> str:
    """The shape pandas writes for the study's cache: a header, then date,value with repr floats; NaN blank."""
    rows = [header] + [f"{d},{'' if not np.isfinite(v) else repr(float(v))}" for d, v in zip(days, vals)]
    return "\n".join(rows) + "\n"


def provider_text(days, vals, decimals: int | None = None) -> str:
    fmt = (lambda v: f"{v:.{decimals}f}") if decimals is not None else (lambda v: repr(float(v)))
    return "date,value\n" + "".join(f"{d},{fmt(v)}\n" for d, v in zip(days, vals))


def run(argv: list[str]) -> tuple[int, str, dict | None, Path]:
    _n[0] += 1
    out = ROOT / "out" / f"run{_n[0]:02d}"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pc.run(["compare", *argv, "--out", str(out)], now=NOW)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8")) if (out / "summary.json").exists() else None
    return code, buf.getvalue(), summary, out


def account(series: str, given: list[str]) -> list[str]:
    """`--unavailable <p> fetch_failed` for each required provider a case does not compare, so a case states only the
    pairs it is about (the refusal itself has its own case)."""
    out = []
    for p, (_, _, required) in pc.PROVIDERS[series].items():
        if required and p not in given:
            out += ["--unavailable", p, "fetch_failed"]
    return out


def check_of(summary: dict, provider: str, cid: str) -> dict:
    pair = next(p for p in summary["pairs"] if p["provider"] == provider)
    return next(c for c in pair["checks"] if c["id"] == cid)


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


# --------------------------------------------------------------------------- #
# SPY
# --------------------------------------------------------------------------- #
SPY = spy_like()
SPY_WIN = ("2010-01-04", "2016-12-30")


def spy_files(days=None, adj=None, raw=None, b_total=None, a_extra: str = ""):
    d0, raw0, adj0, _ = SPY
    days = d0 if days is None else days
    adj = adj0 if adj is None else adj
    raw = raw0 if raw is None else raw
    a_text = pinned_text("Date,yf_SPY", days, adj)
    if a_extra:
        lines = a_text.splitlines(keepends=True)
        a_text = lines[0] + a_extra + "".join(lines[1:])
    a, md5 = write(f"a_spy_{_n[0]}.csv", a_text)
    bt = adj0 * 0.987 if b_total is None else b_total            # a later vintage: one constant factor
    b1, _ = write(f"b_total_{_n[0]}.csv", provider_text(d0, bt, 6))
    b2, _ = write(f"b_split_{_n[0]}.csv", provider_text(d0, raw, 2))
    return a, md5, b1, b2


def spy_args(a, md5, *pairs, unavailable=None):
    args = ["--series", "spy", "--a", str(a), "--a-md5", md5, "--start", SPY_WIN[0], "--end", SPY_WIN[1]]
    for p in pairs:
        args += ["--pair", *p]
    return args + (account("spy", [p[0] for p in pairs]) if unavailable is None else unavailable)


@case
def spy_clean_passes():
    a, md5, b1, b2 = spy_files()
    code, out, s, _ = run(spy_args(a, md5, ("fmp", str(b1)), ("kis", str(b2))))
    assert code == 0 and s["outcome"] == "PASS", out
    adj = check_of(s, "kis", "adjustment_convention")
    assert adj["outcome"] == "PASS" and adj["n_years_off_more"] == 0 and adj["yield_band_ok"] is True, adj
    assert adj["n_full_years"] == 7 and adj["n_years_expected_ex_days"] == 7, adj
    same = check_of(s, "fmp", "returns_same_convention")
    assert same["n_over_tol"] == 0 and same["max_ok"] and same["drift_ok"], same


@case
def spy_price_only_file_treated_as_total_fails():
    d0, raw0, _, _ = SPY
    a, md5, _, _ = spy_files()
    b, _ = write("b_price_as_total.csv", provider_text(d0, raw0, 2))
    code, _, s, _ = run(spy_args(a, md5, ("fmp", str(b))))
    same = check_of(s, "fmp", "returns_same_convention")
    assert code == 1 and same["outcome"] == "FAIL" and same["n_over_tol"] >= 20, same


@case
def spy_missing_session_in_a_fails_with_its_date():
    d0, _, adj0, _ = SPY
    drop = d0.index("2013-05-15")
    days = d0[:drop] + d0[drop + 1:]
    adj = np.delete(adj0, drop)
    a, md5, b1, _ = spy_files(days=days, adj=adj)
    code, _, s, _ = run(spy_args(a, md5, ("fmp", str(b1))))
    cal = check_of(s, "fmp", "calendar")
    assert code == 1 and cal["outcome"] == "FAIL" and cal["only_b"] == ["2013-05-15"] and cal["n_only_a"] == 0, cal


@case
def spy_bad_tick_in_provider_fails():
    d0, _, adj0, _ = SPY
    bt = adj0 * 0.987
    bt[d0.index("2014-02-12")] *= 1.02
    a, md5, b1, _ = spy_files(b_total=bt)
    code, _, s, _ = run(spy_args(a, md5, ("fmp", str(b1))))
    same = check_of(s, "fmp", "returns_same_convention")
    assert code == 1 and same["n_over_tol"] == 2 and same["max_abs_bucket"] == "<=1e-01" and not same["max_ok"], same


@case
def spy_two_missed_dividend_adjustments_in_one_year_fail():
    d0, raw0, _, div0 = SPY
    div = div0.copy()
    for i in [i for i, d in enumerate(d0) if d.startswith("2012") and div[i] > 0][:2]:
        div[i] = 0.0
    factor = np.ones(len(d0))
    f = 1.0
    for i in range(len(d0) - 1, -1, -1):
        factor[i] = f
        if div[i] > 0:
            f *= 1.0 - div[i] / raw0[i - 1]
    a, md5, _, b2 = spy_files(adj=raw0 * factor)
    code, _, s, _ = run(spy_args(a, md5, ("kis", str(b2))))
    adj = check_of(s, "kis", "adjustment_convention")
    assert code == 1 and adj["n_years_off_more"] == 1 and adj["outcome"] == "FAIL", adj


@case
def spy_lines_outside_the_window_are_never_parsed():
    a, md5, b1, _ = spy_files(a_extra="2001-01-02,not_a_number\n")
    code, out, s, _ = run(spy_args(a, md5, ("fmp", str(b1))))
    assert code == 0 and s["outcome"] == "PASS", out


@case
def refusal_message_never_echoes_file_content():
    a, md5, b1, _ = spy_files(a_extra="2013-05-15,123.45x\n")    # a bad cell inside the window
    code, out, s, path = run(spy_args(a, md5, ("fmp", str(b1))))
    assert code == 2 and s is None and "123.45" not in out and "ValueError" in out, out


@case
def spy_without_an_independent_pair_is_withheld():
    a, md5, b1, _ = spy_files()
    code, _, s, _ = run(spy_args(a, md5, ("yahoo_now", str(b1))))
    assert code == 3 and s["outcome"] == "WITHHELD" and s["withheld_reasons"], s


@case
def spy_md5_mismatch_is_refused_and_writes_nothing():
    a, md5, b1, _ = spy_files()
    code, out, s, path = run(spy_args(a, "0" * 32, ("fmp", str(b1))))
    assert code == 2 and s is None and not path.exists() and "REFUSED" in out, out


@case
def pinned_cache_path_is_refused_before_it_is_opened():
    fake = ROOT / "docs" / "asset_expansion" / "cache" / "does_not_exist.csv"
    code, out, s, path = run(spy_args(fake, "0" * 32))
    assert code == 2 and "--owner-run" in out and not path.exists(), out


@case
def out_folder_inside_a_git_work_tree_is_refused():
    repo = ROOT / "fake_repo"
    (repo / ".git").mkdir(parents=True)
    a, md5, b1, _ = spy_files()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pc.run(["compare", *spy_args(a, md5, ("fmp", str(b1))),
                       "--out", str(repo / "pp")], now=NOW)
    assert code == 2 and not (repo / "pp").exists(), buf.getvalue()


@case
def summary_never_carries_a_value_even_on_fail():
    d0, _, adj0, _ = SPY
    adj = adj0.copy()
    adj[d0.index("2015-07-01")] = 4321.123457                    # a planted marker
    a, md5, b1, b2 = spy_files(adj=adj)
    code, _, s, out = run(spy_args(a, md5, ("fmp", str(b1)), ("kis", str(b2))))
    text = (out / "summary.json").read_text(encoding="utf-8")
    assert code == 1 and "4321.1" not in text, "marker leaked"
    body = {k: v for k, v in s.items() if k != "thresholds"}
    assert not re.search(r"\d\.\d", json.dumps(body)), "a decimal number outside the thresholds block"
    for v in list(adj0[:300]) + list(SPY[1][:300]):
        assert f"{v:.2f}" not in json.dumps(body), v
    detail = json.loads((out / "detail.json").read_text(encoding="utf-8"))
    assert detail["integrity"]["integrity_a"]["jump_dates"], "the detail file keeps the dates for the owner"


@case
def summary_validator_refuses_floats_dates_and_stray_integers():
    for bad in ({"pairs": [{"max_abs": 0.0012}]}, {"note": "close 101.25"}, {"worst_day": "2015-07-01"},
                {"price": 4321}):
        try:
            pc.assert_summary_safe(bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
    pc.assert_summary_safe({"thresholds": {"x": 0.5, "late_from": "2017-01-01"}, "n_days": 3, "only_a": ["2015-01-02"],
                            "max_abs_bucket": "<=1e-04", "ok": True})

@case
def providers_take_their_role_from_the_fixed_map():
    a, md5, b1, b2 = spy_files()
    for bad in (["--pair", "coinbase", str(b1)],                                  # not a SPY provider
                ["--pair", "fmp", str(b1)],                                       # kis, yahoo_now unaccounted
                ["--pair", "fmp", str(b1), "--pair", "fmp", str(b1)],             # named twice
                ["--pair", "fmp", str(b1), "--unavailable", "kis", "busy", "--unavailable", "yahoo_now", "no_key"]):
        code, out, s, path = run(spy_args(a, md5, unavailable=[]) + bad)
        assert code == 2 and s is None and not path.exists() and "REFUSED" in out, (bad, out)
    code, out, s, _ = run(spy_args(a, md5, ("fmp", str(b1)), ("kis", str(b2)),
                                   unavailable=["--unavailable", "yahoo_now", "fetch_failed"]))
    assert code == 0 and s["outcome"] == "PASS", out
    assert s["withheld_reasons"] == ["yahoo_now not compared: fetch_failed"], s["withheld_reasons"]
    assert s["providers"]["kis"] == {"role": "cross", "convention": "split", "required": True}, s["providers"]
    assert {p["provider"]: p["role"] for p in s["pairs"]} == {"fmp": "independent", "kis": "cross"}


# --------------------------------------------------------------------------- #
# BTC
# --------------------------------------------------------------------------- #
BTC = btc_like()
BTC_WIN = ("2015-01-01", "2019-12-31")


def btc_run(a_days, a_vals, b_days, b_vals, provider="coinbase"):
    a, md5 = write(f"a_btc_{_n[0]}.csv", pinned_text("Date,yf_BTC-USD", a_days, a_vals))
    b, _ = write(f"b_btc_{_n[0]}.csv", provider_text(b_days, b_vals, 2))
    return run(["--series", "btc", "--a", str(a), "--a-md5", md5, "--start", BTC_WIN[0], "--end", BTC_WIN[1],
                "--pair", provider, str(b), *account("btc", [provider])])


@case
def btc_clean_passes():
    d, p, v = BTC
    code, out, s, _ = btc_run(d, p, d, v)
    db = check_of(s, "coinbase", "day_boundary")
    assert code == 0 and s["outcome"] == "PASS" and db["lag"] == 0 and db["lag0_strictly_fewest"], out


@case
def btc_labels_shifted_by_one_day_fail_the_boundary_check():
    d, p, v = BTC
    code, _, s, _ = btc_run(d, p, d[1:], v[:-1])                # B labels each day by its closing date
    db = check_of(s, "coinbase", "day_boundary")
    assert code == 1 and db["outcome"] == "FAIL" and db["lag"] == 1, db


@case
def btc_seven_missing_days_in_a_fail_two_warn():
    d, p, v = BTC
    rng = np.random.default_rng(3)
    for n, want in ((7, "FAIL"), (2, "WARN")):
        drop = set(rng.choice(np.arange(10, len(d) - 10), size=n, replace=False).tolist())
        keep = [i for i in range(len(d)) if i not in drop]
        code, _, s, _ = btc_run([d[i] for i in keep], p[keep], d, v)
        integ = s["integrity"][0]
        assert integ["outcome"] == want and integ["n_missing_days_a"] == n, integ
        assert len(integ["missing_a"]) == n


@case
def btc_level_dislocations_fail():
    d, p, v = BTC
    v2 = v.copy()
    rng = np.random.default_rng(4)
    late = [i for i, x in enumerate(d) if x >= "2017-01-01"]
    for i in rng.choice(late, size=len(late) // 30, replace=False):
        v2[i] *= 1.03
    code, _, s, _ = btc_run(d, p, d, v2)
    lv = check_of(s, "coinbase", "levels_and_returns")
    assert code == 1 and lv["late"]["within_band"] is False and lv["early"]["within_band"] is True, lv

@case
def btc_late_starting_provider_is_compared_on_its_span():
    d, p, v = BTC
    code, out, s, _ = btc_run(d, p, d[120:], v[120:])            # B starts 120 days after A: within the cap
    cov = check_of(s, "coinbase", "coverage")
    assert code == 0 and s["outcome"] == "PASS" and cov["n_a_outside_b_span"] == 120, out
    assert s["n_a_outside_evidence_spans"] == 120, s
    code, _, s, _ = btc_run(d, p, d[500:], v[500:])               # 500 days late: above the cap of 471
    assert code == 3 and check_of(s, "coinbase", "coverage")["outcome"] == "WITHHELD" and s["outcome"] == "WITHHELD", s


@case
def btc_diagnostic_pair_never_fails_the_series():
    d, p, v = BTC
    code, _, s, _ = btc_run(d, p, d[1:], v[:-1], provider="binance")    # binance is diagnostic in PROVIDERS
    db = check_of(s, "binance", "day_boundary")
    assert code == 3 and db["outcome"] == "WARN" and s["outcome"] == "WITHHELD", s


# --------------------------------------------------------------------------- #
# Cash rate
# --------------------------------------------------------------------------- #
RF = rf_like()
RF_WIN = ("2010-01-04", "2016-12-30")


def rf_run(a_vals, b_days, b_vals, b_decimals=2):
    days, _, hol = RF
    a_text = pinned_text("DATE,DGS3MO", days, [np.nan if i in hol else x for i, x in enumerate(a_vals)])
    a, md5 = write(f"a_rf_{_n[0]}.csv", a_text)
    b, _ = write(f"b_rf_{_n[0]}.csv", provider_text(b_days, b_vals, b_decimals))
    return run(["--series", "rf", "--a", str(a), "--a-md5", md5, "--start", RF_WIN[0], "--end", RF_WIN[1],
                "--pair", "treasury", str(b), *account("rf", ["treasury"])])


def rf_b(vals):
    days, _, hol = RF
    keep = [i for i in range(len(days)) if i not in hol]
    return [days[i] for i in keep], np.asarray(vals)[keep]


@case
def rf_clean_passes():
    _, vals, _ = RF
    code, out, s, _ = rf_run(vals, *rf_b(vals))
    assert code == 0 and s["outcome"] == "PASS", out
    assert check_of(s, "treasury", "units")["percent_units_ok"] is True


@case
def rf_fraction_units_fail():
    _, vals, _ = RF
    code, _, s, _ = rf_run(vals / 100.0, *rf_b(vals / 100.0), b_decimals=4)
    assert code == 1 and check_of(s, "treasury", "units")["outcome"] == "FAIL", s


@case
def rf_one_value_off_by_a_basis_point_fails():
    days, vals, hol = RF
    b_days, b_vals = rf_b(vals)
    b_vals = b_vals.copy()
    b_vals[b_days.index(next(d for d in b_days if d >= "2013-03-01"))] += 0.01
    code, _, s, _ = rf_run(vals, b_days, b_vals)
    v = check_of(s, "treasury", "values")
    assert code == 1 and v["n_off_by_tol"] == 1, v


@case
def rf_blank_in_a_where_b_has_a_value_warns_with_the_date():
    days, vals, hol = RF
    b_days, b_vals = list(days), np.asarray(vals)            # B publishes on every A holiday
    code, _, s, _ = rf_run(vals, b_days, b_vals)
    bl = check_of(s, "treasury", "blanks")
    assert code == 0 and bl["outcome"] == "WARN" and bl["n_blank_a_value_b"] > 0, bl

# --------------------------------------------------------------------------- #
# Whole tool
# --------------------------------------------------------------------------- #
@case
def unexpected_exception_is_error_exit_4_and_writes_nothing():
    a, md5, b1, b2 = spy_files()
    real = pc.assert_summary_safe

    def boom(*_a, **_k):
        raise ValueError("close 4321.12 leaked")                 # an exception whose text quotes a value
    pc.assert_summary_safe = boom
    try:
        code, out, s, path = run(spy_args(a, md5, ("fmp", str(b1)), ("kis", str(b2))))
    finally:
        pc.assert_summary_safe = real
    assert code == 4 and s is None and not path.exists(), out
    assert out.splitlines()[-1] == "PARITY spy ERROR exit=4 summary=-" and "4321" not in out, out


@case
def every_check_is_named_in_COMPUTES_and_no_other_statistic_is_used():
    seen = set()
    a, md5, b1, b2 = spy_files()
    _, _, s, _ = run(spy_args(a, md5, ("fmp", str(b1)), ("kis", str(b2))))
    runs = [s]
    d, p, v = BTC
    runs.append(btc_run(d, p, d, v)[2])
    _, vals, _ = RF
    runs.append(rf_run(vals, *rf_b(vals))[2])
    for summ in runs:
        seen |= {c["id"] for c in summ["integrity"]}
        seen |= {c["id"] for pair in summ["pairs"] for c in pair["checks"]}
    assert seen == set(pc.COMPUTES), sorted(seen ^ set(pc.COMPUTES))
    code = (HERE / "parity_check.py").read_text(encoding="utf-8")
    hits = re.findall(r"\b(corrcoef|cov|std|var|mean|nanmean|nanstd|sharpe|drawdown)\s*\(", code, flags=re.I)
    assert not hits, hits


def main() -> int:
    for fn in CASES:
        try:
            fn()
        except Exception as exc:                              # report the first failing case and stop
            print(f"FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
            print(f"SELFTEST FAIL at {fn.__name__}")
            return 1
        print(f"ok   {fn.__name__}")
    print(f"SELFTEST PASS {len(CASES)} cases (temp root {ROOT})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
