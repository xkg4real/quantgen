"""Descriptive SABR calibration evidence, separate from research validation.

No quality threshold is inferred from solver success or a three-quote fit.
Active bounds are the optimizer's own metadata, not a new near-bound test.
"""
from __future__ import annotations

import math
from .fx import smile_curve, SABR_CALIBRATION_BOUNDS


def fit_diagnostics(fit, forward, expiry, points=(), *, pricing_strike=None):
    points = tuple(points or ())
    strikes = [float(p.strike) for p in points]
    fitted = smile_curve(fit, forward, expiry, strikes) if points else []
    rows = [dict(label=p.label, strike=float(p.strike), quoted_vol=float(p.vol),
                 fitted_vol=float(v), residual_vol_points=float((v-p.vol)*100))
            for p, v in zip(points, fitted)]
    residuals = [r['residual_vol_points'] for r in rows]
    bounds = None if fit.active_bounds is None else list(fit.active_bounds)
    parameters = [dict(name=name, value=float(getattr(fit, name)), lower=lower, upper=upper,
                       distance_to_lower=float(getattr(fit, name)-lower),
                       distance_to_upper=float(upper-getattr(fit, name)))
                  for name, lower, upper in zip(('alpha', 'rho', 'nu'), *SABR_CALIBRATION_BOUNDS)]
    lo, hi = (min(strikes), max(strikes)) if strikes else (None, None)
    position = ('NOT_RUN' if pricing_strike is None or not strikes else
                'EXTRAPOLATION' if pricing_strike < lo or pricing_strike > hi else
                'WITHIN_QUOTED_RANGE')
    return dict(solver_status='CONVERGED' if fit.converged else 'NOT_CONVERGED',
                active_bounds=bounds, bound_source='scipy.least_squares.active_mask',
                parameter_bounds=parameters,
                quote_count=len(rows), free_parameter_count=3, fixed_beta=float(fit.beta),
                calibration_residual_status='COMPUTED' if rows else 'NOT_RUN',
                residuals=rows,
                rmse_vol_points=math.sqrt(sum(r*r for r in residuals)/len(rows)) if rows else None,
                max_abs_residual_vol_points=max(map(abs, residuals)) if rows else None,
                quoted_strike_min=lo, quoted_strike_max=hi,
                pricing_strike=pricing_strike, pricing_strike_scope=position,
                independent_validation='NOT_RUN', arbitrage_validation='NOT_RUN')


def diagnostic_tone(d):
    return 'error' if (d['solver_status'] != 'CONVERGED' or d['active_bounds'] or
                       d['pricing_strike_scope'] == 'EXTRAPOLATION') else 'muted'


def diagnostic_text(d):
    bounds = ('not reported' if d['active_bounds'] is None else
              ', '.join(d['active_bounds']) or 'none reported')
    residual = ('quote residuals NOT_RUN' if d['rmse_vol_points'] is None else
                f"quote RMSE {d['rmse_vol_points']:.6f} / max absolute residual "
                f"{d['max_abs_residual_vol_points']:.6f} vol points")
    parameters = '; '.join(f"{p['name']}={p['value']:.9g} [{p['lower']:g}, {p['upper']:g}]"
                           for p in d['parameter_bounds'])
    return (f"SABR solver {d['solver_status']}; active bounds: {bounds}; {residual}. "
            f"Parameters / calibration bounds: {parameters}. "
            f"{d['quote_count']} calibration quotes / {d['free_parameter_count']} free parameters "
            f"(beta fixed at {d['fixed_beta']:g}). Pricing strike: {d['pricing_strike_scope']}. "
            "Solver convergence and small calibration residuals do not establish fit quality "
            "outside the quoted points. Independent validation: NOT_RUN; arbitrage validation: "
            "NOT_RUN. Hagan approximation: far wings and long expiries are not validated.")
