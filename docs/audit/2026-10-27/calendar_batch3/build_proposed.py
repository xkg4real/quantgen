"""Build the proposed v1.0.0 holidays_CBOE and holidays_ECOS files (audit report
docs/audit/2026-10-27/06_calendar_batch3.md).

Both drafts ship with no rows. CBOE (the VIX official-close calendar) follows the owner-signed holidays_NYSE v1.0.0;
ECOS (BoK ECOS business days: the Seoul FX market and bank days) follows the owner-signed holidays_KRX v1.0.0. The
rows are copied from those signed files with their signatures removed, re-sourced and re-explained. Nothing under
core/calendars/data/ is written and no signature is set.

    python docs/audit/2026-10-27/calendar_batch3/build_proposed.py
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
DRAFT_REF = "1f63f91"
AUDIT_UTC = "2026-10-28T09:30:00Z"
REPORT = "docs/audit/2026-10-27/06_calendar_batch3.md"
VERSION = "1.0.0"

CBOE_NOTICES = {
    "2025-12-24": "https://www.cboe.com/notices/content/?id=57451",     # SPX/VIX options regular trading to 13:15 ET
    "2026-06-19": "https://www.cboe.com/notices/content/?id=60091",
    "2026-09-07": "https://www.cboe.com/notices/content/?id=61299",     # GTH session on the holiday, no regular session
}
FX_YEAR_END = "https://www.ytn.co.kr/_ln/0102_202512171452203412"      # 서울외환시장 12/31 휴장 (2005년부터 관행)
FX_YEAR_END_2 = "https://v.daum.net/v/20251231095305274"
LABOUR_DAY_BANKS = "https://sports.khan.co.kr/article/201705010829003"  # 근로자의 날 은행 휴무


def _signed_rows(name: str) -> list[dict]:
    doc = yaml.safe_load((DATA / f"holidays_{name}.yaml").read_text(encoding="utf-8"))
    assert doc.get("signed_off_by"), f"holidays_{name} must be owner-signed before it is copied"
    return doc["rows"], doc["covers"]


def _strip(row: dict) -> dict:
    out = {k: v for k, v in row.items() if k not in ("evidence",)}
    out["signed_off_by"] = None
    out["retrieved_at_utc"] = AUDIT_UTC
    return out


def build_cboe(doc: dict) -> dict:
    rows, covers = _signed_rows("NYSE")
    out = []
    for r in rows:
        r2 = _strip(r)
        d = r2["date"]
        if r2["kind"] == "closed":
            note = "A: Cboe options follow the NYSE holiday list; no regular session, no 16:15 ET official close"
            if d in ("2026-05-25", "2026-09-07"):
                note = ("B: Cboe ran a GTH session on this holiday (yfinance ^VIX shows a print) but no regular "
                        "session, so no 16:15 ET official close")
            r2["source_url"] = "; ".join(x for x in (r["source_url"], CBOE_NOTICES.get(d)) if x)
            r2["evidence"] = note + "; yfinance ^VIX cache blank on the other NYSE holidays 2025-01..2026-09"
        else:                                               # early_close: VIX options regular trading to 13:15 ET
            r2["close_local"] = "13:15"
            r2["name"] = f"{r['name']} (VIX/SPX options regular trading until 13:15 ET)"
            r2["source_url"] = "; ".join(x for x in (r["source_url"], CBOE_NOTICES.get(d, CBOE_NOTICES["2025-12-24"])) if x)
            r2["evidence"] = ("B: on NYSE 13:00 early-close days Cboe C1 SPX/VIX options trade to 13:15 ET (2025-12-24 "
                              "notice); the VIXCLS publication instant stays 16:15 ET (later, never earlier)")
        out.append(r2)
    doc["covers"] = dict(covers)
    doc["rows"] = out
    doc["unverified"] = [
        "the 2026+ Cboe holiday GTH sessions give VIX prints on some NYSE holidays; this calendar is the regular-session "
        "official close (VIXCLS), so those days stay closed",
        "early-close times are the 2025-12-24 Cboe notice pattern (13:15 ET); Cboe's own notice for each date governs",
        "a Cboe-only closure (none seen 2025-2026) is a new version",
    ]
    return doc


def build_ecos(doc: dict) -> dict:
    rows, covers = _signed_rows("KRX")
    out = []
    for r in rows:
        r2 = _strip(r)
        d, name = r2["date"], r2["name"]
        if d.endswith("-12-31"):
            r2["source_url"] = f"{FX_YEAR_END}; {FX_YEAR_END_2}"
            r2["evidence"] = ("A: 서울외환시장운영협의회가 2005년부터 연말 마지막 영업일(12/31)을 휴장으로 운영 "
                              "(2025-12-31 휴장, 1/2 10:00 개장); KRX 연말 휴장과 같은 날")
        elif "노동절" in name and "대체" not in name:
            r2["source_url"] = f"{r['source_url']}; {LABOUR_DAY_BANKS}"
            r2["evidence"] = "A: 노동절은 2026년부터 공휴일; 그 전에도 은행 휴무(근로자의 날)"
        else:
            r2["evidence"] = ("A: 관공서 공휴일·대체공휴일·선거일은 은행과 서울외환시장 휴무; 날짜는 서명된 "
                              "holidays_KRX v1.0.0과 같음")
        out.append(r2)
    doc["covers"] = dict(covers)
    doc["rows"] = out
    doc["unverified"] = [
        "the onshore USD/KRW market trades 24 hours from 2026-07-06 (Mon 06:00 - Sat 06:00); ECOS still posts the "
        "15:30 KST close only on Korean business days, which this calendar lists",
        "the 2026 and 2027 year-end closures follow the FX market committee's practice; its notice each December governs",
        "1995-2025 rows are not in this file (as holidays_KRX); history is a later version",
    ]
    return doc


BUILDERS = {"holidays_CBOE": build_cboe, "holidays_ECOS": build_ecos}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    diffs = []
    for fid, build in BUILDERS.items():
        name = f"{fid}.yaml"
        old_text = subprocess.run(["git", "show", f"{DRAFT_REF}:core/calendars/data/{name}"], cwd=REPO, check=True,
                                  capture_output=True, text=True, encoding="utf-8").stdout
        doc = build(yaml.safe_load(old_text))
        doc["version"] = VERSION
        doc["status"] = (f"AUDITED, UNSIGNED - proposed v{VERSION} ({REPORT}); refused at load until the owner signs "
                         "(R-20 rule 6, T-CAL-01)")
        for k in ("signed_off_by", "signed_utc", "md5"):
            assert doc[k] is None, (fid, k)
        assert all(r["signed_off_by"] is None for r in doc["rows"]), fid
        new_text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
        (OUT / name).write_text(new_text, encoding="utf-8")
        diffs += difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                      f"a/core/calendars/data/{name}", f"b/core/calendars/data/{name}")
        print(f"{name}: 0 -> {len(doc['rows'])} rows, covers {doc['covers']['from']}..{doc['covers']['to']}")
    (HERE / "proposed.diff").write_text("".join(diffs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
