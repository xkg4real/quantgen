# D-04 · D-05 타임스탬프 감사 (2026-10-27)

감사 차원: `d04_d05_timestamps`. 요청서 4장 D-04(매크로 기준일), D-05(KIS 시세 as_of). 두 항목 모두 요청서에서 "미확정"이었다.
감사 전용이다. 추적 파일은 하나도 고치지 않았다. 수정안은 아래 diff로만 제시한다. `.env`는 열지 않았다. 시장 데이터 공급자에 실제로 호출하지 않았다.

## 0. 요약

1. **D-04는 사실이다(매크로 시트 경로).** `macro_sheet`는 18개 행의 마지막 관측일 중 가장 늦은 날짜 하나를 `as_of`로 쓴다(`core/ficc/macro.py:223`). 행마다 `last_date`는 남지만 화면 표에는 나오지 않는다. 발표 시각과 수신 시각은 아예 보관하지 않는다. 실데이터 18개만으로 재현했다. `as_of 2026-10-23`인데 H.10 환율 4개는 `2026-10-16`에 끝나 있었다(7일 지연이 가려짐).
2. **v2 PIT 경로는 이미 분리돼 있다.** `core/ficc/pit.py`는 `obs_date`, `available_at_utc`, `retrieved_at_utc`를 따로 저장한다. 요청서 주장을 시스템 전체로 넓히면 오류다. 다만 이 경로에도 시세 스냅숏 하나가 수신 시각으로 찍히는 결함이 있다(D05-03).
3. **D-05는 사실이다.** `KISClient.quote()`와 `index()`는 `as_of=_now()`로 응답 수신 시각을 넣는다(`data/krx/kis_client.py:269`, `:324`). KIS `inquire-price` 응답에는 시각 필드가 없다(공식 샘플 82개 필드 확인).
4. **엔진 영향이 크다(P1).** 엔진 신선도 가드는 `quote.as_of`만 본다. 수신 시각이 들어오니 KIS 시세는 늘 0초짜리다. 거래정지 종목이 장중에 모의주문을 체결(FIRED)하는 것을 끝에서 끝까지 재현했다. 같은 가격에 실제 거래소 시각을 넣으면 가드가 SKIP한다.
5. KRX 대체 경로도 같은 문제다. 전일 종가 행이 수신 시각으로 찍혀 "실시간"으로 통과한다(코드 사실, 실서버 동작은 미검증).
6. 제안 패치는 스크래치 사본에 적용해 검증했다. 새 회귀 테스트 10개는 원본에서 10개 모두 FAIL, 패치본에서 10개 모두 PASS. 관련 기존 테스트 284개(PASS 253, NOT_RUN 31)는 패치 전후 결과가 같다(회귀 0건). `git apply --check`로 저장소에 그대로 적용되는 것도 확인했다(적용은 하지 않음).

## 1. 범위

| 항목 | 대상 |
|---|---|
| D-04 | `core/ficc/macro.py`, `core/ficc/data.py`(Series, 캐시, FRED/Yahoo 호출), `core/ficc/insights.py`(서술문·AI 프롬프트), `ui/macro_page.py`, `ui/fcharts.py`, `core/ficc/pit.py`, `core/ficc/context_log.py`, `ui/macro_state_panel.py`, `core/ficc/lag_audit.py`, `core/ficc/macro_artifacts.py` |
| D-05 | `data/krx/kis_client.py`, `data/krx/gateway.py`, `data/krx/krx_market_client.py`, `data/kis_markets.py`, `core/engine/feed.py`, `core/engine/evaluator.py`, `core/engine/orders.py`, `core/markets.py`, `main.py`, `ui/krx_page.py`, `ui/derivatives_page.py`, `docs/kis_quote_check.py`, `research_notes/QUANTGEN asset coverage expansion/kis_api_audit.md` |
| 주장 출처 | `research_notes/QUANTGEN v2 integration map/code_data_layer.md:269`, `:478`, `:494`; `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:1496`(QF1-A25 미해결 질문) |
| 제외 | `paper_live/`, `grokteam/`(열람·실행 안 함). `docs/asset_expansion/cache`의 금지 파일 4개(열지 않음. 사본 생성 때도 폴더 전체를 제외함) |

## 2. 방법

1. 코드를 직접 읽고 file:line을 기록했다. README와 요청서 문장은 근거로 쓰지 않았다.
2. 재현 스크립트는 스크래치 폴더에서 `python3 -B`로 실행했다. 네트워크는 하네스가 막는다(`requests`·`data.net` 세션 패치, FICC 캐시 TTL 0). KIS·FRED·Yahoo 응답은 스텁이다.
3. KIS 응답 필드는 공식 저장소 `koreainvestment/open-trading-api`의 `chk_*.py` 파일을 WebFetch로 읽어 확인했다(`inquire_price`, `inquire_ccnl`, `inquire_index_price`, `inquire_asking_price_exp_ccn`). 접속 불가: `fred.stlouisfed.org`, `www.federalreserve.gov`(DNS 실패). FRED API 파라미터는 2차 문서(fredr)로만 확인했다.
4. 패치 검증: `git archive HEAD`로 필요한 경로만 스크래치에 두 벌 풀었다(`orig`, `tree`). `tree`에만 패치를 적용했다. 두 사본에서 같은 테스트 묶음을 프로세스 안에서 돌렸다(`tests/run_all.py`는 실행하지 않음, `qa/acceptance_results.json` 미변경).
5. 기준선: 클라우드 기준 실행(`baseline2_results.json`)에서 관련 테스트(`engine/test_07`, `engine/test_35`, `ficc/test_macro_rows_*`)는 PASS다. 하지만 아래 7장처럼 이 테스트들은 D-04·D-05를 잡지 못한다.

## 3. 요청서 주장 판정

| 주장 | 판정 | 근거 |
|---|---|---|
| D-04: 매크로 전체 기준일이 가장 늦은 관측일 하나로 정해진다 | **사실** | `core/ficc/macro.py:223` `as_of=max(r.last_date for r in rows)`. 재현 r1 |
| D-04: 그 결과 지표별 지연이 가려진다 | **사실(화면·서술문)** | 표 열에 날짜 없음(`ui/macro_page.py:43`). 칩은 `as of {as_of}` 하나(`:161`). 서술문 "Daily read for {as_of}"(`core/ficc/insights.py:388`), 프롬프트 "Date the note to as_of"(`:559`, `:573`). AI 페이로드 행에는 `last_date`가 있다(`macro.py:240`) |
| D-04 조치: 시리즈별 observation_date / release·available_at / fetched_at 구분 | 시트 경로 **미구분(사실)**, PIT 경로 **구분됨(요청서 주장 확대 시 오류)** | 시트: `MacroRow`(`macro.py:84-97`)와 `Series`(`data.py:77-84`)에 발표·수신 시각 없음. 캐시 수신 시각 `ts`는 `_MEM`에만 있고 버려짐(`data.py:233-265`, `:513-544`). PIT: `PITValue`(`pit.py:56-76`)가 세 시각을 따로 가짐. 재현 r3 |
| D-05: KIS 시세 as_of가 공급자 측정 시각이 아니라 응답 수신 시각이다 | **사실** | `kis_client.py:133-134` `_now()`, `:269`, `:324`. 재현 r2 |
| D-05: 그래서 시세가 실제보다 최신처럼 보인다 | **사실(엔진·화면)** | 엔진 가드 `evaluator.py:261-312`는 `quote.as_of`만 본다. 재현 r4: 거래정지 종목 FIRED. 화면 `ui/krx_page.py:116` "as of {q.as_of}" |
| D-05 조치: exchange timestamp와 fetched_at 별도 보관 | **미구현(사실)** | `Quote`(`kis_client.py:108-122`)에 거래소 시각·수신 시각 필드 구분 없음 |

## 4. 발견사항

### D04-01 매크로 시트 기준일이 최신 관측일 하나라서 시리즈별 지연이 가려진다

