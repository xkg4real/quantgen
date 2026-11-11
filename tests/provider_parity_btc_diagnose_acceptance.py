"""Suite `provider_parity_btc_diagnose`: tools/provider_parity/btc_diagnose.py (owner ruling BTC-나 of 2026-11-11).

The script is run once on the owner's machine and its console output is pasted into the chat, so the cases hold two
things: that what it prints is right (the tool's own counts, split by year), and that it prints nothing but the line
kinds its docstring lists: the two kinds of statistic the owner's option named (per calendar year the number of
disagreement days, and the 99th percentile and the maximum of the level difference) and, beside them, counts and
identifiers. No price, no return and no date finer than a calendar year is among them. The maximum is the level
difference of one day, by the ruling; its date is not printed.

Synthetic series only, built the way tests/provider_parity_acceptance.py builds them (its helpers are imported): a
fake research clone with a pilot table and a synthetic pinned file in a fresh folder under the system temp dir, and
synthetic provider files. Every case runs with socket connects patched to raise. No real price, pilot table, cache
file, `.env` or key is read. In the repository the suite reads the script, the tool, the helper suite, the rerun
guide (its step 18 is run as written) and the CI workflow, each of which is on that workflow's path filter.

    python -B -m unittest tests.provider_parity_btc_diagnose_acceptance -v
    python -B -m tests.provider_parity_btc_diagnose_acceptance          # the same cases, one PASS or FAIL line each

Expected numbers are typed by hand where a case plants the days itself, and are otherwise computed apart from the
script: the files are parsed line by line here and the differences taken with `math.log`, not with the tool's readers.
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests import provider_parity_acceptance as base  # noqa: E402
from tools.provider_parity import btc_diagnose as bd  # noqa: E402

pc = base.pc
WIN = base.BTC_WIN                                   # 2015-01-01 .. 2019-12-31; the late segment starts 2017-01-01
DAYS = base.alldays(*WIN)
YEARS = (2015, 2016, 2017, 2018, 2019)
DAYS_IN = {2015: 365, 2016: 366, 2017: 365, 2018: 365, 2019: 365}
SCRIPT = ROOT / "tools" / "provider_parity" / "btc_diagnose.py"

# The allow-list of this suite, typed apart from the script's own LINE_SHAPES: a line of any other shape fails.
_HEX, _DAY, _N, _PCT = r"[0-9a-f]{64}", r"\d{4}-\d{2}-\d{2}", r"(?:0|[1-9]\d{0,4})", r"(?:\d{1,3}\.\d|n/a)"
_PAIRS = r"(?:pinned-coinbase|pinned-bitstamp|coinbase-bitstamp)"
ALLOWED = [re.compile(x) for x in (
    rf"BTCDIAG 1 tool_sha256={_HEX} script_sha256={_HEX}",
    rf"window start={_DAY} end={_DAY} late_from={_DAY} ret_diff_big=0\.02 level_p99_max=0\.015 level_max=0\.05",
    rf"file (?:coinbase|bitstamp) sha256={_HEX} fetch_record=(?:yes|no)",
    rf"common {_PAIRS} days={_N}",
    rf"returns {_PAIRS} year=20\d\d days={_N} over={_N}",
    rf"returns pinned-(?:coinbase|bitstamp) total days={_N} over={_N} tool_over={_N} tool_allowed={_N}",
    rf"returns coinbase-bitstamp total days={_N} over={_N}",
    rf"levels {_PAIRS} segment=(?:late|early) days={_N} p99_pct={_PCT} max_pct={_PCT} over_p99_max={_N} over_max={_N}",
    rf"split (?:year=20\d\d|total) both={_N} coinbase_only={_N} bitstamp_only={_N} coinbase_edge={_N} "
    rf"bitstamp_edge={_N} coinbase_unpaired={_N} bitstamp_unpaired={_N}",
    rf"venues (?:year=20\d\d|total) both={_N} agree={_N} differ={_N} unpaired={_N}",
    r"BTCDIAG OK exit=0")]


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #
def paths(seed: int = 31):
    """Pinned, coinbase and bitstamp: one random path and two venues a tenth of a percent of noise around it. Every
    price has at least five digits before the point, so a price that reached the output would be seen."""
    rng = np.random.default_rng(seed)
    p = 60000.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, len(DAYS))))
    assert p.min() > 10000.0, p.min()
    return p, p * np.exp(rng.normal(0.0, 0.001, len(DAYS))), p * np.exp(rng.normal(0.0, 0.001, len(DAYS)))


PIN, CB, BS = paths()
# a split line with nothing in it
NO_SPLIT = {"both": 0, "coinbase_only": 0, "bitstamp_only": 0, "coinbase_edge": 0, "bitstamp_edge": 0,
            "coinbase_unpaired": 0, "bitstamp_unpaired": 0}


def bumped(values, plan: dict[str, float]):
    """A copy with the close of each named day moved by exp(x): one day off, so its return and the next day's both
    differ by about x."""
    out = np.array(values, dtype=float)
    for day, x in plan.items():
        out[DAYS.index(day)] *= math.exp(x)
    return out


class Files:
    """A fake research clone with the pinned file `a`, and the two provider files (each a list of days and values)."""

    def __init__(self, a=None, cb=None, bs=None, *, a_days=None, cb_days=None, bs_days=None):
        a_values = dict(zip(DAYS, PIN if a is None else a))
        a_days = DAYS if a_days is None else a_days
        self.w = base.btc_world(a_days, np.array([a_values[d] for d in a_days]))
        cb_days, bs_days = DAYS if cb_days is None else cb_days, DAYS if bs_days is None else bs_days
        cb_values = dict(zip(DAYS, CB if cb is None else cb))
        bs_values = dict(zip(DAYS, BS if bs is None else bs))
        self.coinbase = self.w.file("btc_coinbase.csv",
                                    base.provider_text(cb_days, [cb_values[d] for d in cb_days], 2))
        self.bitstamp = self.w.file("btc_bitstamp.csv",
                                    base.provider_text(bs_days, [bs_values[d] for d in bs_days], 2))
        self.pinned = self.w.repo / "synthetic" / "yf_BTC-USD.csv"

    def argv(self, pairs=None) -> list[str]:
        argv = ["--table", str(self.w.table), "--repo", str(self.w.repo)]
        for provider, path in (("coinbase", self.coinbase), ("bitstamp", self.bitstamp)) if pairs is None else pairs:
            argv += ["--pair", provider, str(path)]
        return argv

    def run(self, pairs=None, extra=()) -> tuple[int, list[str]]:
        code, out = base.capture(lambda: bd.run([*self.argv(pairs), *extra]))
        return code, out.splitlines()

    def summary(self) -> dict:
        """The tool's own compare of the same three files (binance declared unavailable)."""
        code, out, s, _ = self.w.compare([("coinbase", self.coinbase), ("bitstamp", self.bitstamp)])
        assert s is not None, out
        return s


def fields(line: str) -> dict:
    return dict(token.split("=", 1) for token in line.split() if "=" in token)


def table(lines: list[str], kind: str, pair: str | None = None) -> dict:
    """The lines of one kind (and pair) as {year or 'total' or segment: {field: int, or text for a percentage}}."""
    out = {}
    for line in lines:
        words = line.split()
        if words[0] != kind or (pair is not None and words[1] != pair):
            continue
        f = fields(line)
        key = int(f.pop("year")) if "year" in f else f.pop("segment") if "segment" in f else "total"
        out[key] = {k: v if k.endswith("_pct") else int(v) for k, v in f.items()}
    return out


def over_by_year(lines, pair) -> dict:
    return {y: row["over"] for y, row in table(lines, "returns", pair).items()}


