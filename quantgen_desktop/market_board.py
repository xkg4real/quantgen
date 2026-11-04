"""Markets indicator board: four line charts instead of a table (owner request UI-7).

The board owns its Jobs, so loading never disables the analysis tools. It loads only
when shown with automatic refresh enabled (or on its refresh button) and polls while
visible: KIS-sourced cards every minute, delayed daily sources every 15 minutes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from PyQt6.QtCore import QByteArray, QTimer, Qt, pyqtSlot
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from core.i18n import LocaleContext
from core.research.market_board import BOARD_SPECS, BY_KEY, build_routers, load_board
from .jobs import Jobs

KIS_POLL_SECONDS = 180          # three cards each page through KIS history; keep the pacer free
DELAYED_POLL_SECONDS = 900
RETRY_SECONDS = (60, 120, 300, 900)   # failed cards back off instead of retrying every tick


class MarketCard(QFrame):
    def __init__(self, spec):
        super().__init__()
        from .app import label
        self.spec, self.result = spec, None
        self.failure = None          # latest failed refresh while an older good value is shown
        self.failures = 0
        self.attempted_at = None
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(6)
        self.title = label("", "heading")
        head = QHBoxLayout()
        head.addWidget(self.title, 1)
        self.change = label("", wrap=False)
        head.addWidget(self.change, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(head)
        self.value = label("", "number")
        layout.addWidget(self.value)
        self.chart = QSvgWidget()
        self.chart.setFixedHeight(150)
        self.chart.setMinimumWidth(220)
        layout.addWidget(self.chart)
        lines = QVBoxLayout()
        lines.setSpacing(4)
        self.source_line, self.time_line = label("", "caption"), label("", "caption")
        lines.addWidget(self.source_line)
        lines.addWidget(self.time_line)
        layout.addLayout(lines)

    def render(self, ctx, dark=False):
        from core.market.presentation import card_svg
        ko = ctx.language == "ko"
        decimals = 3 if self.spec.unit == "%" else 2
        self.title.setText(self.spec.name(ctx.language))
        result = self.result
        series = result.series if result else None
        self._ctx, self._dark = ctx, dark
        if series is None:
            self.value.setText("—")
            self.change.setText("")
            self.render_chart()
            if result is None:
                self.source_line.setText("시장 화면을 열면 불러옵니다." if ko else "Loads when Markets is shown.")
                self.time_line.setText("")
            else:
                reason = ("설정된 공급사가 없습니다" if ko else "No provider is configured") \
                    if result.error == "ProvidersNotRun" else ("조회 실패" if ko else "Request failed")
                self.source_line.setText(f"{reason} · {result.tried(ctx.language)}")
                self.time_line.setText(("시도 " if ko else "Tried ") + _clock(result.loaded_at))
            self.setAccessibleName(self.spec.name(ctx.language))
            return
        unit = self.spec.unit
        self.value.setText(f"{series.last:,.{decimals}f}" + (" %" if unit == "%" else " 원" if unit == "KRW" and ko
                                                              else " KRW" if unit == "KRW" else ""))
        change = series.change
        if change is None:
            self.change.setText("")
        else:
            arrow = "▲" if change > 0 else "▼" if change < 0 else "–"
            text = f"{change:+.1f} bp" if unit == "%" else f"{change:+.2f}%"
            self.change.setText(f"{arrow} {text}")
            # Korean market convention, as in the price chart: rise red, fall blue.
            colour = "#D94A52" if change > 0 else "#397AC4" if change < 0 else ""
            self.change.setStyleSheet(f"color: {colour};" if colour else "")
        self.render_chart()
        delay = {"KIS": "장중 갱신" if ko else "updates in session",
                 "FRED": "일별 · 공표 지연" if ko else "daily · published with a lag"}.get(
            series.source, "지연 시세" if ko else "delayed")
        stale = (" · 오래된 관측" if ko else " · stale") if series.stale() else ""
        self.source_line.setText(("출처: " if ko else "Source: ") + f"{series.source} · {delay}{stale}")
        # "확인" is when QUANTGEN asked; providers may answer from a local cache. The
        # observation date is the data's own date.
        checked = _clock(self.failure.loaded_at if self.failure else series.fetched_at)
        failed = (" · 갱신 실패, 마지막 값 표시" if ko else " · refresh failed, last value shown") if self.failure else ""
        self.time_line.setText(("관측 " if ko else "Observed ") + series.dates[-1] + " · "
                               + ("확인 " if ko else "Checked ") + checked
                               + (" (한국시간)" if ko else " (Korea time)") + failed)
        self.chart.setToolTip((self.failure or result).tried(ctx.language))
        self.setAccessibleName(f"{self.spec.name(ctx.language)} {self.value.text()} {self.change.text()}")

    def render_chart(self):
        from core.market.presentation import card_svg
        ctx = getattr(self, "_ctx", None)
        if ctx is None:
            return
        series = self.result.series if self.result else None
        decimals = 3 if self.spec.unit == "%" else 2
        svg = card_svg(series.dates if series else (), series.values if series else (), width=self.chart.width(),
                       dark=self._dark, label=self.spec.name(ctx.language), decimals=decimals)
        self.chart.load(QByteArray(svg.encode("utf-8")))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_chart()  # only the chart depends on width


def _clock(text):
    from zoneinfo import ZoneInfo
    try:
        at = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return str(text)
    if at.tzinfo is None:
        return str(text)
    return at.astimezone(ZoneInfo("Asia/Seoul")).strftime("%m-%d %H:%M:%S")


class MarketBoard(QWidget):
    """Four market-indicator cards; no individual stocks (UI-7)."""

    def __init__(self, *, locale=None, routers=None, auto_load=True):
        super().__init__()
        from .app import label
        self.ctx = locale or LocaleContext("ko_KR")
        self.dark = False
        self.auto_load = auto_load
        self._routers = routers
        self._epoch = 0
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        head = QHBoxLayout()
        self.heading = label("", "heading")
        head.addWidget(self.heading, 1, Qt.AlignmentFlag.AlignVCenter)  # keep the accent bar to the text height
        self.status = label("", "caption", wrap=False)
        head.addWidget(self.status)
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(lambda: self.refresh(manual=True))
        head.addWidget(self.refresh_button)
        layout.addLayout(head)
        self.rights = label("", "caption")
        layout.addWidget(self.rights)
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        layout.addLayout(self.grid)
        self.cards = {spec.key: MarketCard(spec) for spec in BOARD_SPECS}
        self._columns = 0
        self._arrange()
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(15_000)  # checks due cards; providers are asked on their own cadence
        self.poll_timer.timeout.connect(self._poll)
        self.set_locale(self.ctx)

    # Layout -----------------------------------------------------------------
    def _arrange(self):
        columns = 2 if self.width() >= 700 else 1
        if columns == self._columns:
            return
        self._columns = columns
        for index, card in enumerate(self.cards.values()):
            self.grid.removeWidget(card)
            self.grid.addWidget(card, index // columns, index % columns)
        for column in range(2):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange()

    # Loading ----------------------------------------------------------------
    def routers(self):
        if self._routers is None:
            self._routers = build_routers()
        return self._routers

    def due_keys(self, now=None):
        now = now or datetime.now(timezone.utc)
        due = []
        for key, card in self.cards.items():
            if card.attempted_at is None:
                due.append(key)
                continue
            age = (now - card.attempted_at).total_seconds()
            series = card.result.series if card.result else None
            if card.failures:
                limit = RETRY_SECONDS[min(card.failures, len(RETRY_SECONDS)) - 1]
            else:
                limit = KIS_POLL_SECONDS if series is not None and series.source == "KIS" else DELAYED_POLL_SECONDS
            if age >= limit:
                due.append(key)
        return due

    def refresh(self, *, manual=False, keys=None):
        if self.jobs.busy:
            return False
        keys = list(keys or (list(self.cards) if manual else self.due_keys()))
        if not keys:
            return False
        self._epoch += 1
        epoch, routers = self._epoch, self.routers()
        self.status.setText("불러오는 중…" if self.ctx.language == "ko" else "Loading…")
        return self.jobs.start(lambda: (epoch, load_board(routers, keys)))

    @pyqtSlot(object)
    def _loaded(self, value):
        epoch, results = value
        if epoch != self._epoch:
            return
        now = datetime.now(timezone.utc)
        for result in results:
            card = self.cards[result.key]
            card.attempted_at = now
            if result.series is None:
                card.failures += 1
                # A failed refresh keeps the last good observation and says so on the card.
                if card.result is not None and card.result.series is not None:
                    card.failure = result
                    continue
            else:
                card.failures, card.failure = 0, None
            card.result = result
        self.status.setText("")
        self.render()

    @pyqtSlot(str)
    def _failed(self, code):
        self.status.setText(("조회 실패" if self.ctx.language == "ko" else "Request failed") + f" ({code})")

    @pyqtSlot(bool)
    def _busy(self, busy):
        self.refresh_button.setEnabled(not busy)

    def _poll(self):
        if self.isVisible():
            self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if self.auto_load:
            self.poll_timer.start()
            QTimer.singleShot(0, self.refresh)

    def hideEvent(self, event):
        self.poll_timer.stop()
        super().hideEvent(event)

    def stop(self):
        """Window closing: stop polling and ignore any answer still in flight."""
        self.poll_timer.stop()
        self._epoch += 1

    # Presentation -----------------------------------------------------------
    def set_locale(self, ctx):
        self.ctx = ctx
        ko = ctx.language == "ko"
        self.heading.setText("시장 지표" if ko else "Market indicators")
        self.refresh_button.setText("새로고침" if ko else "Refresh")
        self.refresh_button.setAccessibleName("시장 지표 새로고침" if ko else "Refresh market indicators")
        self.rights.setText("연구 참고용 · 공급사 표시 권리와 자료 시점(빈티지)은 확인되지 않았습니다. 금리 등락은 bp, 나머지는 직전 관측 대비 %입니다."
                            if ko else "For research · provider display rights and data vintage are unverified. "
                                       "Yield changes are in bp; others are % versus the previous observation.")
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.render()

    def render(self):
        for card in self.cards.values():
            card._ctx, card._dark = self.ctx, self.dark
            card.render(self.ctx, self.dark)


__all__ = ["MarketBoard", "MarketCard", "BY_KEY"]
