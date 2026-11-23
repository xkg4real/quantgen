"""Native Qt painting of the existing engine's percentile fan. No web view."""
import math
from dataclasses import dataclass
import re
from PyQt6.QtCore import QEvent, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFontMetricsF, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from core.theme import LIGHT
from .translations import display


def _axis_number(widget,value,digits=2,*,percent=False,group=True):
    ctx=getattr(widget.window(),'ctx',None)
    if ctx:return ctx.percent(value,digits) if percent else ctx.number(value,digits)
    return format(value,('.'+str(digits)+'%') if percent else (',' if group else '')+'.'+str(digits)+'f')


_TENOR = re.compile(r'(\d+(?:\.\d+)?)([dwmy])')
_TENOR_KO = {'d': '일물', 'w': '주물', 'm': '개월물', 'y': '년물'}
_PCA_KO = re.compile(r'pc(\d+)')


def chart_text(widget, text):
    """Axis captions and series names in the window language (owner issue 02, 2026-11-10).

    Korean comes first from the chart-only vocabulary (owner_ui_language.charts.CHART_TERMS), then tenor
    names ('2y' -> '2년물', as the Flet charts), then the window catalogue. Display only: the chart keeps
    the source names, and exports never see this text."""
    text = str(text)
    if getattr(widget.window(), 'ui_language', None) == 'ko':
        from .owner_ui_language.charts import CHART_TERMS
        if text in CHART_TERMS:
            return CHART_TERMS[text]
        tenor = _TENOR.fullmatch(text)
        if tenor:
            return tenor.group(1) + _TENOR_KO[tenor.group(2)]
        factor = _PCA_KO.fullmatch(text)
        if factor:
            return '주성분 ' + factor.group(1)
    return display(widget, text)


def nice_ticks(lo, hi, count=4, *, integer=False):
    """Round tick values inside [lo, hi]: steps of 1, 2, 2.5 or 5 times a power of ten, whole steps for
    counts (owner issue 02: axes read '0.00 180.50 361.00'). Returns (ticks, step); ([], 0) when the span
    is empty or not finite."""
    if not (math.isfinite(lo) and math.isfinite(hi)) or hi <= lo:
        return [], 0
    raw = (hi - lo) / max(1, count)
    power = 10 ** math.floor(math.log10(raw))
    multiples = (1, 2, 5, 10) if integer and power < 10 else (1, 2, 2.5, 5, 10)
    step = min((m * power for m in multiples), key=lambda s: abs(math.log(s / raw)))   # the nearest round step
    if integer:
        step = max(1, round(step))
    first = math.ceil(lo / step - 1e-9)
    ticks = []
    while True:
        value = (first + len(ticks)) * step
        if value > hi + step * 1e-9 or len(ticks) > 50:
            break
        ticks.append(0.0 if abs(value) < step * 1e-9 else value)
    return ticks, step


def tick_digits(step):
    """Decimals a tick step needs: 0.25 -> 2, 5 -> 0."""
    for digits in range(0, 8):
        scaled = step * 10 ** digits
        if abs(scaled - round(scaled)) < 1e-6 * max(1., scaled):
            return digits
    return 8


@dataclass
class _ChartLayout:
    plot: QRectF
    footer: QRectF
    legends: list
    line_height: float
    x_tick_width: float
    minimum_height: int
    caption: QRectF = None


def _chart_layout(widget, y_labels=(), x_labels=(), legends=(), footer="", caption=""):
    """Measure logical pixels with the actual font; Qt owns device scaling.

    `caption` (the y-axis caption) gets its own line above the plot, so the footer names only the x axis."""
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
    caption_rect = None
    if caption:
        caption_rect = QRectF(12, top - (4 if entries else 8), available, line_height)
        top = caption_rect.bottom() + line_height / 2 + 4
    footer_height = math.ceil(metrics.boundingRect(
        QRectF(0, 0, available, 10000), Qt.TextFlag.TextWordWrap, footer).height()) if footer else 0
    footer_rect = QRectF(12, widget.height() - footer_height - 10, available, footer_height)
    bottom = footer_height + 22 + (line_height + 6 if x_labels else 0)
    tick_width = max((metrics.horizontalAdvance(s) for s in x_labels), default=0) + 6
    left = max(60, max((metrics.horizontalAdvance(s) for s in y_labels), default=0) + 20, tick_width / 2 + 8)
    right = max(24, tick_width / 2 + 8)
    return _ChartLayout(QRectF(left, top, max(1, widget.width()-left-right),
                              max(1, widget.height()-top-bottom)),
                        footer_rect, entries, line_height, tick_width, math.ceil(top + bottom + 140),
                        caption_rect)


def _number_face(painter):
    """Owner UI-D5: tick figures keep the number face (QG Interface); the caller restores the font."""
    from .font_policy import number_font
    painter.save()
    painter.setFont(number_font(painter.font()))


def _draw_y_tick(painter, layout, y, text):
    _number_face(painter)
    painter.drawText(QRectF(8, y-layout.line_height/2, layout.plot.left()-16, layout.line_height),
                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)
    painter.restore()


