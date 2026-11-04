"""Say what the ETF sleeve numbers are, without changing them (§10 NEW-M6-04, NEW-M6-05).

* NEW-M6-04, undefined Sharpe: a sleeve whose daily P&L does not vary (a trend switch that never held
  the fund earns only the fixed cash rate; a flat price leaves every sleeve constant) has a Sharpe of
  0/0. `strategies.summary` guards only `vol > 0`, so float rounding showed about 1e16, or 0.00 at the
  lengths where the rounding cancels. `sleeve_summary` keeps every number of `S.summary` and marks
  such a Sharpe as not defined (`None`), with a status.
* NEW-M6-05, conventions: the sleeves run with a cash warm-up, a fixed cash rate, a gross full-window
  Sharpe, costless daily constant-weight rebalancing and family-level study cards. `sleeve_conventions`
  records them from the same arguments `etf_workflow.analyze` passes to the strategy functions, and
  `conventions_text` / `conventions_korean` state them on every screen.

Numerical tolerance rule (NEW-M6-04). A P&L counts as "no variation" when its sample standard deviation
(ddof=1) is at or below RELATIVE_SD_TOLERANCE x max(1, max|p|), i.e. a relative standard deviation of at
most 1e-10. This is a tolerance, not an exact zero test: a constant cash P&L leaves a rounding residue
of order 1e-20 (5.4e-20 at 505 closes; exactly 0 at some lengths, the first being 547 closes), and a
P&L with a real but tiny variation at or below the tolerance is also reported as not defined. In a probe of 400 driftless walks x 2 cost levels, every
trend P&L that held the fund had a relative sd above 1.7e-3 and every cash-only one at most 5.5e-20, so
the rule agreed with an exact max - min == 0 test on all of them. The same 1e-10 rule guards the crypto
z score (core/crypto/analytics.py).

Nothing here recomputes a model: `core.quant.strategies` is a frozen harness file and stays unchanged,
and for a P&L that varies (above the tolerance) every existing number keeps its value. The texts carry the same number tokens
in English and Korean.
"""
from __future__ import annotations

import math

import numpy as np

from core.quant import strategies as S

COMPUTED = "COMPUTED"
NO_VARIATION = "NOT_DEFINED_NO_VARIATION"
NON_FINITE = "NOT_DEFINED_NON_FINITE"
RELATIVE_SD_TOLERANCE = 1e-10

SLEEVES = ("trend", "vol_target", "buy_hold")
_NAMES = {"trend": "the trend switch", "vol_target": "the vol target", "buy_hold": "buy-and-hold"}
_NAMES_KO = {"trend": "추세 전환", "vol_target": "변동성 목표", "buy_hold": "매수 후 보유"}


# NEW-M6-04: undefined Sharpe -------------------------------------------------------------
def sleeve_summary(pnl) -> dict:
    """`S.summary(pnl)` unchanged, plus `sharpe_status`; `sharpe` is None when it is not defined.

    COMPUTED: the P&L varies (sd above the tolerance rule in the module docstring); `sharpe` is the
    identical `S.summary` value. NOT_DEFINED_NO_VARIATION: the P&L does not vary (or has fewer than
    two values). NOT_DEFINED_NON_FINITE: the P&L contains NaN or infinity. Every other key is
    `S.summary`'s own value in every case.
    """
    s = S.summary(pnl)
    p = np.asarray(pnl, dtype=float)
    if not np.all(np.isfinite(p)):
        return {**s, "sharpe": None, "sharpe_status": NON_FINITE}
    if p.size >= 2 and float(np.std(p, ddof=1)) > RELATIVE_SD_TOLERANCE * max(1.0, float(np.max(np.abs(p)))):
        return {**s, "sharpe_status": COMPUTED}
    return {**s, "sharpe": None, "sharpe_status": NO_VARIATION}


def sharpe_text(s, digits: int = 2):
    """The Sharpe as shown (two decimals), or None when it is not defined."""
    v = (s or {}).get("sharpe")
    return f"{v:.{digits}f}" if v is not None and math.isfinite(v) else None


