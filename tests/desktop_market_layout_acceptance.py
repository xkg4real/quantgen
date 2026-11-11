"""Full-window regressions for market forms hidden by excess tab height."""
from __future__ import annotations

import os
import time
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QMessageBox


class NativeMarketLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.original_font = cls.app.font()
        font = Path(__file__).resolve().parents[1] / "assets/fonts/qg-interface.otf"  # production face (owner UI-D6)
        cls.font_id = QFontDatabase.addApplicationFont(str(font))
        families = QFontDatabase.applicationFontFamilies(cls.font_id)
        if families:
            cls.app.setFont(QFont(families[0], 10))

    @classmethod
    def tearDownClass(cls):
        cls.app.setFont(cls.original_font)
        if cls.font_id >= 0:
            QFontDatabase.removeApplicationFont(cls.font_id)

    def setUp(self):
        self.network = patch("requests.sessions.Session.request",
                             side_effect=AssertionError("Unexpected provider call"))
        self.http = self.network.start()
        self.addCleanup(self.network.stop)
        self.jobs_patch = patch("quantgen_desktop.jobs.Jobs.start",
                                side_effect=AssertionError("Unexpected research job"))
        self.jobs = self.jobs_patch.start()
        self.addCleanup(self.jobs_patch.stop)
        self.paper = Mock(side_effect=AssertionError("Unexpected paper session"))
        self.window = ResearchWindow(auto_refresh=False, market_loader=lambda: [],
                                     paper_factory=self.paper, language="ko")
        self.window.show()
        self.window.navigate("markets")
        self.app.processEvents()
        self.addCleanup(self.close_window)

    def close_window(self):
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.http.assert_not_called()
        self.jobs.assert_not_called()
        self.paper.assert_not_called()

    def select(self, pane):
        self.window.show_market_pane(pane)
        self.app.processEvents()

    def test_forms_stay_compact_after_switching_from_tall_sibling_tabs(self):
        # QTabWidget allocates enough height for its tallest (possibly hidden)
        # sibling. A standalone ToolPane cannot reproduce this regression.
        w = self.window
        for width, height in ((1000, 700), (1360, 940), (1920, 1080)):
            w.resize(width, height)
            self.app.processEvents()
            self.select(w.market_chart)
            for name in ("krx", "macro", "krx"):
                with self.subTest(size=(width, height), pane=name):
                    pane = getattr(w, name)
                    self.select(pane)
                    heading = pane.input_box.layout().itemAt(0).widget()
                    self.assertLessEqual(heading.height(), 80)
                    self.assertLessEqual(pane.input_box.height(), 400)
                    control_y = pane.tool.mapTo(pane.input_box, QPoint()).y()
                    self.assertLessEqual(control_y, 160)
                    self.assertTrue(pane.run.isVisible())

    def test_scrolling_to_form_exposes_controls_in_minimum_window(self):
        w = self.window
        w.resize(1000, 700)
        self.app.processEvents()
        self.select(w.krx)
        scroll = w.stack.currentWidget()
        scroll.ensureWidgetVisible(w.krx.input_box, 0, 0)
        self.app.processEvents()
        viewport = scroll.viewport()
        # Owner UI-8: Markets panes choose providers automatically; no source selector is shown.
        self.assertTrue(w.krx.source.isHidden())
        for name in ("tool", "forms", "run"):
            with self.subTest(control=name):
                control = getattr(w.krx, name)
                bounds = QRect(control.mapTo(viewport, QPoint()), control.size())
                self.assertTrue(viewport.rect().contains(bounds),
                                f"{name} is outside the visible form: {bounds}")

    def test_stock_detail_opens_live_controls_without_starting_a_query(self):
        """UI-D8 (owner 2026-11-11): the stock's screen fills the page viewport and the page does not scroll; its
        toolbar (refresh included) and name are on screen at 1000x700 and 1360x940 in both languages."""
        from PyQt6.QtCore import Qt as _Qt
        w = self.window
        self.assertFalse(hasattr(w, "live_chart_open"))
        for language in ("ko", "en"):
            w.set_language(language)
            for width, height in ((1000, 700), (1360, 940)):
                with self.subTest(language=language, size=(width, height)):
                    w.resize(width, height)
                    self.select(w.krx)
                    w.navigate("home")
                    self.app.processEvents()
                    detail = w.watchlist.open_detail(6)
                    detail.chart_button.click()
                    # A stock's detail opens the chart on the next event.
                    for _ in range(4):
                        self.app.processEvents()
                    self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
                    self.assertIs(w.current_market_pane(), w.market_chart)
                    scroll = w.stack.currentWidget()
                    viewport = scroll.viewport()
                    stock = w.markets_view.stock
                    # Since 2026-11-04 the stock's screen names it in its header; the chart's own code field is hidden.
                    self.assertFalse(w.market_chart.symbol.isVisible())
                    self.assertEqual(stock.instrument.code, w.market_chart.symbol.text())
                    for control in (stock.name, stock.refresh_button, stock.periods):
                        self.assertTrue(control.isVisible())
                        bounds = QRect(control.mapTo(viewport, QPoint()), control.size())
                        self.assertTrue(viewport.rect().contains(bounds),
                                        f"Live chart control is offscreen: {bounds}")
                    # The page lock: no page scroll bar, the view is exactly the viewport's height.
                    self.assertEqual(scroll.verticalScrollBarPolicy(), _Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    self.assertEqual(stock.height(), viewport.height())
                    self.assertEqual(stock.mapTo(viewport, QPoint()).y(), 0)
                    self.assertIsNone(w.market_chart.snapshot)
                    self.assertIsNone(w.market_chart._stream)
                    self.assertTrue(w.market_chart.empty_state.isVisible())
                    self.assertFalse(w.market_chart.chart.isVisible())
        w.navigate("home")
        self.app.processEvents()
        # Leaving restores the page's own scroll bar.
        self.assertEqual(w.stack.widget(w.route_indices["markets"]).verticalScrollBarPolicy(),
                         Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.http.assert_not_called()
        self.jobs.assert_not_called()

    def test_dynamic_indicator_panels_never_overlap_readouts_after_theme_and_width_changes(self):
        """UI-D8: the chart takes the height it is given (lower panels share it instead of growing the page);
        panels never overlap each other, the price pane, the header overlays or the axis, at both sizes, in both
        themes and languages, and the page never scrolls."""
        from tests.desktop_market_chart_acceptance import fixture
        w = self.window
        pane = w.market_chart
        self.select(pane)
        stock = w.markets_view.stock
        pane.snapshot = fixture(pane.request())
        pane.render()
        scroll = w.stack.currentWidget()

        def settle():
            for _ in range(6):
                self.app.processEvents()
                QTest.qWait(15)

        def check():
            layout = pane.chart.layout_info
            self.assertIsNotNone(layout)
            self.assertEqual((layout.width, layout.height), (pane.chart.width(), pane.chart.height()))
            edges = [(layout.price[0], layout.price[1])] + [(top, bottom) for _, top, bottom in layout.panels]
            for (a_top, a_bottom), (b_top, b_bottom) in zip(edges, edges[1:]):
                self.assertLessEqual(a_bottom, b_top)
            self.assertLessEqual(edges[-1][1], layout.axis_top)
            self.assertLessEqual(layout.axis_top, layout.height)
            strip = stock.overlays.ohlc.geometry()
            for key, top, bottom in layout.panels:
                head = stock.overlays.heads[key]
                self.assertTrue(head.isVisible())
                self.assertFalse(head.geometry().intersects(strip))
                self.assertTrue(pane.chart.rect().contains(head.geometry()))
            viewport = scroll.viewport()
            for control in (pane.chart, stock.periods, stock.toolbar):
                bounds = QRect(control.mapTo(viewport, QPoint()), control.size())
                self.assertTrue(viewport.rect().contains(bounds), str(bounds))
            self.assertEqual(scroll.verticalScrollBar().value(), stock.lock.target)

        for language in ('ko', 'en'):
            w.set_language(language)
            for theme in (0, 1):
                w.theme.setCurrentIndex(theme)
                for width, height in ((1360, 940), (1000, 700)):
                    w.resize(width, height)
                    settle()
                    check()
        for width, height in ((1360, 940), (1000, 700)):
            with self.subTest(width=width):
                w.resize(width, height)
                stock.set_studies(("sma", "bb", "rsi", "macd"))
                settle()
                height_with = pane.chart.height()
                check()
                self.assertEqual([key for key, _, _ in pane.chart.layout_info.panels], ["rsi", "macd"])
                stock.set_studies(("sma",))
                settle()
                check()
                self.assertEqual(pane.chart.height(), height_with)  # the chart never grows the page
                self.assertEqual(pane.chart.layout_info.panels, ())


if __name__ == "__main__":
    unittest.main()