def read_by_hand(path: Path) -> dict[str, float]:
    """date -> value from a CSV, parsed line by line: the window's rows with a positive value."""
    rows = [line.split(",") for line in Path(path).read_text(encoding="utf-8").splitlines()[1:]]
    return {d: float(v) for d, v in rows if WIN[0] <= d <= WIN[1] and v and float(v) > 0}


def apart(x: dict, y: dict):
    """Computed apart from the script: the common days, each day's level difference, and the days whose log-return
    difference is above 0.02 (typed here, not read from the tool)."""
    days = sorted(set(x) & set(y))
    level = {d: abs(math.log(x[d] / y[d])) for d in days}
    over = {d: abs((math.log(x[d]) - math.log(x[e])) - (math.log(y[d]) - math.log(y[e]))) > 0.02
            for e, d in zip(days, days[1:])}
    return days, level, over


def levels_by_hand(level: dict) -> dict:
    """Per segment what a levels line says: one decimal of a percent, and `n/a` under 100 days (typed here)."""
    out = {}
    for segment, values in (("late", [v for d, v in level.items() if d >= "2017-01-01"]),
                            ("early", [v for d, v in level.items() if d < "2017-01-01"])):
        enough = len(values) >= 100
        out[segment] = {"days": len(values),
                        "p99_pct": f"{100 * float(np.percentile(values, 99)):.1f}" if enough else "n/a",
                        "max_pct": f"{100 * max(values):.1f}" if enough else "n/a",
                        "over_p99_max": sum(v > 0.015 for v in values), "over_max": sum(v > 0.05 for v in values)}
    return out


# --------------------------------------------------------------------------- #
# What it prints
# --------------------------------------------------------------------------- #
def test_clean_files_print_the_documented_lines_in_order_with_no_disagreement_day():
    """Three series that agree: the lines come in the documented order (the two hashes, the window and thresholds,
    the two provider files, the common days of the three pairs, then (b), (c), (d), (e), (f)), every year of the
    table's window has its line even when nothing happened in it, and the first line names the tool file and the
    script by their own bytes. Each `file` line gives the sha256 of the provider file as it lies on disk, which is
    the `file_sha256` the tool's own compare writes into its summary for the same file, and says whether a fetch
    record lay beside it (none here: these files were written by hand)."""
    f = Files()
    code, lines = f.run()
    assert code == 0 and lines[-1] == "BTCDIAG OK exit=0", lines
    summary = f.summary()
    by_provider = {pair["provider"]: pair for pair in summary["pairs"]}
    for line, (provider, path) in zip(lines[2:4], (("coinbase", f.coinbase), ("bitstamp", f.bitstamp))):
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert line == f"file {provider} sha256={sha} fetch_record=no", line
        assert (by_provider[provider]["file_sha256"], by_provider[provider]["has_fetch_record"]) == (sha, False)
    lines = lines[:2] + lines[4:]                                    # the rest as it was before the file lines
    kinds = [(line.split()[0], line.split()[1]) for line in lines[2:-1]]
    per_year = [("returns", "pinned-coinbase")] * 6 + [("returns", "pinned-bitstamp")] * 6
    assert [k for k, _ in kinds] == ["common"] * 3 + ["returns"] * 12 + ["levels"] * 4 + ["split"] * 6 + \
        ["returns"] * 6 + ["levels"] * 2 + ["venues"] * 6, kinds
    assert kinds[3:15] == per_year and kinds[15:19] == [("levels", "pinned-coinbase")] * 2 + \
        [("levels", "pinned-bitstamp")] * 2 and kinds[25:33] == [("returns", "coinbase-bitstamp")] * 6 + \
        [("levels", "coinbase-bitstamp")] * 2, kinds
    assert lines[0] == (f"BTCDIAG 1 tool_sha256={hashlib.sha256(Path(pc.__file__).read_bytes()).hexdigest()} "
                        f"script_sha256={hashlib.sha256(SCRIPT.read_bytes()).hexdigest()}"), lines[0]
    assert lines[1] == ("window start=2015-01-01 end=2019-12-31 late_from=2017-01-01 ret_diff_big=0.02 "
                        "level_p99_max=0.015 level_max=0.05"), lines[1]
    assert lines[2:5] == ["common pinned-coinbase days=1826", "common pinned-bitstamp days=1826",
                          "common coinbase-bitstamp days=1826"], lines[2:5]
    for pair in ("pinned-coinbase", "pinned-bitstamp", "coinbase-bitstamp"):
        rows = table(lines, "returns", pair)
        assert list(rows) == [*YEARS, "total"], (pair, list(rows))
        # the first day of the window has no return, so 2015 counts 364
        assert {y: rows[y]["days"] for y in YEARS} == {**DAYS_IN, 2015: 364} and rows["total"]["days"] == 1825, rows
        assert all(row["over"] == 0 for row in rows.values()), (pair, rows)
        seg = table(lines, "levels", pair)
        assert (seg["late"]["days"], seg["early"]["days"]) == (1095, 731) and list(seg) == ["late", "early"], seg
        assert all(row["over_p99_max"] == row["over_max"] == 0 for row in seg.values()), seg
    for pair in ("pinned-coinbase", "pinned-bitstamp"):
        assert table(lines, "returns", pair)["total"]["tool_over"] == 0
        assert table(lines, "returns", pair)["total"]["tool_allowed"] == 9 == int(0.005 * 1825)
    zero = dict(NO_SPLIT)
    assert table(lines, "split") == {k: zero for k in (*YEARS, "total")}, table(lines, "split")
    assert table(lines, "venues") == {k: {"both": 0, "agree": 0, "differ": 0, "unpaired": 0}
                                      for k in (*YEARS, "total")}, table(lines, "venues")


def test_disagreement_days_per_year_are_the_tool_s_own_count_split_by_year():
    """(b): one close of a provider moved 4% makes that day's return and the next day's differ from the pinned
    file's. The days are planted by hand, so the count of each year is known: two closes in 2015 (four days), the
    close of 2016-12-31 (one day in 2016 and one in 2017), three closes in 2018 (six days) and the last close of the
    window (one day, 2019). The yearly counts add up to the total line, and the total is the tool's own
    `n_big_return_diff_days` of the same files, read here from the summary that compare writes; `tool_allowed` is
    its `n_allowed`. The other provider's counts are its own."""
    cb = bumped(CB, {"2015-03-10": 0.04, "2015-09-01": -0.04, "2016-12-31": 0.04, "2018-02-02": 0.04,
                     "2018-06-05": 0.04, "2018-11-20": -0.04, "2019-12-31": 0.04})
    bs = bumped(BS, {"2017-07-07": 0.04, "2019-01-01": 0.04})
    f = Files(cb=cb, bs=bs)
    code, lines = f.run()
    assert code == 0, lines
    assert over_by_year(lines, "pinned-coinbase") == {2015: 4, 2016: 1, 2017: 1, 2018: 6, 2019: 1, "total": 13}, lines
    assert over_by_year(lines, "pinned-bitstamp") == {2015: 0, 2016: 0, 2017: 2, 2018: 0, 2019: 2, "total": 4}, lines
    s = f.summary()
    for provider in ("coinbase", "bitstamp"):
        tool = base.check_of(s, provider, "levels_and_returns")
        rows = table(lines, "returns", f"pinned-{provider}")
        assert sum(rows[y]["over"] for y in YEARS) == rows["total"]["over"] == rows["total"]["tool_over"] == \
            tool["n_big_return_diff_days"], (provider, rows, tool)
        assert rows["total"]["tool_allowed"] == tool["n_allowed"] == 9, (provider, rows, tool)
        assert sum(rows[y]["days"] for y in YEARS) == rows["total"]["days"] == \
            base.check_of(s, provider, "coverage")["n_common"] - 1, rows
    assert base.check_of(s, "coinbase", "levels_and_returns")["n_big_return_diff_days"] == 13 > 9
    # apart from the script: the same counts from the files parsed by hand
    a, c = read_by_hand(f.pinned), read_by_hand(f.coinbase)
    _, _, over = apart(a, c)
    assert {y: sum(o for d, o in over.items() if int(d[:4]) == y) for y in YEARS} == \
        {y: n for y, n in over_by_year(lines, "pinned-coinbase").items() if y != "total"}


