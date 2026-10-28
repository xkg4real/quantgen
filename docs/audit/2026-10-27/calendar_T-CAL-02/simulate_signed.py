"""Dry run of the proposed v1.0.0 holiday files through the real loader, with a SIMULATED signature.

Copies core/calendars/data/ to a temporary directory, swaps in proposed/holidays_{KRX,NYSE,FED,SIFMA}.yaml, writes
the placeholder signer "SIMULATION - not a signature" into every file of that copy (and its MANIFEST rows), then
loads it with core.calendars.store.CalendarSet and checks the audited dates and the coverage horizon. Nothing under
core/calendars/data/ is read for writing; the temporary directory is deleted at exit.

    python docs/audit/2026-10-27/calendar_T-CAL-02/simulate_signed.py
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
FOUR = ("holidays_KRX", "holidays_NYSE", "holidays_FED", "holidays_SIFMA")


def fake_sign(data_dir: Path) -> None:
    manifest_path = data_dir / store.MANIFEST
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    by_file = {row["file"]: row for row in manifest["rows"]}
    for path in sorted(data_dir.glob("*.yaml")):
        if path.name == store.MANIFEST:
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in doc.get("rows") or []:
            if isinstance(row, dict) and "signed_off_by" in row:
                row["signed_off_by"] = FAKE
        doc["signed_off_by"], doc["signed_utc"] = FAKE, "2026-10-28T00:00:00Z"
        doc["md5"] = store.content_md5(doc)
        path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        row = by_file.get(path.name)
        if row is not None:
            row.update(version=doc["version"], md5=doc["md5"], signed_off_by=FAKE)
            if path.stem in FOUR and "T-CAL-02" not in row["test_ids"]:
                row["test_ids"].append("T-CAL-02")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")


def first_alert(cal, file_id: str, severity: str, start: date) -> date | None:
    d = start
    while d <= date(2027, 12, 31):
        alerts = store.check_coverage(d, (file_id,), cal=cal, now_utc=datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
        if any(a["severity"] == severity for a in alerts):
            return d
        d += timedelta(days=1)
    return None


def main() -> int:
    failures = []

    def check(label: str, got, want) -> None:
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        for fid in FOUR:
            shutil.copy(HERE / "proposed" / f"{fid}.yaml", data_dir / f"{fid}.yaml")
        fake_sign(data_dir)
        cal = store.CalendarSet(data_dir)

        print("load")
        for fid in FOUR:
            f = cal.file(fid)
            check(f"{fid} loads, v{f.version}, covers {f.covers_from}..{f.covers_to}", cal.refusal(fid), None)

        print("KRX (is_session False = closed)")
        for d in ("2026-06-03", "2026-07-17", "2027-05-03", "2027-07-19", "2027-02-09", "2027-12-27", "2027-12-31"):
            check(f"is_session KR {d}", clocks.is_session("KR", date.fromisoformat(d), cal=cal), False)
        for d in ("2026-06-04", "2027-05-04", "2027-07-20", "2027-12-30"):
            check(f"is_session KR {d}", clocks.is_session("KR", date.fromisoformat(d), cal=cal), True)

        print("NYSE")
        for d, want in (("2027-03-26", True), ("2027-06-18", True), ("2027-12-24", True), ("2027-12-31", False)):
            check(f"nyse_holiday {d}", publication.nyse_holiday(date.fromisoformat(d), cal=cal), want)

        print("FED (fed_business_day False = Board closed)")
        for d, want in (("2027-12-31", False), ("2025-01-09", False), ("2025-12-26", False), ("2027-12-30", True),
                        ("2021-06-18", False), ("2027-07-05", False)):
            check(f"fed_business_day {d}", publication.fed_business_day(date.fromisoformat(d), cal=cal), want)

        print("SIFMA")
        for d, want in (("2026-04-03", "early_close"), ("2026-04-02", "open"), ("2027-03-25", "early_close"),
                        ("2027-03-26", "closed"), ("2027-05-28", "early_close"), ("2027-07-02", "early_close"),
                        ("2027-12-23", "early_close"), ("2027-12-31", "early_close"), ("2025-01-09", "early_close")):
            check(f"sifma_status {d}", publication.sifma_status(date.fromisoformat(d), cal=cal), want)
        check("SIFMA 2026-04-03 close time", cal.holiday_set("SIFMA")[1][date(2026, 4, 3)], "12:00")

        print("market status on 2026-10-28 (every file of the copy carries the simulated signer)")
        for m in ("KR", "US"):
            s = store.status(m, date(2026, 10, 28), cal=cal)
            print(f"  {m}: signed={s['signed']} sessions_left={s['sessions_left']} covers_to={s['covers_to']} "
                  f"alerts={[a['severity'] for a in s['alerts']]}")
            check(f"{m} signed", s["signed"], True)

        print("coverage horizon of the 2027 files: first decision date that warns (<= 60 left) / pages (<= 20 left)")
        for fid in FOUR:
            warn, page = first_alert(cal, fid, "warn", date(2027, 6, 1)), first_alert(cal, fid, "page", date(2027, 9, 1))
            print(f"  {fid:16} warn from {warn}  page from {page}")

    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
