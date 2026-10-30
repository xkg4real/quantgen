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
from core.research.bond_analysis import BondRequest, execute_bond
from core.research.rates_analysis import RatesRequest, execute_rates
from core.research.fx_analysis import FXRequest, execute_fx
from core.research.structuring_analysis import StructuringRequest, execute_structuring
from core.research.signals_analysis import SignalsRequest, execute_signals
from core.research.macro_analysis import MacroRequest, execute_macro
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


def bond_fixture(request):
    from core.ficc.data import synthetic_curve_panel
    panel=synthetic_curve_panel(days=30,seed=23)
    return execute_bond(request,curve_loader=lambda **kwargs:panel)


def rates_fixture(request):
    from core.ficc.data import synthetic_curve_panel, load_short_rate
    panel=synthetic_curve_panel(days=80,seed=23)
    return execute_rates(request,curve_loader=lambda **kwargs:panel,
                         rate_loader=lambda c,**kw:load_short_rate(c,source='synthetic',days=120))


def fx_fixture(request):
    from core.ficc.data import synthetic_fx, load_short_rate, load_policy_rates
    return execute_fx(request,spot_loader=lambda p,**kw:synthetic_fx(p.replace('/',''),days=kw.get('days',120)),
        rate_loader=lambda c,**kw:load_short_rate(c,source='synthetic',days=120),
        policy_loader=lambda c,**kw:load_policy_rates(c,source='synthetic',days=kw.get('days',120)))


def structuring_fixture(request):
    from core.ficc.data import synthetic_curve_panel
    return execute_structuring(request,curve_loader=lambda **kw:synthetic_curve_panel(days=80,seed=23))


def signals_fixture(request):
    return execute_signals(request,history_loader=lambda *a,**kw:history_fixture())


def macro_fixture(request):
    from core.ficc.macro import macro_sheet
    return execute_macro(request,sheet_loader=lambda **kw:macro_sheet(source='synthetic'))