def test_level_statistics_are_those_of_the_files_and_fall_in_the_tool_s_buckets():
    """(c): per segment the 99th percentile and the maximum of abs(log(P_pinned / P_provider)), in percent with one
    decimal, and the days above `level_p99_max` (1.5%) and above `level_max` (5%). Planted in bitstamp: 20 late
    closes 3% off and 2 late closes 6% off (22 days above 1.5%, 2 above 5%, a 99th percentile inside the 3% days), and
    one early close 12% off. The printed values equal those computed here from the files parsed by hand, and each
    falls in the decade bucket the tool's own summary gives for the same segment (as far as one decimal can say); the
    days per segment are the tool's too. `max_pct` is the level difference of one day, the planted one: the ruling
    names the maximum, and the line gives no date."""
    late = [d for d in DAYS if d >= "2017-01-01"]
    plan = {late[40 + 37 * k]: 0.03 for k in range(20)}
    plan.update({late[900]: 0.06, late[1000]: -0.06, "2015-08-20": 0.12})
    f = Files(bs=bumped(BS, plan))
    code, lines = f.run()
    assert code == 0, lines
    seg = table(lines, "levels", "pinned-bitstamp")
    assert (seg["late"]["over_p99_max"], seg["late"]["over_max"]) == (22, 2), seg
    assert (seg["early"]["over_p99_max"], seg["early"]["over_max"]) == (1, 1), seg
    assert seg["late"]["p99_pct"] in ("2.9", "3.0", "3.1") and seg["late"]["max_pct"] in ("5.9", "6.0", "6.1"), seg
    assert seg["early"]["max_pct"] in ("11.9", "12.0", "12.1") and float(seg["early"]["p99_pct"]) < 0.5, seg
    a, b = read_by_hand(f.pinned), read_by_hand(f.bitstamp)
    one_day = max(abs(math.log(a[d] / b[d])) for d in (late[900], late[1000]))       # the two planted 6% days
    assert seg["late"]["max_pct"] == f"{100 * one_day:.1f}", seg
    s = f.summary()
    a = read_by_hand(f.pinned)
    for provider, path in (("coinbase", f.coinbase), ("bitstamp", f.bitstamp)):
        printed = table(lines, "levels", f"pinned-{provider}")
        _, level, _ = apart(a, read_by_hand(path))
        assert printed == levels_by_hand(level), (provider, printed, levels_by_hand(level))
        tool = base.check_of(s, provider, "levels_and_returns")
        for segment in ("late", "early"):
            assert printed[segment]["days"] == tool[segment]["n_days"], (provider, segment)
            for stat in ("p99", "max"):                 # one decimal: the bucket of the value or of its rounding edge
                x = float(printed[segment][f"{stat}_pct"])
                assert tool[segment][f"{stat}_bucket"] in {pc.bucket(max(v, 0.0) / 100)
                                                           for v in (x - 0.05, x, x + 0.05)}, (provider, segment, stat)
    assert base.check_of(s, "bitstamp", "levels_and_returns")["late"]["within_band"] is False
    # (e) the same statistics for coinbase against bitstamp, which involve no pinned value
    _, level, over = apart(read_by_hand(f.coinbase), read_by_hand(f.bitstamp))
    assert table(lines, "levels", "coinbase-bitstamp") == levels_by_hand(level)
    assert over_by_year(lines, "coinbase-bitstamp")["total"] == sum(over.values()) == 46      # 23 closes, two days each


def test_a_pinned_series_that_stands_apart_reads_as_both_and_agree():
    """(d) and (f), the case "the pinned series differs from the venues": the pinned close is moved on five days and
    the venues are left alone. Every disagreement day is then one against both providers, none against one only, and
    on every such day coinbase and bitstamp agree with each other. (e) shows no disagreement between the venues."""
    f = Files(a=bumped(PIN, {"2015-05-05": 0.04, "2016-08-08": -0.04, "2018-01-15": 0.04, "2018-10-10": 0.04,
                             "2019-06-06": -0.04}))
    code, lines = f.run()
    assert code == 0, lines
    want = {2015: 2, 2016: 2, 2017: 0, 2018: 4, 2019: 2, "total": 10}
    assert over_by_year(lines, "pinned-coinbase") == over_by_year(lines, "pinned-bitstamp") == want, lines
    split, venues = table(lines, "split"), table(lines, "venues")
    assert {k: row["both"] for k, row in split.items()} == want, split
    assert all(row["coinbase_only"] == row["bitstamp_only"] == row["coinbase_unpaired"] == row["bitstamp_unpaired"] == 0
               for row in split.values()), split
    assert venues == {k: {"both": n, "agree": n, "differ": 0, "unpaired": 0} for k, n in want.items()}, venues
    assert all(n == 0 for n in over_by_year(lines, "coinbase-bitstamp").values()), lines


def test_a_venue_that_stands_apart_reads_as_only_and_two_venues_apart_read_as_differ():
    """(d) and (f), the case "the venues differ from each other". Coinbase alone is moved on three days in 2018: six
    disagreement days against coinbase only, none against both, bitstamp untouched, and (e) counts the same six days
    between the venues. On 2019-04-04 both venues are moved, by 4% and by 9%: two days against both providers, and on
    both of them the venues differ from each other too. On 2016-02-02 both venues are moved by the same 4%: two days
    against both providers on which the venues agree."""
    cb = bumped(CB, {"2018-03-03": 0.04, "2018-07-07": -0.04, "2018-12-12": 0.04, "2019-04-04": 0.04,
                     "2016-02-02": 0.04})
    bs = bumped(BS, {"2019-04-04": 0.09, "2016-02-02": 0.04})
    code, lines = Files(cb=cb, bs=bs).run()
    assert code == 0, lines
    assert over_by_year(lines, "pinned-coinbase") == {2015: 0, 2016: 2, 2017: 0, 2018: 6, 2019: 2, "total": 10}, lines
    assert over_by_year(lines, "pinned-bitstamp") == {2015: 0, 2016: 2, 2017: 0, 2018: 0, 2019: 2, "total": 4}, lines
    assert over_by_year(lines, "coinbase-bitstamp") == {2015: 0, 2016: 0, 2017: 0, 2018: 6, 2019: 2, "total": 8}, lines
    none = dict(NO_SPLIT)
    assert table(lines, "split") == {2015: none, 2016: {**none, "both": 2}, 2017: none,
                                     2018: {**none, "coinbase_only": 6}, 2019: {**none, "both": 2},
                                     "total": {**none, "both": 4, "coinbase_only": 6}}, table(lines, "split")
    quiet = {"both": 0, "agree": 0, "differ": 0, "unpaired": 0}
    venues = table(lines, "venues")
    assert venues == {2015: quiet, 2016: {**quiet, "both": 2, "agree": 2}, 2017: quiet, 2018: quiet,
                      2019: {**quiet, "both": 2, "differ": 2},
                      "total": {"both": 4, "agree": 2, "differ": 2, "unpaired": 0}}, venues
    # the mirror image: bitstamp alone
    code, lines = Files(bs=bumped(BS, {"2017-05-05": 0.04})).run()
    assert table(lines, "split")["total"] == {**none, "bitstamp_only": 2} and code == 0, table(lines, "split")


