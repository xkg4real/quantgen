"""Read-only, synthetic diagnostics for section 10 triage; no gate re-scoring.

Run with ``python -m tools.status.section10_probes``. Output describes current
behaviour, not a passing research verdict or a declaration that defects are fixed.
"""
from __future__ import annotations

from datetime import date, timedelta
import json
import math
from unittest.mock import patch

import dotenv
import numpy as np
from scipy.stats import chi2


def collect() -> dict:
    with patch.object(dotenv, "load_dotenv", return_value=False):
        from core.quant import validate, strategies
        from core.quant.optimize import optimize_portfolio
        from core.quant.risk import BasketStats
        from core.crypto.analytics import kimchi_premium

    findings = {}
    n, alpha = 200, .01
    found = validate.kupiec(np.zeros(n), alpha)
    exact_lr = -2 * n * math.log1p(-alpha)
    findings["N-M1-01"] = {
        "n": n, "exceptions": 0, "alpha": alpha,
        "current_p": found["p"], "likelihood_ratio_p": float(chi2.sf(exact_lr, 1)),
        "note": "Boundary statistic differs; no stored grade or gate rule changed.",
    }

    rng = np.random.default_rng(81030)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, .004, size=(300, 4)), axis=0))
    weights = strategies.vol_target(prices, target=.12, cap=1)
    findings["N1"] = {"assets": 4, "per_asset_cap": 1,
                      "max_gross_exposure": float(np.abs(weights).sum(axis=1).max()),
                      "note": "A per-asset cap is not a portfolio gross-exposure limit."}

    stats = BasketStats(symbols=("A", "B", "C"), sessions=252,
                        mean_returns=np.array([-.02, -.05, 0]),
                        cov=np.diag(np.array([.1, .4, .2])**2))
    portfolio = optimize_portfolio(stats, rf_rate=.03)
    findings["N-M1-09"] = {"weights": portfolio.weights.tolist(), "sharpe": portfolio.sharpe,
                           "converged": portfolio.converged, "note_from_optimizer": portfolio.note,
                           "note": "Negative-Sharpe optimum is not an arithmetic failure; warning/model choice needs separate handling."}

    # Independent Newey-West sandwich calculation, without calling the
    # implementation's scalar HAC helper or changing its returned values.
    size, horizon = 540, 7
    keys = [(date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(size)]
    btc = 100 * np.exp(np.cumsum(rng.normal(.0002, .01, size)))
    premium = rng.normal(.02, .004, size)
    result = kimchi_premium(dict(zip(keys, btc * 1300 * (1 + premium))),
                            dict(zip(keys, btc)), dict(zip(keys, np.full(size, 1300.))))
    forward = np.full(size, np.nan)
    forward[:-horizon] = np.log(btc[horizon:] / btc[:-horizon])
    mask = np.isfinite(result.z_1y) & np.isfinite(forward)
    X = np.column_stack((np.ones(mask.sum()), result.z_1y[mask]))
    y = forward[mask]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    score = X * (y - X @ beta)[:, None]
    meat = score.T @ score
    for lag in range(1, horizon):
        cross = score[lag:].T @ score[:-lag]
        meat += (1 - lag / horizon) * (cross + cross.T)
    bread = np.linalg.inv(X.T @ X)
    oracle_t = float(beta[1] / math.sqrt((bread @ meat @ bread)[1, 1]))
    findings["NEW-M6-01"] = {"observations": int(mask.sum()), "current_t": result.pred_t,
                             "sandwich_t": oracle_t, "ratio": result.pred_t / oracle_t,
                             "sqrt_n": math.sqrt(mask.sum())}

    oscillating = np.zeros(400)
    for i in range(1, len(oscillating)):
        oscillating[i] = -.7 * oscillating[i - 1] + rng.normal(0, .1)
    half = strategies.half_life(oscillating)
    findings["NEW-M6-03"] = {"generating_phi": -.7, "current_half_life": "infinite" if math.isinf(half) else half,
                             "note": "Stationary alternating process; infinite output must not imply non-stationarity."}
    return {"mode": "synthetic_read_only", "seed": 81030, "findings": findings,
            "actual_data_or_ledgers_used": False, "corrections_applied": False}


def main() -> None:
    # These probes must never fall back to a provider if a dependency changes.
    with patch("socket.socket.connect", side_effect=AssertionError("Probe network access forbidden")), \
            patch("socket.create_connection", side_effect=AssertionError("Probe network access forbidden")):
        print(json.dumps(collect(), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
