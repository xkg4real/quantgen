"""Markets workspace: one page per market (국내 주식 / 미국 주식 / 크립토 / 국내 ETF / 미국 ETF) and one screen per stock.

Owner ruling 2026-11-11 (UI-D10): the rail lists the markets; each market's page ranks its list by the categories
that were the sub-menu, which double as search criteria (`MarketsWorkspace`, `market_rankings.RankingBoard`,
`core.market.screen`). The page's header search narrows the shown market's list and opens a stock by name or code.

Owner request 2026-11-04: one search bar takes a stock code or a stock name (Korean, English, 초성) through
core.market.directory (futures and bonds keep code entry through the kind selector), and choosing a stock
opens one screen with its price chart and every profile section core.research.stock_profile provides.

Owner request 2026-11-11 (point 5, "토스증권처럼 실시간 차트를 다양한 분류기준으로"): below the search, Markets
shows Toss-style ranked lists (`market_rankings.RankingBoard`: trading value, volume, top gainers, top losers,
market cap; all of Korea, KOSPI, KOSDAQ or the US). The watchlist chart cards (`WatchlistGrid`, kept here
with its constructor) moved to Research Home (point 4); the user's watchlist store stays shared.

Provider and observation-date fields are not shown as columns or lines (owner request). They stay in
tooltips, and delayed, fallback, stale and failed states stay labelled (docs/compliance/09-dark-patterns.md).
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone

from PyQt6.QtCore import (QAbstractListModel, QByteArray, QModelIndex, QObject, QSize, QTimer, Qt, pyqtSignal,
                          pyqtSlot)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QComboBox, QCompleter, QFrame, QGridLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QSizePolicy, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market import rankings as _rankings
from core.market import screen as _screen
from core.market.models import ChartRequest, Instrument
from core.theme import DARK, LIGHT
from .company_identity import CompanyMark, company_icon
from .jobs import Jobs
from .tools import CurrentPageStack

# Interface contract between the native UI areas: the rail's 시장 flyouts (owner ruling UI-D11, 2026-11-12;
# `shell_rail.market_menu`) open a MARKET_PAGES page with `MarketsWorkspace.show_market(key)` and rank it with
# `show_category(key)`, a RANKING_CATEGORIES key (or "search", for earlier callers, UI-D7).
RANKING_CATEGORIES = _rankings.CATEGORIES
MARKET_PAGES = _screen.PAGES
MARKET_PAGE_KEYS = _screen.PAGE_KEYS
# Pages whose rows are listed securities the stock screen opens, by asset (UI-D11: the ETF pages too).
PAGE_ASSETS = {"kr": ("domestic_stock",), "us": ("overseas_stock",), "etf_kr": ("domestic_stock",),
               "etf_us": ("overseas_stock",)}
STOCK_PAGES = tuple(PAGE_ASSETS)
ASSET_PAGES = {"domestic_stock": ("kr", "etf_kr"), "overseas_stock": ("us", "etf_us")}
WATCHLIST_KEY = "markets/watchlist"
WATCHLIST_LIMIT = 20
DEFAULT_CODES = ("005930", "000660", "005380", "105560", "373220", "207940")
KIS_POLL_SECONDS = 180
DELAYED_POLL_SECONDS = 900
RETRY_SECONDS = (60, 120, 300, 900)
STALE_DAYS = 7
CARD_BARS = 120
# Owner, 2026-11-11: watchlist cards looked flat ("좌우를 줄이고 상하 살짝 늘려줘"): four columns on a
# wide page and a taller sparkline; raised again the same day (210px).
CARD_CHART_HEIGHT = 210  # owner 2026-11-11 (2nd): still "위아래로 납작해" at 150; about 3:2 on a 300px card


def card_columns(width):
    """Watchlist card columns for a page width: about 300px per card on a wide page."""
    return 4 if width >= 1200 else 3 if width >= 900 else 2 if width >= 600 else 1
STOCK_ASSETS = ("domestic_stock", "overseas_stock")
# US tickers load by their bare code in the analysis tools; HKS/TSE codes ('00700', '7203') would not.
US_EXCHANGES = ("NAS", "NYS", "AMS")
KIS_SOURCES = frozenset({"KIS", "KIS REST"})  # KIS chart snapshots name either; anything else is a fallback
# Kind selector: stocks search by code or name; derivatives and bonds take a code.
KINDS = (("stock", "주식", "Stocks", "005930"),
         ("domestic_future", "국내 파생", "Domestic derivatives", "101W12"),
         ("overseas_future", "해외 파생", "Overseas derivatives", "ESZ26"),
         ("bond", "채권", "Bonds", "KR103502GC66"))


def _text(ctx, ko, en):
    return ko if ctx.language == "ko" else en


def set_tone(widget, tone):
    """Up/down/flat colours through the shared stylesheet; no value clears the tone."""
    from .typography import TONES, set_tone as apply_tone
    if tone in TONES:
        apply_tone(widget, tone)
        return
    if widget.property("tone"):
        widget.setProperty("tone", "")
        widget.style().unpolish(widget)
        widget.style().polish(widget)


def _discard(widget):
    """Hide and detach now; delete later. A deferred delete alone leaves the old text on screen."""
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


def _key(instrument):
    return (instrument.asset, instrument.code, instrument.exchange)


def _change_text(change_pct):
    if change_pct is None:
        return "", None
    arrow = "▲" if change_pct > 0 else "▼" if change_pct < 0 else "–"
    tone = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
    return f"{arrow} {change_pct:+.2f}%", tone


def _price_text(value, instrument):
    if value is None:
        return "—"
    if instrument.asset == "domestic_stock":
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def _clock(text):
    from zoneinfo import ZoneInfo
    try:
        at = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return str(text or "")
    if at.tzinfo is None:
        return str(text)
    return at.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")


# Watchlist store --------------------------------------------------------------------------
class WatchlistStore(QObject):
    """The user's watchlist: a JSON list of instruments in QSettings, or in memory in tests.

    Only asset, code and exchange are stored. An absent key starts from the six Home stocks;
    a stored empty list stays empty (the user removed everything).
    """
    changed = pyqtSignal()

    def __init__(self, settings=None, *, defaults=None, limit=WATCHLIST_LIMIT):
        super().__init__()
        self.settings, self.limit = settings, limit
        self._defaults = list(defaults if defaults is not None
                              else (Instrument("domestic_stock", code) for code in DEFAULT_CODES))
        self._items = self._read()

    def _read(self):
        raw = self.settings.value(WATCHLIST_KEY) if self.settings is not None else None
        if raw is None:
            return list(self._defaults)[: self.limit]
        try:
            rows = json.loads(raw) if isinstance(raw, str) else []
        except ValueError:
            rows = []
        items, seen = [], set()
        for row in rows if isinstance(rows, list) else []:
            try:
                instrument = Instrument(str(row["asset"]), str(row["code"]), str(row.get("exchange", "")))
            except (KeyError, TypeError, ValueError):
                continue  # an invalid stored entry is skipped, never repaired into another code
            if _key(instrument) not in seen and len(items) < self.limit:
                seen.add(_key(instrument))
                items.append(instrument)
        return items

    def _write(self):
        if self.settings is not None:
            self.settings.setValue(WATCHLIST_KEY, json.dumps(
                [{"asset": i.asset, "code": i.code, "exchange": i.exchange} for i in self._items]))
        self.changed.emit()

    def items(self):
        return list(self._items)

    def contains(self, instrument):
        return any(_key(item) == _key(instrument) for item in self._items)

    def full(self):
        return len(self._items) >= self.limit

    def add(self, instrument):
        if self.contains(instrument) or self.full():
            return False
        self._items.append(instrument)
        self._write()
        return True

    def remove(self, instrument):
        before = len(self._items)
        self._items = [item for item in self._items if _key(item) != _key(instrument)]
        if len(self._items) == before:
            return False
        self._write()
        return True


# Symbol directory and search ----------------------------------------------------------------
class DirectoryLoader(QObject):
    """Loads the KIS stock masters once in the background (in memory only)."""
    loaded = pyqtSignal(int)

    def __init__(self, directory, *, enabled=True):
        super().__init__()
        self.directory, self.enabled = directory, enabled
        self._started_at = None
        self._lock = threading.Lock()

    def ensure(self):
        """Start the download unless done, running, disabled, or retried within 10 minutes."""
        if not self.enabled or self.directory is None or getattr(self.directory, "domestic_loaded", True):
            return False
        with self._lock:
            now = datetime.now(timezone.utc)
            if self._started_at is not None and (now - self._started_at).total_seconds() < 600:
                return False
            self._started_at = now
        thread = threading.Thread(target=self._run, name="qg-symbol-master", daemon=True)
        thread.start()
        return True

    def _run(self):
        try:
            added = self.directory.load_domestic()
        except Exception:  # load_domestic never raises by contract; keep the thread quiet anyway
            added = 0
        self.loaded.emit(int(added or 0))


class _ListingModel(QAbstractListModel):
    """Display text is the label with its code; the edit text is the code alone."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listings, self.lang = [], "ko"
        self.palette, self.dpr = LIGHT, 1.0

    def set_rows(self, listings, lang):
        self.beginResetModel()
        self.listings, self.lang = list(listings), lang
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.listings)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.listings):
            return None
        listing = self.listings[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            place = listing.exchange or (_KIND_KO.get(listing.kind, "") if self.lang == "ko"
                                         else _KIND_EN.get(listing.kind, ""))
            name = listing.label(self.lang)
            tail = f"{listing.code} · {place}" if place else listing.code
            return f"{name}   {tail}" if name and name != listing.code else tail
        if role == Qt.ItemDataRole.EditRole:
            return listing.code
        if role == Qt.ItemDataRole.DecorationRole:
            return company_icon(listing.code, listing.label(self.lang), palette=self.palette,
                                size=26, dpr=self.dpr)
        if role == Qt.ItemDataRole.ToolTipRole:
            return listing.label(self.lang)
        return None


_KIND_KO = {"stock": "국내 주식", "etf": "ETF", "etn": "ETN", "reit": "리츠", "other": "국내"}
_KIND_EN = {"stock": "KRX stock", "etf": "ETF", "etn": "ETN", "reit": "REIT", "other": "KRX"}


class SymbolCompleter(QObject):
    """Code-or-name search on any QLineEdit (owner request: every chart search).

    Results come from the symbol directory, ranked there. Choosing a row puts the code in
    the field (the last comma-separated item when ``multi``) and emits ``chosen``.
    """
    chosen = pyqtSignal(object)

    def __init__(self, line_edit, directory, *, assets=STOCK_ASSETS, kinds=None, exchanges=None, multi=False,
                 locale=None, loader=None, limit=8):
        super().__init__(line_edit)
        self.edit, self.directory = line_edit, directory
        self.assets, self.kinds, self.multi, self.limit = assets, kinds, multi, limit
        self.exchanges = exchanges  # overseas exchanges offered; None offers all
        self.ctx = locale or LocaleContext("ko_KR")
        self.loader = loader
        self.enabled = True
        self.model = _ListingModel(self)
        self.completer = QCompleter(self.model, self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setMaxVisibleItems(limit)
        self.completer.setWidget(line_edit)
        self.completer.popup().setObjectName("symbolPopup")
        self.completer.popup().setIconSize(QSize(26, 26))
        self.completer.activated[QModelIndex].connect(self._activated)
        line_edit.textEdited.connect(self._edited)
        line_edit.installEventFilter(self)
        if loader is not None:
            loader.loaded.connect(self._directory_loaded)

    def set_locale(self, ctx):
        self.ctx = ctx

    def set_theme(self, palette, dark):
        """The popup is a separate top-level window, so the window stylesheet never reaches it."""
        from .typography import popup_stylesheet
        self.completer.popup().setStyleSheet(popup_stylesheet(palette, dark))
        self.model.palette = palette
        self.model.dpr = self.edit.devicePixelRatioF()
        if self.model.rowCount():
            self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount() - 1),
                                        [Qt.ItemDataRole.DecorationRole])

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self.edit and event.type() == QEvent.Type.FocusIn and self.loader is not None:
            self.loader.ensure()
        return False

    def _query(self, text):
        return text.split(",")[-1].strip() if self.multi else text.strip()

    def results(self, text):
        query = self._query(text)
        if not query or self.directory is None:
            return []
        narrowed = self.kinds or self.exchanges is not None
        rows = self.directory.search(query, limit=self.limit * 3 if narrowed else self.limit, assets=self.assets)
        if self.kinds:
            rows = [row for row in rows if row.kind in self.kinds]
        if self.exchanges is not None:
            rows = [row for row in rows if row.asset != "overseas_stock" or row.exchange in self.exchanges]
        return rows[: self.limit]

    def _edited(self, text):
        if not self.enabled:
            return
        rows = self.results(text)
        self.model.set_rows(rows, self.ctx.language)
        if rows:
            self.completer.setCompletionPrefix("")
            self.completer.complete()
        else:
            self.completer.popup().hide()

    def _directory_loaded(self, _added):
        if self.edit.hasFocus() and self.completer.popup().isVisible():
            self._edited(self.edit.text())

    @pyqtSlot(QModelIndex)
    def _activated(self, index):
        if not index.isValid() or index.row() >= len(self.model.listings):
            return
        listing = self.model.listings[index.row()]
        self.apply(listing)

    def apply(self, listing):
        """Put the code into the field and announce the choice (tests call this too)."""
        if self.multi:
            parts = [part.strip() for part in self.edit.text().split(",")]
            parts[-1] = listing.code
            text = ", ".join(part for part in parts if part)
        else:
            text = listing.code
        # QCompleter may write the edit role (the bare code) after `activated`; restore ours on the
        # next turn only if the field still holds it, so a screen that clears the field stays clear.
        self.edit.setText(text)

        def restore():
            if self.edit.text() in (text, listing.code):
                self.edit.setText(text)
        QTimer.singleShot(0, restore)
        self.chosen.emit(listing)


