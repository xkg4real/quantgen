"""Dry run of the proposed kr_regime_tags v1.0.0 through the real loader, with a SIMULATED signature on a copy.

Checks the T-REGIME-01 point clauses (spec L2098), the contiguity rule enforced at load, the audited changes, and the
KR market status once every KR file is signed. core/calendars/data/ is only read.

    python docs/audit/2026-10-27/calendar_batch4/simulate_signed.py
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

from core.calendars import regime, store  # noqa: E402

FAKE = "SIMULATION - not a signature"
FID = "kr_regime_tags"


def main() -> int:
    failures = []

    def check(label, got, want):
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
        failures.append(label) if not ok else None

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(store.DATA_DIR, data_dir)
        shutil.copy(HERE / "proposed" / f"{FID}.yaml", data_dir / f"{FID}.yaml")
        mp = data_dir / store.MANIFEST
        manifest = yaml.safe_load(mp.read_text(encoding="utf-8"))
        p = data_dir / f"{FID}.yaml"
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for r in doc["rows"]:
            r["signed_off_by"] = FAKE
        doc["signed_off_by"], doc["signed_utc"] = FAKE, "2026-10-28T00:00:00Z"
        doc["md5"] = store.content_md5(doc)
        p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        next(r for r in manifest["rows"] if r["file"] == p.name).update(version=doc["version"], md5=doc["md5"],
                                                                          signed_off_by=FAKE)
        mp.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        cal = store.CalendarSet(data_dir)
        R = lambda d: regime.regime_tags("KR", d, cal=cal)

        print("load (one row per tag per date, no gap, no overlap)")
        check(f"{FID} loads", cal.refusal(FID), None)
        d, n = date(1995, 1, 1), 0
        while d <= date(2027, 12, 31):
            assert tuple(R(d)) == regime.TAGS
            d += timedelta(days=1); n += 1
        print(f"  [ok] full tag set on every date 1995-01-01..2027-12-31 ({n} dates)")

        print("T-REGIME-01 point clauses (spec L2098)")
        for when, tag, want in ((date(1997, 6, 2), "price_limit", 0.08), (date(1998, 6, 1), "price_limit", 0.12),
                                (date(1999, 6, 1), "price_limit", 0.15), (date(2015, 6, 15), "price_limit", 0.30),
                                (date(1997, 10, 1), "fx_regime", "peg_1997"), (date(2002, 1, 2), "etf_available", False),
                                (date(2024, 6, 3), "short_sale_ban", True), (date(2026, 10, 2), "sell_tax_pct", 0.20),
                                (date(2025, 6, 2), "sell_tax_pct", 0.15), (date(2022, 6, 3), "short_sale_ban", False),
                                (date(2022, 6, 3), "short_sale_regime", "partial_ban_non_index"),
                                (date(1997, 6, 7), "saturday_session", True), (date(1998, 12, 12), "saturday_session", False),
                                (date(2026, 10, 2), "close_time_kst", "15:30"),
                                (date(2026, 10, 2), "random_end", "unconditional_le_30s"),
                                (date(2026, 10, 2), "usdkrw_onshore_hours", "24h"),
                                (date(2024, 2, 26), "value_up", "post_value_up_2024_02_26")):
            check(f"{tag} {when}", R(when)[tag], want)

        print("audited changes")
        check("lunch_break 1997-06-02 (RT-01)", R(date(1997, 6, 2))["lunch_break"], "11:30-13:00")
        check("lunch_break 1999-06-01", R(date(1999, 6, 1))["lunch_break"], "12:00-13:00")
        check("short_sale_ban 2011-08-10 (RT-02)", R(date(2011, 8, 10))["short_sale_ban"], True)
        check("short_sale_regime 2012-06-01 (financials)", R(date(2012, 6, 1))["short_sale_regime"], "partial_ban_financials")
        check("short_sale_regime 2014-01-02", R(date(2014, 1, 2))["short_sale_regime"], "none")
        check("random_end 2000-06-01 (RT-03)", R(date(2000, 6, 1))["random_end"], "none")
        check("random_end 2010-06-01", R(date(2010, 6, 1))["random_end"], "conditional")
        check("fx_regime 1996-06-03 (RT-04)", R(date(1996, 6, 3))["fx_regime"], "market_average_rate")
        check("fx_regime 1998-06-01", R(date(1998, 6, 1))["fx_regime"], "free_float")
        check("price_limit 1995-02-01 stays null", R(date(1995, 2, 1))["price_limit"], None)

        print("KR market status on 2026-10-28 (every KR file now signed or simulated)")
        s = store.status("KR", date(2026, 10, 28), cal=cal)
        print(f"  KR: signed={s['signed']} refused={sorted(s['refused'])} sessions_left={s['sessions_left']}")
        check("KR signed", s["signed"], True)

    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
