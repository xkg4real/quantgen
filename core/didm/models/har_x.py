"""DIDM Version 0, Stage C: HAR-X volatility regression (Notion DIDM 5.1).

    x_{i,t+1} = c_i + b_d x_{i,t} + b_w mean(x_{i,t-4..t}) + b_m mean(x_{i,t-21..t}) + g' z_{i,t} + e_{i,t+1}

with x = log realised variance and z the news regressors (|shock|, direction-probability
entropy). Unit effects c_i are removed by within-unit demeaning (T is long, so the dynamic-
panel bias of order 1/T is ignored). Standard errors are Driscoll-Kraay with a short lag.

numpy only; no network, no clock reads.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.didm.models.lp import Z90, ModelError, bartlett_cov

HAR_NAMES = ("har_d", "har_w", "har_m")
WARMUP = 22
SE_LAGS = 5


def har_features(log_rv: np.ndarray) -> np.ndarray:
    """(T, N, 3): daily value, 5-day mean and 22-day mean, each ending at t. Rows before day 21 are NaN."""
    log_rv = np.asarray(log_rv, dtype=float)
    if log_rv.ndim != 2 or len(log_rv) <= WARMUP + 5:
        raise ModelError("log_rv must be (T, N) with more than 27 dates")
    total = np.cumsum(np.vstack([np.zeros((1, log_rv.shape[1])), log_rv]), axis=0)
    out = np.full(log_rv.shape + (3,), np.nan)
    out[..., 0] = log_rv
    out[4:, :, 1] = (total[5:] - total[:-5]) / 5.0
    out[21:, :, 2] = (total[22:] - total[:-22]) / 22.0
    return out


@dataclass(frozen=True)
class HarFit:
    names: tuple[str, ...]
    coef: np.ndarray
    cov: np.ndarray
    unit_effects: np.ndarray     # (N,)
    resid_var: float

    @property
    def se(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))

    def value(self, name: str) -> float:
        return float(self.coef[self.names.index(name)])

    def interval(self, name: str, z: float = Z90) -> tuple[float, float]:
        j = self.names.index(name)
        return float(self.coef[j] - z * self.se[j]), float(self.coef[j] + z * self.se[j])


def design(log_rv: np.ndarray, extra: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    """Target x_{t+1} and regressors at t for t = 21 .. T-2: (T-22, N) and (T-22, N, 3 + q)."""
    feats = har_features(log_rv)
    if extra is not None:
        extra = np.asarray(extra, dtype=float)
        if extra.ndim != 3 or extra.shape[:2] != log_rv.shape:
            raise ModelError("extra regressors must be (T, N, q)")
        feats = np.concatenate([feats, extra], axis=2)
    x = feats[WARMUP - 1: -1]
    y = np.asarray(log_rv, dtype=float)[WARMUP:]
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ModelError("log_rv and regressors must be finite")
    return y, x


def fit_har_x(log_rv: np.ndarray, extra: np.ndarray | None = None, extra_names: tuple[str, ...] = ()) -> HarFit:
    y, x = design(log_rv, extra)
    names = HAR_NAMES + tuple(extra_names)
    if x.shape[2] != len(names) or len(set(names)) != len(names):
        raise ModelError("one distinct name per extra regressor is required")
    y_mean, x_mean = y.mean(axis=0), x.mean(axis=0)
    yd, xd = y - y_mean, x - x_mean
    xtx = np.einsum("tnp,tnq->pq", xd, xd)
    if np.linalg.cond(xtx) > 1e12:
        raise ModelError("HAR-X regressors are collinear")
    xtx_inv = np.linalg.inv(xtx)
    coef = xtx_inv @ np.einsum("tnp,tn->p", xd, yd)
    resid = yd - xd @ coef
    influence = np.einsum("tnp,tn->tp", xd, resid) @ xtx_inv.T
    return HarFit(names, coef, bartlett_cov(influence, SE_LAGS), y_mean - x_mean @ coef, float(resid.var()))


def predict(fit: HarFit, log_rv: np.ndarray, extra: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(actual, predicted) next-day log RV for t = 21 .. T-2, using the fitted unit effects."""
    y, x = design(log_rv, extra)
    if x.shape[2] != len(fit.names):
        raise ModelError("regressors do not match the fitted model")
    return y, x @ fit.coef + fit.unit_effects