| 필드 | 내용 |
|---|---|
| ID | D04-01 |
| 심각도 | P2 (요청서는 "높음". 시트는 맥락 전용이고 엔진·리스크에 들어가지 않는다(T-CTX-01, `macro.py:1-8`). 그래서 P1이 아니다) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/macro.py` `macro_sheet` `:223`; `MacroRow` `:84-97`; `daily_brief` `:248`. `ui/macro_page.py` `_COLUMNS` `:43`, 칩 `:161-163`. `core/ficc/insights.py` `narrate_macro` `:361`, `narrate_daily_brief` `:388`, `narrate_weekly_strategy` `:437`, 프롬프트 `:559`, `:573`. `ui/fcharts.py:396`(차트 제목) |
| 재현 단계 | `audit_work/d04_d05_timestamps/r1_d04_asof_hides_lag.py`. `core.ficc.data._fetch`를 스텁으로 바꿔 18개 실데이터 행을 만든다. H.15 금리·SOFR·DFF·OAS·VIX는 2026-10-22, H.10 4개(DTWEXBGS, DEXUSEU, DEXJPUS, DEXKOUS)는 2026-10-16, WTI는 2026-10-19, Yahoo 선물 2개는 2026-10-23에 끝난다. `macro_sheet(source="auto")` 호출 |
| 기대 결과 | 기준일과 함께 가장 오래된 관측일이 보인다. 늦은 행이 표시된다. 서술문과 AI 리포트가 행별 날짜를 쓴다 |
| 실제 결과 | `as_of == "2026-10-23"`. 합성 행 없음(`{'FRED': 16, 'YFINANCE': 2}`). 가장 오래된 행은 7일 전(2026-10-16, H.10 4개). `MacroSheet` 필드는 `as_of, rows, regime, sources, synthetic_ids, note`뿐이다. 표 열에 날짜가 없다. 서술문은 "Daily read for 2026-10-23."으로 시작한다. "Biggest moves on the day"에 10-16 변동(EUR/USD +1.2%)과 10-22 변동이 섞인다. 달러 판독(`regime.dollar`)은 10-16에 끝난 DTWEXBGS로 계산된다 |
| 영향 | 사용자는 모든 지표가 10-23 기준이라고 읽는다. 일간·주간 리포트와 Claude 프롬프트도 as_of 날짜로 쓰인다. "하루 변동" 순위가 서로 다른 날의 변동을 비교한다. Yahoo 일봉은 장중 미완성 봉을 오늘 날짜로 줄 수 있다(`data.py:224-230` 주석). 그러면 as_of가 오늘이 되지만 그 값은 종가가 아니다(이 부분은 추정, yfinance 미설치로 미재현). 합성 행이 섞이면 as_of가 오늘로 바뀌는 문제는 D03-02와 같다 |
| 수정안 | 아래 7.1 diff(`core/ficc/macro.py`, `ui/macro_page.py`, `core/ficc/insights.py`). `as_of`는 합성이 아닌 행의 최신일(D03-02 수정 포함). 행마다 `lag_bdays`. 시트에 `oldest_date`, `lagging`. 표에 "Obs date" 열(지연 시 경고색 `-5d`). 칩은 `obs 2026-10-16 → 2026-10-23`. 서술문 첫 문장에 기간. 프롬프트에 "lagging 행은 자기 last_date를 쓴다" |
| 회귀 테스트 | `test_d04_macro_rows_keep_their_own_dates_and_the_sheet_names_the_lag`: `sheet.as_of == "2026-10-23" and sheet.oldest_date == "2026-10-16"`, `dict(sheet.lagging)["DEXKOUS"] == "2026-10-16"`, `sheet.row("DEXKOUS").lag_bdays == 5`, `"end before 2026-10-23" in sheet.note`. `test_d04_daily_brief_and_narrative_carry_the_span`: `brief["oldest_date"] == "2026-10-16"`, `"between 2026-10-16 and 2026-10-23" in narrate_daily_brief(sheet)`. `test_d04_macro_page_shows_an_obs_date_column`: `"Obs date" in _COLUMNS` |

### D04-02 시트 경로는 발표 시각과 수신 시각을 보관하지 않는다 (공급사 필요)

| 필드 | 내용 |
|---|---|
| ID | D04-02 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/data.py` `Series` `:77-84`(필드 `id, label, source, dates, values, note`), `_fred_fetch` `:163-192`(키 없는 `fredgraph.csv`: `observation_date`와 값만), `_cache_get` `:233-265`(수신 시각 `ts`를 `_MEM`에만 둠), `load_many` `:535-538`(`ts`를 Series로 넘기지 않음). `config.py:271`(`FRED_BASE_URL` = fredgraph.csv), `:274`(캐시 TTL 6시간) |
| 재현 단계 | r1 출력: `MacroRow`에 `fetched_at`, `retrieved_at_utc`, `available_at_utc`, `release_date`, `obs_date` 필드 없음. `Series`에 fetch/retrieve 필드 없음 |
| 기대 결과 | 행마다 관측일(observation_date), 발표·이용 가능 시각(release/available_at), 수신 시각(fetched_at)이 따로 있다 |
| 실제 결과 | 관측일(`last_date`)만 있다. 캐시 적중 시 최대 6시간 전에 받은 값이 화면에 나오지만 수신 시각을 알 수 없다. FRED 키 없는 CSV는 발표일·수정(vintage) 정보를 주지 않는다 |
| 영향 | 같은 화면에서 "언제 받았는지"와 "언제 발표됐는지"를 확인할 수 없다. 수정 발표 여부도 구분할 수 없다(요청서 6장 "관측일과 실제 발표일, 수정 발표 여부" 요구 미충족) |
| 수정안 | (1) 즉시: 7.1 diff의 `Series.fetched_at_utc`, `MacroRow.fetched_at_utc`(캐시 적중이면 파일 `ts`, 새 호출이면 그 시각). 표의 Obs date 툴팁에 표시. (2) 발표 시각: 저장소에 이미 발표 규칙이 있다(`core/calendars/publication.py:140-175`, `core/calendars/data/publication_schedules.yaml`의 H15·H10 등). 다만 파일이 미서명 초안이라 로드가 거부된다(`publication_schedules.yaml:3`). 소유자 서명 후 `available_at = publication_instant(series, last_date)`를 행에 붙인다. (3) 공급사(소유자 메모 "공급사필요"에 대한 답): 같은 FRED를 **키 있는 FRED API**로 바꾼다. `fred/series/observations`는 `realtime_start`/`realtime_end`(그 값이 처음 보인 날짜), `output_type`, `vintage_dates`를 준다. `fred/series`는 `last_updated`를 준다. ALFRED가 과거 수정 이력을 준다. 키는 무료다. 새 공급사가 아니라 같은 공급사의 다른 엔드포인트다(2차 문서 확인, 공식 페이지 접속 불가) |
| 회귀 테스트 | `test_d04_macro_rows_keep_their_own_dates_and_the_sheet_names_the_lag`의 `all(r.fetched_at_utc.endswith("Z") for r in sheet.rows)`. FRED API 전환 시: `test_fred_api_rows_carry_realtime_start`(스텁 응답의 `realtime_start`가 행의 `available_date`로 들어가는지) |

### D04-03 v2 PIT·컨텍스트 로그는 세 시각을 구분한다. 화면은 일부만 보여준다

| 필드 | 내용 |
|---|---|
| ID | D04-03 |
| 심각도 | P3 |
| 판정 | 사실(구분은 되어 있음. 요청서 주장을 PIT 경로까지 넓히면 오류) |
| 파일·함수·라인 | `core/ficc/pit.py` `PITValue` `:56-76`, `stamp_release` `:526-546`. `core/ficc/context_log.py` `_raw_item` `:551-558`(`obs_date`, `available_at_utc`, `retrieved_at_utc`, `vintage`, `stale`). `ui/macro_state_panel.py` `_context_tile` `:486-492`(열: Name, Series, Obs date, Value, Value status, Stale, Note). 컨텍스트 로그의 `as_of_utc`는 결정 시각이다(`context_log.py:846`) |
| 재현 단계 | `r3_pit_fields.py` (a): DGS10(FRED_H15)을 `ingest`한다 |
| 기대 결과 | 세 시각이 서로 다르게 저장된다 |
| 실제 결과 | `obs_date 2026-10-22`, `available_at 2026-10-23T20:15Z (calendar_bound)`, `retrieved_at 2026-10-23T22:00Z`. 기대대로다. 화면 타일은 Obs date와 Stale만 보이고 available_at·retrieved_at은 보이지 않는다 |
| 영향 | 낮음. 아티팩트 JSON에는 있다. 화면에서 "발표 후 얼마 만에 받았는지"를 확인할 수 없다 |
| 수정안 | `_context_tile` 표에 "Available (UTC)", "Retrieved (UTC)" 두 열 추가(설명만, diff 생략) |
| 회귀 테스트 | `test_context_tile_shows_available_and_retrieved`: 아이템 1개짜리 ctx로 `_context_tile`을 만들고 표 헤더에 두 열 이름이 있는지 확인 |

