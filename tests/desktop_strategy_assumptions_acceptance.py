"""Native EN/KO and explicit exports retain interpretation and raw card data."""
from copy import deepcopy
from io import BytesIO
import json
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from tests.strategy_assumptions_acceptance import fixture, flow
from core.research.strategy_assumptions import assumption_lines, historical_card_lines
from core.research.strategy_analysis import StrategyRequest, StrategyOutput
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.model_narrative_language import strategy_variants
from quantgen_desktop.commentary import commentary_payload
from PyQt6.QtWidgets import QApplication, QLabel


class DesktopStrategyAssumptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def test_live_notes_survive_locale_switch_and_json_zip(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden')), \
             patch('core.quant.validate.load_cards', side_effect=AssertionError('cards forbidden')):
            window = ResearchWindow(auto_refresh=False)
            try:
                data = fixture('vol_target', 1, cost=1)
                out = StrategyOutput(StrategyRequest(family='vol_target'), data)
                pane = window.strategy
                pane.show_result(out); pane.bind_output('strategy', out)
                original_report = deepcopy(pane.report)
                for locale in ('en','ko','en'):
                    window.set_language(locale)
                    self.app.processEvents()
                    rendered = '\n'.join(w.text() for w in pane.findChildren(QLabel))
                    for line in assumption_lines(data['assumptions'], locale): self.assertIn(line, rendered)
                    self.assertEqual(pane.report, original_report)
                parsed = json.loads(report_bytes(pane.report))
                self.assertEqual(parsed['verdict'], 'NOT_RUN')
                self.assertIn('not a historical rate curve', str(parsed))
                ai = commentary_payload(pane.report)
                self.assertIn('not a historical rate curve', str(ai))
                self.assertEqual(ai['official_verdict'], 'NOT_RUN')
                with ZipFile(BytesIO(report_bytes(pane.report, bundle=True))) as bundle:
                    self.assertIsNone(bundle.testzip())
                    self.assertIn(b'without subtracting a risk-free return', bundle.read('report.html'))
                ko = strategy_variants(data)['ko']
                for line in assumption_lines(data['assumptions'], 'ko'): self.assertIn(line, ko)
            finally:
                window.strategy.clear_result();window.close();window.deleteLater();self.app.processEvents()

    def test_historical_card_notes_do_not_modify_raw_evidence(self):
        card = flow._study_card({'card_id':'S_E8_synthetic','decision':'REVISE','kind':'strategy',
            'hypothesis':'original dollar-neutral claim','decision_reason':'original reason',
            'stats':{'share_cointegrated':.8},'lines':['original ADF share 80%'],'citations':['source']})
        before = deepcopy(card)
        with patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden')), \
             patch('core.quant.validate.load_cards', side_effect=AssertionError('cards forbidden')):
            window = ResearchWindow(auto_refresh=False)
            try:
                pane = window.strategy
                out = StrategyOutput(StrategyRequest(tool='cards'), {'cards':[card]})
                pane.show_result(out); pane.bind_output('strategy',out)
                for locale in ('en','ko'):
                    window.set_language(locale); self.app.processEvents()
                    rendered = '\n'.join(w.text() for w in pane.findChildren(QLabel))
                    for line in historical_card_lines(card,locale): self.assertIn(line,rendered)
                    self.assertIn('original dollar-neutral claim',rendered)
                    self.assertIn('original ADF share 80%',rendered)
                parsed = json.loads(report_bytes(pane.report))
                self.assertIn('not an Engle–Granger cointegration p-value or pass rate',str(parsed))
                self.assertIn('original ADF share 80%',str(parsed))
                ai = commentary_payload(pane.report)
                self.assertIn('not an Engle–Granger cointegration p-value or pass rate',str(ai))
                self.assertIn('original ADF share 80%',str(ai))
                self.assertEqual(card,before)
            finally:
                window.strategy.clear_result();window.close();window.deleteLater();self.app.processEvents()


if __name__=='__main__': unittest.main()
