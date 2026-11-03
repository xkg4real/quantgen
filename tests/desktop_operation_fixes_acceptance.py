"""Owner A2 operation fixes (2026-11-03): wheel guard, bond digit grouping, form clipping, icon.

Offline Qt fixtures; no provider, AI or network calls.
"""
import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow, app_icon
    from quantgen_desktop.bonds import group_digits
    from quantgen_desktop.wheel_guard import guard
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QAbstractSpinBox, QApplication, QComboBox, QScrollArea, QSpinBox, QWidget


def wheel(app, widget, delta=-120, horizontal=False):
    angle = QPoint(delta, 0) if horizontal else QPoint(0, delta)
    event = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), angle, Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
    app.sendEvent(widget, event)


def settle(app, passes=12):
    """Let nested layouts finish. Each nesting level reacts to a size change in its own
    posted LayoutRequest, so one processEvents() can observe a form mid-propagation
    (seen on Windows CI as a one-pass-old ETF height). Twelve passes exceed the depth."""
    for _ in range(passes):
        app.processEvents()


class OperationFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)
        self.provider = Mock(side_effect=AssertionError('Provider forbidden'))
        self.window = ResearchWindow(auto_refresh=False, locale='ko_KR', market_loader=self.provider,
                                     connections_runner=self.provider)
        self.window.resize(1000, 700); self.window.show(); self.window.navigate('markets'); self.app.processEvents()
        self.addCleanup(self.window.deleteLater); self.addCleanup(self.window.hide)

    def test_unfocused_selectors_ignore_the_wheel_and_the_page_scrolls(self):
        w = self.window
        w.show_market_pane(w.rates); self.app.processEvents()
        scroll = w.stack.currentWidget().verticalScrollBar()
        tool, tabs = w.rates.tool, w.market_tabs
        before = (tool.currentIndex(), tabs.currentIndex(), w.theme.currentIndex())
        scroll.setValue(0)
        wheel(self.app, tool); wheel(self.app, tabs.tabBar()); wheel(self.app, w.theme)
        self.assertEqual((tool.currentIndex(), tabs.currentIndex(), w.theme.currentIndex()), before)
        self.assertGreater(scroll.value(), 0)  # the wheel moved the page instead
        tool.setFocus(); self.app.processEvents()
        wheel(self.app, tool)
        self.assertNotEqual(tool.currentIndex(), before[0])  # a focused selector still responds

    def test_real_wheel_cannot_focus_a_selector(self):
        """Qt focuses a control on a real wheel event when its policy includes WheelFocus.

        Synthetic events skip that step, so the policy itself is the check.
        """
        w = self.window
        selectors = [c for c in w.findChildren((QComboBox, QAbstractSpinBox))]
        self.assertTrue(selectors)
        wheel_focus = Qt.FocusPolicy.WheelFocus.value
        loose = [c.accessibleName() or type(c).__name__ for c in selectors
                 if c.focusPolicy().value & wheel_focus == wheel_focus]
        self.assertEqual(loose, [])
        # Widgets created after the window are covered by the next translation pass.
        late = QComboBox(w.rates); late.addItems(['a', 'b'])
        self.app.processEvents(); self.app.processEvents()
        self.assertEqual(late.focusPolicy(), Qt.FocusPolicy.StrongFocus)
        self.assertTrue(late.property('qg_wheel_guard'))

    def test_wheel_goes_to_a_scroll_bar_that_can_move(self):
        outer = QScrollArea(); outer.resize(300, 200)
        page = QWidget(); page.setMinimumSize(280, 800)
        inner = QScrollArea(page); inner.setGeometry(0, 0, 200, 100)
        content = QWidget(); content.setMinimumSize(180, 400); inner.setWidget(content)
        combo = QComboBox(content); combo.addItems(['a', 'b', 'c'])
        spin = QSpinBox(content); spin.setRange(0, 10); spin.move(0, 40)
        outer.setWidget(page); outer.show(); self.app.processEvents()
        self.addCleanup(outer.deleteLater)
        for control in (combo, spin):
            guard(control)
        inner_bar, outer_bar = inner.verticalScrollBar(), outer.verticalScrollBar()
        inner_bar.setValue(inner_bar.maximum())  # the inner area cannot scroll further down
        wheel(self.app, combo)
        self.assertEqual((combo.currentIndex(), inner_bar.value()), (0, inner_bar.maximum()))
        self.assertGreater(outer_bar.value(), 0)  # the next area that can move takes the wheel
        wheel(self.app, spin, delta=120)
        self.assertEqual(spin.value(), 0)
        self.assertLess(inner_bar.value(), inner_bar.maximum())  # scrolling up, the inner area can move
        # Nothing can move: the wheel is swallowed instead of changing the selector.
        inner_bar.setValue(0); outer_bar.setValue(0)
        wheel(self.app, combo, delta=120)
        self.assertEqual((combo.currentIndex(), inner_bar.value(), outer_bar.value()), (0, 0, 0))
        # A sideways wheel moves a horizontal bar, never the vertical one.
        content.setMinimumSize(600, 400); self.app.processEvents()
        wheel(self.app, combo, delta=-120, horizontal=True)
        self.assertGreater(inner.horizontalScrollBar().value(), 0)
        self.assertEqual(inner_bar.value(), 0)
        # Spin boxes keep focus inside; a focused one still changes by wheel.
        spin.setFocus(); self.app.processEvents()
        self.assertTrue(spin.hasFocus())
        wheel(self.app, spin, delta=120)
        self.assertEqual(spin.value(), 1)

    def test_bond_amounts_show_thousands_separators_and_still_parse(self):
        self.assertEqual(group_digits('1000000'), '1,000,000')
        self.assertEqual(group_digits('-1234567.25'), '-1,234,567.25')
        self.assertEqual(group_digits('abc'), 'abc'); self.assertEqual(group_digits(''), '')
        for typed in ('²', '1²', '1.5²', '2030-01-01', '1e6', '.5', '-'):
            self.assertEqual(group_digits(typed), typed)  # never raises; non-plain numbers stay as typed
        field = self.window.bonds.fields['Notional']
        self.assertEqual(field.text(), '1,000,000')
        field.setText('2500000'); field.editingFinished.emit()
        self.assertEqual(field.text(), '2,500,000')
        requests = []
        self.window.bonds.requested.connect(requests.append)
        self.window.bonds.submit()
        self.assertEqual(requests[0].notional, 2_500_000)

    def test_tool_forms_are_not_clipped_after_styles_apply(self):
        w = self.window

        def fits(pane):
            page = pane.forms.currentWidget()
            bottom = max(c.geometry().bottom() for c in page.findChildren(QWidget)
                         if c.parent() is page and not c.isHidden())
            return bottom < pane.forms.height()
        for width in (1000, 1360):
            w.resize(width, 900)
            for pane in (w.rates, w.krx, w.fx, w.etf, w.derivatives, w.crypto):
                w.show_market_pane(pane); settle(self.app)
                self.assertTrue(fits(pane), (type(pane).__name__, width))
        w.show_market_pane(w.rates); settle(self.app)
        w.rates.tool.setCurrentIndex(1); settle(self.app)
        self.assertTrue(fits(w.rates))  # a taller form after switching tools is laid out in full
        # Wider glyphs (Windows fonts) wrap captions to more lines; the form must grow to match.
        from PyQt6.QtWidgets import QLabel
        w.resize(1000, 900); w.show_market_pane(w.fx); settle(self.app)
        before = w.fx.forms.height()  # FX form at width 1000 with its own captions
        w.resize(800, 900); settle(self.app)
        page = w.fx.forms.currentWidget()
        for caption in page.findChildren(QLabel):
            if caption.parent() is page:  # long enough to wrap to more lines in any font
                caption.setText(caption.text() + ' 긴설명' * 12)
        for width in (1000, 1360, 800, 1000):
            w.resize(width, 900); settle(self.app)
            self.assertTrue(fits(w.fx), width)
        self.assertGreater(w.fx.forms.height(), before)  # the wrapped captions really took more room

    def test_window_and_app_icons_carry_taskbar_sizes(self):
        icon = app_icon()
        sizes = {size.width() for size in icon.availableSizes()}
        self.assertTrue({16, 32, 48, 256} <= sizes, sizes)
        self.assertFalse(self.window.windowIcon().isNull())


if __name__ == '__main__':
    unittest.main()
