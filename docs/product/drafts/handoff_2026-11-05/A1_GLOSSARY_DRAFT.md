# A1 표준 용어집 초안 (UI-10)

> **상태: 미검증 초안 (handoff 자료).** 2026-11-05 Claude 세션이 주간 사용량 한도로 멈출 때 백그라운드 워크플로 결과를 그대로 옮겼습니다.
> 소유자 승인 전이며, 반박 검토(challenge) 단계 전에 멈췄습니다. 본문의 `/tmp/claude-0/...` 경로는 그 세션의 임시 폴더라 이제 열 수 없습니다.
> 이 폴더는 main에 병합하지 않습니다. 확정본은 새 PR에서 `docs/product/` 아래 정식 문서로 만듭니다.

# QUANTGEN 표준 용어집 (초안, A1 UI-10)

**적용 범위:** Native(PyQt6, `quantgen_desktop/`)와 Flet 브라우저 앱(`ui/`) 전체.
- 화면 표시에만 적용합니다. 숫자, 판정, 연구 결과, 내보내기 파일의 영어 원문은 바꾸지 않습니다.
- 제공처 이름(FMP, KIS, Yahoo Finance, FRED, DART), 종목코드, 주문 ID, 모형 식별자 데이터도 그대로 둡니다(13-8/a 원칙).

**출처 약어**
- [KRX] 한국거래소 시세·상품명세 용어
- [KOFIA] 금융투자협회(채권정보센터, 펀드·ETF 공시)
- [BOK] 한국은행 경제용어
- [HTS] 주요 증권사 HTS·MTS 화면 용어
- [KIS] 한국투자증권 Open API 용어
- [DART] 전자공시 용어
- [법] 법령 용어
- [관행] 국내 증권사 리서치·채권·파생 데스크 관행
- [APP] 앱 안의 용어집 `core/education/glossary.py`. 32개 용어의 한국어 이름은 이번에 코드를 실행해 확인했습니다.

**검증 한계:** [APP]을 뺀 외부 출처는 일반적인 업계 용례를 기억에 기대어 적은 것입니다. 네트워크가 없어 원문과 대조하지 못했으므로 모두 **unverified**입니다.

## 표기 원칙
1. 한국 시장에서 영어 약어로 쓰는 말은 영어로 둡니다: DV01, VaR, CVaR, ETF, ATM, CTD, PER, EPS, PBR, SVI, SABR, GARCH, GBM, PBO, DSR, IS/OOS, P5/P50/P95, 2s10s, 1y1y.
   - 처음 나오거나 표 머리글일 때만 한국어를 함께 씁니다. 예: 순자산가치(NAV), 과적합 확률(PBO).
2. 그리스 문자(α β γ θ σ κ ν Δ)는 그대로 씁니다.
3. 같은 영어 단어가 화면마다 다른 뜻이면 한국어를 나눕니다(10절). 이때 영어 원문은 바꾸지 않고 화면별 한국어 맵을 둡니다. 내보내기 파일의 영어 머리글을 지키기 위해서입니다.
4. 상태값은 두 단계로 나눕니다(1-2절).
   - 운영 상태: 한국어만 쓰고, 코드는 툴팁과 내보내기에 남깁니다.
   - 공식 연구·검증 코드: "한국어(코드)" 형식으로 씁니다.
5. 입력란 단위는 괄호에 넣습니다: "분석 기간 (거래일)". 개수는 "거래일 수"로 씁니다. 본문에서는 "20거래일"처럼 씁니다. "· 거래일"처럼 단위만 따로 떼어 쓰지 않습니다.
6. 숫자 바로 뒤에는 조사를 붙이지 않습니다. "RSI 62은" 대신 "RSI 62: 과매수 구간입니다"로 씁니다. 수는 아라비아 숫자로 씁니다("오 년" → "5년").
7. 문체는 합니다체로 통일합니다.
8. 띄어쓰기를 고정합니다: 내재변동성, 최대낙폭, 행사가격, 발행가격, 종목코드, 상장주식수, 시가총액, 수익률 곡선, 구성요소.

## 0. 메뉴·화면 이름 결정

| 항목 | 현재 (Native / Flet) | 결정 | 이유 |
|---|---|---|---|
| UI-14 Build & Test | 설계 및 검증 / 설계·검증 | **설계/검증** | 소유자 지정. 두 앱이 서로 다른 이름을 쓰던 것도 함께 정리됩니다. 영어 'Build & Test'는 그대로 둡니다. |
| UI-15 Portfolio & Risk | 포트폴리오 및 위험 / 포트폴리오·위험, Home 바로가기 '포트폴리오 · 위험' | **분석** | 소유자 지정. 다만 같은 왼쪽 메뉴에 '분석 도구'가 함께 있어 헷갈릴 수 있습니다(질문 Q1). |
| UI-1 Macro sheet | 거시 지표표 (실제로 보이는 값. 같은 키의 '매크로 현황'은 가려져 쓰이지 않음) / 거시경제 관측 | **매크로 지표** | '매크로 v2'와 같은 '매크로' 계열로 맞춥니다. 증권사 리서치와 HTS에서 '매크로'가 흔하고 개인투자자도 압니다. '지표표'는 '표'가 겹쳐 어색합니다. |
| UI-1 Macro v2 | 매크로 v2 / 거시경제 v2 | **매크로 v2** | Native는 그대로 두고 Flet만 맞춥니다. |
| Macro (Flet 메뉴) | 매크로 / 거시경제 | **매크로** | 앱 전체에서 한 이름을 씁니다. 한국은행 문서의 '거시경제'는 본문 설명에만 씁니다. |
| Research Home | 연구 홈 / 리서치 홈 | **연구 홈** | Native 기준 |
| Research Library | 연구 보관함 / 연구 라이브러리 | **연구 보관함** | Native 기준 |
| Indicator guide | 기술지표 가이드 / 지표 가이드 | **기술지표 가이드** | Native 기준 |
| Connections | 연결 / 데이터 연결 | **데이터 연결** | 뜻이 더 분명합니다. |
| Signals | 신호 / 기술적 관측 | **기술적 분석** (Q7) | '신호'는 매매 권유처럼 읽힐 수 있습니다. |
| Paper Trading | 모의매매 / 모의 실행 | **모의투자** (Q8) | KIS와 증권사가 쓰는 용어입니다. 3단계 안전 설계 문구('모의투자 기본')와도 같습니다. |
| Strategy Lab / Quant Lab | 전략 실험실 / 분포 분석 | 그대로 | Flet 문장 속 'Quant Lab'은 '분포 분석'으로, Native 문장 속 'Quant Lab'은 '설계/검증 › 몬테카를로'로 바꿉니다. |
| Light / Dark | 밝게·다크 / 밝게·어둡게 | **라이트 / 다크** | 공통 |

## 1-1. 공통 UI

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| Data source / Source | 데이터 출처 / 출처 | | | 관행 |
| Provider | **제공처** | 제공처 이름은 유지 | 공급자·공급처를 하나로 맞춤 | 관행 |
| Model | **모형** | | 통계·가격결정 모형. '모델 카드'만 고유명으로 둠 | APP(GARCH 모형, SABR 모형) |
| Symbol / Ticker | **종목코드** | | FX 화면만 '통화쌍' | KRX |
| Metric / Field (표의 이름 열) | **항목** (Q4) | | 머리글은 '항목 / 값'. 필드·측정 항목을 하나로 맞춤 | HTS |
| Metrics (표 제목) | 주요 지표 | | | HTS |
| Value / Recorded value | 값 / 기록값 | | | |
| Indicator | 지표 | | | |
| Status / Reason | 상태 / 사유 | | '이유'를 '사유'로 | |
| Observations (개수) | 관측 수 | | | |
| Observed value / Observed date | 관측값 / 관측일 | | | |
| Last (값 열) / Last (날짜 열) | 최근값 / 최종 관측일 | | 10절 | |
| Sessions (개수) | 거래일 수 | | 입력란 단위는 "(거래일)" | KRX |
| Calendar days | 달력일 수 | | | |
| Horizon | 분석 기간 | | | |
| Tool / Kind / Detail | 도구 / 종류 / 상세 | | | |
| Synthetic demo | 합성 데이터 시연 | | | |
| blank = … | 비우면 … | | "공란 = …" 표기 금지 | |
| Daily (보고서) / Daily (자료) | 일일 / 일별 | | 일일 시장 해설, 일별 시세 | 관행 |

## 1-2. 상태값 (UI-2)

**운영 상태 (한국어만; 코드는 툴팁·내보내기에 남김)**

| 코드 | 표준 한국어 | 비고 |
|---|---|---|
| OBSERVED | **정상 관측** | 소유자 예시. 툴팁에 '일별 종가 기준'을 둡니다. |
| STALE (자료가 오래됨) | 오래된 자료 | 네 가지로 쓰이던 표현을 하나로 맞춥니다. |
| stale (실시간 수신이 멈춤) | 수신 지연 · 마지막 값 유지 | 위와 다른 상태라서 따로 둡니다. |
| UNAVAILABLE / EMPTY | 조회 불가 / 결과 없음 | |
| NOT_LOADED / LOADING | 조회 전 / 조회 중 | |
| SNAPSHOT / STREAMING | 조회 시세 / 실시간 체결 | |
| CONFIGURED / NOT_CONFIGURED / REACHABLE / UNAVAILABLE(연결) | 설정됨 / 미설정 / 접속 확인 / 응답 없음 | |
| COMPLETED / RUNNING / FAILED | 완료 / 실행 중 / 실패 | |
| COMPUTED / CONVERGED / NOT_APPLICABLE | 계산 완료 / 수렴 / 해당 없음 | |
| PAUSED / CONFIRMED / HALT | 일시 정지 / 확인 완료 / 긴급 정지 | |

**공식 연구·검증 코드 ("한국어(코드)"; 13-8/a의 '공식 상태 코드 유지' 원칙과 UI-2를 함께 만족시키는 방식, Q3)**

| 코드 | 표기 |
|---|---|
| PASS / FAIL / NOT_RUN | 통과(PASS) / 실패(FAIL) / 미실행(NOT_RUN) |
| PARTIAL / NOT_APPLIED | 부분(PARTIAL) / 미반영(NOT_APPLIED) |
| NOT_VERIFIED / NOT_FROZEN / NOT_INSPECTED / NOT_APPROVED | 미검증 / 미동결 / 미점검 / 미승인, 각각 괄호에 코드 |
| REJECT / WITHHELD | 기각(REJECT) / 판정 보류(WITHHELD) |
| ARMED / BUILD_AS_INSURANCE | 활성(ARMED) / 보험용 구축(BUILD_AS_INSURANCE) |
| SYNTHETIC | 합성(SYNTHETIC). 문장 안에서는 "합성 데이터". '합성 데이터 · SYNTHETIC'처럼 두 번 쓰지 않습니다. |

