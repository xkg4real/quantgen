"""Markets as Toss-style real-time ranked lists (owner request 2026-11-11, point 5; decision UI-D7).

Owner: "시장 UI에는 토스증권처럼 실시간 차트를 다양한 분류기준으로 조회할수있게 변경해봐" and "시장 누르면 하위 UI로
종목 고를수있게" (the rail's sub-menu calls `markets_view.show_category(key)`). The watchlist chart cards moved
to Research Home; Markets keeps the stock search and the one-stock screen.

Offline: the ranking loader is a fake; HTTP and Yahoo attempts fail the test unless a test patches Yahoo
with fixture bars; KIS is a fake service whose paths are checked against the frozen allowlist.
"""
import inspect
import os
import re
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    import config
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.market_rankings import (IDLE_REFRESH_SECONDS, LIVE_REFRESH_SECONDS,
                                                  ProductionRankingLoader, RankingBoard, daily_batch, kis_batch)
    from quantgen_desktop.markets_view import RANKING_CATEGORIES, MarketsWorkspace, WatchlistGrid
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton
from core.i18n import LocaleContext
from core.market import rankings as R
from core.market.directory import SymbolDirectory

NOW = datetime(2026, 11, 11, 5, 20, 0, tzinfo=timezone.utc)  # Wednesday 14:20 KST


def member(code):
    return next(m for m in R.DOMESTIC + R.US if m.code == code)


def kr_batch(fetched_at=NOW):
    rows = (("005930", 102300, 1.5, 1.49e7, 1.52e12, 6.05e14), ("000660", 520000, -2.0, 3.1e6, 1.61e12, 3.8e14),
            ("035720", 40000, 4.2, 2.0e7, 8.0e11, 1.8e13), ("247540", 150000, -6.5, 1.0e6, 1.5e11, 1.5e13),
            ("196170", 400000, 0.0, 2.0e5, 8.0e10, 2.1e13), ("005380", 241500, 0.7, 9.8e5, 2.4e11, 5.0e13))
    records = tuple(R.QuoteRecord(member(c), p, p * x / 100, x, v, tv, cap, "KIS", "kis", fetched_at.isoformat())
                    for c, p, x, v, tv, cap in rows)
    return R.Batch("kr", records, "kis", fetched_at.isoformat(), failures=(("028300", "KISError"),))


def us_batch(fetched_at=NOW):
    rows = (("AAPL", 226.13, 0.8, 4.0e7), ("NVDA", 180.2, -1.1, 2.0e8), ("JPM", 301.5, 2.7, 9.0e6))
    records = tuple(R.QuoteRecord(member(c), p, p * x / 100, x, v, p * v, None, "Yahoo Finance", "daily",
                                  "2026-11-10", estimated_value=True, closes=(p * 0.9, p * 0.95, p))
                    for c, p, x, v in rows)
    return R.Batch("us", records, "daily", fetched_at.isoformat())


class FakeLoader:
    def __init__(self, batches):
        self.batches, self.calls = batches, []

    def __call__(self, group, members, cancelled=None, progress=None):
        self.calls.append(group)
        if progress is not None:
            progress(len(members), len(members))
        answer = self.batches[group]
        if isinstance(answer, Exception):
            raise answer
        return answer


class Clock:
    def __init__(self, now=NOW):
        self.now = now

    def __call__(self):
        return self.now


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.market.routing._yahoo_frame"):
            deny = patch(target, side_effect=AssertionError("Network forbidden"))
            deny.start(); self.addCleanup(deny.stop)

    def wait(self, predicate, seconds=5):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not predicate():
            self.app.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())


