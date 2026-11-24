"""DIDM Stage 0, EXPLORATORY power curves (not a registered run, not used for any verdict).

    python -B -m tools.didm.stage0_explore --out <folder outside the repository> --workers 4

Question: at what sample size and effect size would the delayed-pricing layer and the network layer
reach 80% power? The registered grid (core/didm/sim/power.py GRID_V0) and its verdict rule are not
touched and not rerun; this script uses its own seed and prints EXPLORATORY on every table.

Method: (1) simulate two reference designs (one event type, 14 types pooled; N = 200, T = 2,500) and
take the Monte Carlo standard deviation of each estimator; (2) scale that standard deviation by
1 / sqrt(units x days x event rate), which is how a pooled regression's standard error moves when
events are independent; (3) power = normal approximation at two-sided 5%; (4) check the scaling by
simulating a few other designs outright.

Estimators compared for the delayed layer: the registered ratio delta = (Theta_20 - Theta_0) / Theta_20,
and the difference D_h = Theta_h - Theta_0 (h = 5, 20) with a joint Driscoll-Kraay standard error.
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

from core.didm.models import lp
from core.didm.sim import dgp, power
from core.didm.sim.dgp import BP

ROOT = Path(__file__).resolve().parents[2]
EXPLORE_SEED = 77020261124          # deliberately not the report seed
HORIZONS = (0, 1, 5, 20)
NAMES = ("shock", "w_shock", "macro")
ESTIMATES = ("theta_h0", "diff_h5", "diff_h20", "delta_ratio", "phi_h0", "phi_h1", "phi_h5", "phi_h20")


def difference(fit: lp.LPFit, name: str, h0: int, h1: int) -> tuple[float, float]:
    """Theta_h1 - Theta_h0 and its standard error from the joint covariance of the two horizons."""
    j = fit.names.index(name)
    a, b = fit.fits[h0], fit.fits[h1]
    stacked = np.column_stack([a.influence[:, j], b.influence[:, j]])
    cov = lp.bartlett_cov(stacked, lp.hac_lags(max(h0, h1)))
    grad = np.array([-1.0, 1.0])
    return float(b.coef[j] - a.coef[j]), math.sqrt(max(float(grad @ cov @ grad), 0.0))


def truths(p: dgp.Params) -> dict[str, float]:
    t = dgp.truth(p, HORIZONS)
    return {"theta_h0": t["theta_h0"], "diff_h5": t["theta_h5"] - t["theta_h0"],
            "diff_h20": t["theta_h20"] - t["theta_h0"], "delta_ratio": t["delta"],
            "phi_h0": t["phi_h0"], "phi_h1": t["phi_h1"], "phi_h5": t["phi_h5"], "phi_h20": t["phi_h20"]}


def _one(args) -> dict[str, tuple[float, float]]:
    p, ss = args
    panel = dgp.simulate(p, np.random.default_rng(ss))
    fit = lp.fit_lp(panel.returns, np.stack([panel.shock, panel.w_shock, panel.macro], axis=2), NAMES, HORIZONS)
    out = {"theta_h0": (fit.coef("shock", 0), fit.se("shock", 0)),
           "diff_h5": difference(fit, "shock", 0, 5), "diff_h20": difference(fit, "shock", 0, 20)}
    ratio = lp.delayed_share(fit, "shock", 0, 20)
    out["delta_ratio"] = (ratio.value, ratio.se)
    for h in HORIZONS:
        out[f"phi_h{h}"] = (fit.coef("w_shock", h), fit.se("w_shock", h))
    return out


def simulate_design(p: dgp.Params, reps: int, design_index: int, pool) -> dict[str, dict[str, float]]:
    jobs = [(p, np.random.SeedSequence([EXPLORE_SEED, design_index, k])) for k in range(reps)]
    rows = pool.map(_one, jobs, chunksize=4) if pool is not None else [_one(j) for j in jobs]
    true = truths(p)
    out = {}
    for name in ESTIMATES:
        est = np.array([r[name][0] for r in rows])
        se = np.array([r[name][1] for r in rows])
        out[name] = {"truth": true[name], "mean": float(est.mean()), "sd": float(est.std(ddof=1)),
                     "median_se": float(np.median(se)),
                     "coverage90": float((np.abs(est - true[name]) <= lp.Z90 * se).mean()),
                     "power": float((np.abs(est / se) > lp.Z95).mean())}
    return out


def exposure(p: dgp.Params) -> float:
    return p.n_units * p.n_dates * p.event_rate


def scaled_power(effect: float, sd_ref: float, exposure_ref: float, exposure_new: float) -> float:
    return power.normal_power(effect, sd_ref * math.sqrt(exposure_ref / exposure_new))


def exposure_for_power(effect: float, sd_ref: float, exposure_ref: float, target: float = 0.80) -> float:
    """Units x days x event rate at which a z-test of ``effect`` has the target power (2.80 rule)."""
    needed_se = abs(effect) / (lp.Z95 + 0.8416212335729143)
    return exposure_ref * (sd_ref / needed_se) ** 2


def central(**kw) -> dgp.Params:
    return replace(dict(power.GRID_V0)["A one-type central N200"], **kw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=300)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        print("--out must be a folder outside the repository", file=sys.stderr)
        return 2
    designs = [
        ("ref one type N200 T2500", central()),
        ("ref pooled N200 T2500", central(event_rate=power.RATE_POOLED)),
        ("check pooled N500 T2500", central(event_rate=power.RATE_POOLED, n_units=500)),
        ("check pooled N200 T2500 effects x2", central(event_rate=power.RATE_POOLED, theta0=100 * BP, delta=0.30,
                                                       phi_total=20 * BP)),
        ("check one type N200 T2500 effects x2", central(theta0=100 * BP, delta=0.30, phi_total=20 * BP)),
    ]
    pool = multiprocessing.get_context("spawn").Pool(args.workers) if args.workers > 1 else None
    try:
        sims = {label: simulate_design(p, args.reps, i, pool) for i, (label, p) in enumerate(designs)}
    finally:
        if pool is not None:
            pool.close()
    params = dict(designs)
    lines = ["# EXPLORATORY Stage 0 power curves (not a registered run; no verdict)", "",
             f"seed={EXPLORE_SEED} reps={args.reps} | reference designs simulated, other rows scaled by "
             "1/sqrt(units x days x event rate) unless marked simulated", "",
             "## Simulated designs", "",
             "| design | estimator | truth | mean | MC sd | median s.e. | coverage90 % | power % |", "|---|---|---|---|---|---|---|---|"]
    for label, res in sims.items():
        for name in ESTIMATES:
            r = res[name]
            lines.append(f"| {label} | {name} | {r['truth']:.5g} | {r['mean']:.5g} | {r['sd']:.4g} | {r['median_se']:.4g} | "
                         f"{100 * r['coverage90']:.1f} | {100 * r['power']:.1f} |")
    lines += ["", "## Scaling check: predicted from the pooled reference vs simulated", "",
              "| design | estimator | predicted power % | simulated power % |", "|---|---|---|---|"]
    ref_label = "ref pooled N200 T2500"
    ref, ref_exp = sims[ref_label], exposure(params[ref_label])
    for label in list(sims)[2:]:
        for name in ("diff_h5", "diff_h20", "phi_h1", "phi_h5"):
            pred = scaled_power(sims[label][name]["truth"], ref[name]["sd"], ref_exp, exposure(params[label]))
            lines.append(f"| {label} | {name} | {100 * pred:.1f} | {100 * sims[label][name]['power']:.1f} |")
    lines += ["", "## Predicted power by sample size and effect size (pooled over 14 types, event rate 0.07)", "",
              "| units N | days T | effect multiple | D_5 = Theta_5 - Theta_0 | D_20 | phi_1 | phi_5 |", "|---|---|---|---|---|---|---|"]
    table = []
    for n_units in (200, 500, 1000, 2000):
        for n_dates in (2500, 5000):
            for mult in (1, 2, 3):
                p = central(event_rate=power.RATE_POOLED, n_units=max(n_units, 5), n_dates=n_dates)
                row = {"n_units": n_units, "n_dates": n_dates, "multiple": mult}
                for name in ("diff_h5", "diff_h20", "phi_h1", "phi_h5"):
                    # effect multiple: theta0 and phi scale linearly; the delayed amount at fixed delta scales with theta0
                    row[name] = scaled_power(mult * ref[name]["truth"], ref[name]["sd"], ref_exp, exposure(p))
                table.append(row)
                lines.append(f"| {n_units} | {n_dates} | x{mult} | {100 * row['diff_h5']:.0f}% | {100 * row['diff_h20']:.0f}% | "
                             f"{100 * row['phi_h1']:.0f}% | {100 * row['phi_h5']:.0f}% |")
    lines += ["", "## Units x days x event rate needed for 80% power at the central effect sizes", "",
              "| estimator | central effect | needed exposure | as N at T=2,500, pooled | as N at T=2,500, one type |", "|---|---|---|---|---|"]
    needs = {}
    for name in ("theta_h0", "diff_h5", "diff_h20", "phi_h0", "phi_h1", "phi_h5", "phi_h20"):
        need = exposure_for_power(ref[name]["truth"], ref[name]["sd"], ref_exp)
        needs[name] = need
        lines.append(f"| {name} | {ref[name]['truth']:.5g} | {need:,.0f} | {need / 2500 / power.RATE_POOLED:,.0f} | "
                     f"{need / 2500 / power.RATE_ONE_TYPE:,.0f} |")
    lines += ["", "EXPLORATORY: these numbers support a proposal; they are not a Stage 0 result."]
    text = "\n".join(lines) + "\n"
    out.mkdir(parents=True, exist_ok=True)
    (out / "stage0_explore.md").write_text(text, encoding="utf-8", newline="\n")
    (out / "stage0_explore.json").write_text(json.dumps(
        {"exploratory": True, "seed": EXPLORE_SEED, "reps": args.reps, "simulated": sims, "predicted": table,
         "needed_exposure": needs}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
