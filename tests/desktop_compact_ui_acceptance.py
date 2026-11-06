"""Actual Korean hint programs and compact controls preserve user operations."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from pathlib import Path
from unittest.mock import patch
from fontTools.ttLib import TTFont
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont,QRawFont
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from quantgen_desktop.app import ResearchWindow,load_interface_fonts,table,table_rows
from quantgen_desktop.font_policy import INTERFACE_FILES
from tests.qt_fixture_cleanup import delete_owned_widget
ROOT=Path(__file__).resolve().parents[1]
class CompactUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([]);load_interface_fonts(cls.app)
    def settle(self):
        for _ in range(8):self.app.processEvents()
    def test_each_real_weight_has_hinted_components_for_all_modern_hangul(self):
        for filename,weight in zip(INTERFACE_FILES,(400,500,600)):
            with TTFont(ROOT/'assets/fonts'/filename) as face:
                self.assertEqual(face['OS/2'].usWeightClass,weight)
                for tag in ('fpgm','prep','cvt ','gasp'):self.assertIn(tag,face)
                cmap=face.getBestCmap();glyf=face['glyf'];seen=set()
                def check(name):
                    if name in seen:return
                    seen.add(name);glyph=glyf[name]
                    if glyph.isComposite():
                        for c in glyph.components:check(c.glyphName)
                    else:self.assertGreater(len(glyph.program.getBytecode()),0,name)
                for code in range(0xAC00,0xD7A4):self.assertIn(code,cmap);check(cmap[code])
            font=QFont(self.app.font());font.setWeight(QFont.Weight(weight));raw=QRawFont.fromFont(font)
            self.assertEqual(raw.weight(),weight);self.assertTrue(raw.fontTable('fpgm'))
    def test_categories_and_forms_reflow_preserving_keyboard_and_request(self):
        with patch('quantgen_desktop.jobs.Jobs.start',side_effect=AssertionError('unexpected request')):
            w=ResearchWindow(auto_refresh=False,language='ko');self.addCleanup(delete_owned_widget,w)
            w.show();w.navigate('tools');self.settle()
            received=[];w.bonds.requested.connect(received.append)
            # Disconnect the application's runner; observe the exact form request only.
            w.bonds.requested.disconnect(w.run_bond)
            w.bonds.submit();before=received[-1]
            for language in ('ko','en'):
                w.set_language(language)
                for width in (1000,1360,1920):
                    w.resize(width,900);self.settle()
                    for button in w.tool_buttons.values():
                        self.assertTrue(button.parentWidget().rect().contains(button.geometry()))
                        self.assertLessEqual(button.width(),button.sizeHint().width()+2)
                    self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0)
                    self.assertLess(w.bonds.fields['Notional'].width(),300)
                    w.bonds.submit();self.assertEqual(received[-1],before)
                for name,button in w.tool_buttons.items():
                    button.setFocus();QTest.keyClick(button,Qt.Key.Key_Space);self.settle()
                    self.assertIs(w.tool_host.currentWidget(),getattr(w,name));self.assertTrue(button.isChecked())
                w.show_tool(w.bonds)
    def test_small_table_is_content_sized_and_full_values_remain(self):
        t=table(['Metric','Value']);self.addCleanup(delete_owned_widget,t)
        rows=[('Price','123,456.75'),('Duration','12.25')];table_rows(t,rows);t.resize(1600,300);t.show();self.settle()
        self.assertLess(t.width(),700)
        self.assertEqual([[t.item(r,c).text() for c in range(2)] for r in range(2)],[list(row) for row in rows])
        self.assertTrue(t.item(0,1).textAlignment() & Qt.AlignmentFlag.AlignRight)
        self.assertGreaterEqual(t.rowHeight(0),34)
if __name__=='__main__':unittest.main()
