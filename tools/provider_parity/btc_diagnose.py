"""Where the BTC-USD provider parity run disagrees: counts per calendar year and two level statistics, read on the
owner's machine and printed to the console.

Owner ruling BTC-나 of 2026-11-11 (results/RULINGS.md): before pilot 2 the cause of the BTC-USD FAIL of the run of
record PP-20261111T075328Z-btc is looked at, and statistics that are not prices may leave the owner's machine through
the chat. The option put to the owner named two kinds: per calendar year the number of disagreement days, and the
99th percentile and the maximum of the level difference. This script prints those two and, beside them, the counts
and identifiers listed under "Output" below; which lines go beyond the two named kinds is said there and in
results/RULINGS.md, as Claude's reading of the ruling. It is not a run: it makes no network call, writes no summary
and changes no outcome, and run with -B, as below, it writes no file (without -B Python itself leaves `__pycache__`
folders in the tool clone). Run it from the root of the tool clone:

    python -B -m tools.provider_parity.btc_diagnose \
        --table <research clone>/docs/nautilus_bridge/registration/pilot2_C3_btcusd.json --repo <research clone> \
        --pair coinbase <fetch folder>/btc_coinbase.csv --pair bitstamp <fetch folder>/btc_bitstamp.csv --owner-run

What it reads. The option's words were "from the detail file left on the PC". `detail.json` cannot give the yearly
counts: for this check it keeps the 100 largest level differences of a pair and no return difference. So the script
reads the same three files compare read, the pinned BTC-USD file and the two provider files, and computes again. It
reads them only through the tool's own readers (parity_check's read_table, read_pinned and read_provider), aligns
them with the tool's `_common` and takes every threshold from the tool's THRESHOLDS, so the dates and the definitions
are those of the run of record. The md5 of the pinned file, the fetch record of each provider file and the pinned
cache guard (--owner-run) are checked by those readers as compare checks them. It takes the BTC-USD table and the
providers coinbase and bitstamp, each once, and refuses anything else. It opens no `detail.json`.

Words. "pinned" is the md5-pinned yf_BTC-USD.csv. A pair is two series on the days both have. The level difference of
a day is abs(log(P_x / P_y)). A disagreement day is a day whose log-return difference between the two series is above
`ret_diff_big`: the tool's own definition (check_btc_levels), taken over a pair's common days in order. A year is a
calendar year; a return difference belongs to the year of the later of its two days. The late segment starts at
`late_from`, the early segment is the days before it.

Output: these line kinds and no other. Every line is checked against LINE_SHAPES before the first one is printed, and
a refused or failed run prints no line of data. The last column says whether the owner's option named the kind.

  kind      what it says                                                    named in the option
  BTCDIAG   first line: the sha256 of the tool file and of this file;       no: identifiers
            last line: OK, REFUSED or ERROR and the exit code
  window    the table's start and end, and the thresholds used              no: the table's and the tool's constants,
                                                                            all in the pushed summary
  file      per provider file: its sha256 and whether its fetch record      no: identifiers; the summary of record
            lay beside it                                                   states both, so the files can be matched
  common    (a) per pair: the number of days both series have               no: counts (for the pinned pairs the
                                                                            summary of record states them)
  returns   (b) pinned against each provider, (e) coinbase against          `over` of (b) is the first named kind;
            bitstamp: per year and in total, the days compared (`days`)     `days`, the totals and all of (e) are not
            and the disagreement days (`over`); for a pinned pair the       named (`tool_over` and `tool_allowed` are
            total line also gives the tool's own count and allowance        in the summary of record)
  levels    (c) pinned against each provider, (e) coinbase against          `p99_pct` and `max_pct` of (c) are the
            bitstamp: per segment, the days, the 99th percentile and the    second named kind; `days`, the counts
            maximum of the level difference in percent with one decimal,    above a threshold and all of (e) are not
            and the days above `level_p99_max` and above `level_max`; for   named
            a pinned pair also, of those days, the days on which that
            provider alone is apart (`only_p99_max`, `only_max`): pinned
            and the other provider are within the threshold of each
            other, and the two providers are more than it apart
  split     (d) per year and in total, the disagreement days of (b),        no: a breakdown of the named counts
            each in one group: `both` against both providers;
            `<provider>_only` against that provider alone while the two
            venues differ from each other (that provider is the odd one);
            `<provider>_edge` against that provider alone while the two
            venues agree with each other (no series is clearly the odd
            one: pinned is over the threshold from one venue and under it
            from the other); `<provider>_unpaired` when the other
            provider, or the two venues with each other, have no return
            over the same two days
  venues    (f) per year and in total, the `both` days of (d): on how       no: counts
            many coinbase and bitstamp agree with each other within
            `ret_diff_big` (`agree`), differ (`differ`) or have no return
            with each other over the same two days (`unpaired`)

Kinds, in the words of the exception to 3.9 (spec 10.5): calendar membership (common), and differences between two
providers' series as counts, percentiles and an extreme (returns, levels, split, venues). (e) involves no pinned data
at all. No lag count is printed, no median, and nothing of one series alone. That exception names the tool; this
script is a second file beside it and prints by the owner's ruling, not by the spec.

Limits of the level lines. `max_pct` is the level difference of one single day; its date is not printed. Because
the two venues' closes are public, someone who found that day could work the pinned close of that day back from
`max_pct` to about the rounding of one decimal. `p99_pct` and `max_pct` are printed as `n/a` for a segment of fewer
than MIN_SEGMENT_DAYS days, where they would be the figures of a few days. The two counts above a threshold use
`level_p99_max` and `level_max` in both segments; the tool's own early band is wider (`early_level_p99_max`,
`early_level_max`), so the early counts are not the tool's early check.

Never printed by a run that ends OK: a date finer than a calendar year (the table's start and end and the threshold
`late_from` aside), a price, a return, a difference of a day whose date is given. The 99th percentile and the maximum
of the level difference are statistics that 10.5.2 keeps out of summary.json; they are printed here by the owner's
ruling only, rounded to one decimal of a percent. A REFUSED line is the tool's own message and can name a folder
path, an md5 or the window of a fetch record; it carries no price and no date of the data.

How to read it. The lines say which series stands apart, in which years and by how much; they do not say why. `both`
days that are `agree` days: the pinned series stands apart from two venues that agree with each other. `_only` days,
in (d) and in (c): pinned agrees with the other venue and that provider is the odd one. `differ` days: all three
stand apart. `_edge` days decide nothing: a day can fall just over the threshold against one venue and just under
it against the other. The rule Claude applies to the output, written before any output was seen, is in
results/RULINGS.md.

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
MIN_SEGMENT_DAYS = 100     # a segment with fewer days prints n/a for its percentile and its maximum

_HEX, _DAY, _N, _PCT = r"[0-9a-f]{64}", r"\d{4}-\d{2}-\d{2}", r"\d{1,5}", r"(?:\d{1,3}\.\d|n/a)"
_PAIR = r"(?:pinned-coinbase|pinned-bitstamp|coinbase-bitstamp)"
_PINNED_PAIR = r"(?:pinned-coinbase|pinned-bitstamp)"
_WHEN = r"(?:year=\d{4}|total)"
LINE_SHAPES = tuple(re.compile(shape) for shape in (
    rf"BTCDIAG 1 tool_sha256={_HEX} script_sha256={_HEX}",
    rf"window start={_DAY} end={_DAY} late_from={_DAY} ret_diff_big=0\.\d{{1,4}} level_p99_max=0\.\d{{1,4}} "
    rf"level_max=0\.\d{{1,4}}",
    rf"file (?:coinbase|bitstamp) sha256={_HEX} fetch_record=(?:yes|no)",
    rf"common {_PAIR} days={_N}",
    rf"returns {_PAIR} year=\d{{4}} days={_N} over={_N}",
    rf"returns {_PINNED_PAIR} total days={_N} over={_N} tool_over={_N} tool_allowed={_N}",
    rf"returns coinbase-bitstamp total days={_N} over={_N}",
    rf"levels {_PINNED_PAIR} segment=(?:late|early) days={_N} p99_pct={_PCT} max_pct={_PCT} over_p99_max={_N} "
    rf"over_max={_N} only_p99_max={_N} only_max={_N}",
    rf"levels coinbase-bitstamp segment=(?:late|early) days={_N} p99_pct={_PCT} max_pct={_PCT} over_p99_max={_N} "
    rf"over_max={_N}",
    rf"split {_WHEN} both={_N} coinbase_only={_N} bitstamp_only={_N} coinbase_edge={_N} bitstamp_edge={_N} "
    rf"coinbase_unpaired={_N} bitstamp_unpaired={_N}",
    rf"venues {_WHEN} both={_N} agree={_N} differ={_N} unpaired={_N}",
    r"BTCDIAG OK exit=0",
))


class Mismatch(Exception):
    """A count or bucket of this script differs from the tool's own check of the same pair: nothing is printed."""


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _differences(x: pc.Series, y: pc.Series):
    """One pair on the tool's own alignment: the common days, each day's level difference, for every common day but
    the first whether it is a disagreement day (check_btc_levels' expressions), and the common day before it, from
    which its return is taken."""
    days, px, py = pc._common(x, y)
    if len(days) < 2:
        raise pc.Refused("two of the three series have fewer than two days in common")
    level = np.abs(np.log(px / py))
    over = np.abs(np.diff(np.log(px)) - np.diff(np.log(py))) > pc.THRESHOLDS[SERIES]["ret_diff_big"]
    return days, level, dict(zip(days[1:], (bool(o) for o in over))), dict(zip(days[1:], days))


