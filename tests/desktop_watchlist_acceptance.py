"""Native watchlist behavior, truthful source metadata and keyboard access."""
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton

from core.i18n import LocaleContext
from core.research.watchlist import default_home_rows
from core.theme import DARK, LIGHT
from quantgen_desktop.watchlist import DETAIL_COLUMN, SCORE_COLUMN, WatchlistPanel


def sample_rows():
    rows = default_home_rows()
    rows[0].update(value=5000, change=1.25, status="OBSERVED", observation_date="2026-10-30",
                   loaded_at="2026-11-02T03:00:00+00:00")
    rows[3].update(value=4.98, change=-7, status="OBSERVED", observation_date="2026-10-30")
    rows[6].update(value=72000, change=1.45, absolute_change=1000, volume=1200000,
                   open=71000, high=72500, low=70500, status="SNAPSHOT",
                   received_at="2026-11-02T12:00:00+09:00", loaded_at="2026-11-02T03:00:01+00:00",
                   market_cap_raw=123456789, market_cap_unit="UNVERIFIED")
    rows[7].update(status="UNAVAILABLE", reason_code="connection_not_configured")
    return rows


def financial_rows():
    rows = sample_rows()
    rows[6].update(market_cap=72_000_000_000, market_cap_unit="KRW", market_cap_basis="price_x_listed_shares",
                   listed_shares=1_000_000, per=12.34, eps=5834, sector="전기전자",
                   fundamentals_received_at="2026-11-02T02:50:00+00:00", fundamentals_as_of=None)
    return rows


class DesktopWatchlistAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("UI must not query providers"))
        self.network = network.start()
        self.addCleanup(network.stop)
        self.panel = WatchlistPanel(locale=LocaleContext("ko_KR"))
        self.panel.resize(1080, 950)
        self.panel.set_rows(sample_rows())
        self.panel.show()
        self.addCleanup(self.panel.close)
        self.addCleanup(self.panel.deleteLater)
        self.drain()

    def drain(self):
        for _ in range(3):
            self.app.processEvents()

    def fields(self, dialog):
        from PyQt6.QtWidgets import QFormLayout
        return {
            dialog.form.itemAt(i, QFormLayout.ItemRole.LabelRole).widget().text():
            dialog.form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget().text()
            for i in range(dialog.form.rowCount())
        }

    def test_twelve_rows_numeric_values_and_truthful_timing(self):
        table = self.panel.table
        self.assertEqual(table.rowCount(), 12)
        self.assertEqual(table.item(6, 0).text(), "삼성전자")
        self.assertEqual(table.item(6, 0).data(Qt.ItemDataRole.UserRole), "005930")
        from PyQt6.QtWidgets import QStyleOptionViewItem
        option = QStyleOptionViewItem()
        table.itemDelegateForColumn(0).initStyleOption(option, table.model().index(6, 0))
        self.assertEqual(option.text, "")  # The ticker/name widget is the only visible name.
        self.assertEqual(table.item(6, 1).text(), "72,000 KRW")
        self.assertEqual(table.item(6, 2).text(), "+1.45%")
        self.assertEqual(table.item(3, 2).text(), "-7.00 bp")
        self.assertEqual(table.item(6, 3).text(), "120만")
        self.assertEqual(table.item(7, 1).text(), "—")
        self.assertIn("관측", table.item(0, 1).toolTip())
        self.assertIn("수신", table.item(6, 1).toolTip())
        self.assertIn("UTC", table.item(6, 1).toolTip())
        self.assertIn("조회 시세", table.item(6, 1).toolTip())
        self.assertIn("일별 관측", table.item(0, 1).toolTip())
        self.assertEqual(self.panel.rows[6]["observation_date"], None)
        self.network.assert_not_called()

    def test_details_buttons_and_stock_chart_route_only(self):
        routes = []
        self.panel.chart_requested.connect(routes.append)
        self.panel.table.cellWidget(6, DETAIL_COLUMN).click()
        self.drain()
        dialog = self.panel.detail_dialog
        self.assertTrue(dialog.isVisible())
        self.assertIn("삼성전자", dialog.windowTitle() + dialog.title.text())
        fields = self.fields(dialog)
        self.assertNotIn("관측일", fields); self.assertNotIn("공급처", fields)  # owner, 2026-11-04
        self.assertEqual(fields["시가총액"], "확인 안 됨")
        self.assertNotIn("123456789", " ".join(fields.values()))
        self.assertIn("UTC", fields["수신 시각"])
        self.assertIn("시장 체결 시각", dialog.notice.text())
        dialog.chart_button.click()
        self.assertEqual(routes, ["005930"])
        macro = self.panel.open_detail(1)  # KOSPI is on a KRX route but is not a stock code.
        self.assertFalse(macro.chart_button.isVisible())
        macro.open_chart()
        self.assertEqual(routes, ["005930"])
        self.network.assert_not_called()

    def test_keyboard_and_double_click_open_selected_instrument(self):
        self.panel.table.setCurrentCell(8, 0)
        self.panel.table.setFocus()
        QTest.keyClick(self.panel.table, Qt.Key.Key_Return)
        self.drain()
        self.assertEqual(self.panel.detail_dialog.row["symbol"], "005380")
        self.panel.detail_dialog.close()
        self.drain()
        target = self.panel.table.visualItemRect(self.panel.table.item(9, 0)).center()
        QTest.mouseClick(self.panel.table.viewport(), Qt.MouseButton.LeftButton, pos=target)
        QTest.mouseDClick(self.panel.table.viewport(), Qt.MouseButton.LeftButton, pos=target)
        self.drain()
        self.assertEqual(self.panel.detail_dialog.row["symbol"], "105560")
        self.assertEqual(self.panel.table.cellWidget(9, DETAIL_COLUMN).accessibleName(), "KB금융 상세보기")

    def test_language_switch_preserves_selection_and_open_document(self):
        self.panel.table.setCurrentCell(6, 0)
        dialog = self.panel.open_detail(6)
        for locale in (LocaleContext("en_US"), LocaleContext("ko_KR"), LocaleContext("en_US")):
            self.panel.set_locale(locale)
            self.drain()
            self.assertEqual(self.panel.table.currentRow(), 6)
            self.assertIs(self.panel.detail_dialog, dialog)
            self.assertEqual(dialog.row["symbol"], "005930")
        self.assertEqual(self.panel.table.item(3, 0).text(), "US 10-year yield")
        self.assertEqual(self.panel.table.item(6, 0).text(), "Samsung Electronics")
        self.assertIn("Quote snapshot", self.panel.table.item(6, 1).toolTip())
        self.assertNotIn("Observation date", self.fields(dialog)); self.assertNotIn("Provider", self.fields(dialog))
        self.assertEqual(self.fields(dialog)["Market cap"], "Unconfirmed")
        visible_text = [v.text() for v in self.panel.findChildren(QLabel) if v.isVisible()]
        visible_text += [v.text() for v in self.panel.findChildren(QPushButton) if v.isVisible()]
        self.assertFalse([value for value in visible_text if re.search("[가-힣]", value)])
        self.network.assert_not_called()

    def test_theme_change_preserves_values_and_semantic_colors(self):
        before = self.panel.table.item(6, 1).text()
        self.panel.open_detail(6)
        for palette in (DARK, LIGHT, DARK):
            self.panel.set_theme(palette)
            self.drain()
            self.assertEqual(self.panel.table.item(6, 1).text(), before)
            # Korean convention (owner 2026-11-04): a rise is red and a fall is blue, AA on each theme.
            up, down = ("#f0868c", "#7fb0e8") if palette is DARK else ("#c8343d", "#2f6db5")
            self.assertEqual(self.panel.table.item(6, 2).foreground().color().name(), up)
            self.assertEqual(self.panel.table.item(3, 2).foreground().color().name(), down)
            self.assertIn(palette.surface, self.panel.styleSheet())
            self.assertIn(palette.text, self.panel.detail_dialog.styleSheet())

    def test_narrow_panel_keeps_overflow_in_table_and_rows_compact(self):
        self.panel.resize(1064, 950)  # Home content width at a 1360px research window.
        self.drain()
        self.assertEqual(self.panel.table.horizontalScrollBar().maximum(), 0)
        self.panel.resize(700, 950)
        self.drain()
        table = self.panel.table
        self.assertLessEqual(self.panel.width(), 700)
        self.assertLessEqual(table.width(), self.panel.width())
        self.assertGreater(table.horizontalScrollBar().maximum(), 0)
        self.assertLessEqual(table.height(), 600)
        self.assertEqual([table.rowHeight(i) for i in range(12)], [44] * 12)
        self.assertEqual(table.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def test_long_english_company_names_keep_both_lines_in_compact_rows(self):
        from PyQt6.QtGui import QFont, QFontDatabase, QFontMetrics
        path = Path(__file__).resolve().parents[1] / "assets/fonts/qg-interface.otf"
        font_id = QFontDatabase.addApplicationFont(str(path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        self.assertTrue(families)
        font = QFont(families[0])
        font.setPixelSize(13)  # The research window's production text size.
        self.panel.setFont(font)
        rows = financial_rows()
        rows[6]["per"] = 100.50
        self.panel.set_rows(rows)
        self.panel.set_locale(LocaleContext("en_US"))
        self.drain()
        for row in (6, 10, 11):
            identity = self.panel.table.cellWidget(row, 0)
            company = next(label for label in identity.findChildren(QLabel) if label.objectName() != "watchlistTicker")
            self.assertGreaterEqual(company.height(), company.heightForWidth(company.width()), company.text())
            self.assertEqual(self.panel.table.rowHeight(row), 44)
        self.panel.update_score("005930", dict(status="ready", score=79.99, stars=4,
                                                as_of="2026-11-02T03:00:00+00:00", feed_state="stopped", live=False))
        item = self.panel.table.item(6, SCORE_COLUMN)
        lines = item.text().splitlines()
        metrics = QFontMetrics(item.font())
        identity = self.panel.table.cellWidget(6, 0)
        self.assertEqual(lines[1], "Paused · last score")
        self.assertLessEqual(metrics.lineSpacing() * len(lines), identity.height())
        insets = self.panel.table.columnWidth(0) - identity.width()
        self.assertLessEqual(max(metrics.horizontalAdvance(line) for line in lines),
                             self.panel.table.columnWidth(SCORE_COLUMN) - insets)
        per = self.panel.table.item(6, 5)
        self.assertEqual(per.text(), "100.50")
        self.assertLessEqual(QFontMetrics(per.font()).horizontalAdvance(per.text()),
                             self.panel.table.columnWidth(5) - insets - 4)

    def test_busy_refresh_is_explicit_and_keeps_existing_rows(self):
        requests = []
        self.panel.refresh_requested.connect(lambda: requests.append(True))
        self.panel.set_busy(True)
        self.assertFalse(self.panel.refresh.isEnabled())
        self.assertEqual(self.panel.table.rowCount(), 12)
        self.assertEqual(self.panel.refresh.text(), "조회 중…")
        self.panel.refresh.click()
        self.assertEqual(requests, [])
        self.panel.set_locale(LocaleContext("en_US"))
        self.assertEqual(self.panel.refresh.text(), "Loading…")
        self.panel.set_busy(False)
        self.panel.refresh.click()
        self.assertEqual(requests, [True])
        self.network.assert_not_called()

    def test_failure_guidance_never_exposes_provider_error_secrets(self):
        rows = sample_rows()
        rows[7]["error_code"] = "https://provider.invalid?appsecret=do-not-display"
        self.panel.set_rows(rows)
        dialog = self.panel.open_detail(7)
        self.assertIn("KIS", dialog.notice.text())
        self.assertIn("API", dialog.notice.text())
        self.assertNotIn("appsecret", dialog.notice.text())
        self.assertNotIn("provider.invalid", self.panel.table.item(7, 1).toolTip())
        self.assertEqual(self.fields(dialog)["수신 시각"], "—")
        self.panel.set_locale(LocaleContext("en_US"))
        self.assertIn("connection settings", dialog.notice.text())
        self.assertEqual(self.fields(dialog)["Received at"], "—")

    def test_score_column_updates_without_invented_ratings_or_row_rebuilds(self):
        table = self.panel.table
        identity, details = table.cellWidget(6, 0), table.cellWidget(6, DETAIL_COLUMN)
        self.assertEqual(table.horizontalHeaderItem(table.columnCount() - 1).text(), "Q-SCORE")
        self.assertEqual(table.item(0, SCORE_COLUMN).text(), "산정 전")
        score = dict(status="ready", score=72.4, stars=4, as_of="2026-11-02T03:00:00+00:00")
        self.assertTrue(self.panel.update_score("005930", score))
        self.assertEqual(table.item(6, SCORE_COLUMN).text(), "★★★★☆  72.40")
        self.assertIn("UTC", table.item(6, SCORE_COLUMN).toolTip())
        self.assertIs(table.cellWidget(6, 0), identity)
        self.assertIs(table.cellWidget(6, DETAIL_COLUMN), details)
        self.assertFalse(self.panel.update_score("999999", score))
        self.panel.update_score("005930", {**score, "score": 101})
        self.assertNotIn("★", table.item(6, SCORE_COLUMN).text())
        self.panel.update_score("005930", {"status": "insufficient_data"})
        self.assertEqual(table.item(6, SCORE_COLUMN).text(), "자료 부족")
        self.panel.set_locale(LocaleContext("en_US"))
        self.assertEqual(table.item(6, SCORE_COLUMN).text(), "Insufficient data")
        self.assertEqual(table.item(0, SCORE_COLUMN).text(), "Not scored")
        self.network.assert_not_called()

    def test_score_help_hover_and_keyboard_explain_engine_capabilities(self):
        from core.research.qscore import q_score_help
        self.assertIn("기술신호·위험분석 엔진", self.panel.score_help.toolTip())
        self.assertNotIn("70%", self.panel.score_help.toolTip())
        self.panel.score_help.setFocus()
        QTest.keyClick(self.panel.score_help, Qt.Key.Key_Space)
        self.drain()
        dialog = self.panel.score_help_dialog
        self.assertTrue(dialog.isVisible())
        self.assertEqual(dialog.body.text(), q_score_help("ko"))
        self.panel.set_locale(LocaleContext("en_US"))
        self.panel.set_theme(DARK)
        self.assertEqual(dialog.body.text(), q_score_help("en"))
        self.assertIn("technical-signal and risk engines", self.panel.score_help.toolTip())
        self.assertNotIn("70%", dialog.body.text())
        self.assertNotIn("15%", dialog.body.text())
        self.assertIn(DARK.text, dialog.styleSheet())
        self.network.assert_not_called()

    def test_header_help_follows_column_resize_move_and_horizontal_scroll(self):
        header = self.panel.table.horizontalHeader()
        help_button = self.panel.score_help
        self.assertIs(help_button.parentWidget(), header.viewport())
        self.assertEqual(help_button.text(), "?")
        self.assertEqual(self.panel.findChildren(QPushButton, "qScoreHeaderHelp"), [help_button])
        self.assertFalse([button for button in self.panel.findChildren(QPushButton) if button.text() == "Q-SCORE ?"])
        self.assertEqual(header.logicalIndexAt(help_button.geometry().center()), SCORE_COLUMN)
        old_position = help_button.pos()
        header.resizeSection(6, 100)
        self.drain()
        self.assertNotEqual(help_button.pos(), old_position)
        self.assertEqual(header.logicalIndexAt(help_button.geometry().center()), SCORE_COLUMN)
        header.moveSection(header.visualIndex(SCORE_COLUMN), 1)
        self.drain()
        self.assertEqual(header.logicalIndexAt(help_button.geometry().center()), SCORE_COLUMN)
        header.moveSection(header.visualIndex(SCORE_COLUMN), SCORE_COLUMN)
        self.panel.resize(700, 800)
        self.panel.table.horizontalScrollBar().setValue(0)
        self.drain()
        self.assertTrue(help_button.visibleRegion().isEmpty())
        self.panel.set_live_state("connecting")
        self.panel.stop_button.setFocus()
        QTest.keyClick(self.panel.stop_button, Qt.Key.Key_Tab)
        self.drain()
        self.assertIs(self.app.focusWidget(), help_button)
        self.assertGreater(self.panel.table.horizontalScrollBar().value(), 0)
        self.assertTrue(header.viewport().rect().contains(help_button.geometry()))
        QTest.keyClick(help_button, Qt.Key.Key_Return)
        self.drain()
        self.assertTrue(self.panel.score_help_dialog.isVisible())
        self.network.assert_not_called()

    def test_provider_failure_reason_is_localized_safe_and_actionable(self):
        rows = sample_rows()
        rows[0].update(status="UNAVAILABLE", reason_code="rate_limited", error_code="https://unsafe.invalid?secret=hidden")
        self.panel.set_rows(rows)
        tooltip = self.panel.table.item(0, 1).toolTip()
        self.assertIn("요청 제한", self.panel.table.item(0, 1).toolTip())
        self.assertIn("요청 한도", tooltip)
        self.assertIn("새로고침", tooltip)
        self.assertNotIn("KIS", tooltip)
        self.assertNotIn("unsafe.invalid", tooltip)
        self.panel.set_locale(LocaleContext("en_US"))
        tooltip = self.panel.table.item(0, 1).toolTip()
        self.assertIn("Rate limited", self.panel.table.item(0, 1).toolTip())
        self.assertIn("request limit", tooltip)
        self.assertIn("refresh", tooltip)
        self.assertNotIn("secret", tooltip)
        rows[0]["reason_code"] = "no_observations"
        self.panel.set_rows(rows)
        self.panel.set_locale(LocaleContext("ko_KR"))
        self.assertIn("자료 없음", self.panel.table.item(0, 1).toolTip())

    def test_live_controls_trade_metadata_and_disconnect_pause_last_stars(self):
        events = []
        self.panel.live_requested.connect(lambda: events.append("start"))
        self.panel.stop_requested.connect(lambda: events.append("stop"))
        self.panel.live_button.click()
        self.assertEqual(events, ["start"])
        self.panel.set_live_state("connecting")
        self.assertFalse(self.panel.live_button.isEnabled())
        self.assertIn("연결 중", self.panel.live_status.text())
        self.panel.set_live_state("subscribed")
        self.assertFalse(self.panel.live_button.isEnabled())
        self.assertTrue(self.panel.stop_button.isEnabled())
        self.assertIn("조회 시세", self.panel.table.item(6, 1).toolTip())
        identity = self.panel.table.cellWidget(6, 0)
        self.assertFalse(self.panel.update_quote("005930", 72100, 1.59,
                                                "2026-11-02T03:00:02+00:00", status="STREAMING"))
        self.assertTrue(self.panel.update_quote("005930", 72100, 1.59,
                                               "2026-11-02T03:00:02+00:00", status="STREAMING",
                                               market_time="2026-11-02T03:00:01+00:00", source="KIS WebSocket", volume=1200010))
        self.assertEqual(self.panel.rows[6]["stream_source"], "KIS WebSocket")
        self.panel.update_score("005930", dict(status="ready", score=81, stars=5, as_of="2026-11-02T03:00:01+00:00"))
        self.panel.set_live_state("streaming")
        self.assertIs(self.panel.table.cellWidget(6, 0), identity)
        self.assertEqual(self.panel.table.item(6, 1).text(), "72,100 KRW")
        self.assertIn("실시간 체결", self.panel.table.item(6, 1).toolTip())
        self.assertIn("체결", self.panel.table.item(6, 1).toolTip())
        dialog = self.panel.open_detail(6)
        fields = self.fields(dialog)
        self.assertNotEqual(fields["체결 시각"], fields["수신 시각"])
        self.panel.stop_button.click()
        self.assertEqual(events, ["start", "stop"])
        self.panel.set_live_state("stopped")
        self.assertIn("연결 종료", self.panel.table.item(6, 1).toolTip())
        self.assertIn("★★★★★", self.panel.table.item(6, SCORE_COLUMN).text())
        self.assertIn("마지막 점수", self.panel.table.item(6, SCORE_COLUMN).text())
        self.assertEqual(self.panel.table.item(6, 1).text(), "72,100 KRW")
        self.assertEqual(self.fields(dialog)["상태"], "연결 종료")
        self.network.assert_not_called()

    def test_daily_score_date_remains_explicitly_daily(self):
        self.panel.update_score("005930", dict(status="ready", score=50, stars=3, as_of="2026-10-30"))
        self.assertIn("일별 자료", self.panel.table.item(6, SCORE_COLUMN).toolTip())
        self.assertNotIn("UTC", self.panel.table.item(6, SCORE_COLUMN).toolTip())
        self.panel.set_locale(LocaleContext("en_US"))
        self.assertIn("daily data", self.panel.table.item(6, SCORE_COLUMN).toolTip())

    def test_comparison_columns_compact_values_and_full_detail_metadata(self):
        self.panel.set_rows(financial_rows())
        self.panel.set_locale(LocaleContext("en_US"))
        table = self.panel.table
        self.assertEqual([table.horizontalHeaderItem(c).text() for c in range(table.columnCount())],
                         ["Instrument", "Price", "Change", "Volume", "Market cap", "PER", "EPS", "Sector", "Details", "Q-SCORE"])
        self.assertEqual(table.item(6, 3).text(), "1.2M")
        self.assertEqual(table.item(6, 4).text(), "72B KRW")
        self.assertEqual(table.item(6, 5).text(), "12.34")
        self.assertEqual(table.item(6, 6).text(), "5,834")
        self.assertEqual(table.item(6, 7).text(), "Electronics")
        self.assertIn("Quote snapshot", table.item(6, 1).toolTip())
        self.assertIn("KIS", table.item(6, 1).toolTip())
        self.assertIn("UTC", table.item(6, 1).toolTip())
        table.setCurrentCell(6, 1)
        QTest.keyClick(table, Qt.Key.Key_Return)
        fields = self.fields(self.panel.detail_dialog)
        self.assertEqual(fields["Market cap"], "72,000,000,000 KRW")
        self.assertEqual(fields["Market cap basis"], "Price × listed shares")
        self.assertEqual(fields["Volume"], "1,200,000")
        self.assertEqual(fields["Financial reference date"], "Not supplied by provider")
        self.assertEqual(fields["Status"], "Quote snapshot")
        self.assertNotIn("Provider", fields)  # provider stays in the price tooltip (owner, 2026-11-04)
        self.assertIn("EPS unit", self.panel.detail_dialog.rights.text())
        self.panel.set_locale(LocaleContext("ko_KR"))
        self.assertEqual(table.item(6, 3).text(), "120만")
        self.assertEqual(table.item(6, 4).text(), "720억 KRW")
        self.network.assert_not_called()

    def test_market_cap_tick_reuses_only_same_kst_session_shares(self):
        self.panel.set_rows(financial_rows())
        original_clock = self.panel.rows[6]["fundamentals_received_at"]
        self.panel.update_quote("005930", 73000, 2.0, "2026-11-02T03:01:02+00:00",
                                status="STREAMING", market_time="2026-11-02T03:01:00+00:00", source="KIS WebSocket")
        row = self.panel.rows[6]
        self.assertEqual(row["market_cap"], 73_000_000_000)
        self.assertEqual(row["market_cap_as_of"], "2026-11-02T03:01:00+00:00")
        self.assertEqual(row["fundamentals_received_at"], original_clock)
        self.assertEqual((row["per"], row["eps"]), (12.34, 5834))
        self.panel.update_quote("005930", 74000, 3.0, "2026-11-03T03:01:02+00:00",
                                status="STREAMING", market_time="2026-11-03T03:01:00+00:00", source="KIS WebSocket")
        row = self.panel.rows[6]
        self.assertEqual(row["value"], 74000)
        self.assertEqual(row["market_cap"], 73_000_000_000)
        self.assertEqual(row["market_cap_as_of"], "2026-11-02T03:01:00+00:00")
        self.assertEqual(row["fundamentals_received_at"], original_clock)
        self.assertIn("2026. 11. 2.", self.panel.table.item(6, 4).toolTip())
        self.assertIn("2026. 11. 3.", self.panel.table.item(6, 1).toolTip())
        self.network.assert_not_called()

    def test_metric_absence_zero_losses_and_unverified_cap_do_not_change_price(self):
        rows = financial_rows()
        rows[6].update(per=0, eps=-1500, market_cap_unit="UNVERIFIED")
        self.panel.set_rows(rows)
        table = self.panel.table
        self.assertEqual(table.item(6, 1).text(), "72,000 KRW")
        self.assertEqual(table.item(6, 4).text(), "—")
        self.assertEqual(table.item(6, 5).text(), "0.00")
        self.assertEqual(table.item(6, 6).text(), "-1,500")
        self.assertNotIn("123456789", table.item(6, 4).toolTip())
        rows[6].update(per=-4.25, eps=0)
        self.panel.set_rows(rows)
        self.assertEqual(table.item(6, 5).text(), "-4.25")
        self.assertEqual(table.item(6, 6).text(), "0")
        rows[6].update(per=None, eps=float("nan"))
        self.panel.set_rows(rows)
        self.assertEqual(table.item(6, 5).text(), "—")
        self.assertEqual(table.item(6, 6).text(), "—")

    def test_unknown_sector_translation_keeps_provider_original_in_details(self):
        rows = financial_rows()
        rows[6]["sector"] = "공급자 신규 업종"
        self.panel.set_rows(rows)
        self.panel.set_locale(LocaleContext("en_US"))
        self.assertEqual(self.panel.table.item(6, 7).text(), "Untranslated")
        self.assertIn("공급자 신규 업종", self.panel.table.item(6, 7).toolTip())
        dialog = self.panel.open_detail(6)
        self.assertEqual(self.fields(dialog)["Provider sector text"], "공급자 신규 업종")
        self.assertIn("Provider reference date not supplied", self.panel.table.item(6, 6).toolTip())
        rows[6]["sector"] = "운수장비"
        self.panel.set_rows(rows)
        self.assertEqual(self.panel.table.item(6, 7).text(), "Transport eq.")
        self.assertIn("Transport equipment", self.panel.table.item(6, 7).toolTip())
        self.assertEqual(self.fields(dialog)["Sector"], "Transport equipment")


if __name__ == "__main__":
    unittest.main()
