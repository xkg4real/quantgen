"""Short explanations for stock display only; no valuation or risk calculation.

Context is supplied by the caller's raw metadata. Unknown risk periods or
confidence levels stay unknown rather than acquiring a one-day/95% default.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .owner_ui_language.stock import TEXT


@dataclass(frozen=True)
class MetricHelp:
    label: str
    hover: str


def _text(key, language):
    en, ko = TEXT[key]
    return ko if language == "ko" else en


def financial_help(metric_id: str, language: str) -> MetricHelp:
    """Meaning and limitations; numerical values and their dates come from the profile."""
    metric = str(metric_id).lower()
    if metric not in ("per", "pbr", "roe", "psr"):
        raise KeyError(metric_id)
    return MetricHelp(_text("meaning_" + metric, language), _text("term_" + metric, language))


def stock_risk_help(kind, language, *, confidence=None, horizon_days=None, unit=None, basis=None) -> MetricHelp:
    """Explain the historical stock loss convention using explicit view metadata only."""
    kind = str(kind).lower()
    if kind not in ("var", "cvar"):
        raise KeyError(kind)
    ko = language == "ko"
    valid = isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and math.isfinite(confidence) and 0 < confidence < 1
    level = f"{confidence * 100:g}%" if valid else ("미확인" if ko else "unconfirmed")
    period_valid = isinstance(horizon_days, int) and not isinstance(horizon_days, bool) and horizon_days > 0
    period = (f"{horizon_days}일" if ko else f"{horizon_days}-day") if period_valid else ("기간 미확인" if ko else "period unconfirmed")
    metric = "CVaR" if kind == "cvar" else "VaR"
    label = f"{period} {metric} {level}" if valid else f"{period} {metric}"
    context = ((f"기간 {period} · 신뢰수준 {level}" if ko else f"Period {period} · confidence {level}")
               + (f" · {unit}" if unit else (" · 단위 미확인" if ko else " · unit unconfirmed")))
    if basis == "historical_log_loss":
        context += " · 과거 일간 로그손실" if ko else " · historical daily log loss"
    else:
        context += " · 계산 기준 미확인" if ko else " · calculation basis unconfirmed"
    return MetricHelp(label, _text("term_" + kind, language) + "\n" + context)
