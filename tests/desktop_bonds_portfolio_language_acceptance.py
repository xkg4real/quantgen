"""Bond/portfolio display languages retain calculations, warnings and raw evidence."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from tests.desktop_acceptance import bond_fixture, portfolio_fixture
from tests.desktop_fx_language_acceptance import numbers
from core.research.bond_analysis import BondRequest
from core.research.portfolio_analysis import PortfolioRequest
from core.research.portfolio_disclosure import portfolio_disclosure
from core.ficc.insights import narrate_bond
from core.quant.insights import narrate_portfolio
from core.quant.history import convention_warning
from core.quant.optimize import optimize_portfolio
from quantgen_desktop.bonds_portfolio_narrative import (
    bond_korean,portfolio_korean,portfolio_scope_korean,model_note_korean,
    bond_notes,portfolio_notes,hedge_text,convention_korean)
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication


class BondsPortfolioLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        blocked = patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden'))
        blocked.start();self.addCleanup(blocked.stop)

    def test_bond_branches_scenarios_and_funding_units(self):
        out = bond_fixture(BondRequest(source='synthetic',tool='scenarios'))
        for total in (-1.123,0,2.456):
            cr = replace(out.analytics.carry_roll,total=total,breakeven_bp=-12.34 if total<0 else 56.78)
            for krd in ({},{2.:0.,10.:0.},out.analytics.krd):
                a = replace(out.analytics,carry_roll=cr,krd=krd)
                for scenarios in ((),out.scenarios):
                    en,ko = narrate_bond(a,scenarios),bond_korean(a,scenarios)
                    self.assertEqual(sorted(numbers(en)),sorted(numbers(ko)))
                    self.assertEqual('하락해야' in ko,total<0)
                    self.assertEqual('상승할 수' in ko,total>=0)
                    self.assertEqual('최악은' in ko,bool(scenarios))
                    self.assertIn('체결 가능한 레포 호가가 아닙니다',ko)
                    self.assertIn('price * (1 / DF(h) - 1)',ko)

    def test_bond_custom_names_and_unknown_notes_remain_verbatim(self):
        out = bond_fixture(BondRequest())
        raw='ISSUER 원문 17.50 — do not translate'
        a=replace(out.analytics,bond=replace(out.analytics.bond,name=raw),note=raw)
        self.assertEqual(bond_korean(a).count(raw),2)
        flat="No curve supplied: flat curve at the bond's own yield; z-spread is trivially 0."
        self.assertIn('자명하게 0',bond_korean(replace(a,note=flat)))
        self.assertEqual(model_note_korean('Provider: '+flat),'Provider: '+flat)
        altered=replace(out,narrative=raw)
        self.assertIn(raw,bond_notes(altered,'ko'))

    def test_all_portfolio_objectives_caps_and_engine_warning_combinations(self):
        for objective in ('max_sharpe','min_vol','risk_parity','equal_weight'):
            for cap in (.1,1.):
                out=portfolio_fixture(PortfolioRequest(('ONE','TWO','THREE'),objective=objective,max_weight=cap))
                p=out.portfolios[objective]
                ko=portfolio_korean(p)
                self.assertEqual(sorted(numbers(narrate_portfolio(p))),sorted(numbers(ko)))
                disclosure=portfolio_disclosure(out.portfolios,objective)['summary']
                scope=portfolio_scope_korean(out.portfolios,objective)
                self.assertEqual(sorted(numbers(disclosure)),sorted(numbers(scope)))
                self.assertIn('동일 조건의 효율적 투자선 비교가 아닙니다',scope)
                self.assertIn('상한 100%',scope)
                self.assertIn('1/N',scope)
                if cap<1:self.assertIn('기존 완전투자 가능 범위',ko)
                p=replace(p,risk_contrib=None,converged=False)
                self.assertEqual(sorted(numbers(narrate_portfolio(p))),sorted(numbers(portfolio_korean(p))))
                self.assertIn('수렴하지 않았으므로',portfolio_korean(p))
                self.assertNotIn('기여합니다',portfolio_korean(p))

    def test_nonpositive_sharpe_solver_failure_and_unknown_note(self):
        out=portfolio_fixture(PortfolioRequest(('ONE','TWO')))
        stats=replace(out.stats,mean_returns=np.array([-.05,-.10]))
        with patch('core.quant.optimize._solve',return_value=(np.array([.5,.5]),False)):
            p=optimize_portfolio(stats,objective='max_sharpe',max_weight=.1)
        ko=portfolio_korean(p)
        self.assertIn('양수가 아닌 샤프비율',ko)
        self.assertIn('위험이 낮은 배분이라는 근거가 아닙니다',ko)
        self.assertIn('수렴을 보고하지 않았으므로',ko)
        self.assertEqual(sorted(numbers(narrate_portfolio(p))),sorted(numbers(ko)))
        unknown=p.note+' external original 123'
        self.assertEqual(model_note_korean(unknown),unknown)
        self.assertEqual(model_note_korean(''), '')
        self.assertIn(unknown,portfolio_korean(replace(p,note=unknown)))

    def test_return_convention_and_synthetic_mixed_sources_keep_evidence(self):
        out=portfolio_fixture(PortfolioRequest(('BUY','시장Symbol')))
        h1=replace(out.histories[0],adjustment='total',source='YFINANCE',note='Provider 원문 45')
        h2=replace(out.histories[1],adjustment='split',note='Original note 67')
        hs=(h1,h2)
        out=replace(out,histories=hs,convention_warning=convention_warning(hs))
        d=portfolio_disclosure(out.portfolios,out.request.objective)
        en,ko=portfolio_notes(out,'en',d),portfolio_notes(out,'ko',d)
        self.assertEqual(sorted(numbers(en)),sorted(numbers(ko)))
        self.assertIn('배당 재투자가 포함',ko);self.assertIn('배당 미포함',ko)
        for source in ('BUY','시장Symbol','Provider 원문 45','Original note 67','005930.KS','NAS:AAPL'):
            self.assertIn(source,ko);self.assertIn(source,en)
        custom=replace(out,convention_warning='CUSTOM 원문 35',narrative='My own note 678')
        self.assertEqual(convention_korean(custom),custom.convention_warning)
        self.assertIn(custom.narrative,portfolio_notes(custom,'ko',d))

    def test_hedge_signs_precision_rounding_and_no_orders(self):
        for pos in (-123.45,0,789.123):
            out=bond_fixture(BondRequest(tool='hedge',position_dv01=pos))
            en,ko=hedge_text(out.hedge,'en'),hedge_text(out.hedge,'ko')
            self.assertEqual(numbers(en),numbers(ko))
            self.assertIn('실제 주문 없음',ko);self.assertIn('no real orders',en)
            self.assertIn('CTD DV01',ko)
        self.assertEqual(hedge_text(None,'ko'),'')

    def test_switch_repeated_results_and_clear_leave_report_tables_chart_unchanged(self):
        w=ResearchWindow(auto_refresh=False,language='ko');self.addCleanup(w.deleteLater)
        with patch.object(w.jobs,'start',side_effect=AssertionError('no jobs on language change')):
            for q in (BondRequest(tool='hedge'),BondRequest(tool='scenarios'),BondRequest()):
                out=bond_fixture(q);w.bonds.show_result(out)
                before=deepcopy(w.bonds.exports.report);raw=w.bonds.notes.source_text
                table_values=[w.bonds.metrics.item(i,1).text() for i in range(w.bonds.metrics.rowCount())]
                prices=deepcopy(w.bonds.chart.series)
                for lang in ('en','ko','en','ko'):
                    w.set_language(lang)
                    self.assertEqual(w.bonds.notes.text(),bond_notes(out,lang))
                    self.assertEqual(w.bonds.hedge.text(),hedge_text(out.hedge,lang))
                    self.assertEqual(w.bonds.exports.report,before)
                    self.assertEqual(w.bonds.notes.source_text,raw)
                    self.assertEqual([w.bonds.metrics.item(i,1).text() for i in range(w.bonds.metrics.rowCount())],table_values)
                    self.assertEqual(w.bonds.chart.series,prices)
                self.assertEqual(next(s['text'] for s in before['sections'] if s['type']=='text'),raw)
            for objective in ('max_sharpe','risk_parity'):
                out=portfolio_fixture(PortfolioRequest(('ONE','TWO','THREE'),objective=objective,max_weight=.1))
                w.portfolio.show_result(out);before=deepcopy(w.portfolio.exports.report);raw=w.portfolio.notes.source_text
                weights=[w.portfolio.weights.item(i,1).text() for i in range(w.portfolio.weights.rowCount())]
                d=portfolio_disclosure(out.portfolios,objective)
                for lang in ('en','ko','en','ko'):
                    w.set_language(lang)
                    self.assertEqual(w.portfolio.notes.text(),portfolio_notes(out,lang,d))
                    if lang=='ko':self.assertIn(portfolio_scope_korean(out.portfolios,objective),w.portfolio.scope.text())
                    else:self.assertEqual(w.portfolio.scope.text(),w.portfolio.scope.source_text)
                    self.assertEqual(w.portfolio.notes.source_text,raw)
                    self.assertEqual(w.portfolio.exports.report,before)
                    self.assertIs(w.portfolio.chart.output,out)
                    self.assertEqual([w.portfolio.weights.item(i,1).text() for i in range(w.portfolio.weights.rowCount())],weights)
            for pane in (w.bonds,w.portfolio):
                pane.clear_result()
                for lang in ('ko','en'):
                    w.set_language(lang);self.assertEqual(pane.notes.text(),'')
                self.assertIsNone(pane.exports.report)


if __name__=='__main__':unittest.main()
