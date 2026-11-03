"""N1: independent OOS exposure oracles; synthetic inputs and no live I/O."""
from datetime import date, timedelta
from functools import lru_cache
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant import strategies as S
    from core.quant.history import History
    from core.research import strategy_workflow as flow
    from ui import strategy_lab_page as page_module
from core.research.strategy_exposure import exposure_summary, exposure_lines, EXPOSURE_HELP
from tests.portfolio_scope_acceptance import controls
import flet as ft


@lru_cache
def fixture(family='vol_target', count=4, cost=50):
    symbols=('SPY', 'QQQ', 'TLT', 'GLD')[:count]
    rng=np.random.default_rng(7301)
    prices=100*np.exp(np.vstack([np.zeros(count), np.cumsum(rng.normal(.001, .002, (1099,count)),axis=0)]))
    dates=tuple((date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(len(prices)))
    def loader(symbol, **kw):
        return History(symbol, 'SYNTHETIC', dates, tuple(prices[:,symbols.index(symbol)]), note='synthetic fixture')
    with patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden')), \
         patch('core.quant.gate_ledger.family_ledger',side_effect=AssertionError('ledger forbidden')):
        return flow.run_family(family,list(symbols),history_loader=loader,source='synthetic',cost_bps=cost,bootstrap_B=40)


class ExposureTests(unittest.TestCase):
    def test_oos_switching_embargo_partial_tail_and_held_row_alignment(self):
        prices=np.ones((11,2));dates=tuple(f'd{i}' for i in range(10))
        a=np.column_stack([np.linspace(0,1,11),np.linspace(1,0,11)])
        b=np.column_stack([np.linspace(.1,.9,11),np.linspace(.2,1,11)])
        wf=SimpleNamespace(origins=(2,5),chosen=(0,1),dates=dates[3:8])
        fn=lambda p, which: [a,b][which]
        info=exposure_summary('vol_target',prices,dates,[{'which':0},{'which':1}],fn,wf,embargo=1,cash_daily=.03/252)
        # First origin's g0 over rows3:6, then g1 over rows6:8 (partial tail).
        expected=np.r_[a[3:6].sum(axis=1),b[6:8].sum(axis=1)]
        self.assertAlmostEqual(info['gross_mean'],expected.mean())
        self.assertAlmostEqual(info['gross_max'],expected.max())
        self.assertAlmostEqual(info['borrowing_max'],max(0,expected.max()-1))
        self.assertNotEqual(info['gross_mean'],b[3:8].sum(axis=1).mean())
        self.assertNotEqual(info['gross_mean'],np.r_[a[4:7].sum(axis=1),b[7:9].sum(axis=1)].mean())
        self.assertEqual(info['observations'],5)

    def test_real_generators_multi_asset_and_single_asset_caps(self):
        for family in ('vol_target','crypto_trend'):
            for count in (1,4):
                with self.subTest(family=family,count=count):
                    r=fixture(family,count);info=r['exposure']
                    self.assertEqual(info['asset_count'],count)
                    self.assertAlmostEqual(info['gross_max'],count)
                    self.assertAlmostEqual(info['borrowing_max'],count-1)
                    self.assertEqual(info['theoretical_gross_upper_bound'],count)
                    self.assertIsNone(info['portfolio_gross_cap'])
                    self.assertEqual(info['benchmark_gross'],1)
                    self.assertEqual(info['observations'],len(r['wf'].pnl))
                    self.assertIsNone(r['ledger_n'])
                    self.assertEqual(r['score'].n_trials,len(r['grid']))

    def test_simulator_borrowing_and_daily_equal_weight_benchmark_oracle(self):
        r=fixture();p=r['panel'].prices;wf=r['wf'];grid=r['grid']
        dates=r['panel'].dates[1:];lookup={d:i for i,d in enumerate(dates)}
        expected=[];exposure=[]
        for d in wf.dates:
            i=lookup[d]
            block=max(j for j,o in enumerate(wf.origins) if o+21<=i)
            g=wf.chosen[block]
            # Existing generators; independent P&L oracle includes negative cash and turnover.
            if not expected or g!=previous:
                w=S.vol_target(p,**grid[g]);previous=g
            held=w[i];turn=np.abs(held-(w[i-1] if i else np.zeros(p.shape[1]))).sum()
            expected.append(float(held@(p[i+1]/p[i]-1)+(1-held.sum())*.03/252-turn*50/10000))
            exposure.append(float(held.sum()))
        np.testing.assert_allclose(wf.pnl,expected,rtol=1e-12,atol=1e-12)
        self.assertAlmostEqual(r['exposure']['gross_mean'],np.mean(exposure))
        bench=[np.mean(p[lookup[d]+1]/p[lookup[d]]-1) for d in wf.dates]
        np.testing.assert_allclose(r['bench_equity'],np.r_[1,np.cumprod(1+np.array(bench))])

    def test_other_family_is_unmodified_and_cost_refusal_survives_payload(self):
        fn=Mock(side_effect=AssertionError('must not reconstruct other families'))
        self.assertIsNone(exposure_summary('pairs',None,None,None,fn,None,embargo=0,cash_daily=0))
        fn.assert_not_called()
        r=fixture(cost=1);p=flow.payload(r)
        self.assertEqual(p['decision'],'WITHHELD')
        self.assertNotIn('decision',p['stats'])
        self.assertIsNone(p['revise_target'])
        self.assertEqual(p['exposure'],r['exposure'])
        self.assertIn('not exposure-matched',flow.narrative(r))

    def test_flet_actual_notices_and_ai_payload(self):
        for family in ('vol_target','crypto_trend'):
            r=fixture(family);captured={};page=Mock()
            page.run_thread.side_effect=lambda work:work()
            def panel(page,**kw):
                captured.update(payload=kw['payload_fn'](),narrative=kw['narrative'])
                return ft.Text('injected AI panel')
            with patch.object(page_module,'load_cards',return_value=[]), \
                 patch.object(page_module,'run_family',return_value=r), \
                 patch.object(page_module.xc,'equity_chart',wraps=page_module.xc.equity_chart) as chart, \
                 patch.object(page_module,'analysis_panel',side_effect=panel):
                root=page_module.build_strategy_lab_page(page)
                next(c for c in controls(root) if isinstance(c,ft.Button) and c.content=='Run').on_click(None)
            plot_dates,eq,bench=chart.call_args.args
            self.assertEqual(len(plot_dates),len(eq))
            self.assertEqual(len(plot_dates),len(bench))
            self.assertEqual(tuple(plot_dates[1:]),r['wf'].dates)
            self.assertEqual(plot_dates[0],r['panel'].dates[r['panel'].dates.index(r['wf'].dates[0])-1])
            self.assertEqual(eq[0],1.)
            text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
            self.assertIn(EXPOSURE_HELP,text)
            for line in exposure_lines(r['exposure']): self.assertIn(line,text)
            self.assertEqual(captured['payload']['exposure'],r['exposure'])
            self.assertIn('OOS held gross exposure',captured['narrative'])


if __name__=='__main__': unittest.main()
