"""Small reading labels anchored to the original guide chart's own values.

This is a view-only geometry adapter. It neither creates bars nor changes the
shared renderers, indicator definitions or report inputs. Reference-close and
observed-candle charts retain the exact scales already used to draw their lines.
"""
from dataclasses import dataclass
import math

from core.education.catalog import values_for, plot_bounds
from core.education.indicators import study
from core.market.presentation import study_colors


@dataclass(frozen=True)
class CaseAnnotation:
    key: str
    line_id: str
    index: int
    value: float | None
    x: float | None
    y: float | None
    text: tuple
    color: str
    panel: tuple


# These name the actual plotted lines; they do not classify a price as a trade.
_COPY = {
    'SMA20': ('최근 20개 가격의 평균', 'Mean of the last 20 closes'),
    'EMA12': ('최근 가격에 더 민감한 평균', 'Faster, recent-weighted mean'),
    'EMA26': ('긴 흐름을 천천히 반영하는 평균', 'Slower, recent-weighted mean'),
    'MACD': ('빠른 평균 − 느린 평균', 'Fast mean minus slow mean'),
    'SIGNAL': ('MACD를 부드럽게 만든 선', 'Smoothed MACD line'),
    'HISTOGRAM': ('두 선의 차이를 그린 막대', 'Bars show the two-line gap'),
    'TENKAN': ('최근 9개 구간의 중간 가격', 'Midpoint of the last 9 ranges'),
    'KIJUN': ('최근 26개 구간의 중간 가격', 'Midpoint of the last 26 ranges'),
    'SPAN_A': ('앞으로 옮겨 그린 선 · 예측 아님', 'Shifted line, not a forecast'),
    'SPAN_B': ('52개 범위의 중간값을 옮긴 선', 'Shifted 52-range midpoint'),
    'CHIKOU': ('종가를 뒤로 옮겨 그린 선', 'Close plotted backward'),
    'SAR': ('가격 위·아래 점의 위치를 비교', 'Compare dots with the price'),
    'ADX': ('추세의 강도 · 상승 방향 아님', 'Trend strength, not direction'),
    'PDI': ('상승 방향 성분', 'Upward direction component'),
    'MDI': ('하락 방향 성분', 'Downward direction component'),
    'ENV_UPPER': ('20개 평균보다 5% 위', '5% above the 20-close mean'),
    'ENV_MIDDLE': ('띠의 기준이 되는 평균', 'The mean at the band centre'),
    'ENV_LOWER': ('20개 평균보다 5% 아래', '5% below the 20-close mean'),
    'KC_UPPER': ('중심 평균 + 변동폭', 'Centre mean plus range'),
    'KC_MIDDLE': ('최근 가격에 가중한 중심 평균', 'Recent-weighted centre mean'),
    'KC_LOWER': ('중심 평균 − 변동폭', 'Centre mean minus range'),
    'DC_UPPER': ('최근 20개 구간의 최고 가격', 'High of the last 20 ranges'),
    'DC_MIDDLE': ('최고·최저 사이의 중간', 'Midpoint of the high and low'),
    'DC_LOWER': ('최근 20개 구간의 최저 가격', 'Low of the last 20 ranges'),
    'RSI14': ('30·70과 비교 · 반전 확정 아님', 'Compare 30/70; no certain turn'),
    'STOCH_K': ('최근 가격 범위 안의 위치', 'Position in the price range'),
    'STOCH_D': ('위치 변화를 부드럽게 만든 선', 'Smoothed position line'),
    'STOCHRSI_K': ('가격 아닌 RSI 범위 안의 위치', 'Position in the RSI range'),
    'STOCHRSI_D': ('RSI 위치를 부드럽게 만든 선', 'Smoothed RSI-position line'),
    'CCI': ('평소 평균과의 거리 · ±100 비교', 'Distance from mean; compare ±100'),
    'WILLR': ('−20은 위쪽, −80은 아래쪽', '−20 near the top, −80 near bottom'),
    'ROC': ('12개 구간 전보다 변한 비율', 'Change from 12 closes earlier'),
    'DISPARITY': ('평균이 100일 때 현재 가격', 'Price with the mean set to 100'),
    'PSY': ('최근 10번 중 가격이 오른 비율', 'Share of rises in the last 10'),
    'BB_UPPER': ('위 밴드 · 하락 확정선 아님', 'Upper band, not a certain fall'),
    'BB_LOWER': ('아래 밴드 · 반등 확정선 아님', 'Lower band, not a certain bounce'),
    'ATR': ('가격 움직임의 폭 · 방향 아님', 'Movement range, not direction'),
    'PERCENT_B': ('아래 밴드 0 · 위 밴드 1', 'Lower band 0; upper band 1'),
    'BANDWIDTH': ('밴드가 벌어진 폭의 비율', 'Relative distance between bands'),
    'VOLUME_MA': ('최근 20개 거래량의 평균', 'Mean of the last 20 volumes'),
    'OBV': ('상승·하락에 따라 더한 거래량', 'Volume accumulated by close moves'),
    'MFI': ('가격·거래량 지수 · 20·80 비교', 'Price-volume index; compare 20/80'),
    'VWAP': ('거래량 비중으로 평균낸 가격', 'Volume-weighted session mean'),
    'FOREIGN': ('외국인 순매수 수량의 누계', 'Cumulative foreign net buys'),
    'INSTITUTION': ('기관 순매수 수량의 누계', 'Cumulative institutional net buys'),
    'INDIVIDUAL': ('개인 순매수 수량의 누계', 'Cumulative individual net buys'),
    'SHORT_RATIO': ('그날 거래량 중 공매도 비중', 'Short-sale share of daily volume'),
}


