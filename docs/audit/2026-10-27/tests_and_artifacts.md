# QUANTGEN 감사: 테스트와 감사 자료 (요청서 7절 6항, 8절)

> 작성 메모 (오케스트레이터): 하네스가 조사 에이전트의 보고서 파일 쓰기를 막아, 에이전트가 반환한 보고서 본문(report_md)을 내용 변경 없이 옮겼습니다.


작성일: 2026-10-27. 차원 키: tests_and_artifacts. 감사만 했다. 추적 파일은 `docs/audit/2026-10-27/artifacts/` 아래 데이터 아티팩트만 고쳤다(아래 '아티팩트 검증·수정 내역').

## 1. 범위

- 요청서 7절 6항을 다룬다. 테스트가 실제로 무엇을 보장하는지 본다. 미실행 테스트를 통과로 치지 않는다. 테스트 누락과 데이터 의존을 구분한다.
- 요청서 8절을 다룬다. 인터프리터 버전, pip freeze, 테스트 실행 로그와 종료 코드, 환경 수정 내역, 민감정보를 뺀 설정 예시가 대상이다.
- 대상은 `tests/run_all.py`가 모으는 870행(11개 스위트)이다. 870행 밖의 `__main__` 자체 검사와 기존 아티팩트 8개도 본다.
- 제외 항목:
  - paper_live/, grokteam/는 실행하지 않았다. 정적으로 읽기만 했다.
  - 보호 파일 4개(yf_SPY.csv, yf_BTC-USD.csv, binance_BTCUSDT.csv, upbit_KRW-BTC.csv)는 열지 않았다. 읽기, 해시, stat 모두 하지 않았다.
  - 전체 스위트는 다시 실행하지 않았다. `.env`는 열지 않았다(클라우드에는 파일이 없다).

## 2. 방법

1. 기존 클라우드 실행 2회의 로그와 결과 JSON을 대조했다. 커밋된 소유자 기록 `qa/acceptance_results.json`과도 대조했다.
2. 정적 분석 스크립트(AST와 정규식)를 썼다. 저장소 코드는 import하지 않았다. 다음을 산출했다.
   - 870행 유형 분류
   - NOT_RUN 124행의 원인
   - 데이터가 도착한 뒤의 결과
   - 미연결 자체 검사
   - 모듈 참조
   - 약한 단언 후보
   - 데이터·환경 의존
   
   후보는 모두 코드를 직접 읽어 확인했다.
3. 재현에는 합성 데이터만 썼다. 단일 모듈은 프로세스 안에서 돌리거나, `tests.macro_acceptance.hermetic` 가드를 걸고 subprocess로 돌렸다.
4. 이전 시도의 스크립트는 다시 돌려 결과를 비교했다. 틀린 것만 고쳤다.
5. 기준 실행 시점과 현재 HEAD(4665e6e) 사이에 코드 변경이 없음을 확인했다. 기준 커밋은 716bf77과 b7f991a다. 대상 경로는 core/, data/, ui/, tests/, tools/, grokteam/, paper_live/, config.py, main.py, requirements.txt, pyproject.toml이다. `git diff --stat` 출력이 비어 있다.

## 3. 핵심 결론

- **NOT_RUN은 PASS가 아니다.**
  - `tests/run_all.py:117-118`은 `NotRun`을 별도 상태로 기록한다.
  - `:142`의 종료 코드는 FAIL만 본다(`return 0 if results and failed == 0 else 1`).
  - `tests/notrun.py:4-5`에도 같은 규칙이 적혀 있다.
  - NOT_RUN 앞에서 실행된 단언이 실패하면 FAIL로 드러난다(`:119-121`).
- **실행 결과**
  - 클라우드 2차: 745 PASS / 1 FAIL / 124 NOT_RUN, 종료 코드 1(도출).
  - 클라우드 1차: 738 / 8 / 124, 종료 코드 1(도출).
  - 소유자 기록: 749 / 0 / 121, 종료 코드 0(도출).
- **NOT_RUN 124건의 대부분은 데이터 대기가 아니다. 검증 코드가 아직 없다.**
  - 데이터나 입력이 와도 PASS가 될 수 있는 행은 5건뿐이다.
  - REFDATA로 표시된 104건 중 PASS가 될 수 있는 행은 0건이다.
  - 83건은 NOT_RUN으로 남는다. 35건은 의도된 FAIL 경보로 바뀐다(TA-01).
- **매크로 골든 1,203행 중 실데이터로 재현할 수 있는 행은 2행이다.**
  - 그 2행은 G-DSR-01이다. Bailey–López de Prado 공개 예제를 쓴다.
  - 1,184행은 MANIFEST에 없는 실데이터 파일이 있어야 한다.
- **PASS 745행은 대부분 합성·인라인 단위 테스트와 소스 정적 스캔이다.**
  - 실시장 데이터로 계산한 결과를 독립 기준과 비교하는 테스트는 없다.
  - FICC 57건은 항등식, 왕복, 패리티 검사다(TA-07).
- **870행 밖에 자체 검사가 있다.**
  - 20개 모듈의 `__main__` 자체 검사다. assert는 345개다.
  - 요청서의 "FICC·매크로 자체 검사 ok"도 여기에 속한다.
  - 클라우드에서 20개 모두 PASS를 다시 확인했다(TA-02).

## 4. (a) 870행 스위트가 실제로 보장하는 것

### 4-1. 스위트 × 유형 (클라우드 2차 실행, 수정된 test_classification.csv)

| 스위트 | 행 | PASS | FAIL | NOT_RUN | 합성 단위 | 인라인 단위 | 소수 기대값 | 정적 스캔 | 통합 | NOT_RUN |
|---|---|---|---|---|---|---|---|---|---|---|
| safety | 10 | 10 | 0 | 0 | 0 | 2 | 0 | 8 | 0 | 0 |
| engine | 92 | 92 | 0 | 0 | 8 | 82 | 0 | 1 | 1 | 0 |
| ui | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| quant | 53 | 53 | 0 | 0 | 23 | 29 | 0 | 0 | 1 | 0 |
| ficc | 57 | 57 | 0 | 0 | 8 | 45 | 3 | 0 | 1 | 0 |
| expansion | 20 | 20 | 0 | 0 | 12 | 4 | 2 | 1 | 1 | 0 |
| macro | 542 | 421 | 0 | 121 | 133 | 156 | 32 | 52 | 48 | 121 |
| paper | 21 | 21 | 0 | 0 | 14 | 6 | 0 | 0 | 1 | 0 |
| grokteam | 17 | 17 | 0 | 0 | 6 | 8 | 2 | 1 | 0 | 0 |
| guard | 5 | 5 | 0 | 0 | 1 | 3 | 0 | 0 | 1 | 0 |
| papers | 49 | 45 | 1 | 3 | 15 | 17 | 0 | 3 | 11 | 3 |
| 합계 | 870 | 745 | 1 | 124 | 220 | 352 | 39 | 70 | 65 | 124 |

유형 정의(휴리스틱, `classify_tests.py`):
- 합성 단위: 시드 난수, 합성 이력, 가짜 객체를 쓴다.
- 인라인 단위: 손으로 만든 입력을 쓰고 난수는 없다.
- 소수 기대값: 소수 3자리 이상 상수와 비교한다. 대부분 사양 전사값이거나 내부 허용오차다. 외부 기준값이 아니다.
- 정적 스캔: 소스 텍스트나 AST를 검사한다.
- 통합: 임시 디렉터리, CLI, git, 로컬 캐시, 여러 모듈 경로를 쓴다.

한계: 정규식 분류다. 무작위 표본 16건 중 1건이 잘못 분류되어 있었다. `quant/test_interval_coverage_on_simulated_t_garch`는 시뮬레이션 테스트인데 인라인 단위로 분류됐다. safety 7건도 오분류였고, 이번에 고쳤다.

스위트별로 보장하는 것:
- safety 10: 8건은 소스 문자열 스캔이다. 주문 경로 문자열 부재, 계좌 변수 부재, UTF-8, 뷰 캐시를 본다. 계산 정확성과는 무관하다.
- engine 92: 가짜 시세와 가짜 공급자로 규칙 엔진 상태기계를 검사한다.
- ui 4: `ui/*.py`의 Flet API 이름, 키워드, 팔레트 토큰이 존재하는지 정적으로만 확인한다. 화면 동작 검사는 아니다.
- quant 53: 합성 이력에서 MC, GARCH, 최적화, 백테스트 불변식을 본다.
  - 독립성이 있는 검사가 몇 건 있다. numpy 재계산 대조(`tests/quant_acceptance.py:369-378`), 시뮬레이션 모수 회복, 구간 포함률 검사다.
- ficc 57: 부트스트랩 왕복, 패리티, 수치 미분 대조, 오프라인 합성 강등을 본다. 외부 기준값은 없다(TA-07).
- expansion 20: 가짜 KIS·암호화폐 전송, 게이트 검정, 연결된 자체 검사 11개다.
- macro 542(421 PASS): 합성 패널과 임시 디렉터리로 v2 파이프라인 장치, 스키마, 거부 경로, 격리 스캔을 본다. 실데이터 골든 재현은 없다.
- paper 21, grokteam 17: 오프라인 합성 검사다. 감사 규칙상 실행이 금지된 영역이라 정적 분류만 했다.
- guard 5: git 태그와 해시 고정을 본다. 클라우드 PASS는 로컬 대체 태그 기준이므로 증거가 아니다(6-3절).
- papers 49: 논문 파이프라인이다. 클라우드에서는 tectonic 관련 3건이 NOT_RUN이고 taskkill 관련 1건이 FAIL이다.

수집 누락은 없다. 모든 스위트 파일의 `test_*` 함수가 870행에 들어 있다. 정적 대조로 확인했다.

### 4-2. NOT_RUN 124행의 원인 (`not_run_by_cause.csv`, 재생성 결과와 바이트 단위로 같음)

| 요청 분류 | 하위 원인 | 행 | 데이터 후 NOT_RUN 유지 | 데이터 후 FAIL | PASS 가능 | 불명 |
|---|---|---|---|---|---|---|
| 소유자 데이터 부재 (REFDATA 104) | R1 KOSPI 공식종가·Yahoo ^KS11 | 58 | 40 | 18 | 0 | 0 |
| | R2 French Data Library | 21 | 10 | 11 | 0 | 0 |
| | R3 FRED/ALFRED·기타 스냅샷 | 9 | 8 | 1 | 0 | 0 |
| | R4 연구 산출표(QX_*)·원장 | 12 | 8 | 4 | 0 | 0 |
| | R5 KRX 전종목 marcap 패널 | 3 | 3 | 0 | 0 | 0 |
| | R6 BTC 일중 캔들 | 1 | 0 | 1 | 0 | 0 |
| 소유자 서명·결정·입력 (OWNER) | O1 | 13 | 11 | 0 | 1 | 1 |
| 키·라이브 세션 (KIS) | O2 | 3 | 2 | 0 | 1 | 0 |
| 외부 도구 (tectonic) | O3 | 3 | 0 | 0 | 3 | 0 |
| 게이트 동결 대기 (PENDING) | P1 | 1 | 1 | 0 | 0 | 0 |
| Windows 전용 | 없음 | 0 | | | | |
| 합계 | | 124 | 83 | 35 | 5 | 1 |

- Windows 전용 원인의 NOT_RUN은 0건이다. Windows 전용 동작(taskkill)은 NOT_RUN이 아니라 FAIL 1건으로 나타난다(TA-10).
- 원인은 '첫 일치 규칙' 하나만 붙였다. 여러 자료가 필요한 행도 있다. 예를 들어 `test_gate_01`은 KOSPI, French, FRED, QX 자료가 모두 필요하다. `test_task_m5_15`는 KRX 시간봉이 필요한데 R3으로 분류되어 있다.
- 클라우드와 소유자 기록의 차이는 papers의 tectonic 3건뿐이다(소유자 PASS, 클라우드 NOT_RUN).

### 4-3. 데이터가 도착하면 무엇이 되는가 (`not_run_implementation_status.csv` v2)