def sharpe_tooltip(s) -> str:
    """Why a Sharpe tile shows n/a; '' for a defined Sharpe."""
    status = (s or {}).get("sharpe_status")
    if status == NO_VARIATION:
        return ("Not defined: the daily P&L did not vary over the window (for example cash only), "
                "so the Sharpe ratio is undefined. It is not 0.")
    if status == NON_FINITE:
        return "Not defined: the daily P&L contains non-finite values."
    return ""


def _undefined(sl, status):
    return [k for k in SLEEVES if ((sl or {}).get(k) or {}).get("sharpe_status") == status]


def _join_en(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def sharpe_note(sl):
    """English note naming the sleeves whose Sharpe is not defined, or None when all are defined."""
    out = []
    flat, bad = _undefined(sl, NO_VARIATION), _undefined(sl, NON_FINITE)
    if flat:
        out.append(f"Sharpe n/a for {_join_en([_NAMES[k] for k in flat])}: the daily P&L did not vary over this "
                   "window (for example a sleeve that held only cash at the fixed cash rate), so the ratio is "
                   "undefined; it is not 0 and not a large positive Sharpe.")
    if bad:
        out.append(f"Sharpe n/a for {_join_en([_NAMES[k] for k in bad])}: the daily P&L contains non-finite values.")
    return " ".join(out) or None


def sharpe_note_korean(sl):
    """Korean note with the same number tokens as `sharpe_note`, or None."""
    out = []
    flat, bad = _undefined(sl, NO_VARIATION), _undefined(sl, NON_FINITE)
    if flat:
        out.append(f"{', '.join(_NAMES_KO[k] for k in flat)}의 샤프비율은 계산 불가입니다: 이 기간 일별 손익에 "
                   "변동이 없어(예: 고정 현금 금리만 받은 현금 보유 전략) 비율이 정의되지 않습니다. "
                   "0이나 큰 양의 샤프비율이 아닙니다.")
    if bad:
        out.append(f"{', '.join(_NAMES_KO[k] for k in bad)}의 샤프비율은 계산 불가입니다: "
                   "일별 손익에 유한하지 않은 값이 있습니다.")
    return " ".join(out) or None


# NEW-M6-05: conventions --------------------------------------------------------------------
def sleeve_conventions(*, window_sessions: int, trend_lookback: int, vol_window: int, cash_rate_annual: float,
                       trend_card=None, vol_target_card=None) -> dict:
    """Record of the sleeve conventions, built from the arguments passed to the strategy functions.

    `window_sessions` is the number of daily P&L values (daily returns), i.e. closes - 1: the default
    504-close screen has 503. The trend switch first decides at row `trend_lookback`
    (strategies.trend_switch rebalances from t = lookback), so its first `trend_lookback` daily returns
    are in cash; the vol target first decides at row `vol_window + 1` (strategies.vol_target rebalances
    from t = window + 1). `exposure_trend` averages the trend weight from row `trend_lookback` to the last
    row, and the last row's weight is never held.
    """
    window, lookback, vol = int(window_sessions), int(trend_lookback), int(vol_window)
    rate = float(cash_rate_annual)
    if not (0 < lookback < window and 0 < vol < window and math.isfinite(rate)):
        raise ValueError("Invalid sleeve conventions")
    return {"window_daily_returns": window,
            "trend_warmup_daily_returns": lookback,
            "trend_warmup_share": lookback / window,
            "vol_target_warmup_daily_returns": vol + 1,
            "cash_rate_annual": rate,
            "cash_rate_basis": "FIXED_ASSUMPTION_NOT_OBSERVED",
            "sharpe_basis": "GROSS_NOT_EXCESS_OF_CASH",
            "sharpe_window": "FULL_WINDOW_INCLUDING_WARMUP",
            "exposure_first_row": lookback,
            "exposure_window": "WARMUP_END_TO_LAST_ROW_INCLUDING_UNHELD_FINAL_ROW",
            "buy_hold_basis": "NO_WARMUP_NO_CASH_NO_COST",
            "comparison": "NOT_LIKE_FOR_LIKE",
            "vol_target_weight_reset": "CONSTANT_WEIGHT_RESET_EVERY_SESSION_AT_NO_COST",
            "study_verdict_scope": "FAMILY_CARD_NOT_THIS_FUND",
            "trend_card": trend_card, "vol_target_card": vol_target_card}


def _rate(c) -> str:
    return f"{c['cash_rate_annual'] * 100:g}%"


def _cards(c, sep):
    return sep.join(x for x in (c.get("trend_card"), c.get("vol_target_card")) if x)


def conventions_text(c: dict) -> str:
    rate, cards = _rate(c), _cards(c, " and ")
    return (f"Sleeve conventions: the trend switch first decides after {c['trend_warmup_daily_returns']} sessions "
            f"(its 10-month average), so the first {c['trend_warmup_daily_returns']} of these "
            f"{c['window_daily_returns']} daily returns ({c['trend_warmup_share']:.0%}) are a warm-up held in cash, "
            f"and the vol target's first {c['vol_target_warmup_daily_returns']} likewise. "
            f"Cash earns a fixed {rate} a year (assumption: {rate} / 252 per session), not an observed rate, "
            "the same for every currency. "
            "Each Sharpe is the mean daily return × 252 over its standard deviation × √252 on the whole window, "
            "warm-up included, and is gross, not in excess of the cash rate; buy-and-hold has no warm-up, "
            "no cash and no cost. The warm-up replaces the fund's return with the fixed cash return on those "
            "sessions and lowers the measured volatility, so the comparison with buy-and-hold is not "
            "like-for-like. The invested share averages the trend weight from the end of the warm-up to the "
            "last close, including the last close's weight, which is never held. "
            "A vol-target weight below 1 is reset to that weight every session at no cost. "
            + (f"The study verdicts are those of the family cards ({cards}), not a test of this fund."
               if cards else "The study verdicts are those of the family cards, not a test of this fund."))


def conventions_korean(c: dict) -> str:
    rate, cards = _rate(c), _cards(c, ", ")
    return (f"전략 계산 관례: 추세 전환은 {c['trend_warmup_daily_returns']}거래일(10개월 평균)이 지나야 처음 "
            f"판단하므로 이 {c['window_daily_returns']}개 일별 수익률 가운데 처음 "
            f"{c['trend_warmup_daily_returns']}개({c['trend_warmup_share']:.0%})는 현금으로 보유한 준비 구간이며, "
            f"변동성 목표도 처음 {c['vol_target_warmup_daily_returns']}개가 같습니다. "
            f"현금은 연 {rate} 고정 수익을 받습니다(가정: 거래일당 {rate} / 252). 관측 금리가 아니며 통화와 관계없이 같습니다. "
            "각 샤프비율은 준비 구간을 포함한 전체 기간에서 일별 수익률 평균 × 252를 표준편차 × √252로 나눈 값이며, "
            "현금 금리를 뺀 초과 수익 기준이 아닌 총수익 기준입니다. 매수 후 보유에는 준비 구간, 현금, 비용이 없습니다. "
            "준비 구간은 그 거래일의 펀드 수익률을 고정 현금 수익률로 대신하고 측정 변동성을 낮추므로, "
            "매수 후 보유와 같은 조건의 비교가 아닙니다. "
            "투자 비중은 준비 구간이 끝난 뒤부터 마지막 종가까지의 추세 비중 평균이며, 실제로 보유하지 않는 "
            "마지막 종가의 비중도 포함합니다. "
            "변동성 목표 비중이 1보다 작으면 매 거래일 비용 없이 그 비중으로 다시 맞춘다고 봅니다. "
            + (f"연구 판정은 계열 카드({cards})의 판정이며 이 펀드를 검정한 것이 아닙니다."
               if cards else "연구 판정은 계열 카드의 판정이며 이 펀드를 검정한 것이 아닙니다."))
