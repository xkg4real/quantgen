"""Display-only English/Korean vocabulary. Model IDs and report data stay canonical.

Entries match complete labels or explicit templates; no machine translation,
substring replacement of user input, or network calls are used.
"""
import re
from string import Formatter

_PAIRS = r'''
Best score|최고 점수
Highest carry|최고 캐리
Basket return|바스켓 수익률
Equal-weight long return|동일 비중 매수 수익률
Carry ranking|캐리 순위
CCY|통화
USD rate|USD 금리
Carry|캐리
3m vol|3개월 변동성
Carry/vol|캐리/변동성
3m momentum|3개월 모멘텀
Rate date|금리 관측일
Stale|오래된 관측 여부
Carry equity|캐리바스켓 누적 가치
Basket|바스켓
Equal-weight long|동일 비중 매수
Equity · starts at 1|누적 가치 · 시작값 1
Language|언어
Research Home|연구 홈
Markets|시장
Build & Test|설계 및 검증
Portfolio & Risk|포트폴리오 및 위험
Research Library|연구 보관함
System|시스템
PERSONAL RESEARCH|개인 연구
Native desktop preview\nFlet browser is retained|네이티브 데스크톱 미리보기\nFlet 브라우저 유지
Light · A|라이트 · A
Dark|다크
Tool|도구
Data source|데이터 출처
Source|출처
Model|모델
Symbol|종목 코드
Symbols · comma separated|종목 코드 · 쉼표로 구분
Symbols · pairs: y, x order|Symbols · pairs는 y, x 순서
Drift|추세 가정
Horizon · sessions|분석 기간 · 거래일
Paths|시뮬레이션 경로 수
Seed|난수 시드
Target price|목표 가격
Optional|선택 입력
Run analysis|분석 실행
Save analysis JSON|분석 JSON 저장
Save report ZIP|보고서 ZIP 저장
Save analysis results|분석 결과 저장
Choose a tool and source, then run.|도구와 출처를 선택한 후 실행하세요.
Tool changed. Run again.|도구가 변경됐습니다. 다시 실행하세요.
Input error · Check numbers, units, maturities and the selected tool's constraints.|입력 오류 · 숫자, 단위, 만기 및 선택한 도구의 조건을 확인하세요.
Calculation complete · Check sources, observation dates and assumptions. Official validation is separate.|계산 완료 · 출처·관측일·가정을 확인하세요. 공식 검증 판정은 별도입니다.
Calculating… Work continues when you switch pages.|계산 중… 화면을 이동해도 계속됩니다.
Save complete · {name}|저장 완료 · {name}
Save failed · {error} · Check the path and extension.|저장 실패 · {error} · 경로와 확장자를 확인하세요.
Save failed: {error} · Check the path and extension.|저장 실패: {error} · 경로와 확장자를 확인하세요.
Analysis report saved · official validation NOT_RUN|분석 보고서 저장 완료 · 공식 검증 NOT_RUN
Market observations and your research in one place.|관측된 시장과 내가 실행한 연구를 한눈에 확인하세요.
Completed analyses|완료한 분석
In progress|진행 중
Runs to review|확인할 실행
This session's Monte Carlo · separate from investment validation|이번 세션의 Monte Carlo · 투자 판정과 별개
Key market indicators|주요 시장지표
Indicator|지표
Observed value|관측값
Change|변화
Status · observation date|상태 · 관측일
Daily observations · not real time. Unavailable and stale observations are distinguished.|일별 관측 · 실시간 아님 · 조회 실패와 오래된 관측은 구분합니다.
Explore a range of outcomes|가능성을 하나의 숫자로 좁히지 마세요
Run an analysis to connect results with their data evidence.|분석을 실행하면 최신 결과와 데이터 근거가 연결됩니다.
Start research in Quant Lab →|Quant Lab에서 연구 시작 →
P5–P95 is the central 90% of the simulated distribution, not a return guarantee or a 95% confidence interval.|P5–P95는 시뮬레이션 분포의 중앙 90% 구간입니다. 수익 보장이나 95% 신뢰구간이 아닙니다.
Daily market data with providers and observation dates|공급자와 관측일을 함께 확인하는 일별 시장 데이터
Refresh market indicators|시장지표 새로고침
Value|값
Unit|단위
Change from previous|직전 대비
Provider|공급자
Observation date|관측일
Status|상태
USD rate changes are in bp; others are percentages from the previous observation. Data rights and vintages are unverified.|USD 금리는 변화량을 bp로 표시합니다. 나머지는 직전 관측 대비 %입니다. 데이터 권리와 빈티지는 미검증입니다.
Quant Lab · price distributions using the existing engine|Quant Lab · 기존 계산 엔진으로 가격 분포 분석
Analysis settings|분석 설정
Run distribution analysis|분포 분석 실행
Data sources, seeds and model assumptions are recorded.|데이터 출처·시드·모델 가정을 기록합니다.
Distribution and evidence|분포와 근거
No analysis has run yet.|아직 실행한 분석이 없습니다.
Calculation complete ≠ investment validation. This view keeps verdict NOT_RUN and creates no orders or strategy ledger entries.|계산 완료 ≠ 투자 검증. 이 화면은 NOT_RUN 판정을 유지하며 주문이나 전략 원장을 생성하지 않습니다.
Review distribution risk for this session's analyses.|현재 세션 분석의 분포 위험을 확인하세요.
Individual price simulation risk|개별 가격 시뮬레이션 위험
Each row is an individual price simulation, not portfolio-wide risk or a strategy backtest.|각 행은 개별 가격 시뮬레이션입니다. 포트폴리오 전체 위험이나 전략 백테스트가 아닙니다.
This session's evidence · save needed results before closing.|이번 앱 세션의 실행 근거 · 종료 전에 필요한 결과를 저장하세요.
Execution status|실행 상태
Validation verdict|검증 판정
Created · UTC|생성 시각 · UTC
Save selected ResearchRun JSON|선택한 ResearchRun JSON 저장
Save selected report + JSON ZIP|선택한 보고서 + JSON ZIP 저장
Saving currently covers Monte Carlo runs. Select the destination explicitly; there is no autosave.|현재 저장 대상은 Monte Carlo 실행입니다. 자동 저장되지 않으며 경로는 직접 선택합니다.
Reproducibility PARTIAL · data vintage/rights unverified · costs NOT_APPLIED · validation NOT_RUN\nFrozen studies, past ledgers and secret settings are not inspected.|재현성 PARTIAL · 데이터 빈티지/라이선스 미검증 · 비용 NOT_APPLIED · 검증 NOT_RUN\n동결 연구·과거 원장·비밀 설정을 탐색하지 않습니다.
Distinguish recorded evidence from this execution.|기록된 근거와 이번 실행 결과를 구분합니다.
Project status|프로젝트 상태
Recorded checks: {passed} PASS / {failed} FAIL / {not_run} NOT_RUN\nCalendar: {files} signed metadata files · set {version}\nThese are not checks run in this session. Per-file signature verification is separate.|기록된 검사: {passed} PASS / {failed} FAIL / {not_run} NOT_RUN\n달력: {files}개 서명 메타데이터 · 세트 {version}\n위 수치는 이번에 실행한 검사 결과가 아닙니다. 파일별 서명 검증은 별도입니다.
Recorded status could not be verified. Check the sources.|기록된 상태를 검증할 수 없습니다. 출처 자료를 확인하세요.
Data NOT_VERIFIED · formal gates NOT_FROZEN (documented)\nFrozen studies NOT_INSPECTED · public distribution NOT_APPROVED|데이터 NOT_VERIFIED · 공식 게이트 NOT_FROZEN (문서 기록)\n동결 연구 NOT_INSPECTED · 공개 배포 NOT_APPROVED
Desktop migration status|데스크톱 이전 상태
This desktop is an opt-in preview, not a completed migration of every feature.|이번 데스크톱은 선택 실행하는 미리보기입니다. 전체 기능 이전 완료본이 아닙니다.
Check inputs. A symbol and a finite positive target are required.|입력을 확인하세요. Symbol과 유한한 양수 Target이 필요합니다.
Analyzing… Work continues when you switch pages.|분석 중… 화면을 이동해도 계산은 계속됩니다.
FAILED · display validation error · {error}|FAILED · 표시 자료 검증 오류 · {error}
COMPLETED · validation NOT_RUN · reproducibility PARTIAL|COMPLETED · 검증 NOT_RUN · 재현성 PARTIAL
Market lookup failed: {code}|시장 조회 실패: {code}
FAILED · {code} · Check inputs/data.|FAILED · {code} · 입력/데이터를 확인하세요.
FAILED · {code} · Check price/yield and curve source.|FAILED · {code} · Price/Yield와 곡선 출처를 확인하세요.
FAILED · {code} · Check inputs, curve range and data source.|FAILED · {code} · 입력·곡선 범위·데이터 출처를 확인하세요.
FAILED · {code} · Check inputs or data connections.|FAILED · {code} · 입력 또는 데이터 연결을 확인하세요.
Optimizing… Work continues when you switch pages.|최적화 중… 화면을 이동해도 계속됩니다.
Calculating bonds…|채권 계산 중…
Market data|시장 데이터
Disconnected · refresh required|미연결 · 새로고침 필요
Observation {date} · verdict {verdict} · reproducibility {reproducibility}|관측 {date} · 판정 {verdict} · 재현성 {reproducibility}
Select a run to save first.|먼저 저장할 실행을 선택하세요.
Wait until the run finishes before saving.|실행이 끝난 뒤 저장하세요.
Save ResearchRun|ResearchRun 저장
Wait for running analyses or lookups before closing.|진행 중인 분석 또는 조회가 끝난 뒤 종료할 수 있습니다.
Close session|세션 종료
Unsaved session records will be lost. Close now?|저장하지 않은 세션 기록은 사라집니다. 종료할까요?
Wait for the paper engine's current lookup, then close again.|모의 엔진의 진행 중인 조회가 끝나면 다시 종료해 주세요.
Portfolio optimization|포트폴리오 최적화
Run portfolio analysis|포트폴리오 분석 실행
Align observations on common dates, then compare four objectives.|동일 관측일의 이력을 정렬한 후 네 가지 목적함수를 비교합니다.
The input cap applies only to the selected objective. Other objectives, the frontier and random cloud use a 100% per-asset cap.|선택한 목적에만 입력 상한이 적용됩니다. 나머지 목적·Frontier·무작위 구름의 종목당 상한은 100%입니다.
Annual return|연율 수익률
Annual volatility|연율 변동성
Convergence|수렴
Per-asset cap / scope|종목당 상한 / 범위
Correlation matrix|상관행렬
Historical-sample optimization, not a future return guarantee or official gate verdict. All results are long-only and fully invested; equal_weight fixes weights at 1/N.|과거 표본에 대한 최적화이며 미래 수익 보장이나 공식 게이트 판정이 아닙니다. 모든 결과는 롱온리·완전투자이며 equal_weight는 1/N 고정 비중입니다.
Enter 2–15 distinct symbols and valid weights/rates.|서로 다른 2–15개 심볼과 유효한 비중·금리를 입력하세요.
Calculation complete · solver converged={converged} · no official investment verdict|계산 완료 · solver converged={converged} · 공식 투자 판정 없음
Bonds|채권
Bonds · price, risk, scenarios and futures hedge|Bonds · 가격·위험·시나리오·선물 헤지
Enter either price or yield, not both. Clear yield when entering price.|가격과 수익률 중 하나만 입력하세요. Price를 입력할 때는 Yield를 비웁니다.
Run bond analysis|채권 분석 실행
Curve source and observation date are shown together.|곡선 출처와 관측일을 함께 표시합니다.
Input error · Enter finite values and valid maturity/amount; keep either price or yield.|입력 오류 · 유한한 수치와 유효한 만기·금액을 입력하고 Price/Yield 중 하나만 남기세요.
Synthetic curve · not current market data|합성 곡선 · 현재 시장 데이터 아님
Calculation complete · Review curve and bond assumptions.|계산 완료 · 곡선 및 채권 가정을 확인하세요.
Connections|연결
Data connections|데이터 연결
Check configuration · no network calls|설정 여부 확인 · 네트워크 조회 없음
Test KRX access|KRX 접속 검사
Test FRED / Yahoo access|FRED / Yahoo 접속 검사
Test KIS asset data access|KIS 자산 데이터 접속 검사
Test Upbit / Binance public data access|Upbit / Binance 공개 데이터 접속 검사
Use existing connection|기존 연결 사용
Check selected connection|선택한 연결 확인
Configuration and actual responses are distinct. Key values are never shown or saved.|설정 여부와 실제 응답을 구분합니다. 키 값은 표시하거나 저장하지 않습니다.
Connection status|연결 상태
Setting name / path|설정 이름 / 경로
Description|설명
AI commentary · optional|AI 해설 · 선택 기능
Request AI commentary|AI 해설 요청
Select a calculation and review its payload before requesting. Uses the existing Anthropic API connection.|계산 결과를 선택하고 전송 내용을 확인한 뒤 요청하세요. 기존 Anthropic API 연결을 사용합니다.
Refresh completed results|완료 결과 목록 갱신
Preview payload|전송 내용 미리보기
Send displayed calculation and question to the external AI service|표시한 계산 결과와 질문을 외부 AI 서비스로 전송
Rules · paper execution only|Rules · 모의 실행 전용
Enter rules, prices and quantities yourself. Save, confirm, activate and arm the engine are separate steps.|규칙·가격·수량은 직접 입력합니다. 저장 → 확인 → 활성화 → 엔진 Arm을 구분합니다.
Read rules|규칙 읽기
New rule|새 규칙
Edit selected|선택 편집
Activate/pause selected|선택 활성/일시정지
Delete selected|선택 삭제
Selected change history|선택 변경 이력
Name|이름
Instrument|종목
Market code|시장 코드
Side|방향
Size mode|수량 방식
Quantity / amount|수량/금액
Order type|주문 종류
Limit price|지정가
Start · ISO date + UTC offset|시작 · ISO 날짜+UTC offset
End · ISO date + UTC offset|종료 · ISO 날짜+UTC offset
Max triggers|최대 실행 횟수
Per-order limit|건별 한도
Daily limit|일별 한도
Cancel unfilled after · seconds|미체결 취소 초
Cancel price condition|취소 가격 조건
Cancel trigger price|취소 조건 가격
Notes|메모
All conditions required (uncheck for OR)|모든 조건 충족 (해제하면 OR)
Price conditions|가격 조건
Add condition|조건 추가
Remove selected condition|선택 조건 삭제
Review inputs|입력 확인
Save|저장
Review summary and confirm|요약 검토 후 확인
Select|선택
Paper Trading|모의매매
Paper Trading · no real orders|Paper Trading · 실제 주문 없음
Rules and paper records are not read until you explicitly open a session.|명시적으로 세션을 열기 전에는 규칙/모의 기록을 읽지 않습니다.
Open paper session|모의 세션 읽기
Emergency stop|긴급 정지
Stop paper engine|모의 엔진 긴급 정지
Acknowledge HALT|HALT 확인
Evaluate once|한 번 평가
Reset paper records|모의 기록 초기화
No session has been opened.|아직 세션을 읽지 않았습니다.
Fill selected paper order|선택 모의 체결
Cancel selected paper order|선택 모의 취소
Read records again|기록 새로 읽기
Records are read explicitly. Live execution requires existing signed-calendar and connection conditions.|기록은 명시적으로 읽습니다. Live 실행은 기존 서명 달력·연결 조건을 충족해야 합니다.
Read stored research cards|저장된 연구카드 읽기
Run strategy validation|전략 검증 실행
Real-data execution records a trial in the existing research ledger. Synthetic execution does not. Lab DSR currently uses this grid's trial count; cumulative ledger counts are separate work.|실데이터 실행은 기존 연구 원장에 시행을 기록합니다. 합성 실행은 기록하지 않습니다. 현재 Lab의 DSR 시행 수는 이번 그리드 수입니다. 누적 원장 기반 전환은 별도 작업입니다.
This tab is a descriptive macro sheet. Find v2 Overlay, Model cards and Research register in Markets → Macro v2.|이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 Markets의 Macro v2 탭에서 확인합니다.
FX · spot, forwards, options and carry|FX · 현물·선물환·옵션·캐리
Rates · yield curve and rate risk|Rates · 수익률 곡선과 금리 위험
Macro · market observations and local commentary|Macro · 시장 관측과 로컬 해설
Signals · technical observations and costed backtests|Signals · 기술적 관측과 비용 포함 백테스트
Structuring · product structure, maturity payoff and risk|Structuring · 상품 구조·만기 손익·위험
Run an analysis to see the P5–P95 distribution.|분석을 실행하면 P5–P95 분포가 표시됩니다.
Run an analysis to see the efficient frontier.|분석 후 효율적 프런티어가 표시됩니다.
Annual volatility → · Y: annual return (historical estimate)|연율 변동성 → · Y: 연율 수익률 (과거 표본 추정)
0 → {days} sessions · P5 / P25 / P50 / P75 / P95|0 → {days} 거래일 · P5 / P25 / P50 / P75 / P95
'''

