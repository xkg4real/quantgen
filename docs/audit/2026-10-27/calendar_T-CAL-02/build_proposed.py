"""Build the proposed v1.0.0 holiday files for the T-CAL-02 audit (docs/audit/2026-10-27/01_calendar_T-CAL-02.md).

Reads the v0.1.0 drafts as committed before the audit (git DRAFT_REF), applies the audited change list below and
writes the result to proposed/ next to this script, plus proposed.diff. It never touches core/calendars/data/ and
never writes a signature: signed_off_by, signed_utc and md5 stay null on every file and every row (spec L2100; the owner signs).

    python docs/audit/2026-10-27/calendar_T-CAL-02/build_proposed.py
"""
from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DATA = REPO / "core" / "calendars" / "data"
OUT = HERE / "proposed"
DRAFT_REF = "1f63f91"                   # the last commit before the audit: core/calendars/data at v0.1.0-draft
AUDIT_UTC = "2026-10-28T05:31:09Z"
REPORT = "docs/audit/2026-10-27/01_calendar_T-CAL-02.md"
VERSION = "1.0.0"

# --------------------------------------------------------------------------- #
# Sources (search-engine excerpts on 2026-10-28; direct fetch was blocked by the session's network policy)
# --------------------------------------------------------------------------- #
KASI_2026 = "https://astro.kasi.re.kr/kor/life/post/calendarData?year=2026"
KASI_2027 = "https://astro.kasi.re.kr/kor/life/post/calendarData?year=2027"
KASA_2027 = "https://www.kasa.go.kr/prog/plcyBrf/brief/kor/sub01_01_04/view.do?plcyBrfNo=431"
KRX_2026_ADHOC = ("https://www.dailian.co.kr/news/view2/1646567/"
                  "%ED%95%9C%EA%B5%AD%EA%B1%B0%EB%9E%98%EC%86%8C-%EC%A7%80%EB%B0%A9%EC%84%A0%EA%B1%B0%EC%9D%BC"
                  "%EC%A0%9C%ED%97%8C%EC%A0%88-%EC%A6%9D%EC%8B%9C-%ED%9C%B4%EC%9E%A5-2026")
KRX_RULE = "KRX 유가증권시장 업무규정 휴장일 조항(관공서의 공휴일·노동절·연말 휴장일)"
ICE_2024 = ("https://ir.theice.com/press/news-details/2024/"
            "NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx")
ICE_2025 = ("https://ir.theice.com/press/news-details/2025/"
            "NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx")
NYSE_CARTER = "https://www.businesswire.com/news/home/20241230579727/en"
FED_K8 = "https://www.federalreserve.gov/aboutthefed/k8.htm"
FED_STATUTE = "5 U.S.C. 6103 + K.8 Saturday/Sunday footnote; " + FED_K8
SIFMA_PAGE = "https://www.sifma.org/resources/guides-playbooks/holiday-schedule"
SIFMA_PR = "https://www.sifma.org/news/press-releases/"
SIFMA = {
    "2025-01-09": SIFMA_PR + ("sifma-recommends-early-market-close-on-january-9-2025-for-the-national-day-of-mourning-"
                              "in-honor-of-former-president-carter"),
    "2025-04-17": SIFMA_PR + ("sifma-recommends-an-early-market-close-on-april-17-and-a-full-market-close-on-april-18-"
                              "in-the-u-s-in-observance-of-good-friday-2025"),
    "2025-05-23": SIFMA_PR + ("sifma-recommends-an-early-market-close-on-may-23-and-a-full-market-close-on-may-26-"
                              "in-the-u-s-in-observance-of-the-memorial-day-holiday-2025"),
    "2025-07-03": SIFMA_PR + ("sifma-recommends-an-early-market-close-on-july-3-and-a-full-market-close-on-july-4-"
                              "in-the-u-s-in-observance-of-the-independence-day-holiday-2025"),
    "2026-04-03": SIFMA_PR + ("sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-"
                              "good-friday-easter-monday-holidays-2026"),
    "2026-07-02": ("https://mondovisione.com/media-and-resources/news/"
                   "sifma-fixed-income-market-close-recommendations-in-the-us-the-uk-and-japan-2026618/"),
}
SIFMA["2025-04-18"] = SIFMA["2025-04-17"]
SIFMA["2025-05-26"] = SIFMA["2025-05-23"]
SIFMA["2025-07-04"] = SIFMA["2025-07-03"]
SIFMA["2026-07-03"] = SIFMA["2026-07-02"]

