"""Null rejection rate of funding_carry's bootstrap p (gate: p < 0.05) when funding is independent of BTC.
Funding is persistent (AR(1) daily, phi 0.98) as real funding is; forward 30-day returns overlap."""
import sys
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.crypto.analytics import funding_carry

def sim(seed, n=2573, phi=0.98):
    rng = np.random.default_rng(seed)
    ds = [str(np.datetime64("2019-09-10") + np.timedelta64(i, "D")) for i in range(n)]
    px = 10000 * np.exp(np.cumsum(rng.normal(0.0005, 0.035, n)))
    f = np.zeros(n); f[0] = 0.0003
    for t in range(1, n):
        f[t] = 0.0003 * (1 - phi) + phi * f[t - 1] + rng.normal(0, 0.0002)
    fc = funding_carry(dict(zip(ds, f)), dict(zip(ds, px)))
    return fc.bootstrap_p

ps = np.array([sim(s) for s in range(300)])
print("sims", ps.size, "share p<0.05 (false 'BIS sign confirmed'):", round(float(np.mean(ps < 0.05)), 3),
      "share p>0.95:", round(float(np.mean(ps > 0.95)), 3), "nominal 0.05 each")
