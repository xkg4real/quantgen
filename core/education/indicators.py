"""One aligned educational series for every selected indicator. No network/stores.

Also the catalogue of market-chart studies (STUDIES, compute_study) that
core.market.presentation.chart_svg draws and core.education.study_guide explains.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from types import MappingProxyType
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from core.quant.signals import sma, ema


@dataclass(frozen=True)
class Indicator:
    key: str
    letter: str
    color: str
    panel: str
    lines: tuple


INDICATORS = (
    Indicator('sma', 'A', '#358C73', 'price', ('SMA20', 'SMA50')),
    Indicator('ema', 'B', '#477DC2', 'price', ('EMA12', 'EMA26')),
    Indicator('rsi', 'C', '#9666B8', 'rsi', ('RSI14',)),
    Indicator('macd', 'D', '#B27628', 'macd', ('MACD', 'Signal', 'Histogram')),
    Indicator('bb', 'E', '#258895', 'price', ('BB20', 'Upper', 'Lower')),
)
BY_KEY = {i.key: i for i in INDICATORS}
CASES = {
    '2020': ('2019-09-03', '2020-12-31'),
    '2022': ('2021-09-01', '2022-12-30'),
    '2019': ('2018-09-04', '2019-12-31'),
}


@dataclass(frozen=True)
class ChartSeries:
    symbol: str
    dates: tuple
    closes: tuple
    source: str
    unit: str = 'price'
    ohlc: tuple = ()  # Optional real (open, high, low, close) bars, never inferred.
    volume: tuple = ()

    def validate(self):
        if len(self.dates) != len(self.closes) or len(self.closes) < 2:
            raise ValueError('Aligned observations required')
        if list(self.dates) != sorted(set(self.dates)):
            raise ValueError('Dates must be unique and ordered')
        if not all(math.isfinite(float(v)) and v > 0 for v in self.closes):
            raise ValueError('Finite positive reference values required')
        if self.ohlc:
            if len(self.ohlc) != len(self.closes):
                raise ValueError('OHLC length mismatch')
            for close, bar in zip(self.closes, self.ohlc):
                if len(bar) != 4 or not all(math.isfinite(float(v)) and v > 0 for v in bar):
                    raise ValueError('Invalid OHLC')
                o,h,l,c = bar
                if not l <= min(o,c) <= max(o,c) <= h or c != close:
                    raise ValueError('OHLC bounds/close mismatch')
        if self.volume and (len(self.volume) != len(self.closes) or
                not all(math.isfinite(float(v)) and v >= 0 for v in self.volume)):
            raise ValueError('Invalid observed volume')
        return self


def selection(keys):
    supplied = set(keys)
    if not supplied <= set(BY_KEY):
        raise ValueError('Unknown indicator')
    return tuple(i.key for i in INDICATORS if i.key in supplied)


def case_for(keys, requested='auto'):
    selected = selection(keys)
    if requested != 'auto':
        if requested not in CASES:
            raise ValueError('Unknown historical example')
        return requested
    if len(selected) != 1:
        return '2020'
    return '2022' if selected[0] in {'sma','ema'} else '2020'


def historical_case(keys=(), requested='auto'):
    name = case_for(keys, requested)
    root = Path(__file__).parent/'samples'
    meta = json.loads((root/'usdeur_provenance.json').read_text(encoding='utf-8'))
    raw = (root/'usdeur_daily.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest() != meta['data_sha256']:
        raise ValueError('Historical sample integrity mismatch')
    rows = [r for r in csv.DictReader(raw.decode().splitlines()) if CASES[name][0] <= r['date'] <= CASES[name][1]]
    series = ChartSeries(meta['symbol'], tuple(r['date'] for r in rows),
                         tuple(float(r['reference_rate']) for r in rows), meta['provider'], meta['unit'])
    return name, series.validate(), meta


def from_history(history):
    return ChartSeries(history.symbol, tuple(history.dates), tuple(history.closes), history.source).validate()


@lru_cache(maxsize=8)
def indicator_values(series):
    series.validate()
    px = np.asarray(series.closes, dtype=float)
    fast, slow = ema(px,12), ema(px,26)
    line = fast-slow
    signal = ema(line,9)
    # Wilder RSI matches the existing engine's terminal calculation; warmup is absent.
    rs = np.full(len(px), np.nan)
    if len(px) > 14:
        delta = np.diff(px)
        gains, losses = np.maximum(delta,0), np.maximum(-delta,0)
        gain, loss = float(gains[:14].mean()), float(losses[:14].mean())
        for i in range(14,len(px)):
            if i > 14:
                gain = (gain*13+gains[i-1])/14
                loss = (loss*13+losses[i-1])/14
            rs[i] = 100. if loss==0 else 100.-100./(1.+gain/loss)
    middle = sma(px,20)
    std = np.full(len(px), np.nan)
    for i in range(19,len(px)):
        std[i] = np.std(px[i-19:i+1],ddof=0)
    macd_line, macd_signal = line.copy(), signal.copy()
    macd_line[:25] = np.nan
    macd_signal[:33] = np.nan
    values={'SMA20':sma(px,20),'SMA50':sma(px,50),'EMA12':fast,'EMA26':slow,
            'RSI14':rs,'MACD':macd_line,'Signal':macd_signal,'Histogram':macd_line-macd_signal,
            'BB20':middle,'Upper':middle+2*std,'Lower':middle-2*std}
    # Cursor movement reuses calculations; callers cannot corrupt cached values.
    for value in values.values():value.setflags(write=False)
    return MappingProxyType(values)


def counterexamples(series, keys, *, limit=4):
    """Hindsight 5-observation counterexamples to common directional overreadings.

    This is an educational annotation, not execution/backtest or a pass/fail gate.
    """
    selected = selection(keys)
    values = indicator_values(series)
    px = np.asarray(series.closes)
    events=[]
    for key in selected:
        if key=='sma':
            spread=values['SMA20']-values['SMA50']
        elif key=='ema':
            spread=values['EMA12']-values['EMA26']
        elif key=='macd':
            spread=values['Histogram']
        else:
            spread=None
        for i in range(1,len(px)-5):
            direction=0
            if spread is not None and np.isfinite(spread[i-1:i+1]).all():
                if spread[i]>0>=spread[i-1]: direction=1
                if spread[i]<0<=spread[i-1]: direction=-1
            elif key=='rsi' and np.isfinite(values['RSI14'][i-1:i+1]).all():
                a,b=values['RSI14'][i-1:i+1]
                if a>30>=b: direction=1
                if a<70<=b: direction=-1
            elif key=='bb' and np.isfinite(values['Upper'][i-1:i+1]).all():
                if px[i]>values['Upper'][i] and px[i-1]<=values['Upper'][i-1]: direction=-1
                if px[i]<values['Lower'][i] and px[i-1]>=values['Lower'][i-1]: direction=1
            change=float(px[i+5]/px[i]-1)
            if direction and direction*change < 0:
                events.append(dict(index=i,date=series.dates[i],indicator=key,change=change,
                                   interpretation_direction=direction,horizon_observations=5))
    return sorted(events,key=lambda e:e['index'],reverse=True)[:limit]


# ---------------------------------------------------------------------------
# Market-chart studies (owner request 2026-11-11): one registry, pure numpy.
#
# `STUDIES` is the catalogue of every study the stock chart (core.market.presentation.chart_svg)
# can draw, grouped by category: its panel ('price', 'volume' or its own panel
# id), its lines, Korean and English names and default parameters.
# `compute_study(key, bars)` returns read-only float arrays aligned to the bars;
# a value that cannot be computed yet (warm-up, unknown volume, missing
# supply/demand row) is NaN, never a guess. The five education keys above
# (INDICATORS, selection, indicator_values) keep their own definitions; the
# studies 'sma', 'ema', 'rsi', 'macd' and 'bb' describe what the market chart
# draws (SMA20, EMA12/26, Wilder RSI14, MACD 12/26/9, BB20 at 2 population SD).
# Plain-language readings live in core.education.study_guide.
# ---------------------------------------------------------------------------

CATEGORIES = ('trend', 'momentum', 'volatility', 'volume', 'supply')
CATEGORY_NAMES = {'trend': ('추세', 'Trend'), 'momentum': ('모멘텀', 'Momentum'),
                  'volatility': ('변동성', 'Volatility'), 'volume': ('거래량', 'Volume'),
                  'supply': ('수급', 'Supply and demand')}
DAILY_INTERVALS = ('1d', '1w', '1M')
# What a study needs from the data: 'close'; 'ohlc' (high/low too); 'volume';
# 'ohlcv'; 'intraday' (ohlcv on intraday bars); 'kis_flows' / 'kis_shorts' (KIS
# investor-trade-by-stock-daily / daily-short-sale rows, domestic daily charts).
NEEDS = ('close', 'ohlc', 'volume', 'ohlcv', 'intraday', 'kis_flows', 'kis_shorts')
LINE_KINDS = ('price', 'index', 'percent', 'ratio', 'quantity', 'value')
LINE_STYLES = ('solid', 'dash', 'dots', 'bars')


@dataclass(frozen=True)
class StudyLine:
    id: str
    ko: str
    en: str
    kind: str = 'price'   # how a value is formatted: LINE_KINDS
    style: str = 'solid'  # how it is drawn: LINE_STYLES

    def name(self, language='ko'):
        return self.ko if language == 'ko' else self.en


@dataclass(frozen=True)
class Study:
    key: str
    category: str
    panel: str          # 'price' overlay, 'volume' overlay or its own panel id
    lines: tuple        # StudyLine, in drawing order
    ko: str
    en: str
    short: str          # compact chart label, e.g. 'Stoch 14·3·3'
    params: tuple = ()  # ((name, default), ...)
    references: tuple = ()  # conventional reference levels drawn in its panel
    bounds: tuple = ()  # fixed (low, high) panel range; () scales to the data
    needs: str = 'close'
    aliases: tuple = ()

    @property
    def defaults(self):
        return dict(self.params)

    @property
    def overlay(self):
        return self.panel in ('price', 'volume')

    def name(self, language='ko'):
        return self.ko if language == 'ko' else self.en

    def line(self, line_id):
        for line in self.lines:
            if line.id == line_id:
                return line
        raise KeyError(line_id)


def _L(id, ko, en, kind='price', style='solid'):
    return StudyLine(id, ko, en, kind, style)


STUDIES = (
    # Trend -------------------------------------------------------------------------
    Study('sma', 'trend', 'price', (_L('SMA20', '이동평균 20', 'SMA 20'),),
          '이동평균선', 'Moving average', 'SMA 20', (('period', 20),)),
    Study('ema', 'trend', 'price', (_L('EMA12', '빠른 지수평균 12', 'EMA 12'),
                                    _L('EMA26', '느린 지수평균 26', 'EMA 26', style='dash')),
          '지수이동평균', 'Exponential moving average', 'EMA 12·26', (('fast', 12), ('slow', 26))),
    Study('macd', 'trend', 'macd', (_L('MACD', 'MACD', 'MACD', 'value'),
                                    _L('SIGNAL', '신호선', 'Signal', 'value', 'dash'),
                                    _L('HISTOGRAM', '막대', 'Histogram', 'value', 'bars')),
          'MACD', 'MACD', 'MACD 12·26·9', (('fast', 12), ('slow', 26), ('signal', 9)), (0,)),
    Study('ichimoku', 'trend', 'price', (_L('TENKAN', '전환선', 'Conversion line'),
                                         _L('KIJUN', '기준선', 'Base line'),
                                         _L('SPAN_A', '선행스팬 1', 'Leading span A'),
                                         _L('SPAN_B', '선행스팬 2', 'Leading span B'),
                                         _L('CHIKOU', '후행스팬', 'Lagging span', style='dash')),
          '일목균형표', 'Ichimoku cloud', 'Ichimoku 9·26·52',
          (('conversion', 9), ('base', 26), ('span_b', 52), ('displacement', 26)), needs='ohlc'),
    Study('psar', 'trend', 'price', (_L('SAR', 'SAR 점', 'SAR dots', style='dots'),),
          '파라볼릭 SAR', 'Parabolic SAR', 'SAR 0.02·0.2', (('step', 0.02), ('maximum', 0.2)), needs='ohlc'),
    Study('adx', 'trend', 'adx', (_L('ADX', 'ADX', 'ADX', 'index'),
                                  _L('PDI', '+DI', '+DI', 'index'),
                                  _L('MDI', '−DI', '−DI', 'index', 'dash')),
          'ADX·DMI', 'ADX / DMI', 'ADX 14', (('period', 14),), (20, 25), (0, 100), 'ohlc'),
    Study('envelope', 'trend', 'price', (_L('ENV_UPPER', '엔벨로프 위 +5%', 'Envelope +5%'),
                                         _L('ENV_MIDDLE', '엔벨로프 중심 20', 'Envelope middle 20', style='dash'),
                                         _L('ENV_LOWER', '엔벨로프 아래 −5%', 'Envelope −5%')),
          '엔벨로프', 'Envelope', 'ENV 20·5%', (('period', 20), ('percent', 5.0))),
    Study('keltner', 'trend', 'price', (_L('KC_UPPER', '켈트너 위', 'Keltner upper'),
                                        _L('KC_MIDDLE', '켈트너 중심 EMA20', 'Keltner EMA 20', style='dash'),
                                        _L('KC_LOWER', '켈트너 아래', 'Keltner lower')),
          '켈트너 채널', 'Keltner channel', 'KC 20·2·10',
          (('period', 20), ('multiplier', 2.0), ('atr_period', 10)), needs='ohlc'),
    Study('donchian', 'trend', 'price', (_L('DC_UPPER', '돈치안 20봉 최고', 'Donchian 20 high'),
                                         _L('DC_MIDDLE', '돈치안 중간', 'Donchian middle', style='dash'),
                                         _L('DC_LOWER', '돈치안 20봉 최저', 'Donchian 20 low')),
          '돈치안 채널', 'Donchian channel', 'DC 20', (('period', 20),), needs='ohlc'),
    # Momentum ----------------------------------------------------------------------
    Study('rsi', 'momentum', 'rsi', (_L('RSI14', 'RSI 14', 'RSI 14', 'index'),),
          'RSI 상대강도지수', 'Relative strength index', 'RSI 14', (('period', 14),), (30, 70), (0, 100)),
    Study('stoch', 'momentum', 'stoch', (_L('STOCH_K', '%K', '%K', 'index'),
                                         _L('STOCH_D', '%D', '%D', 'index', 'dash')),
          '스토캐스틱', 'Stochastic', 'Stoch 14·3·3', (('period', 14), ('k_smooth', 3), ('d_smooth', 3)),
          (20, 80), (0, 100), 'ohlc'),
    Study('stochrsi', 'momentum', 'stochrsi', (_L('STOCHRSI_K', '%K', '%K', 'index'),
                                               _L('STOCHRSI_D', '%D', '%D', 'index', 'dash')),
          '스토캐스틱 RSI', 'Stochastic RSI', 'StochRSI 14·14·3·3',
          (('rsi_period', 14), ('period', 14), ('k_smooth', 3), ('d_smooth', 3)), (20, 80), (0, 100)),
    Study('cci', 'momentum', 'cci', (_L('CCI', 'CCI', 'CCI', 'value'),),
          'CCI 상품채널지수', 'Commodity channel index', 'CCI 20', (('period', 20), ('constant', 0.015)),
          (-100, 0, 100), needs='ohlc'),
    Study('williams', 'momentum', 'williams', (_L('WILLR', '%R', '%R', 'index'),),
          '윌리엄스 %R', 'Williams %R', '%R 14', (('period', 14),), (-80, -20), (-100, 0), 'ohlc'),
    Study('roc', 'momentum', 'roc', (_L('ROC', 'ROC %', 'ROC %', 'percent'),),
          'ROC 변화율', 'Rate of change', 'ROC 12', (('period', 12),), (0,)),
    Study('disparity', 'momentum', 'disparity', (_L('DISPARITY', '이격도', 'Disparity', 'index'),),
          '이격도', 'Disparity index', '이격도 20', (('period', 20),), (95, 100, 105)),
    Study('psychology', 'momentum', 'psychology', (_L('PSY', '심리도', 'Psychological line', 'index'),),
          '투자심리선', 'Psychological line', '심리도 10', (('period', 10),), (25, 75), (0, 100)),
    # Volatility --------------------------------------------------------------------
    Study('bb', 'volatility', 'price', (_L('BB_UPPER', '볼린저 위 밴드', 'BB upper'),
                                        _L('BB_LOWER', '볼린저 아래 밴드', 'BB lower')),
          '볼린저 밴드', 'Bollinger bands', 'BB 20·2', (('period', 20), ('deviations', 2.0)),
          aliases=('bollinger',)),
    Study('atr', 'volatility', 'atr', (_L('ATR', 'ATR', 'ATR'),),
          'ATR 평균 변동폭', 'Average true range', 'ATR 14', (('period', 14),), needs='ohlc'),
    Study('percent_b', 'volatility', 'percent_b', (_L('PERCENT_B', '%B', '%B', 'ratio'),),
          '볼린저 %B', 'Bollinger %B', '%B 20·2', (('period', 20), ('deviations', 2.0)), (0, 0.5, 1)),
    Study('bandwidth', 'volatility', 'bandwidth', (_L('BANDWIDTH', '밴드폭 %', 'Bandwidth %', 'percent'),),
          '볼린저 밴드폭', 'Bollinger bandwidth', 'BBW 20·2', (('period', 20), ('deviations', 2.0))),
    # Volume ------------------------------------------------------------------------
    Study('volume_ma', 'volume', 'volume', (_L('VOLUME_MA', '거래량 평균 20', 'Volume MA 20', 'quantity'),),
          '거래량 이동평균', 'Volume moving average', 'VOL MA 20', (('period', 20),), needs='volume'),
    Study('obv', 'volume', 'obv', (_L('OBV', 'OBV', 'OBV', 'quantity'),),
          'OBV 누적 거래량', 'On-balance volume', 'OBV', needs='ohlcv'),
    Study('mfi', 'volume', 'mfi', (_L('MFI', 'MFI', 'MFI', 'index'),),
          'MFI 자금흐름지수', 'Money flow index', 'MFI 14', (('period', 14),), (20, 80), (0, 100), 'ohlcv'),
    Study('vwap', 'volume', 'price', (_L('VWAP', 'VWAP', 'VWAP'),),
          'VWAP 거래량 가중 평균가', 'Volume-weighted average price', 'VWAP', needs='intraday'),
    # Supply and demand (domestic stocks, KIS) ------------------------------------------
    Study('investor_flow', 'supply', 'investor_flow',
          (_L('FOREIGN', '외국인', 'Foreign', 'quantity'), _L('INSTITUTION', '기관', 'Institutions', 'quantity'),
           _L('INDIVIDUAL', '개인', 'Individuals', 'quantity', 'dash')),
          '투자자별 순매수', 'Net buying by investor', '순매수 누적', references=(0,), needs='kis_flows'),
    Study('short_ratio', 'supply', 'short_ratio', (_L('SHORT_RATIO', '공매도 비중 %', 'Short-sale share %', 'percent'),),
          '공매도 비중', 'Short-sale share of volume', '공매도 %', needs='kis_shorts'),
)
STUDY_BY_KEY = {s.key: s for s in STUDIES}
_ALIASES = {alias: s.key for s in STUDIES for alias in s.aliases}


def study(key):
    """The registry entry for `key` (aliases such as 'bollinger' accepted)."""
    key = _ALIASES.get(key, key)
    if key not in STUDY_BY_KEY:
        raise ValueError(f'Unknown study {key!r}')
    return STUDY_BY_KEY[key]


def study_keys(category=None):
    """Registry keys in display order, optionally one category."""
    if category is not None and category not in CATEGORIES:
        raise ValueError('Unknown study category')
    return tuple(s.key for s in STUDIES if category is None or s.category == category)


def studies_by_category():
    """((category, (Study, ...)), ...) in display order, for a collapsible list."""
    return tuple((c, tuple(s for s in STUDIES if s.category == c)) for c in CATEGORIES)


@dataclass(frozen=True)
class Bars:
    """Observed OHLCV bars as plain tuples (hashable, so results can be cached).

    Unknown volume is NaN. `interval` uses core.market.models names; anything other
    than 1d/1w/1M counts as intraday (VWAP is computed only there).
    """
    timestamps: tuple
    open: tuple
    high: tuple
    low: tuple
    close: tuple
    volume: tuple = ()
    interval: str = '1d'

    def __post_init__(self):
        n = len(self.close)
        volume = self.volume or (math.nan,) * n
        if not all(len(seq) == n for seq in (self.timestamps, self.open, self.high, self.low, volume)):
            raise ValueError('Bars need aligned timestamps, OHLC and volume')
        object.__setattr__(self, 'timestamps', tuple(str(t) for t in self.timestamps))
        object.__setattr__(self, 'volume', tuple(math.nan if v is None else float(v) for v in volume))
        for name in ('open', 'high', 'low', 'close'):
            seq = tuple(float(v) for v in getattr(self, name))
            if not all(math.isfinite(v) for v in seq):
                raise ValueError('Bars need finite OHLC prices')
            object.__setattr__(self, name, seq)

    def __len__(self):
        return len(self.close)

    @property
    def intraday(self):
        return self.interval not in DAILY_INTERVALS

    def arrays(self):
        return tuple(np.asarray(seq, dtype=float) for seq in (self.open, self.high, self.low, self.close, self.volume))

    @property
    def dates(self):
        return tuple(str(t)[:10] for t in self.timestamps)


def bars_from_candles(candles, interval='1d'):
    """Bars from core.market Candle objects (or anything with those attributes)."""
    candles = tuple(candles)
    return Bars(tuple(c.timestamp for c in candles), tuple(float(c.open) for c in candles),
                tuple(float(c.high) for c in candles), tuple(float(c.low) for c in candles),
                tuple(float(c.close) for c in candles),
                tuple(math.nan if c.volume is None else float(c.volume) for c in candles), interval)


def bars_from_closes(closes, timestamps=None, interval='1d'):
    """Close-only bars (open = high = low = close): enough for the close-based studies."""
    closes = tuple(float(c) for c in closes)
    timestamps = tuple(timestamps) if timestamps is not None else tuple(str(i) for i in range(len(closes)))
    return Bars(timestamps, closes, closes, closes, closes, (), interval)


@dataclass(frozen=True)
class Supply:
    """KIS supply/demand rows by date (YYYY-MM-DD); unknown figures are NaN.

    flows: (date, foreign, institution, individual) net-buy quantities in shares
    (KISMarkets.investor_daily). shorts: (date, short-sale share of volume %,
    short-sale quantity) (KISMarkets.short_sale_daily).
    """
    flows: tuple = ()
    shorts: tuple = ()


def _number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return math.nan
    return value if math.isfinite(value) else math.nan


def supply_from_rows(flows=(), shorts=()):
    """Supply from KISMarkets.investor_daily / short_sale_daily rows (dicts)."""
    flow_rows = {}
    for row in flows or ():
        day = str(row.get('date') or '')[:10]
        if day:
            flow_rows[day] = (day, _number(row.get('foreign_net_qty')), _number(row.get('institution_net_qty')),
                              _number(row.get('individual_net_qty')))
    short_rows = {}
    for row in shorts or ():
        day = str(row.get('date') or '')[:10]
        if day:
            short_rows[day] = (day, _number(row.get('short_ratio_pct')), _number(row.get('short_qty')))
    return Supply(tuple(flow_rows[d] for d in sorted(flow_rows)), tuple(short_rows[d] for d in sorted(short_rows)))


# Building blocks -------------------------------------------------------------------
def _array(x):
    return np.asarray(x, dtype=float)


def rolling(x, n, reduce):
    """reduce(window, axis=1) over each n-long window ending at i; NaN in a window gives NaN."""
    x = _array(x)
    out = np.full(x.size, np.nan)
    n = int(n)
    if n < 1:
        raise ValueError('Window must be at least 1')
    if x.size >= n:
        with np.errstate(invalid='ignore'):
            out[n - 1:] = reduce(sliding_window_view(x, n), axis=1)
    return out


def _flat_windows(x, n):
    """True where the n-long window ending at i holds one repeated value (no NaN).

    The mean of 20 equal decimal prices such as 88.79 is not always exactly 88.79 in
    floating point; the studies use this to make a window with no range read exactly
    flat (standard deviation and mean deviation 0, average equal to the price)."""
    x = _array(x)
    return rolling(x, n, np.max) == rolling(x, n, np.min)


def sma_line(x, n):
    """Simple moving average over the last n values (NaN until n values exist).
    A window of one repeated value averages to exactly that value."""
    x = _array(x)
    out = rolling(x, n, np.mean)
    flat = _flat_windows(x, n)
    out[flat] = x[flat]
    return out


def _recursive(x, n, alpha):
    """Seeded with the mean of the first n values after any leading NaN, then
    out[i] = out[i-1] + alpha * (x[i] - out[i-1]); a later NaN stays NaN.
    (Written this way, and seeded with the value itself when the first n are equal,
    a run of one repeated value stays exactly that value.)"""
    x = _array(x)
    out = np.full(x.size, np.nan)
    finite = np.flatnonzero(np.isfinite(x))
    if not finite.size:
        return out
    first = int(finite[0])
    if x.size - first < n or not np.isfinite(x[first:first + n]).all():
        return out
    seed = x[first:first + n]
    out[first + n - 1] = seed[0] if (seed == seed[0]).all() else seed.mean()
    for i in range(first + n, x.size):
        out[i] = out[i - 1] + alpha * (x[i] - out[i - 1])
    return out


def ema_line(x, n):
    """Exponential moving average, alpha 2/(n+1), seeded with the first n-value mean."""
    return _recursive(x, int(n), 2.0 / (int(n) + 1))


def wilder_line(x, n):
    """Wilder smoothing (RMA): mean of the first n values, then (prev*(n-1) + x)/n."""
    return _recursive(x, int(n), 1.0 / int(n))


def typical_price(high, low, close):
    """(high + low + close) / 3; exactly the price on a bar that did not move
    ((3 × 7.1) / 3 is 7.0999… in floating point)."""
    h, l, c = _array(high), _array(low), _array(close)
    return np.where((h == l) & (l == c), c, (h + l + c) / 3)


def true_range(high, low, close):
    """max(high-low, |high-prev close|, |low-prev close|); the first bar has no previous close (NaN)."""
    h, l, c = _array(high), _array(low), _array(close)
    out = np.full(c.size, np.nan)
    if c.size > 1:
        prev = c[:-1]
        out[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - prev), np.abs(l[1:] - prev)))
    return out


def atr_line(high, low, close, n=14):
    """Wilder ATR: first value at bar n = mean of true ranges 1..n."""
    return wilder_line(true_range(high, low, close), n)


def rsi_line(close, n=14):
    """Wilder RSI as drawn by the market chart: no gains and no losses reads 50."""
    c = _array(close)
    out = np.full(c.size, np.nan)
    n = int(n)
    if c.size <= n:
        return out
    delta = np.diff(c)
    gains, losses = np.maximum(delta, 0), np.maximum(-delta, 0)
    gain, loss = float(gains[:n].mean()), float(losses[:n].mean())
    for i in range(n, c.size):
        if i > n:
            gain = (gain * (n - 1) + gains[i - 1]) / n
            loss = (loss * (n - 1) + losses[i - 1]) / n
        out[i] = 50.0 if gain == loss == 0 else 100.0 if loss == 0 else 100.0 - 100.0 / (1.0 + gain / loss)
    return out


def macd_lines(close, fast=12, slow=26, signal=9):
    """MACD = EMA fast - EMA slow; signal = EMA of MACD from its first value."""
    line = ema_line(close, fast) - ema_line(close, slow)
    sig = ema_line(line, signal)
    return {'MACD': line, 'SIGNAL': sig, 'HISTOGRAM': line - sig}


def bollinger_lines(close, n=20, k=2.0):
    """Middle SMA n and bands at k population standard deviations; a window with no
    range has no deviation (both bands on the middle)."""
    middle = sma_line(close, n)
    sd = rolling(close, n, np.std)
    sd[_flat_windows(close, n)] = 0.0
    return {'BB_MIDDLE': middle, 'BB_UPPER': middle + k * sd, 'BB_LOWER': middle - k * sd}


def _position(value, low, high, flat):
    """(value-low)/(high-low) where the range is positive; `flat` where it is zero."""
    rng = high - low
    out = np.full(np.shape(value), np.nan)
    ok = np.isfinite(value) & np.isfinite(rng)
    with np.errstate(invalid='ignore', divide='ignore'):
        out[ok] = np.where(rng[ok] > 0, (value[ok] - low[ok]) / np.where(rng[ok] > 0, rng[ok], 1), flat)
    return out


def stochastic_lines(high, low, close, n=14, k_smooth=3, d_smooth=3):
    """Lane slow stochastic: raw %K = 100(C-LLn)/(HHn-LLn), %K = SMA k_smooth, %D = SMA d_smooth.
    A window with no range reads 50 (the midpoint)."""
    hh, ll = rolling(high, n, np.max), rolling(low, n, np.min)
    raw = 100 * _position(_array(close), ll, hh, 0.5)
    k = sma_line(raw, k_smooth)
    return {'STOCH_K': k, 'STOCH_D': sma_line(k, d_smooth)}


def stoch_rsi_lines(close, rsi_period=14, n=14, k_smooth=3, d_smooth=3):
    """Stochastic of RSI: raw = 100(RSI-min n)/(max n-min n), %K = SMA k_smooth, %D = SMA d_smooth."""
    r = rsi_line(close, rsi_period)
    raw = 100 * _position(r, rolling(r, n, np.min), rolling(r, n, np.max), 0.5)
    k = sma_line(raw, k_smooth)
    return {'STOCHRSI_K': k, 'STOCHRSI_D': sma_line(k, d_smooth)}


def cci_line(high, low, close, n=20, constant=0.015):
    """(TP - SMA n of TP) / (constant * mean absolute deviation of TP); TP = (H+L+C)/3.
    No deviation in the window reads 0."""
    tp = typical_price(high, low, close)
    mean = sma_line(tp, n)
    dev = rolling(tp, n, lambda w, axis: np.mean(np.abs(w - w.mean(axis=axis, keepdims=True)), axis=axis))
    dev[_flat_windows(tp, n)] = 0.0
    out = np.full(tp.size, np.nan)
    ok = np.isfinite(dev)
    with np.errstate(invalid='ignore', divide='ignore'):
        out[ok] = np.where(dev[ok] > 0, (tp[ok] - mean[ok]) / (constant * np.where(dev[ok] > 0, dev[ok], 1)), 0.0)
    return out


def williams_r_line(high, low, close, n=14):
    """-100 (HHn - C) / (HHn - LLn); a window with no range reads -50."""
    hh, ll = rolling(high, n, np.max), rolling(low, n, np.min)
    return 100 * _position(_array(close), ll, hh, 0.5) - 100


def roc_line(close, n=12):
    """Percent change over n bars: 100 (C / C[n bars ago] - 1)."""
    c = _array(close)
    out = np.full(c.size, np.nan)
    if c.size > n:
        out[n:] = 100 * (c[n:] / c[:-n] - 1)
    return out


def disparity_line(close, n=20):
    """이격도: close / SMA n * 100 (exactly 100 when the close equals its average)."""
    return 100 * (_array(close) / sma_line(close, n))


def psychology_line(close, n=10):
    """투자심리선: percent of the last n bars that closed above the previous close."""
    c = _array(close)
    up = np.full(c.size, np.nan)
    up[1:] = (np.diff(c) > 0).astype(float)
    return 100 * rolling(up, n, np.mean)


def ichimoku_lines(high, low, close, conversion=9, base=26, span_b=52, displacement=26):
    """Ichimoku, aligned to the bar where each value is drawn.

    Conversion = (HH9 + LL9)/2, base = (HH26 + LL26)/2, leading span A = their mean,
    span B = (HH52 + LL52)/2. Leading spans are drawn `displacement` periods ahead
    counting the current bar as the first (displacement - 1 bars to the right) and
    the lagging span is the close drawn the same distance back, as in TradingView.
    The last displacement - 1 leading values lie beyond the latest bar: ichimoku_ahead.
    """
    h, l, c = _array(high), _array(low), _array(close)
    mid = lambda n: (rolling(h, n, np.max) + rolling(l, n, np.min)) / 2
    tenkan, kijun, b = mid(conversion), mid(base), mid(span_b)
    a = (tenkan + kijun) / 2
    shift = int(displacement) - 1
    span_a, span_b_line, chikou = (np.full(c.size, np.nan) for _ in range(3))
    if shift == 0:
        span_a, span_b_line, chikou = a.copy(), b.copy(), c.copy()
    elif c.size > shift:
        span_a[shift:], span_b_line[shift:] = a[:-shift], b[:-shift]
        chikou[:-shift] = c[shift:]
    return {'TENKAN': tenkan, 'KIJUN': kijun, 'SPAN_A': span_a, 'SPAN_B': span_b_line, 'CHIKOU': chikou}


def ichimoku_ahead(high, low, conversion=9, base=26, span_b=52, displacement=26):
    """Leading spans for the displacement - 1 periods after the latest bar: always
    displacement - 1 values, value k drawn k + 1 bars after the latest bar. A series
    shorter than that leaves the first periods blank (NaN) instead of shifting them."""
    h, l = _array(high), _array(low)
    mid = lambda n: (rolling(h, n, np.max) + rolling(l, n, np.min)) / 2
    a, b = (mid(conversion) + mid(base)) / 2, mid(span_b)
    shift = int(displacement) - 1

    def ahead(values):
        if shift <= 0:
            return values[:0]
        blank = np.full(max(0, shift - values.size), np.nan)
        return np.concatenate([blank, values[max(0, values.size - shift):]])
    return {'SPAN_A': ahead(a), 'SPAN_B': ahead(b)}


def parabolic_sar(high, low, step=0.02, maximum=0.2):
    """Wilder's parabolic SAR (TA-Lib's algorithm), first value at bar 1.

    The first trend is long unless bar 1's down move (prior low - low) is positive
    and larger than its up move. Long: SAR starts at bar 0's low and the extreme
    point at bar 1's high; short mirrors it. The acceleration factor starts at
    `step`, grows by `step` at each new extreme up to `maximum`, and SAR never
    enters the latest two bars' range; touching SAR flips the trend to the extreme.
    """
    return _sar_path(high, low, step, maximum)[0]


def parabolic_sar_trend(high, low, step=0.02, maximum=0.2):
    """The side parabolic_sar is following at each bar: 1.0 for an upward move (dots
    below price), -1.0 for a downward move (dots above), NaN where there is no SAR.
    Taken from the algorithm itself, so a dot that lands exactly on the close is
    still on the side of the move it belongs to."""
    return _sar_path(high, low, step, maximum)[1]


def _sar_path(high, low, step, maximum):
    h, l = _array(high), _array(low)
    n = h.size
    out, side = np.full(n, np.nan), np.full(n, np.nan)
    if n < 2:
        return out, side
    up, down = h[1] - h[0], l[0] - l[1]
    long = not (down > 0 and down > up)
    af = step
    if long:
        ep, sar = h[1], l[0]
    else:
        ep, sar = l[1], h[0]
    new_high, new_low = h[1], l[1]  # TA-Lib: bar 1 is also the first 'previous' bar
    for i in range(1, n):
        prev_high, prev_low = new_high, new_low
        new_high, new_low = h[i], l[i]
        if long:
            if new_low <= sar:
                long, sar = False, max(ep, prev_high, new_high)
                out[i] = sar
                af, ep = step, new_low
                sar = max(sar + af * (ep - sar), prev_high, new_high)
            else:
                out[i] = sar
                if new_high > ep:
                    ep, af = new_high, min(af + step, maximum)
                sar = min(sar + af * (ep - sar), prev_low, new_low)
        else:
            if new_high >= sar:
                long, sar = True, min(ep, prev_low, new_low)
                out[i] = sar
                af, ep = step, new_high
                sar = min(sar + af * (ep - sar), prev_low, new_low)
            else:
                out[i] = sar
                if new_low < ep:
                    ep, af = new_low, min(af + step, maximum)
                sar = max(sar + af * (ep - sar), prev_high, new_high)
        side[i] = 1.0 if long else -1.0
    return out, side


def adx_lines(high, low, close, n=14):
    """Wilder DMI/ADX. +DM = up move when it beats the down move and is positive (−DM
    mirrors it); +DI/−DI = 100 * Wilder(±DM)/Wilder(TR) from bar n; DX = 100|+DI−−DI|/(+DI+−DI);
    ADX = Wilder average of DX, first at bar 2n−1. No range reads 0."""
    h, l = _array(high), _array(low)
    pdm, mdm = np.full(h.size, np.nan), np.full(h.size, np.nan)
    if h.size > 1:
        upm, dnm = h[1:] - h[:-1], l[:-1] - l[1:]
        pdm[1:] = np.where((upm > dnm) & (upm > 0), upm, 0.0)
        mdm[1:] = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    tr = wilder_line(true_range(high, low, close), n)
    sp, sm = wilder_line(pdm, n), wilder_line(mdm, n)
    ok = np.isfinite(tr)
    pdi, mdi = np.full(h.size, np.nan), np.full(h.size, np.nan)
    with np.errstate(invalid='ignore', divide='ignore'):
        pdi[ok] = np.where(tr[ok] > 0, 100 * sp[ok] / np.where(tr[ok] > 0, tr[ok], 1), 0.0)
        mdi[ok] = np.where(tr[ok] > 0, 100 * sm[ok] / np.where(tr[ok] > 0, tr[ok], 1), 0.0)
        total = pdi + mdi
        dx = np.where(total > 0, 100 * np.abs(pdi - mdi) / np.where(total > 0, total, 1), 0.0)
    dx[~ok] = np.nan
    return {'ADX': wilder_line(dx, n), 'PDI': pdi, 'MDI': mdi}


def envelope_lines(close, n=20, percent=5.0):
    middle = sma_line(close, n)
    return {'ENV_UPPER': middle * (1 + percent / 100), 'ENV_MIDDLE': middle,
            'ENV_LOWER': middle * (1 - percent / 100)}


def keltner_lines(high, low, close, n=20, multiplier=2.0, atr_period=10):
    """EMA n of close ± multiplier × Wilder ATR atr_period."""
    middle, band = ema_line(close, n), multiplier * atr_line(high, low, close, atr_period)
    return {'KC_UPPER': middle + band, 'KC_MIDDLE': middle, 'KC_LOWER': middle - band}


def donchian_lines(high, low, n=20):
    """Highest high and lowest low of the last n bars (current bar included) and their midpoint."""
    upper, lower = rolling(high, n, np.max), rolling(low, n, np.min)
    return {'DC_UPPER': upper, 'DC_MIDDLE': (upper + lower) / 2, 'DC_LOWER': lower}


def obv_line(close, volume):
    """On-balance volume from 0 at the first bar: + volume on an up close, − on a down close.
    A bar with unknown volume is left blank (NaN) and adds nothing."""
    c, v = _array(close), _array(volume)
    out = np.full(c.size, np.nan)
    total = 0.0
    for i in range(c.size):
        if not math.isfinite(v[i]):
            continue
        if i:
            total += v[i] if c[i] > c[i - 1] else -v[i] if c[i] < c[i - 1] else 0.0
        out[i] = total
    return out


def mfi_line(high, low, close, volume, n=14):
    """Money flow index: 100 − 100/(1 + positive/negative flow over n bars), flow =
    typical price × volume signed by the change in typical price; first at bar n.
    A window with unknown volume is NaN; no flow either way reads 50."""
    tp = typical_price(high, low, close)
    flow = tp * _array(volume)
    pos, neg = np.full(tp.size, np.nan), np.full(tp.size, np.nan)
    if tp.size > 1:
        change = np.diff(tp)
        pos[1:] = np.where(change > 0, flow[1:], 0.0)
        neg[1:] = np.where(change < 0, flow[1:], 0.0)
        bad = ~np.isfinite(flow[1:])
        pos[1:][bad] = neg[1:][bad] = np.nan
    p, q = rolling(pos, n, np.sum), rolling(neg, n, np.sum)
    out = np.full(tp.size, np.nan)
    ok = np.isfinite(p) & np.isfinite(q)
    with np.errstate(invalid='ignore', divide='ignore'):
        out[ok] = np.where(q[ok] > 0, 100 - 100 / (1 + p[ok] / np.where(q[ok] > 0, q[ok], 1)),
                           np.where(p[ok] > 0, 100.0, 50.0))
    return out


def volume_ma_line(volume, n=20):
    return sma_line(volume, n)


_SESSION_GAP = timedelta(hours=2)
_LONG_SESSION = timedelta(hours=20)
_DAILY_BREAK = timedelta(minutes=45)


def session_start_index(timestamps):
    """For each bar, the index of the first bar of its trading session (the VWAP anchor).

    A session starts after a gap of 2 hours or more between bar times: overnight, or the
    switch between the KRX day and night futures sessions. A night session that crosses
    midnight therefore stays one session, and a lunch break (90 minutes at most on the
    supported exchanges) does not split the day. A session already 20 hours long also
    restarts at a gap of 45 minutes or more (the daily break of nearly 24-hour futures)
    or at a new calendar date (a market with no break). Timestamps that are not ISO
    times fall back to one session per calendar date."""
    stamps = [str(t) for t in timestamps]
    out = np.zeros(len(stamps), dtype=int)
    try:
        times = [datetime.fromisoformat(s) for s in stamps]
        gaps = [b - a for a, b in zip(times, times[1:])]  # mixed naive/aware times raise TypeError
    except (TypeError, ValueError):
        times = None
    start = 0
    for i in range(1, len(stamps)):
        new_date = stamps[i][:10] != stamps[i - 1][:10]
        if times is None:
            new = new_date
        else:
            gap, length = gaps[i - 1], times[i] - times[start]
            new = gap >= _SESSION_GAP or (length >= _LONG_SESSION and (gap >= _DAILY_BREAK or new_date))
        if new:
            start = i
        out[i] = start
    return out


def vwap_line(high, low, close, volume, timestamps, intraday=True):
    """Session-anchored VWAP of the typical price (H+L+C)/3, restarting at each trading
    session of the bar timestamps (session_start_index; exchange-local times as KIS reports
    them). Daily and longer bars have no session VWAP (all NaN); unknown-volume bars are blank."""
    tp = typical_price(high, low, close)
    v = _array(volume)
    out = np.full(tp.size, np.nan)
    if not intraday:
        return out
    starts = session_start_index(timestamps)
    session, pv, vol, lo, hi = None, 0.0, 0.0, math.inf, -math.inf
    for i in range(tp.size):
        if starts[i] != session:
            session, pv, vol, lo, hi = starts[i], 0.0, 0.0, math.inf, -math.inf
        if not math.isfinite(v[i]):
            continue
        pv, vol = pv + tp[i] * v[i], vol + v[i]
        if v[i] > 0:
            lo, hi = min(lo, tp[i]), max(hi, tp[i])
        if vol > 0:
            # One repeated price traded all session: the VWAP is exactly that price.
            out[i] = lo if lo == hi else pv / vol
    return out


def investor_flow_lines(dates, supply):
    """Cumulative net buying (shares) by foreign, institutional and individual investors
    from the first chart date with a KIS row; dates without a row are blank and add nothing."""
    rows = {row[0]: row for row in (supply.flows if supply else ())}
    out = {key: np.full(len(dates), np.nan) for key in ('FOREIGN', 'INSTITUTION', 'INDIVIDUAL')}
    totals = [0.0, 0.0, 0.0]
    for i, day in enumerate(dates):
        row = rows.get(str(day)[:10])
        if row is None:
            continue
        for j, key in enumerate(('FOREIGN', 'INSTITUTION', 'INDIVIDUAL')):
            if math.isfinite(row[j + 1]):
                totals[j] += row[j + 1]
                out[key][i] = totals[j]
    return out


def short_ratio_line(dates, supply):
    """Short-sale share of the day's volume (%) on chart dates with a KIS row."""
    rows = {row[0]: row[1] for row in (supply.shorts if supply else ())}
    return np.array([rows.get(str(day)[:10], math.nan) for day in dates], dtype=float)