### D05-01 KIS 시세 as_of가 응답 수신 시각이라 엔진 신선도 가드가 무력화된다

| 필드 | 내용 |
|---|---|
| ID | D05-01 |
| 심각도 | P1 |
| 판정 | 사실 |
| 파일·함수·라인 | `data/krx/kis_client.py` `_now` `:133-134`, `KISClient.quote` `:248-270`(`as_of=_now()` `:269`), `index` `:307-326`(`:324`). 소비: `core/engine/feed.py` `_from_krx` `:199-215` → `_record` `:260-273`; `core/engine/evaluator.py` `evaluate` `:192`, `_freshness` `:261-312`; `core/markets.py:71`(장중 한도 120초), `:249`(KRX 09:00–15:30); 연결 `main.py:106`. 화면 `ui/krx_page.py:116` |
| 재현 단계 | (1) `r2_d05_kis_asof.py`: `_get`을 스텁으로 바꾸고 `quote()` 호출 전후 시각 t0, t1을 잰다. (2) `r4_d05_engine_e2e.py`: 거래정지 종목 응답(`temp_stop_yn=Y`, 거래량 0, 가격 61,000)을 KIS 스텁 → `KRXGateway` → `QuoteFeed` → `Evaluator.evaluate`로 흘린다. 규칙은 "62,000 이하 매수", 시각은 2026-10-27 11:00 KST(장중) |
| 기대 결과 | `as_of`는 거래소가 준 시각이다. 그 시각이 없으면 비어 있고, 피드는 "타임스탬프 없음"으로 거절한다(`feed.py:25-30`에 적힌 계약). 거래정지 종목은 장중에 SKIP 또는 HALT된다 |
| 실제 결과 | `t0 <= as_of <= t1`(수신 시각). 응답 내용과 무관하다. `quote()`·`index()`가 읽는 키에 hour/time/date가 하나도 없다. 공식 `inquire-price` 출력 82개 필드에도 시각 필드가 없다(`chk_inquire_price.py`). 엔진: 신선도 판정 `(None, "")`(통과) → **FIRED**, 모의주문 1건(체결가 61,000). 같은 가격에 실제 마지막 체결 시각(2026-10-26 15:30 KST)을 넣으면 **SKIPPED**("before today's open"). 10분 전 시각이면 HALTED(605초 > 120초). 6.8일 전이면 HALTED(5일 상한) |
| 영향 | KRX 규칙에서는 신선도 가드가 한 번도 작동하지 않는다. 거래정지·피드 정지·장 시작 전 잔존 가격이 모두 "방금 받은 시세"로 통과한다. 모의주문 기록과 그에 기반한 포워드 기록이 오염된다. 실주문 경로는 없다(읽기 전용). 그래서 P0는 아니다. 화면도 수신 시각을 "as of"로 보여준다. 대조: FMP 경로는 공급자 `timestamp`를 쓴다(`data/fmp/quote_client.py:86`, `:282`). KRX 경로만 틀렸다. 모듈 설명문은 4번째 엔드포인트로 `inquire-ccnl`(체결)을 적었지만 구현도 허용목록도 없다(`kis_client.py:8-13`, `config.py:90-116`) |
| 수정안 | 7.2 diff. `Quote.as_of`는 거래소 시각, 새 필드 `Quote.fetched_at`은 수신 시각. 거래소 시각은 이미 허용목록에 있는 `inquire-asking-price-exp-ccn`(FHKST01010200) 응답 `output1.aspr_acpt_hour`(호가 접수 시간, KST HHMMSS)에서 얻는다. 시각만 오므로 수신 시점의 KST 날짜를 붙이고, 수신보다 늦으면 직전 평일로 내린다(`_kst_stamp`). `temp_stop_yn == "Y"`이거나 시각이 없으면 `as_of = ""` → 피드가 거절한다. 대안(소유자 결정): `inquire-ccnl`의 `stck_cntg_hour`(체결 시간)를 쓰면 체결 기준이 된다. 다만 허용목록(`config.py`) 추가와 `tests/macro_m1_pit.py:1047`의 `len(allow) == 25` 변경이 필요하다. 비용: 시세 1건당 KIS 호출 1회 추가(호출 간격 0.12초, P-01과 연관) |
| 회귀 테스트 | `test_d05_kis_quote_as_of_is_the_exchange_book_time_not_the_receipt`: 수신 `02:00:00Z`, `aspr_acpt_hour="105958"` → `q.as_of == "2026-10-27T01:59:58+00:00" and q.fetched_at == "2026-10-27T02:00:00+00:00"`. `test_d05_suspended_or_unstamped_kis_quote_has_no_as_of_and_the_feed_refuses_it`: 거래정지 또는 시각 없음 → `q.as_of == ""`, `feed.fetch(...) is None`, `"timestamp" in feed.last_error(...)`. `test_d05_pre_open_book_time_is_dated_to_the_previous_weekday`: 월요일 08:00 KST에 `"153000"` → 금요일 06:30Z |

### D05-02 KRX 대체 경로의 종가 행도 수신 시각으로 찍혀 실시간 시세로 통과한다

| 필드 | 내용 |
|---|---|
| ID | D05-02 |
| 심각도 | P2 |
| 판정 | 사실(타임스탬프 처리). 실서버가 장중에 행을 주는지는 미검증 |
| 파일·함수·라인 | `data/krx/gateway.py` `quote` `:62-86`(KIS 실패 시 `all_quotes` 대체, `as_of=row["as_of"]` `:82`). `data/krx/krx_market_client.py` `_now` `:64-65`, `_session_date` `:68-69`(머신 로컬 날짜), `_from_api` `:181`, `_from_csv` `:204`, `indices` `:226` |
| 재현 단계 | `r2_d05_kis_asof.py` 5번: KIS 미설정 게이트웨이, `_api` 스텁이 `BAS_DD="20261023"` 종가 행을 준다. 피드와 `_freshness`에 넘긴다 |
| 기대 결과 | 전체 시장 일별 행은 그 세션 종가(15:30 KST)로 찍힌다. 엔진은 "오늘 개장 전 가격"으로 SKIP한다 |
| 실제 결과 | `as_of = 2026-10-27T02:00:00+00:00`(수신 시각). `BAS_DD`는 무시된다. 요청한 `basDd`는 `20261027`(오늘, 로컬 날짜). 엔진 신선도 판정 `(None, "")`(통과) |
| 영향 | KIS 장애 중에 KRX 키가 있으면 전일 종가로 모의주문이 나갈 수 있다. 화면도 종가를 "as of 지금"으로 표시한다(`gateway.py:13-15`의 "KIS 실시간과 KRX 전일 종가를 구분해 표시" 원칙 위반) |
| 수정안 | 7.2 diff `_close_utc`: `as_of`는 `BAS_DD`(없으면 요청한 `basDd`)의 15:30 KST. `fetched_at`은 수신 시각. 게이트웨이가 `fetched_at`을 Quote로 넘긴다 |
| 회귀 테스트 | `test_d05_krx_fallback_row_is_stamped_at_its_session_close`: `row["as_of"] == "2026-10-23T06:30:00+00:00" and row["fetched_at"]` |

### D05-03 PIT `ingest()`가 시세 스냅숏을 수신 시각으로 찍고 "published"로 표시한다

