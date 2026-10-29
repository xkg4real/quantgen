"""PT-04: synthetic partial-FRED fixtures; no provider or research files."""
import math
from unittest.mock import patch
import unittest
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import curves, data, bonds
from core.ficc.common import FICCError, UST_TENORS


def panel(tenors=(.25,.5,1.,2.,3.,5.,7.,10.)):
    values=np.linspace(.04,.045,len(tenors))
    return data.CurvePanel(source='FRED',dates=('2026-10-27','2026-10-28'),tenors=tenors,
                          yields=np.vstack([values-.0001,values]), note='Fixture partial curve')


class PartialCurveTests(unittest.TestCase):
    def test_5s30s_is_not_relabelled_10y_and_local_metrics_survive(self):
        p=panel();r=curves.analyze_curve(p)
        self.assertTrue(math.isnan(r.descriptors['5s30s']))
        self.assertAlmostEqual(r.descriptors['2s10s'],p.yields[-1,-1]-p.yields[-1,3])
        self.assertIn('partial',r.shape)
        self.assertTrue(math.isnan(r.curve.table()[-1]['fwd_1y']))

    def test_bootstrap_and_both_fits_cannot_invent_long_end(self):
        for method in ('bootstrap','nelson_siegel','svensson'):
            with self.subTest(method=method):
                c=curves.curve_from_snapshot(panel().latest(),method=method)
                self.assertLessEqual(max(c.tenors),10)
                self.assertTrue(math.isfinite(c.par_rate(10)))
                with self.assertRaises(FICCError):c.par_rate(30)
                with self.assertRaises(FICCError):c.df(np.array([2.,30.]))

    def test_bumps_and_scenarios_preserve_coverage(self):
        c=curves.curve_from_snapshot(panel().latest())
        variants=[c.shifted(10),c.key_rate_shifted(5,10),bonds.shocked_curve(c,bonds.SCENARIO_SHOCKS['2y-5y-10y fly'])]
        for moved in variants:
            self.assertEqual(moved.observed_max_tenor,10)
            self.assertTrue(math.isfinite(moved.df(5)))
            with self.assertRaises(FICCError):moved.df(20)

    def test_partial_fred_loader_warns_without_network(self):
        p=panel();rows={i:[(d,float(y)*100) for d,y in zip(p.dates,p.yields[:,k])]
                       for k,(i,t) in enumerate(zip(('DGS3MO','DGS6MO','DGS1','DGS2','DGS3','DGS5','DGS7','DGS10'),p.tenors))}
        # This test exercises assembly, not the independent minimum-history requirement.
        with patch.object(data,'_provider_rows',return_value=(rows,{})),patch.object(data,'_MIN_OBS',2):
            loaded=data._treasury_from_fred(2)
        self.assertIn('DGS30',loaded.note)
        self.assertIn('metrics and prices are unavailable',loaded.note)

    def test_full_and_synthetic_curves_keep_existing_numbers(self):
        p=panel(UST_TENORS);c=curves.curve_from_snapshot(p.latest())
        legacy=curves.bootstrap_par_curve(p.tenors,p.yields[-1])
        np.testing.assert_array_equal(c.zeros,legacy.zeros)
        self.assertIsNone(c.observed_max_tenor)
        synthetic=data.synthetic_curve_panel(days=2).latest()
        self.assertIsNone(curves.curve_from_snapshot(synthetic).observed_max_tenor)

    def test_rates_render_and_json_payload_withhold_unobserved_values(self):
        from ui import rates_page
        captured={}
        def analysis(*args,**kwargs):
            captured.update(kwargs)
            import flet as ft
            return ft.Text('fixture analysis')
        with patch.object(rates_page,'load_treasury_curve',return_value=panel()),patch.object(rates_page,'analysis_panel',side_effect=analysis):
            blocks=rates_page._run_curve(object(),source='fred',method='bootstrap',lookback=1)
        self.assertTrue(blocks)
        self.assertEqual(rates_page._pct(math.nan),'n/a')
        self.assertEqual(rates_page._bp(math.nan),'n/a')
        # The AI/explanation payload must use JSON null, not a plausible 30y value or NaN.
        import json
        payload = captured['payload_fn']()
        self.assertIsNone(payload['descriptors']['5s30s'])
        json.dumps(payload,allow_nan=False)


if __name__=='__main__':unittest.main()
