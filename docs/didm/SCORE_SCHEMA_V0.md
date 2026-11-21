# DIDM-1 점수 스키마 V0 (`didm-score-v0`)

- 작성: DATA_SOURCE_DIDM 세션, 2026-11-17. 코드: `core/didm/llm/schema.py`, 시험: `tests/didm_schema_acceptance.py` (네트워크 없음), 고정 자료: `tests/fixtures/didm/`.
- 모수 값 (τ, δ, 문턱 등)은 `docs/didm/PREREG_V0.md`가 정합니다. 이 문서는 **형식**만 정합니다.
- RavenPack은 **공개 문서에 나오는 필드 이름**만 대응표에 적습니다. 분류표·값·계산식은 복사하지 않습니다. 필드 이름은 RavenPack Analytics (RPA 1.0) 공개 사용자 안내서와 D14 6절 기준이며, 이 세션에서는 원문을 다시 열지 못했습니다 (**미검증**: 이름 철자는 DS-3 때 확인).

## 1. 한 기록의 필드

한 기록 = 기사 (또는 수집 항목) 하나 × 대상 하나. 모르는 필드가 있거나, 필드가 빠지거나, 범위를 벗어나면 **고치지 않고 거부**합니다 (거부 수를 셈, DIDM 9).

| 필드 | 형식 | 규칙 |
|---|---|---|
| `record_id` | 식별자 | 영숫자 시작, `_ . : - /` 허용, 128자 이하 |
| `source_id` | 식별자 | 수집 출처 (예: `gdelt-gkg2`, `alfred`) |
| `target_kind` | `firm` / `macro` / `none` | `none`이면 `entity_id`는 null |
| `entity_id` | 식별자 또는 null | 시점 기준 종목·거시 요인 ID (DIDM 6.1 3단계) |
| `published_at` | ISO 8601 + 시간대 | 기사 시각. 시간대 없으면 거부 |
| `received_at` | ISO 8601 + 시간대 | **필수.** 우리가 받은 시각. 검증 기준 |
| `relevance_0_100` | 0~100 | 대상이 기사 주제일 확률 ×100. 신호 문턱은 사전등록 (75) |
| `ess_like_0_100` | 0~100, 50 중립 | **= 50 + 50·(P(+1) − P(−1))**. 다르면 거부 |
| `novelty_0_100` | 0~100 | 100 × P̂(새 사건 \| 설명변수), 사전등록 4.1절 신규성 모형 (`core/didm/novelty.py`). 점수 75 이상 (원확률 0.75 이상) = 새 사건. 옛 묶음 할인 (`cluster_decay()`)은 설명변수 하나 |
| `origin_cluster_id` | 식별자 | 같은 원문 재게재 묶음 (DIDM 5.3) |
| `event_type` | 고정 열거형 14 + `none` (소유자 답 P1) | 사전등록 2절. 모르는 값은 거부 |
| `direction_probs` | [P(+1), P(−1), P(0)] | 각 0~1, 합 1 (오차 1e−6) |
| `uncertainty_entropy` | 실수 (nats) | **= direction_probs의 엔트로피**. 다르면 거부 |
| `p_credibility` | 0~1 | DIDM 5.3 신뢰 상태 π |
| `market_confirmation` | `CONFIRMED` / `CONTRADICTED` / `ALREADY_PRICED` / `PENDING` | 판정 규칙은 사전등록 4절 |
| `model_version` | 문자열 | 고정 스냅샷 ID |
| `prompt_sha256` | 소문자 16진 64자 | 프롬프트 해시 |
| `schema_version` | `didm-score-v0` | 입력에 없으면 기본값. 다르면 거부 |

`published_at > received_at`은 V0에서 거부하지 않습니다 (공급사 시계 오차). 수집기가 그런 기록 수를 따로 셉니다 (DS-4a).

DIDM 10.2의 나머지 필드 (`f_vector`, `causal_path`, `layer_attribution`, `valid_from`/`valid_to`, `expires_at`, `jump_*` 등)는 V1 이후 모형 층의 출력이라 V0 기록에 넣지 않습니다. `valid_from`/`valid_to`는 시점 저장소 (DS-4a)가 기록 밖에서 붙입니다.

## 2. 대응표: DIDM 필드 → 엑셀 대안의 입력 → RavenPack 공개 필드 이름

"자체 계산" = 대안이 그 값을 주지 않아 DIDM이 직접 만듦. Bigdata.com 열은 **Stage 3 뒤** (D14 결정, 시험 없음).

