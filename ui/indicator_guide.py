"""Flet education/market explorer sharing the native chart, data and terminology."""
import base64
import re
import flet as ft

from core.theme import active
from core.i18n import LocaleContext
from core.education.indicators import INDICATORS, selection, historical_case, counterexamples, from_history
from core.education.chart import chart_svg, cursor_text, learning_bundle


class IndicatorGuide(ft.Column):
    def __init__(self,page,*,history=None):
        super().__init__(spacing=14,horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self.host_page=page;self.ctx=getattr(page,'qg_locale',LocaleContext())
        self.keys=();self.requested_case='auto';self.series=None;self.cursor=0
        self.external=from_history(history) if history else None
        self.mounted=False;self.render()

    def did_mount(self):self.mounted=True
    def will_unmount(self):self.mounted=False

    def render_locale(self,ctx):
        self.ctx=ctx;self.render()

    def update_if_mounted(self):
        if self.mounted:self.update()

    def toggle(self,key):
        keys=set(self.keys)
        keys.discard(key) if key in keys else keys.add(key)
        self.keys=selection(keys);self.render();self.update_if_mounted()

    def clear_selection(self,e=None):
        self.keys=();self.render();self.update_if_mounted()

    def choose_case(self,e):
        self.requested_case=e.control.value;self.render();self.update_if_mounted()

    def move_cursor(self,index):
        self.cursor=max(0,min(len(self.series.closes)-1,int(float(index))))
        self.readout.value=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        self.slider.value=self.cursor
        self.draw_chart()
        self.update_if_mounted()

    def draw_chart(self):
        svg=chart_svg(self.series,self.keys,locale=self.ctx,colors=active(),width=self.chart_width,cursor=self.cursor)
        self.image.src='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
        self.image.tooltip=cursor_text(self.series,self.keys,self.cursor,self.ctx)
        self.image.semantics_label=self.ctx.t('guide')+' · '+self.series.symbol

    async def download(self,e=None):
        try:
            data=learning_bundle(self.series,self.keys,self.meta,case_name=self.case_name,locale=self.ctx,cursor=self.cursor)
            filename=await ft.FilePicker().save_file(file_name='quantgen-indicator-guide.zip',
                file_type=ft.FilePickerFileType.CUSTOM,allowed_extensions=['zip'],src_bytes=data)
            if filename and not self.host_page.web and not self.host_page.platform.is_mobile():
                import asyncio
                from core.research.export import save_desktop_export
                await asyncio.to_thread(save_desktop_export,filename,data,extension='zip')
        except Exception:
            self.notice.value=self.ctx.t('save_failed');self.update_if_mounted()

    def render(self):
        ctx=self.ctx;pal=active()
        def text(value,size=14,muted=False):return ft.Text(value,size=size,color=pal.muted if muted else pal.text,selectable=True)
        old_date=self.series.dates[self.cursor] if self.series else None
        if self.external:
            self.series=self.external;self.case_name='research'
            self.meta={'provider':self.series.source,'symbol':self.series.symbol,'rights':'NOT_VERIFIED'}
        else:self.case_name,self.series,self.meta=historical_case(self.keys,self.requested_case)
        self.cursor=self.series.dates.index(old_date) if old_date in self.series.dates else len(self.series.dates)*2//3
        buttons=[]
        for spec in INDICATORS:
            selected=spec.key in self.keys
            button=ft.Button(ft.Row([
                ft.Text(spec.letter,color=spec.color,weight=ft.FontWeight.BOLD,size=15),
                ft.Text(ctx.t(spec.key),expand=True,size=13,color=pal.text),
                ft.Icon(ft.Icons.CHECK_BOX_OUTLINED if selected else ft.Icons.CHECK_BOX_OUTLINE_BLANK,color=spec.color,size=18)
            ],spacing=8),on_click=lambda e,k=spec.key:self.toggle(k),
                tooltip=ctx.t(spec.key+'_meaning'),data={'indicator':spec.key,'selected':selected},
                style=ft.ButtonStyle(bgcolor=pal.accent_soft if selected else pal.surface,
                    side=ft.BorderSide(2 if selected else 1,spec.color if selected else pal.border),
                    padding=12,shape=ft.RoundedRectangleBorder(radius=10)))
            buttons.append(ft.Container(button,col={'xs':12,'sm':6,'lg':4}))
        selected_chips=[ft.Chip(label=text(ctx.t(spec.key),12),on_delete=lambda e,k=spec.key:self.toggle(k))
                        for spec in INDICATORS if spec.key in self.keys]
        self.chart_width=max(350,min(1100,int((getattr(self.host_page,'width',None) or 1000)-(360 if (getattr(self.host_page,'width',None) or 1000)>=700 else 64))))
        svg=chart_svg(self.series,self.keys,locale=ctx,colors=pal,width=self.chart_width,cursor=self.cursor)
        height=int(re.search(r'height="(\d+)"',svg).group(1))
        self.image=ft.Image(src='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode(),
            fit=ft.BoxFit.CONTAIN,width=self.chart_width,height=height,
            semantics_label=ctx.t('guide')+' · '+self.series.symbol,
            tooltip=cursor_text(self.series,self.keys,self.cursor,ctx))
        self.readout=text(cursor_text(self.series,self.keys,self.cursor,ctx),12)
        self.slider=ft.Slider(min=0,max=len(self.series.closes)-1,divisions=len(self.series.closes)-1,
                              value=self.cursor,on_change=lambda e:self.move_cursor(e.control.value),tooltip=ctx.t('cursor'))
        controls=[text(ctx.t('guide_intro')),text(ctx.t('guide_steps'),12,True),
            text(ctx.t('select_indicators'),17),ft.ResponsiveRow(buttons,spacing=10,run_spacing=10),
            ft.Row([text(ctx.t('selected_count',count=len(self.keys)),12,True),
                    ft.TextButton(ctx.t('clear_selection'),on_click=self.clear_selection)],wrap=True),
            *([ft.Row(selected_chips,wrap=True)] if selected_chips else [])]
        if not self.external:
            controls.append(ft.Dropdown(label=ctx.t('sample'),value=self.requested_case,
                options=[ft.dropdown.Option(key,ctx.t('auto_sample' if key=='auto' else 'sample_'+key)) for key in ('auto','2020','2022','2019')],
                on_select=self.choose_case))
        controls += [text(ctx.t('why_sample')+' · '+ctx.t('why_'+self.case_name),12,True),
            text((ctx.t('historical_source') if not self.external else self.series.source)+'\n'+self.series.symbol+' · '+ctx.date(self.series.dates[0])+' → '+ctx.date(self.series.dates[-1]),11,True),
            self.image,self.readout,self.slider,
            text(ctx.t('no_ohlcv_close' if self.external else 'no_ohlcv'),12,True)]
        if len(self.keys)>1:controls += [text(ctx.t('combination'),17),text(ctx.t('combination_text'))]
        if not self.keys:controls.append(text(ctx.t('no_selection'),13,True))
        for spec in INDICATORS:
            if spec.key not in self.keys:continue
            items=[text(spec.letter+'  '+ctx.t(spec.key),17)]
            for field in ('meaning','look','interpret','limit'):
                items += [text(ctx.t(field),13,True),text(ctx.t(spec.key+'_'+field))]
            controls.append(ft.Container(ft.Column(items,spacing=10),padding=18,bgcolor=pal.surface_2,
                border=ft.Border.all(1,pal.border),border_radius=12))
        controls += [text(ctx.t('failed_signals'),17),text(ctx.t('failure_note'),12,True)]
        self.events=counterexamples(self.series,self.keys)
        controls += [ft.TextButton(ctx.t('event',date=ctx.date(e['date']),indicator=ctx.t(e['indicator']),change=ctx.percent(e['change'])),
                on_click=lambda event,i=e['index']:self.move_cursor(i)) for e in self.events]
        if self.keys and not self.events:controls.append(text(ctx.t('no_events'),12,True))
        self.notice=text(ctx.t('education_only'),12,True)
        controls += [ft.Button(ctx.t('report'),on_click=self.download,icon=ft.Icons.DOWNLOAD_OUTLINED),self.notice]
        self.controls=controls
