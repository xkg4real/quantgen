"""M4-N1: exact master identity and request routing; no live data or cards."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv

with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.research import etf_workflow as wf
    from core.research.market_analysis import ETFRequest, MarketOutput
    from core.quant.history import synthetic_history
    from data import kis_markets as km
    from ui import etf_page
from tests.portfolio_scope_acceptance import controls
import flet as ft


def master_row(code='9876', name='코스닥 150'):
    # Deliberately invented fixture code: the implementation must read the master,
    # not hard-code this or any supposed live KOSDAQ150 identifier.
    return (b'1' + code.encode('ascii') + name.encode('cp949').ljust(40, b' ')).decode('cp949')


def unavailable_output():
    fund = replace(synthetic_history('233740', days=320), source='YFINANCE', note='Injected fund')
    with patch.object(wf.config, 'kis_ready', return_value=False), \
         patch.object(wf, 'synthetic_history', side_effect=AssertionError('silent synthetic index')):
        data = wf.analyze('233740', source='yfinance', history_loader=lambda *a, **k: fund,
                          card_loader=lambda p: ())
    return MarketOutput(ETFRequest(code='233740', source='yfinance'), data, wf.narrative(data))


class LETFIndexTests(unittest.TestCase):
    def setUp(self):
        p = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        p.start(); self.addCleanup(p.stop)

    def test_master_exact_name_bytes_missing_ambiguous_and_no_broad_index_fallback(self):
        for name in ('코스닥 150', 'KOSDAQ150', 'KOSDAQ 150'):
            with patch.object(km, 'load_master', return_value=[master_row(name=name)]) as load:
                self.assertEqual(km.domestic_index_code('KOSDAQ150'), '9876')
                load.assert_called_once_with('idxcode')
        for rows in ([], [master_row(name='코스닥')], [master_row(name='코스닥150 선물')],
                     [master_row(name='코스닥150 레버리지')], [master_row(code='ABCD')],
                     [master_row()[:12]], [master_row(), master_row(code='9875')]):
            with self.subTest(rows=rows), patch.object(km, 'load_master', return_value=rows):
                with self.assertRaises(km.KISUnavailable): km.domestic_index_code('KOSDAQ150')
        with patch.object(km, 'load_master', side_effect=AssertionError('unnecessary lookup')):
            self.assertEqual(km.domestic_index_code('KOSPI200'), '2001')

    def test_five_funds_route_actual_index_endpoint_and_variance_to_correct_identity(self):
        fund = synthetic_history('fund-fixture', days=60)
        indices = {code: synthetic_history(name, days=600) for code, name in
                   [('2001', 'kospi-test'), ('9876', 'kosdaq-test')]}
        requests = []
        class Client:
            ready = True
            def _get(self, path, tr_id, params):
                requests.append((path, tr_id, params.copy()))
                history = indices[params['FID_INPUT_ISCD']]
                return {'output2': [{'stck_bsop_date': d.replace('-', ''), 'bstp_nmix_prpr': p}
                                    for d, p in zip(history.dates, history.closes)]}
        class Market(km.KISMarkets):
            def __init__(self): super().__init__(Client())
            def etf_quote(self, code): return None
            def etf_components(self, code): return []
            def etf_nav_daily(self, code, **kwargs):
                return km.Bars(code, fund.dates, fund.closes,
                               extra={'nav': fund.closes, 'premium_pct': (0.,)*len(fund)})
        expected = {'122630': ('KOSPI200','2001'), '252670': ('KOSPI200','2001'),
                    '114800': ('KOSPI200','2001'), '233740': ('KOSDAQ150','9876'),
                    '251340': ('KOSDAQ150','9876')}
        with patch.object(wf.config,'kis_ready',return_value=True), patch.object(km,'KISMarkets',Market), \
             patch.object(km,'load_master',return_value=[master_row()]), \
             patch.object(wf,'synthetic_history',side_effect=AssertionError('synthetic substitution')):
            for code, (name, identifier) in expected.items():
                data = wf.analyze(code,source='kis',days=60,history_loader=lambda *a,**k:fund,
                                  card_loader=lambda p:())
                lt = data['letf']; self.assertEqual(lt['calculation_status'],'COMPUTED',lt)
                self.assertEqual((lt['underlying_index'],lt['index_code']),(name,identifier))
                path,tr,params=requests[-1]
                self.assertEqual(path,'/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice')
                self.assertEqual(tr,'FHKUP03500100')
                self.assertEqual((params['FID_INPUT_ISCD'],params['FID_COND_MRKT_DIV_CODE']),(identifier,'U'))
                variance=np.var(indices[identifier].log_returns()[-63:])
                beta=lt['beta']; oracle=(.5*(beta-beta**2)*63*variance-lt['fee']*63/252)*10000
                self.assertAlmostEqual(lt['last_quarter_drag_bp'],oracle,places=10)
                self.assertIn(name,wf.narrative(data));self.assertEqual(wf.payload(data)['letf']['index_status'],'AVAILABLE')

    def test_no_real_index_provider_keeps_fund_results_but_never_fabricates_drag(self):
        out=unavailable_output();lt=out.data['letf']
        self.assertIn('sleeves',out.data);self.assertNotIn('rows',lt)
        self.assertEqual(lt['calculation_status'],'NOT_RUN');self.assertEqual(lt['index_status'],'UNAVAILABLE')
        self.assertIn('required index: KOSDAQ150',out.narrative)
        self.assertIsNone(wf.payload(out.data)['letf']['index_source'])

    def test_lookup_or_history_failure_never_uses_another_index_or_leaks_url(self):
        fund=synthetic_history('fund',days=60)
        market=Mock();market.etf_quote.return_value=None;market.etf_components.return_value=[]
        market.etf_nav_daily.return_value=km.Bars('233740',fund.dates,fund.closes,
                        extra={'nav':fund.closes,'premium_pct':(0.,)*len(fund)})
        invalid=[km.Bars('INDEX:2001',fund.dates,fund.closes),
                 km.Bars('INDEX:9876',fund.dates,fund.closes),  # <63 returns
                 km.Bars('INDEX:9876',('2026-01-01',)*65,(float('nan'),)*65)]
        cases=[RuntimeError('https://provider/?apikey=secret-fixture')]+invalid
        with patch.object(wf.config,'kis_ready',return_value=True),patch.object(km,'KISMarkets',return_value=market), \
             patch.object(wf,'synthetic_history',side_effect=AssertionError('synthetic substitution')):
            for case in cases:
                market.index_daily.reset_mock();market.index_daily.return_value=case
                with patch.object(km,'load_master',side_effect=case if isinstance(case,Exception) else None,
                                  return_value=[master_row()]):
                    data=wf.analyze('233740',source='kis',days=60,history_loader=lambda *a,**k:fund,card_loader=lambda p:())
                self.assertNotIn('rows',data['letf']);self.assertNotIn('secret-fixture',str(data))
                self.assertEqual(data['letf']['calculation_status'],'NOT_RUN')
                if isinstance(case,Exception):market.index_daily.assert_not_called()
                else:market.index_daily.assert_called_once_with('9876',days=600)

    def test_explicit_demo_uses_distinct_named_index_only(self):
        for code,index in [('122630','KOSPI200'),('233740','KOSDAQ150'),('251340','KOSDAQ150')]:
            with patch.object(wf,'synthetic_history',wraps=synthetic_history) as gen, \
                 patch.object(km,'load_master',side_effect=AssertionError('demo network')):
                data=wf.analyze(code,source='synthetic',days=60,card_loader=lambda p:())
            gen.assert_called_once_with(index,days=600)
            self.assertEqual(data['letf']['index_status'],'SYNTHETIC')
            self.assertIn('not market data',wf.payload(data)['letf']['index_source'])

    def test_flet_unavailable_notice_and_ai_payload_preserve_status(self):
        out=unavailable_output();captured={};page=Mock();page.run_thread.side_effect=lambda f:f()
        def ai(page,**kw):captured.update(payload=kw['payload_fn'](),narrative=kw['narrative']);return ft.Text('injected AI')
        with patch.object(etf_page,'analyze',return_value=out.data),patch.object(etf_page,'analysis_panel',side_effect=ai):
            root=etf_page.build_etf_page(page)
            next(c for c in controls(root) if isinstance(c,ft.Button) and c.on_click).on_click(None)
        text='\n'.join(str(c.value) for c in controls(root) if isinstance(c,ft.Text))
        self.assertIn('LETF calculation NOT_RUN',text);self.assertIn('KOSDAQ150',text)
        self.assertNotIn('Index cond. vol',text)
        self.assertEqual(captured['payload']['letf']['calculation_status'],'NOT_RUN')


if __name__=='__main__':unittest.main()
