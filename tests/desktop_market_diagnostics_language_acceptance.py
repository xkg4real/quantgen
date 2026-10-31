"""Diagnostic display translations keep missing evidence, numbers and reports."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import json
import unittest
from unittest.mock import patch
from tests.ar1_decay_acceptance import etf_fixture, crypto_fixture
from tests.quote_coverage_acceptance import output, board
from tests.desktop_fx_language_acceptance import numbers
from core.ficc import equity_deriv as ED
from core.research.decay_disclosure import decay_text
from core.research.funding_disclosure import funding_text
from core.research.quote_coverage import quote_coverage, quote_coverage_text
from quantgen_desktop.market_diagnostics_language import decay_korean, funding_korean, coverage_korean
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.localization import UiLabel
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEvent


class MarketDiagnosticLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.validate.load_cards',
                       'core.quant.gate_ledger.family_ledger'):
            p=patch(target,side_effect=AssertionError('live I/O forbidden'))
            p.start(); self.addCleanup(p.stop)

    def same_numbers(self,en,ko):
        self.assertEqual(sorted(numbers(en)),sorted(numbers(ko)))

    def test_decay_branch_meaning_units_and_missing_estimate(self):
        cases=[None, {'status':'NOT_ESTIMATED'},
               {'status':'NO_MEMORY','phi':0.,'half_life':0.},
               *[{'status':'NON_DECAYING','phi':p,'half_life':None} for p in (-1.01,1.,1.01)],
               {'status':'OSCILLATING','phi':-.7123,'half_life':2.456},
               {'status':'MONOTONE','phi':.7123,'half_life':2.456}]
        for info in cases:
            ko=decay_korean(info);self.same_numbers(decay_text(info),ko)
            status=(info or {}).get('status')
            if status in ('OSCILLATING','MONOTONE'):
                self.assertIn('관측 후 절반',ko)
                self.assertIn('정상성 검정이나 진입 시점 신호가 아닙니다',ko)
                self.assertEqual('부호가 진동' in ko,status=='OSCILLATING')
            if status=='NON_DECAYING': self.assertIn('유한한 반감기가 없으며',ko)
            if status in (None,'NOT_ESTIMATED'): self.assertIn('느린 평균회귀의 근거가 아닙니다',ko)
        future={'status':'FUTURE_STATUS','phi':.5,'half_life':1.}
        self.assertEqual(decay_korean(future),decay_text(future))

    def test_funding_branches_signs_assumptions_and_raw_reason(self):
        for p in (None,0.,.123456,1.):
            d={'p_lower':p,'cyclic_shifts':79,'forward_observations':30,
               'top_count':12,'bottom_count':13,'reason':'PROVIDER 원문 78.90'}
            fc=SimpleNamespace(diagnostic=d,top_decile_fwd30=-.01234,bottom_decile_fwd30=.02345)
            ko=funding_korean(fc);self.same_numbers(funding_text(fc),ko)
            for warning in ('독립 표본이 아닙니다','p는 폐기했습니다','검증되지 않았습니다',
                            '공식 검증이 아닙니다','유효한 확인 근거가 아닙니다','재검증하지 않습니다'):
                self.assertIn(warning,ko)
            if p is None:self.assertIn(d['reason'],ko)
            else:self.assertIn(f'p={p:.4g}',ko)
        fc=SimpleNamespace(top_decile_fwd30=0.,bottom_decile_fwd30=0.)
        self.same_numbers(funding_text(fc),funding_korean(fc))
        self.assertIn('unknown',funding_korean(fc))

    def test_quote_counts_missing_zero_partial_and_external_scope(self):
        for n in range(4):
            for partial in (False,True):
                q=board()[:n]
                if partial:q=[replace(v,put_bid=None,put_ask=None) for v in q]
                for parity in ([],[{'within':True},{'within':False},{'within':None}]):
                    c=quote_coverage(ED.static_arbitrage(q,quoted_only=True),parity)
                    en,ko=quote_coverage_text(c),coverage_korean(c)
                    self.same_numbers(en,ko)
                    self.assertEqual(en.count('NOT_RUN'),ko.count('NOT_RUN'))
                    self.assertNotIn('nan%',ko)
                    self.assertIn('공식 연구 판정의 근거가 아닙니다',ko)
                    for key,check in c['static'].items():
                        self.assertIn(key,ko)
                        if not check['tests']:self.assertIn(key+': NOT_RUN',ko)
        c['scope']='External scope 원문 123';self.assertTrue(coverage_korean(c).endswith(c['scope']+'.'))

    def test_native_switch_new_results_and_clear_preserve_reports_and_identifiers(self):
        w=ResearchWindow(auto_refresh=False,language='ko')
        try:
            for pane,out in ((w.etf,etf_fixture()),(w.crypto,crypto_fixture()),
                             (w.derivatives,output(False)),(w.derivatives,output(True))):
                pane.show_result(out);pane.bind_output('Diagnostic fixture',out)
                report=deepcopy(pane.report);sections=deepcopy(pane.sections)
                # Warm-up NaNs in chart arrays are missing data, not unequal evidence.
                raw_sections_json=json.dumps(sections,sort_keys=True,default=lambda value:value.item())
                inputs=deepcopy(pane.values());source=pane.source.currentData()
                labels=[v for v in pane.findChildren(UiLabel) if getattr(v,'localized_text',{})]
                self.assertGreater(len(labels),0)
                originals=[v.source_text for v in labels]
                raw_sections=[s['text'] for s in sections if s['type']=='text']
                for original in originals:self.assertIn(original,raw_sections)
                with patch.object(w.jobs,'start',side_effect=AssertionError('no recomputation')):
                    for lang in ('en','ko','en','ko'):
                        w.set_language(lang)
                        for label,original in zip(labels,originals):
                            self.assertEqual(label.text(),label.localized_text[lang])
                            self.assertEqual(label.source_text,original)
                        self.assertEqual(pane.report,report)
                        self.assertEqual(json.dumps(pane.sections,sort_keys=True,default=lambda value:value.item()),raw_sections_json)
                        self.assertEqual(pane.values(),inputs);self.assertEqual(pane.source.currentData(),source)
                pane.clear_result();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
                self.assertIsNone(pane.report);self.assertFalse(pane.has_result)
        finally:
            # A failed assertion must not open the interactive unsaved-session dialog.
            for pane in (w.etf,w.crypto,w.derivatives):pane.clear_result()
            w.deleteLater();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)


if __name__=='__main__':unittest.main()
