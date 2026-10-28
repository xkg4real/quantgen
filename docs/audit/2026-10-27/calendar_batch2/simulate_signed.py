"""Dry run of the proposed kr_sessions, publication_schedules and source_skipped v1.0.0 through the real loader.

Copies core/calendars/data/ (with the owner-signed 2027 holiday files) to a temporary directory, swaps in proposed/,
signs only those three copies with the placeholder "SIMULATION - not a signature" (tools.sign_calendars refuses that
name, so the copy is signed here directly), then checks the audited behaviour. core/calendars/data/ is only read.

    python docs/audit/2026-10-27/calendar_batch2/simulate_signed.py
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
THREE = ("kr_sessions", "publication_schedules", "source_skipped")
UTC = timezone.utc


def fake_sign(data_dir: Path, file_ids) -> None:
    mp = data_dir / store.MANIFEST
    manifest = yaml.safe_load(mp.read_text(encoding="utf-8"))
    rows = {r["file"]: r for r in manifest["rows"]}
    for fid in file_ids:
        p = data_dir / f"{fid}.yaml"
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for r in doc["rows"]:
            r["signed_off_by"] = FAKE
        doc["signed_off_by"], doc["signed_utc"] = FAKE, "2026-10-28T00:00:00Z"
        doc["md5"] = store.content_md5(doc)
        p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        rows[p.name].update(version=doc["version"], md5=doc["md5"], signed_off_by=FAKE)
    mp.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")


def first_alert(cal, fid, severity, start):
    d = start
    while d <= date(2027, 12, 31):
        if any(a["severity"] == severity for a in store.check_coverage(
                d, (fid,), cal=cal, now_utc=datetime(d.year, d.month, d.day, tzinfo=UTC))):
            return d
        d += timedelta(days=1)
    return None


def main() -> int:
    failures = []

    def check(label, got, want):
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
        failures.append(label) if not ok else None

    def raises(label, fn, exc):
        try:
            fn()
        except exc as e:
            print(f"  [ok] {label}: {type(e).__name__}")
            return
        except Exception as e:                       # noqa: BLE001
            print(f"  [FAIL] {label}: {type(e).__name__} (want {exc.__name__})")
            failures.append(label)
            return
        print(f"  [FAIL] {label}: no exception (want {exc.__name__})")
        failures.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        for fid in THREE:
            shutil.copy(HERE / "proposed" / f"{fid}.yaml", data_dir / f"{fid}.yaml")
        fake_sign(data_dir, THREE)
        cal = store.CalendarSet(data_dir)

        print("load")
        for fid in THREE:
            check(f"{fid} loads (v{cal.file(fid).version})", cal.refusal(fid), None)

        print("KR clock (kr_sessions + holidays_KRX)")
        D, B = clocks.decision_time_utc, clocks.close_print_bound_utc
        check("decision_time KR 2026-11-19 (CSAT)", D("KR", date(2026, 11, 19), cal=cal), datetime(2026, 11, 19, 7, 30, tzinfo=UTC))
        check("close_print_bound KR 2026-11-19", B("KR", date(2026, 11, 19), cal=cal), datetime(2026, 11, 19, 7, 30, 30, tzinfo=UTC))
        check("decision_time KR 2027-11-18 (CSAT, added)", D("KR", date(2027, 11, 18), cal=cal), datetime(2027, 11, 18, 7, 30, tzinfo=UTC))
        check("decision_time KR 2026-11-20 (regular)", D("KR", date(2026, 11, 20), cal=cal), datetime(2026, 11, 20, 6, 30, tzinfo=UTC))
        # KR dates before 2026 stop at holidays_KRX coverage (2026-01-01..), so the historical rows are read directly
        def lunch(d):
            rows = store.effective_rows([r for r in cal.file("kr_sessions").rows if r["kind"] == "lunch_break"], d)
            return tuple(rows[0]["window_kst"]) if rows else None
        check("lunch row 1997-06-02", lunch(date(1997, 6, 2)), ("11:30", "13:00"))
        check("lunch row 1999-06-01", lunch(date(1999, 6, 1)), ("12:00", "13:00"))
        check("lunch row 2001-06-01", lunch(date(2001, 6, 1)), None)
        raises("decision_time KR 1997-06-02 (holidays_KRX starts 2026)", lambda: D("KR", date(1997, 6, 2), cal=cal),
               store.CalendarCoverageError)

        print("publication instants")
        P = publication.publication_instant
        check("H15 obs 2026-10-27", P({"schedule_id": "H15"}, date(2026, 10, 27), cal=cal), datetime(2026, 10, 28, 20, 15, tzinfo=UTC))
        check("TREASURY_PAR obs 2026-10-27", P({"schedule_id": "TREASURY_PAR"}, date(2026, 10, 27), cal=cal),
              datetime(2026, 10, 27, 22, 0, tzinfo=UTC))
        check("VIXCLS_CBOE instant obs 2026-10-27 (same day, no calendar lookup)",
              P({"schedule_id": "VIXCLS_CBOE"}, date(2026, 10, 27), cal=cal), datetime(2026, 10, 27, 20, 15, tzinfo=UTC))
        raises("VIXCLS next expected obs (obs_calendar CBOE: holidays_CBOE empty)",
               lambda: publication.next_expected_obs({"schedule_id": "VIXCLS_CBOE", "series_id": "VIXCLS", "obs_calendar": "CBOE"},
                                                     date(2026, 10, 27), cal=cal), store.CalendarUnsigned)
        raises("BLS without release dates", lambda: P({"schedule_id": "BLS"}, date(2026, 10, 27), cal=cal), KeyError)

        print("source exceptions (next expected observation skips them)")
        N = publication.next_expected_obs
        for sid in ("DGS10", "DGS2", "T10Y2Y"):
            check(f"{sid} after 2025-04-17", N({"schedule_id": "H15", "series_id": sid, "channel": "H.15", "obs_calendar": "FED"},
                                               date(2025, 4, 17), cal=cal), date(2025, 4, 21))
        check("DGS2 after 2027-03-25", N({"schedule_id": "H15", "series_id": "DGS2", "channel": "H.15", "obs_calendar": "FED"},
                                          date(2027, 3, 25), cal=cal), date(2027, 3, 29))
        check("DGS2 after 2026-04-02 (2026 Good Friday had a value)",
              N({"schedule_id": "H15", "series_id": "DGS2", "channel": "H.15", "obs_calendar": "FED"}, date(2026, 4, 2), cal=cal),
              date(2026, 4, 3))
        check("DEXKOUS after 2019-01-11", N({"schedule_id": "H10", "series_id": "DEXKOUS", "obs_calendar": "FED"},
                                             date(2019, 1, 11), cal=cal), date(2019, 1, 15))

        print("market status on 2026-10-28")
        for m in ("US", "KR"):
            s = store.status(m, date(2026, 10, 28), cal=cal)
            print(f"  {m}: signed={s['signed']} refused={sorted(s['refused'])} arm_precondition="
                  f"{store.arm_precondition(date(2026, 10, 28), m, cal=cal)}")
        check("US all coverage files signed", store.status("US", date(2026, 10, 28), cal=cal)["signed"], True)

        print("coverage horizon: first decision date that warns / pages")
        for fid in THREE:
            print(f"  {fid:22} warn from {first_alert(cal, fid, 'warn', date(2027, 6, 1))}  "
                  f"page from {first_alert(cal, fid, 'page', date(2027, 9, 1))}")

    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
