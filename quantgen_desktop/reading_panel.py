"""Local glossary help and opt-in provenance folding. No engines, stores or I/O.

Install once after creating the window's stack: install_reading_help(window).
Call the returned controller.set_locale(ctx) after translating the main page.
Only display widgets are inspected; report sections and numeric values are not
reformatted or used to infer a new financial interpretation.
"""
from __future__ import annotations

import weakref

from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QPushButton, QScrollArea, QTableWidget,
    QToolButton, QToolTip, QVBoxLayout, QWidget,
)

from core.education import glossary
from core.i18n import LocaleContext
from .localization import CAPTION_ROLE
from .reading_language import text


def _label(value=''):
    widget = QLabel(value)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return widget


class DetailsFold(QWidget):
    """Contains only content the caller explicitly marks as pure provenance."""
    def __init__(self, ctx=None):
        super().__init__()
        self.ctx = ctx or LocaleContext('en_US')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.toggle = QToolButton()
        self.toggle.setCheckable(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.toggled.connect(self._toggled)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.body)
        self._toggled(False)
        self.set_locale(self.ctx)

    def _toggled(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)

    def add_widget(self, widget):
        self.body_layout.addWidget(widget)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.toggle.setText(text('details', ctx))
        self.toggle.setAccessibleName(text('details', ctx))


class TermPanel(QFrame):
    """Search and display existing glossary entries, with an exact screen quote."""
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx, self.term_key = ctx, None
        self.setObjectName('panel')
        self.setFixedWidth(340)
        self.setAccessibleName(text('title', ctx))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        header = QHBoxLayout()
        self.heading = _label()
        self.heading.setProperty('role', 'heading')
        self.close_button = QPushButton()
        header.addWidget(self.heading, 1)
        header.addWidget(self.close_button)
        layout.addLayout(header)
        self.search = QLineEdit()
        self.search.setMaxLength(120)
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.matches = QListWidget()
        self.matches.setMaximumHeight(140)
        self.matches.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.matches.itemActivated.connect(self._choose_item)
        self.matches.itemClicked.connect(self._choose_item)
        self.search.returnPressed.connect(self._choose_current)
        layout.addWidget(self.matches)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 4, 0)
        self.message = _label()
        self.name, self.summary = _label(), _label()
        self.name.setProperty('role', 'heading')
        for widget in (self.message, self.name, self.summary):
            body_layout.addWidget(widget)
        self.sections = []
        for _ in range(4):
            heading, content = _label(), _label()
            heading.setProperty('role', 'heading')
            body_layout.addWidget(heading)
            body_layout.addWidget(content)
            self.sections.append((heading, content))
        self.quote_heading, self.quote = _label(), _label()
        self.quote_heading.setProperty('role', 'heading')
        body_layout.addWidget(self.quote_heading)
        body_layout.addWidget(self.quote)
        body_layout.addStretch()
        self.scroll.setWidget(body)
        layout.addWidget(self.scroll, 1)
        self.search.textChanged.connect(self._search)
        self.set_locale(ctx)

    def _search(self, query):
        keys = glossary.search(query)
        self.matches.clear()
        for key in keys:
            item = QListWidgetItem(glossary.name(key, self.ctx))
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.matches.addItem(item)
        if keys:
            self.matches.setCurrentRow(0)
        self.term_key = None
        self._render()

    def _choose_item(self, item):
        self.choose(item.data(Qt.ItemDataRole.UserRole))

    def _choose_current(self):
        item = self.matches.currentItem()
        if item is not None:
            self._choose_item(item)

    def choose(self, key):
        if key not in glossary.BY_KEY:
            return
        self.term_key = key
        self._render()

    def _render(self):
        key = self.term_key
        self.message.setVisible(key is None)
        self.message.setText(text('missing' if self.search.text().strip() and not self.matches.count() else 'empty', self.ctx))
        self.name.setText(glossary.name(key, self.ctx) if key else '')
        self.summary.setText(glossary.summary(key, self.ctx) if key else '')
        parts = glossary.sections(key, self.ctx) if key else ()
        for index, (heading, content) in enumerate(self.sections):
            shown = index < len(parts)
            heading.setVisible(shown)
            content.setVisible(shown)
            heading.setText(parts[index][0] if shown else '')
            content.setText(parts[index][1] if shown else '')

    def set_quote(self, quote):
        self.quote.setText(quote)
        self.quote.setVisible(bool(quote))
        self.quote_heading.setVisible(bool(quote))

    def clear_context(self):
        self.set_quote('')
        self.search.clear()
        self.term_key = None
        self._render()

    def set_locale(self, ctx):
        key = self.term_key
        self.ctx = ctx
        self.heading.setText(text('title', ctx))
        self.setAccessibleName(text('title', ctx))
        self.close_button.setText(text('close', ctx))
        self.search.setPlaceholderText(text('search', ctx))
        self.search.setAccessibleName(text('search', ctx))
        self.quote_heading.setText(text('current', ctx))
        self._search(self.search.text())
        if key:
            self.choose(key)


