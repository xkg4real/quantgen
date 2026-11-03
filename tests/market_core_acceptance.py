"""Independent indicator oracles and live-candle state transitions; no I/O."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math
import unittest
from xml.etree import ElementTree

from core.market.models import Candle, ChartRequest, Instrument, MarketQuote, MarketSnapshot, MarketTick
from core.market.live import apply_tick, bucket
from core.market.presentation import chart_svg, indicator_values, indicator_series, readout


def history(n=80, interval="1d"):
    candles = tuple(Candle((datetime(2026, 1, 1) + timedelta(days=i)).date().isoformat(),
                           i + 100, i + 102, i + 99, i + 101, 1000 + i) for i in range(n))
    return MarketSnapshot(ChartRequest(interval=interval), candles)


def contrast_ratio(first, second):
    """WCAG sRGB relative luminance, computed from actual rendered SVG colors."""
    def luminance(value):
        channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))
    low, high = sorted((luminance(first), luminance(second)))
    return (high + .05) / (low + .05)


class ChartContrastTests(unittest.TestCase):
    def test_both_themes_meet_legend_text_and_indicator_line_contrast(self):
        ns = '{http://www.w3.org/2000/svg}'
        for dark in (False, True):
            for width in (420, 1000):
                with self.subTest(dark=dark, width=width):
                    root = ElementTree.fromstring(chart_svg(history(), dark=dark, width=width,
                        indicators=('sma', 'rsi', 'macd', 'bollinger')))
                    background = root.find(ns + 'rect').attrib['fill']
                    texts = root.findall(ns + 'text')
                    self.assertTrue({'SMA20', 'BB20 +2σ', 'BB20 −2σ'} <= {t.text for t in texts})
                    for text in texts:
                        self.assertGreaterEqual(contrast_ratio(text.attrib['fill'], background), 4.5, text.text)
                    paths = root.findall(ns + 'polyline')
                    self.assertGreaterEqual(len(paths), 6)
                    for path in paths:
                        self.assertGreaterEqual(contrast_ratio(path.attrib['stroke'], background), 3)
                    if dark:
                        legend = {t.text: t.attrib['fill'] for t in texts}
                        self.assertEqual(legend['SMA20'], '#C58C23')
                        self.assertEqual(legend['BB20 +2σ'], '#2E9F91')

    def test_theme_changes_only_color_not_values_labels_or_plot_geometry(self):
        snapshot = history()
        before = indicator_series(snapshot)
        outputs = []
        for dark in (False, True):
            root = ElementTree.fromstring(chart_svg(snapshot, dark=dark, cursor=45, visible=30,
                indicators=('sma', 'rsi', 'macd', 'bollinger')))
            for node in root.iter():
                for key in ('fill', 'stroke'): node.attrib.pop(key, None)
            outputs.append(ElementTree.tostring(root))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(indicator_series(snapshot), before)


class IndicatorTests(unittest.TestCase):
    def test_independent_linear_price_oracle_and_warmup(self):
        s = history()
        result = indicator_series(s)
        self.assertTrue(all(v is None for v in result["SMA20"][:19]))
        self.assertEqual(result["SMA20"][19], 110.5)
        self.assertEqual(result["SMA20"][-1], 170.5)
        self.assertTrue(all(v is None for v in result["RSI14"][:14]))
        self.assertEqual(result["RSI14"][14:], [100.0] * 66)
        self.assertTrue(all(v is None for v in result["MACD"][:25]))
        self.assertTrue(all(v is None for v in result["SIGNAL"][:33]))
        self.assertAlmostEqual(result["MACD"][-1], 7.0)
        self.assertAlmostEqual(result["SIGNAL"][-1], 7.0)
        # Population SD of 20 consecutive integers = sqrt((20²-1)/12).
        self.assertAlmostEqual(result["BB_UPPER"][-1], 170.5 + 2 * math.sqrt(399 / 12))

    def test_wilder_rsi_known_reference(self):
        closes = [44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28]
        s = replace(history(len(closes)), candles=tuple(Candle(str(i), c, c, c, c) for i,c in enumerate(closes)))
        self.assertAlmostEqual(indicator_values(s)["RSI14"], 70.464135, places=5)

    def test_flat_rsi_unknown_volume_and_short_warmup(self):
        s = replace(history(40), candles=tuple(Candle(str(i), 100, 100, 100, 100) for i in range(40)))
        self.assertEqual(indicator_values(s)["RSI14"], 50)
        self.assertEqual(indicator_values(s)["MACD"], 0)
        self.assertIsNone(indicator_values(history(10))["SMA20"])
        self.assertIn("V —", readout(s))

    def test_svg_all_panels_mobile_dark_and_escaped_symbol(self):
        for width in (420, 1000):
            s = history()
            svg = chart_svg(s, visible=20, cursor=65, width=width, dark=True,
                            indicators=("sma", "rsi", "macd", "bollinger"))
            root = ElementTree.fromstring(svg)
            self.assertEqual(root.attrib["width"], str(width))
            self.assertIn("SMA20", svg)
            self.assertNotIn("nan", svg.lower())
            self.assertNotIn("inf", svg.lower())
            curves = root.findall('{http://www.w3.org/2000/svg}polyline')
            sma = next(c for c in curves if c.attrib['stroke'] == '#C58C23')
            self.assertEqual(len(sma.attrib['points'].split()),20)  # all visible points are warmed


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.instrument = Instrument()
        self.request = ChartRequest(self.instrument, "1m")
        self.snapshot = MarketSnapshot(self.request,
            (Candle("2026-11-02T09:00:00+09:00",100,102,99,101,10),),
            MarketQuote(self.instrument, price=101, volume=1000, market_time="2026-11-02T09:00:10+09:00",
                        received_at="2026-11-02T00:00:10+00:00"))

    def tick(self, timestamp="2026-11-02T09:00:20+09:00", price=103, volume=2, cumulative_volume=1002):
        return MarketTick(self.instrument, timestamp, price, volume, cumulative_volume)

    def test_current_bar_preserves_ohlc_and_accumulated_volume_oracle(self):
        updated = apply_tick(self.snapshot, self.tick())
        self.assertEqual(updated.candles[-1], Candle("2026-11-02T09:00:00+09:00",100,103,99,103,12))
        self.assertEqual(updated.quote.volume, 1002)
        self.assertEqual(updated.quote.market_time, "2026-11-02T09:00:20+09:00")
        self.assertEqual(apply_tick(updated, self.tick()), updated)
        self.assertEqual(apply_tick(updated, self.tick(cumulative_volume=1001)), updated)

    def test_new_bucket_gaps_and_day_reset(self):
        s = apply_tick(self.snapshot, self.tick(timestamp="2026-11-02T09:03:00+09:00"))
        self.assertEqual(len(s.candles), 2)  # no fabricated 09:01/09:02 candles
        s = apply_tick(s, self.tick(timestamp="2026-11-03T09:00:01+09:00", volume=5,cumulative_volume=5))
        self.assertEqual(s.candles[-1].volume, 5)
        self.assertEqual(s.quote.volume, 5)

    def test_wrong_symbol_bad_timestamp_and_old_ticks_cannot_mutate(self):
        s = apply_tick(self.snapshot, self.tick())
        for tick in (replace(self.tick(),instrument=Instrument(code="000660")),
                     replace(self.tick(),timestamp="2026-11-02T09:00:19+09:00"),
                     replace(self.tick(),timestamp="2026-11-02T09:00:21"),
                     replace(self.tick(),price=float("nan")),replace(self.tick(),volume=-1)):
            self.assertIs(apply_tick(s,tick),s)

    def test_week_month_and_minute_boundaries(self):
        self.assertEqual(bucket("2026-11-03T09:17:05+09:00","1w"),"2026-11-02")
        self.assertEqual(bucket("2026-11-03T09:17:05+09:00","1M"),"2026-11-01")
        self.assertEqual(bucket("2026-11-03T09:17:05+09:00","15m"),"2026-11-03T09:15:00+09:00")

    def test_adjusted_chart_never_gets_raw_tick_price(self):
        s = replace(self.snapshot, request=replace(self.request,adjusted=True))
        updated = apply_tick(s,self.tick())
        self.assertEqual(updated.candles,s.candles)
        self.assertEqual(updated.quote.price,103)

    def test_receipt_time_cannot_establish_a_session_volume_baseline(self):
        s = replace(self.snapshot, quote=replace(self.snapshot.quote,market_time="",volume=1000000))
        updated = apply_tick(s,self.tick(cumulative_volume=3,volume=3))
        self.assertEqual(updated.quote.price,103)
        self.assertIsNone(updated.candles[-1].volume)

    def test_reconnect_cumulative_volume_not_assigned_to_one_minute(self):
        s = apply_tick(self.snapshot,self.tick())
        updated = apply_tick(s,self.tick(timestamp="2026-11-02T09:05:01+09:00",volume=1,cumulative_volume=2000))
        self.assertIsNone(updated.candles[-1].volume)
        self.assertIn("Live gap",updated.note)

    def test_short_gap_across_adjacent_minutes_is_also_unknown(self):
        s = apply_tick(self.snapshot,self.tick(timestamp="2026-11-02T09:00:59+09:00"))
        updated = apply_tick(s,self.tick(timestamp="2026-11-02T09:01:30+09:00",volume=1,cumulative_volume=1100))
        self.assertIsNone(updated.candles[-1].volume)
        self.assertIn("Live gap",updated.note)

    def test_week_volume_adds_new_sessions_cumulative_not_only_last_trade(self):
        s = replace(self.snapshot, request=ChartRequest(interval="1w"),
                    candles=(Candle("2026-11-02",100,102,99,101,1000),),
                    last_tick_at="2026-11-02T15:30:00+09:00",last_cumulative_volume=1000)
        updated = apply_tick(s,self.tick(timestamp="2026-11-03T10:00:00+09:00",volume=2,cumulative_volume=300))
        self.assertEqual(updated.candles[-1].volume,1300)

    def test_offset_normalization_and_missing_cumulative_do_not_duplicate_volume(self):
        s = apply_tick(self.snapshot,self.tick(timestamp="2026-11-02T00:00:20+00:00"))
        self.assertEqual(len(s.candles),1)
        s = apply_tick(s,self.tick(timestamp="2026-11-02T09:00:21+09:00",cumulative_volume=None))
        s = apply_tick(s,self.tick(timestamp="2026-11-02T09:00:22+09:00",cumulative_volume=1006))
        self.assertEqual(s.candles[-1].volume,16)

    def test_nonfinite_or_impossible_candles_rejected(self):
        for values in ((1,0,1,1,1),(1,2,3,1,1),(1,2,1,float("nan"),1),(1,2,1,1,-1)):
            with self.assertRaises(ValueError):Candle("2026-11-02",*values)


if __name__ == "__main__":
    unittest.main()
