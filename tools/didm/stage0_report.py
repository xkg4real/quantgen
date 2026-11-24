"""DIDM Stage 0 report: run the registered simulation grid and print the verdict (DIDM-4).

    python -B -m tools.didm.stage0_report --seed 20261124 --out <folder outside the repository>

Prints, per cell and parameter, the relative bias, the 90% interval coverage and the power,
then one line ``STAGE0: GO|REVISE|NO-GO``. Writes stage0.json and stage0.md into --out.
The same seed gives the same numbers. Everything is simulated: no market data, no network,
no model calls.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
import sys
from dataclasses import asdict
from pathlib import Path

from core.didm.sim import power, recovery

ROOT = Path(__file__).resolve().parents[2]
SHOWN = ("theta_h0", "theta_h1", "theta_h5", "theta_h20", "delta", "delta_h5", "phi_h0", "phi_h1", "phi_h5",
         "phi_h20", "phi_placebo_h5", "psi", "gamma", "eta", "har_d", "har_w", "har_m")


def _pct(value: float | None) -> str:
    return "   n/a" if value is None else f"{100 * value:6.1f}"


def cell_table(cell: recovery.CellSummary) -> list[str]:
    p = cell.params
    lines = [
        f"## {cell.label}",
        f"N={p.n_units} T={p.n_dates} event_rate={p.event_rate} theta0={p.theta0 / power.BP:.0f}bp delta={p.delta} "
        f"half_life={p.half_life}d phi_total={p.phi_total / power.BP:.0f}bp psi={p.psi / power.BP:.0f}bp "
        f"gamma={p.gamma} eta={p.eta} overconfidence={p.overconfidence} | reps={cell.reps} "
        f"mean events={cell.mean_events:.0f}",
        "",
        "| parameter | truth | mean estimate | rel. bias % | MC s.e. | coverage90 % | reject 5% % | reject Holm-14 % |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in SHOWN:
        e = cell.estimates[name]
        lines.append(f"| {name} | {e.truth:.6g} | {e.mean:.6g} | {_pct(e.rel_bias)} | {e.mc_se:.3g} | "
                     f"{_pct(e.coverage90)} | {_pct(e.reject05)} | {_pct(e.reject_holm14)} |")
    lines += ["", "Mis-specified model loses out of sample (share of replications with one-sided DM p < 0.05): "
              + ", ".join(f"{k} {100 * v:.1f}%" for k, v in cell.dm_reject.items())
              + f". Mean QLIKE gain of HAR-X over HAR: {cell.qlike_gain_pct:.2f}%.", ""]
    return lines


def render(cells: list[recovery.CellSummary], seed: int, reps: int) -> tuple[str, power.Verdict]:
    all_checks = power.checks(cells)
    result = power.verdict(all_checks)
    lines = [
        "# DIDM Stage 0 simulation output",
        "",
        f"seed={seed} reps={reps} cells={len(cells)} | thresholds: |relative bias| < {power.MAX_REL_BIAS:.0%}, "
        f"coverage {power.COVERAGE_BAND[0]:.0%}-{power.COVERAGE_BAND[1]:.0%}, power >= {power.MIN_POWER:.0%}, "
        f"DM p < {power.DM_ALPHA}",
        "",
    ]
    for cell in cells:
        lines += cell_table(cell)
    lines += ["## Gate checks that did not pass", ""]
    failed = [c for c in all_checks if c.status != "pass"]
    if failed:
        lines += ["| cell | item | check | value | status | layer |", "|---|---|---|---|---|---|"]
        lines += [f"| {c.cell} | {c.item} | {c.kind} | {c.value:.3f} | {c.status} | {c.detail} |" for c in failed]
    else:
        lines.append("none")
    n_pass = sum(c.status == "pass" for c in all_checks)
    lines += ["", f"checks: {len(all_checks)} total, {n_pass} pass, "
              f"{sum(c.status == 'fail' for c in all_checks)} fail, "
              f"{sum(c.status == 'undetermined' for c in all_checks)} undetermined", "",
              f"STAGE0: {result.line}"]
    return "\n".join(lines) + "\n", result


def to_json(cells: list[recovery.CellSummary], seed: int, reps: int, result: power.Verdict) -> str:
    payload = {
        "seed": seed, "reps": reps, "verdict": result.line, "reasons": list(result.reasons),
        "cells": [{"label": c.label, "params": asdict(c.params), "reps": c.reps,
                   "estimates": {k: asdict(v) for k, v in c.estimates.items()},
                   "dm_reject": c.dm_reject, "qlike_gain_pct": c.qlike_gain_pct, "mean_events": c.mean_events}
                  for c in cells],
        "checks": [asdict(c) for c in power.checks(cells)],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def run(seed: int, reps: int, workers: int, grid=power.GRID_V0) -> list[recovery.CellSummary]:
    if workers <= 1:
        return [recovery.run_cell(label, p, reps, seed, i) for i, (label, p) in enumerate(grid)]
    with multiprocessing.get_context("spawn").Pool(workers) as pool:
        return [recovery.run_cell(label, p, reps, seed, i, pool) for i, (label, p) in enumerate(grid)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True, help="output folder; must be outside the repository")
    parser.add_argument("--reps", type=int, default=power.REPORT_REPS)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        print("--out must be a folder outside the repository", file=sys.stderr)
        return 2
    if args.reps < 2:
        print("--reps must be at least 2", file=sys.stderr)
        return 2
    cells = run(args.seed, args.reps, args.workers)
    text, result = render(cells, args.seed, args.reps)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stage0.md").write_text(text, encoding="utf-8", newline="\n")
    (out / "stage0.json").write_text(to_json(cells, args.seed, args.reps, result), encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