def test_a_day_over_the_threshold_against_one_venue_and_under_it_against_the_other_is_an_edge_day():
    """Review of 2026-11-11 (BD-3): a disagreement day against one provider alone does not by itself mean that the
    provider is the odd one. Here the two venues are the same path with no noise; coinbase's close is 1.4% lower on
    one day and the pinned close 1.6% higher on that day. Against coinbase the pinned return differs by 3.0% (over
    the 2% threshold), against bitstamp by 1.6% (under it), and the venues differ from each other by 1.4% (under
    it): no series is clearly the odd one, so the two days are `coinbase_edge`, not `coinbase_only`, and (e) shows
    no disagreement between the venues. With coinbase 2.5% lower instead, the venues differ from each other too
    and the same days are `coinbase_only`: coinbase is the odd one. Each disagreement day of a provider is in
    exactly one group."""
    exact = np.array(PIN)
    for cb_move, group, venue_days in ((-0.014, "coinbase_edge", 0), (-0.025, "coinbase_only", 2)):
        f = Files(a=bumped(PIN, {"2018-05-05": 0.016}), cb=bumped(exact, {"2018-05-05": cb_move}), bs=exact)
        code, lines = f.run()
        assert code == 0, lines
        assert over_by_year(lines, "pinned-coinbase")["total"] == 2, (cb_move, lines)
        assert over_by_year(lines, "pinned-bitstamp")["total"] == 0, (cb_move, lines)
        assert over_by_year(lines, "coinbase-bitstamp")["total"] == venue_days, (cb_move, lines)
        split = table(lines, "split")
        assert split[2018] == {**NO_SPLIT, group: 2} == split["total"], (cb_move, split)
        assert table(lines, "venues")["total"] == {"both": 0, "agree": 0, "differ": 0, "unpaired": 0}


def test_a_day_the_other_provider_was_not_compared_is_unpaired_not_only():
    """A provider that starts late, as coinbase did in the run of record (2015-07-20), is not compared before its
    first day. A disagreement day against bitstamp in that stretch says nothing about coinbase, so it is counted
    apart as `bitstamp_unpaired`, not as `bitstamp_only`; per year, `both`, `_only` and `_unpaired` of a provider add
    up to its disagreement days of (b). The same holds for a day inside a provider's outage and for the first day
    after it (review of 2026-11-11, BD-6): the other provider's return for that day runs from before the outage, so
    it is not a return over the same two days and cannot say that the other provider "agreed". A day is `both` or
    `_only` only when both providers have a return against pinned from the same previous day. `unpaired` in (f) is
    the `both` day whose return between the two venues runs from another previous day: here pinned lacks a day
    both venues have."""
    start = DAYS.index("2015-07-20")
    gone = {"2018-04-10", "2018-04-11"}                                     # two days coinbase lacks
    cb_days = [d for d in DAYS[start:] if d not in gone]
    a = bumped(PIN, {"2015-03-10": 0.04,          # before coinbase starts: two days against bitstamp alone
                     "2018-04-10": 0.04,          # inside coinbase's outage: the return of 04-12 spans three days
                     "2019-09-09": 0.04})         # both providers are there
    f = Files(a=a, cb_days=cb_days)
    code, lines = f.run()
    assert code == 0 and lines[4:7] == ["common pinned-coinbase days=1624", "common pinned-bitstamp days=1826",
                                        "common coinbase-bitstamp days=1624"], lines[:7]
    assert table(lines, "returns", "pinned-coinbase")[2015] == {"days": 164, "over": 0}, lines
    split = table(lines, "split")
    none = dict(NO_SPLIT)
    assert split == {2015: {**none, "bitstamp_unpaired": 2}, 2016: none, 2017: none,
                     2018: {**none, "bitstamp_unpaired": 2}, 2019: {**none, "both": 2},
                     "total": {**none, "both": 2, "bitstamp_unpaired": 4}}, split
    for provider in ("coinbase", "bitstamp"):
        for when, row in split.items():
            assert row["both"] + row[f"{provider}_only"] + row[f"{provider}_edge"] + row[f"{provider}_unpaired"] == \
                over_by_year(lines, f"pinned-{provider}")[when], (provider, when, row)
    assert table(lines, "venues")["total"] == {"both": 2, "agree": 2, "differ": 0, "unpaired": 0}
    # the pinned close is wrong on the SECOND of the two days coinbase lacks: bitstamp shows it on 04-11 and on 04-12.
    # Coinbase has 04-12, but its return for that day runs from 04-09 and cannot see the close of 04-11, so 04-12 is
    # not a day on which coinbase "agreed": both days are unpaired, none is bitstamp_only
    code, lines = Files(a=bumped(PIN, {"2018-04-11": 0.04}), cb_days=cb_days).run()
    split = table(lines, "split")
    assert code == 0 and split[2018] == {**none, "bitstamp_unpaired": 2} == split["total"], split
    assert over_by_year(lines, "pinned-coinbase")["total"] == 0 and over_by_year(lines, "pinned-bitstamp")[2018] == 2
    # two providers that each have one day of their own before their first common day: coinbase 07-20, bitstamp
    # 07-21, both from 07-22 on; the pinned close of 07-22 moves. On 07-22 each provider's return runs from its own
    # earlier day, so that day is unpaired for both; 07-23 is against both, and the venues agree on it
    cb_days = ["2015-07-20"] + DAYS[DAYS.index("2015-07-22"):]
    bs_days = ["2015-07-21"] + DAYS[DAYS.index("2015-07-22"):]
    code, lines = Files(a=bumped(PIN, {"2015-07-22": 0.04}), cb_days=cb_days, bs_days=bs_days).run()
    split, venues = table(lines, "split"), table(lines, "venues")
    assert code == 0 and split[2015] == {**none, "both": 1, "coinbase_unpaired": 1, "bitstamp_unpaired": 1}, split
    assert venues[2015] == {"both": 1, "agree": 1, "differ": 0, "unpaired": 0} == venues["total"], venues
    assert lines[4:7] == ["common pinned-coinbase days=1625", "common pinned-bitstamp days=1625",
                          "common coinbase-bitstamp days=1624"], lines[4:7]
    # (f) unpaired: pinned lacks 2018-08-08, which both venues have, and its close of 08-09 moves. Against each
    # provider the return of 08-09 runs from 08-07 (the same two days: `both`); between the venues it runs from
    # 08-08, so the venues have no return over those two days. 08-10 is an ordinary `both` day on which they agree
    code, lines = Files(a=bumped(PIN, {"2018-08-09": 0.04}), a_days=[d for d in DAYS if d != "2018-08-08"]).run()
    split, venues = table(lines, "split"), table(lines, "venues")
    assert code == 0 and split[2018] == {**none, "both": 2} == split["total"], split
    assert venues[2018] == {"both": 2, "agree": 1, "differ": 0, "unpaired": 1} == venues["total"], venues
    for row in venues.values():
        assert row["agree"] + row["differ"] + row["unpaired"] == row["both"], venues
    assert lines[4:7] == ["common pinned-coinbase days=1825", "common pinned-bitstamp days=1825",
                          "common coinbase-bitstamp days=1826"], lines[4:7]
    # the same gap in pinned, and a day against coinbase alone: on 08-09 the venues have no return with each other
    # over the two days pinned compares (08-07 to 08-09), so the day cannot be called `_only` or `_edge` and is
    # unpaired; 08-10 has such a return, on which the venues agree, and is an edge day
    exact = np.array(PIN)
    code, lines = Files(a=bumped(PIN, {"2018-08-09": 0.016}), a_days=[d for d in DAYS if d != "2018-08-08"],
                        cb=bumped(exact, {"2018-08-09": -0.014}), bs=exact).run()
    split = table(lines, "split")
    assert code == 0 and split[2018] == {**none, "coinbase_unpaired": 1, "coinbase_edge": 1} == split["total"], split
    assert over_by_year(lines, "pinned-coinbase")["total"] == 2 and over_by_year(lines, "pinned-bitstamp")["total"] == 0
    # the other way round: bitstamp lacks the two days on which the pinned close of 2017-03-03 shows against coinbase
    code, lines = Files(a=bumped(PIN, {"2017-03-03": 0.04}),
                        bs_days=[d for d in DAYS if d not in ("2017-03-03", "2017-03-04")]).run()
    split = table(lines, "split")
    assert code == 0 and split[2017] == {**none, "coinbase_unpaired": 2} == split["total"], split
    assert over_by_year(lines, "pinned-bitstamp")["total"] == 0 and table(lines, "venues")["total"]["both"] == 0, lines


