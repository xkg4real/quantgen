"""A slim index strip at the top of each market page (owner ruling UI-D10, R-D10-3, 2026-11-11).

Owner reading: "A slim market summary strip at the top is welcome where data exists (국내: 코스피·코스닥; 미국:
S&P 500·나스닥; 코인: 비트코인·이더리움) — small, not a second hero chart."

Data: the Research Home cards' own path (`home_view.load_market_history`: `core.ficc.data.load_series` with the
explicit 'yfinance' provider, keyless Yahoo daily closes, no synthetic or cross-provider fallback; the same
`HISTORY_DAYS` so Home and this strip share the in-memory cache for ^GSPC, ^KS11 and BTC-USD). Each tile shows
the last daily close, its change against the close before, and a month of closes as a sparkline. These are
daily figures read with a delay, never live: the strip says "지연·일별", and the date of the last close, the
provider and that an intraday last bar may still be moving stay in the tooltips (owner, 2026-11-04).

Loading runs off the UI thread, one market's two series per job, only while the strip is visible with automatic
loading on, or after the user presses the page's Refresh. The strip is given its series loader (the window passes
`production_series`); without one it never loads and stays hidden, so a page built on its own (tests) cannot
reach a provider. With automatic loading off and nothing loaded the strip is hidden (no empty dashes). A language
or theme switch re-renders without fetching.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math

from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from core.i18n import LocaleContext
from core.market import rankings as R
from .jobs import Jobs

# page -> ((Yahoo symbol, unit), ...); names (English, Korean) in owner_ui_language/market.py INDEX_NAMES.
SUMMARY = {"kr": (("^KS11", "pt"), ("^KQ11", "pt")), "us": (("^GSPC", "pt"), ("^IXIC", "pt")),
           "crypto": (("BTC-USD", "USD"), ("ETH-USD", "USD"))}
SPARK_POINTS = 22            # about a month of trading days
RETRY_SECONDS = 300
TILE_SPARK = (64, 22)


def _refresh_seconds():
    from .home_view import HISTORY_REFRESH_SECONDS
    return HISTORY_REFRESH_SECONDS


def production_series(symbol, **kwargs):
    """`core.ficc.data.load_series`, imported when first called (the window's loader for the strip)."""
    from core.ficc.data import load_series
    return load_series(symbol, **kwargs)


def load_summary(page, *, loader=None):
    """The page's index histories, one after the other; never raises (each failure keeps only a reason code)."""
    from .home_view import MarketInfo, load_market_history
    return tuple(load_market_history(MarketInfo(symbol, "yfinance", unit), loader=loader)
                 for symbol, unit in SUMMARY[page])


def _label(rk, *, numbers=False):
    widget = QLabel()
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setProperty("rk", rk)
    widget.setProperty("qg_literal", True)
    if numbers:
        from .font_policy import number_font
        widget.setFont(number_font(widget.font()))
    return widget


class SummaryTile(QFrame):
    """One index: name, last close, change and a month's sparkline in a single slim row."""

    def __init__(self, symbol, unit):
        super().__init__()
        from .market_rankings import Sparkline
        from .owner_ui_language.market import INDEX_NAMES
        self.symbol, self.names, self.unit = symbol, INDEX_NAMES[symbol], unit
        self.setObjectName("summaryTile")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 7, 12, 7)
        layout.setSpacing(10)
        self.name = _label("sumName")
        self.value = _label("sumValue", numbers=True)
        self.change = _label("sumChange", numbers=True)
        self.spark = Sparkline(*TILE_SPARK)
        for widget in (self.name, self.value, self.change):
            layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.spark, 0, Qt.AlignmentFlag.AlignVCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def show_history(self, history, *, language, dark, loading):
        from .typography import TONE_COLORS, set_tone
        name = self.names[1] if language == "ko" else self.names[0]
        self.name.setText(name)
        ok = history is not None and history.ok
        if ok:
            values = history.values
            last, before = values[-1], values[-2]
            self.value.setText(R.price_text(last, "USD") if self.unit == "USD" else f"{last:,.2f}")
            pct = (last / before - 1) * 100 if before else None
            text, tone = R.change_text(pct)
            self.change.setText(text or "—")
            set_tone(self.change, tone)
            closes = values[-SPARK_POINTS:]
            tones = TONE_COLORS[bool(dark)]
            self.spark.set_values(closes, tones["up"] if closes[-1] >= closes[0] else tones["down"])
            self.spark.show()
        else:
            self.value.setText("—")
            self.change.setText("")
            set_tone(self.change, "flat")
            self.spark.set_values((), "#000000")
            self.spark.setVisible(False)
        self.change.setVisible(bool(self.change.text()))
        self.setToolTip(self._tip(history, language, loading))
        self.setAccessibleName(" ".join(part for part in (name, self.value.text(), self.change.text()) if part))

    def _tip(self, history, language, loading):
        from .translations import translate
        t = (lambda en, **f: translate(en.format(**f), "ko") if language == "ko" else en.format(**f))
        if history is not None and history.ok:
            tip = t("{source} daily close, last {day}; during the session the last value can still be moving.",
                    source="Yahoo Finance", day=history.dates[-1])
            if self.unit == "USD":
                tip += " " + t("US dollars; a coin's day is the UTC calendar day.")
            return tip
        if loading:
            from .owner_ui_language.market import PAGE_TEXT
            return PAGE_TEXT["loading"][1 if language == "ko" else 0]
        if history is not None and history.reason:
            return t("Could not load this index ({code}).", code=history.reason)
        return t("Not loaded yet. Press Refresh to load the list.")


