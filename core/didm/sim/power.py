"""DIDM Stage 0: the registered parameter grid, the thresholds and the verdict rule.

This file was committed before the grid was run with the report seed. Changing the grid,
the gate cells or the rule after seeing results is a new attempt and is written into
ATTEMPTS below and into docs/didm/STAGE0_REPORT_V0.md.

Thresholds are the registered ones (PREREG_V0 3, Stage 0 row; Notion DIDM 6.2):
relative bias < 10%, 90% interval coverage 85-95%, power >= 80% for the planned sample,
mis-specified models lose (DM p < 0.05).

numpy only; no network, no clock reads.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from core.didm.sim.dgp import BP, Params
from core.didm.sim.recovery import CellSummary

# --- registered thresholds (not tunable) ---
MAX_REL_BIAS = 0.10
COVERAGE_BAND = (0.85, 0.95)
MIN_POWER = 0.80
DM_ALPHA = 0.05
REPORT_SEED = 20261124
REPORT_REPS = 500

# --- how the thresholds are read (decided before the run; interpretation by DIDM_DEV) ---
# 1. Bias: a parameter fails only if |relative bias| >= 10% AND the bias is more than 2 Monte Carlo
#    standard errors from zero. With 500 replications a weakly identified parameter can show a 10% gap
#    by chance; that case is reported as "undetermined", not as a failure and not as a pass.
# 2. Coverage is checked for every parameter in every calibrated cell, zero truths included.
# 3. Power is checked where the truth is non-zero, in the gate cell named for that layer, at
#    two-sided 5%. Power at the strictest Holm step over 14 types is reported next to it.
# 4. "Mis-specified models lose" = in the gate cell, the share of replications with one-sided
#    DM p < 0.05 is at least 80% (the power threshold).
# 5. The planned sample is N = 200 units, T = 2,500 trading days (Stage 2 window 2015-2024,
#    upper end of the Notion N range). N = 50 cells are reported, not gated.
MC_SE_MULTIPLE = 2.0

PLANNED_UNITS, PLANNED_DATES = 200, 2500
RATE_ONE_TYPE = 0.005        # about one event of a given type per unit per 200 trading days
RATE_POOLED = 0.07           # 14 types pooled


def _cell(**kw) -> Params:
    base = dict(n_units=PLANNED_UNITS, n_dates=PLANNED_DATES, event_rate=RATE_ONE_TYPE,
                theta0=50 * BP, delta=0.15, half_life=1.0, phi_total=10 * BP, psi=10 * BP,
                gamma=0.10, eta=0.05)
    base.update(kw)
    return Params(**base)


# Central values: day-0 response 50 bp per unit of impact; delayed share 0.15 (prior 0-0.3, US large-cap);
# half-life 1 day (prior 0.5-1); spillover 10 bp ("typical spillover size", Notion 7.4);
# gamma: a unit of |shock| raises next-day log RV by 0.10. Low / high cells halve / double the effects.
_LOW = dict(theta0=25 * BP, delta=0.0, phi_total=0.0, gamma=0.05, eta=0.0)
_HIGH = dict(theta0=100 * BP, delta=0.30, phi_total=20 * BP, gamma=0.20, eta=0.10)

GRID_V0: tuple[tuple[str, Params], ...] = (
    ("A one-type central N200", _cell()),
    ("B one-type central N50", _cell(n_units=50)),
    ("C pooled central N200", _cell(event_rate=RATE_POOLED)),
    ("D pooled central N50", _cell(event_rate=RATE_POOLED, n_units=50)),
    ("E one-type low N200", _cell(**_LOW)),
    ("F one-type high N200", _cell(**_HIGH)),
    ("G one-type central N200 overconfident scorer", _cell(overconfidence=2.0)),
    ("H one-type central N200 half-life 5d", _cell(half_life=5.0)),
    ("I pooled low N200", _cell(event_rate=RATE_POOLED, **_LOW)),
    ("J pooled high N200", _cell(event_rate=RATE_POOLED, **_HIGH)),
)
SENSITIVITY_ONLY = ("G",)        # deliberately mis-calibrated scorer: reported, never gated
GATE_ONE_TYPE, GATE_POOLED = "A", "C"

# layer -> (parameter whose power is gated, gate cell). Core layers decide GO vs NO-GO.
CORE_LAYERS = {
    "direct day-0 response (theta_0)": ("theta_h0", GATE_ONE_TYPE),
    "volatility on |shock| (gamma)": ("gamma", GATE_ONE_TYPE),
}
OTHER_LAYERS = {
    "delayed-pricing share (delta), per type": ("delta", GATE_ONE_TYPE),
    "network spillover (phi, 5-day), pooled": ("phi_h5", GATE_POOLED),
    "macro exposure (psi)": ("psi", GATE_ONE_TYPE),
    "volatility on uncertainty (eta)": ("eta", GATE_ONE_TYPE),
}
DM_GATES = {
    "no network term": ("dm_no_network", GATE_POOLED),
    "no credibility": ("dm_no_credibility", GATE_POOLED),
    "HAR without news terms": ("dm_har_without_news", GATE_POOLED),
}
# Parameters whose bias and coverage are checked in every calibrated cell.
RECOVERY_PARAMS = ("theta_h0", "theta_h1", "theta_h5", "theta_h20", "phi_h0", "phi_h1", "phi_h5", "phi_h20",
                   "psi", "delta", "gamma", "eta", "har_d", "har_w", "har_m")

ATTEMPTS = (
    "attempt 1 (2026-11-24): grid GRID_V0, 500 replications, seed 20261124. Before this commit the code was "
    "only run on toy parameters with large effects (not this grid) to check that it works.",
)


def cell_key(label: str) -> str:
    return label.split()[0]


def events_needed(effect: float, sigma_car: float, z_alpha: float = 1.96, z_power: float = 0.84) -> float:
    """Independent events needed to detect a mean CAR of ``effect`` (Notion DIDM 7.4: (2.80 * sigma / effect) ** 2)."""
    if effect <= 0 or sigma_car <= 0:
        raise ValueError("effect and sigma_car must be positive")
    return ((z_alpha + z_power) * sigma_car / effect) ** 2


@dataclass(frozen=True)
class Check:
    cell: str
    item: str
    kind: str          # bias | coverage | power | dm
    value: float
    status: str        # pass | fail | undetermined
    detail: str = ""


def bias_status(rel_bias: float | None, bias: float, mc_se: float) -> str:
    if rel_bias is None or abs(rel_bias) < MAX_REL_BIAS:
        return "pass"
    return "fail" if abs(bias) > MC_SE_MULTIPLE * mc_se else "undetermined"


def checks(cells: list[CellSummary]) -> list[Check]:
    by_key = {cell_key(c.label): c for c in cells}
    out: list[Check] = []
    for c in cells:
        key = cell_key(c.label)
        if key in SENSITIVITY_ONLY:
            continue
        for name in RECOVERY_PARAMS:
            e = c.estimates[name]
            if e.rel_bias is not None:
                out.append(Check(key, name, "bias", e.rel_bias, bias_status(e.rel_bias, e.mean - e.truth, e.mc_se)))
            ok = COVERAGE_BAND[0] <= e.coverage90 <= COVERAGE_BAND[1]
            out.append(Check(key, name, "coverage", e.coverage90, "pass" if ok else "fail"))
    for layer, (name, key) in {**CORE_LAYERS, **OTHER_LAYERS}.items():
        if key in by_key:
            power = by_key[key].estimates[name].reject05
            out.append(Check(key, name, "power", power, "pass" if power >= MIN_POWER else "fail", layer))
    for model, (name, key) in DM_GATES.items():
        if key in by_key:
            share = by_key[key].dm_reject[name]
            out.append(Check(key, name, "dm", share, "pass" if share >= MIN_POWER else "fail", model))
    return out


@dataclass(frozen=True)
class Verdict:
    line: str                  # GO | REVISE | NO-GO
    reasons: tuple[str, ...]


def verdict(all_checks: list[Check]) -> Verdict:
    """NO-GO: a core layer cannot be recovered (its power gate fails, or its bias fails in a gate cell).
    GO: no failed and no undetermined check. REVISE: everything else."""
    core_names = {name for name, _ in CORE_LAYERS.values()}
    gate_cells = {GATE_ONE_TYPE, GATE_POOLED}
    reasons, no_go = [], False
    for c in all_checks:
        if c.status == "pass":
            continue
        reasons.append(f"{c.cell} {c.item} {c.kind} = {c.value:.3f} ({c.status})" + (f" [{c.detail}]" if c.detail else ""))
        if c.status == "fail" and c.item in core_names and c.kind in ("power", "bias") and c.cell in gate_cells:
            no_go = True
    if no_go:
        return Verdict("NO-GO", tuple(reasons))
    return Verdict("REVISE" if reasons else "GO", tuple(reasons))


def scaled(p: Params, **kw) -> Params:
    return replace(p, **kw)


def normal_power(effect: float, se: float, z_alpha: float = 1.96) -> float:
    """Approximate two-sided power of a z-test with the given effect and standard error."""
    if se <= 0:
        raise ValueError("se must be positive")
    shift = abs(effect) / se
    return 0.5 * math.erfc((z_alpha - shift) / math.sqrt(2)) + 0.5 * math.erfc((z_alpha + shift) / math.sqrt(2))
