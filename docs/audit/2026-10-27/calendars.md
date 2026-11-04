# 캘린더 검증 감사 (dimension: calendars)

> 작성 메모 (오케스트레이터): 하네스가 조사 에이전트의 보고서 파일 쓰기를 막아, 에이전트가 반환한 보고서 본문(report_md)을 내용 변경 없이 옮겼습니다.


- 작성일: 2026-10-27
- 대상: `/home/user/quantgen`. 저장소 파일은 하나도 수정하지 않았다(`git status`로 확인).
- 근거: 소유자 판정 ①-2(캘린더 구현 승인, 감사 선행), 서명 마감 2026-11-01(spec L2101).

## 0. 결론 요약

1. 16개 데이터 파일은 모두 미서명 초안이다. 로더는 설계대로 모두 거부한다. 현재 KR·US 입력은 모두 fail-closed다.
2. **지금 그대로 서명하면 안 된다.** 마감 대상 4개 파일(KRX, NYSE, FED, SIFMA) 가운데 3개에 내용 오류가 있다.
   - KRX: 휴장일 4일이 빠졌다. 2026-06-03 지방선거와 2026-07-17 제헌절은 **사실**이다. 2027-05-03 노동절 대체와 2027-07-19 제헌절 대체는 **추정**이다.
   - SIFMA: 2026-04-03은 휴장이 아니라 12:00 조기폐장이다. 조기폐장 행도 최대 7건 빠졌다.
   - FED: 파일 자체 규칙과 달리 2027-12-31 행이 없다.
3. 다른 감사자의 단서 2건(KRX 2026-06-03, 2026-07-17 누락)은 둘 다 **사실**로 확인했다. 두 날짜는 exchange_calendars 4.13.2 XKRX에도 없다. 라이브러리가 낡은 것이다.
4. NYSE 2025–2027은 XNYS와 휴장일·조기폐장(13:00) 모두 **일치**한다.
5. kr_sessions에는 2027 수능일(2027-11-18)이 없다. 그날 KR 종가 시각이 06:30Z로 계산된다. 정답은 07:30Z다.
6. 휴장일 파일 7개(CBOE, CME, ECOS, HKEX, JPX, SSE, TWSE)는 행이 0개이고 covers가 null이다. 서명할 수 없고 2027도 커버하지 않는다.
7. 서명하면 기존 테스트 2개가 바로 FAIL이 된다. T-CAL-02 마감 테스트는 조건 없이 NOT_RUN이라 마감 준수를 검증하지 못한다.
8. 커버리지 경보(warn 60 / page 20 / OPS HALT)와 `calendar_change` 거버넌스 이벤트는 운영 코드에 연결되어 있지 않다.
9. 제안 diff 4종(YAML, 테스트, 코드, 레거시 JSON)은 모두 `git apply --check`를 통과했다. 스크래치 트리 결과는 다음과 같다.
   - 초안 상태에 모든 diff 적용: 19 PASS, 5 NOT_RUN.
   - 서명 리허설 사본: 새 테스트 4개 모두 PASS.

## 1. 범위

- 코드: `core/calendars/store.py`, `core/calendars/clocks.py`, `core/calendars/publication.py`(관련 부분), `core/calendars/adapter.py`, 레거시 `core/calendars/__init__.py`.
- 데이터: `core/calendars/data/*.yaml` 16개, `MANIFEST.yaml`, 레거시 `data/calendars/*.json`(KRX, US, HKEX, TSE, SSE, TWSE, index).
- 테스트: `tests/macro_m1_calendars.py`(T-CAL-01/02 등), `tests/engine_acceptance.py` 69–75.
- 명세: `research_notes/QUANTGEN v2 integration map/spec_M1_calendars.md`.
- 소유자 메모 "(-> 공급사필요)"와의 관계: 캘린더는 유료 공급사가 필요 없다. 공식 공지(KRX, NYSE, Fed, SIFMA, HKEX, JPX, SSE, TWSE, 우주항공청)가 원천이다. 보조 교차검증으로 KIS 국내휴장일조회(`chk-holiday`, CTCA0903R, `opnd_yn`)를 쓸 수 있다. 이 API는 3자 자료로만 확인했고 실호출은 하지 않았다(**추정**).

## 2. 방법

- 모든 YAML을 직접 읽어 covers, 행 수, 2026·2027 행을 표로 정리했다(`cal_xcheck.py`).
- exchange_calendars 4.13.2와 대조했다: XKRX, XNYS, XHKG, XTKS, XSHG, XTAI, CMES, XCBF. 범위는 2026-01-01..2027-12-31이다. XSHG는 2026까지만 기록되어 있다.
- 웹 공식 출처는 프록시가 차단했다(9절). WebSearch 요약으로 보도자료와 언론 기사를 확인했다. 출처는 10절에 있다.
- 로컬 캐시를 경험적으로 대조했다(`cache_sessions.py`). 사용한 파일: yf_069500.KS, yf_005930.KS, yf_QQQ, yf_TLT, fred_DGS3MO, fred_DEXKOUS, yf__VIX. 금지 파일 4개(yf_SPY.csv, yf_BTC-USD.csv, binance_BTCUSDT.csv, upbit_KRW-BTC.csv)는 열지 않았다.
- 서명 리허설(`sign_dryrun.py`): 데이터 폴더를 스크래치에 복사했다. 가짜 서명자 "AUDIT-DRYRUN (not an owner sign-off)"로 서명하고 `store.content_md5`로 md5를 계산했다. 그 뒤 `CalendarSet(tmp)`로 적재했다.
- 테스트는 `run_all.py`를 쓰지 않았다. 함수를 프로세스 안에서 직접 호출했다. 저장소의 `python3 -B -m tests.macro_m1_calendars` 결과는 16 PASS / 5 NOT_RUN으로, cloud baseline2와 같다.

## 3. 파일별 커버리지와 2027 커버 여부

2026-11-01 이후 세션 수는 2027-12-31까지 센 값이다(T-CAL-02는 60 이상 필요).

| 파일 | covers.from | covers.to | 행 수 (2026/2027) | 2027 완전 커버 | 2026-11-01 이후 세션 | 판정 |
|---|---|---|---|---|---|---|
| holidays_KRX | 2026-01-01 | 2027-12-31 | 29 (15/14) | 형식상 예, 내용 누락 2일 | 초안 289, 교정 287 (60번째 = 2027-01-27) | CAL-01, CAL-02, CAL-11 |
| holidays_NYSE | 2025-01-01 | 2027-12-31 | 37 (12/11) | 예 | 293 | XNYS와 일치 |
| holidays_FED | 2015-01-01 | 2027-12-31 | 137 (11/11) | 2027-12-31 누락 | 291 | CAL-05 |
| holidays_SIFMA | 2025-01-01 | 2027-12-31 | 45 (15/14) | 오류 1, 누락 최대 7 | 290 | CAL-04 |
| holidays_CBOE / CME / ECOS / HKEX / JPX / SSE / TWSE | null | null | 0 | 아니오(서명 불가) | — | CAL-06 |
| kr_sessions | 1995-01-01 | 2027-12-31 | 22 (CSAT 2026만) | 아니오: 2027 수능 누락 | KRX 세트 따름 | CAL-03 |
| market_closes | 2015-01-01 | 2027-12-31 | 3 (기간 개방) | 형식상 예 | WEEKDAYS | 시각 미검증 |
| publication_schedules | 1995-01-01 | 2027-12-31 | 16 (기간 개방) | 형식상 예 | WEEKDAYS | CAL-12 |
| kr_regime_tags | 1995-01-01 | 2027-12-31 | 58 (기간 개방) | 형식상 예 | KRX | 값 대부분 미검증 |
| source_skipped | 2015-01-01 | 2027-12-31 | 19 (마지막 2025-04-18) | 2026·2027 행 없음 | WEEKDAYS | CAL-09 |

- 교정본 기준 KRX `sessions_left`는 2026-11-01에 287, 2027-09-30에 62다.
- 따라서 2027-10 초에 warn(≤60) 구간에 들어간다. 그 뒤 DISARMED 장부는 ARM할 수 없다(`store.arm_precondition`).

## 4. 2026–2027 행 대조

### 4.1 KRX (`holidays_KRX.yaml`, 레거시 `KRX.json`)

- 초안 YAML = 레거시 JSON = XKRX 4.13.2(29일). 세 자료가 같은 오류를 공유한다.

| 날짜 | 초안 | 기준값 | 출처 | 판정 |
|---|---|---|---|---|
| 2026-06-03 (수) | 개장 | 휴장(제9회 전국동시지방선거) | KRX 2026-05-20 휴장 공지(머니투데이, 한국경제, MBC, 아주경제). 캐시 069500·005930에 행 없음 | 사실 |
| 2026-07-17 (금) | 개장 | 휴장(제헌절 공휴일 재지정, 공휴일법 개정 2026-01-29 본회의 의결) | 같은 KRX 공지. NXT도 휴장. 캐시에 행 없음 | 사실 |
| 2027-05-03 (월) | 개장 | 휴장(노동절 5/1 토의 대체공휴일) | 우주항공청 2027 월력요항(2026-06-29). KRX 2027 공지 전 | 추정 |
| 2027-07-19 (월) | 개장 | 휴장(제헌절 7/17 토의 대체공휴일) | 같음 | 추정 |

- 나머지 행은 모두 공휴일 규정과 일치한다.
  - 2026: 01-01, 02-16~18, 03-02, 05-01, 05-05, 05-25, 08-17, 09-24, 09-25, 10-05, 10-09, 12-25, 12-31.
  - 2027: 01-01, 02-08, 02-09, 03-01, 05-05, 05-13, 08-16, 09-14~16, 10-04, 10-11, 12-27, 12-31.
- 2026-09-28 임시공휴일 지정은 불발했다(보도). 교정 후 KRX 평일 휴장일은 2026년 17일, 2027년 16일이다.
- 특수 세션(XKRX): 2026-01-02와 2027-01-04는 10:00 개장이다. 코드는 config `first_trading_day_open_kst`로 처리한다. 수능일 세션(2026-11-19, 2027-11-18; 10:00–16:30)은 XKRX와 레거시 JSON에 없다.

### 4.2 NYSE

- 2025–2027 휴장일 전부와 조기폐장(2025-07-03, 2025-11-28, 2025-12-24, 2026-11-27, 2026-12-24, 2027-11-26, 모두 13:00)이 XNYS와 같다.
- ICE의 2025–2027 발표 요약과도 맞는다(2027-06-18, 2027-07-05, 2027-12-24 대체일, 2027-11-26 13:00).
- 2027-12-31은 개장이 맞다(NYSE는 토요일 신정을 금요일로 당기지 않는다). **불일치 없음.**

### 4.3 FED

- 2026–2027 행은 연방 휴일 규칙(토요일 휴일은 금요일)과 같다. 예외는 **2027-12-31 누락** 하나다.
- 같은 규칙으로 만든 2021-12-31 행은 :665에 있다(CAL-05).
- Chicago Fed는 2027-06-18과 2027-12-24를 '은행 영업, Board 휴무'로 적는다.

### 4.4 SIFMA

| 날짜 | 초안 | 기준값 | 출처 | 판정 |
|---|---|---|---|---|
| 2026-04-03 | closed | early_close 12:00 | SIFMA 2026-03-20 보도자료, NY Fed operating policy 2026-03-12, 캐시 DGS3MO에 값 있음 | 사실 |
| 2026-07-02 | 행 없음 | early_close 14:00 | SIFMA 2026-06-18 보도자료 | 사실 |
| 2026-04-02, 2026-05-22 | 행 없음 | early_close 14:00 | 관행, TradingHours 등 2차 자료 | 추정 |
| 2027-03-25, 2027-05-28, 2027-07-02, 2027-12-23 | 행 없음 | early_close 14:00 | 관행, MarketBeat, 2021 선례 | 추정 |
| 2025-01-09, 2025-04-17, 2025-05-23 | 행 없음 | early_close 14:00 | 관행 | 추정 |

