"""Bound input width while preserving wrapped captions and focus."""
from PyQt6.QtCore import QEvent,QObject,QTimer,Qt
from PyQt6.QtWidgets import QComboBox,QSizePolicy
from .result_layout import ResponsiveFieldGrid
BASE_INPUT,GAP=224,12
def _base_cap(columns):return columns*BASE_INPUT+(columns-1)*GAP
class CompactFieldGrid(ResponsiveFieldGrid):
    """Owner PR89 density: up to 3/4 columns at a 224px base, reflowing only when narrow.

    224px is the base, not a ceiling: when native metrics (fonts, DPI, Windows style)
    make a column's real minimum wider, the cap widens to the narrowest width that still
    fits every column, so a wide window keeps all columns without clipping (A3 rule).
    """
    def __init__(self,fields,*,max_columns=3):
        pairs=tuple(fields)
        for caption,control in pairs:
            control.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
            if isinstance(control,QComboBox):
                control.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                control.setMinimumContentsLength(12);control.setToolTip(control.currentText());control.currentTextChanged.connect(control.setToolTip)
        super().__init__(pairs,max_columns=max_columns)
        self.grid.setHorizontalSpacing(GAP);self.grid.setVerticalSpacing(6)
        self._cap_ready=True;self._sync_cap()
    def _column_minima(self,columns):return [max(176,w) for w in super()._column_minima(columns)]
    def compact_cap(self):
        columns=min(self.max_columns,len(self.fields))
        needed=sum(self._column_minima(columns))+(columns-1)*self.grid.horizontalSpacing()
        return max(_base_cap(self.max_columns),needed)
    def _sync_cap(self):
        cap=self.compact_cap()
        if cap!=self.maximumWidth():self.setMaximumWidth(cap)
        box=self.parentWidget()
        while box is not None and not hasattr(box,'_compact_base'):box=box.parentWidget()
        # The bounded panel follows its visible form (ToolPane shows one form at a time).
        if box is not None and self.isVisibleTo(box):
            wanted=max(box._compact_base,cap+box._compact_extra)
            if wanted!=box.maximumWidth():box.setMaximumWidth(wanted)
    def refresh(self):
        if getattr(self,'_cap_ready',False):self._sync_cap()
        super().refresh()
    def eventFilter(self,watched,event):
        if watched is self and event.type() in (QEvent.Type.Show,QEvent.Type.ParentChange) and not self.timer.isActive():
            self.timer.start(0)
        return super().eventFilter(watched,event)
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
    box._compact_extra=margins.left()+margins.right()+2
    box._compact_base=_base_cap(columns)+box._compact_extra
    box.setMaximumWidth(box._compact_base)
    box.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Preferred)
    box._compact_height=_PanelHeight(box)
    return box
def add_compact_action(layout,button):
    button.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed)
    layout.addWidget(button,0,Qt.AlignmentFlag.AlignLeft)
