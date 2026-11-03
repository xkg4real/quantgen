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
    """User-facing engine overview; calculation details stay in the implementation."""
    language = str(getattr(locale, "language", getattr(locale, "locale", locale))).lower()
    if language.startswith("ko"):
        return (
            "Q-SCORE · 여러 신호를, 하나의 별점으로.\n\n"
            "QUANTGEN의 기술신호·위험분석 엔진이 가격 추세, 모멘텀, 변동성과 하락 위험을 "
            "함께 살핍니다. 여러 관점의 분석을 하나의 별점으로 정리해, 종목마다 다른 가격 흐름을 "
            "같은 기준으로 비교할 수 있도록 돕습니다.\n\n"
            "별점 뒤에는 단계별 분석이 있습니다. 충분한 수정주가 이력과 데이터의 시각·가격 기준을 "
            "점검한 뒤, 단기·장기 흐름과 과거 큰 손실 구간을 분석합니다. "
            "자료가 부족하거나 오래되면 새 별점을 만들지 않습니다.\n\n"
            "살아 있는 시장에 맞춰 갱신됩니다. 실시간 목록에 연결하면 새 체결을 오늘의 "
            "잠정 가격에 반영해 점수를 다시 계산합니다. 별이 많을수록 현재 가격 흐름과 "
            "과거 위험을 함께 평가한 점수가 높다는 뜻입니다. 연결 상태와 점수 기준 시각도 확인하세요.\n\n"
            "Q-SCORE v0.1은 실험적 연구 지표이며 예측력은 검증되지 않았습니다. "
            "기업가치 평가나 매수·매도 추천, 수익 보장이 아니며, QUANTGEN의 모든 모델을 "
            "실행한 결과는 아닙니다. 다른 분석과 함께 종목을 살펴보는 출발점으로 활용하세요."
        )
    return (
        "Q-SCORE · Multiple signals. One research rating.\n\n"
        "QUANTGEN's technical-signal and risk-analysis engines examine price trends, momentum, "
        "volatility and downside risk together. Q-SCORE brings these perspectives into one star "
        "rating, helping you compare different stocks on a consistent basis.\n\n"
        "Each rating follows several stages of analysis. We check adjusted price history, "
        "timestamps and price consistency, then examine short- and long-term behavior and past "
        "large losses. Insufficient or stale data receives no new rating.\n\n"
        "It updates with the market. Connect the live watchlist to incorporate new trades into "
        "today's provisional price and recalculate the score. More stars mean a higher combined "
        "assessment of current price behavior and historical risk. Check the connection status "
        "and score timestamp too.\n\n"
        "Q-SCORE v0.1 is an experimental research indicator with unvalidated predictive power. "
        "It is not a fundamental valuation, a buy/sell recommendation or a guarantee of returns, "
        "and does not run every QUANTGEN model. Use it as a starting point alongside other analysis."
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
