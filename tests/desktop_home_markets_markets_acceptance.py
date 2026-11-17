"""Markets as one page per market with Toss-style ranked lists (owner 2026-11-11, point 5; UI-D7; UI-D10).

Owner: "시장 UI에는 토스증권처럼 실시간 차트를 다양한 분류기준으로 조회할수있게 변경해봐" and "시장 누르면 하위 UI로
종목 고를수있게". Owner ruling UI-D10: "시장에서 그냥 국장 미장 코인 이런걸 하부ui로 두고, 너가 지금 하부ui로 깔아놓은건
해당 시장의 하부ui 선택하고 차후에 검색기준으로 저걸 쓸수있게 구현하면 좋을 거 같은데, 공간 잘써서 센스있게해봐": the rail
calls `markets_view.show_market(key)` (국내 주식 / 미국 주식 / 코인); inside a market's page the categories rank the
list and, with the header search, the sub-market, the sector and the 조건 row, narrow it (`core.market.screen`).
Tests that pinned the UI-D7 page (title "실시간 차트", the 국내 전체·코스피·코스닥·미국 buttons) were updated: the
sub-market is a filter inside a market page and the market is chosen in the rail. The watchlist chart cards moved
to Research Home; Markets keeps the one-stock screen.

Owner ruling UI-D11 (2026-11-12, "코인이 뭐야 ETF라해야지"; the page itself unchanged): the coin page is 크립토 and its
prose says 가상자산 (the tests that pinned "코인" now pin those words), the rail's 시장 rows are the big categories
(주식 is highlighted for both stock pages; `open_market_section(page)` replaces clicking the old per-market items),
and two ETF pages (국내 ETF, 미국 ETF) reuse the page (`MarketPageTests.test_etf_pages...`).

Offline: the ranking loader is a fake; HTTP and Yahoo attempts fail the test unless a test patches Yahoo
with fixture bars; KIS is a fake service whose paths are checked against the frozen allowlist; the index strip's
production loader is patched to fail the test, and strips that load are given fixture series.
"""
import inspect
import os
import re
import threading
import time
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    import config
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.market_rankings import (IDLE_REFRESH_SECONDS, LIVE_REFRESH_SECONDS,
                                                  ProductionRankingLoader, RankingBoard, board_stylesheet,
                                                  daily_batch, kis_batch)
    from quantgen_desktop.markets_view import MARKET_PAGES, RANKING_CATEGORIES, MarketsWorkspace, WatchlistGrid
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QPushButton, QWidget
from core.i18n import LocaleContext
from core.market import rankings as R
from core.market.directory import SymbolDirectory
from tests.qt_fixture_cleanup import delete_owned_widget

NOW = datetime(2026, 11, 11, 5, 20, 0, tzinfo=timezone.utc)  # Wednesday 14:20 KST


def member(code):
    return next(m for m in R.DOMESTIC + R.US if m.code == code)


def kr_batch(fetched_at=NOW):
    """Domestic KIS quotes as `parse_kis_domestic` leaves them: KIS's market cap, checked against listed shares x
    price of the same answer (basis 'provider')."""
    rows = (("005930", 102300, 1.5, 1.49e7, 1.52e12, 6.05e14), ("000660", 520000, -2.0, 3.1e6, 1.61e12, 3.8e14),
            ("035720", 40000, 4.2, 2.0e7, 8.0e11, 1.8e13), ("247540", 150000, -6.5, 1.0e6, 1.5e11, 1.5e13),
            ("196170", 400000, 0.0, 2.0e5, 8.0e10, 2.1e13), ("005380", 241500, 0.7, 9.8e5, 2.4e11, 5.0e13))
    at = fetched_at.isoformat()
    records = tuple(R.with_cap(R.QuoteRecord(member(c), p, p * x / 100, x, v, tv, None, "KIS", "kis", at), cap,
                               basis="provider", source="KIS", as_of=at, shares=float(round(cap / p)))
                    for c, p, x, v, tv, cap in rows)
    return R.Batch("kr", records, "kis", at, failures=(("028300", "KISError"),))


def accent_pixels(widget, colour):
    """How many pixels of `widget` as rendered are (nearly) `colour`."""
    from PyQt6.QtGui import QColor
    image, target = widget.grab().toImage(), QColor(colour)
    near = lambda c: max(abs(c.red() - target.red()), abs(c.green() - target.green()), abs(c.blue() - target.blue())) < 8
    return sum(1 for x in range(image.width()) for y in range(image.height()) if near(image.pixelColor(x, y)))


def kis_domestic(code, price, **fields):
    """A domestic record parsed from a KIS inquire-price answer (`hts_avls`, `lstn_stcn` as given)."""
    out = {"stck_prpr": str(price), "prdy_vrss": "0", "prdy_vrss_sign": "3", "prdy_ctrt": "0.00", "acml_vol": "1000",
           "acml_tr_pbmn": "1000000", **fields}
    return R.parse_kis_domestic(member(code), out, received_at=NOW.isoformat())


def every_domestic(fetched_at=NOW):
    """Every domestic member with a KIS quote: a list that runs past the fold of the smallest window."""
    at = fetched_at.isoformat()
    return R.Batch("kr", tuple(R.QuoteRecord(m, 10000.0 + i, 10.0, 0.1 + i / 100, 1e5 + i, 1e10 - i * 1e7, None, "KIS",
                                             "kis", at) for i, m in enumerate(R.DOMESTIC)), "kis", at)


def us_batch(fetched_at=NOW):
    rows = (("AAPL", 226.13, 0.8, 4.0e7), ("NVDA", 180.2, -1.1, 2.0e8), ("JPM", 301.5, 2.7, 9.0e6))
    records = tuple(R.QuoteRecord(member(c), p, p * x / 100, x, v, p * v, None, "Yahoo Finance", "daily",
                                  "2026-11-10", estimated_value=True, closes=(p * 0.9, p * 0.95, p))
                    for c, p, x, v in rows)
    return R.Batch("us", records, "daily", fetched_at.isoformat())


def us_cap_batch(fetched_at=NOW):
    """US market cap as the loader leaves it: NVIDIA stated by KIS (price-detail), Apple computed from Yahoo
    shares x its price, JPMorgan's share count unreadable."""
    base = us_batch(fetched_at)
    got = {r.member.code: r for r in base.records}
    records = (R.computed_cap(got["AAPL"], 1.484e10, source="Yahoo Finance", as_of="2026-10-17"),
               R.with_cap(got["NVDA"], 4.4e12, basis="provider", source="KIS", as_of="2026-11-11T05:19:00+00:00"),
               R.without_cap(got["JPM"], "no_shares"))
    return replace(base, records=records, caps="ok", cap_reasons=("fmp_plan",))


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
        # The index strip's production series (yfinance does not go through requests): never in a test.
        series = patch("quantgen_desktop.market_summary.production_series",
                       side_effect=AssertionError("Index series forbidden"))
        self.production_series = series.start(); self.addCleanup(series.stop)
        yf = patch("core.ficc.data._yf", None)
        yf.start(); self.addCleanup(yf.stop)

    def wait(self, predicate, seconds=5):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not predicate():
            self.app.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())


class WindowBase(Base):
    """A Korean window on Markets with a fake ranking loader; nothing loads by itself."""

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


