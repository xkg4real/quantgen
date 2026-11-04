# 모델 한계 대장 (②-3)

- 작성: 2026-10-28, 기준 커밋 `d865c7f`, 브랜치 `claude/amazing-gauss-tdiguu`.
- 방법: 6개 영역을 나눠 코드에서 모델을 찾아 적고, 영역마다 독립 검증자가 코드와 대조해 고쳤습니다. 전수 점검이 빠진 모델 8개를 더했고, 비평 단계에서 같은 모델을 두 번 적은 항목 4개를 한 항목으로 합쳤습니다(M2-26 평균-분산·최소분산·위험균등 최적화와 효율적 프런티어 (opt → M1-23 포트폴리오 최적화 (optimize_portfolio, eff; M6-14 레버리지·인버스 ETF drag(Avellaneda–Zhang → M4-18 ETF 화면의 레버리지·인버스 ETF 드래그 예측(GARCH-; Quant Lab 등급(R-16: fast FHS·GJR-EVT 꼬리 포 → M1-21 M9 게이트 (m9_gate, grade_lab); 매크로 카드 게이트 통계, CARD-P 검사, 비용 경로 엔진과 패키지  → M2-30 CARD-P 판정기 (cardp: PC-1'~PC-7 · li).
- 짝 문서: 알려진 오류 통합 목록 `docs/nautilus_bridge/KNOWN_ERRORS_REGISTER_2026-10-28.md`(②-4).

## 1. 목적과 읽는 법

### 1.1 이 문서가 하는 일

이 문서는 로드맵 ②-3 **모델 한계 대장**이다. 완료 기준은 "모델마다 목적, 가정, 한계, 적용 범위, 검증 상태 기록"이다(`docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md`, ②-3 행). ②-4 알려진 오류 통합 목록과 짝을 이룬다. 두 문서는 ②-5 우선순위 결정에 들어간다. 소유자 판정 R5에 따라 Nautilus 작업과 함께 진행했다.

- 이 문서는 코드, 카드, 판정 기준을 바꾸지 않는다. R3에 따라 ⑨-3d 결정 전까지 기존 카드 기준을 그대로 둔다.
- 코드 기준은 `d865c7f`다. `fa28059` 이후 `core`, `ui`, `data`, `tools`, `tests`의 변경은 `d865c7f`(①-2 PT-07) 하나뿐이다. 바뀐 것은 달력 데이터(`core/calendars/data/*.yaml`, `data/calendars/KRX.json`·`index.json`), `core/calendars/store.py`·`publication.py`, 달력 테스트(`tests/macro_m1_calendars.py`, `macro_m1_integration.py`, `macro_m9_lab.py`, `macro_registry.csv`)다(`git diff --stat fa28059 d865c7f`, 14개 파일). 그래서 이 파일들 밖에서 "HEAD fa28059"로 적힌 재현은 같은 코드에서 나온 것이다. 달력 항목은 `d865c7f`에서 다시 확인했다(`tests/macro_m1_calendars.py` 22 PASS / 0 FAIL / 5 NOT_RUN).
- 줄 번호는 `d865c7f` 기준이다. 문서나 docstring의 주장은 코드와 대조한 뒤에만 적었다. 둘이 다르면 가정 칸에는 코드의 동작을, 한계 칸에는 그 차이를 적었다.

### 1.2 여기서 말하는 모델

숫자를 만들어 화면, 저장 카드, 원장, 판정으로 내보내는 계산 단위를 모두 모델로 본다.

- 통계 모형과 추정기: GARCH, GJR, 단기금리 모형, SABR, SVI 등
- 가격 공식: 채권, 스왑, 옵션, 구조화 노트
- 전략 규칙과 손익 시뮬레이터
- 판정 장치: 전략 게이트, 분포 게이트, M9 게이트, CARD-P
- 데이터 규칙: PIT 저장소, 타임스탬프 부여, 세션 시계, 발행 일정, 데이터 계약
- 합성 데이터 생성기
- 모델은 아니지만 사용자가 숫자로 읽는 항목: 공급사 계산값 표시(M6-15), 화면 판정 칩과 이동평균 표시(M6-10), 결정적 해설 문장(M6-16~M6-18), AI 심층 분석(M6-19), 모의주문 규칙 평가기(N-01). 이 항목들은 이름에 "모델 아님"을 붙였다.

범위 밖: `paper_live/`(H1 재현성·H2 비용 게이트·H3 검정력 판정, `paper_live/verdict.py`·`power.py`)와 `grokteam/`(GROKTEAM-BOOK)은 태그 `studies-of-record-2026-10-23`의 동결 연구다. 둘은 HEAD 코드와 따로, 그 태그의 클론에서 판독한다(README.md:47-52, `tests/frozen_guard.py`). 이 등록부에서 다루지 않는다. 다만 두 연구는 QUANTGEN 공용 함수를 쓴다. `paper_live`는 `validate.newey_west_t`(M2-16), `validate.TRADING_DAYS`(252, M2-10), `gate_stats.MDE_FACTOR`(M2-18)를 쓰고, `grokteam`은 `garch`(M1-10), `forecast_eval`, `gate_stats`, `gate_ledger`(M2-17~M2-22)를 쓴다. 이 다섯 모듈은 태그와 `d865c7f` 사이에 바뀌지 않았다(`git diff --stat`). 그래서 해당 모델의 한계가 두 판독에도 그대로 해당한다.

| 묶음 | 범위 | 주요 코드 |
|---|---|---|
| M1 | Quant Lab, Portfolio, lab 등급 | `core/quant/` history, risk, montecarlo, garch, gjr, vol_estimators, lab, optimize |
| M2 | Strategy Lab, 전략 게이트, 카드 통계, 시행 원장 | `core/quant/` strategies, validate, gate_stats, gate_ledger, costed, card_lines, cardp, backtest, signals |
| M3 | FICC 금리: 곡선, 채권, 스왑, 금리 옵션, 단기금리 | `core/ficc/` common, curves, bonds, swaps, ratesim, curve_models, data |
| M4 | FX, 지수 파생, 변동성 상품, 구조화 노트, LETF | `core/ficc/` fx, fx_styles, equity_deriv, vol_products, structured |
| 번호 없음 | 매크로 계층(R-xx 규칙), 시계와 PIT, 테크펀드, CRY-1, R-30 | `core/skills/macro_daily.py`, `core/calendars/`, `core/ficc/` pit, macro, contracts, lag_audit, context_log, `core/quant/` risk_layer, sleeves, refusal, forward_sim, tf_* |
| M6 | 가상자산, ETF 화면, 해설, AI | `core/crypto/analytics.py`, `ui/crypto_page.py`, `ui/etf_page.py`, `core/*/insights.py` |
| N | 그 밖: 모의주문 평가기, 데모 데이터, R-18, R-19, R-15, R-35, KOSPI200 만기 규칙, data_checks | `core/engine/`, `data/kis_markets.py`, `core/quant/validate.py` 등 |

매크로 계층 모델에는 번호가 없다. 이름으로 부른다(예: "R-06 시장 변동성 목표(vt, SMA20)").

두 영역이 같은 코드를 따로 적은 항목은 하나로 합쳤고, 합친 쪽은 세지 않는다. Quant Lab 등급(R-16)은 M1-14~M1-22에, 매크로 카드 게이트 통계·CARD-P 검사·비용 경로 엔진과 패키지 동결은 M2-17~M2-25와 M2-30에 있다. M2-26은 M1-23에, M6-14는 M4-18에 합쳤다. M6-10에는 Crypto 화면 표시만 남기고 규칙은 M2-07에 둔다.

### 1.3 항목의 칸

| 칸 | 내용 |
|---|---|
| 목적 | 무엇을 계산해 어디(화면, 카드, 원장, 판정)로 내보내는가 |
| 가정 | 코드가 실제로 쓰는 관례와 입력 조건. 근거 줄 번호를 붙였다 |
| 한계 | 가정이 깨질 때 생기는 오차, 확인된 결함, 표본 밖 성과. 수치에는 출처를 붙였다(1.5) |
| 적용 범위 | 어느 자산, 시장, 화면, 기간에 쓰는가. 어디에 쓰면 안 되는가 |
| 검증 상태 | 1.4의 네 단계 중 하나 |
| 테스트 ID | 동작을 고정하는 테스트 이름. NOT_RUN은 기준 자료(`REFDATA`)나 소유자 입력(`OWNER`)이 없어 건너뛴 테스트다(`tests/notrun.py`). PASS나 FAIL로 세지 않는다 |
| 알려진 오류 | ②-4 목록과 감사 문서의 ID(1.5) |

### 1.4 검증 상태

| 상태 | 뜻 | 주의 |
|---|---|---|
| 독립 검증됨 | 코드와 다른 구현(외부 라이브러리, 닫힌식, 공개 수치 예, 별도 재구현)이 낸 기준값과 비교한 기록이 있다. 금융 계산 감사(`docs/audit/2026-10-27/financial_calcs.md`. QuantLib 1.44와 arch 8.0.0은 스크래치에만 설치했다), Bonds 화면 감사의 독립 구현, B1·B2 공지의 모수 회복 시뮬레이션이 여기에 든다. 코드를 다시 돌리거나 그 값을 재현한 것은 들지 않는다. 부품(식, 추정기)만 대조됐으면 그 부품을 등록한 모델만 독립 검증됨이다. 예: M4-17 드래그 식은 독립 검증됨이고, 그 식을 쓰는 M4-18은 코드로만 확인이다 | "맞다"는 뜻이 아니다. 어디까지 맞고 어디서 틀리는지 안다는 뜻이다. 대조에서 나온 결함도 그대로 적었다. 예: M3-02 YieldCurve는 정수 만기에서 맞는 범위가 확인돼 독립 검증됨이면서 financial_calcs/FC-02(P1, 짧은 첫 기간)를 안고 있다 |
| 테스트로 확인됨 | QA 실행(`tests/run_all.py` 경로)에 든 테스트나 거기 연결된 자체 검사(`tests/expansion_acceptance.py`의 `_selfcheck`)가 공식이나 불변식을 기준값으로 고정한다. 합성 데이터 생성기는 결정성과 출처 표시를 고정하면 여기에 든다. 형태(NaN, 길이), 결정성, 비용 방향, 구성상 성립하는 부등식만 보는 테스트는 들지 않는다. run_all 밖 `__main__` 자체 검사(TA-02)만 있으면 코드로만 확인이다 | 기준값을 같은 명세에서 가져온 테스트는 명세 자체의 오류를 잡지 못한다. 실데이터 기준값 테스트가 NOT_RUN인 모델이 많다(3.2) |
| 코드로만 확인 | 동작을 고정하는 테스트가 없거나, 있어도 위의 형태 검사뿐이다. 이 등록부를 만들며 코드를 읽었다. 일부 수치는 스크래치 스크립트로 재현했다 | 회귀가 생겨도 알려 주는 장치가 없다. 호출처가 있는지는 검증 상태와 따로 적용 범위 칸에 적었다(예: M3-23, M3-24, M4-08, N-08은 호출처가 없다) |
| 미검증 | 계산이 맞다는 근거가 없다. 두 경우가 있다. 독립 대조에서 기본 입력의 주된 출력을 틀리게 하는 결함이 나와 결론이 바뀌고 맞는 범위도 확인되지 않은 경우(M1-04, M4-23, M6-02, M6-05)와, 출력을 검사할 장치가 없는 경우(M6-19)다 | 대조에서 결함이 나와도 맞는 범위가 확인됐으면 독립 검증됨에 두고 결함을 적는다(예: M3-02) |

검증 상태는 "코드가 적힌 식대로 계산하는가"에 대한 판단이다. 모형이 시장을 잘 설명하는지(표본 밖 성과)는 다른 질문이다. 그 답은 한계 칸에 카드 판정이나 SMOKE 등급으로 적었다. 예를 들어 M1-10 GARCH(1,1)-t는 독립 검증됨이다. 그러나 저장 카드 `D_Q_garch_spy`와 `D_Q_garch_kodex200`은 REJECT다.

### 1.5 수치 출처와 ID 읽기

수치 뒤 괄호는 출처를 뜻한다.

- "감사 재현값": 구현 감사 보고서(`docs/audit/2026-10-27-implementation-audit-report.md`)와 그 하위 감사 문서가 재현한 값
- "검증자 재실행": 감사의 독립 검증자가 다시 돌린 값
- "이번 작업 재현", "이번 측정": 이 등록부를 만들며 스크래치 스크립트로 HEAD에서 다시 낸 값
- 카드 이름(`M_E4_letf_drag` 등): `docs/asset_expansion/cards/`의 저장 카드

알려진 오류 ID의 출처는 다음과 같다.

| ID 꼴 | 출처 |
|---|---|
| D12-11, DF-02, MF-03, P01-11, C01-03, V01-01, CAL-01, TA-02, D03-V01, M-1, M-01, M01 등 | 구현 감사 보고서 3장(141건: P1 11, P2 59, P3 71). M-1, M-01, M01은 서로 다른 행이다. 하이픈과 자릿수까지 그대로 읽는다 |
| FC-09~FC-16 | `financial_calcs.md`. FC-15는 감사 보고서 3장의 TA-07 행에 병합돼 있고, 나머지는 3장에 같은 번호의 행이 있다 |
| financial_calcs/FC-01~FC-08, functional_completeness/FC-01~FC-07 | 두 문서의 번호가 겹쳐서 접두어를 붙였다. 한계 칸에 접두어 없는 FC-0x가 나오면 같은 항목의 알려진 오류 칸에서 접두어를 확인한다 |
| BS-01~BS-41 | Bonds 화면 감사(`docs/audit/2026-10-27/bonds_screen_audit.md`). 제안 패치는 적용되지 않았다 |
| K-a~K-h | `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md`의 알려진 오류 표. K-i는 이월 92건 전체를 가리킨다 |
| PA-xx, PB-xx | 이월 92건(Plan A 17건, Plan B 75건; `docs/superpowers/plans/2026-10-23-execution-record.md`) |
| A3~A6, B4, B6, B7, C1, C2 등 | `docs/ARCHITECTURE_REVIEW.md`(2026-09 검토). 감사 보고서에 행이 없다 |
| N-M1-xx, N1~N18(M2), M3-Nxx, M4-Nx, NEW-M6-xx, "신규 관찰", "신규(미등재)" | 이 등록부를 만들며 처음 확인한 것. 감사 보고서에 행이 없다 |
| D-01~D-05 | 감사 보고서 2장 요청서 주장 표의 항목이다. 3장의 행이 아니다. D12-01, D03-01과 다르다 |
| 감사 12.x | 감사 보고서 §12 소유자 결정 항목 |
| PT-xx | 감사 보고서 §11 수정 묶음 |

모델 번호 N-01~N-08과 M2의 신규 관찰 N1~N18은 서로 다른 것이다. 하이픈과 0이 있는지로 구분한다.

같은 결함이 두 영역에서 따로 번호를 받은 경우는 한 번호로 적고 다른 번호를 괄호에 둔다. N-M1-10 = N16(프런티어가 종목 상한을 무시), M4-N1 = NEW-M6-06(코스닥150 펀드에 KOSPI200 분산), M4-N3 = NEW-M6-07((1−β)r 항 누락), M4-N2 = NEW-M6-08('last-quarter vol' 드래그를 연구 기준처럼 표시), N2 = NEW-M6-09(Strategy Lab crypto_trend 격자 중복)이다.

### 1.6 기존 문서와의 관계

**Models Primer.** `docs/QUANTGEN_Models_Primer.pdf`는 영문 해설서다. `docs/build_models_primer.py`가 `core/quant/` 코드를 직접 불러 만든다. 다루는 범위는 Quant Lab의 가격 경로 모형이다: 로그수익률, Monte Carlo, GBM, 점프 확산, 블록 부트스트랩, GARCH(1,1)-t, 최대우도와 가드레일, 드리프트 스터디, 화면 읽기. 이 등록부로는 M1-01, M1-05~M1-11에 해당한다. Primer는 무엇을 왜 계산하는지 설명한다. 이 등록부는 어디서 틀리고 얼마나 확인됐는지 적는다. Primer를 대신하지 않는다. 전략 게이트, 지수 파생, 곡선과 FX, 변동성 상품, 가상자산은 `docs/QUANTGEN_Expansion_Primer.pdf`(`docs/build_expansion_primer.py`)가 설명한다.

Primer와 코드가 다른 곳이 두 군데 있다. 이 등록부는 코드를 따른다.

- Primer 3.4(`build_models_primer.py:892`)는 점프 모형을 머튼 모형이라고 설명한다. 코드는 정규분포에서 한 번 뽑은 값에 점프 횟수를 곱한다(M1-08, FC-10).
- Primer 3.5(`build_models_primer.py:900`)는 "stationary block bootstrap"이라고 쓴다. 코드는 길이 5로 고정된 원형 블록이다(M1-09, ARCHITECTURE_REVIEW C1).

Primer의 수치는 PDF를 만든 때의 값이다. 이 등록부의 수치와 표본이 다를 수 있다.

**ModelCard.** `core/quant/validate.py:803-834`의 `ModelCard`는 검증 실행 한 번을 기록한다. 가설, 규칙, 데이터, 비용, 프로토콜, 시행 수, 통계, 검정, 판정과 그 사유를 JSON으로 남긴다. 판정은 PASS, REVISE, REJECT, INSUFFICIENT_DATA 중 하나다(`validate.py:50`). `docs/asset_expansion_study.py`가 만든 카드 34개가 `docs/asset_expansion/cards/`에 있다. 카드는 "이 자료에서 이 모형이나 전략이 게이트를 통과했나"에 답한다. 이 등록부의 검증 상태는 "코드가 적힌 대로 계산하나"에 답한다. 등록부는 카드를 한계의 근거로 인용할 뿐이다. 카드를 다시 판정하지 않는다(R3).

등록부는 근거 기록 두 가지를 더 인용한다.

- Quant Lab 등급 파일(`docs/quant_lab/KODEX200.json`, `SPY.json`): 공급사 자료로 돌린 SMOKE 실행이다.
- 매크로 카드(CARD-P, `gate_stats`): 패키지가 동결되지 않아 모두 NOT_RUN이다.

## 2. 요약

검증 상태별 모델 수는 다음과 같다(항목에서 생성).

| 영역 | 독립 검증됨 | 테스트로 확인됨 | 코드로만 확인 | 미검증 | 합계 |
|---|---|---|---|---|---|
| 리스크·시뮬레이션 | 6 | 16 | 0 | 1 | 23 |
| 전략·검증 게이트 | 3 | 26 | 0 | 0 | 29 |
| FICC 금리 | 12 | 7 | 6 | 0 | 25 |
| FICC FX·변동성·구조화 | 7 | 10 | 6 | 1 | 24 |
| 매크로·PIT·달력 | 0 | 26 | 4 | 0 | 30 |
| 가상자산·기타 | 0 | 7 | 8 | 3 | 18 |
| 전수 점검에서 추가 | 0 | 7 | 1 | 0 | 8 |
| 합계 | 28 | 99 | 25 | 5 | 157 |

여러 모델에 걸친 중요한 한계는 다음과 같다.

- **가상자산을 252로 연율화한다(D12-11, 병합 M-03, P1).** 24시간 시장의 일봉은 연 365개다. 그런데 거의 모든 경로가 252를 쓴다. Quant Lab 'Vol (ann.)'는 실제의 0.831배(√(252/365))로 나오고, MC 드리프트는 1.45배(365/252)가 된다(M1-01, M1-05, M1-06). Strategy Lab 게이트(M2-10, M2-14), Signals 백테스트(M2-28), CRY-1 대조도 √252를 쓴다. 판정 자체(부호, DSR, PBO, 세션 수)는 바뀌지 않고 표시값만 틀린다(M2-14). 365로 다시 환산하는 곳은 Crypto 화면의 GARCH뿐이다(M6-08, `ui/crypto_page.py:75-76`). 시장별 연율화 일수 표 `clocks.ANNUALISATION_DAYS`는 테스트 밖에서 부르는 곳이 없다("연율화 일수 표" 항목).
- **가격 입력을 검사하지 않는다(D12-01, D12-02, D12-07).** +inf 종가가 1개만 있어도 MC VaR가 0%가 된다(`montecarlo.py:327`의 `max(0.0, nan)`). 같은 날 2배 값 행이 1개 있으면 MC VaR가 13.5%에서 36.0%로 뛴다. 504세션 중 50세션이 빠지면 연 변동성이 6.8% 커진다. 이 문제를 받는 모델은 M1-01, M1-03, M1-05, M1-07, M1-09, M2-29다. M2-29는 마지막 가격이 inf면 'strong bullish'를 낸다. 검사 함수 `validate.data_checks`(N-08)가 있지만 어디서도 부르지 않는다.
- **기대수익률로 로그 평균을 쓴다(M-02, P2).** 해당 모델은 M1-04, M1-23이다. 2자산 GBM 50/50 표본에서 화면 기대수익은 12.69%, 산술 기대수익은 22.34%다. Sharpe는 0.298 대 0.595다. 모집단 최대 Sharpe 비중은 (0.746, 0.254) 대 (0.604, 0.396)다. 효율적 프런티어의 수익 축도 같이 치우친다.
- **FICC 가격기는 곡선을 하나만 쓰고 스텁을 잘못 센다.** `YieldCurve.annuity`는 짧은 첫 기간에도 1/freq 전체 가중을 준다(financial_calcs/FC-02, P1; `curves.py:47-48`, `:112`). 감사 곡선에서 연 1회 스왑 par가 18m에서 −97.2bp, 6m에서 −207.5bp 틀린다. 정수 테너는 틀리지 않는다. 같은 오류가 M3-12 금리스왑, M3-14 스왑션, M3-15 캡, M3-19 시평 재평가, M4-21 역전환사채, M4-23 스티프너로 이어진다. 또 미국채 CMT 곡선 하나가 스왑 곡선 역할과 원화 상품 할인 곡선 역할을 함께 한다(financial_calcs/FC-05, D03-V02). 그래서 DCD 화면의 'plain KRW deposit' 3.60%는 실제로 미국 금리다(M4-22). FRED 만기 일부가 빠지면 30y 스왑 par가 49bp 낮게 나온다(D03-V01, P1).
- **유의성을 과대하게 보이는 통계가 있다.** 김치 프리미엄 예측 회귀의 t는 √n배 크다(M6-02, NEW-M6-01; `core/crypto/analytics.py:100`, `:116`). 화면 기본값 730일에서 약 25배다. 펀딩 십분위 p는 겹치는 30일 수익률에 iid 부트스트랩을 쓴다. 그래서 귀무가설에서 p<0.05가 나올 확률이 0.373이다(M6-05, NEW-M6-02). 페어 전략의 ADF는 독립 랜덤워크에서 18%를 기각한다. Engle–Granger 검정은 6%다(M2-06, N5). Kupiec·Christoffersen의 x=0 분기는 n 192~380에서 정확한 LR보다 관대하다(M1-17, N-M1-01).
- **Sharpe와 현금 가정이 화면마다 다르다.** Strategy Lab과 ETF 화면은 현금에 연 3%를 고정으로 주고, rf를 빼지 않은 총손익 Sharpe를 쓴다(M2-01, M2-10, M6-13; `ui/strategy_lab_page.py:113`, `ui/etf_page.py:81`). Portfolio는 rf를 뺀다(`core/quant/risk.py:169`). FX 캐리 화면은 CAGR/vol을 쓴다(FC-14: 같은 손익에서 0.428 대 0.467). 합성 추세 전략에서 현금 3%만으로 Sharpe가 −0.07에서 0.21로 오른다(N3). 노출이 없는 구간은 표준편차가 부동소수 잡음 수준이라 Sharpe가 1e16 단위로 폭주한다(P01-11). ETF 화면의 무추세 모의에서는 6.8%가 그렇다(NEW-M6-04).
- **보유 중 리밸런싱과 구성 전환에는 비용을 매기지 않는다.** `simulate()`는 매일 목표 비중으로 비용 없이 다시 맞춘다(K-e; M2-01). 합성 예에서 이 암묵 회전은 연 0.79배다. 편도 50bp면 연 약 40bp가 빠진다. walk-forward 구성 전환의 회전도 과금하지 않는다(N4; 연 약 16bp; M2-09). Strategy Lab은 R-26 틱 하한을 쓰지 않는다. 그래서 저가 ETF 비용이 최대 약 25배 낮게 잡힌다(MF-02). BTCUSD, EURUSD는 'us'(50bp)로 분류된다(K-f; M2-15). 요율표 자체를 실제 수수료·세금표와 대조한 근거도 없다(M2-15).
- **합성 데이터가 실데이터처럼 보이는 경로가 남아 있다.** 오프라인 합성 국채 곡선(M3-25)은 화면 기본값 504일에서 최신 행이 역전돼 있다. 1m 9.586%, 30y 7.171%다(BS-25; HEAD에서 다시 확인). 이 곡선이 z-spread −317.75bp(M3-08), HW r0 3.64%→9.55%(M3-18), Vasicek 시평 VaR(M3-19)로 이어진다. FRED가 막히면 김치 프리미엄이 합성 원/달러로 계산돼 +1,257%가 나온다. 이때도 칩은 녹색 'source: LIVE'다(D03-01; M6-01). 합성 자료의 날짜는 늘 오늘에서 끝난다(BS-34, D03-02).
- **매크로 계층은 테스트로 확인됐지만 운영에서는 거의 돌지 않는다.** 달력 파일 16개가 모두 미서명이다(`core/calendars/data/*.yaml`의 `signed_off_by: null`). 그래서 라이브 실행이 거부된다. `gate.package`가 NOT_FROZEN이라 승인된 카드가 없다(N-06, R-35). 수집기, KODEX 200 바스켓, 모멘텀 파생 시리즈가 연결되지 않았다. 그래서 R-07과 R-03·R-04는 늘 fail closed다. R-09의 `apply_hedge_state`는 생산 코드에서 부르지 않는다. 서명 전 수정 대상이던 CAL-01·CAL-02(P1)와 CAL-03은 `d865c7f`에서 미서명 초안에 반영됐다. 남은 것은 소유자 서명이다(16개 모두 미서명, 마감 2026-10-31T15:00:00Z). R-31 hard stop은 2027-08-24부터 HALT를 기록하지 못한다(M-1, P1).
- **표본 밖 검증은 대부분 불합격이다. PASS 카드에도 단서가 붙는다.** 저장 카드 34개는 PASS 5, REVISE 11, REJECT 18이다. GARCH-t 1일 VaR는 SPY와 KODEX 200 모두 REJECT다(M1-10). LETF drag 예측은 R² 0.03이다(M4-18). DNS는 5개 만기 중 하나에서도 랜덤워크를 이기지 못했다(M3-21). PASS 5개도 모두 이 등록부의 한계에 걸린다.
  - `M_C4_funding`: M6-05의 iid 부트스트랩 p에 기댄다.
  - `M_C7_weekday`: 카드 문구의 'weekend slippage set at 2×'가 코드에 없다(M6-07).
  - `M_O2_basis_today`: KIS 이론가로 역산한 배당 1.16pt를 넣어도 −44.7bp가 남는다(M4-09).
  - `S_C3_crypto_trend_btcusd`, `S_C3_crypto_trend_krwbtc`: CRY-1에서 Binance BTCUSDT는 REJECT였다. 소유자 판정 D-24로 PASS를 유지하고 있다(M2-07).

## 3. 검증 공백

### 3.1 근거가 약한 모델과 공백을 닫는 방법

미검증 모델과 코드로만 확인한 모델이 대상이다. 테스트가 있어도 핵심 주장을 고정하지 못하는 모델도 넣었다. 순서는 다음 기준을 차례로 따랐다.

1. 지금 화면이나 저장 카드에 틀린 숫자나 유의성이 나가는가
2. 판정 장치에 들어가는가
3. 기본 입력에서 오차가 큰가
4. 앱에 연결돼 있는가

담당 표기는 ②-4와 같다(Claude, 사용자, 혼합).

| 순위 | 모델 | 상태 | 공백 | 닫는 방법(테스트 또는 기준) | 담당 |
|---|---|---|---|---|---|
| 1 | M6-02 김치 프리미엄 7일 예측 회귀 | 미검증 | t가 √n배 크다. 그 값이 화면 해설에 그대로 나간다 | statsmodels 0.15.0 OLS `cov_type="HAC"`(maxlags 6, Bartlett)와 기울기 t를 맞추는 테스트를 둔다. 귀무 모의에서 \|t\|>2 비율이 약 0.10인지도 확인한다 | Claude |
| 2 | M6-05 펀딩 십분위 이벤트 스터디 | 미검증 | iid 부트스트랩이라 귀무에서 기각률이 0.373이다. 카드 `M_C4_funding` PASS가 이 p에 기댄다 | 비중첩 30일 창이나 정상 블록 부트스트랩으로 바꾼다. 귀무 모의(펀딩 AR(1) φ 0.98, BTC와 독립) 300회에서 p<0.05 비율이 0.05±2SE 안인지 고정한다. 저장 카드를 다시 판정할지는 소유자가 정한다 | 혼합 |
| 3 | M2-14 전략 게이트, M2-11 부트스트랩 구간 | 테스트로 확인됨 | 판정 순서는 테스트가 고정한다. 그러나 게이트 전체의 검정력과 구간 포괄률을 고정한 테스트는 없다. 진짜 edge(SR 1.0, 2,520세션)도 고원 규칙 때문에 REVISE가 된다 | SR을 아는 합성 계열로 격자 모양별 PASS 확률을 재는 검정력 시뮬레이션을 만든다. 90% 구간 포괄률(iid, AR(1), t(4))을 MC 오차 안에서 고정하는 테스트를 둔다. ⑨-3c(R3 보정 기준 검증)와 함께 한다 | Claude(기준 변경은 사용자, ⑨-3d) |
| 4 | M1-04 바스켓 수익률 통계 | 미검증 | 독립 대조에서 결론을 바꾸는 결함이 나왔다(M-02: 50/50 표본에서 화면 수익 12.69% 대 산술 22.34%, 최대 Sharpe 비중 (0.746, 0.254) 대 (0.604, 0.396)). 이를 잡는 테스트가 없다. 이 값은 Portfolio 화면에 나가고 M1-23 최적화에 들어간다 | 2자산 GBM의 닫힌식(산술 기대수익, 모집단 최대 Sharpe 비중)과 비교하는 테스트를 둔다 | Claude |
| 5 | M3-19 시평 재평가 VaR·CVaR | 코드로만 확인 | 모형 곡선과 시장 곡선의 수준 차이가 손실로 섞인다. 화면 기본 설정에서 1일 시평 평균 PV가 −356,742다. `params` 인자는 무시된다. 감사도 HW 시뮬레이션 평균이 곡선을 재현하는지 검증하지 않았다(`financial_calcs.md` 6장) | 일관성 테스트를 둔다. HW에서는 1일 시평 평균 PV가 오늘 PV와 MC 오차 안에서 같아야 한다. Vasicek·CIR에서는 그 차이를 경고해야 한다. `params`를 바꾸면 결과도 바뀌는지 보는 테스트도 둔다 | Claude |
| 6 | M3-16 단기금리 모형 보정(M3-17, M3-18, M3-20으로 이어짐) | 코드로만 확인 | κ를 크게 과대추정한다. 참값 0.8에서 4.193이 나온다. 그 결과 1y 90% 팬 폭이 161bp가 아니라 80bp가 된다. 표준오차도 없다 | 참 모수를 아는 OU·CIR 경로로 κ·θ의 회복 편향과 구간 포괄률을 재는 시뮬레이션 테스트를 둔다. 화면에 표준오차를 보인다 | Claude |
| 7 | M3-05 곡선 요약 지표 | 코드로만 확인 | 5y5y를 5년 단리 선도로 계산한다. 그래서 같은 화면 Swap 도구의 5y5y와 다르다(합성 곡선 7.974% 대 6.958%) | 평탄한 반기 par 4% 곡선에서 5y5y가 반기 환산 4.000%인지 보는 테스트를 둔다. Swap 도구 값과는 관례 차이만큼만 달라야 한다 | Claude |
| 8 | M4-23 CMS 10y−2y 스티프너 | 미검증 | 독립 재계산(Bachelier 스프레드 옵션)에서 결론을 바꾸는 결함이 나왔다(financial_calcs/FC-01, P1). floor·cap의 시간가치가 빠져 공정가가 낮고 마진이 크다. 경고 문구는 편향 방향을 거꾸로 말한다(M-01) | 스프레드 정규 모형(Bachelier, σ_n 입력)으로 floor·cap 가치를 더한 기준값과 비교한다. 기본 입력, σ_n 50bp/년에서 +2.80 차이가 재현되는지 테스트로 고정한다 | Claude |
| 9 | M4-18 ETF 화면 LETF drag 예측(M6-14를 합침) | 코드로만 확인 | 세 가지 문제가 있다. KOSDAQ150 펀드에 KOSPI200 분산을 쓴다(M4-N1). (1−β)r 항이 빠졌다(M4-N3). 'last-quarter vol' 값을 연구가 찾은 기준인 것처럼 표시한다(M4-N2) | 펀드에서 기초지수로 가는 매핑 테스트, r 항을 포함한 식의 테스트를 둔다. 펀드의 실현 drag(M_E4 자료)와도 비교한다 | Claude |
| 10 | M4-22 이중통화예금, M4-06 FX 캐리 백테스트, M4-11 패리티·정적 차익 검사 | 코드로만 확인 | M4-22: 'plain KRW deposit' 3.60%가 실제로 미국 금리다(financial_calcs/FC-04). 스위트 테스트는 구성상 성립하는 부등식과 페이오프 순서만 본다. M4-06: 스위트 테스트는 형태, 비용 방향, 결정성만 보고 값 검사는 run_all 밖 `fx.py` `__main__`에 있다(TA-02). 'Sharpe'는 CAGR/vol이다(FC-14). M4-11: 장 마감 보드에서 검사 대상이 0개인데 초록색 0으로 보인다 | M4-22: GK 풋(M4-02)으로 다시 계산한 증강 수익률·공정가를 기준값으로 고정하는 테스트와, 할인 곡선 통화가 표시 통화와 같은지 보는 테스트를 둔다. M4-06: `fx.py` `__main__`의 값 검사(월간 금리 1관측 지연, 롱 JPY/숏 EUR 사례)를 `tests/ficc_acceptance.py`로 옮긴다. M4-11: 양쪽 호가가 없는 보드에서는 NOT RUN을 보이도록 요구하는 테스트를 둔다 | Claude |
| 11 | 매크로 시트 지표 통계, 매크로 서술적 판독 | 코드로만 확인 | 행마다 날짜가 다른데 as_of는 하나만 보인다(D04-01). 0 근처 스프레드의 상대 변화가 무버 순위를 차지한다. 임계값의 근거가 없다 | 행별 날짜를 확인하는 테스트와 분모가 0 근처일 때의 처리 테스트를 둔다. 임계값은 민감도 표로 근거를 남긴다 | Claude |
| 12 | M2-15 비용 분류와 비용표 | 테스트로 확인됨(요율은 근거 없음) | us 50bp, krx_stock 35bp 같은 요율을 실제 수수료·세금표와 대조한 근거가 없다. 이 요율이 모든 게이트 판정에 들어간다 | 사용자가 증권사 수수료표와 2026년 세율을 준다. 그 표와 대조하는 기준값 테스트를 둔다 | 사용자 → Claude |
| 13 | 공급사 값 표시: M6-04, M6-11, M6-12, M6-15 | 코드로만 확인 | 결측이 0.0으로 바뀌는 경로가 있다(M01). KIS `hts_avls`(억원 추정)와 KRX `MKTCAP`(원)의 단위 차이는 미검증이다. 펀딩의 오늘 UTC 봉은 미완성이다 | 키가 있는 사용자 PC에서 KIS·Upbit·Binance 실응답을 고정 파일로 저장한다. 그 파일로 단위와 결측 테스트를 만든다 | 혼합 |
| 14 | M6-19 AI 심층 분석, M6-18 화면 해설 | 미검증, 코드로만 확인 | 출력 숫자를 대조하는 장치가 없다. `stop_reason`을 보지 않는다. 일반 시스템 프롬프트에 합성 입력을 밝히라는 규칙이 없다 | 출력에 나온 숫자가 페이로드에 있는지 보는 대조 함수와 테스트를 둔다. `stop_reason`이 `max_tokens`면 잘렸다고 표시한다. 페이로드에 합성 표시가 들어가는지 테스트한다 | Claude |
| 15 | R-13 맥락 로그 계산기(probit 부분) | 테스트로 확인됨(계수 원천은 미대조) | 테스트가 명세 자신의 값(0.744)과만 비교한다. 계수 −0.6045, −0.7374의 원천을 확인하지 않았다 | 원천 문서에서 계수와 예제 값을 확인한다. 그 예제를 기준값 테스트로 둔다 | 혼합 |
| 16 | 연결되지 않은 코드: M3-24 KRW 곡선 패널, M3-23 Koijen 캐리, M4-08 Fama 회귀, N-08 data_checks, 연율화 일수 표 | 코드로만 확인 | 호출처가 없어 결과가 어디에도 나오지 않는다. M4-08은 docstring이 HAC t를 약속하지만 OLS t를 낸다(표기 오류, M4-N5). 호출처가 없어 화면 영향은 없다. N-08과 연율화 일수 표는 연결하는 것 자체가 D12-01, D12-07, D12-11의 수정이다 | 연결할 때 테스트를 함께 둔다. M4-08은 statsmodels HAC t와 대조하는 테스트를 둔다. M3-24는 먼저 KIS 실응답과 CD·통안 기저를 확인한다 | Claude(M3-24의 실응답은 사용자) |
| 17 | 그 밖의 코드로만 확인: M3-01, M4-07, M6-06, M6-08, M6-10, CRY-1 | 코드로만 확인 | 영향이 작거나 표본 밖 판정이 이미 REJECT다. M6-08은 추정기가 독립 검증됐고 화면의 365 환산만 테스트가 없다. M6-10은 저장 판정과 이동평균을 보이는 표시다 | 해당 오류(FC-11, functional_completeness/FC-02, D12-11)를 고칠 때 단언 테스트를 함께 둔다. CRY-1에는 가상자산 365 연율화를 확인하는 테스트를 둔다. M6-08에는 화면의 365 환산(`ui/crypto_page.py:75-76`)을 고정하는 테스트를 둔다. M6-10에는 Days<200 렌더 테스트를 둔다(functional_completeness/MF-01) | Claude |

### 3.2 테스트는 있지만 실데이터 기준값이 없는 모델

다음 모델은 공식이나 규칙이 테스트로 고정돼 있다. 그러나 실데이터 기준값(골든) 테스트가 NOT_RUN이다. 공백을 닫는 데 외부 입력이 필요하다.

| 필요한 입력 | 닫히는 공백 | 담당 |
|---|---|---|
| 서명된 달력 16개(①-2, 마감 2026-10-31T15:00:00Z = 2026-11-01 00:00 KST). CAL-01·02·03·04·05·08·10·12·13·14, M-2, M-4 수정은 `d865c7f`에 들어갔고 서명만 남았다(서명 안내서 `docs/calendar_signoff/SIGNING_KIT_2026-10-28.md`). CAL-06(빈 골격 7개)과 CAL-11은 남아 있다 | 세션 시계, 발행 일정, 지연 감사, gap_sessions(M1-14, M1-16, R-10), 북 런타임의 ARM | 사용자(서명) |
| KOSPI 공식 종가와 I-11 KOSPI 픽스처 | M1-16 B5 골든, M1-21 M9 정식 실행, M1-22 실데이터 리플레이, R-06 골든, R-31 G-LAD. I-11의 두 실데이터 테스트는 픽스처가 와도 서명 달력과 리플레이 입력이 없으면 NOT_RUN이다(TA-01) | 사용자 |
| 동결된 `gate.package`와 R-34 양성 대조 자료 | M2-17, M2-18, M2-19, M2-22, M2-23, M2-24, M2-25, M2-30의 수용 검정 | 혼합 |
| French 일간 MOM 파일 | R-03·R-04 골든, R-28·R-29의 1926년 이후 정산 | 사용자 |
| KRX 전 종목 패널(1995-2026) | 테크펀드 스크린과 거버넌스 카드 | 사용자 |
| KODEX 200 PDF 바스켓 | R-07 한국 집중도 한도 | 사용자 |
| 최신 SEP 표 | M3-20(지금은 2023-12-13 빈티지) | 사용자 |
| SPX 월말 종가 수집 | R-28 추세 축 | 사용자 |

## 4. 공통 가정

여러 모델이 같은 관례를 공유한다. 아래는 그 관례와, 모델마다 다른 곳이다.

### 4.1 수익률과 연율화

| 가정 | 쓰는 곳 | 다른 곳 |
|---|---|---|
| 연 252봉, √N 스케일 | `history.TRADING_DAYS`(`history.py:47`), `garch.py:70`, `validate.py:48`, `sleeves.ANN_DAYS`(`sleeves.py:38`), 규칙 저장소 `vol_target.annualisation_days`(R-06 `sma_vol`), `core/ficc/common.py:7`, `core/ficc/equity_deriv.py:42` | Crypto 화면 GARCH는 √365로 다시 환산한다(`ui/crypto_page.py:75-76`). 펀딩 캐리는 ×365다(`core/crypto/analytics.py:145`). tsmom의 EWMA는 MOP 원식대로 ×261이다(`strategies.py:142`). 매크로 카드 통계는 월간이면 12를 쓴다 |
| 시장별 연율화 표 | `clocks.ANNUALISATION_DAYS = {"CRYPTO": 365}`(`clocks.py:30`), 규칙 저장소 `time.markets.CRYPTO.annualisation_days`(365) | 생산 코드가 둘 다 읽지 않는다. 그래서 D12-11이 생긴다 |
| 관측당 적립 | FX 캐리 백테스트는 관측마다 금리차/252를 더한다(`fx.py:425`) | Yahoo FX는 연 약 260관측이라 캐리가 약 3% 과대다(추정, M4-06) |

√N 스케일은 수익률이 서로 독립이고 분포가 같다는 가정이다. 변동성 군집과 자기상관은 무시한다.

수익률의 정의도 모델마다 다르다.

- **로그수익률:** M1 전반(history, risk, montecarlo, garch), lab의 VaR·ES 채점, R-30, 김치 프리미엄의 선행 수익률, 바스켓 평균과 공분산(M1-04), risk_parity 공분산, vol_target σ̂
- **단순수익률:** 전략 손익 `strategies.simulate`(M2-01), 비용 경로 `costed`(M2-23), 리플레이(M1-22), R-06 `sma_vol`(규칙 `sigma.returns = "simple"`), lab의 SMA20 입력(M1-13)
- **섞인 곳:** FHS는 로그수익률을 단순수익률 SMA20 σ로 나눈다(M1-14). 로그 평균을 산술 기대수익처럼 쓰는 곳은 M-02로 묶인다.

### 4.2 복리와 날짜 계산

| 곳 | 복리 | 날짜 계산 |
|---|---|---|
| 곡선 zero(M3-02) | 연속복리 | ACT/365F 실수 연 |
| 곡선 부트스트랩 입력(M3-03) | 1년 미만은 단리 MM, 1년 이상은 반기 par | 같음 |
| 선도 `fwd`, 1y1y·5y5y(M3-02, M3-05) | 단리 | 같음 |
| 채권 수익률(M3-07) | 연 freq회 이산 복리(street) | 쿠폰일을 만기에서 1/f씩 거꾸로 센다. 결제일과 경과이자는 없다 |
| 금리스왑(M3-12), 캡(M3-15) | 스왑은 고정 다리 연 1회, 캡은 분기 단리 선도 | ACT/365F. SOFR의 ACT/360은 없다(FC-11) |
| FX 선도(M4-01) | 연속복리 CIP | ACT/365F. 현물 결제 지연(T+2)은 없다 |
| KOSPI200 선물(M4-09) | 단리 S(1+rT)−D | T = 잔존 달력일/365 |
| 옵션(M4-02, M4-10, M3-13) | 연속 할인 e^{−rT} | T = 달력일/365, theta는 1/365일 |
| 펀딩 캐리(M6-04) | 일 합계 ×365, 단리 | UTC 날짜 |
| 단기금리 시뮬레이션(M3-16, M3-18) | Euler 이산화 | dt = 1/252. 계열 note에 'monthly'가 있으면 1/12(`ratesim.py:118`) |

FICC의 만기는 `parse_tenor`로 정한다. 'd'는 n/365, 'w'는 n/52, 'm'은 n/12, 'y'는 n이다(`core/ficc/common.py:36`). 그래서 3m은 0.25다. 13주 어음의 91/365 = 0.249315와 다르다. 영업일 조정, 결제일, 지급 지연은 어디에도 없다.

### 4.3 달력, 세션, 정렬

- **Quant, FICC, 가상자산:** 공급사가 준 행이 곧 세션이다. 휴장 달력이 없고 결측 세션도 검사하지 않는다(D12-07).
- **기간은 관측 수로 센다.** MC의 '세션', 매크로 시트의 1/5/21/63관측, 펀딩 7행, FX 캐리의 관측당 1/252가 그렇다. 결측이 있으면 실제 기간은 더 길어진다. 가상자산의 126세션은 약 4.1개월이다.
- **여러 계열은 날짜 교집합으로 맞춘다.** `align_panel`은 60세션 이상, `align_histories`는 31세션 이상을 요구한다. KRX와 미국의 종가 시각 차이는 무시한다(DF-02). 다른 방식도 있다.
  - 김치 프리미엄: UTC 날짜 교집합을 쓰고, 원/달러는 나이 상한 없이 앞채움한다.
  - FX 캐리: 금리를 날짜 기준으로 앞채움한다. 월간 계열은 1관측 늦춘다.
  - 매크로 시트: 주말 행만 지운다.
- **합성 데이터:** 오늘부터 거꾸로 센 평일이다(`history.py`의 `synthetic_history`, `core/ficc/data.py:288-295`). 휴장일이 없다.
- **매크로 계층:** 소유자가 서명한 YAML(`core/calendars/data/`)이 유일한 원천이다. 16개가 모두 미서명이라 라이브 실행은 거부된다. dry run은 레거시 `data/calendars/KRX.json`, `US.json`과 고정 경계 시각을 쓴다(C01-03, CAL-10).
- **gap_sessions(연휴 뒤 다세션 배율):** 서명 달력이 있어야 작동한다. 지금은 달력이 미서명이라 배율이 늘 ×1.000이다(M1-16). `d865c7f` 전 초안에 있던 휴장 누락(CAL-01)은 미서명 초안에 반영됐다.
- **KOSPI200 만기:** 둘째 목요일이다. 휴장일 조정이 없다(N-07; 2027-05-13).

### 4.4 비용과 리밸런싱

| 곳 | 요율 출처 | 첫 진입 |
|---|---|---|
| Strategy Lab, 연구 스크립트(M2-01, M2-15) | `validate.COST_BP_PER_SIDE`(`validate.py:78`): krx_etf 3, krx_stock 35, us 50, crypto 10, futures 5, fx 10bp 편도. 한 실행에 종목 요율의 최댓값을 모든 다리에 쓴다 | 과금(`strategies.py:88`) |
| ETF 화면 슬리브(M6-13) | 3bp 또는 50bp 하드코딩(`ui/etf_page.py:84`) | 과금(`simulate` 사용) |
| Signals 백테스트(M2-28) | 기본 10bp(`ui/signals_page.py:114`, `backtest.py:108`) | — |
| FX 캐리(M4-06) | 회전율 × `cost_bp('fx')` | — |
| 카드 비용 경로, 매크로 북 NAV(M2-23, M2-25, 북 런타임) | R-26 틱 하한 `instruments.cost_per_side` | 무료 |
| 델타 헤지 시뮬레이션(M4-16) | 화면 0bp | — |
| FICC 가격기, 구조화 노트 | 없음 | — |

- 다중 슬리브는 리밸런싱 사이에 비중을 비용 없이 매일 다시 맞춘다고 본다(K-e). `simulate`, FX 캐리, FX 스타일, R-03 종이 시리즈, VIX 롤다운이 그렇다. 이 등록부는 K-e를 결함이 아니라 모델 가정으로 적었다(ROADMAP_REVIEW의 K-e 행).
- 시장 충격은 어디에도 없다. 카드 인쇄 줄의 스트레스 비용(M2-25)만 근사로 넣는다.
- Strategy Lab은 R-26 틱 하한을 쓰지 않는다(MF-02). 외부 티커 형식은 잘못 분류된다(K-f).

### 4.5 현금, 무위험 금리, Sharpe

| 곳 | 현금·무위험 금리 | Sharpe |
|---|---|---|
| Strategy Lab(M2-01, M2-14) | 연 3% 고정(`ui/strategy_lab_page.py:113`) | 평균/표준편차 ×√252. rf를 빼지 않는다(`validate.py:137-143`) |
| ETF 화면(M6-13) | 연 3% 고정(`ui/etf_page.py:81`) | `strategies.summary`. rf를 빼지 않는다 |
| 연구 스크립트 | FRED DGS3MO. 실패하면 3%. KRW 슬리브에도 USD 금리를 쓴다 | rf를 빼지 않는다 |
| Signals 백테스트(M2-28) | 플랫 구간은 0을 번다 | rf를 빼지 않는다 |
| Portfolio(M1-23) | rf 입력, 기본 3%. FRED를 읽지 않는다 | (w·μ − rf)/σ(`risk.py:169`) |
| `analyze_history`(M1-03) | rf 인자, 기본 3% | (연수익 − rf)/연변동성 |
| Quant Lab MC의 rf·premium 모드(M1-06) | KRX 코드는 KRW 3개월, 그 밖은 FRED DGS3MO. 실패하면 3%를 가정하고 오류색 칩을 단다. FX 기호에도 미국 금리를 쓴다(A4) | — |
| 팬 PIT 채점(M1-20) | rf 3% + ERP 4% 고정 | — |
| FX 캐리(M4-06) | 금리차를 적립한다 | CAGR/연변동성(`fx.py:443`, FC-14) |
| 카드 통계, CARD-P(M2-17, M2-23, M2-30) | 입력이 초과수익이어야 한다(`cash_convention.returns = "excess"`) | ΔSR |

### 4.6 가격 조정과 단위

- **History의 조정 관례:** FMP는 adjClose가 있으면 total, 없으면 split이다(`history.py:186`). KIS 국내·해외는 split이다. Yahoo는 total이다. 단 ^로 시작하거나 =F, =X, -USD, -KRW로 끝나는 기호는 ''다(`history.py:279-281`). 합성은 ''다. 관례가 섞여도 `convention_warning`은 경고만 한다(`history.py:103-117`, MF-03).
- **MC 드리프트:** premium·rf 모드는 총수익 계열을 가정한다. 가격수익 계열이면 배당수익률만큼 과대다(M1-06, A3).
- **가격지수와 분배금:** R-06은 KOSPI 가격지수를 쓴다. 매크로 북 NAV는 069500 종가 비율만 쓰고 분배금을 넣지 않는다. ETF 화면의 KRX 종목은 KIS 수정주가(현금 분배 제외)이고, 미국 종목은 FMP 배당 조정 종가다. LETF 연구의 지수 대용은 배당 조정된 069500.KS다(M4-18).
- **연속 선물:** Yahoo =F 계열은 롤 조정이 없다(DF-05). KIS `continuous_futures`는 비율 조정 롤을 하지만 호출처가 없다(N-07, data_flow/MF-02).
- **가상자산:** USDT를 1 USD로 본다(DF-06). 일봉은 UTC 기준이고 오늘 봉은 미완성이다(DF-03).
- **단위:** Series와 History에는 단위 필드가 없다(D03-06). FRED 퍼센트는 곡선 패널에서 100으로 나누고 앞채움한다(`core/ficc/data.py:582-589`). 매크로 시트는 출처가 FRED일 때만 0.01을 곱한다(`core/ficc/macro.py:131-132`). 금리 계열을 History에 넣으면 수치가 무의미해진다(DF-01).
- **정제:** `_clean_rows`는 None과 0 이하 값을 버린다(`history.py:95-100`). FMP, KIS 국내, Yahoo 경로에만 있다(D12-03). +inf와 중복 날짜는 남는다.
- **캐시:** Quant와 FICC는 같은 디스크 캐시를 쓴다. 캐시에서 읽으면 note에 'cached <시각>'이 붙는다. 장중에 받은 마지막 봉은 `provisional_intraday`로 표시한다(`history.py:402-460`).

### 4.7 합성 대체와 출처 표시

- **Quant(`history.load_history`):** `source="auto"`일 때 해당 공급사 키가 없으면 합성으로 간다(`history.py:491-511`). 키가 있는데 호출이 실패하면 오류를 낸다. source를 명시하면 대체하지 않는다.
- **FICC(`core/ficc/data.py`):** `source="auto"`이면 공급사가 응답하지 않을 때도 계열별로 SYNTHETIC으로 바꾸고 note에 사유를 적는다(`data.py:513-545`). source를 명시하면 `FICCError`를 낸다. FX 화면은 Yahoo를 명시해도 금리를 auto로 불러 합성으로 떨어질 수 있다(D03-10).
- **생성기:** 주식 GBM(M1-02), NS 랜덤워크 국채 패널과 OU 단기금리(M3-25), GBM FX·가상자산 데모·KOSPI200 데모 보드(N-02)가 있다. 모두 `source="SYNTHETIC"`과 note를 단다. 값은 시드로 고정되고 날짜는 오늘에서 끝난다. 그래서 매일 최신 자료처럼 보인다(BS-34, D03-02).
- **표시 범위가 화면마다 다르다.** Quant Lab과 Portfolio는 오류색 배너를 띄운다. FICC 해설은 curve, macro, daily, weekly에서만 합성을 밝힌다(D03-03). Crypto 화면은 원/달러만 합성일 때 밝히지 않는다(D03-01). AI 일반 시스템 프롬프트에는 합성 공개 규칙이 없다(D03-04).
- **자료 대신 가정값을 쓰는 곳:** MC rf 3%(오류색 칩), KOSPI200 CD 3.00%('input' 표시, D03-05)가 있다.
- **매크로 PIT:** 합성과 auto 행은 `pit_value`에서 context 역할만 받는다. `pit_window`는 이런 행을 거르지 않는다(잠재 결함).

### 4.8 난수 시드

시드는 고정이다. MC는 7(`montecarlo.py:231`), 단기금리 시뮬레이션은 7(`ratesim.py:219`)이다. lab, 게이트 부트스트랩, R-25는 11(`lab.py:50`)이다. 펀딩 부트스트랩은 3, 연구 부트스트랩은 20261002다. 같은 입력이면 같은 숫자가 나온다. 대신 몬테카를로 오차는 화면에 보이지 않는다. M1-05의 VaR95는 시드에 따라 표준편차 0.27~0.44%p만큼 움직인다. M3-18도 같은 문제가 있다.

## 5. 모델 목록

| # | 모델 | 영역 | 검증 상태 | 관련 오류 | 화면 |
|---|---|---|---|---|---|
| 1 | M1-01 일간 수익률과 연율화 관례 (History, TRADING_DAYS=252) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-11(병합 M-03, P1), D12-01, D12-02, D12-03, D12-05, D12-06, D12-07, D12-12, D12-13, D12-14, DF-01, DF-05, MF-03, TA-06, C01-01 | load_history를 쓰는 모든 화면: Quant Lab, Portfolio, Signals, Strategy Lab, ETF. Crypto 화면만 365로 따로 환산한다(ui/crypto_page.py:75-76). |
| 2 | M1-02 합성 가격 경로 (synthetic_history) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-15, D03-04, D03-06, D03-08 | Quant Lab(배너 ui/quant_lab_page.py:305-307), Portfolio(배너 ui/portfolio_page.py:131-138), Signals, Strategy Lab, ETF LETF 표(source 'synthetic index') |
| 3 | M1-03 단일 자산 위험 통계 (analyze_history: 역사적 1일 VaR·CVaR, 변동성, Sharpe, Sortino, MDD) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-11(병합 M-03; risk.py:84,87,90,93), D12-07(risk.py:75 bdate_range), D12-01, ARCHITECTURE_REVIEW C2(감사 행 없음) | - (화면 없음. insights.narrate_risk도 테스트만 호출) |
| 4 | M1-04 바스켓 수익률 통계 (align_histories, portfolio_point) | 리스크·시뮬레이션 | 미검증 | M-02, DF-02, D12-07, DF-01, D12-11 | Portfolio: return %/yr·vol·Sharpe 칩(ui/portfolio_page.py:146-153), 네 목적 비교표(:159-174), 효율적 프런티어(:176), 상관 히트맵(:177), AI 페이로드(:179-193) |
| 5 | M1-05 Monte Carlo 엔진과 위험 수치 (run_monte_carlo: 팬, 기간 VaR·CVaR, P(loss), P(target)) | 리스크·시뮬레이션 | 독립 검증됨 | D12-11(P1), D12-01, D12-02, DF-03, DF-01, D12-06, ARCHITECTURE_REVIEW C2(감사 행 없음), 신규 N-M1-03, 신규 N-M1-11 | Quant Lab 첫 타일 줄(Spot, Median terminal, 90% range, P(loss), VaR 95, CVaR, Drift (ann.), Vol (ann.), P(target): ui/quant_lab_page.py:308-319), 팬 차트·만기 히스토그램(:338-339), 해설·AI 페이로드(:340-377) |
| 6 | M1-06 MC 드리프트 규칙과 볼록성 보정 (premium, rf, zero, sample) | 리스크·시뮬레이션 | 독립 검증됨 | D12-11, ARCHITECTURE_REVIEW A3·A4(감사 행 없음) | Quant Lab Drift 드롭다운·ERP 입력·rf 칩, 'Drift (ann.)' 타일(ui/quant_lab_page.py:316), drift_note 문장(:321), 해설 |
| 7 | M1-07 GBM 경로 모형 | 리스크·시뮬레이션 | 독립 검증됨 | D12-11, D12-02, D12-06, ARCHITECTURE_REVIEW C2(0 클립, M1-05 공통) | Quant Lab 모형 'GBM (lognormal)' |
| 8 | M1-08 점프 확산 경로 모형 (3σ 분할, 문서상 'Merton') | 리스크·시뮬레이션 | 테스트로 확인됨 | FC-10, TA-08, D12-06, D12-11, ARCHITECTURE_REVIEW A5(감사 행 없음), 신규 N-M1-04 | Quant Lab 모형 'Jump diffusion (Merton)', jump_note 문장 |
| 9 | M1-09 블록 부트스트랩 경로 모형 | 리스크·시뮬레이션 | 테스트로 확인됨 | ARCHITECTURE_REVIEW C1(=N-M1-02, 감사 행 없음), D12-01, D12-02 | Quant Lab 모형 'Block bootstrap (empirical)' |
| 10 | M1-10 GARCH(1,1)-t 추정과 모형 비교 (fit_garch) | 리스크·시뮬레이션 | 독립 검증됨 | FC-09(=ARCHITECTURE_REVIEW B4), TA-02, ARCHITECTURE_REVIEW B6·B7(감사 행 없음), 입력 D12-01·D12-02·D12-11·DF-01 | Quant Lab GARCH 타일 줄·가드레일 칩·스터디 칩(ui/quant_lab_page.py:102-188), 조건부 변동성 차트(ui/qcharts.py:211-235), 해설; ETF LETF 표(ui/etf_page.py:104-115); Derivatives 해설(ui/derivatives_page.py:128-131,170-174); Crypto 365 환산 타일(ui/crypto_page.py:71-76,169) |
| 11 | M1-11 GARCH-t 분산 예측과 유계 t 경로 시뮬레이션 (forecast_variance, horizon_vol, simulate_returns) | 리스크·시뮬레이션 | 독립 검증됨 | D12-11, TA-02, ARCHITECTURE_REVIEW A6(감사 행 없음) | Quant Lab 기본 팬·만기 히스토그램·'Horizon vol (ann.)' 타일·bound_note(ui/quant_lab_page.py:133,338-339); Derivatives 밀도 차트(ui/derivatives_page.py:257-262, 드리프트 0); ETF LETF 21/63/252세션 드래그(ui/etf_page.py:107-110) |
| 12 | M1-12 GJR-GARCH(1,1) t / Hansen skew-t (fit_gjr) | 리스크·시뮬레이션 | 독립 검증됨 | financial_calcs/FC-08(수정 묶음 PT-21), TA-02 | Quant Lab 스터디 칩(skew-t 판정, ui/quant_lab_page.py:182-187), Crypto scorecard 카드, lab 등급의 GJR-EVT 다리 |
| 13 | M1-13 lab 변동성 입력 (SMA20, 확장창 GJR-t 예측) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-07, 신규 N-M1-05, 신규 N-M1-06 | Quant Lab 저장 등급(docs/quant_lab/*.json) 경유만 |
| 14 | M1-14 FHS 1일 VaR·ES (fast FHS) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-07, CAL-01(d865c7f 반영, 서명 대기; gap_sessions 의존) | Quant Lab 저장 등급 문장(구성요소 줄) |
| 15 | M1-15 GJR-EVT 꼬리 (McNeil–Frey, GPD) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-07(입력 간격) | Quant Lab 저장 등급 경유만 |
| 16 | M1-16 꼬리 envelope와 1일 VaR 표시 규칙 (envelope, display_scale, B5) | 리스크·시뮬레이션 | 테스트로 확인됨 | CAL-01, M-2(d865c7f 반영, 서명 대기), TA-12 | Quant Lab 등급 문장 '1-day VaR (envelope)'(ui/quant_lab_page.py:203-236, 저장 JSON의 lines) |
| 17 | M1-17 Kupiec·Christoffersen VaR 백테스트 | 리스크·시뮬레이션 | 테스트로 확인됨 | 신규 N-M1-01 | Quant Lab 칩 'Kupiec 99% VaR', 'Christoffersen CC 99%'; 스터디 칩과 카드 문장(D_Q_*) |
| 18 | M1-18 ES Z2 검정 (Acerbi–Székely, 모의 임계값) | 리스크·시뮬레이션 | 테스트로 확인됨 | - | Quant Lab 칩 'ES 97.5% Z2' |
| 19 | M1-19 Basel 신호등 (traffic_light, basel_zone) | 리스크·시뮬레이션 | 테스트로 확인됨 | - | Quant Lab 칩 'Basel last 250'; 스터디 카드 traffic 값 |
| 20 | M1-20 팬 PIT 검정 (garch_fan_quantiles, fan_pit) | 리스크·시뮬레이션 | 테스트로 확인됨 | D12-11 | Quant Lab 칩 'Fan PIT h21' |
| 21 | M1-21 M9 게이트 (m9_gate, grade_lab) | 리스크·시뮬레이션 | 테스트로 확인됨 | CAL-01, M-2(d865c7f 반영, 서명 대기), TA-01(P2), TA-12, functional_completeness/FC-07(P3), 신규 N-M1-05, 신규 N-M1-01 | Quant Lab 'M9 gate' 칩, SMOKE 칩, 네 통계 칩, 등급 문장(ui/quant_lab_page.py:203-236) |
| 22 | M1-22 역사 구간 재현과 LETF 경로 항등식 (replay, letf_path_return) | 리스크·시뮬레이션 | 테스트로 확인됨 | 신규 N-M1-07 | - (화면 없음) |
| 23 | M1-23 포트폴리오 최적화 (optimize_portfolio, efficient_frontier, 위험 기여) | 리스크·시뮬레이션 | 테스트로 확인됨 | M-02, DF-01, DF-02, D12-01, D12-11 (병합: M-03), P01-05, P01-06, P01-12, M02, 신규 N-M1-09, 신규 N-M1-10(= N16), M2 신규 N3 | Portfolio: 목적 칩·return/vol/Sharpe 칩(ui/portfolio_page.py:146-153), 비중·위험 기여 표, 네 목적 비교표(:159-174), 프런티어 차트(:176), 해설·AI 페이로드(:179-194); ui/qcharts.py:frontier_chart:161 |
| 24 | M2-01 일간 손익 시뮬레이터 (strategies.simulate · equity_curve · summary · align_panel) | 전략·검증 게이트 | 테스트로 확인됨 | K-e, P01-11, D12-11 (병합: M-03), functional_completeness/FC-01 (병합: P01-01), DF-01, DF-02, MF-03, M02; 미등재 신규 N3(현금 3% 고정·통화 불일치·초과수익 아닌 Sharpe) | Strategy Lab 'out-of-sample equity' 차트와 통계 타일(ui/strategy_lab_page.py:261-273, 지금은 렌더 크래시); ETF 화면 'Trend switch Sharpe'·'Vol-target Sharpe'·'Buy & hold Sharpe'·'Trend MDD'(ui/etf_page.py:227-231)와 해설(:145-150); Strategy Lab scorecard의 스터디 카드 수치 |
| 25 | M2-02 추세 전환 trend_switch (Faber SMA / MOP 부호) | 전략·검증 게이트 | 테스트로 확인됨 | DF-02, P01-11; 미등재 신규 N3, N14; ETF 워밍업 포함 Sharpe(M6 그룹 확인 항목) | Strategy Lab 'Trend switch' 실행(지금 렌더 크래시 FC-01); ETF 화면 추세 슬리브(ui/etf_page.py:80-90, :227-231); scorecard S_E1_* |
| 26 | M2-03 변동성 타깃 vol_target (상한형 Moreira–Muir) | 전략·검증 게이트 | 테스트로 확인됨 | 미등재 신규 N1, N3; D12-11(가상자산 입력 시) | Strategy Lab 'Capped volatility target'; ETF 화면 'Vol-target Sharpe'(target 0.12, 단일 종목, ui/etf_page.py:83, :231); scorecard S_E2_* |
| 27 | M2-04 횡단면 모멘텀 xs_momentum (Jegadeesh–Titman 12-1) | 전략·검증 게이트 | 테스트로 확인됨 | DF-02 | Strategy Lab 'Cross-sectional momentum'; scorecard S_E5 |
| 28 | M2-05 시계열 모멘텀 tsmom (MOP 2012) + ewma_vol | 전략·검증 게이트 | 테스트로 확인됨 | data_flow/MF-02(연속 선물 함수는 죽은 코드, 연결하면 롤 오류), DF-01; 미등재 신규 N14 | Strategy Lab 'Time-series momentum'; scorecard S_B3 |
| 29 | M2-06 페어 pairs (Engle–Granger 스프레드) + half_life + adf_pvalue | 전략·검증 게이트 | 테스트로 확인됨 | K-a(부분 수정), functional_completeness/FC-02 (병합: TA-03); 미등재 신규 N5, N6, N10 | Strategy Lab 'Pairs'; scorecard S_E8_pairs_*, S_S6_pairs_*(첫 줄 ADF 문구) |
| 30 | M2-07 가상자산 단기 추세 crypto_trend (Liu–Tsyvinski / Detzel 표결) | 전략·검증 게이트 | 테스트로 확인됨 | D12-11 (병합: M-03), functional_completeness/FC-04, K-c, K-d, K-f, NEW-M6-23; 미등재 신규 N1, N2(= NEW-M6-09) | Strategy Lab 'Crypto short-horizon trend'; Crypto 화면 C3 판정 칩(ui/crypto_page.py:91-96, :156-160); scorecard S_C3_* |
| 31 | M2-08 위험 균등 전략 risk_parity (롤링 공분산) | 전략·검증 게이트 | 테스트로 확인됨 | DF-02, M-02(strategies.py:364 평균이 로그지만 RP 목적함수는 평균을 안 써 영향 없음) | Strategy Lab 'Risk parity'; scorecard S_E3 |
| 32 | M2-09 격자 손익 행렬과 walk-forward 선택 (pnl_matrix · grid_from · walk_forward) | 전략·검증 게이트 | 테스트로 확인됨 | P01-11, functional_completeness/FC-01, K-d, P01-02; 미등재 신규 N4 | Strategy Lab 결과 칩 'IS 756 / OOS 126 / embargo …'와 OOS 곡선(ui/strategy_lab_page.py:252-273); AI 페이로드 walk_forward(:155) |
| 33 | M2-10 Sharpe·Lo 표준오차·최소 기록 길이 (validate.sharpe · lo_se · min_track_record · _col_sharpe) | 전략·검증 게이트 | 독립 검증됨 | P01-11, D12-11 (병합: M-03), financial_calcs/FC-14; 미등재 신규 N3 | Strategy Lab 'OOS Sharpe'·'2× costs'·'Benchmark SR'·'Haircut SR' 타일(ui/strategy_lab_page.py:262-271); ETF 화면 Sharpe 3개; scorecard 'Key numbers'(:187-189) |
| 34 | M2-11 블록 부트스트랩 Sharpe 구간과 벤치마크 차이 검정 (block_bootstrap_ci · sharpe_diff_bootstrap) | 전략·검증 게이트 | 테스트로 확인됨 | V-P01-M3, P01-05, D12-11 (병합: M-03) | Strategy Lab 'OOS Sharpe' 툴팁 90% 구간, 'Benchmark SR' 툴팁 차이·p, 판정 줄(ui/strategy_lab_page.py:262-270, :274) |
| 35 | M2-12 디플레이티드 Sharpe DSR (expected_max_sharpe · deflated_sharpe) | 전략·검증 게이트 | 독립 검증됨 | K-c, P01-11; 미등재 신규 N12 | Strategy Lab 'Deflated Sharpe' 타일, 판정 줄 '… after N trials', 원장 칩 툴팁 'counts only this run's grid'(ui/strategy_lab_page.py:254-256, :264); scorecard 'DSR' |
| 36 | M2-13 과최적화 확률 PBO (validate.pbo_cscv, CSCV) | 전략·검증 게이트 | 독립 검증됨 | financial_calcs/FC-07, P01-02, P01-11; 미등재 신규 N2 | Strategy Lab 'PBO' 타일과 판정 줄(ui/strategy_lab_page.py:265, :274); scorecard 'PBO' |
| 37 | M2-14 전략 게이트 판정 규칙 (score_strategy · _decide_strategy · GATE · plateau_share · year_stats · regime_split) | 전략·검증 게이트 | 테스트로 확인됨 | K-c, K-d, V-P01-M3, D03-09, functional_completeness/MF-02, functional_completeness/FC-01 (병합: P01-01), functional_completeness/FC-06, DF-02, P01-05, D12-11 (병합: M-03), M02; 미등재 신규 N3, N7, N9, N12, N13 | Strategy Lab 판정 칩·이유·통계 타일 11개·판정 줄·AI 분석 패널(ui/strategy_lab_page.py:241-276), scorecard 표와 카드 상세(:158-212); Crypto·Quant Lab·ETF 화면의 카드 판정 칩 |
| 38 | M2-15 비용 분류와 비용표 (cost_class · cost_floor_bp · cost_bp · COST_BP_PER_SIDE) | 전략·검증 게이트 | 테스트로 확인됨 | K-f, functional_completeness/MF-02, functional_completeness/FC-08, D03-09 | Strategy Lab 'Cost bp/side'(빈칸=table), 보류 notice와 'NO VERDICT' 칩(ui/strategy_lab_page.py:221-222, :247-251), 원장 market 칸; FX 화면 Cost 기본값(ui/fx_page.py:159) |
| 39 | M2-16 분포 검증 루프 (score_distribution · kupiec · christoffersen · traffic_light · coverage_check · pit_tests · crps · dm_test) | 전략·검증 게이트 | 테스트로 확인됨 | 미등재 신규 N8 | Strategy Lab scorecard의 분포 카드 D_Q_*·D_C2_* 줄; Quant Lab·Crypto 화면 카드 칩(ui/quant_lab_page.py:168-174, ui/crypto_page.py:91-96) |
| 40 | M2-17 ΔSR 추론: LW-HAC 표준오차·스튜던트화 블록 부트스트랩·Politis–White 블록 (gate_stats) | 전략·검증 게이트 | 테스트로 확인됨 | - | -(오늘 화면 출력 없음. Macro → Model cards는 NOT_RUN 사유만 표시, ui/macro_cards_view.py) |
| 41 | M2-18 검정력·MDE80·UNDERPOWERED 규칙 (power_line · check_power_block · apply_underpowered) | 전략·검증 게이트 | 테스트로 확인됨 | - | -(매크로 카드 NOT_RUN) |
| 42 | M2-19 카드 목적함수 PBO (gate_stats.pbo_on_claim · pbo_null) | 전략·검증 게이트 | 테스트로 확인됨 | financial_calcs/FC-07 | -(매크로 카드 NOT_RUN) |
| 43 | M2-20 인쇄 전용 다중성·보조 통계 (by_qvalue · holm_adjusted · harvey_liu_haircut · lo_adjusted_sr · psr · dsr_vs_zero) | 전략·검증 게이트 | 테스트로 확인됨 | - | -(매크로 카드 NOT_RUN) |
| 44 | M2-21 유효 시행 수 N_eff (gate_ledger: diff_corr · n_clusters · emax_sim · n_equiv · n_eff) | 전략·검증 게이트 | 테스트로 확인됨 | K-c, K-d, functional_completeness/FC-01 | Strategy Lab 원장 칩 'E1 ledger: N configurations'(n_raw만, ui/strategy_lab_page.py:254-256); Macro → Model cards(NOT_RUN) |
| 45 | M2-22 3단계 디플레이트 ΔSR·선택계수 f와 시행 원장 (gate_ledger.step3 · selection_factor · FamilyLedger · repo_anchor) | 전략·검증 게이트 | 테스트로 확인됨 | K-g, PA-01, PB-57, K-c, K-d, K-f; 미등재 신규 N15, N18 | Strategy Lab 원장 칩(ui/strategy_lab_page.py:254-256); Macro → Model cards(NOT_RUN) |
| 46 | M2-23 R4b 비용 경로 엔진 (costed: earning_weights · costed_path · same_exposure_static · vt_weights · 보조 통계) | 전략·검증 게이트 | 테스트로 확인됨 | - | -(직접 없음. core/engine/books.py:643이 같은 관례를 복제한다. 매크로 카드는 NOT_RUN) |
| 47 | M2-24 연구 부트스트랩·gate_boot·v1.2-check (costed.research_bootstrap · gate_boot · v12_check) | 전략·검증 게이트 | 테스트로 확인됨 | - | - |
| 48 | M2-25 카드 인쇄 줄 (card_lines: 실행 변형 A/B/C · 야간/장중 기여 · 회전 · 스트레스 비용 · 롤 · 지속성 등) | 전략·검증 게이트 | 테스트로 확인됨 | - | -(매크로 카드 NOT_RUN) |
| 49 | M2-27 R-15 시장 간 역변동성 기본 비중 (inverse_vol_weights · ewma_sigma · weekly_returns · ledoit_wolf_line) | 전략·검증 게이트 | 테스트로 확인됨 | - | - |
| 50 | M2-28 단일 종목 규칙 백테스트 (backtest.run_backtest: ma_cross · momentum · rsi_revert) | 전략·검증 게이트 | 테스트로 확인됨 | D12-11 (병합: M-03), functional_completeness/FC-08, D12-01, DF-01; 미등재 신규 N11 | Signals 화면 백테스트 칩(strategy %, buy & hold %, Sharpe, max DD, exposure, trades·win)과 곡선(ui/signals_page.py:160-171) |
| 51 | M2-29 기술 신호 합성 점수 (signals.compute_signals · sma · ema · rsi · macd) | 전략·검증 게이트 | 테스트로 확인됨 | D12-01, DF-01; 미등재 신규 N17 | Signals 화면 입장 칩과 구성 표, 헤더 notice(ui/signals_page.py:28, :70, :211); qcharts SMA 선 |
| 52 | M2-30 CARD-P 판정기 (cardp: PC-1'~PC-7 · line_verdict · combine_card_verdict · cardp_evaluate · timing_profile · gate_acceptance_test) | 전략·검증 게이트 | 테스트로 확인됨 | 미등재 신규 N18, functional_completeness/FC-07(P3, UNVERSIONED 상수), TA-01(P2) | -(Macro → Model cards는 NOT_RUN 사유만 표시, ui/macro_cards_view.py) |
| 53 | M3-01 FICC 공통 관례 (common.py) | FICC 금리 | 코드로만 확인 | FC-11 (P3) | Rates 입력(테너 '10y', '5y5y', '18m' 등), Bonds·Rates의 KRD 차트 격자, 모든 bp·% 표시 |
| 54 | M3-02 YieldCurve 할인·보간·범프 | FICC 금리 | 독립 검증됨 | financial_calcs/FC-02 (P1), BS-07, TA-02, TA-07 | Rates 곡선 표(Zero, DF, Par, 1y fwd)와 곡선 차트; Rates 스왑·스왑션·캡·시뮬레이션의 할인; Bonds 곡선 의존 카드; Structuring 할인(core/ficc/structured.py가 curve.zero·df·annuity 사용) |
| 55 | M3-03 par 곡선 부트스트랩 | FICC 금리 | 독립 검증됨 | D03-V01 (P1), BS-14, BS-15, BS-16, BS-17, BS-25, BS-34, BS-37, C01-02, financial_calcs/FC-05, TA-02 | Rates 곡선 도구(출처·as of 칩), Bonds 전 도구, Structuring, Rates 스왑·옵션·시뮬레이션 |
| 56 | M3-04 Nelson–Siegel·Svensson 곡선 적합 | FICC 금리 | 테스트로 확인됨 | TA-02, TA-07 | Rates 곡선 도구 Method 드롭다운, 칩 'nelson_siegel rmse x bp', 곡선 차트 점선, AI 페이로드 ns.params·rmse |
| 57 | M3-05 곡선 요약 지표·모양·국면 분류 | FICC 금리 | 코드로만 확인 | D03-V01 (P1), 신규 M3-N06, PA-12, D03-03, TA-02 | Rates 곡선 도구 타일(Shape, Regime, 2s10s, 5s30s, 3m10y, 2s5s10s fly, Level, 1y1y, 2y1y, 5y5y, 1y fwd vs 1y), 곡선 차트 제목(ui/fcharts.py:90), 곡선 표 '1y fwd' 열, narrate_curve 해설, AI 페이로드; Macro 화면 국면 행(ui/macro_page.py:164) |
| 58 | M3-06 곡선 PCA | FICC 금리 | 테스트로 확인됨 | TA-02 | Rates 곡선 도구 PCA 차트, AI 페이로드 pca_explained, narrate_curve; M3-22 fly 가중치 |
| 59 | M3-07 채권 가격·수익률·듀레이션·볼록성·DV01 | FICC 금리 | 독립 검증됨 | financial_calcs/FC-03 (P2), FC-11, BS-01 (P1, 화면), BS-02, BS-04, BS-05, BS-06, BS-07, BS-19, BS-20, BS-22, BS-23, BS-39, TA-02, TA-07, D03-03 | Bonds 계산기 타일(Price, Yield, Macaulay, Modified, Convexity, DV01), 가격-수익률 차트, narrate_bond, AI 페이로드; Rates 시뮬레이션의 재평가 채권(M3-19) |
| 60 | M3-08 KRD와 z-spread | FICC 금리 | 독립 검증됨 | BS-22, BS-07, BS-25, BS-18(차트 제목 안 보임), BS-35, TA-02 | Bonds 계산기 z-spread 타일(툴팁 curve price), KRD 차트('z-spread held'), AI 페이로드 krd·z_spread |
| 61 | M3-09 채권 carry·roll-down·breakeven | FICC 금리 | 독립 검증됨 | BS-08 (P2), BS-21 (P3), BS-41, BS-07, D03-03 | Bonds 계산기 Carry(3m)·Roll-down·Carry + roll·Breakeven 타일, narrate_bond, AI 페이로드 carry_roll |
| 62 | M3-10 채권 곡선 시나리오 | FICC 금리 | 독립 검증됨 | BS-09 (P2), BS-10 (P2), BS-11 (P2), BS-24, BS-26, D03-V01 | Bonds Scenarios(Worst/Best 타일, 시나리오 차트, 표), narrate_bond, AI 페이로드 scenarios |
| 63 | M3-11 국채선물 헤지 비율 | FICC 금리 | 독립 검증됨 | BS-03, BS-05, BS-12, BS-13, BS-27, BS-28, BS-29, BS-30, BS-32, BS-33 | Bonds Futures hedge(Position DV01, CTD DV01, Conversion factor, Futures DV01, Contracts to sell, Rounded, 잔여 notice), 해설·AI 페이로드 hedge |
| 64 | M3-12 금리스왑 가격기 | FICC 금리 | 독립 검증됨 | financial_calcs/FC-02 (P1), D03-V01 (P1), financial_calcs/FC-05 (P2), FC-11, SF-07, functional_completeness/FC-03, D03-03, P01-05, TA-02, TA-07 | Rates Swap pricer(Par rate, Fixed, PV, DV01, Annuity, Carry (first period), Roll-down 1y 타일, KRD 차트, Forward swap 표), narrate_swap, AI 페이로드 |
| 65 | M3-13 Black-76·Bachelier 옵션식과 내재변동성 | FICC 금리 | 독립 검증됨 | FC-12 (P3), 신규 M3-N04, SF-07, TA-07 | Rates Swaption/cap-floor(Model 드롭다운, Other-model vol 타일); Derivatives 화면(core/ficc/equity_deriv.py:40, 175, 410, 502와 ui/derivatives_page.py:25, 43이 black76·implied_black_vol 재사용) |
| 66 | M3-14 스왑션 가격기 | FICC 금리 | 독립 검증됨 | financial_calcs/FC-02, financial_calcs/FC-05, SF-07, 신규 M3-N04, D03-03, TA-02 | Rates Swaption(Forward, Strike (ATM), Premium 통화·bp, Delta, Gamma, Vega, Theta (1d), Other-model vol 타일, annuity 칩), narrate_swaption, AI 페이로드 |
| 67 | M3-15 캡·플로어 가격기 | FICC 금리 | 독립 검증됨 | M-04 (P3), 신규 M3-N07, financial_calcs/FC-02, financial_calcs/FC-05, SF-07, D03-03 | Rates Cap/Floor(Strike (ATM), ATM (par swap), Premium, Caplets, Dearest caplet 타일, 캡렛 차트·표), narrate_cap_floor, AI 페이로드 |
| 68 | M3-16 단기금리 모형 보정 (Vasicek·CIR·Hull–White) | FICC 금리 | 코드로만 확인 | 신규 M3-N03, 신규 M3-N05(CIR θ 폭주로 연결, 원 정의 확인 필요), TA-02, TA-07 | Rates Rate simulation 타일(kappa, Half-life, theta, sigma, r0)과 출처 칩, narrate_ratesim, AI 페이로드 params; M3-20 SEP 밴드의 기반 모수 |
| 69 | M3-17 단기금리 닫힌식 할인채와 모형 곡선 | FICC 금리 | 독립 검증됨 | 신규 M3-N01, 신규 M3-N05, TA-02 | Rates Rate simulation 'Model zero at {h}y (median path)' 표, narrate_ratesim 곡선 문장, AI 페이로드 model_curve_at_horizon |
| 70 | M3-18 단기금리 경로 시뮬레이션 | FICC 금리 | 테스트로 확인됨 | 신규 M3-N03, 신규 M3-N05, 신규 M3-N09, BS-25(합성 곡선), D03-03, TA-02 | Rates Rate simulation(Mean at h, 90% range, P(> x) 타일, 팬 차트, 칩 paths·seed 7), narrate_ratesim, AI 페이로드 |
| 71 | M3-19 시평 재평가 VaR·CVaR | FICC 금리 | 코드로만 확인 | 신규 M3-N01, 신규 M3-N08, financial_calcs/FC-02(ratesim.py:340, 370), D03-03, TA-02 | Rates Rate simulation에서 Revalue = Bond/Payer swap일 때 Revalued, Mean PV, 90% range, VaR 95 (loss), CVaR 95 타일과 히스토그램, narrate_ratesim, AI 페이로드 horizon_pv |
| 72 | M3-20 SEP 오차대 금리 경로 | FICC 금리 | 테스트로 확인됨 | 신규 M3-N03(κ 편향 경유) | - (화면 호출 없음. core/quant/scenarios.py와 테스트에서만 쓴다. ui/ grep 0건) |
| 73 | M3-21 Diebold–Li 동적 NS 예측 연구 | FICC 금리 | 테스트로 확인됨 | K-a(requirements.txt는 6054b33에서 해결, pyproject.toml에는 아직 없음), TA-03 | Strategy Lab 카드 표와 카드 상세(M_B1_dns — REJECT), docs/asset_expansion/results.md |
| 74 | M3-22 PCA 중립 2-5-10 버터플라이 신호 | FICC 금리 | 테스트로 확인됨 | 신규 M3-N02, K-a(requirements.txt 해결, pyproject.toml 미선언), TA-03, functional_completeness/FC-02, functional_completeness/FC-05 | Strategy Lab 카드(S_B2_pca_fly — REVISE). Rates 화면에는 없다(functional_completeness/FC-05) |
| 75 | M3-23 Koijen 채권 캐리와 캐리 타이밍 (미사용) | FICC 금리 | 코드로만 확인 | - | - |
| 76 | M3-24 KRW 곡선 패널 (미연결) | FICC 금리 | 코드로만 확인 | SF-01 (P3), functional_completeness/FC-03 (P2), D03-V02 (P2) | - |
| 77 | M3-25 오프라인 합성 금리 데이터 (합성 국채 곡선 패널·합성 단기금리) | FICC 금리 | 테스트로 확인됨 | BS-25 (P3), BS-34, D03-03 | Rates·Bonds·Structuring의 'Synthetic …' 오류색 배너와 SYNTHETIC 칩, 그 화면들의 모든 오프라인 숫자 |
| 78 | M4-01 FX 선도(CIP)·선도 포인트·암시 베이시스·캐리 | FICC FX·변동성·구조화 | 테스트로 확인됨 | FC-11, SF-07, D03-10, D12-10, D03-03, D03-04, data_flow/MF-01, functional_completeness/FC-03, 신규 M4-N6 | FX 화면 'Spot, forward & carry': Spot, Forward, Points, Carry long, 두 금리 stat, Implied basis(≥5bp 빨강), 'flat rates across tenors' 칩, 선도 표, fx_spot_chart(ui/fcharts.py:238), AI 패널 kind=fx_forward |
| 79 | M4-02 Garman–Kohlhagen 옵션 가격·그릭스(GK 내재변동성 역산 포함) | FICC FX·변동성·구조화 | 독립 검증됨 | TA-07(병합 FC-15), FC-11, SF-07, D03-V02(병합 financial_calcs/FC-04), D03-03, D03-04 | FX 화면 'Option & smile': Premium, % of spot, Premium/1m, Delta(spot·forward), Gamma/1%, Vega/vol-pt, Theta/day, Rho 2종, AI kind=fx_option. Structuring 화면 옵션 다리 값 |
| 80 | M4-03 델타→행사가 변환과 ATM/RR/BF 3점 스마일 구성 | FICC FX·변동성·구조화 | 독립 검증됨 | FC-11, SF-07 | FX 화면 'Option & smile': Strike stat, 스마일 표(Point, Strike, Vol, Spot delta), 스마일 차트 |
| 81 | M4-04 SABR(Hagan 2002) 스마일 보정·보간 | FICC FX·변동성·구조화 | 독립 검증됨 | 신규 M4-N8 | FX 화면 'Option & smile': 'Vol used' stat, SABR 칩(rho, nu, rmse), 스마일 곡선 차트, 해설의 SABR 문장 |
| 82 | M4-05 FX 캐리 표(캐리, 3m vol, carry/vol, 모멘텀, 점수, 금리 신선도) | FICC FX·변동성·구조화 | 테스트로 확인됨 | data_flow/MF-01, functional_completeness/FC-03, D03-10, D12-10, D03-03, D03-04, D03-08 | FX 화면 'Carry basket': Best score, Highest carry stat, 캐리 막대 차트, 표(Pair~Score), 출처 칩, AI kind=fx_carry |
| 83 | M4-06 FX 캐리 바스켓 백테스트 | FICC FX·변동성·구조화 | 코드로만 확인 | FC-14, DF-04, data_flow/MF-01, D03-10, D12-10, K-e, functional_completeness/FC-03 | FX 화면 'Carry basket': Basket return, Ann. return, Ann. vol, Sharpe, Max drawdown, Equal-weight long stat, 기간·리밸런싱·long/short 칩, 자본곡선 차트, 해설·페이로드 |
| 84 | M4-07 FX 스타일 백테스트(횡단면 모멘텀, 달러 캐리) | FICC FX·변동성·구조화 | 코드로만 확인 | DF-04(같은 지연 규칙), K-e, FC-14(같은 정의, 판정 영향 없음) | - (UI 없음. docs/asset_expansion/results.md와 카드) |
| 85 | M4-08 Fama 회귀(UIP 검정) | FICC FX·변동성·구조화 | 코드로만 확인 | 신규 M4-N5 | - |
| 86 | M4-09 KOSPI200 선물 공정가치·베이시스·암시 조달금리 | FICC FX·변동성·구조화 | 테스트로 확인됨 | financial_calcs/FC-06, FC-13, D03-05, SFV-02, D05-06, P01-04, functional_completeness/MF-01 | 파생 화면 첫 stat 줄: Front future, Basis, Fair value, Mispricing(>20bp 빨강), Implied funding, KIS theo gap. 'rate … (source)' 칩. 해설·AI kind=kospi200_derivatives |
| 87 | M4-10 옵션 보드 내재변동성(Cboe 암시 선도 + Black-76 역산 + KIS IV 대조) | FICC FX·변동성·구조화 | 테스트로 확인됨 | FC-11, D05-06, P01-04, SFV-02, functional_completeness/MF-01, functional_completeness/FC-06, 신규 M4-N10(M_O1 카드 출처 라벨) | 파생 화면: Forward (parity), ATM IV, 'IV gap vs KIS'(게이트 0.5, 초록/빨강) stat, 'n quoted near-ATM' 칩, 스마일 차트(app 대 exchange IV), 장 마감 경고 배너, payload smile |
| 88 | M4-11 풋-콜 패리티 잔차와 정적 차익(수직·버터플라이) 검사 | FICC FX·변동성·구조화 | 코드로만 확인 | functional_completeness/FC-05(vertical 수는 payload에만), functional_completeness/MF-01, 신규 M4-N12 | 파생 화면: 'Butterfly viol.' stat, 해설의 패리티·버터플라이 문장, payload static_arbitrage |
| 89 | M4-12 SVI 스마일 적합과 Gatheral–Jacquier 버터플라이 조건 | FICC FX·변동성·구조화 | 테스트로 확인됨 | - | 파생 화면: 'SVI ρ', 'SVI RMSE'(>1.0 빨강) stat, 스마일 차트의 SVI 곡선, 해설 'arbitrage-free' 문구, payload svi |
| 90 | M4-13 모형무관 내재변동성(MFIV, Cboe 스트립) | FICC FX·변동성·구조화 | 독립 검증됨 | P01-04(체인 범위 결정 12.13), 신규 M4-N9 | 파생 화면: MFIV stat, 해설 'Model-free implied vol … (VKOSPI-style strip)', payload mfiv |
| 91 | M4-14 위험중립 밀도(SVI 위 Breeden–Litzenberger) | FICC FX·변동성·구조화 | 테스트로 확인됨 | functional_completeness/FC-05 | 파생 화면: 'RND ∫' stat, 밀도 차트(f_Q, GARCH 엔진이면 f_P), payload rnd |
| 92 | M4-15 박스 스프레드 조달금리 | FICC FX·변동성·구조화 | 테스트로 확인됨 | 신규 M4-N4 | 파생 화면: 'Box rate' stat, 해설 'The ATM box implies a KRW funding rate of … (±bp)', payload box_rate |
| 93 | M4-16 델타 헤지 손익 시뮬레이션(감마 항등식, GBM·GARCH-t 엔진) | FICC FX·변동성·구조화 | 테스트로 확인됨 | FC-12, 신규 M4-N7, functional_completeness/MF-01 | 파생 화면 헤지 줄: Hedge P&L(mean, 부호 색), SE, CVaR95, σ_h, Break-even realised vol, Identity slope/R², Engine. 해설(GARCH 엔진이면 ν·지속성 문장 포함)·payload hedge |
| 94 | M4-17 레버리지 ETF 드래그 식(Avellaneda–Zhang 2010) | FICC FX·변동성·구조화 | 독립 검증됨 | 신규 M4-N3(= NEW-M6-07) | ETF 화면(M4-18의 계산 엔진). 직접 표시는 M4-18 참조 |
| 95 | M4-18 ETF 화면의 레버리지·인버스 ETF 드래그 예측(GARCH-t 분산 경로, 직전 분기 분산) | FICC FX·변동성·구조화 | 코드로만 확인 | 신규 M4-N1(= NEW-M6-06), 신규 M4-N2(= NEW-M6-08), 신규 M4-N3(= NEW-M6-07), 신규 M4-N10, functional_completeness/FC-06, P01-09 | ETF 화면: '{name} drag, last-quarter vol'(빨강, 툴팁 'the study's better reference', :218-219), 'GARCH drag 21d/63d/252d', 'Index cond. vol', 'ν', 'Study verdict: GARCH drag'(:220-226); 해설 넷째 문장(:156-162); payload letf; README.md:289 |
| 96 | M4-19 VIX 기간구조 롤다운 전략(헤지된 VIX ETP 매도)과 ETP 드리프트 모니터 | FICC FX·변동성·구조화 | 테스트로 확인됨 | K-e, 신규 M4-N10 | - |
| 97 | M4-20 원금보장형 노트(PPN) | FICC FX·변동성·구조화 | 독립 검증됨 | D03-V02(병합 financial_calcs/FC-04), D03-V01, FC-16, D03-03, D03-04 | Structuring 화면 PPN: Fair value, Issue price, Margin, Participation, Greeks, payoff 차트, 다리 표, 헤지 시트, AI kind=structured_product |
| 98 | M4-21 역전환사채(RC) | FICC FX·변동성·구조화 | 독립 검증됨 | financial_calcs/FC-02, D03-V02(병합 financial_calcs/FC-04), D03-V01, FC-16 | Structuring 화면 RC: Fair value, Margin, Coupon (p.a.), Greeks, payoff, 다리, 헤지 시트, AI |
| 99 | M4-22 이중통화예금(DCD) | FICC FX·변동성·구조화 | 코드로만 확인 | D03-V02(병합 financial_calcs/FC-04), functional_completeness/FC-03, D03-V01 | Structuring 화면 DCD: Fair value, Margin, Enhanced yield (simple), Greeks, payoff, 다리, 헤지 시트, AI |
| 100 | M4-23 CMS 10y−2y 스티프너 노트 | FICC FX·변동성·구조화 | 미검증 | financial_calcs/FC-01, M-01, financial_calcs/FC-02, financial_calcs/FC-05, D03-V01, 신규 M4-N11 | Structuring 화면 Steepener: Fair value, Margin, Leverage, Coupon (p.a.)(첫 쿠폰), Greeks(dv01, 2s10s DV01), payoff 차트(x축 bp), 다리 표(쿠폰 일정), 헤지 시트, AI 해설(note 경고 포함) |
| 101 | M4-24 구조화 노트 그릭스(유한차분)와 헤지 시트 | FICC FX·변동성·구조화 | 테스트로 확인됨 | BS-32, D03-V02(병합 financial_calcs/FC-04), financial_calcs/FC-05 | Structuring 화면: Greeks stat 줄, 'Hedge sheet (+ buy / pay fixed, − sell / receive)' 표 |
| 102 | 매크로 시트 지표 통계(18개 지표 변화·z·백분위, 브리프 무버 순위) | 매크로·PIT·달력 | 코드로만 확인 | D04-01(P2), D03-02(P2), D04-02(P2), D03-04(P2, AI 페이로드), D03-06(P3), D03-08(P3), D0405-T1(P3), TA-02(P2), 신규 관찰(rel_1d 분모 0 근처 폭주, 감사 행 없음) | Macro 화면 'Macro sheet' 뷰(ui/macro_page.py:109-128 표, :160-167 타일·z 색); 'Daily market commentary'·'Weekly rates and FX note'(core/ficc/insights.py:380 narrate_daily_brief, deep_analysis 페이로드) |
| 103 | 매크로 서술적 판독(Descriptive read, 5개 임계값 규칙) | 매크로·PIT·달력 | 코드로만 확인 | D03-02(P2), D04-01(P2), D03-04(P2), TA-02(P2) | Macro sheet 뷰 판독 칩(ui/macro_page.py:75-86 read_row, :160); 리포트 페이로드 'regime' 키(macro.py:248) |
| 104 | PIT 저장소와 as-of 읽기(pit_value, pit_window, 순위, 분쟁 판정) | 매크로·PIT·달력 | 테스트로 확인됨 | C01-10(P2), V01-02(P3), D05-03(P3), D04-03(P3), 신규 관찰(pit_window 합성·auto 미거부, 잠재, 감사 행 없음) | 직접 화면 없음. Overlay state 뷰의 inputs 표·data snapshot 칩(ui/macro_state_panel.py:180-202, :431-449)과 모든 macro_state 숫자의 원천 |
| 105 | 타임스탬프·값 상태 부여 규칙(stamping, 종가 10분 격리) | 매크로·PIT·달력 | 테스트로 확인됨 | D05-03(P3), CAL-12(P3, d865c7f 반영, 서명 대기), C01-03(P2, TA-04 병합), K-h | 간접: Overlay state inputs 표의 value_status 열, dry run 빨간 칩 |
| 106 | 월간 달력 오프셋 산술(YoY·MoM·3개월 평균) | 매크로·PIT·달력 | 테스트로 확인됨 | - | Overlay state 'Context log' 타일, Hedge 칩(core_pce) |
| 107 | 세션 시계와 교차시장 사용 가능 시각(결정 시각, gap_sessions) | 매크로·PIT·달력 | 테스트로 확인됨 | CAL-01(P1, D12-08 병합), CAL-02(P1), CAL-03(P2), CAL-08(P2), CAL-10(P2), M-2(P2), CAL-13(P3), CAL-14(P3), M-4(P3) (d865c7f 반영, 서명 대기); CAL-06(P2), CAL-11(P2), M-3(P2, 레거시), D12-07(P2) | Overlay state 결정 세션 칩·Gap 칩(ui/macro_state_panel.py:380-381), 'Live' 실행 비활성 툴팁. 간접적으로 모든 macro_state |
| 108 | 발행 시각과 결측 발표(stale) 판정 | 매크로·PIT·달력 | 테스트로 확인됨 | CAL-07(P2), CAL-09(P3), CAL-04(P3)·CAL-05(P3)·CAL-12(P3)(d865c7f 반영, 서명 대기) | Overlay state 입력 상태(stale, stale_missed_release)와 경보 |
| 109 | 연율화 일수 표(ANNUALISATION_DAYS) | 매크로·PIT·달력 | 코드로만 확인 | D12-11(P1, M-03 병합), M-2(P2, d865c7f 반영: 같은 테스트가 이제 미서명 픽스처를 쓴다) | 직접 표시 없음. 영향 화면: Quant Lab 'Vol (ann.)'·'Drift (ann.)', Signals Sharpe, Strategy Lab 판정, Model cards의 CRY-1 줄 |
| 110 | 독립 지연 감사(lag_audit) | 매크로·PIT·달력 | 테스트로 확인됨 | CAL-01, CAL-03(d865c7f 반영, 서명 대기. 같은 달력에 기대 감사가 달력 오류를 못 잡는 구조는 남는다), C01-03(mtime 수신 시각은 close+10분 검사를 통과할 수 있음), 신규 관찰(창 행 미감사·백테스트 공급사 기준 불일치, 감사 행 없음) | Overlay state Flags 'lag audit: n checked, k violation(s)' 칩(ui/macro_state_panel.py:382-383), HALT 배너 |
| 111 | R-06 시장 변동성 목표(vt, SMA20) | 매크로·PIT·달력 | 테스트로 확인됨 | TA-01(P2, 골든 자리표시자), C01-03(P2, dry run 입력) | Overlay state Vol strip('vt next (specification)', 'vt (recommended book)', ui/macro_state_panel.py:340-357), Composition 줄 |
| 112 | 변동성 표시 라벨(calm/normal/elevated/stressed) | 매크로·PIT·달력 | 테스트로 확인됨 | - | Overlay state Vol strip 'relative/absolute' 칩(ui/macro_state_panel.py:352-353) |
| 113 | R-02 min() 합성과 gross 한도 | 매크로·PIT·달력 | 테스트로 확인됨 | - | Overlay state 북 타일 composed·gross, Composition 줄과 multiplier bar(ui/macro_state_panel.py:210-288) |
| 114 | R-09 헤지 유효성 상태(hedge_state, corr63, 근원 PCE) | 매크로·PIT·달력 | 테스트로 확인됨 | V01-03(P2), CAL-06(P2), 신규 관찰: apply_hedge_state 미연결(감사 행 없음) | Overlay state Flags 'Hedge' 칩 묶음(ui/macro_state_panel.py:361-368) |
| 115 | R-07 한국 집중도 한도(ETF 투시, MSCI 25/50) | 매크로·PIT·달력 | 테스트로 확인됨 | 신규 관찰(미연결, 감사 행 없음). 데이터 공백은 README 'Open owner actions'의 KODEX 200 PDF basket | Overlay state Composition 둘째 줄 'gross = min(composed, bound …)'(ui/macro_state_panel.py:271-272) |
| 116 | R-31 드로다운 사다리와 R-07 hard stop | 매크로·PIT·달력 | 테스트로 확인됨 | M-1(P1), CAL-07(P2), TA-01(P2) | Overlay state Flags 'Ladder' 칩과 hard stop 상태, HALT 배너(ui/macro_state_panel.py:245-274, :369-375) |
| 117 | 북 런타임 상태기계(ARM/DISARM/HALT)와 북 NAV 평가 | 매크로·PIT·달력 | 테스트로 확인됨 | M-1(P1), CAL-07(P2), CAL-08(P2, d865c7f 반영, 서명 대기), 신규 관찰(NAV 분배금 미반영, 감사 행 없음) | Overlay state 북 타일(엔진 상태), HALT 배너와 Acknowledge, Alerts(ui/macro_state_panel.py:210-274, :400-428) |
| 118 | R-03 슬리브 변동성 스케일과 R-04 Daniel-Moskowitz 게이트 | 매크로·PIT·달력 | 테스트로 확인됨 | K-e(종이 시리즈의 무비용 리밸런싱 가정), TA-01(P2) | Overlay state overlays 표(specification 북), Flags 'D-M bear state' 칩(ui/macro_state_panel.py:376-377); Model cards 뷰 MACRO-R03-US-MOM, MACRO-R04-US-DM |
| 119 | R-13 맥락 로그 계산기(Sahm, probit, Taylor, VRP, rv21, SMA10m, 난류) | 매크로·PIT·달력 | 테스트로 확인됨 | D04-03(P3), V01-03(P2), 신규 관찰(KOSPI 추세 월말 지연, probit 계수 원천 미대조) | Overlay state 'Context log' 접힘 타일(ui/macro_state_panel.py:477-495) |
| 120 | R-10 이벤트 창·갭 태그와 R-08 VIX 기간구조 주석 | 매크로·PIT·달력 | 테스트로 확인됨 | CAL-01(P1), CAL-02(P1), CAL-03(P2)(d865c7f 반영, 서명 대기) | Overlay state Flags 'Gap'(gap sessions, VaR display scale)·'Annotation'(VIX ≥ VIX3M) 칩, Event calendar 타일(ui/macro_state_panel.py:379-384, :498-517) |
| 121 | R-28 추세 축과 R-29 미국 선물 vt(FORWARD-SIM 표시 북) | 매크로·PIT·달력 | 테스트로 확인됨 | 신규 관찰(vt_us·월말 창 간격·최신성 미검사, 감사 행 없음) | Overlay state 'FORWARD-SIM · not a recommendation' 그룹(ui/macro_state_panel.py:319-337); Model cards 뷰 MACRO-R28-US-TREND, MACRO-R06-US-FUT |
| 122 | R-11·R-12 거부 북(refusal books, 표시 전용) | 매크로·PIT·달력 | 테스트로 확인됨 | V01-03(P2), 신규 관찰(창 상태·최신성 미검사, 감사 행 없음) | Overlay state 'REFUSAL BOOK · not a recommendation' 그룹; Model cards 뷰 MACRO-R11-KR-KRW, MACRO-R12-US-RATES |
| 123 | R-25 forward record 감시와 강등(CUSUM, 파국 경계) | 매크로·PIT·달력 | 테스트로 확인됨 | - | Model cards 뷰(강등·lockout 표시), Overlay state 경보 |
| 124 | 사전 등록 비용과 틱 하한(R-26 비용 모형) | 매크로·PIT·달력 | 테스트로 확인됨 | functional_completeness/MF-02(P2) | Model cards 헤더 비용 줄; Overlay state는 NAV를 통해 간접 |
| 125 | 시뮬레이션 체결 모형(공식 종가 체결, 상하한가 잠김) | 매크로·PIT·달력 | 테스트로 확인됨 | - | - |
| 126 | 시나리오 라이브러리(M9 충격 창, SEP 금리 밴드) | 매크로·PIT·달력 | 테스트로 확인됨 | - | - (화면 연결 없음) |
| 127 | dry run 대체 시계와 공급사 캐시 수집 | 매크로·PIT·달력 | 테스트로 확인됨 | C01-03(P2, TA-04 병합), K-h, CAL-10(P2, d865c7f에서 KRX.json 행 반영, 고정 경계는 남음), SF-06(P2) | Overlay state 'Run macro_daily → Dry run (local vendor data)' 버튼(ui/macro_state_panel.py:730), Artifacts 'Dry run', 빨간 칩 'VENDOR DATA · DRY RUN' |
| 128 | 테크펀드 스크린과 북 엔진(SCR-1/2, B1-B4, FS-2) | 매크로·PIT·달력 | 테스트로 확인됨 | - | 직접 화면 없음. Model cards 뷰의 테크펀드 카드 초안은 docs/techfund/*.draft.json 정적 파일이다(ui/macro_cards_view.py:26, :159, :239). Research register 뷰 가중치 표(w/3 열)는 council_pages_data.json의 정적 R3 사전값이다(ui/research_view.py:86-110, :288-293). 이 모듈의 계산값이 아니다. |
| 129 | 테크펀드 거버넌스 통계(GOV-1..11: SPA, BH FDR, 귀속, β 북) | 매크로·PIT·달력 | 테스트로 확인됨 | - | 직접 화면 없음. Model cards 뷰 CRY-1 줄(docs/techfund_study.py 산출 JSON을 통해 간접) |
| 130 | CRY-1 대조 실험(크립토 카드 C3 추세, 공급사 캐시) | 매크로·PIT·달력 | 코드로만 확인 | D12-11(P1, M-03 병합), TA-12(P3), 신규 관찰(CRY-1 표시값 √252) | Macro → Model cards 뷰 'CRY-1 control results (crypto card C3)'(ui/macro_cards_view.py:177-205, :242-245) |
| 131 | R-30 변동성 추정기 경주와 단계 게이트(SMA20 대 EWMA·GARCH-t·GJR-t·log-HAR·comb) | 매크로·PIT·달력 | 테스트로 확인됨 | TA-01(P2, REFDATA NOT_RUN 대부분 재현 코드 대기) | Overlay state Vol strip의 estimator 필드(estimator_b5 NOT_RUN, ui/macro_state_panel.py:340-357) |
| 132 | M6-01 김치 프리미엄 수준과 1년 z | 가상자산·기타 | 테스트로 확인됨 | V01-01, D03-01, D03-08, DF-06, D12-03, DF-03, SFV-01, P01-09, NEW-M6-15 | Crypto: stat 'Kimchi premium'(\|p\|>3%면 빨강, :163), 'Premium z (1y)'(:164); 차트 'Kimchi premium (Upbit KRW-BTC vs Binance × USD/KRW)'(:171); 칩 'USD/KRW: {source}'(:159); 해설 첫 문장(:103-105); AI 페이로드 kimchi(:125-126) |
| 133 | M6-02 김치 프리미엄 7일 예측 회귀(기울기, Newey–West t) | 가상자산·기타 | 미검증 | NEW-M6-01 | Crypto 해설 '…its predictive slope on next-week returns is … (t …)'(ui/crypto_page.py:106); AI 페이로드 kimchi.pred_t(:126); 카드 M_C1 문장 |
| 134 | M6-03 평균회귀 진단(ADF p, AR(1) 반감기) 공용 함수 | 가상자산·기타 | 테스트로 확인됨 | functional_completeness/FC-02 (병합: TA-03), K-a(requirements.txt만 반영), NEW-M6-03 | Crypto stat 'Half-life'(:164)와 해설 ADF p; ETF 칩 'half-life … sessions', 'ADF p'(ui/etf_page.py:210-211)와 해설(:140-144); Strategy Lab pairs 진단(M2) |
| 135 | M6-04 펀딩 캐리 연율화, 백분위, 과밀 플래그 | 가상자산·기타 | 코드로만 확인 | DF-03, SFV-01, NEW-M6-13 | Crypto stat 'Funding (ann.)'(플래그면 빨강, 툴팁 플래그), 'Funding pct'(:165-167); 차트 'Perpetual funding, 7-day mean annualised'(:173-175); 해설 둘째 문장(:109-111); AI 페이로드 funding(:127-128) |
| 136 | M6-05 펀딩 십분위 이벤트 스터디와 부트스트랩 p | 가상자산·기타 | 미검증 | NEW-M6-02 | Crypto 해설 '…after top-decile funding … (bootstrap p …)'(:110-111); 판정 칩 'funding: PASS'(녹색, :160); AI 페이로드 funding; README.md:286 |
| 137 | M6-06 ETH/BTC 단위근 검정 | 가상자산·기타 | 코드로만 확인 | functional_completeness/FC-02 (병합: TA-03), PA-10 | Crypto 해설 'ln(ETH/BTC): …'(:117); 판정 칩 'ethbtc: REJECT'(:160); AI 페이로드 ethbtc(:130) |
| 138 | M6-07 요일 표(요일 효과, 주말 거래대금) | 가상자산·기타 | 테스트로 확인됨 | NEW-M6-10, DF-03 | Crypto 카드 'Weekday table (returns %, vol %, mean quote volume)'(:180-185); AI 페이로드 weekday(:130) |
| 139 | M6-08 BTC GARCH(1,1)-t 화면 적합과 365일 환산 | 가상자산·기타 | 코드로만 확인 | D12-11 (병합: M-03), functional_completeness/MF-01, NEW-M6-20 | Crypto stat 'BTC cond. vol (365d)', 'ν'(경계면 빨강, :169); 해설 GARCH 문장과 판정(:112-116); AI 페이로드 garch(:130) |
| 140 | M6-09 GARCH 롤링 스코어카드(GARCH-t, GJR-t, GJR-skew-t 대 EWMA) | 가상자산·기타 | 테스트로 확인됨 | financial_calcs/FC-08, NEW-M6-21 | Crypto 판정 칩 'garch_btc', 'skewt_btc'(:94-96, :160); 해설 GARCH 판정 문장(:115-116) |
| 141 | M6-10 Crypto 화면의 C3 판정 칩과 이동평균 표시(모델 아님, 규칙은 M2-07) | 가상자산·기타 | 코드로만 확인 | functional_completeness/FC-04, functional_completeness/MF-01(규칙의 오류는 M2-07) | Crypto 판정 칩 'crypto_trend_btcusd', 'crypto_trend_krwbtc'(ui/crypto_page.py:160); 차트 'BTCUSDT with 50/200-day averages'(:176-179) |
| 142 | M6-11 크립토 공급사 파생 표시값(perp premium, Upbit 보유 평가) | 가상자산·기타 | 코드로만 확인 | SFV-01, NEW-M6-14, NEW-M6-18, NEW-M6-22 | Crypto stat 'Perp premium'(:168); 카드 'Upbit holdings (read-only): ₩…'(:188-192); AI 페이로드 premium_index, holdings(:129, :131) |
| 143 | M6-12 ETF NAV 괴리율 통계 | 가상자산·기타 | 코드로만 확인 | M01, NEW-M6-03, D05-06, functional_completeness/MF-01, functional_completeness/FC-02 (병합: TA-03) | ETF stat 'Price', 'NAV', 'Premium'(\|p\|>0.5%면 빨강), 'Tracking error', 'AUM', 'CU shares', 'LP holding'(:201-207); 칩 'premium z', '\|premium\| mean', 'half-life', 'ADF p'(:210-213); 차트 '{code} price vs NAV'(:214-215); 해설 첫째·둘째 문장(:135-144) |
| 144 | M6-13 ETF 슬리브 표본 내 요약(추세 전환, 변동성 목표, 매수 보유) | 가상자산·기타 | 테스트로 확인됨 | NEW-M6-04, NEW-M6-05, functional_completeness/MF-02, FC-14, P01-11, K-e, TA-02 | ETF stat 'Trend switch Sharpe', 'Trend MDD', 'Vol-target Sharpe', 'Buy & hold Sharpe', 'B&H MDD', 'Study verdict: trend', 'Study verdict: vol target'(:229-237); 차트 '10-month trend switch vs buy-and-hold'(:238-239); 해설 셋째 문장(:147-152) |
| 145 | M6-15 KRX·KIS 공급사 지표 표시(모델 아님) | 가상자산·기타 | 코드로만 확인 | D05-01, D05-02, D05-05, D05-06, D0405-V02, TA-05, C01-04, M01, NEW-M6-17 | KRX 화면 표(Quote, Daily OHLCV, Disclosures, Financials, Whole-market snapshot, Index levels); ETF 시세 타일(:201-207)과 'Top constituents' 카드(:240-245) |
| 146 | M6-16 Quant 로컬 해설(core/quant/insights.py, 결정적 문장) | 가상자산·기타 | 테스트로 확인됨 | D03-03, P01-13, NEW-M6-16 | Quant Lab(narrate_monte_carlo), Signals(narrate_signals + narrate_backtest), Portfolio(narrate_portfolio)의 'Analysis' 카드(칩 'engine: local'). Strategy Lab 해설은 ui/strategy_lab_page.py 자체 함수라 이 모듈이 아니다(M2). |
| 147 | M6-17 FICC 로컬 해설(core/ficc/insights.py, 결정적 문장) | 가상자산·기타 | 테스트로 확인됨 | D03-03, M-01, D04-01, PA-12, PA-13, TA-02, NEW-M6-11 | Rates, Bonds, FX, Structuring, Macro 화면의 'Analysis' 카드; Macro Daily/Weekly 보고서 버튼(ui/macro_page.py:140-149) |
| 148 | M6-18 Crypto·ETF 화면 해설과 AI 페이로드 | 가상자산·기타 | 코드로만 확인 | D03-01, DF-06, NEW-M6-01, NEW-M6-02, NEW-M6-03, M4-N2(= NEW-M6-08), NEW-M6-18, TA-02 | Crypto 'Analysis' 카드(kind crypto_market, :197-198), ETF 'Analysis' 카드(kind etf_structure, :246-247) |
| 149 | M6-19 AI 심층 분석(Claude 서술, 모델 아님) | 가상자산·기타 | 미검증 | D03-04, D03-01, P01-13, NEW-M6-12, NEW-M6-18, NEW-M6-19 | 모든 분석 화면의 'Deep analysis' 버튼과 결과 카드(칩 'engine: {model}', ui/ai_panel.py:51-54) |
| 150 | N-01 Execution 가격 조건 규칙 평가기와 시세 신선도 가드(모의주문, 모델 아님) | 전수 점검에서 추가 | 테스트로 확인됨 | D-05, D05-01, D05-02, D05-03, D05-04, D05-05, D05-06, D0405-V01, D0405-V02, D0405-T1, 감사 12.5; 신규(미등재): 일 한도 UTC 날짜 경계 | Execution 화면(ui/trading_page.py: 엔진 상태, 결정 로그 사유, 모의주문 목록), Rules 화면(ui/rules_page.py: 검증 메시지) |
| 151 | N-02 화면 데모·대체용 합성 데이터(FX 현물, Crypto 데모, KOSPI200 데모 보드와 지수 경로) | 전수 점검에서 추가 | 테스트로 확인됨 | D-03, D03-01, D03-02, D03-06, D03-08, D03-10, functional_completeness/MF-01, 감사 12.6; 신규(미등재): Derivatives 데모 만기 칩·고정 베이시스 | FX 화면(합성 배너·muted 칩), Crypto 화면(Synthetic 선택 시 배너. live에서 USD/KRW만 합성이면 배너 없음), Derivatives 화면('Synthetic board' 배너) |
| 152 | N-03 R-18 구조 변화 프로토콜(선언 이벤트·재고정, CUSUM 통계 플래그, v1.2 스케일 플래그, BOCPD) | 전수 점검에서 추가 | 테스트로 확인됨 | - | - |
| 153 | N-04 R-19 데이터 계약 검사와 역할별 실패 동작, 연속 실패 HALT 카운터 | 전수 점검에서 추가 | 테스트로 확인됨 | 신규(미등재) 3건: 단조 조항 미작동, 위반 사유 소실, NAV 라인 계약 없음 | Macro 화면 Overlay state 패널(입력 상태와 HALT 사유, ui/macro_state_panel.py), 경보 배너(core/skills/alerts.py) |
| 154 | N-05 R-15 패밀리 허용(사전 점수)과 1/K 기본 비중, 슬리브 오버레이 적용과 북 조립 | 전수 점검에서 추가 | 테스트로 확인됨 | - | - |
| 155 | N-06 R-35 권고 북 승인 규칙, 판정 필터, 처분 매핑과 산출물 경계 게이트 | 전수 점검에서 추가 | 테스트로 확인됨 | functional_completeness/FC-07, 감사 12.11, K-g | Macro 화면 Overlay state 패널과 Model cards 뷰(판정·처분 칩, ui/macro_state_panel.py, ui/macro_cards_view.py) |
| 156 | N-07 KOSPI200 만기일 규칙, 근월물 선택, 연속 선물 스플라이스(data/kis_markets.py) | 전수 점검에서 추가 | 테스트로 확인됨 | data_flow/MF-02, 감사 12.13; 신규(미등재): 만기일 휴장 미조정, 대체 근월물 코드 고정 | Derivatives 화면(만기 칩 'expiry → 날짜', T를 쓰는 모든 타일과 차트) |
| 157 | N-08 가격 시계열 데이터 점검(validate.data_checks, 미연결) | 전수 점검에서 추가 | 코드로만 확인 | D-01, D-02, 감사 12.7 | - |

## 6. 모델별 상세

### 6.1 리스크·시뮬레이션

#### 1. M1-01 일간 수익률과 연율화 관례 (History, TRADING_DAYS=252)

- **위치:** core/quant/history.py:TRADING_DAYS:47; core/quant/history.py:History.log_returns:88-90; core/quant/history.py:History.simple_returns:92-94; core/quant/history.py:_clean_rows:97-102; core/quant/history.py:convention_warning:105-117; core/quant/history.py:fmp_history:186 (adjustment); core/quant/history.py:yf_history:279-281 (adjustment); core/quant/history.py:load_history:464-511; core/quant/garch.py:TRADING_DAYS:70 (별도 상수 252); core/calendars/clocks.py:ANNUALISATION_DAYS:30 (CRYPTO 365, 이 경로들은 쓰지 않음)
- **목적:** 모든 위험·시뮬레이션 모형의 공통 입력이다. 종가를 일간 로그수익률로 바꾸고, 일간 평균·분산을 252로 연율화한다.
- **가정:**
  - 종가 1개가 세션 1개다. 날짜 오름차순, 중복·결측 없음을 가정한다. 검사는 없다.
  - r = ln(P_t/P_{t-1}). 단순수익률은 simple_returns로 따로 있다.
  - 연간 봉 수는 항상 252다(history.py:47, garch.py:70). 24시간 가상자산(연 365봉)도 252로 연율화한다.
  - 가격 조정: FMP는 adjClose가 있으면 total, 없으면 split이다(history.py:186). KIS 국내·해외는 split이다. Yahoo는 total이고 ^·=F·=X·-USD·-KRW 기호만 ''다(history.py:279-281). 합성은 ''다.
  - _clean_rows는 None과 0 이하를 기록 없이 버린다(history.py:98). NaN과 −inf도 이 조건에서 빠진다. +inf와 중복 날짜는 남는다. 날짜는 문자열로 정렬한다.
  - _clean_rows는 FMP·KIS 국내·Yahoo 경로에만 있다. 가상자산(Candles.to_history)과 KIS 기타(Bars.to_history) 경로는 거치지 않는다(D12-03).
  - 금리 계열(Y0xxx, ^TNX)도 같은 History로 들어온다. 단위 필드가 없다.
- **한계:**
  - 가상자산: Quant Lab 'Vol (ann.)'가 ×0.831, MC 드리프트가 1.45배다(D12-11/M-03). 합성 3년·σ 80% 재현에서 sigma_annual 0.6645 대 √365 기준 0.7997(비율 0.8309)이다.
  - +inf 종가 1개면 MC는 sigma nan, VaR 0%가 된다(montecarlo.py:327 max(0.0, nan); D12-01). analyze_history는 ann_vol이 nan인데 var_1d는 무의미한 유한값(이번 재현 0.0162)을 낸다.
  - 같은 날 2배 값 행 1개면 ann_vol 0.329→0.939, MC VaR 13.5%→36.0%다(D12-02, 감사 재현값).
  - 504세션 중 50세션이 빠지면 ann_vol 0.1916→0.2047(+6.8%)이다. 간격 검사가 없다(D12-07, 감사 재현값).
  - 롤 조정 없는 연속 선물(=F)과 쿠폰 없는 채권 가격이 그대로 들어간다(DF-05).
  - 금리 계열을 넣으면 수치가 무의미하고 부호가 반대다(DF-01).
  - 총수익·가격수익 혼합은 경고만 한다. 경고의 처방 문구가 auto 경로와 맞지 않는다(MF-03).
- **적용 범위:** 평일 세션 주식·ETF·지수의 일간 종가에 쓴다. 가상자산의 연율화 값은 PT-02 전에는 쓰지 않는다. 금리·수익률 계열과 롤 미조정 선물에는 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_risk_vol_and_drawdown_match_numpy_whatever_engine(√252), ::test_each_loader_states_its_return_convention, ::test_a_panel_mixing_total_and_price_return_series_is_called_out, ::test_load_history_rejects_blank_and_unknown_source (qa/acceptance_results.json PASS). tests/macro_m9_lab.py::test_t_crypto_01_clock_annualisation_and_no_crypto_sleeve(T-CRYPTO-01)는 시계 함수만 365로 확인하고 이 경로는 확인하지 않는다. financial_calcs.md 검증 절 M-03(m03_crypto_annualisation.py). 재현 work/m1_risk_sim/v1_mc.py 1번(비율 0.8309, 이번에 다시 돌려 같음). work/m1v/v1_checks.py e)(+inf 1개: MC sigma nan·VaR 0.0, analyze_history ann_vol nan·var_1d 0.0162). 정제 로직 테스트 0건(감사 보고서 7.7, TA-06).
- **관련 오류:** D12-11(병합 M-03, P1), D12-01, D12-02, D12-03, D12-05, D12-06, D12-07, D12-12, D12-13, D12-14, DF-01, DF-05, MF-03, TA-06, C01-01
- **화면:** load_history를 쓰는 모든 화면: Quant Lab, Portfolio, Signals, Strategy Lab, ETF. Crypto 화면만 365로 따로 환산한다(ui/crypto_page.py:75-76).

#### 2. M1-02 합성 가격 경로 (synthetic_history)

- **위치:** core/quant/history.py:synthetic_history:232-260; core/quant/history.py:load_history:479-480,491-511 (키 없을 때 대체); ui/quant_lab_page.py:run:305-307 (경고 배너); ui/portfolio_page.py:run:131-138 (경고 배너); ui/etf_page.py:100-103 (합성 KOSPI200 지수)
- **목적:** 공급자 키가 없을 때 화면이 동작하게 하는 데모 가격 경로다. 기호마다 결정적이다.
- **가정:**
  - GBM이다. μ = 2%+(seed%17)%, σ = 14%+(seed%23)%, 시작가 20+(seed%400). seed는 기호 sha256의 앞 4바이트다.
  - dt = 1/252, 로그 드리프트 (μ−½σ²)dt.
  - 날짜는 오늘부터 거꾸로 평일만 만든다. 휴장일은 없다.
  - source='SYNTHETIC'과 note로 표시한다.
- **한계:**
  - 시장 정보가 전혀 없다. 모든 숫자가 데모다.
  - 평일만 만들어 실데이터와 섞으면 교집합에서 행이 빠진다(D12-15).
  - 끝 날짜가 date.today()라 날짜는 매일 바뀌고 값은 같다.
  - Quant Lab·Portfolio는 오류색 배너를 띄운다. AI 해설과 일부 칩은 출처 표시가 약하다(D03-04, D03-08).
- **적용 범위:** 화면 시연과 테스트 전용이다. 판단·보고에 쓰지 않는다. acting 경로는 SYNTHETIC을 거부한다.
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_synthetic_is_deterministic_per_symbol, ::test_auto_routing_falls_back_to_labeled_synthetic, ::test_explicit_provider_without_key_raises_not_simulates; tests/expansion_acceptance.py 'history_auto_degrades_without_keys'(:329); tests/macro_m1_pit.py::test_syn_01_synthetic_rejected_for_acting_allowed_for_context. 코드 읽기로 μ·σ·seed 식을 다시 확인했다(history.py:240-247).
- **관련 오류:** D12-15, D03-04, D03-06, D03-08
- **화면:** Quant Lab(배너 ui/quant_lab_page.py:305-307), Portfolio(배너 ui/portfolio_page.py:131-138), Signals, Strategy Lab, ETF LETF 표(source 'synthetic index')

#### 3. M1-03 단일 자산 위험 통계 (analyze_history: 역사적 1일 VaR·CVaR, 변동성, Sharpe, Sortino, MDD)

- **위치:** core/quant/risk.py:analyze_history:63-118 (gs_quant 분기 71-85, 연율화 84-95, VaR·CVaR 98-101, 0 클립 114, 왜도·첨도 103-106); core/quant/insights.py:narrate_risk:172-193
- **목적:** 단일 계열의 연 수익·변동성, Sharpe·Sortino·Calmar, 최대낙폭, 1일 역사적 VaR·CVaR, 왜도·첨도를 계산한다.
- **가정:**
  - 로그수익률 평균×252가 연 수익, 표준편차(ddof 1)×√252가 연 변동성이다(iid).
  - rf 기본 3%(인자). Sharpe = (ann_ret − rf)/ann_vol. Sortino는 음수 수익률만의 표준편차를 쓴다.
  - VaR는 손실 −r의 경험적 95% 분위(np.percentile 선형 보간)다. 단위는 로그 손실이다(필드 주석은 '+fraction'). CVaR는 VaR 이상 손실의 평균이다. 둘 다 0 아래를 0으로 자른다(risk.py:114).
  - gs_quant가 있으면 오늘에서 끝나는 영업일 색인(bdate_range)을 만들어 vol·MDD를 계산한다. 실제 날짜를 쓰지 않는다. 이 환경에는 gs_quant가 없어 local 분기만 돈다.
  - 21세션 이상이 필요하다.
- **한계:**
  - HEAD에서 화면 소비처가 없다. analyze_history와 narrate_risk는 테스트에서만 불린다(ui/ 호출 0건).
  - 가상자산을 252로 연율화한다(D12-11의 risk.py 부분). 화면이 없어 지금 보이는 영향은 없다.
  - VaR가 로그 손실이라 큰 손실에서 단순 손실보다 크다(단순 5% 손실 = 로그 0.0513).
  - VaR·CVaR를 0에서 자른다. 이익만 나는 표본이면 0.0으로 보이고 숫자가 숨는다(ARCHITECTURE_REVIEW C2).
  - 결측 세션을 모른다(D12-07).
  - 504세션이면 95% 꼬리 표본이 25개뿐이다.
- **적용 범위:** 평일 주식 계열의 서술 통계다. 가상자산 연율화 값과 예측 VaR로 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_risk_vol_and_drawdown_match_numpy_whatever_engine(vol·MDD가 numpy와 1e-6 안), ::test_risk_var_cvar_bounds(0≤VaR≤\|최악일\|, CVaR≥VaR; 모양 검사), ::test_narratives_state_their_numbers. 이 환경에서 import gs_quant는 ModuleNotFoundError다. 그래서 첫 테스트는 local 분기만 확인한다. 외부 기준값 대조는 없다.
- **관련 오류:** D12-11(병합 M-03; risk.py:84,87,90,93), D12-07(risk.py:75 bdate_range), D12-01, ARCHITECTURE_REVIEW C2(감사 행 없음)
- **화면:** - (화면 없음. insights.narrate_risk도 테스트만 호출)

#### 4. M1-04 바스켓 수익률 통계 (align_histories, portfolio_point)

- **위치:** core/quant/risk.py:BasketStats:124-131; core/quant/risk.py:align_histories:134-160 (교집합 140-146, 평균 153, 공분산 154); core/quant/risk.py:portfolio_point:163-170; 소비 core/quant/optimize.py:optimize_portfolio:68-100, efficient_frontier:103-131; ui/portfolio_page.py:run:111-117,146-193
- **목적:** 여러 종목을 공통 날짜로 맞춰 연 평균수익률 벡터·공분산·상관을 만들고, 비중 벡터의 연 수익·변동성·Sharpe를 계산한다. Portfolio 최적화(M1-23)의 입력이다.
- **가정:**
  - 날짜 교집합만 쓴다. 같은 날짜의 종가를 같은 시점으로 본다(KRX·미국 종가 시각 차이 무시).
  - 평균 = 로그수익률 평균×252, 공분산 = 로그수익률 공분산×252(ddof 1).
  - 수익률은 iid·정상이고 약 504세션 표본 추정치가 미래 모수다.
  - Sharpe = (w·μ − rf)/√(wΣw). rf는 화면 입력이다(기본 3%).
  - 공통 세션 31개 이상, 종목 15개 이하(화면).
- **한계:**
  - 기대수익률이 로그 평균이라 산술 평균보다 ½σ² 낮고 분산 효과가 빠진다. 2자산 GBM(μ 8%/40%, σ 15%/60%, ρ 0.2) 50/50 표본에서 화면 12.69% 대 산술 22.34%, Sharpe 0.298 대 0.595다. 모집단 최대 Sharpe 비중은 로그 평균 기준 (0.746, 0.254), 산술 기준 (0.604, 0.396)이다(M-02).
  - KRX·미국 혼합 바스켓은 종가 시각 차이로 상관이 낮게 잡혀 분산 효과가 과대하다(DF-02).
  - 교집합에서 행이 조용히 빠진다. 결측이 변동성을 키운다(D12-07).
  - 가상자산만 담은 바스켓(365봉 격자)도 252로 연율화한다(D12-11).
  - 표본 평균의 표준오차가 커서 최적 비중이 불안정하다(drift study: 표본 평균의 예측력 없음).
- **적용 범위:** 같은 거래소·같은 종가 시각의 주식·ETF 바스켓에서 공분산·상관 서술에 쓴다. 기대수익률과 최대 Sharpe 비중은 M-02 수정 전에는 판단에 쓰지 않는다.
- **검증 상태:** 미검증. 독립 대조에서 결론을 바꾸는 결함(M-02): docs/audit/2026-10-27/financial_calcs.md:617-646(검증 절 M-02, m02_portfolio_logmean.py). 2자산 GBM 50/50 표본에서 화면 수익 12.69% 대 산술 22.34%, Sharpe 0.298 대 0.595, 모집단 최대 Sharpe 비중 (0.746, 0.254) 대 (0.604, 0.396). 감사 보고서 609행. 테스트는 tests/quant_acceptance.py::test_align_histories_requires_overlap(겹침 부족 오류)뿐이고 평균값을 대조하는 테스트는 없다. ui/portfolio_page.py는 테스트 참조 0건(감사 보고서 7.7).
- **관련 오류:** M-02, DF-02, D12-07, DF-01, D12-11
- **화면:** Portfolio: return %/yr·vol·Sharpe 칩(ui/portfolio_page.py:146-153), 네 목적 비교표(:159-174), 효율적 프런티어(:176), 상관 히트맵(:177), AI 페이로드(:179-193)

#### 5. M1-05 Monte Carlo 엔진과 위험 수치 (run_monte_carlo: 팬, 기간 VaR·CVaR, P(loss), P(target))

- **위치:** core/quant/montecarlo.py:MCResult:71-108; core/quant/montecarlo.py:_calibrate:111-117; core/quant/montecarlo.py:run_monte_carlo:229-332 (클램프 238-239, sigma_report 257·297, 경로 302-304, 팬 306, VaR·CVaR 310-313, P(loss)·P(target) 324-325, 0 클립 327); ui/quant_lab_page.py:run:268-382 (타일 308-319); ui/qcharts.py:fan_chart:94-119; ui/qcharts.py:terminal_histogram:122-137; core/quant/insights.py:narrate_monte_carlo:138-169 (P(target) 문장 156-158)
- **목적:** 선택한 경로 모형으로 시드 고정 경로를 그려 백분위 팬(5/25/50/75/95), 만기 분포, 기간 VaR·CVaR, 손실 확률, 목표가 확률을 낸다.
- **가정:**
  - 보정 창은 load_history 기본 504세션이다(FIT_CAPTION, ui/quant_lab_page.py:46).
  - 경로 = spot·exp(누적 로그수익률). spot은 마지막 종가다(장중이면 진행 중 가격).
  - VaR·CVaR는 만기 단순 손실 1 − P_T/spot의 경험 분위와 꼬리 평균이다. 경로 중 최대 손실이 아니다. 타일 'VaR 95'는 입력한 지평 전체의 VaR다. 차트 제목과 해설에는 지평이 나온다.
  - P(target)는 만기 가격 ≥ 목표가인 경로 비율이다(montecarlo.py:325). 지평 중 도달(터치) 확률이 아니다.
  - 시드 7 기본. n_paths는 200~100,000, horizon은 5~1,260으로 자른다.
  - '세션' 1개 = 봉 1개. 연율화는 252다.
  - 모형 모수는 지평 동안 고정이다. 모수 불확실성은 없다.
- **한계:**
  - 몬테카를로 오차를 표시하지 않는다. 5,000경로·126세션에서 VaR95 시드 간 표준편차 0.27~0.44%p, CVaR 0.48~0.61%p다(VaR 약 19~22% 수준).
  - 'Vol (ann.)' 타일의 뜻이 모형마다 다르다. garch_t는 다음 세션 조건부 변동성(cond_vol_last), 나머지는 표본 σ다. 같은 계열에서 18.4% 대 21.3%였다. 그린 팬의 지평 변동성은 20.8%로 또 다르다(N-M1-03).
  - VaR·CVaR를 0 아래에서 자른다(montecarlo.py:327). 저변동·고드리프트 합성(연 σ 약 4.8%, rf 5%+ERP 10%, 252세션)에서 95% 손실 분위 −7.29%(이익)가 VaR 0.0%·CVaR 0.0%로 보인다(ARCHITECTURE_REVIEW C2).
  - 해설은 'Probability of reaching the target'이라 쓴다(insights.py:157). 실제는 만기 기준이다. 목표가가 spot 아래면 '그 위에서 끝날 확률'이 된다(N-M1-11).
  - 가상자산은 Vol ×0.831, 드리프트 1.45배, 126'세션' = 4.1개월이다(D12-11).
  - 입력 오염이 그대로 VaR로 간다. +inf면 VaR 0%, 중복 행이면 VaR 13.5%→36.0%(D12-01, D12-02).
  - 장중 마지막 봉이 spot이 된다. 화면이 말하지 않는다(DF-03).
  - 만기 VaR라 지평 중 낙폭 위험은 보이지 않는다.
- **적용 범위:** 평일 주식·ETF·지수의 수개월 위험 범위 서술에 쓴다. 가격 결정, 주문 판단, 가상자산의 연율화 값에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 25행: GBM VaR 26.33% 대 로그정규 닫힌식 26.37%, CVaR 31.67% 대 31.72%(MC 오차 안). 24행: 네 모형 모두 E[S_T] = S_0·e^{rT}. tests/quant_acceptance.py::test_mc_is_seeded_and_reproducible, ::test_mc_fan_percentiles_are_ordered, ::test_mc_var_and_cvar_are_coherent(모양 검사), ::test_mc_target_probability_brackets, ::test_mc_all_models_run; tests/macro_m9_lab.py::test_t_repro_01c_lab_outputs_reproducible_under_the_seed(T-REPRO-01c). 재현 work/m1_risk_sim/v1_mc.py 2·3번(이번에 다시 돌려 같음), work/m1v/v1_checks.py h)(0 클립).
- **관련 오류:** D12-11(P1), D12-01, D12-02, DF-03, DF-01, D12-06, ARCHITECTURE_REVIEW C2(감사 행 없음), 신규 N-M1-03, 신규 N-M1-11
- **화면:** Quant Lab 첫 타일 줄(Spot, Median terminal, 90% range, P(loss), VaR 95, CVaR, Drift (ann.), Vol (ann.), P(target): ui/quant_lab_page.py:308-319), 팬 차트·만기 히스토그램(:338-339), 해설·AI 페이로드(:340-377)

#### 6. M1-06 MC 드리프트 규칙과 볼록성 보정 (premium, rf, zero, sample)

- **위치:** core/quant/montecarlo.py:resolve_drift:189-203; core/quant/montecarlo.py:_drift_note:206-226; core/quant/montecarlo.py:run_monte_carlo:242-244,292-300; core/quant/montecarlo.py:_bootstrap_correction:177-186; core/quant/garch.py:simulate_returns:674-702; ui/quant_lab_page.py:_risk_free:80-99; ui/quant_lab_page.py:_DRIFTS:38-41; ui/quant_lab_page.py:erp:249-251
- **목적:** 팬의 중심을 정한다. 산술 수익률(rf+ERP 또는 rf)을 모형별 정확한 볼록성 보정 c_t = ln E[exp(shock_t)]로 로그 드리프트로 바꾸거나, 로그 드리프트(0 또는 표본 평균)를 그대로 더한다.
- **가정:**
  - premium: 기대 산술수익률 = rf + ERP. ERP 기본 4%는 자산 종류와 무관하게 들어간다. 입력란 도움말(equity 4 / bonds-gold 1 / FX 0)만 있다(ui/quant_lab_page.py:249-251).
  - rf: KRX 코드는 KRW 3개월(FRED 월간), 그 밖은 FRED DGS3MO다. FRED 응답이 아니면 3%를 가정하고 오류색 칩을 단다(ui/quant_lab_page.py:86-99).
  - 봉당 rate = 연 rate/252. 모형별 c_t를 단계마다 뺀다(GBM ½σ², 점프 닫힌식, 부트스트랩 블록 log-MGF, GARCH-t c(σ_t) 표).
  - sample: 표본 로그 평균×252. zero: 로그 드리프트 0.
  - 가격은 총수익(배당 재투자) 계열이라고 가정한다.
- **한계:**
  - 가상자산은 rate/252를 365봉 경로에 적용해 연 드리프트가 1.45배다(D12-11).
  - FX 기호의 rf 모드가 r_dom − r_for 대신 미국 단기금리를 쓴다(ARCHITECTURE_REVIEW A4, 미해결). 원화 가상자산(KRW-BTC)도 미국 DGS3MO를 쓴다.
  - 가격수익(split) 계열(KIS 국내·해외)에 총수익 기대치를 걸어 배당수익률 q만큼 과대하다(ARCHITECTURE_REVIEW A3의 드리프트 쪽, 미해결).
  - sample 문구가 표본 길이와 무관하게 '2년' 표준오차(σ/√2)를 쓴다(montecarlo.py:225-226).
  - drift study에서 21일 지평에 어떤 방법도 zero를 유의하게 이기지 못했다(rf_erp skill −0.007). 중심은 예측이 아니라 가정이다.
- **적용 범위:** premium·zero는 위험 서술용이다. rf는 가격결정 측도와의 비교용이며 예측이 아니다. sample은 투명성 표시용이다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 24행: z GBM +0.25, jump +0.48, bootstrap −0.26, GARCH-t +1.75(10시드 합성 +0.01). tests/quant_acceptance.py::test_rate_modes_make_the_discounted_price_a_martingale_for_every_model(40,000경로, 3 SE 안), ::test_drift_modes_are_ordered_and_documented, ::test_drift_zero_centres_the_cone_and_sample_reproduces_the_mean, ::test_mc_zero_drift_lowers_median_on_positive_drift_series, ::test_unknown_drift_raises. docs/drift_study/results.md(17종목, 3,135 원점, h=21 표).
- **관련 오류:** D12-11, ARCHITECTURE_REVIEW A3·A4(감사 행 없음)
- **화면:** Quant Lab Drift 드롭다운·ERP 입력·rf 칩, 'Drift (ann.)' 타일(ui/quant_lab_page.py:316), drift_note 문장(:321), 해설

#### 7. M1-07 GBM 경로 모형

- **위치:** core/quant/montecarlo.py:_simulate_gbm:120-123; core/quant/montecarlo.py:run_monte_carlo:278-282,297
- **목적:** 상수 μ·σ와 정규 일간 로그수익률의 기준 경로 모형이다.
- **가정:**
  - σ = 보정 창 전체의 표본 표준편차(√252 연율).
  - 일간 로그수익률이 iid 정규다.
  - 변동성 군집과 점프가 없다.
  - 보정 c = ½σ_d².
- **한계:**
  - 두꺼운 꼬리와 군집을 놓친다. 큰 충격 직후에는 팬이 좁고 조용한 해 뒤에는 넓다(primer 3.3).
  - 가상자산 σ가 ×0.831이다(D12-11).
  - 데이터 오류성 급등이 σ를 키운다(D12-02, D12-06).
- **적용 범위:** 기준선(ΔAIC 비교 대상)과 교육용이다. 꼬리 위험 판단의 단독 근거로 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 24행(z +0.25), 25행(VaR·CVaR가 로그정규 닫힌식과 MC 오차 안). tests/quant_acceptance.py::test_mc_all_models_run, ::test_rate_modes_make_the_discounted_price_a_martingale_for_every_model.
- **관련 오류:** D12-11, D12-02, D12-06, ARCHITECTURE_REVIEW C2(0 클립, M1-05 공통)
- **화면:** Quant Lab 모형 'GBM (lognormal)'

#### 8. M1-08 점프 확산 경로 모형 (3σ 분할, 문서상 'Merton')

- **위치:** core/quant/montecarlo.py:_simulate_jump:126-163 (3σ 분할 131-134, λ 138, 점프 크기 139-140, 점프 충격 145-150, λ/yr 문구 152, 보정 159-162); 문서 core/quant/montecarlo.py:10-13; ui/quant_lab_page.py:_MODEL_LABELS:35-37
- **목적:** 확산에 포아송 점프를 더해 갭 위험을 경로에 넣는다.
- **가정:**
  - 표본을 3σ(점프가 섞인 표본 σ)로 나눠 바깥 날을 점프로 본다.
  - λ = 점프일 수/표본 수(하루당).
  - 점프 크기는 N(μ_J, σ_J) 한 번 뽑은 값 × 횟수 n이다(머튼의 n개 독립 합이 아님).
  - 점프일이 1개면 σ_J = \|μ_J\|/2로 정한다.
  - 점프와 확산은 독립이고 군집이 없다.
  - 보정은 n≤15 부분합의 정확한 log-MGF다.
- **한계:**
  - 문서와 화면은 'Merton'이라 하지만 구성이 다르다. 분산 비율 코드/머튼은 λ=0.008에서 1.0036, λ=0.2에서 1.074~1.128이다(FC-10).
  - 순수 GBM 504세션 계열 40개 중 72.5%에서 3σ 밖 날이 1~3개 나왔다(평균 1.1). 그래서 GBM으로 강등되는 일이 드물고, λ와 점프 크기를 잡음 1~3개로 추정한다(N-M1-04; ARCHITECTURE_REVIEW A5 (i)(ii)와 같은 뿌리).
  - 임계값이 점프가 섞인 σ로 정해져 자기참조적이다(A5).
  - 데이터 오류성 급등도 점프로 잡는다(D12-06).
  - λ/yr 문구가 252를 쓴다(가상자산).
- **적용 범위:** 표본에 실제 사건일이 여러 개 있는 종목의 갭 위험 감을 잡는 데만 쓴다. 점프 모수 자체를 해석하거나 보고하지 않는다.
- **검증 상태:** 테스트로 확인됨. financial_calcs.md FC-10(r05_montecarlo.py 3번)과 3장 24행(z +0.48, 코드 자신의 구성과 일치; A5 (iii)은 닫힘). tests/quant_acceptance.py::test_mc_jump_degrades_to_gbm_without_outliers(note만 단언, 약한 테스트 TA-08), ::test_rate_modes_make_the_discounted_price_a_martingale_for_every_model. 재현 work/m1_risk_sim/v1_mc.py 4번(이번에 다시 돌려 72.5%, 평균 1.1, 최대 3).
- **관련 오류:** FC-10, TA-08, D12-06, D12-11, ARCHITECTURE_REVIEW A5(감사 행 없음), 신규 N-M1-04
- **화면:** Quant Lab 모형 'Jump diffusion (Merton)', jump_note 문장

#### 9. M1-09 블록 부트스트랩 경로 모형

- **위치:** core/quant/montecarlo.py:_simulate_bootstrap:166-174; core/quant/montecarlo.py:_bootstrap_correction:177-186; core/quant/montecarlo.py:run_monte_carlo:287-291; 문서 core/quant/montecarlo.py:14-16; docs/build_models_primer.py:ch3:899-904
- **목적:** 분포 가정 없이 과거 수익률 블록을 다시 뽑아 경로를 만든다.
- **가정:**
  - 원형(circular) 블록 부트스트랩, 블록 길이 5 고정이다. 정상(stationary) 부트스트랩이 아니다.
  - 표본에서 평균을 빼고 재표본한다. 드리프트는 모드가 정한다.
  - 보정 창 504세션이 미래 분포를 대표한다(정상성).
  - 보정은 블록 log-MGF 증분이다(정확).
- **한계:**
  - 표본에서 본 적 없는 크기의 움직임은 그리지 못한다.
  - 5일보다 긴 변동성 군집은 끊긴다. primer 작업 계열의 r² ACF는 lag 5 0.088, lag 20 0.047로 블록보다 오래 남는다. 지금 변동성 수준도 반영하지 않는다(ARCHITECTURE_REVIEW C1).
  - 문서(montecarlo.py:14)와 primer 3.5(build_models_primer.py:900)는 'stationary block bootstrap'이라 하지만 코드는 고정 길이 원형 블록이다(ARCHITECTURE_REVIEW C1이 2026-09에 지적, 미해결).
  - 입력 오염(중복·inf)이 그대로 재표본된다.
- **적용 범위:** 모수 모형의 꼬리를 점검하는 대조용이다. 단독 예측으로 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. financial_calcs.md 3장 24행(z −0.26)은 볼록성 보정만 독립 검증한다. 블록 재표본이 군집을 보존하는지는 검사한 적이 없다(C1이 제안한 lag-5 ACF 테스트 없음). tests/quant_acceptance.py::test_mc_all_models_run, ::test_rate_modes_make_the_discounted_price_a_martingale_for_every_model; tests/macro_m9_lab.py::test_t_repro_01c_lab_outputs_reproducible_under_the_seed.
- **관련 오류:** ARCHITECTURE_REVIEW C1(=N-M1-02, 감사 행 없음), D12-01, D12-02
- **화면:** Quant Lab 모형 'Block bootstrap (empirical)'

#### 10. M1-10 GARCH(1,1)-t 추정과 모형 비교 (fit_garch)

- **위치:** core/quant/garch.py:_loglik:199-212; core/quant/garch.py:loglik_iid_normal:215-219; core/quant/garch.py:_fit:222-264 (시작점 237-241); core/quant/garch.py:_covariance:331-347; core/quant/garch.py:_profile_eta:368-426; core/quant/garch.py:_fit_t:429-443; core/quant/garch.py:fit_garch:446-552 (k·AIC 478-481, cond_vol_last 543, ΔAIC 548); 상수 core/quant/garch.py:BOUNDS:73-79, STATIONARITY_MAX:80, LR_5PCT:85, NU_NORMAL:86, _MIN_OBS:93; core/quant/insights.py:_narrate_garch:59-125 (ΔAIC 문장 106-108); ui/quant_lab_page.py:_garch_blocks:102-162 (ΔAIC 타일 139-140)
- **목적:** 일간 로그수익률에 GARCH(1,1)-t를 최대우도로 맞춘다. 조건부 변동성 경로, 지속성·반감기, 무조건 변동성, ν, LR(t 대 정규), AIC·BIC·ΔAIC(대 GBM), Wald SE와 ν 프로파일 구간을 낸다.
- **가정:**
  - μ는 표본 평균으로 고정한다(추정 안 함). σ²_1 = 표본 분산(ddof 0).
  - 혁신은 단위분산 t다(η = 1/ν ∈ [0, 0.4], ν ≥ 2.5). η = 0이면 정규다.
  - 대칭이다. 음의 충격 효과가 같다(레버리지 없음).
  - 정상성 α+β ≤ 0.9995는 벌점으로, 0.995 초과는 플래그로 다룬다.
  - 표준화 잔차는 iid다.
  - Quant Lab 창은 최근 504세션, 연율화 252.
  - L-BFGS-B, 시작점 β 0.80/0.90/0.94와 정규 해 시드(garch.py:237-241).
- **한계:**
  - 표본 밖 성능: 504세션 이동창 1일 5% VaR가 SPY 6.6%(3,199 원점), KODEX 200 6.6%(3,082 원점) 위반했다. 카드 판정은 둘 다 REJECT(사유: PIT 1% 실패)다. BTC는 5.8%로 REVISE다.
  - 근접 적분 적합이 흔하다. 정상성 경계 적합 비율이 SPY 24%, BTC 78%다(study cards). 500세션에서 β 추정 산포가 중앙 SE의 2.2배다(B2 bulletin).
  - AIC가 μ를 세지 않아 ΔAIC가 GARCH 쪽으로 +2 치우친다(500.68 대 498.68). 해설은 ΔAIC>0이면 'GARCH is preferred'라 쓰고(insights.py:106-108) 타일도 초록이 된다(ui/quant_lab_page.py:139-140). 그래서 0~2 구간 판정이 바뀐다(FC-09).
  - 무조건 변동성에는 구간이 없다. 델타법 포괄률이 지속성 0.95 미만에서 42%였다(B2).
  - 족이 틀리면 구간도 틀린다. 비대칭 혁신에서 η 포괄률 76%다(B2).
  - 잔차 진단(z²의 ACF)과 비정형 적합 표시가 없다(ARCHITECTURE_REVIEW B6, B7).
  - 모듈 문서(garch.py:14)는 시작점 β 0.95라 쓴다. 코드는 0.94다.
  - 100세션 미만이면 예외를 낸다.
- **적용 범위:** 수백 세션 이상 일간 주식·FX 가격 계열의 변동성 군집 서술에 쓴다. 금리 수준 계열에는 쓰지 않는다(DF-01). 1일 VaR의 단독 근거(표본 밖 REJECT)와 ΔAIC 0~2의 경계 판정에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 19~21행: 같은 모수에서 arch 8.0.0과 로그우도 차 0.0, 코드 최대 8326.781342 ≥ arch 8326.777756, 예측 상대오차 3.3e-16. docs/B2_FIX_BULLETIN.md: T=500 Wald 포괄률 α 91%, β 93%, η 93%, ω 97%; T=2000 94~97%; 프로파일 η 93%. tests/quant_acceptance.py::test_garch_recovers_parameters_on_simulated_series, ::test_garch_scaled_t_shocks_have_unit_variance, ::test_garch_respects_bounds_and_flags_on_gbm_series, ::test_garch_t_beats_normal_and_gbm_on_clustered_series, ::test_lr_is_nonnegative_and_correctly_sized_under_the_null, ::test_interval_coverage_on_simulated_t_garch, ::test_intervals_reaching_a_bound_are_flagged, ::test_garch_narrative_states_persistence_and_nu. 표본 밖: docs/asset_expansion/cards/D_Q_garch_spy.json, D_Q_garch_kodex200.json(REJECT), D_C2_garch_btc.json(REVISE) (이번에 카드 값 다시 읽음). garch.py:719 자체 검사는 run_all 밖이다(TA-02).
- **관련 오류:** FC-09(=ARCHITECTURE_REVIEW B4), TA-02, ARCHITECTURE_REVIEW B6·B7(감사 행 없음), 입력 D12-01·D12-02·D12-11·DF-01
- **화면:** Quant Lab GARCH 타일 줄·가드레일 칩·스터디 칩(ui/quant_lab_page.py:102-188), 조건부 변동성 차트(ui/qcharts.py:211-235), 해설; ETF LETF 표(ui/etf_page.py:104-115); Derivatives 해설(ui/derivatives_page.py:128-131,170-174); Crypto 365 환산 타일(ui/crypto_page.py:71-76,169)

#### 11. M1-11 GARCH-t 분산 예측과 유계 t 경로 시뮬레이션 (forecast_variance, horizon_vol, simulate_returns)

- **위치:** core/quant/garch.py:Z_BOUND:71; core/quant/garch.py:forecast_variance:558-571; core/quant/garch.py:horizon_vol:574-576; core/quant/garch.py:_draw_z:594-612; core/quant/garch.py:_correction_table:622-639; core/quant/garch.py:bounded_t_stats:642-651; core/quant/garch.py:martingale_correction:654-671; core/quant/garch.py:simulate_returns:674-702; core/quant/montecarlo.py:run_monte_carlo:252-276
- **목적:** 적합한 GARCH-t로 h세션 분산을 예측하고, \|z\| ≤ 22로 자른 t 혁신으로 경로를 그린다. Quant Lab 기본 팬, ETF LETF 드래그, 파생상품 밀도 차트, lab 팬 PIT에 쓴다.
- **가정:**
  - 모수는 지평 동안 고정이다.
  - σ²_{T+1}에서 출발해 ω + (α·v + β)σ²로 재귀한다(v = 절단 혁신 분산).
  - t 혁신을 ±22에서 자르고 잘린 t에서 다시 뽑는다(재척도 없음). ν > 100이면 정규로 뽑는다.
  - rate 모드에서는 경로마다 c(σ_t)를 표에서 빼 마팅게일을 맞춘다.
  - 필터는 ε = r − 표본 평균으로 하고, 시뮬레이션은 드리프트 모드의 값을 더한다.
  - 연율화 252.
- **한계:**
  - ν < 4에서 절단이 보인다. ν = 2.5면 단위분산의 79.5%만 남고, 더 큰 날은 약 47년에 한 번이다(코드 재계산 46.9년; ARCHITECTURE_REVIEW 1.3은 48년). CVaR95가 비절단보다 2.8~7.8 SE 낮다(ARCHITECTURE_REVIEW 1.3).
  - 팬 PIT(lab SMOKE, 비중첩 원점): SPY h21 χ² p 0.000(n 128) FAIL, KODEX 200 h21 p 0.736(n 83) PASS. h126은 n 13~21이다. 단 채점은 확장창 적합이고 화면 팬은 504세션 창이다(M1-20).
  - LETF 드래그 예측: 52분기 MAE 136bp, 직전 분기 실현분산 91bp, 0 예측 203bp. 기울기 0.25, R² 0.03(M_E4_letf_drag REVISE).
  - 대칭 모형이라 왼쪽 꼬리를 과소 포괄한다(asset_expansion 스터디).
  - 필터 평균과 시뮬레이션 드리프트가 다르다(ARCHITECTURE_REVIEW A6, 미해결).
  - 모수 불확실성을 팬에 넣지 않는다.
  - 가상자산에 rate/252를 쓴다(D12-11).
- **적용 범위:** 주식·지수의 1~6개월 위험 범위 서술에 쓴다. LETF 드래그는 참고치다(화면도 실현분산을 먼저 보인다). 가격결정이나 표본 밖이 보증된 팬으로 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 21행(arch 재귀와 상대 3.3e-16), 24행(GARCH-t 10시드 합성 z +0.01). docs/bounded_innovation_sweep.md(Z_BOUND 띠 14~30, 22 선택). tests/quant_acceptance.py::test_garch_forecast_variance_converges_to_unconditional, ::test_bounded_t_draws_respect_the_bound_and_keep_the_shape, ::test_martingale_correction_matches_quadrature_and_the_normal_closed_form(1e-7), ::test_horizon_vol_describes_the_bounded_paths(3% 안), ::test_mc_default_model_is_garch_t_seeded_and_reproducible; tests/macro_m9_lab.py::test_i11_fan_pit_grades_the_lab_garch_t_fan. docs/quant_lab/SPY.json, KODEX200.json(SMOKE). docs/asset_expansion/cards/M_E4_letf_drag.json. 이번 재계산 work/m1v/v1_checks.py a)(bounded_t_stats(2.5, 22): 분산 0.7950, 46.9년).
- **관련 오류:** D12-11, TA-02, ARCHITECTURE_REVIEW A6(감사 행 없음)
- **화면:** Quant Lab 기본 팬·만기 히스토그램·'Horizon vol (ann.)' 타일·bound_note(ui/quant_lab_page.py:133,338-339); Derivatives 밀도 차트(ui/derivatives_page.py:257-262, 드리프트 0); ETF LETF 21/63/252세션 드래그(ui/etf_page.py:107-110)

#### 12. M1-12 GJR-GARCH(1,1) t / Hansen skew-t (fit_gjr)

- **위치:** core/quant/gjr.py:_skewt_consts:44-48; core/quant/gjr.py:skewt_logpdf:51-55; core/quant/gjr.py:skewt_cdf:58-64; core/quant/gjr.py:skewt_ppf:67-73; core/quant/gjr.py:_loglik:113-127 (정상성 벌점 115); core/quant/gjr.py:fit_gjr:130-183 (지속성 176); core/quant/gjr.py:next_variance:186-188; 소비 core/quant/vol_estimators.py:_gjr_fitter:219-220; core/crypto/analytics.py:garch_scorecard:225-290
- **목적:** 레버리지 항 γ를 더한 GJR-GARCH(1,1)을 t·정규·Hansen skew-t 혁신으로 맞춘다. 채점 전용이다(시뮬레이터에 연결되지 않음).
- **가정:**
  - σ²_t = ω + (α + γ·1{ε<0})ε² + βσ².
  - μ는 표본 평균 고정, σ²_1 = 표본 분산.
  - 지속성 = α + β + γ/2(대칭 혁신 가정). 정상성 벌점도 같은 식이다.
  - skew-t는 ν ≤ 50, λ ∈ [−0.9, 0.9].
  - γ = 0 고정 적합 대비 LR, 경계 혼합 5% 점 2.706.
- **한계:**
  - skew-t에서도 γ/2를 써 지속성을 과소 계산한다. ν=6, λ=−0.3이면 E[z²·1{z<0}] = 0.6048이고, γ=0.15면 0.0157 과소다. 정상성 벌점도 같은 식이라 실제 지속성이 1을 넘는 skew-t 적합을 막지 못할 수 있다(FC-08).
  - SE와 프로파일 구간이 없다.
  - 표본 밖: GJR-t SPY REVISE, KODEX 200 REJECT(5% VaR 6.8%). GJR skew-t SPY는 5.2%로 Kupiec 통과, PIT 실패로 REVISE.
  - 모수 회복 검사는 gjr.py:206 자체 검사뿐이고 run_all 밖이다(TA-02).
- **적용 범위:** lab EVT 다리의 σ(t 혁신), 스터디와 Crypto scorecard 채점에 쓴다. 팬 생성이나 화면 VaR의 단독 근거로 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 22행(arch o=1과 로그우도 차 0.0, 코드 최대 ≥ arch 해), 23행(Hansen skew-t 밀도 ≤1.8e-15). 자체 검사 core/quant/gjr.py:206-235(docs/audit/2026-10-27/artifacts/unwired_selfchecks.csv). tests/macro_m9_lab.py::test_i11_fit_clause_expanding_windows(I-11), tests/macro_m3_estimators.py::test_t_est_04_fallback_to_sma20_no_blend. 카드 D_Q_gjr_spy, D_Q_gjr_kodex200, D_Q_skewt_spy, D_Q_skewt_kodex200, D_C2_gjr_btc, D_C2_skewt_btc(이번에 다시 읽음). 이번 재계산 work/m1v/v1_checks.py b)(0.6048, 과소 0.0157).
- **관련 오류:** financial_calcs/FC-08(수정 묶음 PT-21), TA-02
- **화면:** Quant Lab 스터디 칩(skew-t 판정, ui/quant_lab_page.py:182-187), Crypto scorecard 카드, lab 등급의 GJR-EVT 다리

#### 13. M1-13 lab 변동성 입력 (SMA20, 확장창 GJR-t 예측)

- **위치:** core/quant/vol_estimators.py:sma:111-127; core/quant/vol_estimators.py:fit_ok:152-168; core/quant/vol_estimators.py:_multi_step:179-183; core/quant/vol_estimators.py:_fitted:186-212 (최소 관측 190, 193); core/quant/vol_estimators.py:gjr_t:229-232; core/quant/lab.py:has_min_history:225-232; core/quant/lab.py:lab_fit:238-261; core/quant/lab.py:sma20_sigma:264-267; core/quant/lab.py:gjr_sigma:270-273
- **목적:** lab 꼬리선의 1일 σ 예측을 만든다. fast FHS는 SMA20, GJR-EVT는 확장창 GJR-t를 쓴다.
- **가정:**
  - SMA20 = 최근 20개 단순수익률의 표본분산(ddof 1). lab은 이 σ로 로그수익률을 표준화한다(lab.py:675-679).
  - gjr_sigma(gjr_t)의 최소 이력은 관측 수만 본다. max(round(10×252), 100) = 2,520관측이다(vol_estimators.py:190,193). 달력 10년 검사(has_min_history)는 lab_fit과 fan_origins에만 있다.
  - 21원점마다 확장창 r[:t+1]로 재적합하고 사이에는 모수를 고정해 일간 재귀한다. 재적합 실패 시 옛 모수를 쓰지 않는다.
  - fit_ok: 수렴, ω>0, α≥0, β≥0, α+β+γ/2 ≤ 0.9999, ν ∈ (2, 100]. 아니면 NaN이고 대체하지 않는다.
  - 다단계 예측은 p = α+β+γ/2 기하 감쇠다(lab은 h=1만 쓴다).
- **한계:**
  - KODEX 200 SMOKE 캐시에서 GJR 다리의 첫 유효 원점은 2019-06-27이다. 2016-26 원점 2,599개 중 846개가 insufficient_history다(이번 재실행 확인). EVT 선은 그 뒤 잔차 약 500개(k ≥ 50)를 더 기다려 1,248개에서만 채점된다.
  - 같은 캐시는 2007년 8행 뒤 800일 간격(2007-02-07→2009-04-17)을 수익률 1개(−8.04%)로 넣는다. 이 값은 모든 확장창 GJR·GARCH 적합에 하루짜리 충격으로 남는다(D12-07 사례). 2,520관측은 2019-06-27에 차서 달력 10년(2017-01)보다 늦다.
  - 모듈 문서(vol_estimators.py:16-17, lab.py:15)는 '10년 이상' 확장창이라 쓴다. 코드는 관측 2,520개다. 365봉 계열이면 6.9년이다(N-M1-06).
  - 실질 정규 적합(ν > 100)은 거부되어 그 원점의 EVT 다리가 빈다.
  - SMA20은 국면 전환에 약 20세션 늦다.
  - 독립 감사 범위 밖이었다(financial_calcs.md 1장·6장 제외 목록).
- **적용 범위:** lab 채점과 매크로 M3 하네스 입력이다. 화면 VaR를 직접 만들지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m3_estimators.py::test_sma20_and_ewma_definitions, ::test_causality_no_lookahead, ::test_t_est_04_fallback_to_sma20_no_blend; tests/macro_m4_integration.py::test_estimator_harness_sma20_is_risk_layer_sma_vol(비트 동일); tests/macro_m9_lab.py::test_i11_fit_clause_expanding_windows(I-11, 접두 성질). 재현 work/m1_risk_sim/v3_gjr_ok.py(이번 재실행: gjr ok 1,753, 첫 원점 2019-06-27, insufficient_history 846), v4_rows_per_year.py, v5_gap.py; work/m1v/v1_checks.py k)(2,520관측과 달력 조건이 KODEX에서 같은 날 2019-06-27).
- **관련 오류:** D12-07, 신규 N-M1-05, 신규 N-M1-06
- **화면:** Quant Lab 저장 등급(docs/quant_lab/*.json) 경유만

#### 14. M1-14 FHS 1일 VaR·ES (fast FHS)

- **위치:** core/quant/lab.py:fhs_tail:279-299; core/quant/forecast_eval.py:_Pool:254-282 (quantile, tail_mean)
- **목적:** 표준화 잔차의 확장 풀에서 분위를 뽑아 1일 95/97.5/99% VaR와 97.5% ES를 낸다.
- **가정:**
  - z_s = r_s/σ_{s−1}가 iid다. r은 로그수익률, σ는 SMA20(단순수익률)이다.
  - 풀은 확장형(감쇠 없음)이고 잔차 252개 이후 시작한다. σ가 없는 초기 수익률은 풀에 들어가지 않는다.
  - VaR_a = −σ·q_{1−a}(풀), 선형 보간(pos = q(n−1)). ES = −σ·mean(z \| z ≤ q).
  - 1일 지평, 로그수익률.
- **한계:**
  - 오래된 잔차와 최근 잔차를 같은 무게로 쓴다.
  - SMOKE KODEX 200 fast FHS(2016-26, n 2,599): 95% 위반 4.46%(Kupiec p 0.201), 99% 1.31%. SPY는 fast FHS가 B5 FAIL이라 1일 VaR 표시가 보류됐다.
  - 연휴 뒤 다세션 수익률 배율은 gap_sessions가 있어야 한다. 캘린더 미서명으로 적용되지 않는다.
  - 결측 세션을 하루로 본다(D12-07).
- **적용 범위:** 1일 위험선 채점에 쓴다. 다일 지평에는 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_tails_envelope_lines_and_periods, ::test_i11_gate_mechanics_true_dgp_passes_misspecified_fails(참 σ PASS, σ×0.6이면 99% Kupiec·CC·Z2 FAIL) (I-11). docs/quant_lab/KODEX200.json components_lines(이번에 다시 읽음). 독립 감사 범위 밖.
- **관련 오류:** D12-07, CAL-01(d865c7f 반영, 서명 대기; gap_sessions 의존)
- **화면:** Quant Lab 저장 등급 문장(구성요소 줄)

#### 15. M1-15 GJR-EVT 꼬리 (McNeil–Frey, GPD)

- **위치:** core/quant/lab.py:gpd_tail:302-327; core/quant/lab.py:gpd_quantile:330-335; core/quant/lab.py:gpd_es:338-340; core/quant/lab.py:evt_tail:343-375
- **목적:** GJR-t σ로 표준화한 잔차의 아래 10% 꼬리에 GPD를 맞춰 VaR·ES를 낸다(McNeil–Frey 2단계).
- **가정:**
  - 손실 x = −z, k = floor(0.10n), u = (k+1)번째로 큰 손실.
  - GPD(ξ, β)를 loc 0으로 최대우도 적합한다.
  - 21원점마다 재적합한다. μ = 0.
  - ξ ≥ 1, k < 50, 양의 초과 < 50, β ≤ 0, 비유한이면 실패로 닫는다.
- **한계:**
  - k ≥ 50이려면 잔차가 500개 이상 필요하다. KODEX 200 SMOKE에서 EVT 선의 첫 채점 실현일은 2021-07-14다.
  - ξ 추정 오차가 99% 분위로 크게 전파된다. 구간은 없다.
  - GJR σ가 빈 원점에서는 선이 없다(M1-13).
  - SMOKE KODEX 200: n 1,248, 95% 위반 4.89%(Kupiec p 0.855), 99% 1.20%.
- **적용 범위:** lab envelope의 한 다리다. 단독 화면 숫자가 아니다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_tails_envelope_lines_and_periods(ξ=1.2 주입 시 evt_fit_failed, k=39면 실패, 분위 순서), ::test_i11_grade_lab_end_to_end_synthetic (I-11). 이번 독립 대조 work/m1v/v3_gpd.py: gpd_quantile 대 scipy genpareto.ppf 최대 차 3.5e-10, gpd_es 대 수치적분 꼬리 평균 최대 차 8.6e-10(ξ −0.2~0.6). 실데이터 기준값 대조는 없다.
- **관련 오류:** D12-07(입력 간격)
- **화면:** Quant Lab 저장 등급 경유만

#### 16. M1-16 꼬리 envelope와 1일 VaR 표시 규칙 (envelope, display_scale, B5)

- **위치:** core/quant/lab.py:envelope:378-386; core/quant/lab.py:display_scale:389-392; core/quant/lab.py:grade_lab:667-744 (B5 704-705, 1일 VaR 706-712); core/quant/forecast_eval.py:fhs_eval:285-330; core/quant/forecast_eval.py:b5:354-398; core/quant/validate.py:pit_tests:676; ui/quant_lab_page.py:_lab_grade:191-200; ui/quant_lab_page.py:_grade_blocks:203-236
- **목적:** fast FHS와 GJR-EVT의 원소별 최댓값을 채점선으로 쓴다. 두 다리가 모두 1일 B5를 통과할 때만 최신 1일 VaR 숫자를 보인다.
- **가정:**
  - envelope = max(두 선), ok = 두 다리 모두 ok.
  - EVT 다리가 없으면 envelope를 보류하고 FHS만 채점하며 게이트는 NOT_RUN이다.
  - B5: 5% 위반률이 0.05 ± 2√(0.05·0.95/n) 안이고 PIT χ² p ≥ 0.01, 200원점 이상.
  - EVT 다리의 B5는 GJR σ에 FHS 경험 풀을 붙인 형태로 본다(lab.py:705). GPD 꼬리 자체는 B5에 들어가지 않는다.
  - 표시 배율은 √max(n_US, 1)이다.
- **한계:**
  - 최댓값이라 95%에서 보수적이다. KODEX 200 95% 위반 3.61%(Kupiec p 0.018), SPY 3.93%(p 0.008). 95%선은 게이트에 없다.
  - B5는 5% 수준만 본다. 표시되는 99% VaR와 ES 97.5는 B5 대상이 아니다. EVT 다리는 GPD 선이 아닌 GJR σ+FHS로 B5를 통과한다.
  - gap_sessions가 없어 배율이 늘 ×1.000이고 연휴 뒤 버킷은 '실행 안 됨'이다(캘린더 서명 대기).
  - 저장 등급은 정적이다(KODEX200 2026-09-22, SPY 2026-09-24까지). 화면 실행의 출처·기간과 무관하게 기호 이름으로 붙는다(합성 실행에도 붙는다).
  - B5 실데이터 골든은 NOT_RUN이다(test_t_b5_01_kospi_golden_refdata, test_g_b5_02_spy_refdata_with_smoke_on_local_cache).
- **적용 범위:** Quant Lab의 서술용 1일 위험선이다. acts=False이고 사이징 모듈은 lab을 읽지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_grade_lab_end_to_end_synthetic(보류 시 NOT_RUN, var_1d 표시 규칙), ::test_i11_no_sizing_module_reads_lab (I-11); tests/macro_m3_estimators.py::test_t_b5_01_synthetic_clauses_and_bands(T-B5-01, G-B5-01, G-B5-02). SMOKE(docs/quant_lab/*.json 다시 읽음): KODEX 200 1일 VaR 95% 4.98%, 99% 8.27%(B5 둘 다 PASS); SPY는 보류(fast_fhs B5 FAIL). NOT_RUN 2건은 qa/acceptance_results.json에서 확인.
- **관련 오류:** CAL-01, M-2(d865c7f 반영, 서명 대기), TA-12
- **화면:** Quant Lab 등급 문장 '1-day VaR (envelope)'(ui/quant_lab_page.py:203-236, 저장 JSON의 lines)

#### 17. M1-17 Kupiec·Christoffersen VaR 백테스트

- **위치:** core/quant/validate.py:kupiec:628-638 (x=0·x=n 분기 633-635); core/quant/validate.py:christoffersen:641-658; core/quant/lab.py:grade_var:398-411; core/quant/forecast_eval.py:fhs_eval:323-330
- **목적:** VaR 위반 수가 명목 수준과 맞는지(Kupiec POF), 위반이 몰리는지(Christoffersen 독립·조건부 포괄)를 검정한다.
- **가정:**
  - 귀무에서 위반은 독립 베르누이다.
  - LR ~ χ²(1), CC ~ χ²(2) 점근 분포.
  - x = 0 또는 x = n이면 우도비 대신 점수 검정 z²를 쓴다. CC도 이 값을 lr_uc로 받는다.
  - 1차 마르코프 의존만 본다. 10개 미만이면 CC는 NaN이다.
  - NaN 예측은 버린다.
- **한계:**
  - x = 0에서 점수 검정 p가 정확한 LR p와 다르다. α=0.01이면 n 192~380에서 코드는 p ≥ 0.05(통과), LR은 p < 0.05(기각)다. n=200: 0.155 대 0.045, n=250: 0.112 대 0.025. α=0.05면 n 38~72다(N-M1-01). M9 게이트 최소 n이 200이라 범위 안이다. financial_calcs.md 6장은 '게이트 최소 표본 500/1000'을 전제로 결론이 같다고 했지만 M9 최소는 200이다. 지금 저장 등급(n 1,248/2,697)에는 영향이 없다.
  - 작은 n에서 점근 근사가 거칠다.
  - 2차 이상 의존은 보지 못한다.
- **적용 범위:** 200원점 이상 VaR선의 채점에 쓴다. 위반 0건이고 n < 400이면 정확한 LR로 다시 본다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_gate_mechanics_true_dgp_passes_misspecified_fails(I-11); tests/macro_m3_estimators.py::test_t_b5_01_synthetic_clauses_and_bands(F.kupiec is V.kupiec); tests/expansion_acceptance.py:284(균등 위반 p > 0.05). 이번 독립 재구현 work/m1v/v1_checks.py c): x>0인 무작위 위반열 300개에서 Kupiec LR·독립 LR·CC LR이 코드와 최대 2.3e-13 차이. x=0 분기는 work/m1_risk_sim/v2_kupiec.py 재실행으로 확인(192~380, 38~72). NOT_RUN: tests/macro_m3_estimators.py::test_t_est_02_christoffersen_lines_refdata.
- **관련 오류:** 신규 N-M1-01
- **화면:** Quant Lab 칩 'Kupiec 99% VaR', 'Christoffersen CC 99%'; 스터디 칩과 카드 문장(D_Q_*)

#### 18. M1-18 ES Z2 검정 (Acerbi–Székely, 모의 임계값)

- **위치:** core/quant/lab.py:es_z2:414-457; core/quant/lab.py:grade_lab:683-687 (z_pool·scale·gpd 선택); core/quant/forecast_eval.py:es_z2:407-439 (M3 판, 별도 구현)
- **목적:** 97.5% ES가 손실을 과소평가하는지 Z2로 검정한다. 임계값은 모의로 구한다.
- **가정:**
  - Z2 = Σ x_t·I_t/(n·α·ES_t) + 1, I_t = 1{x_t < −VaR_t}. 음수면 위험 과소다.
  - 귀무 법칙: x*_t = 모형 σ_t × 잔차 풀 iid 추출. EVT 선은 u 너머를 GPD로 다시 뽑는다.
  - 잔차 풀은 표본 전체(마지막 원점까지)의 r/σ이고 GPD는 마지막 적합 하나다. 원점 시점의 법칙이 아니다(브리프 F-11·F-31이 정한 방식).
  - B = 2,000(p 해상도 0.0005), 시드 11.
  - n ≥ 20.
- **한계:**
  - 임계값이 모형 자신의 잔차 풀에서 나온다. 풀 자체가 틀리면 검정력이 약하다.
  - 귀무 법칙이 앞날의 잔차와 마지막 GPD를 쓴다. 꼬리가 나중에 두꺼워진 표본이면 모의 Z2도 함께 낮아져 기각이 덜 된다.
  - envelope의 귀무 법칙은 GJR-EVT 다리(σ_gjr, GPD)다. fast FHS 다리는 법칙에 없다.
  - SMOKE KODEX 200: 2016-26 Z2 +0.242 p 0.571, 2026 기간 Z2 −0.556 p 0.030(기각, 보고만).
- **적용 범위:** lab 97.5% ES 채점에 쓴다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_gate_mechanics_true_dgp_passes_misspecified_fails(참 법칙 p ≥ 0.05, σ×0.6 기각), ::test_t_repro_01c_lab_outputs_reproducible_under_the_seed(T-REPRO-01c). docs/quant_lab/KODEX200.json(다시 읽음). 독립 감사 범위 밖.
- **관련 오류:** -
- **화면:** Quant Lab 칩 'ES 97.5% Z2'

#### 19. M1-19 Basel 신호등 (traffic_light, basel_zone)

- **위치:** core/quant/validate.py:traffic_light:661-663; core/quant/lab.py:basel_zone:460-466; core/quant/lab.py:basel_windows:469-477
- **목적:** 최근 250원점의 99% VaR 위반 수로 녹·황·적 구역을 정한다.
- **가정:**
  - 녹 ≤ 4, 황 ≤ 9, 적 ≥ 10(250원점 기준).
  - n ≠ 250이면 문턱을 n/250로 비례한다(규정이 아닌 해석).
  - 비중첩 250원점 창의 구역 수를 센다.
- **한계:**
  - 비례 문턱은 바젤 규정이 아니다.
  - 250원점 미만이면 'last 250'이 None이다(2026 기간). 화면은 'NOT RUN'으로 보인다.
  - 위반 수만 보고 크기는 보지 않는다.
- **적용 범위:** 99% 1일 VaR선의 보조 지표다. 게이트에 들어가지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_gate_mechanics_true_dgp_passes_misspecified_fails(basel_zone 4/5/10, n=125 비례) (I-11). SMOKE: KODEX 200 창 녹 4, SPY 녹 9·황 1(이번에 다시 읽음).
- **관련 오류:** -
- **화면:** Quant Lab 칩 'Basel last 250'; 스터디 카드 traffic 값

#### 20. M1-20 팬 PIT 검정 (garch_fan_quantiles, fan_pit)

- **위치:** core/quant/lab.py:fan_origins:480-489; core/quant/lab.py:garch_fan_quantiles:492-518; core/quant/lab.py:fan_pit:521-546
- **목적:** Quant Lab 기본 팬(GARCH-t, premium 드리프트)이 h세션 뒤 실현 로그수익률을 잘 덮는지 10분위 χ²로 검정한다.
- **가정:**
  - 원점은 h세션마다 비중첩, 2016년 이후, 뒤에 달력 10년·관측 2,520개 이상(has_min_history).
  - 원점마다 r[:t+1] 확장창으로 GARCH-t를 적합한다(화면 팬은 최근 504세션).
  - 드리프트 premium rf 3% + ERP 4% 고정, 2,000경로, 시드 11.
  - MC 십분위를 정확한 값으로 본다.
  - χ² 10칸, 원점 20개 이상.
- **한계:**
  - 채점하는 적합 창(확장)이 화면 팬의 창(504세션)과 다르다. 등급이 화면 팬을 직접 보증하지 않는다.
  - 원점이 적어 검정력이 낮다(h21 n 83~128, h126 n 13~21). KODEX 200 원점은 2019-06-27부터다.
  - SMOKE SPY h21 p 0.000 FAIL, KODEX 200 p 0.736 PASS.
  - rf·ERP가 고정이라 실제 rf 변화를 반영하지 않는다.
  - 가상자산 연율화 252(지금 채점 대상은 없음).
- **적용 범위:** 주식·지수 팬의 보정 점검에 쓴다. h126은 보고만 한다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_fan_pit_grades_the_lab_garch_t_fan(십분위가 run_monte_carlo와 1e-12 안, 확장창 접두 성질; I-11, T-REPRO-01c), ::test_i11_gate_mechanics_true_dgp_passes_misspecified_fails. docs/quant_lab/SPY.json, KODEX200.json. work/m1v/v1_checks.py k)(KODEX h21 원점 83개, 첫 원점 2019-06-27).
- **관련 오류:** D12-11
- **화면:** Quant Lab 칩 'Fan PIT h21'

#### 21. M1-21 M9 게이트 (m9_gate, grade_lab)

- **위치:** core/quant/lab.py:GATE:67-68; core/quant/lab.py:LAB_CONFIG:70-81; core/quant/lab.py:grade_line:558-614; core/quant/lab.py:m9_gate:617-644; core/quant/lab.py:grade_lab:667-744; core/quant/lab.py:grade_to_json:747-750; docs/quant_lab_grading.py:run_smoke:80, run_formal:97; ui/quant_lab_page.py:_lab_grade:191-200; ui/quant_lab_page.py:_grade_blocks:203-236; core/quant/lab.py:GIT_HASH:49; ui/quant_lab_page.py:_GRADE_FILE:49; docs/quant_lab/manifest.json
- **목적:** 2016-26 기간에서 99% VaR Kupiec p ≥ 0.05, CC p ≥ 0.05, ES Z2 p ≥ 0.05, 팬 PIT h21 p ≥ 0.01을 모두 만족하면 PASS로 판정한다. 결과는 서술용이다(acts=False).
- **가정:**
  - 문턱은 '기본값, 판단'이다(lab.py:68). 규칙 저장소에 없다(lab.py:70).
  - n < 200, 팬 원점 < 20, 결측이면 NOT_RUN이다.
  - 2026 기간과 h126은 보고만 한다.
  - envelope가 보류되면 NOT_RUN이다.
- **한계:**
  - 정식 실행(I-11, KOSPI 픽스처와 서명된 KR/US 캘린더)이 NOT_RUN이다. 저장된 등급(docs/quant_lab/KODEX200.json, SPY.json)은 manifest 라벨이 'SMOKE: VENDOR DATA — Yahoo auto-adjusted closes ..., last row dropped; not an official close, not the I-11 KOSPI fixture, not a card run; gates nothing'인 실행이다: KODEX 200 PASS, SPY FAIL(팬 PIT).
  - '2016-26'이라는 이름과 달리 KODEX 200 SMOKE의 VaR·ES 채점 표본은 2021-07-14 이후 1,248개이고 팬 원점은 2019-06-27 이후 83개다(N-M1-05).
  - 네 검정을 각각 따로 본다. 다중검정 보정이 없다.
  - 95% VaR선은 게이트 밖이다(두 SMOKE 계열 모두 95%에서 과보수).
  - Kupiec·CC의 x=0 분기는 n 192~380에서 관대하다(M1-17, N-M1-01).
  - 화면은 기호 이름만으로 저장 등급을 붙인다(SPY, 069500, 069500.KS, ^KS11; ui/quant_lab_page.py:49, :191-200). 저장 파일이 있는 종목만 등급 줄이 보이고, 화면 실행의 출처·기간과 무관하게 붙는다.
  - 실데이터 테스트 두 건(::test_i11_kospi_oos_2016_26_thresholds_refdata, ::test_i11_replay_kospi_path_refdata)은 픽스처가 와도 서명 달력, 서명된 kr_regime_tags, 북 상태가 없으면 NotRun을 낸다(tests/macro_m9_lab.py:341-345, :399-403; TA-01).
  - GIT_HASH가 상수 'UNVERSIONED'다(lab.py:49). manifest의 git_hash도 UNVERSIONED라 저장 등급이 어느 코드에서 나왔는지 기록되지 않는다(functional_completeness/FC-07, 감사 12.11).
- **적용 범위:** Quant Lab 모형의 서술용 등급이다. 노출·사이징·재조정에 쓰지 않는다(사이징 모듈 import 금지 테스트가 있다). 매크로 영역에 Quant Lab 등급(R-16)으로 따로 적었던 항목은 M1-14~M1-22에 나눠 합쳤다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_gate_mechanics_true_dgp_passes_misspecified_fails(문턱 가장자리 0.0499/0.05, n 199/200), ::test_i11_grade_lab_end_to_end_synthetic, ::test_i11_no_sizing_module_reads_lab, ::test_smoke_grading_on_local_closes_runs_offline_and_is_labelled_vendor_data (I-11). NOT_RUN: ::test_i11_kospi_oos_2016_26_thresholds_refdata(qa/acceptance_results.json 확인). docs/quant_lab/manifest.json(run smoke, seed 11, git_hash UNVERSIONED). work/m1v/v1_checks.py k)(2021-07-14). NOT_RUN: ::test_i11_replay_kospi_path_refdata(M1-22와 같음).
- **관련 오류:** CAL-01, M-2(d865c7f 반영, 서명 대기), TA-01(P2), TA-12, functional_completeness/FC-07(P3), 신규 N-M1-05, 신규 N-M1-01
- **화면:** Quant Lab 'M9 gate' 칩, SMOKE 칩, 네 통계 칩, 등급 문장(ui/quant_lab_page.py:203-236)

#### 22. M1-22 역사 구간 재현과 LETF 경로 항등식 (replay, letf_path_return)

- **위치:** core/quant/lab.py:REPLAYS:756-764; core/quant/lab.py:letf_path_return:767-770; core/quant/lab.py:replay:773-831 (장부 경로 796-814); core/quant/scenarios.py:_letf_daily:186-192 (letf_path_return 사용); core/quant/scenarios.py:_shock_window:204-255 (replay를 부르지 않는 별도 계산, 장부 경로 243-247)
- **목적:** 지정한 위기 구간 8개를 지수 종가와 현재 장부 비중으로 다시 걷는다. 레버리지 ETF 경로 수익을 항등식으로 만든다.
- **가정:**
  - 단순수익률이다. 장부 일간 수익 = Σ w_i·r_i이고 이를 복리한다. 즉 매일 같은 비중으로 되맞춘다(상수 혼합). 매수 후 보유가 아니다.
  - 종가가 없는 상품은 0 수익으로 두고 unmapped에 적는다(그 비중은 매일 현금처럼 남는다).
  - ln(1+R_L) = L·ln(1+R) − ½(L²−L)Σr² − carry. carry는 입력이다.
  - 창 날짜는 수익률 날짜이고 양끝 포함이다.
- **한계:**
  - 화면이 없다. 테스트만 lab.replay와 scenarios를 부른다.
  - 'static weights'·'held'라는 표현과 달리 상수 혼합이다. 10일 +5%/−5% 두 자산 50/50에서 상수 혼합 0.00% 대 매수 후 보유 +11.38%다. 27일 −38.6% 경로·60% 장부면 약 −25.3% 대 −23.2%다(N-M1-07; 테스트가 이 방식을 고정한다).
  - LETF 식은 2차 근사다. 추적오차와 일중 경로를 무시한다.
  - 실데이터 재현(KOSPI 경로)은 NOT_RUN이다.
- **적용 범위:** 시나리오 서술용이다. 손실 확률이나 사이징에 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_lab.py::test_i11_replay_synthetic_companion(I-11; 27수익률 −38.6%, book_return = prod(1+0.6r)−1 단언), tests/macro_m9_scenarios.py::test_letf_identity_on_a_synthetic_path, ::test_shock_window_on_the_current_book_synthetic_companion, ::test_t_repro_01c_scenarios_identical_paths_under_the_seed. NOT_RUN: tests/macro_m9_lab.py::test_i11_replay_kospi_path_refdata, tests/macro_m9_scenarios.py::test_scenario_kospi_jul_2026_path_refdata. 재현 work/m1v/v1_checks.py d).
- **관련 오류:** 신규 N-M1-07
- **화면:** - (화면 없음)

#### 23. M1-23 포트폴리오 최적화 (optimize_portfolio, efficient_frontier, 위험 기여)

- **위치:** core/quant/optimize.py:OBJECTIVES:22; core/quant/optimize.py:_risk_contributions:47-52; core/quant/optimize.py:_solve:55-65; core/quant/optimize.py:optimize_portfolio:68-100; core/quant/optimize.py:efficient_frontier:103-131; ui/portfolio_page.py:run:95-117 (상한은 선택 목적에만 114), 146-177; core/quant/insights.py:narrate_portfolio:238-258
- **목적:** M1-04의 μ·Σ로 롱온리 완전투자 비중을 네 목적(max_sharpe, min_vol, risk_parity, equal_weight)으로 구한다. 효율적 프런티어와 무작위 포트폴리오 1,500개를 그린다.
- **가정:**
  - 입력 μ는 로그수익률 평균×252, Σ는 공분산×252다(M1-04).
  - 롱온리, Σw = 1, 종목당 상한 max_weight(화면 입력, 기본 1.0).
  - SLSQP, 동일 비중에서 시작, maxiter 500, ftol 1e-10. 결과를 잘라 다시 정규화한다. 수렴 실패는 칩으로 알린다.
  - risk parity는 위험 기여 비율과 1/n의 제곱 편차 합을 최소화한다.
  - 프런티어는 min-vol 수익에서 최대 단일 μ까지 25점, 상한 (0, 1)이다. 실패한 점은 조용히 뺀다. 구름은 Dirichlet(1) 1,500개, 시드 11이다.
  - rf는 화면 입력(기본 3%)이다. FRED를 읽지 않는다.
- **한계:**
  - 기대수익률이 로그 평균이라 max_sharpe 비중과 프런티어 수익 축이 치우친다(M-02, M1-04).
  - 초과수익이 모두 음수면 max_sharpe가 가장 변동성이 큰 종목에 몰린다. μ (−2%, −5%, 0%), σ (10%, 40%, 20%), rf 3%에서 비중 (0, 1, 0), Sharpe −0.20이다. min_vol은 Sharpe −0.50이다. 경고가 없다(N-M1-09).
  - 상한은 고른 목적에만 걸린다(ui/portfolio_page.py:113-115). 비교표의 나머지 행과 프런티어(bounds (0, 1), optimize.py:117)는 상한 없이 계산된다. 표시가 없다. 상한 0.3이면 max_sharpe (0.30, 0.30, 0.284, 0.116) 대 무상한 (0.611, 0.389, 0, 0)이다(N-M1-10. M2 검토의 N16과 같은 결함).
  - 표본 평균의 추정 오차를 다루지 않는다(축소·구간 없음). 공유 세션이 31개만 있어도 계산한다. 해설 끝 문장만 이를 말한다.
  - 화면 Sharpe는 rf를 뺀다((w·μ − rf)/σ, risk.py:169). Strategy Lab·ETF·Signals는 rf를 빼지 않는다. 같은 이름의 Sharpe가 화면마다 뜻이 다르다(M2 검토의 N3).
  - 혼합 시장 바스켓은 상관 과소(DF-02), 가상자산은 252 연율화(D12-11)를 그대로 받는다.
  - 같은 종목을 두 번 넣으면 비중이 나뉜다. QQQ, QQQ, TLT에서 상관행렬 행렬식 2.2e-16, min_vol 비중 0.098/0.098/0.804이고 converged=True다(P01-12). 금리 수준 계열을 넣으면 수익률이 무의미하다(DF-01).
- **적용 범위:** 같은 시장 주식·ETF 바스켓의 위험 구조(min_vol, risk_parity) 서술에 쓴다. max_sharpe 비중과 프런티어의 수익 축은 M-02 수정 전과 초과수익 음수 구간에서는 판단에 쓰지 않는다. R-15 inverse-vol(optimize.py:139-251)은 이 항목 밖이다. M2-26으로 따로 적었던 같은 모델을 이 항목에 합쳤다(같은 함수, 같은 테스트 5건).
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_optimizer_weights_are_a_long_only_allocation, ::test_optimizer_objectives_actually_optimize, ::test_risk_parity_equalizes_risk_contributions(기여 0.25±0.02), ::test_max_weight_cap_is_respected, ::test_frontier_is_traced_and_cloud_is_dominated (qa/acceptance_results.json PASS). 모두 합성 바스켓의 행동 검사이고 외부 기준값 대조는 없다. 재현 work/m1v/v2_opt.py(음수 초과수익, 상한 불일치).
- **관련 오류:** M-02, DF-01, DF-02, D12-01, D12-11 (병합: M-03), P01-05, P01-06, P01-12, M02, 신규 N-M1-09, 신규 N-M1-10(= N16), M2 신규 N3
- **화면:** Portfolio: 목적 칩·return/vol/Sharpe 칩(ui/portfolio_page.py:146-153), 비중·위험 기여 표, 네 목적 비교표(:159-174), 프런티어 차트(:176), 해설·AI 페이로드(:179-194); ui/qcharts.py:frontier_chart:161

### 6.2 전략·검증 게이트

#### 24. M2-01 일간 손익 시뮬레이터 (strategies.simulate · equity_curve · summary · align_panel)

- **위치:** core/quant/strategies.py:align_panel:51-66; core/quant/strategies.py:simulate:69-90; core/quant/strategies.py:equity_curve:93-94; core/quant/strategies.py:summary:97-105; ui/strategy_lab_page.py:run_family:113-114,130-131; ui/etf_page.py:(sleeves):80-90; core/ficc/vol_products.py:roll_down_backtest:95-119; docs/asset_expansion_study.py:rf_daily:148-153, strategy_card:174-185
- **목적:** 가중치 경로(T×N)를 일간 순손익과 회전율로 바꾼다. Strategy Lab, ETF 화면 슬리브, 자산확장 스터디 카드, VIX 롤다운 백테스트가 모두 이 엔진을 쓴다.
- **가정:**
  - 체결: 종가 t에 정한 비중을 같은 종가 t에 체결하고 t→t+1 단순수익률을 번다(strategies.py:82-87). 실행 지연은 0이다.
  - 비용: cost_bps × Σ\|Δw\| 편도 선형 과금이다(:88-89). 첫 진입도 과금한다. 마지막 행의 비중 변경은 보유되지 않아 과금하지 않는다. 시장충격, 호가 단위, 최소 수수료는 없다.
  - 보유: 목표 비중을 매일 비용 없이 다시 맞춘다. 가격 드리프트를 무시한다(K-e).
  - 현금: 미배분 비율 1−Σw⁺만 cash_daily를 번다(:84-87). 음수 비중이 하나라도 있으면 현금 이자 0, 차입·대주 비용 0이다(:85). Σw⁺>1이면 음의 현금이 cash_daily 금리로 차입된다.
  - cash_daily 값: Strategy Lab과 ETF 화면은 연 3% 고정(0.03/252, ui/strategy_lab_page.py:113, ui/etf_page.py:81)이다. 스터디는 FRED DGS3MO를 쓰고 결측·실패는 3%다. KRW 슬리브에도 USD 금리를 쓴다(docs/asset_expansion_study.py:148-153, :273).
  - 가격: History.closes를 그대로 쓴다. 공급자에 따라 총수익(Yahoo 수정종가)과 가격수익(KIS 수정주가)이 섞인다. convention_warning(core/quant/history.py:105-117)은 경고만 한다. 가격 유효성(NaN·0·inf)은 여기서 검사하지 않는다.
  - 정렬: 날짜 교집합이다(align_panel). 종가 시각이 다른 시장도 같은 날로 묶는다. 공유 세션이 60 미만이면 거부한다.
  - summary: 252로 연율화한다. Sharpe = 평균×252/(표준편차(ddof 1)×√252)이고 무위험 수익을 빼지 않는다. 연수익은 n/252년 기하 평균이다.
- **한계:**
  - 미과금 리밸런싱(K-e): 합성 4종목(일 σ 1%, 현금 약 51%) trend_switch에서 암묵적 매일 리밸런싱 회전이 연 0.79배다. 50bp/편도면 연 약 40bp가 빠진다. 과금된 회전은 연 2.06배다. 드리프트 장부와 총수익 차이는 연 약 1bp다(q1.py, q5.py, 검증자 재실행 같은 값).
  - 현금 가정 민감도: 같은 합성에서 현금 3%가 Sharpe를 −0.07에서 0.21로 올린다(+0.28). 무위험 3%를 빼면 −0.33이다. 저금리 구간(2009–2021)에서는 현금 수익이 과대다(N3).
  - 전액 현금 구간의 손익은 상수다. 표준편차가 부동소수 잡음(5.4e-20)이라 Sharpe가 3.48e16이 된다(P01-11, HEAD fa28059 재현).
  - 가상자산 365봉도 252로 연율화한다. 변동성·Sharpe 표시값이 √(252/365)=0.831배다(D12-11/M-03).
  - equity_curve는 pnl보다 1점 길다. Strategy Lab 차트(ui/xcharts.py:72-86)가 이를 OOS 날짜 수에 맞추지 않아 ValueError로 멈춘다(FC-01, HEAD 재현: shapes (300,) and (301,)).
  - 금리·지수 수준 시계열(KIS Y0xxx, ^TNX)을 가격으로 처리한다(DF-01).
  - 이벤트 엔진(Nautilus)과 체결·비용 패리티를 이룰 수 없다(K-e).
- **적용 범위:** 일별 종가 기반 연구 비교에만 쓴다. 실거래 체결 추정, 장중 전략, 공매도·레버리지 비용이 중요한 전략, 금리·지수 수준 시계열에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (tests/expansion_acceptance.py selfcheck_strategies; HEAD fa28059 재실행 ok: 매수후보유 재현 1e-9, 비용은 손해만, 회전 합 1); tests/expansion_acceptance.py::test_strategies_are_causal (HEAD fa28059 PASS). 외부 독립 기준값 없음. 정량값: registers/work/m2_strategy_gate/q1.py, q5.py.
- **관련 오류:** K-e, P01-11, D12-11 (병합: M-03), functional_completeness/FC-01 (병합: P01-01), DF-01, DF-02, MF-03, M02; 미등재 신규 N3(현금 3% 고정·통화 불일치·초과수익 아닌 Sharpe)
- **화면:** Strategy Lab 'out-of-sample equity' 차트와 통계 타일(ui/strategy_lab_page.py:261-273, 지금은 렌더 크래시); ETF 화면 'Trend switch Sharpe'·'Vol-target Sharpe'·'Buy & hold Sharpe'·'Trend MDD'(ui/etf_page.py:227-231)와 해설(:145-150); Strategy Lab scorecard의 스터디 카드 수치

#### 25. M2-02 추세 전환 trend_switch (Faber SMA / MOP 부호)

- **위치:** core/quant/strategies.py:trend_switch:162-187; core/quant/strategies.py:_sma:111-116; core/quant/strategies.py:realised_vol:119-126; core/quant/strategies.py:_rebalance_days,_hold:146-156; ui/strategy_lab_page.py:FAMILIES:35-36; ui/etf_page.py:80-90; docs/asset_expansion_study.py:run_trend:271-279
- **목적:** 슬리브마다 가격이 SMA 위(또는 lookback 수익이 양수)면 보유하고 아니면 현금으로 둔다. 1/N 동일가중이다.
- **가정:**
  - 평가는 21 또는 42세션마다다(Lab·스터디 격자). lookback은 126/210/252세션이다(≈6/10/12개월, 월말 평가 아님). ETF 화면은 SMA 210, 21세션 하나다.
  - 슬리브당 1/N, 롱 또는 현금만이다.
  - rule='tsmom': 함수는 P_t/P_{t−L} − 1 − Σrf(일간 금리의 산술 합)의 부호를 본다(:180). 그러나 Lab·스터디 격자는 cash_rate_daily를 넘기지 않아 rf=0이다. 실제 신호는 초과수익이 아니라 원수익의 부호다(N14). ETF 화면은 rf를 넘기지만 rule='sma'라 쓰이지 않는다.
  - vol_cap(22세션 실현변동성 축소, :174, :183-185)은 어떤 호출부도 쓰지 않는다.
  - 신호는 종가 t까지만 쓴다(인과적).
- **한계:**
  - 원 논문의 월말 평가·총수익 지수와 다르다. 평가일 위상에 따른 민감도는 측정하지 않았다.
  - MOP 부호 규칙이 초과수익이 아니라 원수익을 본다(N14). 금리 3–5% 구간에서는 원 규칙보다 롱 판정이 많다.
  - 현금 비중이 커서 현금 3% 가정에 Sharpe가 민감하다(M2-01의 +0.28, N3).
  - ETF 화면 'Trend switch Sharpe'는 워밍업 210세션(비중 0, 현금 3%)을 포함한 전체 손익으로 계산한다(ui/etf_page.py:85-88). 504세션 무추세 합성에서 중앙값 0.11 대 워밍업 제외 −0.04이고, 6.8%의 시드에서 \|Sharpe\|>10이다(M6 그룹 c5_etf_sleeve_warmup.py, 검증자 재실행).
  - 혼합 시장 날짜 교집합의 시차 문제를 받는다(DF-02).
  - 저장 카드 S_E1_trend_us·S_E1_trend_krx는 모두 REJECT다(2026-09-27 생성).
- **적용 범위:** 유동성 있는 ETF·지수 슬리브의 일별 연구에 쓴다. 개별 종목 단기매매나 현재 신호 제공에는 쓰지 않는다(PASS 카드 없음).
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (추세 슬리브 보유 비율 >0.35, 워밍업 구간 0, 비중 ≤0.5; HEAD fa28059 ok); tests/expansion_acceptance.py::test_strategies_are_causal (HEAD PASS). 논문 수치 재현 없음. N14 근거: grep 결과 cash_rate_daily를 넘기는 호출부는 ui/etf_page.py:82(rule='sma')뿐이다.
- **관련 오류:** DF-02, P01-11; 미등재 신규 N3, N14; ETF 워밍업 포함 Sharpe(M6 그룹 확인 항목)
- **화면:** Strategy Lab 'Trend switch' 실행(지금 렌더 크래시 FC-01); ETF 화면 추세 슬리브(ui/etf_page.py:80-90, :227-231); scorecard S_E1_*

#### 26. M2-03 변동성 타깃 vol_target (상한형 Moreira–Muir)

- **위치:** core/quant/strategies.py:vol_target:190-209; core/quant/strategies.py:realised_vol:119-126; ui/strategy_lab_page.py:FAMILIES:37; ui/etf_page.py:83,86; docs/asset_expansion_study.py:run_vol_target:282-290
- **목적:** 직전 실현변동성에 반비례해 노출을 정한다. w = min(cap, σ*/σ̂).
- **가정:**
  - σ̂ = 직전 22 또는 44세션 로그수익 표준편차(ddof 1)×√252다.
  - 21세션마다 갱신한다. 상대 변화가 10% 이하면 이전 비중을 유지한다(band 0.10, :205-206).
  - 열마다 따로 계산한다. 1/N으로 나누지 않는다(단일 자산 설계). cap 기본 1.0이다.
  - σ̂가 비정상이면 비중 0이다(:204).
- **한계:**
  - 다종목 입력이면 열마다 min(cap, σ*/σ̂)라 총노출이 최대 N배다. 현실적 변동성(연 14–22%, Lab 기본 SPY·QQQ·TLT·GLD 수준) 합성 4종목에서 Lab 격자 8개의 평균 총노출은 2.0–3.5배, 최대 약 4.0배다(검증자 v1.py). 저변동(연 6–12%) 합성이면 3.5–4.0배다(q6.py). Σw>1이면 음의 현금이 현금 금리 3%로 차입된다(simulate:85-87). 라벨 'Capped volatility target'과 1배 동일가중 벤치마크와 맞지 않는다(N1).
  - 원 논문의 월간 분산 역수 가중과 정규화 상수가 없다(Cederburg 실시간형).
  - 22세션 창은 급변 직후 반응이 늦다. 갭 위험은 반영하지 않는다.
- **적용 범위:** 단일 자산(지수 ETF) 변동성 타깃에만 쓴다. 다종목 포트폴리오 변동성 타깃으로 쓰면 안 된다. 저장 카드 S_E2_voltarget_spy·S_E2_voltarget_kodex200은 모두 REJECT다.
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (저변동 자산 비중 > 고변동, 열별 최대 ≤1.0; HEAD fa28059 ok); tests/expansion_acceptance.py::test_strategies_are_causal (HEAD PASS). 다종목 총노출 검사는 테스트가 없다. 노출 수치: registers/work/m2_verifier/v1.py, m2_strategy_gate/q6.py.
- **관련 오류:** 미등재 신규 N1, N3; D12-11(가상자산 입력 시)
- **화면:** Strategy Lab 'Capped volatility target'; ETF 화면 'Vol-target Sharpe'(target 0.12, 단일 종목, ui/etf_page.py:83, :231); scorecard S_E2_*

#### 27. M2-04 횡단면 모멘텀 xs_momentum (Jegadeesh–Titman 12-1)

- **위치:** core/quant/strategies.py:xs_momentum:212-229; ui/strategy_lab_page.py:FAMILIES:38-39; docs/asset_expansion_study.py:run_xs_momentum:303-310
- **목적:** [t−lookback, t−skip] 수익률 순위 상위 1/3을 동일가중 보유한다.
- **가정:**
  - 점수 = P_{t−skip}/P_{t−lookback} − 1이다(lookback 126/189/252, skip 5/21).
  - 상위 k = max(1, round(N/3))개를 1/k씩 보유한다. Lab은 long_only=True다.
  - 21/42세션마다 리밸런싱한다. 동률은 stable 정렬 순서다.
  - 배당 반영 여부는 공급자 종가 관례를 따른다.
- **한계:**
  - 종목이 적으면 집중된다. Lab 기본 4종목(SPY, QQQ, TLT, GLD)이면 1종목만 보유한다.
  - 사용자가 고른 현재 종목이라 생존 편향이 있다.
  - 롱숏(long_only=False)이면 현금 이자 0, 대주 비용 0이다.
- **적용 범위:** 섹터 ETF처럼 6개 이상 동질 유니버스에 쓴다. 소수 종목이나 이질 자산 혼합에는 맞지 않는다. 저장 카드 S_E5_xsmom_sectors는 REJECT다.
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (추세 종목 선택, 비중 합 1, 롱숏 순 0; HEAD fa28059 ok); tests/expansion_acceptance.py::test_strategies_are_causal (HEAD PASS).
- **관련 오류:** DF-02
- **화면:** Strategy Lab 'Cross-sectional momentum'; scorecard S_E5

#### 28. M2-05 시계열 모멘텀 tsmom (MOP 2012) + ewma_vol

- **위치:** core/quant/strategies.py:tsmom:232-252; core/quant/strategies.py:ewma_vol:129-143; ui/strategy_lab_page.py:FAMILIES:40-41; docs/asset_expansion_study.py:run_tsmom:313-322
- **목적:** 자산별 lookback 수익 부호 × (변동성 목표/EWMA 변동성)으로 롱숏 포지션을 잡는다.
- **가정:**
  - 포지션 = sign(r_{t−L,t} − Σrf) × min(σ*/σ̂, cap)/N이다. Lab 격자: lookback 63/126/252, σ* 0.20/0.40, cap 1.0, step 21/42, 롱숏.
  - σ̂ = EWMA(질량중심 60, δ=60/61) 로그수익 분산×261의 제곱근이다(MOP 식 1). 평균도 EWMA로 뺀다.
  - Lab·스터디는 cash_rate_daily를 넘기지 않아 Σrf=0이다. 신호는 초과수익이 아니라 원수익 부호다(N14).
  - EWMA 초기값은 r[:22]로 시드하지만 출력은 t≥22부터라 미래 정보가 없다. docstring은 σ̂_{t−1}이지만 코드는 t일 수익까지 포함한 vol[t]를 쓴다(인과성은 유지).
- **한계:**
  - EWMA 연율 261과 다른 곳의 252가 다르다. 분산은 3.6%, σ는 1.8% 크다(√(261/252)=1.0177). 포지션은 1.7% 작다. MOP 원식을 따른 것이라 영향은 작다.
  - MOP 부호가 초과수익이 아니라 원수익이다(N14).
  - 공매도가 하나라도 있으면 현금 이자 0, 차입·증거금 비용 0이다.
  - 선물 롤·만기를 반영하지 않는다. 연속 가격 시계열을 가정한다.
  - /N 때문에 총노출은 cap 이하다.
- **적용 범위:** 선물·지수 다자산 시계열 모멘텀 연구에 쓴다. 저장 카드 S_B3_tsmom_futures는 REJECT(SR 0.08)다. 개별 주식 롱숏 실거래 비용 평가에는 맞지 않는다.
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (상승 롱·하락 숏, \|w\|≤1/3, long_only 클립; HEAD fa28059 ok); tests/expansion_acceptance.py::test_strategies_are_causal (HEAD PASS).
- **관련 오류:** data_flow/MF-02(연속 선물 함수는 죽은 코드, 연결하면 롤 오류), DF-01; 미등재 신규 N14
- **화면:** Strategy Lab 'Time-series momentum'; scorecard S_B3

#### 29. M2-06 페어 pairs (Engle–Granger 스프레드) + half_life + adf_pvalue

- **위치:** core/quant/strategies.py:pairs:287-327; core/quant/strategies.py:PairsDiagnostics:274-284; core/quant/strategies.py:half_life:255-263; core/quant/strategies.py:adf_pvalue:266-271; ui/strategy_lab_page.py:run_family:106-112; docs/asset_expansion_study.py:run_pairs:347-364
- **목적:** 형성 기간에 ln y = a + b ln x를 적합해 잔차 z-점수로 진입·청산한다. 형성 창마다 ADF p와 반감기를 기록한다.
- **가정:**
  - 형성 126/252세션 OLS로 (a, b, μ, σ)를 동결하고 다음 126세션을 거래한다. 거래창 경계에서 포지션이 초기화된다(:310).
  - \|z\| > entry(1.5–3.0)면 진입, z가 exit(0)를 지나면 청산한다. max_hold는 어떤 호출부도 쓰지 않는다.
  - 비중 W = [pos, −pos·b]/(1+\|b\|)·gross다. long_only면 싼 쪽만 보유하고 평시 50/50을 보유한다(:320-325).
  - ADF는 statsmodels adfuller(AIC 시차)이고 반감기는 AR(1) −ln2/lnφ다(φ≤0 또는 ≥1이면 inf).
- **한계:**
  - 추정 잔차에 일반 ADF 임계값을 쓴다. 독립 랜덤워크 300쌍(252세션)에서 5% 기각률이 18%다. Engle–Granger coint는 6%다. 카드 문구 'ADF rejects a unit root in X% of windows'가 공적분을 과대 표시한다(N5, q3.py 검증자 재실행 같은 값).
  - docstring은 'dollar-neutral'이지만 순노출이 (1−b)/(1+\|b\|)다. b<0이면 두 다리가 같은 방향이다(N6).
  - statsmodels: requirements.txt:10에 선언됐다(커밋 6054b33, K-a 부분 수정). pyproject.toml:10-17 dependencies에는 아직 없다. 없으면 adf_pvalue가 경고 없이 NaN이다(FC-02). HEAD 환경엔 0.15.0이 있다.
  - adfuller가 FutureWarning을 낸다(0.16 또는 2027-07 이후 기본 반환형 변경). 0.15.0의 ADFullerResult도 [1]이 p값이라 지금 형태로는 깨지지 않는다(검증자 확인). 경고만 남는다(N10, 위험 낮음).
  - 현금 이자 0, 대주 가능 여부·비용 제약 없음.
- **적용 범위:** 같은 기초자산의 두 상장 상품, 보통주·우선주처럼 경제적 연결이 강한 쌍에만 쓴다. 무작위 종목쌍 탐색에는 쓰면 안 된다(다중검정, N5).
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (합성 공적분 쌍 AR(1) 0.9: share_cointegrated >0.6, 반감기 3–15, Sharpe >1, \|W\| 합 ≤1; HEAD fa28059 ok); tests/expansion_acceptance.py::test_strategies_are_causal (pairs 포함, HEAD PASS); 거짓 공적분율: registers/work/m2_strategy_gate/q3.py.
- **관련 오류:** K-a(부분 수정), functional_completeness/FC-02 (병합: TA-03); 미등재 신규 N5, N6, N10
- **화면:** Strategy Lab 'Pairs'; scorecard S_E8_pairs_*, S_S6_pairs_*(첫 줄 ADF 문구)

#### 30. M2-07 가상자산 단기 추세 crypto_trend (Liu–Tsyvinski / Detzel 표결)

- **위치:** core/quant/strategies.py:crypto_trend:330-348; ui/strategy_lab_page.py:FAMILIES:42; ui/strategy_lab_page.py:127(n_trials=len(grid)); docs/asset_expansion_study.py:run_crypto_trend:325-344
- **목적:** 9개 부호 표결(7/14/21/28세션 수익, 가격 대 SMA 10/20/50/100/200)의 평균으로 롱/플랫을 정한다. 히스테리시스가 있다.
- **가정:**
  - 종합값 > +h면 롱, < −h면 플랫, 사이면 직전 상태 유지다(:343-347).
  - 열마다 0 또는 1이다(현물 롱/플랫). 워밍업 200세션은 플랫이다.
  - 비중은 t까지의 정보로 정하고 t→t+1 보유한다(인과).
  - 비용 crypto 10bp/편도(COST_BP_PER_SIDE), embargo 1이다. 주말 비용 배수는 없다.
- **한계:**
  - 종합값은 ±1 표 9개의 평균이라 홀수/9 격자({1,3,5,7,9}/9)에 있다. Lab 격자 [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]는 규칙 3개가 6열로 중복된다(q4.py 검증자 재현). 스터디는 이미 고쳤지만(docs/asset_expansion_study.py:328-333) Lab은 그대로다. n_trials(6 대 실제 3), σ_SR, 고원이 왜곡되고 저장 C3 카드와 프로토콜이 다르다(domain 미지정)(N2 = NEW-M6-09, K-c: Lab은 6 시행으로 채점한다, ui/strategy_lab_page.py:127).
  - 연구 스크립트 주석(docs/asset_expansion_study.py:328-329)은 '0.05, 0.1, 0.2가 같은 규칙'이라고 잘못 적는다. 실제 중복 쌍은 (0.05, 0.1), (0.2, 0.3), (0.4, 0.5)다. 원장 문장(:340-341 'three of them duplicates')은 맞다(NEW-M6-23).
  - 열마다 0/1이라 다종목이면 총노출이 최대 N배다(합성 3종목 평균 1.5–1.9배, 최대 3.0)(N1).
  - 252 연율화(D12-11). 판정은 불변이고 표시 Sharpe와 turnover_annual이 √(252/365)=0.831배로 낮게 나온다(보수적 방향).
  - CRY-1 대조(README.md:671-680): Upbit KRW-BTC는 vol-scaled 대조 대비 PASS(ΔSR +0.496, p 0.028), Binance BTCUSDT는 REJECT(ΔSR +0.182, p 0.243), 2024-01-10 이후 Binance ΔSR −0.049, ETH 재현 REJECT. 카드 C3는 소유자 판정(D-24)으로 PASS를 유지한다.
  - 'BTCUSD' 표기는 cost_class가 'us'(50bp)로 분류한다(K-f). auto 라우팅은 이 표기를 FMP로 보낸다.
  - 현재 신호 상태(지금 롱인지)는 화면에 없다(functional_completeness/FC-04, 감사 12.10).
  - Strategy Lab은 계산 뒤에 원장에 등록한다(K-d).
  - 거래소 간 가격 차이(김치 프리미엄)는 무시한다.
- **적용 범위:** 단일 가상자산 현물 롱/플랫에 쓴다. 저장 카드 S_C3 BTC-USD·KRW-BTC는 PASS다(SR 1.19/1.22, DSR 1.00, N_total 11, 격자 5). Lab 재실행은 다른 격자라 같은 증거가 아니다. 주문이나 실행 신호로 쓰면 안 된다. Crypto 화면 표시(판정 칩, SMA50/200)는 M6-10이다. M6-10에 따로 적었던 규칙의 가정·한계는 이 항목에 합쳤다.
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__(tests/expansion_acceptance.py::selfcheck_strategies, :451-452: 0/1, 워밍업 0, 추세에서 롱 >0.5; HEAD fa28059 ok); tests/expansion_acceptance.py::test_strategies_are_causal(미래를 바꿔도 과거 비중 불변; HEAD PASS). 카드 S_C3_crypto_trend_btcusd(sr_oos 1.19, dsr 0.99998, pbo 0.19, ledger 기록, 격자 5), S_C3_crypto_trend_krwbtc(sr_oos 1.22, pbo 0.27). 격자 중복: docs/nautilus_bridge/register_evidence/M6_crypto_misc/c4_trend_grid.py(Lab 격자 중복 3쌍, 서로 다른 규칙 3개; 연구 격자 5개 모두 다름)와 M2 검증자 q4.py. K-f: 같은 폴더의 c6_costclass.py(BTCUSD → us 50bp).
- **관련 오류:** D12-11 (병합: M-03), functional_completeness/FC-04, K-c, K-d, K-f, NEW-M6-23; 미등재 신규 N1, N2(= NEW-M6-09)
- **화면:** Strategy Lab 'Crypto short-horizon trend'; Crypto 화면 C3 판정 칩(ui/crypto_page.py:91-96, :156-160); scorecard S_C3_*

#### 31. M2-08 위험 균등 전략 risk_parity (롤링 공분산)

- **위치:** core/quant/strategies.py:risk_parity:351-367; core/quant/optimize.py:optimize_portfolio:68-100; core/quant/optimize.py:_risk_contributions:47-52; ui/strategy_lab_page.py:FAMILIES:43; docs/asset_expansion_study.py:run_risk_parity:293-300
- **목적:** 롤링 공분산으로 위험 기여가 같아지는 롱온리 비중을 21/63세션마다 정한다.
- **가정:**
  - 창 125/250/500/750세션 로그수익 공분산×252(ddof 1)다.
  - 롱온리, 합 1, 비레버리지다.
  - SLSQP가 위험 기여 분산을 최소화한다(1/N 시작).
- **한계:**
  - SLSQP 수렴 여부(converged)를 무시하고 비중을 쓴다(strategies.py:366).
  - 표본 공분산이다(축소 없음). 혼합 시장 비동기 종가로 상관이 과소다(DF-02).
  - 창 길이(최대 750)까지는 전액 현금이다.
  - 레버리지 위험 균등(전통적 RP)과 다르다.
  - 인과성 테스트(test_strategies_are_causal)에 risk_parity는 없다.
- **적용 범위:** 소수 자산군 ETF 배분 연구에 쓴다. 저장 카드 S_E3_riskparity_us는 REJECT다.
- **검증 상태:** 테스트로 확인됨. core/quant/strategies.py::__main__ (합 1, 저변동 자산 과대; HEAD fa28059 ok); tests/quant_acceptance.py::test_risk_parity_equalizes_risk_contributions (솔버 수준, RC 0.25±0.02; HEAD fa28059 로컬 PASS).
- **관련 오류:** DF-02, M-02(strategies.py:364 평균이 로그지만 RP 목적함수는 평균을 안 써 영향 없음)
- **화면:** Strategy Lab 'Risk parity'; scorecard S_E3

#### 32. M2-09 격자 손익 행렬과 walk-forward 선택 (pnl_matrix · grid_from · walk_forward)

- **위치:** core/quant/strategies.py:pnl_matrix:379-389; core/quant/strategies.py:grid_from:392-398; core/quant/validate.py:WalkForward:332-342; core/quant/validate.py:walk_forward:345-381; ui/strategy_lab_page.py:run_family:114-116
- **목적:** 격자의 모든 구성 손익(1×·2× 비용)과 회전을 만들고, 원점마다 IS Sharpe 최고 구성을 다음 OOS 블록에 적용해 OOS 손익을 잇는다.
- **가정:**
  - 각 구성 손익은 전체 표본에서 인과적으로 한 번 계산한 열이다.
  - 원점 o에서 [o−756, o) IS Sharpe 최대(nanargmax) 구성을 [o+embargo, o+embargo+126)에 적용한다. 원점은 126 간격이고 OOS 블록은 이어진다.
  - 데이터가 짧으면 첫 IS가 504다. embargo = 계열 보유기간(Lab: 21/21/21/21/1/63/5).
  - 2× 비용 열과 회전율도 선택된 구성을 따른다.
- **한계:**
  - 원점마다 구성이 바뀔 때 전환 회전을 과금하지 않는다. 합성 trend_switch(26원점 중 14회 전환)에서 연 0.31배, 50bp면 연 약 16bp다. 과금 회전 연 1.76배 대비다(N4, q2.py 검증자 재실행 같은 값).
  - IS 선택 기준이 Sharpe라 전액 현금 상수열(Sharpe 3.5e16)이 뽑힌다(P01-11: VIXY 26원점 중 12).
  - 마지막 OOS 블록은 126보다 짧을 수 있다.
  - 'purged'는 embargo 간격만 뜻한다(일간 손익이라 라벨 정화는 필요 없다).
- **적용 범위:** 사전 정의 격자의 일간 손익 행렬에 쓴다. 구성 전환 때 상태를 리셋해야 하는 경로 의존 전략이나 이벤트 엔진 체결에는 그대로 쓸 수 없다.
- **검증 상태:** 테스트로 확인됨. core/quant/validate.py::__main__ (25구성 중 진짜 edge를 원점 60% 이상에서 선택; HEAD fa28059 ok); tests/expansion_acceptance.py::test_gate_rejects_noise_and_keeps_a_real_edge (HEAD PASS); core/quant/strategies.py::__main__ (pnl_matrix 형상, 2×≤1×).
- **관련 오류:** P01-11, functional_completeness/FC-01, K-d, P01-02; 미등재 신규 N4
- **화면:** Strategy Lab 결과 칩 'IS 756 / OOS 126 / embargo …'와 OOS 곡선(ui/strategy_lab_page.py:252-273); AI 페이로드 walk_forward(:155)

#### 33. M2-10 Sharpe·Lo 표준오차·최소 기록 길이 (validate.sharpe · lo_se · min_track_record · _col_sharpe)

- **위치:** core/quant/validate.py:sharpe:137-143; core/quant/validate.py:lo_se:146-153; core/quant/validate.py:min_track_record:156-160; core/quant/validate.py:_col_sharpe:268-270
- **목적:** 게이트 전반의 연간 Sharpe, Lo(2002) iid 표준오차, 구간이 0을 배제하는 데 필요한 세션 수를 낸다.
- **가정:**
  - SR = 평균/표준편차(ddof 1)×√252다. 무위험 수익을 빼지 않는다(현금 수익 포함 총손익). sharpe는 비유한 값을 버린다.
  - Lo SE = √((1+½SR_d²)/T)·√252, iid 정규다.
  - 최소 기록 T > 252·(z/SR)², z = Φ⁻¹(0.95) = 1.645다(SR 1.0이면 682세션).
  - _col_sharpe와 sharpe는 표준편차가 정확히 0일 때만 0을 돌려준다.
- **한계:**
  - iid라 자기상관·비정규성을 무시한다. Lo 보정·HAC는 매크로 카드(gate_stats)에만 있다.
  - 표준편차가 부동소수 잡음(5e-20)이면 Sharpe가 폭주한다(P01-11).
  - 가상자산 √252(D12-11): 표시 0.831배. 최소 기록 세션 수는 단위가 상쇄돼 불변이다.
  - 화면 간 Sharpe 정의가 다르다. FX 캐리 화면은 CAGR/vol(financial_calcs/FC-14), Portfolio 화면은 rf를 뺀 초과 Sharpe(core/quant/risk.py:169), Lab·ETF·Signals는 rf를 빼지 않은 총손익 Sharpe다(N3).
  - 현금 3% 포함 총손익 Sharpe라 현금 비중 큰 전략이 과대다(N3).
- **적용 범위:** 일간 손익의 연 Sharpe 요약과 판정 입력에 쓴다. 월·주 데이터나 꼬리가 큰 옵션형 손익에서는 SE를 믿기 어렵다.
- **검증 상태:** 독립 검증됨. docs/audit/2026-10-27/financial_calcs.md 3장 26행(Sharpe·Lo SE 직접 계산, 차이 0; audit_work/financial_calcs/r06_validate.out 1번); core/quant/validate.py::__main__ (min_track_record(1.0) = 252·1.645² ±1세션; HEAD fa28059 ok); q1.py(상수열 3.48e16).
- **관련 오류:** P01-11, D12-11 (병합: M-03), financial_calcs/FC-14; 미등재 신규 N3
- **화면:** Strategy Lab 'OOS Sharpe'·'2× costs'·'Benchmark SR'·'Haircut SR' 타일(ui/strategy_lab_page.py:262-271); ETF 화면 Sharpe 3개; scorecard 'Key numbers'(:187-189)

#### 34. M2-11 블록 부트스트랩 Sharpe 구간과 벤치마크 차이 검정 (block_bootstrap_ci · sharpe_diff_bootstrap)

- **위치:** core/quant/validate.py:block_bootstrap_ci:163-183; core/quant/validate.py:sharpe_diff_bootstrap:186-208; core/quant/validate.py:score_strategy:501,516-521; ui/strategy_lab_page.py:run_family:119-129
- **목적:** OOS Sharpe의 90% 구간(0 배제가 PASS 조건)과 '벤치마크를 이긴다' 주장의 단측 p를 낸다.
- **가정:**
  - 순환 블록, 블록 10 고정, B 2000(Lab은 1000), 시드 11이다. T < 2×블록이면 NaN이다.
  - 구간: t* = (SR*−SR)/SE*, SE는 Lo iid 식, CI = [SR − t_hi·SE, SR − t_lo·SE]다.
  - 벤치 검정: 같은 블록을 두 계열에 쓴다. p = P*(ΔSR* ≤ 0)이다(백분위, 영가설 중심화 아님).
  - Lab 벤치마크는 동일가중 매일 리밸런싱, 무비용, 현금 없음이다(pairs는 없음).
- **한계:**
  - 스튜던트화에 HAC가 아닌 iid SE를 쓴다. Ledoit–Wolf 원식과 다르다. 블록 길이를 데이터로 정하지 않는다(PW 미사용).
  - 벤치 p는 영가설 하의 p값이 아니라 부트스트랩 분포의 하측 비율이다(근사).
  - 구간 커버리지를 고정한 테스트가 없다. 검증자 시뮬레이션(T 1,500, SR 0.5, 300회, B 500)에서 90% 구간 커버리지는 iid 정규 0.907, AR(1) φ 0.2 0.893, t(4) 0.883이다(몬테카를로 SE 약 0.017). 강한 자기상관에서는 측정하지 않았다.
  - Lab은 전역 GATE['bootstrap_B']를 1000으로 바꿨다가 되돌린다(V-P01-M3). 동시 실행이면 오염된다(P01-05).
- **적용 범위:** 일간 OOS 손익의 Sharpe 구간과 단순 벤치 비교에 쓴다. 매크로 카드의 ΔSR 판정에는 gate_stats의 LW 스튜던트화 부트스트랩을 쓴다.
- **검증 상태:** 테스트로 확인됨. core/quant/validate.py::__main__ (CI가 SR 포함; 잡음 벤치 대비 p<0.10, 자기 자신 벤치 REJECT; HEAD fa28059 ok); tests/expansion_acceptance.py::test_gate_rejects_noise_and_keeps_a_real_edge (ci90 하한 >0; HEAD PASS); 커버리지: registers/work/m2_verifier/v3_coverage.py. tests/macro_m0_harness.py::test_gate_bootstrap_b_is_not_leaked_by_the_expansion_suite(HEAD PASS)는 테스트 스위트의 GATE 복원만 보는 위생 검사다(모델 검증 아님).
- **관련 오류:** V-P01-M3, P01-05, D12-11 (병합: M-03)
- **화면:** Strategy Lab 'OOS Sharpe' 툴팁 90% 구간, 'Benchmark SR' 툴팁 차이·p, 판정 줄(ui/strategy_lab_page.py:262-270, :274)

#### 35. M2-12 디플레이티드 Sharpe DSR (expected_max_sharpe · deflated_sharpe)

- **위치:** core/quant/validate.py:expected_max_sharpe:211-217; core/quant/validate.py:deflated_sharpe:220-237; core/quant/validate.py:score_strategy:503-507; ui/strategy_lab_page.py:run_family:127
- **목적:** N회 시행 중 최고값이라는 선택 편향을 빼고 관측 Sharpe가 기대 최대치를 넘을 확률을 낸다. 0.95 미만이면 REJECT다.
- **가정:**
  - SR0 = σ_SR·[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))] (BLdP 2014)다. N=1이면 0이다.
  - DSR = Φ((SR−SR0)√(T−1)/√(1 − γ3·SR + (γ4−1)/4·SR²)), SR·σ_SR는 일간 단위, γ4는 비초과 첨도다.
  - σ_SR = 전체 표본 G개 구성 일간 Sharpe의 표준편차(ddof 0)다.
  - N = n_trials다. Lab은 len(grid), 스터디는 N_total이다. SR과 T는 OOS 연결 손익이다.
- **한계:**
  - 시행 수가 이번 격자 크기뿐이다(K-c). 원장의 과거 시행·다른 종목 탐색이 빠져 보정이 약할 수 있다. R3에 따라 ⑨-3d 전까지 기준을 유지한다.
  - 이미 OOS인 손익에 선택 보정을 한 번 더 한다(보수적, 원 논문 용도와 다름).
  - 구성이 1–12개면 σ_SR 추정 잡음이 크다(구성 1개면 σ_SR=0이라 PSR 대 0이 된다). 상관 높은 구성은 σ_SR가 작아 SR0도 작다.
  - 분모 ≤0이면 NaN이다. 이때 REJECT가 아니라 REVISE로 가고, CI가 0을 배제해도 사유가 'interval includes zero'로 잘못 표시된다(N12).
  - 상수열이 σ_SR와 DSR를 바꾼다(P01-11: 0.034 대 0.074).
- **적용 범위:** 한 계열 격자 탐색 뒤 OOS 성과의 과최적화 보정에 쓴다. 계열·화면을 넘는 탐색 횟수에는 원장 N_eff(M2-21)가 필요하다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 27행(BLdP 수치 예 E[max SR] 0.1132, DSR 0.9004 재현; r06_validate.out 2번: 생성 계열에서 V.deflated_sharpe 0.929231 = 공식 0.929231); tests/macro_m1_fixtures.py::test_g_dsr_01_reproduces_bldp(V.expected_max_sharpe 고정, DSR 식은 테스트 안에서 계산; HEAD PASS); tests/macro_m7_stats.py::test_dsr01_bldp_psr_units (T-DSR-01, 0.950502/0.900397, gate_stats.psr 경유; HEAD PASS); tests/macro_m7_stats.py::test_dsr02_units_daily_monthly_and_refusal(V.deflated_sharpe 일·월 일치; HEAD PASS); validate.py::__main__ (N 증가 시 DSR 감소).
- **관련 오류:** K-c, P01-11; 미등재 신규 N12
- **화면:** Strategy Lab 'Deflated Sharpe' 타일, 판정 줄 '… after N trials', 원장 칩 툴팁 'counts only this run's grid'(ui/strategy_lab_page.py:254-256, :264); scorecard 'DSR'

#### 36. M2-13 과최적화 확률 PBO (validate.pbo_cscv, CSCV)

- **위치:** core/quant/validate.py:pbo_cscv:240-265; core/quant/validate.py:score_strategy:508; core/quant/validate.py:_decide_strategy:544-555,576-577
- **목적:** T×G 손익 행렬을 블록으로 나눠 IS 최고 구성이 OOS 중앙값 아래로 떨어지는 비율(PBO), 승자의 OOS 손실 비율, IS→OOS 기울기를 낸다.
- **가정:**
  - S = 8(T<2000) 또는 16(T≥2000) 연속 블록, C(S, S/2) 분할 전부다.
  - r = #{OOS Sharpe ≤ 승자 OOS Sharpe}, w = r/(G+1), PBO = mean(logit(w) < 0)이다.
  - 구성 < 8이면 판정에 안 쓰고 승자 OOS 손실 비율(≤10%)로 대신한다.
  - 고원(거의 같은 구성)에선 PBO≈0.5가 구조적이라 손실 비율 ≤10%면 통과로 본다.
- **한계:**
  - λ<0만 센다(FC-07). 홀수 G에서 약 1/G 낮다(G=9: 0.405 대 0.516). 지금 Lab·스터디의 8개 이상 격자는 모두 짝수(8·12)라 현재 판정 차이는 0이다.
  - S=16이면 12,870 분할을 루프로 돌아 Lab 실행당 약 8–10초다(P01-02).
  - 상수열이 있으면 PBO가 0.0이 된다(P01-11).
  - 동률을 ≤로 세서 중복 열(N2)이 순위를 왜곡한다.
- **적용 범위:** 8개 이상 서로 다른 구성의 동질 격자에 쓴다. 소격자·중복 구성에서는 의미가 약하다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 28행과 FC-07(pypbo 원문 대조, 짝수 G 일치, 홀수 G 차이 재현); tests/macro_m7_stats.py::test_pbo01_noise_control_200_panels_and_objectives (T-PBO-01, 0.535897 = 6897/12870, validate.pbo_cscv와 1e-12 일치; HEAD PASS); tests/macro_m1_fixtures.py::test_t_pbo_01_noise_control_reproduces (HEAD PASS); validate.py::__main__ (잡음 평균 0.3–0.7). 저장 카드 격자 크기: 8·12(짝수), 5·2·1(8 미만).
- **관련 오류:** financial_calcs/FC-07, P01-02, P01-11; 미등재 신규 N2
- **화면:** Strategy Lab 'PBO' 타일과 판정 줄(ui/strategy_lab_page.py:265, :274); scorecard 'PBO'

#### 37. M2-14 전략 게이트 판정 규칙 (score_strategy · _decide_strategy · GATE · plateau_share · year_stats · regime_split)

- **위치:** core/quant/validate.py:GATE:53-74; core/quant/validate.py:plateau_share:384-418; core/quant/validate.py:full_years,year_stats:421-437; core/quant/validate.py:regime_split:440-452; core/quant/validate.py:score_strategy:492-533; core/quant/validate.py:_decide_strategy:536-622; core/quant/validate.py:data_checks:298-326(미사용); ui/strategy_lab_page.py:run_family:85-136; ui/strategy_lab_page.py:narrative,payload:139-155; docs/asset_expansion_study.py:strategy_card:174-210
- **목적:** walk-forward 결과에 사전 등록 기준을 적용해 PASS / REVISE / REJECT / INSUFFICIENT_DATA와 이유, 수정 목표, 평이한 판정 줄을 낸다.
- **가정:**
  - 임계값: CI 90% 하한 >0, DSR ≥0.95, PBO ≤0.05(또는 승자 OOS 손실 ≤10%), OOS/IS ≥0.5, 양수 연도 ≥60%, 2× 비용 Sharpe >0, 고원 ≥50%·경계 아님, 거래 ≥100.
  - 순서: INSUFFICIENT_DATA(거래 <30, 만 연수 <5, 세션 <1,260) → REJECT(DSR <0.95; PBO >0.20이면서 승자 손실 >10%이고 구성 ≥8; 2× 비용 손실이면서 CI가 0 포함; 벤치 p >0.10) → PASS(전부 충족) → INSUFFICIENT_DATA(CI만 실패하고 최소 기록 미달) → REVISE(공학 검사 중 첫 실패, 없으면 'interval').
  - 거래 수 = 회전이 0이 아닌 OOS 세션 수(포지션 변경 횟수)다.
  - 고원·경계는 마지막 원점의 IS Sharpe만 본다. domain으로 자연 경계를 뺀다(Lab은 domain을 주지 않는다).
  - 양수 연도 비율은 부분 연도를 포함한다. 레짐 분할과 McLean–Pontiff 0.6 헤어컷은 인쇄만 한다.
- **한계:**
  - 게이트 전체의 검정력을 측정한 적이 없다. 자체 점검의 합성 진짜 edge(SR 1.0, 2,520세션)는 CI·DSR·PBO를 통과하지만 고원 규칙 때문에 REVISE다(이웃이 잡음이고 격자 끝; 검증자 재현 plateau 0.0, edge True). 고원 규칙은 고립된 진짜 edge도 막는다.
  - 표본 하한(만 5년·1,260세션·30거래)을 넘으면, 최소 기록 길이에 못 미쳐도 DSR <0.95는 INSUFFICIENT가 아니라 REJECT다(REJECT 검사 :593이 INSUFFICIENT 분기 :606보다 먼저다).
  - REVISE 사유 오표시(N12): CI가 0을 배제하고 공학 검사 5개가 모두 통과했는데 DSR이 NaN이거나 PBO가 0.05–0.20(또는 소격자 승자 손실 >10%)이면, 사유가 'interval check failed (interval includes zero)', 수정 목표가 'extend history'로 나온다(:613-622; 검증자 v2.py 재현 3사례).
  - 입력 데이터 점검이 없다(N13). validate.data_checks(:298-326: 0 수익 비율, ±50% 점프, 날짜 공백, 신선도)는 앱 어디서도 부르지 않는다. 자체 점검 :927은 'or True'로 항상 참이다.
  - OOS/IS가 둘 다 음수면 비율이 양수로 통과할 수 있다(그때 CI는 이미 실패한다).
  - 레짐 분할의 고/저 변동성 기준이 OOS 전체 중앙값이다. docstring은 'known at t'라고 하지만 시점 t에 알 수 없다(인쇄만, N9).
  - Lab 고유: n_trials=격자 크기(K-c), B 1000(V-P01-M3), 현금 3% 고정(N3), 틱 하한 없음(MF-02), 합성 입력도 판정 칩(D03-09), 계산 뒤 등록(K-d), 렌더 크래시(FC-01). Lab 자체 점검은 차트를 그리지 않아 FC-01을 잡지 못한다.
  - 저장 스터디 카드(2026-09-27)는 옛 n_years(달력 연도 수)로 기록·표시한다. 예: S_E1_trend_krx '1,884 sessions (9 years)', 현 정의 약 7. 모두 ≥5라 판정은 같다(N7, R3로 재채점 안 함).
  - 가상자산 252 연율화(D12-11)는 판정을 바꾸지 않는다(부호·DSR·PBO·비율·세션 수는 단위 무관). 표시 Sharpe·헤어컷·연 회전만 영향을 받는다.
- **적용 범위:** 사전 정의 격자를 가진 일간 전략의 연구 채택 판정에 쓴다. 실거래 승인이나 주문 근거가 아니다(주문 경로 없음). 저장 카드 판정 기준은 R3 ⑨-3d 전까지 바꾸지 않는다.
- **검증 상태:** 테스트로 확인됨. core/quant/validate.py::__main__ (잡음 5패널 모두 PASS 아님, 자기 벤치 REJECT, 소격자 'reported only'; HEAD fa28059 출력 'ok REVISE SR 1.35 DSR 0.96 PBO 0.03 \| noise: REJECT PBO 0.53'); tests/expansion_acceptance.py::test_gate_rejects_noise_and_keeps_a_real_edge, ::test_gate_counts_whole_years_and_costs_by_the_table (HEAD PASS); ui/strategy_lab_page.py::__main__ (expansion/selfcheck_strategy_lab; HEAD 'ok INSUFFICIENT_DATA INSUFFICIENT_DATA'); tests/macro_ui_views.py::test_strategy_lab_builds_with_foreign_cards_in_a_temp_cards_dir (HEAD PASS); N12 재현: registers/work/m2_verifier/v2.py.
- **관련 오류:** K-c, K-d, V-P01-M3, D03-09, functional_completeness/MF-02, functional_completeness/FC-01 (병합: P01-01), functional_completeness/FC-06, DF-02, P01-05, D12-11 (병합: M-03), M02; 미등재 신규 N3, N7, N9, N12, N13
- **화면:** Strategy Lab 판정 칩·이유·통계 타일 11개·판정 줄·AI 분석 패널(ui/strategy_lab_page.py:241-276), scorecard 표와 카드 상세(:158-212); Crypto·Quant Lab·ETF 화면의 카드 판정 칩

#### 38. M2-15 비용 분류와 비용표 (cost_class · cost_floor_bp · cost_bp · COST_BP_PER_SIDE)

- **위치:** core/quant/validate.py:COST_BP_PER_SIDE:78; core/quant/validate.py:KRX_ETF_CODES:82-84; core/quant/validate.py:cost_class:87-112; core/quant/validate.py:cost_floor_bp:115-121; core/quant/validate.py:cost_bp:124-131; ui/strategy_lab_page.py:run_family:92-103; ui/strategy_lab_page.py:register_trials:71; ui/etf_page.py:84; ui/fx_page.py:159,306
- **목적:** 종목을 비용 행(krx_etf 3, krx_stock 35, us 50, crypto 10, futures 5, fx 10 bp/편도)으로 나누고 한 실행의 최저 허용 비용을 정한다. Lab의 판정 보류와 원장 market 칸을 정한다.
- **가정:**
  - 비용표는 사전 등록값(P10)이고 여기서만 정의한다. R-26 틱 하한(core/quant/instruments.py:cost_per_side)이 이 표를 읽는다.
  - 분류 순서: 상품 레지스트리 → 가상자산 형식(-USD/-USDT/-KRW, BTC-, _looks_crypto) → FX(=X, FX@) → 선물(=F, KRX 지수선물 코드) → 6자리 KRX(KRX_ETF_CODES·레지스트리에 있으면 ETF, 아니면 주식 35bp) → KIS 해외(NAS:/NYS:/AMS:) → 알파벳만이면 us → 그 외 None.
  - 한 실행에 한 요율이다. 종목 요율의 최댓값을 모든 다리에 쓴다.
  - 입력 비용이 표보다 낮으면 실행은 하고 판정을 보류한다.
- **한계:**
  - 외부 티커 형식을 잘못 분류한다(K-f). HEAD 직접 호출에서 BTCUSD, EURUSD, ETHBTC, DOGE → 'us'(50bp)다.
  - 레지스트리에 없는 KRX ETF(예: 122630)는 주식 35bp로 과금한다(의도된 과대 과금, HEAD 확인).
  - 표에 없는 형식(^TNX, ^GSPC, Y0101, SHEL.L)은 None이다. Lab은 비용을 직접 넣어야 돌고 판정은 보류된다.
  - Lab은 틱 하한(R-26, instruments.cost_per_side)을 쓰지 않는다. 저가 ETF 비용이 규칙보다 최대 약 25배 낮다(MF-02).
  - 화면마다 비용 출처가 다르다. Signals 기본 10bp(FC-08), ETF 화면 3/50 하드코딩(ui/etf_page.py:84), FX 화면 cost_bp('fx')다.
  - 요율 자체(us 50bp, krx_stock 35bp 등)를 실제 수수료·세금표와 대조한 근거를 찾지 못했다(미검증).
- **적용 범위:** 표에 있는 6개 시장 형식의 비용 하한에 쓴다. 표에 없는 거래소(LSE 등)는 None으로 판정을 보류한다. 시장충격·슬리피지 모형이 아니다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::test_gate_counts_whole_years_and_costs_by_the_table (HEAD fa28059 PASS); HEAD 직접 호출로 K-f·122630·None 재현; ui/strategy_lab_page.py::__main__ (5bp < 50bp → WITHHELD, 빈칸 → 50bp; HEAD ok).
- **관련 오류:** K-f, functional_completeness/MF-02, functional_completeness/FC-08, D03-09
- **화면:** Strategy Lab 'Cost bp/side'(빈칸=table), 보류 notice와 'NO VERDICT' 칩(ui/strategy_lab_page.py:221-222, :247-251), 원장 market 칸; FX 화면 Cost 기본값(ui/fx_page.py:159)

#### 39. M2-16 분포 검증 루프 (score_distribution · kupiec · christoffersen · traffic_light · coverage_check · pit_tests · crps · dm_test)

- **위치:** core/quant/validate.py:newey_west_t,dm_test:273-292; core/quant/validate.py:kupiec:628-638; core/quant/validate.py:christoffersen:641-658; core/quant/validate.py:traffic_light:661-663; core/quant/validate.py:coverage_check:666-673; core/quant/validate.py:pit_tests:676-710; core/quant/validate.py:crps:713-722; core/quant/validate.py:score_distribution:741-796; docs/asset_expansion_study.py:run_garch:498-505
- **목적:** 롤링 VaR·팬의 보정 상태를 검정해 분포 모형 카드(D_*)를 판정한다.
- **가정:**
  - Kupiec POF(χ²₁; 예외 0 또는 전부면 z 근사), Christoffersen 독립·조건부(h=1만), 바젤 신호등(최근 250일 99% 예외 0–4 녹, 5–9 황, ≥10 적).
  - 90% 밴드 커버리지 ±2SE, PIT: KS·10구간 χ²·Berkowitz LR(χ²₃)·(u−ū)^k 상관도(k 1–4, lag 1/5/20, ±2/√n).
  - CRPS 표본식, DM t(Newey–West 시차, 기본 0).
  - 판정: 원점 <500이면 INSUFFICIENT; 95% 초과율 ≥10%, 적신호, KS p<0.01, 비수렴 >5%면 REJECT; 95% Kupiec·군집·커버리지·PIT·녹신호 전부 통과면 PASS; 아니면 REVISE.
- **한계:**
  - GATE['var99_min_origins'](1000)는 정의만 있고 쓰지 않는다(grep: validate.py:72뿐). 99% 예외로 만든 신호등이 원점 500부터 판정(적신호 REJECT, 녹색 아님 REVISE)에 들어간다. 99% Kupiec p는 인쇄만 한다(N8).
  - h>1이면 Christoffersen을 생략하고 그 검사를 통과로 본다. 겹친 원점의 자기상관을 보정하지 않는다.
  - Kupiec는 예외 0 또는 전부일 때 LR 대신 점수(z²) 검정이다. 정확 LR과 p가 다르다(financial_calcs.md 6장; 게이트 표본에서는 결론이 같음을 손계산으로만 확인).
  - PIT 상관도 플래그 12개 중 하나만 걸려도 실패다(다중검정 미보정). 잡음에서 거짓 실패율은 측정하지 않았다.
- **적용 범위:** 1일 VaR와 팬 차트 보정 검사에 쓴다. 판정 근거 표본은 원점 ≥500이다.
- **검증 상태:** 테스트로 확인됨. core/quant/validate.py::__main__ (정확한 5% 모형 통과, 11%는 p<0.01, 군집 예외 독립성 실패, 균등 PIT 통과·u² 실패, CRPS 점질량 0; HEAD fa28059 ok); tests/expansion_acceptance.py::test_gate_rejects_noise_and_keeps_a_real_edge (kupiec, pit_tests 각 1건; HEAD PASS); financial_calcs.md 1장: Kupiec·Christoffersen·PIT는 코드 읽기만.
- **관련 오류:** 미등재 신규 N8
- **화면:** Strategy Lab scorecard의 분포 카드 D_Q_*·D_C2_* 줄; Quant Lab·Crypto 화면 카드 칩(ui/quant_lab_page.py:168-174, ui/crypto_page.py:91-96)

#### 40. M2-17 ΔSR 추론: LW-HAC 표준오차·스튜던트화 블록 부트스트랩·Politis–White 블록 (gate_stats)

- **위치:** core/quant/gate_stats.py:optimal_block_length,pw_block,pw_block_floor:37-83; core/quant/gate_stats.py:block_indices,row_sharpes:86-115; core/quant/gate_stats.py:delta_sr,_lw_moments,influence_function_dsr:200-225; core/quant/gate_stats.py:lrv_qs_andrews,lrv_bartlett,lw_hac_se:235-291; core/quant/gate_stats.py:lw_studentized_boot:297-336; core/quant/gate_stats.py:pw_block_psi,pc3_blocks:342-362; core/quant/gate_stats.py:se_ladder:368-387
- **목적:** 매크로 카드(CARD-O/CARD-P)의 ΔSR = SR(a) − SR(b)에 대한 표준오차, 영가설 중심 부트스트랩 p, 블록 길이 규칙, SE 사다리를 낸다.
- **가정:**
  - 짝지은 일간 초과수익 ≥30개(_pair), 정상성, 4개 적률의 델타법(LW 2008)이다.
  - LRV는 QS 커널·Andrews AR(1) 대역폭(ρ ±0.97 절단), 비양수면 γ0로 대체한다. NW10을 함께 인쇄한다.
  - 부트스트랩: 순환 블록, B 2000, 시드 11, t* = (ΔSR*−ΔSR)/se*, p_lw = #{t* ≥ t_obs}/B, 0이면 '< 1/B'다.
  - 블록 = max(21, ⌈PW(ψ)⌉), 계산 불가면 250(기록). PC-3는 10과 PW 두 다리다.
  - SE_plateau = max(HAC, 블록 10/21/63/126/250 부트스트랩 SE)다.
- **한계:**
  - arch 8.0.0과 1e-9 일치라는 docstring 주장은 스위트에 고정돼 있지 않다(arch는 의존성이 아니고 HEAD 환경에 없다). 테스트는 교과서 AR(1) 상수 15% 이내만 본다.
  - se*는 겹치지 않는 블록 합으로 T mod block 나머지를 버린다. p 해상도는 1/B(0.0005)다.
  - 오늘 실제 데이터로 돈 적이 없다. 매크로 카드는 전부 NOT_RUN(gate.package NOT_FROZEN)이고 R-24 기준값 테스트는 NOT_RUN이다.
- **적용 범위:** 매크로 카드의 짝지은 일간 장부 비교에 쓴다. Strategy Lab 게이트는 이것을 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_stats.py::test_se01_hac_white_noise_and_ar_ladder (T-SE-01; HEAD fa28059 PASS); ::test_lw_boot_null_centred_and_deterministic (T-REPRO-01b; PASS); ::test_block_rule_pw_psi_floor_fallback_pc3 (PASS); ::test_pzero01_count_zero_prints_floor (T-PZERO-01; PASS); tests/macro_m2_costed.py::test_pw_block_ar1_textbook_and_floors, ::test_block_indices_schemes (PASS); tests/macro_m7_stats.py::test_se01_r03_french_refdata (NOT_RUN). financial_calcs.md는 gate_stats 카드 통계를 범위에서 뺐다.
- **관련 오류:** -
- **화면:** -(오늘 화면 출력 없음. Macro → Model cards는 NOT_RUN 사유만 표시, ui/macro_cards_view.py)

#### 41. M2-18 검정력·MDE80·UNDERPOWERED 규칙 (power_line · check_power_block · apply_underpowered)

- **위치:** core/quant/gate_stats.py:STATS,constants:123-154; core/quant/gate_stats.py:power_line:426-461; core/quant/gate_stats.py:check_power_block:464-476; core/quant/gate_stats.py:apply_underpowered:479-488
- **목적:** 모든 매크로 카드에 검정력 줄을 인쇄하고, MDE80 > 0.10이면 실패한 step-5/PC-3 p값을 INSUFFICIENT_DATA(underpowered)로 바꾼다.
- **가정:**
  - 정규 근사: power(D) = Φ(D/se − 1.2816), MDE80 = 2.1232 × SE_plateau, 단측 α 0.10, 검정력 0.80이다.
  - 탐지 연수 = (세션/252)·(2.1232·se/0.05)², se ∝ 1/√T를 가정한다.
  - UNDERPOWERED는 step5_p_value·pc3_p_value에만 적용한다. PC-1', PC-2, PC-3 점 REJECT, step 3는 면제하지 않는다.
  - 검정력 블록이 없는 카드는 거부한다(T-POWER-02).
- **한계:**
  - 정규 근사와 se 축척 가정에 기댄다.
  - 고정 계수(2.1232, 1.2816)는 저장소 리터럴이다.
  - 오늘 실제 카드로 돈 적이 없다. 기준값 테스트 일부 NOT_RUN(test_power01_fixture_ses_refdata, test_g_pwr_01_02_gate_power_goldens_refdata).
- **적용 범위:** 매크로 카드 판정 보조에 쓴다. 전략 게이트(M2-14)에는 없다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_stats.py::test_power01_arithmetic_synth (T-POWER-01, golden; HEAD fa28059 PASS); ::test_power02_power_block_required (T-POWER-02; PASS); ::test_underpow01_scope (T-UNDERPOW-01; PASS); tests/macro_m7_integration.py::test_one_home_psr_underpowered_rule_by_q_and_holm (PASS); tests/macro_m7_stats.py::test_power01_fixture_ses_refdata, tests/macro_m7_integration.py::test_g_pwr_01_02_gate_power_goldens_refdata (NOT_RUN).
- **관련 오류:** -
- **화면:** -(매크로 카드 NOT_RUN)

#### 42. M2-19 카드 목적함수 PBO (gate_stats.pbo_on_claim · pbo_null)

- **위치:** core/quant/gate_stats.py:_sharpe_from_sums,_windows,_es:623-648; core/quant/gate_stats.py:pbo_on_claim:651-724; core/quant/gate_stats.py:pbo_null:727-735; core/quant/cardp.py:line_verdict:764; docs/macro_overlay_study.py:261-267
- **목적:** 카드 자신의 주장(CARD-O: 대조 대비 ΔSR, CARD-P: 21세션 창 ES95 개선)으로 CSCV PBO와 '승자가 진다' 비율을 낸다.
- **가정:**
  - S=16 연속 블록, C(16,8)=12,870 분할이다. 구성 <10이면 'PBO not run'(대체값 없음)이다.
  - 순위 관례는 validate.pbo_cscv와 같다(logit(w) < 0).
  - des95_21 창은 블록 경계를 넘지 않는다. ES = 하위 ⌈5%·n⌉ 평균 손실이다.
  - pbo_on_claim은 값만 낸다. 거부는 cardp.line_verdict:764에서 PBO >0.2이면서 승자 손실 비율 >10%일 때다. 잡음 대조 PBO(pbo_null)를 함께 인쇄한다.
- **한계:**
  - λ<0만 센다(FC-07, validate와 같은 결함, gate_stats.py:723). 구성 수가 홀수일 때 약 1/G 과소다.
  - T ≥ 2S와 짝수 S가 필요하다. 짧은 표본의 des95_21 반쪽은 창이 2개 미만이면 오류다.
  - 오늘 실제 카드로 돈 적이 없다(test_pbo01_kospi_vt_grid_refdata NOT_RUN).
- **적용 범위:** 매크로 카드의 과탐색 진단에 쓴다. 10개 이상 구성 집합(원장 합집합 + PC-6 격자)이 있어야 한다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_stats.py::test_pbo01_noise_control_200_panels_and_objectives (T-PBO-01: QF3 잡음 0.535897 재현, 200패널 평균 0.4998±0.005, validate와 1e-12 일치; HEAD fa28059 PASS, 82.6초); financial_calcs.md FC-07(pypbo 대조, gate_stats.py:723 포함).
- **관련 오류:** financial_calcs/FC-07
- **화면:** -(매크로 카드 NOT_RUN)

#### 43. M2-20 인쇄 전용 다중성·보조 통계 (by_qvalue · holm_adjusted · harvey_liu_haircut · lo_adjusted_sr · psr · dsr_vs_zero)

- **위치:** core/quant/gate_stats.py:by_qvalue:494-512; core/quant/gate_stats.py:holm_adjusted:515-529; core/quant/gate_stats.py:sharpe_z,harvey_liu_haircut:532-550; core/quant/gate_stats.py:lo_adjusted_sr:553-573; core/quant/gate_stats.py:Sharpe,psr,dsr_vs_zero:579-617; core/quant/gate_ledger.py:psr,dsr_vs_zero,psr_vs_s:618-643
- **목적:** 카드에 BY q, Holm, Harvey–Liu 헤어컷, Lo 자기상관 보정 Sharpe, 단위를 선언한 PSR/DSR를 인쇄한다. 판정에는 쓰지 않는다.
- **가정:**
  - BY q = min_{j≥i} p_(j)·m·c(m)/j, Holm 단계 하강이다.
  - Harvey–Liu: 단측 p, Bonferroni M배, 헤어컷 = 1 − max(z_adj,0)/z다.
  - Lo: η(q) = q/√(q + 2Σ(q−k)ρ_k), q=252다.
  - PSR은 일·월 단위를 선언해야 한다. gate_stats.psr은 단위가 다른 Sharpe 객체를 거부하고, gate_ledger.psr은 \|SR\| >0.5/일, >2/월이면 연율 값으로 보고 거부한다.
- **한계:**
  - Harvey–Liu는 Bonferroni만 쓴다(BHY 등 다른 방법 없음).
  - 인쇄만 하므로 판정에 영향이 없다. 화면에 나온 적이 없다.
- **적용 범위:** 매크로 카드 인쇄 줄. 판정 근거로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_stats.py::test_printed_lines_by_hl_lo_and_verdict_class (golden; HEAD fa28059 PASS); ::test_dsr02_units_daily_monthly_and_refusal (T-DSR-02; PASS); tests/macro_m7_ledger.py::test_dsr02_units_daily_monthly_agree_and_annualised_sr_raises (PASS).
- **관련 오류:** -
- **화면:** -(매크로 카드 NOT_RUN)

#### 44. M2-21 유효 시행 수 N_eff (gate_ledger: diff_corr · n_clusters · emax_sim · n_equiv · n_eff)

- **위치:** core/quant/gate_ledger.py:_aligned,diff_corr:421-457; core/quant/gate_ledger.py:mean_offdiag,linear_n_hat:460-470; core/quant/gate_ledger.py:n_clusters:473-483; core/quant/gate_ledger.py:emax_sim:486-502; core/quant/gate_ledger.py:emax_iid_exact,emax_closed,emax_iid:505-531; core/quant/gate_ledger.py:n_equiv:546-557; core/quant/gate_ledger.py:n_eff:574-582
- **목적:** 한 계열 원장의 시행들이 서로 얼마나 겹치는지 보고 디플레이트에 쓸 유효 시행 수를 낸다.
- **가정:**
  - 시행 = 원장 행이다. ROW_SET_KEY(rule, params, estimator, window, cap, instrument_book, rebalance, timing_class, start_convention)의 md5가 같으면 같은 시행이다. 널 분포 실행은 행이 아니다.
  - 상관 = 저장된 차이 시계열의 공통 창 피어슨 상관(≥20 관측)이다.
  - 군집: 평균 연결, 거리 √(½(1−ρ)), ρ ≥0.5에서 절단한다(FILING_RHO).
  - E[max]: Z~N(0, C) 20만 회 고유분해 추출, 시드 11이다.
  - N_equiv = BLdP 닫힌식 e(N)의 역함수(N<2는 정확 적분), 상한 1e6이다. N_eff = max(N_clusters, N_equiv)다. Kish 설계효과는 금지다.
- **한계:**
  - 정규 근사라 차이 시계열의 꼬리·비정상성을 무시한다.
  - 닫힌식 e(N)은 작은 N에서 정확값과 다르다(N=2: 0.520 대 0.564). 그 구간은 2로 처리한다.
  - ρ 0.5 절단은 판단값이다.
  - Strategy Lab DSR은 이것을 쓰지 않는다(K-c). Lab 원장(E1·E2·E3·E5·E8·C3·B3)은 매크로 카드 계열(R-03·R-06·R-28·R-31)과 다른 파일이다. Lab 칩에는 n_raw만 보인다.
  - Lab은 계산 뒤·채점 전에 등록한다(K-d). 로드·계산 실패 실행은 빠지고, 렌더 실패 실행은 들어간다(FC-01).
  - QF3 26시행 실제 행렬 기준값 테스트는 NOT_RUN이다.
- **적용 범위:** 계열 원장의 다중 시행 보정(매크로 step 3, R3 ⑨-3a 병행 산출)에 쓴다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_ledger.py::test_neff01_e_of_n_and_n_equiv_round_trip (T-NEFF-01, golden; HEAD fa28059 PASS); ::test_neff01_synthetic_block_panel_clusters_emax_padding_and_max (PASS); ::test_step3_02_no_ledger_hash_refused_and_no_kish_anywhere (PASS); ::test_neff01_qf3_26_trial_matrix_refdata (NOT_RUN).
- **관련 오류:** K-c, K-d, functional_completeness/FC-01
- **화면:** Strategy Lab 원장 칩 'E1 ledger: N configurations'(n_raw만, ui/strategy_lab_page.py:254-256); Macro → Model cards(NOT_RUN)

#### 45. M2-22 3단계 디플레이트 ΔSR·선택계수 f와 시행 원장 (gate_ledger.step3 · selection_factor · FamilyLedger · repo_anchor)

- **위치:** core/quant/gate_ledger.py:repo_anchor:122-131; core/quant/gate_ledger.py:Anchor:149-162; core/quant/gate_ledger.py:config_id,validate_row:168-214; core/quant/gate_ledger.py:FamilyLedger.verify_chain,append:284-355; core/quant/gate_ledger.py:deflated_dsr,break_even_n:588-603; core/quant/gate_ledger.py:step3_lines:649-671; core/quant/gate_ledger.py:t_fix:688-697; core/quant/gate_ledger.py:selection_factor:700-733; core/quant/gate_ledger.py:step3:748-813; ui/strategy_lab_page.py:register_trials:55-82; docs/macro_overlay_study.py:_anchor_of:209-212
- **목적:** CARD-O 3단계: Φ((ΔSR − SE_null·e(N))/SE_obs) ≥0.95면 통과다. 선택계수 f(1 또는 N_eff), 손익분기 N, z 점검, BY q·Holm을 인쇄한다. 원장은 해시 체인 jsonl로 시행을 남긴다.
- **가정:**
  - SE_null이 없으면 SE_obs를 쓴다. 세 입력은 같은 연율 단위다.
  - f=1은 겹치는 행이 모두 t_fix 이후일 때다. t_fix는 앵커 문자열(git:<40hex> 또는 external:)이 붙은 헤더 created_utc다. 앵커가 없으면 UnanchoredTimestamp로 거부한다. 앵커 커밋이 헤더를 담는지, 커밋 시각이 created_utc 이전인지는 대조하지 않는다(N15).
  - 두 읽기(market_scoped, family_wide) 중 큰 f가 구속한다. CARD-P는 인쇄만 하고, selection_factor 안에서 상관을 못 구하면 f = N_raw다.
  - 원장: 정규 JSON 한 줄, row_md5와 prev_row_md5, 잠금 안에서 config_id 중복이면 추가하지 않는다. span·market은 키가 아니라 같은 설정 재실행은 새 행이 아니다.
  - repo_anchor = .git/HEAD가 가리키는 loose ref 파일의 sha다.
- **한계:**
  - repo_anchor는 packed-refs(git gc 뒤)나 worktree(.git이 파일)에서 UNVERSIONED다(K-g, PA-01, PB-57). 등록은 거부되지 않고 행이 UNVERSIONED로 남는다(validate_row:212). 실제 영향: Lab 행의 앵커가 빠지고 tests/macro_m7_ledger.py:148이 거짓 실패한다. 정식 러너는 --anchor를 명시해 넘기므로(docs/macro_overlay_study.py:209-212, :256) t_fix 기본 경로를 쓰지 않는다. 이 클론은 loose ref라 git:fa280591…를 돌려준다(HEAD fa28059 확인).
  - step3는 loader로 차이 시계열을 try 밖(gate_ledger.py:765)에서 읽는다. 행에 diff_series_ref가 없으면 CARD-P도 f=N_raw 대체 없이 거부된다(docstring과 다름, 실패 폐쇄 쪽, N18).
  - 디플레이트는 정규 근사다.
  - 카드가 동결 전(NOT_FROZEN)이라 실제 데이터로 돈 적이 없다. 기준값 테스트 일부 NOT_RUN(test_step3_01_end_to_end_from_the_matrix_refdata, test_sel01_e_card_run_f_vs_acceptance_report_f_after_freeze).
  - Lab 등록 행의 market은 cost_class를 따르므로 K-f 오분류가 원장에 들어간다. Lab 계열(E1…B3)은 매크로 계열과 다른 파일이라 지금 step3에 들어가지 않는다.
- **적용 범위:** 매크로 CARD-O 판정과 계열 시행 기록에 쓴다. R3에 따라 Lab 판정 기준에는 아직 연결하지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_ledger.py::test_step3_01_inline_numbers_r03_pass_borderline_r04_fail (T-STEP3-01, golden; HEAD fa28059 PASS); ::test_sel01_a_rows_touching_the_span_before_the_commit_give_f_neff, ::test_sel01_b_configuration_fixed_before_any_row_touched_its_span_gives_f_1_only_anchored, ::test_sel01_c_d_declared_factor_refused_both_verdict_inputs_printed_card_o_gated, ::test_sel01_f_g_h_own_rows_excluded_readings_max_and_two_rows (T-SEL-01; PASS); ::test_ledger01_chain_tamper_quick_checks_and_hash_at_run (T-LEDGER-01; PASS); tests/paper_live_acceptance.py::test_17_strategy_lab_registers_real_runs_only, ::test_18_concurrent_registrations_keep_the_ledger_chain (분류표 PASS, 이번에 재실행 안 함: paper_live 실행 금지 규칙).
- **관련 오류:** K-g, PA-01, PB-57, K-c, K-d, K-f; 미등재 신규 N15, N18
- **화면:** Strategy Lab 원장 칩(ui/strategy_lab_page.py:254-256); Macro → Model cards(NOT_RUN)

#### 46. M2-23 R4b 비용 경로 엔진 (costed: earning_weights · costed_path · same_exposure_static · vt_weights · 보조 통계)

- **위치:** core/quant/costed.py:reference_guard:86-95; core/quant/costed.py:earning_weights:121-127; core/quant/costed.py:costed_path:130-160; core/quant/costed.py:same_exposure_static:163-173; core/quant/costed.py:vt_weights:176-197; core/quant/costed.py:max_drawdown,window_return,calendar_years,tail_exposure_ratio,declustered_onsets:207-261
- **목적:** 매크로 카드·엔진 장부가 쓰는 비용 관례로 일간 순손익을 낸다. S(같은 노출 정적 장부)와 연구용 VT 비중도 만든다.
- **가정:**
  - 단순 일간 수익률이다. 종가 t−1까지 정한 비중이 t 수익을 번다.
  - 비용 = 편도율 × \|Δw\| × stress × legs다. 첫 진입은 무료다(strategies.simulate와 반대). 매수후보유와 S는 무비용, L/S 오버레이는 legs=2다.
  - 현금 수익을 더하지 않는다. 입력이 초과수익이라는 전제다(CARD-P는 cash_convention.returns='excess'를 요구, core/quant/cardp.py:844-853).
  - stress <1은 거부한다. 비중 >1이나 cap >1은 reference 모드(tests/reference/, docs/)에서만 계산한다.
  - vt_weights: t까지의 window개 단순수익 표준편차×√252, min(cap, target/σ)다.
  - calendar_years: 126세션 이상인 연도만 복리로 센다.
- **한계:**
  - simulate와 첫 진입 과금 관례가 다르다. 같은 비중 경로도 두 엔진 손익이 첫 진입일에 다르다(정보).
  - R4b 기준값 테스트와 reference 기준값은 데이터가 없어 NOT_RUN이다.
  - 비중 경로 중간 NaN은 거부한다(실패 폐쇄).
- **적용 범위:** 매크로 카드·엔진 장부의 비용 반영 손익에 쓴다. 이 모듈은 acting 경로가 아니다(acting VT는 risk_layer).
- **검증 상태:** 테스트로 확인됨. tests/macro_m2_costed.py::test_cost01_engine_conventions (T-COST-01; HEAD fa28059 PASS); ::test_vt_weights_research_builder, ::test_kr_golden_window_scores_from_2016_01_04_after_a_20_return_warm_up, ::test_reference_mode_refused_from_core_and_tests (PASS); tests/macro_m5_books.py::test_weight_book_ledger_nav_matches_costed_path_and_persists (PASS); tests/macro_m2_costed.py::test_cost01_r4b_goldens_refdata (NOT_RUN).
- **관련 오류:** -
- **화면:** -(직접 없음. core/engine/books.py:643이 같은 관례를 복제한다. 매크로 카드는 NOT_RUN)

#### 47. M2-24 연구 부트스트랩·gate_boot·v1.2-check (costed.research_bootstrap · gate_boot · v12_check)

- **위치:** core/quant/costed.py:research_bootstrap:278-287; core/quant/costed.py:gate_boot:290-298; core/quant/costed.py:v12_check:339-400
- **목적:** 연구용 ΔSR 부트스트랩 비율, PC-3의 P(ΔSR* ≤ −δ), 옛 v1.2 기준 PC-1~PC-7 재현 등급을 낸다. 'v1.2-check, never a verdict'로 표시한다.
- **가정:**
  - 연구 부트스트랩: 짝지은 순환 63일 블록, B 1000, 시드 20261002, 비율 = ΔSR* > 0 비율이다.
  - gate_boot: B 2000, 시드 11, δ 0.10이다. v12_check가 블록 10과 max(10, PW(d), PW(d²)) 두 다리로 부른다. p_ni = max(두 p) × Bonferroni다.
  - v1.2 순서: 충분성 → REJECT → 불확정 → REVISE → PASS다.
- **한계:**
  - 백분위 부트스트랩 비율이다(영가설 중심 아님).
  - 결과는 판정·장부·산출물에 들어가지 않는다(테스트 밖 호출 없음, HEAD grep).
  - reference 기준값 테스트는 NOT_RUN이다.
- **적용 범위:** 연구 비교와 옛 기준 재현에만 쓴다. 카드 판정에 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m2_costed.py::test_research_bootstrap_deterministic_and_share, ::test_gate_boot_margin, ::test_v12_check_verdict_ordering, ::test_v12_statistics_helpers (HEAD fa28059 PASS); ::test_g_kr_06_cap15_reference_refdata 등 reference (NOT_RUN).
- **관련 오류:** -
- **화면:** -

#### 48. M2-25 카드 인쇄 줄 (card_lines: 실행 변형 A/B/C · 야간/장중 기여 · 회전 · 스트레스 비용 · 롤 · 지속성 등)

- **위치:** core/quant/card_lines.py:exec_variants:35-67; core/quant/card_lines.py:overnight_intraday_attribution:70-84; core/quant/card_lines.py:turnover_by_regime:90-108; core/quant/card_lines.py:stress_cost_line:111-124; core/quant/card_lines.py:roll_cost_line,ban_basis_line:127-140; core/quant/card_lines.py:binding_share,persistence_check:146-164; core/quant/card_lines.py:low_exposure_share,rebound_capture:170-187; core/quant/card_lines.py:cost_lines,card_lines:193-223
- **목적:** 매크로 카드에 체결 방식별 Sharpe(1×·2×), 기여 분해, 연도·레짐별 회전, 스트레스 비용, 선물 롤 비용 등을 인쇄한다. 판정에는 쓰지 않는다.
- **가정:**
  - A: 종가 t 체결·t+1부터 수익, B: t+1 시가 체결(야간 갭은 옛 비중), C: t+1 종가 체결(1세션 지연)이다.
  - 스트레스 비용 = 기본 × clip(σ20/누적 중앙값, 1, 5), ETF 종가 체결에서 \|r\| ≥3%면 +10bp다. 기본 아래로 내리지 않는다.
  - 비용은 instruments.cost_per_side(틱 하한 포함)를 쓴다.
  - 지속성 점검(Kaminski–Lo) = 발동 뒤 21세션 수익 평균 대 무조건 평균이다.
- **한계:**
  - 시가가 없으면 B는 None이다. 오늘 시가 공급이 없다.
  - 스트레스 계수는 KIS 스냅샷으로 보정하지 않았다(calibrated_on_kis_snapshots False).
  - 지속성 점검은 유의성 검정이 없고 창이 겹친다.
  - 카드가 돈 적이 없어 화면에 나온 적이 없다. KOSPI VT20 실행 변형 기준값 NOT_RUN.
- **적용 범위:** 매크로 카드 인쇄 전용이다. 판정 근거로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_cards.py::test_book01_printed_lines_of_a_card (T-BOOK-01, T-BOOK-02, T-COST-01; HEAD fa28059 PASS); ::test_step01_header_mechanics_and_binding_share_of_a_synthetic_ladder (PASS); ::test_book02_kospi_vt20_execution_variants_refdata (NOT_RUN).
- **관련 오류:** -
- **화면:** -(매크로 카드 NOT_RUN)

#### 49. M2-27 R-15 시장 간 역변동성 기본 비중 (inverse_vol_weights · ewma_sigma · weekly_returns · ledoit_wolf_line)

- **위치:** core/quant/optimize.py:weekly_returns:145-151; core/quant/optimize.py:ewma_sigma:154-164; core/quant/optimize.py:inverse_vol_from_sigmas:167-179; core/quant/optimize.py:ledoit_wolf_cov,ledoit_wolf_line:186-211; core/quant/optimize.py:inverse_vol_weights:214-251; core/quant/sleeves.py:base_weights:530-546
- **목적:** 매크로 v2 시장별 기본 비중 IV_m = (1/σ_m)/Σ(1/σ_k)를 PIT 종가로 계산한다. LW 156주 줄을 함께 인쇄한다.
- **가정:**
  - 주간 단순수익(ISO 주의 마지막 관측) 위 0평균 EWMA λ 0.97, 첫 26주 표본분산(ddof 1)으로 시드한다.
  - 52주 미만이면 MissingInput으로 실패 폐쇄하고 이전 비중을 이어간다.
  - 상관은 쓰지 않는다(순수 역변동성). 시장별 입력 계열(IV_SERIES)은 판단값(F-14)이다.
- **한계:**
  - 운영 호출이 없다. sleeves.base_weights만 부르고 그것도 테스트 밖 호출이 없다(HEAD grep).
  - 상관을 무시한다. LW 줄은 인쇄만 한다.
- **적용 범위:** 매크로 v2 슬리브 기본 비중(구현 대기)에 쓴다. 오늘 어떤 화면이나 장부에도 들어가지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m4_sleeves.py::test_inverse_vol_weights_kernels_and_pit_path (T-PRIOR-01; HEAD fa28059 PASS).
- **관련 오류:** -
- **화면:** -

#### 50. M2-28 단일 종목 규칙 백테스트 (backtest.run_backtest: ma_cross · momentum · rsi_revert)

- **위치:** core/quant/backtest.py:_rsi_series:61-74; core/quant/backtest.py:_positions:77-104; core/quant/backtest.py:run_backtest:107-155; ui/signals_page.py:(run worker):114-115,136-139,160-170
- **목적:** Signals 화면에서 한 종목의 단순 규칙 성과를 매수후보유와 나란히 보인다.
- **가정:**
  - 포지션 0/1(롱/플랫), 종가 t 결정·t+1 수익이다.
  - 비용 = cost_bps × \|Δpos\|(함수 기본 10, 화면 기본 10)이다. 플랫은 0을 번다(현금 이자 없음).
  - 벤치마크 = 같은 종목 전체 구간 매수후보유, 무비용이다.
  - Sharpe = 평균×252/(σ√252), 무위험 차감 없음, 연수익은 n/252년 기하다. 승률은 청산된 거래별, 비용 전이다.
- **한계:**
  - 표본 내 1회 실행이다. walk-forward·다중검정 보정이 없다('Context only').
  - 가상자산 252(M-03): 합성 BTC에서 ann_vol 0.4724 대 0.5686, Sharpe 0.427 대 0.514, 연수익 9.53% 대 달력 CAGR 14.09%다.
  - 비용 기본 10bp가 시장 비용표(3–50bp)와 다르다(FC-08).
  - 플랫이 0을 벌어 Strategy Lab(현금 3%)과 Sharpe 정의가 다르다.
  - n_trades는 진입·청산을 각각 1회로 센다. 마지막 봉 변경은 셈에 넣지만 과금하지 않는다(N11).
  - inf 가격이 섞이면 결과가 깨진다(D12-01).
- **적용 범위:** 참고용 문맥 표시에만 쓴다. 판정·장부에 넣으면 안 된다(화면 notice가 이를 밝힌다).
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_backtest_costs_only_hurt, ::test_backtest_has_no_lookahead, ::test_backtest_rejects_inverted_ma_params, ::test_backtest_exposure_and_drawdown_sane (HEAD fa28059 로컬 PASS); financial_calcs.md 검증 절 M-03(m03_crypto_annualisation.py).
- **관련 오류:** D12-11 (병합: M-03), functional_completeness/FC-08, D12-01, DF-01; 미등재 신규 N11
- **화면:** Signals 화면 백테스트 칩(strategy %, buy & hold %, Sharpe, max DD, exposure, trades·win)과 곡선(ui/signals_page.py:160-171)

#### 51. M2-29 기술 신호 합성 점수 (signals.compute_signals · sma · ema · rsi · macd)

- **위치:** core/quant/signals.py:sma:46-50; core/quant/signals.py:ema:53-59; core/quant/signals.py:rsi:62-76; core/quant/signals.py:macd:79-83; core/quant/signals.py:compute_signals:90-173; ui/signals_page.py:SIGNALS_NOTICE:28; ui/signals_page.py:(stance chip):70
- **목적:** 지표 6개의 점수(−100~+100)를 가중 평균해 종합 점수와 입장 단어(strong bearish~strong bullish)를 낸다.
- **가정:**
  - 구성: 가격 대 SMA50(괴리%×8, 0.20), SMA200(×5, 0.20), 63세션 ROC(×4, 0.20), RSI14(≥70 −(r−70)×3.3, ≤30 (30−r)×3.3, 중립대 (r−50)×1.2, 0.15), MACD 12/26/9 히스토그램/(가격 0.5%)×100(0.15), (1−σ20/σ100)×120(0.10).
  - 있는 구성만으로 가중치를 다시 정규화한다. 입장 경계 ±15, ±50이다.
  - EMA는 첫 가격으로, RSI는 첫 n개 단순평균으로 시드한다(Wilder).
- **한계:**
  - 척도가 고정 휴리스틱이다. 자산 변동성과 무관해 가상자산은 빨리 포화되고 채권 ETF는 덜 움직인다. 자산 간 입장 비교가 어렵다.
  - RSI 점수가 70과 30에서 불연속이다. RSI 69.9는 +23.9, 70.0은 0이다(signals.py:126-131)(N17).
  - 종합 점수의 예측력을 검증한 적이 없다.
  - 마지막 가격이 inf면 'strong bullish'가 나온다(D12-01).
  - 짧은 이력에서는 구성이 조용히 빠진다.
- **적용 범위:** Signals 화면의 문맥 표시용이다('Context only — not a v2 signal (DO-NOT-BUILD TF-12)'). 판정·장부·주문 근거로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_signals_read_the_trend_direction, ::test_signal_scores_and_weights_are_bounded, ::test_rsi_stays_in_bounds (HEAD fa28059 로컬 PASS); tests/macro_ui_views.py::test_signals_page_header_notice (HEAD PASS). 예측력은 미검증.
- **관련 오류:** D12-01, DF-01; 미등재 신규 N17
- **화면:** Signals 화면 입장 칩과 구성 표, 헤더 notice(ui/signals_page.py:28, :70, :211); qcharts SMA 선

#### 52. M2-30 CARD-P 판정기 (cardp: PC-1'~PC-7 · line_verdict · combine_card_verdict · cardp_evaluate · timing_profile · gate_acceptance_test)

- **위치:** core/quant/cardp.py:GATE_CFG,constants:50-99; core/quant/cardp.py:build_books:163-169; core/quant/cardp.py:es,cdar,tail_ratio:188-227; core/quant/cardp.py:pc1_prime:239-262; core/quant/cardp.py:pc2:265-280; core/quant/cardp.py:_boot_p,pc3_noninferiority:283-318; core/quant/cardp.py:pc5,pc6,pc7:321-356; core/quant/cardp.py:printed_lines:359-387; core/quant/cardp.py:pc4:493-498; core/quant/cardp.py:line_verdict:739-791; core/quant/cardp.py:combine_card_verdict:799-817; core/quant/cardp.py:_check_header,cardp_evaluate:844-926; core/quant/cardp.py:timing_profile,lookahead_positive_control:992-1075; core/quant/cardp.py:gate_acceptance_test:1186-; docs/macro_overlay_study.py:evaluate_card(러너); core/quant/gate_package.py:REASON_ACCEPTANCE/REASON_ANCHOR/REASON_FIXTURES:45-47; core/ficc/macro_artifacts.py:GIT_HASH:33
- **목적:** 매크로 보호형 카드(CARD-P)의 한 판정선에 PC-1'(ES 개선)~PC-7(표본 충분성)과 상한 규칙을 정해진 순서로 적용해 PASS/REVISE/REJECT/INSUFFICIENT_DATA를 낸다. 판정선들은 가장 나쁜 쪽으로 합친다.
- **가정:**
  - 비교 대상 S = 오버레이 끈 장부 × 평균 노출, 무비용이다(costed.same_exposure_static). 입력은 초과수익이다(헤더 cash_convention.returns='excess' 필수).
  - PC-1': ΔES_h = ES_h(S) − ES_h(rule), h = 21·126세션, ES95. p = 정상(stationary) 부트스트랩(평균 블록 250, 짝지은 행)에서 ΔES* ≤ 0 비율이다(비중심 백분위). 통과는 ΔES>0이고 p×f ≤ 0.10이다.
  - PC-2: 오버레이 끈 장부 최악 5% 날의 평균 노출/전체 평균 노출 ≤ 0.90. PC-3: ΔSR ≥ −0.10이고 p_ni = max(p10, p_PW)×f ≤ 0.10(LW 스튜던트화, 영가설 −δ 중심). PC-4: 에피소드 이익 양수 ≥3, 최대 비중 ≤0.5. PC-5: 양수 연도 ≥60%. PC-6: 이웃 ≥50% 유지. PC-7: 이산 ≥30 발동 또는 연속 ≥5 에피소드, 둘 다 ≥882세션.
  - 순서: PC-7 부족 → REJECT(1× PC-1' ΔES≤0, PC-2, PC-3 점, PC-4 양수 <3, step4 PBO >0.2·승자 패배) → INSUFFICIENT(PC-1' p, PC-4 집중, PC-3 p는 MDE80 >0.10이면 underpowered) → REVISE(2× 다리, PC-6, PC-5) → 상한(do_no_harm 등은 낮추기만) → PASS.
  - f = step3 선택계수(≥1)다. f=1과 f=N_eff 판정을 함께 남긴다. 시점 프로파일(R-34), 발동한 look-ahead 양성 대조, 검정력 블록이 없는 카드는 거부한다.
- **한계:**
  - 실제 데이터로 돈 적이 없다. gate.package가 NOT_FROZEN이다. 동결 거부 사유는 세 가지다: 수용 시험 미통과, 앵커 UNVERSIONED(core/ficc/macro_artifacts.py:33의 GIT_HASH 상수), 기준 픽스처 없음(core/quant/gate_package.py:45-47). 판정 필터는 지금 아무 카드도 들이지 않는다(N-06). 수용 시험의 기준 데이터 실행은 NOT_RUN이다.
  - PC-1' p는 영가설 중심화하지 않은 백분위다. PC-3의 LW 스튜던트화와 형식이 다르다.
  - 임계값·블록·수준은 import 시점에 data/macro/rules_v2.0.0.json에서 읽는다(cardp.py:52-53). 파일이 없으면 모듈 import가 실패한다.
  - gjr_null_pct 인쇄 줄은 만들지 않았다(None, cardp.py:910).
  - step3가 CorrUnavailable을 내면 러너가 카드를 거부한다. CARD-P의 f=N_raw 대체에 도달하지 않는 경로가 있다(N18).
  - 비교군 S와 보유 기준선이 무비용이라 규칙 쪽이 비용만큼 불리하다(보수적 방향, 설계 선택).
- **적용 범위:** 매크로 v2 보호형 카드(R-06 KR 등) 판정에만 쓴다. 동결(FROZEN) 뒤 러너(docs/macro_overlay_study.py)에서만 돈다. Strategy Lab 게이트가 아니다. 매크로 영역에 "매크로 카드 게이트 통계, CARD-P 검사, 비용 경로 엔진과 패키지 동결"로 따로 적었던 항목은 M2-17~M2-25와 이 항목에 합쳤다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_cardp.py HEAD fa28059 재실행 13/25 PASS, 12 NOT_RUN: ::test_order_01_verdict_order_and_caps, ::test_i05_synthetic_end_to_end_protective_passes_noise_does_not, ::test_es_01_sign_convention_identical_to_S_rejects, ::test_placebo_01_noise_overlay_family_passes_pc1_rarely, ::test_dnh_01_do_no_harm_cap_only_lowers, ::test_gate_04_second_failure_ends_evaluation_and_every_attempt_is_logged (PASS); ::test_i08_acceptance_test_on_the_frozen_reference_data_refdata, ::test_gate_01_placebo_counts_and_controls_refdata, ::test_epis_02_pc4_on_the_korea_definitive_cell_refdata (NOT_RUN). 동결 거부: tests/macro_m7_cards.py::test_freeze_refuses_with_exactly_the_three_reasons_here, tests/macro_m8_pipeline.py::test_verdict_filter_refuses_unversioned_and_admits_nothing_today (PASS).
- **관련 오류:** 미등재 신규 N18, functional_completeness/FC-07(P3, UNVERSIONED 상수), TA-01(P2)
- **화면:** -(Macro → Model cards는 NOT_RUN 사유만 표시, ui/macro_cards_view.py)

### 6.3 FICC 금리

#### 53. M3-01 FICC 공통 관례 (common.py)

- **위치:** core/ficc/common.py:TRADING_DAYS:7; BP:8; KEY_TENORS:11; UST_TENORS:14-15; FICCError:18-19; parse_tenor:25-39; parse_forward_tenor:42-47; tenor_label:50-62; bp_text:65-67; pct_text:70-71
- **목적:** 모든 금리 모형이 쓰는 단위와 만기 관례다. 만기 문자열을 연 단위 실수로 바꾼다. bp와 키 만기 격자를 정한다. 모형은 아니지만 모든 금리 숫자의 입력이다.
- **가정:**
  - 만기는 연 단위 실수다(ACT/365F 성격). 'd' = n/365, 'w' = n/52, 'm' = n/12, 'y' = n (common.py:36).
  - 달력, 영업일 조정, 결제일, 지급 지연이 없다.
  - 1bp = 1e-4 (common.py:8). 금리는 모두 소수다.
  - 키 만기 격자는 0.25, 1, 2, 3, 5, 7, 10, 20, 30년이다(common.py:11). KRD bump와 시나리오 ramp가 이 격자 위에서 정의된다.
  - UST 격자는 1m~30y 11개(FRED 순서)다(common.py:14-15). TRADING_DAYS = 252.
- **한계:**
  - 3m = 0.25다. 13주 어음은 91/365 = 0.249315다. 2w = 0.038462, 14/365 = 0.038356이다. 윤년을 무시한다(FC-11).
  - 개별 오차는 수 센트, 1bp 미만이다. FC-03(dirty 가격)과 겹치면 커진다.
  - 0 이하 만기는 FICCError다(common.py:29-30, 37-38). 상한은 없다. 큰 만기는 BS-07의 메모리 문제로 이어진다.
- **적용 범위:** 연구용 근사 만기에만 쓴다. 실제 쿠폰일·결제일이 필요한 호가 비교, 정산, 경과이자 계산에는 쓰지 않는다.
- **검증 상태:** 코드로만 확인. financial_calcs.md FC-11(3m·2w 값, 실제 UST 예 −0.046/100). tests에 parse_tenor·parse_forward_tenor·tenor_label 직접 호출 0건(grep). common.py에는 __main__ 자체 검사가 없다. 이 작업 스크래치 c1_curves.py로 HEAD 값 확인: parse_tenor('3m') = 0.25, parse_tenor('2w') = 0.038462.
- **관련 오류:** FC-11 (P3)
- **화면:** Rates 입력(테너 '10y', '5y5y', '18m' 등), Bonds·Rates의 KRD 차트 격자, 모든 bp·% 표시

#### 54. M3-02 YieldCurve 할인·보간·범프

- **위치:** core/ficc/curves.py:coupon_times:41-48; YieldCurve:55-153(__post_init__:64-74, _log_df:77-85, df:87-89, zero:91-95, fwd:97-101, inst_fwd:103-108, annuity:110-112, par_rate:114-116, shifted:119-123, key_rate_shifted:125-140, table:143-153); flat_curve:159-162; 우회 ui/fcharts.py:curve_chart:64-92(par 선을 반기 격자에서만 그려 스텁 톱니를 피함, :71-76)
- **목적:** 연속복리 zero 노드 하나로 할인계수, zero, 단리 선도, 순간 선도, 연금, par 금리를 답한다. 모든 금리 가격기의 할인 기반이다.
- **가정:**
  - zero는 연속복리 소수다.
  - 노드 사이에서 ln DF가 t에 선형이다(구간별 상수 선도). 양 끝 밖은 zero가 평탄하다(curves.py:82-84).
  - 단일 곡선이다. 같은 곡선으로 선도를 투영하고 할인한다.
  - 쿠폰일은 T − k/freq이고 start 이하는 버린다. 짧은 첫 스텁도 연금에서 1/freq 전체 가중을 받는다(curves.py:47-48, 112).
  - fwd는 단리 (DF1/DF2 − 1)/(t2 − t1)이다. inst_fwd는 1e-4년 중심차분이다(t < 1e-4이면 한쪽 차분).
  - shifted는 모든 노드 zero에 같은 bp를 더한다. key_rate_shifted는 인접 키 만기에서 0이 되는 삼각 bump이고 끝 키 밖은 평탄하다. bump 위치에 보간값 노드를 더해도 곡선은 그대로다.
  - 시간은 ACT/365F 실수 연이다.
- **한계:**
  - 스텁 연금 오류(FC-02): 감사 곡선에서 연 1회 스왑 par가 18m −97.2bp, 6m −207.5bp, 2.5y −63.9bp 틀린다. 이 작업 재현(자체 검사 곡선): 3m −382.5bp, 6m −250.0bp, 18m −115.6bp, 2.5y −76.0bp. 정수 테너는 0bp다.
  - 구간별 상수 선도라 3m 선도가 노드에서 최대 73.9bp 뛴다(financial_calcs #13). 선형 zero 보간과 비교하면 15y z-spread가 8.088bp 다르다(bonds 감사 4.6).
  - inst_fwd는 노드에서 좌우 선도의 평균을 낸다.
  - 30y 너머는 zero 평탄 외삽이다.
  - OIS 할인과 SOFR 투영을 나누지 않는다.
  - zero가 유한한지와 만기 오름차순만 검사한다(curves.py:69-72). DF 단조 감소(양의 선도)를 강제하지 않는다.
  - coupon_times가 n = 0을 허용한다. 극소 만기에서 빈 배열이 나와 하류에서 IndexError가 난다(BS-07).
- **적용 범위:** 정수 만기 스왑·채권·캡의 연구용 할인에 쓴다. 비정수 테너 스왑의 연금, 다중 곡선 평가(OIS 할인, 스왑 스프레드)에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 #12·#13(독립 전역해 대비 zero 1.55e-15, DF 3.4e-15); bonds_screen_audit.md 4.6(동시 Newton 대비 zero 2.1e-15, DF 1.4e-14); tests/ficc_acceptance.py::test_curve_df_is_one_at_zero_and_monotone, ::test_curve_bumps_are_local_and_parallel(이 작업 HEAD PASS); core/ficc/curves.py __main__ HEAD ok(run_all 밖, TA-02). 스텁 오류는 이 작업 스크래치 c1_curves.py로 HEAD 재현. 스텁을 잡는 테스트는 없다.
- **관련 오류:** financial_calcs/FC-02 (P1), BS-07, TA-02, TA-07
- **화면:** Rates 곡선 표(Zero, DF, Par, 1y fwd)와 곡선 차트; Rates 스왑·스왑션·캡·시뮬레이션의 할인; Bonds 곡선 의존 카드; Structuring 할인(core/ficc/structured.py가 curve.zero·df·annuity 사용)

#### 55. M3-03 par 곡선 부트스트랩

- **위치:** core/ficc/curves.py:bootstrap_par_curve:165-201; curve_from_snapshot:262-275(method='bootstrap'); 입력 core/ficc/data.py:load_treasury_curve:552-568, _treasury_from_fred:571-596, synthetic_curve_panel:361-377
- **목적:** FRED 미국채 CMT par 수익률(또는 합성 패널)을 연속복리 zero 곡선으로 바꾼다.
- **가정:**
  - 1년 미만은 단리 MM이다. DF = 1/(1 + y·t) (curves.py:182-185).
  - 1년 이상은 반기 par 채권이다. 1 = y/2·Σ DF(t_i) + DF(T) (curves.py:187-197). curve_from_snapshot은 freq를 넘기지 않아 늘 2다.
  - 노드 사이 쿠폰일 DF는 곡선 자체의 log-linear 보간으로 구한다.
  - FRED 퍼센트를 100으로 나눈다. 만기별 결측은 앞값으로 채우고, 그래도 NaN인 행은 버린다(data.py:582-589).
  - CMT를 반기 채권 수익률로 본다.
  - brentq 구간은 zero [−20%, 100%]다(curves.py:193).
- **한계:**
  - CMT는 재무부의 적합값이다. 실제 거래 채권 가격이 아니다.
  - FRED 만기 일부가 빠져도 2y·10y와 6개 이상이면 남은 노드로 곡선을 만든다. 끝은 평탄 외삽이고 출처는 그대로 FRED다(D03-V01: 30y 스왑 par 49bp 낮음).
  - 만기별 관측일이 섞여도 한 날짜로 표시한다(BS-15). 오래된 곡선에도 녹색 칩이 붙는다(BS-14). 범위·단위·급변 검사가 없다(BS-16).
  - 오프라인 합성 패널(days=504, 화면 기본)의 최신 행이 1m 9.586%에서 30y 7.171%로 역전돼 있다(BS-25, 이 작업 HEAD 재확인). docstring은 'level ~4%'라고 한다. 상세는 M3-25.
  - 손상된 캐시의 inf가 패널까지 간다(C01-02). 최신 행의 inf는 bootstrap이 ValueError로 막지만, 과거 행은 PCA·변화량으로 흐른다.
- **적용 범위:** 미국 정부 곡선에만 쓴다. 스왑 곡선, 원화 곡선, 회사채 곡선의 대용으로 쓰지 않는다(FC-05, D03-V02).
- **검증 상태:** 독립 검증됨. financial_calcs.md #12(fsolve 전역해 1.55e-15); bonds_screen_audit.md 4.2 부트스트랩 행(동시 Newton 2.1e-15), 4.6(FRED 앞채움 독립 구현 6.9e-18); tests/ficc_acceptance.py::test_curve_bootstrap_round_trips_par_inputs(par 왕복 1e-8, 희소 격자; 이 작업 HEAD PASS). 실제 FRED 대조는 NOT_RUN(bonds 1.5).
- **관련 오류:** D03-V01 (P1), BS-14, BS-15, BS-16, BS-17, BS-25, BS-34, BS-37, C01-02, financial_calcs/FC-05, TA-02
- **화면:** Rates 곡선 도구(출처·as of 칩), Bonds 전 도구, Structuring, Rates 스왑·옵션·시뮬레이션

#### 56. M3-04 Nelson–Siegel·Svensson 곡선 적합

- **위치:** core/ficc/curves.py:_loading:207-212; nelson_siegel:215-218; svensson:221-225; NSFit:229-233; fit_nelson_siegel:236-259; curve_from_snapshot:262-275(method='nelson_siegel'\|'svensson'); analyze_curve:338(칩용 적합)
- **목적:** par 수익률에 NS(4모수)나 NSS(6모수)를 최소제곱으로 맞춘다. 매끄러운 곡선을 만들고 적합 RMSE를 보인다.
- **가정:**
  - zero가 아니라 par 수익률에 직접 맞춘다.
  - β는 ±0.5, τ는 [0.1, 30] 경계다. 시작점은 하나다(β0 = 장기, β1 = 단기 − 장기, β2 = 0, τ = 2y; NSS β3 = 0, τ2 = 8y).
  - 만기 가중 없는 등가중 잔차다.
  - NS 방법 곡선은 적합 par를 KEY_TENORS ∪ 입력 만기에서 평가한 뒤 다시 부트스트랩한다(curves.py:271-273).
- **한계:**
  - 다중 시작점이 없다. NSS는 τ1 ≈ τ2에서 식별이 약하다. 국소해 여부는 미검증이다.
  - least_squares의 수렴 여부(res.success)를 확인하지 않는다(curves.py:255).
  - par에 맞춘 NS 모수는 zero NS 모수와 다르다.
  - 적합 품질은 합성 데이터로만 시험했다(rmse < 5bp). DNS 카드의 일별 적합 평균 10.4bp는 λ 고정 3요인 적합이라 직접 비교값이 아니다.
  - Bootstrap 방법에서도 칩용 NS 적합이 함께 돈다(curves.py:338). 스프레드 지표는 방법과 무관하게 원 par로 계산된다. 선도 지표(1y1y, 2y1y, 5y5y)는 방법별 곡선을 쓴다.
- **적용 범위:** 곡선 모양 요약과 매끄러운 보간에 쓴다. 개별 채권 rich/cheap 판정의 기준 곡선으로는 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_curve_ns_fit_is_tight(자기 재현 rmse < 1e-6, 합성 패널 < 5bp, NSS 포함), ::test_curve_report_uses_allowed_regime_and_shape_strings(3개 방법); curves.py __main__ HEAD ok. 이 작업 HEAD PASS. 독립 최적화기 대조는 없다.
- **관련 오류:** TA-02, TA-07
- **화면:** Rates 곡선 도구 Method 드롭다운, 칩 'nelson_siegel rmse x bp', 곡선 차트 점선, AI 페이로드 ns.params·rmse

#### 57. M3-05 곡선 요약 지표·모양·국면 분류

- **위치:** core/ficc/curves.py:_par_at:293-297; _shape:300-310; _regime:313-322; analyze_curve:325-358(descriptors :340-350); 재사용 core/ficc/macro.py:_regime_from:170-178; 서술 core/ficc/insights.py:narrate_curve:79-102, narrate_weekly_strategy:429-458; 화면 ui/rates_page.py:_run_curve:103-153, ui/macro_page.py:164(read_row), :142(주간 노트 호출)
- **목적:** 최신 par 곡선의 2s10s, 5s30s, 3m10y, 2s5s10s fly, level, 1y1y, 2y1y, 5y5y, '1y fwd vs 1y'를 계산한다. 모양(normal/flat/inverted/humped)과 lookback 국면(bull/bear steepener/flattener, parallel up/down, unchanged)을 규칙으로 붙인다.
- **가정:**
  - 스프레드는 스냅샷 par의 선형 보간이다. 끝은 고정한다(curves.py:293-297).
  - 1y1y, 2y1y, 5y5y는 곡선의 단리 선도다(curves.py:346-348). '1y fwd vs 1y'는 연 단리 1y1y에서 반기 1y par를 뺀다(:349).
  - 모양 임계: 2s10s > 25bp면 normal, < −10bp면 inverted, 그 사이에서 중간 만기가 2y와 30y보다 10bp 넘게 높으면 humped.
  - 국면 임계 5bp: 기울기 \|Δ\| ≥ 5bp면 10y 방향(10y가 5bp 안이면 2y·10y 평균)으로 bull/bear를 정한다.
  - lookback 기본 20세션, 과거만 쓴다. 패널 길이 − 1로 자른다.
- **한계:**
  - 끝 고정 때문에 20y·30y가 빠지면 '30y'에 마지막 노드 값을 쓴다. 10y로 끝나는 스냅샷에서 5s30s = 10y − 5y다(D03-V01; 이 작업 재현 −31.3bp = 10y−5y).
  - 5y5y를 5년 단리 선도로 계산한다. 반기 par 4% 평탄 곡선에서 4.380%(반기 환산 4.000%, 같은 화면 Swap 도구 5y5y 4.040%), 6%에서 6.878%(+88bp)다. 화면 기본 합성 곡선(days=504)에서는 타일 7.974% 대 반기 환산 6.825%(+115bp), Swap 도구 6.958%다(M3-N06).
  - '1y fwd vs 1y'는 관례가 섞여 4% 평탄 곡선에서 +4.0bp, 6%에서 +9.0bp가 거짓으로 생긴다.
  - 주간 노트의 '5y5y − level' 문장은 화면에 나오지 않는다. Macro 화면은 narrate_weekly_strategy(sheet)를 curve_report 없이 부른다(ui/macro_page.py:142). 테스트에서만 그 문장이 생긴다.
  - 임계값 5·10·25bp는 경험 규칙이다. 보정·검증이 없다. 매크로 쪽은 'descriptive read — not a regime model'로 표시한다(macro.py:43).
  - narrate_curve는 5y5y 정의(단리)를 말하지 않는다(PA-12).
- **적용 범위:** 서술용 요약이다. 예측이나 매매 신호로 쓰지 않는다.
- **검증 상태:** 코드로만 확인. tests/ficc_acceptance.py::test_curve_report_uses_allowed_regime_and_shape_strings는 허용 문자열 소속과 2s10s = par 차이(1e-12)만 본다. 형태 검사라 검증이 아니다. _regime 4사례는 curves.py __main__에만 있다(run_all 밖, TA-02; HEAD ok). 선도 지표 관례를 보는 테스트는 없다. bonds_screen_audit.md 4.4(시나리오 이름이 _regime 정의와 맞음, 코드 확인). 선도 관례 비교는 이 작업 스크래치 c1_curves.py, c8_fwd.py.
- **관련 오류:** D03-V01 (P1), 신규 M3-N06, PA-12, D03-03, TA-02
- **화면:** Rates 곡선 도구 타일(Shape, Regime, 2s10s, 5s30s, 3m10y, 2s5s10s fly, Level, 1y1y, 2y1y, 5y5y, 1y fwd vs 1y), 곡선 차트 제목(ui/fcharts.py:90), 곡선 표 '1y fwd' 열, narrate_curve 해설, AI 페이로드; Macro 화면 국면 행(ui/macro_page.py:164)

#### 58. M3-06 곡선 PCA

- **위치:** core/ficc/curves.py:PCAResult:365-371; curve_pca:374-397
- **목적:** 일별 par 수익률 변화(bp)의 SVD로 수준·기울기·곡률 요인, 적재, 설명력을 낸다.
- **가정:**
  - 변화가 표본 안에서 정상적이다.
  - 표본 전체를 등가중한다. 평균을 뺀다(curves.py:382).
  - 부호 규약: PC1 적재 평균 양수, PC2 장기 끝 양수, 나머지는 최대 적재 양수.
  - 최소 60일. 라벨은 순서로 붙인다. use_changes=False면 수준 PCA다(화면은 변화).
- **한계:**
  - 'level/slope/curvature' 라벨은 형태 검사 없이 순서로 붙는다.
  - 적재는 표본 창에 따라 바뀐다.
  - FRED 만기가 빠지면 만기 집합이 달라진다.
  - FRED 앞채움으로 생긴 0 변화 행이 그대로 들어간다.
  - 독립 구현 대조가 없다.
- **적용 범위:** 기술 통계와 fly 가중치 입력이다. 위험 요인 모형으로 쓰려면 별도 검증이 필요하다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_curve_pca_explains_level_first(PC1 > 50%, 부호, 60일 미만 거부; 이 작업 HEAD PASS); curves.py __main__ HEAD ok; tests/expansion_acceptance.py::selfcheck_curve_models(fly가 PC1·PC2에 1e-10 안에서 중립. 이는 fly 대수 검사다).
- **관련 오류:** TA-02
- **화면:** Rates 곡선 도구 PCA 차트, AI 페이로드 pca_explained, narrate_curve; M3-22 fly 가중치

#### 59. M3-07 채권 가격·수익률·듀레이션·볼록성·DV01

- **위치:** core/ficc/bonds.py:Bond:40-57; cashflows:67-72; _check_ytm:75-77; _pv_terms:80-84; price_from_yield:87-89; yield_from_price:92-99; macaulay_duration:121-123; modified_duration:126-127; convexity:130-134; dv01:137-141; analyze_bond:231-254
- **목적:** 고정 쿠폰 불릿 채권의 가격↔수익률, Macaulay·수정 듀레이션, 볼록성, DV01을 낸다.
- **가정:**
  - street 관례다. freq회 이산 복리, 분수 지수 t·f.
  - 쿠폰일은 만기에서 1/f씩 거꾸로 센다. ACT/365F 실수 연.
  - 결제일과 경과이자가 없다. 그래서 가격은 모든 현금흐름의 PV, 즉 dirty다. docstring의 'clean-ish'(bonds.py:13)는 틀렸다.
  - 면 100당이다. 통화 숫자는 notional/face 배율.
  - DV01 = ModD·P/face·N·1bp, 1차 근사, 롱이면 양수.
  - 수익률 brentq 구간 [−50%, 200%]. 쿠폰 ≥ 0. freq는 int()로 자른다(bonds.py:57).
- **한계:**
  - clean 호가를 Price에 넣으면 수익률이 틀린다: 7y4m +10.6bp, 7.3y +13~+19bp, 실제 UST 예 +11.5bp(FC-03, bonds 4.8). 정수 만기는 경과이자 0이라 영향이 없다. 화면 기본값(10y, Price 빈칸, Yield 4.50)도 영향이 없다.
  - ACT/365F 일정과 정확한 1/f 간격 때문에 street dirty와 −0.046/100(UST 예), −0.037875/100(2034 예) 차이가 난다.
  - DV01은 1차다. QuantLib basisPointValue와 100당 +3.3e-5 차이(½·Cvx·P·1e-8).
  - 만기 상한이 없다(코어 1e7년에서 10.2초·933MB). 극소 만기는 IndexError다(BS-07).
  - 콜·풋, 감채, FRN, 물가연동이 없다.
- **적용 범위:** 쿠폰일 결제이거나 dirty 가격을 넣는 고정금리 불릿 채권에 쓴다. 시장 clean 호가와 실제 결제일 기준 수익률 비교에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #8(QuantLib FixedRateBond: 가격 5.7e-14, Mac·Mod 2.7e-15, 볼록성 4.3e-14), #9, #10; bonds_screen_audit.md 4.2·4.3(Decimal 60자리 독립 구현 5행×6항목 최대 3.2e-12, 640건 2.9e-14, 무이표 1.1e-13); tests/ficc_acceptance.py::test_bond_par_prices_at_100_and_yield_round_trips, ::test_bond_duration_matches_numeric_derivative, ::test_bond_convexity_is_positive_and_numeric, ::test_bond_analyze_requires_exactly_one_of_price_or_yield(이 작업 HEAD PASS); bonds.py __main__ HEAD ok(run_all 밖).
- **관련 오류:** financial_calcs/FC-03 (P2), FC-11, BS-01 (P1, 화면), BS-02, BS-04, BS-05, BS-06, BS-07, BS-19, BS-20, BS-22, BS-23, BS-39, TA-02, TA-07, D03-03
- **화면:** Bonds 계산기 타일(Price, Yield, Macaulay, Modified, Convexity, DV01), 가격-수익률 차트, narrate_bond, AI 페이로드; Rates 시뮬레이션의 재평가 채권(M3-19)

#### 60. M3-08 KRD와 z-spread

- **위치:** core/ficc/bonds.py:price_from_curve:102-105; z_spread:108-115; key_rate_dv01:144-157; core/ficc/curves.py:YieldCurve.key_rate_shifted:125-140
- **목적:** 곡선 위 상수 연속복리 스프레드(z-spread)와 키 만기별 ±1bp 삼각 bump DV01을 낸다.
- **가정:**
  - z-spread는 연속복리이고 곡선 전체에 같은 값을 더한다.
  - KRD는 zero를 움직이고 z-spread를 고정한 중심차분이다.
  - 삼각 bump의 합은 평행 zero 이동이다(끝 키 밖은 평탄).
  - 단일 곡선. 구간 [−50%, 200%].
- **한계:**
  - KRD 합은 zero 평행 DV01이다. 수익률 DV01과의 비율이 1+y/f(예 1.025)인 것은 평탄 곡선에서만이다. 기울어진 곡선에서는 1.022~1.034다(BS-22: 1.0288, 1.0342; 이 작업: 자체 검사 곡선 1.0219, 합성 곡선 1.0281). 화면에 'DV01 836'과 KRD 'total 860'이 설명 없이 같이 나온다.
  - z-spread는 곡선 출처에 따라 바뀐다. 화면 기본 합성 곡선(9.6% 역전)에서 5.5% 10y(y 4.5%)는 −317.75bp, 4.5% 10y(y 4.5%)는 −315.9bp다(bonds 4.2, BS-25).
  - 깊은 음수 수익률에서 z-spread 구간이 먼저 걸린다(BS-07).
- **적용 범위:** 정부 곡선 대비 상대가치 근사에 쓴다. 옵션 조정 스프레드나 신용 분해에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #11(평탄 곡선 비율 1.025000); bonds_screen_audit.md 4.2(z-spread 2.4e-15, KRD 합 대 해석 미분 상대 8e-7); tests/ficc_acceptance.py::test_bond_krd_sums_to_dv01, ::test_bond_z_spread_round_trips, ::test_bond_flat_curve_reprices_the_yield(이 작업 HEAD PASS). 비율 재현은 스크래치 c2_bonds_opts.py.
- **관련 오류:** BS-22, BS-07, BS-25, BS-18(차트 제목 안 보임), BS-35, TA-02
- **화면:** Bonds 계산기 z-spread 타일(툴팁 curve price), KRD 차트('z-spread held'), AI 페이로드 krd·z_spread

#### 61. M3-09 채권 carry·roll-down·breakeven

- **위치:** core/ficc/bonds.py:CarryRoll:161-166; carry_roll:169-208
- **목적:** 곡선이 그대로라는 가정에서 시평(기본 3개월) 보유 손익을 carry와 roll-down으로 나누고, 그 손익을 지우는 수익률 상승폭(breakeven)을 낸다.
- **가정:**
  - carry = 쿠폰 발생 100c·h − 조달 z(h)·P·h. 가격 전액을 곡선 zero로 조달한다(bonds.py:190-191).
  - roll-down = 일정을 h만큼 당긴 노후 채권의 clean 가격 − 가격. 곡선 불변, z-spread 고정.
  - breakeven = total/(ModD·P), 1차 근사. slope ≤ 0이면 0.
  - 연율이 아니다. 100당 시평 손익이다.
- **한계:**
  - 만기 ≤ horizon이면 시평 가치를 face로 둬서 c·100·(1/f − T)만큼 틀린다. 5.5% 0.25년(합성 곡선): total −2.640(정답 −1.265), Breakeven −1062.6bp(BS-08, 이 작업 HEAD 재현).
  - 연속복리 zero를 단리처럼 조달에 쓴다. 자기 수익률 평탄 곡선의 par 채권 total이 0이 아니다: 4.5%에서 +0.0062/100, 5%에서 +0.0077/100(이 작업 재현). 100당 0.0035~0.0304, breakeven 0.4bp 이하(BS-21).
  - CarryRoll.horizon은 요청값인데 계산은 min(h, T)다(bonds.py:189, 208).
  - 가격에서 수익률을 다시 푼다(bonds.py:188).
  - repo 특례나 실제 조달금리를 쓰지 않는다.
- **적용 범위:** 만기가 horizon보다 긴 채권의 근사 보유 손익에 쓴다. 만기 3개월 이하 채권, 실제 repo 손익에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. bonds_screen_audit.md 4.2(carry 3.2e-16, roll 1.6e-12), 4.7(짧은 만기 표, 차이 = c·100·(1/f − T)); tests/ficc_acceptance.py::test_bond_carry_roll_is_a_holding_period_pnl(평탄 곡선 roll < 0.05, breakeven < 2bp, breakeven 재현), ::test_bond_z_spread_round_trips(total = carry + roll); 이 작업 HEAD PASS. 만기 ≤ horizon 구간은 결함(BS-08)이라 검증 범위 밖이다.
- **관련 오류:** BS-08 (P2), BS-21 (P3), BS-41, BS-07, D03-03
- **화면:** Bonds 계산기 Carry(3m)·Roll-down·Carry + roll·Breakeven 타일, narrate_bond, AI 페이로드 carry_roll

#### 62. M3-10 채권 곡선 시나리오

- **위치:** core/ficc/bonds.py:_ramp:269-271; SCENARIO_SHOCKS:274-284; shocked_curve:288-296; scenario_pnl:299-320
- **목적:** 이름 붙은 9개 충격(±25·±100bp 평행, bear/bull steepener·flattener, 2y-5y-10y fly)으로 곡선을 흔들어 전체 재평가 손익을 낸다.
- **가정:**
  - 충격은 연속복리 zero에 bp를 더한다.
  - z-spread는 원래 곡선과 가격으로 한 번 구해 고정한다(bonds.py:313).
  - 순간 충격이다. 시간이 흐르지 않는다.
  - 비평행 충격은 키 만기 값을 곡선 노드에 선형 보간한다(bonds.py:293-295). 노드 사이는 z·t 보간을 따른다.
  - fly = −12.5·KR2 + 25·KR5 − 12.5·KR10이다. 나머지 키(3y, 7y 포함)는 0이라 5y 주변이 3y~7y의 좁은 삼각형이다(bonds.py:283).
- **한계:**
  - '+100bp'는 채권 수익률 +100bp가 아니다. 평탄 곡선에서 수익률로 +102.5~+103.0bp다. YTM·DV01로 검산하면 2.3~2.9% 차이가 난다(BS-09).
  - 충격을 곡선 노드에만 더한다. 20y·30y가 빠진 곡선에서 30년 채권 bear steepener가 −22,369(전체 곡선 −59,696)다(BS-10).
  - fly 정의가 화면에 없고 −12.5를 −12로 보인다(BS-11).
  - P&L %의 분모가 시장가치다(BS-24).
  - 곡선 모양 의존: 같은 가격에서 B +100bp가 NS 모양 400개에서 [−75,331, −74,175]다(bonds 4.4).
  - 확률이 없다. 시나리오일 뿐이다.
- **적용 범위:** 순간 곡선 충격의 손익 감도에 쓴다. 확률적 위험(VaR)으로 읽지 않는다.
- **검증 상태:** 독립 검증됨. bonds_screen_audit.md 4.4(독립 구현 대비 최대 3.7e-9원, 볼록성 비대칭 2차·4차 대조); tests/ficc_acceptance.py::test_bond_scenarios_show_convexity(부호·부등식만; 이 작업 HEAD PASS). 소유자 화면 숫자는 곡선 스냅샷이 없어 미확인. 골든값 테스트가 없다(BS-26).
- **관련 오류:** BS-09 (P2), BS-10 (P2), BS-11 (P2), BS-24, BS-26, D03-V01
- **화면:** Bonds Scenarios(Worst/Best 타일, 시나리오 차트, 표), narrate_bond, AI 페이로드 scenarios

#### 63. M3-11 국채선물 헤지 비율

- **위치:** core/ficc/bonds.py:futures_hedge_ratio:323-329; ui/bonds_page.py:115-118, 191-211
- **목적:** 포지션 DV01 × 전환계수 / CTD DV01로 매도할 선물 계약 수를 낸다.
- **가정:**
  - 선물 DV01 = CTD DV01/CF.
  - CTD가 바뀌지 않는다. 헤지 대상과 CTD 수익률이 같은 bp만큼 움직인다(yield beta 1).
  - 변동이 작다(1차 근사). net basis가 일정하다.
  - CTD DV01은 계약 1개 액면당 통화/bp다. 빈칸이면 CTD 65, CF 1.0이 쓰인다(ui/bonds_page.py:117).
- **한계:**
  - CTD 변경, gross/net basis와 repo, 인도 옵션, invoice price, 변동증거금 tail이 없다.
  - 화면 기본 65와 0.8은 예시값이다. 시장 입력이 아니다. 빈칸 CF는 화면 표시 0.8이 아니라 1.0이 된다(BS-05).
  - 숏 포지션에 'Contracts to sell −9.82'가 나온다(BS-12). 단위 1,000배 오입력을 경고하지 않는다(BS-13).
  - NaN·overflow 방어가 없다(BS-30). 반올림이 half-to-even이다(BS-28).
  - KTB 선물은 현금결제이고 CF가 없어 이 식을 그대로 못 쓴다(BS-33).
- **적용 범위:** UST 선물로 DV01을 맞추는 1차 근사에 쓴다. KTB 선물 헤지, basis 거래에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. bonds_screen_audit.md 4.5(무작위 20,000건 상대 3.3e-16, 화면 9.82·10·−14 재현); tests/ficc_acceptance.py::test_futures_hedge_arithmetic(이 작업 HEAD PASS).
- **관련 오류:** BS-03, BS-05, BS-12, BS-13, BS-27, BS-28, BS-29, BS-30, BS-32, BS-33
- **화면:** Bonds Futures hedge(Position DV01, CTD DV01, Conversion factor, Futures DV01, Contracts to sell, Rounded, 잔여 notice), 해설·AI 페이로드 hedge

#### 64. M3-12 금리스왑 가격기

- **위치:** core/ficc/swaps.py:Swap:53-75; annuity:78-80; par_swap_rate:83-85; _fixed_rate:88-91; swap_pv:94-100; _pinned:103-105; swap_dv01:108-112; swap_krd:115-124; _aged:141-149; analyze_swap:152-176; 화면 ui/rates_page.py:_run_swap:156-197
- **목적:** 현물·선도 시작 IRS의 par 금리, PV, DV01, KRD, 첫 기간 carry, 1년 roll-down, 선도 스왑 격자(1y1y, 2y1y, 5y5y, 10y10y)를 낸다.
- **가정:**
  - 단일 곡선이다. UST CMT 곡선이 투영과 할인을 모두 한다. 변동 다리 = N(DF_s − DF_e).
  - 양 다리 연 1회(freq=1), ACT/365F. 화면은 freq를 바꾸지 못한다.
  - DV01·KRD는 중심 ±1bp 차분이다. 지급 고정 포지션이 양수.
  - carry = (K − 첫 기간 선도)·N/freq는 수취 기준이고 지급은 부호를 뒤집는다(swaps.py:161-165). roll-down = 1년 늙은 스왑 PV − 오늘 PV(중간 쿠폰 제외).
  - 볼록성·타이밍 조정이 없다.
- **한계:**
  - 비정수 테너는 스텁 오류다(FC-02). 18m par가 약 −1%p 틀린다(자체 검사 곡선 −115.6bp). carry_1y도 스텁 대신 1/freq를 쓴다. 18m 지급 스왑 carry 13,777은 0~1y 선도와 1년 기간으로 계산된 값이다(이 작업 재현).
  - 미국채 곡선을 스왑 곡선으로 쓴다. 스왑 스프레드가 빠진다(FC-05, 크기 미검증). 칩은 'curve: FRED'와 '1/yr both legs'뿐이다.
  - SOFR OIS의 ACT/360, 지급 지연, 영업일 조정이 없다(FC-11).
  - 부분 곡선이면 30y 스왑 par가 49bp 낮다(D03-V01).
  - 원화 IRS가 없다(SF-07, functional_completeness/FC-03).
  - Rates 화면 run()에 재진입 가드가 없다(ui/rates_page.py:451-468). 두 번 누르면 앞 작업 결과가 뒤 결과를 덮을 수 있다(P01-05 패턴).
- **적용 범위:** 정수 테너 USD 스왑 형태의 감도와 구조 학습에 쓴다. 시장 SOFR 스왑 호가나 KRW IRS 평가로 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #14(현금흐름 루프 대비 PV 9.3e-10/1천만, par 일치, 정수 만기); tests/ficc_acceptance.py::test_swap_at_par_has_zero_pv_and_payer_dv01_positive, ::test_swap_krd_sums_to_dv01, ::test_swap_off_market_pv_is_minus_spread_times_annuity(이 작업 HEAD PASS); swaps.py __main__ HEAD ok(run_all 밖). 스텁·carry 재현은 스크래치 c1_curves.py.
- **관련 오류:** financial_calcs/FC-02 (P1), D03-V01 (P1), financial_calcs/FC-05 (P2), FC-11, SF-07, functional_completeness/FC-03, D03-03, P01-05, TA-02, TA-07
- **화면:** Rates Swap pricer(Par rate, Fixed, PV, DV01, Annuity, Carry (first period), Roll-down 1y 타일, KRD 차트, Forward swap 표), narrate_swap, AI 페이로드

#### 65. M3-13 Black-76·Bachelier 옵션식과 내재변동성

- **위치:** core/ficc/swaps.py:_ncdf:41-42; _npdf:45-46; _check:193-197; _intrinsic:200-205; black76:208-230; bachelier:233-253; _invert:256-268; implied_black_vol:271-276; implied_normal_vol:279-282; normal_from_black:285-287; black_from_normal:290-292
- **목적:** 선도 위 유럽형 옵션 가격과 그릭스(연금·명목 1당), 내재변동성 역산, 두 모형 사이 vol 환산을 낸다.
- **가정:**
  - Black-76: 로그정규 선도, F > 0, K > 0.
  - Bachelier: 정규 선도, 음수 허용, nvol은 소수(0.008 = 80bp/년).
  - 변동성은 상수다. 스마일이 없다.
  - df 고정. theta = −∂P/∂T(df 고정).
  - 역산은 brentq [1e-4, 5](Black), [1e-6, 0.5](normal). 가격이 내재가치 + 1e-14 이하이거나 상한 vol 가격을 넘으면 FICCError다(swaps.py:261-266).
- **한계:**
  - T·vol² = 0 내재가치 경로에서 d1·d2 부호가 콜·풋 부호로 정해진다. OTM 콜이 +∞, OTM 풋이 −∞다(FC-12, 이 작업 재현). 지금 소비처는 없다.
  - Black은 F ≤ 0이면 ValueError('use bachelier')다(음수 선도 캡에서 재현).
  - 환산이 양방향으로 실패할 수 있다. Bachelier 가격이 Black 상한(vol 5)을 넘으면 실패한다(F 1%, K 0.1%, 10y×10y 수취, nvol 100bp). 깊은 ITM·아주 작은 vol에서는 '내재가치 이하'로 두 모형 모두 실패한다(1y×5y, K 1%, 합성 곡선). 신규 M3-N04.
  - vol은 사용자 입력이다. 시장 표면이 없다(SF-07).
- **적용 범위:** 단일 vol 유럽형 옵션 가격에 쓴다. 스마일이 중요한 OTM 가격, 버뮤단·아메리칸 옵션에는 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #3(역산 왕복 ≤5e-14), #4(QuantLib blackFormula, Hull 선물옵션 예 1.12, 0~6e-14), #5(QuantLib bachelierBlackFormula ≤9e-19); tests/ficc_acceptance.py::test_black_and_bachelier_agree_atm_and_implied_vols_round_trip, ::test_implied_vol_outside_no_arb_raises(이 작업 HEAD PASS). 실패 사례는 스크래치 c2_bonds_opts.py.
- **관련 오류:** FC-12 (P3), 신규 M3-N04, SF-07, TA-07
- **화면:** Rates Swaption/cap-floor(Model 드롭다운, Other-model vol 타일); Derivatives 화면(core/ficc/equity_deriv.py:40, 175, 410, 502와 ui/derivatives_page.py:25, 43이 black76·implied_black_vol 재사용)

#### 66. M3-14 스왑션 가격기

- **위치:** core/ficc/swaps.py:_option:301-304; Swaption:308-319; SwaptionReport:322-337; price_swaption:340-365; atm_straddle:413-420; 화면 ui/rates_page.py:_run_option:200-251
- **목적:** 유럽형 지급·수취 스왑션의 프리미엄, 통화 그릭스, 다른 모형 vol을 낸다.
- **가정:**
  - F = 선도 par 스왑 금리, A = 오늘로 할인한 선도 연금(실물 결제 연금).
  - 프리미엄 = N·A·opt(F, K, T). strike 빈칸이면 ATM = F.
  - Bachelier vega는 normal vol 1bp당, Black vega는 1 vol-pt(0.01)당.
  - theta 1일 = theta/365. 연금의 시간가치는 빠진다.
  - 단일 곡선. freq = 1(화면에서 못 바꿈).
- **한계:**
  - 비정수 테너면 F와 A가 스텁 오류를 받는다(FC-02).
  - 스왑 스프레드가 빠진 미국채 곡선이다(FC-05).
  - 현금결제 연금 관례가 없다.
  - vol은 사용자 입력이다(SF-07).
  - 다른 모형 vol 환산이 실패하면 예외가 그대로 올라가 프리미엄까지 오류 notice로 끝난다(swaps.py:353-359, M3-N04).
  - atm_straddle은 화면에서 부르지 않는다(grep: 테스트와 자체 검사뿐).
- **적용 범위:** 정수 테너 유럽형 스왑션의 구조 학습에 쓴다. 시장 호가 대체로 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #15(ATM 닫힌식 N·A·σ√T/√(2π)와 QuantLib, 차이 0); tests/ficc_acceptance.py::test_swaption_put_call_parity, ::test_atm_straddle_is_twice_the_atm_payer, ::test_black_and_bachelier_agree_atm_and_implied_vols_round_trip(이 작업 HEAD PASS).
- **관련 오류:** financial_calcs/FC-02, financial_calcs/FC-05, SF-07, 신규 M3-N04, D03-03, TA-02
- **화면:** Rates Swaption(Forward, Strike (ATM), Premium 통화·bp, Delta, Gamma, Vega, Theta (1d), Other-model vol 타일, annuity 칩), narrate_swaption, AI 페이로드

#### 67. M3-15 캡·플로어 가격기

- **위치:** core/ficc/swaps.py:CapFloorReport:369-379; price_cap_floor:382-410; 화면 ui/rates_page.py:_run_option:253-284
- **목적:** 캡렛(플로어렛) 합으로 캡·플로어 프리미엄과 캡렛 표를 낸다.
- **가정:**
  - 캡렛 = N·τ·DF(t_end)·opt(fwd, K, t_start). fwd는 단리 선도. τ는 실제 기간(t1 − t0)이라 캡렛 자체는 스텁을 맞게 다룬다.
  - 현물 시작 캡의 첫 캡렛(t_start = 0)은 이미 고정이라 뺀다.
  - ATM = [start, start + tenor] 전체 분기 par 스왑 금리.
  - freq = 4. 볼록성 조정 없음. 캡렛 전체에 같은 vol. 화면은 start를 넘기지 않아 늘 현물 시작이다.
- **한계:**
  - 'ATM'이 빠진 첫 캡렛 기간을 포함한다(M-04). 1y 분기 캡의 'ATM'에서 cap − floor가 상승 곡선 +451, 앞단 역전 곡선 −1,054다(1백만당; 이 작업 재현 +450.7, −1,053.8).
  - 만기가 1/freq 이하인 현물 캡(예 3m)은 캡렛이 0개다. 프리미엄 0, 'ATM' 5.10%가 오류 없이 나온다(이 작업 재현, 신규 M3-N07). M-04 수정안은 이 경우 FICCError를 낸다.
  - 비정수 테너 ATM은 스텁 오류다. 1.6y 3.4276% 대 3.7591%(FC-02).
  - Black 모형은 음수 선도에서 ValueError다.
  - 스왑 스프레드가 빠진 곡선이다(FC-05).
- **적용 범위:** 정수 연 테너 분기 캡의 구조 학습에 쓴다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #16(캡렛별 QuantLib blackFormula 합, 차이 0); financial_calcs.md 검증 절 M-04(m04_cap_atm.py); tests/ficc_acceptance.py::test_cap_is_sum_of_caplets_and_cap_minus_floor_is_the_swap(현 ATM 정의를 고정한다: tests/ficc_acceptance.py:361; 이 작업 HEAD PASS). M-04·3m 캡 재현은 스크래치 c2_bonds_opts.py.
- **관련 오류:** M-04 (P3), 신규 M3-N07, financial_calcs/FC-02, financial_calcs/FC-05, SF-07, D03-03
- **화면:** Rates Cap/Floor(Strike (ATM), ATM (par swap), Premium, Caplets, Dearest caplet 타일, 캡렛 차트·표), narrate_cap_floor, AI 페이로드

#### 68. M3-16 단기금리 모형 보정 (Vasicek·CIR·Hull–White)

- **위치:** core/ficc/ratesim.py:ShortRateParams:58-64; calibrate:106-155; 입력 core/ficc/data.py:load_short_rate:645-671, _SHORT_RATE_IDS:621-632; 화면 ui/rates_page.py:_run_sim:287-354
- **목적:** 단기금리 이력에서 κ, θ, σ, r0를 이산화 SDE의 OLS 한 번으로 추정한다.
- **가정:**
  - Euler 이산화 OLS다. κ = −b/dt.
  - Vasicek·HW: Δr = a + b·r + ε, 정규·등분산 잔차.
  - CIR: Δr/√r를 1/√r와 √r에 회귀한다(절편 없음). r는 1e-6 하한. θ ≤ 0이면 표본평균으로 바꾼다.
  - dt는 1/252다. note에 'monthly'가 있으면 1/12.
  - κ < 0.01이면 0.01로 막고 θ = 표본평균.
  - 물리측도 추정치를 위험중립 닫힌식에 그대로 쓴다(위험 시장가격 0).
  - USD는 FRED SOFR(없으면 DFF), 기본 756세션. NaN은 지우고 간격을 무시한 채 차분한다(ratesim.py:114, 121).
  - HW의 θ는 회귀 평균이다. 시뮬레이션은 쓰지 않는다.
- **한계:**
  - 3년 일별 OLS는 κ를 크게 과대추정한다(M3-N03). 앱의 오프라인 합성 SOFR은 참 κ 0.8, θ 3.5%, σ 0.7%인 OU인데 κ 4.193(반감기 0.17y, 참값 0.87y)이 나온다. 참 κ 0.8 OU 400개(756일)의 κ 중앙값은 2.23이다. 평균회귀가 없는 랜덤워크 400개에서 κ 중앙값 1.30(반감기 0.53y), 하한 걸림 4.8%, θ 5~95% 범위 2.05%~6.70%다(이전 작업 200개: 1.54, 4.5%, 1.5%~8.0%).
  - 고정 금리 주변 잡음도 평균회귀로 읽힌다(이전 작업: 계단형 정책금리 + 일 4bp 잡음에서 κ 1.67).
  - CIR θ = a/(κ·dt)는 κ가 작으면 폭주한다. 랜덤워크 예: κ 0.061에서 θ 14.97%(표본평균 4.58%), κ 0.045에서 θ 17.42%(이 작업 재현).
  - SOFR의 정책 계단과 분기말 급등은 정규 확산과 다르다.
  - 표준오차·신뢰구간을 보이지 않는다.
  - 감사도 보정 품질을 검증하지 않았다(financial_calcs.md:527).
- **적용 범위:** 시뮬레이션 데모 입력으로만 쓴다. 금리 전망이나 정책 경로 예측으로 쓰지 않는다.
- **검증 상태:** 코드로만 확인. tests/ficc_acceptance.py::test_ratesim_is_seeded_and_reproducible(κ ≥ 0.01, σ > 0만 본다), ::test_ratesim_vasicek_reverts_to_theta(추정 모수의 자기 일관성; 추정 정확도는 보지 않는다). 둘 다 이 작업 HEAD PASS지만 보정 검증이 아니다. ratesim.py __main__ HEAD ok. financial_calcs.md:527 '보정 품질 미검증'. 편향 측정은 이 작업 스크래치 c3_ratesim.py, c4_kappa.py, c7_fan.py.
- **관련 오류:** 신규 M3-N03, 신규 M3-N05(CIR θ 폭주로 연결, 원 정의 확인 필요), TA-02, TA-07
- **화면:** Rates Rate simulation 타일(kappa, Half-life, theta, sigma, r0)과 출처 칩, narrate_ratesim, AI 페이로드 params; M3-20 SEP 밴드의 기반 모수

#### 69. M3-17 단기금리 닫힌식 할인채와 모형 곡선

- **위치:** core/ficc/ratesim.py:_zcb_ab:161-185; zcb_price:188-194; _model_curve:197-203
- **목적:** Vasicek·CIR 아핀 할인채와 곡선에 맞춘 Hull–White 할인채를 낸다. 시평의 모형 zero 곡선(KEY_TENORS 9점)을 만든다.
- **가정:**
  - Vasicek·CIR은 보정 모수를 그대로 쓴다(위험 시장가격 0).
  - HW는 P(0,·)와 f(0,t) = curve.inst_fwd를 써서 t = 0에서 곡선을 재현한다. 곡선이 없으면 r0 평탄.
  - 모형 곡선은 KEY_TENORS 9점이고 그 사이는 log-linear 보간이다.
- **한계:**
  - Vasicek·CIR 곡선은 시장 곡선과 맞지 않는다. 화면 기본 합성 곡선(days=504)에서 10y 시장 zero 7.50% 대 Vasicek 3.60%(389bp)다. 자체 검사 곡선(days=60)에서는 4.16% 대 3.60%다. 이 차이가 M3-19 손실에 섞인다(M3-N01).
  - 기간 프리미엄이 없다.
  - inst_fwd는 노드에서 좌우 선도 평균이다.
  - κ가 작으면 CIR 장기 zero가 θ 쪽으로 커진다. 랜덤워크 예: κ 0.061, r0 5.90%에서 10y 8.09%, 30y 10.36%(이 작업 재현, M3-N05).
- **적용 범위:** 모형 내부 일관성 확인에 쓴다. Vasicek·CIR 곡선을 시장 가격 곡선으로 쓰지 않는다.
- **검증 상태:** 독립 검증됨. financial_calcs.md #17(QuantLib Vasicek, CoxIngersollRoss, HullWhite discountBond 9사례 ≤6.5e-12); tests/ficc_acceptance.py::test_ratesim_hull_white_matches_the_curve_at_t0(곡선 재현 1e-6; 이 작업 HEAD PASS); ratesim.py __main__(Vasicek ZCB = 모형 곡선 1e-12, HEAD ok). 수준 차이는 스크래치 c3_ratesim.py.
- **관련 오류:** 신규 M3-N01, 신규 M3-N05, TA-02
- **화면:** Rates Rate simulation 'Model zero at {h}y (median path)' 표, narrate_ratesim 곡선 문장, AI 페이로드 model_curve_at_horizon

#### 70. M3-18 단기금리 경로 시뮬레이션

- **위치:** core/ficc/ratesim.py:RateSimResult:68-82; _hw_drift:209-215; simulate:218-275; 화면 ui/rates_page.py:_run_sim:287-354
- **목적:** Euler 경로로 단기금리 팬(5/25/50/75/95), 평균, 90% 범위, 임계 초과 확률을 낸다.
- **가정:**
  - Euler, 기본 252단계/년. 정규 충격.
  - CIR은 full truncation이고 max(r, 0)을 보고한다.
  - HW: θ(t)를 곡선에 맞추고 f′ 항을 단계마다 정확히 적분한다. r0를 곡선 f(0,0)으로 바꾼다(ratesim.py:236-239).
  - 시드 7 고정(simulate 기본값, UI 칩 'seed 7'). 경로 수 100~100,000.
  - 물리측도 모수. 점프·정책 계단 없음. P(> 임계)는 종단값만 본다.
- **한계:**
  - 팬과 P(> 임계)는 보정의 κ·θ를 그대로 따른다. κ가 과대추정되면 팬이 좁아진다. 합성 SOFR에서 1y 90% 범위 폭은 추정 모수 80bp, 참 모수 161bp다(이 작업 재현, M3-N03).
  - HW는 r0를 곡선 f(0,0)으로 바꾼다. 화면 기본 합성 곡선에서는 SOFR 3.64%가 9.55%로 바뀐다. note에만 적힌다.
  - HW 실행에서도 'theta' 타일은 시뮬레이션이 쓰지 않는 회귀 평균(3.60%)을 보인다. 같은 화면의 r0는 9.55%, 1y 평균은 8.96%다(ui/rates_page.py:315, 신규 M3-N09).
  - Vasicek은 음수 금리를 허용한다.
  - MC 오차를 보이지 않는다.
- **적용 범위:** 모형 가정의 결과 예시로만 쓴다. 정책금리 확률(FOMC 시장 내재 확률)로 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_ratesim_is_seeded_and_reproducible(시드 재현, 팬 순서), ::test_ratesim_vasicek_reverts_to_theta(30y 평균이 θ의 10% 안), ::test_ratesim_cir_stays_non_negative, ::test_ratesim_hull_white_matches_the_curve_at_t0(이 작업 HEAD PASS). HW 평균 E[r(h)] = f(0,h) + σ²/(2κ²)(1 − e^{−κh})² 검사(오차 3e-4)는 ratesim.py __main__에만 있다(run_all 밖, TA-02; HEAD ok). financial_calcs.md:527: HW 평균의 곡선 재현은 감사 미검증.
- **관련 오류:** 신규 M3-N03, 신규 M3-N05, 신규 M3-N09, BS-25(합성 곡선), D03-03, TA-02
- **화면:** Rates Rate simulation(Mean at h, 90% range, P(> x) 타일, 팬 차트, 칩 paths·seed 7), narrate_ratesim, AI 페이로드

#### 71. M3-19 시평 재평가 VaR·CVaR

- **위치:** core/ficc/ratesim.py:HorizonPV:86-93; _bond_value:326-334; _swap_value:337-341; horizon_pv_distribution:344-387; 화면 ui/rates_page.py:300-308, 329-337
- **목적:** 시뮬레이션 시평에서 채권이나 지급 스왑을 경로별 모형 곡선으로 재평가해 PV 분포, VaR95, CVaR95를 낸다.
- **가정:**
  - 손실 기준은 오늘 시장 곡선 PV다(곡선이 없으면 r0 평탄).
  - 시평 PV는 종단 단기금리 하나로 만든 모형 곡선(KEY_TENORS 9점)으로 계산한다.
  - 최대 500경로를 균등 추출한다.
  - 시평 전 쿠폰은 액면 그대로 더한다(재투자 없음). 스왑의 시평 전 픽싱은 무시한다(변동 다리 par 가정).
  - VaR95 = 손실 95분위, CVaR95 = 그 이상 평균. 오늘 K는 YieldCurve.par_rate(FC-02 공유).
  - 모형 모수는 sim.params에서 읽는다. 함수의 params 인자는 쓰지 않는다(ratesim.py:344, 376-377).
- **한계:**
  - Vasicek·CIR에서는 모형 곡선과 시장 곡선의 수준 차이가 손실로 섞인다(M3-N01). 화면 기본 합성 설정(Vasicek, 10y 지급 스왑)에서 1일 시평에 이미 평균 PV −356,742, 1년 VaR95 327,793(1백만당)이다. 같은 조건 HW는 19,034다. 4% 10y 채권은 1일 시평 평균 PV 1,030,305 대 오늘 741,598이고, 화면은 'VaR 95 (loss) 0'을 보인다(이 작업 HEAD 재현).
  - params 인자가 무시된다. 다른 모수를 넘겨도 결과가 같다(신규 M3-N08).
  - 500경로라 VaR95 상대 표준오차가 약 6%다(정규 근사 계산). CVaR95는 꼬리 25점 평균이다.
  - 재투자와 픽싱을 근사한다.
  - 손익에 쿠폰(carry)이 섞인다. 순수 위험 지표가 아니다.
- **적용 범위:** HW 모형의 개념적 시평 손익 분포에만 쓴다. Vasicek·CIR 결과를 위험 한도나 VaR 보고에 쓰지 않는다.
- **검증 상태:** 코드로만 확인. tests/ficc_acceptance.py::test_horizon_pv_var_is_a_non_negative_loss는 유한, 비음수, 순서만 본다(형태 검사라 검증이 아니다; 이 작업 HEAD PASS). ratesim.py __main__도 같은 형태 검사다. 수준 정확성 검사는 없다. 편향은 이 작업 스크래치 c3_ratesim.py로 HEAD 재현.
- **관련 오류:** 신규 M3-N01, 신규 M3-N08, financial_calcs/FC-02(ratesim.py:340, 370), D03-03, TA-02
- **화면:** Rates Rate simulation에서 Revalue = Bond/Payer swap일 때 Revalued, Mean PV, 90% range, VaR 95 (loss), CVaR 95 타일과 히스토그램, narrate_ratesim, AI 페이로드 horizon_pv

#### 72. M3-20 SEP 오차대 금리 경로

- **위치:** core/ficc/ratesim.py:SEP_RMSE_COVERAGE:281; _terminal_var_per_sigma2:284-290; sep_band_params:293-311; sep_band_paths:314-320; 사용 core/quant/scenarios.py:SEP_VINTAGE:37, Scenario 'sep_rate_band':124-127, _rate_band:256-277
- **목적:** FOMC SEP Table 2의 단기금리 RMSE 밴드(±1.4pp, 1년)를 보정 모형의 σ로 바꿔 시드 고정 금리 경로를 낸다(R-16 rule (4)(e), TASK-M9-03).
- **가정:**
  - 밴드는 약 70% 범위의 RMSE 밴드다(brief F-18 해석).
  - 종단 sd = band/Φ⁻¹(0.85). κ·θ·r0는 유지하고 σ만 푼다.
  - CIR은 정확한 조건부 분산을 쓴다. Vasicek·HW는 OU 분산.
  - 팬 중심은 모형 드리프트다. SEP 중앙값이 아니다.
  - FEDFUNDS로 보정한다(관측 간격 중앙값 ≥ 28일이면 dt = 1/12). HW는 곡선 없이 r0 평탄으로 돈다(scenarios.py:270).
- **한계:**
  - 빈티지가 2023-12-13(Dec-2023 SEP)이고 stale로 표시된다. 최신 SEP 표는 소유자 입력 대기다.
  - κ 편향(M3-N03)이 경로 모양에 들어간다. σ는 밴드에 맞추므로 종단 폭은 보존된다.
  - 장부를 평가하지 않는다. 금리 경로만 낸다.
- **적용 범위:** 시나리오 라이브러리의 금리 경로 불확실성에만 쓴다. 가격 모형이나 포지션 크기 결정에 쓰지 않는다(I-11, acts = False).
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_scenarios.py::test_sep_band_dispersion_matches_the_band_at_the_horizon(I-11: 3개 모형 종단 sd 허용 3~5%, ±1.4pp 내 70% ±2%; 이 작업 HEAD PASS), ::test_t_repro_01c_scenarios_identical_paths_under_the_seed(T-REPRO-01c, I-11), ::test_i11_no_sizing_module_reads_scenarios_or_lab(I-11). ::test_scenario_latest_sep_table_owner는 NotRun을 낸다(소유자 입력 대기, 이 작업 확인). 검증 근거가 아니다.
- **관련 오류:** 신규 M3-N03(κ 편향 경유)
- **화면:** - (화면 호출 없음. core/quant/scenarios.py와 테스트에서만 쓴다. ui/ grep 0건)

#### 73. M3-21 Diebold–Li 동적 NS 예측 연구

- **위치:** core/ficc/curve_models.py:dns_loadings:42-45; dns_factors:48-55; _month_ends:58-64; DNSStudy:68-82; dns_study:85-133; 실행 docs/asset_expansion_study.py:run_dns:449-475
- **목적:** λ 고정 NS 요인 3개의 직접 h단계 AR(1)로 6·12개월 뒤 곡선을 재귀 표본외 예측한다. 랜덤워크와 만기별 RMSE·Diebold–Mariano로 비교한다. 카드 M_B1_dns를 만든다.
- **가정:**
  - λ = 0.0609/월(0.7308/년) 고정.
  - 일별 OLS 요인을 월말에서 뽑는다. 마지막 관측일도 월말로 넣는다(curve_models.py:63).
  - 요인별 독립 AR(1), 직접 h단계 회귀. 첫 예측 120개월째. 각 원점은 그 시점까지 자료만 쓴다.
  - DM: 제곱오차 차이의 Newey–West t, 시차 h − 1. 유의는 t < −1.96이다.
  - FRED CMT par 수익률을 쓴다(Diebold–Li 원문은 zero 수익률).
  - 요인 과정이 정상적이다.
- **한계:**
  - par 수익률 적합이라 원 논문과 다르다. 일 적합 RMSE 평균 10.4bp.
  - 12개월 예측 171개 원점이 겹친다.
  - 실데이터 결과는 REJECT다. 1/2/5/10/30y 5개 만기 중 0개에서 RW를 이겼고 DM t 최소값은 0.589다(2001-07-31~2026-09-24, 303개월).
  - 마지막 관측일 2026-09-24가 월말 표본으로 들어간다.
  - 게이트(4/5 만기 승, 3/5 유의)는 run_dns 코드에 고정된 규칙이다(asset_expansion_study.py:456-459).
- **적용 범위:** 연구 기록이다. 금리 예측 신호로 쓰지 않는다(REJECT).
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_curve_models(합성 NS 패널: 요인 복원, 12개월 6개 이상 만기에서 RW 이김, γ < 1; 이 작업 HEAD에서 curve_models.py __main__ ok); financial_calcs.md #18(곡률 적재 최대점 29.44개월 ≈ 30개월); 카드 docs/asset_expansion/cards/M_B1_dns.json(REJECT, 0/5, 0/5, 이 작업 확인).
- **관련 오류:** K-a(requirements.txt는 6054b33에서 해결, pyproject.toml에는 아직 없음), TA-03
- **화면:** Strategy Lab 카드 표와 카드 상세(M_B1_dns — REJECT), docs/asset_expansion/results.md

#### 74. M3-22 PCA 중립 2-5-10 버터플라이 신호

- **위치:** core/ficc/curve_models.py:butterfly_weights:139-148; fly_series:151-153; FlySignal:157-167; butterfly_signal:170-215; core/quant/strategies.py:half_life:255-263, adf_pvalue:266-271; 실행 docs/asset_expansion_study.py:run_fly:478-497
- **목적:** 롤링 PCA로 수준·기울기에 중립인 (w2, 1, w10) fly를 만들고, z-score 평균회귀 규칙의 거래 통계를 낸다. 카드 S_B2_pca_fly를 만든다.
- **가정:**
  - 250일 창 PCA를 21세션마다 다시 추정한다. 창은 t를 빼서 인과적이다.
  - fly = 수익률 가중합(bp)이다. DV01 가중이 아니다.
  - z 창 250(t 제외), 진입 \|z\| > 2, 청산 z = 0 또는 60세션.
  - 손익 = 포지션 × −Δfly(bp).
  - run_fly는 cost_bp = 1.0을 '다리당 왕복'이라 적지만 게이트는 거래당 평균 > 2 × cost(2bp)로 본다. 세 다리면 3bp 이상이 맞다(asset_expansion_study.py:483-484).
  - ADF와 반감기는 전체 표본 fly 수준으로 계산한다(거래 규칙 자체는 인과적).
- **한계:**
  - 가중치를 21세션마다 바꿀 때 fly 수준이 뛴다. 자체 검사 25년 합성 패널에서 재가중 288회의 점프 중앙값 9.62bp(최대 68.10bp), 같은 가중치 일 변화 중앙값 1.24bp다(이 작업 재현; 이전 작업 60회 9.36bp·최대 34.80bp). 이 점프가 z, 일 손익, 진입가 대비 손익, ADF·반감기에 섞인다(M3-N02).
  - 손익이 bp 단위 수익률 조합이다. 통화 손익이 아니다.
  - adf_pvalue는 어떤 예외든 삼키고 NaN을 낸다. 판정식에서 NaN은 반감기가 120 미만이면 REVISE로 흐른다(TA-03).
  - 실데이터 카드: 38회, 적중 39%, 거래당 −3.8bp, ADF p 0.008, 반감기 104세션 → REVISE.
- **적용 범위:** 연구 카드다. 매매 신호로 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_curve_models(PC1·PC2 중립 1e-10, 합성에서 거래 > 5, ADF < 0.05; HEAD ok); 카드 docs/asset_expansion/cards/S_B2_pca_fly.json(REVISE, 이 작업 확인). statsmodels 0.15.0 설치 환경. 점프 측정은 스크래치 c5_fly.py.
- **관련 오류:** 신규 M3-N02, K-a(requirements.txt 해결, pyproject.toml 미선언), TA-03, functional_completeness/FC-02, functional_completeness/FC-05
- **화면:** Strategy Lab 카드(S_B2_pca_fly — REVISE). Rates 화면에는 없다(functional_completeness/FC-05)

#### 75. M3-23 Koijen 채권 캐리와 캐리 타이밍 (미사용)

- **위치:** core/ficc/curve_models.py:bond_carry:221-224; carry_timing_positions:227-236
- **목적:** KMPV(2018) 식 (15) 캐리 = (y_T − r_short) + D_mod·(y_T − y_{T−h})와, 캐리가 과거 평균보다 크면 롱인 타이밍 규칙이다.
- **가정:**
  - 연율 소수.
  - D_mod는 상수 입력이다.
  - 월 샘플은 step = 21세션, 창은 window개 월 표본(기본 60), 이력 최소 12개.
  - t의 캐리로 t부터 step세션 포지션을 정한다.
- **한계:**
  - 저장소에 호출처가 없다(grep). 결과가 어디에도 나오지 않는다.
  - D_mod 상수와 roll-down 근사.
  - 식 번호와 정의는 원문과 대조하지 않았다.
- **적용 범위:** 미사용 코드다. 쓰려면 검증과 카드가 먼저 있어야 한다.
- **검증 상태:** 코드로만 확인. tests/expansion_acceptance.py::selfcheck_curve_models는 같은 식을 숫자로 다시 계산하는 항등식과 포지션 ∈ {0, 1}, 평균 0.2~0.8만 본다. 외부 기준값이 없다.
- **관련 오류:** -
- **화면:** -

#### 76. M3-24 KRW 곡선 패널 (미연결)

- **위치:** core/ficc/curve_models.py:krw_curve_panel:242-257; data/kis_markets.py:KRW_CURVE_TENORS:62-63, krw_yield_daily:492
- **목적:** KIS 차트로 CD 91일 + 국고 1/3/5/10/20/30년 par 수익률 패널을 만든다.
- **가정:**
  - 공통 날짜 교집합만 쓴다. 최소 30일.
  - 퍼센트를 100으로 나눈다.
  - CD 91일(Y0112)을 0.25년 노드로 쓴다.
- **한계:**
  - 호출처가 0건이다(SF-01, grep).
  - CD는 은행 신용 금리다. 연결하면 할인계수, 선도, 캐리가 CD 신용 스프레드만큼 틀린다(SF-01: 통안+30bp 가정에서 3m zero +29.8bp).
  - 2y 노드가 없다. 2s10s는 보간값이 되고, 2-5-10 fly(M3-22)는 list.index에서 실패한다.
  - KIS 실제 응답과 수익률 관례는 미검증이다.
- **적용 범위:** 미연결이다. 연결 전에 SF-01 수정과 KIS 실응답 확인이 필요하다.
- **검증 상태:** 코드로만 확인. krw_curve_panel 테스트 없음(grep). krw_yield_daily는 가짜 전송으로 쪽 넘김·형태만 본다(tests/expansion_acceptance.py::test_kis_markets_paging_and_shapes, :108). suppliers_ficc_btc.md SF-01, functional_completeness.md FC-03의 제안만 있다.
- **관련 오류:** SF-01 (P3), functional_completeness/FC-03 (P2), D03-V02 (P2)
- **화면:** -

#### 77. M3-25 오프라인 합성 금리 데이터 (합성 국채 곡선 패널·합성 단기금리)

- **위치:** core/ficc/data.py:_seed:284-285; _business_dates:288-295; synthetic_series:320-352(kind='rate'); _ns:355-358; synthetic_curve_panel:361-377; _synthetic_short_rate:635-642; 대체 경로 load_treasury_curve:552-568, load_short_rate:645-671
- **목적:** FRED가 실패하거나 'Synthetic demo'를 고르면 Rates·Bonds·Structuring 화면이 쓰는 대체 데이터를 만든다. 모든 오프라인 금리 숫자의 입력이다.
- **가정:**
  - 곡선: NS β0·β1·β2를 고정 시작점(4%, ±1.5%, 0.5%)에서 일별 랜덤워크(sd 6·8·6bp)한다. τ = 2y. 수익률 하한 5bp.
  - 시드는 sha256('UST_PANEL') 고정이다. 날짜는 오늘에서 거꾸로 센 영업일이다.
  - 단기금리: OU, κ 0.8, θ 2~5%, σ 0.6~1.0%, 0 하한. SOFR 시드는 θ 3.5%, σ 0.7%다.
  - 출처는 'SYNTHETIC'이고 note가 붙는다. 캐시에 넣지 않는다.
- **한계:**
  - 누적 랜덤워크의 첫 행을 고정하고 마지막 행을 쓴다. 최신 행이 days에 따라 다르다: 504일(화면 기본) 9.586%→7.171% 역전, 200일 5.862%→4.769%, 60일 2.450%→4.285%(이 작업 재현). docstring 'level ~4%'는 첫 행에만 맞다(BS-25).
  - 숫자는 매일 같고 날짜만 오늘로 움직인다(BS-34).
  - 합성 곡선 앞단 9.6%와 합성 SOFR 3.6%가 서로 맞지 않는다. 이 불일치가 HW r0 재설정(M3-18)과 Vasicek 재평가 손실(M3-19, M3-N01)을 키운다.
  - 해설 문장 다수가 합성 여부를 말하지 않는다(D03-03). 배너는 있다.
- **적용 범위:** 데모 전용이다. 시장 값으로 읽지 않는다. 모형 검증의 참값 자료로는 쓸 수 있다(합성 SOFR의 κ 0.8 등).
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_data_synthetic_is_deterministic_and_labeled, ::test_data_synthetic_never_touches_the_cache, ::test_data_auto_degrades_to_synthetic_naming_the_provider, ::test_data_shapes_are_clean(결정성·라벨·형태만 본다. 수준의 현실성은 검증하지 않는다). 최신 행 값은 이 작업 스크래치 c2_bonds_opts.py.
- **관련 오류:** BS-25 (P3), BS-34, D03-03
- **화면:** Rates·Bonds·Structuring의 'Synthetic …' 오류색 배너와 SYNTHETIC 칩, 그 화면들의 모든 오프라인 숫자

### 6.4 FICC FX·변동성·구조화

#### 78. M4-01 FX 선도(CIP)·선도 포인트·암시 베이시스·캐리

- **위치:** core/ficc/fx.py:forward:57-61; core/ficc/fx.py:forward_points:64-71; core/ficc/fx.py:implied_basis:74-80; core/ficc/fx.py:carry:83-85; core/ficc/data.py:_SHORT_RATE_IDS:621-632; core/ficc/data.py:load_short_rate:645-671; ui/fx_page.py:_rate:66-72; ui/fx_page.py:do_forward:183-236; core/ficc/insights.py:narrate_fx_forward:208-224
- **목적:** 현물과 두 통화 금리로 무위험 이자 평형(CIP) 선도를 계산한다. 시장 선도를 넣으면 CIP 대비 연율 괴리(암시 베이시스)를 보여준다. 기준통화 매수의 캐리를 보여준다.
- **가정:**
  - F = S·exp((r_dom − r_for)·T). 연속복리. dom은 호가통화, for는 기준통화다(fx.py:4-6, 57-61).
  - T는 parse_tenor의 ACT/365F 실수 연이다('3m' = 0.25). 휴일 달력, 현물 결제 지연(T+2), 영업일 조정이 없다(fx.py:10).
  - 모든 만기(1m~2y)에 같은 금리 한 쌍을 쓴다(평탄, fx_page.py:195). 칸이 비면 load_short_rate 최신값을 쓴다. USD는 SOFR(없으면 DFF), EUR은 ECB 예금금리, GBP는 SONIA로 일간이다. JPY는 OECD 월평균 콜금리, KRW·AUD·CAD·CHF는 OECD 월평균 3m 금리다(data.py:621-632).
  - pip는 현물 > 20이면 0.01, 아니면 0.0001이다(fx.py:67-68).
  - 캐리 = r_for − r_dom(기준통화 매수, p.a., fx.py:83-85).
- **한계:**
  - 익일물·정책금리를 전 만기에 써서 1y·2y 선도가 시장과 기간 프리미엄만큼 다르다(FC-11).
  - JPY·KRW·AUD·CAD·CHF 금리는 OECD 월평균이라 수개월 묵을 수 있다. data.py:617-618 주석은 OECD 3m 계열이 6~8개월 늦다고 적는다(data_flow/MF-01, functional_completeness/FC-03).
  - Yahoo를 명시해도 금리는 source='auto'로 불러 합성 금리로 대체될 수 있다(fx_page.py:71, D03-10). 합성 배너는 뜬다.
  - 암시 베이시스는 순수 통화 베이시스가 아니다. 만기 불일치와 금리 지연이 섞인다. 그런데 해설은 \|basis\| ≥ 5bp면 'a real funding premium'이라고 단정한다(insights.py:219-223, 신규 M4-N6).
  - 시장 선도 포인트 공급원이 없다(SF-07). 결제일 기준이 시장 outright와 다르다.
- **적용 범위:** 선도 메커니즘 설명과 대략의 선도 수준에 쓴다. 시장 선도 호가 대체, 헤지 가격, 베이시스 거래 판단에는 쓰면 안 된다. 만기별 금리를 직접 넣으면 정확도가 오른다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_fx_forward_is_cip_and_its_basis_is_zero; ::test_fx_forward_points_follow_the_pip_rule; ::test_narratives_state_their_numbers(narrate_fx_forward, basis −12bp 문구). HEAD에서 개별 실행 PASS. 테스트는 정의식을 다시 계산하는 수준이다(공식이 자명해서 충분). fx.py __main__ 452-456은 스위트 밖이다(이번 실행 ok). financial_calcs.md 3장 표에 행 없음. 시장 선도와 대조한 적 없음.
- **관련 오류:** FC-11, SF-07, D03-10, D12-10, D03-03, D03-04, data_flow/MF-01, functional_completeness/FC-03, 신규 M4-N6
- **화면:** FX 화면 'Spot, forward & carry': Spot, Forward, Points, Carry long, 두 금리 stat, Implied basis(≥5bp 빨강), 'flat rates across tenors' 칩, 선도 표, fx_spot_chart(ui/fcharts.py:238), AI 패널 kind=fx_forward

#### 79. M4-02 Garman–Kohlhagen 옵션 가격·그릭스(GK 내재변동성 역산 포함)

- **위치:** core/ficc/fx.py:_check_gk:117-123; core/ficc/fx.py:garman_kohlhagen:126-147; core/ficc/fx.py:implied_vol_gk:150-165; ui/fx_page.py:do_option:238-301; core/ficc/structured.py:_vanilla:114-117; core/ficc/insights.py:narrate_fx_option:227-253
- **목적:** FX 유럽형 바닐라의 가격과 그릭스를 낸다. 구조화 상품의 옵션 다리(PPN 콜, RC 풋, DCD 풋)도 같은 함수로 가격을 매긴다(r_for를 배당수익률로 두면 BS와 같다).
- **가정:**
  - 로그정규 현물, 평탄 변동성, 평탄 연속복리 국내·외국 금리.
  - 유럽형 만기 행사. 조기행사·배리어 없음.
  - 델타는 spot delta, 프리미엄 미조정. delta_fwd = N(d1)(fx.py:144).
  - 단위: 기준통화 1단위당 호가통화. vega는 1 vol-pt당, theta는 달력일(1/365)당, rho는 금리 1.00당(UI는 ×1e-4로 bp당), gamma_1pct는 1% 현물 이동당 델타 변화(fx.py:145-146).
  - implied_vol_gk: brentq [1e-4, 5], 무차익 범위 밖이면 FICCError. UI에서는 호출하지 않는다(grep: 테스트와 자체 검사만).
- **한계:**
  - 스마일 위에서 가격은 그 행사가의 SABR vol로 매기지만 그릭스는 vol 고정(sticky-strike) 값이다. 스마일 동학이 없다.
  - USDJPY·USDKRW 시장 관례는 프리미엄 조정 델타다. 예: USDJPY S=150, r_JPY 0.5%, r_USD 4.3%, vol 10%, 3m에서 25d 콜 spot delta 0.250 대 PA delta 0.243(재실행 확인). 관례 차이로 행사가가 어긋난다(FC-11: 1y 25Δ 154.394 대 153.633).
  - 금리 기간구조와 결제 지연이 없다. FX vol은 사용자 입력이고 출처 표시가 없다(SF-07).
  - 구조화 화면에서 국내 금리는 UST 곡선 zero라 KRW·KOSPI200 상품에 다른 통화 금리가 들어간다(D03-V02/financial_calcs/FC-04).
  - implied_vol_gk는 1e-4 vol 가격보다 낮은 가격에 오류 없이 1e-4를 돌려준다(fx.py:161-162). 지금 UI 호출은 없다.
- **적용 범위:** 공식 자체는 정확하다. 유럽형 바닐라의 검산·교육·구조화 분해에 쓴다. 시장 관례(PA 델타, 결제일) 호가와의 직접 비교, 미국형·이색 옵션에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 #1(QuantLib AnalyticEuropeanEngine 5사례 최대 1.7e-13, Hull 예 4.76/0.81), #2(그릭스 ≤5e-13, vanna·volga 상대 ≤1e-6), #3(역산 왕복 ≤5e-14). 이 기준값은 감사 스크래치 스크립트에만 있고 스위트에 고정되지 않았다(TA-07). 스위트: tests/ficc_acceptance.py::test_gk_parity_and_delta_bounds; ::test_gk_implied_vol_round_trips; ::test_narratives_state_their_numbers(항등식·왕복, HEAD 개별 실행 PASS). fx.py __main__ 458-473 유한차분 그릭스는 스위트 밖(이번 실행 ok). PA 델타: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct/check1.py 재실행.
- **관련 오류:** TA-07(병합 FC-15), FC-11, SF-07, D03-V02(병합 financial_calcs/FC-04), D03-03, D03-04
- **화면:** FX 화면 'Option & smile': Premium, % of spot, Premium/1m, Delta(spot·forward), Gamma/1%, Vega/vol-pt, Theta/day, Rho 2종, AI kind=fx_option. Structuring 화면 옵션 다리 값

#### 80. M4-03 델타→행사가 변환과 ATM/RR/BF 3점 스마일 구성

- **위치:** core/ficc/fx.py:strike_from_delta:168-179; core/ficc/fx.py:smile_from_quotes:201-214; ui/fx_page.py:_strike:75-88; ui/fx_page.py:do_option:245-251; ui/fcharts.py:smile_chart:219
- **목적:** ATM, 25d RR, 25d BF 호가에서 25d 풋·ATM·25d 콜 세 점(행사가, vol)을 만든다. 사용자가 '25d'나 'ATM'으로 행사가를 고르게 한다.
- **가정:**
  - vol25c = atm + bf + rr/2, vol25p = atm + bf − rr/2(시장 근사, fx.py:206). smile-consistent BF 재가격은 하지 않는다.
  - ATM은 delta-neutral straddle 행사가 F·exp(½σ²T)(fx.py:211).
  - 25d는 spot delta, 프리미엄 미조정. 각 날개는 자기 vol로 행사가를 푼다.
  - UI의 '25d' 입력은 ATM vol로 행사가를 풀고 가격은 그 행사가의 SABR vol로 매긴다(ui/fx_page.py:12-13 문서, :251-253 코드).
- **한계:**
  - 예(S=1.10, r_USD 4.3%, r_EUR 2.0%, 3m, 화면 기본 ATM 8/RR 0.5/BF 0.3): UI '25d' 콜 행사가 1.1373은 스마일의 25d 콜 행사가 1.1396과 다르다. SABR vol로 다시 잰 델타는 콜 0.263, 풋 −0.251이다(재실행 확인). 이름과 실제 델타가 다르다.
  - 브로커 BF(smile-consistent) 관례와 다르면 날개 vol이 어긋난다. 크기는 미검증.
  - PA 델타 통화쌍(USDJPY, USDKRW)에서 행사가가 시장과 다르다(FC-11).
  - 10d 점이 없어 25d 밖은 SABR 외삽에만 의존한다.
- **적용 범위:** 3점 스마일 근사와 교육용으로 쓴다. 브로커 호가의 행사가 재현, 날개 옵션 가격에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. 독립 검증 범위는 델타→행사가 공식뿐이다: financial_calcs.md 3장 #7(델타 방정식 brentq 직접 풀이 대비 2e-16). 스마일 관례(BF 정의, PA 델타)는 시장 호가와 대조하지 않았다. tests/ficc_acceptance.py::test_strike_from_delta_round_trips; ::test_smile_ordering_follows_the_risk_reversal(HEAD PASS). '25d' 불일치: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct/check1.py 재실행(1.13733/1.13956, 0.2634).
- **관련 오류:** FC-11, SF-07
- **화면:** FX 화면 'Option & smile': Strike stat, 스마일 표(Point, Strike, Vol, Spot delta), 스마일 차트

#### 81. M4-04 SABR(Hagan 2002) 스마일 보정·보간

- **위치:** core/ficc/fx.py:sabr_vol:217-236; core/ficc/fx.py:calibrate_sabr:249-272; core/ficc/fx.py:smile_curve:275-276; ui/fx_page.py:do_option:250-255,277-279
- **목적:** 세 스마일 점에 SABR를 맞춰 임의 행사가의 vol을 보간·외삽한다. 그 vol로 GK 가격을 매긴다.
- **가정:**
  - Hagan 2002 lognormal 전개, β 고정(FX 1.0).
  - α, ρ, ν를 least_squares(trf)로 맞춘다. 경계 α∈[1e-4,5], ρ∈[−0.999,0.999], ν∈[1e-4,5]. 시작점 6개(ρ0 ∈ {−.3,0,.3} × ν0 ∈ {.3,1}) 중 비용 최소(fx.py:263-269).
  - 가중치 없는 vol 잔차 제곱합. converged는 least_squares의 success다(fx.py:272).
- **한계:**
  - UI는 점 3개에 모수 3개를 맞춘다. 보통 정확히 맞아 rmse가 0이다(화면 기본값 6.8e-10). 그래서 칩의 'rmse … vp'는 시장 적합 품질 정보를 주지 않는다.
  - 맞지 않는 경우도 있다. BF < 0이면 0.094 vp, RR 4%면 ρ가 경계 0.999에 붙어 0.11 vp, 1주·RR −3%·BF 2%면 ν가 경계 5에 붙어 0.77 vp다. 세 경우 모두 converged=True라 칩이 오류색이 되지 않는다(fx_page.py:277-279, 이번 측정, 신규 M4-N8).
  - Hagan 전개는 긴 만기·먼 날개에서 음의 밀도(차익)를 낼 수 있다. 검사 장치가 없다.
  - 날개 밖 외삽은 3점이 정한 모수에만 의존한다.
- **적용 범위:** 3점 스마일의 매끄러운 보간에 쓴다. 10d 밖 날개 가격, 긴 만기, 밀도 기반 계산에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. SABR 공식만 독립 검증: financial_calcs.md 3장 #6(QuantLib sabrVolatility 5사례, β=1·0.5, ≤6e-17). calibrate_sabr는 자기 재현만 본다: tests/ficc_acceptance.py::test_sabr_reproduces_its_quotes(rmse<1e-4, HEAD PASS). fx.py __main__ 485-492는 스위트 밖. 경계 사례: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify/v1.py 1번.
- **관련 오류:** 신규 M4-N8
- **화면:** FX 화면 'Option & smile': 'Vol used' stat, SABR 칩(rho, nu, rmse), 스마일 곡선 차트, 해설의 SABR 문장

#### 82. M4-05 FX 캐리 표(캐리, 3m vol, carry/vol, 모멘텀, 점수, 금리 신선도)

- **위치:** core/ficc/fx.py:_leg:322-332; core/ficc/fx.py:_stale:342-343; core/ficc/fx.py:carry_table:346-370; core/ficc/data.py:load_policy_rates:674-676; ui/fx_page.py:do_carry:303-371; core/ficc/insights.py:narrate_carry:256-294; ui/fcharts.py:carry_bar_chart:282
- **목적:** G10+KRW 각 통화의 USD 대비 캐리와 위험 조정 점수를 표로 보여준다.
- **가정:**
  - 캐리 = 최신 r_ccy − 최신 r_usd(p.a.), 통화 매수 기준. USD 선행 호가(USDJPY 등)는 뒤집는다(fx.py:328-329).
  - 3m vol = 최근 63관측 로그수익률 표준편차 × √252.
  - mom_3m = 63관측 단순수익률(연율화 안 함).
  - score = carry/vol + mom/vol. 연 캐리와 3개월 모멘텀을 같은 가중으로 더한다(fx.py:366).
  - rate_stale = 통화 또는 USD 금리의 마지막 관측이 현물 마지막 관측보다 45일 넘게 오래됨(fx.py:51, 342-343, 368-369).
- **한계:**
  - 점수는 단위가 섞인 휴리스틱이다. 3개월 모멘텀이 연율 캐리 대비 사실상 1/4 가중이다. 근거·검증이 없다.
  - 금리는 정책·익일물 또는 OECD 월평균이라 선도 포인트로 본 실제 캐리와 다르다. KRW는 6~8개월 늦은 월간 계열이다(data.py:617-618, functional_completeness/FC-03).
  - rate_stale은 해설에만 나온다(insights.py:288-293). 표에 'Rate date' 열이 없고 AI 페이로드에도 rate_date·rate_stale이 없다(fx_page.py:345-358, data_flow/MF-01).
  - 22관측 미만이면 오류. 현물 0·음수는 _leg가 거절하지만 inf는 거르지 않는다(D12-10).
- **적용 범위:** 통화별 금리차의 대략적 순위와 설명에 쓴다. 매매 신호, 실제 선도 캐리, 최신 금리 판단에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_carry_table_inverts_usd_base_pairs(캐리·모멘텀 값 직접 대조); ::test_narratives_state_their_numbers. HEAD 개별 실행 PASS. 신선도 플래그 검사는 fx.py __main__ 537-545에만 있고 스위트 밖이다(이번 실행 ok). 실데이터로 점수의 예측력을 본 적 없음.
- **관련 오류:** data_flow/MF-01, functional_completeness/FC-03, D03-10, D12-10, D03-03, D03-04, D03-08
- **화면:** FX 화면 'Carry basket': Best score, Highest carry stat, 캐리 막대 차트, 표(Pair~Score), 출처 칩, AI kind=fx_carry

#### 83. M4-06 FX 캐리 바스켓 백테스트

- **위치:** core/ficc/fx.py:_ffill_rates:373-381; core/ficc/fx.py:carry_backtest:384-444; ui/fx_page.py:do_carry:303-371; ui/fcharts.py:carry_equity_chart:263; docs/asset_expansion_study.py:run_fx:425-429
- **목적:** 금리차 순위로 상위 n 통화 매수, 하위 n 매도 바스켓의 과거 성과를 보여준다. 자산 확장 연구에서는 비교 벤치마크로 쓴다.
- **가정:**
  - 리밸런싱일(기본 21관측)마다 그날 알려진 r_ccy − r_usd로 순위를 매기고 다음 관측부터 수익을 받는다.
  - 수익 = 현물 수익률 + (r_ccy − r_usd)/252를 관측마다 더한다. 주말·휴일 간격과 무관하게 1/252(fx.py:425).
  - 금리는 날짜 기준 ffill. note에 'monthly'가 있는 계열은 1관측 지연(fx.py:378).
  - 다리별 ±1/k, 각 다리 자본의 100%(총 노출 200%). 리밸런싱 사이 비중 고정(매일 비용 없이 고정 비중으로 재조정하는 것과 같다. K-e와 같은 가정).
  - 비용 = 회전율 × cost_bps(UI 기본 validate.cost_bp('fx')).
  - 연 수익률은 CAGR, 'Sharpe' = CAGR/연 변동성(fx.py:432-443). 벤치마크는 전 통화 동일가중 매수, 비용 없음.
- **한계:**
  - 'Sharpe'가 게이트의 산술평균 Sharpe(validate.py:137-143)와 다르다(FC-14: 같은 손익에서 0.428 대 0.467).
  - 월평균 금리 발표일을 1관측 지연으로만 근사한다. data.py:617-618 주석대로 OECD 계열이 6~8개월 늦게 나온다면 'no lookahead' 문구(fx.py:438)가 틀린다(DF-04, 추정).
  - 정책·월평균 금리는 실제 선도 캐리가 아니다. 통화 베이시스·스왑 포인트가 없다.
  - Yahoo FX는 평일 기준 연 약 260관측이라 관측당 1/252 적립은 캐리를 약 3% 과대 계상한다(추정).
  - 공통 날짜 교집합만 쓴다. 단일 경로 in-sample 결과이고 다중검정·워크포워드가 없다.
- **적용 범위:** 캐리 효과의 기술적 설명에 쓴다. 성과 주장, 전략 채택, 게이트 판정에는 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. 스위트: tests/ficc_acceptance.py::test_carry_backtest_is_sane_and_costs_only_hurt는 형태(NaN 없음, 길이), 비용 방향, 결정성만 본다(HEAD PASS). 값 검사(월간 1관측 지연, 시작일 2025-03-03, 작은 사례의 롱 JPY/숏 EUR)는 fx.py __main__ 505-536에만 있고 스위트 밖이다(이번 실행 ok). 무예견성은 코드 읽기와 자체 검사뿐(financial_calcs.md 6장). 연구 results.csv의 carry_basket_sharpe 0.371은 CAGR/vol 정의다. 스위트 값 검사가 없어 회귀를 잡지 못한다(TA-02).
- **관련 오류:** FC-14, DF-04, data_flow/MF-01, D03-10, D12-10, K-e, functional_completeness/FC-03
- **화면:** FX 화면 'Carry basket': Basket return, Ann. return, Ann. vol, Sharpe, Max drawdown, Equal-weight long stat, 기간·리밸런싱·long/short 칩, 자본곡선 차트, 해설·페이로드

#### 84. M4-07 FX 스타일 백테스트(횡단면 모멘텀, 달러 캐리)

- **위치:** core/ficc/fx_styles.py:_panel:33-48; core/ficc/fx_styles.py:_run:51-81; core/ficc/fx_styles.py:momentum_backtest:84-100; core/ficc/fx_styles.py:dollar_carry_backtest:103-114; docs/asset_expansion_study.py:run_fx:391-440
- **목적:** Menkhoff 외(2012) FX 모멘텀과 Lustig 외(2014) 달러 캐리를 재현해 자산 확장 연구의 전략 카드 S_V3, S_V4를 만든다.
- **가정:**
  - carry_backtest와 같은 회계: 현물 + 금리차/252, ffill, 월간 1관측 지연, 리밸런싱 사이 비중 고정, 회전율 비용(fx_styles.py:59-69).
  - 모멘텀: 과거 21·f관측 로그 현물 변화 + 누적 금리차로 순위. 상·하위 k = n//3 통화에 ±1/k(USD 대비 7통화면 k=2, fx_styles.py:90-97).
  - 달러 캐리: AFD = 평균(r_i − r_usd) > 0이면 전 통화 동일가중 매수, 아니면 매도.
  - CarryBacktest.sharpe는 CAGR/vol이다(fx_styles.py:74-79).
- **한계:**
  - 금리는 OECD 월평균·정책금리라 실제 선도 할인과 다르다.
  - USD 대비 7개 통화(G10_KRW, data.py:65)라 3분위 포트폴리오가 2통화씩이다. 문헌 표본(수십 통화)과 다르다.
  - CarryBacktest.sharpe는 FC-14와 같은 정의다. 다만 연구 게이트는 일간 손익으로 다시 계산하므로 판정에는 영향이 없다(asset_expansion_study.py:413-424).
  - 연구 판정은 둘 다 REJECT: S_V3 SR_OOS −0.59, DSR 0.06. S_V4 SR_OOS 0.27, 90% CI [−0.42, 0.93](docs/asset_expansion/results.csv).
- **적용 범위:** 연구 기록 재현용이다. UI에 나오지 않는다. 전략 채택 근거로 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. tests/expansion_acceptance.py::selfcheck_fx_styles는 형태(포지션 수 2/7, NaN 없음, 리밸런싱 수)와 비용 방향만 본다. 순위 신호와 수익 값을 기준값과 대조하는 검사는 없다. 실데이터 게이트 카드 docs/asset_expansion/cards/S_V3_fx_momentum.json, S_V4_dollar_carry.json(REJECT)은 전략 가설 검증이지 코드 검증이 아니다.
- **관련 오류:** DF-04(같은 지연 규칙), K-e, FC-14(같은 정의, 판정 영향 없음)
- **화면:** - (UI 없음. docs/asset_expansion/results.md와 카드)

#### 85. M4-08 Fama 회귀(UIP 검정)

- **위치:** core/ficc/fx_styles.py:FamaRow:117-123; core/ficc/fx_styles.py:fama_regression:126-149
- **목적:** 다음 달 환율 변화를 금리차에 회귀해 UIP(기울기 −1)를 검정한다.
- **가정:**
  - 21관측 간격의 비중첩 월 표본. x = (r_ccy − r_usd)·21/252, y = 다음 21관측 로그 현물 변화(USD 표시 외화 가격).
  - OLS. 표본 12개 미만 통화는 건너뛴다.
- **한계:**
  - 모듈 문서(13행)는 HAC t를 약속하지만 반환하는 t_stat은 OLS 동분산 t다(147행). 145행 'HAC' 식은 OLS 정규방정식상 평균이 0인 점수 계열의 t라 항상 0 근처다(이번 측정 3.7e-17). 계산하고 버린다(신규 M4-N5). 표본은 21관측 간격의 비중첩 월이라(fx_styles.py:136-138) 겹침 때문에 t가 부풀지는 않는다. 결함은 표기 오류다. 호출처가 없어 화면 영향은 없다.
  - FamaRow 주석(120행)이 UIP 기울기를 '1?'로 적어 docstring(−1, 128-130행)과 어긋난다.
  - 월평균 금리, 통화 7개.
- **적용 범위:** 현재 호출처가 없다(자체 검사만). 결과를 보고하려면 t 통계를 먼저 고쳐야 한다.
- **검증 상태:** 코드로만 확인. 자체 검사(fx_styles.py __main__ 168-169)는 기울기가 유한한지만 본다. tests/expansion_acceptance.py::selfcheck_fx_styles. 독립 기준 없음. HAC 식이 0이 되는 것은 docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify 안 계산으로 확인(newey_west_t of score ≈ 1.9e-15).
- **관련 오류:** 신규 M4-N5
- **화면:** -

#### 86. M4-09 KOSPI200 선물 공정가치·베이시스·암시 조달금리

- **위치:** core/ficc/equity_deriv.py:fair_value:48-52; core/ficc/equity_deriv.py:implied_repo:55-59; core/ficc/equity_deriv.py:basis_report:81-87; ui/derivatives_page.py:snapshot:65-79,120-122; ui/derivatives_page.py:narrative:148-152; docs/asset_expansion_study.py:run_basis:701-720
- **목적:** 선물이 보유비용 공정가치 대비 rich인지 cheap인지(bp)와 시장 선물이 암시하는 단리 조달금리를 보여준다.
- **가정:**
  - KRX 관례 F* = S·(1 + r·T) − D, T = days_left/365, r = KIS CD 91일(없으면 0.03, derivatives_page.py:71).
  - 배당점수 D는 화면 호출에서 0이다(div_pts 미전달, :121-122).
  - implied_repo는 항상 단리 KRX식이다(convention 무시, FC-13).
  - 'Mispricing' = (F − F*)/S, \|값\| > 20bp면 빨강(:240).
- **한계:**
  - 배당을 빼서 배당이 큰 만기에서 선물이 체계적으로 cheap, 암시 금리가 낮거나 음수로 보인다. 재현: S=400, CD 2.8%, 50일, 배당 5pt면 −125.0bp, −6.325%(financial_calcs/FC-06).
  - 실데이터 M_O2(세션 2026-09-23, 79일): mispricing −55.0bp, 암시 금리 0.67% 대 CD 3.21%. 그러나 KIS 이론가로 역산한 배당은 1.16pt뿐이다. 배당을 넣어도 −44.7bp, 암시 금리 1.15%다(이번 계산). 이 사례의 cheap은 대부분 배당 누락이 아니다. 원인(장 마감 종가 시차, 시장 할인)은 미확정이다. FC-06 수정 뒤에도 이 값은 남는다.
  - CD가 없으면 3.00% 가정값이 'input'으로 표시된다(D03-05, :79).
  - KIS 마스터 실패 시 고정 코드 A01612로 조회한다(SFV-02, :65).
  - 거래비용·증거금·세금·차입 제약이 없어 차익 판단이 아니다.
- **적용 범위:** 배당점수를 넣은 경우의 대략적 베이시스 설명에 쓴다. 현재 화면의 rich/cheap 판정과 암시 조달금리는 배당 미반영이라 판단 근거로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. equity_deriv.py __main__ 573-578(왕복, KRX 대 연속, mispricing 10bp 정확). tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). financial_calcs.md FC-06 재현(r08 1번). docs/asset_expansion/cards/M_O2_basis_today.json PASS는 이론가 차 1.16pt를 배당 대역 0.1+0.02·S·T(약 4.97pt) 안으로 허용한 것이며 배당 보정 검증이 아니다. M_O2 분해: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify/v1.py 3번.
- **관련 오류:** financial_calcs/FC-06, FC-13, D03-05, SFV-02, D05-06, P01-04, functional_completeness/MF-01
- **화면:** 파생 화면 첫 stat 줄: Front future, Basis, Fair value, Mispricing(>20bp 빨강), Implied funding, KIS theo gap. 'rate … (source)' 칩. 해설·AI kind=kospi200_derivatives

#### 87. M4-10 옵션 보드 내재변동성(Cboe 암시 선도 + Black-76 역산 + KIS IV 대조)

- **위치:** core/ficc/equity_deriv.py:board_quotes:106-118; core/ficc/equity_deriv.py:implied_forward:121-139; core/ficc/equity_deriv.py:chain_implied_vols:153-183; core/ficc/equity_deriv.py:reconcile_iv:186-193; core/ficc/swaps.py:black76:208-230; core/ficc/swaps.py:_invert:256-268; core/ficc/swaps.py:implied_black_vol:271-276; data/kis_markets.py:kospi200_expiry:338-343; data/kis_markets.py:option_chain:392-407; ui/derivatives_page.py:snapshot:56-101; ui/xcharts.py:smile_chart:35-54
- **목적:** KOSPI200 옵션 보드에서 선도를 암시하고 OTM 중간가를 Black-76으로 역산해 스마일을 만든다. 거래소(KIS) IV와의 차이를 잰다.
- **가정:**
  - F = K* + e^{rT}(C − P), K*는 \|C − P\| 최소 행사가(Cboe 규칙). F가 보드 범위 밖이면 오류.
  - F 아래는 풋, 위는 콜 중간가. 0.05pt 미만 프리미엄과 내재가치 이하 가격은 버린다.
  - 먼저 양쪽 호가가 있는 \|ln(K/F)\| ≤ 0.15만 쓴다. 5개 미만이면 마지막 체결가로 ±0.10에서 다시 한다(derivatives_page.py:95-98).
  - T = (만기일 − 마지막 세션일) 달력일/365. 만기일은 둘째 목요일 규칙이고 휴일 조정이 없다(kis_markets.py:338-343). r = CD 91일 평탄, 연속복리로 사용.
  - 대조 게이트: \|σ_app − σ_KIS\| 중앙값 ≤ 0.5 vp, 90분위 ≤ 1.5 vp.
  - 보드는 현물 ±10%, 2.5pt다(derivatives_page.py:68). 시리즈 상한 160개(kis_markets.py:393, 406-407) 때문에 지수 1,126에서는 실제로 ±8.75%, 80 행사가다(M_O1 80 행사가와 일치).
- **한계:**
  - 장 마감 뒤에는 서로 다른 시각의 마지막 체결가로 역산한다. 화면이 경고 배너를 띄운다(:228-231).
  - 실데이터 M_O1(장 마감 포착): 중앙값 차 2.22 vp, 90분위 2.95 vp로 게이트 불합격. 원인(시간 관례, 금리, 체결 시차)은 미확정.
  - 달력일/365 T가 KIS 관례와 다를 수 있다(FC-11). 금리는 만기와 무관한 CD 91일이다.
  - 'IV gap vs KIS' 툴팁은 '±15 % quoted'라고 적지만 장 마감 대체 경로는 ±10% 마지막 체결가다(:97, :250).
- **적용 범위:** 장중 양쪽 호가가 있을 때의 스마일 관찰에 쓴다. 장 마감 뒤 값과 KIS IV와의 정량 비교 결론에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. Black-76 공식은 독립 검증(financial_calcs.md 3장 #4: QuantLib blackFormula, Hull 예 1.12, 차이 0~6e-14). 파이프라인은 equity_deriv.py __main__ 579-597(합성 보드에서 F 1e-6, IV 1e-6 재현), tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). ui/derivatives_page.py __main__ 295-302는 스위트 밖(functional_completeness/FC-06, 이번 실행 ok). 실데이터 카드 docs/asset_expansion/cards/M_O1_board_today.json: REVISE.
- **관련 오류:** FC-11, D05-06, P01-04, SFV-02, functional_completeness/MF-01, functional_completeness/FC-06, 신규 M4-N10(M_O1 카드 출처 라벨)
- **화면:** 파생 화면: Forward (parity), ATM IV, 'IV gap vs KIS'(게이트 0.5, 초록/빨강) stat, 'n quoted near-ATM' 칩, 스마일 차트(app 대 exchange IV), 장 마감 경고 배너, payload smile

#### 88. M4-11 풋-콜 패리티 잔차와 정적 차익(수직·버터플라이) 검사

- **위치:** core/ficc/equity_deriv.py:parity_residuals:196-209; core/ficc/equity_deriv.py:static_arbitrage:212-240; ui/derivatives_page.py:snapshot:102-103; ui/derivatives_page.py:narrative:141-142,160-161; ui/derivatives_page.py:build_derivatives_page.worker:251-252
- **목적:** 보드 가격이 패리티, 단조성, 볼록성을 지키는지 센다. 호가 품질 점검용이다.
- **가정:**
  - ρ_K = C − P − e^{−rT}(F − K). F는 같은 보드에서 암시한 값. \|K/F − 1\| ≤ 0.10만, 절반 스프레드 합 안이면 'within'.
  - 수직: 콜은 행사가에 대해 감소, 풋은 증가. 버터플라이: 인접 세 점의 비균등 간격 볼록성(중간점이 현을 넘으면 위반, :232-235). 허용오차 1e-9.
  - 중간가 기준. 화면은 양쪽 호가가 있는 \|ln(K/F)\| ≤ 0.15 행사가만 센다(:103).
- **한계:**
  - F를 같은 보드의 패리티로 암시하므로 패리티 잔차가 구조적으로 작게 나온다(순환).
  - 콜 기울기 하한(≥ −DF)과 달력 차익 검사는 없다.
  - 중간가 기준이라 스프레드 안의 위반도 센다. 허용오차 1e-9는 호가 단위보다 훨씬 작다.
  - 장 마감 뒤에는 양쪽 호가가 없어 검사 대상이 0개다. 'Butterfly viol.'은 0으로 초록이 되고, 해설은 패리티를 'nan%'로 적는다(이번 측정: n_calls 0, n_puts 0, 신규 M4-N12). M_O1의 '버터플라이 위반 0'도 이 경우다.
- **적용 범위:** 장중 보드 품질 경고에 쓴다. 장 마감 뒤 값과 차익 기회 판단에는 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. 패리티 잔차는 값 검사가 있다(equity_deriv.py __main__ 594-595, 잔차 <1e-9). 정적 차익은 깨끗한 보드에서 수직 위반 0만 확인한다(:596-597). 위반을 넣어 잡는지 보는 검사가 없어 탐지기가 고장 나도 통과한다. 버터플라이는 단언하지 않는다. tests/expansion_acceptance.py::selfcheck_equity_deriv. financial_calcs.md 3장 #31(코드 읽기 + 자체 검사). 버터플라이 부등식 방향은 이번 코드 읽기로 확인. 장 마감 재현: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify/v2.py.
- **관련 오류:** functional_completeness/FC-05(vertical 수는 payload에만), functional_completeness/MF-01, 신규 M4-N12
- **화면:** 파생 화면: 'Butterfly viol.' stat, 해설의 패리티·버터플라이 문장, payload static_arbitrage

#### 89. M4-12 SVI 스마일 적합과 Gatheral–Jacquier 버터플라이 조건

- **위치:** core/ficc/equity_deriv.py:SVIFit.arbitrage_free:265-268; core/ficc/equity_deriv.py:svi_w:271-274; core/ficc/equity_deriv.py:svi_g:277-285; core/ficc/equity_deriv.py:fit_svi:288-316; core/ficc/equity_deriv.py:svi_vol:319-320; core/ficc/equity_deriv.py:calendar_crossing:323-327; ui/derivatives_page.py:snapshot:104-106,125
- **목적:** 역산 IV에 raw SVI를 맞춰 매끄러운 스마일을 얻고 무차익 여부(g(k) ≥ 0)를 표시한다. SVI ATM vol은 헤지 시뮬레이션의 σ_h가 된다.
- **가정:**
  - 총분산 w = σ²T에 최소제곱. 가중치는 1/스프레드(없으면 스프레드 0.05, 하한 0.01)이고 평균 1로 정규화한다.
  - 경계 a∈[−1,1], b∈[0,5], ρ∈[−0.999,0.999], m∈[−1,1], σ∈[1e-4,2]. 시작점 1개.
  - 무차익은 적합 후 [k_min−0.05, k_max+0.05] 201점에서 g 최소값으로만 확인한다(제약으로 넣지 않음).
- **한계:**
  - 시작점이 하나라 국소해 위험이 있다. 수렴 여부만 기록한다.
  - 무차익은 적합 범위 근처만 검사한다. 날개 밖은 보장하지 않는다.
  - 실데이터 M_O1: RMSE 2.09 vp(화면 빨강 기준 1.0 초과), min g +0.77.
  - 만기 하나만 맞춘다. calendar_crossing은 UI에서 쓰지 않는다.
- **적용 범위:** 단일 만기 스마일 평활과 RND 입력에 쓴다. 다만기 표면, 날개 가격, 무차익 보장이 필요한 가격결정에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. equity_deriv.py __main__ 598-606(자기 표면 재현 rmse<1e-3, 무차익, 달력 교차 0). tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). 독립 수치 기준과 비교한 적 없음(financial_calcs.md 6장). 실데이터 카드 M_O1_board_today REVISE.
- **관련 오류:** -
- **화면:** 파생 화면: 'SVI ρ', 'SVI RMSE'(>1.0 빨강) stat, 스마일 차트의 SVI 곡선, 해설 'arbitrage-free' 문구, payload svi

#### 90. M4-13 모형무관 내재변동성(MFIV, Cboe 스트립)

- **위치:** core/ficc/equity_deriv.py:mfiv:333-389; core/ficc/equity_deriv.py:interpolate_30d:392-399; ui/derivatives_page.py:snapshot:107-110; data/kis_markets.py:option_chain:392-407
- **목적:** OTM 옵션 스트립으로 모형 없이 만기 기대분산을 계산한다(VKOSPI 방식).
- **가정:**
  - σ² = (2/T)Σ(ΔK/K²)e^{rT}Q(K) − (1/T)(F/K₀ − 1)². K₀ 아래 풋, 위 콜, K₀에서 평균.
  - 매수호가 0(또는 중간가 없음)이 연속 2개면 그 방향을 자른다. 매수호가가 없으면(None) 중간가를 그대로 쓴다(:344-351).
  - ΔK는 이웃 간격의 절반, 양끝은 한쪽 간격.
  - 입력 보드는 현물 ±10%이고 시리즈 상한 160개 때문에 지수 1,126에서 실제 ±8.75%(80 행사가)다.
- **한계:**
  - 절단 편향(평탄 vol, 80 행사가 ±8.75%, 이번 측정): 20%·20일 −0.15 vp, 40%·15일 −2.50 vp, 20%·79일 −1.73 vp. ±10% 전체였다면 −0.07/−1.74/−1.27 vp다. 실데이터 M_O1의 MFIV 37.7% < ATM 39.5%와 방향·크기가 맞는다. 화면에 절단 표시가 없다(신규 M4-N9).
  - 이산화 오차: 간격 2.5pt +0.3bp, 5pt +1.0bp, 25pt +24.9bp(financial_calcs #30).
  - 장 마감 뒤 마지막 체결가도 들어간다(quoted_only 필터 없음).
  - 화면 값은 만기 하나의 분산이다. 30일 보간은 화면에 없어 VKOSPI와 기간이 다르다.
- **적용 범위:** 근월 만기의 대략적 기대 변동성에 쓴다. VKOSPI 재현, 분산 스왑 가격, 먼 만기·고변동 국면 수치에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 #30(평탄 20% 보드, 알려진 정답 대비 이산화 오차). equity_deriv.py __main__ 607-613. tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). 절단 편향: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify/v1.py 2번(160 시리즈 상한 반영), 이전 ±10% 값은 docs/nautilus_bridge/register_evidence/M4_fx_vol_struct/check3.py.
- **관련 오류:** P01-04(체인 범위 결정 12.13), 신규 M4-N9
- **화면:** 파생 화면: MFIV stat, 해설 'Model-free implied vol … (VKOSPI-style strip)', payload mfiv

#### 91. M4-14 위험중립 밀도(SVI 위 Breeden–Litzenberger)

- **위치:** core/ficc/equity_deriv.py:rnd_from_svi:402-416; core/ficc/equity_deriv.py:pricing_kernel:419-426; ui/xcharts.py:density_chart:57-69; ui/derivatives_page.py:snapshot:111; ui/derivatives_page.py:build_derivatives_page.worker:257-263; core/quant/garch.py:simulate_returns:674-702
- **목적:** SVI 스마일로 만든 콜 곡선의 2계 미분으로 만기 위험중립 밀도를 그린다. GARCH 엔진이면 P 밀도와 겹쳐 그린다.
- **가정:**
  - f_Q(K) = e^{rT}∂²C/∂K², np.gradient 두 번, 격자 F·exp(±0.6) 401점.
  - 음수 밀도는 0으로 자르고 negative_share로 비율만 기록한다.
  - P 밀도는 GARCH-t 0 로그드리프트 시뮬레이션(3000경로)의 KDE이고 현물 기준이다(배당 없음, worker 260-262).
- **한계:**
  - SVI 날개 외삽에 크게 의존한다. 적합 범위(\|k\| ≤ 0.15) 밖 꼬리는 모형 가정이다.
  - 음수 밀도를 자르면 적분과 평균이 왜곡된다. 화면은 적분만 보여준다.
  - P 밀도는 현물, Q 밀도는 암시 선도 기준이라 배당만큼 중심이 다르다.
  - 가격결정 커널 f_Q/f_P는 함수만 있고 화면에 없다(functional_completeness/FC-05).
- **적용 범위:** 시장 내재 분포 모양의 시각화에 쓴다. 꼬리 확률 수치, 위험 한도, 커널 추정에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. equity_deriv.py __main__ 614-618(평탄 vol에서 적분 0.99~1.01, 평균/F 오차 <0.2%, negative_share 0). tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). 독립 기준 없음(financial_calcs.md 6장). 실데이터 M_O1 적분 1.000004.
- **관련 오류:** functional_completeness/FC-05
- **화면:** 파생 화면: 'RND ∫' stat, 밀도 차트(f_Q, GARCH 엔진이면 f_P), payload rnd

#### 92. M4-15 박스 스프레드 조달금리

- **위치:** core/ficc/equity_deriv.py:box_rate:432-443; ui/derivatives_page.py:snapshot:112-119; ui/derivatives_page.py:narrative:162-163
- **목적:** 롱 박스 가격에서 KRW 연속복리 조달금리를 암시하고 CD와 비교한다.
- **가정:**
  - B = C(K₁) − C(K₂) + P(K₂) − P(K₁), r = −ln(B/(K₂ − K₁))/T. 중간가 기준.
  - 화면은 F를 사이에 둔 인접 두 행사가(간격 2.5pt)를 쓴다. 양쪽 호가가 하나도 없으면(장 마감) 계산하지 않는다(:117).
  - 유럽형, 신용·증거금·거래비용 없음.
- **한계:**
  - 2.5pt 박스는 가격 오차에 극도로 민감하다. T=20일에서 박스 가격 오차 0.01이면 금리 −7.3%p, 0.025면 −18.2%p, 0.05면 −36.2%p다(재실행 확인). 같은 0.05 오차가 100pt 박스에서는 −0.91%p다. ATM 프리미엄이 약 21pt 수준이라 화면 값은 호가 반올림과 스프레드 잡음이 지배한다(신규 M4-N4).
  - 오차 대역이나 스프레드 기반 경고가 없다.
- **적용 범위:** 넓은 행사가 간격의 양쪽 호가 박스에서만 의미가 있다. 현재 화면의 'Box rate'와 해설의 bp 차이를 조달금리 판단에 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. equity_deriv.py __main__ 619-620(합성 보드 r 1e-9 재현). tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). financial_calcs.md 3장 #31(코드 읽기). 민감도: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct/check2.py 재실행.
- **관련 오류:** 신규 M4-N4
- **화면:** 파생 화면: 'Box rate' stat, 해설 'The ATM box implies a KRW funding rate of … (±bp)', payload box_rate

#### 93. M4-16 델타 헤지 손익 시뮬레이션(감마 항등식, GBM·GARCH-t 엔진)

- **위치:** core/ficc/equity_deriv.py:hedge_pnl_simulation:472-542; ui/derivatives_page.py:snapshot:123-133; ui/derivatives_page.py:narrative:164-174; ui/derivatives_page.py:build_derivatives_page.worker:264-271; core/quant/garch.py:simulate_returns:674-702
- **목적:** σ_h(SVI ATM vol)로 판 옵션을 매일 델타 헤지할 때의 손익 분포, CVaR, 손익분기 실현변동성을 보여주고 손익을 감마 가중 분산 항등식으로 분해한다.
- **가정:**
  - 짧은 옵션 1개, 가격·델타는 Black-76(선도 S·e^{rτ}, 배당 없음), 매일 리밸런싱, dt=1/252.
  - GBM 엔진은 σ_true = σ_h(화면에 σ_true 입력 없음), 드리프트 (r − ½σ²)dt. GARCH-t 엔진은 KOSPI200 600일 적합의 0 로그드리프트 경로(경계 있는 혁신, :489-491).
  - 화면 비용 0bp. 금리는 연속복리 r 평탄. 만기 청산 비용은 없다.
  - 행사가 = round(F/2.5)·2.5(배당 반영 암시 선도), 현물 = 지수.
  - 지평 = max(round(T·252), 5)일(T는 달력일/365, derivatives_page.py:124).
- **한계:**
  - GBM 엔진은 σ_true = σ_h라 평균 손익이 정의상 0이고 손익분기 vol도 σ_h와 같아진다. 이번 측정: +0.29bp(SE 0.92bp), M_O1 유사 입력 +2.17bp(SE 1.52bp)·손익분기 39.28% 대 σ_h 39.5%. 화면은 그 잡음의 부호로 초록·빨강을 칠한다(:265, 신규 M4-N7).
  - 시뮬레이션 선도에 배당이 없어 행사가가 ATM이 아니다(배당점수만큼 ITM 콜).
  - 점프, 비용(화면 0), 이산 배당, 스마일 동학이 없다. 두 엔진의 드리프트 측도가 다르다(GBM은 위험중립형, GARCH는 0 로그드리프트).
  - 죽은 조건식 rate_daily(491행, FC-12).
- **적용 범위:** 감마·변동성 위험의 교육용 분해에 쓴다. 옵션 매도 기대수익, 꼬리 위험 한도, 전략 판단에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. equity_deriv.py __main__ 621-627(σ_h=σ_true면 평균 ≈ 0, σ_h<σ_true면 손실, 손익분기 vol 0.22~0.28, 기울기 0.8~1.2, R²>0.8). tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). 독립 기준 없음(financial_calcs.md 6장). GBM 동어반복: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct/check1.py, docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify/v1.py 7번.
- **관련 오류:** FC-12, 신규 M4-N7, functional_completeness/MF-01
- **화면:** 파생 화면 헤지 줄: Hedge P&L(mean, 부호 색), SE, CVaR95, σ_h, Break-even realised vol, Identity slope/R², Engine. 해설(GARCH 엔진이면 ν·지속성 문장 포함)·payload hedge

#### 94. M4-17 레버리지 ETF 드래그 식(Avellaneda–Zhang 2010)

- **위치:** core/ficc/equity_deriv.py:letf_drag:548-559; core/ficc/equity_deriv.py:letf_realised_drag:562-564
- **목적:** β배 일일 리밸런싱 펀드가 β×지수 대비 잃는 로그 드래그를 분산 경로로 계산한다.
- **가정:**
  - ln(L_T/L_0) − β ln(S_T/S_0) = ((β − β²)/2)Σσ²Δ + ((1 − β)r − f)T. 일일 리밸런싱, 연속 근사.
  - T = 세션 수/252. 금리 r, 보수 f 평탄.
  - 지수 배당수익률 항이 없다(배당 없는 지수 또는 총수익 지수 기준 식).
- **한계:**
  - 식은 정확하지만 결과는 입력 분산의 질에 달렸다.
  - 호출처가 rate를 넘기지 않아 (1 − β)r 항이 0이다(ui/etf_page.py:108,113; docs/asset_expansion_study.py:618). 20% vol, 63세션, f=0.64%, r=3.21%(CD)에서 빠진 항: β=+2 −80bp, β=−1 +160bp, β=−2 +241bp(이번 측정). 인버스 펀드에서 크다(신규 M4-N3).
  - 비교 지수에 따라 맞는 금융 항이 다르다(유도, 미검증). 선물형 펀드를 총수익 지수와 비교하면 (1−β)r − f가 맞다. 가격지수와 비교하면 βq가 더해져 β=+2에서는 일부 상쇄되지만 인버스에서는 여전히 +1%p 이상 남는다.
  - 추적오차, 현금·선물 롤, 괴리율은 없다.
- **적용 범위:** 변동성 드래그 크기의 개념 설명에 쓴다. 금리·배당이 빠진 값을 실제 괴리 예측으로 쓰면 안 된다. 특히 인버스 펀드에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 #29(일일 리밸런싱 2만 경로: β=+2 −0.06249 대 −0.06250, β=−2 −0.18757 대 −0.18750). equity_deriv.py __main__ 628-632. tests/expansion_acceptance.py::selfcheck_equity_deriv(이번 실행 ok). 누락 항 크기: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify 안 letf_drag 계산.
- **관련 오류:** 신규 M4-N3(= NEW-M6-07)
- **화면:** ETF 화면(M4-18의 계산 엔진). 직접 표시는 M4-18 참조

#### 95. M4-18 ETF 화면의 레버리지·인버스 ETF 드래그 예측(GARCH-t 분산 경로, 직전 분기 분산)

- **위치:** ui/etf_page.py:LETF:34-36; ui/etf_page.py:analyze:91-127; ui/etf_page.py:narrative:153-162; ui/etf_page.py:build_etf_page.worker:216-226; core/ficc/equity_deriv.py:letf_drag:548-559(M4-17); core/quant/garch.py:fit_garch:446; core/quant/garch.py:forecast_variance:558-571; data/kis_markets.py:KISMarkets.index_daily:437-449; docs/asset_expansion_study.py:run_letf:602-639; README.md:289
- **목적:** KRX 레버리지·인버스 ETF 5종이 β×지수보다 얼마나 뒤지는지(드래그)를 보인다. 21·63·252일 값은 지수의 GARCH-t 분산 경로로, 분기 값은 직전 63일 실현분산으로 Avellaneda–Zhang 식(M4-17)에 넣어 낸다.
- **가정:**
  - 지수 이력은 KIS index_daily('2001') = KOSPI200 가격지수 약 600세션 요청분이다(:97). 키가 없으면 합성 KOSPI200이고, 이때 펀드 이력도 합성이라 화면 전체가 SYNTHETIC이다.
  - GARCH(1,1)-t(profile=False) 적합 후 forecast_variance로 일별 분산 경로를 만든다.
  - 직전 분기 값 = letf_drag(β, 직전 63일 분산(ddof 0)을 고정한 경로, fee).
  - 보수 0.64%를 5개 펀드에 같게 하드코딩한다(출처 미기재). 금리 r = 0으로 부른다(:108, :113; M4-17).
- **한계:**
  - [결함] 코스닥150 펀드 233740(코스닥150레버리지), 251340(코스닥150선물인버스)도 KOSPI200 분산을 쓴다. 기초지수가 다르다(data/kis_markets.py:437-439로 2001=KOSPI200 확인). 기초지수 변동성이 28%인데 20%로 계산하면 2배 펀드 분기 drag가 −212bp 대신 −116bp(보수 포함)로 과소하다(가정 변동성 예시)(M4-N1, = NEW-M6-06).
  - [결함] r = 0이라 (1−β)r 항이 빠진다. 63세션, CD 3.21% 기준 빠진 항은 β=+2 −80bp, β=−1 +160bp, β=−2 +241bp다(M4-17). 그래서 인버스 3종(252670, 114800, 251340)은 분기 drag가 1.6~2.4%p 과하게 음수이고 합계 부호가 바뀔 수 있다(β=−1, 변동성 20%: 화면 −116bp, 빠진 항을 더하면 +44.5bp). 선물형 펀드의 배당 항(βq)도 없다(M4-N3, = NEW-M6-07).
  - [오해 소지] 화면은 'last-quarter vol' 드래그를 연구가 찾은 더 나은 기준이라 표시한다(툴팁 :219, 해설 :161-162, 코드 주석 :111-112, README.md:289 'the LETF drag at realised variance'). 그러나 연구가 비교한 것은 직전 분기의 가격 기반 실현 drag 자체다(docs/asset_expansion_study.py:613, :620-621의 last_real). 화면 값은 직전 분기 실현분산을 AZ 식(r=0)에 넣은 다른 양이고 검증되지 않았다. 연구는 122630 한 종목과 지수 대용만 썼는데 화면은 그 판정을 5개 펀드에 붙인다(M4-N2, = NEW-M6-08).
  - 실데이터 검증 불합격: M_E4(52분기, KODEX 레버리지) MAE GARCH 136bp, 0 예측 203bp, 직전 분기 실현 drag 91bp. 실현 대 예측 기울기 0.25, R² 0.03(게이트 기울기 0.7~1.3, R² ≥ 0.5)으로 REVISE다. 화면이 이 판정을 함께 보여준다.
  - 연구의 지수 대용은 배당조정 069500.KS다(asset_expansion_study.py:85, :605). 카드 universe는 '^KS200', 주석은 'price proxy'라 적는다(M4-N10). 이 기준이면 r=0 예측이 분기 약 r·T(약 50~80bp)만큼 drag를 덜 잡는다(유도, 미검증). 평균 실현 drag −203bp/분기의 일부를 설명할 수 있다.
  - 연구의 GARCH 적합 창은 504세션이고 화면은 약 600세션 요청분이다.
- **적용 범위:** 드래그의 방향과 대략적 크기 설명에 쓴다. 분기 괴리 예측, 보유 판단에는 쓰면 안 된다. 코스닥150 펀드와 인버스 펀드 값은 수정 전까지 쓰면 안 된다. M6-14로 따로 적었던 같은 모델을 이 항목에 합쳤다.
- **검증 상태:** 코드로만 확인. 검증 결과 불합격: docs/asset_expansion/cards/M_E4_letf_drag.json REVISE(stats.mae_zero_bp 202.51, mean_realised_drag_bp −202.51; 카드 문장은 '203 bp', '-203 bp'), docs/asset_expansion/results.csv 435-442행. 부품은 독립 검증됐다: letf_drag 식(M4-17, financial_calcs #29), GARCH 예측 재귀(financial_calcs #21). 이 모델 고유의 입력(지수 선택, r, 직전 분기 분산)과 판정 인용을 고정하는 스위트 테스트는 없다. tests/expansion_acceptance.py::test_etf_page_sleeves_use_adjusted_closes_and_survive_their_loss는 069500(비레버리지)만 다룬다. ui/etf_page.py __main__ 263-269는 run_all 밖이고(TA-02) 합성에서 drag가 음수인지만 본다. 빠진 r 항의 크기: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify 안 letf_drag 계산.
- **관련 오류:** 신규 M4-N1(= NEW-M6-06), 신규 M4-N2(= NEW-M6-08), 신규 M4-N3(= NEW-M6-07), 신규 M4-N10, functional_completeness/FC-06, P01-09
- **화면:** ETF 화면: '{name} drag, last-quarter vol'(빨강, 툴팁 'the study's better reference', :218-219), 'GARCH drag 21d/63d/252d', 'Index cond. vol', 'ν', 'Study verdict: GARCH drag'(:220-226); 해설 넷째 문장(:156-162); payload letf; README.md:289

#### 96. M4-19 VIX 기간구조 롤다운 전략(헤지된 VIX ETP 매도)과 ETP 드리프트 모니터

- **위치:** core/ficc/vol_products.py:term_structure:36-41; core/ficc/vol_products.py:rolling_beta:44-52; core/ficc/vol_products.py:roll_down_positions:70-92; core/ficc/vol_products.py:roll_down_backtest:95-117; core/ficc/vol_products.py:etp_drift_monitor:120-139; core/quant/strategies.py:simulate:69-91; docs/asset_expansion_study.py:run_vix:368-388
- **목적:** VIX3M/VIX − 1(콘탱고)이 임계값을 넘으면 VIX ETP를 매도하고 SPY 롤링 베타로 헤지하는 Simon–Campasano(2014) 전략을 연구 카드 S_V1로 검증한다. 기대 ETP 드리프트(−b/2)를 계산한다.
- **가정:**
  - 기간구조 대용 b = VIX3M/VIX − 1(93일 지수). VX1/VX2 선물 곡선이 아니다.
  - 진입 b > threshold, 청산 b < exit. 헤지 비중 = size·β, β는 60일 롤링 OLS(하루 늦게 정렬), 0.25 넘게 움직일 때만 갱신.
  - t 종가의 신호로 t→t+1 비중을 잡는다(같은 종가 체결 가정, strategies.py:72-73).
  - 손익은 simulate: 비중 고정 일일 재조정(K-e), 회전율 × cost_bps. 연구는 5bp/side.
  - 연구는 VIXY와 SPY를 쓴다(모듈 문서는 VXX).
  - 드리프트 모니터: 기대 월 드리프트 = −b/2(선형 VX1→VX2 곡선 휴리스틱), 21세션 = 1개월.
- **한계:**
  - 연구 판정 REJECT: SR_OOS −0.14, 90% CI [−0.58, 0.30], PBO 0.93, MDD −89.8%, 총수익 −74.1%(docs/asset_expansion/results.csv 300-314행).
  - −b/2는 휴리스틱이고 데이터로 검증하지 않았다(financial_calcs.md 6장).
  - VIX 급등(점프)을 일별 베타 헤지로 막지 못한다. 손익 꼬리가 크다.
  - S_V1 카드 venue 문구는 '10 bp per side'인데 실제 비용은 5bp다(asset_expansion_study.py:383-385, 신규 M4-N10).
  - roll_down_backtest와 etp_drift_monitor는 호출처가 없다(자체 검사만).
- **적용 범위:** 연구 기록이다. UI에 없다. 전략 채택 근거로 쓰면 안 된다(REJECT).
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_vol_products(합성 자료에서 진입 수, 헤지 재설정 빈도, 베타 부호 회복을 본다. 정확도 기준값은 없다. 이번 실행 ok). docs/asset_expansion/cards/S_V1_vix_rolldown.json(REJECT). financial_calcs.md 1장·6장: 가격 공식 없음, 데이터 검증 없음.
- **관련 오류:** K-e, 신규 M4-N10
- **화면:** -

#### 97. M4-20 원금보장형 노트(PPN)

- **위치:** core/ficc/structured.py:_vanilla:114-117; core/ficc/structured.py:principal_protected_note:144-193; ui/structuring_page.py:_price:93-97; ui/structuring_page.py:build_structuring_page.worker:262-284; core/ficc/insights.py:narrate_structured:512-543
- **목적:** 무이표채 + 참여율 × ATM 콜로 분해하고 공정가 = 발행가 − 마진이 되도록 참여율을 푼다.
- **가정:**
  - 할인은 UST par 곡선 부트스트랩 하나다(통화 무관, structuring_page.py:269-270). 발행자 신용 스프레드 없음.
  - 콜은 GK(BS), 국내 금리 = 곡선 zero(T), 외국 금리·배당은 평탄 연속 수익률.
  - 평탄 변동성, 유럽형, ACT/365F.
  - 콜 명목 = notional/spot 단위. 페이오프 그리드는 할인하지 않은 만기 값. 통화 라벨은 기본 USD(currency 미전달).
- **한계:**
  - 신용 스프레드가 없어 실제 발행자 노트보다 공정가가 높고 마진이 낮게 나온다.
  - KRW·KOSPI200 상품도 UST 곡선으로 할인한다(D03-V02/financial_calcs/FC-04).
  - FRED 일부 만기 실패 시 끝단 고정 값이 실데이터 라벨로 나온다(D03-V01).
  - 이산 배당, 조기상환, 녹인이 없다(FC-16).
- **적용 범위:** 구조 이해와 독립 BS 수준의 가격 분해에 쓴다. 실제 발행 가격 비교, 원화·KOSPI200 상품 판단에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. financial_calcs.md 3장 #32(독립 BS 대비 차이 0), #34(민감도 부호: vol 20→25% 참여율 0.672→0.562, 배당 2→3% 0.672→0.756, 곡선 −100/+100bp 0.545/0.773). tests/ficc_acceptance.py::test_ppn_fair_below_issue_with_positive_participation; ::test_narratives_state_their_numbers(HEAD PASS). structured.py __main__ 449-470은 스위트 밖(이번 실행 ok).
- **관련 오류:** D03-V02(병합 financial_calcs/FC-04), D03-V01, FC-16, D03-03, D03-04
- **화면:** Structuring 화면 PPN: Fair value, Issue price, Margin, Participation, Greeks, payoff 차트, 다리 표, 헤지 시트, AI kind=structured_product

#### 98. M4-21 역전환사채(RC)

- **위치:** core/ficc/structured.py:reverse_convertible:196-248; core/ficc/curves.py:YieldCurve.annuity:110-112; core/ficc/bonds.py:price_from_curve, cashflows; ui/structuring_page.py:_price:98-102
- **목적:** 연이표 채권 − 풋으로 분해하고 쿠폰을 풀어 공정가 = 발행가 − 마진으로 맞춘다.
- **가정:**
  - 쿠폰 c = (issue − margin + put − 100·DF(T))/(100·annuity(T, 1)), 연 1회(structured.py:213-215).
  - 풋은 GK, 행사가 strike_pct × spot, 단위 100/K.
  - PPN과 같은 곡선·신용·변동성 가정.
- **한계:**
  - 비정수 만기에서 첫 짧은 기간도 쿠폰 전액을 준다. 18m(자체 검사 곡선, vol 10%, K 95%): '연' 쿠폰 3.398%가 0.5y와 1.5y에 전액 지급돼 실제 연율 약 4.53%다(재실행 확인, HEAD 213행). 공정가는 맞지만 'Coupon (p.a.)' 표기가 틀린다(financial_calcs/FC-02).
  - 곡선·신용 문제는 PPN과 같다.
- **적용 범위:** 정수 연 만기의 분해와 쿠폰 산출에 쓴다. 비정수 만기의 쿠폰 비교에는 쓰면 안 된다.
- **검증 상태:** 독립 검증됨. 정수 만기 범위: financial_calcs.md 3장 #33(독립 BS 차이 0, 옵션 없는 극한 = 1y 연 par 3.83706853%), #34(vol 25→35% 쿠폰 9.92→13.89% 등 부호 일치). tests/ficc_acceptance.py::test_reverse_convertible_coupon_beats_the_zcb_rate(HEAD PASS). structured.py __main__ 472-485(스위트 밖). 18m: docs/nautilus_bridge/register_evidence/M4_fx_vol_struct/check1.py 재실행.
- **관련 오류:** financial_calcs/FC-02, D03-V02(병합 financial_calcs/FC-04), D03-V01, FC-16
- **화면:** Structuring 화면 RC: Fair value, Margin, Coupon (p.a.), Greeks, payoff, 다리, 헤지 시트, AI

#### 99. M4-22 이중통화예금(DCD)

- **위치:** core/ficc/structured.py:dual_currency_deposit:251-308; ui/structuring_page.py:_price:103-107; ui/structuring_page.py:build_structuring_page.worker:269-270
- **목적:** 예금 − 기준통화 풋으로 분해하고 증강 단리 수익률을 풀어 공정가 = 100 − 마진으로 맞춘다.
- **가정:**
  - 호가통화 곡선은 화면에서 항상 UST 곡선이다. 기준통화 금리 r_for는 평탄 입력값.
  - 풋 단위 = (1 + y·T)·notional/strike. 마진이 풋 프리미엄(100/df 단위)을 넘으면 그 값으로 줄인다. 그래서 y ≥ 일반 예금 단리.
  - 일반 예금 단리 = (1/DF − 1)/T.
- **한계:**
  - UI 기본 입력(USD/KRW 1350, K 1300, 3m)을 자체 검사 미국채형 곡선에 넣으면 'plain KRW deposit' 3.60%는 실제로 미국 금리이고 증강 수익률은 4.87%다. 원화 평탄 2.6% 곡선이면 4.10%로 77bp 차이다(financial_calcs/FC-04; 재실행 4.8683%/3.6000%). 화면 부제는 'UST par curve'라고만 적고(structuring_page.py:295-297) KRW 라벨과의 통화 불일치 경고는 없다(139-141행은 합성 경고만).
  - 고정 시각, 결제일, 영업일이 없다.
- **적용 범위:** 메커니즘 설명에 쓴다. 원화 상품의 수익률·마진 판단에는 KRW 곡선 연결 전까지 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. tests/ficc_acceptance.py::test_dcd_enhanced_yield_beats_the_plain_deposit(y > 예금 단리는 구성상 성립하는 성질이다. HEAD PASS). structured.py __main__ 487-501(마진 상한, 스위트 밖). financial_calcs.md FC-04 재현(r07 3번). 독립 가격 행은 financial_calcs 3장 표에 없다. 풋 가격 자체는 GK 독립 검증(M4-02). 스위트 테스트는 구성상 성립하는 부등식과 페이오프 순서만 본다. 증강 수익률·공정가 기준값 테스트는 없다.
- **관련 오류:** D03-V02(병합 financial_calcs/FC-04), functional_completeness/FC-03, D03-V01
- **화면:** Structuring 화면 DCD: Fair value, Margin, Enhanced yield (simple), Greeks, payoff, 다리, 헤지 시트, AI

#### 100. M4-23 CMS 10y−2y 스티프너 노트

- **위치:** core/ficc/structured.py:_cms_coupons:311-325; core/ficc/structured.py:steepener_note:328-380; core/ficc/swaps.py:par_swap_rate:83-85; core/ficc/curves.py:YieldCurve.key_rate_shifted:125; ui/structuring_page.py:_price:108-111; ui/structuring_page.py:_render:150-152; core/ficc/insights.py:narrate_structured:527-528
- **목적:** 원금 + clip(레버리지 × (CMS10y − CMS2y), floor, cap) 쿠폰 노트의 공정가와 2s10s 민감도, 헤지를 보여준다.
- **가정:**
  - 각 기간 쿠폰 = 기간 시작 t0의 선도 par 스왑금리(연 1회 고정 다리) 스프레드의 clip. 변동성 0(내재가치).
  - 볼록성·지급 시차 조정 없음. 단일 곡선(UST를 스왑 곡선으로 사용).
  - 쿠폰 발생 = cpn/freq(짧은 첫 기간도 전액, :345).
  - 아무것도 풀지 않는다. 마진 = 발행가 − 공정가.
  - dv01_2s10s = 10y zero +0.5bp, 2y zero −0.5bp 삼각 bump의 전진 차분(:365-366).
- **한계:**
  - floor·cap 시간가치가 빠졌다. 기본 입력(L=4, floor 0, cap 없음, 5y, 자체 검사 곡선): 코드 공정가 86.1175(재실행), Bachelier σ_n 50bp/년이면 +2.80, 70bp/년이면 +4.40. 화면 합성 곡선에서는 +0.77/+1.65이고, 선도 스프레드가 모두 음수라 쿠폰이 전부 0, 공정가 66.09 = 원금 할인값뿐이다(이번 측정). 마진이 그만큼 과대(financial_calcs/FC-01).
  - 경고 문구가 볼록성 편향 방향을 거꾸로 말한다('overstated'). 두 누락 모두 공정가치를 낮춘다(M-01; HEAD 334-336, 372-374).
  - 'Coupon (p.a.)' stat과 해설 'The coupon is … a year'는 첫 기간 예상 쿠폰만 보인다(structured.py:378). 자체 검사 곡선에서 2.04%이지만 일정은 2.04→1.52→1.00→0.64→0.68%, 평균 1.18%다(신규 M4-N11). note에는 평균이 적혀 있다.
  - 비정수 만기·freq>1의 짧은 첫 기간이 전액 발생한다(financial_calcs/FC-02).
  - UST 곡선은 스왑 곡선이 아니다(financial_calcs/FC-05).
  - 페이오프 그리드는 실현 스프레드가 모든 기간 같다고 둔다.
- **적용 범위:** 스티프너 구조와 2s10s 노출 설명에 쓴다. 공정가·마진·쿠폰 수치 판단에는 FC-01 수정 전까지 쓰면 안 된다.
- **검증 상태:** 미검증. 독립 대조에서 결론을 바꾸는 결함(financial_calcs/FC-01, P1). 독립 재계산으로 결함 확인: financial_calcs.md 3장 #35(Bachelier 스프레드 옵션 대비 +2.80~+4.40/100) → financial_calcs/FC-01, 검증자 M-01. 선도 par 금리 계산은 스왑 par 독립 검증(#14)과 같은 경로다. 스위트 tests/ficc_acceptance.py::test_steepener_note_warns_about_convexity는 경고 문구 존재와 부호만 본다(HEAD PASS). structured.py __main__ 503-515(스위트 밖). 이번 재현: 공정가 86.1175, 선도 스프레드 +51.0/+37.9/+25.1/+16.1/+17.1bp, docs/nautilus_bridge/register_evidence/M4_fx_vol_struct_verify/v1.py 4번. 기본 spread vol은 소유자 결정 12.14 대기.
- **관련 오류:** financial_calcs/FC-01, M-01, financial_calcs/FC-02, financial_calcs/FC-05, D03-V01, 신규 M4-N11
- **화면:** Structuring 화면 Steepener: Fair value, Margin, Leverage, Coupon (p.a.)(첫 쿠폰), Greeks(dv01, 2s10s DV01), payoff 차트(x축 bp), 다리 표(쿠폰 일정), 헤지 시트, AI 해설(note 경고 포함)

#### 101. M4-24 구조화 노트 그릭스(유한차분)와 헤지 시트

- **위치:** core/ficc/structured.py:_greeks:120-134; core/ficc/structured.py:hedge_sheet:386-436; core/ficc/swaps.py:swap_dv01:108-112; ui/structuring_page.py:build_structuring_page.worker:273-275; ui/structuring_page.py:_render:167-191
- **목적:** 노트 전체 재평가의 중앙 차분으로 delta·gamma·vega·dv01을 내고, 현물·바닐라·스왑·채권선물 수량으로 바꾼다.
- **가정:**
  - delta = (V(1.01S) − V(0.99S))/2, gamma = 2차 차분(1% 단위), vega = ±1 vol-pt 차분, dv01 = ∓1bp 평행 이동. 풀린 모수(참여율, 쿠폰, 수익률)는 고정.
  - 1차 헤지: delta → 현물/선도 단위, vega → 같은 행사가·만기 콜(풋과 vega 같음), dv01 → 만기 같은 payer 스왑(swap_dv01은 +1bp 손익, payer 양수), 선택 시 계약당 DV01 입력의 채권선물.
  - 스티프너는 DV01 중립 2s10s 플래트너(10y 수취 n10, 2y 지급 n2)를 더한다. 부호와 DV01 중립은 이번 코드 읽기로 확인.
- **한계:**
  - 1%·1bp 국소 근사다. 큰 이동과 교차 감마(spot·vol·금리)가 없다.
  - 헤지 수단 간 상호작용(바닐라의 delta가 현물 헤지를 바꿈)을 반영하지 않는다.
  - 'Futures DV01 / contract'의 뜻이 Bonds 화면과 다르다(BS-32: 65 입력 시 12.28계약 대 Bonds CF 0.8에서 9.82).
  - 곡선·통화 문제(financial_calcs/FC-04, FC-05)가 그대로 헤지 수량에 들어간다.
- **적용 범위:** 1차 헤지 규모의 교육용 계산에 쓴다. 실제 헤지 수량으로 쓰면 안 된다(주문 경로 없음).
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_hedge_sheet_sizes_spot_swaps_and_futures(수량 산술 대조); ::test_ppn_fair_below_issue_with_positive_participation(그릭스 부호); ::test_steepener_note_warns_about_convexity(dv01_2s10s>0, 10y receiver). HEAD PASS. financial_calcs.md 3장 #34(민감도 부호). structured.py __main__ 456-463, 511-513(스위트 밖).
- **관련 오류:** BS-32, D03-V02(병합 financial_calcs/FC-04), financial_calcs/FC-05
- **화면:** Structuring 화면: Greeks stat 줄, 'Hedge sheet (+ buy / pay fixed, − sell / receive)' 표

### 6.5 매크로·PIT·달력

#### 102. 매크로 시트 지표 통계(18개 지표 변화·z·백분위, 브리프 무버 순위)

- **위치:** core/ficc/macro.py:_row:128-139; core/ficc/macro.py:_weekdays:142-147; core/ficc/macro.py:_load:150-158; core/ficc/macro.py:macro_sheet:202-225; core/ficc/macro.py:_rel_1d:231-234; core/ficc/macro.py:daily_brief:237-252; core/ficc/macro.py:weekly_brief:255-270; core/ficc/data.py:Series.change:104-108
- **목적:** 18개 교차자산 지표의 최신값, 1d/1w/1m/3m 변화, 1년 z-점수와 백분위를 계산한다. Macro 화면과 일간·주간 리포트(로컬 서술, Claude 심층 분석)의 입력이다. 맥락 전용이다.
- **가정:**
  - 변화는 달력 기간이 아니라 관측 개수(1/5/21/63개) 차이다(macro.py:42, data.py:104-108).
  - 주말 행은 지운다(:142-147). DFF 같은 7일 시리즈도 영업일 개수로 센다. 미국 공휴일 결측은 그대로 둔다.
  - z-점수는 최근 252개 관측(현재 포함)의 모집단 표준편차(ddof 0)로 나눈다. 백분위는 현재값 이하 비율(현재 포함)이다(:133-139). 분포 가정은 없다.
  - FRED 퍼센트 시리즈(unit pct·bp)는 소수로 바꾼다(×0.01). 레벨·FX는 원 단위다(:131-132). 단위 판단은 source=='FRED'에 기댄다.
  - 각 행은 자기 마지막 관측일 기준이다. 시트 as_of는 행 마지막 날짜의 최댓값이다(:223).
  - source='auto'는 지표별로 SYNTHETIC으로 대체하고 synthetic_ids·note에 적는다(:215-219).
  - 무버 순위는 상대 1일 변화 chg/(last−chg)로 금리와 레벨을 한 척도에 섞는다(:231-243).
  - 비용·연율화는 해당 없음.
- **한계:**
  - as_of가 가장 최신 행을 따른다. 다른 행이 며칠 묵어도 시트는 최신처럼 보인다. 표에 행별 날짜 열이 없다(ui/macro_page.py:43). 감사 재현: 지표를 10-23 기준으로 읽는데 달러는 10-16 데이터였다(D04-01). 합성 행이 섞이면 as_of가 합성 날짜가 된다(D03-02). 스크래치 재현(v1_macro_sheet.py): DTWEXBGS를 5관측 잘라도 as_of는 2026-10-28, 달러 행은 2026-10-21.
  - 발표 시각·수신 시각·빈티지가 없다(D04-02). 키 없는 FRED CSV라 최신 빈티지만 온다(data_flow F10).
  - 관측 개수 변화라 시리즈마다 실제 기간이 다르다(주간 발표 DTWEXBGS, 휴일 결측).
  - 252 관측 미만이면 짧은 창으로 z를 낸다. note만 남긴다(:220-222). 레벨 z라 추세 있는 시리즈는 한쪽으로 치우친다.
  - 상대 1일 변화는 분모 last−chg가 0 근처인 행에서 폭주한다. 0을 오가는 T10Y2Y(2s10s)가 2bp만 움직여도 rel_1d 2.0, 10y 10bp 이동은 0.0244다(스크래치 rel1d.py). 'movers_1d' 순위를 스프레드 한 행이 차지할 수 있다(:231-234, :243).
  - Series에 단위 필드가 없다. 새 소비자는 100배 오류를 낼 수 있다(D03-06).
  - ddof 0과 ddof 1의 차이는 0.2%(√(252/251))로 무시할 만하다(스크래치 확인).
- **적용 범위:** 맥락 표시와 리포트 문장 생성 전용이다(T-CTX-01; context_log.py:77 PROTECTED_MODULES). 북·신호·엔진·리스크 입력으로 쓰면 안 된다. 날짜 정렬된 시점 판독이 필요하면 PIT 저장소 경로(맥락 로그)를 써야 한다.
- **검증 상태:** 코드로만 확인. run_all 테스트는 모양만 단언한다: tests/ficc_acceptance.py::test_macro_rows_are_bounded_and_regimes_are_from_the_sets(z ∈ [−6, 6], pct ∈ [0, 1], 집합 소속), ::test_macro_briefs_are_json_payloads(키 개수·JSON 직렬화), ::test_macro_sheet_offline_auto_is_loudly_synthetic_and_fred_raises(합성 표시·예외). 모두 cloud run2 PASS, 합성 데이터. 산식 숫자 단언은 core/ficc/macro.py:295-300 자체 검사(FRED 환산 0.043, chg_1d 0.002, pct_1y 1.0)뿐이고 run_all 밖이다(TA-02). 실데이터 기준값 대조 없음. financial_calcs.md 범위 밖. 스크래치 work/M5_macro_pit/v1_macro_sheet.py, work/M5_macro_pit_verify/rel1d.py.
- **관련 오류:** D04-01(P2), D03-02(P2), D04-02(P2), D03-04(P2, AI 페이로드), D03-06(P3), D03-08(P3), D0405-T1(P3), TA-02(P2), 신규 관찰(rel_1d 분모 0 근처 폭주, 감사 행 없음)
- **화면:** Macro 화면 'Macro sheet' 뷰(ui/macro_page.py:109-128 표, :160-167 타일·z 색); 'Daily market commentary'·'Weekly rates and FX note'(core/ficc/insights.py:380 narrate_daily_brief, deep_analysis 페이로드)

#### 103. 매크로 서술적 판독(Descriptive read, 5개 임계값 규칙)

- **위치:** core/ficc/macro.py:_trend:164-167; core/ficc/macro.py:_regime_from:170-196; core/ficc/curves.py:_regime:313-322
- **목적:** 커브(bull/bear 스티프너·플래트너, parallel), 위험(risk-on/off), 달러(strong/weak/range), 기대인플레이션·실질금리(rising/falling/stable) 단어를 붙인다. 'not a regime model (P19)' 라벨을 단다.
- **가정:**
  - 커브: DGS10·DGS2의 20관측 변화. \|Δ기울기\| ≥ 5bp면 스티프/플랫, 10y 이동이 5bp 미만이면 2y·10y 평균 방향으로 bull/bear. 아니면 \|Δ10y\| ≥ 5bp면 parallel(curves.py:313-322).
  - 위험: VIX z와 HY OAS z의 평균. > 0.75 risk-off, < −0.5 risk-on. 비대칭 임계값이다(:180-181).
  - 달러: DTWEXBGS 21관측 상대 변화 ±1.5%(:183-185).
  - 인플레·실질금리: T10YIE ±10bp, DFII10 ±15bp(21관측, :187-188).
  - 시리즈별 단위 보정(FRED면 ×0.01)을 따른다(:171-175).
  - 추정·확률·평활·잠재 상태가 없다. 임계값은 사양 고정값이다.
- **한계:**
  - 임계값의 근거·민감도 자료가 없다. 경계 근처에서 단어가 쉽게 바뀐다.
  - 입력 날짜가 서로 다를 수 있다. 감사 재현에서 달러 판독이 10-16 데이터였다(D04-01).
  - 합성 입력이 판독을 결정해도 칩에 표시가 없다(D03-02).
  - 시리즈가 없으면 변화를 0.0으로 본다(:174-175). macro_sheet 경로에서는 행 생성이 먼저 실패해 도달하지 않는다(코드 확인).
- **적용 범위:** 표시·리포트 문장 전용이다. 레짐 상태로 쓰거나 노출을 바꾸면 안 된다(P19). v2 변동성 라벨(calm…stressed)과 같은 자리에 두면 안 된다.
- **검증 상태:** 코드로만 확인. 숫자 단언은 core/ficc/macro.py:300(_regime 8bp 1사례)과 :303-314(FRED 퍼센트 대 SYNTHETIC 소수 혼합 커브 2사례) 자체 검사뿐이고 run_all 밖이다(TA-02). run_all 테스트 tests/ficc_acceptance.py::test_macro_rows_are_bounded_and_regimes_are_from_the_sets, ::test_curve_report_uses_allowed_regime_and_shape_strings는 단어가 허용 집합에 드는지만, tests/macro_m6_context.py::test_ctx_01_regime_read_is_relabelled_descriptive는 라벨 문구와 R-06 라벨과의 분리만 단언한다(PASS). risk·dollar·inflation·real 임계값 규칙은 어떤 테스트도 숫자로 누르지 않는다. 임계값의 실데이터 타당성 검증은 없다.
- **관련 오류:** D03-02(P2), D04-01(P2), D03-04(P2), TA-02(P2)
- **화면:** Macro sheet 뷰 판독 칩(ui/macro_page.py:75-86 read_row, :160); 리포트 페이로드 'regime' 키(macro.py:248)

#### 104. PIT 저장소와 as-of 읽기(pit_value, pit_window, 순위, 분쟁 판정)

- **위치:** core/ficc/pit.py:PITStore:217-315; core/ficc/pit.py:PITStore.rows:252-268; core/ficc/pit.py:PITStore.append:284-302; core/ficc/pit.py:_visible:321-322; core/ficc/pit.py:_rank:325-328; core/ficc/pit.py:_best_per_obs:331-337; core/ficc/pit.py:_dispute:362-375; core/ficc/pit.py:pit_value:378-420; core/ficc/pit.py:pit_last:423-431; core/ficc/pit.py:pit_window:434-447; core/ficc/pit.py:returns_excluding_rolls:455-463; core/ficc/pit.py:data_snapshot_id:466-471; core/ficc/pit.py:reconcile:611-628; core/ficc/contracts.py:read_input:463-488
- **목적:** 매크로 v2의 모든 acting·risk_model 입력을 결정 시각과 지식 시각 기준으로 읽는다. 같은 관측일에서 가장 좋은 행을 고른다. 미래 정보 차단의 핵심 장치다.
- **가정:**
  - 보이는 행: available_at_utc ≤ decision_utc 그리고 retrieved_at_utc ≤ knowledge_utc(:321-322).
  - 순위: value_status 등급(official_close > revised > first_release > vendor_close …) → 공급원 우선순위 → 최신 available → 최신 retrieved(:27-28, :325-328). 가장 늦은 관측일을 쓴다(:407).
  - close형 acting 읽기는 require_session과 같은 관측일만 받는다. 이전 종가로 대체하지 않는다(:401-404). official_close가 아니면 provisional_intraday로 거부한다. 백테스트는 선언한 공급사의 vendor_close를 허용한다(:410-414).
  - 합성·auto 값은 pit_value에서 context 역할만 받는다(:408-409).
  - 행은 고치지 않는다. 내용 해시로 중복을 지우고 첫 수신 시각을 유지한다(:284-302).
  - 분쟁: 지수는 tolerance index_bp, 주식은 정확 일치. 공식값을 쓰고 자동 수정하지 않는다(:362-375).
  - read_input이 계약 검사(예: abs_daily_return_max 0.30)와 발행 일정 기반 stale 판정을 더한다(contracts.py:463-488).
- **한계:**
  - 읽을 때 해시와 유한성을 다시 검사하지 않는다. 손상·편집 행이나 JSON NaN이 경고 없이 결정에 들어간다(C01-10, pit.py:263).
  - 창 읽기 pit_window는 합성·auto 행을 거르지 않고 최신성도 보지 않는다(:434-447). 합성 거부는 마지막 값을 읽는 pit_value에만 있다(:408-409). corr63·fx_hedge_credit 창(risk_layer.py), 거부 북 창(refusal.py:75-79), FORWARD-SIM 창(forward_sim.py:373-374)이 이 경로다. vt 창은 _close_ok가 따로 막는다(risk_layer.py:324-327). 지금은 합성 행을 저장하는 생산 코드가 없어 잠재 결함이다(코드상).
  - 공급사 간 대조는 같은 시리즈의 공식 대 공급사뿐이다. reconcile은 운영 호출이 없다(V01-02).
  - 운영 수집기가 연결되지 않았다. Services.ingest 기본값 None(macro_daily.py:120, :457)이고 _provider_rows에 pit_store=를 넘기는 생산 코드가 0곳이다(data.py:450-494; grep 재확인). 라이브 저장소를 앱이 채우지 않는다.
  - 레지스트리는 ALFRED history_channel을 선언하지만(series_registry.yaml:173, PCEPILFE) core에 ALFRED 코드가 없다(grep). FRED 이력으로 채우면 수정값이 first_release로 찍혀 백테스트에 사후 값이 들어간다(data_flow F10).
  - 시리즈 파일 전체를 메모리로 읽는다. 대용량 성능은 미측정.
- **적용 범위:** 매크로 v2(M1-M10)의 결정 입력 읽기 전용이다. Macro sheet 화면은 이 경로를 쓰지 않는다. 외부에서 편집될 수 있는 저장소에는 손상 검사 없이 쓰면 안 된다. 합성 행이 섞일 수 있는 저장소에서 창 계산 결과를 믿으면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_pit.py 24 PASS / 7 NOT_RUN(cloud run2, 수 재확인). PASS: ::test_prov_01_store_read_trace, ::test_syn_01_synthetic_rejected_for_acting_allowed_for_context, ::test_bar_02_dispute_is_not_a_failure_and_vendor_missing, ::test_role_01_counters_halt_scope_and_role_actions, ::test_xmkt_01_cross_market_data_clause, ::test_h10_01_dexkous_never_read_by_production. NOT_RUN: ::test_fix_01_regeneration_at_level_1_tolerance_refdata, ::test_g_post_01_m1_data_rows_refdata. 감사 c01_v01(C01-10) monkeypatch 재현. 매크로 실데이터 골든 재현 0행(감사 보고서 7.3). pit_window 합성 미거부는 코드 읽기(pit.py:434-447).
- **관련 오류:** C01-10(P2), V01-02(P3), D05-03(P3), D04-03(P3), 신규 관찰(pit_window 합성·auto 미거부, 잠재, 감사 행 없음)
- **화면:** 직접 화면 없음. Overlay state 뷰의 inputs 표·data snapshot 칩(ui/macro_state_panel.py:180-202, :431-449)과 모든 macro_state 숫자의 원천

#### 105. 타임스탬프·값 상태 부여 규칙(stamping, 종가 10분 격리)

- **위치:** core/ficc/pit.py:stamp_close:477-513; core/ficc/pit.py:stamp_bar:516-523; core/ficc/pit.py:stamp_release:526-546; core/ficc/pit.py:stamp_quote:549-555; core/ficc/pit.py:ingest:558-594; core/ficc/pit.py:put_derived:638-656; core/ficc/pit.py:check_fixture:731-756; core/calendars/clocks.py:close_stamp:311-331
- **목적:** 받은 값마다 obs_utc, available_at_utc, value_status를 붙인다. 무엇을 종가로 인정할지 정한다.
- **가정:**
  - 종가: close_print_bound_utc+10분 이후 받은 값만 종가다. 검증된 1차 공급원이면 official_close, 아니면 vendor_close(:495-505). 그 전이면 provisional_intraday 스냅숏(:496-501).
  - 거래소 프린트가 경계보다 늦으면 저장하지 않고 플래그를 낸다(:492-494). 예정 종가보다 이른 프린트는 장중값으로 거부한다(clocks.py:325-327).
  - 시가=고가=저가=종가이고 거래량 0인 세션 행은 stale carry 플래그다. 저장하지 않는다(:488-491). 봉에서 종가를 만들지 않는다(:484-485).
  - 합성·auto 행은 최대 vendor_close로 찍는다(:503-504).
  - 발표형: 게시 시각이 있으면 published, 없으면 레지스트리 발행 시각(calendar_bound). 그보다 일찍 받으면 provisional(:533-542).
  - 파생: available_at은 입력의 최댓값, 상태는 가장 약한 입력(:645-646).
  - 견적 스냅숏: quote_utc = 수신 시각(:580-582).
- **한계:**
  - 견적 경로가 수신 시각을 관측 시각으로, 출처를 'published'로 찍는다(D05-03, pit.py:549-555, :580-582). 생산 호출 0곳이라 잠재 결함이다.
  - same_day 규칙이 달력을 읽지 않던 문제(CAL-12)는 d865c7f에서 고쳤다. publication.py:157이 business_day를 먼저 불러 미서명·범위 밖 달력을 거부한다. 그날이 영업일인지는 여전히 보지 않는다.
  - dry run은 캐시 파일 mtime을 수신 시각으로 쓴다(macro_daily.py:1412). 복제·압축 해제만으로 장중 봉이 종가가 될 수 있다(C01-03).
  - 경계 시각 자체가 미서명 달력에 달려 있다. 지금 라이브 스탬프는 모두 CalendarUnsigned로 거부된다.
- **적용 범위:** PIT 저장소에 들어가는 모든 행. 생산 호출은 dry run의 ingest(macro_daily.py:1413)뿐이다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_pit.py::test_close_01_data_clauses_quarantine_and_stamping, ::test_bar_01_a_bar_or_stale_carry_is_never_a_close, ::test_print_01_circuit_breaker_print_is_never_a_close, ::test_fix_01_post_close_fixtures_only, ::test_vix_01_close_timing_by_channel, ::test_history_cache_b_marks_a_running_bar_provisional, tests/macro_m1_calendars.py::test_print01_intraday_print_is_never_a_close, ::test_cal01_same_day_schedule_needs_its_signed_calendar(CAL-12, d865c7f) (PASS). NOT_RUN: tests/macro_m1_pit.py::test_print_01_real_kospi_close_refdata, tests/macro_m1_calendars.py::test_print01_real_kospi_close_2026_03_09.
- **관련 오류:** D05-03(P3), CAL-12(P3, d865c7f 반영, 서명 대기), C01-03(P2, TA-04 병합), K-h
- **화면:** 간접: Overlay state inputs 표의 value_status 열, dry run 빨간 칩

#### 106. 월간 달력 오프셋 산술(YoY·MoM·3개월 평균)

- **위치:** core/ficc/pit.py:calendar_change:675-683; core/ficc/pit.py:yoy:686-687; core/ficc/pit.py:mom:690-691; core/ficc/pit.py:rolling_mean:694-700; core/ficc/pit.py:vendor_status_across_gap:703-706; core/ficc/lag_audit.py:assert_no_positional_shift:126-144
- **목적:** 월간 지표 변화를 위치 이동이 아닌 달력 오프셋으로 계산한다. 끝점이 없으면 NaN과 플래그를 낸다.
- **가정:**
  - 월 키는 그 달 1일이다. 변화는 단순 비율 b/a−1 또는 차분이다.
  - YoY는 창 안의 결측에 영향받지 않는다. rolling_mean은 구성원 하나라도 없으면 NaN이다.
  - 빈티지 선택은 호출자의 PIT 읽기가 한다.
  - 간격 있는 시리즈의 위치 이동은 거부한다(lag_audit.py:126-144).
- **한계:**
  - 빈티지 이력이 없으면 수정값 기반이다(data_flow F10).
  - 레지스트리 missing_months(2025-10-01; CPIAUCSL·CPILFESL·UNRATE, series_registry.yaml:651-653)가 Sahm 등 창 전체를 NaN으로 만든다. 의도된 엄격 전파다.
  - 계절조정 여부는 시리즈 선택에 달려 있다.
- **적용 범위:** hedge_state의 근원 PCE YoY(risk_layer.py:684-692), 맥락 로그의 Sahm·UNRATE·PAYEMS·Taylor 계산. 일간 시리즈에는 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_pit.py::test_miss_01_calendar_offsets_and_the_october_gap, ::test_lag_02_positional_shift_rejected_on_gapped_series, tests/macro_m6_context.py::test_ctx_02_calculators (PASS). NOT_RUN: tests/macro_m1_pit.py::test_miss_01_cpi_yoy_3_353_refdata.
- **관련 오류:** -
- **화면:** Overlay state 'Context log' 타일, Hedge 칩(core_pce)

#### 107. 세션 시계와 교차시장 사용 가능 시각(결정 시각, gap_sessions)

- **위치:** core/calendars/clocks.py:_close_time_of:116-148; core/calendars/clocks.py:is_session:187-205; core/calendars/clocks.py:next_session/prev_session/sessions_between:208-229; core/calendars/clocks.py:decision_time_utc:235-245; core/calendars/clocks.py:_bound_seconds:248-258; core/calendars/clocks.py:close_print_bound_utc:261-267; core/calendars/clocks.py:session:270-308; core/calendars/clocks.py:cross_market_usable:337-344; core/calendars/clocks.py:latest_usable_close:347-356; core/calendars/clocks.py:kr_open_gap_session:362-374; core/calendars/clocks.py:gap_sessions:377-386; core/calendars/clocks.py:completeness_check:389-401; core/calendars/store.py:arm_precondition:505-512; core/calendars/adapter.py:CalendarClocks
- **목적:** 시장별 결정 시각(예정 종가 + 프린트 경계), 세션 여부, 교차시장 종가 사용 가능 여부, KR 개장 갭 세션과 그 사이 미국 세션 수를 계산한다. PIT 스탬프·지연 감사·재ARM 계산의 기준이다.
- **가정:**
  - 결정 시각 = 예정 종가 + 경계(KR random-end 30초 등, US close_print_bound_s, JP·CN·HK·TW 0초)(:248-267).
  - 소유자 서명 YAML이 유일한 원천이다. 상수 시각이 없다. 미서명·커버리지 밖이면 예외(fail closed).
  - 비세션이면 NotASession. 앞뒤로 굴리지 않는다(:242-243).
  - 교차시장: bound(other, D) + buffer 60초 < 결정 시각일 때만 쓴다. HK 같은 날 종가는 항상 불가(:341-342).
  - 시간대 변환은 zoneinfo(서울 DST 없음, 뉴욕 DST 반영).
  - KR 토요일 세션은 saturday_sessions_before 이전만, 수능일은 csat 창(:122-128, :202-204).
  - CRYPTO는 24/7, d+1 00:00Z 종가, 경계 0초(:189-191, :238-240).
- **한계:**
  - 배포된 달력 16개가 모두 미서명이다. 지금 라이브 실행은 모두 거부된다(calendars.md 0절).
  - d865c7f 이전 초안에는 KRX 2026-06-03·07-17 휴장(CAL-01), 2027 대체공휴일 2일(CAL-02), 2027 수능일(CAL-03)이 빠져 있었다. d865c7f에서 미서명 초안에 넣었다. 서명 전까지 라이브 실행은 계속 거부된다.
  - d865c7f의 행 대조는 공식 사이트를 열지 못해 검색 색인 발췌로만 했다. 154행 중 공식 확인 93, 공지 전 18, 확인 실패 42, 불일치 1(SIFMA 2026-04-03, 고침)이다. 소유자가 서명할 때 원문과 대조한다(docs/nautilus_bridge/OWNER_RULINGS_LOG.md, docs/calendar_signoff/SIGNING_KIT_2026-10-28.md).
  - CBOE·ECOS·HKEX 등 7개 파일은 여전히 빈 골격이다(CAL-06). KRX·NYSE의 covers.from이 서명 대상 기간보다 짧다(CAL-11).
  - 세션 이동을 하루씩 반복 호출로 센다. 긴 구간은 느리다(미측정).
  - completeness_check는 운영 호출이 없다(D12-07; core/calendars/__init__.py:212는 이름 목록뿐).
- **적용 범위:** 매크로 v2 결정 시각, PIT 스탬프, 지연 감사, 이벤트 창, 북 재ARM 세션 계산. 레거시 core/calendars/__init__.py(KRX.json)와 별개다. 레거시는 UI·dry run에서 쓴다(CAL-10).
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_calendars.py 22 PASS / 0 FAIL / 5 NOT_RUN(d865c7f, 이번 재실행). PASS: ::test_close01_decision_time_and_bound, ::test_close02_effective_dated_clocks, ::test_gap_sessions_values, ::test_tz01_cross_time_zone, ::test_tz02_event_to_kr_open_gap_session, ::test_xmkt01_same_instant_closes, ::test_sat01_saturday_sessions_and_completeness, ::test_cal02_known_2026_2027_rows_present(CAL-01·02·03·10 행), ::test_cal01_unquoted_time_refused_at_load(CAL-13), ::test_cal01_signed_utc_must_be_iso_utc(M-4), ::test_cal01_manifest_pins_signed_utc_and_statement(CAL-14), ::test_cal02_deadline_clock_injected(CAL-08). NOT_RUN: ::test_close02_on_the_real_signed_files, ::test_sat01_real_kospi_completeness_and_variance_ratio, ::test_cal02_2027_files_signed_before_2026_11_01. 데이터 독립 대조: docs/audit/2026-10-27/calendars.md 2-4절(NYSE 2025-27은 exchange_calendars 4.13.2 XNYS와 일치, KRX·SIFMA·FED 오류 발견), d865c7f 출처 대조 docs/calendar_signoff/evidence/source_check_2026-10-28.json.
- **관련 오류:** CAL-01(P1, D12-08 병합), CAL-02(P1), CAL-03(P2), CAL-08(P2), CAL-10(P2), M-2(P2), CAL-13(P3), CAL-14(P3), M-4(P3) (d865c7f 반영, 서명 대기); CAL-06(P2), CAL-11(P2), M-3(P2, 레거시), D12-07(P2)
- **화면:** Overlay state 결정 세션 칩·Gap 칩(ui/macro_state_panel.py:380-381), 'Live' 실행 비활성 툴팁. 간접적으로 모든 macro_state

#### 108. 발행 시각과 결측 발표(stale) 판정

- **위치:** core/calendars/publication.py:schedule_of:111-126; core/calendars/publication.py:publication_instant:141-182; core/calendars/publication.py:source_skipped:199-208; core/calendars/publication.py:next_expected_obs:211-222; core/calendars/publication.py:add_publication_bdays:225-234; core/calendars/publication.py:usable_at:240-271; core/calendars/publication.py:latest_usable_obs:274-285; core/ficc/contracts.py:stale_deadline_utc:404-408; core/ficc/contracts.py:is_stale:411-421; core/ficc/contracts.py:on_input_failure:427-460
- **목적:** 발표형 시리즈(H.15, H.10, BLS, BEA, Treasury, VIX)의 공개 시각과 다음 예정 관측을 계산한다. 기한 + 유예 영업일을 넘기면 stale로 보고 역할별 fail-closed 동작을 정한다.
- **가정:**
  - 규칙 5종(next_bday_after_obs, monday_after_week, same_day, channel_posting_time, release_calendar)과 서명된 publication_schedules 행을 쓴다.
  - same_day도 발행처 달력이 서명돼 있고 그날을 덮어야 한다(publication.py:157, d865c7f).
  - 소스가 정당하게 건너뛴 날은 source_skipped 목록으로 뺀다.
  - KR 결정에서 미국 날짜 자료는 D ≤ K−1만 쓴다(:256-261).
  - 관측 나이가 아니라 발행 일정으로 stale을 판정한다. 일정에 예정 시각이 없으면(as-posted, 라이브 견적) stale이 될 수 없다(contracts.py:411-421).
- **한계:**
  - 미서명이라 지금은 모두 CalendarUnavailable → missing이다.
  - source_skipped의 Good Friday가 DGS10만 다룬다(CAL-09).
  - d865c7f에서 SIFMA 2026-04-03 오분류(CAL-04, 휴장 → 12:00 조기폐장)와 FED 2027-12-31 누락(CAL-05)을 미서명 초안에서 고쳤다. same_day 규칙이 달력을 읽지 않아 미서명 달력에서도 시각을 내던 문제(CAL-12)도 고쳤다. 다만 그날이 영업일인지는 여전히 보지 않는다(business_day의 반환값을 쓰지 않음).
  - BLS·BEA 발표일은 소유자 입력(release_dates)이다.
  - 커버리지 경보(warn 60/page 20)와 calendar_change 거버넌스 이벤트가 운영에 연결되지 않았다(CAL-07).
- **적용 범위:** acting·risk_model 입력의 stale 판정, lag_audit의 usable_at, hedge_state의 missed_releases. context 입력은 stale 판정을 건너뛴다(contracts.py:480-481).
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_calendars.py::test_publication_h15_h10_vix_avail_timing, ::test_cal01_same_day_schedule_needs_its_signed_calendar(CAL-12, d865c7f), ::test_cal02_known_2026_2027_rows_present(SIFMA·FED 행), tests/macro_m1_pit.py::test_h15_01_strict_h15_and_treasury_channel, ::test_h10_02_strict_h10_publication, ::test_stale_01_schedule_aware_clauses_and_local_smoke, ::test_avail_01_golden_availability_table_on_synthetic_calendars (PASS). NOT_RUN: ::test_stale_01_g_stale_01_reference_table_refdata, ::test_avail_01_official_calendars_are_owner_signed. calendars.md 4.3-4.4절 데이터 대조.
- **관련 오류:** CAL-07(P2), CAL-09(P3), CAL-04(P3)·CAL-05(P3)·CAL-12(P3)(d865c7f 반영, 서명 대기)
- **화면:** Overlay state 입력 상태(stale, stale_missed_release)와 경보

#### 109. 연율화 일수 표(ANNUALISATION_DAYS)

- **위치:** core/calendars/clocks.py:ANNUALISATION_DAYS:30; core/calendars/clocks.py:annualisation_days:33-34
- **목적:** 시장별 연율화 일수(CRYPTO 365, 그 외 252)를 한 곳에 둔다.
- **가정:**
  - 주식·금리 시장은 연 252세션, 24/7 암호화폐는 연 365봉이다.
  - √N 스케일(수익률 독립·동분포)을 전제한다.
- **한계:**
  - 생산 코드 호출이 0곳이다(grep: 정의와 tests/macro_m9_lab.py:530, :537뿐). 실제 경로는 각자 252를 쓴다: validate.TRADING_DAYS(validate.py:48), risk_layer.sma_vol(규칙 저장소 vol_target.annualisation_days 252), sleeves.ANN_DAYS(sleeves.py:38), context_log.rv21_series, history.TRADING_DAYS(history.py:47).
  - 그래서 암호화폐 일봉이 Quant Lab·Signals·MC·게이트에서 252로 연율화되어 변동성·Sharpe가 약 17% 낮다(√(252/365)=0.831, D12-11/M-03). Crypto 화면만 365로 따로 바꾼다(ui/crypto_page.py:75-76).
  - 같은 이유로 CRY-1 대조 실험의 SR·ΔSR도 √252다(docs/techfund_study.py:424-425).
  - √N 스케일은 자기상관·변동성 군집을 무시한다.
- **적용 범위:** 매크로 v2에는 CRYPTO 북이 없다(M10 연기). 표는 참조값일 뿐이다.
- **검증 상태:** 코드로만 확인. tests/macro_m9_lab.py::test_t_crypto_01_clock_annualisation_and_no_crypto_sleeve(PASS, 상수 값과 비율 산술만 단언). 독립: financial_calcs.md M-03(BTC 합성 3년, σ 80%: ann_vol 0.4724 대 0.5686, Sharpe 0.427 대 0.514).
- **관련 오류:** D12-11(P1, M-03 병합), M-2(P2, d865c7f 반영: 같은 테스트가 이제 미서명 픽스처를 쓴다)
- **화면:** 직접 표시 없음. 영향 화면: Quant Lab 'Vol (ann.)'·'Drift (ann.)', Signals Sharpe, Strategy Lab 판정, Model cards의 CRY-1 줄

#### 110. 독립 지연 감사(lag_audit)

- **위치:** core/ficc/lag_audit.py:usable_at:51-60; core/ficc/lag_audit.py:_audit_one:63-103; core/ficc/lag_audit.py:lag_audit:106-123; core/skills/macro_daily.py:lag_audit:537-563; core/quant/risk_layer.py:_hedge_state:701-712
- **목적:** pit_value와 별도로 달력·레지스트리에서 사용 가능 시각을 다시 계산한다. acting·risk_model·forward_sim 입력의 미래 정보 위반을 찾는다. 백테스트는 LookAheadError, 운영은 acting이면 해당 북 OPS HALT(운영자 재ARM), risk_model이면 hedge credit off.
- **가정:**
  - 검사: available ≤ decision, retrieved ≤ knowledge, usable_at ≤ decision, available ≥ 발행 시각(published 예외), 교차시장 bound + 60초, close형 acting은 official_close·session_date 일치·close + 10분 이후 수신.
  - 파생 행은 lineage가 주어질 때만 입력까지 내려간다(:68-70).
  - context 역할은 검사하지 않는다(:117-118).
- **한계:**
  - 스탬프와 감사가 같은 clocks 객체를 쓴다. 달력 자체 오류는 잡지 못한다(예: d865c7f 전 초안의 CAL-01, CAL-03).
  - 파이프라인 호출이 lineage를 넘기지 않는다(macro_daily.py:541). 파생 acting 입력은 자기 시각만 검사된다.
  - 감사 대상은 각 입력의 마지막 값(ctx.state['inputs'])뿐이다(macro_daily.py:539-541). vt σ 창, corr63 창, NAV 창 같은 pit_window 행은 감사하지 않는다(코드상).
  - 백테스트에서 close형 acting 값은 공급사 일치 없이 vendor_close면 통과한다(lag_audit.py:92-93). pit_value는 선언 공급사 일치를 요구한다(pit.py:410-414). 두 검사의 기준이 다르다.
  - LIVE_QUOTE·AS_POSTED·DERIVED 일정은 usable_at이 None이라 스탬프를 그대로 믿는다(:57-58).
- **적용 범위:** 매크로 v2 결정마다(macro.lag_audit 단계)와 hedge_state 내부. 매크로 시트·Strategy Lab 등 v2 밖 경로는 대상이 아니다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_pit.py::test_lag_01_independent_audit_raises_or_halts, ::test_lag_02_positional_shift_rejected_on_gapped_series, tests/macro_m2_risk.py::test_lag_02_shifted_input_changes_vt_and_trips_lag_audit, tests/macro_m1_integration.py::test_stamping_and_lag_audit_on_the_calendar_adapter, tests/macro_m1_books.py::test_lag_audit_and_schema_failure_need_operator_rearm (PASS). NOT_RUN: tests/macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata.
- **관련 오류:** CAL-01, CAL-03(d865c7f 반영, 서명 대기. 같은 달력에 기대 감사가 달력 오류를 못 잡는 구조는 남는다), C01-03(mtime 수신 시각은 close+10분 검사를 통과할 수 있음), 신규 관찰(창 행 미감사·백테스트 공급사 기준 불일치, 감사 행 없음)
- **화면:** Overlay state Flags 'lag audit: n checked, k violation(s)' 칩(ui/macro_state_panel.py:382-383), HALT 배너

#### 111. R-06 시장 변동성 목표(vt, SMA20)

- **위치:** core/quant/risk_layer.py:sma_vol:235-242; core/quant/risk_layer.py:ESTIMATORS:258; core/quant/risk_layer.py:sigma_history:299-311; core/quant/risk_layer.py:_close_ok:324-327; core/quant/risk_layer.py:market_vol_target:330-415; core/quant/risk_layer.py:vt_for_book:418-431; core/quant/risk_layer.py:vol_state:434-457; core/skills/macro_daily.py:vol_and_overlays:603-632; data/macro/rules_v2.0.0.json:vol_target
- **목적:** vt = min(1.0, 목표/σ). σ는 직전 20개 단순수익률의 표준편차(ddof 1) × √252다. KR 목표 0.20, US 0.15. specification 북 gross의 기본 배수다.
- **가정:**
  - 단순수익률, ddof 1, 평균 차감, 252 연율화(규칙 저장소 vol_target.annualisation_days).
  - 결정 세션 종가가 official_close여야 한다(백테스트는 선언 공급사 vendor_close).
  - 창은 세션을 거꾸로 걷는다. stale carry 날은 건너뛰고 창을 늘린다. 그 밖의 결측 세션은 fail closed(F-3).
  - 20개 미만이면 한 번도 ARMED 아닌 북만 warm-up 1.0, 아니면 missing. σ = 0이나 비유한이면 missing.
  - cap 1.0 영구, floor 없음. 추정기는 sma20만 허용한다(:258, :346-348).
  - recommended 북은 R-06 카드 PASS 전까지 vt = 1.0이다(macro_daily.py:632). fail_closed에 이전 값이 없으면 vt 0.0을 쓴다(:632, :671).
- **한계:**
  - 20일 단순 이동창이다. 충격 후 20세션 동안 σ가 계단식으로 반응하고 뒤늦게 빠진다.
  - KOSPI 가격지수(배당 제외)다. 공식 KRX 종가가 이 기기에 없어 실데이터 골든(2026-10-02 rv20 28.82%, vt 0.694)이 NOT_RUN이다.
  - 모든 R-06 카드가 NOT RUN이라 recommended 북에는 1.0으로 들어간다.
  - dry run 캐시 목록에 KOSPI_OFFICIAL_CLOSE가 없다(macro_daily.py:86-91). KR vt는 fail_closed가 되고 테스트가 이를 단언한다(tests/macro_m8_pipeline.py:873-874).
- **적용 범위:** KR·US 결정의 specification 북 composition 입력. 다른 시장은 target_ann null이라 거부한다. CRYPTO는 불가. 주문 크기로 쓰면 안 된다(연구용, 주문 경로 없음).
- **검증 상태:** 테스트로 확인됨. tests/macro_m2_risk.py::test_vt_01_sma20_simple_returns_ddof1_and_the_formula, ::test_vt_01_warmup_stale_carry_degenerate_and_armed_mapping, ::test_miss_02_exception_scope_vt_and_compose_halt_ops_hedge_state_never, tests/macro_m4_integration.py::test_estimator_harness_sma20_is_risk_layer_sma_vol, tests/macro_m8_pipeline.py::test_dry_run_end_to_end_on_the_local_cache(US vt ok, KR fail_closed 단언) (PASS). NOT_RUN: tests/macro_m2_risk.py::test_vt_01_rv20_28_82_and_vt_0_694_on_2_oct_refdata, ::test_g_kr_02_vt20_gross_and_net_refdata, ::test_g_us_01_vt15_refdata 외 g_kr·g_us 6건(macro_m2_risk 13 PASS / 15 NOT_RUN). 스크래치 v2_ladder_compose.py: sma_vol과 독립 numpy 계산이 0.230754로 일치.
- **관련 오류:** TA-01(P2, 골든 자리표시자), C01-03(P2, dry run 입력)
- **화면:** Overlay state Vol strip('vt next (specification)', 'vt (recommended book)', ui/macro_state_panel.py:340-357), Composition 줄

#### 112. 변동성 표시 라벨(calm/normal/elevated/stressed)

- **위치:** core/quant/risk_layer.py:label_of:267-271; core/quant/risk_layer.py:display_label_rel:274-279; core/quant/risk_layer.py:display_label_abs:289-296; core/quant/risk_layer.py:sigma_history:299-311; core/quant/risk_layer.py:market_vol_target:404-407
- **목적:** σ를 자기 과거 분위수와 비교해 4단계 단어를 붙인다. 상대(최근 756개 σ)와 절대(10년 이상 확장 창) 두 가지다.
- **가정:**
  - numpy 선형 분위수, 경계값은 높은 라벨(:267-271).
  - 현재값 포함, 인과적 필터(각 날짜 σ는 그날까지 정보만).
  - 결측 세션이 있어도 라벨 계산은 실패하지 않는다(:404-405 주석 'gaps do not fail it').
- **한계:**
  - 756개 σ 미만이면 상대 라벨이 None, 10년 미만이면 절대 라벨이 None이다.
  - 고정 4분위라 정의상 표본의 약 25%가 늘 stressed다.
  - 라벨용 σ 이력은 저장소의 사용 가능 종가를 모두 이어 만든다(:405). 결측 세션을 건너뛴 여러 날 수익이 한 수익으로 들어가 σ가 왜곡될 수 있다.
  - 실데이터 기대값 테스트가 NOT_RUN이다.
- **적용 범위:** 표시 전용이다. 게이팅이나 레짐 상태로 쓰면 안 된다(P19). 매크로 시트 판독과 같은 자리에 두면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m2_risk.py::test_label_01_causal_boundary_and_null_safe (PASS). NOT_RUN: ::test_label_01_kospi_elevated_stressed_and_us_normal_refdata, tests/macro_m3_estimators.py::test_g_b5_04_display_labels_refdata.
- **관련 오류:** -
- **화면:** Overlay state Vol strip 'relative/absolute' 칩(ui/macro_state_panel.py:352-353)

#### 113. R-02 min() 합성과 gross 한도

- **위치:** core/quant/risk_layer.py:_check_factors:466-474; core/quant/risk_layer.py:compose:477-487; core/quant/risk_layer.py:compose_detail:490-501; core/quant/risk_layer.py:verify_composition:504-513; core/quant/risk_layer.py:risk_layer:516-541; core/quant/sleeves.py:apply_overlays:608-707; core/ficc/macro_artifacts.py:build_overlay_decisions:375-446; core/skills/macro_daily.py:bounds_ok:821-874
- **목적:** composed = vt × min(1, overlays…, ladder, post_rearm_cap). gross = min(composed, 집중도 한도). HALTED면 0이다. 곱셈 합성은 거부한다.
- **가정:**
  - overlay ∈ [0.5, 1], vt ∈ [0, 1], ladder·post_rearm_cap ∈ {0.5, 1}(:466-474).
  - HALTED 밖에서 composed ≥ 0.5 × vt(:485-486).
  - 집중도 한도는 overlay가 아닌 위험 한도라 0.5 × vt 아래로 내릴 수 있다(:516-541).
  - 줄어든 예산을 재정규화하지 않는다.
- **한계:**
  - v2.0에서 total 기준 overlay는 하나도 작동하지 않는다(macro_daily.py:676). 실제 값은 vt × min(ladder, cap)이다.
  - 동시 신호를 min()으로 합쳐 누적 효과는 반영하지 않는다(설계 선택).
  - 0.5 바닥은 사양 고정값이다.
- **적용 범위:** recommended·specification 북. FORWARD-SIM 북은 자기 북 안에서만 쓴다(forward_sim.py:378-379).
- **검증 상태:** 테스트로 확인됨. tests/macro_m2_risk.py::test_cap_02_min_composition_10000_seeded_draws, ::test_cap_01_overlay_layer_cannot_emit_zero, tests/macro_m4_integration.py::test_apply_overlays_composes_through_risk_layer_compose, tests/macro_m7_cards.py::test_cap02_stack_card_dormant_today_generated_at_two_pass_factors_product_refused, tests/macro_m8_pipeline.py::test_i06c_acting_field_failure_halts_described_books_display_failure_never (PASS). NOT_RUN: tests/macro_m2_risk.py::test_cap_02_stack_card_clause_refdata. 스크래치 v2_ladder_compose.py: compose(0.8, [0.75, 0.5]) = 0.4, 곱 0.3은 verify_composition이 거부.
- **관련 오류:** -
- **화면:** Overlay state 북 타일 composed·gross, Composition 줄과 multiplier bar(ui/macro_state_panel.py:210-288)

#### 114. R-09 헤지 유효성 상태(hedge_state, corr63, 근원 PCE)

- **위치:** core/quant/risk_layer.py:corr63:561-578; core/quant/risk_layer.py:missed_releases:581-592; core/quant/risk_layer.py:_week_anchors:599-605; core/quant/risk_layer.py:_fx_hedge_credit:608-631; core/quant/risk_layer.py:hedge_state:634-645; core/quant/risk_layer.py:_hedge_state:648-752; core/quant/risk_layer.py:_nearest_psd:755-764; core/quant/risk_layer.py:apply_hedge_state:767-785; core/quant/risk_layer.py:covariance_carry:788-801; core/quant/risk.py:177-183(재수출만); core/skills/macro_daily.py:vol_and_overlays:633-642
- **목적:** 주식-채권 헤지 신용을 끌지 정한다. corr63(SPX 수익, −Δ10y) > 0, 근원 PCE YoY ≥ 3%, 입력 stale 중 하나면 hedge_credit_off. 주식 −1.5%(주간 −2%)와 달러 하락이 겹치면 hedge_failure. fx_hedge_credit(KOSPI 주간 대 ECOS 15:30 환율 26주 상관)은 표시 전용이다.
- **가정:**
  - Pearson 상관, 공통 날짜 63쌍, 10y 다리의 사용 가능일까지(통계를 늦추고 한 다리만 늦추지 않음, :561-578).
  - 운영은 KIS 10y 견적, 백테스트는 DGS10(strict H.15)(:73-74).
  - PCE는 지식 시각 기준 빈티지로 읽는다.
  - 예외·stale이면 보수적 기본값(credit off). 절대 HALT하지 않는다(:634-645).
  - 달러는 USD 라이브 프록시를 쓰고 DTWEXBGS는 쓰지 않는다.
  - 임계값은 규칙 저장소 risk_layer.hedge_state(core_pce_yoy_threshold 0.03, corr_threshold 0.0, 일간 −0.015, 주간 −0.02)다.
- **한계:**
  - 효과가 연결되지 않았다. apply_hedge_state(공분산의 주식-듀레이션 상관을 max(corr, 0)으로)와 covariance_carry는 생산 호출이 0곳이다. core/quant/risk.py:177-183은 이름만 재수출한다(grep). hedge_credit_off는 지금 표시 플래그일 뿐 어떤 공분산·노출도 바꾸지 않는다(신규 관찰).
  - 입력 대부분이 운영에서 비어 있다: US10Y_KIS_QUOTE, USD_LIVE_PROXY, ECOS_1530_CLOSE(V01-03), 수집기 미연결. 실제 출력은 거의 항상 risk_model_input_stale에 의한 credit off다(코드상).
  - corr63의 10y·USD 창은 상태 필터 없는 pit_window라 라이브 스냅숏·잠정값·합성 행이 섞일 수 있다(:684-686, 잠재).
  - PCE 빈티지 채널(ALFRED)이 코드에 없다(data_flow F10).
  - 63쌍 상관은 ρ = 0 근처에서 표준오차 약 0.13(1/√63)이다. 임계값 0의 근거는 사양이다.
  - corr 실데이터 골든(+0.53, 2026-09-30)이 NOT_RUN이다.
- **적용 범위:** R-09 risk_model 역할. 노출을 직접 바꾸지 않는다. 북을 HALT하면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m2_risk.py::test_hedge_01_reasons_failure_flags_and_fx_credit (golden_value), ::test_hedge_01_stale_inputs_never_halt_and_change_no_exposure, ::test_corr_01_date_aligned_pairs_synthetic, ::test_role_02_spx_failing_sets_hedge_credit_off_through_corr63, ::test_apply_hedge_state_clamps_only_the_hedge_legs, tests/macro_m6_context.py::test_hedge_01_built_macro_state_with_stale_usd_proxy, tests/macro_m8_pipeline.py::test_scope_01_e_f_hedge_exception_and_context_log_failure_halt_nothing (PASS). NOT_RUN: tests/macro_m2_risk.py::test_corr_01_plus_0_53_at_2026_09_30_refdata.
- **관련 오류:** V01-03(P2), CAL-06(P2), 신규 관찰: apply_hedge_state 미연결(감사 행 없음)
- **화면:** Overlay state Flags 'Hedge' 칩 묶음(ui/macro_state_panel.py:361-368)

#### 115. R-07 한국 집중도 한도(ETF 투시, MSCI 25/50)

- **위치:** core/quant/risk_layer.py:li_etf_eligible:840-844; core/quant/risk_layer.py:lookthrough_exposure:853-893; core/quant/risk_layer.py:capped_benchmark:896-916; core/quant/risk_layer.py:concentration_bound:928-989; core/quant/risk_layer.py:risk_limit_breach:992-1016; core/skills/macro_daily.py:_concentration:583-600; data/macro/rules_v2.0.0.json:risk_layer.korea_caps
- **목적:** ETF 구성(PDF) 투시 비중으로 D1 템플릿(msci_25_50: 단일 22.5%, 4.5% 초과 종목 합 45%, 활성 5%, 반도체 50%)의 최대 gross를 구한다. 위반 수준(단일 25%, 합 50%)이면 RISK HALT 대상이다.
- **가정:**
  - 결정 t는 t−1 바스켓만 쓴다(t+1 08:00 KST 공시, :864-868).
  - 레버리지·인버스는 ×L, 틱이 가격의 10bp 초과면 부적격(:840-844).
  - 바스켓 이후 가격 변화는 상대가격으로 재계산할 수 있다(F-4).
  - 벤치마크 기본값은 라인 자신의 바스켓을 캡한 것이다. 각 한도 = 수준/비중, 최솟값이 binding이다.
- **한계:**
  - 운영에서 계산되지 않는다. Services.baskets 기본 None이고 baskets=를 넘기는 생산 코드가 없다(grep). 결과는 항상 'KODEX200_PDF basket not available' fail_closed다(macro_daily.py:587-590)(신규 관찰, 데이터 대기).
  - risk_limit_breach는 생산 호출이 0곳이다. risk_step에 limit_met도 전달되지 않는다(macro_daily.py:667).
  - 반도체 집합은 소유자 서명 전 005930·000660 두 종목뿐이다(:805).
  - 실제 KODEX 바스켓 테스트가 NOT_RUN이다.
- **적용 범위:** KR 시장 롱 라인만. 다른 시장은 ValueError다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m5_books.py::test_caps_01_synthetic_basket_bounds_and_by_book (golden_value), ::test_book_03_li_eligibility_and_lookthrough_x_l, ::test_miss_02_exceptions_in_concentration_bound_and_ladder_halt_ops, tests/macro_m1_fixtures.py::test_synth_b5_bands_and_concentration_bounds (PASS). NOT_RUN: tests/macro_m5_books.py::test_caps_01_real_kodex_basket_refdata, ::test_g_post_01_pair_implied_share_refdata.
- **관련 오류:** 신규 관찰(미연결, 감사 행 없음). 데이터 공백은 README 'Open owner actions'의 KODEX 200 PDF basket
- **화면:** Overlay state Composition 둘째 줄 'gross = min(composed, bound …)'(ui/macro_state_panel.py:271-272)

#### 116. R-31 드로다운 사다리와 R-07 hard stop

- **위치:** core/quant/risk_layer.py:hard_stop_level:1029-1046; core/quant/risk_layer.py:ladder_config:1049-1062; core/quant/risk_layer.py:ladder_step:1072-1101; core/quant/risk_layer.py:ladder_path:1116-1136; core/quant/risk_layer.py:drawdown_ladder:1139-1152; core/quant/risk_layer.py:binding_share_of:1155-1158; core/quant/risk_layer.py:steps_act_in:1161-1170; core/quant/risk_layer.py:ladder_for_book:1178-1183; core/quant/risk_layer.py:ladder_flags:1186-1192; core/engine/books.py:session_offset:250-260; core/engine/books.py:risk_step:573-617; core/skills/macro_daily.py:sessions_around:147-156
- **목적:** 북 전체 NAV 낙폭에 따라 −8%면 0.5, −12%면 0.5와 신규 진입 차단(21세션 시간 상자), 재ARM 이후 고점 대비 −15%면 RISK HALT(10결정 0×, 자동 재ARM, 이후 10결정 0.5 cap)를 건다.
- **가정:**
  - hard stop 기준은 마지막 재ARM 이후 HWM, 단계 기준은 마지막 리셋 이후 running peak이다.
  - ≤ 비교라 정확히 −15.00%에서 발동한다. 단계가 끝나면 단계 기준만 리셋한다(:1093-1094).
  - NAV 결측이면 상태 유지, 3회 연속이면 OPS HALT(books.py:68 NAV_LIMIT 3, :589-597).
  - 재ARM 세션은 북 1차 시장 달력으로 센다. D2 수준은 {ref}로만 읽는다(:1029-1046).
- **한계:**
  - M-1(P1): sessions_around가 앵커 앞뒤(뒤 100일, 앞 130일, 달력일)를 한 번에 조회하고 예외 하나만 나도 전체를 ValueError로 바꾼다(macro_daily.py:147-156). 커버리지 끝 86세션 전(2027-08-24)부터 session_offset이 실패해 hard stop HALT가 기록되지 않고 북이 ARMED로 남는다(calendars.md 재현).
  - −1.5σ_book 옵션은 σ_book 정의 전까지 평가하지 않는다.
  - 고정 수준 규칙이라 변동성 체제와 무관하게 같은 낙폭에 반응한다. 시간 상자 이후 바닥 근처를 새 기준으로 삼아 다시 발동할 수 있다.
  - recommended 북에서는 R-31 PASS나 INVARIANT_STEP(binding share ≤ 0.10) 전에는 단계가 작동하지 않는다. 지금 binding share는 헤더가 없어 None이다(macro_daily.py:672은 binding_share를 넘기지 않음).
  - 실데이터 골든(G-LAD-01..03, KOSPI 1997-2026 재진입)이 NOT_RUN이다. 테스트 헬퍼 _lad가 바로 NotRun이다(TA-01).
- **적용 범위:** recommended·specification 북만(books.RISK_BOOKS). card·FORWARD-SIM·refusal 북에는 없다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m5_books.py::test_halt_01_hard_stop_cycle_exact_15pct, ::test_i_04_ladder_steps_reset_block_and_placement, ::test_step_05_idempotent_halt_flat_minus_16, ::test_halt_01_ops_breach_cure_and_lag_audit_causes, tests/macro_m1_books.py::test_risk_cycle_refusal_window_rearm_and_cap, tests/macro_m8_pipeline.py::test_scope_01_c_d_nav_minus_16_halts_its_own_book_risk, tests/macro_m5_integration.py::test_ladder_block_and_post_rearm_cap_flow_into_gross_evaluator_ledger_and_macro_state (PASS). NOT_RUN: tests/macro_m5_books.py::test_g_lad_01_literal_ladder_refdata, ::test_g_lad_02_qf4_eleven_session_fix_refdata, ::test_g_lad_03_sensitivity_lines_refdata, ::test_i_04b_kospi_1997_2026_reentry_and_pinned_count_refdata. 스크래치 v2_ladder_compose.py: 100→92에서 0.5(21결정), 88에서 차단, 85(정확히 −15%) HALT, 85.01은 미발동.
- **관련 오류:** M-1(P1), CAL-07(P2), TA-01(P2)
- **화면:** Overlay state Flags 'Ladder' 칩과 hard stop 상태, HALT 배너(ui/macro_state_panel.py:245-274, :369-375)

#### 117. 북 런타임 상태기계(ARM/DISARM/HALT)와 북 NAV 평가

- **위치:** core/engine/books.py:arm:318-332; core/engine/books.py:runtime_halt:375-410; core/engine/books.py:runtime_rearm:413-478; core/engine/books.py:step_decision:501-540; core/engine/books.py:book_nav:638-667; core/engine/books.py:record_decision:686-724; core/engine/books.py:heartbeat_check:768-789; core/calendars/store.py:arm_precondition:505-512; core/skills/macro_daily.py:data_ok:499-531; core/skills/macro_daily.py:_default_nav:567-580; core/skills/macro_daily.py:engine_feed:927-961; core/skills/macro_daily.py:run_record:1083-1109
- **목적:** 북마다 DISARMED/ARMED/HALTED를 관리한다. ARM 조건, OPS·RISK HALT, 재ARM, 결정 원장, 북 NAV를 계산한다.
- **가정:**
  - ARM: 라이브 실행, acting 입력 모두 정상, 한 번도 ARMED 아님, 그 시장 달력 파일 모두 서명·60세션 이상 커버(macro_daily.py:1094-1096, store.py:505-512).
  - OPS HALT: acting 입력 연속 실패가 바인딩 한도(기본 2), 북 카운터 2, NAV 3회 결측, lag audit 위반, 스키마 실패, 하트비트 60초. 입력 원인은 정상 결정에서 자동 재ARM, lag audit·스키마는 운영자 재ARM.
  - NAV: 직전 결정 비중이 다음 종가 수익을 받는다(t 결정, t+1 수익). \|Δw\|에 편도 비용(bp)을 그날 부과하고 첫 진입은 무료다. 수익이 없으면 None(보간 없음). 비중 합 ≤ 1.
  - NAV 수익은 공식 종가 두 개의 비율(가격 수익)이다(macro_daily.py:573-575).
  - DISARMED 북은 HALT 되지 않는다(warm-up은 실패가 아님).
- **한계:**
  - 지금 모든 북이 DISARMED다. 라이브 실행은 CalendarUnsigned로 거부되고 dry run·replay는 arm=False다.
  - NAV는 KR 라인 069500 하나만 평가한다(macro_daily.py:73-74). US는 D5 전까지 없다.
  - NAV는 종가 비율만 쓰고 ETF 분배금을 넣지 않는다(macro_daily.py:575). 분배락일 가격 하락이 NAV 손실로 잡혀 사다리 낙폭에 들어간다(코드상, 크기 미측정).
  - 틱표를 못 읽으면 비용을 비워 두고(macro_daily.py:577-579) 비중이 바뀐 날 book_nav가 예외를 낸다(fail closed, P10).
  - 비용은 side 기본값 buy로 부른다(macro_daily.py:577). 매도세는 NAV에 들어가지 않는다. ETF는 면제라 지금 영향은 없다.
  - M-1 세션 창 문제가 RISK 재ARM 계산에도 걸린다.
  - 커버리지 경보와 calendar_change 이벤트가 운영에 연결되지 않았다(CAL-07).
  - 하트비트는 합성 타임스탬프로만 쓴다(v2.0 일간 북은 QuoteFeed를 읽지 않는다).
- **적용 범위:** 매크로 v2 북(recommended:, specification:, forward_sim:, refusal:, card:). 기존 Execution 엔진의 전역 EngineState와 별개다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_books.py 8 PASS(::test_ops_halt_counters_scope_and_auto_rearm, ::test_ever_armed_warmup_and_retire, ::test_lag_audit_and_schema_failure_need_operator_rearm 등), tests/macro_m5_books.py::test_weight_book_ledger_nav_matches_costed_path_and_persists (golden_value), ::test_ops_nav_counter_heartbeat_operator_kill_and_card_trio, tests/macro_m8_pipeline.py::test_default_nav_values_the_book_on_official_closes_only, ::test_obs_04_acting_step_errors_block_feed_count_and_halt_at_the_limit, tests/macro_m1_integration.py::test_calendar_coverage_halt_through_the_book_runtime (PASS). NOT_RUN: tests/macro_m5_books.py::test_mono_01_i01_fixture_clause_refdata.
- **관련 오류:** M-1(P1), CAL-07(P2), CAL-08(P2, d865c7f 반영, 서명 대기), 신규 관찰(NAV 분배금 미반영, 감사 행 없음)
- **화면:** Overlay state 북 타일(엔진 상태), HALT 배너와 Acknowledge, Alerts(ui/macro_state_panel.py:210-274, :400-428)

#### 118. R-03 슬리브 변동성 스케일과 R-04 Daniel-Moskowitz 게이트

- **위치:** core/quant/sleeves.py:sigma126_series:219-226; core/quant/sleeves.py:vol_scale_from_returns:229-257; core/quant/sleeves.py:paper_ls_returns:260-265; core/quant/sleeves.py:overlay_net_returns:268-280; core/quant/sleeves.py:years_line:283-302; core/quant/sleeves.py:sleeve_vol_scale:322-364; core/quant/sleeves.py:dm_from_inputs:367-374; core/quant/sleeves.py:dm_gate:377-421; core/quant/sleeves.py:base_weights:531-596; core/skills/macro_daily.py:vol_and_overlays:643-656
- **목적:** R-03: 모멘텀 롱숏 종이 시리즈의 126일 σ로 vs = min(1, 0.12/σ)(개정 2: 확장 중앙값 목표, 개정 3: 제곱). R-04: 24개월 시장 수익 < 0 그리고 σ126 > 확장 2/3 분위면 0.5(specification 북만).
- **가정:**
  - 126개 유효 수익 필요, 252 연율화, ddof 1(:219-257).
  - 종이 시리즈는 S.xs_momentum(12-1, 상위 1/3, 21일 간격)과 S.simulate의 리밸런싱·비용 0이다(:260-265; K-e).
  - 분위는 현재 포함 확장 창이고 252개 관측이 필요하다(:405-410).
  - 오버레이 자체 회전 비용은 L/S 양다리에 부과하고 첫 진입은 무료다(:268-280).
  - 파라미터는 코드 상수(:38-39)로 규칙 저장소 families.momentum과 중복된다.
- **한계:**
  - 운영에서 계산되지 않는다. MOM_PAPER_LS_SERIES·DM_MKT_RET_24M·DM_MKT_VOL_126(DERIVED)을 저장하는 생산 코드가 없다(put_derived 호출 0곳, grep). US만 등록됐고 US 북은 D5 전까지 비어 있다. 결과는 MissingInput이다(신규 관찰, 데이터 대기). dry run 테스트가 US의 R-03/R-04 fail_closed를 단언한다(tests/macro_m8_pipeline.py:872).
  - DM_QUANTILE 2/3와 저장소 0.6667의 차이는 무시할 만하지만 상수 일치 테스트가 없다.
  - French 일간 MOM 골든이 NOT_RUN이다.
  - R-03 'indicative PASS; step 3 borderline', R-04 'step 3 FAIL(indicative)'는 전수 표본 계산이지 정식 실행이 아니다.
- **적용 범위:** specification 북의 momentum 패밀리, active 기준만. recommended 북에서는 NOT_RUN이라 1.0이다. vt를 L/S 슬리브에 걸면 안 된다(T-BASIS-01).
- **검증 상태:** 테스트로 확인됨. tests/macro_m4_sleeves.py 14 PASS / 7 NOT_RUN. PASS: ::test_r03_01_vs_formula_synthetic (golden_value), ::test_r03_01_vs_reproduces_techfund_rows, ::test_dm_kernel_reproduces_techfund_sample, ::test_r03_01_sleeve_vol_scale_acting_read, ::test_dm_gate_acting_read_and_refusals, ::test_cost_01_both_legs_for_ls_sleeves, ::test_no_renormalisation_and_sign_preserved. NOT_RUN: ::test_r03_01_french_fixture_refdata, ::test_g_mom_01_02_08_french_mom_daily, ::test_g_mom_03_04_05_06_french_mom_and_market.
- **관련 오류:** K-e(종이 시리즈의 무비용 리밸런싱 가정), TA-01(P2)
- **화면:** Overlay state overlays 표(specification 북), Flags 'D-M bear state' 칩(ui/macro_state_panel.py:376-377); Model cards 뷰 MACRO-R03-US-MOM, MACRO-R04-US-DM

#### 119. R-13 맥락 로그 계산기(Sahm, probit, Taylor, VRP, rv21, SMA10m, 난류)

- **위치:** core/ficc/context_log.py:bond_equivalent:291-295; core/ficc/context_log.py:recession_probit_et:298-301; core/ficc/context_log.py:taylor_residual_range:304-310; core/ficc/context_log.py:vrp:317-322; core/ficc/context_log.py:trend_state_sma10m:325-330; core/ficc/context_log.py:rv21_series:333-338; core/ficc/context_log.py:rv21_and_percentile:341-347; core/ficc/context_log.py:causal_zscore:350-359; core/ficc/context_log.py:sahm_inhouse:362-370; core/ficc/context_log.py:turbulence_absorption:373-392; core/ficc/context_log.py:_calc_sahm.._calc_turbulence:628-764; core/ficc/context_log.py:build_context_log:808-854
- **목적:** 결정마다 느린 매크로 맥락을 PIT 읽기로 계산해 기록한다. Sahm, 경기침체 probit, Taylor 잔차 범위, VRP, KOSPI rv21과 3년 백분위, KOSPI SMA10m 추세, 난류·흡수비, 시트 지표 z. acts = false.
- **가정:**
  - Sahm: U-3 3개월 평균 − 직전 12개월 3개월 평균의 최솟값. 하나라도 결측이면 NaN.
  - Probit: Φ(α + β·(GS10 − BEY(TB3MS))), α = −0.6045, β = −0.7374(명세값), BEY = 365d/(360 − 91d).
  - Taylor: r* ∈ {0.5, 1, 2}, 갭 2종(Okun 2×(u*−u), CBO 산출갭), a ∈ {0.5, 1}의 12규칙 min·max, π* = 2, 근원 PCE YoY.
  - VRP: VIX²/12 − 21일 단순수익 제곱합(월 분산 단위).
  - rv21: ddof 1 × √252, 백분위는 최근 756개 중 현재 포함.
  - 추세: 완료된 월말 종가 10개 평균 대비.
  - 난류: 반감기 250 지수가중 평균·공분산(직전 500행), pinv. 흡수비는 상위 N/5 고윳값.
  - z: 최근 252개, 모집단 SD.
- **한계:**
  - probit 계수를 공개 원천과 대조하지 않았다. 테스트는 명세 자신의 0.744와 비교한다(tests/macro_m6_context.py:376). 기억 기반 참고: NY Fed 공개 모형 계수로 알려진 −0.5333/−0.6330을 같은 2023-05 입력(3.57, 5.14)에 넣으면 0.7085, 코드 계수는 0.7442다(스크래치 probit_check.py; 원천 미확인). 어느 원천의 계수인지 확인이 필요하다.
  - KOSPI 추세는 월말 당일에도 그 달을 미완료로 보고 뺀다(context_log.py:716). 월말 결정에서 한 달 늦다(신규 관찰, 맥락 전용).
  - VRP는 앞 30일 내재와 뒤 21일 실현을 섞는 근사다.
  - 난류 universe가 선언되지 않아 항목이 missing으로 남는다(:747-750).
  - 빈티지가 없으면 Sahm·Taylor가 사후 수정값이다(data_flow F10).
  - 라이브 입력 대부분이 비어 있다(수집기 미연결, BoK·KOSIS 없음, V01-03). 실데이터 기대값 테스트가 NOT_RUN이다.
- **적용 범위:** 맥락 전용(P9). acting 모듈이 읽으면 런타임 가드와 정적 스캔이 거부한다(T-CTX-01). 어떤 배수·게이트에도 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m6_context.py::test_ctx_02_calculators (golden_value: probit 0.744, BEY 5.2804, Taylor 12규칙, VRP, Sahm 0.3; 기대값은 명세 자신의 값), ::test_ctx_02_items_vintages_live_and_sheet, ::test_ctx_02_failure_paths_label_and_never_halt, ::test_ctx_01_static_import_scan_and_positive_controls (PASS). NOT_RUN: ::test_ctx_section_11_context_values_refdata, ::test_ctx_02_live_snapshot_sources_owner. 스크래치 work/M5_macro_pit_verify/probit_check.py.
- **관련 오류:** D04-03(P3), V01-03(P2), 신규 관찰(KOSPI 추세 월말 지연, probit 계수 원천 미대조)
- **화면:** Overlay state 'Context log' 접힘 타일(ui/macro_state_panel.py:477-495)

#### 120. R-10 이벤트 창·갭 태그와 R-08 VIX 기간구조 주석

- **위치:** core/calendars/events.py:var_display_scale:155-160; core/calendars/events.py:event_windows:163-201; core/calendars/events.py:kr_open_window:210-219; core/calendars/events.py:cb_reopen_window:222-227; core/calendars/events.py:active_windows:230-254; core/calendars/events.py:holiday_gap_event:265-278; core/calendars/events.py:kr_open_gap_event:281-285; core/calendars/events.py:gap_tags:288-293; core/calendars/clocks.py:gap_sessions:377-386; core/ficc/annotations.py:parity_flag:71-72; core/ficc/annotations.py:vix_ge_vix3m:158
- **목적:** 예정 이벤트(US CPI·NFP 08:25-10:00 ET, FOMC 13:45-15:00·VIX 조건 15:30, BoK 결정·기자회견, KR 개장 30분, 서킷브레이커 재개 30분)의 신규 진입 차단 창, KR 개장 갭(미국 세션 수 n_US), 1일 VaR 표시 배율 √max(n_US, 1)을 만든다. R-08은 VIX ≥ VIX3M 주석이다.
- **가정:**
  - 이벤트 태그는 비중을 바꾸지 않는다(events.tags_change_weights false).
  - 창은 시뮬레이션 장중·선물 신규 진입에만 적용한다.
  - √n 배율은 일간 수익 독립·동분포를 전제한다.
  - 취소 이벤트는 창이 없고, 지연 이벤트는 재저장 시각으로 이동한다.
- **한계:**
  - √n 배율은 이벤트 꼬리를 과소평가할 수 있다(표시 전용).
  - 이벤트 저장소는 소유자 입력이다. 비어 있으면 생성 창(KR 개장)만 나온다.
  - gap_sessions가 달력 오류를 그대로 따른다. d865c7f 전 초안에서는 2026-06-04가 2 대신 1이었다(CAL-01, CAL-02). d865c7f에서 미서명 초안에 휴장 행을 넣었다.
  - v2.0 일간 북에는 장중 진입이 없어 창이 실제로 막는 것은 시뮬레이션 evaluator뿐이다.
- **적용 범위:** 표시·주석과 시뮬레이션 evaluator의 신규 진입 차단. 24시간·일간 북 블랙아웃은 금지다(사양 10절 12항).
- **검증 상태:** 테스트로 확인됨. tests/macro_m5_fills_events.py::test_i06_event_windows_cancelled_delayed_bok_and_artifact, ::test_i06b_i06c_gap_tags_var_scale_and_no_weight_change (golden_value: 2026-10-02 KR 결정 → 2026-10-06 {true, 2, 1.4142}), ::test_i06_evaluator_blocked_for_new_entries_only, ::test_annot01_annotation_never_changes_exposure_and_requests_snapshot, tests/macro_m1_calendars.py::test_gap_sessions_values (PASS). NOT_RUN: tests/macro_m5_fills_events.py::test_g_r08_01_spell_count_smoke_then_refdata, ::test_task_m5_15_event_conditional_variance_refdata.
- **관련 오류:** CAL-01(P1), CAL-02(P1), CAL-03(P2)(d865c7f 반영, 서명 대기)
- **화면:** Overlay state Flags 'Gap'(gap sessions, VaR display scale)·'Annotation'(VIX ≥ VIX3M) 칩, Event calendar 타일(ui/macro_state_panel.py:379-384, :498-517)

#### 121. R-28 추세 축과 R-29 미국 선물 vt(FORWARD-SIM 표시 북)

- **위치:** core/quant/forward_sim.py:below_sma10m:82-87; core/quant/forward_sim.py:trend_multiplier:90-96; core/quant/forward_sim.py:trend_axis:99-111; core/quant/forward_sim.py:vt_us:181-192; core/quant/forward_sim.py:vt_futures_multiplier:195-206; core/quant/forward_sim.py:micro_es_contracts:220-240; core/quant/forward_sim.py:settling_pass:243; core/quant/forward_sim.py:promotion_ok:292; core/quant/forward_sim.py:display_books:362-379; core/skills/macro_daily.py:_forward_display:1015-1024
- **목적:** US 결정에서 R-28(월말 종가 < 10개월 SMA면 0.5)과 R-29(min(1, 0.15/σ_SMA20), CME Micro ES 5bp)를 자기 forward_sim 북에만 표시한다. 추천이 아니다.
- **가정:**
  - 월말 공식 종가(SPX_MONTH_END_CLOSE) 10개, 일간 SPX_OFFICIAL_CLOSE 21개, σ 공식은 sma_vol과 같다.
  - 라이브는 official_close만, 백테스트는 CLOSE_STATUSES(공급사 일치 검사 없음)를 읽는다(:372).
  - 계약 수는 반올림(0에서 멀어지는 방향) 정수이고 계약 1개가 명목의 5% 이하여야 한다.
  - 창 행이 모자라면 이전 값을 유지하고 fail_closed로 표시한다.
- **한계:**
  - vt_us는 pit_window의 마지막 21개 종가를 그대로 쓴다(forward_sim.py:374, :181-192). 세션 결측 검사와 결정 세션 일치 검사가 없다. R-06의 F-3 fail-closed 규칙과 다르다(신규 관찰, 표시 전용).
  - R-28 월말 창도 마지막 10개를 그대로 쓴다(:373). 최근 월말 종가가 빠져도 오래된 10개로 'ok'를 낸다. fail_closed는 10개 미만일 때만이다(:82-96)(신규 관찰, 표시 전용).
  - 소유자 null(명목, 계약 승수, nav_fx 시각)로 계약 수가 계산되지 않는다. 패키지 NOT_FROZEN이라 헤더 커밋도 forward record도 시작되지 않는다.
  - 1926+ 정산 실행은 French 일간 파일 부재로 불가다. R-29는 1990-2026에서 44개 시작일 중 11개만 통과했다(README).
  - 월말 시리즈 수집기가 없다(소유자 데이터 항목 'SPX month-end closes').
- **적용 범위:** forward_sim:R-28, forward_sim:R-29 표시 북만. Korea 인스턴스는 거부한다(T-TREND-03). engine_feed·recommended 북 금지.
- **검증 상태:** 테스트로 확인됨. tests/macro_m8_forward.py::test_trend_mechanics_sma10m_onsets_composition, ::test_trend_03_korea_instance_refused_kospi_trend_context_only, ::test_trend_04_multiplier_only_in_its_forward_sim_book, ::test_usfut_mechanics_vt_contracts_and_nav_fx_fail_closed, ::test_usfut_03_promotion_guard_truth_table, tests/macro_m8_integration.py::test_default_hooks_display_refusal_and_forward_sim_and_never_feed_a_weight_book (PASS). NOT_RUN: tests/macro_m8_forward.py::test_trend_02_french_monthly_and_us_vt15_goldens_refdata, ::test_usfut_02_settling_run_logic_and_the_1926_fixture_refdata, ::test_usfut_05_dla_u2_reproduction_refdata.
- **관련 오류:** 신규 관찰(vt_us·월말 창 간격·최신성 미검사, 감사 행 없음)
- **화면:** Overlay state 'FORWARD-SIM · not a recommendation' 그룹(ui/macro_state_panel.py:319-337); Model cards 뷰 MACRO-R28-US-TREND, MACRO-R06-US-FUT

#### 122. R-11·R-12 거부 북(refusal books, 표시 전용)

- **위치:** core/quant/refusal.py:_window:75-79; core/quant/refusal.py:refusal_krw_leg:88-118; core/quant/refusal.py:refusal_rates_leg:121-153; core/quant/refusal.py:display_legs:170
- **목적:** 은퇴한 REJECT 규칙을 표시 전용 북으로 보여준다. S1: ln(USDKRW_t/USDKRW_{t−20}) > 3%면 KR 0.75. S2: 10y 20관측 변화 > 0.40pp면 US 0.5.
- **가정:**
  - 15:30 KST 스냅숏 또는 ECOS 15:30 종가를 쓴다. DEXKOUS는 쓰지 않는다.
  - 라이브는 KIS 10y 견적, 백테스트는 DGS10(strict H.15).
  - 관측 개수 20, 한쪽 방향.
- **한계:**
  - 입력이 운영에서 비어 있다(ECOS 클라이언트 없음, V01-03). 플래그 null, 값 1.0이 표시된다.
  - 창은 상태 필터 없는 pit_window 마지막 21개다(refusal.py:75-79). 잠정값·스냅숏·합성 행이 섞일 수 있고, 최신 관측의 나이를 보지 않는다. 오래된 자료로 플래그가 켜질 수 있다(코드상, 표시 전용).
  - REJECT 판정은 의회 기록이고 이 기기에서 재현하지 않았다(README).
  - 관측 개수 창이라 휴일 결측에 따라 실제 기간이 달라진다.
- **적용 범위:** refusal:R-11, refusal:R-12 표시만. 다른 북이 읽으면 안 된다(I-03 정적 표지). regate_queue false.
- **검증 상태:** 테스트로 확인됨. tests/macro_m8_forward.py::test_ref_01_s1_retired_refusal_book_display_only, ::test_ref_02_s2_retired_refusal_book_and_the_s2_momentum_clause, tests/macro_m8_pipeline.py::test_i03_book_separation_static_and_runtime (PASS). NOT_RUN: tests/macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata, ::test_g_ref_02_s2_goldens_refdata.
- **관련 오류:** V01-03(P2), 신규 관찰(창 상태·최신성 미검사, 감사 행 없음)
- **화면:** Overlay state 'REFUSAL BOOK · not a recommendation' 그룹; Model cards 뷰 MACRO-R11-KR-KRW, MACRO-R12-US-RATES

#### 123. R-25 forward record 감시와 강등(CUSUM, 파국 경계)

- **위치:** core/quant/forward.py:whole_book:102-111; core/quant/forward.py:rolling_sharpe/rolling_mdd/rolling_es:114-131; core/quant/forward.py:cusum_path:161-172; core/quant/forward.py:cusum_monitor:175-182; core/quant/forward.py:in_control_arl:185-193; core/quant/forward.py:calibrate_h:196-216; core/quant/forward.py:evaluate_triggers:313-320; core/quant/forward.py:placebo_panel:340-352; core/quant/forward.py:false_demotion_rate:370-374; core/quant/forward.py:calibrate_alarms:377-417; core/quant/forward.py:budget_split:432-445; core/quant/forward.py:ForwardRecord:456-590; core/quant/forward.py:forward_monitor:695-737; core/quant/forward.py:demote:809-826; core/skills/macro_daily.py:_forward_monitor:1036-1060
- **목적:** 헤더 커밋 이후 라이브 결정만 쌓는 forward record에서 파국적 성능 저하를 감지해 카드를 강등한다. 판정을 올리지는 않는다.
- **가정:**
  - 북 전체 NAV 기준 쌍대 차이 w_card × (r_on − r_cmp)(:102-111).
  - 월간 단측 CUSUM k = 0.25, h는 블록 부트스트랩(B 2000, seed 11, 블록 12)으로 인통제 ARL ≥ 240개월이 되게 보정(:55, :196-216).
  - CARD-P는 파국 3조건 동시, CARD-O는 2조건 중 하나.
  - 연 10% 거짓 강등 예산을 활성 카드에 균등 배분하고 20개 원형 이동 위약 패널로 확인한다(:56).
  - 결측·HALT·DISARMED 결정은 양쪽에서 뺀다.
- **한계:**
  - 지금 시작된 record가 없다(패키지 NOT_FROZEN, 명목 null).
  - 12개월로는 파국만 감지된다(HONESTY_LINE).
  - 설계 표본 하나로 한 번만 보정한다. 체제가 바뀌면 ARL 가정이 깨질 수 있다.
  - 실데이터 골든이 없다.
- **적용 범위:** PASS 카드의 사후 감시. 판정을 올리는 근거로 쓰면 안 된다(ForwardRecordCannotRaise).
- **검증 상태:** 테스트로 확인됨. tests/macro_m8_forward.py::test_demote_01_trigger_text_and_a_protective_record_never_demotes, ::test_demote_02_every_statistical_trigger_reads_whole_book_nav, ::test_demote_03_false_demotion_budget_on_the_20_shift_panel, ::test_demote_05_no_forward_record_raises_a_verdict, ::test_i14_calibrate_record_monitor_demote_end_to_end, ::test_record_append_only_no_backfill_live_only, tests/macro_m8_integration.py::test_forward_monitor_hook_demotes_locks_out_and_admissions_refuse (PASS).
- **관련 오류:** -
- **화면:** Model cards 뷰(강등·lockout 표시), Overlay state 경보

#### 124. 사전 등록 비용과 틱 하한(R-26 비용 모형)

- **위치:** core/quant/instruments.py:tick_size:105-115; core/quant/instruments.py:tick_floor_bp:118-122; core/quant/instruments.py:stress:125-127; core/quant/instruments.py:stress_cost_line:130-137; core/quant/instruments.py:cost_per_side:168-185; core/quant/instruments.py:check_cost_policy:192-216; core/quant/instruments.py:fx_instrument_check:251-270; core/quant/validate.py:COST_BP_PER_SIDE:78
- **목적:** 편도 비용 = max(표 요율, 수수료 1.4bp + ½틱/가격 + 매도세)다. 2배 스트레스 줄을 함께 낸다. 비용 인하는 거부한다.
- **가정:**
  - 표 요율: KRX ETF 3, KRX 주식 35, US 50, 크립토 10, 선물 5, FX 10 bp(validate.py:78, 게이트 표 하나).
  - KRX ETF 틱표는 2023-12-11부터만(2000원 미만 1원, 이상 5원).
  - 2026년 주식 매도세 20bp(ETF 면제). 매도세는 side='sell'일 때만 더한다(:177).
  - 비KRW 북은 nav_fx가 필요하다.
- **한계:**
  - 이전 틱표와 다른 상품은 소유자 입력이다(None → NotTradable).
  - Strategy Lab은 이 하한을 쓰지 않는다. 저가 ETF 비용이 최대 약 25배 낮게 계산된다(MF-02).
  - 수수료 1.4bp는 데스크 견적이다. 시장 충격·스프레드 변동은 stress_cost_line 근사뿐이다.
  - 북 NAV 호출은 side 기본값 buy다(macro_daily.py:577). 주식 라인이 생기면 매도세가 빠진다(지금은 ETF라 영향 없음).
- **적용 범위:** 매크로 카드 헤더, 북 NAV(_default_nav), 테크펀드 GOV-7. 표 요율 자체는 validate의 GATE 상수다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m0_instruments.py::test_cost02_worked_examples (golden_value: 252670 ₩69에서 편도 72bp 이상), ::test_cost02_floor_never_lowers, ::test_cost03_lowering_refused, ::test_cost02_every_result_at_2x, ::test_study_reads_the_gate_cost_table (PASS). NOT_RUN: ::test_book01_real_sleeve_notional_is_owner_input.
- **관련 오류:** functional_completeness/MF-02(P2)
- **화면:** Model cards 헤더 비용 줄; Overlay state는 NAV를 통해 간접

#### 125. 시뮬레이션 체결 모형(공식 종가 체결, 상하한가 잠김)

- **위치:** core/engine/orders.py:simulate_fill:467-515
- **목적:** 시뮬레이션 주문을 공식 종가에 체결한다. 상하한가 잠김은 비체결·이월(하한가 매도는 2배 비용), ETF iNAV 괴리 30bp 플래그, 선물 만기일 15:20 정지.
- **가정:**
  - 종가 경매 가격으로 전량 체결한다. 수량 제약·시장 충격은 없다.
  - 가격제한은 regime_tags('KR', d)['price_limit']를 쓴다(core/calendars/regime.py, 소유자 서명 태그).
- **한계:**
  - 생산 호출이 0곳이다(grep: 정의와 docstring만). 운영 결과에 영향이 없다.
  - 실데이터 추적오차 골든이 NOT_RUN이다.
  - 체결량·유동성을 무시한다.
- **적용 범위:** 매크로 v2 시뮬레이션 북·evaluator.
- **검증 상태:** 테스트로 확인됨. tests/macro_m5_fills_events.py::test_fill01_official_close_fill_random_end_and_refusals (golden_value), ::test_fill02_limit_lock_both_sides_carry_and_halt_days, ::test_fill03_inav_residual_flag, ::test_bar01_r27_bar_convention_refuses_bar_closes (PASS). NOT_RUN: ::test_fill01_qf1_tracking_error_golden_refdata, ::test_fill02_real_000660_closes_refdata.
- **관련 오류:** -
- **화면:** -

#### 126. 시나리오 라이브러리(M9 충격 창, SEP 금리 밴드)

- **위치:** core/quant/scenarios.py:scenario_library:132-134; core/quant/scenarios.py:run_scenario:137-152; core/quant/scenarios.py:_shock_window:204-253; core/quant/scenarios.py:_rate_band:256; core/ficc/ratesim.py:sep_band_params/sep_band_paths; core/quant/lab.py:letf_path_return:767
- **목적:** 이름 있는 충격 창을 재현하고 SEP 금리 경로 밴드를 시드로 만든다. 현재 시뮬레이션 북에 정적 비중으로 적용한다.
- **가정:**
  - 정적 비중, 레버리지 ETF는 기초자산 × L에 일별 캐리.
  - 창 날짜는 수익률 날짜(포함), '+20일'은 시장 세션 20개.
  - SEP 밴드는 Vasicek/CIR/HW 금리 경로만 낸다(가격 모형 아님).
  - Brent는 Dated 현물이다.
- **한계:**
  - 생산 호출이 0곳이다(ui·core에서 scenarios를 import하는 모듈 없음, grep).
  - 앵커 일부가 OWNER_INPUT이다(2022 유가 충격 t0, 최신 SEP 표).
  - 정적 비중이라 리밸런싱·증거금을 반영하지 않는다. 실데이터 경로 테스트가 NOT_RUN이다.
- **적용 범위:** 맥락 전용(acts = False). 사이징 모듈 import 금지(정적 스캔).
- **검증 상태:** 테스트로 확인됨. tests/macro_m9_scenarios.py::test_letf_identity_on_a_synthetic_path (golden_value), ::test_sep_band_dispersion_matches_the_band_at_the_horizon (golden_value), ::test_shock_window_on_the_current_book_synthetic_companion, ::test_t_repro_01c_scenarios_identical_paths_under_the_seed, ::test_i11_no_sizing_module_reads_scenarios_or_lab (PASS). NOT_RUN: ::test_scenario_brent_history_refdata, ::test_scenario_kospi_jul_2026_path_refdata, ::test_scenario_latest_sep_table_owner, ::test_scenario_oil_2022_anchor_owner.
- **관련 오류:** -
- **화면:** - (화면 연결 없음)

#### 127. dry run 대체 시계와 공급사 캐시 수집

- **위치:** core/skills/macro_daily.py:DRY_RUN_MARKER:83-84; core/skills/macro_daily.py:DRY_RUN_CACHE:86-91; core/skills/macro_daily.py:DryRunClocks:1285-1378; core/skills/macro_daily.py:read_cache_csv:1381-1392; core/skills/macro_daily.py:dry_run:1395-1436
- **목적:** 서명 달력과 공식 종가 없이 파이프라인 전체를 보여준다. 로컬 Yahoo·FRED 캐시를 vendor_close로 임시 PIT 저장소에 넣고 backtest 모드로 KR·US 결정을 돌린다. 모든 북 DISARMED, 빨간 칩.
- **가정:**
  - 세션 = 평일 − 레거시 KRX.json/US.json 휴장(2026-27, 범위 밖은 평일).
  - 고정 경계: KRX 06:30:30Z(2016-08-01 전 06:00:30Z), NYSE 16:00 ET + 30초(:1319-1321).
  - 규칙 기반 발행 시각(H.15 다음 영업일 16:15 ET 등).
  - 수신 시각 = 캐시 파일 mtime(:1412). 백테스트 vendor는 'Yahoo'.
- **한계:**
  - mtime에 의존한다. 복제·압축 해제로 시각이 바뀌어 결과가 달라지고 장중 봉이 종가가 될 수 있다(C01-03, K-h). cloud run1에서 test_dry_run_end_to_end_on_the_local_cache가 FAIL, run2는 PASS였다.
  - 고정 경계(KRX 06:30:30Z, NYSE 16:00 ET + 30초)라 수능일·조기폐장 시각을 반영하지 못한다. 레거시 KRX.json의 휴장 4일과 수능 특수세션 2일은 d865c7f에서 넣었으므로 세션 판정은 맞아졌다(CAL-10).
  - 캐시 목록에 KOSPI_OFFICIAL_CLOSE가 없어 KR vt는 fail_closed다. 테스트가 이를 단언한다(tests/macro_m8_pipeline.py:873-874).
  - ingest가 낸 stale_carry 플래그를 vt 창에 넘기지 않는다. 파이프라인은 live에서만 수집 보고서를 읽는다(macro_daily.py:457-460). 캐시에 평평한 0거래량 행이 있으면 그 세션이 빠져 US vt가 fail_closed가 된다(코드상, 미재현).
  - 캐시 라이선스·매니페스트가 없다(SF-06).
- **적용 범위:** 시연·QA 전용. 판정 작성·engine_feed·ARM은 불가다. 결정 근거로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m8_pipeline.py::test_dry_run_end_to_end_on_the_local_cache (run2 PASS, run1 FAIL: 감사 보고서 7절; US vt ok·KR vt fail_closed 단언 :871-874), ::test_i01_mechanics_five_artifacts_gates_by_role_and_feed_scope (PASS). NOT_RUN: ::test_i01_golden_clauses_refdata.
- **관련 오류:** C01-03(P2, TA-04 병합), K-h, CAL-10(P2, d865c7f에서 KRX.json 행 반영, 고정 경계는 남음), SF-06(P2)
- **화면:** Overlay state 'Run macro_daily → Dry run (local vendor data)' 버튼(ui/macro_state_panel.py:730), Artifacts 'Dry run', 빨간 칩 'VENDOR DATA · DRY RUN'

#### 128. 테크펀드 스크린과 북 엔진(SCR-1/2, B1-B4, FS-2)

- **위치:** core/quant/tf_screens.py:eligible:199-234; core/quant/tf_screens.py:features_at:274-300; core/quant/tf_screens.py:quantile_groups:321-340; core/quant/tf_screens.py:p6_composite:355-375; core/quant/tf_screens.py:dilution_at:408-417; core/quant/tf_screens.py:screen_flags:460-476; core/quant/tf_screens.py:reversal_guard:489-504; core/quant/tf_screens.py:limit_lock_mask:529-545; core/quant/tf_screens.py:l0_composite:560-581; core/quant/tf_screens.py:pair_share_kospi:594-602; core/quant/tf_screens.py:rebuilt_kospi:615; core/quant/tf_books.py:cap_weights:67-83; core/quant/tf_books.py:run_books:206-228; core/quant/tf_books.py:band_select:251-264; core/quant/tf_books.py:turnover_limit:278-286; core/quant/tf_books.py:capacity_check:289-297; core/quant/tf_books.py:daily_net:300-306; core/quant/tf_books.py:daily_stats:315-323; core/quant/tf_books.py:monthly_stats:358-367; core/quant/tf_books.py:break_even_bps:370-379; core/quant/tf_books.py:fs2_momentum_book:382-399
- **목적:** KRX 전 종목 패널에서 SCR-1/2 스크린(F1-F8, 복권형 P6, 희석 DIL), 기본·필터 북 B1-B4, 밴드·회전율·용량 규칙, 일간 IR·월간 NW t, 손익분기 bp, FS-2 제약 모멘텀(FORWARD-SIM)을 계산한다. 연구·표시 코드다.
- **가정:**
  - 적격성은 t−1 행으로 판단한다(INV-3).
  - 매수 후 다음 리밸런싱까지 보유(비중 표류). 정지 종목은 이월, 상장폐지는 현금 동결(스트레스 −30%/−100%).
  - 비용 편도 35/70bp, IR = 평균/표준편차(ddof 1) × √252, 월간 NW 6 lag, 단일 종목 캡 5%.
- **한계:**
  - KRX 전 종목 패널(1995-2026)이 없어 모든 카드가 NOT RUN이다.
  - 랩 상수는 참조값으로만 고정했다. 실데이터 재계산이 불가능하다.
  - 쌍 비중 캡(0.35, 0.45 트리거)과 w/3 정규화는 소유자 확인 전 제안이다.
  - 앱 화면이나 매크로 파이프라인은 이 모듈을 import하지 않는다(grep: tf_books↔tf_screens, tf_gov, docs/techfund_study.py:50뿐).
- **적용 범위:** 연구·표시. 어떤 북·매크로 acting 파라미터에도 들어가지 않는다(rulings 3.7-3.9).
- **검증 상태:** 테스트로 확인됨. tests/macro_tf_screens.py 27 PASS / 2 NOT_RUN: ::test_gold_02_pair_share_recomputed_from_the_lab_columns (golden_value), ::test_ser_01_daily_basis_ir_and_cost_timing (golden_value), ::test_ser_01_monthly_basis_series_reproduces_the_lab_form (golden_value), ::test_book_01_rebalance_hold_stuck_and_delisting_stress, ::test_scr_01_f4_cut_size_and_ordinal_stability, ::test_lock_01_limit_lock_at_each_krx_limit_era (PASS). NOT_RUN: ::test_krx_01_screen_card_runs_need_the_krx_panel, ::test_idx_02_rebuilt_kospi_check_values_need_the_krx_panel, tests/macro_tf_gov.py::test_krx_tech_fund_card_formal_runs_need_the_krx_panel.
- **관련 오류:** -
- **화면:** 직접 화면 없음. Model cards 뷰의 테크펀드 카드 초안은 docs/techfund/*.draft.json 정적 파일이다(ui/macro_cards_view.py:26, :159, :239). Research register 뷰 가중치 표(w/3 열)는 council_pages_data.json의 정적 R3 사전값이다(ui/research_view.py:86-110, :288-293). 이 모듈의 계산값이 아니다.

#### 129. 테크펀드 거버넌스 통계(GOV-1..11: SPA, BH FDR, 귀속, β 북)

- **위치:** core/quant/tf_gov.py:pw_block_dd2:116-124; core/quant/tf_gov.py:attribution_block:141-175; core/quant/tf_gov.py:ledoit_wolf_sharpe_test:178-188; core/quant/tf_gov.py:primary_statistic:197-228; core/quant/tf_gov.py:spa_test:257-291; core/quant/tf_gov.py:bh_fdr:294-310; core/quant/tf_gov.py:family_gate:313-333; core/quant/tf_gov.py:TrialRegistry:350-376; core/quant/tf_gov.py:expected_live:385-389; core/quant/tf_gov.py:step8_subperiods:404-428; core/quant/tf_gov.py:break_even_screen:431-442; core/quant/tf_gov.py:stress_table:455-484; core/quant/tf_gov.py:incubation:527-553; core/quant/tf_gov.py:beta_hat:556-567; core/quant/tf_gov.py:s_beta_book:570-582; core/quant/tf_gov.py:inv1_bound_line:585
- **목적:** 테크펀드 카드에 덧붙이는 강화 규칙과 보고 줄이다. Hansen SPA(정상 부트스트랩), BH FDR q 0.10, Holm, 팩터 귀속(NW t), LW Sharpe 검정, 블록 max(10, PW(d), PW(d²), 2 × 보유), 기대 라이브 0.6 × OOS, 손익분기 < 2 × 비용이면 사전 REJECT, 스트레스 표, 오염 로그, 252세션 인큐베이션, β 북.
- **가정:**
  - 시드·B·블록은 인자다. numpy/scipy만 쓰고 arch는 쓰지 않는다.
  - β는 직전 252세션 OLS(OQ-03 해석, 제안).
  - Council v2.0 값과 다르면 Council이 우선한다.
- **한계:**
  - 대상 카드가 패널 부재로 NOT RUN이다.
  - 계획 헤어컷·팩터 기울기 임계값은 제안 값이다.
  - SPA의 크기·검정력은 합성 자료로만 확인했다.
- **적용 범위:** 테크펀드 CARD-O 카드의 추가 보고·강화. 매크로 acting 파라미터를 바꾸지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_tf_gov.py 20 PASS / 2 NOT_RUN: ::test_gov2_spa_size_on_pure_noise_rule_families, ::test_gov2_spa_power_on_a_planted_rule_and_family_gate, ::test_gov2_bh_fdr_and_holm_on_known_p_vectors, ::test_gov3_attribution_recovers_beta_alpha_and_labels_a_factor_tilt (golden_value), ::test_gov4_pw_block_dd2_floors_at_10_and_twice_the_holding_period, ::test_gov11_s_beta_book_and_the_prior_252_session_beta_window, ::test_gov9_stress_table_windows_and_worst_rolling_relative_loss (PASS).
- **관련 오류:** -
- **화면:** 직접 화면 없음. Model cards 뷰 CRY-1 줄(docs/techfund_study.py 산출 JSON을 통해 간접)

#### 130. CRY-1 대조 실험(크립토 카드 C3 추세, 공급사 캐시)

- **위치:** docs/techfund_study.py:load_close:348-358; docs/techfund_study.py:c3_walk:366-369; docs/techfund_study.py:_score:372-373; docs/techfund_study.py:gov4_tightened:388-400; docs/techfund_study.py:gov_block:403-413; docs/techfund_study.py:split_lines:416-430; docs/techfund_study.py:run_cry1:440-515; core/quant/validate.py:sharpe:137-143
- **목적:** 크립토 카드 C3(추세)의 R3 '무엇이 판정을 바꾸나' 조건을 공급사 캐시로 시험한다. 변동성 맞춘 롱 대조, 2024-01-10 분할, ETH 재현. 결과는 'vendor data, labelled trial' 라벨로 보인다.
- **가정:**
  - Binance BTCUSDT·Upbit KRW-BTC 공개 일간 종가(공식 종가 아님), 편도 10bp.
  - walk_forward 선택, 시행 수 N = 11 + 3 = 14로 R-23 원장 등록.
  - LW 스튜던트화 부트스트랩과 블록 10 부트스트랩 p값, B 2000.
  - 대조 τ와 vol_target이 같은 √252를 써서 변동성 맞춤 자체는 일관된다(:478-480).
- **한계:**
  - SR·ΔSR이 validate.sharpe(√252)로 연율화된다(docs/techfund_study.py:424-425, validate.py:48, :143). 365봉 자료라 표시 SR·ΔSR이 약 17% 작다(√(252/365) = 0.831). p값은 같은 상수로 스케일되어 그대로다(코드 구조상, 미실행). D12-11/M-03과 뿌리가 같지만 이 화면은 감사 목록에 없다(신규 관찰).
  - 자르는 시각 민감도는 장중 봉이 없어 NOT RUN이다.
  - 거래소마다 결과가 갈린다(Upbit PASS p 0.028, Binance REJECT p 0.243, README). 자료 민감도가 크다.
  - Bonferroni 메모만 출력하고 적용하지 않는다(D-24로 C3 PASS 유지).
  - 전체 스위트가 보호 대상 캐시 파일을 읽는다(TA-12).
- **적용 범위:** 라벨 붙은 연구 시행. 정식 카드 실행이나 판정 변경 근거로 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. tests/macro_tf_gov.py::test_cry1_study_runs_offline_end_to_end_on_the_local_caches (PASS: 라벨·시행 수 14·C3 카드 sr_oos 자기 재현 1e-9만 단언. 같은 코드의 자기 일치일 뿐 연율화·통계의 정확성은 단언하지 않음), ::test_cry1_cut_time_sensitivity_needs_intraday_candles (NOT_RUN). 결과 파일 docs/techfund/cry1_*.json. 독립: financial_calcs.md M-03(게이트 validate.sharpe의 √252 문제 재현).
- **관련 오류:** D12-11(P1, M-03 병합), TA-12(P3), 신규 관찰(CRY-1 표시값 √252)
- **화면:** Macro → Model cards 뷰 'CRY-1 control results (crypto card C3)'(ui/macro_cards_view.py:177-205, :242-245)

#### 131. R-30 변동성 추정기 경주와 단계 게이트(SMA20 대 EWMA·GARCH-t·GJR-t·log-HAR·comb)

- **위치:** core/quant/vol_estimators.py:ESTIMATORS:34; core/quant/vol_estimators.py:sma:111-128; core/quant/vol_estimators.py:ewma:130-150; core/quant/vol_estimators.py:fit_ok:152-172; core/quant/vol_estimators.py:garch_t:223-228; core/quant/vol_estimators.py:gjr_t:229-236; core/quant/vol_estimators.py:log_har_range:285-340; core/quant/vol_estimators.py:comb:356-363; core/quant/vol_estimators.py:sigma_for_decision:395-420; core/quant/forecast_eval.py:qlike:103-107; core/quant/forecast_eval.py:dm_test:147-157; core/quant/forecast_eval.py:mcs:203-247; core/quant/forecast_eval.py:b5:354-400; core/quant/forecast_eval.py:stage1:523-552; core/quant/forecast_eval.py:stage2:553-559; core/quant/forecast_eval.py:stage3:560-584; core/quant/forecast_eval.py:evaluate_estimators:585-626; core/quant/forecast_eval.py:estimator_gate:724-771; core/quant/risk_layer.py:ESTIMATORS:258; core/skills/macro_daily.py:735
- **목적:** R-06 σ의 후보 추정기를 같은 예측 목표로 비교한다. 3단계 게이트(B5 보정 → MCS → 책 성과)를 통과해야 R-30 카드 개정으로 교체를 허용한다. 지금 운영 σ는 SMA20뿐이다.
- **가정:**
  - 예측 대상 y[t, h] = Σ_{j=1..h} r²_{t+j}, 시점 t 종가까지 정보만 쓴다.
  - 손실은 QLIKE(Patton 2011)·MSE·tick loss. DM은 Bartlett HAC(lag max(10, 2h))와 HLN 보정.
  - MCS는 T_max, 정상 부트스트랩(평균 블록 max(10, 2h)), 90% 집합 = p ≥ 0.10.
  - B5: 200개 이상 원점에서 5% VaR 초과가 0.05 ± 2√(0.05·0.95/n) 안이고 10구간 PIT χ² p ≥ 0.01(FHS 형식).
  - GARCH-t·GJR-t는 10년 이상 확장 창, 21 원점마다 재적합, 최적화기 지속성 상한 0.9995.
  - 도전자가 실패하면 정확히 SMA20으로 돌아가고 기록한다. 섞지 않는다(:395-420).
- **한계:**
  - 운영에서 돌지 않는다. macro_daily가 vol_state에 gate=None을 넘겨 'estimator_b5 NOT_RUN', 'gate not run'이 찍힌다(macro_daily.py:735, risk_layer.py:441-443). risk_layer.ESTIMATORS에는 sma20만 있고 다른 이름은 market_vol_target이 거부한다(risk_layer.py:258, :346-348). 쓰임은 연구 스크립트 docs/vol_backtest.py뿐이다(grep).
  - 실데이터 골든(KOSPI B5, SPY, 사이징 북)이 NOT_RUN이다.
  - 정규 분위로는 모든 추정기가 PIT에서 실패한다는 전제라 σ를 정규 VaR로 보이지 않는다(forecast_eval.py 모듈 docstring).
- **적용 범위:** R-06 σ 교체 심사 연구 도구. 운영 σ를 바꾸려면 계수된 R-30 카드 개정이 필요하다. 주식 북에는 도전자를 쓰지 않는다(item 33).
- **검증 상태:** 테스트로 확인됨. tests/macro_m3_estimators.py 12 PASS / 8 NOT_RUN(cloud run2). PASS: ::test_sma20_and_ewma_definitions, ::test_causality_no_lookahead, ::test_t_est_04_fallback_to_sma20_no_blend, ::test_t_est_01_mcs_synthetic_companion, ::test_dm_hln_factor_and_legacy_dm_unchanged, ::test_t_b5_01_synthetic_clauses_and_bands, ::test_estimator_gate_reads_through_pit_and_is_schema_valid, ::test_comb_is_half_sum_and_fails_when_either_leg_fails; tests/macro_m4_integration.py::test_estimator_harness_sma20_is_risk_layer_sma_vol. NOT_RUN: ::test_t_b5_01_kospi_golden_refdata, ::test_t_est_01_i_10_dlb_t1a_refdata, ::test_g_b5_02_spy_refdata_with_smoke_on_local_cache, ::test_g_est_04_sizing_books_refdata.
- **관련 오류:** TA-01(P2, REFDATA NOT_RUN 대부분 재현 코드 대기)
- **화면:** Overlay state Vol strip의 estimator 필드(estimator_b5 NOT_RUN, ui/macro_state_panel.py:340-357)

### 6.6 가상자산·기타

#### 132. M6-01 김치 프리미엄 수준과 1년 z

- **위치:** core/crypto/analytics.py:kimchi_premium:69-107; ui/crypto_page.py:_live:45-57(FX :52); ui/crypto_page.py:analyze:62-63; ui/crypto_page.py:build_crypto_page:158-159,163-164,171; data/crypto/crypto_client.py:UpbitPublic.daily:137-165(:151 UTC 날짜, :161 결측→0.0); data/crypto/crypto_client.py:BinancePublic.daily:192-226; core/ficc/data.py:synthetic_series:320-352(합성 FX 수준 :345); docs/asset_expansion_study.py:run_kimchi:534-554
- **목적:** 한국 거래소 BTC 원화 가격과 해외 달러 가격의 괴리(%)를 보인다. 1년 z로 지금 괴리가 과거 대비 어디에 있는지 보인다.
- **가정:**
  - p = P_Upbit(KRW-BTC) / (P_Binance(BTCUSDT) × USDKRW) − 1(:82). USDT를 1 USD로 본다(DF-06).
  - 두 거래소 일봉 모두 UTC 날짜 봉이다(Upbit candle_date_time_utc, crypto_client.py:151; Binance open time UTC, :221). 날짜 교집합만 쓴다(:73).
  - USD/KRW는 FRED DEXKOUS(뉴욕 정오 고시)를 직전 고시값으로 앞채움한다. 나이 상한이 없다(:76). 첫 고시 전 날짜는 버린다(:77-78).
  - z는 직전 최대 365개 관측의 평균과 표준편차(ddof 1)로 계산한다. 현재 값은 창에 넣지 않는다. 인덱스 90(91번째 관측, 창 90개)부터 계산한다(:84-87). 표준편차가 0이면 z = 0이다.
  - 수수료, 송금 한도, 세금은 넣지 않는다. 해설도 차익거래가 아니라고 밝힌다(ui/crypto_page.py:105).
- **한계:**
  - FX 시각이 다르다. UTC 자정 종가 대 뉴욕 정오 고시다. DEXKOUS(H.10)는 주 1회 공표라 FX 나이 3~10일이 상시 생긴다. 감사 재현(V01-01): 참 프리미엄 +2.00%에서 10일 묵은 FX로 +0.52%가 나왔다(검증자 시나리오 +3.53%). note(:106-107)는 'a few hours of FX drift'라고 적고, 그 note도 화면에 나가지 않는다.
  - FRED가 막히면 auto가 합성 FX(수준 10~99, core/ficc/data.py:345)를 넣는다. 감사 재현에서 프리미엄이 +1,257%였고 칩은 녹색 'source: LIVE'였다. 'USD/KRW: SYNTHETIC' 칩은 회색이다(D03-01, D03-08).
  - USDT가 1달러를 벗어난 구간(예: 2022-05)에는 USDT 기저가 섞인다. 평상시 크기는 미검증이다(DF-06).
  - Upbit 종가 결측이 0.0이 되면 last_pct = −100%가 된다(crypto_client.py:161, D12-03).
  - 오늘 UTC 봉은 미완성이다(DF-03).
  - 이름은 '1y z'지만 표본 앞 275개 관측은 90~364개 창으로 계산한다. 관측이 91개 미만이면 z가 NaN이고 last_z가 0.0으로 바뀌어 '+0.00'으로 보인다(:103).
  - Binance fapi가 막히면 펀딩 호출 예외로 analyze 전체가 실패한다. 화면에는 오류 안내 하나만 남고 김치 프리미엄도 사라진다(SFV-01).
  - Refresh마다 Upbit, Binance, FRED를 순차 호출한다(P01-09, 속도).
- **적용 범위:** 연구용 모니터다(카드 M_C1 REVISE, revise_target 'keep as a monitor; never feed the composite'). 차익거래 수익 추정, 매매 신호, 합성 지표 입력으로 쓰면 안 된다. USD/KRW 출처가 SYNTHETIC이거나 FX 나이가 3일을 넘으면 값을 믿으면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_crypto_analytics(core/crypto/analytics.py:302-312: 합성 AR(1) 프리미엄, 평일만 있는 FX 앞채움에서 평균 오차 <0.3%p, ADF p<0.05, 반감기 3~15일). tests/expansion_acceptance.py::selfcheck_crypto_page(ui/crypto_page.py:214-224, 합성 경로만). 이번 세션 HEAD 049306c에서 ui/crypto_page.py 자체 검사 ok. 카드 docs/asset_expansion/cards/M_C1_kimchi.json(REVISE, n 3,288, mean 1.94%, max 58.8%). 실데이터 FX 문제는 감사 V01-01과 D03-01 재현이 근거다. 독립 재계산은 없다. HEAD 재확인: ui/crypto_page.py:52, core/crypto/analytics.py:76, :106-107은 감사 때와 같다.
- **관련 오류:** V01-01, D03-01, D03-08, DF-06, D12-03, DF-03, SFV-01, P01-09, NEW-M6-15
- **화면:** Crypto: stat 'Kimchi premium'(\|p\|>3%면 빨강, :163), 'Premium z (1y)'(:164); 차트 'Kimchi premium (Upbit KRW-BTC vs Binance × USD/KRW)'(:171); 칩 'USD/KRW: {source}'(:159); 해설 첫 문장(:103-105); AI 페이로드 kimchi(:125-126)

#### 133. M6-02 김치 프리미엄 7일 예측 회귀(기울기, Newey–West t)

- **위치:** core/crypto/analytics.py:kimchi_premium:88-101; core/crypto/analytics.py:_hac_var:110-116; core/crypto/analytics.py:38(newey_west_t 임포트, 미사용); ui/crypto_page.py:narrative:106; ui/crypto_page.py:payload:126; docs/asset_expansion_study.py:run_kimchi:534-554(게이트 :539)
- **목적:** 프리미엄 z가 다음 7일 BTC 로그수익률을 예측하는지 기울기와 HAC t로 보인다.
- **가정:**
  - 다음 7행(7일) BTCUSDT 로그수익률을 z에 OLS 회귀한다(:88-95).
  - 겹치는 7일 수익률이라 Bartlett 가중 HAC, 시차 6을 쓴다(:98-100).
  - z와 선행 수익률이 모두 있는 날만 쓴다. 60개를 넘을 때만 계산한다(:93).
  - 정상성과 선형 관계를 가정한다.
- **한계:**
  - [결함] 표준오차가 √n배 작다. :100은 se = sqrt(_hac_var·n)/Σxc²인데 _hac_var(:116)는 이미 S/n을 돌려준다. 바른 식은 sqrt(_hac_var)·n/Σxc²(= sqrt(n·S)/Σxc²)다. :38의 newey_west_t는 평균의 t라 OLS 점수(평균 0)에 그대로 쓸 수 없다.
  - 합성 200회 대조에서 코드 t / statsmodels HAC t 비율이 √n_ok와 정확히 같다(n_ok 1,403에서 37.46). 귀무(BTC와 프리미엄 독립)에서 \|t\|>2 비율: 코드 0.95, statsmodels 0.10.
  - 카드 M_C1의 pred_t +6.15(n 3,288, z는 인덱스 90부터라 n_ok 약 3,191)는 바른 식으로 약 +0.11이다. 게이트가 t<−2를 요구해 REVISE 판정은 바뀌지 않는다.
  - 화면 기본 730일(n_ok 약 633)에서는 t가 약 25배 부풀어 해설에 나온다.
  - 지속적 회귀변수(z, φ≈0.95)와 겹치는 표본이라 바른 HAC도 귀무에서 약 10% 기각한다(\|t\|>2 기준).
- **적용 범위:** 기술 통계다(카드: descriptive tile only). 수정 전에는 t 값을 인용하거나 예측 근거로 쓰면 안 된다. 매매 신호 금지.
- **검증 상태:** 미검증. 자체 검사는 isfinite(pred_t)만 단언한다(core/crypto/analytics.py:313). 독립 대조: docs/nautilus_bridge/register_evidence/M6_crypto_misc/c1_kimchi_hac.py(statsmodels OLS cov_type HAC, maxlags 6, use_correction False, 200회). 이번 검증에서 다시 실행해 같은 결과를 얻었다(비율 37.46 = √1403, 귀무 기각 0.95 대 0.10). 기울기는 일치. 카드 M_C1_kimchi lines[2]. 감사 141행에 없는 신규 결함.
- **관련 오류:** NEW-M6-01
- **화면:** Crypto 해설 '…its predictive slope on next-week returns is … (t …)'(ui/crypto_page.py:106); AI 페이로드 kimchi.pred_t(:126); 카드 M_C1 문장

#### 134. M6-03 평균회귀 진단(ADF p, AR(1) 반감기) 공용 함수

- **위치:** core/quant/strategies.py:half_life:255-263; core/quant/strategies.py:adf_pvalue:266-271; 호출: core/crypto/analytics.py:104(김치), :173-175(ETH/BTC); ui/etf_page.py:77(ETF 괴리); core/quant/strategies.py:pairs:307(pairs, M2 등록부)
- **목적:** 시계열이 평균으로 돌아오는지(ADF p)와 충격이 반으로 주는 기간(반감기)을 보인다.
- **가정:**
  - ADF: statsmodels adfuller, 기본 상수항(regression 'c'), autolag AIC. 모든 예외를 NaN으로 바꾼다(:266-271).
  - 반감기: x_t = c + φ·x_{t−1}를 OLS로 적합하고 −ln2/lnφ. 단위는 관측 간격(일 또는 세션). 관측 10개 미만이면 inf(:259-260).
  - 선형 AR(1), 상수 평균, 구조 변화 없음을 가정한다.
- **한계:**
  - [결함] φ ≤ 0(가장 빨리 되돌아오는 경우)에도 inf를 돌려준다(:263). docstring은 'inf when φ ≥ 1'만 말한다. 백색잡음 504개 표본의 53%가 inf다. ETF 해설은 inf를 'slow-moving enough to matter for entry timing'으로 읽어 뜻이 반대가 된다.
  - statsmodels가 없거나 검정이 실패하면 NaN이 경고 없이 나온다. requirements.txt:10은 6054b33에서 선언했지만 pyproject.toml:10-17에는 아직 없다. eth_btc_test는 NaN이어도 'no rejection' 판정을 낸다(FC-02 미수정분).
  - 설치된 statsmodels 0.15.0은 adfuller 반환형 FutureWarning을 낸다(0.16 또는 2027-07 이후 중 늦은 쪽에서 기본 반환형 변경). 지금은 [1] 인덱스가 동작한다.
  - 반감기 구간이나 표준오차가 없다.
- **적용 범위:** 기술적 진단이다. 공적분, 차익, 진입 시점 판단의 단독 근거로 쓰면 안 된다. φ ≤ 0 결함 수정 전에는 반감기 inf를 '느리다'로 읽으면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_crypto_analytics(φ=0.9 합성에서 ADF p<0.05, 반감기 3~15일, 참값 6.6일). tests/expansion_acceptance.py::selfcheck_strategies(core/quant/strategies.py:463 AR(0.8) 반감기 참값 ±1.0; :443-444 공적분 합성에서 ADF 기각 비율 >0.6, 반감기 중앙값 3~15). φ≤0 동작: docs/nautilus_bridge/register_evidence/M6_crypto_misc/c3_half_life.py(백색잡음, φ=−0.3, 테스트용 0.2·sin(1.7t) 모두 inf). 이번 검증에서 다시 실행해 같은 결과(inf 비율 0.53). FC-02는 docs/audit/2026-10-27/functional_completeness.md:126.
- **관련 오류:** functional_completeness/FC-02 (병합: TA-03), K-a(requirements.txt만 반영), NEW-M6-03
- **화면:** Crypto stat 'Half-life'(:164)와 해설 ADF p; ETF 칩 'half-life … sessions', 'ADF p'(ui/etf_page.py:210-211)와 해설(:140-144); Strategy Lab pairs 진단(M2)

#### 135. M6-04 펀딩 캐리 연율화, 백분위, 과밀 플래그

- **위치:** core/crypto/analytics.py:funding_carry:136-149; data/crypto/crypto_client.py:FundingSeries.daily:97-102; data/crypto/crypto_client.py:BinancePublic.funding:228-256; ui/crypto_page.py:_live:51; ui/crypto_page.py:build_crypto_page:165-167,173-175
- **목적:** BTCUSDT 무기한 선물 펀딩을 연 캐리(%)로 바꾸고, 과거 대비 위치(백분위)와 과밀 여부를 보인다.
- **가정:**
  - 일별 값 = 그날(UTC) 펀딩율 합(보통 8시간 3회). 7행 이동평균 × 365 × 100(:142-145). 단리 합산이며 복리가 아니다.
  - 백분위 = 불러온 기간(화면: 지금부터 min(Days, 1500)일 전까지) 중 현재 값 이하의 비율. 현재 값도 포함한다(:147-148).
  - 플래그: 백분위 ≥ 0.9 'crowded long', ≤ 0.1 'crowded short'(:149).
  - 양(+)이면 롱이 숏에 지급한다.
- **한계:**
  - 오늘 UTC 날짜는 1~2회분만 합산되어 00:00~16:00 UTC에 아래로 치우친다(감사 실측 약 −0.05~−0.11%p, DF-03).
  - 백분위 기준 기간이 Days 입력에 따라 바뀐다. 2019-09-10 이전 자료는 없다.
  - 이동평균은 7행 기준이다. 펀딩이나 현물 날짜가 비면 7일보다 긴 구간이 섞인다(:138 날짜 교집합).
  - core/crypto/analytics.py:144는 ×3×365로 계산한 뒤 :145가 덮어쓰는 죽은 줄이다(값 영향 없음).
  - fapi 단일 호스트라 막히면 화면 전체가 실패한다(SFV-01).
- **적용 범위:** 레버리지 수요의 기술적 모니터다. 실제 캐리 수익(비용, 증거금, 청산 위험 제외 전)이나 매매 신호로 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. 자체 검사는 n, 유한성, 0≤백분위≤1, 플래그 값만 단언한다(core/crypto/analytics.py:314-316). ×365 환산은 코드 읽기로 확인. 카드 docs/asset_expansion/cards/M_C4_funding.json stats(5.55%/yr, 백분위 0.39, 2,573일).
- **관련 오류:** DF-03, SFV-01, NEW-M6-13
- **화면:** Crypto stat 'Funding (ann.)'(플래그면 빨강, 툴팁 플래그), 'Funding pct'(:165-167); 차트 'Perpetual funding, 7-day mean annualised'(:173-175); 해설 둘째 문장(:109-111); AI 페이로드 funding(:127-128)

#### 136. M6-05 펀딩 십분위 이벤트 스터디와 부트스트랩 p

- **위치:** core/crypto/analytics.py:funding_carry:150-161; docs/asset_expansion_study.py:run_funding:556-572(게이트 :560); ui/crypto_page.py:narrative:109-111; ui/crypto_page.py:analyze:94-96(판정 칩)
- **목적:** 펀딩 상위 10% 날 뒤 30일 BTC 수익이 하위 10% 날 뒤보다 낮은지(BIS WP 1087의 부호) 검정한다.
- **가정:**
  - 7일 평균 펀딩의 전 표본 10%, 90% 분위로 날을 고른다(:154, 사후 기준).
  - 다음 30일 로그수익률 평균을 비교한다. 날짜가 겹친다(:150-151).
  - p = 두 집단을 각각 독립 복원추출(iid) 2,000회 했을 때 평균차 ≥ 0인 비율. seed 3(:156-159). 각 집단이 10개를 넘을 때만 계산한다.
- **한계:**
  - [결함] 30일 선행 수익률이 29일씩 겹치고 상위 십분위 날이 시간상 뭉치는데 iid 부트스트랩을 쓴다. 귀무(펀딩과 BTC 독립, 펀딩 AR(1) φ 0.98) 300회 모의에서 p<0.05 비율이 0.373이다(명목 0.05). 반대쪽 p>0.95 비율도 0.33이라 양쪽 모두 과신한다.
  - 카드 M_C4 PASS('BIS sign confirmed', p 0.000)와 README.md:286 'the BIS sign confirmed'는 이 p에 기댄다. 블록 부트스트랩에서 판정이 유지되는지는 미검증이다.
  - 화면 기본 730일이면 상위 십분위가 약 70일이다. 겹치지 않는 30일 창으로는 3개 남짓 분량이다.
  - 분위 기준이 전 표본이라 사후 정보가 들어간다. 기술 통계로만 의미가 있다.
- **적용 범위:** 기술적 이벤트 스터디다. 수정 전에는 p 값과 PASS를 통계적 확인으로 인용하면 안 된다. 매매 신호 금지.
- **검증 상태:** 미검증. 자체 검사는 p를 검사하지 않는다(core/crypto/analytics.py:314-316). 귀무 모의: docs/nautilus_bridge/register_evidence/M6_crypto_misc/c2_funding_null.py. 이번 검증에서 다시 실행해 같은 결과(300회, p<0.05 0.373, p>0.95 0.33). 카드 M_C4_funding(top −2.94%, bottom +7.72%, tests.bootstrap_p 0.0). 감사 141행에 없는 신규 결함.
- **관련 오류:** NEW-M6-02
- **화면:** Crypto 해설 '…after top-decile funding … (bootstrap p …)'(:110-111); 판정 칩 'funding: PASS'(녹색, :160); AI 페이로드 funding; README.md:286

#### 137. M6-06 ETH/BTC 단위근 검정

- **위치:** core/crypto/analytics.py:eth_btc_test:170-175; ui/crypto_page.py:_live:55(ETHUSDT 일봉); ui/crypto_page.py:analyze:69; ui/crypto_page.py:narrative:117; docs/asset_expansion_study.py:run_ethbtc:574-584(판정 :578)
- **목적:** ln(ETH/BTC)가 평균회귀하는지 본다. 귀무 유지가 예상 결과다.
- **가정:**
  - Binance ETHUSDT와 BTCUSDT 일봉 날짜 교집합. USDT는 비율에서 상쇄된다.
  - ADF(상수항, AIC)와 AR(1) 반감기. z_2y = 마지막 730개(현재 포함) 평균과 표준편차(ddof 1) 기준. 관측 100개 이하면 NaN.
  - 판정: p<0.05면 'mean-reverting at 5 %', 아니면 'no rejection of a unit root (the expected null)'.
- **한계:**
  - p가 NaN이면(statsmodels 없음, 검정 실패) 'no rejection' 판정 문장을 낸다(FC-02 미수정분).
  - adf_pvalue를 두 번 부른다(:173, :175. 결과 같음, 낭비).
  - 구조 변화(예: 이더리움 지분증명 전환)를 고려하지 않는다.
  - 화면은 Days(기본 730일) 표본으로 검정한다. 카드(3,327일)와 판정이 다를 수 있다. 730일이면 z_2y는 표본 전체 z와 같다.
  - 합성 모드의 ETH 주석(ui/crypto_page.py:38)은 지금 코드와 맞지 않는다(PA-10, 표시 무관).
- **적용 범위:** 기술 통계다. 카드 M_C8 REJECT(p 0.136, 반감기 337일, 'closed'). 페어 트레이딩 근거로 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. 자체 검사는 n==400과 판정 문장 존재만 단언한다(core/crypto/analytics.py:317-319). ADF는 statsmodels 구현. 카드 docs/asset_expansion/cards/M_C8_ethbtc.json.
- **관련 오류:** functional_completeness/FC-02 (병합: TA-03), PA-10
- **화면:** Crypto 해설 'ln(ETH/BTC): …'(:117); 판정 칩 'ethbtc: REJECT'(:160); AI 페이로드 ethbtc(:130)

#### 138. M6-07 요일 표(요일 효과, 주말 거래대금)

- **위치:** core/crypto/analytics.py:weekday_table:178-200; ui/crypto_page.py:analyze:70; ui/crypto_page.py:build_crypto_page:180-185; docs/asset_expansion_study.py:run_weekday:586-600(주장 문장 :594-597)
- **목적:** 요일별 BTC 평균 수익률, 변동성, 거래대금을 보이고 요일 효과와 주말 거래대금 감소를 검정한다.
- **가정:**
  - 일간 로그수익률을 그 봉의 UTC 날짜 요일에 배정한다(:179-180).
  - 각 요일 대 나머지의 Welch t, 최소 p × 7(Bonferroni, :191-198).
  - 주말/평일 거래대금(quote volume, USDT) 비율과 Welch t(:196-199).
- **한계:**
  - 거래대금은 추세와 자기상관이 커 iid Welch t의 p(카드 3.2e-35)는 과대 확신이다. 비율 자체는 의미가 있다.
  - 수익률이 두꺼운 꼬리라 평균 비교의 검정력이 낮다.
  - 카드 M_C7(lines, reason 'cost input set')과 README.md:287은 'weekend slippage set at 2× in the crypto backtests'라고 적는다. 그러나 코드 어디에도 주말 비용 배수가 없다(docs/asset_expansion_study.py:60 COST = V.COST_BP_PER_SIDE, crypto 고정 10bp; core/, ui/, data/에서 'weekend' grep 결과 비용 코드 없음).
  - 오늘 UTC 봉은 미완성이다(DF-03).
- **적용 범위:** 기술 통계와 비용 가정 참고용이다. 요일 매매 규칙으로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_crypto_analytics(core/crypto/analytics.py:320-321: 주말 효과를 심은 합성에서 7행, 주말 비율<1, p<0.01). 카드 docs/asset_expansion/cards/M_C7_weekday.json(PASS, Bonferroni p 0.18, 주말 61%).
- **관련 오류:** NEW-M6-10, DF-03
- **화면:** Crypto 카드 'Weekday table (returns %, vol %, mean quote volume)'(:180-185); AI 페이로드 weekday(:130)

#### 139. M6-08 BTC GARCH(1,1)-t 화면 적합과 365일 환산

- **위치:** ui/crypto_page.py:analyze:71-77; ui/crypto_page.py:24(CRYPTO_DAYS, 화면 전용 상수); core/quant/garch.py:fit_garch:446; ui/crypto_page.py:narrative:112-116; ui/crypto_page.py:build_crypto_page:169
- **목적:** 최근 최대 730개 BTCUSDT 일간 수익률로 조건부 변동성, 꼬리(ν), 지속성, 반감기를 보인다.
- **가정:**
  - core.quant.garch.fit_garch(dist 't', profile False)를 그대로 쓴다. μ는 표본평균 고정, 단위분산 t.
  - 엔진은 252로 연율화한다(cond_vol_last = sqrt(σ²_{T+1}·252), garch.py:543). 화면은 cond_vol_last/√252×√365로 365일 기준으로 바꾼다(:75-76).
  - 24/7 일봉이라 반감기 단위는 일이다.
- **한계:**
  - 롤링 검증(카드 D_C2_garch_btc, 원점 3,661개): 95% VaR 초과 5.8%, 99% 1.15%, 90% 밴드 적중 88.3%, PIT 실패로 REVISE. 적합의 78%가 정상성 경계에 붙는다(stationarity_share 0.78). 카드는 Yahoo BTC-USD(2014-09-17부터, docs/asset_expansion_study.py:742)로 돌렸고 화면은 Binance BTCUSDT다.
  - Quant Lab은 같은 BTC를 252로 연율화해 약 17% 낮게 보인다. 두 화면 숫자가 다르다(D12-11).
  - Days<200이면 SMA200 렌더에서 worker가 예외로 멈춘다(MF-01, 이 모델의 오류는 아님).
  - GARCH AIC 모수 수 문제(FC-09)는 엔진 쪽이다. 이 화면은 AIC를 보이지 않는다.
- **적용 범위:** BTC 일간 변동성 상태의 기술이다. 99% VaR 같은 꼬리 위험 수치나 포지션 크기 결정에 쓰면 안 된다(카드 REVISE). 엔진 자체는 M1 등록부가 다룬다.
- **검증 상태:** 코드로만 확인. 추정기는 M1-10에서 독립 검증됐다(docs/audit/2026-10-27-implementation-audit-report.md:585, arch 8.0.0과 우도 차 0.0, 예측 상대오차 3.3e-16). 이 모델 고유의 365 환산(ui/crypto_page.py:75-76)을 고정하는 테스트는 없다. tests/macro_m9_lab.py::test_t_crypto_01_clock_annualisation_and_no_crypto_sleeve(:532-533)는 core.crypto.analytics.CRYPTO_DAYS == 365를 단언하고, 화면이 쓰는 ui/crypto_page.py:24 상수는 보지 않는다. tests/expansion_acceptance.py::selfcheck_crypto_page는 garch n == 730(형태)만 본다. 예측 품질: 카드 D_C2_garch_btc.json(REVISE).
- **관련 오류:** D12-11 (병합: M-03), functional_completeness/MF-01, NEW-M6-20
- **화면:** Crypto stat 'BTC cond. vol (365d)', 'ν'(경계면 빨강, :169); 해설 GARCH 문장과 판정(:112-116); AI 페이로드 garch(:130)

#### 140. M6-09 GARCH 롤링 스코어카드(GARCH-t, GJR-t, GJR-skew-t 대 EWMA)

- **위치:** core/crypto/analytics.py:garch_scorecard:225-295; core/quant/gjr.py:fit_gjr, next_variance, skewt_cdf, skewt_ppf; docs/asset_expansion_study.py:run_garch:498-503, :742
- **목적:** BTC 하루 앞 분포 예측을 EWMA(0.94)와 비교 채점한다(VaR 초과, 90% 밴드, PIT, QLIKE).
- **가정:**
  - 730일 창, 7세션마다 재적합. 그 사이에는 모수를 고정하고 분산만 재귀한다(:250-267).
  - 실현분산 대용은 그날 r²(평균 미차감). 손실은 QLIKE(:282-284).
  - EWMA 초기값은 시작 전 표본분산, λ 0.94(:247-248).
  - 단위분산 t, skew-t 분위수. 정상성 경계 적합은 수렴 실패와 따로 센다(:286).
- **한계:**
  - r² 대용은 잡음이 커 QLIKE 비교의 검정력이 낮다(카드 DM p 0.05~0.23).
  - GJR 정상성은 α+β+0.5γ로 대칭 분포를 가정한다. 왼쪽 꼬리가 긴 skew-t에서는 지속성이 낙관적이다(financial_calcs/FC-08: λ=−0.3에서 E[z²1{z<0}]=0.6048).
  - 재적합이 예외로 실패하면 다음 재적합까지 원점을 건너뛰고 그동안 EWMA도 갱신하지 않는다(:258-261). 예외 실패는 nonconv에 세지 않는다(:286은 반환된 비수렴만 센다).
  - n_refits는 계획 횟수(실패 원점 포함)다(:294).
  - 화면에 직접 나오지 않고 카드 판정 칩으로만 나온다.
- **적용 범위:** 연구 채점용이다. BTC 밖 자산이나 다른 창 길이의 정확도 보증으로 일반화하면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_crypto_analytics(core/crypto/analytics.py:322-332: 모의 GARCH-t 1,400개에서 hits95 0.02~0.09, PIT∈[0,1], QLIKE GARCH < EWMA+0.05, GJR γ≥0, 경계와 실패 상호배타). GJR-t 우도와 Hansen skew-t 밀도는 arch와 독립 대조로 일치(docs/audit/2026-10-27-implementation-audit-report.md:587). 카드 D_C2_garch_btc, D_C2_gjr_btc, D_C2_skewt_btc 모두 REVISE.
- **관련 오류:** financial_calcs/FC-08, NEW-M6-21
- **화면:** Crypto 판정 칩 'garch_btc', 'skewt_btc'(:94-96, :160); 해설 GARCH 판정 문장(:115-116)

#### 141. M6-10 Crypto 화면의 C3 판정 칩과 이동평균 표시(모델 아님, 규칙은 M2-07)

- **위치:** ui/crypto_page.py:analyze:93-96(저장 카드 판정 읽기); ui/crypto_page.py:build_crypto_page:160(판정 칩), :176-179(SMA50/200 차트)
- **목적:** Crypto 화면에서 저장 카드 S_C3_crypto_trend_btcusd·krwbtc의 판정 칩과 BTCUSDT 50·200일 이동평균 선을 보인다. 규칙 자체(crypto_trend)는 M2-07이다.
- **가정:**
  - 판정 칩은 docs/asset_expansion/cards의 저장 판정을 그대로 읽는다. 화면에서 다시 계산하지 않는다.
  - SMA50/200은 단순 이동평균이고 앞쪽 49·199개를 NaN으로 채운다(:177-179). 거래 신호가 아니라 표시용이다.
- **한계:**
  - 표시되는 판정은 저장 카드다. CRY-1에서 Binance BTCUSDT가 REJECT였지만 소유자 판정 D-24로 PASS가 표시된다. 근거와 한계는 M2-07에 있다.
  - 화면의 두 이동평균은 C3 규칙 9표 중 2표뿐이다. 이 선으로 규칙의 현재 상태를 읽으면 안 된다. 현재 신호 상태는 화면에 없다(functional_completeness/FC-04, 감사 12.10).
  - Days<200이면 SMA200 렌더에서 worker가 예외로 멈춘다(functional_completeness/MF-01).
- **적용 범위:** 표시 전용이다. 주문이나 실행 신호로 쓰면 안 된다. 규칙의 가정·한계·적용 범위는 M2-07을 본다.
- **검증 상태:** 코드로만 확인. 화면 표시를 고정하는 테스트가 없다. tests/expansion_acceptance.py::selfcheck_crypto_page는 합성 실행이 끝나는지와 GARCH n, 해설 문구만 본다. 규칙의 테스트와 카드 근거는 M2-07에 있다.
- **관련 오류:** functional_completeness/FC-04, functional_completeness/MF-01(규칙의 오류는 M2-07)
- **화면:** Crypto 판정 칩 'crypto_trend_btcusd', 'crypto_trend_krwbtc'(ui/crypto_page.py:160); 차트 'BTCUSDT with 50/200-day averages'(:176-179)

#### 142. M6-11 크립토 공급사 파생 표시값(perp premium, Upbit 보유 평가)

- **위치:** data/crypto/crypto_client.py:BinancePublic.premium_index:257-265; data/crypto/crypto_client.py:BinancePublic.open_interest_hist:267-277; ui/crypto_page.py:_live:56-57; ui/crypto_page.py:build_crypto_page:168; data/crypto/crypto_client.py:UpbitPublic.ticker:167-172; data/crypto/crypto_client.py:UpbitAccount.balances:314-326; ui/crypto_page.py:analyze:78,81-90; ui/crypto_page.py:payload:131; ui/crypto_page.py:build_crypto_page:186-192
- **목적:** 무기한 선물 마크/인덱스 괴리(%)와 Upbit 보유 자산의 원화 평가액을 보인다.
- **가정:**
  - perp premium = (markPrice/indexPrice − 1)×100(:260-261). 수신 시각의 순간값이다.
  - 보유 평가 = (balance + locked) × Upbit KRW-{coin} 현재가. KRW는 그대로(:85-87).
  - avg_buy_price는 Upbit 기록값이다. 세금은 계산하지 않는다(화면 문구 :191).
- **한계:**
  - KRW 시장이 없는 코인은 tick.get(..., 0.0)으로 0원 평가되어 합계가 조용히 줄어든다(:87). 현재가 결측도 0원이 된다(crypto_client.py:169).
  - 없는 마켓이 목록에 섞이면 Upbit ticker 요청 전체가 실패할 수 있다(API 동작 미검증). 그때는 보유 카드 전체가 오류 안내로 바뀐다(:89-90, :193-194).
  - perp premium 결측 처리: indexPrice가 없으면 0.0, markPrice만 없으면 −100%가 된다(crypto_client.py:260-261). 둘 다 정상 값처럼 보인다.
  - 미결제약정 이력(open_interest_hist)은 받기만 하고 화면과 페이로드에 쓰지 않는다(:57, :78). 그래도 실패하면 화면 전체가 실패한다(SFV-01).
  - 보유 내역(수량, 평균 매수가, 원화 평가)이 AI 페이로드(:131)에 들어가 Deep analysis 때 Anthropic API로 나간다. 화면에 따로 알리지 않는다.
  - avg_buy_price 표시에 통화 단위가 없다(:189).
- **적용 범위:** 표시용이다. 세무, 평가 보고, 손익 계산에 쓰면 안 된다.
- **검증 상태:** 코드로만 확인. tests/expansion_acceptance.py::test_crypto_client_refusals_and_router(balances 파싱: avg_buy_price, total 단언; 주문 엔드포인트 문자열 부재). 원화 평가와 perp premium 계산은 테스트가 없다.
- **관련 오류:** SFV-01, NEW-M6-14, NEW-M6-18, NEW-M6-22
- **화면:** Crypto stat 'Perp premium'(:168); 카드 'Upbit holdings (read-only): ₩…'(:188-192); AI 페이로드 premium_index, holdings(:129, :131)

#### 143. M6-12 ETF NAV 괴리율 통계

- **위치:** data/kis_markets.py:KISMarkets.etf_quote:208-221; data/kis_markets.py:KISMarkets.etf_nav_daily:223-235; data/kis_markets.py:_bars:143-156; ui/etf_page.py:analyze:51-55,73-78; ui/etf_page.py:build_etf_page:199-215
- **목적:** KRX ETF의 가격 대 NAV 괴리율(KIS 'dprt')의 현재값, 평균, z, \|괴리\| 평균, ADF, 반감기를 보인다.
- **가정:**
  - 괴리율과 NAV는 KIS 계산값을 그대로 쓴다. QUANTGEN은 다시 계산하지 않는다(정의와 단위는 실응답으로 미검증).
  - z = (마지막 − 전 표본 평균)/표준편차(ddof 1). 현재 값을 포함한 표본 내 z다(:76).
  - 60세션을 넘을 때만 계산한다(:73). KIS 키가 있어야 한다. 합성·무키 경로에는 없다(:56-59).
- **한계:**
  - 결측 NAV와 괴리율이 0.0으로 들어가 통계가 0% 쪽으로 기운다(kis_markets.py:233-234, M01).
  - 해외 지수 ETF는 NAV 산출 시각이 달라 괴리에 시차가 섞인다. 차익 기회로 읽으면 안 된다.
  - 반감기 φ≤0이면 inf가 나오고 해설이 반대로 읽는다(NEW-M6-03).
  - quote의 as_of는 date.today()다(kis_markets.py:220, D05-06). 렌더가 try 밖이라 quote 필드가 None이면 worker가 예외로 멈출 수 있다(MF-01 구조).
- **적용 범위:** KRX ETF 괴리 상태의 기술이다. 차익거래 신호 금지. 미국 ETF는 NAV가 없어 계산하지 않는다.
- **검증 상태:** 코드로만 확인. tests/expansion_acceptance.py::test_etf_page_sleeves_use_adjusted_closes_and_survive_their_loss(premium_stats 키 존재만 단언), tests/expansion_acceptance.py::test_kis_markets_paging_and_shapes(가짜 전송 형태). 실제 KIS 응답 값은 미검증.
- **관련 오류:** M01, NEW-M6-03, D05-06, functional_completeness/MF-01, functional_completeness/FC-02 (병합: TA-03)
- **화면:** ETF stat 'Price', 'NAV', 'Premium'(\|p\|>0.5%면 빨강), 'Tracking error', 'AUM', 'CU shares', 'LP holding'(:201-207); 칩 'premium z', '\|premium\| mean', 'half-life', 'ADF p'(:210-213); 차트 '{code} price vs NAV'(:214-215); 해설 첫째·둘째 문장(:135-144)

#### 144. M6-13 ETF 슬리브 표본 내 요약(추세 전환, 변동성 목표, 매수 보유)

- **위치:** ui/etf_page.py:analyze:60-72,80-90,119-123; core/quant/strategies.py:trend_switch:162-187; core/quant/strategies.py:vol_target:190-209; core/quant/strategies.py:simulate:69-90; core/quant/strategies.py:summary:97-105; core/quant/history.py:225-226(KIS 수정주가 note, adjustment 'split'); ui/etf_page.py:build_etf_page:227-239
- **목적:** 펀드 자체 가격으로 10개월(210세션) 추세 전환, 12% 변동성 목표, 매수 보유의 Sharpe와 MDD를 보이고 연구 판정을 옆에 둔다.
- **가정:**
  - 가격: KRX는 KIS 수정주가(분할·권리만 조정, 현금 분배금 제외), 실패하면 원가격(표시함). 미국은 FMP 배당 조정 종가.
  - 현금 수익은 연 3%/252 고정이다(:81). 화면에 표시하지 않는다.
  - 비용: KRX 3bp, 그 외 50bp 편도 고정(:84).
  - Sharpe = 평균×252/표준편차(strategies.py:104). 무위험 초과 수익이 아니다.
  - 추세: 210세션 워밍업 뒤 21세션마다 P > SMA210이면 보유. 변동성 목표: min(1, 0.12/σ22), ±10% 밴드. 비중 1 미만이면 주식·현금 비율을 매일 비용 없이 맞춘다고 본다(K-e).
- **한계:**
  - [결함] 창 전체에서 추세가 한 번도 켜지지 않으면(하락장, 상승장의 인버스 ETF) 현금 수익만 남아 표준편차가 부동소수 잡음(~1e-19)이 되고 Sharpe가 약 1e16으로 나온다(vol > 0 검사만, strategies.py:104). 무추세 504세션 400회 중 6.8%. P01-11(validate._col_sharpe)과 같은 원인, 다른 함수다. core/ficc/vol_products.py:33도 summary를 쓴다.
  - 첫 210세션(기본 504의 42%)은 워밍업으로 현금(연 3%, 변동 0)이다. 비교가 추세 쪽으로 치우친다. 무추세 모의 중앙값: 화면 0.11, 워밍업 제외 −0.04, 현금 초과 −0.25, 매수 보유 0.08. 'invested' 비율(:90)은 워밍업 뒤만 세는데 Sharpe는 전 구간이다.
  - KRX는 분배금이 빠진 가격이라 매수 보유가 불리하고, 추세는 현금 3%를 받는다. 가격 기준은 해설에 적지만(:152) 현금 가정은 적지 않는다.
  - 비용 표 대신 하드코딩이다(MF-02). 개별 주식 코드를 넣어도 3bp다.
  - 판정 칸은 계열 판정이다(KRX: 4개 ETF 묶음 S_E1_trend_krx, KODEX 200 단일 S_E2; 미국: S_E1_trend_us, SPY). 입력한 펀드의 판정이 아니다.
  - 단일 경로, 표본 내 숫자다. 연구 카드 S_E1, S_E2는 REJECT다.
- **적용 범위:** 펀드 자체 이력의 기술 통계다. 성과 예측이나 전략 채택 근거로 쓰면 안 된다(해설도 'in-sample descriptive'라고 밝힌다).
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::test_etf_page_sleeves_use_adjusted_closes_and_survive_their_loss(분할을 폭락으로 잡지 않음, 수정주가 실패 표시), tests/expansion_acceptance.py::test_strategies_are_causal, tests/expansion_acceptance.py::selfcheck_strategies(trend_switch 워밍업 0, 추세 보유). 1e16과 워밍업 편향: docs/nautilus_bridge/register_evidence/M6_crypto_misc/c5_etf_sleeve_warmup.py(이번 검증에서 다시 실행: 6.8%, 중앙값 0.11/−0.04/−0.25/0.08, 예 seed 2 Sharpe 3.48e16). ui/etf_page.py 자체 검사(:263-269)는 run_all 밖이다(TA-02). 이번 세션 HEAD에서 수동 실행 ok. 카드 S_E1_trend_krx/us, S_E2_voltarget_kodex200/spy 모두 REJECT.
- **관련 오류:** NEW-M6-04, NEW-M6-05, functional_completeness/MF-02, FC-14, P01-11, K-e, TA-02
- **화면:** ETF stat 'Trend switch Sharpe', 'Trend MDD', 'Vol-target Sharpe', 'Buy & hold Sharpe', 'B&H MDD', 'Study verdict: trend', 'Study verdict: vol target'(:229-237); 차트 '10-month trend switch vs buy-and-hold'(:238-239); 해설 셋째 문장(:147-152)

#### 145. M6-15 KRX·KIS 공급사 지표 표시(모델 아님)

- **위치:** ui/krx_page.py:build_krx_page:32-195(시세 :108-116); data/krx/gateway.py:KRXGateway.quote:62-86; data/krx/gateway.py:KRXGateway.daily:88-101; data/krx/kis_client.py:KISClient.quote:248-270; data/krx/kis_client.py:KISClient.index:307-325; data/krx/krx_market_client.py:172-226; data/kis_markets.py:KISMarkets.etf_quote:208-221; data/kis_markets.py:KISMarkets.etf_components; ui/etf_page.py:build_etf_page:240-245
- **목적:** 시세, 일봉, 공시, 재무, 전 종목 스냅숏, 지수 수준, ETF 구성 종목을 공급사 값 그대로 보인다. QUANTGEN이 계산하는 모델은 없다.
- **가정:**
  - 등락, 등락률, 시가총액, 괴리율, 추적오차, AUM, 구성 비중은 공급사(KIS, KRX Open API, OpenDART) 계산값이다.
  - as_of는 수신 시각(_now, kis_client.py:269, krx_market_client.py:181, :204, :226) 또는 date.today()(kis_markets.py:220)다. 거래소 시각이 아니다.
  - 단위를 맞추지 않는다.
- **한계:**
  - KIS quote as_of가 수신 시각이라 엔진 신선도 가드가 작동하지 않는다(D05-01, 엔진 쪽). KRX 클라이언트도 같다(D05-02). 감사 제안 패치에는 엔진 전체 정지 부작용이 있다(D0405-V02).
  - 지수 등락률 키(prdy_ctrt, kis_client.py:322)가 빈칸일 수 있다(D05-05, 미검증).
  - KIS hts_avls(억원 추정)와 KRX MKTCAP(원)의 단위 차이로 시가총액이 10^8배 다를 수 있다(감사 보고서 :2177, 미검증). 화면은 두 출처를 같은 format_compact로 보인다(krx_page.py:114). ETF AUM은 원 단위로 보고 /1e8 해 '억'을 붙인다(ui/etf_page.py:204). 테스트의 가짜 값이 '1'(tests/expansion_acceptance.py:73)이라 단위는 검증되지 않았다.
  - 결측이 0.0으로 바뀌는 경로가 있다(M01).
  - 키 교체나 모의/실전 전환 뒤 KIS 토큰 캐시가 남아 KIS 경로 전체가 실패할 수 있다(C01-04).
- **적용 범위:** 공급사 원자료 열람이다. 계산 입력, 특히 실행 입력으로 쓰려면 PIT와 신선도 규칙을 거쳐야 한다.
- **검증 상태:** 코드로만 확인. tests/expansion_acceptance.py::test_kis_markets_paging_and_shapes, tests/expansion_acceptance.py::selfcheck_kis_markets(가짜 전송), tests/acceptance.py::test_21_krx_gateway_degrades_with_a_reason(키가 있으면 외부 호출, TA-05), tests/macro_m1_pit.py::test_ro_02_kis_client_accepts_only_allowlisted_quotation_paths(:1040). 실응답 단위는 미검증.
- **관련 오류:** D05-01, D05-02, D05-05, D05-06, D0405-V02, TA-05, C01-04, M01, NEW-M6-17
- **화면:** KRX 화면 표(Quote, Daily OHLCV, Disclosures, Financials, Whole-market snapshot, Index levels); ETF 시세 타일(:201-207)과 'Top constituents' 카드(:240-245)

#### 146. M6-16 Quant 로컬 해설(core/quant/insights.py, 결정적 문장)

- **위치:** core/quant/insights.py:_narrate_garch:59-125; core/quant/insights.py:_narrate_drift:128-135; core/quant/insights.py:narrate_monte_carlo:138-169; core/quant/insights.py:narrate_risk:172-193; core/quant/insights.py:narrate_signals:196-210; core/quant/insights.py:narrate_backtest:213-235; core/quant/insights.py:narrate_portfolio:238-257; ui/ai_panel.py:analysis_panel:26-82; 호출: ui/quant_lab_page.py:375-377, ui/signals_page.py:191-193, ui/portfolio_page.py:193-194
- **목적:** 모델이 아니다. 위에서 계산한 숫자를 키 없이 문장으로 옮긴다.
- **가정:**
  - 숫자를 새로 만들지 않는다. 결과 객체 값을 서식만 바꿔 쓴다.
  - 고정 문턱으로 해석 문장을 고른다: 초과첨도 >2 'fat tails', 왜도 ±0.5, Sharpe >1 'strong', <0 'has not paid', MC 콘 폭 (p95−p05)/spot >0.8 'position sizing matters more than direction', <0.25 'narrow', 신호 반대 \|score\|>20, LR > LR_5PCT, ΔAIC 부호.
  - GARCH 경계, 수렴 실패, 구간 경계를 모두 문장으로 밝힌다(:99-124).
- **한계:**
  - 합성 입력을 해설에서 밝히지 않는다(Quant Lab, Signals, Portfolio; D03-03 소비 행렬).
  - 'position sizing matters more than direction here'(:161-164)는 권고처럼 읽힌다. AI 프롬프트의 'Describe; do not recommend … sizing' 원칙(_SYSTEM :276-278, A3 74cc12e)과 어긋난다.
  - 문턱은 관례값이고 검정이 아니다(예: Sharpe > 1).
  - 결과에 들어간 수치 오류(예: D12-11 크립토 연율화)는 그대로 전달된다.
  - narrate_risk는 화면 호출처가 없다(테스트만). narrate_signals와 narrate_portfolio는 테스트가 없다.
  - 타입용 클래스와 garch 상수를 최상단에서 임포트해 시작 시간을 늘린다(:30-35, P01-13).
- **적용 범위:** 화면 설명이다. 숫자의 출처나 정확도를 보증하지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/quant_acceptance.py::test_narratives_state_their_numbers(:514, MC·risk·backtest 숫자 포함 단언), tests/quant_acceptance.py::test_garch_narrative_states_persistence_and_nu(:786), tests/quant_acceptance.py::test_drift_modes_are_ordered_and_documented(:740). 문장 목록과 조건: docs/build_models_primer.py:1938-1960(9.5절).
- **관련 오류:** D03-03, P01-13, NEW-M6-16
- **화면:** Quant Lab(narrate_monte_carlo), Signals(narrate_signals + narrate_backtest), Portfolio(narrate_portfolio)의 'Analysis' 카드(칩 'engine: local'). Strategy Lab 해설은 ui/strategy_lab_page.py 자체 함수라 이 모듈이 아니다(M2).

#### 147. M6-17 FICC 로컬 해설(core/ficc/insights.py, 결정적 문장)

- **위치:** core/ficc/insights.py:narrate_curve:79-102; narrate_bond:105-139; narrate_swap:142-159; narrate_swaption:162-184; narrate_cap_floor:187-205; narrate_fx_forward:208-224; narrate_fx_option:227-253; narrate_carry:256-297; narrate_ratesim:300-327; narrate_macro:358-377; narrate_daily_brief:380-407; narrate_weekly_strategy:429-509; narrate_structured:512-546; REPORT_PROMPTS:549-574; core/ficc/macro.py:_row:128-139(z 정의); core/ficc/macro.py:_regime_from:170-190; core/ficc/macro.py:_rel_1d:231-235; core/ficc/macro.py:daily_brief:237-252; core/ficc/curves.py:_regime:313-322
- **목적:** 모델이 아니다. 금리, 채권, FX, 구조화, 매크로 결과를 한 문단으로 옮긴다.
- **가정:**
  - 금리는 %, 변화와 스프레드는 bp, 금액은 천 단위 구분으로 쓴다.
  - 판정 문턱: FX 베이시스 \|b\|<5bp면 'within noise'(:220-222), 25Δ 리스크리버설 부호, 곡선 레짐 5bp(curves.py:313-322), 달러 레짐 21관측 변화 ±1.5%(macro.py:184-185), 위험 레짐 VIX·HY z 평균 >0.75 risk-off, <−0.5 risk-on(macro.py:180-181).
  - z는 현재 값을 포함한 마지막 252개 관측의 평균과 표준편차(ddof 0)로 계산한다(macro.py:133-135). 해설은 'trailing 252-session mean'이라고 쓴다.
  - 일간 브리프 'Biggest moves'는 모든 행을 상대 변화 chg/(last−chg)로 정렬한다(insights.py:383-385; macro.py:242 주석이 근사라고 인정).
  - 주간 노트는 정의와 창을 밝히고 'makes no recommendation'으로 끝난다.
- **한계:**
  - 합성 표시는 curve, macro, daily, weekly에만 있다. bond, swap, swaption, cap/floor, FX, carry, ratesim, structured에는 없다(D03-03).
  - narrate_structured는 p.note를 그대로 옮겨 스티프너 경고 문구의 방향 오류를 전파한다(:544-545, M-01).
  - README.md:691-693은 모든 FICC 해설이 정의와 창을 밝힌다고 하지만 주간 노트만 그렇다(PA-12. PA-12 원문의 671-673은 지금 줄 번호가 아니다).
  - chg_1w가 없으면 'following a n/a change'가 된다(:442, PA-13).
  - 스프레드가 0 근처(2s10s 부호 전환)면 상대 변화가 폭발해 'Biggest moves' 맨 위에 오른다.
  - macro as_of는 행들 최신 날짜의 최댓값이라 오래된 행이 섞여도 한 날짜로 읽힌다(D04-01).
  - core/ficc/insights.py 자체 검사는 run_all 밖이다(TA-02).
- **적용 범위:** 화면 설명이다. 해설 문장을 투자 판단 근거로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_narratives_state_their_numbers(:613, 각 해설의 핵심 숫자 포함 단언), tests/ficc_acceptance.py::test_weekly_strategy_states_its_views(:660), tests/ficc_acceptance.py::test_weekly_note_has_no_position_language(:671), tests/ficc_acceptance.py::test_weekly_strategy_ranks_positive_carry_first(:780), tests/ficc_acceptance.py::test_report_prompt_and_deep_analysis_degrade_without_network(:700). core/ficc/insights.py 자체 검사는 run_all 밖(unwired_selfchecks.csv PASS, TA-02). 이번 세션 HEAD에서 수동 실행 ok.
- **관련 오류:** D03-03, M-01, D04-01, PA-12, PA-13, TA-02, NEW-M6-11
- **화면:** Rates, Bonds, FX, Structuring, Macro 화면의 'Analysis' 카드; Macro Daily/Weekly 보고서 버튼(ui/macro_page.py:140-149)

#### 148. M6-18 Crypto·ETF 화면 해설과 AI 페이로드

- **위치:** ui/crypto_page.py:narrative:100-120; ui/crypto_page.py:payload:123-131; ui/etf_page.py:narrative:131-165; ui/etf_page.py:payload:168-173
- **목적:** 모델이 아니다. Crypto와 ETF 계산값을 문장과 AI 페이로드로 묶는다.
- **가정:**
  - 숫자는 analyze 결과 그대로다. 판정은 카드 decision을 읽는다.
  - ETF: 반감기 <5세션이면 'a discount reverts within days … no tradeable premium after a 4–5 bp round trip', 아니면 'slow-moving enough to matter for entry timing'(:142-144).
  - 화면 전체가 합성일 때만 'SYNTHETIC' 문장을 붙인다(crypto :118-119, ETF :163-164).
- **한계:**
  - Crypto: FX만 합성일 때 해설과 페이로드가 밝히지 않는다. 페이로드에 usdkrw_source 키가 없다(D03-01, HEAD :125-131 재확인).
  - Crypto: 예측 회귀 t가 √n배 부풀어 나온다(NEW-M6-01). 펀딩 부트스트랩 p를 과신한다(NEW-M6-02).
  - ETF: 반감기 inf(φ≤0)를 'slow-moving'으로 읽는다(NEW-M6-03). '4–5 bp round trip' 결론은 대표 추종 ETF에서 온 일반화다.
  - ETF: LETF 문장이 연구 판정을 화면 값에 잘못 붙인다(M4-N2, = NEW-M6-08). LETF 지수 출처(index_source)를 해설에 쓰지 않는다(합성일 때는 화면 전체 SYNTHETIC 문장이 대신한다).
  - 'world price'는 USDT 가격이다(DF-06).
  - Crypto 페이로드에 Upbit 보유 내역이 들어간다(NEW-M6-18).
- **적용 범위:** 화면 설명이다.
- **검증 상태:** 코드로만 확인. tests/expansion_acceptance.py::selfcheck_crypto_page(ui/crypto_page.py:214-224)는 'Korea pays', 'SYNTHETIC' 포함과 regime 부재, 페이로드 n 일치만 단언한다. 숫자가 analyze 값과 같은지, 조건 문장이 맞는지는 테스트가 없다. ui/etf_page.py:263-269 자체 검사('SYNTHETIC', 'drag' 포함, 페이로드 beta)는 run_all 밖이다(TA-02). 두 자체 검사 모두 이번 세션 HEAD에서 수동 실행 ok.
- **관련 오류:** D03-01, DF-06, NEW-M6-01, NEW-M6-02, NEW-M6-03, M4-N2(= NEW-M6-08), NEW-M6-18, TA-02
- **화면:** Crypto 'Analysis' 카드(kind crypto_market, :197-198), ETF 'Analysis' 카드(kind etf_structure, :246-247)

#### 149. M6-19 AI 심층 분석(Claude 서술, 모델 아님)

- **위치:** core/quant/insights.py:_SYSTEM:263-282; core/quant/insights.py:_payload_to_json:285-296; core/quant/insights.py:deep_analysis:299-341(요청 :316-321, 응답 :333-341); core/ficc/insights.py:REPORT_PROMPTS:549-574; core/ficc/insights.py:deep_analysis:582-588; ui/ai_panel.py:analysis_panel:40-64; config.py:ai_model:217-218
- **목적:** 모델이 아니다. 화면이 계산한 페이로드를 Claude API(기본 claude-sonnet-5)에 보내 서술형 해설만 받는다. 숫자를 만들지 않는다.
- **가정:**
  - 사용자가 버튼을 누르고 ANTHROPIC_API_KEY가 있을 때만 부른다. 도구 없음, max_tokens 1500, thinking 파라미터 없음, 60초(:316-321).
  - 시스템 프롬프트: 학술 서술, 추천·포지션·크기·예측 금지, 주어진 숫자만 사용(:263-282). FICC 일간·주간 보고서 프롬프트는 synthetic_ids를 simulated로 표시하라고 한다(core/ficc/insights.py:559, :573).
  - 결과는 표시만 한다. 실행 경로가 없다.
- **한계:**
  - 출력 내용을 검증하지 않는다. 숫자를 바르게 인용하는지 확인하는 장치가 없다.
  - 일반 시스템 프롬프트에는 합성·가정 입력을 첫 문장에서 밝히라는 규칙이 없다(D03-04). Crypto 페이로드에는 FX 출처가 없다(D03-01).
  - numpy 배열은 앞(가장 오래된) 50개만 보낸다(:290-291). 확인한 페이로드(crypto, ETF, Quant Lab, Portfolio, Signals)에는 배열이 없어 지금은 잠재 문제다. NaN과 inf는 'NaN', 'Infinity' 글자로 들어간다. 사용자 메시지 안의 텍스트라 요청이 실패하지는 않는다.
  - stop_reason을 보지 않는다(:333-341). 기본 모델 claude-sonnet-5는 thinking을 생략하면 adaptive로 돈다(claude-api 참고 문서). max_tokens 1500에서 잘린 글이 정상처럼 보일 수 있다. 실호출로 빈도는 미검증이다.
  - Crypto 페이로드에 Upbit 보유 내역(수량, 평균 매수가, 원화 평가)이 들어가 버튼을 누르면 Anthropic API로 나간다(ui/crypto_page.py:131). 화면에 알리지 않는다.
  - 같은 입력에도 출력이 달라진다(재현성 없음).
- **적용 범위:** 서술 보조다. 숫자 출처, 판정, 검증 근거로 인용하면 안 된다.
- **검증 상태:** 미검증. tests/quant_acceptance.py::test_deep_analysis_without_key_degrades_without_network(:525, 키 없는 경로만), tests/ficc_acceptance.py::test_report_prompt_and_deep_analysis_degrade_without_network(:700, 프롬프트 문구와 무키 경로), tests/macro_m1_pit.py::test_ro_02_kis_client_accepts_only_allowlisted_quotation_paths(:1040, :1079 'tools' 문자열 부재). 직렬화는 코드 읽기와 페이로드 dict 확인(ui/quant_lab_page.py:340-372, ui/portfolio_page.py:179-191, ui/signals_page.py:173-190). claude-sonnet-5는 유효한 모델 ID다(claude-api 참고 문서, 2026-10-06 캐시. 현행 Sonnet은 claude-sonnet-5-5). 실제 모델 출력은 호출하지 않아 미검증.
- **관련 오류:** D03-04, D03-01, P01-13, NEW-M6-12, NEW-M6-18, NEW-M6-19
- **화면:** 모든 분석 화면의 'Deep analysis' 버튼과 결과 카드(칩 'engine: {model}', ui/ai_panel.py:51-54)

### 6.7 전수 점검에서 추가

#### 150. N-01 Execution 가격 조건 규칙 평가기와 시세 신선도 가드(모의주문, 모델 아님)

- **위치:** core/engine/evaluator.py:_met:85-100; conditions_met:103-116; _order_notional:119-134; Evaluator.evaluate:146-258; Evaluator._freshness:261-314; Evaluator._cap_refusal:317-336; core/markets.py:DEFAULT_HARD_AGE_S:62; Session.max_age_open_s:71; Market.trading_state:157-192; _max_age:219-226; _s:229-235; _RT_MAX_AGE:245; core/engine/runtime.py:no_data_grace:76-77; EngineRuntime._grace:343-350; core/engine/feed.py:QuoteFeed.fetch_many:159-197; QuoteFeed._record:260-273; core/engine/orders.py:OrderBook.counts_today:117-124; OrderBook.notional_today:126-137; core/rules/validation.py:validate:72-158; _contradictions:161-181; data/krx/kis_client.py:KISClient.quote:248-270(as_of=_now() :269); data/krx/gateway.py:KRXGateway.quote:62-85; config.py:ENGINE_TICK_SECONDS:185; NO_DATA_GRACE_TICKS:194
- **목적:** 운영자가 적은 가격 조건(이하, 이상, 하향 돌파, 상향 돌파)이 맞으면 모의주문을 만든다. 시세가 없거나 오래되면 엔진을 멈춘다. 주문 한도를 넘으면 사유를 붙여 거절한다. 실주문 경로는 없다.
- **가정:**
  - 조건은 마지막 체결가 하나로 판정한다. 돌파는 직전 폴링 가격(feed._previous)과 이번 가격을 비교한다.
  - 시세 시각(as_of)은 거래소 시각이라고 가정한다. 장중 한도는 KRX 120초, 그 밖 시장 180초다. NEXTGEN_MAX_AGE_<시장>으로 바꿀 수 있다. 5일을 넘으면 달력과 무관하게 HALT한다.
  - 장이 닫혀 있으면(휴장, 주말, 달력 범위 밖 'unknown') 평가하지 않고 SKIP한다.
  - 시세 누락은 기본 3틱(최대 10틱) 유예 뒤 엔진 전체를 HALT한다. 오래된 시세에는 유예가 없다.
  - 금액 모드 수량은 floor(금액/기준가)다. 기준가는 지정가 주문이면 지정가, 아니면 트리거 가격이다.
  - 체결은 운영자가 손으로 한다. 자동 체결 모형은 없다.
  - 일 한도는 거절되지 않은 주문 금액의 UTC 날짜별 합계다.
- **한계:**
  - KIS 시세의 as_of가 응답 수신 시각이다(data/krx/kis_client.py:269). 그래서 KRX 규칙에서는 신선도 가드가 작동하지 않는다. 거래정지 종목도 FIRED된다(D-05, D05-01).
  - 미래 시각 시세에 하한이 없다. age가 음수면 통과한다(D0405-V01).
  - 모의주문에 트리거 시세 시각이 저장되지 않는다(D05-04).
  - 신선도 HALT는 전역이다. 비유동 종목 하나가 모든 시장의 규칙을 멈춘다(D0405-V02).
  - 일 한도와 당일 거절 판정이 UTC 날짜를 쓴다. ASX는 서머타임(AEDT) 동안 한 세션이 두 UTC 날짜에 걸친다. 2026-11-02 세션의 23:30Z(11-01)와 01:30Z(11-02)가 모두 'open'이다. 한도가 세션 중간에 초기화된다(신규, 미등재). 해외 시장은 FMP 국제 요금제가 없으면 시세가 오지 않아 지금 영향은 작다.
  - 돌파는 폴링 간격(기본 5초) 안의 왕복을 놓친다.
  - 모순 검사는 AND 조건에서 상한이 하한보다 낮은 경우만 본다.
  - 달력 범위(2026-2027) 밖 날짜는 'unknown'이라 모든 규칙이 SKIP된다.
- **적용 범위:** Execution·Rules 화면의 연습용 모의주문에만 쓴다. 매크로 북(core/engine/books.py)과 R-27 체결 모형(orders.simulate_fill)과는 별개다. 실주문, 자동 체결, 가격 예측에 쓰면 안 된다. D-05를 고치기 전에는 KRX 규칙의 신선도 판단을 믿으면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/engine_acceptance.py::test_07_stale_quote_halts_the_engine, ::test_08_missing_quote_halts_rather_than_skipping, ::test_10_max_triggers_rejects_with_a_reason, ::test_11_per_order_cap_rejects, ::test_12_daily_cap_counts_prior_orders, ::test_16_crossing_needs_a_previous_observation, ::test_17_notional_sizing_rejects_when_below_one_share, ::test_25_contradictory_and_conditions_are_rejected, ::test_51_us_rule_does_not_halt_overnight, ::test_53_frozen_feed_during_a_session_still_halts, ::test_54_no_print_this_session_skips_rather_than_halting, ::test_55_a_truly_dead_feed_still_halts, ::test_67_a_public_holiday_is_recognised_by_name, ::test_71_a_date_beyond_coverage_is_unknown_not_open, ::test_77~test_80(누락 유예). 감사 D-05·D05-01 재현(r4_d05_engine_e2e.py). UTC 경계는 스크래치 registers/work/sweep/chk1.py로 HEAD에서 확인.
- **관련 오류:** D-05, D05-01, D05-02, D05-03, D05-04, D05-05, D05-06, D0405-V01, D0405-V02, D0405-T1, 감사 12.5; 신규(미등재): 일 한도 UTC 날짜 경계
- **화면:** Execution 화면(ui/trading_page.py: 엔진 상태, 결정 로그 사유, 모의주문 목록), Rules 화면(ui/rules_page.py: 검증 메시지)

#### 151. N-02 화면 데모·대체용 합성 데이터(FX 현물, Crypto 데모, KOSPI200 데모 보드와 지수 경로)

- **위치:** core/ficc/data.py:_FX_START:380-382; synthetic_fx:397-413; _degraded:506-507; load_fx_spot:599-613(auto 대체 :613); _business_dates:288-295; ui/crypto_page.py:_synthetic:27-42; _live:45-57(DEXKOUS auto :52); analyze:60-62; ui/derivatives_page.py:synthetic_board:36-49; snapshot 합성 분기:81-92; 합성 배너:225-227; 자체 점검:295; ui/fx_page.py:_rate:66-72; _synthetic_notice:105-110
- **목적:** 공급자가 없거나 사용자가 데모를 고를 때 화면을 채울 가격 경로를 만든다. FX는 auto 경로에서 Yahoo가 실패하면 자동으로 대체된다. Crypto와 Derivatives 데모는 사용자가 고를 때만 쓴다. M1-02(synthetic_history)와 M3-25(합성 금리)에 없는 생성기다.
- **가정:**
  - synthetic_fx: GBM. 연 변동성은 쌍 이름 시드로 7~10%. 드리프트 −½σ²dt(마팅게일). 시작값 _FX_START(USDKRW 1350, EURUSD 1.10 등, 없으면 1.0). 날짜는 오늘까지의 평일.
  - Crypto 데모: 2024-04-01부터 900일 고정. BTC 일간 로그 수익률 N(0.04%, 3%). USD/KRW는 1380에 N(0, 3) 누적. 김치 프리미엄은 AR(1) φ 0.92, 충격 σ 0.4%p. 펀딩 N(0.02%, 0.04%). 거래대금은 균등 난수.
  - Derivatives 데모: F 1126, T 20/365, r 3.2%. 스마일 v(k)=0.17+0.5·max(0, ln(F/k))+0.8·ln(k/F)². Black-76 가격, 호가 폭 0.02·√가격, 거래소 IV 잡음 N(0, 0.1%p). 행사가 F의 85~115%, 2.5pt 간격.
  - Derivatives 데모 지수 경로: 600일 N(0, 1.1%) 로그 랜덤워크를 마지막 값 1126에 맞춘다. 선물가는 1126(1+rT)+0.8로 고정.
- **한계:**
  - 시장 관계를 재현하지 않는다. FX 쌍 사이 상관이 없고 금리와 무관하다.
  - 날짜가 오늘까지라 최신 데이터처럼 보인다(D03-02 계열).
  - Crypto 'live'에서 FRED DEXKOUS가 실패하면 합성 수준형 계열로 김치 프리미엄을 계산한다. +1257%가 녹색 LIVE 칩과 함께 나오고 배너가 없다(D03-01). HEAD에서도 payload에 usdkrw_source가 없다.
  - Crypto 데모는 Days 입력을 무시하고 늘 900일이다.
  - Derivatives 데모 칩은 'expiry DEMO → 오늘 날짜'인데 T는 20일이다(ui/derivatives_page.py:89, :232). 베이시스 +0.8pt가 고정이라 Mispricing 타일이 늘 값을 보인다(신규, P3).
  - FX 화면에서 Yahoo를 명시해도 금리는 auto로 불러 합성으로 떨어질 수 있다(D03-10).
  - Series에 단위 필드가 없다(D03-06).
- **적용 범위:** 오프라인 데모와 화면 점검에만 쓴다. 매크로 실행 경로에서는 pit.py가 합성 값을 거부한다(T-SYN-01). 연구 결론, 카드, 실데이터 대체 수치로 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/ficc_acceptance.py::test_data_synthetic_is_deterministic_and_labeled, ::test_data_synthetic_never_touches_the_cache, ::test_data_auto_degrades_to_synthetic_naming_the_provider; tests/expansion_acceptance.py::selfcheck_crypto_page; ui/derivatives_page.py:295 자체 점검(테스트 목록에는 없음); 감사 docs/audit/2026-10-27/d03_synthetic_fallback.md 4절 S4·S11
- **관련 오류:** D-03, D03-01, D03-02, D03-06, D03-08, D03-10, functional_completeness/MF-01, 감사 12.6; 신규(미등재): Derivatives 데모 만기 칩·고정 베이시스
- **화면:** FX 화면(합성 배너·muted 칩), Crypto 화면(Synthetic 선택 시 배너. live에서 USD/KRW만 합성이면 배너 없음), Derivatives 화면('Synthetic board' 배너)

#### 152. N-03 R-18 구조 변화 프로토콜(선언 이벤트·재고정, CUSUM 통계 플래그, v1.2 스케일 플래그, BOCPD)

- **위치:** core/ficc/context_log.py:BREAK_LOG,RESEARCH_LOG:56-57; BREAK_KINDS,REANCHOR_KINDS:60-61; rv21_series:333-338; BreakEvent:880-907; macro_conditioned_rules:934-950; log_break:953-989; sync_market_structure_breaks:992-1008; reanchor_eligible:1011-1033; log_research:1036-1041; cusum_flags:1044-1060; scale_flag_v12:1063-1073; bocpd_scale_prob:1076-1094; ex1_passes:1097-1105; check_breaks_config:1108-1123; core/engine/books.py:neutralise_rule:742-757; neutralised_rules:760-765; data/macro/rules_v2.0.0.json:breaks:1471-1481
- **목적:** 구조 변화를 다루는 R-18 규칙이다. 공식 정책 체계 변경을 선언하면 매크로 조건부 승수를 1.0으로 되돌리고 포워드 기록을 새로 시작한다. 시장 구조 태그가 바뀌면 이벤트로 남긴다. 통계적 변화 탐지는 연구 로그에만 쓴다.
- **가정:**
  - 행동을 바꾸는 것은 공식 출처가 있는 선언 이벤트뿐이다. 통계 신호는 EX1 검정 통과 전까지 log-only다.
  - CUSUM: 그 시점 이전 확장창 평균·표준편차로 만든 인과 z. k 0.5, h 5, 최소 60관측. 경보 뒤 0으로 초기화.
  - v1.2 스케일 플래그: rv21이 직전 756세션 중앙값의 2배를 60세션 연속 넘으면 플래그.
  - BOCPD: Adams–MacKay. 평균 0 정규 수익률, 분산 Inverse-Gamma(2, 1e-4) 사전, 위험률 1/250. 기록값은 run length<21의 사후 질량.
  - 재고정은 카드 커밋 뒤 효력일인 선언 이벤트, 헤더의 reanchor_window, 강등 없음, R-25 잠금 없음이 모두 있을 때만 허용.
- **한계:**
  - 통계 함수와 log_break·sync는 운영 호출처가 없다. 테스트에서만 돈다(grep, HEAD).
  - EX1 검정(1990-2026 오탐 10년에 1회 이하, 2012·2020 6개월 내 탐지) 기록이 없다. 그래서 통계 경로는 켤 수 없다.
  - 출고 저장소에 macro_conditioned 규칙이 없다(macro_conditioned_rules(None)==()). 정책 변경 선언의 실제 효과도 지금은 없다.
  - BOCPD 사전은 코드 기본값 (2.0, 1e-4)이다. 저장소의 prior 'declared'와 연결되지 않는다. 정상 N(0, 1%) 수익률 400일에서도 기록값이 약 0.067이다.
  - scale_flag_v12의 중앙값 창은 당일을 포함한다. 42관측부터 짧은 창으로 판정하므로 처음 3년은 '3년 중앙값'이 아니다.
  - reanchor_window는 6.5 스키마에 아직 없다(F-21).
- **적용 범위:** 연구 로그와 선언 이벤트 기록에만 쓴다. EX1 통과와 소유자 결정 전에는 노출이나 가중치를 바꾸는 통계 트리거로 쓰면 안 된다. BOCPD는 화면에 보이지 않게 고정되어 있다(displayed false).
- **검증 상태:** 테스트로 확인됨. tests/macro_m6_context.py::test_break_01_framework_change_neutralises_and_starts_a_forward_record, ::test_break_01_research_log_is_write_only_and_the_statistical_leg_is_gated, ::test_break_01_reanchor_only_on_declared_events_and_the_v12_flag_is_logged, ::test_break_01_market_structure_sync_is_complete_and_idempotent (T-BREAK-01). HEAD 실행: macro_conditioned_rules(None)==(), check_breaks_config(None)==[].
- **관련 오류:** -
- **화면:** -

#### 153. N-04 R-19 데이터 계약 검사와 역할별 실패 동작, 연속 실패 HALT 카운터

- **위치:** core/ficc/contracts.py:DEFAULT_HALT_AFTER,BOOK_COUNTER_HALT_AFTER:36-37; check_contract:359-372; is_stale:411-424; on_input_failure:427-460; read_input:463-491(계약 위반 → MissingInput 'missing' :478-479); InputCounters.step:512-536; data/macro/series_registry.yaml:range_groups US_TREASURY,KR_CALL_CD:69-70; NAV_LINE_CLOSES halt 3:77; grace_publication_bdays:81; KOSPI_OFFICIAL_CLOSE abs 0.30:200; KOSPI200_OFFICIAL_CLOSE:205; KRX_069500_OFFICIAL_CLOSE:218-223; SPX_OFFICIAL_CLOSE:468; VIXCLS:491; VXVCLS:509; 호출처 core/skills/macro_daily.py:486, core/quant/risk_layer.py:366, :660
- **목적:** 매크로 입력 값이 계약(유한, 범위, 일간 수익률 상한)을 지키는지 본다. 실패하면 역할별 동작을 정한다. 실행 입력이 연속으로 실패하면 북을 HALT한다.
- **가정:**
  - 범위: 미 국채 [-1, 20]%, 콜·CD [-1, 40]%, VIX·VIX3M [5, 150]. 일간 \|수익률\| 상한 0.30은 KOSPI·KOSPI200·SPX 공식 종가 3개에만 있다.
  - acting_exposure 실패는 바인딩된 북을 fail closed한다. 입력 카운터가 바인딩 한도(기본 2, NAV_LINE_CLOSES 3, KODEX200_PDF 5)에 닿거나 기본 한도 입력의 북 카운터가 2에 닿으면 HALT(OPS).
  - risk_model 공분산 입력은 5회까지 마지막 값을 stale로 이월하고 그 뒤 뺀다. 그 밖 risk_model 실패는 hedge_credit_off 보수적 기본값이다.
  - context 입력은 stale 라벨만 붙인다. forward_sim 입력은 그 북만 fail closed한다.
  - stale은 다음 예정 발표 시각에 발표 영업일 grace(기본 1)를 더한 기한으로 판정한다. 관측 나이로 판정하지 않는다.
- **한계:**
  - read_input은 check_contract에 obs_date·previous_date를 넘기지 않는다. 그래서 단조 관측일 조항은 운영 경로에서 작동하지 않는다(신규).
  - 계약 위반이 MissingInput('missing')으로 바뀐다. 경보와 기록에 '범위 위반' 사유가 남지 않는다(신규).
  - 실행 NAV 라인 KRX_069500_OFFICIAL_CLOSE에는 범위·일간 수익률 계약이 없다. 유한성만 본다(신규). 승인된 카드가 없어 지금 실제 영향은 없다.
  - 임계값은 보정 값이 아니라 등록부 상수다. 0.30은 단위 오류 정도만 잡는다.
- **적용 범위:** 매크로 일일 파이프라인의 PIT 입력 읽기(macro_daily, risk_layer R-06·hedge_state)에 쓴다. 화면용 History·FICC Series에는 적용되지 않는다. 발표 일정 자체(publication.py)는 기존 '발행 시각과 결측 발표(stale) 판정' 항목이다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m1_pit.py::test_role_01_counters_halt_scope_and_role_actions (T-ROLE-01, T-MISS-02), ::test_role_02_registration_refusals_and_contract (T-ROLE-02), ::test_stale_01_schedule_aware_clauses_and_local_smoke (T-STALE-01), ::test_bar_02_dispute_is_not_a_failure_and_vendor_missing (T-BAR-02). 단조 조항 미작동은 스크래치 registers/work/sweep/chk1.py(inspect)로 HEAD에서 확인.
- **관련 오류:** 신규(미등재) 3건: 단조 조항 미작동, 위반 사유 소실, NAV 라인 계약 없음
- **화면:** Macro 화면 Overlay state 패널(입력 상태와 HALT 사유, ui/macro_state_panel.py), 경보 배너(core/skills/alerts.py)

#### 154. N-05 R-15 패밀리 허용(사전 점수)과 1/K 기본 비중, 슬리브 오버레이 적용과 북 조립

- **위치:** core/quant/sleeves.py:FAMILIES,FIXED_ONE:28-29; paper_ls_returns:260-265; overlay_net_returns:268-280; Prior:424-450; PRIORS:452-468; PRIOR_MIN:470; prior_value:473-475; is_admissible:478-484; check_tilts:487-499; check_fixed_family:502-514; base_weights:531-596; apply_overlays:608-707; build_specification_book:724-767; build_recommended_book:789-828; apply_market_gross:831-851; core/quant/optimize.py:inverse_vol_weights(IV_m, M2-27 항목)
- **목적:** 시장 m의 기본 예산 IV_m을 허용된 패밀리 K_m개에 1/K_m씩 나눈다. 허용 조건은 문헌 사전 점수 1 이상이고 카드가 REJECT가 아닌 것이다. 그 위에 패밀리 승수(vs×min(1, overlay))와 시장 gross(vt×min(...), 집중 한도)를 적용해 명세 북과 권고 북을 조립한다.
- **가정:**
  - 사전 점수는 L1722-1732의 고정 표다. 예: KR momentum 12-1 0, 12-7·잔차 1; KR reversal 1(UNVERIFIED); KR flow 3; KR ts_trend KOSPI 1, KOSDAQ 0. 변형을 선언하지 않으면 가장 낮은 값을 쓴다.
  - 패밀리 사이 배분은 균등(1/K)이다. 패밀리 변동성과 상관은 보지 않는다.
  - 권고 북에서 ts_trend는 자기 카드 PASS 전까지 K 자리만 차지하고 예산은 0이다. 남는 예산은 현금이다.
  - 롱온리 슬리브는 벤치마크 쪽으로 줄인다: base×[w_b + a(w_s − w_b)]. 롱숏 슬리브는 0 쪽으로 줄인다: base×a×w_ls. 승수는 부호를 바꾸지 않고 재정규화하지 않는다.
  - reversal·quality·flow 승수는 1.0 고정이다(R-05). vt는 시장 롱 북에만, vs는 패밀리에만 쓴다.
  - 롱숏 오버레이 비용은 \|Δw\|를 두 다리에 부과한다(T-COST-01).
- **한계:**
  - 운영 슬리브 레지스트리가 없다(F-03). macro_daily는 sleeve_vol_scale과 dm_gate만 부른다. base_weights, apply_overlays, build_*_book은 테스트에서만 돈다(grep, HEAD).
  - 사전 점수는 추정치가 아니라 판정 표다. KR reversal은 BL-U02 검증 전까지 UNVERIFIED다.
  - 카드가 모두 NOT_RUN이라 권고 북 승수는 전부 1.0으로 들어간다.
  - IV_m을 못 읽으면 직전 비중을 이월한다. 직전 상태가 없으면 요인 예산이 0이다.
- **적용 범위:** 매크로 명세 북과 권고 북의 비중 조립 규칙이다. 운영 슬리브가 등록되기 전에는 숫자를 만들지 않는다. 패밀리 간 위험 균등화나 최적화로 읽으면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m4_sleeves.py::test_prior_01_admissibility_and_base_weights, ::test_prior_01_reject_reweight_logged_once, ::test_prior_01_mapping_clause_owner, ::test_inverse_vol_weights_kernels_and_pit_path (T-PRIOR-01), ::test_basis_01_vt_never_on_ls_sleeves (T-BASIS-01), ::test_cost_01_both_legs_for_ls_sleeves (T-COST-01), ::test_r05_reversal_quality_flow_fixed_one, ::test_books_recommended_not_run_and_specification_stack, ::test_no_renormalisation_and_sign_preserved
- **관련 오류:** -
- **화면:** -

#### 155. N-06 R-35 권고 북 승인 규칙, 판정 필터, 처분 매핑과 산출물 경계 게이트

- **위치:** core/skills/macro_daily.py:admissions:296-371; compute_admissions:385-399; bounds_ok:821-874; verdict_filter:877-924; brief:1068-1076; core/quant/cards.py:disposition_for:688-706; check_display_invariant:709-717; write_card git_hash 기본값:791; is_de_risk_factor:867-874; maybe_generate_stack_card:877-916; core/ficc/macro_artifacts.py:GIT_HASH:33; provenance:69-73; acts_in_recommended:190-191
- **목적:** 카드 판정이 권고 북에서 작동해도 되는지 정한다. PASS이면서 처분이 RECOMMENDATION·BUILD_AS_INSURANCE이거나 R-31 INVARIANT_STEP일 때만 승인한다. 승인 전에 결과 해시와 판정 체인, 동결 패키지 md5, 스냅숏 재현과 커밋 해시를 확인한다. 실행 산출물의 min() 합성을 다시 계산해 다르면 격리하고 HALT한다.
- **가정:**
  - 처분 매핑: PASS→RECOMMENDATION 또는 BUILD_AS_INSURANCE. R-31은 동결 binding share ≤0.10이면 INVARIANT_STEP. R-28·MACRO-R06-US-FUT→FORWARD_SIM. R-11·R-12→REFUSAL_BOOK. R-31·R-04 등→SPECIFICATION_ONLY. 나머지 DESCRIPTIVE.
  - 표시 불변식: PASS일 때만 recommendation·insurance로 보인다.
  - 무결성 조건 (i)~(iii) 중 하나라도 어긋나면 integrity failure로 명세 북에 남기고 VERDICT_INTEGRITY 페이지 경보를 낸다.
  - R-25 강등 잠금 중인 패밀리×시장은 승인하지 않는다.
  - de-risk 요인이 2개 이상이 되면 stack 카드 헤더(NOT_RUN)를 만든다. 곱 합성은 거부한다(DNB 31).
- **한계:**
  - 오늘은 패키지가 FROZEN이 아니고 카드가 모두 NOT_RUN이라 아무것도 승인되지 않는다(T-CARD-03).
  - 산출물 provenance의 git_hash는 상수 'UNVERSIONED'다(macro_artifacts.py:33, :72). 카드 git_hash는 실행기 --anchor로 들어가고, 없으면 UNVERSIONED라 (iii)이 거부한다. brief()의 'repository under git' 안내는 저장소가 git 아래 있는 지금 낡았다(FC-07, 감사 12.11).
  - R-31 임계값 0.10은 고정 상수다. 근거는 이 함수 밖에 있다.
  - bounds_ok는 기록된 요인으로 min()을 다시 계산할 뿐이다. 요인 값 자체가 맞는지는 보지 않는다.
- **적용 범위:** 매크로 일일 파이프라인의 권고 북 승인 게이트다. Strategy Lab·ETF 화면 카드(docs/asset_expansion/cards)의 판정에는 쓰지 않는다.
- **검증 상태:** 테스트로 확인됨. tests/macro_m7_cards.py::test_card01_displayed_as_iff_pass_and_disposition_table (T-CARD-01); tests/macro_m8_pipeline.py::test_verdict_filter_refuses_unversioned_and_admits_nothing_today (T-CARD-03), ::test_scope_01_g_admission_binds_the_series_to_the_recommended_book_and_its_failure_halts_it (T-SCOPE-01, T-CARD-03), ::test_i06c_acting_field_failure_halts_described_books_display_failure_never (I-06c); tests/macro_m8_integration.py::test_forward_monitor_hook_demotes_locks_out_and_admissions_refuse (I-14, T-CARD-03), ::test_verdict_filter_reads_the_package_state_and_app_start_never_raises (T-CARD-03, T-OBS-02)
- **관련 오류:** functional_completeness/FC-07, 감사 12.11, K-g
- **화면:** Macro 화면 Overlay state 패널과 Model cards 뷰(판정·처분 칩, ui/macro_state_panel.py, ui/macro_cards_view.py)

#### 156. N-07 KOSPI200 만기일 규칙, 근월물 선택, 연속 선물 스플라이스(data/kis_markets.py)

- **위치:** data/kis_markets.py:KISMarkets.kospi200_expiry:337-343; KISMarkets.option_board:345-390(expiry_date :388); KISMarkets.option_chain:392-430(:427); KISMarkets.continuous_futures:291-317(롤 기준 :305, note :317); _top_of_book:673-698; index_futures_contracts:721-740; front_contract:763-772; ui/derivatives_page.py:snapshot:65(대체 코드 'A01612'), :76(T = (expiry_date − 마지막 세션)/365)
- **목적:** KOSPI200 옵션 만기일을 정해 Derivatives 화면의 만기까지 기간 T를 만든다. 근월 선물 코드를 KIS 마스터에서 고른다. 여러 계약을 이어 비율 조정 연속 선물을 만든다(호출처 없음).
- **가정:**
  - 만기일은 해당 월 둘째 목요일이다. 휴장일 조정은 없다.
  - T는 만기일과 마지막 세션 날짜의 달력일 차이를 365로 나눈 값이다. 최소 1일.
  - 근월물은 마스터의 order 1 행이다. 제품 이름은 부분 문자열로 거른다.
  - 연속 선물은 다음 계약 이력의 6번째 행에서 롤하고 비율로 과거를 조정한다.
  - 15:45~18:00 호가는 동시호가 잔량으로 보고 빈 호가로 처리한다.
- **한계:**
  - 둘째 목요일이 휴장일이면 만기일이 틀린다. 출고 KRX 달력(data/calendars/KRX.json)에서 2027-05-13(부처님오신날)이 해당한다. 2025-10-09(한글날)도 같은 경우다. 그 달 T가 길어져 IV, SVI, MFIV, RND, 박스 금리, 헤지 시뮬레이션 기간이 함께 틀린다(신규).
  - continuous_futures는 note의 '만기 5세션 전'과 달리 다음 계약 이력의 6번째 날에 롤한다. 이력이 겹치면 근월물은 5행만 쓰인다(data_flow/MF-02). 호출처는 없다.
  - 대체 코드 'A01612'(2026-12물)가 고정이다. 마스터를 못 받으면 2026-12-10 만기 뒤에 만료 계약을 가리킨다(신규).
  - 부분 문자열 필터 'KOSPI200'은 미니 KOSPI200도 통과시킬 수 있다. 근월물 선택에 미니가 섞이는지는 실제 마스터로 미검증이다.
  - 야간 세션 시간대 호가 필터는 시험되지 않았다(코드 주석).
- **적용 범위:** Derivatives 화면의 KIS 실보드 경로와 asset_expansion_study의 보드·베이시스 카드에 쓴다. 주간 옵션이나 미니 옵션 만기에는 쓰면 안 된다. continuous_futures는 고치기 전에는 쓰면 안 된다.
- **검증 상태:** 테스트로 확인됨. tests/expansion_acceptance.py::selfcheck_kis_markets → data/kis_markets.py:833-834(202610→2026-10-08, 202612→2026-12-10). 휴장 사례는 스크래치 registers/work/sweep/chk1.py(kospi200_expiry('202705')=2027-05-13, KRX.json 휴장일)로, 롤 사례는 chk2.py로 HEAD에서 재현.
- **관련 오류:** data_flow/MF-02, 감사 12.13; 신규(미등재): 만기일 휴장 미조정, 대체 근월물 코드 고정
- **화면:** Derivatives 화면(만기 칩 'expiry → 날짜', T를 쓰는 모든 타일과 차트)

#### 157. N-08 가격 시계열 데이터 점검(validate.data_checks, 미연결)

- **위치:** core/quant/validate.py:data_checks:298-327; 자체 점검:927-930
- **목적:** 가격 시계열이 적합에 쓸 만한지 점검한다. 30세션 미만, 중복 날짜, 0 이하·비유한 값, 수익률 0 비율 20% 초과, \|로그 수익률\|>0.5, 13 달력일 넘는 공백, 마지막 관측이 5일 넘게 오래된 경우를 문제로 돌려준다.
- **가정:**
  - 임계값은 고정 상수다(max_gap_sessions 5 → 2·5+3=13 달력일, stale_days 5).
  - 분할과 오류 체결은 \|ln r\|>0.5로 잡는다고 가정한다.
- **한계:**
  - 운영 호출처가 없다. Strategy Lab, ETF, Signals 어디서도 부르지 않는다(grep, HEAD). 감사 D-01·D-02의 '관측 간격·중복 검사 없음'이 그대로다.
  - 판정 기준은 \|ln r\| > 0.5(가격 −39.3% / +64.9%)다(validate.py:311, :315). 코드 문구 '±50 %'(:318)는 이 값을 가격 변화처럼 적는다. 3:2 분할(가격 −33.3%, 로그 −0.405)과 5:4 분할(가격 −20%, 로그 −0.223)을 놓친다. KRX ±30% 가격제한 아래 정상 일간 변동의 \|ln r\|은 최대 0.357(하한가)이라 0.5를 넘지 않는다.
  - 자체 점검의 첫 단언은 'or True'라 늘 통과한다(:927). 실질 단언은 ±50% 조항 하나다.
  - today 기본값이 date.today()라 결과가 실행일에 달린다.
- **적용 범위:** 지금은 쓰이지 않는 라이브러리 함수다. 연결하려면 감사 12.7(중복·0 이하·급등락 정책) 결정이 먼저다.
- **검증 상태:** 코드로만 확인. core/quant/validate.py:927-930 자체 점검(±50% 조항만 실질 단언), tests/expansion_acceptance.py::selfcheck_validate로 실행
- **관련 오류:** D-01, D-02, 감사 12.7
- **화면:** -
