# 새 모델 채택 기준 초안 (⑨-4)

- 상태: **초안, 소유자 검토 대기.** 이 문서의 PROPOSAL은 소유자가 승인하기 전에는 효력이 없습니다.
- **소유자 결정 반영 2026-11-04:** 9절의 결정 1~22에 소유자 답(결정표 M-1~M-22)을 원문으로 적었습니다. 승인된 범위는 각 항목 아래에 있습니다. 결정 12와 21에는 메모가 있습니다.
- 작성: Claude (Step 7A 세션), 2026-11-04. 기준 커밋 `bb35b3b`(`main`, 병합 동결 시작점). 브랜치 `claude/model-adoption-criteria-20261104`. 커밋과 push는 소유자가 합니다.
- 개정: 같은 날 검토 의견 21건을 코드와 대조해 반영했습니다. 무엇을 바꿨는지는 10.5에 있습니다.
- 로드맵 항목: ⑨-4 3-2 새 모델 채택 기준. 담당은 Claude 초안 → 사용자 승인, 선행은 ②-5입니다(`docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:138`, `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md:169`). ②-5는 2026-10-28에 승인됐습니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:417`). ⑨-4는 인계 장부(`origin/handoff`의 `LEDGER.md`, `9c0d782`)에 없습니다.
- 짝 문서: 모델 한계 대장(②-3), 알려진 오류 통합 목록(②-4), R3 실행 레지스트리 설계(②-6). 세 문서는 연구 브랜치에 있고 `main`에는 아직 없습니다.
- 소유자가 이 작업과 함께 지정한 작업: ⑤-2 파일럿 공급사 대조, ⑧-1 H2 판독. 이 문서는 두 작업을 하지 않고, 관계만 적습니다(4.4, 8.3).

## 0. 읽는 법

### 0.1 표기

| 표기 | 뜻 |
|---|---|
| `path:line` | `bb35b3b`의 파일과 줄 |
| `research:path:line` | 연구 브랜치 `claude/amazing-gauss-tdiguu`의 `0bc9595`(이 클론의 `up/research`)에 있는 파일과 줄 |
| 기존 | 코드나 설정에 있는 값을 바꾸지 않고 옮긴 것 |
| 기존 규칙 | 이미 승인된 규칙(소유자 판정, 로드맵 규칙)을 이 기준에 그대로 적용한 것 |
| PROPOSAL | Claude의 제안값. 9절의 소유자 결정 번호를 붙였습니다 |
| UNVERIFIED | 이 세션에서 확인하지 못한 것 |
| 이번 측정 | 이 문서를 쓰며 합성 데이터로만 돌린 값(10.3) |

- `core/quant/validate.py`, `gate_stats.py`, `gate_ledger.py`, `forecast_eval.py`는 모델 한계 대장의 기준 커밋 `d865c7f` 뒤로 바뀌지 않았습니다(`git diff --stat d865c7f bb35b3b -- core/quant`에 없음). 그래서 대장의 줄 번호가 이 문서와 같습니다.
- `ui/strategy_lab_page.py`는 바뀌었습니다. Strategy Lab의 실행 코드는 지금 `core/research/strategy_workflow.py`에 있습니다. R3 설계가 인용한 `ui/strategy_lab_page.py`의 줄 번호는 이 커밋과 맞지 않습니다.

### 0.2 요약

- 새 모델은 기존 게이트의 PASS만으로 채택하지 않습니다. PASS는 필요조건입니다.
- 채택은 사전 등록한 비교 검정에서 기준전략을 확실히 이길 때만 합니다. 현직을 바꾸는 교체라면 현직도 확실히 이겨야 합니다. 경계 결과는 채택하지 않습니다.
- 검정은 저장소에 이미 있는 함수로 합니다. 예외는 둘이고, 둘 다 새 코드라 소유자 승인이 필요합니다: R-3의 정확한 LR(한 줄 계산, 기준 계산은 `tools/status/section10_probes.py:27-31`)과 60/40 기준전략(구현 없음).
  - 예측: `forecast_eval.dm_test`(HAC, HLN 보정), `forecast_eval.mcs`(T_max, 90% 집합), 중첩 모형은 `forecast_eval.cw_test`.
  - 전략: `validate.score_strategy` 게이트(walk-forward 756/126, DSR, PBO, 2배 비용, 벤치마크 검정), 현직과 기준전략 대비 짝지은 ΔSharpe(`gate_stats.lw_studentized_boot`).
  - 리스크: `validate.score_distribution`(Kupiec, Christoffersen, 신호등, 커버리지, PIT), `lab.m9_gate`, `forecast_eval.b5`.
- 변동성 추정기에는 이미 채택 기준이 있습니다(R-30 단계 게이트, 4.1.1). 이 초안은 그 구조를 다른 모델로 넓힙니다.
- `GATE`, 저장 카드 34개의 판정, 동결 연구, 게이트 패키지 소스, Nautilus `code_sha256`에 드는 파일은 바꾸지 않습니다(1.3, 7절).
- 시행 수 N의 정의와 시행 분류는 R3(⑨-3a~⑨-3d)를 따릅니다. 자료 원천 변경도 R3 설계 4.2 9a·9b행 그대로 셉니다(4.4). 이 초안은 R3를 다시 설계하지 않습니다.
- 2027-01-01부터 잠금 홀드아웃입니다(⑧-2). 결정 14 전에는 채택 평가의 표본이 2026-12-31 안에서 끝나야 합니다. 그 뒤 자료가 필요한 모의(L2), 실거래 재평가(L3), 경계 재평가는 결정 14 전에 시작하지 않습니다(3.3, 8절).
- 실데이터 게이트 실행, 원장 등록, 공급사 대조는 소유자 PC에서 합니다. Claude는 요약 출력만 받습니다(3.5).
- 이번 측정에서 나온 사실 셋이 규칙에 들어갔습니다.
  - 상관이 낮은 두 전략은 5년 표본으로 연 Sharpe 차이 1.33 미만을 80% 검정력으로 구분하지 못합니다(5.3).
  - 연 Sharpe 0.5 전략은 5년 표본에서 게이트 DSR이 0.868이라 REJECT입니다. INSUFFICIENT_DATA가 아닙니다(5.2).
  - h > 1 예측의 DM 검정은 F-2 판정 수준(단측 0.10)에서 실제로 0.115~0.135 비율로 기각합니다. 원점을 5,000개로 늘려도 줄지 않습니다. 단측 0.05로 낮추면 0.063~0.079입니다(5.4).
- 소유자 결정 22건을 9절에 모았습니다.

## 1. 목적과 범위

### 1.1 요청 원문

로드맵 검토의 수용 행(원문 그대로):

| # | 로드맵 내용 | 판정 | 근거 | 반영 방법 | 위치 |
|---|---|---|---|---|---|
| C2 | 새 모델은 확실히 나을 때만 추가 | 수용 + 구체화 | "확실히"의 기준이 없습니다. `forecast_eval`과 `gate_stats`에 DM, MCS, SPA 검정이 있습니다. | 채택 기준을 **사전 등록한 비교 검정**으로 정합니다. 예측은 DM/MCS, 전략은 paired bootstrap ΔSharpe와 DSR이며, trial 수를 반영합니다. | `ROADMAP_REVIEW_2026-10-27.md:48` |
| E1 | QUANTGEN을 쓰지 않는 단순 기준전략과 비교, 목표 수익 달성만으로는 성공 아님 | 수용 (강하게 일치) | 게이트의 벤치마크 검정(p ≤ 0.10)과 일치합니다. | 패밀리마다 **기준전략을 사전 등록**합니다(buy-and-hold, 60/40, 동일가중, SMA-200). | `:54` |
| E2 | 백테스트 → 모의매매 → 소규모 실거래 | 조건부 수용 | QUANTGEN의 paper_live H2가 진행 중입니다(홀드아웃 11-03 종료, 판독 약 12-19). 실거래는 TRADEGEN이 한국법 범위에서 합니다. | 단계를 올리는 **승격 기준**을 미리 정합니다: 최소 표본, 손실 한도, kill switch. | `:55` |

로드맵 항목: "⑨-4 | **새 모델 채택 기준** | Claude 초안 → 사용자 승인 | ②-5"(`REMAINING_WORK_2026-10-27.md:138`).

정정 하나. C2 행은 SPA가 `gate_stats`에 있다고 적었습니다. SPA는 `core/quant/tf_gov.py:257-291`(테크펀드 GOV-2)에 있습니다. `gate_stats`에는 LW ΔSR, PBO, 검정력, BY q, Holm이 있습니다(`core/quant/gate_stats.py:123-137`).

### 1.2 이 초안이 하는 일

1. "새 모델"의 범위를 정합니다(2절).
2. 표본외 자료를 보기 전에 고정할 항목과 실행 주체를 정합니다(3절).
3. 모델 유형별 채택 규칙을 정합니다(4절). 기존 임계값은 그대로 옮기고, 새 값은 PROPOSAL로 둡니다.
4. 최소 증거(5절), 실패와 경계 처리(6절), 기존 게이트와의 관계(7절), 승격 단계(8절)를 적습니다.
5. 소유자가 정할 것을 번호로 모읍니다(9절).

### 1.3 이 초안이 하지 않는 일

- 코드와 설정을 바꾸지 않습니다. 대상은 `GATE`(`core/quant/validate.py:53-74`), `_decide_strategy`(`:536-622`), `score_distribution`(`:741-796`), Quant Lab M9 기준(`core/quant/lab.py:67-69`), R-30 설정(`data/macro/rules_v2.0.0.json:749-838`), CARD-P 상수(`core/quant/cardp.py:54-72`)입니다.
- `HARNESS_SOURCES`(`core/quant/gate_package.py:36-38`)의 파일을 고치지 않습니다. 고치면 게이트 패키지 변경입니다.
- Nautilus 브리지의 `code_sha256`에 드는 파일을 고치지 않습니다. 그 파일은 `tools/nautilus/**/*.py`, `tools/nautilus/golden/*.json`, `requirements-nautilus.txt`, `HARNESS_SOURCES`의 파일, `docs/asset_expansion_study.py`, `config.py`입니다. 하나라도 고치면 새 `owner_confirmed`가 필요합니다(`research:docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:1185-1191`). Step 7A 중이므로 이 초안의 제안은 이 파일들에서 구현하지 않습니다(7절, 결정 21).
- 저장 카드 34개(`docs/asset_expansion/cards/`)를 다시 판정하지 않습니다. R3 판정에 따라 ⑨-3d 전까지 기존 기준을 유지합니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:167-185`).
- R3 실행 레지스트리를 다시 설계하지 않습니다. 시행 분류와 N의 정의는 R3 설계(`research:docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`, 이하 "R3 설계")가 원본입니다.
- 동결 연구(paper_live H2, GROKTEAM forward look)를 열거나 실행하지 않습니다. H2는 등록 형식만 참고합니다.
- 실데이터, 원장(`~/.nextgen`), 보호 캐시 4개, `.env`, `paper_live/out*/`, `grokteam/out/book/`을 열지 않았습니다.
- ⑪-1과 겹치는 부분이 있습니다. 로드맵 검토는 ⑪-1 TRADEGEN 연동 브리프의 범위에도 "기준전략 사전 등록, 승격 기준"을 넣었습니다(`ROADMAP_REVIEW_2026-10-27.md:173`). 인계 장부의 ⑪-1 기록은 ⑪-1/a(읽기 전용 export 계약)뿐이고(`9c0d782`의 `LEDGER.md:57`), 브리프 v1은 두 주제를 다루지 않습니다(`docs/product/TRADEGEN_READ_ONLY_BRIEF_2026-10-29.md:1-20`). PROPOSAL: 이 문서의 2.3절과 8절을 기준전략과 승격 기준의 단일 출처로 하고, 남은 ⑪-1 작업은 이를 인용합니다(결정 22).

## 2. "새 모델"의 범위

### 2.1 정의

모델 한계 대장의 정의를 씁니다. 숫자를 만들어 화면, 저장 카드, 원장, 판정으로 내보내는 계산 단위가 모델입니다(`research:docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md:19-27`).

이 기준에서 "새 모델"은 셋 중 하나입니다.
- 지금 없는 계산 단위를 더해 판정, 카드, 북, 주문 후보에 쓰려는 것(추가).
- 현직 모델을 다른 모델로 바꾸는 것(교체).
- 이미 있는 계열에 새 규칙이나 새 시장을 더하는 것(추가).

새 모델이 아닌 것:
- 등록된 격자 안에서 파라미터를 바꾼 것. 같은 계열의 시행입니다. 원장 행이 늘 뿐입니다(`core/quant/gate_ledger.py:379-386`; R3 설계 4.2 5행, `:409`).
- 동작이 같은 리팩터. R3 설계 4.2 8a행입니다(행동 지문 일치).
- 같은 데이터 요청의 재측정. R3 설계 4.2 9a행입니다(`:418`).

### 2.2 유형

| 유형 | 무엇 | 저장소 예 | 지금 쓰는 비교 장치 | 규칙 |
|---|---|---|---|---|
| F 예측 | 분산, 수익률, 분위, 금리의 점 예측이나 분포 예측 | R-30 추정기 7종 `sma20`~`comb`(`core/quant/vol_estimators.py:34`); DNS 곡선 예측 카드 `M_B1_dns`; LETF drag 예측 카드 `M_E4_letf_drag` | `forecast_eval.dm_test`(`core/quant/forecast_eval.py:147-156`), `mcs`(`:203-243`), `cw_test`(`:159-165`), `gw_test`(`:168-189`); R-30 단계 게이트(`:523-582`, `:685-721`) | 4.1 |
| S 전략 | 자료로 비중을 정하는 거래 규칙과 그 격자 | Lab 7계열(`core/research/strategy_workflow.py:17-29`); 스터디 카드 `S_*`; 매크로 규칙 R-03, R-06, R-28, R-31(`core/quant/gate_ledger.py:79`) | `validate.score_strategy`(`core/quant/validate.py:492-533`); `gate_stats` ΔSR; `gate_ledger.step3`(`core/quant/gate_ledger.py:748-813`); 테크펀드 SPA(`core/quant/tf_gov.py:257-333`) | 4.2 |
| R 리스크·분포 | VaR, ES, 팬, 예측 분포 | 카드 `D_Q_*`, `D_C2_*`(GARCH-t, GJR, skew-t); Quant Lab FHS·GJR-EVT 포락선(`core/quant/lab.py`); R-06 σ의 B5 | `validate.score_distribution`(`core/quant/validate.py:741-796`); `lab.m9_gate`(`core/quant/lab.py:617-650`); `forecast_eval.b5`(`core/quant/forecast_eval.py:354-400`), `stage1`(`:523-551`) | 4.3 |
| D 데이터 원천·처리 | 공급사, 가격 조정, 정제, 달력 | C3 카드의 Yahoo·Upbit·Binance 차이(CRY-1); ⑤-2 공급사 대조 | R3 설계 4.2 9a·9b행(`:418-419`); ⑤-2(미완료) | 4.4 |
| P 가격 공식 | 채권, 스왑, 옵션의 닫힌식·수치 가격기 | `core/ficc/` | 독립 구현 대조(대장 1.4 "독립 검증됨", `research:...MODEL_LIMITS_REGISTER_2026-10-28.md:61`) | 4.5. 통계 비교 대상 아님 |
| G 판정 장치·비용표 | `GATE`, 비용표, DSR의 N 정의 | K-f 비용 분류, R3 ⑨-3d | 게이트 패키지 버전(`core/quant/gate_package.py:241-255`), 소유자 판정 | 범위 밖(7절) |

- 이 기준을 F, S, R, D에 적용하고 P, G를 빼는 것은 PROPOSAL입니다(결정 1).

### 2.3 현직, 도전자, 기준전략

- **현직(incumbent):** 지금 그 역할에 쓰는 모델입니다. 없으면 기준전략이 현직 역할을 합니다.
- **도전자(challenger):** 새 모델입니다.
- **기준전략(baseline):** QUANTGEN의 판단을 쓰지 않는 단순 규칙입니다(E1).

지금 계열별로 쓰는 비교 대상과 PROPOSAL 기준전략(결정 4):

| 계열 | 지금 비교 대상 | 근거 | PROPOSAL 기준전략 |
|---|---|---|---|
| trend_switch (E1) | 동일가중, 매일 리밸런싱 | `core/research/strategy_workflow.py:99`; `docs/asset_expansion_study.py:275` | 동일가중, SMA-200(아래 정의). US 묶음은 60/40 추가 |
| vol_target (E2) | 첫 자산 buy-and-hold | `docs/asset_expansion_study.py:286` | 같은 자산 buy-and-hold |
| risk_parity (E3) | 동일가중 | `:296` | 동일가중. US 묶음은 60/40 추가 |
| xs_momentum (E5) | 동일가중 | `:306` | 동일가중 |
| tsmom (B3) | 동일가중 | `:317` | 동일가중 |
| crypto_trend (C3) | 첫 자산 buy-and-hold | `:334` | buy-and-hold, 변동성 맞춤 롱온리 대조(CRY-1, `docs/techfund_study.py:83`) |
| pairs (E8, S6) | 없음. 롱온리일 때만 동일가중 | `core/research/strategy_workflow.py:99`; `docs/asset_expansion_study.py:355` | 현금. Sharpe 구간이 0을 배제하는지(기존 검사)로 대신함 |
| VIX 롤다운 (V1) | 무조건 VIXY 숏 | `:383` | 그대로 |
| FX 모멘텀 (V3), 달러 캐리 (V4) | G10 캐리 상위 3 지수(`core.ficc.fx.carry_backtest(top_n=3, cost_bps=5.0)`) | `docs/asset_expansion_study.py:425-431` | 그대로 |
| PCA 버터플라이 (B2) | 없음. 게이트를 쓰지 않고 자체 기준(ADF, 적중률, 거래당 손익 > 비용 2배)으로 판정 | `docs/asset_expansion_study.py:478-496` | 현금. 다만 B2는 게이트용 일간 손익 열이 없어 4.2 규칙을 바로 적용할 수 없습니다(구현 없음) |
| 예측(F) | SMA20(`ForecastSpec.benchmark`) | `core/quant/forecast_eval.py:68` | 분산은 SMA20, 금리·수익률은 랜덤워크 또는 과거 평균 |
| 매크로 CARD-P | 같은 평균 노출의 정적 북 S | `core/quant/cardp.py:158`; `data/macro/rules_v2.0.0.json:1573-1574` | 그대로 |

기준전략의 정의(PROPOSAL, 결정 4):
- **SMA-200:** `strategies.trend_switch(rule="sma", lookback=200, step=21)` 하나로 고정합니다(`core/quant/strategies.py:162`). 200은 E1 격자의 lookback(126, 210, 252)에 없는 값이라 도전자 격자의 원소가 아닙니다(`docs/asset_expansion_study.py:274`). 함수 기본값 210(Faber 10개월)은 격자 안에 있어 쓰지 않습니다.
- **60/40:** SPY 60%, TLT 40%입니다. 두 자산은 이미 US 묶음에 있습니다(`docs/asset_expansion_study.py:243`). 21세션마다 리밸런싱하고, 표 비용 `us`(`core/quant/validate.py:78`)와 아래의 같은 현금 관례를 씁니다. **구현 없음:** `core/`, `docs/*.py`, `tools/`(`tools/nautilus/` 제외)에서 "60/40"을 찾으면 결과가 없습니다. `strategies.simulate`에 고정 비중을 넣으면 비용 없는 매일 리밸런싱이 됩니다(`research:...nautilus-bridge-design.md:1716-1717`). 그래서 새 코드가 필요합니다.
- KRX 묶음의 60/40(예: `069500.KS`와 `152380.KS`, `docs/asset_expansion_study.py:244`)은 넣지 않았습니다. 넣을지는 결정 4입니다.
- 새 기준전략 코드는 1.3의 해시 대상 파일 밖 새 모듈에 둡니다. Step 7A.3 커밋과 병합 동결 해제 전에는 만들지 않습니다(결정 21).
- Lab의 비교 대상은 비용과 현금 수익이 없습니다. 전략 쪽은 현금에 연 3%를 받습니다(`core/research/strategy_workflow.py:93`, `:99`; 대장 N3). PROPOSAL: 채택 비교는 두 쪽에 같은 현금 관례를 씁니다(결정 4).

## 3. 사전 등록

### 3.1 원칙

- 표본외 자료를 보기 전에 등록하고, 등록을 담은 git 커밋으로 시점을 고정합니다. 기준점은 `gate_ledger.anchored`가 받는 `git:<sha>`나 `external:<ref>`입니다(`core/quant/gate_ledger.py:114-119`).
- 등록 뒤에 설정(파라미터, 격자, 유니버스, 비용, 자료 선택)을 바꾸면 R3 설계 4.2의 새 시행입니다(5행 `:409`, 9b행 `:419`, 10행 `:420`). 원장 행이 늘고 N에 더합니다.
- 등록 뒤에 가설이나 주장(유형, 비교 대상, 방향)을 바꾸면 계수된 개정이고 새 등록입니다. 개정은 `gate_ledger.bump_revision`으로 남깁니다. 개정은 원장 행이 아니고 N에 더하지 않습니다(`core/quant/gate_ledger.py:818-826`).
- 저장소의 선례가 둘 있습니다.
  - paper_live H2: 가설, 지표, 검정, 표본, 규칙, 고정 대상을 한 번에 적습니다(`paper_live/config.py:179-221`). `verdict.py --freeze`는 내용이 다른 재고정을 거부하고 규칙 코드의 사본을 남깁니다(`paper_live/verdict.py:39-65`).
  - Nautilus 파일럿 등록표: 자료 해시, 구간, 격자, 비용, 가설을 적고, 이미 쓴 자료라 확증이 아니라고 `claim_label`에 밝힙니다(`research:docs/nautilus_bridge/registration/pilot1_E1_spy.json:11`, `:39-40`).

### 3.2 등록 항목

| # | 항목 | 내용 | 기존 장치 | 상태 |
|---|---|---|---|---|
| 1 | 가설 | 한 문장. 방향, 비교 대상, 단위 | `ModelCard.hypothesis`(`core/quant/validate.py:806`); H2 `claim`(`paper_live/config.py:200`) | 기존 |
| 2 | 현직과 기준전략 | 2.3 표에서 고릅니다. 여러 개면 판정 방식(모두 이김 또는 가장 강한 하나)도 적습니다 | `ForecastSpec.benchmark`(`core/quant/forecast_eval.py:68`); `score_strategy`의 `bench_daily` | PROPOSAL(결정 4) |
| 3 | 지표와 손실 | 예측은 손실 하나(예: QLIKE). 전략은 비용 차감 OOS Sharpe. 리스크는 위반열과 PIT | `ForecastSpec.loss = "qlike"`(`:67`) | 기존 |
| 4 | 검정과 유의수준 | 4절의 규칙에서 고릅니다. 단측·양측과 α를 적습니다 | 단측 α 0.10 관례(`paper_live/config.py:182-183`, `:187`; `core/quant/gate_stats.py:128`; `GATE["bench_p_max"]`, `core/quant/validate.py:71`) | 기존 관례 |
| 5 | 표본 | 자료 원천과 해시, 시작과 끝, OOS 시작, 원점 간격, 보유기간(embargo). 표본은 정확히 정의하고, 빠진 날이 있으면 미완으로 둡니다. 표본을 옮기지 않습니다. 결정 14 전에는 끝이 2026-12-31 이전이어야 합니다(3.3). 해시는 소유자 PC에서 냅니다(3.5) | H2 `sample`(`paper_live/config.py:205-206`); 등록표 `prices_md5`(`pilot1_E1_spy.json:11`); `data/macro/rules_v2.0.0.json:2063` `locked_holdout_start` | 기존 형식. 날짜 제한은 기존 규칙(⑧-2) |
| 6 | 비용 | 표 요율과 2배 스트레스. 표보다 낮은 비용은 판정 보류 | `COST_BP_PER_SIDE`(`core/quant/validate.py:78`); `GATE["cost_stress"]`(`:57`); `core/research/strategy_workflow.py:65-82` | 기존 |
| 7 | 시행 계수 | 계열 ID, 등록 시점의 원장 해시, 이번 격자 크기 G, 원장 N_raw. 원장 등록은 계산 전에 합니다. 등록과 N_raw 읽기는 소유자 PC에서 합니다(3.5) | `_check_header`가 `ledger_hash_at_registration`을 요구(`core/quant/gate_ledger.py:736-746`); `n_raw`(`:333-334`) | 기존(매크로 카드). Lab은 계산 뒤 등록(K-d, `core/research/strategy_workflow.py:97-98`) |
| 8 | 검정력 | 기대 효과와 MDE80. MDE80이 기대 효과보다 크면 INSUFFICIENT_DATA를 예상한다고 적습니다 | `gate_stats.power_line`(`core/quant/gate_stats.py:426-461`), `MDE_FACTOR = 2.1232`(`:144`) | 기존(매크로 카드). 다른 유형은 PROPOSAL(결정 16) |
| 9 | 판정 규칙 | 4절의 해당 규칙과 6절의 결과 처리 | - | PROPOSAL(결정 16) |
| 10 | 확증 여부 | 이미 본 자료인지 적습니다. 확증이면 R3의 네 조건을 채웁니다(3.3) | R3 설계 4.2 7행(`:411`, `:429-438`) | 기존(R3) |
| 11 | 시드와 B | 시드 11, B 2,000 | `GATE["bootstrap_B"]`(`core/quant/validate.py:54`); `gate_stats.SEED_STUDY`, `B_DEFAULT`(`core/quant/gate_stats.py:139-140`) | 기존 |
| 12 | 추가·교체 | 교체면 바꿀 현직의 이름, 추가면 "추가". 결과를 본 뒤 바꾸지 않습니다(4.2.2) | 2.1의 세 정의 | PROPOSAL(결정 19) |

### 3.3 확증과 탐색

- **확증 증거**는 R3의 독립 검증 네 조건을 모두 채운 평가 한 번입니다(R3 설계 `:411`, `:429-438`).
  1. 계열, 설정, 코드 해시, 통과 규칙, 검증 구간을 적은 선언이 기준점 있는 커밋에 있습니다.
  2. 기준점 전에 그 계열의 어떤 실행도 검증 구간을 건드리지 않았습니다.
  3. 그 구간에서 그 설정의 첫 평가입니다.
  4. 결과가 무엇이든 기록합니다.
- **탐색 증거**는 그 밖의 전부입니다. walk-forward OOS도 같은 자료를 앞서 본 적이 있으면 탐색입니다.
- QUANTGEN의 역사 자료는 대부분 이미 쓰였습니다. 예를 들어 파일럿 1의 SPY는 `S_E1_trend_us`에서 같은 격자로 쓰였습니다(`pilot1_E1_spy.json:40`). 그래서 확증 조건을 채우는 자료는 보통 앞으로 쌓이는 자료뿐입니다. 그 양은 edge를 확증하기에 적습니다(5.2, 8.3).
- Lab은 고정 설정을 정한 구간에서 평가하는 기능이 없습니다. 그래서 지금 Lab으로는 확증 평가를 할 수 없습니다(R3 설계 `:440-442`).

**2027-01-01 잠금 홀드아웃 (기존 규칙 ⑧-2).**
- 이 날짜 이후 데이터는 어떤 설계에도 쓰지 않습니다. 모든 묶음에 적용됩니다(`REMAINING_WORK_2026-10-27.md:122`). TRADEGEN 피드백 경로에도 같은 규칙이 있습니다(`ROADMAP_REVIEW_2026-10-27.md:43`, A2 ③).
- 이 기준에서 그 뒤 자료가 필요한 일은 넷입니다.
  1. 2027-01-01이나 그 뒤에 끝나는 L0 표본. R3는 표본이 그 날짜나 그 뒤에 끝나는 실행에 HOLDOUT_TOUCHED를 붙입니다(R3 설계 4.2 16행, `:427`). Lab은 늘 최신 `days` 세션을 읽으므로 2027년부터 실데이터 Lab 실행은 모두 여기에 듭니다(`:440`, `:1648`).
  2. L2 모의 숙성, 그리고 L2 실패 뒤의 재설계(8.1, 8.3).
  3. L3 정기 재평가(8.4).
  4. 경계와 INSUFFICIENT_DATA의 재평가(6.1, 6.2).
- 결정 14 전의 처리(기존 규칙 적용):
  - 채택 평가의 표본(3.2 5번)은 2026-12-31 이전에 끝나야 합니다.
  - HOLDOUT_TOUCHED 실행은 ADOPT할 수 없습니다.
  - 위 2~4는 2026-12-31까지의 세션만 씁니다. 그래서 결정 14 전에는 L2 숙성 252세션을 채울 수 없고, L2와 L3를 시작하지 않습니다.
- 선례가 하나 있습니다. 테크펀드 숙성 시계(GOV-10, 2026-10-01부터 252세션)는 소유자 판정 D-23으로 매크로 홀드아웃 2027-01-01과 별개의 시계입니다(`core/quant/tf_gov.py:65`; `research_notes/QUANTGEN v2 integration map/tf_core_link.md:334`). ⑧-2("모든 묶음에 적용", 2026-10-27) 뒤에도 이 선례가 그대로인지는 확인하지 못했습니다(UNVERIFIED).
- 확증 평가 한 번, 모의 숙성의 시계, 그 뒤 자료에서 본 실패 뒤에 고칠 수 있는 범위는 결정 14입니다.

### 3.4 등록 파일 (PROPOSAL, 결정 15)

- 등록 하나를 JSON 파일 하나로 커밋합니다. 형식은 파일럿 등록표(3.1)와 H2 `HYPOTHESES`를 합친 것입니다. 3.2의 12개 항목을 담습니다.
- 위치 제안: `docs/adoption/registrations/<card_id>.json`.
- R3 레지스트리의 DECLARATION 사건이 구현되면 그 사건이 이 파일을 대신합니다(R3 설계 4.2 7행 조건 1). 이 초안은 그 사건의 형식을 정하지 않습니다.
- 이 기준은 승인 뒤에 등록하는 모델에만 적용합니다. 소급하지 않습니다.

### 3.5 실행 주체 (기존 규칙)

| 일 | 어디서, 누가 | Claude가 받는 것 | 근거 |
|---|---|---|---|
| 등록 파일 작성 | Claude 초안 → 소유자 검토와 커밋 | - | 커밋은 소유자(이 문서 머리말) |
| 자료 해시(3.2 5번), 실데이터 게이트 실행(L0) | 소유자 PC | 판정, 통계, 자료 해시 | `REMAINING_WORK_2026-10-27.md:133`(⑥-1 "사용자: 실제 원장으로 실행 → Claude: 분석과 기록") |
| 원장 등록, N_raw와 원장 해시 읽기(3.2 7번) | 소유자 PC. 공식 원장 기록은 건마다 소유자 승인 | 행 수, 해시, 체인 검사 결과 | `research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:568`, `:318-336`(원장 행 수는 소유자 PC에서 읽어 보고) |
| 공급사 대조(D-1) | 소유자 PC | 일치율과 불일치 날짜만 | `ROADMAP_REVIEW_2026-10-27.md:47`; `REMAINING_WORK_2026-10-27.md:132` |
| Nautilus 기록용 실행(L1) | 소유자 PC. Claude는 of-record 모드를 돌리지 않습니다 | 패리티 검사 결과 | `research:...nautilus-bridge-design.md:1502` |
| 모의 기록(L2) | 소유자 PC | 세션별 요약 | H2와 같은 방식. L2 도구는 아직 없습니다(UNVERIFIED) |
| 합성·밀폐 검사, 분석, 기록 초안 | Claude | - | 10.3 |

- Claude는 가격 파일, 보호 캐시 4개, `~/.nextgen`, `.env`를 열지 않습니다. 실제 SPY의 2004-12-01 이후 행과 실제 BTC 가격을 읽지 않습니다(`research:...nautilus-bridge-design.md:1502`).
- 그래서 L0의 "Claude 분석"은 소유자가 넘긴 요약 출력의 분석입니다. Claude가 실제 가격으로 게이트를 돌리거나 원장을 읽는다는 뜻이 아닙니다.

## 4. 유형별 판정 규칙

### 4.0 공통 규칙 (PROPOSAL, 결정 16; α는 결정 2)

1. 기존 게이트를 먼저 통과합니다. 전략은 `score_strategy` PASS, 분포 카드는 `score_distribution` PASS, Quant Lab 선은 `m9_gate` PASS, R-06 σ 추정기는 Stage 1 통과입니다.
2. 등록한 기준전략을 사전 등록한 비교 검정으로 이깁니다. 교체(3.2 12번)라면 현직도 이깁니다. "이긴다"는 점추정이 등록한 방향이고 단측 p ≤ α(기본 0.10, 결정 2)라는 뜻입니다.
3. 시행 수를 반영합니다. 전략은 DSR(S-2)로 합니다. 예측과 리스크는 평가 전에 등록한 변형 전부를 넣은 MCS 집합과 Holm 보정(F-9, R-7)으로 합니다.
4. 동률이면 단순한 쪽을 남깁니다. 현직이 더 단순하면 현직을 유지합니다. R-30의 `tie_break: simplest_surviving`과 같은 원칙입니다(`data/macro/rules_v2.0.0.json:803`).
5. 검정력이 모자라 판단할 수 없으면 채택하지 않고 INSUFFICIENT_DATA로 둡니다. 교체에서 현직 비교가 INSUFFICIENT_DATA면 교체하지 않습니다.
6. 결정 14 전에는 2027-01-01 이후 자료를 건드린 실행을 채택하지 않습니다(기존 규칙 ⑧-2, 3.3).

### 4.1 예측 모델 (F)

#### 4.1.1 이미 있는 채택 기준: R-30 변동성 추정기 (기존)

| 단계 | 기존 기준 | 근거 |
|---|---|---|
| 등록 | 손실·기준·검정을 미리 선언합니다(기본 `qlike`, `sma20`, `mcs_T_max`). `ml` 종류와 같은 이름의 재등록은 거부합니다 | `core/quant/forecast_eval.py:61-91` |
| Stage 1 보정 | h = 21 비중첩 원점. FHS 5% VaR 초과율이 ±2 이항 SE 안, 팬 PIT χ² p ≥ 0.01, Christoffersen CC p ≥ 0.05, 원점 ≥ 200 | `:523-551`, `:43-46` |
| Stage 2 정확도 | QLIKE MCS(T_max, 정상 부트스트랩 평균 블록 max(10, 2h), B 2,000, 시드 11). 90% 집합은 p ≥ 0.10. MSE MCS는 인쇄만 | `:203-243`, `:553-557`; `data/macro/rules_v2.0.0.json:786-794` |
| Stage 3 경제성 | 목표: 적격 생존자 중 63일 vol-of-vol 최소(`min_vol_of_vol_rolling63`). 적격: SMA20 북 대비 ΔSR ≥ −0.10(비열등), ΔMDD ≥ 0, PC-2 꼬리비 ≤ 0.90. 동률은 부트스트랩 CI 겹침으로 보고 단순한 쪽을 남깁니다 | `forecast_eval.py:560-582`; `rules_v2.0.0.json:795-813`(목표 `:796`) |
| 교체 | 계수된 개정이 있어야 합니다: 도전자 설정의 원장 행, 추정기를 사유로 적은 헤더 revision ≥ 2, 도전자의 v2 CARD-P PASS | `forecast_eval.py:685-721`; `rules_v2.0.0.json:814-817` |
| 열린 문제 | Stage 3의 순위와 승자는 계산하지 않습니다. "겹치는 부트스트랩 CI"가 어떤 통계의 CI인지 정해지지 않았습니다(TASK-M7-28) | `forecast_eval.py:563-567`, `:582` |

- 이 게이트는 운영에서 돌지 않습니다. 운영 σ는 SMA20뿐입니다(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:3111`).
- R-30은 "MCS 집합 안 + 경제성 적격(비열등) + 적격 생존자 중 63일 vol-of-vol 최소, 동률이면 단순한 쪽"입니다. SMA20이 집합에 남고 CI가 겹치면 SMA20이 이깁니다. 그래서 C2의 "확실히 나을 때만"과 같은 방향입니다.

#### 4.1.2 다른 예측 모델로 넓히는 규칙 (PROPOSAL, 결정 5; F-9는 결정 18)

| # | 규칙 | 기본값 | 근거 |
|---|---|---|---|
| F-1 | 분포나 위험 수치로 쓰이는 예측이면 4.3의 보정 규칙을 먼저 통과합니다 | 기존 기준 | 4.3 |
| F-2 | 현직 대비 DM. 손실 차 d = L_도전 − L_현직, `forecast_eval.dm_test`(HAC lag max(10, 2h), HLN 보정, t(n−1)). t < 0이고 단측 p(양측 p의 절반) ≤ α. α는 F-7을 따릅니다 | F-7 | `dm_test`는 양측 p를 냅니다(`core/quant/forecast_eval.py:155`) |
| F-3 | 도전자가 현직을 포함하는 중첩 모형이면 DM 대신 Clark–West 단측 p ≤ 0.10 | - | `cw_test`(`:159-165`) |
| F-4 | 도전자가 MCS 90% 집합(p ≥ 0.10) 안에 있습니다. 후보는 현직, 기준, 그리고 F-9로 등록한 변형 전부입니다 | R-30 Stage 2를 일반화 | `mcs`(`:237`) |
| F-5 | 등록한 변형이 둘 이상이면 F-2의 p에 Holm 보정을 합니다. 묶음은 제출한 것만이 아니라 F-9로 등록한 변형 전부입니다 | - | `gate_stats.holm_adjusted`(`core/quant/gate_stats.py:515-529`) |
| F-6 | 북이나 판정에 들어가는 예측이면 경제성 비열등(Stage 3 형식)도 통과합니다 | 기존 형식 | `forecast_eval.py:560-582` |
| F-7 | 공통 원점 500 이상(모든 h). h = 1은 α 0.10, h > 1은 α 0.05. 원점이 모자라면 DM은 인쇄만 하고 채택하지 않습니다(INSUFFICIENT_DATA) | 이번 측정 5.4 | `dm_test`의 HAC 시차(`:150`) |
| F-8 | 조건부 예측력(GW)은 인쇄만 합니다 | - | `gw_test`(`:168-189`) |
| F-9 | OOS 구간에서 평가하는 예측 변형은 평가 전에 모두 등록하고 원장 행을 남깁니다. 형식은 R-30 교체 증명이 도전자에게 요구하는 원장 행과 같습니다. 등록 없이 평가한 변형이 하나라도 있으면 채택하지 않습니다 | - | `register_forecast`는 같은 이름만 거부하고 수를 세지 않습니다(`core/quant/forecast_eval.py:76-86`). `check_declaration`은 도전자 설정의 R-23 원장 행을 요구합니다(`:704-717`) |

채택 = F-1(해당 시) 그리고 F-2(또는 F-3) 그리고 F-4 그리고 F-6(해당 시) 그리고 F-9.

- C2의 "trial 수를 반영" 요구는 MCS와 Holm만으로는 채워지지 않습니다. 두 방법은 비교에 넣은 모델만 셉니다. F-9가 시도하고 버린 변형까지 세게 합니다.
- R-30 밖의 예측 카드(DNS, LETF drag)는 공통 하네스 없이 스터디 코드가 판정했습니다. 두 카드는 기준(랜덤워크, 설명력)을 넘지 못했습니다(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:141`). 새 예측 모델은 위 규칙과 `forecast_eval`의 함수로 판정합니다.

### 4.2 전략 (S)

#### 4.2.1 기존 전략 게이트 (그대로 옮김)

| 검사 | 기존 기준 | 위치 (`core/quant/validate.py`) |
|---|---|---|
| walk-forward | IS 756, OOS 126, 짧으면 첫 IS 504, embargo = 보유기간 | `:54`, `:345-381` |
| 표본 하한 | 거래 ≥ 30, OOS 만 5년, 세션 ≥ 1,260. 못 미치면 INSUFFICIENT_DATA | `:56`, `:584-591` |
| Sharpe 구간 | 90% 스튜던트화 순환 블록 부트스트랩(블록 10, B 2,000) 하한 > 0 | `:54`, `:163-183`, `:578` |
| DSR | ≥ 0.95. 못 미치면 REJECT | `:55`, `:593` |
| PBO | ≤ 0.05, 또는 승자 OOS 손실 비율 ≤ 10%. 구성 < 8이면 손실 비율만 봅니다. 구성 ≥ 8에서 PBO > 0.20이고 승자도 지면 REJECT | `:55`, `:68`, `:576-577` |
| 기준 대비 | 짝지은 순환 블록 부트스트랩 단측 p ≤ 0.10. 아니면 REJECT | `:71`, `:186-208`, `:592` |
| 2배 비용 | 2배 비용 Sharpe > 0. 손실이면서 구간이 0을 포함하면 REJECT | `:57`, `:580`, `:594` |
| OOS/IS | ≥ 0.5 | `:55`, `:579` |
| 양수 연도 | ≥ 60% | `:55`, `:581` |
| 고원 | 이웃의 50% 이상이 Sharpe 절반 이상, 격자 끝이 아님 | `:56`, `:384-418` |
| 거래 수 | ≥ 100 | `:56`, `:583` |
| 헤어컷 | McLean–Pontiff 0.6, 인쇄만 | `:57` |

판정 순서는 INSUFFICIENT_DATA → REJECT → PASS → INSUFFICIENT_DATA(구간만 실패하고 최소 기록 미달) → REVISE입니다(`:584-622`).

#### 4.2.2 채택 규칙 (PROPOSAL, 결정 번호는 행마다)

| # | 규칙 | 기본값 | 근거와 이유 |
|---|---|---|---|
| S-1 | 기존 게이트 PASS. 게이트의 벤치마크 검정(`bench_daily` 하나, p ≤ 0.10)도 여기에 들어갑니다 | 기존. 필요조건으로 두는 것은 결정 16 | `core/quant/validate.py:592-596` |
| S-2 | DSR의 N은 등록한 N입니다. ⑨-3d 전에는 격자 크기 G와 계열 원장 N_raw(literal, family-wide; R3 설계 3.13) 두 값 모두에서 DSR ≥ 0.95 | 결정 3 | Lab은 N = G입니다(`core/research/strategy_workflow.py:107`, K-c). 스터디는 기록된 이전 격자를 더합니다(`docs/asset_expansion_study.py:182`, `:339-343`). C3 원장은 17행인데 카드 N은 11입니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:327-334`) |
| S-3 | 교체일 때 같은 OOS 세션에서 현직과 짝지은 ΔSharpe. `gate_stats.lw_studentized_boot`(영가설 중심 t*, 블록 = max(21, PW)) 단측 p ≤ 0.10, 점추정 > 0 | 결정 6 | `core/quant/gate_stats.py:297-336`, `:342-356`. `validate.sharpe_diff_bootstrap`의 p는 영가설 p가 아니라 부트스트랩 분포의 하측 비율입니다(`core/quant/validate.py:186-208`; `research:...MODEL_LIMITS_REGISTER_2026-10-28.md:1172`) |
| S-4 | 등록한 기준전략 각각에 대해 S-3과 같은 `gate_stats.lw_studentized_boot` 검정. 단측 p ≤ 0.10, 점추정 > 0. 하네스 파일 밖에서 계산합니다(7절) | 기준 집합은 결정 4, 통계는 결정 6 | 게이트는 `bench_daily`를 하나만 받습니다(`core/quant/validate.py:493`, `:520-521`). 게이트의 벤치 p도 S-3에서 쓰지 않은 하측 비율입니다. 같은 이유로 추가 기준전략의 판정에도 쓰지 않습니다 |
| S-5 | 한 등록에 규칙이 둘 이상이면 계열 SPA consistent p ≤ 0.05(1배 비용). 살아남는 규칙은 BH q 0.10과 창별 지속성 ≥ 60% | 테크펀드 규칙을 넓힘, 결정 7 | `core/quant/tf_gov.py:58-62`, `:257-333` |
| S-6 | 손익분기 비용 < 2 × 표 비용이면 게이트 전에 REJECT. 게이트 시행을 쓰지 않습니다 | 테크펀드 GOV-7을 넓힘, 결정 7 | `core/quant/tf_gov.py:63`, `:431-442` |
| S-7 | 검정력 줄을 인쇄합니다. MDE80 = 2.1232 × SE(ΔSR)가 등록한 기대 ΔSR보다 크면 S-3을 INSUFFICIENT_DATA로 둡니다 | 매크로 카드 규칙을 넓힘, 결정 6 | `core/quant/gate_stats.py:426-488`; 이번 측정 5.3 |
| S-8 | L1(8.2)은 지금 두 파일럿 설정(`pilot` = `E1-SPY`, `C3-BTCUSD`)에만 있습니다. 새 모델에 쓰려면 브리지 스펙 개정, 새 `pilot` 값, 새 `code_sha256`, 새 `owner_confirmed`가 필요합니다. 그 설정이 지원되면 모의 단계 전에 hard 검사 P0~P4, P7, P12, P13을 통과합니다 | 결정 20. UNVERIFIED(파일럿 미실행) | `research:docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:859-872`, `:1126`, `:1176`, `:1185-1191`, `:1713-1721` |

- S-2는 새로 등록하는 모델에만 쓰는 채택 기준입니다. 기존 카드의 판정 기준을 바꾸지 않습니다. R3가 요구한 분리(원장 기반 계수와 기존 판정의 보수화)를 지킵니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:169-171`).
- 소유자가 ⑨-3d 전에 어떤 N도 채택 기준으로 쓰지 않기를 원하면, 새 전략의 채택은 ⑨-3d까지 보류합니다(결정 3의 (가)).
- 추가와 교체를 나눕니다(3.2 12번, 결정 19).
  - **교체**(현직이 있고 그것을 바꿈): S-1~S-4를 모두 봅니다. S-3이 INSUFFICIENT_DATA면 결과도 INSUFFICIENT_DATA이고 교체하지 않습니다(4.0 규칙 2, 5).
  - **추가**(아무것도 바꾸지 않음): S-1, S-2, S-4로 판단합니다. 현직과의 비교는 인쇄만 하고, "현직보다 낫다"고 주장하지 않습니다.
  - 상관이 낮은 새 전략을 교체로 등록하면 S-3이 대개 INSUFFICIENT_DATA가 됩니다(5.3). 그래서 교체는 현직과 상관이 높은 개선에서만 현실적입니다.

### 4.3 리스크·분포 모델 (R)

#### 4.3.1 기존 기준 (그대로 옮김)

분포 카드(`validate.score_distribution`, `core/quant/validate.py:741-796`):

| 판정 | 기존 기준 |
|---|---|
| INSUFFICIENT_DATA | 원점 < 500(`GATE["var95_min_origins"]`, `:72`, `:770`) |
| REJECT | 95% 초과율 ≥ 10%, 신호등 적색(최근 250일 99% 예외 ≥ 10), PIT KS p < 0.01, 비수렴 > 5% |
| PASS | 95% Kupiec p > 0.05, Christoffersen CC p ≥ 0.05, 90% 커버리지 ±2SE, PIT KS p > 0.05이고 상관도 플래그 없음, 신호등 녹색 |
| REVISE | 그 밖 |

Quant Lab M9(`core/quant/lab.py:67-68`, `:617-650`): 2016~26 구간의 99% VaR Kupiec p ≥ 0.05, CC p ≥ 0.05, ES 97.5% Z2 p ≥ 0.05, h = 21 팬 PIT χ² p ≥ 0.01. 원점 ≥ 200, 팬 원점 ≥ 20. 값이 없으면 NOT_RUN이고 통과가 아닙니다.

B5(`core/quant/forecast_eval.py:354-400`; `data/macro/rules_v2.0.0.json:830-837`): 원점 ≥ 200에서 5% 초과율이 ±2 이항 SE 안, 10구간 PIT χ² p ≥ 0.01.

#### 4.3.2 채택 규칙 (PROPOSAL, 결정 8; R-7은 결정 18)

| # | 규칙 | 근거 |
|---|---|---|
| R-1 | 해당 게이트를 통과합니다(분포 카드, M9, B5·Stage 1 중 쓰임에 맞는 것) | 4.3.1 |
| R-2 | 보정 다음은 예리함입니다. 같은 원점에서 적정 점수 규칙으로 현직과 비교합니다. VaR는 tick loss, 분포는 CRPS를 쓰고, F-2(DM 단측, α는 F-7)와 F-4(MCS 집합)를 적용합니다 | `forecast_eval.tick_loss`(`core/quant/forecast_eval.py:113-116`); `validate.crps`(`core/quant/validate.py:713-722`); 모듈 문서의 Gneiting & Raftery 2007(`:30`) |
| R-3 | 위반 0건이고 n < 400이면 정확한 LR p로 다시 봅니다. 위반 0건의 정확한 LR은 −2n·log(1 − α)이고 p는 χ²(1)에서 냅니다. 기준 계산은 `tools/status/section10_probes.py:27-31`입니다. 채택 평가에 쓰려면 이 한 줄을 새 모듈에 옮겨야 하므로 새 코드입니다(결정 8, 21). 코드의 점수 근사는 α 0.01, n 192~380에서 정확한 LR보다 관대합니다. 함수는 고치지 않습니다 | N-M1-01(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:821`); `core/quant/validate.py:633-635` |
| R-4 | 99% 수준을 주장하는 모델은 원점 1,000 이상에서 판정합니다. 이 값은 `GATE["var99_min_origins"]`로 정의돼 있지만 쓰이지 않습니다 | `core/quant/validate.py:72`; N8(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:1275`) |
| R-5 | h > 1은 비중첩 원점으로 Kupiec과 CC를 봅니다. `score_distribution`은 h > 1에서 CC를 건너뜁니다 | `core/quant/validate.py:745-746`; Stage 1의 방식(`core/quant/forecast_eval.py:528`) |
| R-6 | 같은 검사를 같은 원점에서 현직에도 돌려 나란히 적습니다. 현직도 실패하는 검사는 도전자의 우위 근거가 되지 않습니다 | - |
| R-7 | 평가하는 리스크 변형은 평가 전에 모두 등록하고 원장 행을 남깁니다(F-9와 같음). R-2의 MCS 후보와 Holm 묶음은 등록한 변형 전부입니다 | F-9 |

### 4.4 데이터 원천·처리 변경 (D, PROPOSAL, 결정 9)

| # | 규칙 | 근거 |
|---|---|---|
| D-1 | 바꾸기 전에 두 원천을 날짜별로 대조합니다. 대조는 소유자 PC에서 돌리고, Claude는 일치율과 불일치 날짜만 받습니다(3.5). 결과 형식은 ⑤-2 공급사 대조와 같게 합니다. 기준값은 ⑤-2 결과가 나온 뒤 정합니다. 대조 통과는 채택의 전제조건일 뿐이고 시행 분류를 바꾸지 않습니다(D-2) | `REMAINING_WORK_2026-10-27.md:132`; `ROADMAP_REVIEW_2026-10-27.md:47`. ⑤-2는 아직 끝나지 않았습니다(UNVERIFIED: 도구 이름과 기준) |
| D-2 | 시행 분류는 R3 설계 4.2 9a·9b행을 그대로 따릅니다. 같은 자료 요청의 새 판, 또는 "이력 연장" 판정 뒤 같은 `source_requested`로 `days`만 늘린 것은 9a REMEASURE이고 새 시행이 아닙니다. 판정이 바뀌면 DATA_FRAGILE로 표시합니다. 요청한 원천(`source_requested`)을 바꾸면 대조 결과와 상관없이 9b DATA_CHOICE이고 SEARCH로 셉니다 | R3 설계 4.2 9a행(`:418`), 9b행(`:419`) |
| D-3 | 결과를 본 뒤 기간을 줄이거나(늦은 시작일) 원천을 고르는 것도 9b입니다 | R3 설계 4.2 9b행(`:419`) |
| D-4 | 판정이 원천에 따라 갈리면 채택하지 않습니다. 등록한 주 원천에서 성립하고, 둘째 원천에서 점추정의 부호가 같아야 합니다. 둘째 원천의 평가는 9b의 시행으로 셉니다. 소유자가 ⑨-3d에서 달리 정하면 그것을 따릅니다 | CRY-1 대조(변동성 맞춤 롱온리 대조 대비)에서 C3 규칙은 Upbit KRW-BTC로 PASS, Binance BTCUSDT로 REJECT였습니다. 카드 C3는 소유자 판정 D-24로 PASS를 유지합니다(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:145`, `:1093`). 이 규칙은 기존 카드 C3에 소급하지 않습니다 |
| D-5 | 동결 연구의 입력은 바꾸지 않습니다 | `README.md:78-83` |

### 4.5 가격 공식 (P)

- 시장 성과가 아니라 계산의 정확성이 질문입니다.
- 채택 기준은 독립 구현 대조와 기준값 테스트입니다. 모델 한계 대장의 "독립 검증됨" 정의를 씁니다(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:61`).
- 이 문서의 통계 비교는 적용하지 않습니다. 가격기를 거래 신호로 쓰면(예: 이론가 괴리 전략) 그 전략은 S 유형입니다.

## 5. 최소 증거

### 5.1 기존 하한 (그대로 옮김)

| 대상 | 하한 | 위치 |
|---|---|---|
| 전략 게이트 | OOS 만 5년, 1,260세션, 거래 30(INSUFFICIENT 경계). PASS에는 거래 100 | `core/quant/validate.py:56`, `:585-586` |
| 전략 Sharpe 구간 | 최소 기록 T > 252·(z/SR)², z = 1.645 | `:156-160` |
| 분포 카드 | 95% 검정 원점 ≥ 500 | `:72`, `:770` |
| Quant Lab M9 | 원점 ≥ 200, 팬 원점 ≥ 20 | `core/quant/lab.py:67-68` |
| B5, R-30 Stage 1 | 원점 ≥ 200 | `core/quant/forecast_eval.py:43`, `:548` |
| MCS | 공통 원점 ≥ 30 | `:214-215` |
| CARD-P PC-7 | 세션 ≥ 882. 이산 규칙은 군집 제거 시작점 ≥ 30, 연속 규칙은 닫힌 국면 ≥ 5 | `core/quant/cardp.py:68-70`, `:344-357` |
| 매크로 등급 A | 표본 안 스트레스 국면 ≥ 3, OOS 국면 ≥ 1 | `data/macro/rules_v2.0.0.json:2036-2041` |
| 원장 상관 | 공통 관측 ≥ 20 | `core/quant/gate_ledger.py:76` |
| 숙성 | 첫 기록 세션부터 252세션 이상. 소급 기록은 세지 않음 | `core/quant/tf_gov.py:65-66`, `:527-553` |

### 5.2 Sharpe 크기별 필요한 길이 (이번 측정, `validate.min_track_record`, 수준 0.90)

| 연 Sharpe | 세션 | 연 |
|---|---|---|
| 0.3 | 7,576 | 30.1 |
| 0.5 | 2,727 | 10.8 |
| 0.75 | 1,212 | 4.8 |
| 1.0 | 682 | 2.7 |
| 1.5 | 303 | 1.2 |

- OOS 5년 하한을 넘어도, Sharpe 0.5 전략의 90% 구간이 0을 배제하려면 10.8년이 필요합니다.
- 이때 게이트는 INSUFFICIENT_DATA가 아니라 REJECT("deflated Sharpe below 0.95")를 냅니다. 두 이유가 겹칩니다.
  - REJECT 검사(`core/quant/validate.py:592-596`)가 INSUFFICIENT_DATA 분기(`:606-611`)보다 먼저입니다.
  - N = 1에서도 DSR ≥ 0.95는 90% 구간이 0을 배제하는 것과 같은 z(1.645)를 요구합니다. N > 1이면 더 엄격합니다(`:156-160`, `:220-237`).
  - 모델 한계 대장도 같습니다(`research:...MODEL_LIMITS_REGISTER_2026-10-28.md:1231`).
- 이번 측정: 연 Sharpe가 정확히 0.5인 합성 iid 1,260세션에서 `deflated_sharpe(n_trials=1)`은 0.868입니다(50회, 0.867~0.869). 0.95 미만입니다.
- `:606` 분기는 DSR은 통과했는데 부트스트랩 구간만 0을 포함할 때 닿습니다.
- 카드 판정은 REJECT 그대로입니다. 채택에서 이 REJECT를 어떻게 다룰지는 결정 17입니다.
- 모의 단계의 숙성 252세션은 Sharpe 1.5에도 모자랍니다. 그래서 모의 단계는 edge를 확증하지 못합니다(8.3).

### 5.3 ΔSharpe 비교의 최소 검출 효과 (이번 측정)

MDE80 = 2.1232 × SE(ΔSR). SE는 `gate_stats.lw_hac_se`로 냈습니다. 합성 iid 정규 일간 수익률, 두 전략 모두 연 Sharpe 0.5, 조합마다 20회의 중앙값입니다.

| OOS 길이 | ρ = 0 | ρ = 0.5 | ρ = 0.9 | ρ = 0.97 |
|---|---|---|---|---|
| 1,260세션 (5년) | 1.33 | 0.94 | 0.42 | 0.23 |
| 2,520세션 (10년) | 0.95 | 0.68 | 0.30 | 0.16 |
| 5,040세션 (20년) | 0.67 | 0.48 | 0.21 | 0.12 |

- ρ는 두 전략 일간 수익률의 상관입니다. SE는 근사식 √(2(1−ρ)·252/T)과 소수 둘째 자리까지 맞았습니다.
- 서로 거의 독립인 두 전략은 5년으로 연 Sharpe 차이 1.33 미만을 80% 검정력으로 구분하지 못합니다.
- 같은 계열의 변형(ρ ≥ 0.9)은 작은 차이도 잡힙니다. 5년, ρ 0.97이면 0.23입니다.
- 그래서 "현직보다 낫다"는 주장은 현직과 상관이 높은 개선에서만 현실적으로 검증됩니다(4.2.2의 추가·교체 문단).
- 실제 수익률은 꼬리가 두껍고 자기상관이 있어 SE가 더 큽니다(UNVERIFIED: 실데이터에서 재지 않음).

### 5.4 DM 검정의 실제 기각률 (이번 측정)

`forecast_eval.dm_test`를 정확도가 같은 두 예측에 적용했습니다. 손실은 표준정규 오차 제곱의 h일 합(겹치는 원점)입니다. 판정은 F-2와 같게 "t < 0이고 단측 p ≤ α"로 셌습니다. 칸마다 15,000회(시드 셋 × 5,000회)이고, 0.10 근처의 몬테카를로 SE는 약 0.0024입니다.

| h | 원점 n | F-2, α 0.10 | F-2, α 0.05 | 양측 10%(참고) | 비중첩 원점, h = 1 검정, α 0.10 | 영가설 t의 10% 분위 |
|---|---|---|---|---|---|---|
| 1 | 500 | 0.104 | 0.054 | 0.109 | - | −1.31 |
| 1 | 2,000 | 0.103 | 0.054 | 0.105 | - | −1.30 |
| 5 | 500 | 0.119 | 0.067 | 0.133 | 0.119 (100개) | −1.39 |
| 5 | 2,000 | 0.117 | 0.064 | 0.129 | 0.104 (400개) | −1.38 |
| 5 | 5,000 | 0.115 | 0.063 | 0.127 | 0.100 (1,000개) | −1.37 |
| 21 | 500 | 0.135 | 0.079 | 0.155 | 0.180 (24개) | −1.50 |
| 21 | 2,000 | 0.120 | 0.069 | 0.138 | 0.121 (96개) | −1.42 |
| 21 | 5,000 | 0.126 | 0.070 | 0.139 | 0.112 (239개) | −1.42 |

- h = 1은 명목에 맞습니다.
- h > 1은 F-2 수준에서 명목 0.10의 약 1.15~1.35배로 기각합니다. 원점을 2,000이나 5,000으로 늘려도 줄지 않습니다.
- 원인은 HAC 가중입니다. 시차 max(10, 2h)의 Bartlett 가중(`core/quant/validate.py:273-285`)은 겹침이 만든 자기상관(시차 h − 1까지)을 덜 셉니다. 기대 장기분산은 참값의 0.855(h = 5), 0.838(h = 21)입니다. 이 비율로 계산한 기각률은 0.118, 0.120이고, 원점 2,000 이상의 측정값(0.115~0.126)과 맞습니다. 표본 크기와 상관없는 편향이라 원점을 늘려도 남습니다(계산은 10.3).
- 단측 α를 0.05로 낮추면 h > 1에서 0.063~0.079입니다. 명목 0.10 안입니다.
- 이 설계의 합성 영가설로 맞춘 임계값은 t ≤ −1.37~−1.42(원점 2,000 이상)입니다. 손실 분포에 따라 달라지므로 그대로 옮겨 쓸 수 없습니다.
- 비중첩 원점은 400개 이상에서 명목에 가깝습니다. h = 21이면 8,400세션 이상입니다.
- 이것이 F-7의 근거입니다. 손실 분포가 실제 QLIKE와 다르므로 실데이터 손실에서의 기각률은 UNVERIFIED입니다. 변동성이 지속되는 실제 손실은 자기상관이 시차 h − 1보다 길어 편향이 더 클 수 있습니다(UNVERIFIED). MCS의 크기와 검정력은 재지 않았습니다(UNVERIFIED).
- 초판의 표(양측 10%, 칸마다 400~500회, 시드 하나)는 검토에서 재현되지 않아 이 표로 바꿨습니다. 초판의 "명목의 1.6~1.8배"와 "원점 2,000이면 0.11~0.12" 문장은 F-2 수준에서 성립하지 않았고, 초판 F-7의 "h > 1은 원점 2,000 이상"도 근거가 없어 뺐습니다.

### 5.5 국면 (PROPOSAL, 결정 10)

- 채택하려면 OOS 구간에 닫힌 하락 국면이 하나 이상 있어야 합니다. 국면은 CARD-P의 기존 규칙(자기 종가 기준 하락 θ 0.20, 미국 SPX 0.15)으로 셉니다(`core/quant/cardp.py:72`, `:421-466`). 매크로 등급 A의 "OOS 국면 ≥ 1"과 같은 값입니다(`data/macro/rules_v2.0.0.json:2041`).
- 국면별 Sharpe(`validate.regime_split`, `core/quant/validate.py:440-452`)와 스트레스 창 표(`tf_gov.stress_table`, `core/quant/tf_gov.py:455-480`)는 인쇄합니다.
- `regime_split`의 고·저 변동성 기준은 OOS 전체 중앙값입니다. docstring은 "known at t"라고 하지만 시점 t에 알 수 없습니다(N9, `research:...MODEL_LIMITS_REGISTER_2026-10-28.md:1235`). 그래서 판정에 쓰지 않습니다.
- 양수 연도 60%는 기존 게이트에 있습니다(`core/quant/validate.py:55`).

## 6. 실패와 경계 사례

### 6.1 결과 이름

게이트의 어휘는 PASS, REVISE, REJECT, INSUFFICIENT_DATA 네 개입니다(`core/quant/validate.py:50`). PROPOSAL: 채택 단계는 이름 둘(ADOPT, KEEP)을 더합니다(결정 16). 두 이름은 카드 판정이 아닙니다.

| 채택 결과 | 조건 | 다음 |
|---|---|---|
| ADOPT | 4절의 해당 규칙을 모두 충족. 결정 14 전에는 표본이 2026-12-31 이전에 끝남 | 8절의 다음 단계 |
| KEEP (현직 유지) | 게이트는 PASS이지만 게이트 밖의 비교(S-3, S-4, F-2, F-4, R-2)에서 확실히 이기지 못함. 경계 사례 포함. 게이트 자신의 벤치마크 검정 실패는 KEEP이 아니라 게이트 REJECT입니다(`core/quant/validate.py:592`) | 기록만 합니다. 같은 자료로 다시 시도하지 않습니다 |
| REVISE | 게이트가 REVISE. 공학 검사 실패 | 게이트의 수정 목표를 따릅니다. 재실행은 새 시행입니다 |
| REJECT | 게이트 REJECT(DSR, PBO, 2배 비용, 벤치마크), 또는 D-4 위반. 짧은 기록의 DSR REJECT는 결정 17 | 같은 자료로 같은 가설을 다시 내지 않습니다 |
| INSUFFICIENT_DATA | 표본 하한, 최소 기록, 검정력(MDE80) 부족 | 등록 뒤에 생기는 자료로만 다시 봅니다. 그 자료가 2027-01-01 이후면 결정 14가 먼저입니다 |

### 6.2 경계 사례 (PROPOSAL, 결정 11)

- 경계 구간은 게이트가 판정하지 않는 값에만 둡니다.
  - 게이트 밖 비교(S-3, S-4, F-2, R-2)의 단측 p가 (0.10, 0.20].
  - S-2의 둘째 DSR(원장 N_raw)이 [0.90, 0.95)이고, 게이트 DSR(N = G)은 0.95 이상.
  - MCS p가 [0.05, 0.10).
- 게이트 DSR이 0.95 미만이면 경계가 아니라 게이트 REJECT입니다(`core/quant/validate.py:593`). 짧은 기록의 경우는 결정 17입니다.
- PBO는 경계에 넣지 않습니다. 게이트의 과탐색 검사는 PBO와 승자 손실 비율을 함께 봅니다. 구성이 8개 이상이면 PBO가 0.05를 넘어도 승자 손실 비율이 10% 이하(평평한 고원)면 통과합니다. 8개 미만이면 PBO는 인쇄만 합니다(`:59-66`, `:576-577`). PBO 값만으로 경계를 정하면, PBO 0.15인 모델은 경계가 되고 평평한 고원의 PBO 0.5 모델은 경계가 아닌 역전이 생깁니다.
- 경계는 채택하지 않습니다. 이것이 "확실히"의 뜻입니다.
- 경계에서 허용하는 일은 하나입니다. 등록을 고치지 않고, 등록 뒤에 생긴 자료로 같은 검정을 한 번 더 하는 것입니다. 그 재평가 시점도 미리 적습니다. 그 자료가 2027-01-01 이후면 결정 14가 먼저입니다(3.3).

### 6.3 같은 자료에서 다시 맞추지 않기

- 결과를 본 뒤 바꾼 설정은 모두 새 시행입니다. 원장 행이 늘고 DSR의 N이 커집니다(`core/quant/gate_ledger.py:379-386`; R3 설계 4.2 5행). 가설이나 주장을 바꾸면 계수된 개정이고 새 등록입니다(3.1).
- 바뀐 모델은 바뀐 뒤 고정한 시점 이후의 자료로만 확증합니다. H2의 규칙과 같습니다: "a change proposed after seeing a session is a new trial and is tested only on sessions after its own freeze"(`paper_live/config.py:219-220`).
- 확증 평가 뒤에 같은 구간을 다시 평가하면 그 확증은 소진됩니다(R3 설계 4.2 7b행, `:413`).
- 게이트의 수정 목표도 같은 원칙을 씁니다. 비용 가정은 낮추지 않습니다(`core/quant/validate.py:617`). 국면 조건은 사전 등록한 것만 조입니다(`:618`).
- 모의·실거래 결과를 보고 고치는 것도 같습니다. 읽기 전용 증거 보고서를 내고, 바꾸려면 새로 등록하고, 새 자료로 평가합니다(R2, `research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:160-165`; `docs/product/TRADEGEN_READ_ONLY_BRIEF_2026-10-29.md:13-14`). 2027-01-01 이후 자료에서 본 실패 뒤에 무엇을 고칠 수 있는지는 결정 14입니다.

### 6.4 게이트의 알려진 결함과 채택 판단

게이트는 고치지 않습니다. 채택 판단에서만 아래처럼 다룹니다(PROPOSAL, 결정 16).

| 결함 | 게이트 동작 | 채택에서의 처리 | 근거 |
|---|---|---|---|
| N12 DSR 분모 ≤ 0 | DSR NaN이면 REVISE, 사유가 'interval includes zero'로 잘못 나옴 | DSR NaN은 S-2 미충족, INSUFFICIENT_DATA | `research:...KNOWN_ERRORS_REGISTER_2026-10-28.md:1758`; `core/quant/validate.py:593`, `:613-622` |
| K-c N = 격자 크기 | 시행 과소 | S-2 | `core/research/strategy_workflow.py:107`; `research:...KNOWN_ERRORS_REGISTER_2026-10-28.md:869` |
| K-d 계산 뒤 등록 | 실패 실행이 시행에서 빠질 수 있음 | 등록을 계산 전에 합니다(3.2 7번). 해결은 R3 ⑨-3a | `core/research/strategy_workflow.py:97-98`; `research:...KNOWN_ERRORS_REGISTER_2026-10-28.md:870` |
| 고원 규칙 | 고립된 진짜 edge도 REVISE | 그대로 둡니다. 채택하지 않습니다 | `research:...MODEL_LIMITS_REGISTER_2026-10-28.md:1230` |
| Lab 부트스트랩 B 1,000 | 구간 잡음이 큼 | 채택 평가는 B 2,000(`GATE`) | `core/research/strategy_workflow.py:66`, `:104-109` |
| K-f 비용 분류 | `BTCUSD`, `EURUSD`가 `us` 50 bp | 등록에 비용 행을 명시합니다. `bb35b3b`에서 `BTCUSD`는 아직 `us`입니다(코드 읽기) | `core/quant/validate.py:99-110`; `core/quant/history.py:333-335`; `research:...KNOWN_ERRORS_REGISTER_2026-10-28.md:872` |
| 짧은 기록의 DSR REJECT | 최소 기록 미달이어도 DSR < 0.95면 REJECT | 결정 17 | 5.2 |
| N-M1-01, N8 | 4.3.2 R-3, R-4 | 4.3.2 | 4.3.2 |

## 7. 기존 게이트와의 관계

- **바꾸지 않는 것.** `GATE`(`core/quant/validate.py:53-74`)는 "change them here and nowhere else"라고 적혀 있습니다(`:52`). 이 초안은 그 값을 읽기만 합니다. `_decide_strategy`, `score_distribution`, M9 기준, R-30 설정, CARD-P도 그대로입니다. Nautilus `code_sha256`에 드는 파일(`tools/nautilus/**`, `requirements-nautilus.txt`, `HARNESS_SOURCES`의 파일, `docs/asset_expansion_study.py`, `config.py`)도 그대로입니다(1.3).
- **과거 판정.** 저장 카드 34개(PASS 5, REVISE 11, REJECT 18; `research:...MODEL_LIMITS_REGISTER_2026-10-28.md:141`)의 판정은 그대로입니다. 이 기준은 소급하지 않습니다.
- **층 구조.** 채택은 게이트 위의 층입니다. 게이트 PASS는 필요조건이고 충분조건이 아닙니다.
- **새 계산의 자리 (PROPOSAL, 결정 21).** 게이트가 계산하지 않는 것(원장 N의 DSR, 현직·기준전략 대비 LW p, SPA, 새 기준전략, R-3의 정확한 LR)은 1.3의 해시 대상 파일 밖 새 모듈에서 기존 함수를 불러 계산합니다. 하네스 파일을 고치면 게이트 패키지 변경입니다(`core/quant/gate_package.py:36-38`). 게이트 패키지는 아직 NOT_FROZEN입니다(`data/macro/rules_v2.0.0.json:1566`, `gate.package.status`). 새 모듈은 Step 7A.3 커밋과 `main` 병합 동결 해제 전에는 만들지 않습니다(병합 동결은 `b00cb42`의 소유자 판정).
- **R3.** N_raw, N_eff, 시행 분류, 독립 검증 조건은 R3 설계가 원본입니다(3.12~3.15, 4.2). 판정 기준 변경은 소유자의 ⑨-3d 결정입니다(`REMAINING_WORK_2026-10-27.md:120`). R3 10.2 A 질문은 2026-11-03에 모두 승인됐습니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:542`, `:560`). ⑨-3a~⑨-3d는 아직 인계 장부(`9c0d782`)에 없습니다.
- **동결 연구.** paper_live H2(⑧-1, 판독 기한 약 2026-12-19)와 GROKTEAM forward look(⑧-3)은 태그 `studies-of-record-2026-10-23`에서 자기 동결 규칙으로 판독합니다(`README.md:78-83`; `REMAINING_WORK_2026-10-27.md:118-119`). 이 기준은 그 판독에 적용하지 않습니다.
- **Nautilus 브리지.** 엔진 패리티는 별도 검사입니다. 브리지 작업의 완료 기준은 "`GATE` 불변"입니다(`REMAINING_WORK_2026-10-27.md:100`). 브리지는 두 파일럿 설정만 지원하고, 다중 슬리브 북과 Strategy Lab 연동은 범위 밖입니다(`research:...nautilus-bridge-design.md:1713-1721`). S-8은 패리티 결과를 읽기만 합니다.
- **2027-01-01 잠금 홀드아웃.** 그 뒤 자료는 어떤 설계에도 쓰지 않습니다(`REMAINING_WORK_2026-10-27.md:122`). 이 기준에서 그 뒤 자료가 필요한 일과 결정 전의 처리는 3.3에 적었습니다. 확증, 모의 숙성의 시계, 실패 뒤 처리는 결정 14입니다.

## 8. 승격 단계 (PROPOSAL, 결정 13; L1은 결정 20, L3는 결정 12)

### 8.1 단계 표

| 단계 | 이름 | 들어가는 조건 | 하는 일 | 실행 주체 | 통과 조건 | 실패하면 | 승인 |
|---|---|---|---|---|---|---|---|
| L0 | 연구 채택 | 등록 커밋. 결정 14 전에는 표본 끝 ≤ 2026-12-31 | 게이트와 4절 규칙 | 소유자 PC에서 실데이터 실행 → Claude가 요약 출력을 분석 | ADOPT | 6절 | 소유자 |
| L1 | 엔진 독립 재계산 | L0 ADOPT, 브리지가 그 설정을 지원(지금은 두 파일럿뿐, 8.2) | Nautilus 패리티 | 소유자 PC. Claude는 of-record 모드를 돌리지 않음 | P0~P4, P7, P12, P13 hard 통과 | 원인 조사, L0으로 | 소유자(`owner_confirmed`) |
| L2 | 모의 (H2 형식) | L0(해당 시 L1) 통과, 모의 가설 고정, 결정 14가 2027-01-01 이후 세션의 숙성 사용을 허락 | 모의 기록, 숙성 | 소유자 PC 기록 → Claude 분석 | 8.3의 기준 | 중지. 그 뒤 고칠 수 있는 범위는 결정 14 | 소유자 |
| L3 | 소규모 실거래 | L2 통과, 법률 검토, 주문 안전 조건, 결정 14 | 한도 안의 실거래 | 소유자 | 8.4의 정기 재평가 | kill switch, L2로 | 소유자의 명시적 실거래 전환 |

- 결정 14 전에는 L2와 L3를 시작하지 않습니다. 2026-12-31까지 남은 세션으로는 숙성 252세션을 채울 수 없습니다(3.3).

### 8.2 L1 엔진 독립 재계산

- 브리지 스펙의 hard 검사를 씁니다: 입력 출처(P0), 결정 일치 100%(P1), 상관 ≥ 0.9999(P2), |ΔSharpe| ≤ 0.01(P3), 체결 막대 일치(P4), 수수료 재계산(P7), 선택을 맞춘 OOS 계열의 P2·P3(P12), 완전성(P13)(`research:docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:859-872`).
- 브리지는 두 파일럿 설정만 받습니다. `pilot`은 `E1-SPY`, `C3-BTCUSD`, `rehearsal` 중 하나입니다(`:1126`, `:1176`). 다중 슬리브 북(`S_E1_trend_us` 포함)과 Strategy Lab 연동은 범위 밖입니다(`:1713-1721`).
- 그래서 지금은 어떤 새 모델도 L1에 들어갈 수 없습니다. 넣으려면 브리지 스펙 개정, 새 `pilot` 값, `tools/nautilus/**` 변경에 따른 새 `code_sha256`, 새 `owner_confirmed`가 필요합니다(`:1185-1191`). 이 일은 Step 7A 중에는 할 수 없고, Step 10(⑦-1) 뒤에 일정을 잡습니다.
- 파일럿 1·2가 아직 돌지 않았습니다. 이 단계의 실효성은 UNVERIFIED입니다.
- L1을 필수로 할지, 지원하지 않는 모델은 건너뛰고 그 사실을 기록할지는 결정 20입니다. 소유자가 정하기 전에는 L1을 건너뛴 모델이 소유자 모르게 L2로 가지 않도록, 등록과 기록에 "L1 미적용(브리지 미지원)"을 적습니다.

### 8.3 L2 모의 (H2 형식)

- 첫 모의 세션 전에 모의 가설을 고정합니다. 형식은 H2 `HYPOTHESES`입니다: `frozen`, `alpha_one_sided`, `claim`, `metric`, `test`, `sessions`, `sample`, `rule`, `frozen_with`(`paper_live/config.py:185-221`). 규칙 코드의 사본도 남깁니다(`paper_live/verdict.py:39-65`).
- 숙성: 첫 기록 세션부터 252세션 이상, 소급 기록은 세지 않습니다(`core/quant/tf_gov.py:66`, `:527-553`). 결정 14 전에는 2027-01-01 이후 세션을 세지 않습니다(3.3).
- 통과 기준(PROPOSAL, 결정 13):
  1. 충실도: 모의 손익과 같은 날 재연 손익의 차이가 H1 형식 기준 안에 있습니다(|gap| ≤ max(0.5 × 재연 세션 sd, 바닥 금액); `paper_live/config.py:189-198`).
  2. 비용: 실현 비용(슬리피지 포함)이 표 비용의 2배 이하입니다. 게이트가 견딘 스트레스 범위입니다.
  3. 손실: 최대 낙폭이 등록한 한도 안입니다. 기본 제안은 백테스트 OOS 최대 낙폭의 1.5배입니다.
  4. 성과: 모의 Sharpe의 90% 구간 상한이 헤어컷 기대치(0.6 × OOS Sharpe; `core/quant/validate.py:57`, `core/quant/gate_stats.py:149`) 이상입니다. 이 조건은 큰 실패만 거릅니다. 252세션에서 연 Sharpe의 Lo SE는 약 1.0이라 90% 구간은 ±1.645입니다(`core/quant/validate.py:146-153`). 그래서 모의 Sharpe가 0.6 × OOS Sharpe − 1.645 미만일 때만 실패합니다. OOS Sharpe 1.0이면 −1.05, 0.5면 −1.35입니다. 다른 형태는 결정 13에 적었습니다.
  5. 변경 없음: 숙성 중에 규칙을 바꾸면 숙성을 처음부터 다시 셉니다.
- 모의 단계는 edge를 확증하지 않습니다. 252세션으로는 Sharpe 1.5도 0을 배제하지 못합니다(5.2). paper_live의 H3도 edge 검정을 하지 않고 검정력 줄만 냅니다(`paper_live/config.py:213-218`).
- ⑧-1 H2 판독과의 관계: H2는 "2배 비용 게이트가 없는 같은 규칙보다 덜 잃는다"를 10세션의 단측 짝 t로 검정합니다(`paper_live/config.py:199-212`). 판독이 확인되면 L2의 기본 설정에 2배 비용 게이트를 넣을지 소유자가 정합니다(결정 13). 이 문서는 H2 결과를 예단하지 않습니다.

### 8.4 L3 소규모 실거래

- **장소(결정 12).** 두 문서가 다릅니다.
  - 로드맵 검토: 주문은 TRADEGEN에서만 둡니다(`ROADMAP_REVIEW_2026-10-27.md:52`, `:55`).
  - 2026-11-03 소유자 판정: "QUANTGEN 직접 주문"을 택했고, 원칙을 "주문 경로는 격리된 주문 모듈 한 곳에만 둔다"로 고쳤습니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:552`, `:567`, `:577-593`). 이 모듈은 아직 없습니다.
- **어느 쪽이든 지킬 조건**(위 판정의 안전 조건, `:583-593`): 모의투자 기본, 소유자의 명시적 실거래 전환, 주문 한도, 주문마다 확인, 긴급 중지, 모든 주문의 감사 기록, 연구 원장과 분리. 주문 결과는 연구 판정과 원장에 들어가지 않습니다.
- **법률 검토 선행.** 상업 배포 앱의 주문 기능은 별도 법률 검토가 필요합니다(`:567`; ⑩-1, `REMAINING_WORK_2026-10-27.md:140`).
- **자본과 손실 한도.** 소유자가 정합니다. Claude는 값을 제안하지 않습니다. Moonshot의 $30 상한은 별개의 격리 실험입니다(R4).
- **kill switch 조건(PROPOSAL, 결정 12):** 누적 손실이 한도에 닿음; 실현 비용 > 표 비용의 2배; 모의 대비 괴리가 충실도 기준을 넘음; 데이터 원천 대조 실패(D-1 형식).
- **정기 재평가(PROPOSAL, 결정 12):** 252세션마다 등록한 검정을 그 기간의 새 자료에만 적용합니다. 실패하면 L2로 내립니다. 그 기간은 2027-01-01 이후이므로 결정 14가 먼저입니다.
- **피드백.** 실거래 결과는 읽기 전용 증거 보고서로만 돌아옵니다. 모델을 바꾸려면 L0에서 새로 등록합니다(6.3).

## 9. 소유자 결정

- **소유자 답 (2026-11-04):** 각 항목 아래에 원문으로 적었습니다. 출처는 Geon Koh가 Claude Code 채팅(세션 `session_016uB1jgeiPdP8gPkAez3Wrx`)에 붙여 넣은 결정표 2차 답입니다.
  - 첫 줄 원문: `[QUANTGEN 소유자 결정 2026-11-04 · 2차] 아래는 Geon Koh의 결정입니다. (U6 승인과 A2 확인은 이미 기록됨)`
  - 번호 대응: 결정표의 M-n은 이 절의 결정 n입니다. 원문의 (가), (나)는 결정표의 선택지 글자입니다. 이 절의 하위 목록 글자와 다를 수 있습니다(결정 14).

1. **범위.** 이 기준을 유형 F, S, R, D에 적용하고 P(가격 공식)와 G(판정 장치)는 빼는지(2.2).
   - **소유자 결정 2026-11-04 (M-1).** 원문: `M-1 = (가) 예측·전략·리스크·데이터 원천 변경에 적용, 가격 공식과 판정 장치는 제외 [권고]`
2. **유의수준.** 모든 채택 비교를 단측 α 0.10(QUANTGEN 관례)으로 할지, 현직 교체만 0.05로 할지. 기본 제안은 0.10이고, DSR·PBO·검정력 조건이 함께 걸립니다(4.0). h > 1 예측의 α는 결정 5입니다.
   - **소유자 결정 2026-11-04 (M-2).** 원문: `M-2 = (가) 모든 비교 단측 0.10 [권고]`
3. **⑨-3d 전 전략 DSR의 N.** (가) ⑨-3d까지 새 전략 채택을 보류. (나) G와 원장 N_raw 둘 다에서 DSR ≥ 0.95(제안, 잠정). (다) 지금처럼 G만(4.2.2 S-2). (나)는 ⑨-3c의 검증(DSR 시행 수 정의, 유효 시행 수, 시뮬레이션) 전에 N의 한 읽기(literal, family-wide)를 고르는 것입니다(`research:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:175-176`; `REMAINING_WORK_2026-10-27.md:106`). 그래서 (나)를 고르셔도 ⑨-3c 보고서 전까지 잠정이고, ⑨-3d에서 다시 봅니다. 검증 전에는 어떤 N 읽기도 쓰지 않으려면 (가)입니다.
   - **소유자 결정 2026-11-04 (M-3).** 원문: `M-3 = (나) 격자 수와 원장 N 둘 다에서 DSR ≥ 0.95 (잠정) [권고]`
     - 반영: (나)입니다. 위 설명대로 ⑨-3c 보고서 전까지 잠정이고, ⑨-3d에서 다시 봅니다.
4. **기준전략.** 2.3 표의 계열별 기준전략(V3, V4, B2 포함); SMA-200의 정의(`lookback` 200, `step` 21 제안); 60/40의 구성(SPY 60%, TLT 40%, 21세션 리밸런싱, 표 비용 `us` 제안, 구현 없음)과 KRX 묶음 포함 여부; 여럿일 때 "모두 이김"(제안, S-4)과 "가장 강한 하나" 중 무엇; 롱숏 페어의 기준; 같은 현금 관례로 비교할지. 새 기준전략 코드의 자리와 시점은 결정 21입니다.
   - **소유자 결정 2026-11-04 (M-4).** 원문: `M-4 = (가) 초안 2.3 표 그대로 [권고]`
5. **예측 채택 규칙.** MCS 집합 + DM 우위(제안) 또는 R-30처럼 MCS 집합 + 단순한 쪽 우선만; 중첩 모형의 Clark–West; DM 최소 원점(모든 h에서 500 제안). h > 1의 크기 보정은 셋 중 하나입니다(4.1.2 F-7, 5.4).
   - (가) 단측 α 0.05(제안). 이번 측정의 실제 기각률은 0.063~0.079입니다.
   - (나) 합성 영가설로 보정한 임계값. 이번 설계에서는 t ≤ −1.37~−1.42였지만, 등록마다 손실 분포에 맞춘 보정이 필요하고 새 코드입니다.
   - (다) 비중첩 원점과 h = 1 검정. 비중첩 400개 이상이 필요해 h = 21이면 8,400세션 이상입니다.
   - **소유자 결정 2026-11-04 (M-5).** 원문: `M-5 = (가) MCS 포함 + DM 우위, 최소 500 원점, h>1은 α 0.05 [권고]`
     - 반영: MCS 집합 + DM 우위, 모든 h에서 최소 500 원점입니다. h > 1의 크기 보정은 위 (가) 단측 α 0.05입니다.
     - 중첩 모형의 Clark–West는 결정표 문구에 없습니다.
6. **전략 비교 통계.** 현직(S-3)과 추가 기준전략(S-4) 모두 `gate_stats.lw_studentized_boot`(제안) 또는 기존 `validate.sharpe_diff_bootstrap`; S-7의 검정력 줄이 모자라면 S-3을 INSUFFICIENT_DATA로 둘지(4.2.2).
   - **소유자 결정 2026-11-04 (M-6).** 원문: `M-6 = (가) gate_stats.lw_studentized_boot [권고]`
     - S-7의 검정력 줄이 모자랄 때 S-3을 INSUFFICIENT_DATA로 둘지는 결정표 문구에 없습니다.
7. **테크펀드 규칙의 확장.** SPA 계열 게이트(S-5)와 GOV-7 손익분기 선별(S-6)을 모든 전략 계열에 쓸지.
   - **소유자 결정 2026-11-04 (M-7).** 원문: `M-7 = (가) 모든 계열에 적용`
8. **리스크 모델.** R-2(점수 규칙 비교), R-3(위반 0건 정확 LR, 새 코드 한 줄), R-4(99%는 원점 1,000)(4.3.2).
   - **소유자 결정 2026-11-04 (M-8).** 원문: `M-8 = (가) 초안대로 [권고]`
9. **데이터 원천 변경.** D-1~D-4; D-4의 둘째 원천 평가를 9b 시행으로 셀지(제안: 셈, ⑨-3d에서 달리 정할 수 있음). 일치율 기준값은 ⑤-2 결과를 본 뒤 정합니다(4.4).
   - **소유자 결정 2026-11-04 (M-9).** 원문: `M-9 = (가) 초안대로 [권고]`
10. **국면.** OOS에 닫힌 하락 국면이 하나 이상 있어야 채택하는지(5.5).
    - **소유자 결정 2026-11-04 (M-10).** 원문: `M-10 = (나) 불필요`
      - 반영: OOS에 닫힌 하락 국면이 있어야 채택하는 조건은 두지 않습니다.
11. **경계.** 경계 구간의 정의(게이트 밖 비교 p, S-2의 둘째 DSR, MCS p; PBO 제외)와 "경계는 채택하지 않음"(6.2).
    - **소유자 결정 2026-11-04 (M-11).** 원문: `M-11 = (가) 경계 구간 정의 승인, 경계는 채택하지 않음 [권고]`
12. **실거래 장소와 한도.** TRADEGEN만(로드맵 검토 D1·E2) 또는 QUANTGEN 격리 주문 모듈(2026-11-03 판정); 자본 한도, 손실 한도, kill switch 조건, 252세션 정기 재평가(8.4).
    - **소유자 결정 2026-11-04 (M-12).** 원문: `M-12 = (가) QUANTGEN 격리 주문 모듈(11-03 결정과 일치). 자본·손실 한도와 kill switch는 주문 설계 때 정함 [권고] | 메모: (가) 옵션에서 QUANTGEN은 TRADEGEN처럼 AI기반 모듈로  한도 내 능동적으로 전략을 설계해서  운영하는 방식이 아닌, 일반적인 거래소(예. 미래에셋증권 MTS 등)처럼 구현하고 싶습니다. 따라서 뒷부분이 필요하지 않을 것 같습니다`
      - 반영: 실거래 장소는 QUANTGEN 격리 주문 모듈입니다(2026-11-03 판정과 같음).
      - 메모: QUANTGEN의 주문 모듈은 TRADEGEN처럼 AI 모듈이 한도 안에서 전략을 스스로 설계해 운영하는 방식이 아닙니다. 일반 거래소 앱(예: 미래에셋증권 MTS)처럼 만듭니다.
      - 메모에 따라 (가)의 뒷부분 "자본·손실 한도와 kill switch는 주문 설계 때 정함"은 필요하지 않은 것으로 적습니다. 8.4의 "자본과 손실 한도"와 "kill switch 조건(PROPOSAL)"이 이 부분입니다. 8.4 본문은 이번에 고치지 않았습니다.
      - 8.4의 다른 항목(2026-11-03 판정의 안전 조건, 252세션 정기 재평가)은 결정표 문구에 없습니다.
13. **승격 단계와 모의 단계.** L0~L3의 구조와 L0의 승인 방식(8.1); 숙성 252세션; 통과 기준 다섯 가지(충실도, 비용, 낙폭 1.5배, 헤어컷 대비, 변경 없음); H2 판독(⑧-1) 뒤 2배 비용 게이트를 기본으로 넣을지(8.3). 4번 성과 조건의 형태는 셋 중 하나입니다.
    - (가) 지금 형태. 큰 실패만 거르고, 실패선은 0.6 × OOS Sharpe − 1.645입니다.
    - (나) 0.6 × OOS Sharpe에 대한 단측 α 0.10 검정. 실패선은 0.6 × OOS Sharpe − 1.28입니다. 실제 Sharpe가 기대보다 0.6 낮아도 252세션에서 잡을 확률은 약 0.25입니다.
    - (다) 4번을 빼고 1~3, 5만 봅니다.
    - **소유자 결정 2026-11-04 (M-13).** 원문: `M-13 = (나) 0.6×OOS Sharpe에 대한 단측 0.10 검정`
      - 반영: 8.3의 4번 성과 조건은 위 (나)입니다. 실패선은 0.6 × OOS Sharpe − 1.28입니다.
      - 결정표 M-13은 4번의 형태만 물었습니다. 결정 13의 나머지(L0~L3 구조와 L0 승인 방식, 숙성 252세션, 나머지 통과 기준, H2 판독 뒤 2배 비용 게이트)는 결정표 문구에 없습니다.
14. **잠금 홀드아웃(2027-01-01 이후 자료).** 결정 전에는 3.3의 처리를 따릅니다(표본 끝 ≤ 2026-12-31, HOLDOUT_TOUCHED는 ADOPT 불가, L2·L3 시작 안 함).
    - (가) 그 자료를 확증 평가에 한 번 쓸 수 있는지, 쓴다면 언제 어떻게(3.3).
    - (나) L2 모의 숙성과 L3 정기 재평가가 그 뒤 세션을 세도 되는지. 테크펀드처럼 별개의 시계로 둘지(D-23 선례, `core/quant/tf_gov.py:65`).
    - (다) 그 뒤 자료에서 본 L2·L3 실패, 경계, INSUFFICIENT_DATA 뒤에 무엇을 할 수 있는지. 중지와 강등만 하는지, 새 등록으로 고칠 수 있는지.
    - (라) 2027년의 L0 실행. 표본 끝을 2026-12-31로 묶어 두는 지금의 처리를 계속할지.
    - **소유자 결정 2026-11-04 (M-14).** 원문: `M-14 = (가) 지금 처리 유지: 평가 표본은 2026-12-31에 끝냄, 모의·실거래 단계 시작 안 함. 따로 검토 [권고]`
      - 결정표의 선택지 글자는 이 항목의 하위 질문 글자와 다릅니다. 결정표 (가)는 3.3의 지금 처리를 유지하는 선택이었습니다. 결정표 (나)는 "모의 숙성은 별도 시계로 허용(테크펀드 D-23 선례)"이었습니다.
      - 반영: 평가 표본은 2026-12-31에 끝납니다. L2·L3는 시작하지 않습니다. 하위 질문 (가)~(라)는 "따로 검토"로 남습니다.
15. **등록 파일.** 위치(`docs/adoption/registrations/<card_id>.json` 제안)와 형식(3.2의 12개 항목), 그리고 승인 뒤 등록하는 모델에만 적용(소급 없음)(3.4).
    - **소유자 결정 2026-11-04 (M-15).** 원문: `M-15 = (가) docs/adoption/registrations/<card_id>.json, 승인 뒤 등록하는 모델부터(소급 없음) [권고]`
      - 등록 형식(3.2의 12개 항목)은 결정표 문구에 따로 없습니다.
16. **공통 골격.** 4.0의 규칙 1~5(S-1을 필요조건으로 두는 것 포함); 결과 이름 ADOPT·KEEP(6.1); 3.2 8번(다른 유형의 검정력 줄)과 9번(판정 규칙); 6.4 표의 처리.
    - **소유자 결정 2026-11-04 (M-16).** 원문: `M-16 = (가) 초안대로 [권고]`
17. **짧은 기록의 DSR REJECT.** 게이트 REJECT의 사유가 DSR < 0.95 하나뿐이고 세션 수가 `min_track_record`보다 적을 때(5.2). 카드 판정은 어느 쪽이든 REJECT 그대로입니다.
    - (가) 채택에서도 REJECT로 끝냅니다. 새 자료로 다시 보려면 새 등록입니다(제안).
    - (나) 채택에서는 INSUFFICIENT_DATA로 보고, 등록 뒤 자료로만 같은 검정을 다시 합니다. 그 자료가 2027-01-01 이후면 결정 14가 먼저입니다.
    - **소유자 결정 2026-11-04 (M-17).** 원문: `M-17 = (가) 채택에서도 REJECT. 다시 보려면 새 등록 [권고]`
18. **예측·리스크 변형의 시행 계수.** F-9, R-7: 평가 전 등록과 원장 행; MCS 후보와 Holm 묶음은 등록한 변형 전부(4.1.2, 4.3.2).
    - **소유자 결정 2026-11-04 (M-18).** 원문: `M-18 = (가) 초안대로 [권고]`
19. **추가와 교체.** 등록에 추가·교체를 적게 할지(3.2 12번); 교체는 S-3이 INSUFFICIENT_DATA면 교체하지 않음; 추가는 S-1, S-2, S-4로 판단(4.2.2).
    - **소유자 결정 2026-11-04 (M-19).** 원문: `M-19 = (가) 초안대로 [권고]`
20. **L1 엔진 재계산.** 지금은 두 파일럿 설정만 지원합니다(8.2).
    - (가) 필수. 브리지가 지원하지 않는 모델은 브리지 확장(⑦-1 뒤) 전까지 L2로 가지 않습니다.
    - (나) 지원하지 않으면 건너뛰고, 등록과 기록에 "L1 미적용(브리지 미지원)"을 남깁니다(제안).
    - **소유자 결정 2026-11-04 (M-20).** 원문: `M-20 = (나) 지원하지 않으면 건너뛰고 "L1 미적용"으로 기록 [권고]`
21. **새 계산의 자리와 시점.** 1.3의 해시 대상 파일 밖 새 모듈에 둘지(위치는 소유자가 지정, 예: `core/adoption/`); Step 7A.3 커밋과 병합 동결 해제 전에는 만들지 않을지(7절). 여기에 드는 것은 S-2의 원장 N DSR, S-3·S-4의 LW 검정, S-5 SPA, 새 기준전략(SMA-200, 60/40), R-3의 정확한 LR입니다.
    - **소유자 결정 2026-11-04 (M-21).** 원문: `M-21 = (가) Nautilus 지문 대상 밖의 새 모듈(예: core/adoption/), 7A.3과 동결 해제 전에는 만들지 않음 [권고] | 메모: 동결 해제 및 7A.3 완료한 점 참고해주세요.`
      - 반영: 새 계산 코드는 Nautilus 지문(1.3의 해시 대상 파일) 밖의 새 모듈에 둡니다. 결정표 문구의 `core/adoption/`은 예시입니다.
      - 메모에 따라 두 조건은 이미 채워졌습니다. 모두 통과한 7A.3 묶음 커밋은 연구 브랜치 `563db54`입니다. main 병합 동결은 소유자 결정 U4 (나)로 풀렸습니다(main `24e9ece`, PR #70 병합 `f455710`). 그래서 이 모듈은 지금 만들 수 있습니다.
      - 2.3과 7절에서 새 모듈을 Step 7A.3 커밋과 병합 동결 해제 전에는 "만들지 않습니다"라고 한 서술은 결정 전의 것입니다.
22. **⑪-1과의 관계.** 이 문서의 2.3절과 8절을 기준전략과 승격 기준의 단일 출처로 하고 남은 ⑪-1 작업이 이를 인용할지(제안), 아니면 ⑪-1이 맡을지(1.3).
    - **소유자 결정 2026-11-04 (M-22).** 원문: `M-22 = (가) 이 문서를 기준전략·승격 기준의 단일 출처로 하고 ⑪-1이 인용 [권고]`

## 10. 근거 목록

### 10.1 이 커밋(`bb35b3b`)의 코드와 설정

| 파일 | 줄 | 쓴 곳 |
|---|---|---|
| `core/quant/validate.py` | `:50` DECISIONS; `:53-74` GATE; `:59-66` PBO 근거 주석; `:78` 비용표; `:87-112` `cost_class`; `:146-153` Lo SE; `:156-160` 최소 기록; `:163-183` Sharpe 구간; `:186-208` 짝 ΔSharpe; `:211-237` DSR; `:240-265` PBO; `:273-292` NW t, DM; `:345-381` walk-forward; `:440-452` 국면 분할; `:492-533` `score_strategy`(`:493`, `:520-521` 벤치 하나); `:536-622` 판정 순서(`:592-596` REJECT, `:606-611` INSUFFICIENT_DATA); `:628-663` Kupiec, Christoffersen, 신호등; `:713-722` CRPS; `:741-796` 분포 판정; `:803-834` `ModelCard` | 4.2, 4.3, 5.1, 5.2, 5.4, 6, 7, 8.3 |
| `core/quant/forecast_eval.py` | `:43-46` 상수; `:61-91` 등록(`:76-86` `register_forecast`); `:113-116` tick loss; `:147-156` DM(`:150` HAC 시차); `:159-165` CW; `:168-189` GW; `:203-243` MCS; `:354-400` B5; `:523-582` Stage 1~3; `:685-721` 교체 증명(`:704-717` 원장 행 요구) | 4.1, 4.3, 5.1, 5.4 |
| `core/quant/gate_stats.py` | `:123-137` STATS; `:139-152` 상수; `:284-336` LW SE와 부트스트랩; `:342-356` PW 블록; `:426-488` 검정력, UNDERPOWERED; `:515-529` Holm | 4.2, 5.3 |
| `core/quant/gate_ledger.py` | `:57-61` 실행 종류, 행 키; `:76` 최소 공통 관측; `:79` 매크로 계열; `:114-119` 기준점; `:333-334` N_raw; `:379-386` 등록; `:574-582` N_eff; `:736-746` 헤더 검사; `:748-813` step 3; `:818-826` 개정(`bump_revision`) | 2.1, 3, 4.2, 6.3 |
| `core/quant/tf_gov.py` | `:58-68` 상수(`:65` D-23 시계); `:257-291` SPA; `:313-333` 계열 게이트; `:431-442` 손익분기; `:455-480` 스트레스 표; `:527-553` 숙성 | 3.3, 4.2, 5.1, 8.3, 9 |
| `core/quant/lab.py` | `:67-69` M9 기준; `:617-650` `m9_gate` | 4.3 |
| `core/quant/cardp.py` | `:54-72` CARD-P 상수; `:158` 비교 북 S; `:344-357` PC-7; `:421-466` 국면 | 2.3, 5.1, 5.5 |
| `core/quant/gate_package.py` | `:36-38` 하네스 소스; `:241-255` 새 패키지 버전 | 1.3, 7 |
| `core/quant/strategies.py` | `:162` `trend_switch`(기본 lookback 210) | 2.3 |
| `core/quant/vol_estimators.py` | `:34` 추정기 목록 | 2.2 |
| `core/quant/history.py` | `:333-335` `_looks_crypto` | 6.4 |
| `core/research/strategy_workflow.py` | `:17-29` 계열과 격자; `:36-63` 원장 등록; `:65-117` `run_family`(`:97-98` 계산 뒤 등록, `:99` 비교 대상, `:104-109` B 덮어쓰기, `:107` N = G) | 2.3, 4.2, 6.4 |
| `docs/asset_expansion_study.py` | `:173-210` 카드 작성; `:182`, `:207` 시행 수; `:243-244` US·KRX 슬리브; `:274` E1 격자; `:275`~`:383` 계열별 비교 대상; `:339-343` C3 N = 11; `:391-431` FX 카드와 캐리 지수 벤치(`:425-431`); `:478-496` B2 자체 기준 | 2.3, 4.2 |
| `docs/techfund_study.py` | `:83` CRY-1 대조 시행 | 2.3 |
| `data/macro/rules_v2.0.0.json` | `:749-838` R-30 추정기 게이트(`:795-813` Stage 3, `:796` 목표, `:803` 동률 규칙); `:1566` 게이트 패키지 상태; `:1573-1574` CARD-P 비교 북; `:2036-2041` 등급 A; `:2063` `locked_holdout_start` | 3.2, 4.1, 5.1, 7 |
| `paper_live/config.py` | `:179-221` H1·H2·H3 가설과 시행 규칙(`:199-212` H2, `:213-218` H3) | 3, 6.3, 8.3 |
| `paper_live/verdict.py` | `:1-18` 판정 순서; `:39-65` 고정과 사본 | 3.1, 8.3 |
| `tools/status/section10_probes.py` | `:27-31` 위반 0건의 정확한 LR 기준 계산 | 4.3.2 R-3 |
| `research_notes/QUANTGEN v2 integration map/tf_core_link.md` | `:334` D-23(두 시계) | 3.3 |
| `README.md` | `:78-83` 동결 연구와 태그 | 4.4, 7 |
| `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md` | `:43` A2; `:47` C1; `:48` C2; `:52` D1; `:54` E1; `:55` E2; `:169` ⑨-4; `:173` ⑪-1 | 1, 3.3, 3.5, 8.4 |
| `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` | `:100` ③-5 완료 기준; `:106` ⑨-3c; `:118-122` ⑧-1, ⑧-3, ⑨-3d, ⑧-2; `:132` ⑤-2; `:133` ⑥-1; `:138` ⑨-4; `:140` ⑩-1 | 1.1, 3, 7, 8, 9 |
| `docs/product/TRADEGEN_READ_ONLY_BRIEF_2026-10-29.md` | `:1-20` 브리프 v1 전체; `:13-14` 피드백 제어 | 1.3, 6.3 |

`paper_live/config.py`와 `paper_live/verdict.py`는 태그 `studies-of-record-2026-10-23`과 `bb35b3b` 사이에 바뀌지 않았습니다(`git diff --stat`, 출력 없음). 두 파일은 읽기만 했습니다.

### 10.2 연구 브랜치(`0bc9595`)와 인계 장부의 문서

| 파일 | 줄 | 쓴 곳 |
|---|---|---|
| `docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md` | `:19-27` 모델 정의; `:61` 독립 검증됨; `:141-145` 카드 판정 분포와 C3; `:821` N-M1-01; `:1093` CRY-1; `:1172` 벤치 p 근사; `:1230` 고원 규칙; `:1231` 짧은 기록의 DSR REJECT; `:1235` N9; `:1275` N8; `:3111` R-30 운영 미가동 | 2, 4, 5, 6 |
| `docs/nautilus_bridge/KNOWN_ERRORS_REGISTER_2026-10-28.md` | `:869` K-c; `:870` K-d; `:872` K-f; `:1758` N12 | 6.4 |
| `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md` | 3.12~3.15(`:293-351`); 4.2 5·7·7b·9a·9b·10·16행(`:409`, `:411`, `:413`, `:418-419`, `:420`, `:427`); 네 조건(`:429-438`); Lab 확증 불가(`:440-442`); 위험 16 잠금 홀드아웃(`:1648`); 10.2(`:1650-1685`) | 2.1, 3, 4.2, 4.4, 6.3, 7 |
| `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | `:160-165` R2; `:167-185` R3(`:175-176` ⑨-3c 뒤 결정); `:318-336` 원장 행 수 보고(C3 17행 `:327-334`); `:417` ②-5 승인; `:542`, `:560` R3 10.2 A 승인; `:552`, `:567`, `:577-593` 주문 원칙 개정; `:568` 공식 원장 기록 개별 승인 | 1, 3.5, 4.2, 6.3, 7, 8.4, 9 |
| `docs/nautilus_bridge/registration/pilot1_E1_spy.json` | `:11` 자료 해시; `:39-40` 가설과 `claim_label` | 3.1, 3.3 |
| `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` | `:859-872` 패리티 검사(hard: P0~P4, P7, P12, P13); `:1126`, `:1176` `pilot` 값; `:1185-1191` `code_sha256` 범위; `:1502` Claude의 자료·원장 제한; `:1713-1721` 범위 밖 | 1.3, 2.3, 3.5, 4.2 S-8, 7, 8.2 |
| `origin/handoff`의 `LEDGER.md`(`9c0d782`) | `:57` ⑪-1/a | 1.3 |

등록표 JSON은 필드 이름과 위 세 줄만 읽었습니다. 등록표가 가리키는 가격 파일은 열지 않았습니다.

### 10.3 이번 측정

- 스크립트(저장소 밖, 초판): `/tmp/claude-0/-home-user-quantgen/e3190f47-39b0-503d-b10e-e028fba25280/scratchpad/t94_check/power_check.py`(md5 `582c429cda8b6b68247a85478362bcfb`), `/tmp/claude-0/-home-user-quantgen/e3190f47-39b0-503d-b10e-e028fba25280/scratchpad/t94_check/dm_size.py`(md5 `dd4852bfb01981c29f45e952a907353f`, 5.4 초판 표. 이번 개정에서 대체).
- 스크립트(저장소 밖, 개정):
  - `/tmp/claude-0/-home-user-quantgen/e3190f47-39b0-503d-b10e-e028fba25280/scratchpad/t94_check2/dm_rule_level_v2.py`(md5 `7e5dc2958c9935e17803092f044860da`): 5.4 표. 인자 `5000`, 시드 11, 20261104, 99.
  - `/tmp/claude-0/-home-user-quantgen/e3190f47-39b0-503d-b10e-e028fba25280/scratchpad/t94_check2/dm_rule_level.py`(md5 `d381187f4844138a6e20406cad584b89`): 같은 설계를 칸마다 6,000회로 먼저 돌린 것. 결과가 5.4 표와 몬테카를로 오차 안에서 같았습니다.
  - `/tmp/claude-0/-home-user-quantgen/e3190f47-39b0-503d-b10e-e028fba25280/scratchpad/t94_check2/bartlett_bias.py`(md5 `10047b1480670abf2db33100cc6b8b04`): 자료 없는 결정적 계산. Bartlett 기대 장기분산 비율과 그것이 뜻하는 기각률.
  - `/tmp/claude-0/-home-user-quantgen/e3190f47-39b0-503d-b10e-e028fba25280/scratchpad/t94_check2/dsr_check.py`(md5 `45927c3857ca1d9c00134919e56274bf`): 5.2의 DSR 0.868.
- 환경: 별도 venv의 Python 3.13.18, numpy 2.3.5, scipy 1.18.0, pandas 2.3.3. `python -I -B`, `env -i`로 새 빈 HOME과 TMPDIR, 바이트코드 쓰기 끔. 이 클론의 추적 파일은 바뀌지 않았습니다(`git status`에 이 문서만 있음).
- 자료: 모두 합성입니다. 가격 자료, 원장, 네트워크는 쓰지 않았습니다. 저장소 코드 모듈만 불러왔습니다.
- 불러 쓴 함수: `validate.min_track_record`, `validate.deflated_sharpe`, `validate.sharpe`, `gate_stats.lw_hac_se`, `gate_stats.MDE_FACTOR`, `forecast_eval.dm_test`, `forecast_eval.mcs`.
- 결과: 5.2, 5.3, 5.4의 표와 문장. MCS 장난감 예제(모델 B가 손실 0.5만큼 나쁨, B 500)에서 B만 집합 밖(p 0.0)이고 A(p 1.0), C(p 0.556)는 집합 안이었습니다. 멤버십 규칙(p ≥ 0.10)이 코드대로 작동함을 확인한 것이고, 크기나 검정력의 검증은 아닙니다.

### 10.4 UNVERIFIED 목록

- 실데이터에서의 ΔSR SE(5.3)와 QLIKE 손실에서의 DM 기각률(5.4). 변동성이 지속되는 손실에서 h > 1의 편향이 더 큰지.
- MCS의 크기와 검정력.
- Nautilus 패리티가 실제 파일럿에서 통과하는지(S-8, L1).
- ⑤-2 공급사 대조 도구의 이름, 출력, 기준값(D-1).
- L2 모의 기록 도구(3.5). 아직 없습니다.
- ⑧-2(2026-10-27) 뒤에도 D-23의 "두 시계" 선례가 그대로인지(3.3).
- QUANTGEN 격리 주문 모듈의 설계와 안전 검사(L3). 모듈은 아직 없습니다.
- 연구 브랜치 문서의 줄 번호는 `0bc9595` 기준입니다. `main` 병합 뒤 달라질 수 있습니다.
- 소유자 PC의 원장 행 수는 2026-10-28 보고(C3 17행, E1 없음)만 보았습니다. 이 세션은 원장을 열지 않았습니다.

### 10.5 개정 기록 (2026-11-04, 검토 의견 반영)

| 범위 | 바꾼 것 |
|---|---|
| 잠금 홀드아웃 | L2, L3, 경계·INSUFFICIENT_DATA 재평가, 2027년 L0 표본을 결정 14에 묶었습니다. 결정 전 처리(표본 끝 ≤ 2026-12-31, HOLDOUT_TOUCHED는 ADOPT 불가)를 3.3에 적고, 결정 14를 넓혔습니다 |
| 실행 주체 | 3.5와 8.1에 실행 주체를 적었습니다. D-1에 소유자 PC 실행을 적었습니다 |
| 5.2 | 게이트는 짧은 기록의 Sharpe 0.5 전략을 REJECT로 냅니다. 고치고 결정 17을 더했습니다 |
| 5.4, F-7 | F-2 판정 수준으로 칸마다 15,000회 다시 쟀습니다. "원점 2,000" 기준을 빼고 h > 1은 α 0.05를 제안했습니다. 결정 5에 대안을 더했습니다 |
| D-2, D-4 | R3 9a·9b행을 그대로 따르게 고쳤습니다 |
| 1.3, 7 | `code_sha256`에 드는 파일을 더하고, 새 코드의 자리와 시점을 결정 21로 뒀습니다 |
| S-8, L1 | 브리지는 두 파일럿만 지원함을 적고 hard 검사에 P12, P13을 더했습니다. 결정 20을 더했습니다 |
| F-9, R-7 | 예측·리스크 변형의 사전 등록과 원장 행을 더했습니다(결정 18) |
| 추가·교체 | 3.2 12번과 4.2.2의 두 경우를 나눴습니다(결정 19) |
| 결정 번호 | 번호 없던 PROPOSAL에 결정 16 등을 붙였습니다. 결정은 22건입니다 |
| 6.1, 6.2 | KEEP을 게이트 밖 비교로 한정하고, DSR 경계를 S-2의 둘째 DSR로 한정하고, PBO를 경계에서 뺐습니다 |
| S-4 | 추가 기준전략은 LW 검정으로 봅니다 |
| 3.1, 6.3 | 설정 변경(새 시행)과 가설 변경(계수된 개정)을 나눴습니다 |
| 4.1.1 | R-30 Stage 3의 목표(63일 vol-of-vol 최소)를 더했습니다 |
| 8.3 | H2를 H3로 고치고, 성과 조건의 실패선을 적었습니다(결정 13) |
| 2.3 | V3, V4, B2 행과 SMA-200, 60/40의 정의를 더했습니다 |
| 결정 3 | (나)를 ⑨-3c 보고서 전까지 잠정으로 했습니다 |
| R-3 | 기준 계산의 위치를 적고 새 코드임을 밝혔습니다 |
| 인용 | `gate_package.py:36-38`, `verdict.py:39-65`, `config.py:185-221`, 비중첩 원점 수(24, 96, 239)를 고쳤습니다 |
| ⑪-1 | 겹침을 1.3에 적고 결정 22를 더했습니다 |
