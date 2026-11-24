---
status: checkpoint
reason: milestone
from: claude
task: quantgpt-q0
cycle: 2026-11-24
done_ids: QGPT-01/a, QGPT-02, QGPT-04, QGPT-05, QGPT-21, QGPT-03, QGPT-replay
next_ids: QGPT-11, QGPT-20
updated_at: 2026-11-24T21:30:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/quantgpt-q0-20261124
work_commit: 88e42d3
uncommitted_changes: no
pr: none
session: https://claude.ai/code/session_016uB1jfyCrLC5oipyVVMyCe
---

# QUANTGPT 세션 인계 (하부 세션, 메인: QUANTGEN/MAIN)

원장(LEDGER)은 이 세션이 쓰지 않는다. 완료 ID는 메인에 `--done` 문자열로 보냈다(메인이 git으로 확인한 뒤 기록).

## 1. 소유자 지시 (2026-11-24, 원문)

> 자체 LLM에 대한 개발을 착수할 것. 이때, 자체 LLM의 설계와 관련된 파일은 첨부된 .md 파일 및 Notion의 Autonomous Macro Intelligence Engine을 참고해주세요. 이때, 이와 유사한 구조를 가진 qlib에 대한 문서도 첨부하였으니 참고하시길 바랍니다.
> 위 자체 LLM 개발에 대한 하위 session의 이름은 코드명 QuantGPT로 설정해주시고, 개발에 대한 reference 차 Notion의 Econ493 - 인공지능기반경제분석 -> 신경망과 딥러닝 페이지를 참고해주세요.
> QuantGPT에 대한 내용을 TRADEGEN 세션에도 공유하여 진행해주세요.
> Claude.md에 있는 가이드라인을 준수하여 진행해주세요.

같은 날 결정: 코드는 공개 quantgen에서 시작(나중에 비공개 저장소로 옮김), 명세서 v1.0 전문은 공개 저장소에 올리지 않음, TRADEGEN 공유는 TRADEGEN_GITHUB 세션으로.

## 2. 어디에 무엇이 있나

브랜치 `claude/quantgpt-q0-20261124` (origin/main b872d8c에서), 바뀐 파일은 모두 `qgpt/` 아래. main에 PR 없음(MERGE_QUEUE에 "병합: QUANTGPT"가 적힌 뒤에만 연다).

| ID | 커밋 | 파일 | 무엇 |
|---|---|---|---|
| QGPT-01/a | c7e7494 | qgpt/pyproject.toml, quantgpt/**/__init__.py | 패키지 골격 |
| QGPT-02 | 073725b | quantgpt/envelope.py, router.py, contracts/{qss,tasks,news}.py, checks/schema.py | 봉투 qgpt-env-v1, 계약 7종, QSS v0, T-NEWS 판단 부분 출력 |
| QGPT-04 | 3e76b35 | quantgpt/checks/{numbers,citations,leakage}.py | 숫자·인용·시점 누출 검사, 기권 규칙 |
| QGPT-05 | 735e2c0 | quantgpt/registry/{attempts,dsr}.py | 덧붙이기 전용 시도 원장, 원장 기반 DSR |
| QGPT-21 | 30b3279 | quantgpt/tools/protocol.py | 호스트 도구 3종(run_calc, get_card, list_cards) |
| QGPT-03 | 7478f82 | quantgpt/policy/filter.py | 정책 필터 PF-1~6 코드, 시드 규칙 13개 |
| QGPT-replay | 88e42d3 | quantgpt/pipeline.py, backends/{base,fake}.py | 요청 1개 → 봉투 1개, 가짜 백엔드 재생 |

## 3. 검사 (다시 돌리는 법)

```
git clone --no-checkout <origin> w && cd w
git sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
git checkout claude/quantgpt-q0-20261124 && test ! -e docs/asset_expansion/cache
cd qgpt && python -B -m unittest discover -s tests
```

기대 결과: 108개, 기본 환경에서 107 통과 1 건너뜀(scipy가 없으면 원본 DSR 대조 시험을 건너뜀). numpy와 scipy가 있는 환경에서는 108/108. `git diff --name-only origin/main...HEAD -- . ':!docs/asset_expansion/cache'`는 모두 `qgpt/`로 시작해야 한다.

