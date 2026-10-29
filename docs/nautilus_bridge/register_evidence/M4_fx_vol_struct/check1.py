import math, sys
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.ficc import fx, structured as st, equity_deriv as ED
from core.ficc.common import UST_TENORS
from core.ficc.curves import bootstrap_par_curve
par = [0.035, 0.036, 0.037, 0.038, 0.040, 0.041, 0.043, 0.044, 0.045, 0.047, 0.046]
c = bootstrap_par_curve(UST_TENORS, par, date="2026-09-04", source="TEST")

# 1. steepener default fair (FC-01 baseline 86.1175)
s = st.steepener_note(c, maturity=5.0, leverage=4.0, floor=0.0, cap=None, freq=1)
print("steep fair", round(s.fair_value, 4), "margin", round(s.margin, 4), [round(x/1e-4,1) for x in [r for r in []]])
rows = st._cms_coupons(c, 5.0, 1, 4.0, 0.0, None)
print("fwd spreads bp", [round(r[2]*1e4,1) for r in rows])
# 2. RC with 18m maturity: solved coupon, fair
rc = st.reverse_convertible(c, spot=1.10, vol=0.10, r_for_or_div=0.02, maturity=1.5, strike_pct=0.95)
print("RC 18m coupon", rc.coupon, "fair", rc.fair_value)
from core.ficc.bonds import Bond, cashflows
b = Bond(coupon=rc.coupon, maturity=1.5, freq=1, face=100.0, notional=1e6)
print("RC 18m cashflows", cashflows(b))
# 3. DCD default on this curve
d = st.dual_currency_deposit(c, spot=1350.0, vol=0.09, r_for=0.045, maturity=0.25, strike=1300.0, base_ccy="USD", quote_ccy="KRW")
print("DCD y", d.coupon, "dep", (1/c.df(0.25)-1)/0.25, "fair", d.fair_value)
# 4. FX page 25d strike at ATM vol then priced at SABR vol: realised delta
S, T, rd, rf = 1.10, 0.25, 0.043, 0.02
q = fx.SmileQuote(T, 0.08, 0.005, 0.003)
pts = fx.smile_from_quotes(q, S, rd, rf)
F = fx.forward(S, rd, rf, T)
fit = fx.calibrate_sabr(F, T, [x.strike for x in pts], [x.vol for x in pts], beta=1.0)
print("SABR rmse with 3 pts", fit.rmse, fit.converged)
K = fx.strike_from_delta(0.25, S, T, rd, rf, 0.08, call=True)
vk = float(fx.smile_curve(fit, F, T, np.array([K]))[0])
print("25d call: K", K, "vol at K", vk, "delta at SABR vol", fx.garman_kohlhagen(S, K, T, rd, rf, vk, True).delta_spot, "smile 25dC strike", pts[2].strike)
Kp = fx.strike_from_delta(0.25, S, T, rd, rf, 0.08, call=False)
vkp = float(fx.smile_curve(fit, F, T, np.array([Kp]))[0])
print("25d put: delta at SABR vol", fx.garman_kohlhagen(S, Kp, T, rd, rf, vkp, False).delta_spot)
# USDJPY premium-adjusted vs spot delta gap example
S2, rd2, rf2 = 150.0, 0.005, 0.043
k25 = fx.strike_from_delta(0.25, S2, T, rd2, rf2, 0.10, call=True)
g = fx.garman_kohlhagen(S2, k25, T, rd2, rf2, 0.10, True)
print("USDJPY 25d call spot delta", g.delta_spot, "PA delta", g.delta_spot - g.price / S2)
# 5. MFIV strike spacing error check via selfcheck flat board, spacing 2.5 (KOSPI200)
F0, r0, T0 = 1126.0, 0.032, 20/365
df0 = math.exp(-r0*T0)
from core.ficc.swaps import black76
for step in (2.5, 5.0):
    fq = [ED.Quote(strike=k, call_mid=black76(F0, k, T0, 0.2, df0, True).price, put_mid=black76(F0, k, T0, 0.2, df0, False).price, call_bid=0.01, put_bid=0.01) for k in np.arange(700, 1700, step)]
    print("mfiv step", step, ED.mfiv(fq, F0, T0, r0)["vol"])
# 6. LETF financing term omitted when rate not passed
v = np.full(63, 0.2**2/252)
print("letf +2 r=0", ED.letf_drag(2.0, v, fee=0.0064)["drag_bp"], "r=3%", ED.letf_drag(2.0, v, rate=0.03, fee=0.0064)["drag_bp"])
# 7. hedge sim dead param, and strike ATM-forward mismatch is page-level
hs = ED.hedge_pnl_simulation(spot=1120.0, strike=1120.0, horizon_days=20, sigma_hedge=0.2, rate=0.03, n_paths=2000, seed=3, cost_bps=0.0)
print("hedge mean bp", hs.mean_pnl_bp, "se", hs.se_bp, "be", hs.breakeven_vol)
