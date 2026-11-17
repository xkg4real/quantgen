"""Searchable market and analysis terms for the guide. Pure data; no I/O.

Technical-indicator entries reuse the reviewed indicator messages in
core/ui_messages.py, so the chart, the guide and exported reports share one text.
The other entries carry their own Korean and English text; tests hold the two
languages to the same keys and fields. Definitions are educational: they are not
advice, forecasts, research verdicts or a description of any provider's terms.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from core.education.indicators import BY_KEY as INDICATOR_KEYS

CATEGORIES = ('indicator', 'market', 'risk', 'model', 'rates', 'derivatives', 'fx', 'app')
FIELDS = ('name', 'summary', 'meaning', 'use', 'limit')
INDICATOR_FIELDS = ('meaning', 'look', 'interpret', 'limit')
POPULAR = ('rsi', 'macd', 'bb', 'volatility', 'var', 'duration', 'q_score')


@dataclass(frozen=True)
class Term:
    key: str
    category: str
    aliases: tuple
    text: dict  # language -> field -> text; empty for indicators (ui_messages owns them)


def _t(ko, en):
    return {'ko': dict(zip(FIELDS, ko)), 'en': dict(zip(FIELDS, en))}


TERMS = (
    Term('sma', 'indicator', ('SMA', 'MA', '단순이동평균', '이동평균', '이동평균선', '이평선', 'moving average',
                              'simple moving average', '골든크로스', '데드크로스', 'golden cross', 'death cross'), {}),
    Term('ema', 'indicator', ('EMA', '지수이동평균', '지수평활', 'exponential moving average'), {}),
    Term('rsi', 'indicator', ('RSI', '상대강도', '상대강도지수', 'relative strength index', '과매수', '과매도',
                              'overbought', 'oversold'), {}),
    Term('macd', 'indicator', ('MACD', '이동평균수렴확산', 'moving average convergence divergence', '시그널선',
                               'signal line', '히스토그램', 'histogram'), {}),
    Term('bb', 'indicator', ('BB', '볼린저', '볼린저밴드', '볼린저 밴드', 'bollinger', 'bollinger bands', '밴드'), {}),
    Term('candlestick', 'market', ('캔들', '봉', '봉차트', '일봉', '분봉', '양봉', '음봉', 'candle', 'candles', 'OHLC',
                                   'bar chart'), _t(
        ('캔들 차트 · 봉', '정한 기간의 시가·고가·저가·종가를 봉 하나로 그린 가격 차트',
         '1분·1일처럼 정한 기간마다 시가·고가·저가·종가를 봉 하나로 그립니다. 몸통은 시가와 종가 사이, 위아래 꼬리는 '
         '그 기간의 고가와 저가입니다. QUANTGEN 가격 차트는 국내 관례대로 종가가 시가보다 높으면 빨간색, 낮으면 파란색으로 표시합니다.',
         '기간 안의 가격 범위와 방향, 변동이 컸던 구간을 한눈에 봅니다. 봉 주기를 바꿔 짧은 흐름과 긴 흐름을 나눠 볼 수 있습니다.',
         '봉 모양만으로 이후 방향을 알 수 없습니다. 같은 가격도 봉 주기와 기준 시간대에 따라 모양이 달라집니다.'),
        ('Candlestick chart', 'A price chart that draws each period’s open, high, low and close as one bar',
         'Each period, such as one minute or one day, becomes one bar. The body spans the open and close; the wicks '
         'reach the period’s high and low. Following Korean convention, QUANTGEN price charts colour a bar red when it '
         'closes above its open and blue when it closes below.',
         'See each period’s range and direction, and where movement was large. Changing the bar interval separates '
         'short-term and longer-term behaviour.',
         'A bar’s shape does not reveal the next move. The same prices produce different bars at other intervals or '
         'session boundaries.'))),
    Term('volume', 'market', ('거래대금', 'trading volume', 'turnover'), _t(
        ('거래량', '정한 기간에 거래된 주식이나 계약의 수량',
         '정한 기간에 체결된 주식·계약의 수량입니다. 거래대금은 수량에 가격을 곱한 금액입니다.',
         '가격 변화에 얼마나 많은 거래가 동반됐는지 보고 움직임의 강도와 유동성을 가늠합니다.',
         '거래량이 많다고 가격의 방향이 정해지지 않습니다. 종목·시장마다 평소 수준이 달라 같은 종목의 과거와 비교해야 합니다.'),
        ('Volume', 'The number of shares or contracts traded in a period',
         'The number of shares or contracts executed in a period. Turnover is that quantity multiplied by price.',
         'Shows how much trading accompanied a price move, as a gauge of its strength and of liquidity.',
         'High volume does not set direction. Normal levels differ by instrument and market, so compare an instrument '
         'with its own history.'))),
    Term('quote_delay', 'market', ('실시간', '지연', '지연시세', '15분 지연', 'real-time', 'realtime', 'live', 'delayed',
                                   'delayed quotes'), _t(
        ('실시간·지연 시세', '체결 즉시 받는 시세와 정해진 시간 뒤에 받는 시세의 차이',
         '체결 즉시 받는 시세가 실시간 시세이고, 거래소 규정이나 이용 계약에 따라 일정 시간(예: 15분) 뒤에 받는 시세가 지연 시세입니다.',
         '화면의 가격이 언제 기준인지 확인해 판단에 쓰기에 알맞은지 정합니다.',
         '같은 종목도 공급사와 이용 계약에 따라 지연 여부가 다릅니다. 화면의 출처와 시각 표시를 함께 확인하세요.'),
        ('Real-time and delayed quotes', 'Prices received as trades happen versus after a set delay',
         'Real-time quotes arrive as trades execute. Delayed quotes arrive after a period, such as 15 minutes, set by '
         'exchange rules or the data agreement.',
         'Check the time a displayed price refers to before relying on it.',
         'The same instrument can be real-time from one provider and delayed from another. Read the source and time '
         'shown with the price.'))),
    Term('volatility', 'risk', ('vol', '표준편차', '연율화 변동성', 'standard deviation', 'annualized volatility'), _t(
        ('변동성', '수익률이 평균에서 얼마나 흩어지는지를 나타내는 값',
         '수익률이 평균 주위에서 얼마나 크게 흔들리는지를 나타냅니다. 보통 일간 수익률의 표준편차에 √252를 곱해 연 단위로 표시합니다.',
         '자산이나 전략의 위험 크기를 같은 기간 기준으로 비교하고, 위험 한도나 투자 비중을 정할 때 씁니다.',
         '오르내림을 구분하지 않습니다. 과거 변동성이 앞으로도 유지된다는 보장이 없고, 짧은 기간의 추정치는 급변 구간에서 크게 바뀝니다.'),
        ('Volatility', 'How widely returns are spread around their average',
         'Measures how widely returns swing around their average, usually the standard deviation of daily returns '
         'annualized by multiplying by √252.',
         'Compares the size of risk across assets or strategies over the same period, and helps set risk limits or '
         'position sizes.',
         'It treats rises and falls alike. Past volatility need not persist, and short-window estimates change sharply '
         'in turbulent periods.'))),
    Term('mdd', 'risk', ('MDD', 'drawdown', '낙폭', '최대손실폭', 'max drawdown'), _t(
        ('최대낙폭 · MDD', '이전 고점에서 이후 저점까지 가장 크게 떨어진 비율',
         '관측 기간 중 이전 고점에서 이후 저점까지 가장 크게 하락한 비율입니다.',
         '자산이나 전략이 겪은 가장 나쁜 누적 손실 구간을 확인하고, 감당할 수 있는 손실 수준과 비교합니다.',
         '관측한 기간 안의 결과일 뿐 앞으로의 최대 손실을 제한하지 않습니다. 기간이 짧을수록 실제 위험을 작게 보기 쉽습니다.'),
        ('Maximum drawdown · MDD', 'The largest fall from an earlier peak to a later trough',
         'The largest percentage decline from a previous peak to a subsequent trough within the observed period.',
         'Shows the worst cumulative loss an asset or strategy went through, for comparison with the loss you could '
         'tolerate.',
         'It describes the observed period only and does not cap future losses. Short samples tend to understate it.'))),
    Term('var', 'risk', ('VaR', 'value at risk', '최대예상손실'), _t(
        ('위험가치 · VaR', '정한 기간·신뢰수준에서 손실이 넘지 않을 것으로 보는 경계값',
         '정한 기간과 신뢰수준(예: 1일, 95%)에서 손실이 이 값을 넘을 확률이 나머지 확률(5%)이 되는 경계 손실입니다. 1일 95% VaR가 '
         '1억 원이면 하루 손실이 1억 원을 넘는 날이 평균적으로 20일에 하루 정도라는 뜻입니다.',
         '포트폴리오가 평소에 겪을 수 있는 손실 규모를 하나의 숫자로 요약하고 위험 한도와 비교합니다.',
         '경계를 넘은 손실이 얼마나 클지는 알려주지 않습니다. 과거 분포나 모형 가정이 바뀌면 값도 크게 달라집니다.'),
        ('Value at risk · VaR', 'A loss threshold not expected to be exceeded at a set horizon and confidence level',
         'At a chosen horizon and confidence level, such as one day and 95%, the loss exceeded only with the remaining '
         'probability (5%). A one-day 95% VaR of 100 million means a daily loss above 100 million on about one day in '
         'twenty on average.',
         'Summarizes a portfolio’s ordinary loss size in one number for comparison with risk limits.',
         'It says nothing about how large losses beyond the threshold can be, and it shifts with the sample or model '
         'assumptions.'))),
    Term('cvar', 'risk', ('CVaR', 'ES', 'expected shortfall', '기대손실', '기대부족액', 'conditional value at risk'), _t(
        ('조건부 VaR · CVaR', 'VaR를 넘는 나쁜 경우들의 평균 손실',
         '손실이 VaR를 넘는 경우들만 모아 계산한 평균 손실입니다. 기대손실(ES)이라고도 합니다.',
         'VaR보다 꼬리 위험, 즉 드물지만 큰 손실의 크기를 더 직접 보여 줍니다.',
         '꼬리 구간의 관측값이 적어 추정 오차가 큽니다. 과거 자료에 없던 위기는 반영하지 못합니다.'),
        ('Conditional VaR · CVaR', 'The average loss in the cases worse than VaR',
         'The average of the losses that exceed VaR, also called expected shortfall (ES).',
         'Shows the size of tail risk, rare but large losses, more directly than VaR.',
         'Few observations fall in the tail, so the estimate is noisy, and crises absent from the data are not '
         'reflected.'))),
    Term('sharpe', 'risk', ('sharpe ratio', '샤프비율', '샤프 비율', '위험조정수익률', 'risk-adjusted return'), _t(
        ('샤프 지수', '위험 한 단위당 얻은 초과수익',
         '(평균 수익률 − 무위험 수익률) ÷ 수익률의 표준편차입니다. 무위험 수익률을 0으로 두고 계산하기도 합니다.',
         '변동성이 서로 다른 전략이나 자산의 성과를 같은 기준으로 비교합니다.',
         '수익률 분포가 한쪽으로 치우치거나 꼬리 위험이 크면 위험을 작게 볼 수 있습니다. 측정 기간과 연율화 방식에 따라 값이 달라집니다.'),
        ('Sharpe ratio', 'Excess return earned per unit of risk',
         '(Average return − risk-free return) ÷ standard deviation of returns. Some calculations set the risk-free '
         'return to zero.',
         'Compares the performance of strategies or assets with different volatility on one basis.',
         'Skewed returns or heavy tails can make risk look smaller than it is, and the value depends on the period '
         'and annualization.'))),
    Term('beta', 'risk', ('β', '시장민감도', 'market beta'), _t(
        ('베타', '시장 전체 움직임에 대한 자산의 민감도',
         '시장 지수가 1% 움직일 때 자산이 평균적으로 몇 % 움직였는지를 나타냅니다. 시장과의 공분산을 시장 분산으로 나눠 구합니다.',
         '포트폴리오가 시장 전체 움직임에 얼마나 노출되어 있는지 파악하고 헤지 규모를 정합니다.',
         '추정 기간과 기준 지수에 따라 달라지고 시간이 지나며 변합니다. 시장과 무관한 개별 위험은 설명하지 않습니다.'),
        ('Beta', 'An asset’s sensitivity to moves in the overall market',
         'How many percent an asset moved on average when the market index moved 1%, computed as its covariance with '
         'the market divided by the market’s variance.',
         'Gauges a portfolio’s exposure to market-wide moves and sizes hedges.',
         'It depends on the estimation window and benchmark and changes over time. It does not capture risk unrelated '
         'to the market.'))),
    Term('correlation', 'risk', ('상관관계', 'corr', '상관'), _t(
        ('상관계수', '두 자산의 수익률이 함께 움직이는 정도(−1~+1)',
         '두 자산의 수익률이 같은 방향으로 움직이는 정도를 −1에서 +1 사이 값으로 나타냅니다.',
         '분산투자 효과와 포트폴리오 전체 위험을 가늠합니다.',
         '위기 때는 상관계수가 갑자기 높아지는 일이 많습니다. 직선 관계만 재며 인과관계를 뜻하지 않습니다.'),
        ('Correlation', 'How closely two assets’ returns move together (−1 to +1)',
         'Measures, between −1 and +1, how closely two assets’ returns move in the same direction.',
         'Gauges diversification and overall portfolio risk.',
         'Correlations often jump in crises. It measures linear association only and does not imply causation.'))),
    Term('monte_carlo', 'model', ('MC', '몬테카를로', 'monte carlo', '시뮬레이션', 'simulation'), _t(
        ('몬테카를로 시뮬레이션', '가정한 확률 모형으로 미래 경로를 여러 번 만들어 결과 분포를 보는 방법',
         '가정한 확률 모형에서 미래 가격 경로를 수천 번 무작위로 만들어, 가능한 결과가 어떻게 분포하는지 살펴봅니다.',
         '하나의 예측값 대신 결과의 범위(예: P5~P95)와 손실 가능성을 함께 보여 줍니다.',
         '결과는 입력한 모형·변동성·기대수익 가정에 달려 있습니다. 경로 수를 늘려도 잘못된 가정은 바로잡히지 않습니다.'),
        ('Monte Carlo simulation', 'Generating many future paths from an assumed model to study the spread of outcomes',
         'Draws thousands of random future price paths from an assumed probability model to study how outcomes are '
         'distributed.',
         'Shows a range of outcomes (such as P5 to P95) and the chance of loss instead of a single forecast.',
         'Results depend on the model, volatility and expected-return assumptions. More paths do not correct a wrong '
         'assumption.'))),
    Term('percentile_band', 'model', ('P5', 'P95', 'P50', 'P5-P95', '백분위', '백분위수', '중앙값', 'percentile',
                                      'median', 'fan chart', '팬 차트'), _t(
        ('백분위 구간 · P5–P95', '시뮬레이션 결과의 중앙 90%가 놓인 범위',
         '시뮬레이션 결과를 작은 값부터 늘어놓았을 때 5% 위치(P5)와 95% 위치(P95) 사이로, 결과의 중앙 90%를 나타냅니다. P50은 중앙값입니다.',
         '결과가 어느 범위에 몰려 있는지, 기간이 길어질수록 불확실성이 얼마나 커지는지 보여 줍니다.',
         '모형 안에서의 분포입니다. 95% 신뢰구간이나 수익 보장이 아닙니다.'),
        ('Percentile band · P5–P95', 'The range holding the middle 90% of simulated outcomes',
         'With simulated outcomes sorted from lowest to highest, the range between the 5% point (P5) and the 95% point '
         '(P95) holds the middle 90%. P50 is the median.',
         'Shows where outcomes cluster and how uncertainty widens over longer horizons.',
         'It is a distribution within the model, not a 95% confidence interval or a guarantee of returns.'))),
    Term('garch', 'model', ('GARCH', 'GARCH(1,1)', '조건부 변동성', 'conditional volatility', '변동성 군집',
                            'volatility clustering'), _t(
        ('GARCH 모형', '최근 충격에 따라 날마다 변하는 변동성을 추정하는 시계열 모형',
         '큰 가격 변동 뒤에 큰 변동이 이어지는 변동성 군집을 반영해, 시점마다 달라지는 조건부 변동성을 추정합니다. '
         'GARCH(1,1)은 전날의 충격과 전날의 변동성으로 오늘의 변동성을 설명합니다.',
         '변동성이 높은 시기와 낮은 시기를 구분해 위험 추정과 시뮬레이션 범위를 조정합니다.',
         '모수 추정이 불안정할 수 있고, 추정치가 허용 범위의 경계에 닿으면 해석에 주의해야 합니다. 구조적 변화나 갑작스러운 사건은 미리 알지 못합니다.'),
        ('GARCH model', 'A time-series model of volatility that changes with recent shocks',
         'Estimates conditional volatility that changes over time, reflecting volatility clustering: large moves tend '
         'to follow large moves. GARCH(1,1) explains today’s variance with yesterday’s shock and yesterday’s variance.',
         'Separates high- and low-volatility periods to adjust risk estimates and simulation ranges.',
         'Parameter estimates can be unstable; take care when an estimate reaches a bound of its allowed range. It '
         'cannot anticipate structural breaks or sudden events.'))),
    Term('backtest', 'model', ('백테스팅', 'backtesting', '과거 검증', '전략 검증'), _t(
        ('백테스트', '정한 규칙을 과거 데이터에 적용해 보는 계산',
         '정한 매매 규칙을 과거 데이터에 적용해, 그때 거래했다면 어떤 결과가 나왔을지 계산합니다.',
         '규칙의 거래 빈도, 비용의 영향, 손실 구간을 미리 확인합니다.',
         '과거에 맞춘 규칙은 앞으로 같은 결과를 내지 않을 수 있습니다(과최적화). 비용·체결·생존 편향이 반영됐는지 확인하세요.'),
        ('Backtest', 'Applying a fixed rule to historical data',
         'Applies a fixed trading rule to historical data to calculate what trading it would have produced.',
         'Shows the rule’s trading frequency, the effect of costs and its losing periods in advance.',
         'A rule fitted to the past may not repeat its results (overfitting). Check that costs, execution and '
         'survivorship bias are reflected.'))),
    Term('yield_curve', 'rates', ('금리 기간구조', '기간구조', '금리커브', '커브', 'term structure', 'curve',
                                  '장단기 금리차'), _t(
        ('수익률 곡선', '만기별 금리를 이은 곡선',
         '만기가 다른 금리를 이은 곡선으로, 금리의 기간구조라고도 합니다. 보통은 만기가 길수록 금리가 높은 우상향 모양입니다.',
         '경기와 통화정책에 대한 시장 기대를 읽고, 채권과 금리 상품의 가격을 매기는 기준으로 씁니다.',
         '곡선 모양만으로 경기 침체 시점을 정확히 예측할 수 없습니다. 관측 만기 사이의 금리는 보간 방법에 따라 달라집니다.'),
        ('Yield curve', 'Interest rates plotted across maturities',
         'Rates for different maturities joined into one curve, also called the term structure. It usually slopes '
         'upward, with longer maturities paying more.',
         'Reads market expectations for growth and monetary policy, and serves as the basis for pricing bonds and rate '
         'products.',
         'The curve’s shape cannot time a recession precisely. Rates between observed maturities depend on the '
         'interpolation method.'))),
    Term('bootstrap', 'rates', ('bootstrapping', 'bootstrap', '제로금리', '무이표 금리', 'zero curve', 'zero rate',
                                '할인계수', 'discount factor'), _t(
        ('부트스트래핑', '시장 금리에서 할인계수와 무이표 금리를 차례로 풀어내는 방법',
         '시장에서 관측한 이표채·스왑 금리에서 짧은 만기부터 차례로 할인계수와 무이표(제로) 금리를 풀어냅니다.',
         '현금흐름마다 맞는 할인율을 구해 채권·스왑의 가치를 계산합니다.',
         '입력 금리와 보간 방법에 따라 곡선이 달라지고, 관측 만기가 드문 구간에서는 오차가 커집니다.'),
        ('Bootstrapping', 'Solving discount factors and zero rates from market rates, maturity by maturity',
         'Solves discount factors and zero-coupon rates from observed coupon-bond or swap rates, starting with the '
         'shortest maturity.',
         'Provides the discount rate for each cash flow to value bonds and swaps.',
         'The curve depends on the input rates and interpolation, and errors grow where observed maturities are '
         'sparse.'))),
    Term('duration', 'rates', ('수정 듀레이션', '맥컬리 듀레이션', 'modified duration', 'macaulay duration',
                               '금리 민감도'), _t(
        ('듀레이션', '채권 가격의 금리 민감도',
         '채권 현금흐름의 가중평균 만기이자, 금리 변화에 대한 가격 민감도입니다. 수정 듀레이션이 5이면 금리가 1%p 오를 때 가격이 약 5% 내립니다.',
         '금리 변화에 대한 채권·포트폴리오의 가격 위험을 비교하고, 자산과 부채의 금리 위험을 맞출 때 씁니다.',
         '작은 금리 변화에 대한 1차 근사입니다. 금리가 크게 움직이면 볼록성(컨벡시티)을 함께 봐야 합니다.'),
        ('Duration', 'A bond price’s sensitivity to interest rates',
         'The weighted-average maturity of a bond’s cash flows and its price sensitivity to rates. A modified duration '
         'of 5 means the price falls about 5% when rates rise 1 percentage point.',
         'Compares the rate risk of bonds and portfolios and matches the rate risk of assets and liabilities.',
         'It is a first-order approximation for small rate changes. For large moves, consider convexity as well.'))),
    Term('convexity', 'rates', ('convexity', '컨벡시티', '볼록성'), _t(
        ('컨벡시티(볼록성)', '금리에 따른 가격 곡선의 휘어진 정도',
         '가격-금리 곡선이 휘어진 정도로, 금리가 변할 때 듀레이션 자체가 얼마나 바뀌는지를 나타냅니다. 일반 채권은 볼록성이 양수라 '
         '금리가 크게 움직일 때 듀레이션만으로 계산한 것보다 가격이 덜 내리고 더 오릅니다.',
         '큰 금리 변화에서 듀레이션만으로 계산한 가격 변화를 보정합니다.',
         '2차 근사이므로 아주 큰 변화나 옵션이 들어 있는 채권에서는 정확도가 떨어집니다.'),
        ('Convexity', 'The curvature of the price–yield relationship',
         'How curved the price–yield relationship is, that is, how much duration itself changes as rates move. Plain '
         'bonds have positive convexity, so for large rate moves their price falls less and rises more than duration '
         'alone predicts.',
         'Corrects duration-only price estimates for large rate changes.',
         'It is a second-order approximation and loses accuracy for very large moves or bonds with embedded options.'))),
    Term('dv01', 'rates', ('DV01', 'PV01', 'BPV', '베이시스포인트', 'basis point value', '1bp'), _t(
        ('DV01', '금리 1bp 변화에 따른 가치 변화 금액',
         '금리가 1bp(0.01%p) 변할 때 포지션 가치가 바뀌는 금액입니다.',
         '서로 다른 채권·스왑의 금리 위험을 같은 금액 단위로 비교하고 헤지 수량을 정합니다.',
         '보통 모든 만기 금리가 똑같이 움직인다고 가정한 값입니다. 곡선 모양이 바뀌는 위험은 만기 구간별로 따로 봐야 합니다.'),
        ('DV01', 'The value change for a 1 basis-point move in rates',
         'The amount by which a position’s value changes when rates move by 1 basis point (0.01 percentage point).',
         'Compares the rate risk of different bonds and swaps in money terms and sizes hedges.',
         'It usually assumes every maturity moves by the same amount. Risk from changes in curve shape needs '
         'maturity-bucket measures.'))),
    Term('swap_rate', 'rates', ('IRS', '이자율스왑', '금리스왑', 'interest rate swap', '스왑', 'swap'), _t(
        ('스왑 금리', '이자율스왑에서 변동금리와 교환하는 고정금리',
         '이자율스왑(IRS)에서 변동금리와 교환하는 고정금리로, 계약 시점에 스왑의 가치가 0이 되도록 정해집니다.',
         '은행 간 자금 조달 비용과 금리 기대를 반영한 곡선을 만들고, 금리 위험을 헤지하는 데 씁니다.',
         '스왑 금리와 국채 금리의 차이(스왑 스프레드)는 신용과 수급에 따라 변합니다. 국채 곡선으로 스왑 금리를 대신하면 오차가 생깁니다.'),
        ('Swap rate', 'The fixed rate exchanged for a floating rate in an interest rate swap',
         'The fixed rate exchanged for a floating rate in an interest rate swap (IRS), set so the swap is worth zero at '
         'inception.',
         'Builds curves reflecting bank funding costs and rate expectations, and hedges interest rate risk.',
         'The gap between swap and government yields (the swap spread) moves with credit and supply and demand, so '
         'substituting a government curve introduces error.'))),
    Term('greeks', 'derivatives', ('greeks', '그릭스', '델타', 'delta', '감마', 'gamma', '베가', 'vega', '세타', 'theta',
                                   '옵션 민감도'), _t(
        ('그릭스 · 델타·감마·베가·세타', '옵션 가치의 위험 요인별 민감도',
         '옵션 가치가 기초자산 가격(델타), 델타의 변화(감마), 변동성(베가), 시간 경과(세타)에 얼마나 민감한지를 나타내는 값들입니다.',
         '옵션과 구조화 상품의 위험을 요인별로 나눠 보고 헤지 수량을 정합니다.',
         '현재 시점의 국소 민감도라 시장이 크게 움직이면 빠르게 바뀝니다. 가격 모형과 입력 변동성에 따라 값이 다릅니다.'),
        ('Greeks · delta, gamma, vega, theta', 'An option’s sensitivity to each risk factor',
         'How sensitive an option’s value is to the underlying price (delta), to changes in delta (gamma), to '
         'volatility (vega) and to the passage of time (theta).',
         'Breaks down the risk of options and structured products by factor and sizes hedges.',
         'They are local sensitivities that change quickly in large moves, and they depend on the pricing model and '
         'input volatility.'))),
    Term('implied_vol', 'derivatives', ('IV', 'implied volatility', '내재 변동성', '변동성 스마일', 'volatility smile'),
         _t(
        ('내재변동성', '옵션 시장 가격에서 거꾸로 풀어낸 변동성',
         '시장에서 거래되는 옵션 가격을 가격 모형에 넣고 거꾸로 풀어낸 변동성입니다.',
         '시장이 앞으로의 가격 변동을 얼마나 크게 보는지 가늠하고, 옵션 가격 수준을 서로 비교합니다.',
         '앞으로 실제로 나타날 변동성의 예측치가 아니며 위험 프리미엄과 수급이 함께 담깁니다. 행사가와 만기마다 값이 다릅니다(변동성 스마일).'),
        ('Implied volatility', 'The volatility backed out of an option’s market price',
         'The volatility that, entered into a pricing model, reproduces an option’s traded market price.',
         'Gauges how large the market expects future moves to be and compares option price levels.',
         'It is not a forecast of realized volatility; it includes risk premia and supply and demand, and it differs '
         'by strike and maturity (the volatility smile).'))),
    Term('sabr', 'derivatives', ('SABR', 'sabr model', '스마일', '스큐', 'smile', 'skew'), _t(
        ('SABR 모형', '행사가별 내재변동성 모양을 설명하는 확률변동성 모형',
         'α(변동성 수준), β(가격 수준과 변동성의 관계), ρ(가격과 변동성의 상관), ν(변동성의 변동성) 네 모수로 행사가에 따라 '
         '달라지는 내재변동성의 모양(스마일·스큐)을 설명하는 확률변동성 모형입니다.',
         '금리·외환 옵션에서 관측되지 않은 행사가의 변동성을 보간하고 가격을 매깁니다.',
         '모수 추정이 불안정할 수 있고, 금리가 아주 낮거나 행사가가 멀면 근사식이 비현실적인 값을 줄 수 있습니다.'),
        ('SABR model', 'A stochastic-volatility model of how implied volatility varies by strike',
         'A stochastic-volatility model whose four parameters, α (volatility level), β (link between price level and '
         'volatility), ρ (price–volatility correlation) and ν (volatility of volatility), describe the smile and skew '
         'of implied volatility across strikes.',
         'Interpolates volatility for unobserved strikes in rate and FX options and prices them.',
         'Calibration can be unstable, and the approximation can give unrealistic values at very low rates or far '
         'strikes.'))),
    Term('protected_note', 'derivatives', ('원금보장', '구조화 상품', '구조화상품', 'ELB', 'ELS', 'structured note',
                                           'principal protected', '참여율', 'participation rate'), _t(
        ('원금보장형 구조화 상품', '무이표채와 옵션을 결합해 원금을 지키며 상승분에 참여하는 상품',
         '무이표채(원금을 지키는 부분)와 옵션(수익에 참여하는 부분)을 결합해, 만기에 원금을 돌려주면서 기초자산 상승분의 일부(참여율)를 받도록 만든 상품입니다.',
         '상품 가치를 구성요소로 나눠 공정가치, 발행 마진, 참여율을 확인합니다.',
         '원금 보장은 발행자가 지급할 수 있을 때만 유효합니다(발행자 신용위험). 만기 전에 팔면 원금보다 낮을 수 있습니다.'),
        ('Principal-protected note', 'A zero-coupon bond plus an option: principal back at maturity with upside participation',
         'Combines a zero-coupon bond (protecting principal) with an option (participating in gains), repaying '
         'principal at maturity plus a share of the underlying’s rise (the participation rate).',
         'Splits the product into components to check fair value, issuer margin and participation.',
         'Protection holds only if the issuer can pay (issuer credit risk), and selling before maturity can return less '
         'than principal.'))),
    Term('fx_forward', 'fx', ('forward', '선물환율', '선도환율', 'forward rate', '스왑포인트', 'forward points',
                              '이자율 평형', 'interest rate parity'), _t(
        ('선물환', '미래에 미리 정한 환율로 통화를 교환하는 계약',
         '미래의 정한 날짜에 미리 약속한 환율로 통화를 교환하는 계약입니다. 선물환율은 현물환율에 두 통화의 금리 차이를 반영해 정해집니다(이자율 평형).',
         '수출입 대금이나 해외투자의 환율 위험을 헤지하고, 두 통화의 금리 차이를 확인합니다.',
         '선물환율은 미래 현물환율의 예측치가 아닙니다. 실제 시장 가격은 통화 베이시스 때문에 이론값과 다를 수 있습니다.'),
        ('FX forward', 'A contract to exchange currencies at a rate fixed today for a future date',
         'A contract to exchange currencies on a future date at a rate agreed today. The forward rate reflects the spot '
         'rate and the interest rate difference between the two currencies (interest rate parity).',
         'Hedges currency risk on trade payments or foreign investments and shows the rate differential between the '
         'currencies.',
         'A forward rate is not a forecast of the future spot rate, and market prices can differ from theory because '
         'of the cross-currency basis.'))),
    Term('carry', 'fx', ('carry trade', '캐리 트레이드', '금리차', 'rate differential'), _t(
        ('캐리', '가격이 그대로일 때 보유만으로 얻거나 내는 수익',
         '가격이 변하지 않는다고 가정할 때 포지션을 보유해 얻는(또는 내는) 이자·배당 등의 수익입니다.',
         '금리가 높은 통화나 자산을 보유할 때의 수익원을 가격 변동 수익과 나눠 봅니다.',
         '가격이 불리하게 움직이면 쌓인 캐리 수익을 한 번에 잃을 수 있고, 위기 때는 한꺼번에 청산되기도 합니다.'),
        ('Carry', 'The return from simply holding a position if prices stay unchanged',
         'The income earned, or paid, from holding a position, such as interest or dividends, if prices do not change.',
         'Separates the income from holding higher-yielding currencies or assets from returns due to price moves.',
         'An adverse price move can erase accumulated carry at once, and crowded positions can unwind abruptly in a '
         'crisis.'))),
    Term('q_score', 'app', ('Q-SCORE', 'qscore', 'q score', '큐스코어', '별점'), _t(
        ('Q-SCORE', '가격 추세·모멘텀·변동성·하락 위험을 하나의 별점으로 정리한 실험적 연구 지표',
         'QUANTGEN의 기술신호·위험분석 엔진이 가격 추세, 모멘텀, 변동성, 하락 위험을 함께 살펴 하나의 별점으로 정리한 실험적 연구 지표입니다.',
         '종목마다 다른 가격 흐름과 과거 위험을 같은 기준으로 비교하는 출발점으로 씁니다.',
         '예측력이 검증되지 않았습니다. 기업가치 평가나 매수·매도 추천, 수익 보장이 아닙니다.'),
        ('Q-SCORE', 'An experimental research rating combining trend, momentum, volatility and downside risk',
         'An experimental research indicator in which QUANTGEN’s technical-signal and risk-analysis engines examine '
         'price trend, momentum, volatility and downside risk together and summarize them as a star rating.',
         'A starting point for comparing different stocks’ price behaviour and past risk on one basis.',
         'Its predictive power is unvalidated. It is not a fundamental valuation, a buy or sell recommendation or a '
         'guarantee of returns.'))),
)
BY_KEY = {term.key: term for term in TERMS}

from core.search_text import INITIALS as _INITIALS, best_score as _best_score, normal as _normal


def _language(ctx):
    return 'ko' if getattr(ctx, 'language', ctx) == 'ko' else 'en'


def name(key, ctx):
    if key in INDICATOR_KEYS:
        return ctx.t(key)
    return BY_KEY[key].text[_language(ctx)]['name']


def category(key, ctx):
    return ctx.t('cat_' + BY_KEY[key].category)


def summary(key, ctx):
    if key in INDICATOR_KEYS:
        text = ctx.t(key + '_meaning')
        end = text.find('. ')
        return text if end < 0 else text[:end + 1]
    return BY_KEY[key].text[_language(ctx)]['summary']


def sections(key, ctx):
    """Ordered (heading, text) pairs for the detail panel and the term side panel."""
    if key in INDICATOR_KEYS:
        return tuple((ctx.t(field), ctx.t(key + '_' + field)) for field in INDICATOR_FIELDS)
    text = BY_KEY[key].text[_language(ctx)]
    return ((ctx.t('meaning'), text['meaning']), (ctx.t('glossary_use'), text['use']),
            (ctx.t('limit'), text['limit']))


def _names(term, messages):
    if term.key in INDICATOR_KEYS:
        found = [messages[language][term.key] for language in ('ko', 'en')]
    else:
        found = [term.text[language]['name'] for language in ('ko', 'en')]
    return (*found, term.key, *term.aliases)


def _bodies(term, messages):
    if term.key in INDICATOR_KEYS:
        return tuple(messages[language][term.key + '_meaning'] for language in ('ko', 'en'))
    return tuple(term.text[language][field] for language in ('ko', 'en') for field in ('summary', 'meaning'))


def _body_pattern(wanted, query):
    """Definitions match Hangul anywhere (2+ letters) and Latin only at word starts (3+)."""
    if wanted.isascii():
        if len(wanted) < 3:
            return None
        return re.compile(r'(?<![0-9a-z])' + re.escape(' '.join(str(query).casefold().split())))
    return wanted if len(wanted) >= 2 else None


def _body_match(pattern, bodies):
    if pattern is None:
        return False
    if isinstance(pattern, str):
        return any(pattern in _normal(body) for body in bodies)
    return any(pattern.search(unicodedata.normalize('NFC', body).casefold()) for body in bodies)


def search(query, limit=8):
    """Matching keys, best first; Korean and English names match whatever the UI language.

    Exact names beat prefixes, prefixes beat substrings, and Hangul initial consonants
    (e.g. 'ㅂㄹㅈ' for 볼린저) match like prefixes. Definitions are searched last.
    """
    from core.ui_messages import MESSAGES
    wanted = _normal(query)
    if not wanted:
        return ()
    jamo = all(char in _INITIALS for char in wanted)
    body_pattern = None if jamo else _body_pattern(wanted, query)
    scored = []
    for order, term in enumerate(TERMS):
        best = _best_score(wanted, _names(term, MESSAGES))
        if best is None and not jamo and _body_match(body_pattern, _bodies(term, MESSAGES)):
            best = 4
        if best is not None:
            scored.append((best, order, term.key))
    return tuple(key for _, _, key in sorted(scored)[:max(0, int(limit))])