def _draw_x_tick(painter, layout, index, text):
    # Reduce tick density before labels can collide on narrow plots.
    spacing = layout.plot.width()/4
    indices = (0, 1, 2, 3, 4) if spacing >= layout.x_tick_width+6 else (
        (0, 2, 4) if spacing*2 >= layout.x_tick_width+6 else (0, 4))
    if index in indices:
        x = layout.plot.left() + spacing*index
        _number_face(painter)
        painter.drawText(QRectF(x-layout.x_tick_width/2, layout.plot.bottom()+6,
                               layout.x_tick_width, layout.line_height), Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


def _draw_x_ticks_at(painter, layout, ticks):
    """Ticks at their own x positions, [(x, text)] in plot order; thinned until no two labels touch."""
    _number_face(painter)
    metrics = QFontMetricsF(painter.font())
    shown = list(ticks)
    for stride in range(1, len(ticks) + 1):
        shown = ticks[::stride]
        widths = [metrics.horizontalAdvance(text) + 6 for _, text in shown]
        if all(b[0] - a[0] >= (wa + wb) / 2 + 6
               for (a, wa), (b, wb) in zip(zip(shown, widths), zip(shown[1:], widths[1:]))):
            break
    for x, text in shown:
        width = metrics.horizontalAdvance(text) + 6
        left = min(max(2., x - width / 2), painter.device().width() - width - 2)
        painter.drawText(QRectF(left, layout.plot.bottom() + 6, width, layout.line_height),
                         Qt.AlignmentFlag.AlignCenter, text)
    painter.restore()


def _draw_chart_text(painter, layout, colors, footer, series_colors=(), caption=""):
    for (rect, text), color in zip(layout.legends, series_colors):
        painter.setPen(QPen(QColor(color), 2))
        painter.drawLine(QPointF(rect.left()-12, rect.center().y()), QPointF(rect.left()-5, rect.center().y()))
        painter.setPen(QColor(colors.text))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
    painter.setPen(QColor(colors.muted))
    if caption and layout.caption is not None:
        painter.drawText(layout.caption, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         QFontMetricsF(painter.font()).elidedText(caption, Qt.TextElideMode.ElideRight,
                                                                  layout.caption.width()))
    painter.drawText(layout.footer, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, footer)


class _CartesianChart(QWidget):
    # Owner, 2026-11-11: charts read "too wide and too short". A chart's height follows its width
    # (ASPECT), within [minimum height, MAX_HEIGHT], and a chart is never wider than MAX_WIDTH.
    ASPECT = 0.5
    MAX_HEIGHT = 440
    MAX_WIDTH = 920

    def __init__(self, minimum_height, parent=None):
        super().__init__(parent)
        self._base_height = minimum_height
        self.setMinimumSize(350, minimum_height)
        self.setMaximumWidth(self.MAX_WIDTH)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return max(self.minimumHeight(), min(self.MAX_HEIGHT, round(width * self.ASPECT)))

    def sizeHint(self):
        width = min(self.MAX_WIDTH, max(self.minimumWidth(), self.width()))
        return QSize(width, self.heightForWidth(width))

    def _legend_names(self):
        return []

    def _footer_text(self):
        return ""

    def _caption_text(self):
        return ""

    def _reserve_text_space(self):
        if not hasattr(self, '_base_height'):
            return
        names = self._legend_names()
        self.setToolTip('\n'.join(names))
        layout = _chart_layout(self, x_labels=('0',), legends=names, footer=self._footer_text(),
                               caption=self._caption_text())
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
        return display(self, f"0 → {r.horizon_days} sessions · P5 / P25 / P50 / P75 / P95") if r else ""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = self.colors
        painter.fillRect(self.rect(), QColor(p.surface))
        if self.result is None:
            painter.setPen(QColor(p.muted))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, display(self, "분석을 실행하면 P5–P95 분포가 표시됩니다."))
            return
        r = self.result
        lo, hi = min(r.fan[5]), max(r.fan[95])
        pad = max((hi-lo)*0.06, abs(hi)*0.001, 0.001)
        lo -= pad
        hi += pad
        ticks = [lo+(hi-lo)*i/4 for i in range(5)]
        labels = [_axis_number(self,value,1) for value in ticks]
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

    # Display names of the optimiser objectives (risk area request, 2026-11-10: no raw ids such as
    # max_sharpe in the English legend). Korean comes from the window catalogue entry of the id itself.
    OBJECTIVE_NAMES = {'max_sharpe': 'Max Sharpe', 'min_vol': 'Minimum volatility',
                       'risk_parity': 'Risk parity', 'equal_weight': 'Equal weight'}

    def _legend_names(self):
        output = getattr(self, 'output', None)
        if not output:
            return []
        korean = getattr(self.window(), 'ui_language', None) == 'ko'
        return [display(self, v.objective if korean else self.OBJECTIVE_NAMES.get(v.objective, v.objective))
                for v in output.portfolios.values()]

    def _footer_text(self):
        return display(self, "Annual volatility → · Y: annual return (historical estimate)")

    # The approved page draft (owner 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_05_risk.png): random
    # portfolios as faint dots, the frontier as the accent line, the capital market line dashed from the risk-free
    # rate through the max-Sharpe point, single assets as small squares and the four objectives as rings with a name
    # pill (the selected one filled). Axis figures on the right and below; the axis caption and a legend of the marks
    # close the chart. Display only: every mark is a value of the optimiser output (single assets are its mean
    # returns and the diagonal of its covariance), nothing is recomputed.
    ASPECT = 0.42

    def _say(self, english, korean):
        return korean if getattr(self.window(), 'ui_language', None) == 'ko' else english

    def _font(self, pixels, weight=None, *, figures=False):
        from PyQt6.QtGui import QFont
        font = QFont(self.font())
        font.setPixelSize(pixels)
        if weight is not None:
            font.setWeight(QFont.Weight(weight))
        if figures:
            from .font_policy import number_font
            font = number_font(font)
        return font

    @staticmethod
    def _finite(*values):
        try:
            return all(math.isfinite(float(v)) for v in values)
        except (TypeError, ValueError):
            return False

    def _marks(self):
        """What the plot shows, read from the output: cloud and frontier points, the objectives
        [(name, vol, return, sharpe or None, selected)], the single assets [(symbol, vol, return)] and the capital
        market line (risk-free rate, slope) or None."""
        o = self.output
        f = o.frontier

        def pairs(xs, ys):
            xs = list(xs) if xs is not None else []
            ys = list(ys) if ys is not None else []
            return [(float(x), float(y)) for x, y in zip(xs, ys) if self._finite(x, y)]
        cloud = pairs(getattr(f, 'cloud_vols', None), getattr(f, 'cloud_rets', None))
        curve = pairs(getattr(f, 'vols', None), getattr(f, 'rets', None))
        request = getattr(o, 'request', None)
        chosen = getattr(request, 'objective', None)
        objectives = []
        for name, (key, value) in zip(self._legend_names(), o.portfolios.items()):
            if not self._finite(value.ann_vol, value.ann_return):
                continue
            sharpe = getattr(value, 'sharpe', None)
            objectives.append((name, float(value.ann_vol), float(value.ann_return),
                               float(sharpe) if self._finite(sharpe) else None,
                               getattr(value, 'objective', key) == chosen))
        assets = []
        stats = getattr(o, 'stats', None)
        cov, mean = getattr(stats, 'cov', None), getattr(stats, 'mean_returns', None)
        if cov is not None and mean is not None:
            for index, symbol in enumerate(getattr(stats, 'symbols', ())):
                try:
                    variance, ret = float(cov[index][index]), float(mean[index])
                except (IndexError, TypeError, ValueError):
                    continue
                if variance >= 0 and self._finite(variance, ret):
                    assets.append((str(symbol), math.sqrt(variance), ret))
        line = None
        rf = getattr(request, 'rf_rate', None)
        best = o.portfolios.get('max_sharpe') if hasattr(o.portfolios, 'get') else None
        if best is not None and self._finite(rf, best.ann_vol, best.ann_return) and float(best.ann_vol) > 0:
            line = (float(rf), (float(best.ann_return) - float(rf)) / float(best.ann_vol))
        return cloud, curve, objectives, assets, line

    def _legend(self, marks):
        cloud, curve, objectives, assets, line = marks
        entries = [('line', self._say('Efficient frontier', '효율적 프런티어'))]
        if line is not None:
            rf = _axis_number(self, line[0], 2, percent=True)
            entries.append(('dash', self._say(f'Capital market line · risk-free {rf}', f'자본시장선 · 무위험 {rf}')))
        if cloud:
            count = f'{len(cloud):,}'
            entries.append(('dot', self._say(f'{count} random portfolios', f'무작위 조합 {count}개')))
        if assets:
            entries.append(('square', self._say('Single assets', '개별 종목')))
        return entries

    def _frame(self, marks=None):
        """(plot rectangle, footer rows [(x, y, kind or None, text, width)], line height, minimum height) for the
        current size: the y caption above the plot, figures right and below, the axis caption and legend last."""
        small = QFontMetricsF(self._font(11))
        figures = QFontMetricsF(self._font(11, figures=True))
        width, height = self.width(), self.height()
        caption = self._say('X: annual volatility · Y: annual expected return (historical estimate)',
                            '가로 연 변동성 · 세로 연 기대수익률 (과거 추정)')
        entries = self._legend(marks) if marks is not None else []
        line = math.ceil(small.height()) + 2
        usable = max(40., width - 24)
        items = [(kind, text, max(1., min(usable - 22, small.horizontalAdvance(text) + 1))) for kind, text in entries]
        legend_width = sum(w + 21 for _, _, w in items) + 14 * max(0, len(items) - 1)
        caption_width = small.horizontalAdvance(caption) + 1
        rows, y = [], 0.
        if caption_width + 24 + legend_width <= usable:    # one row: the caption left, the legend right
            rows.append((12., y, None, caption, caption_width))
            x = width - 12 - legend_width
            for kind, text, w in items:
                rows.append((x, y, kind, text, w))
                x += w + 21 + 14
            y += line
        else:
            lines = max(1, math.ceil(caption_width / usable))
            rows.append((12., y, None, caption, usable))
            y += line * lines + 4
            x = 12.
            for kind, text, w in items:
                if x > 12 and x + w + 21 > width - 12:
                    x, y = 12., y + line + 2
                rows.append((x, y, kind, text, w))
                x += w + 21 + 14
            y += line if items else 0
        top = line + 8                                     # '↑ annual expected return' above the plot
        right = max(figures.horizontalAdvance(t) for t in ('−100%', '100%', '00.0%', '−00.0%')) + 14
        bottom = math.ceil(figures.height()) + 12 + y + 10
        plot = QRectF(10, top, max(1., width - 10 - right), max(1., height - top - bottom))
        footer_top = height - y - 8
        return (plot, [(x, footer_top + row_y, kind, text, w) for x, row_y, kind, text, w in rows], line,
                math.ceil(top + bottom + 150))

    def _reserve_text_space(self):
        if not hasattr(self, '_base_height'):
            return
        self.setToolTip('\n'.join(self._legend_names()))
        marks = self._marks() if getattr(self, 'output', None) is not None else None
        self.setMinimumHeight(max(self._base_height, self._frame(marks)[3]))

    def paintEvent(self,event):
        from .typography import mix
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self.colors;p.fillRect(self.rect(),QColor(c.surface))
        if self.output is None:
            p.setPen(QColor(c.muted));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,display(self, "분석 후 효율적 프런티어가 표시됩니다."));return
        marks=self._marks()
        cloud,curve,objectives,assets,cml=marks
        box,footer,line_height,_=self._frame(marks)
        xs=[x for x,_ in cloud+curve]+[o[1] for o in objectives]+[a[1] for a in assets]
        ys=[y for _,y in cloud+curve]+[o[2] for o in objectives]+[a[2] for a in assets]
        if not xs:
            return
        xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
        dx=max(xmax-xmin,.001);dy=max(ymax-ymin,.001)
        xmin-=dx*.07;xmax+=dx*.07;ymin-=dy*.1;ymax+=dy*.12
        def point(x,y):return QPointF(box.left()+(float(x)-xmin)/(xmax-xmin)*box.width(),box.bottom()-(float(y)-ymin)/(ymax-ymin)*box.height())
        dashed=QColor(mix(c.border,c.surface,.3));faint=QColor(mix(c.muted,c.surface,.45))
        # Grid and axis figures: returns on the right, volatility below, in round percent steps.
        p.setFont(self._font(11,figures=True));figures=QFontMetricsF(p.font())
        y_ticks,y_step=nice_ticks(ymin,ymax,4);x_ticks,x_step=nice_ticks(xmin,xmax,5)
        y_digits=tick_digits(y_step*100);x_digits=tick_digits(x_step*100)
        for value in y_ticks:
            y=point(xmin,value).y()
            pen=QPen(dashed,1);pen.setDashPattern([3,4]);p.setPen(pen)
            p.drawLine(QPointF(box.left(),y),QPointF(box.right(),y))
            p.setPen(QColor(c.muted))
            p.drawText(QRectF(box.right()+8,y-figures.height()/2,self.width()-box.right()-10,figures.height()),
                       Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,_axis_number(self,value,y_digits,percent=True))
        placed=[]
        for value in x_ticks:
            x=point(value,ymin).x();text=_axis_number(self,value,x_digits,percent=True)
            p.setPen(QPen(QColor(mix(c.border,c.surface,.5)),1));p.drawLine(QPointF(x,box.top()),QPointF(x,box.bottom()))
            w=figures.horizontalAdvance(text)+6;left=min(max(2.,x-w/2),self.width()-w-2)
            if any(left<right+6 and left+w>start-6 for start,right in placed):continue
            placed.append((left,left+w));p.setPen(QColor(c.muted))
            p.drawText(QRectF(left,box.bottom()+6,w,figures.height()),Qt.AlignmentFlag.AlignCenter,text)
        p.setFont(self._font(11));small=QFontMetricsF(p.font())
        p.setPen(faint)
        p.drawText(QRectF(box.left(),box.top()-line_height-6,box.width(),line_height),
                   Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,
                   small.elidedText(self._say('↑ annual expected return','↑ 연 기대수익률'),Qt.TextElideMode.ElideRight,box.width()))
        # The marks, clipped to the plot.
        p.save();p.setClipRect(box.adjusted(-6,-6,6,6))
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(mix(c.muted,c.surface,.68)))
        for x,y in cloud:p.drawEllipse(point(x,y),2.,2.)
        if cml is not None:
            rf,slope=cml;pen=QPen(faint,1.3);pen.setDashPattern([5,4]);p.setPen(pen)
            p.drawLine(point(xmin,rf+slope*xmin),point(xmax,rf+slope*xmax))
        if len(curve)>1:
            path=QPainterPath(point(*curve[0]))
            for x,y in curve[1:]:path.lineTo(point(x,y))
            p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(c.accent),2.2));p.drawPath(path)
        p.restore()
        obstacles=[]
        p.setFont(self._font(11,500));labels=QFontMetricsF(p.font())
        for symbol,x,y in assets:
            at=point(x,y);square=QRectF(at.x()-4,at.y()-4,8,8)
            p.setPen(QPen(QColor(c.muted),1.4));p.setBrush(QColor(c.surface));p.drawRoundedRect(square,2,2)
            w=labels.horizontalAdvance(symbol)+2;h=labels.height()
            rect=QRectF(at.x()+9,at.y()-h/2,w,h)
            if rect.right()>self.width()-2:rect.moveRight(at.x()-9)
            rect.moveTop(min(max(1.,rect.top()),self.height()-h-1))
            p.setPen(QColor(c.muted));p.drawText(rect,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,symbol)
            obstacles+=[square.adjusted(-2,-2,2,2),rect]
        centers=[(point(vol,ret),selected) for _,vol,ret,_,selected in objectives]
        obstacles=[(rect,1.) for rect in obstacles]+[(QRectF(at.x()-8,at.y()-8,16,16),8.) for at,_ in centers]
        for (x0,y0),(x1,y1) in zip(curve,curve[1:]):   # pills keep off the frontier line
            for step in range(4):
                at=point(x0+(x1-x0)*step/4,y0+(y1-y0)*step/4);obstacles.append((QRectF(at.x()-3,at.y()-3,6,6),2.))
        self._paint_pills(p,box,objectives,centers,obstacles,c)
        for at,selected in centers:
            if selected:
                p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(c.accent_soft));p.drawEllipse(at,11.,11.)
                p.setPen(QPen(QColor(c.surface),1.6));p.setBrush(QColor(c.accent));p.drawEllipse(at,5.5,5.5)
            else:
                p.setPen(QPen(QColor(c.text),1.7));p.setBrush(QColor(c.surface));p.drawEllipse(at,5.,5.)
        self._paint_footer(p,footer,line_height,c,faint)

    def _paint_pills(self, p, box, objectives, centers, obstacles, c):
        """A name pill per objective ('Max Sharpe · 0.703') in the free space next to its ring, the selected first.
        `obstacles` are (rectangle, weight): rings weigh most, then the frontier line, assets and their labels. On a
        narrow plot the pills are smaller and leave the Sharpe ratio to the comparison table."""
        from .typography import mix
        compact = box.width() < 520
        taken = []
        for index in sorted(range(len(objectives)), key=lambda i: not objectives[i][4]):
            name, _, _, sharpe, selected = objectives[index]
            at = centers[index][0]
            size = 11 if compact else 12
            name_font = self._font(size, 600 if selected else 500)
            figure_font = self._font(size, 600 if selected else 500, figures=True)
            nm, fm = QFontMetricsF(name_font), QFontMetricsF(figure_font)
            figure = f'· {sharpe:.3f}' if sharpe is not None and not compact else ''
            figure_width = fm.horizontalAdvance(figure) + 1 if figure else 0.
            pad = 7 if compact else 10
            name_width = max(1., min(nm.horizontalAdvance(name) + 1,
                                     box.width() - 2 * pad - 4 - (figure_width + 5 if figure else 0)))
            width = pad + name_width + (5 + figure_width if figure else 0) + pad
            height = max(nm.height(), fm.height()) + (6 if compact else 8)
            px, py = at.x(), at.y()
            candidates = []
            for lift in (26, 50, 76, 104):              # rings of places, nearest first; above the curve is free
                candidates += [(px - 14 - width, py - lift - height / 2), (px + 14, py - lift - height / 2),
                               (px - width / 2, py - lift - height)]
                if lift == 26:
                    candidates += [(px - 20 - width, py - height / 2), (px + 20, py - height / 2),
                                   (px + 14, py + 18 - height / 2), (px - 14 - width, py + 18 - height / 2)]
            best = None
            for rank, (x, y) in enumerate(candidates):
                cx = min(max(box.left() + 2, x), box.right() - width - 2)
                cy = min(max(box.top() + 2, y), box.bottom() - height - 2)
                rect = QRectF(cx, cy, width, height)
                crowd = sum(weight * self._overlap(rect.adjusted(-4, -4, 4, 4), other)
                            for other, weight in obstacles + [(r, 8.) for r in taken])
                score = (round(crowd), abs(cx - x) + abs(cy - y) > 24, rank)
                if best is None or score < best[0]:
                    best = (score, rect)
            rect = best[1]
            taken.append(rect)
            edge = QPointF(min(max(px, rect.left()), rect.right()), min(max(py, rect.top()), rect.bottom()))
            p.setPen(QPen(QColor(c.accent if selected else mix(c.muted, c.surface, .45)), 1.2))
            p.drawLine(edge, at)
            if selected:
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(c.accent))
            else:
                p.setPen(QPen(QColor(mix(c.border, c.surface, .1)), 1)); p.setBrush(QColor(c.surface))
            p.drawRoundedRect(rect, 7, 7)
            p.setPen(QColor(c.on_accent if selected else c.text))
            p.setFont(name_font)
            text_rect = QRectF(rect.left() + pad, rect.top(), name_width, rect.height())
            p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       nm.elidedText(name, Qt.TextElideMode.ElideRight, name_width))
            if figure:
                p.setFont(figure_font)
                p.drawText(QRectF(text_rect.right() + 5, rect.top(), figure_width, rect.height()),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, figure)

    @staticmethod
    def _overlap(a, b):
        r = a.intersected(b)
        return 0. if r.isEmpty() else r.width() * r.height()

    def _paint_footer(self, p, rows, line_height, c, faint):
        """The axis caption on the left and the legend of the marks (line, dashed line, dot, square)."""
        from .typography import mix
        p.setFont(self._font(11)); metrics = QFontMetricsF(p.font())
        for x, y, kind, text, width in rows:
            if kind is None:
                lines = max(1, math.ceil(metrics.horizontalAdvance(text) / max(1., width)))
                p.setPen(QColor(c.muted))
                p.drawText(QRectF(x, y, width, line_height * lines),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, text)
                continue
            mid = y + line_height / 2
            if kind == 'line':
                p.setPen(QPen(QColor(c.accent), 2)); p.drawLine(QPointF(x, mid), QPointF(x + 16, mid))
            elif kind == 'dash':
                pen = QPen(faint, 1.4); pen.setDashPattern([3, 2]); p.setPen(pen)
                p.drawLine(QPointF(x, mid), QPointF(x + 16, mid))
            elif kind == 'dot':
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(mix(c.muted, c.surface, .68)))
                p.drawEllipse(QPointF(x + 8, mid), 3., 3.)
            else:
                p.setPen(QPen(QColor(c.muted), 1.3)); p.setBrush(QColor(c.surface))
                p.drawRoundedRect(QRectF(x + 4, mid - 4, 8, 8), 2, 2)
            p.setPen(QColor(c.muted))
            p.drawText(QRectF(x + 21, y, width, line_height), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       metrics.elidedText(text, Qt.TextElideMode.ElideRight, width))


