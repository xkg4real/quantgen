"""M3-N04: optional cross-model inversion must not erase valid pricing."""
import math
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import swaps, insights
    from core.ficc.curves import flat_curve
    from core.ficc.data import CurvePanel
    from core.ficc.common import FICCError
    from core.research.rates_analysis import RatesRequest, RatesOutput
    from ui import rates_page
import flet as ft
from tests.portfolio_scope_acceptance import controls


def fixture(model='bachelier', tiny=False):
    rate, expiry, tenor, strike, vol = ((.04, 1., 5., .01, .00001) if tiny else (.01, 10., 10., .001, .01))
    curve=flat_curve(rate, date='2026-01-01', source='SYNTHETIC')
    request=RatesRequest(tool='option', source='synthetic', expiry=f'{expiry:g}y', tenor=f'{tenor:g}y',
                         strike=strike, vol=vol, option_model=model, pay_fixed=False)
    panel=CurvePanel('SYNTHETIC',('2026-01-01',),(.5,1.,5.,10.,30.),np.full((1,5),rate),'injected curve')
    report=swaps.price_swaption(swaps.Swaption(expiry,tenor,strike=strike,payer=False),curve,vol=vol,model=model)
    return RatesOutput(request,panel,curve,report,insights.narrate_swaption(report))


class SwaptionConversionTests(unittest.TestCase):
    def test_normal_price_above_black_domain_survives_with_independent_oracle(self):
        out=fixture();r=out.report;q=out.request
        sd=q.vol*math.sqrt(r.swaption.expiry);z=(r.forward-r.strike)/sd
        cdf=lambda x:.5*(1+math.erf(x/math.sqrt(2)))
        density=math.exp(-z*z/2)/math.sqrt(2*math.pi)
        expected=((r.strike-r.forward)*cdf(-z)+sd*density)*r.annuity*q.notional
        self.assertAlmostEqual(r.premium,expected,places=8)
        self.assertTrue(math.isfinite(r.delta) and math.isfinite(r.vega))
        self.assertTrue(math.isnan(r.other_model_vol));self.assertEqual(r.other_model_status,'UNAVAILABLE')
        self.assertIn('primary-model price and Greeks retained',out.narrative)
        with self.assertRaises(FICCError):swaps.black_from_normal(r.forward,r.strike,r.swaption.expiry,q.vol)

    def test_tiny_vol_both_directions_and_nonpositive_strike_keep_primary_result(self):
        for model in ('black','bachelier'):
            for payer in (True,False):
                r=swaps.price_swaption(swaps.Swaption(1.,5.,strike=.01,payer=payer),flat_curve(.04),vol=.00001,model=model)
                self.assertTrue(math.isfinite(r.premium));self.assertEqual(r.other_model_status,'UNAVAILABLE')
                self.assertTrue(math.isnan(r.other_model_vol))
        r=swaps.price_swaption(swaps.Swaption(1.,5.,strike=-.001),flat_curve(.01),vol=.008)
        self.assertEqual(r.other_model_status,'UNAVAILABLE');self.assertIn('forward and strike',r.other_model_reason)

    def test_successful_comparison_reprices_and_primary_input_errors_still_raise(self):
        for model,vol in [('black',.30),('bachelier',.008)]:
            r=swaps.price_swaption(swaps.Swaption(1.,5.),flat_curve(.04),vol=vol,model=model)
            other='black' if model=='bachelier' else 'bachelier'
            back=swaps.price_swaption(r.swaption,flat_curve(.04),vol=r.other_model_vol,model=other)
            self.assertAlmostEqual(r.premium,back.premium,places=6)
            self.assertEqual(r.other_model_status,'COMPUTED');self.assertEqual(r.other_model_reason,'')
        for model,vol in [('black',-.1),('bachelier',math.nan)]:
            with self.assertRaises(ValueError):swaps.price_swaption(swaps.Swaption(1.,5.),flat_curve(.04),vol=vol,model=model)
        with self.assertRaises(ValueError):swaps.price_swaption(swaps.Swaption(1.,5.,strike=-.001),flat_curve(.01),vol=.3,model='black')

    def test_auxiliary_solver_failure_is_local_and_unexpected_assertion_propagates(self):
        for error in (ValueError('bracket'),RuntimeError('convergence')):
            with patch.object(swaps,'black_from_normal',side_effect=error):
                self.assertEqual(fixture().report.other_model_status,'UNAVAILABLE')
        with patch.object(swaps,'black_from_normal',side_effect=AssertionError('programming fault')):
            with self.assertRaises(AssertionError):fixture()

    def test_flet_price_narrative_and_payload_keep_unavailable_comparison(self):
        out=fixture();seen={}
        def ai(page,**kw):seen.update(kw);seen['payload']=kw['payload_fn']();return ft.Text('injected AI')
        with patch.object(rates_page,'_curve',return_value=(out.panel,out.curve)),patch.object(rates_page,'analysis_panel',side_effect=ai):
            blocks=rates_page._run_option(Mock(),source='synthetic',kind='swaption',expiry_text='10y',tenor_text='10y',
                strike_pct=.1,payer=False,model='bachelier',vol_in=100,notional=1_000_000)
        text='\n'.join(str(c.value) for b in blocks for c in controls(b) if isinstance(c,ft.Text))
        self.assertIn('n/a',text);self.assertIn('primary-model price',text)
        self.assertEqual(seen['payload']['other_model_status'],'UNAVAILABLE')
        self.assertIsNone(seen['payload']['other_model_vol']);self.assertGreater(seen['payload']['premium'],0)
        self.assertIn('Other-model vol unavailable',seen['narrative'])


if __name__=='__main__':unittest.main()
