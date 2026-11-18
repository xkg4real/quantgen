"""Which Strategy Lab crypto_trend grid values give identical weight paths (duplicate trials)?"""
import sys
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.quant import strategies as S
rng = np.random.default_rng(5)
P = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.035, 2500)))
lab = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
study = [0.0, 0.222, 0.444, 0.667, 0.889]
W = {h: S.crypto_trend(P, hysteresis=h)[:, 0] for h in lab + study}
for grid, name in ((lab, "Lab grid"), (study, "study grid")):
    pairs = [(a, b) for i, a in enumerate(grid) for b in grid[i + 1:] if np.array_equal(W[a], W[b])]
    print(name, grid, "identical pairs:", pairs, "distinct rules:", len({W[h].tobytes() for h in grid}))
