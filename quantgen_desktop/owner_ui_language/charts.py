"""Korean display text for the owner UI port, area: charts. See the package docstring.

Owner issue 02 (2026-11-10): "people can't read it, and the charts look broken". Besides `PAIRS` (window
chrome, merged into the catalogue), this module holds two chart-only tables that only the native chart
widgets read (quantgen_desktop/charts.py, quantgen_desktop/chart_study.py):

* `CHART_TERMS`: Korean axis captions and series names. They depend on the chart, so they stay out of the
  window catalogue: an equity *curve* reads 누적 성과 here, while the same English word "Equity" is the
  asset class 주식 elsewhere.
* `READINGS`: the four-item "how to read this chart" guide the Flet app shows beside the same chart
  (ui/fcharts.py, ui/xcharts.py, PR #98), keyed by the chart name a pane passes to `ToolPane.line` /
  `ToolPane.bars`, as {'meaning'|'look'|'interpret'|'limit': (Korean, English)}. The Flet wording is kept;
  where a sentence described something only the Flet figure draws (dots, shading, dashed fits, colours),
  it is reworded for the native chart, which names its lines in the legend. Display only: a guide never
  carries a number of a result.
"""

PAIRS = {
    "How to read this chart": "이 차트 읽는 법",
}

# Exact English source text -> Korean, for chart axes and legends only.
CHART_TERMS = {
    # Rates
    "Yield · %": "금리 · %",
    "Zero": "무이표 금리",
    "Par": "파 금리",
    "Par yield · %": "파 금리 · %",
    "Loading": "요인 적재값",
    "level": "수준",
    "slope": "기울기",
    "curvature": "곡률",
    "End · years": "종료 시점 · 년",
    "Years": "경과 기간 · 년",
    "Short rate · %": "단기금리 · %",
    "PV": "보유기간 끝 가치 (PV)",
    "Paths per bin": "구간별 경로 수",
    "Count": "경로 수",
    # Strategy Lab, signals, ETF, FX carry
    "OOS observations": "표본 외(OOS) 거래일",
    "Equity": "누적 성과 (1에서 시작)",
    "Benchmark": "비교 기준",
    "Trend": "추세 전환",
    # Structuring
    "Payoff": "만기 지급액",
    "Per 100 notional": "액면 100당",
    "Underlying at maturity": "만기 시 기초자산 수준",
    "Realized 10y–2y spread · bp": "실현된 10년–2년 금리차 · bp",
    # Derivatives
    "Black-76 IV %": "Black-76 내재변동성 %",
    "SVI IV %": "SVI 내재변동성 %",
    "Index points": "만기 시 지수 수준",
    "Density": "확률밀도",
    "Q density": "위험중립 확률밀도 (f_Q)",
    # ETF and crypto
    "Price / NAV": "가격 / 순자산가치",
    "Premium %": "프리미엄 %",
    "Premium · %": "프리미엄 · %",
    "7-day mean annualized %": "7일 평균 연율 %",
    "Annualized · %": "연율 · %",
    "USDT per BTC": "BTC당 USDT",
    "SMA50": "50일 이동평균 (SMA50)",
    "SMA200": "200일 이동평균 (SMA200)",
}

READING_KEYS = ("meaning", "look", "interpret", "limit")

_EQUITY_LIMIT = ("과거 데이터로 다시 계산한 결과이며 미래 성과를 보장하지 않습니다. 좋은 전략인지는 이 선 하나가 아니라 "
                 "검증 판정(PASS / REVISE / REJECT)과 함께 판단하세요.",
                 "Recomputed on past data; it guarantees no future result. Judge the strategy with its validation "
                 "verdict (PASS / REVISE / REJECT), not this line alone.")


def _equity(meaning_ko, meaning_en, first_ko, first_en, second_ko, second_en, limit=_EQUITY_LIMIT):
    return {
        "meaning": (meaning_ko, meaning_en),
        "look": (f"오른쪽 끝에서 '{first_ko}'과 '{second_ko}' 선의 높이를 비교하고, 중간에 크게 떨어진 구간(낙폭)이 "
                 "어디였는지 보세요. 세로축 1.0이 출발점입니다.",
                 f"Compare the '{first_en}' and '{second_en}' lines at the right end, and find the deep dips along "
                 "the way (drawdowns). 1.0 on the vertical axis is the starting point."),
        "interpret": (f"'{first_ko}' 선이 '{second_ko}' 선보다 위에서 끝나면 같은 기간 비교 대상보다 성과가 좋았습니다. "
                      "1.2는 20% 이익, 0.9는 10% 손실입니다. 선이 덜 출렁일수록 위험이 작았습니다.",
                      f"Ending above the '{second_en}' line means the '{first_en}' line did better over the period. "
                      "1.2 is a 20% gain, 0.9 a 10% loss. A smoother line means less risk taken."),
        "limit": limit,
    }