- 나머지 휴장일은 규칙과 같다(2026-10-12, 2026-11-11, 2027-10-11, 2027-11-11 포함). 2026-11-27, 2026-12-24, 2026-12-31, 2027-11-26, 2027-12-31 14:00도 맞다.

### 4.5 행이 없는 7개 세트: 서명용 참조 목록(교차검증 전용, 원천 아님)

- **HKEX(XHKG, 홍콩 정부 2027 공보 요약과 일치)**
  - 2026 휴장: 01-01, 02-17~19, 04-03, 04-06, 04-07, 05-01, 05-25, 06-19, 07-01, 10-01, 10-19, 12-25.
  - 2026 반일장 12:00: 02-16, 12-24, 12-31.
  - 2027 휴장: 01-01, 02-08, 02-09, 03-26, 03-29, 04-05, 05-13, 06-09, 07-01, 09-16, 10-01, 10-08, 12-27.
  - 2027 반일장: 02-05, 12-24, 12-31.
- **JPX(XTKS, 내각부 축일·춘분 3/21 일요일과 대체 3/22 확인)**
  - 2026: 01-01, 01-02, 01-12, 02-11, 02-23, 03-20, 04-29, 05-04~06, 07-20, 08-11, 09-21~23, 10-12, 11-03, 11-23, 12-31.
  - 2027: 01-01, 01-11, 02-11, 02-23, 03-22, 04-29, 05-03~05, 07-19, 08-11, 09-20, 09-23, 10-11, 11-03, 11-23, 12-31.
- **SSE(XSHG)**
  - 2026: 01-01, 01-02, 02-16~20, 02-23, 04-06, 05-01, 05-04, 05-05, 06-19, 09-25, 10-01, 10-02, 10-05~07.
  - 2027: 국무원 공지 전이라 **만들 수 없다**. XSHG도 2026까지만 있다.
- **TWSE(XTAI)**
  - 2026: 01-01, 02-12, 02-13, 02-16~20, 02-27, 04-03, 04-06, 05-01, 06-19, 09-25, 09-28, 10-09, 10-26, 12-25.
  - 2027(XTAI): 01-01, 02-04, 02-05, 02-08~10, 03-01, 04-05, 04-30, 06-09, 09-15, 09-28, 10-11, 10-25, 12-31.
  - **XTAI 누락 추정**: 2027-04-06(아동절 대체휴일)과 2027-12-24(행헌기념일 12/25 토의 대체휴일). 근거는 행정원 116년 달력 보도다.
- **CBOE(VIX)**: 휴장일은 NYSE와 같다(XCBF도 같다). 조기폐장 종가 시각은 미검증이다.
- **CME**: 레지스트리 소비자가 없다. 세트에서 빼거나 미서명으로 두기를 권한다.
- **ECOS**: 2026-07-06부터 외환시장이 공휴일에도 거래한다(보도). 그래서 KRX 목록 복사는 위험하다(미검증).

### 4.6 기타 파일

- kr_sessions: CSAT 2026-11-19는 맞다(10:00–16:30, 07:30Z, 리허설 확인). 2027-11-18은 누락이다(CAL-03).
- kr_regime_tags: `usdkrw_onshore_hours` 2026-07-06 '24h'는 보도와 맞는다. 나머지 2026 행은 미검증이다.
- market_closes: 시각 3개는 미검증이다. YAML에 `open_local: 09:30`이 따옴표 없이 쓰였지만 문자열로 읽힌다(앞자리 0 때문). `12:00`처럼 쓰면 정수 720이 된다(CAL-13).
- source_skipped: CAL-09.

## 5. 발견사항

### CAL-01 KRX 2026-06-03·2026-07-17 휴장 누락
- **심각도** P1 · **판정** 사실
- **위치**
  - `core/calendars/data/holidays_KRX.yaml:93-112`: 2026-05-25 행과 2026-08-17 행 사이에 행이 없다.
  - `data/calendars/KRX.json`의 holidays 목록.
  - exchange_calendars `xkrx_holidays.py`의 `manually_added_holidays`에 2026-06-03이 없다.
- **재현**
  - `cd /home/user/quantgen && python3 -B <W>/cal_xcheck.py` → `KRX.missing_vs_official`.
  - `python3 -B <W>/sign_dryrun.py` → `KR is_session 2026-06-03: true`, `2026-07-17: true`.
  - `python3 -B <W>/cache_sessions.py` → `weekdays_without_cache_row_not_in_yaml: [2026-06-03, 2026-07-17]`.
- **기대 결과** 두 날짜 모두 휴장이다. 근거는 KRX 2026-05-20 공지다. 증권·파생·일반상품시장이 휴장하고 NXT도 휴장한다.
- **실제 결과** 세 자료(YAML, JSON, XKRX) 모두 개장으로 본다.
- **영향** 그대로 서명하면 KR 시계가 휴장일을 세션으로 본다.
  - `decision_time_utc`가 NotASession 대신 값을 낸다.
  - `completeness_check`가 종가 누락을 보고한다.
  - 리플레이·백테스트의 세션 수와 `gap_sessions`가 틀어진다.
  - 레거시 UI(`core/markets.py:169`)와 DryRunClocks(`core/skills/macro_daily.py:1300`)도 틀린다.
- **수정안** 7.1 diff의 KRX 2026 행 2개를 추가한다. spec L518의 "draft == XKRX" 교차 테스트를 만든다면 XKRX 누락 4일을 허용 목록에 넣는다.
- **회귀 테스트**
  - `test_cal02_known_2026_2027_rows_present`: `MUST_CLOSE['holidays_KRX'] ⊆ closed`.
  - `test_close02_on_the_real_signed_files`: 두 날짜에서 `NotASession`.

### CAL-02 KRX 2027-05-03·2027-07-19 대체공휴일 누락
- **심각도** P1 · **판정** 추정
  - 공휴일 지정 자체는 우주항공청 월력요항 요약으로 확인했다.
  - KRX의 2027 휴장 공지는 아직 없다.
- **위치** `holidays_KRX.yaml:203-242`, `KRX.json`의 2027 목록.
- **재현** `cal_xcheck.py`, `sign_dryrun.py`(두 날짜 `is_session` True).
- **기대 결과** 휴장이다. KRX는 관공서 공휴일에 휴장한다. 2026-05-20 공지에도 "법정공휴일 지정으로 정기 휴장일 포함"이라고 되어 있다.
- **실제 결과** 행이 없다. XKRX에도 없다.
- **영향** 2027년 KR 결정 2회가 휴장일에 잡힌다.
- **수정안** 7.1 diff를 적용한다. KRX 2027 공지(12월 예상) 뒤 다시 대조하고, 다르면 v1.0.1로 재서명한다.
- **회귀 테스트** CAL-01과 같다.

### CAL-03 kr_sessions 2027 수능일 누락
- **심각도** P2 · **판정** 사실
- **위치**
  - `core/calendars/data/kr_sessions.yaml:173-180`: 마지막 `csat_day`가 2026-11-19다. covers.to는 2027-12-31이다.
  - `core/calendars/clocks.py:126-128`, `:159-160`.
- **재현** `sign_dryrun.py` → `KR decision_time_utc 2027-11-18 (CSAT): 2027-11-18T06:30:00Z`. 교정 후에는 07:30:00Z다.
- **기대 결과** 2028학년도 수능은 2027-11-18이다(교육부 2025-06-01 발표). 시장은 10:00–16:30이므로 종가는 07:30Z, bound는 07:30:30Z다.
- **실제 결과** 06:30Z로 계산하고 개장을 09:00으로 본다.
- **영향** 결정 시각이 1시간 이르다. 15:30의 장중 프린트를 종가로 받는다.
- **수정안** `csat_day` 2027-11-18 행을 추가한다(7.1).
- **회귀 테스트**
  - `MUST_CSAT`.
  - `decision_time_utc('KR', 2027-11-18) == 07:30Z`.

### CAL-04 SIFMA 2026-04-03 오류와 조기폐장 누락
- **심각도** P2 · **판정** 사실(2026-04-03, 2026-07-02) / 추정(나머지)
- **위치** `holidays_SIFMA.yaml:155-163`(kind: closed), 조기폐장 행 `:384-433`.
- **재현**
  - `cal_xcheck.py` → `SIFMA.mismatches` 8건.
  - `sign_dryrun.py` → `sifma_status(2026-04-03)='closed'`, `sifma_status(2026-07-02)='open'`.
  - `cache_sessions.py` → DGS3MO에 2026-04-03 값이 있다.
- **기대 결과·실제 결과** 4.4 표 참조.
- **영향** UST_PAR_10Y(obs_calendar SIFMA)가 2026-04-03 관측을 기대하지 않는다. `sifma_status`가 틀린다.
- **수정안** 7.1 diff를 적용한다. 추정 6건은 sifma.org로 확인한 뒤 서명한다.
- **회귀 테스트**
  - `MUST_EARLY`.
  - `sifma_status(2026-04-03)=='early_close'`.

### CAL-05 FED 2027-12-31 누락
- **심각도** P3 · **판정** 사실(파일 내부 불일치). Board 휴무 자체는 추정이다.
- **위치** `holidays_FED.yaml:1245-1253`(마지막 행 2027-12-24). 대응 행 2021-12-31은 `:665`.
- **재현**
  - `cal_xcheck.py` → `FED.yaml_vs_rule_OPM.only_right=[2027-12-31]`.
  - `sign_dryrun.py` → `business_day('FED', 2027-12-31)` True, `2021-12-31` False.
- **기대 결과** 2028-01-01이 토요일이므로 2027-12-31 휴무다.
- **실제 결과** 행이 없다. 생성 루프가 2027년에서 끝나 2028년 대체일이 빠진 것으로 보인다(추정).
- **영향** 2027-12-30 관측의 H.15·H.10 게시 시각이 하루 이르게 계산될 수 있다. 커버리지 마지막 날이라 영향은 작다.
- **수정안** 7.1 diff를 적용한다.
- **회귀 테스트** `MUST_CLOSE['holidays_FED']`.

### CAL-06 휴장일 파일 7개가 빈 골격
- **심각도** P2 · **판정** 사실
- **위치**
  - `holidays_{CBOE,CME,ECOS,HKEX,JPX,SSE,TWSE}.yaml:5-7`(covers null), `:19`(`rows: []`).
  - `store.py:169-171`: covers가 필수다.
- **재현** `cal_xcheck.py` 인벤토리. 교정·서명 사본에서도 7개는 REFUSED이고, `arm_precondition` JP/CN/HK/TW는 False다.
- **기대 결과** 2027-12-31까지 커버하는 서명 가능 파일.
- **실제 결과** 행 0개, covers null이다. 서명해도 로더가 거부한다.
- **영향** 다음 입력이 계속 fail-closed다. 마감 대상 4개를 서명해도 살아나지 않는다.
  - CBOE: VIXCLS, VXVCLS.
  - ECOS: ECOS_1530_CLOSE, BOK_CALL_RATE, KR_CD91, KR_CPI, BOK_BASE_RATE.
  - 교차시장 종가: NIKKEI225, HSI, TAIEX, SHANGHAI.
  - `COVERAGE_FILES`(`store.py:51-55`)는 ECOS와 CBOE를 감시하지 않는다.
- **수정안**
  - 4.5절 목록으로 행을 만들고 공식 공지와 대조해 서명한다.
  - SSE 2027은 국무원 공지 뒤에 만든다.
  - CME는 세트에서 뺀다.
  - `COVERAGE_FILES`에 ECOS(KR)와 CBOE(US)를 추가한다.
- **회귀 테스트** 서명 후 `arm_precondition(2026-11-02, 'JP'/'HK')`가 True. 회귀 행 목록에 HKEX 2027을 추가한다.

