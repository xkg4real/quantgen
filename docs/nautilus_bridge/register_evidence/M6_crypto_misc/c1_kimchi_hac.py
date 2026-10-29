"""Compare kimchi_premium's pred_t with statsmodels OLS HAC (Bartlett, maxlags=6) on synthetic data,
and measure the null rejection rate of |t|>2 for the code's t."""
import sys, math
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
import statsmodels.api as sm
from core.crypto import analytics as CA

def one(seed, n=1500):
    rng = np.random.default_rng(seed)
    ds = [str(np.datetime64("2020-01-01") + np.timedelta64(i, "D")) for i in range(n)]
    us = 30000 * np.exp(np.cumsum(rng.normal(0.0, 0.035, n)))       # BTC independent of premium (null)
    fx = 1300 + np.cumsum(rng.normal(0, 3, n))
    p = np.zeros(n)
    for t in range(1, n):
        p[t] = 0.95 * p[t - 1] + rng.normal(0, 0.4)
    kr = us * fx * (1 + p / 100)
    kp = CA.kimchi_premium(dict(zip(ds, kr)), dict(zip(ds, us)), dict(zip(ds, fx)))
    z = kp.z_1y; h = 7
    fwd = np.full(n, np.nan); fwd[:-h] = np.log(us[h:] / us[:-h])
    ok = np.isfinite(z) & np.isfinite(fwd)
    X = sm.add_constant(z[ok])
    res = sm.OLS(fwd[ok], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": False})
    return kp.pred_slope, kp.pred_t, float(res.params[1]), float(res.tvalues[1]), int(ok.sum())

rows = [one(s) for s in range(200)]
r0 = rows[0]
print("seed0: code slope %.6f t %.3f | statsmodels slope %.6f t %.3f | n_ok %d | ratio t_code/t_sm %.2f sqrt(n) %.2f"
      % (r0[0], r0[1], r0[2], r0[3], r0[4], r0[1] / r0[3], math.sqrt(r0[4])))
ratios = np.array([r[1] / r[3] for r in rows]); n_ok = np.array([r[4] for r in rows])
print("median t_code/t_sm %.2f, median sqrt(n_ok) %.2f" % (np.median(ratios), np.median(np.sqrt(n_ok))))
tc = np.array([r[1] for r in rows]); ts = np.array([r[3] for r in rows])
print("null share |t|>2: code %.2f, statsmodels HAC %.2f (200 sims, BTC independent of the premium)" % (np.mean(abs(tc) > 2), np.mean(abs(ts) > 2)))
print("card M_C1_kimchi pred_t 6.145 on n=3288 -> corrected approx", 6.145 / math.sqrt(3288 - 365 - 7))
