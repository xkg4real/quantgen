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


@dataclass(frozen=True)
class ValuationReference:
    """Educational display bands, never a company-quality or trading score."""
    labels: tuple[str, str, str]
    position: float | None
    band_index: int | None
    reading: str
    hover: str


def valuation_reference(metric_id, value, language='ko') -> ValuationReference:
    """Place an already supplied multiple on explicitly illustrative bands.

    No peer benchmark, expected return or accounting input is inferred. The
    pointer clips at the display's right edge; the caller retains the raw value.
    """
    metric = str(metric_id).lower()
    if metric not in ('per', 'pbr'):
        raise KeyError(metric_id)
    ko = language == 'ko'
    numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
    try:
        shown = float(value) if numeric else math.nan
    except (OverflowError, TypeError, ValueError):
        shown = math.nan
    valid = math.isfinite(shown) and shown > 0
    if metric == 'per':
        low, high, cap = 10., 20., 40.
        labels = ('10 미만', '10–20', '20 초과') if ko else ('<10', '10–20', '>20')
        readings = (('10배 미만 · 이익이 줄어들 전망인지도 확인해요', '이익의 10–20배 구간', '20배 초과 · 성장 기대가 반영됐는지 확인해요') if ko else
                    ('Below 10 · also check whether earnings are expected to fall', '10–20 times earnings',
                     'Above 20 · check whether growth expectations explain it'))
        detail = ('PER 10 미만·10–20·20 초과는 이해를 돕는 참고 구간의 예시이며 업종 평균이나 적정가 기준이 아니에요. '
                  '낮은 PER는 저평가일 수도 있지만 이익 감소 예상이나 일시적인 고점 이익 때문일 수도 있어요. '
                  '0 이하·적자·특수한 회계 기준에서는 통상적인 PER 비교를 보류해요.' if ko else
                  'PER bands below 10, 10–20 and above 20 are illustrative references, not sector averages or fair-value targets. '
                  'A low PER may reflect undervaluation, expected earnings decline or temporarily high earnings. '
                  'Usual PER comparisons do not apply to nonpositive multiples, losses or incompatible accounting bases.')
    else:
        low, high, cap = 1., 3., 6.
        labels = ('1 미만', '1–3', '3 초과') if ko else ('<1', '1–3', '>3')
        readings = (('1배 미만 · 순자산보다 낮은 가격이에요. 수익성도 함께 봐요', '장부자본의 1–3배', '3배 초과 · ROE가 높은지 함께 확인해요') if ko else
                    ('Below 1 · priced under book equity; check profitability too', '1–3 times book equity',
                     'Above 3 · check whether ROE is high enough to explain it'))
        detail = ('PBR 1배는 가격과 주당 장부자본이 같은 지점이에요. 1 미만·1–3·3 초과는 교육용 참고 구간이지 '
                  '업종별 우량 기준이 아니에요. 1배 미만도 낮은 수익성·자산 부실·자본 감소 우려 때문일 수 있고, '
                  '높은 PBR도 높은 ROE와 지속적인 이익으로 설명되는지 확인해야 해요. 자본이 0 이하이면 비교를 보류해요.' if ko else
                  'PBR of 1 means price equals book equity per share. Below 1, 1–3 and above 3 are educational examples, '
                  'not sector-specific quality thresholds. Below-book prices can reflect weak profitability, impaired assets or '
                  'shrinking equity; higher multiples need support from returns on equity and durable earnings. '
                  'Do not use the usual comparison for nonpositive equity.')
    detail += ('\n같은 업종·기간·회계 기준에서 이익의 지속성, ROE와 부채를 함께 살펴요. 낮은 배수만으로 좋은 기업·매수 신호를 뜻하지 않아요. '
               '현재 공급자 값의 기준일·회계 기준은 확인되지 않았어요. 오른쪽 끝은 표시 위치만 제한하며 실제 숫자는 그대로예요.' if ko else
               '\nCompare the same industry, period and accounting basis, alongside earnings durability, ROE and debt. '
               'Low multiples alone do not identify a good company or a buy signal. The provider value’s reference date/accounting basis is unconfirmed. '
               'Only the pointer clips at the right edge; the supplied number stays unchanged.')
    if not valid:
        reading = ('값 미제공·0 이하는 비교 보류' if ko else 'Missing or nonpositive: comparison withheld')
        return ValuationReference(labels, None, None, reading, detail)
    band = 0 if shown < low else 1 if shown <= high else 2
    if shown < low:
        position = shown / low / 3
    elif shown <= high:
        position = (1 + (shown-low)/(high-low)) / 3
    else:
        position = min(1., (2 + (shown-high)/(cap-high)) / 3)
    return ValuationReference(labels, position, band, readings[band], detail)


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
