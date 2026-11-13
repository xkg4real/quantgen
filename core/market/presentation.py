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


# Registry studies other than the five drawn by the original code below (owner request
# 2026-11-11). One (light, dark) pair per line; each meets 4.5:1 on its canvas because
# the colours also label the legend and the panel titles.
_BLUE, _CRIMSON, _GREEN = ("#2F5FD0", "#8FB0FF"), ("#B0302A", "#FF8F87"), ("#2E7D32", "#79C77D")
_MAGENTA, _CYAN, _ORANGE = ("#A3367A", "#EE8FCB"), ("#00718A", "#5FC6DE"), ("#A8520B", "#F3A15C")
_VIOLET, _OLIVE, _SLATE, _BROWN = ("#6A4BC4", "#B7A4F7"), ("#6B6A00", "#C6C45A"), ("#4E5D66", "#B3C0C8"), ("#8A5A2B", "#D9AE7E")
_REFERENCE = ("#5F6D66", "#9AAAA2")
STUDY_COLORS = {
    "ichimoku": {"TENKAN": _BLUE, "KIJUN": _CRIMSON, "SPAN_A": _GREEN, "SPAN_B": _ORANGE, "CHIKOU": _VIOLET},
    "psar": {"SAR": _MAGENTA},
    "adx": {"ADX": _SLATE, "PDI": _GREEN, "MDI": _CRIMSON},
    "envelope": {"ENV_UPPER": _OLIVE, "ENV_MIDDLE": _OLIVE, "ENV_LOWER": _OLIVE},
    "keltner": {"KC_UPPER": _CYAN, "KC_MIDDLE": _CYAN, "KC_LOWER": _CYAN},
    "donchian": {"DC_UPPER": _VIOLET, "DC_MIDDLE": _VIOLET, "DC_LOWER": _VIOLET},
    "stoch": {"STOCH_K": _BLUE, "STOCH_D": _ORANGE},
    "stochrsi": {"STOCHRSI_K": _BLUE, "STOCHRSI_D": _ORANGE},
    "cci": {"CCI": _CYAN},
    "williams": {"WILLR": _MAGENTA},
    "roc": {"ROC": _VIOLET},
    "disparity": {"DISPARITY": _OLIVE},
    "psychology": {"PSY": _BROWN},
    "atr": {"ATR": _ORANGE},
    "percent_b": {"PERCENT_B": _GREEN},
    "bandwidth": {"BANDWIDTH": _CYAN},
    "volume_ma": {"VOLUME_MA": _SLATE},
    "obv": {"OBV": _BLUE},
    "mfi": {"MFI": _MAGENTA},
    "vwap": {"VWAP": _BROWN},
    "investor_flow": {"FOREIGN": _BLUE, "INSTITUTION": _ORANGE, "INDIVIDUAL": _GREEN},
    "short_ratio": {"SHORT_RATIO": _CRIMSON},
}
# Keys the original renderer draws itself ('bb' is the registry name of 'bollinger').
_LEGACY = ("sma", "ema", "bollinger", "rsi", "macd")
_STUDY_PANEL = 112        # one lower study: title row, 76px plot, axis room
_STUDY_UNAVAILABLE = 30   # a study that cannot be drawn on this chart: one line saying why


def study_colors(key, dark=False) -> dict[str, str]:
    """{line id: colour} of a registry study on the light or dark chart canvas."""
    from core.education.indicators import study
    spec = study(key)
    if spec.key in STUDY_COLORS:
        return {line: pair[1 if dark else 0] for line, pair in STUDY_COLORS[spec.key].items()}
    legacy = indicator_colors(dark)[{"bb": "bollinger"}.get(spec.key, spec.key)]
    return {line.id: legacy for line in spec.lines}


def _text_width(value, size=SVG_MIN_TEXT) -> float:
    """Approximate drawn width: Hangul about one em, Latin and digits about 0.6 em."""
    return sum(size * (1.0 if ord(ch) >= 0x1100 else .3 if ch == " " else .6) for ch in str(value))