| 필드 | 내용 |
|---|---|
| ID | D05-03 |
| 심각도 | P2 (현재 이 시리즈를 쓰는 생산 코드가 없다. 잠재 결함) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/pit.py` `ingest` `:580-582`(`quote_utc=retrieved_at_utc`), `stamp_quote` `:549-555`(`available_at_source="published"` 고정). 대상 시리즈 `data/macro/series_registry.yaml:344`(USDKRW_1530_SNAPSHOT, 원천 KIS), `:525`(US10Y_KIS_QUOTE) 등 `obs_kind: quote_snapshot` 4개. `core/ficc/lag_audit.py:58-59`(LIVE_QUOTE면 독립 검사 없음). 소비: `core/quant/cards.py:316`(nav_fx, acting_exposure), `core/quant/forward_sim.py:213-217` |
| 재현 단계 | `r3_pit_fields.py` (b): 15:30:00 KST 스냅숏을 15:45 KST에 받아 `ingest` |
| 기대 결과 | `obs_utc`는 거래소 시각(15:30:00 KST)이다. 없으면 수신 시각을 쓰되 `available_at_source = "inferred_from_retrieval"`이다 |
| 실제 결과 | `obs_utc = available_at_utc = retrieved_at_utc = 2026-10-27T06:45:00Z`, `available_at_source = "published"`. `lag_audit` 위반 0건 |
| 영향 | 15:45에 받은 값이 "15:30:00 스냅숏"으로 통과한다. "published"는 공급자가 그 시각을 공표했다는 뜻이라 출처 표시가 틀린다. 테스트는 `stamp_quote`에 별도 `quote_utc`를 직접 넘긴다(`tests/macro_m8_forward.py:678` 등). 그래서 `ingest` 경로의 결함을 못 잡는다 |
| 수정안 | 7.2 diff: `ingest(..., quote_times=None)` 추가. `stamp_quote(quote_utc=None)`이면 수신 시각 + `inferred_from_retrieval` |
| 회귀 테스트 | `test_d05_pit_ingest_of_a_quote_snapshot_without_exchange_time_is_inferred_from_retrieval`: 시각 없이 → `available_at_source == "inferred_from_retrieval"`; `quote_times={d: 06:30Z}` → `"published"`, `obs_utc == 06:30Z`, `retrieved_at_utc == 06:45Z` |

### D05-04 모의주문에 트리거 시세의 시각이 기록되지 않는다

| 필드 | 내용 |
|---|---|
| ID | D05-04 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/engine/orders.py:67`(`as_of`: "R-27 rule 7 (M5): the triggering quote's own timestamp"), `core/engine/evaluator.py:210-214`(`SimulatedOrder(...)` 생성 시 `as_of` 미전달) |
| 재현 단계 | `r4_d05_engine_e2e.py`: FIRED 주문의 `as_of` 확인 |
| 기대 결과 | 주문 기록에 트리거 시세의 거래소 시각 |
| 실제 결과 | `as_of=None` |
| 영향 | 사후에 "어느 시점 가격으로 체결됐는지" 감사할 수 없다. 지금 넣으면 수신 시각이 들어가므로 D05-01과 함께 고쳐야 한다 |
| 수정안 | 7.2 diff: `as_of=quote.as_of` |
| 회귀 테스트 | `test_d05_simulated_order_records_the_triggering_quote_time`: `book.all()[0].as_of == stamp` |

### D05-05 KIS 지수 등락률 필드명이 공식 필드와 다르다

| 필드 | 내용 |
|---|---|
| ID | D05-05 |
| 심각도 | P3 |
| 판정 | 추정 (공식 샘플 필드 목록 기준. 실응답에 `prdy_ctrt`도 오는지는 미검증) |
| 파일·함수·라인 | `data/krx/kis_client.py` `index` `:322`(`out.get("prdy_ctrt")`) |
| 재현 단계 | `r2_d05_kis_asof.py` 3번: 공식 필드(`bstp_nmix_prdy_ctrt`)로 만든 응답 |
| 기대 결과 | `change_pct == -0.46` |
| 실제 결과 | `change_pct is None`. 공식 `chk_inquire_index_price.py` 36개 필드에 `prdy_ctrt`가 없다 |
| 영향 | 지수 화면의 등락률이 빈칸일 수 있다 |
| 수정안 | 7.2 diff: `out.get("bstp_nmix_prdy_ctrt", out.get("prdy_ctrt"))` |
| 회귀 테스트 | `test_d05_kis_index_reads_the_official_change_pct_field_and_no_receipt_as_of`: `ix["change_pct"] == -0.46 and ix["as_of"] == ""` |

### D05-06 `KISMarkets`의 as_of는 로컬 날짜·로컬 시각이다

| 필드 | 내용 |
|---|---|
| ID | D05-06 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `data/kis_markets.py:220`(etf_quote), `:273`(futures_quote), `:457`(overseas_quote), `:568`(bond_quote): `date.today()`. `:390`, `:430`(OptionBoard): `datetime.now()`(시간대 없음). `ui/derivatives_page.py:78`, `:232-233` |
| 재현 단계 | `r2_d05_kis_asof.py` 6번: `etf_quote`, `bond_quote` |
| 기대 결과 | 거래소 시각 또는 세션 날짜. 수신 시각은 UTC로 따로 |
| 실제 결과 | `as_of == date.today()`(2026-10-27). 토요일에 받으면 금요일 종가가 토요일 날짜로 찍힌다(코드상 사실) |
| 영향 | 낮음. 파생상품 화면은 "prices of {session}" 칩을 따로 보여 일부 완화된다(`ui/derivatives_page.py:233`). 단 같은 줄의 "as of"는 로컬 수신 시각이다 |
| 수정안 | 각 dict에 `"fetched_at": _utc_now()` 추가. `as_of`는 세션 날짜(`last_session()`)로 바꾸거나 키 이름을 `fetched_on`으로 바꾼다. 옵션 보드는 `aspr_acpt_hour`를 이미 읽으므로(`:684`) 그 값을 `book_time`으로 보관한다(설명만, diff 생략) |
| 회귀 테스트 | `test_kis_markets_quotes_carry_utc_fetched_at`: 스텁 클라이언트로 `etf_quote()["fetched_at"].endswith("+00:00")` |

### D0405-T1 기존 테스트가 두 결함을 잡지 못한다

| 필드 | 내용 |
|---|---|
| ID | D0405-T1 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `tests/ficc_acceptance.py:528`(`r.last_date == sheet.as_of`를 합성 시트에서만 확인. 합성 행은 모두 같은 날짜라 지연이 생길 수 없음). `tests/engine_acceptance.py:445-468`(test_35), `:485`(가짜 게이트웨이가 `as_of=datetime.now()`를 직접 넣음). `KISClient.quote()`의 타임스탬프를 확인하는 테스트 없음. `tests/macro_m1_fixtures.py:483-492` `test_kis_quote_check_owner_record`는 NOT_RUN(소유자 실측 기록 없음, `docs/kis_quote_check/` 폴더 없음) |
| 재현 단계 | 기준 실행 `baseline2_results.json`: 위 테스트 PASS. 원본 사본에서 새 회귀 테스트 10개 실행 → 10개 FAIL |
| 기대 결과 | 결함이 있으면 테스트가 실패한다 |
| 실제 결과 | 기존 테스트는 PASS. 결함은 남아 있다 |
| 영향 | "테스트 통과"가 타임스탬프 정확성을 보장하지 않는다 |
| 수정안 | 아래 7.3의 테스트 10개 추가. 소유자 실측(`docs/kis_quote_check.py`, 20세션)으로 `aspr_acpt_hour`와 수신 시각 차이를 기록 |
| 회귀 테스트 | 7.3 전체 |

## 5. 소유자 메모에 대한 답 (이 차원 범위만)

1. **"(-> 공급사필요)" — 금리·매크로의 관측일 / 발표일 / 수정 발표 구분.** 현재 공급 경로(키 없는 FRED CSV, pandas-datareader, Yahoo)로는 발표일과 수정 이력을 얻을 수 없다(D04-02). 가장 깔끔한 선택은 **같은 FRED의 키 기반 API + ALFRED**다. 무료 키 하나로 `realtime_start`(최초 공개일), `vintage_dates`, `output_type=4`(최초 발표값), `fred/series.last_updated`(갱신 시각)를 받는다. 저장소의 v2 설계도 이미 "FRED last_updated를 게시 시각으로 기록"을 전제한다(`core/calendars/publication.py:160`). 한국 금리는 이 차원 범위 밖이다.
2. **KIS의 거래소 시각.** `inquire-price`에는 시각이 없다. 시각을 주는 KIS 엔드포인트는 `inquire-asking-price-exp-ccn`의 `aspr_acpt_hour`(호가 접수 시간, 이미 허용목록), `inquire-ccnl`의 `stck_cntg_hour`(체결 시간, 허용목록 밖), 웹소켓 체결 피드다(`kis_api_audit.md` KQ4). 엔진 용도에는 앞의 둘이면 충분하다.
3. **"FICC/BTC 모두 KIS에서 접근 가능한지".** 공급사 선정 자체는 다른 감사 차원의 범위다. 타임스탬프 관점의 사실만 적는다. KIS의 BTC 관련 데이터는 CME BTC/ETH 선물 시세뿐이다(`kis_api_audit.md:129`, 2025-10-21 공지). 그 시세의 시각 필드는 이번에 확인하지 못했다(미검증).