### CAL-07 커버리지 경보와 거버넌스 이벤트 미연결
- **심각도** P2 · **판정** 사실
- **위치**
  - `store.py:409-437` `check_coverage`, `:453-479` `record_calendar_changes`.
  - 운영 호출은 `core/skills/macro_daily.py:1095`의 `arm_precondition` 하나뿐이다.
  - `core/engine/books.py:368` `coverage_halt`는 정의만 있다.
- **재현** `grep -rn "check_coverage\|record_calendar_changes" --include=*.py core ui` → 테스트 외 호출이 없다.
- **기대 결과** spec L2077, L2090, L4096에 따라 warn·page·OPS HALT가 나고, 서명 버전마다 `calendar_change` 이벤트가 남는다.
- **실제 결과** 운영 경로에 없다.
- **영향**
  - 2027-10 초 잔여 60세션 이하가 되어도 알림이 없다.
  - 서명 사실이 `governance_events.jsonl`에 남지 않는다.
- **수정안** `macro_daily.app_start`(`:1166-`)에서 두 가지를 한다.
  - `CS.record_calendar_changes(macro_dir / GOVERNANCE_LOG, CS.default().file_ids(), clock)`를 부른다.
  - `CS.status(m, today)["alerts"]`를 AlertStore로 올린다. alert code 등록이 필요하다.
- **회귀 테스트** `test_app_start_records_calendar_change_and_coverage_alert`(가칭).

### CAL-08 서명하면 테스트가 깨지고, 마감 테스트는 영구 NOT_RUN
- **심각도** P2 · **판정** 사실
- **위치** `tests/macro_m1_calendars.py`
  - `:521-550` `test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed`.
  - `:355-364` `test_close02_on_the_real_signed_files_is_owner_input`.
  - `:621-626` `test_cal02_2027_files_signed_before_2026_11_01`.
- **재현** `sign_dryrun.py`는 DATA_DIR를 프로세스 안에서만 바꾼다. 결과:
  - 첫 테스트: `AssertionError: holidays_FED`.
  - 둘째 테스트: `AssertionError`.
  - 셋째 테스트: `NotRun`.
- **기대 결과** 서명 후 T-CAL-01 PASS, T-CAL-02 마감 조항 PASS.
- **실제 결과** 서명하면 2개가 FAIL이 된다. 마감 테스트는 조건 없이 NotRun이다.
- **영향** 서명 커밋이 QA를 깨거나, 마감 조항이 끝내 검증되지 않는다.
- **수정안** 7.2 diff를 적용한다.
- **회귀 테스트**
  - 스크래치 결과: 초안에 diff 적용 시 19 PASS / 5 NOT_RUN. 서명 사본에서 새 테스트 4개 PASS.
  - YAML 수정 전에는 `test_cal02_known_2026_2027_rows_present`가 FAIL이다. 의도한 동작이다.

### CAL-09 source_skipped의 Good Friday가 DGS10만 다룸
- **심각도** P2 · **판정** 사실(코드). 2027-03-26 공백은 추정이다.
- **위치** `source_skipped.yaml:125-198`, `publication.py:198-223`.
- **재현** `repro_source_skipped.py` → 2025-04-17 다음 기대 관측:
  - DGS10: 2025-04-21.
  - DGS2, DTB3: 2025-04-18.
  - 세 시리즈 모두 2027-03-25 다음이 2027-03-26.
- **기대 결과** H.15 모든 시리즈가 채권시장 휴장일을 건너뛴다.
- **실제 결과** DGS10만 건너뛴다. 캐시 DGS3MO에 2025-04-18이 없어 H.15 공백을 뒷받침한다.
- **영향** H.15 시리즈 8개가 Good Friday 다음 KR 결정 1회에서 stale이 된다.
- **수정안**
  - 행을 `series: H.15`(채널)로 바꾼다. `source_skipped()`는 채널 일치를 허용한다(`:206-207`).
  - SIFMA 2027 확인 뒤 2027-03-26을 추가한다.
  - 2026-04-03은 조기폐장이라 필요 없다.
- **회귀 테스트** `next_expected_obs(DGS2, 2025-04-17) == 2025-04-21`.

### CAL-10 레거시 KRX.json (UI·dry-run 사용)
- **심각도** P2 · **판정** 사실
- **위치** `data/calendars/KRX.json`. 사용처: `core/markets.py:169`, `core/skills/macro_daily.py:1300`, `core/calendars/__init__.py:145-160`.
- **재현** `L.is_trading_day('KRX', 2026-06-03)`는 True, `L.special_session('KRX', 2026-11-19)`는 None.
- **기대 결과** 휴장 4일은 False다. 수능일 2일은 10:00–16:30이다.
- **실제 결과** 개장으로 보고, 정규 시간으로 본다.
- **영향**
  - 2026-11-19(23일 뒤) UI 시각 표시가 틀린다.
  - SSE.json은 2026-12-31에 끝난다(`stale_markets`: NSE, SGX, SSE, SZSE).
  - 생성기 `pkg_tools/generate_calendars.py`는 저장소에 없다(기존 보고).
- **수정안** 7.4 diff(CRLF 유지). 적용 사본에서 `engine_acceptance` 69–75번 7개 PASS를 확인했다.
- **회귀 테스트** 위 두 assertion과 69–75번.

### CAL-11 KRX·NYSE 커버 시작이 너무 늦음
- **심각도** P2 · **판정** 사실
- **위치**
  - `holidays_KRX.yaml:5-7`(2026-01-01부터) vs `:20`(1995..2027).
  - `holidays_NYSE.yaml:5-7`(2025-01-01부터) vs `:19`(1990..2027).
- **재현** `sign_dryrun.py` → `KR 2025-11-13`와 `US 2024-12-31`에서 `CalendarCoverageError`.
- **기대 결과** T-CLOSE-02(2016-07-29, 2025-11-13)와 T-TZ-01(2006)을 실파일로 검증할 수 있는 과거 구간.
- **실제 결과** 과거 날짜는 OPS HALT 사유가 된다.
- **영향** 서명 후에도 리플레이·실파일 검증이 막힌다. 마감 자체에는 영향이 없다.
- **수정안** 마감 서명 문장에 커버 범위를 명시한다. 과거 구간은 v1.1.0으로 추가한다.
- **회귀 테스트** `decision_time_utc('KR', 2016-07-29) == 06:00Z`.

### CAL-12 same_day 규칙이 달력 서명을 확인하지 않음
- **심각도** P3 · **판정** 사실
- **위치** `publication.py:156-157`, `core/ficc/pit.py:536`.
- **재현** 교정·서명 사본(ECOS·CBOE는 REFUSED)에서 `publication_instant` ECOS_USDKRW와 VIXCLS_CBOE가 모두 'ok'.
- **기대 결과** 미서명 달력에 의존하는 계산은 거부한다.
- **실제 결과** 시각을 돌려준다. `stamp_release`는 그 시각을 `calendar_bound`로 찍는다.
- **영향** 운영 판단은 `next_expected_obs`에서 막힌다. 스탬프만 영향을 받는다.
- **수정안** 7.3 diff.
- **회귀 테스트** `test_cal01_same_day_schedule_needs_its_signed_calendar`. 현재 코드 FAIL, 수정 후 PASS를 확인했다.

### CAL-13 따옴표 없는 HH:MM 허용
- **심각도** P3 · **판정** 사실
- **위치** `store.py:19-20`(docstring), `:102-110`, `clocks.py:80-84`.
- **재현** `repro_unquoted_time.py` → 로드 성공, 값 720, 사용 시 ValueError.
- **기대 결과** 로드할 때 거부한다.
- **실제 결과** 서명·md5·로드를 통과한 뒤, 사용할 때 실패한다.
- **영향** HKEX 반일장 행을 쓸 때 실수할 위험이 있다.
- **수정안** 7.3 diff.
- **회귀 테스트** `test_cal01_unquoted_time_refused_at_load`. 현재 FAIL, 수정 후 PASS.

### CAL-14 signed_utc가 md5와 MANIFEST 밖에 있음
- **심각도** P3 · **판정** 사실
- **위치** `store.py:37`, `:113-116`, `:145-154`, MANIFEST rows.
- **재현** `sign_dryrun.py` → `signed_utc_outside_md5: true`.
- **기대 결과** 마감 준수 증빙을 바꿀 수 없다. 서명 문장이 파일에 남는다.
- **실제 결과** signed_utc를 바꿔도 검사를 통과한다. 서명 문장 필드가 없다.
- **영향** 증빙이 약하다.
- **수정안** 7.3 diff: MANIFEST에 signed_utc를 기록하고 일치를 검사한다. `sign_off_statement`를 필수로 하고 md5 대상에 넣는다. 픽스처 2줄을 고친다(7.2).
- **회귀 테스트** `test_cal01_unsigned_refused_signed_accepted`에 변형을 추가한다. MANIFEST signed_utc가 다르면 오류에 'signed_utc'가 나와야 한다.

## 6. 서명 절차 (소유자용)

### 6.1 서명 대상
- 마감 4개: holidays_KRX, holidays_NYSE, holidays_FED, holidays_SIFMA.
- KR 시계와 ARM에는 kr_sessions도 필요하다(`MARKET_FILES['KR']`).
- `status()`가 KR·US를 '서명됨'으로 보려면 kr_regime_tags, publication_schedules, source_skipped도 필요하다(`COVERAGE_FILES`).
- **권고: 이 8개를 서명한다.** 7개 골격 파일은 행을 채운 뒤 별도로 서명한다.

### 6.2 소유자가 서명하는 문장 (파일마다 1개)

> 본인 <성명>은 <file_id> v<version>(content md5 <md5>)의 모든 행을 <공식 출처: 예) KRX 휴장일 공지 2026-05-20 / nyse.com hours-calendars / federalreserve.gov K.8 / sifma.org holiday schedule>와 <YYYY-MM-DD>에 대조하였다. <covers.from>부터 <covers.to>까지 휴장·조기폐장 행이 공식 출처와 일치함을 확인한다. 공식 공지가 아직 없는 2027년 행(<날짜 목록>)은 <근거: 2027 월력요항 등>에 따른 것이다. 공지가 나오면 다시 대조하고, 차이가 있으면 새 버전으로 재서명한다. 이 파일은 <covers> 밖의 날짜를 보증하지 않는다.

- 이 문장은 `sign_off_statement` 필드에 넣는다.
- 7.3 코드 diff를 적용하면 이 필드가 필수이고 md5 대상이 된다. 적용하지 않으면 governance 이벤트의 reason과 커밋 메시지에 남긴다.

### 6.3 필드 작성 순서 (순서가 중요하다)
1. 7.1 YAML diff를 적용하거나 같은 내용을 직접 고친다.
2. **모든 행**에 다음 3개를 쓴다.
   - `source_url`: 공식 URL 또는 공지 번호.
   - `retrieved_at_utc`: 실제 조회 시각.
   - `signed_off_by`: 서명자 문자열. 모든 곳에서 글자 하나까지 같아야 한다.
   - 행의 `unverified` 문구는 지우거나 남은 의문만 적는다. 이 문구도 md5 대상이다.
3. 파일 수준 필드를 쓴다.
   - `version: 1.0.0`, `status: SIGNED`.
   - `signed_off_by: <서명자>`.
   - `signed_utc: '2026-10-3xTHH:MM:SSZ'`. **2026-10-31T15:00:00Z(=2026-11-01 00:00 KST) 이전**이어야 한다.
   - `sign_off_statement: '<6.2 문장>'`.
   - `md5: null`.
