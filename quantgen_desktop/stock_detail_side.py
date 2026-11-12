"""The stock detail view's right column (owner layout ruling 2026-11-11, UI-D8).

Owner: "그냥 좌측에 존나큰차트 존나크게, 이런 공간 부족해서 스크롤이 필요한 메뉴들은 오른쪽으로 빼서 간소화" and
"오른쪽의 스크롤 필요한 메뉴들은 움직이는거고, 차트쪽은 스크롤로 위아래 이동이 안되는거야. 오른쪽만 움직이는거지 스크롤이".
One fixed-width column, the only part of the screen that scrolls: a compact watchlist with folding groups, the
symbol card (big price, change, an honest market state, volume against its 30-session average, the 52-week bar),
"지금 이 차트" (four plain readings), then folding sections that show 3-4 figures each with the rest behind
"더 보기", and one muted line naming what this screen does not provide. A second page holds the indicator picker.
"""
from __future__ import annotations

from datetime import datetime, timezone
import threading

from PyQt6.QtCore import QPointF, QRectF, QSize, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (QBoxLayout, QFrame, QGridLayout, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy,
                             QStackedWidget, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.theme import DARK, LIGHT
from .company_identity import CompanyMark
from .jobs import Jobs
from .stock_detail_style import ElidedLabel, chevron, label, numbers, set_prop, text

FOLD_VISIBLE = 4          # owner: each section shows 3-4 key figures, the rest folded
WATCH_VISIBLE = 6
RECENT_LIMIT = 8


def _lang(ctx):
    return "ko" if getattr(ctx, "language", "ko") == "ko" else "en"


class FoldHeader(QFrame):
    """A 40px header that folds its section with the bundled chevron; Space or Enter toggles it too."""
    toggled = pyqtSignal(bool)

    def __init__(self, *, title_sd="foldTitle", height=40):
        super().__init__()
        self.setProperty("sd", "foldHead")
        self.setFixedHeight(height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.is_open, self.dark = True, False
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 0, 8, 0)
        row.setSpacing(8)
        self.arrow = label()
        self.arrow.setFixedSize(16, 16)
        row.addWidget(self.arrow, 0, Qt.AlignmentFlag.AlignVCenter)
        self.title = label(title_sd)
        row.addWidget(self.title, 0, Qt.AlignmentFlag.AlignVCenter)
        self.count = label("foldCount")
        row.addWidget(self.count, 0, Qt.AlignmentFlag.AlignVCenter)
        # The digest takes all the room after the title (right-aligned), so it is cut only when it must be.
        self.digest = ElidedLabel("digest", align=Qt.AlignmentFlag.AlignRight)
        row.addWidget(self.digest, 1)
        self._paint_arrow()

    def set_open(self, is_open):
        self.is_open = bool(is_open)
        self._paint_arrow()
        self.setAccessibleName(self.title.text() + (" ▲" if self.is_open else " ▼"))

    def set_theme(self, dark):
        self.dark = bool(dark)
        self._paint_arrow()

    def _paint_arrow(self):
        self.arrow.setPixmap(chevron("down" if self.is_open else "right", self.dark).pixmap(14, 14))

    def toggle(self):
        self.set_open(not self.is_open)
        self.toggled.emit(self.is_open)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.toggle()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.toggle()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            set_prop(self, "focusRing", True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        set_prop(self, "focusRing", False)


class FoldSection(QWidget):
    """A titled fold: up to FOLD_VISIBLE rows shown, the rest behind '더 보기'. Rows are ProfileRow-like
    objects (label, value, tone, hint) or ready widgets."""
    toggled = pyqtSignal(str, bool)

    def __init__(self, key):
        super().__init__()
        self.key = key
        self.ctx, self.dark = LocaleContext("ko_KR"), False
        self.expanded = False
        self._entries, self._note = [], ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.head = FoldHeader()
        self.title = self.head.title
        self.head.toggled.connect(self._toggled)
        layout.addWidget(self.head)
        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(30, 2, 8, 8)
        body.setSpacing(6)
        self.rows = QGridLayout()
        self.rows.setHorizontalSpacing(12)
        self.rows.setVerticalSpacing(7)
        self.rows.setColumnStretch(0, 1)
        body.addLayout(self.rows)
        self.more = QPushButton()
        self.more.setProperty("sd", "link")
        self.more.setProperty("qg_literal", True)
        self.more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more.clicked.connect(self._more)
        body.addWidget(self.more, 0, Qt.AlignmentFlag.AlignLeft)
        self.note = label("rowNote", wrap=True)
        body.addWidget(self.note)
        layout.addWidget(self.body)
        self._widgets = []   # what the grid shows now
        self._made = []      # row labels this section created (rebuilt on each fill)

    def set_title(self, title):
        self.title.setText(title)
        self.head.set_open(self.head.is_open)

    def set_open(self, is_open):
        self.head.set_open(is_open)
        self.body.setVisible(is_open)
        self._digest()

    @property
    def is_open(self):
        return self.head.is_open

    def _toggled(self, is_open):
        self.body.setVisible(is_open)
        self._digest()
        self.toggled.emit(self.key, is_open)

    def _more(self):
        self.expanded = not self.expanded
        self._fill()

    def set_rows(self, entries, *, note="", ctx=None, dark=None):
        """Replace the rows. Widget entries marked `sdOwned` belong to this section from here on: they are
        deleted when a later set_rows drops them, never while they are still entries (folding and '더 보기'
        only hide and show them)."""
        if ctx is not None:
            self.ctx = ctx
        if dark is not None:
            self.dark = bool(dark)
        from PyQt6 import sip
        entries = list(entries)
        for old in self._entries:
            if isinstance(old, QWidget) and not sip.isdeleted(old) and not any(old is entry for entry in entries):
                self.rows.removeWidget(old)
                old.hide()
                if old.property("sdOwned"):
                    old.setParent(None)
                    old.deleteLater()
        self._entries, self._note = entries, note
        self._fill()

    def _fill(self):
        # Row labels made here are rebuilt on every fill; widget entries are only taken out of the grid.
        for widget in self._made:
            self.rows.removeWidget(widget)
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        self._made = []
        from PyQt6 import sip
        self._entries = [entry for entry in self._entries if not (isinstance(entry, QWidget) and sip.isdeleted(entry))]
        for entry in self._entries:
            if isinstance(entry, QWidget):
                self.rows.removeWidget(entry)
                entry.hide()
        self._widgets = []
        lang = _lang(self.ctx)
        shown = self._entries if self.expanded else self._entries[:FOLD_VISIBLE]
        for index, entry in enumerate(shown):
            if isinstance(entry, QWidget):
                self.rows.addWidget(entry, index, 0, 1, 2)
                entry.show()
                self._widgets.append(entry)
                continue
            name = label("rowLabel", wrap=True)
            name.setText(entry.label)
            value = numbers(label("rowValue"))
            value.setText(entry.value)
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if entry.tone in ("up", "down"):
                value.setProperty("tone", entry.tone)
            if entry.hint:
                name.setToolTip(entry.hint)
                value.setToolTip(entry.hint)
            self.rows.addWidget(name, index, 0)
            self.rows.addWidget(value, index, 1)
            self._widgets += [name, value]
            self._made += [name, value]
        extra = len(self._entries) - FOLD_VISIBLE
        self.more.setVisible(extra > 0)
        self.more.setText(text(lang, "less") if self.expanded else text(lang, "more", count=extra))
        self.note.setText(self._note)
        self.note.setVisible(bool(self._note) and (self.expanded or extra <= 0))
        self._digest()

    def _digest(self):
        """Up to two figures on the folded header, so a closed section still says something; the label elides
        its end, never its start, and drops the second figure first when both do not fit."""
        if self.head.is_open or not self._entries:
            self.head.digest.set_choices(())
            return
        values = [e for e in self._entries if not isinstance(e, QWidget)][:2]
        parts = [f"{e.label} {e.value}" for e in values]
        self.head.digest.set_choices([" · ".join(parts[:n]) for n in range(len(parts), 0, -1)])

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.head.set_theme(dark)


# Watchlist ------------------------------------------------------------------------------------
class WatchRow(QFrame):
    opened = pyqtSignal(object)

    def __init__(self, instrument):
        super().__init__()
        self.instrument = instrument
        self.setProperty("sd", "watchRow")
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(10)
        self.mark = CompanyMark(instrument.code, size=26)
        row.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(0)
        names.setContentsMargins(0, 0, 0, 0)
        self.name = label("watchName")
        self.name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.code = label("watchCode")
        names.addWidget(self.name)
        names.addWidget(self.code)
        row.addLayout(names, 1)
        figures = QVBoxLayout()
        figures.setSpacing(1)
        figures.setContentsMargins(0, 0, 0, 0)
        self.price = numbers(label("watchPrice"))
        self.price.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        line = QHBoxLayout()
        line.setSpacing(4)
        line.addStretch(1)
        self.tag = label("watchTag")
        line.addWidget(self.tag)
        self.change = numbers(label("watchChange"))
        line.addWidget(self.change)
        figures.addWidget(self.price)
        figures.addLayout(line)
        row.addLayout(figures)

    def show_result(self, name, result, *, language, dark, current):
        from .markets_view import KIS_SOURCES, _change_text, _price_text, _stale
        self.name.setText(name)
        place = self.instrument.exchange or ("KRX" if self.instrument.asset == "domestic_stock" else "")
        self.code.setText(f"{self.instrument.code} · {place}" if place else self.instrument.code)
        self.mark.set_identity(self.instrument.code, name)
        self.mark.set_theme(DARK if dark else LIGHT)
        self.mark.setVisible(self.instrument.asset in ("domestic_stock", "overseas_stock"))
        snapshot = result.snapshot if result is not None else None
        candles = tuple(getattr(snapshot, "candles", ()) or ())
        tip = f"{name} · {self.instrument.code}"
        if len(candles) >= 1:
            last = candles[-1].close
            pct = (last / candles[-2].close - 1) * 100 if len(candles) > 1 and candles[-2].close else None
            self.price.setText(_price_text(last, self.instrument))
            change, tone = _change_text(pct)
            self.change.setText(change or "—")
            set_prop(self.change, "tone", tone or "")
            source = str(getattr(snapshot, "source", ""))
            tags = []
            if source not in KIS_SOURCES:
                tags.append(text(language, "delayed_tag"))
            if _stale(snapshot):
                tags.append(text(language, "stale_tag"))
            self.tag.setText(" · ".join(tags))
            self.tag.setVisible(bool(tags))
            tip = text(language, "row_tip", name=name, code=self.instrument.code, source=source,
                       date=str(candles[-1].timestamp)[:10])
        else:
            self.price.setText("—")
            self.change.setText("")
            self.change.setVisible(False)
            self.tag.setVisible(False)
        self.change.setVisible(bool(self.change.text()))
        self.setToolTip(tip)
        self.setAccessibleName(f"{name} {self.price.text()} {self.change.text()}")
        set_prop(self, "current", "true" if current else "false")

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


class WatchGroup(QWidget):
    opened = pyqtSignal(object)

    def __init__(self, key):
        super().__init__()
        self.key = key
        self.show_all = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.head = FoldHeader(height=36)
        self.head.toggled.connect(lambda is_open: self.body.setVisible(is_open))
        layout.addWidget(self.head)
        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(0, 0, 0, 2)
        body.setSpacing(1)
        self.list = QVBoxLayout()
        self.list.setSpacing(1)
        body.addLayout(self.list)
        self.empty = label("small", wrap=True)
        self.empty.setContentsMargins(30, 2, 4, 4)
        body.addWidget(self.empty)
        self.all_button = QPushButton()
        self.all_button.setProperty("sd", "link")
        self.all_button.setProperty("qg_literal", True)
        self.all_button.clicked.connect(self._toggle_all)
        body.addWidget(self.all_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.body)
        self.rows = {}

    def _toggle_all(self):
        self.show_all = not self.show_all
        self.parent_render()

    def parent_render(self):
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, CompactWatchlist):
            parent = parent.parentWidget()
        if parent is not None:
            parent.render()

    def set_open(self, is_open):
        self.head.set_open(is_open)
        self.body.setVisible(is_open)

    def show_items(self, items, *, names, results, language, dark, current, empty_text):
        from .markets_view import _key
        wanted = {_key(i): i for i in items}
        for key in list(self.rows):
            if key not in wanted:
                row = self.rows.pop(key)
                self.list.removeWidget(row)
                row.hide()
                row.setParent(None)
                row.deleteLater()
        for index, (key, instrument) in enumerate(wanted.items()):
            row = self.rows.get(key)
            if row is None:
                row = WatchRow(instrument)
                row.opened.connect(self.opened)
                self.rows[key] = row
            self.list.removeWidget(row)
            self.list.insertWidget(index, row)
            row.show_result(names(instrument), results.get(key), language=language, dark=dark,
                            current=current is not None and key == _key(current))
            row.setVisible(self.show_all or index < WATCH_VISIBLE)
        self.head.count.setText(str(len(items)))
        self.empty.setText(empty_text)
        self.empty.setVisible(not items)
        extra = len(items) - WATCH_VISIBLE
        self.all_button.setVisible(extra > 0)
        self.all_button.setText(text(language, "show_less") if self.show_all else
                                text(language, "show_all", count=len(items)))


class CompactWatchlist(QWidget):
    """The user's watchlist (shared store) and the stocks opened this session, as 46px rows.

    Prices come from `markets_view.load_cards` (daily adjusted closes) on the view's own worker, paced like
    Home's cards; nothing loads unless the column is visible with automatic loading on."""
    open_requested = pyqtSignal(object)

    def __init__(self, store, *, name_fn, router_factory=None, auto_load=True, locale=None):
        super().__init__()
        self.store, self.name_fn = store, name_fn
        self.router_factory, self._router = router_factory, None
        self.auto_load = auto_load
        self.ctx, self.dark = locale or LocaleContext("ko_KR"), False
        self.current = None
        self.recent = []
        self.results, self.attempted, self.failures = {}, {}, {}
        self._epoch, self._cancel = 0, None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(lambda code: None)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.watch = WatchGroup("watch")
        self.recent_group = WatchGroup("recent")
        for group in (self.watch, self.recent_group):
            group.opened.connect(self.open_requested)
            layout.addWidget(group)
        self.recent_group.set_open(False)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(15_000)
        self.poll_timer.timeout.connect(self._poll)
        store.changed.connect(self.sync)
        self.render()

    def router(self):
        if self._router is None and self.router_factory is not None:
            self._router = self.router_factory()
        return self._router

    def set_current(self, instrument):
        from .markets_view import _key
        self.current = instrument
        if instrument is not None:
            self.recent = [i for i in self.recent if _key(i) != _key(instrument)]
            self.recent.insert(0, instrument)
            self.recent = self.recent[:RECENT_LIMIT]
        self.render()
        if self.isVisible() and self.auto_load:
            QTimer.singleShot(0, self.refresh)

    def items(self):
        from .markets_view import _key
        seen, out = set(), []
        for instrument in [*self.store.items(), *self.recent]:
            if _key(instrument) not in seen:
                seen.add(_key(instrument))
                out.append(instrument)
        return out

    def due(self, now=None):
        from .markets_view import DELAYED_POLL_SECONDS, KIS_POLL_SECONDS, KIS_SOURCES, RETRY_SECONDS, _key
        now = now or datetime.now(timezone.utc)
        out = []
        for instrument in self.items():
            key = _key(instrument)
            at = self.attempted.get(key)
            if at is None:
                out.append(instrument)
                continue
            result = self.results.get(key)
            snapshot = result.snapshot if result is not None else None
            failures = self.failures.get(key, 0)
            if failures:
                limit = RETRY_SECONDS[min(failures, len(RETRY_SECONDS)) - 1]
            else:
                limit = KIS_POLL_SECONDS if getattr(snapshot, "source", "") in KIS_SOURCES else DELAYED_POLL_SECONDS
            if (now - at).total_seconds() >= limit:
                out.append(instrument)
        return out

    def refresh(self, *, manual=False):
        from .markets_view import load_cards
        if self.jobs.busy:
            return False
        instruments = self.items() if manual else self.due()
        router = self.router()
        if not instruments or router is None:
            return False
        self._epoch += 1
        epoch, cancel = self._epoch, threading.Event()
        self._cancel = cancel
        return self.jobs.start(lambda: (epoch, load_cards(router, instruments, cancel.is_set)))

    @pyqtSlot(object)
    def _loaded(self, value):
        from .markets_view import _key
        epoch, results = value
        if epoch != self._epoch:
            return
        now = datetime.now(timezone.utc)
        for result in results:
            key = _key(result.instrument)
            self.attempted[key] = now
            if result.snapshot is None:
                self.failures[key] = self.failures.get(key, 0) + 1
                if key in self.results:
                    continue
            else:
                self.failures[key] = 0
            self.results[key] = result
        self.render()

    def _poll(self):
        if self.isVisible() and self.auto_load:
            self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if self.auto_load:
            self.poll_timer.start()
            QTimer.singleShot(0, self.refresh)

    def hideEvent(self, event):
        # A running batch stops after its current card (load_cards checks between cards); what it loaded is kept
        # and the rest is due again when the column shows.
        self.poll_timer.stop()
        if self._cancel is not None:
            self._cancel.set()
        super().hideEvent(event)

    def stop(self):
        self.poll_timer.stop()
        self._epoch += 1
        if self._cancel is not None:
            self._cancel.set()

    def sync(self):
        self.render()
        if self.isVisible() and self.auto_load:
            QTimer.singleShot(0, self.refresh)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.render()

    def set_theme(self, dark):
        self.dark = bool(dark)
        for group in (self.watch, self.recent_group):
            group.head.set_theme(dark)
        self.render()

    def render(self):
        from .markets_view import _key
        lang = _lang(self.ctx)
        names = lambda instrument: self.name_fn(instrument, lang)
        watched = self.store.items()
        keys = {_key(i) for i in watched}
        recent = [i for i in self.recent if _key(i) not in keys]
        self.watch.head.title.setText(text(lang, "watch_group"))
        self.watch.head.count.setText(f"{len(watched)}/{self.store.limit}")
        self.recent_group.head.title.setText(text(lang, "recent_group"))
        self.watch.show_items(watched, names=names, results=self.results, language=lang, dark=self.dark,
                              current=self.current, empty_text=text(lang, "watch_empty"))
        self.watch.head.count.setText(f"{len(watched)}/{self.store.limit}")
        self.recent_group.show_items(recent, names=names, results=self.results, language=lang, dark=self.dark,
                                     current=self.current, empty_text=text(lang, "recent_empty"))
        for group in (self.watch, self.recent_group):
            group.head.set_open(group.head.is_open)


# Symbol card ----------------------------------------------------------------------------------
class RangeBar(QWidget):
    """52-week closes: a track from low to high with a dot at the last close."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(16)
        self.position, self.colors = None, ("#E2E3DB", "#194C40", "#646E68")

    def set_value(self, position, colors):
        self.position, self.colors = position, colors
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track, accent, muted = (QColor(c) for c in self.colors)
        y = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, y - 3, self.width(), 6), 3, 3)
        if self.position is not None:
            x = 6 + max(0.0, min(1.0, self.position)) * (self.width() - 12)
            p.setBrush(accent)
            p.drawRoundedRect(QRectF(0, y - 3, x, 6), 3, 3)
            p.setBrush(QColor("#FFFFFF"))
            p.setPen(QPen(accent, 2))
            p.drawEllipse(QPointF(x, y), 5.5, 5.5)
        p.end()


class VolumeBar(QWidget):
    """Volume against its average: 0 to 2x with a tick at 1x; past 2x the fill is capped."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(12)
        self.ratio, self.colors = None, ("#E2E3DB", "#194C40", "#646E68")

    def set_value(self, ratio, colors):
        self.ratio, self.colors = ratio, colors
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track, accent, muted = (QColor(c) for c in self.colors)
        y = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, y - 3, self.width(), 6), 3, 3)
        if self.ratio is not None:
            p.setBrush(accent)
            p.drawRoundedRect(QRectF(0, y - 3, min(1.0, self.ratio / 2) * self.width(), 6), 3, 3)
        p.setPen(QPen(muted, 1.5))
        p.drawLine(QPointF(self.width() / 2, 0), QPointF(self.width() / 2, self.height()))
        p.end()