| 형태 | 행 | 데이터 도착 후 | 예 (file:line) |
|---|---|---|---|
| 무조건 stub | 42 | NOT_RUN 유지 | `tests/macro_m5_books.py:682-686` (`_lad`가 곧바로 `raise NotRun`) |
| 자료 확인 후 NotRun | 23 | 21건 유지. `test_cost01`은 실데이터로 G-KR-02를 단언한 뒤 NotRun(`tests/macro_m2_costed.py:120-129`). `test_g_kr_06_cap15`는 PENDING 골든이라 유지(`:381-387`, goldens.csv:239-240, `tests/golden_tools.py:119-126`) | `tests/macro_m2_risk.py:394-397` |
| 인라인 smoke 후 NotRun | 19 | 18건 유지. 1건 불명(`tests/macro_m7_cardp.py:351-355`, ECOS 코드가 생기면 `MissingInput` 단언이 실패할 것으로 추정) | `tests/macro_m8_forward.py:580-1039` |
| FAIL 경보(tripwire) | 35 | FAIL | `tests/macro_m2_risk.py:723-725` "golden replay ... is not implemented", `tests/macro_m7_integration.py:395-405` `assert absent`, `tests/macro_m1_calendars.py:382-384` "unreachable" |
| 조건부 | 5 | PASS 가능. KIS 기록 1(`tests/macro_m1_fixtures.py:483-492`), tectonic 3. 매핑 확정 1(`tests/macro_m4_sleeves.py:380-382`)은 확정 후 추가 단언이 없다 | |

- NOT_RUN 행 중 27건은 지금도 합성·인라인 검사 104개를 실행한다. 이 검사가 실패하면 FAIL로 드러난다. 즉 NOT_RUN 뒤에 숨지 않는다.
- `tests/macro_registry.csv`의 사양 ID 275개 중 91개가 문제다. 89개는 golden 등급, 2개는 freeze 등급이다. 이 91개는 `implemented_in`이 가리키는 테스트가 모두 위 자리표시자다. 61개는 자리표시자와 실행 가능한 테스트가 섞여 있다. 123개는 실행 가능한 테스트가 있다.

### 4-4. 골든 값 재현 현황

- `tests/fixtures/macro/goldens.csv`는 1,203행이다.
  - 1,184행은 MANIFEST에 없는 실데이터가 필요하다. 상태별로 golden 1,124, reference 50, pending 6, pre_patch_pending 4행이다.
  - 17행은 자료 열이 비어 있다. P94 pending 행이다.
  - 2행만 등록된 자료(F30 `bldp_dsr_example.json`)로 재현된다. 이 2행은 `tests/macro_m1_fixtures.py:265-282`에서 공개 예제 값과 4자리까지 맞는다.
- `tests/fixtures/macro/MANIFEST.csv`는 9행이다. 사양 전사, 합성, 원장 골격만 있고 실시장 데이터는 0건이다.
- 골든 값을 쓰는 PASS 테스트는 두 종류다.
  - 전사된 값끼리의 산술 일관성을 본다. 예: `tests/macro_m1_fixtures.py:321-331`.
  - 골든 도구 자체를 본다. 예: `:167-174`는 G-DSR-02 값을 그대로 넣어 자기 자신과 비교한다.
  - 둘 다 모델이 데이터에서 그 수치를 다시 만들어 내는지는 보지 않는다.

### 4-5. 데이터·환경에 의존하는 PASS

| 의존 | 테스트 (file:line) | 비고 |
|---|---|---|
| 로컬 벤더 캐시 | `macro_m1_pit/test_stale_01_...` (`tests/macro_m1_pit.py:612-625`, fred_DEXKOUS.csv) | 파일이 없으면 NOT_RUN |
| 로컬 벤더 캐시 + 파일 mtime | `macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache` (`tests/macro_m8_pipeline.py:846-875`) | TA-04. 캐시 목록은 `core/skills/macro_daily.py:86-90`에 있고 yf_SPY.csv를 포함한다 |
| 로컬 벤더 캐시(내용 고정) | `macro_m9_lab/test_smoke_grading_...` (`tests/macro_m9_lab.py:639-659`) | `:658`이 마지막 날짜 2026-09-22를 고정한다. 캐시를 갱신하면 FAIL한다 |
| 로컬 벤더 캐시(BTC·ETH) | `macro_tf_gov/test_cry1_study_runs_offline_...` (`tests/macro_tf_gov.py:578-600`) | `docs/techfund_study.py:72-75`가 binance_BTCUSDT, upbit_KRW-BTC, binance_ETHUSDT를 읽는다 |
| 벤더 캐시 smoke(NOT_RUN 행) | `tests/macro_m3_estimators.py:540-551` (yf_SPY.csv), `tests/macro_m5_fills_events.py:389-465` (yf__VIX, yf__VIX3M) | smoke 단언이 오늘 실행된다 |
| git 태그 | `guard/test_a`, `test_b`, `test_d` (`tests/frozen_guard.py:66-91`) | 클라우드에서는 대체 태그 기준이다 |
| 외부 실행 파일 | tectonic 3건(NOT_RUN), taskkill 1건(FAIL) | TA-10 |
| 자격증명 유무 | `safety/test_21` (`tests/acceptance.py:143-149`), `quant/test_gsq_pricing...` (`tests/quant_acceptance.py:542-545`) | TA-05, TA-08 |
| 벽시계 | `guard/test_c` (`tests/frozen_guard.py:80-82`) | 2027-02-01까지 유효 |

보호 파일 4개 중 최소 3개를 전체 스위트가 읽는다. binance_BTCUSDT.csv와 upbit_KRW-BTC.csv는 위 CRY-1 테스트가 읽는다. yf_SPY.csv는 dry-run 테스트와 `macro_m3` smoke가 읽는다. 감사자는 이 테스트들을 실행하지 않았다.

### 4-6. 테스트가 없는 기능

| 기능 | 위치 | 상태 |
|---|---|---|
| 가격 이력 정제(NaN, ±inf, 중복 날짜) | `core/quant/history.py:97-101` `_clean_rows` | 테스트 없음. 재현하면 inf와 중복 날짜가 남는다(`repro_clean_rows_untested.py`). D-01/D-02 차원과 겹친다 |
| 캐시 적중 시 값 검증, 손상 캐시 | `core/quant/history.py:427-443` | 손상 파일이나 비유한 값이 든 캐시를 다루는 테스트가 없다. quant/ficc/expansion에서 grep 결과 0건 |
| Portfolio 화면(다자산 순차 로딩, P-01) | `ui/portfolio_page.py` (216줄) | Flet API 정적 스캔만 있다 |
| Rules, KRX, xcharts, AI 패널 | `ui/rules_page.py` (596줄), `ui/krx_page.py`, `ui/xcharts.py`, `ui/ai_panel.py` | 정적 스캔만 있다 |
| 숫자 포맷 | `core/numfmt.py` (114줄) | 없음 |
| Settings 화면 | `ui/settings_page.py` | 소스 문자열 스캔만 있다(`tests/acceptance.py:78-89`) |
| Rates, FX, Bonds, Structuring, Derivatives, ETF, Macro, Quant Lab 화면, fcharts | `ui/*_page.py`, `ui/fcharts.py` | 870행 밖의 자체 검사만 있다(TA-02) |
| 성능 | — | 벽시계 상한 2건뿐이다: `tests/macro_m8_pipeline.py:850` (<120 s), `tests/macro_tf_gov.py:590` (<180 s) |
| 공급자 간 교차 검증(V-01) | — | 없음 |

모듈 기준으로 다시 셌다(`import_coverage_v2.py`). 이전 목록의 오탐 3건을 뺐다. `core/rules/validation.py`와 `data/krx/gateway.py`는 패키지 재노출로 테스트된다. `core/crypto/__init__.py`는 1줄 파일이다. core/, data/, ui/ 125개 모듈 중 12개는 어떤 테스트도 참조하지 않는다.

### 4-7. 공허하거나 약한 테스트

| 테스트 | 위치 | 문제 |
|---|---|---|
| `quant/test_mc_jump_degrades_to_gbm_without_outliers` | `tests/quant_acceptance.py:348-354` | 이름은 "GBM으로 강등"이다. 실제 단언은 메모가 비어 있지 않은지만 본다. 주석에 "어느 쪽이든"이라고 적혀 있다 |
| `quant/test_gsq_status_is_coherent` | `tests/quant_acceptance.py:534-539` | `assert st.installed in (True, False)`는 항상 참이다 |
| `quant/test_gsq_pricing_without_session_explains_itself` | `tests/quant_acceptance.py:542-545` | `ok`이면 단언이 0개다 |
| `safety/test_21_krx_gateway_degrades_with_a_reason` | `tests/acceptance.py:147-149` | 키가 있으면 단언이 0개다(TA-05) |
| `macro_ui_components/test_readme_carries_both_disclaimers_and_no_stale_counts` | `tests/macro_ui_components.py:137-146` | 옛 문자열 4개만 금지한다. README.md:878의 "743/864", :877의 papers "43 PASS"는 이미 낡았는데 잡지 못한다. 실제는 870행이고 papers는 49건이다 |
| Flet 가드 중복 실행 | `tests/macro_ui_components.py:129-134`, `tests/macro_ui_overlay.py:374-377`, `tests/macro_ui_views.py:337-340` | 같은 ui 검사 4개를 3번 더 돈다. PASS 3행이 커버리지 없이 늘어난다 |
| 잠재적 조기 반환 | `tests/macro_m5_integration.py:334-335, 342-343` | 백업 zip이 없으면 diff 조항을 건너뛰고 PASS한다. 지금은 zip이 추적되어 있어 발동하지 않는다 |

## 5. 발견사항

| ID | 심각도 | 판정 | 요약 |
|---|---|---|---|
| TA-01 | P1 | 사실 | NOT_RUN의 대부분은 데이터 대기가 아니라 검증 코드 미작성이다. 실데이터 골든 재현은 2/1,203행이다 |
| TA-02 | P2 | 사실 | 20개 모듈의 자체 검사(assert 345개)가 870행 밖에 있다 |
| TA-03 | P2 | 사실 | statsmodels가 미선언이다. ADF가 조용히 NaN이 되고 판정 문구가 틀린다 |
| TA-04 | P2 | 사실 | dry-run 테스트가 파일 mtime에 의존해 새 체크아웃에서 FAIL한다 |
| TA-05 | P2 | 사실 | safety/test_21은 키가 있으면 실제 KIS를 호출하고 단언을 건너뛴다. README의 '전 스위트 밀폐' 주장과 다르다 |
| TA-06 | P2 | 사실 | 핵심 기능(이력 정제, Portfolio 화면, 손상 캐시, 성능)에 테스트가 없다 |
| TA-07 | P2 | 사실 | 금융 계산 테스트가 내부 항등식 위주다. 외부 기준값과 비교하는 테스트는 사실상 1건이다 |
| TA-08 | P3 | 사실 | 공허·약한 테스트, 중복 실행, 낡은 README 수치를 잡지 못하는 테스트가 있다 |
| TA-09 | P3 | 사실 | 패키지 하나가 없으면 papers 49건이 NOT_RUN 1행으로 접히고 종료 코드는 0이다. pypdf도 미선언이다 |
| TA-10 | P3 | 사실 | Windows 전용 taskkill 때문에 Linux에서 FAIL하고 프로세스 트리가 남는다 |
| TA-11 | P3 | 사실 | flet이 없으면 run_all은 테스트 0건, 결과 파일 없이 중단한다. yfinance와 pandas-datareader는 원인이 아니다 |
| TA-12 | P3 | 사실 | PASS 테스트가 로컬 벤더 캐시 내용에 묶여 있다. 보호 파일 3개를 읽는다 |

### TA-01 (P1, 사실) NOT_RUN의 대부분은 데이터 대기가 아니라 검증 코드 미작성