# Evidence classes (the report explains them): A official notice + independent cross-check; B official almanac or
# rule + cross-check, the issuer's own notice still to come; C inferred, included because a closure that did not
# happen only makes data available later (never earlier).
EVID_A, EVID_B, EVID_C = "A", "B", "C"

# --------------------------------------------------------------------------- #
# KRX
# --------------------------------------------------------------------------- #
KRX_NAMES = {
    "2026-01-01": "신정 (New Year's Day)",
    "2026-02-16": "설날 연휴 (Seollal)",
    "2026-02-17": "설날 (Seollal)",
    "2026-02-18": "설날 연휴 (Seollal)",
    "2026-03-02": "삼일절 대체공휴일 (Independence Movement Day, substitute)",
    "2026-05-01": "노동절 (Labour Day)",
    "2026-05-05": "어린이날 (Children's Day)",
    "2026-05-25": "부처님오신날 대체공휴일 (Buddha's Birthday, substitute)",
    "2026-06-03": "제9회 전국동시지방선거일 (local elections)",
    "2026-07-17": "제헌절 (Constitution Day)",
    "2026-08-17": "광복절 대체공휴일 (Liberation Day, substitute)",
    "2026-09-24": "추석 연휴 (Chuseok)",
    "2026-09-25": "추석 (Chuseok)",
    "2026-10-05": "개천절 대체공휴일 (National Foundation Day, substitute)",
    "2026-10-09": "한글날 (Hangeul Day)",
    "2026-12-25": "기독탄신일 (Christmas Day)",
    "2026-12-31": "연말 휴장일 (year-end closure)",
    "2027-01-01": "신정 (New Year's Day)",
    "2027-02-08": "설날 연휴 (Seollal)",
    "2027-02-09": "설날 대체공휴일 (Seollal, substitute)",
    "2027-03-01": "삼일절 (Independence Movement Day)",
    "2027-05-03": "노동절 대체공휴일 (Labour Day, substitute)",
    "2027-05-05": "어린이날 (Children's Day)",
    "2027-05-13": "부처님오신날 (Buddha's Birthday)",
    "2027-07-19": "제헌절 대체공휴일 (Constitution Day, substitute)",
    "2027-08-16": "광복절 대체공휴일 (Liberation Day, substitute)",
    "2027-09-14": "추석 연휴 (Chuseok)",
    "2027-09-15": "추석 (Chuseok)",
    "2027-09-16": "추석 연휴 (Chuseok)",
    "2027-10-04": "개천절 대체공휴일 (National Foundation Day, substitute)",
    "2027-10-11": "한글날 대체공휴일 (Hangeul Day, substitute)",
    "2027-12-27": "기독탄신일 대체공휴일 (Christmas Day, substitute)",
    "2027-12-31": "연말 휴장일 (year-end closure)",
}
KRX_ADDED = {"2026-06-03", "2026-07-17", "2027-05-03", "2027-07-19"}


