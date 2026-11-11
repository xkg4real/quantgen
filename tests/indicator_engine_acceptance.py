"""Market-chart study engine (owner request 2026-11-11): every formula against an
independent straightforward implementation or hand-computed values, the beginner
readings in both languages, and chart_svg rendering of every study with end= panning.
No network: sockets are refused for the whole module."""
from dataclasses import replace
from datetime import datetime, timedelta
import math
import re
import statistics
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import numpy as np

from core.education import indicators as E
from core.education import study_guide as G
from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot
from core.market.presentation import STUDY_COLORS, chart_svg, indicator_series, study_colors

SVG = '{http://www.w3.org/2000/svg}'
NAN = math.nan
HANGUL = re.compile('[가-힣]')
# Advice wording that must never appear (negations are written without these phrases).
ADVICE = re.compile(r'매수\s*신호|매도\s*신호|매수\s*추천|매도\s*추천|매수하세요|매도하세요|사세요|파세요|사야\s*합니다|'
                    r'팔아야|매수\s*타이밍|매도\s*타이밍|buy signal|sell signal|you should (buy|sell)|(buy|sell) now|'
                    r'time to (buy|sell)|recommend (buying|selling)|strong (buy|sell)', re.IGNORECASE)
LEGACY = {'sma', 'ema', 'bb', 'rsi', 'macd'}  # drawn by the original chart_svg code, unchanged
APPROVED = {  # the owner-approved list (2026-11-11) plus the five original studies
    'trend': {'sma', 'ema', 'macd', 'ichimoku', 'psar', 'adx', 'envelope', 'keltner', 'donchian'},
    'momentum': {'rsi', 'stoch', 'stochrsi', 'cci', 'williams', 'roc', 'disparity', 'psychology'},
    'volatility': {'bb', 'atr', 'percent_b', 'bandwidth'},
    'volume': {'obv', 'mfi', 'volume_ma', 'vwap'},
    'supply': {'investor_flow', 'short_ratio'},
}


def setUpModule():
    global _deny, _deny_requests
    _deny = patch('socket.socket.connect', side_effect=AssertionError('Network forbidden in this test'))
    _deny.start()
    _deny_requests = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden in this test'))
    _deny_requests.start()


def tearDownModule():
    _deny_requests.stop()
    _deny.stop()


# Fixtures -----------------------------------------------------------------------------
def walk(n=160, seed=7, gaps=True):
    """Deterministic OHLCV with price gaps (opens away from the previous close)."""
    rng = np.random.default_rng(seed)
    close, rows = 100.0, []
    for i in range(n):
        gap = (rng.normal(0, 2.5) if gaps and i % 17 == 9 else rng.normal(0, .4))
        o = max(1.0, close + gap)
        c = max(1.0, o + rng.normal(0, 1.2))
        h = max(o, c) + abs(rng.normal(0, .8))
        l = max(.5, min(o, c) - abs(rng.normal(0, .8)))
        rows.append((o, h, l, c, float(int(1000 + abs(rng.normal(0, 400))))))
        close = c
    return rows


def snapshot(rows, interval='1d', asset='domestic_stock', start=datetime(2026, 1, 5, 9, 0), volume=True):
    candles = []
    for i, (o, h, l, c, v) in enumerate(rows):
        if interval in ('1d', '1w', '1M'):
            stamp = (start + timedelta(days=i)).date().isoformat()
        else:  # two sessions of minute bars
            day, minute = divmod(i, 60)
            stamp = (start + timedelta(days=day, minutes=minute)).isoformat() + '+09:00'
        candles.append(Candle(stamp, o, h, l, c, v if volume else None))
    instrument = Instrument() if asset == 'domestic_stock' else Instrument('overseas_stock', 'AAPL', 'NAS')
    return MarketSnapshot(ChartRequest(instrument, interval=interval, limit=max(20, min(500, len(rows)))), tuple(candles))


def bars_of(rows, interval='1d', volume=None):
    s = snapshot(rows, interval)
    bars = E.bars_from_candles(s.candles, interval)
    if volume is not None:
        bars = replace(bars, volume=tuple(volume))
    return bars


def column(rows, k):
    return [r[k] for r in rows]


def assert_close(test, got, expected, tol=1e-9, msg=''):
    got = list(np.asarray(got, dtype=float))
    test.assertEqual(len(got), len(expected), msg)
    for i, (a, b) in enumerate(zip(got, expected)):
        if b is None or (isinstance(b, float) and math.isnan(b)):
            test.assertTrue(math.isnan(a), f'{msg} [{i}] expected NaN, got {a}')
        else:
            test.assertFalse(math.isnan(a), f'{msg} [{i}] expected {b}, got NaN')
            test.assertLessEqual(abs(a - b), tol * max(1.0, abs(b)), f'{msg} [{i}] {a} != {b}')


# Independent oracles: plain Python lists, one formula each, written from the textbook definition.
def ref_sma(xs, n):
    return [None if i + 1 < n or any(v is None or math.isnan(v) for v in xs[i + 1 - n:i + 1])
            else sum(xs[i + 1 - n:i + 1]) / n for i in range(len(xs))]


def ref_smooth(xs, n, alpha):
    out, first = [None] * len(xs), next((i for i, v in enumerate(xs) if v is not None and not math.isnan(v)), None)
    if first is None or len(xs) - first < n:
        return out
    prev = sum(xs[first:first + n]) / n
    out[first + n - 1] = prev
    for i in range(first + n, len(xs)):
        prev = prev + alpha * (xs[i] - prev)
        out[i] = prev
    return out


def ref_ema(xs, n):
    return ref_smooth(xs, n, 2 / (n + 1))


def ref_wilder(xs, n):
    return ref_smooth(xs, n, 1 / n)


def ref_tr(h, l, c):
    return [None] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]


def ref_rsi(c, n=14):
    out = [None] * len(c)
    if len(c) <= n:
        return out
    gains = [max(0.0, c[i] - c[i - 1]) for i in range(1, len(c))]
    losses = [max(0.0, c[i - 1] - c[i]) for i in range(1, len(c))]
    g, q = sum(gains[:n]) / n, sum(losses[:n]) / n
    for i in range(n, len(c)):
        if i > n:
            g, q = (g * (n - 1) + gains[i - 1]) / n, (q * (n - 1) + losses[i - 1]) / n
        out[i] = 50.0 if g == 0 and q == 0 else 100.0 if q == 0 else 100 - 100 / (1 + g / q)
    return out


def ref_position(value, low, high, flat):
    if value is None or low is None or high is None:
        return None
    return flat if high == low else (value - low) / (high - low)


def ref_stoch(h, l, c, n=14, k=3, d=3):
    raw = [None if i + 1 < n else 100 * ref_position(c[i], min(l[i + 1 - n:i + 1]), max(h[i + 1 - n:i + 1]), .5)
           for i in range(len(c))]
    slow = ref_sma(raw, k)
    return slow, ref_sma(slow, d)


def ref_stochrsi(c, rn=14, n=14, k=3, d=3):
    r = ref_rsi(c, rn)
    raw = []
    for i in range(len(c)):
        window = r[max(0, i + 1 - n):i + 1]
        raw.append(None if i + 1 < n or None in window else 100 * ref_position(r[i], min(window), max(window), .5))
    slow = ref_sma(raw, k)
    return slow, ref_sma(slow, d)


def ref_cci(h, l, c, n=20, const=.015):
    tp = [(a + b + z) / 3 for a, b, z in zip(h, l, c)]
    out = []
    for i in range(len(tp)):
        if i + 1 < n:
            out.append(None)
            continue
        w = tp[i + 1 - n:i + 1]
        mean = statistics.fmean(w)
        dev = statistics.fmean(abs(v - mean) for v in w)
        out.append(0.0 if dev == 0 else (tp[i] - mean) / (const * dev))
    return out


def ref_williams(h, l, c, n=14):
    out = []
    for i in range(len(c)):
        if i + 1 < n:
            out.append(None)
            continue
        hh, ll = max(h[i + 1 - n:i + 1]), min(l[i + 1 - n:i + 1])
        out.append(-50.0 if hh == ll else -100 * (hh - c[i]) / (hh - ll))
    return out


def ref_psar(h, l, step=.02, top=.2):
    """Wilder's parabolic SAR written bar by bar, with TA-Lib's start (bar 1, both
    'previous' extremes taken from bar 1 on the first step)."""
    n = len(h)
    out = [None] * n
    if n < 2:
        return out
    rising = not (l[0] - l[1] > 0 and l[0] - l[1] > h[1] - h[0])
    sar, extreme, af = (l[0], h[1], step) if rising else (h[0], l[1], step)
    for i in range(1, n):
        older_h, older_l = (h[1], l[1]) if i == 1 else (h[i - 1], l[i - 1])
        if rising and l[i] <= sar:          # stopped out: flip to falling at the extreme point
            rising, sar = False, max(extreme, older_h, h[i])
            out[i], af, extreme = sar, step, l[i]
            sar = max(sar + af * (extreme - sar), older_h, h[i])
        elif not rising and h[i] >= sar:    # stopped out: flip to rising
            rising, sar = True, min(extreme, older_l, l[i])
            out[i], af, extreme = sar, step, h[i]
            sar = min(sar + af * (extreme - sar), older_l, l[i])
        elif rising:
            out[i] = sar
            if h[i] > extreme:
                extreme, af = h[i], min(top, af + step)
            sar = min(sar + af * (extreme - sar), older_l, l[i])
        else:
            out[i] = sar
            if l[i] < extreme:
                extreme, af = l[i], min(top, af + step)
            sar = max(sar + af * (extreme - sar), older_h, h[i])
    return out


