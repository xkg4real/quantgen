"""Carry display localization: numeric/source integrity and explicit caveats."""
from copy import deepcopy
from dataclasses import replace
import unittest
import re
from unittest.mock import patch
import numpy as np
from tests.desktop_acceptance import fx_fixture
from tests.desktop_fx_language_acceptance import numbers
from core.research.fx_analysis import FXRequest
from core.ficc.insights import narrate_carry
from quantgen_desktop.fx_narrative import carry_korean, carry_note_korean, fx_korean
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication, QTableWidget


def carry_numbers(text):
    # English "top-3" uses a joining hyphen, not a negative count.
    # Leave genuine negative returns/scores and date delimiters untouched.
    return numbers(re.sub(r'\btop-(?=\d)', 'top ', text))


class CarryLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        blocked = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        blocked.start(); self.addCleanup(blocked.stop)
        self.out = fx_fixture(FXRequest(tool='carry', source='synthetic', days=120,
                                       top_n=9, cost_bps=17, rebalance_days=13))

    def test_carry_result_preserves_every_number_and_caveat(self):
        out = self.out
        en, ko = out.narrative, fx_korean(out)
        self.assertEqual(carry_numbers(en), carry_numbers(ko))
        for text in ('역방향 호가는 이미 변환', '거래 회전량당 17bp', '동일 비중',
                     '모든 금리를 알 수 있는 첫 날짜', '월평균은 한 관측만큼 지연',
                     '미래 정보 사용 없음', 'top_n을 9에서'):
            self.assertIn(text, ko)
        self.assertNotIn('no lookahead', ko)
        self.assertEqual(en, narrate_carry(out.data['rows'], out.data['backtest']))

    def test_stale_rate_warning_requires_observation_date(self):
        rows = [replace(self.out.data['rows'][0], rate_stale=True, rate_date='2025-01-10'),
                replace(self.out.data['rows'][1], rate_stale=True, rate_date='')]
        ko = carry_korean(rows)
        self.assertEqual(carry_numbers(narrate_carry(rows)), carry_numbers(ko))
        self.assertIn(f'{rows[0].ccy} (2025-01-10)', ko)
        self.assertNotIn(f'{rows[1].ccy} ()', ko)
        self.assertIn('오늘 금리가 아닌', ko)
        self.assertIn('OECD 월별 시계열은 지연', ko)
        self.assertNotIn('최근 바스켓', ko)

    def test_empty_results_and_missing_benchmark_do_not_invent_values(self):
        self.assertEqual(carry_korean([]), '읽을 캐리 결과가 없습니다.')
        bt = replace(self.out.data['backtest'], bench_equity=np.array([]), positions=(), note='')
        ko = carry_korean(self.out.data['rows'], bt)
        self.assertEqual(carry_numbers(narrate_carry(self.out.data['rows'], bt)), carry_numbers(ko))
        self.assertIn('+nan%', ko)
        self.assertNotIn('최근 바스켓', ko)

    def test_unknown_or_extended_source_note_is_unchanged(self):
        for note in ('Provider note: EUR/USD 1.234 NOT_RUN', self.out.data['backtest'].note+' Extra source.'):
            self.assertEqual(note, carry_note_korean(note))
            bt = replace(self.out.data['backtest'], note=note)
            self.assertIn(note, carry_korean(self.out.data['rows'], bt))

    def test_unclipped_disclosure_and_negative_ranking(self):
        out = fx_fixture(replace(self.out.request, top_n=1, cost_bps=0))
        rows = [replace(r, carry=-abs(r.carry), score=-abs(r.score)) for r in out.data['rows']]
        ko = carry_korean(rows, out.data['backtest'])
        self.assertEqual(carry_numbers(narrate_carry(rows, out.data['backtest'])), carry_numbers(ko))
        self.assertNotIn('제한했습니다', ko)
        self.assertIn('연 캐리 -', ko)

    def test_visible_language_switch_preserves_reports_tables_and_equity(self):
        w = ResearchWindow(auto_refresh=False, language='ko')
        self.addCleanup(w.deleteLater)
        out = self.out
        w.fx.show_result(out); w.fx.bind_output('fx', out)
        before = deepcopy(w.fx.report)
        bt = out.data['backtest']; equity = bt.equity.copy()
        labels = w.fx.findChildren(UiLabel)
        narrative = next(x for x in labels if x.source_text == out.narrative)
        positions = next(x for x in labels if x.source_text.startswith('Long:'))
        tables = w.fx.findChildren(QTableWidget)
        values = lambda: [[[t.item(r,c).text() if t.item(r,c) else '' for c in range(t.columnCount())]
                            for r in range(t.rowCount())] for t in tables if t.columnCount() == 12]
        original_values = values()
        self.assertTrue(original_values)
        for lang in ('ko','en','ko','en'):
            w.set_language(lang)
            self.assertEqual(narrative.text(), fx_korean(out) if lang == 'ko' else out.narrative)
            self.assertEqual(numbers(positions.source_text), numbers(positions.text()))
            self.assertTrue(positions.text().startswith('매수:' if lang == 'ko' else 'Long:'))
            self.assertEqual(values(), original_values)
            self.assertEqual(w.fx.report, before)
            np.testing.assert_array_equal(bt.equity, equity)
            ranking = next(t for t in tables if t.columnCount() == 12)
            self.assertEqual(ranking.horizontalHeaderItem(1).text(), '통화' if lang == 'ko' else 'CCY')
        self.assertTrue(any(s.get('text') == out.narrative for s in before['sections']))


if __name__ == '__main__': unittest.main()
