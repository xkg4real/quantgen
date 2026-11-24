"""DIDM Stage 0: simulate, estimate, compare with the truth. One cell = one Params, many replications.

For every parameter: mean estimate, relative bias, the Monte Carlo standard error of that mean,
90% interval coverage, and the share of replications rejecting "parameter = 0" (power when the
truth is non-zero, size when it is zero). Three mis-specified models are compared out of sample
with Diebold-Mariano tests: no network term, no credibility, and HAR without the news terms.

Replication k of cell c uses SeedSequence([seed, c, k]), so the numbers do not depend on how the
work is split over processes.

numpy only; no network, no clock reads.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from core.didm.models import har_x, lp
from core.didm.sim.dgp import Params, Panel, simulate, truth

HORIZONS = (0, 1, 5, 20)
LP_NAMES = ("shock", "w_shock", "macro")
TRAIN_FRACTION = 0.70
FORECAST_HORIZON = 1
Z_HOLM14 = 2.9137            # two-sided 0.05 / 14: the strictest Holm step over 14 event types
ALPHA_DM = 0.05


def _stack(*arrays: np.ndarray) -> np.ndarray:
    return np.stack(arrays, axis=2)


def _lp_oos_losses(panel: Panel, columns: tuple[np.ndarray, ...], split: int) -> np.ndarray:
    """Per-date mean squared error of the 1-day-ahead cumulative abnormal return, test dates only."""
    h = FORECAST_HORIZON
    x = _stack(*columns)
    names = tuple(f"x{i}" for i in range(x.shape[2]))
    fit = lp.fit_lp(panel.returns[:split], x[:split], names, horizons=(h,))
    y = lp.cumulative_returns(panel.returns, h)
    y = y - y.mean(axis=1, keepdims=True)
    pred = lp.predict(fit.fits[h].coef, x[: len(y)])
    return ((y - pred) ** 2).mean(axis=1)[split:]


def one_replication(p: Params, rng: np.random.Generator) -> dict[str, tuple[float, float]]:
    """Estimates as {name: (estimate, standard error)}; DM entries are (statistic, p-value)."""
    panel = simulate(p, rng)
    out: dict[str, tuple[float, float]] = {}

    fit = lp.fit_lp(panel.returns, _stack(panel.shock, panel.w_shock, panel.macro), LP_NAMES, HORIZONS)
    for h in HORIZONS:
        out[f"theta_h{h}"] = (fit.coef("shock", h), fit.se("shock", h))
        out[f"phi_h{h}"] = (fit.coef("w_shock", h), fit.se("w_shock", h))
    out["psi"] = (fit.coef("macro", 0), fit.se("macro", 0))
    for name, h1 in (("delta", 20), ("delta_h5", 5)):
        ratio = lp.delayed_share(fit, "shock", 0, h1)
        out[name] = (ratio.value, ratio.se)

    placebo = lp.fit_lp(panel.returns, _stack(panel.shock, panel.w_shock_placebo, panel.macro), LP_NAMES, (5,))
    out["phi_placebo_h5"] = (placebo.coef("w_shock", 5), placebo.se("w_shock", 5))

    extra = _stack(panel.abs_shock, panel.entropy)
    vol = har_x.fit_har_x(panel.log_rv, extra, ("gamma", "eta"))
    for j, name in enumerate(vol.names):
        out[name] = (float(vol.coef[j]), float(vol.se[j]))

    split = int(p.n_dates * TRAIN_FRACTION)
    full = _lp_oos_losses(panel, (panel.shock, panel.w_shock, panel.macro), split)
    no_w = _lp_oos_losses(panel, (panel.shock, panel.macro), split)
    no_cred = _lp_oos_losses(panel, (panel.shock_nocred, panel.w_shock_nocred, panel.macro), split)
    out["dm_no_network"] = lp.dm_test(no_w, full)
    out["dm_no_credibility"] = lp.dm_test(no_cred, full)

    har_fit = har_x.fit_har_x(panel.log_rv[:split])
    harx_fit = har_x.fit_har_x(panel.log_rv[:split], extra[:split], ("gamma", "eta"))
    actual, pred_har = har_x.predict(har_fit, panel.log_rv[split:])
    _, pred_harx = har_x.predict(harx_fit, panel.log_rv[split:], extra[split:])
    out["dm_har_without_news"] = lp.dm_test(((actual - pred_har) ** 2).mean(axis=1),
                                            ((actual - pred_harx) ** 2).mean(axis=1))

    def qlike(pred: np.ndarray, var: float) -> float:
        forecast = np.exp(pred + 0.5 * var)
        ratio = np.exp(actual) / forecast
        return float((ratio - np.log(ratio) - 1.0).mean())
    base, news = qlike(pred_har, har_fit.resid_var), qlike(pred_harx, harx_fit.resid_var)
    out["qlike_gain_pct"] = (100.0 * (base - news) / base, 0.0)
    out["n_events"] = (float(panel.n_events), 0.0)
    return out


@dataclass(frozen=True)
class ParamSummary:
    name: str
    truth: float
    mean: float
    sd: float
    mc_se: float
    rel_bias: float | None       # None when the truth is zero
    coverage90: float
    reject05: float              # power (truth != 0) or size (truth == 0)
    reject_holm14: float
    median_se: float


@dataclass(frozen=True)
class CellSummary:
    label: str
    params: Params
    reps: int
    estimates: dict[str, ParamSummary]
    dm_reject: dict[str, float]      # share of replications where the mis-specified model loses, p < 0.05
    qlike_gain_pct: float
    mean_events: float


def cell_seeds(seed: int, cell_index: int, reps: int) -> list[np.random.SeedSequence]:
    return [np.random.SeedSequence([seed, cell_index, k]) for k in range(reps)]


def _run_one(args: tuple[Params, np.random.SeedSequence]) -> dict[str, tuple[float, float]]:
    p, ss = args
    return one_replication(p, np.random.default_rng(ss))


def summarise(label: str, p: Params, results: list[dict[str, tuple[float, float]]]) -> CellSummary:
    reps = len(results)
    true = truth(p, HORIZONS)
    true["phi_placebo_h5"] = 0.0
    estimates: dict[str, ParamSummary] = {}
    for name, value in true.items():
        est = np.array([r[name][0] for r in results])
        se = np.array([r[name][1] for r in results])
        z = (est) / se
        mean, sd = float(est.mean()), float(est.std(ddof=1)) if reps > 1 else 0.0
        estimates[name] = ParamSummary(
            name=name, truth=value, mean=mean, sd=sd, mc_se=sd / math.sqrt(reps),
            rel_bias=None if value == 0.0 else (mean - value) / value,
            coverage90=float((np.abs(est - value) <= lp.Z90 * se).mean()),
            reject05=float((np.abs(z) > lp.Z95).mean()),
            reject_holm14=float((np.abs(z) > Z_HOLM14).mean()),
            median_se=float(np.median(se)),
        )
    dm = {k: float(np.mean([r[k][1] < ALPHA_DM for r in results]))
          for k in ("dm_no_network", "dm_no_credibility", "dm_har_without_news")}
    return CellSummary(label, p, reps, estimates, dm,
                       float(np.mean([r["qlike_gain_pct"][0] for r in results])),
                       float(np.mean([r["n_events"][0] for r in results])))


def run_cell(label: str, p: Params, reps: int, seed: int, cell_index: int, pool=None) -> CellSummary:
    jobs = [(p, ss) for ss in cell_seeds(seed, cell_index, reps)]
    results = pool.map(_run_one, jobs, chunksize=4) if pool is not None else [_run_one(j) for j in jobs]
    return summarise(label, p, results)