_TERMS = r'''
Price|가격
Yield %|수익률 %
Volatility %|변동성 %
Objective|목적함수
Weight|비중
Risk contribution|위험 기여도
Portfolio|포트폴리오
Risk-free|무위험 금리
Max weight / asset|종목당 최대 비중
Auto|자동
Synthetic demo|합성 데이터 시연
Jump diffusion|점프 확산
Block bootstrap|블록 부트스트랩
Risk premium · rf + ERP|위험 프리미엄 · rf + ERP
Zero · stress|0 · 스트레스 가정
Risk-neutral · rf|위험중립 · rf
Sample mean · noisy|표본 평균 · 추정 오차 유의
Annual|연 1회
Semi-annual|반기
Quarterly|분기
Calculator & risk|계산 및 위험
Futures hedge|선물 헤지
Curve source|곡선 출처
Coupon %|표면금리 %
Maturity|만기
Maturity · years|만기 · 년
Coupons / year|연간 이자 지급 횟수
Coupons per year|연간 이자 지급 횟수
Price · per 100|가격 · 액면 100당
Notional|명목금액
Position DV01 · optional|포지션 DV01 · 선택 입력
Conversion factor|전환계수
New price|새 가격
Revalue|재평가
Scenarios|시나리오
Scenario|시나리오
Yield curve|수익률 곡선
Swap pricer|스왑 가격 계산
Swaption / cap-floor|스왑션 / 캡·플로어
Rate simulation|금리 시뮬레이션
Auto · FRED / synthetic fallback|자동 · FRED / 실패 시 합성 데이터
Auto · synthetic fallback|자동 · 실패 시 합성 데이터
Auto · KIS / FMP|자동 · KIS / FMP
Auto · Yahoo spot / FRED rates|자동 · Yahoo 현물 / FRED 금리
Method|방법
Instrument tenor|상품 만기
Tenor · 10y or 5y5y|기간 · 10y 또는 5y5y
Fixed % · blank = par|고정금리 % · 공란 = 파 금리
Pay fixed|고정금리 지급
Receive fixed|고정금리 수취
Expiry · swaption only|옵션 만기 · 스왑션만
Strike % · blank = ATM|행사가격 % · 공란 = ATM
Swaption side|스왑션 방향
Payer|고정금리 지급형
Receiver|고정금리 수취형
Bachelier · normal|Bachelier · 정규 모형
Normal volatility · bp|정규 변동성 · bp
Horizon · years|분석 기간 · 년
Simulation paths|시뮬레이션 경로 수
Threshold % · optional|임계값 % · 선택 입력
Kind|종류
Instrument|상품
Underlying tenor|기초자산 만기
Spot, forward & carry|현물·선물환·캐리
Option & smile|옵션 및 스마일
Carry basket|캐리 바스켓
Yahoo spot|Yahoo 현물
Pair · base/quote|통화쌍 · 기준/상대 통화
Quote/domestic rate % · blank = provider|상대/국내 금리 % · 공란 = 공급자
Base/foreign rate % · blank = provider|기준/외국 금리 % · 공란 = 공급자
Tenor|기간
Market forward · optional|시장 선물환 · 선택 입력
Expiry|옵션 만기
Strike · ATM / 25d / level|행사가격 · ATM / 25d / 직접 입력
Call|콜
Put|풋
ATM volatility %|ATM 변동성 %
25d risk reversal · vol points|25델타 리스크 리버설 · 변동성 포인트
25d butterfly · vol points|25델타 버터플라이 · 변동성 포인트
Top/bottom N · core caps at half universe|상위/하위 N · 최대 종목 수의 절반
Cost · bp per side|편도 비용 · bp
Rebalance · sessions|리밸런싱 · 거래일
History · observations|이력 · 관측 수
Principal-protected note|원금보장형 노트
Reverse convertible|역전환형 노트
Dual-currency deposit|이중통화 예금
CMS steepener|CMS 스티프너
Issue price · per 100|발행 가격 · 액면 100당
Protection %|보장 비율 %
Leverage · ×|레버리지 · 배
Strike % of spot|현물 대비 행사가격 %
Foreign rate / dividend %|외국 금리 / 배당수익률 %
Futures DV01 / contract · optional|선물 계약당 DV01 · 선택 입력
Spot|현물 가격
Coupon % · blank = solve|쿠폰 % · 공란 = 역산
Base currency|기준 통화
Quote currency|상대 통화
Base currency rate %|기준 통화 금리 %
Floor %|하한 %
Cap % · blank = none|상한 % · 공란 = 없음
Margin · per 100|마진 · 액면 100당
KOSPI200 board|KOSPI200 시세표
Options, futures & hedge P&L|옵션·선물·헤지 손익
Expiry · blank = nearest|만기 · 공란 = 최근 만기
Rate % · blank = provider|금리 % · 공란 = 공급자
Horizon sessions · blank = expiry|기간 거래일 · 공란 = 만기
Paths · 100–100000|경로 수 · 100–100000
Hedge engine|헤지 모형
ETF structure|ETF 구조
NAV, basket & sleeve rules|순자산가치·구성종목·전략 규칙
ETF code|ETF 코드
Sessions|거래일
Crypto research|가상자산 연구
Premium, funding & volatility|프리미엄·펀딩·변동성
Live providers only · no fallback|실제 공급자만 · 대체 데이터 없음
Upbit account read|Upbit 계좌 조회
Off · public data only|꺼짐 · 공개 데이터만
Read holdings with configured read-only key|설정된 조회 전용 키로 보유내역 읽기
KRX · read only|KRX · 조회 전용
Quote|호가
Daily OHLCV|일별 OHLCV
DART disclosures|DART 공시
DART financials|DART 재무제표
Whole market|시장 전체
Indices|지수
Existing provider routing|기존 공급자 연결
Six digit KRX code|6자리 KRX 코드
Daily commentary|일별 해설
Weekly rates & FX|주간 금리·외환
Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.|참고용 · v2 신호 아님 (DO-NOT-BUILD TF-12). 거래 원장에 연결되지 않습니다.
United States|미국
Korea|한국
Overlay state|오버레이 상태
Model cards|모델 카드
Research register|연구 등록부
Macro live decision|매크로 실데이터 판정
Macro dry run|매크로 모의 검사
Live artifacts|실데이터 산출물
Dry-run artifacts|모의 검사 산출물
Strategy family|전략 유형
Trend switch (Faber SMA / MOP sign)|추세 전환 (Faber SMA / MOP 부호)
Volatility target (per-asset cap)|변동성 목표 (종목당 상한)
Risk parity across sleeves|전략 간 위험 균등 배분
Time-series momentum (MOP, long/short)|시계열 모멘텀 (MOP, 매수/매도)
Cross-sectional momentum (long top third)|횡단면 모멘텀 (상위 1/3 매수)
Pairs (Engle–Granger spread, y then x)|페어 (Engle–Granger 스프레드, y 다음 x)
Crypto short-horizon trend (per-asset 0/1)|가상자산 단기 추세 (종목별 0/1)
Cost bp/side · blank = table|편도 비용 bp · 공란 = 기존 비용표
MA crossover|이동평균 교차
RSI mean reversion|RSI 평균회귀
Momentum|모멘텀
Fast / lookback / RSI period|빠른 이동평균 / 관측 창 / RSI 기간
Slow / RSI exit · unused for momentum|느린 이동평균 / RSI 청산 · 모멘텀에는 미사용
Lookback · sessions|관측 창 · 거래일
Trading state|모의 거래 상태
Active rules|활성 규칙
Rule|규칙
Trigger|실행 조건
Triggers|실행 횟수
Outcome|결과
Reason|사유
Revision|개정
Market|시장
Limit|지정가
Quantity|수량
Quoted price|호가 가격
Comparator|비교 조건
Give the rule a name so you can find it later.|나중에 찾을 수 있도록 규칙 이름을 입력하세요.
Enter the instrument code this rule applies to.|이 규칙을 적용할 종목 코드를 입력하세요.
Choose the market so quotes resolve to the right provider.|호가를 올바른 공급자에서 읽도록 시장을 선택하세요.
Choose buy or sell.|매수 또는 매도를 선택하세요.
Choose whether the size is a share count or a cash amount.|수량 기준 또는 금액 기준을 선택하세요.
Enter the size. This program does not choose one for you.|수량 또는 금액을 직접 입력하세요. 앱이 대신 결정하지 않습니다.
Choose market or limit.|시장가 또는 지정가를 선택하세요.
No validity window: this rule stays live until you stop it.|유효기간이 없으면 직접 중지할 때까지 활성 상태가 유지됩니다.
Metrics|측정값
Data sources|데이터 출처
Series|시계열
First|시작 관측일
Last|최종 관측일
Note|비고
Point|지점
Strike|행사가격
Volatility|변동성
Spot delta|현물 델타
Residual · vol points|잔차 · 변동성 포인트
Quoted vol %|호가 변동성 %
Fitted vol %|적합 변동성 %
SABR quote residuals|SABR 호가 잔차
SABR smile|SABR 스마일
Smile quotes|스마일 호가
Observations|관측
Premium|프리미엄
Delta · spot|현물 델타
Delta · forward|선물환 델타
Gamma / 1% spot|현물 1%당 감마
Vega / vol point|변동성 포인트당 베가
Theta / day|일별 세타
Domestic rho / bp|국내 금리 bp당 로
Foreign rho / bp|외국 금리 bp당 로
Volatility used|사용 변동성
Premium · quote / base|프리미엄 · 상대/기준 통화
Premium % of spot|현물 대비 프리미엄 %
Premium / 1m base|기준 통화 백만 단위당 프리미엄
Forward|선물환
Pair|통화쌍
Tenor · years|기간 · 년
Forward curve|선물환 곡선
Spot history|현물 이력
Quote per base|기준 통화당 상대 통화
max_sharpe|최대 Sharpe
min_vol|최소 변동성
risk_parity|위험 균등
equal_weight|동일 비중
Original narrative (English)|원문 해설 (영어)
'''

