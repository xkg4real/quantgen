"""Native Bonds calculator, full-revaluation scenarios and hedge sizing.

Owner-approved page draft (2026-11-17, docs/product/ui_drafts_2026-11-17/draft_02_tools.png): after a run the pane
shows the bond as one lead line, its key figures as a quiet line, the price–yield chart in a card with what a 1%p
move does read off the curve, the rate scenarios and the futures hedge in two cards, then every metric. On the
analysis tools page the form docks into the page's right column (`dock_into`: folds 채권 조건 and 위험·헤지, the curve
source note, the run button pinned at the bottom). Requests, calculations and exports are as before."""
import math

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetricsF, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QBoxLayout, QButtonGroup, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy,
                             QVBoxLayout, QWidget)
from core.research.bond_analysis import BondRequest
from .charts import LineChart, _axis_number, _number_face
from .bonds_portfolio_narrative import bond_notes, hedge_text, display_variants
from .model_narrative_language import localize_columns


def group_digits(text):
    """'1000000.5' -> '1,000,000.5'; text that is not a plain number is left as typed."""
    raw=str(text).strip().replace(',','')
    sign,body=('-',raw[1:]) if raw.startswith('-') else ('',raw)
    whole,dot,fraction=body.partition('.')
    if not (whole.isascii() and whole.isdecimal()) or (fraction and not (fraction.isascii() and fraction.isdecimal())):
        return str(text)
    return sign+f'{int(whole):,}'+dot+fraction


def _minus(text):
    """Figures read with a true minus sign, as in the drafts ('−7.64%')."""
    return str(text).replace('-', '−')


def _local(texts, kit, *, wrap=False):
    """Authored display text in both languages that follows the window language by itself (`LocalLabel`), styled by
    the page kit's `kit` property. Display only: no export reads it."""
    from .chart_study import LocalLabel
    label = LocalLabel(texts)
    label.setProperty('kit', kit)
    label.setWordWrap(wrap)
    if not wrap:
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
    return label


_FREQUENCY = {1: ('annual coupons', '연 1회 이표'), 2: ('semi-annual coupons', '반기 이표'),
              4: ('quarterly coupons', '분기 이표')}
_CURVES = {'SYNTHETIC': ('Synthetic curve', '합성 곡선'), 'FRED': ('FRED US Treasury curve', 'FRED 미국 국채 곡선')}
_TOOLS = {'calc': ('Calculator & risk', '계산 및 위험'), 'scenarios': ('Scenarios', '시나리오'),
          'hedge': ('Futures hedge', '선물 헤지')}


def one_point_moves(output):
    """What a 1%p rise and fall of the bond's own yield do to its price, read off the engine's price curve (the chart's
    line): ((rise %, price), (fall %, price)), or None where the curve does not reach ±1%p. No new calculation."""
    a = output.analytics
    center = a.ytm * 100
    moves = []
    for step in (1.0, -1.0):
        hits = [p for y, p in zip(output.yield_axis, output.price_curve) if abs(float(y) - (center + step)) < 1e-6]
        if not hits or not a.price:
            return None
        moves.append((hits[0] / a.price - 1.0, hits[0]))
    return tuple(moves)