def krx_source(d: str) -> tuple[str, str, str]:
    if d in ("2026-06-03", "2026-07-17"):
        return (f"{KRX_2026_ADHOC}; {KRX_RULE}", EVID_A,
                "KRX announced the closure on 2026-05-20 (reported); no 069500.KS / 005930.KS bar that day "
                "(docs/asset_expansion/cache); absent from exchange_calendars 4.13.2, which the draft copied")
    if d.startswith("2026"):
        return (f"{KASI_2026}; {KRX_RULE}", EVID_A,
                "2026 almanac + KRX rule; no 069500.KS / 005930.KS bar that day (cache to 2026-09-23); "
                "pandas_market_calendars XKRX and python-holidays KR agree")
    if d in ("2027-05-03", "2027-07-19"):
        return (f"{KASA_2027}; {KASI_2027}; {KRX_RULE}", EVID_B,
                "2027 월력요항 (관보 2026-06-29): Labour Day and Constitution Day are public holidays from 2026, "
                "both fall on Saturday in 2027, so the substitute Monday is a public holiday; python-holidays KR "
                "agrees; absent from exchange_calendars 4.13.2; KRX 2027 notice expected Dec 2026")
    return (f"{KASA_2027}; {KASI_2027}; {KRX_RULE}", EVID_B,
            "2027 월력요항 + KRX rule; pandas_market_calendars XKRX and python-holidays KR agree; "
            "KRX 2027 notice expected Dec 2026")


# --------------------------------------------------------------------------- #
# NYSE (no date changes; sources only)
# --------------------------------------------------------------------------- #
def nyse_source(d: str) -> tuple[str, str, str]:
    if d == "2025-01-09":
        return NYSE_CARTER, EVID_A, "NYSE Group closure for the national day of mourning (announced 2024-12-30)"
    return (ICE_2024 if d.startswith("2025") else ICE_2025), EVID_A, \
        "NYSE Group holiday and early-close release; pandas_market_calendars NYSE agrees"


# --------------------------------------------------------------------------- #
# FED (Board of Governors closures: they move the Board's H.15 and H.10 publication)
# --------------------------------------------------------------------------- #
FED_ADDED = {
    # date: (name, source, evidence class, note)
    "2017-01-20": ("Inauguration Day (Board closed)", "https://www.op-f.org/media/0i0pw22x/federal-reserve-board-holidays.pdf",
                   EVID_A, "Board holiday list; H.10 DEXKOUS blank that day"),
    "2018-12-05": ("National Day of Mourning, President G.H.W. Bush (Board closed)",
                   "https://www.federalreserve.gov/newsevents/pressreleases/other20181203a.htm", EVID_A,
                   "Board offices closed, scheduled releases postponed to Dec 6; H.10 DEXKOUS blank"),
    "2018-12-24": ("Executive order closing federal offices (Christmas Eve)",
                   "https://www.federalreserve.gov/newsevents/2018-december.htm", EVID_A,
                   "executive order; Board closure confirmed by the owner 2026-10-28 (CAL-14); H.10 DEXKOUS blank"),
    "2019-12-24": ("Executive order closing federal offices (Christmas Eve)",
                   "https://trumpwhitehouse.archives.gov/presidential-actions/executive-order-providing-closing-"
                   "executive-departments-agencies-federal-government-december-24-2019/", EVID_A,
                   "executive order; Board closure confirmed by the owner 2026-10-28 (CAL-14)"),
    "2020-12-24": ("Executive order closing federal offices (Christmas Eve)", "Board calendar December 2020",
                   EVID_A, "Board closure confirmed by the owner 2026-10-28 (CAL-14); H.10 DEXKOUS blank"),
    "2021-01-20": ("Inauguration Day (Board closed)", "https://www.federalreserve.gov/foia/chair-powell-calendar-012021.htm",
                   EVID_A, "Chair's calendar: 'Board holiday - Inauguration Day'; H.10 DEXKOUS blank"),
    "2024-12-24": ("Executive order closing federal offices (Christmas Eve)",
                   "https://www.federalreserve.gov/newsevents/2024-december.htm", EVID_A,
                   "Board calendar: releases scheduled for Dec 24 published Dec 26"),
    "2025-01-09": ("National Day of Mourning, President Carter (Board closed)",
                   "https://www.federalreserve.gov/newsevents/2025-january.htm", EVID_A,
                   "Board offices closed, releases moved to Jan 10; Reserve Bank payment services open"),
    "2025-12-24": ("Executive order closing federal offices (Christmas Eve)",
                   "https://www.federalreserve.gov/newsevents/2025-december.htm", EVID_A,
                   "Board: offices closed Dec 24 and 26, daily and weekly releases published Dec 29"),
    "2025-12-26": ("Executive order closing federal offices (day after Christmas)",
                   "https://www.federalreserve.gov/newsevents/2025-december.htm", EVID_A,
                   "Board: offices closed Dec 24 and 26, daily and weekly releases published Dec 29"),
    "2027-12-31": ("New Year's Day (January 1, 2028 falls on Saturday; Board closed)", FED_K8, EVID_A,
                   "K.8: for a Saturday holiday the Reserve Banks open the preceding Friday but the Board is closed; "
                   "same treatment as the file's 2021-12-31 row; the draft generator stopped at 2027 holidays"),
}


