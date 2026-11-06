"""Local reading interactions with synthetic displayed values and no external I/O."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent, QPoint, QRect, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from core.education import glossary
from core.i18n import LocaleContext
from core.research.tool_export import report_bytes
from quantgen_desktop.commentary import commentary_payload
from quantgen_desktop.localization import LanguageController
from quantgen_desktop.reading_panel import DetailsFold, install_reading_help
from quantgen_desktop.tools import ToolPane


class ReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.insights.deep_analysis',
                       'core.quant.validate.load_cards', 'core.quant.gate_ledger.family_ledger'):
            deny = patch(target, side_effect=AssertionError('Reading must not call engines, AI or stores'))
            deny.start()
            self.addCleanup(deny.stop)

    def settle(self):
        for _ in range(4):
            self.app.processEvents()
            QTest.qWait(5)

    def host(self, width=1000):
        from core.theme import LIGHT
        window = QMainWindow()
        window.colors = LIGHT
        window.ctx = LocaleContext('en_US')
        window.ui_language = 'en'
        root = QWidget()
        window.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        rail = QWidget()
        rail.setFixedWidth(150)
        outer.addWidget(rail)
        window.stack = QStackedWidget()
        outer.addWidget(window.stack, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        pane = ToolPane('Fixture', [('fixture', 'Fixture')], [('synthetic', 'Synthetic')], {'fixture': []})
        pane.input_box.hide()
        pane.export_json.hide()
        pane.export_zip.hide()
        layout.addWidget(pane)
        layout.addStretch()
        scroll.setWidget(content)
        window.stack.addWidget(scroll)
        window.stack.addWidget(QWidget())
        window.localizer = LanguageController(window)
        helper = install_reading_help(window)
        self.assertIs(helper, install_reading_help(window))
        window.resize(width, 800)
        window.show()
        self.settle()
        def cleanup():
            helper.close(restore=False)
            window.hide()
            window.deleteLater()
            self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
        self.addCleanup(cleanup)
        return window, pane, helper

    def rows(self, pane):
        pane.result_table('Metrics', ['Metric', 'Value'],
                          [['Macaulay duration', '3.000%'], ['Convexity', '−0.00'], ['DV01', '—']])
        return pane.tables['Metrics']

    def locale(self, window, helper, code):
        window.ctx = LocaleContext(code)
        window.ui_language = window.ctx.language
        window.localizer.apply()
        helper.set_locale(window.ctx)
        self.settle()

    def test_only_explicit_provenance_folds_and_sections_stay_identical(self):
        window, pane, helper = self.host()
        visible = []
        roles = (None, 'unknown', 'notice', 'assumption', 'synthetic', 'delayed', 'failure')
        for role in roles:
            visible.append(pane.text('Synthetic / delayed / failure / assumed rate 3% · '+str(role), display_role=role))
        source = pane.text('Fixture provider · 2026-11-06', display_role='provenance')
        before = deepcopy(pane.sections)
        self.settle()
        fold = pane.findChild(DetailsFold)
        self.assertIsNotNone(fold)
        self.assertFalse(source.isVisible())
        for widget in visible:
            self.assertTrue(widget.isVisible())
            self.assertTrue(widget.property('reading_help_keep_visible'))
        for code in ('ko_KR', 'en_US'):
            self.locale(window, helper, code)
            fold.toggle.setChecked(True)
            self.assertTrue(source.isVisible())
            fold.toggle.setChecked(False)
            for widget in visible:
                self.assertTrue(widget.isVisible())
        self.assertEqual(pane.sections, before)
        self.assertFalse(any('display_role' in section for section in pane.sections))

    def test_screen_quotes_are_exact_and_report_and_ai_payload_are_unchanged(self):
        window, pane, helper = self.host(1360)
        table = self.rows(pane)
        pane.text('Fixture provider · 2026-11-06', display_role='provenance')
        report = {'format': 'quantgen.analysis-report/1', 'tool': 'bonds',
                  'execution_status': 'COMPLETED', 'verdict': 'NOT_RUN',
                  'parameters': {'source': 'synthetic'}, 'sections': deepcopy(pane.sections)}
        pane.report = report
        before = (json.dumps(pane.sections), report_bytes(report), json.dumps(commentary_payload(report)))
        self.settle()
        for row, value in enumerate(('3.000%', '−0.00', '—')):
            table.setCurrentCell(row, 1)
            self.assertTrue(helper.open_for(table))
            self.assertEqual(helper.panel.quote.text(), table.item(row, 0).text()+' | '+value)
            helper.panel.search.setText('duration')
            helper.panel.choose('duration')
            for code in ('ko_KR', 'en_US'):
                self.locale(window, helper, code)
                self.assertTrue(helper.panel.quote.text().endswith(' | '+value))
            helper.close()
        fold = pane.findChild(DetailsFold)
        fold.toggle.setChecked(True)
        fold.toggle.setChecked(False)
        self.assertEqual(before, (json.dumps(pane.sections), report_bytes(report), json.dumps(commentary_payload(report))))

    def test_f1_search_escape_and_close_restore_the_original_cell(self):
        window, pane, helper = self.host()
        table = self.rows(pane)
        table.setCurrentCell(1, 1)
        table.setFocus()
        self.settle()
        QTest.keyClick(table, Qt.Key.Key_F1)
        self.settle()
        self.assertTrue(helper.panel.isVisible(), helper.last_notice)
        self.assertIs(self.app.focusWidget(), helper.panel.search)
        self.assertEqual(helper.panel.search.text(), table.item(1, 0).text())
        QTest.keyClick(helper.panel.search, Qt.Key.Key_Escape)
        self.settle()
        self.assertFalse(helper.panel.isVisible())
        self.assertIs(self.app.focusWidget(), table)
        self.assertEqual((table.currentRow(), table.currentColumn()), (1, 1))
        helper.open_for(table)
        table.setFocus()
        QTest.keyClick(table, Qt.Key.Key_Escape)
        self.settle()
        self.assertFalse(helper.panel.isVisible())
        helper.open_for(table)
        helper.panel.close_button.click()
        self.assertIs(self.app.focusWidget(), table)
        self.assertEqual(helper.panel.quote.text(), '')

    def test_glossary_definitions_candidates_and_unknown_are_existing_only(self):
        window, pane, helper = self.host()
        table = self.rows(pane)
        table.setCurrentCell(0, 0)
        helper.open_for(table)
        for code in ('en_US', 'ko_KR'):
            self.locale(window, helper, code)
            for query in ('duration', '듀레이션', 'VaR', 'CVaR'):
                helper.panel.search.setText(query)
                for index in range(helper.panel.matches.count()):
                    self.assertIn(helper.panel.matches.item(index).data(Qt.ItemDataRole.UserRole), glossary.BY_KEY)
                self.assertIsNone(helper.panel.term_key)  # selection is explicit
            helper.panel.choose('duration')
            actual = tuple((heading.text(), body.text()) for heading, body in helper.panel.sections if not heading.isHidden())
            self.assertEqual(actual, glossary.sections('duration', window.ctx))
        helper.panel.search.setText('zzzz-unlisted-term')
        self.assertEqual(helper.panel.matches.count(), 0)
        self.assertIsNone(helper.panel.term_key)
        self.assertIn('용어집', helper.panel.message.text())

    def test_wide_dock_narrow_overlay_never_changes_narrow_body_width_or_covers_notice(self):
        window, pane, helper = self.host()
        notice = pane.text('SYNTHETIC · Assumed rate 3%; delayed fixture data', display_role='assumption')
        table = self.rows(pane)
        table.setCurrentCell(0, 0)
        self.settle()
        scroll = window.stack.currentWidget()
        before = (scroll.viewport().width(), scroll.widget().width(), scroll.verticalScrollBar().value())
        for mode in ('light', 'dark'):
            window.setStyleSheet('QFrame#panel { background: '+('#fafafa' if mode == 'light' else '#1b2a23')+'; }')
            for code in ('ko_KR', 'en_US'):
                self.locale(window, helper, code)
                self.assertTrue(helper.open_for(table), helper.last_notice)
                self.settle()
                self.assertEqual(helper.mode, 'overlay')
                self.assertEqual(helper.panel.width(), 340)
                self.assertEqual(before, (scroll.viewport().width(), scroll.widget().width(), scroll.verticalScrollBar().value()))
                rect = QRect(notice.mapTo(window.centralWidget(), QPoint(0, 0)), notice.size())
                self.assertFalse(helper.panel.geometry().intersects(rect))
                status_rect = QRect(pane.status.mapTo(window.centralWidget(), QPoint(0, 0)), pane.status.size())
                self.assertFalse(helper.panel.geometry().intersects(status_rect))
                helper.close()
        window.resize(1360, 800)
        self.settle()
        self.assertTrue(helper.open_for(table))
        self.settle()
        self.assertEqual(helper.mode, 'docked')
        self.assertEqual(helper.panel.width(), 340)
        self.assertGreaterEqual(window.centralWidget().layout().indexOf(helper.panel), 0)

    def test_no_safe_overlay_space_keeps_notice_and_body_and_explains(self):
        window, pane, helper = self.host()
        table = self.rows(pane)
        table.setCurrentCell(0, 0)
        scroll = window.stack.currentWidget()
        notice = QLabel('SYNTHETIC · failure · assumptions', scroll.viewport())
        notice.setProperty('reading_help_keep_visible', True)
        notice.setGeometry(scroll.viewport().rect())
        notice.show()
        before = scroll.viewport().width()
        self.assertFalse(helper.open_for(table))
        self.assertFalse(helper.panel.isVisible())
        self.assertTrue(notice.isVisible())
        self.assertEqual(scroll.viewport().width(), before)
        self.assertIn('important notices', helper.last_notice)

    def test_result_reset_page_change_and_destroyed_origin_clear_stale_quotes(self):
        window, pane, helper = self.host()
        table = self.rows(pane)
        table.setCurrentCell(0, 0)
        helper.open_for(table)
        pane.clear_result()
        self.settle()
        self.assertFalse(helper.panel.isVisible())
        self.assertEqual(helper.panel.quote.text(), '')
        table = self.rows(pane)
        table.setCurrentCell(0, 0)
        helper.open_for(table)
        window.stack.setCurrentIndex(1)
        self.assertFalse(helper.panel.isVisible())
        self.assertEqual(helper.panel.quote.text(), '')
        window.stack.setCurrentIndex(0)
        helper.open_for(table)
        table.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        helper.close()  # no access to a deleted C++ widget
        self.assertEqual(helper.panel.quote.text(), '')

    def test_same_row_result_replacement_clears_previous_quote_without_report_mutation(self):
        window, pane, helper = self.host(1360)
        table = self.rows(pane)
        before = deepcopy(pane.sections)
        table.setCurrentCell(0, 1)
        helper.open_for(table)
        table.item(0, 1).setText('9.999%')
        self.settle()
        self.assertFalse(helper.panel.isVisible())
        self.assertEqual(helper.panel.quote.text(), '')
        self.assertEqual(pane.sections, before)
        helper.open_for(table)
        self.assertIn('9.999%', helper.panel.quote.text())

    def test_same_size_selected_prose_replacement_clears_previous_quote(self):
        _window, pane, helper = self.host(1360)
        label = pane.text('DV01 3.000%')
        self.settle()
        label.setSelection(0, len(label.text()))
        helper.open_for(label)
        label.setText('DV01 9.999%')
        self.settle()
        self.assertFalse(helper.panel.isVisible())
        self.assertEqual(helper.panel.quote.text(), '')
        self.assertEqual(label.source_text, 'DV01 9.999%')

    def test_context_snapshot_and_locale_do_not_change_original_return_cell(self):
        window, pane, helper = self.host(1360)
        table = self.rows(pane)
        table.setCurrentCell(0, 1)
        helper.open_for(table)
        table.setCurrentCell(2, 0)
        # The context-menu copy path may inspect a different currently selected
        # row; it must not overwrite the F1 origin or the panel's quoted row.
        helper._snapshot(table)
        self.locale(window, helper, 'ko_KR')
        self.assertTrue(helper.panel.quote.text().endswith(' | 3.000%'))
        helper.close()
        self.assertEqual((table.currentRow(), table.currentColumn()), (0, 1))

    def test_actual_bonds_fixture_opens_narrow_and_tool_switch_or_reset_clears_context(self):
        from quantgen_desktop.app import ResearchWindow
        from core.research.bond_analysis import BondRequest
        from tests.desktop_acceptance import bond_fixture
        window = ResearchWindow(auto_refresh=False, language='en')
        helper = install_reading_help(window)
        def cleanup():
            helper.close(restore=False)
            window.hide()
            window.deleteLater()
            self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.addCleanup(cleanup)
        window.bonds.show_result(bond_fixture(BondRequest(source='synthetic')))
        window.show_market_pane(window.bonds)
        window.resize(1000, 800)
        window.show()
        self.settle()
        table = window.bonds.metrics
        table.setCurrentCell(2, 1)
        table.setFocus()
        scroll = window.stack.currentWidget()
        before = (scroll.viewport().width(), scroll.verticalScrollBar().value())
        QTest.keyClick(table, Qt.Key.Key_F1)
        self.settle()
        self.assertTrue(helper.panel.isVisible(), helper.last_notice)
        self.assertEqual(helper.mode, 'overlay')
        self.assertEqual(before, (scroll.viewport().width(), scroll.verticalScrollBar().value()))
        QTest.keyClick(helper.panel.search, Qt.Key.Key_Escape)
        self.settle()
        self.assertIs(self.app.focusWidget(), table)
        helper.open_for(table)
        window.show_tool(window.rates)
        self.assertFalse(helper.panel.isVisible())
        self.assertEqual(helper.panel.quote.text(), '')
        window.show_tool(window.bonds)
        helper.open_for(table)
        window.bonds.clear_result()
        self.assertFalse(helper.panel.isVisible())
        self.assertEqual(helper.panel.quote.text(), '')

    def test_actual_macro_collapses_only_provider_date_and_preserves_warning_report_and_ai(self):
        from quantgen_desktop.macro import MacroPane
        from quantgen_desktop.localization import UiLabel
        from tests.desktop_macro_language_acceptance import output
        window, _pane, helper = self.host()
        scroll = window.stack.currentWidget()
        pane = MacroPane()
        scroll.widget().layout().insertWidget(0, pane)
        out = output('weekly', synthetic=True, short=True)
        pane.show_result(out)
        pane.bind_output('macro', out)
        source = next(label for label in pane.findChildren(UiLabel)
                      if label.property('display_role') == 'provenance')
        fold = pane.findChild(DetailsFold)
        before = (deepcopy(pane.sections), report_bytes(pane.report), json.dumps(commentary_payload(pane.report)))
        self.settle()
        self.assertFalse(source.isVisible())
        for code in ('ko_KR', 'en_US'):
            self.locale(window, helper, code)
            for label in pane.findChildren(UiLabel):
                if label.property('reading_help_keep_visible'):
                    self.assertTrue(label.isVisible(), label.source_text)
            self.assertTrue(any('SYNTHETIC' in label.source_text or '합성 데이터 포함' in label.source_text
                                for label in pane.findChildren(UiLabel)
                                if label.property('reading_help_keep_visible') and label.isVisible()))
            self.assertTrue(any('35 obs' in label.source_text for label in pane.findChildren(UiLabel)
                                if label.property('reading_help_keep_visible') and label.isVisible()))
            fold.toggle.setChecked(True)
            self.assertTrue(source.isVisible())
            fold.toggle.setChecked(False)
        self.assertEqual(before, (pane.sections, report_bytes(pane.report), json.dumps(commentary_payload(pane.report))))


if __name__ == '__main__':
    unittest.main()
