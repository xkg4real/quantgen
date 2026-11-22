"""Actual Qt presentation regressions with fixed, supplied profile dictionaries.

No application window, quote client, model/history engine or provider is created.
Run under the reviewed isolated Qt harness.
"""
from __future__ import annotations

import copy
from types import SimpleNamespace
import unittest


def _profile(*, wide=False):
    raw = {"aspr_acpt_hour": "200000"}
    for level in range(1, 11):
        raw.update({f"askp{level}": str((999999999999 if wide else 1100000) + level),
                    f"bidp{level}": str((999999999999 if wide else 1099000) - level),
                    f"askp_rsqn{level}": "1016", f"bidp_rsqn{level}": "987"})
    return SimpleNamespace(
        values={"key_figures": {"per": 13.2, "pbr": 1.1},
                "orderbook": {"output1": raw}, "flows": {},
                "short_selling": {"latest": {"date": "2026-11-20", "short_ratio_pct": 4.31,
                                               "short_qty": 142859},
                                  "average": {"sessions": 20, "short_ratio_pct": 3.1,
                                              "reported_ratio": 20}}},
        reasons={}, sources={"quote": "FIXED_SYNTHETIC_UI_ONLY"},
        fetched={"quote": "2026-11-21T14:00:00+00:00"})


class StockInsightsStyleAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def _settle(self):
        for _ in range(4):
            self.app.processEvents()

    def test_dynamic_labels_match_existing_stock_detail_type_and_palette(self):
        from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
        from core.theme import DARK, LIGHT
        from quantgen_desktop.stock_detail_style import label, numbers, sheet
        from quantgen_desktop.stock_insights import StockInsightsPanel

        panel, reference = StockInsightsPanel(), QWidget()
        reference_layout = QVBoxLayout(reference)
        profile = _profile()
        original = copy.deepcopy(profile.__dict__)
        try:
            panel.resize(330, 1400)
            panel.show()
            reference.show()
            for language, dark in (("ko", False), ("en", True), ("ko", False)):
                with self.subTest(language=language, dark=dark):
                    palette = DARK if dark else LIGHT
                    reference.setStyleSheet(sheet(palette, dark))
                    panel.set_profile(profile, language=language, dark=dark)
                    self._settle()
                    for role, sd in (("title", "cardTitle"), ("", "body"),
                                     ("muted", "rowNote"), ("value", "rowValue")):
                        expected = label(sd)
                        if role == "value":
                            numbers(expected)
                        expected.setText("PER · 1,100,000")
                        reference_layout.addWidget(expected)
                        expected.ensurePolished()
                        actual = [w for w in panel.findChildren(QLabel)
                                  if w.property("insightRole") == role]
                        self.assertTrue(actual, role)
                        for widget in actual:
                            widget.ensurePolished()
                            self.assertEqual(widget.font().families(), expected.font().families())
                            self.assertEqual(widget.font().pixelSize(), expected.font().pixelSize())
                            self.assertEqual(widget.font().weight(), expected.font().weight())
                            self.assertEqual(widget.font().letterSpacing(), expected.font().letterSpacing())
                            self.assertEqual(widget.palette().color(widget.foregroundRole()),
                                             expected.palette().color(expected.foregroundRole()))
                        reference_layout.removeWidget(expected)
                        expected.deleteLater()
            self.assertEqual(profile.__dict__, original)
        finally:
            panel.close()
            reference.close()
            panel.deleteLater()
            reference.deleteLater()
            self._settle()

    def test_disclosure_uses_existing_link_font_and_keyboard_without_native_box(self):
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QPushButton, QToolButton, QVBoxLayout, QWidget
        from core.theme import LIGHT
        from quantgen_desktop.stock_detail_style import sheet
        from quantgen_desktop.stock_insights import StockInsightsPanel

        panel, reference = StockInsightsPanel(), QWidget()
        expected = QPushButton("기존 더 보기", reference)
        expected.setProperty("sd", "link")
        QVBoxLayout(reference).addWidget(expected)
        reference.setStyleSheet(sheet(LIGHT, False))
        try:
            panel.set_profile(_profile())
            panel.show()
            reference.show()
            self._settle()
            self.assertEqual(panel.findChildren(QToolButton), [])
            buttons = panel.findChildren(QPushButton)
            self.assertGreaterEqual(len(buttons), 2)
            for button in buttons:
                self.assertEqual(button.font().pixelSize(), expected.font().pixelSize())
                self.assertEqual(button.font().weight(), expected.font().weight())
                self.assertEqual(button.palette().color(button.foregroundRole()),
                                 expected.palette().color(expected.foregroundRole()))
                self.assertEqual(button.cursor().shape(), Qt.CursorShape.PointingHandCursor)
                self.assertFalse(button.icon().isNull())
                self.assertFalse(button.isChecked())
                button.setFocus()
                QTest.keyClick(button, Qt.Key.Key_Space)
                self._settle()
                self.assertTrue(button.isChecked())
                QTest.keyClick(button, Qt.Key.Key_Space)
                self.assertFalse(button.isChecked())
        finally:
            panel.close()
            reference.close()
            panel.deleteLater()
            reference.deleteLater()
            self._settle()

    def test_orderbook_preserves_full_prices_at_sidebar_width_and_scrolls_wide_values(self):
        from PyQt6.QtCore import QPoint, Qt
        from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
        from core.theme import DARK, LIGHT
        from quantgen_desktop.stock_detail_style import sheet
        from quantgen_desktop.stock_insights import StockInsightsPanel

        # Match the real stock side column: its surface paints transparent rows,
        # and the scroll page gives the panel its natural content height.
        host = QFrame()
        host.setObjectName("sdSide")
        outer = QVBoxLayout(host)
        outer.setContentsMargins(10, 10, 4, 6)
        outer.setSpacing(8)
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        page.setObjectName("sdPage")
        scroll.setWidget(page)
        outer.addWidget(scroll, 1)
        body = QVBoxLayout(page)
        body.setContentsMargins(2, 4, 10, 16)
        body.setSpacing(12)
        panel = StockInsightsPanel(page)
        body.addWidget(panel)
        body.addStretch(1)

        def assert_cells_fit_vertically(area, expected_count):
            viewport = area.viewport()
            cells = [w for w in area.widget().findChildren(QLabel)
                     if w.property("insightRole") == "value"]
            self.assertEqual(len(cells), expected_count)
            # A zero scrollbar range alone can hide a compressed third row.
            # Check the actual children, without assuming any height algorithm.
            for cell in cells:
                top = cell.mapTo(viewport, QPoint(0, 0)).y()
                bottom = cell.mapTo(viewport, QPoint(0, cell.height() - 1)).y()
                self.assertGreaterEqual(top, viewport.rect().top(), cell.text())
                self.assertLessEqual(bottom, viewport.rect().bottom(), cell.text())

        try:
            host.resize(330, 900)
            host.show()
            for language, dark in (("ko", False), ("en", True)):
                for wide in (False, True):
                    with self.subTest(language=language, dark=dark, wide=wide):
                        profile = _profile(wide=wide)
                        original = copy.deepcopy(profile.__dict__)
                        host.setStyleSheet(sheet(DARK if dark else LIGHT, dark))
                        panel.set_profile(profile, language=language, dark=dark)
                        self._settle()
                        collapsed = panel.findChildren(QScrollArea)
                        self.assertEqual(len(collapsed), 2)
                        self.assertTrue(collapsed[0].isVisible())
                        self.assertFalse(collapsed[1].isVisible())
                        assert_cells_fit_vertically(collapsed[0], 12)
                        # Open the supplied remaining levels through the real button.
                        panel.findChildren(QPushButton)[-1].click()
                        self._settle()
                        areas = panel.findChildren(QScrollArea)
                        self.assertEqual(len(areas), 2)
                        first = areas[0]
                        cells = [w for w in first.widget().findChildren(QLabel)
                                 if w.property("insightRole") == "value"]
                        expected_price = "1,000,000,000,000" if wide else "1,100,001"
                        self.assertIn(expected_price, [w.text() for w in cells])
                        for index, area in enumerate(areas):
                            self.assertTrue(area.isVisible())
                            assert_cells_fit_vertically(area, 12 if index == 0 else 28)
                            self.assertEqual(area.verticalScrollBar().maximum(), 0)
                            for widget in area.widget().findChildren(QLabel):
                                if widget.property("insightRole") == "value":
                                    self.assertFalse(widget.wordWrap())
                                    self.assertGreaterEqual(widget.contentsRect().width(),
                                                            widget.fontMetrics().horizontalAdvance(widget.text()))
                        if wide:
                            self.assertGreater(first.horizontalScrollBar().maximum(), 0)
                            first.horizontalScrollBar().setValue(first.horizontalScrollBar().maximum())
                            self.assertGreater(first.horizontalScrollBar().value(), 0)
                        else:
                            self.assertEqual(first.horizontalScrollBar().maximum(), 0)
                        self.assertEqual(profile.__dict__, original)
        finally:
            panel.close()
            host.close()
            panel.deleteLater()
            host.deleteLater()
            self._settle()


if __name__ == "__main__":
    unittest.main()
