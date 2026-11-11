"""Where the BTC-USD provider parity run disagrees: counts per calendar year and two level statistics, read on the
owner's machine and printed to the console.

Owner ruling BTC-나 of 2026-11-11 (results/RULINGS.md): before pilot 2 the cause of the BTC-USD FAIL of the run of
record PP-20261111T075328Z-btc is looked at, and statistics that are not prices may leave the owner's machine through
the chat: per calendar year the number of disagreement days, and the 99th percentile and the maximum of the level
difference. This script prints those and nothing else. It is not a run: it writes no file, makes no network call,
writes no summary and changes no outcome. Run it from the root of the tool clone:

    python -B -m tools.provider_parity.btc_diagnose \
        --table <research clone>/docs/nautilus_bridge/registration/pilot2_C3_btcusd.json --repo <research clone> \
        --pair coinbase <fetch folder>/btc_coinbase.csv --pair bitstamp <fetch folder>/btc_bitstamp.csv --owner-run

It reads the pinned BTC-USD file and the two provider files only through the tool's own readers (parity_check's
read_table, read_pinned and read_provider), aligns them with the tool's `_common` and takes every threshold from the
tool's THRESHOLDS, so the dates and the definitions are those of the run of record. The md5 of the pinned file, the
fetch record of each provider file and the pinned cache guard (--owner-run) are checked by those readers as compare
checks them. It takes the BTC-USD table and the providers coinbase and bitstamp, each once, and refuses anything else.

Words. "pinned" is the md5-pinned yf_BTC-USD.csv. A pair is two series on the days both have. The level difference of
a day is abs(log(P_x / P_y)). A disagreement day is a day whose log-return difference between the two series is above
`ret_diff_big`: the tool's own definition (check_btc_levels), taken over a pair's common days in order. A year is a
calendar year; a return difference belongs to the year of the later of its two days. The late segment starts at
`late_from`, the early segment is the days before it.

Output: these line kinds and no other. Every line is checked against LINE_SHAPES before the first one is printed, and
a refused or failed run prints no line of data.

  kind      what it says                                                    statistic kind (spec 10.5, exception to 3.9)
  BTCDIAG   first line: the sha256 of the tool file and of this file;       identifiers
            last line: OK, REFUSED or ERROR and the exit code
  window    the table's start and end, and the thresholds used              the table's and the tool's own constants
  common    (a) per pair: the number of days both series have               calendar membership
  returns   (b) pinned against each provider, (e) coinbase against          differences between providers: counts
            bitstamp: per year and in total, the days compared and the
            disagreement days; for a pinned pair the total line also
            gives the tool's own count and allowance (`tool_over`,
            `tool_allowed`), which the summary of record states
  levels    (c) pinned against each provider, (e) coinbase against          differences between providers: counts,
            bitstamp: per segment, the days, the 99th percentile and the    percentiles, extreme
            maximum of the level difference in percent with two decimals,
            and the days above `level_p99_max` and above `level_max`
  split     (d) per year and in total, the disagreement days of (b):        differences between providers: counts
            `both` against both providers; `<provider>_only` against that
            provider while the other was compared that day and agreed
            with pinned; `<provider>_unpaired` against that provider on a
            day the other was not compared
  venues    (f) per year and in total, the `both` days of (d): on how       differences between providers: counts
            many coinbase and bitstamp agree with each other within
            `ret_diff_big` (`agree`), differ (`differ`) or were not
            compared with each other (`unpaired`)

(e) involves no pinned data at all. No lag count is printed, no median, and nothing of one series alone.

Never printed: a date finer than a calendar year (the table's start and end and the threshold `late_from` aside), a
price, a return, a difference of one named day. The 99th percentile and the maximum of the level difference are exact
statistics that 10.5.2 keeps out of summary.json; they are printed here by the owner's ruling only, rounded to two
decimals of a percent.

How to read it. If most `both` days are `agree` days in (f), the pinned series stands apart from two venues that
agree with each other. If the disagreement days are mostly `_only` days, or the `both` days are `differ` days, the
venues stand apart from each other. The years in (b) say when; (c) and (e) say how far apart the levels are.

Exit codes: 0 printed, 2 refused, 4 error; the result is the last line `BTCDIAG <OK|REFUSED|ERROR> exit=<n>`.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import numpy as np

from tools.provider_parity import parity_check as pc

NAME = "btc_diagnose.py"
SERIES = "btc"
PROVIDERS = ("coinbase", "bitstamp")
EXIT_OK, EXIT_REFUSED, EXIT_ERROR = 0, pc.EXIT_REFUSED, pc.EXIT_ERROR

_HEX, _DAY, _N, _PCT = r"[0-9a-f]{64}", r"\d{4}-\d{2}-\d{2}", r"\d{1,5}", r"(?:\d{1,3}\.\d{2}|n/a)"
_PAIR = r"(?:pinned-coinbase|pinned-bitstamp|coinbase-bitstamp)"
_PINNED_PAIR = r"(?:pinned-coinbase|pinned-bitstamp)"
_WHEN = r"(?:year=\d{4}|total)"
LINE_SHAPES = tuple(re.compile(shape) for shape in (
    rf"BTCDIAG 1 tool_sha256={_HEX} script_sha256={_HEX}",
    rf"window start={_DAY} end={_DAY} late_from={_DAY} ret_diff_big=0\.\d{{1,4}} level_p99_max=0\.\d{{1,4}} "
    rf"level_max=0\.\d{{1,4}}",
    rf"common {_PAIR} days={_N}",
    rf"returns {_PAIR} year=\d{{4}} days={_N} over={_N}",
    rf"returns {_PINNED_PAIR} total days={_N} over={_N} tool_over={_N} tool_allowed={_N}",
    rf"returns coinbase-bitstamp total days={_N} over={_N}",
    rf"levels {_PAIR} segment=(?:late|early) days={_N} p99_pct={_PCT} max_pct={_PCT} over_p99_max={_N} over_max={_N}",
    rf"split {_WHEN} both={_N} coinbase_only={_N} bitstamp_only={_N} coinbase_unpaired={_N} bitstamp_unpaired={_N}",
    rf"venues {_WHEN} both={_N} agree={_N} differ={_N} unpaired={_N}",
    r"BTCDIAG OK exit=0",
))


class Mismatch(Exception):
    """A count or bucket of this script differs from the tool's own check of the same pair: nothing is printed."""


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _differences(x: pc.Series, y: pc.Series):
    """One pair on the tool's own alignment: the common days, each day's level difference, and for every common day
    but the first whether it is a disagreement day (check_btc_levels' expressions)."""
    days, px, py = pc._common(x, y)
    if len(days) < 2:
        raise pc.Refused("two of the three series have fewer than two days in common")
    level = np.abs(np.log(px / py))
    over = np.abs(np.diff(np.log(px)) - np.diff(np.log(py))) > pc.THRESHOLDS[SERIES]["ret_diff_big"]
    return days, level, dict(zip(days[1:], (bool(o) for o in over)))


