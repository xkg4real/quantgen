"""DIDM Version 0, Stage B: panel local projections with date fixed effects (Notion DIDM 5.1).

    r_{i,t->t+h} = sum_j b_{h,j} x_{j,i,t} + mu_{h,t} + e_{i,t+h},      h in horizons

``r_{i,t->t+h}`` is the cumulative abnormal return over days t..t+h, so ``b_h`` is the
cumulative response to a unit of regressor j. The date effect mu_t is removed by
subtracting each date's cross-sectional mean (balanced panel). Standard errors are
Driscoll-Kraay: the per-date sums of x*e are treated as one time series and given a
Bartlett (Newey-West) long-run variance, which allows any cross-sectional dependence
and the serial correlation that overlapping horizons create.

Each fit keeps its per-date influence series, so functions of coefficients from
different horizons (the delayed-pricing share) get a joint covariance.

numpy only; no network, no clock reads.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

Z90 = 1.6448536269514722      # two-sided 90% normal quantile
Z95 = 1.959963984540054       # two-sided 95% normal quantile


class ModelError(ValueError):
    pass


def hac_lags(horizon: int) -> int:
    """Bartlett truncation lag for a horizon-h projection: ceil(1.5 * h) (registered, Stage 0 V0)."""
    return int(math.ceil(1.5 * horizon))


def bartlett_cov(series: np.ndarray, lags: int) -> np.ndarray:
    """Long-run covariance of the *sum* of a (T, p) series (not mean-centred: these are moment sums)."""
    cov = series.T @ series
    for lag in range(1, min(lags, len(series) - 1) + 1):
        weight = 1.0 - lag / (lags + 1.0)
        cross = series[lag:].T @ series[:-lag]
        cov += weight * (cross + cross.T)
    return cov


def normal_p_two_sided(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def normal_p_upper(z: float) -> float:
    """P(Z > z)."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


@dataclass(frozen=True)
class HorizonFit:
    horizon: int
    coef: np.ndarray           # (p,)
    cov: np.ndarray            # (p, p) Driscoll-Kraay
    influence: np.ndarray      # (T, p); zero rows where the horizon runs past the sample
    n_dates: int

    @property
    def se(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))


@dataclass(frozen=True)
class LPFit:
    names: tuple[str, ...]
    fits: dict[int, HorizonFit]

    def coef(self, name: str, horizon: int) -> float:
        return float(self.fits[horizon].coef[self.names.index(name)])

    def se(self, name: str, horizon: int) -> float:
        return float(self.fits[horizon].se[self.names.index(name)])

    def interval(self, name: str, horizon: int, z: float = Z90) -> tuple[float, float]:
        b, s = self.coef(name, horizon), self.se(name, horizon)
        return b - z * s, b + z * s


def _check_panel(returns: np.ndarray, regressors: np.ndarray, names) -> None:
    if returns.ndim != 2 or regressors.ndim != 3 or regressors.shape[:2] != returns.shape:
        raise ModelError("returns must be (T, N) and regressors (T, N, p)")
    if regressors.shape[2] != len(names) or len(set(names)) != len(names) or not names:
        raise ModelError("one distinct name per regressor is required")
    if returns.shape[1] < 2:
        raise ModelError("date fixed effects need at least two units")
    if not (np.isfinite(returns).all() and np.isfinite(regressors).all()):
        raise ModelError("returns and regressors must be finite")


def cumulative_returns(returns: np.ndarray, horizon: int) -> np.ndarray:
    """(T - h, N) array of sum_{j=0..h} r[t + j]."""
    total = np.cumsum(returns, axis=0)
    out = total[horizon:].copy()
    out[1:] -= total[: len(total) - horizon - 1]
    return out