class LineChart(_CartesianChart):
    """Series against a shared x axis. Ticks are round values (whole numbers for observation counts), the
    y-axis caption sits above the plot and the x-axis caption below it, both in the window language
    (owner issue 02, 2026-11-10). The series and their source names are unchanged."""
    def __init__(self,x_label,y_label,parent=None):
        super().__init__(280, parent)
        self.x_label=x_label;self.y_label=y_label;self.series=[];self.x=[];self.colors=LIGHT
        self.setAccessibleName(y_label+' versus '+x_label)

    def set_series(self,x,series):
        self.x=list(x);self.series=series;self._reserve_text_space();self.update()

    def _legend_names(self):
        return [chart_text(self, name) for name,_ in getattr(self,'series',())]

    def _footer_text(self):
        return chart_text(self, getattr(self,'x_label',''))

    def _caption_text(self):
        return chart_text(self, getattr(self,'y_label',''))

    def _ticks(self, lo, hi, count, whole):
        """[(value, text)] at round values; as many decimals as the step needs (0.002 -> 3), so a small
        span never repeats a label, and never '-0' (owner issue 02; market area request 2026-11-10)."""
        ticks, step = nice_ticks(lo, hi, count, integer=whole)
        if len(ticks) < 2:
            ticks = [lo, hi] if hi > lo else [lo]
            step = (hi - lo) or abs(lo) or 1.
        digits = 0 if whole else tick_digits(step)
        return [(v, _axis_number(self, round(v, digits) + 0., digits)) for v in ticks]

    def _x_ticks(self, xmin, xmax):
        """Whole numbers when every x is a whole number (observation counts), never '125.75'."""
        whole = all(float(x).is_integer() for x in self.x if math.isfinite(float(x)))
        return self._ticks(xmin, xmax, 6, whole)

    def _y_ticks(self, ymin, ymax):
        return self._ticks(ymin, ymax, 5, False)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.colors
        p.fillRect(self.rect(),QColor(c.surface))
        if not self.x or not self.series:return
        pairs=[[(float(x),float(y)) for x,y in zip(self.x,ys) if math.isfinite(float(x)) and math.isfinite(float(y))] for _,ys in self.series]
        values=[y for points in pairs for x,y in points]
        if not values:return
        xmin=min(x for points in pairs for x,y in points);xmax=max(x for points in pairs for x,y in points)
        # A 5% margin of the data's own span (a fixed .001 flattened small series such as densities).
        ymin,ymax=min(values),max(values);pad=(ymax-ymin)*.05 if ymax>ymin else max(abs(ymax)*.05,.001);ymin-=pad;ymax+=pad
        y_ticks=self._y_ticks(ymin,ymax)
        x_ticks=self._x_ticks(xmin,xmax)
        footer=self._footer_text();caption=self._caption_text()
        layout=_chart_layout(self,[t for _,t in y_ticks],[t for _,t in x_ticks],self._legend_names(),footer,caption)
        box=layout.plot
        def point(x,y):return QPointF(box.left()+(float(x)-xmin)/max(xmax-xmin,1e-9)*box.width(),box.bottom()-(float(y)-ymin)/(ymax-ymin)*box.height())
        for y,text in y_ticks:
            p.setPen(QPen(QColor(c.border),1));p.drawLine(point(xmin,y),point(xmax,y))
            p.setPen(QColor(c.muted));_draw_y_tick(p,layout,point(xmin,y).y(),text)
        p.setPen(QPen(QColor(c.border),1));p.drawLine(QPointF(box.left(),box.bottom()),QPointF(box.right(),box.bottom()))
        for x,_ in x_ticks:
            px=point(x,ymin).x();p.drawLine(QPointF(px,box.bottom()),QPointF(px,box.bottom()+4))
        p.setPen(QColor(c.muted));_draw_x_ticks_at(p,layout,[(point(x,ymin).x(),text) for x,text in x_ticks])
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
        _draw_chart_text(p,layout,c,footer,[colors[i%len(colors)] for i in range(len(self.series))],caption)


