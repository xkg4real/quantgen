"""The native font and type (owner UI-D6) and compact controls preserve user operations."""
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
    def test_interface_face_has_real_weights_and_all_modern_hangul(self):
        """Owner UI-D6 (2026-11-11, second font mockup round, N3): text and figures in QG Interface, the
        Pretendard-derived CFF OTF, with real 400/500/600 faces and all 11,172 modern Hangul syllables.
        Plan A (IBM Plex Sans KR) was dropped; the Gothic A1 TTFs stay unused, for rollback only."""
        from quantgen_desktop.font_policy import INTERFACE_FAMILY, NUMBER_FAMILY, number_font
        self.assertEqual((INTERFACE_FAMILY, NUMBER_FAMILY), ('QG Interface', 'QG Interface'))
        for filename, weight in zip(INTERFACE_FILES, (400, 500, 600)):
            self.assertTrue(filename.endswith('.otf'), filename)
            with TTFont(ROOT/'assets/fonts'/filename) as face:
                self.assertEqual(face['OS/2'].usWeightClass, weight)
                self.assertIn('CFF ', face)
                cmap = face.getBestCmap()
                for code in range(0xAC00, 0xD7A4): self.assertIn(code, cmap)
        for weight in (400, 500, 600):
            font = QFont(self.app.font()); font.setWeight(QFont.Weight(weight))
            raw = QRawFont.fromFont(font)
            self.assertEqual(raw.familyName(), INTERFACE_FAMILY); self.assertEqual(raw.weight(), weight)
            self.assertTrue(raw.fontTable('CFF '))
            self.assertEqual(QRawFont.fromFont(number_font(font)).familyName(), NUMBER_FAMILY)
        self.assertFalse(list((ROOT/'assets/fonts').glob('IBMPlexSansKR-*')))
        for kept in ('qg-interface.ttf', 'qg-interface-medium.ttf', 'qg-interface-semibold.ttf'):
            self.assertTrue((ROOT/'assets/fonts'/kept).is_file(), kept)
            self.assertNotIn(kept, INTERFACE_FILES)

    def test_type_follows_owner_plan_n3(self):
        """UI-D6: section headings and card titles 500, captions 400, buttons/menu 400 (selected menu and
        tool 600), primary button 500, table headers 500; tighter tracking, figures at their own tracking."""
        from quantgen_desktop.typography import window_stylesheet
        from core.theme import LIGHT
        css = window_stylesheet(LIGHT, False)
        n3 = css[css.index('Owner UI-D6'):]
        for rule in ("QLabel[role='heading'], QLabel#watchlistTitle {{ font-weight: 500; letter-spacing: -0.36px; }}",
                     "QLabel[role='caption'] {{ font-weight: 400; }}", "QHeaderView::section {{ font-weight: 500; }}",
                     "QPushButton[nav='true']:checked, QPushButton[tool='true']:checked {{ font-weight: 600; }}",
                     "QLabel[role='price'], QLabel[role='delta'], QFrame#panel QLabel[role='delta'] {{ letter-spacing: 0px; }}"):
            self.assertIn(rule.replace('{{', '{').replace('}}', '}'), n3)
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
    def test_compact_form_keeps_224px_base_and_widens_only_for_native_minima(self):
        # Owner PR89: 3 columns at a 224px base, reflow only when narrow. The base is not a
        # ceiling: real control minima above it (larger fonts, Windows metrics) widen the cap
        # just enough for every column, so a wide window never drops a column (A3 rule).
        from PyQt6.QtWidgets import QFrame,QLabel,QLineEdit,QVBoxLayout,QWidget
        from quantgen_desktop.form_layout import CompactFieldGrid,bound_input_panel
        host=QWidget();self.addCleanup(delete_owned_widget,host)
        outer=QVBoxLayout(host);outer.setContentsMargins(0,0,0,0)
        box=QFrame();inner=QVBoxLayout(box);inner.setContentsMargins(16,16,16,16);bound_input_panel(box)
        fields=[(QLabel(f'Field {index}'),QLineEdit(str(index))) for index in range(9)]
        form=CompactFieldGrid(fields);inner.addWidget(form);outer.addWidget(box)
        host.resize(1600,900);host.show();self.settle()
        for minimum,width,columns,cap in ((200,1600,3,696),(236,1600,3,732),(236,600,2,732),(200,1600,3,696)):
            for _,control in fields:control.setMinimumWidth(minimum)
            host.resize(width,900);self.settle()
            self.assertEqual((form.maximumWidth(),box.maximumWidth(),form.columns),(cap,cap+34,columns))
            self.assertLessEqual(form.width(),cap)
            for index,(caption,control) in enumerate(fields):
                row,column=(index//columns)*2,index%columns
                self.assertIs(form.grid.itemAtPosition(row,column).widget(),caption)
                self.assertIs(form.grid.itemAtPosition(row+1,column).widget(),control)
                self.assertGreaterEqual(control.width(),minimum)
                self.assertLessEqual(control.x()+control.width(),form.width())
                self.assertEqual(control.text(),str(index))
    def test_small_table_is_content_sized_and_full_values_remain(self):
        t=table(['Metric','Value']);self.addCleanup(delete_owned_widget,t)
        rows=[('Price','123,456.75'),('Duration','12.25')];table_rows(t,rows);t.resize(1600,300);t.show();self.settle()
        self.assertLess(t.width(),700)
        self.assertEqual([[t.item(r,c).text() for c in range(2)] for r in range(2)],[list(row) for row in rows])
        self.assertTrue(t.item(0,1).textAlignment() & Qt.AlignmentFlag.AlignRight)
        self.assertGreaterEqual(t.rowHeight(0),34)
if __name__=='__main__':unittest.main()
