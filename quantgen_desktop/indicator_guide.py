"""Native reference indicator guide and reusable market-history explorer."""
from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QComboBox,
                            QPushButton,QSlider,QFileDialog,QTabWidget,QSizePolicy,QLayout)

from core.i18n import LocaleContext
from core.education.indicators import INDICATORS, historical_case, counterexamples, from_history, selection
from core.education.chart import chart_svg, cursor_text, reading_text, learning_bundle, plot_bounds


class TechnicalChart(QSvgWidget):
    cursor_changed=pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.series=None;self.keys=();self.ctx=LocaleContext();self.cursor=0
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumWidth(350)

    def set_chart(self, series, keys, ctx, cursor):
        changed=self.series is not series or self.keys!=tuple(keys) or self.ctx!=ctx
        self.series,self.keys,self.ctx,self.cursor=series,tuple(keys),ctx,int(cursor)
        if changed:self.redraw()
        else:self.update()
        description=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        self.setAccessibleDescription(description);self.setToolTip(description)

    def redraw(self):
        if self.series is None:return
        from core.theme import LIGHT
        colors=getattr(self.window(),'colors',LIGHT)
        svg=chart_svg(self.series,self.keys,locale=self.ctx,colors=colors,width=self.width())
        self.load(QByteArray(svg.encode()))
        self.setFixedHeight(int(self.renderer().viewBoxF().height()))
        description=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        self.setAccessibleName(self.ctx.t('guide')+' · '+self.series.symbol)
        self.setAccessibleDescription(description)
        self.setToolTip(description)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.redraw()

    def mouseMoveEvent(self,event):
        if self.series:
            left,right=plot_bounds(self.series,self.ctx,self.width())
            fraction=(event.position().x()-left)/max(1,right-left)
            self.cursor_changed.emit(max(0,min(len(self.series.closes)-1,round(fraction*(len(self.series.closes)-1)))))
        super().mouseMoveEvent(event)

    def paintEvent(self,event):
        super().paintEvent(event)
        if self.series is None:return
        from core.theme import LIGHT
        colors=getattr(self.window(),'colors',LIGHT)
        left,right=plot_bounds(self.series,self.ctx,self.width())
        x=left+(right-left)*self.cursor/max(1,len(self.series.closes)-1)
        columns=max(1,(self.width()-24)//210)
        import math
        top=12+math.ceil((len(self.keys)+1)/columns)*24+18
        painter=QPainter(self);painter.setPen(QPen(QColor(colors.muted),1,Qt.PenStyle.DashLine))
        painter.drawLine(round(x),top,round(x),self.height()-36)

    def keyPressEvent(self,event):
        if self.series and event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right,Qt.Key.Key_Home,Qt.Key.Key_End):
            at=(0 if event.key()==Qt.Key.Key_Home else len(self.series.closes)-1 if event.key()==Qt.Key.Key_End
                else self.cursor+(1 if event.key()==Qt.Key.Key_Right else -1))
            self.cursor_changed.emit(max(0,min(len(self.series.closes)-1,at)))
            event.accept();return
        super().keyPressEvent(event)