## 2. 주식·시장

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| Quote (한 종목 시세 화면·표) | **현재가** | | 지금은 '호가'인데 잘못된 번역 | HTS |
| Bid/ask quote | 호가 | | 매수·매도 호가, FX·레포 딜러 호가에만 씀 | KRX |
| price (시세 표의 행) | 현재가 | | | HTS |
| Open / High / Low / Close | 시가 / 고가 / 저가 / 종가 | | | KRX |
| Change / Change % | 전일 대비 / 등락률 | | | KRX |
| Volume / Turnover | 거래량 / 거래대금 | | | KRX |
| Market cap / Listed shares | 시가총액 / 상장주식수 | | | KRX |
| Name / Sector / Market | 종목명 / 업종 / 시장 구분 | | | KRX |
| PER / EPS / PBR | PER / EPS / PBR | 유지 | | HTS |
| Daily OHLCV / Whole-market snapshot / Index levels | 일별 시세 / 전 종목 시세 / 지수 시세 | | | KRX |
| Disclosures / Financials (DART) | 공시 / 재무제표 (DART) | DART | | DART |
| Report / Filer / Receipt / Account / This term / Prev term | 보고서명 / 제출인 / 접수번호 / 계정과목 / 당기 / 전기 | | | DART |
| Candlestick | 캔들(봉) | | | APP |
| Real-time / Delayed quote | 실시간 시세 / 지연 시세 | | | HTS |
| Last prints only | 최종 체결가 기준 | | | HTS |
| 52-week range / Short-sale ratio / Investor net buying | 52주 최고·최저 / 공매도 비중 / 투자자별 순매수 | | | KRX |
| ETF / LETF | ETF / 레버리지 ETF | ETF | | KRX |
| nav | 순자산가치(NAV) | 병기 | | KRX·KOFIA |
| premium_pct | 괴리율 | | | KRX |
| tracking_error_pct | 추적오차율 | | | KRX |
| cu_units | 설정단위(CU) | 병기 | | KRX |
| lp_holding_pct | LP 보유 비율 | LP | LP = 유동성공급자 | KRX |
| Fee | 보수 | | | KOFIA |
| Buy & hold / Trend switch / Vol target | 매수 후 보유 / 추세 전환 / 변동성 목표 | | | 관행 |
| USD/KRW | 원/달러 환율 (USD/KRW) | 코드 병기 | | BOK |

## 3. 금리·채권 (UI-11a)

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| Yield / YTM | 만기수익률 (짧게 '수익률') | | | KOFIA |
| Coupon (채권) / Coupon (구조화 상품) | 표면금리 / 쿠폰 | | Rates '채권 쿠폰 %'는 '채권 표면금리 %'로 | KOFIA |
| Price per 100 / per 100 | 액면 100당 가격 / 액면 100당 | | '100당'만 쓰지 않음 | KOFIA |
| Maturity / Tenor / Key tenor | 만기 / 만기 / 주요 만기 | | Tenor 번역 '기간'은 '만기'로 | 관행 |
| Macaulay duration | 맥컬리 듀레이션 | | 서술문의 '매콜리'도 맞춤 | APP 별칭 |
| Modified duration | 수정 듀레이션 | | | KOFIA |
| Convexity | **컨벡시티** (처음 나올 때 '컨벡시티(볼록성)') (Q6) | | | KOFIA·관행 |
| DV01 / Key-rate DV01 | DV01 / 만기별 DV01 | DV01 | PV01·BPV는 별칭 | APP |
| z-spread | Z-스프레드 | | | 관행 |
| 2s10s, 5s30s / 2s5s10s fly | 2s10s 금리차 / 2s5s10s 버터플라이 | 유지 | | 관행 |
| Carry / Roll-down / Carry + roll | 캐리 / 롤다운 / 캐리+롤다운 | | | 관행 |
| Breakeven (bp) | 손익분기 금리 변화(bp) | | 기대인플레이션(BEI)과 구분 | |
| Curve price | 곡선 기준 가격 | | | |
| Yield curve | 수익률 곡선 | | | BOK·APP |
| Zero rate | **무이표 금리** (Q14) | | 정책금리 '제로금리'와 헷갈리지 않게 | 관행 |
| DF / Par | 할인계수 / 파 금리 | | | 관행 |
| Forward rate | **선도금리** (1y1y·5y5y 표기는 유지) | | FX의 '선물환'과 분리 | BOK |
| Bootstrapping (곡선) | 부트스트래핑 | | 몬테카를로의 '블록 부트스트랩'과 다른 개념 | APP |
| Nelson-Siegel / Svensson | Nelson-Siegel / Svensson (NS/NSS) | 유지(고유명) | 콤보 표시명 | |
| Curve shape | 곡선 형태: 정상(우상향) / 역전 / 평탄 / 중간 만기 돌출 | | | rates_narrative |
| Regime (곡선 변화) | 변화 유형 | | | |
| bull steepener | 강세 스티프닝 (금리 하락·장단기 금리차 확대) | | Rates와 Macro가 같은 표를 씀(Q17) | 관행 |
| bear steepener | 약세 스티프닝 (금리 상승·장단기 금리차 확대) | | | 관행 |
| bull flattener | 강세 플래트닝 (금리 하락·장단기 금리차 축소) | | | 관행 |
| bear flattener | 약세 플래트닝 (금리 상승·장단기 금리차 축소) | | | 관행 |
| parallel up / down / unchanged | 평행 상승 / 평행 하락 / 변화 없음 | | | |
| PCA level / slope / curvature | 수준 / 기울기 / 곡률 | | | 관행 |
| Principal component / Loadings / Explained | 주성분 / 주성분 적재값 / 설명 비율 | | | |
| Swap / IRS / Par swap rate | 스왑 / 금리스왑(IRS) / 스왑금리 | IRS | | 관행 |
| Fixed / Float | 고정금리 / 변동금리 | | | |
| Payer / Receiver | 고정금리 지급형 / 고정금리 수취형 | | 현재 번역 유지 | |
| Notional / PV | 명목금액 / 현재가치 | | | |
| Annuity | 애뉴이티(연금계수) | | | 관행 |
| Swaption / Cap / Floor / Caplet | 스왑션 / 캡 / 플로어 / 캐플릿 | | | 관행 |
| Normal vol (bp) / Black vol | 정규 변동성(bp) / Black 변동성 | Bachelier·Black 유지 | | 관행 |
| Vasicek / CIR / Hull-White | Vasicek / CIR / Hull-White 모형 | 유지(고유명) | 콤보 데이터 ID는 그대로(Q15) | |
| Kappa / Theta(장기 평균) / Sigma | 평균회귀 속도 κ / 장기 평균 θ / 변동성 σ | 기호 | 옵션 세타와 분리 | |
| Short rate / Half-life | 단기금리 / 반감기 | | | |
| Shock · bp / Scenario | 금리 충격 · bp / 시나리오 | | | |
| P&L / P&L % | 손익 / 손익률 | | | HTS |
| CTD / Conversion factor | 최저가인도채권(CTD) (표에서는 CTD) / 전환계수 | CTD | | KRX 국채선물 |
| Contracts to sell | 매도 계약 수 | | | |
| Repo | 레포(RP) | | | 관행 |
| UST / Treasury | 미국채, 만기는 '미국채 10년물' | | | 관행 |
| Real yields / Breakevens | 실질금리 / 기대인플레이션(BEI) | | | BOK |
| Payments/year / Annual · Semi-annual · Quarterly | 연 n회 지급 / 연 1회 · 반기 · 분기 | | Flet '연간'은 '연 1회'로 | |
| ACT/365F | ACT/365F | 유지 | | |

## 4. 외환

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| FX / FX swap | 외환 / 외환스왑 | | | BOK |
| Spot (FX) | 현물환율 | | | BOK |
| FX forward / forward points | 선물환(선물환율) / 스왑포인트 | | 이 화면에서만 '선물환' | BOK·APP |
| Pair / Base · quote currency | 통화쌍 / 기준통화 · 상대통화 | | | BOK |
| Domestic / foreign rate | 국내 금리 / 외국 금리 | | | |
| Carry / carry trade / Carry/vol | 캐리 / 캐리 트레이드 / 캐리/변동성 비율 | | | APP |
| Delta spot / forward | 현물 델타 / 선물환 델타 | | 현재 번역 유지 | |
| Rho (domestic / foreign) | 국내 금리 로 / 외국 금리 로 | | | |
| ATM / 25d RR / 25d BF | ATM(등가격) / 25델타 리스크 리버설 / 25델타 버터플라이 | ATM | | 관행 |
| Point (스마일 표의 열) | 구분 | | '지점'은 어색함 | |
| Cross-currency basis | 통화 베이시스 | | | 관행 |
| Rebalance | 리밸런싱 | | | 관행 |
| Rate date | 금리 기준일 | | 화면에 보일지는 Q12 | |

## 5. 파생상품·옵션·구조화 상품 (UI-11a)

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| Option / Call / Put | 옵션 / 콜 / 풋 | | | KRX |
| Strike | **행사가격** | | '행사가'는 쓰지 않음. 테스트 desktop_language_acceptance.py:79가 이미 '행사가격'을 고정함 | KRX |
| Expiry | 만기 (옵션 화면은 '옵션 만기') | | | KRX |
| Underlying / Spot (주식) | 기초자산 / 현물 가격 | | | KRX |
| Implied volatility / Model-free IV | 내재변동성 / 모형 비의존 내재변동성 | | | KRX·APP |
| Smile / Skew / SVI / SABR | 변동성 스마일 / 스큐 / SVI / SABR 모형 | SVI·SABR | | APP |
| Greeks | **민감도(그릭스)** | | 표 열 'Risk'는 '민감도'로 | KRX 옵션 민감도 |
| Delta / Gamma / Vega / Theta / Rho | 델타 / 감마 / 베가 / 세타 / 로 | | | KRX |
| Risk-neutral density | 위험중립 밀도(RND) | | | 관행 |
| Futures / Basis / Box rate / Implied funding | 선물 / 베이시스 / 박스 금리 / 내재 조달금리 | | | KRX |
| Parity forward | 패리티 선도가격 | | | |
| Static arbitrage checks | 정적 차익거래 점검 | | | |
| call/put vertical · butterfly · calendar | 콜·풋 수직 스프레드 / 버터플라이 / 캘린더 스프레드 | | | KRX |
| Hedge simulation / Hedge sheet / Hedge sign | 헤지 시뮬레이션 / 헤지 내역 / 헤지 부호 | | | |
| Payoff / Maturity payoff | 손익 / 만기 손익 구조 | | | |
| Leg / Leg decomposition | 구성요소 / 구성요소별 분해 | | | |
| Rationale / Quantity / Unit | 근거 / 수량 / 단위 | | | |
| Principal-protected note | 원금보장형 구조화 상품 | | 콤보와 결과에 같은 말을 씀 | APP |
| Reverse convertible | 역전환형 구조화 상품 | | | |
| CMS steepener note | CMS 스티프너 상품 | CMS | | |
| Dual-currency deposit | 이중통화예금(DCD) | DCD | | 은행 상품명 |
| ELS / ELB / DLS | 유지 | 유지 | | KOFIA |
| Participation rate / Issue price / Fair value / Margin | 참여율 / 발행가격 / 공정가치 / 마진 | | | |
| Leverage / Enhanced yield / Zero-coupon bond | 레버리지 / 수익률 향상형 / 할인채(무이표채) | | | |