def _returns_lines(name: str, over: dict[str, bool], years: list[int], tool: dict | None) -> list[str]:
    lines = []
    for y in years:
        in_year = [o for d, o in over.items() if int(d[:4]) == y]
        lines.append(f"returns {name} year={y} days={len(in_year)} over={sum(in_year)}")
    total = f"returns {name} total days={len(over)} over={sum(over.values())}"
    if tool is not None:
        total += f" tool_over={tool['n_big_return_diff_days']} tool_allowed={tool['n_allowed']}"
    return lines + [total]


def _levels_lines(name: str, days: list[str], level: np.ndarray,
                  others: tuple[dict[str, float], dict[str, float]] | None = None) -> list[str]:
    """The level lines of one pair. For a pinned pair `others` is, by day, the level difference of pinned against
    the other provider and of the two providers against each other: a day above a threshold counts as `only` when
    the first is within that threshold and the second above it, so that this provider alone is apart."""
    t = pc.THRESHOLDS[SERIES]
    late = np.array([d >= t["late_from"] for d in days])
    lines = []
    for segment, mask in (("late", late), ("early", ~late)):
        x = level[mask]
        if x.size >= MIN_SEGMENT_DAYS:
            p99, mx = f"{100.0 * float(np.percentile(x, 99)):.1f}", f"{100.0 * float(np.max(x)):.1f}"
        else:
            p99 = mx = "n/a"
        line = (f"levels {name} segment={segment} days={int(x.size)} p99_pct={p99} max_pct={mx} "
                f"over_p99_max={int(np.sum(x > t['level_p99_max']))} over_max={int(np.sum(x > t['level_max']))}")
        if others is not None:
            pinned_other, venues = others
            for key in ("level_p99_max", "level_max"):
                alone = sum(1 for d, v, m in zip(days, level, mask)
                            if m and v > t[key] and d in pinned_other and pinned_other[d] <= t[key]
                            and d in venues and venues[d] > t[key])
                line += f" only_{key[len('level_'):]}={alone}"
        lines.append(line)
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


