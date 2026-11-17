"""Per-page presentation translation; cached views and financial inputs survive."""
import flet as ft
from core.i18n import LocaleContext, locale_choices, numeric_presentation


def table_header(source, *, ko=None, **kwargs):
    """Authored column text; an optional Korean override is local to this table."""
    return ft.Text(source, data={'qg_table_header': {'source': source, 'ko': ko}}, **kwargs)


def literal_text(value, **kwargs):
    """A provider/calculation value whose displayed text must survive locale changes."""
    return ft.Text(value, data={'qg_literal_value': True}, **kwargs)


def translate_controls(root,ctx):
    visited=set()
    def visit(control):
        if not isinstance(control,ft.Control) or id(control) in visited:return
        visited.add(id(control))
        if callable(getattr(control,'render_locale',None)) and getattr(control,'ctx',None)!=ctx:control.render_locale(ctx)
        history=getattr(control,'_qg_translation',{})
        fields=['tooltip','hint_text','helper_text']
        if isinstance(control,ft.Text):fields+=['value']
        if isinstance(control,(ft.Button,ft.TextButton,ft.OutlinedButton)):fields+=['content']
        if isinstance(control,ft.dropdown.Option):fields+=['text']
        fields+=['label']
        for field in fields:
            value=getattr(control,field,None)
            if not isinstance(value,str):continue
            data=getattr(control,'data',None)
            if isinstance(control,ft.Text) and field=='value' and isinstance(data,dict):
                if data.get('qg_literal_value') is True:continue
                header=data.get('qg_table_header')
                if isinstance(header,dict):
                    source=header['source']
                    translated=(header['ko'] if ctx.language=='ko' and header.get('ko') is not None
                                else ctx.text(source))
                    control.value=translated;history[field]=(source,translated)
                    continue
            source,last=history.get(field,(value,None))
            if value!=last:source=value
            translated=ctx.text(source)
            if isinstance(control,ft.Text) and field=='value' and getattr(control,'data',None)=={'numeric':True}:
                translated=numeric_presentation(translated,ctx)
            setattr(control,field,translated);history[field]=(source,translated)
        control._qg_translation=history
        for field in ('controls','content','title','subtitle','actions','leading','trailing',
                      'label','rows','cells','columns','tabs','options','destinations'):
            value=getattr(control,field,None)
            if isinstance(value,(list,tuple)):
                for child in value:visit(child)
            else:visit(value)
    visit(root)


class LocalizedRoot(ft.Row):
    def __init__(self,page,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.host_page=page

    def before_update(self):
        from core.theme import set_mode
        from .theme_controller import apply_palette
        apply_palette(self,set_mode(getattr(self.host_page,'qg_theme','light')))
        translate_controls(self,getattr(self.host_page,'qg_locale',LocaleContext()))


class LanguageSettings(ft.Column):
    def __init__(self,page):
        super().__init__(spacing=10)
        self.host_page=page;self.render_locale(getattr(page,'qg_locale',LocaleContext()))

    def choose(self,e):
        callback=getattr(self.host_page,'qg_change_locale',None)
        if callback:callback(e.control.value)

    def render_locale(self,ctx):
        self.ctx=ctx
        priority=[('ko_KR','한국어 · 대한민국'),('en_US','English · United States')]
        choices=priority+[(k,n) for k,n in locale_choices() if k not in {'ko_KR','en_US'}]
        self.controls=[ft.Text(ctx.t('language'),size=17,weight=ft.FontWeight.W_600),
            ft.Dropdown(label=ctx.t('language'),value=str(ctx.locale),
                options=[ft.dropdown.Option(k,n) for k,n in choices],
                editable=True,enable_filter=True,menu_height=320,on_select=self.choose,
                data={'locale_picker':True}),
            ft.Text(ctx.t('language_fallback' if ctx.is_fallback else 'language_coverage'),size=12)]
