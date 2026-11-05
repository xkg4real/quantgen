"""Suite `provider_parity`: tools/provider_parity/parity_check.py (spec 2026-10-26 section 10.5, roadmap item 5-2).

Synthetic series and mocked HTTP only: every test runs with socket connects and the tool's own HTTP layer patched to
raise, so a test that reached the network would fail. No real price, rate, pilot table or key is read; every file is
written into a fresh folder under the system temp dir, and nothing in the repository is read except the tool itself.

    python -m tests.provider_parity_acceptance        # or: python tests/run_all.py --suite provider_parity

Covered: every outcome (PASS, FAIL, WARN, WITHHELD, REFUSED, ERROR) for SPY, BTC-USD and DGS3MO; the late-starting
provider rule (P-D5); the 2027-01-01 cut-off in fetch and compare; md5 refusal; the 10.5.2 summary allow-list; that no
key value is ever printed or written; every fetcher over a fake transport; COMPUTES against the checks (selftest).
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import socket
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.provider_parity import parity_check as pc  # noqa: E402

NOW = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
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


def spy_like(seed: int = 7, lo: str = "2009-06-01", hi: str = "2016-12-30"):
    """Weekday sessions, a 2-decimal raw close with four dividends a year, and the backward total-return adjustment a
    Yahoo-style adjusted close applies (factor 1 - D / P_prev before each ex-date). Synthetic: no real SPY value."""
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
                div[i] = round(0.0045 * raw[i - 1], 2)
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
    w = spy_world()
    fmp, kis, _ = spy_b(w)
    for bad in ([["--pair", "coinbase", str(fmp)]],                                      # not a SPY provider
                [["--pair", "fmp", str(fmp)]],                                           # kis, yahoo_now unaccounted
                [["--pair", "fmp", str(fmp)], ["--pair", "fmp", str(fmp)]],              # named twice
                [["--pair", "fmp", str(fmp)], ["--unavailable", "kis", "busy"],
                 ["--unavailable", "yahoo_now", "no_key"]]):                             # not a listed reason
        code, out, s, path = w.compare([], unavailable=[x for arg in bad for x in arg])
        assert code == 2 and s is None and not path.exists() and "REFUSED" in out, (bad, out)
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
    cases = {"SPY table for btc": ("btc", {}), "table end in 2027": ("spy", {"end": "2027-01-04"}),
             "another file name": ("spy", {"prices_file": "synthetic/yf_QQQ.csv"}),
             "a parent path": ("spy", {"prices_file": "../yf_SPY.csv"}), "rf without rf_file": ("rf", {}),
             "not a table": ("spy", {"schema": "something-else"})}
    for name, (series, change) in cases.items():
        w.table.write_text(json.dumps({**json.loads(original), **change}), encoding="utf-8")
        w.series = series
        code, out, s, path = w.compare([], unavailable=account(series, []))
        assert code == 2 and s is None and not path.exists(), (name, out)
    w.series = "spy"
    w.table.write_text(original, encoding="utf-8")
    outside = w.root / "table.json"
    outside.write_text(original, encoding="utf-8")
    code, out, _, _ = capture_compare(w, table=outside)
    assert code == 2 and "inside --repo" in out, out
    (w.repo / ".git").rmdir()
    code, out, _, _ = capture_compare(w)
    assert code == 2 and "no .git" in out, out


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


def test_btc_seven_missing_days_in_a_fail_two_warn():
    d, p, v = BTC
    rng = np.random.default_rng(3)
    for n, want, code_want in ((7, "FAIL", 1), (2, "WARN", 0)):
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


def fake_kis(calls: list):
    d0, raw0, _, _ = SPY

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


def test_load_keys_reads_only_the_named_keys():
    root = tmp()
    keys = pc.load_keys(key_file(root), environ={})
    assert keys == {"FMP_API_KEY": FMP_KEY, "KIS_APP_KEY": KIS_KEY, "KIS_APP_SECRET": KIS_SECRET,
                    "KIS_BASE_URL": "https://kis.invalid:9443"}
    assert pc.load_keys(None, environ={"FMP_API_KEY": "<your key>", "KIS_APP_KEY": " x1234 "}) == {"KIS_APP_KEY": "x1234"}
    assert pc._redact(f"a {FMP_KEY} b", [FMP_KEY]) == "a <redacted> b"


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