class PriceYieldChart(LineChart):
    """The draft's price–yield chart: the engine's price curve and duration tangent with the convexity gap between
    them shaded, the bond's current point and the curve's prices 1%p either side. Drawing only: `series`, `x` and
    `set_series` are LineChart's, so exports and tests read the same data."""
    ASPECT = 0.48

    def __init__(self):
        super().__init__('Yield (%)', 'Price per 100')
        self.current = None     # (yield %, price) as priced
        self.marks = ()         # ((yield %, price, label, tone), ...) read off the price curve

    def set_current(self, current, marks=()):
        self.current, self.marks = current, tuple(marks)
        self.update()

    def set_series(self, x, series):
        if not list(x):
            self.current, self.marks = None, ()
        super().set_series(x, series)

    def _korean(self):
        return getattr(self.window(), 'ui_language', None) == 'ko'

    def paintEvent(self, event):
        if not self.x or len(self.series) < 2:
            return super().paintEvent(event)
        from .typography import tone_colors
        c, tones = self.colors, tone_colors(self.colors)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(c.surface))
        xs = [float(v) for v in self.x]
        curve = [float(v) for v in self.series[0][1]]
        tangent = [float(v) for v in self.series[1][1]]
        rows = [(x, y, t) for x, y, t in zip(xs, curve, tangent) if all(map(math.isfinite, (x, y, t)))]
        if len(rows) < 2:
            return
        xmin, xmax = rows[0][0], rows[-1][0]
        values = [y for _, y, _ in rows] + [t for _, _, t in rows]
        ymin, ymax = min(values), max(values)
        pad = (ymax - ymin) * .06 or 1.
        ymin, ymax = ymin - pad, ymax + pad
        y_ticks = self._y_ticks(ymin, ymax)
        x_ticks = [(v, text + '%') for v, text in self._ticks(xmin, xmax, 6, False)]
        metrics = QFontMetricsF(self.font())
        line = math.ceil(metrics.height()) + 2
        label_width = max((metrics.horizontalAdvance(t) for _, t in y_ticks), default=30)
        tag = metrics.horizontalAdvance(f'{ymax:,.2f}') + 14
        right = max(label_width, tag) + 14
        box = QRectF(8, 10, max(1., self.width() - 8 - right), max(1., self.height() - 10 - line - 14))

        def point(x, y):
            return QPointF(box.left() + (x - xmin) / max(xmax - xmin, 1e-9) * box.width(),
                           box.bottom() - (y - ymin) / (ymax - ymin) * box.height())
        grid = QColor(c.border)
        tag_y = point(*self.current).y() if self.current is not None else None
        for value, text in y_ticks:
            y = point(xmin, value).y()
            p.setPen(QPen(grid, 1))
            p.drawLine(QPointF(box.left(), y), QPointF(box.right(), y))
            if tag_y is not None and abs(y - tag_y) < line:
                continue        # the price tag sits on the axis here
            p.setPen(QColor(c.muted))
            _number_face(p)
            p.drawText(QRectF(box.right() + 10, y - line / 2, right - 10, line),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
            p.restore()
        p.setPen(QColor(c.muted))
        _number_face(p)
        for value, text in x_ticks:
            x = point(value, ymin).x()
            width = metrics.horizontalAdvance(text) + 8
            p.drawText(QRectF(x - width / 2, box.bottom() + 6, width, line), Qt.AlignmentFlag.AlignCenter, text)
        p.restore()
        # The convexity effect: the gap between the price curve and its duration tangent.
        band = QPainterPath(point(rows[0][0], rows[0][1]))
        for x, y, _ in rows[1:]:
            band.lineTo(point(x, y))
        for x, _, t in reversed(rows):
            band.lineTo(point(x, t))
        band.closeSubpath()
        fill = QColor(c.accent)
        fill.setAlphaF(.12)
        p.fillPath(band, fill)
        for values, pen in ((2, QPen(QColor(c.muted), 1.4, Qt.PenStyle.DashLine)), (1, QPen(QColor(c.accent), 2.2))):
            path = QPainterPath(point(rows[0][0], rows[0][values]))
            for row in rows[1:]:
                path.lineTo(point(row[0], row[values]))
            p.setPen(pen)
            p.drawPath(path)
        p.setFont(self.font())
        for x, y, text, tone in self.marks:
            spot = point(x, y)
            color = QColor(tones.get(tone, c.muted))
            p.setPen(QPen(color, 1.8))
            p.setBrush(QColor(c.surface))
            p.drawEllipse(spot, 4, 4)
            p.setBrush(Qt.BrushStyle.NoBrush)
            left = x < (self.current[0] if self.current else xmin)
            bp, move = text
            width = metrics.horizontalAdvance(bp + ' ' + move) + 4
            x = spot.x() - 9 - width if left else spot.x() + 9
            x = min(max(box.left() + 2, x), box.right() - width)      # never past the plot's edges
            origin = QPointF(x, spot.y() + (18 if left else -9))
            p.setPen(QColor(c.muted))
            p.drawText(origin, bp + ' ')
            p.setPen(color)
            p.drawText(QPointF(origin.x() + metrics.horizontalAdvance(bp + ' '), origin.y()), move)
        if self.current is not None:
            x0, y0 = self.current
            spot = point(x0, y0)
            p.setPen(QPen(QColor(c.muted), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(spot.x(), box.top()), QPointF(spot.x(), box.bottom()))
            guide = QColor(c.accent)
            guide.setAlphaF(.5)
            p.setPen(QPen(guide, 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(box.left(), spot.y()), QPointF(box.right(), spot.y()))
            p.setPen(QPen(QColor(c.surface), 2.5))
            p.setBrush(QColor(c.accent))
            p.drawEllipse(spot, 6.5, 6.5)
            p.setBrush(Qt.BrushStyle.NoBrush)
            price = f'{y0:,.2f}'
            rect = QRectF(box.right() + 4, spot.y() - line / 2 - 1, metrics.horizontalAdvance(price) + 12, line + 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(c.accent))
            p.drawRoundedRect(rect, 4, 4)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QColor(c.on_accent))
            _number_face(p)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, price)
            p.restore()
            words = ('현재 ' if self._korean() else 'Now ') + f'{x0:.3f}% · {y0:,.3f}'
            bold = p.font()
            bold.setWeight(600)
            p.setFont(bold)
            width = QFontMetricsF(bold).horizontalAdvance(words)
            p.setPen(QColor(c.text))
            p.drawText(QPointF(max(box.left() + 2, spot.x() - 14 - width), spot.y() + 24), words)


class CurveLegend(QWidget):
    """The chart card's legend (가격 곡선 · 듀레이션 접선 · 컨벡시티 효과 · 현재), painted with the chart's own marks."""
    ENTRIES = (('line', ('Price curve', '가격 곡선')), ('dash', ('Duration tangent', '듀레이션 접선')),
               ('band', ('Convexity effect', '컨벡시티 효과')), ('dot', ('Now', '현재')))

    GAP = 14

    def __init__(self):
        super().__init__()
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def _texts(self):
        korean = getattr(self.window(), 'ui_language', None) == 'ko'
        return [(kind, pair[1] if korean else pair[0]) for kind, pair in self.ENTRIES]

    def _line(self):
        return math.ceil(QFontMetricsF(self.font()).height()) + 6

    def _rows(self, width):
        """Entries placed left to right, onto a new line when the next one does not fit: [[(kind, text, x)], ...]."""
        metrics = QFontMetricsF(self.font())
        rows, x = [[]], 0.
        for kind, text in self._texts():
            span = metrics.horizontalAdvance(text) + 23
            if rows[-1] and x + span > width:
                rows.append([])
                x = 0.
            rows[-1].append((kind, text, x))
            x += span + self.GAP
        return rows

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return len(self._rows(max(1, width))) * self._line()

    def sizeHint(self):
        metrics = QFontMetricsF(self.font())
        width = sum(metrics.horizontalAdvance(text) + 23 for _, text in self._texts()) + self.GAP * 3
        return QSize(math.ceil(width), self._line())

    def minimumSizeHint(self):
        metrics = QFontMetricsF(self.font())
        return QSize(math.ceil(max(metrics.horizontalAdvance(text) + 23 for _, text in self._texts())), self._line())

    def changeEvent(self, event):
        super().changeEvent(event)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().width() != event.oldSize().width():
            self.updateGeometry()

    def paintEvent(self, event):
        colors = getattr(self.window(), 'colors', None)
        if colors is None:
            from core.theme import LIGHT as colors
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        metrics = QFontMetricsF(self.font())
        line = self._line()
        for number, row in enumerate(self._rows(max(1, self.width()))):
            top = number * line
            mid = top + line / 2
            for kind, text, x in row:
                if kind == 'line':
                    p.setPen(QPen(QColor(colors.accent), 2))
                    p.drawLine(QPointF(x, mid), QPointF(x + 16, mid))
                elif kind == 'dash':
                    p.setPen(QPen(QColor(colors.muted), 1.4, Qt.PenStyle.DashLine))
                    p.drawLine(QPointF(x, mid), QPointF(x + 16, mid))
                elif kind == 'band':
                    fill = QColor(colors.accent)
                    fill.setAlphaF(.18)
                    p.setPen(QPen(QColor(colors.border), 1))
                    p.setBrush(fill)
                    p.drawRoundedRect(QRectF(x + 3, mid - 5, 10, 10), 2, 2)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                else:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(colors.accent))
                    p.drawEllipse(QPointF(x + 8, mid), 4, 4)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QColor(colors.muted))
                p.drawText(QRectF(x + 21, top, metrics.horizontalAdvance(text) + 2, line),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)


