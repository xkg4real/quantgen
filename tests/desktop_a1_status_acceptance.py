"""Explicit status captions preserve codes, provider text and report sections."""
import copy
import unittest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from core.i18n import LocaleContext
from core.research.connections import ConnectionOutput, ConnectionRequest
from quantgen_desktop.app import table, table_rows
from quantgen_desktop.connections import ConnectionsPane
from quantgen_desktop.localization import CAPTION_ROLE, LanguageController
from quantgen_desktop.status_language import STATUS_ROLE
from quantgen_desktop.watchlist import _price_tooltip, _reason, _status
from tests.qt_fixture_cleanup import delete_owned_widget


class A1StatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.host = QWidget()
        self.host.ui_language = 'en'
        self.layout = QVBoxLayout(self.host)
        self.addCleanup(delete_owned_widget, self.host)

    def test_status_roles_round_trip_without_touching_cells_or_ids(self):
        grid = table(['Provider', 'Execution', 'Verdict', 'Value'])
        self.layout.addWidget(grid)
        grid._qg_status_columns = {1: 'execution', 2: 'official'}
        rows = [['NOT_RUN', 'COMPLETED', 'NOT_RUN', '-1,234.567'],
                ['Price', 'FUTURE_CODE', 'PARTIAL', '0.00']]
        original = copy.deepcopy(rows)
        table_rows(grid, rows, ids=['run-1', 'run-2'])
        localizer = LanguageController(self.host)
        for language in ('ko', 'en', 'ko', 'en'):
            self.host.ui_language = language
            localizer.apply()
            self.assertEqual(grid.item(0, 1).text(), '완료' if language == 'ko' else 'COMPLETED')
            self.assertEqual(grid.item(0, 2).text(), '미실행(NOT_RUN)' if language == 'ko' else 'NOT_RUN')
            self.assertEqual(grid.item(1, 2).text(), '부분(PARTIAL)' if language == 'ko' else 'PARTIAL')
            self.assertEqual(grid.item(1, 1).text(), 'FUTURE_CODE')
            self.assertEqual(grid.item(0, 2).toolTip(), 'NOT_RUN')
            self.assertEqual(grid.item(0, 2).data(STATUS_ROLE), 'NOT_RUN')
            self.assertEqual(grid.item(0, 2).data(Qt.ItemDataRole.UserRole), 'run-1')
            for i in range(2):
                for j in (0, 3):
                    self.assertEqual(grid.item(i, j).text(), rows[i][j])
        self.assertEqual(rows, original)

    def test_new_rows_do_not_reuse_prior_status_codes(self):
        grid = table(['Status'])
        grid._qg_status_columns = {0: 'official'}
        self.layout.addWidget(grid)
        self.host.ui_language = 'ko'
        table_rows(grid, [['NOT_RUN']])
        table_rows(grid, [['BLOCKED']])
        self.assertEqual(grid.item(0, 0).text(), '차단(BLOCKED)')
        self.assertEqual(grid.item(0, 0).toolTip(), 'BLOCKED')

    def test_connection_display_keeps_source_rows_and_sections(self):
        pane = ConnectionsPane()
        self.layout.addWidget(pane)
        output = ConnectionOutput(ConnectionRequest(), (
            ('CONFIGURED', 'CONFIGURED', 'SETTING_NAME', 'Provider source text'),
            ('NOT_RUN', 'NOT_CONFIGURED', '', 'unmodified')))
        pane.show_result(output)
        sections = copy.deepcopy(pane.sections)
        localizer = LanguageController(self.host)
        grid = pane.tables['연결 상태']
        for language in ('ko', 'en'):
            self.host.ui_language = language
            localizer.apply()
            self.assertEqual(grid.item(0, 1).text(), '설정 있음' if language == 'ko' else 'CONFIGURED')
            self.assertEqual(grid.item(1, 1).toolTip(), 'NOT_CONFIGURED')
            self.assertEqual(grid.item(0, 0).text(), 'CONFIGURED')
            self.assertEqual(grid.item(1, 0).text(), 'NOT_RUN')
            self.assertEqual(grid.item(0, 3).text(), 'Provider source text')
            self.assertEqual(pane.sections, sections)
        self.assertTrue(any('설정의 존재' in section.get('text', '') for section in pane.sections))

    def test_observed_label_retains_daily_scope_and_raw_code(self):
        row = dict(symbol='^GSPC', kind='market_indicator', status='OBSERVED',
                   provider='YFINANCE', value=5000, unit='points', observation_date='2026-11-01')
        original = dict(row)
        ko, en = LocaleContext('ko_KR'), LocaleContext('en_US')
        self.assertEqual(_status(row, ko), '정상 관측')
        self.assertIn('일별 관측', _reason(row, ko))
        self.assertIn('실시간', _reason(row, ko))
        self.assertIn('OBSERVED', _price_tooltip(row, ko))
        self.assertIn('daily', _reason(row, en))
        self.assertEqual(row, original)
        row['status'] = 'STALE'
        self.assertEqual(_status(row, ko), '오래된 자료')
        self.assertIn('최신이 아닙니다', _reason(row, ko))

    def test_explicit_metric_header_does_not_translate_literal_cells(self):
        grid = table(['지표', 'Value'])
        grid.horizontalHeaderItem(0).setData(CAPTION_ROLE, 'Metric')
        self.layout.addWidget(grid)
        table_rows(grid, [['Metric', '1.23']])
        localizer = LanguageController(self.host)
        for language, expected in [('ko', '항목'), ('en', 'Metric')]:
            self.host.ui_language = language
            localizer.apply()
            self.assertEqual(grid.horizontalHeaderItem(0).text(), expected)
            self.assertEqual(grid.item(0, 0).text(), 'Metric')
            self.assertEqual(grid.item(0, 1).text(), '1.23')


if __name__ == '__main__':
    unittest.main()
