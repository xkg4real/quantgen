"""Rates page (ui/rates_page.py) and curve construction method names."""

EN_TO_KO: dict[str, str] = {
    # Page chrome
    "Yield curve, swaps, swaptions and caps, short-rate simulation — single-curve, ACT/365F, "
    "decimals inside.":
        "수익률 곡선, 스왑, 스왑션·캡/플로어, 단기금리 시뮬레이션 — 단일 곡선, ACT/365F 기준으로 계산합니다.",
    "Swap pricer": "스왑 가격 계산",
    "Swaption / cap-floor": "스왑션 · 캡/플로어",
    "Rate simulation": "금리 시뮬레이션",
    "Curve source": "곡선 출처",
    "Auto (FRED, synthetic fallback)": "자동 (FRED, 실패 시 합성 곡선)",
    "Run": "실행",
    "Pick a tool and press Run": "도구를 고른 뒤 실행을 누르세요",
    "The curve comes from FRED (keyless); with no connection every tool runs on a clearly "
    "labeled synthetic curve, so everything here works immediately.":
        "곡선은 FRED에서 키 없이 받아옵니다. 연결되지 않으면 모든 도구가 '합성'으로 분명히 표시된 "
        "시연용 곡선으로 계산하므로 바로 사용할 수 있습니다.",
    # Yield curve inputs and construction methods
    "Curve method": "곡선 구축 방법",
    "Lookback (sessions)": "변화 비교 기간 (거래일)",
    "Bootstrap": "부트스트랩",
    "Natural cubic spline": "자연 3차 스플라인",
    "Monotone cubic (PCHIP)": "단조 3차 보간 (PCHIP)",
    "Monotone convex (Hagan-West)": "단조 볼록 보간 (Hagan-West)",
    "Diebold-Li": "Diebold-Li (λ 고정)",
    "Exact fit: reprices every quoted yield": "정확 적합 · 모든 고시 금리를 그대로 재현",
    "Smooth fit: the fit error is shown": "근사 적합 · 적합 오차를 함께 표시",
    "Solves the zero rate at each quoted maturity in turn so every quoted yield is repriced "
    "exactly; between maturities the forward rate is held flat. The standard choice for pricing: "
    "the swap, option and simulation tools always use it.":
        "고시된 만기마다 무이표 금리를 차례로 풀어 모든 고시 금리를 정확히 재현하고, 만기 사이의 "
        "선도금리는 일정하다고 둡니다. 가격 산출의 표준 방법이며 스왑·옵션·시뮬레이션 도구는 항상 이 "
        "방법을 씁니다.",
    "Draws a natural cubic spline through the quoted par yields, reads a yield at every half-year "
    "and bootstraps them. Smooth and exact at every quote, but it can swing between widely spaced "
    "long maturities.":
        "고시된 파 금리를 자연 3차 스플라인으로 잇고, 반년마다 읽은 금리를 부트스트랩합니다. 모든 고시 "
        "금리를 정확히 지나는 매끄러운 곡선이지만, 만기 간격이 넓은 장기 구간에서는 출렁일 수 있습니다.",
    "Like the cubic spline, but with a shape-preserving monotone cubic (PCHIP) that never "
    "overshoots the quotes, so it adds no bumps the market does not show. A safe smooth choice for "
    "sparse or kinked curves.":
        "3차 스플라인과 같지만 모양을 보존하는 단조 3차 보간(PCHIP)을 써서 이웃한 고시 금리 범위를 "
        "벗어나지 않습니다. 시장에 없는 굴곡을 만들지 않아, 만기가 듬성하거나 꺾인 곡선에 안전한 "
        "선택입니다.",
    "Hagan and West's method: forward rates are continuous and stay positive, and a change in one "
    "quote moves the curve only nearby, while every quote is repriced exactly. The U.S. Treasury "
    "has used it for its official par yield curve since December 2021.":
        "Hagan-West 방법: 선도금리가 끊기지 않고 양수로 유지되며, 한 만기의 금리가 바뀌어도 그 주변만 "
        "움직입니다. 모든 고시 금리를 정확히 재현하며, 미국 재무부가 2021년 12월부터 공식 파 수익률 "
        "곡선에 쓰고 있습니다.",
    "The method insurance supervisors use (EIOPA, Solvency II): it passes exactly through every "
    "quote and, beyond the last one, bends the forward rate toward an assumed ultimate forward rate "
    "of 3.30% (convergence speed alpha 0.10). Both values are assumptions, not estimates; use it to "
    "see a long-end extrapolation.":
        "보험 감독(EIOPA, 지급여력제도 Solvency II)에서 쓰는 방법입니다. 모든 고시 금리를 정확히 지나고, "
        "마지막 만기 뒤의 선도금리는 미리 가정한 장기 선도금리(UFR) 3.30%로 수렴시킵니다(수렴 속도 alpha "
        "0.10). 두 값은 추정치가 아닌 가정이며, 초장기 구간의 외삽을 볼 때 씁니다.",
    "Fits three factors (level, slope and curvature) plus one decay parameter by least squares. "
    "Smooth and easy to read, but it misses individual quotes; the fit error is shown with the "
    "result.":
        "수준·기울기·곡률 세 요인과 감쇠 모수 하나를 최소제곱으로 맞춥니다. 매끄럽고 읽기 쉽지만 개별 "
        "고시 금리와는 차이가 나며, 적합 오차를 결과와 함께 보여 줍니다.",
    "Nelson-Siegel with the decay fixed at 0.0609 per month (Diebold and Li, 2006), so the three "
    "factors come from a plain regression and can be compared from day to day. Built for tracking "
    "and forecasting the curve; it fits single quotes more loosely.":
        "감쇠 모수를 월 0.0609로 고정한 Nelson-Siegel입니다(Diebold-Li, 2006). 세 요인을 단순 회귀로 "
        "구해 날짜끼리 비교할 수 있어 곡선 추적·예측에 쓰며, 개별 고시 금리와의 차이는 더 큽니다.",
    "Nelson-Siegel with a second hump term (six parameters). It follows long-end shapes better; "
    "many central banks publish curves fitted this way.":
        "Nelson-Siegel에 두 번째 굴곡 항을 더한 모형입니다(모수 6개). 장기 구간 모양을 더 잘 따라가며, "
        "여러 중앙은행이 이 방식으로 맞춘 곡선을 공표합니다.",
    "Nelson-Siegel plus a second slope term that decays twice as fast (five parameters, Björk and "
    "Christensen, 1999). It starts from the Nelson-Siegel fit, so it never fits worse than "
    "Nelson-Siegel.":
        "Nelson-Siegel에 두 배 빠르게 사라지는 두 번째 기울기 항을 더한 모형입니다(모수 5개, "
        "Björk-Christensen, 1999). Nelson-Siegel 적합에서 출발하므로 오차가 그보다 커지지 않습니다.",
    # Swap inputs
    "Swap tenor": "스왑 만기",
    "10y or 5y5y": "예: 10y 또는 5y5y",
    "Fixed rate %": "고정금리 %",
    "blank = par": "비우면 파 금리",
    "Pay fixed": "고정금리 지급",
    "Receive fixed": "고정금리 수취",
    "Tenor: 10y for a spot swap, 5y5y for a 5-year swap starting in 5 years. Leave the fixed "
    "rate blank to price at the par rate.":
        "만기는 바로 시작하는 스왑이면 10y, 5년 뒤 시작하는 5년 스왑이면 5y5y처럼 적습니다. 고정금리를 "
        "비우면 파 금리로 계산합니다.",
    # Swaption / cap-floor inputs
    "Swaption": "스왑션",
    "Cap": "캡",
    "Floor": "플로어",
    "Option expiry": "옵션 만기",
    "Swap / cap length": "스왑·캡 기간",
    "blank = ATM": "비우면 ATM",
    "Swaption side": "스왑션 방향",
    "Payer": "지급자형 (Payer)",
    "Receiver": "수취자형 (Receiver)",
    "Option model": "옵션 모형",
    "Bachelier (normal)": "Bachelier (정규)",
    "Normal vol (bp)": "정규 변동성 (bp)",
    "Black vol (%)": "Black 변동성 (%)",
    "Option expiry applies to swaptions only. Length is the underlying swap, or the whole cap or "
    "floor. Leave the strike blank for at-the-money.":
        "옵션 만기는 스왑션에만 쓰입니다. 기간은 기초 스왑의 길이, 또는 캡·플로어 전체 기간입니다. "
        "행사가를 비우면 등가격(ATM)으로 계산합니다.",
    # Rate simulation inputs
    "Rate model": "금리 모형",
    "Horizon (years)": "기간 (년)",
    "Threshold % (optional)": "기준 금리 % (선택)",
    "Revalue": "재평가 대상",
    "Nothing": "없음",
    "Bond": "채권",
    "Payer swap": "고정금리 지급 스왑",
    "Instrument tenor": "상품 만기",
    "Bond coupon %": "채권 쿠폰 %",
    "The model is calibrated on the SOFR history. The threshold (optional) adds the probability "
    "of ending above it; tenor and coupon are used only when an instrument is revalued.":
        "모형은 SOFR 과거 자료로 보정합니다. 기준 금리(선택)를 넣으면 기간 말에 그보다 높을 확률을 "
        "함께 보여 주며, 상품 만기와 쿠폰은 재평가할 상품을 고른 경우에만 쓰입니다.",
    # Result notices
    "Synthetic curve, not market data: a simulated demo curve stands in for the FRED Treasury "
    "curve. The reason is under Details.":
        "합성 곡선입니다. 시장 데이터가 아니라, FRED 미국채 곡선 대신 시연용 모의 곡선으로 계산했습니다. "
        "이유는 '자세히'에서 볼 수 있습니다.",
    "Synthetic short rate, not market data: a simulated series stands in for SOFR. The reason "
    "is under Details.":
        "합성 단기금리입니다. 시장 데이터가 아니라, SOFR 대신 모의 시계열로 계산했습니다. 이유는 "
        "'자세히'에서 볼 수 있습니다.",
    "Details": "자세히",
    # Curve results
    "2s10s": "2s10s (10년−2년)",
    "5s30s": "5s30s (30년−5년)",
    "3m10y": "3m10y (10년−3개월)",
    "2s5s10s fly": "2s5s10s 버터플라이",
    "Level (2/5/10y)": "금리 수준 (2·5·10년 평균)",
    "1y1y": "1y1y (1년 뒤 1년 선도)",
    "2y1y": "2y1y (2년 뒤 1년 선도)",
    "1y fwd vs 1y": "1년 금리의 1년 뒤 예상 변화",
    # Swap results
    "Par rate": "파 스왑금리",
    "Fixed rate": "고정금리",
    "Fixed rate (par)": "고정금리 (= 파 금리)",
    "PV": "현재가치 (PV)",
    "DV01 (+1bp P&L)": "DV01 (금리 +1bp 때 손익)",
    "Annuity": "연금계수 (Annuity)",
    "Carry (first period)": "캐리 (첫 이자기간)",
    "Roll-down 1y": "1년 롤다운",
    "Forward swap": "선도 스왑",
    # Swaption / cap-floor results
    "Forward": "선도 스왑금리",
    "Strike (ATM)": "행사가격 (ATM)",
    "Premium": "프리미엄",
    "Premium (bp of notional)": "프리미엄 (명목금액 대비 bp)",
    "Delta (per +1bp fwd)": "델타 (선도금리 +1bp당)",
    "Gamma (per bp²)": "감마 (bp²당)",
    "Vega (per 1bp normal vol)": "베가 (정규 변동성 1bp당)",
    "Vega (per 1 vol-pt Black vol)": "베가 (Black 변동성 1%p당)",
    "Theta (1d)": "세타 (1일)",
    "Other-model vol": "다른 모형으로 환산한 변동성",
    "ATM (par swap)": "ATM (파 스왑금리)",
    "Caplets": "캐플릿 수",
    "Dearest caplet": "가장 비싼 캐플릿",
    # Simulation results
    "Mean reversion (kappa)": "평균회귀 속도 (kappa)",
    "Half-life": "반감기",
    "Long-run mean (theta)": "장기 평균 (theta)",
    "Volatility (sigma)": "변동성 (sigma)",
    "Current rate (r0)": "현재 단기금리 (r0)",
    "90% range": "90% 구간",
    "Mean PV": "평균 현재가치",
    "VaR 95 (loss)": "VaR 95 (손실)",
    "CVaR 95": "CVaR 95 (기대 초과손실)",
}