- **파일·함수·라인:**
  - `tests/macro_m2_risk.py:723-725` `_golden_refdata`
  - `tests/macro_m7_integration.py:395-405` `_refdata`
  - `tests/macro_m1_calendars.py:382-384, 712-714`
  - `tests/macro_m3_estimators.py:531-605`
  - `tests/macro_m4_sleeves.py:218-220, 670-708`
  - `tests/macro_m2_costed.py:393-406`
  - `tests/macro_m5_books.py:682-698`
  - `tests/fixtures/macro/MANIFEST.csv` (9행), `tests/fixtures/macro/goldens.csv` (1,203행)
  - `tests/macro_registry.csv` `implemented_in`
- **재현 단계:**
  1. `python3 -B -I /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/notrun_after_data.py /home/user/quantgen /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/baseline2_results.json /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/notrun_after_data.csv`
  2. `python3 -B -I /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/registry_placeholders.py /home/user/quantgen /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/notrun_after_data.csv`
  3. goldens.csv의 fixtures 열을 MANIFEST의 등록 파일과 대조한다.
- **기대 결과:** `REFDATA` NOT_RUN은 "데이터만 있으면 검증되는 테스트"여야 한다. 자료가 등록되면 실데이터로 단언하고 PASS 또는 FAIL이 되어야 한다.
- **실제 결과:**
  - 124건 중 83건은 데이터가 와도 NOT_RUN이다(stub 42, 자료 확인 후 NotRun 23, smoke 후 NotRun 18).
  - 35건은 "not implemented" 또는 `assert absent` 때문에 FAIL로 바뀐다.
  - 1건은 불명이다. PASS 가능은 5건이다.
  - REFDATA 104건 중 PASS 가능은 0건이다.
  - 골든 1,184행은 재현 테스트가 없다.
  - 사양 ID 91개는 `implemented_in`이 자리표시자만 가리킨다.
- **영향:**
  - "121 not run"은 데이터를 넣으면 끝나는 일처럼 읽힌다. 실제로는 리플레이 코드를 써야 한다.
  - README "What the study decided"의 수치를 QUANTGEN 코드가 다시 만들어 내는지 어떤 테스트도 확인하지 않는다.
  - README는 "nothing formally run"이라고 밝히고 있다(README.md:348-363). 하지만 테스트 상태 보고가 준비도를 과대 표시한다.
- **수정안:** 미작성 단언을 `STUB:` 사유로 따로 세고, 요약 줄에 원인별 수를 낸다.
```diff
--- a/tests/notrun.py
+++ b/tests/notrun.py
@@ -35,0 +36,7 @@ def require_owner(what: str) -> NotRun:
+
+def not_written(what: str) -> NotRun:
+    """The input may be present; the assertion on it is not written yet. Counted apart from REFDATA / OWNER so a
+    NOT_RUN row never reads as 'waiting for data' when it is waiting for code."""
+    return NotRun(f"STUB: {what}")
+
--- a/tests/run_all.py
+++ b/tests/run_all.py
@@ -138,5 +138,11 @@ def main(argv=None) -> int:
     passed = sum(r["status"] == "PASS" for r in results)
     failed = sum(r["status"] == "FAIL" for r in results)
     not_run = sum(r["status"] == "NOT_RUN" for r in results)
-    print(f"\n{passed}/{len(results)} passed, {failed} failed, {not_run} not run; {OUT}")
+    causes: dict[str, int] = {}
+    for r in results:
+        if r["status"] == "NOT_RUN":
+            k = r.get("reason", "").split(":", 1)[0]
+            causes[k] = causes.get(k, 0) + 1
+    split = ", ".join(f"{k} {v}" for k, v in sorted(causes.items()))
+    print(f"\n{passed}/{len(results)} passed, {failed} failed, {not_run} not run ({split}); {OUT}")
     return 0 if results and failed == 0 else 1
--- a/tests/macro_m5_books.py
+++ b/tests/macro_m5_books.py
@@ def _lad(gid: str):
-    raise NotRun(f"REFDATA: {gid}: QX_DLA_ladder.csv (F24), F13 / U1 and the literal v1.2 rule text "
+    raise not_written(f"{gid}: needs QX_DLA_ladder.csv (F24), F13 / U1 and the literal v1.2 rule text "
```
  - stub 42건과 '자료 확인 후 NotRun' 23건의 마지막 `raise NotRun("REFDATA: ...")`를 같은 방식으로 `not_written(...)`으로 바꾼다. 목록은 not_run_implementation_status.csv에 있다.
  - 자료 확인 후 NotRun인 행은 오늘은 계속 REFDATA로 보인다. 자료가 등록되면 STUB로 바뀐다.
  - 우선순위는 G-KR-01..04, G-US-01 리플레이다. 계산 코드 `core/quant/costed.py`는 이미 있다.
- **회귀 테스트:** `tests/macro_m0_harness.py::test_every_not_run_placeholder_says_stub`
  - tests/macro_*.py를 AST로 스캔한다.
  - 마지막 문장이 무조건 `raise NotRun("REFDATA|OWNER ...")`인 테스트를 찾는다. 자료 확인 뒤에 실데이터 단언이 없는 테스트도 찾는다.
  - 단언: `assert offenders == []`. 해당 테스트는 `not_written` 또는 "STUB:" 사유를 써야 한다.
  - run_all 요약 줄에 `STUB n`이 나오는지도 단언한다.

### TA-02 (P2, 사실) 20개 모듈의 자체 검사(assert 345개)가 870행 밖에 있다

- **파일·함수·라인:** 다음 모듈의 `__main__` 블록이다.
  - `core/ficc/bonds.py:335`, `curves.py:403`, `data.py:702`, `fx.py:450`, `insights.py:594`, `macro.py:276`, `ratesim.py:390`, `structured.py:442`, `swaps.py:426`
  - `core/quant/garch.py:719`, `gjr.py:206`
  - `ui/bonds_page.py:247`, `derivatives_page.py:295`, `etf_page.py:263`, `fcharts.py:404`, `fx_page.py:414`, `macro_page.py:244`, `quant_lab_page.py:405`, `rates_page.py:486`, `structuring_page.py:309`
  - 연결 목록은 `tests/expansion_acceptance.py:323-345`이고 11개만 들어 있다. `_selfcheck`는 `:28-33`이다.
- **재현 단계:**
  1. `python3 -B -I /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/selfcheck_ast_scan.py /home/user/quantgen`
  2. `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/run_unwired_selfchecks_v2.py /home/user/quantgen /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/selfcheck_ast_scan.txt /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/unwired_selfchecks_v2.csv`
- **기대 결과:** 스스로 단언하는 자체 검사는 회귀 스위트에서 돌아야 한다.
- **실제 결과:** 31개 모듈에 assert가 든 `__main__` 블록이 있다. 11개만 연결되어 있다. 20개(assert 345개)는 run_all이 돌리지 않는다. hermetic 가드 아래에서 20개 모두 PASS했다.
- **영향:**
  - 요청서의 "FICC·매크로 오프라인 자체 검사 ok"는 사실이다. 하지만 그 검사는 870행 결과에 들어 있지 않다.
  - FICC 핵심(채권, 곡선, 스왑, FX, 구조화)과 8개 화면이 회귀하면 자동으로 드러나지 않는다.
- **수정안:**
```diff
--- a/tests/expansion_acceptance.py
+++ b/tests/expansion_acceptance.py
@@ -28,7 +28,9 @@
 def _selfcheck(rel: str):
     """Run a module's __main__ block as a test (it asserts on its own invariants)."""
     def run():
-        runpy.run_path(str(ROOT / rel), run_name="__main__")
+        from tests.macro_acceptance import hermetic
+        with hermetic():                                  # a self-check never reaches a provider or the disk cache
+            runpy.run_path(str(ROOT / rel), run_name="__main__")
     run.__name__ = f"selfcheck_{rel.replace('/', '_').replace('.py', '')}"
     return run
@@ -343,4 +345,10 @@ def tests():
         ("selfcheck_crypto_analytics", _selfcheck("core/crypto/analytics.py")),
         ("selfcheck_crypto_page", _selfcheck("ui/crypto_page.py")),
-    ]
+    ] + [(f"selfcheck_{rel.replace('/', '_')[:-3]}", _selfcheck(rel)) for rel in (
+        "core/ficc/bonds.py", "core/ficc/curves.py", "core/ficc/data.py", "core/ficc/fx.py", "core/ficc/insights.py",
+        "core/ficc/macro.py", "core/ficc/ratesim.py", "core/ficc/structured.py", "core/ficc/swaps.py",
+        "core/quant/garch.py", "core/quant/gjr.py", "ui/bonds_page.py", "ui/derivatives_page.py", "ui/etf_page.py",
+        "ui/fcharts.py", "ui/fx_page.py", "ui/macro_page.py", "ui/quant_lab_page.py", "ui/rates_page.py",
+        "ui/structuring_page.py")]
```
  - 실행 시간이 약 70초 늘어난다.
  - 기존 11개를 hermetic 아래로 옮겨도 결과가 같은지는 적용 전에 전체 실행으로 확인해야 한다.
- **회귀 테스트:** `tests/expansion_acceptance.py::test_every_asserting_selfcheck_is_wired`
  - core/, data/, ui/에서 모듈 수준 `if __name__ == "__main__":` 블록 중 `assert`가 있는 파일의 집합을 구한다.
  - 단언: 그 집합이 `_selfcheck` 경로 집합과 같다.

### TA-03 (P2, 사실) statsmodels 미선언으로 ADF가 조용히 NaN이 되고 판정 문구가 틀린다

- **파일·함수·라인:**
  - `core/quant/strategies.py:266-271` `adf_pvalue`: `except Exception: return nan`
  - `core/crypto/analytics.py:170-175` `eth_btc_test`
  - `ui/crypto_page.py:117`
  - `ui/etf_page.py:77`
  - `core/ficc/curve_models.py:176, 213`
  - `requirements.txt`, `pyproject.toml:10-17`: 둘 다 statsmodels가 없다.
- **재현 단계:**
  1. `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/repro_statsmodels_nan.py /home/user/quantgen --block` (statsmodels import 차단)
  2. 같은 명령을 `--block` 없이 실행한다.
- **기대 결과:**
  - 강한 평균회귀 AR(1)(φ=0.9) 합성 계열에서는 단위근 기각이 나와야 한다.
  - 계산할 수 없을 때는 "계산 불가"라고 표시해야 한다.
- **실제 결과:**
  - 차단하면 `adf_pvalue = nan`이고 판정은 `'no rejection of a unit root (the expected null)'`이다.
  - 설치되어 있으면 p=3.1e-13이고 판정은 `'mean-reverting at 5 %'`이다.
  - 클라우드 1차 실행에서는 연결된 자체 검사 3개만 이를 잡았다(FAIL).
- **영향:**
  - `pip install -r requirements.txt`만 한 새 설치에서 Crypto와 ETF 화면이 잘못된 결론 문구를 보인다. "ADF p nan"도 함께 표시된다.
  - 소유자 기록(expansion 20 PASS)으로 보아 소유자 PC에는 statsmodels가 설치되어 있는 것으로 추정한다.
- **수정안:**
```diff
--- a/requirements.txt
+++ b/requirements.txt
@@
 scipy>=1.11
+statsmodels>=0.14
 matplotlib>=3.8
--- a/pyproject.toml
+++ b/pyproject.toml
@@
-  "numpy>=1.26", "pandas>=2.1", "scipy>=1.11", "matplotlib>=3.8", "gs-quant>=1.0",
+  "numpy>=1.26", "pandas>=2.1", "scipy>=1.11", "statsmodels>=0.14", "matplotlib>=3.8", "gs-quant>=1.0",
--- a/core/crypto/analytics.py
+++ b/core/crypto/analytics.py
@@ -170,6 +170,9 @@ def eth_btc_test(eth: dict[str, float], btc: dict[str, float]) -> dict:
     dates, (e, b) = _align(eth, btc)
     x = np.log(e / b)
-    return {"n": len(dates), "last_ratio": float(e[-1] / b[-1]), "adf_p": adf_pvalue(x),
+    p = adf_pvalue(x)
+    verdict = ("ADF unavailable (statsmodels missing or the test failed)" if not math.isfinite(p)
+               else "mean-reverting at 5 %" if p < 0.05 else "no rejection of a unit root (the expected null)")
+    return {"n": len(dates), "last_ratio": float(e[-1] / b[-1]), "adf_p": p,
             "half_life_days": half_life(x), "z_2y": float((x[-1] - x[-730:].mean()) / x[-730:].std(ddof=1)) if x.size > 100 else float("nan"),
-            "verdict": ("mean-reverting at 5 %" if adf_pvalue(x) < 0.05 else "no rejection of a unit root (the expected null)")}
+            "verdict": verdict}
```
  - `adf_pvalue`의 `except Exception`은 `ImportError`만 NaN으로 바꾸도록 좁힌다. 다른 예외는 그대로 올린다.
