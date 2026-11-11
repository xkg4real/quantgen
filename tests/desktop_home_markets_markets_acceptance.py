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
        self.assertEqual(self.board.badge.text(), "KIS 조회 · 45초마다")  # REST polling, never "실시간"
        self.assertEqual(self.board.heading.text(), "실시간 차트")  # the owner's page name stays
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
        self.assertEqual(self.shown_rows(), [])  # this fixture loader sought no market cap, and says so
        self.assertEqual(self.board.empty.text(), "이 시세에는 시가총액이 없습니다.")
        shown = " ".join(self.page_text())
        self.assertNotIn("Yahoo", shown)
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown), shown)  # dates stay in tooltips

    def test_us_market_cap_ranks_the_figures_found_and_says_where_they_came_from(self):
        # Owner 2026-11-11: "아니 미국 시총 자료 찾으세요". The explanation gives way to the list.
        self.board.loader = FakeLoader({"kr": kr_batch(), "us": us_cap_batch()})
        self.board.market_buttons["us"].click(); self.board.category_buttons["cap"].click(); self.load()
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
        self.board.market_buttons["kr"].click(); self.board.category_buttons["cap"].click(); self.load()
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
        self.board.market_buttons["us"].click(); self.app.processEvents()
        self.assertEqual(self.board.badge.text(), "KIS 무료 시세 · 45초마다 조회")
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
        self.assertEqual(self.board.badge.text(), "KIS free US feed · polled every 45 s")
        self.assertIn("polled every 45 s (REST requests, not a trade stream)", self.board.badge.toolTip())
        self.assertIn("can differ from paid consolidated quotes", self.board.badge.toolTip())
        for state in ("polled", "polled_us", "closed", "stale", "daily", "none"):
            self.assertNotIn("실시간", R.text(R.STATES, state, "ko"))
            self.assertNotIn("real-time", R.text(R.STATES, state, "en").lower())

    def test_market_buttons_show_the_windows_focus_ring_without_changing_their_look(self):
        # 2026-11-11 compliance follow-up (14-contrast, 15-keyboard): the list's own [tool='true'] rule set
        # `border` with no :focus rule, and the closer sheet hid the window's 2px focus ring.
        from core.theme import DARK, LIGHT
        for colors, dark in ((LIGHT, False), (DARK, True)):
            rule = re.search(r"QPushButton\[tool='true'\]:focus \{([^}]*)\}", board_stylesheet(colors, dark))
            self.assertIsNotNone(rule)
            self.assertIn(f"border: 2px solid {colors.accent}", rule.group(1))
        self.window.activateWindow(); self.app.processEvents()
        for theme in (0, 1):
            self.window.theme.setCurrentIndex(theme); self.app.processEvents()
            accent = (DARK if theme else LIGHT).accent
            for key in ("kr", "kospi", "kosdaq", "us"):
                button = self.board.market_buttons[key]
                self.board.category_buttons["value"].setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
                plain, size = accent_pixels(button, accent), button.size()
                if not button.isChecked():
                    self.assertEqual(plain, 0, key)  # unfocused: no ring (the checked one keeps its underline)
                button.setFocus(Qt.FocusReason.TabFocusReason); self.app.processEvents()
                self.assertTrue(button.hasFocus(), key)
                self.assertGreater(accent_pixels(button, accent), plain + 2 * (size.width() + size.height()), key)
                self.assertEqual(button.size(), size, key)  # the ring does not resize or move the button
        self.window.theme.setCurrentIndex(0); self.app.processEvents()

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

    def test_us_market_cap_says_why_when_none_could_be_read(self):
        base = us_batch()
        none = replace(base, records=tuple(R.without_cap(r, "error") for r in base.records), caps="none",
                       cap_reasons=("kis_off", "fmp_no_key", "yahoo_unreachable"))
        self.board.loader = FakeLoader({"us": none})
        self.board.market_buttons["us"].click(); self.board.category_buttons["cap"].click(); self.load()
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
        self.assertEqual(self.loader.calls, ["kr"])

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
