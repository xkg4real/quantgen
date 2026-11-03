"""M4-N12: zero violations must not stand for an unperformed quote check."""
from dataclasses import replace
from functools import lru_cache
import unittest
from unittest.mock import Mock, patch
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import equity_deriv as ED
    from core.research import derivatives_workflow as wf
    from core.research.quote_coverage import quote_coverage, butterfly_display, quote_coverage_text, static_payload
    from core.research.market_analysis import DerivativesRequest, MarketOutput
    from ui import derivatives_page
from tests.portfolio_scope_acceptance import controls
import flet as ft


def board():
    # Unequal strike spacing: call convex chord at100 is 8 1/3, below mid11.
    return [ED.Quote(k,c,p,c-.1,c+.1,p-.1,p+.1)
            for k,c,p in [(90.,12.,1.),(100.,11.,2.),(120.,1.,14.)]]


@lru_cache
def output(closed=False):
    quotes=wf.synthetic_board()
    if closed:quotes=[replace(q,call_bid=None,call_ask=None,put_bid=None,put_ask=None) for q in quotes]
    with patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden')), \
         patch.object(wf,'synthetic_board',return_value=quotes):
        data=wf.snapshot(source='synthetic',n_paths=100)
    if closed:data['live_quotes']=False
    return MarketOutput(DerivativesRequest(source='synthetic',n_paths=100),data,wf.narrative(data),'NOT_APPLICABLE')


class QuoteCoverageTests(unittest.TestCase):
    def test_zero_one_two_three_strikes_have_distinct_inequality_coverage(self):
        for n in range(4):
            raw=ED.static_arbitrage(board()[:n],quoted_only=True)
            c=quote_coverage(raw,[])
            for side in ('call','put'):
                for kind,width in [('vertical',2),('butterfly',3)]:
                    check=c['static'][side+'_'+kind];tests=max(n-width+1,0)
                    self.assertEqual(check['tests'],tests)
                    if not tests:
                        self.assertIsNone(check['violations']);self.assertEqual(check['status'],'NOT_RUN')
                    else:self.assertEqual(check['violations'],raw[side+'_'+kind])
            if n<3:self.assertEqual(butterfly_display(c),('NOT_RUN','muted'))
        self.assertEqual(butterfly_display(c),('1','error'))

    def test_partial_side_and_moneyness_exclusions_are_not_full_pass(self):
        q=[replace(x,put_bid=None,put_ask=None) for x in board()]
        c=quote_coverage(ED.static_arbitrage(q,quoted_only=True),[])
        self.assertEqual(butterfly_display(c),('1 · PARTIAL','error'))
        self.assertEqual(c['static']['put_butterfly']['status'],'NOT_RUN')
        clean=[replace(q[0],call_mid=14),replace(q[1],call_mid=8),q[2]]
        c=quote_coverage(ED.static_arbitrage(clean,quoted_only=True),[])
        self.assertEqual(butterfly_display(c),('0 · PARTIAL','muted'))
        filtered=quote_coverage(ED.static_arbitrage(board(),quoted_only=True,F=100,max_moneyness=.01),[])
        self.assertEqual(butterfly_display(filtered),('NOT_RUN','muted'))

    def test_parity_denominator_and_injected_violations_are_preserved(self):
        raw=ED.static_arbitrage(board(),quoted_only=True)
        self.assertEqual(raw['call_butterfly'],1);self.assertEqual(raw['put_butterfly'],0)
        c=quote_coverage(raw,[{'within':True},{'within':False},{'within':None}])
        self.assertEqual(c['parity'],{'tests':2,'within':1,'within_fraction':.5,'status':'COMPUTED'})
        self.assertIn('50%',quote_coverage_text(c))
        q=board();q[1]=replace(q[1],call_mid=13,put_mid=.5)
        raw=ED.static_arbitrage(q,quoted_only=True)
        self.assertEqual((raw['call_vertical'],raw['put_vertical']),(1,1))
        c=quote_coverage(raw,[])
        self.assertEqual(static_payload(raw,c)['call_vertical'],1)
        self.assertIn('parity NOT_RUN',quote_coverage_text(c))
        self.assertNotIn('nan%',quote_coverage_text(c))

    def test_full_workflow_closed_board_keeps_prices_without_false_zero_or_nan_percentage(self):
        out=output(True);s=out.data
        self.assertGreater(len(s['points']),5);self.assertEqual(s['arbitrage']['n_calls'],0)
        p=wf.payload(s);self.assertIsNone(p['static_arbitrage']['call_butterfly'])
        self.assertIsNone(p['parity_check']['within_fraction'])
        self.assertEqual(p['parity_check']['status'],'NOT_RUN')
        self.assertIn('call_butterfly: NOT_RUN',out.narrative)
        self.assertNotIn('nan%',out.narrative)
        # A genuinely tested clean board still supplies numeric counts.
        clean=wf.payload(output(False).data)
        self.assertEqual(clean['static_arbitrage']['call_butterfly'],0)
        self.assertGreater(clean['static_arbitrage']['checks']['call_butterfly']['tests'],0)

    def test_flet_stat_is_neutral_not_run_and_ai_receives_null(self):
        out=output(True);page=Mock();page.run_thread.side_effect=lambda f:f();seen={};original=derivatives_page.stat
        def stat(title,value,**kw):
            if title=='Butterfly viol.':seen['butterfly']=(value,kw['token'])
            return original(title,value,**kw)
        def ai(page,**kw):seen['payload']=kw['payload_fn']();return ft.Text('injected AI')
        with patch.object(derivatives_page,'snapshot',return_value=out.data), \
             patch.object(derivatives_page,'stat',side_effect=stat), \
             patch.object(derivatives_page,'analysis_panel',side_effect=ai):
            root=derivatives_page.build_derivatives_page(page)
            next(c for c in controls(root) if isinstance(c,ft.Button) and c.on_click).on_click(None)
        self.assertEqual(seen['butterfly'],('NOT_RUN','muted'))
        self.assertIsNone(seen['payload']['static_arbitrage']['put_butterfly'])
        text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
        self.assertIn('NOT_RUN',text);self.assertIn('insufficient eligible quoted strikes',text)


if __name__=='__main__':unittest.main()
