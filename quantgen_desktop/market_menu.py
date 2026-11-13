"""Markets disclosure: every level opens below its row, inside the left rail.

The owner replaced the always-visible/right-flyout design on 2026-11-13.
One branch per depth is open. The rail scrolls; nothing covers a chart.
"""
from PyQt6.QtCore import QEvent, QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from .rail_menu import ChevronButton, OPEN_DELAY_MS, CLOSE_DELAY_MS
from .localization import SKIP_PASS


class MenuPanel(QWidget):
    def __init__(self, anchor, nodes, level, menu):
        super().__init__()
        self.setProperty(SKIP_PASS,True)
        self.setParent(anchor.parentWidget())
        self.anchor, self.level, self.rows = anchor, level, []
        self.setObjectName('marketDropdown')
        column = QVBoxLayout(self)
        column.setContentsMargins(8, 1, 0, 3)
        column.setSpacing(1)
        for node in nodes:
            row = ChevronButton(node.text.replace('&', '&&'), chevron=bool(node.children))
            row.node, row.level = node, level
            row.setProperty('inlineMenu', True)
            row.setProperty('qg_literal', True)
            row.setProperty('marketMenuItem', True)
            row.setAccessibleName(node.text)
            row.setToolTip(node.tip)
            row.setCheckable(True)
            row.setChecked(node.mark in menu.current())
            row.setProperty('current',row.isChecked())
            row.clicked.connect(lambda checked=False, r=row: menu.activate(r))
            row.installEventFilter(menu)
            column.addWidget(row)
            self.rows.append(row)
        layout = anchor.parentWidget().layout()
        layout.insertWidget(layout.indexOf(anchor) + 1, self)


