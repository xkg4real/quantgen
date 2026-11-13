"""Purpose, keyboard access and actual text faces for the research workspaces."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import re
import unittest
from unittest.mock import patch
from PyQt6.QtGui import QRawFont
from PyQt6.QtWidgets import QApplication
from quantgen_desktop.app import ResearchWindow
from tests.qt_fixture_cleanup import delete_owned_widget


class WorkflowGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        deny=patch('quantgen_desktop.jobs.Jobs.start',side_effect=AssertionError('Display must not run a job'))
        deny.start();self.addCleanup(deny.stop)
        self.window=ResearchWindow(auto_refresh=False,language='ko')
        self.addCleanup(delete_owned_widget,self.window)
        self.window.resize(1000,800);self.window.show();self.settle()

    def settle(self):
        for _ in range(8):self.app.processEvents()

    def test_tool_purpose_changes_without_changing_input_or_starting_calculation(self):
        w=self.window;w.navigate('tools');w.bonds.fields['Notional'].setText('2,345,678')
        for key,button in w.tool_buttons.items():
            button.click();self.settle()
            self.assertEqual(w.tools_guide.key,key)
            self.assertTrue(w.tools_guide.purpose.text())
            self.assertEqual(len(w.tools_guide.steps),3)
            self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0)
        self.assertEqual(w.bonds.fields['Notional'].text(),'2,345,678')

    def test_tabs_and_locale_change_the_guide_and_accessible_name(self):
        w=self.window
        for route,tabs,guide,keys in (
                ('quant',w.quant_tabs,w.quant_guide,('monte_carlo','strategy')),
                ('risk',w.risk_tabs,w.risk_guide,('portfolio','signals','paper'))):
            w.navigate(route)
            for i,key in enumerate(keys):
                tabs.setCurrentIndex(i);self.settle();self.assertEqual(guide.key,key)
            w.set_language('en');self.settle()
            self.assertFalse(re.search('[가-힣]',guide.purpose.text()+guide.scope.text()))
            self.assertEqual(guide.accessibleName(),guide.purpose.text())
            self.assertEqual(guide.accessibleDescription(),guide.scope.text())
            w.set_language('ko');self.settle()

    def test_empty_bond_and_simulation_charts_do_not_occupy_the_initial_page(self):
        w=self.window;w.navigate('tools');self.settle()
        self.assertTrue(w.bonds.empty.isVisible());self.assertTrue(w.bonds.result_host.isHidden())
        w.navigate('quant');self.settle()
        self.assertTrue(w.quant_empty.isVisible())
        self.assertTrue(w.quant_study.isHidden());self.assertTrue(w.quant_metrics.isHidden())

    def test_first_visit_shows_heading_and_return_keeps_reading_position(self):
        w=self.window;w.navigate('guide');self.settle()
        scroll=w.stack.currentWidget().verticalScrollBar()
        self.assertEqual(scroll.value(),0)
        self.assertGreater(scroll.maximum(),100)
        scroll.setValue(100)
        w.navigate('tools');self.settle()
        w.navigate('guide');self.settle()
        self.assertEqual(scroll.value(),100)

    def test_styled_headings_captions_and_inputs_resolve_to_real_text_font(self):
        w=self.window;w.navigate('tools');self.settle()
        title=w.stack.currentWidget().widget().layout().itemAt(0).widget()
        widgets=(title,w.tools_guide.purpose,w.tools_guide.scope,w.bonds.fields['Notional'])
        for mode in (0,1):
            w.change_theme(mode);self.settle()
            for widget in widgets:
                raw=QRawFont.fromFont(widget.font())
                self.assertEqual(raw.familyName(),'QG Interface')
                self.assertTrue(all(raw.glyphIndexesForString('QUANTGEN 123 한글')))


if __name__=='__main__':unittest.main()
