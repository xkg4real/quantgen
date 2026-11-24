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
    'sma': (('최근 20일 종가를 똑같은 비중으로 평균낸 선이에요.', 'An equal-weight mean of the last 20 closes'),
            ('가격과 평균선 사이의 거리를 보세요.', 'Compare the price with its average.'),
            ('평균이라 가격보다 늦게 움직여요. 옆으로 오갈 때는 선을 자주 넘나들 수 있어요.', 'An average lags. Sideways prices can cross it repeatedly.')),
    'ema': (('최근 종가에 더 큰 비중을 두는 평균선이에요.', 'A moving average that weights recent closes more'),
            ('12일 설정은 빠르게, 26일 설정은 천천히 따라와요.', 'The 12-bar setting reacts faster than the 26-bar setting.'),
            ('EMA 12는 최근 12일만의 평균이 아니에요. 교차해도 흐름이 이어진다는 보장은 없어요.', 'EMA 12 is not a simple mean of only the last 12 closes. A crossing does not guarantee a continuing trend.')),
    'macd': (('빠른 평균(EMA 12)에서 느린 평균(EMA 26)을 뺀 값이에요.', 'EMA 12 minus EMA 26'),
             ('MACD선이 신호선보다 위인지, 막대가 0 위인지 보세요.', 'Compare MACD with its signal line and the sign of the bars.'),
             ('막대는 두 선의 차이예요. 가격 변화율이나 수익률이 아니에요.', 'A bar is the gap between the lines, not a price return.')),
    'ichimoku': (('가격 범위의 가운데 값과, 그 값을 앞뒤로 옮겨 그린 선들이에요.', 'Price-range midpoints and shifted lines'),
                ('기간은 9·26·52일이에요. 오늘을 첫째로 세어 26번째, 곧 25칸 옮겨 그려요.', 'The ranges are 9/26/52 bars. Shifts reach the 26th bar counting the current bar first: 25 spaces.'),
                ('앞쪽에 그린 선행스팬은 계산값을 옮긴 것이지 미래를 본 값이 아니에요.', 'A leading span is a shifted calculation, not an observation of the future.')),
    'psar': (('가격 위나 아래에 찍히는 점(SAR)이에요.', 'SAR dots above or below the price'),
             ('점이 가격의 위쪽에 있는지 아래쪽에 있는지 보세요.', 'See which side of the price contains the dots.'),
             ('옆으로 오갈 때는 점이 위아래로 자주 바뀔 수 있어요.', 'Dots can switch sides repeatedly in a sideways market.')),
    'adx': (('ADX는 움직임의 세기, +DI·−DI는 오르는 힘과 내리는 힘이에요.', 'ADX measures strength; +DI and −DI are directional components'),
            ('ADX와 두 DI 선을 따로 읽어요.', 'Read ADX separately from the two DI lines.'),
            ('ADX가 높다는 것만으로 가격이 오른다는 뜻은 아니에요.', 'A high ADX alone does not mean that prices are rising.')),
    'envelope': (('20일 평균에서 위아래로 5%씩 떨어뜨린 선이에요.', 'Lines 5% above and below the 20-bar mean'),
                 ('가격이 띠 안에 있는지, 밖에 있는지 보세요.', 'Locate the price inside or outside the fixed-percentage band.'),
                 ('띠 밖으로 나가도 꼭 평균으로 돌아오지는 않아요.', 'Moving outside the band does not guarantee a return to its mean.')),
    'keltner': (('EMA 20을 가운데 두고 평균 변동폭(ATR 10)의 2배만큼 벌린 통로예요.', 'EMA 20 with a width of twice ATR 10'),
                ('가운데 선과 위·아래 경계를 나눠서 보세요.', 'Separate the centre line from the volatility-based edges.'),
                ('움직임이 커지면 통로도 넓어져요. 경계는 정해진 가격 한계가 아니에요.', 'The channel widens with volatility. Its edges are not guaranteed price limits.')),
    'donchian': (('최근 20일의 최고가·최저가와 그 가운데를 이은 선이에요.', 'The high, low and midpoint of the last 20 bars'),
                ('가격이 최근 범위의 위·아래 끝에 얼마나 가까운지 보세요.', 'Compare the price with the edges of its recent range.'),
                ('새 최고가나 최저가가 나오면 경계도 함께 바뀌어요.', 'The edges change when new highs or lows appear.')),
    'rsi': (('오른 폭과 내린 폭을 14일 기준으로 평균내 비교한 0~100 값이에요. 그 전 날들도 조금씩 남아요.', 'A 0–100 index comparing average gains and losses, smoothed on a 14-bar setting; earlier bars still count a little'),
            ('선이 30·70 기준선에 대해 어디에 있는지 보세요.', 'Compare the line with the 30 and 70 reference levels.'),
            ('70 위나 30 아래에 오래 머물 수 있어요. 그것만으로 방향이 바뀐다고 볼 수 없어요.', 'It can stay above 70 or below 30. Neither position confirms a reversal.')),
    'stoch': (('최근 14일 최고가·최저가 사이에서 종가가 어느 높이에 있는지 나타내요.', 'The close within the last 14 bars’ high–low range'),
              ('%K와 이를 부드럽게 한 %D를 20·80 기준선과 함께 보세요.', 'Compare %K, its smoothed %D and the 20/80 levels.'),
              ('값이 높으면 범위 위쪽이라는 뜻이지, 곧 내린다는 뜻은 아니에요.', 'A high value means near the top of the range, not an imminent price fall.')),
    'stochrsi': (('가격이 아니라 RSI가 자기 범위 안에서 어디쯤인지 나타내요.', 'The position of RSI within its own range'),
                 ('RSI 14에 다시 14일 범위를 적용하고 3·3으로 부드럽게 해요.', 'RSI 14 is measured over a 14-bar range, then smoothed 3/3.'),
                 ('RSI보다 민감해요. 작은 움직임에도 교차가 잦을 수 있어요.', 'It is more sensitive than RSI itself and can cross often.')),
    'cci': (('가격이 평소 평균에서 얼마나 멀어졌는지 나타내요.', 'How far the price is from its usual average'),
            ('0과 ±100 기준선에 대해 선의 위치를 보세요.', 'Compare the line with 0 and ±100.'),
            ('0~100 안에 갇힌 값이 아니에요. ±100 밖에서도 계속 움직일 수 있어요.', 'It is not bounded by 0–100 and can continue beyond ±100.')),
    'williams': (('최근 14일 범위에서 종가가 어디에 있는지 −100~0으로 나타내요.', 'The close in a 14-bar range, scaled from −100 to 0'),
                 ('−20에 가까우면 범위 위쪽, −80에 가까우면 아래쪽이에요.', 'Near −20 is toward the range top; near −80 is toward its bottom.'),
                 ('음수 눈금이에요. −20이 −80보다 위쪽이에요.', 'The scale is negative: −20 is above −80.')),
    'roc': (('12일 전 종가와 비교해 지금 종가가 몇 % 변했는지 나타내요.', 'The percentage change from the close 12 bars earlier'),
            ('0% 위인지 아래인지와 변화 크기를 함께 보세요.', 'Read both the sign around 0% and the size of the change.'),
            ('0~100 지수가 아니에요. 지난 변화율이 다음 수익률은 아니에요.', 'This is not a 0–100 index or a forecast of the next return.')),
    'disparity': (('평균 가격을 100으로 놓고 지금 가격이 어디쯤인지 나타내요.', 'The current price with its average set to 100'),
                  ('100이면 평균과 같고, 105면 평균보다 5% 높아요.', '100 equals the mean; 105 is 5% above it.'),
                  ('이미 높거나 낮아도 차이가 더 벌어질 수 있어요.', 'The distance can keep growing even at a high or low value.')),
    'psychology': (('최근 10일 가운데 오른 날의 비율이에요.', 'The share of rising bars among the last 10 bars'),
                   ('오른 폭이 아니라 오른 날의 수만 세는 값이에요.', 'It counts rising bars, not the size of their gains.'),
                   ('값이 같아도 실제 가격 변화 폭은 다를 수 있어요.', 'Equal values can accompany very different price changes.')),
    'bb': (('20일 평균에서 평소 흔들림 크기(표준편차)의 2배만큼 위아래로 벌린 띠예요.', 'Bands two standard deviations from the 20-bar mean'),
           ('가격이 띠의 어디에 있는지와 띠의 폭을 함께 보세요.', 'Compare the price position and the distance between the bands.'),
           ('띠가 앞으로의 가격 범위를 95% 보장하지는 않아요.', 'The bands do not guarantee a 95% range for future prices.')),
    'atr': (('전날 종가와 벌어진 틈(갭)까지 넣은 하루 변동폭을 14일 기준으로 평균낸 값이에요.', 'The true range, including gaps, averaged on a 14-bar setting'),
            ('가격과 같은 단위로 하루에 움직이는 폭을 읽어요.', 'Read the movement range in the same units as the price.'),
            ('ATR이 오르면 움직임이 커진 것이지, 가격이 오른다는 뜻은 아니에요.', 'A rising ATR means a wider range, not a rising price direction.')),
    'percent_b': (('위·아래 볼린저 밴드 사이에서 지금 가격이 어디쯤인지 나타내요.', 'Where the current price sits between the two bands'),
                  ('0이면 아래 밴드, 1이면 위 밴드, 0.5면 가운데예요.', 'Locate the close between the Bollinger bands as a ratio.'),
                  ('밴드 밖에서는 0보다 작거나 1보다 클 수 있어요.', 'Outside the bands, values can be below 0 or above 1.')),
    'bandwidth': (('가격을 감싼 밴드가 얼마나 좁고 넓은지 나타내요.', 'How narrow or wide the bands around the price are'),
                  ('폭이 좁아지는지 넓어지는지 %로 비교해요.', 'Compare narrowing and widening as a percentage.'),
                  ('폭이 좁다고 다음 움직임의 방향을 알 수는 없어요.', 'A narrow width does not reveal the direction of the next move.')),
    'volume_ma': (('최근 20일 거래량의 평균이에요.', 'The mean volume of the last 20 bars'),
                  ('그날 거래량 막대가 평균선보다 높은지 낮은지 보세요.', 'Compare each volume bar with the mean line.'),
                  ('거래량이 늘었다는 것만으로 사는 쪽인지 파는 쪽인지 알 수 없어요.', 'More volume alone does not identify a buying or selling direction.')),
    'obv': (('오른 날의 거래량은 더하고 내린 날의 거래량은 빼서 쌓은 값이에요.', 'Volume added on rising closes and subtracted on falling closes'),
            ('쌓인 값이 오르는지 내리는지 보세요. 금액이 아니라 주식 수예요.', 'Read the cumulative direction since the start, in quantity rather than money.'),
            ('투자자들이 실제로 넣거나 뺀 돈을 잰 값이 아니에요.', 'It does not measure actual cash flowing in or out by investor group.')),
    'mfi': (('가격과 거래량으로 만든 14일 기준 0~100 지수예요.', 'A 14-bar 0–100 index using price and volume'),
            ('선이 20·80 기준선에 대해 어디에 있는지 보세요.', 'Compare the line with the 20 and 80 levels.'),
            ('이름과 달리 기관·외국인의 실제 자금 흐름을 뜻하지 않아요.', 'Despite its name, it does not measure actual institutional or foreign funds.')),
    'vwap': (('장이 열린 뒤부터 거래가 많은 가격에 더 무게를 둬 평균낸 가격이에요.', 'A volume-weighted mean price since the session began'),
             ('거래가 많았던 5분 구간일수록 평균에 더 큰 영향을 줘요.', 'Bars with more volume affect the mean more.'),
             ('5분 간격 학습 예시예요. 날마다 새로 계산하며 일별 차트에는 그리지 않아요.', 'This is a five-minute lesson. VWAP restarts each session and is not drawn on daily bars.')),
    'investor_flow': (('외국인·기관·개인이 날마다 순매수한 수량을 쌓아 올린 값이에요.', 'Cumulative daily net-buy quantities by investor group'),
                      ('0 위인지 아래인지, 세 선이 서로 얼마나 벌어지는지 보세요.', 'Compare the three lines and their positions around zero.'),
                      ('가상 국내 일별 수급이에요. 금액이 아닌 주식 수이며 해외·분 단위 자료에는 쓰지 않아요.', 'These are invented domestic daily flows, in shares rather than money; not overseas or intraday data.')),
    'short_ratio': (('그날 거래량 가운데 공매도로 거래된 수량의 비중이에요.', 'The short-sale share of that day’s traded volume'),
                    ('하루하루의 공매도 거래 비중을 %로 읽어요.', 'Read the percentage of traded volume for each daily bar.'),
                    ('가상 국내 일별 예시예요. 아직 갚지 않은 공매도 잔고 비율과는 달라요.', 'This invented domestic daily example is not the outstanding short-position ratio.')),
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
    # Share counts read as whole shares; "339.25주" looked like a fractional holding.
    digits=0 if kind=='quantity' else 2
    return f'{float(value):,.{digits}f}{suffix}'.replace('-','−')


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


