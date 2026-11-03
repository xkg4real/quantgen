"""NEW-M6-03: amplitude decay, missing estimates, and actual browser paths."""
from datetime import date, timedelta
from functools import lru_cache
from types import SimpleNamespace
import math
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from core.quant import strategies as S
    from core.quant.history import History
    from core.research import etf_workflow as etf, crypto_workflow as crypto
    from core.research.market_analysis import ETFRequest, CryptoRequest, MarketOutput
    from ui import etf_page, crypto_page
from core.research.decay_disclosure import decay_text
from tests.portfolio_scope_acceptance import controls
import flet as ft


def ar(phi,n=800,seed=7306):
    rng=np.random.default_rng(seed);x=np.zeros(n)
    for i in range(1,n):x[i]=phi*x[i-1]+rng.normal(0,.2)
    return x


@lru_cache
def etf_fixture():
    prem=ar(-.7,360);dates=tuple((date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(len(prem)))
    nav=np.full(len(prem),100.);price=nav*(1+prem/100)
    h=History('069500','SYNTHETIC',dates,tuple(price),note='injected NAV fixture')
    km=SimpleNamespace(etf_quote=lambda code:{},etf_components=lambda code:[],
        etf_nav_daily=lambda code,days:SimpleNamespace(dates=dates,close=price,extra={'nav':nav,'premium_pct':prem}))
    with patch('config.kis_ready',return_value=True),patch('data.kis_markets.KISMarkets',return_value=km), \
         patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden')):
        d=etf.analyze('069500',source='kis',days=len(prem),history_loader=lambda *a,**k:h,card_loader=lambda p:[])
    d['data_source']='SYNTHETIC'
    return MarketOutput(ETFRequest(source='synthetic'),d,etf.narrative(d))


@lru_cache
def crypto_fixture():
    data=crypto._synthetic();ds=data['dates'];prem=ar(-.7,len(ds));ratio=ar(-.6,len(ds),seed=2)
    data['upbit']={d:data['binance'][d]*data['usdkrw'][d]*(1+prem[i]/100) for i,d in enumerate(ds)}
    data['eth']={d:data['binance'][d]*np.exp(ratio[i])/20 for i,d in enumerate(ds)}
    with patch.object(crypto,'_synthetic',return_value=data), \
         patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden')):
        d=crypto.analyze(source='synthetic',card_loader=lambda p:[],include_balances=False)
    return MarketOutput(CryptoRequest(source='synthetic'),d,crypto.narrative(d))


class AR1DecayTests(unittest.TestCase):
    def setUp(self):
        for name in ('requests.sessions.Session.request','core.quant.validate.load_cards','core.quant.gate_ledger.family_ledger'):
            p=patch(name,side_effect=AssertionError('live I/O forbidden'));p.start();self.addCleanup(p.stop)

    def test_signed_ar_oracle_uses_impulse_amplitude(self):
        for phi in (-.9,-.7,-.3,.3,.7,.9):
            x=ar(phi,2000)
            # Independent centered covariance / variance OLS, not the implementation's lstsq.
            lag=x[:-1];y=x[1:];b=float((lag-lag.mean())@(y-y.mean())/((lag-lag.mean())@(lag-lag.mean())))
            expected=-math.log(2)/math.log(abs(b));d=S.ar1_decay(x)
            self.assertAlmostEqual(d['phi'],b,places=12)
            self.assertAlmostEqual(S.half_life(x),expected,places=12)
            self.assertEqual(d['status'],'OSCILLATING' if b<0 else 'MONOTONE')
            self.assertAlmostEqual(abs(b)**d['half_life'],.5,places=12)
            self.assertIn('not a stationarity test',decay_text(d))

    def test_unavailable_is_not_nondecay_or_slow_reversion(self):
        for x in ([],np.arange(9),np.ones(30),np.r_[np.arange(20),np.nan],np.zeros((20,2))):
            d=S.ar1_decay(x)
            self.assertEqual(d['status'],'NOT_ESTIMATED');self.assertIsNone(d['half_life'])
            self.assertTrue(math.isinf(S.half_life(x)))
            self.assertIn('not evidence of slow',decay_text(d))
        for phi in (-1.01,1.01):
            d=S.ar1_decay(phi**np.arange(40))
            self.assertEqual(d['status'],'NON_DECAYING');self.assertIsNone(d['half_life'])
            self.assertIn('does not establish slow',decay_text(d))
        # Exact zero-covariance series yields the no-memory limit.
        x=np.tile([1.,0.,-1.,0.],10)
        with patch.object(np.linalg,'lstsq',return_value=(np.array([0.,0.]),[],2,[])):
            self.assertEqual(S.ar1_decay(x)['status'],'NO_MEMORY')
            self.assertEqual(S.half_life(x),0.)

    def test_etf_crypto_workflows_and_payload_expose_negative_phi(self):
        e=etf_fixture();c=crypto_fixture()
        self.assertEqual(e.data['premium_stats']['decay']['status'],'OSCILLATING')
        self.assertIn('oscillates in sign',e.narrative)
        self.assertNotIn('slow-moving enough',e.narrative)
        self.assertNotIn('4–5 bp round trip',e.narrative)
        self.assertEqual(c.data['kimchi'].decay['status'],'OSCILLATING')
        self.assertEqual(c.data['ethbtc']['decay']['status'],'OSCILLATING')
        p=crypto.payload(c.data)
        self.assertEqual(p['kimchi']['decay']['unit'],'observations')
        self.assertTrue(math.isfinite(p['kimchi']['half_life_days']))
        self.assertTrue(math.isfinite(p['ethbtc']['half_life_days']))
        self.assertEqual(etf.payload(e.data)['premium_stats']['decay'],e.data['premium_stats']['decay'])

    def test_actual_flet_pages_show_diagnostic_and_ai_basis(self):
        for mod,out,builder in ((etf_page,etf_fixture(),etf_page.build_etf_page),
                                (crypto_page,crypto_fixture(),crypto_page.build_crypto_page)):
            captured={};page=Mock();page.run_thread.side_effect=lambda work:work()
            def ai(page,**kw):
                captured.update(payload=kw['payload_fn'](),narrative=kw['narrative']);return ft.Text('injected AI')
            with patch.object(mod,'analyze',return_value=out.data),patch.object(mod,'analysis_panel',side_effect=ai):
                root=builder(page)
                next(c for c in controls(root) if isinstance(c,ft.Button) and c.on_click).on_click(None)
            text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
            self.assertIn('oscillates in sign',text)
            self.assertIn('AR(1) amplitude half-life',text)
            self.assertIn('oscillates in sign',captured['narrative'])
            self.assertNotIn('slow-moving enough',text)


if __name__=='__main__':unittest.main()
