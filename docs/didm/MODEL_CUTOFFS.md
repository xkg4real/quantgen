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
| loughran-mcdonald | Loughran-McDonald 사전 | 기준선 | Loughran-McDonald_MasterDictionary_1993-2025.csv (Updated: March, 2026) | — | — | https://sraf.nd.edu/loughranmcdonald-master-dictionary/ | 2026-11-24 | 검증됨 |
| ProsusAI/finbert | FinBERT | 기준선 | 0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031 | — | — | https://huggingface.co/ProsusAI/finbert | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-19991231 | ChronoGPT 빈티지 | 마감일 | 45d6568340081add5c5b1444feb17a94b8f8199d | 1999-12-31 | 2000-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20001231 | ChronoGPT 빈티지 | 마감일 | aab8e7f10ffc8a63b557d47ceeca0712ddc0fdfa | 2000-12-31 | 2001-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20011231 | ChronoGPT 빈티지 | 마감일 | 84f4d197fc931bb3cc39d1a071e8436304890921 | 2001-12-31 | 2002-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20021231 | ChronoGPT 빈티지 | 마감일 | 4b48afa531ff3d530b0273e5c64b8ad1381016e4 | 2002-12-31 | 2003-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20031231 | ChronoGPT 빈티지 | 마감일 | 6aba09104ca8ccb8febb2a29d2e4c8bb99526638 | 2003-12-31 | 2004-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20041231 | ChronoGPT 빈티지 | 마감일 | f446364b14657b8f77d864bd305e7caea5e5e209 | 2004-12-31 | 2005-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20051231 | ChronoGPT 빈티지 | 마감일 | 64a190a1eba9d0bd4a320225284ceb8376634cda | 2005-12-31 | 2006-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20061231 | ChronoGPT 빈티지 | 마감일 | a0a130d03014401d9f7370c50537f49c128da78d | 2006-12-31 | 2007-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20071231 | ChronoGPT 빈티지 | 마감일 | ca382535273b9f3a6d5ff476f565246b8c90fa07 | 2007-12-31 | 2008-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20081231 | ChronoGPT 빈티지 | 마감일 | 020fcd3af211e574905941a369f9635bca53a8d6 | 2008-12-31 | 2009-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20091231 | ChronoGPT 빈티지 | 마감일 | 0c7124691ed3fb527af12dab7013eac1ae56fec7 | 2009-12-31 | 2010-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20101231 | ChronoGPT 빈티지 | 마감일 | 4fb687ab4b3029e5d364423434e6f20019b1b222 | 2010-12-31 | 2011-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20111231 | ChronoGPT 빈티지 | 마감일 | ea5aaed9f362885f367514b067a36cc4faa0ce5e | 2011-12-31 | 2012-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20121231 | ChronoGPT 빈티지 | 마감일 | 67a896b02f6cdcd2e99d62866a2d334eeaeb99b5 | 2012-12-31 | 2013-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20131231 | ChronoGPT 빈티지 | 마감일 | 6f2e595689458b1809d5c6efb9a6095257347ca2 | 2013-12-31 | 2014-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20141231 | ChronoGPT 빈티지 | 마감일 | 4fba07f4ef563b3addf2b05f385d0b347bf1cc0d | 2014-12-31 | 2015-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20151231 | ChronoGPT 빈티지 | 마감일 | aacd4c4e8020dd0ad686d36f18bcf34cd8003bc3 | 2015-12-31 | 2016-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20161231 | ChronoGPT 빈티지 | 마감일 | 20d93dc9b103644b212db413db4ab1207063d010 | 2016-12-31 | 2017-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20171231 | ChronoGPT 빈티지 | 마감일 | 4cc4334a2c2d38ae35deb0bb7fcae642d3f73a10 | 2017-12-31 | 2018-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20181231 | ChronoGPT 빈티지 | 마감일 | 17d7de7945199ff03be989ca84d00c0f59a975af | 2018-12-31 | 2019-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20191231 | ChronoGPT 빈티지 | 마감일 | 7e62517f31b11fad179c79ce79a465aa00c7ee4d | 2019-12-31 | 2020-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20201231 | ChronoGPT 빈티지 | 마감일 | c0d2acbd2a378ac79d8a5ae79a9447d23145eb8a | 2020-12-31 | 2021-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20211231 | ChronoGPT 빈티지 | 마감일 | a070953708ee809e630e4d9652e9c753d7b6782e | 2021-12-31 | 2022-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20221231 | ChronoGPT 빈티지 | 마감일 | 993711fdf078740fe1c837a3687528e2173443d2 | 2022-12-31 | 2023-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20231231 | ChronoGPT 빈티지 | 마감일 | 8ac22e54d37df8bb8037622680414118239fbe53 | 2023-12-31 | 2024-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| manelalab/chrono-gpt-v1-20241231 | ChronoGPT 빈티지 | 마감일 | 1d9f1b8ff50bb45a6fe1402280e617af4c2d805c | 2024-12-31 | 2025-03-31 | https://arxiv.org/abs/2502.21206 | 2026-11-24 | 검증됨 |
| qwen3-candidates | Qwen3 후보 | 마감일 | — | — | — | — | — | 미검증, 자격 없음 |
| claude-fable-5-2 | Claude (API) | 마감일 | claude-fable-5-2 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| claude-opus-5-5 | Claude (API) | 마감일 | claude-opus-5-5 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| claude-sonnet-5-5 | Claude (API) | 마감일 | claude-sonnet-5-5 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| claude-haiku-5-5 | Claude (API) | 마감일 | claude-haiku-5-5 | 2026-06-30 | 2026-09-30 | https://platform.claude.com/docs/en/about-claude/models/overview | 2026-11-24 | 검증됨 |
| quantgpt-in-house | 자체 LLM | 마감일 | — | — | — | — | — | 미검증, 자격 없음 |

