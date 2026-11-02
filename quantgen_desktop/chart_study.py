"""C-format chart + reading pane; one layout, existing result widgets intact."""
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QBoxLayout, QSizePolicy, QLayout, QTabWidget, QStyle


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
            # Intrinsic image/text hints are preferred widths, not a reason to
            # make the whole scroll page wider than its viewport.
            widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            if widget.layout() is not None:
                widget.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
            self.split.addWidget(widget, stretch, Qt.AlignmentFlag.AlignTop)
        self.reflow()

    def hasHeightForWidth(self):
        return True

    @staticmethod
    def _content_height(widget, width):
        if widget.isHidden():
            return 0
        layout = widget.layout()
        if layout and layout.hasHeightForWidth():
            height = layout.totalHeightForWidth(max(1, width))
        elif widget.hasHeightForWidth():
            height = widget.heightForWidth(max(1, width))
        else:
            height = widget.sizeHint().height()
        return max(widget.minimumHeight(), height, 0)

    def heightForWidth(self, width):
        # Ignored horizontal size policies must not make Qt measure prose at
        # zero width, which produces thousands of pixels of phantom whitespace.
        if width >= self.breakpoint:
            available = max(2, width - self.split.spacing())
            left = available * 2 // 3
            return max(self._content_height(self.chart_area, left),
                       self._content_height(self.reading_area, available - left))
        chart = self._content_height(self.chart_area, width)
        reading = self._content_height(self.reading_area, width)
        return chart + reading + (self.split.spacing() if chart and reading else 0)

    def sizeHint(self):
        return QSize(0, self.heightForWidth(max(1, self.width())))

    def minimumSizeHint(self):
        return QSize(max(self.chart_area.minimumWidth(), self.reading_area.minimumWidth()),
                     self.heightForWidth(max(1, self.width())))

    def reflow(self):
        wide = self.width() >= self.breakpoint
        self.split.setDirection(QBoxLayout.Direction.LeftToRight if wide
                                else QBoxLayout.Direction.TopToBottom)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
        if event.size().width() != event.oldSize().width():
            self.updateGeometry()


class CurrentPageTabs(QTabWidget):
    """A scroll page should size the selected tool, not its inactive siblings."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setUsesScrollButtons(True)
        self.currentChanged.connect(self.updateGeometry)

    def _page_hint(self, minimum):
        page = self.currentWidget()
        if page is None:
            return super().minimumSizeHint() if minimum else super().sizeHint()
        size = (page.minimumSizeHint() if minimum else page.sizeHint()).expandedTo(page.minimumSize())
        bar = self.tabBar().minimumSizeHint() if minimum else self.tabBar().sizeHint()
        frame = 2 * self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        return QSize(max(size.width(), bar.width()) + frame,
                     max(0, size.height()) + bar.height() + frame)

    def minimumSizeHint(self):
        return self._page_hint(True)

    def sizeHint(self):
        return self._page_hint(False)

    def hasHeightForWidth(self):
        page = self.currentWidget()
        return page is not None and page.hasHeightForWidth()

    def heightForWidth(self, width):
        page = self.currentWidget()
        if page is None:
            return super().heightForWidth(width)
        frame = 2 * self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        height = (page.heightForWidth(max(1, width - frame)) if page.hasHeightForWidth()
                  else page.sizeHint().height())
        return max(0, height, page.minimumHeight()) + self.tabBar().sizeHint().height() + frame