def attach_symbol_search(line_edit, directory, **kwargs):
    """Install code-or-name search on an existing field; returns the completer."""
    return SymbolCompleter(line_edit, directory, **kwargs)


# Watchlist cards -----------------------------------------------------------------------------
@dataclass(frozen=True)
class CardResult:
    instrument: Instrument
    snapshot: object | None
    error: str = ""
    attempts: tuple = ()


def load_cards(router, instruments, cancelled=None):
    """Daily adjusted closes per instrument, one at a time (KIS paces itself); failures stay per card.

    ``cancelled`` is checked before each card, so closing the window waits for one request at most.
    """
    results = []
    for instrument in instruments:
        if cancelled is not None and cancelled():
            break
        try:
            snapshot = router.load(ChartRequest(instrument, "1d", CARD_BARS, adjusted=True))
            results.append(CardResult(instrument, snapshot, "", tuple(getattr(router, "last_attempts", ()))))
        except Exception as exc:  # the class name is the whole record
            results.append(CardResult(instrument, None, type(exc).__name__,
                                      tuple(getattr(router, "last_attempts", ()))))
    return results


def _closes(snapshot):
    candles = tuple(getattr(snapshot, "candles", ()) or ())
    return [c.timestamp[:10] for c in candles], [float(c.close) for c in candles]