class ReadingHelp(QObject):
    """One window-local controller; keeps overlay geometry outside critical labels."""
    PANEL_WIDTH = 340
    MIN_OVERLAY_HEIGHT = 260

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.ctx = getattr(window, 'ctx', LocaleContext('en_US'))
        self.panel = TermPanel(self.ctx, window.centralWidget())
        self.panel.hide()
        self.panel.close_button.clicked.connect(self.close)
        self._origin = None
        self._cell = None
        self._quote_source = None
        self._quote_check_pending = False
        self._shown = False
        self.mode = None
        self.last_notice = ''
        self.open_shortcut = QShortcut(QKeySequence('F1'), window)
        self.open_shortcut.activated.connect(self.open_from_focus)
        self.close_shortcut = QShortcut(QKeySequence('Escape'), self.panel)
        self.close_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.close_shortcut.setEnabled(False)
        self.close_shortcut.activated.connect(self.close)
        window.installEventFilter(self)
        window.stack.installEventFilter(self)
        window.stack.currentChanged.connect(lambda _index: self.close(restore=False))
        # Tool and risk pages also switch inside the main route's stack.
        for widget in window.findChildren(QWidget):
            changed = getattr(widget, 'currentChanged', None)
            if widget is not window.stack and changed is not None and hasattr(changed, 'connect'):
                changed.connect(lambda _index: self.close(restore=False))
        for index in range(window.stack.count()):
            page = window.stack.widget(index)
            if isinstance(page, QScrollArea):
                page.verticalScrollBar().valueChanged.connect(lambda _value: self._reposition())
                page.horizontalScrollBar().valueChanged.connect(lambda _value: self._reposition())
        QApplication.instance().installEventFilter(self)
        window.destroyed.connect(self._window_destroyed)

    def _window_destroyed(self):
        QApplication.instance().removeEventFilter(self)

    def _origin_widget(self):
        return self._origin() if self._origin else None

    @staticmethod
    def _table(widget):
        while widget is not None:
            if isinstance(widget, QTableWidget):
                return widget
            widget = widget.parentWidget()
        return None

    def _snapshot(self, origin, *, row=None):
        table = self._table(origin)
        if table is not None:
            row = table.currentRow() if row is None else row
        if table is not None and 0 <= row < table.rowCount():
            items = [table.item(row, column) for column in range(table.columnCount())]
            visible = [item.text() for column, item in enumerate(items)
                       if item is not None and not table.isColumnHidden(column)]
            query = items[0].text() if items and items[0] is not None else ''
            return table, query, ' | '.join(visible)
        if isinstance(origin, QLabel):
            selected = origin.selectedText()
            # Only explicitly selected prose is a query, never a guessed meaning
            # for the whole narrative. No input-field contents are inspected.
            return origin, selected, selected
        return origin, '', ''

    def open_from_focus(self):
        if self._shown and self.panel.isAncestorOf(QApplication.focusWidget()):
            self.panel.search.setFocus()
            return
        self.open_for(QApplication.focusWidget())

    def open_for(self, origin=None):
        origin, query, quote = self._snapshot(origin)
        self._origin = weakref.ref(origin) if origin is not None else None
        self._cell = ((origin.currentRow(), origin.currentColumn())
                      if isinstance(origin, QTableWidget) and origin.currentRow() >= 0 else None)
        self._quote_source = self._source_contents(origin)
        if isinstance(origin, QTableWidget) and not origin.property('reading_help_model_watched'):
            origin.setProperty('reading_help_model_watched', True)
            reference = weakref.ref(origin)
            for signal in (origin.model().rowsRemoved, origin.model().rowsInserted,
                           origin.model().columnsRemoved, origin.model().columnsInserted,
                           origin.model().modelReset, origin.destroyed):
                signal.connect(lambda *_args, source=reference: self._source_invalidated(source()))
            for signal in (origin.model().dataChanged, origin.model().layoutChanged):
                signal.connect(self._schedule_quote_check)
        self.panel.clear_context()
        self.panel.search.setText(query)
        self.panel.set_quote(quote)
        # Search candidates remain explicit: no automatic interpretation of a row
        # or narrative using the first body-text search hit.
        self._shown = True
        self.last_notice = ''
        if not self.reflow():
            self._shown = False
            self.close_shortcut.setEnabled(False)
            self.panel.hide()
            self.panel.clear_context()
            self._origin, self._cell, self._quote_source = None, None, None
            self.last_notice = text('no_room', self.ctx)
            QToolTip.showText(self.window.mapToGlobal(QPoint(self.window.width() // 2, 40)), self.last_notice, self.window)
            return False
        self.panel.search.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.panel.search.selectAll()
        self.close_shortcut.setEnabled(True)
        return True

    def _overlay_rect(self):
        page = self.window.stack.currentWidget()
        host = page.viewport() if isinstance(page, QScrollArea) else self.window.stack
        root = self.window.centralWidget()
        start = host.mapTo(root, QPoint(0, 0))
        bounds = QRect(start, host.size()).intersected(root.rect())
        x = bounds.right() - self.PANEL_WIDTH + 1
        if x < bounds.left():
            return None
        strip = QRect(x, bounds.top(), self.PANEL_WIDTH, bounds.height())
        blocked = []
        for widget in page.findChildren(QWidget):
            if not widget.property('reading_help_keep_visible') or not widget.isVisible():
                continue
            rect = QRect(widget.mapTo(root, QPoint(0, 0)), widget.size()).intersected(strip)
            if not rect.isEmpty():
                blocked.append((max(bounds.top(), rect.top() - 6), min(bounds.bottom() + 1, rect.bottom() + 7)))
        cursor, gaps = bounds.top(), []
        for top, bottom in sorted(blocked):
            if top > cursor:
                gaps.append((cursor, top))
            cursor = max(cursor, bottom)
        if cursor <= bounds.bottom():
            gaps.append((cursor, bounds.bottom() + 1))
        if not gaps:
            return None
        top, bottom = max(gaps, key=lambda gap: gap[1] - gap[0])
        if bottom - top < self.MIN_OVERLAY_HEIGHT:
            return None
        return QRect(x, top, self.PANEL_WIDTH, bottom - top)

    def reflow(self):
        if not self._shown:
            return True
        layout = self.window.centralWidget().layout()
        wide = self.window.width() >= 1280
        if wide:
            if layout.indexOf(self.panel) < 0:
                layout.addWidget(self.panel)
            self.panel.setMinimumHeight(0)
            self.panel.setMaximumHeight(16777215)
            self.mode = 'docked'
        else:
            layout.removeWidget(self.panel)
            self.panel.hide()
            layout.activate()
            rect = self._overlay_rect()
            if rect is None:
                return False
            self.panel.setGeometry(rect)
            self.mode = 'overlay'
        self.panel.show()
        self.panel.raise_()
        return True

    def close(self, checked=False, *, restore=True):
        origin, cell = self._origin_widget(), self._cell
        self._shown = False
        self.close_shortcut.setEnabled(False)
        self.window.centralWidget().layout().removeWidget(self.panel)
        self.panel.hide()
        self.panel.clear_context()
        self._origin, self._cell, self.mode, self._quote_source = None, None, None, None
        if restore and origin is not None:
            try:
                if isinstance(origin, QTableWidget) and cell and cell[0] < origin.rowCount():
                    origin.setCurrentCell(*cell)
                if origin.isVisible() and origin.isEnabled():
                    origin.setFocus(Qt.FocusReason.ShortcutFocusReason)
            except RuntimeError:  # result widget was deleted while help was open
                self.window.stack.setFocus()

    def invalidate_source(self, source):
        origin = self._origin_widget()
        if origin is not None and (origin is source or source.isAncestorOf(origin)):
            self.close(restore=False)

    def _source_invalidated(self, source):
        if self._shown and self._origin_widget() is source:
            try:
                self.close(restore=False)
            except (RuntimeError, AttributeError):  # the window is being destroyed
                self._shown = False

    def _source_contents(self, origin):
        """Canonical quoted cells distinguish translation from a new result."""
        if isinstance(origin, QTableWidget) and self._cell:
            row = self._cell[0]
            if row >= origin.rowCount():
                return None
            cells = []
            for column in range(origin.columnCount()):
                if origin.isColumnHidden(column):
                    continue
                item = origin.item(row, column)
                if item is None:
                    cells.append((column, None))
                    continue
                source = item.data(CAPTION_ROLE)
                if source is None and column in getattr(origin, '_qg_status_columns', {}):
                    source = item.toolTip()  # A1 status metadata retains the raw code here.
                cells.append((column, item.text() if source is None else source,
                              item.data(Qt.ItemDataRole.UserRole)))
            return tuple(cells)
        if isinstance(origin, QLabel):
            return getattr(origin, 'source_text', origin.text()), origin.text()
        return None

    def _schedule_quote_check(self, *args):
        if self._shown and not self._quote_check_pending:
            self._quote_check_pending = True
            QTimer.singleShot(0, self._check_quote)

    def _check_quote(self):
        self._quote_check_pending = False
        if not self._shown:
            return
        try:
            current = self._source_contents(self._origin_widget())
        except RuntimeError:
            current = None
        if current != self._quote_source:
            self.close(restore=False)

    def set_locale(self, ctx):
        self.ctx = ctx
        self.panel.set_locale(ctx)
        for fold in self.window.findChildren(DetailsFold):
            fold.set_locale(ctx)
        origin = self._origin_widget()
        if self._shown and origin is not None:
            try:
                _origin, _query, quote = self._snapshot(origin, row=self._cell[0] if self._cell else None)
                self.panel.set_quote(quote)
            except RuntimeError:
                self.close(restore=False)
        if self._shown and not self.reflow():
            self.close()

    def eventFilter(self, watched, event):
        # QLabel has no textChanged signal. Its same-size replacement still
        # schedules a paint/layout update; compare the source after that event.
        if (self._shown and isinstance(self._origin_widget(), QLabel)
                and isinstance(watched, QWidget)
                and (watched is self.window or self.window.isAncestorOf(watched))
                and event.type() in (QEvent.Type.UpdateRequest, QEvent.Type.LayoutRequest,
                                     QEvent.Type.Paint)):
            self._schedule_quote_check()
        if watched in (self.window, self.window.stack) and event.type() == QEvent.Type.Resize and self._shown:
            QTimer.singleShot(0, self._reposition)
        if (self._shown and isinstance(watched, QWidget)
                and watched.property('reading_help_keep_visible')
                and event.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show)):
            QTimer.singleShot(0, self._reposition)
        if event.type() == QEvent.Type.ContextMenu and isinstance(watched, QWidget):
            if not self.window.isAncestorOf(watched) or self.panel.isAncestorOf(watched):
                return False
            table = self._table(watched)
            origin = table or (watched if isinstance(watched, QLabel) and watched.hasSelectedText() else None)
            if origin is not None:
                menu = QMenu(origin)
                menu.addAction(text('learn', self.ctx), lambda: self.open_for(origin))
                # The ordinary text/table copy action remains available.
                copied = origin.selectedText() if isinstance(origin, QLabel) else self._snapshot(origin)[2]
                if copied:
                    menu.addAction('복사' if self.ctx.language == 'ko' else 'Copy', lambda: QApplication.clipboard().setText(copied))
                select_all = (lambda: origin.setSelection(0, len(origin.text()))) if isinstance(origin, QLabel) else origin.selectAll
                menu.addAction('모두 선택' if self.ctx.language == 'ko' else 'Select all', select_all)
                menu.exec(event.globalPos())
                return True
        return False

    def _reposition(self):
        if self._shown and not self.reflow():
            self.close()
            self.last_notice = text('no_room', self.ctx)
            QToolTip.showText(self.window.mapToGlobal(QPoint(self.window.width() // 2, 40)), self.last_notice, self.window)


def install_reading_help(window):
    """Idempotent host hook; callers retain all window/state ownership."""
    existing = getattr(window, '_reading_help', None)
    if existing is not None:
        return existing
    controller = ReadingHelp(window)
    window._reading_help = controller
    return controller
