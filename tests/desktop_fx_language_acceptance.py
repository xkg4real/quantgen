"""FX prose translation must preserve every displayed number and source report."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import re
import unittest
from unittest.mock import Mock, patch
from tests.sabr_diagnostics_acceptance import fixture, spot
from core.research.fx_analysis import FXRequest, execute_fx
from core.ficc.sabr_diagnostics import diagnostic_text, fit_diagnostics
from quantgen_desktop.fx_narrative import fx_korean, sabr_korean
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.localization import UiLabel
from PyQt6.QtWidgets import QApplication


def numbers(text):
    return Counter(re.findall(r'[+-]?\d+(?:[.,]\d+)*(?:e[+-]?\d+)?', text))


class FXLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        network.start(); self.addCleanup(network.stop)

    def test_forward_sign_basis_branches_and_display_precision(self):
        for domestic, foreign, market in ((.03,.02,None), (.02,.03,1.13), (.03,.02,1.09), (.03,.02,1.1055)):
            q = FXRequest(tool='forward', source='synthetic', domestic_rate=domestic,
                          foreign_rate=foreign, market_forward=market, tenor='6m')
            out = execute_fx(q, spot_loader=lambda *a, **kw: spot(),
                             rate_loader=Mock(side_effect=AssertionError('no provider')))
            korean = fx_korean(out)
            self.assertEqual(numbers(out.narrative), numbers(korean))
            self.assertIn('환율 예측값이 아닙니다', korean)
            self.assertIn('얻습니다' if out.data['carry'] >= 0 else '지급합니다', korean)
            if market is None: self.assertNotIn('베이시스', korean)

    def test_option_both_sides_and_solver_evidence_preserved(self):
        for call in (True, False):
            q = FXRequest(tool='option', source='synthetic', call=call, strike='.9',
                          domestic_rate=.03, foreign_rate=.02, tenor='1w', rr=-.03, bf=.02)
            out = execute_fx(q, spot_loader=lambda *a, **kw: spot(),
                             rate_loader=Mock(side_effect=AssertionError('no provider')))
            before = deepcopy(out.data['sabr_diagnostics'])
            korean = fx_korean(out)
            self.assertEqual(numbers(out.narrative), numbers(korean))
            self.assertIn('콜' if call else '풋', korean)
            self.assertIn('EXTRAPOLATION', korean)
            self.assertIn('독립 검증: NOT_RUN; 차익거래 검증: NOT_RUN', korean)
            self.assertIn('입증하지 않습니다', korean)
            self.assertEqual(before, out.data['sabr_diagnostics'])

    def test_missing_residuals_and_unreported_bounds_stay_missing(self):
        out = fixture()
        fit = replace(out.data['fit'], active_bounds=None, converged=False)
        d = fit_diagnostics(fit, out.data['forward'], out.data['report'].expiry)
        text = sabr_korean(d)
        self.assertEqual(numbers(diagnostic_text(d)), numbers(text))
        self.assertIn('호가 잔차 NOT_RUN', text)
        self.assertIn('활성 경계: 미보고', text)
        self.assertIn('NOT_CONVERGED', text)
        self.assertIsNone(d['rmse_vol_points'])

    def test_visible_korean_switches_back_to_exact_original_and_preserves_export(self):
        w = ResearchWindow(auto_refresh=False, language='ko')
        self.addCleanup(w.deleteLater)
        out = fixture()
        w.fx.show_result(out); w.fx.bind_output('fx', out)
        before = deepcopy(w.fx.report)
        narrative = next(x for x in w.fx.findChildren(UiLabel) if x.source_text == out.narrative)
        self.assertEqual(narrative.text(), fx_korean(out))
        self.assertTrue(any(s.get('text') == out.narrative for s in before['sections']))
        for language in ('en', 'ko', 'en'):
            w.set_language(language)
            self.assertEqual(narrative.text(), out.narrative if language == 'en' else fx_korean(out))
            self.assertEqual(before, w.fx.report)

    def test_replacing_message_discards_the_previous_translation(self):
        w = ResearchWindow(auto_refresh=False, language='ko')
        self.addCleanup(w.deleteLater)
        widget = w.fx.text('Original', localized={'ko': '원문'})
        self.assertEqual(widget.text(), '원문')
        widget.setText('New source')
        self.assertEqual(widget.text(), 'New source')

    def test_unsupported_narrative_is_explicitly_not_translated(self):
        from types import SimpleNamespace
        out = SimpleNamespace(request=SimpleNamespace(tool='carry'), data={})
        self.assertIsNone(fx_korean(out))


if __name__ == '__main__': unittest.main()