## 6. 미검증 항목

1. KIS 실응답에서 `aspr_acpt_hour`가 `output1`에 오는지, 장중에 얼마나 자주 바뀌는지, 거래정지 종목에서 어떤 값을 주는지. 소유자 실측 필요(`docs/kis_quote_check.py`, 테스트 `test_kis_quote_check_owner_record` NOT_RUN).
2. `inquire-ccnl` 출력 행의 정렬 순서(최신이 첫 행인지)와 `stck_cntg_hour` 형식. 공식 샘플에 형식 설명 없음.
3. KRX Open API 응답에 `BAS_DD` 필드가 있는지, 장중에 `basDd=오늘`로 요청하면 행이 오는지(D05-02의 실제 발생 여부). 웹 검색으로 공식 필드표를 찾지 못함.
4. KIS 지수 실응답에 `prdy_ctrt`도 함께 오는지(D05-05).
5. FRED H.10(주간 월요일 게시), ICE BofA OAS(약 1일 지연), EIA WTI 게시 주기. 공식 사이트 접속 불가. r1의 날짜는 저장소의 발표 규칙(`publication_schedules.yaml`의 H10 `monday_after_week`, H15 `next_bday_after_obs`)을 따른 예시이고 실측이 아니다.
6. Yahoo 일봉이 장중 미완성 봉을 오늘 날짜로 주는 현상(yfinance 미설치로 미재현. 저장소 주석 `data.py:224-230`만 근거).
7. 패치 후 실제 앱 화면(Flet 페이지) 렌더링. 새 컨트롤 인자(`ft.DataCell(ft.Text(..., tooltip=...))`, `chip(..., "warning", tooltip=...)`)가 생성되는 것만 확인했다.
8. FRED API 파라미터는 2차 문서(fredr 문서)로만 확인했다. `api.stlouisfed.org` 공식 문서는 열지 못했다.
9. CME BTC 선물 KIS 시세의 시각 필드.

## 7. 제안 패치와 회귀 테스트

### 7.0 검증 결과

| 대상 | 원본 사본(`orig`) | 패치 사본(`tree`) |
|---|---|---|
| 새 회귀 테스트 10개 | FAIL 10 | PASS 10 |
| 관련 기존 테스트(`tests.acceptance`, `engine_acceptance`, `ficc_acceptance`, `expansion_acceptance`, `macro_m1_pit`, `macro_m1_integration`, `macro_m2_risk`, `macro_m6_context`, `macro_m8_forward`) | PASS 253, NOT_RUN 31 | PASS 253, NOT_RUN 31 (변화 없음) |
| 모듈 자체 검사 `core.ficc.macro`, `ui.macro_page`, `core.ficc.insights`, `core.ficc.data` | — | 모두 `ok` |
| 허용목록 테스트(`test_ro_02_...`, `test_kis_allowlist_frozen_...`) | PASS | PASS(허용목록 변경 없음) |
| `git apply --check -p1` (저장소, 확인만) | — | 깨끗하게 적용됨 |

패치 사본에서 같은 엔진 시나리오(`r5_patched_e2e.py`): 거래정지 → 시세 없음으로 거절(HALTED, 주문 0건). 호가 시각이 전일 15:30 → SKIPPED. 호가 시각 10:59:58 → FIRED, 주문 `as_of = 2026-10-27 01:59:58+00:00`.

주의 1. 이 패치는 D03-02의 `as_of` 수정(합성 행 제외)을 포함한다. D03 보고서의 같은 줄 diff와 충돌하므로 둘 중 하나만 적용한다.
주의 2. 거래정지·시각 없음은 엔진에서 "시세 없음"이 된다. 유예 횟수를 넘기면 엔진 전체가 멈춘다(`evaluator.py:182-191`). 거래정지 한 종목 때문에 전체가 멈추는 것을 피하려면 종목별 SKIP 경로가 따로 필요하다(소유자 결정).
주의 3. `evaluator.py`와 `ui/macro_page.py`는 CRLF 줄바꿈이다. 아래 diff는 읽기 쉽게 LF로 보였다. 적용용 원본은 `proposed_d04_d05.diff`(CRLF 보존)다.

### 7.1·7.2 diff (D-04, D-05)

