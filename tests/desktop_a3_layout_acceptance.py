"""Result layouts expose all rows without changing synthetic research evidence."""
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from tests.desktop_acceptance import bond_fixture, fixture_runner
from core.research.analysis import AnalysisRequest
from core.research.bond_analysis import BondRequest
from core.research.runs import export_bytes, new_run
from quantgen_desktop.app import ResearchWindow


class A3ResultLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for name in ('requests.sessions.Session.request', 'core.quant.validate.load_cards',
                     'core.quant.gate_ledger.family_ledger'):
            guard = patch(name, side_effect=AssertionError('external I/O forbidden'))
            guard.start(); self.addCleanup(guard.stop)
        self.window = ResearchWindow(auto_refresh=False, language='en')
        self.window.resize(1360, 1000)
        self.window.show()
        self.addCleanup(self.dispose)

    def dispose(self):
        self.window.hide()
        self.window.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def settle(self):
        for _ in range(6):
            self.app.processEvents()
            QTest.qWait(2)

    def assert_all_rows_visible(self, table):
        self.assertEqual(table.verticalScrollBar().maximum(), 0,
                         f'height={table.height()} viewport={table.viewport().height()} '
                         f'header={table.horizontalHeader().height()} frame={table.frameWidth()} '
                         f'rows={[table.rowHeight(r) for r in range(table.rowCount())]}')
        self.assertEqual(table.horizontalScrollBar().maximum(), 0)
        if table.rowCount():
            last = table.visualRect(table.model().index(table.rowCount() - 1, 0))
            self.assertGreaterEqual(last.top(), 0)
            self.assertLessEqual(last.bottom(), table.viewport().height())
            self.assertTrue(table.item(0, 1).textAlignment() & Qt.AlignmentFlag.AlignRight)

    @staticmethod
    def values(table):
        return [table.item(row, 1).text() for row in range(table.rowCount())]

    def put_analysis(self, model):
        request = AnalysisRequest(symbol='TEST', source_requested='synthetic', model=model,
                                  n_paths=200, horizon_days=5, seed=19, drift='premium')
        output = fixture_runner(request, new_run(request.parameters()))
        self.window.pending = 'analysis'
        self.window.job_succeeded(output)
        self.window.navigate('quant')
        return output

    def test_mc_title_chart_and_all_seven_or_eight_rows_keep_evidence(self):
        w = self.window
        for model, count in (('gbm', 7), ('garch_t', 8)):
            with self.subTest(model=model):
                output = self.put_analysis(model)
                expected_values = self.values(w.quant_metrics)
                raw = w.quant_notes.source_text
                run = export_bytes(output.run)
                payload = deepcopy(w.commentary_sources())
                layout = w.quant_metrics.parentWidget().layout()
                self.assertEqual(layout.itemAt(0).widget().source_text, '분포와 근거')
                self.assertLess(layout.indexOf(w.quant_study), layout.indexOf(w.quant_metrics))
                self.assertEqual(w.quant_metrics.rowCount(), count)
                with patch.object(w.jobs, 'start', side_effect=AssertionError('no recompute')):
                    for width in (1360, 1000, 1360):
                        w.resize(width, 1000)
                        for language in ('ko', 'en'):
                            w.set_language(language)
                            self.settle(); w.grab(); self.settle()
                            self.assert_all_rows_visible(w.quant_metrics)
                            self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(), 0)
                            self.assertEqual(self.values(w.quant_metrics), expected_values)
                            self.assertEqual(w.quant_notes.source_text, raw)
                            self.assertFalse(w.quant_notes.isHidden())
                            self.assertIn('assumed fixture rate', w.quant_notes.text())
                            self.assertIn('NOT_RUN', w.analysis_status.text())
                            self.assertEqual(export_bytes(output.run), run)
                            self.assertEqual(w.commentary_sources(), payload)

    def test_bond_panels_reflow_and_retain_tables_chart_report_and_payload(self):
        w, pane = self.window, self.window.bonds
        output = bond_fixture(BondRequest(source='synthetic', tool='scenarios'))
        pane.show_result(output)
        w.navigate('tools'); w.show_tool(pane)
        before = deepcopy(pane.exports.report)
        payload = deepcopy(w.commentary_sources())
        raw = pane.notes.source_text
        values = [self.values(t) for t in (pane.metrics, pane.krd)]
        series = deepcopy(pane.chart.series)
        self.assertEqual(pane.metrics.rowCount(), 12)
        self.assertEqual(pane.krd.rowCount(), len(output.analytics.krd))
        with patch.object(w.jobs, 'start', side_effect=AssertionError('no recompute')):
            for width in (1360, 1000, 1360):
                w.resize(width, 1000)
                for dark in (0, 1):
                    w.theme.setCurrentIndex(dark)
                    for language in ('ko', 'en'):
                        w.set_language(language)
                        self.settle(); pane.grab(); self.settle()
                        first, second = pane.result_panels.panels
                        wide = pane.result_panels.width() >= pane.result_panels.breakpoint
                        if wide:
                            self.assertGreater(second.x(), first.x())
                            self.assertEqual(first.height(), second.height())
                        else:
                            self.assertGreater(second.y(), first.y())
                        self.assertEqual(wide, width == 1360)
                        for table in (pane.metrics, pane.krd):
                            self.assert_all_rows_visible(table)
                        self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(), 0)
                        self.assertEqual([self.values(t) for t in (pane.metrics, pane.krd)], values)
                        self.assertEqual(pane.exports.report, before)
                        self.assertEqual(w.commentary_sources(), payload)
                        self.assertEqual(pane.chart.series, series)
                        self.assertEqual(pane.notes.source_text, raw)
                        self.assertFalse(pane.notes.isHidden())
                        self.assertTrue('SYNTHETIC' in raw or '합성' in raw)
                        # The chart title is the first child, before the study.
                        self.assertEqual(pane.study.parentWidget().layout().indexOf(pane.study), 1)

    def test_larger_font_and_late_empty_results_reserve_real_row_height(self):
        w, pane = self.window, self.window.bonds
        output = bond_fixture(BondRequest(source='synthetic'))
        pane.show_result(output)
        w.navigate('tools'); w.show_tool(pane)
        self.settle()
        small_height = pane.metrics.height()
        values = self.values(pane.metrics)
        pane.metrics.setStyleSheet('QTableWidget {font-size: 24px;} QHeaderView {font-size: 22px;}')
        self.settle(); pane.grab(); self.settle()
        self.assertGreater(pane.metrics.height(), small_height)
        self.assertEqual(self.values(pane.metrics), values)
        self.assert_all_rows_visible(pane.metrics)
        empty = replace(output, analytics=replace(output.analytics, krd={}))
        pane.show_result(empty)
        self.settle()
        self.assertEqual(pane.krd.rowCount(), 0)
        self.assert_all_rows_visible(pane.krd)
        pane.clear_result(); self.settle()
        self.assertEqual(pane.metrics.rowCount(), 0)
        self.assertLess(pane.metrics.height(), small_height)
        self.assertIsNone(pane.exports.report)
        pane.show_result(output); self.settle()
        self.assertEqual(pane.metrics.rowCount(), 12)
        self.assertEqual(pane.krd.rowCount(), len(output.analytics.krd))
        for table in (pane.metrics, pane.krd):
            self.assert_all_rows_visible(table)

    def test_bond_scenarios_and_hedge_remain_available_after_layout_change(self):
        pane = self.window.bonds
        for tool in ('scenarios', 'hedge', 'calc'):
            with self.subTest(tool=tool):
                output = bond_fixture(BondRequest(source='synthetic', tool=tool))
                pane.show_result(output); self.settle()
                self.assertEqual(pane.scenarios.rowCount(), len(output.scenarios))
                self.assertEqual(not pane.scenarios.isHidden(), bool(output.scenarios))
                self.assertEqual(bool(pane.hedge.source_text), bool(output.hedge))
                self.assertEqual(pane.exports.report['tool'], 'bonds')
                if output.hedge:
                    self.assertIn('no real orders', pane.hedge.text())


if __name__ == '__main__':
    unittest.main()
