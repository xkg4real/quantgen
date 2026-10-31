"""Hermetic UI behavior checks. Builders/engine/start hook use inert fixtures."""
from __future__ import annotations

import sys
from dataclasses import fields
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import dotenv
import flet as ft

# Import config without reading a local/ancestor .env.
with patch.object(dotenv, 'load_dotenv', return_value=False):
    import main as app
from ui import research_home
from core.theme import LIGHT, set_mode


def walk(value, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(value, ft.Control) or id(value) in seen:
        return
    seen.add(id(value))
    yield value
    for field in fields(value):
        if field.name.startswith('_'):
            continue
        child = getattr(value, field.name)
        if isinstance(child, ft.Control):
            yield from walk(child, seen)
        elif isinstance(child, list):
            for item in child:
                yield from walk(item, seen)


class Page:
    width = 1440
    window = None
    def __init__(self):
        self.window = SimpleNamespace(); self.controls = []; self.dialog = None
    def add(self, control): self.controls.append(control)
    def update(self): pass
    def show_dialog(self, dialog): self.dialog = dialog
    def pop_dialog(self): self.dialog = None


class ResearchHomeTests(unittest.TestCase):
    def setUp(self):
        self.page = Page(); self.calls = {}; self.built = {}; self.rules_changed = None
        self.start = unittest.mock.Mock()
        hook = SimpleNamespace(on_app_start=self.start)
        p = patch.dict(sys.modules, {'core.skills.macro_daily': hook}); p.start(); self.addCleanup(p.stop)
        for name in ('KRXGateway', 'RuleStore', 'QuoteFeed', 'EngineRuntime'):
            p = patch.object(app, name); mock = p.start(); self.addCleanup(p.stop)
            setattr(self, name, mock)
        for route, _, _ in app.NAV:
            names = {'lab': 'strategy_lab', 'quant': 'quant_lab'}
            name = 'build_' + names.get(route, route) + '_page'
            def builder(*args, key=route, **kwargs):
                self.calls[key] = self.calls.get(key, 0) + 1
                if key == 'rules': self.rules_changed = kwargs['on_changed']
                view = ft.Text('fixture ' + key); self.built[key] = view
                return view
            p = patch.object(app, name, side_effect=builder); p.start(); self.addCleanup(p.stop)
        app.main(self.page)

    def controls(self):
        return [c for root in self.page.controls for c in walk(root)]

    def go(self, route):
        menu = next(c for c in self.controls() if c.data == 'mobile-menu')
        menu.on_click(None)
        buttons = [c for c in walk(self.page.dialog) if c.data == {'route': route}]
        self.assertTrue(buttons, route)
        buttons[-1].on_click(None)
        self.assertIsNone(self.page.dialog)

    def test_default_home_no_analysis_build_and_start_hook_once(self):
        self.assertEqual(self.calls, {})
        self.assertTrue(any(isinstance(c, ft.Text) and c.value == '리서치 홈' for c in self.controls()))
        self.assertEqual(self.page.theme_mode, ft.ThemeMode.LIGHT)
        self.assertEqual(self.page.bgcolor, LIGHT.bg)
        self.start.assert_called_once_with(background=True)
        self.EngineRuntime.assert_called_once()

    def test_all_legacy_routes_and_six_workspaces_survive(self):
        self.assertEqual(len(app.WORKSPACES), 6)
        legacy = {key for key, _, _ in app.NAV}
        grouped = [r for _, _, _, rs in app.WORKSPACES for r in rs]
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertTrue(legacy.issubset(grouped))
        for route in sorted(legacy): self.go(route)
        self.assertEqual(set(self.calls), legacy)
        self.EngineRuntime.assert_called_once()

    def test_cache_and_execution_refresh_rules_invalidation_preserved(self):
        self.go('quant'); first = self.built['quant']
        self.go('macro'); self.go('quant')
        self.assertIs(first, self.built['quant']); self.assertEqual(self.calls['quant'], 1)
        self.go('trading'); self.go('macro'); self.go('trading')
        self.assertEqual(self.calls['trading'], 2)
        self.go('rules'); self.rules_changed(); self.go('trading')
        self.assertEqual(self.calls['trading'], 3)
        self.EngineRuntime.assert_called_once(); self.RuleStore.assert_called_once()

    def test_mobile_menu_and_resize_keep_running_view(self):
        self.go('quant'); first = self.built['quant']
        for width in (390, 420, 1440):
            self.page.width = width; self.page.on_resize(None)
            self.go('home'); self.go('quant')
        self.assertIs(first, self.built['quant'])
        self.assertEqual(self.calls['quant'], 1)

    def test_home_construction_has_no_io_or_jobs(self):
        # Home itself is display-only; no provider, status-file or store reads.
        with patch('builtins.open', side_effect=AssertionError('unexpected file read')), \
             patch('pathlib.Path.open', side_effect=AssertionError('unexpected Path read')):
            view = research_home.build_home_page(self.page, navigate=lambda _:None)
        texts = [c.value for c in walk(view) if isinstance(c, ft.Text)]
        self.assertIn('미연결', texts)
        self.assertTrue(any('중앙 90%' in t for t in texts))
        self.assertIn('0', texts)  # empty current session, not historical trial count

    def test_status_failure_visible_never_ready(self):
        with patch.object(research_home, 'recorded_status', return_value=(None, '자료 확인 실패')):
            view = research_home.build_system_page(self.page, navigate=lambda _:None)
        texts = [c.value for c in walk(view) if isinstance(c, ft.Text)]
        self.assertIn('확인 필요', texts); self.assertIn('자료 확인 실패', texts)
        self.assertNotIn('준비 완료', texts)


if __name__ == '__main__':
    unittest.main()
