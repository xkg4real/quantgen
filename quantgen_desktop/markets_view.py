"""Markets workspace (owner request, 2026-11-04): watchlist charts and one screen per stock.

Replaces the UI-7 indicator board and the UI-8 asset-class tab strip on Markets:

- one search bar takes a stock code or a stock name (Korean, English, 초성) through
  core.market.directory; futures and bonds keep code entry through the kind selector;
- the watchlist the user builds is shown as chart cards (QSettings ``markets/watchlist``);
- choosing a stock opens one screen with its price chart and every profile section
  core.research.stock_profile provides.

Provider and observation-date fields are not shown as columns or lines (owner request).
They stay in tooltips, and delayed, fallback, stale and failed states stay labelled
(docs/compliance/09-dark-patterns.md).
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import date, datetime, timezone

from PyQt6.QtCore import (QAbstractListModel, QByteArray, QModelIndex, QObject, QSize, QTimer, Qt, pyqtSignal,
                          pyqtSlot)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QComboBox, QCompleter, QFrame, QGridLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QSizePolicy, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market.models import ChartRequest, Instrument
from core.theme import DARK, LIGHT
from .company_identity import CompanyMark, company_icon
from .jobs import Jobs
from .tools import CurrentPageStack

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
                self._state(_text(ctx, "시장 화면을 열면 불러옵니다.", "Loads when Markets is shown."))
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
        self.empty.setText(_text(ctx, "관심종목이 없습니다. 위에서 종목을 검색한 뒤 ☆를 눌러 추가하세요.",
                                 "No stocks yet. Search above and press ☆ to add one."))
        self.empty.setVisible(count == 0)
        for card in self.cards.values():
            card.render(ctx, self.dark)


# One stock on one screen ---------------------------------------------------------------------
class ProfileSectionPanel(QFrame):
    def __init__(self):
        super().__init__()
        from .app import label
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        self.title = label("", "heading", wrap=False)
        layout.addWidget(self.title)
        self.rows = QGridLayout()
        self.rows.setHorizontalSpacing(12)
        self.rows.setVerticalSpacing(5)
        self.rows.setColumnStretch(0, 1)
        layout.addLayout(self.rows)
        self.note = label("", "caption")
        layout.addWidget(self.note)
        self._labels = []

    def show_section(self, section):
        from .app import label
        self.title.setText(section.title)
        for widget in self._labels:
            self.rows.removeWidget(widget)
            _discard(widget)
        self._labels = []
        for index, row in enumerate(section.rows):
            name = label(row.label, "muted")
            value = label(row.value, "delta" if row.tone else "", wrap=False)
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if row.tone:
                set_tone(value, row.tone)
            if row.hint:
                name.setToolTip(row.hint)
                value.setToolTip(row.hint)
            self.rows.addWidget(name, index, 0)
            self.rows.addWidget(value, index, 1)
            self._labels += [name, value]
        self.note.setText(section.note)
        self.note.setVisible(bool(section.note))


class StockView(QWidget):
    """Header, the shared price chart and every profile section for one instrument."""
    back_requested = pyqtSignal()
    watch_toggled = pyqtSignal(object, bool)

    def __init__(self, chart, *, store, profile_loader=None, name_fn=None, locale=None, auto_load=True):
        super().__init__()
        from .app import label
        self.chart, self.store = chart, store
        self.profile_loader = profile_loader
        self.name_fn = name_fn or (lambda instrument, lang: instrument.code)
        self.ctx, self.dark, self.auto_load = locale or LocaleContext("ko_KR"), False, auto_load
        self.instrument, self.profile = None, None
        self._epoch = 0
        self._live_price = None
        self._reload, self._job_epoch = False, -1
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._profile_loaded)
        self.jobs.failed.connect(self._profile_failed)
        self.jobs.busy_changed.connect(self._jobs_busy)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        top = QHBoxLayout()
        self.back_button = QPushButton()
        self.back_button.clicked.connect(self.back_requested)
        top.addWidget(self.back_button)
        top.addStretch()
        self.watch_button = QPushButton()
        self.watch_button.setCheckable(True)
        self.watch_button.clicked.connect(self._toggle_watch)
        top.addWidget(self.watch_button)
        layout.addLayout(top)
        header = QHBoxLayout()
        header.setSpacing(12)
        self.mark = CompanyMark("", size=44)
        self.mark.hide()
        header.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(2)
        self.code = label("", "eyebrow", wrap=False)
        self.name = label("", "title", wrap=False)
        names.addWidget(self.code)
        names.addWidget(self.name)
        header.addLayout(names, 1)
        figures = QVBoxLayout()
        figures.setSpacing(2)
        self.price = label("", "number", wrap=False)
        self.price.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.change = label("", "delta", wrap=False)
        self.change.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        figures.addWidget(self.price)
        figures.addWidget(self.change, 0, Qt.AlignmentFlag.AlignRight)
        header.addLayout(figures)
        layout.addLayout(header)
        self.chart_slot = QVBoxLayout()
        self.chart_slot.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.chart_slot)
        self.profile_status = label("", "caption")
        layout.addWidget(self.profile_status)
        self.sections_grid = QGridLayout()
        self.sections_grid.setSpacing(12)
        layout.addLayout(self.sections_grid)
        self.section_panels = []
        self._columns = 0
        chart.snapshot_loaded.connect(self._chart_loaded)
        chart.trade_received.connect(self._chart_tick)
        store.changed.connect(self._sync_watch)
        self.set_locale(self.ctx)

    def adopt_chart(self):
        """Move the shared chart pane into this view (it lives in one place at a time)."""
        if self.chart.parent() is not self:
            self.chart_slot.addWidget(self.chart)
        # The view's header names the instrument; the pane keeps intervals, indicators and live data.
        self.chart.intro.hide()
        self.chart.symbol.hide()
        self.chart.form_labels[1].hide()
        self._fit_form()
        self.chart.show()

    def _fit_form(self):
        # With the code field hidden, keep the interval (and the derivatives market selector) at the left.
        # Changing the chart's asset class resets column 0, so this runs again after set_asset_class.
        form = self.chart._form
        for column in range(3):
            form.setColumnStretch(column, 0)
        form.setColumnStretch(3, 1)

    def show_instrument(self, instrument, *, load=True):
        self.instrument = instrument
        self.profile = None
        self._live_price = None
        self._epoch += 1
        self.adopt_chart()
        if self.chart.asset.currentData() != instrument.asset:
            self.chart.set_asset_class(instrument.asset)
            self._fit_form()
        index = self.chart.exchange.findData(instrument.exchange)
        if index >= 0:
            self.chart.exchange.setCurrentIndex(index)
        self.chart.symbol.setText(instrument.code)
        self._clear_sections()
        self.render_header()
        self._sync_watch()
        self.profile_status.setText("" if instrument.asset in STOCK_ASSETS else
                                    _text(self.ctx, "종목 정보는 주식에만 제공합니다. 차트는 위에 있습니다.",
                                          "Stock details are for stocks only; the chart is above."))
        if load and self.auto_load:
            # Opening a stock loads its chart and details; with automatic refresh off (tests) both
            # stay explicit, exactly like the chart pane's own Load button.
            self.chart.refresh(manual=True)
            self.load_profile()

    def load_profile(self):
        if self.instrument is None or self.profile_loader is None or self.instrument.asset not in STOCK_ASSETS:
            self.profile_status.setText("" if self.instrument is None or self.instrument.asset in STOCK_ASSETS else
                                        _text(self.ctx, "종목 정보는 주식에만 제공합니다. 차트는 위에 있습니다.",
                                              "Stock details are for stocks only; the chart is above."))
            return False
        self.profile_status.setText(_text(self.ctx, "종목 정보를 불러오는 중…", "Loading stock details…"))
        if self.jobs.busy:
            # Another stock's details are still loading; load this one when that job ends.
            self._reload = True
            return False
        self._reload = False
        epoch, instrument, loader = self._epoch, self.instrument, self.profile_loader
        self._job_epoch = epoch
        return self.jobs.start(lambda: (epoch, loader(instrument)))

    @pyqtSlot(bool)
    def _jobs_busy(self, busy):
        # Jobs emits succeeded/failed before it clears its job, so a refused load is retried here.
        if not busy and self._reload and self._job_epoch != self._epoch:
            QTimer.singleShot(0, self.load_profile)

    @pyqtSlot(object)
    def _profile_loaded(self, value):
        epoch, profile = value
        if epoch != self._epoch:
            return  # a newer stock was opened meanwhile; _jobs_busy loads it
        self.profile = profile
        self.profile_status.setText("")
        self.render_header()
        self.render_sections()

    @pyqtSlot(str)
    def _profile_failed(self, code):
        if self._job_epoch != self._epoch:
            return  # the failure belongs to a stock that is no longer open
        self.profile_status.setText(_text(self.ctx, "종목 정보를 불러오지 못했습니다", "Could not load stock details")
                                    + f" ({code})")

    def _chart_loaded(self, snapshot):
        instrument = snapshot.request.instrument
        if self.instrument is None or _key(instrument) != _key(self.instrument):
            return
        quote = getattr(snapshot, "quote", None)
        if quote is not None and quote.price is not None:
            self._live_price = (quote.price, quote.change_pct)
            self.render_header()

    def _chart_tick(self, tick):
        if self.instrument is None or _key(tick.instrument) != _key(self.instrument):
            return
        self._live_price = (tick.price, tick.change_pct)
        self.render_header()

    def _toggle_watch(self):
        if self.instrument is None:
            return
        if self.store.contains(self.instrument):
            self.store.remove(self.instrument)
            self.watch_toggled.emit(self.instrument, False)
        elif self.store.add(self.instrument):
            self.watch_toggled.emit(self.instrument, True)
        self._sync_watch()

    def _sync_watch(self):
        watched = self.instrument is not None and self.store.contains(self.instrument)
        self.watch_button.setChecked(watched)
        full = not watched and self.store.full()
        self.watch_button.setEnabled(self.instrument is not None and not full)
        self.watch_button.setText(("★ " + _text(self.ctx, "관심종목", "Watching")) if watched else
                                  ("☆ " + _text(self.ctx, "관심종목 추가", "Add to watchlist")))
        self.watch_button.setToolTip(_text(self.ctx, f"관심종목은 {self.store.limit}개까지입니다.",
                                           f"Up to {self.store.limit} stocks.") if full else "")

    def render_header(self):
        ctx = self.ctx
        instrument = self.instrument
        if instrument is None:
            self.mark.hide()
            for field in (self.code, self.name, self.price, self.change):
                field.setText("")
            return
        # The directory name (the one on the card) first, so the header does not change name when the
        # details arrive; the profile's name only when the directory does not know the stock.
        name = self.name_fn(instrument, ctx.language)
        if self.profile is not None and name == instrument.code:
            from core.research.stock_profile import display_name
            name = display_name(self.profile, ctx.language) or name
        self.mark.set_identity(instrument.code, name)
        self.mark.setVisible(instrument.asset in STOCK_ASSETS)
        place = instrument.exchange or ("KRX" if instrument.asset == "domestic_stock" else "")
        self.code.setText(f"{instrument.code} · {place}" if place else instrument.code)
        self.name.setText(name)
        price = pct = None
        if self._live_price is not None:
            price, pct = self._live_price
        elif self.profile is not None:
            price, pct = self.profile.last_price, self.profile.change_pct
        self.price.setText(_price_text(price, instrument))
        text, tone = _change_text(pct)
        self.change.setText(text)
        set_tone(self.change, tone)
        self.change.setVisible(bool(text))  # no change, no empty grey pill

    def _clear_sections(self):
        for panel in self.section_panels:
            self.sections_grid.removeWidget(panel)
            _discard(panel)
        self.section_panels = []

    def render_sections(self):
        from core.research.stock_profile import sections
        self._clear_sections()
        if self.profile is None:
            return
        for section in sections(self.profile, self.ctx.language):
            panel = ProfileSectionPanel()
            panel.show_section(section)
            self.section_panels.append(panel)
        self._columns = 0
        self._arrange()

    def _arrange(self):
        columns = 3 if self.width() >= 1060 else 2 if self.width() >= 640 else 1
        if columns == self._columns:
            return
        self._columns = columns
        for panel in self.section_panels:
            self.sections_grid.removeWidget(panel)
        for index, panel in enumerate(self.section_panels):
            self.sections_grid.addWidget(panel, index // columns, index % columns, Qt.AlignmentFlag.AlignTop)
        for column in range(3):
            self.sections_grid.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange()

    def set_locale(self, ctx):
        self.ctx = ctx
        self.back_button.setText("← " + _text(ctx, "관심종목", "Watchlist"))
        self.back_button.setAccessibleName(_text(ctx, "관심종목으로 돌아가기", "Back to watchlist"))
        self._sync_watch()
        self.render_header()
        if self.profile is not None:
            self.render_sections()

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.mark.set_theme(DARK if self.dark else LIGHT)

    def stop(self):
        self._epoch += 1


class MarketsWorkspace(QWidget):
    """Search bar, then either the watchlist cards or one stock's screen."""

    def __init__(self, chart, *, store, directory=None, directory_loader=None, card_router_factory=None,
                 profile_loader=None, locale=None, auto_load=True):
        super().__init__()
        from .app import label
        self.ctx = locale or LocaleContext("ko_KR")
        self.store, self.directory, self.chart = store, directory, chart
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        bar = QFrame()
        bar.setObjectName("panel")
        bar.setProperty("card", "search")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)
        self.kind = QComboBox()
        for key, ko, en, _example in KINDS:
            self.kind.addItem(ko, key)
        self.kind.setAccessibleName("Kind")
        self.kind.currentIndexChanged.connect(self._kind_changed)
        bar_layout.addWidget(self.kind)
        self.search = QLineEdit()
        self.search.setObjectName("marketSearch")
        self.search.setClearButtonEnabled(True)
        self.search.returnPressed.connect(self.submit)
        bar_layout.addWidget(self.search, 1)
        self.open_button = QPushButton()
        self.open_button.setProperty("primary", True)
        self.open_button.clicked.connect(self.submit)
        bar_layout.addWidget(self.open_button)
        layout.addWidget(bar)
        self.message = label("", "caption")
        self.message.hide()
        layout.addWidget(self.message)
        self.completer = attach_symbol_search(self.search, directory, assets=STOCK_ASSETS, locale=self.ctx,
                                              loader=directory_loader)
        self.completer.chosen.connect(self.open_listing)
        if directory_loader is not None:
            directory_loader.loaded.connect(self._directory_loaded)
        self.pages = CurrentPageStack()
        name_fn = self.display_name
        self.grid = WatchlistGrid(store, router_factory=card_router_factory, name_fn=name_fn, locale=self.ctx,
                                  auto_load=auto_load)
        self.grid.open_requested.connect(self.open_instrument)
        self.stock = StockView(chart, store=store, profile_loader=profile_loader, name_fn=name_fn, locale=self.ctx,
                               auto_load=auto_load)
        self.stock.back_requested.connect(self.show_watchlist)
        self.pages.addWidget(self.grid)
        self.pages.addWidget(self.stock)
        layout.addWidget(self.pages)
        self.set_locale(self.ctx)

    # Names ---------------------------------------------------------------------------------
    def display_name(self, instrument, lang):
        if self.directory is not None and instrument.asset in STOCK_ASSETS:
            listing = self.directory.lookup(instrument.asset, instrument.code, instrument.exchange)
            if listing is not None:
                return listing.label(lang)
        return instrument.code

    # Navigation ----------------------------------------------------------------------------
    def show_watchlist(self):
        self.pages.setCurrentIndex(0)

    def showing_stock(self):
        return self.pages.currentIndex() == 1

    def open_listing(self, listing):
        self.open_instrument(Instrument(listing.asset, listing.code, listing.exchange))

    def open_instrument(self, instrument, *, load=True):
        self._say("")
        # The header names the open stock; a leftover query would name another one.
        self.completer.completer.popup().hide()
        self.search.clear()
        self.pages.setCurrentIndex(1)
        self.stock.show_instrument(instrument, load=load)

    def submit(self):
        text = self.search.text().strip()
        if not text:
            return
        kind = self.kind.currentData()
        try:
            if kind == "stock":
                listing = self.directory.resolve(text, assets=STOCK_ASSETS) if self.directory is not None else None
                if listing is not None:
                    self.open_listing(listing)
                    return
                rows = self.completer.results(text)
                if len(rows) == 1:
                    self.open_listing(rows[0])
                    return
                code = text.upper()
                if code.isdigit() and len(code) == 6:
                    self.open_instrument(Instrument("domestic_stock", code))
                    return
                self._say(_text(self.ctx, f"'{text}'와 일치하는 종목을 찾지 못했습니다. 목록에서 고르거나 종목 코드를 입력하세요.",
                                f"No stock matches '{text}'. Pick one from the list or enter its code."))
                if rows:
                    self.completer._edited(text)
                return
            self.open_instrument(Instrument(kind, text.upper()))
        except ValueError:
            self._say(_text(self.ctx, "코드 형식이 맞지 않습니다.", "That code is not valid for this kind."))

    def _directory_loaded(self, _added):
        if self.directory is not None and getattr(self.directory, "error", None):
            self._say(_text(self.ctx, "국내 종목 이름 목록을 불러오지 못했습니다. 국내 종목은 6자리 코드로 검색하세요.",
                            "Could not load the domestic stock names. Search domestic stocks by their 6-digit code."))

    def _say(self, text):
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def _kind_changed(self, *_):
        stock = self.kind.currentData() == "stock"
        self.completer.enabled = stock
        if not stock:
            self.completer.completer.popup().hide()
        self._placeholder()

    def _placeholder(self):
        kind = self.kind.currentData()
        example = next(e for k, _ko, _en, e in KINDS if k == kind)
        self.search.setPlaceholderText(
            _text(self.ctx, "종목 코드나 이름 (예: 005930, 삼성전자, ㅅㅅㅈㅈ, AAPL, 애플)",
                  "Stock code or name (e.g. 005930, Samsung Electronics, AAPL, Apple)") if kind == "stock"
            else _text(self.ctx, f"종목 코드 (예: {example})", f"Code (e.g. {example})"))

    # Presentation --------------------------------------------------------------------------
    def set_locale(self, ctx):
        self.ctx = ctx
        for index, (_key_, ko, en, _example) in enumerate(KINDS):
            self.kind.setItemText(index, ko if ctx.language == "ko" else en)
        self.open_button.setText(_text(ctx, "열기", "Open"))
        self.search.setAccessibleName(_text(ctx, "종목 검색", "Search stocks"))
        self._placeholder()
        self.completer.set_locale(ctx)
        self.grid.set_locale(ctx)
        self.stock.set_locale(ctx)

    def set_theme(self, dark):
        self.grid.set_theme(dark)
        self.stock.set_theme(dark)

    def stop(self):
        self.grid.stop()
        self.stock.stop()


__all__ = ["WatchlistStore", "WatchlistGrid", "WatchCard", "StockView", "MarketsWorkspace", "SymbolCompleter",
           "DirectoryLoader", "attach_symbol_search", "load_cards", "set_tone", "WATCHLIST_KEY", "WATCHLIST_LIMIT"]
