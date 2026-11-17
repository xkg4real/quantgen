"""Hermetic probe of core/ficc/lag_audit.py behaviour (no market data, no network, no writes into the repo)."""
import sys
from datetime import date, datetime, timedelta, timezone
R = sys.argv[1]
sys.path.insert(0, R)
from core.ficc import contracts as C, pit as P, lag_audit as L
UTC = timezone.utc
def U(*a): return datetime(*a, tzinfo=UTC)
REG = C.load_registry()

class Stub:
    def close_print_bound_utc(self, market, d):
        if market == "KR": return U(d.year, d.month, d.day, 6, 30, 30)
        if market == "US": return U(d.year, d.month, d.day, 20, 0, 30)
        if market in ("JP", "CN", "HK", "TW"): return U(d.year, d.month, d.day, 7, 0, 0)
        raise KeyError(market)
    def publication_instant(self, sid, d):
        return None
CLK = Stub()

def close(sid, d, status="official_close", role="acting_exposure", books=("specification",), session=None, retrieved=None):
    m = REG.market(sid)
    b = CLK.close_print_bound_utc(m, d)
    row = P.make_row(series_id=sid, value=1.0, obs_date=d, session_date=session or d, obs_utc=b, obs_kind="close",
                     value_status=status, available_at_utc=b, available_at_source="calendar_bound",
                     retrieved_at_utc=retrieved or b + timedelta(minutes=11), vintage=None, source="KRX", channel=None)
    return row, P.to_value(row, role=role, books=books)

OCT1, OCT2, OCT5 = date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 5)
KR_DEC = U(2026, 10, 2, 6, 30, 30)
live = P.RunContext(KR_DEC, KR_DEC + timedelta(hours=1), "live")

# P1: derived acting input whose lineage input is a later (look-ahead) close; lineage not passed vs passed
_, future_in = close("KOSPI_OFFICIAL_CLOSE", OCT5)
drow = P.make_row(series_id="DM_MKT_VOL_126", value=0.2, obs_date=OCT2, session_date=None, obs_utc=KR_DEC - timedelta(minutes=1),
                  obs_kind="derived", value_status="official_close", available_at_utc=KR_DEC - timedelta(minutes=1),
                  available_at_source="calendar_bound", retrieved_at_utc=KR_DEC - timedelta(minutes=1), vintage=None,
                  source="derived", channel=None, inputs=[future_in.content_hash])
dv = P.to_value(drow, role="acting_exposure", books=("specification",))
print("P1 derived, no lineage   :", L.lag_audit([dv], live, "US", REG, CLK))
print("P1 derived, with lineage :", [x["check"] for x in L.lag_audit([dv], live, "US", REG, CLK, lineage={dv.content_hash: [future_in]})["violations"]])

# P2: an official close of the PREVIOUS session (obs_date = session_date = 1 Oct) audited at the 2 Oct KR decision
_, prev = close("KOSPI_OFFICIAL_CLOSE", OCT1)
print("P2 prior-session close   :", L.lag_audit([prev], live, "KR", REG, CLK))

# P3: a live-quote risk_model input dated AFTER the decision date but stamped before the decision
q = P.make_row(series_id="USD_LIVE_PROXY", value=100.0, obs_date=OCT5, session_date=None, obs_utc=KR_DEC - timedelta(minutes=1),
               obs_kind="quote_snapshot", value_status="live_snapshot", available_at_utc=KR_DEC - timedelta(minutes=1),
               available_at_source="published", retrieved_at_utc=KR_DEC - timedelta(minutes=1), vintage=None, source="X", channel=None)
print("P3 live quote dated D+3  :", L.lag_audit([P.to_value(q, role="risk_model", books=())], live, "KR", REG, CLK))

# P4: a forward_sim close of a market the clocks do not know (DE) -> exception, not a recorded violation
_, dax = close("NIKKEI225_CLOSE", OCT1, role="forward_sim", books=("forward_sim:R-28",))
dax_row = {**{k: getattr(dax, k) for k in P._ROW_FIELDS if k != "content_hash"}, "series_id": "DAX_MONTH_END_CLOSE"}
daxv = P.to_value(P.make_row(**dax_row), role="forward_sim", books=("forward_sim:R-28",))
try:
    print("P4 DE close (stub)       :", L.lag_audit([daxv], live, "KR", REG, CLK))
except Exception as e:
    print("P4 DE close (stub)       : raised", type(e).__name__, e)

# P5: the same with the shipped calendar adapter (signed calendar files; reference data only)
from core.calendars.adapter import CalendarClocks
real = CalendarClocks(REG)
for label, v, mkt in (("DAX_MONTH_END_CLOSE forward_sim", daxv, "KR"),):
    try:
        print("P5", label, ":", L.lag_audit([v], live, mkt, REG, real))
    except Exception as e:
        print("P5", label, ": raised", type(e).__name__, str(e)[:200])
# P6: RawFrameRead is only raised for a non-PITValue element of `inputs`
try:
    L.lag_audit([{"series_id": "KOSPI_OFFICIAL_CLOSE"}], live, "KR", REG, CLK)
except L.RawFrameRead as e:
    print("P6 dict input            : RawFrameRead", e)
# P7: assert_no_positional_shift with unsorted/duplicate dates and the default monthly rule on daily dates
try:
    L.assert_no_positional_shift([date(2026, 10, 1), date(2026, 10, 2)], 1)
    print("P7 daily dates, default monthly rule: accepted")
except L.PositionalShiftRejected as e:
    print("P7 daily dates, default monthly rule: rejected", e)
try:
    L.assert_no_positional_shift([date(2026, 1, 1), date(2026, 1, 1), date(2026, 2, 1)], 1)
    print("P7 duplicate month: accepted")
except L.PositionalShiftRejected as e:
    print("P7 duplicate month: rejected", e)