## 6. 위험·포트폴리오·전략 검증

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| Risk (단원) / Volatility | 위험 / 변동성 | | | |
| Annualized | 연율 (예: 변동성(연율)) | | | 관행 |
| Max drawdown / Drawdown | 최대낙폭(MDD) / 낙폭 | MDD | | APP |
| VaR / CVaR / ES | VaR / CVaR / 기대손실(ES) | 유지 | | APP |
| Sharpe ratio | **샤프 지수** (Q5) | | | APP |
| Deflated Sharpe / Haircut Sharpe | 디플레이티드 샤프 지수(DSR) / 헤어컷 샤프 지수 | DSR | | |
| Beta / Correlation | 베타 / 상관계수 | | | APP |
| Return / Weight | 수익률 / 비중 | | | |
| Efficient frontier | 효율적 투자선 | | | 투자론 관행 |
| max_sharpe / min variance / risk parity / equal weight | 최대 샤프 지수 / 최소분산 / 리스크 패리티 / 동일 비중 | | | 관행 |
| Risk contribution | 위험 기여도 | | | |
| Long-only, fully invested | 매수 전용·전액 투자 | | | |
| Weight cap / At bound (비중) | 종목당 비중 상한 / 비중 상한 도달 | | | |
| Converged | 수렴 여부 (예/아니오) | | True/False 대신 | |
| Benchmark | 벤치마크 | | | |
| Backtest / Costed backtest | 백테스트 / 비용 반영 백테스트 | | | APP |
| Walk-forward | 워크포워드 | | '순차 전진'은 쓰지 않음 | 관행 |
| In-sample / Out-of-sample | 표본 내(IS) / 표본 외(OOS) | IS/OOS | | |
| PBO | 과적합 확률(PBO) | PBO | | |
| Plateau / Positive years | 안정 구간 / 수익 연도 비율 | | | |
| Trades / Win rate / Turnover | 거래 수 / 승률 / 회전율 | | | HTS |
| Cost · bp per side | 편도 비용 · bp | | 현재 번역 유지 | |
| Equity (곡선) | 누적 가치 | | 10절 | |
| Gross exposure / Borrowing | 총노출 / 차입 | | | |
| Scorecard / Decision / Verdict / Study card | 연구 성적표 / 판정 / 검증 판정 / 연구 카드 | | | |

## 7. 계량·통계·몬테카를로

| English | 표준 한국어 | 영어 유지 | 범위·비고 | 출처 |
|---|---|---|---|---|
| Monte Carlo (simulation) | 몬테카를로 (시뮬레이션) | | 'Monte Carlo' 영어 표기를 없앰 | APP |
| Paths / Seed | 시뮬레이션 경로 수 / 난수 시드 | | | |
| Drift | 기대수익률 가정 (드리프트) | | 추세 가정·드리프트를 하나로 맞춤 | |
| rf / ERP / Risk premium | 무위험금리 / 주식위험프리미엄(ERP) / 위험 프리미엄 | ERP | | 관행 |
| Convexity correction (드리프트) | 볼록성 보정 | | 채권 '컨벡시티'와 구분 | |
| P5 / P50 / P95 / Percentile band | P5 / P50(중앙값) / P95 / 백분위 구간 | 유지 | | APP |
| P(loss) / P(terminal ≥ target) | 손실 확률 / 목표가 이상 마감 확률 | | | |
| GBM / GARCH(1,1)-t / Jump | GBM / GARCH 모형 / 점프 모형 | 유지 | | APP |
| Student-t innovations | t분포 충격 | | | |
| Block bootstrap | 블록 부트스트랩 | | 곡선 '부트스트래핑'과 구분 | |
| Persistence / Half-life | 지속성 / 반감기 | | | |
| Sample / Next-session / Horizon-average vol | 표본 변동성 / 다음 거래일 변동성 / 기간 평균 변동성 | | | |
| Conditional volatility | 조건부 변동성 | | | APP |
| Standard error / 95% interval | 표준오차 / 95% 구간 | | | |
| Parameter at bound | 추정 경계 도달 | | 비중 상한과 구분 | |
| z-score / percentile / p-value | z점수 / 백분위 / p값 | | | |
| ADF / AR(1) | ADF 검정(단위근) / AR(1) | 유지 | | |
| Regime (변동성) | 국면 (예: 변동성 국면) | | 상태·국면을 하나로 맞춤 | |
| SMA / EMA / RSI / MACD / BB | 단순이동평균 · SMA 등 [APP] 이름 그대로 | 약어 | | APP |
| Signal line | 시그널선 | | MACD | APP 별칭 |
| Overbought / Oversold / Momentum | 과매수 / 과매도 / 모멘텀 | | | APP |
| Composite / Component scores / Stance | 종합 점수 / 지표별 점수 / 방향 | | '관측값'·'관측 방향'은 쓰지 않음 | |
| strong bullish … strong bearish | 강한 상승 우위 / 상승 우위 / 중립 / 하락 우위 / 강한 하락 우위 | | Native 기준 | |
| Fast / Slow MA | 단기 / 장기 이동평균 | | | HTS |
| Lookback (신호) / Lookback (곡선 변화) | 모멘텀 기간 / 변화 비교 기간 | | '관측 창'은 쓰지 않음 | |

## 8. 가상자산

| English | 표준 한국어 | 영어 유지 | 비고 | 출처 |
|---|---|---|---|---|
| Crypto / Exchange | 가상자산 / 거래소 | | | 법 |
| Kimchi premium / Premium z | 김치 프리미엄 / 프리미엄 z점수 | | | 관행 |
| Perpetual futures / Funding rate | 무기한 선물 / 펀딩비 | | | 관행 |
| ETH/BTC / USDT per BTC | ETH/BTC 비율 / BTC당 USDT | 코드 | | |
| AR(1) amplitude half-life | AR(1) 진폭 반감기 | | | |
| Mon … Sun | 월 화 수 목 금 토 일 | | | |

## 9. 매크로

| English | 표준 한국어 | 비고 |
|---|---|---|
| Macro / Macro sheet / Macro v2 / Macro indicators | 매크로 / 매크로 지표 / 매크로 v2 / 매크로 지표 | 0절 |
| Daily commentary / Weekly rates & FX | 일일 시장 해설 / 주간 금리·외환 | |
| Overlay state / Model cards / Research register | 오버레이 상태 / 모델 카드 / 연구 등록부 | |
| Gate / Gate package / Book | 게이트 / 게이트 패키지 / 북 | |
| Dry run / Live decision | 모의 점검 / 실데이터 판단 | |
| Descriptive read / Group / Last / Observed date | 설명용 관측 / 분류 / 최근값 / 관측일 | |
| 1d 1w 1m 3m | 1일 1주 1개월 3개월 | |
| risk-on / risk-off | 위험 선호 / 위험 회피 | |
| Dollar / Credit / Gold / WTI / VIX | 달러 / 신용 / 금 / WTI / VIX | |
| Disposition / Open questions / Do not build / Go/No-go register | 처리 / 미결 질문 / 구축 제외 / 진행 여부 등록부 | |
| Design priors / Fail-closed inputs | 설계 사전값 / 실패 시 차단 입력 | |

## 10. 같은 영어, 다른 뜻 (화면별 한국어 맵이 필요한 단어)

영어 원문은 바꾸지 않습니다. 화면별 맵에서 한국어만 나눕니다.

| English | 화면·뜻 A | 화면·뜻 B | 지금 보이는 잘못된 값 |
|---|---|---|---|
| Forward | FX: 선물환 | Rates 스왑션·캐플릿: 선도금리. 서술문: 선도가격 | Rates에도 선물환이 뜸 |
| Equity | Structuring 기초자산: 주식 | Strategy·ETF 곡선: 누적 가치 | Strategy 축이 '주식' |
| Component | Signals: 구성 지표 | Rates PCA: 주성분 | PCA에 '구성 지표' |
| Last | Macro 값: 최근값 | FX 출처 표의 날짜: 최종 관측일 | FX에 '최근값' |
| Risk | Macro 단원: 위험 | Structuring Greeks 열: 민감도 | Greeks 열이 '위험' |
| Theta | 옵션: 세타 | 금리 모형: 장기 평균 θ | Rates 모형 표에 영어 'Theta' |
| Close | 시세: 종가 | 버튼: 닫기 | Flet에서 'Close'가 항상 '종가'로 바뀜 |
| Bootstrap | 곡선: 부트스트래핑 | 몬테카를로: 블록 부트스트랩 | |
| At bound | 포트폴리오: 비중 상한 도달 | GARCH: 추정 경계 도달 | |
| Quote | 시세 화면: 현재가 | 호가창·딜러 호가: 호가 | KRX·ETF 표에 '호가' |
| Observations | 개수: 관측 수 | KRX 일별 표 제목: 일별 시세 | '관측' |
| Convexity | 채권: 컨벡시티 | 몬테카를로 드리프트: 볼록성 보정 | |

## 11. 용어집을 둘 곳

- `core/education/glossary.py`의 각 용어에 '표준 이름(ko/en)'과 '화면 맥락' 필드를 더하고, 이 초안의 2~9절 용어를 등록합니다.
- 그러면 A1 표시 맵(Native `translations.py`, Flet `core/ui_legacy_messages.py`)과 A3 UI-12 '알아보기' 패널이 같은 용어 출처를 씁니다.
- 지금 용어집에 없는 용어는 위 표에서 고릅니다. 예: Z-스프레드, 롤다운, 선도금리, 애뉴이티, 스왑션, 펀딩비, PBO, 워크포워드, 효율적 투자선, 리스크 패리티.
- 이 구조는 제안이며 만들어 보지 않았습니다.

## A1 변경 목록 (초안)

A1 변경 목록 (초안)
- 기준: 작업 트리 s10 @516953a. main faf9f3b와 내용이 같습니다.
- 읽기만 했고 아무 파일도 바꾸지 않았습니다(git status 비어 있음).
- 형식: [항목 ID] 파일:줄 — 현재 → 변경 (검증 표시)
- 검증 표시:
  - [R] 이번에 그 줄을 직접 읽음
  - [실행] 이번에 translate()·LocaleContext('ko_KR').text()를 실행해 지금 보이는 한국어를 확인함
  - [S] 앞선 sweep의 목록 기준. 이번에는 다시 확인하지 않았으므로 unverified
- 원칙: 표시층만 바꿉니다(카탈로그, 화면별 맵, localize_columns, 표시용 포맷). 영어 원문, 내보내기, 숫자, 판정, 제공처·모형 식별자는 그대로입니다.

== A1-0 선행 작업 (용어를 바꾸기 전에 필요) ==
- A1-0a 템플릿 버그 [실행: sweep / 코드 R]
  - quantgen_desktop/translations.py:596-602가 템플릿을 re.S와 `.+?`로 컴파일하고, translate()(622-637)는 여러 줄 문장 전체에 템플릿을 먼저 적용합니다. 그래서 첫 줄 템플릿이 다음 줄까지 삼킵니다. 증상:
    - Derivatives 둘째 줄이 영어로 남습니다(display_prose_catalog.py:107-108).
    - Strategy에 "{'step': 42}개"가 나옵니다(display_prose_catalog.py:119).
  - 고칠 것: 자리표시자를 `[^\n]+?`로 바꾸거나, 줄을 먼저 나눈 뒤 템플릿을 적용합니다.
- A1-0b 화면별 한국어 맵 (영어 원문 불변) [R]
  - 대상: rates.py:100, 106 'Forward' / strategy.py:64, market_tools.py:150 'Equity' / rates.py:82 'Component' / fx.py:38 'Last' / structuring.py:61 'Risk' / rates.py:112 'Theta'
  - 예: (rates, 'Forward') → 선도금리
  - 이유: 원문 키를 바꾸면 내보내기 파일의 영어 머리글이 바뀝니다(tools.py:215-216의 sections). 그래서 원문 키 분리 대신 화면별 맵을 둡니다.
- A1-0c 가려진 항목 정리 [R]
  - macro_narrative_language.PAIRS가 translations.py보다 우선합니다(translations.py:610-612, sweep).
  - 지울 것: translations.py:489 'Macro sheet|매크로 현황', :198 'Instrument|종목'(313 '상품'에 가려짐), :379 'Daily commentary|일별 해설', display_prose_catalog.py:93 'Margin · per 100|마진 · 100당', core/ui_messages.py:190 LEGACY 'Macro sheet':'macro'
