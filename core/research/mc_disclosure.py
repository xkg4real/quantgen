"""Named Monte Carlo outputs for display; no estimates are recomputed here."""


def volatility_disclosure(result):
    conditional = result.garch is not None
    return {
        "label": "Next-session vol (ann.)" if conditional else "Sample vol (ann.)",
        "value": result.sigma_annual,
        "basis": "next_session_conditional" if conditional else "historical_sample_log_returns",
        "description": ("Next-session conditional forecast volatility" if conditional
                        else "Historical log-return sample volatility") + ", annualized using 252 sessions.",
        "annualization_sessions": 252,
        "horizon_average_annualized": result.garch_horizon_vol if conditional else None,
        "horizon_sessions": result.horizon_days,
        "horizon_basis": "sqrt(mean forecast daily variance) * sqrt(252), using the engine innovation convention" if conditional else None,
    }
