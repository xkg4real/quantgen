"""Native Qt painting of the existing engine's percentile fan. No web view."""
import math
from dataclasses import dataclass
from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFontMetricsF, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from core.theme import LIGHT


@dataclass
class _ChartLayout:
    plot: QRectF
    footer: QRectF
    legends: list
    line_height: float
    x_tick_width: float
    minimum_height: int


def _chart_layout(widget, y_labels=(), x_labels=(), legends=(), footer=""):
    """Measure logical pixels with the actual font; Qt owns device scaling."""
    metrics = QFontMetricsF(widget.font())
    line_height = math.ceil(metrics.height()) + 2
    available = max(1, widget.width() - 24)
    entries, x, y = [], 12., 10.
    for name in legends:
        width = min(available, math.ceil(metrics.horizontalAdvance(name)) + 30)
        if x > 12 and x + width > widget.width() - 12:
            x, y = 12., y + line_height + 6
        text = metrics.elidedText(name, Qt.TextElideMode.ElideRight, max(1, width - 18))
        entries.append((QRectF(x + 14, y, max(1, width - 18), line_height), text))
        x += width
    top = y + line_height + 12 if entries else 18
    footer_height = math.ceil(metrics.boundingRect(
        QRectF(0, 0, available, 10000), Qt.TextFlag.TextWordWrap, footer).height()) if footer else 0
    footer_rect = QRectF(12, widget.height() - footer_height - 10, available, footer_height)
    bottom = footer_height + 22 + (line_height + 6 if x_labels else 0)
    tick_width = max((metrics.horizontalAdvance(s) for s in x_labels), default=0) + 6
    left = max(60, max((metrics.horizontalAdvance(s) for s in y_labels), default=0) + 20, tick_width / 2 + 8)
    right = max(24, tick_width / 2 + 8)
    return _ChartLayout(QRectF(left, top, max(1, widget.width()-left-right),
                              max(1, widget.height()-top-bottom)),
                        footer_rect, entries, line_height, tick_width, math.ceil(top + bottom + 140))


def _draw_y_tick(painter, layout, y, text):
    painter.drawText(QRectF(8, y-layout.line_height/2, layout.plot.left()-16, layout.line_height),
                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)


def _draw_x_tick(painter, layout, index, text):
    # Reduce tick density before labels can collide on narrow plots.
    spacing = layout.plot.width()/4
    indices = (0, 1, 2, 3, 4) if spacing >= layout.x_tick_width+6 else (
        (0, 2, 4) if spacing*2 >= layout.x_tick_width+6 else (0, 4))
    if index in indices:
        x = layout.plot.left() + spacing*index
        painter.drawText(QRectF(x-layout.x_tick_width/2, layout.plot.bottom()+6,
                               layout.x_tick_width, layout.line_height), Qt.AlignmentFlag.AlignCenter, text)


def _draw_chart_text(painter, layout, colors, footer, series_colors=()):
    for (rect, text), color in zip(layout.legends, series_colors):
        painter.setPen(QPen(QColor(color), 2))
        painter.drawLine(QPointF(rect.left()-12, rect.center().y()), QPointF(rect.left()-5, rect.center().y()))
        painter.setPen(QColor(colors.text))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
    painter.setPen(QColor(colors.muted))
    painter.drawText(layout.footer, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, footer)


