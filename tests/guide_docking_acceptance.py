"""One preselected-dock regression with manual closes and real Workspace.

Small original app/interval helper bodies are isolated from full window/provider
modules. The offline Qt bootstrap supplies the process font/home/runtime policy.
No history loader, model, full application window or disk exporter is invoked.
"""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from tests import guide_lessons_acceptance as lesson_contracts


def _helpers(name,path,names,namespace):
    tree=ast.parse(path.read_bytes())
    nodes=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes}!=set(names):raise AssertionError('original UI helper contract missing')
    module=types.ModuleType(name);module.__package__=name.rpartition('.')[0];module.__dict__.update(namespace)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),module.__dict__)
    return module


@unittest.skipUnless(importlib.util.find_spec('PyQt6'), 'native Qt runtime required')
class GuideDockingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lesson_contracts.GuideLessonContracts.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        lesson_contracts.GuideLessonContracts.tearDownClass.__func__(cls)

    def test_preselected_dock_rebuilds_views_and_keeps_context(self):
        from datetime import date,timedelta
        from PyQt6 import sip
        from PyQt6.QtCore import QCoreApplication,QEvent,Qt
        from PyQt6.QtWidgets import QApplication,QFrame,QVBoxLayout
        from core.i18n import LocaleContext
        from core.education import catalog,indicators as I
        from quantgen_desktop.localization import UiLabel
        from quantgen_desktop.stock_detail_style import text
        from quantgen_desktop.page_kit import Workspace
        root=Path(__file__).resolve().parents[1]
        app=QApplication.instance() or QApplication(['guide-dock-contract','-platform','offscreen'])
        application=_helpers('quantgen_desktop.app',root/'quantgen_desktop/app.py',('label','panel'),
            {'UiLabel':UiLabel,'Qt':Qt,'QFrame':QFrame,'QVBoxLayout':QVBoxLayout})
        stock=_helpers('quantgen_desktop.stock_detail',root/'quantgen_desktop/stock_detail.py',('interval_words',),{'text':text})
        dates=tuple((date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(120))
        closes=tuple(10+i*.02+(i%9)*.04 for i in range(120))
        history=types.SimpleNamespace(symbol='SYNTHETIC_DOCK_TEST',dates=dates,closes=closes,source='FIXED_SYNTHETIC_UI_ONLY')
        with patch.dict(sys.modules,{'quantgen_desktop.app':application,'quantgen_desktop.stock_detail':stock}), \
             patch.object(catalog,'historical_case',side_effect=AssertionError('real case forbidden')), \
             patch.object(I,'historical_case',side_effect=AssertionError('real case forbidden')):
            from quantgen_desktop.indicator_guide import IndicatorGuide
            guide=IndicatorGuide(locale=LocaleContext('ko_KR'),history=history)
            try:
                self.assertFalse(guide.educational_lessons);self.assertIsNone(guide.lesson)
                guide.choose('ema');guide.move_cursor(42)
                before=(guide.keys,guide.focus,guide.series,dict(guide.meta),guide.cursor)
                previous=tuple(guide.chips.values())
                self.assertFalse(hasattr(previous[0],'bar'))
                workspace=Workspace(('Technical indicator guide','기술지표 가이드'))
                guide.dock_into(workspace)
                self.assertEqual((guide.keys,guide.focus,guide.series,dict(guide.meta),guide.cursor),before)
                self.assertTrue(guide.educational_lessons);self.assertEqual(guide.lesson.key,'ema')
                chip=guide.chips['ema']
                self.assertNotIn(chip,previous)
                self.assertIs(chip.parentWidget(),guide.chip_host)
                self.assertIs(chip.bar.parentWidget(),chip)
                self.assertIs(chip.values.parentWidget(),guide.chip_host)
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete.value)
                self.assertTrue(all(sip.isdeleted(old) for old in previous))
                self.assertFalse(sip.isdeleted(chip))
                # New callback widgets still edit the real selection once.
                chip.remove_button.click();self.assertEqual(guide.keys,())
                guide.options['ema'].click();self.assertEqual(guide.keys,('ema',))
                self.assertEqual(guide.focus,'ema');self.assertEqual(guide.cursor,42)
                self.assertEqual(guide.series.closes,closes)
                self.assertIsNotNone(guide.chips['ema'].values)
            finally:
                guide.close();guide.deleteLater()
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete.value)
                app.processEvents()


if __name__=='__main__':unittest.main()
