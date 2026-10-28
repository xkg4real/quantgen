"""Build the proposed v1.0.0 kr_sessions, publication_schedules and source_skipped files (audit report
docs/audit/2026-10-27/04_calendar_batch2.md).

Reads the v0.1.0 drafts as committed before the audits (git DRAFT_REF), applies the audited change list below and
writes proposed/ next to this script plus proposed.diff. It never touches core/calendars/data/ and never writes a
signature: signed_off_by, signed_utc and md5 stay null on every file and row (spec L2100; the owner signs).

    python docs/audit/2026-10-27/calendar_batch2/build_proposed.py
"""
from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE / "proposed"
DRAFT_REF = "1f63f91"                   # the last commit before the calendar audits
AUDIT_UTC = "2026-10-28T07:30:00Z"
REPORT = "docs/audit/2026-10-27/04_calendar_batch2.md"
VERSION = "1.0.0"
EVID_A, EVID_B = "A", "B"

# --------------------------------------------------------------------------- #
# Sources (search-engine excerpts on 2026-10-28; direct fetch is blocked by the session's network policy)
# --------------------------------------------------------------------------- #
WIKI_CSAT = ("https://ko.wikipedia.org/wiki/%EC%97%B0%EB%8F%84%EB%B3%84_%EB%8C%80%ED%95%99%EC%88%98%ED%95%99%EB%8A%A5"
             "%EB%A0%A5%EC%8B%9C%ED%97%98")
MOE_2027 = "https://www.etoday.co.kr/news/view/2390974"            # 교육부 2024-08-16 발표 (2027학년도 = 2026-11-19)
MOE_2028 = "https://www.hangyo.com/news/article.html?no=104640"   # 교육부 발표 (2028학년도 = 2027-11-18)
CSAT_HOURS = "https://www.heraldk.com/article/2025111215214040899"  # 수능일 정규장 10:00~16:30 (2025)
HK_1998_SAT = "https://www.hankookilbo.com/news/article/199812010033710380"
HK_1998_HOURS = "https://www.hankookilbo.com/news/article/199812240073584153"
HERALD_HOURS = "https://biz.heraldcorp.com/article/967855"         # 1995-01 오전장 09:30~11:30, 오후장 13:00~15:00
HK_2000_LUNCH = "https://www.hankookilbo.com/news/article/200005130027413996"
FED_H15 = "https://www.federalreserve.gov/releases/h15/"
FED_H10 = "https://www.federalreserve.gov/releases/h10/"
UST_PAR = "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics"
CBOE_VIX = "https://www.cboe.com/tradable_products/vix/"
ECOS = "https://ecos.bok.or.kr/ (731Y003 / 0000003)"
BLS_SCHED = "https://www.bls.gov/schedule/"
BEA_SCHED = "https://www.bea.gov/news/schedule"
FRED_VIX = "https://fred.stlouisfed.org/series/VIXCLS"
CACHE = "docs/asset_expansion/cache/"


def _sp(*parts: str) -> str:
    return "; ".join(parts)


