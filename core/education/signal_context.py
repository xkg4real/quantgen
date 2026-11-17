"""Observed study changes and reading limits; no recommendations or inferred return statistics."""
import math

from .indicators import compute_study, study


def _value(values, line, index):
    if index < 0:
        return None
    seq = values.get(line, ())
    if index >= len(seq):
        return None
    value = float(seq[index])
    return value if math.isfinite(value) else None


def signal_note(key, bars, index=-1, *, language="ko", values=None):
    """Describe only this observation and its predecessor, never a later candle."""
    if bars is None or not len(bars):
        return ""
    key = study(key).key
    if key not in ("sma", "ema", "macd", "rsi", "bb"):
        return ""
    i = index + len(bars) if index < 0 else index
    if not 0 <= i < len(bars):
        return ""
    values = compute_study(key, bars) if values is None else values
    say = lambda ko, en: ko if str(language).startswith("ko") else en
    at = lambda line, offset=0: _value(values, line, i + offset)
    if key == "rsi":
        now, prev = at("RSI14"), at("RSI14", -1)
        if now is None:
            return ""
        if prev is not None and prev <= 30 < now < 70:
            return say("RSI가 과매도 구간을 벗어났어요. 매도 압력이 약해졌을 가능성이 있어요. 가격 저점도 높아지는지 살펴보세요. 추세 반전이 확정된 것은 아니에요.",
                       "RSI has left the oversold zone. Selling pressure may be easing. Check whether price lows are also rising; a trend reversal is not confirmed.")
        if prev is not None and prev >= 70 > now > 30:
            return say("RSI가 과매수 구간에서 내려왔어요. 상승 속도가 둔화했을 가능성이 있어요. 가격 추세도 함께 살펴보세요. 하락 전환이 확정된 것은 아니에요.",
                       "RSI has left the overbought zone. Upward momentum may be easing. Check the price trend too; a downward reversal is not confirmed.")
        if now <= 30:
            return say("과매도 상태가 이어질 수도 있어요. RSI와 가격 저점이 함께 높아지는지 살펴보세요. 낮은 수치만으로 반등을 판단하기는 어려워요.",
                       "Oversold conditions can persist. Watch whether RSI and price lows rise together. A low reading alone does not establish a rebound.")
        if now >= 70:
            return say("강한 추세에서는 과매수 상태가 이어지기도 해요. 가격과 거래량도 함께 살펴보세요. 높은 수치만으로 하락을 판단하기는 어려워요.",
                       "Strong trends can remain overbought. Check price and volume too. A high reading alone does not establish a decline.")
        return ""
    if key in ("sma", "ema", "macd"):
        if key == "sma":
            current, previous = at("SMA20"), at("SMA20", -1)
            if current is None or previous is None or i == 0:
                return ""
            current, previous = bars.close[i] - current, bars.close[i - 1] - previous
            noun = say("가격이 이동평균선을", "Price crossed its moving average")
        elif key == "ema":
            a, b, a0, b0 = at("EMA12"), at("EMA26"), at("EMA12", -1), at("EMA26", -1)
            if None in (a, b, a0, b0):
                return ""
            current, previous = a - b, a0 - b0
            noun = say("빠른 평균선이 느린 평균선을", "The fast average crossed the slow average")
        else:
            current, previous = at("HISTOGRAM"), at("HISTOGRAM", -1)
            if current is None or previous is None:
                return ""
            noun = say("MACD가 신호선을", "MACD crossed its signal line")
        if previous <= 0 < current or previous >= 0 > current:
            up = current > 0
            return say(f"{noun} {'위로' if up else '아래로'} 통과했어요. 가격 흐름과 거래량도 같은 변화를 보이는지 살펴보세요. 횡보 구간에서는 교차가 반복될 수 있어요.",
                       f"{noun} {'upward' if up else 'downward'}. Check whether price and volume support the change. Crossings can reverse repeatedly in sideways markets.")
        return ""
    if key == "bb":
        low, high = at("BB_LOWER"), at("BB_UPPER")
        low0, high0 = at("BB_LOWER", -1), at("BB_UPPER", -1)
        if low is None or high is None:
            return ""
        if i and low0 is not None and bars.close[i - 1] < low0 and low <= bars.close[i] <= high:
            return say("가격이 하단 밴드 안으로 돌아왔어요. 저점과 가격 추세도 함께 살펴보세요. 밴드가 움직인 영향일 수 있어 반등이 확정된 것은 아니에요.",
                       "Price returned inside the lower band. Check price lows and trend too. The band itself may have moved; a rebound is not confirmed.")
        if i and high0 is not None and bars.close[i - 1] > high0 and low <= bars.close[i] <= high:
            return say("가격이 상단 밴드 안으로 돌아왔어요. 상승 흐름이 이어지는지도 살펴보세요. 밴드 진입만으로 하락 전환을 판단하기는 어려워요.",
                       "Price returned inside the upper band. Check whether the upward trend persists. Re-entry alone does not establish a downward reversal.")
    return ""


def alignment_note(keys, bars, index=-1, *, language="ko", values=None):
    """A disagreement notice, not a vote, confidence score or trade recommendation."""
    if bars is None or not len(bars):
        return ""
    i = index + len(bars) if index < 0 else index
    if not 0 <= i < len(bars):
        return ""
    directions = []
    for key in dict.fromkeys(keys):
        if key not in ("sma", "ema", "macd", "rsi"):
            continue
        v = (values or {}).get(key)
        if v is None:
            # When a caller supplies values, absent studies stay absent.
            if values is not None:
                continue
            v = compute_study(key, bars)
        at = lambda line: _value(v, line, i)
        if key == "sma":
            base = at("SMA20")
            delta = None if base is None else bars.close[i] - base
        elif key == "ema":
            fast, slow = at("EMA12"), at("EMA26")
            delta = None if fast is None or slow is None else fast - slow
        elif key == "macd":
            delta = at("HISTOGRAM")
        else:
            rsi = at("RSI14")
            delta = None if rsi is None else rsi - 50
        if delta is not None and delta != 0:
            directions.append(1 if delta > 0 else -1)
    if 1 in directions and -1 in directions:
        return ("선택한 추세·모멘텀 지표의 방향이 엇갈려요. 보는 기간과 반응 속도가 달라 생길 수 있는 차이예요. 한쪽 신호만으로 다음 방향을 단정하기는 어려워요."
                if str(language).startswith("ko") else
                "The selected trend and momentum readings disagree. Their lookback periods and response speeds differ. One reading alone does not settle the next direction.")
    return ""
