"""Responsive source-usage inventory for the retained Flet browser."""
import flet as ft
from core.i18n import LocaleContext
from core.research.display_rights import display_rights,policy_detail
from core.theme import active


class DataRightsPanel(ft.Column):
    def __init__(self,page):
        super().__init__(spacing=12)
        self.ctx=getattr(page,'qg_locale',LocaleContext());self.record=display_rights();self.query=''
        self.search=ft.TextField(on_change=self.filter)
        self.entries=ft.Column(spacing=8)
        self.render_locale(self.ctx)

    def filter(self,e):
        self.query=e.control.value or '';self.render_entries();self.entries.update()

    def render_entries(self):
        ctx=self.ctx;pal=active();items=[]
        needle=self.query.casefold().strip()
        for group in ('home','registered_series'):
            items.append(ft.Text(ctx.t('rights_home' if group=='home' else 'rights_registry'),size=15,weight=ft.FontWeight.W_600))
            for row in self.record[group]:
                label=' · '.join((row['series_id'],row['source'],ctx.t(row['outcome'])))
                if needle and needle not in label.casefold():continue
                details=[ft.Column([ft.Text(title,size=12,color=pal.muted),ft.Text(value,size=13,selectable=True)],spacing=4)
                         for title,value in policy_detail(self.record,row,ctx)]
                items.append(ft.ExpansionTile(title=ft.Text(label,size=13),
                    subtitle=ft.Text(ctx.t('daily') if row['frequency']=='daily' else row['frequency'],size=11),
                    controls=[ft.Container(ft.Column(details,spacing=12),padding=16)]))
        self.entries.controls=items

    def render_locale(self,ctx):
        self.ctx=ctx;self.search.label=ctx.t('rights_search')
        self.render_entries()
        self.controls=[ft.Text(ctx.t('rights_intro')),ft.Text(ctx.t('rights_scope'),size=12),
                       self.search,self.entries,ft.Text(self.record['legal_review']['scope_'+ctx.language],size=12),
                       *[ft.Text(url,size=11,selectable=True) for url in self.record['legal_review']['sources']]]