class MarketsPageTests(Base):
    def setUp(self):
        super().setUp()
        self.provider = Mock(side_effect=AssertionError("Provider forbidden"))
        self.directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        self.window = ResearchWindow(auto_refresh=False, locale="ko_KR", market_loader=self.provider,
                                     connections_runner=self.provider, symbol_directory=self.directory,
                                     profile_loader=Mock(side_effect=AssertionError("No profile")))
        self.window.resize(1440, 940); self.window.show(); self.window.navigate("markets")
        self.app.processEvents()
        self.addCleanup(self.window.deleteLater); self.addCleanup(self.window.hide)
        self.view = self.window.markets_view
        self.board = self.view.rankings
        self.loader = FakeLoader({"kr": kr_batch(), "us": us_batch()})
        self.board.loader, self.clock = self.loader, Clock()
        self.board.clock = self.clock
        self.board.open_fn = lambda group, now: True

    def load(self):
        self.assertTrue(self.board.refresh(manual=True))
        self.wait(lambda: not self.board.jobs.busy and self.board.group() in self.board.batches)
        self.app.processEvents()

    def shown_rows(self):
        return [row for row in self.board.rows if row.isVisible()]

    def names(self):
        return [row.name.full for row in self.shown_rows()]

    def page_text(self):
        page = self.window.stack.currentWidget().widget()
        return [w.text() for w in [*page.findChildren(QLabel), *page.findChildren(QPushButton)]
                if w.isVisible() and w.text()]

    def test_interface_contract_and_page_structure(self):
        self.assertEqual(RANKING_CATEGORIES, (("value", "Trading value", "거래대금"), ("volume", "Volume", "거래량"),
                                              ("gainers", "Top gainers", "급상승"), ("losers", "Top losers", "급하락"),
                                              ("cap", "Market cap", "시가총액")))
        self.assertTrue(callable(self.view.show_category) and callable(self.view.showing_stock))
        self.assertIsInstance(self.view, MarketsWorkspace)
        self.assertEqual(list(inspect.signature(WatchlistGrid).parameters),
                         ["store", "router_factory", "name_fn", "locale", "auto_load"])
        self.assertEqual(self.window.stack.currentWidget().findChildren(WatchlistGrid), [])  # cards are on Home
        self.assertIs(self.view.pages.currentWidget(), self.board)
        self.assertTrue(self.view.search.isVisible())
        self.assertIs(self.window.current_market_pane(), self.board)  # ResearchWindow keeps working
        self.assertEqual([b.text() for b in self.board.category_buttons.values()],
                         ["거래대금", "거래량", "급상승", "급하락", "시가총액"])
        self.assertEqual([b.text() for b in self.board.market_buttons.values()], ["국내 전체", "코스피", "코스닥", "미국"])
        self.assertEqual(self.board.badge.text(), "자료 없음")
        self.assertIn("아직 불러오지 않았습니다", self.board.empty.text())
        self.assertEqual((self.loader.calls, self.board.tick.isActive()), ([], False))  # automatic refresh off
        self.provider.assert_not_called()

    def test_lists_rank_each_category_from_one_fetch(self):
        self.load()
        self.assertEqual(self.names(), ["SK하이닉스", "삼성전자", "카카오", "현대차", "에코프로비엠", "알테오젠"])
        top = self.shown_rows()[0]
        self.assertEqual((top.rank.text(), top.price.text(), top.change.text(), top.value.text()),
                         ("1", "520,000", "-2.00%", "1.6조"))
        self.assertEqual(top.change.property("tone"), "down")
        self.assertEqual(top.code.full, "000660 · 코스피")
        self.assertEqual(top.mark.symbol, "000660")
        self.assertEqual(self.board.head_value.text(), "거래대금")
        expected = {"volume": ["카카오", "삼성전자", "SK하이닉스", "에코프로비엠", "현대차", "알테오젠"],
                    "gainers": ["카카오", "삼성전자", "현대차"], "losers": ["에코프로비엠", "SK하이닉스"],
                    "cap": ["삼성전자", "SK하이닉스", "현대차", "알테오젠", "카카오", "에코프로비엠"]}
        for key, names in expected.items():
            self.board.category_buttons[key].click(); self.app.processEvents()
            self.assertEqual(self.names(), names, key)
        self.assertEqual(self.board.head_value.text(), "시가총액")
        self.assertEqual(self.shown_rows()[0].value.text(), "605.0조")
        self.board.category_buttons["volume"].click()
        self.assertEqual(self.shown_rows()[0].value.text(), "2,000만주")
        self.board.market_buttons["kosdaq"].click(); self.app.processEvents()
        self.assertEqual(self.names(), ["에코프로비엠", "알테오젠"])
        self.board.set_sector("bio")
        self.assertEqual(self.names(), ["알테오젠"])
        self.assertIn("주요 종목", self.board.footnote.text()); self.assertIn("전체 시장 순위가 아닙니다", self.board.footnote.text())
        self.assertEqual(self.loader.calls, ["kr"])  # categories, markets and sectors re-rank the cached quotes

    def test_source_state_and_refresh_age_are_always_shown(self):
        self.load()
        self.assertEqual(self.board.badge.text(), "KIS 실시간")
        self.assertEqual(self.board.caption.text(), "방금 갱신")
        self.clock.now = NOW + timedelta(seconds=12); self.board._render_status()
        self.assertEqual(self.board.caption.text(), "12초 전 갱신")
        self.clock.now = NOW + timedelta(minutes=3); self.board._render_status()
        self.assertEqual(self.board.caption.text(), "3분 전 갱신")
        self.board.open_fn = lambda group, now: False  # after the close a KIS quote is not live
        self.board.render()
        self.assertEqual(self.board.badge.text(), "KIS · 장 마감")
        self.assertIn("KIS", self.board.badge.toolTip()); self.assertIn("2026-11-11 14:20:00", self.board.badge.toolTip())
        self.board.market_buttons["us"].click(); self.app.processEvents()
        self.assertEqual(self.board.badge.text(), "자료 없음")  # not loaded yet, and nothing loads by itself
        self.assertEqual(self.loader.calls, ["kr"])
        self.load()
        self.assertEqual(self.board.badge.text(), "지연·일별")  # daily bars are never presented as live
        self.assertIn("Yahoo Finance", self.board.badge.toolTip())
        self.assertIn("추정", self.board.footnote.text())
        self.assertEqual(self.names(), ["엔비디아", "애플", "JP모건"])
        self.assertEqual(self.shown_rows()[0].value.text(), "$36.0B")
        self.assertTrue(self.shown_rows()[0].spark.isVisible())  # daily closes give a sparkline cheaply
        self.board.category_buttons["cap"].click(); self.app.processEvents()
        self.assertEqual(self.shown_rows(), [])
        self.assertIn("시가총액은 KIS", self.board.empty.text())
        shown = " ".join(self.page_text())
        self.assertNotIn("Yahoo", shown)
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown), shown)  # dates stay in tooltips

    def test_failures_and_empty_answers_say_so(self):
        self.board.loader = FakeLoader({"kr": RuntimeError("raw provider text"), "us": R.Batch("us", (), "none", NOW.isoformat())})
        self.assertTrue(self.board.refresh(manual=True))
        self.wait(lambda: not self.board.jobs.busy)
        self.app.processEvents()
        self.assertEqual(self.board.badge.text(), "자료 없음")
        self.assertEqual(self.board.caption.text(), "조회 실패 (RuntimeError)")
        self.assertIn("불러오지 못했습니다", self.board.empty.text())
        self.assertNotIn("raw provider", " ".join(self.page_text()))
        self.assertFalse(self.board.due())  # retried after RETRY_SECONDS, not on every tick
        self.clock.now = NOW + timedelta(seconds=61)
        self.assertTrue(self.board.due())
        self.board.market_buttons["us"].click(); self.load()
        self.assertEqual(self.board.badge.text(), "자료 없음")
        self.board.loader = FakeLoader({"kr": kr_batch()})
        self.board.market_buttons["kr"].click(); self.load()
        self.assertIn("1개 종목은 불러오지 못했습니다", self.board.footnote.text())  # HLB failed in the fixture
        self.board.loader = FakeLoader({"kr": RuntimeError("late")})
        self.clock.now = NOW + timedelta(minutes=2)
        self.assertTrue(self.board.refresh(manual=True)); self.wait(lambda: not self.board.jobs.busy)
        self.app.processEvents()
        self.assertTrue(self.shown_rows())  # a failed refresh keeps the last list and says how old it is
        self.assertEqual(self.board.caption.text(), "조회 실패 (RuntimeError) · 2분 전 갱신")
        self.assertEqual(self.board.badge.text(), "KIS 실시간")
        self.clock.now = NOW + timedelta(minutes=5); self.board._render_status()
        self.assertEqual(self.board.badge.text(), "KIS · 갱신 지연")  # an old KIS list is not called real-time

    def test_rail_sub_menu_and_a_row_open_the_stock_screen(self):
        self.load()
        row = self.shown_rows()[0]
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.app.processEvents()
        self.assertTrue(self.view.showing_stock())
        self.assertEqual(self.view.stock.instrument, member("000660").instrument)
        self.assertEqual(self.view.stock.name.text(), "SK하이닉스")
        self.assertIs(self.window.current_market_pane(), self.window.market_chart)
        self.assertIsNone(self.window.market_chart.snapshot)  # opening never loads with automatic refresh off
        self.view.open_instrument(member("035720").instrument)
        self.assertEqual(self.view.stock.name.text(), "카카오")  # curated names when the directory has none
        for key, _en, ko in RANKING_CATEGORIES:
            self.window.navigate("markets")
            self.assertTrue(self.view.show_category(key)); self.app.processEvents()
            self.assertFalse(self.view.showing_stock())
            self.assertTrue(self.board.category_buttons[key].isChecked() and self.board.isVisible())
            self.assertEqual(self.board.category_buttons[key].text(), ko)
        self.view.open_instrument(member("005930").instrument)
        self.window.activateWindow(); self.app.processEvents()
        self.assertTrue(self.view.show_category("search")); self.app.processEvents()
        self.assertTrue(self.view.search.hasFocus())
        self.assertTrue(self.view.showing_stock())  # the search keeps the page that is shown
        self.view.stock.back_button.click(); self.app.processEvents()
        self.assertFalse(self.view.showing_stock())
        self.assertEqual(self.view.stock.back_button.text(), "← 실시간 차트")
        with self.assertRaises(ValueError):
            self.view.show_category("popular")
        self.board.rows[0].setFocus()
        QTest.keyClick(self.board.rows[0], Qt.Key.Key_Return); self.app.processEvents()
        self.assertTrue(self.view.showing_stock())
        self.assertEqual(self.loader.calls, ["kr"])

    def test_language_and_theme_switch_without_refetching(self):
        from core.theme import DARK
        self.load()
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.names()[:2], ["SK hynix", "Samsung Electronics"])
        self.assertEqual(self.shown_rows()[0].value.text(), "₩1.6T")
        self.assertEqual(self.shown_rows()[0].code.full, "000660 · KOSPI")
        self.assertEqual(self.board.badge.text(), "KIS real-time")
        self.assertEqual(self.board.caption.text(), "Updated just now")
        hangul = [t for t in self.page_text() if re.search("[가-힣]", t)]
        self.assertEqual(hangul, [])
        self.assertEqual([self.board.sector_box.itemText(i) for i in range(2)], ["All sectors", "Semiconductors"])
        self.window.theme.setCurrentIndex(1); self.app.processEvents()
        self.assertIn(DARK.accent_soft, self.board.styleSheet())
        self.assertEqual(self.shown_rows()[0].mark.colors, DARK)
        self.window.set_language("ko"); self.app.processEvents()
        self.assertEqual(self.names()[0], "SK하이닉스")
        self.assertEqual(self.loader.calls, ["kr"])