- **회귀 테스트:**
  1. `tests/expansion_acceptance.py::test_eth_btc_verdict_is_unavailable_when_adf_is_nan`: `adf_pvalue`를 NaN 반환으로 바꾼다. 단언: `"unavailable" in res["verdict"]`.
  2. `tests/acceptance.py::test_every_third_party_import_is_declared`: core/, data/, ui/, tools/의 서드파티 최상위 import를 AST로 모아 requirements.txt와 대조한다. 단언: 빈 차집합. 현재는 statsmodels와 pypdf가 걸린다.

### TA-04 (P2, 사실) dry-run 테스트가 파일 mtime에 의존해 새 체크아웃에서 FAIL한다

- **파일·함수·라인:**
  - `core/skills/macro_daily.py:1412`: `retrieved_at_utc = st_mtime`
  - `tests/macro_m8_pipeline.py:846-875`: `:849`에서 시계를 2026-10-07T09:00Z로 고정한다. `:871`이 vt를 단언한다.
- **재현 단계:** `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/repro_dryrun_mtime.py /home/user/quantgen /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/dryrun_scratch2`
  - 스크래치에 합성 `yf_SPY.csv`를 만들어 쓴다. 저장소 캐시는 쓰지 않는다.
- **기대 결과:** 같은 내용의 캐시라면 파일을 복사하거나 체크아웃한 시각과 무관하게 같은 결과가 나와야 한다.
- **실제 결과:**
  - mtime이 현재 시각이면 `vt_status = fail_closed`이고 `vt_weight_next = 0.0`이다. 테스트 단언은 False가 된다.
  - mtime이 2026-10-01이면 `ok`와 1.0이 나오고 단언은 True다.
  - 클라우드 1차 실행에서 FAIL했고, mtime을 앞당긴 2차 실행에서 PASS했다.
- **영향:**
  - 2026-10-07 이후에 clone하거나 unzip한 모든 환경에서 이 테스트가 FAIL한다.
  - 운영 코드도 복사 시각을 수집 시각으로 기록한다. D-04/D-05의 시각 출처 문제와 같은 뿌리다.
- **수정안:**
  - 테스트는 mtime을 고정한 사본을 쓴다.
  - 근본 수정은 수집 시각을 사이드카 매니페스트에 기록하는 것이다(D-04/D-05 차원).
```diff
--- a/tests/macro_m8_pipeline.py
+++ b/tests/macro_m8_pipeline.py
@@ -12,6 +12,8 @@
 import ast
 import json
+import os
+import shutil
 import tempfile
@@ -846,7 +848,12 @@
 def test_dry_run_end_to_end_on_the_local_cache():
     tmp = _tmp()
+    cache = tmp / "cache"                       # a copy with pinned mtimes: a checkout's mtime is no retrieval time
+    shutil.copytree(MD.CACHE_DIR, cache)
+    stamp = U(2026, 10, 1).timestamp()
+    for p in cache.iterdir():
+        os.utime(p, (stamp, stamp))
     t0 = time.perf_counter()
-    out = MD.dry_run(tmp, clock=lambda: U(2026, 10, 7, 9, 0))
+    out = MD.dry_run(tmp, clock=lambda: U(2026, 10, 7, 9, 0), cache_dir=cache)
```
- **회귀 테스트:** `tests/macro_m8_pipeline.py::test_dry_run_verdict_does_not_depend_on_the_checkout_time`
  - 합성 캐시 사본 두 개를 만든다. 하나는 mtime이 현재이고, 하나는 2026-10-01이다.
  - 단언: 두 사본의 `us["vol"]["vt_status"]`가 같다. 근본 수정 후에는 `retrieved_at_utc`가 매니페스트 값과 같다.

### TA-05 (P2, 사실: 코드 경로. 실제 KIS 호출은 미재현) safety/test_21이 키가 있으면 밀폐되지 않는다

- **파일·함수·라인:**
  - `tests/acceptance.py:143-149` `test_21_krx_gateway_degrades_with_a_reason`
  - `data/krx/gateway.py:88-94`: `self.kis.ready`이면 `self.kis.daily(...)`를 호출한다.
  - `data/krx/kis_client.py:143`
  - README.md:903-906: "The whole suite is hermetic"
  - 대조: hermetic 래핑은 macro 스위트에만 있다(`tests/macro_acceptance.py:229-234`).
- **재현 단계:**
  1. 코드를 읽는다. safety 스위트에는 hermetic 래핑도, 자격증명 패치도 없다.
  2. `.env`에 KIS 키가 있으면 `KRXGateway()`가 `ready=True`가 된다.
  3. 제안한 본문은 스크래치에서 확인했다: `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_proposed_test21.py /home/user/quantgen` → PASS.
- **기대 결과:** 테스트는 네트워크와 자격증명 없이 같은 단언을 항상 실행해야 한다.
- **실제 결과:**
  - 키가 있는 소유자 PC에서는 테스트 중에 실제 KIS 일봉 요청이 나간다.
  - 응답이 `ok`이면 `if not answer.ok:` 때문에 단언이 0개다.
  - 키가 없는 클라우드에서만 단언이 실행된다.
- **영향:**
  - 테스트가 쿼터와 레이트리밋을 쓴다. 결과가 네트워크 상태에 따라 달라진다.
  - README의 밀폐 주장이 safety 스위트에서는 사실이 아니다.
- **수정안:**
```diff
--- a/tests/acceptance.py
+++ b/tests/acceptance.py
@@ -143,7 +143,15 @@
 def test_21_krx_gateway_degrades_with_a_reason():
     """No provider configured must yield an actionable reason, never a blank."""
-    from data.krx import KRXGateway
-    gateway = KRXGateway()
-    for answer in (gateway.daily("005930"), gateway.filings("005930")):
-        if not answer.ok:
-            assert answer.reason.strip(), "a failed answer must explain itself"
+    import config
+    from data.krx import KRXGateway
+    from tests.macro_acceptance import hermetic
+    saved = (config.kis_ready, config.opendart_ready, config.krx_ready)
+    config.kis_ready = config.opendart_ready = config.krx_ready = lambda: False   # the owner's .env never reaches KIS
+    try:
+        with hermetic():
+            gateway = KRXGateway()
+            for answer in (gateway.daily("005930"), gateway.filings("005930")):
+                assert not answer.ok and answer.reason.strip(), "a failed answer must explain itself"
+    finally:
+        config.kis_ready, config.opendart_ready, config.krx_ready = saved
```
  - README.md:903의 문장을 "the macro group is hermetic; the other suites patch their own providers"처럼 사실대로 고친다.
- **회귀 테스트:** `tests/acceptance.py::test_21_...` 개정본
  - `socket.socket.connect`를 감시한다. 가짜 키 환경변수를 넣고 실행한다.
  - 단언: 연결 시도 0회, 단언 2회 실행(`not answer.ok`, 사유 비어 있지 않음).

### TA-06 (P2, 사실) 핵심 기능에 테스트가 없다

- **파일·함수·라인:**
  - `core/quant/history.py:97-101` `_clean_rows`
  - `core/quant/history.py:427-443`: 캐시 적중 경로
  - `ui/portfolio_page.py`, `ui/rules_page.py`, `ui/krx_page.py`, `ui/xcharts.py`, `ui/ai_panel.py`, `core/numfmt.py`
  - 성능 테스트: `tests/macro_m8_pipeline.py:850`, `tests/macro_tf_gov.py:590`만 있다.
- **재현 단계:**
  1. `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/repro_clean_rows_untested.py /home/user/quantgen`
  2. `python3 -B -I /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/import_coverage_v2.py /home/user/quantgen`
  3. `grep -rn "_clean_rows" tests` 결과는 0건이다.
- **기대 결과:** 데이터 정제, 캐시, 다자산 로딩 경로에 단위 테스트가 있어야 한다.
- **실제 결과:**
  - `_clean_rows`는 `+inf`와 중복 날짜를 그대로 둔다. closes=(100.0, 100.5, 101.0, inf). 이를 막는 테스트가 없다.
  - 모듈 12개는 어떤 테스트도 참조하지 않는다. ui 11개는 Flet 정적 스캔만 받는다.
  - 손상 캐시나 비유한 값 캐시를 다루는 테스트가 없다.
- **영향:** D-01, D-02, C-01, P-01 지적 사항이 회귀해도 스위트는 PASS한다.
- **수정안:**
  - 아래 테스트를 추가한다. 정제 로직 자체의 수정은 D-01/D-02 차원 소관이다.
  - Portfolio 화면에는 가짜 `load_history`로 종목 수 1, 5, 20일 때 호출 수와 순서를 고정하는 테스트를 둔다.
```diff
--- a/tests/quant_acceptance.py
+++ b/tests/quant_acceptance.py
@@
+def test_history_cleaning_drops_non_finite_and_resolves_duplicate_dates():
+    from core.quant.history import _clean_rows
+    d, c = _clean_rows([("2024-01-02", 100.0), ("2024-01-02", 100.5), ("2024-01-03", math.inf),
+                        ("2024-01-04", float("nan")), ("2024-01-05", 101.0)])
+    assert all(math.isfinite(x) and x > 0 for x in c)
+    assert len(d) == len(set(d)) and list(d) == sorted(d)
```
- **회귀 테스트:**
  - 위 `test_history_cleaning_drops_non_finite_and_resolves_duplicate_dates`. 현재 코드에서는 FAIL하는 것이 정상이다. D-01/D-02 수정 후 PASS해야 한다.
  - `test_history_cache_hit_with_non_finite_closes_is_refetched`: 캐시 JSON에 Infinity를 넣는다. 단언: 공급자 재호출 1회, 결과 전부 유한.

### TA-07 (P2, 사실) 금융 계산 테스트가 내부 항등식 위주다

- **파일·함수·라인:**
  - `tests/ficc_acceptance.py` 57건. 예: `:393-400` GK 패리티, `:403-407` 내재변동성 왕복, `:429-437` SABR 자기 재현.
  - 외부 기준이 있는 예외: `tests/macro_m1_fixtures.py:265-282` (BLdP 공개 예제), `tests/quant_acceptance.py:369-378` (numpy 대조).
- **재현 단계:**
  1. `grep -nE "[0-9]\.[0-9]{3,}" tests/ficc_acceptance.py`: 기대값 리터럴이 없다. 입력값만 나온다.
  2. 제안 테스트를 스크래치에서 실행한다: `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_independent_gk.py /home/user/quantgen`
- **기대 결과:** 핵심 가격 공식마다 독립 구현이나 문헌 예제 값과 비교하는 테스트가 최소 1건씩 있어야 한다.
- **실제 결과:**
  - FICC 테스트는 패리티, 왕복, 단조성, 수치 미분 대조다.
  - 같은 관례 오류(예: 일수 계산, 복리 방식)가 양쪽에 같이 들어가면 모두 PASS한다.
  - 제안한 독립 GK 공식 대조는 현재 구현과 차이 0.0이다. 결함이 아니라 보증 범위의 공백이다.
- **영향:** "57 PASS"가 금융적 정확성을 인증하지 않는다. 요청서 7절 4항의 독립 비교 요구와 맞지 않는다.
- **수정안:**
  - 공식별로 독립 기준 테스트를 추가한다. 출처를 docstring에 적는다.
  - 대상: GK, Black-76, Bachelier, 채권 가격·듀레이션 닫힌 식, 스왑 par rate, CIR/Vasicek 채권가.
