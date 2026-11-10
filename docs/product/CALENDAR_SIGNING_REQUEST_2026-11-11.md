# 달력 파일 서명 요청 목록 (2026-11-11)

소유자 결정 3번("3-승인(행 목록 요청)", 2026-11-11)에 따라 뽑은 목록입니다. 누출 감사 LA-02로 본문을 갖춘 시험 가운데
네 개는 자료가 들어와도 서명된 달력이 과거를 덮지 못해 계속 '소유자 대기(OWNER)'로 남습니다. 이 문서는 그 시험들이
어느 파일의 어느 기간과 어느 행을 기다리는지 적습니다.

- 서명은 소유자만 합니다. Claude는 `signed_off_by`, `signed_utc`, `md5` 칸을 쓰지 않았고, 이번 작업에서
  `core/calendars/data/` 아래 파일은 하나도 바꾸지 않았습니다.
- 아래 내용은 기억이 아니라 코드에서 뽑았습니다. 시험 파일이 선언한 필요 범위(`CLOSE02_NEEDS`, `STALE01_CAL_FILES`,
  `STALE01_CAL_SPAN`, `REPLAY_CAL_NEEDS`, `AVAIL01_NEEDS`, `_official_calendar`, T-REGIME-01 관문)를 읽고, 각 관문을
  배포된 달력(`CalendarSet()`)에 실제로 돌린 결과를 "오늘 실행한 결과"에 그대로 붙였습니다.
- 사양은 `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`이고, `L2015`처럼 적은 것은
  그 파일의 줄 번호입니다.

## 한눈에 보기

기다리는 시험이 많은 파일부터 적었습니다.

| 순서 | 파일 | 지금 서명된 범위 | 시험에 필요한 범위 | 이 파일을 기다리는 시험 |
| --- | --- | --- | --- | --- |
| 1 | `holidays_KRX.yaml` | 2026-01-01 ~ 2027-12-31 | 1997-01-01부터 끊김 없이 | 4개: T-CLOSE-02, G-STALE-01(T-STALE-01), T-AVAIL-01, T-SAT-01(F01) |
| 2 | `kr_sessions.yaml` | 1995-01-01 ~ 2027-12-31 (범위는 충분) | 행 2종 추가, `owner_must_sign` 4개 항목 정리 | 1개: T-CLOSE-02 (KR 조항 8개) |
| 3 | `holidays_NYSE.yaml` | 2025-01-01 ~ 2027-12-31 | 2015-12-04부터 | 1개: G-STALE-01 |
| 4 | `holidays_CBOE.yaml` | 2025-01-01 ~ 2027-12-31 | 2015-12-04부터 | 1개: G-STALE-01 |
| 5 | `holidays_JPX.yaml` | 2025-01-01 ~ 2027-12-31 | 2024-10-28부터 | 1개: T-CLOSE-02 (JP 조항 1개) |
| 참고 | `kr_regime_tags.yaml` | 1995-01-01 ~ 2027-12-31 (충분) | 서명 범위는 더 필요 없음 | T-REGIME-01은 기대값 파일(소유자 산출물)을 기다림 |

시험이 풀리는 조건을 시험별로 보면 이렇습니다.

| 시험 | 풀리려면 | 자료 파일도 필요한가 |
| --- | --- | --- |
| T-AVAIL-01 (공식 달력) | `holidays_KRX`가 2015-01-01 ~ 2015-01-06과 2025-11-13을 덮음 | 아니요. 달력만 넓어지면 바로 PASS 또는 FAIL이 나옵니다 |
| T-SAT-01 (F01) | `holidays_KRX`가 1997-01-03 ~ 2026-10-02를 덮음 | 예. KRX 공식 종가 파일 F01 |
| G-STALE-01 / T-STALE-01 | `holidays_KRX`, `holidays_NYSE`, `holidays_CBOE`가 2015-12-04 ~ 2026-10-25를 덮음 | 예. FRED 파일 4개 |
| T-CLOSE-02 (서명 파일) | 1번, 2번, 5번이 모두 끝남 | 아니요. 달력만으로 실행됩니다 |

