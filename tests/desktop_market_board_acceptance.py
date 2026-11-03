"""Native Markets indicator board (owner UI-7): four charts replace the table, no stocks."""
import datetime
import math
import os
import time
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication, QTableWidget
from core.research.market_board import build_routers


def series(n=90):
    end = datetime.date.today()
    return ([(end - datetime.timedelta(days=n - 1 - i)).isoformat() for i in range(n)],
            [2500 * (1 + 0.02 * math.sin(i / 7)) for i in range(n)])


class MarketBoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)
        self.provider = Mock(side_effect=AssertionError('Provider forbidden'))
        self.window = ResearchWindow(auto_refresh=False, locale='ko_KR', market_loader=self.provider,
                                     connections_runner=self.provider)
        self.window.resize(1360, 940); self.window.show(); self.window.navigate('markets'); self.app.processEvents()
        self.addCleanup(self.window.deleteLater); self.addCleanup(self.window.hide)
        self.calls = []

        def fetch(name):
            def run(argument):
                self.calls.append(name); return series()
            return run
        self.board = self.window.market_board
        self.board._routers = build_routers(fetchers={'kis_ready': lambda: (True, ()), 'kis_index': fetch('kis'),
                                                      'kis_chart': fetch('kis'), 'kis_fx': fetch('kis'),
                                                      'yfinance': fetch('yahoo'), 'fred': fetch('fred')})

    def wait(self, predicate):
        end = time.monotonic() + 8
        while time.monotonic() < end and not predicate():
            self.app.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())

    def load(self):
        self.board.refresh(manual=True)
        self.wait(lambda: not self.board.jobs.busy and all(c.result for c in self.board.cards.values()))

    def test_the_table_is_gone_and_construction_loads_nothing(self):
        w = self.window
        self.assertFalse(hasattr(w, 'market_table'))
        self.assertIn('표시 권리', self.board.rights.text())  # the rights/vintage caveat stays visible
        page = w.stack.currentWidget().widget()
        tables = [t for t in page.findChildren(QTableWidget) if t.isVisible() and t.isAncestorOf(w.market_board)]
        self.assertEqual(tables, [])
        self.assertEqual(len(self.board.cards), 4)
        self.assertEqual(self.calls, []); self.assertFalse(self.board.poll_timer.isActive())
        self.provider.assert_not_called()

    def test_cards_show_value_change_chart_and_two_equal_lines_without_stocks(self):
        self.load()
        self.assertEqual(set(self.calls), {'kis', 'fred'})
        for key, card in self.board.cards.items():
            self.assertNotEqual(card.value.text(), '—', key)
            self.assertTrue(card.chart.renderer().isValid(), key)
            self.assertTrue(card.source_line.text().startswith('출처: '), key)
            self.assertIn('한국시간', card.time_line.text())
            self.assertEqual(card.source_line.font().pointSizeF(), card.time_line.font().pointSizeF())
            for stock in ('삼성전자', 'SK하이닉스', '005930', '000660'):
                self.assertNotIn(stock, card.title.text() + card.source_line.text())
        self.assertFalse(self.window.jobs.busy)
        self.assertTrue(self.window.rates.input_box.isEnabled())  # the board never disables tools

    def test_failure_is_per_card_and_keeps_the_last_good_value(self):
        self.load()
        before = self.board.cards['kospi'].value.text()

        def broken(argument):
            raise RuntimeError('https://secret.example/?key=1')
        self.board._routers = build_routers(fetchers={'kis_ready': lambda: (False, ('KIS_APP_KEY',)),
                                                      'yfinance': broken, 'fred': broken})
        self.load()
        card = self.board.cards['kospi']
        self.assertEqual(card.value.text(), before)
        self.assertIn('갱신 실패', card.time_line.text())  # the failure is visible, the old value labelled
        self.assertNotIn('secret', card.time_line.text() + card.chart.toolTip())
        # Failed cards back off instead of being asked again on every 15-second tick.
        self.assertNotIn('kospi', self.board.due_keys())
        import datetime as dt
        later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=card.failures and 61)
        self.assertIn('kospi', self.board.due_keys(later))
        fresh = type(self.board)(routers=self.board._routers, auto_load=False)
        self.addCleanup(fresh.deleteLater)
        fresh.refresh(manual=True)
        self.wait(lambda: not fresh.jobs.busy and all(c.result for c in fresh.cards.values()))
        line = fresh.cards['kospi'].source_line.text()
        self.assertIn('조회 실패', line); self.assertIn('KIS_APP_KEY', line); self.assertNotIn('secret', line)

    def test_layout_language_theme_and_polling_follow_visibility(self):
        self.load()
        w = self.window
        positions = {self.board.grid.getItemPosition(self.board.grid.indexOf(c))[:2] for c in self.board.cards.values()}
        self.assertEqual(positions, {(0, 0), (0, 1), (1, 0), (1, 1)})
        narrow = type(self.board)(routers=self.board._routers, auto_load=False)
        self.addCleanup(narrow.deleteLater)
        narrow.resize(600, 1200); narrow.show(); self.app.processEvents()
        columns = {narrow.grid.getItemPosition(narrow.grid.indexOf(c))[1] for c in narrow.cards.values()}
        self.assertEqual(columns, {0})  # one column below 700 px
        narrow.hide()
        w.resize(1000, 700); self.app.processEvents()
        viewport = w.stack.currentWidget().viewport().width()
        self.assertLessEqual(self.board.width(), viewport)  # the minimum window keeps the board inside the page
        calls = len(self.calls)
        w.set_language('en'); w.change_theme(1); self.app.processEvents()
        self.assertEqual(self.board.cards['kospi'].title.text(), 'KOSPI')
        self.assertTrue(self.board.cards['ust10y'].change.text().endswith('bp'))
        self.assertEqual(len(self.calls), calls)  # language and theme re-render without reloading
        self.board.auto_load = True
        self.board.hide(); self.board.show(); self.app.processEvents()
        self.assertTrue(self.board.poll_timer.isActive())
        w.navigate('home'); self.app.processEvents()
        self.assertFalse(self.board.poll_timer.isActive())


if __name__ == '__main__':
    unittest.main()