_FORMULAS = {
    'sma': lambda b, p, s: {'SMA20': sma_line(b[3], p['period'])},
    'ema': lambda b, p, s: {'EMA12': ema_line(b[3], p['fast']), 'EMA26': ema_line(b[3], p['slow'])},
    'macd': lambda b, p, s: macd_lines(b[3], p['fast'], p['slow'], p['signal']),
    'ichimoku': lambda b, p, s: ichimoku_lines(b[1], b[2], b[3], p['conversion'], p['base'], p['span_b'],
                                               p['displacement']),
    'psar': lambda b, p, s: {'SAR': parabolic_sar(b[1], b[2], p['step'], p['maximum'])},
    'adx': lambda b, p, s: adx_lines(b[1], b[2], b[3], p['period']),
    'envelope': lambda b, p, s: envelope_lines(b[3], p['period'], p['percent']),
    'keltner': lambda b, p, s: keltner_lines(b[1], b[2], b[3], p['period'], p['multiplier'], p['atr_period']),
    'donchian': lambda b, p, s: donchian_lines(b[1], b[2], p['period']),
    'rsi': lambda b, p, s: {'RSI14': rsi_line(b[3], p['period'])},
    'stoch': lambda b, p, s: stochastic_lines(b[1], b[2], b[3], p['period'], p['k_smooth'], p['d_smooth']),
    'stochrsi': lambda b, p, s: stoch_rsi_lines(b[3], p['rsi_period'], p['period'], p['k_smooth'], p['d_smooth']),
    'cci': lambda b, p, s: {'CCI': cci_line(b[1], b[2], b[3], p['period'], p['constant'])},
    'williams': lambda b, p, s: {'WILLR': williams_r_line(b[1], b[2], b[3], p['period'])},
    'roc': lambda b, p, s: {'ROC': roc_line(b[3], p['period'])},
    'disparity': lambda b, p, s: {'DISPARITY': disparity_line(b[3], p['period'])},
    'psychology': lambda b, p, s: {'PSY': psychology_line(b[3], p['period'])},
    'bb': lambda b, p, s: {k: v for k, v in bollinger_lines(b[3], p['period'], p['deviations']).items()
                           if k != 'BB_MIDDLE'},
    'atr': lambda b, p, s: {'ATR': atr_line(b[1], b[2], b[3], p['period'])},
    'percent_b': lambda b, p, s: {'PERCENT_B': _percent_b(b[3], p['period'], p['deviations'])},
    'bandwidth': lambda b, p, s: {'BANDWIDTH': _bandwidth(b[3], p['period'], p['deviations'])},
    'volume_ma': lambda b, p, s: {'VOLUME_MA': volume_ma_line(b[4], p['period'])},
    'obv': lambda b, p, s: {'OBV': obv_line(b[3], b[4])},
    'mfi': lambda b, p, s: {'MFI': mfi_line(b[1], b[2], b[3], b[4], p['period'])},
}


