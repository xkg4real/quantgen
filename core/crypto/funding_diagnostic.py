"""Exploratory, retrospective funding/return association; no study gate.

The circular-phase null makes every relative cyclic alignment equiprobable.
It is stronger than ordinary stationarity/zero correlation. Enumerating the
orbit preserves each series' ordering (on a ring), overlapping returns and
event clusters. It does not establish a real-market predictive relationship.
"""
import numpy as np


def phase_diagnostic(signal, forward_return, horizon):
    x, y = np.asarray(signal, float), np.asarray(forward_return, float)
    if (x.ndim != 1 or x.shape != y.shape or not x.size
            or not np.isfinite(x).all() or not np.isfinite(y).all()):
        raise ValueError("Funding diagnostic requires aligned finite vectors")
    if type(horizon) is not int or horizon < 1:
        raise ValueError("Forward horizon must be a positive integer")
    lo, hi = np.quantile(x, [.1, .9])
    top, bottom = x >= hi, x <= lo
    nt, nb = int(top.sum()), int(bottom.sum())
    observed = float(y[top].mean() - y[bottom].mean())
    out = dict(method="EXHAUSTIVE_CIRCULAR_PHASE", status="NOT_ESTIMATED",
        p_lower=None, alternative="top_minus_bottom < 0", observed_difference=observed,
        eligible_observations=len(x), top_count=nt, bottom_count=nb,
        forward_observations=horizon, deciles="FULL_SAMPLE_RETROSPECTIVE",
        cyclic_shifts=0, official_validation="NOT_RUN",
        assumptions="Independent series with equiprobable relative cyclic phase; not verified for market data",
        limitations="Wraparound and structural breaks; not a predictive signal or historical-card revalidation")
    if hi <= lo or np.any(top & bottom):
        out['reason'] = "Top and bottom groups overlap (tied quantiles)"
        return out
    if min(nt, nb) <= 10:
        out['reason'] = "Each event group needs more than 10 observations"
        return out
    if np.ptp(y) == 0:
        out['reason'] = "Forward returns have no variation"
        return out
    weights = top / nt - bottom / nb
    # dot(roll(weights, k), y), all k including identity. FFT accelerates the
    # exact enumeration; no IID draws, arbitrary block length or random seed.
    differences = np.fft.ifft(np.fft.fft(y) * np.conj(np.fft.fft(weights))).real
    tolerance = 64 * np.finfo(float).eps * max(1., float(np.max(np.abs(y))))
    out.update(status="EXPLORATORY", cyclic_shifts=len(x),
        p_lower=float(np.mean(differences <= observed + tolerance)))
    return out
