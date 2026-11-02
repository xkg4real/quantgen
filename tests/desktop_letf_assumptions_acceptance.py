"""Native LETF scenario inputs, separate attribution and unchanged reference."""
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch
from tests.desktop_acceptance import QApplication, ResearchWindow
from tests.desktop_fx_language_acceptance import numbers
from core.research.market_analysis import ETFRequest, execute_etf
from core.research.letf_disclosure import letf_text
from quantgen_desktop.market_narrative_language import letf_korean
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.tools import fmt
from PyQt6.QtCore import QEvent


class NativeLETFAssumptionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.validate.load_cards',
                       'core.quant.gate_ledger.family_ledger'):
            p = patch(target, side_effect=AssertionError('live I/O forbidden'))
            p.start(); self.addCleanup(p.stop)
        self.window = ResearchWindow(auto_refresh=False, language='en')
        self.pane = self.window.etf
        self.fields = self.pane.fields['etf']
        self.pane.source.setCurrentIndex(self.pane.source.findData('synthetic'))

    def tearDown(self):
        self.pane.clear_result(); self.window.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def inputs(self, mode, rate='', fee='', dividend=''):
        self.fields['letf_benchmark'].setCurrentIndex(self.fields['letf_benchmark'].findData(mode))
        for key, value in [('letf_funding_rate', rate), ('letf_annual_fee', fee),
                           ('letf_dividend_yield', dividend)]: self.fields[key].setText(value)

    def test_reference_defaults_and_percent_conversion_survive_language_switch(self):
        q = self.pane.make_request(); q.validate()
        self.assertEqual(q, ETFRequest(source='synthetic'))
        self.inputs('price_return', '-1.5', '.64', '2.1')
        self.fields['code'].setText('252670')
        q = self.pane.make_request(); q.validate()
        self.assertEqual((q.letf_funding_rate, q.letf_annual_fee, q.letf_dividend_yield), (-.015, .0064, .021))
        values = self.pane.values()
        with patch.object(self.window.jobs, 'start', side_effect=AssertionError('no recomputation')):
            for language in ('ko', 'en', 'ko'):
                self.window.set_language(language)
                self.assertEqual(self.pane.values(), values)
                self.assertEqual(self.pane.make_request(), q)

    def test_incomplete_or_double_counted_dividends_never_emit_a_request(self):
        received = []
        # Disconnect the window's execution callback so this test can observe
        # request validation without ever starting a workflow.
        self.pane.requested.disconnect()
        self.pane.requested.connect(received.append)
        for mode, rate, fee, dividend in [
            ('zero_rate_reference', '2', '', ''), ('total_return', '', '.64', ''),
            ('total_return', '2', '', ''), ('total_return', '2', '.64', '0'),
            ('price_return', '2', '.64', ''), ('price_return', '2', '.64', '-1'),
            ('price_return', '2', '-.1', '1'), ('price_return', 'nan', '.64', '1')]:
            with self.subTest(mode=mode, rate=rate, fee=fee, dividend=dividend):
                self.inputs(mode, rate, fee, dividend); self.pane.submit()
                self.assertFalse(received)
                self.assertIn('Input error', self.pane.status.text())
        self.inputs('total_return', '2', '.64')
        self.pane.submit(); self.assertEqual(len(received), 1)
        self.assertIsNone(received[0].letf_dividend_yield)

    def test_synthetic_scenarios_display_each_signed_term_and_export_assumptions(self):
        cases = [ETFRequest(source='synthetic', code='122630'),
                 ETFRequest(source='synthetic', code='122630', letf_benchmark='total_return',
                            letf_funding_rate=.035, letf_annual_fee=.0064),
                 ETFRequest(source='synthetic', code='252670', letf_benchmark='price_return',
                            letf_funding_rate=.035, letf_annual_fee=.007, letf_dividend_yield=.02)]
        for q in cases:
            with self.subTest(q=q):
                out = execute_etf(q); lt = out.data['letf']
                self.assertEqual(numbers(letf_text(lt)), numbers(letf_korean(lt)))
                self.pane.show_result(out); self.pane.bind_output('Synthetic LETF scenario', out)
                report = deepcopy(self.pane.report)
                self.assertEqual(report['parameters']['letf_benchmark'], q.letf_benchmark)
                self.assertEqual(report['verdict'], 'NOT_RUN')
                interpretation = next(s for s in report['sections'] if s['type'] == 'letf_interpretation')
                self.assertEqual(interpretation['assumptions'], lt['assumptions'])
                table = self.pane.tables['AZ variance proxies · bp']
                self.assertEqual(table.columnCount(), 7)
                for language in ('ko', 'en'):
                    self.window.set_language(language)
                    self.assertEqual(table.horizontalHeaderItem(3).text(), '펀딩 항' if language == 'ko' else 'Funding term')
                    self.assertEqual(table.horizontalHeaderItem(4).text(), '보수 가정 항' if language == 'ko' else 'Fee assumption term')
                    for i, row in enumerate(lt['rows']):
                        self.assertEqual([table.item(i, c).text() for c in range(1, 7)],
                                         [fmt(row[k]) for k in ('drag_bp', 'variance_bp', 'funding_bp',
                                                               'fee_bp', 'dividend_bp', 'reference_drag_bp')])
                    self.assertEqual(self.pane.report, report)
                    disclosure = next(x for x in self.pane.findChildren(UiLabel) if x.source_text == letf_text(lt))
                    self.assertEqual(disclosure.text(), letf_korean(lt) if language == 'ko' else letf_text(lt))
                if q.letf_benchmark != 'zero_rate_reference':
                    self.assertIn('관측된 펀드 비용이나 검증된 분배금이 아닙니다', letf_korean(lt))
                    self.assertIn('별도 비교 기준', letf_korean(lt))
                self.pane.clear_result(); self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_legacy_missing_attribution_is_unavailable_not_inferred_zero(self):
        out = execute_etf(ETFRequest(source='synthetic', code='122630'))
        data = deepcopy(out.data)
        for row in data['letf']['rows']:
            for key in ('funding_bp', 'dividend_bp', 'reference_drag_bp'): row.pop(key)
        self.pane.show_result(replace(out, data=data))
        table = self.pane.tables['AZ variance proxies · bp']
        for i in range(table.rowCount()):
            self.assertEqual([table.item(i, c).text() for c in (3, 5, 6)], ['—', '—', '—'])


if __name__ == '__main__': unittest.main()
