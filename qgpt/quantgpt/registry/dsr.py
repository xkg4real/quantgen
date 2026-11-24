"""Deflated Sharpe ratio, standard library only.

The formulas restate the host application's definitions so that a ledger here
and the validation gate there discount a result by the same amount:

* ``expected_max_sharpe``  E[max of N null Sharpe ratios] ~ sd * [(1-g) * Z(1-1/N) + g * Z(1-1/(N e))],
  0 for N = 1 (g is the Euler-Mascheroni constant, Z the normal quantile).
* ``deflated_sharpe``      Phi((SR - SR0) * sqrt(T-1) / sqrt(1 - g3*SR + (g4-1)/4 * SR^2)) on per-period
  returns, with SR0 the expected maximum above; sample sd with T-1, skewness and kurtosis with T.
* ``deflated_delta``       Phi((delta - se_null * hurdle) / se_obs).

Callers outside this package do not pass a trial count: ``AttemptLedger.deflated_sharpe`` takes it from
the ledger.
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Sequence

EULER_GAMMA = 0.5772156649015329
_NORMAL = NormalDist()


def expected_max_sharpe(n_trials: int, sr_sd: float) -> float:
    n = max(int(n_trials), 1)
    if n == 1:
        return 0.0
    return sr_sd * ((1 - EULER_GAMMA) * _NORMAL.inv_cdf(1 - 1.0 / n)
                    + EULER_GAMMA * _NORMAL.inv_cdf(1 - 1.0 / (n * math.e)))


def moments(returns: Sequence[float]) -> tuple[float, float, float, int]:
    """(per-period Sharpe, skewness, kurtosis, T); a constant series has Sharpe 0, skew 0, kurtosis 3."""
    x = [float(v) for v in returns]
    t = len(x)
    if t < 3:
        raise ValueError("need at least 3 observations")
    if not all(math.isfinite(v) for v in x):
        raise ValueError("returns must be finite")
    mean = sum(x) / t
    m2 = sum((v - mean) ** 2 for v in x) / t
    if m2 <= 0:
        return 0.0, 0.0, 3.0, t
    sd = math.sqrt(m2 * t / (t - 1))
    m3 = sum((v - mean) ** 3 for v in x) / t
    m4 = sum((v - mean) ** 4 for v in x) / t
    return mean / sd, m3 / m2 ** 1.5, m4 / m2 ** 2, t


def per_period_sharpe(returns: Sequence[float]) -> float:
    return moments(returns)[0]


def population_sd(values: Sequence[float]) -> float:
    """Dispersion of the trials' Sharpe ratios (divides by the count, as the host does); 0 for one value."""
    values = [float(v) for v in values]
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def deflated_sharpe(returns: Sequence[float], *, n_trials: int, sr_sd: float) -> float:
    sr, g3, g4, t = moments(returns)
    sr0 = expected_max_sharpe(n_trials, sr_sd)
    denom = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr ** 2
    if denom <= 0:
        return math.nan
    return _NORMAL.cdf((sr - sr0) * math.sqrt(t - 1) / math.sqrt(denom))


def deflated_delta(delta_sr: float, se_obs: float, se_null: float, hurdle: float) -> float:
    if not (se_obs > 0) or not (se_null >= 0):
        raise ValueError("deflated_delta needs se_obs > 0 and se_null >= 0")
    return _NORMAL.cdf((delta_sr - se_null * hurdle) / se_obs)
