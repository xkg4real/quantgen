"""Per-window display translation, without rebuilding forms or rerunning jobs."""
from PyQt6.QtCore import QObject, QEvent, QSignalBlocker, QTimer, Qt, QLocale
from PyQt6.QtWidgets import (QAbstractButton, QComboBox, QLabel, QLineEdit,
                             QTableWidget, QTabWidget, QPlainTextEdit, QWidget)
from .translations import display

CAPTION_ROLE = Qt.ItemDataRole.UserRole + 802


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
        language = getattr(self.window(), 'ui_language', None)
        localized = getattr(self, 'localized_text', {}).get(language)
        super().setText(localized if localized is not None else display(self, self.source_text))

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
        self.apply()

    def schedule(self, *args):
        if not self.applying and not self.pending:
            self.pending = True
            QTimer.singleShot(0, self.apply)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.LayoutRequest, QEvent.Type.ChildAdded,
                            QEvent.Type.PolishRequest):
            self.schedule()
        return False

    def _text(self, widget, key, current, setter):
        cache = getattr(widget, '_qg_display_sources', {})
        source, rendered = cache.get(key, (current, current))
        if current != rendered:
            source = current
        translated = display(widget, source)
        if key == 'text' and widget.property('nav'):
            translated = translated.replace('&&', '&').replace('&', '&&')
        cache[key] = (source, translated)
        widget._qg_display_sources = cache
        if current != translated:
            setter(translated)

    def apply(self):
        if self.applying:
            return
        self.pending = False
        self.applying = True
        ctx = getattr(self.window, "ctx", None)
        if ctx:
            self.window.setLocale(QLocale(str(ctx.locale)))
            self.window.setLayoutDirection(Qt.LayoutDirection.RightToLeft if ctx.rtl else Qt.LayoutDirection.LeftToRight)
        try:
            for widget in [self.window, *self.window.findChildren(QWidget)]:
                if not getattr(widget, '_qg_watched', False):
                    widget.installEventFilter(self)
                    widget._qg_watched = True
                    if isinstance(widget, (QComboBox, QTableWidget)):
                        model = widget.model()
                        model.dataChanged.connect(self.schedule)
                        model.headerDataChanged.connect(self.schedule)
                        model.rowsInserted.connect(self.schedule)
                        model.modelReset.connect(self.schedule)
                with QSignalBlocker(widget):
                    if isinstance(widget, UiLabel):
                        widget.retranslate()
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
                                self._text(widget, ('header', i), item.text(), item.setText)
                        # Only explicitly tagged metric captions; never symbols,
                        # order IDs, numbers or provider-supplied values.
                        for column in widget.property('localized_columns') or ():
                            for row in range(widget.rowCount()):
                                item = widget.item(row, column)
                                if item and item.data(CAPTION_ROLE) is not None:
                                    item.setText(display(widget, item.data(CAPTION_ROLE)))
                    if isinstance(widget, (QLineEdit, QPlainTextEdit)):
                        self._text(widget, 'placeholder', widget.placeholderText(), widget.setPlaceholderText)
                    self._text(widget, 'accessible', widget.accessibleName(), widget.setAccessibleName)
                    self._text(widget, 'tooltip', widget.toolTip(), widget.setToolTip)
                if hasattr(widget, '_reserve_text_space'):
                    widget._reserve_text_space()
                    widget.update()
        finally:
            self.applying = False


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
