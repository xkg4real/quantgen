"""Live indicator rendering contracts with independent price-series oracles."""
from xml.etree import ElementTree as ET
import unittest

from core.market.models import Candle, ChartRequest, MarketSnapshot
from core.market.presentation import chart_svg, indicator_colors, indicator_series, readout, _axis_number


class LiveChartPresentationTests(unittest.TestCase):
    def history(self):
        return MarketSnapshot(ChartRequest(), tuple(Candle(f"2026-10-{i+1:02d}", i+1, i+2, i, i+1, 10)
                                                    for i in range(30)))

    def test_ema_independent_linear_price_oracle_and_warmup(self):
        values = indicator_series(self.history())
        self.assertEqual(values['EMA12'][:11], [None]*11)
        self.assertEqual(values['EMA26'][:25], [None]*25)
        self.assertAlmostEqual(values['EMA12'][11], 6.5)
        self.assertAlmostEqual(values['EMA26'][25], 13.5)
        self.assertAlmostEqual(values['EMA12'][-1], 24.5)
        self.assertAlmostEqual(values['EMA26'][-1], 17.5)

    def test_selection_changes_actual_paths_and_panel_heights_at_small_widths(self):
        ns = '{http://www.w3.org/2000/svg}'
        for width in (320, 420, 500, 1000):
            for dark in (False, True):
                with self.subTest(width=width, dark=dark):
                    plain = ET.fromstring(chart_svg(self.history(), width=width, dark=dark, indicators=()))
                    all_on = ET.fromstring(chart_svg(self.history(), width=width, dark=dark,
                        indicators=('sma', 'ema', 'bollinger', 'rsi', 'macd')))
                    self.assertEqual(plain.findall(ns+'polyline'), [])
                    self.assertGreater(int(all_on.attrib['height']), int(plain.attrib['height']))
                    colors = indicator_colors(dark)
                    ema_lines = [line for line in all_on.findall(ns+'polyline') if line.attrib['stroke'] == colors['ema']]
                    self.assertEqual(len(ema_lines), 2)
                    self.assertEqual({line.attrib.get('stroke-dasharray','') for line in ema_lines}, {'', '4 3'})
                    for text in all_on.findall(ns+'text'):
                        if text.attrib['y'] == '60.0':
                            self.assertLess(float(text.attrib['x']) + len(text.text)*7, int(all_on.attrib['width']) - 10)

    def test_tick_identity_and_localized_candle_readout(self):
        candle = Candle('2026-11-02T09:00:01+09:00',100,105,99,102,3,sequence=2,trade_count=1)
        snapshot = MarketSnapshot(ChartRequest(interval='1tick'),(candle,))
        self.assertIn('#2', readout(snapshot, language='ko'))
        self.assertIn('시작 100', readout(snapshot, language='ko'))
        self.assertIn('거래량 3', readout(snapshot, language='ko'))
        self.assertIn('O 100', readout(snapshot, language='en'))
        self.assertIn('거래량', chart_svg(snapshot, language='ko'))
        self.assertIn('Volume', chart_svg(snapshot, language='en'))
        self.assertIn('09:00:01', chart_svg(snapshot, language='ko'))
        self.assertNotIn('KIS', chart_svg(snapshot, language='ko'))

    def test_grid_rounds_distracting_fractions_without_losing_small_scales(self):
        self.assertEqual(_axis_number(182.77333333, 136.64), '183')
        self.assertEqual(_axis_number(0.12345678, 0.003), '0.1235')
        self.assertNotEqual(_axis_number(1e-9, 3e-9), _axis_number(2e-9, 3e-9))
        self.assertEqual(_axis_number(-0.001, 100), '0')
        self.assertIn('마지막 102', readout(MarketSnapshot(ChartRequest(),
            (Candle('2026-11-02',100,103.456789,99,102,2),)), language='ko'))
        self.assertIn('103.456789', readout(MarketSnapshot(ChartRequest(),
            (Candle('2026-11-02',100,103.456789,99,102,2),)), language='ko'))


if __name__ == '__main__':
    unittest.main()