| DIDM 필드 | 엑셀 대안 쪽 입력 (근거: `VENDOR_EVAL_2026-11.md` 2절) | RavenPack 공개 필드 이름 (미검증) | Bigdata.com |
|---|---|---|---|
| `record_id` | 자체 계산 (수집기가 부여) | `RP_STORY_ID` (기사 ID) | Stage 3 뒤 |
| `source_id` | 자체 계산 (출처 이름 고정 목록) | `SOURCE_NAME`, `RP_SOURCE_ID` | Stage 3 뒤 |
| `target_kind` | 자체 계산 | `ENTITY_TYPE` | Stage 3 뒤 |
| `entity_id` | Tiingo 티커 태그, Alpha Vantage 티커, GDELT 조직·인물·장소 (H열) → 자체 연결 | `RP_ENTITY_ID` | Stage 3 뒤 |
| `published_at` | GDELT 파일 시각·`DATEADDED`, Tiingo `publishedDate`, Alpha Vantage `time_published` (제3자 사본 기준 이름) | `TIMESTAMP_UTC` | Stage 3 뒤 |
| `received_at` | 자체 계산 (수신 시각). Tiingo `crawlDate`는 보조 | 해당 없음 (공급사 시각만) | Stage 3 뒤 |
| `relevance_0_100` | Alpha Vantage `relevance_score` (0~1, 있으면, O열 ? → DS-4b 확인) ×100 보조 + 자체 계산 | `RELEVANCE` (0~100) | Stage 3 뒤 |
| `ess_like_0_100` | 자체 계산 (FinBERT/LLM 확률). 보조: Alpha Vantage 감성 (−1~1 → 50 + 50·x), GDELT 논조 (50 + tone/2), Cryptopanic 투표 (G·X열) | `EVENT_SENTIMENT_SCORE` (ESS, 0~100, 50 중립) | Stage 3 뒤 |
| `novelty_0_100` | 자체 계산 (N열: 엑셀은 대안 없음 X, 소유자 확정 O = 자체 NLP 직접 구현; 사전등록 4.1절 모형) | `EVENT_SIMILARITY_DAYS`, `EVENT_SIMILARITY_KEY` (옛 판 ENS) | Stage 3 뒤 |
| `origin_cluster_id` | 자체 계산 (근접 중복 묶음) | `EVENT_SIMILARITY_KEY` | Stage 3 뒤 |
| `event_type` | 자체 계산 (I열 자체 NLP). 보조: GDELT CAMEO 사건 코드, Alpha Vantage `topics` | `TOPIC`, `GROUP`, `TYPE`, `CATEGORY` (이름만; 분류표 복사 안 함) | Stage 3 뒤 |
| `direction_probs` | 자체 계산 | 해당 없음 | Stage 3 뒤 |
| `uncertainty_entropy` | 자체 계산 | 해당 없음 | Stage 3 뒤 |
| `p_credibility` | 자체 계산 (독립 출처 수, 공식 발표 여부; 공식 숫자: FRED/ALFRED·CME·Trading Economics, K열) | `NEWS_TYPE` (보조 정보) | Stage 3 뒤 |
| `market_confirmation` | 자체 계산 (W열: 대안 없음 → 시장 반응 확인; 시세는 기존 KIS·Upbit·FRED·Yahoo 캐시) | 해당 없음 (Impact Analytics는 공개 문서에서 확인 못함, 엑셀 W3) | Stage 3 뒤 |
| `model_version` | 자체 계산 | 해당 없음 | Stage 3 뒤 |
| `prompt_sha256` | 자체 계산 | 해당 없음 | Stage 3 뒤 |

모든 DIDM 필드에 대안 쪽 입력 또는 "자체 계산"이 있습니다 (완료 조건 1).

## 3. Stage 3 기준선

Loughran–McDonald 사전, FinBERT, Alpha Vantage 감성 (과거 값이 당시 계산값인지 확인 전에는 과거 검증에 쓰지 않음). 자세한 규칙은 `PREREG_V0.md` 6절.

## 4. Stage 1 정답 집합 한 줄 형식

`core/didm/llm/schema.py` `validate_gold()`. 예시: `tests/fixtures/didm/gold_label_v0.json` (시험이 통과를 확인).

| 필드 | 값 |
|---|---|
| `article_id`, `annotator_id` | 식별자 (주석자 2명 + 판정자 1명, DIDM 9) |
| `market` | `EN` / `KR` |
| `source_tier` | 1 공식·통신, 2 주요 매체, 3 소셜·기타 |
| `target_kind`, `entity_id` | 점수 기록과 같음 |
| `is_subject` | 대상이 기사의 주제인가 (DIDM 9 질문 1) |
| `event_type` | 같은 열거형 |
| `direction` | `+1` / `-1` / `0` |
| `is_new_event` | 새 사건인가 (신규성 정답) |
| `claim_status` | `reported` / `confirmed` (DIDM 9 질문 5) |
| `published_at`, `received_at` | 시간대 있는 ISO 8601 |

## 5. 시험

```
python -m unittest tests.didm_schema_acceptance
```

2026-11-18: 23개 통과 (네트워크 없음; 14개 유형 확인 포함). 신규성 모형은 `tests/didm_novelty_acceptance.py` 6개. 거부 확인: 범위 밖 점수 (관련성 100.5·−1, 신규성 101, 신뢰 1.2), `received_at` 없음·null·시간대 없음, 모르는 `event_type`·`market_confirmation`·필드, ESS·엔트로피 불일치, 확률 합 ≠ 1, 잘못된 해시, 숫자 대신 불리언.