def _percent_b(close, n, k):
    """(close − lower) / (upper − lower) of BB n·k; bands with no width read 0.5."""
    bands = bollinger_lines(close, n, k)
    return _position(_array(close), bands['BB_LOWER'], bands['BB_UPPER'], 0.5)


def _bandwidth(close, n, k):
    """(upper − lower) / middle × 100 of BB n·k (percent of the middle band)."""
    bands = bollinger_lines(close, n, k)
    return 100 * (bands['BB_UPPER'] - bands['BB_LOWER']) / bands['BB_MIDDLE']


@lru_cache(maxsize=256)
def _compute(key, bars, supply, params):
    spec = STUDY_BY_KEY[key]
    p = dict(params)
    arrays = bars.arrays()
    if key == 'vwap':
        values = {'VWAP': vwap_line(*arrays[1:], bars.timestamps, bars.intraday)}
    elif key == 'investor_flow':
        values = investor_flow_lines(bars.dates, supply)
    elif key == 'short_ratio':
        values = {'SHORT_RATIO': short_ratio_line(bars.dates, supply)}
    else:
        values = _FORMULAS[key](arrays, p, supply)
    values = {line.id: np.asarray(values[line.id], dtype=float) for line in spec.lines}
    for array in values.values():
        array.setflags(write=False)
    return MappingProxyType(values)


