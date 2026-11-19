"""The 시장 main screen and the categories' main screens (owner 2026-11-17), offscreen and offline.

Owner, verbatim: "현재 시장 ui가 클릭해도 화면이 넘어가지지 않습니다 ... 그래도 시장의 메인화면이 별도로 존재하긴 해야합니다 ...
시장 메인화면엔 시장의 하부 메뉴들 바로가기가 세련된 화면으로 구현되어야 하고" · "주식도 마찬가지입니다. 현재 국내주식, 미국주식
바로가기만 가능하고, 정작 '주식' 바로가기는 눌리지 않습니다" · "지수, 주식, 크립토 하고 쭉쭉 잇는데, 이 범주까지만 살려두고,
그다음 하위범주 ... 좌측 바로가기 ui 삭제합니다".

Covered: 시장 opens the root screen (nine category cards in the rail's order, its index strip); a category with several
destinations opens its own screen whose cards are exactly the rail menu's leaves; a category with one destination opens
it directly from the rail and from its card; card chips (destinations, rankings) route like the rail; the 주식 / ETF
screens preview each market's top lists from the market page's own loader and share that cache with it, never loading
with automatic loading off until 불러오기; a preview name opens its stock screen; Back; the rail highlight; language and
theme switches re-render without fetching; closing stops the jobs.
Offline: HTTP and Yahoo fail the test; the ranking loader is a fake; the index strip's series loader fails the test;
Home's index history loader (core.ficc.data.load_series) is blocked, and with automatic loading off it is never called.
"""
import os
import time
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton
from core.market.directory import SymbolDirectory
from core.theme import DARK, LIGHT
from quantgen_desktop import shell_rail
from quantgen_desktop.market_hub import CATEGORY_COPY, DESTINATION_COPY, MarketHub
from tests.desktop_home_markets_markets_acceptance import FakeLoader, kr_batch, us_batch
from tests.qt_fixture_cleanup import delete_owned_widget

APP = QApplication.instance() or QApplication([])
CATEGORY_KEYS = ("indices", "stocks", "crypto", "futures", "fx", "govt", "corp", "etf", "economy")