def _stale(snapshot, today=None):
    dates, _ = _closes(snapshot)
    if not dates:
        return True
    try:
        last = date.fromisoformat(dates[-1])
    except ValueError:
        return False
    return ((today or date.today()) - last).days > STALE_DAYS


class WatchCard(QFrame):
    opened = pyqtSignal(object)
    removed = pyqtSignal(object)

    def __init__(self, instrument, name_fn):
        super().__init__()
        from .app import label
        self.instrument, self.name_fn = instrument, name_fn
        self.result = None
        self.failure = None
        self.failures = 0
        self.attempted_at = None
        self._ctx, self._dark = LocaleContext("ko_KR"), False
        self.setObjectName("panel")
        self.setProperty("card", "watch")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(4)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.mark = CompanyMark(instrument.code, size=34)
        head.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(1)
        self.title = label("", "cardTitle", wrap=False)
        self.code = label("", "eyebrow", wrap=False)
        names.addWidget(self.title)
        names.addWidget(self.code)
        head.addLayout(names, 1)
        self.remove_button = QPushButton("×")
        self.remove_button.setProperty("flat", True)
        self.remove_button.setFixedSize(28, 28)
        self.remove_button.clicked.connect(lambda: self.removed.emit(self.instrument))
        head.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(head)
        figures = QHBoxLayout()
        self.price = label("", "price", wrap=False)
        self.change = label("", "delta", wrap=False)
        figures.addWidget(self.price)
        figures.addWidget(self.change)
        figures.addStretch()
        layout.addLayout(figures)
        self.chart = QSvgWidget()
        self.chart.setFixedHeight(CARD_CHART_HEIGHT)  # owner 2026-11-11: narrower, taller cards
        self.chart.setMinimumWidth(200)
        layout.addWidget(self.chart)
        self.state = label("", "caption", wrap=False)
        self.state.hide()
        layout.addWidget(self.state)

    def name(self):
        return self.name_fn(self.instrument, self._ctx.language)

    def render(self, ctx, dark=False):
        self._ctx, self._dark = ctx, dark
        name = self.name()
        self.mark.set_identity(self.instrument.code, name)
        self.mark.set_theme(DARK if dark else LIGHT)
        self.title.setText(name)
        place = self.instrument.exchange or ("KRX" if self.instrument.asset == "domestic_stock" else "")
        self.code.setText(f"{self.instrument.code} · {place}" if place else self.instrument.code)
        self.remove_button.setToolTip(_text(ctx, "관심종목에서 빼기", "Remove from watchlist"))
        self.remove_button.setAccessibleName(_text(ctx, f"{name} 관심종목에서 빼기", f"Remove {name} from watchlist"))
        snapshot = self.result.snapshot if self.result else None
        if snapshot is None:
            self.price.setText("—")
            self.change.setText("")
            set_tone(self.change, "")
            self.change.hide()  # an empty delta pill showed as a blank grey box
            if self.result is None:
                self._state(_text(ctx, "화면을 열면 불러옵니다.", "Loads when shown."))
            else:
                self._state(_text(ctx, "불러오지 못했습니다", "Could not load") + f" ({self.result.error})")
            self.render_chart()
            self.setAccessibleName(name)
            return
        dates, closes = _closes(snapshot)
        quote = getattr(snapshot, "quote", None)
        last = quote.price if quote is not None and quote.price is not None else (closes[-1] if closes else None)
        pct = quote.change_pct if quote is not None and quote.change_pct is not None else (
            (closes[-1] / closes[-2] - 1) * 100 if len(closes) >= 2 and closes[-2] else None)
        self.price.setText(_price_text(last, self.instrument))
        text, tone = _change_text(pct)
        self.change.setText(text)
        set_tone(self.change, tone)
        self.change.setVisible(bool(text))  # no change, no empty grey pill
        self.render_chart()
        # Not shown as text: provider and observation date (owner request). They stay in the tooltip.
        source = str(getattr(snapshot, "source", "") or "")
        self.setToolTip(_text(ctx, "출처 ", "Source ") + source + (" · " + dates[-1] if dates else "")
                        + _text(ctx, " · 확인 ", " · checked ") + _clock(getattr(snapshot, "fetched_at", "")))
        states = []
        if source and source not in KIS_SOURCES:
            # Owner, 2026-11-04: no provider on the card; the fallback's name stays in the tooltip.
            states.append(_text(ctx, "지연 시세", "Delayed"))
        if _stale(snapshot):
            states.append(_text(ctx, "오래된 자료", "Stale data"))
        if self.failure is not None:
            states.append(_text(ctx, "갱신 실패, 마지막 값 표시", "Refresh failed, last value shown"))
        self._state(" · ".join(states))
        self.setAccessibleName(f"{name} {self.price.text()} {self.change.text()}")

    def _state(self, text):
        self.state.setText(text)
        self.state.setVisible(bool(text))

    def render_chart(self):
        from core.market.presentation import card_svg
        snapshot = self.result.snapshot if self.result else None
        dates, closes = _closes(snapshot) if snapshot is not None else ((), ())
        decimals = 0 if self.instrument.asset == "domestic_stock" else 2
        svg = card_svg(dates, closes, width=max(self.chart.width(), 220), height=CARD_CHART_HEIGHT, dark=self._dark,
                       label=self.name(), decimals=decimals)
        self.chart.load(QByteArray(svg.encode("utf-8")))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_chart()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.opened.emit(self.instrument)
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.opened.emit(self.instrument)
            return
        super().keyPressEvent(event)


