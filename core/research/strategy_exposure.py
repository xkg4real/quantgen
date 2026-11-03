"""Disclosure only for the Lab's independent, long-only asset sleeves.

The weight generators, P&L, walk-forward selection and score are unchanged.
Exposure is reconstructed from the chosen configuration at each OOS origin;
the final in-sample winner is never applied to the whole reported OOS span.
"""
from __future__ import annotations

import numpy as np


EXPOSURE_HELP = (
    "Volatility target and Crypto trend allocate independently to each asset. "
    "Their cap is per asset, not a portfolio gross cap; N assets can reach N× exposure. "
    "They are single-asset rules, not a portfolio volatility target or a 1× basket. "
    "Multi-asset results are an unnormalized sleeve sum."
)


def exposure_summary(family, prices, dates, grid, weight_fn, wf, *, embargo, cash_daily):
    """Summarize held weights over exactly the walk-forward return observations.

    `dates[i]` labels P[i] -> P[i+1], hence it uses W[i], not W[i+1].
    Only deterministic existing weight generators are called; no I/O or scoring.
    """
    if family not in {"vol_target", "crypto_trend"}:
        return None
    price = np.asarray(prices)
    n_assets = price.shape[1]
    lookup = {d: i for i, d in enumerate(dates)}
    rows = np.array([lookup[d] for d in wf.dates], dtype=int)
    starts = np.asarray(wf.origins, dtype=int) + embargo
    origin_index = np.searchsorted(starts, rows, side="right") - 1
    if not len(rows) or np.any(origin_index < 0) or len(starts) != len(wf.chosen):
        raise ValueError("Cannot align exposure with walk-forward origins")
    selected = np.asarray(wf.chosen, dtype=int)[origin_index]
    held = np.empty((len(rows), n_assets))
    for g in np.unique(selected):
        weights = weight_fn(price, **grid[g])
        mask = selected == g
        held[mask] = weights[rows[mask]]
    gross = np.abs(held).sum(axis=1)
    # Both disclosed families are long-only. This is simulate()'s cash rule.
    cash = 1.0 - held.sum(axis=1)
    caps = [float(p.get("cap", 1.0)) for p in grid] if family == "vol_target" else [1.0]
    return {
        "scope": "stitched_oos_selected_configurations",
        "observations": int(len(rows)), "asset_count": int(n_assets),
        "per_asset_cap_min": min(caps), "per_asset_cap_max": max(caps),
        "portfolio_gross_cap": None,
        "theoretical_gross_upper_bound": n_assets * max(caps),
        "gross_mean": float(gross.mean()), "gross_max": float(gross.max()),
        "borrowing_max": float(np.maximum(-cash, 0).max()),
        "cash_rate_per_session": float(cash_daily),
        "benchmark_gross": 1.0,
        "benchmark_basis": "equal_weight_daily_returns_not_exposure_matched",
    }


def exposure_lines(info):
    if info is None:
        return []
    cap = f"{info['per_asset_cap_min']:g}–{info['per_asset_cap_max']:g}×"
    if info['per_asset_cap_min'] == info['per_asset_cap_max']:
        cap = f"{info['per_asset_cap_max']:g}×"
    return [
        f"Per-asset cap {cap}; {info['asset_count']} independent sleeves; "
        f"no portfolio gross cap. Theoretical total upper bound "
        f"{info['theoretical_gross_upper_bound']:g}×. Single-asset rules; "
        "multi-asset input is an unnormalized sum, not portfolio volatility targeting.",
        f"OOS held gross exposure: mean {info['gross_mean']:.2f}×, "
        f"max {info['gross_max']:.2f}× across {info['observations']} observations. "
        "Uses each walk-forward origin's selected configuration, not the final winner for all dates.",
        f"Maximum OOS borrowing {info['borrowing_max']:.2f}× equity. "
        f"Cash = 1 − sum(weights); negative cash is borrowed at "
        f"{info['cash_rate_per_session']:.8f} per session (Lab assumption: 3% / 252). "
        "The 1× equal-weight daily-return benchmark is not exposure-matched.",
    ]
