"""Dry run of the proposed batch-5 files (holidays_JPX, SSE, HKEX, TWSE, CME and market_closes v1.0.0) through the real
loader, the decision clocks and the cross-market rule, with a SIMULATED signature.

Copies core/calendars/data/ to a temporary directory, swaps in proposed/, raises those six MANIFEST rows to 1.0.0 and
signs only those six copies with the placeholder "SIMULATION - not a signature". core/calendars/data/ is only read.

    python docs/audit/2026-10-27/calendar_batch5/simulate_signed.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

from core.calendars import clocks, publication, store  # noqa: E402

FAKE = "SIMULATION - not a signature"
SIX = ("holidays_JPX", "holidays_SSE", "holidays_HKEX", "holidays_TWSE", "holidays_CME", "market_closes")
UTC = timezone.utc


def U(y, m, d, hh=0, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


def fake_sign(data_dir: Path) -> None:
    mp = data_dir / store.MANIFEST
    manifest = yaml.safe_load(mp.read_text(encoding="utf-8"))
    rows = {r["file"]: r for r in manifest["rows"]}
    for fid in SIX:
        p = data_dir / f"{fid}.yaml"
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for r in doc["rows"]:
            r["signed_off_by"] = FAKE
        doc["signed_off_by"], doc["signed_utc"] = FAKE, "2026-10-28T00:00:00Z"
        doc["md5"] = store.content_md5(doc)
        p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        rows[p.name].update(version=doc["version"], md5=doc["md5"], signed_off_by=FAKE)
    mp.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")


def first_alert(cal, fid: str, severity: str, start: date) -> date | None:
    d = start
    while d <= date(2027, 12, 31):
        alerts = store.check_coverage(d, (fid,), cal=cal, now_utc=U(d.year, d.month, d.day))
        if any(a["severity"] == severity for a in alerts):
            return d
        d += timedelta(days=1)
    return None


def main() -> int:
    failures = []

    def check(label, got, want):
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        for fid in SIX:
            shutil.copy(HERE / "proposed" / f"{fid}.yaml", data_dir / f"{fid}.yaml")
        fake_sign(data_dir)
        cal = store.CalendarSet(data_dir)
        S = lambda m, y, mo, d: clocks.is_session(m, date(y, mo, d), cal=cal)
        D = lambda m, y, mo, d: clocks.decision_time_utc(m, date(y, mo, d), cal=cal)

        print("load")
        for fid in SIX:
            check(f"{fid} loads", cal.refusal(fid), None)

        print("JP (TSE)")
        check("2026-09-22 citizens' holiday", S("JP", 2026, 9, 22), False)
        check("2026-09-24 session", S("JP", 2026, 9, 24), True)
        check("2027-03-22 substitute holiday", S("JP", 2027, 3, 22), False)
        check("2026-12-30 session (no half day)", S("JP", 2026, 12, 30), True)
        check("decision 2026-10-22", D("JP", 2026, 10, 22), U(2026, 10, 22, 6, 30))

        print("CN (SSE)")
        check("2026-10-07 National Day", S("CN", 2026, 10, 7), False)
        check("2026-10-08 session", S("CN", 2026, 10, 8), True)
        check("2026-10-10 make-up Saturday is not a session", S("CN", 2026, 10, 10), False)
        check("2027-02-12 inferred Spring Festival", S("CN", 2027, 2, 12), False)
        check("decision 2026-10-08 (15:00 CST)", D("CN", 2026, 10, 8), U(2026, 10, 8, 7, 0))

        print("HK (HKEX)")
        check("2026-10-19 day after Chung Yeung", S("HK", 2026, 10, 19), False)
        check("decision 2026-10-22 (CAS end 16:10 HKT)", D("HK", 2026, 10, 22), U(2026, 10, 22, 8, 10))
        check("decision 2026-12-24 half day (12:10 HKT)", D("HK", 2026, 12, 24), U(2026, 12, 24, 4, 10))
        check("2027-12-27 first weekday after Christmas", S("HK", 2027, 12, 27), False)
        mc = cal.file("market_closes").rows
        hk = lambda d: [r["close_local"] for r in store.effective_rows(mc, d) if r.get("market") == "HK"]
        check("market_closes HK 2016-07-22 (before CAS)", hk(date(2016, 7, 22)), ["16:00"])
        check("market_closes HK 2016-07-25 (CAS)", hk(date(2016, 7, 25)), ["16:10"])

        print("TW (TWSE)")
        check("2026-10-23 typhoon Champi", S("TW", 2026, 10, 23), False)
        check("2026-10-22 session", S("TW", 2026, 10, 22), True)
        check("2025-01-23 settlement-only day", S("TW", 2025, 1, 23), False)
        check("decision 2026-10-22 (13:30 TST)", D("TW", 2026, 10, 22), U(2026, 10, 22, 5, 30))

        print("CME (equity settlement days)")
        for d, want in (("2026-04-03", False), ("2026-04-02", True), ("2025-01-09", False), ("2025-11-28", True),
                        ("2027-12-31", True), ("2027-12-24", False), ("2026-10-12", True)):
            check(f"business_day CME {d}", publication.business_day("CME", date.fromisoformat(d), cal=cal), want)
        check("CME 2025-11-28 halt", cal.holiday_set("CME")[1][date(2025, 11, 28)], "12:15")

        print("cross-market rule at the KRX close of 2026-10-22 (06:30:30Z bound)")
        b = clocks.close_print_bound_utc("KR", date(2026, 10, 22), cal=cal)
        for m, want in (("TW", True), ("JP", False), ("CN", False), ("HK", False)):
            check(f"{m} same-date close usable", clocks.cross_market_usable(m, date(2026, 10, 22), b, cal=cal), want)

        print("market status on 2026-10-29")
        for m in ("JP", "CN", "HK", "TW"):
            s = store.status(m, date(2026, 10, 29), cal=cal)
            print(f"  {m}: signed={s['signed']} sessions_left={s['sessions_left']} covers_to={s['covers_to']} "
                  f"alerts={[a['severity'] for a in s['alerts']]}")
            check(f"{m} signed", s["signed"], True)
            check(f"{m} ARM precondition", store.arm_precondition(date(2026, 10, 29), m, cal=cal), True)

        print("coverage horizon: first decision date that warns (<= 60 left) / pages (<= 20 left)")
        for fid in SIX[:5]:
            print(f"  {fid:14} warn from {first_alert(cal, fid, 'warn', date(2027, 6, 1))}  "
                  f"page from {first_alert(cal, fid, 'page', date(2027, 9, 1))}")

    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