def ref_adx(h, l, c, n=14):
    """TA-Lib style: Wilder running sums (sum of the first n, then S - S/n + x)."""
    size = len(c)
    pdm, mdm, tr = [0.0] * size, [0.0] * size, ref_tr(h, l, c)
    for i in range(1, size):
        up, down = h[i] - h[i - 1], l[i - 1] - l[i]
        pdm[i] = up if up > down and up > 0 else 0.0
        mdm[i] = down if down > up and down > 0 else 0.0
    pdi, mdi, dx = [None] * size, [None] * size, [None] * size
    if size <= n:
        return [None] * size, pdi, mdi
    sp, sm, st = sum(pdm[1:n + 1]), sum(mdm[1:n + 1]), sum(tr[1:n + 1])
    for i in range(n, size):
        if i > n:
            sp, sm, st = sp - sp / n + pdm[i], sm - sm / n + mdm[i], st - st / n + tr[i]
        pdi[i] = 0.0 if st == 0 else 100 * sp / st
        mdi[i] = 0.0 if st == 0 else 100 * sm / st
        total = pdi[i] + mdi[i]
        dx[i] = 0.0 if total == 0 else 100 * abs(pdi[i] - mdi[i]) / total
    return ref_wilder(dx, n), pdi, mdi


def ref_obv(c, v):
    out, total = [], 0.0
    for i in range(len(c)):
        if v[i] is None or math.isnan(v[i]):
            out.append(None)
            continue
        if i:
            total += v[i] if c[i] > c[i - 1] else -v[i] if c[i] < c[i - 1] else 0
        out.append(total)
    return out


def ref_mfi(h, l, c, v, n=14):
    tp = [(a + b + z) / 3 for a, b, z in zip(h, l, c)]
    out = [None] * len(c)
    for i in range(n, len(c)):
        window = range(i + 1 - n, i + 1)
        if any(v[j] is None or math.isnan(v[j]) for j in window):
            continue
        pos = sum(tp[j] * v[j] for j in window if tp[j] > tp[j - 1])
        neg = sum(tp[j] * v[j] for j in window if tp[j] < tp[j - 1])
        out[i] = 50.0 if pos == neg == 0 else 100.0 if neg == 0 else 100 - 100 / (1 + pos / neg)
    return out


def ref_vwap(h, l, c, v, stamps):
    out, day, pv, vol = [], None, 0.0, 0.0
    for i in range(len(c)):
        if stamps[i][:10] != day:
            day, pv, vol = stamps[i][:10], 0.0, 0.0
        if v[i] is None or math.isnan(v[i]):
            out.append(None)
            continue
        pv += (h[i] + l[i] + c[i]) / 3 * v[i]
        vol += v[i]
        out.append(pv / vol if vol else None)
    return out


class RegistryTests(unittest.TestCase):
    def test_registry_lists_the_approved_studies_once_with_valid_fields(self):
        keys = [s.key for s in E.STUDIES]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual({c: set(E.study_keys(c)) for c in E.CATEGORIES}, APPROVED)
        self.assertEqual([c for c, _ in E.studies_by_category()], list(E.CATEGORIES))
        for spec in E.STUDIES:
            with self.subTest(spec.key):
                self.assertIn(spec.category, E.CATEGORIES)
                self.assertIn(spec.needs, E.NEEDS)
                self.assertTrue(spec.ko and spec.en and spec.short)
                self.assertFalse(HANGUL.search(spec.en))
                ids = [line.id for line in spec.lines]
                self.assertEqual(len(ids), len(set(ids)))
                for line in spec.lines:
                    self.assertIn(line.kind, E.LINE_KINDS)
                    self.assertIn(line.style, E.LINE_STYLES)
                    self.assertTrue(line.ko and line.en)
                self.assertEqual(spec.overlay, spec.panel in ('price', 'volume'))
                if spec.bounds:
                    self.assertTrue(all(spec.bounds[0] <= r <= spec.bounds[1] for r in spec.references))
                self.assertIs(E.study(spec.key), spec)
        self.assertIs(E.study('bollinger'), E.study('bb'))
        with self.assertRaises(ValueError):
            E.study('nope')

    def test_original_education_contract_is_unchanged(self):
        self.assertEqual([i.key for i in E.INDICATORS], ['sma', 'ema', 'rsi', 'macd', 'bb'])
        with self.assertRaises(ValueError):
            E.selection(('stoch',))
        self.assertEqual(E.selection(('bb', 'sma')), ('sma', 'bb'))

    def test_default_parameters_are_the_standard_ones(self):
        expected = {'rsi': {'period': 14}, 'stoch': {'period': 14, 'k_smooth': 3, 'd_smooth': 3},
                    'stochrsi': {'rsi_period': 14, 'period': 14, 'k_smooth': 3, 'd_smooth': 3},
                    'cci': {'period': 20, 'constant': .015}, 'williams': {'period': 14}, 'roc': {'period': 12},
                    'disparity': {'period': 20}, 'psychology': {'period': 10},
                    'ichimoku': {'conversion': 9, 'base': 26, 'span_b': 52, 'displacement': 26},
                    'psar': {'step': .02, 'maximum': .2}, 'envelope': {'period': 20, 'percent': 5.0},
                    'keltner': {'period': 20, 'multiplier': 2.0, 'atr_period': 10}, 'donchian': {'period': 20},
                    'atr': {'period': 14}, 'adx': {'period': 14}, 'percent_b': {'period': 20, 'deviations': 2.0},
                    'bandwidth': {'period': 20, 'deviations': 2.0}, 'mfi': {'period': 14}, 'volume_ma': {'period': 20},
                    'macd': {'fast': 12, 'slow': 26, 'signal': 9}}
        for key, params in expected.items():
            self.assertEqual(E.study(key).defaults, params, key)
        self.assertEqual(E.study('stoch').references, (20, 80))
        self.assertEqual(E.study('rsi').references, (30, 70))
        self.assertEqual(E.study('williams').bounds, (-100, 0))

    def test_every_drawn_line_has_a_colour_and_a_guide(self):
        for spec in E.STUDIES:
            for dark in (False, True):
                palette = study_colors(spec.key, dark)
                self.assertEqual(set(palette), {line.id for line in spec.lines}, spec.key)
            self.assertIn(spec.key, G.GUIDE)
        self.assertTrue(set(STUDY_COLORS) <= set(E.STUDY_BY_KEY))

    def test_results_are_read_only_aligned_and_parameters_validated(self):
        bars = bars_of(walk(80))
        for key in E.study_keys():
            values = E.compute_study(key, bars)
            self.assertEqual(set(values), {line.id for line in E.study(key).lines})
            for array in values.values():
                self.assertEqual(len(array), len(bars))
                with self.assertRaises(ValueError):
                    array[0] = 1.0
        self.assertIs(E.compute_study('rsi', bars), E.compute_study('rsi', bars))  # cached for cursor moves
        with self.assertRaises(ValueError):
            E.compute_study('rsi', bars, length=3)
        for bad in (0, -1, 2.5, True, float('nan')):
            with self.assertRaises(ValueError):
                E.compute_study('rsi', bars, period=bad)
        with self.assertRaises(TypeError):
            E.compute_study('rsi', [1, 2, 3])
        assert_close(self, E.compute_study('rsi', bars, period=5)['RSI14'], ref_rsi(column(walk(80), 3), 5))

    def test_no_study_reads_future_bars(self):
        rows = walk(150)
        full = bars_of(rows, '1m')
        for cut in (40, 77, 120):
            part = bars_of(rows[:cut], '1m')
            for key in E.study_keys():
                if E.study(key).needs.startswith('kis_'):
                    continue
                whole, prefix = E.compute_study(key, full), E.compute_study(key, part)
                for line in E.reading_lines(key):
                    with self.subTest(key=key, line=line, cut=cut):
                        np.testing.assert_allclose(prefix[line], whole[line][:cut], rtol=1e-12, atol=1e-9)

    def test_original_five_match_the_market_chart_series(self):
        rows = walk(120)
        snap = snapshot(rows)
        legacy = indicator_series(snap)
        bars = E.bars_from_candles(snap.candles)
        pairs = {('sma', 'SMA20'): 'SMA20', ('ema', 'EMA12'): 'EMA12', ('ema', 'EMA26'): 'EMA26',
                 ('rsi', 'RSI14'): 'RSI14', ('macd', 'MACD'): 'MACD', ('macd', 'SIGNAL'): 'SIGNAL',
                 ('macd', 'HISTOGRAM'): 'HISTOGRAM', ('bb', 'BB_UPPER'): 'BB_UPPER', ('bb', 'BB_LOWER'): 'BB_LOWER'}
        for (key, line), old in pairs.items():
            assert_close(self, E.compute_study(key, bars)[line], legacy[old], 1e-11, f'{key}.{line}')

    def test_warmup_counts_and_availability(self):
        self.assertEqual({k: E.warmup(k) for k in ('rsi', 'stoch', 'stochrsi', 'adx', 'macd', 'ichimoku', 'psar', 'roc')},
                         {'rsi': 14, 'stoch': 17, 'stochrsi': 31, 'adx': 27, 'macd': 33, 'ichimoku': 76, 'psar': 1,
                          'roc': 12})
        supply = E.supply_from_rows([{'date': '2026-01-05', 'foreign_net_qty': 1}], ())
        self.assertEqual(E.availability('vwap', interval='1d'), 'intraday_only')
        self.assertEqual(E.availability('vwap', interval='5m'), '')
        self.assertEqual(E.availability('obv', has_volume=False), 'needs_volume')
        self.assertEqual(E.availability('investor_flow', asset='overseas_stock'), 'domestic_daily_only')
        self.assertEqual(E.availability('investor_flow', interval='5m', supply=supply), 'domestic_daily_only')
        self.assertEqual(E.availability('investor_flow'), 'no_supply_data')
        self.assertEqual(E.availability('investor_flow', supply=supply), '')
        self.assertEqual(E.availability('short_ratio', supply=supply), 'no_supply_data')
        for code in ('intraday_only', 'needs_volume', 'domestic_daily_only', 'no_supply_data'):
            self.assertTrue(HANGUL.search(G.availability_text(code, 'ko')))
            self.assertFalse(HANGUL.search(G.availability_text(code, 'en')))


