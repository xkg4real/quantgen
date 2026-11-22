"""Native reference indicator guide and reusable market-history explorer.

The 기술지표 가이드 page follows the owner-approved draft (owner 2026-11-17, "시안 7개 전부 승인, 앱에 적용 진행하세요";
docs/product/ui_drafts_2026-11-17/draft_03_guide.png): `IndicatorGuide.dock_into(workspace)` moves the same widgets
into the page kit's frame (`page_kit.Workspace`). The toolbar holds the title, 기술지표 27 | 투자 용어, the education
badge, 모두 해제 and 보고서 저장. The canvas holds the example's name line and its price figures at the reading date,
the chart card (indicator tags with their values, the chart with the reading date marked, the date slider, the
signals that missed) and the example's provenance in small print. The right column holds 지표 (the 27 studies by
category) and 해석 (one card per selected study: state, the reading at that date, a gauge, the 결론 block of
core.education.outlook, one concept line and one limit line), with the combined reading and the education note pinned
at its foot. 투자 용어 shows the glossary: the terms by category on the right, the chosen term on the canvas.

The Signals pane embeds the same class undocked as a history explorer (the stacked layout built in __init__).
The docked guide keeps the original case chart first and adds small explanations
on its own lines. A separate, explicitly invented diagram is an optional
supplement below it; history calculations and export inputs keep their paths.
"""
from html import escape
import math
import re

from PyQt6.QtCore import QByteArray, QPointF, QRectF, QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetricsF
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QBoxLayout,QComboBox,QPushButton,QSlider,
                            QFileDialog,QSizePolicy,QLayout,QFrame)

from core.i18n import LocaleContext
from core.education import glossary
from core.education.indicators import from_history, study, CATEGORIES, CATEGORY_NAMES
from core.education import study_guide
from core.education.catalog import (INDICATORS, BY_KEY, historical_case, counterexamples, selection,
    chart_svg, cursor_text, reading_text, learning_bundle, plot_bounds, from_snapshot, missing_reason,
    values_for, bars_for)

CIRCLED = '①②③④⑤⑥⑦⑧⑨'
BADGE = ('Education · not advice', '교육용 과거 사례 · 투자 권유 아님')


def _ko(ctx):
    return getattr(ctx, 'language', 'ko') == 'ko'


def _faint(colors):
    from .typography import mix
    return mix(colors.muted, colors.bg, 0.35)


def guide_sheet(p, dark):
    """The guide page's own rules (draft_03_guide), set on the page's canvas and right column; the page kit's rules
    (`page_kit.kit_sheet`) stay on the Workspace above them."""
    from .stock_detail_style import line_color
    faint = _faint(p)
    line = line_color(p)
    return f"""
      QWidget[guide='box'], QLabel[guide], QSlider, QSvgWidget {{ background: transparent; }}
      QFrame[guide='tag'] {{ background: {p.surface_2}; border: 0; border-radius: 8px; }}
      QPushButton[guide='tagName'] {{ border: 0; background: transparent; padding: 3px 2px 3px 2px;
                                      font-size: 12px; font-weight: 600; color: {p.text}; }}
      QPushButton[guide='tagName'][current='true'] {{ color: {p.accent}; }}
      QPushButton[guide='tagName']:hover {{ color: {p.accent}; }}
      QPushButton[guide='tagX'] {{ border: 0; background: transparent; padding: 3px 8px 3px 3px; font-size: 12px;
                                   color: {faint}; }}
      QPushButton[guide='tagX']:hover {{ color: {p.text}; }}
      QPushButton[guide='tagName']:focus, QPushButton[guide='tagX']:focus {{ border: 1px solid {p.accent};
                                   border-radius: 4px; }}
      QLabel[guide='tagValues'] {{ font-size: 12px; color: {p.text}; letter-spacing: 0px; }}
      QLabel[guide='caseTitle'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[guide='date'] {{ font-size: 13px; font-weight: 600; color: {p.text}; letter-spacing: 0px; }}
      QLabel[guide='hint'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[guide='keys'] {{ font-size: 11px; color: {faint}; }}
      QLabel[guide='fine'] {{ font-size: 11px; color: {p.muted}; }}
      QLabel[guide='failTitle'] {{ font-size: 12px; font-weight: 600; color: {p.text}; }}
      QLabel[guide='failNote'] {{ font-size: 11px; color: {faint}; }}
      QLabel[guide='key'] {{ font-size: 12px; color: {faint}; }}
      QLabel[guide='note'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[guide='groupTitle'] {{ font-size: 12px; font-weight: 600; color: {p.muted}; }}
      QLabel[guide='groupCount'] {{ font-size: 11px; color: {faint}; }}
      QLabel[guide='intro'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[guide='together'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[guide='togetherKey'] {{ font-size: 13px; font-weight: 600; color: {p.text}; }}
      QLabel[guide='termTitle'] {{ font-size: 20px; font-weight: 600; letter-spacing: -0.5px; color: {p.text}; }}
      QLabel[guide='termCategory'] {{ font-size: 12px; font-weight: 600; color: {p.accent}; }}
      QLabel[guide='termSummary'] {{ font-size: 15px; font-weight: 500; color: {p.text}; letter-spacing: -0.2px; }}
      QLabel[guide='sectionTitle'] {{ font-size: 12px; font-weight: 600; color: {p.muted}; }}
      QLabel[guide='sectionText'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[guide='pageTitle'] {{ font-size: 14px; font-weight: 600; color: {p.muted}; }}
      QLabel[guide='pageText'] {{ font-size: 14px; color: {p.text}; }}
      QFrame[guide='rule'] {{ background: {line}; border: 0; min-height: 1px; max-height: 1px; }}
      QSlider::groove:horizontal {{ height: 4px; border-radius: 2px; background: {p.surface_2}; }}
      QSlider::sub-page:horizontal {{ height: 4px; border-radius: 2px; background: {p.accent_soft}; }}
      QSlider::handle:horizontal {{ width: 12px; height: 12px; margin: -6px 0; border-radius: 8px;
                                   background: {p.surface}; border: 3px solid {p.accent}; }}
      QSlider:focus {{ outline: 0; }}
    """


