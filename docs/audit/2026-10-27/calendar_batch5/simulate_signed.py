"""Dry run of the proposed release_calendar v1.0.0 through the real loader, the clocks adapter and the data layer.

Copies core/calendars/data/ to a temporary directory, adds proposed/release_calendar.yaml with a MANIFEST row, signs
only that copy with the placeholder "SIMULATION - not a signature", and adds release_calendar to the US coverage
files in-process (the store.py change that lands with the signature). Then every row's publication instant is
checked against its own date, time and zone, and the BLS/BEA/DOL series are ingested and read. core/calendars/data/
is only read.

    python docs/audit/2026-10-27/calendar_batch5/simulate_signed.py

Run it on a tree with the proposed code patch (proposed_code.diff) to see the 10:00 ET rows and the long-lag
usable_at pass; on the current tree those checks fail and the rest pass.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from collections import Counter
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

from core.calendars import store  # noqa: E402
from core.calendars.adapter import CalendarClocks  # noqa: E402
from core.ficc import contracts as C, pit as P  # noqa: E402

FAKE = "SIMULATION - not a signature"
FID = "release_calendar"
UTC = timezone.utc
NY = ZoneInfo("America/New_York")
SERIES = {"CPI": ("CPIAUCSL", "CPILFESL"), "EMPSIT": ("UNRATE", "PAYEMS", "SAHMREALTIME"),
          "PIO": ("PCEPI", "PCEPILFE"), "CLAIMS": ("ICSA",)}
U = lambda *a: datetime(*a, tzinfo=UTC)          # noqa: E731


def fake_sign(data_dir: Path) -> str:
    p = data_dir / f"{FID}.yaml"
    shutil.copy(HERE / "proposed" / f"{FID}.yaml", p)
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    proposed_md5 = store.content_md5(doc)
    for r in doc["rows"]:
        r["signed_off_by"] = FAKE
    doc["signed_off_by"], doc["signed_utc"] = FAKE, "2026-10-28T00:00:00Z"
    doc["md5"] = store.content_md5(doc)
    p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    mp = data_dir / store.MANIFEST
    manifest = yaml.safe_load(mp.read_text(encoding="utf-8"))
    manifest["rows"] = [r for r in manifest["rows"] if r["file"] != f"{FID}.yaml"] + [
        {"file": f"{FID}.yaml", "version": doc["version"], "md5": doc["md5"], "signed_off_by": FAKE,
         "test_ids": ["T-AVAIL-01"]}]
    mp.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    return proposed_md5


def main() -> int:
    failures = []

    def check(label, got, want):
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
        failures.append(label) if not ok else None

    before = {p.name: store.md5_hex(p.read_bytes()) for p in sorted(store.DATA_DIR.glob("*.yaml"))}
    if FID not in store.COVERAGE_FILES["US"]:
        store.COVERAGE_FILES["US"] = store.COVERAGE_FILES["US"] + (FID,)
        print(f"store.COVERAGE_FILES['US'] += ('{FID}',)  (in-process; the store.py change that lands with the signature)")
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        proposed_md5 = fake_sign(data_dir)
        cal = store.CalendarSet(data_dir)
        reg = C.default_registry()
        clk = CalendarClocks(reg, cal=cal)

        print("load")
        f = cal.file(FID)
        check(f"{FID} loads (v{f.version}, covers {f.covers_from}..{f.covers_to})", cal.refusal(FID), None)
        check("rows", len(f.rows), 264)
        print(f"  proposed content md5 (what the owner signs): {proposed_md5}")

        print("every row: publication instant == its own date, time and zone")
        bad, n = [], 0
        for row in f.rows:
            want = datetime.combine(date.fromisoformat(row["release_date"]),
                                    time(*map(int, row["time"].split(":"))), tzinfo=ZoneInfo(row["tz"])).astimezone(UTC)
            for sid in SERIES[row["release"]]:
                n += 1
                got = clk.publication_instant(sid, date.fromisoformat(row["period"]))
                if got != want:
                    bad.append(f"{sid} {row['period']}: {got} != {want}")
        check(f"{n} instants (8 series over their release rows): mismatches", len(bad), 0)
        for b in bad:
            print(f"      {b}")
        check("BEA 10:00 ET, EDT: PCEPILFE 2025-03 -> 2025-04-30", clk.publication_instant("PCEPILFE", date(2025, 3, 1)),
              U(2025, 4, 30, 14, 0))
        check("BEA 10:00 ET, EST: PCEPILFE 2025-10 -> 2026-01-22", clk.publication_instant("PCEPILFE", date(2025, 10, 1)),
              U(2026, 1, 22, 15, 0))
        check("CLAIMS week of 2026-11-21 -> Wed 2026-11-25 (Thanksgiving)",
              clk.publication_instant("ICSA", date(2026, 11, 21)), U(2026, 11, 25, 13, 30))
        check("CPI 2026-10 -> 2026-11-10 08:30 EST", clk.publication_instant("CPIAUCSL", date(2026, 10, 1)),
              U(2026, 11, 10, 13, 30))
        for sid, d in (("CPIAUCSL", date(2025, 10, 1)), ("CPILFESL", date(2025, 10, 1)), ("PCEPI", date(2027, 12, 1)),
                       ("CPIAUCSL", date(2024, 11, 1))):
            try:
                got = clk.publication_instant(sid, d)
            except KeyError:
                got = "KeyError (no release date: unpublished)"
            check(f"{sid} {d} (no row)", got, "KeyError (no release date: unpublished)")

        print("usable_at at the KRX decision, every monthly row released in the KRX file's span (from 2026-01-02)")
        errs, n = Counter(), 0
        for row in f.rows:
            if row["release"] == "CLAIMS" or row["release_date"] < "2026-01-02":
                continue
            sid, n = SERIES[row["release"]][0], n + 1
            try:
                ua = clk.usable_at(sid, date.fromisoformat(row["period"]), "KR")
                if ua < clk.publication_instant(sid, date.fromisoformat(row["period"])):
                    errs["before publication"] += 1
            except (ValueError, store.CalendarCoverageError) as exc:
                errs[f"{row['release']} {type(exc).__name__}"] += 1
        check(f"usable_at errors over {n} rows (lags of 60+ days need the probe patch)", dict(errs), {})

        print("data layer: ingest stamps and reads")
        st = P.PITStore(Path(tmp) / "pit", registry=reg, clocks=clk)
        P.ingest(st, "CPIAUCSL", [(date(2026, 9, 1), 336.298)], source="FRED",
                 retrieved_at_utc=U(2026, 10, 14, 14, 0), registry=reg, clocks=clk)
        row = st.rows("CPIAUCSL")[0]
        check("CPIAUCSL 2026-09 available_at (calendar_bound, 08:30 EDT)",
              (row["available_at_utc"], row["available_at_source"]), (U(2026, 10, 14, 12, 30), "calendar_bound"))
        P.ingest(st, "PCEPILFE", [(date(2026, 7, 1), 128.1), (date(2026, 8, 1), 128.4)], source="FRED",
                 retrieved_at_utc=U(2026, 10, 1, 0, 0), registry=reg, clocks=clk)
        ctx = P.RunContext(U(2026, 10, 28, 6, 30, 30), U(2026, 10, 28, 7, 0))
        v = C.read_input(st, reg, "PCEPILFE", ctx, "hedge_state", clk)
        check("PCEPILFE risk_model read on 2026-10-28 (Aug obs; Sep due 2026-10-29)", type(v).__name__, "PITValue")
        check("  obs_date", getattr(v, "obs_date", None), date(2026, 8, 1))
        late = P.RunContext(U(2026, 11, 6, 6, 30, 30), U(2026, 11, 6, 7, 0))
        v2 = C.read_input(st, reg, "PCEPILFE", late, "hedge_state", clk)
        check("PCEPILFE on 2026-11-06 without the Sep obs: stale (missed release)",
              getattr(v2, "reason", type(v2).__name__), "stale")
        P.ingest(st, "ICSA", [(date(2026, 10, 24), 219000.0)], source="FRED",
                 retrieved_at_utc=U(2026, 10, 29, 12, 0), registry=reg, clocks=clk)
        check("ICSA retrieved before 08:30 ET on release day: provisional print",
              st.rows("ICSA")[0]["value_status"], "provisional_intraday")

        print("US coverage with release_calendar")
        s = store.status("US", date(2026, 10, 28), cal=cal)
        check("US signed on 2026-10-28", (s["signed"], s["refused"]), (True, {}))
        print(f"  US sessions_left={s['sessions_left']} covers {s['covers_from']}..{s['covers_to']} "
              f"alerts={[a['severity'] for a in s['alerts']]}")
        print(f"  {FID}: FED business days left on 2026-10-28: {store.sessions_left(cal, f, date(2026, 10, 28))}")
        for d in (date(2027, 10, 1), date(2027, 10, 8), date(2027, 12, 1)):
            sev = [a["severity"] for a in store.status("US", d, cal=cal)["alerts"]]
            print(f"  {d}: sessions_left={store.sessions_left(cal, f, d)} alerts={sev}")

    after = {p.name: store.md5_hex(p.read_bytes()) for p in sorted(store.DATA_DIR.glob("*.yaml"))}
    check("core/calendars/data unchanged", after == before, True)
    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