class _CartesianChart(QWidget):
    def __init__(self, minimum_height, parent=None):
        super().__init__(parent)
        self._base_height = minimum_height
        self.setMinimumSize(350, minimum_height)

    def _legend_names(self):
        return []

    def _footer_text(self):
        return ""

    def _reserve_text_space(self):
        if not hasattr(self, '_base_height'):
            return
        names = self._legend_names()
        self.setToolTip('\n'.join(names))
        layout = _chart_layout(self, x_labels=('0',), legends=names, footer=self._footer_text())
        self.setMinimumHeight(max(self._base_height, layout.minimum_height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reserve_text_space()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._reserve_text_space()


class FanChart(_CartesianChart):
    def __init__(self, parent=None):
        super().__init__(240, parent)
        self.result = None
        self.colors = LIGHT
        self.setAccessibleName("Monte Carlo percentile fan, P5 to P95")

    def set_result(self, result):
        self.result = result
        self._reserve_text_space()
        self.update()

    def _footer_text(self):
        r = getattr(self, 'result', None)
        return f"0 → {r.horizon_days} sessions · P5 / P25 / P50 / P75 / P95" if r else ""

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
        lo, hi = min(r.fan[5]), max(r.fan[95])
        pad = max((hi-lo)*0.06, abs(hi)*0.001, 0.001)
        lo -= pad
        hi += pad
        ticks = [lo+(hi-lo)*i/4 for i in range(5)]
        labels = [f"{value:,.1f}" for value in ticks]
        footer = self._footer_text()
        layout = _chart_layout(self, labels, footer=footer)
        box = layout.plot
        def point(i, value):
            return QPointF(box.left()+box.width()*i/r.horizon_days,
                           box.bottom()-box.height()*(float(value)-lo)/(hi-lo))
        painter.setPen(QPen(QColor(p.border), 1))
        for i in range(5):
            value = ticks[i]
            y = point(0, value).y()
            painter.drawLine(QPointF(box.left(), y), QPointF(box.right(), y))
            painter.setPen(QColor(p.muted))
            _draw_y_tick(painter, layout, y, labels[i])
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
        _draw_chart_text(painter, layout, p, footer)


class FrontierChart(_CartesianChart):
    def __init__(self,parent=None):
        super().__init__(280, parent)
        self.output=None;self.colors=LIGHT
        self.setAccessibleName("Efficient frontier, annual volatility versus annual return")

    def set_output(self,output):
        self.output=output;self._reserve_text_space();self.update()

    def _legend_names(self):
        output = getattr(self, 'output', None)
        return [v.objective for v in output.portfolios.values()] if output else []

    def _footer_text(self):
        return "Annual volatility → · Y: annual return (historical estimate)"

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
        y_labels=[f"{ymin+(ymax-ymin)*i/4:.1%}" for i in range(5)]
        x_labels=[f"{xmin+(xmax-xmin)*i/4:.1%}" for i in range(5)]
        footer=self._footer_text()
        layout=_chart_layout(self,y_labels,x_labels,self._legend_names(),footer)
        box=layout.plot
        def point(x,y):return QPointF(box.left()+(float(x)-xmin)/(xmax-xmin)*box.width(),box.bottom()-(float(y)-ymin)/(ymax-ymin)*box.height())
        p.setPen(QPen(QColor(c.border),1))
        for i in range(5):
            y=ymin+(ymax-ymin)*i/4;x=xmin+(xmax-xmin)*i/4
            p.drawLine(point(xmin,y),point(xmax,y))
            p.setPen(QColor(c.muted));_draw_y_tick(p,layout,point(xmin,y).y(),y_labels[i])
            _draw_x_tick(p,layout,i,x_labels[i])
            p.setPen(QPen(QColor(c.border),1))
        cloud=QColor(c.accent);cloud.setAlpha(45);p.setPen(QPen(cloud,2))
        for x,y in zip(f.cloud_vols,f.cloud_rets):p.drawPoint(point(x,y))
        line=QPainterPath()
        for i,(x,y) in enumerate(zip(f.vols,f.rets)):
            if i:line.lineTo(point(x,y))
            else:line.moveTo(point(x,y))
        p.setPen(QPen(QColor(c.accent),2));p.drawPath(line)
        colors=(c.accent,'#4474A4','#84649C','#A85F7A')
        for index,value in enumerate(ports):
            center=point(value.ann_vol,value.ann_return)
            color=QColor(colors[index%len(colors)])
            p.setPen(QPen(color,2));p.setBrush(color);p.drawEllipse(center,4,4)
        _draw_chart_text(p,layout,c,footer,[colors[i%len(colors)] for i in range(len(ports))])


class LineChart(_CartesianChart):
    def __init__(self,x_label,y_label,parent=None):
        super().__init__(280, parent)
        self.x_label=x_label;self.y_label=y_label;self.series=[];self.x=[];self.colors=LIGHT
        self.setAccessibleName(y_label+' versus '+x_label)

    def set_series(self,x,series):
        self.x=list(x);self.series=series;self._reserve_text_space();self.update()

    def _legend_names(self):
        return [name for name,_ in getattr(self,'series',())]

    def _footer_text(self):
        return getattr(self,'x_label','')+' · '+getattr(self,'y_label','')

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.colors
        p.fillRect(self.rect(),QColor(c.surface))
        if not self.x or not self.series:return
        pairs=[[(float(x),float(y)) for x,y in zip(self.x,ys) if math.isfinite(float(x)) and math.isfinite(float(y))] for _,ys in self.series]
        values=[y for points in pairs for x,y in points]
        if not values:return
        xmin=min(x for points in pairs for x,y in points);xmax=max(x for points in pairs for x,y in points)
        ymin,ymax=min(values),max(values);pad=max((ymax-ymin)*.05,.001);ymin-=pad;ymax+=pad
        y_labels=[f'{ymin+(ymax-ymin)*i/4:,.2f}' for i in range(5)]
        x_labels=[f'{xmin+(xmax-xmin)*i/4:.2f}' for i in range(5)]
        footer=self._footer_text()
        layout=_chart_layout(self,y_labels,x_labels,self._legend_names(),footer)
        box=layout.plot
        def point(x,y):return QPointF(box.left()+(float(x)-xmin)/max(xmax-xmin,1e-9)*box.width(),box.bottom()-(float(y)-ymin)/(ymax-ymin)*box.height())
        for i in range(5):
            y=ymin+(ymax-ymin)*i/4;x=xmin+(xmax-xmin)*i/4
            p.setPen(QPen(QColor(c.border),1));p.drawLine(point(xmin,y),point(xmax,y))
            p.setPen(QColor(c.muted));_draw_y_tick(p,layout,point(xmin,y).y(),y_labels[i])
            _draw_x_tick(p,layout,i,x_labels[i])
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
        colors=(c.accent,'#4474A4','#84649C','#A85F7A','#9C7B30')
        _draw_chart_text(p,layout,c,footer,[colors[i%len(colors)] for i in range(len(self.series))])


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