class SignedBars(QWidget):
    """A zero-centered display: sign is spatial as well as written."""
    def __init__(self,rows,*,limit=None,parent=None):
        super().__init__(parent)
        self.rows=list(rows);self.colors=LIGHT
        self.localized_labels = {}
        finite=[abs(float(v)) for _,v in self.rows if math.isfinite(float(v))]
        self.limit=limit or max([1.,*finite])*1.1
        self.setMinimumWidth(350)
        self.setFixedHeight(34+len(self.rows)*28)
        self.setAccessibleName('Zero-centered values: '+', '.join(f'{n}: {v:+.2f}' for n,v in self.rows))

    def display_label(self, index):
        """Only captions explicitly tagged by the originating pane translate."""
        language = getattr(self.window(), 'ui_language', None)
        return self.localized_labels.get(index, {}).get(language, self.rows[index][0])

    # ------------------------------------------------------------------ z-score reading (owner issue 02)
    Z_ROW = 28

    def show_zscores(self, *, groups, group_names, texts, hatched=()):
        """Draw the rows as 1-year z-scores the way the Flet macro chart reads (PR #98).

        `groups` gives each row's group key (bar colour, a rule between groups, one legend entry each),
        `group_names` {key: {'ko': .., 'en': ..}}, `hatched` the row indices drawn hatched (synthetic data,
        named once in the legend instead of on every row) and `texts` the band, unusual, axis and synthetic
        captions as {'ko': .., 'en': ..}. The usual range |z| < 1 is shaded, |z| = 2 is dashed and every
        value is printed at its bar end. Rows, values and the export are unchanged."""
        self.zscore = {'groups': list(groups), 'names': dict(group_names), 'texts': dict(texts),
                       'hatched': set(hatched)}
        self._reserve_text_space()
        self.update()

    def _z_language(self):
        return 'ko' if getattr(self.window(), 'ui_language', None) == 'ko' else 'en'

    def _z_text(self, key):
        value = self.zscore['texts'].get(key, {})
        return value.get(self._z_language(), value.get('en', ''))

    def _z_colors(self):
        c = self.colors
        return {'rates': c.accent, 'credit': c.error, 'fx': c.success, 'risk': c.muted}

    def _z_legend(self, metrics, width):
        """[(swatch rect, text rect, text, colour, hatched)] wrapped to `width`, and the number of lines."""
        language = self._z_language()
        colors = self._z_colors()
        items = [(self.zscore['names'].get(g, {}).get(language, g), colors.get(g, self.colors.text), False)
                 for g in dict.fromkeys(self.zscore['groups'])]
        if self.zscore['hatched']:
            items.append((self._z_text('synthetic'), self.colors.muted, True))
        line = math.ceil(metrics.height()) + 2
        out, x, y, lines = [], 12., 0., 1
        for text, color, hatched in items:
            w = metrics.horizontalAdvance(text) + 36
            if x > 12 and x + w > width - 12:
                x, y, lines = 12., y + line + 6, lines + 1
            out.append((QRectF(x, y + (line - 12) / 2, 12, 12), QRectF(x + 18, y, w - 30, line), text, color,
                        hatched))
            x += w
        return out, lines

    def _z_height(self):
        metrics = QFontMetricsF(self.font())
        line = math.ceil(metrics.height()) + 2
        _, lines = self._z_legend(metrics, max(350, self.width()))
        return math.ceil(line + 16 + len(self.rows) * self.Z_ROW + 2 * (line + 4) + 10 + lines * (line + 6) + 8)

    def _reserve_text_space(self):
        if getattr(self, 'zscore', None):
            self.setFixedHeight(self._z_height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().width() != event.oldSize().width():
            self._reserve_text_space()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._reserve_text_space()

    def _paint_zscores(self, p):
        c = self.colors
        metrics = QFontMetricsF(self.font())
        line = math.ceil(metrics.height()) + 2
        names = [self.display_label(i) for i in range(len(self.rows))]
        label_w = min(max((metrics.horizontalAdvance(n) for n in names), default=0) + 12, self.width() * .42)
        left, right = 8 + label_w + 10, self.width() - 18
        finite = [abs(float(v)) for _, v in self.rows if math.isfinite(float(v))]
        bound = max(3., float(math.ceil(max(finite, default=0.) + .9)))
        scale = (right - left) / (2 * bound)
        zero = (left + right) / 2

        def x_at(v):
            return zero + max(-bound, min(bound, float(v))) * scale

        rows_top = line + 12
        rows_bottom = rows_top + len(self.rows) * self.Z_ROW
        band = QColor(c.accent)
        band.setAlpha(22)
        p.fillRect(QRectF(x_at(-1), rows_top, x_at(1) - x_at(-1), rows_bottom - rows_top), band)
        p.setPen(QColor(c.muted))
        band_text = self._z_text('band')
        band_w = metrics.horizontalAdvance(band_text) + 8
        p.drawText(QRectF(zero - band_w / 2, 4, band_w, line), Qt.AlignmentFlag.AlignCenter, band_text)
        unusual = self._z_text('unusual')
        unusual_w = metrics.horizontalAdvance(unusual) + 8
        dashed = QPen(QColor(c.muted), 1, Qt.PenStyle.DashLine)
        for v in (-2, 2):
            x = x_at(v)
            p.setPen(dashed)
            p.drawLine(QPointF(x, rows_top), QPointF(x, rows_bottom))
            if abs(x - zero) >= (band_w + unusual_w) / 2 + 4:
                p.setPen(QColor(c.muted))
                p.drawText(QRectF(x - unusual_w / 2, 4, unusual_w, line), Qt.AlignmentFlag.AlignCenter, unusual)
        groups = self.zscore['groups']
        p.setPen(QPen(QColor(c.border), 1))
        for k in range(1, len(self.rows)):
            if k < len(groups) and groups[k] != groups[k - 1]:
                y = rows_top + k * self.Z_ROW
                p.drawLine(QPointF(8, y), QPointF(self.width() - 8, y))
        colors = self._z_colors()
        for i, (_name, value) in enumerate(self.rows):
            y = rows_top + i * self.Z_ROW + self.Z_ROW / 2
            p.setPen(QColor(c.text))
            p.drawText(QRectF(8, y - line / 2, label_w, line),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       metrics.elidedText(names[i], Qt.TextElideMode.ElideRight, label_w))
            if not math.isfinite(float(value)):
                p.drawText(QRectF(zero + 6, y - line / 2, 40, line), Qt.AlignmentFlag.AlignVCenter, '—')
                continue
            color = QColor(colors.get(groups[i] if i < len(groups) else None, c.text))
            bar = QRectF(min(zero, x_at(value)), y - 8, abs(x_at(value) - zero), 16)
            p.fillRect(bar, color)
            if i in self.zscore['hatched']:
                p.fillRect(bar, QBrush(QColor(c.surface), Qt.BrushStyle.BDiagPattern))
            text = f'{float(value):+.2f}'.replace('-', '−')
            w = metrics.horizontalAdvance(text) + 6
            tx = x_at(value) + 4 if value >= 0 else x_at(value) - 4 - w
            tx = min(max(tx, left - 6), self.width() - w - 2)
            p.fillRect(QRectF(tx, y - line / 2 + 2, w, line - 4), QColor(c.surface))
            p.setPen(QColor(c.text))
            p.drawText(QRectF(tx, y - line / 2, w, line), Qt.AlignmentFlag.AlignCenter, text)
        p.setPen(QPen(QColor(c.text), 1))
        p.drawLine(QPointF(zero, rows_top - 2), QPointF(zero, rows_bottom + 2))
        step = 1 if scale >= metrics.horizontalAdvance('−3') + 14 else 2
        p.setPen(QColor(c.muted))
        for v in range(-int(bound), int(bound) + 1):
            if v % step:
                continue
            text = f'{v:+d}'.replace('-', '−') if v else '0'
            p.drawText(QRectF(x_at(v) - 20, rows_bottom + 4, 40, line), Qt.AlignmentFlag.AlignCenter, text)
        axis_top = rows_bottom + line + 8
        p.drawText(QRectF(8, axis_top, self.width() - 16, line), Qt.AlignmentFlag.AlignCenter,
                   metrics.elidedText(self._z_text('axis'), Qt.TextElideMode.ElideRight, self.width() - 16))
        legend_top = axis_top + line + 10
        entries, _ = self._z_legend(metrics, self.width())
        for swatch, rect, text, color, hatched in entries:
            box = swatch.translated(0, legend_top)
            p.fillRect(box, QColor(color))
            if hatched:
                p.fillRect(box, QBrush(QColor(c.surface), Qt.BrushStyle.BDiagPattern))
            p.setPen(QColor(c.text))
            p.drawText(rect.translated(0, legend_top), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       text)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self.colors;p.fillRect(self.rect(),QColor(c.surface))
        if getattr(self, 'zscore', None):
            self._paint_zscores(p);return
        left=min(230,self.width()*.4);right=self.width()-64
        zero=(left+right)/2;half=(right-left)/2
        p.setPen(QColor(c.muted));p.drawText(QPointF(zero-4,15),'0')
        for i,(name,value) in enumerate(self.rows):
            y=28+i*28
            p.setPen(QColor(c.text));p.drawText(QRectF(8,y-10,left-16,22),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,
                p.fontMetrics().elidedText(self.display_label(i),Qt.TextElideMode.ElideRight,int(left-16)))
            p.setPen(QPen(QColor(c.border),1));p.drawLine(QPointF(zero,y-10),QPointF(zero,y+10))
            if not math.isfinite(float(value)):
                p.drawText(QPointF(right+10,y+5),'—');continue
            dx=max(-1,min(1,float(value)/self.limit))*half
            p.fillRect(QRectF(min(zero,zero+dx),y-6,abs(dx),12),QColor(c.accent))
            p.setPen(QColor(c.text));p.drawText(QPointF(right+8,y+5),f'{value:+.2f}')