class AnalysisAdapterTests(unittest.TestCase):
    def test_signals_all_strategies_preserve_costed_backtest(self):
        from core.quant.backtest import run_backtest
        from core.quant.signals import compute_signals
        for tool in ('ma_cross','momentum','rsi_revert'):
            q=SignalsRequest(tool=tool,fast=10,slow=30 if tool=='ma_cross' else 50,cost_bps=17)
            out=signals_fixture(q)
            direct=run_backtest(out.history,strategy=tool,params=q.parameters(),cost_bps=17)
            self.assertEqual(out.backtest.total_return,direct.total_return)
            self.assertEqual(out.report,compute_signals(out.history))
        with self.assertRaises(ValueError):SignalsRequest(fast=60,slow=50).validate()

    def test_macro_narratives_preserve_observations_and_units(self):
        from core.ficc import insights
        from quantgen_desktop.macro import level,change
        from types import SimpleNamespace
        for tool,narrate in (('sheet',insights.narrate_macro),('daily',insights.narrate_daily_brief),('weekly',insights.narrate_weekly_strategy)):
            out=macro_fixture(MacroRequest(tool=tool))
            self.assertEqual(out.narrative,narrate(out.sheet))
            self.assertTrue(out.sheet.synthetic_ids)
        self.assertEqual(level(SimpleNamespace(unit='pct',last=.042)),'4.200%')
        self.assertEqual(change(SimpleNamespace(unit='pct'),.001),'+10.00 bp')
        self.assertEqual(change(SimpleNamespace(unit='fx'),.001),'0.0010')
    def test_structuring_terms_optional_coupon_and_futures_hedge_match_existing_core(self):
        from core.ficc import structured
        cases=[StructuringRequest(),StructuringRequest(tool='rc',maturity='1y',coupon=.1),
               StructuringRequest(tool='dcd',maturity='3m',spot=1350,vol=.09,r_for=.045,margin=.25),
               StructuringRequest(tool='steep',maturity='5y',cap=.05,frequency=2)]
        for q in cases:
            q=replace(q,futures_dv01=65)
            o=structuring_fixture(q);r=o.report
            if q.tool=='ppn':direct=structured.principal_protected_note(o.curve,spot=1.1,vol=.08,r_for_or_div=.02,maturity=3,notional=1e6,margin=1)
            elif q.tool=='rc':direct=structured.reverse_convertible(o.curve,spot=1.1,vol=.08,r_for_or_div=.02,maturity=1,notional=1e6,strike_pct=.95,coupon=.1,margin=1)
            elif q.tool=='dcd':direct=structured.dual_currency_deposit(o.curve,spot=1350,vol=.09,r_for=.045,maturity=.25,notional=1e6,strike=1300,base_ccy='USD',quote_ccy='KRW',margin=.25)
            else:direct=structured.steepener_note(o.curve,maturity=5,notional=1e6,leverage=4,floor=0,cap=.05,freq=2,issue_price=100)
            self.assertEqual(r.fair_value,direct.fair_value);self.assertEqual(r.greeks,direct.greeks)
            hedge=structured.hedge_sheet(direct,curve=o.curve,futures_dv01_per_contract=65)
            self.assertEqual([h.quantity for h in r.hedge],[h.quantity for h in hedge])
        with self.assertRaises(ValueError):
            execute_structuring(StructuringRequest(futures_dv01=0),curve_loader=lambda **kw:self.fail('provider called'))

    def test_rates_branches_match_core_and_do_not_fetch_invalid_requests(self):
        from core.ficc.common import FICCError
        from core.ficc.curves import analyze_curve
        from core.ficc.swaps import analyze_swap, price_swaption, price_cap_floor
        from core.ficc.ratesim import calibrate, simulate
        for method in ('bootstrap','nelson_siegel','svensson'):
            out=rates_fixture(RatesRequest(source='synthetic',method=method))
            direct=analyze_curve(out.panel,method=method,lookback=20)
            self.assertEqual(out.report.descriptors,direct.descriptors)
            self.assertIsNotNone(out.pca)
        for side in (True,False):
            out=rates_fixture(RatesRequest(tool='swap',tenor='5y5y',pay_fixed=side,fixed_rate=.04))
            self.assertEqual(out.report.pv,analyze_swap(out.report.swap,out.curve).pv)
        for kind in ('swaption','cap','floor'):
            for model,vol in (('black',.3),('bachelier',.008)):
                q=RatesRequest(tool='option',kind=kind,option_model=model,vol=vol,tenor='5y',strike=.04,pay_fixed=False)
                out=rates_fixture(q)
                direct=price_swaption(out.report.swaption,out.curve,vol=vol,model=model) if kind=='swaption' else price_cap_floor(out.curve,5,.04,vol=vol,model=model,cap=kind=='cap')
                self.assertEqual(out.report.premium,direct.premium)
        for model,instrument in (('vasicek','none'),('cir','bond'),('hull_white','swap')):
            q=RatesRequest(tool='sim',model=model,instrument=instrument,horizon=.25,n_paths=100,threshold=.05)
            out=rates_fixture(q)
            direct=simulate(calibrate(out.series,model=model),horizon=.25,n_paths=100,threshold=.05,curve=out.curve,seed=7)
            self.assertEqual(out.report.mean_terminal,direct.mean_terminal)
            self.assertEqual(out.report.prob_above,direct.prob_above)
            self.assertEqual(out.horizon_pv is None,instrument=='none')
        for changes in ({'tool':'bad'},{'tool':'option','vol':float('nan')},{'tool':'swap','tenor':'bad'},
                        {'tool':'sim','n_paths':100.5},{'tool':'sim','instrument':'bond','horizon':10,'tenor':'5y'}):
            with self.assertRaises((ValueError,FICCError)):
                execute_rates(RatesRequest(**changes),curve_loader=lambda **kw:self.fail('provider reached'))

    def test_fx_conventions_typed_rates_delta_strikes_and_carry_match_core(self):
        from core.ficc import fx
        for pair in ('EURUSD','USD/KRW'):
            q=FXRequest(pair=pair,domestic_rate=.04,foreign_rate=.03,market_forward=1.12 if pair=='EURUSD' else 1400)
            out=fx_fixture(q);d=out.data
            self.assertEqual(len(out.sources),1)  # typed rates must not fetch a provider
            self.assertEqual(d['forward'],fx.forward(d['S'],.04,.03,.25))
            self.assertEqual(d['basis'],fx.implied_basis(d['S'],q.market_forward,.04,.03,.25))
        for strike,call in (('ATM',True),('25d',False),('1.12',True)):
            out=fx_fixture(FXRequest(tool='option',strike=strike,call=call));r=out.data['report']
            direct=fx.garman_kohlhagen(r.spot,r.strike,r.expiry,r.r_dom,r.r_for,r.vol,call)
            self.assertEqual(r.price,direct.price);self.assertEqual(r.rho_dom,direct.rho_dom)
            if strike=='25d':self.assertAlmostEqual(r.strike,fx.strike_from_delta(.25,r.spot,r.expiry,r.r_dom,r.r_for,.08,call=False))
        out=fx_fixture(FXRequest(tool='carry',days=120,cost_bps=7,top_n=4))
        spots={s.id[:6]:s for s in out.sources[:7]};rates={c:s for c,s in zip(('USD','EUR','JPY','GBP','AUD','CAD','CHF','KRW'),out.sources[7:])}
        direct=fx.carry_backtest(spots,rates,top_n=4,cost_bps=7,rebalance_days=21)
        self.assertEqual(list(out.data['backtest'].equity),list(direct.equity))
        self.assertEqual(out.data['backtest'].top_n,3)
        for changes in ({'tool':'option','strike':'100d'},{'domestic_rate':float('inf')},{'tool':'carry','top_n':1.5}):
            with self.assertRaises(ValueError):
                execute_fx(FXRequest(**changes),spot_loader=lambda *a,**k:self.fail('provider reached'))

    def test_bond_price_scenarios_and_hedge_match_existing_core(self):
        from core.ficc.bonds import analyze_bond,scenario_pnl,futures_hedge_ratio
        for tool in ('calc','scenarios','hedge'):
            out=bond_fixture(BondRequest(source='synthetic',tool=tool))
            a=out.analytics
            direct=analyze_bond(a.bond,ytm=.045,curve=out.curve)
            self.assertEqual(a.price,direct.price);self.assertEqual(a.krd,direct.krd)
            if tool=='scenarios':
                direct_rows=scenario_pnl(a.bond,out.curve,a.price)
                self.assertEqual([r.pnl for r in out.scenarios],[r.pnl for r in direct_rows])
                self.assertEqual(len(out.scenarios),9)
            if tool=='hedge':self.assertEqual(out.hedge[3],futures_hedge_ratio(a.dv01,65,.8))
        with self.assertRaises(ValueError):BondRequest(price=100,yield_rate=.04).validate()
        with self.assertRaises(ValueError):BondRequest(notional=float('nan')).validate()
        with self.assertRaises(ValueError):BondRequest(tool='hedge',ctd_dv01=0).validate()
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
                                   portfolio_runner=portfolio_fixture,bond_runner=bond_fixture,
                                   rates_runner=rates_fixture,fx_runner=fx_fixture,structuring_runner=structuring_fixture,
                                   signals_runner=signals_fixture,macro_runner=macro_fixture)
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

    def test_native_bonds_calculator_scenarios_hedge_and_input_error(self):
        w=self.window;w.navigate('markets');b=w.bonds
        for tool in ('calc','scenarios','hedge'):
            b.tool.setCurrentIndex(b.tool.findData(tool));b.submit();self.wait_idle()
            self.assertEqual(b.metrics.rowCount(),12)
            self.assertEqual(b.krd.rowCount(),9)
            self.assertTrue(b.chart.series)
            self.assertIn('합성 곡선',b.notes.text())
            if tool=='scenarios':self.assertEqual(b.scenarios.rowCount(),9)
            if tool=='hedge':self.assertIn('실제 주문 없음',b.hedge.text())
        b.fields['Price · per 100'].setText('100');b.submit()
        self.assertIn('입력 오류',b.status.text())
        self.assertFalse(w.jobs.busy)

    def test_native_rates_tools_units_locking_and_results(self):
        w=self.window;w.navigate('markets');w.market_tabs.setCurrentWidget(w.rates)
        pane=w.rates
        for tool in ('curve','swap','option','sim'):
            pane.tool.setCurrentIndex(pane.tool.findData(tool))
            if tool=='sim':pane.fields[tool]['n_paths'].setText('100')
            pane.submit()
            self.assertFalse(pane.input_box.isEnabled())
            self.wait_idle()
            self.assertTrue(pane.has_result,pane.status.text())
            self.assertIn('Metrics',pane.tables)
            self.assertTrue(pane.input_box.isEnabled())
        pane.tool.setCurrentIndex(pane.tool.findData('option'))
        pane.fields['option']['option_model'].setCurrentIndex(1)
        self.assertEqual(pane.fields['option']['vol'].text(),'30')
        self.assertEqual(pane.make_request().vol,.3)
        pane.fields['option']['kind'].setCurrentIndex(1)
        self.assertFalse(pane.fields['option']['expiry'].isEnabled())
        pane.submit();self.wait_idle()
        self.assertIn('Caplets',pane.tables)
        w.theme.setCurrentIndex(1);self.app.processEvents()
        self.assertTrue(all(c.colors==w.colors for c in pane.charts.values()))
        pane.fields['option']['tenor'].setText('invalid')
        pane.submit()
        self.assertIn('입력 오류',pane.status.text());self.assertFalse(w.jobs.busy)

    def test_native_fx_all_tools_and_invalid_input_clears_stale_result(self):
        w=self.window;w.navigate('markets');w.market_tabs.setCurrentWidget(w.fx)
        pane=w.fx
        for tool in ('forward','option','carry'):
            pane.tool.setCurrentIndex(pane.tool.findData(tool))
            if tool=='carry':pane.fields[tool]['days'].setText('120')
            pane.submit();self.wait_idle()
            self.assertTrue(pane.has_result,pane.status.text())
            self.assertTrue(pane.charts)
            self.assertGreater(pane.tables['Data sources'].rowCount(),0)
        pane.fields['carry']['top_n'].setText('2.5');pane.submit()
        self.assertIn('입력 오류',pane.status.text());self.assertFalse(pane.has_result)

    def test_native_structuring_all_products_payoff_hedges_and_units(self):
        w=self.window;w.navigate('markets');w.market_tabs.setCurrentWidget(w.structuring)
        pane=w.structuring
        for key in ('ppn','rc','dcd','steep'):
            pane.tool.setCurrentIndex(pane.tool.findData(key))
            pane.fields[key]['futures_dv01'].setText('65')
            pane.submit();self.wait_idle()
            self.assertTrue(pane.has_result,pane.status.text())
            self.assertGreater(pane.tables['Leg decomposition'].rowCount(),0)
            self.assertTrue(pane.charts['Maturity payoff'].series)
        self.assertIn('bp',pane.charts['Maturity payoff'].x_label)

    def test_native_signals_and_macro_do_not_feed_a_book(self):
        w=self.window
        w.signals.submit();self.wait_idle()
        self.assertTrue(w.signals.has_result,w.signals.status.text())
        self.assertGreater(w.signals.tables['Signal components'].rowCount(),0)
        self.assertIn('Costed backtest',w.signals.charts)
        for tool in ('sheet','daily','weekly'):
            w.macro.tool.setCurrentIndex(w.macro.tool.findData(tool));w.macro.submit();self.wait_idle()
            self.assertTrue(w.macro.has_result,w.macro.status.text())
            self.assertGreater(w.macro.tables['Macro indicators'].rowCount(),10)
        self.assertEqual(len(w.session.runs()),0)

    def test_native_volatility_labels_distinguish_sample_and_forecast(self):
        w=self.window;self.configure_gbm()
        for model in ('gbm','garch_t'):
            with self.subTest(model=model):
                w.model.setCurrentIndex(w.model.findData(model));w.run_analysis();self.wait_idle()
                run=w.session.runs()[0];result=w.outputs[run['run_id']].result
                rows={w.quant_metrics.item(i,0).text():w.quant_metrics.item(i,1).text()
                      for i in range(w.quant_metrics.rowCount())}
                expected='Next-session vol (ann.)' if model=='garch_t' else 'Sample vol (ann.)'
                self.assertEqual(rows[expected],f'{result.sigma_annual:.1%}')
                self.assertIn('annualized using 252 sessions',w.quant_notes.text())
                if model=='garch_t':
                    self.assertEqual(rows['Horizon-average vol (ann.)'],f'{result.garch_horizon_vol:.1%}')
                else:self.assertNotIn('Horizon-average vol (ann.)',rows)
                self.assertEqual(run['verdict'],'NOT_RUN')

    def test_terminal_target_label_and_notes_preserve_research_contract(self):
        w=self.window;self.configure_gbm();w.target.setText('100')
        w.run_analysis();self.wait_idle()
        run=w.session.runs()[0];result=w.outputs[run['run_id']].result
        rows={w.quant_metrics.item(i,0).text():w.quant_metrics.item(i,1).text()
              for i in range(w.quant_metrics.rowCount())}
        self.assertEqual(rows['P(terminal ≥ target)'],f'{result.prob_target:.1%}')
        self.assertNotIn('P(target)',rows)
        self.assertIn('final price >= 100.00 after 5 sessions',w.quant_notes.text())
        self.assertEqual(run['verdict'],'NOT_RUN')
        self.assertEqual(run['parameters']['target'],100)
        self.assertEqual(set(run['metrics']),{'spot','p05','p50','p95','prob_loss','var_pct','cvar_pct'})

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