class TechnicalChart(QSvgWidget):
    cursor_changed=pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.series=None;self.keys=();self.ctx=LocaleContext();self.cursor=0
        # The docked guide shows the indicator tags above the chart, so the SVG leaves its own legend out; markers
        # are the numbered counterexamples [(index, '1'), ...] painted over the chart.
        self.legend=True;self.markers=()
        # candles=True (the docked guide): an observed market example is drawn like the stock detail chart
        # (core.market.detail_svg: candles, bands, sub-panels, the reading date on the time axis) in a window of
        # WINDOW bars that follows the reading date; reference closes keep the catalogue's line chart.
        self.candles=False;self.view_end=None;self.layout_info=None;self.crop=0
        # Only the dedicated education page enables these painted labels.
        # The reusable Signals/history explorer keeps its original presentation.
        self.annotations_enabled=False;self.annotation_focus=None
        self.annotations=();self.annotation_boxes=()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumWidth(350)

    WINDOW=140

    def set_chart(self, series, keys, ctx, cursor):
        changed=self.series is not series or self.keys!=tuple(keys) or self.ctx!=ctx
        if self.series is not series:self.view_end=None
        moved=int(cursor)!=self.cursor
        self.series,self.keys,self.ctx,self.cursor=series,tuple(keys),ctx,int(cursor)
        if changed or (moved and self._snapshot() is not None):self.redraw()
        else:self.update()
        description=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        self.setAccessibleDescription(description);self.setToolTip(description)

    def _snapshot(self):
        snapshot=getattr(self.series,'snapshot',None) if self.candles else None
        return snapshot if snapshot is not None and len(getattr(snapshot,'candles',()) or ())>1 else None

    def _window(self, count):
        """(visible, end) of the drawn bars: the window moves only when the reading date leaves it."""
        visible=min(count,self.WINDOW)
        if self.view_end is None:   # a new example opens with its reading date in the middle
            self.view_end=min(count-1,self.cursor+visible//2)
        end=max(visible-1,min(count-1,self.view_end))
        if self.cursor>end:end=min(count-1,self.cursor+visible//5)
        elif self.cursor<end-visible+1:end=max(visible-1,self.cursor+visible-1-visible//5)
        self.view_end=end
        return visible,end

    def _redraw_candles(self, snapshot, colors):
        from core.market.detail_svg import HEADER, panel_keys, render
        from .stock_detail_style import text as sd_text
        from .typography import is_dark
        lang='ko' if self.ctx.language=='ko' else 'en'
        visible,end=self._window(len(snapshot.candles))
        width=max(240,self.width());height=470+120*len(panel_keys(self.keys))
        try:values=values_for(self.series,self.keys)
        except Exception:values=None
        svg,layout=render(snapshot,studies=self.keys,cursor=self.cursor,end=end,visible=visible,width=width,height=height,
                          dark=is_dark(colors),theme={'bg':colors.surface,'text':colors.text,'muted':colors.muted,
                                                      'border':colors.border},
                          months=sd_text(lang,'months'),supply=getattr(self.series,'supply',None),values=values)
        # The renderer leaves its top band for a view's own strip; the guide's tags sit above the card instead.
        crop=HEADER-12
        svg=svg.replace(f'height="{height}" viewBox="0 0 {width} {height}"',
                        f'height="{height-crop}" viewBox="0 {crop} {width} {height-crop}"',1)
        self.layout_info,self.crop=layout,crop
        self.load(QByteArray(svg.encode()))
        self.setFixedHeight(height-crop)

    def redraw(self):
        if self.series is None:return
        from core.theme import LIGHT
        colors=getattr(self.window(),'colors',LIGHT)
        snapshot=self._snapshot()
        if snapshot is not None:
            self._redraw_candles(snapshot,colors)
            self._describe()
            return
        self.layout_info=None;self.crop=0
        svg=chart_svg(self.series,self.keys,locale=self.ctx,colors=colors,width=self.width(),legend=self.legend)
        self.load(QByteArray(svg.encode()))
        self.setFixedHeight(int(self.renderer().viewBoxF().height()))
        self._describe()

    def _describe(self):
        description=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        self.setAccessibleName(self.ctx.t('guide')+' · '+self.series.symbol)
        self.setAccessibleDescription(description)
        self.setToolTip(description)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.redraw()

    def _bounds(self):
        """(left, right, x of index) of the plot: the market renderer centres each candle in its slot."""
        count=len(self.series.closes)
        if getattr(self.series,'snapshot',None) is not None:
            from core.market.presentation import plot_bounds as market_bounds
            left,right=market_bounds(self.width());step=(right-left)/max(1,count)
            return left,right,lambda i:left+(i+.5)*step
        left,right=plot_bounds(self.series,self.ctx,self.width())
        return left,right,lambda i:left+(right-left)*i/max(1,count-1)

    def mouseMoveEvent(self,event):
        if self.series and self.layout_info is not None:
            self.cursor_changed.emit(self.layout_info.index_at(event.position().x()))
        elif self.series:
            count=len(self.series.closes)
            left,right,_x=self._bounds()
            if getattr(self.series,'snapshot',None) is not None:
                index=int((event.position().x()-left)//max(1e-9,(right-left)/max(1,count)))
            else:
                index=round((event.position().x()-left)/max(1,right-left)*(count-1))
            self.cursor_changed.emit(max(0,min(count-1,index)))
        super().mouseMoveEvent(event)

    def legend_top(self):
        import math
        columns=max(1,(self.width()-24)//210)
        return 12+(math.ceil((len(self.keys)+1)/columns)*24 if self.legend else 0)

    def _paint_candles(self, painter, colors):
        """Over the detail chart: each sub-panel's name in its head row and the numbered signals that missed under
        their candles (the renderer draws the reading date itself)."""
        layout=self.layout_info;crop=self.crop
        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        font=QFont(self.font());font.setPixelSize(12);painter.setFont(font)
        painter.setPen(QColor(colors.muted))
        for key,top,_bottom in layout.panels:
            painter.drawText(QPointF(layout.plot_left+4,top-crop+17),study(key).short)
        candles=self.series.snapshot.candles
        font.setPixelSize(10);font.setWeight(QFont.Weight.DemiBold);painter.setFont(font)
        for index,number in self.markers:
            if not layout.start<=index<layout.stop:continue
            cx=layout.x_of(index);cy=layout.y_of_price(candles[index].low)-crop+13
            cy=min(cy,layout.price[1]-crop-9)
            painter.setPen(QPen(QColor(colors.text),1.3));painter.setBrush(QColor(colors.surface))
            painter.drawEllipse(QPointF(cx,cy),8,8)
            painter.drawText(QRectF(cx-8,cy-8,16,16),Qt.AlignmentFlag.AlignCenter,number)

    def paintEvent(self,event):
        super().paintEvent(event)
        if self.series is None:return
        from core.theme import LIGHT
        colors=getattr(self.window(),'colors',LIGHT)
        if self.layout_info is not None:
            painter=QPainter(self);self._paint_candles(painter,colors)
            self._paint_annotations(painter,colors);painter.end()
            return
        _left,_right,x_of=self._bounds()
        x=x_of(self.cursor)
        top=self.legend_top()+18
        painter=QPainter(self);painter.setPen(QPen(QColor(colors.muted),1,Qt.PenStyle.DashLine))
        painter.drawLine(round(x),top,round(x),self.height()-36)
        if self.markers:
            # The signals that missed (the canvas's numbered chips) sit on the date axis line.
            painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
            font=QFont(self.font());font.setPixelSize(10);font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            y=self.height()-36-10
            for index,number in self.markers:
                if not 0<=index<len(self.series.closes):continue
                cx=x_of(index)
                painter.setPen(QPen(QColor(colors.text),1.3));painter.setBrush(QColor(colors.surface))
                painter.drawEllipse(QPointF(cx,y),8,8)
                painter.drawText(QRectF(cx-8,y-8,16,16),Qt.AlignmentFlag.AlignCenter,number)
        self._paint_annotations(painter,colors)
        painter.end()

    def _paint_annotations(self,painter,colors):
        """Restrained stock-chart typography, connected to this case's exact points.

        Labels are painted, not child widgets: pointer/keyboard handling and the
        chart's original SVG, dates, cursor and report inputs remain unchanged.
        """
        self.annotations=();self.annotation_boxes=()
        if not self.annotations_enabled:return
        from .guide_case_annotations import case_annotations
        from .font_policy import number_font
        from .typography import scaled_font,is_dark
        font=number_font(scaled_font(self.font(),12,400))
        metrics=QFontMetricsF(font);line_height=metrics.lineSpacing()
        proposed=case_annotations(self.series,self.keys,self.cursor,self.ctx.language,
                   width=self.width(),legend_top=self.legend_top(),layout=self.layout_info,
                   crop=self.crop,focus=self.annotation_focus,dark=is_dark(colors))
        painter.save();painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        painter.setFont(font)
        drawn=[];boxes=[]
        for panel in dict.fromkeys(item.panel for item in proposed):
            group=[item for item in proposed if item.panel==panel]
            left,top,right,bottom=panel
            left=max(3.,left+4);right=min(self.width()-3.,right-4)
            top=max(3.,top+3);bottom=min(self.height()-3.,bottom-3)
            available=right-left
            if available<70 or bottom-top<line_height*2+8:continue
            columns=min(len(group),max(1,int(available//210)))
            box_height=line_height*2+8;gap=6.
            rows=max(1,int((bottom-top+gap)//(box_height+gap)))
            group=group[:columns*rows]
            cell=(available-gap*(columns-1))/columns
            box_width=min(230.,cell)
            for i,item in enumerate(group):
                bx=left+(i%columns)*(cell+gap)
                by=top+(i//columns)*(box_height+gap)
                box=QRectF(bx,by,box_width,box_height)
                tone=QColor(item.color or colors.text)
                if item.x is not None and item.y is not None:
                    # A plain leader and a small point use the line's own colour.
                    painter.setPen(QPen(tone,0.8))
                    edge=QPointF(min(max(item.x,box.left()+3),box.right()-3),
                                min(max(item.y,box.top()+3),box.bottom()-3))
                    painter.drawLine(edge,QPointF(item.x,item.y))
                    painter.setBrush(QColor(colors.surface))
                    painter.drawEllipse(QPointF(item.x,item.y),2.,2.)
                fill=QColor(colors.surface);fill.setAlpha(240)
                painter.setBrush(fill);painter.setPen(QPen(QColor(colors.border),0.6))
                painter.drawRoundedRect(box,3,3)
                for row,text in enumerate(item.text[:2]):
                    painter.setPen(QColor(colors.text if row==0 else colors.muted))
                    fitted=metrics.elidedText(str(text),Qt.TextElideMode.ElideRight,box.width()-12)
                    painter.drawText(QRectF(box.left()+6,box.top()+4+row*line_height,
                                           box.width()-12,line_height),
                                     int(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter),fitted)
                drawn.append(item);boxes.append(box)
        self.annotations=tuple(drawn);self.annotation_boxes=tuple(boxes)
        painter.restore()
        full=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        if drawn:full+='\n'+'\n'.join(' · '.join(item.text) for item in drawn)
        self.setAccessibleDescription(full);self.setToolTip(full)

    def keyPressEvent(self,event):
        if self.series and event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right,Qt.Key.Key_Home,Qt.Key.Key_End):
            at=(0 if event.key()==Qt.Key.Key_Home else len(self.series.closes)-1 if event.key()==Qt.Key.Key_End
                else self.cursor+(1 if event.key()==Qt.Key.Key_Right else -1))
            self.cursor_changed.emit(max(0,min(len(self.series.closes)-1,at)))
            event.accept();return
        super().keyPressEvent(event)


class _Flip(QWidget):
    """One row of parts that stacks them when narrower than `breakpoint` (the draft's one-line rows at 1440 px stay
    readable in a 1000 px window instead of widening the canvas)."""

    def __init__(self, breakpoint, spacing=10):
        super().__init__()
        self.breakpoint=breakpoint
        self.setProperty('guide','box')
        self.box=QBoxLayout(QBoxLayout.Direction.LeftToRight,self)
        self.box.setContentsMargins(0,0,0,0);self.box.setSpacing(spacing)
        self.box.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

    def minimumSizeHint(self):
        parts=[self.box.itemAt(i) for i in range(self.box.count())]
        width=max((item.minimumSize().width() for item in parts if not item.isEmpty()),default=0)
        return QSize(width,super().minimumSizeHint().height())

    def resizeEvent(self,event):
        super().resizeEvent(event)
        direction=(QBoxLayout.Direction.LeftToRight if self.width()>=self.breakpoint
                   else QBoxLayout.Direction.TopToBottom)
        if self.box.direction()!=direction:self.box.setDirection(direction)


def _style(widget, **props):
    """Set (or clear, with None) style properties and repolish."""
    for name, value in props.items():
        widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)


class ReadingCard(QFrame):
    """One term's explanation, in three arrangements (`set_variant`):

    'panel'  the embedded explorer's panel (the old look): name, category, one line, '자세한 해설과 주의점' with the
             four sections behind it, and 차트에 표시 / 차트에서 빼기;
    'side'   a card of the guide page's 해석 column (draft_03_guide): name and parameters, the state pill, the reading
             at the chart's date, a gauge, the 결론 block (core.education.outlook: ▲ / ▼ conditions, 지금은, 근거 수준),
             one concept line and one limit line, the four sections behind '자세한 해설과 주의점';
    'page'   a glossary term on the 투자 용어 canvas: category, name, summary and its sections, open."""

    def __init__(self):
        super().__init__()
        from .stock_detail_style import label as sd_label, numbers
        from .indicator_picker import ConclusionBlock, Gauge
        from .page_kit import rule
        self.key=None;self.variant=None
        self.box=QVBoxLayout(self)
        head=QHBoxLayout();head.setContentsMargins(0,0,0,0);head.setSpacing(8)
        column=QVBoxLayout();column.setContentsMargins(0,0,0,0);column.setSpacing(2)
        self.category=sd_label(wrap=True)
        self.title=sd_label(wrap=True,selectable=True)
        self.eyebrow=sd_label(wrap=True)          # the category above the title ('page')
        column.addWidget(self.eyebrow);column.addWidget(self.title);column.addWidget(self.category)
        head.addLayout(column,1)
        self.pill=sd_label('pill')
        head.addWidget(self.pill,0,Qt.AlignmentFlag.AlignTop)
        self.chart=QPushButton()
        head.addWidget(self.chart,0,Qt.AlignmentFlag.AlignTop)
        self.box.addLayout(head)
        self.summary=sd_label(wrap=True,selectable=True)
        self.box.addWidget(self.summary)
        self.reading=numbers(sd_label('guideReadingSmall',wrap=True,selectable=True))
        self.box.addWidget(self.reading)
        self.gauge=Gauge()
        self.box.addWidget(self.gauge)
        self.conclusion=ConclusionBlock()
        self.box.addWidget(self.conclusion)
        self.notes_rule=rule();self.notes_rule.setProperty('guide','rule')
        self.box.addWidget(self.notes_rule)
        self.notes=QWidget();self.notes.setProperty('guide','box');notes=QGridLayout(self.notes)
        notes.setContentsMargins(0,0,0,0);notes.setHorizontalSpacing(7);notes.setVerticalSpacing(2)
        self.concept_key=sd_label();self.concept=sd_label(wrap=True,selectable=True)
        self.limit_key=sd_label();self.limit=sd_label(wrap=True,selectable=True)
        for row,(key,text) in enumerate(((self.concept_key,self.concept),(self.limit_key,self.limit))):
            key.setProperty('guide','key');text.setProperty('guide','note')
            notes.addWidget(key,row,0,Qt.AlignmentFlag.AlignTop);notes.addWidget(text,row,1)
        notes.setColumnStretch(1,1)
        self.box.addWidget(self.notes)
        self.more=QPushButton();self.more.setCheckable(True)
        self.box.addWidget(self.more,0,Qt.AlignmentFlag.AlignLeft)
        self.body=QWidget();self.body.setProperty('guide','box');body=QVBoxLayout(self.body)
        body.setContentsMargins(0,0,0,0);body.setSpacing(6)
        self.sections=[]
        for _ in range(4):
            heading=sd_label(wrap=True);text=sd_label(wrap=True,selectable=True)
            body.addWidget(heading);body.addWidget(text)
            self.sections.append((heading,text))
        self.box.addWidget(self.body);self.body.hide()
        self.more.toggled.connect(self._more_toggled)
        self.set_variant('panel')

    def _more_toggled(self,on):
        self.body.setVisible(on or self.variant=='page')

    def set_variant(self, variant):
        if variant==self.variant:return
        self.variant=variant
        panel,side,page=variant=='panel',variant=='side',variant=='page'
        self.setObjectName('panel' if panel else '')
        _style(self,sd='guideCard' if side else None,kit='card' if page else None)
        self.box.setContentsMargins(*((22,20,22,22) if panel else (14,12,14,12) if side else (28,24,28,26)))
        self.box.setSpacing(14 if panel else 7 if side else 10)
        self.title.setTextFormat(Qt.TextFormat.RichText if side else Qt.TextFormat.PlainText)
        _style(self.title,role='heading' if panel else None,kit='lead' if side else None,
               guide='termTitle' if page else 'name' if side else None)
        _style(self.category,role='caption' if panel else None,guide=None if panel else 'note')
        _style(self.eyebrow,guide='termCategory' if page else None)
        _style(self.summary,role='' if panel else None,guide='termSummary' if page else None)
        _style(self.more,sd='link' if side else None)
        for heading,text in self.sections:
            heading.setContentsMargins(0,0 if panel else 6,0,0)   # a little air between the sections
            _style(heading,role='heading' if panel else None,
                   guide=None if panel else 'sectionTitle' if side else 'pageTitle')
            _style(text,role='' if panel else None,guide=None if panel else 'sectionText' if side else 'pageText')
        self.category.setVisible(panel)
        self.eyebrow.setVisible(page)
        self.summary.setVisible(not side)
        self.chart.setVisible(panel)
        for widget in (self.reading,self.gauge,self.conclusion,self.notes_rule,self.notes,self.pill):
            widget.setVisible(side)
        self.more.setVisible(not page)
        self.body.setVisible(page or self.more.isChecked())
        self.setMaximumWidth(760 if page else 16777215)


class IndicatorGuide(QWidget):
    """Visible multiple choices and one shared historical chart; no search required."""

    def __init__(self, *, locale=None, history=None):
        super().__init__()
        from .app import label, panel
        self.ctx=locale or LocaleContext()
        self.keys=();self.external=from_history(history) if history else None
        self.series=None;self.cursor=0;self.meta={};self.case_name='2020'
        self.focus=None
        self.docked=False;self.workspace=None;self.cards={};self.hint=None;self._bars=(None,None)
        self.educational_lessons=False;self.lesson=None  # Signals/history embeds stay off.
        self.detail_timer=QTimer(self);self.detail_timer.setSingleShot(True)
        self.detail_timer.timeout.connect(self.reveal_detail)
        self.market_series=None;self.category='all'
        self.setObjectName('studyGuide')
        layout=QVBoxLayout(self);layout.setContentsMargins(0,12,0,0);layout.setSpacing(14)
        # The guide is embedded in a scroll page: long translated labels must
        # wrap within its viewport instead of setting the entire page width.
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.intro=label('');layout.addWidget(self.intro)
        self.steps=label('','caption');layout.addWidget(self.steps)
        box,inner=panel('')
        self.selection_box=box
        self.selection_title=label('', 'heading');inner.addWidget(self.selection_title)
        from .category_picker import CategoryFlow
        filter_host=QWidget();filter_row=CategoryFlow(filter_host);inner.addWidget(filter_host)
        self.filter_host=filter_host
        self.categories={}
        for key in ('all',*CATEGORIES):
            button=QPushButton();button.setCheckable(True);button.setProperty('sd','period')
            button.clicked.connect(lambda checked=False,k=key:self.filter_category(k))
            filter_row.addWidget(button);self.categories[key]=button
        self.options={}
        for spec in INDICATORS:
            button=QPushButton();button.setCheckable(True);button.setProperty('sd','text')
            button.setProperty('studyChoice',True)
            button.setMaximumWidth(215)
            button.clicked.connect(lambda checked,k=spec.key:self.toggle(k,checked))
            self.options[spec.key]=button
        self.choices=QWidget();self.choices.setMaximumWidth(1040)
        self.choice_flow=CategoryFlow(self.choices)
        for button in self.options.values():self.choice_flow.addWidget(button)
        inner.addWidget(self.choices)
        selected=QHBoxLayout()
        self.selected_label=label('', 'caption');selected.addWidget(self.selected_label,1)
        self.clear=QPushButton();self.clear.clicked.connect(self.clear_selection);selected.addWidget(self.clear)
        inner.addLayout(selected)
        self.chip_host=QWidget();self.chip_row=CategoryFlow(self.chip_host)
        inner.addWidget(self.chip_host);self.chips={}
        self.case=QComboBox()
        self.case.setObjectName('sdInterval');self.case.setMaximumWidth(420)
        for key in ('auto','2020','2022','2019'):self.case.addItem(key,key)
        self.case.currentIndexChanged.connect(self.render)
        self.case.setVisible(self.external is None);inner.addWidget(self.case)
        layout.addWidget(box)
        # The focused term's explanation (an indicator, or a glossary term chosen from 투자 용어).
        self.detail=ReadingCard();self.detail.hide()
        self.detail.chart.clicked.connect(self._toggle_detail_chart)
        self.detail_title=self.detail.title;self.detail_category=self.detail.category
        self.detail_summary=self.detail.summary;self.detail_chart=self.detail.chart
        self.detail_sections=self.detail.sections;self.detail_body=self.detail.body
        self.detail_more=self.detail.more
        self.why=label('','muted')
        self.source=label('','caption')
        self.chart_area=QWidget();chart_layout=QVBoxLayout(self.chart_area)
        chart_layout.setContentsMargins(0,0,0,0)
        self.reading_area=QWidget();reading_layout=QVBoxLayout(self.reading_area)
        reading_layout.setContentsMargins(0,0,0,0);reading_layout.setSpacing(14)
        from .chart_study import ChartStudy
        self.study=ChartStudy(self.chart_area,self.reading_area)
        layout.addWidget(self.study)
        self.chart=TechnicalChart();self.chart.cursor_changed.connect(self.move_cursor);chart_layout.addWidget(self.chart)
        self.readout=label('');chart_layout.addWidget(self.readout)
        self.slider=QSlider(Qt.Orientation.Horizontal);self.slider.valueChanged.connect(self.move_cursor);chart_layout.addWidget(self.slider)
        self.ohlcv_notice=label('','caption');chart_layout.addWidget(self.ohlcv_notice)
        self.line_styles=label('','caption');chart_layout.addWidget(self.line_styles)
        chart_layout.addWidget(self.why);chart_layout.addWidget(self.source)
        reading_layout.addWidget(self.detail)
        self.combination=label('');reading_layout.addWidget(self.combination)
        self.fail_title=label('','heading');reading_layout.addWidget(self.fail_title)
        self.fail_note=label('','caption');reading_layout.addWidget(self.fail_note)
        self.event_host=QWidget();self.event_layout=QVBoxLayout(self.event_host)
        self.event_layout.setContentsMargins(0,0,0,0);reading_layout.addWidget(self.event_host)
        reading_layout.addStretch()
        terms,terms_layout=panel('')
        self.terms_box=terms
        self.terms_title=label('', 'heading');terms_layout.addWidget(self.terms_title)
        self.terms=QComboBox();self.terms.setEditable(False)
        for term in glossary.TERMS:
            if term.key not in BY_KEY:self.terms.addItem('',term.key)
        self.terms.activated.connect(self.choose_term)
        terms_layout.addWidget(self.terms);layout.addWidget(terms)
        self.export=QPushButton();self.export.clicked.connect(self.save_report)
        layout.addWidget(self.export,0,Qt.AlignmentFlag.AlignLeft)
        self.notice=label('','caption');layout.addWidget(self.notice)
        self.render()

    # The guide page (owner-approved draft 2026-11-17) -----------------------------------------------------------
    def dock_into(self, ws):
        """Place the guide's widgets in a page kit `Workspace` (draft_03_guide). Every widget, signal, calculation,
        export and text path stays; only where they sit and how they look change. The workspace becomes this
        widget's only content."""
        from .category_picker import CategoryFlow
        from .page_kit import Card, EmptyState, KeyFigures, Text
        from .stock_detail_style import label as sd_label
        self.docked=True;self.workspace=ws
        # A preselected undocked explorer has compact chips without docked
        # colour bars/value labels. Rebuild only those UI widgets; keep every
        # selection and the original data/date/report inputs intact.
        for chip in tuple(self.chips.values()):
            for part in (chip,getattr(chip,'values',None)):
                if part is not None:
                    self.chip_row.removeWidget(part);part.hide();part.deleteLater()
        self.chips.clear()
        self.educational_lessons=True  # This entry point is the dedicated technical-guide page.
        own=self.layout()
        while own.count():
            item=own.takeAt(0)
            if item.widget() is not None:item.widget().hide()
        own.setSpacing(0)
        own.addWidget(ws)
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        # Toolbar: 기술지표 27 | 투자 용어, the education badge, then 모두 해제 and 보고서 저장 on the right.
        count=len(INDICATORS)
        ws.add_mode((f'Indicators {count}',f'기술지표 {count}'))
        terms_mode=ws.add_mode(('Glossary','투자 용어'))
        self.badge=ws.add_badge(BADGE)
        for button,kit in ((self.clear,'ghost'),(self.export,'secondary')):
            button.setParent(None);_style(button,kit=kit)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            ws.add_toolbar(button,right=True)
        ws.mode_changed.connect(lambda _index:self._sync_toolbar())
        ws.toolbar_host.installEventFilter(self)
        # Canvas: name line with the example, price figures at the reading date, the chart card, small print.
        canvas=ws.modes[0].canvas
        canvas.setSpacing(10)
        head=_Flip(640);row=head.box
        self.case_title=sd_label(wrap=True,selectable=True)
        self.case_title.setTextFormat(Qt.TextFormat.RichText)
        self.case_title.setProperty('guide','caseTitle')
        row.addWidget(self.case_title,1,Qt.AlignmentFlag.AlignVCenter)
        self.case_box=QWidget();self.case_box.setProperty('guide','box');case_row=QHBoxLayout(self.case_box)
        case_row.setContentsMargins(0,0,0,0);case_row.setSpacing(8)
        self.case_caption=Text(('Example','사례'),'fieldLabel')
        case_row.addWidget(self.case_caption)
        self.case.setParent(None);self.case.setMaximumWidth(340)
        self.case.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        case_row.addWidget(self.case);case_row.addStretch(1)
        row.addWidget(self.case_box,0,Qt.AlignmentFlag.AlignVCenter)
        canvas.addWidget(head)
        figures=QWidget();figures.setProperty('guide','box');figure_row=QHBoxLayout(figures)
        figure_row.setContentsMargins(0,0,0,0);figure_row.setSpacing(18)
        self.reading_date=sd_label(selectable=True);self.reading_date.setProperty('guide','date')
        figure_row.addWidget(self.reading_date,0,Qt.AlignmentFlag.AlignTop)
        self.figures=KeyFigures();figure_row.addWidget(self.figures,1)
        canvas.addWidget(figures)
        card=Card(margins=(16,12,16,8),spacing=8)
        self.chart_card=card
        # The owner's case chart remains the first, always-visible figure.
        # Keep its name/date/price controls in their original canvas positions.
        self.context_host=QWidget();self.context_host.setProperty('guide','box')
        context=QVBoxLayout(self.context_host);context.setContentsMargins(0,0,0,0);context.setSpacing(10)
        card.body.addWidget(self.context_host)
        legend=QWidget();legend.setProperty('guide','box');legend_row=QHBoxLayout(legend)
        legend_row.setContentsMargins(0,0,0,0);legend_row.setSpacing(10)
        self.chip_host.setParent(None);self.chip_host.setProperty('guide','box');self.chip_row.setSpacing(12)
        legend_row.addWidget(self.chip_host,1)
        self.hint=sd_label(wrap=True);self.hint.setProperty('guide','hint')
        legend_row.addWidget(self.hint,1)
        context.addWidget(legend)
        for widget in (self.chart,self.readout,self.slider,self.ohlcv_notice,self.line_styles,self.why,self.source):
            self.chart_area.layout().removeWidget(widget)
        self.chart.legend=False;self.chart.candles=True;self.chart.annotations_enabled=True
        context.addWidget(self.chart)
        scrub=QWidget();scrub.setProperty('guide','box');scrub_row=QHBoxLayout(scrub);scrub_row.setContentsMargins(0,0,0,0);scrub_row.setSpacing(10)
        scrub_row.addWidget(self.slider,1)
        self.keys_hint=sd_label();self.keys_hint.setProperty('guide','keys')
        scrub_row.addWidget(self.keys_hint)
        context.addWidget(scrub)
        self.readout.setParent(card);self.readout.hide()   # its text stays the chart's accessible description
        self.line_styles.setParent(card);self.line_styles.hide()   # the tags carry each indicator's colour
        # The signals that missed: title, numbered chips (they move the reading date), a short hindsight note.
        self.fail_row=_Flip(660);fail=self.fail_row.box
        fail.setContentsMargins(0,8,0,4)
        self.reading_area.layout().removeWidget(self.fail_title)
        self.reading_area.layout().removeWidget(self.fail_note)
        _style(self.fail_title,role=None,guide='failTitle')
        fail.addWidget(self.fail_title,0,Qt.AlignmentFlag.AlignTop)
        self.old_event_host=self.event_host;self.old_event_host.setParent(self);self.old_event_host.hide()
        self.event_host=QWidget();self.event_host.setProperty('guide','box');self.event_layout=CategoryFlow(self.event_host)
        fail.addWidget(self.event_host,1)
        self.fail_short=Text(('Hindsight · not a win rate','사후 관찰 · 승률 아님'))
        self.fail_short.setProperty('guide','failNote')
        fail.addWidget(self.fail_short,0,Qt.AlignmentFlag.AlignTop)
        self.fail_rule=QFrame();self.fail_rule.setProperty('guide','rule');self.fail_rule.setFixedHeight(1)
        context.addWidget(self.fail_rule)
        context.addWidget(self.fail_row)
        canvas.addWidget(card)
        # Small print: the example's provenance, why it was chosen, missing OHLCV, the hindsight rule in full.
        notes=QWidget();notes.setProperty('guide','box');notes_column=QVBoxLayout(notes);notes_column.setContentsMargins(4,2,4,0);notes_column.setSpacing(3)
        for widget in (self.why,self.source,self.ohlcv_notice,self.fail_note):
            _style(widget,role=None,guide='fine')
            notes_column.addWidget(widget)
        context.addWidget(notes)
        # Invented drawings are a clearly separate, optional supplement AFTER
        # the original chart and its provenance, never its replacement.
        supplement=Card(margins=(16,8,16,8),spacing=8)
        self.lesson_card=supplement
        self.lesson_toggle=QPushButton();self.lesson_toggle.setCheckable(True)
        self.lesson_toggle.setProperty('kit','ghost')
        self.lesson_toggle.toggled.connect(self._toggle_lesson)
        supplement.body.addWidget(self.lesson_toggle,0,Qt.AlignmentFlag.AlignLeft)
        from .guide_lessons import GuideLesson
        self.lesson=GuideLesson(supplement)
        self.lesson.choose_requested.connect(self.choose)
        supplement.body.addWidget(self.lesson)
        self.lesson.hide()
        canvas.addWidget(supplement)
        canvas.addStretch(1)
        self.study.setParent(self);self.study.hide()
        # Right column: 지표 (the studies by category) | 해석 (a card per selected study); the combined reading and the
        # education note are pinned at its foot.
        side=ws.modes[0].side
        self.reading_side=side
        pick=side.add_page(('Indicators','지표'))
        pick.setSpacing(12)
        self.reading_page=side.add_page(('Reading','해석'))
        self.reading_page.setSpacing(8)
        _style(self.selection_title,role=None,guide='intro')
        self.selection_title.setParent(None);pick.addWidget(self.selection_title)
        self.groups={}
        for category in CATEGORIES:
            group=QWidget();group.setProperty('guide','box')
            column=QVBoxLayout(group);column.setContentsMargins(0,0,0,0);column.setSpacing(6)
            title_row=QHBoxLayout();title_row.setContentsMargins(2,0,0,0);title_row.setSpacing(6)
            name=sd_label();name.setProperty('guide','groupTitle')
            number=sd_label();number.setProperty('guide','groupCount')
            title_row.addWidget(name);title_row.addWidget(number);title_row.addStretch(1)
            column.addLayout(title_row)
            host=QWidget();host.setProperty('guide','box');flow=CategoryFlow(host);flow.setSpacing(5)
            column.addWidget(host)
            group.name,group.number,group.flow,group.host=name,number,flow,host
            pick.addWidget(group);self.groups[category]=group
        for key,button in self.options.items():
            self.choice_flow.removeWidget(button)
            _style(button,sd=None,studyChoice=None,kit='chip')
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            group=self.groups[study(key).category]
            group.flow.addWidget(button)
        self.selection_box.hide()
        self.reading_empty=EmptyState(('Choose an indicator under Indicators to read it here at the chart’s date.',
                                       '지표에서 고르면 차트 날짜의 해석과 결론이 여기에 나와요.'))
        self.reading_empty.setMinimumHeight(220);self.reading_empty.text.setProperty('guide','hint')
        self.reading_page.addWidget(self.reading_empty)
        foot=side.foot;foot.setSpacing(5)
        together=QHBoxLayout();together.setContentsMargins(0,0,0,0);together.setSpacing(6)
        self.together_key=Text(('Together','함께 읽으면'));self.together_key.setProperty('guide','togetherKey')
        together.addWidget(self.together_key,0,Qt.AlignmentFlag.AlignTop)
        self.reading_area.layout().removeWidget(self.combination)
        _style(self.combination,role=None,guide='together')
        together.addWidget(self.combination,1)
        foot.addLayout(together)
        self.notice.setParent(None);_style(self.notice,role=None,guide='fine')
        foot.addWidget(self.notice)
        self.reading_area.layout().removeWidget(self.detail)
        self.reading_page.addWidget(self.detail)
        # 투자 용어: the chosen term on the canvas, the terms by category on the right.
        self.term_canvas=terms_mode.canvas
        self.term_empty=EmptyState(('Choose a term on the right to read what it means, where it is used and its limits.',
                                    '오른쪽에서 용어를 고르면 뜻과 쓰임, 해석의 한계를 볼 수 있어요.'))
        self.term_empty.setMinimumHeight(320);self.term_empty.text.setProperty('guide','hint')
        self.term_canvas.addWidget(self.term_empty)
        self.term_canvas.addStretch(1)
        term_page=terms_mode.side.add_page()
        term_page.setSpacing(12)
        _style(self.terms_title,role=None,guide='intro')
        self.terms_title.setParent(None);term_page.addWidget(self.terms_title)
        self.terms.setParent(self);self.terms.hide()    # the list below drives it; kept for keyboard callers and tests
        self.terms_box.hide()
        self.term_groups={};self.term_buttons={}
        for i in range(self.terms.count()):
            key=self.terms.itemData(i);category=glossary.BY_KEY[key].category
            group=self.term_groups.get(category)
            if group is None:
                group=QWidget();group.setProperty('guide','box')
                column=QVBoxLayout(group);column.setContentsMargins(0,0,0,0);column.setSpacing(6)
                group.name=sd_label();group.name.setProperty('guide','groupTitle')
                column.addWidget(group.name)
                host=QWidget();host.setProperty('guide','box')
                group.flow=CategoryFlow(host);group.flow.setSpacing(5);column.addWidget(host)
                term_page.addWidget(group);self.term_groups[category]=group
            button=QPushButton();button.setCheckable(True);_style(button,kit='chip')
            button.setCursor(Qt.CursorShape.PointingHandCursor);button.setMaximumWidth(300)
            button.clicked.connect(lambda checked=False,k=key:self.choose_term(self.terms.findData(k)))
            group.flow.addWidget(button);self.term_buttons[key]=button
        self.term_note=Text(('Explanations for learning · not investment advice','용어 설명은 교육용이에요 · 투자 권유 아님'))
        self.term_note.setProperty('guide','fine')
        terms_mode.side.foot.addWidget(self.term_note)
        ws.finish()
        self.export.show();self.notice.show()
        self.render()
        return ws

    def show_side(self, index):
        """지표 (0) or 해석 (1) in the guide page's right column."""
        if self.docked:self.reading_side.show_page(index)

    def _sync_toolbar(self):
        if not self.docked:return
        self.clear.setVisible(bool(self.keys) and self.workspace.current_mode()==0)
        self.export.setVisible(self.workspace.current_mode()==0)   # its saved/failed line is in that mode's column
        self._fit_toolbar()

    def _fit_toolbar(self):
        """The badge steps aside when the toolbar row cannot hold it in this language and width (the same education
        note stays at the foot of the right column); nothing in the row is ever clipped."""
        from .page_kit import pick
        ws=self.workspace;lang='ko' if _ko(self.ctx) else 'en'

        def advance(widget,text,pad):
            widget.ensurePolished()
            return widget.fontMetrics().horizontalAdvance(text)+pad
        need=advance(ws.title,pick(lang,ws.title.pair),4)
        need+=sum(advance(button,pick(lang,button.pair),26) for button in ws.switch.buttons)+8
        need+=sum(button.sizeHint().width() for button in (self.clear,self.export) if not button.isHidden())
        badge=advance(self.badge,'● '+pick(lang,BADGE),24)
        spacing=ws.toolbar.spacing()*3+ws.toolbar_right.spacing()+24
        wanted=BADGE if need+badge+spacing<=ws.toolbar_host.width() else ''
        if self.badge.pair!=wanted:self.badge.set_pair(wanted)

    def eventFilter(self, watched, event):
        from PyQt6.QtCore import QEvent
        if self.docked and watched is self.workspace.toolbar_host and event.type()==QEvent.Type.Resize:
            self._fit_toolbar()
        return False

    def _price(self, value):
        """A price in the example's own precision (reference rates four decimals, won whole numbers)."""
        try:value=float(value)
        except (TypeError,ValueError):return '—'
        if not math.isfinite(value):return '—'
        unit=getattr(self.series,'unit','')
        digits=4 if unit=='EUR per USD' or abs(value)<1 else 0 if unit=='KRW' or (abs(value)>=1000 and unit!='USD') else 2
        return self.ctx.number(value,digits).replace('-','−')

    def _value(self, kind, value):
        if kind=='price':return self._price(value)
        return study_guide.format_value(kind,value,self.ctx.language)

    def _engine_bars(self):
        if self._bars[0] is not self.series:self._bars=(self.series,bars_for(self.series))
        return self._bars[1]

    def _interval(self):
        return getattr(self.series,'interval','1d') or '1d'

    def _short_date(self, iso, *, year=True):
        text=self.ctx.date(iso)
        if not year:
            text=re.sub(r'^\d{4}\. ','',text) if _ko(self.ctx) else re.sub(r', \d{4}$','',text)
        return text

    def _case_line(self):
        """'삼성전자 · 005930 · 일 단위 · 2026. 6. 15. → 11. 10.' (the draft's name line)."""
        ctx=self.ctx;series=self.series;ko=_ko(ctx)
        name=code=series.symbol
        snapshot=getattr(series,'snapshot',None)
        if snapshot is not None:
            try:
                from .home_view import directory_name
                name=directory_name(getattr(self.window(),'symbol_directory',None),snapshot.request.instrument,
                                    'ko' if ko else 'en')
            except Exception:
                name=code
        try:
            from .stock_detail import interval_words
            interval=interval_words(self._interval(),'ko' if ko else 'en',long=True)
        except Exception:
            interval=self._interval()
        first,last=series.dates[0],series.dates[-1]
        same=str(first)[:4]==str(last)[:4]
        span=self._short_date(first)+' → '+self._short_date(last,year=not same)
        parts=([code] if name!=code else [])+[interval,span]
        from core.theme import LIGHT
        colors=getattr(self.window(),'colors',LIGHT)
        return (f'<span style="font-size:15px;font-weight:600;color:{colors.text}">{escape(name)}</span>'
                f' · '+' · '.join(escape(p) for p in parts))

    def _docked_render(self):
        """The page's own parts that follow the selection, the example and the language."""
        if not self.docked:return
        from core.theme import LIGHT
        from .typography import is_dark
        ctx=self.ctx;ko=_ko(ctx)
        colors=getattr(self.window(),'colors',LIGHT)
        if self.educational_lessons and self.lesson is not None:
            lesson_key=self.focus if self.focus in self.keys else next(iter(self.keys),None)
            self.lesson.set_lesson(lesson_key,ctx.language,is_dark(colors))
            self.chart.annotation_focus=lesson_key
            opened=self.lesson_toggle.isChecked()
            self.lesson_toggle.setText(('보조 학습 그림 접기' if opened else '보조 학습 그림 보기') if ko else
                                       ('Hide supplementary diagram' if opened else 'Show supplementary diagram'))
            self.lesson_toggle.setAccessibleDescription('사례 아래에 따로 보는 가상 학습 그림이에요. 위 사례 차트와 보고서 값은 바뀌지 않아요.' if ko else
                                                       'An invented supplement below the case. The original case chart and report values stay unchanged.')
        self.case_title.setText(self._case_line())
        self.case_box.setVisible(self.external is None)
        count=len(self.keys)
        segment=self.reading_side.segment.buttons
        segment[0].set_pair((f'Indicators {count}' if count else 'Indicators',f'지표 {count}' if count else '지표'))
        self.selection_title.setText(('기술지표 27개를 쓰임에 따라 묶었어요. 여러 개를 고르면 같은 날짜에서 함께 비교해요.' if ko else
                                      'The 27 indicators grouped by use. Choose several to compare them on the same date.')
                                     .replace('27',str(len(INDICATORS))))
        for category,group in self.groups.items():
            group.name.setText(CATEGORY_NAMES[category][0 if ko else 1])
            on=sum(1 for key in self.keys if study(key).category==category)
            total=sum(1 for spec in INDICATORS if study(spec.key).category==category)
            group.number.setText(f'{on}/{total}' if on else str(total))
        self.hint.setText(self.intro_text());self.hint.setVisible(not self.keys)
        self.chip_host.setVisible(bool(self.keys))
        self.keys_hint.setText(('← → 하루씩' if self._interval()=='1d' else '← → 한 칸씩') if ko else
                               ('← → one day' if self._interval()=='1d' else '← → one step'))
        # The tags: colour bar, short name (shows its card in 해석), × (removes it); values follow the date.
        for key,chip in self.chips.items():
            name=study(key).name(ctx.language)
            chip.show_button.setToolTip(name+' · '+('해석 보기' if ko else 'show its reading'))
        # 해석: the focused study's card is `detail`; the others are cards of the same kind.
        for key in [k for k in self.cards if k not in self.keys or k==self.focus]:
            card=self.cards.pop(key);self.reading_page.removeWidget(card);card.hide();card.deleteLater()
        layout=self.reading_page
        for position,key in enumerate(self.keys):
            if key==self.focus:
                card=self.detail
            else:
                card=self.cards.get(key)
                if card is None:
                    card=ReadingCard();card.set_variant('side');self.cards[key]=card
                self._fill_explanation(card,key)
            if layout.indexOf(card)!=position+1:
                layout.removeWidget(card);layout.insertWidget(position+1,card)
            card.show()
        self.reading_empty.setVisible(not self.keys)
        # The focused glossary term sits on the 투자 용어 canvas.
        if self.focus is not None and self.focus not in BY_KEY:
            if self.term_canvas.indexOf(self.detail)<0:
                self.reading_page.removeWidget(self.detail)
                self.term_canvas.insertWidget(0,self.detail)
            self.detail.set_variant('page')
        elif self.reading_page.indexOf(self.detail)<0:
            self.term_canvas.removeWidget(self.detail)
            self.reading_page.insertWidget(1+(self.keys.index(self.focus) if self.focus in self.keys else 0),self.detail)
        if self.focus in BY_KEY:
            self.detail.set_variant('side')
            # 해석 lists the studies on the chart; one taken off the chart keeps the focus but no card.
            self.detail.setVisible(self.focus in self.keys)
        self.term_empty.setVisible(self.focus is None or self.focus in BY_KEY)
        for key,button in self.term_buttons.items():
            button.setText(glossary.name(key,ctx))
            button.setToolTip(glossary.summary(key,ctx))
            button.blockSignals(True);button.setChecked(key==self.focus);button.blockSignals(False)
        for category,group in self.term_groups.items():
            group.name.setText(glossary.category(next(k for k in self.term_buttons if glossary.BY_KEY[k].category==category),ctx))
        self.terms_title.setText(('투자 용어 %d개를 분야별로 모았어요. 고르면 뜻과 쓰임, 해석의 한계를 볼 수 있어요.' if ko else
                                  'The %d investing terms by field. Choose one to read what it means, where it is used '
                                  'and its limits.') % self.terms.count())
        # The signals that missed, numbered in date order; each chip moves the reading date there.
        covered=[key for key in self.keys if key in ('sma','ema','rsi','macd','bb')]
        self.fail_title.setText('빗나간 신호도 보세요' if ko else 'See the signals that missed')
        self.fail_row.setVisible(bool(covered));self.fail_rule.setVisible(bool(covered))
        self.fail_short.setVisible(bool(self.events))
        self.fail_short.setToolTip(ctx.t('failure_note'))
        ordered=sorted(self.events,key=lambda e:e['index'])
        buttons=[self.event_layout.itemAt(i).widget() for i in range(self.event_layout.count())]
        buttons=[b for b in buttons if isinstance(b,QPushButton)]
        markers=[]
        for number,(event,button) in enumerate(zip(ordered,sorted(buttons,key=lambda b:b.property('eventIndex')))):
            start=event['index'];end=min(len(self.series.dates)-1,start+5)
            # The year is left out when it is the example's last year (the draft's '10. 29. → 11. 5.').
            final=str(self.series.dates[-1])[:4]
            first_year=str(self.series.dates[start])[:4]!=final
            same=str(self.series.dates[start])[:4]==str(self.series.dates[end])[:4]
            change=('+' if event['change']>0 else '')+ctx.percent(event['change']).replace('-','−')
            label=CIRCLED[number] if number<len(CIRCLED) else str(number+1)
            prefix=(study(event['indicator']).short+' · ') if len(covered)>1 else ''
            button.setText(f'{label} {prefix}{self._short_date(self.series.dates[start],year=first_year)} → '
                           f'{self._short_date(self.series.dates[end],year=first_year and not same)}  {change}')
            button.setToolTip(button.accessibleName())
            markers.append((start,str(number+1)))
        self.chart.markers=tuple(markers);self.chart.update()
        # Small print: where the example comes from (the name line already shows its symbol and dates).
        self.source.setText(self.source.text().split('\n')[0])
        self.fail_note.setVisible(bool(covered))
        self._sync_toolbar()
        sheet=guide_sheet(colors,is_dark(colors))
        for host in (self.workspace.canvas_stack,self.workspace.side_stack):
            if host.styleSheet()!=sheet:host.setStyleSheet(sheet)
        self._focus_order()

    def _toggle_lesson(self,opened):
        self.lesson.setVisible(bool(opened))
        self._docked_render()

    def _focus_order(self):
        """Tab follows the page as it reads: toolbar, the example, the tags, the chart and its date, the signals that
        missed, then the right column (its switch, the choices, the cards) and the glossary list."""
        ws=self.workspace
        chain=[*ws.switch.buttons,self.clear,self.export]
        chain+=[self.case]
        for key in self.keys:
            chip=self.chips.get(key)
            if chip is not None:chain+=[chip.show_button,chip.remove_button]
        chain+=[self.chart,self.slider]
        chain+=[self.event_layout.itemAt(i).widget() for i in range(self.event_layout.count())
                if isinstance(self.event_layout.itemAt(i).widget(),QPushButton)]
        if self.educational_lessons and self.lesson is not None:
            chain+=[self.lesson_toggle]
            if self.lesson_toggle.isChecked():chain+=self.lesson.focus_widgets()
        chain+=list(self.reading_side.segment.buttons)
        for category in CATEGORIES:
            group=self.groups[category]
            chain+=[group.flow.itemAt(i).widget() for i in range(group.flow.count())]
        chain+=[(self.detail if key==self.focus else self.cards[key]).more for key in self.keys
                if key==self.focus or key in self.cards]
        chain+=list(self.term_buttons.values())
        chain=[widget for widget in chain if widget is not None]
        for first,second in zip(chain,chain[1:]):QWidget.setTabOrder(first,second)

    def _fill_explanation(self, card, key):
        """Name, category, summary and the four sections of `key` (an indicator or a glossary term)."""
        ctx=self.ctx;card.key=key
        spec=BY_KEY.get(key)
        card.setProperty('term',key)
        if spec:
            info=study_guide.guide(key,ctx.language,getattr(self.series,'interval','1d'))
            brief=study_guide.short_guide(key,ctx.language)
            title,category,summary=info.name,info.category,brief.one_liner
            place=('가격 위의 선' if study(key).panel=='price' else '가격 아래의 보조 영역') if ctx.language=='ko' else (
                'Overlay on the price' if study(key).panel=='price' else 'Study area below the price')
            # Owner 2026-11-17: a short concept, then the conclusion (상승/하락 흐름 쪽으로 읽는 경우, evidence) as the
            # interpretation; the regime line closes the limits.
            from core.education import outlook as conclusions
            if key in conclusions.OUTLOOK:
                verdict=conclusions.outlook(key,ctx.language)
                parts=tuple(zip((ctx.t(f) for f in ('meaning','look','interpret','limit')),
                                (verdict.concept,place+' · '+', '.join(l.name(ctx.language) for l in study(key).lines),
                                 conclusions.text_block(key,ctx.language),info.caution)))
            else:
                parts=tuple(zip((ctx.t(f) for f in ('meaning','look','interpret','limit')),
                                (info.what,place+' · '+', '.join(l.name(ctx.language) for l in study(key).lines),info.how,info.caution)))
        else:
            title,category,summary=glossary.name(key,ctx),glossary.category(key,ctx),glossary.summary(key,ctx)
            parts=glossary.sections(key,ctx)
        if card.variant=='side' and spec:
            from core.theme import LIGHT
            colors=getattr(self.window(),'colors',LIGHT)
            match=re.search(r'(\d[\d.·%]*)$',study(key).short)
            params=match.group(1) if match else ''
            card.title.setText(escape(title)+(f'&nbsp;&nbsp;<span style="font-size:12px;font-weight:400;'
                                              f'color:{_faint(colors)}">{escape(params)}</span>' if params else ''))
        else:
            card.title.setText(title)
        card.category.setText(category);card.eyebrow.setText(category)
        card.summary.setText(summary)
        if spec is not None:
            card.chart.setText(ctx.t('remove_from_chart' if key in self.keys else 'add_to_chart'))
        card.chart.setVisible(spec is not None and card.variant=='panel')
        card.more.setText('자세한 해설과 주의점' if ctx.language=='ko' else 'Full explanation and limitations')
        card.more.setAccessibleName(card.more.text()+' · '+title)
        for i,(heading,body) in enumerate(card.sections):
            shown=i<len(parts)
            heading.setVisible(shown);body.setVisible(shown)
            if shown:heading.setText(parts[i][0]);body.setText(parts[i][1])

    def _fill_reading(self, card, key):
        """What a 해석 card says at the reading date: state pill, reading, gauge, 결론 (with 지금은), concept, limit."""
        from core.theme import LIGHT
        from core.education import outlook as conclusions
        from .indicator_picker import guide_parts, state_word, state_tone, gauge_labels, gauge_palette
        from .typography import is_dark
        ctx=self.ctx;lang='ko' if _ko(ctx) else 'en'
        colors=getattr(self.window(),'colors',LIGHT)
        missing=missing_reason(self.series,key,ctx.language)
        conclusion=conclusions.outlook(key,lang) if key in conclusions.OUTLOOK else None
        short=study_guide.short_guide(key,lang)
        reading,code,gauge,current='', '',None,None
        if missing:
            reading=missing
        else:
            values=values_for(self.series,self.keys).get(key)
            bars=self._engine_bars()
            try:
                reading,code,gauge,short,_long=guide_parts(key,bars,language=lang,interval=self._interval(),
                                                          supply=getattr(self.series,'supply',None),values=values,
                                                          index=self.cursor)
            except Exception:
                reading,code,gauge='','',None
            if conclusion is not None:
                try:current=conclusions.now(key,values,bars,self.cursor,lang)
                except Exception:current=None
        card.reading.setText(reading);card.reading.setVisible(bool(reading))
        word=state_word(key,code,lang)
        card.pill.setText(word);_style(card.pill,tone=state_tone(code) or 'flat');card.pill.setVisible(bool(word))
        if gauge is not None:
            kind,position,marks=gauge
            card.gauge.set_value(kind,position,marks,gauge_labels(key,gauge,lang),gauge_palette(colors,is_dark(colors)))
        card.gauge.setVisible(gauge is not None)
        card.conclusion.setVisible(conclusion is not None)
        if conclusion is not None:
            # As the approved draft: one condition per side on the card; '자세한 해설과 주의점' keeps both
            # (outlook.text_block in the 어떻게 읽나요? section).
            from dataclasses import replace
            card.conclusion.show_conclusion(lang,replace(conclusion,up=conclusion.up[:1],down=conclusion.down[:1]),
                                            current)
        card.concept_key.setText('개념' if lang=='ko' else 'Concept')
        card.limit_key.setText('한계' if lang=='ko' else 'Limit')
        card.concept.setText(short.one_liner)
        card.limit.setText(conclusion.regime if conclusion is not None else short.caution)
        return current

    def _docked_cursor(self):
        """Everything that follows the reading date: figures, tag values, the 해석 cards and the combined line."""
        if not self.docked:return
        ctx=self.ctx;ko=_ko(ctx);series=self.series;i=self.cursor
        self.reading_date.setText(self._short_date(series.dates[i]))
        items=[]
        if series.ohlc:
            o,h,l,c=series.ohlc[i]
            items+=[(('Open','시가'),self._price(o),''),(('High','고가'),self._price(h),''),
                    (('Low','저가'),self._price(l),''),(('Close','종가'),self._price(c),'')]
        else:
            close=(('Reference rate','기준환율') if getattr(series,'unit','')=='EUR per USD' else ('Close','종가'))
            items.append((close,self._price(series.closes[i]),''))
        if i>0 and series.closes[i-1]:
            change=series.closes[i]-series.closes[i-1];pct=change/series.closes[i-1]
            sign='+' if change>0 else '−' if change<0 else ''
            items.append((('',''),f'{sign}{self._price(abs(change))} ({sign}{abs(pct)*100:.2f}%)',
                          'up' if change>0 else 'down' if change<0 else ''))
        if series.volume and i<len(series.volume) and series.volume[i] is not None:
            from core.market.rankings import compact
            asset=getattr(series,'asset','')
            volume=(compact(series.volume[i],'shares','ko' if ko else 'en') if asset in ('domestic_stock','overseas_stock')
                    else study_guide.format_value('quantity',series.volume[i],ctx.language))
            items.append((('Volume','거래량'),volume,''))
        if tuple(items)!=self.figures.items:self.figures.set_items(items)   # hover moves the date often
        values=values_for(series,self.keys)
        for key,chip in self.chips.items():
            lines=study(key).lines
            if key not in values:
                chip.values.setText('—');continue
            parts=[]
            for line in lines:
                try:raw=float(values[key][line.id][i])
                except (KeyError,IndexError,TypeError,ValueError):raw=math.nan
                text=self._value(line.kind,raw)
                parts.append(f'{line.name(ctx.language)} {text}' if len(lines)>1 else text)
            chip.values.setText('   '.join(parts))
        nows=[]
        for key in self.keys:
            card=self.detail if key==self.focus else self.cards.get(key)
            if card is not None:nows.append((key,self._fill_reading(card,key)))
        self.combination.setText(self._together(nows))
        self.together_key.setVisible(len(self.keys)>1)

    def _together(self, nows):
        """The foot's combined line: how many selected studies read up, down or neither at this date. A tally, not
        a vote: agreement is not independent evidence (core ui_messages 'combination_text')."""
        ko=_ko(self.ctx)
        if not nows:
            return ('지표를 고르면 이 날짜의 신호를 함께 읽을 수 있어요.' if ko else
                    'Choose indicators to read their signals at this date together.')
        if len(nows)==1:
            return ('지표를 하나 더 고르면 같은 날짜의 신호를 함께 비교할 수 있어요.' if ko else
                    'Choose another indicator to compare signals on the same date.')
        from core.education import outlook as conclusions
        sides=[now.side for _key,now in nows if now is not None]
        if not sides:
            return ('이 날짜에선 함께 읽을 결론이 없어요.' if ko else 'No conclusion can be read at this date.')
        up,down,neutral=(sides.count(s) for s in ('up','down','neutral'))
        unknown=len(nows)-len(sides)
        word=lambda side:conclusions.SIDES[side][0 if ko else 1]
        if up and down:
            parts=[f'{word("up")} {up}',f'{word("down")} {down}']+([f'{word("neutral")} {neutral}'] if neutral else [])
            text=(f'방향이 엇갈려요({" · ".join(parts)}). 보는 기간과 반응 속도가 달라서 생길 수 있어요.' if ko else
                  f'They disagree ({" · ".join(parts)}). Their lookbacks and response speeds differ.')
        elif (up or down) and not neutral and not unknown:
            side='up' if up else 'down'
            text=(f'{len(nows)}개 모두 {word(side)}이에요. 같은 쪽이라고 근거가 그만큼 늘어난 건 아니에요.' if ko else
                  f'All {len(nows)} read as {word(side).lower()}. Agreement does not add that much evidence.')
        elif up or down:
            side='up' if up else 'down'
            text=(f'{word(side)} {up or down} · 나머지는 뚜렷하지 않아요.' if ko else
                  f'{word(side)} {up or down} · the rest show no clear side.')
        else:
            text=('어느 쪽도 뚜렷하지 않아요.' if ko else 'None shows a clear side.')
        return text

    # Shared behaviour ---------------------------------------------------------------------------------------------
    def filter_category(self,key):
        self.category=key
        for name,button in self.categories.items():button.setChecked(name==key)
        if self.docked:
            for category,group in self.groups.items():group.setVisible(key=='all' or category==key)
            return
        for name,button in self.options.items():
            self.choice_flow.removeWidget(button)
            shown=key=='all' or study(name).category==key
            button.setVisible(shown)
            if shown:self.choice_flow.addWidget(button)
        self.choice_flow.invalidate();self.choices.updateGeometry()

    def set_market_snapshot(self,snapshot,supply=None):
        if len(snapshot.candles)<2:return
        self.market_series=from_snapshot(snapshot,supply)
        if self.case.findData('market')<0:self.case.addItem('', 'market')
        self.case.setItemText(self.case.findData('market'),
            '최근 조회한 시장 차트 · '+self.market_series.symbol if self.ctx.language=='ko' else
            'Last observed market chart · '+self.market_series.symbol)
        if self.case.currentData()=='market':self.render()

    def set_locale(self,ctx):
        self.ctx=ctx
        self.render()

    def set_theme(self,colors):
        from .research_style import apply
        from .typography import is_dark
        apply(self,colors,is_dark(colors))
        self.render()

    def intro_text(self):
        if self.docked:
            return ('오른쪽 지표 목록에서 고르면 차트와 해석이 함께 바뀌어요. 여러 개를 고르면 같은 날짜의 신호를 비교할 수 있어요.'
                    if self.ctx.language=='ko' else
                    'Choose an indicator from the list on the right to see it on the chart and read it. '
                    'Choose several to compare signals on the same date.')
        return ('지표를 골라 차트에서 확인해 보세요. 여러 개를 선택하면 같은 기간의 신호를 함께 비교할 수 있어요.'
                if self.ctx.language=='ko' else
                'Choose an indicator and see it on the chart. Select more than one to compare signals over the same period.')

    def choose_term(self,index):
        self.choose(self.terms.itemData(index))
        self.detail_timer.start(0)

    def reveal_detail(self):
        from PyQt6.QtWidgets import QScrollArea
        parent=self.detail.parentWidget()
        while parent is not None and not isinstance(parent,QScrollArea):parent=parent.parentWidget()
        if parent is not None:parent.ensureWidgetVisible(self.detail,0,20)

    def choose(self,key):
        """Show a term's explanation; an indicator is also drawn on the chart."""
        if key not in glossary.BY_KEY and key not in BY_KEY:
            raise ValueError('Unknown guide term')
        self.focus=key
        if key in BY_KEY:self.keys=selection(set(self.keys)|{key})
        self.render()

    def remove(self,key):
        self.keys=selection(set(self.keys)-{key})
        self.render()

    def toggle(self,key,checked):
        self.choose(key) if checked else self.remove(key)

    def clear_selection(self):
        self.keys=();self.focus=None;self.render()

    def _toggle_detail_chart(self):
        if self.focus in BY_KEY:
            self.remove(self.focus) if self.focus in self.keys else self.choose(self.focus)

    def _show_reading(self, key):
        """A tag's name: that study's card in 해석 (docked) or its explanation (embedded)."""
        self.choose(key)
        if self.docked:
            self.show_side(1)
            self.detail_timer.start(0)

    @staticmethod
    def clear_layout(layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()

    def _make_chip(self, spec):
        """A tag for a selected study: its name (shows the explanation) and × (removes it from the chart). Docked, the
        tag also carries a colour bar and the study's values at the reading date (draft_03_guide legend)."""
        # Name part shows the explanation; the × part removes it from the chart (U+00D7: the bundled font has no U+2715).
        chip=QFrame() if self.docked else QWidget();chip.setProperty('indicator',spec.key)
        row=QHBoxLayout(chip);row.setContentsMargins(0,0,0,0);row.setSpacing(2)
        chip.show_button=QPushButton();chip.show_button.setProperty('chip',True)
        chip.show_button.setStyleSheet('QPushButton { border-left: 4px solid '+spec.color+'; }')
        chip.show_button.clicked.connect(lambda checked=False,k=spec.key:self._show_reading(k))
        chip.remove_button=QPushButton('×');chip.remove_button.setProperty('chip',True)
        chip.remove_button.clicked.connect(lambda checked=False,k=spec.key:self.remove(k))
        chip.values=None
        if self.docked:
            from .indicator_picker import ColorBar
            from .stock_detail_style import label as sd_label, numbers
            _style(chip,guide='tag')
            row.setContentsMargins(8,0,0,0)
            chip.bar=ColorBar();chip.bar.setFixedHeight(26);row.addWidget(chip.bar)
            for button,role in ((chip.show_button,'tagName'),(chip.remove_button,'tagX')):
                button.setStyleSheet('');_style(button,chip=None,guide=role)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
            row.addWidget(chip.show_button);row.addWidget(chip.remove_button)
            chip.values=numbers(sd_label(selectable=True));chip.values.setProperty('guide','tagValues')
            chip.values.setMinimumHeight(26);chip.values.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            return chip
        row.addWidget(chip.show_button);row.addWidget(chip.remove_button)
        return chip

    def render(self,*unused):
        from .app import label,panel
        ctx=self.ctx
        old_date=self.series.dates[self.cursor] if self.series else None
        if self.case.currentData()=='market' and self.market_series:
            self.series=self.market_series;self.case_name='market'
            self.meta={'provider':self.series.source,'symbol':self.series.symbol,'interval':self.series.interval,'rights':'NOT_VERIFIED'}
        elif self.external:
            self.series=self.external;self.case_name='research'
            self.meta={'provider':self.series.source,'symbol':self.series.symbol,'rights':'NOT_VERIFIED'}
        else:
            self.case_name,self.series,self.meta=historical_case(self.keys,self.case.currentData() or 'auto')
        self.cursor=self.series.dates.index(old_date) if old_date in self.series.dates else len(self.series.dates)*2//3
        ko=ctx.language=='ko'
        self.intro.setText(self.intro_text())
        self.steps.setText('① 지표 선택   →   ② 차트 위 날짜 이동   →   ③ 신호와 한계 비교' if ko else
                           '1 Choose indicators   →   2 Move across dates   →   3 Compare signals and limitations')
        if not self.docked:
            self.selection_title.setText('기술지표 27 · 함께 비교하기' if ko else '27 indicators · Choose several')
        for key,button in self.categories.items():
            button.setText(('전체' if ko else 'All') if key=='all' else CATEGORY_NAMES[key][0 if ko else 1])
            button.setChecked(key==self.category)
        for spec in INDICATORS:
            button=self.options[spec.key]
            info=study(spec.key);copy=study_guide.short_guide(spec.key,ctx.language)
            button.setText(info.name(ctx.language) if ko else info.label('en'))
            button.setAccessibleName(info.name(ctx.language));button.setAccessibleDescription(copy.one_liner)
            button.blockSignals(True);button.setChecked(spec.key in self.keys);button.blockSignals(False)
            button.setToolTip(info.name(ctx.language)+' · '+copy.one_liner);button.update()
        self.terms_title.setText('다른 투자 용어도 알아보세요' if ko else 'Explore other investing concepts')
        self.terms.setAccessibleName(self.terms_title.text())
        for i in range(self.terms.count()):
            key=self.terms.itemData(i)
            self.terms.setItemText(i,glossary.category(key,ctx)+' · '+glossary.name(key,ctx))
        self.detail_more.setText('자세한 해설과 주의점' if ko else 'Full explanation and limitations')
        self.selected_label.setText(ctx.t('chart_selection'));self.selected_label.setVisible(bool(self.keys) and not self.docked)
        self.clear.setText(ctx.t('clear_selection'));self.clear.setVisible(bool(self.keys))
        for key in [k for k in self.chips if k not in self.keys]:
            chip=self.chips.pop(key)
            for part in (chip,chip.values):
                if part is not None:self.chip_row.removeWidget(part);part.hide();part.deleteLater()
        for spec in INDICATORS:
            if spec.key not in self.keys:continue
            chip=self.chips.get(spec.key)
            if chip is None:
                chip=self._make_chip(spec)
                self.chips[spec.key]=chip
            if self.chip_row.indexOf(chip)<0:
                self.chip_row.addWidget(chip)
                if chip.values is not None:self.chip_row.addWidget(chip.values)
            name=study(spec.key).name(ctx.language)
            from core.market.presentation import study_colors
            from core.theme import LIGHT
            colors=getattr(self.window(),'colors',LIGHT)
            color=next(iter(study_colors(spec.key,colors.bg!=LIGHT.bg).values()))
            if self.docked:
                chip.bar.set_color(color)
            else:
                chip.show_button.setStyleSheet('QPushButton { border-left: 3px solid '+color+'; }')
            chip.show_button.setText(study(spec.key).short if ko else study(spec.key).label('en'))
            chip.show_button.setToolTip(name);chip.show_button.setAccessibleName(name)
            chip.show_button.setProperty('current',spec.key==self.focus)
            if self.docked:_style(chip.show_button)
            chip.remove_button.setToolTip(ctx.t('remove_from_chart')+' · '+name)
            chip.remove_button.setAccessibleName(ctx.t('remove_from_chart')+' · '+name)
        self.chip_host.setVisible(bool(self.keys))
        self._render_detail()
        self.case.setAccessibleName(ctx.t('sample'))
        self.case.blockSignals(True)
        for i,key in enumerate(('auto','2020','2022','2019')):self.case.setItemText(i,ctx.t('auto_sample' if key=='auto' else 'sample_'+key))
        if self.market_series:
            self.case.setItemText(self.case.findData('market'),('최근 조회한 시장 차트 · ' if ko else
                                 'Last observed market chart · ')+self.market_series.symbol)
        self.case.blockSignals(False)
        self.why.setText(('실제 시장에서 조회한 같은 종목·기간을 비교합니다.' if ko else 'Compare the same observed instrument and period.')
            if self.case_name=='market' else ctx.t('why_sample')+' · '+ctx.t('why_'+self.case_name))
        self.source.setText((ctx.t('historical_source') if self.case_name not in ('research','market') else self.series.source)
            +'\n'+self.series.symbol+' · '+ctx.date(self.series.dates[0])+' → '+ctx.date(self.series.dates[-1]))
        self.slider.blockSignals(True);self.slider.setRange(0,len(self.series.closes)-1)
        self.slider.setValue(self.cursor);self.slider.setAccessibleName(ctx.t('cursor'));self.slider.blockSignals(False)
        self.ohlcv_notice.setText(ctx.t('no_ohlcv_close' if self.external else 'no_ohlcv') if not self.series.ohlc else '')
        self.ohlcv_notice.setVisible(bool(self.ohlcv_notice.text()) or not self.docked)
        self.line_styles.setText(('같은 지표는 선택 표시와 차트에서 같은 색으로 표시합니다.' if ko else
                                 'Selected indicators use matching colours on the chart.') if self.keys else '')
        self.combination.setText(ctx.t('combination')+'\n'+ctx.t('combination_text') if len(self.keys)>1 else ctx.t('search_no_selection') if not self.keys else '')
        self.fail_title.setText(ctx.t('failed_signals'));self.fail_note.setText(ctx.t('failure_note'))
        covered=any(key in ('sma','ema','rsi','macd','bb') for key in self.keys)
        self.fail_title.setVisible(covered);self.fail_note.setVisible(covered)
        self.clear_layout(self.event_layout)
        self.events=counterexamples(self.series,self.keys)
        for event in (sorted(self.events,key=lambda e:e['index']) if self.docked else self.events):
            b=QPushButton(ctx.t('event',date=ctx.date(event['date']),indicator=ctx.t(event['indicator']),change=ctx.percent(event['change'])))
            b.clicked.connect(lambda checked=False,i=event['index']:self.move_cursor(i));self.event_layout.addWidget(b)
            if self.docked:
                b.setAccessibleName(b.text());b.setProperty('eventIndex',event['index'])
                _style(b,kit='chip');b.setCursor(Qt.CursorShape.PointingHandCursor)
        # With nothing selected the reading column already says so once.
        if not self.events and covered:
            empty=label(ctx.t('no_events'),'muted')
            if self.docked:_style(empty,role=None,guide='note')
            self.event_layout.addWidget(empty)
        self.export.setText(ctx.t('report'));self.notice.setText(ctx.t('education_only'))
        self._docked_render()
        self.move_cursor(self.cursor)

    def _render_detail(self):
        key=self.focus
        self.detail.setVisible(key is not None)
        if key is None:return
        self.detail.setStyleSheet('')
        if self.docked:
            self.detail.set_variant('side' if key in BY_KEY else 'page')
        self._fill_explanation(self.detail,key)

    def move_cursor(self,index):
        self.cursor=max(0,min(len(self.series.closes)-1,int(index)))
        self.chart.set_chart(self.series,self.keys,self.ctx,self.cursor)
        self.readout.setText(cursor_text(self.series,self.keys,self.cursor,self.ctx))
        if not self.docked:   # docked, the 해석 cards carry each reading and the foot the combined line
            self.combination.setText(reading_text(self.series,self.keys,self.cursor,self.ctx) if self.keys else ('위에서 지표를 선택하면 이 날짜의 신호를 함께 읽을 수 있어요.' if self.ctx.language=='ko' else 'Choose an indicator above to read its signal at this date.'))
        self.slider.blockSignals(True);self.slider.setValue(self.cursor);self.slider.blockSignals(False)
        self._docked_cursor()

    def save_report(self):
        from core.research.export import save_desktop_export
        path,_=QFileDialog.getSaveFileName(self,self.ctx.t('report'),'quantgen-indicator-guide.zip','Report (*.zip)')
        if not path:return
        try:
            data=learning_bundle(self.series,self.keys,self.meta,case_name=self.case_name,locale=self.ctx,cursor=self.cursor)
            save_desktop_export(path,data,extension='zip')
        except (OSError,ValueError,TypeError):self.notice.setText(self.ctx.t('save_failed'));return
        self.notice.setText(self.ctx.t('saved'))