def _returns_lines(name: str, over: dict[str, bool], years: list[int], tool: dict | None) -> list[str]:
    lines = []
    for y in years:
        in_year = [o for d, o in over.items() if int(d[:4]) == y]
        lines.append(f"returns {name} year={y} days={len(in_year)} over={sum(in_year)}")
    total = f"returns {name} total days={len(over)} over={sum(over.values())}"
    if tool is not None:
        total += f" tool_over={tool['n_big_return_diff_days']} tool_allowed={tool['n_allowed']}"
    return lines + [total]


def _levels_lines(name: str, days: list[str], level: np.ndarray) -> list[str]:
    t = pc.THRESHOLDS[SERIES]
    late = np.array([d >= t["late_from"] for d in days])
    lines = []
    for segment, mask in (("late", late), ("early", ~late)):
        x = level[mask]
        if x.size:
            p99, mx = f"{100.0 * float(np.percentile(x, 99)):.2f}", f"{100.0 * float(np.max(x)):.2f}"
        else:
            p99 = mx = "n/a"
        lines.append(f"levels {name} segment={segment} days={int(x.size)} p99_pct={p99} max_pct={mx} "
                     f"over_p99_max={int(np.sum(x > t['level_p99_max']))} over_max={int(np.sum(x > t['level_max']))}")
    return lines


def _check_against_tool(name: str, a: pc.Series, b: pc.Series, days: list[str], level: np.ndarray,
                        over: dict[str, bool]) -> dict:
    """The tool's own levels_and_returns check of the same pair. Its count of disagreement days, its days per segment
    and its decade buckets must be this script's, or nothing is printed."""
    tool = pc.check_btc_levels(a, b).summary
    if tool.get("n_big_return_diff_days") != sum(over.values()):
        raise Mismatch(f"{name}: the disagreement days do not sum to the tool's own count")
    late = np.array([d >= pc.THRESHOLDS[SERIES]["late_from"] for d in days])
    for segment, mask in (("late", late), ("early", ~late)):
        x = level[mask]
        if tool[segment]["n_days"] != int(x.size):
            raise Mismatch(f"{name}: the {segment} days differ from the tool's own count")
        if x.size and (pc.bucket(float(np.percentile(x, 99))), pc.bucket(float(np.max(x)))) != \
                (tool[segment]["p99_bucket"], tool[segment]["max_bucket"]):
            raise Mismatch(f"{name}: the {segment} level statistics fall outside the tool's own buckets")
    return tool


