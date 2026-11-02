"""Explicit interpretation of existing Lab outputs, without rescoring them.

The metadata describes the current live Lab implementation. Historical cards
are kept intact and receive separate reading notes only when their pair family
is identified. None of these notes changes a gate or validates a model.
"""
from __future__ import annotations


def assumption_summary(family, *, cash_daily, has_regime):
    return {
        "schema": "quantgen.strategy-assumptions/1",
        "cash_rate_per_session": float(cash_daily),
        "cash_rate_source": "fixed_assumption_not_historical_curve",
        "cash_allocation": "1_minus_sum_weights_only_when_all_weights_nonnegative",
        "sharpe_basis": "net_returns_without_risk_free_subtraction",
        "annualization_sessions": 252,
        "momentum_signal_cash_rate_per_session": 0.0 if family in {"trend_switch", "tsmom"} else None,
        "pairs_weighting": "formation_ols_gross_normalized_not_dollar_neutral" if family == "pairs" else None,
        "pairs_cointegration_validation": "NOT_PERFORMED" if family == "pairs" else None,
        "regime_threshold_basis": "whole_oos_median_retrospective" if has_regime else None,
    }


def assumption_lines(info, locale="en"):
    if not isinstance(info, dict) or info.get("schema") != "quantgen.strategy-assumptions/1":
        return []
    rate = f"{info['cash_rate_per_session']:.8f}"
    if locale == "ko":
        lines = [
            f"현금·Sharpe 가정: 매도 포지션이 없는 행에서 현금 비중 1 − sum(weights)에 거래일당 {rate}를 "
            "적용합니다(고정 3% / 252, 역사적 금리 곡선 아님). 음수 현금에는 같은 차입금리를 적용합니다. "
            "Sharpe는 비용 차감 수익률에서 무위험 수익률을 추가로 빼지 않으며, 연율화는 252세션입니다. "
            "현금 가정에 따라 결과가 달라질 수 있습니다."
        ]
        if info.get("momentum_signal_cash_rate_per_session") is not None:
            lines.append("모멘텀 신호 가정: 현재 Lab의 MOP 방식 부호 규칙은 신호 금리를 0으로 두므로 원수익의 부호를 "
                         "사용합니다. 손익의 고정 현금금리 3%와 별개이며, 역사적 초과수익을 사용하는 MOP 논문의 재현이 아닙니다.")
        if info.get("pairs_weighting"):
            lines.extend([
                "페어 매수·매도형 노출: 형성 구간 회귀계수 b로 비중을 gross × [pos, −pos×b] / (1+|b|)로 정합니다. "
                "순노출은 gross × pos × (1−b) / (1+|b|)이며, 일반적으로 달러 중립이 아닙니다. "
                "b<0이면 두 다리가 같은 방향일 수 있습니다.",
                "페어 회귀는 Engle–Granger의 첫 단계입니다. 현재 Lab 실행은 정식 공적분 검증을 수행하지 않으며, "
                "잔차 ADF 또는 과거 카드의 공적분 표기를 검증 통과로 해석하지 않습니다."
            ])
        if info.get("regime_threshold_basis"):
            lines.append("레짐 구분은 사후 설명입니다. 변동성 자체는 직전 관측으로 계산하지만 고·저 변동성 경계는 "
                         "전체 OOS 표본의 중앙값이므로 당시 알려진 경계나 인과적 매매 신호가 아닙니다. "
                         "뒤의 관측이 추가되면 앞부분의 분류가 바뀔 수 있습니다.")
        return lines
    lines = [
        f"Cash and Sharpe assumptions: rows without short positions apply {rate} per session to "
        "cash weight 1 − sum(weights) (fixed 3% / 252, not a historical rate curve). Negative cash "
        "is borrowed at that same rate. Sharpe uses net returns without subtracting a risk-free return; "
        "annualization uses 252 sessions. Results can be sensitive to the cash assumption."
    ]
    if info.get("momentum_signal_cash_rate_per_session") is not None:
        lines.append("Momentum signal assumption: the Lab's MOP-style sign rule uses a zero signal cash rate, "
                     "so its sign is based on raw returns. This is separate from the fixed 3% cash rate in P&L "
                     "and is not a reproduction of the paper's historical excess-return rule.")
    if info.get("pairs_weighting"):
        lines.extend([
            "Long/short pairs exposure: the formation regression coefficient b gives weights "
            "gross × [pos, −pos×b] / (1+|b|). Net exposure is gross × pos × (1−b) / (1+|b|), "
            "so the book is generally not dollar-neutral. For b<0 both legs can point in the same direction.",
            "The pair regression is Engle–Granger step 1. This Lab run does not perform a formal "
            "cointegration validation; residual ADF values or historical cointegration labels are not a validation pass."
        ])
    if info.get("regime_threshold_basis"):
        lines.append("Regime split is retrospective: volatility uses preceding observations, but the high/low "
                     "cutoff is the median over the whole OOS sample. It is not a threshold known at the time "
                     "or a causal trading signal; later observations can change earlier classifications.")
    return lines


def historical_card_lines(card, locale="en"):
    """Separate reading notes for identifiable stored pair cards; never edit them."""
    card_id = str(card.get("card_id") or "")
    if not (card_id.startswith("S_E8_") or card.get("family") in {"E8", "pairs"}):
        return []
    if locale == "ko":
        return [
            "과거 페어 카드 해석 안내: 추정 잔차의 일반 ADF 기각 비율(share_cointegrated 표기 포함)은 "
            "Engle–Granger 공적분 검정의 p값이나 통과율이 아닙니다. 아래 원문·수치·판정은 보존된 역사적 "
            "기록이며, 현재 공적분 유효성이나 새 연구 판정을 확정하지 않습니다.",
            "과거 달러 중립 표현 안내: 현재 페어의 매수·매도형 비중은 회귀계수로 총노출을 정규화한 비중이며 일반적으로 "
            "순노출이 0이 아닙니다. 회귀계수가 음수면 두 다리가 같은 방향일 수 있습니다."
        ]
    return [
        "Historical pair-card reading note: the ordinary ADF rejection share for fitted residuals "
        "(including the share_cointegrated label) is not an Engle–Granger cointegration p-value or pass rate. "
        "The original text, numbers and decision remain historical records; they do not establish current "
        "cointegration validity or a new research verdict.",
        "Historical dollar-neutral wording: current long/short pair weights are gross-normalized using the regression "
        "coefficient and generally have nonzero net exposure. A negative coefficient can put both legs in the same direction."
    ]
