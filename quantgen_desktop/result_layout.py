"""Opt-in layouts for small result tables; raw result data stays untouched."""
from PyQt6.QtCore import QEvent, QObject, QSize, QTimer, Qt
from PyQt6.QtWidgets import QBoxLayout, QLayout, QSizePolicy, QWidget


class ContentTableHeight(QObject):
    """Keep every result row visible as values, language, font and width change.

    This is deliberately opt-in: large history/scenario tables keep their usual
    scrolling. Coalescing model notifications avoids a resize for every cell.
    """
    def __init__(self, table):
        super().__init__(table)
        self.table = table
        self.pending = self.measuring = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.measure)
        table.setMinimumHeight(0)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for widget in (table, table.viewport(), table.horizontalHeader()):
            widget.installEventFilter(self)
        model = table.model()
        for signal in (model.dataChanged, model.headerDataChanged, model.rowsInserted,
                       model.rowsRemoved, model.modelReset):
            signal.connect(self.schedule)
        table.horizontalHeader().sectionResized.connect(self.schedule)
        table.horizontalHeader().geometriesChanged.connect(self.schedule)
        table.verticalHeader().sectionResized.connect(self.schedule)
        self.schedule()

    def schedule(self, *args):
        if not self.measuring and not self.pending:
            self.pending = True
            self.timer.start(0)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.FontChange,
                            QEvent.Type.StyleChange, QEvent.Type.Show,
                            QEvent.Type.PolishRequest):
            self.schedule()
        return False

    def measure(self):
        self.pending = False
        self.measuring = True
        try:
            table = self.table
            alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            for row in range(table.rowCount()):
                for column in range(1, table.columnCount()):
                    item = table.item(row, column)
                    if item is not None and item.textAlignment() != alignment:
                        item.setTextAlignment(alignment)
            table.resizeRowsToContents()
            height = self.content_height()
            if table.minimumHeight() != height or table.maximumHeight() != height:
                table.setFixedHeight(height)
                table.updateGeometry()
        finally:
            self.measuring = False
        # Qt can resize the styled header synchronously while setting the table
        # height. Its notification was suppressed by the measurement guard;
        # reconcile that new geometry in a separate pass rather than recurse.
        if self.table.height() != self.content_height():
            self.schedule()

    def content_height(self):
        table = self.table
        height = 2 * table.frameWidth()
        if not table.horizontalHeader().isHidden():
            height += table.horizontalHeader().height()
        height += sum(table.rowHeight(row) for row in range(table.rowCount())
                      if not table.isRowHidden(row))
        if table.horizontalScrollBar().isVisible():
            height += table.horizontalScrollBar().sizeHint().height()
        return height


def fit_result_table(table):
    """Attach one height controller, retaining it for the lifetime of the table."""
    if not hasattr(table, '_content_height_controller'):
        table._content_height_controller = ContentTableHeight(table)
    return table


class PairedResultPanels(QWidget):
    """Equal-width G1 panels, stacked when their available content is narrow."""
    def __init__(self, first, second, *, breakpoint=820):
        super().__init__()
        self.panels = first, second
        self.breakpoint = breakpoint
        self.split = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.split.setContentsMargins(0, 0, 0, 0)
        self.split.setSpacing(18)
        self.split.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        for widget in self.panels:
            widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            if widget.layout() is not None:
                widget.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
            self.split.addWidget(widget, 1)
        self.reflow()

    def hasHeightForWidth(self):
        return True

    @staticmethod
    def _height(widget, width):
        layout = widget.layout()
        height = (layout.totalHeightForWidth(max(1, width))
                  if layout and layout.hasHeightForWidth() else widget.sizeHint().height())
        return max(0, widget.minimumHeight(), height)

    def heightForWidth(self, width):
        if width >= self.breakpoint:
            available = max(2, width - self.split.spacing())
            first = available // 2
            return max(self._height(self.panels[0], first),
                       self._height(self.panels[1], available - first))
        return sum(self._height(widget, width) for widget in self.panels) + self.split.spacing()

    def sizeHint(self):
        return QSize(0, self.heightForWidth(max(1, self.width())))

    def minimumSizeHint(self):
        return self.sizeHint()

    def reflow(self):
        direction = (QBoxLayout.Direction.LeftToRight if self.width() >= self.breakpoint
                     else QBoxLayout.Direction.TopToBottom)
        self.split.setDirection(direction)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
        if event.size().width() != event.oldSize().width():
            self.updateGeometry()