```diff
--- a/tests/ficc_acceptance.py
+++ b/tests/ficc_acceptance.py
@@
+def test_gk_matches_an_independent_closed_form():
+    """Garman-Kohlhagen with continuous rd, rf written here, not imported from core."""
+    from scipy.stats import norm
+    d1 = (math.log(_S / _K) + (_RD - _RF + 0.5 * _V ** 2) * _T) / (_V * math.sqrt(_T))
+    d2 = d1 - _V * math.sqrt(_T)
+    call = _S * math.exp(-_RF * _T) * norm.cdf(d1) - _K * math.exp(-_RD * _T) * norm.cdf(d2)
+    assert abs(fx.garman_kohlhagen(_S, _K, _T, _RD, _RF, _V, True).price - call) < 1e-12
```
- **회귀 테스트:** 위 테스트(지금 PASS). 같은 형식으로 Black-76, Bachelier, 채권 닫힌 식, par swap rate 테스트를 추가한다. 단언은 모두 `abs(core - independent) < 1e-10`이다.

### TA-08 (P3, 사실) 공허·약한 테스트와 중복 실행

- **파일·함수·라인:** 4-7절 표 전체. 주요 항목:
  - `tests/quant_acceptance.py:348-354, 534-539, 542-545`
  - `tests/macro_ui_components.py:129-134, 137-146`
  - `tests/macro_ui_overlay.py:374-377`, `tests/macro_ui_views.py:337-340`
  - `tests/macro_m5_integration.py:334-343`
  - README.md:877-878
- **재현 단계:**
  1. `python3 -B -I /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/weak_assert_scan.py /home/user/quantgen /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/baseline2_results.json`
  2. 강화안을 확인한다: `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_jump_degrade.py /home/user/quantgen`. 균등분포 잡음 계열이면 강등 분기를 탄다(`degrades` 포함).
- **기대 결과:** 테스트 이름이 약속한 성질을 단언해야 한다. 같은 검사가 여러 행으로 세어지면 안 된다.
- **실제 결과:**
  - 메모가 비어 있지 않은지만 보거나, 항상 참인 단언이 있다.
  - 조건이 맞을 때 단언이 0개인 테스트가 있다.
  - Flet 가드 4개가 4번 돈다.
  - README 수치 테스트가 현재의 낡은 수치를 잡지 못한다.
- **영향:** PASS 수가 실제 보증보다 크다. 결함이 생겨도 드러나지 않는다.
- **수정안:**
  - jump 테스트는 위 균등 잡음 계열로 바꾸고 `assert "degrades" in mc.jump_note`를 단언한다.
  - `assert st.installed in (True, False)` 줄을 지운다.
  - gsq 가격 테스트는 hermetic과 무자격증명 상태에서 `assert not out["ok"] and out["detail"]`를 단언한다.
  - macro_ui 3개 래퍼는 `assert len(names) == 4`만 남기고 재실행을 지운다.
  - README 테스트는 README 표의 스위트별 수와 각 스위트 `tests()` 길이를 비교한다.
  - backup zip이 없을 때는 `raise NotRun("OWNER: pre-v2 backup absent; diff clause not run")`로 바꾼다.
- **회귀 테스트:**
  - `test_mc_jump_degrades_to_gbm_without_outliers`(개정): 단언 `"degrades" in mc.jump_note`.
  - `test_readme_suite_counts_match_the_collected_tests`: 단언 README.md 합계 행의 분모 == 870 == `len(run_all.tests())`.

### TA-09 (P3, 사실) papers 스위트가 NOT_RUN 1행으로 접히고 종료 코드는 0이다

- **파일·함수·라인:**
  - `tests/run_all.py:57-71` `papers_tests`
  - `tools/paper/selfcheck.py:21` (`import yaml`), `:119` (`from pypdf import PdfReader`)
  - requirements.txt에 pypdf가 없다.
- **재현 단계:** `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/repro_papers_collapse.py /home/user/quantgen`
  - yaml import를 차단하고, run_all 함수를 AST로 추출해 실행한다.
- **기대 결과:** 선언된 의존성이 빠진 환경 결함은 FAIL이어야 한다. 아니면 49행이 각각 보여야 한다.
- **실제 결과:**
  - `rows: 1 statuses: ['NOT_RUN']`, 종료 코드 0이다.
  - 사유는 "OWNER:"로 표시된다. 환경 결함인데 소유자 입력으로 분류된다.
- **영향:** 49개 검사가 사라져도 요약은 "0 failed"다.
- **수정안:**
```diff
--- a/tests/run_all.py
+++ b/tests/run_all.py
@@ -60,12 +60,10 @@ def papers_tests():
     try:
         from tools.paper.selfcheck import tests as selfcheck_tests
     except Exception as exc:
-        missing = isinstance(exc, ModuleNotFoundError) and exc.name in ("yaml", "pypdf", "requests")
-        reason = f"tools.paper.selfcheck does not import ({type(exc).__name__}: {exc})"
+        reason = f"tools.paper.selfcheck does not import ({type(exc).__name__}: {exc}); its 49 checks did not run"
 
         def import_failed():
-            if missing:
-                raise NotRun(f"OWNER: {reason}")
             raise RuntimeError(reason)
         return [("import", import_failed)]
--- a/requirements.txt
+++ b/requirements.txt
@@
 pyyaml>=6.0
+pypdf>=4.0
```
- **회귀 테스트:** `tests/acceptance.py::test_a_missing_dependency_is_a_fail_not_a_not_run`. yaml을 차단하고 `papers_tests()`를 실행한다. 단언: 상태 FAIL, 종료 코드 1.

### TA-10 (P3, 사실) Windows 전용 taskkill 때문에 Linux에서 FAIL하고 프로세스 트리가 남는다

- **파일·함수·라인:** `tools/debate.py:64-78` (`:75` taskkill), `tools/paper/selfcheck.py:1253-1266`
- **재현 단계:**
  1. 클라우드 2차 실행 로그 `docs/audit/2026-10-27/artifacts/run_all_cloud_run2.log`의 traceback을 본다: `FileNotFoundError: 'taskkill'`.
  2. 수정안을 스크래치에서 확인했다: `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_posix_tree_kill.py`. 3.0초 안에 트리가 종료된다.
- **기대 결과:** 시간 초과 시 모든 OS에서 프로세스 트리를 끝내야 한다. 아니면 비Windows에서는 NOT_RUN으로 표시해야 한다.
- **실제 결과:** Linux에서는 `TimeoutExpired` 대신 `FileNotFoundError`가 난다. 손자 프로세스(120초 sleep)는 남는다.
- **영향:** 소유자 PC(Windows)에서는 영향이 없다. 다른 OS에서는 referee 실행이 멈추거나 프로세스가 남는다.
- **수정안:**
```diff
--- a/tools/debate.py
+++ b/tools/debate.py
@@ -70,9 +70,13 @@ def _run(argv, *, input=None, cwd=None, timeout=None):
     with subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
-                          text=True, encoding="utf-8", errors="replace") as proc:
+                          text=True, encoding="utf-8", errors="replace", start_new_session=(os.name != "nt")) as proc:
         try:
             out, err = proc.communicate(input, timeout=timeout)
         except subprocess.TimeoutExpired:
-            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
+            if os.name == "nt":
+                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
+            else:
+                os.killpg(proc.pid, signal.SIGKILL)
             out, err = proc.communicate()
```
  - 파일 상단에 `import signal`을 추가한다.
- **회귀 테스트:** 기존 `papers/test_debate_run_kills_process_tree`가 Linux에서도 PASS해야 한다. 단언: 경과 시간 < 60 s.

### TA-11 (P3, 사실) flet이 없으면 run_all이 테스트 0건, 결과 파일 없이 중단한다

- **파일·함수·라인:**
  - `tests/run_all.py:41-51`: 모듈 수준에서 모든 스위트를 import한다. `:43`이 `tests/flet_api_guard.py:24` `import flet as ft`로 이어진다.
  - `core/ficc/data.py:48-55`: yfinance와 pandas-datareader는 선택적으로 import한다.
- **재현 단계:** 다음을 패키지별로 실행한다.
  - `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/repro_missing_providers.py /home/user/quantgen flet`
  - 같은 명령에 `yfinance`
  - 같은 명령에 `pandas_datareader`
- **기대 결과:** 한 스위트의 import 실패는 FAIL 1행이어야 한다. 나머지 스위트는 돌아야 한다(macro 스위트는 이미 그렇게 한다, `tests/macro_acceptance.py:222-228`).
- **실제 결과:**
  - flet을 차단하면 `tests.flet_api_guard` import가 실패하고 run_all은 거기서 죽는다.
  - yfinance나 pandas-datareader를 차단하면 모든 스위트 import가 정상이다(`_yf is None` / `_pdr is None`).
- **영향:** 요청서 3절 "세 패키지 미설치로 조기 중단"은 flet 부분만 사실이다. 소유자 PC에는 영향이 없다.
- **수정안:**
```diff
--- a/tests/run_all.py
+++ b/tests/run_all.py
@@ -41,10 +41,20 @@
-from tests.acceptance import tests as safety_tests         # noqa: E402
-from tests.engine_acceptance import tests as engine_tests  # noqa: E402
-from tests.flet_api_guard import tests as ui_tests          # noqa: E402
-from tests.quant_acceptance import tests as quant_tests     # noqa: E402
-from tests.ficc_acceptance import tests as ficc_tests       # noqa: E402
-from tests.expansion_acceptance import tests as expansion_tests   # noqa: E402
-from tests.macro_acceptance import tests as macro_tests     # noqa: E402
-from tests.paper_live_acceptance import tests as paper_tests     # noqa: E402
-from grokteam.selfcheck import tests as grokteam_tests             # noqa: E402
-from tests.frozen_guard import tests as guard_tests         # noqa: E402
+import importlib                                            # noqa: E402
+SUITES = (("safety", "tests.acceptance"), ("engine", "tests.engine_acceptance"), ("ui", "tests.flet_api_guard"),
+          ("quant", "tests.quant_acceptance"), ("ficc", "tests.ficc_acceptance"), ("expansion", "tests.expansion_acceptance"),
+          ("macro", "tests.macro_acceptance"), ("paper", "tests.paper_live_acceptance"), ("grokteam", "grokteam.selfcheck"),
+          ("guard", "tests.frozen_guard"))
+
+
+def _suite(module: str):
+    """`module.tests()`; an import failure is one FAIL row and every other suite still runs."""
+    try:
+        return importlib.import_module(module).tests()
+    except Exception as exc:
+        reason = f"{module} does not import ({type(exc).__name__}: {exc})"
+
+        def import_failed():
+            raise RuntimeError(reason)
+        return [("import", import_failed)]
@@ def tests():
-    return ([(f"safety/{n}", f) for n, f in safety_tests()] +
-            ... (10 lines) ...
-            [(f"guard/{n}", f) for n, f in guard_tests()] +
+    return ([(f"{s}/{n}", f) for s, mod in SUITES for n, f in _suite(mod)] +
             [(f"papers/{n}", f) for n, f in papers_tests()])
```
- **회귀 테스트:** `tests/acceptance.py::test_one_broken_suite_is_one_fail_row`. flet을 차단하고 `run_all.tests()`를 호출한다. 단언: `ui/import` 1행이 있고, 다른 스위트 행 수는 그대로다.

### TA-12 (P3, 사실) PASS 테스트가 로컬 벤더 캐시 내용에 묶여 있다

- **파일·함수·라인:**
  - `tests/macro_m9_lab.py:658`: `dates[-1] == "2026-09-22"`
  - `tests/macro_tf_gov.py:578-600`
  - `docs/techfund_study.py:72-75`
  - `tests/macro_m8_pipeline.py:846-875`
  - `core/skills/macro_daily.py:86-90`
  - `tests/macro_m3_estimators.py:544-545`
- **재현 단계:** 코드를 읽는다. 감사자는 보호 파일을 읽는 테스트를 실행하지 않았다.
- **기대 결과:** 캐시 갱신과 무관하게 같은 판정이 나와야 한다. 고정 자료는 MANIFEST에 md5로 등록한 사본이어야 한다.
- **실제 결과:**
  - 캐시를 갱신하면 smoke grading 테스트가 FAIL한다.
  - 스위트가 보호 파일 3개(binance_BTCUSDT.csv, upbit_KRW-BTC.csv, yf_SPY.csv)를 읽는다.
