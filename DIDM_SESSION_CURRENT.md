# DIDM_DEV 세션 인계 문서

- session: DIDM_DEV (https://claude.ai/code/session_016uB1jj8iv57xVbx6EbLLwq), 메인: QUANTGEN/MAIN (session_01H6RrzMUzF8vwK8xkX977mB)
- updated_at: 2026-11-24 (KST)
- work_branch: `claude/didm-dev-20261124` (main b872d8c에서 시작), work_commit: `ba28b02`
- PR: 없음 (MERGE_QUEUE에 "병합: DIDM_DEV"가 적힌 뒤에만 엶). 원장은 메인이 씀.

## 0. 소유자 지시 원문 (2026-11-24, 메인 세션 전달)

> 기존의 OS확장, Payment, Data Sourcing과 더불어 DIDM 개발, 그리고 아래에서 설명할 자체 LLM에 대한 세션도 하부 세션에 분리하여 추가해주세요.

데이터 수집은 DATA_SOURCE 세션, DIDM 모형은 이 세션, 자체 LLM은 QUANTGPT 세션.

## 1. 경계 (한 경로는 한 세션만)

이 세션: `core/didm/llm/**`, `core/didm/novelty.py`, 새 `core/didm/{sim,models,eval,calibration,credibility,entities,baselines}/`, 새 `tools/didm/` 스크립트, `tests/didm_{schema,novelty}_acceptance.py`와 새 `tests/didm_*`, `docs/didm/PREREG_V0.md`(동결, 고치지 않음)·`SCORE_SCHEMA_V0.md`·새 문서. `core/didm/{ingest,store}/**`, `data/didm/**`, 공유 파일(`runtime-smoke.yml`, `docs/compliance/*`, `requirements.txt`, `pyproject.toml`)은 직접 고치지 않음.

## 2. 한 일

| ID | 상태 | 커밋 | 검사 |
|---|---|---|---|
| DIDM-2 채점기 계약 | 끝 (push) | ba28b02 | `python -B -m unittest tests.didm_contract_acceptance tests.didm_schema_acceptance` → Ran 56 OK; `python -B -m tools.didm.export_schema --check` → 종료 0; `git diff origin/main -- core/didm/llm/schema.py` 비어 있음 |
| DIDM-3 모델 학습 마감일 목록 | 다음 | — | — |
| DIDM-4 Stage 0 모의실험 | 그다음 | — | — |

DIDM-2 내용: 판단 `didm-judgement-v0` 9개 필드 (`core/didm/llm/judgement.py`), 채점기 인터페이스·레코드 조립 (`core/didm/llm/scorer.py`), JSON Schema 2개 (`docs/didm/schema/`), 적합성 예시 accept 10·reject 34, 문서 `docs/didm/SCORER_CONTRACT_V0.md`.

## 3. 열린 것

- 보정 지도 버전: 사전등록 5절 7번은 기록마다 남기라고 하나 `didm-score-v0`에 필드가 없음. 지금은 `Assembled.calibration_version` 곁기록. 레코드 필드 추가는 새 스키마 버전 (메인 판단).
- PR 때 필요한 공유 파일 변경 (지금은 하지 않음): `.github/workflows/runtime-smoke.yml`의 시험 목록에 `tests.didm_contract_acceptance` 추가, `docs/compliance/source-review.json` 기준선 갱신.
- 이 컨테이너에는 scipy가 없음. DIDM 코드는 numpy와 표준 라이브러리만 씀.

## 4. 이어받는 법

```
git clone --no-checkout <origin> w && cd w
git sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
git checkout claude/didm-dev-20261124 && test ! -e docs/asset_expansion/cache
python -B -m unittest tests.didm_contract_acceptance tests.didm_schema_acceptance tests.didm_novelty_acceptance
```

하지 말 것: 보호 캐시·`.env` 열기, 유료·모델·공급사 호출, 모델 내려받기, 실제 가격으로 Stage 0, `PREREG_V0.md`와 등록 임계값 변경, `jsonschema`·`pydantic` 추가.
