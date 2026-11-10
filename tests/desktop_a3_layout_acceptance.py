"""Result layouts expose all rows without changing synthetic research evidence."""
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent, QPoint, Qt
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

    @staticmethod
    def mc_geometry(window):
        scroll = window.stack.currentWidget()
        controls = (('source', window.source), ('model', window.model), ('drift', window.drift),
                    ('horizon', window.horizon), ('paths', window.paths), ('seed', window.seed),
                    ('erp', window.erp))
        child_hints = ','.join(f'{name}:{widget.minimumSizeHint().width()}/{widget.width()}'
                               for name, widget in controls)
        return (f'window={window.width()} language={window.ui_language} '
                f'viewport={scroll.viewport().width()} content={scroll.widget().width()} '
                f'tabs_min={window.quant_tabs.minimumSizeHint().width()} '
                f'mc_min={window.quant_tabs.widget(0).minimumSizeHint().width()} '
                f'strategy_min={window.strategy.minimumSizeHint().width()} '
                f'strategy_explicit_min={window.strategy.minimumWidth()} '
                f'config_min={window.quant_form.parentWidget().minimumSizeHint().width()} '
                f'form_width={window.quant_form.width()} columns={window.quant_form.columns} '
                f'result_min={window.quant_metrics.parentWidget().minimumSizeHint().width()} '
                f'control_min/width=[{child_hints}]')

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
                            self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(), 0,
                                             self.mc_geometry(w))
                            self.assertEqual(self.values(w.quant_metrics), expected_values)
                            self.assertEqual(w.quant_notes.source_text, raw)
                            self.assertFalse(w.quant_notes.isHidden())
                            self.assertIn('assumed fixture rate', w.quant_notes.text())
                            self.assertIn('NOT_RUN', w.analysis_status.text())
                            self.assertEqual(export_bytes(output.run), run)
                            self.assertEqual(w.commentary_sources(), payload)

    def test_inactive_strategy_minimum_does_not_widen_monte_carlo(self):
        w = self.window
        output = self.put_analysis('gbm')
        values = self.values(w.quant_metrics)
        run = export_bytes(output.run)
        payload = deepcopy(w.commentary_sources())
        # Native font/style hints can make the inactive Strategy form wider.
        # Use an explicit width to reproduce that layout contract on every OS.
        w.strategy.setMinimumWidth(1800)
        with patch.object(w.jobs, 'start', side_effect=AssertionError('no recompute')):
            for width in (1000, 1360, 1000):
                w.resize(width, 1000)
                for language in ('en', 'ko'):
                    w.set_language(language)
                    self.settle()
                    self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(), 0,
                                     self.mc_geometry(w))
                    viewport = w.stack.currentWidget().viewport()
                    for widget in (w.quant_study, w.quant_metrics):
                        left = widget.mapTo(viewport, QPoint(0, 0)).x()
                        self.assertGreaterEqual(left, 0)
                        self.assertLessEqual(left + widget.width(), viewport.width(),
                                             self.mc_geometry(w))
                    self.assert_all_rows_visible(w.quant_metrics)
                    self.assertEqual(self.values(w.quant_metrics), values)
                    self.assertEqual(export_bytes(output.run), run)
                    self.assertEqual(w.commentary_sources(), payload)
            # Respect the same constraint when its own page is selected.
            w.quant_tabs.setCurrentWidget(w.strategy)
            self.settle()
            self.assertGreater(w.stack.currentWidget().horizontalScrollBar().maximum(), 0)
            w.quant_tabs.setCurrentIndex(0)
            self.settle()
            self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(), 0,
                             self.mc_geometry(w))

    def test_mc_wide_option_captions_preserve_choices_without_page_overflow(self):
        w = self.window
        output = self.put_analysis('gbm')
        # Owner issues 04/12 (2026-11-10): the data source is chosen by the app; its selector is hidden.
        self.assertTrue(w.source.isHidden()); self.assertNotIn(w.source, [c for _, c in w.quant_form.fields])
        controls = (w.model, w.drift)
        choices = [[combo.itemData(i) for i in range(combo.count())] for combo in controls]
        selection = [combo.currentData() for combo in controls]
        values = self.values(w.quant_metrics)
        run = export_bytes(output.run)
        payload = deepcopy(w.commentary_sources())
        # Wider native font/style metrics grow content-driven option hints.
        # Long synthetic captions exercise that same Qt width path on every OS,
        # without requiring an installed Windows font or changing option data.
        for combo in controls:
            index = combo.currentIndex()
            combo.setItemText(index, combo.itemText(index) + ' · wide native option caption ' * 5)
            # A native font/style change invalidates Qt's first-show cached
            # hint without overriding the production sizing policy.
            combo.setStyleSheet('QComboBox { font-size: 14px; }')
            combo.updateGeometry()
        with patch.object(w.jobs, 'start', side_effect=AssertionError('no recompute')):
            for width in (1000, 1360, 1000):
                w.resize(width, 1000)
                for language in ('ko', 'en'):
                    w.set_language(language)
                    self.settle()
                    scroll = w.stack.currentWidget()
                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0, self.mc_geometry(w))
                    for combo, data, selected in zip(controls, choices, selection):
                        self.assertEqual([combo.itemData(i) for i in range(combo.count())], data)
                        self.assertEqual(combo.currentData(), selected)
                        self.assertEqual(combo.toolTip(), combo.currentText())
                        self.assertEqual(combo.view().model().index(combo.currentIndex(), 0).data(),
                                         combo.currentText())
                    for widget in (w.symbol, w.model, w.drift, w.horizon, w.paths,
                                   w.seed, w.erp, w.target, w.quant_study, w.quant_metrics):
                        left = widget.mapTo(scroll.viewport(), QPoint(0, 0)).x()
                        self.assertGreaterEqual(left, 0)
                        self.assertLessEqual(left + widget.width(), scroll.viewport().width(),
                                             self.mc_geometry(w))
                        self.assertGreaterEqual(widget.width(), widget.minimumSizeHint().width())
                    self.assert_all_rows_visible(w.quant_metrics)
                    self.assertEqual(self.values(w.quant_metrics), values)
                    self.assertEqual(export_bytes(output.run), run)
                    self.assertEqual(w.commentary_sources(), payload)

    def test_mc_larger_combo_fonts_reflow_and_keep_field_order_and_evidence(self):
        w = self.window
        output = self.put_analysis('gbm')
        controls = (w.symbol, w.model, w.drift, w.horizon, w.paths,
                    w.seed, w.erp, w.target)
        values = self.values(w.quant_metrics)
        run = export_bytes(output.run)
        payload = deepcopy(w.commentary_sources())
        selection = [combo.currentData() for combo in (w.model, w.drift)]
        for combo in (w.model, w.drift):
            combo.setStyleSheet('QComboBox { font-size: 18px; }')
        with patch.object(w.jobs, 'start', side_effect=AssertionError('no recompute')):
            for width in (1000, 1360, 1000):
                w.resize(width, 1000)
                for language in ('en', 'ko'):
                    w.set_language(language)
                    self.settle()
                    scroll = w.stack.currentWidget()
                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0, self.mc_geometry(w))
                    columns = w.quant_form.columns
                    if width == 1360:
                        self.assertEqual(columns, 3, self.mc_geometry(w))
                    # Native font metrics choose the narrow column count; the
                    # strict viewport/minimum checks must hold on every OS.
                    self.assertEqual([control for _, control in w.quant_form.fields], list(controls))
                    for index, (caption, control) in enumerate(w.quant_form.fields):
                        row, column = (index // columns) * 2, index % columns
                        self.assertIs(w.quant_form.grid.itemAtPosition(row, column).widget(), caption)
                        self.assertIs(w.quant_form.grid.itemAtPosition(row + 1, column).widget(), control)
                        left = control.mapTo(scroll.viewport(), QPoint(0, 0)).x()
                        self.assertGreaterEqual(left, 0)
                        self.assertLessEqual(left + control.width(), scroll.viewport().width())
                        self.assertGreaterEqual(control.width(), control.minimumSizeHint().width())
                        self.assertLessEqual(control.y() + control.height(), w.quant_form.height())
                    controls[0].setFocus()
                    self.settle()
                    for current, following in zip(controls, (*controls[1:], w.run_button)):
                        self.assertIs(self.app.focusWidget(), current)
                        QTest.keyClick(current, Qt.Key.Key_Tab)
                    self.assertIs(self.app.focusWidget(), w.run_button)
                    self.assertEqual([combo.currentData() for combo in (w.model, w.drift)], selection)
                    self.assertEqual(self.values(w.quant_metrics), values)
                    self.assertEqual(export_bytes(output.run), run)
                    self.assertEqual(w.commentary_sources(), payload)
        # A single field's real native minimum is sufficient for the final
        # one-column layout; larger constraints are never silently suppressed.
        minimum = w.quant_form.minimumSizeHint().width()
        self.assertEqual(w.quant_form.columns_for_width(minimum), 1)
        self.assertGreaterEqual(minimum, max(control.minimumSizeHint().width() for control in controls))

    def test_mc_field_grid_reuses_one_two_three_and_one_columns_without_clipping(self):
        from PyQt6.QtWidgets import QLabel, QLineEdit
        from quantgen_desktop.result_layout import ResponsiveFieldGrid
        fields = [(QLabel(f'Field {index}'), QLineEdit(str(index))) for index in range(9)]
        for _, control in fields:
            control.setMinimumWidth(250)
        form = ResponsiveFieldGrid(fields)
        self.addCleanup(form.deleteLater)
        form.show()
        for width, columns in ((260, 1), (550, 2), (850, 3), (260, 1)):
            form.resize(width, 1000)
            self.settle()
            self.assertEqual(form.columns, columns)
            for index, (caption, control) in enumerate(fields):
                row, column = (index // columns) * 2, index % columns
                self.assertIs(form.grid.itemAtPosition(row, column).widget(), caption)
                self.assertIs(form.grid.itemAtPosition(row + 1, column).widget(), control)
                self.assertEqual(control.text(), str(index))
                self.assertGreaterEqual(control.width(), 250)
                self.assertGreaterEqual(control.x(), 0)
                self.assertLessEqual(control.x() + control.width(), form.width())
                self.assertLessEqual(control.y() + control.height(), form.height())

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