4. `python3 -B -m core.calendars.store`를 실행하고 그 파일의 `md5=` 값을 읽는다. 이 값은 최상위 `signed_off_by`, `signed_utc`, `md5`만 빼고 계산한 canonical JSON md5다. 이후 행이나 문장을 한 글자라도 바꾸면 md5가 달라진다.
5. 그 값을 파일의 `md5:`에 쓴다.
6. `MANIFEST.yaml`에서 해당 행을 다음처럼 쓴다.
   ```yaml
   - file: holidays_KRX.yaml
     version: 1.0.0
     md5: <4단계 값>
     signed_off_by: <파일과 같은 문자열>
     signed_utc: '<파일과 같은 값>'   # 7.3 diff 적용 시 필수
     test_ids: [T-CAL-01, T-CAL-02, T-CLOSE-02, T-SAT-01, T-TZ-02]
   ```
   MANIFEST 최상위에도 `version`, `signed_off_by`, `signed_utc`를 쓴다. 이것이 `CalendarSet.version`, 즉 `event_calendar.calendar_version`이 된다.
7. 다시 `python3 -B -m core.calendars.store`를 실행해 8개 파일이 `signed`로 나오는지 본다.
8. 서명 리허설은 이 순서대로 했고 모든 파일이 적재됐다. KR·US는 `status.signed=True`였다. `sessions_left`는 KR 287, US 290이었다. `arm_precondition`은 KR·US 모두 True였다.

### 6.4 증명 테스트 (`run_all.py`는 쓰지 않는다)
- 명령: `python3 -B -m tests.macro_m1_calendars`. 결과 파일을 쓰지 않는다.
- 7.2 diff 적용 후 서명 전 기대값: 19 PASS / 5 NOT_RUN.
- 서명 후에는 다음 4개가 PASS여야 한다.
  - `test_cal01_shipped_files_signed_or_refused`: 서명 파일이 MANIFEST와 일치하고 draft status와 FIXTURE 서명자가 없다.
  - `test_cal02_2027_files_signed_before_2026_11_01`: signed_utc가 마감 전이고, covers_to ≥ 2027-12-31, 2026-11-01 이후 세션 ≥ 60, KR·US ARM 가능.
  - `test_cal02_known_2026_2027_rows_present`: 이번 감사에서 찾은 행이 모두 있다.
  - `test_close02_on_the_real_signed_files`: 실파일에서 T-CLOSE-02 값이 맞는다.
- 기존 `test_cal01_unsigned_refused_signed_accepted`, `test_cal01_calendar_change_governance_event`, `test_cal02_coverage_warn_page_halt`는 계속 PASS여야 한다.

### 6.5 거버넌스 기록
- CAL-07이 고쳐지기 전에는 서명 직후 한 번 수동으로 부른다.
- `store.record_calendar_changes(<macro_dir>/governance_events.jsonl, [8개 file_id], clock)`.
- 경로는 `core/skills/macro_daily.py:144`를 따른다. 파일마다 `calendar_change` 이벤트가 1건씩 생긴다.

### 6.6 이후 일정
- KRX 2027 휴장일 공지(12월 예상)가 나오면 대조하고, 차이가 있으면 v1.0.1로 재서명한다.
- 2028 파일은 늦어도 **2027-09**까지 서명해야 한다. 2027-10 초에 잔여 60세션 이하가 되기 때문이다.
- KRX 공지는 12월에 나온다. 따라서 매년 6월 월력요항으로 다음 해 행을 먼저 서명하고, 12월 공지로 재확인하는 2단계가 필요하다.

## 7. 제안 diff (적용하지 않음)

- 스크래치 파일로 `git apply`할 수 있다(9절 경로). 네 diff 모두 `git apply --check`를 통과했다.

### 7.1 YAML (`proposed_yaml.diff`)

```diff
--- a/core/calendars/data/holidays_FED.yaml
+++ b/core/calendars/data/holidays_FED.yaml
@@ -1251,3 +1251,12 @@
   kind: closed
   name: Christmas Day
   unverified: 'UNVERIFIED: derived by the statutory holiday rule, not read from the publisher''s schedule; owner confirms'
+- effective_from: '2027-12-31'
+  effective_to: '2027-12-31'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-12-31'
+  kind: closed
+  name: New Year's Day (observed; 2028-01-01 is a Saturday)
+  unverified: 'UNVERIFIED: the file''s own Saturday -> Friday rule (cf. 2021-12-31); Reserve Banks open, Board closed; owner confirms against federalreserve.gov'
--- a/core/calendars/data/holidays_KRX.yaml
+++ b/core/calendars/data/holidays_KRX.yaml
@@ -13,7 +13,9 @@
   / signed_utc at file level, set md5 to the content md5 printed by `python -m core.calendars.store`, and add the matching
   MANIFEST.yaml row with a new test id
 unverified:
-- 'every date: cross-checked against exchange_calendars XKRX only'
+- 'every date: cross-checked against exchange_calendars XKRX only; XKRX 4.13.2 lacks 2026-06-03, 2026-07-17, 2027-05-03 and
+  2027-07-19 (added from the KRX 2026-05-20 notice and the 2027 월력요항)'
+- 2027 rows follow the public-holiday regulation until the KRX 2027 휴장일 notice (December 2026); re-verify then
 - no CSAT day carried here (see kr_sessions)
 - 2027 must be signed before 2026-11-01 (spec L2101)
 owner_must_sign:
@@ -100,6 +102,24 @@
   name: KRX holiday (name from the KRX notice at sign-off)
   unverified: 'UNVERIFIED cross-check only (exchange_calendars 4.13.2 via data/calendars/*.json, spec L2003: never the source);
     the owner replaces source_url with the exchange notice at sign-off'
+- effective_from: '2026-06-03'
+  effective_to: '2026-06-03'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2026-06-03'
+  kind: closed
+  name: 제9회 전국동시지방선거 (공휴일)
+  unverified: 'UNVERIFIED: absent from exchange_calendars 4.13.2 XKRX; KRX 휴장 공지 2026-05-20 (press: mt.co.kr, hankyung.com, imbc, ajunews); the owner replaces source_url with the exchange notice at sign-off'
+- effective_from: '2026-07-17'
+  effective_to: '2026-07-17'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2026-07-17'
+  kind: closed
+  name: 제헌절 (공휴일 재지정, 공휴일법 개정 2026-01-29 의결)
+  unverified: 'UNVERIFIED: absent from exchange_calendars 4.13.2 XKRX; KRX 휴장 공지 2026-05-20 (press: mt.co.kr, hankyung.com, imbc, ajunews); the owner replaces source_url with the exchange notice at sign-off'
 - effective_from: '2026-08-17'
   effective_to: '2026-08-17'
   source_url: null
@@ -210,6 +230,15 @@
   name: KRX holiday (name from the KRX notice at sign-off)
   unverified: 'UNVERIFIED cross-check only (exchange_calendars 4.13.2 via data/calendars/*.json, spec L2003: never the source);
     the owner replaces source_url with the exchange notice at sign-off'
+- effective_from: '2027-05-03'
+  effective_to: '2027-05-03'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-05-03'
+  kind: closed
+  name: 노동절(5/1 토) 대체공휴일
+  unverified: 'UNVERIFIED: absent from exchange_calendars 4.13.2 XKRX; 우주항공청 2027년 월력요항 2026-06-29; KRX 2027 notice pending; the owner replaces source_url with the exchange notice at sign-off'
 - effective_from: '2027-05-05'
   effective_to: '2027-05-05'
   source_url: null
@@ -230,6 +259,15 @@
   name: KRX holiday (name from the KRX notice at sign-off)
   unverified: 'UNVERIFIED cross-check only (exchange_calendars 4.13.2 via data/calendars/*.json, spec L2003: never the source);
     the owner replaces source_url with the exchange notice at sign-off'
+- effective_from: '2027-07-19'
+  effective_to: '2027-07-19'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-07-19'
+  kind: closed
+  name: 제헌절(7/17 토) 대체공휴일
+  unverified: 'UNVERIFIED: absent from exchange_calendars 4.13.2 XKRX; 우주항공청 2027년 월력요항 2026-06-29; KRX 2027 notice pending; the owner replaces source_url with the exchange notice at sign-off'
 - effective_from: '2027-08-16'
   effective_to: '2027-08-16'
   source_url: null
--- a/core/calendars/data/holidays_SIFMA.yaml
+++ b/core/calendars/data/holidays_SIFMA.yaml
@@ -158,8 +158,9 @@
   retrieved_at_utc: '2026-10-06T00:00:00Z'
   signed_off_by: null
   date: '2026-04-03'
-  kind: closed
-  name: Good Friday (bond market closed)
+  kind: early_close
+  close_local: '12:00'
+  name: Good Friday (employment report day; SIFMA 12:00 ET early close, not a full close)
   unverified: 'UNVERIFIED: derived by the statutory holiday rule, not read from the publisher''s schedule; owner confirms'
 - effective_from: '2026-05-25'
   effective_to: '2026-05-25'
@@ -431,3 +432,73 @@
   close_local: '14:00'
   name: SIFMA early close recommendation
   unverified: 'UNVERIFIED: derived by the statutory holiday rule, not read from the publisher''s schedule; owner confirms'
+- effective_from: '2026-04-02'
+  effective_to: '2026-04-02'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2026-04-02'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Good Friday
+  unverified: 'UNVERIFIED: usual pattern, secondary calendars; owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
+- effective_from: '2026-05-22'
+  effective_to: '2026-05-22'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2026-05-22'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Memorial Day
+  unverified: 'UNVERIFIED: usual pattern; TradingHours lists it; owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
+- effective_from: '2026-07-02'
+  effective_to: '2026-07-02'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2026-07-02'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Independence Day (observed)
+  unverified: 'UNVERIFIED: SIFMA release 2026-06-18; owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
+- effective_from: '2027-03-25'
+  effective_to: '2027-03-25'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-03-25'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Good Friday
+  unverified: 'UNVERIFIED: usual pattern; MarketBeat lists it; owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
+- effective_from: '2027-05-28'
+  effective_to: '2027-05-28'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-05-28'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Memorial Day
+  unverified: 'UNVERIFIED: usual pattern; owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
+- effective_from: '2027-07-02'
+  effective_to: '2027-07-02'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-07-02'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Independence Day (observed)
+  unverified: 'UNVERIFIED: usual pattern; owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
+- effective_from: '2027-12-23'
+  effective_to: '2027-12-23'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  date: '2027-12-23'
+  kind: early_close
+  close_local: '14:00'
+  name: day before Christmas Day (observed)
+  unverified: 'UNVERIFIED: usual pattern (2021 precedent); owner confirms against sifma.org/resources/guides-playbooks/holiday-schedule'
--- a/core/calendars/data/kr_sessions.yaml
+++ b/core/calendars/data/kr_sessions.yaml
@@ -178,6 +178,14 @@
   kind: csat_day
   date: '2026-11-19'
   unverified: 'UNVERIFIED: date from memory of the KRX CSAT-day notices; owner confirms'
+- effective_from: '2027-11-18'
+  effective_to: '2027-11-18'
+  source_url: null
+  retrieved_at_utc: '2026-10-27T00:00:00Z'
+  signed_off_by: null
+  kind: csat_day
+  date: '2027-11-18'
+  unverified: 'UNVERIFIED: 2028학년도 수능, announced by the Ministry of Education on 2025-06-01; the KRX CSAT-day notice confirms the session window'
 - effective_from: '1995-01-01'
   effective_to: '1998-12-06'
   source_url: null
```

- source_skipped(CAL-09) 수정은 SIFMA 2027 확인 뒤에 정한다. 그래서 diff에 넣지 않았다. 형태는 다음과 같다.
  - 기존 `series: DGS10` Good Friday 행을 `series: H.15`로 바꾼다.
  - `2027-03-26` 행을 추가한다.

### 7.2 테스트 (`proposed_tests.diff`, `tests/macro_m1_calendars.py`)