def diagnose(a: pc.Series, b: dict[str, pc.Series], *, start: str, end: str) -> list[str]:
    """Every line of data, in order. `a` is the pinned series, `b` the two provider series by name."""
    t = pc.THRESHOLDS[SERIES]
    years = list(range(int(start[:4]), int(end[:4]) + 1))
    lines = [f"BTCDIAG 1 tool_sha256={pc.tool_sha256()} script_sha256={script_sha256()}",
             f"window start={start} end={end} late_from={t['late_from']} ret_diff_big={t['ret_diff_big']!r} "
             f"level_p99_max={t['level_p99_max']!r} level_max={t['level_max']!r}"]
    pinned = {}
    for p in PROVIDERS:
        days, level, over = _differences(a, b[p])
        pinned[p] = (days, level, over, _check_against_tool(f"pinned-{p}", a, b[p], days, level, over))
    v_days, v_level, v_over = _differences(b["coinbase"], b["bitstamp"])
    lines += [f"common pinned-{p} days={len(pinned[p][0])}" for p in PROVIDERS]
    lines.append(f"common coinbase-bitstamp days={len(v_days)}")
    for p in PROVIDERS:                                                             # (b)
        lines += _returns_lines(f"pinned-{p}", pinned[p][2], years, pinned[p][3])
    for p in PROVIDERS:                                                             # (c)
        lines += _levels_lines(f"pinned-{p}", pinned[p][0], pinned[p][1])
    cb, bs = pinned["coinbase"][2], pinned["bitstamp"][2]
    both = sorted(d for d, o in cb.items() if o and bs.get(d) is True)
    for when in [*years, None]:                                                     # (d)
        def n(days) -> int:
            return sum(1 for d in days if when is None or int(d[:4]) == when)
        lines.append(f"split {'total' if when is None else f'year={when}'} both={n(both)} "
                     f"coinbase_only={n(d for d, o in cb.items() if o and bs.get(d) is False)} "
                     f"bitstamp_only={n(d for d, o in bs.items() if o and cb.get(d) is False)} "
                     f"coinbase_unpaired={n(d for d, o in cb.items() if o and d not in bs)} "
                     f"bitstamp_unpaired={n(d for d, o in bs.items() if o and d not in cb)}")
    lines += _returns_lines("coinbase-bitstamp", v_over, years, None)               # (e)
    lines += _levels_lines("coinbase-bitstamp", v_days, v_level)
    for when in [*years, None]:                                                     # (f)
        days = [d for d in both if when is None or int(d[:4]) == when]
        lines.append(f"venues {'total' if when is None else f'year={when}'} both={len(days)} "
                     f"agree={sum(1 for d in days if v_over.get(d) is False)} "
                     f"differ={sum(1 for d in days if v_over.get(d) is True)} "
                     f"unpaired={sum(1 for d in days if d not in v_over)}")
    return lines + ["BTCDIAG OK exit=0"]


def assert_lines_safe(lines: list[str]) -> None:
    """The output as an allow-list: every line has one of LINE_SHAPES, or nothing is printed."""
    for k, line in enumerate(lines):
        if not any(shape.fullmatch(line) for shape in LINE_SHAPES):
            raise Mismatch(f"line {k + 1} has a shape outside the allow-list")


def _read(args) -> tuple[pc.Series, dict[str, pc.Series], dict]:
    named = [p for p, _ in args.pair]
    if sorted(named) != sorted(PROVIDERS):
        raise pc.Refused(f"--pair takes {' and '.join(PROVIDERS)}, each once, and no other provider")
    tab = pc.read_table(args.table, args.repo, SERIES)
    a = pc.read_pinned(tab["path"], md5=tab["md5"], start=tab["start"], end=tab["end"], owner_run=args.owner_run)
    b = {}
    for provider, path in args.pair:
        b[provider], _, _ = pc.read_provider(Path(path), provider=provider, series=SERIES, start=tab["start"],
                                             end=tab["end"], owner_run=args.owner_run,
                                             window=(tab["start"], tab["end"]))
    return a, b, tab


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -B -m tools.provider_parity.btc_diagnose",
                                 description="Where the BTC-USD provider parity run disagrees (owner ruling BTC-나).")
    ap.add_argument("--table", type=Path, required=True, help="the pilot 2 table, inside --repo")
    ap.add_argument("--repo", type=Path, required=True, help="the research clone's root (read only)")
    ap.add_argument("--pair", nargs=2, action="append", default=[], metavar=("PROVIDER", "FILE"),
                    help="coinbase and bitstamp, each once")
    ap.add_argument("--owner-run", action="store_true", help="only on the owner's machine: read the pinned cache file")
    return ap


def run(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    say = pc._Say()
    try:
        a, b, tab = _read(args)
        lines = diagnose(a, b, start=tab["start"], end=tab["end"])
        assert_lines_safe(lines)
    except pc.Refused as exc:
        say(f"REFUSED: {exc}")
        say(f"BTCDIAG REFUSED exit={EXIT_REFUSED}")
        return EXIT_REFUSED
    except Mismatch as exc:                   # the message is this script's own words and names no value
        say(f"ERROR: {exc}")
        say(f"BTCDIAG ERROR exit={EXIT_ERROR}")
        return EXIT_ERROR
    except Exception as exc:                  # the text can quote a value, so only the type
        say(f"ERROR: {type(exc).__name__}")
        say(f"BTCDIAG ERROR exit={EXIT_ERROR}")
        return EXIT_ERROR
    for line in lines:
        say(line)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(run())
