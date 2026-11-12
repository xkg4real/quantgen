"""Per-window display translation, without rebuilding forms or rerunning jobs."""
from PyQt6.QtCore import QObject, QEvent, QSignalBlocker, QTimer, Qt, QLocale
from PyQt6.QtWidgets import (QAbstractButton, QComboBox, QLabel, QLineEdit,
                             QTableWidget, QTabWidget, QPlainTextEdit, QWidget)
from .translations import display
from .wheel_guard import guard as guard_wheel
from .status_language import STATUS_ROLE, status_text

CAPTION_ROLE = Qt.ItemDataRole.UserRole + 802
# A widget built in the window language and rebuilt on a language switch (the 시장 menu's flyouts, UI-D11) carries
# this property from before it gets its parent: no pass visits it or its children, and adding it schedules none.
# A pass over the whole window takes about a tenth of a second, too slow to follow every flyout a pointer opens.
SKIP_PASS = 'qg_no_language_pass'


class UiLabel(QLabel):
    """Retain the original message for exports and later language changes."""
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.source_text = str(text)
        self.retranslate()

    def setText(self, text):
        if str(text) != self.source_text:
            self.localized_text = {}
        self.source_text = str(text)
        self.retranslate()

    def retranslate(self):
        window = self.window()
        language = getattr(window, 'ui_language', None)
        ctx = getattr(window, 'ctx', None)
        key = (self.source_text, language, str(ctx.locale) if ctx is not None else None,
               tuple(sorted(getattr(self, 'localized_text', {}).items())))
        if key == getattr(self, '_qg_rendered_key', None) and self.text() == getattr(self, '_qg_rendered', None):
            return  # same source, language and locale as last time: the display text cannot differ
        localized = getattr(self, 'localized_text', {}).get(language)
        rendered = localized if localized is not None else display(self, self.source_text)
        super().setText(rendered)
        self._qg_rendered_key, self._qg_rendered = key, self.text()

    def event(self, event):
        result = super().event(event)
        if event.type() == QEvent.Type.ParentChange and hasattr(self, 'source_text'):
            self.retranslate()
        return result


