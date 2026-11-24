# DIDM-2 채점기 계약 V0 (`didm-judgement-v0`)

- 작성: DIDM_DEV 세션, 2026-11-24. 코드: `core/didm/llm/judgement.py`, `core/didm/llm/scorer.py`. 시험: `tests/didm_contract_acceptance.py` (네트워크·모델 호출 없음).
- 이 문서는 **형식**만 정합니다. 문턱·모수는 `docs/didm/PREREG_V0.md`(동결)가 정하고, 레코드 형식은 `docs/didm/SCORE_SCHEMA_V0.md`가 정합니다. `core/didm/llm/schema.py`는 이 작업에서 바꾸지 않았습니다.

## 1. 왜 둘로 나누나

`didm-score-v0` 레코드에는 언어 모델이 만들 수 없는 값이 있습니다 (참신성 모형 출력, 원출처 묶음, 신뢰 상태, 시장 확인, 수신 시각). 그래서 모델이 내는 부분을 **판단(judgement)** 으로 따로 정하고, 레코드는 DIDM이 조립합니다. LLM, 자체 LLM, FinBERT, Loughran-McDonald 사전이 모두 같은 판단 형식을 내므로 같은 자로 비교할 수 있습니다 (사전등록 6절 절제 순서).

```
ScoreRequest ─▶ Scorer.judge() ─▶ 판단(JSON) ─▶ validate_judgement()
                                                     │
참신성·군집·신뢰·시장 확인·저장소 시각 ─────────────▶ assemble_record() ─▶ validate_record() ─▶ ScoreRecord
```

## 2. 채점기가 받는 것: `ScoreRequest`

| 필드 | 값 |
|---|---|
| `article_id` | 식별자 |
| `language` | `en` / `ko` |
| `title` | 비어 있지 않은 문자열 |
| `body` | 문자열 또는 null (제목만 오는 수집원) |
| `target_kind`, `entity_id` | 레코드와 같음. `none`이면 `entity_id`는 null |
| `entity_name` | 모델에 보여 주는 이름. 종목명을 가린 프롬프트면 가린 값 (사전등록 5절 4번). `none`이면 null |

기사 글은 요청 안에서만 쓰이고 판단·레코드·거부 기록에는 들어가지 않습니다.

## 3. 채점기가 내는 것: 판단 9개 필드

모르는 필드가 있거나, 필드가 빠지거나, 범위를 벗어나면 **고치지 않고 거부**합니다 (`JudgementError`, `SchemaError`의 하위). 검증에는 **요청이 꼭 필요합니다** (`validate_judgement(raw, request)`): 레코드의 대상은 언제나 DIDM이 물은 대상이고 모델이 고른 대상이 아닙니다. 거부 사유는 규칙과 필드 이름만 담은 고정 문구이고 모델 출력 값은 들어가지 않습니다 (기사 글이 사유에 섞이지 않게).

| 필드 | 형식 | 규칙 |
|---|---|---|
| `judgement_version` | `didm-judgement-v0` | 다르면 거부 |
| `article_id` | 식별자 | 요청 값과 같아야 함 |
| `target_kind`, `entity_id` | 레코드와 같음 | 요청 값과 같아야 함 (다른 기사·다른 대상의 판단을 붙이지 않음) |
| `p_subject` | 0~1 | 대상이 기사의 주제일 확률, 보정 전 원값. 대상이 없으면 0 |
| `event_type` | 15개 값 중 하나 | `event_type_probs`에서 확률이 가장 큰 키. 정확히 같은 값의 동률일 때만 그중 하나를 고를 수 있음 (오차 허용 없음) |
| `event_type_probs` | 15개 키 전부 | 각 0~1, 합 1 (오차 1e-6) |
| `direction_probs` | [P(+1), P(−1), P(0)] | 각 0~1, 합 1 (오차 1e-6), 그리고 P(+1) + P(−1) ≤ 1 (오차 1e-9, 레코드 스키마와 같은 조건). 보정 전 원값 |
| `claim_status` | `reported` / `confirmed` | 정답 집합 `GoldLabel.claim_status`와 같은 값 |

자유 서술 (근거 문장 등)은 받지 않습니다.

## 4. 채점기 자체 정보: `ScorerInfo`

