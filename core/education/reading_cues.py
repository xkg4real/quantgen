"""Specific chart cross-checks, not entries, exits or forecasts. Shared display copy."""
CHECKS = {
    'sma': ('가격이 선 위인지와 평균선 기울기를 함께 보세요. 위에 있어도 선이 내려가면 흐름이 엇갈려요.',
            'Compare price position with the average’s slope. Price above a falling average gives mixed context.'),
    'ema': ('두 선의 교차 뒤 간격이 벌어지는지 보세요. 곧 다시 붙으면 방향이 불안정해요.',
            'After a crossing, watch whether the two lines separate. A quick reunion suggests an unstable direction.'),
    'macd': ('막대의 부호와 길이 변화를 나눠 보세요. 양수여도 짧아지면 두 선의 상승 격차가 줄고 있어요.',
             'Separate histogram sign from size. Positive bars getting shorter mean the bullish line gap is shrinking.'),
    'ichimoku': ('가격의 구름 위치와 전환선·기준선의 순서가 같은 방향인지 보세요.',
                 'Check whether price position relative to the cloud agrees with the conversion/base line order.'),
    'psar': ('점이 반대편으로 바뀐 뒤 가격이 그 방향을 이어가는지 보세요.',
             'After the dots flip sides, check whether price continues in that direction.'),
    'adx': ('방향은 +DI·−DI, 추세 강도는 ADX로 나눠 읽으세요. ADX 상승만으로 상승장을 뜻하지 않아요.',
            'Read direction from +DI versus −DI and strength from ADX. Rising ADX alone does not mean rising prices.'),
    'envelope': ('가격의 띠 이탈과 중심 평균선의 기울기를 함께 보세요. 고정 폭이라 종목별 변동성 차이는 반영하지 않아요.',
                 'Compare a band break with the centre average’s slope. Fixed-width bands do not adapt to volatility.'),
    'keltner': ('가격의 위치뿐 아니라 띠가 넓어지는지 보세요. 넓어지면 최근 가격 변동 폭도 커진 상태예요.',
                'Check band width as well as price position. Wider bands reflect a larger recent price range.'),
    'donchian': ('위·아래 선이 새 고저가 때문에 움직였는지, 옛 봉이 계산 기간에서 빠져 움직였는지 구분하세요.',
                 'A boundary can move because of a new extreme or because an old bar left the lookback window.'),
    'rsi': ('30·70 통과와 가격의 고저점을 함께 보세요. 수치 회복과 가격 저점 상승이 동반되는지 확인하세요.',
            'Compare crossings of 30/70 with price highs and lows. Check whether RSI recovery accompanies rising price lows.'),
    'stoch': ('%K·%D 교차 위치를 보세요. 80 위나 20 아래의 교차도 추세가 강하면 되돌려질 수 있어요.',
              'Locate the %K/%D crossing within the range. Even crossings above 80 or below 20 can reverse in a strong trend.'),
    'stochrsi': ('가격 위치가 아니라 RSI의 상대 위치예요. 원래 RSI와 가격도 같은 변화를 보이는지 확인하세요.',
                 'This locates RSI, not price, within its range. Cross-check the underlying RSI and price movement.'),
    'cci': ('±100 돌파 뒤 0선 쪽으로 돌아오는지 보세요. 절댓값이 크다는 이유만으로 반전을 뜻하지 않아요.',
            'After a ±100 break, watch for a return toward zero. A large absolute reading alone does not imply reversal.'),
    'williams': ('0에 가까우면 최근 고가 쪽, −100에 가까우면 저가 쪽이에요. 가격 고저점의 변화도 확인하세요.',
                 'Near zero means near the recent high; near −100 means near the low. Cross-check changing price extremes.'),
    'roc': ('0선 통과와 변화율의 증감을 구분하세요. 양수여도 낮아지면 과거 대비 상승 폭이 줄고 있어요.',
            'Separate zero crossings from changes in rate. A declining positive value means the lookback gain is shrinking.'),
    'disparity': ('100에서 얼마나 떨어졌는지와 평균선 방향을 같이 보세요. 105는 평균보다 5% 위라는 뜻이에요.',
                  'Compare distance from 100 with the average’s direction. A value of 105 means 5% above the average.'),
    'psychology': ('오른 봉의 비율이지 상승 폭이 아니에요. 작은 상승 여러 번과 큰 하락 한 번이 함께 있을 수 있어요.',
                   'It counts up bars, not the size of gains. Many small rises can coexist with one large fall.'),
    'bb': ('밴드 접촉과 안쪽 복귀를 구분하세요. 중심선 방향과 밴드 폭까지 봐야 변동성 확대를 함께 읽을 수 있어요.',
           'Distinguish a band touch from re-entry. Check the middle line and band width for volatility context.'),
    'atr': ('ATR을 현재 가격과 비교하세요. 같은 ATR이라도 가격이 다른 종목의 상대 변동성은 달라요.',
            'Compare ATR with current price. The same ATR implies different relative volatility at different price levels.'),
    'percent_b': ('0은 하단, 1은 상단이에요. 밴드 자체가 움직여도 값이 바뀌므로 실제 가격과 띠를 함께 보세요.',
                  'Zero is the lower band and one the upper. Moving bands also change the value, so inspect price and bands together.'),
    'bandwidth': ('축소 뒤 확대되는지를 보세요. 폭은 움직임의 크기만 보여주므로 방향은 가격으로 확인하세요.',
                  'Watch for expansion after contraction. Width describes size, so read direction from price.'),
    'volume_ma': ('현재 거래량을 평균과 비교하세요. 진행 중인 봉의 거래량은 아직 완성되지 않았어요.',
                  'Compare volume with its average. Volume in the current unfinished bar is incomplete.'),
    'obv': ('가격과 OBV가 같은 방향의 고저점을 만드는지 보세요. 절대 수치는 시작 시점에 따라 달라요.',
            'Compare the direction of price and OBV highs/lows. Absolute OBV depends on the starting point.'),
    'mfi': ('20·80 부근에서 가격과 거래량 변화도 확인하세요. 현금 유입액이나 투자자별 매매액은 아니에요.',
            'Near 20/80, cross-check price and volume. This is not measured cash flow or investor-level buying.'),
    'vwap': ('가격과 VWAP의 차이를 보되 누적 시작·초기화 기준을 확인하세요. 기준이 다르면 값도 달라져요.',
             'Check price distance from VWAP and its accumulation/reset basis. Different bases produce different values.'),
    'investor_flow': ('순매수 부호와 집계 기간을 같이 보세요. 투자자별 자료가 없으면 가격·거래량으로 대신 추정하지 않아요.',
                      'Read net-flow sign with the reporting period. Price and volume cannot replace missing investor data.'),
    'short_ratio': ('비중 변화와 전체 거래량을 같이 보세요. 전체 거래량이 줄어도 공매도 비중은 커질 수 있어요.',
                    'Compare short-sale share with total volume. The share can rise when total volume falls.'),
}


def check_note(key, language='ko'):
    return CHECKS[key][0 if str(language).startswith('ko') else 1]


def reading_tip(key, language='ko'):
    from .study_guide import short_guide
    caution = short_guide(key, language).caution
    if key == 'rsi':
        caution = ('과매수·과매도 상태는 강한 추세에서 오래 이어질 수 있어요.'
                   if str(language).startswith('ko') else 'Overbought or oversold conditions can persist in strong trends.')
    return check_note(key, language) + '\n' + caution