class LanguageController(QObject):
    """Translate authored chrome only. Input text, item data and reports stay raw.

    Qt layout/model notifications cover late results and dynamic button text.
    Source and rendered text are stored separately, so switching is reversible.
    A queued pass is coalesced and signals are blocked while display text changes.
    """
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.pending = self.applying = False
        self._quiet = {}  # id(widget) -> open quiet windows (`quiet`)
        self.apply()

    def quiet(self, widget, ms=60):
        """The layout requests a widget gets in the next `ms` come from a `SKIP_PASS` child shown or hidden over it
        (a flyout, which is in no layout): they need no pass. Requests on any other widget still schedule one."""
        key = id(widget)
        self._quiet[key] = self._quiet.get(key, 0) + 1
        QTimer.singleShot(ms, lambda: self._unquiet(key))

    def _unquiet(self, key):
        left = self._quiet.get(key, 0) - 1
        if left > 0:
            self._quiet[key] = left
        else:
            self._quiet.pop(key, None)

    def schedule(self, *args):
        if not self.applying and not self.pending:
            self.pending = True
            QTimer.singleShot(0, self.apply)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.LayoutRequest, QEvent.Type.ChildAdded,
                            QEvent.Type.PolishRequest):
            if event.type() == QEvent.Type.ChildAdded and _skipped(event.child()):
                return False
            if event.type() == QEvent.Type.LayoutRequest and id(watched) in self._quiet:
                return False
            self.schedule()
        return False

    def _stamp(self, widget):
        """The window language and locale a text was rendered for; a pass re-renders a text only when this or the
        text itself changed. Without it every pass re-translated every text, about a second per pass once the
        Markets list and the stock screen were added, and a pass runs after any layout change (a window resize
        took over a second to settle; PR 109's Windows CI timed out on it)."""
        window = widget.window()
        stamp = self._stamps.get(id(window))
        if stamp is None:
            ctx = getattr(window, 'ctx', None)
            stamp = (getattr(window, 'ui_language', None), str(ctx.locale) if ctx is not None else None)
            self._stamps[id(window)] = stamp
        return stamp

    def _text(self, widget, key, current, setter):
        cache = getattr(widget, '_qg_display_sources', {})
        stamp = self._stamp(widget)
        entry = cache.get(key)
        if entry is not None and current == entry[1] and entry[2] == stamp:
            return  # rendered for this language from this source, and nobody has replaced it since
        source, rendered = (entry[0], entry[1]) if entry is not None else (current, current)
        if current != rendered:
            source = current
        translated = display(widget, source)
        if key == 'text' and widget.property('nav'):
            translated = translated.replace('&&', '&').replace('&', '&&')
        cache[key] = (source, translated, stamp)
        widget._qg_display_sources = cache
        if current != translated:
            setter(translated)

    def apply(self):
        if self.applying:
            return
        self.pending = False
        self.applying = True
        self._stamps = {}  # window language and locale, read once per pass
        ctx = getattr(self.window, "ctx", None)
        if ctx:
            self.window.setLocale(QLocale(str(ctx.locale)))
            self.window.setLayoutDirection(Qt.LayoutDirection.RightToLeft if ctx.rtl else Qt.LayoutDirection.LeftToRight)
        try:
            widgets = [self.window, *self.window.findChildren(QWidget)]
            skipped = [widget for widget in widgets if _skipped(widget)]
            if skipped:
                left_out = {id(widget) for root in skipped for widget in (root, *root.findChildren(QWidget))}
                widgets = [widget for widget in widgets if id(widget) not in left_out]
            for widget in widgets:
                if not getattr(widget, '_qg_watched', False):
                    widget.installEventFilter(self)
                    widget._qg_watched = True
                    guard_wheel(widget)  # owner UI-3: the wheel scrolls the page, not selectors
                    if isinstance(widget, (QComboBox, QTableWidget)):
                        model = widget.model()
                        model.dataChanged.connect(self.schedule)
                        model.headerDataChanged.connect(self.schedule)
                        model.rowsInserted.connect(self.schedule)
                        model.modelReset.connect(self.schedule)
                with QSignalBlocker(widget):
                    if isinstance(widget, UiLabel):
                        widget.retranslate()
                    elif widget.property('qg_literal'):
                        pass  # text already in its language (narrative_view.NarrativeLine)
                    elif isinstance(widget, QLabel):
                        self._text(widget, 'text', widget.text(), widget.setText)
                    elif isinstance(widget, QAbstractButton):
                        self._text(widget, 'text', widget.text(), widget.setText)
                    elif isinstance(widget, QComboBox) and not widget.isEditable():
                        for i in range(widget.count()):
                            self._text(widget, ('item', i), widget.itemText(i),
                                       lambda text, i=i: widget.setItemText(i, text))
                    elif isinstance(widget, QTabWidget):
                        for i in range(widget.count()):
                            self._text(widget, ('tab', i), widget.tabText(i),
                                       lambda text, i=i: widget.setTabText(i, text))
                    elif isinstance(widget, QTableWidget):
                        for i in range(widget.columnCount()):
                            item = widget.horizontalHeaderItem(i)
                            if item:
                                source = item.data(CAPTION_ROLE)
                                if source is not None:
                                    item.setText(display(widget, source))
                                else:
                                    self._text(widget, ('header', i), item.text(), item.setText)
                        # Only explicitly tagged metric captions; never symbols,
                        # order IDs, numbers or provider-supplied values.
                        for column in widget.property('localized_columns') or ():
                            for row in range(widget.rowCount()):
                                item = widget.item(row, column)
                                if item and item.data(CAPTION_ROLE) is not None:
                                    item.setText(display(widget, item.data(CAPTION_ROLE)))
                        for column, context in getattr(widget, '_qg_status_columns', {}).items():
                            for row in range(widget.rowCount()):
                                item = widget.item(row, column)
                                if item and item.data(STATUS_ROLE) is not None:
                                    raw = item.data(STATUS_ROLE)
                                    item.setText(status_text(widget, raw, context))
                                    item.setToolTip(str(raw))
                    if isinstance(widget, (QLineEdit, QPlainTextEdit)):
                        self._text(widget, 'placeholder', widget.placeholderText(), widget.setPlaceholderText)
                    self._text(widget, 'accessible', widget.accessibleName(), widget.setAccessibleName)
                    self._text(widget, 'tooltip', widget.toolTip(), widget.setToolTip)
                if hasattr(widget, '_reserve_text_space'):
                    widget._reserve_text_space()
                    widget.update()
        finally:
            self.applying = False


def _skipped(obj):
    return isinstance(obj, QWidget) and bool(obj.property(SKIP_PASS))


def locale_picker(ctx,parent=None):
    from core.i18n import locale_choices
    picker=QComboBox(parent)
    picker.setProperty('localePicker',True)
    picker.setEditable(True);picker.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    picker.setMaxVisibleItems(14);picker.setMinimumWidth(180);picker.setMaximumWidth(480)
    picker.completer().setFilterMode(Qt.MatchFlag.MatchContains)
    picker.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    choices=list(locale_choices())
    priority=[('ko_KR','한국어 · 대한민국'),('en_US','English · United States')]
    for key,label in priority+[(k,n) for k,n in choices if k not in {'ko_KR','en_US'}]:picker.addItem(label,key)
    index=picker.findData(str(ctx.locale));picker.setCurrentIndex(max(0,index))
    return picker
