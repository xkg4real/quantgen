"""Shared vector chart grammar for Qt, Flet and offline education reports."""
from html import escape
import math
from io import BytesIO
import json
import hashlib
from zipfile import ZipFile, ZIP_DEFLATED

from core.i18n import LocaleContext
from core.theme import LIGHT
from .indicators import INDICATORS, BY_KEY, selection, indicator_values, counterexamples


def plot_bounds(series,ctx,width):
    largest=max(abs(v) for v in series.closes)*1.2
    labels=[ctx.number(largest,4 if series.unit=='EUR per USD' else 2)]
    if series.volume:labels.append(ctx.number(max(series.volume)*1.1,0))
    return max(76,max(map(len,labels))*7+18),width-20


def chart_svg(series, keys=(), *, locale=None, colors=LIGHT, width=960, cursor=None, chart_type='line'):
    """No scripts, external assets or inferred OHLC. All panels share x positions."""
    series.validate()
    selected = selection(keys)
    ctx = locale or LocaleContext()
    width = max(350,min(1800,int(width)))
    if chart_type not in {'line','candles'} or (chart_type=='candles' and not series.ohlc):
        raise ValueError('Observed OHLC bars required for candle view')
    values = indicator_values(series)
    panels = ['price'] + [k for k in ('rsi','macd') if k in selected]
    if series.volume: panels.append('volume')
    # Compact abbreviations are glossary terms, shared with the selection buttons.
    legends=[(series.symbol,colors.text)] + [(' / '.join(ctx.text(n) for n in BY_KEY[k].lines),BY_KEY[k].color) for k in selected]
    legend_rows=max(1,math.ceil(len(legends)/max(1,(width-24)//210)))
    top=12+legend_rows*24
    # Reserve measured-by-glyph-budget space for large prices and locale separators.
    left,right=plot_bounds(series,ctx,width)
    area=right-left
    height=top+280+(len(panels)-1)*145+42
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
           '<title>'+escape(ctx.t('guide')+' · '+series.symbol)+'</title>',
           '<desc>'+escape(ctx.t('education_only'))+'</desc>',
           f'<rect width="{width}" height="{height}" rx="12" fill="{colors.surface}"/>',
           '<g font-family="QG Interface,Noto Sans CJK KR,Segoe UI,sans-serif" font-size="12">']
    def text(x,y,value,color=None,anchor='start',size=12):
        parts.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{color or colors.text}" text-anchor="{anchor}" font-size="{size}">{escape(str(value))}</text>')
    def line(x1,y1,x2,y2,color,width=1,dash=''):
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    columns=max(1,(width-24)//210)
    for index,(name,color) in enumerate(legends):
        lx=14+(index%columns)*210;ly=20+(index//columns)*24
        line(lx,ly-4,lx+14,ly-4,color,2)
        visible=name if len(name)<=max(14,(width//columns-36)//7) else name[:max(11,(width//columns-36)//7)-1]+'…'
        text(lx+20,ly,visible,color,size=11)
    x=lambda i:left+area*i/max(1,len(series.closes)-1)
    index=max(0,min(len(series.closes)-1,int(cursor))) if cursor is not None else None
    for number,panel in enumerate(panels):
        ytop=top+20 if number==0 else top+280+(number-1)*145+20
        ybottom=ytop+(240 if number==0 else 104)
        if panel=='price':
            draws=[(list(series.closes),colors.text,2,'')]
            for key in selected:
                spec=BY_KEY[key]
                if spec.panel=='price':
                    draws += [(values[n],spec.color,1.6,'' if j==0 else '5 3') for j,n in enumerate(spec.lines)]
            raw=[float(v) for seq,_,_,_ in draws for v in seq if math.isfinite(float(v))]
            if chart_type=='candles': raw += [float(v) for bar in series.ohlc for v in bar]
            low,high=min(raw),max(raw)
            pad=max((high-low)*.08,abs(high)*.0001,.00001)
            low,high=low-pad,high+pad
            ticks=[low+(high-low)*i/3 for i in range(4)]
            label=ctx.t('price')+' · '+ctx.text(series.unit)
        elif panel=='rsi':
            low,high=0.,100.;ticks=[0,30,50,70,100]
            draws=[(values['RSI14'],BY_KEY['rsi'].color,1.7,'')];label='RSI14'
        elif panel=='macd':
            draws=[(values[n],BY_KEY['macd'].color,1.6,'' if n=='MACD' else '5 3') for n in ('MACD','Signal')]
            raw=[abs(float(v)) for n in ('MACD','Signal','Histogram') for v in values[n] if math.isfinite(float(v))]
            high=max([.00001,*raw])*1.15;low=-high;ticks=[low,0,high];label='MACD 12 / 26 / 9'
        else:
            low,high=0,max(1,max(series.volume))*1.1;ticks=[0,high]
            draws=[];label=ctx.text('Volume')
        y=lambda v:ybottom-(float(v)-low)/(high-low)*(ybottom-ytop)
        text(left,ytop-7,label,colors.muted,size=11)
        for value in ticks:
            yy=y(value)
            line(left,yy,right,yy,colors.border,.7)
            digits=0 if panel in {'rsi','volume'} else (4 if series.unit=='EUR per USD' or panel=='macd' else 2)
            text(left-9,yy+4,ctx.number(value,digits),colors.muted,'end',10)
        if panel=='rsi':
            for value in (30,70): line(left,y(value),right,y(value),BY_KEY['rsi'].color,.8,'4 4')
        if panel=='price' and 'bb' in selected:
            valid=[i for i in range(len(series.closes)) if math.isfinite(float(values['Upper'][i]))]
            points=[(x(i),y(values['Upper'][i])) for i in valid]+[(x(i),y(values['Lower'][i])) for i in reversed(valid)]
            if points:parts.append('<polygon points="'+' '.join(f'{a:.2f},{b:.2f}' for a,b in points)+f'" fill="{BY_KEY["bb"].color}" fill-opacity="0.08"/>')
        if panel=='macd':
            for i,value in enumerate(values['Histogram']):
                if not math.isfinite(float(value)): continue
                line(x(i),y(0),x(i),y(value),BY_KEY['macd'].color,max(.8,min(4,area/len(series.closes)*.6)))
        if panel=='volume':
            for i,value in enumerate(series.volume): line(x(i),y(0),x(i),y(value),colors.muted,max(.8,area/len(series.closes)*.65))
        if panel=='price' and chart_type=='candles':
            half=max(.7,min(4,area/len(series.closes)*.35))
            for i,(o,h,l,c) in enumerate(series.ohlc):
                rising=c>=o;color=colors.success if rising else colors.error
                line(x(i),y(h),x(i),y(l),color)
                parts.append(f'<rect x="{x(i)-half:.2f}" y="{min(y(o),y(c)):.2f}" width="{half*2:.2f}" height="{max(1,abs(y(o)-y(c))):.2f}" fill="{colors.surface if rising else color}" stroke="{color}"/>')
            draws=draws[1:]
        for seq,color,stroke,dash in draws:
            commands=[];connected=False
            for i,value in enumerate(seq):
                if not math.isfinite(float(value)):
                    connected=False;continue
                commands.append(('L' if connected else 'M')+f'{x(i):.2f} {y(value):.2f}')
                connected=True
            parts.append('<path d="'+' '.join(commands)+f'" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linejoin="round"'
                         +(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
        if index is not None:
            line(x(index),ytop,x(index),ybottom,colors.muted,.9,'3 3')
        if number==len(panels)-1:
            count=3 if width<600 else 5
            for i in range(count):
                at=round(i*(len(series.closes)-1)/(count-1))
                text(x(at),ybottom+23,ctx.date(series.dates[at]),colors.muted,
                     'start' if i==0 else ('end' if i==count-1 else 'middle'),10)
    parts.append('</g></svg>')
    return ''.join(parts)


def cursor_text(series, keys, index, locale=None):
    ctx=locale or LocaleContext()
    at=max(0,min(len(series.closes)-1,int(index)))
    values=indicator_values(series)
    digits=4 if series.unit=='EUR per USD' else 2
    parts=[ctx.date(series.dates[at]),series.symbol+' '+ctx.number(series.closes[at],digits)]
    for key in selection(keys):
        for name in BY_KEY[key].lines:
            value=float(values[name][at])
            parts.append(ctx.text(name)+' '+(ctx.number(value,1 if name=='RSI14' else digits) if math.isfinite(value) else '—'))
    return ' · '.join(parts)


def reading_text(series, keys, index, locale=None):
    """Selected-date observations, without inferred trading direction or verdicts."""
    ctx=locale or LocaleContext();at=max(0,min(len(series.closes)-1,int(index)))
    values=indicator_values(series);lines=[]
    for key in selection(keys):
        names=BY_KEY[key].lines
        if not all(math.isfinite(float(values[name][at])) for name in names):
            lines.append(ctx.t('reading_warmup',indicator=ctx.t(key)));continue
        if key in {'sma','ema','macd'}:
            first,second=names[:2]
            a,b=values[first][at],values[second][at]
            lines.append(ctx.t('reading_above' if a>b else 'reading_below' if a<b else 'reading_equal',
                               first=ctx.text(first),second=ctx.text(second)))
        elif key=='rsi':
            value=values['RSI14'][at]
            lines.append(ctx.t('reading_rsi_high' if value>=70 else 'reading_rsi_low' if value<=30 else 'reading_rsi_mid'))
        else:
            value=series.closes[at]
            lines.append(ctx.t('reading_bb_high' if value>values['Upper'][at] else 'reading_bb_low' if value<values['Lower'][at] else 'reading_bb_mid'))
    if len(selection(keys))>1:lines.append(ctx.t('combination_text'))
    return '\n'.join(lines)


def learning_bundle(series, keys, meta, *, case_name, locale=None, cursor=None):
    ctx=locale or LocaleContext();selected=selection(keys)
    sections=[]
    for key in selected:
        sections.append('<section><h2>'+escape(ctx.t(key))+'</h2>'+''.join(
            '<h3>'+escape(ctx.t(field))+'</h3><p>'+escape(ctx.t(key+'_'+field))+'</p>'
            for field in ('meaning','look','interpret','limit'))+'</section>')
    examples=counterexamples(series,selected)
    event_text=[ctx.t('event',date=ctx.date(e['date']),indicator=ctx.t(e['indicator']),change=ctx.percent(e['change'])) for e in examples]
    body=(f'<!doctype html><html lang="{ctx.language}" dir="{"rtl" if ctx.rtl else "ltr"}"><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\'">'
          '<title>'+escape(ctx.t('report_title'))+'</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:24px;color:#202823;background:#f7f5f0}svg{width:100%;height:auto}section{background:white;padding:20px;margin:16px 0;border-radius:12px}h3{font-size:14px}p{line-height:1.6}</style>'
          '<h1>'+escape(ctx.t('report_title'))+'</h1><p>'+escape(ctx.t('education_only'))+'</p><p>'+escape(ctx.t('historical_source') if case_name!='research' else series.source)+'</p>'
          +chart_svg(series,selected,locale=ctx,cursor=cursor)
          +'<p>'+escape(ctx.t('line_styles'))+'</p>'
          +('<h2>'+escape(ctx.t('cursor'))+'</h2><p>'+escape(cursor_text(series,selected,cursor,ctx))+'</p><p>'+escape(reading_text(series,selected,cursor,ctx)).replace('\n','<br>')+'</p>' if cursor is not None else '')
          +'<h2>'+escape(ctx.t('why_sample'))+'</h2><p>'+escape(ctx.t('why_'+case_name))+'</p>'
          +''.join(sections)+'<h2>'+escape(ctx.t('failed_signals'))+'</h2><p>'+escape(ctx.t('failure_note'))+'</p>'
          +''.join('<p>'+escape(text)+'</p>' for text in event_text)
          +'<p>'+escape(ctx.t('source'))+': '+escape(meta.get('provider',series.source))+' · '+escape(meta.get('series_url',''))+'</p></html>')
    record=dict(format='quantgen.indicator-education/1',locale=str(ctx.locale),text_language=ctx.language,
                case=case_name,symbol=series.symbol,first_date=series.dates[0],last_date=series.dates[-1],
                selected_indicators=list(selected),source=meta,education_only=True,verdict='NOT_RUN',
                counterexamples=examples)
    record['input_sha256']=hashlib.sha256(json.dumps(list(zip(series.dates,series.closes)),separators=(',',':'),allow_nan=False).encode()).hexdigest()
    files={'report.html':body.encode(),'education.json':(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()}
    files['MANIFEST.json']=json.dumps({'format':'quantgen.indicator-education/1','files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()}},indent=2).encode()
    out=BytesIO()
    with ZipFile(out,'w',ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
    return out.getvalue()