class WatchlistGrid(QWidget):
    """The user's watchlist as chart cards; loads only while visible with auto load on."""
    open_requested = pyqtSignal(object)

    def __init__(self, store, *, router_factory=None, name_fn=None, locale=None, auto_load=True):
        super().__init__()
        from .app import label
        self.store, self.ctx, self.dark = store, locale or LocaleContext("ko_KR"), False
        self.auto_load = auto_load
        self._router_factory, self._router = router_factory, None
        self.name_fn = name_fn or (lambda instrument, lang: instrument.code)
        self._epoch = 0
        self._cancel = None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        head = QHBoxLayout()
        self.heading = label("", "heading", wrap=False)
        # Beside the taller refresh button the heading keeps its text height (its accent bar too).
        head.addWidget(self.heading, 1, Qt.AlignmentFlag.AlignVCenter)
        self.status = label("", "caption", wrap=False)
        head.addWidget(self.status)
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(lambda: self.refresh(manual=True))
        head.addWidget(self.refresh_button)
        layout.addLayout(head)
        self.empty = label("", "muted")
        layout.addWidget(self.empty)
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        layout.addLayout(self.grid)
        self.cards = {}
        self._columns = 0
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(15_000)
        self.poll_timer.timeout.connect(self._poll)
        store.changed.connect(self.sync)
        self.sync()

    # Cards ---------------------------------------------------------------------------------
    def sync(self):
        wanted = {_key(i): i for i in self.store.items()}
        for key in list(self.cards):
            if key not in wanted:
                card = self.cards.pop(key)
                self.grid.removeWidget(card)
                _discard(card)
        for key, instrument in wanted.items():
            if key not in self.cards:
                card = WatchCard(instrument, self.name_fn)
                card.opened.connect(self.open_requested)
                card.removed.connect(self.store.remove)
                self.cards[key] = card
        order = [self.cards[key] for key in wanted]
        self.cards = {key: self.cards[key] for key in wanted}
        self._columns = 0
        self._arrange(order)
        self.render()
        if self.isVisible() and self.auto_load and any(card.attempted_at is None for card in order):
            QTimer.singleShot(0, self.refresh)

    def _arrange(self, order=None):
        order = order if order is not None else list(self.cards.values())
        width = self.width()
        columns = card_columns(width)
        self._columns = columns
        for card in order:
            self.grid.removeWidget(card)
        for index, card in enumerate(order):
            self.grid.addWidget(card, index // columns, index % columns)
        for column in range(4):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = event.size().width()
        columns = card_columns(width)
        if columns != self._columns:
            self._columns = 0
            self._arrange(list(self.cards.values()))

    # Loading -------------------------------------------------------------------------------
    def router(self):
        if self._router is None and self._router_factory is not None:
            self._router = self._router_factory()
        return self._router

    def due(self, now=None):
        now = now or datetime.now(timezone.utc)
        out = []
        for card in self.cards.values():
            if card.attempted_at is None:
                out.append(card.instrument)
                continue
            age = (now - card.attempted_at).total_seconds()
            snapshot = card.result.snapshot if card.result else None
            if card.failures:
                limit = RETRY_SECONDS[min(card.failures, len(RETRY_SECONDS)) - 1]
            else:
                limit = KIS_POLL_SECONDS if snapshot is not None and getattr(snapshot, "source", "") in KIS_SOURCES \
                    else DELAYED_POLL_SECONDS
            if age >= limit:
                out.append(card.instrument)
        return out

    def refresh(self, *, manual=False):
        if self.jobs.busy:
            return False
        instruments = [card.instrument for card in self.cards.values()] if manual else self.due()
        router = self.router()
        if not instruments or router is None:
            return False
        self._epoch += 1
        epoch, cancel = self._epoch, threading.Event()
        self._cancel = cancel
        self.status.setText(_text(self.ctx, "불러오는 중…", "Loading…"))
        return self.jobs.start(lambda: (epoch, load_cards(router, instruments, cancel.is_set)))

    @pyqtSlot(object)
    def _loaded(self, value):
        epoch, results = value
        if epoch != self._epoch:
            return
        now = datetime.now(timezone.utc)
        for result in results:
            card = self.cards.get(_key(result.instrument))
            if card is None:
                continue
            card.attempted_at = now
            if result.snapshot is None:
                card.failures += 1
                if card.result is not None and card.result.snapshot is not None:
                    card.failure = result  # keep the last good chart and say so
                    continue
            else:
                card.failures, card.failure = 0, None
            card.result = result
        self.status.setText("")
        self.render()

    @pyqtSlot(str)
    def _failed(self, code):
        self.status.setText(_text(self.ctx, "조회 실패", "Request failed") + f" ({code})")

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
        self.poll_timer.stop()
        self._epoch += 1
        if self._cancel is not None:
            self._cancel.set()

    # Presentation --------------------------------------------------------------------------
    def set_locale(self, ctx):
        self.ctx = ctx
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.render()

    def render(self):
        ctx = self.ctx
        count = len(self.cards)
        self.heading.setText(_text(ctx, "관심종목", "Watchlist") + (f"  {count}/{self.store.limit}" if count else ""))
        self.refresh_button.setText(_text(ctx, "새로고침", "Refresh"))
        self.refresh_button.setAccessibleName(_text(ctx, "관심종목 새로고침", "Refresh watchlist"))
        # The grid lives on Research Home since 2026-11-11; stocks are added from their screen on Markets.
        self.empty.setText(_text(ctx, "관심종목이 없습니다. 시장에서 종목을 연 뒤 ☆를 눌러 추가하세요.",
                                 "No stocks yet. Open a stock on Markets and press ☆ to add it."))
        self.empty.setVisible(count == 0)
        for card in self.cards.values():
            card.render(ctx, self.dark)


# Codes of other kinds typed in a market's search (the former kind selector, UI-D10): offered, never guessed.
_CODE_PATTERNS = (("domestic_future", "kr", r"[1-4]\d{2}[A-Z0-9]{3,5}"), ("bond", "kr", r"KR[0-9A-Z]{10}"),
                  ("overseas_future", "us", r"[A-Z]{1,3}[FGHJKMNQUVXZ]\d{2}"))


def _code_choices(text, page, lang):
    """(label, Instrument) for each other kind whose code pattern the typed text fits on this market's page."""
    import re
    code = str(text or "").strip().upper()
    out = []
    for kind, where, pattern in _CODE_PATTERNS:
        if where != page or not re.fullmatch(pattern, code):
            continue
        if kind == "domestic_future" and not re.search("[A-Z]", code):
            continue  # six digits are a stock code
        try:
            instrument = Instrument(kind, code)
        except ValueError:
            continue
        name = next(ko if lang == "ko" else en for key, ko, en, _example in KINDS if key == kind)
        out.append((f"{name} {code}", instrument))
    return out


# One stock on one screen ---------------------------------------------------------------------
# Owner 2026-11-11 (UI-D8): the stock's screen is quantgen_desktop.stock_detail (a chart that fills the screen,
# the period bar, and one scrolling right column); the name StockView is kept for the app and its tests.
from .stock_detail import ProfileSectionPanel, StockDetailView as StockView  # noqa: E402  UI-D8


class MarketsWorkspace(QWidget):
    """One market's page (`market_rankings.RankingBoard`), or one stock's screen.

    Owner ruling UI-D10 (2026-11-11): one page per market (`MARKET_PAGES`: 국내 주식, 미국 주식, 크립토, and since
    UI-D11 국내 ETF, 미국 ETF), opened with `show_market(key)`; the ranking categories are that market's own chips
    and search
    criteria. The page has no title, description or separate search card: its header row carries the market's
    name, data state and a search scoped to the market (`search`), which narrows the list as it is typed and on
    Enter opens the one stock it names (the list's, or any stock of that market in the symbol directory).
    """
    # The shown list's RANKING_CATEGORIES key when it changes (chips inside the page too), and "" when a
    # stock's screen replaces the list. Kept for callers of the category sub-menu (UI-D7).
    category_changed = pyqtSignal(str)
    # The shown market's MARKET_PAGES key when it changes; the rail's sub-menu highlight follows it.
    market_changed = pyqtSignal(str)

    def __init__(self, chart, *, store, directory=None, directory_loader=None, ranking_loader=None,
                 profile_loader=None, summary_loader=None, locale=None, auto_load=True):
        super().__init__()
        from .market_rankings import RankingBoard
        self.ctx = locale or LocaleContext("ko_KR")
        self.store, self.directory, self.chart = store, directory, chart
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.pages = CurrentPageStack()
        name_fn = self.display_name
        self.rankings = RankingBoard(loader=ranking_loader, locale=self.ctx, auto_load=auto_load,
                                     summary_loader=summary_loader)
        self.rankings.open_requested.connect(self.open_instrument)
        self.rankings.listing_requested.connect(self._open_other)
        self.rankings.category_changed.connect(self.category_changed)
        self.rankings.page_changed.connect(self.market_changed)
        self.rankings.page_changed.connect(self._remember_stock_market)
        self.rankings.others_fn = self._others
        self._stock_market = "kr"   # the stock market a search for stocks returns to from the coin page
        self.search = self.rankings.search
        self.search.returnPressed.connect(self.submit)
        self.rankings.search_submitted.connect(self.submit)  # Enter in the pinned bar's search
        self.message = self.rankings.message
        # The directory's code-or-name matching, without its popup: the list narrows in place, and stocks of
        # this market outside the list are offered under it (`RankingBoard._others`). Focusing the search starts
        # the symbol master download (as before).
        self.completer = attach_symbol_search(self.search, directory, assets=STOCK_ASSETS, locale=self.ctx,
                                              loader=directory_loader)
        self.completer.enabled = False
        self.completer.chosen.connect(self.open_listing)
        if directory_loader is not None:
            directory_loader.loaded.connect(self._directory_loaded)
        self.stock = StockView(chart, store=store, profile_loader=profile_loader, name_fn=name_fn, locale=self.ctx,
                               auto_load=auto_load, directory=directory, directory_loader=directory_loader)
        self.stock.back_requested.connect(self.show_rankings)
        self.stock.open_requested.connect(self.open_instrument)
        self.pages.addWidget(self.rankings)
        self.pages.addWidget(self.stock)
        layout.addWidget(self.pages)
        self.set_locale(self.ctx)

    @property
    def grid(self):
        """The list page. Kept for `ResearchWindow.current_market_pane()`; the watchlist grid is on Home."""
        return self.rankings

    # Names ---------------------------------------------------------------------------------
    def display_name(self, instrument, lang):
        if self.directory is not None and instrument.asset in STOCK_ASSETS:
            listing = self.directory.lookup(instrument.asset, instrument.code, instrument.exchange)
            if listing is not None:
                return listing.label(lang)
        member = _rankings.member_for(instrument)
        if member is not None:
            return member.label("ko" if lang == "ko" else "en")
        return instrument.code

    # Navigation ----------------------------------------------------------------------------
    def show_rankings(self):
        was_stock = self.showing_stock()
        self.pages.setCurrentIndex(0)
        if was_stock:
            self.category_changed.emit(self.rankings.category)
            self.market_changed.emit(self.rankings.page)

    def show_market(self, key):
        """Show one market's page (a MARKET_PAGES key): 국내 주식, 미국 주식, 크립토, 국내 ETF or 미국 ETF.

        An open stock's screen gives way to the list; the market keeps its own criteria from its last visit.
        """
        if key not in MARKET_PAGE_KEYS:
            raise ValueError(f"Unknown market {key!r}")
        self.rankings.set_page(key)
        self.show_rankings()
        self._scroll_to_top()
        return True

    def show_category(self, key):
        """Earlier callers (UI-D7 category sub-menu, Home's 'add to watchlist'): a RANKING_CATEGORIES key ranks the
        shown market's list by it; "search" focuses the search; a MARKET_PAGES key shows that market.

        An open stock's screen gives way to the list; the search keeps whatever page is shown.
        """
        if key in MARKET_PAGE_KEYS:
            return self.show_market(key)
        if key == "search":
            if self.showing_stock():
                # The stock screen locks the page, so the list's search above it cannot be reached: its toolbar
                # search takes the focus instead (a stock chosen there opens in place). Without one the list comes
                # back with its search.
                if self.stock.focus_search():
                    return True
                self.show_rankings()
            return self.focus_search()
        if key not in _rankings.CATEGORY_KEYS:
            raise ValueError(f"Unknown ranking category {key!r}")
        if _screen.category_note(self.rankings.page, key):
            self.rankings.set_page(self._stock_market)  # coins cannot rank by it; the stock market shown last can
        self.rankings.set_category(key)
        self.show_rankings()
        self._scroll_to_top()  # a newly chosen list starts at its first rank
        return True

    def focus_search(self):
        """The list's search for a stock (Home's "add to watchlist", the window's live-chart action). A coin page
        cannot find or open a stock (UI-D10 review: Home's add landed on the coin search), so it gives way to the
        stock market shown last. An ETF page keeps its search: ETFs open like stocks."""
        if self.rankings.page not in STOCK_PAGES:
            self.rankings.set_page(self._stock_market)
        self._scroll_to_top()
        self.search.setFocus(Qt.FocusReason.OtherFocusReason)
        self.search.selectAll()
        return True

    def _remember_stock_market(self, page):
        if page in ("kr", "us"):
            self._stock_market = page

    def _scroll_to_top(self):
        from PyQt6.QtWidgets import QScrollArea
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        if parent is not None:
            parent.verticalScrollBar().setValue(0)

    def current_category(self):
        """The RANKING_CATEGORIES key of the list shown, or None while a stock's screen is shown.
        The first visit shows "value" (trading value)."""
        return None if self.showing_stock() else self.rankings.category

    def current_market(self):
        """The MARKET_PAGES key of the market page: the one shown, or the one a stock's screen was opened over."""
        return self.rankings.page

    def showing_stock(self):
        return self.pages.currentIndex() == 1

    def open_listing(self, listing):
        """A stock chosen from the directory (a suggestion under the search): its code was not typed in the list's
        search as a filter, so the search is cleared."""
        self.search.clear()
        self.open_instrument(Instrument(listing.asset, listing.code, listing.exchange))

    def open_instrument(self, instrument, *, load=True):
        self._say()
        if instrument is None:
            return  # a coin: the stock screen has no instrument for it
        was_stock = self.showing_stock()
        # The stock's screen first, then the market page under it follows the stock (so Back returns to its
        # market's list): switched while hidden, the list starts no fetch behind the stock screen (UI-D10
        # review); it loads when Back shows it.
        self.pages.setCurrentIndex(1)
        pages = ASSET_PAGES.get(instrument.asset, ())
        if pages and self.rankings.page not in pages:  # an ETF opened from an ETF page keeps that page under it
            member = _rankings.member_for(instrument)
            self.rankings.set_page(member.group if member is not None and member.group in pages else pages[0])
        self.stock.show_instrument(instrument, load=load)
        if not was_stock:
            self.category_changed.emit("")

    def submit(self):
        """Enter in the search: open the one stock the text names, else leave the answer to the page.

        In order: the list's single row; the single stock of this market's curated list the text names (whether
        or not its quote is loaded or passes the criteria: `Screen.members`, UI-D10 review); when the list has
        none by that name, a directory match in this market, a six-digit domestic code, the single stock of
        another market's curated list, or a directory match in the other stock markets (as the earlier "종목
        검색" did). Several names, a coin, or a name the criteria leave out: the narrowed list and its empty
        state say why. A code of another kind (derivatives, bonds) is offered under the list, never guessed."""
        text = self.search.text().strip()
        if not text:
            return
        board, page = self.rankings, self.rankings.page
        shown = [row.record.member for row in board.ranked]
        if len(shown) == 1 and shown[0].instrument is not None:
            self.open_instrument(shown[0].instrument)
            return
        named = board.screen.members()
        if len(named) > 1:  # '카카오' names 카카오 itself among 카카오뱅크 and 카카오페이
            from core.search_text import normal
            wanted = normal(text)
            exact = [m for m in named if wanted in {normal(m.name_ko), normal(m.name_en), normal(m.code)}]
            named = exact if len(exact) == 1 else named
        if named:
            if len(named) == 1 and named[0].instrument is not None:
                self.open_instrument(named[0].instrument)
            return  # several, a coin, or one the criteria leave out: the list and its empty state answer
        if replace(board.screen, sub="", sector="").members():
            return  # the market has it outside the sub-market or sector chosen: the empty state says so
        own = PAGE_ASSETS.get(page, ())
        other = tuple(asset for asset in STOCK_ASSETS if asset not in own)
        listing = self.directory.resolve(text, assets=own) if own and self.directory is not None else None
        if listing is not None:
            self.open_listing(listing)
            return
        code = text.upper()
        if code.isdigit() and len(code) == 6:
            self.search.clear()
            self.open_instrument(Instrument("domestic_stock", code))
            return
        if board._others():
            return  # the suggestions under the search are the answer
        elsewhere = [member for each in MARKET_PAGE_KEYS if each != page
                     for member in _screen.Screen(each, text=text).members()]
        if len(elsewhere) == 1 and elsewhere[0].instrument is not None:
            self.search.clear()
            self.open_instrument(elsewhere[0].instrument)  # its screen, and Back to its market's list
            return
        if elsewhere:
            return  # the '…에서 보기' pointers under the search are the answer
        listing = self.directory.resolve(text, assets=other) if self.directory is not None else None
        if listing is not None:
            self.open_listing(listing)  # the stock is in the other market: its screen, and Back to that list
            return
        self._say("no_coin" if page == "crypto" else "not_found", text=text)

    def _open_other(self, payload):
        if isinstance(payload, Instrument):
            self.search.clear()
            self.open_instrument(payload)
        else:
            self.open_listing(payload)

    def _others(self, text, page):
        """What the search text names outside the list: stocks of this market in the symbol directory, and a code
        of another kind (국내 파생, 해외 파생, 채권) offered as an explicit choice, never guessed: (label, payload)."""
        if page == "crypto":
            return []
        lang = "ko" if self.ctx.language == "ko" else "en"
        out = list(_code_choices(text, page, lang))
        if self.directory is None:
            return out
        assets = PAGE_ASSETS.get(page, ("overseas_stock",))
        rows = self.directory.search(text, limit=12, assets=assets)
        for listing in rows:
            kind = getattr(listing, "kind", "stock")
            if listing.asset == "overseas_stock":
                # 미국 주식's search also reaches the other overseas listings the earlier search opened (TSE, HKS).
                tail = "" if listing.exchange in US_EXCHANGES else f" · {listing.exchange}"
            else:
                tail = "" if kind in ("stock", "") else " · " + (_KIND_KO if lang == "ko" else _KIND_EN).get(kind, kind)
            out.append((f"{listing.label(lang)} {listing.code}{tail}", listing))
        return out

    def _directory_loaded(self, _added):
        if self.directory is not None and getattr(self.directory, "error", None):
            self._say("directory_failed")
        elif self.rankings.query and not self.showing_stock():
            self.rankings.render()  # the suggestions under the search can now name more stocks

    def _say(self, key=None, **fields):
        """A message under the search, as a PAGE_TEXT key (re-rendered in the new language on a switch)."""
        self.rankings.say(key, **fields)

    # Presentation --------------------------------------------------------------------------
    def set_locale(self, ctx):
        self.ctx = ctx
        self.completer.set_locale(ctx)
        self.rankings.set_locale(ctx)
        self.stock.set_locale(ctx)

    def set_theme(self, dark):
        self.rankings.set_theme(dark)
        self.stock.set_theme(dark)

    def stop(self):
        self.rankings.stop()
        self.rankings.summary.stop()
        self.stock.stop()


__all__ = ["WatchlistStore", "WatchlistGrid", "WatchCard", "StockView", "MarketsWorkspace", "SymbolCompleter",
           "DirectoryLoader", "attach_symbol_search", "load_cards", "set_tone", "WATCHLIST_KEY", "WATCHLIST_LIMIT",
           "RANKING_CATEGORIES", "MARKET_PAGES", "MARKET_PAGE_KEYS"]
