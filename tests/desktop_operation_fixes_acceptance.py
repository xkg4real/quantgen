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
from PyQt6.QtWidgets import QAbstractSpinBox, QApplication, QComboBox, QLabel, QScrollArea, QSpinBox, QWidget


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


def layout_report(pane):
    """The numbers needed to diagnose a clipped form on a platform we cannot run locally."""
    from PyQt6.QtGui import QFontInfo
    from PyQt6.QtWidgets import QAbstractScrollArea

    def size(widget):
        width = widget.width()
        hfw = widget.heightForWidth(width) if widget.hasHeightForWidth() else '-'
        return (f"{type(widget).__name__} {width}x{widget.height()} hint={widget.sizeHint().height()} "
                f"min={widget.minimumSizeHint().height()} minH={widget.minimumHeight()} hfw={hfw} "
                f"pol={widget.sizePolicy().verticalPolicy().name}")
    app = QApplication.instance()
    page = pane.forms.currentWidget()
    lines = [f"style={app.style().name()} app_font={QFontInfo(app.font()).family()} {app.font().pointSizeF()}pt "
             f"dpr={pane.devicePixelRatioF()}"]
    for child in page.findChildren(QWidget):
        if child.parent() is page and not child.isHidden():
            text = child.text()[:14] if hasattr(child, 'text') and callable(child.text) else ''
            info = QFontInfo(child.font())
            lines.append(f"  {type(child).__name__} {text!r} geo={child.geometry().getRect()} "
                         f"hint={child.sizeHint().height()} font={info.family()} {info.pixelSize()}px "
                         f"hfw={child.heightForWidth(child.width()) if child.hasHeightForWidth() else '-'}")
    widget = page
    while widget is not None:
        lines.append('  ' + size(widget))
        if isinstance(widget, QAbstractScrollArea):
            bar = widget.verticalScrollBar()
            lines.append(f"  scrollbar visible={bar.isVisible()} max={bar.maximum()}")
            break
        widget = widget.parentWidget()
    return '\n'.join(lines)


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
        # Markets (owner, 2026-11-04): the watchlist cards make the page taller than the window.
        w.navigate('markets'); settle(self.app)
        scroll = w.stack.currentWidget().verticalScrollBar()
        self.assertGreater(scroll.maximum(), 0)
        kind = w.markets_view.kind
        before = (kind.currentIndex(), w.theme.currentIndex())
        scroll.setValue(0)
        wheel(self.app, kind); wheel(self.app, w.theme)
        self.assertEqual((kind.currentIndex(), w.theme.currentIndex()), before)
        self.assertGreater(scroll.value(), 0)  # the wheel moved the page instead
        # The analysis tools are buttons on their own page (no tab bar to scroll); a tool's selector
        # and the tool buttons ignore the wheel too.
        w.show_market_pane(w.rates); settle(self.app)
        tool = w.rates.tool
        start = tool.currentIndex()
        wheel(self.app, tool); wheel(self.app, w.tool_buttons['bonds'])
        self.assertEqual((tool.currentIndex(), w.current_market_pane()), (start, w.rates))
        tool.setFocus(); self.app.processEvents()
        wheel(self.app, tool)
        self.assertNotEqual(tool.currentIndex(), start)  # a focused selector still responds

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
            box = pane.input_box  # nothing in the input panel is squeezed below its wrapped height
            return bottom < pane.forms.height() and box.height() >= box.heightForWidth(box.width())
        for width in (1000, 1360):
            w.resize(width, 900)
            for pane in (w.rates, w.krx, w.fx, w.etf, w.derivatives, w.crypto):
                w.show_market_pane(pane); settle(self.app)
                self.assertTrue(fits(pane), f"{type(pane).__name__} at {width}\n{layout_report(pane)}")
        w.show_market_pane(w.rates); settle(self.app)
        w.rates.tool.setCurrentIndex(1); settle(self.app)
        self.assertTrue(fits(w.rates), layout_report(w.rates))  # a taller form after switching tools is laid out in full
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
            self.assertTrue(fits(w.fx), f"{width}\n{layout_report(w.fx)}")
        self.assertGreater(w.fx.forms.height(), before)  # the wrapped captions really took more room

    def test_form_panel_is_not_capped_at_a_wider_preferred_width(self):
        """Windows CI: the ETF panel's size hint, taken at a wider preferred width, was 383 px while its
        wrapped content needed 411 px at the real width, and a Maximum height policy cut it to 383.
        A child that prefers a wide layout, plus a long wrapping line, recreates that on any platform:
        the panel's own captions alone may not wrap at the real width with a platform's fonts
        (Ubuntu CI, 2026-11-04: 388 == 388 once the left menu was narrowed)."""
        from PyQt6.QtCore import QSize

        class WideHint(QWidget):
            def sizeHint(self): return QSize(1600, 8)
            def minimumSizeHint(self): return QSize(10, 8)
        w = self.window
        w.resize(1000, 900); w.show_market_pane(w.etf); settle(self.app)
        grid = w.etf.forms.currentWidget().layout()
        grid.addWidget(WideHint(), grid.rowCount(), 0, 1, 3)
        wrapping = QLabel("wrap " * 120); wrapping.setWordWrap(True)  # ASCII: every platform font has it
        grid.addWidget(wrapping, grid.rowCount(), 0, 1, 3); settle(self.app)
        box = w.etf.input_box
        self.assertLess(box.sizeHint().height(), box.heightForWidth(box.width()))  # the Windows condition holds
        self.assertGreaterEqual(box.height(), box.heightForWidth(box.width()), layout_report(w.etf))

    def test_window_and_app_icons_carry_taskbar_sizes(self):
        icon = app_icon()
        sizes = {size.width() for size in icon.availableSizes()}
        self.assertTrue({16, 32, 48, 256} <= sizes, sizes)
        self.assertFalse(self.window.windowIcon().isNull())


if __name__ == '__main__':
    unittest.main()
