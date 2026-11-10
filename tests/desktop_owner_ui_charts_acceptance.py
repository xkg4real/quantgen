"""Owner UI port, area charts + macro (owner issues 02, 11 and 14, 2026-11-10), native PyQt app.

What the owner sees: chart axes with round ticks (no "180.50" observation indices), Korean axis captions
and legends in a Korean window, a "how to read this chart" guide under each chart that has one in the
Flet app, and a Macro sheet whose z-score chart reads like the fixed Flet chart (plain names, groups,
usual-range band, unusual guides, synthetic status said once) with tables sized to their rows. English
windows stay English, a language switch reruns nothing, and exports are unchanged. No network.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop import charts
    from quantgen_desktop.chart_study import ChartReading
    from quantgen_desktop.localization import UiLabel
    from quantgen_desktop.owner_ui_language.charts import READINGS, READING_KEYS
    from tests.desktop_macro_language_acceptance import output as macro_output
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QFontMetricsF, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

Z_CHART = '1y z-scores · descriptive only'


def painted(widget):
    """Every text the widget paints, with its bounds."""
    records = []

    class Recording(QPainter):
        def drawText(self, *args):
            metrics = QFontMetricsF(self.font())
            if isinstance(args[0], QRectF):
                rect, flags, text = args
                records.append((text, metrics.boundingRect(rect, flags, text)))
            elif isinstance(args[0], QPointF):
                records.append((args[1], metrics.boundingRect(args[1]).translated(args[0])))
            return super().drawText(*args)

    with patch.object(charts, 'QPainter', Recording):
        widget.grab()
    return records


class Host(QWidget):
    """A top-level stand-in for the window language of a chart."""
    def __init__(self, language):
        super().__init__()
        from core.i18n import LocaleContext
        self.ui_language = language
        self.ctx = LocaleContext('ko_KR' if language == 'ko' else 'en_US')


class ChartAxesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def chart(self, language, x_label, y_label, x, series):
        host = Host(language)
        self.addCleanup(host.deleteLater)
        chart = charts.LineChart(x_label, y_label, parent=host)
        chart.resize(790, 320)
        chart.set_series(x, series)
        host.resize(800, 340)
        host.show()
        self.app.processEvents()
        return chart

    def test_observation_axes_have_whole_round_ticks(self):
        values = [1 + 0.001 * i for i in range(723)]
        chart = self.chart('en', 'OOS observations', 'Equity', range(len(values)), [('Strategy', values)])
        texts = [t for t, _ in painted(chart)]
        x_ticks = [t for t in texts if re.fullmatch(r'[\d,]+', t)]
        self.assertGreaterEqual(len(x_ticks), 3, texts)
        self.assertTrue(all(int(t.replace(',', '')) % 100 == 0 for t in x_ticks), x_ticks)
        self.assertFalse(any(re.fullmatch(r'\d+\.\d\d', t) and float(t) > 10 for t in texts), texts)
        y_ticks = [float(t) for t in texts if re.fullmatch(r'\d\.\d+', t)]
        self.assertTrue(y_ticks and all(abs(v * 10 - round(v * 10)) < 1e-9 for v in y_ticks), y_ticks)

    def test_index_axes_and_small_spans_never_print_fractions_repeats_or_negative_zero(self):
        # Market area request (2026-11-10): ETF/crypto/derivatives axes read '125.75', '251.50', and the
        # risk-neutral density axis read 0.01, 0.01, 0.00, 0.00, -0.00.
        import math
        for x, values in ((range(504), [100 + i % 7 for i in range(504)]),
                          ([4000 + 25 * k for k in range(81)],
                           [1e-3 * math.exp(-((k - 40) / 12) ** 2) - 2e-5 for k in range(81)]),
                          (range(30), [-0.004 + 0.0003 * i for i in range(30)])):
            with self.subTest(span=max(values) - min(values)):
                chart = self.chart('en', 'Index points', 'Density', x, [('Q density', values)])
                records = painted(chart)
                plot_bottom = max(rect.bottom() for t, rect in records if t == 'Index points')
                numbers = [(t, rect) for t, rect in records if re.fullmatch(r'[-−]?[\d,]*\.?\d+', t)]
                y_labels = [t for t, rect in numbers if rect.right() < 80]
                x_labels = [t for t, rect in numbers if rect.right() >= 80 and rect.bottom() < plot_bottom]
                self.assertGreaterEqual(len(y_labels), 3, y_labels)
                self.assertEqual(len(y_labels), len(set(y_labels)), y_labels)
                self.assertFalse([t for t in y_labels if re.fullmatch(r'[-−]0(\.0+)?', t)], y_labels)
                self.assertTrue(x_labels and all('.' not in t for t in x_labels), x_labels)

    def test_frontier_legend_names_objectives_in_each_language(self):
        from types import SimpleNamespace
        from quantgen_desktop.translations import translate
        ids = ('max_sharpe', 'min_vol', 'risk_parity', 'equal_weight')
        output = SimpleNamespace(
            frontier=SimpleNamespace(cloud_vols=[.1, .2], vols=[.1, .2], cloud_rets=[.1, .2], rets=[.1, .2]),
            portfolios={k: SimpleNamespace(ann_vol=.1 + i * .02, ann_return=.1 + i * .01, objective=k)
                        for i, k in enumerate(ids)})
        for language, expected in (('en', ['Max Sharpe', 'Minimum volatility', 'Risk parity', 'Equal weight']),
                                   ('ko', [translate(k, 'ko') for k in ids])):
            host = Host(language)
            self.addCleanup(host.deleteLater)
            chart = charts.FrontierChart(parent=host)
            chart.resize(790, 320)
            chart.set_output(output)
            self.assertEqual(chart._legend_names(), expected)
            if language == 'ko':
                self.assertTrue(all(re.search('[가-힣]', name) for name in expected), expected)
            self.assertTrue(set(expected) <= {t for t, _ in painted(chart)})

    def test_tenor_axes_use_round_years(self):
        tenors = [1 / 12, .25, .5, 1, 2, 3, 5, 7, 10, 20, 30]
        chart = self.chart('en', 'Maturity · years', 'Yield · %', tenors, [('Zero', [4 + t / 30 for t in tenors])])
        texts = [t for t, _ in painted(chart)]
        self.assertTrue({'10', '20', '30'} <= set(texts), texts)
        self.assertNotIn('7.56', texts)

    def test_korean_window_shows_korean_axis_captions_and_legends(self):
        equity = [1 + 0.001 * i for i in range(50)]
        cases = (
            ('OOS observations', 'Equity', [('Strategy', equity), ('Benchmark', equity)],
             {'표본 외(OOS) 거래일', '누적 성과 (1에서 시작)', '전략', '비교 기준'},
             {'OOS observations', 'Equity', 'Strategy', 'Benchmark'}),
            ('Tenor · years', 'Loading', [('level', equity), ('slope', equity), ('curvature', equity)],
             {'기간 · 년', '요인 적재값', '수준', '기울기', '곡률'},
             {'Tenor · years', 'Loading', 'level', 'slope', 'curvature'}),
            ('Maturity · years', 'Yield · %', [('Zero', equity), ('Par', equity)],
             {'만기 · 년', '금리 · %', '무이표 금리', '파 금리'},
             {'Maturity · years', 'Yield · %', 'Zero', 'Par'}),
            ('Observations · 2026-07-22 → 2026-11-10', 'Par yield · %', [('3m', equity), ('10y', equity)],
             {'관측 · 2026-07-22 → 2026-11-10', '파 금리 · %', '3개월물', '10년물'},
             {'Observations · 2026-07-22 → 2026-11-10', 'Par yield · %', '3m', '10y'}),
        )
        for x_label, y_label, series, korean, english in cases:
            with self.subTest(y_label=y_label):
                chart = self.chart('ko', x_label, y_label, range(50), series)
                texts = {t for t, _ in painted(chart)}
                self.assertTrue(korean <= texts, (korean - texts, texts))
                chart.window().ui_language = 'en'
                from core.i18n import LocaleContext
                chart.window().ctx = LocaleContext('en_US')
                chart._reserve_text_space()
                texts = {t for t, _ in painted(chart)}
                self.assertTrue(english <= texts, (english - texts, texts))
                self.assertEqual(chart.series, series)

    def test_y_caption_and_ticks_stay_inside_and_apart(self):
        chart = self.chart('ko', 'Observations', 'Par yield · %', range(80),
                           [(f'{t}y', [3 + t / 10 + i / 100 for i in range(80)]) for t in (2, 5, 10, 30)])
        records = painted(chart)
        bounds = QRectF(chart.rect()).adjusted(-1, -1, 1, 1)
        for text, rect in records:
            self.assertTrue(bounds.contains(rect), (text, rect))
        caption = next(rect for text, rect in records if text == '파 금리 · %')
        for text, rect in records:
            if re.fullmatch(r'[\d.]+', text):
                self.assertFalse(caption.intersects(rect), (text, rect, caption))


class MacroSheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.ficc.macro.macro_sheet'):
            blocker = patch(target, side_effect=AssertionError('network/loader forbidden'))
            blocker.start()
            self.addCleanup(blocker.stop)
        self.window = ResearchWindow(auto_refresh=False, language='ko')
        self.window.resize(1440, 900)
        self.window.show()
        self.addCleanup(self.close)

    def close(self):
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def settle(self):
        for _ in range(5):
            self.app.processEvents()
            QTest.qWait(10)

    def run_sheet(self, **kwargs):
        pane = self.window.macro
        self.window.show_market_pane(pane)
        out = macro_output('sheet', **kwargs)
        pane.show_result(out)
        pane.bind_output('macro', out)
        self.settle()
        return pane, out

    def test_z_chart_reads_like_the_flet_chart_in_both_languages(self):
        pane, out = self.run_sheet(short=True)
        chart = pane.charts[Z_CHART]
        report, sections = deepcopy(pane.report), deepcopy(pane.sections)
        rows = deepcopy(chart.rows)
        # The export keeps the source rows, ' · SYNTHETIC' included.
        bars = next(s for s in pane.sections if s.get('name') == Z_CHART)
        self.assertTrue(all(name.endswith(' · SYNTHETIC') for name, _ in bars['rows']))
        with patch.object(self.window.jobs, 'start', side_effect=AssertionError('rerun')):
            for language in ('ko', 'en', 'ko'):
                self.window.set_language(language)
                self.settle()
                labels = [chart.display_label(i) for i in range(len(chart.rows))]
                self.assertFalse(any('SYNTHETIC' in name for name in labels), labels)
                self.assertEqual(set(chart.zscore['hatched']), set(range(len(chart.rows))))
                texts = [t for t, _ in painted(chart)]
                if language == 'ko':
                    self.assertIn('투자등급 회사채 스프레드 (IG OAS)', labels)
                    self.assertIn('장단기 금리차 10년−2년 (2s10s)', labels)
                    for text in ('평소 범위 (±1)', '1년 z-점수 (0 = 1년 평균, ±2 = 이례적)', '금리', '신용', '외환',
                                 '위험선호', '합성 데이터 · 실제 관측 아님'):
                        self.assertIn(text, texts)
                else:
                    self.assertEqual(labels, [a.label for a in out.sheet.rows])
                    for text in ('Usual range (±1)', '1-year z-score (0 = 1-year average, ±2 = unusual)', 'Rates',
                                 'Credit', 'Synthetic data · not observed'):
                        self.assertIn(text, texts)
                # Every value is printed once, at its bar end.
                for _, value in chart.rows:
                    self.assertEqual(texts.count(f'{value:+.2f}'.replace('-', '−')), 1, value)
                self.assertEqual(chart.rows, rows)
                self.assertEqual(pane.report, report)
                self.assertEqual(pane.sections, sections)
        heading = pane.result_layout.itemAt(pane.result_layout.indexOf(chart) - 2).widget()
        self.assertEqual(heading.text(), '주요 거시 지표: 1년 평균 대비 현재 위치 (z-점수)')

    def test_display_only_text_is_not_mistaken_for_export_text(self):
        # Tests and exports find a result's text by UiLabel.source_text; guides and captions are not UiLabels.
        pane, _ = self.run_sheet(short=True)
        texts = [s['text'] for s in pane.sections if s['type'] == 'text']
        for label in pane.findChildren(UiLabel):
            if getattr(label, 'localized_text', {}):
                self.assertIn(label.source_text, texts)
        self.assertTrue(pane.charts[Z_CHART].reading.texts)

    def test_synthetic_status_is_said_once_on_screen(self):
        pane, out = self.run_sheet(short=True)
        for language, words in (('ko', ('합성', 'SYNTHETIC')), ('en', ('SYNTHETIC', 'ynthetic'))):
            self.window.set_language(language)
            self.settle()
            # The chart's reading guide explains what hatching means; it is not a status line.
            shown = [w.text() for w in pane.result.findChildren(UiLabel)
                     if w.isVisible() and any(word in w.text() for word in words)
                     and not isinstance(w.parentWidget().parentWidget().parentWidget(), ChartReading)]
            self.assertEqual(len(shown), 1, shown)
            self.assertIn('35', shown[0])                     # the short-series note rides on the same notice
            for ident in out.sheet.synthetic_ids:
                self.assertIn(ident, shown[0])

    def test_descriptive_read_explains_each_word_with_the_summary_numbers(self):
        pane, out = self.run_sheet()
        summary = next(w for w in pane.result.findChildren(UiLabel) if w.source_text == out.sheet.regime.summary)
        for language, expected in (('ko', ('수익률곡선 · 금리 하락·곡선 가팔라짐 —', '(20거래일: 10년 금리 -14bp, 장단기 금리차 +12bp)',
                                           '위험 · 위험 회피 —', '(VIX·하이일드 평균 z-점수 +0.91)')),
                                   ('en', ('Curve · bull steepener —', '(20 sessions: 10y -14bp, 2s10s +12bp)',
                                           'Risk · risk-off —', '(VIX/HY average z +0.91)'))):
            self.window.set_language(language)
            self.settle()
            for text in expected:
                self.assertIn(text, summary.text())
            self.assertEqual(summary.text().count('\n'), 4)
        self.assertTrue(any(s.get('text') == out.sheet.regime.summary for s in pane.report['sections']))

    def test_tables_are_sized_to_their_rows_and_change_columns_read_korean(self):
        pane, out = self.run_sheet()
        read, indicators = pane.tables['Descriptive read'], pane.tables['Macro indicators']
        for table in (read, indicators):
            controller = table._content_height_controller
            self.assertEqual(table.height(), controller.content_height())
            self.assertEqual(table.verticalScrollBar().maximum(), 0)
        self.assertLess(read.height(), 120)                   # one row: no empty table body
        self.assertEqual(indicators.horizontalScrollBar().maximum(), 0)
        headers = [indicators.horizontalHeaderItem(c).text() for c in range(3, 7)]
        self.assertEqual(headers, ['1일', '1주', '1개월', '3개월'])
        # Names stay left-aligned (they are words, not values).
        from PyQt6.QtCore import Qt
        self.assertFalse(indicators.item(0, 1).textAlignment() & Qt.AlignmentFlag.AlignRight)
        self.window.set_language('en')
        self.settle()
        self.assertEqual([indicators.horizontalHeaderItem(c).text() for c in range(3, 7)], ['1d', '1w', '1m', '3m'])
        export = next(s for s in pane.report['sections'] if s.get('name') == 'Macro indicators')
        self.assertEqual(export['headers'][3:7], ['1d', '1w', '1m', '3m'])
        self.assertEqual(len(export['headers']), 11)

    def test_rerun_replaces_the_wide_indicator_table(self):
        pane, _ = self.run_sheet()
        pane, _ = self.run_sheet()
        self.settle()
        tables = [w for w in pane.wide.findChildren(type(pane.tables['Macro indicators'])) if not w.isHidden()]
        self.assertEqual(tables, [pane.tables['Macro indicators']])
        pane.clear_result()
        self.settle()
        self.assertEqual(pane.wide_layout.count(), 0)

    def test_macro_screens_say_no_english_words_in_korean_notes(self):
        self.window.macro.status.setText(self.window.macro.status.source_text)
        self.assertNotIn('descriptive', self.window.macro.status.text())
        self.assertNotIn('Overlay', self.window.macro.status.text())
        records = self.window.macro_records.status
        self.assertNotIn('Live', records.text())
        self.assertIn('실제 실행', records.text())
        self.window.set_language('en')
        self.settle()
        self.assertTrue(records.text().startswith('Records are read explicitly.'))
        self.assertTrue(self.window.macro.status.text().startswith('This tab is a descriptive macro sheet.'))

    def test_macro_v2_closing_note_reads_in_each_language_and_exports_unchanged(self):
        from quantgen_desktop.macro_records import MacroRecordOutput, MacroRecordRequest
        pane = self.window.macro_records
        self.window.show_market_pane(pane)
        data = {'tf': {'weights': [{'name': 'fixture', 'weight': 3}], 'register': [{'status': 'OWNER-DECISION'}]},
                'backlog': {'items': [{'id': 'DNB-fixture'}]}, 'council': {'resolutions': ['synthetic']}}
        out = MacroRecordOutput(MacroRecordRequest(tool='research'), data)
        pane.show_result(out)
        pane.bind_output('macro v2', out)
        self.settle()
        source = 'Research register · 표시 전용. 설계 가중치를 노출·규칙·book 입력으로 보내지 않습니다.'
        self.assertTrue(any(s.get('text') == source for s in pane.report['sections']))
        report = deepcopy(pane.report)
        for language, expected in (('ko', '연구 등록부 · 표시 전용. 설계 가중치를 노출·규칙·북 입력으로 보내지 않습니다.'),
                                   ('en', 'Research register · display only. Design weights are not sent as '
                                          'exposure, rule or book inputs.')):
            self.window.set_language(language)
            self.settle()
            self.assertEqual(' '.join(pane.narrative_view.lines()), expected)
            self.assertEqual(pane.report, report)


class ReadingGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_every_native_tool_chart_has_a_complete_guide(self):
        names = set()
        for path in Path('quantgen_desktop').glob('*.py'):
            names |= set(re.findall(r"self\.(?:line|bars)\(\s*'([^']+)'", path.read_text(encoding='utf-8')))
        names.add(Z_CHART)                                    # macro.py passes it through a constant
        self.assertTrue(names)
        self.assertEqual(sorted(names - set(READINGS)), [])
        for name, guide in READINGS.items():
            self.assertEqual(tuple(guide), READING_KEYS, name)
            for korean, english in guide.values():
                self.assertTrue(re.search('[가-힣]', korean), (name, korean))
                self.assertFalse(re.search('[가-힣]', english), (name, english))

    def test_guide_follows_the_window_language_under_the_chart(self):
        window = ResearchWindow(auto_refresh=False, language='ko')
        self.addCleanup(window.deleteLater)
        window.resize(1440, 900)
        window.show()
        pane = window.macro
        window.show_market_pane(pane)
        with patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden')):
            out = macro_output('sheet')
            pane.show_result(out)
        self.app.processEvents()
        chart = pane.charts[Z_CHART]
        guide = chart.reading
        self.assertIsInstance(guide, ChartReading)
        self.assertEqual(pane.result_layout.indexOf(guide), pane.result_layout.indexOf(chart) + 1)
        self.assertTrue(guide.body.isVisible())
        self.assertEqual(guide.headings[0].text(), '01  무엇을 나타내나요?')
        self.assertEqual(guide.texts[0].text(), READINGS[Z_CHART]['meaning'][0])
        self.assertEqual(guide.toggle.text(), '이 차트 읽는 법')
        self.assertEqual(guide.columns, 2)
        window.set_language('en')
        self.app.processEvents()
        self.assertEqual(guide.headings[3].text(), '04  Limits')
        self.assertEqual(guide.texts[3].text(), READINGS[Z_CHART]['limit'][1])
        self.assertEqual(guide.toggle.text(), 'How to read this chart')
        guide.toggle.setChecked(False)
        self.assertFalse(guide.body.isVisible())
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            window.close()


if __name__ == '__main__':
    unittest.main()
