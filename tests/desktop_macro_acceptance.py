"""Macro v2 native views on public synthetic schema fixtures; no actual stores."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.macro_records import MacroRecordRequest, MacroRecordOutput, execute_macro_records, display_fields
    from ui import macro_state_panel as original
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtTest import QTest


def fixture_view():
    path = Path(__file__).parent / 'fixtures/macro/schema_examples.json'
    state = json.loads(path.read_text(encoding='utf-8'))['macro_state']
    return {'state': state, 'overlays': [], 'context_log': None, 'event_calendar': None,
            'alerts': [], 'owner_items': {}}


class MacroActionTests(unittest.TestCase):
    def test_nested_regime_is_excluded_from_display(self):
        self.assertEqual(display_fields({'nested': [{'regime_state': 'hidden', 'label': 'visible'}]}), {'nested': [{'label': 'visible'}]})

    def test_invalid_actions_refuse_before_backend(self):
        backend = Mock(side_effect=AssertionError('backend called'))
        for q in (MacroRecordRequest(tool='cards', action='run_live'), MacroRecordRequest(market='INVALID'),
                  MacroRecordRequest(action='ack'), MacroRecordRequest(source='invalid')):
            with self.assertRaises(ValueError): execute_macro_records(q, backend=backend)
        backend.assert_not_called()

    def test_live_prerequisite_failure_never_runs_pipeline(self):
        with tempfile.TemporaryDirectory() as root, \
             patch('config.macro_dir', return_value=Path(root)), \
             patch.object(original, 'live_missing', return_value=['signed calendars']), \
             patch.object(original.MD, 'run_decision') as run:
            with self.assertRaises(ValueError): execute_macro_records(MacroRecordRequest(action='run_live'))
            run.assert_not_called()
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_stale_alert_and_invalid_halt_are_not_acknowledged(self):
        with tempfile.TemporaryDirectory() as root, patch('config.macro_dir', return_value=Path(root)), \
             patch.object(original, 'load_view', return_value={'state': {'quarantined_utc': 'fixture'}}), \
             patch('core.skills.alerts.AlertStore') as store, patch.object(original.BK, 'acknowledge') as ack:
            store.return_value.open.return_value = []
            for kind in ('alert', 'halt'):
                with self.assertRaises(ValueError):
                    execute_macro_records(MacroRecordRequest(action='ack', kind=kind, ident='missing'))
            store.return_value.acknowledge.assert_not_called(); ack.assert_not_called()
            self.assertEqual(list(Path(root).iterdir()), [])


class NativeMacroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = ResearchWindow(auto_refresh=False)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.wait_idle()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes): self.window.close()
        self.window.deleteLater(); self.app.processEvents()

    def wait_idle(self):
        for _ in range(2000):
            self.app.processEvents()
            if not self.window.jobs.busy: return
            QTest.qWait(10)
        self.fail('Worker did not finish')

    def render(self, kind, data):
        p = self.window.macro_records
        self.window.macro_records_runner = lambda q: MacroRecordOutput(q, deepcopy(data))
        p.tool.setCurrentIndex(p.tool.findData(kind)); p.submit(); self.wait_idle()
        return p

    def test_valid_state_keeps_recorded_values_and_separates_display_only_books(self):
        data = fixture_view()
        p = self.render('overlay', data)
        self.assertTrue(p.has_result, p.status.text())
        self.assertIn('recommended:KR', p.tables)
        rows = next(s['rows'] for s in p.sections if s.get('name') == 'recommended:KR')
        expected = data['state']['concentration']['by_book']['recommended:KR']['composed']
        self.assertEqual(rows[1][1], f'{expected:,.4f}')
        self.assertIn('Display-only books · not a recommendation', p.tables)
        self.assertEqual(p.report['verdict'], 'NOT_RUN')

    def test_missing_quarantined_and_acting_errors_show_no_numbers_or_exports(self):
        good = fixture_view()
        self.render('overlay', good)
        for state in (None, {'quarantined_utc': 'fixture', 'secret_number': 987654321},
                      {'schema': 'macro_state', 'runtime': [{'engine_state': 'INVALID'}]}):
            data = deepcopy(good); data['state'] = state
            p = self.render('overlay', data)
            self.assertIn('Owner decisions / inputs / proposals', p.tables)
            self.assertFalse(p.has_result)
            self.assertIsNone(p.report)
            self.assertNotIn('987654321', str(p.sections))
            self.assertFalse(p.export_json.isEnabled())

    def test_card_verdict_is_distinct_from_disposition_and_invalid_view_does_not_crash(self):
        data = {'cards': [{'card_id': 'A', 'verdict': 'NOT_RUN', 'disposition': 'BUILD_AS_INSURANCE'},
                          {'card_id': 'B', 'verdict': 'REJECT', 'rerun': False},
                          {'card_id': 'C', 'verdict': 'BUILD_AS_INSURANCE'}],
                'verdicts': [], 'gate_status': {'status': 'NOT_FROZEN', 'reasons': ['fixture']},
                'headers': [], 'techfund': [], 'cry1': []}
        p = self.render('cards', data)
        rows = [r for s in p.sections if s.get('type') == 'table' for r in s['rows']]
        by_id = {r[0]: r for r in rows}
        self.assertEqual(by_id['A'][1:3], ['NOT_RUN', 'BUILD_AS_INSURANCE'])
        self.assertEqual(by_id['B'][1], 'REJECT')
        self.assertEqual(by_id['C'][1], 'INVALID')
        p = self.render('cards', {})
        self.assertIn('FAILED', p.status.text()); self.assertIsNone(p.report)

    def test_research_view_is_explicit_and_searchable_without_sizing(self):
        p = self.window.macro_records
        self.assertFalse(p.has_result)
        data = {'tf': {'weights': [{'name': 'fixture', 'weight': 3}], 'register': [{'status': 'OWNER-DECISION'}]},
                'backlog': {'items': [{'id': 'DNB-fixture'}]}, 'council': {'resolutions': ['synthetic']}}
        p = self.render('research', data)
        self.assertTrue(p.has_result)
        self.assertIn('Design priors · not gate PASS', p.tables)
        self.assertIn('OWNER-DECISION', str(p.sections))
        self.assertFalse(p.live_button.isEnabled())


if __name__ == '__main__': unittest.main()