def chart_svg(snapshot: MarketSnapshot, *, indicators=("sma", "rsi", "macd"),
              cursor: int | None = None, width: int = 1000, dark: bool = False,
              visible: int | None = 120, language="en", end: int | None = None, supply=None,
              price_height: int | None = None) -> str:
    """Indicators warm up on the full history; zoom only crops the viewport.

    Candle positions are observation based. Gaps do not fabricate candles.
    Trade timestamps retain the exchange's offset; daily bars are local dates.

    `indicators` takes the five original keys ('sma', 'ema', 'bollinger' or 'bb',
    'rsi', 'macd') and any key of core.education.indicators.STUDIES: price
    overlays share the candle panel, 'volume_ma' the volume panel, and every other
    study gets its own panel below with its conventional reference lines.
    `end` is the index of the last bar shown (pan; default the latest bar). A panned
    chart is the chart of the history ending at `end`: nothing after it is drawn (the
    Ichimoku lagging span stops displacement - 1 bars before `end`).
    `supply` (indicators.Supply or {'flows': rows, 'shorts': rows} from
    KISMarkets.investor_daily / short_sale_daily) feeds the supply/demand studies.
    `price_height` makes the candle panel taller than its 204px default (a detail
    view filling the screen); everything below it moves down by the difference.
    """
    from core.education import indicators as engine
    from core.education.study_guide import availability_short, format_value
    width = max(MIN_CHART_WIDTH, min(2400, int(width)))
    fg, bg, grid = ("#E9EEE9", "#17211E", "#34443D") if dark else ("#20372E", "#FFFFFF", "#DCE4DF")
    up, down = "#D94A52", "#397AC4"
    # Indicator colors also label the legend: meet text contrast on each canvas.
    colors = indicator_colors(dark)
    blue, gold = colors["bollinger"], colors["sma"]
    indicators = tuple("bollinger" if key == "bb" else key for key in indicators)
    # Unknown keys are ignored, as the original renderer always did.
    requested = {key for key in indicators if key not in _LEGACY and key in engine.STUDY_BY_KEY}
    extra = tuple(spec for spec in engine.STUDIES if spec.key in requested)
    ko = language == "ko"
    if isinstance(supply, dict):
        supply = engine.supply_from_rows(supply.get("flows") or (), supply.get("shorts") or ())
    request = snapshot.request
    has_volume = any(c.volume is not None for c in snapshot.candles)
    reason = {spec.key: engine.availability(spec.key, asset=request.instrument.asset, interval=request.interval,
                                            supply=supply, has_volume=has_volume) for spec in extra}
    overlays = [spec for spec in extra if spec.panel == "price"]
    volume_studies = [spec for spec in extra if spec.panel == "volume"]
    lower = [spec for spec in extra if not spec.overlay]
    rsi_on, macd_on = "rsi" in indicators, "macd" in indicators
    # Overlay legends of the added studies wrap onto rows under the original legend.
    added_legend = []
    for spec in overlays:
        palette = study_colors(spec.key, dark)
        if reason[spec.key]:
            added_legend.append((f"{spec.label(language)} — {availability_short(reason[spec.key], language)}", fg))
        else:
            added_legend += [(line.name(language), palette[line.id]) for line in spec.lines]
    original_legend = any(key in indicators for key in ("sma", "ema", "bollinger"))
    legend_rows, legend_x = [], 18
    for name, color in added_legend:
        if not legend_rows or legend_x + _text_width(name) > width - 12:
            legend_rows.append([])
            legend_x = 18
        legend_rows[-1].append((legend_x, name, color))
        legend_x += _text_width(name) + 16
    dy = 18 * max(0, len(legend_rows) - (0 if original_legend else 1))
    grow = max(0, int(price_height) - 204) if price_height else 0
    below = dy + grow  # every row under the candle panel
    lower_height = sum(_STUDY_UNAVAILABLE if reason[spec.key] else _STUDY_PANEL for spec in lower)
    height = 410 + below + 112 * (rsi_on + macd_on) + lower_height
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
    stop = total if end is None else max(1, min(total, int(end) + 1))
    start = max(0, stop - max(10, int(visible))) if visible is not None else 0
    bars = snapshot.candles[start:stop]
    left, right = plot_bounds(width)
    step = (right - left) / len(bars)
    x = lambda j: left + (j + .5) * step
    selected = stop - 1 if cursor is None else max(start, min(stop - 1, int(cursor)))
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
    for row, items in enumerate(legend_rows):
        for item_x, name, color in items:
            text(item_x, 60 + 18 * (row + (1 if original_legend else 0)), name, color=color)
    values = {}
    if extra:
        candles = engine.bars_from_candles(snapshot.candles, request.interval)
        values = {spec.key: engine.compute_study(spec.key, candles, supply=supply)
                  for spec in extra if not reason[spec.key]}

    # The Ichimoku lagging span at bar j is the close `displacement - 1` bars later: past
    # the last bar shown (`end`) it would show prices from after it, so panning would
    # differ from a chart that ends there. It is left blank instead.
    lag = engine.study("ichimoku").defaults["displacement"] - 1

    def window(key, line_id):
        seq = [None if not math.isfinite(v) else float(v) for v in values[key][line_id][start:stop]]
        if key == "ichimoku" and line_id == "CHIKOU":
            seq = [None if start + j + lag >= stop else value for j, value in enumerate(seq)]
        return seq

    lo, hi = min(c.low for c in bars), max(c.high for c in bars)
    if "bollinger" in indicators:
        bounds = [v for key in ("BB_UPPER", "BB_LOWER") for v in series[key][start:stop] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    if "sma" in indicators:
        bounds = [v for v in series["SMA20"][start:stop] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    if "ema" in indicators:
        bounds = [v for key in ("EMA12", "EMA26") for v in series[key][start:stop] if v is not None]
        if bounds:
            lo, hi = min(lo, min(bounds)), max(hi, max(bounds))
    for spec in overlays:
        if spec.key in values:
            bounds = [v for line_spec in spec.lines for v in window(spec.key, line_spec.id) if v is not None]
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

    def polylines(seq, sy, color, *, dash=""):
        segments, current = [], []
        for j, value in enumerate(seq):
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

    def curve(key, sy, color, *, dash=""):
        polylines(series[key][start:stop], sy, color, dash=dash)

    def draw_study(spec, sy):
        palette = study_colors(spec.key, dark)
        if spec.key == "ichimoku":
            span_a, span_b = window("ichimoku", "SPAN_A"), window("ichimoku", "SPAN_B")
            for j in range(len(bars) - 1):
                a0, a1, b0, b1 = span_a[j], span_a[j + 1], span_b[j], span_b[j + 1]
                if None in (a0, a1, b0, b1):
                    continue
                fill = palette["SPAN_A"] if a0 + a1 >= b0 + b1 else palette["KIJUN"]
                parts.append(f'<polygon points="{x(j):.2f},{sy(a0):.2f} {x(j + 1):.2f},{sy(a1):.2f} '
                             f'{x(j + 1):.2f},{sy(b1):.2f} {x(j):.2f},{sy(b0):.2f}" fill="{fill}" fill-opacity="0.14"/>')
        for line_spec in spec.lines:
            seq = window(spec.key, line_spec.id)
            color = palette[line_spec.id]
            if line_spec.style == "dots":
                radius = max(1.4, min(2.6, step * .22))
                for j, value in enumerate(seq):
                    if value is not None:
                        parts.append(f'<circle cx="{x(j):.2f}" cy="{sy(value):.2f}" r="{radius:.2f}" fill="{color}"/>')
            else:
                polylines(seq, sy, color, dash="4 3" if line_spec.style == "dash" else "")

    def study_panel(spec, top):
        """One lower study: a title row with the values at the selected bar, the plot
        with its conventional reference lines and labelled axis. Returns the next top."""
        name = spec.name(language)
        numbers = "·".join(f"{value:g}" if isinstance(value, float) else str(value) for _, value in spec.params)
        title = f"{name} {numbers}".strip() if numbers else name
        if spec.key not in values:
            note = f"{title} — {availability_short(reason[spec.key], language)}"
            while _text_width(note) > width - left - 10 and len(note) > 4:
                note = note[:-2] + "…"
            text(left, top, note)
            return top + _STUDY_UNAVAILABLE
        palette = study_colors(spec.key, dark)
        data = values[spec.key]
        readings = [(f"{line_spec.name(language)} {format_value(line_spec.kind, data[line_spec.id][selected], language)}",
                     palette[line_spec.id]) for line_spec in spec.lines]
        # Title, then the values; a second row when one line would not fit.
        rows, cursor_x, row = [[(left, title, fg)]], left + _text_width(title) + 14, 0
        for label, color in readings:
            if cursor_x + _text_width(label) > right + 90:
                rows.append([])
                row += 1
                cursor_x = left
            rows[row].append((cursor_x, label, color))
            cursor_x += _text_width(label) + 12
        for index, items in enumerate(rows):
            for item_x, label, color in items:
                text(item_x, top + 16 * index, label, color=color)
        plot_top, plot_bottom = top + 12 + 16 * (len(rows) - 1), top + 88
        seqs = {line_spec.id: window(spec.key, line_spec.id) for line_spec in spec.lines}
        finite = [v for seq in seqs.values() for v in seq if v is not None]
        if spec.bounds:
            low, high = spec.bounds
            low, high = min([low, *finite]), max([high, *finite])
        else:
            candidates = finite + [float(r) for r in spec.references]
            low, high = (min(candidates), max(candidates)) if candidates else (0.0, 1.0)
            pad = (high - low) * .08 or max(abs(high) * .01, 1e-6)
            low, high = low - pad, high + pad
        if high == low:
            high += 1
        sy = lambda value: plot_bottom - (value - low) / (high - low) * (plot_bottom - plot_top)
        quantity = spec.lines[0].kind == "quantity"

        def axis(value):
            if quantity:
                return format_value("quantity", value, language)
            return _axis_number(value, high - low).replace("-", "−")

        labelled = []
        ticks = sorted(set(spec.bounds) | set(spec.references)) if spec.bounds else [low, (low + high) / 2, high]
        for value in ticks:
            line(left, sy(value), right, sy(value))
        for value in [*spec.references, *ticks]:
            yy = sy(value)
            if any(abs(yy - other) < 13 for other in labelled):
                continue
            labelled.append(yy)
            text(right + 7, yy + 4, axis(value))
        reference = _REFERENCE[1 if dark else 0]
        for value in spec.references:
            line(left, sy(value), right, sy(value), reference, "3 4")
        for line_spec in spec.lines:
            polylines(seqs[line_spec.id], sy, palette[line_spec.id], dash="4 3" if line_spec.style == "dash" else "")
        if not finite:
            text(left + 4, (plot_top + plot_bottom) / 2 + 4,
                 "아직 계산할 봉이 부족합니다" if ko else "Not enough bars yet")
        return top + _STUDY_PANEL

    price_top, price_bottom = 74 + dy, 278 + below
    price_y = panel(price_top, price_bottom, lo, hi)
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
    for spec in overlays:
        if spec.key in values:
            draw_study(spec, price_y)
    # Unknown volume stays absent instead of becoming an invented zero.
    volumes = [c.volume for c in bars if c.volume is not None]
    volume_label = "거래량" if language == "ko" else "Volume"
    text(left, 303 + below, volume_label if volumes else volume_label + " —")
    maxvol = max(volumes, default=0) or 1
    for spec in volume_studies:
        if spec.key in values:
            averages = [v for line_spec in spec.lines for v in window(spec.key, line_spec.id) if v is not None]
            maxvol = max([maxvol, *averages])
    for j, c in enumerate(bars):
        if c.volume is not None and c.volume > 0:
            h = c.volume / maxvol * 48
            rect(x(j) - step * .3, 359 + below - h, step * .6, h, up if c.close >= c.open else down)
    line(left, 359 + below, right, 359 + below)
    text(right + 7, 317 + below, number(max(volumes)) if volumes else "—")
    label_x = left + _text_width(volume_label if volumes else volume_label + " —") + 14
    for spec in volume_studies:
        palette = study_colors(spec.key, dark)
        if spec.key not in values:
            text(label_x, 303 + below, f"{spec.label(language)} —")
            label_x += _text_width(f"{spec.label(language)} —") + 14
            continue
        for line_spec in spec.lines:
            text(label_x, 303 + below, line_spec.name(language), color=palette[line_spec.id])
            label_x += _text_width(line_spec.name(language)) + 14
            polylines(window(spec.key, line_spec.id), lambda v: 359 + below - v / maxvol * 48, palette[line_spec.id])
    # Sparse x ticks leave room at mobile widths and for exchange-local times.
    count = min(len(bars), max(2, (right - left) // 160))
    for k in range(count):
        j = round(k * (len(bars) - 1) / max(1, count - 1))
        stamp = bars[j].timestamp
        label = stamp[5:10] + (" " + stamp[11:19 if snapshot.request.interval in LIVE_INTERVALS else 16] if len(stamp) > 10 else "")
        half = len(label) * 3.3  # keep the edge ticks inside the canvas at 12px
        text(min(max(x(j), half + 2), width - half - 2), 379 + below, label, anchor="middle")
    top = 398 + below
    if rsi_on:
        text(left, top, "RSI14 · Wilder", color=colors["rsi"])
        sy = panel(top + 12, top + 88, 0, 100, percent=True)
        for boundary in (30, 70):
            line(left, sy(boundary), right, sy(boundary), gold, "3 4")
        curve("RSI14", sy, colors["rsi"])
        top += 112
    if macd_on:
        text(left, top, "MACD12/26 · Signal9", color=colors["macd"])
        macd_values = [v for key in ("MACD", "SIGNAL", "HISTOGRAM") for v in series[key][start:stop] if v is not None]
        extent = max((abs(v) for v in macd_values), default=1) * 1.1 or 1
        sy = panel(top + 12, top + 88, -extent, extent)
        line(left, sy(0), right, sy(0), fg)
        for j, value in enumerate(series["HISTOGRAM"][start:stop]):
            if value is not None and abs(value) > 1e-12:
                rect(x(j) - step * .3, min(sy(0), sy(value)), step * .6, abs(sy(value) - sy(0)), up if value >= 0 else down)
        curve("MACD", sy, colors["macd"])
        curve("SIGNAL", sy, colors["macd"], dash="4 3")
        top += 112
    for spec in lower:
        top = study_panel(spec, top)
    line(x(selected - start), 73 + dy, x(selected - start), height - 12, fg, "3 4")
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
