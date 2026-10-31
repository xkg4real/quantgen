"""M4-N8: bounded synthetic fits, injected UI and descriptive diagnostics."""
import json
import math
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import fx, insights
    from core.ficc.data import Series
    from core.ficc.sabr_diagnostics import fit_diagnostics, diagnostic_text, diagnostic_tone
    from core.research.fx_analysis import FXRequest, execute_fx
    from ui import fx_page
import flet as ft
from tests.portfolio_scope_acceptance import controls


def spot():
    return Series('EURUSD', 'EURUSD', 'SYNTHETIC', ('2026-01-01',), (1.1,), 'injected')


def fixture(tenor='6m', rr=.005, bf=.003, strike='ATM'):
    q = FXRequest(tool='option', source='synthetic', domestic_rate=.03, foreign_rate=.02,
                  tenor=tenor, rr=rr, bf=bf, strike=strike)
    return execute_fx(q, spot_loader=lambda *a, **k: spot(),
                      rate_loader=Mock(side_effect=AssertionError('no provider')))


class SABRDiagnosticTests(unittest.TestCase):
    def setUp(self):
        p = patch('socket.socket.connect', side_effect=AssertionError('no network'))
        p.start(); self.addCleanup(p.stop)

    def test_convergence_never_implies_independent_or_arbitrage_pass(self):
        out = fixture(); d = out.data['sabr_diagnostics']
        self.assertEqual(d['solver_status'], 'CONVERGED')
        self.assertEqual(d['active_bounds'], [])
        self.assertLess(d['rmse_vol_points'], 1e-6)
        self.assertEqual((d['quote_count'], d['free_parameter_count']), (3, 3))
        self.assertEqual(d['independent_validation'], 'NOT_RUN')
        self.assertEqual(d['arbitrage_validation'], 'NOT_RUN')
        self.assertEqual(diagnostic_tone(d), 'muted')
        self.assertIn('do not establish fit quality', out.narrative)

    def test_optimizer_bounds_and_material_residual_survive_success(self):
        for tenor, rr, bf, bound in [('6m', .005, -.001, 'rho upper'),
                                      ('6m', .04, .003, 'rho upper'),
                                      ('1w', -.03, .02, 'nu upper')]:
            with self.subTest(tenor=tenor, rr=rr, bf=bf):
                solves=[];original=fx.least_squares
                def capture(*a,**kw):
                    r=original(*a,**kw);solves.append(r);return r
                with patch.object(fx,'least_squares',side_effect=capture):
                    out=fixture(tenor,rr,bf)
                d=out.data['sabr_diagnostics'];best=min(solves,key=lambda r:r.cost)
                self.assertTrue(out.data['fit'].converged)
                expected_bounds=[f"{name} {'lower' if mask<0 else 'upper'}"
                                 for name,mask in zip(('alpha','rho','nu'),best.active_mask) if mask]
                self.assertEqual(d['active_bounds'],expected_bounds)
                # SciPy releases can stop just inside a bound without marking it active.
                # Exact parameter/limit/distance evidence must still be exposed.
                param=next(p for p in d['parameter_bounds'] if p['name']==bound.split()[0])
                self.assertLess(param['distance_to_upper'],1e-5)
                self.assertEqual(param['distance_to_upper'],param['upper']-param['value'])
                residuals=[r['residual_vol_points'] for r in d['residuals']]
                self.assertAlmostEqual(d['rmse_vol_points'],math.sqrt(sum(r*r for r in residuals)/3),places=12)
                self.assertAlmostEqual(d['rmse_vol_points'],out.data['fit'].rmse*100,places=12)
                for row, p in zip(d['residuals'],out.data['points']):
                    expected=fx.sabr_vol(out.data['forward'],p.strike,out.data['T'],out.data['fit'].alpha,1,
                                         out.data['fit'].rho,out.data['fit'].nu)
                    self.assertAlmostEqual(row['residual_vol_points'],100*(expected-p.vol),places=12)
                self.assertEqual(d['max_abs_residual_vol_points'],max(map(abs,residuals)))
                self.assertIn('Parameters / calibration bounds:',out.narrative)

    def test_unsuccessful_solver_and_unknown_bounds_are_not_conflated(self):
        out=fixture();fit=replace(out.data['fit'],converged=False,active_bounds=None)
        d=fit_diagnostics(fit,out.data['forward'],out.data['T'],out.data['points'])
        self.assertEqual(d['solver_status'],'NOT_CONVERGED');self.assertIsNone(d['active_bounds'])
        self.assertIn('not reported',diagnostic_text(d));self.assertEqual(diagnostic_tone(d),'error')

    def test_missing_quotes_cannot_be_presented_as_zero_residual(self):
        out=fixture();d=fit_diagnostics(out.data['fit'],out.data['forward'],out.data['T'])
        self.assertEqual(d['calibration_residual_status'],'NOT_RUN')
        self.assertIsNone(d['rmse_vol_points']);self.assertIsNone(d['max_abs_residual_vol_points'])
        self.assertEqual(d['pricing_strike_scope'],'NOT_RUN')
        self.assertIn('quote residuals NOT_RUN',insights.narrate_fx_option(out.data['report'],sabr=out.data['fit']))
        json.dumps(d,allow_nan=False)

    def test_strike_extrapolation_is_literal_not_a_new_quality_threshold(self):
        out=fixture();fit=out.data['fit'];points=out.data['points'];lo=min(p.strike for p in points)
        for strike, expected in [(lo,'WITHIN_QUOTED_RANGE'),(lo*.99,'EXTRAPOLATION')]:
            d=fit_diagnostics(fit,out.data['forward'],out.data['T'],points,pricing_strike=strike)
            self.assertEqual(d['pricing_strike_scope'],expected)
        self.assertIn('EXTRAPOLATION',fixture(strike='.9').narrative)

    def test_flet_visible_warning_residuals_and_real_ai_payload(self):
        seen={};page=Mock();page.run_thread.side_effect=lambda work:work()
        def ai(page,**kw):seen.update(payload=kw['payload_fn'](),narrative=kw['narrative']);return ft.Text('AI fixture')
        with patch.object(fx_page,'load_fx_spot',return_value=spot()), \
             patch.object(fx_page,'load_short_rate',side_effect=AssertionError('no provider')), \
             patch.object(fx_page,'analysis_panel',side_effect=ai):
            root=fx_page.build_fx_page(page)
            fields={c.label:c for c in controls(root) if isinstance(c,(ft.TextField,ft.Dropdown))}
            for key,value in {'Tool':'option','Data source':'synthetic','Quote-ccy rate %':'3',
                              'Base-ccy rate %':'2','Expiry':'1w','25d RR %':'-3','25d BF %':'2'}.items():
                fields[key].value=value
            next(c for c in controls(root) if isinstance(c,ft.Button)).on_click(None)
        text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
        self.assertIn('nu upper',text);self.assertIn('3 calibration quotes / 3 free parameters',text)
        self.assertIn('SABR solver CONVERGED',text);self.assertIn('arbitrage validation: NOT_RUN',text)
        tables=[c for c in controls(root) if isinstance(c,ft.DataTable)]
        self.assertTrue(any(t.columns[-1].label.value=='Residual · vol points' and len(t.rows)==3 for t in tables))
        d=seen['payload']['sabr_diagnostics'];self.assertIn('nu upper',d['active_bounds'])
        self.assertGreater(d['rmse_vol_points'],.7);self.assertIn('NOT_RUN',seen['narrative'])
        json.dumps(seen['payload'],allow_nan=False)


if __name__=='__main__':unittest.main()
