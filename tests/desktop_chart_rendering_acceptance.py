"""Measure actual Qt paint text for the clipped-axis and overlapping-legend bugs."""
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QFont, QFontMetricsF, QPainter
from PyQt6.QtWidgets import QApplication
from core.theme import DARK, LIGHT
from quantgen_desktop import charts


class ChartRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def painted_text(self, widget):
        records = []

        class RecordingPainter(QPainter):
            def drawText(self, *args):
                metrics = QFontMetricsF(self.font())
                if isinstance(args[0], QRectF):
                    rect, flags, text = args
                    bounds = metrics.boundingRect(rect, flags, text)
                elif isinstance(args[0], QPointF):
                    pos, text = args
                    bounds = metrics.boundingRect(text).translated(pos)
                else:
                    return super().drawText(*args)
                records.append((text, bounds))
                return super().drawText(*args)

        widget.show()
        self.app.processEvents()
        with patch.object(charts, 'QPainter', RecordingPainter):
            pixmap = widget.grab()
        self.assertFalse(pixmap.isNull())
        widget.hide()
        self.addCleanup(widget.deleteLater)
        return records

    def assert_inside(self, widget, records):
        bounds = QRectF(widget.rect()).adjusted(-1, -1, 1, 1)
        for text, rect in records:
            self.assertTrue(bounds.contains(rect), (text, rect, bounds))

    def test_large_price_ticks_keep_leading_digits_at_small_width(self):
        for palette in (LIGHT, DARK):
            chart = charts.FanChart()
            chart.resize(350, 280)
            chart.colors = palette
            result = SimpleNamespace(horizon_days=5, fan={
                p: [123456789*(1+(p-50)*.0005*i) for i in range(6)]
                for p in (5, 25, 50, 75, 95)})
            chart.set_result(result)
            records = self.painted_text(chart)
            self.assert_inside(chart, records)
            self.assertIn('123,456,789.0', [text for text, _ in records])
            self.assertIs(chart.result, result)

    def test_frontier_legends_and_footer_fit_without_overlapping(self):
        names = ('max_sharpe', 'min_vol', 'risk_parity', 'equal_weight')
        chart = charts.FrontierChart()
        chart.resize(350, 280)
        chart.set_output(SimpleNamespace(
            frontier=SimpleNamespace(cloud_vols=[.1, .2], vols=[.1, .2],
                                     cloud_rets=[.1, .2], rets=[.1, .2]),
            portfolios={name: SimpleNamespace(ann_vol=.1+i*.02, ann_return=.1+i*.01, objective=name)
                        for i, name in enumerate(names)}))
        records = self.painted_text(chart)
        self.assert_inside(chart, records)
        legends = [rect for text, rect in records if text in names]
        self.assertEqual(len(legends), 4)
        for i, rect in enumerate(legends):
            for other in legends[i+1:]:
                self.assertFalse(rect.intersects(other), (rect, other))

    def test_long_series_names_and_large_ticks_fit_after_font_and_width_changes(self):
        name = 'A long financial series name that must stay readable'
        chart = charts.LineChart('Sessions', 'Price / NAV')
        values = [100000000+i*1000 for i in range(5)]
        chart.set_series(range(5), [(name, values), ('NAV', values)])
        for width, size in ((350, 10), (440, 14), (900, 10)):
            chart.setFont(QFont(chart.font().family(), size))
            chart.resize(width, 280)
            records = self.painted_text(chart)
            self.assert_inside(chart, records)
            legends = [(text, rect) for text, rect in records if text.startswith('A long') or text == 'NAV']
            self.assertEqual(len(legends), 2)
            self.assertFalse(legends[0][1].intersects(legends[1][1]))
            self.assertIn(name, chart.toolTip())
            self.assertEqual(chart.series[0][1], values)

    def test_many_series_reserve_plot_height_and_do_not_overlap_ticks(self):
        chart = charts.LineChart('Sessions', 'Price')
        chart.resize(350, 280)
        chart.set_series(range(5), [(f'Financial series {i}', [j+i for j in range(5)]) for i in range(12)])
        records = self.painted_text(chart)
        self.assert_inside(chart, records)
        legend_rects = [rect for text, rect in records if text.startswith('Financial series')]
        tick_rects = [rect for text, rect in records if text.replace('.', '').isdigit()]
        self.assertEqual(len(legend_rects), 12)
        self.assertGreater(chart.minimumHeight(), 280)
        for rect in legend_rects:
            for tick in tick_rects:
                self.assertFalse(rect.intersects(tick))


if __name__ == '__main__':
    unittest.main()