## 서명은 어떻게 기록되는가

- 서명은 파일 머리의 세 칸 `signed_off_by`, `signed_utc`, `md5`와 모든 행의 `signed_off_by`, 그리고
  `core/calendars/data/MANIFEST.yaml`에 있는 그 파일 행(`version`, `md5`, `signed_off_by`, `test_ids`)으로 기록됩니다.
  `md5`는 세 서명 칸을 뺀 내용의 md5입니다(`core/calendars/store.py`의 `content_md5`).
- 읽을 때 검사하는 곳은 `core/calendars/store.py`의 `parse_file`입니다. 서명 칸이 비었거나, 내용이 바뀌어 md5가
  맞지 않거나, MANIFEST 행이 없거나 다르면 그 파일을 거부합니다(`CalendarUnsigned`). 그 모듈의 설명문은 "This module
  never writes a signature"라고 적고 있습니다(사양 L2088, L2100).
- 서명을 쓰는 도구는 `tools/sign_calendars.py`이고 소유자만 실행합니다("Run by the owner only: the library and the
  build never sign", 사양 L2100).

  ```
  python -m tools.sign_calendars --signer "<서명자 이름>" holidays_KRX holidays_NYSE
  ```

  도구는 서명 전 내용의 지문(md5)을 먼저 보여 주고, `SIGN`을 입력해야 기록합니다.
- 이미 서명된 파일은 그대로 다시 서명할 수 없습니다. 도구가 "already signed; a change is a new version with a new
  signature"라며 거부합니다. 기간을 넓히거나 행을 더하는 것은 새 버전입니다. 내용을 바꾸면 옛 서명의 md5와 맞지 않아
  서명 전까지 그 파일이 거부되고, 그 시장의 입력은 닫힌 상태가 됩니다(사양 L2053, L2088).
- 새 버전에는 MANIFEST 행에 시험 ID가 있어야 합니다(`change_control.test_per_change: required`, 사양 L2053).
  `MANIFEST.yaml`의 `status`는 파일 하나를 다시 서명하면 세트 버전도 올리고 세트 서명을 새로 해야 한다고 적고 있습니다.
- 지금 상태는 `python -m core.calendars.store`로 볼 수 있습니다. 읽기만 하며 파일별 범위와 `owner_must_sign` 항목을
  출력합니다.

## 파일별 요청

### 1. `holidays_KRX.yaml` (KRX 휴장일)

- 지금: v1.0.0, 2026-01-01 ~ 2027-12-31, 33행.
- 필요한 범위와 그 이유:

  | 시험 | 읽는 기간 | 선언한 곳 |
  | --- | --- | --- |
  | T-CLOSE-02 | 1997-01-01 ~ 1997-06-07, 1999-01-01 ~ 1999-03-02, 2014-01-01 ~ 2014-06-02, 2015-01-01 ~ 2015-11-12, 2016-01-01 ~ 2016-08-01, 2025-01-01 ~ 2025-11-13 | `tests/macro_m1_calendars.py`의 `CLOSE02_NEEDS` |
  | G-STALE-01 / T-STALE-01 | 2015-12-04 ~ 2026-10-25 | `tests/macro_m1_pit.py`의 `STALE01_CAL_SPAN` |
  | T-AVAIL-01 | 2015-01-01 ~ 2015-01-06, 2025-11-13 | `tests/macro_m1_pit.py`의 `AVAIL01_NEEDS` |
  | T-SAT-01 (F01) | 1997-01-03 ~ 2026-10-02 | `tests/macro_m1_calendars.py`의 `F01_SPAN` |

  한국 거래일 하나를 판정할 때 코드는 그해 1월 1일부터 읽습니다(그해 첫 거래일인지 확인,
  `core/calendars/clocks.py`의 `_is_first_trading_day`). 그래서 각 기간이 1월 1일에서 시작합니다. 파일의 범위는 하나의
  이어진 구간(`covers.from` ~ `covers.to`)이므로 **1997-01-01부터 지금의 2027-12-31까지 끊김 없이** 덮어야 네 시험이 모두
  풀립니다.
- 서명할 행: 그 기간의 모든 KRX 휴장일(`kind: closed`). 공휴일, 대체공휴일, 임시공휴일, 선거일, 연말 휴장일이
  들어갑니다. 1998-12-12 이전의 토요일 거래일은 행이 아니라 규칙(`saturday_sessions_before`)으로 처리되므로, 그 시기에는
  토요일에 쉰 날만 휴장일 행으로 넣으면 됩니다.
- 파일이 스스로 적은 `owner_must_sign` (원문):
  - `KRX holiday list 1995-01-01 .. 2027-12-31 from the KRX notices (substitute and election holidays)`
  - `signed_off_by on every row and at file level; md5; MANIFEST row`
- 소유자가 서명한다고 적은 사양 줄: L1449(휴장일 달력은 공식 공지에서 오고 "each change needs an owner sign-off and one
  test"), L2053(변경은 소유자 서명이 있는 새 버전), L2100(서명 없는 달력은 읽을 때 거부).
- 자료 생성까지 보면: 결정 2로 고친 생성기가 Yahoo ^KS11 파일(F13, 1996-12부터)의 시각을 찍으려면 1996-01-01부터
  필요합니다(아래 "자료 생성기가 읽는 범위"). 파일이 스스로 정한 목표인 1995-01-01부터 서명하시면 시험과 생성 모두를
  덮습니다.

### 2. `kr_sessions.yaml` (KRX 거래 시간 규칙)

- 지금: v1.0.0, 1995-01-01 ~ 2027-12-31, 24행(`regular_open` 2, `lunch_break` 2, `csat_day` 20: 2008-11-13부터
  2027-11-18까지). `saturday_close`, `csat_window`, `csat_closing_call`, `random_end_extension` 행은 없습니다.
- 기다리는 시험은 T-CLOSE-02 하나이지만, KR 조항 여덟 개가 모두 이 파일을 기다립니다.
- 없어서 기다리는 행 (시험이 그 행의 값을 기대값으로 읽습니다):

  | 필요한 행 | 유효해야 하는 날짜 | 기다리는 조항 | 소유자 서명이라고 적은 사양 줄 |
  | --- | --- | --- | --- |
  | `saturday_close` (토요일 종가 시각 `close_kst`) | 1997-06-07 | KR Saturday 1997-06-07 | L2015("their own (half-day) close time from the KRX notice"), L2067("owner-signed at M1") |
  | `csat_window` (수능일 거래 시간 `window_kst`) | 2015-11-12 | KR pre-2016 CSAT 2015-11-12 | L2013("before 2016-08-01 the CSAT window comes from the KRX notice ... UNVERIFIED until signed"), L2063 |

- `owner_must_sign`에 남아 있어서 기다리는 항목 (원문 네 줄). 시험은 조항이 읽는 행을 이 목록의 항목이 덮고 있으면
  기다립니다. 행을 확정해 서명한 뒤 새 버전에서 그 항목을 목록에서 지워야 풀립니다.

  | `owner_must_sign` 항목 (원문) | 기다리는 조항 | 사양 줄 |
  | --- | --- | --- |
  | `saturday_close rows (saturday_session_close_kst, from_krx_notice): without them decision_time_utc on a pre-1998-12-12 Saturday raises CalendarUnsigned (never the weekday close)` | 1997-06-07 토요일 | L2015, L2067 |
  | `random_end_extension rows for sessions before 2015-06-15 whose conditional random end was triggered` | 2015-06-12 / 2015-06-15, 2014-06-02, 1997-06-07 토요일, 1999-03-02 | L2012("plus any extension the KRX notice records"), L2061(`triggered_extensions: from_krx_notice`) |
  | `csat_window / csat_closing_call rows for CSAT days before 2016-08-01` | 2015-11-12 수능일 | L2013, L2063, L2064 |
  | `the CSAT date list` | 체제 태그 조항을 뺀 KR 조항 전부: 2016-07-29 / 2016-08-01, 2026년, 2015-06-12 / 2015-06-15, 2014-06-02, 2025-11-13, 2015-11-12, 1999-03-02 | L2013 |

- 소유자가 정하실 것:
  - 조건부 랜덤엔드(2015-06-15 이전)가 발동되어 종가가 늦어진 날이 실제로 있었는지. 없었다면 "행 없음"으로 확정하고
    항목을 지웁니다. 행이 없으면 코드는 연장 0초로 읽습니다.
  - 수능일 목록이 2008년 이전에도 필요한지. 파일의 `unverified`가 "CSAT days before 2008 are not listed: whether KRX
    shifted hours on those days is not established"라고 적고 있습니다.
  - 이 대기 방식이 맞는지. `owner_must_sign`에 항목이 남아 있으면 그 행을 읽는 조항을 기다리게 하는 것은 LA-02 2부의
    소유자 질문 14번이고 아직 답이 없습니다.

### 3. `holidays_NYSE.yaml` (NYSE 휴장일·조기 종료)

- 지금: v1.0.0, 2025-01-01 ~ 2027-12-31, 37행.
- 필요: G-STALE-01이 2015-12-04 ~ 2026-10-25를 읽습니다(`STALE01_CAL_SPAN`: 결정 구간 2016-01-04 ~ 2026-09-25를 앞뒤로 한 달
  넓힌 것). T-CLOSE-02의 미국 조항(2025-07-03 ~ 2026-11-27)과 T-LABEL-01(2026-08-01 ~ 2026-10-31)은 오늘 범위 안입니다.
- 서명할 행: 2015-12-04 ~ 2024-12-31의 휴장일(`closed`)과 조기 종료일(`early_close`, 종료 시각 `close_local`).
- 파일의 `owner_must_sign` (원문): `NYSE holiday and early-close list from nyse.com for 1990-01-01 .. 2027-12-31 (T-TZ-01
  needs 2006)`
- 사양 줄: L1449, L2021(조기 종료 13:00 ET), L2053.
- 자료 생성까지 보면: ^GSPC 파일(F14, 1990년부터)의 시각을 찍으려면 1990-01-02부터 필요합니다.

### 4. `holidays_CBOE.yaml` (Cboe 휴장일, VIX 공식 종가 달력)

- 지금: v1.0.0, 2025-01-01 ~ 2027-12-31, 37행.
- 필요: G-STALE-01이 2015-12-04 ~ 2026-10-25를 읽습니다(시험이 선언한 `STALE01_CAL_FILES`에 이 파일이 있습니다).
- 파일의 `owner_must_sign` (원문): `Cboe holiday list (VIX official close calendar), with licence, owner and md5 (spec
  section 9.5)`
- 사양 줄: L6033(JPX, SSE, HKEX, TWSE, CME, Cboe 달력은 공식 공지에서, M1), L1449, L2053.

### 5. `holidays_JPX.yaml` (도쿄 거래소 휴장일)

- 지금: v1.0.0, 2025-01-01 ~ 2027-12-31, 54행.
- 필요: T-CLOSE-02의 도쿄 조항이 2024-10-28 ~ 2024-11-05를 읽습니다. 도쿄 종가가 15:00에서 15:30으로 바뀐 경계
  (2024-11-05, 사양 L2022)를 확인하는 조항입니다.
- 서명할 행: 2024-10-28 ~ 2024-12-31의 휴장일. 시험은 2024-11-04가 도쿄 휴장일이라고 보고 그 주의 마지막 거래일에서 옛
  종가를 읽습니다. 이것은 LA-02 2부 작업자의 지식에 기댄 것이라 서명하실 때 확인이 필요합니다(2부 소유자 질문 17번).
- 파일의 `owner_must_sign` (원문): `JPX trading calendar from the Korea-covariance span, with licence, owner and md5
  (spec section 9.5)`
- 사양 줄: L6033, L2022, L2053.

### 참고. `kr_regime_tags.yaml`과 기대값 파일 (T-REGIME-01)

- 서명 범위는 충분합니다. v1.0.0이 1995-01-01 ~ 2027-12-31로 서명되어 있고 T-REGIME-01 전 구간 시험의 달력 관문은 오늘
  통과합니다.
- 시험이 기다리는 것은 달력 서명이 아니라 기대값 파일 `tests/fixtures/macro/kr_regime_tags_expected.csv`입니다(사양
  L2098: "a committed expected-values file built from the official notices (including `price_limit` before
  Apr-1995)"). 결정 6으로 `ACQUISITION.csv`에 행을 추가했고, 형식(날짜 한 줄에 태그 15개)은 시험이 선언했습니다.
  파일은 아직 없습니다.
- 그 파일을 만들 때 정하실 것이 하나 있습니다. 서명된 파일은 1995-04-01 이전의 `price_limit`을 값 없음(null)으로 두었고
  (`unverified`: "a 17-step fixed-amount schedule, no single fraction"), 사양은 기대값 파일이 그 기간의 `price_limit`을
  포함한다고 적습니다. 기대값 파일에 숫자를 적으면 서명 파일과 달라 그 90일이 FAIL이 됩니다. 기대값도 빈 칸으로 두거나,
  서명 파일의 그 행을 새 버전에서 고쳐야 합니다. 지어낸 기대값 파일로 실제 시험 본문을 돌려 확인했습니다(0.046을 적으면
  90개 값이 다르다고 FAIL).
- 파일의 `owner_must_sign` (원문 세 줄):
  - `exact days from the official notices for every row marked UNVERIFIED`
  - `the committed expected-values file tests/fixtures/macro/kr_regime_tags_expected.csv (T-REGIME-01 full-range clause)`
  - `coverage into 2027 with the 2027 calendars (brief F-4)`

## 오늘 달력 때문에 기다리지 않는 시험

아래 시험은 배포된 서명 달력으로 달력 관문을 통과합니다. 자료 파일만 들어오면 실행됩니다.

- T-PRINT-01 (F01, F13): 2026-02-23 ~ 2026-03-09.
- G-POST-01 두 곳: 2026-09-18 ~ 2026-10-02.
- T-VT-01, T-LABEL-01: `kr_sessions`, `holidays_KRX`(2026-01-01 ~ 2026-10-31), `holidays_NYSE`(2026-08-01 ~ 2026-10-31),
  `publication_schedules`, `source_skipped`.
- T-REGIME-01 전 구간: `kr_regime_tags` 1995-01-01 ~ 2026-12-31.
- T-MISS-01, T-B5-01, G-REF-01은 서명 달력을 읽지 않습니다.

`holidays_FED`(2015-01-01부터), `publication_schedules`(1995-01-01부터), `source_skipped`(2015-01-01부터),
`market_closes`, `holidays_SSE`, `holidays_HKEX`, `holidays_TWSE`는 위 시험들이 읽는 날짜를 오늘 모두 덮습니다. 이
파일들에도 `owner_must_sign` 항목이 있지만 이 문서의 시험을 막지 않습니다.

## 자료 생성기가 읽는 범위 (시험이 아니라 자료 만들기 단계)

결정 2로 고친 생성기(`docs/macro_fixtures.py`)는 참조 종가 파일의 각 행에 그 시장 달력의 종가 시각을 찍습니다. 시험의
대기와는 별개로, 자료 확보(⑨-2) 때 이 범위가 서명되어 있어야 파일을 만들 수 있습니다. 생성기는 `--only F13 F14 F27`처럼
파일을 골라 쓸 수 있고(검토 반영), 고른 파일 가운데 하나라도 거부되면 아무 파일도 쓰지 않습니다. `--only` 없이 전체를
한 번에 쓰는 실행은 서명 범위를 넓혀도 거부됩니다. 자료 행 40개 가운데 24개는 달력 범위가 아니라 규칙 때문에 시각을
찍지 못합니다(등록도 선언도 안 된 id 17개, F16, 발표 시각 일정이 없는 계열 6개. 배포 달력에서 2026-10-01 날짜 하나로
확인). 그 24개는 이 문서의 서명 범위와 무관하며 3부 기록의 질문 4에 있습니다.

| 파일 | 계열 | 읽는 달력 | 필요한 범위 | 확인한 방법 |
| --- | --- | --- | --- | --- |
| F13 `yahoo_KS11_1996-12_2026-10-02.csv` | KS11 | `kr_sessions`, `holidays_KRX` | 1996-01-01부터 | 실행함: 배포 달력에서 1996-12-02 행은 "holidays_KRX ... 1996-12-02 is outside"로 거부. `holidays_KRX`가 1996-06-01에 시작하는 합성 달력에서는 "1996-01-01 is outside"로 거부(1월 1일부터 읽음) |
| F14 `yahoo_GSPC_1990_2026-10-01.csv` | GSPC | `holidays_NYSE` | 1990-01-02부터 | 실행함: 배포 달력에서 1990-01-02 행은 "holidays_NYSE ... is outside"로 거부 |
| F27 `krx_005930_000660_closes_mcap.csv` | 005930, 000660 | `kr_sessions`, `holidays_KRX` | 파일의 첫 날짜가 속한 해의 1월 1일부터 | 2026-10-02 행은 배포 달력에서 찍힘. 파일의 시작 날짜는 모릅니다 |
| F01 `krx_kospi_official_close_1997-01-03_2026-10-02.csv` | KOSPI_OFFICIAL_CLOSE | `kr_sessions`, `holidays_KRX` | 1997-01-01부터, 그리고 1998-12-12 이전의 모든 토요일 거래일에 유효한 `saturday_close` 행. 토요일 종가 시각이 바뀐 적이 없으면 유효 기간을 적은 행 하나로 충분하고, 바뀌었으면 기간마다 한 행 | 코드로 읽음(`core/calendars/clocks.py`의 `_close_time_of`: 토요일에는 그 날짜에 유효한 `saturday_close` 행이 정확히 하나여야 함. 합성 달력은 `effective_to`가 1998-12-11인 행 하나를 씀). 서명 달력으로는 실행하지 못함 |
| F16 `yahoo_KRWX_2004_2026-10-01.csv` | KRWX | 없음 | 정해지지 않음 | 실행함: "no market calendar for its REFERENCE_FILES market 'FX'"로 거부 |

F16은 서명 범위가 아니라 규칙의 문제입니다. 사양의 시장 시계 표(L1289-1291)와 `core/calendars`에 외환 시장의 종가 시계가
없습니다. KRW=X 일별 종가를 어느 달력으로 찍을지는 소유자가 정하셔야 합니다. 선택지는 (가) NYSE 달력을 씀(미국
휴장일의 KRW=X 행은 거래일이 아니라서 거부되고, 16:00 ET는 외환 거래일이 끝나기 전입니다), (나) 달력 파일에 외환 종가
규칙을 새로 서명해 넣음(이번 서명과 함께 할 수 있습니다), (다) F16을 빼고 감. G-POST-01은 F16이 있어야 실행됩니다.

## 오늘 실행한 결과 (원문)

2026-11-11(KST), 이 브랜치에서 캐시·`.env`·네트워크 접근을 거부하는 실행기로 각 관문을 배포된 `CalendarSet()`에 돌렸습니다.
영어 문장은 시험이 NOT_RUN 사유로 내는 그대로입니다.

T-CLOSE-02, `_close02_waiting` (23줄):

```
KR 2016-07-29 / 2016-08-01 close and bound: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2016-01-01..2016-08-01
KR 2016-07-29 / 2016-08-01 close and bound: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
KR 2026-01-02 .. 2026-10-05 sessions and non-sessions: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
KR 2015-06-12 / 2015-06-15 random-end bound: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2015-01-01..2015-06-15
KR 2015-06-12 / 2015-06-15 random-end bound: kr_sessions.yaml v1.0.0 lists 'random_end_extension rows for sessions before 2015-06-15 whose conditional random end was triggered' under owner_must_sign
KR 2015-06-12 / 2015-06-15 random-end bound: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
KR 2014-06-02 conditional random-end bound: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2014-01-01..2014-06-02
KR 2014-06-02 conditional random-end bound: kr_sessions.yaml v1.0.0 lists 'random_end_extension rows for sessions before 2015-06-15 whose conditional random end was triggered' under owner_must_sign
KR 2014-06-02 conditional random-end bound: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
KR CSAT 2025-11-13: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2025-01-01..2025-11-13
KR CSAT 2025-11-13: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
KR pre-2016 CSAT 2015-11-12: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2015-01-01..2015-11-12
KR pre-2016 CSAT 2015-11-12: kr_sessions.yaml v1.0.0 has no signed csat_window row effective on 2015-11-12
KR pre-2016 CSAT 2015-11-12: kr_sessions.yaml v1.0.0 lists 'csat_window / csat_closing_call rows for CSAT days before 2016-08-01' under owner_must_sign
KR pre-2016 CSAT 2015-11-12: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
KR Saturday 1997-06-07: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 1997-01-01..1997-06-07
KR Saturday 1997-06-07: kr_sessions.yaml v1.0.0 has no signed saturday_close row effective on 1997-06-07
KR Saturday 1997-06-07: kr_sessions.yaml v1.0.0 lists 'saturday_close rows' under owner_must_sign
KR Saturday 1997-06-07: kr_sessions.yaml v1.0.0 lists 'random_end_extension rows for sessions before 2015-06-15 whose conditional random end was triggered' under owner_must_sign
KR 1999-03-02 lunch break and closing call: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 1999-01-01..1999-03-02
KR 1999-03-02 lunch break and closing call: kr_sessions.yaml v1.0.0 lists 'random_end_extension rows for sessions before 2015-06-15 whose conditional random end was triggered' under owner_must_sign
KR 1999-03-02 lunch break and closing call: kr_sessions.yaml v1.0.0 lists 'the CSAT date list' under owner_must_sign
JP 2024-10-28 .. 2024-11-05 close: holidays_JPX.yaml v1.0.0 covers 2025-01-01..2027-12-31, needs 2024-10-28..2024-11-05
```

G-STALE-01, `_stale01_waiting` (3줄; 자료 파일 4개가 등록된 뒤에 이 사유가 나옵니다):

```
holidays_CBOE.yaml v1.0.0 covers 2025-01-01..2027-12-31, needs 2015-12-04..2026-10-25
holidays_NYSE.yaml v1.0.0 covers 2025-01-01..2027-12-31, needs 2015-12-04..2026-10-25
holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2015-12-04..2026-10-25
```

T-AVAIL-01, `_avail01_waiting` (2줄):

```
DGS10 dated Fri 2015-01-02 -> KRX close Tue 2015-01-06: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2015-01-01..2015-01-06
CSAT close 2025-11-13 07:30Z: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31, needs 2025-11-13..2025-11-13
```

T-SAT-01 (F01), `_official_calendar(1997-01-03, 2026-10-02)` (F01이 등록된 뒤에 이 사유가 나옵니다):

```
OWNER: the signed KRX clock files must cover 1997-01-03..2026-10-02: holidays_KRX.yaml v1.0.0 covers 2026-01-01..2027-12-31
```

기다릴 것이 없다고 나온 관문:

```
T-VT-01    _replay_waiting (KOSPI 행): []
T-LABEL-01 _replay_waiting (두 행):    []
T-PRINT-01 (F01, F13) _official_calendar(2026-02-23, 2026-03-09): 통과
G-POST-01 (두 곳)     _official_calendar(2026-09-18, 2026-10-02): 통과
T-REGIME-01 _regime01_waiting: []
```

## 확인하지 못한 것

- 넓혀서 서명한 달력으로는 어떤 시험도 실제로 돌려 보지 못했습니다. 위 범위를 서명하면 시험이 PASS한다는 뜻이 아니라,
  그때부터 PASS 또는 FAIL이 나온다는 뜻입니다.
- 시험이 선언한 필요 범위(`CLOSE02_NEEDS` 등)가 코드가 실제로 읽는 날짜와 같은지는 LA-02 1부·2부가 합성 달력에서
  추적해 고정한 것입니다. 이번에는 그 추적을 다시 하지 않고 선언과 관문 결과만 읽었습니다.
- 생성기 표의 F01 줄과 F27의 시작 날짜는 코드와 파일 이름으로 읽은 것입니다. 실제 참조 파일은 이 환경에 없습니다.
- 2015년 이전에 조건부 랜덤엔드 연장이 있었는지, 토요일 종가 시각, 2016-08-01 이전 수능일 거래 시간은 KRX 공지에서만
  알 수 있습니다. Claude는 값을 추정하지 않았습니다.
- 여기 적은 사양 줄 번호는 현재 사양 파일 기준입니다.

## 체크리스트

파일을 고치는 것(새 버전 초안)과 서명하는 것은 다른 일입니다. 초안에 서명 칸을 비워 두는 것까지는 요청하시면 Claude가
따로 준비할 수 있습니다. 이번 작업에는 넣지 않았습니다. 각 행을 공식 출처와 대조하고 서명하는 것은 소유자 일입니다.

- [ ] `holidays_KRX.yaml`: 1997-01-01(권장 1995-01-01) ~ 2025-12-31의 휴장일 행을 더한 새 버전에 서명
- [ ] `kr_sessions.yaml`: 1998-12-12 이전 토요일 종가(`saturday_close`) 행에 서명 (최소한 1997-06-07에 유효한 행)
- [ ] `kr_sessions.yaml`: 2016-08-01 이전 수능일 거래 시간(`csat_window`, `csat_closing_call`) 행에 서명 (최소한
      2015-11-12에 유효한 `csat_window` 행)
- [ ] `kr_sessions.yaml`: 2015-06-15 이전 조건부 랜덤엔드 연장(`random_end_extension`)이 있었는지 확정
- [ ] `kr_sessions.yaml`: 수능일 목록 확정 (2008년 이전 포함 여부)
- [ ] `kr_sessions.yaml`: 확정한 항목을 `owner_must_sign`에서 지운 새 버전에 서명
- [ ] `holidays_NYSE.yaml`: 2015-12-04(F14를 만들려면 1990-01-02) ~ 2024-12-31의 휴장일·조기 종료 행을 더한 새 버전에 서명
- [ ] `holidays_CBOE.yaml`: 2015-12-04 ~ 2024-12-31의 휴장일 행을 더한 새 버전에 서명
- [ ] `holidays_JPX.yaml`: 2024-10-28 ~ 2024-12-31의 휴장일 행을 더한 새 버전에 서명 (2024-11-04 휴장 여부 확인)
- [ ] `MANIFEST.yaml`: 바뀐 파일마다 행(버전, md5, 서명자, 시험 ID)과 세트 버전·세트 서명 갱신
- [ ] 결정: KRW=X(F16)를 어느 달력으로 찍을지 (가 / 나 / 다)
- [ ] 결정: 기대값 파일에서 1995-04-01 이전 `price_limit`을 빈 칸으로 둘지, 서명 파일의 그 행을 고칠지
- [ ] 결정: LA-02 2부 질문 14번 (`owner_must_sign` 항목이 남아 있으면 시험을 기다리게 하는 방식)
