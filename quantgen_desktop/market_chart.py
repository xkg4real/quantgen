"""Native KIS chart workspace; all data and chart calculations are shared with Flet."""
from __future__ import annotations

from datetime import datetime, timezone

from PyQt6.QtCore import QByteArray, QObject, QTimer, Qt, QSize, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QIcon, QPixmap
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
                   "60m": "60분", "1d": "일봉", "1w": "주봉", "1M": "월봉",
                   "1tick": "1틱", "10tick": "10틱", "100tick": "100틱",
                   "1s": "1초", "5s": "5초", "10s": "10초", "30s": "30초"}


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
        self.indicators = ("sma",)
        self.dark = False
        self.language = "en"
        self.setMinimumWidth(260)
        self.setMinimumHeight(300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._propagate_chart_height)

    def set_snapshot(self, snapshot, cursor=0, *, visible_bars=120, indicators=None, dark=False, language="en"):
        self.snapshot, self.cursor = snapshot, cursor
        self.visible_bars, self.dark = visible_bars, dark
        self.language = language
        if indicators is not None:
            self.indicators = tuple(indicators)
        self.redraw()

    def redraw(self):
        if self.snapshot is None:
            self.load(QByteArray())
            return
        from core.market.presentation import chart_svg
        svg = chart_svg(self.snapshot, indicators=self.indicators, cursor=self.cursor,
                        width=max(320, self.width()), dark=self.dark, visible=self.visible_bars, language=self.language)
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
        self._auto_updates = False
        self._restart_pending = False
        self._resync_attempted = False
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
        self.bar_count.setValue(120)
        self.form_labels = [self._label() for _ in range(5)]
        for column, index in enumerate((0, 1, 3)):
            form.addWidget(self.form_labels[index], 0, column)
            form.addWidget((self.asset, self.symbol, self.exchange, self.interval, self.bar_count)[index], 1, column)
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
        self.provenance, self.note, self.availability = self._label(), self._label(), self._label()
        self.advanced = QWidget()
        advanced_layout = QVBoxLayout(self.advanced)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_form = QGridLayout()
        self.zoom_label = self._label()
        self.visible_bars = QSpinBox()
        self.visible_bars.setRange(20, 500)
        self.visible_bars.setValue(120)
        self.visible_bars.valueChanged.connect(self.render)
        for column, (caption, control) in enumerate(((self.form_labels[2], self.exchange),
                (self.form_labels[4], self.bar_count), (self.zoom_label, self.visible_bars))):
            advanced_form.addWidget(caption, 0, column)
            advanced_form.addWidget(control, 1, column)
        advanced_layout.addLayout(advanced_form)
        actions = QHBoxLayout()
        actions.addWidget(self.poll_button)
        actions.addWidget(self.stream_button)
        actions.addStretch()
        advanced_layout.addLayout(actions)
        for field in (self.provenance, self.note, self.availability):
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
        self.chart = MarketChartSvg()
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
            "sma": ("이동평균 · 최근 20개 봉의 평균 가격입니다. 가격 위·아래에서 흐름을 비교해 보세요. 변화에 늦게 반응할 수 있어요.",
                    "Moving average · Mean closing price of 20 bars. Compare price above or below the line to read the trend; it can lag."),
            "ema": ("지수이평 · 최근 가격에 더 무게를 둔 12·26개 봉의 평균입니다. 두 선의 방향과 간격을 보세요. 빠른 반응만큼 잘못된 전환 신호도 늘 수 있어요.",
                    "EMA · Averages over 12/26 bars give recent prices more weight. Compare the lines' direction and gap; faster response can mean more false turns."),
            "bollinger": ("볼린저 · 최근 20개 봉의 변동 폭을 보여줍니다. 밴드가 벌어지면 가격 변화가 커진 구간이에요. 경계에 닿아도 반전이 보장되지는 않아요.",
                          "Bollinger · Bands show price variation over 20 bars. Wider bands mean more variation; touching an edge does not guarantee a reversal."),
            "rsi": ("RSI · 최근 14개 봉의 상승·하락 강도를 0~100으로 비교합니다. 70·30선을 참고하되, 강한 흐름에서는 높거나 낮은 값이 오래 이어질 수 있어요.",
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
            "domestic_stock": "KRX 시장 · 마지막 봉은 아직 변할 수 있어요. 진행 중인 분봉 거래량은 공급자 값이 확정되기 전까지 표시하지 않습니다. 빈 시간에 가짜 봉을 만들지 않아요.",
            "domestic_future": "국내 선물·옵션 · 만기 종목과 일치하는 시장을 선택하세요. 가격은 포인트 등 계약별 시세 단위이며 일반 원화 현금 금액이 아닙니다. 마지막 봉은 변할 수 있어요.",
            "bond": "채권 이력은 최대 100개 일봉이며 과거 분봉 조회는 지원하지 않습니다. 가격은 액면 10,000원 기준입니다.",
            "overseas_future": "해외선물 가격은 검증된 종목 마스터의 가격 배율을 적용합니다. 공급자 시각 기준이 검증되지 않은 분봉은 제공하지 않습니다. CME·SGX 시세는 별도 이용 권한이 필요합니다.",
            "overseas_stock": ("미국 무료 Nasdaq 시장센터 시세 · 지연 0분. 유료 통합 시세와 거래 범위·가격이 다를 수 있어요. 과거 분봉은 정규장만 포함하며 시가는 다음 날 정정될 수 있습니다."
                               if instrument.exchange in ("NAS", "NYS", "AMS") else "해외 무료 시세 · 15분 지연. 과거 분봉은 정규장만 포함합니다."),
        }[instrument.asset]

    def _data_note(self, note, instrument):
        if self.ctx.language != "ko" or not note:
            return note
        import re
        from data.kis_workspace import availability_note
        note = note.replace(availability_note(instrument), self._availability_text(instrument))
        translations = {
            "Received executions only: tick/second bars begin when the stream connects. Historical tick/second bars are unavailable; gaps are not filled. The first/current bar can be partial; volume is received trade volume, not session volume.": "틱·초봉은 연결 이후 받은 체결만 모읍니다. 과거 틱·초봉은 제공하지 않으며 빈 구간을 채우지 않습니다. 첫 봉·현재 봉은 일부 체결만 포함할 수 있고, 거래량은 수신한 체결의 합계입니다.",
            "Current quote unavailable; waiting for a valid streaming execution.": "현재가 조회 불가 · 정상 체결 수신을 기다립니다.",
            "Clock-aligned aggregation of observed minute bars; missing minutes are not filled.": "관측된 분봉을 시각 구간에 맞춰 묶습니다. 없는 분봉은 채우지 않습니다.",
            "Live gap: some executions were not received; affected bars are partial. No missing trades are reconstructed.": "체결 공백 · 일부 체결을 받지 못해 해당 봉이 불완전합니다. 누락된 거래는 만들어 채우지 않습니다.",
            "Live gap: missing trades may affect OHLC and minute-bar volume. Reload history to reconcile.": "체결 공백 · 가격·분봉 거래량에 누락이 있을 수 있습니다. 다시 조회해 이력을 맞추세요.",
            "REST snapshot; quote timestamp convention unverified.": "시점 조회 · 시세 시각 기준 미검증.",
            "REST snapshot; market timestamp not provided.": "시점 조회 · 공급자가 시장 시각을 제공하지 않습니다.",
        }
        for original, translated in translations.items():
            note = note.replace(original, translated)
        return re.sub(r"Partial history: (\d+)/(\d+) requested bars \(provider window or paging limit\)\.",
                      r"부분 이력 · 요청한 \2개 중 \1개 봉만 조회됐습니다(공급자 조회 범위·페이지 한도).", note)

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
        self.advanced_button.setText(self._text("차트 설정 · 데이터", "Chart settings · data"))
        self.indicator_title.setText(self._text("기술지표", "Indicators"))
        self.guide_button.setText(self._text("차트 읽는 법 ?", "How to read this ?"))
        self.zoom_label.setText(self._text("표시 봉 수", "Visible bars"))
        self.chart_help.setText(self._text("봉 하나는 선택한 기간의 가격입니다. 아래 거래량은 거래된 수량이에요.",
                                         "Each candle shows prices over one interval. Volume below shows how much traded."))
        self.guide.setText(self._text(
            "봉의 몸통은 시작·마지막 가격, 위아래 꼬리는 최고·최저 가격입니다. 빨강은 시작보다 상승, 파랑은 하락을 뜻해요. "
            "마지막 봉은 체결마다 바뀔 수 있어요. 틱봉은 체결 횟수, 초·분봉은 시간을 기준으로 묶습니다. "
            "틱·초봉은 연결 이후 받은 체결부터 쌓이며 빈 시간을 가짜 봉으로 채우지 않아요. "
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
                ("자산", "종목 코드", "거래소", "봉 주기", "조회 봉 수"),
                ("Asset", "Instrument code", "Exchange", "Interval", "History bars")):
            label.setText(self._text(ko, en))
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
                (self.exchange,"해외 거래소","Overseas exchange"), (self.interval,"차트 봉 주기","Chart interval"),
                (self.bar_count,"조회 봉 수","History bars"), (self.visible_bars,"표시 봉 수","Visible bars"),
                (self.cursor_slider,"캔들 선택 · 좌우 방향키","Select candle · left / right arrows")):
            control.setAccessibleName(self._text(ko, en))
        self.limitations.setText(self._text(
            "체결 수신은 장 운영과 이용 권한에 따라 달라집니다. 해외 시세는 지연될 수 있어요. 지표 계산에 필요한 봉이 부족하면 —로 표시합니다. 화면을 벗어나면 수신을 멈춥니다.",
            "Trade delivery depends on market hours and access; overseas data may be delayed. Indicators show — until enough bars arrive. Updates stop when you leave this screen."))
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
            supported = supported_intervals(instrument, paper=self._paper())
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
        self._last_received = ""
        self._last_tick_received = ""
        self._cursor = 0
        self.chart.set_snapshot(None)
        self.quote.clear()
        self.quote_detail.clear()
        self.q_score_label.hide()
        self.provenance.clear()
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
        elif self._auto_updates:
            self.poll_timer.start()
            self.poll_button.blockSignals(True)
            self.poll_button.setChecked(True)
            self.poll_button.blockSignals(False)
            self._mode = "polling"
            self._status_detail = self._text("이 자산은 체결 스트림 미지원", "Trade streaming is unavailable for this asset")
            self._render_status()

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
        from core.market.models import LIVE_INTERVALS
        from core.market.presentation import indicator_colors, readout, indicator_series, number
        from core.theme import DARK
        dark = getattr(self.window(), "colors", None) == DARK
        selected = tuple(key for key, button in self.indicator_boxes.items() if button.isChecked())
        colors = indicator_colors(dark)
        for key, button in self.indicator_boxes.items():
            swatch = QPixmap(8, 8)
            swatch.fill(QColor(colors[key]))
            button.setIcon(QIcon(swatch))
            button.setIconSize(QSize(8, 8))
        self.indicator_help.setText("\n".join(self._indicator_explanation(key) for key in selected))
        self.indicator_help.setVisible(bool(selected))
        self.indicator_reading.setVisible(bool(selected))
        live_only = self.interval.currentData() in LIVE_INTERVALS
        notices = []
        if self.asset.currentData() == "overseas_stock":
            notices.append(self._text("미국 무료 Nasdaq 시장센터 시세 · 0분 지연 · 유료 통합 시세와 다를 수 있어요.",
                                      "US free Nasdaq market-center feed · 0-minute delay · may differ from paid consolidated feeds.")
                           if self.exchange.currentData() in ("NAS", "NYS", "AMS") else self._text(
                                      "해외 무료 시세 · 15분 지연", "Free overseas feed · 15-minute delay"))
        if live_only:
            notices.append(self._text("틱·초봉은 연결 이후 받은 체결만 표시해요. 첫 봉·현재 봉은 부분 구간이며 거래량은 받은 체결의 합계입니다.",
                                      "Tick/second bars use received trades from connection onward. First/current bars may be partial; volume is the received trade total."))
            if self.snapshot and self.snapshot.candles and self.interval.currentData().endswith("tick"):
                candle = self.snapshot.candles[-1]
                target = int(self.interval.currentData()[:-4])
                notices.append(self._text(f"현재 봉 · 수신 체결 {candle.trade_count or 0}/{target}회",
                                          f"Current candle · {candle.trade_count or 0}/{target} received trades"))
        if self.snapshot and "Live gap" in self.snapshot.note:
            notices.append(self._text("체결 공백이 있어 일부 봉이 불완전합니다. 조회 / 새로고침으로 다시 연결하세요.",
                                      "Some trades were missed; affected candles are incomplete. Load / refresh to reconnect."))
        if self.snapshot and "Partial history:" in self.snapshot.note:
            notices.append(self._text(f"요청한 {self.snapshot.request.limit}개 중 {len(self.snapshot.candles)}개 봉을 받았어요.",
                                      f"Received {len(self.snapshot.candles)} of {self.snapshot.request.limit} requested bars."))
        self.feed_notice.setText("\n".join(notices))
        self.feed_notice.setVisible(bool(notices))
        self.poll_button.setEnabled(not live_only)
        self.bar_count.setToolTip(self._text("틱·초봉은 수신한 봉의 보관 개수입니다.", "For tick/second charts, this limits retained received bars."))
        has_candles = bool(self.snapshot and self.snapshot.candles)
        self.empty_state.setVisible(not has_candles)
        self.chart.setVisible(has_candles)
        self.cursor_slider.setVisible(has_candles)
        if not has_candles:
            waiting = self.snapshot is not None and live_only
            self.empty_state.setText(self._text(
                "연결 이후의 첫 체결을 기다리고 있어요. 체결이 도착하면 틱·초봉이 차례로 그려집니다. 장이 닫혀 있거나 거래가 없으면 기다릴 수 있어요." if waiting else
                "종목과 봉 주기를 고른 뒤 ‘조회 / 새로고침’을 누르세요. 지원되는 종목은 체결 연결과 갱신까지 자동으로 시작합니다. 지표는 지금 선택해도 좋아요.",
                "Waiting for the first received trade. Tick/second candles grow as trades arrive; a closed or quiet market may take time." if waiting else
                "Choose an instrument and interval, then Load / refresh. Supported instruments connect and update automatically. You can select indicators now."))
        if self.snapshot is None:
            return
        snapshot = self.snapshot
        q = snapshot.quote
        if q is not None:
            unit = self._text("계약 시세 단위", "contract quote units") if q.instrument.asset == "domestic_future" else q.currency
            self.quote.setText(f"{number(q.price)} {unit}")
            self.quote_detail.setText(f"{q.instrument.symbol} · {number(q.change)} ({number(q.change_pct)}%)")
        self.provenance.setText(self._text("출처", "Source") + f": {snapshot.source} · "
            + self._text("조회 시각", "Fetched") + f": {snapshot.fetched_at}"
            + (" · " + self._text("체결 시각", "Market time") + f": {q.market_time}" if q and q.market_time else ""))
        self.availability.setText(self._availability_text(snapshot.request.instrument))
        self.note.setText(" · ".join(dict.fromkeys(self._data_note(str(note), snapshot.request.instrument)
                                 for note in (snapshot.note, q.note if q else "") if note)))
        n = len(snapshot.candles)
        if not n:
            self.reading.clear()
            self.indicator_reading.setText(self._text("지표는 실제 수신한 봉이 충분히 쌓인 뒤 표시돼요.", "Indicators appear once enough actual bars have arrived."))
            return
        self._cursor = max(0, n - self.visible_bars.value(), min(n - 1, self._cursor))
        self.cursor_slider.blockSignals(True)
        self.cursor_slider.setRange(0, n - 1)
        self.cursor_slider.setValue(self._cursor)
        self.cursor_slider.setEnabled(True)
        self.cursor_slider.blockSignals(False)
        self.chart.set_snapshot(snapshot, self._cursor, visible_bars=self.visible_bars.value(),
                                indicators=selected, dark=dark, language=self.ctx.language)
        self.reading.setText(readout(snapshot, self._cursor, language=self.ctx.language))
        self.chart.setAccessibleDescription(self.reading.text())
        self.chart.setAccessibleName(self._text("KIS 캔들 차트", "KIS candlestick chart"))
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