- A1-0d Native 항목 추가 [실행]
  - 지금 Flet 공용 카탈로그로 넘어가 보이는 말: Field→필드, Component→구성 지표, Light→밝게, Monte Carlo→몬테카를로, Close→종가, Composite→종합 관측값, Stance→관측 방향, Max drawdown→최대 낙폭
  - Native에 자기 항목을 둡니다. 그래야 core/ui_legacy_messages.py를 고칠 때 Native가 모르는 사이에 바뀌지 않습니다.

== UI-1 매크로 이름 통일 ==
- UI-1/01 quantgen_desktop/macro_narrative_language.py:6 'Macro sheet': 거시 지표표 → 매크로 지표 [R][실행]
- UI-1/02 translations.py:489 매크로 현황 → 삭제(A1-0c) [R]
- UI-1/03 translations.py:490 Macro v2|매크로 v2 → 그대로 [R][실행]
- UI-1/04 core/ui_legacy_messages.py:232
  - 'Macro sheet': 거시경제 관측 → 매크로 지표 [R]
  - 'Macro v2': 거시경제 v2 → 매크로 v2 [R]
- UI-1/05 core/ui_messages.py:139 'macro': 거시경제 → 매크로 (Flet 메뉴) [R]
- UI-1/06 macro_narrative_language.py:5 (우선 적용됨)와 translations.py:242: 'Macro · 시장 관측과 로컬 해설' → '매크로 · 시장 관측과 해설' [R]
- UI-1/07 macro_narrative_language.py:8-9와 translations.py:239 [R]
  - 현재: '이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 …'
  - 변경: '이 탭은 설명용 매크로 지표입니다. v2 오버레이·모델 카드·연구 등록부는 분석 도구 › 매크로 v2에서 확인하세요.'
  - 두 파일의 영어 원문이 조금 다르므로 둘 다 고칩니다.
- UI-1/08 macro_narrative_language.py:13 'Macro indicators': 거시 지표 → 매크로 지표 [R]
- UI-1/09 ui/macro_page.py:44-45 보기 목록 [S]: Overlay state / Model cards / Research register (영어) → 오버레이 상태 / 모델 카드 / 연구 등록부 (Native 번역과 같게) [실행: Native]
- UI-1/10 ui/research_home.py:257-258 [S]
  - "Macro의 Research register와 연구 카드에서…" → "매크로 화면의 연구 등록부와 연구 카드에서…"
  - "Macro 열기" → "매크로 열기"
- UI-1/11 테스트 tests/desktop_market_tabs_acceptance.py:22 '거시 지표표' → '매크로 지표' [R]

== UI-2 상태값 ==
- UI-2/01 OBSERVED → 정상 관측 (툴팁 '일별 종가 기준')
  - quantgen_desktop/watchlist.py:53 일별 관측 → 정상 관측 [R]
  - ui/research_home.py:172 일별 관측 → 정상 관측 [R]
  - 테스트 tests/desktop_watchlist_acceptance.py:88 [R]
  - 소유자가 원문 'OBSERVED'를 본 위치는 찾지 못했습니다(unverified). 앱 코드에서 이 값을 만드는 곳은 core/research/markets.py:107 하나이고, 두 앱 모두 번역합니다.
- UI-2/02 STALE → 오래된 자료
  - translations.py:34 FX 머리글 'Stale': 오래된 관측 여부 → 오래된 자료 [R][실행]
  - ui/research_home.py:172 '오래된 관측 · 확인 필요' → '오래된 자료 · 확인 필요' [R]
  - market_chart.py:1007 '오래된 값 · 조회 실패' → '오래된 자료 · 조회 실패' [S]
  - watchlist.py:52 오래된 자료는 그대로. 테스트 desktop_markets_watchlist_acceptance.py:131이 이 말을 고정합니다 [R].
  - watchlist.py:63 '수신 지연 · 마지막 값 유지'는 다른 상태라 그대로 둡니다 [R].
- UI-2/03 ui/research_home.py:172 UNAVAILABLE 조회 실패 → 조회 불가 (watchlist.py:51과 같게) [R]
- UI-2/04 app.py:1007-1009 Home 요약 [R]
  - 현재: '판정 {verdict} · 재현성 {reproducibility}' (NOT_RUN, PARTIAL이 원문 그대로)
  - 변경: '판정 미실행(NOT_RUN) · 재현성 부분(PARTIAL)'. 표시용 맵만 씁니다.
  - 같은 줄의 '관측 {last_observation}' 날짜를 보일지는 Q12.
- UI-2/05 app.py:1004-1005 보관함 실행 표 COMPLETED / NOT_RUN → 완료 / 미실행(NOT_RUN) [S]
- UI-2/06 translations.py:132 [R]
  - 현재: 'COMPLETED · 검증 NOT_RUN · 재현성 PARTIAL'
  - 변경: '완료 · 검증 미실행(NOT_RUN) · 재현성 부분(PARTIAL)'
- UI-2/07 translations.py:121 [R]
  - 현재: '재현성 PARTIAL · 데이터 빈티지/라이선스 미검증 · 비용 NOT_APPLIED · 검증 NOT_RUN'
  - 변경: '재현성 부분(PARTIAL) · 데이터 빈티지·이용 권리 미검증 · 비용 미반영(NOT_APPLIED) · 검증 미실행(NOT_RUN)'
- UI-2/08 translations.py:124, 126 (System) [R]
  - 'PASS / FAIL / NOT_RUN' → '통과(PASS) / 실패(FAIL) / 미실행(NOT_RUN)'
  - 'NOT_VERIFIED · NOT_FROZEN · NOT_INSPECTED · NOT_APPROVED' → '미검증(NOT_VERIFIED) · 미동결(NOT_FROZEN) · 미점검(NOT_INSPECTED) · 미승인(NOT_APPROVED)'
- UI-2/09 연결 상태 [R 537 / S 나머지]
  - core/research/connections.py:33, 53-56 → quantgen_desktop/connections.py:22에서 표시할 때 바꿈: CONFIGURED / NOT_CONFIGURED / REACHABLE / UNAVAILABLE → 설정됨 / 미설정 / 접속 확인 / 응답 없음
  - translations.py:537 'CONFIGURED는 설정의 존재만 뜻합니다' → '설정됨은 설정이 있다는 뜻일 뿐입니다'
- UI-2/10 market_tools.py:83 정적 차익거래 'Status' COMPUTED / 'NOT_RUN' → 계산 완료 / 미실행(NOT_RUN) [R]
- UI-2/11 market_tools.py:147 NOT_LOADED / NOT_APPLICABLE → 조회 전 / 해당 없음 [R]
- UI-2/12 KRX 상태 [R]
  - market_tools.py:266과 translations.py:529: 'UNAVAILABLE · 공급자 응답을 확인하세요. 대체 값을 생성하지 않습니다.' → '조회 불가 · 제공처 응답을 확인하세요. 대체 값은 만들지 않습니다.'
  - market_tools.py:279와 translations.py:530: 'EMPTY · 공급자가 빈 결과를 반환했습니다.' → '결과 없음 · 제공처가 빈 결과를 보냈습니다.'
- UI-2/13 SYNTHETIC → '합성(SYNTHETIC)' 또는 문장 안에서 '합성 데이터'
  - translations.py:525 'SYNTHETIC · 모든 시세는 합성 데이터입니다.' → '합성(SYNTHETIC) · 모든 시세가 합성 데이터입니다.' [R]
  - translations.py:527, 528, 541 [S]
  - 매크로 막대 라벨·표의 '· SYNTHETIC' → '· 합성' [S]
  - app.py:909 '합성 데이터 · SYNTHETIC' → '합성 데이터' (A3 UI9-2와 같은 줄) [S]
  - 테스트 [R]: desktop_macro_language_acceptance.py:144가 '금 · SYNTHETIC'을 그대로 비교합니다. :96과 desktop_rates_language_acceptance.py:31은 'SYNTHETIC' 포함만 보므로 '합성(SYNTHETIC)'이면 통과합니다.
- UI-2/14 macro_records.py [R 283 / S 나머지]
  - :251 engine ARMED, REJECT, BUILD_AS_INSURANCE, NOT_FROZEN → 활성(ARMED) 등
  - :283 '{kind} · NOT_LOADED' → '{kind} · 조회 전'
- UI-2/15 Strategy 판정 줄 'WITHHELD' → 판정 보류(WITHHELD) [S]
- UI-2/16 FX SABR '수치 해법 CONVERGED' → '수치 해법 수렴' [S]
- UI-2/17 paper.py:281, 288, 293, 296와 translations.py:228, 477-478 [S, 실행 안 함]: PAUSED → 일시 정지, CONFIRMED → 확인 완료, HALT 확인 → 긴급 정지 확인, '엔진 Arm' → '엔진 활성화'
- UI-2/18 Flet 상태값 [S]
  - ui/research_home.py:151, 263 COMPLETED / RUNNING / FAILED → 완료 / 실행 중 / 실패
  - ui/components.py:165-171 입력 상태 칩: ok / warmup / disputed / not run / stale / missing … → 정상 / 준비 중 / 이의 제기 / 미실행 / 오래된 자료 / 누락 / 잠정값 거부 / 세션 불일치 / 합성 데이터 거부 / 안전 차단
- UI-2/19 translations.py:572 '직접 입력한 금리: {rates}'에서 실행 중 값 'none' → '없음' [R 템플릿 / S 값]

== UI-6b 금리·KRX의 어색한 번역 ==
- UI-6b/01 Rates 곡선 비교 기간 [R][실행]
  - translations.py:405 'Lookback · sessions': 관측 창 · 거래일 → 변화 비교 기간 (거래일)
  - rates.py:65 결과 행 'Lookback' (영어) → 비교 기간
  - rates.py:73 머리글 'Change · {n}d' → '{n}거래일 변화' (템플릿)
- UI-6b/02 Signals 입력란 [R]
  - translations.py:403: 빠른 이동평균 / 관측 창 / RSI 기간 → 단기 이동평균 · 모멘텀 기간 · RSI 기간
  - translations.py:404: 느린 이동평균 / RSI 청산 · 모멘텀에는 미사용 → 장기 이동평균 · RSI 청산 기준 · 모멘텀에는 쓰지 않음
- UI-6b/03 'Sessions' [R][실행]
  - translations.py:363 거래일 → 거래일 수
  - core/ui_legacy_messages.py:251 관측 수 → 거래일 수
- UI-6b/04 'Horizon · sessions' [R]
  - translations.py:62 분석 기간 · 거래일 → 분석 기간 (거래일)
  - core/ui_legacy_messages.py:228 분석 기간 · 관측 수 → 분석 기간 (거래일)
- UI-6b/05 translations.py:357 기간 거래일 · 공란 = 만기 → 보유 기간 (거래일) · 비우면 만기까지 [R]
- UI-6b/06 translations.py:333 리밸런싱 · 거래일 → 리밸런싱 주기 (거래일) [R]
- UI-6b/07 display_prose_catalog.py:82 'Paths / sessions': 경로 수 / 거래일 → 경로 수 / 거래일 수 [R]
- UI-6b/08 '공란 =' 표기 [R]
  - translations.py:355 '만기 · 공란 = 최근 만기' → '만기 · 비우면 최근월물'
  - :356 '금리 % · 공란 = 공급자' → '금리 % · 비우면 제공처 값'
  - :320 → '상대(국내) 금리 % · 비우면 제공처 값'
  - :321 → '기준(외국) 금리 % · 비우면 제공처 값'
  - :346 '쿠폰 % · 공란 = 역산' → '쿠폰 % · 비우면 역산'