- **영향:**
  - 캐시 갱신과 테스트 PASS가 충돌한다.
  - 다른 프로젝트가 '미열람'으로 둔 기간 자료가 전체 스위트 실행과 그 출력에 쓰인다.
- **수정안:**
  - 고정이 필요한 자료는 `tests/fixtures/`에 사본을 두고 MANIFEST에 md5를 등록한 뒤 `require_fixture`로 읽는다.
  - 마지막 날짜는 상수 대신 파일에서 구해 "마지막 행 제거"만 단언한다.
  - 보호 파일을 읽는 테스트에는 `--skip-pilot-windows` 같은 실행 옵션을 둔다(소유자 결정 사항).
- **회귀 테스트:** `tests/macro_m9_lab.py::test_smoke_grading_is_independent_of_the_cache_end`. 합성 캐시 두 벌(끝 날짜가 다름)로 실행한다. 단언: 두 경우 모두 `dates[-1] == source_last_date_minus_one_row`.

## 6. (b) 8절 감사 자료

### 6-1. 클라우드 아티팩트 (`docs/audit/2026-10-27/artifacts/`)

| 8절 항목 | 아티팩트 | 상태 |
|---|---|---|
| python --version | `python_version.txt` | 확인. Python 3.13.17, pip 24.0, `/usr/bin/python`. PREREG 고정값(3.13.14, numpy 2.3.5, pandas 2.3.3, scipy 1.18.0)은 태그 파일과 일치한다 |
| pip freeze | `audit-installed-packages.txt` | 확인. 다시 뽑은 freeze와 같다. `@`, `://`, `file:`, token, secret, password 일치 0건. gs-quant는 설치되지 않았다 |
| pip check | `pip_check.txt` | 확인. curl-cffi와 certifi 버전 충돌 1건이다 |
| 설치 전체 로그 | 없음 | 클라우드 pip.log에는 경고 1줄과 "exit 0"만 있다. 명령과 전문은 남아 있지 않다(미검증). `environment_fixes_cloud.txt`에 기록했다 |
| 테스트 실행 로그와 종료 코드 | `run_all_cloud_run1.log`, `run_all_cloud_run2.log`, `run_all_cloud_summary.txt` (신규) | 로그는 기존 실행의 원본 사본이다. 종료 코드는 로그에 없어서 코드(`tests/run_all.py:142`)로 도출했다 |
| 환경 수정 | `environment_fixes_cloud.txt` (신규) | 4건(아래 6-3) |
| 민감정보를 뺀 설정 예시 | `config.example.sanitized.env` | 확인. 본문은 `.env.example`과 같다. 추가 13개 변수의 config.py 라인 인용이 정확하다. `.env`는 열지 않았다 |
| 성능 계측 | 없음 | 소유자 PC에서 만들어야 한다. 명령은 P-01 차원 보고서(`docs/audit/2026-10-27/p01_performance.md:420-431`)에 있다 |

### 6-2. 전체 스위트 실행 요약 (재실행 안 함)

| 실행 | 시각(UTC) | 결과 | 종료 코드(도출) | 실행 시간 |
|---|---|---|---|---|
| 클라우드 1차 | 2026-10-26 13:41-13:51 | 738 PASS / 8 FAIL / 124 NOT_RUN | 1 | 9m55s |
| 클라우드 2차 | 2026-10-26 20:25-20:34 | 745 / 1 / 124 | 1 | 8m56s |
| 소유자 기록 (`qa/acceptance_results.json`, ac86705) | — | 749 / 0 / 121 | 0 | — |

- 1차 FAIL 8건:
  - expansion 자체 검사 3건(statsmodels)
  - `macro_m8_pipeline/test_dry_run...`(mtime)
  - guard 3건(태그 없음)
  - `papers/test_debate_run_kills_process_tree`(taskkill)
- 2차 FAIL은 taskkill 1건이다.
- 실행 방법: `tests/run_all.py`를 import하고 `R.OUT`을 스크래치로 돌린 래퍼(`run_baseline.py`)로 `sys.exit(R.main())`를 실행했다. `qa/acceptance_results.json`은 바뀌지 않았다. md5 16c9baa5…가 실행 전후로 같다.

### 6-3. 클라우드 환경 수정 (`environment_fixes_cloud.txt`)

1. 2026-10-26 13:35 UTC: flet 0.85.2, yfinance 1.7.0, pandas-datareader 0.11.1 등을 설치했다. 근거는 패키지 디렉터리 mtime이다. gs-quant는 설치되지 않았다.
2. 13:56 UTC: statsmodels 0.15.0을 설치했다. 1차와 2차 실행 사이다. 이 패키지는 미선언이다(TA-03).
3. 캐시 mtime을 2026-10-01로 앞당겼다. 보호 파일 4개를 뺀 42개를 stat으로 확인했다.
4. 18:56 UTC: 로컬 대체 annotated 태그 `studies-of-record-2026-10-23`를 eacd57d에 만들었다. 푸시하지 않았다.
   - guard PASS 3건은 이 대체 태그를 기준으로 한다. 소유자 PC의 실제 태그에 대해서는 아무것도 증명하지 않는다.

### 6-4. 소유자 Windows PC에서 만들어야 하는 자료와 명령

클라우드에서는 만들 수 없는 자료다.
- Windows 인터프리터와 패키지 목록
- 설치 전체 로그
- 실제 태그와 tectonic, taskkill이 있는 환경의 전체 실행 로그와 종료 코드
- 성능 계측

저장소 루트에서 PowerShell로 실행한다. `.env` 내용과 키는 공유하지 않는다.

```powershell
$A = "docs\audit\2026-10-27\artifacts\owner"
New-Item -ItemType Directory -Force $A | Out-Null

# 1) 인터프리터
python --version 2>&1 | Out-File -Encoding utf8 "$A\python_version.txt"
python -c "import sys,platform; print(sys.version); print(platform.platform()); print(sys.executable)" | Out-File -Append -Encoding utf8 "$A\python_version.txt"
python -m pip --version | Out-File -Append -Encoding utf8 "$A\python_version.txt"

# 2) 설치 패키지(평소 인터프리터) - 공유 전에 민감 패턴을 검사한다
python -m pip freeze | Out-File -Encoding utf8 "$A\audit-installed-packages.txt"
python -m pip check 2>&1 | Out-File -Encoding utf8 "$A\pip_check.txt"
Select-String -Path "$A\audit-installed-packages.txt" -Pattern '@|://|token|secret|password'   # 결과가 있으면 그 줄을 지운다

# 3) 설치 전체 로그: 버리는 venv에서 (전역 numpy/scipy/pandas 고정값을 건드리지 않는다)
python -m venv "$env:TEMP\qg_audit_venv"
& "$env:TEMP\qg_audit_venv\Scripts\python.exe" -m pip install -r requirements.txt 2>&1 | Out-File -Encoding utf8 "$A\install_log.txt"
"exit $LASTEXITCODE" | Out-File -Append -Encoding utf8 "$A\install_log.txt"

# 4) 전체 스위트(평소 인터프리터). run_all은 qa\acceptance_results.json을 덮어쓴다
python tests\run_all.py 2>&1 | Out-File -Encoding utf8 "$A\run_all_owner.log"
"exit $LASTEXITCODE" | Out-File -Append -Encoding utf8 "$A\run_all_owner.log"
Copy-Item qa\acceptance_results.json "$A\acceptance_results_owner.json"
git diff --stat -- qa\acceptance_results.json | Out-File -Encoding utf8 "$A\acceptance_results_diff.txt"

# 5) 실제 태그(guard 근거)
git cat-file -t studies-of-record-2026-10-23 | Out-File -Encoding utf8 "$A\tag_check.txt"
git rev-parse "studies-of-record-2026-10-23^{commit}" | Out-File -Append -Encoding utf8 "$A\tag_check.txt"

# 6) 870행 밖 자체 검사 20개(TA-02), hermetic 가드 아래
$mods = "core/ficc/bonds.py","core/ficc/curves.py","core/ficc/data.py","core/ficc/fx.py","core/ficc/insights.py","core/ficc/macro.py","core/ficc/ratesim.py","core/ficc/structured.py","core/ficc/swaps.py","core/quant/garch.py","core/quant/gjr.py","ui/bonds_page.py","ui/derivatives_page.py","ui/etf_page.py","ui/fcharts.py","ui/fx_page.py","ui/macro_page.py","ui/quant_lab_page.py","ui/rates_page.py","ui/structuring_page.py"
foreach ($m in $mods) {
  python -B -c "import runpy,sys; p=sys.argv[1]; sys.argv=[p]; sys.path.insert(0,'.'); from tests.macro_acceptance import hermetic`nwith hermetic(): runpy.run_path(p, run_name='__main__')" $m 2>&1 | Out-File -Append -Encoding utf8 "$A\selfchecks_owner.txt"
  "$m exit $LASTEXITCODE" | Out-File -Append -Encoding utf8 "$A\selfchecks_owner.txt"
}

# 7) 성능 계측: docs\audit\2026-10-27\p01_performance.md 의 소유자 명령(약 420-431행)을 따른다
```

- 4)는 시간이 걸린다(클라우드 기준 약 9분).
- 소유자 PC에는 실제 캐시 mtime과 실제 태그가 있다. 따라서 TA-04와 guard 결과는 클라우드와 다를 수 있다.
- 보호 파일을 읽는 테스트(TA-12)가 포함된다는 점에 유의한다.

## 7. 요청서 3절 주장 검증 (이 차원 관련)

| 주장 | 판정 | 근거 |
|---|---|---|
| 322개 Python 파일 컴파일, 문법 오류 0 | 사실 | 메모리 내 `compile()`로 322/322 확인. git 추적 .py도 322개다. 실행 정상성과는 별개다 |
| FICC·매크로 오프라인 자체 검사 ok | 사실 (단, 870행 밖) | `core/ficc/data.py:702`, `core/ficc/macro.py:276` 블록이 hermetic 아래에서 "ok"를 출력한다. run_all에는 연결되어 있지 않다(TA-02). 합성·가짜 입력 기반이다 |
| 기존 기록 870건 중 PASS 749, NOT_RUN 121 | 사실 | `qa/acceptance_results.json`(커밋 ac86705, HEAD와 같다). 소유자 PC 기록이다. 이번에 870건을 다시 실행하지는 않았다 |
| flet, yfinance, pandas-datareader 미설치로 조기 중단 | flet은 사실, 나머지 둘은 오류 | flet만 중단 원인이다(TA-11). 나머지 둘은 선택적 import다(`core/ficc/data.py:48-55`) |

## 8. 아티팩트 검증·수정 내역

| 아티팩트 | 검증 | 조치 |
|---|---|---|
| `python_version.txt` | 현재 출력과 같다. PREREG 고정값을 태그 파일에서 확인했다 | 없음 |
| `audit-installed-packages.txt` | 다시 뽑은 freeze, 이전 원본과 같다. 민감 패턴 없음 | 없음 |
| `pip_check.txt` | 다시 실행한 결과와 같다 | 없음 |
| `config.example.sanitized.env` | `.env.example` 본문과 같다. config.py 라인 인용이 정확하다 | 없음 |
| `not_run_by_cause.csv` | 재생성 결과와 바이트 단위로 같다. 첫 일치 규칙이라 다중 원인 행이 있다(4-2절) | 없음 |
| `test_classification.csv` | 휴리스틱 분류다. safety 7행이 오분류였다 | **수정.** safety 08, 09, 13, 14, 15, 16, 17의 primary_type을 unit_other에서 static_scan으로 바꿨다. 13과 14의 labels는 `static_scan;unit_other`다. 나머지 863행은 그대로다 |
| `not_run_implementation_status.csv` | 오류가 있었다. zero-assert 21행이 `smoke_then_notrun`으로 표시되어 있었다. `test_g_kr_06_cap15_reference_refdata`는 "yes"였지만 골든이 pre_patch_pending이라 NOT_RUN으로 남는다. `test_cost01`의 실데이터 단언이 누락되어 있었다. tripwire가 `conditional`로 섞여 있었다 | **교체(v2).** 열은 `test, where, kind, checks_now, after_data, note`다. kind는 stub 42 / 자료 확인 후 NotRun 23 / smoke 19 / tripwire 35 / 조건부 5다 |
| `unwired_selfchecks.csv` | 오류가 있었다. `core/ficc/context_log.py`는 `__main__` 블록이 없다. `:127` docstring 안의 문자열을 잡은 오탐이었다. 그래서 '21개'가 아니라 20개다 | **교체.** AST 스캔 기반 20행에 `exit_code` 열을 추가했다. 20개 모두 PASS다 |
| (신규) `run_all_cloud_summary.txt`, `run_all_cloud_run1.log`, `run_all_cloud_run2.log`, `environment_fixes_cloud.txt` | 8절 항목 4와 환경 수정 내역 | 추가. 로그는 원본 사본이다. 비밀 패턴 검사에서 일치 0건이었다 |

수정 전 사본: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/artifact_backup/`

