"""Authored rates display text must retain numbers, branches and source reports."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from tests.desktop_acceptance import rates_fixture
from tests.desktop_fx_language_acceptance import numbers
from core.research.rates_analysis import RatesRequest
from core.ficc import insights
from quantgen_desktop.rates_narrative import rates_korean, curve_korean, simulation_korean, SHAPES, REGIMES
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication


class RatesLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        blocked = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        blocked.start(); self.addCleanup(blocked.stop)

    def test_curve_fit_methods_pca_and_synthetic_disclosure(self):
        for method in ('bootstrap','nelson_siegel','svensson'):
            out = rates_fixture(RatesRequest(method=method,source='synthetic'))
            ko = rates_korean(out)
            self.assertEqual(numbers(out.narrative),numbers(ko))
            self.assertIn('SYNTHETIC',ko)
            self.assertIn('시장이 아닌 생성기',ko)
            self.assertIn('PCA 설명 분산',ko)
            self.assertIn(SHAPES[out.report.shape],ko)
            self.assertIn(REGIMES[out.report.regime],ko)

    def test_curve_without_pca_unknown_labels_and_missing_changes(self):
        out = rates_fixture(RatesRequest(source='synthetic'))
        r = replace(out.report,changes={},shape='future-shape',regime='future-regime')
        self.assertEqual(numbers(insights.narrate_curve(r)),numbers(curve_korean(r)))
        self.assertIn('future-shape',curve_korean(r)); self.assertIn('n/a',curve_korean(r))
        self.assertNotIn('PCA',curve_korean(r))
        pca = replace(out.pca,latest_scores=np.array([1.2]),labels=('unknown-component',))
        self.assertEqual(numbers(insights.narrate_curve(r,pca)),numbers(curve_korean(r,pca)))
        self.assertIn('unknown-component',curve_korean(r,pca))

    def test_swap_pay_receive_fixed_and_par_preserve_signs(self):
        for pay in (True,False):
            for fixed in (None,.08):
                out = rates_fixture(RatesRequest(tool='swap',source='synthetic',pay_fixed=pay,fixed_rate=fixed))
                ko = rates_korean(out)
                self.assertEqual(numbers(out.narrative),numbers(ko))
                self.assertIn('지급합니다' if pay else '수취합니다',ko)
                self.assertIn('곡선이 실현되면',ko)
                r = replace(out.report,krd={})
                self.assertEqual(numbers(insights.narrate_swap(r)),numbers(rates_korean(replace(out,report=r))))

    def test_option_kind_model_side_and_original_notes(self):
        for kind in ('swaption','cap','floor'):
            for model,vol in (('bachelier',.008),('black',.3)):
                for pay in (True,False):
                    out = rates_fixture(RatesRequest(tool='option',source='synthetic',kind=kind,
                        option_model=model,vol=vol,pay_fixed=pay,tenor='5y'))
                    ko = rates_korean(out)
                    self.assertEqual(numbers(out.narrative),numbers(ko))
                    self.assertIn('Bachelier' if model=='bachelier' else 'Black-76',ko)
                    if out.report.note: self.assertIn(out.report.note,ko)

    def test_unavailable_auxiliary_conversion_is_not_presented_as_success(self):
        out = rates_fixture(RatesRequest(tool='option',source='synthetic',strike=-.01))
        self.assertEqual(out.report.other_model_status,'UNAVAILABLE')
        ko = rates_korean(out)
        self.assertEqual(numbers(out.narrative),numbers(ko))
        self.assertNotIn('같은 프리미엄을 다른 모형으로 환산',ko)
        self.assertIn(out.report.note,ko)
        self.assertEqual(out.report.other_model_status,'UNAVAILABLE')

    def test_simulation_models_horizon_valuation_and_optional_evidence(self):
        for model,instrument in (('vasicek','none'),('cir','bond'),('hull_white','swap')):
            out = rates_fixture(RatesRequest(tool='sim',source='synthetic',model=model,instrument=instrument,
                                            horizon=.25,n_paths=100,threshold=.05))
            ko = rates_korean(out)
            self.assertEqual(numbers(out.narrative),numbers(ko))
            self.assertIn('초과할 확률',ko)
            self.assertEqual('기대 초과손실' in ko, instrument!='none')
            for note in (out.report.params.note,out.report.note):
                if note:self.assertIn(note,ko)
            r = replace(out.report,threshold=None,prob_above=None,model_curve_at_horizon=())
            self.assertEqual(numbers(insights.narrate_ratesim(r)),numbers(simulation_korean(r)))
            self.assertNotIn('초과할 확률',simulation_korean(r))
            self.assertNotIn('중앙 경로의 종료 시점 곡선',simulation_korean(r))

    def test_language_switch_restores_exact_sources_without_export_mutation(self):
        w = ResearchWindow(auto_refresh=False,language='ko');self.addCleanup(w.deleteLater)
        cases = [RatesRequest(source='synthetic'),RatesRequest(tool='swap',source='synthetic'),
                 RatesRequest(tool='option',source='synthetic'),
                 RatesRequest(tool='option',kind='floor',source='synthetic'),
                 RatesRequest(tool='sim',source='synthetic',horizon=.25,n_paths=100,threshold=.05)]
        with patch.object(w.jobs,'start',side_effect=AssertionError('language must not run jobs')):
            for q in cases:
                out = rates_fixture(q);w.rates.show_result(out);w.rates.bind_output('rates',out)
                before = deepcopy(w.rates.report)
                label = next(v for v in w.rates.findChildren(UiLabel) if v.source_text==out.narrative)
                for lang in ('ko','en','ko','en'):
                    w.set_language(lang)
                    self.assertEqual(label.text(),rates_korean(out) if lang=='ko' else out.narrative)
                    self.assertEqual(w.rates.report,before)
                self.assertTrue(any(s.get('text')==out.narrative for s in before['sections']))

    def test_unknown_tool_has_explicit_fallback(self):
        self.assertIsNone(rates_korean(SimpleNamespace(request=SimpleNamespace(tool='future'),report=None)))


if __name__ == '__main__':unittest.main()
