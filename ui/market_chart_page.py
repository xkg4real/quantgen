"""Session-owned KIS chart view; brokerage credentials remain in Python.

REST jobs and stream callbacks carry a generation so late work cannot repaint a
different symbol. Navigation/disconnect cancels polling and closes the stream.
"""
from __future__ import annotations

import asyncio
import base64
from collections import deque
from datetime import datetime
import math
import re
import threading
import time

import flet as ft

from core.i18n import LocaleContext
from core.market.models import ChartRequest, Instrument
from core.theme import RADII, active
from ui.components import card


ASSET_LABELS = (
    ("domestic_stock", "국내주식 · ETF", "KR stocks · ETF"),
    ("overseas_stock", "해외주식", "Overseas stocks"),
    ("domestic_future", "국내선물옵션", "KR futures/options"),
    ("overseas_future", "해외선물", "Overseas futures"),
    ("bond", "장내채권", "Exchange-traded bonds"),
)
TIMEFRAMES = (("1m", "1분", "1 minute"), ("3m", "3분", "3 minutes"),
              ("5m", "5분", "5 minutes"), ("15m", "15분", "15 minutes"),
              ("30m", "30분", "30 minutes"), ("60m", "60분", "60 minutes"),
              ("1d", "일봉", "Daily"), ("1w", "주봉", "Weekly"), ("1M", "월봉", "Monthly"))
DEFAULT_CODES = {"domestic_stock": "005930", "overseas_stock": "AAPL",
                 "domestic_future": "", "overseas_future": "", "bond": ""}
# Indicator readings under the quote: (key in indicator_values, ko label, en label, ko tip, en tip).
METRICS = (
    ("SMA20", "SMA20", "SMA20", "최근 20개 봉 종가의 단순 평균", "Simple average of the last 20 closes"),
    ("RSI14", "RSI14", "RSI14", "14개 봉 상대강도지수 (0–100)", "14-bar relative strength index (0–100)"),
    ("MACD", "MACD", "MACD", "12·26 지수이동평균의 차이", "Difference of the 12- and 26-bar EMAs"),
    ("SIGNAL", "MACD 시그널", "MACD signal", "MACD의 9개 봉 지수이동평균", "9-bar EMA of MACD"),
    ("HISTOGRAM", "MACD 히스토그램", "MACD histogram", "MACD − 시그널", "MACD minus signal"),
)
LITERAL = {"qg_literal_value": True}  # page-authored per locale; the catalogue must not rewrite it
# The candle colours of core.market.presentation.chart_svg (`up, down`), reused so the price headline and
# the candles show a rise and a fall in the same colours (that module keeps them local to the chart).
CANDLE_UP, CANDLE_DOWN = "#D94A52", "#397AC4"
_SENTENCE_BREAK = re.compile(r"(?<=\.)\s+(?=[A-Z])")
_PARTIAL_HISTORY = re.compile(r"Partial history: (\d+)/(\d+) requested bars \(provider window or paging limit\)\.")


def _sentences(text):
    return [part.strip() for part in _SENTENCE_BREAK.split(str(text or "").strip()) if part.strip()]