class FormulaTests(unittest.TestCase):
    """Each study against its independent oracle on gapped random-walk data."""

    def setUp(self):
        self.rows = walk(160)
        self.bars = bars_of(self.rows)
        self.o, self.h, self.l, self.c, self.v = (column(self.rows, k) for k in range(5))

    def values(self, key, **params):
        return E.compute_study(key, self.bars, **params)

    def test_averages_and_bands(self):
        assert_close(self, self.values('sma')['SMA20'], ref_sma(self.c, 20))
        assert_close(self, self.values('ema')['EMA12'], ref_ema(self.c, 12))
        assert_close(self, self.values('ema')['EMA26'], ref_ema(self.c, 26))
        mid = ref_sma(self.c, 20)
        env = self.values('envelope')
        assert_close(self, env['ENV_UPPER'], [None if m is None else m * 1.05 for m in mid])
        assert_close(self, env['ENV_LOWER'], [None if m is None else m * .95 for m in mid])
        sd = [None if i < 19 else statistics.pstdev(self.c[i - 19:i + 1]) for i in range(len(self.c))]
        upper = [None if m is None else m + 2 * s for m, s in zip(mid, sd)]
        lower = [None if m is None else m - 2 * s for m, s in zip(mid, sd)]
        assert_close(self, self.values('bb')['BB_UPPER'], upper, 1e-9)
        assert_close(self, self.values('percent_b')['PERCENT_B'],
                     [None if u is None else (c - lo) / (u - lo) for c, u, lo in zip(self.c, upper, lower)], 1e-9)
        assert_close(self, self.values('bandwidth')['BANDWIDTH'],
                     [None if u is None else (u - lo) / m * 100 for u, lo, m in zip(upper, lower, mid)], 1e-9)
        atr10 = ref_wilder(ref_tr(self.h, self.l, self.c), 10)
        mid_e = ref_ema(self.c, 20)
        kc = self.values('keltner')
        assert_close(self, kc['KC_MIDDLE'], mid_e)
        assert_close(self, kc['KC_UPPER'], [None if m is None or a is None else m + 2 * a for m, a in zip(mid_e, atr10)])
        assert_close(self, kc['KC_LOWER'], [None if m is None or a is None else m - 2 * a for m, a in zip(mid_e, atr10)])
        dc = self.values('donchian')
        hh = [None if i < 19 else max(self.h[i - 19:i + 1]) for i in range(len(self.c))]
        ll = [None if i < 19 else min(self.l[i - 19:i + 1]) for i in range(len(self.c))]
        assert_close(self, dc['DC_UPPER'], hh)
        assert_close(self, dc['DC_LOWER'], ll)
        assert_close(self, dc['DC_MIDDLE'], [None if a is None else (a + b) / 2 for a, b in zip(hh, ll)])

    def test_wilder_family_rsi_atr_adx(self):
        assert_close(self, self.values('rsi')['RSI14'], ref_rsi(self.c))
        tr = ref_tr(self.h, self.l, self.c)
        assert_close(self, self.values('atr')['ATR'], ref_wilder(tr, 14), 1e-9)
        adx, pdi, mdi = ref_adx(self.h, self.l, self.c)
        got = self.values('adx')
        assert_close(self, got['PDI'], pdi, 1e-9, 'PDI')
        assert_close(self, got['MDI'], mdi, 1e-9, 'MDI')
        assert_close(self, got['ADX'], adx, 1e-9, 'ADX')
        # Gaps count: true range reaches back to the previous close.
        gap_bars = [i for i in range(1, len(self.c)) if abs(self.o[i] - self.c[i - 1]) > 2]
        self.assertTrue(gap_bars)
        self.assertTrue(any(tr[i] > self.h[i] - self.l[i] + 1e-9 for i in gap_bars))

    def test_macd(self):
        line = [None if a is None or b is None else a - b for a, b in zip(ref_ema(self.c, 12), ref_ema(self.c, 26))]
        signal = ref_ema(line, 9)
        got = self.values('macd')
        assert_close(self, got['MACD'], line)
        assert_close(self, got['SIGNAL'], signal)
        assert_close(self, got['HISTOGRAM'], [None if s is None else m - s for m, s in zip(line, signal)])

    def test_oscillators(self):
        k, d = ref_stoch(self.h, self.l, self.c)
        assert_close(self, self.values('stoch')['STOCH_K'], k)
        assert_close(self, self.values('stoch')['STOCH_D'], d)
        k, d = ref_stochrsi(self.c)
        assert_close(self, self.values('stochrsi')['STOCHRSI_K'], k, 1e-8)
        assert_close(self, self.values('stochrsi')['STOCHRSI_D'], d, 1e-8)
        assert_close(self, self.values('cci')['CCI'], ref_cci(self.h, self.l, self.c), 1e-9)
        assert_close(self, self.values('williams')['WILLR'], ref_williams(self.h, self.l, self.c))
        assert_close(self, self.values('roc')['ROC'],
                     [None if i < 12 else 100 * (self.c[i] / self.c[i - 12] - 1) for i in range(len(self.c))])
        mid = ref_sma(self.c, 20)
        assert_close(self, self.values('disparity')['DISPARITY'],
                     [None if m is None else c / m * 100 for c, m in zip(self.c, mid)])
        up = [None] + [1.0 if self.c[i] > self.c[i - 1] else 0.0 for i in range(1, len(self.c))]
        assert_close(self, self.values('psychology')['PSY'],
                     [None if s is None else s * 100 for s in ref_sma(up, 10)])

    def test_ichimoku_alignment(self):
        got = self.values('ichimoku')
        mid = lambda n, i: (max(self.h[i - n + 1:i + 1]) + min(self.l[i - n + 1:i + 1])) / 2 if i >= n - 1 else None
        size = len(self.c)
        tenkan = [mid(9, i) for i in range(size)]
        kijun = [mid(26, i) for i in range(size)]
        span_a_raw = [None if b is None else (a + b) / 2 for a, b in zip(tenkan, kijun)]
        span_b_raw = [mid(52, i) for i in range(size)]
        assert_close(self, got['TENKAN'], tenkan)
        assert_close(self, got['KIJUN'], kijun)
        # 26 periods ahead counting the current bar: drawn 25 bars to the right.
        assert_close(self, got['SPAN_A'], [None] * 25 + span_a_raw[:-25])
        assert_close(self, got['SPAN_B'], [None] * 25 + span_b_raw[:-25])
        assert_close(self, got['CHIKOU'], self.c[25:] + [None] * 25)
        ahead = E.ichimoku_ahead(self.h, self.l)
        assert_close(self, ahead['SPAN_A'], span_a_raw[-25:])
        assert_close(self, ahead['SPAN_B'], span_b_raw[-25:])

    def test_parabolic_sar(self):
        assert_close(self, self.values('psar')['SAR'], ref_psar(self.h, self.l))
        sar = self.values('psar')['SAR']
        for i in range(2, len(self.c)):  # SAR sits outside the bar it is drawn on
            self.assertTrue(sar[i] <= self.l[i] + 1e-9 or sar[i] >= self.h[i] - 1e-9, i)

    def test_volume_studies(self):
        volume = list(self.v)
        volume[50] = NAN  # an unreported bar
        bars = replace(self.bars, volume=tuple(volume))
        assert_close(self, E.compute_study('obv', bars)['OBV'], ref_obv(self.c, volume))
        assert_close(self, E.compute_study('mfi', bars)['MFI'], ref_mfi(self.h, self.l, self.c, volume), 1e-9)
        assert_close(self, E.compute_study('volume_ma', bars)['VOLUME_MA'], ref_sma(volume, 20))
        self.assertTrue(np.isnan(E.compute_study('vwap', bars)['VWAP']).all())  # daily bars: no session VWAP
        minute = bars_of(self.rows[:120], '1m', volume=volume[:120])
        stamps = minute.timestamps
        assert_close(self, E.compute_study('vwap', minute)['VWAP'],
                     ref_vwap(self.h[:120], self.l[:120], self.c[:120], volume[:120], stamps), 1e-12)
        self.assertNotEqual(stamps[59][:10], stamps[60][:10])
        tp60 = (self.h[60] + self.l[60] + self.c[60]) / 3
        self.assertAlmostEqual(E.compute_study('vwap', minute)['VWAP'][60], tp60)  # restarts each session


