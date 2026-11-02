"""Synthetic 5y5y convention disclosure; no providers, keys or actual stores."""
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
import json
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np
from tests.desktop_acceptance import ResearchWindow, RatesRequest, execute_rates
from tests.desktop_fx_language_acceptance import numbers
from core.ficc.data import CurvePanel
from core.ficc.curves import analyze_curve
from core.ficc.swaps import par_swap_rate
from core.ficc import insights
from core.ficc.forward_conventions import (
    FIVE_YEAR_SIMPLE_LABEL, FIVE_YEAR_SIMPLE_LABEL_KO,
    FIVE_YEAR_SIMPLE_NOTE, FIVE_YEAR_SIMPLE_NOTE_KO, curve_descriptor_conventions,
)
from core.i18n import LocaleContext
from core.research.tool_export import report_bytes
from quantgen_desktop.rates_narrative import rates_korean
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.commentary import commentary_payload
from PyQt6.QtWidgets import QApplication


def flat_panel(rate):
    tenors = (.5, 1., 2., 3., 5., 7., 10., 20., 30.)
    return CurvePanel('SYNTHETIC', ('2026-01-01', '2026-01-02'), tenors,
                      np.full((2, len(tenors)), rate), 'Flat semiannual par curve fixture')


class ForwardConventionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        blocked = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        blocked.start(); self.addCleanup(blocked.stop)

    def test_flat_curve_oracle_distinguishes_simple_from_semiannual_and_par_swap(self):
        expected_keys = {'2s10s', '5s30s', '3m10y', '2s5s10s_fly', 'level',
                         '1y1y', '2y1y', '5y5y', '1y_fwd_1y_ahead'}
        for rate, expected_pct in ((.04, 4.379888399895148), (.06, 6.878327586882436)):
            report = analyze_curve(flat_panel(rate))
            value = report.descriptors['5y5y']
            # Independent nominal semiannual -> five-year simple accumulation.
            oracle = math.expm1(10 * math.log1p(rate / 2)) / 5
            self.assertAlmostEqual(value, oracle, places=13)
            self.assertAlmostEqual(value * 100, expected_pct, places=10)
            self.assertEqual(value, report.curve.fwd(5., 10.))
            equivalent = 2 * math.expm1(math.log1p(value * 5) / 10)
            self.assertAlmostEqual(equivalent, rate, places=13)
            self.assertAlmostEqual(par_swap_rate(report.curve, 5., start=5., freq=2), rate, places=13)
            self.assertGreater(value, rate)
            self.assertEqual(set(report.descriptors), expected_keys)

    def test_authored_narrative_names_convention_in_both_languages_and_preserves_unknown(self):
        out = execute_rates(RatesRequest(source='synthetic'), curve_loader=lambda **_: flat_panel(.04))
        self.assertIn('five-year simple-compounded 5y5y', out.narrative)
        self.assertIn('not a forward par swap rate', out.narrative)
        korean = rates_korean(out)
        self.assertIn('오 년 단리 5y5y', korean)
        self.assertIn('선도 파 스왑금리나 반기 복리 금리가 아닙니다', korean)
        self.assertEqual(numbers(out.narrative), numbers(korean))
        self.assertIsNone(rates_korean(replace(out, narrative='Historical/provider report 5y5y 4.38%')))
        self.assertEqual(numbers(FIVE_YEAR_SIMPLE_NOTE), numbers(FIVE_YEAR_SIMPLE_NOTE_KO))

    def test_native_label_ai_payload_and_export_preserve_values_when_language_changes(self):
        out = execute_rates(RatesRequest(source='synthetic'), curve_loader=lambda **_: flat_panel(.06))
        window = ResearchWindow(auto_refresh=False, language='en'); self.addCleanup(window.deleteLater)
        pane = window.rates; pane.show_result(out); pane.bind_output('rates', out)
        saved = deepcopy(pane.report); inputs = deepcopy(pane.values())
        note = next(x for x in pane.findChildren(UiLabel) if x.source_text == FIVE_YEAR_SIMPLE_NOTE)
        table = pane.tables['Metrics']
        index = next(i for i in range(table.rowCount()) if table.item(i, 0).text() == FIVE_YEAR_SIMPLE_LABEL)
        value = table.item(index, 1).text()
        with patch.object(window.jobs, 'start', side_effect=AssertionError('recompute forbidden')):
            for language in ('ko', 'en', 'ko'):
                window.set_language(language)
                self.assertEqual(table.item(index, 0).text(), FIVE_YEAR_SIMPLE_LABEL_KO if language == 'ko' else FIVE_YEAR_SIMPLE_LABEL)
                self.assertEqual(note.text(), FIVE_YEAR_SIMPLE_NOTE_KO if language == 'ko' else FIVE_YEAR_SIMPLE_NOTE)
                self.assertEqual(table.item(index, 1).text(), value)
                self.assertEqual(pane.report, saved); self.assertEqual(pane.values(), inputs)
        payload = commentary_payload(saved)
        for sections in (payload['sections'], json.loads(report_bytes(saved))['sections']):
            disclosure = next(x for x in sections if x['type'] == 'descriptor_conventions')
            self.assertEqual(disclosure['values'], curve_descriptor_conventions())
            self.assertIn(FIVE_YEAR_SIMPLE_NOTE, [x.get('text') for x in sections])
        with ZipFile(BytesIO(report_bytes(saved, bundle=True))) as archive:
            self.assertEqual(json.loads(archive.read('analysis.json')), saved)
            self.assertIn(b'five-year simple-compounded forward', archive.read('report.html'))
        pane.clear_result()

    def test_flet_labels_and_ai_payload_include_convention_without_numeric_schema_change(self):
        import flet as ft
        from ui import rates_page
        panel = flat_panel(.04)
        baseline = analyze_curve(panel)
        for language in ('en', 'ko'):
            stats, notices, captured = [], [], {}
            def stat(label, value, **_):
                stats.append((label, value)); return ft.Text(label)
            def notice(text, *_args, **_kwargs):
                notices.append(text); return ft.Text(text)
            def capture(page, **kwargs):
                captured.update(narrative=kwargs['narrative'], payload=kwargs['payload_fn']())
                return ft.Text('Offline analysis placeholder')
            page = SimpleNamespace(qg_locale=LocaleContext(language))
            with patch.object(rates_page, 'load_treasury_curve', return_value=panel), \
                 patch.object(rates_page, 'stat', side_effect=stat), \
                 patch.object(rates_page, 'notice', side_effect=notice), \
                 patch.object(rates_page, 'analysis_panel', side_effect=capture), \
                 patch.object(rates_page.fcharts, 'curve_chart', return_value=ft.Container()), \
                 patch.object(rates_page.fcharts, 'curve_history_chart', return_value=ft.Container()):
                rates_page._run_curve(page, source='synthetic', method='bootstrap', lookback=20)
            label = FIVE_YEAR_SIMPLE_LABEL_KO if language == 'ko' else FIVE_YEAR_SIMPLE_LABEL
            self.assertIn((label, '4.38%'), stats)
            self.assertIn(FIVE_YEAR_SIMPLE_NOTE_KO if language == 'ko' else FIVE_YEAR_SIMPLE_NOTE, notices)
            self.assertEqual(captured['payload']['descriptors'], baseline.descriptors)
            self.assertEqual(captured['payload']['descriptor_conventions'], curve_descriptor_conventions())
            self.assertIn('five-year simple-compounded 5y5y', captured['narrative'])

    def test_weekly_text_and_ai_prompt_do_not_call_simple_forward_a_par_swap(self):
        from core.ficc.macro import macro_sheet
        text = insights.narrate_weekly_strategy(macro_sheet(source='synthetic'), analyze_curve(flat_panel(.04)))
        for value in (text, insights.report_prompt('weekly_fi_fx_strategy')):
            self.assertIn('five-year simple-compounded 5y5y', value)
            self.assertIn('not a forward par swap rate', value)


if __name__ == '__main__': unittest.main()
