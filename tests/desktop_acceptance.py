"""Native Qt integration with deterministic histories; no network or actual stores."""
from datetime import date, timedelta
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.quant.history import History
    from core.quant.montecarlo import run_monte_carlo
from core.research.analysis import AnalysisRequest, execute_analysis, funding_rate
from core.research.portfolio_analysis import PortfolioRequest, execute_portfolio
from core.research.runs import new_run, read_export
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.jobs import Jobs
from PyQt6.QtCore import QThread
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox


def history_fixture():
    dates = tuple((date(2026,1,1)+timedelta(days=i)).isoformat() for i in range(120))
    closes = tuple(100+0.08*i+math.sin(i*.7)*2+math.cos(i*.17) for i in range(120))
    return History("TEST", "SYNTHETIC", dates, closes, note="Deterministic test fixture")


def fixture_runner(request, run):
    return execute_analysis(request, run, history_loader=lambda *a,**k:history_fixture(),
                            rate_reader=lambda s:(.03,"assumed fixture rate"))


def portfolio_fixture(request):
    def history(symbol, **kwargs):
        h=history_fixture()
        offset=request.symbols.index(symbol)
        closes=tuple(100+.05*i+math.sin(i*(.4+.1*offset))*3+math.cos(i*.1+offset) for i in range(120))
        return replace(h,symbol=symbol,closes=closes)
    return execute_portfolio(request,history_loader=history)


class AnalysisAdapterTests(unittest.TestCase):
    def test_portfolio_adapter_preserves_solver_comparisons_and_warnings(self):
        from core.quant.optimize import optimize_portfolio
        request=PortfolioRequest(('ONE','TWO','THREE'),source='synthetic',max_weight=.5)
        out=portfolio_fixture(request)
        self.assertEqual(len(out.portfolios),4)
        for key,p in out.portfolios.items():
            direct=optimize_portfolio(out.stats,objective=key,rf_rate=.03,max_weight=.5 if key=='max_sharpe' else 1)
            self.assertEqual(list(p.weights),list(direct.weights))
            self.assertEqual(p.converged,direct.converged)
        self.assertTrue(all(h.source=='SYNTHETIC' for h in out.histories))
        for syms in [('ONE',),('ONE','ONE')]:
            with self.assertRaises(ValueError):PortfolioRequest(syms).validate()
    def test_adapter_matches_engine_for_every_model_and_preserves_verdict(self):
        h = history_fixture()
        for model in ("gbm", "jump", "bootstrap", "garch_t"):
            with self.subTest(model=model):
                q=AnalysisRequest(symbol="TEST",source_requested="synthetic",model=model,
                                  n_paths=200,horizon_days=5,seed=19,drift="zero")
                direct=run_monte_carlo(h,model=model,n_paths=200,horizon_days=5,seed=19,drift="zero",rf_rate=0,erp=0)
                out=fixture_runner(q,new_run(q.parameters()))
                self.assertEqual(out.result.median_terminal,direct.median_terminal)
                self.assertEqual(out.result.cvar_pct,direct.cvar_pct)
                self.assertEqual(out.run['verdict'],'NOT_RUN')
                self.assertEqual(out.run['reproducibility'],'PARTIAL')
                self.assertTrue(out.run['data']['synthetic'])
                self.assertEqual(read_export(__import__('core.research.runs',fromlist=['export_bytes']).export_bytes(out.run)),out.run)

    def test_invalid_request_refuses_before_provider_and_mismatched_record_refused(self):
        q=AnalysisRequest()
        for change in ({'target':float('nan')},{'target':-1},{'erp':float('inf')},
                       {'horizon_days':1},{'n_paths':True},{'seed':-1},{'symbol':' '},{'model':'unknown'}):
            with self.assertRaises(ValueError):replace(q,**change).parameters()
        other=new_run(replace(q,seed=8).parameters())
        with self.assertRaises(ValueError):execute_analysis(q,other,history_loader=lambda *a: self.fail('provider called'))

    def test_funding_source_currency_and_fallback_remain_explicit(self):
        from types import SimpleNamespace
        usd=lambda *a,**k:SimpleNamespace(source='FRED',last=4.2,last_date='2026-10-29')
        krw=lambda *a,**k:SimpleNamespace(source='FRED',last=.03,last_date='2026-09-01')
        self.assertEqual(funding_rate('AAPL',series_loader=usd,short_rate_loader=krw)[0],.042)
        self.assertEqual(funding_rate('005930',series_loader=usd,short_rate_loader=krw)[0],.03)
        synthetic=lambda *a,**k:SimpleNamespace(source='SYNTHETIC',last=99)
        rate,note=funding_rate('AAPL',series_loader=synthetic,short_rate_loader=synthetic)
        self.assertEqual(rate,.03);self.assertIn('assumed',note)


class NativeDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        # Unexpected I/O must fail before opening external resources.
        self.network=patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden'))
        self.network.start(); self.addCleanup(self.network.stop)
        self.window=ResearchWindow(auto_refresh=False,market_loader=lambda:[],analysis_runner=fixture_runner,
                                   portfolio_runner=portfolio_fixture)
        self.window.show(); self.app.processEvents()
        self.addCleanup(self.cleanup_window)

    def cleanup_window(self):
        self.wait_idle()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater();self.app.processEvents()

    def wait_idle(self):
        for _ in range(1500):
            self.app.processEvents()
            if not self.window.jobs.busy:return
            QTest.qWait(10)
        self.fail('Worker did not finish in 15 seconds')

    def configure_gbm(self):
        w=self.window
        w.symbol.setText('TEST');w.source.setCurrentIndex(w.source.findData('synthetic'))
        w.model.setCurrentIndex(w.model.findData('gbm'));w.drift.setCurrentIndex(w.drift.findData('zero'))
        w.paths.setValue(200);w.horizon.setValue(5)

    def test_navigation_native_widgets_no_browser_and_dark_theme(self):
        w=self.window
        self.assertEqual(w.stack.count(),6)
        self.assertEqual(w.stack.currentIndex(),0)
        for route in w.route_indices:
            w.navigate(route)
            self.assertTrue(w.nav[route].isChecked())
        w.theme.setCurrentIndex(1);self.app.processEvents()
        self.assertEqual(w.home_chart.colors,w.colors)
        self.assertNotIn('QtWebEngineWidgets',__import__('sys').modules)
        self.assertFalse(w.grab().isNull())

    def test_native_portfolio_weights_frontier_correlation_and_synthetic_label(self):
        w=self.window;w.navigate('risk')
        w.portfolio.symbols.setText('ONE,TWO,THREE')
        w.portfolio.source.setCurrentIndex(w.portfolio.source.findData('synthetic'))
        w.portfolio.submit();self.wait_idle()
        self.assertEqual(w.portfolio.weights.rowCount(),3)
        self.assertEqual(w.portfolio.comparison.rowCount(),4)
        self.assertEqual(w.portfolio.correlation.columnCount(),4)
        self.assertIsNotNone(w.portfolio.chart.output)
        self.assertIn('합성 데이터',w.portfolio.notes.text())
        self.assertTrue(w.portfolio.run.isEnabled())

    def test_analysis_navigation_and_native_export_cancel_and_failure(self):
        w=self.window;self.configure_gbm()
        w.run_analysis();w.navigate('home');self.wait_idle()
        run=w.session.runs()[0]
        self.assertEqual(run['execution_status'],'COMPLETED')
        self.assertIn('TEST',w.home_summary.text());self.assertEqual(w.count_labels[0].text(),'1')
        self.assertIsNotNone(w.home_chart.result)
        w.navigate('library');w.run_table.selectRow(0)
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'research.json'
            with patch('quantgen_desktop.app.QFileDialog.getSaveFileName',return_value=(str(dest),'')):
                w.export_selected(False)
            self.assertEqual(read_export(dest.read_bytes()),run)
            with patch('quantgen_desktop.app.QFileDialog.getSaveFileName',return_value=('','')):
                w.export_selected(False)
            self.assertEqual(len(list(Path(d).iterdir())),1)
            with patch('quantgen_desktop.app.QFileDialog.getSaveFileName',return_value=(str(Path(d)/'.env.json'),'')):
                w.export_selected(False)
            self.assertIn('저장 실패',w.export_status.text())
            self.assertFalse((Path(d)/'.env.json').exists())

    def test_failure_is_recorded_and_provider_message_is_not_exposed(self):
        self.configure_gbm()
        def broken(*args):raise RuntimeError('https://provider/?apikey=DO_NOT_SHOW')
        self.window.analysis_runner=broken
        self.window.run_analysis();self.wait_idle()
        self.assertEqual(self.window.session.runs()[0]['execution_status'],'FAILED')
        self.assertIn('RuntimeError',self.window.analysis_status.text())
        self.assertNotIn('DO_NOT_SHOW',self.window.analysis_status.text())
        self.assertTrue(self.window.run_button.isEnabled())

    def test_single_worker_guard_and_close_guard_gui_delivery(self):
        self.configure_gbm();release=threading.Event();threads=[]
        def delayed(q,r):
            threads.append(QThread.currentThread())
            release.wait(5)
            return fixture_runner(q,r)
        self.window.analysis_runner=delayed
        self.window.run_analysis();self.window.run_analysis()
        self.assertEqual(len(self.window.session.runs()),1)
        self.assertFalse(self.window.close())
        self.window.jobs.succeeded.connect(lambda _:threads.append(QThread.currentThread()))
        release.set();self.wait_idle()
        self.assertNotEqual(threads[0],self.app.thread())
        self.assertEqual(threads[1],self.app.thread())


if __name__ == '__main__':unittest.main()