## 3. 행마다 확인한 것

모두 2026-11-24에 출처 페이지를 직접 열어 읽은 값입니다. 모델 가중치와 사전 파일은 받지 않았습니다 (모델 카드, 저장소 정보, 논문 본문 페이지만).

- **Loughran-McDonald 사전 (검증됨, 기준선).** 출처 페이지의 글: "Master Dictionary Updated: March, 2026", 파일 이름 `Loughran-McDonald_MasterDictionary_1993-2025.csv`. 같은 페이지: "The dictionary/sentiment lists are free for use in academic research. For commercial licenses, please contact us". **상업 이용은 별도 허가가 필요합니다** (권리 확인은 이 표의 범위 밖, 메인에 보고함). 알아둘 점: 이 판은 2025년까지의 공시로 갱신된 사전이라 과거 구간에 쓰면 그 뒤에 더해진 단어가 들어갑니다. 사전등록 5절 4번이 사전을 기준선으로 이름 붙였으므로 자격은 있지만, Stage 2 보고서에 판 이름을 적습니다.
- **FinBERT `ProsusAI/finbert` (검증됨, 기준선).** 저장소 main 커밋 `0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031` (마지막 수정 2026-10-12). 모델 카드의 글: Financial PhraseBank (Malo et al. 2014)로 미세조정, "further pre-trained on a subset of the Reuters TRC2 corpus", 논문 arXiv:1908.10063. NIST 페이지의 글: TRC2는 "covering the period from 2008-01-01 00:00:03 to 2009-02-28 23:54:14". 모델 카드에 **학습 마감일 문구는 없습니다** (기준선 규칙에는 마감일이 필요 없음). **가중치 라이선스가 CC BY-NC-SA 4.0 (비상업)** 입니다 (메인에 보고함).
- **ChronoGPT 26개 빈티지 (검증됨).** 저장소 `manelalab/chrono-gpt-v1-<연도>1231`, 1999~2024, 각 main 커밋을 스냅샷 ID로 적었습니다. 논문 (arXiv 2502.21206 v3) 본문의 글: "We create model checkpoints for each year from 1999 to 2024 (26 models in total)", 표 1 Knowledge Cutoff "December, 1999" (ChronoGPT 1999) … "December, 2024" (ChronoGPT 2024). 표 1은 처음과 끝 빈티지만 적고 가운데는 줄였으므로, 가운데 빈티지의 마감일 (그 해 12월 31일)은 "해마다 하나"라는 본문과 저장소 이름에서 온 값입니다. 모델 카드 자체에는 마감일 문구가 없습니다. 같은 저장소 묶음에 `chrono-bert-v1-*`, `chrono-gpt-instruct-v1-*`도 있으나 쓸 때 행을 더합니다.
- **Qwen3 후보 (미검증).** 모델 카드 (`Qwen/Qwen3-8B`, main 커밋 `b968826d9c46dd6066d109eabc6255188de91218`)와 기술 보고서 (arXiv 2505.09388 본문 전체)를 열어 찾았으나 **학습 마감일 문구가 없습니다.** 공개 기준일이 없으므로 사전등록 5절 2번에 따라 과거 검증에 쓰지 않습니다. 자체 LLM의 기반 모델로 Qwen3을 쓰면 자체 LLM도 같은 이유로 자격이 없습니다 (QUANTGPT에 알릴 것).
- **Claude 4개 행 (검증됨).** 출처의 "Latest models" 표를 두 번 따로 열어 같은 값을 확인했습니다. 표의 글 그대로: Training data cutoff "Jun 2026", Reliable knowledge cutoff "Jun 2026" (네 모델 모두). 같은 페이지: "Every Claude model ID is a pinned snapshot, including the dateless IDs used from the 4.6 generation on." 마감일은 달의 마지막 날 (2026-06-30)로 봤습니다. **어느 모델을 Claude 기준선으로 쓸지는 아직 정하지 않았습니다.** 자격 시작이 2026-09-30이므로 Stage 2 (2015~2024)에는 쓸 수 없습니다.
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
