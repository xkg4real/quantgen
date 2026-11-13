"""Native reference indicator guide and reusable market-history explorer."""
from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QPushButton,QSlider,
                            QFileDialog,QSizePolicy,QLayout)

from core.i18n import LocaleContext
from core.education import glossary
from core.education.indicators import INDICATORS, BY_KEY, historical_case, counterexamples, from_history, selection
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
    """Visible multiple choices and one shared historical chart; no search required."""

    def __init__(self, *, locale=None, history=None):
        super().__init__()
        from .app import label, panel
        self.ctx=locale or LocaleContext()
        self.keys=();self.external=from_history(history) if history else None
        self.series=None;self.cursor=0;self.meta={};self.case_name='2020'
        self.focus=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,12,0,0);layout.setSpacing(14)
        # The guide is embedded in a scroll page: long translated labels must
        # wrap within its viewport instead of setting the entire page width.
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.intro=label('');layout.addWidget(self.intro)
        self.steps=label('','caption');layout.addWidget(self.steps)
        box,inner=panel('')
        from .choice_cards import ChoiceCard, ChoiceGrid
        self.selection_title=label('', 'heading');inner.addWidget(self.selection_title)
        self.options={}
        for spec in INDICATORS:
            button=ChoiceCard();button.swatch=spec.color
            button.clicked.connect(lambda checked,k=spec.key:self.toggle(k,checked))
            self.options[spec.key]=button
        self.choices=ChoiceGrid(self.options.values());inner.addWidget(self.choices)
        selected=QHBoxLayout()
        self.selected_label=label('', 'caption');selected.addWidget(self.selected_label,1)
        self.clear=QPushButton();self.clear.clicked.connect(self.clear_selection);selected.addWidget(self.clear)
        inner.addLayout(selected)
        from .category_picker import CategoryFlow
        self.chip_host=QWidget();self.chip_row=CategoryFlow(self.chip_host)
        inner.addWidget(self.chip_host);self.chips={}
        self.case=QComboBox()
        for key in ('auto','2020','2022','2019'):self.case.addItem(key,key)
        self.case.currentIndexChanged.connect(self.render)
        self.case.setVisible(self.external is None);inner.addWidget(self.case)
        layout.addWidget(box)
        self.detail,detail_layout=panel('');self.detail.hide()
        head=QHBoxLayout()
        title_column=QVBoxLayout();title_column.setSpacing(2)
        self.detail_title=label('','heading');title_column.addWidget(self.detail_title)
        self.detail_category=label('','caption');title_column.addWidget(self.detail_category)
        head.addLayout(title_column,1)
        self.detail_chart=QPushButton();self.detail_chart.clicked.connect(self._toggle_detail_chart)
        head.addWidget(self.detail_chart,0,Qt.AlignmentFlag.AlignTop)
        detail_layout.addLayout(head)
        self.detail_sections=[]
        for _ in range(4):
            heading=label('','heading');body=label('')
            detail_layout.addWidget(heading);detail_layout.addWidget(body)
            self.detail_sections.append((heading,body))
        self.detail_summary=label('');detail_layout.insertWidget(1,self.detail_summary)
        self.detail_body=QWidget();body_layout=QVBoxLayout(self.detail_body)
        body_layout.setContentsMargins(0,0,0,0)
        for heading,body in self.detail_sections:
            detail_layout.removeWidget(heading);detail_layout.removeWidget(body)
            body_layout.addWidget(heading);body_layout.addWidget(body)
        self.detail_more=QPushButton();self.detail_more.setCheckable(True)
        self.detail_more.toggled.connect(self.detail_body.setVisible)
        detail_layout.addWidget(self.detail_more,0,Qt.AlignmentFlag.AlignLeft)
        detail_layout.addWidget(self.detail_body);self.detail_body.hide()
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
        self.terms_title=label('', 'heading');terms_layout.addWidget(self.terms_title)
        self.terms=QComboBox();self.terms.setEditable(False)
        for term in glossary.TERMS:
            if term.key not in BY_KEY:self.terms.addItem('',term.key)
        self.terms.activated.connect(lambda i:self.choose(self.terms.itemData(i)))
        terms_layout.addWidget(self.terms);layout.addWidget(terms)
        self.export=QPushButton();self.export.clicked.connect(self.save_report)
        layout.addWidget(self.export,0,Qt.AlignmentFlag.AlignLeft)
        self.notice=label('','caption');layout.addWidget(self.notice)
        self.render()

    def set_locale(self,ctx):
        self.ctx=ctx
        self.render()

    def intro_text(self):
        return ('지표를 골라 차트에서 확인해 보세요. 여러 개를 선택하면 같은 기간의 신호를 함께 비교할 수 있어요.'
                if self.ctx.language=='ko' else
                'Choose an indicator and see it on the chart. Select more than one to compare signals over the same period.')

    def choose(self,key):
        """Show a term's explanation; an indicator is also drawn on the chart."""
        if key not in glossary.BY_KEY:
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
        ko=ctx.language=='ko'
        self.intro.setText(self.intro_text())
        self.steps.setText('① 지표 선택   →   ② 차트 위 날짜 이동   →   ③ 신호와 한계 비교' if ko else
                           '1 Choose indicators   →   2 Move across dates   →   3 Compare signals and limitations')
        self.selection_title.setText('어떤 흐름이 궁금한가요? · 복수 선택' if ko else 'What would you like to see? · Choose several')
        purposes={
            'sma':('가격의 큰 방향','The broader price trend'),
            'ema':('최근 가격 변화에 빠르게 반응','Responds faster to recent prices'),
            'rsi':('최근 상승과 하락의 강도','The strength of recent gains and losses'),
            'macd':('추세의 힘이 바뀌는 구간','Changes in trend momentum'),
            'bb':('평소보다 커지거나 줄어든 변동','Expanding and contracting volatility')}
        for spec in INDICATORS:
            button=self.options[spec.key]
            button.set_copy(ctx.t(spec.key),purposes[spec.key][0 if ko else 1])
            button.blockSignals(True);button.setChecked(spec.key in self.keys);button.blockSignals(False)
            button.setToolTip(glossary.summary(spec.key,ctx));button.update()
        self.terms_title.setText('다른 투자 용어도 알아보세요' if ko else 'Explore other investing concepts')
        self.terms.setAccessibleName(self.terms_title.text())
        for i in range(self.terms.count()):
            key=self.terms.itemData(i)
            self.terms.setItemText(i,glossary.category(key,ctx)+' · '+glossary.name(key,ctx))
        self.detail_more.setText('자세한 해설과 주의점' if ko else 'Full explanation and limitations')
        self.selected_label.setText(ctx.t('chart_selection'));self.selected_label.setVisible(bool(self.keys))
        self.clear.setText(ctx.t('clear_selection'));self.clear.setVisible(bool(self.keys))
        for key in [k for k in self.chips if k not in self.keys]:
            chip=self.chips.pop(key);self.chip_row.removeWidget(chip);chip.hide();chip.deleteLater()
        for spec in INDICATORS:
            if spec.key not in self.keys:continue
            chip=self.chips.get(spec.key)
            if chip is None:
                # Name part shows the explanation; the × part removes it from the chart (U+00D7: the bundled font has no U+2715).
                chip=QWidget();chip.setProperty('indicator',spec.key)
                row=QHBoxLayout(chip);row.setContentsMargins(0,0,0,0);row.setSpacing(2)
                chip.show_button=QPushButton();chip.show_button.setProperty('chip',True)
                chip.show_button.setStyleSheet('QPushButton { border-left: 4px solid '+spec.color+'; }')
                chip.show_button.clicked.connect(lambda checked=False,k=spec.key:self.choose(k))
                chip.remove_button=QPushButton('×');chip.remove_button.setProperty('chip',True)
                chip.remove_button.clicked.connect(lambda checked=False,k=spec.key:self.remove(k))
                row.addWidget(chip.show_button);row.addWidget(chip.remove_button)
                self.chips[spec.key]=chip
            if self.chip_row.indexOf(chip)<0:self.chip_row.addWidget(chip)
            chip.show_button.setText(spec.letter+'  '+spec.key.upper())
            chip.show_button.setToolTip(ctx.t(spec.key));chip.show_button.setAccessibleName(ctx.t(spec.key))
            chip.show_button.setProperty('current',spec.key==self.focus)
            chip.remove_button.setToolTip(ctx.t('remove_from_chart')+' · '+ctx.t(spec.key))
            chip.remove_button.setAccessibleName(ctx.t('remove_from_chart')+' · '+ctx.t(spec.key))
        self.chip_host.setVisible(bool(self.keys))
        self._render_detail()
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
        self.combination.setText(ctx.t('combination')+'\n'+ctx.t('combination_text') if len(self.keys)>1 else ctx.t('search_no_selection') if not self.keys else '')
        self.fail_title.setText(ctx.t('failed_signals'));self.fail_note.setText(ctx.t('failure_note'))
        self.fail_title.setVisible(bool(self.keys));self.fail_note.setVisible(bool(self.keys))
        self.clear_layout(self.event_layout)
        self.events=counterexamples(self.series,self.keys)
        for event in self.events:
            b=QPushButton(ctx.t('event',date=ctx.date(event['date']),indicator=ctx.t(event['indicator']),change=ctx.percent(event['change'])))
            b.clicked.connect(lambda checked=False,i=event['index']:self.move_cursor(i));self.event_layout.addWidget(b)
        # With nothing selected the reading column already says so once.
        if not self.events and self.keys:self.event_layout.addWidget(label(ctx.t('no_events'),'muted'))
        self.export.setText(ctx.t('report'));self.notice.setText(ctx.t('education_only'))
        self.move_cursor(self.cursor)

    def _render_detail(self):
        key,ctx=self.focus,self.ctx
        self.detail.setVisible(key is not None)
        if key is None:return
        spec=BY_KEY.get(key)
        self.detail.setStyleSheet('QFrame#panel { border-left: 4px solid '+spec.color+'; }' if spec else '')
        self.detail.setProperty('term',key)
        self.detail_title.setText((spec.letter+'  ' if spec else '')+glossary.name(key,ctx))
        self.detail_category.setText(glossary.category(key,ctx))
        self.detail_summary.setText(glossary.summary(key,ctx))
        self.detail_chart.setVisible(spec is not None)
        if spec is not None:
            self.detail_chart.setText(ctx.t('remove_from_chart' if key in self.keys else 'add_to_chart'))
        parts=glossary.sections(key,ctx)
        for i,(heading,body) in enumerate(self.detail_sections):
            shown=i<len(parts)
            heading.setVisible(shown);body.setVisible(shown)
            if shown:heading.setText(parts[i][0]);body.setText(parts[i][1])

    def move_cursor(self,index):
        self.cursor=max(0,min(len(self.series.closes)-1,int(index)))
        self.chart.set_chart(self.series,self.keys,self.ctx,self.cursor)
        self.readout.setText(cursor_text(self.series,self.keys,self.cursor,self.ctx))
        self.combination.setText(reading_text(self.series,self.keys,self.cursor,self.ctx) if self.keys else ('위에서 지표를 선택하면 이 날짜의 신호를 함께 읽을 수 있어요.' if self.ctx.language=='ko' else 'Choose an indicator above to read its signal at this date.'))
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
