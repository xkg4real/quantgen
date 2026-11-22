"""Compact line samples for the dedicated guide's original case chart.

Only renderer descriptors and availability are read here. No indicator is
calculated, no observation is invented, and report/price inputs are untouched.
"""
from dataclasses import dataclass

from core.education.catalog import missing_reason
from core.education.indicators import study
from core.market.presentation import study_colors
from core.theme import DARK, LIGHT


@dataclass(frozen=True)
class LegendSample:
    key: str
    line_id: str
    label: str
    style: str
    color: str
    dash: tuple = ()
    secondary_color: str = ''
    opacity: float = 1.0


_LABELS = {
    'SMA20': ('SMA 20', 'SMA 20'),
    'EMA12': ('EMA 12', 'EMA 12'), 'EMA26': ('EMA 26', 'EMA 26'),
    'SIGNAL': ('Signal', 'Signal'), 'HISTOGRAM': ('Histogram', 'Histogram'),
    'TENKAN': ('전환', 'Tenkan'), 'KIJUN': ('기준', 'Kijun'),
    'SPAN_A': ('선행 A', 'Span A'), 'SPAN_B': ('선행 B', 'Span B'),
    'CHIKOU': ('후행', 'Chikou'), 'SAR': ('SAR', 'SAR'),
    'ENV_UPPER': ('위 +5%', 'Upper +5%'), 'ENV_MIDDLE': ('MA 20', 'MA 20'),
    'ENV_LOWER': ('아래 −5%', 'Lower −5%'),
    'KC_UPPER': ('위', 'Upper'), 'KC_MIDDLE': ('EMA 20', 'EMA 20'),
    'KC_LOWER': ('아래', 'Lower'),
    'DC_UPPER': ('최고 20', 'High 20'), 'DC_MIDDLE': ('중간', 'Middle'),
    'DC_LOWER': ('최저 20', 'Low 20'),
    'BB_UPPER': ('위 밴드', 'Upper band'), 'BB_LOWER': ('아래 밴드', 'Lower band'),
    'PSY': ('PSY 10', 'PSY 10'), 'VOLUME_MA': ('거래량 MA 20', 'Volume MA 20'),
    'SHORT_RATIO': ('공매도 %', 'Short-sale %'),
}


def line_legend(series, keys, language='ko', *, focus=None, dark=False,
                renderer='reference', unavailable=(), price_color=''):
    """Samples match the selected chart renderer, rather than a style's name.

    The reference renderer draws a dot-designated series as a path. Its dash
    spacing differs from the candle renderer. Candle histograms use the same
    positive/negative colours as its actual bars.
    """
    if renderer not in ('reference', 'candles'):
        raise ValueError('Unknown guide renderer')
    if series is None or not getattr(series, 'closes', ()):
        return ()
    keys = tuple(keys)
    key = focus if focus in keys else next(iter(keys), None)
    ko = language == 'ko'
    candles = renderer == 'candles'
    if key is None:
        if candles:
            from core.market.detail_svg import CANDLES
            up, down = CANDLES[bool(dark)]
            return (LegendSample('', 'CLOSE', '가격' if ko else 'Price',
                                 'candles', up, secondary_color=down),)
        return (LegendSample('', 'CLOSE', '가격' if ko else 'Price', 'solid',
                             price_color or (DARK if dark else LIGHT).text),)
    if key in unavailable or missing_reason(series, key, language):
        return ()
    spec = study(key)
    palette = study_colors(key, bool(dark))
    samples = []
    for line in spec.lines:
        style = line.style
        if not candles and style == 'dots':
            style = 'solid'  # catalogue chart_svg's actual path rendering
        color, secondary, opacity = palette[line.id], '', 1.0
        if candles and style == 'bars':
            from core.market.detail_svg import CANDLES
            color, secondary = CANDLES[bool(dark)]
            opacity = .55
        label = _LABELS.get(line.id, (line.ko, line.en))[0 if ko else 1]
        samples.append(LegendSample(key, line.id, label, style, color,
                       (5., 4.) if candles and style == 'dash' else
                       (5., 3.) if style == 'dash' else (),
                       secondary, opacity))
    if candles and key == 'bb':
        samples.append(LegendSample(key, 'BAND', 'BB', 'band',
                                   palette['BB_UPPER'], opacity=.07))
    elif candles and key == 'ichimoku':
        samples.append(LegendSample(key, 'CLOUD', '구름' if ko else 'Cloud',
                                   'band', palette['SPAN_A'],
                                   secondary_color=palette['KIJUN'], opacity=.13))
    return tuple(samples)


def legend_layout(samples, panel, measure, *, row_height=18., swatch_width=28.,
                  padding=5., margin=5.):
    """Pack one quiet legend at the plot's bottom right in logical pixels.

    The caller supplies its existing font's measurements. A too-small plot
    returns no overlay instead of shrinking type or crossing its axes.
    Rectangles are (left, top, width, height), and inputs remain unchanged.
    """
    samples = tuple(samples)
    if not samples:
        return None, ()
    left, top, right, bottom = map(float, panel)
    width, height = right-left-2*margin, bottom-top-2*margin
    if width < swatch_width+padding*2+30 or height < row_height+padding*2:
        return None, ()
    max_rows = max(1, int((height-2*padding)//row_height))
    columns = (len(samples)+max_rows-1)//max_rows
    # All names stay next to their actual sample; do not silently omit rows.
    if width/columns < swatch_width+padding*2+30:
        return None, ()
    rows = (len(samples)+columns-1)//columns
    wanted = max(float(measure(sample.label)) for sample in samples)+swatch_width+2*padding+8
    column_width = min(width/columns, max(96., wanted))
    box_width = column_width*columns
    box_height = rows*row_height+2*padding
    x, y = right-margin-box_width, bottom-margin-box_height
    placements = []
    for i, sample in enumerate(samples):
        col, row = i//rows, i%rows
        rx, ry = x+col*column_width+padding, y+padding+row*row_height
        placements.append((sample, (rx, ry, swatch_width, row_height),
                           (rx+swatch_width+8, ry, column_width-swatch_width-2*padding-8,
                            row_height)))
    return (x, y, box_width, box_height), tuple(placements)
