"""Structuring, FX, Bonds, Derivatives, ETF, Crypto and KRX pages.

Exact English source -> Korean caption. Dynamic sentences (numbers inside the
words) are authored in Korean at the call site with `LocalText` / the
`ui.ficc_widgets` helpers instead. Tickers, model names (SABR, GARCH, SVI),
indicator abbreviations and verdict codes stay as they are.
"""

EN_TO_KO: dict[str, str] = {
    # ------------------------------------------------------------ shared chrome
    "Run": "실행",
    "Load": "불러오기",
    "Refresh": "새로고침",
    "Analyze": "분석 실행",
    "Optional": "선택 입력",
    "Open Settings": "설정 열기",
    "n/a": "해당 없음",
    "not run": "실행 안 됨",
    "Equity": "주식",
    "Tenor": "만기",
    "Premium": "프리미엄",
    "Yield": "수익률",
    "Data": "데이터",
    "Engine": "엔진",
    "Provider message (why the data is simulated)": "제공처 메시지 (시뮬레이션 데이터로 계산한 이유)",

    # --------------------------------------------------------------- Structuring
    "Structured products decomposed into legs, priced off the latest UST par curve, with Greeks and the "
    "first-order hedge sheet.":
        "구조화 상품을 구성요소로 나누고 최신 미국 국채 파 수익률 곡선으로 가격을 매깁니다. "
        "민감도(그릭스)와 1차 헤지표를 함께 보여 줍니다.",
    "Product": "상품",
    "Principal-protected note": "원금보장형 노트",
    "Reverse convertible": "역전환사채형 노트",
    "Dual-currency deposit": "이중통화예금",
    "Steepener note": "스티프너 노트 (CMS)",
    "Curve source": "곡선 출처",
    "Auto (FRED, synthetic fallback)": "자동 (FRED, 실패 시 합성 곡선)",
    "Underlying": "기초자산",
    "3y, 6m": "예: 3y, 6m",
    "Futures DV01 / contract": "계약당 선물 DV01",
    "Price the term sheet": "입력한 조건표로 가격 계산",
    "Vol (%)": "변동성 (%)",
    "Foreign rate / dividend (%)": "해외금리·배당수익률 (%)",
    "Protection (%)": "원금보장 비율 (%)",
    "Issue price": "발행가격",
    "Margin (per 100)": "발행 마진 (100당)",
    "Strike (% of spot)": "행사가격 (현물 대비 %)",
    "Coupon (%)": "쿠폰 (%)",
    "Blank = solve": "빈칸이면 자동 산출",
    "Base ccy": "기준통화",
    "Quote ccy": "상대통화",
    "Base-ccy rate (%)": "기준통화 금리 (%)",
    "Leverage (x)": "레버리지 (배)",
    "Floor (%)": "쿠폰 하한 (%)",
    "Cap (%)": "쿠폰 상한 (%)",
    "Blank = no cap": "빈칸이면 상한 없음",
    "Coupons / yr": "연간 이자 지급 횟수",
    "Structure a product": "상품을 구성해 보세요",
    "Pick a product and type the term sheet. Without FRED the note prices off a clearly labeled synthetic "
    "curve, so every control here works immediately.":
        "상품을 고르고 조건표를 입력한 뒤 [가격]을 누르세요. 금리 곡선은 앱이 FRED에서 자동으로 가져오며, "
        "FRED에 연결되지 않으면 '합성' 표시가 붙은 곡선으로 계산하므로 모든 기능을 바로 쓸 수 있습니다.",
    "Fair value": "공정가치",
    "Leverage": "레버리지",
    "Participation": "참여율",
    "First-period expected coupon · p.a.": "첫 이자기간 기대 쿠폰 · 연율",
    "Enhanced yield (simple)": "가산 수익률 (단리)",
    "Coupon (p.a.)": "쿠폰 (연율)",
    "Delta (per +1% spot)": "델타 (현물 +1%당)",
    "Gamma (per +1%)": "감마 (+1%당)",
    "Vega (per vol-pt)": "베가 (변동성 1%p당)",
    "DV01 (per -1bp)": "DV01 (금리 -1bp당)",
    "2s10s DV01 (per +1bp)": "2년-10년 DV01 (+1bp당)",
    "x-axis: realised 10y-2y spread in bp, held flat for every coupon period":
        "가로축: 실현 10년-2년 금리 스프레드(bp), 모든 이자기간 동안 같은 값이라고 가정",
    "Legs (per 100 of notional, signed for the holder)": "구성요소 (명목 100당, 보유자 기준 부호)",
    "Hedge sheet (+ buy / pay fixed, - sell / receive)": "헤지표 (+ 매수·고정금리 지급, - 매도·고정금리 수취)",
    "No first-order hedge: every Greek is zero.": "1차 헤지가 필요 없습니다: 모든 민감도가 0입니다.",

    # ------------------------------------------------------------------------ FX
    "Forwards, carry, Garman-Kohlhagen on a SABR smile, and a no-lookahead G10+KRW carry backtest.":
        "선도환율과 캐리, SABR 변동성 스마일 위의 Garman-Kohlhagen 옵션 가격, "
        "미래 정보를 쓰지 않는 G10+KRW 캐리 백테스트를 계산합니다.",
    "Spot, forward & carry": "현물·선도환율·캐리",
    "Option & smile": "통화옵션·변동성 스마일",
    "Carry basket": "캐리 바스켓",
    "Auto (Yahoo spot, FRED rates)": "자동 (현물 Yahoo, 금리 FRED)",
    "Pair": "통화쌍",
    "EURUSD or USD/KRW": "예: EURUSD, USD/KRW",
    "Quote-ccy rate %": "상대통화 금리 %",
    "Base-ccy rate %": "기준통화 금리 %",
    "blank = short rate": "빈칸이면 최신 단기금리",
    "Blank = latest short rate": "빈칸이면 최신 단기금리",
    "USD for EURUSD; KRW for USDKRW": "EURUSD는 USD, USDKRW는 KRW 금리",
    "EUR for EURUSD; USD for USDKRW": "EURUSD는 EUR, USDKRW는 USD 금리",
    "Market forward (optional)": "시장 선도환율 (선택)",
    "outright, e.g. 1.1050": "아웃라이트 환율, 예: 1.1050",
    "1.12, 25d or ATM": "예: 1.12, 25d, ATM",
    "Call": "콜",
    "Put": "풋",
    "ATM vol %": "ATM 변동성 %",
    "25d call vol minus 25d put vol": "25델타 리스크 리버설: 25델타 콜 변동성 - 25델타 풋 변동성",
    "25d butterfly: wing vol over ATM vol": "25델타 버터플라이: ATM 대비 날개 변동성 가산분",
    "Top n": "상위 n개",
    "Cost (bp)": "거래비용 (bp)",
    "Per side; defaults to QUANTGEN's FX table rate": "편도 기준이며 기본값은 QUANTGEN 외환 비용표의 값입니다",
    "Rebalance (sessions)": "리밸런싱 주기 (거래일)",
    "History (sessions)": "분석 기간 (거래일)",
    "Pick a tool and press Run": "도구를 고르고 [실행]을 누르세요",
    "Forwards and carry, a vanilla on the smile, or the carry basket. Blank rate fields pull the latest short "
    "rate; without providers everything runs on a clearly labeled synthetic series.":
        "선도환율과 캐리, 스마일 위의 바닐라 통화옵션, 또는 캐리 바스켓을 계산합니다. 금리 칸을 비워 두면 "
        "최신 단기금리를 자동으로 가져오고, 데이터 제공처에 연결되지 않으면 '합성' 표시가 붙은 시계열로 계산합니다.",
    "Points": "스왑포인트",
    "Implied basis": "내재 베이시스",
    "% of spot": "현물 대비 %",
    "Spot / forward": "현물 / 선도환율",
    "Vol used": "적용 변동성",
    "SABR vol at the strike": "행사가격에서의 SABR 변동성",
    "Delta (spot)": "델타 (현물)",
    "Gamma / 1%": "감마 / 1%",
    "Vega / vol-pt": "베가 / 변동성 1%p",
    "Theta / day": "세타 / 1일",
    "Solver status only; independent validation NOT_RUN": "최적화 상태만 표시합니다. 독립 검증은 NOT_RUN입니다.",
    "Best score": "최고 점수",
    "Highest carry": "최고 캐리",
    "Basket return": "바스켓 누적 수익률",
    "Ann. return": "연환산 수익률",
    "Ann. vol": "연환산 변동성",
    "Equal-weight long": "동일가중 매수 수익률",

    # --------------------------------------------------------------------- Bonds
    "Price, yield, duration and convexity; key-rate DV01s, z-spread and carry/roll off the UST curve; curve "
    "scenarios; a Treasury-futures hedge.":
        "가격·수익률·듀레이션·컨벡시티, 미국 국채 곡선 기준 만기별 DV01·z-스프레드·캐리/롤다운, "
        "금리 곡선 시나리오, 국채선물 헤지를 계산합니다.",
    "Auto (FRED, else synthetic)": "자동 (FRED, 실패 시 합성 곡선)",
    "Maturity (years)": "만기 (년)",
    "Coupons / year": "연간 이자 지급 횟수",
    "Price (per 100)": "가격 (액면 100당)",
    "blank = from yield": "빈칸이면 수익률로 계산",
    "blank = from price": "빈칸이면 가격으로 계산",
    "Blank = from yield": "빈칸이면 수익률로 계산",
    "Blank = from price": "빈칸이면 가격으로 계산",
    "Position DV01": "포지션 DV01",
    "Blank = from the calculator": "빈칸이면 계산기 값 사용",
    "Describe a bond and press Run": "채권 조건을 입력하고 [실행]을 누르세요",
    "Quote it by price or by yield (leave the other blank). The curve comes from FRED without a key; without a "
    "connection the page runs on a labeled synthetic curve.":
        "가격과 수익률 중 하나만 입력하세요(다른 하나는 비워 둡니다). 금리 곡선은 앱이 FRED에서 키 없이 "
        "자동으로 가져오며, 연결되지 않으면 '합성' 표시가 붙은 곡선으로 계산합니다.",
    "z-spread": "z-스프레드",
    "Currency per bp, positive for a long": "금리 1bp당 통화 금액, 매수 포지션은 양수",
    "Roll-down": "롤다운",
    "Carry + roll": "캐리 + 롤다운",
    "Breakeven": "손익분기 금리 상승폭",
    "Yield rise that wipes out carry + roll": "캐리와 롤다운 수익을 모두 상쇄하는 수익률 상승폭",
    "Worst": "최악 시나리오",
    "Best": "최선 시나리오",
    "Futures DV01": "선물 DV01",
    "CTD DV01 / CF": "CTD DV01 / 전환계수",
    "Contracts to sell": "매도할 선물 계약 수",
    "Rounded": "반올림 계약 수",
    "From the calculator unless overridden": "직접 입력하지 않으면 계산기 값",

    # --------------------------------------------------------------- Derivatives
    "KOSPI200 futures basis, option surface, risk-neutral density, box rate, hedge P&L.":
        "KOSPI200 선물 베이시스, 옵션 변동성 곡면, 위험중립 확률밀도, 박스 금리, 헤지 손익을 계산합니다.",
    "Board": "옵션 보드",
    "KIS live (KOSPI200 board)": "KIS 실시간 (KOSPI200 보드)",
    "Synthetic demo board": "합성 시연 보드",
    "Expiry (YYYYMM)": "만기월 (YYYYMM)",
    "blank = nearest": "빈칸이면 최근월물",
    "Blank = nearest expiry": "빈칸이면 최근월물",
    "Risk-free rate %": "무위험 금리 %",
    "Blank = CD 91-day rate": "빈칸이면 CD 91일물 금리",
    "Hedge-sim engine": "헤지 시뮬레이션 엔진",
    "GBM at the ATM vol": "GBM (ATM 변동성)",
    "GARCH(1,1)-t on the index history": "GARCH(1,1)-t (지수 가격 이력으로 추정)",
    "Load the board": "옵션 보드를 불러오세요",
    "The nearest KOSPI200 expiry from KIS (or a synthetic demo): futures basis and fair value, the Black-76 smile "
    "against the exchange's IV, an SVI fit with the butterfly check, the model-free variance, the risk-neutral "
    "density, the box-spread quote check, and a hedge P&L simulation in bp of notional.":
        "KIS에서 KOSPI200 최근월물(또는 합성 시연 보드)을 불러와 선물 베이시스와 이론가, 거래소 내재변동성과 "
        "비교한 Black-76 스마일, 버터플라이 점검을 포함한 SVI 적합, 모형무관 분산, 위험중립 확률밀도, "
        "박스 스프레드 호가 점검, 명목금액 대비 bp 단위 헤지 손익 시뮬레이션을 보여 줍니다.",
    "Synthetic board: a smile-shaped demo chain, not market quotes.":
        "합성 보드: 스마일 모양으로 만든 시연용 옵션 체인이며 시장 호가가 아닙니다.",
    "Forward (parity)": "선도가격 (풋-콜 패리티)",
    "Front future": "최근월 선물",
    "Basis (pts)": "베이시스 (pt)",
    "Mispricing": "이론가 대비 괴리",
    "Implied funding": "내재 조달금리",
    "KIS theo gap": "KIS 이론가 차이",
    "ATM IV": "ATM 내재변동성",
    "MFIV": "MFIV (모형무관 변동성)",
    "MFIV strike range": "MFIV 행사가격 범위",
    "IV gap vs KIS": "KIS 대비 내재변동성 차이",
    "Butterfly viol.": "버터플라이 위반",
    "Box rate (quote check)": "박스 금리 (호가 점검)",
    "RND ∫": "위험중립 밀도 적분",
    "Hedge P&L (mean)": "헤지 손익 (평균)",
    "SE": "표준오차",
    "Break-even realised vol": "손익분기 실현변동성",
    "Identity slope / R²": "항등식 기울기 / R²",
    "Model-free variance not computed": "모형무관 분산을 계산하지 않았습니다",
    "Options outside this range are omitted; the omitted wings bias MFIV downward (truncated strip).":
        "이 범위 밖의 옵션은 빠집니다. 빠진 날개 구간 때문에 MFIV는 낮게 나옵니다 (절단된 행사가격 구간).",
    "median |σ_app − σ_KIS| on quoted strikes within ±15 % of F; gate 0.5":
        "F의 ±15% 안에서 호가가 있는 행사가격의 |σ_앱 − σ_KIS| 중앙값, 기준 0.5",
    "short the ATM option at σ_h, delta-hedged daily; bp of notional":
        "σ_h로 ATM 옵션을 매도하고 매일 델타 헤지, 명목금액 대비 bp",
    "GBM engine: equals σ_h by construction, up to Monte Carlo noise":
        "GBM 엔진에서는 구성상 σ_h와 같습니다 (몬테카를로 오차 범위 안에서)",

    # ----------------------------------------------------------------------- ETF
    "NAV premium, basket, leveraged-fund drag, sleeve rules.":
        "NAV 괴리율, 구성종목, 레버리지 ETF 보유비용(드래그), 슬리브 규칙을 분석합니다.",
    "ETF code": "ETF 종목코드",
    "069500, 122630, SPY": "예: 069500, 122630, SPY",
    "Auto (KIS for KRX codes)": "자동 (국내 종목은 KIS)",
    "LETF comparison": "레버리지 ETF 비교 기준",
    "Zero-rate reference (legacy)": "무금리 기준 (기존 계산)",
    "Total-return scenario": "총수익 시나리오",
    "Price-return scenario": "가격수익 시나리오",
    "Annual funding rate (%)": "연 조달금리 (%)",
    "Explicit assumption, e.g. 3.21": "직접 입력하는 가정, 예: 3.21",
    "Annual fee (%)": "연 보수 (%)",
    "Explicit assumption": "직접 입력하는 가정",
    "Annual dividend yield (%)": "연 배당수익률 (%)",
    "Required for price return": "가격수익 비교에 필요",
    "LETF inputs are annual continuous-rate assumptions, not live market observations. Price-return comparison "
    "requires dividends; total-return already includes them. The zero-rate reference preserves the previous "
    "calculation.":
        "레버리지 ETF 입력값은 연속복리 기준 연간 가정이며 실시간 시장 관측값이 아닙니다. 가격수익 비교에는 "
        "배당수익률이 필요하고, 총수익에는 이미 배당이 포함됩니다. 무금리 기준은 기존 계산을 그대로 유지합니다.",
    "Pick an ETF": "ETF를 고르세요",
    "NAV premium and its half-life, the basket, the leveraged-fund drag from the GARCH variance term structure, "
    "and the trend / vol-target sleeve rules with the validation study's verdict.":
        "NAV 괴리율과 그 반감기, 구성종목, GARCH 분산 기간구조로 구한 레버리지 ETF 보유비용(드래그), "
        "추세·변동성 목표 슬리브 규칙과 검증 연구의 판정을 보여 줍니다. 데이터는 앱이 자동으로 가져옵니다.",
    "Enter explicit funding and fee assumptions; price-return also needs a dividend yield.":
        "조달금리와 보수 가정을 직접 입력하세요. 가격수익 비교에는 배당수익률도 필요합니다.",
    "NAV": "NAV (순자산가치)",
    "Tracking error": "추적오차",
    "AUM": "순자산총액",
    "CU shares": "CU 구성 주식수",
    "LP holding": "LP 보유 비중",
    "Listed": "상장일",
    "Trend switch Sharpe": "추세 전환 샤프 지수",
    "Trend MDD": "추세 전환 최대 낙폭",
    "Vol-target Sharpe": "변동성 목표 샤프 지수",
    "Buy & hold Sharpe": "매수 후 보유 샤프 지수",
    "B&H MDD": "매수 후 보유 최대 낙폭",
    "Study verdict: trend": "연구 판정: 추세 전환",
    "Study verdict: vol target": "연구 판정: 변동성 목표",
    "Index cond. vol": "지수 조건부 변동성",
    "Historical 122630 study · not current validation": "122630 과거 연구 · 현재 검증 아님",
    "Top constituents": "상위 구성종목",

    # -------------------------------------------------------------------- Crypto
    "Kimchi premium, funding carry, GARCH-t on Bitcoin — read-only.":
        "김치 프리미엄, 펀딩비 캐리, 비트코인 GARCH-t 분석 — 조회 전용입니다.",
    "Upbit + Binance (keyless)": "Upbit + Binance (키 불필요)",
    "Days": "기간 (일)",
    "Refresh the crypto sheet": "가상자산 시트를 새로고침하세요",
    "Kimchi premium, perpetual funding as carry, GARCH-t on Bitcoin, the ETH/BTC test and the weekday table, all "
    "from keyless Upbit and Binance data; Upbit holdings when a read-only key is set.":
        "김치 프리미엄, 캐리로 본 무기한 선물 펀딩비, 비트코인 GARCH-t, ETH/BTC 검정, 요일별 표를 키가 필요 없는 "
        "Upbit·Binance 데이터로 계산합니다. 조회 전용 키를 설정하면 Upbit 보유 자산도 보여 줍니다.",
    "Read-only: QUANTGEN never submits crypto orders, never holds a wallet key, and never assumes an account on an "
    "unregistered foreign exchange. Binance is public data only.":
        "조회 전용: QUANTGEN은 가상자산 주문을 내지 않고, 지갑 키를 보관하지 않으며, 미신고 해외 거래소 계정을 "
        "전제하지 않습니다. Binance는 공개 데이터만 사용합니다.",
    "Synthetic data: every series here is simulated.": "합성 데이터: 이 화면의 모든 시계열은 시뮬레이션입니다.",
    "Kimchi premium": "김치 프리미엄",
    "AR(1) amplitude half-life": "AR(1) 진폭 반감기",
    "Funding (ann.)": "펀딩비 (연율)",
    "Funding pct": "펀딩비 백분위",
    "Perp premium": "무기한 선물 프리미엄",
    "BTC cond. vol (365d)": "BTC 조건부 변동성 (365일)",
    "Not computed: fewer than 91 observations or no variation in the window.":
        "계산 안 됨: 관측치가 91개 미만이거나 구간 안에서 값이 변하지 않았습니다.",
    "Binance did not return both mark and index prices.": "Binance가 마크 가격과 지수 가격을 모두 주지 않았습니다.",
    "Weekday table (returns %, vol %, mean quote volume)": "요일별 표 (수익률 %, 변동성 %, 평균 거래대금)",
    "avg_buy_price is the cost-basis record for the 2027 virtual-asset tax; this page computes no tax.":
        "avg_buy_price는 2027년 가상자산 과세를 위한 취득가액 기록이며, 이 화면은 세금을 계산하지 않습니다.",
    "Set UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY (자산조회 scope only) to show holdings.":
        "보유 자산을 보려면 UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY(자산조회 권한만)를 설정하세요.",

    # ----------------------------------------------------------------------- KRX
    "Read-only Korean market data. Quotes and OHLCV from KIS, disclosures from OpenDART, snapshots from the KRX "
    "Open API.":
        "국내 시장 데이터 조회 전용 화면입니다. 시세와 일별 OHLCV는 KIS, 공시는 OpenDART, "
        "전 종목 스냅샷은 KRX Open API에서 가져옵니다.",
    "No order or account-mutation path exists in this build.": "이 빌드에는 주문이나 계좌를 변경하는 기능이 없습니다.",
    "KRX code": "종목코드",
    "Quote": "현재가",
    "Daily OHLCV": "일별 시세 (OHLCV)",
    "Disclosures (DART)": "공시 (DART)",
    "Financials (DART)": "재무제표 (DART)",
    "Whole-market snapshot": "전 종목 스냅샷",
    "Index levels": "지수 시세",
    "Choose a dataset and press Run": "조회할 데이터를 고르고 [실행]을 누르세요",
    "Results always carry the provider that produced them.": "결과에는 항상 데이터를 제공한 곳이 함께 표시됩니다.",
    "No Korean data provider is configured": "국내 데이터 제공처가 설정되지 않았습니다",
    "KIS needs KIS_APP_KEY + KIS_APP_SECRET, OpenDART needs OPENDART_API_KEY, and the KRX Open API needs "
    "KRX_API_KEY. All three are free to register; KRX's keyless export is blocked.":
        "KIS는 KIS_APP_KEY와 KIS_APP_SECRET, OpenDART는 OPENDART_API_KEY, KRX Open API는 KRX_API_KEY가 "
        "필요합니다. 세 곳 모두 무료로 등록할 수 있으며, KRX의 키 없는 내보내기는 차단되어 있습니다.",
    "Change %": "등락률",
    "Open / High / Low": "시가 / 고가 / 저가",
    "Market cap": "시가총액",
}
