"""The current AZ variance proxy is not the historical realised-drag benchmark."""
from functools import lru_cache
import unittest
from unittest.mock import Mock,patch
import numpy as np
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from core.research import etf_workflow as wf
    from core.research.market_analysis import ETFRequest,MarketOutput
    from ui import etf_page
from tests.portfolio_scope_acceptance import controls
import flet as ft

@lru_cache
def fixture(code='233740'):
    with patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden')):
        data=wf.analyze(code,source='synthetic',card_loader=lambda p:[{'card_id':'M_E4_letf_drag','decision':'REVISE','lines':['Injected historical study fixture']}])
    return MarketOutput(ETFRequest(source='synthetic',code=code),data,wf.narrative(data),'PROVIDED')

class LETFDisclosureTests(unittest.TestCase):
    def test_all_funds_scope_includes_distinct_proxy_and_preserves_card(self):
        for code in wf.LETF:
            out=fixture(code);lt=out.data['letf'];p=wf.payload(out.data)['letf']
            self.assertEqual(lt['verdict'],'REVISE')
            self.assertEqual(p['interpretation']['historical_study_fund'],'122630')
            self.assertEqual(p['interpretation']['current_proxy_validation'],'NOT_RUN')
            self.assertEqual(p['interpretation']['prior_quarter_quantity'],'AZ_PROXY_FROM_PRIOR_63_OBSERVATION_VARIANCE')
            self.assertIn('not observed fund/index realised drag',out.narrative)
            self.assertNotIn('better guide',out.narrative)
            # Independent AZ constant-variance formula; no engine or provider substitution.
            expected=(.5*(lt['beta']-lt['beta']**2)*(lt['last_quarter_vol']**2/252)*63-lt['fee']*63/252)*10000
            self.assertAlmostEqual(lt['last_quarter_drag_bp'],expected,places=10)

    def test_actual_flet_tooltips_narrative_and_ai_scope(self):
        for code in ('122630','233740'):
            out=fixture(code);captured={};page=Mock();page.run_thread.side_effect=lambda work:work()
            def ai(page,**kw):captured.update(payload=kw['payload_fn'](),narrative=kw['narrative']);return ft.Text('injected AI')
            with patch.object(etf_page,'analyze',return_value=out.data),patch.object(etf_page,'analysis_panel',side_effect=ai):
                root=etf_page.build_etf_page(page)
                next(c for c in controls(root) if isinstance(c,ft.Button) and c.on_click).on_click(None)
            text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
            self.assertIn('AZ proxy',text);self.assertIn('Historical 122630 study',text)
            self.assertIn('not observed fund/index realised drag',text)
            self.assertNotIn('better reference',str(root))
            self.assertIn('not validate this fund',captured['narrative'])
            self.assertEqual(captured['payload']['letf']['interpretation']['current_proxy_validation'],'NOT_RUN')

if __name__=='__main__':unittest.main()
