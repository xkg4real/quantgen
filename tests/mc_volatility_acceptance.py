"""N-M1-03 display semantics on the same synthetic history for all four models."""
from datetime import date, timedelta
from functools import lru_cache
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.quant.history import History
    from core.quant.montecarlo import run_monte_carlo, MODELS
    from core.quant import insights
    from ui import quant_lab_page
from core.research.mc_disclosure import volatility_disclosure
from core.research.runs import SessionResearch
from tests.portfolio_scope_acceptance import controls
import flet as ft


def history():
    rng=np.random.default_rng(7303)
    r=rng.normal(0,.005,300);r[-40:]*=4
    return History('VOL_FIXTURE','SYNTHETIC',
        tuple((date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(301)),
        tuple(100*np.exp(np.r_[0,r.cumsum()])),note='synthetic volatility fixture')


@lru_cache
def result(model):
    return run_monte_carlo(history(),model=model,n_paths=200,horizon_days=20,drift='zero',seed=7)


class McVolatilityTests(unittest.TestCase):
    def setUp(self):
        p=patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden'))
        p.start();self.addCleanup(p.stop)

    def test_sample_conditional_and_horizon_values_are_not_interchanged(self):
        sample=float(np.std(history().log_returns(),ddof=1)*np.sqrt(252))
        for model in MODELS:
            with self.subTest(model=model):
                mc=result(model);info=volatility_disclosure(mc)
                self.assertEqual(info['value'],mc.sigma_annual)
                self.assertEqual(info['annualization_sessions'],252)
                if model=='garch_t':
                    self.assertEqual(info['basis'],'next_session_conditional')
                    self.assertEqual(info['value'],mc.garch.cond_vol_last)
                    self.assertEqual(info['horizon_average_annualized'],mc.garch_horizon_vol)
                    self.assertGreater(abs(info['value']-sample),.1)
                    self.assertGreater(abs(info['value']-info['horizon_average_annualized']),.001)
                else:
                    self.assertEqual(info['basis'],'historical_sample_log_returns')
                    self.assertEqual(info['value'],sample)
                    self.assertIsNone(info['horizon_average_annualized'])

    def test_narrative_names_next_session_and_horizon_average(self):
        text=insights.narrate_monte_carlo(result('garch_t'))
        self.assertIn('next session (annualized)',text)
        self.assertIn('20-session average forecast vol (annualized)',text)
        self.assertNotIn('vol today',text)
        for model in ('gbm','jump','bootstrap'):
            self.assertIn('historical sample log-return volatility',insights.narrate_monte_carlo(result(model)))

    def test_flet_tiles_and_actual_ai_payload_match_each_model(self):
        for model in MODELS:
            with self.subTest(model=model):
                captured={};mc=result(model)
                def panel(page,**kw):
                    captured.update(kw['payload_fn']())
                    return ft.Text('injected AI panel')
                page=Mock();page.run_thread.side_effect=lambda work:work()
                with patch.object(quant_lab_page,'session_for',return_value=SessionResearch()), \
                     patch.object(quant_lab_page,'load_history',return_value=history()), \
                     patch.object(quant_lab_page,'run_monte_carlo',return_value=mc), \
                     patch.object(quant_lab_page,'_lab_grade',return_value=None), \
                     patch.object(quant_lab_page,'analysis_panel',side_effect=panel):
                    root=quant_lab_page.build_quant_lab_page(page);inputs=root.controls[1].controls
                    inputs[0].value='VOL_FIXTURE';inputs[1].value='synthetic'
                    inputs[2].value=model;inputs[3].value='zero';inputs[5].value='20';inputs[6].value='200'
                    next(c for c in inputs if isinstance(c,ft.Button)).on_click(None)
                texts=[str(c.value) for c in controls(root) if isinstance(c,ft.Text)]
                info=volatility_disclosure(mc)
                self.assertIn(info['label'],texts)
                self.assertNotIn('Vol (ann.)',texts)
                self.assertEqual(captured['volatility_definition'],info)
                self.assertEqual(captured['vol_annual'],mc.sigma_annual)
                if model=='garch_t':self.assertIn('Horizon-average vol (ann.)',texts)


if __name__=='__main__':
    unittest.main()
