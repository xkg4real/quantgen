"""LA-01 pipeline reproduction on a synthetic store (no market data, no network).
Case A: NAV line close absent -> how data_ok classifies it.
Case B: NAV line close present but stamped available_at 06:00Z (before the 06:30:30Z bound) -> lag_audit violation; who HALTs."""
import sys
from datetime import date, timedelta, datetime, timezone
R = sys.argv[1]; sys.path.insert(0, R)
import tests.macro_m8_pipeline as T
from core.ficc import pit as P
from core.engine import books as B
NAV = "KRX_069500_OFFICIAL_CLOSE"

def build(nav_mode):
    store, days, px = T._kospi_store(40, scale_sigma_to=0.2882)
    rows = T.kr_rows(days, px, nav=(nav_mode == "ok"))
    if nav_mode == "early":
        for i, d in enumerate(days):
            bound = T.CLK.close_print_bound_utc("KR", d)
            early = bound.replace(hour=6, minute=0, second=0) if d == days[-1] else None
            rows.append(T._close_row(NAV, d, px[i] * 10.0, market="KR", available=early))
    hs = T._hedge_store()
    for sid in hs.series_ids():
        rows += hs.rows(sid)
    store.append(rows)
    return store, days

for mode in ("ok", "absent", "early"):
    tmp = T._tmp("la01_")
    store, days = build(mode)
    s = T.services(tmp, store, None)
    rec = T.run(s, "KR", T.OCT2)
    dok = T.step(rec, "data_ok")["result"]
    la = T.step(rec, "macro.lag_audit")["result"]
    fc = sorted({c["series_id"] for c in dok.get("fail_closed", [])})
    ff = {b: v for b, v in dok.get("forward_failed", {}).items()}
    viol = sorted({v["series_id"] + ":" + v["check"] for v in la.get("violations", [])})
    print(f"[{mode}] last day {days[-1]} data_ok.status={dok.get('status')} fail_closed={fc} forward_failed={ff}")
    print(f"[{mode}] lag_audit.status={la.get('status')} violations={viol} halted={la.get('halted')}")
    st = T.state_of(tmp, rec)
    print(f"[{mode}] runtime=" + str([(e.get('book_id'), e.get('engine_state')) for e in st.get('runtime', [])]))
