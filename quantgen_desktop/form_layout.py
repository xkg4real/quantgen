"""Bound input width while preserving wrapped captions and focus."""
from PyQt6.QtCore import QEvent,QObject,QTimer,Qt
from PyQt6.QtWidgets import QComboBox,QSizePolicy
from .result_layout import ResponsiveFieldGrid
class CompactFieldGrid(ResponsiveFieldGrid):
    def __init__(self,fields,*,max_columns=3):
        pairs=tuple(fields)
        for caption,control in pairs:
            control.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
            if isinstance(control,QComboBox):
                control.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                control.setMinimumContentsLength(12);control.setToolTip(control.currentText());control.currentTextChanged.connect(control.setToolTip)
        super().__init__(pairs,max_columns=max_columns)
        self.grid.setHorizontalSpacing(12);self.grid.setVerticalSpacing(6)
        self.setMaximumWidth(max_columns*224+(max_columns-1)*12)
    def _column_minima(self,columns):return [max(176,w) for w in super()._column_minima(columns)]
class _PanelHeight(QObject):
    """Qt can measure a capped child at its wider parent's width; use actual width."""
    def __init__(self,box):
        super().__init__(box);self.box=box;self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.measure);box.installEventFilter(self);self.timer.start(0)
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.Resize,QEvent.Type.LayoutRequest,QEvent.Type.FontChange,QEvent.Type.StyleChange,QEvent.Type.Show):
            if not self.timer.isActive():self.timer.start(0)
        return False
    def measure(self):
        layout=self.box.layout()
        needed=layout.totalHeightForWidth(self.box.width()) if layout.hasHeightForWidth() else layout.totalMinimumSize().height()
        if needed>=0 and needed!=self.box.minimumHeight():self.box.setMinimumHeight(needed)
def bound_input_panel(box,*,columns=3):
    margins=box.layout().contentsMargins()
    box.setMaximumWidth(columns*224+(columns-1)*12+margins.left()+margins.right()+2)
    box.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Preferred)
    box._compact_height=_PanelHeight(box)
    return box
def add_compact_action(layout,button):
    button.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed)
    layout.addWidget(button,0,Qt.AlignmentFlag.AlignLeft)
