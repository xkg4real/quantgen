"""Synthetic M3-N08 checks: simulation/revaluation parameter consistency."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.ficc import data, ratesim
    from core.ficc.bonds import Bond, price_from_curve
    from core.ficc.curves import curve_from_snapshot, flat_curve
    from core.ficc.swaps import Swap
    from core.research.rates_analysis import RatesRequest, execute_rates
    from ui import rates_page
import flet as ft


PARAMS = ratesim.ShortRateParams("vasicek", .2, .03, .01, .03)
BOND = Bond(coupon=.04, maturity=5)
SWAP = Swap(tenor=5, fixed_rate=.04)


def fixture():
    return ratesim.RateSimResult(
        model="vasicek", params=PARAMS, horizon=.5, n_paths=3,
        terminal=np.array([.01, .03, .05]))


def revalue(params, sim, kind, curve=None):
    return ratesim.horizon_pv_distribution(
        params, sim, kind=kind, curve=curve,
        **{kind: BOND if kind == "bond" else SWAP})


class RatesRevaluationParamsTests(unittest.TestCase):
    def setUp(self):
        for target in ("requests.sessions.Session.request", "socket.socket.connect",
                       "core.ficc.data._fred_fetch", "core.ficc.data._yf_fetch"):
            guard = patch(target, side_effect=AssertionError("no provider/network"))
            guard.start()
            self.addCleanup(guard.stop)

    def assertSamePV(self, a, b):
        np.testing.assert_array_equal(a.pvs, b.pvs)
        for name in ("mean", "p05", "p95", "var95", "cvar95", "note"):
            self.assertEqual(getattr(a, name), getattr(b, name), name)

    def test_each_calculation_mismatch_fails_before_curve_or_path_pricing(self):
        changed = {"model": "cir", "kappa": .7, "theta": .08,
                   "sigma": .02, "r0": .06}
        for kind in ("bond", "swap"):
            for name, value in changed.items():
                with self.subTest(kind=kind, field=name), \
                     patch.object(ratesim, "flat_curve", side_effect=AssertionError("priced")), \
                     patch.object(ratesim, "_model_curve", side_effect=AssertionError("priced")):
                    sim = replace(fixture(), terminal=None)
                    with self.assertRaisesRegex(ValueError, "different: " + name):
                        revalue(replace(PARAMS, **{name: value}), sim, kind)
            with self.subTest(kind=kind, field="one-ulp kappa"):
                with self.assertRaisesRegex(ValueError, "different: kappa"):
                    revalue(replace(PARAMS, kappa=np.nextafter(.2, 1.0)), fixture(), kind)

    def test_equal_new_params_and_note_only_changes_preserve_all_values(self):
        for kind in ("bond", "swap"):
            for curve in (None, flat_curve(.03)):
                with self.subTest(kind=kind, default_curve=curve is None):
                    sim = fixture()
                    baseline = revalue(PARAMS, sim, kind, curve)
                    self.assertSamePV(baseline, revalue(replace(PARAMS), sim, kind, curve))
                    self.assertSamePV(baseline, revalue(
                        replace(PARAMS, note="description only"),
                        replace(sim, params=replace(PARAMS, note="another description")),
                        kind, curve))

    def test_recorded_pv_and_loss_quantile_values_are_unchanged(self):
        curve = flat_curve(.03)
        expected = {
            "bond": ([1120703.3315827162, 1061636.0252331055, 1005844.886573232],
                     33617.2361375428, 39196.350003530155),
            "swap": ([-119882.57560776983, -60241.7996243344, -3908.158314276544],
                     70259.73496252048, 76223.81256086403),
        }
        for kind, (pvs, var, cvar) in expected.items():
            with self.subTest(kind=kind):
                result = revalue(PARAMS, fixture(), kind, curve)
                np.testing.assert_allclose(result.pvs, pvs, rtol=0, atol=1e-8)
                self.assertAlmostEqual(result.var95, var, places=7)
                self.assertAlmostEqual(result.cvar95, cvar, places=7)
                today = (price_from_curve(BOND, curve) * BOND.notional / BOND.face
                         if kind == "bond" else SWAP.notional * (
                             1 - curve.df(5) - .04 * curve.annuity(5, 1)))
                losses = today - np.array(pvs)
                cutoff = np.percentile(losses, 95)
                self.assertAlmostEqual(result.var95, max(0, cutoff), places=7)
                self.assertAlmostEqual(result.cvar95,
                                       max(0, np.mean(losses[losses >= cutoff])), places=7)

    def test_hull_white_normalization_uses_final_params_with_or_without_curve(self):
        original = replace(PARAMS, model="hull_white", r0=.01)
        for curve in (None, flat_curve(.04)):
            sim = ratesim.simulate(original, horizon=.5, n_paths=100,
                                   steps_per_year=2, curve=curve, seed=7)
            for kind in ("bond", "swap"):
                with self.subTest(kind=kind, default_curve=curve is None):
                    result = revalue(sim.params, sim, kind, curve)
                    self.assertTrue(np.isfinite(result.pvs).all())
                    self.assertEqual(result.pvs.size, 100)
                    if curve is not None:
                        self.assertNotEqual(original.r0, sim.params.r0)
                        self.assertAlmostEqual(sim.params.r0, curve.inst_fwd(0))
                        with self.assertRaisesRegex(ValueError, "different: r0"):
                            revalue(original, sim, kind, curve)

    def test_native_service_and_flet_use_simulation_params_in_all_models(self):
        panel = data.synthetic_curve_panel(days=40, seed=19)
        series = data.synthetic_series("SOFR", days=60, kind="rate")
        curve = curve_from_snapshot(panel.latest())
        for model in ratesim.MODELS:
            for kind in ("bond", "swap"):
                with self.subTest(model=model, kind=kind):
                    original = replace(PARAMS, model=model, r0=.01)
                    request = RatesRequest(tool="sim", source="synthetic", model=model,
                                           horizon=.5, n_paths=100, instrument=kind, tenor="5y")
                    with patch.object(ratesim, "calibrate", return_value=original):
                        output = execute_rates(request, curve_loader=lambda **kw: panel,
                                               rate_loader=lambda *a, **kw: series)
                    self.assertIsNotNone(output.horizon_pv)
                    if model == "hull_white":
                        self.assertNotEqual(original.r0, output.report.params.r0)
                    captures = []
                    def analysis(_page, *, kind, narrative, payload_fn, sections=None):
                        captures.append((kind, narrative, payload_fn()))
                        return ft.Text(narrative)
                    with patch.object(rates_page, "load_short_rate", return_value=series), \
                         patch.object(rates_page, "_curve", return_value=(panel, curve)), \
                         patch.object(rates_page, "calibrate", return_value=original), \
                         patch.object(rates_page.fcharts, "rate_fan_chart", return_value=ft.Text("chart")), \
                         patch.object(rates_page.fcharts, "horizon_pv_hist", return_value=ft.Text("hist")), \
                         patch.object(rates_page, "analysis_panel", side_effect=analysis), \
                         patch.object(rates_page, "stat", wraps=rates_page.stat) as stat:
                        blocks = rates_page._run_sim(
                            Mock(), source="synthetic", model=model, horizon=.5, n_paths=100,
                            threshold_pct=None, instrument=kind, instr_tenor_text="5y", coupon_pct=4)
                    self.assertTrue(blocks)
                    self.assertEqual(len(captures), 1)
                    tag, narrative, payload = captures[0]
                    self.assertEqual(tag, "rates_simulation")
                    self.assertEqual(narrative, output.narrative)
                    self.assertEqual(payload["params"]["r0"], output.report.params.r0)
                    for name in ("mean", "p05", "p95", "var95", "cvar95", "note"):
                        self.assertEqual(payload["horizon_pv"][name],
                                         getattr(output.horizon_pv, name), name)
                    stats = {c.args[0]: c.args[1] for c in stat.call_args_list}
                    self.assertEqual(stats["VaR 95 (loss)"], rates_page._money(output.horizon_pv.var95))
                    self.assertEqual(stats["CVaR 95"], rates_page._money(output.horizon_pv.cvar95))


if __name__ == "__main__":
    unittest.main()
