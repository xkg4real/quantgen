"""Actual Qt presentation regressions with fixed, supplied profile dictionaries.

No application window, quote client, model/history engine or provider is created.
Run under the reviewed isolated Qt harness.
"""
from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace
import unittest


def _profile(*, wide=False, quantities='flat'):
    raw = {"aspr_acpt_hour": "200000"}
    for level in range(1, 11):
        ask_qty = '0' if quantities == 'zero' else (str(level * 10) if quantities == 'varied' else '1016')
        bid_qty = '0' if quantities == 'zero' else (str(level * 25) if quantities == 'varied' else '987')
        if quantities == 'varied' and level == 2:
            ask_qty = ''
        if quantities == 'varied' and level == 1:
            bid_qty = '0'
        raw.update({f"askp{level}": str((999999999999 if wide else 1100000) + level),
                    f"bidp{level}": str((999999999999 if wide else 1099000) - level),
                    f"askp_rsqn{level}": ask_qty, f"bidp_rsqn{level}": bid_qty})
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
        from quantgen_desktop.font_policy import configure_interface_font, INTERFACE_FAMILY
        cls.app = QApplication.instance() or QApplication([])
        previous_font = cls.app.font()
        cls.addClassCleanup(cls.app.setFont, previous_font)
        family = configure_interface_font(cls.app, Path(__file__).resolve().parents[1] / 'assets/fonts')
        if family != INTERFACE_FAMILY:
            raise AssertionError('The production QG font bundle is required for stock layout contracts')

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
                            # The stock page already uses the up/down role for
                            # market sides. Compare that same role, not neutral ink.
                            expected.setProperty('tone', widget.property('tone'))
                            expected.style().unpolish(expected)
                            expected.style().polish(expected)
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

        def assert_visible_cells_fit(area, expected_rows):
            viewport=area.viewport()
            self.assertEqual(tuple(area.visible_rows),tuple(expected_rows))
            cells=[]
            for row in expected_rows:
                for cell in (row.price_label,row.quantity_bar.label):
                    self.assertFalse(cell.isHidden())
                    self.assertFalse(cell.wordWrap())
                    self.assertGreaterEqual(cell.contentsRect().width(),
                                            cell.fontMetrics().horizontalAdvance(cell.text()),cell.text())
                    top=cell.mapTo(viewport,QPoint(0,0)).y()
                    bottom=cell.mapTo(viewport,QPoint(0,cell.height()-1)).y()
                    self.assertGreaterEqual(top,viewport.rect().top(),cell.text())
                    self.assertLessEqual(bottom,viewport.rect().bottom(),cell.text())
                    cells.append(cell)
            # Hidden levels must not leave stray values painting outside the table.
            for row in area.rows:
                self.assertEqual(row.price_label.isHidden(),row not in expected_rows)
            self.assertEqual(len(cells),2*len(expected_rows))
            self.assertEqual(area.verticalScrollBar().maximum(),0)

        try:
            from PyQt6.QtGui import QColor
            from quantgen_desktop.typography import tone_colors
            host.resize(330,900)
            host.show()
            for language,dark in (("ko",False),("en",True)):
                for wide,quantities in ((False,'varied'),(False,'zero'),(True,'varied')):
                    with self.subTest(language=language,dark=dark,wide=wide,quantities=quantities):
                        profile=_profile(wide=wide,quantities=quantities)
                        # Force truly exceptional values, rather than assuming a
                        # particular number of digits cannot fit the new ladder.
                        if wide:
                            for level in range(1,11):
                                profile.values['orderbook']['output1'][f'askp{level}']=str(10**18+level*1024)
                                profile.values['orderbook']['output1'][f'bidp_rsqn{level}']=str(10**18+level*1024)
                        original=copy.deepcopy(profile.__dict__)
                        host.setStyleSheet(sheet(DARK if dark else LIGHT,dark))
                        panel.set_profile(profile,language=language,dark=dark)
                        self._settle()
                        self.assertEqual(panel.findChildren(QScrollArea),[panel.depth_ladder])
                        ladder=panel.depth_ladder
                        rows=ladder.rows
                        self.assertEqual(tuple((r.side,r.level) for r in rows),
                            tuple(('ask',i) for i in range(10,0,-1))+tuple(('bid',i) for i in range(1,11)))
                        raw=profile.values['orderbook']['output1']
                        expected_scale=max(float(raw[f'{side}p_rsqn{level}'])
                            for side in ('ask','bid') for level in range(1,11)
                            if raw[f'{side}p_rsqn{level}']!='')
                        self.assertEqual(ladder.scale,expected_scale)
                        for row in rows:
                            qty_raw=raw[f'{row.side}p_rsqn{row.level}']
                            qty=None if qty_raw=='' else float(qty_raw)
                            # The existing depth contract withholds the whole
                            # level when either its price or size is missing.
                            price=None if qty is None else float(raw[f'{row.side}p{row.level}'])
                            self.assertEqual(row.quantity,qty)
                            self.assertEqual(row.price,price)
                            self.assertEqual(row.price_label.text(),'—' if price is None else f'{price:,.0f}')
                            bar=row.quantity_bar
                            self.assertEqual((bar.side,bar.quantity,bar.scale),(row.side,qty,expected_scale))
                            self.assertEqual(bar.color,tone_colors(dark)['down' if row.side=='ask' else 'up'])
                            color=QColor(bar.color)
                            self.assertGreater(color.blue(),color.red()) if row.side=='ask' else self.assertGreater(color.red(),color.blue())
                            self.assertIs(row.widgets[0 if row.side=='ask' else 2],bar)
                            self.assertIs(row.widgets[1],row.price_label)
                            if qty is None:
                                self.assertIsNone(bar.fraction)
                                self.assertNotEqual(bar.label.text(),'0')
                            else:
                                self.assertEqual(bar.label.text(),f'{qty:,.0f}')
                                self.assertAlmostEqual(bar.fraction,qty/expected_scale if expected_scale else 0)
                        self.assertFalse(ladder.expanded)
                        collapsed=tuple(r for r in rows if r.level<=3)
                        self.assertEqual(tuple((r.side,r.level) for r in collapsed),
                            (('ask',3),('ask',2),('ask',1),('bid',1),('bid',2),('bid',3)))
                        assert_visible_cells_fit(ladder,collapsed)
                        initial_scale=ladder.scale
                        panel.depth_toggle.click()
                        self._settle()
                        self.assertTrue(ladder.expanded)
                        self.assertEqual(ladder.scale,initial_scale)
                        assert_visible_cells_fit(ladder,rows)
                        # Read geometric order, not just the model's tuple order.
                        y=[r.price_label.mapTo(ladder.viewport(),QPoint()).y() for r in rows]
                        self.assertEqual(y,sorted(y))
                        self.assertEqual(len(set(y)),20)
                        if wide:
                            self.assertGreater(ladder.horizontalScrollBar().maximum(),0)
                            ladder.horizontalScrollBar().setValue(ladder.horizontalScrollBar().maximum())
                            self.assertGreater(ladder.horizontalScrollBar().value(),0)
                        else:
                            self.assertEqual(ladder.horizontalScrollBar().maximum(),0)
                        panel.depth_toggle.click()
                        self._settle()
                        assert_visible_cells_fit(ladder,collapsed)
                        self.assertEqual(ladder.scale,initial_scale)
                        self.assertEqual(profile.__dict__,original)

        finally:
            panel.close()
            host.close()
            panel.deleteLater()
            host.deleteLater()
            self._settle()


if __name__ == "__main__":
    unittest.main()
