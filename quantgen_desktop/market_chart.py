"""Native KIS chart workspace; all data and chart calculations are shared with Flet."""
from __future__ import annotations

import math
from datetime import datetime, timezone

from PyQt6.QtCore import QByteArray, QEvent, QObject, QTimer, Qt, QSize, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market.models import ChartRequest, Instrument, INTERVALS
from .jobs import Jobs


_ASSETS = (
    ("domestic_stock", "국내주식 / ETF", "Korean stock / ETF", "005930"),
    ("overseas_stock", "해외주식", "Overseas stock", "AAPL"),
    ("domestic_future", "국내선물옵션", "Korean futures / options", "101W12"),
    ("overseas_future", "해외선물", "Overseas futures", "ESZ26"),
    ("bond", "장내채권", "Exchange-traded bond", "KR103502GC66"),
)
_EXCHANGES = ("NAS", "NYS", "AMS", "HKS", "TSE", "SHS", "SZS", "HSX", "HNX")
# Owner 2026-11-11 (R-D9-2): plain time words, never '봉' ("몇분, 일, 주 월, 년"); 1Y is built from the monthly history.
_INTERVAL_NAMES = {"1m": "1분", "3m": "3분", "5m": "5분", "15m": "15분", "30m": "30분",
                   "60m": "60분", "1d": "일", "1w": "주", "1M": "월", "1Y": "년",
                   "1tick": "1틱", "10tick": "10틱", "100tick": "100틱",
                   "1s": "1초", "5s": "5초", "10s": "10초", "30s": "30초"}


class _StreamBridge(QObject):
    tick = pyqtSignal(int, object)
    status = pyqtSignal(int, str)
    history = pyqtSignal(int, object, object)


class MarketChartSvg(QSvgWidget):
    """The same SVG as the web view with native keyboard and pointer selection.

    Detail mode (the stock screen, owner 2026-11-11): the chart is drawn by core.market.detail_svg at exactly the
    widget's size, the plain wheel does nothing over it ("스크롤로 차트좌우이동 ... 그냥 막아버리고"), Ctrl + wheel
    (and a trackpad pinch) zooms on the bar under the pointer (`zoom_handler`, owner R-D12-1 "차트 확대를 +-로 하지말고
    컨트롤 + 마우스 휠 이렇게 하자"), a left-button drag on the plot pans it (`drag_handler`, owner R-D12-2 "차트 화면
    좌클릭해서 좌우로 끌면 좌우도 움직일수잇게"), and the arrow keys pan (`key_handler`, the pane). Outside detail mode it keeps
    the document-height chart_svg drawing.
    """
    cursor_changed = pyqtSignal(int)
    layout_changed = pyqtSignal(object)   # detail_svg.ChartLayout after each detail redraw (None when empty)
    wheel_ignored = pyqtSignal()          # detail: a plain wheel turn that changed nothing (the screen names the keys)
    WHEEL_NOTCH = 120                     # one wheel notch (QWheelEvent.angleDelta) = one zoom step
    PINCH_STEP = 0.2                      # pinch scale change worth one zoom step

    def __init__(self, parent=None):
        super().__init__(parent)
        self.snapshot = None
        self.cursor = 0
        self.visible_bars = 120
        self.end = None          # last bar index shown; None follows the latest bar
        self.indicators = ("sma",)
        self.dark = False
        self.language = "en"
        self.detail = False
        self.supply = None
        self.theme = None        # detail: palette colours (bg, text, muted, border)
        self.months = None       # detail: month names in the window language
        self.layout_info = None
        self.zoom_handler = None   # detail: handler(steps, x) zooms keeping the bar at chart x in place
        self.drag_handler = None   # detail: handler(start, x) shows the window from bar `start` (left-drag pan)
        self._wheel_rest = 0       # Ctrl+wheel delta short of a notch (high-resolution wheels, trackpads)
        self._pinch_rest = 0.0
        self._press = None         # detail: where a left press on the plot went down (the drag distance counts from it)
        self._grab = None          # detail: (pointer x, window start, bar width, plot left) the held press pans from
        self._grab_layout = None   # detail: the window (`_layout_key`) the held press last left the chart at
        self._pointer_x = None     # detail: chart x of the pointer while the press is held
        self._hover_x = None       # detail: chart x of the pointer over the chart or its overlays (None: elsewhere)
        self._dragging = False     # the press has moved the platform drag distance: it pans until release
        self.setMinimumWidth(260)
        self.setMinimumHeight(300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._propagate_chart_height)

    def set_detail(self, on):
        """Fill the space the layout gives (no fixed height); the plain wheel never moves the chart (Ctrl + wheel zooms,
        a left-drag pans)."""
        self.detail = bool(on)
        # Hover moves reach the chart over its overlay labels too (Qt drops plain moves over a child that does not
        # track the mouse), so the pointer shape there follows the plot under them (owner R-D12-2).
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, self.detail)
        if self.detail:
            self.setMinimumHeight(220)
            self.setMaximumHeight(16777215)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            self._release_drag()
            self._hover_x = None
            self.unsetCursor()
        self.redraw()

    def set_snapshot(self, snapshot, cursor=0, *, visible_bars=120, indicators=None, dark=False, language="en",
                     end=None, supply=None):
        self.snapshot, self.cursor = snapshot, cursor
        self.visible_bars, self.dark = visible_bars, dark
        self.language = language
        self.end, self.supply = end, supply
        if indicators is not None:
            self.indicators = tuple(indicators)
        self.redraw()

    def window(self):
        """(start, stop) of the bars drawn."""
        from core.market.detail_model import window
        n = len(self.snapshot.candles) if self.snapshot else 0
        return window(n, min(n, self.visible_bars) if n else 1, self.end)

    def redraw(self):
        if self.snapshot is None:
            self.load(QByteArray())
            if self.detail:
                self.layout_info = None
                self.layout_changed.emit(None)
                self._sync_pointer()
            return
        if self.detail:
            from core.market.detail_svg import EN_MONTHS, render
            svg, layout = render(self.snapshot, studies=self.indicators, cursor=self.cursor, end=self.end,
                                 visible=self.visible_bars, width=max(240, self.width()), height=max(200, self.height()),
                                 dark=self.dark, theme=self.theme, months=self.months or EN_MONTHS, supply=self.supply)
            self.load(QByteArray(svg.encode("utf-8")))
            self.layout_info = layout
            self.layout_changed.emit(layout)
            self._sync_pointer()
            return
        from core.market.presentation import chart_svg
        svg = chart_svg(self.snapshot, indicators=self.indicators, cursor=self.cursor,
                        width=max(320, self.width()), dark=self.dark, visible=self.visible_bars, language=self.language,
                        end=self.end)
        self.load(QByteArray(svg.encode("utf-8")))
        height = self.renderer().viewBoxF().height()
        if height > 0 and self.minimumHeight() != round(height):
            self.setFixedHeight(round(height))
            # A redraw can occur inside a resize/layout pass. Defer invalidation
            # until that pass finishes, otherwise the tab's cached old height
            # lets RSI/MACD overlap the slider and textual readouts below it.
            self._geometry_timer.start(0)

    def _propagate_chart_height(self):
        parent = self.parentWidget()
        while parent is not None:
            if parent.layout() is not None:
                parent.layout().invalidate()
            parent.updateGeometry()
            if parent.inherits("QAbstractScrollArea"):
                break
            parent = parent.parentWidget()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.redraw()

    def _on_plot(self, x):
        """Detail mode: chart x lies over the drawn bars (where a drag grabs the chart)."""
        layout = self.layout_info
        return bool(self.detail and self.snapshot and self.snapshot.candles and layout is not None
                    and layout.stop > layout.start and layout.plot_left <= x < layout.plot_right)

    def _pannable(self):
        """Detail mode: fewer bars are shown than were loaded, so a drag can move the window."""
        layout = self.layout_info
        return bool(self.detail and self.snapshot and layout is not None
                    and 0 < layout.stop - layout.start < len(self.snapshot.candles))

    def _layout_key(self):
        """The drawn window and bar geometry a held press pans from (None when nothing is drawn)."""
        layout = self.layout_info
        return None if layout is None else (layout.start, layout.stop, layout.step, layout.plot_left)

    def pointer_shape(self):
        """The mouse pointer's shape over the chart (`self.cursor` is the selected bar, not QWidget.cursor())."""
        return QWidget.cursor(self).shape()

    def _set_pointer(self, shape):
        """Show `shape` over the chart and the overlays that take its pointer (None: the usual arrow)."""
        if shape is None:
            if self.testAttribute(Qt.WidgetAttribute.WA_SetCursor):
                self.unsetCursor()
        elif self.pointer_shape() != shape:
            self.setCursor(shape)

    def _hover_cursor(self, x):
        """Owner R-D12/A1: an open hand everywhere over the detail chart, including its axes and full history."""
        self._set_pointer(Qt.CursorShape.OpenHandCursor if self.detail and 0 <= x <= self.width() else None)

    def _sync_pointer(self):
        """After a redraw (a zoom, a reload, a new live bar) the pointer shape says whether a drag can move the
        window now, without waiting for the next mouse move."""
        if not self.detail:
            return
        if self._press is not None:
            if self._dragging:
                self._set_pointer(Qt.CursorShape.ClosedHandCursor)
        elif self._hover_x is not None:
            self._hover_cursor(self._hover_x)

    def _release_drag(self):
        self._press, self._grab, self._grab_layout, self._pointer_x = None, None, None, None
        self._dragging = False

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self._press is not None:
            if self.detail and event.buttons() & Qt.MouseButton.LeftButton:
                self._drag_move(event)
                event.accept()
                return
            self._release_drag()     # the release went elsewhere (a popup, the window lost the mouse)
        if self.detail:
            self._hover_x = x
            self._hover_cursor(x)
        if self.snapshot and self.snapshot.candles:
            if self.detail and self.layout_info is not None:
                self.cursor_changed.emit(self.layout_info.index_at(x))
            else:
                start, stop = self.window()
                visible = stop - start
                # Pointer selection is complemented by an exact, keyboard accessible slider.
                from core.market.presentation import plot_bounds
                left, right = plot_bounds(max(320, self.width()))
                fraction = max(0, min(1, (event.position().x() - left) / max(1, right - left)))
                self.cursor_changed.emit(start + round(fraction * max(0, visible - 1)))
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        x = event.position().x()
        if event.button() == Qt.MouseButton.LeftButton and self._on_plot(x):
            # Owner R-D12-2: a left press on the plot grabs the chart; it pans once the press moves the platform
            # drag distance, and a press released before that is a click that selects the bar under it.
            layout = self.layout_info
            self._press, self._pointer_x = event.position(), x
            self._grab = (x, layout.start, layout.step, layout.plot_left)
            self._grab_layout = self._layout_key()
            self._dragging = False
            event.accept()
            return
        super().mousePressEvent(event)

    def _drag_move(self, event):
        """Grab-and-drag: the bar grabbed at the press stays under the pointer (the window starts that many bars
        earlier or later; the pane stops it at the first and the latest bar, the selection staying on the bar under
        the pointer). The zoom is kept, the page never moves. When something else moved or zoomed the window while
        the press was held (Ctrl + wheel, a key, a period chip, a new live bar), the drag goes on from the bar under
        the pointer at that moment instead of undoing that change."""
        position = event.position()
        x = position.x()
        if not self._dragging:
            if (position - self._press).manhattanLength() < QApplication.startDragDistance():
                self._pointer_x = x
                return
            self._dragging = True
        layout = self.layout_info
        if layout is None or layout.stop <= layout.start:
            self._pointer_x = x
            return
        if self._layout_key() != self._grab_layout:
            self._grab = (self._pointer_x, layout.start, layout.step, layout.plot_left)
        self._pointer_x = x
        self._set_pointer(Qt.CursorShape.ClosedHandCursor)
        origin, start, step, left = self._grab
        step = max(float(step), 1e-9)
        grabbed = math.floor((origin - left) / step)    # the grabbed bar's slot ...
        now = math.floor((x - left) / step)             # ... and the slot under the pointer now
        if self.drag_handler is not None:
            self.drag_handler(start + grabbed - now, x)
        self._grab_layout = self._layout_key()

    def mouseReleaseEvent(self, event):
        if self._press is not None and event.button() == Qt.MouseButton.LeftButton:
            self._release_drag()
            x = event.position().x()
            if self.detail:
                self._hover_x = x if self.rect().contains(event.position().toPoint()) else None
                self._hover_cursor(x)
                if self.layout_info is not None and self.snapshot and self.snapshot.candles:
                    # A click selects the bar under it, as before; after a drag the selection (and the readout) is
                    # the bar under the pointer too, also when the drag ended against the first or the latest bar.
                    self.cursor_changed.emit(self.layout_info.index_at(x))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        self._release_drag()
        super().hideEvent(event)

    def wheelEvent(self, event):
        """Owner 2026-11-11: the plain wheel never moves or zooms the chart. Over the stock screen's chart it does
        nothing at all (accepted, so the page does not scroll either); elsewhere the page scrolls.

        Owner R-D12-1 (2026-11-12): Ctrl + wheel over the stock screen's chart zooms, wheel up in, one notch one
        step, on the bar under the pointer (it stays under the pointer). Sideways turns never pan or zoom."""
        if not self.detail:
            event.ignore()
            return
        event.accept()
        if not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._wheel_rest = 0
            self.wheel_ignored.emit()
            return
        delta = event.angleDelta()
        if abs(delta.x()) > abs(delta.y()):
            return
        turn = -delta.y() if event.inverted() else delta.y()   # the wheel's own direction: away from the hand = in
        if not turn:
            return
        if (turn > 0) != (self._wheel_rest > 0):
            self._wheel_rest = 0                                # a turn back starts afresh
        self._wheel_rest += turn
        steps = int(self._wheel_rest / self.WHEEL_NOTCH)
        if not steps:
            return
        self._wheel_rest -= steps * self.WHEEL_NOTCH
        if self.zoom_handler is not None:
            self.zoom_handler(steps, event.position().x())

    def event(self, event):
        """A trackpad pinch (QNativeGestureEvent ZoomNativeGesture) zooms like Ctrl + wheel (R-D12-1). Hover moves,
        which also come while the pointer is over an overlay label, keep the pointer shape (R-D12-2)."""
        kind = event.type()
        if self.detail and kind in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
            x = self.mapFromGlobal(event.globalPosition()).x()
            self._hover_x = x
            if self._press is None:
                self._hover_cursor(x)
        elif kind in (QEvent.Type.HoverLeave, QEvent.Type.Leave):
            self._hover_x = None
        if self.detail and kind == QEvent.Type.NativeGesture:
            if event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                self._pinch_rest += event.value()
                steps = int(self._pinch_rest / self.PINCH_STEP)
                if steps:
                    self._pinch_rest -= steps * self.PINCH_STEP
                    if self.zoom_handler is not None:
                        self.zoom_handler(steps, event.position().x())
                event.accept()
                return True
            if event.gestureType() in (Qt.NativeGestureType.BeginNativeGesture, Qt.NativeGestureType.EndNativeGesture):
                self._pinch_rest = 0.0
        return super().event(event)

    def keyPressEvent(self, event):
        handler = getattr(self, "key_handler", None)
        if handler is not None and handler(event):
            event.accept()
            return
        super().keyPressEvent(event)


