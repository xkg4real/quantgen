"""The native guide uses all market studies, their calculations and their copy.

Bundled FX history contains reference closes only. OHLC/volume-dependent studies
remain selectable for learning but are never calculated from invented candles.
An observed market snapshot supplies its own OHLCV, interval and optional flows.
The original five-study web export API stays unchanged.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from html import escape
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import math

from core.i18n import LocaleContext
from core.theme import LIGHT
from . import indicators as I
from . import study_guide as G
from core.market.presentation import study_colors

ORDER = ('sma','ema','rsi','macd','bb') + tuple(s.key for s in I.STUDIES if s.key not in I.BY_KEY)
INDICATORS = tuple(I.Indicator(k, '', next(iter(study_colors(k).values())), I.study(k).panel,
                               tuple(line.id for line in I.study(k).lines)) for k in ORDER)
BY_KEY = {s.key:s for s in INDICATORS}


@dataclass(frozen=True)
class ObservedSeries(I.ChartSeries):
    interval: str = '1d'
    asset: str = ''
    supply: I.Supply | None = None
    snapshot: object = field(default=None,compare=False,hash=False)

    def validate(self):
        if self.snapshot is not None and self.interval.endswith('tick'):
            # Different received trades can share an exchange timestamp. Their
            # order is the snapshot's candle order, not invented subsecond times.
            if list(self.dates)!=sorted(self.dates):raise ValueError('Unordered trades')
            I.ChartSeries(self.symbol,tuple(range(len(self.dates))),self.closes,
                          self.source,self.unit,self.ohlc,self.volume).validate()
            return self
        return super().validate()


def from_snapshot(snapshot, supply=None):
    candles=snapshot.candles
    if len(candles)<2:raise ValueError('At least two observed bars are needed')
    volume=tuple(c.volume for c in candles)
    if any(v is None for v in volume):volume=()
    return ObservedSeries(snapshot.request.instrument.symbol,tuple(c.timestamp for c in candles),
        tuple(c.close for c in candles),snapshot.source,
        snapshot.quote.currency if snapshot.quote else 'price',
        tuple((c.open,c.high,c.low,c.close) for c in candles),volume,
        snapshot.request.interval,snapshot.request.instrument.asset,supply,snapshot).validate()


def selection(keys):
    keys=set(keys)
    if not keys<=set(BY_KEY):raise ValueError('Unknown study')
    return tuple(key for key in ORDER if key in keys)


def historical_case(keys=(), requested='auto'):
    return I.historical_case(tuple(k for k in selection(keys) if k in I.BY_KEY),requested)


def bars_for(series):
    if series.ohlc:
        return I.Bars(series.dates,*zip(*series.ohlc),series.volume,getattr(series,'interval','1d'))
    return I.bars_from_closes(series.closes,series.dates)


def missing_reason(series,key,language='ko'):
    spec=I.study(key)
    if spec.needs in ('ohlc','ohlcv','intraday') and not series.ohlc:
        return ('이 예시는 종가만 있어요. 시장에서 조회한 OHLC 차트를 선택하면 함께 볼 수 있어요.' if language=='ko' else
                'This example has closes only. Select an observed market chart to use its OHLC data.')
    reason=I.availability(key,asset=getattr(series,'asset',''),interval=getattr(series,'interval','1d'),
                          supply=getattr(series,'supply',None),has_volume=bool(series.volume))
    return G.availability_text(reason,language) if reason else ''


@lru_cache(maxsize=12)
def values_for(series, keys):
    bars=bars_for(series)
    return {key:I.compute_study(key,bars,supply=getattr(series,'supply',None))
            for key in keys if not missing_reason(series,key)}


def plot_bounds(series,ctx,width):
    return 18,max(350,int(width))-100


def chart_svg(series, keys=(), *, locale=None, colors=LIGHT, width=960, cursor=None):
    from core.market.presentation import chart_svg as market_chart_svg
    selected=selection(keys);ctx=locale or LocaleContext();dark=colors.bg!=LIGHT.bg
    snapshot=getattr(series,'snapshot',None)
    if snapshot is not None:
        return market_chart_svg(snapshot,indicators=selected,cursor=cursor,width=width,dark=dark,
                                visible=None,language=ctx.language,supply=getattr(series,'supply',None))
    series.validate();width=max(350,int(width));values=values_for(series,selected)
    lower=[k for k in selected if I.study(k).panel!='price']
    missing=[k for k in selected if k not in values]
    lower=[k for k in lower if k in values]
    columns=max(1,(width-24)//210);top=12+math.ceil((len(selected)+1)/columns)*24
    height=top+285+len(lower)*135+len(missing)*42+38
    left,right=plot_bounds(series,ctx,width)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<title>'+escape(ctx.t('guide')+' · '+series.symbol)+'</title>',
         f'<rect width="{width}" height="{height}" rx="12" fill="{colors.surface}"/>',
         '<g font-family="QG Interface" font-size="12">']
    def text(x,y,value,color=None,anchor='start'):
        out.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{color or colors.text}" text-anchor="{anchor}">{escape(str(value))}</text>')
    def line(x1,y1,x2,y2,color,stroke=1,dash=''):
        out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{stroke}" stroke-dasharray="{dash}"/>')
    legends=[(series.symbol,colors.text)]+[(I.study(k).label(ctx.language),next(iter(study_colors(k,dark).values()))) for k in selected]
    for at,(name,color) in enumerate(legends):
        x,y=14+at%columns*210,20+at//columns*24
        line(x,y-4,x+12,y-4,color,2);text(x+18,y,name,color)
    x=lambda i:left+(right-left)*i/max(1,len(series.closes)-1)
    for number,key in enumerate(('price',*lower)):
        ytop=top+22 if number==0 else top+285+(number-1)*135+22
        bottom=ytop+(235 if number==0 else 92)
        draws=[]
        if key=='price':
            draws=[(series.closes,colors.text,'solid')]
            for study in selected:
                if I.study(study).panel=='price' and study in values:
                    colors_by_line=study_colors(study,dark)
                    draws.extend((values[study][l.id],colors_by_line[l.id],l.style) for l in I.study(study).lines)
            title=('1달러당 유로' if ctx.language=='ko' else series.unit) if series.unit=='EUR per USD' else ('가격' if ctx.language=='ko' and series.unit=='price' else series.unit)
        else:
            spec=I.study(key);colors_by_line=study_colors(key,dark)
            draws=[(values[key][l.id],colors_by_line[l.id],l.style) for l in spec.lines]
            title=spec.name(ctx.language)
        raw=[float(v) for seq,_c,_s in draws for v in seq if math.isfinite(float(v))]
        bounds=I.study(key).bounds if key!='price' else ()
        if bounds:low,high=bounds
        elif raw:
            low,high=min(raw),max(raw);pad=max((high-low)*.08,abs(high)*.0001,.00001);low-=pad;high+=pad
        else:low,high=0,1
        y=lambda v:bottom-(float(v)-low)/max(high-low,1e-12)*(bottom-ytop)
        text(left,ytop-8,title,colors.muted)
        for i in range(4):
            value=low+(high-low)*i/3
            line(left,y(value),right,y(value),colors.border,.6)
            text(right+9,y(value)+4,ctx.number(value,4 if series.unit=='EUR per USD' and key=='price' else 2),colors.muted)
        if key!='price':
            for ref in I.study(key).references:
                if low<=ref<=high:line(left,y(ref),right,y(ref),colors.muted,.7,'4 4')
        for seq,color,style in draws:
            commands=[];connected=False
            for i,value in enumerate(seq):
                if not math.isfinite(float(value)):connected=False;continue
                if style=='bars':line(x(i),y(max(low,min(high,0))),x(i),y(value),color,2);continue
                commands.append(('L' if connected else 'M')+f'{x(i):.2f},{y(value):.2f}');connected=True
            if commands:out.append(f'<path d="{" ".join(commands)}" fill="none" stroke="{color}" stroke-width="1.6" stroke-dasharray="{"5 3" if style=="dash" else ""}"/>')
    offset=top+285+len(lower)*135
    for i,key in enumerate(missing):
        text(left,offset+i*42+17,I.study(key).name(ctx.language)+' · —',next(iter(study_colors(key,dark).values())))
        # Keep the full reason in the adjacent reading card / accessible text.
        short=('현재 예시에 필요한 자료가 없어요' if ctx.language=='ko' else 'Required data is absent from this example')
        text(left,offset+i*42+34,short,colors.muted)
    for i,anchor in ((0,'start'),(len(series.dates)//2,'middle'),(len(series.dates)-1,'end')):
        text(x(i),height-12,ctx.date(series.dates[i]),colors.muted,anchor)
    out.append('</g></svg>');return ''.join(out)


def cursor_text(series,keys,index,locale=None):
    ctx=locale or LocaleContext();at=max(0,min(len(series.closes)-1,int(index)))
    selected=selection(keys);values=values_for(series,selected)
    parts=[ctx.date(series.dates[at]),series.symbol+' '+ctx.number(series.closes[at],4 if series.unit=='EUR per USD' else 2)]
    for key in selected:
        for item in I.study(key).lines:
            value=values[key][item.id][at] if key in values else math.nan
            parts.append(item.name(ctx.language)+' '+(ctx.number(float(value),2) if math.isfinite(value) else '—'))
    return ' · '.join(parts)


def reading_text(series,keys,index,locale=None):
    from .signal_context import alignment_note
    from .reading_cues import reading_tip
    ctx=locale or LocaleContext();selected=selection(keys);values=values_for(series,selected);bars=bars_for(series)
    parts=[]
    for key in selected:
        missing=missing_reason(series,key,ctx.language)
        reading=missing or G.short_reading(key,bars,index,language=ctx.language,values=values.get(key),supply=getattr(series,'supply',None))
        note='' if missing else reading_tip(key,ctx.language)
        parts.append(I.study(key).name(ctx.language)+' · '+reading+('\n'+note if note else ''))
    difference=alignment_note(selected,bars,index,language=ctx.language,values=values)
    if difference:parts.append(difference)
    return '\n\n'.join(parts)


def counterexamples(series,keys,*,limit=4):
    return I.counterexamples(series,tuple(k for k in selection(keys) if k in I.BY_KEY),limit=limit)


def learning_bundle(series,keys,meta,*,case_name,locale=None,cursor=None):
    ctx=locale or LocaleContext();selected=selection(keys)
    body=['<!doctype html><html lang="'+ctx.language+'"><meta charset="utf-8"><title>QUANTGEN</title>',
          '<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:24px}svg{width:100%;height:auto}p{line-height:1.6}</style>',
          '<h1>'+escape(ctx.t('report_title'))+'</h1><p>'+escape(ctx.t('education_only'))+'</p>',
          '<p>'+escape(series.symbol+' · '+series.source+' · '+series.dates[0]+' → '+series.dates[-1])+'</p>',
          chart_svg(series,selected,locale=ctx)]
    for key in selected:
        item=G.guide(key,ctx.language,getattr(series,'interval','1d'))
        body.append('<section><h2>'+escape(item.name)+'</h2>')
        for title,value in ((ctx.t('meaning'),item.what),(ctx.t('look'),item.how),(ctx.t('limit'),item.caution)):
            body.append('<h3>'+escape(title)+'</h3><p>'+escape(value)+'</p>')
        body.append('<p>'+escape(missing_reason(series,key,ctx.language))+'</p></section>')
    if cursor is not None:
        body.append('<p>'+escape(cursor_text(series,selected,cursor,ctx))+'</p>')
        body.append('<p>'+escape(reading_text(series,selected,cursor,ctx)).replace('\n','<br>')+'</p>')
    body.append('</html>')
    record={'format':'quantgen.study-education/2','selected_indicators':list(selected),'locale':str(ctx.locale),
            'case':case_name,'source':meta,'education_only':True,'verdict':'NOT_RUN',
            'input_sha256':hashlib.sha256(json.dumps(list(zip(series.dates,series.closes))).encode()).hexdigest()}
    files={'report.html':''.join(body).encode(),'education.json':json.dumps(record,ensure_ascii=False,indent=2).encode()}
    files['MANIFEST.json']=json.dumps({'format':record['format'],'files':{k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in files.items()}},indent=2).encode()
    out=BytesIO()
    with ZipFile(out,'w',ZIP_DEFLATED) as archive:
        for name,value in files.items():archive.writestr(name,value)
    return out.getvalue()
