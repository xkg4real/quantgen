"""Full-window price chart for the native stock detail view (owner request 2026-11-11, UI-D8).

Owner: "해당 차트로 화면을 거의 가득채워도 가능해. 정보전달과 가독성에 신경쓰고 공간 넉넉하게써줘". Unlike
`core.market.presentation.chart_svg` (a document-height chart that grows with every study), this renderer draws at
an exact width x height: a header band left empty for the view's OHLC strip and indicator legend, the price pane
with the volume overlay in its bottom part, one sub-panel per lower study (each sized so that the whole chart fits;
panels that would be too small are listed in `hidden_panels`), and the time axis. The price scale is on the right
with a filled last-price tag, as in TradingView. Every study comes from core.education.indicators (no look-ahead,
warm-up stays empty); this module only draws. Pure: no Qt, no I/O.

Text is drawn at 12px or larger in the app family. The caller passes display labels (month names), so the output
contains only digits and those labels: English output has no Hangul.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import math

from core.market.presentation import SVG_FONT_FAMILY, SVG_MIN_TEXT, _text_width, study_colors

HEADER = 58          # empty band at the top: OHLC strip (y 6-30) and the indicator legend (y 32-54), drawn by the view
AXIS = 28            # time axis under the last panel
RIGHT_AXIS = 80      # price axis on the right
PLOT_LEFT = 12
PANEL_GAP = 6
PANEL_HEAD = 26      # each sub-panel's first rows hold the view's panel header (name, values, reading)
MIN_PANEL = 84
NOTE_PANEL = PANEL_HEAD + 8   # a study that cannot be drawn here: its header row says why
PANEL_SHARE = 0.56   # sub-panels take at most this share of the usable height
VOLUME_SHARE = 0.18  # the volume overlay fills the bottom of the price pane
MIN_PRICE = 140
EN_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
CANDLES = {False: ("#D94A52", "#397AC4"), True: ("#EC5F67", "#4F92DC")}   # rise red, fall blue (Korean convention)
THEMES = {
    False: {"bg": "#F7F5F0", "text": "#202823", "muted": "#646E68", "border": "#E2E3DB"},
    True: {"bg": "#101915", "text": "#EAF1E9", "muted": "#A7B8AC", "border": "#34483C"},
}


def mix(a, b, amount):
    """`amount` of the way from hex colour a to b."""
    a, b = a.lstrip("#"), b.lstrip("#")
    pa, pb = [int(a[i:i + 2], 16) for i in (0, 2, 4)], [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(pa, pb))


def _luminance(color):
    c = color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        v = int(c[i:i + 2], 16) / 255
        out.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@dataclass(frozen=True)
class ChartLayout:
    """Geometry of one render, for the view's overlays and pointer mapping."""
    width: int
    height: int
    plot_left: float
    plot_right: float
    step: float
    start: int                    # first bar index drawn
    stop: int                     # one past the last bar drawn
    cursor: int                   # the selected bar (inside the window)
    price: tuple = (0.0, 0.0)     # top, bottom of the price pane
    volume: tuple = (0.0, 0.0)    # top, bottom of the volume overlay
    panels: tuple = ()            # (key, top, bottom) per shown sub-panel, top to bottom
    axis_top: float = 0.0
    hidden_panels: tuple = ()     # sub-panel keys that did not fit
    unavailable: dict = field(default_factory=dict, hash=False)   # key -> engine availability code
    price_range: tuple = (0.0, 1.0)  # low, high used by the price renderer
    price_scale: tuple = (0.0, 1.0)  # pixel top, bottom of that exact scale

    def y_of_price(self, value):
        low, high = self.price_range
        top, bottom = self.price_scale
        return bottom - (value - low) / (high - low) * (bottom - top)

    def price_at(self, y):
        low, high = self.price_range
        top, bottom = self.price_scale
        return low + (bottom - y) / max(bottom - top, 1e-9) * (high - low)

    def index_at(self, x):
        """The bar under a pointer x (clamped to the window)."""
        if self.stop <= self.start:
            return self.start
        j = int((float(x) - self.plot_left) // max(self.step, 1e-9))
        return self.start + max(0, min(self.stop - self.start - 1, j))

    def x_of(self, index):
        return self.plot_left + (index - self.start + 0.5) * self.step


def panel_keys(studies):
    """Selected registry keys that draw in their own sub-panel, in the order they were turned on: a new panel
    goes to the bottom, and when the window is too short the latest ones are the ones hidden."""
    from core.education.indicators import study
    out = []
    for key in studies:
        try:
            spec = study(key)
        except ValueError:
            continue
        if not spec.overlay and spec.key not in out:
            out.append(spec.key)
    return tuple(out)


def overlay_keys(studies):
    from core.education.indicators import STUDIES, study
    wanted = set()
    for key in studies:
        try:
            wanted.add(study(key).key)
        except ValueError:
            continue
    return tuple(s.key for s in STUDIES if s.key in wanted and s.overlay)


def max_panels(height):
    """How many full sub-panels fit in a chart of this height."""
    usable = max(0, height - HEADER - AXIS)
    return max(0, int(PANEL_SHARE * usable // (MIN_PANEL + PANEL_GAP)))


def plan_panels(height, keys, unavailable=()):
    """((key, height), ...) shown and the keys hidden, so the price pane keeps at least its share."""
    usable = max(0, height - HEADER - AXIS)
    budget = PANEL_SHARE * usable
    notes = [k for k in keys if k in unavailable]
    full = [k for k in keys if k not in unavailable]
    room = budget - len(notes) * (NOTE_PANEL + PANEL_GAP)
    fit = max(0, int(room // (MIN_PANEL + PANEL_GAP)))
    shown_full, hidden = full[:fit], tuple(full[fit:])
    if shown_full:
        each = min(150.0, max(MIN_PANEL, 0.2 * usable))
        if len(shown_full) * (each + PANEL_GAP) > room:
            each = room / len(shown_full) - PANEL_GAP
        each = max(MIN_PANEL, each)
    else:
        each = 0
    sizes = tuple((k, float(NOTE_PANEL) if k in unavailable else float(each))
                  for k in keys if k in notes or k in shown_full)
    return sizes, hidden


def _nice_step(span, count):
    raw = span / max(1, count)
    if raw <= 0 or not math.isfinite(raw):
        return 1.0
    power = 10 ** math.floor(math.log10(raw))
    # The nice step nearest the raw one (in ratio), so a tall pane gets enough labelled grid lines.
    return min((m * power for m in (1, 2, 2.5, 5, 10)), key=lambda step: abs(math.log(step / raw)))


def nice_ticks(low, high, count=5):
    step = _nice_step(high - low, count)
    first = math.ceil(low / step) * step
    out, value = [], first
    while value <= high + step * 1e-9 and len(out) < 50:
        out.append(round(value, 10))
        value += step
    return out, step


def price_text(value, step=None):
    """Axis and tag figures: thousands separators, decimals from the grid step or the magnitude."""
    if value is None or not math.isfinite(value):
        return "—"
    if step is not None and step > 0:
        decimals = next((d for d in range(7) if abs(round(step, d) - step) <= step * 1e-6), 6)
    else:
        size = abs(value)
        decimals = 0 if size >= 1000 else 2 if size >= 1 else 4
    text = f"{value:,.{decimals}f}"
    return text.replace("-", "−")


def compact(value):
    """12.35M style (the app's compact volume convention in both languages)."""
    if value is None or not math.isfinite(value):
        return "—"
    size, sign = abs(value), "−" if value < 0 else ""
    for unit, scale in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if size >= scale:
            text = f"{size / scale:,.2f}".rstrip("0").rstrip(".")
            return f"{sign}{text}{unit}"
    return f"{sign}{size:,.0f}"


def _stamp(candle):
    return str(getattr(candle, "timestamp", ""))


def cursor_label(stamp, intraday, interval="1d"):
    """The selected candle's time on the axis: date and clock for minutes, the date for days and weeks, the
    month for monthly candles and the year for yearly ones."""
    stamp = str(stamp)
    if intraday and len(stamp) >= 16:
        return f"{stamp[5:7]}/{stamp[8:10]} {stamp[11:16]}"
    if interval == "1Y":
        return stamp[:4]
    if interval == "1M":
        return stamp[:7]
    return stamp[:10]


def _time_ticks(bars, start, x, *, intraday, months, min_gap):
    """[(x, label, major)], spaced at least `min_gap` px; year/day boundaries are kept first."""
    candidates = []
    previous = None
    for j, candle in enumerate(bars):
        stamp = _stamp(candle)
        if len(stamp) < 10:
            continue
        year, month, day = stamp[:4], stamp[5:7], stamp[8:10]
        if intraday:
            clock = stamp[11:16] if len(stamp) >= 16 else ""
            if previous is None or previous[:10] != stamp[:10]:
                candidates.append((x(j), f"{int(month)}/{int(day)}", 2))
            elif clock and clock[3:5] in ("00", "30"):
                candidates.append((x(j), clock, 0 if clock[3:5] == "30" else 1))
        else:
            if previous is None:
                pass
            elif previous[:4] != year:
                candidates.append((x(j), year, 3))
            elif previous[5:7] != month:
                candidates.append((x(j), months[int(month) - 1], 2))
            elif previous[8:10] != day:
                candidates.append((x(j), f"{int(month)}/{int(day)}", 0))
        previous = stamp
    kept = []
    for level in (3, 2, 1, 0):
        for item in candidates:
            if item[2] != level:
                continue
            width = _text_width(item[1]) + min_gap
            if all(abs(item[0] - other[0]) >= max(width, _text_width(other[1]) + min_gap) for other in kept):
                kept.append(item)
        if level == 2 and len(kept) >= 4:
            break
    return sorted(kept)


def render(snapshot, *, studies=(), cursor=None, end=None, visible=120, width=900, height=600, dark=False,
           theme=None, months=EN_MONTHS, supply=None, values=None, price_levels=()):
    """(svg text, ChartLayout) of `snapshot` at exactly width x height.

    `studies`: registry keys (core.education.indicators.STUDIES; 'bollinger' is accepted for 'bb'). `end` is the
    last bar index shown (None follows the latest bar) and `visible` the number of bars. `values` may carry
    precomputed engine results {key: {line: array}}; missing ones are computed here. `theme` overrides the
    palette colours bg/text/muted/border.
    """
    from core.education import indicators as engine
    width, height = max(240, int(width)), max(200, int(height))
    colors = dict(THEMES[bool(dark)], **(theme or {}))
    bg, fg, muted = colors["bg"], colors["text"], colors["muted"]
    grid = mix(colors["border"], bg, 0.35)
    soft = mix(colors["border"], bg, 0.6)
    up, down = CANDLES[bool(dark)]
    candles = tuple(getattr(snapshot, "candles", ()) or ())
    request = getattr(snapshot, "request", None)
    interval = getattr(request, "interval", "1d")
    asset = getattr(getattr(request, "instrument", None), "asset", "domestic_stock")
    intraday = interval not in ("1d", "1w", "1M", "1Y")
    if isinstance(supply, dict):
        supply = engine.supply_from_rows(supply.get("flows") or (), supply.get("shorts") or ())
    keys = []
    for key in studies:
        try:
            spec = engine.study(key)
        except ValueError:
            continue
        if spec.key not in keys:
            keys.append(spec.key)
    has_volume = any(c.volume is not None for c in candles)
    unavailable = {}
    for key in keys:
        code = engine.availability(key, asset=asset, interval=interval, supply=supply, has_volume=has_volume)
        if code:
            unavailable[key] = code
    overlays = [k for k in overlay_keys(keys) if k not in unavailable]
    lower = panel_keys(keys)
    sizes, hidden = plan_panels(height, lower, unavailable)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" fill="{bg}"/>']

    def text(x, y, value, *, color=muted, size=SVG_MIN_TEXT, anchor="start", weight=None):
        size = max(SVG_MIN_TEXT, size)
        bold = f' font-weight="{weight}"' if weight else ""
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-family="{SVG_FONT_FAMILY}" '
                     f'font-size="{size}"{bold} text-anchor="{anchor}">{escape(str(value))}</text>')

    def line(x1, y1, x2, y2, color=grid, dash="", width_=1.0, opacity=None):
        extra = (f' stroke-dasharray="{dash}"' if dash else "") + (f' stroke-opacity="{opacity}"' if opacity else "")
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" '
                     f'stroke-width="{width_}"{extra}/>')

    def rect(x, y, w, h, color, opacity=None, radius=0):
        extra = (f' fill-opacity="{opacity}"' if opacity is not None else "") + (f' rx="{radius}"' if radius else "")
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(.6, w):.2f}" height="{max(.6, h):.2f}" '
                     f'fill="{color}"{extra}/>')

    plot_left, plot_right = PLOT_LEFT, width - RIGHT_AXIS
    axis_top = height - AXIS
    panels_total = sum(h + PANEL_GAP for _, h in sizes)
    price_top = HEADER
    price_bottom = max(price_top + MIN_PRICE, axis_top - panels_total)
    if not candles:
        layout = ChartLayout(width, height, plot_left, plot_right, 1.0, 0, 0, 0, (price_top, price_bottom),
                             (price_bottom, price_bottom), (), axis_top, tuple(hidden), dict(unavailable))
        return "".join(parts) + "</svg>", layout

    total = len(candles)
    visible = max(1, min(total, int(visible or total)))
    stop = total if end is None else max(1, min(total, int(end) + 1))
    stop = max(stop, visible)
    start = stop - visible
    bars = candles[start:stop]
    step = (plot_right - plot_left) / len(bars)
    x = lambda j: plot_left + (j + .5) * step
    selected = stop - 1 if cursor is None else max(start, min(stop - 1, int(cursor)))

    values = dict(values or {})
    engine_bars = None
    for key in keys:
        if key in unavailable or key in values:
            continue
        if engine_bars is None:
            engine_bars = engine.bars_from_candles(candles, interval)
        values[key] = engine.compute_study(key, engine_bars, supply=supply)

    def window(key, line_id):
        data = values[key][line_id]
        return [None if not math.isfinite(float(v)) else float(v) for v in data[start:stop]]

    # Price scale: candles and the overlay studies in view.
    lo, hi = min(c.low for c in bars), max(c.high for c in bars)
    for key in overlays:
        spec = engine.study(key)
        if spec.panel != "price":
            continue
        for line_spec in spec.lines:
            seen = [v for v in window(key, line_spec.id) if v is not None]
            if seen:
                lo, hi = min(lo, min(seen)), max(hi, max(seen))
    levels = [float(v) for v in price_levels if math.isfinite(float(v)) and float(v) > 0]
    if levels:
        lo, hi = min(lo, *levels), max(hi, *levels)
    pad = (hi - lo) * .04 or max(abs(hi) * .01, .01)
    lo, hi = lo - pad, hi + pad
    pane = price_bottom - price_top
    volume_top = price_bottom - VOLUME_SHARE * pane
    scale_top, scale_bottom = price_top + 10, price_bottom - 0.14 * pane
    price_y = lambda v: scale_bottom - (v - lo) / (hi - lo) * (scale_bottom - scale_top)

    # Grid and price axis.
    ticks, tick_step = nice_ticks(lo, hi, max(3, int((scale_bottom - scale_top) // 52)))
    last = candles[-1]
    prev_close = candles[-2].close if total > 1 else last.open
    last_tone = up if last.close >= prev_close else down
    last_y = price_y(last.close)
    tag_y = last_y if price_top + 10 <= last_y <= price_bottom - 4 else None
    for value in ticks:
        yy = price_y(value)
        if not price_top + 4 <= yy <= price_bottom - 2:
            continue
        line(plot_left, yy, plot_right, yy)
        if tag_y is None or abs(yy - tag_y) > 14:
            text(plot_right + 8, yy + 4, price_text(value, tick_step))
    time_ticks = _time_ticks(bars, start, x, intraday=intraday, months=months or EN_MONTHS, min_gap=28)
    for tx, _label, _major in time_ticks:
        line(tx, price_top, tx, axis_top, soft)

    # Bollinger fill and Ichimoku cloud behind the candles.
    if "bb" in overlays:
        upper, lower_band = window("bb", "BB_UPPER"), window("bb", "BB_LOWER")
        color = study_colors("bb", dark)["BB_UPPER"]
        _band(parts, x, price_y, upper, lower_band, color, 0.07)
    if "ichimoku" in overlays:
        palette = study_colors("ichimoku", dark)
        span_a, span_b = window("ichimoku", "SPAN_A"), window("ichimoku", "SPAN_B")
        for j in range(len(bars) - 1):
            a0, a1, b0, b1 = span_a[j], span_a[j + 1], span_b[j], span_b[j + 1]
            if None in (a0, a1, b0, b1):
                continue
            fill = palette["SPAN_A"] if a0 + a1 >= b0 + b1 else palette["KIJUN"]
            parts.append(f'<polygon points="{x(j):.2f},{price_y(a0):.2f} {x(j + 1):.2f},{price_y(a1):.2f} '
                         f'{x(j + 1):.2f},{price_y(b1):.2f} {x(j):.2f},{price_y(b0):.2f}" fill="{fill}" '
                         f'fill-opacity="0.13"/>')

    # Volume overlay (unknown volume stays absent, never an invented zero).
    volumes = [c.volume for c in bars if c.volume is not None]
    max_volume = max(volumes, default=0) or 1
    if "volume_ma" in overlays:
        averages = [v for v in window("volume_ma", "VOLUME_MA") if v is not None]
        max_volume = max([max_volume, *averages])
    volume_h = price_bottom - volume_top - 2
    for j, c in enumerate(bars):
        if c.volume is not None and c.volume > 0:
            h = c.volume / max_volume * volume_h
            rect(x(j) - step * .32, price_bottom - h, step * .64, h, up if c.close >= c.open else down, 0.26)
    if "volume_ma" in overlays:
        color = study_colors("volume_ma", dark)["VOLUME_MA"]
        _polyline(parts, x, lambda v: price_bottom - v / max_volume * volume_h, window("volume_ma", "VOLUME_MA"),
                  color)

    # Candles.
    body = max(1.0, step * .62)
    for j, c in enumerate(bars):
        color = up if c.close >= c.open else down
        line(x(j), price_y(c.high), x(j), price_y(c.low), color)
        top, bottom = price_y(max(c.open, c.close)), price_y(min(c.open, c.close))
        rect(x(j) - body / 2, top, body, max(1.0, bottom - top), color)

    # Price overlays.
    for key in overlays:
        spec = engine.study(key)
        if spec.panel != "price":
            continue
        palette = study_colors(key, dark)
        for line_spec in spec.lines:
            seq = window(key, line_spec.id)
            color = palette[line_spec.id]
            if line_spec.style == "dots":
                radius = max(1.3, min(2.6, step * .22))
                for j, value in enumerate(seq):
                    if value is not None:
                        parts.append(f'<circle cx="{x(j):.2f}" cy="{price_y(value):.2f}" r="{radius:.2f}" '
                                     f'fill="{color}"/>')
            else:
                _polyline(parts, x, price_y, seq, color, dash="5 4" if line_spec.style == "dash" else "",
                          width_=1.6)

    # Last price line and tag on the axis.
    if tag_y is not None:
        line(plot_left, tag_y, plot_right, tag_y, last_tone, "2 3", 1.0, 0.8)
        rect(plot_right + 2, tag_y - 11, RIGHT_AXIS - 6, 22, last_tone, radius=4)
        text(plot_right + 8, tag_y + 4.5, price_text(last.close),
             color="#FFFFFF", weight=600)
    if selected != total - 1:
        cy = price_y(candles[selected].close)
        if price_top + 10 <= cy <= price_bottom - 4 and (tag_y is None or abs(cy - tag_y) > 22):
            rect(plot_right + 2, cy - 11, RIGHT_AXIS - 6, 22, fg, radius=4)
            text(plot_right + 8, cy + 4.5, price_text(candles[selected].close),
                 color=bg, weight=500)

    # Sub-panels.
    panels, top = [], price_bottom
    for key, size in sizes:
        top += PANEL_GAP
        bottom = top + size
        panels.append((key, top, bottom))
        line(plot_left, top, width, top, mix(colors["border"], bg, 0.15))
        if key not in unavailable:
            _study_panel(parts, engine.study(key), window, x, len(bars), step, top + PANEL_HEAD, bottom - 4,
                         plot_left, plot_right, dark, grid, muted, up, down, text, line, rect)
        top = bottom

    # Time axis and cursor.
    line(plot_left, axis_top, width, axis_top, mix(colors["border"], bg, 0.15))
    cursor_x = x(selected - start)
    cursor_text = cursor_label(_stamp(candles[selected]), intraday, interval)
    cursor_w = _text_width(cursor_text) + 16
    for tx, label, _major in time_ticks:
        if abs(tx - cursor_x) < cursor_w / 2 + _text_width(label) / 2 + 6:
            continue
        half = _text_width(label) / 2
        text(min(max(tx, plot_left + half), plot_right - half), axis_top + 18, label, anchor="middle")
    line(cursor_x, price_top, cursor_x, axis_top, fg, "3 4", 1.0, 0.55)
    cx = min(max(cursor_x, plot_left + cursor_w / 2), plot_right - cursor_w / 2)
    rect(cx - cursor_w / 2, axis_top + 4, cursor_w, 20, fg, radius=4)
    text(cx, axis_top + 18, cursor_text, color=bg, anchor="middle", weight=500)

    layout = ChartLayout(width, height, plot_left, plot_right, step, start, stop, selected,
                         (price_top, price_bottom), (volume_top, price_bottom), tuple(panels), axis_top,
                         tuple(hidden), dict(unavailable), (lo, hi), (scale_top, scale_bottom))
    return "".join(parts) + "</svg>", layout


def _polyline(parts, x, sy, seq, color, *, dash="", width_=1.5):
    segment = []

    def flush():
        if len(segment) > 1:
            parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{color}" '
                         f'stroke-width="{width_}" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else "")
                         + '/>')
        elif len(segment) == 1:
            px, py = segment[0].split(",")
            parts.append(f'<circle cx="{px}" cy="{py}" r="1.2" fill="{color}"/>')
        segment.clear()

    for j, value in enumerate(seq):
        if value is None:
            flush()
        else:
            segment.append(f"{x(j):.2f},{sy(value):.2f}")
    flush()


def _band(parts, x, sy, upper, lower, color, opacity):
    run = []

    def flush():
        if len(run) > 1:
            top = " ".join(f"{x(j):.2f},{sy(u):.2f}" for j, u, _ in run)
            bottom = " ".join(f"{x(j):.2f},{sy(l):.2f}" for j, _, l in reversed(run))
            parts.append(f'<polygon points="{top} {bottom}" fill="{color}" fill-opacity="{opacity}"/>')
        run.clear()

    for j, (u, l) in enumerate(zip(upper, lower)):
        if u is None or l is None:
            flush()
        else:
            run.append((j, u, l))
    flush()


def _study_panel(parts, spec, window, x, count, step, plot_top, plot_bottom, plot_left, plot_right, dark, grid,
                 muted, up, down, text, line, rect):
    palette = study_colors(spec.key, dark)
    seqs = {line_spec.id: window(spec.key, line_spec.id) for line_spec in spec.lines}
    finite = [v for seq in seqs.values() for v in seq if v is not None]
    if spec.bounds:
        low, high = spec.bounds
        low, high = min([low, *finite]), max([high, *finite])
    else:
        candidates = finite + [float(r) for r in spec.references]
        low, high = (min(candidates), max(candidates)) if candidates else (0.0, 1.0)
        # Nothing computed yet (too little history): a plain ±1 frame, not ±1e-06 labels.
        pad = (high - low) * .1 or max(abs(high) * .01, 1e-6 if finite else 1.0)
        low, high = low - pad, high + pad
    if high == low:
        high += 1
    sy = lambda v: plot_bottom - (v - low) / (high - low) * (plot_bottom - plot_top)
    quantity = spec.lines[0].kind == "quantity"
    references = sorted(float(r) for r in spec.references)
    if spec.bounds and len(references) >= 2:
        band_top, band_bottom = sy(references[-1]), sy(references[0])
        rect(plot_left, band_top, plot_right - plot_left, band_bottom - band_top, palette[spec.lines[0].id], 0.05)
    fitted = [] if spec.bounds or not finite else [v for v in nice_ticks(low, high, 2)[0] if v not in references]
    for value in fitted:
        line(plot_left, sy(value), plot_right, sy(value), grid)
    for value in references:
        line(plot_left, sy(value), plot_right, sy(value), muted, "3 4", 1.0, 0.5)
    taken = []
    for value in [*references, *fitted]:
        yy = sy(value)
        if not plot_top - 2 <= yy <= plot_bottom + 2 or any(abs(yy - t) < 13 for t in taken):
            continue
        taken.append(yy)
        label = compact(value) if quantity else (f"{value:g}" if abs(value) < 1e4 else price_text(value))
        text(plot_right + 8, yy + 4, label.replace("-", "−"))
    for line_spec in spec.lines:
        seq = seqs[line_spec.id]
        color = palette[line_spec.id]
        if line_spec.style == "bars":
            zero = sy(0.0) if low <= 0 <= high else plot_bottom
            for j, value in enumerate(seq):
                if value is not None and abs(value) > 1e-12:
                    yy = sy(value)
                    rect(x(j) - step * .3, min(zero, yy), max(1.0, step * .6), abs(yy - zero),
                         up if value >= 0 else down, 0.55)
        elif line_spec.style == "dots":
            for j, value in enumerate(seq):
                if value is not None:
                    parts.append(f'<circle cx="{x(j):.2f}" cy="{sy(value):.2f}" r="1.6" fill="{color}"/>')
        else:
            _polyline(parts, x, sy, seq, color, dash="5 4" if line_spec.style == "dash" else "", width_=1.5)


__all__ = ["ChartLayout", "render", "max_panels", "plan_panels", "panel_keys", "overlay_keys", "price_text",
           "compact", "cursor_label", "contrast", "mix", "HEADER", "AXIS", "PANEL_HEAD", "RIGHT_AXIS",
           "EN_MONTHS", "THEMES", "CANDLES"]
