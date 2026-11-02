"""Descriptive rate-model metadata; no calibration or pricing decisions."""


def theta_semantics(params):
    """Retain theta's numeric value while identifying its model-specific role."""
    if params.model == "hull_white":
        return {
            "value": params.theta,
            "role": "regression_mean_not_used_by_hull_white_drift",
            "used_by_simulation": False,
            "label": "Regression mean · unused by HW drift",
            "label_ko": "회귀 평균 · HW 드리프트에 미사용",
            "note": "Hull–White uses a time-dependent drift fitted from the input curve; this regression mean is not its long-run mean.",
            "note_ko": "Hull–White는 입력 곡선에서 맞춘 시간 가변 드리프트를 사용합니다. 이 회귀 평균은 모형의 장기 평균이 아닙니다.",
        }
    return {
        "value": params.theta,
        "role": "long_run_mean",
        "used_by_simulation": True,
        "label": "Theta · long-run mean",
        "label_ko": "Theta · 장기 평균",
        "note": "Theta is the long-run mean used in this model's mean-reversion drift.",
        "note_ko": "Theta는 이 모형의 평균회귀 드리프트에서 사용하는 장기 평균입니다.",
    }