class MarketsPageTests(WindowBase):
    def test_interface_contract_and_page_structure(self):
        self.assertEqual(RANKING_CATEGORIES, (("value", "Trading value", "거래대금"), ("volume", "Volume", "거래량"),
                                              ("gainers", "Top gainers", "급상승"), ("losers", "Top losers", "급하락"),
                                              ("cap", "Market cap", "시가총액"), ("qscore", "Q-SCORE highest first", "Q-SCORE 높은 순")))
        self.assertEqual(MARKET_PAGES, (("kr", "Korean stocks", "국내 주식"), ("us", "US stocks", "미국 주식"),
                                        ("crypto", "Crypto", "크립토"), ("etf_kr", "Korean ETFs", "국내 ETF"),
                                        ("etf_us", "US ETFs", "미국 ETF")))
        self.assertTrue(callable(self.view.show_market) and callable(self.view.show_category)
                        and callable(self.view.showing_stock))
        self.assertIsInstance(self.view, MarketsWorkspace)
        self.assertEqual(list(inspect.signature(WatchlistGrid).parameters),
                         ["store", "router_factory", "name_fn", "locale", "auto_load"])
        self.assertEqual(self.window.stack.currentWidget().findChildren(WatchlistGrid), [])  # cards are on Home
        self.assertIs(self.view.pages.currentWidget(), self.board)
        self.assertTrue(self.view.search.isVisible())
        self.assertIs(self.window.current_market_pane(), self.board)  # ResearchWindow keeps working
        # UI-D10: no page title, description paragraph or separate search card; the header names the market.
        page = self.window.stack.currentWidget().widget()
        self.assertEqual([w.text() for w in page.findChildren(QLabel)
                          if w.isVisible() and w.property("role") in ("title", "muted")], [])
        shown = self.page_text()
        self.assertNotIn("시장", shown); self.assertNotIn("실시간 차트", shown)
        self.assertFalse([w for w in page.findChildren(QComboBox) if w.isVisible() and w.findData("bond") >= 0])
        self.assertEqual(self.board.heading.text(), "국내 주식")
        self.assertEqual([b.text() for b in self.board.category_buttons.values()],
                         ["거래대금", "거래량", "급상승", "급하락", "시가총액", "Q-SCORE 높은 순"])
        self.assertEqual([b.text() for b in self.board.sub_buttons.values()], ["전체", "코스피", "코스닥"])
        self.assertFalse(self.board.summary_section.isVisible())  # nothing loaded, nothing loads: no empty strip
        self.assertFalse(self.board.conditions_section.isVisible())
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
        self.board.sub_buttons["kosdaq"].click(); self.app.processEvents()
        self.assertEqual(self.names(), ["에코프로비엠", "알테오젠"])
        self.board.set_sector("bio")
        self.assertEqual(self.names(), ["알테오젠"])
        self.assertIn("주요 종목", self.board.footnote.text()); self.assertIn("전체 시장 순위가 아닙니다", self.board.footnote.text())
        self.assertEqual(self.loader.calls, ["kr"])  # categories, markets and sectors re-rank the cached quotes

    def test_source_state_and_refresh_age_are_always_shown(self):
        self.load()
        self.assertEqual(self.board.badge.text(), "KIS 조회 · 45초마다")  # REST polling, never "실시간"
        self.assertEqual(self.board.heading.text(), "국내 주식")  # UI-D10: the market's name heads its page
        self.assertIn("45초마다 조회(REST 요청이며 체결 수신이 아닙니다)", self.board.badge.toolTip())
        self.assertEqual(self.board.caption.text(), "방금 갱신")
        self.clock.now = NOW + timedelta(seconds=12); self.board._render_status()
        self.assertEqual(self.board.caption.text(), "12초 전 갱신")
        self.clock.now = NOW + timedelta(minutes=3); self.board._render_status()
        self.assertEqual(self.board.caption.text(), "3분 전 갱신")
        self.board.open_fn = lambda group, now: False  # after the close a KIS quote is not live
        self.board.render()
        self.assertEqual(self.board.badge.text(), "KIS · 장 마감")
        self.assertIn("KIS", self.board.badge.toolTip()); self.assertIn("2026-11-11 14:20:00", self.board.badge.toolTip())
        self.view.show_market("us"); self.app.processEvents()
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
        self.assertEqual(self.shown_rows(), [])  # this fixture loader sought no market cap, and says so
        self.assertEqual(self.board.empty.text(), "이 시세에는 시가총액이 없습니다.")
        shown = " ".join(self.page_text())
        self.assertNotIn("Yahoo", shown)
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown), shown)  # dates stay in tooltips

    def test_us_market_cap_ranks_the_figures_found_and_says_where_they_came_from(self):
        # Owner 2026-11-11: "아니 미국 시총 자료 찾으세요". The explanation gives way to the list.
        self.board.loader = FakeLoader({"kr": kr_batch(), "us": us_cap_batch()})
        self.view.show_market("us"); self.board.category_buttons["cap"].click(); self.load()
        rows = self.shown_rows()
        self.assertEqual(self.names(), ["엔비디아", "애플", "JP모건"])
        self.assertEqual([(r.rank.text(), r.value.text()) for r in rows], [("1", "$4.4T"), ("2", "$3.4T"), ("", "—")])
        self.assertFalse(self.board.empty.isVisible())
        self.assertEqual(self.board.head_value.text(), "시가총액(계산값)")
        self.assertEqual(rows[1].value.toolTip(), "상장주식수 148.4억주 (Yahoo Finance, 2026-10-17) × 가격 $226.13 = $3.4T")
        self.assertEqual(rows[0].value.toolTip(), "KIS 제공 시가총액 · 2026-11-11 14:19 (한국 시간) 기준")
        self.assertEqual(rows[2].value.toolTip(), "상장주식수를 읽지 못했습니다.")
        self.assertIn("Yahoo Finance", self.board.head_value.toolTip())
        self.assertIn("시가총액(계산값) = 상장주식수 × 표시 가격", self.board.footnote.text())
        self.assertIn("1개 종목은 시가총액을 읽지 못해 순위 없이 맨 아래에 둡니다.", self.board.footnote.text())
        shown = " ".join(self.page_text())
        self.assertNotIn("Yahoo", shown); self.assertNotIn("FMP", shown)  # providers and dates in tooltips only
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown), shown)
        self.board.set_sector("bio")  # no US bio stock in the fixture: nothing ranked, so no '—' rows either
        self.assertEqual((self.shown_rows(), self.board.empty.text()), ([], "이 목록에는 시가총액을 읽은 종목이 없습니다."))
        self.board.set_sector("")
        self.window.set_language("en"); self.app.processEvents()
        rows = self.shown_rows()
        self.assertEqual(self.board.head_value.text(), "Market cap (computed)")
        self.assertEqual([r.value.text() for r in rows], ["$4.4T", "$3.4T", "—"])
        self.assertEqual(rows[1].value.toolTip(), "Shares outstanding 14.8B (Yahoo Finance, 2026-10-17) × price $226.13 = $3.4T.")
        self.assertEqual(rows[0].value.toolTip(), "KIS market cap, stated 2026-11-11 14:19 KST.")
        self.assertIn("No market cap for 1 of these stocks", self.board.footnote.text())
        self.assertEqual([t for t in self.page_text() if re.search("[가-힣]", t)], [])
        self.board.category_buttons["value"].click(); self.app.processEvents()
        self.assertEqual(self.board.head_value.text(), "Trading value")
        self.assertEqual(len(self.shown_rows()), 3)
        self.assertNotIn("market cap", self.board.footnote.text().lower())
        self.window.set_language("ko"); self.app.processEvents()
        # Domestic: KIS's figure, checked against listed shares x price of the same answer (the tooltip says so).
        self.view.show_market("kr"); self.board.category_buttons["cap"].click(); self.load()
        self.assertEqual(self.board.head_value.text(), "시가총액")
        self.assertEqual(self.shown_rows()[0].value.toolTip(),
                         "KIS 제공 시가총액(hts_avls를 1억 원 단위로 읽음) · 2026-11-11 14:20 (한국 시간) 기준 · "
                         "같은 KIS 응답의 상장주식수 59.1억주 × 현재가 102,300 = 605.0조와 25% 안에서 맞음")
        no_cap = kr_batch()
        self.board.batches["kr"] = replace(no_cap, records=tuple(replace(r, market_cap=None) for r in no_cap.records))
        self.board.render()
        self.assertEqual(self.shown_rows(), [])
        self.assertIn("시가총액은 KIS", self.board.empty.text())  # the domestic explanation stays
        self.assertEqual(self.board.loader.calls, ["us", "kr"])

    def test_us_kis_quotes_are_the_free_feed_polled_never_live(self):
        # 2026-11-11 compliance follow-up: the stock detail view calls KIS US quotes "무료 시세"; so does the list.
        base = us_batch()
        polled = replace(base, mode="kis", records=tuple(replace(r, mode="kis", source="KIS", as_of=NOW.isoformat())
                                                         for r in base.records))
        self.board.batches["us"] = polled
        self.view.show_market("us"); self.app.processEvents()
        # UI-D10 review: the domestic state's word order ("KIS 조회 · 45초마다"); "조회" stays in the tooltip.
        self.assertEqual(self.board.badge.text(), "KIS 무료 시세 · 45초마다")
        self.assertEqual(self.board.badge.property("state"), "polled_us")
        tip = self.board.badge.toolTip()
        self.assertIn("KIS 현재가 · 45초마다 조회(REST 요청이며 체결 수신이 아닙니다)", tip)
        self.assertIn("미국 시세는 KIS 무료 시세이며 유료 통합 시세와 다를 수 있습니다.", tip)
        self.board.open_fn = lambda group, now: False
        self.board.render()
        self.assertEqual(self.board.badge.text(), "KIS · 장 마감")
        self.assertIn("300초마다 조회", self.board.badge.toolTip())  # outside the session: the slow cadence
        self.window.set_language("en"); self.app.processEvents()
        self.board.open_fn = lambda group, now: True
        self.board.render()
        self.assertEqual(self.board.badge.text(), "KIS free feed · polled every 45 s")
        self.assertIn("polled every 45 s (REST requests, not a trade stream)", self.board.badge.toolTip())
        self.assertIn("can differ from paid consolidated quotes", self.board.badge.toolTip())
        for state in ("polled", "polled_us", "closed", "stale", "daily", "none"):
            self.assertNotIn("실시간", R.text(R.STATES, state, "ko"))
            self.assertNotIn("real-time", R.text(R.STATES, state, "en").lower())

    def test_market_buttons_show_the_windows_focus_ring_without_changing_their_look(self):
        # 2026-11-11 compliance follow-up (14-contrast, 15-keyboard): the list's own [tool='true'] rule set
        # `border` with no :focus rule, and the closer sheet hid the window's 2px focus ring. UI-D10: these are
        # the sub-market buttons of each market page now.
        from core.theme import DARK, LIGHT
        for colors, dark in ((LIGHT, False), (DARK, True)):
            rule = re.search(r"QPushButton\[tool='true'\]:focus \{([^}]*)\}", board_stylesheet(colors, dark))
            self.assertIsNotNone(rule)
            self.assertIn(f"border: 2px solid {colors.accent}", rule.group(1))
        self.window.activateWindow(); self.app.processEvents()
        for theme in (0, 1):
            self.window.theme.setCurrentIndex(theme); self.app.processEvents()
            accent = (DARK if theme else LIGHT).accent
            for page, key in (("kr", ""), ("kr", "kospi"), ("kr", "kosdaq"), ("us", ""), ("us", "NAS"), ("us", "NYS")):
                self.board.set_page(page); self.app.processEvents()
                button = self.board.sub_buttons[key]
                self.board.category_buttons["value"].setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
                plain, size = accent_pixels(button, accent), button.size()
                if not button.isChecked():
                    self.assertEqual(plain, 0, key)  # unfocused: no ring (the checked one keeps its underline)
                button.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
                self.assertTrue(button.hasFocus(), key)
                self.assertGreater(accent_pixels(button, accent), plain + 2 * (size.width() + size.height()), key)
                self.assertEqual(button.size(), size, key)  # the ring does not resize or move the button
        self.window.theme.setCurrentIndex(0); self.app.processEvents()

    def test_chips_and_market_buttons_are_radio_groups_for_the_keyboard(self):
        # Reviewer 2026-11-11 (15-keyboard): both rows are exclusive QButtonGroups, so Tab stops only at the
        # selected chip and the selected market button, and the arrow keys move focus and select; an unselected
        # chip never gets keyboard focus (the docs say so instead of calling them ordinary Tab stops). UI-D10: the
        # market buttons are the page's sub-market filter (전체·코스피·코스닥); the 조건 toggle follows the sector.
        self.window.activateWindow(); self.app.processEvents()
        chips, markets = self.board.category_buttons, self.board.sub_buttons

        def tab_from(widget, count=3):
            widget.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
            seen = []
            for _ in range(count):
                QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Tab); self.app.processEvents()
                seen.append(self.app.focusWidget())
            return seen
        self.assertEqual(tab_from(self.board.refresh_button, 4),
                         [chips["value"], markets[""], self.board.sector_box, self.board.conditions_button])
        self.assertEqual(tab_from(self.board.search, 1), [self.board.refresh_button])
        self.assertEqual(tab_from(self.board.refresh_button, 1), [chips["value"]])
        QTest.keyClick(chips["value"], Qt.Key.Key_Right); self.app.processEvents()
        self.assertEqual((self.board.category, self.app.focusWidget()), ("volume", chips["volume"]))
        self.assertTrue(chips["volume"].isChecked())
        self.assertEqual(tab_from(chips["volume"], 1), [markets[""]])
        QTest.keyClick(markets[""], Qt.Key.Key_Right); self.app.processEvents()
        self.assertEqual((self.board.market, self.app.focusWidget()), ("kospi", markets["kospi"]))
        self.assertEqual(tab_from(self.board.refresh_button),
                         [chips["volume"], markets["kospi"], self.board.sector_box])
        self.assertEqual(self.loader.calls, [])  # moving within the domestic group fetches nothing

    def test_domestic_market_cap_is_used_only_when_it_agrees_and_says_its_basis(self):
        # 2026-11-11 compliance follow-up (12-claims 2026-11-02: hts_avls unit unverified): as the US path checks
        # KIS tomv, hts_avls x 1e8 is used only within 25% of listed shares x price of the same answer.
        records = (kis_domestic("005930", 102300, hts_avls="6050000", lstn_stcn="5969782550"),  # agrees
                   kis_domestic("000660", 520000, hts_avls="", lstn_stcn="728002365"),        # computed
                   kis_domestic("035720", 40000, hts_avls="17", lstn_stcn="442000000"),       # refused
                   kis_domestic("005380", 241500, hts_avls="505000"))                         # no share count
        self.board.loader = FakeLoader({"kr": R.Batch("kr", records, "kis", NOW.isoformat())})
        self.board.category_buttons["cap"].click(); self.load()
        rows = self.shown_rows()
        self.assertEqual([(r.rank.text(), r.name.full, r.value.text()) for r in rows],
                         [("1", "삼성전자", "605.0조"), ("2", "SK하이닉스", "378.6조"), ("", "카카오", "—"),
                          ("", "현대차", "—")])
        self.assertEqual(self.board.head_value.text(), "시가총액(계산값)")
        self.assertIn("같은 KIS 응답의 상장주식수 59.7억주 × 현재가 102,300 = 610.7조와 25% 안에서 맞음",
                      rows[0].value.toolTip())
        self.assertEqual(rows[1].value.toolTip(), "상장주식수 7.3억주 (KIS, 2026-11-11) × 가격 520,000 = 378.6조")
        self.assertEqual(rows[2].value.toolTip(), "KIS 시가총액이 같은 응답의 상장주식수 × 현재가와 25% 넘게 달라 쓰지 않습니다.")
        self.assertEqual(rows[3].value.toolTip(), "KIS 응답에 상장주식수가 없어 시가총액을 확인할 수 없으므로 쓰지 않습니다.")
        self.assertIn("1억 원 단위", self.board.head_value.toolTip())
        self.assertIn("계산값: 같은 KIS 응답의 상장주식수 × 현재가", self.board.head_value.toolTip())
        note = self.board.footnote.text()
        self.assertIn("시가총액은 KIS 제공 값이며, 같은 응답의 상장주식수 × 현재가와 맞는 종목에만 씁니다.", note)
        self.assertIn("시가총액(계산값) = KIS 응답의 상장주식수 × 현재가입니다.", note)
        self.assertIn("2개 종목은 쓸 수 있는 시가총액이 없어 순위 없이 맨 아래에 둡니다", note)
        self.board.category_buttons["value"].click(); self.app.processEvents()
        self.assertEqual(len(self.shown_rows()), 4)  # the refused figures never cost the quotes
        self.assertNotIn("시가총액", self.board.footnote.text())
        # None usable: the list says why instead of ranking nothing.
        refused = (kis_domestic("005930", 102300, hts_avls="605", lstn_stcn="5969782550"),
                   kis_domestic("000660", 520000, hts_avls="3786"))
        self.board.batches["kr"] = R.Batch("kr", refused, "kis", NOW.isoformat())
        self.board.category_buttons["cap"].click(); self.app.processEvents()
        self.assertEqual(self.shown_rows(), [])
        self.assertEqual(self.board.empty.text(),
                         "국내 시가총액을 쓰지 못했습니다. KIS 시가총액이 같은 응답의 상장주식수 × 현재가와 25% 넘게 달라 "
                         "쓰지 않습니다. KIS 응답에 상장주식수가 없어 시가총액을 확인할 수 없으므로 쓰지 않습니다.")
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.board.empty.text(),
                         "Could not use domestic market cap. KIS's market cap differs by more than 25% from listed "
                         "shares × price of the same answer, so it is not used. KIS gave no listed share count, so "
                         "its market cap could not be checked and is not used.")
        self.board.batches["kr"] = R.Batch("kr", records, "kis", NOW.isoformat()); self.board.render()
        self.assertEqual(self.shown_rows()[0].value.toolTip(),
                         "KIS market cap (hts_avls read as 100 million won), stated 2026-11-11 14:20 KST; it agrees "
                         "within 25% with listed shares 6.0B × price 102,300 = ₩610.7T of the same KIS answer.")
        self.assertEqual(self.board.head_value.text(), "Market cap (computed)")

    def test_domestic_cap_fields_present_but_unusable_say_so(self):
        # Reviewer 2026-11-11: a listed share count of 0 is not "no share count", and a stated cap of 0 is refused,
        # never replaced by the computed figure (the docs promise that only for an absent hts_avls).
        records = (kis_domestic("005930", 102300, hts_avls="6050000", lstn_stcn="5969782550"),
                   kis_domestic("000660", 520000, hts_avls="0", lstn_stcn="728002365"),
                   kis_domestic("035720", 40000, hts_avls="17", lstn_stcn="0"))
        self.board.batches["kr"] = R.Batch("kr", records, "kis", NOW.isoformat())
        self.board.category_buttons["cap"].click(); self.app.processEvents()
        rows = self.shown_rows()
        self.assertEqual([(r.rank.text(), r.name.full, r.value.text()) for r in rows],
                         [("1", "삼성전자", "605.0조"), ("", "SK하이닉스", "—"), ("", "카카오", "—")])
        self.assertEqual(self.board.head_value.text(), "시가총액")  # nothing computed stands in for the refused cap
        self.assertEqual(rows[1].value.toolTip(), "KIS 시가총액이 0보다 큰 수가 아니어서 쓰지 않습니다.")
        self.assertEqual(rows[2].value.toolTip(),
                         "KIS 상장주식수가 0보다 큰 정수가 아니어서 시가총액을 확인하거나 계산할 수 없습니다.")
        self.board.batches["kr"] = R.Batch("kr", records[1:], "kis", NOW.isoformat()); self.board.render()
        self.assertEqual(self.board.empty.text(),
                         "국내 시가총액을 쓰지 못했습니다. KIS 시가총액이 0보다 큰 수가 아니어서 쓰지 않습니다. "
                         "KIS 상장주식수가 0보다 큰 정수가 아니어서 시가총액을 확인하거나 계산할 수 없습니다.")
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.board.empty.text(),
                         "Could not use domestic market cap. KIS's market cap is not a positive number, so it is not "
                         "used. KIS's listed share count is not a positive whole number, so the market cap could not "
                         "be checked or computed.")
        self.assertEqual(self.loader.calls, [])

    def test_us_market_cap_says_why_when_none_could_be_read(self):
        base = us_batch()
        none = replace(base, records=tuple(R.without_cap(r, "error") for r in base.records), caps="none",
                       cap_reasons=("kis_off", "fmp_no_key", "yahoo_unreachable"))
        self.board.loader = FakeLoader({"us": none})
        self.view.show_market("us"); self.board.category_buttons["cap"].click(); self.load()
        self.assertEqual(self.shown_rows(), [])
        self.assertEqual(self.board.empty.text(),
                         "미국 시가총액을 읽지 못했습니다. KIS가 연결되어 있지 않습니다. FMP_API_KEY가 설정되어 있지 않습니다. "
                         "Yahoo Finance에 연결하지 못했습니다.")
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.board.empty.text(),
                         "Could not read US market cap. KIS is not connected. FMP_API_KEY is not set. "
                         "Yahoo Finance could not be reached.")
        plan = replace(none, cap_reasons=("kis_none", "fmp_plan", "yahoo_timeout"))
        self.board.batches["us"] = plan; self.board.render()
        self.assertEqual(self.board.empty.text(), "Could not read US market cap. KIS returned no usable market cap. "
                                                  "The FMP plan does not include batch quotes. "
                                                  "Yahoo Finance did not answer in time.")
        self.board.category_buttons["volume"].click(); self.app.processEvents()
        self.assertEqual(len(self.shown_rows()), 3)  # the quotes themselves are kept

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
        self.view.show_market("us"); self.load()
        self.assertEqual(self.board.badge.text(), "자료 없음")
        self.board.loader = FakeLoader({"kr": kr_batch()})
        self.view.show_market("kr"); self.load()
        self.assertIn("1개 종목은 불러오지 못했습니다", self.board.footnote.text())  # HLB failed in the fixture
        self.board.loader = FakeLoader({"kr": RuntimeError("late")})
        self.clock.now = NOW + timedelta(minutes=2)
        self.assertTrue(self.board.refresh(manual=True)); self.wait(lambda: not self.board.jobs.busy)
        self.app.processEvents()
        self.assertTrue(self.shown_rows())  # a failed refresh keeps the last list and says how old it is
        self.assertEqual(self.board.caption.text(), "조회 실패 (RuntimeError) · 2분 전 갱신")
        self.assertEqual(self.board.badge.text(), "KIS 조회 · 45초마다")
        self.clock.now = NOW + timedelta(minutes=5); self.board._render_status()
        self.assertEqual(self.board.badge.text(), "KIS · 갱신 지연")  # an old KIS list is not called polled

    def test_rail_sub_menu_and_a_row_open_the_stock_screen(self):
        self.assertEqual(self.view.current_category(), "value")  # first visit: trading value
        heard = []
        self.view.category_changed.connect(heard.append)
        self.board.category_buttons["losers"].click()  # a chip inside the page; the rail follows the signal
        self.assertEqual((heard, self.view.current_category()), (["losers"], "losers"))
        self.view.show_category("losers")
        self.assertEqual(heard, ["losers"])  # no change, no signal
        self.view.show_category("value")
        self.assertEqual(heard, ["losers", "value"])
        scroll = self.window.stack.currentWidget().verticalScrollBar()
        self.board.loader = FakeLoader({"kr": every_domestic()})
        self.load()
        self.window.resize(1000, 700)  # the minimum window: the list runs past the fold
        for _ in range(5):
            self.app.processEvents()
        self.assertGreater(scroll.maximum(), 0)
        scroll.setValue(scroll.maximum())
        self.view.show_category("volume")
        self.assertEqual(scroll.value(), 0)  # the chosen list is brought into view from its first rank
        scroll.setValue(scroll.maximum())
        self.view.show_category("search")
        self.assertEqual(scroll.value(), 0)
        self.view.show_category("value")
        self.board.loader = FakeLoader({"kr": kr_batch()})
        self.load()
        row = self.shown_rows()[0]
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.app.processEvents()
        self.assertTrue(self.view.showing_stock())
        self.assertIsNone(self.view.current_category())
        self.assertEqual(heard[-1], "")  # a stock's screen replaced the list
        self.view.show_rankings()
        self.assertEqual((heard[-1], self.view.current_category()), ("value", "value"))
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.app.processEvents()
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
        # UI-D8: the stock screen locks the page, so its own toolbar search (on screen) takes the focus and the
        # stock stays open; the list's search bar sits above the locked page.
        self.assertTrue(self.view.stock.search.hasFocus())
        self.assertTrue(self.view.stock.search.isVisible())
        self.assertTrue(self.view.showing_stock())  # the search keeps the page that is shown
        self.view.stock.back_button.click(); self.app.processEvents()
        self.assertFalse(self.view.showing_stock())
        # UI-D8 toolbar compaction (spec 2.3): in this 1000x700 window the back button keeps only its arrow; its
        # name stays in the tooltip and the accessible name.
        back = self.view.stock.back_button
        self.assertIn(back.text(), ("←", "← 실시간 차트"))
        self.assertEqual((back.toolTip(), back.accessibleName()), ("실시간 차트로 돌아가기", "실시간 차트로 돌아가기"))
        with self.assertRaises(ValueError):
            self.view.show_category("popular")
        self.board.rows[0].setFocus()
        QTest.keyClick(self.board.rows[0], Qt.Key.Key_Return); self.app.processEvents()
        self.assertTrue(self.view.showing_stock())
        self.assertEqual(self.loader.calls, [])

    def test_language_and_theme_switch_without_refetching(self):
        from core.theme import DARK
        self.load()
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.names()[:2], ["SK hynix", "Samsung Electronics"])
        self.assertEqual(self.shown_rows()[0].value.text(), "₩1.6T")
        self.assertEqual(self.shown_rows()[0].code.full, "000660 · KOSPI")
        self.assertEqual(self.board.badge.text(), "KIS · polled every 45 s")
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


