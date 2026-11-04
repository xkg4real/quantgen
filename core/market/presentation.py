"""One OHLCV/indicator renderer for Qt SVG and Flet images; no web services."""
from __future__ import annotations

from html import escape
import math
from statistics import fmean, pstdev

from .models import MarketSnapshot, LIVE_INTERVALS


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
    result = {"SMA20": _sma(values, 20), "EMA12": _ema(values, 12), "EMA26": _ema(values, 26), "RSI14": [None] * n,
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
    fast, slow = result["EMA12"], result["EMA26"]
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


def readout(snapshot: MarketSnapshot, cursor: int | None = None, *, language="en") -> str:
    if not snapshot.candles:
        return "OHLCV —"
    c = snapshot.candles[-1 if cursor is None else max(0, min(len(snapshot.candles) - 1, cursor))]
    labels = ("시작", "최고", "최저", "마지막", "거래량") if language == "ko" else ("O", "H", "L", "C", "V")
    values = (c.open, c.high, c.low, c.close, c.volume)
    sequence = getattr(c, "sequence", None)
    identity = f" · #{sequence}" if sequence is not None else ""
    return (f"{snapshot.request.instrument.symbol} · {c.timestamp}{identity} · "
            + "   ".join(f"{label} {number(value)}" for label, value in zip(labels, values)))


def indicator_colors(dark=False):
    """One color per indicator family across controls, help and chart lines."""
    return {"sma": "#C58C23" if dark else "#896000",
            "ema": "#91B8F3" if dark else "#345DA4",
            "bollinger": "#2E9F91" if dark else "#157367",
            "rsi": "#C4A0E2" if dark else "#81529E",
            "macd": "#F1B47B" if dark else "#9A5625"}


def _axis_number(value, span):
    """Round visual grid labels only; full observations remain in the readout."""
    if not math.isfinite(value):
        return "—"
    step = abs(span) / 3
    precision = max(0, min(8, 1 - math.floor(math.log10(step)))) if step > 0 else 2
    if abs(value) >= 1e12 or (value and abs(value) < 1e-5):
        return f"{value:.5g}"
    rounded = round(value, precision)
    if rounded == 0:
        rounded = 0
    text = f"{rounded:,.{precision}f}"
    return text.rstrip("0").rstrip(".") if precision else text


# QtSvg reads a comma list as one (missing) family, so SVG text names only the
# registered app family; Flet and browsers fall back to their default sans-serif.
SVG_FONT_FAMILY = "QG Interface"
# Hangul loses strokes below 12px; every chart label is drawn at 12px or larger.
SVG_MIN_TEXT = 12
MIN_CHART_WIDTH = 320  # the narrowest native chart; drawn 1:1 so labels never shrink


def plot_bounds(width: int = 1000) -> tuple[int, int]:
    return 18, max(MIN_CHART_WIDTH, int(width)) - 100


def chart_svg(snapshot: MarketSnapshot, *, indicators=("sma", "rsi", "macd"),
              cursor: int | None = None, width: int = 1000, dark: bool = False,
              visible: int | None = 120, language="en") -> str:
    """Indicators warm up on the full history; zoom only crops the viewport.

    Candle positions are observation based. Gaps do not fabricate candles.
    Trade timestamps retain the exchange's offset; daily bars are local dates.
    """
    width = max(MIN_CHART_WIDTH, min(2400, int(width)))
    fg, bg, grid = ("#E9EEE9", "#17211E", "#34443D") if dark else ("#20372E", "#FFFFFF", "#DCE4DF")
    up, down = "#D94A52", "#397AC4"
    # Indicator colors also label the legend: meet text contrast on each canvas.
    colors = indicator_colors(dark)
    blue, gold = colors["bollinger"], colors["sma"]
    rsi_on, macd_on = "rsi" in indicators, "macd" in indicators
    height = 410 + 112 * (rsi_on + macd_on)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<title>QUANTGEN OHLCV · ' + escape(' · '.join(indicators)) + '</title>',
             f'<rect width="{width}" height="{height}" fill="{bg}"/>']

    def text(x, y, value, *, color=fg, size=SVG_MIN_TEXT, anchor="start", weight=None):
        size = max(SVG_MIN_TEXT, size)
        bold = f' font-weight="{weight}"' if weight else ''
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-family="{SVG_FONT_FAMILY}" font-size="{size}"{bold} text-anchor="{anchor}">{escape(str(value))}</text>')

    def line(x1, y1, x2, y2, color=grid, dash=""):
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="1"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')

    def rect(x, y, w, h, color):
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(.5,w):.2f}" height="{max(1,h):.2f}" fill="{color}"/>')

    text(18, 21, f"{snapshot.request.instrument.symbol} · {snapshot.request.interval}", size=14, weight=600)
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
    text(18, 42, snapshot.candles[selected].timestamp)
    legend = []
    if "sma" in indicators:
        legend.append(("SMA20", gold))
    if "ema" in indicators:
        legend.append(("EMA12 / 26", colors["ema"]))
    if "bollinger" in indicators:
        legend += [("BB20 +2σ", blue), ("BB20 −2σ", blue)]
    # About 7px per 12px Latin glyph; the gap narrows on small charts so the legend stays one line.
    legend_width = sum(len(name) * 7 for name, _ in legend)
    gap = max(10, min(22, (width - 30 - legend_width) / max(1, len(legend) - 1))) if legend else 0
    legend_x = 18
    for name, color in legend:
        text(legend_x, 60, name, color=color)
        legend_x += len(name) * 7 + gap
    lo, hi = min(c.low for c in bars), max(c.high for c in bars)
    if "bollinger" in indicators:
        bounds = [v for key in ("BB_UPPER", "BB_LOWER") for v in series[key][start:] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    if "sma" in indicators:
        bounds = [v for v in series["SMA20"][start:] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    if "ema" in indicators:
        bounds = [v for key in ("EMA12", "EMA26") for v in series[key][start:] if v is not None]
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
            text(right + 7, yy + 4, f"{value:.0f}" if percent else _axis_number(value, maximum - minimum))
        return sy

    def curve(key, sy, color, *, dash=""):
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
            parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{color}" stroke-width="1.5"'
                         + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')

    price_y = panel(74, 278, lo, hi)
    for j, c in enumerate(bars):
        color = up if c.close >= c.open else down
        line(x(j), price_y(c.high), x(j), price_y(c.low), color)
        rect(x(j) - step * .3, min(price_y(c.open), price_y(c.close)), step * .6,
             abs(price_y(c.open) - price_y(c.close)), color)
    if "sma" in indicators:
        curve("SMA20", price_y, gold)
    if "ema" in indicators:
        curve("EMA12", price_y, colors["ema"])
        curve("EMA26", price_y, colors["ema"], dash="4 3")
    if "bollinger" in indicators:
        curve("BB_UPPER", price_y, blue)
        curve("BB_LOWER", price_y, blue)
    # Unknown volume stays absent instead of becoming an invented zero.
    volumes = [c.volume for c in bars if c.volume is not None]
    volume_label = "거래량" if language == "ko" else "Volume"
    text(left, 303, volume_label if volumes else volume_label + " —")
    maxvol = max(volumes, default=0) or 1
    for j, c in enumerate(bars):
        if c.volume is not None and c.volume > 0:
            h = c.volume / maxvol * 48
            rect(x(j) - step * .3, 359 - h, step * .6, h, up if c.close >= c.open else down)
    line(left, 359, right, 359)
    text(right + 7, 317, number(max(volumes)) if volumes else "—")
    # Sparse x ticks leave room at mobile widths and for exchange-local times.
    count = min(len(bars), max(2, (right - left) // 160))
    for k in range(count):
        j = round(k * (len(bars) - 1) / max(1, count - 1))
        stamp = bars[j].timestamp
        label = stamp[5:10] + (" " + stamp[11:19 if snapshot.request.interval in LIVE_INTERVALS else 16] if len(stamp) > 10 else "")
        half = len(label) * 3.3  # keep the edge ticks inside the canvas at 12px
        text(min(max(x(j), half + 2), width - half - 2), 379, label, anchor="middle")
    top = 398
    if rsi_on:
        text(left, top, "RSI14 · Wilder", color=colors["rsi"])
        sy = panel(top + 12, top + 88, 0, 100, percent=True)
        for boundary in (30, 70):
            line(left, sy(boundary), right, sy(boundary), gold, "3 4")
        curve("RSI14", sy, colors["rsi"])
        top += 112
    if macd_on:
        text(left, top, "MACD12/26 · Signal9", color=colors["macd"])
        values = [v for key in ("MACD", "SIGNAL", "HISTOGRAM") for v in series[key][start:] if v is not None]
        extent = max((abs(v) for v in values), default=1) * 1.1 or 1
        sy = panel(top + 12, top + 88, -extent, extent)
        line(left, sy(0), right, sy(0), fg)
        for j, value in enumerate(series["HISTOGRAM"][start:]):
            if value is not None and abs(value) > 1e-12:
                rect(x(j) - step * .3, min(sy(0), sy(value)), step * .6, abs(sy(value) - sy(0)), up if value >= 0 else down)
        curve("MACD", sy, colors["macd"])
        curve("SIGNAL", sy, colors["macd"], dash="4 3")
    line(x(selected - start), 73, x(selected - start), height - 12, fg, "3 4")
    text(width - 10, height - 3, "거래소 시간 · 마지막 봉은 갱신 중일 수 있어요" if language == "ko" else "Exchange time · latest candle may still be forming", anchor="end")
    return "".join(parts) + "</svg>"


def card_svg(dates, values, *, width: int = 360, height: int = 150, dark: bool = False,
             label: str = "", decimals: int = 2) -> str:
    """Compact line chart for the Markets indicator cards (owner UI-7).

    Close-only observations are drawn as a line in the guide's C-format style:
    light gridlines at the low, middle and high values with right-hand labels, the
    first and last dates underneath and a dot on the latest value. Nothing is
    inferred: no candles, smoothing or projected values.
    """
    width = max(220, min(1200, int(width)))
    height = max(110, min(400, int(height)))
    fg, bg, grid, muted = (("#E9EEE9", "#17211E", "#34443D", "#A7B8AC") if dark
                           else ("#20372E", "#FFFFFF", "#E4E8E3", "#646E68"))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<title>' + escape(label or "QUANTGEN market indicator") + '</title>',
             f'<rect width="{width}" height="{height}" fill="{bg}"/>']
    points = [(d, float(v)) for d, v in zip(dates, values) if v is not None and math.isfinite(float(v))]
    if len(points) < 2:
        parts.append(f'<text x="12" y="{height / 2:.0f}" fill="{muted}" font-family="{SVG_FONT_FAMILY}" '
                     f'font-size="{SVG_MIN_TEXT}">—</text>')
        return "".join(parts) + "</svg>"
    low, high = min(v for _, v in points), max(v for _, v in points)
    if high == low:  # a flat series sits mid-card between distinct gridlines
        pad = abs(high) * 0.005 or 0.5
        low, high = low - pad, high + pad
    span = high - low
    grid_values = (low, (low + high) / 2, high)
    grid_labels = [f"{value:,.{max(0, int(decimals))}f}" for value in grid_values]
    # Right-hand labels at 12px need about 6.4px per character.
    left, right, top, bottom = 6, width - max(58, int(max(map(len, grid_labels)) * 6.4) + 10), 10, height - 24
    x = lambda i: left + (right - left) * i / (len(points) - 1)
    y = lambda v: bottom - (bottom - top) * (v - low) / span

    def text(tx, ty, value, *, anchor="start", color=muted, size=SVG_MIN_TEXT):
        size = max(SVG_MIN_TEXT, size)
        parts.append(f'<text x="{tx:.1f}" y="{ty:.1f}" fill="{color}" font-family="{SVG_FONT_FAMILY}" '
                     f'font-size="{size}" text-anchor="{anchor}">{escape(str(value))}</text>')

    for value, grid_label in zip(grid_values, grid_labels):
        gy = y(value)
        parts.append(f'<line x1="{left}" y1="{gy:.2f}" x2="{right}" y2="{gy:.2f}" stroke="{grid}" stroke-width="1"/>')
        text(right + 6, gy + 4, grid_label)
    path = " ".join(("M" if i == 0 else "L") + f"{x(i):.2f},{y(v):.2f}" for i, (_, v) in enumerate(points))
    parts.append(f'<path d="{path}" fill="none" stroke="{fg}" stroke-width="1.6" stroke-linejoin="round"/>')
    last_x, last_y = x(len(points) - 1), y(points[-1][1])
    parts.append(f'<circle cx="{last_x:.2f}" cy="{last_y:.2f}" r="3" fill="{fg}"/>')
    text(left, height - 6, points[0][0])
    text(right, height - 6, points[-1][0], anchor="end")
    return "".join(parts) + "</svg>"