def _finite(seq):
    return [float(v) for v in seq if v is not None and math.isfinite(float(v))]


def _reference_scale(series, keys, values, key, top):
    """The reference-close catalogue's exact y range and plot rectangle."""
    if study(key).panel == 'price':
        raw = _finite(series.closes)
        for selected in keys:
            if selected in values and study(selected).panel == 'price':
                raw.extend(v for seq in values[selected].values() for v in _finite(seq))
        ytop, bottom = top + 22, top + 257
        bounds = ()
    else:
        lower = [k for k in keys if study(k).panel != 'price' and k in values]
        if key not in lower:
            return None
        ytop = top + 285 + lower.index(key) * 135 + 22
        bottom = ytop + 92
        raw = [v for seq in values[key].values() for v in _finite(seq)]
        bounds = study(key).bounds
    if bounds:
        low, high = bounds
    elif raw:
        low, high = min(raw), max(raw)
        pad = max((high-low)*.08, abs(high)*.0001, .00001)
        low, high = low-pad, high+pad
    else:
        low, high = 0., 1.
    return ytop, bottom, low, high


def _candle_scale(spec, values, layout, crop):
    """The detail renderer's exact sub-panel scale, including visible references."""
    panel = next((p for p in layout.panels if p[0] == spec.key), None)
    if panel is None or spec.key in layout.unavailable:
        return None
    from core.market.detail_svg import PANEL_HEAD
    raw = [v for seq in values[spec.key].values() for v in _finite(seq[layout.start:layout.stop])]
    if spec.bounds:
        low, high = min([spec.bounds[0], *raw]), max([spec.bounds[1], *raw])
    else:
        candidates = raw + [float(r) for r in spec.references]
        low, high = (min(candidates), max(candidates)) if candidates else (0., 1.)
        pad = (high-low)*.1 or max(abs(high)*.01, 1e-6 if raw else 1.)
        low, high = low-pad, high+pad
    if high == low:
        high += 1
    return panel[1]+PANEL_HEAD-crop, panel[2]-4-crop, low, high


