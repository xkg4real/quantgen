"""Visible research workflows: native layout, wrapping and unchanged input state, offline."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow, load_interface_fonts
from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QApplication, QLabel
from tests.qt_fixture_cleanup import delete_owned_widget


class WorkspaceReadabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion')
        load_interface_fonts(cls.app)

    def setUp(self):
        network = patch('requests.sessions.Session.request', side_effect=AssertionError('offline'))
        network.start(); self.addCleanup(network.stop)
        jobs = patch('quantgen_desktop.jobs.Jobs.start', side_effect=AssertionError('no calculation'))
        jobs.start(); self.addCleanup(jobs.stop)
        self.window = ResearchWindow(auto_refresh=False, market_loader=lambda: [])
        self.addCleanup(delete_owned_widget, self.window)
        self.window.show()

    def settle(self):
        for _ in range(12):
            self.app.processEvents()

    def test_all_research_tabs_fit_and_wrap_in_both_languages_and_themes(self):
        w = self.window
        w.symbol.setText('MSFT')
        for language, theme in (('ko', 0), ('en', 1)):
            w.set_language(language); w.change_theme(theme)
            for width in (1000, 1360, 2000):
                w.resize(width, 750)
                for route, tabs in (('risk', w.risk_tabs), ('quant', w.quant_tabs)):
                    w.navigate(route)
                    for index in range(tabs.count()):
                        tabs.setCurrentIndex(index); self.settle()
                        page = w.stack.currentWidget()
                        with self.subTest(language=language, theme=theme, width=width, route=route, tab=index):
                            self.assertEqual(page.horizontalScrollBar().maximum(), 0)
                            for text in tabs.currentWidget().findChildren(QLabel):
                                if text.isVisibleTo(page) and text.wordWrap() and len(text.text()) > 40:
                                    self.assertGreaterEqual(text.height()+2, text.heightForWidth(text.width()), text.text())
                                    pos = text.mapTo(page.widget(), QPoint())
                                    self.assertLessEqual(pos.x()+text.width(), page.widget().width()+1, text.text())
        self.assertEqual(w.symbol.text(), 'MSFT')
