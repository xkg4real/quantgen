"""No credentials or network: price-scenario arithmetic, real chart gestures and stock-view integration."""
import math
import os
import unittest
from dataclasses import replace
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from core.i18n import LocaleContext
from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot
from core.market.risk_reward import RiskRewardPlan
from core.theme import LIGHT, DARK
from quantgen_desktop.market_chart import MarketChartSvg
from quantgen_desktop.risk_reward import RiskRewardTool
from tests.qt_fixture_cleanup import delete_owned_widget

APP = QApplication.instance() or QApplication([])


class PriceScenarioTests(unittest.TestCase):
    def test_known_long_and_short_payoffs(self):
        for p in (RiskRewardPlan("long", 100, 95, 115), RiskRewardPlan("short", 100, 105, 85)):
            self.assertEqual(p.metrics, dict(risk=5, reward=15, ratio=3, risk_pct=5, reward_pct=15))

    def test_no_ratio_for_zero_risk_wrong_direction_or_nonfinite_prices(self):
        for p in (RiskRewardPlan("long", 100, 100, 110), RiskRewardPlan("short", 100, 95, 110),
                  RiskRewardPlan("long", 0, -1, 1), RiskRewardPlan("invalid", 100, 95, 110)):
            self.assertIsNone(p.metrics)
        for value in (math.nan, math.inf, -math.inf):
            for key in ("entry", "stop", "target"):
                self.assertIsNone(replace(RiskRewardPlan("long", 100, 95, 110), **{key: value}).metrics)

    def test_entry_translation_preserves_distances(self):
        p = RiskRewardPlan("long", 100, 95, 115).moved("entry", 110)
        self.assertEqual((p.entry, p.stop, p.target, p.metrics["ratio"]), (110, 105, 125, 3))


