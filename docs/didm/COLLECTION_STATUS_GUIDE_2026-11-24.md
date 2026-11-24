# DIDM 수집 현황 점검 안내 (D4, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 D4). 코드: `tools/didm/collection_status.py`, 시험: `tests/didm_collection_status_acceptance.py` (합성 저장소, 네트워크 없음).
- 목적: 소유자 PC의 일별 수집 (`tools/didm/collect_daily.py`)이 공급원별로 실제 몇 건, 어느 기간을 쌓았고 어느 날이 빠졌는지 명령 한 줄로 확인. DIDM_DEV가 Stage 2 표본 (2015~2024)에 쓸 수 있는 것과 없는 것을 2절 표로 정리.

## 1. 명령 한 줄 (읽기만)

PowerShell, `QUANTGEN_didm` 폴더에서:

```
python -m tools.didm.collection_status --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm"
```

| 선택 | 뜻 |
|---|---|
| `--since 2026-11-17` | 빠진 날을 이 날부터 셈 (기본: 그 공급원의 첫 수신일) |
| `--sample 2015 2024` | 표본 연도 범위 (기본 2015~2024) |
| `--json` | 같은 내용을 JSON으로 (메인·DIDM_DEV에 붙여 줄 때) |
| `--by-entity` | (D13) 공급원별로 회사·계열 식별자 (CIK, corp_code, 뉴스 종목 기호, Kalshi 티커, ALFRED·ECOS 계열)마다 건수·기간·연간 건수. 식별자만 나오고 제목·값은 나오지 않음. GDELT처럼 식별자 필드가 없는 공급원은 빠짐. 대형주·소형주 사건율 비교용 (`SAMPLE_EXPANSION_FEASIBILITY_2026-11-24.md` 4절) |

- 저장소 파일 `didm_store.sqlite`를 SQLite **읽기 전용** 모드로 엽니다. 파일이 없으면 만들지 않고 "no store"로 끝납니다 (시험이 확인: 쓰기 거부, 파일 해시 불변, 빈 폴더 그대로).
- 출력은 공급원 이름·종류·건수·날짜뿐입니다. 기사 제목·URL·값·키는 출력하지 않습니다 (시험이 확인).

### 출력 읽는 법

한 줄 예 (합성 자료):

```
gdelt-gkg2 / gdelt_gkg: items 3 (versions 3), valid 2026-11-17..2026-11-20, received 2026-11-17..2026-11-20 on 3 days, missing 1 days (e.g. 2026-11-19), sample years with data 0/10
```

| 값 | 뜻 | 볼 점 |
|---|---|---|
| `items` | 서로 다른 항목 수 (기사·공시·관측치) | 0이면 그 공급원은 아직 수집 안 됨 |
| `versions` | 저장된 행 수 (같은 항목 재수신·정정 포함) | items보다 많으면 같은 것을 여러 번 받은 것 (정상, 덮어쓰지 않음) |
| `valid` | 자료가 가리키는 시각의 범위 (기사 시각, 관측일) | Stage 2 표본에 들어가는지 판단 |
| `received` | 수집기를 돌린 날의 범위 | 마지막 날이 오늘과 멀면 일별 수집이 멈춘 것 |
| `missing N days` | 첫 수신일 (또는 `--since`)부터 저장소 마지막 수신일 사이에 그 공급원이 아무것도 받지 않은 날 수 | GDELT·Kalshi 일별 수집이면 0이어야 함. ALFRED·ECOS·EDGAR처럼 필요할 때만 돌리는 것은 빈 날이 정상 |
| `sample years with data a/b` | 표본 연도 중 자료가 한 건이라도 있는 해 | `--json`의 `sample_years`에 연도별 건수 |

- 약관상 연구 표본 제외 (source_id): `alpaca-news`, `krx-listing-datagokr`, `krx-openapi`, `massive-news` — 개인·비상업 약관: 연결 확인용, 연구 표본·학습 불가. 근거: `SAMPLE_EXPANSION_FEASIBILITY_2026-11-24.md` 9·10절 (2026-11-24 원문 확인, 법률 자문 아님). 목록은 `core/didm/ingest/terms.py` 한 곳에 있고, 이 줄과 다르면 `tests.didm_terms_guard_acceptance`가 실패합니다.

## 2. Stage 2 표본 (2015~2024)에 지금 수집기로 채울 수 있는가

기준: 이 저장소의 지금 코드 (main `de32ea1` + DS-5b/5c 브랜치 `claude/ds-5bc-news-20261124` + D6·D7 브랜치 `claude/ds-edgar-history-20261124`, D8 갱신 2026-11-24). "채움"은 코드 변경 없이 소유자가 명령으로 받을 수 있다는 뜻입니다.