def crypto_batch(fetched_at=NOW):
    """Coins as the Yahoo daily path leaves them (`record_from_bars`): dollar volume as trading value."""
    rows = (("BTC", 96123.5, 95000.0, 4.1e10), ("ETH", 3412.8, 3480.0, 2.2e10), ("XRP", 2.31, 2.2, 6.1e9),
            ("DOGE", 0.3812, 0.37, 3.2e9))
    records = tuple(R.record_from_bars(next(m for m in R.CRYPTO if m.code == code),
                                       [("2026-11-09", 1, 1, 1, before, volume), ("2026-11-10", 1, 1, 1, last, volume)])
                    for code, last, before, volume in rows)
    return R.Batch("crypto", records, "daily", fetched_at.isoformat())


def etf_batch(group, fetched_at=NOW):
    """KIS quotes of four ETFs of a list (UI-D11): ranked as stocks are; no market cap."""
    members = R.ETF_KR if group == "etf_kr" else R.ETF_US
    rows = ((0, 1.2, 4.0e6, 1.6e11), (1, -0.8, 9.0e6, 8.0e10), (2, 2.4, 2.0e7, 3.0e11), (3, -1.9, 3.0e6, 1.0e10))
    at = fetched_at.isoformat()
    records = []
    for index, pct, volume, value in rows:
        price = 40000.0 - index * 5000 if group == "etf_kr" else 500.0 - index * 50
        scale = 1 if group == "etf_kr" else 1e-3
        records.append(R.QuoteRecord(members[index], price, price * pct / 100, pct, volume, value * scale, None, "KIS",
                                     "kis", at))
    return R.Batch(group, tuple(records), "kis", at)


def fixture_series(symbol, source="yfinance", days=400):
    """Index and coin daily closes for the strip, as `core.ficc.data.load_series` answers them."""
    from types import SimpleNamespace
    base = {"^KS11": 2600.0, "^KQ11": 750.0, "^GSPC": 5800.0, "^IXIC": 18700.0, "BTC-USD": 96000.0,
            "ETH-USD": 3400.0}[symbol]
    dates = tuple(f"2026-10-{day:02d}" for day in range(1, 31))
    return SimpleNamespace(source="YFINANCE", dates=dates, values=tuple(base * (1 + i / 1000) for i in range(30)))