_PAIRS += r'''
PyQt6 native: Home, daily Markets, Bonds, Rates, FX, Structuring, Macro sheet, Derivatives, ETF, Crypto, KRX, Monte Carlo, Strategy Lab, portfolios, Signals, Library/export, Connections, System\nMacro v2, paper trading, rules and optional AI commentary are connected / Remaining checks: actual Windows display, DPI and installation\nBrowser: the existing Flet app is retained.|PyQt6 네이티브: Home, 일별 Markets, Bonds, Rates, FX, Structuring, Macro sheet, Derivatives, ETF, Crypto, KRX, Monte Carlo, Strategy Lab, 포트폴리오, Signals, Library·저장, 연결 설정, System\nMacro v2·모의매매·규칙·선택 AI 해설 연결 완료 / 남은 검증: 실제 Windows 표시·DPI·설치\n브라우저: 기존 Flet 앱을 유지합니다.
Confirm rule|규칙 확인
Delete rule|규칙 삭제
Delete {name} and its change history?|{name} 및 변경 이력을 삭제할까요?
Confirmation does not arm the engine.|확인은 엔진을 활성화하지 않습니다.
Reset paper orders, verdicts and crossing history? Rules are retained.|모의 주문·판정·교차 이력을 초기화할까요? 규칙은 유지됩니다.
Save verified · {status}|저장 확인 완료 · {status}
CONFIRMED · activation is separate.|CONFIRMED · 활성화는 별도입니다.
{status} · Arming the engine is separate.|{status} · 엔진 Arm은 별도입니다.
Paper record complete|모의 기록 완료
Rejected|거절
'''

