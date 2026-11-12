"""Owner UI port, area market (owner screenshots 03, 04, 05, 11, 14; 2026-11-10), native PyQt app.

05 "오와 열 맞추고 글씨 조정": the home watchlist draws every title at its cells' inset, numbers line up on
   their last digit with the unit in a slot after them, one body size, and no value is elided.
14 "한국어 영어 섞임": the market tools read in Korean in the Korean window (headings, legends, row names,
   codes beside their Korean meaning), and in English in the English window.
03 numbers carry thousands separators; 04/12 the derivatives board is picked automatically;
11 narratives are headed Korean bullets without raw card ids or 'not run'.
Display only: requests, `pane.sections` and `pane.report` are identical across language switches.

Offline: synthetic workflows and fakes only; HTTP is refused.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
import re
import unittest
from copy import deepcopy
from unittest.mock import patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.research.market_analysis import (CryptoRequest, DerivativesRequest, ETFRequest, KRXOutput, KRXRequest,
                                               execute_crypto, execute_derivatives, execute_etf)
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor, QFontMetrics
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox

from core.i18n import LocaleContext
from quantgen_desktop.watchlist import (BODY_PX, CELL_PADDING, NUMERIC_COLUMNS, SCORE_COLUMN, UNIT_GAP,
                                        WatchlistPanel, _split_number)
from tests.qt_fixture_cleanup import delete_owned_widget


def sections_json(pane):
    return json.dumps(pane.sections, sort_keys=True, default=lambda value: getattr(value, "item", lambda: str(value))())


class WatchlistAlignmentTests(unittest.TestCase):
    """Issue 05 on the native live-quote table (home)."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        # Measure the app's own face (QG Interface), as a ResearchWindow does: the platform sans differs by OS
        # (Segoe UI on Windows put the column title 4 px off its figures on PR 109's Windows CI).
        from quantgen_desktop import use_interface_fonts
        use_interface_fonts()

    def setUp(self):
        from tests.desktop_watchlist_acceptance import financial_rows
        deny = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        deny.start(); self.addCleanup(deny.stop)
        rows = financial_rows()
        rows[2].update(value=1387.5, change=0.21, status="OBSERVED", observation_date="2026-11-05")  # KRW/USD
        rows[5].update(value=96123.5, change=2.4, status="OBSERVED", observation_date="2026-11-05")   # USD
        self.panel = WatchlistPanel(locale=LocaleContext("ko_KR"))
        self.panel.resize(1240, 900)
        self.panel.set_rows(rows)
        for symbol, price, pct in (("005930", 193500, -3.97), ("000660", 528000, 1.54), ("207940", 1012000, 0.5)):
            self.panel.update_quote(symbol, price, pct, "2026-11-06T06:20:03+00:00", volume=21345678)
        self.panel.show()
        self.addCleanup(delete_owned_widget, self.panel)
        for _ in range(4):
            self.app.processEvents()

    def test_numbers_split_from_their_units(self):
        self.assertEqual(_split_number("1,387.50 KRW/USD"), ("1,387.50", "KRW/USD", True))
        self.assertEqual(_split_number("+1.45%"), ("+1.45", "%", False))
        self.assertEqual(_split_number("-7.00 bp"), ("-7.00", "bp", True))
        self.assertEqual(_split_number("1,155T KRW"), ("1,155", "T KRW", False))
        self.assertEqual(_split_number("—"), ("—", "", False))

    def test_one_body_size_and_item_text_unchanged(self):
        table = self.panel.table
        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                item = table.item(row, column)
                if item is not None:
                    self.assertEqual(item.font().pixelSize(), BODY_PX, (row, column))
        self.assertEqual(table.item(6, 1).text(), "193,500 KRW")   # tests, tooltips and exports keep the text
        self.assertEqual(table.item(2, 1).text(), "1,387.50 KRW/USD")

    def test_no_value_or_title_is_elided(self):
        table, delegate = self.panel.table, self.panel.cell_delegate
        for column in NUMERIC_COLUMNS:
            slot = delegate.unit_widths.get(column, 0)
            for row in range(table.rowCount()):
                item = table.item(row, column)
                number, unit, _ = _split_number(item.text())
                needed = QFontMetrics(item.font()).horizontalAdvance(number) + 2 * CELL_PADDING + (slot + UNIT_GAP if slot else 0)
                self.assertLessEqual(needed, table.columnWidth(column), (row, column, item.text()))
                if unit:
                    self.assertLessEqual(QFontMetrics(delegate.unit_font(item.font())).horizontalAdvance(unit), slot)

    def test_columns_fit_figures_in_the_face_the_delegate_draws(self):
        """Figures are drawn with font_policy.number_font (owner UI-D5); widths must be measured with it too.
        A wider number face (here: the same face at 1.6x size) must widen the columns, not elide."""
        from PyQt6.QtGui import QFont
        import quantgen_desktop.font_policy as policy
        real = policy.number_font

        def wide(base):
            font = QFont(real(base)); font.setPixelSize(round((base.pixelSize() if base.pixelSize() > 0 else 13) * 1.6))
            return font
        table, delegate = self.panel.table, self.panel.cell_delegate
        with patch.object(policy, "number_font", side_effect=wide):
            self.panel._fit_columns()
            for column in NUMERIC_COLUMNS:
                slot = delegate.unit_widths.get(column, 0)
                for row in range(table.rowCount()):
                    item = table.item(row, column)
                    number, _, _ = _split_number(item.text())
                    needed = QFontMetrics(wide(item.font())).horizontalAdvance(number) + 2 * CELL_PADDING + (
                        slot + UNIT_GAP if slot else 0)
                    self.assertLessEqual(needed, table.columnWidth(column), (row, column, item.text()))

    def test_score_title_sits_over_its_values(self):
        header = self.panel.table.horizontalHeader()
        left, title_width = header._group_geometry()
        self.assertEqual(left, header.sectionViewportPosition(SCORE_COLUMN) + CELL_PADDING)
        self.assertGreaterEqual(self.panel.score_help.x(), left + title_width)
        self.assertEqual(header.logicalIndexAt(self.panel.score_help.geometry().center()), SCORE_COLUMN)

    def _ink_columns(self, image, top, bottom, left, right):
        """x positions in [left, right) with a dark (text) pixel between top and bottom."""
        xs = []
        for x in range(max(0, left), min(image.width(), right)):
            if any(QColor(image.pixel(x, y)).lightness() < 150 for y in range(max(0, top), min(image.height(), bottom))):
                xs.append(x)
        return xs

    def test_digits_and_titles_share_one_right_edge(self):
        table = self.panel.table
        header = table.horizontalHeader()
        image = table.viewport().grab().toImage()
        head = header.viewport().grab().toImage()
        for column in (1, 5, 6):
            left = table.columnViewportPosition(column)
            right = left + table.columnWidth(column)
            slot = self.panel.cell_delegate.unit_widths.get(column, 0)
            edge = right - 1 - CELL_PADDING - (slot + UNIT_GAP if slot else 0)
            ends = set()
            for row in range(table.rowCount()):
                if table.item(row, column).text() == "—":
                    continue
                rect = table.visualRect(table.model().index(row, column))
                ink = self._ink_columns(image, rect.top() + 6, rect.bottom() - 6, left, edge + 2)
                self.assertTrue(ink, (column, row))
                ends.add(max(ink))
            self.assertTrue(ends)
            self.assertLessEqual(max(ends) - min(ends), 1, (column, sorted(ends)))   # every last digit on one edge
            title = self._ink_columns(head, 4, head.height() - 4, left, right)
            self.assertLessEqual(abs(max(title) - (right - 1 - CELL_PADDING)), 2, column)

    def test_english_window_stays_english(self):
        self.panel.set_locale(LocaleContext("en_US"))
        self.app.processEvents()
        self.assertEqual(self.panel.table.horizontalHeaderItem(1).text(), "Price")
        self.assertEqual(self.panel.table.item(6, 1).text(), "193,500 KRW")


