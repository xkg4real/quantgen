"""Pure model of the native stock detail view (owner request 2026-11-11, UI-D8).

Owner: "검색해서 한 차트를 구체적으로 볼때에는, 해당 차트로 화면을 거의 가득채워도 가능해" and "스크롤로
차트좌우이동이 가능한데, 이거 그냥 막아버리고 pc기준 좌우화살표로 차트 좌우 확인할수있게 변경해줘". This module holds
what the view decides without Qt: the period chips (interval, bars requested and bars shown), the pan window,
which intervals the chart routers can deliver, an honest market-state code for the quote, the volume against its
30-session average and the four "지금 이 차트" readings. Display text lives in
quantgen_desktop/owner_ui_language/stock.py; here are only codes and numbers. No I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math

DAILY = ("1d", "1w", "1M")
# key: (interval, bars requested). Daily periods share one 1d x 400 request, so switching among them never
# reloads; 400 = 252 sessions shown for 1Y plus the warm-up of a 120-bar average (Ichimoku needs 78).
PERIODS = (
    ("1D", "1m", 400),
    ("5D", "15m", 140),
    ("1M", "1d", 400),
    ("3M", "1d", 400),
    ("6M", "1d", 400),
    ("YTD", "1d", 400),
    ("1Y", "1d", 400),
    ("5Y", "1w", 400),
    ("ALL", "1M", 500),
)
PERIOD_KEYS = tuple(key for key, _, _ in PERIODS)
DEFAULT_PERIOD = "6M"
_SHOWN = {"1M": 22, "3M": 63, "6M": 126, "1Y": 252, "5Y": 261}
MIN_VISIBLE = 20
BOND_BARS = 100          # KIS bond history is at most 100 daily bars
VOLUME_SESSIONS = 30
VOLUME_MIN_SESSIONS = 10
LIVE_TRADE_SECONDS = 60


def period_request(key, instrument):
    """(interval, bars requested) of a period chip for an instrument; ValueError for an unknown key."""
    for name, interval, limit in PERIODS:
        if name == key:
            if getattr(instrument, "asset", "") == "bond":
                return "1d", BOND_BARS
            return interval, limit
    raise ValueError(f"Unknown period {key!r}")


def visible_for(key, candles):
    """How many of the loaded bars a period shows (at least MIN_VISIBLE, at most what was received)."""
    candles = tuple(candles or ())
    n = len(candles)
    if not n:
        return MIN_VISIBLE
    if key in _SHOWN:
        shown = _SHOWN[key]
    elif key == "1D":
        last = str(candles[-1].timestamp)[:10]
        shown = sum(1 for c in candles if str(c.timestamp)[:10] == last)
    elif key == "5D":
        days = []
        for c in reversed(candles):
            day = str(c.timestamp)[:10]
            if day not in days:
                if len(days) == 5:
                    break
                days.append(day)
        shown = sum(1 for c in candles if str(c.timestamp)[:10] in days)
    elif key == "YTD":
        year = str(candles[-1].timestamp)[:4]
        shown = sum(1 for c in candles if str(c.timestamp)[:4] == year)
    else:  # ALL
        shown = n
    return max(min(MIN_VISIBLE, n), min(n, shown))


def window(n, visible, end=None):
    """(start, stop) of the bars drawn: `visible` bars ending at index `end` (None = the latest bar)."""
    n = max(0, int(n))
    if not n:
        return 0, 0
    visible = max(1, min(n, int(visible)))
    stop = n if end is None else max(1, min(n, int(end) + 1))
    stop = max(stop, visible)
    return stop - visible, stop


def routable_intervals(router, instrument, *, paper=False, supported=None):
    """Intervals the chart router can deliver for this instrument, in the pane's order.

    The KIS list (`data.kis_workspace.supported_intervals`) when the primary provider is ready; otherwise only
    what a ready fallback supports (Yahoo: 1d, 1w and 1M for stocks with a verified ticker).
    """
    if supported is None:
        from data.kis_workspace import supported_intervals
        supported = supported_intervals(instrument, paper=paper)
    supported = tuple(supported)
    primary = getattr(router, "primary", None)
    try:
        ready = bool(primary.ready()[0]) if primary is not None else True
    except Exception:
        ready = False
    if ready:
        return supported
    from core.market.models import ChartRequest
    out = []
    for interval in supported:
        try:
            request = ChartRequest(instrument, interval, 100)
        except ValueError:
            continue
        for provider in getattr(router, "fallbacks", ()):
            try:
                if provider.supports(request) and provider.ready()[0]:
                    out.append(interval)
                    break
            except Exception:
                continue
    return tuple(out)


def period_reason(key, instrument, intervals):
    """'' when the period chip can be used, else a reason code: 'bond_daily', 'needs_kis'."""
    interval, _ = period_request(key, instrument)
    if getattr(instrument, "asset", "") == "bond" and key not in ("1M", "3M", "6M", "YTD", "1Y"):
        return "bond_daily"
    if interval not in tuple(intervals):
        return "needs_kis"
    return ""


# Market state ---------------------------------------------------------------------------------
@dataclass(frozen=True)
class QuoteState:
    code: str            # live, live_quiet, us_free, delayed15, fallback, polling, snapshot, closed, holiday,
                         # stale, error, loading, idle
    tone: str            # success, muted, warning, error
    age: int | None = None       # seconds since the last trade (live codes)
    market_time: str = ""        # the quote's market time, as given
    venue: str = ""              # KRX, US or ''


STATE_TONES = {"live": "success", "live_quiet": "muted", "us_free": "warning", "delayed15": "warning",
               "fallback": "warning", "polling": "muted", "snapshot": "muted", "closed": "muted",
               "holiday": "muted", "stale": "error", "error": "error", "loading": "muted", "idle": "muted"}
US_EXCHANGES = ("NAS", "NYS", "AMS")


def venue_of(instrument):
    asset = getattr(instrument, "asset", "")
    if asset in ("domestic_stock", "domestic_future", "bond"):
        return "KRX"
    if asset == "overseas_stock" and getattr(instrument, "exchange", "") in US_EXCHANGES:
        return "US"
    return ""


def _age(stamp, now):
    if not stamp:
        return None
    try:
        at = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if at.tzinfo is None:
        return None
    return max(0, int(round((now - at).total_seconds())))


def quote_state(instrument, *, source="", mode="idle", has_data=False, last_trade_at="", market_time="",
                now=None, venue_state=None):
    """An honest market-state code for the open chart; never "live" for delayed, fallback or closed data.

    `mode` is the chart pane's feed mode (idle, loading, snapshot, polling, connecting, subscribed, streaming,
    stale, error, stopped). `venue_state(code, moment)` defaults to core.markets.trading_state.
    """
    now = now or datetime.now(timezone.utc)
    venue = venue_of(instrument)
    if not has_data:
        code = {"loading": "loading", "error": "error", "stale": "error"}.get(mode, "idle")
        return QuoteState(code, STATE_TONES[code], venue=venue)
    if mode == "error":
        return QuoteState("error", "error", venue=venue)
    if mode == "stale":
        return QuoteState("stale", "error", venue=venue)
    kis = str(source or "").upper().startswith("KIS")
    if not kis:
        return QuoteState("fallback", "warning", market_time=market_time, venue=venue)
    state, why = "unknown", ""
    if venue:
        if venue_state is None:
            from core.markets import trading_state as venue_state
        try:
            state, why = venue_state(venue, now)
        except Exception:
            state, why = "unknown", ""
    if state == "closed":
        code = "holiday" if "holiday" in str(why) else "closed"
        return QuoteState(code, "muted", market_time=market_time, venue=venue)
    asset = getattr(instrument, "asset", "")
    if asset == "overseas_stock":
        code = "us_free" if venue == "US" else "delayed15"
        return QuoteState(code, "warning", market_time=market_time, venue=venue)
    age = _age(last_trade_at, now)
    if mode == "streaming":
        code = "live" if age is not None and age <= LIVE_TRADE_SECONDS else "live_quiet"
        return QuoteState(code, STATE_TONES[code], age=age, market_time=market_time, venue=venue)
    if mode in ("connecting", "subscribed"):
        return QuoteState("live_quiet", "muted", age=age, market_time=market_time, venue=venue)
    if mode == "polling":
        return QuoteState("polling", "muted", market_time=market_time, venue=venue)
    if mode == "loading":
        return QuoteState("loading", "muted", market_time=market_time, venue=venue)
    return QuoteState("snapshot", "muted", market_time=market_time, venue=venue)


# Volume against its average --------------------------------------------------------------------
@dataclass(frozen=True)
class VolumeRatio:
    volume: float | None
    average: float | None
    ratio: float | None
    sessions: int            # sessions in the average (before today)
    today_included: bool     # the volume is today's (possibly intraday cumulative)


def volume_vs_average(candles, today_volume=None, *, today=None, sessions=VOLUME_SESSIONS):
    """Today's volume against the average of the `sessions` daily bars before today (never today's own bar).

    `candles` are daily bars, ascending. `today` is an ISO date (default: the last bar's date). The volume is
    `today_volume` when given, else the bar dated `today`, else None. Fewer than VOLUME_MIN_SESSIONS bars give
    no average.
    """
    rows = [c for c in (candles or ()) if getattr(c, "volume", None) is not None and math.isfinite(float(c.volume))]
    if not rows:
        return VolumeRatio(today_volume, None, None, 0, today_volume is not None)
    day = str(today or rows[-1].timestamp)[:10]
    before = [c for c in rows if str(c.timestamp)[:10] < day][-sessions:]
    own = next((c for c in reversed(rows) if str(c.timestamp)[:10] == day), None)
    volume = today_volume if today_volume is not None else (float(own.volume) if own is not None else None)
    if len(before) < VOLUME_MIN_SESSIONS:
        return VolumeRatio(volume, None, None, len(before), own is not None or today_volume is not None)
    average = sum(float(c.volume) for c in before) / len(before)
    ratio = volume / average if volume is not None and average > 0 else None
    return VolumeRatio(volume, average, ratio, len(before), own is not None or today_volume is not None)


# "지금 이 차트": four plain readings at the latest bar --------------------------------------------
@dataclass(frozen=True)
class SummaryRow:
    topic: str               # trend, strength, movement, trading
    code: str                # the reading's case (see now_summary)
    values: dict             # numbers the text template fills
    study: str = ""          # the registry study a click turns on


def _percentile(values, value):
    values = [v for v in values if math.isfinite(v)]
    if not values:
        return None
    return sum(1 for v in values if v <= value) / len(values)


def now_summary(bars, *, volume=None):
    """(trend, strength, movement, trading) SummaryRows for core.education.indicators.Bars at the last bar.

    trend: close against SMA20 and SMA60 (above_both, below_both, mixed_up, mixed_down, short; 'wait' when
    there are fewer than 20 bars). strength: RSI14 by the same rule as the RSI panel's reading
    (core.education.study_guide): 'high' at 70 or more and 'low' at 30 or less as displayed; in between
    'even' when rises and falls were about the same size, else 'upper' / 'lower' (rises / falls larger) with
    '_more' or '_much' as the engine's ratio grows (its 'slightly', 'plainly' and 'much'); 'wait' without RSI. movement: ATR14 as % of the close and its place among the last 120 values (small < 20th percentile,
    large > 80th, usual; wait). trading: `volume` (VolumeRatio) ratio (low < 0.7, usual, high > 1.3; short when
    the average needs more sessions; none without volume).
    """
    from core.education.indicators import compute_study
    from core.education.study_guide import _degree, _ratio, _shown
    n = len(bars)
    close = bars.close[-1] if n else math.nan
    rows = []
    sma20 = compute_study("sma", bars)["SMA20"][-1] if n else math.nan
    sma60 = compute_study("sma", bars, period=60)["SMA20"][-1] if n else math.nan
    if not math.isfinite(sma20):
        rows.append(SummaryRow("trend", "wait", {"needed": 20, "have": n}, "sma"))
    elif not math.isfinite(sma60):
        rows.append(SummaryRow("trend", "short", {"pct20": (close / sma20 - 1) * 100}, "sma"))
    else:
        d20, d60 = (close / sma20 - 1) * 100, (close / sma60 - 1) * 100
        code = ("above_both" if d20 >= 0 and d60 >= 0 else "below_both" if d20 < 0 and d60 < 0
                else "mixed_up" if d20 >= 0 else "mixed_down")
        rows.append(SummaryRow("trend", code, {"pct20": d20, "pct60": d60}, "sma"))
    rsi = compute_study("rsi", bars)["RSI14"][-1] if n else math.nan
    if not math.isfinite(rsi):
        rows.append(SummaryRow("strength", "wait", {"needed": 15, "have": n}, "rsi"))
    else:
        # One rule with the RSI panel's reading, so the card and the panel never say 'slightly' and 'much' of
        # the same number: the band follows the displayed value, the words the ratio of rises to falls.
        shown = _shown(rsi)
        ratio, ratio_text = _ratio(rsi)
        degree = 3 if not ratio_text else _degree(ratio)
        if shown >= 70:
            code = "high"
        elif shown <= 30:
            code = "low"
        elif degree == 0:
            code = "even"
        else:
            code = ("upper" if rsi >= 50 else "lower") + ("", "", "_more", "_much")[degree]
        rows.append(SummaryRow("strength", code, {"rsi": shown, "ratio": ratio if ratio_text else math.inf},
                               "rsi"))
    atr = compute_study("atr", bars)["ATR"] if n else ()
    last = atr[-1] if n else math.nan
    if not (n and math.isfinite(last) and close):
        rows.append(SummaryRow("movement", "wait", {"needed": 15, "have": n}, "atr"))
    else:
        closes = bars.close
        pcts = [a / c * 100 for a, c in zip(atr[-120:], closes[-120:]) if math.isfinite(a) and c]
        pct = last / close * 100
        rank = _percentile(pcts, pct)
        code = "small" if rank is not None and rank < 0.2 else "large" if rank is not None and rank > 0.8 else "usual"
        rows.append(SummaryRow("movement", code, {"pct": pct, "atr": last, "bars": len(pcts)}, "atr"))
    if volume is None or volume.volume is None:
        rows.append(SummaryRow("trading", "none", {}, "volume_ma"))
    elif volume.ratio is None:
        rows.append(SummaryRow("trading", "short", {"sessions": volume.sessions, "needed": VOLUME_MIN_SESSIONS},
                               "volume_ma"))
    else:
        code = "low" if volume.ratio < 0.7 else "high" if volume.ratio > 1.3 else "usual"
        rows.append(SummaryRow("trading", code, {"ratio": volume.ratio, "volume": volume.volume,
                                                 "average": volume.average, "sessions": volume.sessions},
                               "volume_ma"))
    return tuple(rows)


# One-word state of a study for the picker's value column (spec 5.1: "71,800 · 선 위", "64.2 · 보통") ---------
# key: (line, high level, low level); at or above high is 'high', at or below low is 'low', else 'middle'.
_LEVELS = {"rsi": ("RSI14", 70, 30), "stoch": ("STOCH_K", 80, 20), "stochrsi": ("STOCHRSI_K", 80, 20),
           "mfi": ("MFI", 80, 20), "cci": ("CCI", 100, -100), "williams": ("WILLR", -20, -80),
           "disparity": ("DISPARITY", 105, 95), "psychology": ("PSY", 75, 25)}
_BANDS = {"bb": ("BB_UPPER", "BB_LOWER"), "envelope": ("ENV_UPPER", "ENV_LOWER"),
          "keltner": ("KC_UPPER", "KC_LOWER"), "donchian": ("DC_UPPER", "DC_LOWER")}
STATE_CODES = ("high", "middle", "low", "above", "below", "fast_above", "fast_below", "signal_above",
               "signal_below", "cloud_above", "cloud_in", "cloud_below", "dots_below", "dots_above", "band_above",
               "band_in", "band_below", "trend_clear", "trend_weak", "volume_more", "volume_usual", "volume_less")


def _value(values, line, index):
    try:
        value = float(values[line][index])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def study_state(key, values, bars, index=-1):
    """A one-word state code (STATE_CODES) of `key` at bar `index`, or '' when the study has none (ATR, OBV,
    band width, flows, …) or a value is missing. `values` is core.education.indicators.compute_study output."""
    try:
        close = float(bars.close[index])
    except (AttributeError, IndexError, TypeError, ValueError):
        return ""
    if not math.isfinite(close):
        return ""
    if key in _LEVELS:
        line, high, low = _LEVELS[key]
        value = _value(values, line, index)
        if value is None:
            return ""
        value = float(f"{value:.1f}")   # as displayed, like the panel's reading
        return "high" if value >= high else "low" if value <= low else "middle"
    if key in ("sma", "vwap"):
        value = _value(values, "SMA20" if key == "sma" else "VWAP", index)
        return "" if value is None or value == close else "above" if close > value else "below"
    if key == "ema":
        fast, slow = _value(values, "EMA12", index), _value(values, "EMA26", index)
        return "" if None in (fast, slow) or fast == slow else "fast_above" if fast > slow else "fast_below"
    if key == "macd":
        histogram = _value(values, "HISTOGRAM", index)
        return "" if not histogram else "signal_above" if histogram > 0 else "signal_below"
    if key == "ichimoku":
        a, b = _value(values, "SPAN_A", index), _value(values, "SPAN_B", index)
        if None in (a, b):
            return ""
        return "cloud_above" if close > max(a, b) else "cloud_below" if close < min(a, b) else "cloud_in"
    if key == "psar":
        sar = _value(values, "SAR", index)
        return "" if sar is None else "dots_below" if sar < close else "dots_above"
    if key == "adx":
        adx = _value(values, "ADX", index)
        return "" if adx is None else "trend_clear" if adx >= 20 else "trend_weak"
    if key == "percent_b":
        position = _value(values, "PERCENT_B", index)
        if position is None:
            return ""
        return "band_above" if position > 1 else "band_below" if position < 0 else "band_in"
    if key in _BANDS:
        upper, lower = (_value(values, line, index) for line in _BANDS[key])
        if None in (upper, lower):
            return ""
        return "band_above" if close > upper else "band_below" if close < lower else "band_in"
    if key == "volume_ma":
        average = _value(values, "VOLUME_MA", index)
        try:
            volume = float(bars.volume[index])
        except (IndexError, TypeError, ValueError):
            return ""
        if not average or not math.isfinite(volume):
            return ""
        ratio = volume / average
        return "volume_more" if ratio >= 1.3 else "volume_less" if ratio <= 0.7 else "volume_usual"
    return ""


__all__ = ["PERIODS", "PERIOD_KEYS", "DEFAULT_PERIOD", "period_request", "visible_for", "window",
           "routable_intervals", "period_reason", "QuoteState", "quote_state", "venue_of", "VolumeRatio",
           "volume_vs_average", "SummaryRow", "now_summary", "study_state", "STATE_CODES"]
