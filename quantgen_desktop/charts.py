"""Native Qt painting of the existing engine's percentile fan. No web view."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from core.theme import LIGHT


class FanChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.colors = LIGHT
        self.setMinimumSize(350, 240)
        self.setAccessibleName("Monte Carlo percentile fan, P5 to P95")

    def set_result(self, result):
        self.result = result
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = self.colors
        painter.fillRect(self.rect(), QColor(p.surface))
        if self.result is None:
            painter.setPen(QColor(p.muted))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "분석을 실행하면 P5–P95 분포가 표시됩니다.")
            return
        r = self.result
        box = QRectF(60, 18, self.width()-84, self.height()-58)
        lo, hi = min(r.fan[5]), max(r.fan[95])
        pad = max((hi-lo)*0.06, abs(hi)*0.001, 0.001)
        lo -= pad
        hi += pad
        def point(i, value):
            return QPointF(box.left()+box.width()*i/r.horizon_days,
                           box.bottom()-box.height()*(float(value)-lo)/(hi-lo))
        painter.setPen(QPen(QColor(p.border), 1))
        for i in range(5):
            value = lo+(hi-lo)*i/4
            y = point(0, value).y()
            painter.drawLine(QPointF(box.left(), y), QPointF(box.right(), y))
            painter.setPen(QColor(p.muted))
            painter.drawText(QRectF(0, y-9, 53, 18), Qt.AlignmentFlag.AlignRight, f"{value:,.1f}")
            painter.setPen(QPen(QColor(p.border), 1))
        for low, high, alpha in ((5,95,35), (25,75,65)):
            area = QPainterPath(point(0, r.fan[low][0]))
            for i, v in enumerate(r.fan[low]): area.lineTo(point(i,v))
            for i in range(r.horizon_days, -1, -1): area.lineTo(point(i,r.fan[high][i]))
            area.closeSubpath()
            color = QColor(p.accent); color.setAlpha(alpha)
            painter.fillPath(area, color)
        painter.setPen(QPen(QColor(p.accent), 2))
        line = QPainterPath(point(0, r.fan[50][0]))
        for i,v in enumerate(r.fan[50]): line.lineTo(point(i,v))
        painter.drawPath(line)
        painter.setPen(QColor(p.muted))
        painter.drawText(QRectF(box.left(), box.bottom()+12, box.width(), 24),
                         Qt.AlignmentFlag.AlignCenter, f"0 → {r.horizon_days} sessions · P5 / P25 / P50 / P75 / P95")


class FrontierChart(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.output=None;self.colors=LIGHT
        self.setMinimumSize(350,280)
        self.setAccessibleName("Efficient frontier, annual volatility versus annual return")

    def set_output(self,output):
        self.output=output;self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self.colors;p.fillRect(self.rect(),QColor(c.surface))
        if self.output is None:
            p.setPen(QColor(c.muted));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,"분석 후 효율적 프런티어가 표시됩니다.");return
        o=self.output;f=o.frontier;ports=list(o.portfolios.values())
        xs=[*f.cloud_vols,*f.vols,*[v.ann_vol for v in ports]]
        ys=[*f.cloud_rets,*f.rets,*[v.ann_return for v in ports]]
        xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
        dx=max(xmax-xmin,.001);dy=max(ymax-ymin,.001)
        xmin-=dx*.1;xmax+=dx*.1;ymin-=dy*.1;ymax+=dy*.1
        box=QRectF(65,24,self.width()-110,self.height()-70)
        def point(x,y):return QPointF(box.left()+(float(x)-xmin)/(xmax-xmin)*box.width(),box.bottom()-(float(y)-ymin)/(ymax-ymin)*box.height())
        p.setPen(QPen(QColor(c.border),1))
        for i in range(5):
            y=ymin+(ymax-ymin)*i/4;x=xmin+(xmax-xmin)*i/4
            p.drawLine(point(xmin,y),point(xmax,y))
            p.setPen(QColor(c.muted));p.drawText(QRectF(0,point(xmin,y).y()-8,58,18),Qt.AlignmentFlag.AlignRight,f"{y:.1%}")
            p.drawText(QRectF(point(x,ymin).x()-25,box.bottom()+5,50,18),Qt.AlignmentFlag.AlignCenter,f"{x:.1%}")
            p.setPen(QPen(QColor(c.border),1))
        cloud=QColor(c.accent);cloud.setAlpha(45);p.setPen(QPen(cloud,2))
        for x,y in zip(f.cloud_vols,f.cloud_rets):p.drawPoint(point(x,y))
        line=QPainterPath()
        for i,(x,y) in enumerate(zip(f.vols,f.rets)):
            if i:line.lineTo(point(x,y))
            else:line.moveTo(point(x,y))
        p.setPen(QPen(QColor(c.accent),2));p.drawPath(line)
        for index,value in enumerate(ports):
            center=point(value.ann_vol,value.ann_return)
            p.setBrush(QColor(c.surface));p.drawEllipse(center,5,5)
            p.drawText(QPointF(min(center.x()+8,self.width()-120),max(16,center.y()-8-index*2)),value.objective)
        p.setPen(QColor(c.muted));p.drawText(QRectF(box.left(),self.height()-24,box.width(),20),Qt.AlignmentFlag.AlignCenter,"Annual volatility → · Y: annual return (historical estimate)")
