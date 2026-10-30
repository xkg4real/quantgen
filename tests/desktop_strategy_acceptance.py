"""Native Strategy Lab tests: synthetic histories, no live ledger/card access."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch, Mock
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.research.strategy_analysis import StrategyRequest, execute_strategy
    from core.research import strategy_workflow as flow
    from core.quant import validate as V
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtTest import QTest


class StrategyTests(unittest.TestCase):
    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.gate_ledger.family_ledger',
                       'core.quant.validate.load_cards'):
            p = patch(target, side_effect=AssertionError('live I/O forbidden'))
            p.start(); self.addCleanup(p.stop)

    def test_invalid_requests_reject_before_runner(self):
        runner = Mock(side_effect=AssertionError('runner called'))
        for q in (StrategyRequest(family='bad'), StrategyRequest(symbols=()),
                  StrategyRequest(family='pairs', symbols=('SPY',)), StrategyRequest(cost_bps=-1),
                  StrategyRequest(symbols=('../.env',)), StrategyRequest(days=10)):
            with self.assertRaises(ValueError): execute_strategy(q, runner=runner)
        runner.assert_not_called()

    def test_all_families_use_existing_grid_gate_and_skip_real_registration(self):
        original = deepcopy(V.GATE)
        for family in flow.FAMILIES:
            q = StrategyRequest(family=family, symbols=('SPY', 'QQQ'), cost_bps=50)
            d = execute_strategy(q).data
            self.assertIsNone(d['ledger_n'])
            self.assertEqual(d['score'].n_trials, len(flow.FAMILIES[family][2]))
            self.assertEqual(d['sources'], ['SYNTHETIC', 'SYNTHETIC'])
            self.assertEqual(V.GATE, original)
            self.assertGreater(len(d['equity']), 100)
            if family == 'pairs': self.assertIsNone(d['bench_equity'])

    def test_sensitivity_verdict_withheld_and_global_gate_restored_on_failure(self):
        q = StrategyRequest(symbols=('SPY', 'QQQ'), cost_bps=1)
        d = execute_strategy(q).data
        safe = flow.payload(d)
        self.assertEqual(safe['decision'], 'WITHHELD')
        self.assertNotIn('decision', safe['stats'])
        self.assertIsNone(safe['revise_target'])
        original = deepcopy(V.GATE)
        with patch.object(V, 'score_strategy', side_effect=RuntimeError('fixture scoring failure')):
            with self.assertRaises(RuntimeError): execute_strategy(q)
        self.assertEqual(V.GATE, original)

    def test_failed_registration_stops_scoring_without_touching_real_ledger(self):
        def run(*a, **kw):
            return flow.run_family(*a, **kw, trial_registrar=Mock(side_effect=ValueError('test registration failed')))
        with patch.object(V, 'score_strategy') as score:
            with self.assertRaises(ValueError): execute_strategy(StrategyRequest(), runner=run)
        score.assert_not_called()


class NativeStrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def test_run_export_and_cards_preserve_refusals_and_do_not_autoload(self):
        def runner(q):
            if q.tool == 'cards':
                return execute_strategy(q, cards_loader=lambda: [flow._study_card({'card_id': 'S_FIXTURE',
                    'kind': 'strategy', 'decision': 'REJECT', 'decision_reason': 'fixture rejection', 'lines': ['No approval']})])
            return execute_strategy(q)
        with patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden')), \
             patch('core.quant.gate_ledger.family_ledger', side_effect=AssertionError('ledger forbidden')), \
             patch.object(V, 'load_cards', side_effect=AssertionError('study read forbidden')):
            w = ResearchWindow(auto_refresh=False, strategy_runner=runner)
            try:
                p = w.strategy
                self.assertFalse(p.has_result)
                p.fields['run']['cost'].setText('1')
                p.fields['run']['symbols'].setText('SPY, QQQ')
                p.submit()
                for _ in range(3000):
                    self.app.processEvents()
                    if not w.jobs.busy: break
                    QTest.qWait(10)
                self.assertFalse(w.jobs.busy)
                self.assertTrue(p.has_result, p.status.text())
                self.assertIn('WITHHELD', str(p.sections))
                self.assertEqual(p.report['verdict'], 'NOT_RUN')
                self.assertIn('Walk-forward equity', p.charts)
                p.tool.setCurrentIndex(p.tool.findData('cards'))
                self.assertIsNone(p.report)
                p.submit()
                for _ in range(1000):
                    self.app.processEvents()
                    if not w.jobs.busy: break
                    QTest.qWait(10)
                self.assertFalse(w.jobs.busy)
                self.assertIn('REJECT', str(p.sections))
                self.assertEqual(p.tables['Study scorecard'].rowCount(), 1)
            finally:
                with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes): w.close()
                w.deleteLater(); self.app.processEvents()


if __name__ == '__main__': unittest.main()