def fed_source(d: str) -> tuple[str, str, str]:
    if d == "2021-06-18":
        return ("https://www.federalreserve.gov/newsevents/pressreleases/other20210617b.htm", EVID_A,
                "Board offices closed for Juneteenth 2021 (Reserve Bank services operated normally)")
    if d >= "2025-01-01":
        return FED_K8, EVID_A, "K.8 holiday table; python-holidays US (observed) agrees"
    return FED_STATUTE, EVID_A, "statutory federal holiday with K.8 observance; python-holidays US (observed) agrees"


# --------------------------------------------------------------------------- #
# SIFMA
# --------------------------------------------------------------------------- #
SIFMA_EARLY_ADDED = {
    "2025-01-09": "National Day of Mourning, President Carter (SIFMA early close)",
    "2025-04-17": "day before Good Friday",
    "2025-05-23": "day before Memorial Day",
    "2026-05-22": "day before Memorial Day",
    "2026-07-02": "day before Independence Day (observed)",
    "2027-03-25": "day before Good Friday",
    "2027-05-28": "day before Memorial Day",
    "2027-07-02": "day before Independence Day (observed)",
    "2027-12-23": "day before Christmas Day (observed)",
}


def sifma_source(d: str) -> tuple[str, str, str]:
    if d in SIFMA:
        return SIFMA[d], EVID_A, "SIFMA recommendation; pandas_market_calendars SIFMAUS agrees"
    if d.startswith("2027"):
        return SIFMA_PAGE, EVID_B, ("SIFMA 2026/2027 recommendations issued 2025-12-17; 2027 dates read from "
                                    "pandas_market_calendars SIFMAUS and two secondary calendars")
    if d in ("2025-10-13", "2025-11-11", "2026-10-12", "2026-11-11"):
        return SIFMA_PAGE, EVID_A, "bond-market-only holiday; H.15 DGS3MO blank where in cache range"
    return SIFMA_PAGE, EVID_A, "SIFMA holiday schedule; pandas_market_calendars SIFMAUS agrees"


# --------------------------------------------------------------------------- #
def _row(d: str, kind: str, name: str, source: tuple[str, str, str], close_local: str | None = None) -> dict:
    url, evid, note = source
    row = {"effective_from": d, "effective_to": d, "source_url": url, "retrieved_at_utc": AUDIT_UTC,
           "signed_off_by": None, "date": d, "kind": kind}
    if close_local is not None:
        row["close_local"] = close_local
    row["name"] = name
    row["evidence"] = f"{evid}: {note}"
    return row


def _retag(row: dict, source: tuple[str, str, str], name: str | None = None) -> dict:
    out = {k: v for k, v in row.items() if k != "unverified"}
    out["source_url"], out["retrieved_at_utc"] = source[0], AUDIT_UTC
    if name is not None:
        out["name"] = name
    out["evidence"] = f"{source[1]}: {source[2]}"
    return out


def _sorted(rows: list[dict]) -> list[dict]:
    order = {"closed": 0, "early_close": 1, "open": 2}
    return sorted(rows, key=lambda r: (order[r["kind"]], r["date"]))


