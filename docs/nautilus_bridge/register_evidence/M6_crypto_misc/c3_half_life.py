"""half_life() on fast-reverting series: phi <= 0 returns inf, which the ETF narrative reads as 'slow-moving'."""
import sys, math
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.quant import strategies as S
rng = np.random.default_rng(1)
n = 504
cases = {"white noise (phi 0)": rng.normal(0, 0.1, n),
         "AR(1) phi -0.3": None, "AR(1) phi 0.3": None, "test premium 0.2*sin(1.7 t)": 0.2 * np.sin(np.arange(400) * 1.7)}
for phi in (-0.3, 0.3):
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal(0, 0.1)
    cases[f"AR(1) phi {phi}"] = x
share_inf = np.mean([math.isinf(S.half_life(rng.normal(0, 0.1, n))) for _ in range(500)])
for k, x in cases.items():
    hl = S.half_life(x)
    text = ("reverts within days" if hl < 5 else "slow-moving enough to matter for entry timing")
    print(f"{k:32s} half_life={hl:8.3f}  ETF narrative -> {text}; chip 'half-life {hl:.0f} sessions'")
print("white noise n=504: share of draws with half_life = inf:", share_inf)