class MarketPageTests(WindowBase):
    """Owner ruling UI-D10: markets in the rail; criteria and search per market; a compact page."""

    def setUp(self):
        super().setUp()
        self.loader = FakeLoader({"kr": kr_batch(), "us": us_batch(), "crypto": crypto_batch()})
        self.board.loader = self.loader
        self.series = Mock(side_effect=fixture_series)
        self.board.summary.loader = self.series

    def test_show_market_switches_pages_and_each_keeps_its_own_criteria(self):
        heard = []
        self.view.market_changed.connect(heard.append)
        self.assertEqual((self.view.current_market(), self.board.heading.text()), ("kr", "국내 주식"))
        self.assertTrue(self.window.market_sections["stocks"].isChecked())
        self.assertTrue(self.view.show_market("us")); self.app.processEvents()
        self.assertEqual((heard, self.board.page, self.board.heading.text()), (["us"], "us", "미국 주식"))
        self.assertTrue(self.window.market_sections["stocks"].isChecked())  # the rail follows the page
        self.view.show_market("crypto"); self.app.processEvents()
        self.assertEqual([k for k, b in self.window.market_sections.items() if b.isChecked()], ["crypto"])
        self.view.show_market("us"); self.app.processEvents()
        self.assertEqual([b.text() for b in self.board.sub_buttons.values()], ["전체", "나스닥", "NYSE"])
        # The placeholder follows the field's width (`RankingBoard._render_placeholder`): the long or the short form,
        # both naming this market. Which one fits depends on the platform's text widths (Windows CI chose the short).
        self.assertIn(self.board.search.placeholderText(), ("미국 주식에서 찾기 · 이름, 코드, 업종", "미국 주식 안에서 찾기"))
        self.load()
        self.board.category_buttons["gainers"].click()
        self.board.sub_buttons["NYS"].click(); self.app.processEvents()
        self.assertEqual(self.names(), ["JP모건"])  # NYSE only, rising only
        self.view.show_market("kr"); self.load()
        self.assertEqual((self.board.category, self.board.sub), ("value", ""))  # Korea keeps its own criteria
        self.view.show_market("us")
        self.assertEqual((self.board.category, self.board.sub, self.names()), ("gainers", "NYS", ["JP모건"]))
        # Earlier callers: a category ranks the shown market; a market key shows that market.
        self.assertTrue(self.view.show_category("losers"))
        self.assertEqual((self.board.page, self.board.category), ("us", "losers"))
        self.assertTrue(self.view.show_category("crypto"))
        self.assertEqual(self.board.page, "crypto")
        with self.assertRaises(ValueError):
            self.view.show_market("jp")
        # A stock opened over a market keeps that market highlighted; Back returns to its list.
        self.view.show_market("us"); self.board.set_sub(""); self.board.set_category("value")
        QTest.mouseClick(self.shown_rows()[0], Qt.MouseButton.LeftButton); self.app.processEvents()
        self.assertTrue(self.view.showing_stock())
        self.window.navigate("markets")
        self.assertTrue(self.window.market_sections["stocks"].isChecked())
        self.view.open_instrument(member("005930").instrument)  # a Korean stock from elsewhere (Home's cards)
        self.view.stock.back_button.click(); self.app.processEvents()
        self.assertEqual((self.board.page, self.view.showing_stock()), ("kr", False))
        self.assertEqual(self.loader.calls, ["us", "kr"])

    def test_search_category_and_conditions_combine(self):
        self.load()
        self.view.search.setText("반도체"); self.app.processEvents()  # a sector's name finds its stocks
        self.assertEqual(self.names(), ["SK하이닉스", "삼성전자"])  # ranked by trading value
        chips = [c for c in self.board.filter_chips if c.isVisible()]
        self.assertEqual([c.text() for c in chips], ["‘반도체’  ×"])
        self.assertEqual(self.board.count.text(), "종목 2개")  # UI-D10 review: as the crypto page's "자산 2개"
        self.board.category_buttons["gainers"].click(); self.app.processEvents()
        self.assertEqual(self.names(), ["삼성전자"])  # the same search, ranked by the rise
        self.board.category_buttons["value"].click()
        self.board.conditions_button.click(); self.app.processEvents()
        self.assertTrue(self.board.conditions_section.isVisible())
        self.assertEqual(self.board.conditions_button.text(), "조건")
        low, high = self.board.condition_controls["change"]
        low.setFocus(); QTest.keyClicks(low, "0"); self.app.processEvents()
        self.assertEqual(self.names(), ["삼성전자"])  # change at least 0%
        box = self.board.condition_controls["value"][0]
        self.assertEqual([box.itemText(i) for i in range(box.count())],
                         ["제한 없음", "100억 이상", "500억 이상", "1,000억 이상", "5,000억 이상"])
        self.view.search.setText(""); self.app.processEvents()
        box.setCurrentIndex(box.findData(5e11)); self.app.processEvents()
        self.assertEqual(self.names(), ["삼성전자", "카카오"])  # 0% or more, trading value 5,000억 or more
        # UI-D10 review: the open panel shows the conditions itself; their chips show once it is closed.
        self.assertEqual([c.text() for c in self.board.filter_chips if c.isVisible()], [])
        self.board.conditions_button.click(); self.app.processEvents()
        self.assertEqual([c.text() for c in self.board.filter_chips if c.isVisible()],
                         ["등락률 0% 이상  ×", "거래대금 5,000억 이상  ×"])
        self.assertEqual(self.board.conditions_button.text(), "조건 2")
        self.board.conditions_button.click(); self.app.processEvents()
        high.setFocus(); QTest.keyClicks(high, "-1"); self.app.processEvents()
        self.assertTrue(high.property("invalid"))  # a low bound above the high one is not applied
        self.assertEqual(self.names(), ["삼성전자", "카카오"])
        high.clear(); QTest.keyClicks(high, "2"); self.app.processEvents()
        self.assertEqual(self.names(), ["삼성전자"])
        self.board.conditions_button.click(); self.app.processEvents()
        next(c for c in self.board.filter_chips if c.isVisible()).click(); self.app.processEvents()
        self.assertEqual((low.text(), high.text()), ("", ""))  # one click removes that condition
        self.assertEqual(self.names(), ["SK하이닉스", "삼성전자", "카카오"])
        self.view.search.setText("카카"); self.app.processEvents()
        self.assertEqual(self.names(), ["카카오"])
        self.board.clear_button.click(); self.app.processEvents()  # 모두 지우기: search and conditions
        self.assertEqual((self.view.search.text(), self.board.screen.limits), ("", ()))
        self.assertEqual(len(self.names()), 6)
        self.view.search.setText("없는이름"); self.app.processEvents()
        self.assertEqual(self.board.empty.text(), "이 목록에는 ‘없는이름’에 맞는 종목이 없습니다.")
        self.view.search.setText("현대"); self.app.processEvents()
        QTest.keyClick(self.view.search, Qt.Key.Key_Return); self.app.processEvents()
        self.assertEqual(self.view.stock.instrument, member("005380").instrument)  # one match: Enter opens it
        self.view.show_rankings()
        self.assertEqual(self.view.search.text(), "현대")  # the narrowed list is still there on return
        self.view.search.setText("101W12"); self.app.processEvents()  # a derivative's code: offered, not guessed
        offered = [b for b in self.board.other_buttons if b.isVisible()]
        self.assertEqual([b.text() for b in offered], ["국내 파생 101W12"])
        self.assertFalse(self.view.showing_stock())
        offered[0].click(); self.app.processEvents()
        self.assertEqual(self.view.stock.instrument.asset, "domestic_future")
        self.assertEqual(self.loader.calls, ["kr"])  # narrowing and opening never refetch

    def test_a_new_condition_is_one_more_row_of_data(self):
        from core.market import screen as S
        extra = S.Condition("volume", "Volume", "거래량", "min", "money", lambda r: r.volume, pages=("kr",),
                            steps={"kr": (5e6, 1e7)})
        with patch.object(S, "CONDITIONS", S.CONDITIONS + (extra,)), \
                patch.object(S, "CONDITION_KEYS", S.CONDITION_KEYS + ("volume",)):
            board = RankingBoard(loader=FakeLoader({"kr": kr_batch()}), locale=LocaleContext("ko_KR"),
                                 auto_load=False, clock=Clock(), open_fn=lambda group, now: True)
            self.addCleanup(board.deleteLater)
            board.resize(1200, 900); board.show()
            self.assertTrue(board.refresh(manual=True))
            self.wait(lambda: not board.jobs.busy and "kr" in board.batches)
            self.app.processEvents()
            box = board.condition_controls["volume"][0]  # built from the table, no code of its own
            self.assertEqual(board.condition_names["volume"].text(), "거래량")
            box.setCurrentIndex(box.findData(1e7)); self.app.processEvents()
            # volume 1,000만 or more, ranked by trading value
            self.assertEqual([r.name.full for r in board.rows if r.isVisible()], ["삼성전자", "카카오"])
            board.set_page("us")
            self.assertFalse(board.condition_groups["volume"].isVisibleTo(board))  # Korea only, as its table says

    def test_coin_market_degrades_cleanly(self):
        self.view.show_market("crypto"); self.load()
        self.assertEqual(self.board.heading.text(), "크립토")
        self.assertEqual(self.board.badge.text(), "지연·일별")  # Yahoo daily bars, never live
        self.assertEqual(self.names(), ["비트코인", "이더리움", "리플", "도지코인"])
        top = self.shown_rows()[0]
        self.assertEqual((top.price.text(), top.value.text(), top.code.full), ("$96,123.50", "$41.0B", "BTC"))
        self.assertEqual(self.shown_rows()[3].price.text(), "$0.3812")
        # UI-D10 review: a ranking coins cannot make is left out (a disabled chip read as a dead tab, its reason
        # in a tooltip no keyboard reaches); the footnote says why.
        self.assertEqual([k for k, b in self.board.category_buttons.items() if b.isVisible()],
                         ["value", "gainers", "losers"])
        self.assertIn("가상자산은 거래량·시가총액 순위가 없습니다", self.board.footnote.text())
        self.assertIn("가상자산 시가총액이 없습니다", self.board.footnote.text())
        self.assertFalse(any(b.isVisible() for b in self.board.sub_buttons.values()))
        self.assertFalse(self.board.sector_box.isVisible())
        self.board.conditions_button.click(); self.app.processEvents()
        self.assertFalse(self.board.condition_groups["cap"].isVisible())
        self.assertTrue(self.board.condition_groups["value"].isVisible())
        self.board.set_category("cap")  # set from code all the same: the list says why instead of ranking nothing
        self.assertEqual(self.board.empty.text(), "이 앱이 쓰는 자료에는 가상자산 시가총액이 없어 시가총액 순위를 매기지 않습니다.")
        self.board.set_category("gainers")
        self.assertEqual(self.names(), ["리플", "도지코인", "비트코인"])  # +5.00%, +3.03%, +1.18%
        row = self.shown_rows()[0]
        self.assertIn("가상자산은 아직 종목 화면이 없어", row.toolTip())
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.app.processEvents()
        row.setFocus(); QTest.keyClick(row, Qt.Key.Key_Return); self.app.processEvents()
        self.assertFalse(self.view.showing_stock())  # nothing opens, nothing breaks
        self.view.search.setText("엑스알피"); self.app.processEvents()
        self.assertEqual(self.names(), ["리플"])
        QTest.keyClick(self.view.search, Qt.Key.Key_Return); self.app.processEvents()
        self.assertFalse(self.view.showing_stock())
        self.assertIn("UTC", self.board.badge.toolTip()); self.assertIn("Yahoo Finance", self.board.badge.toolTip())
        shown = " ".join(self.page_text())
        self.assertNotIn("Yahoo", " ".join(t for t in self.page_text() if "지연·일별:" not in t))
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown), shown)
        self.board.batches["crypto"] = R.Batch("crypto", (), "none", NOW.isoformat()); self.board.render()
        self.assertEqual((self.board.badge.text(), self.shown_rows()), ("자료 없음", []))
        self.assertEqual(self.loader.calls, ["crypto"])

    def test_index_strip_loads_with_refresh_and_says_delayed(self):
        self.assertFalse(self.board.summary_section.isVisible())
        self.board.refresh_button.click()
        self.wait(lambda: not self.board.jobs.busy and not self.board.summary.jobs.busy and "kr" in self.board.batches)
        self.app.processEvents()
        self.assertTrue(self.board.summary_section.isVisible())
        tiles = [t for t in self.board.summary.tiles.values() if t.isVisible()]
        self.assertEqual([(t.name.text(), t.value.text(), t.change.text()) for t in tiles],
                         [("코스피", "2,675.40", "+0.10%"), ("코스닥", "771.75", "+0.10%")])
        self.assertIn("Yahoo Finance", tiles[0].toolTip()); self.assertIn("2026-10-30", tiles[0].toolTip())
        self.assertTrue(self.board.summary.state.isVisible())  # the list is KIS-polled, the strip is daily: said
        self.assertEqual(self.board.summary.state.text(), "지연·일별")
        self.assertEqual([c.args[0] for c in self.series.call_args_list], ["^KS11", "^KQ11"])
        self.view.show_market("crypto")
        self.board.refresh_button.click()
        self.wait(lambda: not self.board.jobs.busy and not self.board.summary.jobs.busy
                  and "crypto" in self.board.batches)
        self.app.processEvents()
        names = [t.name.text() for t in self.board.summary.tiles.values() if t.isVisible()]
        self.assertEqual(names, ["비트코인", "이더리움"])
        self.assertFalse(self.board.summary.state.isVisible())  # the header already says 지연·일별
        self.series.side_effect = RuntimeError("provider text")  # a failed reload keeps the closes shown
        self.board.summary.refresh(manual=True)
        self.wait(lambda: not self.board.summary.jobs.busy)
        self.app.processEvents()
        self.assertEqual(self.board.summary.tiles["BTC-USD"].value.text(), "$98,784.00")
        self.view.show_market("us"); self.board.summary.refresh(manual=True)
        self.wait(lambda: not self.board.summary.jobs.busy)
        self.app.processEvents()
        tile = self.board.summary.tiles["^GSPC"]
        self.assertEqual(tile.value.text(), "—")
        self.assertIn("provider_unavailable", tile.toolTip()); self.assertNotIn("provider text", tile.toolTip())
        self.production_series.assert_not_called()

    def test_language_switch_refetches_nothing(self):
        self.load()
        self.board.summary.refresh(manual=True)
        self.wait(lambda: not self.board.summary.jobs.busy)
        self.board.set_limit("change", 0, None)
        self.board.set_conditions_open(True)
        series_calls = self.series.call_count
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.board.heading.text(), "Korean stocks")
        # UI-D10 review: the open 조건 panel shows the condition itself, so its chip shows only once it is closed.
        self.assertEqual([c.text() for c in self.board.filter_chips if c.isVisible()], [])
        self.board.set_conditions_open(False)
        self.assertEqual([c.text() for c in self.board.filter_chips if c.isVisible()], ["Change at least 0%  ×"])
        self.assertEqual(self.board.condition_names["value"].text(), "Trading value")
        self.assertEqual(self.board.conditions_button.text(), "Conditions 1")
        self.assertEqual([t.name.text() for t in self.board.summary.tiles.values() if t.isVisible()],
                         ["KOSPI", "KOSDAQ"])
        self.assertEqual([b.text() for b in self.window.market_sections.values()],
                         ["Indices", "Stocks", "Crypto", "Futures", "Forex", "Government bonds", "Corporate bonds",
                          "ETFs", "World economy"])
        self.assertEqual([t for t in self.page_text() if re.search("[가-힣]", t)], [])
        fly = self.window.rail_flyouts
        # Owner 2026-11-13: the rail stops at country; rankings stay on the page.
        country = fly.open_root(self.window.market_sections["stocks"])
        self.assertIsNotNone(country)
        self.assertEqual([r.text() for r in country.rows], ["Korea", "US"])
        self.assertEqual([r.node.leaf for r in country.rows],
                         [("market", "kr", ""), ("market", "us", "")])
        self.assertTrue(all(not r.node.children for r in country.rows))
        self.assertEqual(len(fly.panels), 1)
        self.assertEqual([b.text() for b in self.board.category_buttons.values() if b.isVisible()],
                         ["Trading value", "Volume", "Top gainers", "Top losers", "Market cap", "Q-SCORE highest first"])
        self.window.set_language("ko"); self.app.processEvents()
        self.assertFalse(fly.is_open())
        self.assertEqual([b.text() for b in self.window.market_sections.values()],
                         ["지수", "주식", "크립토", "선물", "외환", "국채", "회사채", "ETF", "월드 이코노미"])
        country = fly.open_root(self.window.market_sections["stocks"])
        self.assertIsNotNone(country)
        self.assertEqual([r.text() for r in country.rows], ["국내", "미국"])
        self.assertEqual([bool(r.property("current")) for r in country.rows], [True, False])
        self.assertEqual([b.text() for b in self.board.category_buttons.values() if b.isVisible()],
                         ["거래대금", "거래량", "급상승", "급하락", "시가총액", "Q-SCORE 높은 순"])
        self.assertEqual([b.isChecked() for b in self.board.category_buttons.values()],
                         [True, False, False, False, False, False])
        fly.close_all()
        self.assertEqual((self.loader.calls, self.series.call_count), (["kr"], series_calls))

    def test_every_control_shows_the_windows_focus_ring(self):
        from core.theme import DARK, LIGHT
        self.load()
        self.view.search.setText("삼성")  # the search's chip shows while the 조건 panel is open (UI-D10 review)
        self.board.set_limit("change", 0, None)
        self.board.set_conditions_open(True)
        self.window.activateWindow(); self.app.processEvents()
        for theme in (0, 1):
            self.window.theme.setCurrentIndex(theme); self.app.processEvents()
            accent = (DARK if theme else LIGHT).accent
            sheet = self.board.styleSheet()
            for selector in ("QLineEdit#marketSearch:focus", "QPushButton#conditionsToggle:focus",
                             "QLineEdit#condEdit:focus", "QComboBox#condBox:focus",
                             "QPushButton[filterChip='true']:focus", "QPushButton[textButton='true']:focus",
                             "QPushButton#otherStock:focus", "QPushButton#rankRefresh:focus"):
                self.assertIn(f"{selector} {{ border: 2px solid {accent}", sheet, selector)
            chip = next(c for c in self.board.filter_chips if c.isVisible())
            for widget in (self.board.search, self.board.conditions_button, chip,
                           self.board.condition_controls["change"][0], self.board.condition_controls["value"][0],
                           self.board.conditions_clear):
                self.board.refresh_button.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
                plain, size = accent_pixels(widget, accent), widget.size()
                widget.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
                self.assertTrue(widget.hasFocus(), widget)
                self.assertGreater(accent_pixels(widget, accent), plain + widget.width(), widget)
                self.assertEqual(widget.size(), size, widget)  # the ring does not resize the control
        self.window.theme.setCurrentIndex(0); self.app.processEvents()
        # Keyboard path through the 조건 row: Tab from the toggle reaches its fields, then the active chips.
        self.board.conditions_button.setFocus(Qt.FocusReason.TabFocusReason)
        seen = []
        for _ in range(5):
            QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Tab); self.app.processEvents()
            seen.append(self.app.focusWidget())
        low, high = self.board.condition_controls["change"]
        self.assertEqual(seen[:4], [low, high, self.board.condition_controls["value"][0],
                                    self.board.condition_controls["cap"][0]])
        QTest.keyClick(self.board.conditions_button, Qt.Key.Key_Space); self.app.processEvents()

    def test_refresh_off_fetches_nothing_on_any_market(self):
        for key in ("kr", "us", "crypto"):
            self.window.open_market_section(key); self.app.processEvents()
            self.assertFalse(self.board.jobs.busy or self.board.summary.jobs.busy, key)
            self.assertFalse(self.board.summary_section.isVisible(), key)
        self.assertEqual((self.loader.calls, self.series.call_count), ([], 0))
        self.production_series.assert_not_called()