# --------------------------------------------------------------------------- #
# kr_sessions
# --------------------------------------------------------------------------- #
def build_kr_sessions(doc: dict) -> dict:
    rows = []
    for r in doc["rows"]:
        r = {k: v for k, v in r.items() if k != "unverified"}
        r["retrieved_at_utc"] = AUDIT_UTC
        if r["kind"] == "csat_day":
            src = _sp(WIKI_CSAT, MOE_2027) if r["date"] == "2026-11-19" else WIKI_CSAT
            note = ("교육부 발표 2024-08-16; KRX 수능일 시간 공지는 보통 2~3주 전" if r["date"] == "2026-11-19" else
                    "연도별 수능 목록과 당시 보도 일치" + ("; 포항 지진으로 11-16에서 연기" if r["date"] == "2017-11-23" else "")
                    + ("; 코로나19로 11-19에서 연기" if r["date"] == "2020-12-03" else ""))
            r["source_url"], r["evidence"] = src, f"{EVID_A}: {note}"
            rows.append(r)
        elif r["kind"] == "regular_open":
            r["source_url"] = _sp(HK_1998_HOURS, HERALD_HOURS)
            r["evidence"] = (f"{EVID_A}: 1998-12-07부터 오전장 09:00 시작(30분 앞당김); 그 전 09:30" if r["open_kst"] == "09:00"
                             else f"{EVID_A}: 1995-01 이후 오전장 09:30~11:30; 1998-12-07에 09:00으로 변경")
            rows.append(r)
        elif r["kind"] == "lunch_break":
            # CHANGE KS-02: the draft carried 12:00-13:00 for the whole 1995-2000 span; before 1998-12-07 the morning
            # session ended at 11:30 (lunch 11:30-13:00); 1998-12-07 shortened it by 30 minutes to 12:00-13:00.
            early = dict(r, effective_from="1995-01-01", effective_to="1998-12-06", window_kst=["11:30", "13:00"],
                         source_url=_sp(HERALD_HOURS, HK_1998_HOURS),
                         evidence=f"{EVID_A}: 오전장 09:30~11:30, 오후장 13:00~15:00 (1995-01 ~ 1998-12-06)")
            late = dict(r, effective_from="1998-12-07", effective_to="2000-05-21", window_kst=["12:00", "13:00"],
                        source_url=_sp(HK_1998_HOURS, HK_2000_LUNCH),
                        evidence=f"{EVID_A}: 1998-12-07 오전장 09:00~12:00(점심 30분 단축); 2000-05-22 점심 휴장 폐지")
            rows += [early, late]
        else:
            raise ValueError(f"kr_sessions: unexpected row kind {r['kind']!r}")
    # CHANGE KS-01: the 2027 CSAT day (2028학년도) is missing although the file covers 2027.
    rows.append({"effective_from": "2027-11-18", "effective_to": "2027-11-18", "source_url": _sp(MOE_2028, WIKI_CSAT),
                 "retrieved_at_utc": AUDIT_UTC, "signed_off_by": None, "kind": "csat_day", "date": "2027-11-18",
                 "evidence": f"{EVID_A}: 교육부 발표(2028학년도 수능 2027-11-18 목); KRX 시간 공지는 2027년 11월 초 예상"})
    order = {"regular_open": 0, "lunch_break": 1, "csat_day": 2}
    doc["rows"] = sorted(rows, key=lambda r: (order[r["kind"]], r.get("date") or r["effective_from"]))
    doc["unverified"] = [
        "CSAT trading hours come from the rules-store config (+1 h: 10:00-16:30 KST since 2016-08-01, confirmed by the "
        "2023-2025 KRX notices); KRX publishes each year's CSAT-day notice 2-3 weeks before the exam",
        "pre-2016-08-01 CSAT window: config placeholder 10:00-16:00 (the +1 h pattern on the 09:00-15:00 session); "
        "no csat_window row signed",
        "CSAT days before 2008 are not listed: whether KRX shifted hours on those days is not established",
        "saturday_close rows (Saturday sessions before 1998-12-12) are absent: a pre-1998 Saturday decision fails "
        "closed (CalendarUnsigned)",
        "random_end_extension rows (conditional random end before 2015-06-15) are absent: no extension is assumed",
    ]
    return doc


# --------------------------------------------------------------------------- #
# publication_schedules (no rule, time or calendar changes; sources and evidence only)
# --------------------------------------------------------------------------- #
PUB_SOURCES = {
    "H15": (FED_H15, EVID_B, "spec L1299; H.15 daily update on the next Fed business day; 16:15 ET not re-read on the "
                             "publisher page (network policy)"),
    "H10": (FED_H10, EVID_B, "spec L1301; weekly release on Monday for the previous week, next business day when "
                             "Monday is a Board holiday; 16:15 ET not re-read on the publisher page"),
    "TREASURY_PAR": (UST_PAR, EVID_B, "spec L1300: 'usually available ... by 6:00 PM'; the logged first-seen posting "
                                      "time is the record's available_at"),
    "BLS": (BLS_SCHED, EVID_B, "spec L1297: 08:30 ET; release dates come from the M5 event store (none here: the "
                               "BLS series fail closed until then)"),
    "BEA": (BEA_SCHED, EVID_B, "spec L1851: BEA release calendar; release dates from the M5 event store"),
    "VIXCLS_CBOE": (CBOE_VIX, EVID_B, "spec L1302: official close 16:15 ET; needs holidays_CBOE, which has no rows yet"),
    "VIXCLS_FRED": (FRED_VIX, EVID_B, "spec brief F-23: declared lag D+1 (conservative default) until the 20-session "
                                      "FRED last_updated measurement (TASK-M1-23, owner)"),
    "ECOS_USDKRW": (ECOS, EVID_B, "spec L1305: 15:00 KST before 2016-08-01, 15:30 after; needs holidays_ECOS, which "
                                  "has no rows yet"),
    "KODEX200_PDF": ("spec L1411", EVID_B, "default, judgment: 08:00 KST on the next KRX session until measured "
                                           "(TASK-M1-23, owner)"),
}


def build_publication(doc: dict) -> dict:
    rows = []
    for r in doc["rows"]:
        r = {k: v for k, v in r.items() if k != "unverified"}
        sid = r["schedule_id"]
        if sid.startswith("MARKET_CLOSE_"):
            r["evidence"] = f"{EVID_A}: spec L1852 (a close is published at its close-print bound; R-20)"
        else:
            url, evid, note = PUB_SOURCES[sid]
            spec_ref = r.get("source_url")
            r["source_url"] = _sp(url, spec_ref) if spec_ref else url
            r["evidence"] = f"{evid}: {note}"
        r["retrieved_at_utc"] = AUDIT_UTC
        rows.append(r)
    doc["rows"] = rows
    doc["unverified"] = [
        "publisher times (H.15 16:15, H.10 Monday 16:15, Treasury 18:00, Cboe 16:15 ET) are the spec's values; the "
        "publisher pages were not re-read (network policy)",
        "dependencies outside this file: VIXCLS_CBOE needs holidays_CBOE and ECOS_USDKRW needs holidays_ECOS (both "
        "empty); BLS and BEA need release dates from the M5 event store. Those series fail closed until then",
        "VIXCLS_FRED lag and KODEX200_PDF instant are the spec's conservative defaults until the owner's measurement",
    ]
    return doc


