"""Build the proposed release_calendar v1.0.0 (audit report docs/audit/2026-10-27/12_release_calendar.md).

BLS/BEA plan A stage 1, approved by the owner (docs/audit/2026-10-27/11_bls_bea_stage1_status.md): one row per
(release, reference period) whose release date falls in 2025-01-01..2027-12-31, for CPI, EMPSIT (BLS), PIO (BEA
Personal Income and Outlays) and CLAIMS (DOL Unemployment Insurance Weekly Claims).

Inputs, both under sources/:
  official_schedules.yaml   the BLS, BEA and FRED schedule pages the owner saved on 2026-10-28, transcribed
  alfred_first_release.csv  first ALFRED vintage per observation (extract_alfred.py over the owner's downloads)
  alfred_vintages.csv       every ALFRED vintage date of the four series
and the owner-signed holidays_FED file (CLAIMS holiday rule).

Every date that two records cover must agree, or the build stops. Evidence: A = two records agree (ALFRED's first
vintage and an official schedule, or two BLS schedule pages); B = one official record; C = derived from the
weekly rule because no official 2027 claims dates exist yet. Nothing under core/calendars/data/ is written and no
signature is set.

    python docs/audit/2026-10-27/calendar_batch5/build_proposed.py
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DATA = REPO / "core" / "calendars" / "data"
SRC = HERE / "sources"
OUT = HERE / "proposed"
REPORT = "docs/audit/2026-10-27/12_release_calendar.md"
VERSION = "1.0.0"
LO, HI = date(2025, 1, 1), date(2027, 12, 31)
NY = "America/New_York"
SERIES = {"CPI": "CPIAUCSL", "EMPSIT": "PAYEMS", "PIO": "PCEPI", "CLAIMS": "ICSA"}
TODAY = date(2026, 10, 28)                       # audit date: releases after it have no ALFRED vintage yet

D = lambda s: date.fromisoformat(s)             # noqa: E731


class Mismatch(Exception):
    pass


def load_sources():
    sched = yaml.safe_load((SRC / "official_schedules.yaml").read_text(encoding="utf-8"))
    first = defaultdict(dict)
    with (SRC / "alfred_first_release.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            first[r["series_id"]][r["period"]] = (r["first_realtime_start"], r["has_value"] == "True")
    vint = defaultdict(set)
    with (SRC / "alfred_vintages.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            vint[r["series_id"]].add(r["vintage_date"])
    fed = yaml.safe_load((DATA / "holidays_FED.yaml").read_text(encoding="utf-8"))
    assert fed.get("signed_off_by"), "holidays_FED must be owner-signed"
    fed_closed = {r["date"] for r in fed["rows"] if r.get("kind") == "closed"}
    return sched, first, vint, fed_closed


class Claims:
    """period -> {source: (release_date, time)} for one release; every source of a period must agree."""

    def __init__(self, release: str):
        self.release, self.by = release, defaultdict(dict)

    def add(self, period: str, source: str, day: str, time: str = "08:30") -> None:
        self.by[period][source] = (day, time)

    def settle(self) -> dict[str, tuple[str, str, list[str]]]:
        out = {}
        for period, srcs in sorted(self.by.items()):
            values = set(srcs.values())
            if len({v[0] for v in values}) != 1:
                raise Mismatch(f"{self.release} {period}: sources disagree {srcs}")
            day = next(iter(values))[0]
            times = {v[1] for k, v in srcs.items() if k != "ALFRED"} or {"08:30"}
            if len(times) != 1:
                raise Mismatch(f"{self.release} {period}: times disagree {srcs}")
            out[period] = (day, times.pop(), sorted(srcs))
        return out


def monthly_alfred(c: Claims, first: dict, series: str, log: list[str]) -> None:
    for period, (day, has_value) in first[series].items():
        if not has_value:
            log.append(f"{c.release} {period}: ALFRED's first vintage {day} has no value (cancelled release): no row")
            continue
        c.add(period, "ALFRED", day)


def build_cpi(sched, first, log) -> Claims:
    c = Claims("CPI")
    monthly_alfred(c, first, "CPIAUCSL", log)
    for period, v in sched["BLS_LAPSE"]["CPI"].items():
        if v["revised"] is None:
            assert first["CPIAUCSL"][period][1] is False, period    # ALFRED agrees: no value
            continue
        c.add(period, "BLS_LAPSE", v["revised"])
    for period, day in sched["BLS_CPI"].items():
        c.add(period, "BLS_CPI", day)
    for period, day in sched["BLS_2027"]["CPI"].items():
        c.add(period, "BLS_2027", day)
    return c


def build_empsit(sched, first, log) -> Claims:
    c = Claims("EMPSIT")
    monthly_alfred(c, first, "PAYEMS", log)
    lapse = sched["BLS_LAPSE"]["EMPSIT"]
    for period, v in lapse.items():
        if v["revised"] is None:     # October 2025: no release of its own; establishment data came with November
            nxt = lapse[(D(period).replace(day=28) + timedelta(days=4)).replace(day=1).isoformat()]["revised"]
            c.add(period, "BLS_LAPSE", nxt)
            log.append(f"EMPSIT {period}: no release of its own; establishment data published with the next month "
                       f"on {nxt} (household survey not collected: UNRATE registry missing_months)")
            continue
        c.add(period, "BLS_LAPSE", v["revised"])
    for period, day in sched["BLS_EMPSIT"].items():
        c.add(period, "BLS_EMPSIT", day)
    for period, day in sched["BLS_2027"]["EMPSIT"].items():
        c.add(period, "BLS_2027", day)
    return c


def build_pio(sched, first, log) -> Claims:
    c = Claims("PIO")
    monthly_alfred(c, first, "PCEPI", log)
    for key in ("BEA_2025", "BEA_2026", "BEA_2027"):
        for period, (day, time) in sched[key].items():
            c.add(period, key, day, time)
    return c


def claims_rule(period: date, fed_closed: set[str]) -> date:
    """DOL weekly claims: Thursday 08:30 ET after the week ending Saturday `period`; Wednesday when that Thursday is
    a federal holiday."""
    thu = period + timedelta(days=5)
    return thu - timedelta(days=1) if thu.isoformat() in fed_closed else thu


def build_claims(sched, first, vint, fed_closed, log) -> Claims:
    c = Claims("CLAIMS")
    for period, (day, has_value) in first["ICSA"].items():
        assert has_value
        c.add(period, "ALFRED", day)
    fred = sorted(D(x) for x in sched["FRED_CLAIMS_2025"] + sched["FRED_CLAIMS_2026"])
    assert len(sched["FRED_CLAIMS_2025"]) == 46 and len(sched["FRED_CLAIMS_2026"]) == 52      # "of 46", "of 52"
    assert all(d.weekday() in (2, 3) for d in fred), "claims are released on Thursday, or Wednesday"
    # every FRED date up to the audit date carries an ALFRED vintage, and vice versa within 2025-2026
    past = {d.isoformat() for d in fred if d <= TODAY}
    v = {x for x in vint["ICSA"] if "2025-01-01" <= x <= TODAY.isoformat()}
    if past != v:
        raise Mismatch(f"CLAIMS: FRED calendar vs ALFRED vintages differ: {sorted(past ^ v)}")
    log.append(f"CLAIMS: {len(past)} FRED release dates up to {TODAY} == ALFRED ICSA vintage dates")
    alfred_last = max(D(p) for p in first["ICSA"])
    period = date(2024, 12, 28)
    rule_hits, rule_miss = 0, []
    while True:
        rel = next((d for d in fred if d > period), None)
        if rel is None:
            break
        p = period.isoformat()
        src = "FRED_CLAIMS_2025" if rel.year == 2025 else "FRED_CLAIMS_2026"
        c.add(p, src, rel.isoformat())
        if period > alfred_last and rel.isoformat() in vint["ICSA"]:
            c.add(p, "ALFRED_VINTAGE", rel.isoformat())             # a vintage on that Thursday: released then
        expect = claims_rule(period, fed_closed)
        if expect == rel:
            rule_hits += 1
        else:
            rule_miss.append(f"{p}: rule {expect} vs {rel}")
        period += timedelta(days=7)
    log.append(f"CLAIMS rule (Thursday; Wednesday when the Thursday is a FED holiday) reproduces {rule_hits} of "
               f"{rule_hits + len(rule_miss)} official 2025-2026 dates; the others are the 2025 shutdown:")
    log += [f"  {m}" for m in rule_miss]
    assert all("2025-11-20" in m for m in rule_miss), rule_miss
    while True:                                                  # 2027: no official dates yet (FRED: none)
        rel = claims_rule(period, fed_closed)
        if rel > HI:
            break
        c.add(period.isoformat(), "RULE_2027", rel.isoformat())
        period += timedelta(days=7)
    return c


def evidence(release: str, srcs: list[str], day: str, time: str) -> tuple[str, str]:
    names = {"ALFRED": "ALFRED first vintage", "ALFRED_VINTAGE": "an ALFRED vintage on that date",
             "BLS_LAPSE": "BLS lapse revised-dates page", "BLS_CPI": "BLS CPI schedule",
             "BLS_EMPSIT": "BLS Employment Situation schedule", "BLS_2027": "BLS 2027 release calendar",
             "BEA_2025": "BEA 2025 schedule", "BEA_2026": "BEA 2026 schedule", "BEA_2027": "BEA 2027 schedule",
             "FRED_CLAIMS_2025": "FRED claims calendar 2025", "FRED_CLAIMS_2026": "FRED claims calendar 2026",
             "RULE_2027": "weekly rule over the signed holidays_FED"}
    listed = " and ".join(names[s] for s in srcs)
    if srcs == ["RULE_2027"]:
        thu = D(day).weekday() == 3
        return "C", ("C: no official 2027 claims dates yet (FRED: none on 2026-10-28); Thursday 08:30 ET after the "
                     "week" + ("" if thu else "; Wednesday because the Thursday is a federal holiday") +
                     "; replace with the DOL dates when published")
    grade = "A" if len(srcs) >= 2 else "B"
    note = "agree" if len(srcs) >= 2 else "only (one official record)"
    t = "" if time == "08:30" else f"; {time} ET per BEA (not 08:30)"
    return grade, f"{grade}: {listed} {note}{t}"


def rows_for(release: str, settled: dict, sched: dict) -> list[dict]:
    docs = sched["documents"]
    out = []
    for period, (day, time, srcs) in settled.items():
        if not (LO <= D(day) <= HI):
            continue
        keys = [s for s in srcs if s not in ("ALFRED_VINTAGE", "RULE_2027")]
        keys = ["ALFRED" if s == "ALFRED" else s for s in keys]
        if "ALFRED_VINTAGE" in srcs:
            keys.append("ALFRED")
        urls = []
        for k in keys:
            u = docs[k]["url"]
            if k == "ALFRED":
                u = f"https://alfred.stlouisfed.org/series?seid={SERIES[release]}"
            if u not in urls:
                urls.append(u)
        if "RULE_2027" in srcs:
            urls = [docs["FRED_CLAIMS_2027"]["url"], "rule: Thursday after the week, Wednesday when that Thursday "
                    "is closed in holidays_FED v1.0.0 (owner-signed)"]
        retrieved = max(docs[k]["retrieved_at_utc"] for k in (keys or ["FRED_CLAIMS_2027"]))
        grade, ev = evidence(release, srcs, day, time)
        out.append({"effective_from": day, "effective_to": day, "source_url": "; ".join(urls),
                    "retrieved_at_utc": retrieved, "signed_off_by": None, "release": release, "period": period,
                    "release_date": day, "time": time, "tz": NY, "evidence": ev})
    return out


def envelope(rows: list[dict]) -> dict:
    return {
        "file_id": "release_calendar",
        "version": VERSION,
        "status": (f"AUDITED, UNSIGNED - proposed v{VERSION} ({REPORT}); refused at load until the owner signs "
                   "(R-20 rule 6, T-CAL-01)"),
        "covers": {"from": LO.isoformat(), "to": HI.isoformat()},
        "coverage_calendar": "FED",
        "signed_off_by": None,
        "signed_utc": None,
        "md5": None,
        "description": ("BLS, BEA and DOL release dates (spec L1448, L1851): one row per release and reference "
                        "period whose release date falls in the covered range. period = the FRED observation date "
                        "(first of the month; the week-ending Saturday for CLAIMS); release_date and time are local "
                        "America/New_York. A period without a row has no release date and stays unpublished "
                        "(October 2025 CPI was cancelled). Releases: CPI -> CPIAUCSL, CPILFESL; EMPSIT -> UNRATE, "
                        "PAYEMS, SAHMREALTIME; PIO -> PCEPI, PCEPILFE; CLAIMS -> ICSA."),
        "how_to_sign": ("verify every row against its official source, then run `python -m tools.sign_calendars "
                        "--signer \"<name>\" --expect release_calendar=<md5> release_calendar` after the file is "
                        "copied in and its MANIFEST.yaml row added"),
        "unverified": [
            "CLAIMS 2027 (52 rows, evidence C): FRED listed no 2027 claims dates on 2026-10-28; the rows follow the "
            "rule that reproduces every 2025-2026 date outside the 2025 shutdown (Thursday; Wednesday when the "
            "Thursday is a federal holiday: 2027-11-10 Veterans Day, 2027-11-24 Thanksgiving); a new version "
            "replaces them once DOL publishes",
            "evidence B rows (one official record): future dates on a single schedule page (BLS November-December "
            "2026, BEA from 2026-10-29, FRED claims from 2026-10-29) and 2025 BLS dates before the shutdown, which "
            "rest on ALFRED alone; a rescheduled or cancelled release is a release event (M5) until a new version",
            "CPI September 2025 -> 2025-10-24: ALFRED's first vintage; the 08:30 ET time is BLS's standard time, "
            "not printed on the saved pages",
            "1995-2024 release dates are stage 2 (separate approval): those observations stay unpublished",
        ],
        "owner_must_sign": [
            "BLS, BEA and DOL release dates per release and reference period (spec L1448), with the time of day "
            "(four BEA releases were at 10:00 ET)",
        ],
        "rows": rows,
    }


def main() -> int:
    sched, first, vint, fed_closed = load_sources()
    log: list[str] = []
    holidays_2027 = set(sched["BLS_2027"]["holidays"])
    fed_2027 = {d for d in fed_closed if d.startswith("2027-")}
    if holidays_2027 != fed_2027:
        raise Mismatch(f"BLS 2027 holidays vs signed holidays_FED 2027: {sorted(holidays_2027 ^ fed_2027)}")
    log.append(f"BLS 2027 calendar holidays == signed holidays_FED 2027 closed dates ({len(fed_2027)})")
    builders = (build_cpi(sched, first, log), build_empsit(sched, first, log), build_pio(sched, first, log),
                build_claims(sched, first, vint, fed_closed, log))
    rows: list[dict] = []
    for c in builders:
        settled = c.settle()
        rel_rows = rows_for(c.release, settled, sched)
        grades = Counter(r["evidence"][0] for r in rel_rows)
        twice = sum(1 for _, (_, _, s) in settled.items() if len(s) >= 2)
        log.append(f"{c.release}: {len(rel_rows)} rows {rel_rows[0]['release_date']}..{rel_rows[-1]['release_date']}"
                   f"; evidence {dict(sorted(grades.items()))}; {twice} periods carried by two records, all agree")
        rows += rel_rows
    off = [r for r in rows if r["time"] != "08:30"]
    log.append("not 08:30 ET: " + ", ".join(f"{r['release']} {r['period']} -> {r['release_date']} {r['time']}"
                                             for r in off))
    weekend = [r for r in rows if D(r["release_date"]).weekday() >= 5]
    closed = [(r["release"], r["period"], r["release_date"]) for r in rows if r["release_date"] in fed_closed]
    # 2025-12-24 (Wed): federal offices closed by executive order, yet DOL issued the claims report that morning
    # (ALFRED vintage and FRED calendar agree); the Christmas Thursday moved it there
    assert not weekend and closed == [("CLAIMS", "2025-12-20", "2025-12-24")], (weekend, closed)
    log.append("no release date falls on a weekend; one falls on a signed FED closure: CLAIMS 2025-12-20 -> "
               "2025-12-24 (executive-order closure; DOL released anyway, ALFRED and FRED agree)")
    keys = Counter((r["release"], r["period"]) for r in rows)
    assert max(keys.values()) == 1
    rows.sort(key=lambda r: (r["release_date"], ("CLAIMS", "EMPSIT", "CPI", "PIO").index(r["release"]), r["period"]))
    doc = envelope(rows)
    OUT.mkdir(exist_ok=True)
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    (OUT / "release_calendar.yaml").write_text(text, encoding="utf-8")
    sys.path.insert(0, str(REPO))
    from core.calendars import store
    md5 = store.content_md5(yaml.safe_load(text))
    log.append(f"release_calendar.yaml: {len(rows)} rows ({dict(Counter(r['release'] for r in rows))}); "
               f"content md5 {md5}")
    (HERE / "build.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
