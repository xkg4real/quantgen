"""Portfolio, Quant Lab, Signals, Execution, Rules, Settings and the research home/library/system pages and main navigation."""

EN_TO_KO: dict[str, str] = {
    # ------------------------------------------------------------------ shared inputs
    "Auto": "자동",
    "Auto (keyed providers only)": "자동 (키가 있는 제공자만)",
    "AAPL or 005930": "예: AAPL 또는 005930",
    "Data from": "데이터 출처",

    # ------------------------------------------------------------------ Signals (기술적 분석)
    "Technical composite with dissent shown, and a costed backtest against buy-and-hold.":
        "여러 기술적 지표를 하나의 점수로 모으되 반대 신호도 함께 보여 주고, 같은 아이디어를 거래비용을 "
        "반영해 백테스트한 결과를 매수 후 보유와 비교합니다.",
    "Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.":
        "참고용 관측입니다. 매매 신호가 아니며(DO-NOT-BUILD TF-12), 이 화면의 결과는 어떤 포트폴리오에도 "
        "반영되지 않습니다.",
    "Backtest strategy": "백테스트 전략",
    "MA cross (fast/slow)": "이동평균 교차 (단기/장기)",
    "Momentum (lookback)": "모멘텀 (관찰 기간)",
    "Fast/lookback": "단기·관찰 기간",
    "Slow/exit": "장기 기간·청산 기준",
    "Cost (bps)": "거래비용 (bp)",
    "ma_cross: fast SMA · momentum: lookback · rsi_revert: RSI period":
        "이동평균 교차: 단기 이동평균 기간 · 모멘텀: 관찰 기간 · RSI 평균회귀: RSI 계산 기간",
    "ma_cross: slow SMA · rsi_revert: exit-above RSI level · momentum: unused":
        "이동평균 교차: 장기 이동평균 기간 · RSI 평균회귀: 이 RSI 값 위에서 청산 · 모멘텀: 사용 안 함",
    "Analyze": "분석 실행",
    "Read a chart, then make the read prove itself": "차트를 읽고, 그 판단을 백테스트로 검증합니다",
    "The composite signal and its components render above the backtest of the same idea on the same history, "
    "with costs.":
        "종목을 입력하고 [분석 실행]을 누르면 종합 관측값과 지표별 점수가 먼저 나오고, 같은 기간에 같은 "
        "아이디어를 거래비용까지 반영해 백테스트한 결과가 이어서 나옵니다.",
    "Indicator readings": "지표별 관측",
    "Weight in the composite": "종합 점수에서의 가중치",
    "Trade statistics": "거래 통계",
    "beats buy & hold": "매수 후 보유보다 높음",
    "trails buy & hold": "매수 후 보유보다 낮음",
    "Strategy return": "전략 수익률",
    "Buy & hold": "매수 후 보유",
    "Max drawdown": "최대 낙폭",
    "Time in market": "보유 기간 비중",
    "RSI (14)": "RSI (14일)",
    "Synthetic data": "합성 데이터",
    "Yahoo Finance": "야후 파이낸스",
    "Crypto venue": "가상자산 거래소",

    # ------------------------------------------------------------------ Portfolio (포트폴리오)
    "Mean-variance optimization, risk parity, and the efficient frontier — solved with scipy on aligned daily "
    "histories.":
        "여러 종목을 묶어 평균-분산 최적화, 위험 균형(리스크 패리티), 효율적 투자선을 계산합니다. 종목들의 "
        "일별 가격을 같은 날짜로 맞춘 뒤 scipy로 풉니다.",
    "Symbols (comma separated)": "종목 (쉼표로 구분)",
    "AAPL, MSFT, NVDA, TLT, GLD": "예: AAPL, MSFT, NVDA, TLT, GLD",
    "Max Sharpe": "샤프 지수 최대화",
    "Minimum volatility": "최소 변동성",
    "Risk parity": "위험 균형 (리스크 패리티)",
    "Equal weight": "동일 비중",
    "Max weight/asset": "종목당 최대 비중 (0~1)",
    "Per-asset weight cap for the selected objective, 0 to 1 (1.0 = no cap).":
        "선택한 목적함수에서 한 종목이 가질 수 있는 최대 비중입니다. 0~1 사이로 입력하며 1.0은 상한 없음입니다.",
    "Risk-free %": "무위험 금리 (%)",
    "Optimize": "최적화 실행",
    "Build a portfolio": "포트폴리오를 구성해 보세요",
    "List symbols and pick an objective. All four objectives are computed and marked on the frontier so the "
    "trade-offs are visible, not implied.":
        "종목을 쉼표로 나눠 입력하고 목적함수를 고른 뒤 [최적화 실행]을 누르세요. 네 가지 목적함수를 모두 "
        "계산해 효율적 투자선 위에 함께 표시하므로, 서로의 장단점을 직접 비교할 수 있습니다.",
    "List at least two symbols, comma separated.": "종목을 두 개 이상, 쉼표로 나눠 입력하세요.",
    "At most 15 symbols — the covariance of more is not estimable on two years of dailies.":
        "종목은 최대 15개까지입니다. 그보다 많으면 2년치 일별 자료로 공분산을 안정적으로 추정할 수 없습니다.",
    "solver did not converge": "최적화 계산 미수렴",
    "Expected return (ann.)": "연 기대수익률",
    "Volatility (ann.)": "연 변동성",
    "Shared sessions": "공통 거래일 수",
    "Weights and risk contributions": "종목별 비중과 위험 기여도",
    "All four objectives compared": "네 가지 목적함수 비교",
    "Role": "구분",
    "Per-asset cap": "종목당 상한",
    "Efficient frontier": "효율적 투자선",
    "Frontier / random cloud: 100% per-asset bound; markers use each row's cap.":
        "효율적 투자선과 무작위 포트폴리오 점은 종목당 100% 상한으로, 목적함수 표식은 각 행의 상한으로 계산했습니다.",
    "Correlation of daily returns": "일별 수익률의 상관관계",
    "Yahoo (total return)": "야후 (총수익 기준)",

    # ------------------------------------------------------------------ Quant Lab (분포 분석)
    "Monte Carlo simulation — calibrated on daily history, seeded and reproducible.":
        "한 종목의 일별 가격으로 모형을 보정한 뒤 몬테카를로 모의실험으로 미래 가격의 분포를 그립니다. "
        "난수 시드가 고정되어 같은 입력이면 같은 결과가 나옵니다.",
    "Auto (KIS for 6-digit, else FMP)": "자동 (6자리 코드는 KIS, 그 외 FMP)",
    "GARCH(1,1)-t (default)": "GARCH(1,1)-t (기본)",
    "GBM (lognormal)": "GBM (로그정규)",
    "Jump diffusion (Merton)": "점프 확산 (Merton)",
    "Block bootstrap (empirical)": "블록 부트스트랩 (실제 수익률 재표집)",
    "Risk premium: rf + ERP, less convexity (default)": "위험프리미엄 방식 (기본)",
    "Zero (stress view)": "0 (스트레스 관점)",
    "Risk-neutral: rf, less convexity": "위험중립 방식",
    "Sample mean (noisy)": "표본 평균 (잡음 큼)",
    "ERP %": "위험프리미엄 (%)",
    "equity 4 / bonds-gold 1 / FX 0": "권장값: 주식 4 · 채권·금 1 · 외환 0",
    "Horizon (sessions)": "기간 (거래일)",
    "Target price (optional)": "목표 가격 (선택)",
    "Simulate": "모의실험 실행",
    "Calibrate and simulate": "종목과 모형을 고르고 모의실험을 실행하세요",
    "Pick a symbol and a model — GARCH(1,1)-t is the default, so volatility clustering and fat tails are in the "
    "fan from the first run. The drift defaults to the risk-premium view (rf + ERP, less each model's convexity "
    "correction): in the out-of-sample study the trailing sample mean had no forecasting power over one year, so "
    "it is offered only for transparency. Without API keys the lab runs on a clearly labeled synthetic series, so "
    "every control here works immediately.":
        "기본 모형은 GARCH(1,1)-t라서 변동성이 몰려 나타나는 현상과 두꺼운 꼬리가 처음부터 반영됩니다. "
        "드리프트(추세 가정)는 기본적으로 위험프리미엄 방식(무위험 금리 + ERP에서 모형별 볼록성 보정을 뺌)을 "
        "씁니다. 표본 외 검증에서 과거 평균 수익률은 1년 앞을 예측하지 못했기 때문에, 표본 평균 방식은 비교용으로만 "
        "둡니다. API 키가 없으면 합성 데이터임을 분명히 표시하고 계산하므로 모든 기능을 바로 써 볼 수 있습니다.",
    "Median terminal": "만기 가격 중앙값",
    "90% range": "90% 범위",
    "P(loss)": "손실 확률",
    "CVaR": "CVaR (꼬리 평균 손실)",
    "Drift (ann.)": "연 드리프트",
    "Next-session vol (ann.)": "다음 거래일 변동성 (연율)",
    "Sample vol (ann.)": "표본 변동성 (연율)",
    "Next-session conditional forecast volatility, annualized using 252 sessions.":
        "다음 거래일의 조건부 예측 변동성을 연 252거래일로 연율화한 값입니다.",
    "Historical log-return sample volatility, annualized using 252 sessions.":
        "과거 로그수익률의 표본 변동성을 연 252거래일로 연율화한 값입니다.",
    "P(terminal ≥ target)": "만기 가격 ≥ 목표 가격 확률",
    "Validation record": "검증 기록",
    "Fit window: the last 504 daily closes (the history default); descriptive, not an R-16 graded fit. The graded "
    "lab line is the expanding-window grading (docs/quant_lab), shown below when stored.":
        "보정 구간: 최근 504개 일별 종가(기본값). 설명용 적합이며 R-16 등급 평가를 거친 적합이 아닙니다. "
        "등급 평가는 확장 구간 방식(docs/quant_lab)이며, 저장된 결과가 있으면 아래에 표시합니다.",
    "SMOKE · vendor data, not an official close, not a card run · gates nothing":
        "SMOKE · 공식 종가가 아닌 데이터 제공업체 자료, 카드 실행 아님 · 어떤 관문 판정에도 쓰이지 않음",
    "Grading report details": "검증 보고서 세부 내용",
    "GARCH fit": "GARCH 적합 결과",
    "GARCH alpha": "GARCH 알파 (충격 반응)",
    "GARCH beta": "GARCH 베타 (변동성 기억)",
    "GARCH alpha+beta": "GARCH 알파+베타 (지속성)",
    "95% Wald interval from the observed information (B2)": "관측 정보행렬로 구한 95% Wald 신뢰구간 (B2)",
    "95% Wald interval from the observed information (B2), delta method":
        "관측 정보행렬로 구한 95% Wald 신뢰구간 (B2), 델타 방법",
    "Half-life (sessions)": "반감기 (거래일)",
    "the persistence interval mapped through the half-life": "지속성 신뢰구간을 반감기로 환산한 범위",
    "nu (tail)": "nu (꼬리 두께)",
    "Uncond vol (ann.)": "장기 평균 변동성 (연율)",
    "no interval: the delta method covers 42% to 100% depending on persistence (B2)":
        "신뢰구간 없음: 델타 방법의 포함률이 지속성에 따라 42%~100%로 달라집니다 (B2)",
    "Horizon-average vol (ann.)": "기간 평균 변동성 (연율)",
    "Annualized forecast RMS across the simulated horizon; 252 sessions/year, using the engine innovation "
    "convention.":
        "모의실험 기간 전체의 예측 변동성 제곱평균제곱근을 연율화한 값입니다 (연 252거래일, 엔진의 충격 분포 기준).",
    "LR t vs normal": "우도비 검정 (t 대 정규)",
    "dAIC vs GBM": "AIC 차이 (GBM 대비)",
    "GARCH guardrails clear": "GARCH 안전장치 모두 정상",
    "SE undefined": "표준오차 계산 불가",
    "normal innovations": "정규분포 충격",
    "the t fit found no heavier tail than the normal (eta = 1/nu at 0)":
        "t 분포 적합에서 정규분포보다 두꺼운 꼬리가 발견되지 않았습니다 (eta = 1/nu = 0)",
    "persistence interval reaches 1": "지속성 신뢰구간이 1에 닿음",
    "95% profile-likelihood interval: cut 1.92 inside, 1.35 at the normal (the boundary null of the LR tile); "
    "'normal' means the interval includes eta = 0":
        "95% 프로파일 우도 신뢰구간: 내부 기준 1.92, 정규분포 경계 기준 1.35 (LR 타일의 경계 귀무가설). "
        "'정규분포'는 구간에 eta = 0이 포함된다는 뜻입니다",
    "95% profile-likelihood interval: cut 1.92 inside, 1.35 at the normal (the boundary null of the LR tile); "
    "'normal' means the interval includes eta = 0; greyed: alpha at its bound, the reference distribution is "
    "indicative only":
        "95% 프로파일 우도 신뢰구간: 내부 기준 1.92, 정규분포 경계 기준 1.35 (LR 타일의 경계 귀무가설). "
        "'정규분포'는 구간에 eta = 0이 포함된다는 뜻입니다. 회색 표시: 알파가 경계값이라 기준 분포는 참고용입니다",
    "5% point of the boundary null (half delta-0, half chi-square(1)): 2.706":
        "경계 귀무가설(절반은 0의 점질량, 절반은 카이제곱(1))의 5% 임계값: 2.706",
    "5% point of the boundary null (half delta-0, half chi-square(1)): 2.706; greyed: alpha at its bound, "
    "reference distribution indicative only":
        "경계 귀무가설(절반은 0의 점질량, 절반은 카이제곱(1))의 5% 임계값: 2.706. 회색 표시: 알파가 경계값이라 "
        "기준 분포는 참고용입니다",
    "the information matrix is not positive definite at the optimum": "최적점에서 정보행렬이 양의 정부호가 아닙니다",
    "the Hessian is not finite at the optimum": "최적점에서 헤시안 행렬이 유한하지 않습니다",
    "a finite-difference step leaves the domain (stationarity cap or a bound)":
        "유한차분 계산 단계가 허용 범위(정상성 상한 또는 경계)를 벗어납니다",
    "a 95% interval crosses a guardrail (0 or the cap for alpha and beta, nu = 2.5); a symmetric interval there "
    "is indicative only":
        "95% 신뢰구간이 안전장치 경계(알파·베타의 0 또는 상한, nu = 2.5)를 넘습니다. 그 근처의 대칭 구간은 참고용입니다",
    "an integrated variance is not excluded at 95%: the sample cannot pin down where vol settles":
        "95% 수준에서 적분형 분산을 배제할 수 없습니다. 이 표본으로는 변동성이 결국 어디에 자리 잡을지 정할 수 없습니다",

    # ------------------------------------------------------------------ Settings (설정)
    "Credential presence only. No key is ever displayed here.":
        "API 키가 설정되어 있는지만 보여 줍니다. 키 값은 이 화면에 절대 표시하지 않습니다.",
    "Quant analysis providers": "분석용 데이터 제공자",
    "FICC data providers": "금리·채권·외환(FICC) 데이터 제공자",
    "Korean market providers": "국내 시장 데이터 제공자",
    "Crypto providers": "가상자산 데이터 제공자",
    "configured": "설정됨",
    "not set": "미설정",
    "Claude API (deep analysis)": "Claude API (심층 분석)",
    "GS Marquee (gs_quant session)": "GS Marquee (gs_quant 세션)",
    "FRED (St. Louis Fed)": "FRED (세인트루이스 연준)",
    "KRX Data marketplace": "KRX 데이터 마켓플레이스",
    "Upbit (public candles)": "업비트 (공개 캔들)",
    "Binance (public klines, funding)": "바이낸스 (공개 캔들·펀딩비)",
    "Upbit account (자산조회 only)": "업비트 계정 (자산조회 권한만)",
    "dividend-adjusted US end-of-day prices": "배당을 반영한 미국 주식 일별 종가",
    "Optional. Offline gs_quant analytics work without it.": "선택 사항입니다. 없어도 gs_quant 오프라인 분석은 동작합니다.",
    "Keyless. Treasury curve, SOFR, OECD short rates, credit OAS, macro.":
        "키 불필요. 미국 국채 금리 곡선, SOFR, OECD 단기 금리, 신용 스프레드(OAS), 거시 지표.",
    "Keyless. FX spot, futures and index levels.": "키 불필요. 환율 현물, 선물, 지수 수준.",
    "Read-only quotes, OHLCV and index levels for KOSPI/KOSDAQ.":
        "코스피·코스닥 시세, 일별 시가·고가·저가·종가·거래량, 지수 수준 (조회 전용).",
    "Corporate filings and reported financials. Free key.": "기업 공시와 재무제표. 무료 키.",
    "Whole-market session snapshots. The keyless CSV export now returns HTTP 403, so the free Open API key is "
    "required.":
        "시장 전체 거래일 스냅샷. 키 없이 받던 CSV 내보내기가 이제 HTTP 403을 돌려주므로 무료 Open API 키가 필요합니다.",
    "Keyless. KRW-BTC daily since 2017-09-25; FIU-registered venue.":
        "키 불필요. 2017-09-25부터의 KRW-BTC 일별 자료, 금융정보분석원(FIU) 신고 거래소.",
    "Keyless data only; no account is ever assumed. Hosts may be blocked in Korea: test below.":
        "키 없는 공개 데이터만 씁니다. 계정은 가정하지 않습니다. 국내에서는 접속이 막힐 수 있으니 아래에서 확인하세요.",
    "Issue the key with 자산조회 scope only, allow-list this IP; keys expire after one year. QUANTGEN never "
    "implements an order path.":
        "키는 자산조회 권한만으로 발급하고 이 IP를 허용 목록에 넣으세요. 키는 1년 뒤 만료됩니다. QUANTGEN에는 "
        "주문 기능이 없습니다.",
    "fred.stlouisfed.org (no key needed)": "fred.stlouisfed.org (키 불필요)",
    "finance.yahoo.com (no key needed)": "finance.yahoo.com (키 불필요)",
    "docs.upbit.com (no key needed)": "docs.upbit.com (키 불필요)",
    "developers.binance.com (no key needed)": "developers.binance.com (키 불필요)",
    "upbit.com → Open API 관리 (자산조회 only)": "upbit.com → Open API 관리 (자산조회 권한만)",
    "not installed": "미설치",
    "offline analytics active": "오프라인 분석 사용 가능",
    "offline analytics unavailable": "오프라인 분석 사용 불가",
    "Marquee session active": "Marquee 세션 연결됨",
    "Marquee session off": "Marquee 세션 꺼짐",
    "gs-quant is not installed (pip install gs-quant).": "gs-quant가 설치되어 있지 않습니다 (pip install gs-quant).",
    "Offline analytics active. Set GS_CLIENT_ID and GS_CLIENT_SECRET to enable Marquee pricing.":
        "오프라인 분석을 쓸 수 있습니다. Marquee 가격 조회를 쓰려면 GS_CLIENT_ID와 GS_CLIENT_SECRET을 설정하세요.",
    "Credentials present; session not opened yet.": "인증 정보는 있지만 아직 세션을 열지 않았습니다.",
    "Marquee session active.": "Marquee 세션이 연결되어 있습니다.",
    "The Rates, Bonds, FX, Macro and Structuring pages read the Treasury curve, SOFR, credit spreads and FX "
    "fixings from FRED and Yahoo Finance. Both are keyless; fetches are cached on disk for a few hours.":
        "금리·채권·외환·매크로·구조화 상품 화면은 미국 국채 금리 곡선, SOFR, 신용 스프레드, 환율 고시값을 FRED와 "
        "야후 파이낸스에서 읽습니다. 둘 다 키가 필요 없으며, 받아 온 자료는 몇 시간 동안 디스크에 저장해 다시 씁니다.",
    "Test FICC data access": "FICC 데이터 연결 확인",
    "contacting FRED and Yahoo…": "FRED와 야후에 연결하는 중…",
    "KRX closed its keyless CSV export; a free KRX_API_KEY is now required for whole-market snapshots. KIS and "
    "OpenDART registration is also free.":
        "KRX가 키 없이 쓰던 CSV 내보내기를 닫았습니다. 시장 전체 스냅샷에는 이제 무료 KRX_API_KEY가 필요합니다. "
        "KIS와 OpenDART 등록도 무료입니다.",
    "Test KRX access": "KRX 연결 확인",
    "contacting KRX…": "KRX에 연결하는 중…",
    "reachable": "연결됨",
    "unavailable": "연결 안 됨",
    "The same KIS key serves ETF NAV, KOSPI200 / KTB / USD futures, the option board, overseas stocks, KRW "
    "benchmark yields and exchange-traded bonds — quotations only, no derivatives account needed (probed "
    "2026-09-25). CME ES/NQ/ZN/6E/GC/CL history answers HTTP 500 on a stock-account key.":
        "같은 KIS 키로 ETF 순자산가치(NAV), 코스피200·국채·달러 선물, 옵션 시세판, 해외 주식, 원화 지표 금리, "
        "장내 채권 시세를 조회할 수 있습니다. 시세 조회 전용이며 파생상품 계좌는 필요 없습니다 (2026-09-25 확인). "
        "CME ES/NQ/ZN/6E/GC/CL 과거 시세는 주식 계좌 키로는 HTTP 500을 돌려줍니다.",
    "Test KIS asset domains": "KIS 자산군별 연결 확인",
    "one read-only call per KIS asset domain…": "KIS 자산군마다 조회 요청을 한 번씩 보내는 중…",
    "Upbit and Binance public data are keyless. An Upbit key is optional and must be issued with 자산조회 "
    "(balance) scope only; QUANTGEN never submits orders, withdrawals or transfers and never holds a wallet key.":
        "업비트와 바이낸스 공개 데이터는 키가 필요 없습니다. 업비트 키는 선택 사항이며 자산조회 권한만으로 발급해야 "
        "합니다. QUANTGEN은 주문·출금·이체를 하지 않으며 지갑 키도 보관하지 않습니다.",
    "Test crypto data access": "가상자산 데이터 연결 확인",
    "contacting Upbit and Binance…": "업비트와 바이낸스에 연결하는 중…",
    "Environment template": "환경 변수 템플릿 (.env)",
    "QUANTGEN reads these from this machine only.": "QUANTGEN은 이 값들을 이 컴퓨터에서만 읽습니다.",

    # ------------------------------------------------------------------ Execution (모의투자)
    "Execution": "모의투자 실행",
    "Simulated order flow from rules you wrote.": "직접 작성한 규칙에서 나온 모의 주문 흐름입니다.",
    "Evaluate now": "지금 평가",
    "Run one pass immediately instead of waiting for the next interval.":
        "다음 주기를 기다리지 않고 지금 한 번 평가합니다.",
    "Refresh this view": "화면 새로고침",
    "Acknowledge halt": "정지 확인",
    "Disarm": "작동 해제",
    "Arm": "작동 시작",
    "Stops new orders immediately and keeps open ones.": "새 주문을 즉시 막고, 이미 있는 미체결 주문은 그대로 둡니다.",
    "Nothing is running to stop.": "멈출 작업이 없습니다.",
    "This program never re-arms itself. Acknowledge the halt, check the cause, then arm again when you are ready.":
        "이 프로그램은 스스로 다시 작동하지 않습니다. 정지를 확인하고 원인을 점검한 뒤, 준비되면 다시 작동을 시작하세요.",
    "No rule is being evaluated and no market request is being made.":
        "평가 중인 규칙이 없고, 시세 요청도 보내지 않습니다.",
    "Active rules": "활성 규칙",
    "Fired today": "오늘 실행",
    "Rejected today": "오늘 거부",
    "Committed today": "오늘 주문 금액",
    "blocked by your caps": "설정한 한도에 막힘",
    "Venues": "거래소",
    "Rules on a closed venue are skipped, not stopped. They resume when the market opens.":
        "휴장 중인 거래소의 규칙은 멈추지 않고 건너뜁니다. 장이 열리면 다시 평가합니다.",
    "Open simulated orders": "모의 미체결 주문",
    "Nothing outstanding. Orders placed by a rule rest here until you fill or cancel them.":
        "미체결 주문이 없습니다. 규칙이 낸 주문은 직접 체결하거나 취소할 때까지 여기에 남습니다.",
    "These do not fill by themselves — that is the decision you are practising.":
        "이 주문들은 저절로 체결되지 않습니다. 체결할지 정하는 것이 바로 연습하는 판단입니다.",
    "Fill": "체결",
    "Cancel": "취소",
    "Decision log": "판단 기록",
    "Empty. Every evaluation appears here — including the ones that did nothing, with the reason.":
        "아직 비어 있습니다. 아무 일도 하지 않은 평가까지 모든 평가가 이유와 함께 여기에 표시됩니다.",
    "newest first": "최신순",
    "No rules yet": "아직 규칙이 없습니다",
    "The engine executes rules you write. Nothing here is suggested for you — every condition, size and limit is "
    "yours.":
        "엔진은 직접 작성한 규칙만 실행합니다. 이 화면은 아무것도 추천하지 않으며, 조건·수량·한도는 모두 직접 정합니다.",
    "Write a rule": "규칙 작성",
    "Open rules": "규칙 열기",
    "Fired": "실행됨",
    "Rejected": "거부됨",
    "Skipped": "건너뜀",
    "Halted": "정지됨",
    "Blocked": "차단됨",
    "Disarmed. No rule will be evaluated.": "작동을 해제했습니다. 규칙을 평가하지 않습니다.",
    "Emergency stop. Open orders are kept; new orders are blocked.":
        "긴급 정지했습니다. 미체결 주문은 남기고 새 주문은 막습니다.",
    "Halt acknowledged. The engine is disarmed — arm it when ready.":
        "정지를 확인했습니다. 엔진은 해제 상태이며, 준비되면 작동을 시작하세요.",
    "Nothing to evaluate.": "평가할 것이 없습니다.",
    "Cancelled.": "취소했습니다.",
    "Armed.": "작동을 시작했습니다.",
    "Already armed.": "이미 작동 중입니다.",
    "No such order.": "해당 주문이 없습니다.",

    # ------------------------------------------------------------------ Rules (규칙)
    "Your conditions. The program adds none.": "조건은 모두 직접 정합니다. 프로그램은 아무것도 덧붙이지 않습니다.",
    "New rule": "새 규칙",
    "Edit rule": "규칙 수정",
    "A rule says: when this price condition holds, place this order at this size, within these limits. Every part "
    "of that is yours to write.":
        "규칙은 '이 가격 조건이 맞으면, 이 수량으로, 이 한도 안에서 이 주문을 낸다'는 문장입니다. 모든 부분을 직접 "
        "작성합니다.",
    "Write your first rule": "첫 규칙 작성",
    "Draft": "초안",
    "Confirmed": "확인됨",
    "Active": "활성",
    "Paused": "일시 중지됨",
    "Exhausted": "한도 소진",
    "Expired": "기간 만료",
    "Cancelled": "취소됨",
    "Review & confirm": "검토 후 확인",
    "Fix the errors first": "먼저 오류를 고치세요",
    "Read the summary and confirm": "요약을 읽고 확인하세요",
    "Activate": "활성화",
    "Pause": "일시 중지",
    "Resume": "다시 시작",
    "Edit": "수정",
    "Delete": "삭제",
    "(unnamed)": "(이름 없음)",
    "Delete this rule?": "이 규칙을 삭제할까요?",
    "Keep it": "유지",
    "Confirmed. Activate it when you want the engine to watch it.":
        "확인했습니다. 엔진이 이 규칙을 감시하게 하려면 활성화하세요.",
    "Active. It will be evaluated while the engine is armed.": "활성화했습니다. 엔진이 작동하는 동안 평가합니다.",
    "Paused.": "일시 중지했습니다.",
    "Active again.": "다시 활성화했습니다.",
    "Confirmed. Activate it on the list when you are ready.": "확인했습니다. 준비되면 목록에서 활성화하세요.",
    "Every field is blank until you fill it.": "모든 항목은 직접 채우기 전까지 비어 있습니다.",
    "This rule is already confirmed. Changing a condition, size or limit returns it to draft and you will confirm "
    "it again.":
        "이미 확인한 규칙입니다. 조건·수량·한도를 바꾸면 초안으로 돌아가며 다시 확인해야 합니다.",
    "What and where": "무엇을, 어디서",
    "The instrument this rule watches.": "이 규칙이 감시할 종목입니다.",
    "Rule name": "규칙 이름",
    "How you will recognise it": "나중에 알아볼 수 있는 이름",
    "Instrument code": "종목 코드",
    "choose a market first": "먼저 시장을 고르세요",
    "Market": "시장",
    "Your FMP plan returns HTTP 402 for this venue. The rule can be saved, but the engine cannot quote it until the "
    "plan covers international exchanges.":
        "현재 FMP 요금제는 이 거래소에 HTTP 402를 돌려줍니다. 규칙은 저장할 수 있지만, 요금제가 해외 거래소를 포함하기 "
        "전까지 엔진이 시세를 받을 수 없습니다.",
    "When it fires": "언제 실행할지",
    "Conditions are compared against the last traded price.": "조건은 마지막 체결 가격과 비교합니다.",
    "Conditions must": "조건 결합 방식",
    "All be true (AND)": "모두 충족 (AND)",
    "Any be true (OR)": "하나라도 충족 (OR)",
    "Last price": "현재가가",
    "is at or below": "이하일 때",
    "is at or above": "이상일 때",
    "crosses down through": "아래로 뚫고 내려갈 때",
    "crosses up through": "위로 뚫고 올라갈 때",
    "price": "가격",
    "Remove": "삭제",
    "Add condition": "조건 추가",
    "What it does": "무엇을 할지",
    "The order placed when the conditions hold.": "조건이 맞을 때 낼 주문입니다.",
    "Direction": "방향",
    "Buy": "매수",
    "Sell": "매도",
    "Size is a": "수량 기준",
    "Share count": "주식 수",
    "Cash amount": "금액",
    "Size": "수량·금액",
    "Order type": "주문 유형",
    "Market order": "시장가 주문",
    "Limit order": "지정가 주문",
    "Limit price": "지정가",
    "Only for a limit order": "지정가 주문일 때만 입력",
    "Limits": "한도",
    "Ceilings this rule may never cross. Leave blank for none — blank means no ceiling, not a safe default.":
        "이 규칙이 절대 넘지 않을 상한입니다. 비워 두면 상한이 없다는 뜻이며, 안전한 기본값이 아닙니다.",
    "Max times this rule may fire": "최대 실행 횟수",
    "Max amount per order": "주문당 최대 금액",
    "Max amount per day": "하루 최대 금액",
    "Cancel unfilled order after (s)": "미체결 주문 자동 취소 (초)",
    "In plain language": "쉬운 말로 다시 읽기",
    "Discard": "버리기",
    "Save draft": "초안 저장",
    "Fix the highlighted fields first": "표시된 항목을 먼저 고치세요",
    "Read the sentence above, then confirm": "위 문장을 읽고 확인하세요",
    "Is this what you meant?": "의도한 내용이 맞나요?",
    "Confirming does not arm it. You activate the rule on the list, and the engine only acts while armed.":
        "확인해도 바로 작동하지 않습니다. 목록에서 규칙을 활성화해야 하며, 엔진은 작동 중일 때만 움직입니다.",
    "Keep editing": "계속 수정",
    "Confirm": "확인",
    "Give the rule a name so you can find it later.": "나중에 찾을 수 있도록 규칙 이름을 정하세요.",
    "Enter the instrument code this rule applies to.": "이 규칙을 적용할 종목 코드를 입력하세요.",
    "Choose the market so quotes resolve to the right provider.": "올바른 시세 제공자로 연결되도록 시장을 고르세요.",
    "Choose buy or sell.": "매수 또는 매도를 고르세요.",
    "Choose whether the size is a share count or a cash amount.": "수량을 주식 수로 할지 금액으로 할지 고르세요.",
    "Enter the size. This program does not choose one for you.": "수량을 입력하세요. 이 프로그램은 수량을 대신 정하지 않습니다.",
    "Size must be greater than zero.": "수량은 0보다 커야 합니다.",
    "A share count must be a whole number.": "주식 수는 정수여야 합니다.",
    "Choose market or limit.": "시장가 또는 지정가를 고르세요.",
    "A limit order needs a limit price.": "지정가 주문에는 지정가가 필요합니다.",
    "Limit price must be greater than zero.": "지정가는 0보다 커야 합니다.",
    "Limit price is ignored for a market order.": "시장가 주문에서는 지정가를 쓰지 않습니다.",
    "Add at least one trigger condition.": "실행 조건을 하나 이상 추가하세요.",
    "Condition price must be greater than zero.": "조건 가격은 0보다 커야 합니다.",
    "The end of the window must come after its start.": "유효 기간의 끝은 시작보다 뒤여야 합니다.",
    "This window has already closed, so the rule cannot fire.": "유효 기간이 이미 끝나 이 규칙은 실행될 수 없습니다.",
    "No validity window: this rule stays live until you stop it.": "유효 기간 없음: 직접 멈출 때까지 이 규칙은 계속 살아 있습니다.",
    "Maximum trigger count must be at least one.": "최대 실행 횟수는 1 이상이어야 합니다.",
    "Maximum order amount must be greater than zero.": "주문당 최대 금액은 0보다 커야 합니다.",
    "Maximum daily amount must be greater than zero.": "하루 최대 금액은 0보다 커야 합니다.",
    "The daily cap is below the per-order cap, so no order can pass both.":
        "하루 한도가 주문당 한도보다 작아서 어떤 주문도 두 한도를 모두 통과할 수 없습니다.",
    "No caps set: this rule has no ceiling on how much it can order.": "한도 없음: 이 규칙이 주문할 수 있는 금액에 상한이 없습니다.",
    "The order amount is above this rule's own maximum order amount.": "주문 금액이 이 규칙의 주문당 최대 금액보다 큽니다.",
    "Cancel delay must be greater than zero seconds.": "자동 취소 대기 시간은 0초보다 커야 합니다.",
    "KRX — KOSPI / KOSDAQ": "한국거래소 — 코스피 / 코스닥",
    "United States — NASDAQ / NYSE / AMEX": "미국 — 나스닥 / 뉴욕 / 아멕스",
    "United Kingdom — London": "영국 — 런던",
    "Germany — XETRA": "독일 — XETRA",
    "France — Euronext Paris": "프랑스 — 유로넥스트 파리",
    "Netherlands — Euronext Amsterdam": "네덜란드 — 유로넥스트 암스테르담",
    "Italy — Borsa Italiana": "이탈리아 — 이탈리아 증권거래소",
    "Spain — BME Madrid": "스페인 — BME 마드리드",
    "Switzerland — SIX Swiss": "스위스 — SIX 스위스 거래소",
    "Sweden — Nasdaq Stockholm": "스웨덴 — 나스닥 스톡홀름",
    "Norway — Oslo Børs": "노르웨이 — 오슬로 증권거래소",
    "Japan — Tokyo": "일본 — 도쿄",
    "Hong Kong": "홍콩",
    "China — Shanghai": "중국 — 상하이",
    "China — Shenzhen": "중국 — 선전",
    "Taiwan": "대만",
    "Singapore": "싱가포르",
    "India — NSE": "인도 — NSE",
    "Australia": "호주",
    "Canada — Toronto": "캐나다 — 토론토",
    "Brazil — B3": "브라질 — B3",
    "Mexico": "멕시코",

    # ------------------------------------------------------------------ Research home / library / system
    "Weekly": "주간",
    "Monthly": "월간",
    "Month-end": "월말",
    "Event-driven": "발표 시점마다",
}
