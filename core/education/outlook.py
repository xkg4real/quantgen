"""The conclusion part (결론부) of every chart-study explanation (owner request 2026-11-17).

Owner, verbatim: "모든 기술지표 해석에, '결론부'가 필요합니다. 오히려 개념설명을 간소화해도 좋습니다. 기술지표가 이렇게 있을때
상승흐름이 예상되고, 이렇게 있을때 하강흐름이 예상된다. 이부분을 표현해주는게 중요합니다. 그리고 기술지표 해석하는 부분들이
전문가 맞나요? 보통 bb기준 하단에 있을때 추후에 상승이 찾아올 확률이 높다고 해석하는게 전문가의 해석 아닌가요? ... 여러
논문들 참고해서 검토합니다".

For each study: the chart conditions practitioners read as an upward flow (`up`) and as a downward flow (`down`), the
regime in which that reading flips or fails (`regime`), and how strong the published evidence is that those readings
predict returns after costs (`grade` with a one-line reason and the sources it rests on). `now()` says which side the
chart's current state is closer to, from the computed values only.

Sources: a literature review run for this request (originators' rules and peer-reviewed tests, each citation checked by a
second reviewer; corrections applied: e.g. Bollinger's W-bottom is confirmed by the break of the high between the two
lows, MACD and RSI divergences are 'momentum fading' warnings, not timing signals, a 3x ATR drop is an exit rule, a
daily short-sale share cannot show covering). Unverified items and in-house backtests were left out.

These are conditional, textbook readings for education. They are not forecasts, win rates or recommendations, and the
evidence grade says plainly when the readings have not held up after costs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Evidence grades, weakest last: (Korean, English).
GRADES = {
    "strong": ("근거 강함", "Strong evidence"),
    "moderate": ("근거 보통", "Moderate evidence"),
    "mixed": ("근거 엇갈림", "Mixed evidence"),
    "weak": ("근거 약함", "Weak evidence"),
    "none": ("검증 연구 없음", "No published test"),
}

SIDES = {"up": ("상승 흐름 쪽", "Upward flow"), "down": ("하락 흐름 쪽", "Downward flow"),
         "neutral": ("뚜렷하지 않음", "No clear side")}

# key: (concept (ko, en), up ((ko, en), ...), down (...), regime (ko, en), grade, grade reason (ko, en), sources)
OUTLOOK = {
    "sma": (
        ("최근 20일 종가의 평균을 이은 선이에요", "The average of the last 20 closes, as a line"),
        (("종가가 20일선을 위로 넘고 선도 위로 기울면 상승 쪽이에요",
          "A close crossing above the 20-day line while the line turns up reads upward"),
         ("오르는 중 눌림이 20일선 근처에서 멈추고 다시 오르면 상승 유지 쪽이에요",
          "In a rise, a pullback that stops near the line and turns up reads as the trend holding")),
        (("종가가 20일선을 아래로 깨고 선도 아래로 기울면 하락 쪽이에요",
          "A close breaking below the 20-day line while the line turns down reads downward"),
         ("반등이 20일선에 막혀 다시 밀리면 하락 유지 쪽이에요",
          "A rebound that stalls at the line and falls again reads as the fall holding")),
        ("가격이 20일선을 자주 넘나드는 횡보장에선 신호가 잦고 자주 빗나가요",
         "In sideways markets price crosses the line often and the signals often miss"),
        "mixed",
        ("옛 지수 자료와 종목 간 비교에선 정보가 있었지만, 비용·후속 검증에선 많이 약해졌어요",
         "Informative in old index data and across stocks, much weaker after costs and in later tests"),
        ("Brock·Lakonishok·LeBaron (1992)", "Sullivan·Timmermann·White (1999)", "Han·Yang·Zhou (2013)")),
    "ema": (
        ("최근 가격에 무게를 더 둔 12일·26일 평균선이에요", "12- and 26-day averages weighted to recent prices"),
        (("12일선이 26일선을 위로 넘고 두 선 간격이 벌어지면 상승 쪽이에요",
          "The 12-day line crossing above the 26-day line with the gap widening reads upward"),
         ("가격이 두 선 위에 있고 눌림이 12일선에서 멈추면 상승 유지 쪽이에요",
          "Price above both lines with pullbacks stopping at the 12-day line reads as the rise holding")),
        (("12일선이 26일선을 아래로 내려가고 간격이 벌어지면 하락 쪽이에요",
          "The 12-day line crossing below the 26-day line with the gap widening reads downward"),
         ("가격이 두 선 아래에 있고 반등이 12일선에 막히면 하락 유지 쪽이에요",
          "Price below both lines with rebounds stalling at the 12-day line reads as the fall holding")),
        ("두 선이 엉켜 자주 교차하는 횡보장에선 교차 신호가 잘 빗나가요",
         "When the lines tangle in sideways markets, crossings often miss"),
        "mixed",
        ("선물 시장에선 비용 뒤에도 성과가 있었지만, 주식의 짧은 교차는 검증이 약해요",
         "Crossovers held up net of costs in futures; short crossovers on stocks are poorly tested"),
        ("Lukac·Brorsen·Irwin (1988)", "Park·Irwin (2007)")),
    "macd": (
        ("12일·26일 평균선의 간격과 그 변화를 보여줘요", "The gap between the 12- and 26-day averages and its change"),
        (("MACD선이 시그널선을 위로 넘으면 상승 쪽, 0선 위라면 더 무게를 둬요",
          "MACD crossing above its signal line reads upward, more so above zero"),
         ("가격 저점은 낮아지는데 MACD 저점이 높아지면 하락 힘이 약해지는 신호예요",
          "Lower price lows with higher MACD lows warn that the fall is losing force")),
        (("MACD선이 시그널선을 아래로 넘으면 하락 쪽, 0선 아래라면 더 무게를 둬요",
          "MACD crossing below its signal line reads downward, more so below zero"),
         ("가격 고점은 높아지는데 MACD 고점이 낮아지면 상승 힘이 약해지는 신호예요",
          "Higher price highs with lower MACD highs warn that the rise is losing force")),
        ("추세장에서 잘 맞고, 0선 근처를 오가는 횡보장에선 신호가 자주 뒤집혀요",
         "Works in trends; near zero in sideways markets the signals flip often"),
        "weak",
        ("일부 지수에서만 성과가 보였고 다른 시장·기간에선 재현되지 않았어요",
         "Gains appeared in a few indices only and did not replicate elsewhere"),
        ("Chong·Ng (2008)", "Chong·Ng·Liew (2014)")),
    "ichimoku": (
        ("전환선·기준선·구름으로 추세와 지지 구간을 보여줘요", "Lines and a cloud that frame trend and support"),
        (("가격이 구름 위에 머물면 상승 쪽, 구름이 두꺼울수록 받침이 단단해요",
          "Price above the cloud reads upward; a thicker cloud is firmer support"),
         ("전환선이 기준선을 위로 넘고 그 자리가 구름 위면 상승 쪽에 무게를 둬요",
          "The conversion line crossing above the base line above the cloud adds weight upward")),
        (("가격이 구름 아래에 머물면 하락 쪽, 구름이 두꺼울수록 위가 막혀 있어요",
          "Price below the cloud reads downward; a thicker cloud is firmer resistance"),
         ("전환선이 기준선을 아래로 넘고 그 자리가 구름 아래면 하락 쪽에 무게를 둬요",
          "The conversion line crossing below the base line below the cloud adds weight downward")),
        ("가격이 구름 안에 있으면 방향이 정해지지 않은 구간이에요",
         "Price inside the cloud means the direction is undecided"),
        "weak",
        ("연구가 적고, 일부 지수에서 좋아 보인 규칙도 다른 기간엔 맞지 않았어요",
         "Few studies; rules that looked good on some indices failed in other periods"),
        ("Deng 외 (2021)", "Park·Irwin (2007)")),
    "psar": (
        ("가격을 따라붙는 점으로 추세가 바뀐 자리를 보여줘요", "Trailing dots that mark where the trend turned"),
        (("점이 가격 위에서 아래로 옮겨 오면 상승 쪽으로 방향이 바뀐 거예요",
          "Dots moving from above to below price mark a turn upward"),
         ("ADX가 25 위인 추세장에서 나온 상향 전환일수록 무게를 둬요",
          "An upward flip in a trend (ADX above 25) carries more weight")),
        (("점이 가격 아래에서 위로 옮겨 가면 하락 쪽으로 방향이 바뀐 거예요",
          "Dots moving from below to above price mark a turn downward"),
         ("ADX가 25 위인 추세장에서 나온 하향 전환일수록 무게를 둬요",
          "A downward flip in a trend (ADX above 25) carries more weight")),
        ("횡보장에선 점이 자주 뒤집혀 신호가 잦고 잘 빗나가요",
         "In sideways markets the dots flip often and miss"),
        "weak",
        ("주식을 직접 검증한 연구는 찾지 못했어요. 옛 선물 시험의 성과도 이후 사라졌어요",
         "No direct stock test found; its early futures gains later vanished"),
        ("Wilder (1978)", "Lukac·Brorsen·Irwin (1988)")),
    "adx": (
        ("ADX는 추세의 세기, +DI·−DI는 방향을 보여줘요", "ADX shows trend strength; +DI and −DI show direction"),
        (("+DI가 −DI 위에 있고 ADX가 25 위로 오르면 상승 추세가 힘을 받는 쪽이에요",
          "+DI above −DI with ADX rising past 25 reads as an uptrend gaining force"),
         ("ADX가 20 아래에서 올라오며 +DI가 앞서면 새 상승 추세가 생기는 쪽이에요",
          "ADX rising from below 20 with +DI ahead reads as a new uptrend forming")),
        (("−DI가 +DI 위에 있고 ADX가 25 위로 오르면 하락 추세가 힘을 받는 쪽이에요",
          "−DI above +DI with ADX rising past 25 reads as a downtrend gaining force"),
         ("상승 중 ADX가 40 위에서 꺾이면 상승 힘이 빠지는 쪽이에요. 전환은 DI 교차로 확인해요",
          "ADX turning down from above 40 in a rise reads as the rise fading; confirm a turn by the DI cross")),
        ("ADX가 20 아래면 추세가 약한 횡보장이라 DI 교차가 자주 빗나가요",
         "With ADX below 20 the market is ranging and DI crosses often miss"),
        "weak",
        ("수익 예측력을 보인 연구는 거의 없고, 추세·횡보를 가르는 거름망으로 쓰여요",
         "Little evidence it predicts returns; used as a trend-or-range filter"),
        ("Wilder (1978)", "Park·Irwin (2007)")),
    "envelope": (
        ("이동평균선 위아래로 같은 비율(±5%)의 띠를 둔 선이에요", "Bands a fixed ±5% around a moving average"),
        (("평균선이 평평할 때 아래 띠 밖 주가가 안으로 돌아오면 반등 쪽이에요",
          "With a flat average, price returning inside from below the lower band reads as a rebound"),
         ("평균선이 오르는 중 평균선까지 눌렸다 다시 오르면 상승 지속 쪽이에요",
          "With a rising average, a dip to the average that turns up reads as the rise continuing")),
        (("평균선이 내리는 중 주가가 아래 띠 밖에 머물면 하락 추세 쪽이에요",
          "With a falling average, price staying below the lower band reads as a downtrend"),
         ("평균선이 평평할 때 위 띠 밖 주가가 안으로 돌아오면 되돌림 쪽이에요",
          "With a flat average, price returning inside from above the upper band reads as a pullback")),
        ("폭이 고정이라 변동성이 큰 종목·시기엔 자주 뚫리고, 작을 땐 잘 닿지 않아요",
         "Fixed width: often pierced when volatility is high, rarely touched when it is low"),
        "weak",
        ("비용을 뺀 직접 검증이 거의 없고, 바탕인 이동평균 규칙의 근거도 엇갈려요",
         "Hardly tested net of costs; the moving-average rules beneath it are mixed"),
        ("Leung·Chong (2003)", "Brock·Lakonishok·LeBaron (1992)")),
    "keltner": (
        ("평균선 위아래로 ATR 배수만큼 띠를 두른 통로예요", "A channel an ATR multiple around an average"),
        (("중심선이 오르는 중 종가가 위 통로 밖에서 마감하면 상승 추세 쪽이에요",
          "With a rising centre line, a close above the upper channel reads as an uptrend"),
         ("상승 추세 중 중심선까지 눌렸다 다시 오르면 상승 지속 쪽이에요",
          "In an uptrend, a dip to the centre line that turns up reads as the rise continuing")),
        (("중심선이 내리는 중 종가가 아래 통로 밖에서 마감하면 하락 추세 쪽이에요",
          "With a falling centre line, a close below the lower channel reads as a downtrend"),
         ("하락 추세 중 중심선까지 반등했다 다시 밀리면 하락 지속 쪽이에요",
          "In a downtrend, a rebound to the centre line that falls again reads as the fall continuing")),
        ("통로 밖 종가는 추세장에선 힘의 표시지만, 횡보장에선 금방 되돌아오기 쉬워요",
         "Closes outside show strength in trends but soon return in sideways markets"),
        "none",
        ("켈트너 통로를 직접 검증한 동료심사 연구는 찾지 못했어요",
         "No peer-reviewed test of Keltner channels was found"),
        ("Park·Irwin (2007)",)),
    "donchian": (
        ("최근 20일 최고가와 최저가로 그린 통로예요", "A channel of the 20-day high and low"),
        (("종가가 직전 20일 최고가를 넘으면 상승 추세 쪽이지만, 실패하는 돌파도 많아요",
          "A close above the prior 20-day high reads as an uptrend, though many breakouts fail"),
         ("위·아래 선이 함께 계단처럼 올라가면 상승 흐름 쪽이에요",
          "Both lines stepping up together reads as an upward flow")),
        (("종가가 직전 20일 최저가를 깨면 하락 추세 쪽이지만, 실패하는 이탈도 많아요",
          "A close below the prior 20-day low reads as a downtrend, though many breakdowns fail"),
         ("돌파 직후 돌파한 가격 아래로 되밀리면 가짜 돌파 쪽이에요",
          "Falling back under the breakout price right after reads as a false breakout")),
        ("추세장에선 돌파가 잘 이어지지만, 횡보장에선 가짜 돌파가 잦아요",
         "Breakouts follow through in trends; false breakouts are common in ranges"),
        "mixed",
        ("여러 선물 시장에선 수십 년간 비용 뒤에도 버텼지만, 개별 주식에선 약해졌어요",
         "Held up net of costs across futures for decades, weaker in single stocks"),
        ("Brock·Lakonishok·LeBaron (1992)", "Szakmary·Shen·Sharma (2010)", "Moskowitz·Ooi·Pedersen (2012)")),
    "rsi": (
        ("최근 오른 힘과 내린 힘을 0~100으로 나타낸 값이에요", "Recent up-moves versus down-moves on a 0-100 scale"),
        (("RSI가 30 아래에 있다가 다시 30 위로 올라오면 반등 쪽이에요",
          "RSI climbing back above 30 from below reads as a rebound"),
         ("상승 추세에서 RSI가 40~50에서 받치고 다시 오르면 상승 지속 쪽이에요",
          "In an uptrend, RSI holding 40-50 and turning up reads as the rise continuing")),
        (("RSI가 70 위에 있다가 다시 70 아래로 내려오면 조정 쪽이에요",
          "RSI falling back below 70 from above reads as a pullback"),
         ("하락 추세에서 RSI가 50~60에서 막히고 꺾이면 하락 지속 쪽이에요",
          "In a downtrend, RSI stalling at 50-60 and turning down reads as the fall continuing")),
        ("강한 추세에선 70 위·30 아래에 오래 머물러, 과열·침체만 보면 틀리기 쉬워요",
         "In strong trends RSI stays above 70 or below 30 for long; reading only extremes misleads"),
        "mixed",
        ("일부 지수에선 30·70 규칙이 매수 보유를 앞섰지만, 다른 시장·비용 반영 후엔 약해요",
         "30/70 rules beat buy-and-hold in some indices, little elsewhere or after costs"),
        ("Wilder (1978)", "Wong·Manzur·Chew (2003)", "Chong·Ng (2008)")),
    "stoch": (
        ("최근 고가~저가 범위에서 종가가 어디쯤인지 보여줘요", "Where the close sits in the recent high-low range"),
        (("%K가 20 아래에서 %D를 위로 넘고 20 위로 올라오면 반등 쪽이에요",
          "%K crossing above %D below 20 and rising past 20 reads as a rebound"),
         ("상승 추세에서 80 위에 오래 머물면 힘이 강하다는 쪽이에요",
          "Staying above 80 in an uptrend reads as strength")),
        (("%K가 80 위에서 %D를 아래로 넘고 80 아래로 내려오면 조정 쪽이에요",
          "%K crossing below %D above 80 and falling under 80 reads as a pullback"),
         ("하락 추세에서 20 아래에 오래 머물면 약세가 이어지는 쪽이에요",
          "Staying below 20 in a downtrend reads as weakness continuing")),
        ("오르내림이 반복되는 장에서 더 잘 맞고, 강한 추세에선 끝 구간에 붙어 있어요",
         "Works better in swinging markets; in strong trends it sticks to the ends"),
        "weak",
        ("직접 검증이 적고, 종목·설정에 따라 결과가 달라 비용 뒤 이익이 작아요",
         "Few direct tests; results vary by stock and setting, small after costs"),
        ("Lane (1984)", "Rosillo 외 (2013)")),
    "stochrsi": (
        ("RSI가 최근 범위에서 어디쯤인지 다시 잰 값이에요", "Where RSI sits within its own recent range"),
        (("20 아래에 있다가 다시 20 위로 올라오면 단기 반등 쪽이에요",
          "Rising back above 20 from below reads as a short rebound"),
         ("상승 추세 중 20 근처까지 내려왔다 다시 오르면 눌림 뒤 재상승 쪽이에요",
          "In an uptrend, a dip toward 20 that turns up reads as a resumed rise")),
        (("80 위에 있다가 다시 80 아래로 내려오면 단기 조정 쪽이에요",
          "Falling back below 80 from above reads as a short pullback"),
         ("하락 추세 중 80 근처에서 다시 꺾이면 반등이 끝나는 쪽이에요",
          "In a downtrend, turning down near 80 reads as the rebound ending")),
        ("아주 민감해 신호가 잦아요. 큰 추세와 같은 방향의 신호가 더 믿을 만해요",
         "Very sensitive and busy; signals in the direction of the larger trend are sturdier"),
        "none",
        ("스토캐스틱 RSI를 직접 검증한 동료심사 연구는 찾지 못했어요",
         "No peer-reviewed test of Stochastic RSI was found"),
        ("Chande·Kroll (1994)",)),
    "cci": (
        ("주가가 평소 평균에서 얼마나 벗어났는지 잰 값이에요", "How far price has moved from its usual average"),
        (("추세장에서 CCI가 +100 위로 올라서면 상승 흐름이 힘을 받는 쪽이에요",
          "In a trend, CCI rising above +100 reads as the upward flow gaining force"),
         ("−100 아래에 있다가 다시 −100 위로 올라오면 반등 쪽이에요",
          "Rising back above −100 from below reads as a rebound")),
        (("추세장에서 CCI가 −100 아래로 내려가면 하락 흐름이 힘을 받는 쪽이에요",
          "In a trend, CCI falling below −100 reads as the downward flow gaining force"),
         ("+100 위에 있다가 다시 +100 아래로 내려오면 조정 쪽이에요",
          "Falling back below +100 from above reads as a pullback")),
        ("추세장에선 ±100 돌파를 흐름의 시작으로, 횡보장에선 되돌림 신호로 읽어요",
         "In trends a ±100 break starts a flow; in ranges it is a reversion cue"),
        "none",
        ("확인된 동료심사 검증이 없고, 찾은 연구도 비용·표본 밖 검증이 없는 예시 수준이에요",
         "No confirmed peer-reviewed test; the studies found are illustrative, without costs or out-of-sample checks"),
        ("Lambert (1980)",)),
    "williams": (
        ("종가가 최근 최고가에서 얼마나 내려와 있는지 보여줘요", "How far the close sits below the recent high"),
        (("−80 아래에 있다가 다시 −80 위로 올라오면 반등 쪽이에요",
          "Rising back above −80 from below reads as a rebound"),
         ("상승 추세에서 −20 위에 자주 머물면 힘이 강한 쪽이에요",
          "Staying above −20 in an uptrend reads as strength")),
        (("−20 위에 있다가 다시 −20 아래로 내려오면 조정 쪽이에요",
          "Falling back below −20 from above reads as a pullback"),
         ("하락 추세에서 −80 아래에 자주 머물면 약세가 이어지는 쪽이에요",
          "Staying below −80 in a downtrend reads as weakness continuing")),
        ("스토캐스틱과 같은 계산이라 강한 추세에선 끝 구간에 오래 머물러요",
         "The same arithmetic as stochastics: in strong trends it stays at the ends"),
        "weak",
        ("윌리엄스 %R 자체를 검증한 동료심사 연구는 찾지 못했어요",
         "No peer-reviewed test of Williams %R itself was found"),
        ("Williams (1973)",)),
    "roc": (
        ("지금 가격이 12일 전보다 몇 % 달라졌는지 보여줘요", "How much price changed against 12 days ago, in %"),
        (("ROC가 0 아래에서 0 위로 올라서면 상승 흐름 쪽이에요",
          "ROC crossing above zero reads as an upward flow"),
         ("ROC가 0 위에서 더 높아지면 오르는 속도가 붙는 쪽이에요",
          "ROC rising further above zero reads as the rise speeding up")),
        (("ROC가 0 위에서 0 아래로 내려서면 하락 흐름 쪽이에요",
          "ROC crossing below zero reads as a downward flow"),
         ("주가는 오르는데 ROC가 낮아지면 오르는 속도가 줄어드는 쪽이에요",
          "Rising price with a falling ROC reads as the rise slowing")),
        ("몇 달 흐름은 이어지는 편이고, 며칠 급변은 되돌림이 잦지만 거래가 몰린 급락은 더 가기도 해요",
         "Moves over months tend to persist; sharp moves over days often revert, though heavy-volume drops can extend"),
        "mixed",
        ("9~12개월 모멘텀은 근거가 강하지만, 12일 같은 짧은 기간은 오히려 되돌림 구간이에요",
         "9-12 month momentum is well supported; 12-day horizons fall where stocks tend to revert"),
        ("Moskowitz·Ooi·Pedersen (2012)", "Jegadeesh (1990)", "Lehmann (1990)")),
    "disparity": (
        ("종가를 20일 평균선으로 나눈 값으로, 100이 기준이에요", "The close over its 20-day average; 100 is the line"),
        (("이격도가 95 아래에 있다가 다시 95 위로 올라오면 반등 쪽이에요",
          "Rising back above 95 from below reads as a rebound"),
         ("이격도가 100 위에서 유지되면 평균선 위 상승 흐름 쪽이에요",
          "Staying above 100 reads as an upward flow above the average")),
        (("이격도가 105 위에 있다가 다시 105 아래로 내려오면 조정 쪽이에요",
          "Falling back below 105 from above reads as a pullback"),
         ("이격도가 100 아래에서 유지되면 평균선 아래 하락 흐름 쪽이에요",
          "Staying below 100 reads as a downward flow below the average")),
        ("급등·급락장에선 105·95를 넘어 더 벌어질 수 있어 추세 방향을 함께 봐요",
         "In sharp moves it can stretch past 105 or 95; read it with the trend"),
        "mixed",
        ("평균선 위·아래 자체는 정보가 있지만, 105·95 되돌림 기준은 검증된 적이 없어요",
         "Above versus below the average carries information; the 105/95 thresholds are untested"),
        ("Brock·Lakonishok·LeBaron (1992)", "Han·Yang·Zhou (2013)")),
    "psychology": (
        ("최근 10일 가운데 오른 날이 몇 %인지 보여줘요", "The share of up days in the last 10 days"),
        (("25% 아래에 있다가 다시 25% 위로 올라오면 비관이 풀리는 쪽이에요",
          "Rising back above 25% from below reads as pessimism easing"),
         ("50% 위로 올라서고 주가도 평균선 위면 상승 흐름 쪽이에요",
          "Above 50% with price above its average reads as an upward flow")),
        (("75% 위에 있다가 다시 75% 아래로 내려오면 과열이 식는 쪽이에요",
          "Falling back below 75% from above reads as overheating cooling"),
         ("50% 아래로 내려서고 주가도 평균선 아래면 하락 흐름 쪽이에요",
          "Below 50% with price below its average reads as a downward flow")),
        ("오른 날 수만 세고 폭은 안 봐서, 추세가 강하면 75% 위에 오래 머물러요",
         "It counts days, not sizes; in strong trends it stays above 75%"),
        "none",
        ("투자심리선의 예측력을 검증한 동료심사 연구는 찾지 못했어요",
         "No peer-reviewed test of the psychological line was found"),
        ("Lehmann (1990)",)),
    "bb": (
        ("20일 평균선 위아래로 가격 흩어짐(표준편차)의 2배만큼 띠를 둘러요",
         "Bands two standard deviations around the 20-day average"),
        (("중심선이 평평할 때 하단 밖 종가가 다시 밴드 안으로 들어오면 반등 쪽이에요",
          "With a flat middle line, a close returning inside from below the lower band reads as a rebound"),
         ("두 번째 저점이 더 낮아도 하단 안에서 멈추고 사이 고점을 넘으면 바닥 쪽이에요",
          "A second, lower low that holds inside the band, then a break of the high between, reads as a bottom")),
        (("중심선이 내려가며 종가가 하단 밖에 머물고 밴드가 넓어지면 하락 지속 쪽이에요",
          "A falling middle line with closes staying below a widening lower band reads as the fall continuing"),
         ("중심선이 평평할 때 상단 밖 종가가 안으로 돌아오면 되돌림 쪽이에요",
          "With a flat middle line, a close returning inside from above the upper band reads as a pullback")),
        ("횡보장에선 하단이 되돌림 자리가 되곤 하지만, 추세장에선 하단을 타고 더 내려가요",
         "In ranges the lower band is often a turning point; in trends price walks down along it"),
        "weak",
        ("비용을 빼거나 널리 알려진 뒤의 검증에선 밴드 터치의 우위가 거의 없었어요",
         "After costs, and once the bands became popular, band touches showed little edge"),
        ("Bollinger (2001)", "Lento·Gradojevic·Wright (2007)", "Fang·Jacobsen·Qin (2017)")),
    "percent_b": (
        ("가격이 볼린저 밴드 안 어디쯤인지 0~1로 보여줘요", "Where price sits within the Bollinger Bands, 0 to 1"),
        (("중심선이 평평할 때 %b가 0 아래에서 다시 0 위로 오르면 반등 쪽이에요",
          "With a flat middle line, %b rising back above 0 reads as a rebound"),
         ("주가는 새 저점인데 %b 저점이 높아지고 사이 고점을 넘으면 바닥 쪽이에요",
          "A new price low with a higher %b low, then a break of the high between, reads as a bottom")),
        (("%b가 0.5 아래에 오래 머물고 중심선이 내리면 하락 흐름 쪽이에요",
          "%b staying under 0.5 with a falling middle line reads as a downward flow"),
         ("중심선이 평평할 때 %b가 1 위에서 다시 1 아래로 내리면 되돌림 쪽이에요",
          "With a flat middle line, %b falling back below 1 reads as a pullback")),
        ("횡보장에선 0 아래가 과매도지만, 추세장에선 하락 힘이 강하다는 뜻이 돼요",
         "Below 0 is oversold in a range, but in a trend it means strong selling"),
        "weak",
        ("밴드를 0~1로 다시 잰 값이라 볼린저 밴드의 약한 근거를 그대로 물려받아요",
         "A rescaling of the bands, so it inherits their weak evidence"),
        ("Bollinger (2001)", "Fang·Jacobsen·Qin (2017)")),
    "bandwidth": (
        ("밴드 폭을 중심선으로 나눠 변동성 크기를 본 값이에요", "Band width over the middle line: the size of moves"),
        (("폭이 6개월 최저권까지 좁아진 뒤 종가가 상단 밖에서 마감하면 상승 쪽이에요",
          "After width shrinks to a six-month low, a close above the upper band reads upward"),
         ("좁던 폭이 넓어지기 시작하고 중심선이 위로 돌면 상승 확장 쪽이에요",
          "Narrow width starting to widen while the middle line turns up reads as an upward expansion")),
        (("폭이 6개월 최저권까지 좁아진 뒤 종가가 하단 밖에서 마감하면 하락 쪽이에요",
          "After width shrinks to a six-month low, a close below the lower band reads downward"),
         ("좁던 폭이 넓어지기 시작하고 중심선이 아래로 돌면 하락 확장 쪽이에요",
          "Narrow width starting to widen while the middle line turns down reads as a downward expansion")),
        ("폭이 좁으면 큰 움직임이 가깝다는 뜻일 뿐, 방향은 돌파로 보고 첫 돌파는 속기도 해요",
         "Narrow width only says a big move is near; direction comes from the break, and the first break can fake"),
        "weak",
        ("좁은 폭 뒤 변동성이 커지는 건 꾸준하지만, 방향을 맞힌다는 근거는 없어요",
         "Low width reliably precedes bigger moves, but not their direction"),
        ("Bollinger (2001)", "Fang·Jacobsen·Qin (2017)")),
    "atr": (
        ("갭까지 포함한 하루 변동 폭의 14일 평균이에요", "The 14-day average daily range, gaps included"),
        (("급락 때 치솟았던 ATR이 꺾여 내려오면 불안이 가라앉는 쪽이에요",
          "ATR turning down after a spike in a sell-off reads as stress easing"),
         ("낮던 ATR이 커지며 종가가 위쪽 저항을 넘으면 상승 돌파 쪽이에요",
          "A low ATR expanding as the close clears resistance reads as an upward breakout")),
        (("주가가 내리며 ATR이 함께 커지면 불안이 커지는 하락 쪽이에요",
          "Price falling while ATR rises reads as a fall with growing stress"),
         ("상승 중 종가가 고점에서 ATR 3배 넘게 밀리면 추세가 약해진 쪽이에요",
          "A close more than 3 ATR below the high in a rise reads as the trend weakening")),
        ("ATR은 움직임의 크기만 알려줘요. 방향은 가격과 추세선으로 따로 봐요",
         "ATR gives only the size of moves; read direction from price"),
        "weak",
        ("변동성이 이어진다는 근거는 있지만, ATR이 방향을 알려준다는 근거는 없어요",
         "Volatility persists, but nothing shows ATR predicts direction"),
        ("Wilder (1978)", "Moreira·Muir (2017)")),
    "volume_ma": (
        ("오늘 거래량을 최근 20일 평균과 비교한 값이에요", "Today's volume against its 20-day average"),
        (("가격이 오르며 거래량이 20일 평균을 크게 넘으면 상승에 힘이 실린 쪽이에요",
          "Price rising on volume well above average reads as force behind the rise"),
         ("저항선을 넘는 날 거래량이 평균보다 많으면 돌파에 힘이 실린 쪽이에요",
          "Above-average volume on a break of resistance reads as force behind the breakout")),
        (("가격이 내리며 거래량이 평균을 크게 넘으면 매도 압력 쪽이지만, 뒤이어 반등하기도 해요",
          "Price falling on heavy volume reads as selling pressure, though rebounds often follow"),
         ("가격은 새 고점인데 거래량이 평균보다 적으면 상승 힘이 약해진 쪽이에요",
          "A new high on below-average volume reads as the rise losing force")),
        ("거래량은 방향이 아니라 힘이에요. 늘 가격과 함께 봐요",
         "Volume is force, not direction; always read it with price"),
        "mixed",
        ("거래량 급증과 다음 달 수익의 관련을 보인 연구는 있지만, 기간에 따라 방향이 바뀌어요",
         "Volume shocks relate to next-month returns, but the sign changes with the horizon"),
        ("Gervais·Kaniel·Mingelgrin (2001)", "Lee·Swaminathan (2000)")),
    "obv": (
        ("오른 날 거래량은 더하고 내린 날은 뺀 누적선이에요", "Volume added on up days and subtracted on down days"),
        (("가격은 옆걸음인데 OBV가 먼저 고점을 높이면 매집 쪽이에요",
          "OBV making higher highs while price moves sideways reads as accumulation"),
         ("가격과 OBV가 함께 직전 고점을 넘으면 상승 확인 쪽이에요",
          "Price and OBV clearing their prior highs together reads as the rise confirmed")),
        (("가격은 새 고점인데 OBV가 고점을 못 넘으면 상승 힘이 약한 쪽이에요",
          "A new price high without a new OBV high reads as a weak rise"),
         ("가격과 OBV가 함께 직전 저점을 깨면 하락 확인 쪽이에요",
          "Price and OBV breaking their prior lows together reads as the fall confirmed")),
        ("값보다 기울기를 봐요. 하루 거래량 폭증에 흔들리고 횡보장에선 헛신호가 잦아요",
         "Read its slope, not its level; one-day volume spikes and ranges give false cues"),
        "weak",
        ("직접 검증이 적고, 자료 선택을 통제하면 성과가 덜 성숙한 시장·옛 기간에만 남아요",
         "Few direct tests; after data-snooping control, gains remain only in young markets and old data"),
        ("Granville (1963)", "Hsu·Kuan (2005)")),
    "mfi": (
        ("거래량을 반영한 RSI로, 0~100 사이 값이에요", "A volume-weighted RSI on a 0-100 scale"),
        (("MFI가 20 아래에 있다가 다시 20 위로 올라오면 반등 쪽이에요",
          "MFI rising back above 20 from below reads as a rebound"),
         ("상승 추세에서 MFI가 50 위를 지키면 매수세가 이어지는 쪽이에요",
          "MFI holding above 50 in an uptrend reads as buying continuing")),
        (("MFI가 80 위에 있다가 다시 80 아래로 내려오면 조정 쪽이에요",
          "MFI falling back below 80 from above reads as a pullback"),
         ("하락 추세에서 MFI가 50 아래에 머물면 매도세가 이어지는 쪽이에요",
          "MFI staying below 50 in a downtrend reads as selling continuing")),
        ("강한 추세에선 80 위·20 아래에 오래 머물러, 반대로 읽으면 틀리기 쉬워요",
         "In strong trends it stays above 80 or below 20; fading it often fails"),
        "weak",
        ("MFI를 직접 검증한 동료심사 연구는 찾지 못했어요",
         "No peer-reviewed test of MFI was found"),
        ()),
    "vwap": (
        ("거래량을 가중한 평균 가격, 곧 평균 체결 단가예요", "The volume-weighted average price paid"),
        (("가격이 VWAP 위에 머물고 VWAP도 오르면 매수 우위 쪽이에요",
          "Price above a rising VWAP reads as buyers in control"),
         ("VWAP 아래로 밀렸다가 다시 위로 올라서면 반등 쪽이에요",
          "Price recovering above VWAP after dipping below reads as a rebound")),
        (("가격이 VWAP 아래에 머물고 VWAP도 내리면 매도 우위 쪽이에요",
          "Price below a falling VWAP reads as sellers in control"),
         ("VWAP까지 반등했다가 막히고 다시 밀리면 하락 유지 쪽이에요",
          "A rebound that stalls at VWAP and falls again reads as the fall holding")),
        ("원래 체결 품질을 재는 기준선이에요. 시작점이 바뀌면 값도 달라져요",
         "It is an execution benchmark; a different start gives a different value"),
        "weak",
        ("검증된 쓰임은 체결 기준선이고, 수익 예측 근거는 아직 약해요",
         "Its documented use is as an execution benchmark; return prediction is unproven"),
        ("Berkowitz·Logue·Noser (1988)",)),
    "investor_flow": (
        ("외국인·기관·개인이 하루에 순매수한 수량이에요", "Daily net buying by foreigners, institutions and individuals"),
        (("외국인과 기관이 여러 날 함께 순매수하면 수급이 받쳐주는 쪽이에요",
          "Foreigners and institutions net buying together for several days reads as support"),
         ("개인이 판 물량을 외국인·기관이 함께 받아가면 수급이 좋아지는 쪽이에요",
          "Foreigners and institutions absorbing individuals' selling reads as improving demand")),
        (("외국인과 기관이 여러 날 함께 순매도하면 수급이 약해진 쪽이에요",
          "Foreigners and institutions net selling together for several days reads as weak demand"),
         ("지수가 빠지는데 개인만 계속 순매수하면 단기 약세가 이어지는 쪽이에요",
          "Only individuals buying while the index falls reads as short-term weakness continuing")),
        ("외국인은 오른 뒤 따라 사는 편이라, 하루 수급만으론 다음 방향을 맞히기 어려워요",
         "Foreigners tend to buy after rises, so one day's flows rarely tell the next move"),
        "mixed",
        ("누가 사고파는지는 알려주지만, 외국인 매매는 지난 수익을 따라가는 편이라 예측력은 엇갈려요",
         "Shows who trades; foreign flows follow past returns, so predictive power is mixed"),
        ("Choe·Kho·Stulz (1999)", "Choe·Kho·Stulz (2005)")),
    "short_ratio": (
        ("하루 거래량 중 공매도가 차지한 비중이에요", "Short sales as a share of daily volume"),
        (("공매도 비중이 높았다가 평소 수준으로 줄면 새 하락 베팅이 줄어든 쪽이에요",
          "A high short share falling back to normal reads as fewer new bets on a fall"),
         ("공매도 비중이 평소로 돌아온 뒤에도 가격이 버티면 하락 압력이 줄어든 쪽이에요",
          "Price holding after the short share normalises reads as less downward pressure")),
        (("공매도 비중이 평소보다 크게 높아지면 이후 몇 주 약세 쪽이에요",
          "A short share well above normal reads as weakness over the following weeks"),
         ("주가가 오른 뒤 공매도 비중이 급증하면 되돌림 쪽이에요",
          "A jump in the short share after a rise reads as a pullback")),
        ("공매도엔 헤지·시장조성 물량도 섞여 있어, 비중만으론 단정하기 어려워요",
         "Short sales include hedging and market making; the share alone is not decisive"),
        "moderate",
        ("공매도가 많은 종목의 몇 주 수익이 낮았다는 연구가 여럿 있지만, 효과는 작아요",
         "Several studies find heavily shorted stocks lag over weeks, but the effect is small"),
        ("Boehmer·Jones·Zhang (2008)", "Diether·Lee·Werner (2009)")),
}


@dataclass(frozen=True)
class Outlook:
    key: str
    concept: str
    up: tuple
    down: tuple
    regime: str
    grade: str          # a GRADES key
    grade_text: str     # '근거 약함' ...
    grade_reason: str
    sources: tuple


@dataclass(frozen=True)
class Now:
    side: str           # 'up' | 'down' | 'neutral'
    label: str          # '상승 흐름 쪽' ...
    reason: str         # the observed facts behind it


def _ko(language):
    return str(language or "ko").startswith("ko")


def outlook(key, language="ko"):
    """The conclusion of `key` in the window language."""
    concept, up, down, regime, grade, reason, sources = OUTLOOK[key]
    pick = 0 if _ko(language) else 1
    return Outlook(key, concept[pick], tuple(item[pick] for item in up), tuple(item[pick] for item in down),
                   regime[pick], grade, GRADES[grade][pick], reason[pick], tuple(sources))


# What the chart shows now --------------------------------------------------------------------------------------
def _at(values, line, i):
    try:
        v = float(values[line][i])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _series_at(series, i):
    try:
        v = float(series[i])
    except (IndexError, TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _slope(values, line, i, back=5):
    """Relative change of a line over `back` bars (None when unknown)."""
    a, b = _at(values, line, i - back), _at(values, line, i)
    if a is None or b is None or a == 0 or i - back < 0:
        return None
    return (b - a) / abs(a)


def _crossed_up(values, line, level, i, within=3):
    """The line rose through `level` within the last `within` bars and is above it now."""
    now = _at(values, line, i)
    if now is None or now <= level:
        return False
    for j in range(i - 1, max(-1, i - within - 1), -1):
        v = _at(values, line, j)
        if v is not None and v <= level:
            return True
    return False


def _crossed_down(values, line, level, i, within=3):
    now = _at(values, line, i)
    if now is None or now >= level:
        return False
    for j in range(i - 1, max(-1, i - within - 1), -1):
        v = _at(values, line, j)
        if v is not None and v >= level:
            return True
    return False


FLAT = 0.004   # a middle line moving less than 0.4% over five bars is 'flat'


def _say(language, ko, en):
    return ko if _ko(language) else en


def _num(value, digits=1):
    """A figure with the typographic minus the screen uses (core.education.study_guide._minus)."""
    text = f"{value:,.{digits}f}" if abs(value) >= 1000 else f"{value:.{digits}f}"
    return text.replace("-", "−")


def _close_slope(bars, i, n=20, back=5):
    """Relative change over `back` bars of the n-bar average close (the bands' middle line), or None."""
    if i - back - n + 1 < 0:
        return None
    try:
        now = sum(float(bars.close[j]) for j in range(i - n + 1, i + 1)) / n
        then = sum(float(bars.close[j]) for j in range(i - back - n + 1, i - back + 1)) / n
    except (IndexError, TypeError, ValueError):
        return None
    if not (math.isfinite(now) and math.isfinite(then)) or then == 0:
        return None
    return (now - then) / abs(then)


def _now_band(values, bars, i, upper, lower, middle, language, name_ko, name_en):
    close = _series_at(bars.close, i)
    up_v, lo_v = _at(values, upper, i), _at(values, lower, i)
    if close is None or None in (up_v, lo_v):
        return None
    mid_now = _at(values, middle, i) if middle else (up_v + lo_v) / 2
    if middle:
        slope = _slope(values, middle, i)
    else:
        a_u, a_l = _at(values, upper, i - 5), _at(values, lower, i - 5)
        slope = None if None in (a_u, a_l) or i < 5 else (mid_now - (a_u + a_l) / 2) / abs((a_u + a_l) / 2)
    flat = slope is not None and abs(slope) < FLAT
    rising, falling = slope is not None and slope >= FLAT, slope is not None and slope <= -FLAT
    prev = [(_series_at(bars.close, j), _at(values, upper, j), _at(values, lower, j)) for j in range(max(0, i - 3), i)]
    was_below = any(c is not None and l is not None and c < l for c, _u, l in prev)
    was_above = any(c is not None and u is not None and c > u for c, u, _l in prev)
    if close < lo_v:
        if falling:
            return "down", _say(language, f"종가가 {name_ko} 하단 밖이고 중심선이 내려가고 있어요",
                                f"The close is below the lower {name_en} and the middle line is falling")
        return "neutral", _say(language, f"종가가 {name_ko} 하단 밖이에요. 다시 안으로 들어오는지 봐요",
                               f"The close is below the lower {name_en}; watch for a return inside")
    if close > up_v:
        if rising:
            return "up", _say(language, f"종가가 {name_ko} 상단 밖이고 중심선이 오르고 있어요",
                              f"The close is above the upper {name_en} and the middle line is rising")
        return "neutral", _say(language, f"종가가 {name_ko} 상단 밖이에요. 다시 안으로 들어오는지 봐요",
                               f"The close is above the upper {name_en}; watch for a return inside")
    if was_below and not falling:
        return "up", _say(language, f"하단 밖에 있던 종가가 {name_ko} 안으로 돌아왔고 중심선이 {'평평해요' if flat else '오르고 있어요'}",
                          f"The close came back inside from below and the middle line is {'flat' if flat else 'rising'}")
    if was_above and not rising:
        return "down", _say(language, f"상단 밖에 있던 종가가 {name_ko} 안으로 돌아왔고 중심선이 {'평평해요' if flat else '내려가고 있어요'}",
                            f"The close came back inside from above and the middle line is {'flat' if flat else 'falling'}")
    if rising and close >= mid_now:
        return "up", _say(language, "종가가 중심선 위이고 중심선이 오르고 있어요",
                          "The close is above a rising middle line")
    if falling and close <= mid_now:
        return "down", _say(language, "종가가 중심선 아래이고 중심선이 내려가고 있어요",
                            "The close is below a falling middle line")
    return "neutral", _say(language, f"종가가 {name_ko} 안에 있고 뚜렷한 조건이 없어요",
                           f"The close is inside the {name_en} with no clear condition")


def _now_level(values, i, line, low, high, language, unit="", digits=1, up_ok=True, down_ok=True):
    """Oscillators read by their re-crossings of `low` / `high`. up_ok / down_ok: whether the trend condition of
    that side holds (the bands' middle line for %b)."""
    v = _at(values, line, i)
    if v is None:
        return None
    shown, lo, hi = _num(v, digits) + unit, _num(low, 0 if float(low).is_integer() else 1) + unit, \
        _num(high, 0 if float(high).is_integer() else 1) + unit
    if _crossed_up(values, line, low, i) and up_ok:
        return "up", _say(language, f"{lo} 아래에 있다가 다시 위로 올라왔어요 (지금 {shown})",
                          f"It rose back above {lo} (now {shown})")
    if _crossed_down(values, line, high, i) and down_ok:
        return "down", _say(language, f"{hi} 위에 있다가 다시 아래로 내려왔어요 (지금 {shown})",
                            f"It fell back below {hi} (now {shown})")
    if v >= high:
        return "neutral", _say(language, f"{hi} 위에 있어요 (지금 {shown}). 추세가 강하면 오래 머물 수 있어요",
                               f"It is above {hi} (now {shown}); in strong trends it can stay there")
    if v <= low:
        return "neutral", _say(language, f"{lo} 아래에 있어요 (지금 {shown}). 다시 올라오는지 봐요",
                               f"It is below {lo} (now {shown}); watch for a move back above")
    return "neutral", _say(language, f"{lo}~{hi} 사이에 있어요 (지금 {shown})",
                           f"It is between {lo} and {hi} (now {shown})")


def _trend(values_sma, i):
    return _slope(values_sma, "SMA20", i)


def now(key, values, bars, index=-1, language="ko"):
    """Which side of `outlook(key)` the chart's bar `index` is closer to, or None when the values cannot say.
    A 'neutral' answer still carries what was observed."""
    if values is None or bars is None:
        return None
    n = len(bars.close)
    i = index + n if index < 0 else index
    if not 0 <= i < n:
        return None
    result = None
    close = _series_at(bars.close, i)
    if key == "sma":
        sma, slope = _at(values, "SMA20", i), _slope(values, "SMA20", i)
        if close is not None and sma is not None and slope is not None:
            if close > sma and slope > 0:
                result = "up", _say(language, "종가가 20일선 위이고 20일선이 오르고 있어요", "The close is above a rising 20-day line")
            elif close < sma and slope < 0:
                result = "down", _say(language, "종가가 20일선 아래이고 20일선이 내려가고 있어요", "The close is below a falling 20-day line")
            else:
                result = "neutral", _say(language, "가격 위치와 20일선 기울기가 엇갈려요", "Price position and the line's slope disagree")
    elif key == "ema":
        fast, slow = _at(values, "EMA12", i), _at(values, "EMA26", i)
        f0, s0 = _at(values, "EMA12", i - 3), _at(values, "EMA26", i - 3)
        if None not in (fast, slow, f0, s0):
            gap, gap0 = fast - slow, f0 - s0
            if gap > 0 and gap >= gap0:
                result = "up", _say(language, "12일선이 26일선 위이고 간격이 벌어지고 있어요", "The 12-day line is above the 26-day line and the gap is widening")
            elif gap < 0 and gap <= gap0:
                result = "down", _say(language, "12일선이 26일선 아래이고 간격이 벌어지고 있어요", "The 12-day line is below the 26-day line and the gap is widening")
            else:
                result = "neutral", _say(language, "두 선의 간격이 좁아지고 있어요", "The gap between the lines is narrowing")
    elif key == "macd":
        macd, hist = _at(values, "MACD", i), _at(values, "HISTOGRAM", i)
        if None not in (macd, hist):
            if hist > 0 and macd > 0:
                result = "up", _say(language, "MACD선이 시그널선 위이고 0선 위예요", "MACD is above its signal line and above zero")
            elif hist < 0 and macd < 0:
                result = "down", _say(language, "MACD선이 시그널선 아래이고 0선 아래예요", "MACD is below its signal line and below zero")
            else:
                result = "neutral", _say(language, "시그널선과의 위치와 0선 위치가 엇갈려요", "The signal-line and zero-line positions disagree")
    elif key == "ichimoku":
        a, b = _at(values, "SPAN_A", i), _at(values, "SPAN_B", i)
        if close is not None and None not in (a, b):
            if close > max(a, b):
                result = "up", _say(language, "가격이 구름 위에 있어요", "Price is above the cloud")
            elif close < min(a, b):
                result = "down", _say(language, "가격이 구름 아래에 있어요", "Price is below the cloud")
            else:
                result = "neutral", _say(language, "가격이 구름 안에 있어 방향이 정해지지 않았어요", "Price is inside the cloud: no direction yet")
    elif key == "psar":
        sar = _at(values, "SAR", i)
        if close is not None and sar is not None:
            result = ("up", _say(language, "점이 가격 아래에 있어요", "The dots are below price")) if sar < close else \
                ("down", _say(language, "점이 가격 위에 있어요", "The dots are above price"))
    elif key == "adx":
        adx, pdi, mdi = _at(values, "ADX", i), _at(values, "PDI", i), _at(values, "MDI", i)
        if None not in (adx, pdi, mdi):
            if adx < 20:
                result = "neutral", _say(language, f"ADX {adx:.0f} · 추세가 약한 구간이에요", f"ADX {adx:.0f}: a weak trend")
            elif pdi > mdi:
                result = "up", _say(language, f"ADX {adx:.0f} · +DI가 −DI 위에 있어요", f"ADX {adx:.0f} with +DI above −DI")
            else:
                result = "down", _say(language, f"ADX {adx:.0f} · −DI가 +DI 위에 있어요", f"ADX {adx:.0f} with −DI above +DI")
    elif key == "bb":
        result = _now_band(values, bars, i, "BB_UPPER", "BB_LOWER", None, language, "밴드", "band")
    elif key == "envelope":
        result = _now_band(values, bars, i, "ENV_UPPER", "ENV_LOWER", "ENV_MIDDLE", language, "띠", "envelope")
    elif key == "keltner":
        result = _now_band(values, bars, i, "KC_UPPER", "KC_LOWER", "KC_MIDDLE", language, "통로", "channel")
    elif key == "donchian":
        hi_prev, lo_prev = _at(values, "DC_UPPER", i - 1), _at(values, "DC_LOWER", i - 1)
        if close is not None and None not in (hi_prev, lo_prev):
            if close > hi_prev:
                result = "up", _say(language, "종가가 직전 최고가를 넘었어요", "The close cleared the prior high")
            elif close < lo_prev:
                result = "down", _say(language, "종가가 직전 최저가를 깼어요", "The close broke the prior low")
            else:
                result = "neutral", _say(language, "종가가 통로 안에 있어요", "The close is inside the channel")
    elif key == "percent_b":
        # Bollinger: a return inside counts only while the middle line is not trending against it.
        slope = _close_slope(bars, i)
        result = _now_level(values, i, "PERCENT_B", 0.0, 1.0, language, digits=2,
                            up_ok=slope is None or slope > -FLAT, down_ok=slope is None or slope < FLAT)
        v = _at(values, "PERCENT_B", i)
        if result is not None and result[0] == "neutral" and v is not None and 0 < v < 1:
            if slope is not None and slope <= -FLAT and v < 0.5:
                result = "down", _say(language, f"%b {_num(v, 2)} · 0.5 아래이고 중심선이 내려가고 있어요",
                                      f"%b {_num(v, 2)}: below 0.5 with a falling middle line")
            else:
                result = "neutral", _say(language, f"%b {_num(v, 2)} · 밴드 안이에요", f"%b {_num(v, 2)}: inside the bands")
    elif key == "bandwidth":
        v = _at(values, "BANDWIDTH", i)
        past = [x for x in (_at(values, "BANDWIDTH", j) for j in range(max(0, i - 126), i + 1)) if x is not None]
        if v is not None and past:
            low = sorted(past)[max(0, len(past) // 5 - 1)]
            squeeze = v <= low
            result = "neutral", (_say(language, "폭이 최근 6개월 가운데 좁은 편이에요. 방향은 돌파로 확인해요",
                                      "Width is near its six-month low; direction comes from the break") if squeeze else
                                 _say(language, "폭은 방향을 알려주지 않아요. 가격과 함께 봐요",
                                      "Width does not give direction; read it with price"))
    elif key == "atr":
        result = "neutral", _say(language, "ATR은 움직임의 크기예요. 방향은 가격으로 봐요", "ATR is the size of moves; read direction from price")
    elif key == "rsi":
        result = _now_level(values, i, "RSI14", 30, 70, language)
    elif key == "stoch":
        result = _now_level(values, i, "STOCH_K", 20, 80, language)
    elif key == "stochrsi":
        result = _now_level(values, i, "STOCHRSI_K", 20, 80, language)
    elif key == "cci":
        v = _at(values, "CCI", i)
        if v is not None:
            if _crossed_up(values, "CCI", -100, i):
                result = "up", _say(language, f"−100 아래에서 다시 올라왔어요 (지금 {_num(v, 0)})", f"It rose back above −100 (now {_num(v, 0)})")
            elif _crossed_down(values, "CCI", 100, i):
                result = "down", _say(language, f"+100 위에서 다시 내려왔어요 (지금 {_num(v, 0)})", f"It fell back below +100 (now {_num(v, 0)})")
            elif v > 100:
                result = "up", _say(language, f"+100 위예요 (지금 {_num(v, 0)}). 추세장에선 상승 흐름으로 읽어요", f"Above +100 (now {_num(v, 0)}): upward in a trend")
            elif v < -100:
                result = "down", _say(language, f"−100 아래예요 (지금 {_num(v, 0)}). 추세장에선 하락 흐름으로 읽어요", f"Below −100 (now {_num(v, 0)}): downward in a trend")
            else:
                result = "neutral", _say(language, f"±100 사이예요 (지금 {_num(v, 0)})", f"Between ±100 (now {_num(v, 0)})")
    elif key == "williams":
        result = _now_level(values, i, "WILLR", -80, -20, language)
    elif key == "roc":
        v, v0 = _at(values, "ROC", i), _at(values, "ROC", i - 3)
        if v is not None and v0 is not None:
            if v > 0 and v >= v0:
                result = "up", _say(language, f"ROC {v:+.1f}% · 0 위에서 높아지고 있어요", f"ROC {v:+.1f}%: above zero and rising")
            elif v < 0 and v <= v0:
                result = "down", _say(language, f"ROC {_num(v)}% · 0 아래에서 낮아지고 있어요", f"ROC {_num(v)}%: below zero and falling")
            else:
                result = "neutral", _say(language, f"ROC {('+' if v > 0 else '') + _num(v)}% · 속도가 바뀌고 있어요", f"ROC {('+' if v > 0 else '') + _num(v)}%: the pace is changing")
    elif key == "disparity":
        v = _at(values, "DISPARITY", i)
        if v is not None:
            if _crossed_up(values, "DISPARITY", 95, i):
                result = "up", _say(language, f"95 아래에서 다시 올라왔어요 (지금 {v:.1f})", f"It rose back above 95 (now {v:.1f})")
            elif _crossed_down(values, "DISPARITY", 105, i):
                result = "down", _say(language, f"105 위에서 다시 내려왔어요 (지금 {v:.1f})", f"It fell back below 105 (now {v:.1f})")
            elif v >= 100:
                result = "up", _say(language, f"{v:.1f} · 평균선 위에 있어요", f"{v:.1f}: above the average")
            else:
                result = "down", _say(language, f"{v:.1f} · 평균선 아래에 있어요", f"{v:.1f}: below the average")
    elif key == "psychology":
        result = _now_level(values, i, "PSY", 25, 75, language, "%")
    elif key == "volume_ma":
        average = _at(values, "VOLUME_MA", i)
        volume = _series_at(bars.volume, i)
        previous = _series_at(bars.close, i - 1) if i > 0 else None
        if None not in (average, volume, close, previous) and average > 0:
            ratio = volume / average
            if ratio >= 1.3 and close > previous:
                result = "up", _say(language, f"오르는 날 거래량이 평균의 {ratio:.1f}배예요", f"Up day on {ratio:.1f}x average volume")
            elif ratio >= 1.3 and close < previous:
                result = "down", _say(language, f"내리는 날 거래량이 평균의 {ratio:.1f}배예요", f"Down day on {ratio:.1f}x average volume")
            else:
                result = "neutral", _say(language, f"거래량이 평균의 {ratio:.1f}배예요", f"Volume is {ratio:.1f}x its average")
    elif key == "obv":
        o, o0 = _at(values, "OBV", i), _at(values, "OBV", i - 10)
        c0 = _series_at(bars.close, i - 10) if i >= 10 else None
        if None not in (o, o0, close, c0):
            if o > o0 and close > c0:
                result = "up", _say(language, "최근 10일 가격과 OBV가 함께 올랐어요", "Price and OBV both rose over 10 days")
            elif o < o0 and close < c0:
                result = "down", _say(language, "최근 10일 가격과 OBV가 함께 내렸어요", "Price and OBV both fell over 10 days")
            else:
                result = "neutral", _say(language, "최근 10일 가격과 OBV의 방향이 엇갈려요", "Price and OBV disagree over 10 days")
    elif key == "mfi":
        result = _now_level(values, i, "MFI", 20, 80, language)
    elif key == "vwap":
        vw, slope = _at(values, "VWAP", i), _slope(values, "VWAP", i, 3)
        if close is not None and vw is not None and slope is not None:
            if close > vw and slope >= 0:
                result = "up", _say(language, "가격이 VWAP 위이고 VWAP이 오르고 있어요", "Price is above a rising VWAP")
            elif close < vw and slope <= 0:
                result = "down", _say(language, "가격이 VWAP 아래이고 VWAP이 내려가고 있어요", "Price is below a falling VWAP")
            else:
                result = "neutral", _say(language, "가격 위치와 VWAP 방향이 엇갈려요", "Price position and VWAP direction disagree")
    elif key == "investor_flow":
        foreign = [_at(values, "FOREIGN", j) for j in range(max(0, i - 4), i + 1)]
        inst = [_at(values, "INSTITUTION", j) for j in range(max(0, i - 4), i + 1)]
        if all(v is not None for v in foreign + inst) and foreign:
            f, s = sum(foreign), sum(inst)
            if f > 0 and s > 0:
                result = "up", _say(language, "최근 5일 외국인과 기관이 함께 순매수했어요", "Foreigners and institutions both net bought over 5 days")
            elif f < 0 and s < 0:
                result = "down", _say(language, "최근 5일 외국인과 기관이 함께 순매도했어요", "Foreigners and institutions both net sold over 5 days")
            else:
                result = "neutral", _say(language, "최근 5일 외국인과 기관의 방향이 엇갈려요", "Foreigners and institutions disagree over 5 days")
    elif key == "short_ratio":
        v = _at(values, "SHORT_RATIO", i)
        past = [x for x in (_at(values, "SHORT_RATIO", j) for j in range(max(0, i - 20), i)) if x is not None]
        if v is not None and past:
            usual = sum(past) / len(past)
            if usual > 0 and v >= usual * 1.5:
                result = "down", _say(language, f"공매도 비중 {v:.1f}% · 평소({usual:.1f}%)보다 크게 높아요", f"Short share {v:.1f}%, well above its usual {usual:.1f}%")
            else:
                result = "neutral", _say(language, f"공매도 비중 {v:.1f}% · 평소({usual:.1f}%) 수준이에요", f"Short share {v:.1f}%, near its usual {usual:.1f}%")
    if result is None:
        return None
    side, reason = result
    return Now(side, SIDES[side][0 if _ko(language) else 1], reason)


def text_block(key, language="ko", current=None):
    """The conclusion as plain text (reports, the indicator guide page): the two sides, now, regime and evidence."""
    o = outlook(key, language)
    ko = _ko(language)
    lines = [("상승 흐름 쪽으로 읽는 경우" if ko else "Read as an upward flow when")]
    lines += ["· " + item for item in o.up]
    lines += [("하락 흐름 쪽으로 읽는 경우" if ko else "Read as a downward flow when")]
    lines += ["· " + item for item in o.down]
    if current is not None:
        lines.append(("지금은 " if ko else "Now: ") + current.label + " · " + current.reason)
    lines.append(o.regime)
    lines.append(f"{o.grade_text} · {o.grade_reason}")
    if o.sources:
        lines.append(("근거 자료: " if ko else "Sources: ") + ", ".join(o.sources))
    return "\n".join(lines)


__all__ = ["OUTLOOK", "GRADES", "SIDES", "Outlook", "Now", "outlook", "now", "text_block"]