def every_us(fetched_at=NOW):
    """Every US member with a KIS quote and market cap (long English names, every figure the list can show)."""
    at = fetched_at.isoformat()
    records = []
    for i, m in enumerate(R.US):
        price = 100.0 + i
        record = R.QuoteRecord(m, price, 1.0, 0.5 - i / 50, 1e6 + i, 2e9 - i * 1e7, None, "KIS", "kis", at)
        records.append(R.with_cap(record, 1e12 - i * 1e10, basis="provider", source="KIS", as_of=at, shares=1e9))
    return R.Batch("us", tuple(records), "kis", at, caps="ok")


def daily_kr(fetched_at=NOW):
    """The Yahoo daily path for Korea: closes for the sparkline, estimated trading value, no market cap."""
    rows = (("005930", 102300.0, 1.5, 1.49e7), ("000660", 520000.0, -2.0, 3.1e6), ("035720", 40000.0, 4.2, 2.0e7))
    records = tuple(R.QuoteRecord(member(c), p, p * x / 100, x, v, p * v, None, "Yahoo Finance", "daily",
                                  "2026-11-10", estimated_value=True, closes=(p * 0.9, p * 0.95, p))
                    for c, p, x, v in rows)
    return R.Batch("kr", records, "daily", fetched_at.isoformat())


def clear_mark_shown(edit):
    """Whether a line edit's clear (⊗) button is drawn: Qt fades it by its `opacity` (0 hidden, 1 shown)."""
    from PyQt6.QtWidgets import QToolButton
    return any((button.property("opacity") or 0) > 0 for button in edit.findChildren(QToolButton))


class EtfAndCryptoNameTests(WindowBase):
    """Owner ruling UI-D11 (2026-11-12): "코인이 뭐야 ETF라해야지" — ETF markets on the same page and paths as stocks,
    and the coin market called 크립토 (가상자산 in sentences), never 코인; the page itself unchanged (R-D11-3)."""

    def setUp(self):
        super().setUp()
        self.loader = FakeLoader({"kr": kr_batch(), "us": us_batch(), "crypto": crypto_batch(),
                                  "etf_kr": etf_batch("etf_kr"), "etf_us": etf_batch("etf_us")})
        self.board.loader = self.loader
        self.series = Mock(side_effect=fixture_series)
        self.board.summary.loader = self.series
        self.addCleanup(self.idle)

    def idle(self):
        self.board.stop()
        self.wait(lambda: not self.board.jobs.busy and not self.board.summary.jobs.busy)

    def test_etf_pages_reuse_the_market_page_and_open_the_stock_screen(self):
        opened = []
        self.view.stock.show_instrument = lambda instrument, load=True: opened.append(instrument)
        self.window.open_market_leaf(("market", "etf_kr", "volume"))  # 시장 › ETF › 국내 › 거래량
        self.load()
        self.assertEqual((self.board.heading.text(), self.board.category), ("국내 ETF", "volume"))
        self.assertEqual([k for k, b in self.window.market_sections.items() if b.isChecked()], ["etf"])
        self.assertEqual(self.names(), ["KODEX 레버리지", "TIGER 200", "KODEX 200", "KODEX 인버스"])
        self.assertEqual(self.board.badge.text(), "KIS 조회 · 45초마다")
        # No market cap for ETFs: the chip, the column and the condition are left out, and the footnote says why.
        self.assertEqual([k for k, b in self.board.category_buttons.items() if b.isVisible()],
                         ["value", "volume", "gainers", "losers"])
        self.assertNotIn("cap", dict(self.board.column_header.plan))
        self.assertIn("ETF는 시가총액 순위가 없습니다", self.board.footnote.text())
        self.assertIn("순자산(AUM)", self.board.footnote.text())
        self.assertIn("주요 ETF 20개 안에서 매긴 순위", self.board.footnote.text())
        self.assertFalse(self.board.sector_box.isVisible())
        self.assertFalse(any(segment.isVisible() for segment in self.board.segments.values()))
        self.board.conditions_button.click(); self.app.processEvents()
        self.assertFalse(self.board.condition_groups["cap"].isVisible())
        self.board.conditions_button.click(); self.app.processEvents()
        self.assertIn(self.board.search.placeholderText(), ("국내 ETF에서 찾기 · 이름이나 코드", "국내 ETF 안에서 찾기"))
        self.board.set_category("cap")  # from code all the same: the list says why
        self.assertIn("ETF의 규모는 시가총액이 아니라 순자산(AUM)", self.board.empty.text())
        self.board.set_category("value")
        top = self.shown_rows()[0]
        self.assertEqual((top.name.full, top.code.full, top.price.text(), top.value.text()),
                         ("KODEX 레버리지", "122630", "30,000", "3,000억"))
        QTest.mouseClick(top, Qt.MouseButton.LeftButton); self.app.processEvents()
        self.assertEqual(opened[-1], R.ETF_KR[2].instrument)  # an ETF opens the stock screen like a stock
        self.assertEqual(opened[-1].asset, "domestic_stock")
        self.view.stock.back_button.click(); self.app.processEvents()
        self.assertEqual((self.board.page, self.view.showing_stock()), ("etf_kr", False))  # back to the ETF list
        self.view.search.setText("레버리지"); self.app.processEvents()
        self.assertEqual(self.names(), ["KODEX 레버리지"])
        self.assertEqual(self.board.count.text(), "ETF 1개")
        self.view.search.setText("")
        self.window.open_market_leaf(("market", "etf_us", "gainers"))
        self.load()
        self.assertEqual((self.board.heading.text(), self.board.page, self.board.category), ("미국 ETF", "etf_us",
                                                                                              "gainers"))
        self.assertEqual(self.board.badge.text(), "KIS 무료 시세 · 45초마다")
        self.assertEqual(self.names(), ["뱅가드 S&P 500", "SPDR S&P 500"])
        top = self.shown_rows()[0]
        self.assertEqual((top.code.full, top.mark.spec.letters), ("VOO", "VO"))  # a ticker's letters, as US stocks
        QTest.mouseClick(top, Qt.MouseButton.LeftButton); self.app.processEvents()
        self.assertEqual((opened[-1].asset, opened[-1].code, opened[-1].exchange), ("overseas_stock", "VOO", "AMS"))
        self.view.stock.back_button.click(); self.app.processEvents()
        self.assertEqual(self.board.page, "etf_us")
        # The index strip shows the ETF's home market; one fetch per list, and the strip's series are shared.
        self.assertEqual(self.loader.calls, ["etf_kr", "etf_us"])

    def test_no_coin_label_in_the_korean_window(self):
        from quantgen_desktop.markets_view import MARKET_PAGES
        from PyQt6.QtWidgets import QAbstractButton, QLineEdit
        everyone = R.DOMESTIC + R.US + R.CRYPTO + R.ETF_KR + R.ETF_US
        names = sorted({n for m in everyone for n in (m.name_ko, m.name_en, *m.aliases)}, key=len, reverse=True)

        def scrub(text):
            for name in names:  # an asset's own name (비트코인, 라이트코인, 코인베이스) is not a label
                text = text.replace(name, "")
            return text

        def texts(root):
            out = []
            for widget in (root, *root.findChildren(QWidget)):
                if not widget.isVisible():
                    continue
                out += [widget.toolTip(), widget.accessibleName(), widget.accessibleDescription()]
                if isinstance(widget, (QLabel, QAbstractButton)):
                    out.append(widget.text())
                if isinstance(widget, QLineEdit):
                    out += [widget.text(), widget.placeholderText()]
                if isinstance(widget, QComboBox):
                    out += [widget.itemText(i) for i in range(widget.count())]
            return [t for t in out if t]

        seen = []
        for page, _english, korean in MARKET_PAGES:
            self.window.open_market_section(page)
            self.load()
            self.board.summary.refresh(manual=True)
            self.wait(lambda: not self.board.summary.jobs.busy)
            self.app.processEvents()
            self.assertEqual(self.board.heading.text(), korean)
            for key, chip in self.board.category_buttons.items():
                if chip.isVisible():
                    chip.click(); self.app.processEvents()
                    seen += texts(self.window)
            self.view.search.setText("zzz"); self.app.processEvents()  # the empty states
            seen += texts(self.window)
            self.view.search.setText("")
        fly = self.window.rail_flyouts
        for key, row in self.window.market_sections.items():
            seen.append(row.text())
            panel = fly.open_root(row)
            if key in ("crypto", "futures", "corp"):
                # These approved direct destinations deliberately have no submenu.
                self.assertIsNone(panel)
                self.assertEqual(fly.panels, [])
                self.assertFalse(row.chevron)
                fly.close_all()
                continue
            self.assertIsNotNone(panel, key)
            seen += texts(panel)
            for sub in [r for r in panel.rows if r.node.children]:
                seen += texts(fly.open_child(sub))
            fly.close_all()
        self.assertIn("크립토", seen)
        self.assertIn("가상자산", " ".join(seen))
        self.assertEqual([t for t in seen if "코인" in scrub(t)], [])