class AutomaticRefreshTests(Base):
    def test_polls_only_while_visible_and_on_the_cadence_of_its_source(self):
        clock = Clock()
        loader = FakeLoader({"kr": kr_batch(), "us": us_batch()})
        board = RankingBoard(loader=loader, locale=LocaleContext("ko_KR"), auto_load=True, clock=clock,
                             open_fn=lambda group, now: True)
        self.addCleanup(board.deleteLater)
        self.assertEqual(loader.calls, [])  # nothing on construction
        board.resize(1100, 900); board.show()
        self.wait(lambda: loader.calls == ["kr"] and not board.jobs.busy and "kr" in board.batches)
        self.assertTrue(board.tick.isActive())
        clock.now = NOW + timedelta(seconds=LIVE_REFRESH_SECONDS - 1); board._tick(); self.app.processEvents()
        self.assertEqual(loader.calls, ["kr"])
        clock.now = NOW + timedelta(seconds=LIVE_REFRESH_SECONDS); board._tick()
        self.wait(lambda: loader.calls == ["kr", "kr"] and not board.jobs.busy)
        board.set_market("us")
        self.wait(lambda: loader.calls == ["kr", "kr", "us"] and not board.jobs.busy)  # a new group loads at once
        board.batches["us"] = us_batch(NOW)
        clock.now = NOW + timedelta(seconds=IDLE_REFRESH_SECONDS - 1)
        self.assertFalse(board.due())  # delayed daily bars refresh on the slow cadence
        board.batches["kr"] = kr_batch(NOW)
        board.open_fn = lambda group, now: False
        self.assertFalse(board.due("kr"))  # KIS after the close too
        board.hide(); self.app.processEvents()
        self.assertFalse(board.tick.isActive())
        clock.now = NOW + timedelta(hours=2); board._tick(); self.app.processEvents()
        self.assertEqual(loader.calls, ["kr", "kr", "us"])  # hidden: nothing loads

    def test_progress_is_shown_and_stop_drops_a_late_answer(self):
        gate, started = threading.Event(), threading.Event()

        def slow(group, members, cancelled=None, progress=None):
            progress(3, len(members)); started.set()
            gate.wait(5)
            return kr_batch()
        board = RankingBoard(loader=slow, locale=LocaleContext("ko_KR"), auto_load=False, clock=Clock(),
                             open_fn=lambda group, now: True)
        self.addCleanup(board.deleteLater)
        board.show()
        self.assertTrue(board.refresh(manual=True))
        self.wait(lambda: started.is_set() and "3/" in board.caption.text())
        self.assertEqual(board.caption.text(), f"불러오는 중… 3/{len(R.DOMESTIC)}")
        self.assertFalse(board.refresh(manual=True))  # one fetch at a time
        board.stop(); gate.set()
        self.wait(lambda: not board.jobs.busy)
        self.app.processEvents()
        self.assertEqual(board.batches, {})


