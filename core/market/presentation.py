"""One OHLCV/indicator renderer for Qt SVG and Flet images; no web services."""
from __future__ import annotations

from html import escape
import math
from statistics import fmean, pstdev

from .models import MarketSnapshot


def _sma(values, period):
    return [None if i + 1 < period else fmean(values[i + 1 - period:i + 1]) for i in range(len(values))]


def _ema(values, period):
    out = [None] * len(values)
    if len(values) < period:
        return out
    out[period - 1] = fmean(values[:period])
    alpha = 2 / (period + 1)
    for i in range(period, len(values)):
        out[i] = alpha * values[i] + (1 - alpha) * out[i - 1]
    return out


def indicator_series(snapshot: MarketSnapshot) -> dict[str, list]:
    values = [c.close for c in snapshot.candles]
    n = len(values)
    result = {"SMA20": _sma(values, 20), "RSI14": [None] * n,
              "MACD": [None] * n, "SIGNAL": [None] * n, "HISTOGRAM": [None] * n,
              "BB_UPPER": [None] * n, "BB_LOWER": [None] * n}
    if n > 14:
        changes = [b - a for a, b in zip(values, values[1:])]
        gain = fmean(max(0, d) for d in changes[:14])
        loss = fmean(max(0, -d) for d in changes[:14])
        for i in range(14, n):
            if i > 14:
                gain = (gain * 13 + max(0, changes[i - 1])) / 14
                loss = (loss * 13 + max(0, -changes[i - 1])) / 14
            result["RSI14"][i] = 50.0 if gain == loss == 0 else 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    fast, slow = _ema(values, 12), _ema(values, 26)
    macd = [None if a is None or b is None else a - b for a, b in zip(fast, slow)]
    result["MACD"] = macd
    if n >= 26:
        result["SIGNAL"] = [None] * 25 + _ema(macd[25:], 9)
        result["HISTOGRAM"] = [None if a is None or b is None else a - b for a, b in zip(macd, result["SIGNAL"])]
    for i in range(19, n):
        sd = pstdev(values[i - 19:i + 1])
        result["BB_UPPER"][i] = result["SMA20"][i] + 2 * sd
        result["BB_LOWER"][i] = result["SMA20"][i] - 2 * sd
    return result


def indicator_values(snapshot: MarketSnapshot) -> dict[str, float | None]:
    return {key: values[-1] if values else None for key, values in indicator_series(snapshot).items()}


def number(value) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    if value == 0:
        return "0"
    if abs(value) < .01 or abs(value) >= 1e12:
        return f"{value:.6g}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def readout(snapshot: MarketSnapshot, cursor: int | None = None) -> str:
    if not snapshot.candles:
        return "OHLCV —"
    c = snapshot.candles[-1 if cursor is None else max(0, min(len(snapshot.candles) - 1, cursor))]
    return (f"{snapshot.request.instrument.symbol} · {c.timestamp} · "
            f"O {number(c.open)}   H {number(c.high)}   L {number(c.low)}   "
            f"C {number(c.close)}   V {number(c.volume)}")


def plot_bounds(width: int = 1000) -> tuple[int, int]:
    return 18, max(420, int(width)) - 100