```diff
--- a/tests/macro_m1_calendars.py
+++ b/tests/macro_m1_calendars.py
@@ -127,7 +127,8 @@
 
 def _doc(file_id, covers, calendar, rows, version="1.0.0-fixture") -> dict:
     return {"file_id": file_id, "version": version, "covers": {"from": covers[0], "to": covers[1]},
-            "coverage_calendar": calendar, "signed_off_by": SIGNER, "signed_utc": SIGNED_UTC, "md5": None, "rows": rows}
+            "coverage_calendar": calendar, "signed_off_by": SIGNER, "signed_utc": SIGNED_UTC, "md5": None, "rows": rows,
+            "sign_off_statement": "fixture: not an owner statement"}
 
 
 def _sign(doc: dict) -> dict:
@@ -141,7 +142,8 @@
         _sign(doc)
         (root / f"{name}.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
         rows.append({"file": f"{name}.yaml", "version": doc["version"], "md5": doc["md5"],
-                     "signed_off_by": None if unsigned_manifest else doc["signed_off_by"], "test_ids": ["T-CAL-01"]})
+                     "signed_off_by": None if unsigned_manifest else doc["signed_off_by"], "signed_utc": doc["signed_utc"],
+                     "test_ids": ["T-CAL-01"]})
     manifest = {"version": manifest_version, "signed_off_by": SIGNER, "signed_utc": SIGNED_UTC, "rows": rows}
     (root / "MANIFEST.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
 
@@ -354,15 +356,29 @@
 test_close02_effective_dated_clocks.test_ids = ["T-CLOSE-02"]
 
 
-def test_close02_on_the_real_signed_files_is_owner_input():
-    """The same assertions on the shipped files need the owner's signature; the drafts are unsigned."""
-    refused = store.describe()
-    assert refused and all(r["status"] == "REFUSED" for r in refused)
-    raise NotRun("OWNER: core/calendars/data/*.yaml are unsigned drafts; T-CLOSE-02 on the real KRX/NYSE files waits for "
-                 "the owner's sign-off (Saturday closes, pre-2016 CSAT window, CSAT dates, random-end extensions)")
+def test_close02_on_the_real_signed_files():
+    """Replaces the unconditional NotRun: the T-CLOSE-02 values on the signed KRX/NYSE files."""
+    live = CalendarSet()
+    if any(live.refusal(f) for f in ("kr_sessions", "holidays_KRX", "holidays_NYSE")):
+        raise NotRun("OWNER: kr_sessions / holidays_KRX / holidays_NYSE unsigned; T-CLOSE-02 on the real files waits")
+    U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
+    assert clocks.decision_time_utc("KR", date(2026, 10, 2), cal=live) == U(2026, 10, 2, 6, 30)
+    assert clocks.close_print_bound_utc("KR", date(2026, 10, 2), cal=live) == U(2026, 10, 2, 6, 30, 30)
+    assert clocks.decision_time_utc("KR", date(2026, 11, 19), cal=live) == U(2026, 11, 19, 7, 30)     # CSAT
+    assert clocks.decision_time_utc("KR", date(2027, 11, 18), cal=live) == U(2027, 11, 18, 7, 30)     # CSAT 2027
+    for d in (date(2026, 10, 5), date(2026, 6, 3), date(2026, 7, 17), date(2027, 5, 3), date(2027, 7, 19)):
+        try:
+            clocks.decision_time_utc("KR", d, cal=live)
+            raise AssertionError(f"KR {d} answered as a session")
+        except NotASession:
+            pass
+    assert clocks.decision_time_utc("US", date(2026, 11, 27), cal=live) == U(2026, 11, 27, 18, 0)
+    assert clocks.close_print_bound_utc("US", date(2026, 10, 1), cal=live) == U(2026, 10, 1, 20, 0, 30)
+    if live.refusal("holidays_SIFMA") is None:
+        assert publication.sifma_status(date(2026, 4, 3), cal=live) == "early_close"
 
 
-test_close02_on_the_real_signed_files_is_owner_input.test_ids = ["T-CLOSE-02"]
+test_close02_on_the_real_signed_files.test_ids = ["T-CLOSE-02"]
 
 
 def test_print01_intraday_print_is_never_a_close():
@@ -518,36 +534,47 @@
     return _CACHE[key][1]
 
 
-def test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed():
-    """The shipped drafts carry signed_off_by: null -> refused; every KR and US clock raises CalendarUnsigned, which the
-    data layer maps to MissingInput('missing') with fail_closed (brief F-5); no book can ARM."""
-    live = store.default()
-    assert live.data_dir == store.DATA_DIR
-    for fid in live.file_ids():
-        assert live.refusal(fid), fid
-        raw = store.read_yaml(live.data_dir / f"{fid}.yaml")
-        assert raw.get("signed_off_by") is None and raw.get("md5") is None, fid       # never signed by the build
-        assert raw.get("unverified") and raw.get("owner_must_sign"), fid
-    for market in ("KR", "US", "JP", "CN", "HK", "TW"):
-        _raises(lambda: clocks.decision_time_utc(market, date(2026, 10, 2), cal=live), CalendarUnsigned)
-        _raises(lambda: clocks.is_session(market, date(2026, 10, 2), cal=live), CalendarUnsigned)
-        assert store.arm_precondition(date(2026, 10, 2), market, cal=live) is False
-    _raises(lambda: regime.regime_tags("KR", date(2026, 10, 2), cal=live), CalendarUnsigned)
-    _raises(lambda: publication.publication_instant({"schedule_id": "H15"}, date(2026, 10, 2), cal=live), CalendarUnsigned)
-    assert store.status("KR", date(2026, 10, 2), cal=live)["signed"] is False
-    assert live.version == "unsigned"
+def test_cal01_shipped_files_signed_or_refused():
+    """Replaces test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed: a draft (signed_off_by null) is
+    refused and still lists its open items; a signed file loads, matches its MANIFEST row, and carries no draft status."""
+    live = CalendarSet()                               # fresh: never the cached default
     manifest = store.read_yaml(store.DATA_DIR / "MANIFEST.yaml")
-    assert all(r["md5"] is None and r["signed_off_by"] is None for r in manifest["rows"])
     assert {r["file"] for r in manifest["rows"]} == {f"{f}.yaml" for f in live.file_ids()}
+    drafts = []
+    for fid in live.file_ids():
+        raw = _raw(fid)
+        if raw.get("signed_off_by") is None:
+            drafts.append(fid)
+            assert live.refusal(fid), fid
+            assert raw.get("md5") is None and raw.get("unverified") and raw.get("owner_must_sign"), fid
+        else:
+            assert live.refusal(fid) is None, (fid, live.refusal(fid))
+            f = live.file(fid)
+            row = live.manifest["rows"][f"{fid}.yaml"]
+            assert row["md5"] == f.md5 and row["signed_off_by"] == f.signed_off_by and row["version"] == f.version
+            assert "UNSIGNED" not in str(raw.get("status", "")), f"{fid}: signed file still says UNSIGNED DRAFT"
+            assert "FIXTURE" not in f.signed_off_by.upper(), f"{fid}: fixture signer in a shipped file"
+    for market, fids in store.MARKET_FILES.items():
+        if any(f in drafts for f in fids):            # an unsigned file of the market: every clock fails closed
+            try:
+                clocks.decision_time_utc(market, date(2026, 10, 2), cal=live)
+                raise AssertionError(f"{market}: clock answered with an unsigned file")
+            except store.CalendarUnsigned:
+                pass
+            assert store.arm_precondition(date(2026, 10, 2), market, cal=live) is False
+    if any(f in drafts for f in store.COVERAGE_FILES["KR"]):
+        assert store.status("KR", date(2026, 10, 2), cal=live)["signed"] is False
+    if not manifest.get("signed_off_by"):
+        assert live.version == "unsigned"
     # the rules-store paths of section 7 resolve to these files
     from core.rules.macro_rules import load_store
     s = load_store()
     assert s.get("calendars.regime_tags_file") == "core/calendars/data/kr_regime_tags.yaml"
     assert s.get("data_contracts.source_exceptions") == "core/calendars/data/source_skipped.yaml"
-    assert (store.DATA_DIR.parents[2] / s.get("calendars.regime_tags_file")).is_file()
+    assert (Path(store.__file__).resolve().parents[2] / s.get("calendars.regime_tags_file")).is_file()
 
 
-test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed.test_ids = ["T-CAL-01"]
+test_cal01_shipped_files_signed_or_refused.test_ids = ["T-CAL-01"]
 
 
 def test_cal01_calendar_change_governance_event():
@@ -576,6 +603,31 @@
 test_cal01_calendar_change_governance_event.test_ids = ["T-CAL-01"]
 
 
+def test_cal01_same_day_schedule_needs_its_signed_calendar():
+    """A same_day schedule (VIX 16:15 ET, ECOS 15:30 KST) reads its publisher's calendar: unsigned or absent -> refused."""
+    docs = {k: v for k, v in fixture_docs().items() if k != "holidays_CBOE"}
+    cal = fixture_set("no_cboe", docs)
+    exc = _raises(lambda: publication.publication_instant({"schedule_id": "VIXCLS_CBOE"}, date(2026, 10, 2), cal=cal),
+                  CalendarUnsigned)
+    assert "holidays_CBOE" in str(exc)
+
+
+test_cal01_same_day_schedule_needs_its_signed_calendar.test_ids = ["T-CAL-01"]
+
+
+def test_cal01_unquoted_time_refused_at_load():
+    """`close_local: 12:00` (PyYAML 1.1: the int 720) is refused at load, never at first use."""
+    docs = {k: v for k, v in fixture_docs().items() if k in ("holidays_HKEX", "market_closes")}
+    docs["holidays_HKEX"]["rows"].append(_hol(date(2026, 12, 24), "early_close", "12:00"))
+    cal = fixture_set("unquoted_time", docs)
+    p = cal.data_dir / "holidays_HKEX.yaml"
+    p.write_text(p.read_text(encoding="utf-8").replace("close_local: '12:00'", "close_local: 12:00"), encoding="utf-8")
+    assert "unquoted time" in str(_raises(lambda: CalendarSet(cal.data_dir).file("holidays_HKEX"), CalendarUnsigned))
+
+
+test_cal01_unquoted_time_refused_at_load.test_ids = ["T-CAL-01"]
+
+
 def test_cal02_coverage_warn_page_halt():
     """A file ending N sessions after the decision date: N=61 no alert, 60 warn, 20 page, 0 page; outside -> OPS HALT
     calendar_coverage through the injected runtime hook, never a NotASession."""
@@ -618,14 +670,56 @@
 test_cal02_coverage_warn_page_halt.test_ids = ["T-CAL-02"]
 
 
+DEADLINE_FILES = ("holidays_KRX", "holidays_NYSE", "holidays_FED", "holidays_SIFMA")
+DEADLINE_UTC = "2026-10-31T15:00:00Z"            # 2026-11-01 00:00 KST: "signed off before 2026-11-01" (spec L2101)
+# Closures the 4.13.2 cross-check misses or the draft got wrong (audit 2026-10-27). Raw YAML: runs signed or not.
+MUST_CLOSE = {"holidays_KRX": ("2026-06-03", "2026-07-17", "2027-05-03", "2027-07-19"),
+              "holidays_FED": ("2027-12-31",)}
+MUST_EARLY = {"holidays_SIFMA": {"2026-04-03": "12:00", "2026-07-02": "14:00"}}
+MUST_CSAT = ("2026-11-19", "2027-11-18")
+
+
+def _raw(fid):
+    return store.read_yaml(store.DATA_DIR / f"{fid}.yaml")
+
+
 def test_cal02_2027_files_signed_before_2026_11_01():
-    raise NotRun("OWNER: the 2027 KRX, NYSE, Fed and SIFMA files must be signed before 2026-11-01 (spec L2101); "
-                 "core/calendars/data/holidays_{KRX,NYSE,FED,SIFMA}.yaml are unsigned drafts")
+    """Deadline clause on the real files (spec L2101): signed before 2026-11-01 KST, covering 2027-12-31, >= 60
+    sessions after 2026-11-01, and the KR/US markets ARM-able on that date."""
+    live = CalendarSet()
+    unsigned = [f for f in DEADLINE_FILES + ("kr_sessions",) if live.refusal(f)]
+    if unsigned:
+        raise NotRun(f"OWNER: {unsigned} unsigned; the 2027 KRX, NYSE, Fed and SIFMA files must be signed before "
+                     "2026-11-01 (spec L2101)")
+    for fid in DEADLINE_FILES:
+        f = live.file(fid)
+        assert f.signed_utc < DEADLINE_UTC, f"{fid}: signed {f.signed_utc}, deadline {DEADLINE_UTC}"
+        assert f.covers_to >= date(2027, 12, 31), f"{fid}: covers only to {f.covers_to}"
+        assert store.sessions_left(live, f, date(2026, 11, 1)) >= 60, fid
+    for market in ("KR", "US"):
+        assert store.arm_precondition(date(2026, 11, 2), market, cal=live), market
 
 
 test_cal02_2027_files_signed_before_2026_11_01.test_ids = ["T-CAL-02"]
 
 
+def test_cal02_known_2026_2027_rows_present():
+    """Regression for the audit findings: every listed closure, early close and CSAT day is in the shipped file."""
+    for fid, dates in MUST_CLOSE.items():
+        closed = {r["date"] for r in _raw(fid)["rows"] if r.get("kind") == "closed"}
+        missing = [d for d in dates if d not in closed]
+        assert not missing, f"{fid}: closures missing {missing}"
+    for fid, want in MUST_EARLY.items():
+        rows = {r["date"]: r for r in _raw(fid)["rows"]}
+        for d, t in want.items():
+            assert d in rows and rows[d].get("kind") == "early_close" and rows[d].get("close_local") == t, (fid, d, rows.get(d))
+    csat = {r["date"] for r in _raw("kr_sessions")["rows"] if r.get("kind") == "csat_day"}
+    assert set(MUST_CSAT) <= csat, f"kr_sessions: CSAT days missing {sorted(set(MUST_CSAT) - csat)}"
+
+
+test_cal02_known_2026_2027_rows_present.test_ids = ["T-CAL-02"]
+
+
 # --------------------------------------------------------------------------- #
```