- UI-6b/09 rates.py:60 출처 줄 '… · 80 observations · bootstrap' (영어) → '관측 80개 · 부트스트래핑' [R]. 이 줄을 화면에 둘지는 A3 UI-12에서 정합니다.
- UI-6b/10 'Quote' [R][실행]
  - translations.py:371 호가 → 현재가
  - 이 키는 KRX 도구 콤보와 시세 표 제목(market_tools.py:133, 272)에 함께 쓰입니다.
  - 같은 '호가'라도 FX·레포 문장은 매수·매도 호가라 그대로 둡니다. 관련 테스트: desktop_fx_language_acceptance.py:62, desktop_carry_language_acceptance.py:39, desktop_bonds_portfolio_language_acceptance.py:44 [R].
- UI-6b/11 market_tools.py:276-277 KRX 일별 표 [R]
  - 머리글은 제공처 키입니다: date / open / high / low / close / volume → 일자 / 시가 / 고가 / 저가 / 종가 / 거래량 (머리글 표시 맵)
  - 표 제목 'Observations'(관측) → 일별 시세 (화면별 맵)
  - :278 '{n} rows · first 300 displayed' → '{n}행 · 처음 300행 표시' (카탈로그에 있는지는 확인 안 함)
- UI-6b/12 translations.py:443 'Observations': 관측 → 관측 수 (개수일 때) [R][실행]
- UI-6b/13 Flet KRX 화면 ui/krx_page.py [S]
  - :23-28 도구: Quote / Daily OHLCV / Disclosures (DART) / Financials (DART) / Whole-market snapshot / Index levels → 현재가 / 일별 시세 / 공시 (DART) / 재무제표 (DART) / 전 종목 시세 / 지수 시세
  - :35-37, 108-116, 126-127, 136-137, 146-147, 156-158, 167-168 머리글 → 용어집 2절 (종목코드, 전일 대비, 등락률, 시가총액, 보고서명, 제출인, 접수번호, 계정과목, 당기, 전기, 시장 구분, 지수명 …)
- UI-6b/14 Flet ui/rates_page.py [S]
  - :383 'Lookback (sessions)' → 변화 비교 기간 (거래일)
  - :407 'Horizon (years)' → 분석 기간 (년)
  - :409 'Threshold' → 임계값

== UI-10 필드·측정값 오역, 자산별 혼용, 표준 용어집 ==
- UI-10/01 'Field' → 항목
  - core/ui_legacy_messages.py:253 'Fields':'필드','Field':'필드' → '항목' [R][실행]
  - translations.py에도 'Field|항목'을 둡니다.
  - 이 값이 보이는 곳: market_tools.py:133(ETF), :272(KRX), macro_records.py:251.
- UI-10/02 translations.py:566 'Metric|측정 항목' → 항목 [R]. 테스트 tests/desktop_language_acceptance.py:77 [R]. (Q4)
- UI-10/03 translations.py:427 'Metrics|측정값' → 주요 지표 [R] (Q4)
- UI-10/04 market_tools.py:272 KRX 시세 행 이름(asdict 키) [R 줄 / S 키 목록]
  - 이름 열에 표시 맵을 둡니다. 소문자 키가 다른 카탈로그 항목과 겹치지 않게 화면별 맵으로 둡니다.
  - ticker, name, price, change, change_pct, volume, market_cap, high, low, open, currency, per, eps, sector, listed_shares → 종목코드, 종목명, 현재가, 전일 대비, 등락률, 거래량, 시가총액, 고가, 저가, 시가, 통화, PER, EPS, 업종, 상장주식수
- UI-10/05 market_tools.py:133 ETF 시세 행 [R]: price, nav, premium_pct, tracking_error_pct, cu_units, lp_holding_pct → 현재가, 순자산가치(NAV), 괴리율 %, 추적오차율 %, 설정단위(CU), LP 보유 비율 %
- UI-10/06 market_tools.py:224-226 ETH/BTC 행 [R]: n, last_ratio, adf_p, z_2y, verdict → 관측 수, 최근 비율, ADF p값, 2년 z점수, 검증 판정
- UI-10/07 macro_records.py [R]
  - :132 QTreeWidget 머리글 ['Field','Recorded value']는 LanguageController가 바꾸지 않습니다. display()를 직접 불러 항목 / 기록값으로 표시합니다.
  - :251 표 머리글도 같은 말로 바꾸고, 'Recorded value|기록값' 항목을 더합니다.
- UI-10/08 'Model' → 모형 (모델 카드는 고유명이라 그대로)
  - translations.py:57 모델 → 모형 [R][실행]
  - Flet(core/ui_legacy_messages.py:227, core/ui_messages.py:161)은 이미 모형 [R]
- UI-10/09 'Provider' → 제공처 [R]
  - translations.py:100 공급자 → 제공처
  - core/ui_messages.py:113 공급처 → 제공처
  - core/ui_legacy_messages.py:233 공급처 → 제공처
  - 한국어 원문 속 공급자·공급처: translations.py:320, 321, 356, 529, 530 [R]; watchlist.py(21줄), core/research/stock_profile.py, data_rights 트리 머리글, core/ui_legacy_messages.py:15, 34, 79, 80, 180, 187 [S]
  - 테스트 [R]: desktop_market_tabs_acceptance.py:53, desktop_markets_watchlist_acceptance.py:168, desktop_watchlist_acceptance.py:101은 공급자·공급처가 화면에 없음을 확인합니다. 바꾼 뒤에도 같은 보호가 되도록 '제공처'도 검사에 넣어야 합니다.
- UI-10/10 'Symbol' → 종목코드
  - translations.py:58 '종목 코드' → '종목코드'; :59 '종목코드 · 쉼표로 구분' [R]
  - translations.py:60 'Symbols · pairs는 y, x 순서' → '종목코드 · 페어는 y, x 순서' [R]
  - core/ui_messages.py:146과 core/ui_legacy_messages.py:227, 257 '종목·통화쌍' → '종목코드' (FX 화면만 '통화쌍') [R]
- UI-10/11 'Drift' → 기대수익률 가정 (드리프트)
  - translations.py:61 추세 가정 [R][실행]
  - core/ui_legacy_messages.py:227 드리프트 [R]
- UI-10/12 core/ui_legacy_messages.py:228 [R]
  - Paths 경로 수 → 시뮬레이션 경로 수
  - Seed 시드 → 난수 시드
  - :229 합성 시연 → 합성 데이터 시연 [S]
  - :230 위험프리미엄 → 위험 프리미엄 [S]
  - :231 '표본 평균 · 잡음 주의' → '표본 평균 · 추정 오차 유의' [S]
- UI-10/13 core/ui_messages.py:152 'light' 밝게 → 라이트; :153 'dark' 어둡게 → 다크 [R][실행]
- UI-10/14 메뉴 이름 [R]
  - core/ui_messages.py:14 리서치 홈 → 연구 홈. 테스트 tests/research_home_acceptance.py:93, 166.
  - :18 연구 기록과 core/ui_legacy_messages.py:205 연구 라이브러리 → 연구 보관함
  - :21 지표 가이드 → 기술지표 가이드
  - translations.py:170 'Connections|연결' → 데이터 연결
- UI-10/15 'Signals' → 기술적 분석 (Q7) [R]
  - translations.py:485 신호
  - core/ui_messages.py:129 기술적 관측
- UI-10/16 'Paper Trading' → 모의투자 (Q8)
  - translations.py:222 모의매매 [R]
  - core/ui_legacy_messages.py:232 모의매매 [R]
  - main.py:216 'Execution · simulated' 모의 실행 [S]
  - translations.py:223 'Paper Trading · 실제 주문 없음' → '모의투자 · 실제 주문 없음' [R]
- UI-10/17 같은 영어, 다른 뜻 (A1-0b 화면별 맵) [R][실행]
  - rates.py:100 스왑션 'Forward', :106 Caplets 머리글 'Forward': 선물환 → 선도금리. FX(translations.py:456)는 선물환 그대로.
  - strategy.py:64 축 'Equity': 주식 → 누적 가치. 'OOS observations' → 표본 외 관측.
  - market_tools.py:150 'Equity · starts at 1' → '누적 가치 · 시작값 1'.
  - rates.py:82 'Component': 구성 지표 → 주성분.
  - fx.py:38 'Last': 최근값 → 최종 관측일.
  - structuring.py:61 'Risk': 위험 → 민감도 (macro_narrative_language.py:12 'Risk':'위험'이 앱 전체에 적용되고 있음).
  - core/ui_legacy_messages.py:238 'Close':'종가'가 'close' 닫기(ui_messages.py:119)를 가립니다. 'Close'를 화면별로 나눕니다.
  - translations.py:433 'Point' 지점 → 구분.
  - translations.py:322 'Tenor' 기간 → 만기.
- UI-10/18 'Strike' → 행사가격
  - core/ui_legacy_messages.py:250 'Strike %':'행사가 %', 'Strike':'행사가' → 행사가격 %, 행사가격 [R]
  - display_prose_catalog.py:72 '행사가 범위', :77 '인접 행사가' → 행사가격 [R]
  - display_prose_catalog.py:108 '행사가 {strikes}개' → '행사가격 {strikes}개' [R]
  - core/research/option_disclosure.py와 rates_narrative.py의 '행사가' [S]
- UI-10/19 '내재 변동성' → '내재변동성': display_prose_catalog.py:71-72 [R]
- UI-10/20 'Sharpe' → 샤프 지수 (Q5)
  - translations.py:462 '최대 Sharpe' → '최대 샤프 지수' [R]
  - 영어로 남은 표 행 'Sharpe'(ETF, FX 캐리, 포트폴리오, Signals, Strategy)에 항목을 더합니다 [실행].
  - bonds_portfolio_narrative.py:22, 89 '샤프비율' → '샤프 지수' [R]
  - market_narrative_language.py:67, fx_narrative.py:56, core/research/sleeve_disclosure.py [S]
  - 테스트 [R]: etf_sleeve_disclosure_acceptance.py:145, 303, 304, 315, 316, 326, 340, 356, desktop_bonds_portfolio_language_acceptance.py:83
- UI-10/21 구조화 상품 이름 [R]
  - translations.py:335 원금보장형 노트 → 원금보장형 구조화 상품
  - :336 역전환형 노트 → 역전환형 구조화 상품
  - display_prose_catalog.py:141-142 '원금보장형 상품' / '역전환형 상품' → 위와 같은 이름
  - :143 '이중통화 예금' → '이중통화예금(DCD)'
- UI-10/22 '액면 100당' 표기 [R]
  - translations.py:339 '발행 가격 · 액면 100당' → '발행가격 · 액면 100당'
  - display_prose_catalog.py:44 '값 · 100당' → '가치 · 액면 100당'
  - :46 '공정가치 · 100당' → '공정가치 · 액면 100당'
- UI-10/23 표면금리 [R]
  - translations.py:505 '채권 쿠폰 %' → '채권 표면금리 %'
  - :275 표면금리 %는 그대로
- UI-10/24 'Annual' [R]: core/ui_legacy_messages.py:248 연간 → 연 1회 (Native translations.py:269와 같게)
- UI-10/25 'Volatility regime' → 변동성 국면: display_prose_catalog.py:127과 translations의 변동성 상태 [R][실행]. core/ui_legacy_messages.py:255는 이미 국면 [R].
- UI-10/26 core/ui_legacy_messages.py [R]
  - :241 'Reason' 이유 → 사유
  - :237 'At bound' 경계값 도달 → 포트폴리오는 '비중 상한 도달', GARCH는 '추정 경계 도달'
  - :251 'Calendar days' 달력 일수 → 달력일 수. translations.py:504 달력일도 같게.
