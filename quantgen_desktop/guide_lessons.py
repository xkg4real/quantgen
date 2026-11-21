"""Chart-first lessons, used only by the docked educational guide.

The invented OHLCV/flow fixture is deliberately separate from market/history
objects, provenance and report inputs. All indicator arrays come from the study
registry's compute_study (including its seeded EMA); no alternate formula lives
here. A callout and its line use the very same Plot.point mapping.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from html import escape
import math

from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetricsF
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy

from core.education.indicators import Bars, Supply, compute_study, study
from core.market.presentation import study_colors
from core.theme import LIGHT, DARK


# Concept / what to compare / one limit. These explain observations, never an
# instruction to trade. Registry keys, parameters and calculation categories stay
# in their original modules.
LESSONS = {
    'sma': (('최근 20봉 종가를 같은 비중으로 평균낸 선', 'An equal-weight mean of the last 20 closes'),
            ('가격과 평균선의 거리를 보세요.', 'Compare the price with its average.'),
            ('평균은 늦게 반응해요. 횡보하면 위아래로 자주 오갈 수 있어요.', 'An average lags. Sideways prices can cross it repeatedly.')),
    'ema': (('최근 종가에 더 큰 비중을 주는 가중평균', 'A moving average that weights recent closes more'),
            ('12봉 설정은 빠르게, 26봉 설정은 천천히 반응해요.', 'The 12-bar setting reacts faster than the 26-bar setting.'),
            ('12봉 EMA는 최근 12개만의 단순평균이 아니에요. 교차가 추세 지속을 보장하지 않아요.', 'EMA 12 is not a simple mean of only the last 12 closes. A crossing does not guarantee a continuing trend.')),
    'macd': (('빠른 EMA12에서 느린 EMA26을 뺀 값', 'EMA 12 minus EMA 26'),
             ('MACD와 신호선의 위치, 막대의 부호를 비교해요.', 'Compare MACD with its signal line and the sign of the bars.'),
             ('막대는 두 선의 차이예요. 가격 변화율이나 수익률이 아니에요.', 'A bar is the gap between the lines, not a price return.')),
    'ichimoku': (('가격 범위의 중간값과 앞뒤로 옮긴 선', 'Price-range midpoints and shifted lines'),
                ('전환 9·기준 26·범위 52봉. 이동은 현재 봉을 첫째로 센 26번째, 즉 25칸이에요.', 'The ranges are 9/26/52 bars. Shifts reach the 26th bar counting the current bar first: 25 spaces.'),
                ('선행스팬은 계산한 값을 옮겨 그린 선이지 미래를 관측한 값이 아니에요.', 'A leading span is a shifted calculation, not an observation of the future.')),
    'psar': (('가격 위아래에 놓이는 SAR 점', 'SAR dots above or below the price'),
             ('점이 가격의 어느 쪽에 있는지 보세요.', 'See which side of the price contains the dots.'),
             ('횡보에서는 점의 위치가 자주 바뀔 수 있어요.', 'Dots can switch sides repeatedly in a sideways market.')),
    'adx': (('ADX는 강도, +DI·−DI는 방향 성분', 'ADX measures strength; +DI and −DI are directional components'),
            ('ADX와 두 DI를 서로 구분해서 읽어요.', 'Read ADX separately from the two DI lines.'),
            ('ADX가 높다는 말만으로 가격 상승을 뜻하지 않아요.', 'A high ADX alone does not mean that prices are rising.')),
    'envelope': (('20봉 평균에서 위아래 5% 떨어진 선', 'Lines 5% above and below the 20-bar mean'),
                 ('가격이 고정 비율의 띠 어디에 놓이는지 보세요.', 'Locate the price inside or outside the fixed-percentage band.'),
                 ('띠 밖으로 나갔다고 반드시 평균으로 돌아오지는 않아요.', 'Moving outside the band does not guarantee a return to its mean.')),
    'keltner': (('EMA20 중심에 ATR10의 2배 폭을 더한 채널', 'EMA 20 with a width of twice ATR 10'),
                ('중심선과 변동폭으로 만든 위·아래 선을 구분해요.', 'Separate the centre line from the volatility-based edges.'),
                ('변동폭이 커지면 채널도 넓어져요. 경계는 확정된 가격 한계가 아니에요.', 'The channel widens with volatility. Its edges are not guaranteed price limits.')),
    'donchian': (('최근 20봉 최고·최저와 그 중간', 'The high, low and midpoint of the last 20 bars'),
                ('가격과 최근 범위의 경계를 비교해요.', 'Compare the price with the edges of its recent range.'),
                ('새 고가·저가가 나오면 경계도 바뀌어요.', 'The edges change when new highs or lows appear.')),
    'rsi': (('14봉 상승·하락폭을 비교한 0~100 지수', 'A 0–100 index comparing gains and losses over 14 bars'),
            ('30·70 기준선과 현재 선의 위치를 비교해요.', 'Compare the line with the 30 and 70 reference levels.'),
            ('70 위·30 아래에 오래 머물 수 있어요. 반전을 확정하지 않아요.', 'It can stay above 70 or below 30. Neither position confirms a reversal.')),
    'stoch': (('최근 14봉 고저 범위에서 종가의 위치', 'The close within the last 14 bars’ high–low range'),
              ('%K와 이를 평활한 %D, 20·80 기준을 비교해요.', 'Compare %K, its smoothed %D and the 20/80 levels.'),
              ('높은 값은 범위 위쪽이라는 뜻이지 곧 하락한다는 뜻이 아니에요.', 'A high value means near the top of the range, not an imminent price fall.')),
    'stochrsi': (('가격이 아니라 RSI 범위 안의 위치', 'The position of RSI within its own range'),
                 ('RSI14에 다시 14봉 범위와 3·3 평활을 적용해요.', 'RSI 14 is measured over a 14-bar range, then smoothed 3/3.'),
                 ('RSI 자체보다 민감해요. 짧은 움직임에도 교차가 잦을 수 있어요.', 'It is more sensitive than RSI itself and can cross often.')),
    'cci': (('가격이 평소 평균에서 얼마나 멀어졌는지', 'How far the price is from its usual average'),
            ('0·±100을 기준으로 위치를 보세요.', 'Compare the line with 0 and ±100.'),
            ('0~100으로 제한되지 않아요. ±100 밖에서도 계속 움직일 수 있어요.', 'It is not bounded by 0–100 and can continue beyond ±100.')),
    'williams': (('14봉 범위에서 종가가 놓인 −100~0 위치', 'The close in a 14-bar range, scaled from −100 to 0'),
                 ('−20에 가까우면 범위 위쪽, −80에 가까우면 아래쪽이에요.', 'Near −20 is toward the range top; near −80 is toward its bottom.'),
                 ('음수 축이에요. −20이 −80보다 위라는 점을 확인해요.', 'The scale is negative: −20 is above −80.')),
    'roc': (('12봉 전 종가 대비 현재 종가의 변화율', 'The percentage change from the close 12 bars earlier'),
            ('0% 위·아래와 변화의 크기를 함께 봐요.', 'Read both the sign around 0% and the size of the change.'),
            ('0~100 지수가 아니에요. 과거 변화율이 다음 수익률은 아니에요.', 'This is not a 0–100 index or a forecast of the next return.')),
    'disparity': (('평균 가격을 100으로 놓고 현재 위치를 비교', 'The current price with its average set to 100'),
                  ('100이면 평균과 같고, 105면 평균보다 5% 높아요.', '100 equals the mean; 105 is 5% above it.'),
                  ('높거나 낮아도 괴리가 더 커질 수 있어요.', 'The distance can keep growing even at a high or low value.')),
    'psychology': (('최근 10봉 중 상승한 봉의 비율', 'The share of rising bars among the last 10 bars'),
                   ('얼마나 크게 올랐는지가 아니라 상승 횟수를 세요.', 'It counts rising bars, not the size of their gains.'),
                   ('같은 값이어도 실제 가격 변화폭은 다를 수 있어요.', 'Equal values can accompany very different price changes.')),
    'bb': (('20봉 평균에서 표준편차 2배 떨어진 밴드', 'Bands two standard deviations from the 20-bar mean'),
           ('가격의 위치와 밴드 사이 폭을 함께 봐요.', 'Compare the price position and the distance between the bands.'),
           ('밴드는 미래 가격의 95% 보장 구간이 아니에요.', 'The bands do not guarantee a 95% range for future prices.')),
    'atr': (('갭까지 포함한 14봉 평균 변동폭', 'The 14-bar average true range, including gaps'),
            ('가격과 같은 단위로 움직임의 폭을 읽어요.', 'Read the movement range in the same units as the price.'),
            ('ATR 상승은 변동폭 증가예요. 상승 방향을 뜻하지 않아요.', 'A rising ATR means a wider range, not a rising price direction.')),
    'percent_b': (('위·아래 밴드 사이에서 현재 가격이 놓인 위치', 'Where the current price sits between the two bands'),
                  ('종가가 두 볼린저 밴드 사이 어디인지 비율로 읽어요.', 'Locate the close between the Bollinger bands as a ratio.'),
                  ('밴드 밖에서는 0 미만·1 초과도 가능해요.', 'Outside the bands, values can be below 0 or above 1.')),
    'bandwidth': (('가격을 감싼 밴드가 얼마나 좁고 넓은지', 'How narrow or wide the bands around the price are'),
                  ('폭이 좁아지고 넓어지는 정도를 %로 비교해요.', 'Compare narrowing and widening as a percentage.'),
                  ('폭이 좁다고 다음 움직임의 방향을 알 수는 없어요.', 'A narrow width does not reveal the direction of the next move.')),
    'volume_ma': (('최근 20봉 거래량의 평균', 'The mean volume of the last 20 bars'),
                  ('거래량 막대와 평균선을 비교해요.', 'Compare each volume bar with the mean line.'),
                  ('거래량 증가만으로 매수·매도 방향을 알 수는 없어요.', 'More volume alone does not identify a buying or selling direction.')),
    'obv': (('상승 봉 거래량을 더하고 하락 봉 거래량을 뺀 누계', 'Volume added on rising closes and subtracted on falling closes'),
            ('시작점 이후 누적 방향을 읽어요. 금액이 아니라 수량이에요.', 'Read the cumulative direction since the start, in quantity rather than money.'),
            ('투자 주체의 실제 자금 유입·유출을 측정한 값이 아니에요.', 'It does not measure actual cash flowing in or out by investor group.')),
    'mfi': (('가격·거래량으로 만든 14봉 0~100 지수', 'A 14-bar 0–100 index using price and volume'),
            ('20·80 기준과 선의 위치를 비교해요.', 'Compare the line with the 20 and 80 levels.'),
            ('이름과 달리 기관·외국인의 실제 자금을 뜻하지 않아요.', 'Despite its name, it does not measure actual institutional or foreign funds.')),
    'vwap': (('세션 시작부터 거래량 비중으로 평균낸 가격', 'A volume-weighted mean price since the session began'),
             ('거래가 많은 봉이 평균에 더 큰 영향을 줘요.', 'Bars with more volume affect the mean more.'),
             ('5분봉 학습 예시예요. 새 세션에서 초기화하며 일봉 VWAP는 그리지 않아요.', 'This is a five-minute lesson. VWAP restarts each session and is not drawn on daily bars.')),
    'investor_flow': (('외국인·기관·개인의 일별 순매수 수량 누계', 'Cumulative daily net-buy quantities by investor group'),
                      ('0 기준 위·아래와 세 선의 차이를 비교해요.', 'Compare the three lines and their positions around zero.'),
                      ('가상 국내 일봉 수급이에요. 수량이지 금액이 아니며 해외·분봉에 대입하지 않아요.', 'These are invented domestic daily flows, in shares rather than money; not overseas or intraday data.')),
    'short_ratio': (('그날 거래량 중 공매도 거래 수량의 비중', 'The short-sale share of that day’s traded volume'),
                    ('각 일봉의 거래 비중을 %로 읽어요.', 'Read the percentage of traded volume for each daily bar.'),
                    ('가상 국내 일봉 예시예요. 미청산 공매도 잔고 비율과 달라요.', 'This invented domestic daily example is not the outstanding short-position ratio.')),
}


def words(pair, language):
    return pair[0 if language == 'ko' else 1]


@lru_cache(maxsize=2)
def teaching_bars(intraday=False):
    """Manual, deterministic invented bars: no file, source, provider or RNG."""
    n = 180
    close = tuple(100 + .055*i + 7*math.sin(i/11) + 2.2*math.sin(i/3.7) for i in range(n))
    opening = (99.4,) + tuple(close[i-1] + .4*math.sin(i/2) for i in range(1,n))
    high = tuple(max(o,c) + 1.1 + .3*math.cos(i/4) for i,(o,c) in enumerate(zip(opening,close)))
    low = tuple(min(o,c) - 1.1 - .3*math.sin(i/5) for i,(o,c) in enumerate(zip(opening,close)))
    volume = tuple(float(1000 + (i*137)%900 + 400*(1+math.sin(i/8))) for i in range(n))
    start = datetime(2024,1,8,9)
    if intraday:
        stamps = tuple((start+timedelta(days=i//60,minutes=(i%60)*5)).isoformat() for i in range(n))
    else:
        dates=[]; day=start
        while len(dates)<n:
            if day.weekday()<5:dates.append(day.date().isoformat())
            day+=timedelta(days=1)
        stamps=tuple(dates)
    bars=Bars(stamps,opening,high,low,close,volume,'5m' if intraday else '1d')
    flows=tuple((day[:10],float(90*math.sin(i/10)),float(60*math.cos(i/13)),
                 float(-90*math.sin(i/10)-60*math.cos(i/13))) for i,day in enumerate(stamps))
    shorts=tuple((day[:10],float(4+2*math.sin(i/14)),float(30+i%11)) for i,day in enumerate(stamps))
    return bars,Supply(flows,shorts)


@lru_cache(maxsize=27)
def lesson_values(key):
    bars,supply=teaching_bars(key=='vwap')
    return bars,compute_study(key,bars,supply=supply)


def number(value,kind):
    if not math.isfinite(float(value)):return '—'
    suffix='%' if kind=='percent' else ''
    return f'{float(value):,.2f}{suffix}'.replace('-','−')


@dataclass(frozen=True)
class Plot:
    left: float
    top: float
    width: float
    height: float
    count: int
    low: float
    high: float

    def point(self,index,value):
        return (self.left+self.width*index/(self.count-1),
                self.top+self.height*(self.high-float(value))/(self.high-self.low))


def last_finite(values):
    return next((i for i in range(len(values)-1,-1,-1) if math.isfinite(float(values[i]))),None)


def crossing(values,other):
    """Actual adjacent finite sign change only; missing values never bridge a gap."""
    for i in range(len(values)-1,0,-1):
        a,b,c,d=(float(values[i-1]),float(other[i-1]),float(values[i]),float(other[i]))
        if all(math.isfinite(v) for v in (a,b,c,d)) and (a-b)*(c-d)<0:return i
    return None


def line_role(key,line,language):
    roles={
        ('ema','EMA12'):('최근 가격에 더 빨리 반응하는 선 · 12봉 설정','Reacts faster to recent prices · 12-bar setting'),
        ('ema','EMA26'):('큰 흐름을 천천히 따라가는 선 · 26봉 설정','Follows the broader movement more slowly · 26-bar setting'),
        ('sma','SMA20'):('가격을 같은 비중으로 고르게 평균낸 선 · 20봉','An equal-weight average of prices · 20 bars'),
        ('macd','MACD'):('빠른 가격 흐름과 느린 흐름 사이의 거리','The gap between faster and slower price movements'),
        ('macd','SIGNAL'):('그 거리를 더 부드럽게 이은 비교선','A smoother comparison line for that gap'),
        ('macd','HISTOGRAM'):('두 선 사이가 얼마나 벌어졌는지 보여 주는 막대','Bars showing the gap between those two lines'),
        ('ichimoku','TENKAN'):('짧은 가격 범위의 가운데 · 9봉','The midpoint of a shorter price range · 9 bars'),
        ('ichimoku','KIJUN'):('더 긴 가격 범위의 가운데 · 26봉','The midpoint of a longer price range · 26 bars'),
        ('ichimoku','SPAN_A'):('두 가운데 선을 합쳐 앞쪽으로 옮긴 선','The two midpoints averaged and shifted forward'),
        ('ichimoku','SPAN_B'):('더 넓은 가격 범위의 가운데를 앞쪽으로 이동','A wider range midpoint shifted forward'),
        ('ichimoku','CHIKOU'):('현재 종가를 뒤쪽으로 옮겨 놓은 선','The current close shifted backward'),
        ('adx','ADX'):('방향과 별개로 움직임이 뚜렷한 정도','How strong the movement is, apart from its direction'),
        ('adx','PDI'):('위쪽으로 움직인 가격의 성분','The component of upward price movement'),
        ('adx','MDI'):('아래쪽으로 움직인 가격의 성분','The component of downward price movement'),
        ('envelope','ENV_UPPER'):('평균 가격보다 5% 위인 선','The line 5% above the mean price'),
        ('envelope','ENV_MIDDLE'):('가격 흐름의 가운데 · 20봉 평균','The centre of the price movement · 20-bar mean'),
        ('envelope','ENV_LOWER'):('평균 가격보다 5% 아래인 선','The line 5% below the mean price'),
        ('keltner','KC_UPPER'):('가격의 흔들림을 반영한 위쪽 경계','An upper edge that reflects the price range'),
        ('keltner','KC_MIDDLE'):('최근 가격에 더 무게를 둔 가운데 선','The centre line weighted toward recent prices'),
        ('keltner','KC_LOWER'):('가격의 흔들림을 반영한 아래쪽 경계','A lower edge that reflects the price range'),
        ('donchian','DC_UPPER'):('최근 20봉에서 가장 높았던 가격','The highest price over the last 20 bars'),
        ('donchian','DC_MIDDLE'):('최고 가격과 최저 가격 사이의 가운데','The midpoint between the highest and lowest prices'),
        ('donchian','DC_LOWER'):('최근 20봉에서 가장 낮았던 가격','The lowest price over the last 20 bars'),
        ('stoch','STOCH_K'):('최근 가격 범위 중 어느 높이에 왔는지','Where the close sits within its recent range'),
        ('stoch','STOCH_D'):('그 높이를 부드럽게 이은 비교선','A smoother line for comparing that position'),
        ('stochrsi','STOCHRSI_K'):('가격이 아닌 RSI 자체 범위 안에서의 위치','The position in RSI’s range, rather than the price range'),
        ('stochrsi','STOCHRSI_D'):('그 위치를 다시 부드럽게 이은 선','That position smoothed again for comparison'),
        ('bb','BB_UPPER'):('평소 흔들림의 크기로 넓힌 위쪽 밴드','An upper band expanded by the size of usual price variations'),
        ('bb','BB_LOWER'):('평소 흔들림의 크기로 넓힌 아래쪽 밴드','A lower band expanded by the size of usual price variations'),
        ('investor_flow','FOREIGN'):('외국인이 순매수한 수량의 누계','The cumulative quantity bought net by foreign investors'),
        ('investor_flow','INSTITUTION'):('기관이 순매수한 수량의 누계','The cumulative quantity bought net by institutions'),
        ('investor_flow','INDIVIDUAL'):('개인이 순매수한 수량의 누계','The cumulative quantity bought net by individuals'),
    }
    if (key,line.id) in roles:return words(roles[(key,line.id)],language)
    if len(study(key).lines)==1:
        return line.name(language)+' · '+words(LESSONS[key][0],language)
    return line.name(language)


def axis_unit(spec,language):
    kind=spec.lines[0].kind
    pair={'price':('가상 가격 단위','Invented price units'),
          'quantity':('가상 수량 (주)','Invented quantity (shares)'),
          'percent':('퍼센트 (%)','Percent (%)'),'ratio':('비율','Ratio'),
          'index':('지수','Index'),'value':('값','Value')}[kind]
    if spec.key=='macd':pair=('가상 가격 차이','Invented price difference')
    return words(pair,language)


def _wrap(text,width,measure):
    """Measured SVG lines; handles Hangul and a single long word without clipping."""
    rows=[];row=''
    for char in text:
        if row and measure(row+char)>width:
            rows.append(row.rstrip());row=char.lstrip()
        else:row+=char
    if row:rows.append(row.rstrip())
    return rows or ['']


def lesson_svg(key,step,language,*,width=700,dark=False,font_family='QG Interface',measure=None):
    """Return SVG and inspectable geometry, with no market/export input accepted."""
    if key not in LESSONS:raise ValueError('Unknown lesson')
    if step not in (0,1,2):raise ValueError('Unknown lesson step')
    width=max(320,int(width));measure=measure or (lambda text:sum(13 if ord(c)>255 else 7.5 for c in text))
    bars,values=lesson_values(key);spec=study(key);palette=study_colors(key,dark)
    theme=DARK if dark else LIGHT
    ink=theme.text;muted=theme.muted;bg=theme.surface;rule=theme.border
    line_specs=list(spec.lines)
    selected=line_specs[:3]
    anchors=[];event=None;comparison_name=None
    if step==2:
        eligible={'sma','ema','macd','stoch','stochrsi','rsi','cci','williams','roc','disparity','psychology','mfi','percent_b','vwap'}
        if key in eligible:
            first=values[line_specs[0].id]
            if len(line_specs)>1:
                other=values[line_specs[1].id];comparison_name=line_specs[1].name(language)
            elif spec.panel=='price':
                other=bars.close;comparison_name=words(('종가','Close'),language)
            elif spec.references:
                other=(spec.references[0],)*len(bars);comparison_name=str(spec.references[0])
            else:other=None
            event=crossing(first,other) if other is not None else None
        selected=line_specs[:1]
    for pos,line in enumerate(selected):
        arr=values[line.id];index=event if event is not None else last_finite(arr)
        if index is None:continue
        value=float(arr[index]);bar_name=f'{index+1}봉' if language=='ko' else f'bar {index+1}'
        label=line_role(key,line,language) if step==0 else line.name(language)+' · '+number(value,line.kind)+' · '+bar_name
        if step==0 and not label.startswith(('①','②','③')):label=f'{pos+1} '+label
        if step==2:
            label=words(('이 봉 전후 위치가 바뀜','Positions switch across this bar'),language) if event is not None else (
                words(('교차 표시 없음','No crossing is marked'),language) if key in eligible else
                words(('현재 예시의 선 위 값','A value on the example line'),language))
            if comparison_name is not None:label+=' · '+line.name(language)+' / '+comparison_name
        anchors.append({'line':line.id,'index':index,'value':value,'color':palette[line.id],
                        'label':label,'number':pos+1,'text_rows':_wrap(label,width-56,measure)})
    # Full-width separate lanes cannot overlap, even at the narrowest viewport.
    lane_y=14
    for anchor in anchors:
        anchor['label_box']=(12,lane_y,width-24,18*len(anchor['text_rows'])+16)
        lane_y+=anchor['label_box'][3]+6
    top=lane_y+22;plot_height=220
    finite=[float(v) for line in line_specs for v in values[line.id] if math.isfinite(float(v))]
    reference=list(spec.references)
    if spec.panel=='price':finite+=list(bars.close)
    if spec.panel=='volume':finite+=list(bars.volume)+[0.0]
    if any(line.style=='bars' for line in line_specs):finite+=[0.0]
    finite+=reference
    if spec.bounds:finite+=list(spec.bounds)
    low,high=(min(finite),max(finite)) if finite else (0.,1.)
    if spec.bounds:
        # Registry-bounded studies keep their real domain (e.g. RSI0–100).
        # If a future calculation is out of domain, stop rather than clip it.
        low,high=map(float,spec.bounds)
        if any(v<low-1e-9 or v>high+1e-9 for v in finite):
            raise ValueError('Lesson value outside its registered bounds')
    else:
        pad=max((high-low)*.1,abs(high)*.01,.01);low-=pad;high+=pad
    plot=Plot(20,top,width-92,plot_height,len(bars),low,high)
    height=int(top+plot_height+54)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
         '<title>'+escape(spec.name(language)+' · '+words(('가상 학습 그림','Invented teaching chart'),language))+'</title>',
         f'<rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="{bg}"/>',
         f'<g font-family="{escape(font_family,quote=True)}" font-size="13" fill="{ink}">']
    svg.append(f'<text x="{plot.left}" y="{plot.top-9}" fill="{muted}" font-size="12">{escape(axis_unit(spec,language))}</text>')
    for frac in (0,.5,1):
        value=plot.high-(plot.high-plot.low)*frac;y=plot.top+plot.height*frac
        svg.append(f'<path d="M {plot.left} {y:.3f} H {plot.left+plot.width}" stroke="{rule}"/>')
        svg.append(f'<text x="{plot.left+plot.width+8}" y="{y+4:.3f}" fill="{muted}" font-size="12">{escape(number(value,line_specs[0].kind))}</text>')
    for level in reference:
        _,y=plot.point(0,level)
        svg.append(f'<path d="M {plot.left} {y:.3f} H {plot.left+plot.width}" stroke="{muted}" stroke-dasharray="3 5" opacity=".6"/>')
        svg.append(f'<text x="{plot.left+4}" y="{y-5:.3f}" fill="{muted}" font-size="12">{escape(number(level,line_specs[0].kind))}</text>')
    paths={}
    def draw_series(name,arr,color,style='solid',stroke_width=2):
        points=[];segments=[];segment=[]
        for i,value in enumerate(arr):
            if not math.isfinite(float(value)):
                if segment:segments.append(segment);segment=[]
                continue
            x,y=plot.point(i,value);points.append((i,float(value),x,y));segment.append((x,y))
        if segment:segments.append(segment)
        paths[name]=points
        if style=='dots':
            svg.extend(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="2" fill="{color}"/>' for _,_,x,y in points)
        elif style=='bars':
            zero=plot.point(0,0)[1]
            svg.extend(f'<path d="M {x:.3f} {zero:.3f} V {y:.3f}" stroke="{color}" stroke-width="2"/>' for _,_,x,y in points)
        else:
            dash=' stroke-dasharray="6 4"' if style=='dash' else ''
            for segment in segments:
                path=' '.join(('M' if i==0 else 'L')+f' {x:.3f} {y:.3f}' for i,(x,y) in enumerate(segment))
                svg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{stroke_width}"{dash}/>')
    if spec.panel=='price':draw_series('CLOSE',bars.close,muted,stroke_width=1)
    if spec.panel=='volume':draw_series('VOLUME',bars.volume,rule,'bars')
    for line in line_specs:draw_series(line.id,values[line.id],palette[line.id],line.style)
    for anchor in anchors:
        x,y=plot.point(anchor['index'],anchor['value']);anchor['point']=(x,y)
        bx,by,bw,bh=anchor['label_box'];color=anchor['color']
        svg.append(f'<path d="M {bx+bw-12} {by+bh} L {x:.3f} {y:.3f}" stroke="{color}" fill="none" stroke-dasharray="2 4" opacity=".7"/>')
        svg.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="5" fill="{bg}" stroke="{color}" stroke-width="2"/>')
        svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="{bg}" stroke="{color}"/>')
        for row,text in enumerate(anchor['text_rows']):
            svg.append(f'<text x="{bx+12}" y="{by+23+row*18}" fill="{color}">{escape(text)}</text>')
    first=words(('오래된 봉','Earlier bars'),language) if step==0 else words(('1봉','Bar 1'),language)
    last=words(('최근 봉','Recent bars'),language) if step==0 else words((f'{len(bars)}봉',f'Bar {len(bars)}'),language)
    svg.append(f'<text x="{plot.left}" y="{top+plot_height+25}" fill="{muted}" font-size="12">{first}</text>')
    svg.append(f'<text x="{plot.left+plot.width}" y="{top+plot_height+25}" fill="{muted}" text-anchor="end" font-size="12">{last}</text>')
    svg.append('</g></svg>')
    return ''.join(svg),{'width':width,'height':height,'plot':plot,'anchors':anchors,'paths':paths,
                         'crossing_index':event,'key':key,'step':step,'interval':bars.interval,
                         'computed_lines':tuple(values),'references':tuple(reference),
                         'axis_unit':axis_unit(spec,language),'comparison_name':comparison_name,
                         'registered_axis_bounds':tuple(spec.bounds)}


class LessonFigure(QSvgWidget):
    step_requested=pyqtSignal(int)

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right,Qt.Key.Key_Home,Qt.Key.Key_End):
            self.step_requested.emit({Qt.Key.Key_Left:-1,Qt.Key.Key_Right:1,Qt.Key.Key_Home:-3,Qt.Key.Key_End:3}[event.key()])
            event.accept();return
        super().keyPressEvent(event)


class GuideLesson(QWidget):
    """Explicitly created in dock_into only; no history or export parameter."""
    choose_requested=pyqtSignal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.key=None;self.language='ko';self.dark=False;self.step=0;self.geometry_info=None
        self.setObjectName('guideLesson')
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,16);box.setSpacing(10)
        self.title=QLabel();self.title.setWordWrap(True);box.addWidget(self.title)
        self.badge=QLabel();self.badge.setWordWrap(True);box.addWidget(self.badge)
        self.starter=QWidget();starter=QHBoxLayout(self.starter);starter.setContentsMargins(0,0,0,0)
        self.start_buttons=[]
        for key in ('sma','ema','rsi'):
            button=QPushButton();button.setProperty('kit','chip')
            button.clicked.connect(lambda checked=False,k=key:self.choose_requested.emit(k))
            starter.addWidget(button);self.start_buttons.append((key,button))
        box.addWidget(self.starter)
        self.step_host=QWidget();steps=QHBoxLayout(self.step_host);steps.setContentsMargins(0,0,0,0);steps.setSpacing(6)
        self.buttons=[]
        for i in range(3):
            button=QPushButton();button.setCheckable(True);button.setProperty('sd','period')
            button.clicked.connect(lambda checked=False,s=i:self.set_step(s));steps.addWidget(button);self.buttons.append(button)
        box.addWidget(self.step_host)
        self.figure=LessonFigure();self.figure.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.figure.setMinimumWidth(320)
        self.figure.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        self.figure.step_requested.connect(self.move_step);box.addWidget(self.figure)
        self.legend=QLabel();self.legend.setWordWrap(True);self.legend.setTextFormat(Qt.TextFormat.RichText);box.addWidget(self.legend)
        self.caption=QLabel();self.caption.setWordWrap(True);self.caption.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);box.addWidget(self.caption)
        self.limit=QLabel();self.limit.setWordWrap(True);box.addWidget(self.limit)
        self.context_label=QLabel();self.context_label.setWordWrap(True);box.addWidget(self.context_label)

    def focus_widgets(self):
        return self.buttons+[self.figure] if self.key else [button for _,button in self.start_buttons]

    def set_lesson(self,key,language,dark):
        if key!=self.key:self.step=0
        self.key=key if key in LESSONS else None;self.language=language;self.dark=bool(dark)
        accent=(DARK if self.dark else LIGHT).accent
        self.figure.setStyleSheet('QSvgWidget { border: 2px solid transparent; border-radius: 10px; } '
                                 'QSvgWidget:focus { border-color: '+accent+'; }')
        self.refresh()

    def move_step(self,delta):
        self.set_step(0 if delta==-3 else 2 if delta==3 else max(0,min(2,self.step+delta)))

    def set_step(self,step):
        self.step=max(0,min(2,int(step)));self.refresh()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.refresh()

    def refresh(self):
        ko=self.language=='ko';key=self.key
        self.title.setText(('선 위에서 배우기 · '+study(key).name(self.language) if key else '선 위에서 배우기') if ko else
                           ('Learn on the lines · '+study(key).name(self.language) if key else 'Learn on the lines'))
        self.title.setStyleSheet('font-size: 17px; font-weight: 500;')
        self.badge.setText(('가상 5분봉 학습 그림 · 세션별 초기화' if key=='vwap' else '가상 일봉 학습 그림 · 1칸 = 1거래일') if ko else
                           ('Invented 5-minute lesson · resets each session' if key=='vwap' else 'Invented daily-bar lesson · one bar = one trading day'))
        for candidate,button in self.start_buttons:button.setText(('시작: ' if ko else 'Start: ')+study(candidate).label(self.language))
        self.starter.setVisible(not key)
        for widget in (self.step_host,self.figure,self.legend,self.caption,self.limit):widget.setVisible(bool(key))
        self.context_label.setText(('사례 차트 보기에서 원래 날짜·출처를 확인할 수 있어요. 보고서는 그 사례를 기준으로 하며, 가상 학습 값은 섞이지 않아요.' if ko else
                                    'Show the context chart to inspect its original dates and source. Reports use that context; invented lesson values stay separate.'))
        if not key:
            self.badge.setText('오른쪽 지표를 고르거나 아래에서 시작해 보세요.' if ko else 'Choose an indicator on the right, or start below.')
            self.geometry_info=None;return
        for i,button in enumerate(self.buttons):
            button.setText((('1 선의 뜻','2 값 비교','3 관찰·한계') if ko else ('1 Lines','2 Compare','3 Limits'))[i])
            button.setChecked(i==self.step)
            button.setAccessibleName(button.text()+' · '+study(key).name(self.language))
        font=QFont(self.font());font.setPixelSize(13);metrics=QFontMetricsF(font)
        svg,info=lesson_svg(key,self.step,self.language,width=max(320,self.figure.width()),dark=self.dark,
                             font_family=font.family(),measure=metrics.horizontalAdvance)
        self.geometry_info=info;self.figure.setFixedHeight(info['height']);self.figure.load(QByteArray(svg.encode('utf-8')))
        palette=study_colors(key,self.dark);spec=study(key);bars,values=lesson_values(key)
        legend=[];plain=[]
        for i,line in enumerate(spec.lines):
            index=last_finite(values[line.id]);value=number(values[line.id][index],line.kind) if index is not None else '—'
            style={'solid':('실선','solid'),'dash':('점선','dashed'),'dots':('점','dots'),'bars':('막대','bars')}[line.style][0 if ko else 1]
            bar_name=(f'{index+1}봉' if ko else f'bar {index+1}') if index is not None else '—'
            compact=f'{i+1} {line.name(self.language)} · {style}'
            detail=f'{compact} · {value} ({bar_name})'
            visible=detail if self.step==1 else compact
            legend.append(f'<span style="color:{palette[line.id]}">{escape(visible)}</span>')
            plain.append(detail+' · '+line_role(key,line,self.language))
        if spec.panel in ('price','volume'):
            value=bars.close[-1] if spec.panel=='price' else bars.volume[-1]
            name=('종가' if spec.panel=='price' else '거래량 막대') if ko else ('Close' if spec.panel=='price' else 'Volume bars')
            detail=name+' · '+number(value,'price' if spec.panel=='price' else 'quantity')
            legend.append(escape(detail if self.step==1 else name));plain.append(detail)
        self.legend.setText(' &nbsp; / &nbsp; '.join(legend))
        self.legend.setToolTip('\n'.join(plain))
        self.legend.setAccessibleName('선 범례' if ko else 'Line legend')
        self.legend.setAccessibleDescription('\n'.join(plain))
        concept,comparison,limit=LESSONS[key]
        text=words(concept if self.step==0 else comparison if self.step==1 else limit,self.language)
        if self.step==0 and key=='ema':text+=(' · 12·26은 봉 수 설정이에요. 이 예시는 일봉이에요.' if ko else ' · 12/26 are bar-span settings; this example uses daily bars.')
        if self.step==2 and info['crossing_index'] is not None:
            text=(f"{info['crossing_index']+1}봉 전후 두 값의 위치가 바뀌었어요. " if ko else
                  f"The values switch positions across bar {info['crossing_index']+1}. ")+text
        if self.step==2 and info['comparison_name'] is not None:
            text+=(' 교차는 빈 값 없이 이웃한 두 봉에서 위치가 분명히 바뀔 때만 표시해요.' if ko else
                   ' A crossing is marked only when adjacent finite bars clearly switch sides.')
        self.caption.setText(text)
        self.limit.setText(('계산 준비 구간·없는 값은 선을 잇지 않아요. 교육용이며 예측·매매 지시가 아니에요.' if ko else
                            'Warm-up and missing values stay blank. Education only; no prediction or trading instruction.'))
        description='\n'.join([self.badge.text(),info['axis_unit'],text,*plain,*[a['label'] for a in info['anchors']],self.limit.text()])
        self.figure.setAccessibleName(self.title.text());self.figure.setAccessibleDescription(description)
        self.caption.setAccessibleDescription(description)