- 픽스처 두 줄(첫 두 hunk)은 7.3의 store 변경과 짝이다. 7.3을 적용하지 않으면 빼도 된다.
- 테스트 이름 두 개가 바뀐다. qa 기록과의 연속성이 필요하면 옛 이름을 유지해도 된다.

### 7.3 코드 (`proposed_code.diff`; store.py는 CRLF)

```diff
--- a/core/calendars/publication.py
+++ b/core/calendars/publication.py
@@ -154,6 +154,7 @@
             monday += timedelta(days=1)
         instant = _instant(monday, t, tz)
     elif rule == "same_day":
+        business_day(s["calendar"], obs_date, cal=cal)       # the publisher's calendar must be signed and cover D (T-CAL-01)
         instant = _instant(obs_date, t, tz)
     elif rule == "channel_posting_time":
         if s.get("posting_utc"):
--- a/core/calendars/store.py
+++ b/core/calendars/store.py
@@ -116,11 +116,28 @@
     return md5_hex(canonical_json(body))
 
 
+TIME_KEYS = ("close_local", "open_local", "close_kst", "open_kst", "time", "declared_time", "window_kst")
+
+
+def _reject_unquoted_times(value, where: str) -> None:
+    """PyYAML 1.1 reads an unquoted 12:00 as the sexagesimal int 720: refuse it at load, not at use."""
+    if isinstance(value, dict):
+        for k, v in value.items():
+            if k in TIME_KEYS and v is not None and not (isinstance(v, str) or
+                                                         (isinstance(v, list) and all(isinstance(x, str) for x in v))):
+                raise CalendarUnsigned(f"{where}.{k}: unquoted time {v!r}; quote every HH:MM string")
+            _reject_unquoted_times(v, f"{where}.{k}")
+    elif isinstance(value, list):
+        for i, v in enumerate(value):
+            _reject_unquoted_times(v, f"{where}[{i}]")
+
+
 def read_yaml(path: Path) -> dict:
     doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
     if not isinstance(doc, dict):
         raise CalendarUnsigned(f"{path.name}: not a mapping")
     _reject_native_dates(doc, path.name)
+    _reject_unquoted_times(doc, path.name)
     return doc
 
 
@@ -149,6 +166,11 @@
                                f"{manifest_row.get('md5')!r}) does not match the file ({doc['version']!r}, {digest})")
     if not _signed(manifest_row.get("signed_off_by")) or manifest_row["signed_off_by"] != doc["signed_off_by"]:
         raise CalendarUnsigned(f"{name}: {MANIFEST} signer does not match the file signer")
+    if manifest_row.get("signed_utc") != doc["signed_utc"]:
+        raise CalendarUnsigned(f"{name}: {MANIFEST} signed_utc {manifest_row.get('signed_utc')!r} != file "
+                               f"{doc['signed_utc']!r} (signed_utc sits outside the md5; the manifest pins it)")
+    if not _signed(doc.get("sign_off_statement")):
+        raise CalendarUnsigned(f"{name}: sign_off_statement is empty (the sentence the owner signs is part of the md5)")
     tests = manifest_row.get("test_ids")
     if not isinstance(tests, list) or not tests or not all(_signed(t) for t in tests):
         raise CalendarUnsigned(f"{name}: {MANIFEST} row names no test id (test_per_change: required)")
```

- CAL-07 연결(macro_daily.app_start)은 alert code 등록 방식을 정해야 한다. 그래서 diff 대신 5절에 스케치만 적었다.

### 7.4 레거시 JSON (`proposed_legacy_json.diff`; 두 파일 모두 CRLF, 아래는 LF로 표시)

```diff
--- a/data/calendars/KRX.json
+++ b/data/calendars/KRX.json
@@ -26,6 +26,8 @@
   "2026-05-01",
   "2026-05-05",
   "2026-05-25",
+  "2026-06-03",
+  "2026-07-17",
   "2026-08-17",
   "2026-09-24",
   "2026-09-25",
@@ -37,8 +39,10 @@
   "2027-02-08",
   "2027-02-09",
   "2027-03-01",
+  "2027-05-03",
   "2027-05-05",
   "2027-05-13",
+  "2027-07-19",
   "2027-08-16",
   "2027-09-14",
   "2027-09-15",
@@ -53,9 +57,17 @@
    "open": "10:00",
    "close": "15:30"
   },
+  "2026-11-19": {
+   "open": "10:00",
+   "close": "16:30"
+  },
   "2027-01-04": {
    "open": "10:00",
    "close": "15:30"
+  },
+  "2027-11-18": {
+   "open": "10:00",
+   "close": "16:30"
   }
  }
 }
--- a/data/calendars/index.json
+++ b/data/calendars/index.json
@@ -11,8 +11,8 @@
     "from": "2026-01-01",
     "to": "2027-12-31"
    },
-   "holidays": 29,
-   "special_sessions": 2
+   "holidays": 33,
+   "special_sessions": 4
   },
   "US": {
    "calendar": "XNYS",
```

- `source.library`는 exchange_calendars로 남는다. test 74가 이 값을 요구한다. 손으로 보정한 사실은 커밋 메시지에 남긴다.

## 8. 미검증 항목

1. KRX 공지 원문은 차단으로 직접 읽지 못했다. 2026-06-03과 2026-07-17은 언론 보도 4건과 캐시 공백으로 확인했다.
2. KRX 2027 휴장일 공지는 아직 없다. KRX 업무규정 원문도 확인하지 못했다.
3. SIFMA 일정표 원문은 차단됐다. 2026-04-03과 2026-07-02 외의 조기폐장, 그리고 2027-03-26 전일 휴장은 추정이다.
4. Fed Board의 2027-12-31 휴무, 그리고 Board 휴무 금요일의 H.15 관측 존재 여부(예: 2021-12-31 DGS10)는 확인하지 못했다.
5. NYSE는 ICE 요약과 XNYS로만 확인했다.
6. HKEX, JPX, TWSE, SSE 공식 페이지는 차단됐다. TWSE 2027과 SSE 2027은 미확정이다.
7. CBOE 조기폐장 종가 시각과 CME 대상 상품은 확인하지 못했다.
8. 2026-07-06 24시간 외환시장 이후 ECOS의 공휴일 게시 여부는 확인하지 못했다.
9. 2026-04-03 DGS10 값은 확인하지 못했다. 캐시에는 DGS3MO만 있다.
10. yfinance ^VIX의 미국 휴일 행(2026-05-25, 2026-09-07)은 공급사 산출물로 보이지만 확인하지 못했다.
11. kr_regime_tags 2026 행 대부분과 market_closes 시각은 대조하지 않았다.
12. KIS `chk-holiday` 실호출은 하지 않았다.
13. 차단 호스트: data.krx.co.kr, global.krx.co.kr, www.krx.co.kr, www.kasa.go.kr, www.nyse.com, ir.theice.com, www.sifma.org, www.federalreserve.gov, www.hkex.com.hk, www.jpx.co.jp, www.twse.com.tw, www.sse.com.cn, www.cmegroup.com, www.cboe.com, www.bok.or.kr, www.kofiabond.or.kr, en.wikipedia.org, www.mt.co.kr, www.hankyung.com, news.mtn.co.kr, news.bizwatch.co.kr. WebFetch는 DNS 오류로 실패했다.

## 9. 재현 스크립트와 산출물 경로

`<W>` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/calendars`. 모든 스크립트는 `cd /home/user/quantgen && python3 -B <W>/<script>`로 실행한다. 저장소에는 쓰지 않는다.

- 교차검증: `<W>/cal_xcheck.py` → `<W>/cal_xcheck_result.json`, `<W>/cal_xcheck_stdout.txt`
- 캐시 경험 대조: `<W>/cache_sessions.py` → `<W>/cache_sessions_result.json`
- 서명 리허설과 재현: `<W>/sign_dryrun.py`(+ `<W>/sign_dryrun_lib.py`) → `<W>/sign_dryrun_result.json`
- CAL-13: `<W>/repro_unquoted_time.py`
- CAL-09: `<W>/repro_source_skipped.py`
- diff 생성기: `<W>/make_diffs.py`, `<W>/make_test_diff.py`, `<W>/make_legacy_json_diff.py`
- diff 파일: `<W>/proposed_yaml.diff`, `<W>/proposed_tests.diff`, `<W>/proposed_code.diff`, `<W>/proposed_legacy_json.diff`
- 테스트 검증
  - `<W>/verify_proposed_tests.py` → `<W>/verify_proposed_tests_result.json`
  - `<W>/run_cal_module.py`(스크래치 트리 `<W>/codetree`에서 실행)
  - `<W>/verify_patched_tree_signed.py`
- 차단 호스트 목록: `<W>/web/blocked_hosts.txt`

## 10. 웹 출처 (WebSearch 요약으로만 확인; 직접 열람은 차단)

- KRX 2026-05-20 휴장 공지 보도
  - https://www.mt.co.kr/stock/2026/05/20/2026052010314634386
  - https://www.hankyung.com/article/2026052094456
  - https://imnews.imbc.com/news/2026/econo/article/6823907_36932.html
  - https://www.ajunews.com/view/20260520145232772
- 제헌절 공휴일법 본회의 통과(2026-01-29): https://news.mtn.co.kr/news-detail/2026012916083741222
- 2027 월력요항(우주항공청)
  - https://www.kasa.go.kr/prog/plcyBrf/brief/kor/sub01_01_04/view.do?plcyBrfNo=431
  - https://www.cbci.co.kr/news/articleView.html?idxno=619741
- 2028학년도 수능 2027-11-18: https://www.dhnews.co.kr/news/view/1065578177989020
- 2026-09-28 임시공휴일 불발: https://www.wikitree.co.kr/articles/1161815
- 외환시장 24시간(2026-07-06): https://www.kukinews.com/article/view/kuk202607060061
- SIFMA
  - https://www.sifma.org/news/press-releases/sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-good-friday-easter-monday-holidays-2026
  - https://www.newyorkfed.org/markets/opolicy/operating_policy_260312
  - https://mondovisione.com/media-and-resources/news/sifma-fixed-income-market-close-recommendations-in-the-us-the-uk-and-japan-2026618/
  - https://www.sifma.org/resources/guides-playbooks/holiday-schedule
  - https://www.marketbeat.com/bond-market-holidays/
- NYSE: https://ir.theice.com/press/news-details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx
- Fed
  - https://www.chicagofed.org/utilities/about-us/bank-holidays
  - https://www.frbservices.org/about/holiday-schedules
- 홍콩 2027: https://www.gov.hk/en/about/abouthk/holiday/2027.htm
- 일본 2027
  - https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html
  - https://www.nippon.com/ja/japan-data/h02794/
- 대만 116년
  - https://www.ettoday.net/news/20260521/3169805.htm
  - https://wantrich.chinatimes.com/news/20260521900621-420101
- KIS chk-holiday(3자): https://algolab.co.kr/blog/krx-market-holiday-check-bot-scheduling-2026

<!-- verifier-section -->

## 독립 검증 결과

- 검증자: 적대적 재검증(dimension: calendars). 저장소 파일은 수정하지 않았다. 기존 `git status`의 docs/audit 변경은 이번 검증 전부터 있던 것이다.
- 작업 폴더 `W` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_calendars`
- 조사자 스크립트를 쓰지 않고 서명 리허설을 다시 짰다(`W/vsign.py`, `W/v_core.py` → `W/v_core_out.json`).
  - 데이터 폴더를 스크래치에 복사했다. 행 수정 없이 가짜 서명자로 서명하고 `CalendarSet(copy)`로 적재했다.
