"""One aligned educational series for every selected indicator. No network/stores."""
from dataclasses import dataclass
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np

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
    return {'SMA20':sma(px,20),'SMA50':sma(px,50),'EMA12':fast,'EMA26':slow,
            'RSI14':rs,'MACD':macd_line,'Signal':macd_signal,'Histogram':macd_line-macd_signal,
            'BB20':middle,'Upper':middle+2*std,'Lower':middle-2*std}


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
