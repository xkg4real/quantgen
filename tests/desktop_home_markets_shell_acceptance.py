"""Owner 2026-11-13: hidden, downward Markets menu; every destination stays in Markets. Offline.

Owner 2026-11-17, verbatim: "지수, 주식, 크립토 하고 쭉쭉 잇는데, 이 범주까지만 살려두고, 그다음 하위범주 ex) 지수 기준 코스피,
코스닥, s&p... 이부분 그냥 좌측 바로가기 ui 삭제합니다" and "정작 '주식' 바로가기는 눌리지 않습니다": the rail keeps the nine
categories with no rows under them; a category with several destinations opens its main screen (`market_hub.MarketHub`),
one with a single destination opens it. The tests that walked the country rows (국내/미국) now walk the categories and
the category screens; the real-click test (QWindow hit testing) is kept for the category rows."""
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
        # Owner-approved draft 2026-11-17 (draft_06_library.png): the Research Library fills the window like the stock
        # detail screen; the page itself no longer scrolls, its canvas does. The scroll position Ctrl+B must keep there
        # is the canvas's, given a range by session records (RUNNING runs, nothing computed or fetched).
        from core.research.runs import new_run
        for index in range(14):
            w.session.put(new_run({"symbol": f"T{index:02d}", "model": "gbm", "horizon_days": 21, "n_paths": 200}))
        w.refresh_views()
        for route in ("library", "system"):
            w.navigate(route)
            self.settle()
            page = w.stack.currentWidget()
            self.assertIsInstance(page, QScrollArea)
            scroller = w.library_workspace.canvas_scroll if route == "library" else page
            bar = scroller.verticalScrollBar()
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

    def test_initially_hidden_hover_reveals_and_leave_hides_without_navigating(self):
        w=self.window()
        self.assertTrue(w.market_submenu.isHidden())
        self.hover(w.nav['markets']);self.assertTrue(w.market_submenu.isVisible())
        self.assertEqual(w._route(),'home')
        self.assertEqual(tuple(b.text() for b in w.market_sections.values()),ENGLISH)
        self.park_pointer(w);QTest.qWait(CLOSE_DELAY_MS+150)
        self.assertTrue(w.market_submenu.isHidden())

    def test_window_mouse_click_on_hovered_category_opens_its_main_screen(self):
        # Send through QWindow hit testing, as an OS click does. QPushButton.click()
        # skips the application filter and cannot reproduce a disappearing menu.
        w = self.window()
        for category in ('indices', 'stocks', 'fx', 'govt', 'etf', 'economy'):
            w.navigate('home')
            self.hover(w.nav['markets'])
            row = w.market_sections[category]
            w.rail_scroll.ensureWidgetVisible(row, 0, 8)
            self.hover(row)
            self.assertEqual(w.rail_flyouts.panels, [])     # no rows under a category any more
            QTest.mouseClick(w.windowHandle(), Qt.MouseButton.LeftButton, pos=row.mapTo(w, row.rect().center()))
            self.settle()
            self.assertEqual(w._route(), 'markets')
            self.assertIs(w.markets_content.currentWidget(), w.market_hub)
            self.assertEqual(w.market_hub.current_category(), category)
            self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], [category])
        # The stocks screen's 국내 card opens the Korean stock list.
        w.open_market_hub('stocks'); self.settle()
        card = w.market_hub.cards[0]
        QTest.mouseClick(w.windowHandle(), Qt.MouseButton.LeftButton, pos=card.mapTo(w, QPoint(24, 24)))
        self.settle()
        self.assertIs(w.markets_content.currentWidget(), w.markets_view)
        self.assertEqual(w.markets_view.current_market(), 'kr')

    def test_single_destination_mouse_click_needs_no_submenu(self):
        w = self.window()
        for category, target in (('crypto', ('market', 'crypto', '')),
                                 ('futures', ('workspace', 'futures', 'derivatives', 'board')),
                                 ('corp', ('workspace', 'corp', 'bonds', ''))):
            w.navigate('home')
            self.hover(w.nav['markets'])
            row = w.market_sections[category]
            w.rail_scroll.ensureWidgetVisible(row, 0, 8)
            self.hover(row)
            self.assertEqual(w.rail_flyouts.panels, [])
            self.assertFalse(row.chevron)
            QTest.mouseClick(w.windowHandle(), Qt.MouseButton.LeftButton,
                             pos=row.mapTo(w, row.rect().center()))
            self.settle()
            self.assertEqual(w._route(), 'markets')
            if target[0] == 'market':
                self.assertEqual(w.markets_view.current_market(), target[1])
            else:
                self.assertEqual(w.market_asset_category, category)

    def test_categories_have_no_rows_under_them_and_never_cover_the_page(self):
        w=self.window();w.resize(1440,1000)
        self.hover(w.nav['markets'])
        menu=w.rail_flyouts
        for key in CATEGORY_KEYS:
            row=w.market_sections[key]
            w.rail_scroll.ensureWidgetVisible(row,0,8)
            self.hover(row)
            self.assertEqual(menu.panels,[],key)
            self.assertFalse(row.chevron,key)
            self.assertTrue(w.sidebar.isAncestorOf(row))
            self.assertLessEqual(row.mapTo(w.sidebar,QPoint(0,0)).x()+row.width(),w.sidebar.width())
        self.assertEqual(w._route(),'home')   # hovering never navigates

    def test_outside_window_click_dismisses_without_navigating(self):
        w = self.window()
        self.hover(w.nav['markets']); self.hover(w.market_sections['stocks'])
        QTest.mouseClick(w.windowHandle(), Qt.MouseButton.LeftButton,
                         pos=QPoint(w.width() - 12, 30))
        self.settle()
        self.assertTrue(w.market_submenu.isHidden())
        self.assertEqual(w._route(), 'home')

    def test_every_leaf_stays_in_markets_and_tools_have_independent_state(self):
        w=self.window();view=w.markets_view
        for category in shell_rail.market_menu('en'):
            for leaf in walk((category,)):
                with self.subTest(leaf=leaf):
                    self.assertIn(leaf[0],('market','series','workspace'))
                    w.open_market_leaf(leaf);self.settle()
                    self.assertEqual(w._route(),'markets')
                    self.assertTrue(w.nav['markets'].isChecked())
                    self.assertFalse(w.nav['home'].isChecked() or w.nav['tools'].isChecked())
                    page=w.markets_content.currentWidget()
                    if leaf[0]=='market':
                        self.assertIs(page,view)
                        self.assertEqual(view.current_market(), leaf[1])
                        if leaf[2]:
                            self.assertEqual(view.current_category(), leaf[2])
                        else:
                            self.assertIn(view.current_category(), shell_rail.page_categories(leaf[1]))
                    elif leaf[0]=='series':self.assertEqual(page.symbol,leaf[2])
                    else:
                        self.assertIsNot(page.pane,getattr(w,leaf[2]))
                        if leaf[3]:self.assertEqual(page.pane.tool.currentData(),leaf[3])
                    self.assertEqual([k for k,b in w.market_sections.items() if b.isChecked()],[category.key])
        w.open_stock_chart('005930');self.assertIs(w.markets_content.currentWidget(),view)
        w.open_market_leaf(('series','indices','^KS11'))
        w.open_live_chart();self.assertIs(w.markets_content.currentWidget(),view)

    def test_indices_use_observed_history_and_keep_destination_through_language_changes(self):
        from quantgen_desktop.home_view import MarketHistory
        w=self.window();w.open_market_leaf(('series','indices','^GSPC'))
        page=w.markets_content.currentWidget()
        page._loaded((page.epoch,MarketHistory('^GSPC',('2026-01-01','2026-01-02'),(100,101),'YFINANCE')))
        self.assertIn('101',page.price.text());self.assertIn('YFINANCE',page.status.text())
        self.assertEqual(page.selector.count(),5)
        for language in ('ko','en'):
            w.set_language(language);self.settle()
            self.assertEqual(page.symbol,'^GSPC');self.assertEqual(w._route(),'markets')
        w.open_market_leaf(('series','fx','DEXKOUS'))
        self.assertEqual(page.selector.count(),1);self.assertEqual(page.symbol,'DEXKOUS')

    def test_keyboard_opens_walks_selects_and_dismisses(self):
        w=self.window();button=w.nav['markets'];button.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(button,Qt.Key.Key_Return);self.settle()
        self.assertIs(w.markets_content.currentWidget(),w.market_hub)      # 시장 itself: the 시장 main screen
        self.assertIsNone(w.market_hub.current_category())
        QTest.keyClick(button,Qt.Key.Key_Down)
        self.assertTrue(w.market_sections['indices'].hasFocus())
        QTest.keyClick(w.market_sections['indices'],Qt.Key.Key_Right);self.settle()
        menu=w.rail_flyouts
        self.assertEqual(menu.panels,[])                                  # nothing opens under a category
        QTest.keyClick(w.market_sections['indices'],Qt.Key.Key_Down)
        self.assertTrue(w.market_sections['stocks'].hasFocus())
        QTest.keyClick(w.market_sections['stocks'],Qt.Key.Key_Return);self.settle()
        self.assertEqual(w.market_hub.current_category(),'stocks')
        self.assertTrue(w.market_submenu.isHidden())
        menu.root_clicked(w.market_sections['crypto'],keyboard=True);self.settle()
        QTest.qWait(OPEN_DELAY_MS+50)
        QTest.keyClick(w.market_sections['crypto'],Qt.Key.Key_Escape)
        self.assertTrue(w.market_submenu.isHidden())

    def test_collapsed_rail_language_and_no_global_translation_pass(self):
        w=self.window();w.set_sidebar_collapsed(True)
        w.market_strip.click();self.settle()
        self.assertFalse(w.sidebar_collapsed);self.assertTrue(w.market_submenu.isVisible())
        for language,names in (('ko',KOREAN),('en',ENGLISH)):
            w.set_language(language);self.settle()
            self.assertTrue(w.market_submenu.isHidden())
            self.assertEqual(tuple(b.text() for b in w.market_sections.values()),names)
            w.rail_flyouts.root_clicked(w.market_sections['etf'],keyboard=True);self.settle()
            self.assertEqual(w.rail_flyouts.panels,[])
            w.open_market_hub('etf');self.settle()
            self.assertEqual([c.title.text() for c in w.market_hub.cards],
                             ['국내','미국'] if language=='ko' else ['Korea','US'])
            w.rail_flyouts.open_root();self.settle()
        passes=[];w.localizer.apply=lambda:passes.append(1)
        w.rail_flyouts.close_all();self.settle()
        w.rail_flyouts.root_clicked(w.market_sections['stocks']);self.settle()
        self.assertEqual(passes,[])

    def test_small_window_keyboard_scroll_and_dark_theme(self):
        w=self.window();w.resize(1000,700)
        for theme,palette in ((0,LIGHT),(1,DARK)):
            w.change_theme(theme);menu=w.rail_flyouts
            menu.open_root(keyboard=True);self.settle()
            last=w.market_sections['economy'];last.setFocus(Qt.FocusReason.TabFocusReason)
            w.rail_scroll.ensureWidgetVisible(last,0,8);self.settle()
            top=last.mapTo(w.rail_scroll.viewport(),QPoint(0,0)).y()
            self.assertGreaterEqual(top,0)
            self.assertLessEqual(top+last.height(),w.rail_scroll.viewport().height())
            self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0)
            self.assertEqual(w.sidebar.styleSheet(),rail_stylesheet(palette,bool(theme)))
            w.nav['tools'].click();self.assertTrue(w.market_submenu.isHidden())


if __name__=='__main__':unittest.main()
