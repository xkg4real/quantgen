"""Dry run of the proposed holidays_CBOE and holidays_ECOS v1.0.0 through the real loader and the data layer.

Copies core/calendars/data/ to a temporary directory, swaps in proposed/, signs only those two copies with the
placeholder "SIMULATION - not a signature", then checks the VIX and ECOS paths that were blocked. core/calendars/data/
is only read.

    python docs/audit/2026-10-27/calendar_batch3/simulate_signed.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

from core.calendars import publication, store  # noqa: E402
from core.calendars.adapter import CalendarClocks  # noqa: E402
from core.ficc import contracts as C, pit as P  # noqa: E402

FAKE = "SIMULATION - not a signature"
TWO = ("holidays_CBOE", "holidays_ECOS")
UTC = timezone.utc


def fake_sign(data_dir: Path) -> None:
    mp = data_dir / store.MANIFEST
    manifest = yaml.safe_load(mp.read_text(encoding="utf-8"))
    rows = {r["file"]: r for r in manifest["rows"]}
    for fid in TWO:
        p = data_dir / f"{fid}.yaml"
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for r in doc["rows"]:
            r["signed_off_by"] = FAKE
        doc["signed_off_by"], doc["signed_utc"] = FAKE, "2026-10-28T00:00:00Z"
        doc["md5"] = store.content_md5(doc)
        p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        rows[p.name].update(version=doc["version"], md5=doc["md5"], signed_off_by=FAKE)
    mp.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")


def main() -> int:
    failures = []

    def check(label, got, want):
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
        failures.append(label) if not ok else None

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        for fid in TWO:
            shutil.copy(HERE / "proposed" / f"{fid}.yaml", data_dir / f"{fid}.yaml")
        fake_sign(data_dir)
        cal = store.CalendarSet(data_dir)
        reg = C.default_registry()
        clk = CalendarClocks(reg, cal=cal)

        print("load")
        for fid in TWO:
            check(f"{fid} loads (v{cal.file(fid).version}, {len(cal.file(fid).rows)} rows)", cal.refusal(fid), None)

        print("next expected observation")
        N = publication.next_expected_obs
        vix = {"schedule_id": "VIXCLS_CBOE", "series_id": "VIXCLS", "obs_calendar": "CBOE"}
        ecos = {"schedule_id": "ECOS_USDKRW", "series_id": "ECOS_1530_CLOSE", "obs_calendar": "ECOS"}
        check("VIXCLS after 2026-11-25 (Thanksgiving 11-26)", N(vix, date(2026, 11, 25), cal=cal), date(2026, 11, 27))
        check("VIXCLS after 2026-05-22 (Memorial Day 05-25)", N(vix, date(2026, 5, 22), cal=cal), date(2026, 5, 26))
        check("ECOS after 2026-12-30 (12-31 FX year-end, 01-01)", N(ecos, date(2026, 12, 30), cal=cal), date(2027, 1, 4))
        check("ECOS after 2027-04-30 (05-03 노동절 대체)", N(ecos, date(2027, 4, 30), cal=cal), date(2027, 5, 4))
        check("CBOE early close 2026-11-27", cal.holiday_set("CBOE")[1].get(date(2026, 11, 27)), "13:15")

        print("data layer: ingest and non-context reads")
        st = P.PITStore(Path(tmp) / "pit", registry=reg, clocks=clk)
        P.ingest(st, "ECOS_1530_CLOSE", [(date(2026, 10, 27), 1391.2)], source="ECOS",
                 retrieved_at_utc=datetime(2026, 10, 27, 7, 0, tzinfo=UTC), registry=reg, clocks=clk)
        P.ingest(st, "VIXCLS", [(date(2026, 10, 27), 16.4)], source="FRED",
                 retrieved_at_utc=datetime(2026, 10, 28, 1, 0, tzinfo=UTC), registry=reg, clocks=clk)
        ctx = P.RunContext(datetime(2026, 10, 28, 6, 30, 30, tzinfo=UTC), datetime(2026, 10, 28, 7, 0, tzinfo=UTC))
        v = C.read_input(st, reg, "ECOS_1530_CLOSE", ctx, "nav_fx_backtests", clk)
        check("ECOS_1530_CLOSE forward_sim read (R-29 nav_fx_backtests)", type(v).__name__, "PITValue")
        check("  value", getattr(v, "value", None), 1391.2)
        v2 = C.read_input(st, reg, "VIXCLS", ctx, "R-08", clk)
        check("VIXCLS context read (R-08)", type(v2).__name__, "PITValue")
        stale = C.is_stale(st, reg, "VIXCLS", ctx.decision_utc, ctx.knowledge_utc, clk)
        check("VIXCLS staleness check runs (CBOE calendar readable)", stale.stale, False)

        print("coverage horizon")
        for fid in TWO:
            f = cal.file(fid)
            print(f"  {fid:14} covers {f.covers_from}..{f.covers_to}; sessions left on 2026-10-28: "
                  f"{store.sessions_left(cal, f, date(2026, 10, 28))}")

    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