def case_annotations(series, keys, cursor, language='ko', *, width, legend_top,
                     layout=None, crop=0, focus=None, dark=False):
    """Up to three labels of the focused selected study on the original chart.

    Missing data/warm-up yields an unanchored, explicit note, never a fabricated
    point or a point taken from the separate invented lesson. No Qt or I/O here.
    """
    if series is None or not series.closes:
        return ()
    keys = tuple(keys)
    at = max(0, min(len(series.closes)-1, int(cursor)))
    ko = language == 'ko'
    key = focus if focus in keys else next(iter(keys), None)
    left, right = (layout.plot_left, layout.plot_right) if layout else plot_bounds(series, None, width)
    price_panel = (left, (layout.price[0]-crop if layout else legend_top+22),
                   right, (layout.price[1]-crop if layout else legend_top+257))
    if key is None:
        value = float(series.closes[at])
        if layout:
            x, y = layout.x_of(at), layout.y_of_price(value)-crop
        else:
            raw = _finite(series.closes); low, high = min(raw), max(raw)
            pad = max((high-low)*.08, abs(high)*.0001, .00001)
            low, high = low-pad, high+pad
            x = left+(right-left)*at/max(1, len(series.closes)-1)
            y = price_panel[3]-(value-low)/(high-low)*(price_panel[3]-price_panel[1])
        return (CaseAnnotation('', 'CLOSE', at, value, x, y,
                 (('이 날짜의 종가' if ko else 'Close at this date'),
                  ('오른쪽에서 지표를 골라 비교해요' if ko else 'Choose an indicator to compare')),
                 '', price_panel),)
    spec = study(key)
    values = values_for(series, keys)
    palette = study_colors(key, dark)
    if key not in values:
        return (CaseAnnotation(key, '', at, None, None, None,
                 (spec.name(language), '이 사례에 필요한 자료가 없어요' if ko else 'Required data is absent in this case'),
                 next(iter(palette.values())), price_panel),)
    if layout:
        x = layout.x_of(at)
        if spec.panel == 'price':
            sy = lambda value: layout.y_of_price(value)-crop
            panel = price_panel
        elif key == 'volume_ma':
            bars = series.snapshot.candles[layout.start:layout.stop]
            raw = [c.volume for c in bars if c.volume is not None]
            raw += _finite(values[key]['VOLUME_MA'][layout.start:layout.stop])
            maximum = max(raw, default=0) or 1
            height = layout.price[1]-layout.volume[0]-2
            sy = lambda value: layout.price[1]-value/maximum*height-crop
            panel = price_panel
        else:
            scale = _candle_scale(spec, values, layout, crop)
            if scale is None:
                return (CaseAnnotation(key, '', at, None, None, None,
                         (spec.name(language), '보조차트 공간이 부족해요' if ko else 'This sub-chart does not fit here'),
                         next(iter(palette.values())), price_panel),)
            top, bottom, low, high = scale
            sy = lambda value: bottom-(value-low)/max(high-low, 1e-12)*(bottom-top)
            panel = (left, top, right, bottom)
    else:
        # A one-bar observed snapshot has no supported detail layout here.
        if getattr(series, 'snapshot', None) is not None:
            return ()
        top, bottom, low, high = _reference_scale(series, keys, values, key, legend_top)
        sy = lambda value: bottom-(value-low)/max(high-low, 1e-12)*(bottom-top)
        x = left+(right-left)*at/max(1, len(series.closes)-1)
        panel = (left, top, right, bottom)
    out = []
    for line in spec.lines[:3]:
        raw = values[key].get(line.id, ())
        value = float(raw[at]) if len(raw) > at and raw[at] is not None else math.nan
        if not math.isfinite(value):
            continue
        y = sy(value)
        if not (left <= x <= right and panel[1]-.01 <= y <= panel[3]+.01):
            continue
        number = f'{value:,.2f}'.replace('-', '−') + ('%' if line.kind == 'percent' else '')
        caption = _COPY.get(line.id, (line.ko, line.en))[0 if ko else 1]
        out.append(CaseAnnotation(key, line.id, at, value, float(x), float(y),
                   (line.name(language)+' · '+number, caption), palette[line.id], panel))
    if not out:
        out.append(CaseAnnotation(key, '', at, None, None, None,
                   (spec.name(language), '이 날짜에 표시할 값이 없어요' if ko else 'No value is available at this date'),
                   next(iter(palette.values())), panel))
    return tuple(out)
