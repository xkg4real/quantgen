# ⑨-1 시점 기준 데이터와 미래 정보 누출 감사 결과 (2026-11-04)

- **상태:** 초안입니다. 소유자 검토를 기다립니다.
- **기준 커밋:** `main` `bb35b3b`(2026-11-04 03:36 +0900, PR #69 병합).
- **작성:** Claude(Step 7A 세션).
- **로드맵:** ⑨-1 "2-2 시점 기준 데이터와 누출 감사 결과 정리 — 기존 `lag_audit`과 M1 계약 기준의 보고서"(`docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md:136`, `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:103`). 선행은 ②-5입니다.
- **읽지 않은 것:** 보호 캐시 `docs/asset_expansion/cache/*`, 실행 출력과 홀드아웃 `paper_live/out*/`, 원장 `grokteam/out/book/`, 로컬 저장소와 캐시 `~/.nextgen`(운영 PIT 저장소가 있다면 여기 있음), 비밀값 `.env`. 이 경로는 이 클론에 없고, 열거나 grep하거나 해시하지 않았습니다. 이 경로를 읽는 연구, 리드아웃, 실데이터 검사, 네트워크 호출도 돌리지 않았습니다.
- **판정 정의:** 충족 = 사양 조항이 코드에 있고 기록된 검사가 PASS. 부분 = 코드에 있으나 범위나 연결에 공백이 있음. 미충족 = 조항이 빠졌거나 사양과 반대로 동작함. 해당 없음 = 그 영역에 시점 결정 경로가 없음.
- **심각도 정의:** 높음 = 누출이나 결측이 HALT·fail-closed를 건너뛰는 경로가 있거나, 판정을 받칠 실데이터 근거가 전혀 없음. 중간 = 감사·계약의 범위나 독립성 공백, 또는 연구 결과의 타이밍 오류. 낮음 = 현재 경로에서 발생하지 않는 잠재 결함, 기록·표시 문제, 보수적인 이탈.

## 0. 요약 — 영역별 판정 표

| 영역 | 판정 | 근거 한 줄 | 후속 조치 |
|---|---|---|---|
| PIT 저장소와 as-of 읽기(`pit_value`) | 충족(합성 데이터 기준) | 가시성 필터, 세션 일치, 합성 거부, 공식 종가 규칙이 있고 검사 PASS(`core/ficc/pit.py:396-420`) | LA-02 |
| 종가 도장과 10분 격리(`stamp_close`) | 부분 | 체결 시각이 예정 종가보다 이르면 막지 않음(`core/ficc/pit.py:492-510`) | LA-06 |
| 독립 지연 감사 함수(`lag_audit`) | 부분 | 최신 값 하나만 감사. 창 행, 파생 lineage는 감사 밖(`core/ficc/lag_audit.py:72-74`, `:114-115`) | LA-04, LA-05, LA-15, LA-16, LA-19, LA-23 |
| 감사 위반 시 런타임 조치(HALT) | 부분, NAV 라인은 미충족 | NAV 라인 종가의 바인딩이 `forward_sim`으로 덮여 HALT·page가 나가지 않음(`core/skills/macro_daily.py:479-489`, `:543-553`) | LA-01 |
| 백테스트·카드 측 감사(`LookAheadError`, 카드 거부, I-05) | 미충족 | 카드의 `lag_audit`는 합성 고정값. I-05는 한 번도 실행되지 않음(`core/quant/cardp.py:976-980`) | LA-02, LA-07 |
| 데이터 계약과 역할별 실패 동작(R-19) | 부분 | 신선도와 역할 동작은 구현. 단조 조항 미작동, NAV 결측이 acting으로 처리되지 않음(`core/ficc/contracts.py:472-479`) | LA-01, LA-20 |
| 교차시장 규칙(R-19 규칙 6, TASK-M1-18) | 매크로 충족, 연구 경로 미충족 | 매크로는 `bound + 60 s` 규칙 구현(`core/ficc/contracts.py:494-496`). Strategy Lab은 같은 날짜 종가를 그대로 결합(`core/quant/strategies.py:51-66`) | LA-12 |
| 달력(R-20) 서명과 범위 | 부분 | 17개 파일 서명 완료. KRX 휴장일은 2026-2027만 포함. 범위 HALT가 파이프라인에 연결되지 않음 | LA-08, LA-22 |
| 운영 데이터 적재 | 미충족(안전하게 닫힘) | 라이브 모드에서 저장소를 채우는 경로가 없음(`core/skills/macro_daily.py:120`, `:457-458`, `:1449`) | LA-03 |
| 실데이터 검사 증거 | 미충족 | 실데이터 PIT 조항은 전부 NOT_RUN. 데이터가 와도 코드 수정 없이는 PASS가 될 수 없음 | LA-02, LA-09 |
| 매크로 밖 전략 엔진의 인과성 | 충족(인덱스 기준) | 결정은 종가 t, 체결은 종가 t, 수익은 t→t+1(`core/quant/strategies.py:82-89`) | LA-13 |
| 매크로 밖 데이터 시점 | 미충족 | VIX 16:15 ET 종가로 16:00 ET 체결, OECD 월간 금리 1관측 지연, H.15·H.10 관측일 사용 | LA-10, LA-11, LA-24, LA-25 |
| 위치 이동 금지(T-LAG-02 linter) | 부분 | 런타임 헬퍼만 있고 운영 호출과 정적 검사가 없음(`core/ficc/lag_audit.py:126-141`) | LA-23 |
| 레거시 `as_of` 항목(D-04, D-05) | 미종결 | 결과 문서가 없음. 코드에 그대로 남아 있음(`core/ficc/macro.py:223`, `data/krx/kis_client.py:300`, `:361`) | LA-14 |

발견 사항은 29건입니다. 높음 2건, 중간 12건, 낮음 15건입니다(7절).

## 1. 범위와 방법

### 1.1 범위

1. `core/ficc/lag_audit.py`의 동작, 호출처, 적용 대상(3절).
2. M1 데이터 계층 계약 TASK-M1-01~M1-23과 그 검사(4절).
3. 매크로 밖 모듈의 결정 시점과 체결 시점: `core/quant/strategies.py`, `core/quant/validate.py`, `core/quant/backtest.py`, `docs/asset_expansion_study.py`, `core/research/strategy_workflow.py`, `core/ficc`(fx, fx_styles, curve_models, vol_products, bonds, curves), `core/crypto`, `core/quant/forward.py`, `paper_live/engine.py`·`replay.py`(코드만), 연구 브랜치의 `tools/nautilus`(5절).
4. 기록된 검사 결과와 기존 문서의 결론(6절).

### 1.2 방법

- 네 개의 독자 보고서를 합쳤습니다. 중복은 하나로 묶고, 서로 다른 주장은 코드를 다시 읽어 정했습니다(1.4).
- 근거는 세 종류로 나눕니다.
  - **[기록]** 기록된 검사 결과입니다. 이 세션에서 테스트를 다시 돌리지 않았습니다.
    - `qa/acceptance_results.json`: 소유자 Windows 실행, 870행(PASS 749, FAIL 0, NOT_RUN 121). 마지막 커밋은 `ac86705`(2026-10-23 23:34 +0900, "QA: full run on merged master")입니다. 파일 자체에는 실행 시각과 커밋이 없습니다.
    - 스크래치 `runs/full.json`: Linux 실행, 964행(PASS 836, FAIL 4, NOT_RUN 124). 파일 시각은 2026-11-03 18:49Z(2026-11-04 KST)입니다.
    - 스크래치 `runs/macro2.json`: Linux 매크로 재실행, 546행(PASS 424, FAIL 1, NOT_RUN 121). 파일 시각은 2026-11-03 19:03Z입니다. 매크로 행은 이 파일이 `full.json`을 대신합니다. 두 파일은 PIT 관련 행에서 모두 같습니다.
    - Linux 실행은 이 `main`을 포함한 연구 브랜치 트리에서 돌았습니다(작업 지시 기준). 실행 트리의 커밋은 로그에 남아 있지 않습니다(UNVERIFIED, 8절).
  - **[코드]** 코드 읽기입니다. 모든 인용은 `bb35b3b` 기준 `file:line`입니다.
  - **[검사]** 저장소 밖 스크래치에서 돌린 작은 재현입니다. 모두 `HOME`과 `TMPDIR`을 스크래치 아래 새 디렉터리로 두었고, 시장 데이터와 네트워크를 쓰지 않았고, 추적 파일을 쓰지 않았습니다.
    - 독자 1: `la_tools/probe.py`(P1~P7), `la_tools/keys.py`.
    - 독자 2: `hermetic_tmp` 아래 짧은 스니펫 4개(mvenv 인터프리터).
    - 독자 3: `la_probe/slack.py`(numpy만 사용).
    - 이 세션: `la_tools/keys.py`를 다시 돌렸고 결과가 같았습니다. 실행 뒤 `git status`는 깨끗했습니다.
- `core/skills/macro_daily.py` 파이프라인 전체는 돌리지 않았습니다. 이 환경에는 `scipy`가 없어 파이프라인 import가 실패합니다(독자 1 보고).

### 1.3 용어

- PIT는 이 문서에서 point-in-time(시점 기준)입니다.
- `core/quant/validate.py:676`의 `pit_tests`, `core/quant/lab.py:521`의 `fan_pit`, `ROADMAP_REVIEW_2026-10-27.md:50`(C4)의 "PIT 검정"은 probability integral transform입니다. 시점 기준 증거로 세지 않았습니다.
- 핸드오프 원장(`git show origin/handoff:LEDGER.md`, 로컬 원격 참조 기준)에는 ⑨-1 행이 없습니다. ⑨-2/a, ⑨-2/c는 있습니다(`LEDGER.md:54`, `:112`).

### 1.4 독자 사이의 불일치와 정리

| 주제 | 독자 주장 | 정리 | 근거 |
|---|---|---|---|
| DE/GB 월말 종가의 KeyError 심각도 | 독자 1 낮음, 독자 2 중간 | **낮음.** 적재 단계의 `is_session`이 먼저 KeyError를 내므로 이런 행은 저장소에 들어갈 수 없습니다. 라이브 적재도 연결돼 있지 않습니다. 다만 발생하면 모든 장부의 acting 단계가 멈춥니다 | `core/ficc/pit.py:572-574`, `core/calendars/clocks.py:97-99` |
| 세션 검사 약화의 심각도 | 독자 1 중간 | **낮음.** 운영 경로에서는 `pit_value`가 acting 종가를 결정 세션으로 걸러, 이전 세션 종가가 감사까지 오지 않습니다. 감사의 독립성 공백으로만 기록합니다 | `core/ficc/pit.py:401-402`, `:415-416` |
| `RawFrameRead` | 독자 2 "원시 프레임을 거부" | 둘 다 맞습니다. 함수는 거부하지만, 두 호출처가 미리 `PITValue`만 넘겨 운영에서는 도달하지 않습니다 | `core/ficc/lag_audit.py:112-113`, `core/skills/macro_daily.py:540`, `core/quant/risk_layer.py:660-664` |
| `forward_sim` 위반의 무처리 | 독자 1 "R-01 위반" | **낮음으로 낮춤.** §3.9는 acting과 risk-model 위반의 조치만 정합니다. R-01 "On violation"의 "forward record"는 R-25 forward record입니다. 사양 공백으로 기록합니다 | `QUANTGEN_MACRO_INTEGRATION.md:1210-1217`, `:1495` |
| 라이브 적재 미연결의 심각도 | 독자 2 높음 | **중간.** 모든 acting 입력이 안전하게 닫히므로 지금 누출은 없습니다. 계약이 운영 데이터로 돌지 않았다는 점은 LA-02(높음)에 함께 반영합니다 | `core/skills/macro_daily.py:457-458` |
| NOT_RUN 개수 | 독자 2 "M1 13건", 독자 4 "PIT 19건" | 범위가 다릅니다. 둘 다 맞습니다. M1 모듈 행 수는 이 세션에서 다시 셌습니다(6절) | `runs/full.json`, `runs/macro2.json` |
| NAV 결측 시 `data_ok` 처리 | 독자 1 "범위 밖, 미검증" | 이 세션에서 코드를 다시 읽었습니다. 같은 원인으로 결측도 `forward_sim` 실패로 처리됩니다(LA-01). 파이프라인 실행으로는 확인하지 않았습니다 | `core/skills/macro_daily.py:505-508`, `core/ficc/contracts.py:430`, `:458-459` |

## 2. 기준: lag_audit과 M1 계약

### 2.1 독립 지연 감사의 요구사항

- **§3.9 `macro.lag_audit`**(`QUANTGEN_MACRO_INTEGRATION.md:1210-1217`): `pit_value`와 독립으로, 모든 acting과 risk-model 입력에 대해 달력과 레지스트리로 `usable_at`을 다시 계산합니다. 요구는 다음과 같습니다.
  - `usable_at <= decision_utc`, `available_at_utc >= publication_instant`.
  - 종가는 예정 종가 이후여야 합니다. 파생 입력은 lineage의 각 입력을 감사합니다.
  - `retrieved_at_utc <= knowledge_utc`, R-01의 상태 검사와 세션 검사.
  - acting 위반은 그 입력이 먹이는 장부를 HALT(OPS)합니다. risk-model 위반은 `hedge_credit_off`와 경보이고 HALT가 아닙니다. 공분산 전용 바인딩은 이월 후 제외합니다(R-19 규칙 4).
  - 기록은 `macro_state.lag_audit`에 씁니다.
- **TASK-M1-19**(`QUANTGEN_V2_CLAUDE_CODE_TASKS.md:512-525`): 위 내용에 더해, 백테스트에서 `LookAheadError`를 내고 위반이 닿은 결과를 무효로 합니다. 잠정 행이 acting 입력에 닿으면 같은 위반입니다. linter는 간격이 있는 시계열의 위치 이동을 거부합니다. 수용 검사는 T-LAG-01, T-LAG-02, T-CLOSE-01입니다.
- **R-01**(`QUANTGEN_MACRO_INTEGRATION.md:1485-1495`):
  - 규칙 1: acting 입력은 `available_at_utc <= decision_utc`이고 지연은 달력 기준입니다.
  - 규칙 2: 종가형 acting 입력은 `official_close`이고 `session_date`가 결정 세션과 같아야 합니다.
  - 규칙 3: 종가 + 10분 전에 받은 행, 평평한 OHLC·거래량 0 행, 봉에서 만든 값은 종가로 저장하지 않습니다.
  - 규칙 6: 결측·신선도 초과·잠정·합성 입력은 역할별 동작을 따릅니다.
  - On violation: 위반은 백테스트 결과나 forward record를 무효로 합니다. 카드 연구는 카드를 쓰지 않습니다. 런타임은 HALT(OPS)입니다.
- **R-19**(`QUANTGEN_MACRO_INTEGRATION.md:1813`): 규칙 4는 역할별 실패 동작(`:1866`), 규칙 6은 교차시장 가용성 `close_print_bound_utc(M, D) + buffer < decision_utc`입니다(`:1892`).
- **R-20**(`QUANTGEN_MACRO_INTEGRATION.md:1983`): 규칙 3은 종가 도장입니다. `obs_utc`는 예정 종가, `available_at_utc`는 기록된 체결 시각 또는 bound입니다(`:2025-2031`). 규칙 6은 서명된 변경만 받습니다(`:2053`).
- **감사에 맡겨진 다른 문장:** "원시 DataFrame을 직접 읽지 않는다. 지연 감사가 이를 강제한다"(`:1106`). "맥락 로그는 acting 모듈이 읽지 않는다. 지연 감사와 import 가드(T-CTX-01)가 강제한다"(`:1672`).
- **사양이 인정한 한계:** v1.2의 지연 검사는 레지스트리의 `available_at`을 믿으므로 레지스트리 오류로는 실패하지 않습니다. 그래서 R-34가 성능 기반 타이밍 프로필과 양성 대조군을 더합니다(`:3397-3399`).

### 2.2 M1 종료 기준

- M1 종료 검사는 31개입니다(`QUANTGEN_V2_CLAUDE_CODE_TASKS.md:258`).
- 작업 목록은 M(k)의 종료 검사가 모두 통과해야 M(k+1)을 시작하라고 합니다(`QUANTGEN_V2_CLAUDE_CODE_TASKS.md:15`). 실행기는 NOT_RUN을 종료 코드에 넣지 않습니다(`tests/run_all.py:13-15`, 독자 2 인용). 그래서 "M1 통과"는 "FAIL 없음"이라는 뜻이고, 31개가 모두 PASS라는 뜻이 아닙니다. M2~M9는 이미 만들어져 있습니다.

## 3. lag_audit의 동작과 적용 범위

### 3.1 검사 항목 [코드]

`lag_audit(inputs, ctx, market, registry, clocks, *, lineage=None)`은 역할이 `acting_exposure`, `risk_model`, `forward_sim`인 입력만 셉니다(`core/ficc/lag_audit.py:21`, `:114-116`). `context`와 `history`는 건너뛰고 `checked`에도 넣지 않습니다.

| # | 검사(코드의 이름) | 대상 | 코드 |
|---|---|---|---|
| 1 | `available_at_utc <= decision_utc` | 감사 대상 전부 | `core/ficc/lag_audit.py:65-67` |
| 2 | `retrieved_at_utc <= knowledge_utc` | 감사 대상 전부 | `:68-70` |
| 3 | `usable_at <= decision_utc` | 등록, 비파생, bound가 있는 시계열 | `:76-80` |
| 4 | `available_at_utc >= publication_instant` | 3과 같음. 단 `available_at_source == "published"`이면 생략 | `:81-83` |
| 5 | `cross-market bound + 60 s < decision_utc`, 같은 날짜 HK 종가 금지 | 다른 시장의 종가 | `:84-91` |
| 6 | `value_status == official_close`(백테스트는 `vendor_close` 허용) | acting 종가 | `:92-95` |
| 7 | `session_date == decided session`(실제 비교는 `session_date != obs_date`) | acting 종가 | `:96-98` |
| 8 | `retrieved_at_utc >= close + 10 min` | acting 종가 | `:99-102` |

- `usable_at`은 종가면 `close_print_bound_utc(시장, obs_date)`, 일정이 `LIVE_QUOTE`·`AS_POSTED`·`DERIVED`이면 `None`, 그 밖에는 `publication_instant`입니다(`core/ficc/lag_audit.py:51-60`). 결정 시장을 받지 않습니다. `core/calendars/publication.py:239-275`의 `usable_at`과 다른 두 번째 구현입니다(독자 1·2 인용).
- 파생 값(`obs_kind == "derived"`)은 3~8을 직접 받지 않고 `lineage.get(content_hash, ())`로 재귀합니다. `lineage`의 기본값은 빈 dict입니다(`:72-74`, `:109`).
- 결과는 `{checked, violations[], books[]}`입니다. 백테스트에서는 위반이 있으면 역할과 관계없이 첫 위반만 적은 `LookAheadError`를 냅니다(`:118-123`).
- 달력 호출을 감싸지 않습니다. 달력 예외는 그대로 올라갑니다(`:57`, `:60`, `:87-89`, `:99`).
- `QUARANTINE_MINUTES`(10)와 교차시장 버퍼(60초)는 코드 상수입니다(`core/ficc/pit.py:35`, `core/ficc/contracts.py:38`, 독자 1 인용). 규칙 저장소에도 같은 값이 있습니다(`data/macro/rules_v2.0.0.json:369`, `:483`, 독자 1 인용).

### 3.2 호출처 [코드]

| 호출처 | 입력 | 시장·모드 | 위반 시 조치 |
|---|---|---|---|
| `core/skills/macro_daily.py:537-561`(파이프라인 3단계 `macro.lag_audit`) | `pit_snapshot`이 읽은 `PITValue`(최신 값 하나씩) | 결정 시장, 실행 모드 그대로 | acting: 장부별 `runtime_halt(..., "OPS", "lag_audit_violation")`와 page 경보. risk_model: warn과 `hedge_credit_off`. 그 밖(forward_sim): 조치 없음. 결과는 `ctx.state["lag_audit"]`. 백테스트는 `LookAheadError`가 단계 오류가 됨 |
| `core/quant/risk_layer.py:694-705`(`hedge_state`) | 자기가 읽은 risk-model 값(PCEPILFE, SPX 종가, 10년물, USD 프록시) | `"US"`, `"live"` 고정 | 해당 시계열을 stale로 표시(보수적 기본값). HALT 없음. 감사 예외도 stale로 처리 |

- `lag_audit_violation` HALT는 운영자 재무장이 필요합니다(`core/engine/books.py:58`, 독자 1 인용).
- 백테스트 단계 오류는 `acting_error`가 되어 뒤 acting 단계를 건너뛰고 `engine_feed`를 막습니다(`core/skills/pipeline.py:237-255`).
- 나머지 참조는 감사를 부르지 않습니다. 표시(`ui/macro_state_panel.py:360`), forward record 표시(`core/quant/forward.py:47`, `:637-649`), 카드의 합성 필드(`core/quant/cardp.py:976-980`), 카드 거부 조항(`docs/macro_overlay_study.py:281-282`)뿐입니다. `paper_live/`, `tools/`, `quantgen_desktop/`에는 참조가 없습니다(독자 1의 grep).
- `assert_no_positional_shift`는 테스트에서만 부릅니다(`tests/macro_m1_pit.py:805-809`, `tests/macro_m2_risk.py:656`). `core/`에 pandas `.shift(` 호출은 없습니다(독자 1의 grep).

### 3.3 적용 대상 [코드, 독자 1 집계]

- 레지스트리 73개 시계열 가운데 28개가 감사 대상 역할의 바인딩을 가집니다(`data/macro/series_registry.yaml:61-78`, 독자 1의 `la_tools/reg_table.py`).
  - 거래소 달력이 있는 종가 16개(KRX 5, NYSE 4, JP 2, HK 2, TW 2, CN 1).
  - 달력이 없는 시장의 종가 2개(`DAX_MONTH_END_CLOSE` DE, `FTSE100_MONTH_END_CLOSE` GB, `:733-734`).
  - 실시간 호가 3개(`US10Y_KIS_QUOTE`, `USD_LIVE_PROXY`, `USDKRW_1530_SNAPSHOT`).
  - 파생 acting 3개(`MOM_PAPER_LS_SERIES`, `DM_MKT_RET_24M`, `DM_MKT_VOL_126`).
  - 발표 시각이 있는 시계열 4개(`KODEX200_PDF`, `ECOS_1530_CLOSE`, `DGS10`, `PCEPILFE`).
- 감사 밖:
  - 나머지 45개(context, history, 미바인딩).
  - 모든 창 읽기. `pit_window`는 행을 `role="history"`로 돌려주므로(`core/ficc/pit.py:444-445`), 넘겨도 감사가 건너뜁니다.
  - 파생 값의 입력. 두 호출처 모두 `lineage`를 넘기지 않고(`core/skills/macro_daily.py:541`, `core/quant/risk_layer.py:700`), `PITValue`에는 입력 해시가 없습니다(`core/ficc/pit.py:129`, `:210-211`).
- 실시간 호가, `AS_POSTED`, 미등록 시계열은 검사 1·2만 받습니다. 이 둘은 `pit_value`의 가시성 필터가 이미 보장합니다(`core/ficc/pit.py:400`). 그래서 이 입력들에는 독립 검사가 사실상 없습니다(LA-23).

### 3.4 구조적 한계

- 감사는 행에 도장을 찍은 것과 같은 `clocks` 객체를 씁니다(`core/ficc/pit.py:487`). `pit_value`와는 독립이지만 달력·레지스트리와는 독립이 아닙니다.
- 날짜를 앞당겨 다시 붙이고 도장도 맞춘 값은 잡지 못합니다. 사양도 이 한계를 인정하고 R-34로 보완하려 합니다(`QUANTGEN_MACRO_INTEGRATION.md:3397-3399`). 그런데 R-34 쪽 감사 필드는 합성값입니다(LA-07).

## 4. M1 계약 항목별 구현 상태

검사 열은 2026-11-04 Linux 기록입니다. 줄 번호는 독자 2·4가 인용한 테스트 위치입니다. 상태는 [코드] 읽기 결과입니다.

| TASK | 내용 | 상태 | 근거 | 검사 |
|---|---|---|---|---|
| M1-01 | KIS 호가 필드 확인 | 미실행(소유자) | `docs/kis_quote_check/` 없음. KIS는 `unverified`라서 KIS 종가는 `vendor_close`로만 저장(`data/macro/series_registry.yaml:57-59`, `core/ficc/pit.py:502-505`) | NOT_RUN 2건(`tests/macro_m1_fixtures.py:483`, `tests/macro_m1_pit.py:1089`) |
| M1-02 | KIS 읽기 전용 가드 | 구현 | `config.py:86-90`, `data/krx/kis_client.py:56-77` | PASS |
| M1-03 | 유효일자 기준 시장 시계 | 코드 구현, 데이터 부분 | `core/calendars/clocks.py:187-268`. `holidays_KRX.yaml`은 2026-01-01~2027-12-31만(`core/calendars/data/holidays_KRX.yaml:5-7`). `kr_sessions`에 토요일·랜덤엔드 연장·2016년 전 수능 행 없음(`core/calendars/data/kr_sessions.yaml:15-27`) | 픽스처 PASS, 실제 파일 NOT_RUN(`tests/macro_m1_calendars.py:358`) |
| M1-04 | `regime_tags` | 부분 | `core/calendars/regime.py:31-92`. 서명 완료(`kr_regime_tags.yaml:1-11`). 기대값 CSV 없음 | 점 검사 PASS, 전체 범위 NOT_RUN(`tests/macro_m1_calendars.py:744`) |
| M1-05 | 달력 변경 통제, 60세션 범위 | 라이브러리 구현, 파이프라인 미연결 | `core/calendars/store.py:132-181`, `:410-448`. 운영 코드에서 `check_coverage`·`coverage_halt` 호출 없음(LA-08) | PASS |
| M1-06 | 발표 달력, 출처 예외 | 구현 | `core/calendars/publication.py:47-237`, `core/calendars/clocks.py:362-374` | 합성 PASS, 공식 달력 NOT_RUN(`tests/macro_m1_pit.py:581`) |
| M1-07 | 이중 시점 추가 전용 저장소, 지식 시각 고정 | 구현 | `core/ficc/pit.py:56-108`, `:217-315`. 라이브는 적재 뒤 `knowledge_utc` 고정(`core/skills/macro_daily.py:461-464`) | PASS |
| M1-08 | 시계열 레지스트리 | 구현. 채널 필드는 미사용 | `data/macro/series_registry.yaml:31-73`, `core/ficc/contracts.py:225-304` | PASS |
| M1-09 | 시계열별 계약 | 부분 | 단조 조항은 날짜를 받아야 작동하는데 `read_input`이 넘기지 않음. 위반 사유도 버림(`core/ficc/contracts.py:359-372`, `:472-479`) | 해당 검사 없음(LA-20) |
| M1-10 | `pit_value` | 구현 | `core/ficc/pit.py:378-420` | PASS |
| M1-11 | 공식 종가 우선 | 부분 | 체결 시각이 예정 종가보다 이른 경우를 막지 않음(`core/ficc/pit.py:492-510`). 운영 공식 종가 로더 없음. "시가 = 전일 종가" 표시 조항은 찾지 못함(UNVERIFIED) | 합성 PASS, 실데이터 NOT_RUN(`tests/macro_m1_pit.py:545`) |
| M1-12 | 캐시의 장중 행 차단 | 장치 구현, 미연결 | `core/ficc/data.py:217-265`. 로더가 `pit_store`·`not_before` 없이 호출(`core/ficc/data.py:449-497`, 독자 2 인용) | PASS(`tests/macro_m1_pit.py:303`) |
| M1-13 | 파생·월간 시계열 | 부분 | `put_derived`(`core/ficc/pit.py:638`)는 운영 호출 없음. ALFRED 빈티지 미구현 | 합성 PASS, CPI 3.353 NOT_RUN |
| M1-14 | 이름 붙인 시계열, 선물 롤 | 부분 | `core/ficc/pit.py:346-352`, `:434-463`. 고정 롤 달력은 소유자 입력 | PASS |
| M1-15 | 합성 데이터 거부 | 부분 | `pit_value`만 거부(`core/ficc/pit.py:408-409`). `pit_window`는 거부 안 함(`:434-447`) | PASS(LA-21) |
| M1-16 | 일정 기반 신선도 | 구현 | `core/ficc/contracts.py:482-487` 등 | PASS, G-STALE-01 NOT_RUN |
| M1-17 | 역할별 동작과 카운터 | 구현. 단 파이프라인의 바인딩 저장 결함 | `core/ficc/contracts.py:427-460`, `core/skills/macro_daily.py:499-531`(LA-01) | PASS |
| M1-18 | 교차시장 가용성 | 매크로 구현 | `core/ficc/contracts.py:494-496`, `core/calendars/publication.py:239-272` | PASS |
| M1-19 | 독립 지연 감사, 종가 도장 | 부분 | 3절 | T-LAG-01·02, T-CLOSE-01 PASS |
| M1-20 | 장부별 런타임 | 구현 | `core/engine/books.py:368-480`, `:501-540` | PASS |
| M1-21 | ECOS, Treasury par-yield 공급자 | 미구현 | 코드에 ECOS 엔드포인트와 treasury.gov 공급자 없음(독자 2 grep). `tests/fixtures/macro/ACQUISITION.csv`에 미취득으로 남음 | — |
| M1-22 | 골든 픽스처 | 미완(REFDATA) | `check_fixture`는 구현(`core/ficc/pit.py:731-756`). 생성기는 원천 디렉터리 부재로 거부 | 합성 PASS, 재생성 NOT_RUN(`tests/macro_m1_pit.py:405`) |
| M1-23 | M1 측정 | 미실행 | KODEX200_PDF 기본값만 레지스트리에 있음. FRED VIX 게시 지연은 선언값 | — |

## 5. 매크로 밖 모듈의 누출 위험 점검

주 근거는 독자 3의 [코드] 읽기입니다. 이 세션에서 다시 읽은 곳은 `core/quant/strategies.py:51-66`, `:82-89`, `core/research/strategy_workflow.py:58`, `docs/asset_expansion_study.py:368-380`, `core/ficc/vol_products.py:78-91`, `core/ficc/fx.py:22-30`, `:380-388`, `tests/expansion_acceptance.py:294-306`입니다. 연구 브랜치에서 읽은 함수들은 `main`과 같습니다(독자 3의 `git diff --stat`, 결과 없음).

| 모듈 | 결정 시점 규칙 | 체결 시점 | 전체 표본 통계 사용 여부 | 판정 | 근거 |
|---|---|---|---|---|---|
| `core/quant/strategies.py`(7개 계열, `simulate`) | 가중치 t는 t까지의 자료로 계산 | 종가 t. 수익은 t→t+1 | 가중치에는 없음 | 충족(동시 종가 패널일 때) | `core/quant/strategies.py:82-89`, `:125-389` |
| `core/quant/validate.py`(`walk_forward`, 게이트) | 표본 내 [o−w, o)에서 선택하고 o+embargo부터 적용 | 해당 계열 그대로 | DSR 분산, PBO, 국면 분할 중앙값. 평가 단계에만 사용 | 충족 | `core/quant/validate.py:347`, `:365-377`, `:446-452`, `:505-508`, `:570-583` |
| `core/quant/backtest.py` | 종가 t에 정한 포지션 | t+1 수익 | 없음 | 충족 | `core/quant/backtest.py:122-125`, `:160` |
| Strategy Lab(`core/research/strategy_workflow.py`, `align_panel`) | 날짜 교집합으로 비동기 시장 종가를 한 행에 둠. `risk_parity`, `pairs`는 늦게 닫는 시장의 종가를 읽을 수 있음 | 종가 t | 없음 | 미충족(TASK-M1-18 기준) | `core/quant/strategies.py:51-66`, `core/research/strategy_workflow.py:58`, `QUANTGEN_V2_CLAUDE_CODE_TASKS.md:506` |
| VIX 롤다운(`run_vix`, `roll_down_positions`) | VIX·VIX3M 종가(16:15 ET)로 결정 | VIXY·SPY 종가(16:00 ET) | 없음 | 미충족(T-VIX-01) | `docs/asset_expansion_study.py:370-380`, `core/ficc/vol_products.py:78-91`, `QUANTGEN_MACRO_INTEGRATION.md:1302` |
| FX carry·momentum(`core/ficc/fx.py`, `fx_styles.py`) | 월간 OECD 금리를 1관측만 늦춰 사용. FRED 최신 빈티지 | 순위일 | 없음 | 미충족(DF-04) | `core/ficc/fx.py:24-29`, `:380-388`, `core/ficc/fx_styles.py:42-43`, `:81` |
| PCA fly, DNS(`core/ficc/curve_models.py`) | 인덱스로는 인과적. 관측일 t의 DGS 곡선을 t에 사용(H.15는 다음 연준 영업일 게시) | 종가 t | 카드 게이트의 ADF·반감기는 전체 표본 | 부분(VALUE 타이밍) | `core/ficc/curve_models.py:183-213`, `docs/asset_expansion_study.py:481-485`, `QUANTGEN_MACRO_INTEGRATION.md:1299` |
| 암호화폐(`core/crypto/analytics.py`) | GARCH는 [t−w, t). kimchi z는 t 제외 꼬리 창. 단 DEXKOUS(d)를 d에 사용 | 일봉 UTC 마감 | `funding_carry` 분위수, ADF·반감기가 전체 표본 | 부분 | `core/crypto/analytics.py:76-92`, `:137`, `:158-159`, `:169` |
| 채권·금리 분석(`core/ficc/bonds.py`, `curves.py`) | `panel.latest()` 가격. 백테스트 결정 없음 | 없음 | 없음 | 해당 없음 | `core/ficc/bonds.py:12-14`, `core/ficc/curves.py:335-336` |
| `paper_live/engine.py`, `replay.py`(코드만) | 실행 중인 1분 봉 제외, 봉 끝 시각 도장, `index <= now`로 자름 | 마지막 관측 호가(결정에 쓴 가격, 최대 25분, KRX 30분 경과 가능) | 비홀드아웃 재생이 라이브 시점에 적합한 sigma를 과거 날에 적용(자기 공개) | 부분 | `paper_live/engine.py:189-206`, `:466-473`, `paper_live/replay.py:7-9`, `:151` |
| `core/quant/forward.py` | 소급 입력, 비라이브 행, 이전 세션 거부 | 해당 없음 | 경보 기준은 기록보다 앞선 설계 표본 | 충족 | `core/quant/forward.py:13-14`, `:494-500`, `:521-528` |
| `tools/nautilus`(연구 브랜치만, `main`에 없음) | `P[<=i]`만 사용 | 같은 봉 종가의 MARKET 주문 | 없음 | 해당 없음(`main`), 연구 브랜치는 부분 | 연구 브랜치 `0bc9595:tools/nautilus/sandbox.py:125-143`, `runner.py:629-634`(SPY 21:00 UTC 고정 도장) |

- `core/ficc/lag_audit.py`와 `LookAheadError`는 매크로 v2 경로에서만 씁니다. 위 표의 어떤 모듈도 감사를 부르지 않습니다(독자 3의 grep). 연구 브랜치의 모델 한계 대장도 v2 밖 경로는 감사 범위 밖이라고 적습니다(`MODEL_LIMITS_REGISTER_2026-10-28.md:2701`, 연구 브랜치 `0bc9595`).
- 수정 주가(`auto_adjust=True`)는 이 규칙들에 미래 기업행동을 새게 하지 않는다고 봅니다. 모든 계열이 비율, 로그 차분, 절편 있는 OLS를 쓰기 때문입니다(독자 3의 추론). 측정하지 않았습니다(UNVERIFIED).

## 6. 검사 증거

열은 상태입니다. Windows = `qa/acceptance_results.json`(2026-10-23), Linux = `runs/full.json`과 `runs/macro2.json`(2026-11-04, PIT 행은 두 파일이 같음). 이 세션에서 세 파일을 다시 읽어 확인했습니다.

| 검사 | 요구사항 | 2026-10-23 Windows | 2026-11-04 Linux | 비고 |
|---|---|---|---|---|
| T-LAG-01(4건: `macro_m1_pit` lag_01, `macro_m1_integration` stamping_and_lag_audit, `macro_m1_books` operator rearm, `macro_m7_cardp` probe isolation) | 독립 감사가 백테스트에서 raise, 런타임에서 HALT | PASS | PASS | 입력은 합성. 세션 검사(7번)와 lineage를 쓰는 사례는 없음 |
| T-LAG-02(`macro_m1_pit` 위치 이동 거부, `macro_m2_risk` vt 조항) | 간격 있는 시계열의 위치 이동 거부 | PASS | PASS | 이동한 행 자체는 감사하지 않음(LA-23) |
| T-CLOSE-01(`macro_m1_pit` close_01, `macro_m8_pipeline` close_01) | 10분 격리 경계, `calendar_bound` 도장 | PASS | PASS | |
| T-XMKT-01 | 교차시장 +60초 | PASS | PASS | |
| T-PROV-01(캐시 사고 재현 등) | 장중 행이 종가로 쓰이지 않음 | PASS | PASS | |
| T-PRINT-01 | 서킷브레이커 체결은 종가가 아님 | 합성 PASS, 실데이터 NOT_RUN | 같음 | 체결 시각을 넘기는 사례 없음(LA-06) |
| T-AVAIL-01 | 가용성 골든 표 | 합성 PASS, 공식 달력 NOT_RUN | 같음 | 공식 달력 검사는 무조건 NotRun |
| T-STALE-01 | 일정 기반 신선도 | 조항 PASS, G-STALE-01 NOT_RUN | 같음 | PASS의 "local smoke"는 보호 캐시 파일을 읽음(`tests/macro_m1_pit.py:615-618`). 파일은 열지 않음 |
| T-H10-01·02, T-H15-01, T-VIX-01, T-SYN-01, T-BAR-01·02, T-ROLE-01·02, T-SER-01·02, T-MISS-02, T-FIX-01(합성) | M1 데이터 조항 | PASS | PASS | |
| T-CAL-01 / T-CAL-02 범위 경보 | 서명, 범위 경보·HALT | PASS | PASS | 라이브러리 단위. 파이프라인 연결 검사는 없음(LA-08) |
| T-CAL-02 "2027 파일이 11-01 전에 서명" | 서명 기한 | NOT_RUN | PASS | 10-28~29 서명 뒤 바뀜 |
| T-CLOSE-02, T-SAT-01, T-REGIME-01 | 실제 서명 파일 | 픽스처 PASS, 실제 NOT_RUN | 같음 | KRX 휴장일이 2026년부터라 2015·2016·2025 골든이 안 됨 |
| T-HALT-01(`macro_m5_books`), T-OBS-04(`macro_m8_pipeline`) | 감사 원인의 HALT, 미실행 표시 | PASS | PASS | NAV 라인 위반 주입 사례 없음(LA-01) |
| T-PLACEBO-01·02, I-05 합성 | R-34 합성 대조군 | PASS | PASS | |
| T-PLACEBO-01 양성 대조군(KR_SOX_KRW) | 실제 양성 대조군 | NOT_RUN | NOT_RUN | |
| I-05 전체 표본 지연 감사 | COMPLIANT 골든 전체 감사 | NOT_RUN | NOT_RUN | 사유 "REFDATA: COMPLIANT golden backtest fixture 부재"(`tests/macro_m7_cardp.py:693-698`) |
| G-POST-01(3건) | 패치 후 데이터 행 | NOT_RUN | NOT_RUN | |
| I-01 dry run(`test_dry_run_end_to_end_on_the_local_cache`) | `pit_snapshot`·`lag_audit` 단계 실데이터 통과 | PASS | **FAIL**(두 파일 모두) | `tests/macro_m8_pipeline.py:852`의 `appended > 0`에서 실패. 원인 UNVERIFIED(LA-09) |
| T-REPLAY-01 | 바이트 단위 재생 | PASS | PASS | |
| T-LABEL-01, `macro_m3_estimators` 인과성 | 표시 라벨과 추정기의 인과성 | PASS | PASS | 실데이터 라벨 검사는 NOT_RUN |
| `expansion/strategies_are_causal` | 미래를 바꿔도 오늘 가중치 불변 | PASS | PASS | 1봉 여유가 있어 t+1 참조를 못 잡음. `risk_parity` 제외(LA-13) |
| `quant/test_backtest_has_no_lookahead` | 백테스트 엔진 무누출 | PASS | PASS | 합성 상승 시계열 |
| `macro_tf_gov/test_inv1_decide_at_close_fill_at_official_close_on_the_costed_engine` | 종가 결정, 공식 종가 체결 | PASS | PASS | |
| unittest 모듈 PIT 검사 6건(미래 가격·날짜·틱, embargo) | — | 행 없음 | 그룹 단위 "OK"만 | `ci_2.log`, `ci_7.log`, `ci_9.log`. 실행 트리 커밋 미기록 |

- **M1 모듈 합계**(`macro/macro_m1_*` 행, 이 세션에서 셈): Windows 82건 = PASS 68, NOT_RUN 14, FAIL 0. Linux 84건 = PASS 71, NOT_RUN 13, FAIL 0. 바뀐 상태는 `test_cal02_2027_files_signed_before_2026_11_01` 하나이고, 2건은 나중에 추가됐습니다.
- **PIT 관련 매크로 121건**(독자 4가 키워드와 레지스트리 ID로 고른 집합): Windows PASS 99, NOT_RUN 20, 없음 2. Linux PASS 102, NOT_RUN 19, FAIL 0.
- **NOT_RUN 19건의 코드 형태**(독자 4, [코드]): 데이터가 와도 코드 수정 없이는 하나도 PASS가 되지 않습니다.
  - 11건은 무조건 `NotRun`을 냅니다(예: `tests/macro_m7_cardp.py:694`, `tests/macro_m1_pit.py:582`).
  - 4건은 픽스처 확인 뒤에도 `NotRun`을 냅니다(예: `tests/macro_m2_risk.py:291`).
  - 4건은 픽스처가 등록되면 `AssertionError("unreachable" 또는 "not implemented")`로 FAIL합니다(예: `tests/macro_m1_calendars.py:388-389`, `tests/macro_m7_cardp.py:476-477`).
- **실데이터 근거:** PASS는 모두 합성 데이터, stub 시계, 테스트가 서명한 달력 위에서 나왔습니다. 예외는 T-STALE-01의 local smoke 하나입니다.

## 7. 발견 사항

### LA-01 NAV 라인 종가의 바인딩이 `forward_sim`으로 덮여, 감사 위반에 HALT가 없고 결측이 acting으로 닫히지 않음 — 높음

- **내용:**
  - `pit_snapshot`은 입력과 바인딩을 `(sid, b.consumer)` 키로 저장합니다(`core/skills/macro_daily.py:479`, `:489`).
  - `KRX_069500_OFFICIAL_CLOSE`에는 consumer가 둘 다 `nav`인 바인딩이 두 개 있습니다. acting(recommended·specification, `halt_after 3`)이 먼저이고 forward_sim(R-28, R-29)이 뒤입니다(`data/macro/series_registry.yaml:77-78`, `core/ficc/contracts.py:165-169`).
  - 읽기는 acting 바인딩으로 풀리지만(`core/skills/macro_daily.py:481`, `core/ficc/contracts.py:177-179`), 저장되는 바인딩은 마지막 `b`인 forward_sim입니다.
  - 결과 1: `macro.lag_audit`은 `roles`를 저장된 바인딩에서 만듭니다(`core/skills/macro_daily.py:542-544`). NAV 종가의 역할은 `{"forward_sim"}`만 남습니다. 위반이 나도 acting 분기(HALT, page)와 risk_model 분기를 모두 타지 않습니다(`:548-556`).
  - 결과 2: `data_ok`는 저장된 바인딩을 `on_input_failure`에 넘깁니다(`core/skills/macro_daily.py:506-508`). 이 함수는 바인딩의 역할을 씁니다(`core/ficc/contracts.py:430`). NAV 종가가 없으면 KR 두 장부의 acting fail-closed가 아니라 forward_sim 장부 실패로 처리됩니다(`core/ficc/contracts.py:458-459`). `vt`는 `KOSPI_OFFICIAL_CLOSE`를 읽으므로(`core/quant/risk_layer.py:71`) 이 결측을 대신 잡지 않습니다. NAV 계산은 수익률 없이 진행됩니다(`core/skills/macro_daily.py:569-578`).
- **근거:** [검사] 레지스트리만 읽는 재현(`la_tools/keys.py`, 이 세션에서 다시 실행): `KR: key ('KRX_069500_OFFICIAL_CLOSE', 'nav') overwritten: acting_exposure -> forward_sim (read as acting_exposure)`, `roles[KRX_069500_OFFICIAL_CLOSE] = ['forward_sim']`. 결과 2는 [코드]이고 파이프라인 실행으로 확인하지 않았습니다. 이 시계열에 위반이나 결측을 주입하는 파이프라인 검사는 없습니다.
- **기존 ID:** 없음. T-LAG-01 런타임 조항, T-ROLE-01, T-MISS-02와 관련됩니다.
- **권고(제안):** `pit_snapshot`이 풀린 바인딩(`resolved`)을 저장하거나 키에 역할을 넣습니다. NAV 종가 위반 주입 시 `recommended:KR`·`specification:KR`의 OPS HALT와 page를, 결측 주입 시 acting fail-closed를 확인하는 `macro_m8_pipeline` 검사를 더합니다. 관계: 새 작업입니다. ⑨-5(매크로 카드 실행)와 ⑥ 파일럿 전에 처리하는 것이 맞습니다. 라이브 적재(LA-03)가 연결되기 전까지는 실제로 발생하지 않습니다.

### LA-02 실데이터 기반 누출 증거가 없고, NOT_RUN 검사는 데이터가 와도 PASS가 될 수 없음 — 높음

- **내용:** 실데이터 PIT 조항은 Windows와 Linux 모두 NOT_RUN입니다. I-05 전체 표본 지연 감사, G-POST-01, T-PRINT-01 실데이터, G-STALE-01, T-MISS-01 CPI, T-AVAIL-01 공식 달력, T-PLACEBO-01 양성 대조군이 여기 듭니다. 6절대로 19건 모두 코드 수정 없이는 PASS가 될 수 없습니다. 일부 사유도 낡았습니다. `test_regime01_full_range_expected_values_file`은 서명 뒤에도 "unsigned draft"라고 적고(`tests/macro_m1_calendars.py:744-747`), `test_avail_01_official_calendars_are_owner_signed`는 서명 상태와 무관하게 NotRun입니다(`tests/macro_m1_pit.py:581-583`).
- **근거:** `tests/macro_m7_cardp.py:475-477`, `:693-695`, `tests/macro_m1_pit.py:405-416`, `:545-546`, `:647-650`, `:875-876`, `tests/macro_m1_calendars.py:386-389`, `:786-789`, `tests/macro_m3_estimators.py:531-534`, `tests/macro_m1_fixtures.py:315`, `tests/macro_m2_risk.py:289-292`, `:342-345`, `tests/macro_m8_forward.py:828-832`(독자 4 인용). `docs/product/DATA_READINESS_2026-10-29.json`은 73개 시계열 모두 `acquisition_status NOT_VERIFIED`, 기록된 차단 121건을 `NOT_RETESTED`로 둡니다(I-05는 `:2200-2205`, 독자 4 인용).
- **기존 ID:** I-05(NOT_RUN, REFDATA). ⑨-2 매크로 데이터 확보(⑨-2/a 완료분은 메타데이터 목록뿐, `LEDGER.md:54`).
- **권고(제안):** 이 보고서의 결론은 합성 데이터와 코드 읽기에 한정됩니다. 소유자 판단에도 그렇게 써야 합니다. 별도로 골든 본문을 구현해, 무조건 `NotRun`과 `unreachable` 단언을 `require_fixture` 뒤의 실제 단언으로 바꿉니다. 그래야 ⑨-2 데이터가 들어왔을 때 PASS나 FAIL이 납니다. 관계: ⑨-2의 후속 작업입니다. I-05는 ⑨-5 전의 수용 관문으로 둡니다.

### LA-03 라이브 PIT 적재가 연결되지 않아 M1 계약이 운영 데이터로 돈 적이 없음 — 중간

- **내용:** `Services.ingest`의 기본값은 `None`입니다(`core/skills/macro_daily.py:120`). `pit_snapshot`은 `ingest`가 있을 때만 적재합니다(`:457-458`). CLI는 아무것도 적재하지 않습니다(`:1449`의 주석 "the CLI ingests nothing"). 캐시 로더는 `pit_store`·`not_before` 없이 호출됩니다(`core/ficc/data.py:449-497`, `:535`, `:572`, `:608`, `:662`, 독자 2 인용). 공식 종가 로더(TASK-M1-11)와 ECOS·Treasury 공급자(TASK-M1-21)도 없습니다. 그래서 라이브의 모든 acting 입력은 `MissingInput("missing")`이 되어 닫히고 ARM되지 않습니다. 지금 누출은 없지만 계약은 검증되지 않은 상태입니다.
- **기존 ID:** 없음. TASK-M1-11, M1-12, M1-21과 관련됩니다.
- **권고(제안):** `data.ingest`를 구현합니다. `pit_snapshot`에서 가져오고, `not_before = bound + 10 min`으로 저장하고, 결정 마감까지 재시도한 뒤 지식 시각을 고정합니다. 기록된 공급자 응답으로 라이브 파이프라인을 돌리는 통합 검사를 더합니다. 관계: ⑨-2(데이터 확보)가 끝나야 의미가 있습니다. 연결 전에 LA-01, LA-04, LA-06을 먼저 고치는 순서를 권합니다.

### LA-04 창(`pit_window`) 행이 독립 감사 밖에 있음 — 중간

- **내용:** 감사는 `pit_snapshot`의 최신 값 하나와 `hedge_state`의 최신 값만 봅니다. 그런데 `vt`(R-06)의 20개 수익률 창, `corr63`, 헤지 다리, R-03·R-04 슬리브, NAV 수익률, forward_sim, optimize, forecast_eval은 `pit_window`로 읽습니다. 이 행들은 저장소의 가시성 규칙(도장 `available_at <= decision`)만 거칩니다. 달력으로 `usable_at`이나 `publication_instant`를 다시 계산하지 않습니다. `pit_window`는 행을 `role="history"`로 돌려주므로 넘겨도 감사가 건너뜁니다(`core/ficc/pit.py:444-445`, `core/ficc/lag_audit.py:114-115`). 너무 이르게 `published`로 찍힌 과거 행 하나가 통계를 바꿔도 위반이 나지 않습니다.
- **근거:** `core/quant/risk_layer.py:366-370`, `:706-709`, `core/quant/sleeves.py:338-345`, `:390-401`, `core/quant/forward_sim.py:373-374`, `core/quant/optimize.py:250-255`, `core/quant/forecast_eval.py:745-750`(독자 1 인용), `core/skills/macro_daily.py:572-573`(이 세션).
- **기존 ID:** §10 관찰 모델 110 "독립 지연 감사(lag_audit)", "창 행 미감사"(`docs/product/SECTION10_QUEUE_2026-10-30.json:843`, NOT_RUN).
- **권고(제안):** acting과 risk-model 소비자의 창 읽기가 돌려준 모든 행에 감사를 돌립니다(묶음 변형 가능). 감사한 창 행 수를 `macro_state.lag_audit`에 적습니다. 관계: §10 모델 110의 수정 범위입니다.

### LA-05 파생 acting 입력의 lineage를 감사하지 않음 — 중간(잠재)

- **내용:** 파생 값은 `lineage`로만 감사되는데 두 호출처 모두 넘기지 않습니다(`core/skills/macro_daily.py:541`, `core/quant/risk_layer.py:700`). `PITValue`에는 입력 해시가 없어 감사가 스스로 lineage를 만들 수도 없습니다(`core/ficc/pit.py:129`, `:205-211`). 미래 정보를 쓴 파생 값도 위반 0건으로 통과합니다. 파생 acting 시계열은 3개입니다(`data/macro/series_registry.yaml:736`, `:754`, `:772`). 지금은 `put_derived`의 운영 호출이 없어 파생 행이 생기지 않습니다(`core/ficc/pit.py:638`, 이 세션 grep). `lineage=`를 넘기는 검사도 없습니다(이 세션 grep, `core`와 `tests`).
- **근거:** [검사] 독자 1 P1: lineage 없이 `{'checked': 1, 'violations': []}`, lineage를 주면 위반 4건.
- **기존 ID:** 없음. TASK-M1-13, M1-19와 관련됩니다.
- **권고(제안):** 호출처가 저장소 행의 `inputs` 해시로 lineage를 만들어 넘기게 하거나, lineage가 없는 파생 입력을 감사가 거부하게 합니다. 운영 파생 작성기가 들어오기 전에 검사를 더합니다. 관계: 새 작업입니다.

### LA-06 이른 체결 시각이 기록된 종가가 `official_close`로 저장되고 감사를 통과함 — 중간(잠재)

- **내용:** `stamp_close`는 체결 시각이 bound보다 늦은 경우만 막습니다(`core/ficc/pit.py:492-494`). 예정 종가보다 이른 체결 시각을 막는 `IntradayPrint` 가드는 `clocks.close_stamp`에만 있고(`core/calendars/clocks.py:311-334`), `stamp_close`는 그것을 쓰지 않습니다. 체결 시각이 있으면 `available_at_source`가 `published`가 되고(`core/ficc/pit.py:506-507`), 감사는 `published`에 대해 검사 4를 건너뜁니다(`core/ficc/lag_audit.py:81`). 독자 2의 [검사]: 2026-03-09 KRX 행에 체결 시각 01:31Z(10:31 KST 서킷브레이커 체결), 수신 06:45Z를 주자 `official_close`, `available_at 01:31Z`로 저장됐고 감사 위반은 없었습니다. 이는 R-01 v2.0이 막으려던 2-Oct 장중 행 사고와 같은 종류입니다(`QUANTGEN_MACRO_INTEGRATION.md:1493`). 지금은 `print_times`를 넘기는 운영 호출이 없습니다(이 세션 grep, `core`·`tools`·`paper_live`·`docs`).
- **기존 ID:** 없음. T-PRINT-01, TASK-M1-11, R-20 규칙 3과 관련됩니다.
- **권고(제안):** `stamp_close`가 `print_time_utc < decision_time_utc`를 거부하거나 표시하게 합니다(`close_stamp` 재사용). 감사는 종가형 행의 `published` `available_at`이 예정 종가보다 이르면 위반으로 봅니다. 체결 시각이 있는 T-PRINT-01 사례를 더합니다. 관계: 새 작업입니다. LA-03 연결 전에 끝내야 합니다.

### LA-07 카드·백테스트 측 T-LAG-01이 감사에 연결되지 않음 — 중간

- **내용:** R-34 타이밍 프로필의 행은 `lag_audit` 위반 수를 `1 if L <= 0 else 0`으로 고정합니다(`core/quant/cardp.py:974-980`). 정직한 행만 세는 `prof["lag_audit_violations"]`는 늘 0이므로, `docs/macro_overlay_study.py:281-282`의 `CardRefused`는 실행될 수 없습니다. 카드 입력 로더는 아직 없습니다. `CardInputs.data_fn`은 `PITValue`가 아니라 배열을 돌려주므로 카드 백테스트를 `core.ficc.lag_audit`에 태울 경로가 없습니다(`docs/macro_overlay_study.py:131-142`, 독자 1 인용). R-01은 "모든 백테스트 결과와 모든 카드에 lag_audit 기록"을 요구합니다(`QUANTGEN_MACRO_INTEGRATION.md:1494`).
- **기존 ID:** I-05(NOT_RUN, REFDATA).
- **권고(제안):** 카드 로더를 만들 때 `pit_value`로 `PITValue`를 만들고 모든 acting 입력에 백테스트 모드 감사를 돌리게 합니다. 카드의 `lag_audit_violations`는 그 결과에서 가져옵니다. I-05는 수용 관문으로 유지합니다. 관계: ⑨-5(매크로 카드 실행)의 전제 조건입니다.

### LA-08 서명 달력이 백테스트 기간을 덮지 않고, 범위 HALT가 파이프라인에 연결되지 않음 — 중간

- **내용:**
  - 서명된 `holidays_KRX`는 2026-01-01~2027-12-31만 덮습니다(`core/calendars/data/holidays_KRX.yaml:5-7`). 2026년 전의 KR `is_session`·결정은 `CalendarCoverageError`를 냅니다(독자 2의 [검사]). `release_calendar`는 2025~2027이고 1995~2024는 2단계로 미뤘습니다(`docs/audit/2026-10-27/12_release_calendar.md`, F-07, 독자 4 인용). 그래서 과거 백테스트의 가용성·감사 판정에는 서명 달력 근거가 없습니다.
  - 운영 코드는 `check_coverage`나 `coverage_halt`를 부르지 않습니다(이 세션 grep, `core`·`paper_live`·`tools`; 정의는 `core/calendars/store.py:410`, `core/engine/books.py:368`). 범위를 벗어난 날짜는 OPS HALT와 60·20세션 경보 대신 잡히지 않은 예외가 됩니다(`core/skills/pipeline.py:207`, `core/skills/macro_daily.py:1462`, 독자 2 인용). ARM 사전조건은 범위를 확인합니다.
- **기존 ID:** `kr_sessions.yaml`의 `owner_must_sign` 목록, `12_release_calendar.md` F-07, NOT_RUN 사유.
- **권고(제안):** 이 보고서의 PIT 결론을 발표일은 2025년 이후, KRX 세션은 2026년 이후로 한정합니다. 소유자: 과거 KRX 휴장일(최소 2015·2016·2025 골든 날짜), 토요일 종가, 랜덤엔드 연장 행에 서명합니다. Claude: `run_decision` 시작에서 `check_coverage(..., halt=coverage_halt(...))`를 부르고 `CalendarCoverageError`를 OPS HALT로 기록합니다. 관계: 서명은 ①-2(완료)의 연장이고, 연결은 새 작업입니다.

### LA-09 `pit_snapshot`·`lag_audit` 단계를 실데이터로 지나는 유일한 검사(I-01)가 Linux에서 FAIL — 중간

- **내용:** `test_dry_run_end_to_end_on_the_local_cache`는 Windows(2026-10-23, 달력 서명 전)에서 PASS, Linux 두 실행에서 FAIL입니다. 실패 위치는 `appended > 0` 단언입니다(`tests/macro_m8_pipeline.py:852`). 검사는 보호 캐시에 의존합니다(`:875`). 원인은 UNVERIFIED입니다. Linux에 캐시가 없는 것이 가장 그럴듯하지만, 캐시를 열지 않았으므로 확인하지 않았습니다.
- **기존 ID:** 없음.
- **권고(제안):** 캐시가 있는 소유자 Windows에서 현재 `main`으로 다시 돌려 결과를 기록합니다. 그때까지 10-23의 PASS를 현재 증거로 쓰지 않습니다. 관계: ⑤-1(Windows 인계) 실행 때 함께 돌릴 수 있습니다.

### LA-10 VIX 롤다운 카드가 16:15 ET VIX 종가로 결정하고 16:00 ET 종가로 체결함 — 중간

- **내용:** `run_vix`는 `^VIX`, `^VIX3M`, VIXY, SPY를 같은 날짜로 묶습니다(`docs/asset_expansion_study.py:370-373`). `roll_down_positions`는 `basis[t]`로 `W[t]`를 정하고(`core/ficc/vol_products.py:81-91`), `simulate`는 VIXY·SPY의 종가 t에 체결합니다(`core/quant/strategies.py:82-83`). 사양은 VIX·VIX3M 공식 종가를 16:15 ET로 두고, T-VIX-01은 VIX(D)를 D의 미국 종가에 쓸 수 없다고 합니다(`QUANTGEN_MACRO_INTEGRATION.md:1302`, 독자 3 인용). 효과 크기는 UNVERIFIED입니다(연구 미실행). 저장된 카드 S_V1은 REJECT(DSR 0.279, 독자 3 인용)이고, 편향은 전략에 유리한 쪽이므로 판정은 그대로입니다. 라이브러리 함수는 이 타이밍을 그대로 갖고 있습니다.
- **기존 ID:** 없음. ML #96은 같은 종가 체결 가정만 기록합니다(`MODEL_LIMITS_REGISTER_2026-10-28.md:2399-2415`, 연구 브랜치).
- **권고(제안):** `run_vix`와 `roll_down_backtest`에서 basis를 한 세션 늦춥니다. `roll_down_positions`에 T-VIX-01형 단위 검사를 더합니다. 저장된 카드의 타이밍을 NON-COMPLIANT로 기록합니다. 관계: 새 작업이고 ②-4 목록에 더할 후보입니다.

### LA-11 월간 OECD 단기금리가 1관측만 늦춰지는데 "no lookahead"라고 적혀 있음 — 중간

- **내용:** `_ffill_rates`는 메모에 "monthly"가 있으면 1관측 늦춥니다. 3월의 어느 날이든 2월 평균을 씁니다(`core/ficc/fx.py:24-29`, `:380-388`). 감사 보고서는 FRED 갱신을 3월 16일로 확인했고, 코드 주석은 이 시계열이 "6-8개월 늦다"고 적습니다(독자 3 인용). 금리는 FRED 최신 빈티지입니다. JPY, KRW, AUD, CAD, CHF는 월간만 있어 carry 순위, dollar-carry, momentum 누적이 게시 전 값을 씁니다. 화면 메모는 여전히 "no lookahead"입니다(`ui/fx_page.py:322`, 독자 3 인용). 이 지연은 위치 이동이므로 T-LAG-02도 어깁니다. 실제 게시 지연은 UNVERIFIED(감사 원문도 '추정')입니다. 영향: FX 화면 carry 백테스트, S_V3, S_V4(둘 다 REJECT).
- **기존 ID:** DF-04(P3, 추정, PT-14 물결 2, 소유자 결정 12.4, `KNOWN_ERRORS_REGISTER_2026-10-28.md:1575`, 연구 브랜치), ML #83. `main`과 연구 브랜치 모두 미수정입니다.
- **권고:** DF-04 수정을 PT-14 물결 2대로 진행합니다. 게시일 규칙으로 순위를 매기고 "no lookahead" 문구를 지웁니다. S_V3, S_V4는 라벨을 붙인 민감도로만 다시 계산합니다. 관계: 기존 ②-4 항목입니다. 새 작업이 아닙니다.

### LA-12 Strategy Lab이 비동기 시장의 같은 날짜 종가를 결합하고 모든 시행을 COMPLIANT로 기록함 — 중간

- **내용:** `align_panel`은 날짜 라벨의 교집합을 씁니다(`core/quant/strategies.py:51-66`). KRX 종가(06:30Z), NYSE 종가(20:00/21:00Z), 암호화폐 종가(다음 날 00:00Z)가 한 행에 들어갑니다. `risk_parity`의 공분산 창과 `pairs`의 z는 같은 날짜의 모든 열을 씁니다(`core/quant/strategies.py:340`, `:385-389`, 독자 3 인용). 그래서 KRX나 미국 다리의 가중치가 몇 시간 뒤에 닫는 시장에 기댈 수 있습니다. 자산별 계열(`trend_switch`, `vol_target`, `tsmom`, `crypto_trend`)은 영향이 없습니다. `register_trials`는 시장이 섞여도(`MULTI`) `timing_class="COMPLIANT"`를 고정값으로 영구 원장에 씁니다(`core/research/strategy_workflow.py:52-58`). TASK-M1-18은 "비동기 시장의 같은 날짜 종가를 결합하지 않는다"고 합니다(`QUANTGEN_V2_CLAUDE_CODE_TASKS.md:506`).
- **기존 ID:** ML #24(정렬을 가정으로만 기록), ML #110(Lab은 감사 범위 밖). KE ID는 없습니다.
- **권고(제안):** `run_family`에서 `risk_parity`와 `pairs`에 비동기 패널이 들어오면 거부하거나 늦게 닫는 시장을 한 세션 늦춥니다. `timing_class`는 그 검사 결과로 정합니다. 관계: ⑨-3a(R3 레지스트리 구현)가 시행 기록 형식을 바꿀 때 함께 반영하는 것이 맞습니다.

### LA-13 인과성 회귀 검사가 1봉 앞 참조를 잡지 못하고 `risk_parity`를 빼먹음 — 중간

- **내용:** `test_strategies_are_causal`은 `P[600:]`를 바꾸고 `W[:599]`만 비교합니다(`tests/expansion_acceptance.py:294-306`). 행 599의 입력 `P[:600]`은 바뀌지 않으므로, `P[t+1]`을 읽는 규칙도 통과합니다. 독자 3의 [검사](`la_probe/slack.py`): t+1 참조 규칙은 `[:599]`에서 통과하고 `[:600]`에서 실패, t+2 참조는 둘 다 실패. `risk_parity`는 목록에 없습니다. FICC·암호화폐 신호 함수(`butterfly_signal`, `roll_down_positions`, FX 가중치 함수, kimchi z)에는 접두 불변 검사가 없습니다. 지금은 읽어 보면 인과적이지만 이를 고정하는 검사가 없습니다.
- **기존 ID:** 없음.
- **권고(제안):** `W[:600]`을 비교하고 `risk_parity`, `trend_switch(vol_cap)`, `vol_target(band)`를 더합니다. 위 신호 함수에도 같은 접두 검사를 더합니다. 관계: 새 작업입니다. 작은 검사 수정입니다.

### LA-14 감사 항목 D-04, D-05가 닫히지 않음 — 중간

- **내용:** 2026-10-27 감사 요청은 D-04(매크로 기준일이 가장 늦은 관측일이라 지표별 지연을 가릴 수 있음)와 D-05(KIS `as_of`가 수신 시각일 수 있음)를 "높음·미확정"으로 적었습니다(`docs/audit/2026-10-27/00_request.md:24-25`). 2026-10-28 결정으로 범위가 달력으로 좁혀졌고(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:34-55`, 독자 4 인용), 두 항목의 결과 문서는 없습니다. 코드에는 그대로 있습니다: `MacroSheet(as_of=max(r.last_date for r in rows), ...)`(`core/ficc/macro.py:223`), `as_of=_now()`(`data/krx/kis_client.py:300`, `:361`).
  - 이 세션의 확인 범위: `core.ficc.macro`는 맥락 전용 보호 모듈이고 acting 모듈은 import할 수 없습니다(`core/ficc/context_log.py:77`, T-CTX-01). `core/skills/macro_daily.py`는 `kis_client`를 import하지 않습니다(grep). 그래서 매크로 v2 행동 경로에는 닿지 않는 것으로 보입니다.
  - `kis_client`는 `core/quant/history.py:198`, `core/research/watchlist.py:57`에서 씁니다. 이 경로의 `as_of`가 결정에 쓰이는지는 UNVERIFIED입니다.
- **기존 ID:** D-04, D-05(`00_request.md`).
- **권고:** 소유자가 이 보고서로 두 항목을 닫을지 정합니다. 닫는 문장의 초안: "D-04: 매크로 v2 acting 경로 해당 없음(`context_log.py:77`), 표시 경로의 기준일 표기 문제로 남김. D-05: 매크로 v2 acting 경로 해당 없음. `history.py`·`watchlist.py` 경로 확인 필요." 관계: 기존 감사 항목의 종결입니다.

### LA-15 감사의 세션 검사가 결정 세션이 아니라 `obs_date`와 비교함 — 낮음

- **내용:** R-01 규칙 2는 `session_date == 결정 세션`을 요구합니다(`QUANTGEN_MACRO_INTEGRATION.md:1493`). 감사는 같은 이름으로 `v.session_date != v.obs_date`를 봅니다(`core/ficc/lag_audit.py:96-98`). `RunContext`에는 결정 세션 필드가 없습니다. 독자 1의 [검사] P2: 10월 1일 공식 종가를 10월 2일 KR 결정에 넣어도 위반 0건. 운영 경로에서는 `pit_value`가 acting 종가를 결정 세션으로 거르므로(`core/ficc/pit.py:401-402`, `:415-416`) 실제로는 막힙니다. 감사가 이 조항에서 독립적이지 않다는 뜻입니다. 이 검사를 실행하는 테스트는 없습니다(독자 1 grep).
- **기존 ID:** 없음.
- **권고(제안):** 결정 세션을 감사에 넘기고 acting 종가의 `session_date`와 `obs_date`를 그것과 비교합니다. 이전 세션 종가 사례를 검사에 더합니다.

### LA-16 DE·GB 월말 종가에서 감사가 KeyError를 냄 — 낮음(잠재)

- **내용:** `DAX_MONTH_END_CLOSE`(DE), `FTSE100_MONTH_END_CLOSE`(GB)는 종가형이고 forward_sim에 바인딩돼 있습니다(`data/macro/series_registry.yaml:64-65`, `:76`, `:733-734`). 감사는 이들에 `close_print_bound_utc`를 부르고, M1 시장(`KR, US, JP, CN, HK, TW`)이 아니면 KeyError가 납니다(`core/calendars/clocks.py:25`, `:97-99`, `core/calendars/store.py:248-252`). `pit_snapshot`은 forward_sim 바인딩을 모든 시장의 결정에서 읽고, `macro.lag_audit`은 acting 단계입니다. 이런 행이 저장되면 acting 단계 오류가 되어 모든 장부의 뒤 단계가 건너뛰어지고 결정이 누락으로 셉니다(`core/skills/pipeline.py:249-255`, `:316-317`). "forward_sim 실패는 다른 장부를 HALT하지 않는다"는 원칙과 어긋납니다. 다만 적재 단계의 `is_session`이 같은 KeyError를 먼저 내므로(`core/ficc/pit.py:572-574`) 지금은 이런 행이 생길 수 없습니다.
- **근거:** 독자 1 P4(stub), 독자 2의 [검사](mvenv), 이 세션 [코드].
- **기존 ID:** 없음.
- **권고(제안):** 감사의 달력 호출을 감싸 실패를 그 입력의 역할과 장부로 한정된 위반으로 기록하거나, 달력이 없는 시장의 종가 등록을 거부합니다. DAX 행이 있는 저장소로 검사합니다.

### LA-17 forward_sim 위반은 조치가 없고, 공분산 전용 risk 입력은 과잉 반응함 — 낮음

- **내용:** forward_sim 입력은 감사되지만(`core/ficc/lag_audit.py:21`) 파이프라인 단계는 acting과 risk_model만 처리합니다(`core/skills/macro_daily.py:546-556`). forward_sim 위반은 경보도, FORWARD-SIM 장부 실패도 없습니다. §3.9는 이 경우의 조치를 정하지 않으므로 사양 공백입니다(1.4). 반대로 모든 risk_model 위반은 `hedge_credit_off`를 켭니다. §3.9는 공분산 전용 바인딩(ASIA_INDEX_CLOSES 등)은 이월 후 제외라고 합니다(`QUANTGEN_MACRO_INTEGRATION.md:1214-1216`). `data_ok`는 이를 따르지만(`core/ficc/contracts.py:448-451`) 감사 단계는 따르지 않습니다. 보수적인 쪽의 이탈입니다.
- **기존 ID:** 없음.
- **권고(제안):** forward_sim 분기(경보와 그 장부만 fail-closed)를 더하고, `binding.action == "risk_model_covariance"`이면 이월 후 제외를 적용합니다. 사양 §3.9에 forward_sim 조치를 적을지는 소유자가 정합니다.

### LA-18 백테스트 위반 시 `macro_state.lag_audit`가 빈 기록이 되어 '미실행'과 '깨끗함'을 구분하기 어려움 — 낮음

- **내용:** 백테스트에서는 `LA.lag_audit`이 `ctx.state["lag_audit"]`을 쓰기 전에 raise합니다(`core/skills/macro_daily.py:541`, `:557`). `build_macro_state`는 `{checked: 0, violations: []}`과 `extras.lag_audit_status = "not_run"`을 씁니다(`core/ficc/macro_artifacts.py:323-327`). 위반 내용은 실행 기록의 단계 오류에만 남습니다. 패널은 `lag_audit`만 읽고 `lag_audit_status`는 읽지 않습니다(`ui/macro_state_panel.py:360`).
- **기존 ID:** 없음. T-OBS-04(미실행 표시)는 PASS입니다.
- **권고(제안):** 단계에서 `LookAheadError`를 잡아 위반 목록을 기록한 뒤 다시 raise합니다. 패널에 `lag_audit_status`를 표시합니다.

### LA-19 감사 기준값의 하드코딩, 느슨한 백테스트 공급사 규칙, `hedge_state`의 시장 고정 — 낮음

- **내용:**
  - 10분 격리와 60초 버퍼가 코드 상수입니다. 규칙 저장소의 같은 값과 묶는 검사가 없습니다(`core/ficc/pit.py:35`, `core/ficc/contracts.py:38`, `core/calendars/store.py:242-245`, `data/macro/rules_v2.0.0.json:369`, `:483`).
  - 백테스트에서 감사는 어떤 `vendor_close`든 받습니다(`core/ficc/lag_audit.py:93`). `pit_value`는 선언된 공급사만 받습니다(`core/ficc/pit.py:411-412`). 독자 2의 [검사]: 선언 공급사가 없는 백테스트에서 KIS `vendor_close`가 위반 없이 통과.
  - `hedge_state`는 KR 결정에서도 `"US"`로 감사하므로 미국 종가에 60초 버퍼가 적용되지 않습니다(`core/quant/risk_layer.py:700`). 결정 시각이 몇 시간 떨어져 있어 실제 영향은 거의 없습니다.
  - `data.us10y.dgs10_strict_lag_bdays=2`, `treasury_lag_bdays=1` 키를 읽는 `.py`가 없습니다(독자 1 grep). H.15 16:15 ET 발표 시각 규칙과 같은지는 UNVERIFIED입니다.
- **기존 ID:** §10 관찰 모델 110 "백테스트 공급사 기준 불일치"(`docs/product/SECTION10_QUEUE_2026-10-30.json:843`).
- **권고(제안):** 두 값을 유효 규칙 저장소에서 읽거나 일치 검사를 더합니다. 선언 공급사를 감사에 넘깁니다. `hedge_state` 감사에 결정 시장을 넘깁니다.

### LA-20 데이터 계약의 단조 조항이 작동하지 않고 위반 사유가 사라짐 — 낮음

- **내용:** `check_contract`의 단조 조항은 `obs_date`와 `previous_date`가 있어야 작동합니다(`core/ficc/contracts.py:370-371`). `read_input`은 둘을 넘기지 않고, 위반이면 사유 없이 `MissingInput("missing")`을 돌려줍니다(`core/ficc/contracts.py:472-479`). NAV 라인 `KRX_069500_OFFICIAL_CLOSE`의 계약에는 범위와 일간 수익률 한도가 없습니다(`data/macro/series_registry.yaml:218-223`).
- **기존 ID:** §10 관찰 모델 153(N-04) "단조 조항 미작동, 위반 사유 소실, NAV 라인 계약 없음"(`docs/product/SECTION10_QUEUE_2026-10-30.json:893-894`).
- **권고:** §10 모델 153의 수정 범위대로 처리합니다. 새 작업이 아닙니다.

### LA-21 `pit_window`가 합성·auto 행을 거부하지 않음 — 낮음(잠재)

- **내용:** `pit_value`는 context가 아닌 읽기에서 합성·auto 행을 거부합니다(`core/ficc/pit.py:408-409`). `pit_window`에는 이 필터가 없습니다(`:434-447`). `_close_ok`는 상태와 공급사만 거릅니다(`core/quant/risk_layer.py:324-327`, 독자 2 인용). 선언 공급사의 auto 행이 백테스트 `vt` 창에 들어갈 수 있습니다.
- **기존 ID:** §10 관찰 모델 104 "pit_window 합성·auto 미거부"(`docs/product/SECTION10_QUEUE_2026-10-30.json:838`).
- **권고:** §10 모델 104의 수정 범위대로 처리합니다.

### LA-22 발표 지연·취소 이벤트가 운영 시계에 전달되지 않음 — 낮음

- **내용:** `publication_instant`는 이벤트를 받을 때만 지연·취소된 발표의 예정 시각을 옮기거나 지웁니다(`core/calendars/publication.py:171-180`, 독자 2 인용). `default_services`는 `CalendarClocks(registry, cal=cal)`을 이벤트 없이 만듭니다(`core/skills/macro_daily.py:166-167`). `events`는 `Services`에만 들어갑니다(`:176`). R-19 규칙 3의 이동·삭제 조항이 운영에서 작동하지 않습니다. 지연된 발표가 예정 시각에 "가용"으로 계산될 수 있습니다. 실제 값의 도장은 수신 시각으로 제한되므로 누출보다는 신선도 판정 오류에 가깝습니다(UNVERIFIED).
- **기존 ID:** 없음.
- **권고(제안):** `default_services`가 이벤트를 `CalendarClocks`에 넘기게 하고, 지연된 BLS 발표로 검사합니다.

### LA-23 감사의 구조적 한계와, 감사가 강제한다고 적힌 조항 — 낮음

- **내용:**
  - 사양은 원시 프레임 금지(`QUANTGEN_MACRO_INTEGRATION.md:1106`)와 맥락 격리(`:1672`)를 감사가 강제한다고 적습니다. `RawFrameRead`는 운영에서 도달하지 않고(1.4), 감사는 context 입력을 건너뜁니다(`core/ficc/lag_audit.py:114-115`). 격리는 `context_log`의 런타임 가드와 정적 검사(T-CTX-01)가 맡습니다(`core/ficc/context_log.py:71-72`, `:95-103`, 독자 1 인용).
  - 날짜를 바꾸고 도장도 맞춘 값은 감사가 잡지 못합니다(3.4). T-LAG-02의 vt 조항은 이동한 저장소가 `vt`를 바꾸는지만 확인하고, 감사는 따로 만든 행에만 돌립니다(`tests/macro_m2_risk.py:631-656`). 이 부류는 R-34 타이밍 프로필이 맡아야 하지만 실제 양성 대조군은 미실행입니다(LA-02).
  - 위치 이동 linter는 런타임 헬퍼만 있습니다. 운영 호출도 정적 검사도 없습니다(3.2).
  - 실시간 호가, `AS_POSTED`, 미등록 입력은 `pit_value`가 이미 보장한 검사 1·2만 받습니다. 독자 1 P3: 결정보다 사흘 뒤 `obs_date`에 도장이 이른 호가가 위반 없이 통과.
- **기존 ID:** T-LAG-02, T-CTX-01, §10 DO-NOT-BUILD 19번.
- **권고:** 사양의 두 문장을 "pit_value 전용 접근과 T-CTX-01이 강제한다"로 고칠지 소유자가 정합니다. 호가 입력에는 `obs_date <= 결정 세션`과 `obs_utc <= available_at_utc <= decision_utc` 검사를 더하고 미등록 ID를 거부하는 것을 제안합니다. 월간·간격 시계열의 위치 이동 정적 검사는 선택 사항입니다.

### LA-24 PCA fly와 kimchi 예측 검정이 H.15·H.10 자료를 게시일이 아니라 관측일에 씀 — 낮음

- **내용:** `butterfly_signal`은 관측일 t의 FRED DGS 곡선으로 진입하고 손익은 t→t+1부터입니다(`core/ficc/curve_models.py:183-213`). T-H15-01 기준으로 DGS(D)는 다음 연준 영업일 16:15 ET에 가용하므로 D+2 미국 종가부터 쓸 수 있습니다(`QUANTGEN_MACRO_INTEGRATION.md:1299`, 독자 3 인용). `kimchi_premium`은 DEXKOUS를 나이 제한 없이 날짜로 앞채움합니다. 과거 구간에서 d의 프리미엄과 z는 H.10이 최대 1주 뒤 게시하는 d의 정오 환율을 씁니다(`core/crypto/analytics.py:76-92`). 사양의 타이밍 분류로는 COMPLIANT가 아니라 VALUE입니다. 카드 S_B2는 REVISE, M_C1은 REVISE(감시 전용)입니다(독자 3 인용). 크기는 UNVERIFIED입니다.
- **기존 ID:** ML #74(전체 표본 ADF·반감기), M3-N02, V01-01, DF-06, ML #132. 과거 구간 타이밍은 어디에도 없습니다.
- **권고(제안):** 두 카드의 타이밍 라벨을 VALUE로 적거나, 엄격한 H.15 2세션 지연·H.10 게시일(또는 ECOS 15:30 고시)로 다시 계산합니다.

### LA-25 카드 게이트가 전체 표본 기준값을 씀 — 낮음

- **내용:** `funding_carry`는 전체 표본의 `np.quantile`로 상·하위 분위를 정합니다(`core/crypto/analytics.py:137`, `:169`). 저장된 M_C4_funding PASS는 이 사건 연구와 폐기된 IID bootstrap에 기댑니다. 현재 코드는 `bootstrap_p=NaN`을 내므로 다시 돌리면 REVISE가 될 것으로 봅니다(코드 추론, 미실행). fly, kimchi, ETH/BTC 카드도 전체 표본 ADF·반감기로 판정합니다(`docs/asset_expansion_study.py:484`, `:539`, `:560-561`, `:578`). 가중치에 미래 정보가 들어가는 것은 아니고, 판정 단계의 표본 내 선택입니다.
- **기존 ID:** ML #136, NEW-M6-02(`SECTION10_QUEUE_2026-10-30.json:583`, PARTIAL_IMPLEMENTED), ML #74.
- **권고:** 저장된 M_C4 PASS를 유지할지는 소유자가 정합니다. 게이트를 유지한다면 분위 경계는 확장 창으로, ADF·반감기는 표본외로 계산합니다. 관계: 기존 항목입니다. ⑨-3b(R3 비교 보고서)에서 함께 볼 수 있습니다.

### LA-26 forward record 연결과 dry run 시계의 잠재 문제 — 낮음

- **내용:** `ForwardRecord.decision_row`와 R-25 강등 조건은 `lag_audit_violation`을 받습니다(`core/quant/forward.py:47`, `:510-535`, `:637-649`). 운영 코드에는 forward 결정 행을 쓰는 곳이 없습니다(테스트만, `tests/macro_m8_forward.py:409`, 독자 1 grep). 그래서 `macro.lag_audit` 결과가 forward record에 닿지 않습니다. dry run의 `DryRunClocks`는 BLS·BEA 월간 시계열의 발표 시각을 관측일 08:30 ET로 돌려줍니다. 약 한 달 이릅니다(`core/skills/macro_daily.py:15-18`, `:86-90`, `:1285-1343`, 독자 1 인용). dry run 감사도 같은 stub을 쓰므로 잡지 못합니다. 지금 `DRY_RUN_CACHE`에 BLS·BEA 시계열은 없습니다.
- **기존 ID:** 없음.
- **권고(제안):** forward record가 시작될 때 `macro_state.lag_audit` 위반을 결정 행의 `lag_audit_violation`에 연결합니다. dry run stub은 발표 달력 시계열을 거부하거나 `None` 시각을 주게 합니다.

### LA-27 승인(admissions) 계산이 재생·백테스트에서 시점 기준이 아님 — 낮음

- **내용:** `compute_admissions`는 현재 카드와 판정 행을 읽고 `decision_utc`는 잠금 판단에만 씁니다(`core/skills/macro_daily.py:385-398`). S9 기록이 일부러 열어 둔 항목입니다(`research_notes/QUANTGEN v2 integration map/sprint_logs/S9.md:181`, 독자 4 인용). 지금은 UNVERSIONED라 승인되는 카드가 없으므로 영향이 없습니다.
- **기존 ID:** S9 열린 검토 항목.
- **권고:** 열린 PIT 예외로 유지하고, 첫 정식 카드가 승인되기 전에 고칩니다. 관계: ⑨-5의 전제입니다.

### LA-28 증거 품질의 공백 — 낮음

- **내용:**
  - unittest 모듈의 PIT 검사 6건(미래 가격·날짜·틱, OOS embargo 정렬)은 결과 파일에 행이 없습니다. Linux 증거는 그룹 단위 "OK"뿐이고 실행 트리 커밋이 없습니다(`runs/ci_2.log`, `ci_7.log`, `ci_9.log`, `ci_groups.txt`, 독자 4 인용).
  - `walk_forward`의 OOS 오프셋과 embargo를 단언하는 검사가 없습니다(`tests/expansion_acceptance.py:276-277`는 게이트 판정만 확인). "embargo 21에서 누출 없음"은 심사자의 코드 읽기 결론입니다(`docs/superpowers/specs/2026-10-26-nautilus-review/round1_claude_quant.md:360-363`, 독자 4 인용).
- **기존 ID:** 없음.
- **권고(제안):** 인용할 때 해당 모듈을 알려진 커밋에서 `-v`로 다시 돌리거나 '그룹 단위 증거'로 표시합니다. 밀폐형 `walk_forward` embargo 검사를 더합니다.

### LA-29 연구 경로의 기타 시점 관찰 — 낮음

| 관찰 | 근거 | 기존 ID | 권고(제안) |
|---|---|---|---|
| 연구 로더와 Strategy Lab이 실행 중인 마지막 봉을 빼지 않음. 마지막 손익일에만 들어가므로 결정 누출은 아님. 저장 카드의 캐시가 실행 중 봉으로 끝나는지는 UNVERIFIED | `docs/asset_expansion_study.py:68-79`, `core/quant/history.py:65-68`, `core/research/strategy_workflow.py:84-85` | DF-03(P2, PT-03·PT-14) | `core/ficc/data.py`의 `_running_bar`처럼 마지막 행을 표시하고 Lab에 `History.status` 표시 |
| Nautilus 브리지가 SPY 봉을 연중 21:00 UTC로 도장. EDT에는 NYSE 종가가 20:00Z. 단일 종목이라 결합 오류는 없음 | 연구 브랜치 `0bc9595:tools/nautilus/runner.py:629-634` | 없음 | `close_print_bound_utc`로 도장하거나 고정 도장을 문서화 |
| 사양 10.4의 파일럿 구간 열람 이력에 SPY·BTC를 읽은 다른 카드(S_E2, S_E3, S_V1, D_Q, D_C2)가 빠짐. 두 파일럿은 이미 비확증으로 표시됨 | `docs/asset_expansion_study.py:726`, `:728`, `:737`, `:742-749` | 없음 | 사양 10.4와 실행 기록에 행 추가. 관계: ⑥-1, ⑥-2 전 |
| `paper_live` 라이브 진입이 결정에 쓴 마지막 호가(최대 25분, KRX 30분)로 체결됨. 비홀드아웃 재생은 나중에 적합한 sigma를 씀(자기 공개) | `paper_live/engine.py:466-473`, `:511-541`, `paper_live/config.py:117`, `:241`, `paper_live/replay.py:7-9` | 없음 | 비홀드아웃 재생 통계를 표본 내로 표시. 다음 관측 호가 체결 민감도 추가 |
| 유니버스와 페어를 오늘의 종목으로 고름(생존 편향). 코드 수준 누출은 아님 | `docs/asset_expansion_study.py:243-246`, `core/quant/tf_books.py:4-6` | ML #27 | 카드에 생존·선택 라벨 표시 |

- 제외: `walk_forward`가 원점에서 설정 전환 비용을 매기지 않는 문제(N4)는 비용 회계이고 시점 문제가 아니므로 이 보고서에서 다루지 않습니다(`core/quant/validate.py:375`, `SECTION10_QUEUE_2026-10-30.json:174`).

### 7.1 발견 사항 집계

| 심각도 | 건수 | ID |
|---|---|---|
| 높음 | 2 | LA-01, LA-02 |
| 중간 | 12 | LA-03 ~ LA-14 |
| 낮음 | 15 | LA-15 ~ LA-29 |

- 기존 ID로 이미 관리되는 것: LA-04·LA-19(§10 모델 110), LA-11(DF-04), LA-20(§10 모델 153), LA-21(§10 모델 104), LA-25(ML #136, NEW-M6-02), LA-29의 첫 행(DF-03), LA-14(D-04, D-05), LA-27(S9).
- 새 작업 제안은 이 보고서에서 승인되지 않습니다. 순서와 범위는 소유자가 정합니다.

## 8. 확인하지 못한 것 (UNVERIFIED)

1. 파이프라인 전체 실행. `macro_daily`의 `pit_snapshot`, `data_ok`, `macro.lag_audit`, `hedge_state`를 끝까지 돌리지 않았습니다(`scipy` 부재). LA-01의 결과 1은 레지스트리 재현으로, 결과 2는 코드 읽기로만 확인했습니다.
2. 서명된 실제 달력 위의 `CalendarClocks`. 독자 1의 P5는 `scipy` 부재로 실패했습니다. DE·GB 동작은 코드와 stub, 독자 2의 mvenv 스니펫으로만 확인했습니다.
3. Linux I-01 dry run FAIL의 원인(LA-09). 보호 캐시를 열지 않았습니다.
4. Linux 실행 트리(`fullrun`, `prep`)의 커밋. 로그에 없습니다.
5. 운영자 PC의 실제 PIT 저장소와 캐시. 파생, DE, GB 행이 어디든 있는지 보지 않았습니다.
6. `data.us10y.dgs10_strict_lag_bdays=2`가 H.15 발표 시각 규칙과 모든 KR·US 결정에서 같은지.
7. TASK-M1-11의 "시가 = 전일 종가 표시" 조항의 위치. 찾지 못했습니다.
8. 서명 달력 행을 KRX, NYSE, Fed, SIFMA 공식 출처와 대조하지 않았습니다.
9. 연구 경로 결함의 크기: S_V1 VIX 타이밍(LA-10), DF-04 실제 게시 지연(LA-11), H.15·H.10 타이밍(LA-24), M_C4 재실행 판정(LA-25), `paper_live` 체결 지연. 연구를 돌리지 않았습니다.
10. Yahoo 종가 시각(`^VIX`, `=X` 환율, `=F` 선물, BTC-USD 일 경계)과 Upbit `candle_date_time_utc` 의미를 공급사 문서와 대조하지 않았습니다.
11. D-05의 `kis_client` `as_of`가 `core/quant/history.py`, `core/research/watchlist.py` 경로에서 결정에 쓰이는지.
12. 지연된 발표가 운영 시계에서 실제로 어떤 판정을 낳는지(LA-22).
13. 검토하지 않은 모듈: `core/quant/history.py` 내부, techfund(`tf_books`, `tf_screens`, `techfund_study`), grokteam, `quant_lab_grading`, `drift_study`, `vol_backtest`, `bounded_innovation_sweep`, `costed.py`, `card_lines.py`, Strategy Lab 외 UI 화면의 타이밍 라벨, Nautilus `parity.py`·`register_e1.py`·`launch.py`의 세부.
14. 수정 주가가 비율 기반 규칙에 누출을 만들지 않는다는 추론(5절)의 수치 확인.
15. 핸드오프 원장은 로컬 원격 참조(`origin/handoff`)로만 읽었습니다. 원격의 최신 상태와 다를 수 있습니다.
16. 연구 브랜치에만 있는 문서(`KNOWN_ERRORS_REGISTER_2026-10-28.md`, `MODEL_LIMITS_REGISTER_2026-10-28.md`, 감사 보고서)는 `origin/claude/bold-davinci-aipgwi@0bc9595`에서 읽은 독자 3의 인용입니다. `main`에는 없습니다.

## 9. 근거 파일 목록

경로는 저장소 기준입니다. 별도 표시가 없으면 `main` `bb35b3b`입니다.

**감사 대상 코드**
- `core/ficc/lag_audit.py`
- `core/ficc/pit.py`
- `core/ficc/contracts.py`
- `core/ficc/data.py`
- `core/ficc/macro_artifacts.py`
- `core/ficc/context_log.py`
- `core/ficc/macro.py`
- `core/skills/macro_daily.py`
- `core/skills/pipeline.py`
- `core/engine/books.py`
- `core/calendars/clocks.py`, `core/calendars/store.py`, `core/calendars/publication.py`, `core/calendars/adapter.py`, `core/calendars/regime.py`
- `core/calendars/data/MANIFEST.yaml`, `core/calendars/data/holidays_KRX.yaml`, `core/calendars/data/kr_sessions.yaml`, `core/calendars/data/kr_regime_tags.yaml`
- `data/macro/series_registry.yaml`, `data/macro/rules_v2.0.0.json`
- `data/krx/kis_client.py`, `config.py`
- `core/quant/risk_layer.py`, `core/quant/cardp.py`, `core/quant/forward.py`, `core/quant/sleeves.py`, `core/quant/forward_sim.py`, `core/quant/optimize.py`, `core/quant/forecast_eval.py`
- `docs/macro_overlay_study.py`
- `ui/macro_state_panel.py`

**매크로 밖 코드**
- `core/quant/strategies.py`, `core/quant/validate.py`, `core/quant/backtest.py`, `core/quant/history.py`, `core/quant/tf_books.py`
- `core/research/strategy_workflow.py`
- `docs/asset_expansion_study.py`
- `core/ficc/fx.py`, `core/ficc/fx_styles.py`, `core/ficc/curve_models.py`, `core/ficc/vol_products.py`, `core/ficc/bonds.py`, `core/ficc/curves.py`
- `core/crypto/analytics.py`, `core/crypto/funding_diagnostic.py`
- `paper_live/engine.py`, `paper_live/replay.py`, `paper_live/config.py`
- 연구 브랜치 `origin/claude/bold-davinci-aipgwi@0bc9595`: `tools/nautilus/sandbox.py`, `tools/nautilus/runner.py`

**사양과 계획**
- `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`(§3.9 `:1208-1217`, R-01 `:1485-1495`, R-19 `:1813`, R-20 `:1983`, `:1106`, `:1672`, `:3397-3399`)
- `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_V2_CLAUDE_CODE_TASKS.md`(`:15`, `:256-258`, TASK-M1-01~M1-23 `:260-580`)
- `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md`, `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md`, `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`

**검사와 결과**
- `tests/macro_m1_pit.py`, `tests/macro_m1_calendars.py`, `tests/macro_m1_integration.py`, `tests/macro_m1_books.py`, `tests/macro_m1_fixtures.py`, `tests/macro_m2_risk.py`, `tests/macro_m3_estimators.py`, `tests/macro_m5_books.py`, `tests/macro_m7_cardp.py`, `tests/macro_m8_pipeline.py`, `tests/macro_m8_forward.py`, `tests/macro_tf_gov.py`, `tests/expansion_acceptance.py`, `tests/quant_acceptance.py`, `tests/run_all.py`, `tests/notrun.py`, `tests/macro_registry.csv`
- `qa/acceptance_results.json`(2026-10-23 Windows, 커밋 `ac86705`)
- 스크래치 `runs/full.json`, `runs/macro2.json`, `runs/full.log`, `runs/macro2.log`, `runs/ci_groups.txt`, `runs/ci_2.log`, `runs/ci_7.log`, `runs/ci_9.log`(2026-11-04 Linux; 저장소 밖)
- 스크래치 재현 스크립트: `la_tools/keys.py`, `la_tools/probe.py`, `la_tools/reg_table.py`, `la_probe/slack.py`(저장소 밖)

**기존 기록**
- `docs/product/SECTION10_QUEUE_2026-10-30.json`, `docs/product/DATA_READINESS_2026-10-29.json`, `docs/product/DATA_ACQUISITION_2026-10-29.md`
- `docs/audit/2026-10-27/00_request.md`, `docs/audit/2026-10-27/01_calendar_T-CAL-02.md`, `docs/audit/2026-10-27/12_release_calendar.md`, `docs/audit/2026-10-27/16_signature_batch5.md`
- `research_notes/QUANTGEN v2 integration map/council_reports.md`, `code_data_layer.md`, `sprint_logs/S2.md`, `S3.md`, `S5.md`, `S9.md`
- 연구 브랜치 `0bc9595`: `docs/nautilus_bridge/KNOWN_ERRORS_REGISTER_2026-10-28.md`, `docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md`
- 핸드오프 원장 `origin/handoff:LEDGER.md`(⑨-1 행 없음 확인만)
