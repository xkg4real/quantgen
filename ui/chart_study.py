"""Common C-format chart frame; keeps figure data and existing chart types."""
import base64
from io import BytesIO
import flet as ft
import numpy as np
from matplotlib.colors import to_rgba
from core.i18n import LocaleContext
from core.theme import active, token_names


def study_row(chart, reading):
    return ft.ResponsiveRow([
        ft.Container(chart, col={'xs':12, 'md':8}),
        ft.Container(reading, col={'xs':12, 'md':4}),
    ], spacing=18, run_spacing=18, vertical_alignment=ft.CrossAxisAlignment.START)


def figure_image(figure):
    buffer=BytesIO()
    figure.savefig(buffer, format='png', bbox_inches='tight', facecolor=figure.get_facecolor())
    return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode('ascii')


def recolour_figure(figure, old, new):
    """Change semantic paint only; values, limits, labels and colormaps stay intact."""
    pairs=[(np.asarray(to_rgba(getattr(old,key)))[:3],
            np.asarray(to_rgba(getattr(new,key)))[:3]) for key in token_names()]
    def mapped(value):
        try:
            rgba=np.asarray(to_rgba(value)) if isinstance(value,str) else np.asarray(value,dtype=float)
        except (TypeError,ValueError):return None
        if rgba.ndim not in (1,2) or rgba.shape[-1] not in (3,4):return None
        out=rgba.copy()
        for before,after in pairs:
            match=np.all(np.isclose(rgba[...,:3],before,atol=1e-6),axis=-1)
            if rgba.ndim==1:
                if match:out[:3]=after
            else:out[match,:3]=after
        return out if not np.array_equal(out,rgba) else None
    for artist in figure.findobj():
        for name in ('color','facecolor','edgecolor','markerfacecolor','markeredgecolor'):
            getter,setter=getattr(artist,'get_'+name,None),getattr(artist,'set_'+name,None)
            if not callable(getter) or not callable(setter):continue
            value=mapped(getter())
            if value is not None:setter(value)


class FigureStudy(ft.Column):
    def __init__(self, figure, *, expand=True):
        super().__init__(spacing=12, expand=expand)
        self.figure=figure
        self.palette=getattr(figure,'_qg_palette',active())
        self.ctx=LocaleContext()
        axes=[ax for ax in figure.axes if ax.get_label()!='<colorbar>']
        self.chart_title=' · '.join(filter(None,(ax.get_title(loc='left') or ax.get_title() for ax in axes)))
        self.axis_text=' · '.join(dict.fromkeys(x for ax in axes for x in (ax.get_xlabel(),ax.get_ylabel()) if x))
        self.legend_text=' · '.join(dict.fromkeys(text.get_text() for ax in axes if ax.get_legend() for text in ax.get_legend().get_texts()))
        self.image=ft.Image(src=figure_image(figure),fit=ft.BoxFit.CONTAIN,
            semantics_label=self.chart_title or 'QUANTGEN chart',expand=True)
        self.render_locale(self.ctx)

    @property
    def src(self):
        """Keep the inline-image inspection contract of the chart factories."""
        return self.image.src

    def render_locale(self, ctx):
        self.ctx=ctx;p=self.palette
        def text(value,size=13,muted=False):
            return ft.Text(value,size=size,color=p.muted if muted else p.text,selectable=True)
        details=[(ctx.t('meaning'),self.chart_title or ctx.t('chart_result')),
                 (ctx.t('look'),self.axis_text or ctx.t('chart_axes')),
                 (ctx.t('interpret'),self.legend_text or ctx.t('chart_compare')),
                 (ctx.t('limit'),ctx.t('chart_limits'))]
        reading=ft.Container(ft.Column([ft.Column([text(f'{i:02}  {heading}',12,True),text(body)],spacing=6)
            for i,(heading,body) in enumerate(details,1)],spacing=18),padding=18,
            bgcolor=p.surface_2,border=ft.Border.all(1,p.border),border_radius=12)
        self.controls=[study_row(self.image,reading)]

    def render_theme(self, palette):
        if palette==self.palette:return
        recolour_figure(self.figure,self.palette,palette)
        self.palette=palette
        self.image.src=figure_image(self.figure)
        self.render_locale(self.ctx)
