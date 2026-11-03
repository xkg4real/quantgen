"""Say what three option-board numbers are, without changing them (§10 M4-N4, M4-N7, M4-N9).

* Box (M4-N4): an adjacent-strike box is a 2.5-point payoff, so quote rounding and
  spreads dominate its implied rate. It is priced only from four two-sided legs and is
  shown with its sensitivity and the range at the quoted bids and asks, as a
  quote-quality check rather than a funding rate.
* Hedge simulation (M4-N7): the GBM engine simulates at sigma_true = sigma_h, so the
  expected hedge P&L is zero by construction and the sign of the simulated mean is noise.
* MFIV (M4-N9): the strip stops at the quoted strikes, so the omitted wings bias the
  model-free variance downward; the covered range is stated.

Nothing here recomputes a model: `core.ficc.equity_deriv` is unchanged and valid
inputs keep every existing number.
"""
from __future__ import annotations

import math
from typing import Optional

from core.ficc import equity_deriv as ED
from core.ficc.common import BP, FICCError

BOX_SCOPE = "Adjacent-strike box from quoted mids; a quote-quality check, not a funding-rate estimate"
HEDGE_SCOPE = ("GBM engine simulates at sigma_true = sigma_h: the expected hedge P&L is 0 bp by construction and the "
               "sign of the simulated mean is Monte Carlo noise; not an estimate of the option seller's return")
MFIV_SCOPE = ("Finite strike strip: options outside the strike range are omitted, which biases the model-free "
              "variance downward; not the full expected variance")


# Box -------------------------------------------------------------------------------
def _two_sided(bid, ask) -> bool:
    # The same rule chain_implied_vols applies inline in core/ficc/equity_deriv.py (bid and ask, bid > 0,
    # ask >= bid); kept here so that model module stays unchanged.
    return bid is not None and ask is not None and bid > 0 and ask >= bid


def box_check(quotes, T: float, F: float, *, live: bool):
    """(box, check): the unchanged `ED.box_rate` result or None, and what was checked.

    The strikes are the existing choice (the nearest strike at or below F and the
    nearest above). The box is priced only when all four legs have two-sided quotes:
    a box from last prints or one-sided quotes is not a rate.
    """
    below = [q.strike for q in quotes if q.strike <= F]
    above = [q.strike for q in quotes if q.strike > F]
    if not below or not above:
        return None, {"status": "NOT_RUN", "reason": "no_bracketing_strikes", "scope": BOX_SCOPE}
    k1, k2 = max(below), min(above)
    if not live:
        return None, {"status": "NOT_RUN", "reason": "market_closed", "k1": k1, "k2": k2, "scope": BOX_SCOPE}
    by = {q.strike: q for q in quotes}
    a, b = by[k1], by[k2]
    legs = {f"call {k1:g}": (a.call_bid, a.call_ask), f"call {k2:g}": (b.call_bid, b.call_ask),
            f"put {k2:g}": (b.put_bid, b.put_ask), f"put {k1:g}": (a.put_bid, a.put_ask)}
    missing = [name for name, (bid, ask) in legs.items() if not _two_sided(bid, ask)]
    if missing:
        return None, {"status": "NOT_RUN", "reason": "legs_not_two_sided", "k1": k1, "k2": k2,
                      "legs_without_two_sided_quote": missing, "scope": BOX_SCOPE}
    try:
        box = ED.box_rate(quotes, T, k1=k1, k2=k2)
    except (FICCError, ValueError) as exc:
        return None, {"status": "NOT_RUN", "reason": "not_priced", "k1": k1, "k2": k2, "error": str(exc),
                      "scope": BOX_SCOPE}
    width = k2 - k1
    # At the touch: buying the box pays the asks on its long legs and receives the bids on its short legs.
    bought = a.call_ask - b.call_bid + b.put_ask - a.put_bid
    sold = a.call_bid - b.call_ask + b.put_bid - a.put_ask
    check = {"status": "COMPUTED", "k1": k1, "k2": k2, "width_pts": width, "box_price": box["box"],
             "box_bought_at_quotes": bought, "box_sold_at_quotes": sold,
             "rate_bought_at_quotes": -math.log(bought / width) / T if bought > 0 else None,
             "rate_sold_at_quotes": -math.log(sold / width) / T if sold > 0 else None,
             "bp_per_0_01pt": 0.01 / (box["box"] * T) / BP, "scope": BOX_SCOPE}
    return box, check