def test_level_lines_use_the_late_thresholds_in_both_segments_and_say_n_a_for_a_short_segment():
    """Two things about the `levels` lines that no case held (review of 2026-11-11, BD-2, BD-5, BD-9). The two counts
    above a threshold use `level_p99_max` (1.5%) and `level_max` (5%) in the early segment as in the late one; the
    tool's own early band is wider (3% and 10%), so an early day 2% off and an early day 7% off are counted here
    while the tool's early check still passes. And a segment of fewer than 100 days, an empty one included, prints
    `n/a` for its 99th percentile and its maximum, which would be the figures of a few days; its counts are still
    printed. With 100 days the two figures are there."""
    f = Files(bs=bumped(BS, {"2015-06-06": 0.02, "2016-03-03": 0.07}))
    code, lines = f.run()
    early = table(lines, "levels", "pinned-bitstamp")["early"]
    assert code == 0 and (early["days"], early["over_p99_max"], early["over_max"]) == (731, 2, 1), early
    assert early["max_pct"] in ("6.9", "7.0", "7.1"), early
    tool = base.check_of(f.summary(), "bitstamp", "levels_and_returns")
    assert tool["early"]["within_band"] is True and tool["outcome"] != "FAIL", tool
    t = pc.THRESHOLDS["btc"]
    old = t["late_from"]
    f = Files(bs=bumped(BS, {DAYS[50]: 0.06}))
    try:
        for late_from, days, shown in ((DAYS[0], 0, False), (DAYS[1], 1, False), (DAYS[99], 99, False),
                                       (DAYS[100], 100, True)):
            t["late_from"] = late_from
            code, lines = f.run()
            assert code == 0, (late_from, lines)
            for pair in ("pinned-coinbase", "pinned-bitstamp", "coinbase-bitstamp"):
                early = table(lines, "levels", pair)["early"]
                assert early["days"] == days, (late_from, pair, early)
                assert (early["p99_pct"] != "n/a") is shown and (early["max_pct"] != "n/a") is shown, (pair, early)
                assert table(lines, "levels", pair)["late"]["days"] == 1826 - days
            early = table(lines, "levels", "pinned-bitstamp")["early"]              # the planted day is DAYS[50]
            assert (early["over_p99_max"], early["over_max"]) == ((1, 1) if days > 50 else (0, 0)), (days, early)
            assert early["max_pct"] == ("n/a" if not shown else early["max_pct"]) and \
                (not shown or early["max_pct"] in ("5.9", "6.0", "6.1")), early
    finally:
        t["late_from"] = old
    assert bd.MIN_SEGMENT_DAYS == 100


# --------------------------------------------------------------------------- #
# What it never prints, and what it never does
# --------------------------------------------------------------------------- #
def digit_strings(*paths: Path) -> set[str]:
    """Every value of the files as it is written, and the digits before its point (five or more by construction)."""
    found = set()
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines()[1:]:
            value = line.split(",")[1]
            if value:
                found |= {value, value.split(".")[0]}
    return found