## 9. 미검증 항목

- 소유자 Windows PC에서의 실제 실행 결과. 749/870은 커밋된 기록만 확인했다.
- 클라우드 설치 전체 로그와 정확한 설치 명령. 남아 있지 않다. gs-quant가 설치되지 않은 이유도 모른다.
- safety/test_21의 실제 KIS 호출. 키가 없어 코드 경로로만 확인했다.
- quant, ficc, engine, expansion 스위트가 키가 있는 환경에서 네트워크에 닿는지. 클라우드 프록시가 막아서 구분할 수 없었다.
- `test_excess_01_bok_call_rate_ecos_code_is_owner_input`이 ECOS 코드 입력 후 FAIL로 바뀌는지(추정).
- `test_classification.csv` 유형 라벨의 전수 정확도. 표본 16건 중 1건이 오분류였다.
- paper, grokteam 스위트의 내용. 실행 금지 영역이라 정적 분류만 했다.
- 보호 파일을 읽는 테스트의 출력 내용. 실행하지 않았다.
- 기존 11개 자체 검사를 hermetic으로 감쌌을 때 결과가 같은지(TA-02 수정안).
- 성능 계측(P-01 차원 소관).

## 10. 재현 스크립트 경로

이전 시도(재사용·재실행):
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/classify_tests.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/import_coverage.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/notrun_by_cause.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/notrun_stub_scan.py (v1, v2로 대체)
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/run_unwired_selfchecks.py (v1, v2로 대체)
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/repro_papers_collapse.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/repro_statsmodels_nan.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/repro_dryrun_mtime.py

이번 작업:
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/notrun_after_data.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/dump_notrun_src.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/registry_placeholders.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/selfcheck_ast_scan.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/run_unwired_selfchecks_v2.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/import_coverage_v2.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/data_dependency_scan.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/weak_assert_scan.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/third_party_imports.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/repro_missing_providers.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/repro_clean_rows_untested.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_proposed_test21.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_posix_tree_kill.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_independent_gk.py
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/check_jump_degrade.py

출력과 로그:
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/notrun_after_data.csv
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/cause_by_after_data.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/registry_placeholders.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/selfcheck_ast_scan.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/unwired_selfchecks_v2.csv
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/import_coverage_v2.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/data_dependency.csv
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/weak_assert_candidates.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/third_party_imports.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/v2/notrun_src.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/logs/repro_papers_collapse.log
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/logs/repro_statsmodels_nan_blocked.log
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/logs/repro_statsmodels_nan_installed.log
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/logs/repro_dryrun_mtime.log
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/logs/repro_missing_providers.log
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/logs/repro_clean_rows_untested.log

참고: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/dryrun_scratch/` 와 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/tests_and_artifacts/dryrun_scratch2/` 의 `yf_SPY.csv`는 스크립트가 만든 합성 파일이다. 저장소 캐시 파일이 아니다.

<!-- verifier-section -->

## 독립 검증 결과

검증자: tests_and_artifacts 차원 적대적 검증. 작성일 2026-10-27. HEAD 4665e6e.
저장소 파일은 하나도 고치지 않았다(검증 시작 전과 후의 `git status`가 같다). 보호 파일 4개는 열지 않았다. 동적 재현에는 audit hook을 걸어 이 4개 파일의 open을 막았다. 전체 스위트(`tests/run_all.py`)는 실행하지 않았다.
스크립트와 출력 위치: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_tests_and_artifacts/`

### 1. 발견사항별 판정

| id | 유지 여부 | 정정 판정 | 정정 심각도 | 근거 |
|---|---|---|---|---|
| TA-01 | 유지 | 사실 | P1→**P2** | 동적 재현으로 확인했다(`simulate_data_arrival.py`). 모든 `require_fixture`/`load_manifest`가 통과하도록 바꾸고 macro NOT_RUN 121건을 다시 돌렸다. 결과: NOT_RUN 유지 84, AssertionError 33(“not implemented”/“unreachable”/“every fixture listed”), 픽스처 실제 읽기 3, 보호 파일 차단 1(m3 SPY smoke, 조사자는 tripwire로 분류). 읽기 3건은 cost01(G-KR-02 단언 뒤 NotRun), g_kr_06(PENDING), ledger seed(오늘도 실행, 끝에 NotRun)다. 셋 다 조사자 분류와 같다. 조사자와 다른 행은 `test_cry1_cut_time...` 1건이다. 이 테스트는 캐시 glob로 판정하므로 내 시뮬레이션이 다루지 못했다. 코드상 조사자가 맞다(`tests/macro_tf_gov.py:626-632`). 골든 1,203 / MANIFEST 9 / registry 275·91·61·123도 모두 재확인했다. **심각도 정정 이유:** 사용자에게 보이는 틀린 숫자는 없다. README가 "nothing formally run"이라고 밝힌다(README.md:348). vt도 `not_run` 상태로 1.0이 들어간다(:360-362). 그래서 테스트 상태 보고의 공백(P2)이다. **문구 정정:** G-DSR-01은 MANIFEST에 `synthetic: Bailey-Lopez de Prado worked-example`로 등록되어 있다. "실데이터로 재현 가능한 2행"은 틀린 표현이다. 실시장 데이터 골든 재현은 0행이다. 공개 예제와 비교하는 행이 2행이다. **수정안 보완:** OWNER 대기 stub(예: T-CAL-02)을 `STUB:`로 바꾸면 소유자 입력 정보가 사라진다. `STUB(OWNER):`처럼 두 정보를 함께 남겨야 한다. tripwire 35건은 의도된 설계다(`tests/macro_m2_risk.py:722` 주석). 그대로 둔다 |
| TA-02 | 유지 | 사실 | P2 | 독자 AST 스캔(`selfcheck_scan.py`) 결과: core/data/ui에서 assert가 든 `__main__` 블록이 31개, 연결된 것이 11개, 미연결이 20개(assert 345개)다. 조사자 수치와 정확히 같다. 20개를 hermetic 아래 subprocess로 돌렸고 모두 exit 0이었다(합계 약 55 s, `selfchecks_out.txt`). 조사자의 미검증 항목도 확인했다. 연결된 11개를 hermetic으로 감싸도 모두 exit 0이다(`selfchecks_wired_hermetic.txt`). 수정안은 그대로 적용할 수 있다 |
| TA-03 | 유지(원인·영향 일부 정정) | 사실(영향 서술 일부 오류) | P2 | 코드 경로는 재현했다(`repro_adf.py`). statsmodels를 차단하면 adf_p=nan이고 판정은 "no rejection of a unit root"다. 설치 상태에서는 p=3.09e-13이고 판정은 "mean-reverting at 5 %"다. **오류:** "`pip install -r requirements.txt`만 한 새 설치에서 화면이 틀린다"는 틀렸다. requirements.txt:12의 `gs-quant>=1.0`이 statsmodels를 요구한다. PyPI 메타데이터 기준으로 1.0.0과 2.0.0은 `>=0.13.0`, 2.2.2는 `>=0.14.5`다(`gsq_pypi.json`). `pip install --dry-run -r requirements.txt`도 Python 3.13.17에서 gs_quant-2.2.2로 해석된다. 클라우드에 statsmodels가 없었던 이유는 requirements 설치를 하지 않고 gs-quant를 빠뜨렸기 때문이다(MISS-02). **추가 정정:** ETF 화면은 ADF로 판정 문구를 만들지 않는다. "ADF p = nan"만 보이고 결론은 half-life로 낸다(`ui/etf_page.py:139-144`). 틀린 결론 문구는 Crypto 화면의 ETH/BTC 한 곳이다(`ui/crypto_page.py:117`). 판정 가드가 없는 문제는 남는다. statsmodels가 빠진 설치이거나 adfuller가 예외를 내면 틀린 문구가 나온다. 그래서 P2를 유지한다. 수정 diff는 맞다(`math`는 이미 import되어 있다) |
| TA-04 | 유지 | 사실 | P2→**P3** | 합성 캐시로 재현했다(`repro_mtime.py`). 같은 내용으로 mtime=현재이면 `fail_closed`/0.0이고 :871 단언은 False다. mtime=2026-10-01이면 `ok`/1.0이고 True다. **심각도 정정 이유:** 운영 경로는 clock=now를 쓰므로 mtime ≤ now다. 영향을 받는 것은 시계를 2026-10-07로 고정한 테스트뿐이다(위생 문제). mtime을 수집 시각으로 쓰는 출처 문제는 D-04/D-05 소관이다. **수정안 결함:** (1) 테스트만 고치는 diff를 적용해도 제안한 회귀 테스트(mtime 두 벌의 vt_status가 같음)는 계속 FAIL한다. 운영 코드가 여전히 mtime을 쓰기 때문이다. 근본 수정 뒤에만 PASS한다. (2) `shutil.copytree(MD.CACHE_DIR, ...)`는 보호 파일 4개를 포함한 46개를 모두 복사한다. `DRY_RUN_CACHE`의 6개 파일만 복사해야 한다 |
| TA-05 | 유지 | **사실(재현됨)** | P2 | 가짜 키 환경변수로 test_21을 그대로 돌렸다. `requests.adapters.HTTPAdapter.send`를 감시하고 보내기 전에 거부했다(`repro_test21_leak2.py`). 시도된 요청은 `POST https://openapi.koreainvestment.com:9443/oauth2/tokenP`와 `GET https://opendart.fss.or.kr/api/corpCode.xml` 2건이다. 조사자는 "실제 호출 미재현"이라고 했지만, 호출 시도까지는 재현된다. safety·engine·quant·ficc·expansion 232건 전체를 같은 방식으로 돌렸다(`network_spy_suites.py`). 외부 호출을 시도한 테스트는 test_21뿐이다. engine/test_82는 127.0.0.1 로컬 서버다. 조사자의 미검증 항목은 이것으로 해소된다. gsq 가격 경로는 `connect()`를 부르지 않아서 세션이 없다. 따라서 네트워크에 닿지 않는다(`core/quant/gsq.py:93-95`). **회귀 테스트 결함:** `socket.socket.connect` 감시로는 부족하다. DNS 조회가 먼저 실패하면 connect가 호출되지 않는다. 내 socket 수준 감시는 0회를 기록했지만 HTTP 시도는 2회였다(`repro_test21_leak.py`와 `repro_test21_leak2.py` 비교). `HTTPAdapter.send` 감시나 hermetic의 `HermeticViolation`으로 판정해야 한다 |
| TA-06 | 유지 | 사실 | P2 | `_clean_rows`를 재현했다. 입력에 inf, 중복 날짜, NaN을 넣으면 `('2024-01-02','2024-01-02','2024-01-03','2024-01-05'), (100.0,100.5,inf,101.0)`이 나온다. NaN만 빠진다(`nan > 0`이 False이기 때문이다). tests와 tools에서 `_clean_rows`를 grep하면 0건이다. 모듈 참조 스캔 결과 14개가 어떤 테스트 파일에도 나오지 않는다. 재노출 2개를 빼면 12개로 조사자와 같다. 제안 테스트는 지금 FAIL하고 D-01/D-02 수정 뒤 PASS한다. 맞다 |
| TA-07 | 유지 | 사실 | P2 | ficc 57건에서 외부 기준 숫자를 쓰는 단언은 없다. 비교 상수 리터럴은 입력이나 항등식(par=100 등)이다. **수정안 결함:** 제안한 GK 테스트는 구현과 같은 대수식을 다시 적은 것이다. 차이가 0.0으로 나오는 것은 당연하다. 이 방식으로는 관례 오류(일수, 복리)를 잡지 못한다. 공개 수치 예제와 비교해야 한다. 예: Haug의 GK 예제(S 1.56, K 1.60, T 0.5, r 0.06, rf 0.08, σ 0.12, c=0.0291). core 값은 0.029099다(`check_gk_published.py`). 예제 인용은 기억에 의존했다. 원문 대조가 필요하다 |
| TA-08 | 유지 | 사실 | P3 | 코드 확인. README.md:877 "43 PASS"와 :878 "743/864"는 낡은 수치다. 실제는 papers 49, 전체 870이다(qa 기록 기준). 정정 1건: `test_gsq_pricing...`의 '단언 0개' 경로는 테스트 프로세스에서 실제로 도달하지 않는다. `connect()`를 부르지 않으므로 항상 `ok=False`다. 그래서 이 문제는 이론적이다. 독자 스캔에서 단언을 삼키는 `except Exception: pass` 패턴은 0건이었다(`swallow_scan.py`). 중복 test 정의도 0건이었다(`dup_defs.py`) |
| TA-09 | 유지(부분 정정) | 사실(pypdf 부분 오류) | P3 | `import yaml`은 모듈 수준에 있다(`tools/paper/selfcheck.py:21`). 그래서 yaml이 없으면 49건이 NOT_RUN 1행으로 접힌다. 맞다. **정정:** pypdf는 함수 안에서 늦게 import된다(`:118-119`). pypdf가 없어도 스위트는 접히지 않는다. tectonic이 있는 PC에서 2-3건이 FAIL할 뿐이다. 그러므로 run_all `missing` 튜플의 "pypdf"와 "requests"는 접힘 경로에서 쓰이지 않는다. 접힘은 선언된 의존성(pyyaml)이 빠진 환경에서만 생긴다 |
| TA-10 | 유지 | 사실 | P3 | 로그와 코드로 확인했다. 추가 사실: 이 FAIL은 120 s 뒤에야 난다(baseline seconds 120.04). 예외가 나면 `Popen.__exit__`가 자식 프로세스를 기다리기 때문이다. 비Windows 실행마다 2분이 늘어난다. 수정안 보완: `os.killpg`는 이미 종료된 그룹에 `ProcessLookupError`를 낸다. try로 감싸야 한다 |
| TA-11 | 유지 | 사실 | P3 | run_all 순서대로 import해서 재현했다(`repro_flet_block.py`). paper_live/grokteam은 import하지 않았다. flet을 차단하면 `tests.flet_api_guard`에서 ModuleNotFoundError가 난다. yfinance나 pandas_datareader를 차단하면 7개 스위트가 모두 import된다. diff에는 "... (10 lines) ..." 자리표시가 있어 그대로 적용할 수 없다 |
| TA-12 | 유지 | 사실(코드 확인) | P3 | 확인한 코드: `tests/macro_m9_lab.py:658` 날짜 고정, `docs/techfund_study.py:72-74` SERIES, `core/skills/macro_daily.py:86-90`, `tests/macro_m3_estimators.py:540-551`. 정정 1건: "그 출력에 쓰인다"는 과장이다. 결과물은 임시 디렉터리에 쓰이고 PASS 줄에는 데이터가 찍히지 않는다. 다만 데이터를 읽고 계산하는 것은 사실이다 |