- UI-10/27 Signals 점수 [R]
  - core/ui_legacy_messages.py:239 'Composite' 종합 관측값 → 종합 점수
  - :240 'Signal components' 지표별 관측값 → 지표별 점수
  - :241 'Stance' 관측 방향 → 방향
  - :245 강한 상승 관측 … → 강한 상승 우위 / 상승 우위 / 중립 / 하락 우위 / 강한 하락 우위
  - :254 '가격과 SMA50의 위치' → '50일 이동평균 대비 가격' (200일도 같게)
- UI-10/28 'Monte Carlo' → 몬테카를로 [R]
  - translations.py:84 '이번 세션의 Monte Carlo · 투자 판정과 별개'
  - :120 '현재 저장 대상은 Monte Carlo 실행입니다'
  - :93 'Quant Lab에서 연구 시작 →' → '몬테카를로에서 연구 시작 →'
  - :104 'Quant Lab · 기존 계산 엔진으로 가격 분포 분석' → '몬테카를로 · 가격 분포 분석'
  - app.py:526 탭 'Monte Carlo'에 Native 항목을 둡니다(지금은 Flet 카탈로그로 넘어감) [R]
- UI-10/29 곡선 변화 유형 한 표 (Q17) [R]
  - rates_narrative.py:12-14 '금리 하락·기울기 확대' 등과 macro_narrative_language.py:18-19 '금리 하락·곡선 가팔라짐' 등을 '강세 스티프닝 (금리 하락·장단기 금리차 확대)' 계열 하나로 맞춥니다.
  - 두 모듈이 같은 표를 씁니다.
- UI-10/30 macro_narrative_language.py:11 'Curve' 수익률곡선 → 수익률 곡선 [R]
- UI-10/31 미국채 표기
  - 매크로 표 '미국채 2y'와 서술문 'UST' → '미국채 2년물' / '미국채' [S]
  - watchlist.py:41 '미국 10년 금리' → '미국채 10년물 금리' [R]
- UI-10/32 Flet 문장
  - ui/research_home.py:157, 158, 203, 259, 260 'Quant Lab' → 분포 분석; :230 'Strategy Lab' → 전략 실험실 [S]
  - :228-232 'Data source를 synthetic, Symbol을 SPY…' → '데이터 출처를 합성 데이터 시연, 종목코드를 SPY, 모형을 GBM으로…' [S]
- UI-10/33 Flet 결과 표 머리글이 한 줄 안에서 한·영 혼용 [S]
  - ui/bonds_page.py:132-138, 181
  - ui/structuring_page.py:183, 191
  - ui/krx_page.py:126-127, 156-158
  - ui/macro_page.py:43
  - ui/rates_page.py:137
  - ui/fx_page.py:286, 354-355
  - 바꿀 말은 용어집 2~9절을 따릅니다.
  - Flet 화면 원문 중 영어로 남은 것은 전부 1,556개입니다. 목록: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/flet_english_in_korean.tsv (범위는 Q11)
- UI-10/34 Flet 차트(ui/fcharts.py, ui/qcharts.py, ui/xcharts.py의 59곳)는 영어 글자가 PNG에 박힙니다. 차트를 만드는 함수에 언어를 넘기고, 언어를 바꾸면 다시 그립니다 [S].
- UI-10/35 문체: market_chart.py의 해요체 20줄(예 :379) → 합니다체 (Q13) [S]

== UI-11a 채권 지표·그릭스·레그 분해 ==
- UI-11a/01 bonds.py:82-87 지표 이름 [R][실행]
  - 현재는 bonds.py:51에서 localize_columns를 부르지 않아 모두 영어입니다. localize_columns(self.metrics,(0,))를 더하고 카탈로그 항목을 둡니다.
  - Price → 가격 (액면 100당)
  - Yield → 만기수익률
  - Macaulay duration → 맥컬리 듀레이션
  - Modified duration → 수정 듀레이션
  - Convexity → 컨벡시티
  - DV01 → DV01
  - z-spread → Z-스프레드
  - Curve price → 곡선 기준 가격
  - 'Carry · {h} years' → '캐리 · {h}년' (템플릿)
  - Roll-down → 롤다운
  - Carry + roll → 캐리+롤다운
  - Breakeven → 손익분기 금리 변화
- UI-11a/02 bonds.py:83-84, 87 값의 단위 [R]
  - ' years' → '년', ' currency / bp' → ' (통화/bp)'
  - 보통 표 칸은 번역 대상이 아니므로 언어에 맞춘 표시용 포맷이 필요합니다. 숫자는 그대로입니다.
  - 내보내기는 칸 글자가 아니라 객체를 씁니다(bonds.py:106-108) [S].
- UI-11a/03 bonds.py:53-54 머리글 [R]
  - 'Key tenor · years' → '주요 만기 · 년'
  - 'DV01 · currency / bp' → 'DV01 · 통화/bp'
  - Scenario / 'Shock · bp' / P&L / 'P&L %' → 시나리오 / 금리 충격 · bp / 손익 / 손익률 %
  - 'New price'는 이미 '새 가격'
- UI-11a/04 bonds.py:52, 88 차트 [R]
  - 축 'Yield (%)' → '수익률 (%)', 'Price per 100' → '액면 100당 가격'
  - 범례 'Duration tangent' → '듀레이션 접선'
- UI-11a/05 bonds_portfolio_narrative.py:56-57 [R]: 매콜리 → 맥컬리, 볼록성 → 컨벡시티 (Q6)
- UI-11a/06 structuring.py:61 [R][실행]
  - 제목 'Greeks'(영어) → 민감도(그릭스)
  - 머리글 'Risk'(위험) → 민감도 (A1-0b)
- UI-11a/07 structuring.py:63-64 [R]
  - 'Maturity payoff' → 만기 손익 구조
  - 'Payoff' → 손익
  - 'Realized 10y–2y spread · bp' → 실현 10y–2y 스프레드 · bp
  - 'Underlying at maturity' → 만기 기초자산 가격
  - 'Per 100 notional' → 액면 100당
- UI-11a/08 structuring.py:66 [R]
  - 'Leg decomposition' → 구성요소별 분해
  - 머리글 'Value · per 100' → 가치 · 액면 100당
  - Leg / Kind / Detail은 이미 구성요소 / 종류 / 상세 [실행]
- UI-11a/09 structuring.py:68 'Hedge sheet' → 헤지 내역 [R]. 머리글 상품 / 수량 / 단위 / 근거는 이미 번역됨 [실행].
- UI-11a/10 structuring.py:48 'Leverage' → 레버리지; 구성요소 이름 'ATM call' → ATM 콜 [S]
- UI-11a/11 translations.py:533 [R]
  - 현재: 'Hedge 부호: … 실제 주문을 실행하지 않습니다.'
  - 변경: '헤지 부호: … 실제 주문은 내지 않습니다.'
- UI-11a/12 rates.py:86-88 스왑 [R]
  - Swap → 스왑
  - Par rate → 스왑금리
  - Fixed → 고정금리
  - PV → 현재가치
  - 'DV01 · +1bp P&L' → 'DV01 · +1bp 손익'
  - Annuity → 애뉴이티
  - 'Carry · first period' → 캐리 · 첫 기간
  - 'Roll-down · 1y' → 롤다운 · 1년
- UI-11a/13 rates.py:89-90 [R]
  - 'Key-rate DV01' → 만기별 DV01
  - 머리글 'Currency / bp' → 통화/bp
  - 'Forward swaps' → 선도 스왑금리
- UI-11a/14 rates.py:93, 100-102 스왑션 [R]
  - 'Premium / notional' → 프리미엄 · 명목금액 대비
  - Forward → 선도금리
  - Annuity → 애뉴이티
  - 'Delta · per +1bp' → 델타 · +1bp당
  - 'Gamma · per bp²' → 감마 · bp²당
  - 'Vega · {unit}' → 베가 · {unit} (템플릿)
  - 'Theta · 1 day' → 세타 · 1일
  - 'Other-model vol' → 다른 모형 기준 변동성
- UI-11a/15 rates.py:103 '{expiry} × {tenor} · Payer/Receiver' → '… · 고정금리 지급형 / 수취형' (템플릿) [R]
- UI-11a/16 rates.py:106 Caplets [R]
  - 머리글 'Start · y', 'End · y', Forward, Premium → 시작 · 년, 종료 · 년, 선도금리, 프리미엄
  - 제목 → 캐플릿
- UI-11a/17 rates.py:73 'Curve table' → 수익률 곡선 표 [R][실행]
  - 머리글: Tenor 기간 → 만기, Zero → 무이표 금리, DF → 할인계수, Par → 파 금리, '1y forward' → 1년 선도금리
- UI-11a/18 rates.py:65 [R]
  - Shape → 곡선 형태
  - Regime → 변화 유형
  - 'NS/NSS fit RMSE' → NS/NSS 적합 오차(RMSE)
  - 값 r.shape / r.regime('normal', 'bull steepener')는 영어 그대로 나옵니다. SHAPES / REGIMES 맵으로 표시합니다.
- UI-11a/19 rates.py:81-83 PCA [R]
  - 'PCA loadings' → 주성분 적재값
  - 축 'Tenor · years' → 만기 · 년, 'Loading' → 적재값
  - 'PCA variance' → 주성분 설명력
  - 머리글: 주성분 / 설명 비율 / 최근 점수
  - 이름 level / slope / curvature → 수준 / 기울기 / 곡률 (rates_narrative.py:15 COMPONENTS)
- UI-11a/20 rates.py:111-124 금리 모형 시뮬레이션 [R]
  - 'Kappa · /year' → 평균회귀 속도 κ · /년
  - 'Half-life · years' → 반감기 · 년
  - Theta → 장기 평균 θ
  - Sigma → 변동성 σ
  - Initial rate → 초기 금리
  - Terminal mean → 만기 시점 평균
  - 'P(terminal > threshold)' → 만기 금리가 임계값을 넘을 확률
  - Threshold → 임계값
  - 축 Years / 'Short rate · %' → 년 / 단기금리 · %
  - 'Horizon curve · median path' → 분석 기간 말 곡선 · 중앙 경로
  - 'Model zero' → 모형 무이표 금리
  - 'Horizon PV distribution' → 분석 기간 말 현재가치 분포
  - Count → 빈도
  - 'Paths per bin' → 구간별 경로 수
- UI-11a/21 rates.py 콤보 표시명 [R 12, 15 / S 19, 21] (데이터 ID는 그대로)
  - :12 bootstrap / nelson_siegel / svensson → 부트스트래핑 / Nelson-Siegel / Svensson
  - :15 swaption / cap / floor → 스왑션 / 캡 / 플로어
  - :19 vasicek / cir / hull_white → Vasicek / CIR / Hull-White
  - :21 none / bond / swap → 없음 / 채권 / 스왑
- UI-11a/22 market_tools.py:51-83 Derivatives [R]
  - :51 'Futures & volatility' → 선물·변동성
  - :71 'Implied volatility smile' → 내재변동성 스마일
  - :75 'Risk-neutral density' → 위험중립 밀도; 'Q density' → Q 밀도; 축 'Index points' / 'Density' → 지수 포인트 / 밀도
  - :76 'Hedge simulation' → 헤지 시뮬레이션
  - :77 'Engine', 'Paths / sessions' → 엔진, 경로 수 / 거래일 수
  - :82 'Static arbitrage checks' → 정적 차익거래 점검; 머리글 Check / Violations / Tests / Status → 점검 항목 / 위반 수 / 검사 수 / 상태
  - :83 키 call_vertical / call_butterfly / put_* → 콜 수직 스프레드 / 콜 버터플라이 / 풋 수직 스프레드 / 풋 버터플라이
