"""Native KIS chart workspace; all data and chart calculations are shared with Flet."""
from __future__ import annotations

from datetime import datetime, timezone

from PyQt6.QtCore import QByteArray, QObject, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget)

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
_INTERVAL_NAMES = {"1m": "1분", "3m": "3분", "5m": "5분", "15m": "15분", "30m": "30분",
                   "60m": "60분", "1d": "일봉", "1w": "주봉", "1M": "월봉"}


class _StreamBridge(QObject):
    tick = pyqtSignal(int, object)
    status = pyqtSignal(int, str)


class MarketChartSvg(QSvgWidget):
    """The same SVG as the web view with native keyboard and pointer selection."""
    cursor_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.snapshot = None
        self.cursor = 0
        self.visible_bars = 120
        self.indicators = ("sma", "rsi", "macd")
        self.dark = False
        self.setMinimumWidth(260)
        self.setMinimumHeight(490)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def set_snapshot(self, snapshot, cursor=0, *, visible_bars=120, indicators=None, dark=False):
        self.snapshot, self.cursor = snapshot, cursor
        self.visible_bars, self.dark = visible_bars, dark
        if indicators is not None:
            self.indicators = tuple(indicators)
        self.redraw()

    def redraw(self):
        if self.snapshot is None:
            self.load(QByteArray())
            return
        from core.market.presentation import chart_svg
        svg = chart_svg(self.snapshot, indicators=self.indicators, cursor=self.cursor,
                        width=max(320, self.width()), dark=self.dark, visible=self.visible_bars)
        self.load(QByteArray(svg.encode("utf-8")))
        height = self.renderer().viewBoxF().height()
        if height > 0:
            self.setFixedHeight(round(height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.redraw()

    def mouseMoveEvent(self, event):
        if self.snapshot and self.snapshot.candles:
            n = len(self.snapshot.candles)
            visible = min(n, self.visible_bars)
            # Pointer selection is complemented by an exact, keyboard accessible slider.
            from core.market.presentation import plot_bounds
            left, right = plot_bounds(max(320, self.width()))
            fraction = max(0, min(1, (event.position().x() - left) / max(1, right - left)))
            self.cursor_changed.emit(n - visible + round(fraction * max(0, visible - 1)))
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if self.snapshot and self.snapshot.candles and event.key() in (
                Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End):
            n = len(self.snapshot.candles)
            target = (0 if event.key() == Qt.Key.Key_Home else n - 1 if event.key() == Qt.Key.Key_End
                      else self.cursor + (1 if event.key() == Qt.Key.Key_Right else -1))
            self.cursor_changed.emit(max(0, min(n - 1, target)))
            event.accept()
            return
        super().keyPressEvent(event)


class MarketChartPane(QWidget):
    """One bounded REST worker and one cancellable stream per visible chart pane."""
    snapshot_loaded = pyqtSignal(object)
    trade_received = pyqtSignal(object)
    feed_state_changed = pyqtSignal(str)

    def __init__(self, *, service=None, stream_factory=None, locale=None):
        super().__init__()
        if service is None:
            from data.kis_workspace import MarketDataService
            service = MarketDataService()
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
        self._pending_stream_epoch = None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        self.bridge = _StreamBridge(self)
        self.bridge.tick.connect(self._tick)
        self.bridge.status.connect(self._stream_status)
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
        layout.addWidget(self.intro)
        form = QGridLayout()
        for column, stretch in enumerate((2, 3, 2, 1, 1)):
            form.setColumnStretch(column, stretch)
        self.asset = QComboBox()
        self.asset.setMinimumWidth(145)
        for key, ko, en, code in _ASSETS:
            self.asset.addItem(ko, key)
        self.symbol = QLineEdit("005930")
        self.symbol.setMaxLength(32)
        self.exchange = QComboBox()
        self.exchange.setMinimumWidth(95)
        for exchange in _EXCHANGES:
            self.exchange.addItem(exchange, exchange)
        self.interval = QComboBox()
        for interval in INTERVALS:
            self.interval.addItem(_INTERVAL_NAMES[interval], interval)
        self.interval.setCurrentIndex(self.interval.findData("1d"))
        self.bar_count = QSpinBox()
        self.bar_count.setRange(20, 500)
        self.bar_count.setValue(120)
        self.form_labels = [self._label() for _ in range(5)]
        for column, (caption, control) in enumerate(zip(self.form_labels,
                (self.asset, self.symbol, self.exchange, self.interval, self.bar_count))):
            form.addWidget(caption, 0, column)
            form.addWidget(control, 1, column)
        layout.addLayout(form)
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
        for button in (self.load_button, self.poll_button, self.stream_button, self.stop_button):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.status = self._label()
        self.quote = self._label()
        self.q_score_label = self._label()
        self.q_score_label.hide()
        self.provenance = self._label()
        self.note = self._label()
        self.availability = self._label()
        for field in (self.status, self.quote, self.q_score_label, self.provenance, self.note, self.availability):
            layout.addWidget(field)
        display_row = QHBoxLayout()
        self.indicator_boxes = {}
        for key, name in (("sma", "SMA 20"), ("bollinger", "Bollinger 20 / 2σ"),
                          ("rsi", "RSI 14"), ("macd", "MACD 12/26/9")):
            box = QCheckBox(name)
            box.setChecked(True)
            box.toggled.connect(self.render)
            display_row.addWidget(box)
            self.indicator_boxes[key] = box
        self.zoom_label = self._label()
        display_row.addStretch()
        display_row.addWidget(self.zoom_label)
        self.visible_bars = QSpinBox()
        self.visible_bars.setRange(20, 500)
        self.visible_bars.setValue(120)
        self.visible_bars.valueChanged.connect(self.render)
        display_row.addWidget(self.visible_bars)
        layout.addLayout(display_row)
        self.empty_state = self._label()
        layout.addWidget(self.empty_state)
        self.chart = MarketChartSvg()
        self.chart.cursor_changed.connect(self.move_cursor)
        layout.addWidget(self.chart)
        self.cursor_slider = QSlider(Qt.Orientation.Horizontal)
        self.cursor_slider.valueChanged.connect(self.move_cursor)
        self.cursor_slider.setEnabled(False)
        layout.addWidget(self.cursor_slider)
        self.reading = self._label()
        layout.addWidget(self.reading)
        self.indicator_reading = self._label()
        layout.addWidget(self.indicator_reading)
        self.limitations = self._label()
        layout.addWidget(self.limitations)
        self.asset.currentIndexChanged.connect(self._asset_changed)
        for control in (self.symbol,):
            control.textChanged.connect(self._inputs_changed)
        for control in (self.exchange, self.interval):
            control.currentIndexChanged.connect(self._inputs_changed)
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

    def set_locale(self, ctx):
        self.ctx = ctx
        self.intro.setText(self._text("KIS 시세 · 일봉·분봉 캔들과 실시간 지표", "KIS market chart · daily / intraday candles and live indicators"))
        self.load_button.setText(self._text("조회 / 새로고침", "Load / refresh"))
        self.poll_button.setText(self._text("5초 주기 조회", "Poll every 5 seconds"))
        self.stream_button.setText(self._text("실시간 체결 연결", "Connect live trades"))
        self.stop_button.setText(self._text("수신 중지", "Stop updates"))
        self.zoom_label.setText(self._text("표시 봉 수", "Visible bars"))
        self.empty_state.setText(self._text(
            "종목과 봉 주기를 선택한 뒤 ‘실시간 체결 연결’을 누르면 과거 차트를 조회하고 체결 수신을 시작합니다. 일회 조회는 ‘조회 / 새로고침’을 사용하세요. KIS 앱키·시크릿 설정이 필요합니다.",
            "Choose an instrument and interval, then select Connect live trades to load history and start the stream. Use Load / refresh for a snapshot. A KIS app key and secret are required."))
        for label, ko, en in zip(self.form_labels,
                ("자산", "종목 코드", "거래소", "봉 주기", "조회 봉 수"),
                ("Asset", "Instrument code", "Exchange", "Interval", "History bars")):
            label.setText(self._text(ko, en))
        self.asset.blockSignals(True)
        for index, (_, ko, en, _) in enumerate(_ASSETS):
            self.asset.setItemText(index, self._text(ko, en))
        self.asset.blockSignals(False)
        self.interval.blockSignals(True)
        for index, interval in enumerate(INTERVALS):
            self.interval.setItemText(index, self._text(_INTERVAL_NAMES[interval], interval))
        self.interval.blockSignals(False)
        if self.asset.currentData() == "domestic_future" and self.exchange.count():
            self.exchange.setItemText(0, self._text("자동 · 지수선물", "Auto · index future"))
        for control, ko, en in ((self.asset,"자산 선택","Select asset"), (self.symbol,"종목 코드","Instrument code"),
                (self.exchange,"해외 거래소","Overseas exchange"), (self.interval,"차트 봉 주기","Chart interval"),
                (self.bar_count,"조회 봉 수","History bars"), (self.visible_bars,"표시 봉 수","Visible bars"),
                (self.cursor_slider,"캔들 선택 · 좌우 방향키","Select candle · left / right arrows")):
            control.setAccessibleName(self._text(ko, en))
        self.limitations.setText(self._text(
            "조회 주기와 실제 체결 수신은 다릅니다. 해외 시세는 거래소·이용 권한에 따라 지연될 수 있습니다. "
            "최근 봉과 지표는 체결에 따라 바뀌며, 지표의 표본이 부족하면 —로 표시합니다. 화면을 벗어나면 수신을 중지합니다.",
            "Polling and trade streaming have separate connection states. Overseas quotes may be delayed by exchange or entitlement. "
            "The latest candle and indicators change with new trades; insufficient history is shown as —. Updates stop when this pane is hidden."))
        self.render()

    def set_q_score(self, symbol, score):
        if symbol != self.symbol.text().strip() or self.asset.currentData() != 'domestic_stock':
            return
        self._q_score = (symbol, score)
        self._render_q_score()

    def _render_q_score(self):
        visible = bool(self.snapshot and self._q_score and
                       self.snapshot.request.instrument.asset == 'domestic_stock' and
                       self.snapshot.request.instrument.code == self._q_score[0])
        self.q_score_label.setVisible(visible)
        if visible:
            from .watchlist import _score_text, _score_tooltip
            score = self._q_score[1]
            self.q_score_label.setText('Q-SCORE · ' + _score_text(score, self.ctx))
            self.q_score_label.setToolTip(_score_tooltip(score, self.ctx))

    def request(self):
        asset = self.asset.currentData()
        exchange = (self.exchange.currentData() or "") if asset in ("overseas_stock", "domestic_future") else ""
        return ChartRequest(Instrument(asset, self.symbol.text(), exchange),
                            self.interval.currentData(), self.bar_count.value(), adjusted=False)

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

    def _configure_intervals(self):
        from data.kis_workspace import supported_intervals
        try:
            instrument = Instrument(self.asset.currentData(), self.symbol.text(),
                                    self.exchange.currentData() or "")
            supported = supported_intervals(instrument)
        except ValueError:
            supported = INTERVALS
        self.interval.blockSignals(True)
        for index in range(self.interval.count()):
            self.interval.model().item(index).setEnabled(self.interval.itemData(index) in supported)
        if self.interval.currentData() not in supported:
            self.interval.setCurrentIndex(self.interval.findData("1d"))
        self.interval.blockSignals(False)

    def _inputs_changed(self, *_):
        self.stop()
        self.snapshot = None
        self._q_score = None
        self._stream_gap = False
        self._last_request = None
        self._last_received = ""
        self._last_tick_received = ""
        self._cursor = 0
        self.chart.set_snapshot(None)
        self.quote.clear()
        self.q_score_label.hide()
        self.provenance.clear()
        self.note.clear()
        self.reading.clear()
        self.indicator_reading.clear()
        self.cursor_slider.setEnabled(False)
        self._mode = "idle"
        self._status_detail = ""
        from data.kis_workspace import availability_note
        try:
            self.availability.setText(availability_note(self.request().instrument))
        except ValueError:
            self.availability.clear()
        self._busy(self.jobs.busy)
        self.render()

    def refresh(self, *, manual=False, for_stream=False):
        if self.jobs.busy:
            return False
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
        self._epoch += 1
        epoch = self._epoch
        self._job_epoch = epoch
        self._pending_stream_epoch = epoch if for_stream else None
        self._last_request = request
        self._mode = "loading"
        self._status_detail = self._text("실시간 연결 전 차트 동기화", "Synchronizing history before live connection") if for_stream else ""
        self._render_status()
        return self.jobs.start(lambda: (epoch, request, self.service.load(request)))

    @pyqtSlot(object)
    def _loaded(self, result):
        epoch, request, snapshot = result
        if epoch != self._epoch or request != self.request():
            return
        selected = self._selected_timestamp()
        auto_stream = self._pending_stream_epoch == epoch
        self._pending_stream_epoch = None
        self.snapshot = snapshot
        self._stream_gap = False
        self._last_received = snapshot.fetched_at
        self._restore_cursor(selected)
        self._mode = "polling" if self.poll_timer.isActive() else "snapshot"
        self._status_detail = ""
        self.render()
        self.snapshot_loaded.emit(snapshot)
        if auto_stream:
            self._subscribe(epoch, request)

    @pyqtSlot(str)
    def _failed(self, code):
        if self._job_epoch != self._epoch:
            return
        self._pending_stream_epoch = None
        self._mode = "stale" if self.snapshot is not None else "error"
        self._status_detail = (self._text(
            "KIS 앱키·시크릿을 찾지 못했습니다. QUANTGEN 폴더의 .env에 KIS_APP_KEY와 KIS_APP_SECRET을 설정한 뒤 앱을 다시 실행하세요. 시스템 → 데이터 연결에서 설정 여부를 확인할 수 있습니다.",
            "KIS app key or secret is missing. Set KIS_APP_KEY and KIS_APP_SECRET in the QUANTGEN folder's .env, then restart. Check their presence under System → Connections.")
            if code == 'KISUnavailable' else self._text("조회 실패", "Request failed") + f" ({code})")
        self._render_status()

    @pyqtSlot(bool)
    def _busy(self, busy):
        self.load_button.setEnabled(not busy)
        self.stream_button.setEnabled(not busy and self._stream is None)
        self.stop_button.setEnabled(busy or self._stream is not None or self.poll_timer.isActive())

    def _poll_toggled(self, enabled):
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
        if self.jobs.busy or self._stream is not None:
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
        self._stream = self.stream_factory()
        try:
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
        self._status_detail = status
        if status == "RECONNECTING":
            self._stream_gap = True
        if self._stream_gap:
            self._mode = "stale"
            self._status_detail = self._text("연결 공백 · 조회 / 새로고침 후 다시 연결하세요.",
                                             "Stream gap · load / refresh the chart before reconnecting.")
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
            return self.snapshot.candles[self._cursor].timestamp
        return None

    def _restore_cursor(self, timestamp):
        n = len(self.snapshot.candles)
        self._cursor = (next((i for i, c in enumerate(self.snapshot.candles) if c.timestamp == timestamp), 0)
                        if timestamp is not None else max(0, n - 1))
        if n - self._cursor > self.visible_bars.value():
            self.visible_bars.blockSignals(True)
            self.visible_bars.setValue(n - self._cursor)
            self.visible_bars.blockSignals(False)

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
        if self._emitted_mode != self._mode:
            self._emitted_mode = self._mode
            self.feed_state_changed.emit(self._mode)

    def move_cursor(self, value):
        if self.snapshot is None or not self.snapshot.candles:
            return
        self._cursor = max(0, min(len(self.snapshot.candles) - 1, value))
        # Keep the selected candle visible when keyboard/slider selects older history.
        needed = len(self.snapshot.candles) - self._cursor
        if needed > self.visible_bars.value():
            self.visible_bars.blockSignals(True)
            self.visible_bars.setValue(needed)
            self.visible_bars.blockSignals(False)
        self.render()

    def render(self, *_):
        self._render_status()
        self._render_q_score()
        has_candles = bool(self.snapshot and self.snapshot.candles)
        self.empty_state.setVisible(not has_candles)
        self.chart.setVisible(has_candles)
        if self.snapshot is None:
            return
        from core.market.presentation import readout, indicator_values, number
        snapshot = self.snapshot
        n = len(snapshot.candles)
        if not n:
            return
        self._cursor = max(0, n - self.visible_bars.value(), min(n - 1, self._cursor))
        self.cursor_slider.blockSignals(True)
        self.cursor_slider.setRange(0, n - 1)
        self.cursor_slider.setValue(self._cursor)
        self.cursor_slider.setEnabled(True)
        self.cursor_slider.blockSignals(False)
        selected = tuple(key for key, box in self.indicator_boxes.items() if box.isChecked())
        dark = getattr(self.window(), "colors", None)
        from core.theme import DARK
        self.chart.set_snapshot(snapshot, self._cursor, visible_bars=self.visible_bars.value(),
                                indicators=selected, dark=dark == DARK)
        self.reading.setText(readout(snapshot, self._cursor))
        self.chart.setAccessibleDescription(self.reading.text())
        self.chart.setAccessibleName(self._text("KIS 캔들 차트", "KIS candlestick chart"))
        q = snapshot.quote
        if q is not None:
            unit = self._text("계약 시세 단위", "contract quote units") if q.instrument.asset == "domestic_future" else q.currency
            self.quote.setText(f"{q.instrument.symbol} · {number(q.price)} {unit} · Δ {number(q.change)} · {number(q.change_pct)}%")
        self.provenance.setText(self._text("출처", "Source") + f": {snapshot.source} · "
            + self._text("조회 시각", "Fetched") + f": {snapshot.fetched_at}"
            + (" · " + self._text("체결 시각", "Market time") + f": {q.market_time}" if q and q.market_time else ""))
        self.note.setText(" · ".join(str(note) for note in (snapshot.note, q.note if q else "") if note))
        values = indicator_values(snapshot)
        self.indicator_reading.setText(" · ".join(f"{key}: {'—' if value is None else f'{value:,.3f}'}" for key, value in values.items()))
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