class MarketHubTests(unittest.TestCase):
    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.market.routing._yahoo_frame"):
            deny = patch(target, side_effect=AssertionError("Network forbidden"))
            deny.start(); self.addCleanup(deny.stop)
        series = patch("quantgen_desktop.market_summary.production_series",
                       side_effect=AssertionError("Index series forbidden"))
        series.start(); self.addCleanup(series.stop)
        # Home's own index chart loads through core.ficc.data.load_series (yfinance), outside the patches
        # above; keep it offline. load_market_history turns the error into a failure state.
        home = patch("core.ficc.data.load_series", side_effect=AssertionError("Home series forbidden"))
        self.home_series = home.start(); self.addCleanup(home.stop)

    def window(self, *, auto=False):
        provider = Mock(side_effect=AssertionError("Provider forbidden"))
        directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        w = ResearchWindow(auto_refresh=auto, locale="ko_KR", market_loader=provider, connections_runner=provider,
                           symbol_directory=directory, profile_loader=Mock(side_effect=AssertionError("No profile")))
        w.resize(1440, 900); w.show()
        self.loader = FakeLoader({"kr": kr_batch(), "us": us_batch()})
        w.markets_view.rankings.loader = self.loader
        w.markets_view.rankings.open_fn = lambda group, now: True
        self.addCleanup(lambda: self.close(w))
        self.settle()
        return w

    def close(self, w):
        from quantgen_desktop.jobs import Jobs
        w.markets_view.stop(); w.home_view.stop(); w.market_hub.stop()
        for jobs in w.findChildren(Jobs):
            self.assertTrue(jobs.pool.waitForDone(6000))
        APP.processEvents()
        delete_owned_widget(w)

    def settle(self, rounds=6):
        for _ in range(rounds):
            APP.processEvents(); QTest.qWait(10)

    def wait(self, predicate, seconds=5):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not predicate():
            APP.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())

    def test_markets_opens_the_root_screen_with_every_category_in_the_rails_order(self):
        w = self.window()
        w.nav["markets"].click(); self.settle()
        hub = w.market_hub
        self.assertEqual(w._route(), "markets")
        self.assertIs(w.markets_content.currentWidget(), hub)
        self.assertIsNone(hub.current_category())
        self.assertFalse(hub.back_button.isVisible())
        self.assertEqual(hub.title.text(), "시장")
        self.assertEqual(tuple(card.category for card in hub.cards), CATEGORY_KEYS)
        self.assertEqual([card.title.text() for card in hub.cards],
                         [node.text for node in shell_rail.market_menu("ko")])
        self.assertTrue(all(card.text.text() for card in hub.cards))
        self.assertEqual(set(CATEGORY_COPY), set(CATEGORY_KEYS))
        self.assertTrue(w.market_submenu.isVisible())       # the categories show under 시장, nothing under them
        self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], [])
        self.assertEqual(self.loader.calls, [])             # automatic loading off: nothing fetched

    def test_each_category_screen_lists_exactly_the_rail_menus_destinations(self):
        w = self.window()
        for node in shell_rail.market_menu("ko"):
            with self.subTest(category=node.key):
                if not node.children:
                    with self.assertRaises(ValueError):
                        w.market_hub.show_category(node.key)
                    continue
                w.open_market_hub(node.key); self.settle()
                hub = w.market_hub
                self.assertEqual(hub.current_category(), node.key)
                self.assertTrue(hub.back_button.isVisible())
                self.assertEqual(hub.title.text(), node.text)
                self.assertEqual([card.leaf for card in hub.cards], [child.leaf for child in node.children])
                self.assertEqual([card.title.text() for card in hub.cards], [child.text for child in node.children])
                for card in hub.cards:
                    self.assertIn(hub._leaf_key(card.leaf), DESTINATION_COPY)
                    self.assertTrue(card.text.text())
                self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], [node.key])

    def test_cards_and_chips_route_like_the_rail(self):
        w = self.window()
        # A destination card on a category screen.
        for node in shell_rail.market_menu("ko"):
            for index, child in enumerate(node.children):
                with self.subTest(leaf=child.leaf):
                    w.open_market_hub(node.key); self.settle()
                    w.market_hub.cards[index].activated.emit(); self.settle()
                    self.assertEqual(w._route(), "markets")
                    page = w.markets_content.currentWidget()
                    self.assertIsNot(page, w.market_hub)
                    if child.leaf[0] == "market":
                        self.assertEqual(w.markets_view.current_market(), child.leaf[1])
                    elif child.leaf[0] == "series":
                        self.assertEqual(page.symbol, child.leaf[2])
                    self.assertEqual([k for k, b in w.market_sections.items() if b.isChecked()], [node.key])
        # A single-destination category card on the root screen opens its destination.
        for key, check in (("crypto", lambda: w.markets_view.current_market() == "crypto"),
                           ("futures", lambda: w.market_asset_category == "futures"),
                           ("corp", lambda: w.market_asset_category == "corp")):
            w.open_market_hub(); self.settle()
            card = next(c for c in w.market_hub.cards if c.category == key)
            self.assertFalse(card.chips.isVisible())
            QTest.mouseClick(card, Qt.MouseButton.LeftButton, pos=QPoint(30, 30)); self.settle()
            self.assertTrue(check(), key)
        # A destination chip on the root card and a ranking chip on the 주식 screen.
        w.open_market_hub(); self.settle()
        indices = next(c for c in w.market_hub.cards if c.category == "indices")
        chips = [b for b in indices.chips.findChildren(QPushButton)]
        self.assertEqual([c.text().replace("&&", "&") for c in chips],
                         [n.text for n in shell_rail.market_menu("ko")[0].children])
        chips[2].click(); self.settle()
        self.assertEqual(w.markets_content.currentWidget().symbol, "^GSPC")
        w.open_market_hub("stocks"); self.settle()
        ranking = [b for b in w.market_hub.cards[1].chips.findChildren(QPushButton)]
        self.assertEqual([b.text() for b in ranking][:4], ["거래대금", "거래량", "급상승", "급하락"])
        ranking[3].click(); self.settle()
        self.assertEqual((w.markets_view.current_market(), w.markets_view.current_category()), ("us", "losers"))
        # Back, from a category screen.
        w.open_market_hub("fx"); self.settle()
        w.market_hub.back_button.click(); self.settle()
        self.assertIs(w.markets_content.currentWidget(), w.market_hub)
        self.assertIsNone(w.market_hub.current_category())

    def test_rail_category_rows_open_their_screen_or_their_single_destination(self):
        w = self.window()
        for key in CATEGORY_KEYS:
            w.navigate("home")
            w.market_sections[key].click(); self.settle()
            node = next(n for n in shell_rail.market_menu("ko") if n.key == key)
            if node.children:
                self.assertIs(w.markets_content.currentWidget(), w.market_hub, key)
                self.assertEqual(w.market_hub.current_category(), key)
            else:
                self.assertIsNot(w.markets_content.currentWidget(), w.market_hub, key)
            self.assertEqual(w.rail_flyouts.panels, [])

    def test_previews_wait_for_the_load_button_with_automatic_loading_off(self):
        w = self.window()
        w.open_market_hub("stocks"); self.settle()
        hub = w.market_hub
        previews = [card.preview for card in hub.cards]
        self.assertTrue(all(p is not None for p in previews))
        self.assertEqual(self.loader.calls, [])
        self.assertTrue(previews[0].load_button.isVisible())
        self.assertFalse(previews[0].columns_host.isVisible())
        previews[0].load_button.click()
        self.wait(lambda: self.loader.calls == ["kr", "us"] and not hub.preview_jobs.busy)
        self.settle()
        board = w.markets_view.rankings
        self.assertEqual(set(board.batches), {"kr", "us"})      # shared with the market page: no second fetch
        heads = [label.text() for label in previews[0].findChildren(type(hub.title)) if label.property("sd") == "hubPreviewHead"]
        self.assertEqual(heads, ["거래대금 상위", "급상승", "급하락"])
        rows = [b for b in previews[0].findChildren(QPushButton) if b.property("sd") == "hubPreviewRow"]
        self.assertTrue(rows)
        names = [r.accessibleName() for r in rows]
        self.assertTrue(any("카카오 +4.20%" == n for n in names))   # the largest rise in the fixture
        w.open_market_section("kr"); self.settle()
        self.assertEqual(self.loader.calls, ["kr", "us"])        # the list opens from the shared batch
        # A preview name opens the stock screen over its market's page.
        w.open_market_hub("stocks"); self.settle()
        opened = []
        w.markets_view.open_instrument = lambda instrument: opened.append(instrument)
        rows = [b for b in w.market_hub.cards[0].preview.findChildren(QPushButton) if b.property("sd") == "hubPreviewRow"]
        rows[0].click(); self.settle()
        self.assertEqual(len(opened), 1)
        self.assertEqual(opened[0].asset, "domestic_stock")
        self.assertEqual(w.markets_view.current_market(), "kr")
        self.assertFalse(self.home_series.called)               # automatic loading off: Home loads nothing either

    def test_previews_load_by_themselves_with_automatic_loading_on(self):
        w = self.window(auto=True)
        w.markets_view.rankings.refresh = lambda **_: False     # only the hub fetches here
        w.open_market_hub("etf"); self.settle()
        self.loader.batches.update(etf_kr=kr_batch(), etf_us=us_batch())
        w.open_market_hub("stocks"); self.settle()
        self.wait(lambda: "kr" in self.loader.calls and "us" in self.loader.calls and not w.market_hub.preview_jobs.busy)

    def test_language_and_theme_switches_rerender_without_fetching(self):
        w = self.window()
        w.open_market_hub("stocks"); self.settle()
        for language, title, first in (("en", "Stocks", "Korea"), ("ko", "주식", "국내")):
            w.set_language(language); self.settle()
            self.assertEqual(w.market_hub.title.text(), title)
            self.assertEqual(w.market_hub.cards[0].title.text(), first)
        for index, palette in ((1, DARK), (0, LIGHT)):
            w.change_theme(index); self.settle()
            self.assertIs(w.market_hub.colors, palette)
            self.assertIn(palette.accent.lower(), w.market_hub.styleSheet().lower())
        self.assertEqual(self.loader.calls, [])

    def test_columns_follow_the_width_and_nothing_scrolls_sideways(self):
        w = self.window()
        w.open_market_hub(); self.settle()
        for width, columns in ((1440, 3), (1000, 2)):
            w.resize(width, 820); self.settle(10)
            self.assertEqual(w.market_hub._columns, columns)
            self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(), 0)
            right = max(card.mapTo(w.market_hub, QPoint(card.width(), 0)).x() for card in w.market_hub.cards)
            self.assertLessEqual(right, w.market_hub.width())

    def test_closing_waits_for_the_hubs_jobs(self):
        w = self.window()
        hub = w.market_hub
        self.assertIn(("hub",), w.market_destinations)
        self.assertFalse(hub.jobs.busy)
        hub.stop()
        self.assertFalse(hub.load_previews(("kr",), manual=True))


if __name__ == "__main__":
    unittest.main()