## 4. 정한 것과 이유

- 봉투: `envelope_version`, 선택 필드 `reason_code`(12종)를 둠. ok가 아니면 body는 null. tool 모드의 ok는 정책 위반 0개, 숫자 전부 found_in_payload=true. 작업 코드 없는 요청은 task=null, blocked/no_task_code, PF-6.
- `request_sha256` = sha256(정규화 JSON{task, mode, input, model, adapter, prompt_version}). 정규화: 키 정렬, 공백 없음, UTF-8 그대로(ensure_ascii 끔), NaN·Infinity 거부.
- QSS v0: 저장 카드 34개의 필드에서 정함. 단계 2개(draft: 증거·판정 필드 금지 / recorded: 증거·판정·출처 필수). 카드의 NaN 26개는 `{"$nonfinite":"NaN"}`로 적음. 34/34가 글자 그대로 왕복.
- T-NEWS: 모델은 5개 필드만 냄(target_kind, entity_id, relevance_0_100, event_type, direction_probs). ess_like·엔트로피는 호스트 계산, 참신성·원출처 묶음·신뢰·시장 확인·수신 시각은 DIDM 쪽. 메인에 물어 둔 것 2개(p_credibility를 호스트가 정하는지, 방향 확률 보정을 DIDM이 하는지)는 답 대기.
- 숫자 기권 규칙: tool 모드는 데이터에도 요청 문장에도 없는 숫자가 있으면 기권, owner는 기록만. 고정 사례 20개(계산으로 나온 맞는 숫자)에서 기권 18/20. 메인에 선택지 3개를 보냄(계산은 호스트가 미리 payload에 넣기를 추천). 결정 전까지 엄격 규칙 유지.
- 인용·시점 누출 검사는 두 모드 모두에서 기권으로 처리(규제 필터가 아니라 정확성 검사라서).
- 시도 원장: 체인만으로는 끝에서 잘린 줄을 알 수 없으므로 head() 해시를 원장 밖에 고정해야 함.
- 정책 필터: 저장소에는 시드 규칙과 합성 문장만. 검토된 전체 규칙, 평가 문항, 레드팀 문항은 넣지 않음(메인이 소유자에게 확인 전).

## 5. 확인하지 못한 것 (미검증)

- 명세서 v1.0 전문과의 대조(파일이 아직 안 옴). 계약 6종의 필드 이름은 요약만 보고 정한 초안.
- 시드 정책 규칙의 실제 차단 성능(부정문 오탐, 돌려 말하기 미탐).
- 한국어 토크나이저 왕복, 실제 백엔드의 재생(실제 백엔드가 아직 없음).
- gate_ledger.py의 deflated_dsr와의 직접 실행 대조(식과 손계산만 확인).

## 6. 다음 일

1. QGPT-11 채점기(가짜 백엔드): 봉투 묶음(JSON Lines)을 받아 환각률(숫자 미발견), 기권률, 계약 통과율, 누출률을 내는 `qgpt/eval/`. 완료 조건: 고정 봉투 묶음에서 손으로 센 값과 일치하는 unittest.
2. QGPT-20 SQLite FTS5 인덱스와 as_of 필터(문서·카드만): `quantgpt/rag/`. 완료 조건: as_of보다 늦은 문서가 검색 결과에 0개, 카드 34개 색인.
3. 명세서 전문이 오면 4절과 다른 점을 메인에 보고하고 맞춘다.

## 7. TRADEGEN 공유

2026-11-24 TRADEGEN_GITHUB 세션(session_019s6Fyn2GetszXS83ZaV6W9)에 요약을 보냄. 첫 시도는 신뢰 확인 필요로 거절, 소유자가 카드에서 허용, 다시 보내 전달됨. 내용은 handoff `QUANTGPT_TRADEGEN.md` v0.1의 요점과 구현 상태. TRADEGEN 코드 변경은 요청하지 않았고 tradegen 저장소에 push하지 않았다.
