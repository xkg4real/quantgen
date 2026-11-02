"""Transparent, experimental Q-SCORE for the domestic-stock watchlist.

This is a new display composite, not an approved trading strategy, a valuation,
or an estimate of future profit. It reuses QUANTGEN's existing technical-signal
and historical-risk engines without invoking providers, orders, AI, fitting or
research ledgers. All thresholds are explicit product-methodology choices;
they have not been calibrated or validated as return predictors.

Ticks replace the current provisional daily close (or add one new session),
never add a daily observation per tick. Callers retain the adjusted daily
baseline and throttle recomputation. Raw live-chart candles are not modified.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
from numbers import Real
from typing import Mapping

import numpy as np

from core.market.models import MarketSnapshot
from core.quant.history import History
from core.quant.risk import analyze_history
from core.quant.signals import compute_signals


METHODOLOGY = "Q-SCORE v0.1"
MIN_SESSIONS = 200
MAX_SESSIONS = 252
MAX_HISTORY_AGE_DAYS = 7
MAX_QUOTE_AGE_SECONDS = 120
MAX_FUTURE_QUOTE_SECONDS = 5
_KST = timezone(timedelta(hours=9))
_SOURCES = {"KIS", "KIS REST"}


def q_score_help(locale="ko") -> str:
    """Same full methodology for the header tooltip and accessible dialog."""
    language = str(getattr(locale, "language", getattr(locale, "locale", locale))).lower()
    if language.startswith("ko"):
        return (
            "Q-SCORE v0.1 · 가격 흐름과 과거 위험을 요약하는 실험적 연구 별점입니다.\n\n"
            "QUANTGEN 기술신호 엔진 70%: 50·200일 이동평균, 63거래일 모멘텀, "
            "RSI(14), MACD(12/26/9), 단기·장기 변동성 비율을 함께 봅니다. "
            "기존 위험분석 엔진의 최대 낙폭 15%, 95% 과거 기대손실(CVaR) 15%를 더합니다.\n\n"
            "기술신호는 -100~100을 0~100으로 바꿉니다. 위험 점수는 최대 낙폭 0~40%, "
            "일간 CVaR 0~8%를 각각 100~0으로 환산하고 범위를 벗어나면 제한합니다. "
            "합계 20·40·60·80점부터 별이 하나씩 늘어납니다(1~5개). "
            "기술신호 내부 비중은 이동평균 50일 20%·200일 20%, 모멘텀 20%, "
            "RSI 15%, MACD 15%, 변동성 10%입니다.\n\n"
            "수정된 일별 가격이 최소 200개 필요하며 최근 252개까지 사용합니다. "
            "새 체결은 오늘의 잠정 종가에 반영해 다시 계산합니다. "
            "과거 자료가 7일 넘게 오래되었거나 체결이 120초 넘게 지연되면 새 별점을 산정하지 않습니다. "
            "거래 중단·연결 중단 여부와 데이터 시각도 함께 확인하세요.\n\n"
            "기업가치·재무제표를 평가하거나 모든 QUANTGEN 모델을 실행한 결과는 아닙니다. "
            "비중과 구간은 초기 설계값이며 예측력은 검증되지 않았습니다. "
            "별점은 매수·매도 추천이나 수익 보장이 아닙니다."
        )
    return (
        "Q-SCORE v0.1 · An experimental research rating of price behavior and historical risk.\n\n"
        "70% uses QUANTGEN's existing technical-signal engine: 50/200-session moving averages, "
        "63-session momentum, RSI(14), MACD(12/26/9), and short/long volatility ratio. "
        "The existing risk engine contributes 15% maximum drawdown and 15% historical 95% CVaR "
        "(average loss in the worst 5% of daily log returns).\n\n"
        "Technical signals are mapped from -100..100 to 0..100. Risk scores map drawdown "
        "of 0..40% and daily CVaR of 0..8% to 100..0, clipped at these limits. "
        "Stars increase at 20, 40, 60 and 80 points (1–5 stars). The technical engine weights "
        "SMA50 20%, SMA200 20%, momentum 20%, RSI 15%, MACD 15%, and volatility 10%.\n\n"
        "At least 200 adjusted daily observations are required; at most the latest 252 are used. "
        "New trades update today's provisional close before recalculation. History older than "
        "7 calendar days or trades delayed by more than 120 seconds receive no new rating. "
        "Check the data timestamp and connection/trading status too.\n\n"
        "This does not assess fundamentals or run every QUANTGEN model. Weights and thresholds "
        "are initial design choices with unvalidated predictive power. Stars are not a buy/sell "
        "recommendation or a guarantee of returns."
    )


def _instant(value) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)


def _day(value) -> date:
    if isinstance(value, datetime):
        return _instant(value).astimezone(_KST).date()
    if isinstance(value, date):
        return value
    text = str(value)
    if len(text) == 10:
        return date.fromisoformat(text)
    return _instant(text).astimezone(_KST).date()


def _positive(value) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError("Numeric price required")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError("Positive finite price required")
    return number


def _field(row, name):
    return row.get(name) if isinstance(row, Mapping) else getattr(row, name)


def _result(status, reason, *, now, symbol="", source="", **fields):
    result = {
        "status": status, "reason": reason, "score": None, "stars": None,
        "as_of": None, "computed_at": now.isoformat(), "methodology": METHODOLOGY,
        "symbol": symbol, "source": source, "live": False, "components": {},
        "sessions": 0, "price_basis": "adjusted_daily", "experimental": True,
    }
    result.update(fields)
    return result


def compute_q_score(history, latest_price=None, as_of=None, *, source=None,
                    adjusted=None, interval="1d", symbol="", now=None,
                    previous_as_of=None) -> dict:
    """Compute a bounded, JSON-safe score or an explicit non-score state.

    ``history`` may be a History, a daily adjusted MarketSnapshot, or a sequence
    of Candle / mapping rows with ``timestamp`` and ``close``. Bare sequences
    require explicit ``source='KIS'`` and ``adjusted=True``. Metadata on History
    and MarketSnapshot is authoritative and cannot be overridden by keywords.

    ``as_of`` is the timestamp of an actual latest-price observation, not its
    download time. Supplying latest_price requires an aware timestamp. Without
    a latest price the result describes the last daily observation, live=False.
    Pass previous_as_of to reject out-of-order updates; this function is pure.
    The caller must stop labelling an old retained result live after disconnect.
    """
    try:
        clock = _instant(now) if now is not None else datetime.now(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        # A broken clock cannot be used to claim current market data.
        return _result("unavailable", "invalid_clock", now=datetime.now(timezone.utc))

    def refuse(reason, *, status="unavailable", **fields):
        return _result(status, reason, now=clock, symbol=symbol, source=source or "", **fields)

    try:
        if isinstance(history, MarketSnapshot):
            symbol = history.request.instrument.symbol
            source = history.source
            adjusted = history.request.adjusted
            interval = history.request.interval
            if history.request.instrument.asset != "domestic_stock":
                return refuse("unsupported_instrument")
            rows = history.candles
            dates = [_day(row.timestamp) for row in rows]
            values = [_positive(row.close) for row in rows]
        elif isinstance(history, History):
            symbol = history.symbol
            source = history.source
            adjusted = history.adjustment in ("split", "total")
            if len(history.dates) != len(history.closes):
                return refuse("invalid_history")
            dates = [_day(d) for d in history.dates]
            values = [_positive(p) for p in history.closes]
        else:
            rows = tuple(history) if history is not None else ()
            dates = [_day(_field(row, "timestamp")) for row in rows]
            values = [_positive(_field(row, "close")) for row in rows]
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return refuse("invalid_history")

    if interval != "1d":
        return refuse("daily_history_required")
    if str(source or "").upper() not in _SOURCES:
        return refuse("unverified_source")
    if adjusted is not True:
        return refuse("adjusted_history_required")
    if len(values) < MIN_SESSIONS:
        return refuse("insufficient_history", status="insufficient_data", sessions=len(values))
    if any(b <= a or (b - a).days > 14 for a, b in zip(dates, dates[1:])):
        return refuse("invalid_history_dates")
    today = clock.astimezone(_KST).date()
    if dates[-1] > today:
        return refuse("future_history")
    if (today - dates[-1]).days > MAX_HISTORY_AGE_DAYS:
        return refuse("stale_history")

    dates, values = dates[-MAX_SESSIONS:], values[-MAX_SESSIONS:]
    tick_time = None
    if latest_price is not None:
        try:
            price = _positive(latest_price)
            tick_time = _instant(as_of)
            previous = _instant(previous_as_of) if previous_as_of is not None else None
        except (TypeError, ValueError, OverflowError):
            return refuse("invalid_quote")
        age = (clock - tick_time).total_seconds()
        if age < -MAX_FUTURE_QUOTE_SECONDS:
            return refuse("future_quote")
        if age > MAX_QUOTE_AGE_SECONDS:
            return refuse("stale_quote")
        tick_day = tick_time.astimezone(_KST).date()
        if (previous is not None and tick_time < previous) or tick_day < dates[-1]:
            return refuse("out_of_order_quote")
        # Conservative guard against mixing a split-adjusted scale with a raw
        # quote across a corporate action. Multi-session jumps can also trigger
        # this guard: refresh/review the history instead of inventing continuity.
        if not 0.65 <= price / values[-1] <= 1.35:
            return refuse("adjustment_mismatch")
        if tick_day == dates[-1]:
            values[-1] = price
        else:
            dates.append(tick_day)
            values.append(price)
            dates, values = dates[-MAX_SESSIONS:], values[-MAX_SESSIONS:]

    if max(values) == min(values):
        return refuse("flat_history", status="insufficient_data", sessions=len(values))
    series = History(symbol, str(source), tuple(d.isoformat() for d in dates), tuple(values),
                     adjustment="split", status="provisional_intraday" if tick_time else "")
    try:
        signals = compute_signals(series)
        risk = analyze_history(series)
        if not all(math.isfinite(v) for v in (signals.composite, risk.max_drawdown, risk.cvar_1d)):
            return refuse("invalid_engine_output")
        signal_score = float(np.clip((signals.composite + 100) / 2, 0, 100))
        drawdown_score = float(np.clip((1 - abs(risk.max_drawdown) / 0.40) * 100, 0, 100))
        tail_score = float(np.clip((1 - max(0, risk.cvar_1d) / 0.08) * 100, 0, 100))
        score = round(signal_score * 0.70 + drawdown_score * 0.15 + tail_score * 0.15, 2)
        stars = min(5, 1 + int(score // 20))
        components = {
            "technical": {"score": signal_score, "weight": 0.70, "raw": signals.composite,
                          "engine": "core.quant.signals.compute_signals", "signals": {
                              c.key: {"score": c.score, "weight": c.weight}
                              for c in signals.components}},
            "drawdown": {"score": drawdown_score, "weight": 0.15, "raw": risk.max_drawdown,
                         "engine": "core.quant.risk.analyze_history", "backend": risk.engine},
            "tail_loss": {"score": tail_score, "weight": 0.15, "raw": risk.cvar_1d,
                          "engine": "core.quant.risk.analyze_history", "backend": "local",
                          "confidence": 0.95},
        }
    except (ArithmeticError, AttributeError, TypeError, ValueError):
        return refuse("engine_unavailable")
    return _result(
        "ready", "", now=clock, symbol=symbol, source=str(source), score=score,
        stars=stars, as_of=tick_time.isoformat() if tick_time else dates[-1].isoformat(),
        live=tick_time is not None, sessions=len(series), components=components,
        price_basis="provisional_daily" if tick_time else "adjusted_daily",
        history_start=dates[0].isoformat(), history_end=dates[-1].isoformat(),
        last_price=values[-1],
    )
