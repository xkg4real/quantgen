"""Offline overseas name search (owner UI-16): bundled list, both languages, no I/O beyond the file."""
import json
import unittest
from unittest.mock import patch

from core.market import symbols
from core.market.models import Instrument


class SymbolSearchTests(unittest.TestCase):
    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)

    def test_names_codes_and_korean_initials_find_the_listing(self):
        expected = {'apple': ('AAPL', 'NAS'), '애플': ('AAPL', 'NAS'), 'AAPL': ('AAPL', 'NAS'), 'aapl': ('AAPL', 'NAS'),
                    'tsm': ('TSM', 'NYS'), 'tsmc': ('TSM', 'NYS'), '엔비': ('NVDA', 'NAS'), 'ㅌㅅㄹ': ('TSLA', 'NAS'),
                    'spy': ('SPY', 'AMS'), '텐센트': ('00700', 'HKS'), '7203': ('7203', 'TSE'), 'microsoft': ('MSFT', 'NAS')}
        for query, listing in expected.items():
            first = symbols.search(query)[0]
            self.assertEqual((first.code, first.exchange), listing, query)

    def test_limits_empty_and_unknown_queries(self):
        self.assertEqual(symbols.search(''), ())
        self.assertEqual(symbols.search('zzzz'), ())
        self.assertEqual(len(symbols.search('a', limit=3)), 3)
        self.assertEqual(symbols.search('a', limit=0), ())

    def test_every_entry_is_a_valid_kis_instrument_and_labels_are_bilingual(self):
        payload = json.loads(symbols.DATA.read_text(encoding='utf-8'))
        self.assertEqual(payload['schema'], 'quantgen.overseas-symbols/1')
        seen = set()
        for entry in symbols.entries():
            Instrument('overseas_stock', entry.code, entry.exchange)  # raises on an invalid code/exchange
            self.assertNotIn((entry.code, entry.exchange), seen); seen.add((entry.code, entry.exchange))
            self.assertIn(entry.code, entry.label('ko')); self.assertIn(entry.code, entry.label('en'))
            self.assertTrue(entry.name_ko and entry.name_en)
        self.assertEqual(symbols.lookup('aapl').exchange, 'NAS')
        self.assertIsNone(symbols.lookup('AAPL', 'NYS'))


if __name__ == '__main__':
    unittest.main()
