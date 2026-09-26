"""Portfolio construction: Markowitz frontier, max-Sharpe, min-vol, risk parity.

scipy's SLSQP does the constrained optimization (long-only, fully invested,
optional per-asset cap). Risk parity is solved on the same machinery by
minimizing the dispersion of risk contributions. The efficient frontier is
traced by sweeping target returns between the min-vol portfolio's return and
the best single asset's, minimizing volatility at each stop.

Every optimizer starts from equal weights and the result reports whether the
solver actually converged — a portfolio built on a failed optimization is
worse than no portfolio, so `converged=False` is surfaced, never swallowed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize

from core.quant.risk import BasketStats, portfolio_point

OBJECTIVES = ("max_sharpe", "min_vol", "risk_parity", "equal_weight")


@dataclass(frozen=True)
class OptimizedPortfolio:
    objective: str
    symbols: tuple[str, ...]
    weights: np.ndarray = field(repr=False, default=None)
    ann_return: float = 0.0
    ann_vol: float = 0.0
    sharpe: float = 0.0
    converged: bool = True
    note: str = ""
    risk_contrib: np.ndarray = field(repr=False, default=None)  # fraction of total risk


@dataclass(frozen=True)
class Frontier:
    vols: np.ndarray = field(repr=False, default=None)
    rets: np.ndarray = field(repr=False, default=None)
    cloud_vols: np.ndarray = field(repr=False, default=None)    # random portfolios
    cloud_rets: np.ndarray = field(repr=False, default=None)
    cloud_sharpes: np.ndarray = field(repr=False, default=None)


def _risk_contributions(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    port_var = float(w @ cov @ w)
    if port_var <= 0:
        return np.full_like(w, 1.0 / w.size)
    marginal = cov @ w
    return w * marginal / port_var


def _solve(objective_fn, n: int, *, cap: float) -> tuple[np.ndarray, bool]:
    w0 = np.full(n, 1.0 / n)
    bounds = [(0.0, cap)] * n
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    res = minimize(objective_fn, w0, method="SLSQP", bounds=bounds,
                   constraints=cons, options={"maxiter": 500, "ftol": 1e-10})
    w = np.clip(res.x, 0.0, cap)
    s = w.sum()
    if s > 0:
        w = w / s
    return w, bool(res.success)


def optimize_portfolio(stats: BasketStats, *, objective: str = "max_sharpe",
                       rf_rate: float = 0.03, max_weight: float = 1.0) -> OptimizedPortfolio:
    objective = (objective or "max_sharpe").lower()
    if objective not in OBJECTIVES:
        raise ValueError(f"Unknown objective {objective!r}. One of {OBJECTIVES}.")
    n = len(stats.symbols)
    cap = float(min(max(max_weight, 1.0 / n + 1e-9), 1.0))
    mu, cov = stats.mean_returns, stats.cov

    note = ""
    if objective == "equal_weight":
        w, ok = np.full(n, 1.0 / n), True
    elif objective == "min_vol":
        w, ok = _solve(lambda w: w @ cov @ w, n, cap=cap)
    elif objective == "max_sharpe":
        def neg_sharpe(w):
            vol = np.sqrt(max(w @ cov @ w, 1e-12))
            return -((w @ mu - rf_rate) / vol)
        w, ok = _solve(neg_sharpe, n, cap=cap)
    else:  # risk_parity
        def rc_dispersion(w):
            rc = _risk_contributions(np.clip(w, 1e-9, None), cov)
            return float(np.sum((rc - 1.0 / n) ** 2))
        w, ok = _solve(rc_dispersion, n, cap=cap)
        note = "Weights equalize each asset's contribution to portfolio risk."

    ret, vol, sharpe = portfolio_point(w, stats, rf_rate=rf_rate)
    if not ok:
        note = (note + " " if note else "") + "Solver did not report convergence; treat weights as approximate."
    return OptimizedPortfolio(objective=objective, symbols=stats.symbols,
                              weights=w, ann_return=ret, ann_vol=vol,
                              sharpe=sharpe, converged=ok, note=note.strip(),
                              risk_contrib=_risk_contributions(w, cov))


def efficient_frontier(stats: BasketStats, *, points: int = 25,
                       rf_rate: float = 0.03, n_cloud: int = 1500,
                       seed: int = 11) -> Frontier:
    n = len(stats.symbols)
    mu, cov = stats.mean_returns, stats.cov

    lo = optimize_portfolio(stats, objective="min_vol", rf_rate=rf_rate)
    hi_ret = float(np.max(mu))
    targets = np.linspace(lo.ann_return, hi_ret, points)
    vols, rets = [], []
    for t in targets:
        cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
                {"type": "eq", "fun": lambda w, t=t: w @ mu - t}]
        res = minimize(lambda w: w @ cov @ w, np.full(n, 1.0 / n),
                       method="SLSQP", bounds=[(0.0, 1.0)] * n,
                       constraints=cons, options={"maxiter": 300, "ftol": 1e-10})
        if res.success:
            vols.append(float(np.sqrt(max(res.fun, 0.0))))
            rets.append(float(t))

    rng = np.random.default_rng(seed)
    raw = rng.dirichlet(np.ones(n), size=n_cloud)
    c_rets = raw @ mu
    c_vols = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", raw, cov, raw), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        c_sharpe = np.where(c_vols > 0, (c_rets - rf_rate) / c_vols, 0.0)

    return Frontier(vols=np.array(vols), rets=np.array(rets),
                    cloud_vols=c_vols, cloud_rets=c_rets, cloud_sharpes=c_sharpe)