# --------------------------------------------------------------------------- #
# source_skipped
# --------------------------------------------------------------------------- #
FED_CLOSED = {"2017-01-20", "2018-12-05", "2018-12-24", "2020-12-24", "2021-01-20"}
SPEC_LIST = {"2017-01-20", "2018-12-05", "2020-11-27", "2020-12-24", "2016-01-22", "2018-03-02"}


def build_source_skipped(doc: dict) -> dict:
    rows = []
    for r in doc["rows"]:
        r = {k: v for k, v in r.items() if k != "unverified"}
        r["retrieved_at_utc"] = AUDIT_UTC
        d, series = r["date"], r["series"]
        if series == "DGS10":
            # CHANGE SS-01: a Good Friday full close blanks every H.15 series, not only DGS10; key the row by the
            # H.15 channel, which source_skipped() matches for all nine H.15 series.
            r["series"] = "H.15"
            r["reason"] = "Good Friday SIFMA full close: no H.15 rates for that date (every H.15 series)"
            r["source_url"] = _sp("spec L1854 (Good-Friday bond-market closures)", CACHE + "fred_DGS3MO.csv")
            r["evidence"] = f"{EVID_A}: H.15 DGS3MO blank in the local cache that day; 2015, 2021, 2023, 2026 had values (early closes)"
        elif series == "DEXKOUS":
            cache = CACHE + "fred_DEXKOUS.csv"
            r["source_url"] = _sp("spec L1854 list", cache) if d in SPEC_LIST else cache
            r["evidence"] = (f"{EVID_A}: DEXKOUS blank in the local cache; also a Board closure in holidays_FED v1.0.0 "
                             "(redundant, harmless)" if d in FED_CLOSED else
                             f"{EVID_A}: DEXKOUS blank in the local cache on a Board business day (KRW-only gap)")
        elif series == "DTWEXBGS":
            board = "; also a Board closure in holidays_FED v1.0.0" if d in FED_CLOSED else ""
            r["source_url"] = "spec L1854 (DC storm closures 2016-01-22 and 2018-03-02; QF2-A3, DLA-S1)"
            r["evidence"] = f"{EVID_B}: spec list; no local DTWEXBGS file to check{board}"
        else:
            raise ValueError(f"source_skipped: unexpected series {series!r}")
        rows.append(r)
    # CHANGE SS-02: Good Friday 2027 (Mar 26) is a SIFMA full close in the signed holidays_SIFMA v1.0.0.
    rows.append({"effective_from": "2027-03-26", "effective_to": "2027-03-26",
                 "source_url": _sp("holidays_SIFMA v1.0.0 (2027-03-26 closed)", "spec L1854"),
                 "retrieved_at_utc": AUDIT_UTC, "signed_off_by": None, "series": "H.15", "date": "2027-03-26",
                 "reason": "Good Friday SIFMA full close: no H.15 rates for that date (every H.15 series)",
                 "evidence": f"{EVID_B}: expected from the signed SIFMA calendar; a BLS reschedule onto that day "
                             "would make it an early close (then remove this row in a new version)"})
    doc["rows"] = sorted(rows, key=lambda r: (r["series"], r["date"]))
    doc["unverified"] = [
        "DTWEXBGS rows rest on the spec's list (no local DTWEXBGS file)",
        "future source gaps (a KRW-only H.10 blank, a Board weather closure) are added as a new version",
    ]
    return doc


BUILDERS = {"kr_sessions": build_kr_sessions, "publication_schedules": build_publication,
            "source_skipped": build_source_skipped}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    diffs = []
    for fid, build in BUILDERS.items():
        name = f"{fid}.yaml"
        old_text = subprocess.run(["git", "show", f"{DRAFT_REF}:core/calendars/data/{name}"], cwd=REPO, check=True,
                                  capture_output=True, text=True, encoding="utf-8").stdout
        n_old = len(yaml.safe_load(old_text)["rows"])
        doc = build(yaml.safe_load(old_text))
        doc["version"] = VERSION
        doc["status"] = (f"AUDITED, UNSIGNED - proposed v{VERSION} from the calendar audit ({REPORT}); refused at load "
                         "until the owner signs (R-20 rule 6, T-CAL-01)")
        for k in ("signed_off_by", "signed_utc", "md5"):
            assert doc[k] is None, (fid, k)
        assert all(r["signed_off_by"] is None for r in doc["rows"]), fid
        new_text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
        (OUT / name).write_text(new_text, encoding="utf-8")
        diffs += difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                      f"a/core/calendars/data/{name}", f"b/core/calendars/data/{name}")
        print(f"{name}: {n_old} -> {len(doc['rows'])} rows")
    (HERE / "proposed.diff").write_text("".join(diffs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
