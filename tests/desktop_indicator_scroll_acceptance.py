"""The stock screen's 지표 list holds still while live prices arrive (owner 2026-11-17), offscreen and offline.

Owner, verbatim: "상세차트 지표부분 스크롤 내릴때 불안정합니다. 검토해주세요". Cause found: every live refresh (about every
1.2 s) re-filled every picker row and open guide card; a value whose text length changed ('9.98' -> '10.02') moved its
place chip to line 2 and back, and the guide cards showed then hid their parts, so rows grew and shrank by tens of pixels
(the whole list by about 330 px) under a reader who was scrolling. Now: a row keeps the widest value it has shown on the
chart, refreshes set only what changed, and the row at the top of the view keeps its place if anything above it moves.
"""
import os
import random
import unittest
from dataclasses import replace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QEvent, QObject, QPoint
from PyQt6.QtWidgets import QWidget

from tests import desktop_stock_detail_acceptance as base

APP, SAMSUNG = base.APP, base.SAMSUNG

STUDIES = ("sma", "bb", "rsi", "macd", "stoch", "obv", "adx", "ichimoku")


class _ShowHide(QObject):
    def __init__(self):
        super().__init__()
        self.events = []

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Hide):
            self.events.append((type(watched).__name__, watched.property("sd"), event.type()))
        return False


class IndicatorScrollTests(base.StockDetailTests):
    """Reuses the stock screen fixture (offline providers, KIS chart service, profile loader)."""

    def prepared(self):
        self.open(SAMSUNG)
        picker = self.view.picker
        picker._emit(STUDIES)
        self.settle()
        self.view.side.set_page(1)
        self.settle()
        for row in picker.rows().values():
            if row.key in picker.selected:
                row.open_guide(True)
        self.settle(10)
        return picker

    def tick(self, change):
        snapshot = self.pane.snapshot
        candles = list(snapshot.candles)
        last = candles[-1]
        price = last.close * (1 + change)
        candles[-1] = replace(last, close=price, high=max(last.high, price), low=min(last.low, price))
        self.pane.snapshot = replace(snapshot, candles=tuple(candles))
        self.pane.render()
        self.view._refresh_side()
        self.settle(4)

    def heights(self, picker):
        return {key: row.height() for key, row in picker.rows().items() if row.isVisible()}

    def test_rows_keep_their_height_while_live_prices_change_value_lengths(self):
        picker = self.prepared()
        random.seed(3)
        self.tick(0.01)
        first, total = self.heights(picker), picker.height()
        grown = dict(first)
        for _ in range(8):
            self.tick(random.uniform(-0.03, 0.03))
            now = self.heights(picker)
            for key, height in now.items():
                self.assertGreaterEqual(height, grown[key] - 1, key)   # a row may grow once, never shrink back
                grown[key] = max(grown[key], height)
        settled = self.heights(picker)
        for _ in range(4):
            self.tick(random.uniform(-0.03, 0.03))
            self.assertEqual(self.heights(picker), settled)
        self.assertLessEqual(abs(picker.height() - total), 140)

    def test_a_refresh_with_the_same_data_shows_or_hides_nothing(self):
        picker = self.prepared()
        self.view._refresh_side(); self.settle()
        spy = _ShowHide()
        widgets = picker.findChildren(QWidget)
        for widget in widgets:
            widget.installEventFilter(spy)
        self.view._refresh_side(); self.settle()
        for widget in widgets:
            widget.removeEventFilter(spy)
        self.assertEqual(spy.events, [])

    def test_the_row_at_the_top_of_the_view_keeps_its_place_when_rows_above_it_grow(self):
        picker = self.prepared()
        scroll = self.view.side.indicator_scroll
        bar = scroll.verticalScrollBar()
        bar.setValue(bar.maximum() // 2); self.settle()
        anchor = picker._scroll_anchor()
        self.assertIsNotNone(anchor)
        _scroll, row, y = anchor
        above = [r for r in picker.rows().values() if r.isVisible()
                 and r.mapTo(scroll.viewport(), QPoint(0, 0)).y() + r.height() <= 0]
        self.assertTrue(above)
        above[0].setMinimumHeight(above[0].height() + 90)
        picker._restore_anchor(anchor); self.settle()
        self.assertEqual(row.mapTo(scroll.viewport(), QPoint(0, 0)).y(), y)


# Do not re-run the inherited stock screen tests from this module.
for _name in [n for n in dir(base.StockDetailTests) if n.startswith("test_")]:
    setattr(IndicatorScrollTests, _name, None)


if __name__ == "__main__":
    unittest.main()
