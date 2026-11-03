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
from PyQt6.QtCore import QEvent,QPoint,QSize
from PyQt6.QtWidgets import QApplication,QWidget,QScrollArea,QComboBox
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

    def overflow_context(self, window, pane, width, language):
        scroll=window.stack.currentWidget()
        tabs=window.market_tabs if pane is window.macro else window.risk_tabs
        def geometry(widget):
            hint=widget.minimumSizeHint()
            return f'{widget.width()}x{widget.height()} min={widget.minimumWidth()} hint={hint.width()}x{hint.height()}'
        return (f'width={width} actual_window={window.width()} language={language} '
                f'viewport={geometry(scroll.viewport())} content={geometry(scroll.widget())} '
                f'pane={geometry(pane)} input_box={geometry(pane.input_box)} '
                f'study={geometry(pane.study)} tabs={geometry(tabs)} '
                f'tabbar={geometry(tabs.tabBar())} tool={geometry(pane.tool)} source={geometry(pane.source)}')

    def test_inactive_oversize_page_does_not_set_selected_page_minimum(self):
        tabs=CurrentPageTabs();small=QWidget();large=QWidget();large.setMinimumSize(8000,9000)
        tabs.addTab(small,'Small');tabs.addTab(large,'Large');tabs.setCurrentWidget(small)
        self.assertLess(tabs.minimumSizeHint().width(),1000);self.assertLess(tabs.minimumSizeHint().height(),1000)
        tabs.setCurrentWidget(large);self.assertGreaterEqual(tabs.minimumSizeHint().width(),8000)
        tabs.setCurrentWidget(small);self.assertLess(tabs.minimumSizeHint().width(),1000)
        tabs.deleteLater()

    def test_height_for_width_uses_selected_page_and_keeps_explicit_minimum(self):
        class WrappingPage(QWidget):
            def __init__(self, height):
                super().__init__(); self.content_height=height
            def sizeHint(self): return QSize(200,self.content_height)
            def minimumSizeHint(self): return QSize(100,20)
            def hasHeightForWidth(self): return True
            def heightForWidth(self,width): return self.content_height
        tabs=CurrentPageTabs(); small=WrappingPage(50); large=WrappingPage(9000)
        tabs.addTab(small,'Small'); tabs.addTab(large,'Large')
        tabs.setCurrentWidget(small)
        self.assertTrue(tabs.hasHeightForWidth())
        self.assertLess(tabs.heightForWidth(700),200)
        small.setMinimumHeight(450)
        self.assertGreaterEqual(tabs.heightForWidth(700),450)
        self.assertLess(tabs.heightForWidth(700),600)
        tabs.setCurrentWidget(large)
        self.assertGreaterEqual(tabs.heightForWidth(700),9000)
        tabs.setCurrentWidget(small)
        self.assertLess(tabs.heightForWidth(700),600)
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
                    self.assertEqual(scroll.horizontalScrollBar().maximum(),0,
                                     self.overflow_context(w,pane,width,language))
                    narrative=next(x for x in pane.findChildren(UiLabel) if x.source_text==out.narrative)
                    x=narrative.mapTo(scroll.viewport(),QPoint(0,0)).x()
                    self.assertGreaterEqual(x,0);self.assertLessEqual(x+narrative.width(),scroll.viewport().width())
                    self.assertGreaterEqual(narrative.height()+2,narrative.heightForWidth(narrative.width()))
                    self.assertEqual(pane.report,before)

    def test_platform_wide_header_options_fit_without_losing_selection_or_text(self):
        original_hint=QComboBox.minimumSizeHint
        def platform_hint(combo):
            hint=original_hint(combo)
            width=combo.property('platform_intrinsic_width')
            if width and combo.sizeAdjustPolicy()!=QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon:
                return QSize(width,hint.height())
            return hint
        with patch.object(QComboBox,'minimumSizeHint',platform_hint):
            w=self.window(); pane=w.macro
            # Markets hide the source selector (UI-8), so the visible tool combo alone carries the
            # measured Windows-wide hint (251 + 459 px) that reproduces the overflow.
            self.assertTrue(pane.source.isHidden())
            pane.tool.setProperty('platform_intrinsic_width',251+459)
            pane.source.setProperty('platform_intrinsic_width',459)
            pane.tool.setCurrentIndex(pane.tool.findData('weekly'))
            pane.source.setCurrentIndex(pane.source.findData('fred'))
            w.navigate('markets');w.show_market_pane(pane);w.resize(1000,1000)
            choices=[[combo.itemData(i) for i in range(combo.count())] for combo in (pane.tool,pane.source)]
            policies=[combo.sizeAdjustPolicy() for combo in (pane.tool,pane.source)]
            request=pane.make_request()
            # The measured Windows content-driven hints must reproduce overflow.
            for combo in (pane.tool,pane.source):
                combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                combo.updateGeometry()
            self.settle()
            self.assertGreater(w.stack.currentWidget().horizontalScrollBar().maximum(),0)
            for combo,policy in zip((pane.tool,pane.source),policies):
                combo.setSizeAdjustPolicy(policy)
                combo.updateGeometry()
            with patch.object(w.jobs,'start',side_effect=AssertionError('no recompute')):
                for language in ('en','ko','en'):
                    w.set_language(language);self.settle();pane.grab();self.settle()
                    self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0,
                                     self.overflow_context(w,pane,1000,language))
                    self.assertEqual(pane.make_request(),request)
                    for combo,items in zip((pane.tool,pane.source),choices):
                        self.assertEqual([combo.itemData(i) for i in range(combo.count())],items)
                        self.assertEqual(combo.toolTip(),combo.currentText())
                        self.assertTrue(combo.accessibleName())

    def test_cleared_sibling_tools_do_not_expand_macro_input_labels(self):
        w=self.window()
        structured=structuring_fixture(StructuringRequest(source='synthetic',tool='steep',maturity='5y',cap=.03))
        pane=w.structuring;pane.show_result(structured);pane.bind_output('structuring',structured)
        w.navigate('markets');w.show_market_pane(pane);self.settle();pane.grab()
        pane.clear_result();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        macro=macro_fixture('weekly',short=True);pane=w.macro;pane.show_result(macro);pane.bind_output('macro',macro)
        w.show_market_pane(pane)
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
                    if label.isHidden():continue  # Markets hide the source caption (UI-8); hidden widgets keep Qt's default size
                    self.assertLessEqual(label.height(),max(50,label.heightForWidth(label.width())+10))
                self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0,
                                 self.overflow_context(w,pane,width,language))


if __name__=='__main__':unittest.main()
