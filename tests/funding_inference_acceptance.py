"""Funding event-study inference: synthetic oracles and actual Flet payload."""
from datetime import date, timedelta
import math
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.crypto.analytics import funding_carry
    from core.crypto.funding_diagnostic import phase_diagnostic
    from core.research import crypto_workflow as workflow
    from ui import crypto_page
from tests.ar1_decay_acceptance import crypto_fixture
from tests.portfolio_scope_acceptance import controls
import flet as ft


def inputs(n=730):
    rng=np.random.default_rng(971)
    ds=[(date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(n)]
    f=rng.normal(0,.001,n);px=100*np.exp(np.cumsum(rng.normal(0,.02,n)))
    return dict(zip(ds,f)),dict(zip(ds,px))


class FundingTests(unittest.TestCase):
    def test_phase_probability_matches_full_brute_force_orbit(self):
        # Independent direct rolling oracle; tests sign, normalization and ties.
        for n in (130,257):
            rng=np.random.default_rng(n);x=np.round(rng.normal(size=n),1)
            y=np.convolve(rng.normal(size=n+29),np.ones(30),mode='valid')
            lo,hi=np.quantile(x,[.1,.9]);top=x>=hi;bot=x<=lo
            values=np.array([y[np.roll(top,k)].mean()-y[np.roll(bot,k)].mean() for k in range(n)])
            got=phase_diagnostic(x,y,30)
            self.assertAlmostEqual(got['observed_difference'],values[0],places=12)
            self.assertAlmostEqual(got['p_lower'],np.mean(values<=values[0]+1e-12),places=12)
            self.assertGreaterEqual(got['p_lower'],1/n)
            self.assertEqual(got['official_validation'],'NOT_RUN')

    def test_uniform_phase_null_controls_full_orbit_rejections(self):
        # Under its stated conditional null the relative phase is uniform.
        # Exhaust the orbit, rather than asserting calibration from one RNG run.
        rng=np.random.default_rng(22);n=131
        x=np.cumsum(rng.normal(size=n));y=np.convolve(rng.normal(size=n+29),np.ones(30),mode='valid')
        ps=np.array([phase_diagnostic(np.roll(x,k),y,30)['p_lower'] for k in range(n)])
        for alpha in (.01,.05,.1):self.assertLessEqual(float(np.mean(ps<=alpha)),alpha)

    def test_descriptive_means_and_carry_preserved_seed_independent(self):
        f,px=inputs();result=funding_carry(f,px);x=np.array(list(f.values()));p=np.array(list(px.values()))
        trail=np.convolve(x,np.ones(7)/7,mode='valid');ret=np.log(p[30:]/p[:-30])[6:]
        eligible=trail[:-30];lo,hi=np.quantile(eligible,[.1,.9])
        self.assertAlmostEqual(result.top_decile_fwd30,ret[eligible>=hi].mean(),places=14)
        self.assertAlmostEqual(result.bottom_decile_fwd30,ret[eligible<=lo].mean(),places=14)
        np.testing.assert_allclose(result.carry_ann_pct[6:],trail*365*100,rtol=0,atol=1e-12)
        self.assertTrue(math.isnan(result.bootstrap_p))
        self.assertEqual(result.diagnostic,funding_carry(f,px,seed=99).diagnostic)
        self.assertEqual(result.diagnostic['eligible_observations'],694)

    def test_unavailable_degenerate_insufficient_and_gapped_inputs(self):
        for x,y in [(np.ones(130),np.arange(130)),(np.arange(130),np.ones(130)),(np.arange(90),np.arange(90))]:
            d=phase_diagnostic(x,y,30);self.assertEqual(d['status'],'NOT_ESTIMATED');self.assertIsNone(d['p_lower'])
        f,px=inputs();del f[list(f)[50]]
        d=funding_carry(f,px).diagnostic;self.assertIsNone(d['p_lower']);self.assertIn('gaps',d['reason'])
        for kw in ({'window':0},{'fwd':-1},{'fwd':1.5}):
            with self.assertRaises(ValueError):funding_carry(*inputs(),**kw)
        for bad in (0.,-1.,float('nan'),float('inf')):
            f,px=inputs();px[next(iter(px))]=bad
            with self.assertRaises(ValueError):funding_carry(f,px)
        f,px=inputs();f[next(iter(f))]=float('nan')
        with self.assertRaises(ValueError):funding_carry(f,px)

    def test_actual_flet_workflow_payload_distinguishes_historical_card(self):
        out=crypto_fixture();data=dict(out.data);data['verdicts']=dict(data['verdicts'],M_C4_funding='PASS')
        captured={};page=Mock();page.run_thread.side_effect=lambda worker:worker()
        def ai(page,**kw):captured.update(payload=kw['payload_fn'](),narrative=kw['narrative']);return ft.Text('injected AI')
        with patch.object(crypto_page,'analyze',return_value=data),patch.object(crypto_page,'analysis_panel',side_effect=ai):
            root=crypto_page.build_crypto_page(page)
            next(c for c in controls(root) if isinstance(c,ft.Button) and c.on_click).on_click(None)
        text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
        for token in ('historical, not revalidated','overlapping windows','IID bootstrap p retired','Exploratory circular-phase'):
            self.assertIn(token,text)
        p=captured['payload'];self.assertIsNone(p['funding']['bootstrap_p'])
        self.assertEqual(p['verdicts']['M_C4_funding'],'PASS')
        self.assertIn('not valid confirmation',p['verdict_context']['M_C4_funding'])
        self.assertIn('assumption is unverified',captured['narrative'])
        self.assertNotIn('(bootstrap p ',captured['narrative'])

if __name__=='__main__':unittest.main()