class MarketToolsKoreanTests(unittest.TestCase):
    """Issues 03, 04, 11 and 14 on Derivatives, ETF, Crypto and KRX."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.quant.gate_ledger.family_ledger"):
            deny = patch(target, side_effect=AssertionError("live I/O forbidden"))
            deny.start(); self.addCleanup(deny.stop)
        self.window = ResearchWindow(auto_refresh=False, language="ko")
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for pane in (self.window.derivatives, self.window.etf, self.window.crypto, self.window.krx):
            pane.clear_result()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        delete_owned_widget(self.window)
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def apply(self, language):
        self.window.set_language(language)
        self.window.localizer.apply()
        self.app.processEvents()

    def cells(self, table, column):
        return [table.item(r, column).text() for r in range(table.rowCount()) if not table.isRowHidden(r)]

    def show(self, pane, out, name):
        pane.show_result(out)
        pane.bind_output(name, out)
        return deepcopy(pane.report), sections_json(pane)

    def assert_display_only(self, pane, report, sections):
        self.assertEqual(pane.report, report)
        self.assertEqual(sections_json(pane), sections)

    def test_derivatives_reads_korean_and_returns_to_english(self):
        pane = self.window.derivatives
        out = execute_derivatives(DerivativesRequest(source="synthetic", n_paths=100))
        report, sections = self.show(pane, out, "Derivatives fixture")
        checks = pane.tables["Static arbitrage checks"]
        for language in ("ko", "en", "ko"):
            self.apply(language)
            korean = language == "ko"
            self.assertEqual(checks.item(1, 0).text(), "콜 버터플라이" if korean else "call_butterfly")
            self.assertEqual(checks.item(1, 3).text(), "계산 완료(COMPUTED)" if korean else "COMPUTED")
            self.assertEqual(pane.tables["Hedge simulation"].item(0, 1).text(), "GBM")
            headings = {w.text() for w in pane.findChildren(QLabel) if w.property("role") == "heading"}
            self.assertIn("정적 차익거래 점검" if korean else "Static arbitrage checks", headings)
            # The chart area puts the x caption under the plot and the y caption above it (owner issue 02).
            density = pane.charts["Risk-neutral density"]
            footer, caption = density._footer_text(), density._caption_text()
            self.assertTrue(footer and caption)
            if korean:
                self.assertIsNone(re.search(r"[A-Za-z]{3,}", footer + caption), footer + caption)
            else:
                self.assertIsNone(re.search(r"[가-힣]", footer + caption), footer + caption)
            self.assert_display_only(pane, report, sections)
        bullets = " ".join(pane.narrative_view.lines("ko"))
        self.assertIn("콜 수직 스프레드", bullets)
        for raw in ("call_vertical", "synthetic front", "(assumed)", "(gbm,"):
            self.assertNotIn(raw, bullets, raw)

    def test_etf_sleeves_codes_and_narrative_without_raw_ids(self):
        pane = self.window.etf
        out = execute_etf(ETFRequest(code="069500", source="synthetic"))
        report, sections = self.show(pane, out, "ETF fixture")
        sleeves = pane.tables["Descriptive sleeve backtests"]
        self.apply("ko")
        self.assertEqual(self.cells(sleeves, 0), ["추세 전환", "변동성 목표", "매수 후 보유"])
        self.assertEqual(set(self.cells(sleeves, 3)), {"불러오지 않음(NOT_LOADED)"})
        shown = " ".join([w.text() for w in pane.findChildren(QLabel) if w.isVisibleTo(pane)]
                         + pane.narrative_view.lines("ko"))
        for raw in ("S_E1_trend_krx", "S_E2_voltarget_kodex200", "not run", "Simulated series", "ETF price / NAV",
                    "Descriptive sleeve backtests", "Trend switch vs buy & hold"):
            self.assertNotIn(raw, shown, raw)
        self.assertIn("국내 ETF 추세 전환", shown)
        self.apply("en")
        self.assertEqual(self.cells(sleeves, 0), ["Trend switch", "Vol target", "Buy & hold"])
        self.assertEqual(set(self.cells(sleeves, 3)), {"NOT_LOADED"})
        self.assert_display_only(pane, report, sections)
        rows = next(s for s in pane.sections if s.get("name") == "Descriptive sleeve backtests")["rows"]
        self.assertEqual([r[0] for r in rows], ["trend", "vol_target", "buy_hold"])   # the export keeps the keys

    def test_crypto_numbers_and_unit_root_wording(self):
        pane = self.window.crypto
        out = execute_crypto(CryptoRequest(source="synthetic"))
        report, sections = self.show(pane, out, "Crypto fixture")
        ethbtc = pane.tables["ETH/BTC"]
        self.apply("ko")
        values = dict(zip(self.cells(ethbtc, 0), self.cells(ethbtc, 1)))
        self.assertIn("최근 ETH/BTC 비율", values)
        self.assertLessEqual(len(values["최근 ETH/BTC 비율"]), 8)          # 0.007077, not 0.007077012706654069
        self.assertIn(values["단위근 검정"], ("단위근을 기각하지 못함(예상된 귀무가설)", "5% 수준에서 평균회귀"))
        self.assertEqual(self.cells(pane.tables["Weekday observations"], 0)[:2], ["월", "화"])
        self.apply("en")
        values = dict(zip(self.cells(ethbtc, 0), self.cells(ethbtc, 1)))
        self.assertIn(values["Unit-root test"], ("no rejection of a unit root (the expected null)", "mean-reverting at 5 %"))
        self.assert_display_only(pane, report, sections)
        rows = dict(next(s for s in pane.sections if s.get("name") == "ETH/BTC")["rows"])
        self.assertIsInstance(rows["last_ratio"], float)

    def test_krx_quote_has_thousands_separators_and_korean_rows(self):
        from data.krx.gateway import Answer
        from data.krx.kis_client import Quote
        pane = self.window.krx
        quote = Quote("005930", "삼성전자", 71000.0, 500.0, 0.71, 12345678, 4.2e14, 71500.0, 70000.0, 70500.0,
                      as_of="2026-11-04T06:00:00+00:00", source="KIS")
        out = KRXOutput(KRXRequest("quote", "005930"), Answer(quote, "KIS"))
        report, sections = self.show(pane, out, "KRX fixture")
        table = pane.tables["Quote"]
        self.apply("ko")
        values = dict(zip(self.cells(table, 0), self.cells(table, 1)))
        self.assertEqual((values["현재가"], values["거래량"], values["시가총액"]),
                         ("71,000", "12,345,678", "420,000,000,000,000"))
        self.assertNotIn("as_of", self.cells(table, 0))
        self.assertEqual(pane.narrative_view.lines("ko"), ["시장 관측 조회 전용이며 주문이나 계좌 조작을 수행하지 않습니다."])
        self.apply("en")
        self.assertEqual(dict(zip(self.cells(table, 0), self.cells(table, 1)))["Last price"], "71,000")
        self.assert_display_only(pane, report, sections)
        rows = dict(next(s for s in pane.sections if s.get("name") == "Quote")["rows"])
        self.assertEqual((rows["price"], rows["source"]), (71000.0, "KIS"))

    def test_derivatives_board_is_chosen_automatically(self):
        pane = self.window.derivatives
        self.assertTrue(pane.source.isHidden())
        for ready, board in ((False, "synthetic"), (True, "kis")):
            with patch("config.kis_ready", return_value=ready):
                request = pane.make_request()
            self.assertEqual((request.source, pane.source.currentData()), (board, board))
            request.validate()
        # An explicit choice (tests, fixtures) is kept.
        pane.source.setCurrentIndex(pane.source.findData("synthetic"))
        with patch("config.kis_ready", return_value=True):
            pane._auto_board = None
            self.assertEqual(pane.make_request().source, "synthetic")


if __name__ == "__main__":
    unittest.main()