def build_krx(doc: dict) -> dict:
    rows = [_retag(r, krx_source(r["date"]), KRX_NAMES[r["date"]]) for r in doc["rows"]]
    rows += [_row(d, "closed", KRX_NAMES[d], krx_source(d)) for d in sorted(KRX_ADDED)]
    doc["unverified"] = [
        "2027 rows: from the 2027 월력요항 (관보) and the KRX holiday rule; KRX publishes its own 2027 notice in "
        "December 2026. A difference (e.g. an added temporary holiday) is a new version with a new signature",
        "temporary holidays designated after the audit date are not in this file (change control)",
        "1995-2025 rows are not in this file yet (T-CLOSE-02 needs 2015, 2016 and 2025): a later version",
    ]
    doc["rows"] = _sorted(rows)
    return doc


def build_nyse(doc: dict) -> dict:
    doc["rows"] = _sorted([_retag(r, nyse_source(r["date"])) for r in doc["rows"]])
    doc["unverified"] = ["closures announced after the audit date (e.g. a national day of mourning) are a new version"]
    return doc


def build_fed(doc: dict) -> dict:
    rows = [_retag(r, fed_source(r["date"])) for r in doc["rows"]]
    have = {r["date"] for r in rows}
    for d, (name, url, evid, note) in FED_ADDED.items():
        assert d not in have, d
        rows.append(_row(d, "closed", name, (url, evid, note)))
    doc["unverified"] = [
        "set semantics: days the Board of Governors is closed (they move H.15 and H.10); Reserve Bank payment "
        "services may be open on some of them",
        "closures ordered after the audit date (e.g. a Christmas Eve executive order for 2026 or 2027) are a new version",
    ]
    doc["rows"] = _sorted(rows)
    return doc


def build_sifma(doc: dict) -> dict:
    rows = []
    for r in doc["rows"]:
        if r["date"] == "2026-04-03":       # was a full close: SIFMA recommended a 12:00 close (jobs report day)
            rows.append(_row(r["date"], "early_close", "Good Friday (12:00 early close; March employment report)",
                             sifma_source(r["date"]), close_local="12:00"))
            continue
        rows.append(_retag(r, sifma_source(r["date"])))
    have = {r["date"] for r in rows}
    for d, name in SIFMA_EARLY_ADDED.items():
        assert d not in have, d
        rows.append(_row(d, "early_close", name, sifma_source(d), close_local="14:00"))
    doc["unverified"] = [
        "2027 dates: SIFMA's 2027 page was not read directly (network policy); dates from pandas_market_calendars "
        "SIFMAUS and two secondary calendars. Good Friday 2027 (Mar 26) is a full close because the March jobs "
        "report is due Apr 2; a BLS reschedule onto Mar 26 would turn it into a 12:00 early close (new version)",
        "SIFMA recommendations are voluntary and can change for market conditions (new version when they do)",
    ]
    doc["rows"] = _sorted(rows)
    return doc


BUILDERS = {"KRX": build_krx, "NYSE": build_nyse, "FED": build_fed, "SIFMA": build_sifma}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    diffs = []
    for name, build in BUILDERS.items():
        src = DATA / f"holidays_{name}.yaml"
        old_text = subprocess.run(["git", "show", f"{DRAFT_REF}:core/calendars/data/{src.name}"], cwd=REPO, check=True,
                                  capture_output=True, text=True, encoding="utf-8").stdout
        doc = build(yaml.safe_load(old_text))
        doc["version"] = VERSION
        doc["status"] = (f"AUDITED, UNSIGNED - proposed v{VERSION} from the T-CAL-02 audit ({REPORT}); refused at "
                         "load until the owner signs (R-20 rule 6, T-CAL-01)")
        for k in ("signed_off_by", "signed_utc", "md5"):
            assert doc[k] is None, (name, k)
        assert all(r["signed_off_by"] is None for r in doc["rows"]), name
        new_text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
        (OUT / src.name).write_text(new_text, encoding="utf-8")
        diffs += difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                      f"a/core/calendars/data/{src.name}", f"b/core/calendars/data/{src.name}")
        print(f"{src.name}: {len(yaml.safe_load(old_text)['rows'])} -> {len(doc['rows'])} rows")
    (HERE / "proposed.diff").write_text("".join(diffs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
