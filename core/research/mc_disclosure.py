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


# The block bootstrap's resampling scheme (§10 N-M1-02/a, ARCHITECTURE_REVIEW C1).
# The block length is the default of core.quant.montecarlo._simulate_bootstrap and
# _bootstrap_correction; run_monte_carlo passes no other value. This module does not
# import the engine: tests/mc_bootstrap_disclosure_acceptance.py pins the constant to
# both defaults, so a change there fails the test before the text can go stale.
BOOTSTRAP_BLOCK_SESSIONS = 5

# The (5-k)/5 retention is the long-horizon value: a path of H sessions has
# floor(H/5)*(5-k) + max(0, H mod 5 - k) same-block pairs out of H-k at lag k, which is
# never below (5-k)/5 and tends to it as H grows (at H = 5 the path is one block).
# "Drift" is 드리프트 in Flet and 추세 가정 in Native, so the Korean names both.
BOOTSTRAP_TEXT = (
    "Block bootstrap: circular, fixed 5-session blocks of the demeaned daily log returns in the "
    "fit window, wrapping at the sample end (not a stationary bootstrap with random block lengths). "
    "Blocks are drawn independently from anywhere in the window, so volatility clustering is kept "
    "only within a block: at lags 1-4, lag k keeps about (5-k)/5 of the sample's over a horizon well "
    "beyond 5 sessions (more over a shorter one), and none is kept from lag 5. The fan does not start "
    "from the current volatility level. Each day's shock is one of the sample's demeaned daily "
    "returns, with the drift added on top."
)

BOOTSTRAP_TEXT_KO = (
    "블록 부트스트랩: 추정 구간의 일별 로그수익률에서 평균을 뺀 값을 5거래일 고정 길이 블록 단위로 "
    "다시 뽑으며, 표본 끝에 닿으면 처음으로 이어 붙이는 원형 방식입니다(블록 길이가 무작위인 "
    "정상(stationary) 부트스트랩이 아닙니다). 블록은 구간 어디에서나 서로 독립적으로 뽑으므로 "
    "변동성 군집은 한 블록 안에서만 유지됩니다. 시차 1-4에서는 분석 기간이 5거래일보다 충분히 길 때 "
    "시차 k에 표본의 약 (5-k)/5가 남고(기간이 짧으면 더 많이 남음), 시차 5부터는 전혀 남지 않습니다. "
    "팬 차트는 현재 변동성 수준에서 출발하지 않습니다. 하루하루의 충격은 표본의 평균을 뺀 일별 "
    "수익률 가운데 하나이고, 그 위에 드리프트(추세 가정)를 더합니다."
)


def bootstrap_disclosure(model):
    """The resampling scheme for the model id 'bootstrap'; None for every other model.

    Keyed on the model id, not on a result, because the scheme is fixed per model and
    a stored ResearchRun records only parameters.model."""
    if model != "bootstrap":
        return None
    return {
        "method": "circular_block_bootstrap",
        "block_sessions": BOOTSTRAP_BLOCK_SESSIONS,
        "block_length": "fixed",
        "resampled": "demeaned_daily_log_returns",
        "within_block_lag_retention": "(5-k)/5 for k=1..4 over a long horizon, more over a short one",
        "clustering_from_lag": BOOTSTRAP_BLOCK_SESSIONS,   # none of it is kept from this lag on
        "current_vol_level": "not_used",
        "description": BOOTSTRAP_TEXT,
    }