def diagnose(a: pc.Series, b: dict[str, pc.Series], *, start: str, end: str,
             files: dict[str, tuple[str, bool]]) -> list[str]:
    """Every line of data, in order. `a` is the pinned series, `b` the two provider series by name, `files` each
    provider file's sha256 and whether its fetch record lay beside it."""
    t = pc.THRESHOLDS[SERIES]
    years = list(range(int(start[:4]), int(end[:4]) + 1))
    lines = [f"BTCDIAG 1 tool_sha256={pc.tool_sha256()} script_sha256={script_sha256()}",
             f"window start={start} end={end} late_from={t['late_from']} ret_diff_big={t['ret_diff_big']!r} "
             f"level_p99_max={t['level_p99_max']!r} level_max={t['level_max']!r}"]
    lines += [f"file {p} sha256={files[p][0]} fetch_record={'yes' if files[p][1] else 'no'}" for p in PROVIDERS]
    pinned = {}
    for p in PROVIDERS:
        days, level, over, before = _differences(a, b[p])
        pinned[p] = (days, level, over, _check_against_tool(f"pinned-{p}", a, b[p], days, level, over), before)
    v_days, v_level, v_over, v_before = _differences(b["coinbase"], b["bitstamp"])
    lines += [f"common pinned-{p} days={len(pinned[p][0])}" for p in PROVIDERS]
    lines.append(f"common coinbase-bitstamp days={len(v_days)}")
    for p in PROVIDERS:                                                             # (b)
        lines += _returns_lines(f"pinned-{p}", pinned[p][2], years, pinned[p][3])
    by_day = {p: dict(zip(pinned[p][0], (float(v) for v in pinned[p][1]))) for p in PROVIDERS}
    venues_by_day = dict(zip(v_days, (float(v) for v in v_level)))
    for p, other in (PROVIDERS, PROVIDERS[::-1]):                                   # (c)
        lines += _levels_lines(f"pinned-{p}", pinned[p][0], pinned[p][1], (by_day[other], venues_by_day))
    cb, bs = pinned["coinbase"][2], pinned["bitstamp"][2]
    cb_before, bs_before = pinned["coinbase"][4], pinned["bitstamp"][4]
    # a day is paired when both providers have a return against pinned over the same two days, and the venues have a
    # return with each other over those two days when they share the day before as well
    paired = {d for d in cb if d in bs and cb_before[d] == bs_before[d]}
    venues_too = {d for d in paired if v_before.get(d) == cb_before[d]}
    both = sorted(d for d in paired if cb[d] and bs[d])
    group = {}                                   # (provider, day) -> the one group of a day against that provider alone
    for name, mine, other in (("coinbase", cb, bs), ("bitstamp", bs, cb)):
        for d, flagged in mine.items():
            if flagged and not (d in paired and other[d]):
                group[name, d] = "unpaired" if d not in venues_too else "only" if v_over[d] else "edge"
    for when in [*years, None]:                                                     # (d)
        def n(days) -> int:
            return sum(1 for d in days if when is None or int(d[:4]) == when)

        def alone(name: str, kind: str) -> int:
            return n(d for (who, d), k in group.items() if who == name and k == kind)
        lines.append(f"split {'total' if when is None else f'year={when}'} both={n(both)} "
                     f"coinbase_only={alone('coinbase', 'only')} bitstamp_only={alone('bitstamp', 'only')} "
                     f"coinbase_edge={alone('coinbase', 'edge')} bitstamp_edge={alone('bitstamp', 'edge')} "
                     f"coinbase_unpaired={alone('coinbase', 'unpaired')} "
                     f"bitstamp_unpaired={alone('bitstamp', 'unpaired')}")
    lines += _returns_lines("coinbase-bitstamp", v_over, years, None)               # (e)
    lines += _levels_lines("coinbase-bitstamp", v_days, v_level)
    for when in [*years, None]:                                                     # (f)
        days = [d for d in both if when is None or int(d[:4]) == when]
        lines.append(f"venues {'total' if when is None else f'year={when}'} both={len(days)} "
                     f"agree={sum(1 for d in days if d in venues_too and not v_over[d])} "
                     f"differ={sum(1 for d in days if d in venues_too and v_over[d])} "
                     f"unpaired={sum(1 for d in days if d not in venues_too)}")
    return lines + ["BTCDIAG OK exit=0"]


