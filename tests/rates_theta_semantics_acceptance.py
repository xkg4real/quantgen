"""Hull–White theta is descriptive calibration output, not its drift level."""
from copy import deepcopy
from dataclasses import replace
import json
import unittest
from unittest.mock import Mock, patch

import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import data, ratesim
    from core.ficc.curves import curve_from_snapshot, flat_curve
    from core.ficc.rate_diagnostics import theta_semantics
    from core.research.rates_analysis import RatesRequest, execute_rates
    from core.research.tool_export import report_bytes
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.commentary import commentary_payload
    from quantgen_desktop.localization import UiLabel
    from quantgen_desktop.rates_narrative import simulation_korean
    from ui import rates_page
from PyQt6.QtWidgets import QApplication
import flet as ft


def output(model):
    panel = data.synthetic_curve_panel(days=40, seed=19)
    series = data.synthetic_series('SOFR', days=60, kind='rate')
    params = ratesim.ShortRateParams(model, .2, .03, .01, .01)
    with patch.object(ratesim, 'calibrate', return_value=params):
        result = execute_rates(
            RatesRequest(tool='sim', source='synthetic', model=model, horizon=.25,
                         n_paths=100, instrument='bond', tenor='5y'),
            curve_loader=lambda **kw: panel, rate_loader=lambda *a, **kw: series)
    return result, panel, series, params


class ThetaSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'socket.socket.connect',
                       'core.ficc.data._fred_fetch', 'core.ficc.data._yf_fetch'):
            guard = patch(target, side_effect=AssertionError('network/provider forbidden'))
            guard.start(); self.addCleanup(guard.stop)

    def test_hull_white_theta_change_leaves_paths_and_curve_unchanged(self):
        params = ratesim.ShortRateParams('hull_white', .2, .03, .01, .01)
        args = dict(horizon=.25, n_paths=100, steps_per_year=12, curve=flat_curve(.04), seed=7)
        a = ratesim.simulate(params, **args)
        b = ratesim.simulate(replace(params, theta=.30), **args)
        np.testing.assert_array_equal(a.terminal, b.terminal)
        for q in a.fan: np.testing.assert_array_equal(a.fan[q], b.fan[q])
        self.assertEqual(a.model_curve_at_horizon, b.model_curve_at_horizon)
        self.assertFalse(theta_semantics(params)['used_by_simulation'])
        for model in ('vasicek', 'cir'):
            p = replace(params, model=model)
            self.assertTrue(theta_semantics(p)['used_by_simulation'])
            self.assertEqual(theta_semantics(p)['role'], 'long_run_mean')

    def test_native_bilingual_display_export_and_ai_preview_keep_theta_role(self):
        w = ResearchWindow(auto_refresh=False, language='ko',
                           paper_factory=Mock(side_effect=AssertionError('no store')))
        self.addCleanup(w.deleteLater)
        for model in ratesim.MODELS:
            with self.subTest(model=model):
                out, *_ = output(model)
                w.rates.show_result(out)
                with patch('core.research.provenance.code_evidence', return_value={'commit':'fixture'}), \
                     patch('core.research.provenance.runtime_evidence', return_value={'python':'fixture'}):
                    w.rates.bind_output('rates', out)
                original = deepcopy(w.rates.report)
                labels = [x for x in w.rates.findChildren(UiLabel)
                          if getattr(x, 'source_text', '') == out.narrative]
                self.assertTrue(labels)
                for language in ('en', 'ko', 'en'):
                    w.set_language(language)
                    self.assertEqual(labels[-1].text(), out.narrative if language == 'en'
                                     else simulation_korean(out.report, out.horizon_pv))
                    self.assertEqual(w.rates.report, original)
                canonical = json.loads(report_bytes(original))
                semantics = next(s['theta'] for s in canonical['sections']
                                 if s.get('type') == 'rate_parameter_semantics')
                self.assertEqual(semantics, theta_semantics(out.report.params))
                self.assertEqual(semantics['value'], .03)
                self.assertEqual(canonical['verdict'], 'NOT_RUN')
                ai = commentary_payload(original)
                self.assertIn({'type':'rate_parameter_semantics','theta':semantics}, ai['sections'])
                metrics = next(s for s in canonical['sections'] if s.get('name') == 'Metrics')
                self.assertEqual('Theta' in dict(metrics['rows']), model != 'hull_white')
                if model == 'hull_white':
                    self.assertIn('regression mean', out.narrative)
                    self.assertNotIn('long-run mean', out.narrative)
                    self.assertIn('회귀 평균', simulation_korean(out.report))
                    self.assertNotIn('장기 평균', simulation_korean(out.report))
                    note = next(x for x in w.rates.findChildren(UiLabel)
                                if x.source_text.startswith(semantics['label'] + ':'))
                    w.set_language('ko')
                    self.assertIn(semantics['label_ko'], note.text())
                    self.assertIn(semantics['note_ko'], note.text())
                    w.set_language('en')
                    self.assertIn(semantics['note'], note.text())
                else:
                    self.assertIn('long-run mean', out.narrative)

    def test_flet_theta_tile_notice_and_real_payload_boundary_agree(self):
        for model in ratesim.MODELS:
            with self.subTest(model=model):
                out, panel, series, params = output(model)
                captures = []
                def analysis(_page, **kwargs):
                    captures.append(kwargs['payload_fn']())
                    return ft.Text(kwargs['narrative'])
                with patch.object(rates_page, 'load_short_rate', return_value=series), \
                     patch.object(rates_page, '_curve', return_value=(panel, curve_from_snapshot(panel.latest()))), \
                     patch.object(rates_page, 'calibrate', return_value=params), \
                     patch.object(rates_page.fcharts, 'rate_fan_chart', return_value=ft.Text('chart')), \
                     patch.object(rates_page.fcharts, 'horizon_pv_hist', return_value=ft.Text('hist')), \
                     patch.object(rates_page, 'analysis_panel', side_effect=analysis), \
                     patch.object(rates_page, 'stat', wraps=rates_page.stat) as stat, \
                     patch.object(rates_page, 'notice', wraps=rates_page.notice) as notice:
                    rates_page._run_sim(Mock(), source='synthetic', model=model, horizon=.25,
                                        n_paths=100, threshold_pct=None, instrument='bond',
                                        instr_tenor_text='5y', coupon_pct=4)
                semantics = captures[0]['parameter_semantics']['theta']
                self.assertEqual(semantics, theta_semantics(out.report.params))
                self.assertEqual(captures[0]['params']['theta'], .03)
                self.assertEqual(captures[0]['horizon_pv']['var95'], out.horizon_pv.var95)
                titles = [c.args[0] for c in stat.call_args_list]
                self.assertEqual('theta' in titles, model != 'hull_white')
                if model == 'hull_white':
                    self.assertIn(semantics['label'], titles)
                    self.assertIn(semantics['note'], [c.args[0] for c in notice.call_args_list])


if __name__ == '__main__':
    unittest.main()