```diff
--- orig/core/engine/evaluator.py
+++ tree/core/engine/evaluator.py
@@ -212,7 +212,7 @@
             rule_name=rule.name, symbol=rule.symbol, market=rule.market,
             side=rule.side, kind=rule.order_kind, quantity=quantity,
             limit_price=rule.limit_price, notional=notional,
-            trigger_price=quote.price, created_at=now,
+            trigger_price=quote.price, created_at=now, as_of=quote.as_of,
         )
 
         # 7. idempotency — cheap pre-check, so a duplicate does not even get
--- orig/core/ficc/data.py
+++ tree/core/ficc/data.py
@@ -82,6 +82,7 @@
     dates: tuple[str, ...]            # ISO dates, ascending
     values: tuple[float, ...]
     note: str = ""
+    fetched_at_utc: str = ""          # when the provider answered (a cache hit keeps its file's ts); "" if simulated
 
     def __len__(self) -> int:
         return len(self.values)
@@ -532,10 +533,13 @@
             for i in group:
                 out[i] = synthetic_series(i, days=days, kind=_synthetic_kind(i))
             continue
+        t_call = time.time()
         rows, errors = _provider_rows(prov, group, days)
         for i in group:
             if i in rows:
-                out[i] = _series_from_rows(i, prov, rows[i], days)
+                ts = _MEM.get(_cache_key(prov, i, days), (t_call,))[0]
+                out[i] = replace(_series_from_rows(i, prov, rows[i], days),
+                                 fetched_at_utc=_dt.fromtimestamp(ts, _tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
             elif source == "auto":
                 out[i] = _degraded(synthetic_series(i, days=days, kind=_synthetic_kind(i)),
                                    prov, errors[i])
--- orig/core/ficc/insights.py
+++ tree/core/ficc/insights.py
@@ -385,7 +385,11 @@
                    else 0.0, reverse=True)[:3]
     r = sheet.row
     lines = [
-        f"Daily read for {sheet.as_of}. Rates: 2y {_level(r('DGS2'))} ({_chg(r('DGS2'))} on "
+        f"Daily read for {sheet.as_of}"
+        + (f" (series end between {sheet.oldest_date} and {sheet.as_of}: "
+           + ", ".join(f"{i} {d}" for i, d in getattr(sheet, "lagging", ())) + ")"
+           if getattr(sheet, "lagging", ()) else "")
+        + f". Rates: 2y {_level(r('DGS2'))} ({_chg(r('DGS2'))} on "
         f"the day, {_chg(r('DGS2'), 'chg_1w')} on the week), 10y {_level(r('DGS10'))} "
         f"({_chg(r('DGS10'))}, {_chg(r('DGS10'), 'chg_1w')}), 2s10s {_level(r('T10Y2Y'))} "
         f"({_chg(r('T10Y2Y'))}); the 20-session curve read (descriptive, not a regime model, P19) is a "
@@ -556,7 +560,8 @@
         "against their trailing 252-session distribution, each stated with its definition "
         "and window, and the observation that would revise the reading. Describe, do not "
         "recommend: no trades, positions, entry or exit levels, sizing or forecasts. Date the "
-        "note to as_of and flag any ids listed under synthetic_ids as simulated."),
+        "note to as_of, give a series' own last_date wherever it is listed under lagging, and flag any ids "
+        "listed under synthetic_ids as simulated."),
     "weekly_fi_fx_strategy": (
         "Write a weekly fixed-income and FX research note in a formal, third-person, "
         "journal-style register, in this format: a one-line headline; 'Duration', 'Curve' and "
@@ -570,7 +575,8 @@
         "assumption or window they are most sensitive to; and 'What would revise this "
         "reading', naming the data that would change each description. Describe, do not "
         "recommend: no trades, positions, entry or exit levels, sizing or forecasts. Date it "
-        "to as_of and flag any synthetic_ids as simulated."),
+        "to as_of, give a series' own last_date wherever it is listed under lagging, and flag any "
+        "synthetic_ids as simulated."),
 }
 
 
--- orig/core/ficc/macro.py
+++ tree/core/ficc/macro.py
@@ -95,6 +95,8 @@
     z_1y: float
     pct_1y: float                     # percentile rank of `last` in the 1y window, 0..1
     source: str
+    fetched_at_utc: str = ""          # provider answer instant (cache file ts on a hit); "" when simulated
+    lag_bdays: int = 0                # weekdays between last_date and the sheet's as_of (0 = current)
 
 
 @dataclass(frozen=True)
@@ -117,6 +119,8 @@
     sources: dict[str, int]           # count of rows per source label
     synthetic_ids: tuple[str, ...]
     note: str = ""
+    oldest_date: str = ""             # the earliest last_date among the rows (as_of is the latest)
+    lagging: tuple[tuple[str, str], ...] = ()      # (id, last_date) of each live row behind as_of
 
     def row(self, id: str) -> MacroRow | None:
         return next((r for r in self.rows if r.id == id), None)
@@ -136,7 +140,8 @@
     changes = {name: s.change(n) for name, n in _CHANGES}
     return MacroRow(id=ind.id, label=ind.label, group=ind.group, unit=ind.unit,
                     last=float(s.last), last_date=s.last_date, **changes,
-                    z_1y=z, pct_1y=float((x <= x[-1]).mean()), source=s.source)
+                    z_1y=z, pct_1y=float((x <= x[-1]).mean()), source=s.source,
+                    fetched_at_utc=getattr(s, "fetched_at_utc", ""))
 
 
 def _weekdays(s: Series) -> Series:
@@ -220,9 +225,19 @@
     short = min(len(series[i.id]) for i in INDICATORS)
     if short < _Z_WINDOW:
         notes.append(f"Shortest series has {short} obs; z/percentile use fewer than 252.")
-    return MacroSheet(as_of=max(r.last_date for r in rows), rows=rows,
-                      regime=_regime_from(series, by_id), sources=sources,
-                      synthetic_ids=synthetic, note=" ".join(notes))
+    # as_of = the latest LIVE observation (a simulated row is dated today by construction, D03-02); each row keeps
+    # its own last_date and its lag behind as_of, so a weekly H.10 or a lagged OAS series is never hidden (D-04).
+    live = [r.last_date for r in rows if r.source != "SYNTHETIC"] or [r.last_date for r in rows]
+    as_of = max(live)
+    rows = tuple(replace(r, lag_bdays=int(np.busday_count(r.last_date, as_of)) if r.last_date < as_of else 0)
+                 for r in rows)
+    lagging = tuple((r.id, r.last_date) for r in rows if r.lag_bdays > 0 and r.source != "SYNTHETIC")
+    if lagging:
+        notes.append(f"{len(lagging)}/{len(rows)} rows end before {as_of}: "
+                     + ", ".join(f"{i} {d}" for i, d in lagging) + ".")
+    return MacroSheet(as_of=as_of, rows=rows, regime=_regime_from(series, by_id), sources=sources,
+                      synthetic_ids=synthetic, note=" ".join(notes),
+                      oldest_date=min(r.last_date for r in rows), lagging=lagging)
 
 
 # --------------------------------------------------------------------------- #
@@ -245,7 +260,8 @@
              for k, i in (("2y", "DGS2"), ("10y", "DGS10"), ("30y", "DGS30"),
                           ("2s10s", "T10Y2Y"), ("10y_real", "DFII10"),
                           ("10y_breakeven", "T10YIE"))}
-    return {"as_of": sheet.as_of, "regime": asdict(sheet.regime), "curve": curve,
+    return {"as_of": sheet.as_of, "oldest_date": sheet.oldest_date,
+            "lagging": [list(x) for x in sheet.lagging], "regime": asdict(sheet.regime), "curve": curve,
             "movers_z": by_z,
             "movers_1d": [dict(asdict(r), rel_1d=_rel_1d(r)) for r in by_1d],
             "rows": rows, "sources": dict(sheet.sources),
--- orig/core/ficc/pit.py
+++ tree/core/ficc/pit.py
@@ -546,18 +546,20 @@
                     provider_mode=provider_mode, synthetic=synthetic)
 
 
-def stamp_quote(series_id: str, obs_date: date, value: float, *, quote_utc: datetime, retrieved_at_utc: datetime,
+def stamp_quote(series_id: str, obs_date: date, value: float, *, quote_utc: datetime | None, retrieved_at_utc: datetime,
                 source: str, channel: str | None = None, provider_mode: str = "explicit", synthetic: bool = False) -> dict:
-    """A live quote snapshot: live_snapshot on a quote_snapshot row, available at its stamp."""
-    return make_row(series_id=series_id, value=float(value), obs_date=obs_date, session_date=None, obs_utc=quote_utc,
-                    obs_kind="quote_snapshot", value_status="live_snapshot", available_at_utc=quote_utc,
-                    available_at_source="published", retrieved_at_utc=retrieved_at_utc, vintage=None, source=source,
+    """A live quote snapshot: live_snapshot on a quote_snapshot row, available at its exchange stamp ("published").
+    Without an exchange stamp the receipt instant is used and labelled inferred_from_retrieval (D-05)."""
+    stamp, src = (quote_utc, "published") if quote_utc is not None else (retrieved_at_utc, "inferred_from_retrieval")
+    return make_row(series_id=series_id, value=float(value), obs_date=obs_date, session_date=None, obs_utc=stamp,
+                    obs_kind="quote_snapshot", value_status="live_snapshot", available_at_utc=stamp,
+                    available_at_source=src, retrieved_at_utc=retrieved_at_utc, vintage=None, source=source,
                     channel=channel, provider_mode=provider_mode, synthetic=synthetic)
 
 
 def ingest(store: PITStore, series_id: str, rows, *, source: str, retrieved_at_utc: datetime, registry, clocks,
            provider_mode: str = "explicit", synthetic: bool = False, print_times: dict | None = None,
-           ohlcv: dict | None = None, channel: str | None = None) -> IngestReport:
+           ohlcv: dict | None = None, channel: str | None = None, quote_times: dict | None = None) -> IngestReport:
     """Stamp and append `[(obs_date, value), ...]` by the series' obs_kind (single shot; the M8 workflow schedules
     it). Flags are returned, never stored. `retrieved_at_utc` is the caller's pinned instant."""
     series_id = named_series(series_id)
@@ -578,8 +580,9 @@
                             ohlcv=(ohlcv or {}).get(obs_date), channel=channel, provider_mode=provider_mode,
                             synthetic=synthetic)
         elif kind == "quote_snapshot":
-            r = stamp_quote(series_id, obs_date, value, quote_utc=retrieved_at_utc, retrieved_at_utc=retrieved_at_utc,
-                            source=source, channel=channel, provider_mode=provider_mode, synthetic=synthetic)
+            r = stamp_quote(series_id, obs_date, value, quote_utc=(quote_times or {}).get(obs_date),
+                            retrieved_at_utc=retrieved_at_utc, source=source, channel=channel,
+                            provider_mode=provider_mode, synthetic=synthetic)
         elif kind == "release":
             r = stamp_release(series_id, obs_date, value, retrieved_at_utc=retrieved_at_utc, source=source,
                               registry=registry, clocks=clocks, channel=channel, provider_mode=provider_mode,
--- orig/data/krx/gateway.py
+++ tree/data/krx/gateway.py
@@ -79,7 +79,7 @@
                     change=row["change"], change_pct=row["change_pct"],
                     volume=row["volume"], market_cap=row["market_cap"],
                     high=row["high"], low=row["low"], open=row["open"],
-                    as_of=row["as_of"], source="KRX",
+                    as_of=row["as_of"], source="KRX", fetched_at=row.get("fetched_at", ""),
                 )
                 return Answer(quote, "KRX")
         return Answer(None, "", ok=False,
--- orig/data/krx/kis_client.py
+++ tree/data/krx/kis_client.py
@@ -10,7 +10,13 @@
     현재가        /uapi/domestic-stock/v1/quotations/inquire-price
     일별 시세     /uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice
     지수          /uapi/domestic-stock/v1/quotations/inquire-index-price
-    체결          /uapi/domestic-stock/v1/quotations/inquire-ccnl
+    호가 (시각)   /uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn
+
+TIMESTAMPS
+----------
+`Quote.as_of` is the exchange instant of the price (the book's 호가 접수 시간), never the receipt instant; the
+receipt is `Quote.fetched_at`. A quote without an exchange instant has `as_of == ""`, which the engine's feed
+treats as missing data (it never invents a time).
 
 Adding an order path would require a new module, a new credential (account
 number), and an explicit decision. That is deliberate.
@@ -118,8 +124,9 @@
     low: Optional[float]
     open: Optional[float]
     currency: str = "KRW"
-    as_of: str = ""
+    as_of: str = ""          # exchange instant (ISO UTC) of the price; "" when the exchange gave none (never "now")
     source: str = "KIS"
+    fetched_at: str = ""     # receipt instant (ISO UTC): when this process got the answer
 
 
 def _f(value: Any) -> Optional[float]:
@@ -134,6 +141,24 @@
     return datetime.now(timezone.utc).isoformat(timespec="seconds")
 
 
+_KST = timezone(timedelta(hours=9))
+_BOOK_PATH = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"     # allowlisted (quote check)
+
+
+def _kst_stamp(hhmmss: str, receipt_utc: datetime) -> Optional[datetime]:
+    """A KST time of day from the exchange (HHMMSS) dated on the receipt's KST date; one weekday earlier when that
+    would put it after the receipt (a pre-open answer still shows the previous session). None if unreadable.
+    ponytail: a holiday between sessions dates the stamp later than the truth, never later than today's open."""
+    t = str(hhmmss or "").strip()
+    if len(t) != 6 or not t.isdigit() or int(t[:2]) > 23:
+        return None
+    local = receipt_utc.astimezone(_KST)
+    stamp = local.replace(hour=int(t[:2]), minute=int(t[2:4]), second=int(t[4:]), microsecond=0)
+    while stamp > local or stamp.weekday() >= 5:
+        stamp -= timedelta(days=1)
+    return stamp.astimezone(timezone.utc)
+
+
 class KISClient:
     """Thin read-only wrapper. Construction performs no network request."""
 
@@ -255,6 +280,13 @@
             retry=False,
         )
         out = payload.get("output") or {}
+        fetched = _now()
+        # FHKST01010100 carries no time of day (open-trading-api chk_inquire_price: 82 fields, none a time). The
+        # exchange instant is the level-1 book's 호가 접수 시간 (`aspr_acpt_hour`, FHKST01010200); a suspended
+        # issue (temp_stop_yn = Y) has no live price at all. Either way as_of is never the receipt instant (D-05).
+        stamp = None
+        if str(out.get("temp_stop_yn") or "").strip().upper() != "Y":
+            stamp = self.exchange_time(code, datetime.fromisoformat(fetched))
         return Quote(
             ticker=code,
             name=str(out.get("hts_kor_isnm") or "").strip(),
@@ -266,9 +298,21 @@
             high=_f(out.get("stck_hgpr")),
             low=_f(out.get("stck_lwpr")),
             open=_f(out.get("stck_oprc")),
-            as_of=_now(),
+            as_of=stamp.isoformat(timespec="seconds") if stamp else "",
+            fetched_at=fetched,
         )
 
+    def exchange_time(self, code: str, receipt_utc: datetime) -> Optional[datetime]:
+        """The KRX book instant of `code` (UTC), or None when KIS gives none or the call fails (fail closed)."""
+        try:
+            payload = self._get(_BOOK_PATH, "FHKST01010200",
+                                {"FID_COND_MRKT_DIV_CODE": _MRKT_STOCK, "FID_INPUT_ISCD": _normalize(code)},
+                                retry=False)
+        except KISError:
+            return None
+        out = payload.get("output1") or payload.get("output") or {}
+        return _kst_stamp(out.get("aspr_acpt_hour"), receipt_utc)
+
     def daily(self, code: str, *, start: Optional[str] = None,
               end: Optional[str] = None, adjusted: bool = True) -> list[dict]:
         """Daily OHLCV. Dates are YYYYMMDD; defaults to the last ~100 sessions."""
@@ -319,9 +363,10 @@
             "market": name.upper(),
             "level": _f(out.get("bstp_nmix_prpr")),
             "change": _f(out.get("bstp_nmix_prdy_vrss")),
-            "change_pct": _f(out.get("prdy_ctrt")),
+            "change_pct": _f(out.get("bstp_nmix_prdy_ctrt", out.get("prdy_ctrt"))),
             "volume": _f(out.get("acml_vol")),
-            "as_of": _now(),
+            "as_of": "",                 # FHPUP02100000 carries no time of day; never the receipt instant
+            "fetched_at": _now(),
             "source": "KIS",
         }
 
--- orig/data/krx/krx_market_client.py
+++ tree/data/krx/krx_market_client.py
@@ -21,7 +21,7 @@
 
 import csv
 import io
-from datetime import datetime, timezone
+from datetime import datetime, timedelta, timezone
 from typing import Optional
 
 import config
@@ -69,6 +69,14 @@
     return date or datetime.now().strftime("%Y%m%d")
 
 
+def _close_utc(yyyymmdd: str) -> str:
+    """The KRX regular-session close (15:30 KST) of a session date, ISO UTC: a whole-market row is that close,
+    never a live print, so its as_of is the close instant and not the receipt (D-05)."""
+    d = datetime.strptime(str(yyyymmdd).strip()[:8], "%Y%m%d")
+    return (d.replace(hour=15, minute=30, tzinfo=timezone(timedelta(hours=9)))
+            .astimezone(timezone.utc).isoformat(timespec="seconds"))
+
+
 class KRXMarketClient:
     """Whole-market KRX data. Construction performs no network request."""
 
@@ -148,7 +156,7 @@
                     continue
                 try:
                     for raw in self._api(endpoint, {"basDd": day}):
-                        out.append(self._from_api(raw, name))
+                        out.append(self._from_api(raw, name, day))
                 except KRXError:
                     continue
             if out:
@@ -160,9 +168,9 @@
             })
         except KRXError:
             return []
-        return [q for q in (self._from_csv(r, market) for r in rows) if q]
+        return [q for q in (self._from_csv(r, market, day) for r in rows) if q]
 
-    def _from_api(self, raw: dict, market: str) -> dict:
+    def _from_api(self, raw: dict, market: str, day: str) -> dict:
         return {
             "ticker": str(raw.get("ISU_SRT_CD") or "").strip(),
             "name": str(raw.get("ISU_NM") or "").strip(),
@@ -178,11 +186,12 @@
             "market_cap": _f(raw.get("MKTCAP")),
             "shares": _f(raw.get("LIST_SHRS")),
             "currency": "KRW",
-            "as_of": _now(),
+            "as_of": _close_utc(raw.get("BAS_DD") or day),
+            "fetched_at": _now(),
             "source": "KRX Open API",
         }
 
-    def _from_csv(self, raw: dict, market: str) -> Optional[dict]:
+    def _from_csv(self, raw: dict, market: str, day: str) -> Optional[dict]:
         code = (raw.get("종목코드") or "").strip()
         if not code:
             return None
@@ -201,15 +210,17 @@
             "market_cap": _f(raw.get("시가총액")),
             "shares": _f(raw.get("상장주식수")),
             "currency": "KRW",
-            "as_of": _now(),
+            "as_of": _close_utc(day),
+            "fetched_at": _now(),
             "source": "KRX",
         }
 
     def indices(self, *, date: Optional[str] = None) -> list[dict]:
         if not self.has_key:
             return []
+        day = _session_date(date)
         try:
-            rows = self._api(_API_ENDPOINTS["INDEX"], {"basDd": _session_date(date)})
+            rows = self._api(_API_ENDPOINTS["INDEX"], {"basDd": day})
         except KRXError:
             return []
         out = []
@@ -223,7 +234,8 @@
                 "change": _f(raw.get("CMPPREVDD_IDX")),
                 "change_pct": _f(raw.get("FLUC_RT")),
                 "volume": _f(raw.get("ACC_TRDVOL")),
-                "as_of": _now(),
+                "as_of": _close_utc(raw.get("BAS_DD") or day),
+                "fetched_at": _now(),
                 "source": "KRX Open API",
             })
         return out
--- orig/ui/krx_page.py
+++ tree/ui/krx_page.py
@@ -113,7 +113,8 @@
                                           if q.volume else "—"),
                                 key_value("Market cap", format_compact(q.market_cap, locale, 1)
                                           if q.market_cap else "—"),
-                                key_value("Source", f"{answer.source} · as of {q.as_of}"),
+                                key_value("Source", f"{answer.source} · as of "
+                                          f"{q.as_of or 'exchange time unknown'} · fetched {q.fetched_at or '—'}"),
                             ], spacing=6),
                         ]
                     else:
--- orig/ui/macro_page.py
+++ tree/ui/macro_page.py
@@ -40,7 +40,7 @@
 _HEADLINE = ("DGS2", "DGS10", "DGS30", "T10Y2Y", "DFII10", "T10YIE",
              "VIXCLS", "BAMLH0A0HYM2", "DTWEXBGS")
 _REGIME_TOKEN = {"risk-on": "success", "risk-off": "error"}
-_COLUMNS = ("Group", "Indicator", "Last", "1d", "1w", "1m", "3m", "z (1y)", "pct (1y)", "Source")
+_COLUMNS = ("Group", "Indicator", "Last", "Obs date", "1d", "1w", "1m", "3m", "z (1y)", "pct (1y)", "Source")
 _VIEWS = (("sheet", "Macro sheet"), ("overlay", "Overlay state"), ("cards", "Model cards"),
           ("research", "Research register"))
 _BUILDERS = {"overlay": build_overlay_view, "cards": build_cards_view,     # view key -> builder(page);
@@ -112,6 +112,9 @@
             rows.append(ft.DataRow(cells=[
                 cell(r.group, token="muted"), cell(r.label),
                 cell(_level(r)),
+                ft.DataCell(ft.Text(r.last_date + (f" (-{r.lag_bdays}d)" if r.lag_bdays else ""), size=11,
+                                    color=pal.warning if r.lag_bdays else pal.text,
+                                    tooltip=f"fetched {r.fetched_at_utc or 'n/a'}")),
                 cell(_chg(r, r.chg_1d), token=sign_token(r.chg_1d)),
                 cell(_chg(r, r.chg_1w), token=sign_token(r.chg_1w)),
                 cell(_chg(r, r.chg_1m), token=sign_token(r.chg_1m)),
@@ -122,7 +125,7 @@
             ]))
         dt = ft.DataTable(
             columns=[ft.DataColumn(ft.Text(c, size=11, color=pal.muted),
-                                   numeric=i >= 2 and c != "Source")
+                                   numeric=i >= 2 and c not in ("Source", "Obs date"))
                      for i, c in enumerate(_COLUMNS)],
             rows=rows, column_spacing=16, heading_row_height=34, data_row_max_height=32)
         return ft.Row([dt], scroll=ft.ScrollMode.AUTO)
@@ -158,7 +161,10 @@
         elif sheet.note:
             blocks.append(notice(sheet.note, "muted"))
         rg = sheet.regime
-        blocks.append(ft.Row([chip(f"as of {sheet.as_of}")]
+        span = (f"latest obs {sheet.as_of}" if sheet.oldest_date in ("", sheet.as_of)
+                else f"obs {sheet.oldest_date} → {sheet.as_of}")
+        blocks.append(ft.Row([chip(span, "warning" if sheet.lagging else "muted",
+                                   tooltip=", ".join(f"{i} {d}" for i, d in sheet.lagging))]
                              + [chip(f"{src}: {n}", "error" if src == "SYNTHETIC" else "success")
                                 for src, n in sheet.sources.items()], spacing=6, wrap=True))
         blocks.append(read_row(rg))
```