class HandComputedTests(unittest.TestCase):
    """Small fixtures worked out by hand (values in the comments)."""

    def bars(self, highs, lows, closes, volume=(), interval='1d', stamps=None):
        stamps = stamps or tuple(f'2026-01-{i + 1:02d}' for i in range(len(closes)))
        return E.Bars(tuple(stamps), tuple(closes), tuple(highs), tuple(lows), tuple(closes), tuple(volume), interval)

    def test_psar_by_hand(self):
        b = self.bars((10, 11, 12, 12.5, 11, 10), (9, 9.5, 10.5, 11, 9, 8.5), (9.5, 10.5, 11.5, 12, 9.5, 9))
        # Long from bar 1: SAR 9 (bar 0 low); 9 + .02(11-9) = 9.04; EP 12, AF .04: 9.04 + .04(12-9.04) = 9.1584;
        # bar 4's low 9 touches 9.358896, so SAR flips to the extreme 12.5 and stays above the last two highs.
        assert_close(self, E.compute_study('psar', b)['SAR'], [NAN, 9.0, 9.04, 9.1584, 12.5, 12.5], 1e-12)

    def test_stochastic_williams_cci_by_hand(self):
        b = self.bars((3, 4, 5, 6), (1, 2, 3, 4), (2, 3, 5, 4))
        # Window 3: bar 2 range 1..5, close 5 -> 100; bar 3 range 2..6, close 4 -> 50; %D(2) = 75.
        st = E.compute_study('stoch', b, period=3, k_smooth=1, d_smooth=2)
        assert_close(self, st['STOCH_K'], [NAN, NAN, 100.0, 50.0])
        assert_close(self, st['STOCH_D'], [NAN, NAN, NAN, 75.0])
        assert_close(self, E.compute_study('williams', b, period=3)['WILLR'], [NAN, NAN, 0.0, -50.0])
        # Typical prices 2, 3, 13/3, 14/3; window 3 at bar 2: mean 28/9, mean deviation 22/27.
        tp, mean, dev = 13 / 3, 28 / 9, 22 / 27
        self.assertAlmostEqual(E.compute_study('cci', b, period=3)['CCI'][2], (tp - mean) / (.015 * dev))

    def test_rate_disparity_psychology_obv_by_hand(self):
        b = self.bars((100, 110, 121, 121, 133.1), (100, 110, 121, 121, 133.1), (100, 110, 121, 121, 133.1),
                      (100, 200, 300, 400, 500))
        assert_close(self, E.compute_study('roc', b, period=1)['ROC'], [NAN, 10, 10, 0, 10], 1e-12)
        assert_close(self, E.compute_study('disparity', b, period=2)['DISPARITY'],
                     [NAN, 110 / 105 * 100, 121 / 115.5 * 100, 100, 133.1 / 127.05 * 100], 1e-12)
        # Up closes: -, yes, yes, no (flat), yes -> 3-bar share at bar 3 = 2/3, bar 4 = 2/3.
        assert_close(self, E.compute_study('psychology', b, period=3)['PSY'], [NAN, NAN, NAN, 200 / 3, 200 / 3], 1e-12)
        assert_close(self, E.compute_study('obv', b)['OBV'], [0, 200, 500, 500, 1000])

    def test_atr_mfi_vwap_by_hand(self):
        b = self.bars((11, 13, 12), (9, 10, 8), (10, 12, 9), (10, 20, 30))
        # TR: -, max(3, 3, 0) = 3, max(4, 0, 4) = 4; ATR(2) at bar 2 = 3.5.
        assert_close(self, E.compute_study('atr', b, period=2)['ATR'], [NAN, NAN, 3.5])
        # TP 10, 35/3, 29/3: bar 1 up (flow 35/3*20), bar 2 down (29/3*30) -> MFI = 100 - 100/(1 + 700/870).
        self.assertAlmostEqual(E.compute_study('mfi', b, period=2)['MFI'][2], 100 - 100 / (1 + (700 / 3) / 290))
        stamps = ('2026-11-02T09:00:00+09:00', '2026-11-02T09:01:00+09:00', '2026-11-03T09:00:00+09:00')
        minute = self.bars((11, 13, 12), (9, 10, 8), (10, 12, 9), (10, 20, 30), '1m', stamps)
        assert_close(self, E.compute_study('vwap', minute)['VWAP'], [10.0, (100 + 700 / 3) / 30, 29 / 3])

    def test_wilder_rsi_reference_and_adx_trend(self):
        closes = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
        b = E.bars_from_closes(closes)
        self.assertAlmostEqual(E.compute_study('rsi', b)['RSI14'][14], 70.464135, places=5)
        steady = E.bars_from_closes([100 + i for i in range(40)])
        adx = E.compute_study('adx', E.Bars(steady.timestamps, steady.close, tuple(c + 1 for c in steady.close),
                                            tuple(c - 1 for c in steady.close), steady.close))
        self.assertAlmostEqual(adx['PDI'][-1], 50)  # +DM 1 per bar over a true range of 2 (high minus previous close)
        self.assertEqual(adx['MDI'][-1], 0)
        self.assertAlmostEqual(adx['ADX'][-1], 100)
        # Equal up and down moves (a widening range) count for neither side: +DI = −DI = 0, ADX 0.
        widening = E.compute_study('adx', E.Bars(tuple(str(i) for i in range(40)), (100.0,) * 40,
                                                 tuple(101.0 + i for i in range(40)), tuple(99.0 - i for i in range(40)),
                                                 (100.0,) * 40))
        self.assertEqual((widening['PDI'][-1], widening['MDI'][-1], widening['ADX'][-1]), (0.0, 0.0, 0.0))

    def test_flat_prices_read_midpoints_not_errors(self):
        flat = E.Bars(tuple(f'2026-01-{i + 1:02d}' for i in range(80)), (100.0,) * 80, (100.0,) * 80, (100.0,) * 80,
                      (100.0,) * 80, (500.0,) * 80)
        last = {key: {line: float(v[-1]) for line, v in E.compute_study(key, flat).items()} for key in E.study_keys()
                if not E.study(key).needs.startswith('kis_') and key != 'vwap'}
        expected = {'rsi': {'RSI14': 50}, 'stoch': {'STOCH_K': 50, 'STOCH_D': 50},
                    'stochrsi': {'STOCHRSI_K': 50, 'STOCHRSI_D': 50}, 'williams': {'WILLR': -50}, 'cci': {'CCI': 0},
                    'adx': {'ADX': 0, 'PDI': 0, 'MDI': 0}, 'atr': {'ATR': 0}, 'percent_b': {'PERCENT_B': .5},
                    'bandwidth': {'BANDWIDTH': 0}, 'disparity': {'DISPARITY': 100}, 'psychology': {'PSY': 0},
                    'roc': {'ROC': 0}, 'mfi': {'MFI': 50}, 'obv': {'OBV': 0}, 'macd': {'MACD': 0, 'SIGNAL': 0, 'HISTOGRAM': 0},
                    'envelope': {'ENV_UPPER': 105, 'ENV_MIDDLE': 100, 'ENV_LOWER': 95},
                    'keltner': {'KC_UPPER': 100, 'KC_MIDDLE': 100, 'KC_LOWER': 100}}
        for key, lines in expected.items():
            for line, value in lines.items():
                self.assertAlmostEqual(last[key][line], value, msg=f'{key}.{line}')
        self.assertTrue(all(math.isfinite(v) for lines in last.values() for k, v in lines.items() if k != 'CHIKOU'))

    def test_short_and_single_bar_series_are_nan_not_errors(self):
        for rows in (walk(1), walk(5), walk(13)):
            bars = bars_of(rows)
            for key in E.study_keys():
                values = E.compute_study(key, bars)
                self.assertTrue(all(len(v) == len(rows) for v in values.values()))
            self.assertTrue(np.isnan(E.compute_study('rsi', bars)['RSI14']).all())
            self.assertTrue(np.isnan(E.compute_study('ichimoku', bars)['SPAN_B']).all())
        self.assertEqual(float(E.compute_study('obv', bars_of(walk(1)))['OBV'][0]), 0.0)

    def test_supply_rows_align_to_chart_dates(self):
        bars = bars_of(walk(6))
        dates = bars.dates
        supply = E.supply_from_rows(
            [{'date': dates[1], 'foreign_net_qty': 100, 'institution_net_qty': -40, 'individual_net_qty': -60},
             {'date': dates[3], 'foreign_net_qty': -30, 'institution_net_qty': None, 'individual_net_qty': 30},
             {'date': '2025-12-31', 'foreign_net_qty': 999}],  # outside the chart: ignored
            [{'date': dates[2], 'short_ratio_pct': 4.5}, {'date': dates[5], 'short_ratio_pct': 'x'}])
        flows = E.compute_study('investor_flow', bars, supply=supply)
        assert_close(self, flows['FOREIGN'], [NAN, 100, NAN, 70, NAN, NAN])
        assert_close(self, flows['INSTITUTION'], [NAN, -40, NAN, NAN, NAN, NAN])
        assert_close(self, flows['INDIVIDUAL'], [NAN, -60, NAN, -30, NAN, NAN])
        assert_close(self, E.compute_study('short_ratio', bars, supply=supply)['SHORT_RATIO'], [NAN, NAN, 4.5, NAN, NAN, NAN])
        self.assertTrue(np.isnan(E.compute_study('investor_flow', bars)['FOREIGN']).all())


