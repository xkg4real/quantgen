"""Left rail: hide/show with memory, the Markets sub-menu and keyboard use (owner 2026-11-11, UI-D7 points 2-3).

Owner: "시장 누르면 하위 UI로 종목 고를수있게 바꿔주고, 왼쪽 UI화면들 숨기는 기능도 필요해. 공간이슈때문에".
Offline: provider requests raise, dotenv loading is patched off, no jobs run.
"""
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow

from PyQt6.QtCore import QObject, QPoint, QRect, QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QScrollArea
from tests.qt_fixture_cleanup import delete_owned_widget

from core.theme import DARK, LIGHT
from quantgen_desktop import shell_rail
from quantgen_desktop.typography import (RAIL_COLLAPSED_WIDTH, SIDEBAR_WIDTH_RANGE, mix, rail_stylesheet,
                                         window_stylesheet)

SECTION_KEYS = ("value", "volume", "gainers", "losers", "cap", "search")
ENGLISH = ("Trading value", "Volume", "Top gainers", "Top losers", "Market cap", "Stock search")
KOREAN = ("거래대금", "거래량", "급상승", "급하락", "시가총액", "종목 검색")


class ShellRailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        network.start()
        self.addCleanup(network.stop)
        jobs = patch("quantgen_desktop.jobs.Jobs.start", side_effect=AssertionError("the rail must not start jobs"))
        jobs.start()
        self.addCleanup(jobs.stop)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "settings.ini")

    def store(self):
        return QSettings(self.path, QSettings.Format.IniFormat)

    def window(self, show=True, **kwargs):
        w = ResearchWindow(auto_refresh=False, market_loader=lambda: [], **kwargs)
        self.addCleanup(delete_owned_widget, w)
        if show:
            w.resize(1360, 820)
            w.show()
            w.activateWindow()
            QTest.qWaitForWindowActive(w)
            self.settle()
        return w

    def settle(self):
        for _ in range(6):
            self.app.processEvents()

    # Owner point 3: hide the rail for space; remembered across restarts.
    def test_rail_hides_to_a_strip_and_the_choice_survives_a_restart(self):
        store = self.store()
        w = self.window(language_store=store)
        expanded = w.sidebar.width()
        self.assertTrue(SIDEBAR_WIDTH_RANGE[0] <= expanded <= SIDEBAR_WIDTH_RANGE[1], expanded)
        self.assertTrue(w.sidebar_hide.isVisible())
        self.assertFalse(w.sidebar_show.isVisible())
        w.sidebar_hide.click()
        self.settle()
        self.assertTrue(w.sidebar_collapsed)
        self.assertEqual(w.sidebar.width(), RAIL_COLLAPSED_WIDTH)
        self.assertTrue(w.sidebar_show.isVisible())
        for widget in (*w.nav.values(), w.theme, w.language, w.paper_halt, w.brand_label):
            self.assertFalse(widget.isVisible(), widget)
        self.assertGreater(w.stack.width(), 1360 - RAIL_COLLAPSED_WIDTH - 2)
        store.sync()
        self.assertTrue(shell_rail.stored_flag(self.store()))

        restarted = self.window(language_store=self.store())
        self.assertTrue(restarted.sidebar_collapsed)
        self.assertEqual(restarted.sidebar.width(), RAIL_COLLAPSED_WIDTH)
        restarted.sidebar_show.click()
        self.settle()
        self.assertFalse(restarted.sidebar_collapsed)
        self.assertEqual(restarted.sidebar.width(), expanded)
        for widget in (restarted.theme, restarted.language, restarted.paper_halt, *restarted.nav.values()):
            self.assertTrue(widget.isVisible(), widget)
        restarted.language_store.sync()
        self.assertFalse(shell_rail.stored_flag(self.store()))
        self.assertFalse(self.window(language_store=self.store()).sidebar_collapsed)

    def test_unreadable_or_missing_setting_means_an_open_rail(self):
        store = self.store()
        store.setValue(shell_rail.SETTINGS_KEY, 42)
        store.sync()
        self.assertFalse(self.window(show=False, language_store=self.store()).sidebar_collapsed)
        self.assertFalse(self.window(show=False).sidebar_collapsed)  # no store at all
        self.assertFalse(shell_rail.stored_flag(object()))

    def test_ctrl_b_toggles_and_keeps_the_page_and_its_scroll_position(self):
        w = self.window()
        w.resize(1100, 720)
        for route in ("library", "system"):
            w.navigate(route)
            self.settle()
            page = w.stack.currentWidget()
            self.assertIsInstance(page, QScrollArea)
            bar = page.verticalScrollBar()
            self.assertGreater(bar.maximum(), 200, route)
            bar.setValue(200)
            for collapsed in (True, False):
                QTest.keyClick(w.stack, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
                self.settle()
                with self.subTest(route=route, collapsed=collapsed):
                    self.assertEqual(w.sidebar_collapsed, collapsed)
                    self.assertIs(w.stack.currentWidget(), page)
                    self.assertTrue(w.nav[route].isChecked())
                    self.assertEqual(bar.value(), min(200, bar.maximum()))

    def test_language_change_keeps_a_hidden_rail_hidden_and_reopens_at_the_fitted_width(self):
        w = self.window()
        w.set_sidebar_collapsed(True)
        for language in ("ko", "en", "ko"):
            w.set_language(language)
            self.settle()
            self.assertEqual(w.sidebar.width(), RAIL_COLLAPSED_WIDTH, language)
        w.set_sidebar_collapsed(False)
        self.settle()
        self.assertEqual(w.sidebar.width(), w.sidebar_expanded_width)
        self.assertEqual(w.fit_sidebar(), w.sidebar_expanded_width)
        # The brand row (symbol, wordmark, hide toggle) fits without overlap in both languages.
        for language in ("en", "ko"):
            w.set_language(language)
            self.settle()
            self.assertLessEqual(w.brand_label.geometry().right(), w.sidebar_hide.geometry().left(), language)
            self.assertLessEqual(w.sidebar_hide.geometry().right(), w.sidebar.width() - 2, language)

    def test_paper_engine_stop_stays_reachable_while_the_rail_is_hidden(self):
        w = self.window()
        w.set_sidebar_collapsed(True)
        self.settle()
        self.assertFalse(w.paper_halt_strip.isVisible())
        runtime = Mock()
        w.paper_session.runtime = runtime
        w.paper_engine_changed()  # the session's changed signal calls this; a Mock runtime would upset the paper page
        self.settle()
        self.assertTrue(w.paper_halt_strip.isVisible())
        self.assertTrue(w.paper_halt.isEnabled())
        w.paper_halt_strip.click()
        runtime.halt.assert_called_once_with()
        w.paper_session.runtime = None
        w.paper_engine_changed()  # the session's changed signal calls this; a Mock runtime would upset the paper page
        self.assertFalse(w.paper_halt_strip.isVisible())
        self.assertFalse(w.paper_halt.isEnabled())

    # Owner point 2: Markets opens sub-items to pick what to look at.
    def test_markets_sub_menu_shows_only_for_markets_and_calls_the_page(self):
        w = self.window()
        self.assertEqual(tuple(w.market_sections), SECTION_KEYS)
        self.assertEqual(tuple(b.text() for b in w.market_sections.values()), ENGLISH)
        self.assertNotIn("search", w.nav)
        self.assertEqual(len(w.nav), 8)
        self.assertFalse(w.market_submenu.isVisible())
        w.nav["markets"].click()
        self.settle()
        self.assertTrue(w.market_submenu.isVisible())
        w.nav["markets"].click()  # clicked again: still open
        self.assertTrue(w.market_submenu.isVisible())
        for route in w.nav:
            w.navigate(route)
            self.assertEqual(w.market_submenu.isVisible(), route == "markets", route)
        w.markets_view.show_category = Mock()
        for key in SECTION_KEYS:
            w.navigate("tools")
            w.market_sections[key].click()
            self.settle()
            with self.subTest(key=key):
                self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
                self.assertTrue(w.nav["markets"].isChecked())
                w.markets_view.show_category.assert_called_with(key)
                self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], [key])
                self.assertTrue(w.market_submenu.isVisible())
        self.assertEqual(w.markets_view.show_category.call_count, len(SECTION_KEYS))
        w.market_sections["cap"].click()  # clicking the selected item keeps it selected
        self.assertTrue(w.market_sections["cap"].isChecked())
        with self.assertRaises(ValueError):
            w.open_market_section("rankings")

    def test_sections_follow_the_markets_page_contract(self):
        w = self.window(show=False)
        try:
            from quantgen_desktop.markets_view import RANKING_CATEGORIES
        except ImportError:  # until the Markets page publishes its categories
            RANKING_CATEGORIES = shell_rail.FALLBACK_CATEGORIES
        self.assertEqual(tuple(w.market_sections), tuple(row[0] for row in RANKING_CATEGORIES) + ("search",))
        self.assertEqual(tuple(row[1] for row in RANKING_CATEGORIES), ENGLISH[:5])

    def test_highlight_follows_what_markets_shows(self):
        w = self.window()
        view = w.markets_view
        view.show_category = Mock()
        w.navigate("markets")
        self.assertEqual([b for b in w.market_sections.values() if b.isChecked()], [])
        view.current_category = lambda: "losers"  # the page may report its own category
        w.navigate("home")
        w.navigate("markets")
        self.assertTrue(w.market_sections["losers"].isChecked())
        view.showing_stock = lambda: True  # one stock's screen belongs to stock search
        w.navigate("markets")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["search"])
        del view.current_category
        view.showing_stock = lambda: False
        w.market_sections["volume"].click()
        w.navigate("guide")
        w.navigate("markets")  # back on Markets: the last choice stays highlighted
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["volume"])

    def test_highlight_follows_the_page_when_it_announces_its_category(self):
        class Page(QObject):
            category_changed = pyqtSignal(str)

        w = self.window(show=False)
        page = Page()
        w.connect_market_sections(page)
        page.category_changed.emit("cap")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["cap"])
        page.category_changed.emit("search")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["search"])
        w.connect_market_sections(object())  # a page without the signal is fine

    def test_search_works_before_the_page_has_categories(self):
        w = self.window()
        real = w.markets_view
        stub = SimpleNamespace(showing_stock=lambda: False, search=Mock())
        w.markets_view = stub
        try:
            w.open_market_section("search")
            stub.search.setFocus.assert_called_once()
            w.open_market_section("value")  # no category view yet: Markets opens, nothing fails
            self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
            self.assertTrue(w.market_sections["value"].isChecked())
        finally:
            w.markets_view = real

    def test_sub_menu_and_toggles_in_korean_and_english_without_rebuilding(self):
        w = self.window()
        w.navigate("markets")
        buttons = dict(w.market_sections)
        for language, texts, hide, show in (("ko", KOREAN, "메뉴 숨기기 (Ctrl+B)", "메뉴 펼치기 (Ctrl+B)"),
                                            ("en", ENGLISH, "Hide menu (Ctrl+B)", "Show menu (Ctrl+B)"),
                                            ("ko", KOREAN, "메뉴 숨기기 (Ctrl+B)", "메뉴 펼치기 (Ctrl+B)")):
            w.set_language(language)
            self.settle()
            with self.subTest(language=language):
                self.assertEqual(tuple(b.text() for b in w.market_sections.values()), texts)
                self.assertEqual(tuple(b.accessibleName() for b in w.market_sections.values()), texts)
                self.assertEqual((w.sidebar_hide.toolTip(), w.sidebar_show.toolTip()), (hide, show))
                self.assertEqual(w.nav["markets"].text(), "시장" if language == "ko" else "Markets")
                self.assertEqual(w.market_sections, buttons)
                self.assertTrue(w.market_submenu.isVisible())
        self.assertEqual(w.sidebar_hide.accessibleName(), "메뉴 숨기기")
        restored = self.window(language="ko")
        self.assertEqual(tuple(b.text() for b in restored.market_sections.values()), KOREAN)

    # Keyboard: arrows walk the rail, Return opens, the ring shows for keyboard focus only.
    def test_rail_keyboard_walk_and_focus_ring(self):
        w = self.window()
        w.markets_view.show_category = Mock()
        home = w.nav["home"]
        home.setFocus(Qt.FocusReason.TabFocusReason)
        self.settle()
        self.assertTrue(home.hasFocus())
        self.assertTrue(home.property("focusRing"))
        QTest.keyClick(home, Qt.Key.Key_Down)
        markets = w.nav["markets"]
        self.assertTrue(markets.hasFocus())
        self.assertFalse(home.property("focusRing"))
        self.assertTrue(markets.property("focusRing"))
        QTest.keyClick(markets, Qt.Key.Key_Return)
        self.settle()
        self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
        self.assertTrue(w.market_submenu.isVisible())
        QTest.keyClick(markets, Qt.Key.Key_Down)
        value = w.market_sections["value"]
        self.assertTrue(value.hasFocus())
        QTest.keyClick(value, Qt.Key.Key_Down)
        QTest.keyClick(w.market_sections["volume"], Qt.Key.Key_Enter)
        w.markets_view.show_category.assert_called_with("volume")
        self.assertTrue(w.market_sections["volume"].isChecked())
        QTest.keyClick(w.market_sections["volume"], Qt.Key.Key_Space)
        w.markets_view.show_category.assert_called_with("volume")
        QTest.keyClick(w.market_sections["volume"], Qt.Key.Key_End)
        self.assertTrue(w.nav["system"].hasFocus())
        QTest.keyClick(w.nav["system"], Qt.Key.Key_Home)
        self.assertTrue(w.sidebar_hide.hasFocus())
        self.assertTrue(w.sidebar_hide.property("focusRing"))
        QTest.keyClick(w.sidebar_hide, Qt.Key.Key_Up)  # stays on the first item
        self.assertTrue(w.sidebar_hide.hasFocus())
        QTest.keyClick(w.sidebar_hide, Qt.Key.Key_Return)  # hide from the keyboard: focus moves to show
        self.settle()
        self.assertTrue(w.sidebar_collapsed)
        self.assertTrue(w.sidebar_show.hasFocus())
        self.assertTrue(w.sidebar_show.property("focusRing"))
        QTest.keyClick(w.sidebar_show, Qt.Key.Key_Space)
        self.settle()
        self.assertFalse(w.sidebar_collapsed)
        self.assertTrue(w.sidebar_hide.hasFocus())
        # A mouse click never leaves a ring behind.
        QTest.mouseClick(w.nav["tools"], Qt.MouseButton.LeftButton)
        self.settle()
        self.assertEqual(w.stack.currentIndex(), w.route_indices["tools"])
        self.assertFalse(w.nav["tools"].property("focusRing"))
        self.assertFalse(w.market_submenu.isVisible())

    def test_short_window_scrolls_the_rail_to_the_focused_item(self):
        w = self.window()
        w.resize(1000, 700)
        w.navigate("markets")
        self.settle()
        bar = w.rail_scroll.verticalScrollBar()
        self.assertGreater(bar.maximum(), 0)  # nav + sub-menu do not fit; bottom controls stay pinned
        for widget in (w.paper_halt, w.theme, w.language):
            self.assertTrue(w.sidebar.rect().contains(QRect(widget.mapTo(w.sidebar, QPoint(0, 0)), widget.size())))
        last = w.nav["system"]
        last.setFocus(Qt.FocusReason.TabFocusReason)
        self.settle()
        top = last.mapTo(w.rail_scroll.viewport(), last.rect().topLeft()).y()
        self.assertGreaterEqual(top, 0)
        self.assertLessEqual(top + last.height(), w.rail_scroll.viewport().height())
        self.assertLessEqual(w.minimumSizeHint().height(), 700)

    # Light and dark: the rail's own containers never paint the page background over the sidebar surface.
    def test_light_and_dark_rail_surfaces_and_rules(self):
        w = self.window()
        w.markets_view.show_category = Mock()
        w.navigate("markets")
        for index, palette in ((0, LIGHT), (1, DARK)):
            w.theme.setCurrentIndex(index)
            self.settle()
            with self.subTest(theme=index):
                image = w.sidebar.grab().toImage()
                nav_host = w.rail_scroll.widget()
                spot = nav_host.mapTo(w.sidebar, nav_host.rect().bottomLeft())
                self.assertEqual(QColor(image.pixel(spot.x() + 20, spot.y() - 3)).name(), palette.surface.lower())
                self.assertFalse(w.sidebar_hide.icon().isNull())
                self.assertFalse(w.sidebar_show.icon().isNull())
                rail = w.sidebar.styleSheet()
                self.assertEqual(rail, rail_stylesheet(palette, bool(index)))
                self.assertIn(f"QPushButton[subnav='true']:checked {{ color: {palette.accent};", rail)
                self.assertNotRegex(rail, r"font-weight:\s*(700|800|900|bold)")
                # Owner: lighter dividing lines. The rail edge sits between the surface and the border token.
                edge = QColor(image.pixel(w.sidebar.width() - 1, w.sidebar.height() // 2))
                surface, border = QColor(palette.surface), QColor(palette.border)
                self.assertEqual(edge.name(), mix(palette.surface, palette.border, 0.45))
                self.assertLess(abs(edge.lightness() - surface.lightness()), abs(border.lightness() - surface.lightness()))
                # The window sheet stays the integrator's: no rail rules leak into it.
                self.assertNotIn("subnav", w.styleSheet())
                self.assertEqual(w.styleSheet(), window_stylesheet(palette, bool(index)))
                # Sub-items: airy text rows, no box (no background) unless keyboard-focused.
                for button in w.market_sections.values():
                    self.assertGreaterEqual(button.height(), 30)
                checked = w.market_sections["value"]
                w.open_market_section("value")
                self.settle()
                spot = checked.mapTo(w.sidebar, checked.rect().center())
                self.assertEqual(QColor(w.sidebar.grab().toImage().pixel(spot.x() + 40, spot.y())).name(),
                                 palette.surface.lower())


if __name__ == "__main__":
    unittest.main()