class MarketReviewTests(WindowBase):
    """UI-D10 review (2026-11-11): two independent reviewers' findings, each pinned by its scenario."""

    def setUp(self):
        Base.setUp(self)
        self.provider = Mock(side_effect=AssertionError("Provider forbidden"))
        self.directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        self.window = ResearchWindow(auto_refresh=False, locale="ko_KR", market_loader=self.provider,
                                     connections_runner=self.provider, symbol_directory=self.directory,
                                     profile_loader=Mock(side_effect=AssertionError("No profile")))
        self.window.resize(1440, 940); self.window.show(); self.window.navigate("markets")
        self.app.processEvents()
        self.addCleanup(delete_owned_widget, self.window)
        self.view = self.window.markets_view
        self.board = self.view.rankings
        self.addCleanup(self.idle)
        self.loader = FakeLoader({"kr": kr_batch(), "us": us_batch(), "crypto": crypto_batch()})
        self.board.loader, self.clock = self.loader, Clock()
        self.board.clock = self.clock
        self.board.open_fn = lambda group, now: True
        self.series = Mock(side_effect=fixture_series)
        self.board.summary.loader = self.series

    def idle(self):
        self.board.stop()
        self.wait(lambda: not self.board.jobs.busy and not self.board.summary.jobs.busy)

    def settle(self, seconds=0.3):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.app.processEvents(); time.sleep(0.01)

    def test_home_add_and_enter_reach_stocks_from_the_coin_page(self):
        # Review: Home's "add to watchlist" landed on the coin search once Markets was last on 코인.
        self.window.activateWindow(); self.app.processEvents()
        opened = []
        self.view.stock.show_instrument = lambda instrument, load=True: opened.append(instrument.code)
        self.window.open_market_section("us"); self.window.open_market_section("crypto")
        self.window.navigate("home"); self.window.home_view.add_requested.emit(); self.app.processEvents()
        self.assertEqual(self.board.page, "us")  # the stock market shown last, never the coin page
        self.assertIs(self.app.focusWidget(), self.view.search)
        self.view.show_market("crypto")
        self.window.open_live_chart(); self.app.processEvents()
        self.assertEqual(self.board.page, "us")
        self.view.show_market("crypto"); self.view.show_category("search")
        self.assertEqual(self.board.page, "us")
        self.view.show_market("kr")
        self.view.search.setText("005930"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertEqual(opened, ["005930"])
        # Enter on the coin page with a stock's name or code: the stock opens, nothing says "no coin".
        self.view.show_rankings(); self.view.show_market("crypto")
        self.view.search.setText("AAPL"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertEqual((opened[-1], self.board.message.isVisible()), ("AAPL", False))
        self.view.show_rankings(); self.view.show_market("crypto")
        self.view.search.setText("zzz"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertEqual(self.board.message.text(), "이 목록에는 ‘zzz’에 맞는 가상자산이 없습니다.")
        self.assertEqual(self.loader.calls, [])

    def test_enter_reads_the_markets_own_list_and_says_no_match_only_when_true(self):
        opened = []
        self.view.stock.show_instrument = lambda instrument, load=True: opened.append(instrument.code)
        # Not loaded: '카카오' is in the curated list, so Enter opens it (the one whose name it is) without quotes.
        self.view.search.setText("카카오"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertEqual((opened, self.board.message.isVisible()), (["035720"], False))
        self.view.show_rankings()
        # Coins not loaded: BTC is a listed coin; the page says it is not loaded, not that no coin matches.
        self.view.show_market("crypto")
        self.view.search.setText("BTC"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertFalse(self.board.message.isVisible())
        self.assertIn("아직 불러오지 않았습니다", self.board.empty.text())
        # Loaded, 급상승, ETH (down): no "no coin" message; the empty state names the cause and a way out.
        self.load(); self.board.set_category("gainers")
        self.view.search.setText("ETH"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertFalse(self.board.message.isVisible())
        self.assertEqual(self.board.empty.text(),
                         "급상승은 오른 가상자산만 보여 줍니다. 지금 기준에 맞는 가상자산 1개는 오르지 않았습니다.")
        action = next(b for b in self.board.empty_actions if b.isVisible())
        self.assertEqual(action.text(), "거래대금 순으로 보기")
        self.assertFalse(self.board.count.isVisible())  # no "자산 0개" beside the empty state
        action.click(); self.app.processEvents()
        self.assertEqual((self.board.category, self.names()), ("value", ["이더리움"]))
        self.assertEqual(opened, ["035720"])

    def test_the_message_follows_its_market_and_language(self):
        self.view.show_market("crypto")
        self.view.search.setText("zzz"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertTrue(self.board.message.isVisible())
        self.view.show_market("kr"); self.app.processEvents()
        self.assertEqual((self.board.message.isVisible(), self.board.active_section.isVisible()), (False, False))
        self.view.search.setText("zzz"); QTest.keyClick(self.view.search, Qt.Key.Key_Return)
        self.assertEqual(self.board.message.text(),
                         "‘zzz’에 맞는 종목을 찾지 못했습니다. 이름을 고치거나 종목 코드를 입력하세요.")
        self.window.set_language("en"); self.app.processEvents()
        self.assertEqual(self.board.message.text(), "No stock matches ‘zzz’. Check the name or enter its code.")
        self.assertEqual(self.loader.calls, [])

    def test_opening_another_markets_stock_fetches_nothing_behind_its_screen(self):
        # Review: set_page ran while the list was visible, so a US round and the US strip loaded behind the stock.
        self.view.stock.show_instrument = lambda instrument, load=True: None
        self.board.auto_load = self.board.summary.auto_load = True
        self.board.hide(); self.board.show()
        self.wait(lambda: "kr" in self.board.batches and not self.board.jobs.busy and not self.board.summary.jobs.busy)
        self.settle()
        self.assertEqual((self.loader.calls, [c.args[0] for c in self.series.call_args_list]),
                         (["kr"], ["^KS11", "^KQ11"]))
        self.view.open_instrument(member("AAPL").instrument)
        self.settle(0.5)
        self.assertEqual((self.view.showing_stock(), self.board.page), (True, "us"))
        self.assertEqual((self.loader.calls, self.series.call_count), (["kr"], 2))  # nothing behind the stock screen
        self.assertFalse(self.board.refresh() or self.board.summary.refresh())  # hidden: automatic loads wait
        self.view.show_rankings()
        self.wait(lambda: "us" in self.board.batches and not self.board.summary.jobs.busy
                  and self.board.summary.has_data("us"))
        self.assertEqual(self.loader.calls, ["kr", "us"])  # Back shows the US list: it loads now

    def test_strip_keeps_a_refresh_pressed_while_it_loads_and_stops_on_close(self):
        gate, asked = threading.Event(), []

        def slow(symbol, **kwargs):
            asked.append(symbol)
            gate.wait(5)
            return fixture_series(symbol)
        self.board.summary.loader = slow
        self.board.refresh_button.click()  # 국내 주식: list and strip
        self.wait(lambda: asked == ["^KS11"] and not self.board.jobs.busy)
        self.view.show_market("us")
        self.board.refresh_button.click()  # 미국 주식 while the domestic strip still loads
        gate.set()
        self.wait(lambda: self.board.summary.has_data("us") and not self.board.summary.jobs.busy)
        self.app.processEvents()
        self.assertEqual(asked, ["^KS11", "^KQ11", "^GSPC", "^IXIC"])  # the second Refresh was kept, not dropped
        self.assertTrue(self.board.summary_section.isVisible())
        # Closing while the strip loads: the job stops before its second request.
        gate.clear(); asked.clear()
        self.board.summary.refresh(manual=True)
        self.wait(lambda: asked == ["^GSPC"])
        self.view.stop(); gate.set()
        self.wait(lambda: not self.board.summary.jobs.busy)
        self.settle(0.2)
        self.assertEqual(asked, ["^GSPC"])

    def sideways_report(self, scroll, language, page, size, category):
        """What made the page wider than its viewport: sizes, then the widest and right-most visible widgets
        (Windows CI failed this check where Linux passes; the message names the culprit)."""
        from PyQt6.QtWidgets import QWidget
        board, viewport = self.board, scroll.viewport()
        widgets = [w for w in board.findChildren(QWidget) if w.isVisible()]

        def name(w):
            text = w.text() if hasattr(w, "text") and callable(w.text) else ""
            return f"{type(w).__name__}#{w.objectName()}:{str(text)[:28]!r}"
        widest = sorted(widgets, key=lambda w: -w.minimumSizeHint().width())[:6]
        rightmost = sorted(widgets, key=lambda w: -w.mapTo(board, w.rect().topRight()).x())[:6]
        return (f"{language}/{page}/{size}/{category}: window {self.window.width()}x{self.window.height()}, "
                f"viewport {viewport.width()}x{viewport.height()}, hbar max {scroll.horizontalScrollBar().maximum()}, "
                f"vbar {scroll.verticalScrollBar().isVisible()}, board {board.width()} min {board.minimumSizeHint().width()} "
                f"hint {board.sizeHint().width()} minW {board.minimumWidth()}; widest "
                + ", ".join(f"{name(w)}={w.minimumSizeHint().width()}" for w in widest)
                + "; rightmost " + ", ".join(f"{name(w)}@{w.mapTo(board, w.rect().topRight()).x()}" for w in rightmost))

    def test_no_market_or_language_scrolls_sideways_at_1000_px(self):
        # Review: English 1000-1250 px overflowed (criteria stuck on one line, Refresh and columns cut off).
        self.board.loader = FakeLoader({"kr": every_domestic(), "us": every_us(), "crypto": crypto_batch()})
        scroll = self.window.stack.widget(self.window.route_indices["markets"])
        for language in ("en", "ko"):
            self.window.set_language(language); self.app.processEvents()
            for page in ("kr", "us", "crypto"):
                self.view.show_market(page)
                if page not in self.board.batches:
                    self.load()
                if not self.board.summary.has_data(page):
                    self.board.summary.refresh(manual=True)
                    self.wait(lambda: not self.board.summary.jobs.busy)
                for size in ((1000, 700), (1440, 900), (1000, 700), (1250, 800)):  # directly, and after resizes
                    self.window.resize(*size)
                    for category in ("value", "gainers"):
                        self.board.set_category(category)
                        end = time.monotonic() + 3
                        while time.monotonic() < end and scroll.horizontalScrollBar().maximum() != 0:
                            self.app.processEvents(); time.sleep(0.01)
                        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0,
                                         self.sideways_report(scroll, language, page, size, category))
                        self.assertLessEqual(self.board.width(), scroll.viewport().width(), (language, page, size))
        self.window.resize(1000, 700); self.view.show_market("us"); self.app.processEvents()
        self.assertTrue(self.board.refresh_button.isVisible())
        right = self.board.refresh_button.mapTo(scroll.viewport(), self.board.refresh_button.rect().topRight()).x()
        self.assertLessEqual(right, scroll.viewport().width())  # Refresh is on screen, not behind a scrollbar

    def test_rows_use_the_width_for_the_figures_and_headings_rank(self):
        # Review: ~616 px of empty row between the names and the numbers at 1440 px (KIS has no sparkline).
        self.load()
        row = self.shown_rows()[0]
        self.assertEqual([key for key, _w in row.plan], ["sector", "price", "change", "value", "volume", "cap"])
        self.assertEqual((row.sector.text(), row.figures["volume"].text(), row.figures["cap"].text()),
                         ("반도체", "310만주", "380.0조"))
        self.assertTrue(row.figures["value"].property("ranked"))
        self.assertTrue(self.board.column_header.cells["value"].property("ranked"))

        def ink(cell, text):
            x = cell.mapTo(row, cell.rect().topLeft()).x()
            width = cell.fontMetrics().horizontalAdvance(text)
            right = bool(cell.alignment() & Qt.AlignmentFlag.AlignRight)
            return (x + cell.width() - width, x + cell.width()) if right else (x, x + width)
        for row in self.shown_rows():
            name = max(row.name.fontMetrics().horizontalAdvance(row.name.full),
                       row.code.fontMetrics().horizontalAdvance(row.code.full))
            spans = [(row.name.mapTo(row, row.name.rect().topLeft()).x(),) * 2]
            spans[0] = (spans[0][0], spans[0][0] + name)
            spans += [ink(row.cells[key], row.cells[key].text()) for key, _w in row.plan]
            gaps = [b[0] - a[1] for a, b in zip(spans, spans[1:])]
            self.assertLess(max(gaps), 200, (row.name.full, gaps))
        # A heading ranks by its column, as its chip does.
        QTest.mouseClick(self.board.column_header.cells["cap"], Qt.MouseButton.LeftButton)
        self.assertEqual((self.board.category, self.names()[0]), ("cap", "삼성전자"))
        QTest.mouseClick(self.board.column_header.cells["change"], Qt.MouseButton.LeftButton)
        self.assertEqual(self.board.category, "gainers")
        QTest.mouseClick(self.board.column_header.cells["change"], Qt.MouseButton.LeftButton)
        self.assertEqual(self.board.category, "losers")
        # The daily path: the sparkline follows the name, not the price.
        self.board.batches["kr"] = daily_kr(); self.board.set_category("value")
        row = self.shown_rows()[0]
        keys = [key for key, _w in row.plan]
        self.assertEqual(keys[:3], ["spark", "sector", "price"])
        self.assertNotIn("cap", keys)  # no figure on that path: no empty column either
        self.assertEqual(self.loader.calls, ["kr"])

    def test_the_checked_chip_and_a_row_show_keyboard_focus(self):
        from core.theme import DARK, LIGHT
        self.load()
        self.window.activateWindow(); self.app.processEvents()
        chip = self.board.category_buttons["value"]
        for theme in (0, 1):
            self.window.theme.setCurrentIndex(theme); self.app.processEvents()
            palette = DARK if theme else LIGHT
            self.board.refresh_button.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
            plain = accent_pixels(chip, palette.on_accent)
            QTest.keyClick(self.board.refresh_button, Qt.Key.Key_Tab); self.app.processEvents()
            self.assertIs(self.app.focusWidget(), chip)  # the checked chip is the criteria row's Tab stop
            self.assertGreater(accent_pixels(chip, palette.on_accent), plain + chip.width(), theme)  # its ring shows
            row = self.shown_rows()[0]
            self.board.search.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
            plain = accent_pixels(row, palette.accent)
            row.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
            self.assertGreater(accent_pixels(row, palette.accent), plain + row.width(), theme)  # a ring, not the fill
        self.window.theme.setCurrentIndex(0)

    def test_no_bong_on_the_daily_path(self):
        # Owner rule R-D9-2 ("한국어 화면 어디에도 '봉' 없음"); the review found '일봉' and '마지막 봉' on this page.
        self.board.loader = FakeLoader({"kr": daily_kr(), "us": us_batch(), "crypto": crypto_batch()})
        for page in ("kr", "us", "crypto"):
            self.view.show_market(page); self.load()
            texts = [self.board.badge.toolTip(), self.board.footnote.text(), self.board.footnote.toolTip()]
            for widget in [*self.board.findChildren(QLabel), *self.board.findChildren(QPushButton),
                           *self.board.sticky.findChildren(QLabel), *self.board.sticky.findChildren(QPushButton)]:
                texts += [widget.text(), widget.toolTip(), widget.accessibleName(), widget.accessibleDescription()]
            self.assertFalse([t for t in texts if "봉" in t], page)
        self.view.show_market("kr")
        self.assertIn("지연·일별: 마지막 날 종가 기준", self.board.footnote.text())
        self.assertEqual(self.board.badge.toolTip(), "Yahoo Finance 일별 값 · 마지막 2026-11-10 · 거래대금은 종가×거래량 추정")

    def test_criteria_ranking_left_filters_together_right_and_one_clear_action(self):
        self.load()
        chips = [b for b in self.board.category_buttons.values() if b.isVisible()]
        segment, sector, toggle = self.board.segments["kr"], self.board.sector_box, self.board.conditions_button
        x = lambda w: w.mapTo(self.board, w.rect().topLeft()).x()
        right = lambda w: x(w) + w.width()
        self.assertLess(right(chips[-1]), x(segment))
        self.assertLess(x(segment), x(sector)); self.assertLess(x(sector), x(toggle))
        self.assertLess(x(sector) - right(segment), 24); self.assertLess(x(toggle) - right(sector), 24)
        self.assertLessEqual(self.board.width() - right(toggle), 2)  # the filters end at the right edge, together
        # 업종, sub-market, search and conditions are chips; 모두 지우기 clears them all (the review found 업종 kept).
        self.board.set_sector("semis"); self.board.sub_buttons["kospi"].click()
        self.view.search.setText("삼성"); self.board.set_limit("value", 1e11)
        shown = lambda: [c.property("filterKey") for c in self.board.filter_chips if c.isVisible()]
        self.assertEqual(shown(), ["text", "sub", "sector", "value"])
        self.assertTrue(self.board.clear_button.isVisible())
        self.board.set_conditions_open(True); self.app.processEvents()
        self.assertEqual(shown(), ["text", "sub", "sector"])  # the open panel shows the condition itself
        self.assertEqual((self.board.clear_button.isVisible(), self.board.conditions_clear.isVisible()), (False, True))
        self.board.set_conditions_open(False); self.app.processEvents()
        self.assertFalse(self.board.conditions_clear.isVisible())
        self.board.clear_button.click(); self.app.processEvents()
        screen = self.board.screen
        self.assertEqual((screen.text, screen.sub, screen.sector, screen.limits), ("", "", "", ()))
        self.assertEqual((self.board.sector_box.currentData(), self.board.sub_buttons[""].isChecked()), ("", True))
        self.assertEqual(shown(), [])

    def test_search_clear_mark_follows_the_text(self):
        # Review: blockSignals left the ⊗ on an empty field after chip ×, 모두 지우기 or a market switch. Qt fades
        # the mark in or out, so each check waits for the fade (a mark left behind never fades and fails).
        self.load()
        search = self.view.search
        shown, gone = (lambda: clear_mark_shown(search)), (lambda: not clear_mark_shown(search))
        search.setText("삼성"); self.wait(shown)
        next(c for c in self.board.filter_chips if c.isVisible()).click()
        self.assertEqual(search.text(), ""); self.wait(gone)
        search.setText("삼성"); self.board.set_limit("value", 1e11); self.wait(shown)
        self.board.clear_button.click(); self.wait(gone)
        search.setText("삼성"); self.wait(shown)
        self.view.show_market("us")
        self.assertEqual(search.text(), ""); self.wait(gone)
        self.view.show_market("kr")
        self.assertEqual(search.text(), "삼성"); self.wait(shown)

    def test_an_inverted_range_is_kept_while_typed_and_cleared_with_its_condition(self):
        from core.theme import LIGHT
        from quantgen_desktop.typography import TONE_COLORS
        self.load()
        self.board.set_conditions_open(True)
        low, high = self.board.condition_controls["change"]
        low.setFocus(); QTest.keyClicks(low, "5"); high.setFocus(); QTest.keyClicks(high, "-1")
        self.assertEqual((low.property("invalid"), high.property("invalid")), (True, True))
        self.assertTrue(self.board.condition_error.isVisible())  # said on a line of its own, not a tooltip alone
        self.assertEqual(self.board.condition_error.text(), "최소가 최대보다 큽니다. 두 값을 맞추면 적용합니다.")
        self.board.category_buttons["gainers"].click(); self.app.processEvents()
        self.assertEqual((low.text(), high.text(), high.property("invalid")), ("5", "-1", True))  # still typed
        for clear in (lambda: self.board.conditions_clear.click(), lambda: self.board.clear_button.click(),
                      lambda: self.view.show_market("us")):
            self.view.show_market("kr"); self.board.set_conditions_open(True)
            self.board.set_limit("change", 1, None)
            low.setFocus(); low.clear(); QTest.keyClicks(low, "5"); high.setFocus(); QTest.keyClicks(high, "-1")
            self.assertTrue(high.property("invalid"))
            clear(); self.app.processEvents()
            self.assertEqual((low.property("invalid"), high.property("invalid"), high.toolTip()), (False, False, ""))
            self.assertFalse(self.board.condition_error.isVisible())
        self.view.show_market("kr")
        self.assertEqual((low.text(), high.text()), ("5", ""))  # the valid bound typed stays; the inverted one went
        sheet = board_stylesheet(LIGHT, False)
        rule = re.search(r"QLineEdit#condEdit\[invalid='true'\] \{([^}]*)\}", sheet).group(1)
        self.assertIn(LIGHT.error, rule); self.assertNotIn(TONE_COLORS[False]["up"], rule)  # not the rise red
        focus = re.search(r"QLineEdit#condEdit\[invalid='true'\]:focus \{([^}]*)\}", sheet).group(1)
        self.assertIn(f"border: 2px solid {LIGHT.accent}", focus)  # focus still shows on an invalid field

    def test_coin_page_has_no_dead_controls_and_says_coin(self):
        self.view.show_market("crypto"); self.load()
        self.assertEqual([k for k, b in self.board.category_buttons.items() if b.isVisible()],
                         ["value", "gainers", "losers"])
        row = self.shown_rows()[0]
        self.assertEqual((row.focusPolicy(), row.property("openable")), (Qt.FocusPolicy.NoFocus, False))
        self.assertIn("QFrame#rankRow[openable='false']:hover { background: transparent; }",
                      " ".join(self.board.styleSheet().split()))
        self.assertNotIn("시가총액", self.board.conditions_button.toolTip())
        self.assertEqual(self.board.conditions_button.toolTip(), "등락률, 거래대금으로 목록을 좁힙니다.")
        self.assertEqual(self.board.search.placeholderText(), "크립토 찾기 · 이름이나 티커(BTC)")
        self.view.search.setText("반도체"); self.app.processEvents()
        self.assertEqual(self.board.empty.text(), "이 목록에는 ‘반도체’에 맞는 가상자산이 없습니다.")
        self.view.search.setText("이더"); self.app.processEvents()
        self.assertEqual(self.board.count.text(), "자산 1개")
        self.view.show_market("us"); self.app.processEvents()
        self.assertEqual(self.board.conditions_button.toolTip(), "등락률, 거래대금, 시가총액으로 목록을 좁힙니다.")

    def test_pinned_bar_keeps_market_ranking_search_and_headings_on_screen(self):
        self.board.loader = FakeLoader({"kr": every_domestic(), "us": us_batch(), "crypto": crypto_batch()})
        self.window.resize(1000, 700); self.load()
        scroll = self.window.stack.widget(self.window.route_indices["markets"])
        bar = self.board.sticky
        self.assertIs(bar.parentWidget(), scroll.viewport())
        self.assertFalse(bar.isVisible())
        scroll.verticalScrollBar().setValue(900); self.settle()
        self.assertTrue(bar.isVisible())
        self.assertEqual((bar.name.text(), bar.rank_button.text()), ("국내 주식", "거래대금 순"))
        self.assertEqual(bar.mapTo(scroll.viewport(), bar.rect().topLeft()).y(), 0)
        self.assertEqual([k for k, _w in bar.header.plan], [k for k, _w in self.board.column_header.plan])
        cells = lambda header: [header.cells[k].mapTo(self.board.window(), header.cells[k].rect().topLeft()).x()
                                for k, _w in header.plan]
        self.assertEqual(cells(bar.header), cells(self.board.column_header))  # the same columns as the rows
        QTest.mouseClick(bar.header.cells["volume"], Qt.MouseButton.LeftButton)
        self.assertEqual(self.board.category, "volume")
        bar.search.setText("현대차"); self.app.processEvents()
        self.assertEqual((self.view.search.text(), self.names()), ("현대차", ["현대차"]))
        scroll.verticalScrollBar().setValue(0); self.settle()
        self.assertFalse(bar.isVisible())
        self.view.search.setText(""); self.app.processEvents()
        scroll.verticalScrollBar().setValue(900); self.settle()
        opened = []
        self.view.stock.show_instrument = lambda instrument, load=True: opened.append(instrument.code)
        bar.search.setText("005380"); bar.search.returnPressed.emit()
        self.assertEqual(opened, ["005380"])  # Enter in the pinned search does what the header search does
        self.assertFalse(bar.isVisible())  # the stock screen hides the list and its bar

    def test_other_market_pointer_and_us_letter_marks(self):
        self.load()
        self.view.search.setText("테슬라"); self.app.processEvents()
        pointers = [b for b in self.board.market_buttons if b.isVisible()]
        self.assertEqual([b.text() for b in pointers], ["미국 주식에서 보기: 테슬라 TSLA"])
        pointers[0].click(); self.app.processEvents()
        self.assertEqual((self.board.page, self.view.search.text()), ("us", "테슬라"))
        self.view.show_market("kr"); self.view.search.setText("비트"); self.app.processEvents()
        self.assertEqual([b.text() for b in self.board.market_buttons if b.isVisible()],
                         ["크립토에서 보기: 비트코인 BTC 외 1개"])
        self.view.search.setText("삼성"); self.app.processEvents()
        self.assertFalse(any(b.isVisible() for b in self.board.market_buttons))  # this market has it
        # US letter marks come from the ticker (the review found 마이, 마스 and two 'AC').
        self.board.loader = FakeLoader({"us": every_us()})
        self.view.show_market("us"); self.view.search.setText(""); self.load()
        marks = {row.code.full.split(" ")[0]: row.mark.spec.letters for row in self.shown_rows()}
        self.assertEqual((marks["AAPL"], marks["MSFT"], marks["AMZN"], marks["GOOGL"]), ("AP", "MS", "AM", "GO"))
        self.window.set_language("en"); self.app.processEvents()
        marks = {row.code.full.split(" ")[0]: row.mark.spec.letters for row in self.shown_rows()}
        self.assertNotEqual(marks["AMZN"], marks["GOOGL"])


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

    def test_rounds_are_timed_from_their_start_and_a_slow_round_reads_delayed(self):
        # Reviewer 2026-11-11: a batch's fetched_at is stamped after the round's last request (81 domestic
        # requests take at least 9.6 s at the KIS client's 0.12 s spacing). Timed from it, each stock was asked
        # every 55 s or more while the state said "every 45 s"; rounds are now timed from their start.
        clock, took = Clock(), [12]

        def timed(group, members, cancelled=None, progress=None):
            clock.now += timedelta(seconds=took[0])
            return kr_batch(clock.now)  # stamped at the end of the round, as kis_batch does
        board = RankingBoard(loader=timed, locale=LocaleContext("ko_KR"), auto_load=False, clock=clock,
                             open_fn=lambda group, now: True)
        self.addCleanup(board.deleteLater)
        board.show()
        self.assertTrue(board.refresh(manual=True))
        self.wait(lambda: not board.jobs.busy and "kr" in board.batches)
        self.app.processEvents()
        self.assertEqual(board.batches["kr"].fetched_at, (NOW + timedelta(seconds=12)).isoformat())
        clock.now = NOW + timedelta(seconds=LIVE_REFRESH_SECONDS - 1)
        self.assertFalse(board.due())
        clock.now = NOW + timedelta(seconds=LIVE_REFRESH_SECONDS)
        self.assertTrue(board.due())  # 45 s after the round started, not 45 s after it ended (57 s)
        board._render_status()
        self.assertEqual((board.state(), board.badge.text()), ("polled", "KIS 조회 · 45초마다"))
        self.assertNotIn("회차", board.badge.toolTip())
        # A round longer than the interval: the next one is due at once and the state stops saying "every 45 s".
        took[0], first = LIVE_REFRESH_SECONDS + 5, board.batches["kr"]
        self.assertTrue(board.refresh())
        self.wait(lambda: not board.jobs.busy and board.batches["kr"] is not first)
        self.app.processEvents()
        self.assertTrue(board.due())
        board._render_status()
        self.assertEqual((board.state(), board.badge.text()), ("stale", "KIS · 갱신 지연"))
        self.assertIn("마지막 조회 한 회차가 50초 걸려 45초보다 길었으므로 종목마다 그보다 드물게 조회했습니다.",
                      board.badge.toolTip())
        board.set_locale(LocaleContext("en_US")); board._render_status()
        self.assertIn("The last round of requests took 50 s, longer than 45 s, so each stock was asked less often "
                      "than that.", board.badge.toolTip())
        # A batch set from outside, with no round recorded, is timed from its fetched_at as before.
        board.batches["kr"] = kr_batch(clock.now)
        self.assertFalse(board.due())
        self.assertEqual(board.state(), "polled")

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
    def __init__(self, ready=True, fail=(), no_detail=()):
        self.ready, self.fail, self.no_detail, self.calls = ready, set(fail), set(no_detail), []

    def _get(self, path, tr_id, params):
        config_paths = config.KIS_QUOTATION_ALLOWLIST
        assert path in config_paths, path
        self.calls.append((path, tr_id, dict(params)))
        code = params.get("FID_INPUT_ISCD") or params.get("SYMB")
        if code in self.fail or "*" in self.fail:
            raise RuntimeError("KIS said no")
        if tr_id == "HHDFS76200200":  # overseas price-detail: market cap and listed shares
            if code in self.no_detail:
                raise RuntimeError("no detail")
            return {"output": {"last": "100.5", "tomv": "1507500000000", "shar": "15000000000", "curr": "USD",
                               "perx": "30.10", "pbrx": "40.20"}}
        if tr_id == "FHKST01010100":  # hts_avls (100 million won) agrees with lstn_stcn x stck_prpr
            return {"output": {"stck_prpr": "70000", "prdy_vrss": "700", "prdy_vrss_sign": "2", "prdy_ctrt": "1.01",
                               "acml_vol": "1000", "acml_tr_pbmn": "70000000", "hts_avls": "4200",
                               "lstn_stcn": "6000000"}}
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

    def test_etf_lists_take_the_stocks_allowlisted_kis_quotes_or_yahoo_daily_and_no_market_cap(self):
        service = FakeService()
        kr = kis_batch(service, "etf_kr", R.ETF_KR[:2], sleep=lambda s: None)
        us = kis_batch(service, "etf_us", R.ETF_US[:2], sleep=lambda s: None)
        self.assertEqual([(c[1], c[2]) for c in service.calls],
                         [("FHKST01010100", {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "069500"}),
                          ("FHKST01010100", {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "102110"}),
                          ("HHDFS00000300", {"AUTH": "", "EXCD": "AMS", "SYMB": "SPY"}),
                          ("HHDFS00000300", {"AUTH": "", "EXCD": "NAS", "SYMB": "QQQ"})])
        self.assertTrue(all(path in config.KIS_QUOTATION_ALLOWLIST for path, _tr, _p in service.calls))
        self.assertEqual(([r.member.code for r in kr.records], kr.group), (["069500", "102110"], "etf_kr"))
        self.assertEqual((us.group, us.mode), ("etf_us", "kis"))
        # The production loader: no price-detail (market cap) request and no market-cap source for ETFs.
        caps = Mock(side_effect=AssertionError("ETFs have no market cap"))
        live = FakeService()
        batch = ProductionRankingLoader(service_factory=lambda: live, caps=caps)("etf_us", R.ETF_US[:3])
        self.assertEqual([c[1] for c in live.calls], ["HHDFS00000300"] * 3)
        caps.assert_not_called()
        self.assertEqual(R.source_state(batch, open_now=True), "polled_us")
        asked = []

        def frame(symbol, interval, period):
            asked.append(symbol)
            return [("2026-11-09", 1, 1, 1, 100.0, 10.0), ("2026-11-10", 1, 1, 1, 101.0, 20.0)]
        with patch("core.market.routing._yahoo_frame", side_effect=frame):
            idle = ProductionRankingLoader(service_factory=lambda: FakeService(ready=False), caps=caps)
            daily_kr = idle("etf_kr", R.ETF_KR[:3])
            daily_us = idle("etf_us", R.ETF_US[:2])
        self.assertEqual(sorted(asked), ["069500.KS", "102110.KS", "122630.KS", "QQQ", "SPY"])  # KRX ETFs: .KS only
        self.assertEqual((daily_kr.mode, daily_kr.group, len(daily_kr.records)), ("daily", "etf_kr", 3))
        self.assertTrue(all(r.estimated_value for r in daily_us.records))  # close x volume, as for stocks
        caps.assert_not_called()

    def test_kis_price_detail_market_cap_in_the_paced_us_batch(self):
        # Owner approval 2026-11-11 ("승인."): KIS overseas price-detail added to the read-only allowlist.
        self.assertIn("/uapi/overseas-price/v1/quotations/price-detail", config.KIS_QUOTATION_ALLOWLIST)
        members = (member("AAPL"), member("TSM"), member("JPM"))
        service, sleeps, ticks, details, moment = FakeService(no_detail={"JPM"}), [], iter(range(100)), {}, [0.0]
        batch = kis_batch(service, "us", members, sleep=sleeps.append, clock=lambda: next(ticks) * 0.01,
                          per_second=20, details=details, now=lambda: moment[0])
        self.assertEqual([c[1] for c in service.calls],
                         ["HHDFS00000300", "HHDFS76200200", "HHDFS00000300", "HHDFS00000300", "HHDFS76200200"])
        self.assertEqual(service.calls[1][2], {"AUTH": "", "EXCD": "NAS", "SYMB": "AAPL"})
        self.assertEqual(len(sleeps), 4)  # every request, detail included, through the same 20/s pacing
        got = {r.member.code: r for r in batch.records}
        self.assertEqual(set(got), {"AAPL", "TSM", "JPM"})  # a failed detail costs no quote
        self.assertEqual((got["AAPL"].market_cap, got["AAPL"].cap_basis, got["AAPL"].cap_source),
                         (1507500000000.0, "provider", "KIS"))
        self.assertEqual((got["TSM"].market_cap, got["JPM"].market_cap), (None, None))  # ADR not asked; JPM failed
        moment[0] = 299.0
        kis_batch(service, "us", members, sleep=sleeps.append, details=details, now=lambda: moment[0])
        self.assertEqual([c[1] for c in service.calls[5:]], ["HHDFS00000300"] * 3)  # details reused for 5 min
        moment[0] = 301.0
        again = kis_batch(service, "us", members, sleep=sleeps.append, details=details, now=lambda: moment[0])
        self.assertEqual(service.calls[-1][1], "HHDFS76200200")
        self.assertEqual(again.records[0].cap_source, "KIS")
        plain = kis_batch(FakeService(), "us", members[:1], sleep=sleeps.append)  # no details: price only
        self.assertEqual((plain.records[0].market_cap, plain.records[0].cap_basis), (None, ""))

    def test_us_fetch_adds_market_caps_after_the_quotes_and_kr_is_unchanged(self):
        from core.market.market_cap import MarketCapSource, SharesCache
        asked = []

        def shares(symbol):
            asked.append(symbol)
            return 1.5e10, "2026-10-31"
        caps = MarketCapSource(fmp_key=lambda: "", yahoo_fetch=shares, cache=SharesCache(None))
        loader = ProductionRankingLoader(service_factory=lambda: FakeService(ready=True), caps=caps)
        us = loader("us", (member("AAPL"), member("TSM")))
        apple, tsmc = us.records
        self.assertEqual((us.mode, us.caps, us.cap_reasons), ("kis", "ok", ("fmp_no_key",)))
        self.assertEqual((apple.market_cap, apple.cap_basis, apple.cap_source), (1507500000000.0, "provider", "KIS"))
        self.assertEqual((tsmc.market_cap, tsmc.cap_missing), (None, "adr"))
        self.assertEqual(asked, [])  # KIS stated it: Yahoo is not asked
        no_detail = ProductionRankingLoader(service_factory=lambda: FakeService(ready=True, no_detail={"AAPL"}),
                                            caps=caps)("us", (member("AAPL"),))
        self.assertEqual((no_detail.records[0].market_cap, no_detail.records[0].cap_basis, no_detail.cap_reasons),
                         (1.5e10 * 100.5, "computed", ("kis_none", "fmp_no_key")))  # Yahoo shares x KIS last
        self.assertEqual(asked, ["AAPL"])
        kr = loader("kr", R.DOMESTIC[:2])
        # Domestic caps come checked from the same KIS answer (hts_avls against lstn_stcn x stck_prpr); the US
        # market-cap step (FMP, Yahoo) is never asked for them.
        self.assertEqual((kr.caps, [r.cap_basis for r in kr.records], asked), ("", ["provider", "provider"], ["AAPL"]))
        self.assertEqual([c[1] for c in loader.service().calls[3:]], ["FHKST01010100"] * 2)  # domestic: no detail
        self.assertEqual(loader("us", (member("AAPL"),), cancelled=lambda: True).caps, "")  # stopped: not sought
        broken = ProductionRankingLoader(service_factory=lambda: FakeService(ready=True),
                                         caps=Mock(side_effect=RuntimeError("provider text")))
        kept = broken("us", (member("AAPL"),))
        self.assertEqual((len(kept.records), kept.caps), (1, "none"))  # a market-cap failure keeps the quotes

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
        self.assertIsNone(loader._caps)     # and so is the US market-cap step
        self.assertEqual(window.markets_view.rankings.batches, {})
        self.assertFalse(window.markets_view.rankings.jobs.busy)
        window.hide()


if __name__ == "__main__":
    unittest.main()