class InlineMarketMenu(QObject):
    activated = pyqtSignal(object)

    def __init__(self, parent, window):
        super().__init__(parent)
        self.window = window
        self.current = lambda: frozenset()
        self.roots, self.panels = {}, []
        self.header = self.container = self.strip = None
        self.keyboard = False
        self.pending = None
        self.open_timer = QTimer(self)
        self.open_timer.setSingleShot(True)
        self.open_timer.timeout.connect(self._open_pending)
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self._close_outside)
        self.focus_timer=QTimer(self);self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self._reveal_focus)
        QApplication.instance().focusChanged.connect(self._focus_changed)
        QApplication.instance().installEventFilter(self)

    def _focus_changed(self,old,new):
        if not self.is_open() or new is None:return
        if new is self.header or self.container.isAncestorOf(new):
            self.focus_timer.start(0)
        elif self.keyboard:self.close_all()

    def _reveal_focus(self):
        focus=QApplication.focusWidget()
        if self.is_open() and focus is not None and self.container.isAncestorOf(focus):
            self.window.rail_scroll.ensureWidgetVisible(focus,0,8)

    def configure(self, header, container, strip):
        self.header, self.container, self.strip = header, container, strip
        container.setProperty(SKIP_PASS,True)
        header.installEventFilter(self)
        strip.installEventFilter(self)
        container.installEventFilter(self)
        container.hide()

    def watch_root(self, row, factory):
        self.roots[row] = factory
        row.setProperty('inlineMenu', True)
        row.installEventFilter(self)

    def open_root(self, row=None, *, keyboard=False):
        if row is not None:
            return self.root_clicked(row,keyboard=keyboard)
        if self.container is None:
            return
        self.keyboard = keyboard
        self._quiet()
        self.close_timer.stop()
        if self.window.sidebar_collapsed:
            self.window.set_sidebar_collapsed(False, remember=False)
        self.container.show()
        if keyboard:
            next(iter(self.window.market_sections.values())).setFocus(Qt.FocusReason.TabFocusReason)

    def open_child(self,row,*,keyboard=False):
        return self._open(row.level+1,row,row.node.children,keyboard=keyboard)

    def root_clicked(self, row, *, keyboard=False):
        self.open_root(keyboard=keyboard)
        if row in (self.header, self.strip):
            return None
        return self._open(0, row, self.roots[row](), keyboard=keyboard)

    def _open(self, depth, row, nodes, *, keyboard=False):
        self._quiet()
        if depth < len(self.panels) and self.panels[depth].anchor is row:
            panel = self.panels[depth]
        else:
            self._close_from(depth)
            if not nodes:
                return None
            panel = MenuPanel(row, nodes, depth, self)
            self.panels.append(panel)
            row.set_open(True)
            panel.show()
        if keyboard and panel.rows:
            self.keyboard = True
            panel.rows[0].setFocus(Qt.FocusReason.TabFocusReason)
            self.window.rail_scroll.ensureWidgetVisible(panel.rows[0], 0, 12)
        return panel

    def _close_from(self, depth):
        self.open_timer.stop()
        self.pending=None
        for panel in reversed(self.panels[depth:]):
            panel.anchor.set_open(False)
            panel.hide()
            panel.parentWidget().layout().removeWidget(panel)
            panel.deleteLater()
        del self.panels[depth:]

    def close_all(self, *unused):
        self._quiet()
        self.open_timer.stop()
        self.close_timer.stop()
        self.pending = None
        self._close_from(0)
        if self.container is not None:
            self.container.hide()
        self.keyboard = False

    def _quiet(self):
        # This subtree is authored in the active language. Its expanding layout
        # changes geometry only; do not translate the entire app on each hover.
        localizer=getattr(self.window,'localizer',None)
        widget=self.container
        while localizer is not None and widget is not None:
            localizer.quiet(widget)
            widget=widget.parentWidget()

    def is_open(self):
        return self.container is not None and not self.container.isHidden()

    def activate(self, row):
        if row.node.leaf:
            leaf = row.node.leaf
            self.close_all()
            self.activated.emit(leaf)
        else:
            self._open(row.level + 1, row, row.node.children, keyboard=row.hasFocus())

    def _open_pending(self):
        pending, self.pending = self.pending, None
        if pending is None:
            return
        row, depth, factory = pending
        if row.isVisible() and row.underMouse():
            self._open(depth, row, factory())

    def _close_outside(self):
        if not self.is_open():
            return
        target = QApplication.widgetAt(QCursor.pos())
        inside = target is not None and (target is self.header or target is self.container
                  or self.container.isAncestorOf(target))
        focus = QApplication.focusWidget()
        keyboard_inside = self.keyboard and focus is not None and (
            focus is self.header or self.container.isAncestorOf(focus))
        if not inside and not keyboard_inside:
            self.close_all()

    def set_theme(self, palette, dark):
        for row in self.roots:
            row.tones = (palette.muted, palette.text, palette.accent)
            row.tint = palette.accent_soft
            row.update()
        for panel in self.panels:
            for row in panel.rows:
                row.tones = (palette.muted, palette.text, palette.accent)
                row.update()

    def eventFilter(self, watched, event):
        kind = event.type()
        owned_row = watched in self.roots or hasattr(watched, 'node') and isinstance(watched, ChevronButton)
        if kind == QEvent.Type.Enter:
            if watched in (self.header, self.strip):
                self.open_root()
            if owned_row:
                self.keyboard = False
                self.close_timer.stop()
                depth = 0 if watched in self.roots else watched.level + 1
                factory = self.roots.get(watched) or (lambda: watched.node.children)
                self.pending = (watched, depth, factory)
                self.open_timer.start(OPEN_DELAY_MS)
        elif kind == QEvent.Type.Leave and (owned_row or watched in (self.header, self.container)):
            self.close_timer.start(CLOSE_DELAY_MS)
        elif kind == QEvent.Type.KeyPress and owned_row:
            key = event.key()
            if hasattr(watched,'node') and key in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
                self.activate(watched)
                return True
            if key in (Qt.Key.Key_Escape, Qt.Key.Key_Left):
                if hasattr(watched, 'level'):
                    panel = self.panels[watched.level]
                    anchor = panel.anchor
                    self._close_from(watched.level)
                    anchor.setFocus(Qt.FocusReason.TabFocusReason)
                else:
                    self.close_all()
                    self.header.setFocus(Qt.FocusReason.TabFocusReason)
                return True
            if key == Qt.Key.Key_Right:
                if watched in self.roots:
                    self.root_clicked(watched, keyboard=True)
                else:
                    self._open(watched.level + 1, watched, watched.node.children, keyboard=True)
                return True
            if hasattr(watched, 'level') and key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                rows = self.panels[watched.level].rows
                at = (rows.index(watched) + (1 if key == Qt.Key.Key_Down else -1)) % len(rows)
                rows[at].setFocus(Qt.FocusReason.TabFocusReason)
                self.keyboard = True
                self.window.rail_scroll.ensureWidgetVisible(rows[at], 0, 12)
                return True
        elif kind == QEvent.Type.MouseButtonPress and self.is_open():
            if watched is not self.header and watched is not self.container and not (
                    isinstance(watched, QWidget) and self.container.isAncestorOf(watched)):
                self.close_all()
        elif kind in (QEvent.Type.WindowDeactivate, QEvent.Type.Close) and watched is self.window:
            self.close_all()
        return super().eventFilter(watched, event)