_PAIRS += r'''
Rates|금리
Signals|신호
Structuring|구조화 상품
Crypto|가상자산
Derivatives|파생상품
Macro sheet|매크로 현황
Macro v2|매크로 v2
Strategy Lab|전략 실험실
Rules|규칙
Underlying|기초자산
Equity|주식
Calendar days|달력일
Bond coupon %|채권 쿠폰 %
CTD DV01 / contract|계약당 최저가인도채권 DV01
Upbit + Binance · public data|Upbit + Binance · 공개 데이터
KIS · option board|KIS · 옵션 시세판
Arm|엔진 활성화
Disarm|엔진 비활성화
BUY|매수
SELL|매도
QUANTITY|수량
NOTIONAL|금액
MARKET|시장가
LIMIT|지정가
AT_OR_ABOVE|이상
AT_OR_BELOW|이하
CROSSES_UP|상향 돌파
CROSSES_DOWN|하향 돌파
Synthetic data included · not current market data.|합성 데이터 포함 · 현재 시장 데이터가 아닙니다.
Synthetic data · {detail}|합성 데이터 · {detail}
Synthetic short rates · {detail}|합성 단기금리 · {detail}
Synthetic data included: {detail}|합성 데이터 포함: {detail}
SYNTHETIC · all quotes are synthetic.|SYNTHETIC · 모든 시세는 합성 데이터입니다.
Last prints only · quotes outside trading hours/at close are not simultaneously executable prices.|Last prints only · 장외/마감 시 호가는 동시 체결 가능한 가격이 아닙니다.
SYNTHETIC · not market observations.|SYNTHETIC · 시장 관측값이 아닙니다.
SYNTHETIC · all time series are synthetic.|SYNTHETIC · 모든 시계열은 합성 데이터입니다.
UNAVAILABLE · Check the provider response. No substitute values are generated.|UNAVAILABLE · 공급자 응답을 확인하세요. 대체 값을 생성하지 않습니다.
EMPTY · The provider returned an empty result.|EMPTY · 공급자가 빈 결과를 반환했습니다.
All products use the same UST curve. KRW products are illustrative structures discounted with this curve, not KRW market quotes.|모든 상품에 동일한 UST 곡선을 사용합니다. KRW 상품도 이 곡선으로 할인하는 구조 예시이며 KRW 시장 호가가 아닙니다.
The CMS chart assumes the same spread is realized in every coupon period.|CMS 차트는 각 쿠폰 기간에 같은 스프레드가 실현된다고 가정합니다.
Hedge sign: + buy / pay fixed, − sell / receive fixed. No real orders are executed.|Hedge 부호: + 매수 / 고정금리 지급, − 매도 / 고정금리 수취. 실제 주문을 실행하지 않습니다.
Observed rate history|관측 금리 이력
PCA NOT_RUN · at least 60 observations are required.|PCA 미실행 · 60개 이상의 관측이 필요합니다.
Rate distribution · central 90%|금리 분포 · 중앙 90%
CONFIGURED means the setting exists. Test actual connectivity separately.|CONFIGURED는 설정의 존재만 뜻합니다. 실제 접속 성공은 별도 검사로 확인하세요.
Read-only connection checks. No account queries, orders or connection-setting changes are performed.|읽기 전용 접속 검사 결과입니다. 계좌 조회·주문·연결 설정 변경은 수행하지 않습니다.
Checks finished · some responses are unavailable.|검사 종료 · 응답 불가 항목이 있습니다.
Changes in rates/spreads are in bp; other changes use original units. Classifications are descriptive and do not change validation gates or positions.|금리·스프레드의 변화는 bp, 다른 지표의 변화는 원 단위입니다. 분류는 설명용이며 검증 게이트나 포지션을 바꾸지 않습니다.
SYNTHETIC · scores below are synthetic demonstrations, not official research-card verdicts.|SYNTHETIC · 아래 점수는 합성 시연입니다. 공식 연구카드 판정이 아닙니다.
Stored research records. Reading does not rerun cards or change verdicts.|저장된 연구 기록입니다. 조회는 카드를 재실행하거나 판정을 바꾸지 않습니다.
NOT_LOADED · no stored research cards.|NOT_LOADED · 저장된 연구카드가 없습니다.
Question · do not enter passwords or account information|궁금한 점 · 비밀번호나 계좌정보는 입력하지 마세요
Only this payload and question will be sent. AI commentary does not change official gate verdicts.|이 내용과 질문만 전송합니다. AI 해설은 공식 gate 판정을 변경하지 않습니다.
Requesting AI commentary…|AI 해설 요청 중…
Complete a calculation first. Failed/unrun records are not sent.|먼저 계산을 완료하세요. 실패·미실행 기록은 전송하지 않습니다.
Keep the question within 4,000 characters.|질문을 4,000자 이내로 입력하세요.
AI commentary complete · {detail} · original official verdicts are retained.|AI 해설 완료 · {detail} · 공식 판정은 원래 기록을 유지합니다.
Common {detail}|공통 {detail}
Synthetic data: {detail} · a calculation demonstration, not an investment allocation.|합성 데이터: {detail} · 투자 배분이 아닌 계산 시연입니다.
Search fields/values in this record|이 기록에서 필드·값 검색
BUILD_AS_INSURANCE / FORWARD_SIM / REFUSAL_BOOK describe uses, not PASS verdicts. Reading performs no validation or approval.|BUILD_AS_INSURANCE / FORWARD_SIM / REFUSAL_BOOK는 용도 표기이며 PASS 판정이 아닙니다. 조회는 검증이나 승인을 수행하지 않습니다.
Verified source records displayed. Reading does not change official verdicts or recommended books.|검증된 원문 기록을 표시했습니다. 조회가 공식 판정이나 권장 book을 바꾸지 않습니다.
Research register · display only. Design weights are not sent as exposure, rule or book inputs.|Research register · 표시 전용. 설계 가중치를 노출·규칙·book 입력으로 보내지 않습니다.
Recorded settings displayed. Exposure is not recalculated in the UI. FORWARD-SIM/refusal are not recommendations.|기록된 구성 값을 표시했습니다. 화면에서 노출을 재계산하지 않습니다. FORWARD-SIM·refusal은 권장이 아닙니다.
NOT_LOADED · no macro_state. Values are not inferred.|NOT_LOADED · macro_state가 없습니다. 값을 추정하지 않습니다.
NOT_LOADED · no execution records|NOT_LOADED · 실행 기록 없음
REFUSED · values from invalid macro_state are not displayed.|REFUSED · 검증에 실패한 macro_state의 수치는 표시하지 않습니다.
Alert acknowledged · {detail}|알림 확인 · {detail}
HALT acknowledged · {detail}|HALT 확인 · {detail}
Sell futures {contracts} contracts · rounded {rounded}\nResidual DV01 after rounding {residual} per bp · no real orders|선물 매도 {contracts} contracts · 반올림 {rounded}\n반올림 후 잔여 DV01 {residual} per bp · 실제 주문 없음
Volatility target and Crypto trend allocate independently to each asset. Their cap is per asset, not a portfolio gross cap; N assets can reach N× exposure. They are single-asset rules, not a portfolio volatility target or a 1× basket. Multi-asset results are an unnormalized sleeve sum.|변동성 목표·가상자산 추세는 종목별로 독립 배분합니다. 상한은 종목당 상한이며 포트폴리오 총노출 상한이 아닙니다. N개 종목은 총 N배 노출에 이를 수 있습니다. 포트폴리오 변동성 목표나 1배 바스켓이 아닌 단일 종목 규칙이며, 여러 종목의 결과는 정규화하지 않은 전략별 합계입니다.
'''

