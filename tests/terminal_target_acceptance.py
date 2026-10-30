"""N-M1-11: distinguish terminal probability from crossing during a path."""
from datetime import date, timedelta
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.quant.history import History
    from core.quant import montecarlo, insights
    from ui import quant_lab_page
from core.research.runs import SessionResearch
from tests.portfolio_scope_acceptance import controls
import flet as ft


def history():
    return History("FIXTURE", "SYNTHETIC",
        tuple((date(2026, 1, 1)+timedelta(days=i)).isoformat() for i in range(40)),
        tuple(100+np.sin(i) for i in range(40)), note="injected fixture")


def fixed_result(target):
    # Half cross 2*spot and return to spot; half end at spot/2.
    shocks = np.zeros((200, 5))
    shocks[:100, :2] = [np.log(2), -np.log(2)]
    shocks[100:, 0] = np.log(.5)
    with patch.object(montecarlo, "_simulate_gbm", return_value=shocks):
        return montecarlo.run_monte_carlo(history(), model="gbm", n_paths=200,
            horizon_days=5, target=target, drift="zero", n_sample_paths=200)


class TerminalTargetTests(unittest.TestCase):
    def setUp(self):
        p=patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        p.start(); self.addCleanup(p.stop)

    def test_path_crossing_does_not_count_as_terminal_success(self):
        target = history().last*1.5
        result = fixed_result(target)
        self.assertEqual(float(np.mean(result.sample_paths.max(axis=1) >= target)), .5)
        self.assertEqual(result.prob_target, 0.)
        text = insights.narrate_monte_carlo(result)
        self.assertIn("finishing at or above", text)
        self.assertIn("after 5 sessions: 0%", text)
        self.assertNotIn("Probability of reaching", text)

    def test_below_spot_target_and_equality_use_the_same_terminal_rule(self):
        for target in (history().last*.75, history().last):
            with self.subTest(target=target):
                result = fixed_result(target)
                self.assertEqual(float(np.mean(result.sample_paths.max(axis=1) >= target)), 1.)
                self.assertEqual(result.prob_target, .5)
                self.assertIn("after 5 sessions: 50%", insights.narrate_monte_carlo(result))

    def test_absent_target_stays_absent(self):
        result = fixed_result(None)
        self.assertIsNone(result.prob_target)
        self.assertNotIn("finishing at or above", insights.narrate_monte_carlo(result))

    def test_flet_tile_and_actual_ai_payload_use_terminal_definition(self):
        target = history().last*1.5
        result = fixed_result(target)
        session = SessionResearch()
        captured = {}
        def panel(page, **kw):
            captured.update(payload=kw['payload_fn'](), narrative=kw['narrative'])
            return ft.Text("injected AI panel")
        page = Mock(); page.run_thread.side_effect = lambda work: work()
        with patch.object(quant_lab_page, 'session_for', return_value=session), \
             patch.object(quant_lab_page, 'load_history', return_value=history()), \
             patch.object(quant_lab_page, 'run_monte_carlo', return_value=result), \
             patch.object(quant_lab_page, '_lab_grade', return_value=None), \
             patch.object(quant_lab_page, 'analysis_panel', side_effect=panel):
            root = quant_lab_page.build_quant_lab_page(page)
            inputs = root.controls[1].controls
            inputs[0].value = "FIXTURE"; inputs[1].value = "synthetic"
            inputs[2].value = "gbm"; inputs[3].value = "zero"
            inputs[5].value = "5"; inputs[6].value = "200"; inputs[7].value = str(target)
            next(c for c in inputs if isinstance(c, ft.Button)).on_click(None)
        text = "\n".join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
        self.assertIn("P(terminal ≥ target)", text)
        self.assertNotIn("P(target)", text)
        self.assertEqual(captured['payload']['prob_target'], 0.)
        self.assertIn("terminal_price >= target", captured['payload']['prob_target_basis'])
        self.assertEqual(session.runs()[0]['verdict'], 'NOT_RUN')


if __name__ == '__main__':
    unittest.main()
