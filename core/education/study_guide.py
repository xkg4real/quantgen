"""Plain-language guide for the market-chart studies (core.education.indicators.STUDIES).

For every study: what it is, how to read it and a caution, in Korean and English,
plus a reading of its value at one bar for beginners. Conventional thresholds are
named as conventions; nothing here forecasts prices or advises buying or selling.
Pure functions over Bars and computed values; no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re

import numpy as np

from core.education.indicators import (CATEGORY_NAMES, Bars, Supply, availability, compute_study,
                                       parabolic_sar_trend, reading_lines, rsi_line, session_start_index, study,
                                       warmup)

FIELDS = ('what', 'how', 'caution')
DISCLAIMER = {
    'ko': '지표는 이미 일어난 가격과 거래량을 요약한 것입니다. 앞으로의 가격을 예측하거나 매매를 권하지 않습니다.',
    'en': 'Indicators summarise prices and volume that already happened. They neither forecast prices nor recommend trades.',
}
PARAM_NAMES = {
    'period': ('기간', 'period'), 'fast': ('빠른 기간', 'fast'), 'slow': ('느린 기간', 'slow'),
    'signal': ('신호선', 'signal'), 'conversion': ('전환선', 'conversion'), 'base': ('기준선', 'base'),
    'span_b': ('선행스팬 2', 'span B'), 'displacement': ('선행·후행 거리', 'displacement'),
    'step': ('가속 단계', 'step'), 'maximum': ('최대 가속', 'maximum'), 'percent': ('폭 %', 'width %'),
    'multiplier': ('ATR 배수', 'ATR multiple'), 'atr_period': ('ATR 기간', 'ATR period'),
    'k_smooth': ('%K 평균', '%K smoothing'), 'd_smooth': ('%D 평균', '%D smoothing'),
    'rsi_period': ('RSI 기간', 'RSI period'), 'constant': ('상수', 'constant'),
    'deviations': ('표준편차 배수', 'deviations'),
}
AVAILABILITY = {
    'intraday_only': ('VWAP는 하루 안의 거래로 계산하므로 분봉 차트에서만 표시합니다.',
                      'VWAP is computed within one trading day, so it is shown on intraday charts only.'),
    'needs_volume': ('이 종목·주기는 거래량 자료가 없어 계산할 수 없습니다.',
                     'This chart has no reported volume, so the study cannot be computed.'),
    'domestic_daily_only': ('국내 주식 일봉 차트에서만 볼 수 있습니다(한국투자증권 수급 자료).',
                            'Available on daily charts of Korean stocks only (KIS supply and demand data).'),
    'no_supply_data': ('수급 자료를 아직 받지 못했습니다. 한국투자증권(KIS) 연결이 설정되어 있어야 합니다.',
                       'Supply and demand data has not been received. A KIS connection must be configured.'),
}
# Short forms for a chart label.
AVAILABILITY_SHORT = {
    'intraday_only': ('분봉 전용', 'intraday charts only'),
    'needs_volume': ('거래량 자료 없음', 'no volume data'),
    'domestic_daily_only': ('국내 주식 일봉 전용', 'Korean stocks, daily charts only'),
    'no_supply_data': ('수급 자료 없음 · KIS 연결 필요', 'no supply data · KIS connection needed'),
}

# key: ((what, how, caution) in Korean, (what, how, caution) in English)
GUIDE = {
    'sma': (
        ('최근 20개 봉(일봉이면 20거래일) 종가의 단순 평균을 이은 선입니다. 들쭉날쭉한 가격을 부드럽게 만들어 큰 방향을 보여줍니다.',
         '가격이 선 위에 있으면 최근 평균보다 높게, 아래에 있으면 낮게 거래되고 있다는 뜻입니다. 선이 오르막이면 평균 가격이 오르는 중입니다.',
         '평균선은 이미 지난 가격으로 만들어져 늘 한발 늦습니다. 옆으로 움직이는 장에서는 가격이 선을 자주 넘나듭니다.'),
        ('A line joining the plain average of the last 20 closes (20 sessions on a daily chart). It smooths the zigzags to show the broader direction.',
         'Price above the line trades higher than its recent average; below, lower. A rising line means the average price is climbing.',
         'An average is built from past prices, so it always lags. In sideways markets price crosses it back and forth.')),
    'ema': (
        ('최근 가격에 더 큰 비중을 둔 평균선입니다. 빠른 선(12)과 느린 선(26)을 함께 그립니다.',
         '빠른 선이 느린 선 위에 있으면 최근 흐름이 더 긴 흐름보다 강하다는 뜻입니다. 두 선의 교차는 흐름이 바뀐 결과를 보여줍니다.',
         '단순 평균보다 빨리 반응하는 만큼 잡음에도 쉽게 흔들립니다.'),
        ('Averages that give recent prices more weight, drawn as a fast line (12) and a slow line (26).',
         'The fast line above the slow line means the recent move is stronger than the longer one. A crossing shows a change that has already happened.',
         'Reacting faster than a simple average also means reacting to more noise.')),
    'macd': (
        ('빠른 지수평균(12)에서 느린 지수평균(26)을 뺀 값입니다. 신호선은 그 값의 9개 봉 지수평균, 막대는 둘의 차이입니다.',
         '0선 위면 단기 평균이 장기 평균보다 높은 상태입니다. MACD가 신호선 위에 있으면(막대가 위쪽) 최근 오름 속도가 붙는 쪽으로 읽습니다.',
         '가격 단위에 따라 숫자 크기가 달라 다른 종목과 그대로 비교할 수 없습니다. 횡보장에서는 교차가 잦습니다.'),
        ('The fast exponential average (12) minus the slow one (26). The signal line is its 9-bar exponential average; the bars are the difference.',
         'Above zero, the short average is above the long one. MACD above its signal line (bars above zero) reads as upward momentum building.',
         'Its size depends on the price scale, so do not compare it across instruments. Sideways markets produce frequent crossings.')),
    'ichimoku': (
        ('일본에서 만든 추세 지표로 전환선(9)·기준선(26)·후행스팬과, 두 선행스팬 사이의 구름으로 이루어집니다. 선행스팬은 현재 봉을 포함해 26번째 봉 위치(오른쪽으로 25봉)에, 후행스팬은 같은 거리만큼 왼쪽에 그립니다.',
         '가격이 구름 위면 상승 흐름, 아래면 하락 흐름, 구름 안이면 방향이 뚜렷하지 않은 구간으로 보는 것이 관례입니다. 처음에는 전환선과 기준선의 위아래부터 보세요.',
         '선이 많아 처음엔 복잡합니다. 마지막 봉 오른쪽으로 뻗는 미래 구름은 이 차트에 그리지 않습니다.'),
        ('A Japanese trend study: conversion line (9), base line (26), lagging span and a cloud between two leading spans. Leading spans are drawn on the 26th bar counting the current one (25 bars right); the lagging span the same distance left.',
         'By convention, price above the cloud reads as an uptrend, below as a downtrend, and inside as no clear direction. Start with which of the conversion and base lines is on top.',
         'There are many lines at first. The future cloud to the right of the last bar is not drawn on this chart.')),
    'psar': (
        ('가격 위나 아래에 점을 찍어 지금의 흐름을 따라가는 지표입니다. 흐름이 길어질수록 점이 가격에 빠르게 다가갑니다(가속 0.02씩, 최대 0.2).',
         '점이 가격 아래에 있으면 상승 흐름, 위에 있으면 하락 흐름을 따라가는 중입니다. 가격이 점에 닿으면 점이 반대편으로 넘어갑니다.',
         '옆으로 움직이는 장에서는 점이 자주 뒤집힙니다. 흐름이 뚜렷한 구간에서 읽기 쉬운 도구입니다.'),
        ('Dots above or below price that trail the current move. The longer the move, the faster the dots close in (step 0.02, maximum 0.2).',
         'Dots below price trail an upward move; dots above trail a downward move. When price touches the dots they flip to the other side.',
         'In sideways markets the dots flip often. It is easiest to read when a move is clear.')),
    'adx': (
        ('ADX는 방향과 상관없이 추세가 얼마나 뚜렷한지를 0~100으로, +DI와 −DI는 오르는 힘과 내리는 힘을 보여줍니다(14개 봉, Wilder 방식).',
         'ADX가 25 이상이면 추세가 뚜렷하다고, 20 아래면 뚜렷한 추세가 없다고 보는 관례가 있습니다. 방향은 +DI와 −DI 중 어느 쪽이 위인지로 봅니다.',
         'ADX가 높다는 것은 추세가 강하다는 뜻일 뿐 오른다는 뜻이 아닙니다. 하락 추세에서도 ADX는 올라갑니다.'),
        ('ADX shows how clear a trend is on a 0 to 100 scale, whatever its direction; +DI and −DI show the upward and downward pressure (14 bars, Wilder).',
         'By convention ADX of 25 or more marks a clear trend and below 20 no clear trend. The direction is whichever of +DI and −DI is on top.',
         'A high ADX means a strong trend, not a rising price. ADX also rises in downtrends.')),
    'envelope': (
        ('20개 봉 이동평균의 위아래 5% 지점에 선을 그린 띠입니다.',
         '가격이 위 선 근처면 평균보다 5% 가까이 올라 있고, 아래 선 근처면 5% 가까이 내려 있다는 뜻입니다.',
         '5%는 정해진 규칙이 아니라 흔히 쓰는 기본값입니다. 변동이 큰 종목은 띠를 자주 벗어납니다.'),
        ('A band drawn 5% above and below the 20-bar moving average.',
         'Price near the upper line is about 5% above its average; near the lower line, about 5% below.',
         'Five percent is a common default, not a rule. Volatile instruments leave the band often.')),
    'keltner': (
        ('20개 봉 지수평균을 중심으로, 평균 변동폭(ATR 10)의 2배만큼 위아래에 그린 띠입니다.',
         '띠 위로 나가면 평소 변동폭에 비해 크게 올랐다는 뜻, 아래로 나가면 크게 내렸다는 뜻입니다.',
         '가격이 띠 밖에 오래 머물 수 있습니다. 띠를 벗어난 것 자체가 되돌림을 뜻하지는 않습니다.'),
        ('A band around the 20-bar exponential average, two average true ranges (ATR 10) above and below.',
         'Leaving the band upward means a large rise for the usual range; downward, a large fall.',
         'Price can stay outside for a long time. Leaving the band does not by itself mean a pullback.')),
    'donchian': (
        ('최근 20개 봉(현재 봉 포함)의 최고가와 최저가를 이은 띠입니다. 가운데 선은 둘의 중간입니다.',
         '가격이 위 선에 닿으면 20개 봉 중 최고가와 같거나 새로 쓴 것이고, 아래 선에 닿으면 최저가와 같거나 새로 쓴 것입니다.',
         '최고가·최저가를 새로 썼다고 그 방향으로 계속 간다는 보장은 없습니다.'),
        ('A band joining the highest high and lowest low of the last 20 bars (current bar included), with their midpoint.',
         'Touching the upper line matches or sets a 20-bar high; touching the lower line matches or sets a 20-bar low.',
         'A new high or low does not guarantee the move continues.')),
    'rsi': (
        ('최근 14개 봉 동안 오른 폭과 내린 폭을 비교해 0~100으로 나타낸 값입니다(Wilder 방식).',
         '50보다 높으면 오른 폭이 더 컸고, 낮으면 내린 폭이 더 컸습니다. 70 이상은 과매수, 30 이하는 과매도라고 부르는 관례가 있습니다.',
         '강한 상승장에서는 RSI가 70 위에 오래 머물 수 있습니다. 과매수는 많이 올랐다는 뜻이지 곧 떨어진다는 뜻이 아닙니다.'),
        ('Compares the size of rises and falls over the last 14 bars on a 0 to 100 scale (Wilder).',
         'Above 50 the rises were larger; below 50 the falls were. By convention 70 or more is called overbought and 30 or less oversold.',
         'In strong rallies RSI can stay above 70 for long. Overbought means it rose a lot, not that it is about to fall.')),
    'stoch': (
        ('지금 종가가 최근 14개 봉의 최고가·최저가 범위에서 어디쯤인지를 0~100으로 나타냅니다. %K는 3개 봉 평균, %D는 %K의 3개 봉 평균입니다.',
         '100에 가까우면 최근 몇 봉의 종가가 범위 꼭대기 근처, 0에 가까우면 바닥 근처에서 마감했다는 뜻입니다. 80 이상을 과매수, 20 이하를 과매도로 부르는 관례가 있습니다.',
         '범위 안의 위치일 뿐 가격이 싸거나 비싸다는 판정이 아닙니다. 추세가 강하면 한쪽 끝에 오래 붙어 있습니다.'),
        ('Where the close sits within the high-low range of the last 14 bars, 0 to 100. %K is a 3-bar average and %D a 3-bar average of %K.',
         'Near 100 the recent closes finished near the top of the range; near 0, near the bottom. By convention 80 or more is overbought and 20 or less oversold.',
         'It is a position in a range, not a verdict that price is cheap or dear. In strong trends it stays at one end.')),
    'stochrsi': (
        ('RSI 값에 스토캐스틱을 한 번 더 적용한 지표입니다. 지금 RSI가 최근 14개 봉 RSI 범위의 어디쯤인지 0~100으로 보여줍니다.',
         '80 이상이면 RSI가 최근 범위 꼭대기 근처, 20 이하면 바닥 근처라는 뜻으로 읽는 것이 관례입니다.',
         'RSI보다 훨씬 민감해 0과 100 사이를 자주 오갑니다. 다른 지표와 함께 보조로 보는 것이 일반적입니다.'),
        ('A stochastic applied to RSI: where today’s RSI sits within its own 14-bar range, 0 to 100.',
         'By convention 80 or more reads as RSI near the top of its recent range and 20 or less near the bottom.',
         'It is far more sensitive than RSI and swings between 0 and 100 often. It is usually read alongside other studies.')),
    'cci': (
        ('평균가격(고가·저가·종가의 평균)이 20개 봉 평균에서 얼마나 떨어져 있는지를 평소 벗어나는 정도와 비교한 값입니다.',
         '+100 위면 평소보다 크게 위로, −100 아래면 크게 아래로 벗어난 상태로 보는 관례가 있습니다. 0 근처는 평균 가까이에 있다는 뜻입니다.',
         '위아래 한계가 없어 강한 추세에서는 ±200을 넘기도 합니다.'),
        ('How far the typical price (mean of high, low and close) is from its 20-bar average, compared with its usual deviation.',
         'By convention above +100 is an unusually large move up and below −100 down. Near 0 price is close to its average.',
         'It has no upper or lower limit and passes ±200 in strong trends.')),
    'williams': (
        ('지금 종가가 최근 14개 봉 최고가에서 얼마나 내려와 있는지를 0~−100으로 나타냅니다. 스토캐스틱을 뒤집어 놓은 모양입니다.',
         '−20 위(0에 가까움)면 범위 꼭대기 근처, −80 아래면 바닥 근처에서 마감했다는 뜻이며 각각 과매수·과매도로 부르는 관례가 있습니다.',
         '범위 안의 위치일 뿐입니다. 추세가 강하면 한쪽 끝에 오래 머뭅니다.'),
        ('How far the close is below the highest high of the last 14 bars, from 0 to −100: a stochastic turned upside down.',
         'Above −20 (near 0) the bar closed near the top of the range; below −80 near the bottom. By convention these are called overbought and oversold.',
         'It is only a position in a range. In strong trends it stays at one end.')),
    'roc': (
        ('지금 종가가 12개 봉 전 종가보다 몇 % 변했는지 보여줍니다.',
         '0 위면 12개 봉 전보다 올랐고 0 아래면 내렸습니다. 0에서 멀수록 변화가 컸습니다.',
         '비교하는 시작점 하루의 가격에 따라 값이 크게 달라질 수 있습니다.'),
        ('The percent change of the close from 12 bars ago.',
         'Above 0 price is higher than 12 bars ago; below 0, lower. The further from 0, the larger the change.',
         'The value depends heavily on the single starting price it compares with.')),
    'disparity': (
        ('지금 종가가 20개 봉 이동평균의 몇 %인지 나타냅니다(종가 ÷ 이동평균 × 100). 국내에서 많이 쓰는 지표입니다.',
         '100이면 평균과 같고 105면 평균보다 5% 위입니다. 20일 이격도는 흔히 105 이상을 과열, 95 이하를 침체로 보는 관례가 있습니다.',
         '알맞은 기준은 종목의 변동성에 따라 다릅니다. 기준을 넘었다고 곧 평균으로 돌아온다는 보장은 없습니다.'),
        ('The close as a percent of its 20-bar moving average (close ÷ average × 100), widely used in Korea.',
         '100 equals the average; 105 is 5% above it. For the 20-day version 105 or more is conventionally called overheated and 95 or less depressed.',
         'Sensible levels depend on the instrument’s volatility. Crossing a level does not mean a return to the average.')),
    'psychology': (
        ('최근 10개 봉 가운데 앞 봉보다 오른 봉이 몇 %인지 나타냅니다(국내에서 많이 쓰는 투자심리선).',
         '75% 이상이면 오른 봉이 대부분이라 과열, 25% 이하면 내린 봉이 대부분이라 침체로 보는 관례가 있습니다.',
         '오르내린 횟수만 세고 크기는 보지 않습니다. 조금 오른 날도 크게 오른 날과 똑같이 셉니다.'),
        ('The share of the last 10 bars that closed above the previous bar (the psychological line, popular in Korea).',
         'By convention 75% or more, mostly up bars, is called overheated and 25% or less, mostly down bars, depressed.',
         'It counts rises, not their size: a small rise counts the same as a large one.')),
    'bb': (
        ('20개 봉 평균을 중심으로, 같은 기간 가격이 흩어진 정도(표준편차)의 2배만큼 위아래로 그린 띠입니다.',
         '가격이 위 밴드에 가까우면 최근 범위의 위쪽, 아래 밴드에 가까우면 아래쪽에 있다는 뜻입니다. 띠가 좁아지면 가격 움직임이 잦아든 것입니다.',
         '밴드 밖으로 나간 가격은 한동안 그 밖에서 움직일 수 있습니다. 이 띠는 미래 가격의 범위를 약속하지 않습니다.'),
        ('A band two standard deviations of the last 20 closes above and below their average.',
         'Price near the upper band sits high in its recent range; near the lower band, low. A narrowing band means price movement has calmed.',
         'Price can keep moving outside a band for a while. The band does not promise a range for future prices.')),
    'atr': (
        ('한 봉 동안 가격이 평균적으로 얼마나 움직였는지를 가격 단위로 보여줍니다. 앞 봉 종가와의 갭도 포함합니다(14개 봉, Wilder 방식).',
         '숫자가 클수록 출렁임이 크다는 뜻입니다. 종가 대비 %로 바꿔 보면 다른 종목과 비교하기 쉽습니다.',
         '방향은 알려주지 않습니다. 크게 오를 때와 크게 내릴 때 모두 커집니다.'),
        ('How much price typically moved in one bar, in price units, including gaps from the previous close (14 bars, Wilder).',
         'Larger means bigger swings. As a percent of the close it is easier to compare across instruments.',
         'It has no direction: it grows in sharp rises and sharp falls alike.')),
    'percent_b': (
        ('종가가 볼린저 밴드(20개 봉, 2배)의 어디에 있는지를 숫자로 나타냅니다. 0은 아래 밴드, 0.5는 가운데, 1은 위 밴드입니다.',
         '1보다 크면 위 밴드 밖, 0보다 작으면 아래 밴드 밖에 있다는 뜻입니다.',
         '밴드 밖으로 나갔다고 곧 안으로 돌아온다는 보장은 없습니다.'),
        ('Where the close sits in the Bollinger band (20 bars, 2 deviations): 0 is the lower band, 0.5 the middle, 1 the upper band.',
         'Above 1 the close is outside the upper band; below 0, outside the lower band.',
         'Outside the band does not mean it will soon return inside.')),
    'bandwidth': (
        ('볼린저 밴드의 위아래 폭이 가운데 선의 몇 %인지 보여줍니다.',
         '값이 작아지면 가격 움직임이 잦아든 것이고 커지면 움직임이 커진 것입니다. 아주 좁아진 상태를 스퀴즈라고 부르는 관례가 있습니다.',
         '폭은 움직임의 크기만 알려줄 뿐 방향은 알려주지 않습니다.'),
        ('The distance between the Bollinger bands as a percent of the middle line.',
         'Falling values mean price movement has calmed; rising values, that it has grown. A very narrow band is conventionally called a squeeze.',
         'Width tells you the size of movement, never its direction.')),
    'volume_ma': (
        ('최근 20개 봉 거래량의 평균을 거래량 막대 위에 선으로 그립니다.',
         '막대가 선보다 길면 평소보다 거래가 많았던 봉입니다. 가격이 크게 움직인 날 거래도 함께 많았는지 확인할 때 봅니다.',
         '아직 끝나지 않은 마지막 봉은 거래가 쌓이는 중이라 막대가 작게 보일 수 있습니다.'),
        ('The average volume of the last 20 bars, drawn as a line over the volume bars.',
         'A bar taller than the line traded more than usual. Use it to check whether a large price move came with heavy trading.',
         'The last, still-forming bar is accumulating trades and can look small.')),
    'obv': (
        ('오른 봉의 거래량은 더하고 내린 봉의 거래량은 빼서 누적한 값입니다(이 차트의 첫 봉을 0으로 시작).',
         '숫자 자체보다 방향을 봅니다. OBV가 오르면 오른 봉의 거래가 더 많았다는 뜻입니다.',
         '시작점에 따라 숫자가 달라지므로 다른 종목이나 기간과 값을 비교하지 않습니다. 거래량을 모르는 봉은 비워 둡니다.'),
        ('A running total that adds volume on up bars and subtracts it on down bars (starting from 0 at this chart’s first bar).',
         'Read its direction, not its level. A rising OBV means more volume traded on up bars.',
         'Its level depends on the starting bar, so do not compare values across instruments or periods. Bars with unknown volume are left blank.')),
    'mfi': (
        ('거래량을 반영한 RSI입니다. 최근 14개 봉 동안 평균가격이 오른 봉과 내린 봉의 거래대금을 비교해 0~100으로 나타냅니다.',
         '80 이상은 돈이 오르는 쪽으로 많이 몰렸다(과매수), 20 이하는 내리는 쪽으로 많이 몰렸다(과매도)고 보는 관례가 있습니다.',
         '가격 × 거래량으로 계산한 추정치이며 실제로 누가 샀고 팔았는지는 알려주지 않습니다.'),
        ('A volume-weighted RSI: money flow on bars whose typical price rose versus fell over the last 14 bars, 0 to 100.',
         'By convention 80 or more means money flowed heavily into rising bars (overbought) and 20 or less into falling bars (oversold).',
         'It is an estimate from price times volume and does not show who actually bought or sold.')),
    'vwap': (
        ('오늘 장 시작부터 지금까지 거래된 가격을 거래량으로 가중 평균한 값입니다. 분봉 차트에서만 계산하며 날짜가 바뀌면 다시 시작합니다.',
         '현재가가 VWAP 위면 오늘 거래된 평균 단가보다 높게, 아래면 낮게 거래되고 있다는 뜻입니다.',
         '장 초반에는 거래가 적어 VWAP가 크게 흔들립니다. 일봉 이상의 차트에는 표시하지 않습니다.'),
        ('The average price traded today, weighted by volume, from the open until now. Computed on intraday charts only; it restarts each day.',
         'Price above VWAP trades above today’s average traded price; below, under it.',
         'Early in the session few trades make it jumpy. It is not shown on daily or longer charts.')),
    'investor_flow': (
        ('외국인·기관·개인이 하루 동안 산 주식 수에서 판 주식 수를 뺀 값(순매수)을 차트 기간 동안 누적한 선입니다. 한국투자증권(KIS) 자료이며 국내 주식 일봉에서만 볼 수 있습니다.',
         '선이 오르면 그 투자자가 산 양이 많았고, 내리면 판 양이 많았다는 뜻입니다. 누가 꾸준히 사고 누가 파는지 비교해 보세요.',
         '순매수는 이미 끝난 거래의 기록입니다. 누군가 샀다는 사실이 가격이 오른다는 뜻은 아니며, 장중 수치는 장 마감 후 확정치와 다를 수 있습니다.'),
        ('Shares bought minus shares sold (net buying) by foreign, institutional and individual investors, added up over the chart. KIS data, Korean stocks on daily charts only.',
         'A rising line means that group bought more than it sold; a falling line, the reverse. Compare who keeps buying and who keeps selling.',
         'Net buying records trades that are over. Someone buying does not mean the price will rise, and intraday figures can differ from the final ones.')),
    'short_ratio': (
        ('그날 거래량 가운데 공매도(빌린 주식을 판 거래)가 차지한 비율입니다. 한국투자증권(KIS) 자료이며 국내 주식 일봉에서만 볼 수 있습니다.',
         '비율이 평소보다 높으면 하락에 대비하거나 위험을 줄이려는 거래가 늘었다는 뜻일 수 있습니다. 최근 평균과 비교해 보세요.',
         '공매도는 헤지 등 여러 이유로 이뤄집니다. 비율이 높다고 주가가 떨어진다는 뜻은 아닙니다.'),
        ('The share of the day’s volume that was short selling (selling borrowed shares). KIS data, Korean stocks on daily charts only.',
         'A higher share than usual can mean more trading to hedge or to bet on a fall. Compare it with the recent average.',
         'Short selling happens for many reasons, including hedging. A high share does not mean the price will fall.')),
}


@dataclass(frozen=True)
class StudyGuide:
    key: str
    name: str
    category: str
    params: str
    what: str
    how: str
    caution: str


def _lang(language):
    return 'ko' if str(language or '').lower().startswith('ko') else 'en'


def category_name(category, language='ko'):
    return CATEGORY_NAMES[category][0 if _lang(language) == 'ko' else 1]


def params_text(key, language='ko', **params):
    """'기간 14 · %K 평균 3 · %D 평균 3' style text of the (default) parameters."""
    spec = study(key)
    values = {**spec.defaults, **params}
    index = 0 if _lang(language) == 'ko' else 1
    return ' · '.join(f'{PARAM_NAMES[name][index]} {_plain(values[name])}' for name, _ in spec.params)


def guide(key, language='ko'):
    """Name, category, parameters and the one-line what / how / caution of a study."""
    spec = study(key)
    lang = _lang(language)
    what, how, caution = GUIDE[spec.key][0 if lang == 'ko' else 1]
    return StudyGuide(spec.key, spec.name(lang), category_name(spec.category, lang), params_text(spec.key, lang),
                      what, how, caution)


def availability_text(code, language='ko'):
    return AVAILABILITY[code][0 if _lang(language) == 'ko' else 1] if code else ''


def availability_short(code, language='ko'):
    return AVAILABILITY_SHORT[code][0 if _lang(language) == 'ko' else 1] if code else ''


def disclaimer(language='ko'):
    return DISCLAIMER[_lang(language)]


# Number formatting -------------------------------------------------------------------
_NEGATIVE = re.compile(r'(?<![\w.])-(?=\d)')


def _minus(text):
    """Typographic minus (U+2212) for negative numbers, as the chart labels use."""
    return _NEGATIVE.sub('\u2212', text)


def _plain(value):
    return f'{value:g}' if isinstance(value, float) else str(value)


def _trim(text):
    return text.rstrip('0').rstrip('.') if '.' in text else text


def format_value(kind, value, language='ko'):
    """Display text for one study value; '—' when it is not available."""
    if value is None or not math.isfinite(float(value)):
        return '—'
    value = float(value)
    if kind == 'index':
        return _minus(f'{value:.1f}')
    if kind == 'percent':
        return _minus(f'{value:.1f}%')
    if kind == 'ratio':
        return _minus(f'{value:.2f}')
    if kind == 'quantity':
        return _quantity(value, language)
    if abs(value) >= 1:
        return _minus(_trim(f'{value:,.2f}'))
    return _minus(f'{value:.4g}')


def _quantity(value, language='ko', signed=False):
    sign = '+' if signed and value > 0 else '−' if value < 0 else ''
    size = abs(value)
    if _lang(language) == 'ko':
        if size >= 1e8:
            text = _trim(f'{size / 1e8:,.1f}') + '억'
        elif size >= 1e4:
            text = _trim(f'{size / 1e4:,.1f}') + '만'
        else:
            text = f'{size:,.0f}'
    else:
        text = f'{size:,.0f}'
    return sign + text


def _price(value):
    return format_value('price', value)


# Units by bar interval -----------------------------------------------------------------
_UNITS = {'1d': ('일', 'days', '거래일', '전날', 'day'), '1w': ('주', 'weeks', '주', '전주', 'week'),
          '1M': ('개월', 'months', '개월', '전달', 'month')}


class _Say:
    """Language and bar-interval wording for one reading."""

    def __init__(self, bars, language):
        self.lang = _lang(language)
        self.ko = self.lang == 'ko'
        unit = _UNITS.get(getattr(bars, 'interval', ''), None)
        self.daily = unit is not None
        self.unit = unit or ('개 봉', 'bars', '개 봉', '앞 봉', 'bar')

    def n(self, count):
        """'14일' / '14개 봉' / '14 days' / '14 bars'."""
        return f'{count}{self.unit[0]}' if self.ko else f'{count} {self.unit[1]}'

    def count_subject(self, count):
        """'7일이' / '7주가' / '7개 봉이' (Korean subject particle after the counter)."""
        return f'{count}{self.unit[0]}' + ('가' if self.unit[0] == '주' else '이')

    def ago(self, count):
        return f'{count}{self.unit[0]} 전' if self.ko else f'{count} {self.unit[1]} ago'

    def avg(self, count):
        """'20일 평균' / '20-day average'."""
        return f'{count}{self.unit[0]} 평균' if self.ko else f'{count}-{self.unit[4]} average'

    def __call__(self, ko, en):
        return ko if self.ko else en


def _at(values, line, index):
    value = float(values[line][index]) if 0 <= index < len(values[line]) else math.nan
    return value if math.isfinite(value) else None


def _pct(a, b):
    return (a / b - 1) * 100 if b else math.nan


def _shown(value, digits=1):
    """`value` as it is displayed with `digits` decimals ('-0.0' shows as 0.0). Readings
    choose their words from this, so the text never contradicts the printed number."""
    return float(f'{value:.{digits}f}') + 0.0


def _fmt(value, digits=1, sign=False):
    """The displayed number: rounded once, never '-0', '+' only on a positive value."""
    shown = _shown(value, digits)
    return f'{shown:{"+" if sign and shown > 0 else ""}.{digits}f}'


def _side(value, digits=1):
    """1 / -1 by the sign of the displayed value; 0 when it displays as zero."""
    shown = _shown(value, digits)
    return (shown > 0) - (shown < 0)


def _ratio(x):
    """For a 0-100 balance index (RSI, MFI): (larger side ÷ smaller side as displayed, its text).
    One side at zero gives (inf, '')."""
    if x >= 100 or x <= 0:
        return math.inf, ''
    ratio = x / (100 - x) if x >= 50 else (100 - x) / x
    text = f'{ratio:.1f}' if ratio < 9.95 else f'{ratio:,.0f}'
    return float(text.replace(',', '')), text


def _degree(ratio):
    """How much larger one side is, by the displayed ratio (the same words at every threshold):
    0 about equal, 1 slightly, 2 plainly, 3 much."""
    return 0 if ratio < 1.1 else 1 if ratio < 1.5 else 2 if ratio < 2 else 3


# Readings ------------------------------------------------------------------------------
def _read_sma(v, i, c, b, s, say, p):
    n = p['period']
    m = _at(v, 'SMA20', i)
    d = _pct(c[i], m)
    side = _side(d)
    if side:
        where = say(f'종가가 {say.avg(n)}보다 {_fmt(abs(d))}% {"위" if side > 0 else "아래"}에 있습니다. '
                    f'최근 {say.n(n)} 평균 가격보다 {"높게" if side > 0 else "낮게"} 거래되고 있다는 뜻입니다.',
                    f'The close is {_fmt(abs(d))}% {"above" if side > 0 else "below"} the {say.avg(n)}: it trades '
                    f'{"higher" if side > 0 else "lower"} than the average of the last {say.n(n)}.')
    else:
        where = say(f'종가가 {say.avg(n)}과 {"같습니다" if d == 0 else "거의 같습니다"}.',
                    f'The close {"equals" if d == 0 else "almost equals"} the {say.avg(n)}.')
    before = _at(v, 'SMA20', i - 5)
    if before is None:
        return where
    return where + ' ' + say(
        f'평균선은 {say.ago(5)}보다 {"올라가는" if m > before else "내려가는"} 중입니다.' if m != before else
        f'평균선은 {say.ago(5)}과 같은 높이로 평평합니다.',
        f'The average is {"rising" if m > before else "falling" if m < before else "flat"} versus 5 {say.unit[1]} ago.')


def _read_ema(v, i, c, b, s, say, p):
    fast, slow = _at(v, 'EMA12', i), _at(v, 'EMA26', i)
    d = _pct(fast, slow)
    side = _side(d)
    text = say(f'빠른 지수평균({p["fast"]})이 느린 지수평균({p["slow"]})보다 {_fmt(abs(d))}% '
               f'{"위" if side > 0 else "아래"}에 있습니다. 최근 흐름이 더 긴 흐름보다 {"강했다" if side > 0 else "약했다"}는 뜻입니다.',
               f'The fast average ({p["fast"]}) is {_fmt(abs(d))}% {"above" if side > 0 else "below"} the slow one '
               f'({p["slow"]}): the recent move has been {"stronger" if side > 0 else "weaker"} than the longer one.') if side else say(
        f'빠른 지수평균과 느린 지수평균이 {"같습니다" if d == 0 else "거의 같습니다"}.',
        f'The fast and slow averages are {"equal" if d == 0 else "almost equal"}.')
    for back in range(1, 4):
        a, z = _at(v, 'EMA12', i - back), _at(v, 'EMA26', i - back)
        if a is not None and z is not None and (a - z) * (fast - slow) < 0:
            return text + ' ' + say(f'최근 {back + 1}개 봉 사이에 두 선이 교차했습니다. 교차는 이미 일어난 변화를 보여줄 뿐입니다.',
                                    f'The lines crossed within the last {back + 1} bars; a crossing shows a change that already happened.')
    return text


def _read_macd(v, i, c, b, s, say, p):
    m, h = _at(v, 'MACD', i), _at(v, 'HISTOGRAM', i)
    zero = say(f'MACD {format_value("value", m)}: {p["fast"]}{say.unit[0]} 지수평균이 '
               f'{p["slow"]}{say.unit[0]} 지수평균보다 {"높습니다" if m > 0 else "낮습니다"}.' if m else
               f'MACD {format_value("value", m)}: {p["fast"]}{say.unit[0]} 지수평균과 {p["slow"]}{say.unit[0]} 지수평균이 같습니다.',
               f'MACD {format_value("value", m)}: the {p["fast"]}-{say.unit[4]} average is '
               f'{"above" if m > 0 else "below" if m < 0 else "equal to"} the {p["slow"]}-{say.unit[4]} average.')
    momentum = say('MACD가 신호선보다 위에 있어 막대가 위쪽입니다. 최근 오름 속도가 붙거나 내림 속도가 줄어드는 쪽입니다.'
                   if h > 0 else 'MACD가 신호선보다 아래에 있어 막대가 아래쪽입니다. 최근 내림 속도가 붙거나 오름 속도가 줄어드는 쪽입니다.'
                   if h < 0 else 'MACD와 신호선이 같은 값입니다.',
                   'MACD is above its signal line (bars above zero): upward momentum is building or downward momentum fading.'
                   if h > 0 else 'MACD is below its signal line (bars below zero): downward momentum is building or upward momentum fading.'
                   if h < 0 else 'MACD equals its signal line.')
    return zero + ' ' + momentum


def _read_ichimoku(v, i, c, b, s, say, p):
    tenkan, kijun, a, bb = (_at(v, k, i) for k in ('TENKAN', 'KIJUN', 'SPAN_A', 'SPAN_B'))
    top, bottom = max(a, bb), min(a, bb)
    if c[i] > top:
        cloud = say('가격이 구름 위에 있습니다. 일목균형표에서는 이를 상승 흐름으로 보는 것이 관례입니다.',
                    'Price is above the cloud, which by convention reads as an uptrend.')
    elif c[i] < bottom:
        cloud = say('가격이 구름 아래에 있습니다. 일목균형표에서는 이를 하락 흐름으로 보는 것이 관례입니다.',
                    'Price is below the cloud, which by convention reads as a downtrend.')
    else:
        cloud = say('가격이 구름 안에 있습니다. 방향이 뚜렷하지 않은 구간으로 보는 것이 관례입니다.',
                    'Price is inside the cloud, conventionally a stretch without a clear direction.')
    if tenkan != kijun:
        lines = say(f'전환선이 기준선보다 {"위" if tenkan > kijun else "아래"}에 있습니다'
                    f'(최근 {p["conversion"]}개 봉의 중간값이 {p["base"]}개 봉 중간값보다 {"높음" if tenkan > kijun else "낮음"}).',
                    f'The conversion line is {"above" if tenkan > kijun else "below"} the base line '
                    f'(the {p["conversion"]}-bar midpoint is {"higher" if tenkan > kijun else "lower"} than the {p["base"]}-bar one).')
    else:
        lines = say(f'전환선과 기준선이 같은 높이에 있습니다(최근 {p["conversion"]}개 봉의 중간값과 {p["base"]}개 봉 중간값이 같음).',
                    f'The conversion line is level with the base line (the {p["conversion"]}-bar midpoint equals the {p["base"]}-bar one).')
    if a == bb:
        color = say('선행스팬 1과 2가 같아 구름 두께가 없습니다.', 'Span A equals span B, so the cloud has no thickness.')
    else:
        color = say('구름은 ' + ('선행스팬 1이 위인 양운(상승 구름)' if a > bb else '선행스팬 2가 위인 음운(하락 구름)') + '입니다.',
                    'The cloud is ' + ('the bullish kind (span A on top).' if a > bb else 'the bearish kind (span B on top).'))
    return ' '.join((cloud, lines, color))


def _read_psar(v, i, c, b, s, say, p):
    sar = _at(v, 'SAR', i)
    # The side comes from the SAR algorithm itself: a dot can land exactly on the close.
    side = parabolic_sar_trend(b[1], b[2], p['step'], p['maximum'])
    below = side[i] > 0
    if _price(sar) != _price(c[i]):
        text = say(f'SAR 점({_price(sar)})이 가격 {"아래" if below else "위"}쪽에 있습니다. '
                   f'{"상승" if below else "하락"} 흐름을 따라가는 중입니다.',
                   f'The SAR dot ({_price(sar)}) is {"below" if below else "above"} price: it is trailing '
                   f'{"an upward" if below else "a downward"} move.')
    else:
        text = say(f'SAR 점({_price(sar)})이 종가와 같은 높이에 찍혔지만 계산상 가격 {"아래" if below else "위"}쪽 점입니다. '
                   f'{"상승" if below else "하락"} 흐름을 따라가는 중입니다.',
                   f'The SAR dot ({_price(sar)}) is level with the close but counts as {"below" if below else "above"} '
                   f'price: it is trailing {"an upward" if below else "a downward"} move.')
    if i >= 1 and math.isfinite(side[i - 1]) and side[i - 1] != side[i]:
        text += ' ' + say('이번 봉에서 점이 반대편으로 넘어왔습니다. 흐름이 바뀌었다고 보는 관례가 있지만 횡보장에서는 자주 뒤집힙니다.',
                          'The dots flipped sides on this bar. By convention that marks a change of move, but in sideways markets flips are frequent.')
    return text


def _read_adx(v, i, c, b, s, say, p):
    adx, pdi, mdi = _at(v, 'ADX', i), _at(v, 'PDI', i), _at(v, 'MDI', i)
    shown = _shown(adx)
    if shown >= 40:
        level = say('추세가 매우 뚜렷한 구간입니다(25 이상을 뚜렷한 추세로 보는 관례에서 한참 위).',
                    'the trend is very clear (well above the conventional 25).')
    elif shown >= 25:
        level = say('추세가 뚜렷한 구간입니다(25 이상을 기준으로 보는 관례).', 'the trend is clear (25 or more by convention).')
    elif shown >= 20:
        level = say('추세가 생기는지 애매한 구간입니다.', 'it is unclear whether a trend is forming.')
    else:
        level = say('뚜렷한 추세가 없는 구간입니다(20 미만을 기준으로 보는 관례).', 'there is no clear trend (below 20 by convention).')
    up, down = _shown(pdi), _shown(mdi)
    if up != down:
        side = say(f'+DI({_fmt(pdi)})가 −DI({_fmt(mdi)})보다 {"높아 오르는 힘이" if up > down else "낮아 내리는 힘이"} 더 컸습니다.',
                   f'+DI ({_fmt(pdi)}) is {"above" if up > down else "below"} −DI ({_fmt(mdi)}): '
                   f'{"upward" if up > down else "downward"} pressure was larger.')
    elif pdi == mdi == 0:
        side = say('+DI와 −DI가 모두 0이라 오르는 힘도 내리는 힘도 없었습니다.',
                   '+DI and −DI are both 0.0: there was no upward or downward pressure.')
    else:
        side = say(f'+DI({_fmt(pdi)})와 −DI({_fmt(mdi)})가 {"같아" if pdi == mdi else "거의 같아"} 두 힘이 비슷했습니다.',
                   f'+DI ({_fmt(pdi)}) is {"equal" if pdi == mdi else "almost equal"} to −DI ({_fmt(mdi)}): the two were balanced.')
    return say(f'ADX {_fmt(adx)}: ', f'ADX {_fmt(adx)}: ') + level + ' ' + side + ' ' + say(
        'ADX는 추세의 세기만 보여주고 방향은 알려주지 않습니다.', 'ADX measures strength only, not direction.')


def _band_reading(say, close, upper, middle, lower, name_ko, name_en, detail_ko, detail_en):
    if close > upper:
        return say(f'종가가 {name_ko} 위 선 밖에 있습니다. {detail_ko} 위로 벗어났습니다.',
                   f'The close is above the upper {name_en} line: {detail_en} upward.')
    if close < lower:
        return say(f'종가가 {name_ko} 아래 선 밖에 있습니다. {detail_ko} 아래로 벗어났습니다.',
                   f'The close is below the lower {name_en} line: {detail_en} downward.')
    d = _pct(close, middle)
    side = _side(d)
    if side:
        return say(f'종가가 {name_ko} 안, 중심선보다 {_fmt(abs(d))}% {"위" if side > 0 else "아래"}에 있습니다.',
                   f'The close is inside the {name_en}, {_fmt(abs(d))}% {"above" if side > 0 else "below"} the middle line.')
    return say(f'종가가 {name_ko} 안, 중심선과 {"같은" if d == 0 else "거의 같은"} 높이에 있습니다.',
               f'The close is inside the {name_en}, {"level with" if d == 0 else "almost level with"} the middle line.')


def _read_envelope(v, i, c, b, s, say, p):
    return _band_reading(say, c[i], _at(v, 'ENV_UPPER', i), _at(v, 'ENV_MIDDLE', i), _at(v, 'ENV_LOWER', i),
                         '엔벨로프', 'envelope', f'{say.avg(p["period"])}에서 {_plain(p["percent"])}% 넘게',
                         f'more than {_plain(p["percent"])}% away from the {say.avg(p["period"])}')


def _read_keltner(v, i, c, b, s, say, p):
    return _band_reading(say, c[i], _at(v, 'KC_UPPER', i), _at(v, 'KC_MIDDLE', i), _at(v, 'KC_LOWER', i),
                         '켈트너 채널', 'Keltner channel', '평소 변동폭(ATR)의 2배보다 크게',
                         'more than twice the usual range (ATR)')


def _read_donchian(v, i, c, b, s, say, p):
    upper, lower = _at(v, 'DC_UPPER', i), _at(v, 'DC_LOWER', i)
    n = p['period']
    if upper == lower:
        return say(f'최근 {say.n(n)} 동안 최고가와 최저가가 같아 가격 범위가 없습니다.',
                   f'The highest high and the lowest low of the last {say.n(n)} are the same: there is no range.')
    # The band includes this bar, so a high equal to the band only ties the earlier highs;
    # a new high must beat every earlier bar in the window (and a new low likewise).
    earlier = slice(max(0, i - n + 1), i)
    new_high = n > 1 and b[1][i] > float(np.max(b[1][earlier]))
    new_low = n > 1 and b[2][i] < float(np.min(b[2][earlier]))
    if new_high and new_low:
        return say(f'이번 봉에서 최근 {say.n(n)} 중 최고가와 최저가를 모두 새로 썼습니다. 범위가 위아래로 넓어졌을 뿐 방향을 알려주지는 않습니다.',
                   f'This bar set both a new high and a new low for the last {say.n(n)}: the range widened both ways, which shows no direction.')
    if new_high:
        return say(f'이번 봉에서 최근 {say.n(n)} 중 최고가를 새로 썼습니다. 그 방향으로 계속 간다는 보장은 없습니다.',
                   f'This bar set a new high for the last {say.n(n)}. That does not guarantee the move continues.')
    if new_low:
        return say(f'이번 봉에서 최근 {say.n(n)} 중 최저가를 새로 썼습니다. 그 방향으로 계속 간다는 보장은 없습니다.',
                   f'This bar set a new low for the last {say.n(n)}. That does not guarantee the move continues.')
    where = (c[i] - lower) / (upper - lower) * 100
    text = say(f'종가가 최근 {say.n(n)} 가격 범위의 바닥에서 {where:.0f}% 높이에 있습니다.',
               f'The close sits {where:.0f}% of the way up the range of the last {say.n(n)}.')
    if n > 1 and b[1][i] == upper:
        text = say(f'이번 봉 고가가 최근 {say.n(n)} 최고가와 같습니다(새로 쓴 것은 아님). ',
                   f'This bar’s high matched the highest high of the last {say.n(n)} (a tie, not a new high). ') + text
    elif n > 1 and b[2][i] == lower:
        text = say(f'이번 봉 저가가 최근 {say.n(n)} 최저가와 같습니다(새로 쓴 것은 아님). ',
                   f'This bar’s low matched the lowest low of the last {say.n(n)} (a tie, not a new low). ') + text
    return text


def _read_rsi(v, i, c, b, s, say, p):
    r = _at(v, 'RSI14', i)
    n = say.n(p['period'])
    shown = _shown(r)
    # RSI = 100 − 100/(1 + average rise ÷ average fall): the words follow that ratio, the
    # same way on both sides of 70 and 30; the conventional names follow the printed value.
    ratio, ratio_text = _ratio(r)
    degree = 3 if not ratio_text else _degree(ratio)
    rising = r >= 50
    if degree == 0:
        head = say(f'RSI {_fmt(r)}: 최근 {n} 동안 오른 폭과 내린 폭이 비슷했습니다.',
                   f'RSI {_fmt(r)}: over the last {n} rises and falls were about the same size.')
    else:
        big, small = say(('오른', '내린') if rising else ('내린', '오른'), ('rises', 'falls') if rising else ('falls', 'rises'))
        size = say(('조금 더', '더', '훨씬')[degree - 1], ('slightly larger', 'larger', 'much larger')[degree - 1])
        moves = ('상승폭', '하락폭') if rising else ('하락폭', '상승폭')
        detail = say(f'평균 {moves[0]}이 평균 {moves[1]}의 {ratio_text}배' if ratio_text else f'{small} 폭은 없었음',
                     f'the average {big[:-1]} was {ratio_text}× the average {small[:-1]}' if ratio_text else f'there were no {small}')
        head = say(f'RSI {_fmt(r)}: 최근 {n} 동안 {big} 폭이 {small} 폭보다 {size} 컸습니다({detail}).',
                   f'RSI {_fmt(r)}: over the last {n} the {big} were {size} than the {small} ({detail}).')
    if shown >= 70:
        return head + ' ' + say("70 이상을 과매수 구간으로 부르는 관례가 있습니다. 팔라는 뜻이 아니라 '최근 많이 올랐다'는 뜻입니다.",
                                "70 or more is conventionally called overbought. It means 'it has risen a lot', not 'sell'.")
    if shown <= 30:
        return head + ' ' + say("30 이하를 과매도 구간으로 부르는 관례가 있습니다. 사라는 뜻이 아니라 '최근 많이 내렸다'는 뜻입니다.",
                                "30 or less is conventionally called oversold. It means 'it has fallen a lot', not 'buy'.")
    return head + ' ' + say('30~70은 어느 쪽으로도 치우치지 않은 범위로 보는 것이 관례입니다.',
                            '30 to 70 is conventionally read as not stretched either way.')


def _range_reading(say, value, high_level, low_level, top_ko, top_en, low_ko, low_en, mid_ko, mid_en, digits=1):
    """The conventional band of `value` as it is printed with `digits` decimals."""
    shown = _shown(value, digits)
    if shown >= high_level:
        return say(top_ko, top_en)
    if shown <= low_level:
        return say(low_ko, low_en)
    return say(mid_ko, mid_en)


def _smoothed_position(say, k, raw, smooth, n, what_ko, what_en, thing_ko, thing_en, this_ko, this_en):
    """Reading of a slow %K (the `smooth`-bar average of raw positions in a range): the
    conventional band of that average, then where this bar alone finished."""
    k_text = _fmt(k)
    if smooth > 1:
        lead_ko = f'%K {k_text}: 최근 {n} {what_ko} 범위 안에서 {thing_ko} 위치를 {say.n(smooth)} 동안 평균하면 '
        lead_en = f'%K {k_text}: {thing_en} position in the {what_en} range of the last {n}, averaged over {say.n(smooth)}, is '
        tail = ' ' + say(f'{this_ko}만 보면 범위의 {raw:.0f}% 높이입니다.', f'{this_en} alone is {raw:.0f}% of the way up.')
    else:
        lead_ko = f'%K {k_text}: 최근 {n} {what_ko} 범위 안에서 {thing_ko} 위치는 '
        lead_en = f'%K {k_text}: {thing_en} position in the {what_en} range of the last {n} is '
        tail = ''
    return _range_reading(
        say, k, 80, 20,
        lead_ko + '꼭대기 근처입니다(80 이상을 과매수로 부르는 관례).',
        lead_en + 'near the top (80 or more is conventionally overbought).',
        lead_ko + '바닥 근처입니다(20 이하를 과매도로 부르는 관례).',
        lead_en + 'near the bottom (20 or less is conventionally oversold).',
        lead_ko + f'바닥에서 {k_text}% 높이입니다.',
        lead_en + f'{k_text}% of the way up.') + tail


def _raw_position(values, i, n):
    """100 × (value − lowest) / (highest − lowest) over the n values ending at i; 50 with no range."""
    window = np.asarray(values[max(0, i - n + 1):i + 1], dtype=float)
    low, high = float(np.min(window)), float(np.max(window))
    return 100 * (values[i] - low) / (high - low) if high > low else 50.0


def _read_stoch(v, i, c, b, s, say, p):
    k, d = _at(v, 'STOCH_K', i), _at(v, 'STOCH_D', i)
    n = p['period']
    # %K is the k_smooth-bar average of the raw position, not where this bar closed.
    window = slice(max(0, i - n + 1), i + 1)
    high, low = float(np.max(b[1][window])), float(np.min(b[2][window]))
    raw = 100 * (c[i] - low) / (high - low) if high > low else 50.0
    text = _smoothed_position(say, k, raw, p['k_smooth'], say.n(n), '가격', 'price', '종가', 'the close’s',
                              '이번 봉 종가', 'This bar’s close')
    ks, ds = _shown(k), _shown(d)
    if ks != ds:
        return text + ' ' + say(f'%K가 %D({_fmt(d)})보다 {"위에 있어 범위 안 위치가 올라가는" if ks > ds else "아래에 있어 범위 안 위치가 내려가는"} 중입니다.',
                                f'%K is {"above" if ks > ds else "below"} %D ({_fmt(d)}): the position in the range is '
                                f'{"rising" if ks > ds else "falling"}.')
    return text + ' ' + say(f'%K와 %D({_fmt(d)})가 {"같아 범위 안 위치가 그대로입니다" if k == d else "거의 같아 범위 안 위치에 큰 변화가 없습니다"}.',
                            f'%K is {"equal" if k == d else "almost equal"} to %D ({_fmt(d)}): the position in the range is '
                            f'{"unchanged" if k == d else "barely changing"}.')


def _read_stochrsi(v, i, c, b, s, say, p):
    k = _at(v, 'STOCHRSI_K', i)
    n = p['period']
    # Like the stochastic, %K averages the raw position of RSI over k_smooth bars.
    raw = _raw_position(rsi_line(c[:i + 1], p['rsi_period']), i, n)
    text = _smoothed_position(say, k, raw, p['k_smooth'], say.n(n), 'RSI', 'RSI', 'RSI의', 'RSI’s',
                              '이번 봉 RSI', 'This bar’s RSI')
    return text + ' ' + say('매우 민감한 지표라 값이 자주 크게 바뀝니다.', 'It is very sensitive and swings often.')


def _read_cci(v, i, c, b, s, say, p):
    x = _at(v, 'CCI', i)
    n = say.avg(p['period'])
    shown = _fmt(x, 0)
    return _range_reading(
        say, x, 100, -100,
        f'CCI {shown}: 평균가격이 {n}보다 평소 벗어나는 정도를 크게 넘어 위에 있습니다(+100 이상을 과열로 보는 관례).',
        f'CCI {shown}: the typical price is unusually far above its {n} (+100 or more is conventionally overheated).',
        f'CCI {shown}: 평균가격이 {n}보다 평소 벗어나는 정도를 크게 넘어 아래에 있습니다(−100 이하를 침체로 보는 관례).',
        f'CCI {shown}: the typical price is unusually far below its {n} (−100 or less is conventionally depressed).',
        f'CCI {shown}: 평균가격이 {n} 가까이(±100 안)에 있습니다.',
        f'CCI {shown}: the typical price is near its {n} (within ±100).', digits=0)


def _read_williams(v, i, c, b, s, say, p):
    x = _at(v, 'WILLR', i)
    n = say.n(p['period'])
    shown = _fmt(x)
    return _range_reading(
        say, x, -20, -80,
        f'%R {shown}: 종가가 최근 {n} 최고가 근처입니다(−20 이상을 과매수로 부르는 관례).',
        f'%R {shown}: the close is near the highest high of the last {n} (−20 or more is conventionally overbought).',
        f'%R {shown}: 종가가 최근 {n} 최저가 근처입니다(−80 이하를 과매도로 부르는 관례).',
        f'%R {shown}: the close is near the lowest low of the last {n} (−80 or less is conventionally oversold).',
        f'%R {shown}: 종가가 최근 {n} 최고가에서 범위의 {_fmt(-x)}%만큼 내려와 있습니다.',
        f'%R {shown}: the close is {_fmt(-x)}% of the range below the highest high of the last {n}.')


def _read_roc(v, i, c, b, s, say, p):
    x = _at(v, 'ROC', i)
    ago = say.ago(p['period'])
    side = _side(x)
    if side:
        return say(f'ROC {_fmt(x, sign=True)}%: 종가가 {ago}보다 {_fmt(abs(x))}% {"올랐습니다" if side > 0 else "내렸습니다"}.',
                   f'ROC {_fmt(x, sign=True)}%: the close is {_fmt(abs(x))}% {"higher" if side > 0 else "lower"} than {ago}.')
    return say(f'ROC {_fmt(x)}%: 종가가 {ago}과 {"같습니다" if x == 0 else "거의 같습니다"}.',
               f'ROC {_fmt(x)}%: the close is {"unchanged" if x == 0 else "almost unchanged"} from {ago}.')


def _read_disparity(v, i, c, b, s, say, p):
    x = _at(v, 'DISPARITY', i)
    n = p['period']
    shown = _shown(x)
    gap = _shown(shown - 100)  # the distance printed is the one the printed value implies
    if gap:
        text = say(f'이격도 {_fmt(x)}: 종가가 {say.avg(n)}보다 {_fmt(abs(gap))}% {"위" if gap > 0 else "아래"}에 있습니다.',
                   f'Disparity {_fmt(x)}: the close is {_fmt(abs(gap))}% {"above" if gap > 0 else "below"} the {say.avg(n)}.')
    else:
        text = say(f'이격도 {_fmt(x)}: 종가가 {say.avg(n)}과 {"같습니다" if x == 100 else "거의 같습니다"}.',
                   f'Disparity {_fmt(x)}: the close {"equals" if x == 100 else "almost equals"} the {say.avg(n)}.')
    if shown >= 105 or shown <= 95:
        hot = shown >= 105
        # The 105/95 convention belongs to the 20-day disparity; say so on other charts.
        if say.daily and say.unit[0] == '일' and n == 20:
            text += ' ' + say(f'20일 이격도는 흔히 {"105 이상을 과열" if hot else "95 이하를 침체"}로 보는 관례가 있습니다.',
                              f'For the 20-day version {"105 or more" if hot else "95 or less"} is conventionally called '
                              f'{"overheated" if hot else "depressed"}.')
        else:
            text += ' ' + say(f'{"105 이상을 과열" if hot else "95 이하를 침체"}로 보는 관례는 20일 이격도 기준이라, '
                              f'이 {say.n(n)} 이격도에는 그대로 맞지 않을 수 있습니다.',
                              f'Calling {"105 or more overheated" if hot else "95 or less depressed"} is a convention for the '
                              f'20-day version; it may not fit this {n}-{say.unit[4]} one.')
    return text


def _read_psychology(v, i, c, b, s, say, p):
    x = _at(v, 'PSY', i)
    n = p['period']
    ups = round(x * n / 100)
    shown = _shown(x, 0)
    if ups == 0:
        count = say(f'최근 {say.n(n)} 동안 {say.unit[3]}보다 오른 적이 없습니다(심리도 0%).',
                    f'Not one of the last {say.n(n)} closed above the previous {say.unit[4]} (psychological line 0%).')
    else:
        count = say(f'최근 {say.n(n)} 중 {say.count_subject(ups)} {say.unit[3]}보다 올랐습니다(심리도 {_fmt(x, 0)}%).',
                    f'{ups} of the last {say.n(n)} closed above the previous {say.unit[4]} (psychological line {_fmt(x, 0)}%).')
    if shown >= 75:
        count += ' ' + say('75% 이상을 과열로 보는 관례가 있습니다.', '75% or more is conventionally called overheated.')
    elif shown <= 25:
        count += ' ' + say('25% 이하를 침체로 보는 관례가 있습니다.', '25% or less is conventionally called depressed.')
    return count


def _read_bb(v, i, c, b, s, say, p):
    upper, lower = _at(v, 'BB_UPPER', i), _at(v, 'BB_LOWER', i)
    middle = (upper + lower) / 2
    width = (upper - lower) / middle * 100 if middle else math.nan
    if c[i] > upper:
        text = say('종가가 볼린저 위 밴드 밖에 있습니다. 최근 가격이 흩어진 정도에 비해 크게 올라 있으며, 밴드 밖에서 한동안 머물 수도 있습니다.',
                   'The close is outside the upper band: high for its recent spread, and it can stay outside for a while.')
    elif c[i] < lower:
        text = say('종가가 볼린저 아래 밴드 밖에 있습니다. 최근 가격이 흩어진 정도에 비해 크게 내려 있으며, 밴드 밖에서 한동안 머물 수도 있습니다.',
                   'The close is outside the lower band: low for its recent spread, and it can stay outside for a while.')
    else:
        where = (c[i] - lower) / (upper - lower) * 100 if upper > lower else 50.0
        text = say(f'종가가 밴드 안, 아래 밴드에서 {where:.0f}% 높이에 있습니다.',
                   f'The close is inside the bands, {where:.0f}% of the way from the lower to the upper band.')
    return text + ' ' + say(f'밴드 폭은 가운데 선의 {width:.1f}%입니다.', f'The band is {width:.1f}% of the middle line wide.')


def _read_atr(v, i, c, b, s, say, p):
    x = _at(v, 'ATR', i)
    if x == 0:
        return say(f'ATR 0: 최근 {say.n(p["period"])} 동안 가격이 전혀 움직이지 않았습니다(고가·저가·종가가 모두 같음).',
                   f'ATR 0: price did not move at all over the last {say.n(p["period"])} (high, low and close all equal).')
    text = say(f'ATR {_price(x)}: 최근 {say.n(p["period"])} 동안 한 봉에 평균 {_price(x)}(종가의 {x / c[i] * 100:.1f}%)만큼 움직였습니다.',
               f'ATR {_price(x)}: over the last {say.n(p["period"])} price moved about {_price(x)} per bar ({x / c[i] * 100:.1f}% of the close).')
    before = _at(v, 'ATR', i - 20)
    if before:
        ratio = x / before
        text += ' ' + say(f'{say.ago(20)}' + ('보다 출렁임이 커졌습니다.' if ratio > 1.2 else '보다 출렁임이 줄었습니다.'
                                              if ratio < 0.8 else '과 출렁임이 비슷합니다.'),
                          f'Swings are {"larger than" if ratio > 1.2 else "smaller than" if ratio < 0.8 else "similar to"} {say.ago(20)}.')
    return text + ' ' + say('방향은 알려주지 않습니다.', 'It says nothing about direction.')


def _read_percent_b(v, i, c, b, s, say, p):
    x = _at(v, 'PERCENT_B', i)
    shown, head = _shown(x, 2), f'%B {_fmt(x, 2)}: '
    if shown > 1:
        return say(head + '종가가 위 밴드 밖에 있습니다.', head + 'the close is above the upper band.')
    if shown < 0:
        return say(head + '종가가 아래 밴드 밖에 있습니다.', head + 'the close is below the lower band.')
    if shown == 1:
        return say(head + '종가가 위 밴드와 같은 높이에 있습니다.', head + 'the close is level with the upper band.')
    if shown == 0:
        return say(head + '종가가 아래 밴드와 같은 높이에 있습니다.', head + 'the close is level with the lower band.')
    if shown == 0.5:
        return say(head + '종가가 아래 밴드(0)와 위 밴드(1) 사이 한가운데에 있습니다.',
                   head + 'the close is halfway between the lower (0) and upper (1) bands.')
    return say(head + f'종가가 아래 밴드(0)와 위 밴드(1) 사이, 가운데보다 {"위쪽" if shown > 0.5 else "아래쪽"}에 있습니다.',
               head + f'the close is between the lower (0) and upper (1) bands, {"above" if shown > 0.5 else "below"} the middle.')


def _read_bandwidth(v, i, c, b, s, say, p):
    x = _at(v, 'BANDWIDTH', i)
    history = np.asarray(v['BANDWIDTH'][max(0, i - 119):i + 1], dtype=float)
    history = history[np.isfinite(history)]
    text = say(f'밴드폭 {x:.1f}%: 위아래 밴드 사이가 가운데 선의 {x:.1f}%입니다.',
               f'Bandwidth {x:.1f}%: the bands are {x:.1f}% of the middle line apart.')
    if history.size >= 40:
        share = float(np.mean(history < x))
        if share <= 0.1:
            text += ' ' + say(f'최근 {say.n(history.size)} 중 가장 좁은 편입니다(스퀴즈라고 부르는 관례). 움직임이 잦아들었다는 뜻이며 방향은 알려주지 않습니다.',
                              f'It is among the narrowest of the last {say.n(history.size)} (conventionally a squeeze): movement has calmed; direction is unknown.')
        elif share >= 0.9:
            text += ' ' + say(f'최근 {say.n(history.size)} 중 가장 넓은 편입니다. 최근 움직임이 컸습니다.',
                              f'It is among the widest of the last {say.n(history.size)}: recent movement was large.')
        else:
            text += ' ' + say(f'최근 {say.n(history.size)} 가운데 중간쯤입니다.', f'It is mid-range for the last {say.n(history.size)}.')
    return text


def _read_volume_ma(v, i, c, b, s, say, p):
    volume, average = b[4][i], _at(v, 'VOLUME_MA', i)
    if not math.isfinite(volume):
        return say('이 봉의 거래량은 제공되지 않았습니다.', 'This bar’s volume was not reported.')
    n = p['period']
    if not average or average <= 0:
        # KIS reports a trading halt as volume 0: there is no average to compare with.
        if volume == 0:
            return say(f'이번 봉을 포함해 최근 {say.n(n)} 동안 거래량이 0입니다(거래정지 등으로 거래가 없었을 수 있습니다).',
                       f'Volume was 0 on this bar and throughout the last {say.n(n)} (for example during a trading halt).')
        return say(f'이번 봉 거래량은 {_quantity(volume, say.lang)}이지만 {say.avg(n)}이 0이라 배수로 비교할 수 없습니다.',
                   f'This bar’s volume is {_quantity(volume, say.lang)}, but the {say.avg(n)} is 0, so there is no multiple to compare.')
    ratio = volume / average
    shown = _shown(ratio)
    text = say(f'이번 봉 거래량은 {say.avg(n)}의 {_fmt(ratio)}배입니다.',
               f'This bar’s volume is {_fmt(ratio)}× the {say.avg(n)}.')
    if shown >= 2:
        text += ' ' + say('평소보다 거래가 크게 늘었습니다.', 'Trading was much heavier than usual.')
    elif shown <= 0.5:
        text += ' ' + say('평소보다 거래가 적었습니다.', 'Trading was lighter than usual.')
    return text


def _read_obv(v, i, c, b, s, say, p):
    now = _at(v, 'OBV', i)
    back = next((j for j in range(i - 20, -1, -1) if _at(v, 'OBV', j) is not None), None) if i >= 20 else None
    if back is None:
        return say(f'OBV {_quantity(now, say.lang)}: 방향을 보려면 20개 봉 이상이 필요합니다.',
                   f'OBV {_quantity(now, say.lang)}: at least 20 bars are needed to read its direction.')
    change, move = now - _at(v, 'OBV', back), c[i] - c[back]
    text = say(f'최근 {say.n(i - back)} 동안 OBV가 {"늘었습니다. 오른 봉의 거래량이 내린 봉보다 많았습니다" if change > 0 else "줄었습니다. 내린 봉의 거래량이 오른 봉보다 많았습니다" if change < 0 else "그대로입니다"}.',
               f'Over the last {say.n(i - back)} OBV {"rose: more volume traded on up bars than on down bars" if change > 0 else "fell: more volume traded on down bars than on up bars" if change < 0 else "was unchanged"}.')
    if change * move < 0:
        text += ' ' + say('같은 기간 가격은 반대로 움직였습니다. 가격과 거래량 흐름이 엇갈리는 것을 다이버전스라고 부르는 관례가 있습니다.',
                          'Price moved the other way over the same span; that mismatch is conventionally called a divergence.')
    return text


def _read_mfi(v, i, c, b, s, say, p):
    x = _at(v, 'MFI', i)
    n = say.n(p['period'])
    # MFI = 100 − 100/(1 + rising-bar money ÷ falling-bar money): words follow that ratio
    # continuously across 80 and 20; the conventional names follow the printed value.
    ratio, ratio_text = _ratio(x)
    degree = 3 if not ratio_text else _degree(ratio)
    rising = x >= 50
    if degree == 0:
        head = say(f'MFI {_fmt(x)}: 최근 {n} 동안 오른 봉과 내린 봉의 거래대금이 비슷했습니다.',
                   f'MFI {_fmt(x)}: over the last {n} money on rising and falling bars was about equal.')
    else:
        big, small = say(('오른', '내린') if rising else ('내린', '오른'), ('rising', 'falling') if rising else ('falling', 'rising'))
        size = say(('조금 더', '더', '훨씬')[degree - 1], ('slightly more', 'more', 'far more')[degree - 1])
        detail = say(f'{small} 봉의 {ratio_text}배' if ratio_text else f'{small} 봉의 거래대금은 없었음',
                     f'{ratio_text}× as much' if ratio_text else f'none on {small} bars')
        head = say(f'MFI {_fmt(x)}: 최근 {n} 동안 {big} 봉의 거래대금이 {small} 봉보다 {size} 많았습니다({detail}).',
                   f'MFI {_fmt(x)}: over the last {n} {size} money traded on {big} bars than on {small} ones ({detail}).')
    shown = _shown(x)
    if shown >= 80:
        return head + ' ' + say('80 이상을 과매수로 부르는 관례가 있습니다.', '80 or more is conventionally called overbought.')
    if shown <= 20:
        return head + ' ' + say('20 이하를 과매도로 부르는 관례가 있습니다.', '20 or less is conventionally called oversold.')
    return head


def _read_vwap(v, i, c, b, s, say, p):
    x = _at(v, 'VWAP', i)
    d = _pct(c[i], x)
    # This bar against its own session (the cursor may sit on an earlier day), named by the
    # date the session opened (a night session that crosses midnight keeps its opening date).
    day = b[6][session_start_index(b[6])[i]][:10]
    side = _side(d, 2)
    if side:
        return say(f'이 봉의 종가가 {day} 장 VWAP({_price(x)})보다 {_fmt(abs(d), 2)}% {"위" if side > 0 else "아래"}에 있습니다. '
                   f'그 장 시작부터 이 봉까지 거래된 평균 단가보다 {"높게" if side > 0 else "낮게"} 끝났다는 뜻입니다.',
                   f'This bar closed {_fmt(abs(d), 2)}% {"above" if side > 0 else "below"} the VWAP of the {day} session '
                   f'({_price(x)}): {"above" if side > 0 else "below"} the average price traded from that session’s open to this bar.')
    return say(f'이 봉의 종가가 {day} 장 VWAP({_price(x)})와 {"같습니다" if d == 0 else "거의 같습니다"}. '
               f'그 장 시작부터 이 봉까지 거래된 평균 단가와 {"같은" if d == 0 else "거의 같은"} 값에서 끝났다는 뜻입니다.',
               f'This bar closed {"at" if d == 0 else "almost at"} the VWAP of the {day} session ({_price(x)}): '
               f'{"at" if d == 0 else "almost at"} the average price traded from that session’s open to this bar.')


_GROUPS = (('외국인', 'foreign investors'), ('기관', 'institutions'), ('개인', 'individuals'))


def _read_investor_flow(v, i, c, b, s, say, p):
    day = b[5][i]
    rows = [row for row in s.flows if row[0] <= day]
    if not rows or rows[-1][0] != day:
        return say('이날의 투자자별 매매 자료가 없습니다.', 'No investor trading data for this date.')
    unit = say('주', ' shares')
    today = ', '.join(say(f'{ko} {_quantity(value, "ko", True)}{unit}', f'{en} {_quantity(value, "en", True)}{unit}')
                      for (ko, en), value in zip(_GROUPS, rows[-1][1:]) if math.isfinite(value))
    text = say(f'이날 순매수: {today}.', f'Net buying on this date: {today}.') if today else say(
        '이날 투자자별 순매수 수치가 비어 있습니다.', 'The investor net-buying figures for this date are blank.')
    window = rows[-20:]
    if len(window) >= 5:
        # Only a positive total is buying and only a negative one selling: all three can be net sellers.
        totals = {k: sum(row[k + 1] for row in window if math.isfinite(row[k + 1])) for k in range(3)
                  if any(math.isfinite(row[k + 1]) for row in window)}
        buyers = sorted((k for k in totals if totals[k] > 0), key=lambda k: -totals[k])
        sellers = sorted((k for k in totals if totals[k] < 0), key=lambda k: totals[k])
        qty = lambda k, lang: _quantity(totals[k], lang, True)
        buy_ko = f'{_GROUPS[buyers[0]][0]}이 가장 많이 순매수했고({qty(buyers[0], "ko")}주)' if buyers else ''
        sell_ko = f'{_GROUPS[sellers[0]][0]}이 가장 많이 순매도했습니다({qty(sellers[0], "ko")}주)' if sellers else ''
        buy_en = f'{_GROUPS[buyers[0]][1]} were the largest net buyers ({qty(buyers[0], "en")} shares)' if buyers else ''
        sell_en = f'{_GROUPS[sellers[0]][1]} were the largest net sellers ({qty(sellers[0], "en")} shares)' if sellers else ''
        if buyers and sellers:
            ko, en = f'{buy_ko}, {sell_ko}.', f'{buy_en} and {sell_en}.'
        elif buyers:
            ko, en = f'{buy_ko}, 순매도한 투자자는 없습니다.', f'{buy_en}; no group was a net seller.'
        elif sellers:
            ko, en = f'순매수한 투자자는 없고 {sell_ko}.', f'no group was a net buyer, and {sell_en}.'
        elif totals:
            ko, en = '세 투자자 모두 순매수 합계가 0입니다.', 'every group’s net buying adds up to zero.'
        else:
            ko = en = ''
        if ko:
            text += ' ' + say(f'최근 {len(window)}거래일 합계로는 {ko}', f'Over the last {len(window)} sessions, {en}')
    return text + ' ' + say('이미 끝난 거래의 기록이며 앞으로의 가격을 알려주지 않습니다.', 'These are completed trades; they do not tell future prices.')


def _read_short_ratio(v, i, c, b, s, say, p):
    day = b[5][i]
    rows = [row for row in s.shorts if row[0] <= day and math.isfinite(row[1])]
    if not rows or rows[-1][0] != day:
        return say('이날의 공매도 자료가 없습니다.', 'No short-sale data for this date.')
    x = rows[-1][1]
    text = say(f'이날 거래량 중 공매도 비중은 {x:.1f}%입니다.', f'Short selling was {x:.1f}% of the day’s volume.')
    window = [row[1] for row in rows[-20:]]
    if len(window) >= 5:
        mean = sum(window) / len(window)
        text += ' ' + say(f'최근 {len(window)}거래일 평균({mean:.1f}%)' + ('보다 높습니다.' if x > mean * 1.2 else '보다 낮습니다.'
                                                                      if x < mean * 0.8 else '과 비슷합니다.'),
                          f'That is {"above" if x > mean * 1.2 else "below" if x < mean * 0.8 else "close to"} the {len(window)}-session average of {mean:.1f}%.')
    return text


_READERS = {name[6:]: fn for name, fn in globals().items() if name.startswith('_read_')}


def study_reading(key, bars, index, *, language='ko', values=None, supply=None, **params):
    """Plain-language reading of `key` at bar `index` (negative counts from the end).

    Explains what the value means for a beginner and names conventional thresholds as
    conventions; never advice. Before enough bars exist it says how many are needed.
    """
    spec = study(key)
    if not isinstance(bars, Bars) or not len(bars):
        raise ValueError('study_reading needs non-empty Bars')
    say = _Say(bars, language)
    i = index + len(bars) if index < 0 else index
    if not 0 <= i < len(bars):
        raise IndexError('bar index out of range')
    # The asset is the caller's to check (indicators.availability); a domestic stock is assumed here.
    code = availability(spec.key, asset='domestic_stock', interval=bars.interval, supply=supply,
                        has_volume=any(math.isfinite(v) for v in bars.volume))
    if code:
        return availability_text(code, say.lang)
    if values is None:
        values = compute_study(spec.key, bars, supply=supply, **params)
    needed = reading_lines(spec.key)
    if spec.category != 'supply' and not all(_at(values, line, i) is not None for line in needed):
        if spec.needs in ('volume', 'ohlcv') and not math.isfinite(bars.volume[i]):
            return say('이 봉의 거래량이 없어 계산하지 않았습니다.', 'This bar has no reported volume, so it was not computed.')
        first = warmup(spec.key) if not params else None
        if first is not None and i < first:
            return say(f'{spec.ko}: 아직 계산할 수 없습니다. 최소 {first + 1}개 봉이 필요합니다(이 봉은 {i + 1}번째).',
                       f'{spec.en}: not available yet. It needs at least {first + 1} bars (this is bar {i + 1}).')
        return say(f'{spec.ko}: 이 봉에서는 값을 계산할 수 없습니다.', f'{spec.en}: no value at this bar.')
    arrays = bars.arrays()
    data = (arrays[0], arrays[1], arrays[2], arrays[3], arrays[4], bars.dates, bars.timestamps)
    merged = {**spec.defaults, **params}
    return _minus(_READERS[spec.key](values, i, arrays[3], data, supply if isinstance(supply, Supply) else Supply(),
                                     say, merged))


def line_readout(key, bars, index, *, language='ko', values=None, supply=None, **params):
    """((line name, formatted value), ...) of `key` at bar `index` for a compact readout."""
    spec = study(key)
    lang = _lang(language)
    i = index + len(bars) if index < 0 else index
    if values is None:
        values = compute_study(spec.key, bars, supply=supply, **params)
    return tuple((line.name(lang), format_value(line.kind, _at(values, line.id, i), lang)) for line in spec.lines)