- 테스트 비교:
  - 저장소 사본 4개를 만들었다: 초안, 서명본, 패치 적용 초안, 패치 적용 서명본(`W/t_unsigned`, `W/t_signed`, `W/tree`, `W/t_patched_signed`).
  - 캘린더에 의존하는 14개 macro 모듈과 engine_acceptance를 돌렸다(`W/run_mods.sh` → `W/res_*.txt`). `run_all.py`는 쓰지 않았다.
  - 사본에는 docs/를 복사하지 않았다. 그래서 금지 파일 4개는 열리지 않았다. 사본 환경 때문에 생긴 FAIL 10건은 네 사본 모두 같다. 비교는 차이만 본다.
- 웹 확인(WebSearch 요약만 봄):
  - KRX 2026-05-20 휴장 공지 보도(bizwatch).
  - 2026-04-28 국무회의의 '관공서의 공휴일에 관한 규정' 개정(노동절·제헌절 공휴일, 대체공휴일 적용, mt.co.kr·newsis).
  - 2027 월력요항(segye, kbthink).
  - SIFMA 2026-03-20과 2026-06-18 보도자료.
  - 교육부 2028학년도 수능 2027-11-18(dhnews).

| id | 유지 여부 | 정정 판정 | 정정 심각도 | 근거 |
|---|---|---|---|---|
| CAL-01 | 유지 | 사실 | P1 | 서명본에서 `is_session('KR', 2026-06-03/07-17)`가 True이고 결정 시각은 06:30Z다. XKRX 4.13.2도 두 날을 세션으로 본다. 캐시 3종(069500, 005930, 102110)에서 YAML이 개장으로 보는 평일 가운데 행이 없는 날은 이 두 날뿐이다(`W/cache_gaps.py`). 추가 근거: `gap_sessions('KR', 2026-06-04)`가 1이다. 교정하면 2다(`W/v_gap.py`). 그래서 macro_state flags(`kr_open_gap_event`, `var_display_scale`)가 틀린다. 영향 정정: `completeness_check`는 운영 코드에서 부르는 곳이 없다. |
| CAL-02 | 유지 | 추정 | P1 | 재현됨(2027-05-03, 2027-07-19가 세션). 공휴일 지정과 대체공휴일 적용은 규정 개정 보도와 월력요항으로 확인했다. KRX 2027 공지가 없으므로 '추정'이 맞다. 2027-05-04와 2027-07-20의 `gap_sessions`가 1이다. 2가 맞다. |
| CAL-03 | 유지 | 사실 | P2 | 서명본에서 2027-11-18 결정 시각은 06:30Z, bound는 06:30:30Z, 개장은 09:00이다. 2026-11-19는 07:30Z와 10:00으로 맞다. 수능일 2027-11-18은 교육부 발표로 확인했다. 대개는 CloseAfterBound로 fail-closed가 되므로 P2가 적절하다. |
| CAL-04 | 유지 | 사실 | P3 (P2에서 낮춤) | 데이터 오류는 사실이다. SIFMA 2026-03-20 보도자료에 12:00 조기폐장이 있다. DGS3MO 2026-04-03 값은 3.71이다. 07-02 14:00은 2026-06-18 보도자료에 있다. 그러나 `sifma_status`는 테스트 밖에서 부르는 곳이 없다(grep). SIFMA 집합의 운영 소비자는 UST_PAR_10Y의 obs_calendar와 TREASURY_PAR의 grace 계산뿐이다. 잘못 들어간 'closed'는 stale 판정을 하루 느슨하게 할 뿐 틀린 숫자를 만들지 않는다. 조기폐장 행은 운영 소비자가 없다. 참고: SIFMA는 04-03을 결제일로 보지 말라고 권고했다. 행 이름에 이 점을 적는 것이 좋다. |
| CAL-05 | 유지 | 사실(파일 내부 불일치) | P3 | `holidays_FED.yaml:665`에 2021-12-31이 있다. 마지막 행은 :1250의 2027-12-24다. 파일 머리말(:16)은 토→금 규칙을 선언한다. `business_day('FED', 2027-12-31)`이 True다. Board 휴무 자체는 미검증이다. |
| CAL-06 | 유지 | 사실 | P2 | 7개 파일은 covers가 null이고 행이 0개다. 서명본에서도 REFUSED다. JP/CN/HK/TW는 ARM할 수 없다. 영향 정정 세 가지. (1) 시리즈 id는 NIKKEI225_CLOSE, HSI_CLOSE, TAIEX_CLOSE, SHANGHAI_CLOSE다. (2) 이 바인딩들은 context, risk_model, forward_sim이다. acting_exposure가 아니다. context 읽기는 미서명 캘린더에서도 라벨이 붙은 값으로 나온다(tests/macro_m1_integration.py:164-167). 그래서 '계속 fail-closed'는 과장이다. (3) KR·US ARM에는 영향이 없다(서명본에서 arm KR/US True). 4.5절 참조 목록은 exchange_calendars 4.13.2(XHKG, XTKS, XTAI, XSHG)와 일치한다. 교차검증일 뿐 원천이 아니다. |
| CAL-07 | 유지 | 사실 | P2 | `check_coverage`, `record_calendar_changes`, `coverage_halt`는 테스트에서만 부른다. 운영 호출은 `macro_daily.py:1095`의 `arm_precondition`뿐이다. 다만 M-1에 따르면 60세션 경보를 연결해도 엔진이 그보다 먼저(약 86세션 남았을 때) 깨진다. |
| CAL-08 | 유지(불완전) | 사실 | P2 | 재현했다: shipped_drafts는 `AssertionError: holidays_FED`, close02는 AssertionError, 마감 테스트는 NotRun이다. 패치 사본 결과(19/5, 서명 시 21/3)도 재현했다. 그러나 서명하면 다른 모듈의 테스트 2개도 FAIL이 된다. 제안 diff 4개를 모두 적용해도 마찬가지다(M-2). 제안된 마감 테스트는 signed_utc를 문자열로 비교한다(M-4). |
| CAL-09 | 유지(영향 주장 오류) | 사실(코드) / 영향 오류 | P3 (P2에서 낮춤) | 코드 사실은 재현했다. DGS2·DTB3의 2025-04-17 다음 기대 관측은 04-18이다. 그러나 H.15 9개 시리즈는 모두 `grace_publication_bdays=1`이다. DGS2(last_obs 2025-04-17)의 deadline은 2025-04-22 20:15Z다. 실제 04-21 관측도 같은 시각에 게시된다. 그래서 KR 결정 04-22 06:30:30Z와 04-23은 모두 Fresh다(`W/v_cal09.py`). 'stale 1회'는 재현되지 않는다. `series: H.15` 수정은 정합성 차원에서 맞다. DGS3MO 캐시의 Good Friday 공백(2016–2020, 2022, 2024, 2025)이 이를 뒷받침한다. |
| CAL-10 | 유지 | 사실 | P2 | `is_trading_day('KRX', 2026-06-03)`=True, `special_session(2026-11-19)`=None을 재현했다. 레거시 데이터는 evaluator(`core/engine/evaluator.py:176-178`), runtime(:195, :217), `core/quant/history.py:381`에 쓰인다. 정정 1: `stale_markets()`는 2026-10-27에 빈 목록을 낸다. 2026-11-01부터 NSE/SGX/SSE/SZSE가 나온다. 정정 2: DryRunClocks(`macro_daily.py:1316-1323`)는 06:30:30Z와 16:00 ET를 하드코딩한다. 그래서 JSON 수정이 DryRunClocks의 수능일이나 미국 반일장에는 반영되지 않는다. diff 적용 사본에서 engine_acceptance 68–75는 PASS다. |
| CAL-11 | 유지 | 사실 | P2 | `KR 2025-11-13`, `US 2024-12-31`에서 CalendarCoverageError가 난다. 초안의 `owner_must_sign`(1995..2027)에도 못 미친다. |
| CAL-12 | 유지 | 사실 | P3 | ECOS/CBOE가 REFUSED인 서명본에서 ECOS_USDKRW는 06:30Z, VIXCLS_CBOE는 20:15Z를 낸다. 새 테스트는 현재 코드에서 FAIL, 패치 후 PASS였다(`W/stageB.txt`). |
| CAL-13 | 유지(수정안 불완전) | 사실 | P3 | PyYAML은 `12:00`을 720, `16:15`를 975로 읽고 `09:30`은 문자열로 둔다. 패치는 `close_local: 12:00`을 거부한다. 그러나 TIME_KEYS가 키 이름 기반이다. 그래서 kr_regime_tags의 `value`(close_time_kst '15:00'/'15:30', `kr_regime_tags.yaml:100,108`)에 따옴표 없는 `15:30`을 쓰면 패치 후에도 930으로 적재된다(`W/m5tmp`). 시간 리졸버를 뺀 SafeLoader를 쓰는 편이 낫다. |
| CAL-14 | 유지 | 사실 | P3 | `SIGNATURE_FIELDS`(store.py:37)가 signed_utc를 md5에서 뺀다. `parse_file`(131-180)은 MANIFEST의 signed_utc와 비교하지 않는다. 형식도 검사하지 않는다(M-4). |

- 서명 절차(6절)에 대한 주의:
  - 6.1은 kr_regime_tags 서명을 권고한다. 그런데 보고서 스스로 이 파일 값이 '대부분 미검증'이라고 적었다. 서명은 대조했다는 증언이다. 미검증 행을 서명하라는 권고는 모순이다.
  - 6.6의 "2028 파일은 2027-09까지"는 늦다. M-1에 따라 늦어도 2027-08-23까지 서명해야 한다. 아니면 코드를 고쳐야 한다.
- 소유자 메모 "(-> 공급사필요)"와의 관계: 이 dimension에서 유료 공급사가 필요 없다는 판단에 동의한다. KIS `chk-holiday`는 실호출하지 않았다(미검증).

### 누락 발견사항

