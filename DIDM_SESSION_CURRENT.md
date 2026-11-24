# DIDM_DEV 세션 인계 문서

- session: DIDM_DEV (https://claude.ai/code/session_016uB1jj8iv57xVbx6EbLLwq), 메인: QUANTGEN/MAIN (session_01H6RrzMUzF8vwK8xkX977mB)
- updated_at: 2026-11-24 20:00 KST
- work_branch: `claude/didm-dev-20261124` (main b872d8c에서 시작), work_commit: `fc4b830`
- 수정 전용 브랜치: `claude/didm-contract-fixes-20261124` @ `feed288` (3626913에서, 통합 PR ①에 합쳐짐: 메인 703aa01)
- PR: 없음 (메인이 통합 PR로 묶음; 이 세션은 PR을 열지 않음). 원장은 메인이 씀.

## 0. 소유자 지시 원문 (2026-11-24, 메인 세션 전달)

> 기존의 OS확장, Payment, Data Sourcing과 더불어 DIDM 개발, 그리고 아래에서 설명할 자체 LLM에 대한 세션도 하부 세션에 분리하여 추가해주세요.

데이터 수집은 DATA_SOURCE 세션, DIDM 모형은 이 세션, 자체 LLM은 QUANTGPT 세션.

## 1. 경계 (한 경로는 한 세션만)

이 세션: `core/didm/llm/**`, `core/didm/novelty.py`, 새 `core/didm/{sim,models,eval,calibration,credibility,entities,baselines}/`, 새 `tools/didm/` 스크립트, `tests/didm_{schema,novelty}_acceptance.py`와 새 `tests/didm_*`, `docs/didm/PREREG_V0.md`(동결, 고치지 않음)·`SCORE_SCHEMA_V0.md`·새 문서. `core/didm/{ingest,store}/**`, `data/didm/**`, 공유 파일(`runtime-smoke.yml`, `docs/compliance/*`, `requirements.txt`, `pyproject.toml`)은 직접 고치지 않음.

## 2. 한 일

| ID | 상태 | 커밋 | 검사 |
|---|---|---|---|
| DIDM-2 채점기 계약 | 끝 | ba28b02, 검토 수정 feed288 | `python -B -m unittest tests.didm_contract_acceptance tests.didm_schema_acceptance` → 43 + 26 OK; `python -B -m tools.didm.export_schema --check` → 종료 0; schema.py 변경 없음 |
| DIDM-3/a 마감일 규칙 코드·표 | 끝 | 3626913, 검토 수정 feed288 | `tests.didm_cutoffs_acceptance` 24 OK |
| DIDM-3/b 표 채움 (출처 페이지 직접 확인) | 끝 | e01bb08 | 35행 중 33행 검증됨; Qwen3·자체 LLM 미검증 |
| 통합 PR ① 검토 지적 12건 | 끝 | feed288 → 4f38621로 개발 브랜치에 합침 | 변형 25개 중 생존 0 |
| DIDM-4 Stage 0 모의실험 | 시도 1회 끝, **판정 REVISE** | 6aaba25(격자 선커밋), 325fad7, 72edc0f | `tests.didm_stage0_acceptance` 34 OK; `python -B -m tools.didm.stage0_report --seed 20261124 --out <저장소 밖> --workers 4` 두 번 → 출력 동일, `STAGE0: REVISE` |
| DIDM-5 Stage 1 측정 도구 | 끝 (도구만; **Stage 1 자체는 미실행**, 정답 집합 없음) | fc4b830 | `python -B -m unittest tests.didm_stage1_acceptance` → 29 OK (합성 표시만); 변형 19개 중 생존 0 |
| DIDM-6 이후 (개체 연결, 군집화, 신뢰 상태, 시장 확인, 채점기·프롬프트) | 메인 배정 대기 | — | — |

개발 브랜치 전체: DIDM_DEV 시험 6개 모듈 + gateway_boundary 197 OK.

DIDM-5 문서: `docs/didm/STAGE1_TOOLS_V0.md` (재는 방법과 해석 5가지), `GOLD_SET_V0.md` (표본 규칙), `LABELLING_GUIDE_V0.md` (주석자 안내 초안), `SCORE_SCHEMA_V1_PROPOSAL.md` (보정 지도 버전 필드 제안, 미적용).

## 3. 열린 것

- **Stage 0 REVISE의 뜻** (`docs/didm/STAGE0_REPORT_V0.md`): θ₀·γ·ψ·η 통과. δ(지연 비중) 검정력 22%, φ(연결망) 11%, 신뢰 상태·연결망 없는 모형이 표본 밖에서 뚜렷이 지지 않음, HAR 월 계수 포함률 56%. 고칠 안 (가)~(라)는 보고서 5절에 제안으로만 있음. 적용하면 시도 2회로 기록. (가)는 사전등록 Stage 2 문구와 닿아 V0.1이 필요한지 메인·소유자 판단 대기.
- 보정 지도 버전: 지금은 `Assembled.calibration_version` 곁기록. `didm-score-v1` 제안을 메인에 올림 (`docs/didm/SCORE_SCHEMA_V1_PROPOSAL.md`), 적용 시점은 메인 판단.
- Stage 1을 돌리려면 필요한 것 (소유자): 주석자 2명·판정자 지정, 표시 도구, 기사 본문을 주석자에게 보여 줄 권리 확인. 그 전에는 도구만 있음.
- 라이선스: FinBERT 가중치 CC BY-NC-SA 4.0, LM 사전 학술 무료·상업 별도 허가. 소유자 확인 대기, 그 전까지 연구 비교용으로만. 저장소·배포물에 두 파일 없음.
- Qwen3은 공개 학습 마감일이 없어 과거 검증 자격 없음 → 자체 LLM의 기반 모델 선택에 영향 (QUANTGPT에 전달됨).
- 공유 파일 (runtime-smoke.yml 시험 목록, source-review.json 기준선)은 메인이 통합 PR에서 처리. 다음 묶음에 `tests.didm_stage0_acceptance` 추가 필요.
- 이 컨테이너에는 scipy·matplotlib이 없음. DIDM 코드는 numpy와 표준 라이브러리만 씀.
- 미검증: 호스트 CI, Python 3.13 이외 판에서의 Stage 0 숫자 일치.

## 4. 이어받는 법

```
git clone --no-checkout <origin> w && cd w
git sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
git checkout claude/didm-dev-20261124 && test ! -e docs/asset_expansion/cache
python -B -m unittest tests.didm_contract_acceptance tests.didm_schema_acceptance tests.didm_novelty_acceptance
```

하지 말 것: 보호 캐시·`.env` 열기, 유료·모델·공급사 호출, 모델 내려받기, 실제 가격으로 Stage 0, `PREREG_V0.md`와 등록 임계값 변경, `jsonschema`·`pydantic` 추가.
