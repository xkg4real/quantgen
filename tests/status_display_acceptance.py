"""System status displays use verified temporary evidence; no providers or real stores."""
from copy import deepcopy
from dataclasses import fields
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import flet as ft
from PyQt6.QtWidgets import QApplication, QFrame, QVBoxLayout, QWidget

from core.i18n import LocaleContext
from core.recorded_status_display import recorded_status_display
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.localization import LanguageController, UiLabel
from tools.status.snapshot import START, END, collect, render, verify
from ui import research_home
from ui.localization import translate_controls


def walk(control):
    if not isinstance(control, ft.Control):
        return
    yield control
    for field in fields(control):
        if field.name.startswith('_'):
            continue
        value = getattr(control, field.name)
        for child in value if isinstance(value, list) else [value]:
            yield from walk(child)


class InertPane(QWidget):
    def __init__(self, *args):
        super().__init__()
        self.requested = SimpleNamespace(connect=lambda callback: None)


class SystemHost(QWidget):
    """Use the real System builder without starting ResearchWindow services."""
    def __init__(self):
        super().__init__()
        self.ctx = LocaleContext('en_US')
        self.ui_language = 'en'
        self.paper_session = object()

    def page(self, *args):
        return QVBoxLayout(self)

    def change_language(self, *args):
        raise AssertionError('A render must not change settings')

    def run_tool(self, *args):
        raise AssertionError('A render must not call a provider')


class StatusDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='quantgen-status-display-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'qa').mkdir()
        (self.root / 'core/calendars/data').mkdir(parents=True)
        (self.root / 'README.md').write_text(
            'QUANTGEN is a commercial quantitative finance research application.\n'
            "As of 2026-10-30, QUANTGEN's commercial launch is an owner-approved decision\n"
            'gate.package.status = NOT_FROZEN\n' + START + END, encoding='utf-8')
        self.qa = self.root / 'qa/acceptance_results.json'
        self.qa.write_text(json.dumps([{'test': 'ok', 'status': 'PASS'},
                                       {'test': 'pending', 'status': 'NOT_RUN'}]), encoding='utf-8')
        (self.root / 'core/calendars/data/MANIFEST.yaml').write_text(
            "version: 1.0.0\nsigned_off_by: fixture\nsigned_utc: '2026-10-29T00:00:00Z'\n"
            'rows:\n- file: fixture.yaml\n  signed_off_by: fixture\n  md5: synthetic-only\n', encoding='utf-8')
        self.status = collect(self.root, '2026-11-06T01:02:03+00:00')
        readme = self.root / 'README.md'
        readme.write_text(readme.read_text(encoding='utf-8').split(START)[0] + render(self.status), encoding='utf-8')
        self.snapshot = self.root / 'qa/research_status.json'
        self.snapshot.write_text(json.dumps(self.status), encoding='utf-8')
        self.status = verify(self.root)

    def browser(self):
        page = SimpleNamespace(qg_locale=LocaleContext('en_US'))
        with patch.object(research_home, 'ROOT', self.root), \
             patch('ui.data_rights.DataRightsPanel', side_effect=lambda page: ft.Text('fixture rights')):
            built = research_home.build_system_page(page, navigate=lambda route: None)
        return next(c for c in walk(built) if isinstance(c, research_home.RecordedStatusView))

    def native(self):
        host = SystemHost()
        self.addCleanup(host.deleteLater)
        with patch('quantgen_desktop.app.application_root', return_value=self.root), \
             patch('quantgen_desktop.connections.ConnectionsPane', InertPane), \
             patch('quantgen_desktop.paper.RulesPane', InertPane), \
             patch('quantgen_desktop.data_rights.DataRightsPane', InertPane):
            ResearchWindow.make_system(host)
        host.localizer = LanguageController(host)
        box = next(w for w in host.findChildren(QFrame) if w.property('recorded_project_status'))
        return host, box

    def browser_text(self, view, locale):
        translate_controls(view, LocaleContext(locale))
        return [control.value for control in view.controls]

    def native_text(self, host, box, locale):
        host.ctx = LocaleContext(locale)
        host.ui_language = host.ctx.language
        host.localizer.apply()
        return [item.text() for item in box.findChildren(UiLabel)
                if getattr(item, 'localized_text', None)]

    def assert_failure_in_both(self):
        browser = self.browser()
        host, native = self.native()
        for locale in ('en_US', 'ko_KR', 'en_US'):
            with self.subTest(locale=locale):
                browser_lines = self.browser_text(browser, locale)
                self.assertEqual(browser_lines, self.native_text(host, native, locale))
                self.assertEqual(len(browser_lines), 2)
                text = '\n'.join(browser_lines)
                for code in ('OWNER_APPROVED', 'COMMERCIAL', 'NOT_FROZEN', 'NOT_INSPECTED', 'NOT_VERIFIED'):
                    self.assertNotIn(code, text)
                self.assertNotIn('2026-10-30', text)

    def test_verified_status_is_identical_in_both_views_through_locale_roundtrip(self):
        browser = self.browser()
        host, native = self.native()
        initial = self.browser_text(browser, 'en_US')
        for locale in ('en_US', 'ko_KR', 'en_US', 'ko_KR', 'en_US'):
            with self.subTest(locale=locale):
                browser_lines = self.browser_text(browser, locale)
                self.assertEqual(browser_lines, self.native_text(host, native, locale))
                text = '\n'.join(browser_lines)
                for value in ('COMMERCIAL', 'OWNER_APPROVED', '2026-10-30', 'NOT_VERIFIED',
                              'NOT_FROZEN', 'NOT_INSPECTED', '1 PASS / 0 FAIL / 1 NOT_RUN',
                              '2026-10-29T00:00:00Z', '2026-11-06T01:02:03+00:00'):
                    self.assertIn(value, text)
                self.assertNotIn('NOT_APPROVED', text)
        self.assertEqual(initial, self.browser_text(browser, 'en_US'))

    def test_owner_decision_is_separate_from_regulatory_readiness_and_publication(self):
        lines = recorded_status_display(self.status)
        english = '\n'.join(line.en for line in lines)
        korean = '\n'.join(line.ko for line in lines)
        self.assertIn('owner decision OWNER_APPROVED', english)
        self.assertIn('not regulatory endorsement or technical readiness', english)
        self.assertIn('Actual public release is not established', english)
        self.assertIn('소유자 결정 OWNER_APPROVED', korean)
        self.assertIn('규제 승인이나 기술 준비 완료를 뜻하지 않습니다', korean)
        self.assertIn('실제 공개 배포 여부는 확인되지 않습니다', korean)

    def test_formatter_and_views_do_not_mutate_verified_snapshot(self):
        before = deepcopy(self.status)
        disk_before = self.snapshot.read_text(encoding='utf-8')
        view = research_home.RecordedStatusView(self.status, LocaleContext('en_US'))
        with patch('quantgen_desktop.app.verify', return_value=self.status):
            host, native = self.native()
        for locale in ('en_US', 'ko_KR', 'en_US'):
            self.browser_text(view, locale)
            self.native_text(host, native, locale)
        self.assertEqual(self.status, before)
        self.assertEqual(self.snapshot.read_text(encoding='utf-8'), disk_before)

    def test_generation_time_is_not_presented_as_a_test_or_publication_time(self):
        lines = recorded_status_display(self.status)
        generated = [line for line in lines if self.status['generated_at'] in line.en]
        self.assertEqual(len(generated), 1)
        self.assertTrue(generated[0].en.startswith('Snapshot generated at:'))
        self.assertTrue(generated[0].ko.startswith('상태 자료 생성 시각:'))
        self.assertTrue(any('source records no run time or commit' in line.en for line in lines))
        self.assertIsNone(self.status['code_test']['run_at'])
        self.assertIsNone(self.status['code_test']['run_commit'])

    def test_missing_snapshot_shows_no_approval(self):
        self.snapshot.unlink()
        self.assert_failure_in_both()

    def test_missing_source_shows_no_approval(self):
        self.qa.unlink()
        self.assert_failure_in_both()

    def test_stale_source_shows_no_approval(self):
        self.qa.write_text(json.dumps([{'test': 'changed', 'status': 'FAIL'}]), encoding='utf-8')
        self.assert_failure_in_both()

    def test_tampered_policy_shows_no_approval(self):
        tampered = deepcopy(self.status)
        tampered['distribution_policy']['public_release'] = 'PUBLISHED'
        self.snapshot.write_text(json.dumps(tampered), encoding='utf-8')
        self.assert_failure_in_both()

    def test_unreadable_snapshot_shows_no_approval(self):
        self.snapshot.write_text('{invalid json', encoding='utf-8')
        self.assert_failure_in_both()

    def test_malformed_calendar_yaml_shows_no_approval(self):
        (self.root / 'core/calendars/data/MANIFEST.yaml').write_text('rows: [', encoding='utf-8')
        self.assert_failure_in_both()

    def test_system_critical_panels_keep_a3_protection(self):
        host, native = self.native()
        self.assertTrue(native.property('reading_help_keep_visible'))
        for item in (host.locale_notice, host.connections, host.rules, host.data_rights):
            self.assertTrue(item.property('reading_help_keep_visible'))
        for item in native.findChildren(UiLabel):
            parent = item
            while parent is not None and not parent.property('reading_help_keep_visible'):
                parent = parent.parentWidget()
            self.assertIs(parent, native)


if __name__ == '__main__':
    unittest.main()
