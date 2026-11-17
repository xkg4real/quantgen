"""Content-width tables; native metrics and full cell data are retained."""
import re
from PyQt6.QtCore import QEvent,QObject,QTimer,Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QAbstractItemView,QHeaderView
_NUMBER=re.compile(r'^[+−-]?(?:\d[\d, ]*(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?(?:\s*(?:%|bp|bps|[KMBT]|KRW|USD|EUR|원))?$')
class CompactTableLayout(QObject):
    def __init__(self,table):
        super().__init__(table);self.table=table;self.measuring=False
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.measure)
        table.setMinimumWidth(0);table.setWordWrap(True);table.setShowGrid(False)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.horizontalHeader().setStretchLastSection(False);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setMinimumSectionSize(48)
        for widget in (table,table.viewport(),table.horizontalHeader()):widget.installEventFilter(self)
        model=table.model()
        for signal in (model.dataChanged,model.headerDataChanged,model.rowsInserted,model.rowsRemoved,model.columnsInserted,model.columnsRemoved,model.modelReset):signal.connect(self.schedule)
        self.schedule()
    def schedule(self,*args):
        if not self.measuring and not self.timer.isActive():self.timer.start(0)
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.Resize,QEvent.Type.FontChange,QEvent.Type.StyleChange,QEvent.Type.Show):self.schedule()
        return False
    def measure(self):
        if self.measuring:return
        self.measuring=True
        try:
            t=self.table;m=QFontMetrics(t.font());hm=QFontMetrics(t.horizontalHeader().font());widths=[]
            for c in range(t.columnCount()):
                header=t.horizontalHeaderItem(c);width=max(64,hm.horizontalAdvance(header.text())+28) if header else 64
                for r in range(t.rowCount()):
                    item=t.item(r,c)
                    if item is not None:width=max(width,max((m.horizontalAdvance(s) for s in item.text().splitlines()),default=0)+26)
                    widget=t.cellWidget(r,c)
                    if widget:width=max(width,widget.sizeHint().width())
                widths.append(min(width,round(360*max(1,m.height()/17))))
            # Hidden columns (e.g. provider/date kept for export) take no width (owner UI port, 2026-11-11).
            shown=sum(w for c,w in enumerate(widths) if not t.isColumnHidden(c))
            natural=max(120,shown+2*t.frameWidth()+t.verticalScrollBar().sizeHint().width())
            if t.maximumWidth()!=natural:t.setMaximumWidth(natural);t.updateGeometry()
            available=t.viewport().width()
            if 0<len(widths)<=3 and sum(widths)>available>=len(widths)*80:
                total=sum(widths);widths=[80+int((available-80*len(widths))*w/total) for w in widths];widths[-1]+=available-sum(widths)
            for c,width in enumerate(widths):
                t.setColumnWidth(c,width)
                for r in range(t.rowCount()):
                    item=t.item(r,c)
                    if item is not None:
                        side=Qt.AlignmentFlag.AlignRight if c>0 and _NUMBER.fullmatch(item.text().strip()) else Qt.AlignmentFlag.AlignLeft
                        # Explicit alignment set by result contracts takes priority.
                        if not item.data(Qt.ItemDataRole.TextAlignmentRole):item.setTextAlignment(side|Qt.AlignmentFlag.AlignVCenter)
                        # Owner UI-D5: a cell that is only a figure keeps the number face (QG Interface).
                        if _NUMBER.fullmatch(item.text().strip()) and item.data(Qt.ItemDataRole.FontRole) is None:
                            from .font_policy import number_font
                            item.setFont(number_font(t.font()))
            t.verticalHeader().setMinimumSectionSize(max(34,m.height()+10));t.resizeRowsToContents()
        finally:self.measuring=False
def configure_compact_table(table):
    if not hasattr(table,'_compact_layout_controller'):table._compact_layout_controller=CompactTableLayout(table)
    return table