class IndicatorGuide(QWidget):
    def __init__(self, *, locale=None, history=None):
        super().__init__()
        from .app import label, panel
        self.ctx=locale or LocaleContext()
        self.keys=();self.external=from_history(history) if history else None
        self.series=None;self.cursor=0;self.meta={};self.case_name='2020'
        layout=QVBoxLayout(self);layout.setContentsMargins(0,12,0,0);layout.setSpacing(14)
        # The guide is embedded in a scroll page: long translated labels must
        # wrap within its viewport instead of setting the entire page width.
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.intro=label('');layout.addWidget(self.intro)
        self.steps=label('','caption');layout.addWidget(self.steps)
        box,inner=panel('')
        self.choose_label=label('','heading');inner.addWidget(self.choose_label)
        self.button_grid=QGridLayout();inner.addLayout(self.button_grid)
        self.buttons={}
        for i,spec in enumerate(INDICATORS):
            button=QPushButton();button.setCheckable(True)
            button.setProperty('indicator',spec.key)
            button.setStyleSheet('QPushButton { border-left: 4px solid '+spec.color+'; }')
            button.toggled.connect(lambda checked,k=spec.key:self.toggle(k,checked))
            self.buttons[spec.key]=button
            self.button_grid.addWidget(button,i//2,i%2)
        row=QHBoxLayout();self.selected_label=label('','caption');row.addWidget(self.selected_label,1)
        self.clear=QPushButton();self.clear.clicked.connect(self.clear_selection);row.addWidget(self.clear)
        inner.addLayout(row)
        self.case=QComboBox()
        for key in ('auto','2020','2022','2019'):self.case.addItem(key,key)
        self.case.currentIndexChanged.connect(self.render)
        self.case.setVisible(self.external is None);inner.addWidget(self.case)
        layout.addWidget(box)
        self.why=label('','muted');layout.addWidget(self.why)
        self.source=label('','caption');layout.addWidget(self.source)
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
        self.combination=label('');reading_layout.addWidget(self.combination)
        self.explanations=QTabWidget();reading_layout.addWidget(self.explanations)
        self.fail_title=label('','heading');reading_layout.addWidget(self.fail_title)
        self.fail_note=label('','caption');reading_layout.addWidget(self.fail_note)
        self.event_host=QWidget();self.event_layout=QVBoxLayout(self.event_host)
        self.event_layout.setContentsMargins(0,0,0,0);reading_layout.addWidget(self.event_host)
        reading_layout.addStretch()
        self.export=QPushButton();self.export.clicked.connect(self.save_report);layout.addWidget(self.export)
        self.notice=label('','caption');layout.addWidget(self.notice)
        self.render()

    def set_locale(self,ctx):
        self.ctx=ctx;self.render()

    def toggle(self,key,checked):
        chosen=set(self.keys)
        chosen.add(key) if checked else chosen.discard(key)
        self.keys=selection(chosen);self.render()

    def clear_selection(self):
        self.keys=()
        for button in self.buttons.values():
            button.blockSignals(True);button.setChecked(False);button.blockSignals(False)
        self.render()

    @staticmethod
    def clear_layout(layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()

    def render(self,*unused):
        from .app import label,panel
        ctx=self.ctx
        old_date=self.series.dates[self.cursor] if self.series else None
        if self.external:
            self.series=self.external;self.case_name='research'
            self.meta={'provider':self.series.source,'symbol':self.series.symbol,'rights':'NOT_VERIFIED'}
        else:
            self.case_name,self.series,self.meta=historical_case(self.keys,self.case.currentData() or 'auto')
        self.cursor=self.series.dates.index(old_date) if old_date in self.series.dates else len(self.series.dates)*2//3
        self.intro.setText(ctx.t('guide_intro'));self.steps.setText(ctx.t('guide_steps'))
        self.choose_label.setText(ctx.t('select_indicators'))
        for spec in INDICATORS:
            button=self.buttons[spec.key];button.setText(('✓  ' if spec.key in self.keys else '')+spec.letter+'  '+ctx.t(spec.key))
            button.setAccessibleName(ctx.t(spec.key));button.setToolTip(ctx.t(spec.key+'_meaning'))
        self.selected_label.setText(ctx.t('selected_count',count=len(self.keys)))
        self.clear.setText(ctx.t('clear_selection'))
        self.case.setAccessibleName(ctx.t('sample'))
        self.case.blockSignals(True)
        for i,key in enumerate(('auto','2020','2022','2019')):self.case.setItemText(i,ctx.t('auto_sample' if key=='auto' else 'sample_'+key))
        self.case.blockSignals(False)
        self.why.setText(ctx.t('why_sample')+' · '+ctx.t('why_'+self.case_name))
        self.source.setText((ctx.t('historical_source') if not self.external else self.series.source)
            +'\n'+self.series.symbol+' · '+ctx.date(self.series.dates[0])+' → '+ctx.date(self.series.dates[-1]))
        self.slider.blockSignals(True);self.slider.setRange(0,len(self.series.closes)-1)
        self.slider.setValue(self.cursor);self.slider.setAccessibleName(ctx.t('cursor'));self.slider.blockSignals(False)
        self.ohlcv_notice.setText(ctx.t('no_ohlcv_close' if self.external else 'no_ohlcv') if not self.series.ohlc else '')
        self.line_styles.setText(ctx.t('line_styles') if self.keys else '')
        self.combination.setText(ctx.t('combination')+'\n'+ctx.t('combination_text') if len(self.keys)>1 else ctx.t('no_selection') if not self.keys else '')
        focused=(
            self.explanations.currentWidget().property('indicator') if self.explanations.currentWidget() else None)
        while self.explanations.count():
            old=self.explanations.widget(0);self.explanations.removeTab(0);old.deleteLater()
        for spec in INDICATORS:
            if spec.key not in self.keys:continue
            box,inner=panel(spec.letter+'  '+ctx.t(spec.key))
            box.setStyleSheet('QFrame#panel { border-left: 4px solid '+spec.color+'; }')
            for field in ('meaning','look','interpret','limit'):
                inner.addWidget(label(ctx.t(field),'heading'))
                inner.addWidget(label(ctx.t(spec.key+'_'+field)))
            box.setProperty('indicator',spec.key)
            self.explanations.addTab(box,spec.letter+' '+spec.key.upper())
            if spec.key==focused:self.explanations.setCurrentWidget(box)
        self.fail_title.setText(ctx.t('failed_signals'));self.fail_note.setText(ctx.t('failure_note'))
        self.clear_layout(self.event_layout)
        self.events=counterexamples(self.series,self.keys)
        for event in self.events:
            b=QPushButton(ctx.t('event',date=ctx.date(event['date']),indicator=ctx.t(event['indicator']),change=ctx.percent(event['change'])))
            b.clicked.connect(lambda checked=False,i=event['index']:self.move_cursor(i));self.event_layout.addWidget(b)
        if not self.events:self.event_layout.addWidget(label(ctx.t('no_events') if self.keys else ctx.t('no_selection'),'muted'))
        self.export.setText(ctx.t('report'));self.notice.setText(ctx.t('education_only'))
        self.move_cursor(self.cursor)

    def move_cursor(self,index):
        self.cursor=max(0,min(len(self.series.closes)-1,int(index)))
        self.chart.set_chart(self.series,self.keys,self.ctx,self.cursor)
        self.readout.setText(cursor_text(self.series,self.keys,self.cursor,self.ctx))
        self.combination.setText(reading_text(self.series,self.keys,self.cursor,self.ctx) if self.keys else self.ctx.t('no_selection'))
        self.slider.blockSignals(True);self.slider.setValue(self.cursor);self.slider.blockSignals(False)

    def save_report(self):
        from core.research.export import save_desktop_export
        path,_=QFileDialog.getSaveFileName(self,self.ctx.t('report'),'quantgen-indicator-guide.zip','Report (*.zip)')
        if not path:return
        try:
            data=learning_bundle(self.series,self.keys,self.meta,case_name=self.case_name,locale=self.ctx,cursor=self.cursor)
            save_desktop_export(path,data,extension='zip')
        except (OSError,ValueError,TypeError):self.notice.setText(self.ctx.t('save_failed'));return
        self.notice.setText(self.ctx.t('saved'))
