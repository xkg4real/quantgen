"""Guide search glossary: language parity, search ranking and purity. No Qt, network or stores."""
import re
import unittest
from unittest.mock import patch

from core.education import glossary
from core.education.indicators import INDICATORS
from core.i18n import LocaleContext
from core.ui_messages import MESSAGES


class GlossaryContentTests(unittest.TestCase):
    def test_every_term_has_both_languages_and_english_has_no_hangul(self):
        self.assertEqual(len(glossary.TERMS), len(glossary.BY_KEY))
        for term in glossary.TERMS:
            self.assertIn(term.category, glossary.CATEGORIES)
            if term.key in {spec.key for spec in INDICATORS}:
                self.assertEqual(term.text, {}, term.key)
                continue
            self.assertEqual(set(term.text), {'ko', 'en'}, term.key)
            for language in ('ko', 'en'):
                self.assertEqual(tuple(term.text[language]), glossary.FIELDS, term.key)
                self.assertTrue(all(value.strip() for value in term.text[language].values()), term.key)
            self.assertFalse([f for f, v in term.text['en'].items() if re.search('[가-힣]', v)], term.key)
            self.assertTrue(re.search('[가-힣]', term.text['ko']['meaning']), term.key)

    def test_indicators_reuse_reviewed_messages_and_categories_are_catalogued(self):
        self.assertTrue({spec.key for spec in INDICATORS} <= set(glossary.BY_KEY))
        for language in ('ko', 'en'):
            ctx = LocaleContext('ko_KR' if language == 'ko' else 'en_US')
            for category in glossary.CATEGORIES:
                self.assertIn('cat_' + category, MESSAGES[language])
            self.assertEqual(glossary.name('rsi', ctx), MESSAGES[language]['rsi'])
            self.assertEqual(glossary.sections('rsi', ctx),
                             tuple((MESSAGES[language][f], MESSAGES[language]['rsi_' + f])
                                   for f in ('meaning', 'look', 'interpret', 'limit')))
            heads = [heading for heading, _ in glossary.sections('duration', ctx)]
            self.assertEqual(heads, [MESSAGES[language][k] for k in ('meaning', 'glossary_use', 'limit')])
            self.assertTrue(glossary.summary('rsi', ctx).endswith('.'))
        self.assertTrue(set(glossary.POPULAR) <= set(glossary.BY_KEY))

    def test_search_title_follows_the_owner_wording(self):
        self.assertEqual(MESSAGES['en']['search_title'], 'Search what you want to explore')
        self.assertEqual(MESSAGES['ko']['search_title'], '궁금한 내용을 검색해 보세요')


class GlossarySearchTests(unittest.TestCase):
    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)

    def test_names_abbreviations_and_both_languages_rank_first(self):
        expected = {'rsi': 'rsi', 'RSI': 'rsi', '상대': 'rsi', '볼린저': 'bb', 'bollinger': 'bb', 'BB': 'bb',
                    '이동평균': 'sma', 'moving': 'sma', 'ema': 'ema', 'MACD': 'macd', '듀레이션': 'duration',
                    'duration': 'duration', 'VaR': 'var', 'cvar': 'cvar', '기대손실': 'cvar', '델타': 'greeks',
                    'q-score': 'q_score', 'Q SCORE': 'q_score', '선물환': 'fx_forward', 'P5': 'percentile_band',
                    '캔들': 'candlestick', 'ㅂㄹㅈ': 'bb', 'ㄷㄹㅇㅅ': 'duration'}
        for query, key in expected.items():
            self.assertEqual(glossary.search(query)[0], key, query)

    def test_definitions_match_last_and_short_latin_does_not_scan_definitions(self):
        found = glossary.search('금리')
        self.assertIn('duration', found); self.assertIn('swap_rate', found)
        self.assertEqual(glossary.search('rs')[0], 'rsi')
        # Two Latin letters never scan definitions: every hit has 'rs' in a name, key or alias.
        for key in glossary.search('rs'):
            names = glossary._names(glossary.BY_KEY[key], MESSAGES)
            self.assertTrue(any('rs' in glossary._normal(n) for n in names), key)
        self.assertEqual(glossary.search('variance')[:1], ('beta',))  # a definition word, matched at a word start

    def test_empty_unknown_limits_and_determinism(self):
        for query in ('', '   ', '·', 'zzzz', 'ㅋㅋㅋㅋ'):
            self.assertEqual(glossary.search(query), (), query)
        self.assertEqual(len(glossary.search('ㅂ')), 8); self.assertEqual(len(glossary.search('ㅂ', limit=3)), 3)
        self.assertEqual(glossary.search('ㅂ', limit=0), ())
        self.assertEqual(glossary.search('변동'), glossary.search('변동'))
        self.assertEqual(glossary.search(' RSI '), ('rsi',))


if __name__ == '__main__':
    unittest.main()