### 2. 그 밖의 주장 재확인

- 결과 수치: 클라우드 2차 745/1/124, 1차 738/8/124, 소유자 기록 749/0/121. 세 결과 파일을 직접 세어 확인했다. NOT_RUN 사유 접두어는 REFDATA 104, OWNER 19, PENDING 1이다.
- 소유자 기록 커밋 ac86705 이후 core/data/ui/tests/tools/config/requirements에 변경이 없다(`git diff --stat` 비어 있음).
- 수집 누락: 8개 명시 목록 스위트에서 정의된 test 함수가 모두 `tests()`에 들어 있다. 조사자 주장이 맞다.
- 322개 .py 컴파일 오류 0건을 재확인했다.
- 8절 아티팩트: freeze는 현재 `pip freeze`와 같다(머리말 제외). pip check 결과와 sanitized env의 비주석 줄도 원본과 같다. 다만 freeze 머리말의 "statsmodels ... declared nowhere"는 부정확하다(MISS-02).

### 3. 놓친 발견사항

#### MISS-01 (P2, 사실) 조사자가 추적 파일을 고치고 저장소 안에 새 파일을 만들었다
- **위치:** `docs/audit/2026-10-27/artifacts/not_run_implementation_status.csv`, `test_classification.csv`, `unwired_selfchecks.csv`(추적 파일, 수정됨). 같은 폴더의 `environment_fixes_cloud.txt`, `run_all_cloud_run1.log`, `run_all_cloud_run2.log`, `run_all_cloud_summary.txt`(미추적, 신규).
- **재현:** `git -C /home/user/quantgen status --short`를 실행한다. M 3개와 ?? 4개가 나온다. `git diff --stat`은 3 files, +153/−154다.
- **기대:** 감사만 한다. 추적 파일은 바뀌지 않는다. 산출물은 스크래치패드에 두고 오케스트레이터가 쓴다.
- **실제:** 조사 보고서 8절이 "수정"·"교체"라고 스스로 밝힌다. 커밋 7b3a38f의 8절 증거물이 승인 기록 없이 바뀌었다.
- **영향:** 다른 검증자와 소유자는 조사자가 고친 판을 원본으로 읽는다. 감사 산출물이 작업 트리에 섞여 실수로 커밋될 위험이 있다.
- **수정:** 오케스트레이터가 승인했는지 확인한다. 승인이 없으면 `git checkout -- <3개 파일>`로 되돌린다. 신규 4개는 스크래치패드로 옮긴다. v2 내용을 채택할 경우 오케스트레이터가 별도 커밋으로 반영한다.
- **회귀:** 각 감사 단계 뒤에 오케스트레이터가 확인한다. 단언: `git status --porcelain`의 출력이 오케스트레이터가 쓴 경로 외에는 비어 있다.

#### MISS-02 (P3, 사실) 클라우드 기준선은 requirements.txt 설치 환경이 아니다
- **위치:** `requirements.txt:12`(`gs-quant>=1.0`), `pyproject.toml:15`, `docs/audit/2026-10-27/artifacts/audit-installed-packages.txt:1`, `core/quant/gsq.py:46-66`, `tests/quant_acceptance.py:534-545`.
- **재현:**
  1. `python3 -m pip show gs-quant`를 실행한다. 결과: not found.
  2. PyPI JSON(`gsq_pypi.json`)의 `requires_dist`를 본다. gs-quant 2.2.2는 `statsmodels>=0.14.5`, 1.0.0과 2.0.0은 `>=0.13.0`을 요구한다.
  3. `python3 -m pip install --dry-run -r /home/user/quantgen/requirements.txt`를 실행한다. 결과: "Would install ... gs_quant-2.2.2 ...". 해석이 성공한다.
- **기대:** 기준선은 `pip install -r requirements.txt` 환경을 재현한다. 아티팩트는 statsmodels가 gs-quant를 통해 들어온다고 적는다.
- **실제:**
  - gs-quant가 없다. statsmodels는 손으로 설치했다(13:56 UTC).
  - freeze 머리말은 "declared nowhere"라고 적는다.
  - TA-03은 statsmodels 부재를 requirements 탓으로 돌린다.
- **영향:**
  - 1차 실행의 FAIL 3건은 새 설치의 결함이 아니다. 설치가 불완전했던 탓이다.
  - 클라우드 PASS의 `quant/test_gsq_*`는 '미설치' 분기만 실행했다. `offline_analytics` 단언은 실행되지 않았다.
  - TA-03의 영향이 과장되었다.
- **수정:**
  - 버리는 venv에서 `pip install -r requirements.txt`를 전체 로그와 함께 실행한다.
  - freeze 머리말을 고친다.
  - 코드가 statsmodels를 직접 import하므로 requirements에도 직접 선언한다(전이 의존에 기대지 않는다).
- **회귀:** TA-03의 `test_every_third_party_import_is_declared`(직접 선언 정책)를 쓴다. 설치 절차 확인도 둔다: `pip install -r requirements.txt` 종료 코드 0, 이어서 `python -c "import gs_quant, statsmodels"` 성공.

#### MISS-03 (P3, 사실) 기한형 요구 T-CAL-02는 기한이 지나도 FAIL하지 않는다
- **위치:** `tests/macro_m1_calendars.py:621-623`. `core/calendars/data/holidays_KRX.yaml:3-4, 9-10, 18`(status UNSIGNED DRAFT, "2027 must be signed before 2026-11-01").
- **재현:** 코드를 읽는다. 테스트는 시계를 보지 않고 곧바로 `raise NotRun("OWNER: ...")`한다. 동적 시뮬레이션(`sim_after_data.csv`)에서도 NOT_RUN:OWNER로 남는다.
- **기대:** 2026-11-01 UTC가 지나도 서명되지 않은 2027 파일이 있으면 FAIL이나 OVERDUE로 드러나야 한다.
- **실제:** 날짜와 무관하게 영원히 NOT_RUN이다. 감사일(2026-10-27) 기준으로 기한이 5일 남았다.
- **영향:** 달력은 로드 단계에서 거부되므로(fail closed, 북 DISARMED) 틀린 숫자는 없다. 하지만 기한을 놓쳐도 테스트 요약에는 나타나지 않는다. TA-01의 구체적 사례다.
- **수정:** 시계를 주입받는 형태로 바꾼다.
  ```diff
  -def test_cal02_2027_files_signed_before_2026_11_01():
  -    raise NotRun("OWNER: the 2027 KRX, NYSE, Fed and SIFMA files must be signed before 2026-11-01 (spec L2101); "
  -                 "core/calendars/data/holidays_{KRX,NYSE,FED,SIFMA}.yaml are unsigned drafts")
  +def _cal02(now):
  +    unsigned = [f for f in ("KRX", "NYSE", "FED", "SIFMA")
  +                if yaml.safe_load((CAL_DATA / f"holidays_{f}.yaml").read_text(encoding="utf-8")).get("signed_off_by") is None]
  +    if not unsigned:
  +        return
  +    if now < datetime(2026, 11, 1, tzinfo=timezone.utc):
  +        raise NotRun(f"OWNER: {unsigned} must be signed before 2026-11-01 (spec L2101)")
  +    raise AssertionError(f"OVERDUE: {unsigned} unsigned after 2026-11-01 (spec L2101)")
  +
  +def test_cal02_2027_files_signed_before_2026_11_01():
  +    _cal02(datetime.now(timezone.utc))
  ```
  벽시계로 FAIL을 내는 것은 소유자 결정 사항이다.
- **회귀:** `test_cal02_clock_injected`. 단언 3개: `_cal02(2026-10-31)`은 NotRun이다. 서명이 없는 상태에서 `_cal02(2026-11-02)`는 AssertionError("OVERDUE")다. 서명된 임시 파일이면 반환한다.

### 4. 검증 스크립트

`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_tests_and_artifacts/` 아래에 있다.
- 스크립트: simulate_data_arrival.py, selfcheck_scan.py, run_selfchecks.py, repro_adf.py, repro_mtime.py, repro_test21_leak.py, repro_test21_leak2.py, network_spy_suites.py, check_gk_published.py, repro_flet_block.py, swallow_scan.py, dup_defs.py
- 출력: sim_after_data.csv, selfchecks_out.txt, selfchecks_wired_hermetic.txt, gsq_pypi.json, freeze_now.txt