class MarketSummary(QWidget):
    """The page's two index tiles and the honest data state ("지연·일별")."""
    loaded = pyqtSignal(str)
    changed = pyqtSignal()

    def __init__(self, *, loader=None, locale=None, auto_load=True, clock=None):
        super().__init__()
        self.setObjectName("marketSummary")
        self.loader, self.auto_load = loader, auto_load
        self.ctx, self.dark = locale or LocaleContext("ko_KR"), False
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.page = "kr"
        self.histories = {}          # symbol -> MarketHistory
        self._fetched = {}           # page -> when its last load finished
        self._loading = None         # page while its job runs
        self._epoch, self._stopped = 0, False
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.tiles = {}
        for page, rows in SUMMARY.items():
            for symbol, unit in rows:
                tile = SummaryTile(symbol, unit)
                tile.hide()
                self.tiles[symbol] = tile
                layout.addWidget(tile)
        layout.addSpacing(4)
        self.state = _label("sumState")
        layout.addWidget(self.state, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)
        self.timer = QTimer(self)
        self.timer.setInterval(60_000)
        self.timer.timeout.connect(self._tick)
        self.render()

    # Loading ---------------------------------------------------------------------------------
    def due(self, page=None):
        page = page or self.page
        fetched = self._fetched.get(page)
        if fetched is None:
            return True
        ok = all(self.histories.get(symbol) is not None and self.histories[symbol].ok
                 for symbol, *_ in SUMMARY[page])
        limit = _refresh_seconds() if ok else RETRY_SECONDS
        return (self.clock() - fetched).total_seconds() >= limit

    def refresh(self, *, manual=False):
        if self.loader is None or self._stopped or self.jobs.busy or (not manual and not self.due()):
            return False
        self._epoch += 1
        epoch, page, loader = self._epoch, self.page, self.loader
        self._loading = page
        started = self.jobs.start(lambda: (epoch, page, load_summary(page, loader=loader)))
        self.render()
        return started

    @pyqtSlot(object)
    def _loaded(self, value):
        epoch, page, histories = value
        if epoch != self._epoch:
            return
        self._loading = None
        for history in histories:
            kept = self.histories.get(history.symbol)
            if history.ok or kept is None or not kept.ok:
                self.histories[history.symbol] = history  # a failed reload keeps the last good closes
        self._fetched[page] = self.clock()
        self.render()
        self.loaded.emit(page)
        if page != self.page and self.isVisible() and self.auto_load:
            QTimer.singleShot(0, self.refresh)

    @pyqtSlot(str)
    def _failed(self, _code):
        self._loading = None
        self._fetched[self.page] = self.clock()
        self.render()

    def _tick(self):
        if self.isVisible() and self.auto_load:
            self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if self.auto_load:
            self.timer.start()
            QTimer.singleShot(0, self.refresh)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def stop(self):
        self.timer.stop()
        self._stopped = True
        self._epoch += 1
        self._loading = None

    # Presentation ----------------------------------------------------------------------------
    def set_page(self, page):
        if page not in SUMMARY:
            raise ValueError(f"Unknown market page {page!r}")
        self.page = page
        self.render()
        if self.auto_load and self.isVisible():
            QTimer.singleShot(0, self.refresh)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.render()

    def has_data(self, page=None):
        return any(self.histories.get(symbol) is not None and self.histories[symbol].ok
                   for symbol, *_ in SUMMARY[page or self.page])

    def wanted(self):
        """Shown when it has something to show or will load by itself: never a row of empty dashes."""
        return self.has_data() or self._loading == self.page or (
            self.auto_load and self.loader is not None and not self._stopped)

    def render(self):
        from .translations import translate
        lang = "ko" if self.ctx.language == "ko" else "en"
        shown = {symbol for symbol, *_ in SUMMARY[self.page]}
        for symbol, tile in self.tiles.items():
            if symbol in shown:
                tile.show_history(self.histories.get(symbol), language=lang, dark=self.dark,
                                  loading=self._loading == self.page)
            tile.setVisible(symbol in shown)
        self.state.setText(R.text(R.STATES, "daily", lang))
        self.state.setToolTip(translate("Index and coin figures are Yahoo Finance daily closes, read with a delay; "
                                        "not live.", "ko") if lang == "ko" else
                              "Index and coin figures are Yahoo Finance daily closes, read with a delay; not live.")
        self.state.setVisible(self.has_data())
        self.changed.emit()  # the page shows the strip only while `wanted()`


__all__ = ["MarketSummary", "SummaryTile", "SUMMARY", "load_summary", "production_series"]