def compute_study(key, bars, *, supply=None, **params):
    """Read-only arrays {line id: values} aligned to `bars`; NaN where not computable.

    `params` override the registry defaults by name (e.g. period=20). `supply` is a
    Supply (supply_from_rows) for the 'supply' category; without it those lines are NaN.
    """
    spec = study(key)
    if not isinstance(bars, Bars):
        raise TypeError('compute_study needs Bars (bars_from_candles)')
    unknown = set(params) - set(spec.defaults)
    if unknown:
        raise ValueError(f'Unknown parameter for {spec.key}: {sorted(unknown)}')
    merged = {**spec.defaults, **params}
    for name, value in merged.items():
        whole = isinstance(spec.defaults[name], int)
        if (isinstance(value, bool) or not isinstance(value, int if whole else (int, float))
                or not math.isfinite(value) or value <= 0):
            raise ValueError(f'{spec.key}.{name} must be a positive ' + ('whole number' if whole else 'number'))
    return _compute(spec.key, bars, supply if isinstance(supply, Supply) else None, tuple(sorted(merged.items())))


def compute_studies(keys, bars, *, supply=None):
    """{key: compute_study(key, bars)} for several studies with default parameters."""
    return {study(k).key: compute_study(k, bars, supply=supply) for k in keys}