### 7.3 회귀 테스트 (제안. 저장소에는 넣지 않음)

전문: `regression_d04_d05.py`(아래 경로). 권장 위치: D-04 테스트 3개는 `tests/ficc_acceptance.py`, D-05 테스트 6개는 `tests/engine_acceptance.py`, PIT 테스트 1개는 `tests/macro_m1_pit.py`.

| 테스트 이름 | 핵심 단언 |
|---|---|
| `test_d04_macro_rows_keep_their_own_dates_and_the_sheet_names_the_lag` | `sheet.as_of == "2026-10-23" and sheet.oldest_date == "2026-10-16"`; `dict(sheet.lagging)["DEXKOUS"] == "2026-10-16"`; `sheet.row("DEXKOUS").lag_bdays == 5`; `sheet.row("ZN=F").lag_bdays == 0`; 모든 행 `fetched_at_utc.endswith("Z")` |
| `test_d04_daily_brief_and_narrative_carry_the_span` | `brief["oldest_date"] == "2026-10-16"`; `["DEXKOUS", "2026-10-16"] in brief["lagging"]`; 서술문에 `"between 2026-10-16 and 2026-10-23"`; 프롬프트에 `"lagging"` |
| `test_d04_macro_page_shows_an_obs_date_column` | `"Obs date" in ui.macro_page._COLUMNS` |
| `test_d05_kis_quote_as_of_is_the_exchange_book_time_not_the_receipt` | `q.as_of == "2026-10-27T01:59:58+00:00" and q.fetched_at == "2026-10-27T02:00:00+00:00"` |
| `test_d05_suspended_or_unstamped_kis_quote_has_no_as_of_and_the_feed_refuses_it` | 두 경우 모두 `q.as_of == ""`, `feed.fetch("005930", "KRX") is None`, `"timestamp" in feed.last_error("005930")` |
| `test_d05_pre_open_book_time_is_dated_to_the_previous_weekday` | 월 08:00 KST에 `_kst_stamp("153000", ...) == 2026-10-23 06:30Z`; 빈 값·잘못된 값은 `None` |
| `test_d05_krx_fallback_row_is_stamped_at_its_session_close` | `row["as_of"] == "2026-10-23T06:30:00+00:00" and row["fetched_at"]` |
| `test_d05_kis_index_reads_the_official_change_pct_field_and_no_receipt_as_of` | `ix["change_pct"] == -0.46 and ix["as_of"] == "" and ix["fetched_at"]` |
| `test_d05_simulated_order_records_the_triggering_quote_time` | `d.outcome is Outcome.FIRED and book.all()[0].as_of == stamp` |
| `test_d05_pit_ingest_of_a_quote_snapshot_without_exchange_time_is_inferred_from_retrieval` | 시각 없음 → `"inferred_from_retrieval"`, `obs_utc == 06:45Z`; `quote_times` 있음 → `"published"`, `obs_utc == 06:30Z`, `retrieved_at_utc == 06:45Z` |

