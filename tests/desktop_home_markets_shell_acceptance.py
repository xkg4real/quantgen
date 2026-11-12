"""Left rail: hide/show with memory, the Markets sub-menu and keyboard use (owner 2026-11-11, UI-D7 points 2-3).

Owner: "시장 누르면 하위 UI로 종목 고를수있게 바꿔주고, 왼쪽 UI화면들 숨기는 기능도 필요해. 공간이슈때문에".
Owner ruling UI-D10 (2026-11-11): "시장에서 그냥 국장 미장 코인 이런걸 하부ui로 두고, ..." — the sub-menu lists the
markets and calls `markets_view.show_market(key)`; the five ranking categories and stock search it listed under UI-D7
are now inside each market's page (these tests pinned them; updated for UI-D10).
Owner ruling UI-D11 (2026-11-12, with a TradingView-style menu image): "시장 하위 유아이를 저렇게 두지 말고 이런식으로
큰 범주로 묶고 ... 주식 ... 마우스 올려놓으면 더 하부로 국내, 미국, 글로벌 ... 국내에 마우스 올려놓으면 다시 거래대금 거래량
급상승 급하락 이렇게 누를수있게 ... 코인이 뭐야". The tests that pinned the three market items (국내 주식 / 미국 주식 /
코인: their keys, texts, the click that opened a market, the arrow walk over them and their highlight) now pin the
nine categories (지수 … 월드 이코노미), the click that opens a flyout, the hover and keyboard cascades, each leaf's
landing page, the hidden rail's menu button, and that a flyout costs no window-wide language pass.
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
from quantgen_desktop.rail_menu import (CLOSE_DELAY_MS, OPEN_DELAY_MS, PANEL_GAP, ROW_HEIGHT, SHADOW, SWITCH_DELAY_MS,
                                        MarketRailRow)
from quantgen_desktop.typography import (MARKET_ROW_HEIGHT, RAIL_COLLAPSED_WIDTH, SIDEBAR_WIDTH_RANGE,
                                         flyout_stylesheet, mix, rail_stylesheet, window_stylesheet)

CATEGORY_KEYS = ("indices", "stocks", "crypto", "futures", "fx", "govt", "corp", "etf", "economy")
ENGLISH = ("Indices", "Stocks", "Crypto", "Futures", "Forex", "Government bonds", "Corporate bonds", "ETFs",
           "World economy")
KOREAN = ("지수", "주식", "크립토", "선물", "외환", "국채", "회사채", "ETF", "월드 이코노미")


def walk(nodes):
    """Every leaf under a 시장 menu (its `leaf` tuples)."""
    for node in nodes:
        if node.children:
            yield from walk(node.children)
        else:
            yield node.leaf


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
        self.addCleanup(self.park_pointer, w)
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

    def hover(self, widget):
        """Point at a widget as a person does and wait out the menu's open or switch delay."""
        QTest.mouseMove(widget)
        QTest.qWait(max(OPEN_DELAY_MS, SWITCH_DELAY_MS) + 90)
        self.settle()

    def park_pointer(self, w):
        """Leave the pointer off the rail, so a later window is not opened under it."""
        try:
            QTest.mouseMove(w, QPoint(w.width() - 5, w.height() - 5))
        except RuntimeError:
            pass

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

    # Owner ruling UI-D11: under 시장 the image's big categories, each a roomy row with a chevron.
    def test_market_rows_are_the_images_big_categories_and_open_flyouts(self):
        w = self.window()
        w.resize(1360, 940)
        self.settle()
        self.assertEqual(tuple(w.market_sections), CATEGORY_KEYS)
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
        w.navigate("markets")
        self.settle()
        for row in w.market_sections.values():
            self.assertIsInstance(row, MarketRailRow)
            self.assertTrue(row.chevron and row.property("flyout"))
            self.assertEqual(row.height(), MARKET_ROW_HEIGHT)  # roomy while the rail has the room
        # A click opens the row's flyout (the menu), never a page by itself.
        w.markets_view.show_market = Mock()
        fly = w.rail_flyouts
        for key, title in zip(CATEGORY_KEYS, ENGLISH):
            w.market_sections[key].click()
            self.settle()
            with self.subTest(key=key):
                self.assertEqual(fly.open_path(), (title,))
                self.assertIs(fly.anchors[0], w.market_sections[key])
                self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
        w.markets_view.show_market.assert_not_called()
        w.market_sections["stocks"].click()
        self.settle()
        # 주식 › 국내 / 미국 only: no data path for 글로벌 exists, so no dead item is shown.
        self.assertEqual([r.text() for r in fly.panels[0].rows], ["Korea", "US"])
        fly.close_all()
        for old in ("rankings", "value", "search", "indices", "stocks"):  # not market pages
            with self.assertRaises(ValueError):
                w.open_market_section(old)

    def test_menu_tree_reaches_every_market_page_and_only_what_the_app_has(self):
        w = self.window(show=False)
        from quantgen_desktop.home_view import HOME_MARKETS
        from quantgen_desktop.markets_view import MARKET_PAGES
        for language in ("en", "ko"):
            menu = shell_rail.market_menu(language)
            self.assertEqual(tuple(node.key for node in menu), CATEGORY_KEYS)
            self.assertEqual(tuple(node.text for node in menu), ENGLISH if language == "en" else KOREAN)
            self.assertTrue(all(node.children for node in menu))
            leaves = [leaf for leaf in walk(menu)]
            pages = {leaf[1] for leaf in leaves if leaf[0] == "market"}
            self.assertEqual(pages, {key for key, _en, _ko in MARKET_PAGES})
            for leaf in leaves:
                with self.subTest(language=language, leaf=leaf):
                    if leaf[0] == "market":
                        self.assertIn(leaf[2], shell_rail.page_categories(leaf[1]))
                    elif leaf[0] == "home":
                        self.assertIn(leaf[1], {info.symbol for info in HOME_MARKETS})
                    else:
                        self.assertEqual(leaf[0], "tool")
                        pane = getattr(w, leaf[1])
                        if leaf[2]:
                            self.assertGreaterEqual(pane.tool.findData(leaf[2]), 0)
        self.assertEqual(shell_rail.page_categories("crypto"), ("value", "gainers", "losers"))
        for page in ("etf_kr", "etf_us"):
            self.assertEqual(shell_rail.page_categories(page), ("value", "volume", "gainers", "losers"))
        self.assertEqual(shell_rail.page_categories("kr"), ("value", "volume", "gainers", "losers", "cap"))
        etf = next(node for node in shell_rail.market_menu("ko") if node.key == "etf")
        self.assertEqual([n.text for n in etf.children], ["국내", "미국"])
        self.assertEqual({n.note for n in etf.children}, {"시가총액 순위 없음"})
        self.assertTrue(all("순자산(AUM)" in n.note_tip for n in etf.children))  # the reason, as a tooltip
        self.assertEqual(shell_rail.market_sections(), tuple(zip(CATEGORY_KEYS, ENGLISH)))

    def test_hover_opens_three_levels_aligned_with_their_rows_and_leaving_closes_them(self):
        w = self.window()
        w.resize(1440, 900)
        w.navigate("markets")
        self.settle()
        fly, host = w.rail_flyouts, w.centralWidget()
        middle = lambda widget: widget.mapTo(host, widget.rect().center()).y()
        stocks = w.market_sections["stocks"]
        self.hover(stocks)
        self.assertEqual(fly.open_path(), ("Stocks",))
        first = fly.panels[0]
        self.assertEqual([r.text() for r in first.rows], ["Korea", "US"])
        self.assertLessEqual(abs(middle(first.rows[0]) - middle(stocks)), 1)  # level with the row it came from
        self.assertEqual(first.x() + SHADOW, w.sidebar.width() + PANEL_GAP)  # right of the rail
        self.assertTrue(stocks.open)
        self.hover(first.rows[0])
        self.assertEqual(fly.open_path(), ("Stocks", "Korea"))
        second = fly.panels[1]
        self.assertEqual([r.text() for r in second.rows], ["Trading value", "Volume", "Top gainers", "Top losers",
                                                          "Market cap"])
        self.assertEqual([r.node.leaf for r in second.rows][0], ("market", "kr", "value"))
        self.assertLessEqual(abs(middle(second.rows[0]) - middle(first.rows[0])), 1)
        self.assertEqual(second.x() + SHADOW, first.x() + first.width() - SHADOW + PANEL_GAP)
        self.assertTrue(all(r.height() == ROW_HEIGHT for r in (*first.rows, *second.rows)))
        self.assertEqual([r.chevron for r in first.rows], [True, True])
        self.assertFalse(any(r.chevron for r in second.rows))
        self.hover(second.rows[2])  # a leaf: nothing more opens
        self.assertEqual(len(fly.panels), 2)
        self.hover(first.rows[1])  # 미국: its rankings replace 국내's
        self.assertEqual(fly.open_path(), ("Stocks", "US"))
        self.assertEqual(fly.panels[1].rows[0].node.leaf, ("market", "us", "value"))
        self.hover(w.market_sections["etf"])  # another rail row: its own flyout
        self.assertEqual(fly.open_path(), ("ETFs",))
        self.assertFalse(stocks.open)
        QTest.mouseMove(w.stack, QPoint(w.stack.width() - 30, w.stack.height() - 30))
        QTest.qWait(CLOSE_DELAY_MS + 200)
        self.assertFalse(fly.is_open())
        self.assertFalse(w.market_sections["etf"].open)

    def test_a_move_toward_the_open_flyout_over_a_sibling_keeps_it(self):
        w = self.window()
        w.resize(1440, 900)
        w.navigate("markets")
        self.settle()
        fly = w.rail_flyouts
        self.hover(w.market_sections["stocks"])
        self.hover(fly.panels[0].rows[0])
        korea = fly.panels[1]
        QTest.mouseMove(fly.panels[0].rows[1])  # crossing 미국 on the way
        QTest.qWait(40)
        QTest.mouseMove(korea.rows[2])
        QTest.qWait(SWITCH_DELAY_MS + 150)
        self.assertEqual(fly.open_path(), ("Stocks", "Korea"))
        self.assertIs(fly.panels[1], korea)

    def test_every_leaf_lands_on_its_page_market_and_category(self):
        w = self.window()
        w.resize(1440, 900)
        w.navigate("markets")
        self.settle()
        fly, view = w.rail_flyouts, w.markets_view
        for category in shell_rail.market_menu("en"):
            paths = [(category, leaf) for leaf in category.children if not leaf.children]
            paths += [(sub, leaf) for sub in category.children for leaf in sub.children]
            for parent, leaf in paths:
                with self.subTest(leaf=leaf.leaf):
                    self.assertTrue(w.market_submenu.isVisible())  # Markets, or a page a flyout opened
                    fly.open_root(w.market_sections[category.key])
                    if parent is not category:
                        fly.open_child(next(r for r in fly.panels[0].rows if r.node.key == parent.key))
                    row = next(r for r in fly.panels[-1].rows if r.node == leaf)
                    QTest.mouseClick(row, Qt.MouseButton.LeftButton)
                    self.settle()
                    self.assertFalse(fly.is_open())
                    kind = leaf.leaf[0]
                    highlighted = [k for k, b in w.market_sections.items() if b.isChecked()]
                    self.assertTrue(w.market_submenu.isVisible())
                    if kind == "market":
                        _kind, page, ranking = leaf.leaf
                        self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
                        self.assertEqual((view.current_market(), view.current_category()), (page, ranking))
                        self.assertFalse(view.showing_stock())
                        self.assertEqual(highlighted, [shell_rail.PAGE_CATEGORY[page]])
                    elif kind == "home":
                        self.assertEqual(w.stack.currentIndex(), w.route_indices["home"])
                        self.assertEqual(w.home_view.selected, leaf.leaf[1])
                        self.assertTrue(w.nav["home"].isChecked())
                        self.assertEqual(highlighted, [shell_rail.HOME_CATEGORY[leaf.leaf[1]]])
                    else:
                        _kind, name, sub = leaf.leaf
                        pane = getattr(w, name)
                        self.assertEqual(w.stack.currentIndex(), w.route_indices["tools"])
                        self.assertIs(w.tool_host.currentWidget(), pane)
                        self.assertTrue(w.tool_buttons[name].isChecked())
                        if sub:
                            self.assertEqual(pane.tool.currentData(), sub)
                        self.assertEqual(highlighted, [shell_rail.TOOL_CATEGORY[name]])
        # Another tool picked on that page: the rows stay; the highlight follows the tool.
        w.show_tool(w.structuring)
        self.assertTrue(w.market_submenu.isVisible())
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], [])
        w.show_tool(w.rates)
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["govt"])
        w.nav["guide"].click()  # a page chosen in the rail: the 시장 rows fold away again
        self.assertFalse(w.market_submenu.isVisible())

    def test_keyboard_opens_walks_and_closes_the_flyouts(self):
        w = self.window()
        w.resize(1440, 900)
        w.navigate("markets")
        self.settle()
        fly = w.rail_flyouts
        w.markets_view.show_market = Mock()
        w.markets_view.show_category = Mock()
        etf = w.market_sections["etf"]
        etf.setFocus(Qt.FocusReason.TabFocusReason)
        self.settle()
        QTest.keyClick(etf, Qt.Key.Key_Right)
        focus = lambda: QApplication.focusWidget()
        self.assertEqual(fly.open_path(), ("ETFs",))
        self.assertIs(focus(), fly.panels[0].rows[0])
        self.assertTrue(focus().property("focusRing"))
        QTest.keyClick(focus(), Qt.Key.Key_Down)
        self.assertEqual(focus().text(), "US")
        QTest.keyClick(focus(), Qt.Key.Key_Down)  # wraps like a menu
        self.assertEqual(focus().text(), "Korea")
        QTest.keyClick(focus(), Qt.Key.Key_Up)
        QTest.keyClick(focus(), Qt.Key.Key_Right)
        self.assertEqual(fly.open_path(), ("ETFs", "US"))
        self.assertIs(focus(), fly.panels[1].rows[0])
        self.assertTrue(focus().property("focusRing"))
        QTest.keyClick(focus(), Qt.Key.Key_Left)  # back to the row it came from
        self.assertEqual((fly.open_path(), focus().text()), (("ETFs",), "US"))
        self.assertTrue(focus().property("focusRing"))
        QTest.keyClick(focus(), Qt.Key.Key_Escape)  # the last flyout: back to the rail row
        self.assertFalse(fly.is_open())
        self.assertIs(focus(), etf)
        self.assertTrue(etf.property("focusRing"))
        QTest.keyClick(etf, Qt.Key.Key_Return)  # Enter opens it too
        self.assertIs(focus(), fly.panels[0].rows[0])
        QTest.keyClick(focus(), Qt.Key.Key_Return)  # 국내
        QTest.keyClick(focus(), Qt.Key.Key_Down)  # 거래량
        QTest.keyClick(focus(), Qt.Key.Key_Return)
        self.settle()
        self.assertFalse(fly.is_open())
        w.markets_view.show_market.assert_called_with("etf_kr")
        w.markets_view.show_category.assert_called_with("volume")
        self.assertIs(focus(), etf)  # the keyboard user is back on the rail row
        self.assertTrue(etf.property("focusRing"))
        QTest.keyClick(etf, Qt.Key.Key_Right)
        QTest.keyClick(focus(), Qt.Key.Key_Tab)  # Tab leaves the menu
        self.assertFalse(fly.is_open())
        self.assertIs(focus(), etf)
        # ↑/↓ in the rail close an open flyout; Esc anywhere closes one the pointer opened.
        QTest.keyClick(etf, Qt.Key.Key_Right)
        QTest.keyClick(fly.panels[0].rows[0], Qt.Key.Key_Left)
        QTest.keyClick(etf, Qt.Key.Key_Up)
        self.assertFalse(fly.is_open())
        self.assertIs(focus(), w.market_sections["corp"])
        self.hover(w.market_sections["crypto"])
        self.assertTrue(fly.is_open())
        w.markets_view.search.setFocus(Qt.FocusReason.OtherFocusReason)
        QTest.keyClick(w.markets_view.search, Qt.Key.Key_Escape)
        self.assertFalse(fly.is_open())

    def test_hidden_rail_opens_the_same_menu_from_its_strip(self):
        w = self.window()
        w.resize(1440, 900)
        w.navigate("markets")
        w.set_sidebar_collapsed(True)
        self.settle()
        fly, view = w.rail_flyouts, w.markets_view
        strip = w.market_strip
        self.assertTrue(strip.isVisible())
        self.assertEqual(strip.accessibleName(), "Markets")
        self.assertFalse(strip.icon().isNull())
        self.hover(strip)
        top = fly.panels[0]
        self.assertEqual(tuple(r.text() for r in top.rows), ENGLISH)
        self.assertTrue(all(r.chevron for r in top.rows))
        self.assertEqual(top.x() + SHADOW, RAIL_COLLAPSED_WIDTH + PANEL_GAP)
        self.hover(next(r for r in top.rows if r.text() == "Stocks"))
        self.hover(next(r for r in fly.panels[1].rows if r.text() == "US"))
        self.assertEqual(fly.open_path(), ("", "Stocks", "US"))
        QTest.mouseClick(next(r for r in fly.panels[2].rows if r.text() == "Top gainers"), Qt.MouseButton.LeftButton)
        self.settle()
        self.assertFalse(fly.is_open())
        self.assertEqual((view.current_market(), view.current_category()), ("us", "gainers"))
        self.assertTrue(w.sidebar_collapsed)
        strip.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(strip, Qt.Key.Key_Right)
        self.assertIs(QApplication.focusWidget(), fly.panels[0].rows[0])
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Escape)
        self.assertIs(QApplication.focusWidget(), strip)
        self.assertIn(strip, w.rail_buttons())
        fly.root_clicked(strip)
        QTest.keyClick(w.stack, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)  # the rail comes back
        self.settle()
        self.assertFalse(fly.is_open())
        self.assertFalse(w.sidebar_collapsed)

    def test_a_click_elsewhere_a_page_change_a_resize_or_a_theme_closes_the_menu(self):
        w = self.window()
        w.navigate("markets")
        self.settle()
        fly = w.rail_flyouts
        row = w.market_sections["fx"]
        fly.open_root(row)
        QTest.mouseClick(fly.panels[0].rows[0], Qt.MouseButton.RightButton)  # inside: stays
        self.assertTrue(fly.is_open())
        QTest.mouseClick(w.markets_view.search, Qt.MouseButton.LeftButton)
        self.assertFalse(fly.is_open())
        for close in (lambda: w.navigate("markets"), lambda: w.resize(1300, 800), lambda: w.theme.setCurrentIndex(1),
                      lambda: w.set_language("ko")):
            fly.open_root(w.market_sections["fx"])
            self.assertTrue(fly.is_open())
            close()
            self.settle()
            self.assertFalse(fly.is_open())
            self.assertFalse(w.market_sections["fx"].open)

    def test_highlight_follows_what_markets_shows(self):
        w = self.window()
        view = w.markets_view
        w.navigate("markets")
        # The Markets page reports its default market (국내 주식, under 주식) on the first visit.
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["stocks"])
        view.rankings.set_page("crypto")  # the page's own change (signal) moves the highlight
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["crypto"])
        view.rankings.set_page("etf_us")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["etf"])
        view.current_market = lambda: "us"  # the page may report its own market
        w.navigate("home")
        w.navigate("markets")
        self.assertTrue(w.market_sections["stocks"].isChecked())
        view.showing_stock = lambda: True  # a stock's screen keeps the market it was opened over
        w.navigate("markets")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["stocks"])
        view.current_market = lambda: None  # the page reports nothing: the last choice is kept
        view.showing_stock = lambda: False
        w.market_sections["crypto"].click()  # a click opens the flyout; it does not move the highlight
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["stocks"])
        w.rail_flyouts.close_all()
        w.navigate("guide")
        w.navigate("markets")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["stocks"])

    def test_highlight_follows_the_page_when_it_announces_its_market(self):
        class Page(QObject):
            market_changed = pyqtSignal(str)

        w = self.window(show=False)
        w.navigate("markets")
        page = Page()
        w.connect_market_sections(page)
        page.market_changed.emit("crypto")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["crypto"])
        page.market_changed.emit("etf_kr")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["etf"])
        page.market_changed.emit("us")
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], ["stocks"])
        w.connect_market_sections(object())  # a page without the signal is fine

    def test_a_page_without_markets_still_opens(self):
        w = self.window()
        real = w.markets_view
        stub = SimpleNamespace(showing_stock=lambda: False, search=Mock())
        w.markets_view = stub
        try:
            w.open_market_section("us")  # no market pages yet: Markets opens, nothing fails
            self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
            self.assertTrue(w.market_sections["stocks"].isChecked())
        finally:
            w.markets_view = real

    def test_menu_and_toggles_in_korean_and_english_without_rebuilding_or_fetching(self):
        w = self.window()
        w.navigate("markets")
        buttons = dict(w.market_sections)
        fly = w.rail_flyouts
        for language, texts, hide, show in (("ko", KOREAN, "메뉴 숨기기 (Ctrl+B)", "메뉴 펼치기 (Ctrl+B)"),
                                            ("en", ENGLISH, "Hide menu (Ctrl+B)", "Show menu (Ctrl+B)"),
                                            ("ko", KOREAN, "메뉴 숨기기 (Ctrl+B)", "메뉴 펼치기 (Ctrl+B)")):
            fly.open_root(buttons["stocks"])
            w.set_language(language)
            self.settle()
            with self.subTest(language=language):
                self.assertFalse(fly.is_open())  # an open flyout closes; the next opens in the new language
                self.assertEqual(tuple(b.text() for b in w.market_sections.values()), texts)
                self.assertEqual(tuple(b.accessibleName() for b in w.market_sections.values()), texts)
                self.assertEqual((w.sidebar_hide.toolTip(), w.sidebar_show.toolTip()), (hide, show))
                self.assertEqual(w.nav["markets"].text(), "시장" if language == "ko" else "Markets")
                self.assertEqual(w.market_sections, buttons)
                self.assertTrue(w.market_submenu.isVisible())
                fly.open_root(buttons["etf"])
                fly.open_child(fly.panels[0].rows[0])
                korean = language == "ko"
                self.assertEqual([r.text() for r in fly.panels[0].rows], ["국내", "미국"] if korean else ["Korea", "US"])
                self.assertEqual([r.text() for r in fly.panels[1].rows],
                                 ["거래대금", "거래량", "급상승", "급하락"] if korean
                                 else ["Trading value", "Volume", "Top gainers", "Top losers"])
                self.assertEqual(fly.panels[1].note.text(), "시가총액 순위 없음" if korean else "No ranking by market cap")
                self.assertIn("순자산" if korean else "net assets", fly.panels[1].note.toolTip())
                fly.close_all()
                fly.open_root(buttons["fx"])
                self.assertEqual(fly.panels[0].rows[1].text(), "현물·선물환·캐리" if korean else "Spot, forward && carry")
                self.assertEqual(fly.panels[0].rows[1].accessibleName(),
                                 "현물·선물환·캐리" if korean else "Spot, forward & carry")
                fly.close_all()
        self.assertEqual(w.sidebar_hide.accessibleName(), "메뉴 숨기기")
        restored = self.window(language="ko")
        self.assertEqual(tuple(b.text() for b in restored.market_sections.values()), KOREAN)
        # Network and jobs are patched to fail this test: nothing was fetched or started.

    def test_flyouts_open_without_a_window_wide_language_pass(self):
        w = self.window()
        w.navigate("markets")
        for _ in range(3):
            self.settle()
        passes = []
        w.localizer.apply = lambda: passes.append(1)
        fly = w.rail_flyouts
        for key in CATEGORY_KEYS:
            fly.open_root(w.market_sections[key])
            first = fly.panels[0].rows[0]
            if first.node.children:
                fly.open_child(first)
            self.settle()
            fly.close_all()
            self.settle()
        QTest.qWait(100)
        self.settle()
        self.assertEqual(passes, [])

    # Keyboard: arrows walk the rail, Return opens, the ring shows for keyboard focus only.
    def test_rail_keyboard_walk_and_focus_ring(self):
        w = self.window()
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
        indices = w.market_sections["indices"]
        self.assertTrue(indices.hasFocus())
        QTest.keyClick(indices, Qt.Key.Key_Down)
        self.assertTrue(w.market_sections["stocks"].hasFocus())
        QTest.keyClick(w.market_sections["stocks"], Qt.Key.Key_End)
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
        QTest.keyClick(w.sidebar_show, Qt.Key.Key_Down)  # the hidden rail's 시장 button is next
        self.assertTrue(w.market_strip.hasFocus())
        QTest.keyClick(w.market_strip, Qt.Key.Key_Up)
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
        # UI-D10: three market sub-items instead of six; the rail scrolls only if it must, and the bottom
        # controls stay pinned either way.
        self.assertGreaterEqual(bar.maximum(), 0)
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
        w.markets_view.show_market = Mock()
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
                    self.assertGreaterEqual(button.height(), 26)  # 820 px high: tightened so the rail need not scroll
                checked = w.market_sections["stocks"]
                w.open_market_section("kr")
                self.settle()
                spot = checked.mapTo(w.sidebar, checked.rect().center())
                self.assertEqual(QColor(w.sidebar.grab().toImage().pixel(spot.x() + 40, spot.y())).name(),
                                 palette.surface.lower())
                # The flyouts: the theme's surface in a light-lined 8 px box, their sheet from the same tokens.
                fly = w.rail_flyouts
                fly.open_root(checked)
                panel = fly.panels[0]
                self.assertEqual(panel.styleSheet(), flyout_stylesheet(palette, bool(index)))
                self.assertNotRegex(panel.styleSheet(), r"font-weight:\s*(700|800|900|bold)")
                shot = panel.grab().toImage()
                self.assertEqual(QColor(shot.pixel(SHADOW + 3, panel.height() // 2)).name(), palette.surface.lower())
                edge = QColor(shot.pixel(SHADOW, panel.height() // 2))
                self.assertNotEqual(edge.name(), palette.surface.lower())  # the line
                self.assertLess(abs(edge.lightness() - surface.lightness()), 60)  # a light one
                self.assertTrue(checked.open)
                fly.close_all()
                self.assertFalse(checked.open)


if __name__ == "__main__":
    unittest.main()
