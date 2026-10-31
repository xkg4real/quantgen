"""C-format chart + reading pane; one layout, existing result widgets intact."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QBoxLayout, QSizePolicy, QLayout


class ChartStudy(QWidget):
    def __init__(self, chart, reading, *, breakpoint=820):
        super().__init__()
        self.chart_area, self.reading_area = chart, reading
        self.breakpoint = breakpoint
        self.split = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        # The two-column minimum must not prevent reaching the stack breakpoint.
        # Platform fonts can otherwise make a scroll area keep the wide layout.
        self.split.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.split.setContentsMargins(0, 0, 0, 0)
        self.split.setSpacing(18)
        for widget, stretch in ((chart, 2), (reading, 1)):
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.split.addWidget(widget, stretch, Qt.AlignmentFlag.AlignTop)
        self.reflow()

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        size.setWidth(max(self.chart_area.minimumSizeHint().width(),
                          self.reading_area.minimumSizeHint().width(),
                          self.chart_area.minimumWidth(), self.reading_area.minimumWidth()))
        return size

    def reflow(self):
        wide = self.width() >= self.breakpoint
        self.split.setDirection(QBoxLayout.Direction.LeftToRight if wide
                                else QBoxLayout.Direction.TopToBottom)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