def assert_lines_safe(lines: list[str]) -> None:
    """The output as an allow-list: every line has one of LINE_SHAPES, or nothing is printed."""
    for k, line in enumerate(lines):
        if not any(shape.fullmatch(line) for shape in LINE_SHAPES):
            raise Mismatch(f"line {k + 1} has a shape outside the allow-list")


def _read(args) -> tuple[pc.Series, dict[str, pc.Series], dict, dict[str, tuple[str, bool]]]:
    named = [p for p, _ in args.pair]
    if sorted(named) != sorted(PROVIDERS):
        raise pc.Refused(f"--pair takes {' and '.join(PROVIDERS)}, each once, and no other provider")
    tab = pc.read_table(args.table, args.repo, SERIES)
    a = pc.read_pinned(tab["path"], md5=tab["md5"], start=tab["start"], end=tab["end"], owner_run=args.owner_run)
    b, files = {}, {}
    for provider, path in args.pair:
        b[provider], sha, has_record = pc.read_provider(Path(path), provider=provider, series=SERIES,
                                                        start=tab["start"], end=tab["end"],
                                                        owner_run=args.owner_run, window=(tab["start"], tab["end"]))
        files[provider] = (sha, has_record)
    return a, b, tab, files


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
        a, b, tab, files = _read(args)
        lines = diagnose(a, b, start=tab["start"], end=tab["end"], files=files)
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
