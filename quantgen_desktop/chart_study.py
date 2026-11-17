"""C-format chart + reading pane; one layout, existing result widgets intact."""
from PyQt6.QtCore import QEvent, Qt, QSize
from PyQt6.QtWidgets import QLabel, QWidget, QBoxLayout, QSizePolicy, QLayout, QTabWidget, QStyle


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


class LocalLabel(QLabel):
    """Display-only authored text in both languages ({'ko': .., 'en': ..}).

    Not a `UiLabel`: exports and tests find a result's text labels by `UiLabel.source_text`, and this text
    is in no export. Marked `qg_literal`, so the window catalogue never rewrites it; it follows the window
    language itself (`LanguageController.apply` calls `_reserve_text_space` after a switch)."""

    def __init__(self, texts, role=''):
        super().__init__()
        self.texts = dict(texts)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.setProperty('role', role)
        self.setProperty('qg_literal', True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.sync()

    def sync(self):
        language = 'ko' if getattr(self.window(), 'ui_language', None) == 'ko' else 'en'
        text = self.texts.get(language, self.texts.get('en', ''))
        if self.text() != text:
            self.setText(text)

    def _reserve_text_space(self):
        self.sync()

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.Type.ParentChange, QEvent.Type.Show):
            self.sync()
        return result


class ChartReading(QWidget):
    """'How to read this chart' under a chart (owner issue 02, 2026-11-10).

    The four items of the Flet reading panel (ui/chart_study.py `_qg_reading`, PR #98): what the chart
    shows, where to look, how to read it and its limits, in the window language. Both language variants
    are authored ({'ko'|'en'} per item), so a language switch needs no rerun. Two columns in reading order
    when there is room, one when narrow. Open by default; the toggle folds it. Display only."""
    BREAKPOINT = 620

    def __init__(self, guide, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QGridLayout, QToolButton, QVBoxLayout
        from core.ui_messages import MESSAGES
        from .owner_ui_language.charts import READING_KEYS
        self.setObjectName('chartReading')
        self.setProperty('reading_help_keep_visible', False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.toggle = QToolButton()
        self.toggle.setText('How to read this chart')
        self.toggle.setAccessibleName('How to read this chart')
        self.toggle.setCheckable(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.toggled.connect(self._toggled)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.body = QWidget()
        self.grid = QGridLayout(self.body)
        self.grid.setContentsMargins(0, 0, 0, 4)
        self.grid.setHorizontalSpacing(20)
        self.grid.setVerticalSpacing(12)
        layout.addWidget(self.body)
        self.cells, self.headings, self.texts = [], [], []
        for index, key in enumerate(READING_KEYS, 1):
            korean, english = guide[key]
            cell = QWidget()
            column = QVBoxLayout(cell)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(3)
            heading = LocalLabel({language: f"{index:02}  {MESSAGES[language][key]}" for language in ('ko', 'en')},
                                 'caption')
            text = LocalLabel({'ko': korean, 'en': english}, 'muted')
            for widget in (heading, text):
                widget.setProperty('reading_help_keep_visible', False)
                column.addWidget(widget)
            self.cells.append(cell)
            self.headings.append(heading)
            self.texts.append(text)
        self.columns = 0
        self._place(1)
        self.toggle.setChecked(True)

    def _toggled(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)

    def _place(self, columns):
        if columns == self.columns:
            return
        for cell in self.cells:
            self.grid.removeWidget(cell)
        for index, cell in enumerate(self.cells):
            self.grid.addWidget(cell, index // columns, index % columns, Qt.AlignmentFlag.AlignTop)
        for column in range(2):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        self.columns = columns
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place(2 if event.size().width() >= self.BREAKPOINT else 1)


def chart_reading(name):
    """The reading guide for a chart a pane names (owner_ui_language.charts.READINGS), or None."""
    from .owner_ui_language.charts import READINGS
    guide = READINGS.get(name)
    return ChartReading(guide) if guide else None