READINGS = {
    "1y z-scores · descriptive only": {
        "meaning": ("주요 거시 지표 18개가 지금 지난 1년 평균보다 얼마나 높거나 낮은지를 z-점수로 보여 줍니다. "
                    "0은 1년 평균과 같다는 뜻이고, +1은 평소 흔들림(표준편차) 1개만큼 높다는 뜻입니다.",
                    "How far each of the 18 macro indicators sits above or below its own 1-year average, as a "
                    "z-score. 0 means at the 1-year average; +1 means one typical swing (standard deviation) above it."),
        "look": ("막대가 0의 오른쪽이면 1년 평균보다 높고, 왼쪽이면 낮습니다. 옅은 띠(±1) 안은 평소 범위, "
                 "점선(±2) 밖은 1년 중 드문 수준입니다. 막대 끝 숫자가 정확한 z-점수입니다.",
                 "Bars right of 0 are above the 1-year average, bars left of it below. Inside the shaded band (±1) "
                 "is the usual range; beyond the dashed lines (±2) is rare for the past year. The number at each "
                 "bar end is the exact z-score."),
        "interpret": ("막대 색은 지표 묶음(금리·신용·외환·위험선호)이며 묶음 사이에 구분선이 있습니다. 빗금 막대는 실제 관측이 "
                      "아닌 합성 데이터입니다. 신용 스프레드와 VIX가 함께 오른쪽이면 시장이 위험을 피하는 분위기입니다. "
                      "차트 위 '설명용 관측' 표는 같은 지표의 최근 변화를 정해진 규칙으로 정리한 것입니다.",
                      "Bar colour is the indicator group (rates, credit, FX, risk appetite), with a rule between "
                      "groups. Hatched bars are synthetic data, not observations. Credit spreads and VIX both to the "
                      "right mean markets are avoiding risk. The 'Descriptive read' table above the chart sums up "
                      "recent changes of the same indicators with fixed rules."),
        "limit": ("지금 상태를 설명할 뿐이며 국면 모형이나 예측이 아닙니다. z-점수는 지난 1년만 비교하므로 "
                  "1년 내내 이례적이었다면 0이 '정상'을 뜻하지 않습니다. 매매 신호나 투자 권유로 쓰지 마세요.",
                  "A descriptive read of the present, not a regime model or a forecast (P19). The z-score compares "
                  "with the past year only, so 0 is not 'normal' if the whole year was unusual. Not a trading "
                  "signal or a recommendation."),
    },
    "Walk-forward equity": _equity(
        "처음에 1을 넣었다면 전략과 비교 기준이 각각 얼마가 되었는지를 거래일 순서대로 보여 줍니다. 전략을 정하는 데 "
        "쓰지 않은 기간(표본 외, OOS)의 성과입니다.",
        "What 1 invested at the start became, session by session, for the strategy and the benchmark. This is the "
        "out-of-sample period, not used to choose the strategy.",
        "전략", "Strategy", "비교 기준", "Benchmark"),
    "Costed backtest": _equity(
        "처음에 1을 넣었다면 규칙대로 사고판 전략과 계속 보유(매수 후 보유)가 각각 얼마가 되었는지를 거래일 순서대로 "
        "보여 줍니다. 전략에는 화면의 편도 거래 비용을 뺐습니다.",
        "What 1 invested at the start became, session by session, for the rule-based strategy and for buy and "
        "hold. The strategy pays the per-side cost shown on the page.",
        "전략", "Strategy", "매수 후 보유", "Buy & hold",
        limit=("과거 데이터로 다시 계산한 결과이며 미래 성과를 보장하지 않습니다. 이 화면은 기술적 관측일 뿐 "
               "검증된 전략 판정이 아닙니다.",
               "Recomputed on past data; it guarantees no future result. This page is a technical observation, "
               "not a validated strategy verdict.")),
    "Trend switch vs buy & hold": _equity(
        "처음에 1을 넣었다면 추세 전환 규칙과 계속 보유(매수 후 보유)가 각각 얼마가 되었는지를 거래일 순서대로 "
        "보여 줍니다.",
        "What 1 invested at the start became, session by session, for the trend-switch rule and for buy and hold.",
        "추세 전환", "Trend", "매수 후 보유", "Buy & hold",
        limit=("같은 데이터로 계산한 설명용 결과이며 새로운 검증 판정이 아닙니다. 미래 성과를 보장하지 않습니다.",
               "A descriptive in-sample result, not a new study decision; it guarantees no future result.")),
    "Carry equity": {
        "meaning": ("금리가 높은 통화를 사고 낮은 통화를 파는 캐리 전략을 과거 데이터로 다시 계산한 누적 성과(1에서 "
                    "시작)입니다. '동일 비중 매수'는 모든 통화를 같은 비중으로 산 비교 기준입니다.",
                    "The carry strategy (long high-yield, short low-yield currencies) recomputed on past data, as "
                    "growth of 1. 'Equal-weight long' buys every currency in equal weights, for comparison."),
        "look": ("'바스켓'과 '동일 비중 매수' 선의 끝 높이와 중간 낙폭을 비교하세요.",
                 "Compare where the 'Basket' and 'Equal-weight long' lines end, and the dips on the way."),
        "interpret": ("'바스켓' 선이 위에 있으면 같은 기간 단순 분산 매수보다 성과가 좋았습니다. 캐리 전략은 평소 꾸준하다가 "
                      "위험 회피 국면에 한꺼번에 크게 잃는 경향이 있습니다.",
                      "Basket above equal-weight means carry beat the simple basket over the period. Carry tends to "
                      "earn steadily and then lose sharply when markets turn risk-off."),
        "limit": ("과거 데이터의 백테스트이며 미래 성과를 보장하지 않습니다. 표시한 비용 외의 실제 비용·체결 차이는 "
                  "반영되지 않았습니다.",
                  "A backtest on past data, no guarantee of future results. Real costs beyond the stated cost and "
                  "execution are not included."),
    },
    "수익률 곡선": {
        "meaning": ("오늘의 국채 금리로 만든 수익률 곡선입니다. 파 금리(액면가에 거래되는 채권의 수익률)와 무이표 금리(만기에 "
                    "한 번 받는 돈의 할인율)를 만기별로 그렸습니다.",
                    "The yield curve built from today's Treasury yields: par yields (the yield of a bond priced at "
                    "par) and zero rates (the discount rate of one payment at maturity), by maturity."),
        "look": ("가로축은 만기(년)입니다. 왼쪽 단기에서 오른쪽 장기로 곡선이 오르는지 내리는지, 두 선의 간격이 어디서 "
                 "벌어지는지 보세요.",
                 "Across is maturity in years. See whether the curve rises or falls from the short end (left) to the "
                 "long end (right), and where the two lines move apart."),
        "interpret": ("장기 금리가 단기보다 높으면 정상(우상향), 낮으면 역전된 곡선입니다. 곡선 형태와 최근 변화는 아래 "
                      "지표 표에 있습니다.",
                      "Long yields above short ones is a normal (upward) curve; below is inverted. The curve shape "
                      "and the recent move are in the metrics table below."),
        "limit": ("오늘 곡선의 계산 결과이며 미래 금리 전망이 아닙니다. 구축 방법에 따라 고시 금리 사이의 모양이 "
                  "달라집니다. 출처가 '합성'이면 실제 금리가 아닙니다.",
                  "Arithmetic on today's curve, not a forecast. The construction method changes the shape between "
                  "quotes. A SYNTHETIC source means these are not market yields."),
    },
    "관측 금리 이력": {
        "meaning": ("만기별(예: 3개월·2년·10년·30년) 국채 금리가 날짜에 따라 어떻게 움직였는지 보여 줍니다.",
                    "How the par yields of each maturity (e.g. 3 months, 2, 10 and 30 years) moved over time."),
        "look": ("선들의 높이 차이(장단기 금리차)와 최근 방향을 보세요. 오른쪽 끝이 가장 최근이며, 관측 기간은 "
                 "가로축 설명에 있습니다.",
                 "Look at the gaps between the lines (the curve slope) and their recent direction; the right end is "
                 "the latest, and the observed dates are in the axis caption."),
        "interpret": ("선들이 함께 오르내리면 금리 수준이 바뀐 것이고, 간격이 바뀌면 곡선 기울기가 바뀐 것입니다. "
                      "단기 금리 선이 장기 금리 선보다 위에 있으면 곡선이 역전된 상태입니다.",
                      "Lines moving together mean the level changed; a changing gap means the slope changed. A "
                      "short-maturity line above a long one means the curve is inverted."),
        "limit": ("관측된 금리를 그린 것이며 앞으로의 금리를 예측하지 않습니다. 출처가 '합성'이면 실제 금리가 아닙니다.",
                  "Observed yields only, not a forecast. A SYNTHETIC source means these are not market yields."),
    },
    "PCA loadings": {
        "meaning": ("매일의 금리 곡선 변화를 서로 겹치지 않는 몇 가지 움직임(주성분)으로 나눈 결과입니다. 선 하나가 "
                    "한 요인이 만기별 금리를 얼마나 움직이는지(적재값)를 보여 줍니다.",
                    "The daily changes of the yield curve split into a few independent movements (principal "
                    "components). Each line shows how much one factor moves the yield at each maturity (its "
                    "loadings)."),
        "look": ("각 선의 모양을 세로축 0을 기준으로 보세요. 각 요인이 설명하는 변동의 몫은 아래 분산 표에 "
                 "있습니다.",
                 "Read the shape of each line against zero on the vertical axis. The share of the variation each "
                 "factor explains is in the variance table below."),
        "interpret": ("모든 만기에서 같은 부호로 비슷하면 곡선 전체가 함께 오르내리는 '수준' 요인, 단기와 장기의 "
                      "부호가 반대면 '기울기' 요인, 중간 만기만 반대면 '곡률' 요인입니다. 첫 요인의 비율이 클수록 "
                      "곡선이 대부분 평행하게 움직였다는 뜻입니다.",
                      "Same sign and similar size at every maturity is the 'level' factor (the whole curve moves "
                      "together); opposite signs at the short and long ends is 'slope'; only the middle moving the "
                      "other way is 'curvature'. A large first share means the curve mostly moved in parallel."),
        "limit": ("관측 기간의 변화로 계산한 통계적 분해이며, 기간이 바뀌면 요인 모양과 비율도 바뀝니다. 앞으로의 "
                  "금리 움직임을 예측하지 않습니다.",
                  "A statistical split of the changes in the observed window; another window gives other shapes and "
                  "shares. It does not forecast rate moves."),
    },
    "Caplet premium": {
        "meaning": ("캡(또는 플로어)을 이자기간마다의 옵션(캡렛·플로어렛)으로 나눠, 각 기간이 끝나는 시점별 프리미엄을 "
                    "보여 줍니다.",
                    "The cap (or floor) split into one option per interest period (caplets or floorlets): the "
                    "premium of each period, by the time it ends."),
        "look": ("선이 기간에 따라 어떻게 오르내리는지 보세요. 기간별 선도금리는 위 표에 있습니다.",
                 "See how the line changes across periods. Each period's forward rate is in the table "
                 "above."),
        "interpret": ("캡렛은 선도금리가 행사금리보다 높을수록, 시작 시점이 멀수록(불확실성이 클수록) 비쌉니다. "
                      "플로어렛은 선도금리가 행사금리보다 낮을수록 비쌉니다. 모두 더하면 전체 프리미엄입니다.",
                      "A caplet costs more the further the forward is above the strike and the later it starts "
                      "(more uncertainty); a floorlet costs more the further the forward is below the strike. They "
                      "add up to the total premium."),
        "limit": ("입력한 변동성 하나와 단일 곡선으로 계산한 모형 가격이며, 시장 호가도 금리 예측도 아닙니다.",
                  "A model price from one input volatility and a single curve; it is not a market quote and not a "
                  "rate forecast."),
    },
    "금리 분포 · 중앙 90%": {
        "meaning": ("과거 단기금리로 추정한 모형이 만든 미래 단기금리 경로들의 분포입니다. P50은 중앙값, P5와 P95 사이에 "
                    "경로의 90%, P25와 P75 사이에 50%가 들어갑니다.",
                    "The spread of future short-rate paths from a model fitted to past short rates. P50 is the "
                    "median; 90% of the paths lie between P5 and P95, 50% between P25 and P75."),
        "look": ("시간이 지나면서 P5와 P95 선의 간격이 얼마나 넓어지는지, P50 선이 어느 쪽으로 기우는지 보세요.",
                 "See how fast the gap between the P5 and P95 lines widens over time, and which way the P50 line "
                 "leans."),
        "interpret": ("간격이 넓을수록 모형이 보는 금리의 불확실성이 큽니다. 비교 금리를 넘을 확률은 아래 표에 있으며 "
                      "모형 안에서만 의미가 있습니다.",
                      "A wider gap means more rate uncertainty in the model. The probability of ending above the "
                      "threshold is in the table below, meaningful only inside the model."),
        "limit": ("과거 데이터로 추정한 모형의 시뮬레이션이며 금리 전망이 아닙니다. 모형이나 추정 기간이 바뀌면 범위와 "
                  "비율도 바뀝니다.",
                  "A simulation from a model fitted to past data, not a rate forecast. Another model or fitting "
                  "window gives other bands and shares."),
    },
    "Horizon PV distribution": {
        "meaning": ("금리 시뮬레이션의 경로마다 보유기간 끝에서 상품(채권·스왑)을 다시 평가한 가치가 어느 구간에 몇 개 "
                    "있는지 보여 줍니다.",
                    "The value of the instrument (bond or swap) revalued at the end of the horizon on every "
                    "simulated rate path, counted per value bin."),
        "look": ("선이 가장 높은 곳(가장 흔한 가치)과, 왼쪽(낮은 가치)으로 길게 늘어지는지를 보세요.",
                 "Look at the peak (the most common value) and whether the line trails off to the left (low "
                 "values)."),
        "interpret": ("왼쪽 꼬리가 길수록 나쁜 금리 경로에서 가치가 많이 줄어듭니다. VaR95는 95% 수준의 손실, CVaR95는 "
                      "그보다 나쁜 5% 경로의 평균 손실이며 아래 표에 있습니다.",
                      "The longer the left tail, the more value is lost on bad rate paths. VaR95 is the loss at the "
                      "95% level and CVaR95 the average loss on the worst 5% of paths, in the table below."),
        "limit": ("단기금리 모형의 시뮬레이션에서 나온 분포이며 실제 손실 한도나 확률을 보장하지 않습니다. 모형에 "
                  "없는 위험(신용·유동성)은 빠져 있습니다.",
                  "A distribution from a short-rate model simulation; it guarantees no actual loss limit or "
                  "probability. Risks outside the model (credit, liquidity) are left out."),
    },
    "Spot history": {
        "meaning": ("현물 환율이 날짜에 따라 어떻게 움직였는지 보여 줍니다. 관측 기간은 가로축 설명에 있습니다.",
                    "How the spot rate moved over time; the observed dates are in the axis caption."),
        "look": ("오른쪽 끝(가장 최근)의 수준과 최근의 방향, 크게 움직인 구간을 보세요.",
                 "Look at the right end (the latest level), the recent direction and the large moves."),
        "interpret": ("선이 오르면 기준 통화 1단위를 사는 데 상대 통화가 더 많이 든다는 뜻입니다. 선도환율은 아래 "
                      "선도 곡선에서 금리 차이로 계산한 값입니다.",
                      "A rising line means one unit of the base currency costs more of the quote currency. The "
                      "forward rates are in the forward curve below, computed from the rate gap."),
        "limit": ("관측된 과거 환율이며 앞으로를 예측하지 않습니다. 출처가 '합성'이면 실제 시세가 아닙니다.",
                  "Observed past rates, not a forecast. A SYNTHETIC source means these are not market quotes."),
    },
    "Forward curve": {
        "meaning": ("두 통화의 금리 차이로 계산한 만기별 선도환율입니다.",
                    "The forward rate for each tenor, computed from the two currencies' interest-rate gap."),
        "look": ("가로축은 오늘부터의 기간(년)입니다. 선이 오르는지 내리는지와 그 기울기를 보세요.",
                 "Across is the time from today in years. See whether the line rises or falls, and how steeply."),
        "interpret": ("선도환율이 현물보다 높거나 낮은 것은 금리 차이를 반영한 계산 결과입니다. 환율이 그 방향으로 "
                      "움직인다는 뜻은 아닙니다.",
                      "A forward above or below spot reflects the interest-rate gap; it does not mean the rate will "
                      "move that way."),
        "limit": ("선도환율은 전망이 아니라 금리 차이로 계산한 값이며, 화면은 만기 전체에 같은 금리를 씁니다.",
                  "The forward is arithmetic on the rate gap, not a forecast; the page uses flat rates across "
                  "tenors."),
    },
    "SABR smile": {
        "meaning": ("행사가격마다 통화옵션 시장이 매기는 내재변동성을, 시장 호가(등가격·25델타 리스크 리버설·버터플라이)에 "
                    "맞춘 SABR 모형 곡선으로 보여 줍니다.",
                    "The implied volatility the FX option market sets at each strike, as the SABR model fitted to "
                    "the market quotes (at-the-money, 25-delta risk reversal and butterfly)."),
        "look": ("곡선의 가장 낮은 지점, 양쪽 끝이 올라가는 정도, 왼쪽과 오른쪽의 높이 차이를 보세요. 호가와 적합값의 "
                 "차이는 아래 표에 있습니다.",
                 "Look at the lowest point of the curve, how much the ends lift, and the difference between the "
                 "left and right sides. Quotes against fitted values are in the table below."),
        "interpret": ("양쪽 끝이 높을수록 큰 환율 변동에 대비한 옵션이 비싸게 매겨졌다는 뜻입니다. 한쪽이 더 높으면 "
                      "시장이 그 방향의 급변을 더 비싸게 보험하고 있다는 뜻입니다.",
                      "Higher ends mean options against large FX moves are priced dearer. One side higher than the "
                      "other means the market pays more to insure a sharp move that way."),
        "limit": ("한 시점의 호가에 맞춘 모형 곡선이며 환율 방향이나 미래 변동성을 예측하지 않습니다. 호가 사이와 "
                  "바깥의 행사가격은 모형이 채운 값입니다.",
                  "A model curve fitted to quotes at one moment; it does not forecast the rate or future "
                  "volatility. Strikes between and beyond the quotes are filled in by the model."),
    },
    "Maturity payoff": {
        "meaning": ("만기에 기초자산(또는 금리차)이 어느 수준일 때 액면 100당 얼마를 돌려받는지 보여 줍니다.",
                    "What the note pays at maturity per 100 of face for each level of the underlying (or spread)."),
        "look": ("선이 꺾이는 지점(행사가격·배리어)과, 선이 100보다 위인 구간과 아래인 구간을 보세요.",
                 "Find where the line bends (strikes, barriers) and where it is above or below 100."),
        "interpret": ("선이 100보다 위인 구간에서 만기를 맞으면 원금보다 많이, 아래면 적게 돌려받습니다. 모형 공정가치와 "
                      "발행가는 위 표에 있습니다.",
                      "Ending where the line is above 100 pays back more than the face amount, below it less. The "
                      "model fair value and the issue price are in the tables above."),
        "limit": ("만기 시점의 지급 구조만 보여 주며, 그 수준에 도달할 확률이나 중도 매도 가격은 알려 주지 않습니다. "
                  "발행사 신용 위험은 반영하지 않았습니다. 수익 전망이 아닙니다.",
                  "Only the payoff at maturity: it does not tell how likely each level is or what the note would "
                  "sell for before maturity. Issuer credit risk is not included. Not a return forecast."),
    },
    "Implied volatility smile": {
        "meaning": ("행사가격별 옵션 내재변동성입니다. 'Black-76 내재변동성'은 앱이 중간호가에서 거꾸로 계산한 값, "
                    "'SVI 내재변동성'은 그 값에 맞춘 SVI 곡선입니다.",
                    "Implied volatility by strike. 'Black-76 IV' is the app's inversion of the mid quotes; 'SVI IV' "
                    "is the SVI curve fitted to them."),
        "look": ("두 선이 서로 가까운지, 왼쪽(낮은 행사가격)과 오른쪽의 높이 차이를 보세요.",
                 "Whether the two lines sit close together, and the height difference between the left (low "
                 "strikes) and the right."),
        "interpret": ("왼쪽이 높게 올라가면 하락에 대비하는 풋옵션이 비싸게 거래된다는 뜻으로 주가지수 옵션에서 흔한 "
                      "모양입니다. 두 선이 크게 다르면 호가가 얇거나 오래된 행사가격일 수 있습니다.",
                      "A left side rising high means puts that insure against a fall trade dear, the usual shape "
                      "for index options. A large gap between the lines can mean thin or stale quotes at that "
                      "strike."),
        "limit": ("한 시점의 호가로 계산한 값이며 지수 방향이나 미래 변동성을 예측하지 않습니다. 합성 보드이면 시장 호가가 "
                  "아닙니다.",
                  "Computed from quotes at one moment; it does not forecast the index or future volatility. A "
                  "synthetic board is not market quotes."),
    },
    "Risk-neutral density": {
        "meaning": ("옵션 가격(SVI 스마일)에서 거꾸로 계산한, 만기 때 기초자산 수준에 대한 위험중립 확률밀도(f_Q)입니다.",
                    "The risk-neutral density (f_Q) of the underlying's level at expiry, backed out of option "
                    "prices (the SVI smile)."),
        "look": ("봉우리의 위치와 왼쪽 꼬리의 두께를 보세요. 위 표의 적분 값이 1에 가까워야 밀도가 제대로 계산된 "
                 "것입니다.",
                 "Look at where the peak sits and how fat the left tail is. The integral in the table above should "
                 "be close to 1 for a well-formed density."),
        "interpret": ("왼쪽 꼬리가 두꺼울수록 옵션 시장이 큰 하락 가능성에 보험료를 더 얹어 가격을 매기고 있다는 "
                      "뜻입니다.",
                      "A fatter left tail means option prices carry more premium for a large fall."),
        "limit": ("위험중립 밀도는 실제 확률이 아니라 위험 보상이 섞인 가격 기준의 분포입니다. 지수 방향을 예측하지 "
                  "않습니다.",
                  "A risk-neutral density is not the real-world probability; it mixes in the price of risk. It "
                  "does not forecast the index."),
    },
    "ETF price / NAV": {
        "meaning": ("ETF의 시장 거래가격과 1주당 순자산가치(NAV)를 날짜별로 함께 보여 줍니다.",
                    "The ETF's market price and its net asset value per share (NAV), day by day."),
        "look": ("두 선이 서로 붙어 움직이는지, 벌어지는 구간이 있는지 보세요.",
                 "Whether the two lines move together, and where they come apart."),
        "interpret": ("가격이 NAV보다 위면 보유 자산 가치보다 비싸게(할증), 아래면 싸게(할인) 거래된 것입니다. 그 차이는 "
                      "아래 괴리율 차트에 있습니다.",
                      "Price above NAV means the ETF traded above the value of its holdings (a premium), below it "
                      "at a discount. The gap is charted in the premium chart below."),
        "limit": ("일별 종가 기준이며 장중 가격과 다를 수 있습니다. 매매 신호가 아닙니다.",
                  "Based on daily closes; intraday prices can differ. Not a trading signal."),
    },
    "NAV premium": {
        "meaning": ("ETF 시장가격과 순자산가치(NAV)의 차이인 괴리율(%)을 날짜별로 보여 줍니다.",
                    "The premium (%): the gap between the ETF's market price and its NAV, day by day."),
        "look": ("선이 0 위(할증)인지 아래(할인)인지와 크게 벌어지는 구간을 보세요.",
                 "Whether the line is above 0 (premium) or below it (discount), and where it grows."),
        "interpret": ("괴리율이 양수면 ETF가 보유 자산 가치보다 비싸게, 음수면 싸게 거래된 것입니다. 0 근처에서 작게 "
                      "움직일수록 가격이 순자산가치를 잘 따라간 것입니다.",
                      "A positive premium means the ETF traded above the value of its holdings, a negative one "
                      "below it. Small moves around 0 mean the price tracked the NAV closely."),
        "limit": ("일별 종가 기준이며 장중 괴리율과 다를 수 있습니다. 괴리율이 줄어든다는 예측이나 매매 신호가 아닙니다.",
                  "Based on daily closes; the intraday premium can differ. It is not a forecast that the gap will "
                  "close or a trading signal."),
    },
    "Kimchi premium": {
        "meaning": ("업비트의 원화 비트코인 가격이 바이낸스 달러 가격을 원화로 환산한 값보다 몇 % 비싼지(김치 프리미엄)를 "
                    "날짜별로 보여 줍니다.",
                    "How many percent the won price of bitcoin on Upbit is above the Binance dollar price converted "
                    "into won (the kimchi premium), day by day."),
        "look": ("선이 0 위인지 아래인지, 최근 값이 지난 범위에 비해 높은지 낮은지를 보세요.",
                 "Whether the line is above or below 0, and whether the latest value is high or low against the "
                 "past range."),
        "interpret": ("0보다 위면 국내 가격이 해외보다 비싸고, 아래면 쌉니다(역프리미엄). 프리미엄이 벌어졌다가 0 쪽으로 "
                      "돌아오는 속도는 화면의 반감기 수치로 확인하세요.",
                      "Above 0 the domestic price is dearer than abroad, below 0 cheaper (a reverse premium). How "
                      "fast a gap closes back toward 0 is the half-life shown on the page."),
        "limit": ("국내외 거래소 종가와 환율로 계산한 값이며 수수료·송금 제한·세금은 빠져 있습니다. 가격 예측이나 차익거래 "
                  "기회를 뜻하지 않습니다.",
                  "Computed from exchange closes and the exchange rate; fees, transfer limits and taxes are left "
                  "out. It is not a forecast or an arbitrage opportunity."),
    },
    "Perpetual funding": {
        "meaning": ("바이낸스 비트코인 무기한 선물의 펀딩비를 7일 평균으로 고르게 한 뒤 연율로 환산한 값입니다.",
                    "The funding rate of the Binance bitcoin perpetual future, smoothed over 7 days and annualised."),
        "look": ("선이 0 위인지 아래인지와 최근 급등·급락 구간을 보세요.",
                 "Whether the line is above or below 0, and recent spikes or drops."),
        "interpret": ("양수면 매수(롱) 포지션이 매도(숏) 포지션에 펀딩비를 내고 있다는 뜻으로 선물 매수 수요가 많다는 "
                      "신호이고, 음수면 그 반대입니다.",
                      "Positive means long positions pay shorts, a sign of strong demand to be long the future; "
                      "negative is the reverse."),
        "limit": ("과거 펀딩비이며 앞으로의 펀딩비나 가격을 예측하지 않습니다. 실제 캐리 수익은 거래 비용과 가격 변동에 "
                  "따라 달라집니다.",
                  "Past funding only, not a forecast of funding or price. Any real carry depends on trading costs "
                  "and price moves."),
    },
    "Bitcoin": {
        "meaning": ("일별 종가와 50일·200일 단순이동평균을 함께 그린 가격 흐름입니다.",
                    "Daily closes with the 50- and 200-day simple moving averages."),
        "look": ("가격이 이동평균선 위에 있는지 아래에 있는지, 50일선이 200일선 위에 있는지를 보세요.",
                 "Whether the price is above or below the averages, and whether the 50-day average is above the "
                 "200-day one."),
        "interpret": ("가격이 이동평균 위에 있으면 최근 가격이 그 기간 평균보다 높다는 뜻입니다. 50일선이 200일선을 넘어서는 "
                      "것은 이미 일어난 상승을 요약할 뿐입니다.",
                      "A price above an average means recent prices exceed that period's mean. A 50-over-200 cross "
                      "summarises a rise that has already happened."),
        "limit": ("지나간 가격만 보여 주며 앞으로의 방향을 예측하지 않습니다. 합성 데이터이면 실제 시세가 아닙니다.",
                  "Past prices only, not a forecast. Synthetic data means these are not market prices."),
    },
    "Price history": {
        "meaning": ("일별 종가가 날짜에 따라 어떻게 움직였는지 보여 줍니다.",
                    "How the daily close moved over time."),
        "look": ("오른쪽 끝(가장 최근)의 가격과 최근 방향, 크게 움직인 구간을 보세요.",
                 "Look at the right end (the latest price), the recent direction and the large moves."),
        "interpret": ("위의 구성 점수는 이 가격 흐름에서 정해진 규칙으로 계산한 요약입니다.",
                      "The component scores above are rule-based summaries of this price path."),
        "limit": ("지나간 가격만 보여 주며 앞으로의 방향을 예측하지 않습니다. 합성 데이터이면 실제 시세가 아닙니다.",
                  "Past prices only, not a forecast. Synthetic data means these are not market prices."),
    },
    "Component scores · -100…100": {
        "meaning": ("기술적 관측의 구성 항목마다 -100부터 +100까지의 점수를 0을 가운데 둔 막대로 보여 줍니다.",
                    "Each technical component's score from -100 to +100, as bars centred on 0."),
        "look": ("막대가 0의 오른쪽(+)인지 왼쪽(−)인지와 길이를 보세요. 오른쪽 숫자가 정확한 점수입니다.",
                 "Whether each bar points right of 0 (+) or left (−), and how long it is. The number on the right "
                 "is the exact score."),
        "interpret": ("오른쪽으로 길수록 그 항목이 상승 쪽을, 왼쪽으로 길수록 하락 쪽을 가리킵니다. 항목끼리 방향이 다르면 "
                      "신호가 엇갈린다는 뜻입니다.",
                      "The longer to the right, the more that component leans up; to the left, down. Components "
                      "pointing different ways mean the signals disagree."),
        "limit": ("점수는 정해진 규칙으로 계산한 요약 값이며 수익 전망이나 검증 통과를 뜻하지 않습니다.",
                  "A score is a rule-based summary; it is not a return forecast or a validation pass."),
    },
}