def chart_svg(snapshot: MarketSnapshot, *, indicators=("sma", "rsi", "macd"),
              cursor: int | None = None, width: int = 1000, dark: bool = False,
              visible: int | None = 120) -> str:
    """Indicators warm up on the full history; zoom only crops the viewport.

    Candle positions are observation based. Gaps do not fabricate candles.
    Trade timestamps retain the exchange's offset; daily bars are local dates.
    """
    width = max(420, min(2400, int(width)))
    fg, bg, grid = ("#E9EEE9", "#17211E", "#34443D") if dark else ("#20372E", "#FFFFFF", "#DCE4DF")
    up, down, blue, gold = "#D94A52", "#397AC4", "#2E9F91", "#C58C23"
    rsi_on, macd_on = "rsi" in indicators, "macd" in indicators
    height = 410 + 112 * (rsi_on + macd_on)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<title>QUANTGEN OHLCV · SMA20 · RSI14 · MACD12/26/9</title>',
             f'<rect width="{width}" height="{height}" fill="{bg}"/>']

    def text(x, y, value, *, color=fg, size=11, anchor="start"):
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-family="sans-serif" font-size="{size}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def line(x1, y1, x2, y2, color=grid, dash=""):
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="1"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')

    def rect(x, y, w, h, color):
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(.5,w):.2f}" height="{max(1,h):.2f}" fill="{color}"/>')

    text(18, 21, f"{snapshot.request.instrument.symbol} · {snapshot.request.interval} · {snapshot.source}", size=13)
    if not snapshot.candles:
        text(18, 70, "OHLCV —")
        return "".join(parts) + "</svg>"
    series = indicator_series(snapshot)
    total = len(snapshot.candles)
    start = max(0, total - max(10, int(visible))) if visible is not None else 0
    bars = snapshot.candles[start:]
    left, right = plot_bounds(width)
    step = (right - left) / len(bars)
    x = lambda j: left + (j + .5) * step
    selected = total - 1 if cursor is None else max(start, min(total - 1, int(cursor)))
    # A compact readout lives outside SVG in both clients; this label never clips.
    text(18, 42, snapshot.candles[selected].timestamp, size=10)
    legend = []
    if "sma" in indicators:
        legend.append(("SMA20", gold))
    if "bollinger" in indicators:
        legend += [("BB20 +2σ", blue), ("BB20 −2σ", blue)]
    for i, (name, color) in enumerate(legend):
        text(18 + i * 110, 60, name, color=color, size=10)
    lo, hi = min(c.low for c in bars), max(c.high for c in bars)
    if "bollinger" in indicators:
        bounds = [v for key in ("BB_UPPER", "BB_LOWER") for v in series[key][start:] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    if "sma" in indicators:
        bounds = [v for v in series["SMA20"][start:] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    pad = (hi - lo) * .06 or max(abs(hi) * .01, .01)
    lo, hi = lo - pad, hi + pad

    def panel(top, bottom, minimum, maximum, *, percent=False):
        if maximum == minimum:
            maximum += 1
        sy = lambda value: bottom - (value - minimum) / (maximum - minimum) * (bottom - top)
        for k in range(4):
            value = minimum + (maximum - minimum) * k / 3
            yy = sy(value)
            line(left, yy, right, yy)
            text(right + 7, yy + 4, f"{value:.0f}" if percent else number(value), size=10)
        return sy

    def curve(key, sy, color):
        segments, current = [], []
        for j, value in enumerate(series[key][start:]):
            if value is None:
                if current:
                    segments.append(current)
                    current = []
            else:
                current.append(f"{x(j):.2f},{sy(value):.2f}")
        if current:
            segments.append(current)
        for segment in segments:
            parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{color}" stroke-width="1.5"/>')

    price_y = panel(74, 278, lo, hi)
    for j, c in enumerate(bars):
        color = up if c.close >= c.open else down
        line(x(j), price_y(c.high), x(j), price_y(c.low), color)
        rect(x(j) - step * .3, min(price_y(c.open), price_y(c.close)), step * .6,
             abs(price_y(c.open) - price_y(c.close)), color)
    if "sma" in indicators:
        curve("SMA20", price_y, gold)
    if "bollinger" in indicators:
        curve("BB_UPPER", price_y, blue)
        curve("BB_LOWER", price_y, blue)
    # Unknown volume stays absent instead of becoming an invented zero.
    volumes = [c.volume for c in bars if c.volume is not None]
    text(left, 303, "Volume" if volumes else "Volume —", size=10)
    maxvol = max(volumes, default=0) or 1
    for j, c in enumerate(bars):
        if c.volume is not None and c.volume > 0:
            h = c.volume / maxvol * 48
            rect(x(j) - step * .3, 359 - h, step * .6, h, up if c.close >= c.open else down)
    line(left, 359, right, 359)
    text(right + 7, 317, number(max(volumes)) if volumes else "—", size=10)
    # Sparse x ticks leave room at mobile widths and for exchange-local times.
    count = min(len(bars), max(2, (right - left) // 150))
    for k in range(count):
        j = round(k * (len(bars) - 1) / max(1, count - 1))
        stamp = bars[j].timestamp
        label = stamp[5:10] + (" " + stamp[11:16] if len(stamp) > 10 else "")
        text(x(j), 379, label, anchor="middle", size=9)
    top = 398
    if rsi_on:
        text(left, top, "RSI14 · Wilder", size=10)
        sy = panel(top + 12, top + 88, 0, 100, percent=True)
        for boundary in (30, 70):
            line(left, sy(boundary), right, sy(boundary), gold, "3 4")
        curve("RSI14", sy, blue)
        top += 112
    if macd_on:
        text(left, top, "MACD12/26 · Signal9", size=10)
        values = [v for key in ("MACD", "SIGNAL", "HISTOGRAM") for v in series[key][start:] if v is not None]
        extent = max((abs(v) for v in values), default=1) * 1.1 or 1
        sy = panel(top + 12, top + 88, -extent, extent)
        line(left, sy(0), right, sy(0), fg)
        for j, value in enumerate(series["HISTOGRAM"][start:]):
            if value is not None and abs(value) > 1e-12:
                rect(x(j) - step * .3, min(sy(0), sy(value)), step * .6, abs(sy(value) - sy(0)), up if value >= 0 else down)
        curve("MACD", sy, blue)
        curve("SIGNAL", sy, gold)
    line(x(selected - start), 73, x(selected - start), height - 12, fg, "3 4")
    text(width - 10, height - 3, "OHLCV · exchange time · latest bar may be open", anchor="end", size=9)
    return "".join(parts) + "</svg>"
