"""Market-screen parity and native export tests with synthetic/injected data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.research.market_analysis import (DerivativesRequest, ETFRequest, CryptoRequest, KRXRequest,
        execute_derivatives, execute_etf, execute_crypto, execute_krx)
    from core.research import etf_workflow, crypto_workflow
    from quantgen_desktop.app import ResearchWindow
from core.research.tool_export import make_report, report_bytes
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox


class MarketAdapterTests(unittest.TestCase):
    def setUp(self):
        p = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        p.start(); self.addCleanup(p.stop)

    def test_invalid_inputs_never_call_providers(self):
        cases = [(execute_derivatives,DerivativesRequest(n_paths=0),'snapshot_loader'),
                 (execute_etf,ETFRequest(code='../.env'),'analyze_fn'),
                 (execute_crypto,CryptoRequest(days=1),'analyze_fn')]
        for fn,q,keyword in cases:
            with self.assertRaises(ValueError): fn(q,**{keyword:lambda *a,**k:self.fail('called provider')})
        with self.assertRaises(ValueError): execute_krx(KRXRequest(code='bad'),gateway=object())

    def test_derivatives_parity_density_and_percentage_rate(self):
        out = execute_derivatives(DerivativesRequest(source='synthetic',n_paths=100,rate_pct=4))
        d = out.data
        self.assertAlmostEqual(d['rate'],.04)
        self.assertAlmostEqual(d['F'],1126,places=6)
        self.assertAlmostEqual(d['box']['rate'],.04,places=6)
        self.assertTrue(.99<d['rnd']['integral']<1.01)
        self.assertEqual(d['hedge'].n_paths,100)
        self.assertEqual(d['source'],'synthetic')

    def test_etf_reuses_adjusted_history_and_never_reads_study_store_by_default(self):
        with patch.object(etf_workflow,'load_cards',side_effect=AssertionError('study store read')):
            out = execute_etf(ETFRequest(code='SPY',source='synthetic',days=504))
        self.assertEqual(out.study_status,'NOT_LOADED')
        self.assertEqual(out.data['data_source'],'SYNTHETIC')
        self.assertEqual(out.data['sleeves']['cost_bps'],50)
        from core.quant import strategies as S
        px=out.data['price']; weights=S.trend_switch(px[:,None],rule='sma',lookback=210,step=21,cash_rate_daily=.03/252)
        pnl,_=S.simulate(px[:,None],weights,cost_bps=50,cash_daily=.03/252)
        self.assertAlmostEqual(out.data['sleeves']['trend']['sharpe'],S.summary(pnl)['sharpe'])

    def test_crypto_public_default_and_365_day_vol_convention(self):
        import config
        from core.quant import validate
        with patch.object(config,'upbit_ready',side_effect=AssertionError('account check')), \
             patch.object(validate,'load_cards',side_effect=AssertionError('study store read')):
            out=execute_crypto(CryptoRequest(source='synthetic'))
        self.assertIsNone(out.data['balances'])
        self.assertEqual(out.study_status,'NOT_LOADED')
        self.assertEqual(out.data['garch']['n'],730)
        from core.quant.garch import fit_garch
        import numpy as np
        fit=fit_garch(np.diff(np.log(out.data['btc']))[-730:],dist='t',profile=False)
        self.assertAlmostEqual(out.data['garch']['cond_vol_365'],fit.cond_vol_last*np.sqrt(365/252))
        self.assertEqual(len(out.data['weekday']['rows']),7)

    def test_krx_dispatch_preserves_failure_and_provenance(self):
        from data.krx.gateway import Answer
        from unittest.mock import Mock
        gateway=Mock()
        for tool,method in [('quote','quote'),('daily','daily'),('filings','filings'),('financials','financials'),('snapshot','market_snapshot'),('indices','indices')]:
            expected=Answer([], 'TEST',False,'No provider configured')
            getattr(gateway,method).return_value=expected
            result=execute_krx(KRXRequest(tool),gateway=gateway)
            self.assertIs(result.answer,expected)
            getattr(gateway,method).assert_called_once_with(*(() if tool in {'snapshot','indices'} else ('005930',)))

    def test_explicit_export_is_finite_escaped_and_never_claims_gate_pass(self):
        report=make_report('fixture',ETFRequest(),[{'text':'<script>bad</script> https://host/?apikey=SECRET','values':[float('nan'),1.2]}])
        obj=json.loads(report_bytes(report))
        self.assertEqual(obj['verdict'],'NOT_RUN')
        self.assertEqual(obj['sections'][0]['values'],[None,1.2])
        self.assertNotIn('SECRET',json.dumps(obj))
        with ZipFile(BytesIO(report_bytes(report,bundle=True))) as z:
            self.assertIsNone(z.testzip())
            self.assertNotIn(b'<script>bad',z.read('report.html'))


class NativeMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        p=patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden'))
        p.start();self.addCleanup(p.stop)
        self.window=ResearchWindow(auto_refresh=False)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.wait_idle()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):self.window.close()
        self.window.deleteLater();self.app.processEvents()

    def wait_idle(self):
        for _ in range(2000):
            self.app.processEvents()
            if not self.window.jobs.busy:return
            QTest.qWait(10)
        self.fail('Worker did not finish')

    def test_new_market_panes_complete_on_gui_thread_and_export_snapshot(self):
        w=self.window
        for name in ('derivatives','etf','crypto'):
            pane=getattr(w,name)
            pane.source.setCurrentIndex(pane.source.findData('synthetic'))
            if name=='derivatives':pane.fields['board']['paths'].setText('100')
            pane.submit();self.wait_idle()
            self.assertTrue(pane.has_result,pane.status.text())
            self.assertTrue(pane.export_json.isEnabled())
            self.assertEqual(pane.report['tool'],name)
            self.assertEqual(pane.report['parameters']['source'],'synthetic')
            self.assertTrue(pane.charts)
        pane=w.crypto
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'crypto.json'
            with patch('quantgen_desktop.tools.QFileDialog.getSaveFileName',return_value=(str(dest),'')):pane.export_result(False)
            self.assertEqual(json.loads(dest.read_text())['tool'],'crypto')
            with patch('quantgen_desktop.tools.QFileDialog.getSaveFileName',return_value=('','')):pane.export_result(True)
            self.assertEqual(len(list(Path(d).iterdir())),1)
        pane.fields['crypto']['days'].setText('nan');pane.submit()
        self.assertFalse(pane.has_result);self.assertIsNone(pane.report)

    def test_krx_refusal_does_not_disclose_provider_url_or_show_completed(self):
        from data.krx.gateway import Answer
        from core.research.market_analysis import KRXOutput
        p=self.window.krx
        p.show_result(KRXOutput(KRXRequest(),Answer(None,'KIS',False,'timeout https://host/?apikey=SECRET')))
        self.assertIn('UNAVAILABLE',p.status.text())
        self.assertFalse(p.has_result)
        self.assertNotIn('SECRET',str(p.sections))


if __name__=='__main__': unittest.main()