# Lines a reading needs: the lagging span is drawn in the past, so it never gates a reading.
_READING_LINES = {'ichimoku': ('TENKAN', 'KIJUN', 'SPAN_A', 'SPAN_B')}


def reading_lines(key):
    spec = study(key)
    return _READING_LINES.get(spec.key, tuple(line.id for line in spec.lines))


@lru_cache(maxsize=None)
def warmup(key):
    """0-based index of the first bar where every reading line of `key` has a value
    (default parameters, no gaps); bars needed = warmup(key) + 1."""
    spec = study(key)
    if spec.needs in ('kis_flows', 'kis_shorts'):
        return 0
    n = 400
    close = tuple(100 + 10 * math.sin(i / 5) + (i % 7) * .3 for i in range(n))
    stamps = tuple(f'2026-01-01T09:{i // 60 % 60:02d}:{i % 60:02d}' for i in range(n))
    bars = Bars(stamps, close, tuple(c + 1 for c in close), tuple(c - 1 for c in close), close,
                tuple(1000.0 + i for i in range(n)), '1m')
    values = compute_study(spec.key, bars)
    ready = np.logical_and.reduce([np.isfinite(values[line]) for line in reading_lines(spec.key)])
    return int(np.flatnonzero(ready)[0])


def availability(key, *, asset='domestic_stock', interval='1d', supply=None, has_volume=True):
    """'' when the study can be drawn for this chart, else a reason code:
    'intraday_only' (VWAP on daily or longer bars), 'needs_volume', 'domestic_daily_only'
    (KIS supply/demand on another asset or interval) or 'no_supply_data' (rows not loaded)."""
    spec = study(key)
    if spec.needs == 'intraday' and interval in DAILY_INTERVALS:
        return 'intraday_only'
    if spec.needs in ('volume', 'ohlcv', 'intraday') and not has_volume:
        return 'needs_volume'
    if spec.needs in ('kis_flows', 'kis_shorts'):
        if asset != 'domestic_stock' or interval != '1d':
            return 'domestic_daily_only'
        rows = (supply.flows if spec.needs == 'kis_flows' else supply.shorts) if isinstance(supply, Supply) else ()
        if not rows:
            return 'no_supply_data'
    return ''