def readable_time(value):
    """'2026-11-06T16:03:54+00:00' -> '2026-11-06 16:03:54 UTC'; date-only and unknown text unchanged."""
    text = str(value or "")
    if "T" not in text:
        return text
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    stamp = moment.strftime("%Y-%m-%d %H:%M:%S")
    offset = moment.utcoffset()
    if offset is None:
        return stamp
    minutes = int(offset.total_seconds() // 60)
    if minutes == 0:
        return stamp + " UTC"
    sign, minutes = ("+" if minutes > 0 else "-"), abs(minutes)
    return stamp + f" UTC{sign}{minutes // 60}" + (f":{minutes % 60:02d}" if minutes % 60 else "")


def _new_service():
    from data.kis_workspace import MarketDataService
    return MarketDataService()


def _new_stream():
    from data.kis_stream import KISStream
    return KISStream()


class MarketChartPage(ft.Column):
    """Cached Flet view with an explicit, reversible network lifecycle."""

    def __init__(self, page, *, service=None, stream_factory=None, on_open_settings=None):
        super().__init__(spacing=16, scroll=ft.ScrollMode.AUTO, expand=True,
                         horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self.host_page = page
        self.ctx = getattr(page, "qg_locale", LocaleContext())
        self._service = service
        self._stream_factory = stream_factory or _new_stream
        self._open_settings = on_open_settings
        self.mounted = False
        self.snapshot = None
        self.cursor = None
        self.visible_bars = 120
        self._generation = 0
        self._live_epoch = 0
        self._load_serial = 0
        self._load_lock = asyncio.Lock()
        self._loading = False
        self._stream = None
        self._poll_future = None
        self._watch_future = None
        self._tick_lock = threading.Lock()
        self._pending_ticks = deque()
        self._drain_scheduled = False
        self._last_tick = None
        self._stream_started = None
        self._stream_state = "STOPPED"
        self._stale = False
        self._gap_warning = False
        self._palette = active()
        self._viewport = None

        pal = self._palette
        # Type scale: page title 26 bold, quote price 26, section text 13–15, captions 12.
        self.title = ft.Text(size=26, weight=ft.FontWeight.BOLD, color=pal.text)
        self.subtitle = ft.Text(size=13, color=pal.muted)
        # Inputs: one row, one height. The code field enforces its length without a counter
        # line, which used to push it above the dropdowns.
        field = dict(border_radius=RADII["md"])
        self.asset = ft.Dropdown(value="domestic_stock", width=210, on_select=self.asset_changed, **field)
        self.code = ft.TextField(value="005930", width=170, max_length=32, counter="",
                                 on_change=self.inputs_changed, on_submit=self.load_chart, **field)
        self.exchange = ft.Dropdown(value="NAS", width=130, visible=False,
            options=[ft.dropdown.Option(k) for k in ("NAS", "NYS", "AMS", "HKS", "TSE", "SHS", "SZS", "HSX", "HNX")],
            on_select=self.inputs_changed, **field)
        self.interval = ft.Dropdown(value="1d", width=130, on_select=self.inputs_changed, **field)
        self.count = ft.Dropdown(value="240", width=130,
            options=[ft.dropdown.Option(str(k)) for k in (120, 240, 500)], on_select=self.inputs_changed, **field)
        # Actions: one primary query, the polling toggle, the stream pair, then the settings link.
        self.load = ft.Button(on_click=self.load_chart, icon=ft.Icons.REFRESH, height=40)
        self.auto = ft.Switch(value=False, on_change=self.toggle_auto,
                              label_text_style=ft.TextStyle(size=14, color=pal.text))
        self.live = ft.OutlinedButton(on_click=self.start_live, icon=ft.Icons.PLAY_ARROW, height=40)
        self.stop = ft.OutlinedButton(on_click=self.stop_live, icon=ft.Icons.STOP, disabled=True, height=40)
        self.settings = ft.TextButton(on_click=lambda e: self._open_settings and self._open_settings(),
                                      icon=ft.Icons.SETTINGS_OUTLINED, height=40,
                                      visible=on_open_settings is not None)
        self.busy = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False)
        # Status: three labelled lines in one block, one size.
        self.status = ft.Text(size=12, color=pal.text, selectable=True, expand=True)
        self.stream_status = ft.Text(size=12, color=pal.text, selectable=True, expand=True)
        self.coverage = ft.Text(size=12, color=pal.muted, selectable=True, expand=True)
        self.status_caption, self.stream_caption, self.coverage_caption = (
            ft.Text(size=12, color=pal.muted, width=72) for _ in range(3))
        status_block = ft.Container(ft.Column([
            ft.Row([caption, value], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START)
            for caption, value in ((self.status_caption, self.status),
                                   (self.stream_caption, self.stream_status),
                                   (self.coverage_caption, self.coverage))], spacing=6),
            padding=ft.Padding(12, 10, 12, 10), bgcolor=pal.surface,
            border=ft.Border.all(1, pal.border), border_radius=RADII["md"])
        # Quote headline: instrument line, price with signed change, indicator readings, provenance.
        self.quote_title = ft.Text(size=13, color=pal.muted, data=LITERAL)
        self.price = ft.Text(size=26, weight=ft.FontWeight.W_600, color=pal.text, selectable=True, data=LITERAL)
        self.currency = ft.Text(size=13, color=pal.muted, data=LITERAL)
        self.change = ft.Text(size=15, weight=ft.FontWeight.W_600, selectable=True, data=LITERAL)
        # Indicator readings: label over value, built once and updated in place on every tick.
        self.metric_labels = {key: ft.Text(size=12, color=pal.muted, data=LITERAL) for key, *_ in METRICS}
        self.metric_values = {key: ft.Text("—", size=14, weight=ft.FontWeight.W_600, color=pal.text,
                                           selectable=True, data=LITERAL) for key, *_ in METRICS}
        self.metrics = ft.Row([ft.Container(ft.Column([self.metric_labels[key], self.metric_values[key]], spacing=2))
                               for key, *_ in METRICS], spacing=24, run_spacing=8, wrap=True)
        self.source = ft.Text(size=12, color=pal.muted, selectable=True, data=LITERAL)
        self.note = ft.Text(size=12, color=pal.muted, selectable=True, data=LITERAL)
        self.quote_card = card(ft.Column([
            self.quote_title,
            ft.Row([self.price, self.currency, self.change], spacing=10, wrap=True,
                   vertical_alignment=ft.CrossAxisAlignment.END),
            self.metrics, ft.Divider(height=1, color=pal.border), self.source, self.note], spacing=8))
        self.quote_card.visible = False
        # Indicator toggles: one compact wrap row. A labelled Checkbox fills the whole run of a
        # wrap row (and a width scales it), so each one sits in a tight Row of its own.
        self.indicator_caption = ft.Text(size=12, color=pal.muted)
        self.indicators = {
            key: ft.Checkbox(value=key != "bollinger", on_change=self.indicators_changed,
                             label_style=ft.TextStyle(size=13, color=pal.text))
            for key in ("sma", "rsi", "macd", "bollinger")
        }
        self.image = ft.Image(src="data:image/svg+xml;base64," + base64.b64encode(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1"/>').decode(),
            visible=False, fit=ft.BoxFit.CONTAIN, gapless_playback=True)
        # Chart navigation: two sliders with their labels and current values on one grid.
        self.zoom_label = ft.Text(size=12, color=pal.muted, width=96)
        self.zoom = ft.Slider(min=20, max=500, divisions=48, value=120, expand=True,
                              on_change_end=self.zoom_changed, disabled=True)
        self.zoom_value = ft.Text(size=12, color=pal.text, width=88, text_align=ft.TextAlign.RIGHT, data=LITERAL)
        self.cursor_label = ft.Text(size=12, color=pal.muted, width=96)
        self.cursor_slider = ft.Slider(min=0, max=1, divisions=1, value=1, expand=True,
                                       on_change=self.cursor_changed, disabled=True)
        self.cursor_value = ft.Text(size=12, color=pal.text, width=88, text_align=ft.TextAlign.RIGHT, data=LITERAL)
        self.reading = ft.Text(size=13, color=pal.text, selectable=True)
        self.chart_tools = ft.Column([
            ft.Row([label, slider, value], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            for label, slider, value in ((self.zoom_label, self.zoom, self.zoom_value),
                                         (self.cursor_label, self.cursor_slider, self.cursor_value))
        ] + [self.reading], spacing=0, visible=False)
        self.explanation = ft.Text(size=12, color=pal.muted)
        self.controls = [
            ft.Column([self.title, self.subtitle], spacing=4),
            ft.Row([self.asset, self.code, self.exchange, self.interval, self.count],
                   spacing=12, run_spacing=12, wrap=True, vertical_alignment=ft.CrossAxisAlignment.START),
            # Groups wrap as units: query + polling, then the stream pair, then the settings link.
            ft.Row([ft.Row([self.load, self.auto], spacing=12, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([self.live, self.stop], spacing=8, tight=True),
                    self.settings, self.busy],
                   spacing=16, run_spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            status_block,
            self.quote_card,
            ft.Row([self.indicator_caption] + [ft.Row([box], tight=True) for box in self.indicators.values()],
                   spacing=12, run_spacing=0, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.image, self.chart_tools, self.explanation]
        self.render_locale(self.ctx)
        self.status.value = self.text("종목과 주기를 선택하고 조회하세요.", "Choose an instrument and timeframe, then load.")

    def text(self, ko, en):
        return ko if self.ctx.language == "ko" else en

    def render_locale(self, ctx):
        self.ctx = ctx
        self.title.value = self.text("실시간 시세 · 차트", "Live quotes & charts")
        self.subtitle.value = self.text("KIS 시세 · 캔들 · 거래량 · 기술지표", "KIS quotes · candles · volume · technical indicators")
        self.asset.label = self.text("자산", "Asset")
        self.asset.options = [ft.dropdown.Option(key, self.text(ko, en)) for key, ko, en in ASSET_LABELS]
        self.code.label = self.text("종목코드", "Instrument code")
        self.code.hint_text = self.text("현재 거래 중인 종목코드", "Current listed instrument code")
        self.exchange.label = self.text("거래소", "Exchange")
        self.interval.label = self.text("차트 주기", "Timeframe")
        self._refresh_capabilities()
        self.count.label = self.text("요청 봉 수", "Requested bars")
        self.load.content = self.text("조회 / 새로고침", "Load / refresh")
        self.auto.label = self.text("5초마다 조회", "Poll every 5 seconds")
        self.auto.tooltip = self.text("REST로 5초마다 다시 조회합니다.", "Re-query over REST every 5 seconds.")
        self.live.content = self.text("실시간 연결", "Connect stream")
        self.stop.content = self.text("연결 중지", "Stop stream")
        self.settings.content = self.text("데이터 연결", "Connection settings")
        self.status_caption.value = self.text("조회 상태", "Query")
        self.stream_caption.value = self.text("실시간", "Stream")
        self.coverage_caption.value = self.text("제공 범위", "Coverage")
        self.indicator_caption.value = self.text("보조지표", "Indicators")
        for key, ko, en in (("sma", "SMA 20", "SMA 20"), ("rsi", "RSI 14", "RSI 14"),
                            ("macd", "MACD 12 / 26 / 9", "MACD 12 / 26 / 9"),
                            ("bollinger", "볼린저 20 / 2σ", "Bollinger 20 / 2σ")):
            self.indicators[key].label = self.text(ko, en)
        for item, (key, ko, en, ko_tip, en_tip) in zip(self.metrics.controls, METRICS):
            self.metric_labels[key].value = self.text(ko, en)
            item.tooltip = self.text(ko_tip, en_tip)
        self.zoom_label.value = self.text("표시 봉 수", "Visible bars")
        self.zoom.tooltip = self.text("표시 범위 · 봉 수", "Visible range · bars")
        self.cursor_label.value = self.text("봉 선택", "Candle")
        self.cursor_slider.tooltip = self.text("봉 선택 · 맨 오른쪽은 최신 봉 추적", "Select a candle · rightmost follows the latest")
        self.explanation.value = self.text(
            "마지막 봉과 지표는 수신 중 바뀔 수 있습니다. 표본이 부족한 지표는 —로 표시합니다. "
            "5초 조회는 REST 주기 조회이며, 실시간 연결은 WebSocket 체결 수신입니다. 해외시세 지연과 제공 범위는 위의 ‘제공 범위’와 출처 줄을 확인하세요.",
            "The current candle and indicators can change with new trades. Indicators without enough history show —. "
            "Polling uses REST every 5 seconds; streaming receives WebSocket trades. See Coverage and the source line above for overseas delays and coverage.")
        if self.snapshot:
            self.draw_chart()
        self._render_stream_status()

    def render_theme(self, palette):
        viewport = getattr(self.host_page, "width", None)
        if palette != self._palette or viewport != self._viewport:
            self._palette, self._viewport = palette, viewport
            if self.snapshot:
                self.draw_chart()

    def _update_view(self):
        if self.mounted:
            self.update()

    def did_mount(self):
        self.mounted = True
        # A return to the view never silently reconnects or starts a data query.

    def reconnect_session(self):
        self.mounted = True

    def will_unmount(self):
        self.deactivate()

    def deactivate(self):
        self.mounted = False
        self._generation += 1
        self._load_serial += 1
        self._loading = False
        self.busy.visible = False
        self.auto.value = False
        self._cancel_poll()
        self._stop_stream()

    def current_request(self):
        asset = self.asset.value or "domestic_stock"
        exchange = (self.exchange.value or "") if asset in ("overseas_stock", "domestic_future") else ""
        return ChartRequest(Instrument(asset, self.code.value or "", exchange),
                            self.interval.value or "1d", int(self.count.value or "240"))

    def _refresh_capabilities(self):
        from data.kis_workspace import supported_intervals, availability_note
        asset = self.asset.value or "domestic_stock"
        code = (self.code.value or ("005930" if asset == "domestic_stock" else "UNSET"))
        exchange = (self.exchange.value or "") if asset in ("overseas_stock", "domestic_future") else ""
        try:
            instrument = Instrument(asset, code, exchange)
        except ValueError:
            return
        supported = supported_intervals(instrument)
        self.interval.options = [ft.dropdown.Option(key, self.text(ko, en)) for key, ko, en in TIMEFRAMES if key in supported]
        if self.interval.value not in supported:
            self.interval.value = "1d"
        korean = {
            "domestic_stock": ("KRX 시세 · 마지막 봉은 수신 중 바뀔 수 있습니다. 진행 중인 분봉 거래량은 KIS가 직전 분 값을 "
                               "잠시 반복할 수 있어 확정 전까지 표시하지 않습니다. 무거래 구간의 봉은 임의로 채우지 않습니다."),
            "domestic_future": ("만기별 종목코드와 시장 구분을 확인하세요. 가격은 원화 금액이 아니라 계약 호가 단위(포인트 등)입니다. "
                                "마지막 봉은 수신 중 바뀔 수 있습니다."),
            "overseas_future": "일·주·월봉 지원. 분봉과 WebSocket은 시각·가격 단위 확인이 필요해 지원하지 않습니다. CME/SGX는 시세 이용권이 필요합니다.",
            "bond": "채권 차트는 최근 최대 100개 일봉을 지원합니다. 첨부 KIS 규격에는 과거 분봉 조회가 없습니다. 가격은 액면 1만원 기준입니다.",
            "overseas_stock": ("미국 무료 Nasdaq 시세 · 0분 지연 · 유료 통합시세와 범위·OHLC가 다를 수 있습니다. "
                               "분봉은 정규장 기준이며 장중 시가는 다음 날 정정될 수 있습니다."
                if instrument.exchange in ("NAS", "NYS", "AMS") else "해외 무료 시세 · 15분 지연 · 분봉은 정규장 기준입니다."),
        }
        self.coverage.value = korean[asset] if self.ctx.language == "ko" else availability_note(instrument)

    def _cancel_poll(self):
        if self._poll_future is not None:
            self._poll_future.cancel()
            self._poll_future = None

    def _stop_stream(self):
        self._live_epoch += 1
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
        if self._watch_future is not None:
            self._watch_future.cancel()
            self._watch_future = None
        with self._tick_lock:
            self._pending_ticks.clear()
            self._drain_scheduled = False
        self._stream_state = "STOPPED"
        self._last_tick = self._stream_started = None
        self.live.disabled = False
        self.stop.disabled = True
        self._render_stream_status()

    def stop_live(self, e=None):
        self._stop_stream()
        self._update_view()

    def inputs_changed(self, e=None):
        self._generation += 1
        self._load_serial += 1
        self._loading = False
        self.busy.visible = False
        self.auto.value = False
        self._cancel_poll()
        self._stop_stream()
        self._refresh_capabilities()
        self.snapshot = None
        self.cursor = None
        self.image.visible = self.quote_card.visible = self.chart_tools.visible = False
        self.zoom.disabled = self.cursor_slider.disabled = True
        self.price.value = self.change.value = self.source.value = self.reading.value = self.note.value = ""
        self.status.value = self.text("조건이 바뀌었습니다. 다시 조회하세요.", "Selection changed. Load the new chart.")
        self._update_view()

    def asset_changed(self, e=None):
        self.code.value = DEFAULT_CODES.get(self.asset.value, "")
        self.exchange.visible = self.asset.value in ("overseas_stock", "domestic_future")
        choices = ("F", "O", "JF", "JO", "CF", "CM", "EU") if self.asset.value == "domestic_future" else ("NAS", "NYS", "AMS", "HKS", "TSE", "SHS", "SZS", "HSX", "HNX")
        self.exchange.options = [ft.dropdown.Option(k) for k in choices]
        self.exchange.value = choices[0]
        self.inputs_changed()

    async def load_chart(self, e=None, *, periodic=False):
        if not self.mounted:
            return False
        try:
            request = self.current_request()
        except (ValueError, TypeError):
            self.status.value = self.text("종목코드와 거래소를 확인하세요.", "Check the instrument code and exchange.")
            self._update_view()
            return False
        if self._stream is not None:
            self._stop_stream()
        generation = self._generation
        self._load_serial += 1
        serial = self._load_serial
        async with self._load_lock:
            if not self.mounted or generation != self._generation or serial != self._load_serial:
                return False
            self._loading = True
            self.busy.visible = True
            self.status.value = self.text("KIS 시세 조회 중…", "Loading KIS market data…")
            self._update_view()
            try:
                if self._service is None:
                    self._service = _new_service()
                snapshot = await asyncio.to_thread(self._service.load, request)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if self.mounted and generation == self._generation and serial == self._load_serial:
                    self._stale = bool(self.snapshot and self.snapshot.request == request)
                    # Provider exceptions may contain URLs or credentials; show only known class categories.
                    reason = {"KISUnavailable": self.text("KIS 연결 설정이 필요합니다.", "Configure the KIS connection."),
                              "ValueError": self.text("이 자산·주기의 제공 범위 또는 입력을 확인하세요.", "Check the asset/timeframe coverage and inputs.")}.get(
                                  type(exc).__name__, self.text("KIS 조회에 실패했습니다. 연결 상태와 제공 범위를 확인하세요.",
                                                             "KIS query failed. Check connectivity and available coverage."))
                    self.status.value = reason + (self.text(" 이전 결과 · 새로고침 실패", " Previous result · refresh failed") if self._stale else "")
                    self._update_view()
                return False
            finally:
                if generation == self._generation and serial == self._load_serial:
                    self._loading = False
                    self.busy.visible = False
                    self._update_view()
            if (not self.mounted or generation != self._generation or serial != self._load_serial
                    or request != self.current_request()):
                return False
            self.snapshot = snapshot
            self.cursor = None
            self._stale = False
            self._gap_warning = False
            self.status.value = self.text("REST 조회 완료", "REST query complete") + (self.text(" · 5초 주기 조회", " · 5-second polling") if periodic else "")
            self.draw_chart()
            self._update_view()
            return True

    async def toggle_auto(self, e=None):
        self._cancel_poll()
        if self.auto.value and self.mounted:
            self._stop_stream()
            generation = self._generation
            await self.load_chart(periodic=True)
            if self.mounted and self.auto.value and generation == self._generation:
                self._poll_future = self.host_page.run_task(self._poll, generation)
        self._update_view()

    async def _poll(self, generation):
        while self.mounted and self.auto.value and generation == self._generation:
            await asyncio.sleep(5)
            if self.mounted and self.auto.value and generation == self._generation:
                await self.load_chart(periodic=True)

    async def start_live(self, e=None):
        if not self.mounted:
            return
        self.auto.value = False
        self._cancel_poll()
        self._stop_stream()
        start_epoch = self._live_epoch
        try:
            request = self.current_request()
        except (ValueError, TypeError):
            self.status.value = self.text("종목코드와 거래소를 확인하세요.", "Check the instrument code and exchange.")
            self._update_view()
            return
        # A stopped/cached view can miss an arbitrary amount of market activity.
        # Every new subscription starts from authoritative history, even when the
        # selected request has not changed.
        if not await self.load_chart():
            return
        if not self.mounted or start_epoch != self._live_epoch or request != self.current_request():
            return
        # Fence any already-running REST response before accepting live ticks.
        self._load_serial += 1
        generation, epoch = self._generation, self._live_epoch
        self._stream_state = "CONNECTING"
        self._last_tick = None
        self._stream_started = time.monotonic()
        try:
            stream = self._stream_factory()
            self._stream = stream
            stream.start(request.instrument,
                lambda tick: self._queue_tick(generation, epoch, tick),
                lambda status: self._queue_status(generation, epoch, status))
        except Exception as exc:
            self._stop_stream()
            self.status.value = self.text("실시간 연결을 시작할 수 없습니다. KIS 설정과 해당 자산 지원 범위를 확인하세요.",
                "Cannot start streaming. Check KIS configuration and support for this asset.")
            self._update_view()
            return
        self.live.disabled, self.stop.disabled = True, False
        self._loading = self.busy.visible = False
        self.status.value = self.text("WebSocket 체결 수신 · 마지막 봉 갱신", "WebSocket trades · updating the current candle")
        self._render_stream_status()
        self._watch_future = self.host_page.run_task(self._watch_stream, generation, epoch)
        self._update_view()

    def _queue_status(self, generation, epoch, status):
        if self.mounted and generation == self._generation and epoch == self._live_epoch:
            self.host_page.run_task(self._receive_status, generation, epoch, status)

    async def _receive_status(self, generation, epoch, status):
        if self.mounted and generation == self._generation and epoch == self._live_epoch:
            state = status.split(":", 1)[0] if status else "ERROR"
            if state == "LIVE" and self._last_tick is None:
                state = "SUBSCRIBED"
            self._stream_state = state
            if self._stream_state == "RECONNECTING":
                self._gap_warning = self._stale = True
                self.status.value = self.text("연결 공백 · 일부 봉의 OHLC와 거래량이 불완전할 수 있습니다. 중지 후 새로고침하세요.",
                    "Connection gap · candle OHLC and volume may be incomplete. Stop streaming and reload.")
            self._render_stream_status()
            self._update_view()

    def _queue_tick(self, generation, epoch, tick):
        if not self.mounted or generation != self._generation or epoch != self._live_epoch:
            return
        with self._tick_lock:
            # Bound callbacks for a disconnected/slow browser. A gap becomes visible;
            # it is never presented as a complete trade-volume reconstruction.
            if len(self._pending_ticks) >= 4096:
                self._pending_ticks.clear()
                self._pending_ticks.append(None)
            self._pending_ticks.append(tick)
            if self._drain_scheduled:
                return
            self._drain_scheduled = True
        self.host_page.run_task(self._drain_ticks, generation, epoch)

    async def _drain_ticks(self, generation, epoch):
        await asyncio.sleep(0.15)
        if not self.mounted or generation != self._generation or epoch != self._live_epoch:
            return
        with self._tick_lock:
            ticks = list(self._pending_ticks)
            self._pending_ticks.clear()
            self._drain_scheduled = False
        if self.snapshot is None or self._gap_warning:
            return
        from core.market.live import apply_tick
        old_time = self.snapshot.candles[self.cursor].timestamp if self.cursor is not None else None
        changed = False
        for tick in ticks:
            if tick is None:
                self._gap_warning = self._stale = True
                self.status.value = self.text("체결 처리 지연으로 일부 수신 누락 · 다시 조회하세요.", "Some trades were dropped while the view was busy. Reload the chart.")
                break
            if tick.instrument != self.snapshot.request.instrument:
                continue
            result = apply_tick(self.snapshot, tick)
            if result is not self.snapshot:
                self.snapshot = result
                self._last_tick = time.monotonic()
                changed = True
        if old_time:
            self.cursor = next((i for i, candle in enumerate(self.snapshot.candles) if candle.timestamp == old_time), None)
        if changed:
            self._stream_state = "LIVE"
        self._render_stream_status()
        self.draw_chart()
        self._update_view()

    async def _watch_stream(self, generation, epoch):
        while self.mounted and generation == self._generation and epoch == self._live_epoch and self._stream is not None:
            await asyncio.sleep(5)
            if self.mounted and generation == self._generation and epoch == self._live_epoch:
                self._render_stream_status()
                self._update_view()

    def _render_stream_status(self):
        labels = {
            "STOPPED": self.text("실시간 연결 중지", "Stream stopped"),
            "CONNECTING": self.text("실시간 연결 중…", "Connecting stream…"),
            "SUBSCRIBED": self.text("구독 완료 · 체결 대기", "Subscribed · awaiting trades"),
            "LIVE": self.text("체결 수신 중", "Receiving trades"),
            "RECONNECTING": self.text("연결 복구 중 · 수신 공백 가능", "Reconnecting · there may be a data gap"),
            "ERROR": self.text("실시간 연결 오류 · 설정과 자산 지원을 확인하세요.", "Stream error · check configuration and asset support."),
        }
        value = labels.get(self._stream_state, labels["ERROR"])
        if self.asset.value == "overseas_stock" and self.exchange.value not in ("NAS", "NYS", "AMS"):
            value += self.text(" · 15분 지연 시세", " · 15-minute delayed quotes")
        last = self._last_tick or self._stream_started
        if self._stream is not None and last is not None and time.monotonic() - last >= 30:
            value += self.text(" · 30초 이상 새 체결 없음 · 장 운영/연결 확인", " · no new trades for 30+ seconds · check market hours/connection")
        if self._gap_warning:
            value += self.text(" · 수신 공백 발생 · 차트 재조회 필요", " · data gap occurred · reload the chart")
        self.stream_status.value = value

    def indicators_changed(self, e=None):
        if self.snapshot:
            self.draw_chart()
            self._update_view()

    def zoom_changed(self, e=None):
        self.visible_bars = max(20, min(500, int(float(self.zoom.value or 120))))
        if self.snapshot and self.cursor is not None:
            self.cursor = max(self.cursor, len(self.snapshot.candles) - self.visible_bars)
        self.draw_chart()
        self._update_view()

    def cursor_changed(self, e=None):
        if self.snapshot and self.snapshot.candles:
            index = min(len(self.snapshot.candles) - 1, max(0, round(float(self.cursor_slider.value or 0))))
            self.cursor = None if index == len(self.snapshot.candles) - 1 else index
            if index < len(self.snapshot.candles) - self.visible_bars:
                self.visible_bars = min(500, len(self.snapshot.candles) - index)
                self.zoom.value = self.visible_bars
            self.draw_chart()
            self._update_view()

    def draw_chart(self):
        if self.snapshot is None or not self.snapshot.candles:
            return
        from core.market.presentation import chart_svg, readout, indicator_values, number as market_number
        snapshot = self.snapshot
        width = max(350, min(1300, int((getattr(self.host_page, "width", None) or 1200) - 320)))
        selected = tuple(key for key, checkbox in self.indicators.items() if checkbox.value)
        svg = chart_svg(snapshot, indicators=selected, cursor=self.cursor, width=width,
                        dark=getattr(self.host_page, "qg_theme", "light") == "dark", visible=self.visible_bars,
                        language=self.ctx.language)
        self.image.src = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
        dimensions = re.search(r'<svg[^>]*width="(\d+)"[^>]*height="(\d+)"', svg)
        if dimensions:
            self.image.aspect_ratio = int(dimensions.group(1)) / int(dimensions.group(2))
        self.image.visible = True
        self.image.semantics_label = snapshot.request.instrument.symbol + " · " + snapshot.request.interval
        self.image.tooltip = self.reading.value = readout(snapshot, self.cursor, language=self.ctx.language)
        self.zoom.disabled = self.cursor_slider.disabled = False
        self.cursor_slider.max = max(1, len(snapshot.candles) - 1)
        self.cursor_slider.divisions = max(1, len(snapshot.candles) - 1)
        self.cursor_slider.value = self.cursor if self.cursor is not None else len(snapshot.candles) - 1
        self.zoom_value.value = str(min(self.visible_bars, len(snapshot.candles))) + self.text("봉", " bars")
        self.cursor_value.value = (self.text("최신 봉", "Latest") if self.cursor is None
                                   else f"{self.cursor + 1} / {len(snapshot.candles)}")
        self.chart_tools.visible = True
        values = indicator_values(snapshot)
        def number(value):
            if value is None or not math.isfinite(value):
                return "—"
            return self.ctx.number(value, 2)
        quote = snapshot.quote
        instrument = snapshot.request.instrument
        asset = next((self.text(ko, en) for key, ko, en in ASSET_LABELS if key == instrument.asset), instrument.asset)
        timeframe = next((self.text(ko, en) for key, ko, en in TIMEFRAMES if key == snapshot.request.interval),
                         snapshot.request.interval)
        self.quote_title.value = " · ".join((instrument.symbol, asset, timeframe))
        self.price.value = market_number(quote.price if quote else snapshot.candles[-1].close)
        if quote:
            self.currency.value = self.text("호가 단위", "quote units") if quote.currency == "quote units" else quote.currency
        else:
            self.currency.value = self.text("마지막 봉 종가", "last candle close")
        self.change.value, self.change.color = self._change_text(quote)
        for key, value in self.metric_values.items():
            value.value = number(values.get(key))
        sources = snapshot.source + (" / " + quote.source if quote and quote.source != snapshot.source else "")
        parts = [self.text("출처 ", "Source ") + sources, str(len(snapshot.candles)) + self.text("봉", " bars"),
                 self.text("마지막 봉 ", "Last candle ") + readable_time(snapshot.candles[-1].timestamp)]
        if quote and quote.market_time:
            parts.append(self.text("시세 시각 ", "Quote time ") + readable_time(quote.market_time))
        if (quote and quote.received_at) or snapshot.fetched_at:
            parts.append(self.text("수신 ", "Received ")
                         + readable_time((quote.received_at if quote else "") or snapshot.fetched_at))
        self.source.value = " · ".join(parts)
        self.note.value = self._note_text(snapshot)
        self.note.visible = bool(self.note.value)
        self.quote_card.visible = True

    def _change_text(self, quote):
        """'▼ 8,000 (-3.97%)' and its colour: the chart's own candle pair (KRX convention, rise red,
        fall blue), so the headline and the candles agree. The arrow and sign carry the direction
        without colour."""
        from core.market.presentation import number as market_number
        finite = lambda value: value if value is not None and math.isfinite(value) else None
        change = finite(quote.change) if quote else None
        pct = finite(quote.change_pct) if quote else None
        direction = pct if pct is not None else change
        if direction is None:
            return "", self._palette.muted
        if direction > 0:
            mark, colour = "▲", CANDLE_UP
        elif direction < 0:
            mark, colour = "▼", CANDLE_DOWN
        else:
            mark, colour = "", self._palette.muted
        pieces = [mark] if mark else []
        if change is not None:
            pieces.append(market_number(abs(change)))
        if pct is not None:
            signed = ("+" if pct > 0 else "-" if pct < 0 else "") + self.ctx.number(abs(pct), 2) + "%"
            pieces.append(f"({signed})" if change is not None else signed)
        return " ".join(pieces), colour

    def _note_text(self, snapshot):
        """Provider caveats not already shown as coverage, de-duplicated and in the reader's language."""
        from data.kis_workspace import availability_note
        quote = snapshot.quote
        shown = set(_sentences(availability_note(snapshot.request.instrument)))
        sentences = []
        for sentence in _sentences(snapshot.note) + _sentences(quote.note if quote else ""):
            if sentence not in shown:
                shown.add(sentence)
                sentences.append(sentence)
        if self.ctx.language != "ko":
            return " ".join(sentences)
        def korean(sentence):
            partial = _PARTIAL_HISTORY.fullmatch(sentence)
            if partial:
                return f"요청한 {partial.group(2)}봉 중 {partial.group(1)}봉만 받았습니다(제공 기간 또는 페이지 한도)."
            return self.ctx.text(sentence)
        return " ".join(korean(sentence) for sentence in sentences)


def build_market_chart_page(page, *, on_open_settings=None, service=None, stream_factory=None):
    return MarketChartPage(page, service=service, stream_factory=stream_factory, on_open_settings=on_open_settings)
