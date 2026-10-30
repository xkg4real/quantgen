"""Native Qt painting of the existing engine's percentile fan. No web view."""
import math
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
        box=QRectF(65,40,self.width()-110,self.height()-86)
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
            color=QColor((c.accent,'#4474A4','#84649C','#A85F7A')[index])
            p.setPen(QPen(color,2));p.setBrush(color);p.drawEllipse(center,4,4)
            legend_x=65+index*(self.width()-100)/4
            p.drawEllipse(QPointF(legend_x,16),3,3)
            p.setPen(QColor(c.text));p.drawText(QPointF(legend_x+9,20),value.objective)
        p.setPen(QColor(c.muted));p.drawText(QRectF(box.left(),self.height()-24,box.width(),20),Qt.AlignmentFlag.AlignCenter,"Annual volatility → · Y: annual return (historical estimate)")


class LineChart(QWidget):
    def __init__(self,x_label,y_label,parent=None):
        super().__init__(parent)
        self.x_label=x_label;self.y_label=y_label;self.series=[];self.x=[];self.colors=LIGHT
        self.setMinimumSize(350,280)
        self.setAccessibleName(y_label+' versus '+x_label)

    def set_series(self,x,series):
        self.x=list(x);self.series=series;self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.colors
        p.fillRect(self.rect(),QColor(c.surface))
        if not self.x or not self.series:return
        pairs=[[(float(x),float(y)) for x,y in zip(self.x,ys) if math.isfinite(float(x)) and math.isfinite(float(y))] for _,ys in self.series]
        values=[y for points in pairs for x,y in points]
        if not values:return
        xmin=min(x for points in pairs for x,y in points);xmax=max(x for points in pairs for x,y in points)
        ymin,ymax=min(values),max(values);pad=max((ymax-ymin)*.05,.001);ymin-=pad;ymax+=pad
        columns=max(1,(self.width()-90)//160)
        top=18+20*math.ceil(len(self.series)/columns)
        box=QRectF(65,top,self.width()-90,self.height()-top-45)
        def point(x,y):return QPointF(box.left()+(float(x)-xmin)/max(xmax-xmin,1e-9)*box.width(),box.bottom()-(float(y)-ymin)/(ymax-ymin)*box.height())
        for i in range(5):
            y=ymin+(ymax-ymin)*i/4;x=xmin+(xmax-xmin)*i/4
            p.setPen(QPen(QColor(c.border),1));p.drawLine(point(xmin,y),point(xmax,y))
            p.setPen(QColor(c.muted));p.drawText(QRectF(0,point(xmin,y).y()-8,58,18),Qt.AlignmentFlag.AlignRight,f'{y:,.2f}')
            p.drawText(QRectF(point(x,ymin).x()-25,box.bottom()+5,50,18),Qt.AlignmentFlag.AlignCenter,f'{x:.2f}')
        for index,(name,ys) in enumerate(self.series):
            color=(c.accent,'#4474A4','#84649C','#A85F7A','#9C7B30')[index%5]
            p.setPen(QPen(QColor(color),2))
            line=QPainterPath();connected=False
            for x,y in zip(self.x,ys):
                if not math.isfinite(float(x)) or not math.isfinite(float(y)):
                    connected=False;continue
                if connected:line.lineTo(point(x,y))
                else:line.moveTo(point(x,y));connected=True
            p.drawPath(line)
            p.drawText(QPointF(65+(index%columns)*160,18+(index//columns)*20),name)
        p.setPen(QColor(c.muted));p.drawText(QRectF(box.left(),self.height()-22,box.width(),20),Qt.AlignmentFlag.AlignCenter,self.x_label+' · '+self.y_label)


class SignedBars(QWidget):
    """A zero-centered display: sign is spatial as well as written."""
    def __init__(self,rows,*,limit=None,parent=None):
        super().__init__(parent)
        self.rows=list(rows);self.colors=LIGHT
        finite=[abs(float(v)) for _,v in self.rows if math.isfinite(float(v))]
        self.limit=limit or max([1.,*finite])*1.1
        self.setMinimumWidth(350)
        self.setFixedHeight(34+len(self.rows)*28)
        self.setAccessibleName('Zero-centered values: '+', '.join(f'{n}: {v:+.2f}' for n,v in self.rows))

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self.colors;p.fillRect(self.rect(),QColor(c.surface))
        left=min(230,self.width()*.4);right=self.width()-64
        zero=(left+right)/2;half=(right-left)/2
        p.setPen(QColor(c.muted));p.drawText(QPointF(zero-4,15),'0')
        for i,(name,value) in enumerate(self.rows):
            y=28+i*28
            p.setPen(QColor(c.text));p.drawText(QRectF(8,y-10,left-16,22),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,
                p.fontMetrics().elidedText(name,Qt.TextElideMode.ElideRight,int(left-16)))
            p.setPen(QPen(QColor(c.border),1));p.drawLine(QPointF(zero,y-10),QPointF(zero,y+10))
            if not math.isfinite(float(value)):
                p.drawText(QPointF(right+10,y+5),'—');continue
            dx=max(-1,min(1,float(value)/self.limit))*half
            p.fillRect(QRectF(min(zero,zero+dx),y-6,abs(dx),12),QColor(c.accent))
            p.setPen(QColor(c.text));p.drawText(QPointF(right+8,y+5),f'{value:+.2f}')