class SymbolCard(QWidget):
    """Big price, change, state, volume against the 30-session average and the 52-week bar."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        head = QHBoxLayout()
        head.setSpacing(8)
        self.name = label("cardTitle")
        self.name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        head.addWidget(self.name, 1)
        self.sector = label("sector")
        head.addWidget(self.sector)
        layout.addLayout(head)
        # Price and change sit on one line when the column has room and the change drops under the price when it
        # does not: a seven-digit won price beside its change ('1,255,000  ▼ −22,000 (−1.72%)') is wider than a
        # 300-330 px column, and the column then shifted sideways and cut both edges (owner's PC, 2026-11-12).
        self.figures = figures = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        figures.setSpacing(10)
        self.price = numbers(label("price", selectable=True))
        figures.addWidget(self.price, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.change = numbers(label("change"))
        figures.addWidget(self.change, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        figures.addStretch(1)
        layout.addLayout(figures)
        self.state = label("state", wrap=True)
        layout.addWidget(self.state)
        self.qscore = label("qscore")
        self.qscore.hide()
        layout.addWidget(self.qscore, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(6)
        volume = QHBoxLayout()
        self.volume = numbers(label("body"))
        volume.addWidget(self.volume)
        volume.addStretch(1)
        self.volume_ratio = numbers(label("small"))
        volume.addWidget(self.volume_ratio)
        layout.addLayout(volume)
        self.volume_bar = VolumeBar()
        layout.addWidget(self.volume_bar)
        layout.addSpacing(6)
        self.range_title = label("small")
        layout.addWidget(self.range_title)
        self.range_bar = RangeBar()
        layout.addWidget(self.range_bar)
        ends = QHBoxLayout()
        self.range_low = numbers(label("small"))
        self.range_high = numbers(label("small"))
        self.range_high.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ends.addWidget(self.range_low)
        ends.addStretch(1)
        ends.addWidget(self.range_high)
        layout.addLayout(ends)
        self.range_from = numbers(label("body", wrap=True))
        layout.addWidget(self.range_from)

    def minimumSizeHint(self):
        # The figures may stack, so the card asks only for its widest single figure, never for both side by side.
        hint = super().minimumSizeHint()
        margins = self.layout().contentsMargins()
        widest = max(self.price.sizeHint().width(), self.change.sizeHint().width()) + margins.left() + margins.right()
        return QSize(min(hint.width(), max(widest, 160)), hint.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_figures()

    def _fit_figures(self):
        margins = self.layout().contentsMargins()
        room = self.width() - margins.left() - margins.right()
        need = self.price.sizeHint().width() + self.figures.spacing() + self.change.sizeHint().width()
        direction = QBoxLayout.Direction.LeftToRight if need <= room else QBoxLayout.Direction.TopToBottom
        if self.figures.direction() != direction:
            self.figures.setDirection(direction)
            self.figures.setSpacing(10 if direction == QBoxLayout.Direction.LeftToRight else 4)


class NowRow(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.study = ""
        self.setProperty("sd", "nowRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 6, 6, 6)
        row.setSpacing(10)
        self.topic = label("topic")
        self.topic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.topic.setFixedWidth(64)
        row.addWidget(self.topic, 0, Qt.AlignmentFlag.AlignTop)
        # The reading's first sentence, then what it means in a quieter line (owner R-D9-3: no walls of text).
        lines = QVBoxLayout()
        lines.setContentsMargins(0, 0, 0, 0)
        lines.setSpacing(3)
        self.sentence = numbers(label("body", wrap=True))
        lines.addWidget(self.sentence)
        self.detail = numbers(label("nowDetail", wrap=True))
        lines.addWidget(self.detail)
        row.addLayout(lines, 1)

    def set_reading(self, value):
        import re
        parts = re.split(r"(?<=[.])\s+", str(value or ""), maxsplit=1)
        self.sentence.setText(parts[0])
        self.detail.setText(parts[1] if len(parts) > 1 else "")
        self.detail.setVisible(len(parts) > 1)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.study:
            self.clicked.emit(self.study)
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space) and self.study:
            self.clicked.emit(self.study)
            return
        super().keyPressEvent(event)


class NowCard(QWidget):
    """'지금 이 차트': four plain readings of the latest candle (trend, strength, movement, trading)."""
    study_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        head = QVBoxLayout()
        head.setContentsMargins(6, 0, 6, 2)
        head.setSpacing(1)
        self.title = label("cardTitle")
        self.caption = label("small")
        head.addWidget(self.title)
        head.addWidget(self.caption)
        layout.addLayout(head)
        self.rows = []
        for _ in range(4):
            row = NowRow()
            row.clicked.connect(self.study_requested)
            layout.addWidget(row)
            self.rows.append(row)
        self.disclaimer = label("small", wrap=True)
        self.disclaimer.setContentsMargins(6, 2, 6, 0)
        layout.addWidget(self.disclaimer)


def rule():
    line = QFrame()
    line.setProperty("sd", "rule")
    return line


class RightColumn(QFrame):
    """The one scrolling column: page 0 the stock (watchlist, card, readings, sections), page 1 the indicators."""
    page_changed = pyqtSignal(int)

    def __init__(self, *, store, name_fn, router_factory=None, auto_load=True, locale=None):
        super().__init__()
        self.setObjectName("sdSide")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 6, 6)
        layout.setSpacing(8)
        segment = QFrame()
        segment.setObjectName("sdSegment")
        seg = QHBoxLayout(segment)
        seg.setContentsMargins(3, 3, 3, 3)
        seg.setSpacing(3)
        self.stock_tab, self.indicators_tab = QPushButton(), QPushButton()
        for index, button in enumerate((self.stock_tab, self.indicators_tab)):
            button.setProperty("sd", "seg")
            button.setProperty("qg_literal", True)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.set_page(i))
            seg.addWidget(button, 1)
        layout.addWidget(segment)
        layout.setContentsMargins(10, 10, 4, 6)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)
        self.stock_scroll, self.stock_page = self._scroll()
        self.indicator_scroll, self.indicator_page = self._scroll()
        self.pages.addWidget(self.stock_scroll)
        self.pages.addWidget(self.indicator_scroll)
        body = QVBoxLayout(self.stock_page)
        body.setContentsMargins(2, 4, 10, 16)
        body.setSpacing(12)
        self.watchlist = CompactWatchlist(store, name_fn=name_fn, router_factory=router_factory,
                                          auto_load=auto_load, locale=locale)
        body.addWidget(self.watchlist)
        body.addWidget(rule())
        self.card = SymbolCard()
        body.addWidget(self.card)
        body.addWidget(rule())
        self.now = NowCard()
        body.addWidget(self.now)
        self.now_rule = rule()
        body.addWidget(self.now_rule)
        self.profile_status = label("small", wrap=True)
        self.profile_status.setContentsMargins(6, 0, 6, 0)
        body.addWidget(self.profile_status)
        self.retry_button = QPushButton()
        self.retry_button.setProperty("sd", "link")
        self.retry_button.setProperty("qg_literal", True)
        self.retry_button.hide()
        body.addWidget(self.retry_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.sections = {}
        for key in ("key_figures", "range", "risk", "technical", "supply"):
            section = FoldSection(key)
            section.set_open(key in ("key_figures", "technical"))
            self.sections[key] = section
            body.addWidget(section)
        self.unavailable = label("small", wrap=True)
        self.unavailable.setContentsMargins(6, 6, 6, 0)
        body.addWidget(self.unavailable)
        body.addStretch(1)
        self.indicator_layout = QVBoxLayout(self.indicator_page)
        self.indicator_layout.setContentsMargins(2, 4, 10, 16)
        self.indicator_layout.setSpacing(0)
        self.set_page(0)

    def _scroll(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        page.setObjectName("sdPage")
        scroll.setWidget(page)
        # The column never moves sideways: a focused row or a selected price label asking to be made visible
        # used to scroll a page wider than the column, so both edges were cut and no scroll bar showed why.
        bar = scroll.horizontalScrollBar()
        bar.rangeChanged.connect(lambda *_: bar.setValue(0))
        bar.valueChanged.connect(lambda value: bar.setValue(0) if value else None)
        return scroll, page

    def set_page(self, index):
        self.pages.setCurrentIndex(index)
        self.stock_tab.setChecked(index == 0)
        self.indicators_tab.setChecked(index == 1)
        self.page_changed.emit(index)

    def current_scroll(self):
        return self.pages.currentWidget()


__all__ = ["FoldHeader", "FoldSection", "CompactWatchlist", "WatchRow", "SymbolCard", "RangeBar", "VolumeBar",
           "NowCard", "RightColumn"]