_PAIRS += '\nAnalysis narrative · original source language retained|분석 해설 · 원문 언어 유지\nMetric|측정 항목\n'

_PAIRS += '\nUS 10-year yield|미국 10년 금리\nBitcoin|비트코인\n'

_PAIRS += r'''
Analysis narrative · display language; original retained in export|분석 해설 · 선택 언어로 표시하며 내보내기에는 원문 유지
Flat rates across tenors · typed rates: {rates}|모든 만기에 동일 금리 적용 · 직접 입력한 금리: {rates}
Delta strike uses ATM vol, then reprices at SABR vol. ATM means delta-neutral straddle.|델타 행사가격은 ATM 변동성으로 구한 뒤 SABR 변동성으로 다시 가격을 산출합니다. ATM은 델타 중립 스트래들을 뜻합니다.
{ccy} domestic rate|{ccy} 국내 금리
{ccy} foreign rate|{ccy} 외국 금리
Forward points|선물환 포인트
Pip size|핍 크기
Carry · long {ccy} / year|{ccy} 매수 연간 캐리
Implied basis|내재 베이시스
Market forward|시장 선물환
Forwards|선물환
Points|포인트
Volatility · %|변동성 · %
Observations · {start} → {end}|관측 · {start} → {end}
'''

EN, KO = {}, {}
TEMPLATES = []
for line in (_PAIRS + _TERMS).strip().splitlines():
    if not line.strip(): continue
    en, ko = (s.replace('\\n', '\n') for s in line.split('|', 1))
    EN[ko], KO[en] = en, ko
    if '{' in en:
        for source, target, language in ((en, ko, 'ko'), (ko, en, 'en')):
            parts = []
            for literal, key, spec, conversion in Formatter().parse(source):
                parts.append(re.escape(literal))
                if key is not None: parts.append(f'(?P<{key}>.+?)')
            TEMPLATES.append((language, re.compile(''.join(parts), re.S), target))


KO["Build && Test"] = KO["Build & Test"]
KO["Portfolio && Risk"] = KO["Portfolio & Risk"]

def translate(text, language):
    """Translate only authored UI messages; unknown source text stays intact."""
    text = str(text)
    if language not in ('en', 'ko'): return text
    mapping = KO if language == 'ko' else EN
    if text in mapping: return mapping[text]
    for lang, pattern, target in TEMPLATES:
        if lang == language:
            m = pattern.fullmatch(text)
            if m: return target.format(**m.groupdict())
    if '\n' in text:
        return '\n'.join(translate(line, language) for line in text.split('\n'))
    return text


def display(widget, text):
    window = widget.window()
    translated = translate(text, getattr(window, 'ui_language', None))
    ctx = getattr(window, 'ctx', None)
    return ctx.text(text) if ctx and translated == str(text) else translated