class MarketChartPane(QWidget):
    """One bounded REST worker and one cancellable stream per visible chart pane."""
    snapshot_loaded = pyqtSignal(object)
    trade_received = pyqtSignal(object)
    feed_state_changed = pyqtSignal(str)
    rendered = pyqtSignal()    # after every render(): the stock screen refreshes its header, overlays and readings
    q_score_changed = pyqtSignal()

    def __init__(self, *, service=None, stream_factory=None, locale=None, router=None):
        super().__init__()
        from core.market.routing import ChartRouter, KISChartProvider, default_chart_router
        injected = service is not None
        if service is None:
            from data.kis_workspace import MarketDataService
            service = MarketDataService()
        # The KIS route always reads the pane's current service. An injected service
        # (fixtures) keeps KIS-only behaviour unless a router is given explicitly.
        current = lambda: self.service
        self.router = router or (ChartRouter(KISChartProvider(current)) if injected else default_chart_router(current))
        if stream_factory is None:
            from data.kis_stream import KISStream
            stream_factory = KISStream
        self.service, self.stream_factory = service, stream_factory
        self.ctx = locale or LocaleContext("ko_KR")
        self.snapshot = None
        self._epoch = self._job_epoch = 0
        self._stream = None
        self._stream_gap = False
        self._last_received = ""
        self._last_tick_received = ""
        self._mode = "idle"
        self._emitted_mode = None
        self._q_score = None
        self._status_detail = ""
        self._cursor = 0
        self._last_request = None
        self._attempts = ()
        self._pending_stream_epoch = None
        self._auto_updates = False
        self._restart_pending = False
        self._resync_attempted = False
        # Stock screen (detail mode, owner 2026-11-11): pan window, registry studies and the period chip.
        self.detail = False
        self._end = None          # last bar index shown; None follows the latest bar
        self._studies = None      # registry study keys; None means the five legacy buttons choose
        self.period = None        # detail_model.PERIODS key that chose the request, or None
        self.period_view = False  # True while the window is the period's own (no manual pan or zoom since)
        self.supply = None        # core.education.indicators.Supply for the KIS supply/demand studies
        self.input_timer = QTimer(self)
        self.input_timer.setSingleShot(True)
        self.input_timer.setInterval(450)
        self.input_timer.timeout.connect(self._restart_after_inputs)
        self.resync_timer = QTimer(self)
        self.resync_timer.setSingleShot(True)
        self.resync_timer.setInterval(450)
        self.resync_timer.timeout.connect(self._resync_after_gap)
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        self.bridge = _StreamBridge(self)
        self.bridge.tick.connect(self._tick)
        self.bridge.status.connect(self._stream_status)
        self.bridge.history.connect(self._history_preview)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(5000)
        self.poll_timer.timeout.connect(self.refresh)
        self.age_timer = QTimer(self)
        self.age_timer.setInterval(1000)
        self.age_timer.timeout.connect(self._render_status)
        # Fold trade bursts into five chart paints per second; tick merging stays ordered.
        self.paint_timer = QTimer(self)
        self.paint_timer.setSingleShot(True)
        self.paint_timer.setInterval(200)
        self.paint_timer.timeout.connect(self.render)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.intro = self._label()
        self.intro.setProperty("role", "heading")
        layout.addWidget(self.intro)
        form = QGridLayout()
        for column, stretch in enumerate((2, 3, 1)):
            form.setColumnStretch(column, stretch)
        self.asset = QComboBox()
        self.asset.setMinimumWidth(145)
        for key, ko, en, code in _ASSETS:
            self.asset.addItem(ko, key)
        self.symbol = QLineEdit("005930")
        self.symbol.setMaxLength(32)
        self.symbol.returnPressed.connect(lambda: self.refresh(manual=True))
        self.exchange = QComboBox()
        self.exchange.setMinimumWidth(95)
        self.interval = QComboBox()
        for interval in INTERVALS:
            self.interval.addItem(_INTERVAL_NAMES.get(interval, interval), interval)
        self.interval.setCurrentIndex(self.interval.findData("1d"))
        self.bar_count = QSpinBox()
        self.bar_count.setRange(20, 500)
        # Owner UI-16: no 조회 봉 수 input. Load 240 bars so Ctrl + wheel can zoom out past the 120 shown.
        self.bar_count.setValue(240)
        self.form_labels = [self._label() for _ in range(5)]
        for column, index in enumerate((0, 1, 3)):
            form.addWidget(self.form_labels[index], 0, column)
            form.addWidget((self.asset, self.symbol, self.exchange, self.interval, self.bar_count)[index], 1, column)
        # The Markets asset-class tab chooses the asset (UI-8); the combo stays as state only.
        self.asset.hide();self.form_labels[0].hide()
        # Exchange is not an input (UI-16): overseas search sets it; only domestic derivatives
        # keep a visible market selector (F/O/JF/…), which KIS needs for ambiguous codes.
        form.addWidget(self.form_labels[2], 0, 0)
        form.addWidget(self.exchange, 1, 0)
        self._form = form
        layout.addLayout(form)
        self.symbol_suggestions = QListWidget()
        self.symbol_suggestions.setObjectName("symbolSuggestions")
        self.symbol_suggestions.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.symbol_suggestions.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.symbol_suggestions.itemClicked.connect(self._symbol_chosen)
        self.symbol_suggestions.itemActivated.connect(self._symbol_chosen)
        self.symbol_suggestions.hide()
        self.symbol.installEventFilter(self)
        self.symbol_suggestions.installEventFilter(self)
        self._choosing_symbol = False
        layout.addWidget(self.symbol_suggestions)
        buttons = QHBoxLayout()
        self.load_button = QPushButton()
        self.load_button.setProperty("primary", True)
        self.load_button.clicked.connect(lambda: self.refresh(manual=True))
        self.poll_button = QCheckBox()
        self.poll_button.toggled.connect(self._poll_toggled)
        self.stream_button = QPushButton()
        self.stream_button.clicked.connect(self.start_stream)
        self.stop_button = QPushButton()
        self.stop_button.clicked.connect(self.stop)
        self.advanced_button = QPushButton()
        self.advanced_button.setCheckable(True)
        buttons.addWidget(self.load_button)
        buttons.addWidget(self.stop_button)
        buttons.addStretch()
        buttons.addWidget(self.advanced_button)
        layout.addLayout(buttons)
        self.status = self._label()
        self.status.setProperty("role", "muted")
        self.quote = self._label()
        self.quote.setProperty("role", "number")
        self.quote_detail = self._label()
        self.q_score_label = self._label()
        self.q_score_label.hide()
        for field in (self.status, self.quote, self.quote_detail, self.q_score_label):
            layout.addWidget(field)
        # Owner, 2026-11-04: no provider or observation-time lines. `provenance` shows only a delay
        # notice when the data is not domestic real-time; source and times live in the price tooltip.
        self.provenance, self.times = self._label(), self._label()
        self.times.hide()
        source_lines = QVBoxLayout()
        source_lines.setSpacing(5)
        for field in (self.provenance, self.times):
            field.setProperty("role", "caption")
            source_lines.addWidget(field)
        layout.addLayout(source_lines)
        self.note, self.availability = self._label(), self._label()
        self.advanced = QWidget()
        advanced_layout = QVBoxLayout(self.advanced)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_form = QGridLayout()
        self.zoom_label = self._label()
        self.visible_bars = QSpinBox()
        self.visible_bars.setRange(20, 500)
        self.visible_bars.setValue(120)
        self.visible_bars.valueChanged.connect(self.render)
        # History size and visible bars are internal state now: Ctrl + wheel zooms the chart (R-D12-1).
        for column, (caption, control) in enumerate(((self.form_labels[4], self.bar_count), (self.zoom_label, self.visible_bars))):
            advanced_form.addWidget(caption, 0, column)
            advanced_form.addWidget(control, 1, column)
            caption.hide()
            control.hide()
        advanced_layout.addLayout(advanced_form)
        actions = QHBoxLayout()
        actions.addWidget(self.poll_button)
        actions.addWidget(self.stream_button)
        actions.addStretch()
        advanced_layout.addLayout(actions)
        for field in (self.note, self.availability):
            advanced_layout.addWidget(field)
        self.advanced.hide()
        self.advanced_button.toggled.connect(self.advanced.setVisible)
        layout.addWidget(self.advanced)
        heading = QHBoxLayout()
        self.indicator_title = self._label()
        self.indicator_title.setProperty("role", "heading")
        self.guide_button = QPushButton()
        self.guide_button.setCheckable(True)
        heading.addWidget(self.indicator_title)
        heading.addStretch()
        heading.addWidget(self.guide_button)
        layout.addLayout(heading)
        display_row = QHBoxLayout()
        self.indicator_boxes = {}
        # A whole button is clickable; network state never disables display choices.
        for key in ("sma", "ema", "bollinger", "rsi", "macd"):
            button = QPushButton()
            button.setCheckable(True)
            button.setChecked(key == "sma")
            button.setProperty("indicator", key)
            button.toggled.connect(self.render)
            display_row.addWidget(button)
            self.indicator_boxes[key] = button
        layout.addLayout(display_row)
        self.chart_help = self._label()
        self.chart_help.setProperty("role", "muted")
        self.feed_notice = self._label()
        self.feed_notice.setProperty("role", "muted")
        self.indicator_help = self._label()
        self.guide = self._label()
        self.guide.hide()
        self.guide_button.toggled.connect(self.guide.setVisible)
        for field in (self.chart_help, self.feed_notice, self.indicator_help, self.guide):
            layout.addWidget(field)
        self.empty_state = self._label()
        layout.addWidget(self.empty_state)
        # Stock screen only (spec 10): a failed first load shows a retry button and what was tried under the text.
        self.empty_actions = QWidget()
        actions = QVBoxLayout(self.empty_actions)
        actions.setContentsMargins(24, 4, 24, 0)
        actions.setSpacing(10)
        actions.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.empty_retry = QPushButton()
        self.empty_retry.setProperty("sd", "text")
        self.empty_retry.setProperty("qg_literal", True)
        self.empty_retry.clicked.connect(lambda: self.refresh(manual=True))
        actions.addWidget(self.empty_retry, 0, Qt.AlignmentFlag.AlignHCenter)
        self.empty_tried = self._label()
        self.empty_tried.setProperty("role", "muted")
        self.empty_tried.setProperty("qg_literal", True)
        self.empty_tried.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.empty_tried.setMaximumWidth(560)
        actions.addWidget(self.empty_tried, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.empty_actions)
        self.empty_actions.hide()
        self.chart = MarketChartSvg()
        self.chart.zoom_handler = self.zoom_at
        self.chart.drag_handler = self.drag_to
        self.chart.key_handler = self.chart_key
        self.chart.cursor_changed.connect(self.move_cursor)
        layout.addWidget(self.chart)
        self.cursor_slider = QSlider(Qt.Orientation.Horizontal)
        self.cursor_slider.valueChanged.connect(self.move_cursor)
        self.cursor_slider.setEnabled(False)
        layout.addWidget(self.cursor_slider)
        self.reading, self.indicator_reading, self.limitations = self._label(), self._label(), self._label()
        for field in (self.reading, self.indicator_reading, self.limitations):
            layout.addWidget(field)
        self.asset.currentIndexChanged.connect(self._asset_changed)
        self.symbol.textChanged.connect(self._inputs_changed)
        self.symbol.textChanged.connect(self._symbol_typed)
        self.exchange.currentIndexChanged.connect(self._exchange_changed)
        self.interval.currentIndexChanged.connect(self._inputs_changed)
        self.bar_count.valueChanged.connect(self._inputs_changed)
        self._configure_exchange()
        self._configure_intervals()
        self.set_locale(self.ctx)
        self._busy(False)

    @staticmethod
    def _label():
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def _text(self, ko, en):
        return ko if self.ctx.language == "ko" else en

    def _indicator_explanation(self, key):
        descriptions = {
            "sma": ("이동평균 · 최근 20개 값의 평균 가격입니다. 가격 위·아래에서 흐름을 비교해 보세요. 변화에 늦게 반응할 수 있어요.",
                    "Moving average · Mean closing price of 20 bars. Compare price above or below the line to read the trend; it can lag."),
            "ema": ("지수이평 · 최근 가격에 더 무게를 둔 12·26개 값의 평균입니다. 두 선의 방향과 간격을 보세요. 빠른 반응만큼 잘못된 전환 신호도 늘 수 있어요.",
                    "EMA · Averages over 12/26 bars give recent prices more weight. Compare the lines' direction and gap; faster response can mean more false turns."),
            "bollinger": ("볼린저 · 최근 20개 값의 변동 폭을 보여줍니다. 밴드가 벌어지면 가격 변화가 커진 구간이에요. 경계에 닿아도 반전이 보장되지는 않아요.",
                          "Bollinger · Bands show price variation over 20 bars. Wider bands mean more variation; touching an edge does not guarantee a reversal."),
            "rsi": ("RSI · 최근 14개 값의 상승·하락 강도를 0~100으로 비교합니다. 70·30선을 참고하되, 강한 흐름에서는 높거나 낮은 값이 오래 이어질 수 있어요.",
                    "RSI · Compares gains and losses over 14 bars on a 0–100 scale. Watch 70/30, but strong trends can stay high or low."),
            "macd": ("MACD · 빠른 평균과 느린 평균의 차이로 흐름 변화를 봅니다. 아래 두 선과 막대의 방향을 함께 보세요. 횡보에서는 잦은 교차가 생길 수 있어요.",
                     "MACD · The gap between fast and slow averages shows changes in momentum. Read both lines and the bars; sideways prices can cause repeated crossings."),
        }
        return self._text(*descriptions[key])

    def _paper(self):
        from urllib.parse import urlparse
        base = str(getattr(getattr(self.service, "client", None), "base_url", ""))
        return urlparse(base).hostname == "openapivts.koreainvestment.com"

    def _can_stream(self, request):
        from data.kis_stream import subscription_for
        try:
            subscription_for(request.instrument, paper=self._paper())
            return True
        except ValueError:
            return False

    def _exchange_changed(self, *_):
        self._configure_intervals()
        self._inputs_changed()

    def _availability_text(self, instrument):
        from data.kis_workspace import availability_note
        if self.ctx.language != "ko":
            return availability_note(instrument)
        return {
            "domestic_stock": "KRX 시장 · 마지막 값은 아직 변할 수 있어요. 진행 중인 분 단위 거래량은 공급자 값이 확정되기 전까지 표시하지 않습니다. 빈 시간을 가짜 값으로 채우지 않아요.",
            "domestic_future": "국내 선물·옵션 · 만기 종목과 일치하는 시장을 선택하세요. 가격은 포인트 등 계약별 시세 단위이며 일반 원화 현금 금액이 아닙니다. 마지막 값은 변할 수 있어요.",
            "bond": "채권 이력은 최대 100거래일이며 과거 분 단위 조회는 지원하지 않습니다. 가격은 액면 10,000원 기준입니다.",
            "overseas_future": "해외선물 가격은 검증된 종목 마스터의 가격 배율을 적용합니다. 공급자 시각 기준이 검증되지 않은 분 단위 자료는 제공하지 않습니다. CME·SGX 시세는 별도 이용 권한이 필요합니다.",
            "overseas_stock": ("미국 무료 Nasdaq 시장센터 시세 · 지연 0분. 유료 통합 시세와 거래 범위·가격이 다를 수 있어요. 과거 분 단위 자료는 정규장만 포함하며 시가는 다음 날 정정될 수 있습니다."
                               if instrument.exchange in ("NAS", "NYS", "AMS") else "해외 무료 시세 · 15분 지연. 과거 분 단위 자료는 정규장만 포함합니다."),
        }[instrument.asset]

    def _data_note(self, note, instrument):
        if self.ctx.language != "ko" or not note:
            return note
        import re
        from data.kis_workspace import availability_note
        note = note.replace(availability_note(instrument), self._availability_text(instrument))
        translations = {
            "Received executions only: tick/second bars begin when the stream connects. Historical tick/second bars are unavailable; gaps are not filled. The first/current bar can be partial; volume is received trade volume, not session volume.": "틱·초 단위는 연결 이후 받은 체결만 모읍니다. 과거 틱·초 자료는 제공하지 않으며 빈 구간을 채우지 않습니다. 첫 구간·현재 구간은 일부 체결만 포함할 수 있고, 거래량은 수신한 체결의 합계입니다.",
            "Current quote unavailable; waiting for a valid streaming execution.": "현재가 조회 불가 · 정상 체결 수신을 기다립니다.",
            "Clock-aligned aggregation of observed minute bars; missing minutes are not filled.": "관측된 1분 자료를 시각 구간에 맞춰 묶습니다. 없는 분은 채우지 않습니다.",
            "Clock-aligned aggregation of observed one-minute bars; first/latest bars can be partial.": "관측된 1분 자료를 시각 구간에 맞춰 묶습니다. 처음과 마지막 구간은 일부만 담길 수 있습니다.",
            "Live gap: some executions were not received; affected bars are partial. No missing trades are reconstructed.": "체결 공백 · 일부 체결을 받지 못해 해당 구간이 불완전합니다. 누락된 거래는 만들어 채우지 않습니다.",
            "Live gap: missing trades may affect OHLC and minute-bar volume. Reload history to reconcile.": "체결 공백 · 가격·분 단위 거래량에 누락이 있을 수 있습니다. 다시 조회해 이력을 맞추세요.",
            "REST snapshot; quote timestamp convention unverified.": "시점 조회 · 시세 시각 기준 미검증.",
            "REST snapshot; market timestamp not provided.": "시점 조회 · 공급자가 시장 시각을 제공하지 않습니다.",
            "Yahoo Finance fallback: unadjusted OHLC, delayed; not a KIS quote. Live trade updates and Q-SCORE use KIS only.": "Yahoo Finance 대체 자료 · 수정 전 시가·고가·저가·종가, 지연 시세이며 KIS 시세가 아닙니다. 실시간 체결 갱신과 Q-SCORE는 KIS 자료만 씁니다.",
        }
        for original, translated in translations.items():
            note = note.replace(original, translated)
        # The yearly chart's monthly request, with or without the KIS paging remark (Yahoo writes none).
        note = re.sub(r"Partial history: (\d+)/(\d+) requested monthly bars \(provider window or paging limit\)\.",
                      r"부분 이력 · 요청한 \2개월 중 \1개월만 조회됐습니다(공급자 조회 범위·페이지 한도).", note)
        note = re.sub(r"Partial history: (\d+)/(\d+) requested monthly bars\.",
                      r"부분 이력 · 요청한 \2개월 중 \1개월만 조회됐습니다.", note)
        note = re.sub(r"Partial history: (\d+)/(\d+) requested bars \(provider window or paging limit\)\.",
                      r"부분 이력 · 요청한 \2개 중 \1개만 조회됐습니다(공급자 조회 범위·페이지 한도).", note)
        note = re.sub(r"Yearly candles from monthly history: first month (\d{4})-(\d{2}), last month (\d{4})-(\d{2})\.",
                      r"연 단위는 월 자료를 해마다 묶었습니다(첫 달 \1-\2, 마지막 달 \3-\4).", note)
        return re.sub(r"Partial history: (\d+)/(\d+) requested bars\.",
                      r"부분 이력 · 요청한 \2개 중 \1개만 조회됐습니다.", note)

    def _restart_after_inputs(self):
        if not self._restart_pending or self.jobs.busy:
            return
        self._restart_pending = False
        self.refresh(manual=True)

    def _resync_after_gap(self):
        if not self._auto_updates or not self._stream_gap:
            return
        if self.jobs.busy:
            self.resync_timer.start()
            return
        self.refresh(for_stream=True, automatic=True)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.intro.setText(self._text("가격의 흐름을 한눈에", "See the price story"))
        self.load_button.setText(self._text("조회 / 새로고침", "Load / refresh"))
        self.poll_button.setText(self._text("5초 주기 조회", "Poll every 5 seconds"))
        self.stream_button.setText(self._text("체결 연결 다시 시도", "Retry trade stream"))
        self.stop_button.setText(self._text("수신 중지", "Stop updates"))
        self.advanced_button.setText(self._text("데이터 설명 · 수신 설정", "Data notes · updates"))
        self.indicator_title.setText(self._text("기술지표", "Indicators"))
        self.guide_button.setText(self._text("차트 읽는 법 ?", "How to read this ?"))
        self.zoom_label.setText(self._text("표시 개수", "Visible bars"))
        self.chart_help.setText(self._text("캔들 하나는 선택한 시간 단위의 가격입니다. 아래 거래량은 거래된 수량이에요.",
                                         "Each candle shows prices over one interval. Volume below shows how much traded."))
        self.guide.setText(self._text(
            "캔들의 몸통은 시작·마지막 가격, 위아래 꼬리는 최고·최저 가격입니다. 빨강은 시작보다 상승, 파랑은 하락을 뜻해요. "
            "마지막 캔들은 체결마다 바뀔 수 있어요. 틱 단위는 체결 횟수, 초·분 단위는 시간을 기준으로 묶습니다. "
            "틱·초 단위는 연결 이후 받은 체결부터 쌓이며 빈 시간을 가짜 캔들로 채우지 않아요. "
            "차트에 마우스를 올리거나 좌우 방향키로 값을 살펴보세요. 지표를 다시 누르면 숨길 수 있어요. 지표는 투자 판단의 참고자료입니다.",
            "The candle body runs from open to close; wicks show the high and low. Red closes above the open, blue below. "
            "The latest candle can change with each trade. Tick candles group a number of trades; second and minute candles group time. "
            "Tick/second candles start with trades received after connecting; empty periods are not filled with invented bars. "
            "Hover or use the arrow keys to inspect a candle. Select an indicator again to hide it. Indicators are research aids."))
        names = {"sma": ("이동평균", "Moving avg"), "ema": ("지수이평", "EMA"),
                 "bollinger": ("볼린저", "Bollinger"), "rsi": ("RSI", "RSI"), "macd": ("MACD", "MACD")}
        for key, button in self.indicator_boxes.items():
            button.setText(self._text(*names[key]))
            button.setAccessibleName(self._text(*names[key]) + self._text(" 표시 / 숨기기", " show / hide"))
            button.setToolTip(self._indicator_explanation(key))
        for label, ko, en in zip(self.form_labels,
                ("자산", "종목 코드", "시장 구분", "시간 단위", "조회 개수"),
                ("Asset", "Instrument code", "Market", "Interval", "History bars")):
            label.setText(self._text(ko, en))
        self._search_mode()
        if self.symbol_suggestions.count():
            self._symbol_typed(self.symbol.text())  # rebuild labels in the new language
        self.asset.blockSignals(True)
        for index, (_, ko, en, _) in enumerate(_ASSETS):
            self.asset.setItemText(index, self._text(ko, en))
        self.asset.blockSignals(False)
        self.interval.blockSignals(True)
        for index, interval in enumerate(INTERVALS):
            self.interval.setItemText(index, self._text(_INTERVAL_NAMES.get(interval, interval), interval))
        self.interval.blockSignals(False)
        if self.asset.currentData() == "domestic_future" and self.exchange.count():
            self.exchange.setItemText(0, self._text("자동 · 지수선물", "Auto · index future"))
        for control, ko, en in ((self.asset,"자산 선택","Select asset"), (self.symbol,"종목 코드","Instrument code"),
                (self.exchange,"시장 구분","Market division"), (self.interval,"차트 시간 단위","Chart interval"),
                (self.bar_count,"조회 개수","History bars"), (self.visible_bars,"표시 개수","Visible bars"),
                (self.cursor_slider,"캔들 선택 · 좌우 방향키","Select candle · left / right arrows")):
            control.setAccessibleName(self._text(ko, en))
        self.limitations.setText(self._text(
            "체결 수신은 장 운영과 이용 권한에 따라 달라집니다. 해외 시세는 지연될 수 있어요. 지표 계산에 필요한 자료가 부족하면 —로 표시합니다. 화면을 벗어나면 수신을 멈춥니다.",
            "Trade delivery depends on market hours and access; overseas data may be delayed. Indicators show — until enough bars arrive. Updates stop when you leave this screen."))
        self.render()

    # Stock screen (detail mode) -------------------------------------------------------------------
    def _detail_hidden(self):
        """Pane widgets the stock screen replaces with its own toolbar, period bar, overlays and side column."""
        return (self.intro, self.symbol, self.symbol_suggestions, self.load_button, self.stop_button,
                self.advanced_button, self.advanced, self.status, self.quote, self.quote_detail, self.q_score_label,
                self.provenance, self.times, self.indicator_title, self.guide_button, *self.indicator_boxes.values(),
                self.chart_help, self.indicator_help, self.guide, self.cursor_slider, self.reading,
                self.indicator_reading, self.limitations, self.interval, self.form_labels[1], self.form_labels[3])

    def _show(self, widget, visible):
        widget.setVisible(bool(visible) and not (self.detail and widget in self._detail_hidden()))

    def set_detail_mode(self, on):
        """Owner 2026-11-11: the stock screen shows the chart large; its toolbar, period bar and right column
        replace the pane's own controls. The pane keeps the feed notice, the empty state and the chart (which
        then fills the height it is given), and the domestic-derivative market selector."""
        on = bool(on)
        if on == self.detail:
            return
        self.detail = on
        layout = self.layout()
        if on:
            for widget in self._detail_hidden():
                widget.hide()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            layout.setAlignment(Qt.AlignmentFlag(0))
            layout.setStretchFactor(self.chart, 1)
            self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty_state.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            self.empty_actions.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            self.chart.set_detail(True)
            self._configure_intervals()
        self.render()

    def selected_indicators(self):
        """The registry keys drawn (core.education.indicators.STUDIES; the legacy 'bollinger' is 'bb')."""
        if self._studies is not None:
            return self._studies
        return tuple("bb" if key == "bollinger" else key for key, button in self.indicator_boxes.items()
                     if button.isChecked())

    def set_indicators(self, keys):
        """Choose the studies by registry key; the five legacy buttons mirror the choice."""
        from core.education.indicators import study
        chosen = []
        for key in keys:
            try:
                name = study(key).key
            except ValueError:
                continue
            if name not in chosen:
                chosen.append(name)
        self._studies = tuple(chosen)
        for key, button in self.indicator_boxes.items():
            button.blockSignals(True)
            button.setChecked(("bb" if key == "bollinger" else key) in self._studies)
            button.blockSignals(False)
        self.render()

    def window(self):
        """(start, stop) of the bars shown."""
        from core.market.detail_model import window
        n = len(self.snapshot.candles) if self.snapshot else 0
        return window(n, self.visible_bars.value(), self._end)

    def pan(self, bars):
        """Move the window `bars` bars (negative: older); the selected candle moves with it."""
        n = len(self.snapshot.candles) if self.snapshot else 0
        if n < 2 or not bars:
            return False
        start, stop = self.window()
        visible = stop - start
        current = stop - 1
        target = max(visible - 1, min(n - 1, current + int(bars)))
        if target == current:
            return False
        self._end = None if target >= n - 1 else target
        shift = target - current
        self._cursor = max(target - visible + 1, min(target, self._cursor + shift))
        self.period_view = False
        self.render()
        return True

    def drag_to(self, start, x=None):
        """Owner R-D12-2 ("차트 화면 좌클릭해서 좌우로 끌면 좌우도 움직일수잇게 !! 화살표도 유지하고"): a left-drag on the
        chart shows the window from bar `start`, stopped at the first and the latest bar; the zoom is kept and a
        window that reaches the latest bar follows live data again. The selected candle is the one under the pointer
        at chart x (the grabbed one, while the window is not stopped at an end), also when the window cannot move.
        Returns whether the window moved."""
        n = len(self.snapshot.candles) if self.snapshot else 0
        if n < 2:
            return False
        first, stop = self.window()
        visible = stop - first
        start = max(0, min(n - visible, int(start)))
        moved = start != first
        end = start + visible - 1
        cursor = self._cursor
        layout = self.chart.layout_info
        if x is not None and layout is not None and layout.step > 0:
            # Also when the window is stopped at an end (or every bar is shown): the readout follows the pointer.
            slot = math.floor((float(x) - layout.plot_left) / layout.step)
            cursor = start + max(0, min(visible - 1, slot))
        elif moved:
            cursor = max(start, min(end, self._cursor + start - first))
        if not moved and cursor == self._cursor:
            return False
        if moved:
            self._end = None if end >= n - 1 else end
            self.period_view = False
        self._cursor = cursor
        self.render()
        return moved

    def go_first(self):
        """Home: the earliest loaded candles, the selection on the first one."""
        if not self.snapshot or not self.snapshot.candles:
            return False
        start, stop = self.window()
        visible = stop - start
        n = len(self.snapshot.candles)
        self._end = None if visible >= n else visible - 1
        self._cursor = 0
        self.period_view = False if self._end is not None else self.period_view
        self.render()
        return True

    def follow_latest(self):
        """End: back to the latest bar, following live data."""
        if not self.snapshot or not self.snapshot.candles:
            return False
        self._end = None
        self._cursor = len(self.snapshot.candles) - 1
        self.render()
        return True

    def reset_view(self):
        """'0' / 기본 보기: the period's own window (or 120 bars), following the latest bar."""
        from core.market.detail_model import visible_for
        self._end = None
        if self.snapshot and self.snapshot.candles:
            self._cursor = len(self.snapshot.candles) - 1
        visible = visible_for(self.period, self.snapshot.candles if self.snapshot else ()) if self.period else 120
        self.period_view = self.period is not None
        self.visible_bars.blockSignals(True)
        self.visible_bars.setValue(max(self.visible_bars.minimum(), visible))
        self.visible_bars.blockSignals(False)
        self.render()
        return True

    def apply_period(self, key):
        """A period chip: interval, bars requested and bars shown (core.market.detail_model.PERIODS).

        Daily periods share one 1d x 400 request, so moving among them only changes the window. A new request
        reloads at once only when the chart had data or was updating; with automatic loading off and nothing
        loaded it stays explicit."""
        from core.market.detail_model import period_request
        try:
            instrument = self.request().instrument
        except (TypeError, ValueError):
            instrument = None
        interval, limit = period_request(key, instrument)
        index = self.interval.findData(interval)
        if index < 0:
            return False
        self.period, self.period_view = key, True
        if interval == self.interval.currentData() and limit == self.bar_count.value():
            if self.snapshot is not None:
                self.reset_view()
            else:
                self.render()
            return True
        had = (self.snapshot is not None and bool(self.snapshot.candles)) or self._auto_updates
        for control in (self.interval, self.bar_count):
            control.blockSignals(True)
        self.interval.setCurrentIndex(index)
        self.bar_count.setValue(limit)
        for control in (self.interval, self.bar_count):
            control.blockSignals(False)
        self._inputs_changed()
        if had:
            self.refresh(manual=True)
        return True

    def set_interval(self, interval):
        """An interval chosen in the stock screen's toolbar: no period chip, the latest 120 bars shown of a request
        sized for the interval (core.market.detail_model.interval_request: never the 50 years the 전체 chip
        left behind)."""
        from core.market.detail_model import interval_request
        index = self.interval.findData(interval)
        if index < 0 or interval == self.interval.currentData():
            return False
        try:
            instrument = self.request().instrument
        except (TypeError, ValueError):
            instrument = None
        self.period, self.period_view = None, False
        for control, value in ((self.visible_bars, 120),
                               (self.bar_count, interval_request(interval, instrument, self.bar_count.value()))):
            control.blockSignals(True)
            control.setValue(value)
            control.blockSignals(False)
        had = (self.snapshot is not None and bool(self.snapshot.candles)) or self._auto_updates
        self.interval.setCurrentIndex(index)
        if had:
            self.refresh(manual=True)
        return True

    def chart_key(self, event):
        """Owner 2026-11-11: "좌우화살표로 차트 좌우 확인할수있게" — ←/→ move the chart itself one step (Shift: ten),
        the selected candle moving with it; when every loaded candle is already in view they move the selection
        instead. Home/End go to the first loaded / the latest data and 0 restores the view. No key zooms: the
        chart zooms with Ctrl + wheel (owner R-D12-1 "차트 확대를 +-로 하지말고 컨트롤 + 마우스 휠 이렇게 하자")."""
        key, shift = event.key(), bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        if self.snapshot is None or not self.snapshot.candles:
            return False
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            direction = 1 if key == Qt.Key.Key_Right else -1
            if not self.pan((10 if shift else 1) * direction):
                self.move_cursor(self._cursor + (10 if shift else 1) * direction)
            return True
        if key == Qt.Key.Key_Home:
            self.go_first()
            return True
        if key == Qt.Key.Key_End:
            self.follow_latest()
            return True
        if key == Qt.Key.Key_0 and not shift:
            self.reset_view()
            return True
        return False

    def feed_facts(self):
        """What the stock screen states about the feed, without reading private fields."""
        snapshot = self.snapshot
        quote = snapshot.quote if snapshot is not None else None
        return {"mode": self._mode, "has_data": bool(snapshot and snapshot.candles),
                "source": str(getattr(snapshot, "source", "") or ""),
                "last_trade_at": str(getattr(snapshot, "last_tick_at", "") or ""),
                "last_received": self._last_received, "fetched_at": str(getattr(snapshot, "fetched_at", "") or ""),
                "market_time": str(getattr(quote, "market_time", "") or ""), "status": self.status.text(),
                "notice": self.feed_notice.text(), "note": self.note.text(), "availability": self.availability.text(),
                "streaming": self._stream is not None, "polling": self.poll_timer.isActive(),
                "busy": self.jobs.busy, "auto": self._auto_updates}

    def set_q_score(self, symbol, score):
        if symbol != self.symbol.text().strip() or self.asset.currentData() != 'domestic_stock':
            return
        self._q_score = (symbol, score)
        self._render_q_score()
        self.q_score_changed.emit()

    def _render_q_score(self):
        visible = bool(self.snapshot and self._q_score and
                       self.snapshot.request.instrument.asset == 'domestic_stock' and
                       self.snapshot.request.instrument.code == self._q_score[0])
        self._show(self.q_score_label, visible)
        if visible:
            from .watchlist import _score_text, _score_tooltip
            score = self._q_score[1]
            self.q_score_label.setText('Q-SCORE · ' + _score_text(score, self.ctx))
            self.q_score_label.setToolTip(_score_tooltip(score, self.ctx))
        self._q_score_shown = visible

    def q_score_text(self):
        """(text, tooltip) of the open stock's Q-SCORE, or None."""
        if not getattr(self, "_q_score_shown", False):
            return None
        return self.q_score_label.text(), self.q_score_label.toolTip()

    def q_score_result(self):
        """The open stock's Q-SCORE result as the app's controllers last gave it (the watchlist feed or the chart's
        score history), or None; the stock screen weighs it against its own (stock_qscore.pick)."""
        if (not self._q_score or self.asset.currentData() != 'domestic_stock'
                or self._q_score[0] != self.symbol.text().strip()):
            return None
        return self._q_score[1]

    def request(self):
        asset = self.asset.currentData()
        exchange = (self.exchange.currentData() or "") if asset in ("overseas_stock", "domestic_future") else ""
        if asset == "overseas_stock":
            # A code typed without choosing a result still uses its listed exchange when known.
            from core.market.symbols import lookup
            listed = lookup(self.symbol.text())
            if listed is not None and lookup(self.symbol.text(), exchange) is None:
                exchange = listed.exchange
        return ChartRequest(Instrument(asset, self.symbol.text(), exchange),
                            self.interval.currentData(), self.bar_count.value(), adjusted=False)

    # Overseas name search (UI-16) -----------------------------------------
    def _search_mode(self):
        overseas = self.asset.currentData() == "overseas_stock"
        self.symbol.setPlaceholderText(self._text("이름이나 코드로 검색 · 예: 애플, TSLA", "Search by name or code · e.g. Apple, TSLA")
                                       if overseas else "")
        self.form_labels[1].setText(self._text("종목 검색", "Search instrument") if overseas else self._text("종목 코드", "Instrument code"))
        if not overseas:
            self.symbol_suggestions.hide()

    def _symbol_typed(self, text):
        if self._choosing_symbol or self.asset.currentData() != "overseas_stock":
            self.symbol_suggestions.hide()
            return
        from core.market.symbols import search
        found = search(text, 8)
        current = (self.symbol.text().strip().upper(), self.exchange.currentData())
        if len(found) == 1 and (found[0].code, found[0].exchange) == current:
            found = ()  # already chosen
        self.symbol_suggestions.clear()
        for entry in found:
            item = QListWidgetItem(entry.label(self.ctx.language))
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.symbol_suggestions.addItem(item)
        if found:
            self.symbol_suggestions.setCurrentRow(0)
            rows = sum(self.symbol_suggestions.sizeHintForRow(i) for i in range(len(found)))
            self.symbol_suggestions.setFixedHeight(rows + 2 * self.symbol_suggestions.frameWidth() + 6)
        self._show(self.symbol_suggestions, bool(found))  # filled but never shown on the stock screen

    def suggestion_codes(self):
        return tuple((self.symbol_suggestions.item(i).data(Qt.ItemDataRole.UserRole).code,
                      self.symbol_suggestions.item(i).data(Qt.ItemDataRole.UserRole).exchange)
                     for i in range(self.symbol_suggestions.count()))

    def choose_symbol(self, entry):
        """Set code and exchange from a search result and load it immediately."""
        self._choosing_symbol = True
        try:
            self.exchange.setCurrentIndex(self.exchange.findData(entry.exchange))
            self.symbol.setText(entry.code)
        finally:
            self._choosing_symbol = False
        self.symbol_suggestions.hide()
        self.refresh(manual=True)

    def _symbol_chosen(self, item):
        if item is not None:
            self.choose_symbol(item.data(Qt.ItemDataRole.UserRole))

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        key = event.key()
        if watched is self.symbol and self.symbol_suggestions.isVisible():
            if key == Qt.Key.Key_Down:
                self.symbol_suggestions.setFocus()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._symbol_chosen(self.symbol_suggestions.currentItem() or self.symbol_suggestions.item(0))
                return True
            if key == Qt.Key.Key_Escape:
                self.symbol_suggestions.hide()
                return True
        elif watched is self.symbol_suggestions and (
                key == Qt.Key.Key_Escape or (key == Qt.Key.Key_Up and self.symbol_suggestions.currentRow() <= 0)):
            if key == Qt.Key.Key_Escape:
                self.symbol_suggestions.hide()
            self.symbol.setFocus()
            return True
        return False

    def _zoom_target(self, steps):
        """(n, bars shown now, bars shown after `steps` zoom steps): each step in shows 0.8 times the bars, each step
        out 1.25 times, never fewer than 20 nor more than were loaded."""
        n = len(self.snapshot.candles) if self.snapshot else 0
        current = min(self.visible_bars.value(), n)
        target = max(min(20, n), min(n, round(current * (0.8 ** steps))))
        return n, current, target

    def zoom(self, steps):
        """Zoom `steps` steps (positive: in) keeping the window's last bar; returns False at a limit."""
        n, current, target = self._zoom_target(steps)
        if n < 2 or target == current:
            return False
        if self._end is not None and target > self._end + 1:
            end = min(n - 1, target - 1)
            self._end = None if end >= n - 1 else end
        self.period_view = False
        self.visible_bars.setValue(target)
        return True

    def zoom_at(self, steps, x):
        """Owner R-D12-1: Ctrl + wheel (one notch one step, wheel up in) zooms on the bar under the pointer at chart
        x, which stays under the pointer and becomes the selected candle; near the first or the latest bar the
        window stops at that end. Returns False at a limit (nothing changes)."""
        layout = self.chart.layout_info
        n, current, target = self._zoom_target(steps)
        if n < 2 or target == current:
            return False
        if layout is None or layout.stop <= layout.start or layout.plot_right <= layout.plot_left:
            return self.zoom(steps)
        bar = layout.index_at(x)
        step = (layout.plot_right - layout.plot_left) / target   # the bar width after the zoom (detail_svg.render)
        slot = max(0, min(target - 1, int((float(x) - layout.plot_left) // step)))
        start = max(0, min(n - target, bar - slot))
        end = start + target - 1
        self._end = None if end >= n - 1 else end
        self._cursor = bar
        self.period_view = False
        self.visible_bars.setValue(target)
        return True

    def _clock(self, text):
        """A provider timestamp as concise Korea time; date-only values stay dates."""
        from zoneinfo import ZoneInfo
        try:
            at = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return str(text)
        if at.tzinfo is None:
            return str(text)[:10] if len(str(text)) <= 10 else at.strftime("%m-%d %H:%M:%S")
        return at.astimezone(ZoneInfo("Asia/Seoul")).strftime("%m-%d %H:%M:%S")

    def _delay_text(self, snapshot):
        instrument = snapshot.request.instrument
        if not self._from_kis(snapshot):
            return self._text("지연 시세", "delayed")
        if instrument.asset == "overseas_stock":
            return (self._text("미국 무료 시세 · 지연 0분", "US free feed · 0-minute delay")
                    if instrument.exchange in ("NAS", "NYS", "AMS") else self._text("15분 지연", "15-minute delay"))
        if instrument.asset == "bond":
            return self._text("일별 시세", "daily prices")
        if instrument.asset == "overseas_future":
            return self._text("해외선물 시세", "overseas futures quotes")
        return self._text("국내 실시간 시세", "domestic real-time")

    def set_asset_class(self, asset):
        """Called by the Markets asset-class tabs; changing class stops updates like any input change."""
        index = self.asset.findData(asset)
        if index < 0:
            raise ValueError("Unsupported asset class")
        if index != self.asset.currentIndex():
            self.asset.setCurrentIndex(index)

    def _asset_changed(self, *_):
        asset = self.asset.currentData()
        self._configure_exchange()
        example = next(row[3] for row in _ASSETS if row[0] == asset)
        self.symbol.blockSignals(True)
        self.symbol.setText(example)
        self.symbol.blockSignals(False)
        self._configure_intervals()
        self._inputs_changed()

    def _configure_exchange(self):
        asset = self.asset.currentData()
        self.exchange.blockSignals(True)
        self.exchange.clear()
        if asset == "overseas_stock":
            for exchange in _EXCHANGES:
                self.exchange.addItem(exchange, exchange)
        elif asset == "domestic_future":
            self.exchange.addItem(self._text("자동 · 지수선물", "Auto · index future"), "")
            for division in ("F", "O", "JF", "JO", "CF", "CM", "EU"):
                self.exchange.addItem(division, division)
        else:
            self.exchange.addItem("—", "")
        self.exchange.setEnabled(asset in ("overseas_stock", "domestic_future"))
        self.exchange.blockSignals(False)
        self.exchange.setVisible(asset == "domestic_future")
        self.form_labels[2].setVisible(asset == "domestic_future")
        self._form.setColumnStretch(0, 2 if asset == "domestic_future" else 0)
        self._search_mode()

    def _configure_intervals(self):
        from data.kis_workspace import supported_intervals
        try:
            instrument = Instrument(self.asset.currentData(), self.symbol.text(),
                                    self.exchange.currentData() or "")
            from core.market.detail_model import with_derived
            supported = with_derived(supported_intervals(instrument, paper=self._paper()))
            if self.detail:
                # The stock screen offers only what a ready provider can deliver (KIS, else Yahoo daily).
                from core.market.detail_model import routable_intervals
                routable = routable_intervals(self.router, instrument, paper=self._paper(), supported=supported)
                supported = routable or supported
        except ValueError:
            supported = INTERVALS
        self.interval.blockSignals(True)
        for index in range(self.interval.count()):
            self.interval.model().item(index).setEnabled(self.interval.itemData(index) in supported)
        if self.interval.currentData() not in supported:
            self.interval.setCurrentIndex(self.interval.findData("1d"))
        self.interval.blockSignals(False)

    def _inputs_changed(self, *_):
        resume = self._auto_updates or self._restart_pending
        self.stop()
        self._configure_intervals()
        self.snapshot = None
        self._q_score = None
        self._stream_gap = False
        self._last_request = None
        self._attempts = ()
        self._last_received = ""
        self._last_tick_received = ""
        self._cursor = 0
        self._end = None
        self.chart.set_snapshot(None)
        self.quote.clear()
        self.quote_detail.clear()
        self.q_score_label.hide()
        self.provenance.clear()
        self.times.clear()
        self.note.clear()
        self.reading.clear()
        self.indicator_reading.clear()
        self.cursor_slider.setEnabled(False)
        self._mode = "idle"
        self._status_detail = ""
        try:
            self.availability.setText(self._availability_text(self.request().instrument))
        except ValueError:
            self.availability.clear()
        self._busy(self.jobs.busy)
        self.render()
        if resume:
            self._restart_pending = True
            self.input_timer.start()

    def refresh(self, *, manual=False, for_stream=False, automatic=False):
        if self.jobs.busy:
            return False
        self.input_timer.stop()
        self.resync_timer.stop()
        self._restart_pending = False
        self._pending_stream_epoch = None
        if manual or for_stream:
            self._stop_stream()
        try:
            request = self.request()
        except (TypeError, ValueError):
            self._mode = "error"
            self._status_detail = self._text("종목 코드와 거래소를 확인하세요.", "Check the instrument code and exchange.")
            self._render_status()
            return False
        auto = manual or for_stream
        if auto:
            if not automatic:
                self._resync_attempted = False
            self._auto_updates = True
            self.poll_timer.stop()
            self.poll_button.blockSignals(True)
            self.poll_button.setChecked(False)
            self.poll_button.blockSignals(False)
        for_stream = auto and self._can_stream(request)
        self._epoch += 1
        epoch = self._epoch
        self._job_epoch = epoch
        self._pending_stream_epoch = epoch if for_stream else None
        self._last_request = request
        self._mode = "loading"
        self._status_detail = self._text("실시간 연결 전 차트 동기화", "Synchronizing history before live connection") if for_stream else ""
        self._render_status()
        # Attempts travel with the result: the router runs one job at a time on this pane's Jobs.
        router = self.router
        from core.market.detail_model import load_chart   # the yearly interval is built from the monthly history
        def preview(snapshot):
            self.bridge.history.emit(epoch, request, snapshot)
        return self.jobs.start(lambda: (epoch, request, load_chart(router, request, on_snapshot=preview),
                                       tuple(router.last_attempts)))

    @pyqtSlot(int, object, object)
    def _history_preview(self, epoch, request, snapshot):
        """Paint received history while paging continues; no live connection or score publication yet."""
        if epoch != self._epoch or request != self.request() or snapshot.request != request or not snapshot.candles:
            return
        selected = self._selected_timestamp()
        self.snapshot = snapshot
        self._restore_cursor(selected)
        self._last_received = snapshot.fetched_at
        if selected is None and self.period and self.period_view:
            from core.market.detail_model import visible_for
            self.visible_bars.blockSignals(True)
            self.visible_bars.setValue(max(self.visible_bars.minimum(), visible_for(self.period, snapshot.candles)))
            self.visible_bars.blockSignals(False)
        self._mode = "loading"
        self._status_detail = self._text("먼저 받은 차트를 표시하고 있어요 · 나머지 기간을 불러오는 중",
                                        "Showing received history · loading the remaining period")
        self.render()

    @pyqtSlot(object)
    def _loaded(self, result):
        epoch, request, snapshot, attempts = result
        if epoch != self._epoch or request != self.request():
            return
        self._attempts = attempts
        selected = self._selected_timestamp()
        auto_stream = self._pending_stream_epoch == epoch
        self._pending_stream_epoch = None
        self.snapshot = snapshot
        self._stream_gap = False
        self._last_received = snapshot.fetched_at
        self._restore_cursor(selected)
        if selected is None and self.period and self.period_view:
            from core.market.detail_model import visible_for
            self.visible_bars.blockSignals(True)
            self.visible_bars.setValue(max(self.visible_bars.minimum(), visible_for(self.period, snapshot.candles)))
            self.visible_bars.blockSignals(False)
        self._mode = "polling" if self.poll_timer.isActive() else "snapshot"
        self._status_detail = ""
        self.render()
        self.snapshot_loaded.emit(snapshot)
        if not self._from_kis(snapshot):
            # A fallback answer is a delayed snapshot: no KIS stream, no 5-second polling of it.
            self._auto_updates = False
            self.poll_timer.stop()
            self.poll_button.blockSignals(True)
            self.poll_button.setChecked(False)
            self.poll_button.blockSignals(False)
            self._mode = "snapshot"
            self._status_detail = self._text(f"{snapshot.source} 자료로 표시 · 자동 갱신 없음",
                                             f"Showing {snapshot.source} data · no automatic updates")
            self._render_status()
            self._busy(self.jobs.busy)
            return
        if auto_stream:
            self._subscribe(epoch, request)
        elif self._auto_updates:
            self.poll_timer.start()
            self.poll_button.blockSignals(True)
            self.poll_button.setChecked(True)
            self.poll_button.blockSignals(False)
            self._mode = "polling"
            self._status_detail = self._text("이 자산은 체결 스트림 미지원", "Trade streaming is unavailable for this asset")
            self._render_status()

    @staticmethod
    def _from_kis(snapshot):
        return str(getattr(snapshot, "source", "")).startswith("KIS")

    def _tried(self):
        from core.market.routing import describe
        return describe(self._attempts, self.ctx.language)

    @pyqtSlot(str)
    def _failed(self, code):
        if self._job_epoch != self._epoch:
            return
        self._pending_stream_epoch = None
        self._mode = "stale" if self.snapshot is not None else "error"
        # The failed job was the router's only job; its attempts belong to this request.
        self._attempts = tuple(getattr(self.router, "last_attempts", ()))
        if code == "ProvidersNotRun":
            code = "KISUnavailable"
        if code == "ProvidersUnavailable":
            self._status_detail = self._text("모든 공급사 조회 실패", "Every provider failed") + " · " + self._tried()
            if any(a.provider == "KIS" and (a.missing or a.reason == "KISUnavailable") for a in self._attempts):
                self._status_detail += self._text(
                    " · KIS를 쓰려면 QUANTGEN 폴더의 .env에 KIS_APP_KEY와 KIS_APP_SECRET을 설정하고 앱을 다시 실행하세요.",
                    " · To use KIS, set KIS_APP_KEY and KIS_APP_SECRET in the QUANTGEN folder's .env and restart.")
            self._render_status()
            return
        self._status_detail = (self._text(
            "KIS 앱키·시크릿을 찾지 못했습니다. QUANTGEN 폴더의 .env에 KIS_APP_KEY와 KIS_APP_SECRET을 설정한 뒤 앱을 다시 실행하세요. 시스템 → 데이터 연결에서 설정 여부를 확인할 수 있습니다.",
            "KIS app key or secret is missing. Set KIS_APP_KEY and KIS_APP_SECRET in the QUANTGEN folder's .env, then restart. Check their presence under System → Connections.")
            if code == 'KISUnavailable' else self._text("조회 실패", "Request failed") + f" ({code})")
        self._render_status()

    @pyqtSlot(bool)
    def _busy(self, busy):
        self.load_button.setEnabled(not busy)
        if getattr(self, "empty_retry", None) is not None:
            self.empty_retry.setEnabled(not busy)
        self.stream_button.setEnabled(not busy and self._stream is None)
        self.stop_button.setEnabled(busy or self._stream is not None or self.poll_timer.isActive())
        if not busy and self._restart_pending and not self.input_timer.isActive():
            self.input_timer.start()

    def _poll_toggled(self, enabled):
        from core.market.models import LIVE_INTERVALS
        if enabled and self.interval.currentData() in LIVE_INTERVALS:
            self.poll_button.blockSignals(True)
            self.poll_button.setChecked(False)
            self.poll_button.blockSignals(False)
            return
        self._auto_updates = False
        self._pending_stream_epoch = None
        self._stop_stream()
        if enabled:
            self.poll_timer.start()
            self.refresh()
        else:
            self.poll_timer.stop()
            self._mode = "snapshot" if self.snapshot else "idle"
            self._render_status()
        self._busy(self.jobs.busy)

    def start_stream(self):
        if self.jobs.busy:
            return
        try:
            request = self.request()
        except ValueError:
            return
        self.poll_button.blockSignals(True)
        self.poll_button.setChecked(False)
        self.poll_button.blockSignals(False)
        self.poll_timer.stop()
        # Every connection begins with authoritative history. A retained chart may
        # have spent hours hidden; a new trade cannot reconstruct that missing OHLC.
        self.refresh(for_stream=True)

    def _subscribe(self, epoch, request):
        if epoch != self._epoch or self.snapshot is None or request != self.request():
            return
        self._mode = "connecting"
        self._status_detail = ""
        self._last_tick_received = ""
        try:
            self._stream = self.stream_factory()
            self._stream.start(request.instrument,
                lambda tick: self.bridge.tick.emit(epoch, tick),
                lambda status: self.bridge.status.emit(epoch, str(status)))
        except Exception as exc:
            self._stop_stream()
            self._mode = "error"
            self._status_detail = self._text("실시간 연결 불가", "Stream unavailable") + f" ({type(exc).__name__})"
        self._busy(self.jobs.busy)
        self._render_status()

    @pyqtSlot(int, object)
    def _tick(self, epoch, tick):
        if epoch != self._epoch or self._stream is None or self.snapshot is None:
            return
        if self._stream_gap:
            # A reconnect cannot reconstruct the missing OHLC history from the next print.
            return
        if tick.instrument != self.snapshot.request.instrument:
            return
        from core.market.live import apply_tick
        selected = self._selected_timestamp()
        updated = apply_tick(self.snapshot, tick)
        if updated is self.snapshot:
            return
        self.snapshot = updated
        self._last_received = tick.received_at
        self._last_tick_received = tick.received_at
        self._restore_cursor(selected)
        self._mode = "streaming"
        self._status_detail = ""
        self.trade_received.emit(tick)
        if not self.paint_timer.isActive():
            self.paint_timer.start()

    @pyqtSlot(int, str)
    def _stream_status(self, epoch, status):
        if epoch != self._epoch or self._stream is None:
            return
        # Status strings are authored, credential-free values from KISStream.
        known = ("SUBSCRIBED", "LIVE", "connected", "subscribed", "streaming", "STOPPED", "CONNECTING", "RECONNECTING")
        self._status_detail = "" if status in known else status
        if status == "RECONNECTING":
            self._stream_gap = True
        if self._stream_gap:
            self._mode = "stale"
            self._status_detail = self._text("연결 공백 · 조회 / 새로고침 후 다시 연결하세요.",
                                             "Stream gap · load / refresh the chart before reconnecting.")
            if (self._auto_updates and not self._resync_attempted
                    and status in ("SUBSCRIBED", "LIVE", "connected", "subscribed", "streaming")):
                self._resync_attempted = True
                self.resync_timer.start()
                self._status_detail = self._text("연결이 돌아와 차트를 다시 맞추고 있어요.",
                                                 "Connection restored; resynchronizing the chart.")
        elif status.startswith("ERROR"):
            self._mode = "stale" if self.snapshot else "error"
        elif status == "STOPPED":
            self._mode = "stopped"
        elif status in ("SUBSCRIBED", "LIVE", "connected", "subscribed", "streaming"):
            self._mode = "streaming" if self._last_tick_received else "subscribed"
        else:
            self._mode = "connecting"
        self._render_status()
        self._busy(self.jobs.busy)

    def _stop_stream(self):
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()

    def stop(self):
        self._auto_updates = False
        self._restart_pending = False
        self.input_timer.stop()
        self.resync_timer.stop()
        self._epoch += 1
        self._pending_stream_epoch = None
        self.paint_timer.stop()
        self.poll_timer.stop()
        self.poll_button.blockSignals(True)
        self.poll_button.setChecked(False)
        self.poll_button.blockSignals(False)
        self._stop_stream()
        self._mode = "stale" if self._stream_gap and self.snapshot is not None else "stopped"
        self._status_detail = self._text("연결 공백 · 조회 / 새로고침 후 다시 연결하세요.",
            "Stream gap · load / refresh the chart before reconnecting.") if self._stream_gap else ""
        self._busy(self.jobs.busy)
        self._render_status()

    def _selected_timestamp(self):
        """None means follow the latest candle; a timestamp pins historical inspection."""
        if self.snapshot and self.snapshot.candles and 0 <= self._cursor < len(self.snapshot.candles) - 1:
            candle = self.snapshot.candles[self._cursor]
            return candle.timestamp, getattr(candle, "sequence", None)
        return None

    def _restore_cursor(self, timestamp):
        n = len(self.snapshot.candles)
        self._cursor = (next((i for i, c in enumerate(self.snapshot.candles) if (c.timestamp, getattr(c, "sequence", None)) == timestamp), 0)
                        if timestamp is not None else max(0, n - 1))
        if timestamp is not None:
            # A pinned candle stays in view: the window stops following new bars instead of growing.
            start, stop = self.window()
            if not start <= self._cursor < stop:
                visible = stop - start
                end = min(n - 1, self._cursor + visible - 1)
                self._end = None if end >= n - 1 else end
        elif self._end is not None and self._end >= n:
            self._end = None

    def _render_status(self):
        modes = {
            "idle": ("조회 대기", "Ready to load"), "loading": ("시세 조회 중", "Loading market data"),
            "snapshot": ("단일 조회", "Snapshot"), "polling": ("5초 주기 조회", "Polling every 5 seconds"),
            "connecting": ("체결 연결 / 재연결 중", "Connecting / reconnecting trade stream"),
            "subscribed": ("체결 구독 연결 · 첫 체결 대기", "Subscribed · waiting for the first trade"),
            "streaming": ("체결 스트림", "Trade stream"), "stale": ("오래된 값 · 조회 실패", "Stale · refresh failed"),
            "error": ("데이터 사용 불가", "Data unavailable"), "stopped": ("수신 중지", "Updates stopped"),
        }
        text = self._text(*modes.get(self._mode, modes["idle"]))
        if self._status_detail:
            text += " · " + self._status_detail
        if self._last_received:
            try:
                at = datetime.fromisoformat(self._last_received.replace("Z", "+00:00"))
                if at.tzinfo is not None:
                    seconds = max(0, round((datetime.now(timezone.utc) - at).total_seconds()))
                    text += self._text(f" · 마지막 수신 {seconds}초 전", f" · last received {seconds}s ago")
            except (ValueError, TypeError):
                pass
        # Connection heartbeats don't establish that market observations are fresh.
        if self._mode == "streaming" and self.snapshot and self.snapshot.last_tick_at:
            try:
                observed = datetime.fromisoformat(self.snapshot.last_tick_at.replace("Z", "+00:00"))
                age = max(0, round((datetime.now(timezone.utc) - observed).total_seconds()))
                if age > 60:
                    text += self._text(f" · 지연·오래된 체결: {age}초 전 관측", f" · delayed / stale trade: observed {age}s ago")
                elif self._last_tick_received:
                    received = datetime.fromisoformat(self._last_tick_received.replace("Z", "+00:00"))
                    gap = max(0, round((datetime.now(timezone.utc) - received).total_seconds()))
                    if gap > 15:
                        text += self._text(f" · 최근 {gap}초간 새 체결 없음", f" · no new trade for {gap}s")
            except (ValueError, TypeError):
                pass
        self.status.setText(text)
        self._render_empty()
        if self._emitted_mode != self._mode:
            self._emitted_mode = self._mode
            self.feed_state_changed.emit(self._mode)

    def _render_empty(self):
        """The centred text when there is no candle to draw, kept in step with the feed mode: refresh() and
        _failed() change the mode without a full render, so this also runs from _render_status. On the stock
        screen a failed load adds a retry button and what was tried (spec 10)."""
        if getattr(self, "empty_actions", None) is None:
            return
        from core.market.models import LIVE_INTERVALS
        has_candles = bool(self.snapshot and self.snapshot.candles)
        live_only = self.interval.currentData() in LIVE_INTERVALS
        waiting = self.snapshot is not None and live_only
        hint = getattr(self, "empty_hint", None)
        failed = self.detail and not has_candles and self._mode in ("error", "stale") and not waiting
        if not has_candles and self.detail and hint is not None:
            self.empty_state.setText(hint(self._mode, waiting))
        elif not has_candles:
            self.empty_state.setText(self._text(
                "연결 이후의 첫 체결을 기다리고 있어요. 체결이 도착하면 틱·초 단위 캔들이 차례로 그려집니다. 장이 닫혀 있거나 거래가 없으면 기다릴 수 있어요." if waiting else
                "종목과 시간 단위를 고른 뒤 ‘조회 / 새로고침’을 누르세요. 지원되는 종목은 체결 연결과 갱신까지 자동으로 시작합니다. 지표는 지금 선택해도 좋아요.",
                "Waiting for the first received trade. Tick/second candles grow as trades arrive; a closed or quiet market may take time." if waiting else
                "Choose an instrument and interval, then Load / refresh. Supported instruments connect and update automatically. You can select indicators now."))
        if self.detail:
            self.empty_state.setAlignment((Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom) if failed
                                          else Qt.AlignmentFlag.AlignCenter)
        self.empty_retry.setText(self._text("다시 시도", "Try again"))
        self.empty_retry.setEnabled(not self.jobs.busy)
        from .stock_detail_style import polite
        self.empty_tried.setText(polite(self._status_detail, self.ctx.language) if failed else "")
        self.empty_tried.setVisible(failed and bool(self._status_detail))
        self.empty_actions.setVisible(failed)

    def move_cursor(self, value):
        if self.snapshot is None or not self.snapshot.candles:
            return
        n = len(self.snapshot.candles)
        self._cursor = max(0, min(n - 1, value))
        # Owner 2026-11-11: past the window's edge the window pans with the selected candle; the zoom is kept.
        start, stop = self.window()
        visible = stop - start
        if self._cursor < start:
            end = self._cursor + visible - 1
            self._end = None if end >= n - 1 else end
            self.period_view = False
        elif self._cursor >= stop:
            self._end = None if self._cursor >= n - 1 else self._cursor
            self.period_view = False
        self.render()

    def render(self, *_):
        try:
            self._render()
        finally:
            self.rendered.emit()

    def _render(self):
        self._render_status()
        self._render_q_score()
        from core.market.models import LIVE_INTERVALS
        from core.market.presentation import indicator_colors, readout, indicator_series, number
        from core.theme import DARK
        dark = getattr(self.window(), "colors", None) == DARK
        selected = tuple(key for key, button in self.indicator_boxes.items() if button.isChecked())
        drawn = self.selected_indicators() if self.detail else selected
        colors = indicator_colors(dark)
        for key, button in self.indicator_boxes.items():
            swatch = QPixmap(8, 8)
            swatch.fill(QColor(colors[key]))
            button.setIcon(QIcon(swatch))
            button.setIconSize(QSize(8, 8))
        self.indicator_help.setText("\n".join(self._indicator_explanation(key) for key in selected))
        self._show(self.indicator_help, bool(selected))
        self._show(self.indicator_reading, bool(selected))
        live_only = self.interval.currentData() in LIVE_INTERVALS
        notices = []
        if self.snapshot is not None and not self._from_kis(self.snapshot):
            notices.append(self._text(f"KIS 대신 {self.snapshot.source} 자료입니다(지연·수정 전 가격). 시도: ",
                                      f"{self.snapshot.source} data instead of KIS (delayed, unadjusted). Tried: ")
                           + self._tried())
        if self.asset.currentData() == "overseas_stock" and self.snapshot is None:
            notices.append(self._text("미국 무료 Nasdaq 시장센터 시세 · 0분 지연 · 유료 통합 시세와 다를 수 있어요.",
                                      "US free Nasdaq market-center feed · 0-minute delay · may differ from paid consolidated feeds.")
                           if self.exchange.currentData() in ("NAS", "NYS", "AMS") else self._text(
                                      "해외 무료 시세 · 15분 지연", "Free overseas feed · 15-minute delay"))
        if live_only:
            notices.append(self._text("틱·초 단위는 연결 이후 받은 체결만 표시해요. 첫 캔들·현재 캔들은 부분 구간이며 거래량은 받은 체결의 합계입니다.",
                                      "Tick/second bars use received trades from connection onward. First/current bars may be partial; volume is the received trade total."))
            if self.snapshot and self.snapshot.candles and self.interval.currentData().endswith("tick"):
                candle = self.snapshot.candles[-1]
                target = int(self.interval.currentData()[:-4])
                notices.append(self._text(f"현재 캔들 · 수신 체결 {candle.trade_count or 0}/{target}회",
                                          f"Current candle · {candle.trade_count or 0}/{target} received trades"))
        if self.snapshot and "Live gap" in self.snapshot.note:
            notices.append(self._text("체결 공백이 있어 일부 구간이 불완전합니다. 조회 / 새로고침으로 다시 연결하세요.",
                                      "Some trades were missed; affected candles are incomplete. Load / refresh to reconnect."))
        # Spec 4.3: "전체" asks for more months than almost any stock has, so its partial-history notice is
        # suppressed; the data note keeps the count (the stock screen's ⓘ).
        if self.snapshot and "Partial history:" in self.snapshot.note and not (self.detail and self.period == "ALL") \
                and self.snapshot.request.interval != "1Y":
            from core.education.study_guide import unit_count
            interval, limit = self.snapshot.request.interval, self.snapshot.request.limit
            received = len(self.snapshot.candles)
            notices.append(self._text(f"요청한 {unit_count(interval, limit)} 중 {unit_count(interval, received)}만 받았어요.",
                                      f"Received {received} of {limit} requested bars."))
        notice = ("  ·  " if self.detail else "\n").join(notices)
        if self.detail and self.ctx.language == "ko":
            from .stock_detail_style import polite
            notice = polite(notice)   # the stock screen speaks 해요체 (owner wording rule, UI-D8 spec 6)
        self.feed_notice.setText(notice)
        self.feed_notice.setVisible(bool(notices))
        self.poll_button.setEnabled(not live_only)
        self.bar_count.setToolTip(self._text("틱·초 단위는 수신한 캔들의 보관 개수입니다.", "For tick/second charts, this limits retained received bars."))
        has_candles = bool(self.snapshot and self.snapshot.candles)
        self.empty_state.setVisible(not has_candles)
        self.chart.setVisible(has_candles)
        self._show(self.cursor_slider, has_candles)
        self._render_empty()
        if self.snapshot is None:
            return
        snapshot = self.snapshot
        q = snapshot.quote
        if q is not None:
            unit = self._text("계약 시세 단위", "contract quote units") if q.instrument.asset == "domestic_future" else q.currency
            self.quote.setText(f"{number(q.price)} {unit}")
            self.quote_detail.setText(f"{q.instrument.symbol} · {number(q.change)} ({number(q.change_pct)}%)")
        delay = self._delay_text(snapshot)
        realtime = self._from_kis(snapshot) and snapshot.request.instrument.asset in ("domestic_stock", "domestic_future")
        self.provenance.setText("" if realtime else delay)
        self._show(self.provenance, not realtime)
        self.times.setText(self._text("조회", "Fetched") + f" {self._clock(snapshot.fetched_at)}"
            + (" · " + self._text("체결", "Market") + f" {self._clock(q.market_time)}" if q and q.market_time else "")
            + self._text(" (한국시간)", " (Korea time)"))
        source_tip = self._text("출처", "Source") + f": {snapshot.source} · {delay}\n{self.times.text()}"
        self.quote.setToolTip(source_tip)
        self.quote_detail.setToolTip(source_tip)
        self.availability.setText(self._availability_text(snapshot.request.instrument) if self._from_kis(snapshot) else '')
        self.note.setText(" · ".join(dict.fromkeys(self._data_note(str(note), snapshot.request.instrument)
                                 for note in (snapshot.note, q.note if q else "") if note)))
        self.provenance.setToolTip(source_tip + ("\n" + self.note.text() if self.note.text() else ""))
        n = len(snapshot.candles)
        if not n:
            self.reading.clear()
            self.indicator_reading.setText(self._text("지표는 실제 수신한 캔들이 충분히 쌓인 뒤 표시돼요.", "Indicators appear once enough actual bars have arrived."))
            return
        start, stop = self.window()
        self._cursor = max(start, min(stop - 1, self._cursor))
        self.cursor_slider.blockSignals(True)
        self.cursor_slider.setRange(0, n - 1)
        self.cursor_slider.setValue(self._cursor)
        self.cursor_slider.setEnabled(True)
        self.cursor_slider.blockSignals(False)
        self.chart.set_snapshot(snapshot, self._cursor, visible_bars=self.visible_bars.value(),
                                indicators=drawn, dark=dark, language=self.ctx.language, end=self._end,
                                supply=self.supply if self.detail else None)
        self.reading.setText(readout(snapshot, self._cursor, language=self.ctx.language))
        self.chart.setAccessibleDescription(self.reading.text())
        if not self.detail:
            # The stock screen names its chart itself (how to move and zoom it: owner_ui_language 'chart_name').
            self.chart.setAccessibleName(self._text("캔들 차트", "Candlestick chart") + f" · {snapshot.source}")
        values = {key: data[self._cursor] for key, data in indicator_series(snapshot).items()}
        keys = {"sma": ("SMA20",), "ema": ("EMA12", "EMA26"), "bollinger": ("BB_UPPER", "BB_LOWER"),
                "rsi": ("RSI14",), "macd": ("MACD", "SIGNAL", "HISTOGRAM")}
        names = {"BB_UPPER": self._text("밴드 위", "Upper band"), "BB_LOWER": self._text("밴드 아래", "Lower band"),
                 "SIGNAL": self._text("신호선", "Signal"), "HISTOGRAM": self._text("막대", "Histogram")}
        self.indicator_reading.setText(" · ".join(f"{names.get(key, key)}: {number(values[key])}" for family in selected for key in keys[family]))
        self._busy(self.jobs.busy)

    def showEvent(self, event):
        super().showEvent(event)
        self.age_timer.start()

    def hideEvent(self, event):
        self.stop()
        self.age_timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop()
        self.age_timer.stop()
        super().closeEvent(event)