class FakeService:
    def __init__(self, ready=True, fail=()):
        self.ready, self.fail, self.calls = ready, set(fail), []

    def _get(self, path, tr_id, params):
        config_paths = config.KIS_QUOTATION_ALLOWLIST
        assert path in config_paths, path
        self.calls.append((path, tr_id, dict(params)))
        code = params.get("FID_INPUT_ISCD") or params.get("SYMB")
        if code in self.fail or "*" in self.fail:
            raise RuntimeError("KIS said no")
        if tr_id == "FHKST01010100":
            return {"output": {"stck_prpr": "70000", "prdy_vrss": "700", "prdy_vrss_sign": "2", "prdy_ctrt": "1.01",
                               "acml_vol": "1000", "acml_tr_pbmn": "70000000", "hts_avls": "4200"}}
        return {"output": {"last": "100.5", "diff": "0.5", "sign": "2", "rate": "0.50", "tvol": "10", "tamt": "1005"}}


class LoaderTests(Base):
    def test_kis_quotes_through_allowlisted_paths_at_a_bounded_rate(self):
        members = R.DOMESTIC[:4] + R.US[:2]
        service, sleeps, ticks = FakeService(fail={members[1].code}), [], iter(range(100))
        batch = kis_batch(service, "kr", members, sleep=sleeps.append, clock=lambda: next(ticks) * 0.01,
                          per_second=20)
        self.assertEqual([c[1] for c in service.calls], ["FHKST01010100"] * 4 + ["HHDFS00000300"] * 2)
        self.assertEqual(service.calls[-2][2], {"AUTH": "", "EXCD": "NAS", "SYMB": "AAPL"})
        self.assertEqual(len(sleeps), 5); self.assertTrue(all(abs(s - 0.04) < 1e-9 for s in sleeps))  # 20/s
        self.assertEqual((batch.mode, len(batch.records), batch.failures), ("kis", 5, ((members[1].code, "RuntimeError"),)))
        first = batch.records[0]
        self.assertEqual((first.trading_value, first.market_cap, first.change_pct), (7e7, 4.2e11, 1.01))
        stop = kis_batch(service, "kr", members, cancelled=lambda: True, sleep=sleeps.append)
        self.assertEqual(stop.records, ())

    def test_daily_path_when_kis_is_not_configured_or_answers_nothing(self):
        bars = {"005930.KS": [("2026-11-07", 1, 1, 1, 100.0, 10.0), ("2026-11-10", 1, 1, 1, 101.0, 20.0)],
                "247540.KQ": [("2026-11-07", 1, 1, 1, 50.0, 5.0), ("2026-11-10", 1, 1, 1, 49.0, 6.0)],
                "035720.KQ": [("2026-11-07", 1, 1, 1, 40.0, 1.0), ("2026-11-10", 1, 1, 1, 41.0, 2.0)],  # moved market
                "AAPL": [("2026-11-07", 1, 1, 1, 200.0, 1.0), ("2026-11-10", 1, 1, 1, 210.0, 3.0)]}
        asked = []

        def frame(symbol, interval, period):
            asked.append(symbol)
            self.assertEqual((interval, period), ("1d", "1mo"))
            return bars.get(symbol, [])
        members = (member("005930"), member("247540"), member("035720"), member("000660"), member("AAPL"))
        with patch("core.market.routing._yahoo_frame", side_effect=frame):
            factory = Mock(return_value=FakeService(ready=False))
            loader = ProductionRankingLoader(service_factory=factory)
            factory.assert_not_called()  # nothing is constructed before the first fetch
            batch = loader("kr", members)
            self.assertEqual(batch.mode, "daily")
            got = {r.member.code: r for r in batch.records}
            self.assertEqual(set(got), {"005930", "247540", "035720", "AAPL"})
            self.assertEqual(batch.failures, (("000660", "LookupError"),))
            self.assertEqual(got["035720"].market, "KOSDAQ")  # answered under .KQ: listed on KOSDAQ now
            self.assertEqual(got["005930"].trading_value, 101.0 * 20.0)
            self.assertTrue(got["005930"].estimated_value)
            self.assertIn("005930.KS", asked)
            self.assertNotIn("247540.KS", asked)  # the curated market's suffix answers first
            down = ProductionRankingLoader(service_factory=lambda: FakeService(ready=True, fail={"*"}))
            fallback = down("kr", members[:2])
            self.assertEqual((fallback.mode, fallback.fallback, len(fallback.records)), ("daily", True, 2))
            live = ProductionRankingLoader(service_factory=lambda: FakeService(ready=True))("kr", members[:2])
            self.assertEqual((live.mode, live.fallback), ("kis", False))
        self.assertEqual(daily_batch("kr", members[:1], fetch=lambda s: [], workers=2).mode, "none")

    def test_window_constructs_no_kis_service_and_fetches_nothing_with_refresh_off(self):
        window = ResearchWindow(auto_refresh=False, locale="en_US",
                                market_loader=Mock(side_effect=AssertionError("Provider forbidden")))
        self.addCleanup(window.deleteLater)
        window.show(); window.navigate("markets")
        for key, _en, _ko in RANKING_CATEGORIES:
            window.markets_view.show_category(key)
        window.markets_view.rankings.set_market("us")
        self.app.processEvents()
        loader = window.markets_view.rankings.loader
        self.assertIsInstance(loader, ProductionRankingLoader)
        self.assertIsNone(loader._service)  # its KIS service is built on the first fetch only
        self.assertEqual(window.markets_view.rankings.batches, {})
        self.assertFalse(window.markets_view.rankings.jobs.busy)
        window.hide()


if __name__ == "__main__":
    unittest.main()
