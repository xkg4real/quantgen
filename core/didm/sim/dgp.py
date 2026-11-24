"""DIDM Stage 0: a synthetic world that follows Version 0 exactly (Notion DIDM 5.1), with known parameters.

One firm-day may carry one typed event. For an event the scorer reports direction probabilities
(P+, P-, P0) and DIDM a credibility pi. The world then draws the truth: the event is real with
probability pi and its direction d in {+1, -1, 0} follows the *true* probabilities. So a calibrated
scorer satisfies E[real * d | scorer output] = pi * (P+ - P-) = the shock, and a regression on the
shock is unbiased even though the shock is a noisy measurement (Berkson error). An overconfident
scorer (``overconfidence`` > 1 sharpens the reported probabilities) breaks that equality.

    r_{i,t}  = mu_t + sum_j beta_j imp_{i,t-j} + sum_j betaW_j (W imp)_{i,t-j} + psi B_i f_t + sqrt(RV_{i,t}) z_{i,t}
    x_{i,t+1} = c + b_d x_{i,t} + b_w mean5(x) + b_m mean22(x) + gamma |s_{i,t}| + eta u_{i,t} + e_{i,t+1},  x = log RV

imp = real * d (what actually happened), s = pi * (P+ - P-) (what DIDM observes), u = entropy of the
calibrated direction probabilities, W a row-normalised link matrix, z a unit-variance Student t(5).
No prices or returns from any market enter here: every number is drawn from the seeded generator.

numpy only; no network, no clock reads.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

BP = 1e-4
DRIFT_HORIZON = 20           # days over which the delayed response is spread (PREREG_V0 3: h up to 20)


class SimError(ValueError):
    pass


@dataclass(frozen=True)
class Params:
    n_units: int
    n_dates: int
    event_rate: float                 # P(event) per unit-day for the event type(s) pooled in this cell
    theta0: float                     # day-0 return per unit of realised impact (decimal; 50 bp = 0.005)
    delta: float                      # delayed-pricing share of the direct response, in [0, 1)
    half_life: float                  # days; decay of the delayed part
    phi_total: float                  # cumulative 20-day spillover return per unit of linked impact
    psi: float                        # return per unit of B_i * f_t
    gamma: float                      # next-day log RV per unit of |shock|
    eta: float                        # next-day log RV per nat of direction entropy
    phi_delayed_share: float = 0.5    # spillovers arrive later than direct effects (Cohen-Frazzini)
    links: int = 3
    sigma_daily: float = 0.02         # Notion DIDM 7.4: daily abnormal-return SD 2%
    har: tuple[float, float, float] = (0.35, 0.35, 0.20)
    vol_noise: float = 0.5
    credibility_beta: tuple[float, float] = (8.0, 2.0)
    direction_concentration: tuple[float, float, float] = (0.6, 0.6, 0.3)
    overconfidence: float = 1.0       # 1 = calibrated scorer; 2 = probabilities squared and renormalised
    burn: int = 250

    def __post_init__(self) -> None:
        if self.n_units < self.links + 2 or self.n_dates < 200:
            raise SimError("need at least links + 2 units and 200 dates")
        if not 0.0 < self.event_rate <= 1.0 or not 0.0 <= self.delta < 1.0 or self.half_life <= 0:
            raise SimError("event_rate in (0, 1], delta in [0, 1), half_life > 0")
        if not 0.0 <= self.phi_delayed_share < 1.0 or sum(self.har) >= 1.0 or self.overconfidence <= 0:
            raise SimError("phi_delayed_share in [0, 1), HAR coefficients summing below 1, overconfidence > 0")


def kernel(day0: float, delayed_share: float, half_life: float) -> np.ndarray:
    """Daily impulse responses beta_0..beta_20: beta_0 = day0, the rest decays geometrically and
    sums to day0 * delayed_share / (1 - delayed_share), so the share arriving after day 0 is exact."""
    rho = 0.5 ** (1.0 / half_life)
    weights = rho ** np.arange(DRIFT_HORIZON)
    weights /= weights.sum()
    return np.concatenate([[day0], day0 * delayed_share / (1.0 - delayed_share) * weights])


def direct_kernel(p: Params) -> np.ndarray:
    return kernel(p.theta0, p.delta, p.half_life)


def spill_kernel(p: Params) -> np.ndarray:
    return kernel(p.phi_total * (1.0 - p.phi_delayed_share), p.phi_delayed_share, p.half_life)


def truth(p: Params, horizons: tuple[int, ...]) -> dict[str, float]:
    """True values of everything the estimators report."""
    direct, spill = np.cumsum(direct_kernel(p)), np.cumsum(spill_kernel(p))
    out = {"delta": p.delta, "psi": p.psi, "gamma": p.gamma, "eta": p.eta,
           "har_d": p.har[0], "har_w": p.har[1], "har_m": p.har[2]}
    for h in horizons:
        out[f"theta_h{h}"] = float(direct[min(h, DRIFT_HORIZON)])
        out[f"phi_h{h}"] = float(spill[min(h, DRIFT_HORIZON)])
    if 5 in horizons:
        out["delta_h5"] = float(1.0 - direct[0] / direct[5]) if direct[5] else 0.0
    return out


@dataclass(frozen=True)
class Panel:
    returns: np.ndarray              # (T, N)
    log_rv: np.ndarray               # (T, N)
    shock: np.ndarray                # pi * (P+ - P-), as the scorer reports it
    shock_nocred: np.ndarray         # (P+ - P-): credibility ignored (mis-specified)
    w_shock: np.ndarray              # W @ shock
    w_shock_nocred: np.ndarray
    w_shock_placebo: np.ndarray      # rewired W @ shock
    macro: np.ndarray                # B_i * f_t
    abs_shock: np.ndarray
    entropy: np.ndarray
    n_events: int
    extra: dict = field(default_factory=dict)


def _links(rng: np.random.Generator, n: int, k: int) -> np.ndarray:
    scores = rng.random((n, n))
    np.fill_diagonal(scores, 2.0)
    w = np.zeros((n, n))
    np.put_along_axis(w, np.argsort(scores, axis=1)[:, :k], 1.0 / k, axis=1)
    return w


def _convolve(impulse: np.ndarray, weights: np.ndarray) -> np.ndarray:
    out = weights[0] * impulse
    for j in range(1, len(weights)):
        if weights[j] != 0.0:
            out[j:] += weights[j] * impulse[:-j]
    return out


def simulate(p: Params, rng: np.random.Generator) -> Panel:
    t_all, n = p.burn + p.n_dates, p.n_units
    event = rng.random((t_all, n)) < p.event_rate
    probs = rng.dirichlet(p.direction_concentration, size=(t_all, n))
    draw = rng.random((t_all, n))
    direction = np.where(draw < probs[..., 0], 1.0, np.where(draw < probs[..., 0] + probs[..., 1], -1.0, 0.0))
    pi = rng.beta(*p.credibility_beta, size=(t_all, n))
    real = rng.random((t_all, n)) < pi
    impact = np.where(event & real, direction, 0.0)

    def entropy(q: np.ndarray) -> np.ndarray:
        safe = np.where(q > 0, q, 1.0)
        return -(q * np.log(safe)).sum(axis=-1)

    reported = probs
    if p.overconfidence != 1.0:
        reported = probs ** p.overconfidence
        reported = reported / reported.sum(axis=-1, keepdims=True)
    sign_true = probs[..., 0] - probs[..., 1]
    sign_seen = reported[..., 0] - reported[..., 1]
    shock = np.where(event, pi * sign_seen, 0.0)
    shock_nocred = np.where(event, sign_seen, 0.0)
    # Volatility responds to the calibrated quantities; the scorer's versions are what gets regressed.
    drive_abs = np.where(event, np.abs(pi * sign_true), 0.0)
    drive_ent = np.where(event, entropy(probs), 0.0)
    seen_ent = np.where(event, entropy(reported), 0.0)

    w, w_placebo = _links(rng, n, p.links), _links(rng, n, p.links)
    factor, exposure = rng.standard_normal(t_all), rng.standard_normal(n)
    macro = factor[:, None] * exposure[None, :]

    level = float(np.log(p.sigma_daily ** 2))
    b_d, b_w, b_m = p.har
    const = (1.0 - b_d - b_w - b_m) * level
    x = np.full((t_all, n), level)
    noise = p.vol_noise * rng.standard_normal((t_all, n))
    running5 = x[17:22].sum(axis=0)
    running22 = x[0:22].sum(axis=0)
    for t in range(21, t_all - 1):
        x[t + 1] = (const + b_d * x[t] + b_w * running5 / 5.0 + b_m * running22 / 22.0
                    + p.gamma * drive_abs[t] + p.eta * drive_ent[t] + noise[t + 1])
        running5 += x[t + 1] - x[t - 4]
        running22 += x[t + 1] - x[t - 21]

    z = rng.standard_t(5, size=(t_all, n)) / np.sqrt(5.0 / 3.0)
    returns = (0.01 * rng.standard_normal(t_all)[:, None]
               + _convolve(impact, direct_kernel(p))
               + _convolve(impact @ w.T, spill_kernel(p))
               + p.psi * macro
               + np.exp(0.5 * x) * z)

    cut = slice(p.burn, None)
    return Panel(
        returns=returns[cut], log_rv=x[cut], shock=shock[cut], shock_nocred=shock_nocred[cut],
        w_shock=(shock @ w.T)[cut], w_shock_nocred=(shock_nocred @ w.T)[cut],
        w_shock_placebo=(shock @ w_placebo.T)[cut], macro=macro[cut],
        abs_shock=np.abs(shock[cut]), entropy=seen_ent[cut], n_events=int(event[cut].sum()),
    )
