# DIDM_DEV 세션 인계 문서

- session: DIDM_DEV (https://claude.ai/code/session_016uB1jj8iv57xVbx6EbLLwq), 메인: QUANTGEN/MAIN (session_01H6RrzMUzF8vwK8xkX977mB)
- updated_at: 2026-11-24 23:00 KST
- work_branch: `claude/didm-dev-20261124` (main b872d8c에서 시작), work_commit: `9b81479`
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
| DIDM-4/b 사전등록 V0.1 제안서 + 탐색 검정력 | 끝 (**미적용**, 소유자 답 대기: 질문 6개) | d11a52f, 64c74a7 | 등록 파일 무변경; `python -B -m tools.didm.stage0_explore --out <저장소 밖> --workers 4` (시드 77020261124, 탐색 표시) |
| DIDM-2/2 후속 검토 지적 11건 (FRESH-1~11) | 끝 | b1d9eae | 계약 49 + 마감일 28 + 스키마 26 OK; 변형 17개 생존 0 |
| Stage 1 해석을 설정값 한 곳으로 + 제안서 8·9절 | 끝 | 91134bb | `tests.didm_stage1_acceptance` 30 OK |
| DIDM-8 시장 확인·거시 서프라이즈 | 끝 (합성 입력만) | c1929cc | `tests.didm_confirmation_acceptance` 20 OK; 변형 20개 생존 0 |
| DIDM-7 유사도·근접 중복 군집화·개체 연결 (첫 판) | 끝 (합성 사례만; 실제 정밀도·재현율 미측정) | b2d955c | `tests.didm_entities_acceptance` 23 OK; 변형 20개 생존 0 |
| DIDM-6 기준선 채점기 래퍼 | 라이선스 답 뒤 (설계 메모만: 제안서 9절) | — | — |
| 재확인 시험 빈틈 + 시장 확인 해석 설정값 + 제안서 0·10절 | 끝 | d71cd7d | 변형 9개 생존 0 |
| DIDM-9 신뢰 상태와 충격 구성 | 끝 (합성 사례만; 가중치는 임시값) | 1e7dbb9 | `tests.didm_credibility_acceptance` 22 OK; 변형 26개 생존 0 |
| DIDM-9 덧붙임: 검증을 거친 판단만 조립되는 표식, `assemble_batch` | 끝 | 7ed29b0 | 계약 52 OK; 변형 5개 생존 0 |
| DIDM-9/e2e 끝에서 끝까지 합성 실행 (배선 시험, 등록 실행 아님) | 끝 | 9b81479 | `python -B -m unittest tests.didm_e2e_acceptance` → 17 OK (약 16초); 변형 12개 생존 0 |

개발 브랜치 전체: DIDM_DEV 시험 10개 모듈 + novelty + gateway_boundary 297 OK (약 52초). 등록된 ID 번호는 통합 브랜치 `docs/nautilus_bridge/REMAINING_WORK_2026-11-24.md` 2.2절 (DIDM-6 기준선 래퍼, 7 개체 연결·군집화, 8 시장 확인, 9 신뢰 상태·충격).

DIDM-5 문서: `docs/didm/STAGE1_TOOLS_V0.md` (재는 방법과 해석 5가지), `GOLD_SET_V0.md` (표본 규칙), `LABELLING_GUIDE_V0.md` (주석자 안내 초안), `SCORE_SCHEMA_V1_PROPOSAL.md` (보정 지도 버전 필드 제안, 미적용).

## 3. 열린 것

- **Stage 0 REVISE의 뜻** (`docs/didm/STAGE0_REPORT_V0.md`): θ₀·γ·ψ·η 통과. δ(지연 비중) 검정력 22%, φ(연결망) 11%, 신뢰 상태·연결망 없는 모형이 표본 밖에서 뚜렷이 지지 않음, HAR 월 계수 포함률 56%. 고칠 안은 `docs/didm/PREREG_V0_1_PROPOSAL_2026-11-24.md`에 질문 14개로 정리 (12절; Stage 0 6개, Stage 1 해석·한국어 기준선 3개, 시장 확인 M1·M5 2개, 신뢰 상태 C1·C2·C9 3개) (메인 결정: 네 가지 모두 소유자 답 전에는 적용하지 않음, (다)도 포함). 답이 오면 승인 항목만 `PREREG_V0_1.md`로 옮기고 격자·규칙을 먼저 커밋한 뒤 Stage 0 시도 2회.
- 보정 지도 버전: 지금은 `Assembled.calibration_version` 곁기록. `didm-score-v1` 제안을 메인에 올림 (`docs/didm/SCORE_SCHEMA_V1_PROPOSAL.md`), 적용 시점은 메인 판단.
- Stage 1을 돌리려면 필요한 것 (소유자): 주석자 2명·판정자 지정, 표시 도구, 기사 본문을 주석자에게 보여 줄 권리 확인. 그 전에는 도구만 있음.
- 라이선스: FinBERT 가중치 CC BY-NC-SA 4.0, LM 사전 학술 무료·상업 별도 허가. 소유자 확인 대기, 그 전까지 연구 비교용으로만. 저장소·배포물에 두 파일 없음.
- Qwen3은 공개 학습 마감일이 없어 과거 검증 자격 없음 → 자체 LLM의 기반 모델 선택에 영향 (QUANTGPT에 전달됨).
- 공유 파일 (runtime-smoke.yml 시험 목록, source-review.json 기준선)은 메인이 통합 PR에서 처리. 다음 묶음에 `tests.didm_stage0_acceptance` 추가 필요.
- 문구에 없어 정한 선택은 문서마다 번호로: 시장 확인 M1~M7 (`MARKET_CONFIRMATION_V0.md` 2절), 군집화·연결 E1~E5 (`ENTITIES_V0.md` 4절, E1·E2는 Stage 1 정답 집합으로 확인), 신뢰 상태 C1~C10 (`CREDIBILITY_V0.md` 3절). 판정이 달라지는 M1·M5·C1·C2·H1~H5는 설정값 한 곳에 있고 제안서 질문에 들어 있음.
- 사건 식별자 (메인 결정 2026-11-24): 대상 + 사건 유형 + 첫 보도 뒤 7일 창 (`core/didm/credibility/events.py`); 원출처 묶음은 사건 안 재게시 할인에만. 레코드의 `p_credibility`는 받은 시점 값이고 충격은 결정 시각 값을 다시 읽음.
- e2e에서 드러난 틈 6가지는 `docs/didm/E2E_V0.md` 4절 (시장 확인 표지를 둘 자리, 참신성·관련성 모형 미연결, 입장·공식 표시, 보정 없는 길, 묶음 속도, 유형 판단이 틀릴 때). v1 형식 제안은 `SCORE_SCHEMA_V1_PROPOSAL.md` 3.1절.
- 신뢰 가중치는 임시값 (`cred-placeholder-…`). 해결된 소문 집합이 생기면 `fit_weights`로 대체. 보도의 입장 (지지/반박)·공식 여부는 지금 호출자가 줌 (판단 형식에 필드 없음).
- `run_scorer`는 `calibrated=True/False`가 필수 (무보정이면 레코드의 1e-9 조건을 미리 검사).
- `confirm_repository_trust`는 부르지 않음 (메인 알림 2026-11-24: 부르면 세션이 신뢰 기기 전용이 되어 메인이 닿지 못함).
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
