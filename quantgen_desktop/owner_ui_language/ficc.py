"""Korean display text for the owner UI port, area: ficc. See the package docstring.

Bonds, Rates, Structuring and FX panes (owner issues 03, 08, 11, 14). Wording follows the Flet pages'
reviewed Korean (core/ui_page_messages/rates.py and ficc_pages.py) wherever Flet says the same thing; the
Flet catalogue itself already reaches native captions through `LocaleContext.text`, so only words the
native panes print and Flet does not are listed here. Raw keys and words whose Korean depends on the
screen (Shape, Regime, Theta, Sigma, Component, Forward, curve-shape codes) are not catalogued: the panes
show them under the specific English captions below (`model_narrative_language.show_as`), and the export
keeps the original words. Short finance words that are catalogued (Zero, Par, Swap, Rate, Score, level,
slope, curvature, option, swap, Years, Count) carry their one general Korean meaning.
"""

PAIRS = {
    # Pane titles: English source, Korean title led by the tool button's name (no "Rates · 한국어" mix).
    "Rates · yield curve and rate risk": "금리 · 수익률 곡선과 금리 위험",
    "Bonds · price, risk, scenarios and futures hedge": "채권 · 가격·위험·시나리오·선물 헤지",
    "Structuring · product structure, maturity payoff and risk": "구조화 상품 · 상품 구조·만기 손익·위험",
    "FX · spot, forwards, options and carry": "외환 · 현물·선물환·옵션·캐리",

    # Rates · yield curve
    "Curve table": "만기별 금리표",
    "Zero": "무이표 금리",
    "Par": "파 금리",
    "DF": "할인계수",
    "1y forward": "1년 선도금리",
    "Change · {n}d": "최근 {n}거래일 변화",
    "Yield · %": "수익률 · %",
    "Par yield · %": "파 수익률 · %",
    "Curve shape": "곡선 형태",
    "Upward (normal) curve": "정상 우상향",
    "Inverted curve": "역전",
    "Humped curve": "중간 만기 돌출",
    "Flat curve": "평탄",
    "Curve move · last {n} sessions": "최근 {n}거래일 곡선 변화",
    "Change window · sessions": "변화 비교 기간 · 거래일",
    "NS/NSS fit RMSE": "NS/NSS 적합 오차 (RMSE)",
    "PCA loadings": "PCA 요인 적재값",
    "PCA variance": "PCA 설명 분산",
    "PCA factor": "PCA 요인",
    "Explained": "설명 비율",
    "Latest score": "최근 점수",
    "level": "수준",
    "slope": "기울기",
    "curvature": "곡률",
    "Loading": "적재값",
    # Rates · swap
    "Key-rate DV01": "만기별 DV01",
    "Currency / bp": "통화 금액 / bp",
    "Forward swaps": "선도 스왑",
    "Swap": "스왑",
    "DV01 · +1bp P&L": "DV01 (금리 +1bp 때 손익)",
    "Carry · first period": "캐리 (첫 이자기간)",
    "Roll-down · 1y": "1년 롤다운",
    # Rates · swaption / cap-floor
    "Premium / notional": "명목금액 대비 프리미엄",
    "Delta · per +1bp": "델타 (선도금리 +1bp당)",
    "Gamma · per bp²": "감마 (bp²당)",
    "Vega · per 1bp normal vol": "베가 (정규 변동성 1bp당)",
    "Vega · per 1 vol-pt Black vol": "베가 (Black 변동성 1%p당)",
    "Theta · 1 day": "세타 (1일)",
    "ATM par swap": "ATM (파 스왑금리)",
    "Caplets": "캡렛",
    "Caplet premium": "캡렛 프리미엄",
    "Start · y": "시작 · 년",
    "End · y": "종료 · 년",
    "End · years": "종료 · 년",
    "Forward rate": "선도금리",
    "Black volatility · %": "Black 변동성 · %",
    # Rates · simulation
    "Mean reversion (kappa) · per year": "평균회귀 속도 (kappa) · 연",
    "Half-life · years": "반감기 · 년",
    "Threshold rate": "비교 금리",
    "Terminal mean": "기간 말 평균 금리",
    "P(terminal > threshold)": "기간 말 비교 금리 초과 확률",
    "{value} decimal / sqrt-year": "{value} (소수, 연 제곱근 기준)",
    "{value} sqrt-r": "{value} (sqrt-r 기준)",
    "bond mean PV": "채권 평균 현재가치",
    "swap mean PV": "스왑 평균 현재가치",
    "PV P5 / P95": "현재가치 P5 / P95",
    "VaR 95 · loss": "VaR 95 (손실)",
    "CVaR 95 · loss": "CVaR 95 (기대 초과손실)",
    "Horizon curve · median path": "기간 말 곡선 · 중앙 경로",
    "Horizon PV distribution": "기간 말 현재가치 분포",
    "Short rate · %": "단기금리 · %",
    "Years": "년",
    "Count": "개수",
    "Paths per bin": "구간별 경로 수",

    # Structuring
    "Greeks": "민감도 (그릭스)",
    "Maturity payoff": "만기 손익",
    "Leg decomposition": "구성요소 분해",
    "Hedge sheet": "헤지표",
    "Payoff": "만기 지급액",
    "Underlying at maturity": "만기 기초자산 가격",
    "Per 100 notional": "명목 100당",
    "Realized 10y–2y spread · bp": "실현 10년–2년 스프레드 · bp",
    "ATM call": "ATM 콜",
    # Leg kinds (`core.ficc.structured.Leg.kind`), as the Flet page shows them
    "zcb": "무이표채",
    "coupon_bond": "이표채",
    "option": "옵션",
    "swap": "스왑",

    # Bonds
    "Enter either price or yield, not both. Clear yield when entering price.":
        "가격과 수익률 중 하나만 입력하세요. 가격을 입력할 때는 수익률 칸을 비웁니다.",
    "Input error · Enter finite values and valid maturity/amount; keep either price or yield.":
        "입력 오류 · 유한한 수치와 유효한 만기·금액을 입력하고 가격과 수익률 중 하나만 남기세요.",
    "Curve price": "곡선 기준 가격",
    "Carry · {horizon} years": "캐리 · {horizon}년",
    "DV01 · currency per bp": "DV01 (금리 1bp당 통화 금액)",
    "Key tenor · years": "기준 만기 · 년",
    "DV01 · currency / bp": "DV01 · 1bp당 통화 금액",
    "Shock · bp": "금리 충격 · bp",
    "+25bp parallel": "+25bp 평행 이동",
    "-25bp parallel": "-25bp 평행 이동",
    "+100bp parallel": "+100bp 평행 이동",
    "-100bp parallel": "-100bp 평행 이동",
    "2y-5y-10y fly": "2년-5년-10년 버터플라이",
    "Duration tangent": "듀레이션 접선",
    "Yield (%)": "수익률 (%)",
    "Price per 100": "액면 100당 가격",

    # FX
    "Rate": "금리",
    "Score": "점수",
    "Annual vol": "연환산 변동성",
}