| 공급원 (`source_id`) | 2015~2024 채움 | 방법·한계 | 시점 (point-in-time) 주의 |
|---|---|---|---|
| GDELT 2.0 사건·GKG (`gdelt-events2`, `gdelt-gkg2`) | **가능 (양이 큼)** | `--gdelt-day YYYYMMDD [--gdelt-gkg]`로 하루 96개 파일. GDELT 2.0 15분 파일은 2015-02 중순부터라 2015-01~02 초는 없음. 10년이면 약 35만 파일이라 표본 날짜를 골라 받는 것을 권함 | 파일 시각 = 공개 시각. 되받은 날 `received_at`은 오늘이므로 과거 시점 재현은 `published_at` 기준 |
| ALFRED 빈티지 (`alfred`) | **가능** | `--alfred SERIES` (FRED_API_KEY) 또는 소유자 내려받기 파일 | **진짜 시점 자료**: 빈티지별 `realtime_start`로 그 날 알 수 있던 값 재현 (`value_as_known_on`) |
| ECOS (`ecos`) | **가능** | `--ecos "STAT,CYCLE,START,END,ITEM"` (따옴표 필수) | 개정 이력 없음 (최신값만). 과거 시점 재현은 발표 지연 가정 필요 |
| SEC EDGAR (`sec-edgar`) | **가능 (D6 뒤)** | `--edgar-history CIK --edgar-from 2015-01-01 --edgar-to 2024-12-31`: `filings.recent`와 기간에 겹치는 과거 파일 (`filings.files`)을 함께 읽음. 회사당 과거 파일 상한 `--edgar-max-files` (기본 10), 출력의 `complete False`면 상한을 올려 다시. 기본 서식 8-K·6-K·10-Q·10-K. D6 전 `--edgar`는 최근 약 1,000건만 | 접수 시각 (`acceptanceDateTime`) = 공개 시각. 없으면 접수일 00:00 뉴욕 시각 + `time_precision` "date" (+1 거래일 지연, OpenDART와 같음) |
| OpenDART (`opendart`) | **가능 (나눠 받기)** | `--opendart BGN END`. 회사 지정 없는 전체 목록은 한 번에 짧은 기간만 허용되므로 (OpenDART 안내, 이 세션에서 다시 확인 못함) 기간을 잘라 여러 번 | 접수일만 있음 (시각 없음) |
| Kalshi (`kalshi`) | **불가 (2015~2020)**, 2021~ **가능 (D7 뒤, 미검증)** | Kalshi 시장은 2021년 이후. `--kalshi-history KXFED --kalshi-from 2021-07-01 --kalshi-to 2024-12-31`: 정산·마감·진행 중 시장의 일봉 (개장~마감, 365일 창). 시리즈당 시장 상한 `--kalshi-max-markets` (기본 200). 오래된 시장의 일봉을 지금 API가 주는지, `min_close_ts` 필터가 있는지는 소유자 PC 첫 실행으로 확인 | 일봉은 기간 끝 시각 = 공개 시각 (`end_period_ts`). 현재 스냅샷 (`--kalshi`)은 받은 시각 기준이라 과거 재현 불가 |
| Alpaca 뉴스 (`alpaca-news`, DS-5b 브랜치) | **미확인** | `--alpaca-news SYM --news-start 2015-01-01`. 공급사 안내상 2015년부터 있으나 무료 계정이 REST 뉴스를 허용하는지 소유자 실행 전 모름 | 기사 `updated_at` 정정은 새 행으로 쌓임. 되받은 날 `received_at`은 오늘 |
| Massive 뉴스 (`massive-news`, DS-5c 브랜치) | **미확인** | `--massive-news TICKER --news-start ...`, 무료 분당 5회. 무료 플랜의 과거 깊이 모름 | 위와 같음 |
| Alpha Vantage·Tiingo·CryptoPanic 뉴스 | **보류** | 무료로 과거 뉴스 안 됨 (OA-08 결과, DS-4b 보류) | — |
| EODHD (DS-5a) | **보류** | 유료, 소유자 N1 답 대기 | — |
| FinBERT 기준 점수 (`finbert-baseline`) | 표본 기사에 따라감 | `--finbert` (GKG 제목에만) | 계산 시각 = 수신 시각 |

### DIDM_DEV에 전할 핵심

1. 과거 자료를 지금 받으면 `received_at`이 전부 오늘 날짜입니다. 저장소의 `as_of(t)`는 "우리가 언제 받았나" 기준이라 2015~2024 시점 재현에는 쓸 수 없고, **`published_at` (공개 시각) + 사전등록한 지연**으로 대신해야 합니다. 예외는 ALFRED (빈티지가 진짜 시점).
2. 뉴스 본문은 어느 공급원에서도 저장하지 않습니다 (제목·메타데이터만). 본문이 필요한 모형이면 DS 쪽에 따로 요청해 주세요.
3. D6 (EDGAR 과거 목록)·D7 (Kalshi 과거 일봉)으로 코드 쪽 빈칸은 메웠습니다. 남은 빈칸은 공급원 사정 (Kalshi 2015~2020 없음, 뉴스 무료 한계)이라 코드로 메울 수 없습니다.

### 소유자 실행 예 (D6·D7, 병합 뒤)

```
python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --edgar-history 320193 --edgar-from 2015-01-01 --edgar-to 2024-12-31
python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --kalshi-history KXFED --kalshi-from 2021-07-01 --kalshi-to 2024-12-31 --kalshi-max-markets 20
python -m tools.didm.collection_status --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm"
```

EDGAR는 `SEC_EDGAR_USER_AGENT`가 있어야 하고, Kalshi는 키가 없습니다. 마지막 줄로 `sec-edgar`·`kalshi / kalshi_candle`의 `sample years with data`를 확인합니다.

## 3. 시험

```
python -m unittest tests.didm_collection_status_acceptance
```

2026-11-24: 7개 통과 (네트워크 없음). 합성 저장소 (GDELT 3일 중 하루 빔, ALFRED 3항목 × 2번 수신)로 건수·기간·빠진 날·표본 연도, `--since`·`--json`·`--sample`, 읽기 전용 (쓰기 거부, 파일 해시 불변, 없는 저장소를 만들지 않음), 본문 비출력, 빈 저장소를 확인.

D6·D7 시험: `tests.didm_edgar_history_acceptance` 9개, `tests.didm_kalshi_history_acceptance` 7개 (오프라인).

D13 시험: `tests.didm_collection_status_acceptance`에 4개 추가 (최신 판만 셈, 기사 하나가 여러 종목이면 각각 셈, 태그 없는 항목 수, 식별자만 출력, 긴 목록은 위·아래 5개만 글로).