class KeyRateBars(QWidget):
    """The hedge card's DV01 by key maturity (the draft's '만기별 DV01'): the largest few of the run's key-rate DV01s as
    bars against the largest, each with its value. The same numbers as the 'DV01 by maturity' table; drawing only."""
    ROWS = 4

    def __init__(self):
        super().__init__()
        self.rows = ()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMaximumWidth(560)       # bars read against each other, not across a wide card

    def set_rows(self, rows):
        """rows: ((tenor years, DV01), ...) as the engine gave them; the largest ROWS by size are drawn."""
        self.rows = tuple(sorted(((t, v) for t, v in rows if math.isfinite(v) and v), key=lambda r: -abs(r[1]))[:self.ROWS])
        self.setFixedHeight(len(self.rows) * self._line())
        self.update()

    def _line(self):
        return math.ceil(QFontMetricsF(self.font()).height()) + 8

    def sizeHint(self):
        return QSize(220, len(self.rows) * self._line())

    def paintEvent(self, event):
        if not self.rows:
            return
        colors = getattr(self.window(), 'colors', None)
        if colors is None:
            from core.theme import LIGHT as colors
        korean = getattr(self.window(), 'ui_language', None) == 'ko'
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        metrics = QFontMetricsF(self.font())
        line, top = self._line(), max(abs(v) for _, v in self.rows)
        names = [f'{t:g}' + ('년' if korean else 'y') for t, _ in self.rows]
        values = [f'{v:,.2f}' for _, v in self.rows]
        left = max(metrics.horizontalAdvance(n) for n in names) + 10
        right = max(metrics.horizontalAdvance(v) for v in values) + 10
        track = max(10., self.width() - left - right)
        for row, ((_, value), name, text) in enumerate(zip(self.rows, names, values)):
            y = row * line
            p.setPen(QColor(colors.muted))
            p.drawText(QRectF(0, y, left, line), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(colors.surface_2))
            p.drawRoundedRect(QRectF(left, y + line / 2 - 3, track, 6), 3, 3)
            p.setBrush(QColor(colors.accent))
            p.drawRoundedRect(QRectF(left, y + line / 2 - 3, max(6., track * abs(value) / top), 6), 3, 3)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QColor(colors.text))
            _number_face(p)
            p.drawText(QRectF(self.width() - right, y, right, line), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       text)
            p.restore()


class CardRow(QWidget):
    """Cards side by side (the draft's scenario and hedge cards), stacked below `breakpoint`; a hidden card takes no
    room and the other one spans the row."""

    def __init__(self, cards, stretches, *, breakpoint=640):
        super().__init__()
        self.breakpoint = breakpoint
        self.box = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(12)
        for card, stretch in zip(cards, stretches):
            self.box.addWidget(card, stretch)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        direction = (QBoxLayout.Direction.LeftToRight if self.width() >= self.breakpoint
                     else QBoxLayout.Direction.TopToBottom)
        if self.box.direction() != direction:
            self.box.setDirection(direction)


