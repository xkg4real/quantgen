# 새 공급사 3곳 연결 계획 — EODHD, Alpaca News, Massive (DS-5a·5b·5c, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 D3, 2026-11-24). **문서만.** 이 문서는 가입·결제·수집기 추가를 승인하지 않습니다.
- **법률 자문이 아닙니다.** 요금·권리·이력 깊이는 모두 검색 요약 기준이며 **미검증**입니다 (공급사 호스트는 이 클라우드 세션에서 막힘).
- 엑셀 (소유자 RavenPack 대안 9개) 밖의 공급사입니다. `VENDOR_EVAL_2026-11.md`의 엑셀 칸은 바꾸지 않습니다.

## 0. 지금 상태 (origin/main `b872d8c`)

| 공급사 | main에 있는 것 | 없는 것 |
|---|---|---|
| EODHD Economic Events | `core/didm/ingest/eodhd.py` (주어진 응답을 읽는 순수 파서·쪽 나누기 계획, PR #142 `d835d9f`), `docs/didm/EODHD_SUPPLIED_INPUT_CONTRACT_2026-11-23.md`, `tests/didm_eodhd_acceptance.py` | HTTP 클라이언트 (`data/didm/eodhd.py`), 키 이름, 수집기 옵션, 저장소 행 변환 |
| Alpaca News | `core/didm/ingest/alpaca_news.py` (주어진 응답 파서, PR #143 `5af3787`), `tests/didm_alpaca_news_acceptance.py` | HTTP 클라이언트, 키 이름, 수집기 옵션, 저장소 행 변환 |
| Massive (옛 Polygon.io) ticker news | `data/didm/massive_news.py` (주어진 쪽 파서, 가져오기 없음), `core/didm/ingest/massive_news.py` (기록·시각 검사), PR #144 `51b8298`, `tests/didm_massive_news_acceptance.py` | HTTP 호출, 키 이름, 수집기 옵션, 저장소 행 변환 |

- `core/credentials/names.py`에 세 공급사의 키 이름이 **없습니다** (연구용 9개만).
- GPT 인계가 말하는 "B6 공급원 표" (`B6_PROVIDER_MAPPING_2026-11-23.md`)는 저장소·handoff에 없고 소유자 확인 기록도 없습니다. 그래서 **세 공급사를 쓸지 자체가 소유자 확인 대상**입니다 (아래 4절 질문 N0).

## 1. 무엇을 채우나 (평가표 정보 유형 기준)

| 공급사 | 채우는 칸 | 지금 그 칸을 채우는 것 | 더하는 가치 |
|---|---|---|---|
| EODHD Economic Events | T 발표치·컨센서스, K 미국 거시 이벤트 감시 | 엑셀: Trading Economics (유료·견적, Stage 3 뒤) | 컨센서스로 "예상 대비 충격" 계산 (사전등록 4절). **단, 과거 예상치는 발표 시점 증거가 없어 과거 검증에 못 씀** (EODHD 계약 문서) → 앞으로 쌓는 값에만 의미 |
| Alpaca News (Benzinga) | F 뉴스 수집, H 티커 태깅, P 과거 뉴스 (2015~) | GDELT (2015-02~, 금융 특화 아님), EDGAR·OpenDART (공시) | 티커 붙은 금융 뉴스 메타데이터 (공급사 안내상 2015년부터). **무료 조회·저장 권리·이력 깊이가 확인되면** Stage 2 (2015~2024) 사건연구 표본 후보 (미검증, 아래 3절). 과거 구간은 PREREG 5절 1항대로 `published_at` + 1거래일 지연; `updated_at`이 `created_at`보다 늦은 기사는 표시하고 따로 셈 (파서 계약상 `created_at`·`updated_at`은 변하지 않은 과거 판을 보증하지 않음). 감성 점수 없음 (자체 NLP) |
| Massive ticker news | F, H, G (기사별 종목 감성 `insights`, 있으면) | GDELT + 자체 NLP | 종목별 감성이 붙은 뉴스. 무료 이력 깊이는 미검증. **감성 점수는 PREREG 5절 5항 확인 (과거 값이 당시 계산값인지) 전에는 과거 검증에 쓰지 않음** (파서 계약: 기사 시각이 감성 부여 시각을 보증하지 않음) |

## 2. 키 이름 (결제·계정 세션에 요청, 값 없음)

`core/credentials/names.py`의 `RESEARCH`에 더해 달라고 요청합니다 (그 파일은 결제·계정 세션 소유; 이 세션은 고치지 않음). 넣기 전까지 `data/didm/keys.py`는 환경변수로 읽습니다.

| 이름 (제안) | 공급사 | 보내는 곳 (공개 문서 기준, 미검증) |
|---|---|---|
| `EODHD_API_KEY` | EODHD | 쿼리 `api_token` → URL에 키가 들어가므로 로그·오류 문구에 URL 금지 |
| `ALPACA_API_KEY_ID` | Alpaca | 헤더 `APCA-API-KEY-ID` |
| `ALPACA_API_SECRET_KEY` | Alpaca | 헤더 `APCA-API-SECRET-KEY` |
| `MASSIVE_API_KEY` | Massive | 헤더 `Authorization: Bearer` (쿼리 `apiKey`도 가능하다는 자료 있음 → 헤더 사용) |

## 3. 소유자 가입 표 (요금·권리 **미검증**, 2026-11-24 검색 요약)

| 공급사 | 무료로 확인할 수 있나 | 유료 (자료마다 다름) | 개인/상업 | 먼저 확인할 것 |
|---|---|---|---|---|
| EODHD | Economic Events는 **ALL-IN-ONE 묶음**에만 있는 것으로 보임 → 무료 확인 어려움 | ALL-IN-ONE 월 $89.99~$99.99 (홍보 페이지마다 다름) | 개인 요금제는 개인용, 상업은 Startups/Enterprise 별도 | 이 요금제에 Economic Events 포함 여부, 예상치 발표 시점·버전 기록 유무, 저장·학습 허용 |
| Alpaca News | Basic (무료) 계정으로 REST 뉴스가 되는지 **자료가 엇갈림** (2021 베타 공지는 무료, 사용자 글은 403 "Subscription does not permit querying news") | Algo Trader Plus 등 시세 유료 요금제 (가격 미확인) | 증권사 계정 (모의 계정 가입으로 키 발급 가능 여부 미검증) | 무료 키 1회 호출 (OA-08과 같은 방식), 뉴스 저장·학습 허용 (원 공급자 Benzinga 조건) |
| Massive | 무료 플랜 있음 (분당 5회, 공식 지식베이스). 뉴스 엔드포인트가 무료에 들어가는지와 이력 깊이는 미검증 | Starter $29 / Developer $79 / Advanced $199 (2026 제3자 정리, 옛 Polygon 가격과 다름) | 개인용 요금제와 사업자 요금제 구분 (미검증) | 무료 키 1회 호출, `insights` (감성) 필드가 무료에 오는지, 저장·학습 허용 |

소유자 답 2 (2026-11-18, 비용 단계)에 따라 **유료 가입은 하지 않습니다.** 무료로 확인할 수 있는 Alpaca·Massive만 소유자 확인 (N0) 뒤에 무료 키로 1회 확인합니다.

**원문 확인 (D14, 2026-11-24, 법률 자문 아님; 자세한 인용·URL은 `SAMPLE_EXPANSION_FEASIBILITY_2026-11-24.md` 9절):**
- Alpaca: 무료 Basic 계정 확인 (docs.alpaca.markets/docs/about-market-data-api), 소유자 PC에서 무료 키로 뉴스 60건 실측 (2026-11-24). 과거 2015~는 옛 판 문서 (v1.4.2) 문구. 호출 한도는 주식 기준 200/분. **저장·파생·상업 이용 약관은 `files.alpaca.markets` PDF라 미검증.**
- Massive: 무료 Basic은 **뉴스 2년치만**, 2021-04 이전은 거의 없음, 감성 (insights)은 2024-07-02부터. 개인 약관은 **개인·비상업·비업무 용도만**, 시장자료 약관 5(g)는 **AI·ML 학습 금지**, 플랜 종료 뒤 30일 안 삭제. → 지금 플랜으로는 DIDM 학습·검증 자료에 쓰지 않는 것을 제안 (소유자 결정).
- Benzinga 묶음 (Massive): 2009-04-27~, 요금 페이지 "$99/month per dataset" (개인 요금표; 사업자 조건은 별도).

- 약관상 연구 표본 제외 (source_id): `alpaca-news`, `krx-listing-datagokr`, `krx-openapi`, `massive-news` — 개인·비상업 약관: 연결 확인용, 연구 표본·학습 불가. 근거: `SAMPLE_EXPANSION_FEASIBILITY_2026-11-24.md` 9·10절 (2026-11-24 원문 확인, 법률 자문 아님). 목록은 `core/didm/ingest/terms.py` 한 곳에 있고, 이 줄과 다르면 `tests.didm_terms_guard_acceptance`가 실패합니다.

## 4. 범위 (DS-5a·5b·5c) — 소유자 확인 전에는 시작하지 않음

| ID | 시작 조건 | 할 일 | 완료 조건 |
|---|---|---|---|
| DS-5b Alpaca News | N0 승인 + 소유자가 무료 키 발급 + 결제·계정 세션이 키 이름 2개 등록 (또는 그 전엔 환경변수) | `data/didm/alpaca_news.py` (헤더 인증, `SourceError`로 공급사 문구·키 가림, 쪽 넘김), 저장소 행 변환 (`published_at` = `created_at`, `updated_at`도 함께 저장해 정정 판은 새 행으로 쌓음, `received_at` = 받은 시각, 본문·요약·이미지 저장 안 함), `collect_daily --alpaca-news` (기간·종목), 고정 자료 시험 | 소유자 PC 1회 실행: 행 수·이력 시작일 출력, 무료 403이면 보류로 기록 |
| DS-5c Massive news | DS-5b와 같음 (키 1개) | `data/didm/massive_news.py`에 HTTP 함수 추가 (기존 파서 재사용), 저장소 행 변환, `collect_daily --massive-news`, 분당 5회 제한 지키기 | 소유자 PC 1회 실행: 행 수, `insights` 유무, 이력 시작일 |
| DS-5a EODHD Economic Events | N0 승인 + **소유자 유료 결정** (무료 확인 불가) | `data/didm/eodhd.py` (쿼리 키, 기존 쪽 나누기 계획 사용), 저장소 행 변환 (예상치는 발표 시점 증거가 없으면 `historically_eligible=false` 유지), 수집기 옵션 | 소유자 PC 1회 실행, 예상치 발표 시점 증거 유무 기록 |

공통: 공급사 호출은 `data/didm/`에만 (D7-G), core는 주입 함수만. 키는 `data/didm/keys.py`. 수집 자료는 저장소 밖. 앱 화면에는 보이지 않음 (보이려면 `routes.json`·`display_rights.json`·법률 의견 = 구조 변경, 소유자에게 먼저 알림).

## 5. 소유자 질문

- **N0.** EODHD·Alpaca·Massive 세 곳을 DIDM 공급원으로 더하는 것을 원하십니까? (GPT가 파서를 만들었으나 저장소에 소유자 확인 기록이 없음.) 원하시면 무료로 확인 가능한 Alpaca·Massive부터.
- **N1.** EODHD (월 약 $90~100, 미검증)는 소유자 답 2대로 Stage 3 뒤 판단으로 둘까요?

## 6. 출처 (2026-11-24 검색 요약, 미검증)

- EODHD 요금·Economic Events 포함: https://eodhd.com/pricing , https://eodhd.com/financial-academy/financial-apis-manuals/economic-events , https://eodhd.com/commercial-pricing
- Alpaca 뉴스: https://docs.alpaca.markets/us/docs/historical-news-data , https://docs.alpaca.markets/us/docs/about-market-data-api , https://alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news , https://forum.alpaca.markets/t/news-api-endpoint-suddenly-returns-403/14919
- Massive: https://massive.com/knowledge-base/article/what-is-the-request-limit-for-massives-restful-apis , https://massive.com/compare/massive-vs-tiingo.md , https://try.qveris.ai/polygon-pricing-optimized/
- 저장소: `core/didm/ingest/{eodhd,alpaca_news,massive_news}.py`, `data/didm/massive_news.py`, `docs/didm/EODHD_SUPPLIED_INPUT_CONTRACT_2026-11-23.md` (origin/main `b872d8c`).