class GuideTests(unittest.TestCase):
    def setUp(self):
        rows = walk(200, seed=11)
        self.bars = bars_of(rows)
        self.minute = bars_of(rows[:120], '1m')
        dates = self.bars.dates
        self.supply = E.supply_from_rows(
            [{'date': d, 'foreign_net_qty': (i * 1371) % 50000 - 25000, 'institution_net_qty': (i * 917) % 30000 - 15000,
              'individual_net_qty': 4000 - i * 100} for i, d in enumerate(dates[-40:])],
            [{'date': d, 'short_ratio_pct': 2 + (i % 7) * .5, 'short_qty': 1000 + i} for i, d in enumerate(dates[-40:])])

    def test_every_study_has_a_plain_guide_in_both_languages(self):
        for key in E.study_keys():
            ko, en = G.guide(key, 'ko'), G.guide(key, 'en')
            with self.subTest(key):
                for field in G.FIELDS:
                    self.assertTrue(HANGUL.search(getattr(ko, field)), field)
                    self.assertFalse(HANGUL.search(getattr(en, field)), field)
                    for text in (getattr(ko, field), getattr(en, field)):
                        self.assertIsNone(ADVICE.search(text), text)
                        self.assertLess(len(text), 260, text)
                self.assertEqual(len({ko.what, ko.how, ko.caution}), 3)
                self.assertEqual(ko.category, E.CATEGORY_NAMES[E.study(key).category][0])
                self.assertEqual(ko.name, E.study(key).ko)
        self.assertEqual(G.params_text('stoch'), '기간 14 · %K 평균 3 · %D 평균 3')
        self.assertEqual(G.params_text('psar', 'en'), 'step 0.02 · maximum 0.2')
        self.assertIn('예측', G.disclaimer('ko'))
        self.assertIn('recommend', G.disclaimer('en'))

    def readings(self, key):
        for language in ('ko', 'en'):
            for bars in (self.bars, self.minute):
                for index in (0, 5, 30, 90, -40, -1):
                    yield language, bars, index, G.study_reading(key, bars, index, language=language, supply=self.supply)

    def test_readings_are_plain_language_without_advice_or_missing_numbers(self):
        for key in E.study_keys():
            for language, bars, index, text in self.readings(key):
                with self.subTest(key=key, language=language, interval=bars.interval, index=index):
                    self.assertTrue(text.strip())
                    self.assertIsNone(ADVICE.search(text), text)
                    self.assertNotRegex(text.lower(), r'\bnan\b|\bnone\b|\binf\b|\{|\}')
                    if language == 'ko':
                        self.assertTrue(HANGUL.search(text), text)
                    else:
                        self.assertFalse(HANGUL.search(text), text)

    def test_readings_name_conventions_and_say_what_a_value_means(self):
        rising = E.bars_from_closes([100 * 1.01 ** i for i in range(40)])
        falling = E.bars_from_closes([100 * .99 ** i for i in range(40)])
        hot = G.study_reading('rsi', rising, -1)
        self.assertRegex(hot, r'^RSI 100\.0: 최근 14일 동안 오른 폭이 내린 폭보다 훨씬 컸습니다')
        self.assertIn('과매수 구간으로 부르는 관례', hot)
        self.assertIn("팔라는 뜻이 아니라 '최근 많이 올랐다'는 뜻입니다", hot)
        cold = G.study_reading('rsi', falling, -1)
        self.assertIn('과매도', cold)
        self.assertIn('사라는 뜻이 아니라', cold)
        self.assertIn("not 'sell'", G.study_reading('rsi', rising, -1, language='en'))
        self.assertIn('conventionally', G.study_reading('rsi', rising, -1, language='en'))
        # Owner 2026-11-11 (R-D9-2): no '봉' in Korean; minute charts count their own periods.
        self.assertIn('최근 14개 5분 구간', G.study_reading('rsi', replace(rising, interval='5m'), -1))
        self.assertIn('최근 14주', G.study_reading('rsi', replace(rising, interval='1w'), -1))
        self.assertIn('관례', G.study_reading('stoch', rising, -1))
        self.assertIn('이격도', G.study_reading('disparity', rising, -1))
        self.assertIn('10일 중 10일이 전날보다 올랐습니다', G.study_reading('psychology', rising, -1))
        self.assertIn('10주 중 10주가 전주보다', G.study_reading('psychology', replace(rising, interval='1w'), -1))
        self.assertIn('구름 위', G.study_reading('ichimoku', E.bars_from_closes([100 * 1.01 ** i for i in range(90)]), -1))

    def test_warmup_unavailable_and_missing_data_say_why(self):
        self.assertIn('최소 15일의 자료가 필요합니다', G.study_reading('rsi', self.bars, 3))   # R-D9-2: no '봉'
        self.assertIn('at least 77 bars', G.study_reading('ichimoku', self.bars, 10, language='en'))
        self.assertEqual(G.study_reading('vwap', self.bars, -1), G.availability_text('intraday_only', 'ko'))
        self.assertEqual(G.study_reading('investor_flow', self.bars, -1), G.availability_text('no_supply_data', 'ko'))
        self.assertEqual(G.study_reading('short_ratio', self.minute, -1, supply=self.supply),
                         G.availability_text('domestic_daily_only', 'ko'))
        self.assertIn('자료가 없습니다', G.study_reading('investor_flow', self.bars, 10, supply=self.supply))
        unknown = replace(self.bars, volume=tuple(NAN if i == 199 else v for i, v in enumerate(self.bars.volume)))
        self.assertIn('거래량', G.study_reading('volume_ma', unknown, -1))
        self.assertIn('거래량이 없어', G.study_reading('obv', unknown, -1))
        flows = G.study_reading('investor_flow', self.bars, -1, supply=self.supply)
        self.assertIn('이날 순매수: 외국인', flows)
        self.assertIn('최근 20거래일 합계', flows)
        self.assertIn('최근 20거래일 평균', G.study_reading('short_ratio', self.bars, -1, supply=self.supply))

    def test_readout_formats_every_line(self):
        for key in E.study_keys():
            pairs = G.line_readout(key, self.bars, -1, supply=self.supply)
            self.assertEqual([name for name, _ in pairs], [line.ko for line in E.study(key).lines])
            for _, text in pairs:
                self.assertNotIn('nan', text.lower())
        self.assertEqual(G.format_value('quantity', -153000, 'ko'), '−15.3만')
        self.assertEqual(G.format_value('quantity', 2.5e8, 'ko'), '2.5억')
        self.assertEqual(G.format_value('percent', 3.456), '3.5%')
        self.assertEqual(G.format_value('price', 71523.456), '71,523.46')
        self.assertEqual(G.format_value('index', NAN), '—')


def lum(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]


def contrast(a, b):
    low, high = sorted((lum(a), lum(b)))
    return (high + .05) / (low + .05)


