import math, sys
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.ficc import fx, structured as st, equity_deriv as ED
from core.ficc.common import UST_TENORS
from core.ficc.curves import bootstrap_par_curve
from core.ficc.swaps import black76
from core.ficc import insights

# 1. SABR 3-point fit: does it always fit exactly? negative BF, extreme RR
S, T, rd, rf = 1.10, 0.25, 0.043, 0.02
F = fx.forward(S, rd, rf, T)
for atm, rr, bf, TT in ((0.08, 0.005, 0.003, 0.25), (0.08, 0.0, -0.002, 0.25), (0.08, 0.04, 0.001, 0.25), (0.08, 0.005, 0.003, 2.0), (0.08, -0.03, 0.02, 1/52)):
    pts = fx.smile_from_quotes(fx.SmileQuote(TT, atm, rr, bf), S, rd, rf)
    FF = fx.forward(S, rd, rf, TT)
    fit = fx.calibrate_sabr(FF, TT, [p.strike for p in pts], [p.vol for p in pts], beta=1.0)
    print(f"SABR atm {atm} rr {rr} bf {bf} T {TT:.3f}: rmse {fit.rmse*100:.4f} vp, rho {fit.rho:+.3f}, nu {fit.nu:.3f}, conv {fit.converged}")

# 2. MFIV truncation with the 160-series cap (80 strikes) at index 1126
for vol, days in ((0.20, 20), (0.40, 15), (0.20, 79)):
    F0, r0, T0 = 1126.0, 0.032, days / 365
    df0 = math.exp(-r0 * T0)
    ks_all = np.arange(math.ceil(F0 * 0.9 / 2.5) * 2.5, F0 * 1.10 + 1e-9, 2.5)
    ks = np.array(sorted(sorted(ks_all, key=lambda k: abs(k - F0))[:80]))
    q = [ED.Quote(strike=float(k), call_mid=black76(F0, k, T0, vol, df0, True).price, put_mid=black76(F0, k, T0, vol, df0, False).price, call_bid=0.01, put_bid=0.01) for k in ks]
    mv = ED.mfiv(q, F0, T0, r0)
    print(f"MFIV cap80 vol {vol} days {days}: range {ks.min():.1f}-{ks.max():.1f} ({ks.min()/F0-1:+.3%}/{ks.max()/F0-1:+.3%}), mfiv {mv['vol']:.4f}, bias {(mv['vol']-vol)*100:+.2f} vp; n_all {len(ks_all)}")

# 3. M_O2 decomposition with the KIS-theo-implied dividend
Fut, Sp, cd, days, theo = 1127.75, 1126.12, 0.0321, 79.0, 1132.78
T2 = days / 365
fair0 = ED.fair_value(Sp, cd, T2)
D = fair0 - theo
rep = ED.basis_report(Fut, Sp, cd, T2, div_pts=D)
print(f"M_O2: fair(no div) {fair0:.2f}, KIS-implied div {D:.2f} pts, mispricing no-div {(Fut-fair0)/Sp/1e-4:+.1f}bp, with KIS div {rep.mispricing_bp:+.1f}bp, implied rate with div {rep.implied_rate:.4%}")

# 4. Steepener: first coupon vs schedule
par = [0.035, 0.036, 0.037, 0.038, 0.040, 0.041, 0.043, 0.044, 0.045, 0.047, 0.046]
c = bootstrap_par_curve(UST_TENORS, par, date="2026-09-04", source="TEST")
s = st.steepener_note(c, maturity=5.0, leverage=4.0, floor=0.0, cap=None, freq=1)
rows = st._cms_coupons(c, 5.0, 1, 4.0, 0.0, None)
print("steepener stat coupon", s.coupon, "schedule", [round(r[3], 5) for r in rows], "avg", sum(r[3] for r in rows)/len(rows))
print("narr:", [x for x in insights.narrate_structured(s).split(". ") if "coupon is" in x])
# synthetic screen curve too
from core.ficc.data import load_treasury_curve
from core.ficc.curves import curve_from_snapshot
panel = load_treasury_curve(source="synthetic"); cs = curve_from_snapshot(panel.latest())
s2 = st.steepener_note(cs, maturity=5.0, leverage=4.0, floor=0.0, cap=None, freq=1)
rows2 = st._cms_coupons(cs, 5.0, 1, 4.0, 0.0, None)
print("synthetic curve steepener fair", round(s2.fair_value, 4), "coupon stat", s2.coupon, "schedule", [round(r[3], 5) for r in rows2])

# 5. RC 18m effective annual coupon
rc = st.reverse_convertible(c, spot=1.10, vol=0.10, r_for_or_div=0.02, maturity=1.5, strike_pct=0.95)
print("RC 18m coupon", rc.coupon, "sum coupons/1.5y", 2 * rc.coupon / 1.5)

# 6. structuring: PPN on EQ underlying currency label
ppn = st.principal_protected_note(c, spot=400.0, vol=0.2, r_for_or_div=0.02, maturity=3.0, underlying="EQ")
print("PPN EQ currency", ppn.currency, "hedge unit", ppn.hedge[0].unit)

# 7. hedge sim GBM: displayed break-even approx sigma_h
hs = ED.hedge_pnl_simulation(spot=1126.0, strike=1125.0, horizon_days=14, sigma_hedge=0.395, rate=0.0321, n_paths=3000, seed=7)
print("GBM sim M_O1-like: mean", round(hs.mean_pnl_bp, 2), "se", round(hs.se_bp, 2), "be", round(hs.breakeven_vol, 4))