def _box_parts(s: dict):
    box, check = s.get("box"), s.get("box_check") or {}
    return box, check, box_computed(s)


def box_computed(s: dict) -> bool:
    """A priced box with its band and sensitivity (older saved results may have the box without a check)."""
    return bool(s.get("box")) and (s.get("box_check") or {}).get("status") == "COMPUTED"


def box_text(s: dict) -> str:
    box, check, computed = _box_parts(s)
    if box:
        head = (f"The adjacent-strike ATM box prices at {box['rate']:.2%} from mids against {s['rate']:.2%}"
                if not computed else
                f"The adjacent-strike ATM box ({check['k1']:g}/{check['k2']:g}, {check['width_pts']:g} points wide) "
                f"prices at {box['rate']:.2%} from mids against {s['rate']:.2%}; each 0.01 point of box price moves "
                f"it by {check['bp_per_0_01pt']:.0f} bp")
        if computed:
            bought, sold = check["rate_bought_at_quotes"], check["rate_sold_at_quotes"]
            head += (f", and at the quoted bids and asks it spans {bought:.2%} bought to {sold:.2%} sold"
                     if bought is not None and sold is not None else
                     ", and at the quoted bids and asks one side leaves no positive box price")
        return head + ". It is a quote-quality check, not a funding-rate estimate."
    if check.get("reason") == "legs_not_two_sided":
        n = len(check["legs_without_two_sided_quote"])
        return (f"No ATM box was priced: {n} of its 4 legs lack a two-sided quote, and a box from last prints "
                f"or one-sided quotes is not a rate.")
    if check.get("reason") == "market_closed":
        return "No ATM box was priced: the market is closed, and a box from last prints is not a rate."
    return "No ATM box could be priced from the mids."


def box_korean(s: dict) -> str:
    box, check, computed = _box_parts(s)
    if box:
        head = (f"인접 행사가 ATM 박스는 중간값 기준 {box['rate']:.2%}이며 비교 금리는 {s['rate']:.2%}입니다"
                if not computed else
                f"인접 행사가 ATM 박스({check['k1']:g}/{check['k2']:g}, 간격 {check['width_pts']:g}포인트)는 "
                f"중간값 기준 {box['rate']:.2%}이며 비교 금리는 {s['rate']:.2%}입니다. 박스 가격이 0.01포인트 바뀔 때마다 "
                f"이 값은 {check['bp_per_0_01pt']:.0f} bp 움직입니다")
        if computed:
            bought, sold = check["rate_bought_at_quotes"], check["rate_sold_at_quotes"]
            head += (f". 매수·매도호가로 계산하면 살 때 {bought:.2%}, 팔 때 {sold:.2%}입니다"
                     if bought is not None and sold is not None else
                     ". 매수·매도호가로 계산하면 한쪽은 박스 가격이 양수가 되지 않습니다")
        return head + ". 조달금리 추정치가 아니라 호가 품질 점검입니다."
    if check.get("reason") == "legs_not_two_sided":
        n = len(check["legs_without_two_sided_quote"])
        return (f"ATM 박스를 산출하지 않았습니다: 4개 다리 중 {n}개에 양방향 호가가 없으며, "
                f"마지막 체결가나 한쪽 호가로 만든 박스는 금리가 아닙니다.")
    if check.get("reason") == "market_closed":
        return "ATM 박스를 산출하지 않았습니다: 장이 마감되어 마지막 체결가로 만든 박스는 금리가 아닙니다."
    return "중간값으로 가격을 산출할 수 있는 ATM 박스가 없습니다."


def box_tooltip(s: dict) -> str:
    box, check, computed = _box_parts(s)
    if computed:
        bought, sold = check["rate_bought_at_quotes"], check["rate_sold_at_quotes"]
        band = (f"{bought:.2%} bought, {sold:.2%} sold" if bought is not None and sold is not None
                else "one side leaves no positive box price")
        return (f"{check['k1']:g}/{check['k2']:g} box, {check['width_pts']:g} points wide, from four two-sided mids. "
                f"{check['bp_per_0_01pt']:.0f} bp per 0.01 point of box price; at the quoted bids/asks {band}. "
                "Quote-quality check, not a funding-rate estimate.")
    return box_text(s)