- UI-11a/23 core/ui_legacy_messages.py:247 'CTD DV01 / contract' 계약당 CTD DV01은 그대로 두고, Native의 '계약당 최저가인도채권 DV01'을 이것과 같게 [R 247 / S Native]
- UI-11a/24 Flet [S]
  - ui/bonds_page.py:132-138, 157-167, 181, 194-200
  - ui/structuring_page.py:61-63, 181-192
  - ui/rates_page.py:229-235, 265-269
  - ui/fx_page.py:275, 286-290
  - 위 Native와 같은 용어로 바꿉니다. 영어 원문이 Native와 달라('Delta (per +1% spot)'와 'Delta · per +1% spot') 같은 키를 쓸 수 없으므로 Flet 쪽 항목을 따로 둡니다.

== UI-14 / UI-15 ==
- UI-14/01 '설계/검증' [R]
  - translations.py:46 '설계 및 검증' → '설계/검증'
  - core/ui_messages.py:16 '설계·검증' → '설계/검증'
  - translations.py:470 안내문의 메뉴 이름도 맞춥니다 [S]
  - 영어 'Build && Test' 테스트(desktop_language_acceptance.py:62)는 영향 없음 [S]
- UI-15/01 '분석' (Q1) [R]
  - translations.py:47 '포트폴리오 및 위험' → '분석'
  - core/ui_messages.py:17 '포트폴리오·위험' → '분석'
  - core/ui_legacy_messages.py:205 '포트폴리오 · 위험'(ui/research_home.py:224 Home 바로가기) → '분석'
  - 왼쪽 메뉴 폭은 가장 긴 이름에 맞춰 자동으로 줄어듭니다(app.py:311-330) [S]

== 13-8/b2/c/b 남은 모형 해설·제공처 메모·인라인 문구 ==
- 13-8/01 app.py:903-908 몬테카를로 지표 행 [R]
  - 지금은 'Spot'만 번역됩니다. localize_columns와 카탈로그 항목을 둡니다.
  - 'Sample vol (ann.)' → 표본 변동성 (연율)
  - 'Next-session vol (ann.)' → 다음 거래일 변동성 (연율)
  - 'P(loss)' → 손실 확률
  - 'VaR 95 / CVaR'는 그대로
  - 'Paths / horizon / seed' → 경로 수 / 분석 기간 / 시드
  - 'P(terminal ≥ target)' → 목표가 이상 마감 확률
  - 'Horizon-average vol (ann.)' → 기간 평균 변동성 (연율)
- 13-8/02 app.py:593 위험 표 머리글 [R]: Symbol / Model / P(loss) / VaR 95 / CVaR / Source → 종목코드 / 모형 / 손실 확률 / VaR 95 / CVaR / 출처. 출처 열을 보일지는 Q12.
- 13-8/03 app.py:909-929 몬테카를로 메모 [S]
  - localized_text로 한국어 판을 둡니다(부트스트랩 공시 BOOTSTRAP_TEXT_KO와 같은 방식).
  - 배치·줄이기는 A3 UI-9가 맡고, A1은 문구만 맡습니다.
  - 테스트 [S]: desktop_acceptance.py:390, 404, mc_bootstrap_disclosure_acceptance.py:530-556
- 13-8/04 '시장 데이터를 쓰지 않음' 메모 [S]
  - bonds_portfolio_narrative.py:131-133, rates.py:60, structuring.py:40: 'Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.' → '모의 미국채 파 곡선(Nelson-Siegel 랜덤워크) · 시장 데이터 제공처를 쓰지 않았습니다.'
  - 두 번 나오는 문제는 A3 UI11b-5에서 한 번만 보이게 합니다.
  - 'Simulated series (GBM…) — no market data provider was used.' → '모의 시계열(GBM, μ=…, σ=…) · 시장 데이터 제공처를 쓰지 않았습니다.'
- 13-8/05 rates.py:91, 94-95 [R]
  - '{n} notional · {f} payments/year · single curve · ACT/365F' → '명목금액 {n} · 연 {f}회 지급 · 단일 곡선 · ACT/365F'
  - '{model} · {vol} normal|Black · {n} notional' → '{model} · 정규 변동성 {vol} | Black 변동성 {vol} · 명목금액 {n}'
  - r.note는 영어 [S]
- 13-8/06 rates.py:118 'Seed 7 · {n} paths' → '시드 7 · 경로 {n}개' [R]. params.note와 r.note [S].
- 13-8/07 strategy.py [R 12, 35, 55-64 / S 나머지]
  - :35 'Study scorecard' → 연구 성적표; 머리글 Card / Kind / Decision / Reason → 카드 / 종류 / 판정 / 사유
  - :55-62 'Validation statistics' → 검증 통계. 행:
    - 'OOS Sharpe' → 표본 외(OOS) 샤프 지수
    - '90% interval' → 90% 구간
    - 'Deflated Sharpe' → 디플레이티드 샤프 지수(DSR)
    - 'PBO' → 과적합 확률(PBO)
    - 'OOS / IS' → OOS/IS 비율
    - '2× cost Sharpe' → 비용 2배 샤프 지수
    - 'Positive years' → 수익 연도 비율
    - 'Plateau' → 안정 구간
    - 'Plateau edge' → 안정 구간 경계
    - 'Benchmark Sharpe' / 'Benchmark difference' / 'Benchmark p' → 벤치마크 샤프 지수 / 벤치마크 대비 차이 / 벤치마크 p값
    - 'Haircut Sharpe' → 헤어컷 샤프 지수
  - :63-64 범례 Strategy / Benchmark → 전략 / 벤치마크; 'Walk-forward equity' → 워크포워드 누적 가치
  - :12 콤보 synthetic / auto / kis / fmp / yfinance / crypto → 합성 데이터 시연 / 자동 / KIS / FMP / Yahoo / 가상자산 거래소
  - 판정 사유 문장 [S]
- 13-8/08 macro_records.py [R 109, 182, 200-201 / S 나머지]
  - :109 'Macro dry run' / 'Macro live decision' → 매크로 모의 점검 / 매크로 실데이터 판단
  - :182 'Gate package:' → 게이트 패키지:
  - :200 머리글 Card / Verdict / Disposition / Reason / Label / Book → 카드 / 판정 / 처리 / 사유 / 라벨 / 북
  - :201 'Tech-fund drafts · NOT_RUN / not a recommendation' → 기술주 펀드 초안 · 미실행(NOT_RUN) · 권장 아님
  - :201-217, 261-279의 제목 약 40개 → 용어집 9절
  - ui/macro_cards_view.py:32-34 카드 설명과 DISCLAIMERS, WEIGHT_CAPTION
- 13-8/09 market_tools.py:204-227 Crypto [R]
  - 'Premium / volatility' → 프리미엄·변동성
  - 'Kimchi premium · %' → 김치 프리미엄 · %
  - 'Premium z' → 프리미엄 z점수
  - 'AR(1) amplitude half-life · observations' → AR(1) 진폭 반감기 · 관측 수
  - 차트 'Kimchi premium' / 'Premium %' / 'Days' / 'Premium · %' → 김치 프리미엄 / 프리미엄 % / 일 / 프리미엄 · %
  - 'Perpetual funding' → 무기한 선물 펀딩비
  - '7-day mean annualized %' → 7일 평균 연율 %
  - 'Annualized · %' → 연율 · %
  - 'Weekday observations' → 요일별 관측; 머리글 Day / n / 'Mean return %' / 'Vol %' / 'Mean volume' → 요일 / 관측 수 / 평균 수익률 % / 변동성 % / 평균 거래량
  - Mon…Sun → 월…일
- 13-8/10 market_tools.py:130, 145-150 ETF [R]
  - 'ETF price / NAV' → ETF 가격 / NAV; 축 'Observations' / 'Price / NAV' → 관측 / 가격·NAV
  - 'Descriptive sleeve backtests' → 전략별 백테스트 (설명용)
  - 머리글 Sleeve / Sharpe / 'Max drawdown' / 'Study decision' → 전략 / 샤프 지수 / 최대낙폭 / 연구 판정
  - 키 trend / vol_target / buy_hold → 추세 전환 / 변동성 목표 / 매수 후 보유
  - 'Trend switch vs buy & hold' → 추세 전환 대 매수 후 보유; 범례 'Trend' → 추세 전환
  - 축 'Sessions' → 거래일
- 13-8/11 Portfolio [R]
  - portfolio.py:69 str(p.converged) True/False → 예/아니오
  - portfolio.py:70 ' · selected' / ' · comparison' → ' · 선택' / ' · 비교'
  - portfolio.py:26 콤보 auto / fmp / kis / yfinance / synthetic → 자동 / FMP / KIS / Yahoo / 합성 데이터 시연
  - bonds_portfolio_narrative.py:87 objective.replace('_','-')('max-sharpe 포트폴리오') → 목적 이름 맵(최대 샤프 지수 / 최소분산 / 리스크 패리티 / 동일 비중)
  - 'THREE은' 조사 문제 [S]
  - bonds_portfolio_narrative.py:106 '선택 목적 {objective}' → '선택 목적: {목적 이름}'
- 13-8/12 한·영이 섞인 카탈로그 값 [R 60, 163, 189, 223, 241-244, 526 / S 나머지]
  - 화면 제목: translations.py:163, 241, 242, 243, 244, 189, 223 'Bonds · / Rates · / Macro · / Signals · / Structuring · / Rules · / Paper Trading ·' → 채권 · / 금리 · / 매크로 · / 기술적 분석 · / 구조화 상품 · / 규칙 · / 모의투자 ·
  - :129 'Symbol과 유한한 양수 Target' → '종목코드와 0보다 큰 목표 가격'
  - :135, 164, 167 'Price/Yield' → 가격/수익률 (bonds.py:48 입력 안내 포함)
  - :153 'Frontier' → 효율적 투자선
  - :159 'equal_weight는' → '동일 비중은'
  - :161 'solver converged=True' → '최적화 수렴: 예'
  - :190, 478 '엔진 Arm' → 엔진 활성화
  - :235 'Live 실행' → 실데이터 실행
  - :205-206 'UTC offset' → UTC 오프셋
  - :526 'Last prints only · 장외/마감 시 호가는…' → '최종 체결가 기준 · 장외·마감 시세는 동시에 체결할 수 있는 가격이 아닙니다.'
  - :545, 554-556 'gate / book / Research register / refusal' → 게이트 / 북 / 연구 등록부 / 거부 북
  - display_prose_catalog.py:106 'OOS 차입'과 :187 [R 106 / S 187]
  - macro_narrative_language.py:5, 8 → UI-1/06, UI-1/07
- 13-8/13 숫자와 조사 [R]
  - rates_narrative.py:27 '오 년 단리' → '5년 단리'
  - :29 '향후 일 년간' → '향후 1년간'
  - :56 '일 년 롤다운' → '1년 롤다운'
  - :49 '{s.label}은'('10y payer은') → '{표시 이름}은'. 예: '10년 고정금리 지급 스왑은'. label 맵이 필요합니다.
  - core/ficc/forward_conventions.py:9 '오 년' [S]
  - display_prose_catalog.py:133-135 'RSI {rsi}은 과매수이며…' → 'RSI {rsi}: 과매수 구간이며 상승 쪽으로 치우쳐 있습니다.' (과매도, 중립도 같게)