## 8. 재현 스크립트 경로

모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d04_d05_timestamps/` 아래에 있다. 저장소 밖이다. 각 스크립트 옆에 같은 이름의 `.log`가 있다.

| 파일 | 내용 |
|---|---|
| `_harness.py` | 네트워크 차단, 키 제거, FICC 캐시 TTL 0 |
| `r1_d04_asof_hides_lag.py` | D04-01, D04-02 (실데이터 18행, as_of 최대값, 행별 지연, 필드 부재, 서술문·프롬프트) |
| `r2_d05_kis_asof.py` | D05-01, D05-02, D05-05, D05-06 (수신 시각, 읽는 키, 지수 필드, 엔진 가드, KRX 대체, KISMarkets) |
| `r3_pit_fields.py` | D04-03, D05-03 (PIT 세 시각 분리, 스냅숏 수신 시각 찍기, lag_audit 무검출) |
| `r4_d05_engine_e2e.py` | D05-01, D05-04 (거래정지 종목 FIRED, 주문 as_of None, 거래소 시각이면 SKIPPED) |
| `r5_patched_e2e.py` | 패치 사본에서 같은 시나리오 (HALTED / SKIPPED / FIRED + 주문 시각) |
| `regression_d04_d05.py` | 제안 회귀 테스트 10개 |
| `run_subset.py` | 사본 하나에 대해 관련 테스트 묶음 실행(`python3 -B run_subset.py <사본 경로> [--only-audit]`) |
| `proposed_d04_d05.diff` | 적용용 diff(CRLF 보존). `proposed_d04_d05.clean.diff`는 읽기용 |
| `subset_orig.log`, `subset_tree.log` | 원본·패치 사본 테스트 결과 |
| `orig/`, `tree/` | `git archive HEAD` 사본(원본, 패치본). `docs/asset_expansion/cache` 제외 |
