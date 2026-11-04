"""Say what the ETF sleeve numbers are, without changing them (§10 NEW-M6-04, NEW-M6-05).

* NEW-M6-04, undefined Sharpe: a sleeve whose daily P&L does not vary has a standard deviation of 0, so
  its Sharpe is undefined. A trend switch that never held the fund earns only the fixed cash rate: its
  mean is positive (0.03 a year), so the ratio is a positive number over 0, not 0/0 (0/0 only for a
  P&L that is 0 throughout, such as buy-and-hold on a flat price). `strategies.summary` guards only
  `vol > 0`, so float rounding showed about 1e16, or 0.00 at the lengths where the rounding cancels.
  `sleeve_summary` keeps every number of `S.summary` and marks such a Sharpe as not defined (`None`),
  with a status. On a flat price, buy-and-hold and the vol target (whose realised vol is 0, so it stays
  in cash) never vary; the trend switch does not vary either when its 210-session average equals the
  price exactly (as at 100.0), but at many other flat levels float rounding of that average puts it in
  the fund on some rows, so its P&L moves between 0 and the cash rate and its Sharpe is defined (20.80
  at 100.37 over 505 closes, the same number as before).
* NEW-M6-05, conventions: the sleeves run with a cash warm-up, a fixed cash rate, a full-window Sharpe
  on raw (not excess-of-cash) returns after the sleeve's cost, costless daily constant-weight
  rebalancing and family-level study cards. `sleeve_conventions` records them from the same arguments
  `etf_workflow.analyze` passes to the strategy functions, and `conventions_text` /
  `conventions_korean` state them on every screen.

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
        return ("Not defined: the daily P&L did not vary over the window (for example cash only), so its "
                "standard deviation is 0 and the Sharpe ratio is undefined. Any number here would be float "
                "rounding, not a result.")
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
                   "window (for example a sleeve that held only cash at the fixed cash rate), so the standard "
                   "deviation is 0 and the ratio is undefined; a figure of 0 or a very large number here would "
                   "be float rounding, not a result.")
    if bad:
        out.append(f"Sharpe n/a for {_join_en([_NAMES[k] for k in bad])}: the daily P&L contains non-finite values.")
    return " ".join(out) or None


def sharpe_note_korean(sl):
    """Korean note with the same number tokens as `sharpe_note`, or None."""
    out = []
    flat, bad = _undefined(sl, NO_VARIATION), _undefined(sl, NON_FINITE)
    if flat:
        out.append(f"{', '.join(_NAMES_KO[k] for k in flat)}의 샤프비율은 계산 불가입니다: 이 기간 일별 손익에 "
                   "변동이 없어(예: 고정 현금 금리만 받은 현금 보유 전략) 표준편차가 0이므로 비율이 정의되지 "
                   "않습니다. 여기서 0이나 매우 큰 값이 나온다면 결과가 아니라 부동소수점 반올림 오차입니다.")
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
    row, and the last row's weight is never held. `trend_card_loaded` / `vol_target_card_loaded` start
    as None (not known) and are set by the caller once the study cards are loaded (`with_loaded_cards`).
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
            "sharpe_basis": "RAW_RETURN_NOT_EXCESS_OF_CASH_AFTER_SLEEVE_COST",
            "sharpe_window": "FULL_WINDOW_INCLUDING_WARMUP",
            "exposure_first_row": lookback,
            "exposure_window": "WARMUP_END_TO_LAST_ROW_INCLUDING_UNHELD_FINAL_ROW",
            "buy_hold_basis": "NO_WARMUP_NO_CASH_NO_COST",
            "comparison": "NOT_LIKE_FOR_LIKE",
            "vol_target_weight_reset": "CONSTANT_WEIGHT_RESET_EVERY_SESSION_AT_NO_COST",
            "study_verdict_scope": "FAMILY_CARD_NOT_THIS_FUND",
            "trend_card": trend_card, "vol_target_card": vol_target_card,
            "trend_card_loaded": None, "vol_target_card_loaded": None}


def with_loaded_cards(c: dict, loaded_card_ids) -> dict:
    """The record with whether each family card was among the loaded study cards (a new dict).

    Without a loaded card the verdict reads "not run", so the text must not call it the card's verdict.
    """
    ids = set(loaded_card_ids)
    return {**c, "trend_card_loaded": c.get("trend_card") in ids,
            "vol_target_card_loaded": c.get("vol_target_card") in ids}


def _rate(c) -> str:
    return f"{c['cash_rate_annual'] * 100:g}%"


def _cards(c):
    """(cards whose verdict is shown, cards that were not loaded); a card of unknown status counts as shown."""
    pairs = ((c.get("trend_card"), c.get("trend_card_loaded")), (c.get("vol_target_card"), c.get("vol_target_card_loaded")))
    return [x for x, ok in pairs if x and ok is not False], [x for x, ok in pairs if x and ok is False]


def _verdict_scope(c) -> str:
    shown, missing = _cards(c)
    out = []
    if shown or not missing:
        out.append(f"The study verdicts are those of the family card{'s' if len(shown) != 1 else ''} "
                   f"({_join_en(shown)}), not a test of this fund." if shown
                   else "The study verdicts are those of the family cards, not a test of this fund.")
    if missing:
        many = len(missing) > 1
        out.append(f"The family study card{'s' if many else ''} ({_join_en(missing)}) {'were' if many else 'was'} "
                   f"not loaded here, so no study verdict is shown for {'them' if many else 'it'} (not run); a "
                   "card's verdict covers the rule family, not this fund.")
    return " ".join(out)


def _verdict_scope_korean(c) -> str:
    shown, missing = _cards(c)
    out = []
    if shown or not missing:
        out.append(f"연구 판정은 계열 카드({', '.join(shown)})의 판정이며 이 펀드를 검정한 것이 아닙니다." if shown
                   else "연구 판정은 계열 카드의 판정이며 이 펀드를 검정한 것이 아닙니다.")
    if missing:
        out.append(f"계열 연구 카드({', '.join(missing)})를 여기서 불러오지 않아 연구 판정이 표시되지 않습니다"
                   "(not run). 카드의 판정은 이 펀드가 아니라 전략 계열에 대한 것입니다.")
    return " ".join(out)


def conventions_text(c: dict) -> str:
    rate = _rate(c)
    return (f"Sleeve conventions: the trend switch first decides after {c['trend_warmup_daily_returns']} sessions "
            f"(the length of its 10-month moving average), so the first {c['trend_warmup_daily_returns']} of these "
            f"{c['window_daily_returns']} daily returns ({c['trend_warmup_share']:.0%}) are a warm-up held in cash, "
            f"and the vol target's first {c['vol_target_warmup_daily_returns']} likewise. "
            f"Cash earns a fixed {rate} a year (assumption: {rate} / 252 per session), not an observed rate, "
            "the same for every currency. "
            "Each Sharpe is the mean daily return × 252 over its standard deviation × √252 on the whole window, "
            "warm-up included. It uses raw returns, not returns in excess of the cash rate, and the trend switch "
            "and vol target returns are after their per-side trading cost; buy-and-hold has no warm-up, no cash "
            "and no cost. The warm-up replaces the fund's return with the fixed cash return on those "
            "sessions and lowers the measured volatility, so the comparison with buy-and-hold is not "
            "like-for-like. The invested share averages the trend weight from the end of the warm-up to the "
            "last close, including the last close's weight, which is never held. "
            "A vol-target weight below 1 is reset to that weight every session at no cost. "
            + _verdict_scope(c))


def conventions_korean(c: dict) -> str:
    rate = _rate(c)
    return (f"전략 계산 관례: 추세 전환은 {c['trend_warmup_daily_returns']}거래일(10개월 이동평균 기간)이 지나야 처음 "
            f"판단하므로 이 {c['window_daily_returns']}개 일별 수익률 가운데 처음 "
            f"{c['trend_warmup_daily_returns']}개({c['trend_warmup_share']:.0%})는 현금으로 보유한 준비 구간이며, "
            f"변동성 목표도 처음 {c['vol_target_warmup_daily_returns']}개는 현금으로 보유한 준비 구간입니다. "
            f"현금은 연 {rate} 고정 수익을 받습니다(가정: 거래일당 {rate} / 252). 관측 금리가 아니며 통화와 관계없이 같습니다. "
            "각 샤프비율은 준비 구간을 포함한 전체 기간에서 일별 수익률 평균 × 252를 표준편차 × √252로 나눈 값이며, "
            "현금 금리를 빼지 않은 수익률 기준입니다. 추세 전환과 변동성 목표의 수익률은 편도 거래 비용을 뺀 값이고, "
            "매수 후 보유에는 준비 구간, 현금, 비용이 없습니다. "
            "준비 구간은 그 거래일의 펀드 수익률을 고정 현금 수익률로 대신하고 측정 변동성을 낮추므로, "
            "매수 후 보유와 같은 조건의 비교가 아닙니다. "
            "투자 비중은 준비 구간이 끝난 뒤부터 마지막 종가까지의 추세 비중 평균이며, 실제로 보유하지 않는 "
            "마지막 종가의 비중도 포함합니다. "
            "변동성 목표 비중이 1보다 작으면 매 거래일 비용 없이 그 비중으로 다시 맞춘다고 봅니다. "
            + _verdict_scope_korean(c))
