"""DIDM-4: Stage 0 simulation. The estimators recover known parameters on synthetic data, the registered
thresholds are the ones in PREREG_V0, the verdict rule behaves as written, and a seed fixes every number.

The tests use small toy worlds with large effects. They do not run the registered grid (that is
tools/didm/stage0_report.py) and they use no market data, no network and no model."""
from __future__ import annotations

import ast
import io
import re
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path

import numpy as np

from core.didm.models import har_x, lp
from core.didm.sim import dgp, power, recovery
from tools.didm import stage0_report

ROOT = Path(__file__).resolve().parents[1]
TOY = dgp.Params(n_units=40, n_dates=400, event_rate=0.10, theta0=300 * dgp.BP, delta=0.4, half_life=1.0,
                 phi_total=300 * dgp.BP, psi=20 * dgp.BP, gamma=0.6, eta=0.4, links=2, burn=60)
TOY_SEED = 7


class LocalProjection(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(1)
        self.x = rng.standard_normal((300, 12, 2))
        self.beta = np.array([0.5, -0.2])
        self.noise = 0.01 * rng.standard_normal((300, 12))
        self.date_effect = rng.standard_normal((300, 1))

    def test_recovers_coefficients_and_ignores_date_effects(self):
        r = self.x @ self.beta + self.noise
        a = lp.fit_lp(r, self.x, ("a", "b"), horizons=(0,))
        b = lp.fit_lp(r + 5.0 * self.date_effect, self.x, ("a", "b"), horizons=(0,))
        self.assertAlmostEqual(a.coef("a", 0), 0.5, delta=0.005)
        self.assertAlmostEqual(a.coef("b", 0), -0.2, delta=0.005)
        np.testing.assert_allclose(a.fits[0].coef, b.fits[0].coef, atol=1e-10)
        lo, hi = a.interval("a", 0)
        self.assertLess(lo, a.coef("a", 0))
        self.assertLess(a.coef("a", 0), hi)

    def test_cumulative_returns(self):
        r = np.arange(12.0).reshape(6, 2)
        out = lp.cumulative_returns(r, 2)
        self.assertEqual(out.shape, (4, 2))
        np.testing.assert_allclose(out[0], r[0] + r[1] + r[2])
        np.testing.assert_allclose(out[3], r[3] + r[4] + r[5])
        np.testing.assert_allclose(lp.cumulative_returns(r, 0), r)

    def test_delayed_response_shows_up_at_longer_horizons(self):
        impulse = self.x[..., 0]
        r = 1.0 * impulse + self.noise
        r[1:] += 0.5 * impulse[:-1]
        fit = lp.fit_lp(r, self.x[..., :1], ("s",), horizons=(0, 1))
        self.assertAlmostEqual(fit.coef("s", 0), 1.0, delta=0.05)
        self.assertAlmostEqual(fit.coef("s", 1), 1.5, delta=0.08)
        share = lp.delayed_share(fit, "s", 0, 1)
        self.assertAlmostEqual(share.value, 1 / 3, delta=0.03)
        self.assertGreater(share.se, 0)

    def test_bad_inputs_are_refused(self):
        r = self.x @ self.beta
        with self.assertRaises(lp.ModelError):
            lp.fit_lp(r, np.concatenate([self.x, self.x[..., :1]], axis=2), ("a", "b", "c"), horizons=(0,))
        with self.assertRaises(lp.ModelError):
            lp.fit_lp(r, self.x, ("a", "a"), horizons=(0,))
        with self.assertRaises(lp.ModelError):
            lp.fit_lp(r, self.x, ("a", "b"), horizons=(500,))
        bad = r.copy()
        bad[3, 3] = np.nan
        with self.assertRaises(lp.ModelError):
            lp.fit_lp(bad, self.x, ("a", "b"), horizons=(0,))

    def test_hac_lag_rule_and_bartlett(self):
        self.assertEqual([lp.hac_lags(h) for h in (0, 1, 5, 20)], [0, 2, 8, 30])
        series = np.array([[1.0], [2.0], [3.0]])
        self.assertAlmostEqual(float(lp.bartlett_cov(series, 0)[0, 0]), 14.0)
        self.assertAlmostEqual(float(lp.bartlett_cov(series, 1)[0, 0]), 14.0 + 0.5 * 2 * 8.0)

    def test_diebold_mariano(self):
        rng = np.random.default_rng(2)
        good = rng.random(400)
        stat, p = lp.dm_test(good + 0.2 + 0.05 * rng.standard_normal(400), good)
        self.assertGreater(stat, 5)
        self.assertLess(p, 0.001)
        stat, p = lp.dm_test(good, good + 0.2)
        self.assertGreater(p, 0.99)
        self.assertEqual(lp.dm_test(good, good), (0.0, 0.5))
        with self.assertRaises(lp.ModelError):
            lp.dm_test(good[:5], good[:5])


class HarX(unittest.TestCase):
    def test_features(self):
        x = np.arange(60.0).reshape(30, 2)
        f = har_x.har_features(x)
        self.assertTrue(np.isnan(f[20, 0, 2]) and np.isnan(f[3, 0, 1]))
        self.assertAlmostEqual(f[21, 0, 2], x[:22, 0].mean())
        self.assertAlmostEqual(f[29, 1, 1], x[25:30, 1].mean())
        np.testing.assert_allclose(f[..., 0], x)

    def test_recovers_coefficients_on_a_simulated_panel(self):
        panel = dgp.simulate(replace(TOY, n_dates=1500), np.random.default_rng(3))
        fit = har_x.fit_har_x(panel.log_rv, np.stack([panel.abs_shock, panel.entropy], axis=2), ("gamma", "eta"))
        self.assertAlmostEqual(fit.value("gamma"), 0.6, delta=0.06)
        self.assertAlmostEqual(fit.value("eta"), 0.4, delta=0.05)
        self.assertAlmostEqual(fit.value("har_d"), 0.35, delta=0.02)
        actual, pred = har_x.predict(fit, panel.log_rv, np.stack([panel.abs_shock, panel.entropy], axis=2))
        self.assertEqual(actual.shape, pred.shape)
        self.assertLess(((actual - pred) ** 2).mean(), actual.var())

    def test_shape_errors(self):
        with self.assertRaises(lp.ModelError):
            har_x.fit_har_x(np.zeros((10, 3)))
        with self.assertRaises(lp.ModelError):
            har_x.fit_har_x(np.zeros((60, 3)), np.zeros((59, 3, 1)), ("g",))


class World(unittest.TestCase):
    def test_kernel_puts_the_stated_share_after_day_zero(self):
        k = dgp.kernel(0.005, 0.3, 1.0)
        self.assertEqual(len(k), 21)
        self.assertAlmostEqual(k[0], 0.005)
        self.assertAlmostEqual(k[1:].sum() / k.sum(), 0.3)
        self.assertGreater(k[1], k[2])
        self.assertAlmostEqual(dgp.kernel(0.005, 0.0, 1.0)[1:].sum(), 0.0)

    def test_truth_table(self):
        t = dgp.truth(TOY, (0, 1, 5, 20))
        self.assertAlmostEqual(t["theta_h0"], 0.03)
        self.assertAlmostEqual(t["theta_h20"], 0.03 / 0.6)
        self.assertAlmostEqual(t["phi_h20"], 0.03)
        self.assertAlmostEqual(t["phi_h0"], 0.015)
        self.assertEqual((t["delta"], t["gamma"], t["eta"]), (0.4, 0.6, 0.4))

    def test_same_seed_same_world_and_other_seed_other_world(self):
        a = dgp.simulate(TOY, np.random.default_rng(TOY_SEED))
        b = dgp.simulate(TOY, np.random.default_rng(TOY_SEED))
        c = dgp.simulate(TOY, np.random.default_rng(TOY_SEED + 1))
        np.testing.assert_array_equal(a.returns, b.returns)
        np.testing.assert_array_equal(a.log_rv, b.log_rv)
        self.assertFalse(np.array_equal(a.returns, c.returns))
        self.assertEqual(a.returns.shape, (400, 40))

    def test_shocks_are_zero_without_an_event_and_bounded(self):
        panel = dgp.simulate(TOY, np.random.default_rng(TOY_SEED))
        self.assertTrue((np.abs(panel.shock) <= 1.0).all())
        self.assertTrue((np.abs(panel.shock) <= np.abs(panel.shock_nocred) + 1e-12).all())
        self.assertAlmostEqual((panel.shock != 0).mean(), 0.10, delta=0.02)
        self.assertTrue(((panel.entropy > 0) <= (panel.shock_nocred != 0) | (panel.entropy > 0)).all())
        self.assertTrue((panel.entropy <= np.log(3) + 1e-9).all())

    def test_bad_parameters_are_refused(self):
        for change in (dict(delta=1.0), dict(event_rate=0.0), dict(half_life=0.0), dict(n_dates=50),
                       dict(har=(0.5, 0.4, 0.2)), dict(n_units=3)):
            with self.subTest(change=change), self.assertRaises(dgp.SimError):
                replace(TOY, **change)


class Recovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell = recovery.run_cell("T toy", TOY, reps=30, seed=TOY_SEED, cell_index=0)

    def test_known_parameters_come_back(self):
        for name in ("theta_h0", "theta_h1", "phi_h5", "psi", "gamma", "eta", "har_d"):
            with self.subTest(name):
                e = self.cell.estimates[name]
                self.assertLess(abs(e.rel_bias), 0.10)
        self.assertAlmostEqual(self.cell.estimates["delta"].mean, 0.4, delta=0.08)

    def test_intervals_cover_and_large_effects_are_detected(self):
        for name in ("theta_h0", "theta_h5", "gamma", "eta"):
            with self.subTest(name):
                e = self.cell.estimates[name]
                self.assertGreaterEqual(e.coverage90, 0.70)       # 30 replications: a loose band
                self.assertEqual(e.reject05, 1.0)
        placebo = self.cell.estimates["phi_placebo_h5"]
        self.assertEqual(placebo.truth, 0.0)
        self.assertIsNone(placebo.rel_bias)
        self.assertLess(placebo.reject05, 0.35)

    def test_misspecified_models_lose_when_effects_are_large(self):
        self.assertGreaterEqual(self.cell.dm_reject["dm_har_without_news"], 0.8)
        self.assertGreater(self.cell.qlike_gain_pct, 0.0)
        # The toy test window is short (120 dates), so the network and credibility comparisons get a
        # world where those two layers are very strong.
        strong = replace(TOY, n_dates=800, phi_total=1500 * dgp.BP, theta0=600 * dgp.BP,
                         credibility_beta=(1.0, 1.0))
        cell = recovery.run_cell("T strong", strong, reps=12, seed=TOY_SEED, cell_index=2)
        self.assertGreaterEqual(cell.dm_reject["dm_no_network"], 0.8)
        self.assertGreaterEqual(cell.dm_reject["dm_no_credibility"], 0.8)

    def test_overconfident_scorer_biases_the_response(self):
        cell = recovery.run_cell("T over", replace(TOY, overconfidence=2.0), reps=30, seed=TOY_SEED, cell_index=1)
        self.assertLess(cell.estimates["theta_h0"].rel_bias, -0.10)

    def test_replications_are_seeded_by_seed_cell_and_index(self):
        again = recovery.run_cell("T toy", TOY, reps=30, seed=TOY_SEED, cell_index=0)
        self.assertEqual(again.estimates, self.cell.estimates)
        other = recovery.run_cell("T toy", TOY, reps=30, seed=TOY_SEED + 1, cell_index=0)
        self.assertNotEqual(other.estimates["theta_h0"].mean, self.cell.estimates["theta_h0"].mean)


def summary(name: str, truth: float, mean: float, mc_se: float, coverage: float, reject: float):
    return recovery.ParamSummary(name, truth, mean, mc_se * 10, mc_se, None if truth == 0 else (mean - truth) / truth,
                                 coverage, reject, reject, mc_se)


def fake_cells(**overrides) -> list[recovery.CellSummary]:
    """Cells A and C where everything passes, unless an override (name -> ParamSummary fields) says otherwise."""
    cells = []
    for label, params in power.GRID_V0:
        if power.cell_key(label) not in ("A", "C"):
            continue
        est = {}
        for name in (*power.RECOVERY_PARAMS, "delta_h5", "phi_placebo_h5"):
            est[name] = summary(name, 1.0, 1.01, 0.01, 0.90, 0.95)
        for name, (cell, fields) in overrides.items():
            if cell == power.cell_key(label):
                est[name] = summary(name, *fields)
        dm = {"dm_no_network": 0.9, "dm_no_credibility": 0.9, "dm_har_without_news": 0.9}
        cells.append(recovery.CellSummary(label, params, 500, est, dm, 3.0, 2500.0))
    return cells


class RegisteredRule(unittest.TestCase):
    def test_thresholds_are_the_registered_ones(self):
        self.assertEqual(power.MAX_REL_BIAS, 0.10)
        self.assertEqual(power.COVERAGE_BAND, (0.85, 0.95))
        self.assertEqual(power.MIN_POWER, 0.80)
        self.assertEqual(power.DM_ALPHA, 0.05)
        self.assertEqual((power.REPORT_SEED, power.REPORT_REPS), (20261124, 500))
        prereg = (ROOT / "docs" / "didm" / "PREREG_V0.md").read_text(encoding="utf-8")
        self.assertIn("상대 편의 < 10%, 90% 구간 포함률 85~95%, 계획 표본에서 검정력 ≥ 80%", prereg)

    def test_grid_is_the_committed_one(self):
        self.assertEqual([power.cell_key(label) for label, _ in power.GRID_V0], list("ABCDEFGHIJ"))
        a = dict(power.GRID_V0)["A one-type central N200"]
        self.assertEqual((a.n_units, a.n_dates, a.event_rate), (200, 2500, 0.005))
        self.assertEqual((a.theta0, a.delta, a.phi_total, a.gamma, a.eta), (0.005, 0.15, 0.001, 0.10, 0.05))
        self.assertEqual(a.sigma_daily, 0.02)
        self.assertEqual(len(power.ATTEMPTS), 1)

    def test_all_pass_is_go(self):
        result = power.verdict(power.checks(fake_cells()))
        self.assertEqual((result.line, result.reasons), ("GO", ()))

    def test_core_layer_without_power_is_no_go(self):
        cells = fake_cells(theta_h0=("A", (1.0, 1.0, 0.01, 0.90, 0.50)))
        self.assertEqual(power.verdict(power.checks(cells)).line, "NO-GO")
        cells = fake_cells(gamma=("A", (1.0, 1.3, 0.01, 0.90, 0.95)))      # 30% bias, far beyond MC error
        self.assertEqual(power.verdict(power.checks(cells)).line, "NO-GO")

    def test_other_layer_without_power_is_revise(self):
        cells = fake_cells(delta=("A", (0.15, 0.15, 0.01, 0.90, 0.10)))
        result = power.verdict(power.checks(cells))
        self.assertEqual(result.line, "REVISE")
        self.assertTrue(any("delta" in r and "power" in r for r in result.reasons))

    def test_coverage_outside_the_band_is_revise(self):
        for coverage in (0.84, 0.96):
            cells = fake_cells(theta_h5=("C", (1.0, 1.0, 0.01, coverage, 0.95)))
            self.assertEqual(power.verdict(power.checks(cells)).line, "REVISE", coverage)
        for coverage in (0.85, 0.95):
            cells = fake_cells(theta_h5=("C", (1.0, 1.0, 0.01, coverage, 0.95)))
            self.assertEqual(power.verdict(power.checks(cells)).line, "GO", coverage)

    def test_bias_rule(self):
        self.assertEqual(power.bias_status(0.05, 0.05, 0.001), "pass")
        self.assertEqual(power.bias_status(0.20, 0.20, 0.01), "fail")
        self.assertEqual(power.bias_status(0.20, 0.20, 0.50), "undetermined")
        self.assertEqual(power.bias_status(None, 0.20, 0.01), "pass")
        cells = fake_cells(phi_h20=("C", (1.0, 1.3, 0.5, 0.90, 0.95)))
        self.assertEqual(power.verdict(power.checks(cells)).line, "REVISE")     # undetermined is not a pass

    def test_misspecified_model_that_does_not_lose_is_revise(self):
        cells = fake_cells()
        cells[1] = replace(cells[1], dm_reject=dict(cells[1].dm_reject, dm_no_network=0.3))
        self.assertEqual(power.verdict(power.checks(cells)).line, "REVISE")

    def test_sensitivity_cell_is_not_gated(self):
        cells = fake_cells()
        g_label, g_params = power.GRID_V0[6]
        bad = {n: summary(n, 1.0, 2.0, 0.001, 0.0, 0.0) for n in (*power.RECOVERY_PARAMS, "delta_h5", "phi_placebo_h5")}
        cells.append(recovery.CellSummary(g_label, g_params, 500, bad, cells[0].dm_reject, 0.0, 0.0))
        self.assertEqual(power.verdict(power.checks(cells)).line, "GO")

    def test_event_count_formula_matches_the_research_note(self):
        sigma_car = 0.02 * 5 ** 0.5
        self.assertAlmostEqual(power.events_needed(0.01, sigma_car), 157, delta=1)
        self.assertAlmostEqual(power.events_needed(0.005, sigma_car), 627, delta=2)
        self.assertAlmostEqual(power.normal_power(2.8, 1.0), 0.80, delta=0.005)
        self.assertAlmostEqual(power.normal_power(0.0, 1.0), 0.05, delta=0.001)


TINY_GRID = (("A tiny", TOY), ("C tiny", replace(TOY, event_rate=0.2)))


class ReportTool(unittest.TestCase):
    def test_same_seed_gives_the_same_report_and_ends_with_the_verdict_line(self):
        first, verdict = stage0_report.render(stage0_report.run(5, 6, 1, TINY_GRID), 5, 6)
        second, _ = stage0_report.render(stage0_report.run(5, 6, 1, TINY_GRID), 5, 6)
        self.assertEqual(first, second)
        self.assertRegex(first.strip().splitlines()[-1], r"^STAGE0: (GO|REVISE|NO-GO)$")
        self.assertIn(verdict.line, ("GO", "REVISE", "NO-GO"))
        for word in ("rel. bias %", "coverage90 %", "reject 5% %"):
            self.assertIn(word, first)
        other, _ = stage0_report.render(stage0_report.run(6, 6, 1, TINY_GRID), 6, 6)
        self.assertNotEqual(first, other)

    def test_worker_processes_do_not_change_the_numbers(self):
        serial = stage0_report.run(5, 6, 1, TINY_GRID)
        parallel = stage0_report.run(5, 6, 2, TINY_GRID)
        self.assertEqual([c.estimates for c in serial], [c.estimates for c in parallel])

    def test_output_folder_inside_the_repository_is_refused(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(stage0_report.main(["--seed", "1", "--out", str(ROOT / "docs" / "x"), "--reps", "2"]), 2)
        self.assertIn("outside the repository", err.getvalue())
        self.assertFalse((ROOT / "docs" / "x").exists())

    def test_json_output_is_complete(self):
        cells = stage0_report.run(5, 4, 1, TINY_GRID)
        _, verdict = stage0_report.render(cells, 5, 4)
        text = stage0_report.to_json(cells, 5, 4, verdict)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "stage0.json").write_text(text, encoding="utf-8")
        self.assertTrue(re.search(r'"verdict": "(GO|REVISE|NO-GO)"', text))
        self.assertIn('"theta_h0"', text)


class Boundaries(unittest.TestCase):
    FILES = ("core/didm/models/lp.py", "core/didm/models/har_x.py", "core/didm/sim/dgp.py",
             "core/didm/sim/recovery.py", "core/didm/sim/power.py", "tools/didm/stage0_report.py")
    BANNED = ("data", "requests", "urllib", "http", "socket", "time", "datetime", "pandas", "scipy", "statsmodels",
              "yfinance", "core.gateway", "core.credentials", "core.engine", "core.didm.store", "core.didm.ingest")

    def test_simulation_code_reaches_no_data_source_network_or_clock(self):
        for rel in self.FILES:
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    for banned in self.BANNED:
                        self.assertFalse(name == banned or name.startswith(banned + "."), f"{rel} imports {name}")


if __name__ == "__main__":
    unittest.main()