def fit_lp(returns: np.ndarray, regressors: np.ndarray, names: tuple[str, ...],
           horizons: tuple[int, ...] = (0, 1, 5, 20)) -> LPFit:
    returns = np.asarray(returns, dtype=float)
    regressors = np.asarray(regressors, dtype=float)
    names = tuple(names)
    _check_panel(returns, regressors, names)
    n_dates_all = returns.shape[0]
    x_all = regressors - regressors.mean(axis=1, keepdims=True)
    fits: dict[int, HorizonFit] = {}
    for h in horizons:
        if isinstance(h, bool) or not isinstance(h, int) or h < 0 or h >= n_dates_all - len(names) - 1:
            raise ModelError(f"horizon {h!r} does not fit the sample")
        y = cumulative_returns(returns, h)
        y = y - y.mean(axis=1, keepdims=True)
        x = x_all[: len(y)]
        xtx = np.einsum("tnp,tnq->pq", x, x)
        try:
            xtx_inv = np.linalg.inv(xtx)
        except np.linalg.LinAlgError:
            raise ModelError("regressors are collinear after removing date effects") from None
        if not np.isfinite(xtx_inv).all() or np.linalg.cond(xtx) > 1e12:
            raise ModelError("regressors are collinear after removing date effects")
        coef = xtx_inv @ np.einsum("tnp,tn->p", x, y)
        resid = y - x @ coef
        moments = np.einsum("tnp,tn->tp", x, resid)
        influence = np.zeros((n_dates_all, len(names)))
        influence[: len(y)] = moments @ xtx_inv.T
        fits[h] = HorizonFit(h, coef, bartlett_cov(influence[: len(y)], hac_lags(h)), influence, len(y))
    return LPFit(names, fits)


def predict(coef: np.ndarray, regressors: np.ndarray) -> np.ndarray:
    """Date-demeaned prediction x_demeaned @ coef for a (T, N, p) block (compare with date-demeaned outcomes)."""
    x = regressors - regressors.mean(axis=1, keepdims=True)
    return x @ coef


@dataclass(frozen=True)
class Ratio:
    value: float
    se: float

    def interval(self, z: float = Z90) -> tuple[float, float]:
        return self.value - z * self.se, self.value + z * self.se


def delayed_share(fit: LPFit, name: str, h0: int = 0, h1: int = 20) -> Ratio:
    """delta = (Theta_h1 - Theta_h0) / Theta_h1: the share of the cumulative response that arrives after h0.

    Delta-method standard error from the joint Driscoll-Kraay covariance of the two horizons.
    The ratio is unstable when Theta_h1 is near zero; the caller reads the interval, not the point.
    """
    j = fit.names.index(name)
    a, b = fit.fits[h0], fit.fits[h1]
    t0, t1 = float(a.coef[j]), float(b.coef[j])
    if t1 == 0.0:
        raise ModelError("cumulative response at the long horizon is exactly zero")
    stacked = np.column_stack([a.influence[:, j], b.influence[:, j]])
    cov = bartlett_cov(stacked, hac_lags(max(h0, h1)))
    grad = np.array([-1.0 / t1, t0 / t1 ** 2])
    var = float(grad @ cov @ grad)
    return Ratio(1.0 - t0 / t1, math.sqrt(max(var, 0.0)))


def dm_test(loss_a: np.ndarray, loss_b: np.ndarray, lags: int | None = None) -> tuple[float, float]:
    """Diebold-Mariano on per-date losses. Returns (statistic, one-sided p that model B has lower loss).

    statistic > 0 means model A's loss is larger. Bartlett long-run variance, lag ceil(n ** (1/3)) by default.
    """
    d = np.asarray(loss_a, dtype=float) - np.asarray(loss_b, dtype=float)
    if d.ndim != 1 or len(d) < 10 or not np.isfinite(d).all():
        raise ModelError("losses must be two finite series of at least 10 dates")
    n = len(d)
    if lags is None:
        lags = int(math.ceil(n ** (1.0 / 3.0)))
    centred = (d - d.mean()).reshape(-1, 1)
    var = float(bartlett_cov(centred, lags)[0, 0]) / n ** 2
    if var <= 0.0:
        return (0.0, 0.5) if d.mean() == 0 else (math.copysign(math.inf, d.mean()), 0.0 if d.mean() > 0 else 1.0)
    stat = float(d.mean()) / math.sqrt(var)
    return stat, normal_p_upper(stat)