def slot_name(index,interval,language):
    """One-based position on the lesson's x axis, in plain day/five-minute wording (owner R-D9-2)."""
    if language!='ko':return f'bar {index+1}'
    return f'{index+1}번째 5분' if interval!='1d' else f'{index+1}일째'


def line_role(key,line,language):
    roles={
        ('ema','EMA12'):('최근 가격에 더 빨리 반응하는 선 · 12일 설정','Reacts faster to recent prices · 12-bar setting'),
        ('ema','EMA26'):('큰 흐름을 천천히 따라가는 선 · 26일 설정','Follows the broader movement more slowly · 26-bar setting'),
        ('sma','SMA20'):('가격을 같은 비중으로 고르게 평균낸 선 · 20일','An equal-weight average of prices · 20 bars'),
        ('macd','MACD'):('빠른 가격 흐름과 느린 흐름 사이의 거리','The gap between faster and slower price movements'),
        ('macd','SIGNAL'):('그 거리를 더 부드럽게 이은 비교선','A smoother comparison line for that gap'),
        ('macd','HISTOGRAM'):('두 선 사이가 얼마나 벌어졌는지 보여 주는 막대','Bars showing the gap between those two lines'),
        ('ichimoku','TENKAN'):('짧은 가격 범위의 가운데 · 9일','The midpoint of a shorter price range · 9 bars'),
        ('ichimoku','KIJUN'):('더 긴 가격 범위의 가운데 · 26일','The midpoint of a longer price range · 26 bars'),
        ('ichimoku','SPAN_A'):('두 가운데 선을 합쳐 앞쪽으로 옮긴 선','The two midpoints averaged and shifted forward'),
        ('ichimoku','SPAN_B'):('더 넓은 가격 범위의 가운데를 앞쪽으로 이동','A wider range midpoint shifted forward'),
        ('ichimoku','CHIKOU'):('현재 종가를 뒤쪽으로 옮겨 놓은 선','The current close shifted backward'),
        ('adx','ADX'):('방향과 별개로 움직임이 뚜렷한 정도','How strong the movement is, apart from its direction'),
        ('adx','PDI'):('위쪽으로 움직인 가격의 성분','The component of upward price movement'),
        ('adx','MDI'):('아래쪽으로 움직인 가격의 성분','The component of downward price movement'),
        ('envelope','ENV_UPPER'):('평균 가격보다 5% 위인 선','The line 5% above the mean price'),
        ('envelope','ENV_MIDDLE'):('가격 흐름의 가운데 · 20일 평균','The centre of the price movement · 20-bar mean'),
        ('envelope','ENV_LOWER'):('평균 가격보다 5% 아래인 선','The line 5% below the mean price'),
        ('keltner','KC_UPPER'):('가격의 흔들림을 반영한 위쪽 경계','An upper edge that reflects the price range'),
        ('keltner','KC_MIDDLE'):('최근 가격에 더 무게를 둔 가운데 선','The centre line weighted toward recent prices'),
        ('keltner','KC_LOWER'):('가격의 흔들림을 반영한 아래쪽 경계','A lower edge that reflects the price range'),
        ('donchian','DC_UPPER'):('최근 20일 동안 가장 높았던 가격','The highest price over the last 20 bars'),
        ('donchian','DC_MIDDLE'):('최고 가격과 최저 가격 사이의 가운데','The midpoint between the highest and lowest prices'),
        ('donchian','DC_LOWER'):('최근 20일 동안 가장 낮았던 가격','The lowest price over the last 20 bars'),
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
        value=float(arr[index]);bar_name=slot_name(index,bars.interval,language)
        label=line_role(key,line,language) if step==0 else line.name(language)+' · '+number(value,line.kind)+' · '+bar_name
        if step==0 and not label.startswith(('①','②','③')):label=f'{pos+1} '+label
        if step==2:
            label=words(('여기서 두 값의 위아래가 바뀌어요','Positions switch across this bar'),language) if event is not None else (
                words(('표시할 교차가 없어요','No crossing is marked'),language) if key in eligible else
                words(('예시 선 위의 값이에요','A value on the example line'),language))
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
    reference_labels=[]
    for level in reference:
        _,y=plot.point(0,level)
        svg.append(f'<path d="M {plot.left} {y:.3f} H {plot.left+plot.width}" stroke="{muted}" stroke-dasharray="3 5" opacity=".6"/>')
        reference_labels.append((y,number(level,line_specs[0].kind)))
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
    # Reference values sit above the lines on a small background, so a line
    # crossing the left edge no longer runs through "0.00" or "70.00".
    for y,text in reference_labels:
        box_w=measure(text)+8
        svg.append(f'<rect x="{plot.left+1}" y="{y-19:.3f}" width="{box_w:.1f}" height="16" rx="3" fill="{bg}" opacity=".9"/>')
        svg.append(f'<text x="{plot.left+5}" y="{y-6:.3f}" fill="{muted}" font-size="12">{escape(text)}</text>')
    for anchor in anchors:
        x,y=plot.point(anchor['index'],anchor['value']);anchor['point']=(x,y)
        bx,by,bw,bh=anchor['label_box'];color=anchor['color']
        svg.append(f'<path d="M {bx+bw-12} {by+bh} L {x:.3f} {y:.3f}" stroke="{color}" fill="none" stroke-dasharray="2 4" opacity=".7"/>')
        svg.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="5" fill="{bg}" stroke="{color}" stroke-width="2"/>')
        svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="{bg}" stroke="{color}"/>')
        for row,text in enumerate(anchor['text_rows']):
            svg.append(f'<text x="{bx+12}" y="{by+23+row*18}" fill="{color}">{escape(text)}</text>')
    first=words(('← 과거','Earlier bars'),language) if step==0 else (slot_name(0,bars.interval,language) if language=='ko' else 'Bar 1')
    last=words(('최근 →','Recent bars'),language) if step==0 else (slot_name(len(bars)-1,bars.interval,language) if language=='ko' else f'Bar {len(bars)}')
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
        box.setAlignment(Qt.AlignmentFlag.AlignTop)
        from .stock_detail_style import label
        self.title=label('cardTitle',wrap=True);box.addWidget(self.title)
        self.badge=label('rowNote',wrap=True);box.addWidget(self.badge)
        self.starter=QWidget();starter=QHBoxLayout(self.starter);starter.setContentsMargins(0,0,0,0)
        self.start_buttons=[]
        for key in ('sma','ema','rsi'):
            button=QPushButton();button.setProperty('sd','period')
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
        self.legend=label('body',wrap=True);self.legend.setTextFormat(Qt.TextFormat.RichText);box.addWidget(self.legend)
        self.caption=label('body',wrap=True,selectable=True);box.addWidget(self.caption)
        self.limit=label('rowNote',wrap=True);box.addWidget(self.limit)
        self.context_label=label('rowNote',wrap=True);box.addWidget(self.context_label)

    def focus_widgets(self):
        return self.buttons+[self.figure] if self.key else [button for _,button in self.start_buttons]

    def set_lesson(self,key,language,dark):
        if key!=self.key:self.step=0
        self.key=key if key in LESSONS else None;self.language=language;self.dark=bool(dark)
        from .stock_detail_style import sheet
        self.setStyleSheet(sheet(DARK if self.dark else LIGHT,self.dark))
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
        self.badge.setText(('가상 학습 그림 · 한 칸 = 5분 · 날마다 새로 계산해요' if key=='vwap' else '가상 학습 그림 · 한 칸 = 하루(거래일)') if ko else
                           ('Invented 5-minute lesson · resets each session' if key=='vwap' else 'Invented daily-bar lesson · one bar = one trading day'))
        for candidate,button in self.start_buttons:button.setText(('시작: ' if ko else 'Start: ')+study(candidate).label(self.language))
        self.starter.setVisible(not key)
        for widget in (self.step_host,self.figure,self.legend,self.caption,self.limit):widget.setVisible(bool(key))
        self.context_label.setText(('위 사례 차트에서 원래 날짜·출처를 확인하세요. 이 보조 그림은 가상 예시이며, 사례·보고서 값은 바뀌지 않아요.' if ko else
                                    'The original dates and source are on the case chart above. This supplementary diagram is invented; case and report values stay unchanged.'))
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
            bar_name=slot_name(index,bars.interval,self.language) if index is not None else '—'
            # "막대 · 막대" said the same thing twice; a bar series named for its style needs no style word.
            name=line.name(self.language)
            compact=f'{i+1} {name}' if name.lower()==style.lower() else f'{i+1} {name} · {style}'
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
        if self.step==0 and key=='ema':text+=(' 12·26은 반응 속도를 정하는 기간 설정이고, 이 예시는 하루 단위예요.' if ko else ' · 12/26 are bar-span settings; this example uses daily bars.')
        if self.step==2 and info['crossing_index'] is not None:
            # Observation first, then the indicator's limit, each as its own sentence.
            where=slot_name(info['crossing_index'],bars.interval,self.language)
            text=(f"{where} 무렵 두 값의 위아래가 바뀌었어요. " if ko else
                  f"The values switch positions across bar {info['crossing_index']+1}. ")+text
        note=('계산에 필요한 앞부분과 빈 값은 선을 잇지 않아요. 교육용 예시이며 예측이나 매매 지시가 아니에요.' if ko else
              'Warm-up and missing values stay blank. Education only; no prediction or trading instruction.')
        if self.step==2 and info['comparison_name'] is not None:
            # The marking rule is a footnote, not part of the reading itself.
            step_unit='5분 구간' if bars.interval!='1d' else '날'
            note=(f'교차는 값이 비지 않은 이웃한 두 {step_unit} 사이에서 위아래가 바뀔 때만 표시해요. ' if ko else
                  'A crossing is marked only when adjacent finite bars clearly switch sides. ')+note
        self.caption.setText(text)
        self.limit.setText(note)
        description='\n'.join([self.badge.text(),info['axis_unit'],text,*plain,*[a['label'] for a in info['anchors']],self.limit.text()])
        self.figure.setAccessibleName(self.title.text());self.figure.setAccessibleDescription(description)
        self.caption.setAccessibleDescription(description)
