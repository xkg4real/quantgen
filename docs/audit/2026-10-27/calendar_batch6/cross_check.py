"""Cross-check the proposed batch-5 holiday files against two calendar libraries (not sources, spec L2003).

Needs exchange_calendars and pandas_market_calendars, which the repository does not pin; install them in a separate
virtual environment and run this file from there:

    python -m venv /tmp/xvenv && /tmp/xvenv/bin/pip install exchange_calendars pandas_market_calendars pyyaml
    /tmp/xvenv/bin/python -I docs/audit/2026-10-27/calendar_batch6/cross_check.py

For each market it prints the weekday closures (closed rows) that only the proposed file has and those that only a
library has, restricted to the library's own range, and the early closes that differ.
"""
from __future__ import annotations

import importlib.metadata as md
from pathlib import Path

import exchange_calendars as xc
import pandas as pd
import pandas_market_calendars as pmc
import yaml

HERE = Path(__file__).resolve().parent
LO, HI = "2025-01-01", "2027-12-31"
LIBS = {"holidays_JPX": (("xc", "XTKS"), ("pmc", "JPX")), "holidays_SSE": (("xc", "XSHG"), ("pmc", "SSE")),
        "holidays_HKEX": (("xc", "XHKG"), ("pmc", "HKEX")), "holidays_TWSE": (("xc", "XTAI"),),
        "holidays_CME": (("pmc", "CME_Equity"),)}


def lib_dates(kind: str, code: str):
    if kind == "xc":
        c = xc.get_calendar(code, start="2024-01-01")
        hi = min(pd.Timestamp(HI), c.last_session)
        sess = set(c.sessions_in_range(LO, hi))
        early = {d.strftime("%Y-%m-%d"): c.closes[d].tz_convert(c.tz).strftime("%H:%M")
                 for d in c.early_closes if pd.Timestamp(LO) <= d <= hi}
    else:
        c = pmc.get_calendar(code)
        sched = c.schedule(LO, HI)
        hi = pd.Timestamp(HI)
        sess = set(sched.index)
        early = {i.strftime("%Y-%m-%d"): r.market_close.tz_convert(c.tz).strftime("%H:%M")
                 for i, r in c.early_closes(sched).iterrows()}
    closed = {d.strftime("%Y-%m-%d") for d in pd.bdate_range(LO, hi) if d not in sess}
    return closed, early, hi.strftime("%Y-%m-%d")


def main() -> None:
    print("exchange_calendars", md.version("exchange_calendars"), "| pandas_market_calendars",
          md.version("pandas_market_calendars"))
    for fid, libs in LIBS.items():
        doc = yaml.safe_load((HERE / "proposed" / f"{fid}.yaml").read_text(encoding="utf-8"))
        ours_closed = {r["date"] for r in doc["rows"] if r["kind"] == "closed"}
        ours_early = {r["date"]: r["close_local"] for r in doc["rows"] if r["kind"] == "early_close"}
        for kind, code in libs:
            closed, early, hi = lib_dates(kind, code)
            mine = {d for d in ours_closed if d <= hi}
            print(f"{fid} vs {kind}:{code} (to {hi}): proposed {len(mine)} closed, library {len(closed)}")
            print("   only proposed:", " ".join(sorted(mine - closed)) or "-")
            print("   only library: ", " ".join(sorted(closed - mine)) or "-")
            diff = sorted(set(ours_early) ^ {d for d in early if d <= hi})
            print("   early closes differ on:", " ".join(diff) or "-",
                  "| proposed times:", sorted(set(ours_early.values())), "library times:", sorted(set(early.values())))


if __name__ == "__main__":
    main()