# Hedge simulation ---------------------------------------------------------------------
def hedge_scope(*, sigma_hedge: float, engine: str = "gbm", sigma_true: Optional[float] = None,
                drift_daily: Optional[float] = None, cost_bps: float = 0.0) -> dict:
    """Built in `snapshot` from the same arguments it passes to the simulation.

    The simulation draws at `sigma_true or sigma_hedge`, so a missing or zero sigma_true is sigma_h.
    """
    zero_mean = engine == "gbm" and (not sigma_true or sigma_true == sigma_hedge) and drift_daily is None \
        and not cost_bps
    return {"expected_mean_status": "ZERO_BY_CONSTRUCTION" if zero_mean else "MODEL_RESULT",
            "expected_mean_pnl_bp": 0.0 if zero_mean else None, "scope": HEDGE_SCOPE if zero_mean else None}


def same_vol(s: dict) -> bool:
    """True only when snapshot recorded that the simulation ran at sigma_true = sigma_h."""
    return (s.get("hedge_scope") or {}).get("expected_mean_status") == "ZERO_BY_CONSTRUCTION"


def hedge_text(s: dict) -> str:
    if not same_vol(s):
        return ""
    return ("GBM engine: paths are simulated at σ_true = σ_h, so the expected hedge P&L is 0 bp by construction and "
            "the break-even vol equals σ_h up to Monte Carlo noise; the simulated mean is sampling noise and its sign "
            "is not a result. The GARCH-t engine's path volatility is not set to σ_h.")


def hedge_korean(s: dict) -> str:
    if not same_vol(s):
        return ""
    return ("GBM 엔진: 경로를 σ_true = σ_h로 생성하므로 헤지 손익의 기댓값은 정의상 0 bp이고 손익분기 변동성은 "
            "몬테카를로 잡음 범위에서 σ_h와 같습니다. 모의 평균은 표본 잡음이며 그 부호는 결과가 아닙니다. "
            "GARCH-t 엔진의 경로 변동성은 σ_h에 고정되지 않습니다.")


# MFIV strip ------------------------------------------------------------------------------
def mfiv_strip(s: dict) -> dict:
    """The strike range the strip covered, in forward moneyness and ATM-vol standard deviations."""
    mv, F = s.get("mfiv") or {}, s.get("F")
    if not mv.get("n_strikes") or mv.get("k_min") is None or not F:
        return {"status": "NOT_RUN", "n_strikes": 0, "k_min": None, "k_max": None, "k0": None,
                "lower_moneyness": None, "upper_moneyness": None, "lower_atm_vol_sd": None,
                "upper_atm_vol_sd": None, "scope": MFIV_SCOPE}
    atm = s.get("atm")
    iv, T = getattr(atm, "iv", None), s.get("T")
    sd = iv * math.sqrt(T) if iv and T and math.isfinite(iv * math.sqrt(T)) and iv * math.sqrt(T) > 0 else None
    k_min, k_max = float(mv["k_min"]), float(mv["k_max"])
    return {"status": "COMPUTED", "n_strikes": int(mv["n_strikes"]), "k_min": k_min, "k_max": k_max,
            "k0": mv.get("k0"), "lower_moneyness": k_min / F - 1, "upper_moneyness": k_max / F - 1,
            "lower_atm_vol_sd": math.log(k_min / F) / sd if sd else None,
            "upper_atm_vol_sd": math.log(k_max / F) / sd if sd else None, "scope": MFIV_SCOPE}


def mfiv_text(strip: dict) -> str:
    if strip["status"] != "COMPUTED":
        return ""
    sd = (f" (about {strip['lower_atm_vol_sd']:+.1f} to {strip['upper_atm_vol_sd']:+.1f} ATM-vol standard deviations)"
          if strip["lower_atm_vol_sd"] is not None else "")
    return (f"The strip covers strikes {strip['lower_moneyness']:+.1%} to {strip['upper_moneyness']:+.1%} of the "
            f"forward{sd}; options outside it are omitted, which biases the model-free vol downward: a "
            "truncated-strip value, not the full expected variance.")


def mfiv_korean(strip: dict) -> str:
    if strip["status"] != "COMPUTED":
        return ""
    sd = (f" (ATM 변동성 기준 표준편차 약 {strip['lower_atm_vol_sd']:+.1f}~{strip['upper_atm_vol_sd']:+.1f})"
          if strip["lower_atm_vol_sd"] is not None else "")
    return (f"스트립은 선도 대비 {strip['lower_moneyness']:+.1%}~{strip['upper_moneyness']:+.1%} 행사가만 "
            f"포함합니다{sd}. 이 범위 밖 옵션은 빠지므로 모형 비의존 변동성은 낮게 편향되며, 전체 기대분산이 아니라 "
            "절단된 스트립 값입니다.")