모델 출력이 아니라 채점기 래퍼가 고정값으로 줍니다: `model_version` (고정 스냅샷 ID, `MODEL_CUTOFFS.md`의 키), `prompt_sha256` (프롬프트가 없는 채점기는 고정 설정 글의 해시), `temperature` (0이 아니면 거부, 사전등록 5절 7번).

## 5. 레코드 17개 필드의 출처

| 출처 | 필드 |
|---|---|
| DIDM 조립 (`Assembly`의 `ASSEMBLY_FIELDS`) | `record_id`, `source_id`, `published_at`, `received_at`, `relevance_0_100`, `novelty_0_100`, `origin_cluster_id`, `p_credibility`, `market_confirmation` |
| 조립 때 계산 | `ess_like_0_100`, `uncertainty_entropy` (보정된 `direction_probs`에서) |
| 판단에서 복사 | `target_kind`, `entity_id`, `event_type`, `direction_probs` (보정기를 주면 보정된 값) |
| `ScorerInfo` | `model_version`, `prompt_sha256` |

- `Assembly`에는 위 9개 값 말고 그 값들을 계산한 대상 (`article_id`, `target_kind`, `entity_id`)도 들어갑니다. 판단과 다르면 `assemble_record`가 거부합니다 (다른 기사·다른 종목의 참신성·관련성 값이 붙는 것을 막음).
- 너무 큰 정수처럼 실수로 바꿀 수 없는 숫자는 판단에서도 조립에서도 거부로 셉니다 (묶음 전체가 멈추지 않음).
- `p_subject`는 레코드에 그대로 들어가지 않습니다. 관련성 모형 (사전등록 4.1절, y = `is_subject`)의 설명변수이고, `relevance_0_100`은 그 모형의 출력입니다.
- 보정: `assemble_record(..., calibrate_direction=함수, calibration_version="...")`. 보정기 없이 조립하면 원값이 들어가고 곁기록의 `calibration_version`이 `uncalibrated`입니다 (보정 전 확률은 순위로만, 사전등록 1절 A3).
- **알려진 틈:** 사전등록 5절 7번은 보정 지도 버전을 기록마다 남기라고 하는데 `didm-score-v0`에는 그 필드가 없습니다. 지금은 `Assembled.calibration_version`으로 레코드 옆에 둡니다. 레코드 필드로 넣는 것은 새 스키마 버전입니다 (미결, 메인 판단).

## 6. 다른 저장소·다른 언어에서 쓰기

`docs/didm/schema/didm-judgement-v0.schema.json`, `didm-score-v0.schema.json` (JSON Schema 2020-12). 코드에서 만들어 내며 손으로 고치지 않습니다.

```
python -B -m tools.didm.export_schema            # 다시 만들기
python -B -m tools.didm.export_schema --check    # 코드와 같으면 종료 코드 0
```

식별자·해시 패턴은 끝에 `(?!\n)`을 붙여 내보냅니다. 파이썬 검증기는 전체 일치로 보지만 JSON Schema 검증기는 부분 검색을 하므로, 끝에 줄바꿈이 붙은 값이 통과하지 않게 한 것입니다.

JSON Schema로 쓸 수 없는 규칙 (합 1, ESS·엔트로피 일치, 요청과 같은 대상, 최대 확률 유형)은 파일의 `x-didm-cross-field-rules`에 글로 적혀 있고, 판정 기준은 파이썬 검증기와 적합성 예시입니다.

## 7. 적합성 예시

`tests/fixtures/didm/conformance/accept/` 11개 (레코드 6, 판단 5), `reject/` 43개 (레코드 21, 판단 22). 거부 예시마다 `expect` (오류 글의 일부)와 `json_schema_detects` (JSON Schema만으로 잡히는지)가 있습니다. 판단 적합 예시에는 **기대 레코드 (`expected_record`)** 가 있어 조립 결과를 필드 하나하나 비교합니다 (기대값은 조립 함수를 부르지 않고 따로 계산해 적은 값). 경계 예시: 합이 1에서 5e-7 벗어난 것은 통과, 2e-6 벗어난 것은 거부. 글은 모두 합성입니다. 새 채점기는 이 예시를 통과해야 합니다.

```
python -B -m unittest tests.didm_contract_acceptance tests.didm_schema_acceptance
```

2026-11-24 (검토 반영 뒤): 계약 43 + 스키마 26 통과.