class ChartScenarioTests(unittest.TestCase):
    def setUp(self):
        self.view = QWidget()
        self.view.ctx, self.view.palette = LocaleContext("ko_KR"), LIGHT
        self.view.instrument = Instrument()
        self.view.risk_button, self.view.more_risk = QPushButton(self.view), QAction(self.view)
        self.view.price_text = lambda value: self.view.ctx.number(value, 0)
        self.chart = MarketChartSvg(self.view)
        self.view.chart = SimpleNamespace(chart=self.chart)
        self.tool = RiskRewardTool(self.view)
        layout = QVBoxLayout(self.view)
        layout.addWidget(self.chart)
        self.view.resize(900, 600)
        self.chart.set_detail(True)
        self.view.show()
        self.snapshot = MarketSnapshot(ChartRequest(), tuple(
            Candle(f"2026-10-{i+1:02d}", 100 + i, 102 + i, 99 + i, 101 + i, 1000) for i in range(25)))
        self.chart.set_snapshot(self.snapshot, visible_bars=20, indicators=(), language="ko")
        self.tool.open()
        self.tool.set_plan(RiskRewardPlan("long", 110, 105, 125), fit=True)
        APP.processEvents()
        self.addCleanup(delete_owned_widget, self.view)
        self.addCleanup(delete_owned_widget, self.tool.panel)

    def drag(self, key, price):
        layout = self.chart.layout_info
        x = self.tool.region().center().x()
        start = QPoint(round(x), round(layout.y_of_price(getattr(self.tool.plan, key))))
        end = QPoint(round(x), round(layout.y_of_price(price)))
        QTest.mousePress(self.chart, Qt.MouseButton.LeftButton, pos=start)
        move = QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(end), QPointF(self.chart.mapToGlobal(end)),
                           Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        APP.sendEvent(self.chart, move)
        QTest.mouseRelease(self.chart, Qt.MouseButton.LeftButton, pos=end)
        APP.processEvents()

    def test_drag_updates_real_price_and_ratio_without_panning(self):
        before = self.chart.window()
        self.drag("stop", 100)
        self.assertEqual(self.chart.window(), before)
        self.assertAlmostEqual(self.tool.plan.stop, 100, delta=1)
        self.assertAlmostEqual(self.tool.plan.metrics["ratio"], 1.5, delta=.2)
        before = self.tool.plan
        self.drag("entry", before.entry + 2)
        self.assertEqual(self.tool.plan.target - self.tool.plan.entry, before.target - before.entry)
        self.assertEqual(self.tool.plan.entry - self.tool.plan.stop, before.entry - before.stop)

    def test_price_mapping_roundtrip_and_view_changes_keep_authored_levels(self):
        plan = self.tool.plan
        for width in (440, 1000):
            self.view.resize(width, 650)
            self.chart.dark = True
            self.view.palette = DARK
            self.chart.set_snapshot(replace(self.snapshot, candles=self.snapshot.candles +
                                           (Candle("2026-10-26", 125, 132, 123, 130, 1200),)),
                                    visible_bars=12, indicators=("rsi",), dark=True)
            APP.processEvents()
            mapping = self.chart.layout_info
            for value in (plan.stop, plan.entry, plan.target):
                self.assertAlmostEqual(mapping.price_at(mapping.y_of_price(value)), value)
            self.assertEqual(self.tool.plan, plan)

    def test_direction_invalid_input_clear_and_locale(self):
        self.tool.direction.setCurrentIndex(1)
        self.assertEqual(self.tool.plan, RiskRewardPlan("short", 110, 115, 95))
        self.tool.fields["stop"].setValue(100)
        self.assertIsNone(self.tool.plan.metrics)
        self.assertIn("목표가 < 진입가 < 손절가", self.tool.result.text())
        self.view.ctx = LocaleContext("en_US")
        self.tool.translate()
        self.assertIn("Short: target < entry < stop", self.tool.result.text())
        self.tool.clear()
        self.assertIsNone(self.tool.plan)
        self.assertEqual(self.tool.price_levels, ())

    def test_new_instrument_clears_scenario_and_missing_data_cannot_seed(self):
        self.view.instrument = Instrument(code="000660")
        self.tool.sync()
        self.tool.seed()
        self.assertIsNone(self.tool.plan)
        self.assertFalse(self.tool.reset.isEnabled())
        self.assertFalse(self.tool.active)

    def test_unrepresentable_mirrored_prices_do_not_desynchronise_the_direction(self):
        self.tool.set_plan(RiskRewardPlan("long", 110, 100, 300), fit=True)
        self.tool.direction.setCurrentIndex(1)
        self.assertEqual(self.tool.plan.direction, "short")
        self.assertEqual(self.tool.direction.currentData(), self.tool.plan.direction)
        self.assertIsNone(self.tool.plan.metrics)
        self.assertEqual(self.tool.fields["target"].value(), self.tool.plan.target)


class StockScenarioIntegrationTests(unittest.TestCase):
    def test_toolbar_and_narrow_menu_open_the_docked_tool(self):
        from tests import desktop_stock_detail_acceptance as fixtures
        fixture = fixtures.StockDetailTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        fixture.open(profile=False)
        view = fixture.view
        view.risk_button.click()
        fixture.settle()
        self.assertTrue(view.risk.panel.isVisible())
        self.assertTrue(view.risk.active)
        self.assertEqual(view.side.pages.currentIndex(), 0)
        self.assertIs(view.risk.panel.parentWidget(), view.side.stock_page)
        fixture.window.resize(1000, 700)
        fixture.settle()
        view.risk.panel.hide()
        view.more_risk.trigger()
        self.assertTrue(view.risk.panel.isVisible())
        fixture.window.set_language("en")
        fixture.settle()
        self.assertEqual(view.risk.title.text(), "Risk / reward")
        view.set_studies(("rsi",))
        view._refresh_side(force=True)
        fixture.settle()
        # The fixture ends in an actual falling stretch: the live guide explains persistence,
        # rather than turning its low RSI into a buying instruction.
        card = view._technical_blocks["rsi"][2]
        self.assertIn("Oversold conditions can persist", card.context_note.text())
        self.assertNotRegex(card.context_note.text(), "[가-힣]")


if __name__ == "__main__":
    unittest.main()
