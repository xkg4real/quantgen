"""Markets indicator board data (owner UI-7): four indicators, no stocks, KIS first, no synthetic."""
import datetime
import math
import re
import unittest
from unittest.mock import patch

from core.market.presentation import card_svg
from core.research import market_board as board


def series(n=60, start=100.0, end_date=None):
    end = end_date or datetime.date.today()
    dates = [(end - datetime.timedelta(days=n - 1 - i)).isoformat() for i in range(n)]
    return dates, [start * (1 + 0.01 * math.sin(i)) for i in range(n)]


class BoardCoreTests(unittest.TestCase):
    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)

    def test_four_indicators_none_of_them_an_individual_stock(self):
        self.assertEqual([s.key for s in board.BOARD_SPECS], ['kospi', 'spx', 'usdkrw', 'ust10y'])
        for spec in board.BOARD_SPECS:
            for _, kind, argument in spec.chain:
                self.assertNotIn(kind, ('kis_stock', 'stock'))
                self.assertFalse(isinstance(argument, str) and re.fullmatch(r'\d{6}', argument), spec.key)
                self.assertNotEqual(kind, 'synthetic')
        self.assertEqual(board.BY_KEY['kospi'].chain[0][0], 'KIS')
        self.assertEqual(board.BY_KEY['usdkrw'].chain[0][0], 'KIS')

    def test_kis_first_then_fallback_when_kis_is_not_configured(self):
        calls = []

        def fetch(name):
            def run(argument):
                calls.append((name, argument)); return series()
            return run
        routers = board.build_routers(fetchers={'kis_ready': lambda: (True, ()), 'kis_index': fetch('kis_index'),
                                                'kis_chart': fetch('kis_chart'), 'kis_fx': fetch('kis_fx'),
                                                'yfinance': fetch('yfinance'), 'fred': fetch('fred')})
        results = board.load_board(routers)
        self.assertEqual([r.series.source for r in results], ['KIS', 'KIS', 'KIS', 'FRED'])
        self.assertNotIn('yfinance', [name for name, _ in calls])
        calls.clear()
        routers = board.build_routers(fetchers={'kis_ready': lambda: (False, ('KIS_APP_KEY', 'KIS_APP_SECRET')),
                                                'yfinance': fetch('yfinance'), 'fred': fetch('fred')})
        results = board.load_board(routers)
        sources = {r.key: r.series.source for r in results}
        self.assertEqual(sources['kospi'], 'Yahoo Finance'); self.assertEqual(sources['spx'], 'Yahoo Finance')
        self.assertIn(sources['usdkrw'], ('FRED', 'Yahoo Finance'))
        self.assertIn('KIS_APP_KEY', results[0].tried('en'))
        self.assertNotIn('kis_index', [name for name, _ in calls])

    def test_failures_stay_per_card_and_carry_no_provider_text(self):
        def broken(argument):
            raise RuntimeError('https://secret.example/?apikey=XYZ')
        routers = board.build_routers(fetchers={'kis_ready': lambda: (False, ('KIS_APP_KEY',)),
                                                'yfinance': broken, 'fred': lambda a: series()})
        results = {r.key: r for r in board.load_board(routers)}
        self.assertIsNone(results['kospi'].series); self.assertEqual(results['kospi'].error, 'ProvidersUnavailable')
        self.assertNotIn('secret', repr(results['kospi'].attempts) + results['kospi'].tried('ko'))
        self.assertIsNotNone(results['ust10y'].series)

    def test_validation_change_units_and_staleness(self):
        dates, values = series(3)
        s = board.BoardSeries('ust10y', tuple(dates), (4.0, 4.1, 4.25), 'FRED')
        self.assertAlmostEqual(s.change, 15.0)  # basis points for a yield
        p = board.BoardSeries('kospi', tuple(dates), (100.0, 100.0, 102.0), 'KIS')
        self.assertAlmostEqual(p.change, 2.0)
        self.assertEqual(board.valid_series('kospi', board.BoardSeries('kospi', ('2026-01-01',), (1.0,), 'X')), 'too_few_values')
        self.assertEqual(board.valid_series('kospi', board.BoardSeries('kospi', ('2026-01-02', '2026-01-01'), (1.0, 2.0), 'X')), 'unordered_dates')
        self.assertEqual(board.valid_series('kospi', board.BoardSeries('kospi', ('2026-01-01', '2026-01-02'), (1.0, float('nan')), 'X')), 'bad_value')
        self.assertEqual(board.valid_series('spx', p), 'wrong_series')
        old = board.BoardSeries('kospi', ('2026-01-01', '2026-01-02'), (1.0, 2.0), 'X')
        self.assertTrue(old.stale(datetime.date(2026, 1, 20))); self.assertFalse(old.stale(datetime.date(2026, 1, 5)))

    def test_card_svg_is_a_line_with_labels_at_card_widths_and_handles_no_data(self):
        dates, values = series(30)
        for width in (220, 360, 480):
            for dark in (False, True):
                svg = card_svg(dates, values, width=width, dark=dark, label='KOSPI', decimals=2)
                self.assertIn(f'width="{width}"', svg); self.assertIn('<path d="M', svg)
                self.assertIn(dates[0], svg); self.assertIn(dates[-1], svg)
                self.assertNotIn('<rect x=', svg)  # no candles are invented for close-only data
        self.assertIn('—', card_svg((), ()))
        flat = card_svg(dates[:5], [4.25] * 5, width=300, decimals=3)
        labels = [part.split('>')[1].split('<')[0] for part in flat.split('<text')[1:4]]
        self.assertEqual(len(set(labels)), 3)  # a flat series keeps three distinct gridlines

    def test_usdkrw_asks_fred_only_after_yahoo_fails(self):
        calls = []

        def yahoo(argument):
            calls.append('yahoo'); return series()

        def fred(argument):
            calls.append('fred'); return series()
        routers = board.build_routers(fetchers={'kis_ready': lambda: (False, ('KIS_APP_KEY',)),
                                                'yfinance': yahoo, 'fred': fred})
        result = board.load_board(routers, ['usdkrw'])[0]
        self.assertEqual((result.series.source, calls), ('Yahoo Finance', ['yahoo']))

        def broken(argument):
            calls.append('yahoo'); raise RuntimeError('down')
        calls.clear()
        routers = board.build_routers(fetchers={'kis_ready': lambda: (False, ('KIS_APP_KEY',)),
                                                'yfinance': broken, 'fred': fred})
        result = board.load_board(routers, ['usdkrw'])[0]
        self.assertEqual((result.series.source, calls), ('FRED', ['yahoo', 'fred']))


if __name__ == '__main__':
    unittest.main()