NUMERIC = ('x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'width', 'height')


class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.rows = walk(180, seed=3)
        self.snap = snapshot(self.rows)
        dates = [c.timestamp[:10] for c in self.snap.candles]
        self.supply = {'flows': [{'date': d, 'foreign_net_qty': 1000 - i * 37, 'institution_net_qty': i * 11 - 200,
                                  'individual_net_qty': 300 - i} for i, d in enumerate(dates[-50:])],
                       'shorts': [{'date': d, 'short_ratio_pct': 1 + i % 5} for i, d in enumerate(dates[-50:])]}

    def check(self, svg, dark):
        root = ET.fromstring(svg)
        background = root.find(SVG + 'rect').attrib['fill']
        for node in root.iter():
            for name in NUMERIC:
                if name in node.attrib:
                    self.assertTrue(math.isfinite(float(node.attrib[name])), (node.tag, name))
            if 'points' in node.attrib:
                for pair in node.attrib['points'].split():
                    self.assertTrue(all(math.isfinite(float(v)) for v in pair.split(',')))
        for text in root.iter(SVG + 'text'):
            self.assertEqual(text.attrib['font-family'], 'QG Interface')
            self.assertGreaterEqual(float(text.attrib['font-size']), 12)
            self.assertNotRegex((text.text or '').lower(), r'\bnan\b|\binf\b|none')
            self.assertGreaterEqual(contrast(text.attrib['fill'], background), 4.5, text.text)
        for mark in [*root.iter(SVG + 'polyline'), *root.iter(SVG + 'circle')]:
            color = mark.attrib.get('stroke') or mark.attrib['fill']
            self.assertGreaterEqual(contrast(color, background), 3, color)
        return root

    def test_every_study_renders_alone_in_both_themes_languages_and_widths(self):
        for key in E.study_keys():
            spec = E.study(key)
            for dark in (False, True):
                for width in (320, 1000):
                    for language in ('ko', 'en'):
                        with self.subTest(key=key, dark=dark, width=width, language=language):
                            base = ET.fromstring(chart_svg(self.snap, indicators=(), width=width, dark=dark,
                                                           language=language))
                            svg = chart_svg(self.snap, indicators=(key,), width=width, dark=dark, language=language,
                                            supply=self.supply)
                            root = self.check(svg, dark)
                            palette = study_colors(key, dark)
                            marks = [m for m in [*root.iter(SVG + 'polyline'), *root.iter(SVG + 'circle')]
                                     if (m.attrib.get('stroke') or m.attrib.get('fill')) in palette.values()]
                            if key != 'vwap':  # daily chart: VWAP is listed as intraday only
                                self.assertTrue(marks, 'study lines are drawn')
                            added = int(root.attrib['height']) - int(base.attrib['height'])
                            if not spec.overlay:
                                self.assertGreaterEqual(added, 112)
                            texts = ' '.join(t.text or '' for t in root.iter(SVG + 'text'))
                            if key in LEGACY:  # the original renderer keeps its own labels
                                continue
                            if not spec.overlay:
                                self.assertIn(spec.name(language), texts)
                            for line in spec.lines if spec.panel == 'price' and key != 'vwap' else ():
                                self.assertIn(line.name(language), texts)

    def test_everything_at_once_keeps_rows_apart_and_labels_inside(self):
        keys = E.study_keys()
        for width in (320, 640, 1400):
            for dark in (False, True):
                svg = chart_svg(self.snap, indicators=keys, width=width, dark=dark, language='ko', supply=self.supply,
                                cursor=150)
                root = self.check(svg, dark)
                self.assertEqual(root.attrib['width'], str(width))
                for text in root.iter(SVG + 'text'):
                    if text.attrib.get('text-anchor', 'start') == 'start':
                        self.assertLessEqual(float(text.attrib['x']), width, text.text)
                titles = [t for t in root.iter(SVG + 'text') if t.text and t.text.startswith(('스토캐스틱 14', 'ADX·DMI'))]
                self.assertEqual(len(titles), 2)

    def test_reference_lines_and_cursor_values_in_lower_panels(self):
        svg = chart_svg(self.snap, indicators=('stoch',), cursor=120, language='ko')
        root = ET.fromstring(svg)
        dashed = [l for l in root.iter(SVG + 'line') if l.attrib.get('stroke-dasharray') == '3 4'
                  and l.attrib['stroke'] == '#5F6D66']
        self.assertEqual(len(dashed), 2)  # 20 and 80
        labels = {t.text for t in root.iter(SVG + 'text')}
        self.assertTrue({'0', '20', '80', '100'} <= labels)
        k = E.compute_study('stoch', E.bars_from_candles(self.snap.candles))['STOCH_K'][120]
        self.assertIn(f'%K {k:.1f}', labels)
        cci = ET.fromstring(chart_svg(self.snap, indicators=('cci',), language='en'))
        self.assertTrue({'100', '−100'} <= {t.text for t in cci.iter(SVG + 'text')})

    def test_end_pans_without_changing_bars_or_reading_the_future(self):
        keys = ('sma', 'ema', 'bollinger', 'rsi', 'macd', 'stoch', 'adx', 'psar', 'keltner', 'obv', 'volume_ma')
        for end, visible in ((100, 60), (59, 30), (179, 120), (12, 120)):
            with self.subTest(end=end, visible=visible):
                truncated = replace(self.snap, candles=self.snap.candles[:end + 1])
                self.assertEqual(chart_svg(self.snap, indicators=keys, end=end, visible=visible, language='ko'),
                                 chart_svg(truncated, indicators=keys, visible=visible, language='ko'))
        panned = ET.fromstring(chart_svg(self.snap, indicators=(), end=100, visible=60))
        self.assertEqual([t.text for t in panned.iter(SVG + 'text')][1], self.snap.candles[100].timestamp)
        self.assertEqual(chart_svg(self.snap, end=179), chart_svg(self.snap))
        self.assertEqual(chart_svg(self.snap, end=10_000), chart_svg(self.snap))
        self.assertEqual(chart_svg(self.snap, end=None, cursor=50), chart_svg(self.snap, cursor=50))
        in_view = ET.fromstring(chart_svg(self.snap, indicators=(), end=100, visible=60, cursor=170))
        self.assertEqual([t.text for t in in_view.iter(SVG + 'text')][1], self.snap.candles[100].timestamp)

    def test_theme_changes_only_colours_and_price_height_moves_rows(self):
        keys = ('ichimoku', 'psar', 'stochrsi', 'investor_flow', 'vwap')
        outputs = []
        for dark in (False, True):
            root = ET.fromstring(chart_svg(self.snap, indicators=keys, dark=dark, supply=self.supply, language='ko'))
            for node in root.iter():
                for key in ('fill', 'stroke'):
                    node.attrib.pop(key, None)
            outputs.append(ET.tostring(root))
        self.assertEqual(outputs[0], outputs[1])
        short = ET.fromstring(chart_svg(self.snap, indicators=('rsi', 'cci')))
        tall = ET.fromstring(chart_svg(self.snap, indicators=('rsi', 'cci'), price_height=504))
        self.assertEqual(int(tall.attrib['height']) - int(short.attrib['height']), 300)
        self.assertEqual(chart_svg(self.snap, price_height=204), chart_svg(self.snap))

    def test_unavailable_studies_say_why_instead_of_drawing(self):
        texts = lambda svg: ' '.join(t.text or '' for t in ET.fromstring(svg).iter(SVG + 'text'))
        daily = texts(chart_svg(self.snap, indicators=('vwap', 'investor_flow'), language='ko'))
        self.assertIn('VWAP — 분 단위 차트 전용', daily)   # R-D9-2: no '봉'
        self.assertIn('수급 자료 없음', daily)
        overseas = snapshot(self.rows, asset='overseas')
        self.assertIn('국내 주식 · 일 단위 전용', texts(chart_svg(overseas, indicators=('short_ratio',), language='ko',
                                                       supply=self.supply)))
        minute = snapshot(self.rows[:120], '1m')
        drawn = ET.fromstring(chart_svg(minute, indicators=('vwap',), language='en'))
        color = study_colors('vwap')['VWAP']
        self.assertTrue([p for p in drawn.iter(SVG + 'polyline') if p.attrib['stroke'] == color])
        no_volume = snapshot(self.rows, volume=False)
        self.assertIn('no volume data', texts(chart_svg(no_volume, indicators=('obv',), language='en')))
        with_rows = ET.fromstring(chart_svg(self.snap, indicators=('investor_flow', 'short_ratio'), supply=self.supply))
        strokes = {p.attrib['stroke'] for p in with_rows.iter(SVG + 'polyline')}
        self.assertTrue(set(study_colors('investor_flow').values()) | set(study_colors('short_ratio').values()) <= strokes)

    def test_short_series_and_unknown_keys(self):
        short = snapshot(walk(8))
        root = self.check(chart_svg(short, indicators=E.study_keys(), language='ko'), False)
        self.assertIn('아직 계산할 봉이 부족합니다', {t.text for t in root.iter(SVG + 'text')})
        self.assertEqual(chart_svg(self.snap, indicators=('sma', 'not-a-study')).replace(' · not-a-study', ''),
                         chart_svg(self.snap, indicators=('sma',)))
        self.assertEqual(chart_svg(self.snap, indicators=('bb',)), chart_svg(self.snap, indicators=('bollinger',)))


def flat_bars(price, n=40, interval='1d', volume=100.0):
    """n bars that never move (open = high = low = close), with a constant volume."""
    if interval in ('1d', '1w', '1M'):
        stamps = tuple((datetime(2026, 2, 2) + timedelta(days=i)).date().isoformat() for i in range(n))
    else:
        stamps = tuple((datetime(2026, 2, 2, 9) + timedelta(minutes=i)).isoformat() for i in range(n))
    prices = (float(price),) * n
    return E.Bars(stamps, prices, prices, prices, prices, (volume,) * n, interval)


def faked(key, bars, line, value, index=-1):
    """compute_study values with one line's value at `index` replaced (a reading of any value)."""
    values = {k: np.array(v, dtype=float) for k, v in E.compute_study(key, bars).items()}
    values[line][index] = value
    return values


def both(key, bars, index=-1, **kwargs):
    return G.study_reading(key, bars, index, language='ko', **kwargs), \
        G.study_reading(key, bars, index, language='en', **kwargs)


class VerifierDefectTests(unittest.TestCase):
    """Regressions for the independent verifier's defects 1-11 in the beginner readings
    (engine_verify_defects.md, 2026-11-11). Each test failed on the commit before the fix."""

    def test_defect_1_flat_windows_of_decimal_prices_read_exactly_flat(self):
        for price in (88.79, 0.3, 7.1, 51300.0):
            with self.subTest(price=price):
                b = E.bars_from_closes([price] * 40)
                self.assertEqual(E.compute_study('percent_b', b)['PERCENT_B'][-1], 0.5)
                self.assertEqual(E.compute_study('cci', b)['CCI'][-1], 0.0)
                self.assertEqual(E.compute_study('disparity', b)['DISPARITY'][-1], 100.0)
                self.assertEqual(E.compute_study('bandwidth', b)['BANDWIDTH'][-1], 0.0)
                self.assertEqual(E.compute_study('sma', b)['SMA20'][-1], price)
                self.assertEqual(E.compute_study('ema', b)['EMA26'][-1], price)
                self.assertEqual(E.compute_study('macd', b)['MACD'][-1], 0.0)
                self.assertEqual(E.compute_study('keltner', b)['KC_UPPER'][-1], price)
                minute = flat_bars(price, 30, '1m')
                self.assertEqual(E.compute_study('vwap', minute)['VWAP'][-1], price)
                ko, en = both('bb', b)
                self.assertIn('아래 밴드에서 50% 높이', ko)
                self.assertIn('50% of the way', en)
                self.assertIn('한가운데', both('percent_b', b)[0])
                self.assertTrue(both('cci', b)[1].startswith('CCI 0:'))
                for key in ('sma', 'disparity', 'envelope', 'keltner'):
                    ko, en = both(key, b)
                    self.assertNotRegex(ko, r'0\.0% (위|아래)')
                    self.assertNotRegex(en, r'0\.0% (above|below)')
                self.assertNotIn('위 선 밖', both('keltner', b)[0])

    def test_defect_2_stochastic_reading_separates_the_average_from_this_bar(self):
        n = 20
        highs = [50.0] * n
        lows = [10.0] * n
        closes = [30.0] * n
        highs[n - 14], lows[1] = 100.0, 1.0
        for j in (n - 3, n - 2):
            closes[j] = lows[j] = 1.0
        closes[-1] = highs[-1] = 1 + .9 * 99  # raw positions 0%, 0%, 90% of the 1..100 range
        b = E.Bars(tuple(f'2026-01-{i + 1:02d}' for i in range(n)), tuple(closes), tuple(highs), tuple(lows),
                   tuple(closes), (1000.0,) * n)
        self.assertAlmostEqual(E.compute_study('stoch', b)['STOCH_K'][-1], 30.0)
        ko, en = both('stoch', b)
        self.assertIn('이날 종가만 보면 범위의 90% 높이', ko)   # R-D9-2: '이번 봉' is '이날' on a daily chart
        self.assertIn('This bar’s close alone is 90% of the way up', en)
        self.assertNotIn('30% 높이에서 마감', ko)
        self.assertNotIn('finished 30%', en)
        self.assertIn('3일 동안 평균하면', ko)
        # The mirror case: raw 100, 100, 40 averages to %K 80 (near the top) though this bar closed at 40%.
        closes = [30.0] * n
        closes[-3] = closes[-2] = highs[-3] = highs[-2] = 100.0
        closes[-1] = 1 + .4 * 99
        b = E.Bars(b.timestamps, tuple(closes), tuple(highs), tuple(lows), tuple(closes), (1000.0,) * n)
        self.assertAlmostEqual(E.compute_study('stoch', b)['STOCH_K'][-1], 80.0)
        ko, en = both('stoch', b)
        self.assertIn('꼭대기 근처', ko)
        self.assertIn('이날 종가만 보면 범위의 40% 높이', ko)
        # StochRSI: this bar's own position is the unsmoothed one (k_smooth = 1).
        bars = bars_of(walk(160, seed=5))
        raw = E.compute_study('stochrsi', bars, k_smooth=1)['STOCHRSI_K']
        slow = E.compute_study('stochrsi', bars)['STOCHRSI_K']
        index = max(range(40, 160), key=lambda j: abs(raw[j] - slow[j]))
        self.assertGreater(abs(raw[index] - slow[index]), 10)
        ko, en = both('stochrsi', bars, index)
        self.assertIn(f'이날 RSI만 보면 범위의 {raw[index]:.0f}% 높이', ko)
        self.assertIn(f'This bar’s RSI alone is {raw[index]:.0f}% of the way up', en)

    def test_defect_3_zero_volume_never_prints_nan(self):
        halted = flat_bars(51300, 25, volume=0.0)
        ko, en = both('volume_ma', halted)
        for text in (ko, en):
            self.assertNotRegex(text.lower(), r'\bnan\b')
        self.assertIn('거래량이 0', ko)
        self.assertIn('Volume was 0', en)

    def test_defect_4_investor_flow_never_calls_a_net_seller_a_buyer(self):
        bars = flat_bars(100, 25)
        dates = bars.dates
        selling = E.supply_from_rows([{'date': d, 'foreign_net_qty': -1000, 'institution_net_qty': -500,
                                       'individual_net_qty': -200} for d in dates])
        ko, en = both('investor_flow', bars, supply=selling)
        self.assertNotIn('샀고', ko)
        self.assertNotIn('순매수했고', ko)
        self.assertIn('순매수한 투자자는 없고 외국인이 가장 많이 순매도했습니다(−2만주)', ko)
        self.assertNotIn('bought', en)
        self.assertIn('no group was a net buyer', en)
        mixed = E.supply_from_rows([{'date': d, 'foreign_net_qty': 300, 'institution_net_qty': -100,
                                     'individual_net_qty': -200} for d in dates])
        ko, en = both('investor_flow', bars, supply=mixed)
        self.assertIn('외국인이 가장 많이 순매수했고(+6,000주), 개인이 가장 많이 순매도했습니다(−4,000주)', ko)
        blank = E.supply_from_rows([{'date': d, 'foreign_net_qty': 1, 'institution_net_qty': 1, 'individual_net_qty': -2}
                                    for d in dates[:-1]] +
                                   [{'date': dates[-1], 'foreign_net_qty': None, 'institution_net_qty': None,
                                     'individual_net_qty': None}])
        ko, en = both('investor_flow', bars, supply=blank)
        self.assertNotIn('순매수: .', ko)
        self.assertNotIn('date: .', en)
        self.assertIn('비어 있습니다', ko)

    def test_defect_5_psar_side_and_flip_come_from_the_engine(self):
        b = E.Bars(('2026-01-01', '2026-01-02', '2026-01-03'), (9.5, 9.4, 10.0), (10.0, 9.5, 10.5), (9.0, 8.0, 7.0),
                   (9.5, 8.2, 7.0), (1.0,) * 3)
        assert_close(self, E.compute_study('psar', b)['SAR'], [NAN, 10.0, 7.0])  # turns long on bar 2, SAR = close
        assert_close(self, E.parabolic_sar_trend(b.high, b.low), [NAN, -1.0, 1.0])
        ko, en = both('psar', b)
        self.assertIn('below price', en)
        self.assertIn('an upward move', en)
        self.assertIn('flipped', en)
        self.assertIn('아래쪽', ko)
        self.assertIn('상승 흐름', ko)
        self.assertIn('반대편으로 넘어왔습니다', ko)
        bars = bars_of(walk(160, seed=8))
        side = E.parabolic_sar_trend(bars.high, bars.low)
        for i in range(2, 160):
            text = G.study_reading('psar', bars, i, language='en')
            self.assertEqual('below price' in text, side[i] > 0, i)
            self.assertEqual('flipped' in text, side[i] != side[i - 1], i)

    def test_defect_6_vwap_reading_names_the_session_of_the_bar(self):
        stamps = tuple(f'2026-11-10T09:{m:02d}:00+09:00' for m in range(30)) + \
            tuple(f'2026-11-11T09:{m:02d}:00+09:00' for m in range(30))
        closes = tuple(100 + math.sin(i / 3) for i in range(60))
        b = E.Bars(stamps, closes, tuple(c + .2 for c in closes), tuple(c - .2 for c in closes), closes,
                   tuple(1000.0 + i for i in range(60)), '1m')
        for index, day in ((20, '2026-11-10'), (50, '2026-11-11')):
            ko, en = both('vwap', b, index)
            self.assertIn(f'{day} 장 VWAP', ko)
            self.assertIn(f'{day} session', en)
            self.assertNotIn('오늘', ko)
            self.assertNotIn('today', en.lower())

    def test_defect_7_donchian_tie_is_not_a_new_high(self):
        highs = [100.0] * 25
        highs[10] = highs[-1] = 105.0
        b = E.Bars(tuple(f'2026-01-{i + 1:02d}' for i in range(25)), (95.0,) * 25, tuple(highs), (90.0,) * 25,
                   (95.0,) * 25, (1.0,) * 25)
        ko, en = both('donchian', b)
        self.assertNotIn('새로 썼습니다', ko)
        self.assertNotIn('new high', en.replace('not a new high', ''))
        self.assertIn('최고가와 같습니다', ko)
        self.assertIn('a tie', en)
        flat_ko, flat_en = both('donchian', flat_bars(51300, 25))
        self.assertNotIn('새로 썼습니다', flat_ko)
        self.assertNotIn('new high', flat_en)
        highs[-1] = 106.0  # beating the earlier 105 is a new high
        ko, en = both('donchian', replace(b, high=tuple(highs)))
        self.assertIn('최고가를 새로 썼습니다', ko)
        self.assertIn('set a new high', en)

    def test_defect_8_words_follow_the_value_and_the_printed_number(self):
        bars = bars_of(walk(120, seed=2))
        rsi = lambda r, language='ko': G.study_reading('rsi', bars, -1, language=language,
                                                       values=faked('rsi', bars, 'RSI14', r))
        # 69 (rises 2.23x the falls) and 70 (2.33x) are described alike, with the ratio itself.
        self.assertIn('훨씬 컸습니다(평균 상승폭이 평균 하락폭의 2.2배)', rsi(69.0))
        self.assertIn('훨씬 컸습니다(평균 상승폭이 평균 하락폭의 2.3배)', rsi(70.0))
        self.assertIn('much larger', rsi(69.0, 'en'))
        words = [re.search(r'폭보다 (조금 더|더|훨씬) 컸습니다', rsi(r)).group(1) for r in np.arange(53, 100, .25)]
        order = {'조금 더': 1, '더': 2, '훨씬': 3}
        self.assertEqual([order[w] for w in words], sorted(order[w] for w in words))
        mfi = G.study_reading('mfi', bars, -1, values=faked('mfi', bars, 'MFI', 79.0))
        self.assertIn('훨씬 많았습니다(내린 날의 3.8배)', mfi)   # R-D9-2: '봉' is the day on a daily chart
        self.assertIn('far more', G.study_reading('mfi', bars, -1, language='en', values=faked('mfi', bars, 'MFI', 79.0)))
        # The conventional band always matches the number printed at the start of the reading.
        sweep = lambda *centres, step=.001, width=.1: np.concatenate(
            [np.arange(c - width, c + width, step) for c in centres])
        cases = (
            ('rsi', 'RSI14', r'RSI ([\d.]+):', sweep(30, 70),
             ((lambda x: x >= 70, '과매수'), (lambda x: x <= 30, '과매도'), (lambda x: 30 < x < 70, '30~70'))),
            ('stoch', 'STOCH_K', r'%K ([\d.]+):', sweep(20, 80),
             ((lambda x: x >= 80, '과매수'), (lambda x: x <= 20, '과매도'))),
            ('stochrsi', 'STOCHRSI_K', r'%K ([\d.]+):', sweep(20, 80),
             ((lambda x: x >= 80, '과매수'), (lambda x: x <= 20, '과매도'))),
            ('williams', 'WILLR', r'%R (−[\d.]+):', sweep(-20, -80),
             ((lambda x: x >= -20, '과매수'), (lambda x: x <= -80, '과매도'))),
            ('cci', 'CCI', r'CCI (−?\d+):', sweep(100, -100, step=.01, width=1),
             ((lambda x: x >= 100, '과열'), (lambda x: x <= -100, '침체'), (lambda x: -100 < x < 100, '±100 안'))),
            ('mfi', 'MFI', r'MFI ([\d.]+):', sweep(20, 80),
             ((lambda x: x >= 80, '과매수'), (lambda x: x <= 20, '과매도'))),
            ('percent_b', 'PERCENT_B', r'%B (−?[\d.]+):', sweep(0, 1, step=.0001, width=.01),
             ((lambda x: x > 1, '위 밴드 밖'), (lambda x: x < 0, '아래 밴드 밖'))),
            ('disparity', 'DISPARITY', r'이격도 ([\d.]+):', sweep(95, 105),
             ((lambda x: x >= 105, '과열'), (lambda x: x <= 95, '침체'))),
            ('adx', 'ADX', r'ADX ([\d.]+):', sweep(20, 25, 40),
             ((lambda x: x >= 40, '매우 뚜렷'), (lambda x: 25 <= x < 40, '추세가 뚜렷한 구간'),
              (lambda x: 20 <= x < 25, '애매'), (lambda x: x < 20, '20 미만'))),
        )
        for key, line, pattern, values, rules in cases:
            for value in values:
                text = G.study_reading(key, bars, -1, values=faked(key, bars, line, float(value)))
                shown = float(re.match(pattern, text).group(1).replace('−', '-'))
                for rule, phrase in rules:
                    self.assertEqual(rule(shown), phrase in text, f'{key} {value!r}: {text}')
        # The verifier's examples.
        self.assertTrue(rsi(69.96).startswith('RSI 70.0:'))
        self.assertIn('과매수', rsi(69.96))
        cci = G.study_reading('cci', bars, -1, values=faked('cci', bars, 'CCI', 99.6))
        self.assertTrue(cci.startswith('CCI 100:') and '±100 안' not in cci)
        stoch = G.study_reading('stoch', bars, -1, values=faked('stoch', bars, 'STOCH_K', 79.97))
        self.assertTrue(stoch.startswith('%K 80.0:') and '과매수' in stoch)

    def test_defect_9_equal_and_flat_branches_read_as_natural_korean(self):
        broken = re.compile(r'보다 (같|평평|정확히|0\.0+% (같|변하지))|같은 곳|보다 같음|equal than|unchanged than|'
                            r'0\.0+% (above|below|at|unchanged)')
        for price in (51300, 88.79):
            daily, minute = flat_bars(price, 90), flat_bars(price, 40, '1m')
            texts = {key: both(key, minute if key == 'vwap' else daily) for key in E.study_keys()
                     if not E.study(key).needs.startswith('kis_')}
            for key, pair in texts.items():
                for text in pair:
                    self.assertIsNone(broken.search(text), f'{key}: {text}')
                    self.assertNotRegex(text.lower(), r'\bnan\b|\bnone\b|\binf\b|−0\.0\b')
            ko = {key: pair[0] for key, pair in texts.items()}
            self.assertIn('평균선은 5일 전과 같은 높이로 평평합니다', ko['sma'])
            self.assertIn('12일 지수평균과 26일 지수평균이 같습니다', ko['macd'])
            self.assertIn('전환선과 기준선이 같은 높이에 있습니다', ko['ichimoku'])
            self.assertIn('+DI와 −DI가 모두 0', ko['adx'])
            self.assertIn('중심선과 같은 높이', ko['envelope'])
            self.assertIn('중심선과 같은 높이', ko['keltner'])
            self.assertIn('%K와 %D(50.0)가 같아', ko['stoch'])
            self.assertIn('12일 전과 같습니다', ko['roc'])
            self.assertIn('20일 평균과 같습니다', ko['disparity'])
            self.assertIn('한가운데', ko['percent_b'])
            self.assertIn('VWAP', ko['vwap'])
            self.assertIn('같습니다', ko['vwap'])

    def test_defect_10_ichimoku_pans_exactly_like_a_truncated_history(self):
        snap = snapshot(walk(200, seed=5))
        for end, visible in ((120, 60), (150, 120), (90, 30), (199, 60)):
            with self.subTest(end=end, visible=visible):
                truncated = replace(snap, candles=snap.candles[:end + 1])
                for keys in (('ichimoku',), ('ichimoku', 'stoch', 'psar', 'vwap', 'donchian')):
                    self.assertEqual(chart_svg(snap, indicators=keys, end=end, visible=visible, language='ko'),
                                     chart_svg(truncated, indicators=keys, visible=visible, language='ko'))

    def test_defect_11a_ichimoku_ahead_is_aligned_on_short_series(self):
        # ichimoku_ahead always returns displacement - 1 values, value k drawn k + 1 bars after the last bar.
        rows = walk(90, seed=4)
        h, l, c = column(rows, 1), column(rows, 2), column(rows, 3)
        for size in (1, 10, 24, 25, 26, 60):
            ahead = E.ichimoku_ahead(h[:size], l[:size], base=9, span_b=9)
            # Leading spans are causal: drawn on a longer series, bars size..size+24 show exactly these values.
            drawn = E.ichimoku_lines(h[:size] + h[60:85], l[:size] + l[60:85], c[:size] + c[60:85], base=9, span_b=9)
            for line in ('SPAN_A', 'SPAN_B'):
                with self.subTest(size=size, line=line):
                    self.assertEqual(len(ahead[line]), 25)
                    assert_close(self, ahead[line], list(drawn[line][size:size + 25]))

    def test_defect_11b_disparity_convention_names_the_chart_it_reads(self):
        # The 105/95 convention is the 20-day disparity's: other charts are not called '20일 이격도'.
        rising = [100 * 1.01 ** i for i in range(40)]
        weekly = G.study_reading('disparity', E.bars_from_closes(rising, interval='1w'), -1)
        self.assertNotIn('20일 이격도는 흔히', weekly)
        self.assertIn('20주 이격도', weekly)
        self.assertIn('20-week', G.study_reading('disparity', E.bars_from_closes(rising, interval='1w'), -1, language='en'))
        self.assertIn('20일 이격도는 흔히 105 이상을 과열', G.study_reading('disparity', E.bars_from_closes(rising), -1))
        minute = G.study_reading('disparity', E.bars_from_closes(rising, interval='5m'), -1)
        self.assertIn('20개 5분 구간 이격도', minute)   # R-D9-2: no '봉'
        self.assertNotIn('20일 이격도는 흔히', minute)

    def test_defect_11c_vwap_session_survives_midnight_in_a_night_session(self):
        # A KRX night futures session crossing midnight stays one VWAP session; the day session restarts it.
        stamps = ('2026-11-10T23:58:00+09:00', '2026-11-10T23:59:00+09:00', '2026-11-11T00:00:00+09:00',
                  '2026-11-11T00:01:00+09:00', '2026-11-11T08:45:00+09:00', '2026-11-11T08:46:00+09:00')
        prices = (10.0, 12.0, 14.0, 16.0, 20.0, 22.0)
        night = E.Bars(stamps, prices, prices, prices, prices, (1.0, 1.0, 2.0, 1.0, 1.0, 3.0), '1m')
        # (10 + 12 + 28) / 4 = 12.5 after midnight, (50 + 16) / 5 = 13.2; the day session starts again at 20.
        assert_close(self, E.compute_study('vwap', night)['VWAP'], [10.0, 11.0, 12.5, 13.2, 20.0, 21.5])
        self.assertIn('2026-11-10 장 VWAP', G.study_reading('vwap', night, 3))
        # Lunch breaks of 60-90 minutes keep one session; overnight gaps split it.
        lunch = ('2026-11-10T11:29:00+09:00', '2026-11-10T13:00:00+09:00', '2026-11-11T09:30:00+09:00')
        self.assertEqual(list(E.session_start_index(lunch)), [0, 0, 2])
        # A nearly 24-hour futures session (30-minute bars across midnight) restarts after its daily break.
        globex = [(datetime(2026, 11, 8, 17) + timedelta(minutes=30 * k)).isoformat() for k in range(46)] + \
            [(datetime(2026, 11, 9, 17) + timedelta(minutes=30 * k)).isoformat() for k in range(3)]
        self.assertEqual(list(E.session_start_index(globex)), [0] * 46 + [46] * 3)


if __name__ == '__main__':
    unittest.main()