#### M-1 엔진의 세션 창(앞 130일)이 커버리지 경보(60세션)보다 먼저 깨져 hard stop HALT가 실패
- **심각도** P1
- **판정** 사실(risk_step 예외와 ARMED 유지는 재현). 이후 OPS 진동은 추정이다.
- **위치**
  - `core/skills/macro_daily.py:147-156` `sessions_around`: back=100, ahead=130이다. 단위가 '일'이다. 모든 예외를 ValueError로 감싼다.
  - `:171` `BookRegistry(sessions=lambda m: sessions_around(clocks, m, anchor[0]))`.
  - `core/engine/books.py:251-260` `session_offset`.
  - `:393-395` `runtime_halt`의 RISK 분기.
  - `:612-613` `risk_step`의 hard_stop.
- **재현**
  - `cd /home/user/quantgen && python3 -B W/v_horizon.py`
    - 2027-08-23은 ok(157개)이고 sessions_left는 87이다.
    - 2027-08-24에는 `ValueError: KR: sessions unavailable ... 2028-01-01 is outside`가 난다. 이때 sessions_left는 86이다.
  - `python3 -B W/v_hardstop.py`
    - anchor 2027-06-01: NAV 85에서 HALTED RISK hard_stop.
    - anchor 2027-09-01: `risk_step RAISED ValueError`. 장부는 `mode ARMED halted False`로 남는다.
- **기대 결과** 10세션 이상 커버되어 있으면 −15% 하락에서 RISK hard_stop HALT가 기록된다. `rearm_not_before`는 t+10이다. 커버리지 경보는 엔진이 깨지기 전에 울린다.
- **실제 결과**
  - 2027-08-24부터(잔여 86세션, warn 60보다 많음) `session_offset`이 예외를 던진다.
  - hard stop HALT가 기록되지 않는다.
  - `vol_and_overlays`의 예외는 `acting_error`가 된다. 이어서 OPS STEP_ERROR HALT가 된다. 이 HALT는 자동 재ARM된다. RISK의 10세션 재ARM 거부와 재ARM 후 0.5 cap은 적용되지 않는다(추정).
- **영향**
  - 안전 규칙(hard stop)이 날짜 조건에 따라 약해진다. 경보 임계(60)와 ARM 조건(60)이 이 실패를 막지 못한다.
  - 조사자의 '2027-09까지 서명' 권고로는 늦다.
  - P0가 아닌 이유: 현재는 모든 장부가 DISARMED다. 2028 파일을 제때 서명하면 피할 수 있다.
- **수정안**(스크래치에서 검증: `W/v_hardstop_fix.py` → 2027-09-01 HALTED RISK, rearm_not_before 2027-09-21)
```diff
--- a/core/skills/macro_daily.py
+++ b/core/skills/macro_daily.py
@@ def sessions_around(clocks, market: str, anchor: date, back: int = 100, ahead: int = 130) -> list[date]:
     out = []
     for i in range(-back, ahead + 1):
         d = anchor + timedelta(days=i)
         try:
             if clocks.is_session(market, d):
                 out.append(d)
+        except CS.CalendarCoverageError:
+            if d > anchor:
+                break          # coverage ends inside the look-ahead: session_offset refuses only when n runs past it
+            continue           # before covers.from: the window starts at the coverage start
         except Exception as exc:                               # noqa: BLE001  (an unsigned calendar is a refusal, not a session)
             raise ValueError(f"{market}: sessions unavailable around {anchor} ({type(exc).__name__}: {exc})") from exc
     return out
```
- **회귀 테스트** `test_hard_stop_halts_near_calendar_horizon`
  - 픽스처 세트 KRX covers.to=2027-12-31, anchor 2027-09-01.
  - `risk_step(..., 85.0)` 후 다음을 확인한다: `book.halted`, `halt['class']=='RISK'`, `halt['reason_code']=='hard_stop'`, `rearm_not_before=='2027-09-21'`.
  - 현재 코드에서는 ValueError로 FAIL한다.

#### M-2 서명하면 다른 모듈 테스트 2개도 FAIL. 제안 테스트 diff로는 막지 못함
- **심각도** P2 · **판정** 사실
- **위치**
  - `tests/macro_m1_integration.py:155-176` `test_unsigned_shipped_calendars_fail_acting_inputs_closed`: `store.CalendarSet()`(배포 파일)이 미서명이라고 가정한다.
  - `tests/macro_m9_lab.py:515`, `:538-540` `test_t_crypto_01_clock_annualisation_and_no_crypto_sleeve`: 기본 세트의 KR 시계가 예외를 던진다고 가정한다.
- **재현**
  - `W/run_mods.sh`를 `W/t_unsigned`와 `W/t_signed`에서 돌렸다. PASS→FAIL은 4건이다. 조사자가 말한 2건과 위 2건이다.
  - diff 4개를 모두 적용한 사본(`W/res_patched_unsigned.txt` vs `W/res_patched_signed.txt`)에서도 위 2건은 PASS→FAIL이다.
- **기대 결과** 소유자 서명 커밋이 QA를 깨지 않는다.
- **실제 결과** 서명 즉시 FAIL 2건이 남는다.
- **영향** 서명 커밋이 QA를 깨뜨린다. 그대로 두면 '미서명' 가정을 지키려 서명을 미루거나 테스트를 끄게 된다.
- **수정안** 두 테스트가 배포 파일 대신 명시적 미서명 픽스처를 쓰게 한다.
```diff
--- a/tests/macro_m1_integration.py
+++ b/tests/macro_m1_integration.py
@@ def test_unsigned_shipped_calendars_fail_acting_inputs_closed():
-    unsigned = CalendarClocks(REG, cal=store.CalendarSet())              # the shipped drafts, refused at load
+    docs = fixture_docs()
+    for d in docs.values():
+        d["signed_off_by"] = None                                        # an unsigned set, whatever the shipped files are
+    unsigned_cal = fixture_set("integration_unsigned", docs)
+    unsigned = CalendarClocks(REG, cal=unsigned_cal)
@@
-    assert not store.arm_precondition(OCT2, "KR", cal=store.CalendarSet())    # no book can ARM
+    assert not store.arm_precondition(OCT2, "KR", cal=unsigned_cal)          # no book can ARM
--- a/tests/macro_m9_lab.py
+++ b/tests/macro_m9_lab.py
@@
-    _raises(lambda: K.decision_time_utc("KR", d), (CalendarUnsigned, CalendarCoverageError, NotASession))
+    from tests.macro_m1_calendars import fixture_docs, fixture_set
+    docs = fixture_docs(); docs["holidays_KRX"]["signed_off_by"] = None
+    _raises(lambda: K.decision_time_utc("KR", d, cal=fixture_set("m9_unsigned_krx", docs)),
+            (CalendarUnsigned, CalendarCoverageError, NotASession))
```
- **회귀 테스트** 서명 리허설 사본에서 캘린더 의존 모듈 전체를 돌려 PASS→FAIL이 0건인지 본다(`W/run_mods.sh` 비교). 각 테스트는 서명 전과 후 모두 PASS여야 한다.

#### M-3 레거시 NSE/SGX/SSE/SZSE 캘린더가 2026-12-31에 만료. 안내된 재생성 도구는 없음
- **심각도** P2 · **판정** 사실
- **위치**
  - `data/calendars/{NSE,SGX,SSE,SZSE}.json`(covers.to 2026-12-31).
  - `tests/engine_acceptance.py:936-941` `test_73`: `stale_markets()`가 `datetime.now()`를 쓴다.
  - `ui/trading_page.py:373-386`: 문구 "Regenerate with pkg_tools/generate_calendars.py". `core/engine/runtime.py:173`이 이 데이터를 공급한다.
  - `core/calendars/__init__.py:4`.
  - `pkg_tools/`는 저장소에 없다.
- **재현**
  - `python3 -B -c "from core import calendars as L; from datetime import date; print([r['market'] for r in L.stale_markets(date(2027,1,1)) if r['expired']])"` → `['NSE','SGX','SSE','SZSE']`. 이 값이면 test_73 단언이 실패한다.
  - `stale_markets(date(2026,11,1))`에서도 같은 4개가 stale로 나온다.
  - `ls pkg_tools`는 없음이다.
  - exchange_calendars 4.13.2 XSHG도 2026까지만 있다. 재생성해도 SSE/SZSE 2027은 만들 수 없다.
- **기대 결과** 만료 전에 실행 가능한 갱신 경로가 있다. UI 안내는 실제 도구를 가리킨다.
- **실제 결과**
  - 2026-11-01부터 UI가 없는 스크립트를 실행하라고 안내한다.
  - 2027-01-01부터 test_73이 FAIL이다.
  - 2027년 그 거래소들의 휴장일은 '알 수 없음'이 된다. 그러면 주간 패턴 기본값으로 'open'이 표시된다(`core/markets.py:174-181`). 예: SSE 춘절.
- **영향** 66일 뒤 QA가 깨진다. 소비자 화면에 휴장일이 개장으로 표시된다.
- **수정안**
  - 생성기를 복구하거나, UI 문구를 실제 절차(공식 공지로 JSON 수기 보정과 서명)로 바꾼다.
  - SSE/SZSE 2027은 국무원 공지(통상 11–12월) 뒤에 추가한다.
  - test_73은 설계상 경보이므로 유지한다. 다만 만료 30일 전부터 보이는 별도 경고 테스트를 둔다.
- **회귀 테스트**
  - `stale_markets(date(2027,1,2))`에 만료 시장이 없어야 한다(데이터 갱신 후).
  - UI 문구가 가리키는 경로가 실제로 있어야 한다: `Path('pkg_tools/generate_calendars.py').exists()` 또는 문구 변경.

#### M-4 signed_utc 형식을 검사하지 않음. 제안 마감 테스트의 문자열 비교가 오판함
- **심각도** P3 · **판정** 사실
- **위치**
  - `core/calendars/store.py:139-140`: 빈 값만 검사한다.
  - 제안 테스트 `DEADLINE_UTC` 문자열 비교(`f.signed_utc < DEADLINE_UTC`).
- **재현** 패치 사본을 각 값으로 서명하고 `test_cal02_2027_files_signed_before_2026_11_01`을 돌렸다(`W/sign_patched.py`, `W/t_ps_*`).
  - `"10/30/2026"`: PASS(오판).
  - `"2026-10-31T23:59:00+09:00"`: 마감 전(14:59Z)인데 AssertionError.
  - `"2026-11-02T00:00:00Z"`: 정상적으로 FAIL.
- **기대 결과** 형식이 틀린 서명 시각은 적재할 때 거부한다. 마감 비교는 datetime으로 한다.
- **실제 결과** 임의 문자열이 통과한다. 비교는 사전순이다.
- **영향** 마감 준수 증빙이 오판될 수 있다.
- **수정안**
```diff
--- a/core/calendars/store.py
+++ b/core/calendars/store.py
@@ def parse_file(doc: dict, *, manifest_row: Optional[dict], path: Optional[Path] = None) -> CalendarFile:
     if not _signed(doc.get("signed_utc")):
         raise CalendarUnsigned(f"{name}: signed_utc is empty")
+    try:
+        if not doc["signed_utc"].endswith("Z"):
+            raise ValueError("must end in Z (UTC)")
+        datetime.fromisoformat(doc["signed_utc"][:-1] + "+00:00")
+    except ValueError as exc:
+        raise CalendarUnsigned(f"{name}: signed_utc {doc['signed_utc']!r} is not an ISO-8601 UTC instant ({exc})") from None
```
  - 테스트 쪽은 `datetime.fromisoformat(f.signed_utc[:-1] + "+00:00") < datetime(2026, 10, 31, 15, tzinfo=timezone.utc)`로 비교한다.
- **회귀 테스트** `test_cal01_signed_utc_must_be_iso_utc`
  - 픽스처 signed_utc `"10/30/2026"`이면 CalendarUnsigned이고, 메시지에 'signed_utc'가 들어간다.
  - `"2026-10-30T00:00:00Z"`이면 적재된다.