class BondsPane(QWidget):
    requested=pyqtSignal(object)
    result_changed=pyqtSignal(bool)   # a result is shown (True) or cleared (False); the page's status badge

    def __init__(self):
        super().__init__()
        from .app import label,panel,table
        from .form_layout import CompactFieldGrid,bound_input_panel,add_compact_action
        from .page_kit import Card, KeyFigures
        self.has_result=False
        layout=QVBoxLayout(self);layout.setContentsMargins(0,12,0,0);layout.setSpacing(18)
        box,inner=panel('Bonds · price, risk, scenarios and futures hedge')
        self.input_box=box
        bound_input_panel(box,columns=4)
        pairs=[];self.fields={}
        fields=[('Coupon %','4.50'),('Maturity · years','10'),('Notional','1000000'),
                ('Price · per 100',''),('Yield %','4.50'),('Position DV01 · optional',''),
                ('CTD DV01 / contract','65'),('Conversion factor','0.8')]
        for i,(name,value) in enumerate(fields):
            # Owner UI-4: amounts read with thousands separators (1,000,000); parsing strips them.
            w=QLineEdit(group_digits(value));w.setAccessibleName(name);self.fields[name]=w
            w.editingFinished.connect(lambda w=w:w.setText(group_digits(w.text())))
            pairs.append((label(name,'caption'),w))
        self.frequency=QComboBox()
        for text,value in [('Annual',1),('Semi-annual',2),('Quarterly',4)]:self.frequency.addItem(text,value)
        self.frequency.setCurrentIndex(1)
        self.source=QComboBox()
        for v in ('auto','fred','synthetic'):self.source.addItem(v,v)
        self.tool=QComboBox()
        for text,value in [('Calculator & risk','calc'),('Scenarios','scenarios'),('Futures hedge','hedge')]:self.tool.addItem(text,value)
        for i,(name,w) in enumerate((('Coupons / year',self.frequency),('Tool',self.tool))):
            w.setAccessibleName(name);pairs.append((label(name,'caption'),w))
        # Owner UI-8: the curve provider is automatic (FRED, labelled synthetic fallback); no selector.
        self.source.setAccessibleName('Curve source');self.source.hide()
        self.form=CompactFieldGrid(pairs,max_columns=4)
        inner.addWidget(self.form)
        self.hint=label('Enter either price or yield, not both. Clear yield when entering price.','caption')
        inner.addWidget(self.hint)
        self.run=QPushButton('채권 분석 실행');self.run.setProperty('primary',True);self.run.clicked.connect(self.submit);add_compact_action(inner,self.run)
        self.status=label('곡선 출처와 관측일을 함께 표시합니다.','muted');self.status.setProperty('reading_help_keep_visible',True);inner.addWidget(self.status);layout.addWidget(box)
        from .chart_study import LocalLabel
        # Before a run: one quiet line in an empty card (the drafts' empty state).
        self.empty_card=Card(margins=(24,24,24,24))
        self.empty=LocalLabel({'ko':'채권 조건을 입력하고 실행하면 가격·위험·시나리오가 여기에 나타나요.',
                               'en':'Enter bond terms and run the analysis to see value, risk and scenarios here.'},'muted')
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_card.setMinimumHeight(260)
        self.empty_card.body.addStretch(1);self.empty_card.body.addWidget(self.empty);self.empty_card.body.addStretch(1)
        layout.addWidget(self.empty_card)
        self.result_host=QWidget();layout.addWidget(self.result_host)
        layout=QVBoxLayout(self.result_host);layout.setContentsMargins(0,0,0,0);layout.setSpacing(12)
        self.result_host.hide()
        from .report_actions import ReportActions
        from .result_layout import PairedResultPanels, fit_result_table
        # Lead line and exports: '4.50% 10년 채권 · 반기 이표 · 명목금액 1,000,000 · 수익률 4.500% 기준 · 합성 곡선 …'.
        self.exports = ReportActions(self.status)
        for button,kit in ((self.exports.json_button,'ghost'),(self.exports.zip_button,'secondary')):
            button.setProperty('kit',kit);button.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed)
        from .tools import ReflowRow, card_fill
        head=QHBoxLayout();head.setContentsMargins(0,0,0,0);head.setSpacing(8)
        self.lead=_local({},'lead');self.lead_note=_local({},'leadNote',wrap=True)
        head.addWidget(self.lead,0,Qt.AlignmentFlag.AlignTop);head.addWidget(self.lead_note,1,Qt.AlignmentFlag.AlignTop)
        self.lead_row=ReflowRow(head,(self.exports,))   # the exports go under the lead line when the canvas is narrow
        layout.addWidget(self.lead_row)
        self.figures=KeyFigures()
        layout.addWidget(self.figures)
        # The price–yield chart card: its title and what a 1%p move does, the chart with its axis words and legend,
        # the curve notes (ChartStudy: beside the chart when wide, under it otherwise).
        self.chart_card=Card(margins=(18,14,18,12),spacing=8)
        chart_head=QWidget();row=QHBoxLayout(chart_head);row.setContentsMargins(0,0,0,0);row.setSpacing(12)
        self.chart_title=_local({'en':'Price–yield curve','ko':'가격·수익률 곡선'},'cardTitle')
        self.reading=_local({},'hint',wrap=True);self.reading.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.chart_title,0,Qt.AlignmentFlag.AlignVCenter);row.addWidget(self.reading,1)
        self.chart_card.body.addWidget(chart_head)
        self.chart=PriceYieldChart()
        self.chart_area=QWidget();area=QVBoxLayout(self.chart_area);area.setContentsMargins(0,0,0,0);area.setSpacing(4)
        area.addWidget(self.chart)
        self.axes=_local({'en':'Across: yield (%) · up: price per 100 face','ko':'가로 수익률(%) · 세로 액면 100당 가격'},'hint',wrap=True)
        self.legend=CurveLegend()
        foot=ReflowRow(self.axes,(self.legend,),breakpoint=600,spacing=12,stacked=Qt.AlignmentFlag.AlignLeft)
        area.addWidget(foot)
        self.notes=label('','muted')
        self.notes.setProperty('reading_help_keep_visible',True)
        from .chart_study import ChartStudy
        self.study=ChartStudy(self.chart_area,self.notes)
        self.chart_card.body.addWidget(self.study)
        card_fill(chart_head, self.chart_area, foot, foot.actions, self.study)
        layout.addWidget(self.chart_card)
        # Rate scenarios (full revaluation) and the futures hedge, side by side when there is room.
        self.scenario_card=Card(margins=(16,14,16,12),spacing=8)
        top=QHBoxLayout();top.setContentsMargins(0,0,0,0);top.setSpacing(8)
        top.addWidget(_local({'en':'Rate scenarios','ko':'금리 시나리오'},'cardTitle'),0,Qt.AlignmentFlag.AlignBottom)
        top.addWidget(_local({'en':'Parallel shifts · full revaluation','ko':'평행 이동 · 전체 재평가'},'cardNote'),0,Qt.AlignmentFlag.AlignBottom)
        top.addStretch(1)
        from .page_kit import Button
        self.more_scenarios=Button(('',''),'ghost',checkable=True)
        self.more_scenarios.toggled.connect(self._show_shapes)
        top.addWidget(self.more_scenarios,0,Qt.AlignmentFlag.AlignVCenter)
        self.scenario_card.body.addLayout(top)
        self.scenarios=fit_result_table(table(['Scenario','Shock · bp','New price','P&L','P&L %']))
        self.scenarios.setColumnHidden(1,True)   # the scenario's name says its shock; the export keeps the column
        self.scenario_card.body.addWidget(self.scenarios);self.scenario_card.body.addStretch(1)
        self.hedge_card=Card(margins=(16,14,16,12),spacing=8)
        top=QHBoxLayout();top.setContentsMargins(0,0,0,0);top.setSpacing(8)
        top.addWidget(_local({'en':'Futures hedge','ko':'선물 헤지'},'cardTitle'),0,Qt.AlignmentFlag.AlignBottom)
        top.addStretch(1)
        top.addWidget(_local({'en':'No real orders','ko':'실제 주문 없음'},'cardNote'),0,Qt.AlignmentFlag.AlignBottom)
        self.hedge_card.body.addLayout(top)
        big=QHBoxLayout();big.setContentsMargins(0,0,0,0);big.setSpacing(8)
        self.hedge_count=_local({},'big');self.hedge_side=_local({},'leadNote');self.hedge_raw=_local({},'cardNote')
        big.addWidget(self.hedge_count,0,Qt.AlignmentFlag.AlignBaseline);big.addWidget(self.hedge_side,0,Qt.AlignmentFlag.AlignBaseline)
        big.addStretch(1);big.addWidget(self.hedge_raw,0,Qt.AlignmentFlag.AlignBaseline)
        self.hedge_card.body.addLayout(big)
        self.hedge=label('','caption');self.hedge.setProperty('reading_help_keep_visible',True)
        self.hedge_card.body.addWidget(self.hedge)
        from .page_kit import rule
        self.hedge_card.body.addWidget(rule())
        self.krd_title=_local({},'hint',wrap=True);self.krd_bars=KeyRateBars()
        self.hedge_card.body.addWidget(self.krd_title);self.hedge_card.body.addWidget(self.krd_bars)
        self.hedge_card.body.addStretch(1)
        self.lower=CardRow((self.scenario_card,self.hedge_card),(135,100))
        layout.addWidget(self.lower)
        # Every metric the run computed, and DV01 by key maturity.
        self.metrics=fit_result_table(table(['Metric','Value']));self.metrics.setProperty('localized_columns', [0])
        metrics_box=Card(margins=(16,14,16,12),spacing=8);metrics_box.body.addWidget(label('Key metrics','heading'))
        metrics_box.body.addWidget(self.metrics);metrics_box.body.addStretch()
        self.krd=fit_result_table(table(['Key tenor · years','DV01 · currency / bp']))
        krd_box=Card(margins=(16,14,16,12),spacing=8);krd_box.body.addWidget(label('DV01 by maturity','heading'))
        krd_box.body.addWidget(self.krd);krd_box.body.addStretch()
        # Side by side from 600 px: the canvas beside the page's right column is narrower than the old full page.
        self.result_panels=PairedResultPanels(metrics_box,krd_box,breakpoint=600)
        layout.addWidget(self.result_panels)
        self._output=None
        self._render_scenario_toggle()

    # Docking (analysis tools page) ---------------------------------------------------------------------------------
    def dock_into(self, side, *, title=None):
        """The approved draft's right column: the form as two folds (채권 조건: coupon, maturity, notional, coupons per
        year, yield, price and the price-or-yield hint; 위험·헤지: the tool as chips, position DV01, CTD DV01, conversion
        factor), the curve source note, the run button and status pinned at the bottom. The same line edits and
        combos move (their captions, accessible names, values and the request are unchanged)."""
        from .form_layout import CompactFieldGrid
        from .page_kit import Button, Fold, Soft
        from .tools import dock_form
        box, inner, old = self.input_box, self.input_box.layout(), self.form
        old.timer.stop()
        old.removeEventFilter(old)
        captions = {}
        for caption, control in old.fields:
            caption.removeEventFilter(old); control.removeEventFilter(old)
            captions[control] = caption
        while old.grid.count():
            old.grid.takeAt(0)
        old.fields = ()      # a late refresh of the old grid must not take its fields back
        pair = lambda control: (captions[control], control)
        f = self.fields
        terms = CompactFieldGrid([pair(f['Coupon %']), pair(f['Maturity · years']), pair(f['Notional']),
                                  pair(self.frequency), pair(f['Yield %']), pair(f['Price · per 100'])], max_columns=2)
        position = CompactFieldGrid([pair(f['Position DV01 · optional'])], max_columns=1)
        futures = CompactFieldGrid([pair(f['CTD DV01 / contract']), pair(f['Conversion factor'])], max_columns=2)
        self.form = terms
        heading = inner.itemAt(0).widget()
        if heading is not None and heading.property('role') == 'heading':
            heading.hide()      # the folds name the sections
        self.terms_fold = Fold(('Bond terms', '채권 조건'))
        self.terms_fold.body.addWidget(terms)
        inner.removeWidget(self.hint)
        self.terms_fold.body.addWidget(self.hint)
        self.risk_fold = Fold(('Risk & hedge', '위험·헤지'))
        tool_caption = captions[self.tool]
        self.tool.hide()
        chips = QHBoxLayout(); chips.setContentsMargins(0, 0, 0, 0); chips.setSpacing(6)
        self.tool_chips = []
        group = QButtonGroup(box); group.setExclusive(True)
        for index in range(self.tool.count()):
            chip = Button(_TOOLS.get(self.tool.itemData(index), (self.tool.itemText(index),) * 2), 'chip', checkable=True)
            chip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            chip.clicked.connect(lambda checked=False, i=index: self.tool.setCurrentIndex(i))
            group.addButton(chip); chips.addWidget(chip, 1)
            self.tool_chips.append(chip)
        self.tool_chip_group = group
        self.tool.currentIndexChanged.connect(self._sync_chips)
        self._sync_chips()
        tool_host = QWidget(); column = QVBoxLayout(tool_host); column.setContentsMargins(0, 0, 0, 0); column.setSpacing(5)
        tool_caption.setContentsMargins(0, 5, 0, 0)
        column.addWidget(tool_caption); column.addLayout(chips)
        column.addWidget(self.tool)     # hidden: it still carries the request's tool and keeps a parent
        self.risk_fold.body.addWidget(tool_host)
        self.risk_fold.body.addWidget(position)
        self.risk_fold.body.addWidget(futures)
        inner.removeWidget(old); old.hide(); old.setParent(None); old.deleteLater()   # empty now
        self.curve_note = Soft(('Where the curve comes from', '곡선 출처'),
                               ('FRED US Treasury yields, fetched automatically. When FRED cannot be reached the app '
                                'uses a synthetic curve and says so with the result.',
                                'FRED 미국 국채 수익률을 자동으로 받아요. 연결이 안 되면 합성 곡선으로 바꾸고 결과에 그렇다고 표시해요.'))
        index = inner.indexOf(self.run)
        for offset, widget in enumerate((self.terms_fold, self.risk_fold)):
            inner.insertWidget(index + offset, widget)
        inner.removeWidget(self.status)
        page = dock_form(box, self.run, side, title=title)
        page.addWidget(self.curve_note)     # beside the form, not in it: the docked form draws no box backgrounds
        # Preferred, not Maximum: a Maximum height is capped at a size hint taken before the folds' captions took their
        # docked style, which cut the last field row (as in owner UI-6a).
        box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        for grid in (terms, position, futures):          # the draft's field rhythm: caption, input, then air
            grid.grid.setVerticalSpacing(5)
            for caption, _control in grid.fields:
                caption.setContentsMargins(0, 5, 0, 0)
            grid.refresh()
        self.status.setProperty('role', 'caption')        # a quiet line under the run button, as in Build & Test
        side.foot.addWidget(self.status)
        # Reading order: the fields as shown, the tool chips, then the run button at the bottom of the column.
        order = [f['Coupon %'], f['Maturity · years'], f['Notional'], self.frequency, f['Yield %'],
                 f['Price · per 100'], *self.tool_chips, f['Position DV01 · optional'], f['CTD DV01 / contract'],
                 f['Conversion factor'], self.run]
        for first, second in zip(order, order[1:]):
            QWidget.setTabOrder(first, second)
        self.docked_side = side
        layout = self.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        return side

    def _sync_chips(self, *args):
        for index, chip in enumerate(getattr(self, 'tool_chips', ())):
            chip.setChecked(index == self.tool.currentIndex())

    def _render_scenario_toggle(self):
        shapes = sum(1 for row in range(self.scenarios.rowCount()) if self._is_shape(row))
        self.more_scenarios.setVisible(bool(shapes))
        self.more_scenarios.set_pair((('Hide curve shapes', '곡선 형태 접기') if self.more_scenarios.isChecked() else
                                      (f'{shapes} curve shapes', f'곡선 형태 {shapes}개 더 보기')))

    def _is_shape(self, row):
        output = self._output
        return bool(output is not None and row < len(output.scenarios)
                    and not isinstance(output.scenarios[row].shock_bp, (int, float)))

    def _show_shapes(self, shown):
        for row in range(self.scenarios.rowCount()):
            self.scenarios.setRowHidden(row, self._is_shape(row) and not shown)
        self._render_scenario_toggle()

    # Language (kit pieces with values in the window language) ------------------------------------------------------
    def _language(self):
        return 'ko' if getattr(self.window(), 'ui_language', None) == 'ko' else 'en'

    def set_language(self, language):
        language = 'ko' if str(language or '').startswith('ko') else 'en'
        for widget in (self.figures, self.more_scenarios, *getattr(self, 'tool_chips', ())):
            widget.set_language(language)
        for widget in (getattr(self, 'terms_fold', None), getattr(self, 'risk_fold', None),
                       getattr(self, 'curve_note', None)):
            if widget is not None:
                widget.set_language(language)
        if self._output is not None:
            self._render_figures(self._output, language)
        self.legend.update(); self.legend.updateGeometry(); self.chart.update()

    def _render_figures(self, o, language):
        a = o.analytics
        korean = language == 'ko'
        self.figures.set_language(language)
        self.figures.set_items((
            (('Price', '가격'), f'{a.price:,.3f}', ''),
            (('Yield', '수익률'), f'{a.ytm:.3%}', ''),
            (('Macaulay duration', '맥컬리 듀레이션'), f'{a.macaulay:.2f}' + ('년' if korean else 'y'), ''),
            (('Modified duration', '수정 듀레이션'), f'{a.modified:.3f}', ''),
            (('Convexity', '컨벡시티'), f'{a.convexity:.2f}', ''),
            (('DV01', 'DV01'), f'{a.dv01:,.2f} /bp', ''),
            (('z-spread', 'z-스프레드'), _minus(f'{a.z_spread * 10000:+.1f}bp'), '')))

    def _render_lead(self, o):
        a, q = o.analytics, o.request
        bond = a.bond
        coupon, years = f'{bond.coupon * 100:.2f}%', f'{bond.maturity:g}'
        self.lead.texts = {'en': f'{coupon} {years}-year bond', 'ko': f'{coupon} {years}년 채권'}
        freq = _FREQUENCY.get(bond.freq, (f'{bond.freq} coupons a year', f'연 {bond.freq}회 이표'))
        basis = ((f'priced at {q.price:,.3f}', f'가격 {q.price:,.3f} 기준') if q.price is not None else
                 (f'at a {a.ytm:.3%} yield', f'수익률 {a.ytm:.3%} 기준'))
        curve = _CURVES.get(o.panel.source, (str(o.panel.source),) * 2)
        notional = f'{bond.notional:,.0f}'
        self.lead_note.texts = {
            'en': f'· {freq[0]} · notional {notional} · {basis[0]} · {curve[0]} {o.curve.date}',
            'ko': f'· {freq[1]} · 명목금액 {notional} · {basis[1]} · {curve[1]} {o.curve.date}'}
        moves = one_point_moves(o)
        if moves is None:
            self.reading.texts = {}
            self.chart.set_current((a.ytm * 100, a.price))
        else:
            (rise, rise_price), (fall, fall_price) = moves
            up, down = _minus(f'{rise:+.2%}'), _minus(f'{fall:+.2%}')
            gain = fall > -rise
            self.reading.texts = {
                'en': f'Rates +1%p {up} · −1%p {down}' + (' · a fall gains more than an equal rise loses' if gain else ''),
                'ko': f'금리 1%p 상승 {up} · 1%p 하락 {down}' + (' · 같은 폭이면 이익이 손실보다 커요' if gain else '')}
            center = a.ytm * 100
            self.chart.set_current((center, a.price), (
                (center - 1, fall_price, ('−100bp', _minus(f'{fall:+.2%}')), 'up' if fall >= 0 else 'down'),
                (center + 1, rise_price, ('+100bp', _minus(f'{rise:+.2%}')), 'down' if rise < 0 else 'up')))
        if o.hedge:
            pos, ctd, cf, n = o.hedge
            count = round(n)
            self.hedge_count.texts = {'en': f'{abs(count):,} contracts', 'ko': f'{abs(count):,}계약'}
            self.hedge_side.texts = ({'en': 'sell', 'ko': '매도'} if n >= 0 else {'en': 'buy', 'ko': '매수'})
            self.hedge_raw.texts = {'en': f'computed {n:,.2f}', 'ko': f'계산값 {n:,.2f}'}
            total = sum(abs(v) for v in a.krd.values() if math.isfinite(v))
            self.krd_bars.set_rows(a.krd.items())
            if self.krd_bars.rows and total:
                tenor, value = self.krd_bars.rows[0]
                share = f'{abs(value) / total:.0%}'
                self.krd_title.texts = {'en': f'DV01 by maturity · {share} in the {tenor:g}y bucket',
                                        'ko': f'만기별 DV01 · {tenor:g}년 구간에 {share}'}
            else:
                self.krd_title.texts = {}
        if hasattr(self, 'curve_note'):
            self.curve_note.text.set_pair((
                f'{curve[0]} · observed {o.curve.date} · {len(o.panel)} sessions. When FRED cannot be reached the app '
                'uses a synthetic curve and says so.',
                f'{curve[1]} · {o.curve.date} 관측 · {len(o.panel)}거래일. 연결이 안 되면 합성 곡선으로 바꾸고 그렇다고 표시해요.'))
        for widget in (self.lead, self.lead_note, self.reading, self.hedge_count, self.hedge_side, self.hedge_raw,
                       self.krd_title):
            widget.sync()
            widget.setVisible(bool(widget.texts))

    def submit(self):
        def number(name,default=None):
            s=self.fields[name].text().strip().replace(',','')
            return float(s) if s else default
        try:
            y=number('Yield %')
            q=BondRequest(coupon=number('Coupon %',0)/100,maturity=number('Maturity · years',10),
                frequency=self.frequency.currentData(),notional=number('Notional',1e6),price=number('Price · per 100'),
                yield_rate=y/100 if y is not None else None,source=self.source.currentData(),tool=self.tool.currentData(),
                position_dv01=number('Position DV01 · optional'),ctd_dv01=number('CTD DV01 / contract',65),conversion_factor=number('Conversion factor',1))
            q.validate()
        except (ValueError,TypeError):
            self.clear_result()
            self.status.setText('Input error · Enter finite values and valid maturity/amount; keep either price or yield.');return
        self.requested.emit(q)

    def show_result(self,o):
        from .app import table_rows
        self.empty.hide();self.empty_card.hide();self.result_host.show()
        a=o.analytics;cr=a.carry_roll
        # Values are language-neutral (the unit 'y' as in tenors, DV01's unit in its caption), so a
        # Korean window shows no English unit words (owner issues 03/14); captions translate.
        table_rows(self.metrics,[('Price',f'{a.price:.3f}'),('Yield',f'{a.ytm:.3%}'),
            ('Macaulay duration',f'{a.macaulay:.3f}y'),('Modified duration',f'{a.modified:.3f}'),
            ('Convexity',f'{a.convexity:.3f}'),('DV01 · currency per bp',f'{a.dv01:,.2f}'),
            ('z-spread',f'{a.z_spread*10000:.2f} bp'),('Curve price',f'{a.curve_price:.3f}'),
            (f'Carry · {cr.horizon:g} years',f'{cr.carry:+.3f}'),('Roll-down',f'{cr.rolldown:+.3f}'),
            ('Carry + roll',f'{cr.total:+.3f}'),('Breakeven',f'{cr.breakeven_bp:+.2f} bp')])
        self.chart.set_series(o.yield_axis,[('Price',o.price_curve),('Duration tangent',o.duration_tangent)])
        table_rows(self.krd,[[f'{k:g}',f'{v:,.2f}'] for k,v in sorted(a.krd.items())])
        table_rows(self.scenarios,[[r.name,str(r.shock_bp),f'{r.new_price:.3f}',f'{r.pnl:+,.2f}',f'{r.pnl_pct:+.2%}'] for r in o.scenarios])
        localize_columns(self.scenarios,(0,))  # scenario names ('+25bp parallel', 'bear steepener')
        self.scenarios.setVisible(bool(o.scenarios))
        self.scenario_card.setVisible(bool(o.scenarios))
        self._output=o
        self.more_scenarios.setChecked(False)
        self._show_shapes(False)
        self.hedge.setText('')
        if o.hedge:
            pos,ctd,cf,n=o.hedge
            self.hedge.setText(f'선물 매도 {n:,.2f} contracts · 반올림 {round(n):,}\n'
                f'Position DV01 {pos:,.2f} × CF {cf:.4f} / CTD DV01 {ctd:,.2f}\n'
                f'반올림 후 잔여 DV01 {pos-round(n)*ctd/cf:+,.2f} per bp · 실제 주문 없음')
        self.hedge_card.setVisible(bool(o.hedge))
        self.lower.setVisible(bool(o.scenarios) or bool(o.hedge))
        self.notes.setText('\n'.join(n for n in [
            ('합성 곡선 · 현재 시장 데이터 아님' if o.panel.source=='SYNTHETIC' else o.panel.source),
            f'{o.curve.source} · {o.curve.date} · {o.curve.method} · {len(o.panel)} sessions',
            o.panel.note,o.curve.note,a.note,o.narrative] if n))
        display_variants(self.notes, bond_notes(o,'en'), bond_notes(o,'ko'))
        display_variants(self.hedge, hedge_text(o.hedge,'en'), hedge_text(o.hedge,'ko'))
        self._render_lead(o)
        self._render_figures(o, self._language())
        self.status.setText('계산 완료 · 곡선 및 채권 가정을 확인하세요.')
        self.exports.set_result('bonds', o.request, [
            {'type': 'provenance', 'source': o.panel.source, 'date': o.curve.date,
             'curve_source': o.curve.source, 'method': o.curve.method, 'note': o.panel.note},
            {'type': 'analytics', 'data': a}, {'type': 'scenarios', 'data': o.scenarios},
            {'type': 'hedge', 'data': o.hedge},
            {'type': 'price_yield', 'yield_pct': o.yield_axis, 'price': o.price_curve, 'tangent': o.duration_tangent},
            {'type': 'text', 'text': self.notes.source_text}])
        self.has_result=True
        self.result_changed.emit(True)

    def clear_result(self):
        self.exports.clear()
        self.result_host.hide();self.empty_card.show();self.empty.show()
        for widget in (self.metrics, self.krd, self.scenarios):
            widget.setRowCount(0)
        self.chart.set_series([], [])
        self.hedge.setText('')
        self.notes.setText('')
        self._output=None
        self.figures.set_items(())
        self.has_result=False
        self.result_changed.emit(False)
