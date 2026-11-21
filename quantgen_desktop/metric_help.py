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


def mc_metadata(record=None, result=None):
    """Read display metadata only. Old saved records do not record confidence."""
    params = record.get('parameters') or {} if isinstance(record, dict) else {}
    return {'confidence': getattr(result, 'var_level', params.get('var_level')),
            'horizon_days': getattr(result, 'horizon_days', params.get('horizon_days'))}


def risk_help(kind, context, language, *, confidence=None, horizon_days=None,
              horizon_years=None, unit=None) -> MetricHelp:
    """Display an existing risk result; never infer a missing saved confidence.

    `hedge_signed_bp` is a lower-P&L-tail statistic, distinct from positive loss.
    Periods are trading sessions except `rates_pv_loss`, whose horizon is years.
    """
    kind = str(kind).lower()
    if kind not in ('var', 'cvar'):
        raise KeyError(kind)
    if context not in ('mc_terminal_loss', 'hedge_signed_bp', 'rates_pv_loss'):
        raise KeyError(context)
    if context == 'hedge_signed_bp' and kind != 'cvar':
        raise ValueError('The hedge result supplies signed CVaR only')
    ko = language == 'ko'
    valid = isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and math.isfinite(confidence) and 0 < confidence < 1
    level = f'{confidence * 100:g}%' if valid else ('미기록' if ko else 'not recorded')
    metric = 'CVaR' if kind == 'cvar' else 'VaR'
    meaning = ('나쁜 5% 때 평균손익' if ko else 'worst 5% average profit/loss') if context == 'hedge_signed_bp' else (
        ('큰 손실 평균' if ko else 'average large loss') if kind == 'cvar' else ('손실 경계' if ko else 'loss boundary'))
    label = metric + (f' {level}' if valid else '') + ' · ' + meaning
    if context == 'hedge_signed_bp':
        definition = ('CVaR — 손익(P&L)이 가장 낮은 약 5% 경로의 평균이에요. 음수는 손실이고 양수는 이익일 수 있어요. 최대 손실이나 양수 손실 한도가 아니에요.' if ko else
                      'CVaR — mean P&L of the lowest roughly 5% of paths. Negative is a loss; positive may be a gain. It is not maximum loss or a positive loss limit.')
        basis = ('기준 현물가격 대비 bp · 1 bp = 0.01% · 경로 수의 5%를 내림하되 최소 1개' if ko else
                 'bp of initial spot · 1 bp = 0.01% · floor(5% of paths), at least one path')
    else:
        definition = (('VaR — 표시된 기간·신뢰수준의 손실 경계예요. 더 큰 손실도 가능하며 최대 손실은 아니에요.' if ko else
                       'VaR — loss boundary at the displayed horizon and confidence. Larger losses remain possible; it is not maximum loss.') if kind == 'var' else
                      ('CVaR — VaR 이상 큰 손실들의 평균이에요. 최대 손실은 아니에요.' if ko else
                       'CVaR — mean loss at or beyond the VaR boundary, not maximum loss.'))
        if context == 'mc_terminal_loss':
            basis = ('시뮬레이션 만기 손실 = 1 − 만기 가격 / 시작 가격 · 시작 가격 대비 % · 음수 계산값은 0으로 표시' if ko else
                     'Simulated terminal loss = 1 − terminal / initial price · % of initial price · negative risk estimates display as zero')
        else:
            basis = ('PV 손실 = 현재 PV − 시점 PV · 명목금액과 같은 금액 단위(%, bp 아님; 통화 코드 미지정) · 음수 계산값은 0으로 표시' if ko else
                     "PV loss = today's PV − horizon PV · money in the notional's units (not %, not bp; currency unspecified) · negative risk estimates display as zero")
    if context == 'rates_pv_loss':
        valid_horizon = isinstance(horizon_years, (int, float)) and not isinstance(horizon_years, bool) and math.isfinite(horizon_years) and horizon_years > 0
        period = (f'{horizon_years:g}년' if ko else f'{horizon_years:g} years') if valid_horizon else ('기간 미기록' if ko else 'horizon not recorded')
    else:
        valid_horizon = isinstance(horizon_days, int) and not isinstance(horizon_days, bool) and horizon_days > 0
        period = (f'{horizon_days}거래일' if ko else f'{horizon_days} trading sessions') if valid_horizon else ('기간 미기록' if ko else 'horizon not recorded')
    metadata = (f'기간 {period} · 신뢰수준 {level}' if ko else f'Horizon {period} · confidence {level}')
    if unit:
        metadata += ' · ' + str(unit)
    return MetricHelp(label, definition + '\n' + metadata + '\n' + basis)


def risk_pair(kind, context, **metadata):
    """The page kit accepts (English, Korean) label and hover pairs."""
    en = risk_help(kind, context, 'en', **metadata)
    ko = risk_help(kind, context, 'ko', **metadata)
    return (en.label, ko.label), (en.hover, ko.hover)
