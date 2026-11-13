"""Keyboard-operable choices with measured wrapping and the app's native palette."""
from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton, QLabel, QGridLayout, QVBoxLayout, QWidget, QSizePolicy


class ChoiceCard(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.swatch = None
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(15, 12, 32, 12)
        self.column.setSpacing(5)
        self.title, self.description = QLabel(), QLabel()
        for label in (self.title, self.description):
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            label.setProperty('qg_literal', True)
            label.setStyleSheet('background: transparent; border: none; padding: 0;')
            self.column.addWidget(label)
        self.title.setProperty('role', 'choiceTitle')
        self.description.setProperty('role', 'caption')
        self.toggled.connect(self.update)

    def set_copy(self, title, description):
        self.setText(title)
        self.title.setText(title)
        self.description.setText(description)
        self.setAccessibleName(title)
        self.setAccessibleDescription(description)
        self.updateGeometry()

    def hasHeightForWidth(self): return True
    def heightForWidth(self, width): return self.column.totalHeightForWidth(max(100, width))
    def sizeHint(self): return QSize(220, max(84, self.heightForWidth(220)))
    def minimumSizeHint(self): return QSize(180, 72)

    def paintEvent(self, event):
        from core.theme import LIGHT
        colors = getattr(self.window(), 'colors', LIGHT)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = self.isChecked()
        painter.setBrush(QColor(colors.accent_soft if selected else colors.surface))
        painter.setPen(QPen(QColor(colors.accent if selected or self.hasFocus() else colors.border),
                            2 if self.hasFocus() else 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 10, 10)
        if self.swatch:
            painter.setPen(QPen(QColor(self.swatch), 3))
            painter.drawLine(6, 17, 6, self.height() - 17)
        painter.setBrush(QColor(colors.accent if selected else colors.surface))
        painter.setPen(QPen(QColor(colors.accent if selected else colors.border), 1))
        painter.drawEllipse(QRectF(self.width() - 25, 15, 12, 12))
        if selected:
            painter.setPen(QPen(QColor(colors.on_accent), 1.6))
            x = self.width() - 23
            painter.drawLine(x, 21, x + 3, 24)
            painter.drawLine(x + 3, 24, x + 7, 18)


class ChoiceGrid(QWidget):
    def __init__(self, buttons, *, columns=3):
        super().__init__()
        self.buttons, self.max_columns = tuple(buttons), columns
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(8)
        self.columns = 0
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._reflow()

    def _columns(self, width): return max(1, min(self.max_columns, (width + 8) // 228))
    def hasHeightForWidth(self): return True
    def heightForWidth(self, width):
        columns = self._columns(width)
        cell = max(1, (width - (columns - 1) * 8) // columns)
        heights = [max(b.heightForWidth(cell) for b in self.buttons[i:i + columns])
                   for i in range(0, len(self.buttons), columns)]
        return sum(heights) + max(0, len(heights) - 1) * 8
    def sizeHint(self): return QSize(0, self.heightForWidth(max(228, self.width())))
    def minimumSizeHint(self): return QSize(180, self.heightForWidth(max(180, self.width())))
    def _reflow(self):
        columns = self._columns(self.width())
        if columns == self.columns: return
        while self.grid.count(): self.grid.takeAt(0)
        for col in range(self.max_columns): self.grid.setColumnStretch(col, int(col < columns))
        for i, button in enumerate(self.buttons): self.grid.addWidget(button, i // columns, i % columns)
        self.columns = columns
        self.updateGeometry()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()

