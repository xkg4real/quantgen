"""N-M1-09/N-M1-10: analytic baskets and injected Flet controls, no providers."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.quant.optimize import OBJECTIVES, optimize_portfolio, efficient_frontier
    from core.quant.risk import BasketStats
    from core.research.portfolio_analysis import PortfolioOutput, PortfolioRequest
    from core.research.portfolio_disclosure import portfolio_disclosure
    from ui import portfolio_page
import flet as ft


def basket(negative=False):
    sd = np.array([.1, .4, .2]) if negative else np.array([.1, .2, .3])
    return BasketStats(("ONE", "TWO", "THREE"), 101,
        np.array([-.02, -.05, 0.] if negative else [.12, .08, .04]),
        np.diag(sd**2), np.eye(3), np.zeros((100, 3)))


def output_fixture(objective="max_sharpe", cap=.5, negative=False):
    stats = basket(negative)
    q = PortfolioRequest(stats.symbols, source="synthetic", objective=objective, max_weight=cap)
    ports = {o: optimize_portfolio(stats, objective=o, max_weight=cap if o == objective else 1.)
             for o in OBJECTIVES}
    histories = tuple(SimpleNamespace(symbol=s, source="SYNTHETIC", note="fixture",
        first_date="2026-01-01", last_date="2026-04-11") for s in stats.symbols)
    return PortfolioOutput(q, histories, stats, ports,
        efficient_frontier(stats, points=8, n_cloud=30), "fixture narrative", "")


def controls(root):
    yield root
    for child in getattr(root, "controls", None) or []:
        yield from controls(child)
    content = getattr(root, "content", None)
    if isinstance(content, ft.Control):
        yield from controls(content)


class PortfolioScopeTests(unittest.TestCase):
    def setUp(self):
        p = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        p.start(); self.addCleanup(p.stop)

    def test_negative_excess_sharpe_keeps_known_solution_and_warns(self):
        p = optimize_portfolio(basket(True))
        np.testing.assert_allclose(p.weights, [0, 1, 0], atol=1e-7)
        self.assertAlmostEqual(p.sharpe, -.2)
        self.assertIn("No asset has positive estimated excess return", p.note)
        self.assertIn("higher volatility", p.note)
        self.assertTrue(p.converged)
        self.assertNotIn("No asset", optimize_portfolio(basket()).note)
        self.assertNotIn("No asset", optimize_portfolio(basket(True), objective="min_vol").note)

    def test_zero_excess_and_failed_solver_keep_warning_and_failure(self):
        stats = basket(); stats.mean_returns[:] = .03
        with patch("core.quant.optimize.minimize", return_value=SimpleNamespace(x=np.ones(3)/3, success=False)):
            p = optimize_portfolio(stats)
        self.assertIn("No asset has positive", p.note)
        self.assertIn("did not report convergence", p.note)
        self.assertFalse(p.converged)

    def test_analytic_min_vol_risk_parity_and_equal_weight_unchanged(self):
        stats = basket()
        for objective, raw in [("min_vol", 1/np.diag(stats.cov)),
                               ("risk_parity", 1/np.sqrt(np.diag(stats.cov))),
                               ("equal_weight", np.ones(3))]:
            with self.subTest(objective=objective):
                p = optimize_portfolio(stats, objective=objective)
                np.testing.assert_allclose(p.weights, raw/raw.sum(), atol=2e-5)

    def test_scope_reports_actual_cap_for_each_selected_objective(self):
        for selected in OBJECTIVES:
            with self.subTest(selected=selected):
                out = output_fixture(selected)
                scope = portfolio_disclosure(out.portfolios, selected)
                for name, p in out.portfolios.items():
                    row = scope["objectives"][name]
                    self.assertEqual(row["effective_max_weight"], .5 if name == selected else 1.)
                    self.assertEqual(row["role"], "selected" if name == selected else "comparison")
                    self.assertLessEqual(float(max(p.weights)), row["effective_max_weight"] + 1e-8)
                self.assertFalse(scope["frontier"]["uses_selected_cap"])
                self.assertEqual(scope["random_cloud"]["effective_max_weight"], 1.)
                self.assertTrue(scope["objectives"]["equal_weight"]["fixed_equal_weights"])
                # Genuine difference: the comparison can exceed the user's cap.
                other = "min_vol" if selected != "min_vol" else "max_sharpe"
                self.assertGreater(float(max(out.portfolios[other].weights)), .5)

    def test_infeasible_request_reports_adjustment_without_changing_bound(self):
        out = output_fixture(cap=.1)
        p = out.portfolios["max_sharpe"]
        self.assertEqual(p.requested_max_weight, .1)
        self.assertEqual(p.effective_max_weight, 1/3+1e-9)
        np.testing.assert_allclose(p.weights, np.ones(3)/3, atol=1e-7)
        scope = portfolio_disclosure(out.portfolios, "max_sharpe")
        self.assertTrue(scope["objectives"]["max_sharpe"]["cap_adjusted"])
        self.assertIn("adjusted", p.note)
        self.assertIn("10.00% requested", scope["summary"])

    def test_flet_exposes_comparison_warning_and_scope_in_actual_payload(self):
        out = output_fixture("min_vol", .1, negative=True)
        captured = {}
        def panel(page, **kw):
            captured.update(payload=kw["payload_fn"](), narrative=kw["narrative"])
            return ft.Text("injected AI panel")
        page = Mock(); page.run_thread.side_effect = lambda work: work()
        with patch.object(portfolio_page, "load_history", side_effect=out.histories), \
             patch.object(portfolio_page, "align_histories", return_value=out.stats), \
             patch.object(portfolio_page, "convention_warning", return_value=""), \
             patch.object(portfolio_page, "analysis_panel", side_effect=panel):
            root = portfolio_page.build_portfolio_page(page)
            inputs = root.controls[1].controls
            inputs[0].value = "ONE,TWO,THREE"
            inputs[2].value = "min_vol"
            inputs[3].value = ".1"
            next(c for c in inputs if isinstance(c, ft.Button)).on_click(None)
        text = "\n".join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
        self.assertIn("No asset has positive", text)  # max-Sharpe is not selected
        self.assertIn("100% per-asset bound", text)
        self.assertIn("10.00% requested", text)
        self.assertIn("selected", text)
        scope = captured["payload"]["constraint_scope"]
        self.assertEqual(scope["objectives"]["min_vol"]["requested_max_weight"], .1)
        self.assertEqual(scope["objectives"]["max_sharpe"]["effective_max_weight"], 1.)
        self.assertIn("No asset has positive", scope["objectives"]["max_sharpe"]["note"])
        self.assertIn("not a like-for-like", captured["narrative"])


if __name__ == "__main__":
    unittest.main()