def test_output_is_held_to_an_allow_list_and_carries_no_price_no_return_and_no_day():
    """The ruling lets statistics that are not prices leave the machine, so the output is held mechanically. Every
    line has one of the shapes typed in this suite. The only dates are the table's start and end and the threshold
    `late_from`: no day of the data, in any spelling tried here. No value of the three files appears, nor the digits
    before its point (every synthetic price has five or more, and no count has that many). No return of a planted
    day appears, and no difference with more than one decimal of a percent. One level difference of a single day is
    in the output by design: `max_pct` is the difference of the day with the largest one (here a planted day),
    rounded to one decimal and without its date, because the ruling names the maximum. The numbers that do appear
    are counts, years, the three thresholds, the hashes of the first lines and percentages with one decimal. The
    files used here disagree on planted days, so there is something to leak."""
    planted = {"2015-03-14": 0.04, "2018-06-05": -0.07, "2018-11-23": 0.031, "2019-02-28": 0.045}
    f = Files(a=bumped(PIN, {"2016-10-09": 0.04}), cb=bumped(CB, planted), bs=bumped(BS, {"2018-06-05": 0.02}))
    code, lines = f.run()
    assert code == 0 and len(lines) == 44, lines
    for line in lines:
        assert sum(bool(shape.fullmatch(line)) for shape in ALLOWED) == 1, line
    assert [line.split()[0] for line in lines[:4]] == ["BTCDIAG", "window", "file", "file"], lines[:4]
    text = "\n".join(lines[4:])                                     # after the hashes and the window
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", "\n".join(lines[1:]))
    assert dates == ["2015-01-01", "2019-12-31", "2017-01-01"], dates
    for day in [*planted, "2016-10-09"]:
        y, m, d = day.split("-")
        for spelled in (day, f"{m}-{d}", f"{y}{m}{d}", f"{m}/{d}", f"{y}/{m}", f"{y}-{m}"):
            assert spelled not in text, (spelled, text)
    values = digit_strings(f.pinned, f.coinbase, f.bitstamp)
    assert len(values) > 5000 and all(len(v.split(".")[0]) >= 5 for v in values)
    leaked = [v for v in values if v in text]
    assert not leaked, leaked[:5]
    a, c = read_by_hand(f.pinned), read_by_hand(f.coinbase)
    for day in planted:                                              # the returns of each planted day, in percent
        before = DAYS[DAYS.index(day) - 1]
        for x in (math.log(c[day] / c[before]), math.log(a[day] / a[before])):
            for spelled in (f"{abs(100 * x):.1f}", f"{abs(100 * x):.2f}", f"{abs(x):.4f}", repr(abs(x))[:8]):
                assert f"={spelled}" not in text and f" {spelled}" not in text, (day, spelled)
    # the one difference of a single day that is printed: the late maximum, to one decimal and no further
    worst = abs(math.log(a["2018-06-05"] / c["2018-06-05"]))
    late = table(lines, "levels", "pinned-coinbase")["late"]
    assert late["max_pct"] == f"{100 * worst:.1f}" == "7.1" and f"{100 * worst:.2f}" not in text, (late, worst)
    numbers = re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", re.sub(r"year=\d{4}", "", text))
    decimals = sorted({n for n in numbers if "." in n})
    assert decimals and all(re.fullmatch(r"\d{1,2}\.\d", n) for n in decimals), decimals
    assert all(len(n) <= 4 for n in numbers if "." not in n), numbers            # counts: at most 1,826 days
    # the script's own allow-list refuses a line of any other shape, wherever it stands, before anything is printed
    hexes = "0" * 64
    levels = "levels pinned-coinbase segment=late days=1095 p99_pct={} max_pct={} over_p99_max=22 over_max=2"
    bad_lines = (
        "price 61234.55", "returns pinned-coinbase day=2018-06-05 over=1", "levels pinned-coinbase max=0.0712",
        "returns pinned-coinbase year=2018 days=365 over=6 worst=2018-06-05",
        "returns pinned-coinbase year=2018 days=365 over=6 day=2018-06-05",          # a date as one more field
        "split year=2018 both=1 coinbase_only=0 bitstamp_only=0 coinbase_edge=0 bitstamp_edge=0 coinbase_unpaired=0 "
        "bitstamp_unpaired=0 day=2018-06-05",
        "split year=2018 both=1 coinbase_only=0 bitstamp_only=0 coinbase_unpaired=0 bitstamp_unpaired=0",   # no edge
        "common pinned-coinbase days=123456",                                        # a count of six digits
        "returns pinned-coinbase year=2018 days=365 over=612345",
        levels.format("3.02", "6.1"), levels.format("3.0", "6.123"),                 # more than one decimal
        levels.format("61234.5", "6.1"), levels.format("high", "6.1"), levels.format("3.0", "61234"),
        "returns pinned-binance year=2018 days=365 over=6", "common coinbase-pinned days=10",    # another pair
        "levels pinned-coinbase segment=2018 days=365 p99_pct=3.0 max_pct=6.1 over_p99_max=2 over_max=0",
        f"file binance sha256={hexes} fetch_record=yes", f"file coinbase sha256={hexes} fetch_record=maybe",
        "file coinbase sha256=61234.55 fetch_record=yes",
        "BTCDIAG OK exit=0 61234.55", " BTCDIAG OK exit=0", "BTCDIAG OK exit=0\nprice 61234.55", "")
    for bad in bad_lines:
        for position in (0, 1, len(lines) // 2, len(lines) - 1, len(lines)):
            tried = lines[:position] + [bad] + lines[position:]
            try:
                bd.assert_lines_safe(tried)
            except bd.Mismatch as exc:
                assert str(exc) == f"line {position + 1} has a shape outside the allow-list", (bad, position, exc)
            else:
                raise AssertionError(f"the allow-list takes {bad!r} at line {position + 1}")
    bd.assert_lines_safe(lines)
    real = bd.diagnose
    for position in (0, 1, len(lines) - 1):          # a line that should never be built, first, second and last
        built = lines[:position] + ["price 61234.55"] + lines[position:]
        bd.diagnose = lambda *_a, built=built, **_k: built
        try:
            code, printed = f.run()
        finally:
            bd.diagnose = real
        assert (code, printed) == (4, [f"ERROR: line {position + 1} has a shape outside the allow-list",
                                       "BTCDIAG ERROR exit=4"]), printed


def test_anything_but_the_btc_table_and_coinbase_and_bitstamp_each_once_is_refused():
    """The script takes the BTC-USD table and the two providers of the ruling, each once. Anything else is refused
    with exit 2 and no line of data: another provider, one provider twice or alone, a third pair, the SPY table, a
    pinned file whose md5 is not the table's, a pinned cache path without --owner-run (refused before it is opened),
    a provider file with a row from 2027, and a research clone that holds the tool."""
    f = Files()
    cb, bs = f.coinbase, f.bitstamp

    def refused(pairs=None, words="", extra=(), files=f):
        code, lines = files.run(pairs, extra)
        assert code == 2 and len(lines) == 2 and lines[1] == "BTCDIAG REFUSED exit=2", lines
        assert lines[0].startswith("REFUSED: ") and words in lines[0], lines
    each_once = "--pair takes coinbase and bitstamp, each once, and no other provider"
    for pairs in ([("coinbase", cb), ("binance", bs)], [("coinbase", cb), ("coinbase", cb)], [("coinbase", cb)],
                  [("bitstamp", bs)], [], [("coinbase", cb), ("bitstamp", bs), ("binance", bs)],
                  [("coinbase", cb), ("bitstamp", bs), ("bitstamp", bs)], [("fmp", cb), ("kis", bs)]):
        refused(pairs, each_once)
    spy = base.spy_world()
    code, out = base.capture(lambda: bd.run(["--table", str(spy.table), "--repo", str(spy.repo), "--pair", "coinbase",
                                             str(cb), "--pair", "bitstamp", str(bs)]))
    assert code == 2 and out.splitlines() == ["REFUSED: --series btc takes the BTC-USD table",
                                              "BTCDIAG REFUSED exit=2"], out
    g = Files()
    tab = json.loads(g.w.table.read_text(encoding="utf-8"))
    g.w.table.write_text(json.dumps({**tab, "prices_md5": "0" * 32}), encoding="utf-8")
    refused(words="md5", files=g)
    g.w.table.write_text(json.dumps({**tab, "prices_file": "docs/asset_expansion/cache/yf_BTC-USD.csv"}),
                         encoding="utf-8")                              # not created: the guard comes first
    refused(words="--owner-run", files=g)
    refused(words="cannot be read (FileNotFoundError)", extra=["--owner-run"], files=g)
    late_row = f.w.file("btc_2027.csv", bs.read_text(encoding="utf-8") + "2027-01-04,61234.55\n")
    refused([("coinbase", cb), ("bitstamp", late_row)], "2027-01-01")
    code, out = base.capture(lambda: bd.run(["--table", str(f.w.table), "--repo", str(ROOT), "--pair", "coinbase",
                                             str(cb), "--pair", "bitstamp", str(bs)]))
    assert code == 2 and "--repo holds this tool" in out and base.last_line(out) == "BTCDIAG REFUSED exit=2", out
    one_day = Files(cb_days=DAYS[:1])                                   # one common day: no return to compare
    refused(words="fewer than two days in common", files=one_day)
    code, lines = f.run(extra=["--owner-run"])                          # the flag itself changes nothing
    assert code == 0 and lines[-1] == "BTCDIAG OK exit=0", lines


def test_files_in_their_fetch_folders_are_held_to_their_fetch_records():
    """On the owner's machine the two files lie in their fetch folders, each beside its fetch record. The script
    reads them through the tool's own reader, so the record's rules hold as in compare: the files of two fetches are
    taken, and a file edited after its fetch, or handed to the wrong provider name, is refused."""
    w = base.btc_world()
    folders = {}
    for provider, handler in (("coinbase", base.coinbase_handler), ("bitstamp", base.bitstamp_handler)):
        code, out, folders[provider] = base.fetch("btc", provider, start=WIN[0], end=WIN[1],
                                                  http=base.FakeHttp(handler))
        assert code == 0, out
    cb, bs = folders["coinbase"] / "btc_coinbase.csv", folders["bitstamp"] / "btc_bitstamp.csv"
    argv = ["--table", str(w.table), "--repo", str(w.repo)]
    code, out = base.capture(lambda: bd.run([*argv, "--pair", "coinbase", str(cb), "--pair", "bitstamp", str(bs)]))
    lines = out.splitlines()
    assert code == 0 and lines[4:7] == ["common pinned-coinbase days=1826", "common pinned-bitstamp days=1826",
                                        "common coinbase-bitstamp days=1826"], out
    # each file line names the file by the sha256 its own fetch record holds, and says the record was there
    for line, (provider, path) in zip(lines[2:4], (("coinbase", cb), ("bitstamp", bs))):
        recorded = json.loads((path.parent / "meta.json").read_text(encoding="utf-8"))["csv"]["sha256"]
        assert line == f"file {provider} sha256={recorded} fetch_record=yes", line
        assert recorded == hashlib.sha256(path.read_bytes()).hexdigest()
    assert table(lines, "returns", "coinbase-bitstamp")["total"] == {"days": 1825, "over": 0}      # the same closes
    code, out = base.capture(lambda: bd.run([*argv, "--pair", "bitstamp", str(cb), "--pair", "coinbase", str(bs)]))
    assert code == 2 and "its fetch record names another provider or series" in out, out
    text = cb.read_text(encoding="utf-8").splitlines(keepends=True)
    cb.write_text("".join(text[:-1]), encoding="utf-8")                # one row gone after the fetch
    code, out = base.capture(lambda: bd.run([*argv, "--pair", "coinbase", str(cb), "--pair", "bitstamp", str(bs)]))
    assert code == 2 and out.splitlines()[-2].startswith("REFUSED: btc_coinbase.csv: not the file its fetch record "
                                                         "describes"), out
    assert base.last_line(out) == "BTCDIAG REFUSED exit=2", out


def test_an_error_prints_its_type_only_and_a_failed_self_check_prints_no_data():
    """An unexpected exception can quote a value in its text, so only its type is printed. Before anything is
    printed the script holds its own numbers to the tool's levels_and_returns check of the same pair (the count of
    disagreement days, the days per segment, the decade buckets); when they differ, the run ends ERROR in the
    script's own words and no line of data is printed. The check runs for each pinned pair, so each of its five
    comparisons is broken here for coinbase alone and for bitstamp alone."""
    f = Files(cb=bumped(CB, {"2018-06-05": 0.04}))
    real = pc._common

    def boom(*_a, **_k):
        raise ValueError("close 61234.55 leaked on 2018-06-05")
    pc._common = boom
    try:
        code, lines = f.run()
    finally:
        pc._common = real
    assert (code, lines) == (4, ["ERROR: ValueError", "BTCDIAG ERROR exit=4"]), lines
    real = pc.check_btc_levels
    bitstamp_days = len(read_by_hand(f.bitstamp))
    coinbase_values = np.array(list(read_by_hand(f.coinbase).values()))
    for provider in ("coinbase", "bitstamp"):        # the check runs for each pinned pair: tamper with one at a time
        for change, words in (
                (lambda s: {**s, "n_big_return_diff_days": s["n_big_return_diff_days"] + 1},
                 f"pinned-{provider}: the disagreement days do not sum to the tool's own count"),
                (lambda s: {**s, "late": {**s["late"], "n_days": s["late"]["n_days"] - 1}},
                 f"pinned-{provider}: the late days differ from the tool's own count"),
                (lambda s: {**s, "early": {**s["early"], "n_days": s["early"]["n_days"] + 1}},
                 f"pinned-{provider}: the early days differ from the tool's own count"),
                (lambda s: {**s, "early": {**s["early"], "max_bucket": "<=1e-08"}},
                 f"pinned-{provider}: the early level statistics fall outside the tool's own buckets"),
                (lambda s: {**s, "late": {**s["late"], "p99_bucket": "<=1e-08"}},
                 f"pinned-{provider}: the late level statistics fall outside the tool's own buckets")):
            seen = []

            def other(a, b, change=change, provider=provider, seen=seen):
                check = real(a, b)
                seen.append(len(b.dates))
                # the provider series differ in one planted close, so the pair is known by its values
                if (provider == "coinbase") == bool(np.array_equal(b.values, coinbase_values)):
                    check.summary = change(check.summary)
                return check
            pc.check_btc_levels = other
            try:
                code, lines = f.run()
            finally:
                pc.check_btc_levels = real
            assert (code, lines) == (4, [f"ERROR: {words}", "BTCDIAG ERROR exit=4"]), (provider, lines)
            assert seen and all(n == bitstamp_days == 1826 for n in seen), seen
    code, lines = f.run()
    assert code == 0 and over_by_year(lines, "pinned-coinbase")["total"] == 2, lines


def test_it_reads_through_the_tool_s_readers_and_takes_the_tool_s_thresholds():
    """The dates and the definitions are the tool's: the table, the pinned file and the provider files are read by
    parity_check's read_table, read_pinned and read_provider (each called as compare calls it for BTC-USD), the
    pairs are aligned by its `_common`, and the thresholds are its THRESHOLDS at the time of the run. The script
    has no reader, no alignment and no threshold of its own: it imports no CSV, JSON or data-frame module, opens no
    file but itself (for its sha256), and names no threshold value. It calls no statistic outside the kinds the 3.9
    exception allows (the tool's own scan)."""
    f = Files(cb=bumped(CB, {"2018-06-05": 0.015}))                     # 1.5%: under ret_diff_big, over a smaller one
    calls = []
    saved = {name: getattr(pc, name) for name in ("read_table", "read_pinned", "read_provider", "_common")}

    def spy_on(name):
        def wrapper(*args, **kwargs):
            calls.append((name, args, kwargs))
            return saved[name](*args, **kwargs)
        return wrapper
    for name in saved:
        setattr(pc, name, spy_on(name))
    try:
        code, lines = f.run(extra=["--owner-run"])
    finally:
        for name, fn in saved.items():
            setattr(pc, name, fn)
    assert code == 0 and over_by_year(lines, "pinned-coinbase")["total"] == 0, lines
    # check_btc_levels calls _common once more for each pinned pair (the script's self-check)
    assert [c[0] for c in calls] == ["read_table", "read_pinned", "read_provider", "read_provider"] + ["_common"] * 5
    assert calls[0][1] == (f.w.table, f.w.repo, "btc"), calls[0]
    assert calls[1][2] == {"md5": hashlib.md5(f.pinned.read_bytes()).hexdigest(), "start": WIN[0], "end": WIN[1],
                           "owner_run": True}, calls[1][2]
    for call, (provider, path) in zip(calls[2:4], (("coinbase", f.coinbase), ("bitstamp", f.bitstamp))):
        assert call[1] == (path,) and call[2] == {"provider": provider, "series": "btc", "start": WIN[0],
                                                  "end": WIN[1], "owner_run": True, "window": WIN}, call
    calls.clear()                                                       # without the flag, nothing is let through
    for name in saved:
        setattr(pc, name, spy_on(name))
    try:
        code, lines = f.run()
    finally:
        for name, fn in saved.items():
            setattr(pc, name, fn)
    assert code == 0 and [c[2]["owner_run"] for c in calls[1:4]] == [False, False, False], calls[1:4]
    t = pc.THRESHOLDS["btc"]
    old = (t["ret_diff_big"], t["late_from"], t["level_p99_max"], t["level_max"])
    try:
        t["ret_diff_big"], t["late_from"], t["level_p99_max"], t["level_max"] = 0.01, "2018-01-01", 0.011, 0.0115
        code, lines = f.run()
    finally:
        t["ret_diff_big"], t["late_from"], t["level_p99_max"], t["level_max"] = old
    assert code == 0 and over_by_year(lines, "pinned-coinbase") == {2015: 0, 2016: 0, 2017: 0, 2018: 2, 2019: 0,
                                                                    "total": 2}, lines
    assert lines[1] == ("window start=2015-01-01 end=2019-12-31 late_from=2018-01-01 ret_diff_big=0.01 "
                        "level_p99_max=0.011 level_max=0.0115"), lines[1]
    seg = table(lines, "levels", "pinned-coinbase")
    assert (seg["late"]["days"], seg["early"]["days"]) == (730, 1096), seg
    assert (seg["late"]["over_p99_max"], seg["late"]["over_max"]) == (1, 1), seg
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
        {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert imported == {"__future__", "argparse", "hashlib", "re", "sys", "pathlib", "numpy", "tools"}, imported
    called = {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert not called & {"open", "read_text", "write_text", "write_bytes", "mkdir", "makedirs", "read_csv", "loadtxt",
                         "urlopen", "connect", "system", "Popen", "run_compare", "run_fetch"}, called
    assert source.count("read_bytes") == 1 and "Path(__file__).read_bytes()" in source
    code_only = "\n".join(ast.unparse(n) for n in tree.body[1:])        # the docstring aside
    for literal in ("0.02", "0.015", "0.05", "2017-01-01", "0.005"):
        assert literal not in code_only, literal
    assert pc.forbidden_statistics(source) == [], pc.forbidden_statistics(source)


def test_it_writes_no_file_and_opens_no_socket():
    """The script only reads. Run with every way of opening a file for writing, creating a folder or removing or
    renaming a path recorded, and from an empty working folder: nothing is recorded, the working folder stays empty
    and the files of the fake clone and the provider files are byte for byte and stamp for stamp as they were. Socket
    connects raise for the whole case, as for every case of this suite."""
    f = Files(cb=bumped(CB, {"2018-06-05": 0.04}))
    cwd = base.tmp()

    def snapshot():
        return {str(p): (p.stat().st_size, p.stat().st_mtime_ns, p.is_dir()) for p in sorted(f.w.root.rglob("*"))}
    before = snapshot()
    writes = []
    real_open, real_os_open = io.open, os.open
    names = ("mkdir", "makedirs", "remove", "unlink", "rename", "replace", "rmdir")
    real = {name: getattr(os, name) for name in names}

    def open_recorded(file, mode="r", *args, **kwargs):
        if any(c in str(mode) for c in "wax+"):
            writes.append(("open", str(file), mode))
        return real_open(file, mode, *args, **kwargs)

    def os_open_recorded(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC):
            writes.append(("os.open", str(path), flags))
        return real_os_open(path, flags, *args, **kwargs)

    def recorded(name):
        def wrapper(*args, **kwargs):
            writes.append((name, str(args[0]) if args else ""))
            return real[name](*args, **kwargs)
        return wrapper
    here = os.getcwd()
    os.chdir(cwd)
    io.open = builtins.open = open_recorded
    os.open = os_open_recorded
    for name in names:
        setattr(os, name, recorded(name))
    try:
        code, lines = f.run()
    finally:
        io.open = builtins.open = real_open
        os.open = real_os_open
        for name in names:
            setattr(os, name, real[name])
        os.chdir(here)
    assert code == 0 and lines[-1] == "BTCDIAG OK exit=0" and len(lines) == 44, lines
    assert writes == [], writes
    assert list(cwd.iterdir()) == [] and snapshot() == before
    # the guard of this suite is live: a connect raises
    try:
        import socket
        socket.create_connection(("192.0.2.1", 9), timeout=0.01)
    except AssertionError as exc:
        assert "reached for the network" in str(exc), exc
    else:
        raise AssertionError("a socket connect went through")


def test_it_runs_as_a_module_from_the_clone_root_as_the_owner_runs_it():
    """`python -B -m tools.provider_parity.btc_diagnose ...` from the repository root, with the console encoding
    forced to cp949 (the Korean Windows default for redirected output): the same lines as in the process, exit 0
    and nothing at all on the error stream, because the owner pastes everything the window shows. A refusal says
    its two lines on the output stream and nothing on the error stream; a usage error ends with exit 2 and no
    traceback."""
    f = Files(cb=bumped(CB, {"2018-06-05": 0.04}))
    env = {**os.environ, "PYTHONIOENCODING": "cp949", "PYTHONDONTWRITEBYTECODE": "1"}

    def cli(*args):
        done = subprocess.run([sys.executable, "-B", "-m", "tools.provider_parity.btc_diagnose", *args],
                              cwd=str(ROOT), env=env, capture_output=True, timeout=600)
        return done.returncode, done.stdout.decode("cp949").splitlines(), done.stderr.decode("cp949", errors="replace")
    code, lines, err = cli(*f.argv(), "--owner-run")
    assert (code, lines) == (0, f.run()[1]) and err == "", (lines, err)
    code, lines, err = cli(*f.argv([("coinbase", f.coinbase)]))
    assert code == 2 and len(lines) == 2 and lines[-1] == "BTCDIAG REFUSED exit=2" and err == "", (lines, err)
    code, lines, err = cli("--table", str(f.w.table))
    assert code == 2 and lines == [] and "usage:" in err and "Traceback" not in err, (lines, err)


def test_the_rerun_guide_s_diagnostic_line_runs_as_written_and_prints_what_the_guide_says():
    """The owner pastes step 18 of the rerun guide as it stands, so the line is taken from the guide file and run
    here on the synthetic first sitting of the provider parity suite: the pilot 2 table's own window, the coinbase
    and bitstamp files in their `fetch1-...` folders, each beside a fetch record that names the first fixed
    version's sha256. It prints 84 lines, the number the guide tells the owner to expect and to paste (13 calendar
    years, 2014 to 2026), begins and ends as the guide says, and every line starts with one of the words the guide
    lists. The two `file` lines name the files of the first sitting by the sha256 their fetch records hold. The
    guide's two failure lines are the script's own."""
    line = [b for b in base.guide_blocks(base.RERUN_GUIDE) if "btc_diagnose" in b]
    assert len(line) == 1 and line[0].endswith(" --owner-run"), line
    w = base.RerunWorld()
    code, out = base.capture(lambda: bd.run(w.tool_line(line[0], "btc_diagnose")))
    lines = out.splitlines()
    assert code == 0 and len(lines) == 84 and lines[-1] == "BTCDIAG OK exit=0", out
    assert lines[1].startswith("window start=2014-09-17 end=2026-09-25 late_from=2017-01-01 "), lines[1]
    pp = w.q / "provider_parity"
    recorded = {provider: json.loads((pp / f"fetch1-btc-{provider}" / "meta.json").read_text(encoding="utf-8"))
                for provider in ("coinbase", "bitstamp")}
    assert lines[2:4] == [f"file {provider} sha256={recorded[provider]['csv']['sha256']} fetch_record=yes"
                          for provider in ("coinbase", "bitstamp")], lines[2:4]
    assert lines[4:7] == ["common pinned-coinbase days=4086", "common pinned-bitstamp days=4392",
                          "common coinbase-bitstamp days=4086"], lines[4:7]
    assert all(sum(bool(shape.fullmatch(x)) for shape in ALLOWED) == 1 for x in lines)
    guide = base.RERUN_GUIDE.read_text(encoding="utf-8")
    assert guide.count("84줄") >= 3 and "82줄" not in guide and "13개 연도" in guide, guide.count("84줄")
    for said in ("`BTCDIAG 1 tool_sha256=<64자> script_sha256=<64자>`", "`BTCDIAG OK exit=0`",
                 "`BTCDIAG REFUSED exit=2`", "`BTCDIAG ERROR exit=4`"):
        assert said in guide, said
    kinds = sorted({x.split()[0] for x in lines[1:-1]})
    assert kinds == ["common", "file", "levels", "returns", "split", "venues", "window"], kinds
    assert all(f"`{kind}`" in guide for kind in kinds), kinds
    code, out = base.capture(lambda: bd.run(w.tool_line(line[0].replace("--pair bitstamp", "--pair binance"),
                                                        "btc_diagnose")))
    assert code == 2 and base.last_line(out) == "BTCDIAG REFUSED exit=2", out


def test_every_repository_file_this_suite_reads_starts_the_ci_workflow():
    """CI runs this suite only for a pull request that touches a path on the filter of runtime-smoke.yml, and runs
    it by name. Every repository file the suite reads is on that filter (the script, the tool, the suite whose
    helpers it imports, this file, the workflow and the rerun guide), so none can change without the suite running,
    and the workflow's unittest command names this module."""
    workflow = base.WORKFLOW.read_text(encoding="utf-8")
    paths = re.findall(r"'([^']+)'", re.search(r"^    paths: \[(.*)\]$", workflow, flags=re.M).group(1))
    for path in (SCRIPT, Path(pc.__file__), Path(base.__file__), Path(__file__), base.WORKFLOW, base.RERUN_GUIDE):
        rel = path.resolve().relative_to(ROOT).as_posix()
        assert rel in paths or any(p.endswith("/**") and rel.startswith(p[:-2]) for p in paths), rel
    assert paths.count("tests/provider_parity_btc_diagnose_acceptance.py") == 1, paths
    assert len(re.findall(r"^ +python -m unittest .*\btests\.provider_parity_btc_diagnose_acceptance\b.* -v$",
                          workflow, flags=re.M)) == 1


# --------------------------------------------------------------------------- #
# Collection
# --------------------------------------------------------------------------- #
def _guarded(fn):
    def run():
        try:
            with base.no_network():
                fn()
        finally:
            base._remove_tmp_roots()
    run.__name__ = fn.__name__
    run.__doc__ = fn.__doc__
    return run


def tests():
    return [(n, _guarded(v)) for n, v in sorted(globals().items()) if n.startswith("test_") and callable(v)]


def load_tests(loader, standard_tests, pattern):
    """`python -m unittest tests.provider_parity_btc_diagnose_acceptance`: the same cases, each under the guard."""
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
