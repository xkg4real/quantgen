# DIDM-3 모델 학습 마감일 목록 (`MODEL_CUTOFFS`)

- 작성: DIDM_DEV 세션, 2026-11-24. 코드: `core/didm/llm/cutoffs.py` (이 표와 같은 내용의 `REGISTRY`), 시험: `tests/didm_cutoffs_acceptance.py` (표와 코드가 다르면 실패).
- 근거: `docs/didm/PREREG_V0.md` 5절 2~4번 (동결). 이 문서는 그 규칙을 **실행할 수 있게** 옮긴 것이고 규칙을 바꾸지 않습니다.
- **마감일은 추측하지 않습니다.** 출처 페이지를 직접 열어 확인한 값만 적고, 못 연 것은 "미검증, 자격 없음"입니다.

## 1. 규칙

1. 모델마다 학습 마감일과 그 공개 출처가 있어야 합니다. 없으면 그 모델은 과거 검증에 쓰지 않습니다.
2. 그 모델의 점수로 검증할 수 있는 기사: **기사 날짜(UTC) ≥ 마감일 + 3개월.** 기사 날짜는 **발행일(`published_at`)과 받은 날(`received_at`) 중 이른 날**입니다. 과거 기사를 오늘 받아 오면 받은 날은 오늘이지만 (사전등록 5절 1번) 모델이 그 기사로 학습했을 수 있으므로, 받은 날만 보면 안 됩니다. 예: 마감 2023-12-31 → 2024-03-31부터. 달 끝은 맞춥니다 (2023-11-30 → 2024-02-29).
3. 출처가 달까지만 적으면 (예: "Jun 2026") 그 달의 마지막 날로 봅니다 (늦은 쪽 = 보수적).
4. 자체 LLM: 마감일 = 기반 모델의 마감일과 미세조정 자료 마지막 날 중 **늦은 날**. 둘 중 하나라도 모르면 자격 없음.
5. 상용 API 모델도 같은 규칙. 느슨하게 하는 예외는 없습니다.
6. 사전등록 5절 4번이 마감일 이전 구간에 쓰라고 이름을 적은 기준선 (Loughran-McDonald 사전, FinBERT)은 기사 날짜 제한이 없습니다. 다만 **고정 스냅샷·출처·확인일이 있어야** 쓸 수 있고, 이 예외는 코드의 `BASELINE_KEYS` 두 키에만 적용됩니다 (다른 모델에 "기준선" 표시를 붙여도 자격이 생기지 않음). ChronoGPT는 빈티지마다 고정 시점이 마감일이고 2번 규칙을 그대로 따릅니다.
7. 목록에 없는 `model_version`은 자격 없음 (닫힌 쪽으로 실패).
8. 모델 버전이 바뀌면 새 행입니다 (사전등록 5절 6번).

## 2. 목록

"자격 시작"은 마감일 + 3개월. 상태가 "검증됨"인 행만 과거 검증에 쓸 수 있습니다.

| 키 (`model_version`) | 계열 | 규칙 | 스냅샷 ID | 마감일 | 자격 시작 | 출처 URL | 확인일 | 상태 |
|---|---|---|---|---|---|---|---|---|
| loughran-mcdonald | Loughran-McDonald 사전 | 기준선 | — | — | — | — | — | 미검증, 자격 없음 |
| ProsusAI/finbert | FinBERT | 기준선 | — | — | — | — | — | 미검증, 자격 없음 |
| chronogpt-vintages | ChronoGPT 빈티지 | 마감일 | — | — | — | — | — | 미검증, 자격 없음 |
| qwen3-candidates | Qwen3 후보 | 마감일 | — | — | — | — | — | 미검증, 자격 없음 |
| claude-fable-5-2 | Claude (API) | 마감일 | claude-fable-5-2 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| claude-opus-5-5 | Claude (API) | 마감일 | claude-opus-5-5 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| claude-sonnet-5-5 | Claude (API) | 마감일 | claude-sonnet-5-5 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| claude-haiku-5-5 | Claude (API) | 마감일 | claude-haiku-5-5 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| quantgpt-in-house | 자체 LLM | 마감일 | — | — | — | — | — | 미검증, 자격 없음 |

## 3. 행마다 확인한 것

- **Claude 4개 행 (검증됨).** 2026-11-24에 위 URL의 "Latest models" 표를 두 번 따로 열어 같은 값을 확인했습니다. 표의 글 그대로: Training data cutoff "Jun 2026", Reliable knowledge cutoff "Jun 2026" (네 모델 모두). 같은 페이지: "Every Claude model ID is a pinned snapshot, including the dateless IDs used from the 4.6 generation on." 그래서 스냅샷 ID = 모델 ID입니다. 마감일은 두 값 중 넓은 쪽인 Training data cutoff를 썼고 달의 마지막 날 (2026-06-30)로 봤습니다. **어느 모델을 Claude 기준선으로 쓸지는 아직 정하지 않았습니다.** 자격 시작이 2026-09-30이므로 Stage 2 (2015~2024)에는 쓸 수 없고 Stage 3·5의 끝부분에만 쓸 수 있습니다.
- **Loughran-McDonald, FinBERT, ChronoGPT, Qwen3 (미검증).** 출처 호스트 `sraf.nd.edu`, `huggingface.co`, `arxiv.org`, `trec.nist.gov`를 이 세션의 네트워크 정책이 막아 페이지를 열지 못했습니다. 검색 요약으로 본 값 (사전 판 이름, 저장소 이름, 논문 번호 등)은 열어 본 페이지가 아니므로 **표에 넣지 않았습니다.** 호스트가 열리면 스냅샷 ID (파일 판 또는 저장소 커밋), 출처 URL, 확인일, 마감일을 채웁니다. ChronoGPT와 Qwen3은 그때 빈티지·후보마다 한 행으로 나눕니다. Qwen3은 공식 출처가 마감일을 밝히지 않으면 그대로 자격 없음입니다.
- **자체 LLM (미검증).** 기반 모델과 미세조정 자료가 정해지면 `in_house_card()`로 행을 만듭니다. 기반 모델이 미검증이면 자체 LLM도 미검증입니다.

## 4. 쓰는 법

```python
from core.didm.llm.cutoffs import REGISTRY
REGISTRY.eligibility("claude-fable-5-2", published_at=record.published_at, received_at=record.received_at)
# -> Eligibility(eligible, reason, eligible_from); 두 시각이 모두 필요하고 이른 날로 판정
```

```
python -B -m unittest tests.didm_cutoffs_acceptance
```
