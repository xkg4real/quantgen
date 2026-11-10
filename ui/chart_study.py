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
        ft.Container(chart, col={'xs':12, 'xl':8}),
        ft.Container(reading, col={'xs':12, 'xl':4}),
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


READING_KEYS=('meaning','look','interpret','limit')


def _language(ctx):
    return 'ko' if getattr(ctx,'language','en')=='ko' else 'en'


def _close(figure):
    import matplotlib.pyplot as plt
    plt.close(figure)


class FigureStudy(ft.Column):
    """A chart image beside its reading panel.

    The panel uses chart-specific guidance when the figure carries `_qg_reading`
    ({'meaning'|'look'|'interpret'|'limit': (Korean, English)}); otherwise it falls back to
    the figure's own title, axis labels and legend. With `factory(ctx) -> figure` the chart
    itself is redrawn in the page language when the locale changes (same data, same palette).
    """
    def __init__(self, figure, *, expand=True, factory=None):
        super().__init__(spacing=12, expand=expand)
        self.factory=factory
        self.palette=getattr(figure,'_qg_palette',active())
        self.ctx=LocaleContext()
        self.figure_language=getattr(figure,'_qg_language',None)
        self.image=ft.Image(src='',fit=ft.BoxFit.CONTAIN,expand=True)
        self._use(figure)
        self.render_locale(self.ctx)

    def _use(self, figure):
        self.figure=figure
        axes=[ax for ax in figure.axes if ax.get_label()!='<colorbar>']
        self.chart_title=' · '.join(filter(None,(ax.get_title(loc='left') or ax.get_title() for ax in axes)))
        self.axis_text=' · '.join(dict.fromkeys(x for ax in axes for x in (ax.get_xlabel(),ax.get_ylabel()) if x))
        legends=[ax.get_legend() for ax in axes if ax.get_legend()]+list(getattr(figure,'legends',()))
        self.legend_text=' · '.join(dict.fromkeys(text.get_text() for legend in legends for text in legend.get_texts()))
        self.reading=getattr(figure,'_qg_reading',None) or {}
        self.image.src=figure_image(figure)
        self.image.semantics_label=self.chart_title or 'QUANTGEN chart'

    @property
    def src(self):
        """Keep the inline-image inspection contract of the chart factories."""
        return self.image.src

    def _relocalise(self, language):
        """Redraw the figure in `language` through the factory; the current palette is kept."""
        try:
            fresh=self.factory(self.ctx)
        except Exception:                      # the chart already rendered once; keep it rather than fail
            return
        drawn=getattr(fresh,'_qg_palette',self.palette)
        if drawn!=self.palette:recolour_figure(fresh,drawn,self.palette)
        fresh._qg_palette=self.palette
        self.figure_language=language
        self._use(fresh)
        _close(fresh)

    def render_locale(self, ctx):
        self.ctx=ctx;p=self.palette
        language=_language(ctx)
        if self.factory is not None and language!=self.figure_language:
            self._relocalise(language)
        def text(value,size=13,muted=False,weight=None,literal=False):
            return ft.Text(value,size=size,color=p.muted if muted else p.text,selectable=True,weight=weight,
                           data={'qg_literal_value':True} if literal else None)
        fallback={'meaning':self.chart_title or ctx.t('chart_result'),
                  'look':self.axis_text or ctx.t('chart_axes'),
                  'interpret':self.legend_text or ctx.t('chart_compare'),
                  'limit':ctx.t('chart_limits')}
        details=[]
        for key in READING_KEYS:
            authored=self.reading.get(key)
            if authored:
                details.append((ctx.t(key),authored[0] if language=='ko' else authored[1],True))
            else:
                details.append((ctx.t(key),fallback[key],False))
        reading=ft.Container(ft.Column([ft.Column([text(f'{i:02}  {heading}',12,True,ft.FontWeight.W_600),
                                                   text(body,literal=literal)],spacing=6)
            for i,(heading,body,literal) in enumerate(details,1)],spacing=18),padding=18,
            bgcolor=p.surface_2,border=ft.Border.all(1,p.border),border_radius=12)
        self.controls=[study_row(self.image,reading)]

    def render_theme(self, palette):
        if palette==self.palette:return
        recolour_figure(self.figure,self.palette,palette)
        self.palette=palette
        self.figure._qg_palette=palette
        self.image.src=figure_image(self.figure)
        self.render_locale(self.ctx)