- 13-8/14 Flet [S]
  - 지역 서술 18곳이 모두 영어입니다:
    - ui/bonds_page.py:140, 207
    - ui/crypto_page.py:103
    - ui/derivatives_page.py:132
    - ui/etf_page.py:158
    - ui/fx_page.py:237, 308, 378
    - ui/macro_page.py:133, 140, 142
    - ui/portfolio_page.py:209
    - ui/quant_lab_page.py:400
    - ui/rates_page.py:156, 200, 257, 293, 363
    - ui/signals_page.py:206
    - ui/strategy_lab_page.py:168
  - 방법: Qt와 무관한 Native 서술 모듈을 core/로 옮겨 두 앱이 함께 씁니다.
  - ui/ai_panel.py:52-53, 69, 78-98의 화면 틀 문구 → 분석가에게 질문 (선택) / 심층 분석 / 분석 / 엔진: 로컬
  - 모형·제공처 메모: bonds_page.py:123, 213; quant_lab_page.py:324, 340, 343, 348, 354; signals_page.py:169, 183; portfolio_page.py:136-140, 146; crypto_page.py:50; derivatives_page.py:75; etf_page.py:172
  - 범위는 Q11.

== 고쳐야 할 테스트 (고정된 문자열, 읽어서 확인) ==
- tests/desktop_market_tabs_acceptance.py:22 '거시 지표표' [R]
- tests/desktop_language_acceptance.py:77 '측정 항목' [R]
- tests/desktop_watchlist_acceptance.py:88 '일별 관측' [R]
- tests/research_home_acceptance.py:93, 166 '리서치 홈' [R]
- tests/desktop_macro_language_acceptance.py:144 '금 · SYNTHETIC' [R]
- 샤프비율: tests/etf_sleeve_disclosure_acceptance.py:145, 303, 304, 315, 316, 326, 340, 356 / tests/desktop_bonds_portfolio_language_acceptance.py:83 [R]
- 공급자·공급처가 없는지 보는 검사 3곳(UI-10/09)에 '제공처'를 더함 [R]
- tests/desktop_typography_acceptance.py:297 '기술지표 가이드'는 그대로 통과 [R]
- 이 목록 밖의 테스트 영향은 확인하지 않았습니다(unverified). tests/run_all.py는 금지라 실행하지 않았습니다.

== A3와 동시에 진행할 때 (소유자 질문 관련) ==
- A1만 고치는 파일: quantgen_desktop/translations.py, display_prose_catalog.py, macro_narrative_language.py, *_narrative.py, core/ui_messages.py, core/ui_legacy_messages.py, core/education/glossary.py(이름 필드), 위 테스트 핀
- A3만 고치는 파일: chart_study.py, typography.py, ui/components.py, 레이아웃 코드
- 둘 다 고치는 파일: bonds.py, app.py, structuring.py, strategy.py, rates.py, market_tools.py, macro_records.py, portfolio.py, tools.py
  - 이 파일들에서 A1이 바꾸는 것은 localize_columns 호출, 표시 맵, 템플릿 원문뿐입니다.
  - 파일마다 A3를 먼저 병합하고 A1을 이어 붙이거나, 한 브랜치에서 함께 작업하면 충돌을 피할 수 있습니다.
- 용어집(위 초안)은 A1 라벨과 A3 UI-12 '알아보기' 패널이 함께 쓰므로 가장 먼저 확정해야 합니다.

## 소유자께 여쭐 이름 선택 (초안)

소유자께 여쭐 이름 선택 (각 항목에 권장 기본값을 적었습니다)

Q0. A1과 A3를 동시에 진행해도 되는지 (요청하신 질문)
- 권장: 가능합니다. 다만 아래 세 조건이 필요합니다.
  1. 용어집(이 초안)을 먼저 확정합니다.
  2. A1의 카탈로그 작업(translations.py, display_prose_catalog.py, macro_narrative_language.py, *_narrative.py, core/ui_messages.py, core/ui_legacy_messages.py, 테스트 핀)은 A3 레이아웃 작업과 나란히 진행합니다.
  3. 두 작업이 함께 건드리는 화면 파일(bonds.py, app.py, structuring.py, strategy.py, rates.py, market_tools.py, macro_records.py, portfolio.py, tools.py)은 파일마다 A3를 먼저 병합하고 A1의 표시 맵을 이어 붙입니다.
- 주의할 점 두 가지:
  - 2026-11-03에 정하신 순서(A3 디자인 → A1 이름·번역)를 바꾸는 결정입니다.
  - CLAUDE.md의 핸드오프 규칙은 "작업은 한 번에 하나"입니다. 그래서 별도 세션 두 개로 나누지 말고, 한 작업(하나의 CURRENT.md) 안에 A1과 A3를 하위 ID로 묶어야 합니다. 세션을 나누면 push_handoff가 거부(exit 3)할 수 있습니다.

Q1. UI-15 '포트폴리오 및 위험' → '분석'
- 왼쪽 메뉴에 '분석 도구'가 함께 있어 '분석'과 '분석 도구'가 헷갈릴 수 있습니다.
- 권장: 말씀하신 대로 '분석'으로 바꾸고 화면을 보여 드린 뒤 확인받겠습니다.
- 다른 안: '포트폴리오 분석', 또는 '분석 도구'를 '시장 분석 도구'로 바꾸기.

Q2. UI-1 매크로 두 탭의 이름
- 권장: '매크로 지표' / '매크로 v2'. Flet의 '거시경제' 계열(메뉴, 관측, v2)도 '매크로'로 바꿉니다.
- 다른 안: '거시경제 지표' / '거시경제 v2'. 한국은행식 표기지만 개인투자자에게는 '매크로'가 더 익숙합니다.
- 'v2'를 '매크로 연구' 같은 뜻 있는 이름으로 바꿀지도 정해 주세요. 권장은 그대로 두기입니다.

Q3. 상태 코드의 표기 규칙
- 13-8/a에서 '공식 상태 코드는 원문 유지'로 정했는데, UI-2는 자연스러운 한국어를 요청하셨습니다. 둘을 함께 만족시키는 방식이 필요합니다.
- 권장: 두 단계로 나눕니다.
  - 운영 상태(OBSERVED, STALE, CONFIGURED, COMPLETED, UNAVAILABLE 등): 한국어만 쓰고 코드는 툴팁과 내보내기에 남깁니다.
  - 연구·검증 코드(PASS, FAIL, NOT_RUN, PARTIAL, REJECT, WITHHELD, NOT_FROZEN, SYNTHETIC): "미실행(NOT_RUN)"처럼 한국어 옆 괄호에 코드를 둡니다.
- 다른 안: 모두 한국어로만 쓰기. 이 경우 SYNTHETIC을 고정한 테스트 여러 개를 고쳐야 합니다.

Q4. 표의 '필드' / '측정 항목' / '측정값'
- 권장: 이름 열은 '항목', 값 열은 '값', 표 제목 'Metrics'는 '주요 지표'.
- 이유: KRX·ETF 시세 표의 행(현재가, 거래량 등)은 측정한 값이 아니라 시세 항목이고, HTS 표도 '항목'을 씁니다.
- 다른 안: 말씀하신 '측정값'을 제목으로, '측정 항목'을 열 이름으로 앱 전체에 쓰기. 이 경우 '필드'만 '측정 항목'으로 바꾸면 됩니다.

Q5. Sharpe ratio의 한국어
- 권장: '샤프 지수'. 앱 용어집이 이미 이 말을 쓰고, 펀드평가와 HTS에서도 흔합니다(외부 대조는 못 함).
- 바꾸면 서술문의 '샤프비율'과 이를 고정한 테스트 약 9곳을 고쳐야 합니다.
- 다른 안: '샤프비율'로 통일. 용어집 이름 하나만 바꾸면 됩니다.

Q6. Convexity의 한국어
- 권장: 표에서는 '컨벡시티', 처음 나올 때는 '컨벡시티(볼록성)'. 채권 업계 표현입니다.
- 몬테카를로 드리프트의 'convexity correction'은 '볼록성 보정'으로 따로 둡니다.
- 다른 안: '볼록성'으로 통일. 지금 서술문과 같습니다.

Q7. Signals 메뉴 이름
- 권장: Native '신호'와 Flet '기술적 관측'을 모두 '기술적 분석'으로 바꿉니다. '신호'는 매매 권유처럼 읽힐 수 있습니다.
- 다른 안: '신호'를 유지하고 Flet만 맞추기.

Q8. Paper Trading 이름
- 권장: Native '모의매매'와 Flet '모의 실행'을 모두 '모의투자'로 바꿉니다. KIS와 증권사가 쓰는 말이고, 3단계 안전 설계 문구와도 같습니다.
- 다른 안: '모의매매' 유지.

Q9. 거래일 단위 표기 (UI-6b)
- 권장: 입력란 단위는 괄호에 "분석 기간 (거래일)", 개수는 "거래일 수", 본문은 "20거래일".
- 다른 안: HTS처럼 "(일)"만 쓰기. 짧지만 달력일과 구분되지 않습니다.

Q10. Provider의 한국어
- 권장: '제공처'로 통일합니다(공급자·공급처 대체). 제공처 이름(FMP, KIS, Yahoo Finance)은 그대로 둡니다.
- 다른 안: '데이터 제공업체'.

Q11. Flet 브라우저 앱에 얼마나 적용할지
- PR #71에서 Flet을 바꾸지 않은 것은 Claude가 정한 것이고, 소유자 결정이 아닙니다.
- 권장: A1에서는 두 앱이 함께 쓰는 카탈로그(core/ui_messages.py, core/ui_legacy_messages.py)와 요청 항목에 해당하는 Flet 화면 머리글까지 바꿉니다. Native 화면에도 영향이 가기 때문입니다.
- 영어로 남은 Flet 원문 1,556개, Flet 차트 글자, Flet 서술 18곳은 별도 후속 항목으로 둡니다.

Q12. PR #71 규칙(라이브 화면에 제공처·관측일 열 없음)을 분석 도구까지 넓힐지
- 남아 있는 곳: 매크로 지표 표의 출처·관측일 열, FX 출처 표와 캐리 '금리 기준일' 열, Home 요약의 '관측 {날짜}', 몬테카를로 위험 표의 출처 열.
- 권장: 화면에서 빼고 툴팁과 내보내기에 남깁니다.
- 단, 컴플라이언스 문서 09-dark-patterns.md에 따라 오래된 자료·합성·지연·실패 상태는 화면 글자로 계속 보입니다.

Q13. 문체
- 권장: Markets 종목 차트의 해요체 20줄을 앱의 나머지와 같은 합니다체로 바꿉니다.

Q14. Zero rate의 한국어
- 권장: '무이표 금리'. 정책금리 0%를 뜻하는 '제로금리'와 헷갈리지 않습니다.
- 다른 안: '제로금리'. 데스크 관행입니다.

Q15. 모형 콤보의 표시명
- 권장: 고유명은 라틴 문자로 보기 좋게 씁니다(nelson_siegel → Nelson-Siegel, hull_white → Hull-White, vasicek → Vasicek). 일반어는 한국어로 씁니다(swaption → 스왑션, none → 없음).
- 콤보의 데이터 ID는 그대로 둡니다(13-8/a).

Q16. OBSERVED의 표시
- 권장: 말씀하신 '정상 관측'을 쓰고, 툴팁에 '일별 종가 기준'을 둡니다. 지금 쓰는 '일별 관측'의 '일별'이라는 뜻을 툴팁으로 남기기 위해서입니다.
- 원문 'OBSERVED'가 그대로 보인 화면은 이번 조사에서 찾지 못했습니다(unverified). 어느 화면이었는지 알려 주시면 확인하겠습니다.

Q17. 곡선 변화 유형 표기
- 권장: '강세 스티프닝 (금리 하락·장단기 금리차 확대)'처럼 업계 용어와 풀이를 함께 쓰고, Rates와 Macro가 같은 표를 씁니다. 좁은 표 칸에는 '강세 스티프닝'만 씁니다.
- 다른 안: 풀이만 쓰기('금리 하락·장단기 금리차 확대').
