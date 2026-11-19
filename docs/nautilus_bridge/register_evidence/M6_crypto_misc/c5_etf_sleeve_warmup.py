"""ETF page sleeve stats (ui/etf_page.py:80-90): how much do the 210-session warm-up in cash (3 %/yr, zero vol)
and the non-excess Sharpe move the 'Trend switch Sharpe' on a driftless random walk (true edge 0)?"""
import sys, math
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.quant import strategies as S
rf = 0.03 / 252
res = []
for seed in range(400):
    rng = np.random.default_rng(seed)
    px = 100 * np.exp(np.cumsum(rng.normal(-0.5 * 0.012 ** 2, 0.012, 505)))     # 19 %/yr vol, zero expected return
    W = S.trend_switch(px[:, None], rule="sma", lookback=210, step=21, cash_rate_daily=rf)
    pt, _ = S.simulate(px[:, None], W, cost_bps=3.0, cash_daily=rf)
    full = S.summary(pt)["sharpe"]
    post = S.summary(pt[210:])["sharpe"]
    excess = (np.mean(pt - rf) * 252) / (np.std(pt, ddof=1) * math.sqrt(252))
    bh = S.summary(px[1:] / px[:-1] - 1)["sharpe"]
    res.append((full, post, excess, bh))
r = np.array(res)
print("driftless walk, 504 sessions, 400 seeds: mean page 'Trend Sharpe' %.2f | after warm-up only %.2f | "
      "page window but excess of 3%% cash %.2f | B&H Sharpe %.2f" % tuple(r.mean(axis=0)))
print("share of seeds where page trend Sharpe > B&H Sharpe: %.2f" % np.mean(r[:, 0] > r[:, 3]))
big = np.abs(r[:, 0]) > 10
print("share of seeds with |page trend Sharpe| > 10 (all-cash window, std of a constant cash series ~1e-19): %.3f" % big.mean())
ok = ~big
print("excluding those: median page trend Sharpe %.2f | after warm-up %.2f | excess-of-cash %.2f | B&H %.2f"
      % tuple(np.median(r[ok], axis=0)))
i = int(np.argmax(big))
print("example seed", i, "page trend Sharpe", r[i, 0])
