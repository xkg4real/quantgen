"""Full-window regressions for market forms hidden by excess tab height."""
from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QMessageBox


class NativeMarketLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.original_font = cls.app.font()
        font = Path(__file__).resolve().parents[1] / "assets/fonts/qg-interface.otf"
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
        self.window.market_tabs.setCurrentWidget(pane)
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
        for name in ("tool", "source", "forms", "run"):
            with self.subTest(control=name):
                control = getattr(w.krx, name)
                bounds = QRect(control.mapTo(viewport, QPoint()), control.size())
                self.assertTrue(viewport.rect().contains(bounds),
                                f"{name} is outside the visible form: {bounds}")

    def test_stock_detail_opens_live_controls_without_starting_a_query(self):
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
                    for _ in range(3):
                        self.app.processEvents()
                    self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
                    self.assertIs(w.market_tabs.currentWidget(), w.market_chart)
                    viewport = w.stack.currentWidget().viewport()
                    for control in (w.market_chart.symbol, w.market_chart.load_button):
                        self.assertTrue(control.isVisible())
                        bounds = QRect(control.mapTo(viewport, QPoint()), control.size())
                        self.assertTrue(viewport.rect().contains(bounds),
                                        f"Live chart control is offscreen: {bounds}")
                    self.assertIsNone(w.market_chart.snapshot)
                    self.assertIsNone(w.market_chart._stream)
                    self.assertTrue(w.market_chart.empty_state.isVisible())
                    self.assertFalse(w.market_chart.chart.isVisible())
        self.http.assert_not_called()
        self.jobs.assert_not_called()


if __name__ == "__main__":
    unittest.main()
