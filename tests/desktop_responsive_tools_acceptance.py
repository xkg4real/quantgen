"""Selected-tool geometry stays readable after paint, locale and resize changes."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
import unittest
from unittest.mock import patch
from tests.desktop_acceptance import signals_fixture,structuring_fixture
from tests.desktop_macro_language_acceptance import output as macro_fixture
from core.research.signals_analysis import SignalsRequest
from core.research.structuring_analysis import StructuringRequest
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.chart_study import CurrentPageTabs
from quantgen_desktop.localization import UiLabel
from PyQt6.QtCore import QEvent,QPoint
from PyQt6.QtWidgets import QApplication,QWidget,QScrollArea
from PyQt6.QtTest import QTest


class ResponsiveToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        for name in ('requests.sessions.Session.request','core.quant.validate.load_cards','core.quant.gate_ledger.family_ledger'):
            p=patch(name,side_effect=AssertionError('external I/O forbidden'));p.start();self.addCleanup(p.stop)

    def settle(self):
        for _ in range(3):self.app.processEvents();QTest.qWait(5)

    def window(self):
        w=ResearchWindow(auto_refresh=False,language='en');w.resize(1440,1000);w.show()
        def cleanup():
            w.hide();w.deleteLater();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.addCleanup(cleanup)
        return w

    def test_inactive_oversize_page_does_not_set_selected_page_minimum(self):
        tabs=CurrentPageTabs();small=QWidget();large=QWidget();large.setMinimumSize(8000,9000)
        tabs.addTab(small,'Small');tabs.addTab(large,'Large');tabs.setCurrentWidget(small)
        self.assertLess(tabs.minimumSizeHint().width(),1000);self.assertLess(tabs.minimumSizeHint().height(),1000)
        tabs.setCurrentWidget(large);self.assertGreaterEqual(tabs.minimumSizeHint().width(),8000)
        tabs.setCurrentWidget(small);self.assertLess(tabs.minimumSizeHint().width(),1000)
        tabs.deleteLater()

    def test_signals_render_locale_narrow_wide_keeps_narrative_inside_viewport(self):
        w=self.window();pane=w.signals;out=signals_fixture(SignalsRequest(source='synthetic'))
        pane.show_result(out);pane.bind_output('signals',out);w.navigate('risk');w.risk_tabs.setCurrentWidget(pane)
        before=deepcopy(pane.report)
        with patch.object(w.jobs,'start',side_effect=AssertionError('no recompute')):
            for width in (1440,1000,1440,1000):
                w.resize(width,1000)
                for language in ('en','ko'):
                    w.set_language(language);self.settle();pane.grab();self.settle()
                    scroll=w.stack.currentWidget();self.assertIsInstance(scroll,QScrollArea)
                    self.assertEqual(scroll.horizontalScrollBar().maximum(),0)
                    narrative=next(x for x in pane.findChildren(UiLabel) if x.source_text==out.narrative)
                    x=narrative.mapTo(scroll.viewport(),QPoint(0,0)).x()
                    self.assertGreaterEqual(x,0);self.assertLessEqual(x+narrative.width(),scroll.viewport().width())
                    self.assertGreaterEqual(narrative.height()+2,narrative.heightForWidth(narrative.width()))
                    self.assertEqual(pane.report,before)

    def test_cleared_sibling_tools_do_not_expand_macro_input_labels(self):
        w=self.window()
        structured=structuring_fixture(StructuringRequest(source='synthetic',tool='steep',maturity='5y',cap=.03))
        pane=w.structuring;pane.show_result(structured);pane.bind_output('structuring',structured)
        w.navigate('markets');w.market_tabs.setCurrentWidget(pane);self.settle();pane.grab()
        pane.clear_result();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        macro=macro_fixture('weekly',short=True);pane=w.macro;pane.show_result(macro);pane.bind_output('macro',macro)
        w.market_tabs.setCurrentWidget(pane)
        for width in (1440,1000,1440):
            w.resize(width,1000)
            for language in ('en','ko'):
                w.set_language(language);self.settle();pane.grab();self.settle()
                self.assertLess(pane.input_box.height(),400)
                if pane.study.width()<pane.study.breakpoint:
                    last=max(widget.mapTo(pane.study,QPoint(0,widget.height())).y()
                             for widget in (pane.result_layout.itemAt(i).widget() for i in range(pane.result_layout.count()))
                             if widget is not None and not widget.isHidden())
                    reading_top=pane.result_reading.mapTo(pane.study,QPoint(0,0)).y()
                    self.assertLessEqual(reading_top-last,pane.study.split.spacing()+24)
                for label in pane.input_box.findChildren(UiLabel):
                    self.assertLessEqual(label.height(),max(50,label.heightForWidth(label.width())+10))
                self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0)


if __name__=='__main__':unittest.main()
