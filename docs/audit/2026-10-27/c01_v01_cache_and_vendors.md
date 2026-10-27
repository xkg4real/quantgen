# C-01 · V-01 감사 보고서: 캐시 재검증과 공급자 간 교차 비교

- 감사일: 2026-10-27
- 감사 차원: `c01_v01_cache_and_vendors`. 요청서 4장 C-01과 V-01, 7장 3번(캐시 만료·무효화), 6장 소유자 메모 두 줄.
- 성격: 감사 전용. 저장소의 추적 파일은 하나도 고치지 않았다. 이 보고서 파일만 새로 만들었다. 수정안은 부록 A의 diff로만 제시한다.
- 비밀정보: `.env`를 열지 않았다. 재현 스크립트는 `dotenv`를 빈 모듈로 바꿔서 `config`를 import해도 `.env`를 읽지 않는다. 키·토큰을 출력하지 않았다. KIS 재현은 가짜 키(`DUMMY_KEY_A`)와 가짜 HTTP 세션만 썼다.
- 네트워크: 시장 데이터 공급자에 접속하지 않았다. 재현 스크립트는 소켓 연결을 막는다. 문서 조회 중 `fred.stlouisfed.org`, `apiportal.koreainvestment.com`, `algolab.co.kr`는 이 환경에서 DNS 실패(ENOTFOUND)로 막혔다. GitHub 코드 검색과 웹 검색은 됐다.
- 금지 파일: `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`는 열지도, 읽지도, 해시하지도 않았다. 이 중 `yf_SPY.csv`를 읽는 `tests/macro_m8_pipeline.py::test_dry_run_end_to_end_on_the_local_cache`는 실행하지 않았다. dry run 재현은 임시 폴더의 합성 CSV로 했다. `DRY_RUN_CACHE`도 합성 파일 이름으로 바꿨다.
- 테스트: `tests/run_all.py`는 실행하지 않았다. 관련 기존 테스트 63건은 스크립트에서 함수 단위로 불렀다. 원본 63/63 PASS, 패치 트리 70/70 PASS(새 테스트 7건 포함).

## 0. 요약

1. C-01의 "손상된 캐시 재사용" 주장은 **사실**이다. 디스크 캐시 두 곳(`core/quant/history.py::_cached`, `core/ficc/data.py::_cache_get`)은 JSON 파싱만 되면 내용을 검사하지 않는다. NaN, ±inf, 0 이하 가격, 역순·중복 날짜, 1행·0행 파일이 모두 그대로 나간다(재현 R1, R2). 쓰기 경로는 행 수 하한과 정렬을 지킨다. 읽기 경로는 이를 다시 확인하지 않는다.
2. "오래된 캐시 재사용"은 **부분 사실**이다. 두 시계열 캐시는 TTL(기본 6시간, 장중 10분)을 정확히 지킨다. 미래 시각 파일도 거부한다(R3c). 그러나 두 곳이 다르다.
   - Macro dry run은 공급사 CSV의 수신 시각을 파일 mtime으로 정한다. clone이나 복사 한 번에 결과가 바뀐다(R5: US `vt_status` ok → fail_closed). 장중 봉이 종가로 바뀌기도 한다(R5b). 원 기준선의 I-01 FAIL 원인이 이것이다.
   - KIS 토큰 캐시는 앱 키·도메인과 묶이지 않는다. 서버가 거절해도 지우지 않는다(R4).
3. 시장 데이터 캐시 어디에도 스키마 버전, 무결성 해시, 원자적 쓰기가 없다. md5 검증이 있는 곳은 서명 캘린더 저장소(`core/calendars/store.py`) 하나뿐이다.
4. V-01의 "공급자 간 일치도를 아직 비교하지 않았다"는 **사실**이다. 교차 공급자 비교 코드는 없다. 있는 것은 PIT 저장소의 공식 대 공급사 종가 대조(`core/ficc/pit.py:611` `reconcile`)뿐이다.
5. 코드에 있는 공급자로 비교 쌍 16개를 만들 수 있다(6장). 하네스 `tools/vendor_compare.py`를 설계했다. 스크래치 트리에서 합성 데이터로 검증했다(셀프테스트 11/11 PASS). 실제 수집은 소유자 PC에서 해야 한다. 이 클라우드는 공급자 접속이 막혀 있다.
6. 이미 화면에 나가는 교차 공급자 계산 하나에서 결함을 재현했다(V01-01, P2). Crypto 화면의 김치 프리미엄은 FRED DEXKOUS(주 1회 공표)를 나이 제한 없이 앞으로 채운다. 합성 경로에서 참값 +2.00%가 +0.52%로 나왔다. 쓰인 FX는 10일 묵은 값이었다. 결과 note는 "a few hours of FX drift"라고 쓴다.
7. 소유자 메모 두 줄에 대한 답(7장). KIS는 원화 금리, 국고채, KRX 금리·통화 선물, 미국 10·30년 금리, 원/달러 고시, CME BTC 선물 일봉을 준다(코드 근거, 실제 응답은 미검증). BTC 현물, 미국 국채 전 구간, SOFR, 신용 스프레드는 KIS에 없다. 이미 구현된 FRED, Upbit, Binance가 맞는 대안이다. 한국 공식 거시 지표(기준금리, 콜금리, CD91, 15:30 환율, CPI)는 레지스트리가 ECOS·KOSIS를 요구한다. 그런데 클라이언트가 없다(V01-03). "공급사필요"의 실체가 이것이다.
8. 제안 패치(부록 A, 10개 파일)를 스크래치 트리에 적용해 검증했다. 새 회귀 테스트 7건은 원본 코드에서 7건 모두 FAIL, 패치 트리에서 7건 모두 PASS다. 기존 관련 테스트 63건은 패치 뒤에도 PASS다. diff는 HEAD(`527cdf2`)에 `git apply --check`로 적용된다.

## 1. 범위

- C-01: `core/ficc/data.py`의 FICC 캐시, `core/quant/history.py`의 가격 이력 캐시, `data/*`의 캐시(KIS 토큰, OpenDART 기업코드, FMP 시세, KIS 마스터 파일), `docs/asset_expansion/cache` 사용처(연구 스크립트, Macro dry run), `config.py`의 `~/.nextgen` 경로, 프로세스 메모리 캐시(`lru_cache`, 캘린더).
- 점검 항목: 캐시 키, TTL, stale 처리, 스키마 버전, 무결성 검사(md5·크기·파싱), 손상 처리, 무효화.
- V-01: 같은 자산·같은 기간의 공급자 간 비교 하네스 설계. 시간대·통화·단위·수정주가 기준 정렬. 지표. 코드에 있는 공급자 쌍. 실행 위치.
- 소유자 메모: "(-> 공급사필요)", "(-> FICC/BTC 모두 KIS에서 접근 가능한지…)". 코드 근거로 답하고 구현은 제안만 한다.
- 제외: `paper_live/`, `grokteam/`(실행·수정 안 함). `grokteam`의 sha 검사 캐시와 `tools/paper`의 번들 캐시는 범위 밖이다.
- 다른 차원과 겹치는 부분은 번호로 참조한다. D-01/D-02(`_clean_rows`), D-03(합성 대체; D03-01 Crypto FX 합성, D03-06 단위, D03-07 오래된 캐시 대 합성), D-04/D-05(시각 필드).

## 2. 방법

1. `cache`, `ttl`, `json.load`, `write_text`, `.nextgen`, `lru_cache`, `st_mtime`를 grep 했다. 캐시마다 키·TTL·만료·손상 처리 코드를 줄 단위로 읽었다.
2. 스크래치 폴더에서 작은 스크립트로 재현했다. 공통 전처리 `_guard.py`가 dotenv 스텁, 소켓 차단, 임시 HOME·캐시·macro 폴더, 키 환경변수 제거를 한다.
3. 각 의심 경로는 임시 폴더에 캐시 파일을 직접 써서 재현했다. 같은 스크립트를 원본과 패치 트리에서 돌려 전후를 비교했다(`AUDIT_TREE=1`).
4. 패치는 스크래치 트리(저장소 일부 복사본)에만 적용했다. 기존 관련 테스트 63건과 새 테스트 7건을 양쪽에서 돌렸다.
5. 판정 기준. 재현했으면 **사실**. 코드로만 확인했고 외부 동작에 달렸으면 **추정**. 주장과 코드가 다르면 **오류**. 확인하지 못하면 **미검증**.

## 3. 요청서·코드 주장 검증

| # | 주장 | 출처 | 판정 | 근거 |
|---|---|---|---|---|
| 1 | 캐시 읽기 경로의 품질 재검증 정도는 추적이 필요하다. 손상된 캐시가 재사용될 수 있다 | 요청서 C-01 | 사실 | `core/quant/history.py:430-436`, `core/ficc/data.py:251-265`. R1, R2 |
| 2 | 오래된 캐시가 재사용될 수 있다 | 요청서 C-01 | 부분 사실 | 시계열 TTL은 지킨다(`history.py:424-436`, `data.py:248-265`, R3c). 예외: dry run mtime(`core/skills/macro_daily.py:1412`, R5, R5b), KIS 토큰(`data/krx/kis_client.py:146-155`, R4) |
| 3 | TTL, stale-while-revalidate, 캐시 키, 스키마 버전, 유효성 검사, 무효화 테스트가 필요하다 | 요청서 C-01 조치 | 사실(필요함) | 스키마 버전 없음. stale 정책 없음. 손상 캐시 테스트 없음(`tests/`에 해당 테스트 0건) |
| 4 | 같은 자산의 공급자 간 일치도를 아직 비교하지 않았다 | 요청서 V-01 | 사실 | 교차 비교 모듈 없음. `core/ficc/pit.py:611`은 한 시리즈의 공식·공급사 종가만 대조 |
| 5 | "Seconds a fetched series stays valid in the FICC cache. 0 disables caching." | `config.py:272-274` | 사실 | `data.py:248-250, 269-270`, `history.py:424-426`. 기존 테스트 PASS |
| 6 | "keyed by provider/id/days. Synthetic results are never cached. Cache failures are ignored, never raised." | `core/ficc/data.py:26-28` | 사실 | `data.py:220-221, 268-279`. `ficc/test_data_synthetic_never_touches_the_cache` PASS |
| 7 | "A hit says so: note gains 'cached <fetch time>'" | `core/quant/history.py:409-410` | 사실(부분) | `history.py:437-438`. 시각에 시간대 표기가 없다. FICC 캐시 적중은 아무 표시가 없다(R2: 새 수신과 적중 결과가 `==`로 같음) |
| 8 | "Failures are never stored, and neither is a series too short to be a real history." | `core/quant/history.py:418-419` | 사실(쓰기만) | `history.py:449`. 읽기에서는 1행·0행 파일도 나간다(R1) |
| 9 | "fetches are cached on disk for a few hours" | `ui/settings_page.py:206` | 부분 오류 | FRED는 6시간. Yahoo 시계열은 이력 캐시에서 평일 내내 10분(R3d: 주 168시간 중 123시간) |
| 10 | "A cold start reuses a still-valid token… The cache file holds a token, never the appkey/appsecret." | `data/krx/kis_client.py:20-24` | 사실(부분) | 키 원문은 저장하지 않는다(사실). "still-valid"는 로컬 만료 시각만 본다. 키 교체, 도메인 변경, 서버 거절을 반영하지 않는다(R4) |
| 11 | "the file's real retrieval instant (L1283)" | `core/skills/macro_daily.py:1412` 주석 | 오류 | mtime은 clone·복사·압축 해제로 바뀐다. 원 기준선에서 I-01 FAIL. mtime을 2026-10-01로 되돌린 baseline2에서 PASS. R5, R5b |
| 12 | "manifest.json: md5 of results.csv, data spans, run date" | `docs/asset_expansion_study.py:10` | 오류(부분) | 실제 키는 `cards, decisions, quick, rescored, results_md5, run, seed`. data spans와 입력 해시가 없다(R6c) |
| 13 | "USD/KRW forward-filled by date (… a few hours of FX drift)" | `core/crypto/analytics.py:106-107` | 오류 | DEXKOUS는 주간 공표다(레지스트리 `schedule: H10`, `data/macro/series_registry.yaml:19, 141-157`). 마지막 주는 최대 약 10일 묵은 FX를 쓴다(R7) |
| 14 | KIS가 CBOE VX, ICE DX, CME BTC 일봉을 준다. CME ES/NQ/ZN 등은 주식 계좌 키로 HTTP 500 | `data/kis_markets.py:12-15, 514-517` | 미검증 | "PROBED LIVE 2026-09-25"라고 적혀 있다. 이 환경에서는 KIS에 접속할 수 없다 |

## 4. 캐시 지도 (C-01)

### 4.1 디스크 캐시

| # | 캐시 | 저장 위치 | 키 | TTL·만료 | stale 처리 | 스키마 버전 | 무결성 검사 | 손상 처리 | 무효화 | 관련 테스트 |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | FICC 시계열 (`core/ficc/data.py:214-279`) | 메모리 `_MEM`(`:216`) + `config.ficc_cache_dir()`(`config.py:277-279`; 기본 `~/.nextgen/ficc_cache`, `NEXTGEN_FICC_CACHE`) 아래 `{PROVIDER}_{id}_{days}.json` | `_cache_key`(`:220-221`): 영숫자·`_.-` 외 문자는 `_`. 조정 기준·엔드포인트 버전은 키에 없음 | `FICC_CACHE_TTL_SECONDS` 기본 6시간(`config.py:274`). 마지막 행이 기록 UTC 날짜 이상이면 10분(`_running_bar` `:224-230`). PIT 경로는 `not_before`(종가+10분) 이전 파일 거부(`:259`). 미래 시각 거부(`:262`) | 만료 시 재요청. 실패하면 `auto`는 SYNTHETIC, 명시 공급자는 `FICCError`(`:539-543`; D03-07) | 없음(`{"ts","rows"}`) | 없음. JSON 파싱만 | 파싱 실패는 miss. 파싱되는 손상은 그대로 서빙(C01-02) | TTL, 파일 삭제, TTL 0 | T-PROV-01, `ficc/test_data_synthetic_never_touches_the_cache` |
| D2 | 가격 이력 (`core/quant/history.py:353-458`) | D1과 같은 폴더, `HIST_{PROVIDER}_{SYMBOL}_{days}.json` | 같은 정규식, 기호는 대문자 | 쓸 때 장중이면(`_may_be_trading` `:363-387`) 10분, 아니면 6시간이되 그 뒤 장이 열렸으면 만료(`_traded_since` `:390-399`). `live` 플래그 없는 구 파일은 10분 | 만료 시 재요청. 실패하면 `HistoryError`(stale 사용 없음, C01-06). 키가 없는 공급자는 캐시를 건너뛰고 바로 예외(`:425`) | 암묵적(`live` 플래그 유무) | `len(dates) == len(closes)`만(`:436`) | 파싱 실패는 miss. 파싱되는 손상은 그대로 서빙(C01-01) | TTL, `_traded_since`, 파일 삭제(문서 `:420-421`) | `quant/test_history_cache_serves_a_rerun…`, `quant/test_the_cache_knows_when_a_market_may_be_trading`, T-PROV-01 b |
| D3 | KIS 접근 토큰 (`data/krx/kis_client.py:53, 146-195`) | `~/.nextgen/kis_token.json`. `Path.home()` 고정, 환경변수로 바꿀 수 없음 | 없음(파일 하나) | 서버 `expires_in`(기본 86400초) − 120초 | 없음 | 없음 | 없음 | 파싱 실패면 새 토큰 | 없음. 서버 거절에도 유지(C01-04) | 없음 |
| D4 | OpenDART 기업코드 (`data/krx/opendart_client.py:44-46, 94-149`) | `~/.nextgen/dart_corp_codes.json`. 고정 경로 | 없음 | 7일(`:45`) | 만료 시 재요청 | 없음 | `entries`가 dict인지만 | 파싱 실패면 재요청 | `corp_codes(refresh=True)` | 확인 못 함 |
| D5 | 연구용 CSV (`docs/asset_expansion_study.py:68-136`) | `docs/asset_expansion/cache/*.csv`(git 추적 46개) | 파일명(`yf_`, `fred_`, `upbit_`, `binance_`) | 없음. `--refresh`만 | 해당 없음 | 없음 | 없음. manifest에 입력 해시 없음 | `read_csv` 실패는 예외 | `--refresh`, 파일 삭제 | 간접(D-01/D-02 R4 스캔) |
| D6 | Macro dry run 입력 (`core/skills/macro_daily.py:69, 86-90, 1395-1433`) | D5 중 6개 파일 | `DRY_RUN_CACHE` | 없음 | 해당 없음 | 없음 | 없음 | 파싱 실패 행은 건너뜀(`:1381-1392`) | 실행마다 `dry_run/pit` 재구성(`:1402`) | I-01(금지 파일을 읽어 이번 감사에서 미실행) |
| D7 | PIT 저장소 (`core/ficc/pit.py:217-316`) | `config.macro_dir()`(기본 `~/.nextgen/macro`) | 시리즈별 JSONL | 캐시 아님(추가 전용 저장소) | 해당 없음 | 행 필드 고정 | 쓸 때 `content_hash` 검사(`:288-289`). 읽을 때 재검사 없음 | 손상 줄은 `PITError`로 실패(`:263-264`) | 행 수정 금지, 정정은 새 행 | M1 PIT 테스트군 |

### 4.2 메모리 캐시

| # | 캐시 | 수명·TTL | 무효화 | 비고 |
|---|---|---|---|---|
| M1 | FMP 시세 `FMPQuoteClient._cache` (`data/fmp/quote_client.py:123, 212-220`) | `FMP_MIN_INTERVAL_SECONDS` 20초(`config.py:68`) | 시간 경과 | 시세 최대 나이 120초(`config.py:182`)보다 짧다. `engine/test_50_fmp_cache_window_cannot_outlast_the_staleness_guard` PASS |
| M2 | KIS 마스터 파일 `_MASTER_CACHE` (`data/kis_markets.py:653-670`) | 프로세스 수명, TTL 없음 | 재시작 | 긴 세션에서 신규 상장·만기 반영 안 됨(추정, C01-08) |
| M3 | 생성 캘린더 `_CACHE` (`core/calendars/__init__.py:88-120`) | 프로세스 수명 | 재시작 | 정적 파일. KRX·US 범위 2026-01-01~2027-12-31(`data/calendars/KRX.json`, `US.json`) |
| M4 | 서명 캘린더 `_DEFAULT` (`core/calendars/store.py:331-345`) | 프로세스 수명 | `reload()` | 유일하게 md5 검증이 있는 저장소(`:113-142`) |
| M5 | `lru_cache`: 규칙 저장소(`core/ficc/context_log.py:786`, `core/quant/risk_layer.py:187`), 스키마 레지스트리(`core/ficc/macro_schema.py:241`), GARCH 표(`core/quant/garch.py:622`) | 프로세스 수명 | 재시작 | 저장소에 포함된 정적 데이터. 시장 데이터 아님 |
| M6 | FICC `_MEM` (`core/ficc/data.py:216`) | 항목마다 D1 TTL로 판정 | 만료 항목도 지우지 않음 | 상한 없음(C01-08) |

### 4.3 `~/.nextgen` 경로

| 경로 | 정의 | 환경변수 재지정 | 용도 |
|---|---|---|---|
| `~/.nextgen/ficc_cache` | `config.py:277-279` | `NEXTGEN_FICC_CACHE` | D1, D2 |
| `~/.nextgen/macro` | `config.py:176-178` | `QUANTGEN_MACRO_DIR` | PIT 저장소, 산출물, 경보, dry run |
| `~/.nextgen/trading` | `config.py:169-171` | `NEXTGEN_TRADING_DIR` | 규칙·엔진 상태(캐시 아님) |
| `~/.nextgen/kis_token.json` | `data/krx/kis_client.py:53` | 불가 | D3 |
| `~/.nextgen/dart_corp_codes.json` | `data/krx/opendart_client.py:44` | 불가 | D4 |

같은 Yahoo 티커가 D1(`YFINANCE_^VIX_756`)과 D2(`HIST_YFINANCE_^VIX_504`)에 따로 저장된다. 신선도 규칙도 다르다(`_running_bar` 대 `_may_be_trading`). 그래서 화면마다 마지막 봉이 최대 10분 다를 수 있다(추정, 재현 안 함).

## 5. 발견사항

### 5.1 요약 표

| ID | 심각도 | 판정 | 파일·라인 | 한 줄 요약 |
|---|---|---|---|---|
| C01-01 | P2 | 사실 | `core/quant/history.py:402-458` | 가격 이력 캐시가 파싱되는 손상 파일(NaN, inf, 0 이하, 역순, 중복, 0~1행, 다른 기호)을 그대로 쓴다 |
| C01-02 | P2 | 사실 | `core/ficc/data.py:233-279, 466, 571-596` | FICC 캐시도 같다. 5행 하한·정렬이 적중에서 빠진다. inf가 국채 곡선까지 간다 |
| C01-03 | P2 | 사실 | `core/skills/macro_daily.py:1412` | dry run이 파일 mtime을 수신 시각으로 쓴다. 복사 한 번에 결과·종가 판정이 바뀐다 |
| C01-04 | P2 | 사실 | `data/krx/kis_client.py:53, 146-166, 216-245` | KIS 토큰이 키·도메인과 묶이지 않고, 서버가 거절해도 남는다 |
| V01-01 | P2 | 사실 | `core/crypto/analytics.py:69-107`, `ui/crypto_page.py:52, 63` | 김치 프리미엄이 최대 약 10일 묵은 FRED 환율로 계산되고, note는 "몇 시간"이라고 한다 |
| V01-02 | P2 | 사실 | (부재) `core/ficc/pit.py:611` | 공급자 간 교차 비교 수단이 없다 |
| V01-03 | P2 | 사실 | `data/macro/series_registry.yaml:310-424` | 레지스트리가 요구하는 ECOS·KOSIS 클라이언트가 없다(소유자 메모 "공급사필요") |
| C01-05 | P3 | 사실 | `core/ficc/data.py:77-84, 498-503`, `core/quant/history.py:437` | FICC 시계열에 수신 시각이 없다. 이력 캐시 표시는 시간대가 없다 |
| C01-06 | P3 | 사실 | `core/quant/history.py:424-445`, `core/ficc/data.py:539-543` | stale 정책이 없다. 실패하면 이력은 예외, FICC는 합성 |
| C01-07 | P3 | 사실(성능 영향은 미계측) | `core/quant/history.py:363-387` | Yahoo·KIS 비주식 이력은 평일 내내 10분 캐시다 |
| C01-08 | P3 | 사실 | `data.py:216, 220, 276`, `history.py:452`, `kis_markets.py:653` | 스키마 버전, 원자적 쓰기, 메모리 상한이 없다 |
| C01-09 | P3 | 사실 | `docs/asset_expansion_study.py:68-136, 813` | 연구용 CSV 캐시: 입력 해시 없음, 항상 참인 조건식, 0 이하 행 무경고 삭제 |

P0·P1은 없다. 실행(acting) 경로는 PIT 저장소를 거치고, 합성·자동 대체 값을 거부한다(`core/ficc/pit.py:393-409`). 이번에 찾은 결함은 표시·연구·재현성 경로에 있다.

### 5.2 상세

#### C01-01 · P2 · 사실 — 가격 이력 캐시는 파싱되는 손상 파일을 그대로 쓴다

| 항목 | 내용 |
|---|---|
| ID | C01-01 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/history.py` `_cached` `:402-458`. 읽기 `:430`(검사 없는 `json.loads`), `:436`(검사는 `len(dates) == len(closes)` 하나), `:439-442`(파일의 `symbol`, `source`를 그대로 씀). 쓰기 `:449-455`(`json.dumps` 기본값 `allow_nan=True`, 비원자적 `write_text`) |
| 재현 단계 | `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r01_history_cache_corrupt.py`. 임시 캐시 폴더에 `HIST_FMP_<SYM>_30.json` 11종을 쓰고 `_cached`를 부른다. fetch 함수는 불리면 `REFETCH`를 던진다 |
| 기대 결과 | 손상 파일은 miss로 보고 다시 받는다. 쓰기 경로의 약속(30행 이상, 실패와 짧은 시계열은 저장 안 함)이 읽기에서도 지켜진다 |
| 실제 결과 | 11종 모두 SERVED. NaN·inf 종가는 `log_returns`를 비유한으로 만든다. 0·음수는 log에서 -inf/NaN. 역순·중복 날짜는 그대로. 1행 파일은 길이 1 History. 0행 파일은 `.last`에서 IndexError. 파일 이름은 `HIST_FMP_SYMBOL_AND_…`인데 내용의 `symbol=MSFT`, `source=KIS`가 그대로 나간다. inf는 비표준 JSON 토큰 `Infinity`로 저장된다 |
| 영향 | 손상·수기 편집·구버전 파일 하나가 TTL(최대 6시간) 동안 수익률·변동성·최적화 입력이 된다. D-01의 inf는 fetch 단계에서 걸러지지 않는다(`_clean_rows` `:97-102`). 그래서 inf가 캐시에 써지고 6시간 재사용된다. 0행 파일은 화면 작업 스레드에서 예외를 낸다 |
| 수정안 | 부록 A의 `core/quant/history.py`. 읽기·쓰기 공통 게이트 `_valid_cached`: 스키마 버전(`v` ≤ 2), 파일 키 일치(`key`), ISO 날짜 엄격 오름차순, 종가 유한·양수, 30행 이상. `parse_constant`로 `NaN`/`Infinity` 토큰 거부. 쓰기는 `allow_nan=False`, 임시 파일 후 `os.replace`. D-01/D-02 제안의 `_well_formed`와 목적이 같다. 둘 다 채택하면 하나로 합친다. 잔여: `key` 필드가 없는 v1 파일은 기호 불일치를 못 잡는다(R1 after: `symbol_and_source_mismatch` SERVED). 배포 뒤 최대 TTL(6시간)만 남는다 |
| 회귀 테스트 | `tests/cache_vendor_acceptance.py::test_c01_history_cache_refuses_corrupt_payloads`: 손상 10종마다 `len(calls) == n + 1`(재요청), 결과 종가는 모두 유한·양수, 날짜는 정렬·유일. 유효한 v1 파일은 `"cached" in note`이고 재요청 없음. `test_c01_history_cache_never_persists_non_finite_and_writes_atomically`: inf 종가 시계열은 파일이 생기지 않음, 저장 파일은 `p["v"] == 2`, `p["key"] == "HIST_FMP_OK_30"`, `*.tmp` 잔여 없음 |

#### C01-02 · P2 · 사실 — FICC 캐시도 같다. 쓰기 규칙이 적중에서 빠진다

| 항목 | 내용 |
|---|---|
| ID | C01-02 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/data.py` `_cache_get` `:233-265`(`:254-255` 검사 없는 파싱), `_provider_rows` `:466`(`if hit:`만 확인), `:486-487`(새 수신에만 `sorted`와 `_MIN_OBS`), `_cache_put` `:268-279`, `_treasury_from_fred` `:571-596`, `CurvePanel.yields` 주석 `:132`("NaN-free") |
| 재현 단계 | `python3 -B …/r02_ficc_cache_corrupt.py`. 공급자 함수는 예외를 던지게 바꾼다. `source="fred"`를 명시한다. 거부되면 `FICCError`가 나야 한다 |
| 기대 결과 | 손상 파일은 miss. 명시 공급자면 `FICCError`. 곡선 패널은 유한값만 |
| 실제 결과 | NaN, inf, 2행(`_MIN_OBS`=5 미만), 역순, 중복 모두 `source=FRED`로 나갔다. 같은 2행을 새로 받으면 거부된다(`FICCError`). 중복 케이스는 마지막 값이 2026-08-01 날짜의 99.0이다. 즉 `Series.last`가 옛 날짜 값이다. 국채 곡선에서는 DGS2의 inf가 패널까지 갔다(`any_inf=True`). DGS10의 NaN은 직전 값으로 조용히 채워졌다(note 없음) |
| 영향 | 금리·FX·매크로 화면이 손상 파일 하나로 비유한 값을 계산한다. 곡선 모델 피팅과 DV01에 inf가 들어간다. "NaN-free" 계약이 깨진다 |
| 수정안 | 부록 A의 `core/ficc/data.py`. `_rows_ok`(ISO 날짜 엄격 오름차순, 유한값) 읽기·쓰기 게이트. `_provider_rows`에서 적중에도 `_MIN_OBS` 적용(3행 PIT 픽스처를 깨지 않도록 `_cache_get`이 아니라 여기서). `v`/`key` 스키마. 원자적 쓰기, 이름 바꾸기 실패 시 임시 파일 삭제 |
| 회귀 테스트 | `test_c01_ficc_cache_refuses_corrupt_payloads_and_states_retrieved_at`: 손상 5종마다 `load_series(…, source="fred")`가 `FICCError`. 유효 파일은 `s.retrieved_at ==` 파일 `ts`의 UTC ISO. 기존 `test_prov_01_cache_regression_replays_the_incident` PASS 유지 |

#### C01-03 · P2 · 사실 — dry run이 파일 mtime을 수신 시각으로 쓴다

| 항목 | 내용 |
|---|---|
| ID | C01-03 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/skills/macro_daily.py` `dry_run` `:1395-1433`, 핵심은 `:1412`. 호출 지점 `ui/macro_state_panel.py:730`(UI 버튼), `tests/macro_m8_pipeline.py:849`. 캐시 폴더 `:69`, 파일 목록 `:86-90` |
| 재현 단계 | (1) `python3 -B …/r05_mtime_provenance.py`: 합성 CSV 6개, `DRY_RUN_CACHE`를 합성 파일로 재지정, 실행 시계 2026-10-07 09:00Z, mtime만 바꿔 두 번 실행. (2) `python3 -B …/r05b_mtime_hides_running_bar.py`: 같은 행을 `P.ingest`에 두 수신 시각으로 넣음(dry run과 같은 호출, 같은 시계) |
| 기대 결과 | 같은 바이트는 같은 결과. 수신 시각은 수집할 때 기록한 값 |
| 실제 결과 | (1) mtime 2026-10-06 22:00Z → US `vt_status=ok`, `vt_weight_next=0.904`. mtime=지금 → `vt_status=fail_closed`, 0.0, 입력 0개. (2) 01:56Z(장중) 수신이면 2026-10-02 행은 `provisional_intraday`. 같은 파일을 나중에 복사하면(mtime 2026-10-27) `vendor_close`. (3) 원 기준선 실행에서 `test_dry_run_end_to_end_on_the_local_cache`가 `tests/macro_m8_pipeline.py:871`에서 FAIL. mtime을 2026-10-01로 되돌린 baseline2에서 PASS |
| 영향 | 새 clone, ZIP 해제, Windows 복사 뒤 dry run 결과와 I-01 테스트가 달라진다(재현성 결함). TASK-M1-12가 막은 "장중 봉이 종가로 둔갑"이 파일 복사로 다시 생긴다. 결과는 DISARMED·backtest 라벨이므로 실행 경로 영향은 없다 |
| 수정안 | 부록 A. 다운로드 때 `cache/RETRIEVAL.json`(`{파일: {retrieved_at_utc, sha256}}`)을 기록(`docs/asset_expansion_study.py::_record_retrieval`). dry run은 sha256이 맞는 항목만 믿는다. 항목이 없으면 mtime을 쓰되 최신 행을 빼고 `retrieved_at_source: "mtime"`으로 표시. 기존 46개 파일의 실제 수신 시각은 소유자만 안다(미검증). 소유자가 `RETRIEVAL.json`을 채우거나 다시 받아야 I-01이 mtime과 무관해진다 |
| 회귀 테스트 | `test_c01_dry_run_reads_retrieval_from_the_manifest_not_the_mtime`: 매니페스트가 있으면 mtime 두 값에서 `ingested`가 같고 `retrieved_at_source == "manifest"`. 없으면 `"mtime"`이고 `appended`가 1 적다. R5 after: 매니페스트 고정 시 mtime=지금이어도 `vt_status=ok`, 0.904 |

#### C01-04 · P2 · 사실 — KIS 토큰 캐시가 키·도메인과 묶이지 않고, 거절돼도 남는다

| 항목 | 내용 |
|---|---|
| ID | C01-04 |
| 심각도 | P2 |
| 판정 | 사실(코드 동작). 서버의 거절 방식은 추정 |
| 파일·함수·라인 | `data/krx/kis_client.py` `_TOKEN_PATH` `:53`(바꿀 수 없는 고정 경로), `_cached_token` `:146-155`, `_store_token` `:157-166`, `_get` `:198-245`(토큰 오류 코드 처리 없음. HTTP 200 + `rt_cd≠0`도 메시지만 올림 `:243-244`) |
| 재현 단계 | `python3 -B …/r04_kis_token_cache.py`. 가짜 키와 가짜 세션. (a) `DUMMY_KEY_A`로 받은 토큰 파일을 두고 `DUMMY_KEY_B`, 모의투자 도메인으로 `token()`. (b) 서버가 `EGW00123`으로 응답 |
| 기대 결과 | 다른 키·도메인이면 새 토큰. 서버가 토큰을 거절하면 캐시에서 지우고 새로 받는다 |
| 실제 결과 | (a) 세 경우 모두 `TOKEN_ISSUED_FOR_KEY_A`를 다시 씀. 발급 요청 0회. (b) 두 번 연속 같은 오류. 토큰 파일 그대로. 발급 0회. 파일은 기본 권한으로 써진다(umask 022면 0644) |
| 영향 | 키 교체, 실전·모의 전환, 서버측 폐기 뒤 최대 약 24시간 KIS 데이터 경로가 모두 실패한다. 사용자는 파일을 지워야 하는데 안내가 없다. 공유 PC(POSIX)에서는 bearer 토큰을 다른 계정이 읽을 수 있다. 서버가 다른 키의 토큰을 `EGW00123`으로 거절한다는 점은 추정이다. 근거: 공식 샘플 `koreainvestment/open-trading-api`의 `legacy/rest/current_price_samle.py`(EGW00123이면 재인증), 제3자 구현 `kgcrom/cluefin`의 `_token_manager.py`(키·서버별 캐시 파일, EGW00123 언급) |
| 수정안 | 부록 A의 `data/krx/kis_client.py`. 파일에 `scope = sha256(app_key|base_url)[:16]`(키 원문 아님)와 `issued_at`을 저장. 불일치면 새로 발급. `EGW00121`/`EGW00123`이면 토큰을 지운다. 단, 발급 60초 안의 토큰은 유지(발급 횟수 제한 보호). `retry=True` 경로는 새 토큰으로 1회 재시도. `retry=False`(실시간 시세)는 재시도 없이 다음 호출에서 새 토큰. 권한 0600, 원자적 교체 |
| 회귀 테스트 | `test_c01_kis_token_is_scoped_and_dropped_when_refused`: 거절된 실시간 시세 호출은 실패하지만 토큰 파일이 즉시 지워지고 `posts == []`. 다음 호출은 새 토큰으로 성공(`gets == ["Bearer OLD", "Bearer T1"]`). `_get` 재시도 경로는 `gets == ["Bearer OLD", "Bearer T2"]`. KEY_B와 모의 도메인은 각각 새 토큰. 파일에 키 원문 없음. POSIX에서 `mode & 0o077 == 0` |

#### V01-01 · P2 · 사실 — 김치 프리미엄이 최대 약 10일 묵은 환율로 계산된다

| 항목 | 내용 |
|---|---|
| ID | V01-01 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `ui/crypto_page.py` `_live` `:52`(FRED `DEXKOUS`), `analyze` `:63`. `core/crypto/analytics.py` `kimchi_premium` `:69-107`(`:76` 날짜 앞채움, 나이 제한 없음. `:106-107` note). 레지스트리 `data/macro/series_registry.yaml:19`(H10: `monday_after_week_else_next_fed_business_day`), `:141-157`(`_fred_h10`), `:349-355`(DEXKOUS `production_reads: false`) |
| 재현 단계 | `python3 -B …/r07_kimchi_fx_age.py`. 합성 BTC 400일(2026-10-26까지). FX는 2026-10-16(금)까지만. 참 프리미엄은 매일 +2.00% |
| 기대 결과 | FX가 오래되면 그 날짜를 빼거나 경고한다. note는 실제 나이를 말한다 |
| 실제 결과 | 마지막 10일 프리미엄 +2.04, +1.94, +1.98, +2.01, +2.00, +1.61, +0.98, +0.81, +0.46, +0.52%. 마지막 값은 10일 전 FX를 썼다. 결과 객체에 FX 나이 필드가 없다. note는 "a few hours of FX drift" |
| 영향 | Crypto 화면의 헤드라인(마지막 프리미엄, z-score, 예측 회귀 입력)이 그동안의 환율 변동만큼 틀린다. FX가 합성으로 바뀌는 경우(D03-01, +1257%)와는 별개 결함이다 |
| 수정안 | 부록 A. `kimchi_premium(max_fx_age_days=None)`(기본값은 연구 결과 보존), 나이 필드 3개(`fx_age_days_last`, `fx_age_days_max`, `fx_stale_dropped`), 실제 나이를 적는 note. Crypto 화면은 4일로 제한. 공급자 선택(설명형): 매일 갱신되는 환율로 바꾼다. 1순위 KIS `FX@KRW`(설정돼 있을 때), 2순위 Yahoo `KRW=X`(무키, 당일 갱신), FRED DEXKOUS는 마지막 대안. `usdkrw_source`는 이미 넘기므로 화면 칩에 함께 표시 |
| 회귀 테스트 | `test_v01_kimchi_premium_reports_and_caps_fx_age`: FX가 10일 묵으면 `fx_age_days_last == 10`이고 note에 "10 day(s) old". `max_fx_age_days=4`면 마지막 날짜 `2026-10-20`, `fx_stale_dropped == 6`, `fx_age_days_max <= 4` |

#### V01-02 · P2 · 사실 — 공급자 간 교차 비교 수단이 없다

| 항목 | 내용 |
|---|---|
| ID | V01-02 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | 부재. 유일한 대조는 `core/ficc/pit.py:362-375`(`_dispute`, 허용오차 `index_bp`)와 `:611-630`(`reconcile`, 같은 시리즈의 공식 대 공급사 종가, 공식 행이 있어야 동작). 레지스트리 `sources:` 목록(`series_registry.yaml:90, 108, 478, 497, 672-734`)은 여러 공급자를 선언만 한다. 조정 기준 차이는 `core/quant/history.py:105-118` `convention_warning`이 문장으로만 경고한다 |
| 재현 단계 | `grep -rln -i "vendor_compare\|cross_provider\|provider_compare" --include=*.py .` 결과 없음. 하네스 셀프테스트 `python3 -B …/run_harness_selftest.py` |
| 기대 결과 | 같은 자산·기간을 두 공급자에서 받아 차이를 숫자로 남긴다 |
| 실제 결과 | 수단 없음 |
| 영향 | 공급자를 바꾸면(KIS↔Yahoo, FMP↔Yahoo) 결과가 얼마나 움직이는지 모른다. 날짜 기준 하루 밀림 같은 결함을 찾을 방법이 없다 |
| 수정안 | 6장 설계, 부록 A `tools/vendor_compare.py`(fetch는 소유자 PC, compare·selftest는 어디서나) |
| 회귀 테스트 | `test_v01_vendor_compare_selftest`: 심어 둔 결함 11개(하루 밀림, 6일 누락, 50bp 튐, ×100 단위, 배당 조정 1일, sha·inf, 금리 2bp 스프레드, 금리 10bp 튐 날짜, +2% 프리미엄 등)를 모두 잡아 `selftest(...) == []` |

#### V01-03 · P2 · 사실 — 레지스트리가 요구하는 ECOS·KOSIS 클라이언트가 없다

| 항목 | 내용 |
|---|---|
| ID | V01-03 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `data/macro/series_registry.yaml` `ECOS_1530_CLOSE` `:310-329`(channel "ECOS 731Y003/0000003"), `BOK_BASE_RATE` `:356-372`, `KR_CPI` `:373-389`(source KOSIS), `BOK_CALL_RATE` `:390-407`(channel "OWNER input before the M7 freeze"), `KR_CD91` `:408-424`. 소비자: `core/quant/risk_layer.py:610-622`(`ECOS_1530_CLOSE`를 PIT에서 읽음), `core/quant/refusal.py:12, 33, 92`(없으면 REFUSAL, 배수 1.0) |
| 재현 단계 | `grep -rn -i ecos --include=*.py core data ui`: 소비 코드와 픽스처 이름만 있고 수집 클라이언트가 없다 |
| 기대 결과 | 레지스트리의 각 공급자에 수집 경로가 하나씩 있다 |
| 실제 결과 | ECOS·KOSIS 수집 경로가 없다. 해당 시리즈는 소유자 제공 픽스처로만 채워진다 |
| 영향 | 한국 공식 거시(기준금리, 콜금리, CD91, 15:30 환율, CPI)가 운영에서 항상 비어 fail-closed된다. 틀린 값은 아니지만 기능이 꺼진다. 요청서 6장 메모 "(-> 공급사필요)"가 가리키는 공백이다 |
| 수정안 | 7장 권장 구현(설명형). 단일 접점 `_ecos_fetch`, 키 `ECOS_API_KEY`, hermetic 접점 등록, PIT `ingest`로 레지스트리 id에 적재 |
| 회귀 테스트 | (제안) `test_v01_ecos_client_is_one_touchpoint_and_hermetic`: `tests/macro_acceptance._touchpoints()`에 `_ecos_fetch`가 있고, 패치된 응답 JSON으로 `BOK_BASE_RATE` 행이 `first_release`로 적재되며, 키가 없으면 `ECOSUnavailable` |

#### C01-05 · P3 · 사실 — FICC 시계열은 언제 받은 값인지 말하지 않는다

| 항목 | 내용 |
|---|---|
| ID | C01-05 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/data.py` `Series` `:77-84`(수신 시각 필드 없음), `_series_from_rows` `:498-503`. 이력 캐시 표시 `core/quant/history.py:437-438`(시간대 없는 로컬 시각). 화면 칩 `ui/portfolio_page.py:143`, `ui/strategy_lab_page.py:257`은 이력 note에만 반응 |
| 재현 단계 | `r02_ficc_cache_corrupt.py` 마지막 부분. 새로 받은 Series와 6시간 안의 캐시 적중 Series를 비교 |
| 기대 결과 | D-04/D-05의 요구대로 fetched_at이 관측일과 따로 결과에 남는다 |
| 실제 결과 | 둘이 `==`로 같다. note는 둘 다 빈 문자열. 이력 캐시는 "cached 2026-10-27 17:50"처럼 시간대 없이 표시 |
| 영향 | FICC 화면은 최대 6시간 묵은 값을 새 값처럼 보여 준다(일별 데이터라 영향은 작다). 감사 추적이 어렵다 |
| 수정안 | 부록 A: `Series.retrieved_at`(UTC ISO, 기본값 ""라 위치 인자 호환) 추가, `_series_from_rows`에서 채움. 이력 표시는 `datetime.fromtimestamp(ts, timezone.utc)`와 "Z" |
| 회귀 테스트 | C01-02 테스트의 `s.retrieved_at == want` 단언. R2 after: 적중의 `retrieved_at`이 파일 `ts`와 같음 |

#### C01-06 · P3 · 사실 — stale 정책이 없다

| 항목 | 내용 |
|---|---|
| ID | C01-06 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/history.py:424-445`(만료 파일은 버리고 fetch, 실패하면 예외 전파). `core/ficc/data.py:248-265, 539-543` |
| 재현 단계 | `python3 -B …/r03_stale_policy.py` (a)(b) |
| 기대 결과 | 요청서가 말한 stale-while-revalidate, 최소한 표시용 stale-if-error(라벨 부착) |
| 실제 결과 | (a) TTL을 5초 넘긴 실제 AAPL 파일이 있어도 FMP 429면 `source="fmp"`, `"auto"` 모두 `HistoryError`. (b) DGS10은 SYNTHETIC(last 0.0372, 소수)을 반환. 실제 값은 퍼센트(4.x). 단위 변화는 D03-06 |
| 영향 | 일시 장애 때 화면이 비거나 시뮬레이터 값으로 바뀐다. FICC 쪽은 D03-07과 같은 사실이다. 여기서는 이력 쪽까지 묶어 정책 문제로 본다 |
| 수정안 | 설명형. `_cached`와 `_provider_rows`에 `stale_if_error_s`(예: 24시간). 표시(display·context) 경로에서만, 실패 시 만료 파일을 `status="stale"`, note `STALE cache written <UTC>; <provider> failed: …`로 돌려준다. PIT `not_before` 경로와 acting 경로에서는 금지한다. D03-07 수정안과 하나로 구현한다 |
| 회귀 테스트 | (제안) `test_c01_stale_real_cache_is_labelled_not_replaced`: TTL+5초 파일, 공급자 429 → `h.status == "stale"`, `"STALE" in h.note`, 값은 파일 값. `not_before`를 주면 여전히 `None` |

#### C01-07 · P3 · 사실(성능 영향은 미계측) — Yahoo·KIS 비주식 이력은 평일 내내 10분 캐시

| 항목 | 내용 |
|---|---|
| ID | C01-07 |
| 심각도 | P3 |
| 판정 | 사실(동작). 실제 대기 시간 영향은 미계측 |
| 파일·함수·라인 | `core/quant/history.py` `_may_be_trading` `:363-387`. 특히 `:386-387`: 거래소를 모르는 공급자는 평일이면 True |
| 재현 단계 | `r03_stale_policy.py` (d). 2026-10-19(월) 00:00Z부터 168시간을 실제 함수로 표본 |
| 기대 결과 | 장이 닫힌 뒤 받은 시계열은 6시간 캐시 |
| 실제 결과 | "장중"(10분 TTL)으로 판정된 시간: YFINANCE SPY 123/168, ^VIX 123/168, KIS Y0101 123/168, FMP SPY 35/168, KIS 005930 40/168, YFINANCE 005930.KS 40/168, CRYPTO 168/168 |
| 영향 | Strategy Lab·Portfolio의 Yahoo 자산(ETF, 지수, 선물, FX)은 평일에 10분마다 전체를 다시 받는다. P-01(순차 호출 누적)과 겹친다. 실제 시간은 계측하지 않았다 |
| 수정안 | 설명형. Yahoo 티커의 거래소 추론: 접미사 없는 영문 티커와 `^GSPC`, `^VIX`는 US 캘린더. `.KS/.KQ`는 이미 KRX. `=X` FX는 주말만 닫힘. `=F`는 CME Globex 일정. KIS `Y0…` 금리는 한국 영업일 15:30 KST 이후 확정. 또는 FICC의 `_running_bar` 규칙(마지막 행 날짜가 기록 UTC 날짜보다 이르면 확정)을 함께 쓴다 |
| 회귀 테스트 | (제안) `test_c01_yahoo_us_listing_is_final_after_the_close`: `_may_be_trading("YFINANCE", "SPY", 2026-08-19 22:00Z) is False`, `15:00Z`면 `True` |

#### C01-08 · P3 · 사실 — 스키마 버전, 원자적 쓰기, 메모리 상한이 없다

| 항목 | 내용 |
|---|---|
| ID | C01-08 |
| 심각도 | P3 |
| 판정 | 사실. (3)(4)는 추정 |
| 파일·함수·라인 | `core/ficc/data.py:276`(`{"ts","rows"}`만, 비원자적), `:216`(`_MEM` 상한 없음), `:220-221`(키에 조정 기준 없음; `_yf_fetch`는 `auto_adjust=True` 고정 `:200`). `core/quant/history.py:452-455`. `data/krx/kis_client.py:160-164`. `data/krx/opendart_client.py:104-113`. `data/kis_markets.py:653-670`(`_MASTER_CACHE`, TTL 없음) |
| 재현 단계 | `r02` 마지막 줄: 원본 payload 키 `['rows', 'ts']`. 나머지는 코드 열람 |
| 기대 결과 | 형식 버전이 있고, 쓰기는 원자적이며, 메모리 캐시는 상한이 있다 |
| 실제 결과 | (1) 형식이 바뀌어도(예: 2026-10-02 FMP `/full` → `/dividend-adjusted` 전환) 구 파일을 가를 방법이 TTL뿐이다. (2) `write_text`는 비운 뒤 쓴다. 여러 화면이 `page.run_thread`로 동시에 돌면 읽는 쪽이 빈 파일을 볼 수 있다. 파싱 실패라 재수신으로 끝난다(안전하지만 낭비). (3) 4.3절의 이중 저장으로 화면마다 마지막 봉이 다를 수 있다(추정). (4) 긴 세션에서 KIS 마스터가 갱신되지 않는다(추정) |
| 영향 | 낮음. 형식 변경 시 최대 6시간 혼선, 동시 실행 시 중복 요청 |
| 수정안 | 부록 A가 (1)(2)를 두 시계열 캐시와 KIS 토큰에 적용한다(`v`, `key`, 임시 파일 후 `os.replace`). 조정 방식을 바꿀 때는 `_CACHE_SCHEMA`를 올린다. 설명형: `_MASTER_CACHE`는 KST 날짜별 키로 하루 1회 갱신. `_MEM`은 512개 LRU 상한 |
| 회귀 테스트 | `test_c01_history_cache_never_persists_non_finite_and_writes_atomically`의 `v`, `key`, `*.tmp` 단언. R2 after: payload 키 `['key', 'rows', 'ts', 'v']` |

#### C01-09 · P3 · 사실 — 연구용 CSV 캐시: 입력 해시 없음, 항상 참인 조건식, 0 이하 행 무경고 삭제

| 항목 | 내용 |
|---|---|
| ID | C01-09 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `docs/asset_expansion_study.py` `_cached` `:68-79`(특히 `:79`), `fred` `:94-105`, `binance_funding` `:123-136`, manifest `:813-816`, 머리말 `:10` |
| 재현 단계 | `python3 -B …/r06_study_cache.py`(CACHE를 임시 폴더로, 합성 CSV) |
| 기대 결과 | 입력 파일 해시가 결과와 함께 남는다. 데이터 정리는 명시적이고 기록된다 |
| 실제 결과 | (a) `name.startswith("_") is False`가 `yf_`, `upbit_`, `binance_` 이름에서 항상 True다. 그래서 `s[s > 0]` 필터가 항상 걸린다. (b) 7행 중 4행이 나갔다. 0, -1, NaN 행은 경고 없이 빠졌고 inf와 역순은 그대로였다. (c) manifest에 입력 해시가 없다. D-01/D-02 R4 스캔에 따르면 허용된 42개 파일에 inf·중복·역순은 없다. 그러나 `yf_CL_F.csv`의 2020-04-20 -37.63 행은 이 규칙으로 조용히 빠진다 |
| 영향 | 결과 재현성의 입력 쪽 근거가 없다(`results.csv` md5만 있음). 입력 파일이 덮어써져도 알 수 없다. WTI 음수 가격일 제외가 어디에도 기록되지 않는다 |
| 수정안 | 부록 A. 동작은 그대로 둔다(동결된 연구 결과 보존). 식을 `s[s > 0]`로 명시. 읽은 파일의 sha256을 manifest `inputs`에 기록. 새로 받을 때 `RETRIEVAL.json` 기록(C01-03과 연결). 삭제 행 수를 카드 note에 남길지는 소유자 판단 |
| 회귀 테스트 | (제안) `test_c01_study_manifest_pins_inputs`: CACHE를 임시 폴더로 두고 `_cached` 뒤 `INPUTS[파일] == sha256(파일)`, 새로 받으면 `RETRIEVAL.json`에 항목. 스크래치 확인 `r06b_study_inputs_after.py`(패치 트리): `INPUTS sha256 == file sha256: True` |

## 6. V-01 교차 공급자 비교 하네스 설계

### 6.1 코드에 있는 공급자와 비교 쌍

코드에서 쓰는 공급자는 Yahoo(`core/ficc/data.py:195-210`), FRED(`:163-192`), KIS(`data/krx/kis_client.py`, `data/kis_markets.py`), FMP(`core/quant/history.py:123-189`), Upbit·Binance(`data/crypto/crypto_client.py`)다. ECOS는 클라이언트가 없다(V01-03). KRX 마켓플레이스(`data/krx/krx_market_client.py`)는 키가 필요해 이번 쌍에서 뺐다.

| 쌍 | 자산 | 왼쪽 (공급자 · 기호 · 코드 경로) | 오른쪽 | 비교 방식 | 허용오차 | 필요 키 | 기대 |
|---|---|---|---|---|---|---|---|
| P01 | 삼성전자 종가 | KIS `005930` `history.kis_history`(수정주가, 분할·권리) | Yahoo `005930.KS` `auto_adjust=False` Close | level | 0bp | KIS | 정확히 일치 |
| P02 | 삼성전자 총수익 대 가격수익 | KIS `005930` | Yahoo `005930.KS` 수정 Close | returns | 1bp | KIS | 배당락일만 다름 |
| P03 | KODEX 200 | KIS `069500` | Yahoo `069500.KS` | level | 0bp | KIS | 정확히 일치 |
| P04 | KOSPI | KIS 지수 `0001` `kis_markets.index_daily` | Yahoo `^KS11` | level | 1bp(레지스트리 `_krx_close`) | KIS | 일치 |
| P05 | KOSPI 200 | KIS 지수 `2001` | Yahoo `^KS200` | level | 1bp | KIS | 일치 |
| P06 | Apple 분할 수정가 | KIS `NAS:AAPL`(MODP=1) | Yahoo `AAPL` 원 Close | level | 1bp | KIS | 일치 |
| P07 | Apple 배당 수정가 | FMP `dividend-adjusted` adjClose | Yahoo `AAPL` 수정 Close | returns | 5bp | FMP | 수준은 방법론 차, 수익률은 수 bp |
| P08 | S&P 500 | KIS 해외 차트 `SPX`(시장 N) | Yahoo `^GSPC` | level | 1bp | KIS | 지연 탐색으로 KIS 날짜 기준 확인 |
| P09 | VIX | FRED `VIXCLS` | Yahoo `^VIX` | level | 0.5bp | 없음 | 같은 Cboe 종가 |
| P10 | VIX3M | FRED `VXVCLS` | Yahoo `^VIX3M` | level | 0.5bp | 없음 | 같은 Cboe 종가 |
| P11 | 미국 10년 금리(%) | FRED `DGS10` | KIS `Y0202`(시장 I) | spread | 3bp | KIS | H.15 CMT 대 시장 호가, 수 bp |
| P12 | 미국 30년 금리(%) | FRED `DGS30` | KIS `Y0201` | spread | 3bp | KIS | 위와 같음 |
| P13 | 원/달러: FRED 대 Yahoo | FRED `DEXKOUS`(정오 NY) | Yahoo `KRW=X` | level | 50bp | 없음 | 고시 시각 차이의 분포. 1% 초과는 결함 후보 |
| P14 | 원/달러: KIS 대 Yahoo | KIS `FX@KRW`(시장 X) | Yahoo `KRW=X` | level | 50bp | KIS | 위와 같음 |
| P15 | BTC 달러 | Binance `BTCUSDT` 1d(00:00 UTC) | Yahoo `BTC-USD`(00:00 UTC) | level | 30bp | 없음 | USDT/USD 기저 + 거래소 차, 지연 0 |
| P16 | BTC 원화 | Upbit `KRW-BTC`(09:00 KST = 00:00 UTC 경계) | Binance `BTCUSDT` × Yahoo `KRW=X` | premium | 없음 | 없음 | 오차가 아니라 김치 프리미엄 분포 |

막힌 쌍(클라이언트 없음): 국고채 3년 KIS `Y0101` 대 ECOS 시장금리(일별), 원/달러 15:30 KIS 스냅샷 대 ECOS `731Y003`, KOSPI KIS 대 KRX 공식 종가(키 필요). ECOS 통계표 코드는 미검증이다.

### 6.2 정렬 규칙

- 날짜 기준(시간대): 각 leg가 `date_basis`를 가진다. 주식·지수는 거래소 현지 세션 날짜(KST, NY). FRED는 관측일(NY 영업일). 암호화폐는 UTC 날짜다. Upbit 일봉은 `candle_date_time_utc`(`data/crypto/crypto_client.py:137-165`, 특히 `:151`, `:165`), Binance 1d는 UTC(`:221-226`)다. Yahoo `KRW=X` 일봉의 날짜 기준은 문서화돼 있지 않다(미검증). 그래서 지연을 탐색한다.
- 지연 탐색: −1, 0, +1일. 기본은 0이다. 다른 지연이 차이 중앙값을 절반 이하로 줄일 때만 그 지연을 쓴다. 0이 아닌 지연이 나오면 그 자체가 발견사항(날짜 규약 차이)이다. 추세가 있는 시계열의 고정 편차를 날짜 이동으로 "설명"하지 않기 위한 규칙이다(셀프테스트로 확인).
- 통화: 같은 통화끼리만 수준을 비교한다. Upbit KRW 대 Binance USDT는 `KRW=X`로 환산해 premium 모드로만 본다. USDT와 USD의 차이는 P15에서 따로 잰다.
- 단위: 금리는 양쪽 모두 퍼센트다(FRED 원값, KIS 퍼센트 `data/kis_markets.py:55`). 차이는 bp(×100)로 낸다. `scale` 필드로 ×0.01, ×10 같은 보정을 한다. 단위가 어긋나면 일치율 0%로 드러난다(셀프테스트). 합성 대체 시 단위가 바뀌는 문제는 D03-06이다.
- 조정 기준: raw, split, total을 leg에 적는다. 같은 기준끼리는 수준 비교(P01). 다른 기준은 returns 모드로 일간 로그수익률 차이를 본다. 배당락일만 튀어야 정상이다(P02, P07). 앱의 `_yf_fetch`는 `auto_adjust=True` 고정(`core/ficc/data.py:200`)이라 하네스는 원가 비교용으로 yfinance를 직접 부른다.
- 캐시: 수집 단계에서 `config.FICC_CACHE_TTL_SECONDS = 0`으로 앱 캐시를 끈다. 지금 공급자가 주는 값을 비교한다.

### 6.3 지표

- `n_left`, `n_right`, `n_common`: 각 쪽 행 수와 공통 날짜 수.
- `only_left`, `only_right`: 한쪽에만 있는 날짜 수와 처음 5개 날짜.
- `match_rate`: 허용오차 안에 드는 공통 날짜 비율.
- `median_bp`, `p95_bp`, `max_bp`: 차이의 분포(bp). level은 상대 차이, spread는 절대 차이×100, returns는 일간 로그수익률 차이.
- `max_abs_diff`: 원 단위 최대 절대 차이.
- `worst`: 가장 큰 차이 5개(날짜, bp).
- `lag_days`: 채택된 지연.
- `ok`: 지연 0이고 일치율 99% 이상. premium 모드는 지연 0만 본다.
- premium 모드: 부호 있는 `premium_median_bp`, `premium_p5_bp`, `premium_p95_bp`.
- 스냅샷 이상: sha256 불일치, 비유한 값, 중복 날짜, 역순 행을 목록으로 보고한다. 고치지는 않는다(`pit.reconcile`과 같은 원칙: never auto-correct).

### 6.4 스크립트 개요 (`tools/vendor_compare.py`, 부록 A 전문)

- `Leg`(provider, symbol, loader, unit, scale, date_basis, adjustment, currency), `Pair`(id, asset, left, right, tol_bp, compare, lags, needs, expect), `PAIRS` 16개.
- `write_leg`, `read_leg`: `<out>/<pair>/{left,right}.csv`(`date,value`)와 `.json` 사이드카(공급자, 기호, loader, 단위, 날짜 기준, 조정 기준, `fetched_at_utc`, sha256, 행 수, 라이브러리 버전, 소요 초). 키·토큰은 쓰지 않는다.
- `compare_rows`(순수 함수), `compare_dir`, `render`(Markdown 표), `--json`(`compare.json`), `--strict`(실패 시 종료 코드 1).
- `_loaders`: 코드베이스 클라이언트를 그대로 쓴다(`core.quant.history`, `core.ficc.data`, `data.kis_markets`). 원가·수정가 비교용 yfinance 직접 호출만 추가한다.
- `fetch`: 키가 없는 쌍은 건너뛴다(`needs`). 한 leg가 실패해도 나머지는 계속한다.
- `selftest`: 합성 결함 11개.

### 6.5 실행 위치와 절차

- 수집(fetch)은 소유자 PC에서 한다. `docs/asset_expansion/study.log`의 경로(`C:\Users\…`)로 보아 Windows다. 이 클라우드는 공급자 호스트에 접속할 수 없다(FRED DNS 실패 확인).
- 비교(compare)와 셀프테스트는 어디서나 된다. 스냅샷 폴더를 zip으로 넘기면 감사자가 같은 결과를 재현한다.
- 시점: 두 시장이 모두 닫힌 뒤 실행한다. 예: KST 07:00~08:30(미국 장 마감 뒤, 한국 장 시작 전). 그래야 장중 봉이 섞이지 않는다.
- 출력은 저장소 밖(`~/.nextgen/vendor_compare/`)에 둔다. 요약 표만 감사 문서로 옮긴다.

```powershell
cd <저장소 경로>
python tools\vendor_compare.py selftest
python tools\vendor_compare.py fetch --out "$env:USERPROFILE\.nextgen\vendor_compare\2026-10-28" --days 750
python tools\vendor_compare.py compare "$env:USERPROFILE\.nextgen\vendor_compare\2026-10-28" --json
```

이번 감사에서 실행한 것(합성 스냅샷, `run_harness_compare_demo.py`)의 출력 일부:

| pair | asset | lag | n L/R/common | only L/R | match | median bp | p95 bp | max bp | ok |
|---|---|---|---|---|---|---|---|---|---|
| P01 | Samsung Electronics close (KRW) | +0 | 250/247/247 | 3/0 | 100.0% | 0.00 | 0.00 | 0.00 | yes |
| P09 | VIX close | +1 | 250/250/250 | 0/0 | 100.0% | 0.00 | 0.00 | 0.00 | NO |
| P11 | UST 10y yield (pct) | +0 | 250/250/250 | 0/0 | 100.0% | 2.00 | 2.00 | 2.00 | yes |
| P16 | BTC: Upbit KRW vs Binance x USD/KRW (kimchi premium) | +0 | 250/250/250 | 0/0 | 0.0% | 200.00 | 200.00 | 200.00 | yes |

P09는 오른쪽 날짜를 하루 밀어 둔 합성 데이터다. 하네스가 지연 +1을 찾고 `ok=NO`로 표시했다. `--strict` 종료 코드는 1이었다.

### 6.6 결과 해석 기준

- P01, P03: 정확히 일치해야 한다. 어긋나면 KIS 수정주가 처리(유상증자 등)나 Yahoo 데이터 결함이다.
- P04, P05, P08: 1bp 안이어야 한다(레지스트리 허용오차). 지연이 0이 아니면 KIS 해외 차트가 KST 날짜로 적는 것일 수 있다.
- P02, P07: returns 중앙값이 수 bp 안이어야 한다. 배당락일만 크면 정상이다. `worst` 날짜가 배당락일인지 확인한다.
- P09, P10: 같은 Cboe 종가다. 0.5bp를 넘으면 결함이다.
- P11, P12: 3bp 안이 정상이다.
- P13, P14: 고시 시각이 달라 분포로 본다. 1%를 넘는 날은 결함 후보다. V01-01의 공급자 선택 근거가 된다.
- P15: 30bp 안이 정상이다. 크면 USDT 디페그나 거래소 이상이다.
- P16: 오차 지표가 아니다. V01-01 수정 전후 프리미엄을 비교하는 데 쓴다.

## 7. 소유자 메모 대응: FICC·BTC 공급자

메모: "(-> 공급사필요)", "(-> FICC/BTC 모두 KIS에서 접근 가능한지, 안된다면 다른 공급사 중 최적화된 공급사 알아서 파악해서 딱 깔끔하고 센스있게 implement 할 것.)"

이 차원은 감사 전용이라 구현하지 않았다. 아래는 코드 근거와 제안이다. KIS 가능 범위는 `data/kis_markets.py`의 문서 문자열(2026-09-25 실측이라고 적힘)에 근거한다. 실제 응답은 미검증이다.

| 영역 | KIS로 되는가 (코드 근거) | 코드에 이미 있는 대안 | 권장 | 상태 |
|---|---|---|---|---|
| 원화 금리(국고채 1·3·5·10·20·30년, CD91, 콜, 회사채 AA- 3년) | 됨. 시장 I 차트 `KRW_YIELD_CODES`(`data/kis_markets.py:55-60`), `krw_yield_daily`(`:492-494`), 스냅샷 `comp-interest`(`:499-512`) | 없음 | 화면·이력: KIS. 공식 값: ECOS | ECOS 미구현 |
| 국고채 개별 종목 가격·수익률 | 됨. `bond_daily`(`:570-578`) | 없음 | KIS | 구현됨 |
| KTB 선물, 원/달러 선물(KRX) | 됨. 시장 CF(`:52`), `futures_daily` | 없음 | KIS | 구현됨 |
| 미국 국채 전 구간(1개월~30년) | 일부. `Y0202` 10년, `Y0201` 30년, `Y0204` 연방기금(`:61`) | FRED `DGS*`(`core/ficc/data.py:67-68`) | FRED. KIS는 교차 검증(P11, P12) | 구현됨 |
| SOFR, 신용 스프레드, OECD 단기금리 | 안 됨(코드에 없음) | FRED | FRED | 구현됨 |
| 원/달러 | 됨. `FX@KRW` 고시(`:64`), 레지스트리 `USDKRW_1530_SNAPSHOT`(`series_registry.yaml:330-348`) | FRED DEXKOUS(주간 공표), Yahoo `KRW=X` | 화면: KIS → Yahoo → FRED 순. 공식 15:30: ECOS `731Y003` | ECOS 미구현. V01-01 |
| 해외 금리·지수 선물(ZN, ES 등) | 안 됨. 주식 계좌 키로 HTTP 500(`:13-15, 516`) | Yahoo 연속 선물 `=F` | Yahoo | 구현됨 |
| VIX | 선물만. CBOE VX(`:13`, `core/ficc/vol_products.py:6`) | FRED VIXCLS, Yahoo `^VIX` | 현물 FRED·Yahoo, 선물 KIS | 구현됨 |
| BTC 현물 | 안 됨(코드에 없음) | Upbit KRW, Binance USDT, Yahoo BTC-USD | Upbit + Binance(무키) | 구현됨 |
| BTC 선물(CME) | 됨. `ovf_daily("BTC…", "CME")`(`:514-517`) | 없음 | 규제 선물 기준가로 KIS | 함수만 있음. `load_history`가 `BTCU26@CME`를 FMP로 보냄(`_looks_kis_market` 거짓, 감사 중 확인) |
| BTC 펀딩·미결제약정 | 안 됨 | Binance fapi | Binance | 구현됨 |
| 한국 거시(기준금리, 콜금리, CD91 공식, CPI) | 안 됨 | 없음 | ECOS, KOSIS | 미구현(V01-03) |

권장 구현(제안, 미구현):

1. ECOS 클라이언트 `data/ecos/ecos_client.py`. 네트워크 접점은 `_ecos_fetch(stat, cycle, start, end, item)` 하나. URL 형식은 `https://ecos.bok.or.kr/api/StatisticSearch/{KEY}/json/kr/{from}/{to}/{stat}/{cycle}/{start}/{end}/{item}`이다. 이 형식은 2차 자료(wikidocs, CRAN `ecos` 패키지 문서)로 확인했고 공식 문서는 열지 못했다(미검증). 키는 `ECOS_API_KEY`(`config._clean`; Settings 화면에는 존재 여부만). `tests/macro_acceptance._touchpoints()`에 접점을 추가해 hermetic을 지킨다. 적재는 레지스트리 id(`BOK_BASE_RATE`, `BOK_CALL_RATE`, `KR_CD91`, `ECOS_1530_CLOSE`)로 `core.ficc.pit.ingest`를 거친다. 통계표·항목 코드는 소유자가 확정한다(레지스트리가 이미 "OWNER input"이라고 적고 있다).
2. KOSIS 클라이언트(`KR_CPI`)도 같은 틀로 만든다.
3. BTC는 지금 구성(Upbit KRW 현물, Binance USDT 현물·무기한, Yahoo BTC-USD)을 유지한다. KIS CME BTC 선물은 `load_history` 라우팅에 `^[A-Z0-9]+@(CME|CBOE|ICE)$` → `KISMarkets.ovf_daily` 규칙을 더해 규제 선물 기준가로 쓴다. 하네스 P15 옆에 basis 쌍으로 추가할 수 있다. CME BTC 선물 정산 시각은 미검증이다.
4. 미국 금리는 FRED를 유지한다. KIS `Y0202`, `Y0201`은 교차 검증에 쓴다.
5. 원/달러는 V01-01의 순서를 따른다. 공식 15:30 종가는 ECOS 클라이언트가 생긴 뒤 연결한다.

## 8. 미검증 항목

- KIS 실제 응답: 커버리지 주장(`data/kis_markets.py:7-16`), `EGW00121`의 뜻, 다른 키·도메인 토큰을 서버가 어떻게 거절하는지. 공식 오류코드 페이지가 이 환경에서 열리지 않았다.
- FRED DEXKOUS의 주간 공표: 저장소 레지스트리(`schedule: H10`)에 근거했다. FRED 페이지는 DNS 실패로 열지 못했다. 실제 지연 일수 분포는 확인하지 않았다.
- ECOS URL 형식과 통계표 코드(`731Y003` 등)의 뜻.
- CME BTC 선물 정산 시각. Yahoo `KRW=X` 일봉의 날짜 기준.
- `docs/asset_expansion/cache`의 46개 파일이 실제로 언제 받아졌는지. `RETRIEVAL.json`을 채우려면 소유자 확인이 필요하다.
- 패치 뒤 I-01(`test_dry_run_end_to_end_on_the_local_cache`)의 결과. 금지 파일(`yf_SPY.csv`)을 읽기 때문에 실행하지 않았다. mtime 대체 경로에서 최신 행을 빼는 것이 vt 결과에 주는 영향은 확인하지 못했다.
- C01-07의 실제 대기 시간 영향. 계측하지 않았다.
- C01-08 (3) 화면 간 마지막 봉 차이, (4) KIS 마스터 미갱신. 코드로만 추론했다.
- 하네스 fetch 단계. 공급자 접속 금지 규칙으로 실행하지 않았다. compare와 selftest만 합성 데이터로 실행했다.
- Windows에서의 `os.replace` 동작. 다른 스레드가 파일을 읽는 중이면 이름 바꾸기가 실패할 수 있다. 그때는 캐시를 갱신하지 않고 임시 파일을 지운다(코드상). 리눅스에서만 실행했다.
- OpenDART 기업코드 캐시(D4)의 관련 테스트 존재 여부.

## 9. 재현 스크립트 경로

모두 스크래치 폴더에 있다. 저장소 밖이다. `AUDIT_TREE=1`을 붙이면 패치 트리에서 같은 스크립트를 돌린다. 출력은 같은 이름의 `.out`(원본), `.after.out`(패치 트리)이다.

- 공통 전처리: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/_guard.py`
- R1 이력 캐시 손상(C01-01): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r01_history_cache_corrupt.py`
- R2 FICC 캐시 손상·수신 시각(C01-02, C01-05, C01-08): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r02_ficc_cache_corrupt.py`
- R3 stale 정책·10분 TTL 시간 수(C01-06, C01-07): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r03_stale_policy.py`
- R4 KIS 토큰(C01-04): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r04_kis_token_cache.py`
- R5 dry run mtime(C01-03): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r05_mtime_provenance.py`
- R5b mtime이 장중 봉을 감춤(C01-03): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r05b_mtime_hides_running_bar.py`
- R6 연구용 CSV 캐시(C01-09): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r06_study_cache.py`
- R6b 패치 뒤 입력 해시(C01-09): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r06b_study_inputs_after.py`
- R7 김치 프리미엄 FX 나이(V01-01): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/r07_kimchi_fx_age.py`
- 하네스 셀프테스트(V01-02): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/run_harness_selftest.py`
- 하네스 compare 데모: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/run_harness_compare_demo.py`
- 기존·새 테스트 실행(패치 트리, `--orig`면 원본): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/run_tree_tests.py`
- 새 테스트를 원본 코드에 대고 실행: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/run_new_tests_on_orig.py`
- 패치 트리: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/tree/`
- 패치(줄바꿈 원본 유지, `git apply` 바로 가능): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/c01_v01_cache_and_vendors/proposed_c01_v01.diff`

테스트 실행 결과:

| 실행 | 결과 |
|---|---|
| 원본, 기존 관련 테스트(quant 3, ficc 전체, macro_m1_pit 2, engine 1) | 63 PASS, 0 FAIL |
| 패치 트리, 같은 63건 + 새 테스트 7건 | 70 PASS, 0 FAIL |
| 새 테스트 7건을 원본 코드에 대고 실행 | 7 FAIL(결함을 잡음) |
| 하네스 셀프테스트 | 11 PASS |

## 부록 A. 제안 패치 (unified diff, HEAD `527cdf2` 기준)

적용 전 확인: `git apply --check`가 통과한다. `core/quant/history.py`와 `tests/run_all.py`는 CRLF 파일이다. 아래 본문은 LF로 옮겼다. 이 본문으로 적용하려면 `git apply --ignore-whitespace`를 쓰고, 그 두 파일의 새 줄을 CRLF로 맞춘다. 스크래치의 `proposed_c01_v01.diff`는 원래 줄바꿈을 유지해 그대로 적용된다.

포함 파일: `core/quant/history.py`(C01-01, C01-05, C01-08), `core/ficc/data.py`(C01-02, C01-05, C01-08), `data/krx/kis_client.py`(C01-04), `core/skills/macro_daily.py`(C01-03), `docs/asset_expansion_study.py`(C01-03, C01-09), `core/crypto/analytics.py`·`ui/crypto_page.py`(V01-01), `tests/run_all.py`(새 스위트 `cache` 등록), 새 파일 `tools/vendor_compare.py`(V01-02), `tests/cache_vendor_acceptance.py`(회귀 테스트 7건).

```diff
--- a/core/quant/history.py
+++ b/core/quant/history.py
@@ -427,14 +427,16 @@
     name = re.sub(r"[^A-Za-z0-9_.-]", "_", f"HIST_{provider}_{symbol.upper()}_{days}")
     path = config.ficc_cache_dir() / f"{name}.json"
     try:
-        p = json.loads(path.read_text("utf-8"))
+        p = json.loads(path.read_text("utf-8"), parse_constant=_reject_constant)
+        if not _valid_cached(p, name):
+            raise ValueError("cache payload failed validation")     # treated as a miss: refetch
         # Only an explicit `"live": false` earns the full TTL (a file from
         # before the flag existed does not), and only while the market has not
         # traded since it was written.
         final = p.get("live") is False and not _traded_since(provider, symbol, float(p["ts"]))
         limit = ttl if final else min(ttl, _CACHE_LIVE_TTL)
-        if 0 <= time.time() - float(p["ts"]) < limit and len(p["dates"]) == len(p["closes"]):
-            stamp = datetime.fromtimestamp(float(p["ts"])).strftime("%Y-%m-%d %H:%M")
+        if 0 <= time.time() - float(p["ts"]) < limit:
+            stamp = datetime.fromtimestamp(float(p["ts"]), timezone.utc).strftime("%Y-%m-%d %H:%MZ")   # UTC, stated
             note = "; ".join(x for x in (str(p.get("note") or ""), f"cached {stamp}") if x)
             return History(str(p["symbol"]), str(p["source"]), tuple(p["dates"]),
                            tuple(float(c) for c in p["closes"]), note=note,
@@ -447,17 +449,66 @@
     if live and not h.status:
         h = replace(h, status="provisional_intraday")   # M1: a running last bar is never presented as a close
     if len(h) >= _CACHE_MIN_ROWS:
-        try:
-            path.parent.mkdir(parents=True, exist_ok=True)
-            path.write_text(json.dumps({"ts": time.time(), "live": live, "symbol": h.symbol,
-                                        "source": h.source, "note": h.note,
-                                        "adjustment": h.adjustment, "status": h.status,
-                                        "dates": h.dates, "closes": h.closes}), "utf-8")
-        except Exception:
-            pass                              # a cache that cannot be written is not an error
+        payload = {"v": _CACHE_SCHEMA, "key": name, "ts": time.time(), "live": live, "symbol": h.symbol,
+                   "source": h.source, "note": h.note, "adjustment": h.adjustment, "status": h.status,
+                   "dates": list(h.dates), "closes": list(h.closes)}
+        if _valid_cached(payload, name):      # never persist what the reader would refuse (NaN, inf, <= 0, order)
+            try:
+                _atomic_write(path, json.dumps(payload, allow_nan=False))
+            except Exception:
+                pass                          # a cache that cannot be written is not an error
     return h
 
 
+_CACHE_SCHEMA = 2                             # 1 = the pre-2026-10-27 shape without "v"/"key" (still readable)
+
+
+def _reject_constant(token: str):
+    raise ValueError(f"non-finite JSON constant {token!r} in a cache file")
+
+
+def _valid_cached(p: dict, name: str) -> bool:
+    """The read-side gate of `_cached` (C-01): the same rules the fetch path promises, re-checked on every hit.
+    Schema not newer than this code, key equal to the file's key (a copied/renamed file is refused), ISO dates
+    strictly ascending (sorted, no duplicates), closes finite and > 0, at least `_CACHE_MIN_ROWS` rows."""
+    try:
+        if int(p.get("v", 1)) > _CACHE_SCHEMA or p.get("key", name) != name:
+            return False
+        dates, closes = p["dates"], p["closes"]
+        if not (isinstance(dates, list) and isinstance(closes, list)) or len(dates) != len(closes):
+            return False
+        if len(dates) < _CACHE_MIN_ROWS or not math.isfinite(float(p["ts"])):
+            return False
+        prev = ""
+        for d, c in zip(dates, closes):
+            if not isinstance(d, str) or d <= prev or date.fromisoformat(d[:10]).isoformat() != d[:10]:
+                return False
+            if isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) or c <= 0:
+                return False
+            prev = d
+        return True
+    except Exception:
+        return False
+
+
+def _atomic_write(path, text: str) -> None:
+    """Write-then-rename: a reader sees the old file or the new one, never a truncated one."""
+    import os
+    import tempfile
+    path.parent.mkdir(parents=True, exist_ok=True)
+    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
+    try:
+        with os.fdopen(fd, "w", encoding="utf-8") as fh:
+            fh.write(text)
+        os.replace(tmp, path)
+    except BaseException:
+        try:
+            os.unlink(tmp)
+        except OSError:
+            pass
+        raise
+
+
 SOURCES = ("auto", "fmp", "kis", "yfinance", "crypto", "synthetic")
 
 
--- a/core/ficc/data.py
+++ b/core/ficc/data.py
@@ -82,6 +82,9 @@
     dates: tuple[str, ...]            # ISO dates, ascending
     values: tuple[float, ...]
     note: str = ""
+    # C-01 provenance (appended with a default so positional construction keeps working): UTC ISO instant the rows
+    # were retrieved from the provider — the cache file's `ts` on a hit, the fetch time otherwise; "" = synthetic.
+    retrieved_at: str = ""
 
     def __len__(self) -> int:
         return len(self.values)
@@ -251,10 +254,15 @@
     hit = _MEM.get(key)
     if hit is None:
         try:
-            payload = json.loads((config.ficc_cache_dir() / f"{key}.json").read_text("utf-8"))
+            payload = json.loads((config.ficc_cache_dir() / f"{key}.json").read_text("utf-8"),
+                                 parse_constant=_reject_constant)
+            if int(payload.get("v", 1)) > _CACHE_SCHEMA or payload.get("key", key) != key:
+                return None
             hit = (float(payload["ts"]), [(str(d), float(v)) for d, v in payload["rows"]])
         except Exception:
             return None
+        if not _rows_ok(hit[1]):
+            return None                                   # corrupt or hand-edited file: a miss, never served
     ts, rows = hit
     if not_before is not None and ts <= float(not_before):
         return None
@@ -266,16 +274,54 @@
 
 
 def _cache_put(key: str, rows: Rows) -> None:
-    if float(config.FICC_CACHE_TTL_SECONDS) <= 0:
+    if float(config.FICC_CACHE_TTL_SECONDS) <= 0 or not _rows_ok(rows):
         return
     now = time.time()
     _MEM[key] = (now, rows)
+    import os
+    import tempfile
+    tmp = None
     try:
         d = config.ficc_cache_dir()
         d.mkdir(parents=True, exist_ok=True)
-        (d / f"{key}.json").write_text(json.dumps({"ts": now, "rows": rows}), "utf-8")
+        fd, tmp = tempfile.mkstemp(prefix=f"{key}.", suffix=".tmp", dir=str(d))
+        with os.fdopen(fd, "w", encoding="utf-8") as fh:
+            fh.write(json.dumps({"v": _CACHE_SCHEMA, "key": key, "ts": now, "rows": rows}, allow_nan=False))
+        os.replace(tmp, d / f"{key}.json")                # atomic: a reader never sees a truncated file
     except Exception:
-        pass
+        if tmp:                                           # e.g. Windows refuses the rename while a reader holds it
+            try:
+                os.unlink(tmp)
+            except OSError:
+                pass
+
+
+_CACHE_SCHEMA = 2           # 1 = {"ts", "rows"} only (pre-2026-10-27; still readable)
+
+
+def _reject_constant(token: str):
+    raise ValueError(f"non-finite JSON constant {token!r} in a cache file")
+
+
+def _rows_ok(rows) -> bool:
+    """C-01 read/write gate: ISO dates strictly ascending (sorted, no duplicate), values finite. The row-count
+    floor (`_MIN_OBS`) is applied by `_provider_rows`, not here, so a short PIT fixture can still be read."""
+    prev = ""
+    try:
+        for d, v in rows:
+            d = str(d)
+            if d <= prev or date.fromisoformat(d[:10]).isoformat() != d[:10] or not math.isfinite(float(v)):
+                return False
+            prev = d
+    except Exception:
+        return False
+    return True
+
+
+def _retrieved_at(provider: str, id: str, days: int) -> str:
+    hit = _MEM.get(_cache_key(provider, id, days))
+    ts = hit[0] if hit else time.time()
+    return _dt.fromtimestamp(ts, _tz.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
 
 
 # --------------------------------------------------------------------------- #
@@ -463,7 +509,7 @@
     for i in ids:
         key = _cache_key(provider, i, days)
         hit = _cache_get(key, not_before=not_before)
-        if hit:
+        if hit and len(hit) >= _MIN_OBS:                  # the fetch path's floor applies to a hit too (C-01)
             rows[i] = hit
             if pit_store is not None and key in _MEM:
                 pit_store.ingest_rows(provider, i, hit, _dt.fromtimestamp(_MEM[key][0], _tz.utc))
@@ -500,7 +546,7 @@
     rows = rows[-days:]
     return Series(id=id, label=label or id, source=provider,
                   dates=tuple(d for d, _ in rows), values=tuple(float(v) for _, v in rows),
-                  note=note)
+                  note=note, retrieved_at=_retrieved_at(provider, id, days))
 
 
 def _degraded(s: Series, provider: str, reason: str) -> Series:
--- a/data/krx/kis_client.py
+++ b/data/krx/kis_client.py
@@ -80,6 +80,10 @@
 # calls (about 25 ms apart) inside one second were enough to trip it, which a
 # single ETF analysis does. Every call in the process is therefore spaced out.
 _RATE_LIMITED = "EGW00201"
+# Token refused by the server (expired, revoked, or minted for another app key / domain). EGW00123 is the code the
+# official sample re-authenticates on (koreainvestment/open-trading-api legacy/rest/current_price_samle.py);
+# EGW00121 is reported by third parties for an invalid token (UNVERIFIED against the official error table).
+_TOKEN_REJECTED = ("EGW00121", "EGW00123")
 _MIN_GAP_S = 0.12                       # about 8 requests a second
 _PACE_LOCK = threading.Lock()
 _last_call = [0.0]
@@ -143,11 +147,19 @@
         self.ready = bool(config.kis_ready() and requests is not None)
 
     # -- token ---------------------------------------------------------------
+    def _scope(self) -> str:
+        """Which app key and domain a token belongs to: a one-way digest, never the key itself (C-01)."""
+        import hashlib
+        app_key, _ = config.kis_credentials()
+        return hashlib.sha256(f"{app_key}|{self.base_url}".encode()).hexdigest()[:16]
+
     def _cached_token(self) -> Optional[str]:
         try:
             data = json.loads(_TOKEN_PATH.read_text(encoding="utf-8"))
         except Exception:
             return None
+        if data.get("scope") != self._scope():
+            return None   # minted for another key or domain (or a pre-scope file): mint a new one
         token = data.get("access_token")
         expires = data.get("expires_at", 0)
         if token and time.time() < float(expires) - 120:
@@ -155,16 +167,35 @@
         return None
 
     def _store_token(self, token: str, expires_in: float) -> None:
+        import os
         try:
             _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
-            _TOKEN_PATH.write_text(
-                json.dumps({"access_token": token,
-                            "expires_at": time.time() + float(expires_in)}),
-                encoding="utf-8",
-            )
+            tmp = _TOKEN_PATH.with_name(_TOKEN_PATH.name + ".tmp")
+            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)   # owner-only on POSIX
+            with os.fdopen(fd, "w", encoding="utf-8") as fh:
+                fh.write(json.dumps({"access_token": token, "scope": self._scope(), "issued_at": time.time(),
+                                     "expires_at": time.time() + float(expires_in)}))
+            os.replace(tmp, _TOKEN_PATH)
         except Exception:
             pass          # a non-persistable token still works for this session
 
+    def _drop_token(self, *, min_age_s: float = 60.0) -> bool:
+        """Forget the cached token after the server refused it, so the next call mints a new one. A token issued
+        less than `min_age_s` ago is kept: a refusal right after issuance is a key/domain problem that a new token
+        will not cure, and issuance itself is rate-limited. True when the token was dropped."""
+        with _TOKEN_LOCK:
+            try:
+                issued = float(json.loads(_TOKEN_PATH.read_text(encoding="utf-8")).get("issued_at") or 0.0)
+            except Exception:
+                issued = 0.0
+            if time.time() - issued < min_age_s:
+                return False
+            try:
+                _TOKEN_PATH.unlink()
+            except OSError:
+                pass
+            return True
+
     def token(self) -> str:
         if not self.ready:
             raise KISUnavailable("Set KIS_APP_KEY and KIS_APP_SECRET to enable KIS")
@@ -223,14 +254,17 @@
             except Exception as exc:
                 raise KISError(f"{tr_id}: {type(exc).__name__}") from None
             self.last_headers = {k.lower(): v for k, v in resp.headers.items()}
-            if resp.status_code == 200:
-                break
-            # KIS reports its own errors as HTTP 500 with a code in the body.
+            # KIS reports its own errors as HTTP 500 (sometimes 200) with a code in the body.
             try:
                 body = resp.json()
                 code, why = str(body.get("msg_cd") or ""), str(body.get("msg1") or "").strip()
             except Exception:
                 code = why = ""
+            if code in _TOKEN_REJECTED and attempt == 1 and self._drop_token() and retry:
+                headers["authorization"] = f"Bearer {self.token()}"     # never keep a refused token (C-01)
+                continue                    # retry=False (live quote): dropped, the next call mints; no 2nd attempt
+            if resp.status_code == 200 and code not in _TOKEN_REJECTED:
+                break
             if code == _RATE_LIMITED and retry and attempt == 1:
                 time.sleep(1.0)             # let the one-second window pass, then once more
                 continue
--- a/core/skills/macro_daily.py
+++ b/core/skills/macro_daily.py
@@ -1392,6 +1392,22 @@
     return out
 
 
+RETRIEVAL_FILE = "RETRIEVAL.json"      # {file: {"retrieved_at_utc": ISO Z, "sha256": hex}} written by the downloader
+
+
+def _sha256(path: Path) -> str:
+    import hashlib
+    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
+
+
+def _retrieval_manifest(cache_dir: Path) -> dict:
+    try:
+        doc = json.loads((Path(cache_dir) / RETRIEVAL_FILE).read_text(encoding="utf-8"))
+    except (OSError, ValueError):
+        return {}
+    return doc if isinstance(doc, dict) else {}
+
+
 def dry_run(macro_dir, *, clock: Callable[[], datetime], cache_dir: Path = CACHE_DIR, clocks=None,
             markets: Iterable[str] = MARKETS, rows_per_series: int = 900) -> dict:
     """The demonstrable end-to-end path on local vendor data: labelled, offline, never acting, never a verdict."""
@@ -1403,16 +1419,27 @@
     store = P.PITStore(root / "pit", registry=registry, clocks=clocks)
     now = clock()
     ingested, last = {}, {}
+    retrieval = _retrieval_manifest(Path(cache_dir))
     for sid, (name, source) in DRY_RUN_CACHE.items():
         path = Path(cache_dir) / name
         if not path.is_file():
             ingested[sid] = {"file": name, "status": "absent"}
             continue
         rows = read_cache_csv(path)[-rows_per_series:]
-        fetched = datetime.fromtimestamp(path.stat().st_mtime, UTC)   # the file's real retrieval instant (L1283): a running bar stays provisional
+        # C-01: the retrieval instant comes from the cache's RETRIEVAL.json (written at download time, sha256-pinned),
+        # not from the filesystem mtime, which a clone, unzip or copy resets. Without a matching entry the instant is
+        # unknown: the mtime is used as a lower-trust stand-in AND the newest row is withheld, because a row fetched
+        # mid-session must never become a close just because the file was copied later (L1283).
+        entry = retrieval.get(name) or {}
+        if entry.get("sha256") == _sha256(path) and entry.get("retrieved_at_utc"):
+            fetched, prov = P.parse_utc(entry["retrieved_at_utc"]), "manifest"
+        else:
+            fetched, prov = datetime.fromtimestamp(path.stat().st_mtime, UTC), "mtime"
+            rows = rows[:-1]
         rep = P.ingest(store, sid, rows, source=source, retrieved_at_utc=fetched, registry=registry, clocks=clocks,
                        provider_mode="explicit", channel=f"dry_run:{name}")
-        ingested[sid] = {"file": name, "appended": rep.appended, "logged": rep.logged, "flagged": len(rep.flags)}
+        ingested[sid] = {"file": name, "appended": rep.appended, "logged": rep.logged, "flagged": len(rep.flags),
+                         "retrieved_at_source": prov}
         closes = [r["obs_date"] for r in store.rows(sid) if r["value_status"] in P.CLOSE_STATUSES]
         if closes:
             last[sid] = max(closes)                            # the decided session is the last stamped close, never a quote
--- a/docs/asset_expansion_study.py
+++ b/docs/asset_expansion_study.py
@@ -65,18 +65,48 @@
 # --------------------------------------------------------------------------- #
 # Data (cached)
 # --------------------------------------------------------------------------- #
-def _cached(name: str, loader) -> pd.Series:
-    f = CACHE / (name.replace("=", "_").replace("^", "_").replace(":", "_").replace("/", "_") + ".csv")
+INPUTS: dict[str, str] = {}      # cache file -> sha256 of the bytes this run read (written to manifest.json)
+
+
+def _sha256(f: Path) -> str:
+    return hashlib.sha256(f.read_bytes()).hexdigest()
+
+
+def _record_retrieval(f: Path) -> None:
+    """C-01: the download instant and content hash of a freshly written cache file, in cache/RETRIEVAL.json.
+    core.skills.macro_daily.dry_run reads it instead of the file's mtime."""
+    path = CACHE / "RETRIEVAL.json"
+    try:
+        doc = json.loads(path.read_text(encoding="utf-8"))
+    except (OSError, ValueError):
+        doc = {}
+    doc[f.name] = {"retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sha256": _sha256(f)}
+    path.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
+
+
+def _read_or_fetch(f: Path, loader) -> pd.Series:
     if f.exists() and not REFRESH:
         s = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0]
     else:
         s = loader()
-        s = s.dropna()
-        s.name = name
         s.to_csv(f)
-    s = s.dropna()
+        _record_retrieval(f)
+    INPUTS[f.name] = _sha256(f)
+    return s
+
+
+def _cached(name: str, loader) -> pd.Series:
+    f = CACHE / (name.replace("=", "_").replace("^", "_").replace(":", "_").replace("/", "_") + ".csv")
+
+    def load():
+        s = loader().dropna()
+        s.name = name
+        return s
+    s = _read_or_fetch(f, load).dropna()
     s.index = pd.to_datetime(s.index)
-    return s[s > 0] if (s > 0).all() or name.startswith("_") is False else s
+    # Was `s[s > 0] if (s > 0).all() or name.startswith("_") is False else s`: the second operand is True for
+    # every name used here (yf_, upbit_, binance_), so the filter always applied. Same behaviour, stated plainly.
+    return s[s > 0]
 
 
 def yf(symbol: str, start: str = "1995-01-01") -> pd.Series:
@@ -95,11 +125,7 @@
     def load():
         import pandas_datareader.data as web
         return web.DataReader(series_id, "fred", start).iloc[:, 0].astype(float)
-    f = CACHE / f"fred_{series_id}.csv"
-    if f.exists() and not REFRESH:
-        s = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0]
-    else:
-        s = load(); s.to_csv(f)
+    s = _read_or_fetch(CACHE / f"fred_{series_id}.csv", load)
     s.index = pd.to_datetime(s.index)
     return s.dropna()
 
@@ -126,11 +152,7 @@
         f = BinancePublic().funding(symbol, days=3000)
         d = f.daily()
         return pd.Series(list(d.values()), index=pd.to_datetime(list(d.keys())))
-    f = CACHE / f"binance_funding_{symbol}.csv"
-    if f.exists() and not REFRESH:
-        s = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0]
-    else:
-        s = load(); s.to_csv(f)
+    s = _read_or_fetch(CACHE / f"binance_funding_{symbol}.csv", load)
     s.index = pd.to_datetime(s.index)
     return s
 
@@ -813,7 +835,8 @@
     (OUT / "manifest.json").write_text(json.dumps({"run": date.today().isoformat(), "seed": SEED, "results_md5": md5,
                                                     "quick": QUICK, "cards": [c["card_id"] for c in cards],
                                                     "rescored": sorted(run_ids),
-                                                    "decisions": {c["card_id"]: c["decision"] for c in cards}},
+                                                    "decisions": {c["card_id"]: c["decision"] for c in cards},
+                                                    "inputs": dict(sorted(INPUTS.items()))},
                                                    indent=1), encoding="utf-8")
 
 
--- a/core/crypto/analytics.py
+++ b/core/crypto/analytics.py
@@ -64,18 +64,33 @@
     pred_t: float = 0.0                # Newey–West t (lag 6)
     n: int = 0
     note: str = ""
+    fx_age_days_last: int = 0          # calendar days between the last premium date and the FX row it used (V-01)
+    fx_age_days_max: int = 0
+    fx_stale_dropped: int = 0          # trailing dates removed because their FX was older than max_fx_age_days
 
 
 def kimchi_premium(upbit_krw: dict[str, float], binance_usdt: dict[str, float],
-                   usdkrw: dict[str, float], *, z_window: int = 365, horizon: int = 7) -> KimchiPremium:
+                   usdkrw: dict[str, float], *, z_window: int = 365, horizon: int = 7,
+                   max_fx_age_days: int | None = None) -> KimchiPremium:
     """Inputs are {date: close} dicts; USD/KRW is forward-filled by date because
-    the FX fixing has no weekend rows."""
+    the FX fixing has no weekend rows. `max_fx_age_days` (None = no limit, the
+    study's frozen behaviour) drops the dates whose forward-filled FX is older:
+    FRED DEXKOUS is published weekly (H.10), so its last week is otherwise
+    priced at an FX up to ~10 days old. The age is always reported."""
     dates = sorted(set(upbit_krw) & set(binance_usdt))
     fx_dates = np.array(sorted(usdkrw))
     fx_vals = np.array([usdkrw[d] for d in fx_dates], dtype=float)
     idx = np.searchsorted(fx_dates, np.array(dates), side="right") - 1
     keep = idx >= 0
+    age = np.array([(date.fromisoformat(d) - date.fromisoformat(fx_dates[i])).days if k else 0
+                    for d, i, k in zip(dates, idx, keep)])
+    dropped = 0
+    if max_fx_age_days is not None:
+        stale = keep & (age > max_fx_age_days)
+        dropped = int(stale.sum())
+        keep = keep & ~stale
     dates = [d for d, k in zip(dates, keep) if k]
+    age = age[keep]
     fx = fx_vals[idx[keep]]
     kr = np.array([upbit_krw[d] for d in dates])
     us = np.array([binance_usdt[d] for d in dates])
@@ -103,8 +118,11 @@
                          last_z=float(z[-1]) if np.isfinite(z[-1]) else 0.0, mean_pct=float(prem.mean()),
                          max_pct=float(prem.max()), adf_p=adf_pvalue(prem), half_life_days=half_life(prem),
                          pred_slope=slope, pred_t=t, n=int(prem.size),
-                         note=("USD/KRW forward-filled by date (FRED noon fixing vs UTC-midnight closes: a few hours "
-                               "of FX drift); a positive premium means Korea pays more than the world price."))
+                         fx_age_days_last=int(age[-1]), fx_age_days_max=int(age.max()), fx_stale_dropped=dropped,
+                         note=(f"USD/KRW forward-filled by date (noon New York fixing vs UTC-midnight closes); the last "
+                               f"premium uses an FX row {int(age[-1])} day(s) old (max {int(age.max())})"
+                               + (f", {dropped} date(s) with older FX dropped" if dropped else "")
+                               + "; a positive premium means Korea pays more than the world price."))
 
 
 def _hac_var(u: np.ndarray, lag: int) -> float:
--- a/ui/crypto_page.py
+++ b/ui/crypto_page.py
@@ -60,7 +60,9 @@
 def analyze(*, days: int = 730, source: str = "live") -> dict:
     d = _live(days) if source == "live" else _synthetic()
     out: dict = {"source": d["source"], "usdkrw_source": d.get("usdkrw_source", "synthetic")}
-    out["kimchi"] = CA.kimchi_premium(d["upbit"], d["binance"], d["usdkrw"])
+    # V-01: never price a premium at an FX row more than 4 calendar days old (a weekend plus a holiday); FRED DEXKOUS
+    # is published weekly, so its last week would otherwise use one stale fixing. The age is in kp.fx_age_days_last.
+    out["kimchi"] = CA.kimchi_premium(d["upbit"], d["binance"], d["usdkrw"], max_fx_age_days=4)
     try:
         out["funding"] = CA.funding_carry(d["funding_daily"], d["binance"])
     except ValueError as exc:
--- a/tests/run_all.py
+++ b/tests/run_all.py
@@ -48,6 +48,7 @@
 from tests.paper_live_acceptance import tests as paper_tests     # noqa: E402
 from grokteam.selfcheck import tests as grokteam_tests             # noqa: E402
 from tests.frozen_guard import tests as guard_tests         # noqa: E402
+from tests.cache_vendor_acceptance import tests as cache_tests    # noqa: E402
 from tests.notrun import NotRun                             # noqa: E402
 
 REGISTRY = ROOT / "tests" / "macro_registry.csv"
@@ -82,6 +83,7 @@
             [(f"paper/{n}", f) for n, f in paper_tests()] +
             [(f"grokteam/{n}", f) for n, f in grokteam_tests()] +
             [(f"guard/{n}", f) for n, f in guard_tests()] +
+            [(f"cache/{n}", f) for n, f in cache_tests()] +
             [(f"papers/{n}", f) for n, f in papers_tests()])
 
 
@@ -128,7 +130,7 @@
 def main(argv=None) -> int:
     parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
     parser.add_argument("--milestone", help="run the exit set of M<k> via tests/macro_registry.csv")
-    parser.add_argument("--suite", help="run one suite: safety, engine, ui, quant, ficc, expansion, macro, paper, grokteam, guard or papers")
+    parser.add_argument("--suite", help="run one suite: safety, engine, ui, quant, ficc, expansion, macro, paper, grokteam, guard, cache or papers")
     args = parser.parse_args(argv)
     if args.milestone and not re.fullmatch(r"M(10|[0-9])", args.milestone):
         parser.error("--milestone takes M0..M10")
--- /dev/null
+++ b/tools/vendor_compare.py
@@ -0,0 +1,440 @@
+"""Cross-provider comparison harness (audit item V-01): the same asset over the same period from two providers,
+aligned on time zone, currency, unit and adjustment basis, then measured. Report only: nothing is corrected, nothing
+feeds a model (the same rule as core.ficc.pit.reconcile: "never auto-correct").
+
+Three commands:
+
+  fetch     OWNER'S MACHINE ONLY (the cloud proxy blocks the providers). Pulls each leg with the app cache off and
+            writes <out>/<pair>/<leg>.csv (date,value) plus <leg>.json (provider, symbol, loader, params,
+            fetched_at_utc, sha256, unit, date_basis, adjustment, library versions). Keys stay in .env; nothing
+            secret is written.
+                python tools/vendor_compare.py fetch --out %USERPROFILE%\\.nextgen\\vendor_compare\\2026-10-28
+                python tools/vendor_compare.py fetch --out <dir> --pairs P01,P07 --days 750
+  compare   HERMETIC. Reads a snapshot dir only (it can be zipped and audited anywhere) and prints one row per pair;
+            --json writes compare.json next to the snapshots; --strict exits 1 when a pair is outside tolerance.
+                python tools/vendor_compare.py compare <dir> [--json] [--strict]
+  selftest  HERMETIC. Synthetic legs with planted defects; proves the metrics catch each one.
+"""
+from __future__ import annotations
+
+import argparse
+import csv
+import hashlib
+import json
+import math
+import sys
+import time
+from dataclasses import asdict, dataclass, field
+from datetime import date, timedelta
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+if str(ROOT) not in sys.path:
+    sys.path.insert(0, str(ROOT))
+
+
+# --------------------------------------------------------------------------------------------------------------- #
+# Pair table
+# --------------------------------------------------------------------------------------------------------------- #
+@dataclass(frozen=True)
+class Leg:
+    provider: str            # FRED | YAHOO | KIS | FMP | UPBIT | BINANCE
+    symbol: str
+    loader: str              # key into LOADERS (fetch phase only)
+    unit: str                # price | pct | index | krw_per_usd
+    scale: float = 1.0       # multiply to reach the pair's canonical unit
+    date_basis: str = ""     # what the row date means: "KST session", "NY session", "UTC day", ...
+    adjustment: str = ""     # raw | split | total | n/a
+    currency: str = ""
+
+
+@dataclass(frozen=True)
+class Pair:
+    id: str
+    asset: str
+    left: Leg
+    right: Leg
+    tol_bp: float            # a row matches when its difference (in bp, see `compare`) is <= tol_bp
+    # level   : |right/left - 1| in bp of the level (prices, indices, FX)
+    # spread  : |right - left| x 100, i.e. bp of yield when the unit is pct (rates)
+    # returns : |daily log-return difference| in bp (adjusted vs unadjusted legs; the residual days are listed)
+    # premium : signed (left/right - 1) in bp, reported as a distribution, never "matched" (kimchi premium)
+    compare: str = "level"
+    lags: tuple[int, ...] = (-1, 0, 1)
+    needs: tuple[str, ...] = ()
+    expect: str = ""         # what a disagreement means for this pair
+
+
+def _y(sym, unit="price", adj="split", ccy="", basis="exchange session", loader="yahoo_close"):
+    return Leg("YAHOO", sym, loader, unit, 1.0, basis, adj, ccy)
+
+
+PAIRS: tuple[Pair, ...] = (
+    Pair("P01", "Samsung Electronics close (KRW)",
+         Leg("KIS", "005930", "kis_stock", "price", 1.0, "KST session", "split", "KRW"),
+         _y("005930.KS", ccy="KRW", basis="KST session"), 0.0, needs=("KIS",),
+         expect="exact: both are split/rights-adjusted KRX closes; Yahoo with auto_adjust=False"),
+    Pair("P02", "Samsung Electronics total return vs price return",
+         Leg("KIS", "005930", "kis_stock", "price", 1.0, "KST session", "split", "KRW"),
+         _y("005930.KS", adj="total", ccy="KRW", basis="KST session", loader="yahoo_adjclose"), 1.0, "returns",
+         needs=("KIS",), expect="returns equal except ex-dividend sessions (listed as the residual days)"),
+    Pair("P03", "KODEX 200 ETF close",
+         Leg("KIS", "069500", "kis_stock", "price", 1.0, "KST session", "split", "KRW"),
+         _y("069500.KS", ccy="KRW", basis="KST session"), 0.0, needs=("KIS",)),
+    Pair("P04", "KOSPI index", Leg("KIS", "0001", "kis_index", "index", 1.0, "KST session", "n/a", "KRW"),
+         _y("^KS11", "index", "n/a", "KRW", "KST session"), 1.0, needs=("KIS",),
+         expect="registry tolerance index_bp: 1 (data/macro/series_registry.yaml _krx_close)"),
+    Pair("P05", "KOSPI 200 index", Leg("KIS", "2001", "kis_index", "index", 1.0, "KST session", "n/a", "KRW"),
+         _y("^KS200", "index", "n/a", "KRW", "KST session"), 1.0, needs=("KIS",)),
+    Pair("P06", "Apple close, split-adjusted (USD)",
+         Leg("KIS", "NAS:AAPL", "kis_overseas", "price", 1.0, "NY session", "split", "USD"),
+         _y("AAPL", ccy="USD", basis="NY session"), 1.0, needs=("KIS",)),
+    Pair("P07", "Apple dividend-adjusted close (USD)",
+         Leg("FMP", "AAPL", "fmp_adjclose", "price", 1.0, "NY session", "total", "USD"),
+         _y("AAPL", adj="total", ccy="USD", basis="NY session", loader="yahoo_adjclose"), 5.0, "returns",
+         needs=("FMP",), expect="levels drift by methodology; daily returns should agree to a few bp"),
+    Pair("P08", "S&P 500 index", Leg("KIS", "SPX", "kis_chart_index", "index", 1.0, "NY session?", "n/a", "USD"),
+         _y("^GSPC", "index", "n/a", "USD", "NY session"), 1.0, needs=("KIS",),
+         expect="lag search shows whether KIS dates the NY close on the KST calendar day"),
+    Pair("P09", "VIX close", Leg("FRED", "VIXCLS", "fred", "index", 1.0, "NY session", "n/a", ""),
+         _y("^VIX", "index", "n/a", "", "NY session"), 0.5, expect="exact to 2 decimals (both Cboe 16:15 ET)"),
+    Pair("P10", "VIX3M close", Leg("FRED", "VXVCLS", "fred", "index", 1.0, "NY session", "n/a", ""),
+         _y("^VIX3M", "index", "n/a", "", "NY session"), 0.5),
+    Pair("P11", "UST 10y yield (pct)", Leg("FRED", "DGS10", "fred", "pct", 1.0, "NY business day", "n/a", ""),
+         Leg("KIS", "Y0202", "kis_yield", "pct", 1.0, "?", "n/a", ""), 3.0, "spread", needs=("KIS",),
+         expect="H.15 constant-maturity vs a market close quote: a few bp; the lag shows KIS's date basis"),
+    Pair("P12", "UST 30y yield (pct)", Leg("FRED", "DGS30", "fred", "pct", 1.0, "NY business day", "n/a", ""),
+         Leg("KIS", "Y0201", "kis_yield", "pct", 1.0, "?", "n/a", ""), 3.0, "spread", needs=("KIS",)),
+    Pair("P13", "USD/KRW: FRED noon NY vs Yahoo",
+         Leg("FRED", "DEXKOUS", "fred", "krw_per_usd", 1.0, "NY noon", "n/a", "KRW"),
+         _y("KRW=X", "krw_per_usd", "n/a", "KRW", "Yahoo daily bar (UTC/London)"), 50.0,
+         expect="different fixing instants: a distribution, not an error; > 1 % is a data problem"),
+    Pair("P14", "USD/KRW: KIS fixing vs Yahoo",
+         Leg("KIS", "FX@KRW", "kis_fx", "krw_per_usd", 1.0, "KST day", "n/a", "KRW"),
+         _y("KRW=X", "krw_per_usd", "n/a", "KRW", "Yahoo daily bar (UTC/London)"), 50.0, needs=("KIS",)),
+    Pair("P15", "BTC: Binance BTCUSDT vs Yahoo BTC-USD",
+         Leg("BINANCE", "BTCUSDT", "binance", "price", 1.0, "UTC day (00:00 close)", "n/a", "USDT"),
+         _y("BTC-USD", "price", "n/a", "USD", "UTC day (00:00 close)"), 30.0,
+         expect="USDT/USD basis plus venue spread; lag must be 0"),
+    Pair("P16", "BTC: Upbit KRW vs Binance x USD/KRW (kimchi premium)",
+         Leg("UPBIT", "KRW-BTC", "upbit", "price", 1.0, "UTC day (09:00 KST close)", "n/a", "KRW"),
+         Leg("BINANCE", "BTCUSDT", "binance_krw", "price", 1.0, "UTC day", "n/a", "KRW via KRW=X"), 0.0,
+         "premium", lags=(0,), expect="not an error metric: the premium distribution (median, p5, p95)"),
+)
+
+
+# --------------------------------------------------------------------------------------------------------------- #
+# Snapshot I/O (shared by fetch and compare)
+# --------------------------------------------------------------------------------------------------------------- #
+def write_leg(path: Path, rows: list[tuple[str, float]], meta: dict) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    text = "date,value\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
+    path.with_suffix(".csv").write_text(text, encoding="utf-8")
+    meta = dict(meta, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), rows=len(rows))
+    path.with_suffix(".json").write_text(json.dumps(meta, indent=1, sort_keys=True), encoding="utf-8")
+
+
+def read_leg(path: Path) -> tuple[list[tuple[str, float]], dict, list[str]]:
+    """Rows, sidecar, and the anomalies found (the harness reports them; it never fixes them)."""
+    text = path.with_suffix(".csv").read_text(encoding="utf-8")
+    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
+    issues = []
+    if meta.get("sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
+        issues.append("sha256 mismatch: the snapshot was edited after fetch")
+    rows, seen, prev = [], set(), ""
+    for rec in csv.DictReader(text.splitlines()):
+        d, raw = (rec.get("date") or "")[:10], rec.get("value")
+        try:
+            v = float(raw)
+            date.fromisoformat(d)
+        except (TypeError, ValueError):
+            issues.append(f"unparseable row {d!r},{raw!r}")
+            continue
+        if not math.isfinite(v):
+            issues.append(f"non-finite value on {d}")
+            continue
+        if d in seen:
+            issues.append(f"duplicate date {d}")
+            continue
+        if d < prev:
+            issues.append(f"out of order at {d}")
+        seen.add(d)
+        prev = max(prev, d)
+        rows.append((d, v))
+    rows.sort()
+    return rows, meta, issues
+
+
+# --------------------------------------------------------------------------------------------------------------- #
+# Alignment and metrics (pure; numpy only)
+# --------------------------------------------------------------------------------------------------------------- #
+def _shift(d: str, k: int) -> str:
+    return (date.fromisoformat(d) + timedelta(days=k)).isoformat()
+
+
+def _align(left: dict, right: dict, lag: int) -> list[tuple[str, float, float]]:
+    """Pairs (date, left, right[date + lag]); lag in calendar days."""
+    return [(d, left[d], right[_shift(d, lag)]) for d in sorted(left) if _shift(d, lag) in right]
+
+
+def _rel_bp(a: float, b: float) -> float:
+    return abs(b / a - 1.0) * 1e4 if a else math.inf
+
+
+def compare_rows(pair: Pair, left_rows, right_rows) -> dict:
+    import numpy as np
+    L = {d: v * pair.left.scale for d, v in left_rows}
+    R = {d: v * pair.right.scale for d, v in right_rows}
+
+    def score(lag):
+        al = _align(L, R, lag)
+        if pair.compare == "returns":
+            diffs = [abs(math.log(r1 / r0) - math.log(l1 / l0)) * 1e4
+                     for (_, l0, r0), (_, l1, r1) in zip(al, al[1:])]
+        elif pair.compare == "spread":
+            diffs = [abs(rv - lv) * 100.0 for _, lv, rv in al]
+        elif pair.compare == "premium":
+            diffs = [(lv / rv - 1.0) * 1e4 for _, lv, rv in al]
+        else:
+            diffs = [_rel_bp(lv, rv) for _, lv, rv in al]
+        return (float(np.median(np.abs(diffs))) if diffs else math.inf, -len(al)), al, diffs
+    # Lag 0 unless another lag at least halves the median difference: a constant bias on a trending series must
+    # not be "explained" by a date shift, while a real one-day date-convention offset collapses the error.
+    scored = {k: score(k) for k in pair.lags}
+    lag = 0 if 0 in scored else pair.lags[0]
+    alt = min((k for k in scored if k != lag), key=lambda k: scored[k][0], default=None)
+    if alt is not None and scored[alt][0][0] < 0.5 * scored[lag][0][0]:
+        lag = alt
+    _, al, diffs = scored[lag]
+    common = {d for d, _, _ in al}
+    only_left = sorted(d for d in L if d not in common)
+    only_right = sorted(d for d in R if _shift(d, -lag) not in L)
+    arr = np.asarray(diffs, dtype=float)
+    if pair.compare == "premium":
+        out_p = {"premium_median_bp": float(np.median(arr)) if arr.size else math.nan,
+                 "premium_p5_bp": float(np.percentile(arr, 5)) if arr.size else math.nan,
+                 "premium_p95_bp": float(np.percentile(arr, 95)) if arr.size else math.nan}
+        arr = np.abs(arr)
+    else:
+        out_p = {}
+    out = {"pair": pair.id, "asset": pair.asset, "compare": pair.compare, "lag_days": lag,
+           "n_left": len(L), "n_right": len(R), "n_common": len(al),
+           "only_left": len(only_left), "only_left_first": only_left[:5],
+           "only_right": len(only_right), "only_right_first": only_right[:5],
+           "tol_bp": pair.tol_bp}
+    if arr.size:
+        worst = np.argsort(-arr)[:5]
+        dates = [d for d, _, _ in (al[1:] if pair.compare == "returns" else al)]   # a return is dated by its end
+        out.update(match_rate=float(np.mean(arr <= pair.tol_bp)), median_bp=float(np.median(arr)),
+                   p95_bp=float(np.percentile(arr, 95)), max_bp=float(arr.max()),
+                   max_abs_diff=float(max(abs(rv - lv) for _, lv, rv in al)),
+                   worst=[(dates[i], round(float(arr[i]), 3)) for i in worst])
+    else:
+        out.update(match_rate=0.0, median_bp=math.nan, p95_bp=math.nan, max_bp=math.nan, max_abs_diff=math.nan,
+                   worst=[])
+    out.update(out_p)
+    out["ok"] = (bool(arr.size) and lag == 0) if pair.compare == "premium" else \
+        (bool(arr.size) and lag == 0 and out["match_rate"] >= 0.99)
+    return out
+
+
+def compare_dir(snap: Path, *, write_json: bool = False) -> list[dict]:
+    results = []
+    for pair in PAIRS:
+        d = snap / pair.id
+        if not (d / "left.csv").is_file() or not (d / "right.csv").is_file():
+            results.append({"pair": pair.id, "asset": pair.asset, "status": "not fetched"})
+            continue
+        lrows, lmeta, lissues = read_leg(d / "left")
+        rrows, rmeta, rissues = read_leg(d / "right")
+        res = compare_rows(pair, lrows, rrows)
+        res.update(left_issues=lissues, right_issues=rissues,
+                   left_fetched_at=lmeta.get("fetched_at_utc"), right_fetched_at=rmeta.get("fetched_at_utc"))
+        results.append(res)
+    if write_json:
+        (snap / "compare.json").write_text(json.dumps(results, indent=1, default=str), encoding="utf-8")
+    return results
+
+
+def render(results: list[dict]) -> str:
+    head = "| pair | asset | lag | n L/R/common | only L/R | match | median bp | p95 bp | max bp | ok |"
+    lines = [head, "|" + "---|" * 10]
+    for r in results:
+        if "n_common" not in r:
+            lines.append(f"| {r['pair']} | {r['asset']} | | | | | | | | {r.get('status')} |")
+            continue
+        lines.append(f"| {r['pair']} | {r['asset']} | {r['lag_days']:+d} | {r['n_left']}/{r['n_right']}/{r['n_common']}"
+                     f" | {r['only_left']}/{r['only_right']} | {r['match_rate']:.1%} | {r['median_bp']:.2f}"
+                     f" | {r['p95_bp']:.2f} | {r['max_bp']:.2f} | {'yes' if r['ok'] else 'NO'} |")
+    return "\n".join(lines)
+
+
+# --------------------------------------------------------------------------------------------------------------- #
+# Fetch phase (owner's machine). Each loader returns [(iso_date, value)] from the codebase's own clients, with the
+# app cache switched off so the comparison sees what the provider answers now, not a 6-hour-old file.
+# --------------------------------------------------------------------------------------------------------------- #
+def _loaders(days: int) -> dict:
+    import config
+    config.FICC_CACHE_TTL_SECONDS = 0.0
+
+    def yahoo(sym, adjusted):
+        import yfinance as yf
+        df = yf.download(sym, period="5y" if days > 504 else "2y", progress=False, auto_adjust=adjusted,
+                         threads=False)
+        col = df["Close"]
+        col = col.iloc[:, 0] if hasattr(col, "columns") else col
+        return [(str(d)[:10], float(v)) for d, v in col.dropna().items()]
+
+    def hist(fn):
+        return lambda sym: (lambda h: list(zip(h.dates, h.closes)))(fn(sym, days=days))
+
+    from core.ficc import data as F
+    from core.quant import history as H
+    from data.kis_markets import CHART_FX, CHART_INDEX, CHART_YIELD, KISMarkets
+
+    def kis_bars(get):
+        return lambda sym: list(zip(*(lambda b: (b.dates, b.close))(get(sym))))
+
+    km = KISMarkets() if config.kis_ready() else None
+
+    def binance_krw(sym):
+        btc = dict(hist(H.crypto_history)(sym))
+        fx = dict(yahoo("KRW=X", False))
+        return [(d, v * fx[d]) for d, v in btc.items() if d in fx]
+    return {
+        "yahoo_close": lambda s: yahoo(s, False),
+        "yahoo_adjclose": lambda s: yahoo(s, True),
+        "fred": lambda s: (lambda x: list(zip(x.dates, x.values)))(F.load_series(s, source="fred", days=days)),
+        "kis_stock": hist(H.kis_history),
+        "kis_index": kis_bars(lambda s: km.index_daily(s, days=days)),
+        "kis_overseas": hist(H.kis_market_history),
+        "kis_chart_index": kis_bars(lambda s: km.overseas_chart(CHART_INDEX, s, days=days)),
+        "kis_yield": kis_bars(lambda s: km.overseas_chart(CHART_YIELD, s, days=days)),
+        "kis_fx": kis_bars(lambda s: km.overseas_chart(CHART_FX, s, days=days)),
+        "fmp_adjclose": hist(H.fmp_history),
+        "upbit": hist(H.crypto_history),
+        "binance": hist(H.crypto_history),
+        "binance_krw": binance_krw,
+    }
+
+
+def fetch(out: Path, ids: set[str] | None, days: int) -> None:
+    import config
+    ready = {"KIS": config.kis_ready(), "FMP": config.fmp_ready()}
+    loaders = _loaders(days)
+    versions = {}
+    for mod in ("yfinance", "pandas", "numpy", "requests"):
+        try:
+            versions[mod] = __import__(mod).__version__
+        except Exception:
+            versions[mod] = None
+    for pair in PAIRS:
+        if ids and pair.id not in ids:
+            continue
+        missing = [n for n in pair.needs if not ready.get(n)]
+        if missing:
+            print(f"{pair.id}: skipped, {'/'.join(missing)} not configured")
+            continue
+        for side, leg in (("left", pair.left), ("right", pair.right)):
+            t0 = time.time()
+            try:
+                rows = loaders[leg.loader](leg.symbol)
+            except Exception as exc:                                   # report and go on: one leg never stops a run
+                print(f"{pair.id} {side} {leg.provider} {leg.symbol}: {type(exc).__name__}: {exc}")
+                continue
+            write_leg(out / pair.id / side, rows, dict(asdict(leg), pair=pair.id, side=side, days=days,
+                                                       fetched_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",
+                                                                                    time.gmtime()),
+                                                       seconds=round(time.time() - t0, 2), versions=versions))
+            print(f"{pair.id} {side} {leg.provider} {leg.symbol}: {len(rows)} rows")
+
+
+# --------------------------------------------------------------------------------------------------------------- #
+# Self-test (hermetic): planted defects must show up in the metrics
+# --------------------------------------------------------------------------------------------------------------- #
+def selftest(tmp: Path) -> list[str]:
+    import numpy as np
+    rng = np.random.default_rng(5)
+    days, d = [], date(2024, 1, 2)
+    while len(days) < 300:
+        if d.weekday() < 5:
+            days.append(d.isoformat())
+        d += timedelta(days=1)
+    base = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(days))))
+    rows = list(zip(days, map(float, base)))
+    p = PAIRS[0]
+    fails = []
+
+    def check(name, cond):
+        print(f"{'PASS' if cond else 'FAIL'} {name}")
+        if not cond:
+            fails.append(name)
+    r = compare_rows(p, rows, rows)
+    check("identical legs: lag 0, match 100 %, ok", r["lag_days"] == 0 and r["match_rate"] == 1.0 and r["ok"])
+    shifted = [(_shift(d, 1), v) for d, v in rows]
+    r = compare_rows(p, rows, shifted)
+    check("right dated one day later: lag +1 found, not ok", r["lag_days"] == 1 and not r["ok"])
+    gaps = [x for i, x in enumerate(rows) if i % 50 != 7]
+    r = compare_rows(p, rows, gaps)
+    check("6 dates missing on the right are listed", r["only_left"] == 6 and r["only_left_first"][0] == rows[7][0])
+    spiked = list(rows)
+    spiked[123] = (spiked[123][0], spiked[123][1] * 1.005)
+    r = compare_rows(p, rows, spiked)
+    check("one 50 bp print is the worst date", r["worst"][0][0] == rows[123][0] and abs(r["max_bp"] - 50) < 1e-6)
+    pct = [(d, v * 100) for d, v in rows]
+    r = compare_rows(p, rows, pct)
+    check("unit x100 is never a match", r["match_rate"] == 0.0)
+    factor = [(d, v * (0.98 if i < 200 else 1.0)) for i, (d, v) in enumerate(rows)]
+    ret_pair = PAIRS[1]
+    r = compare_rows(ret_pair, rows, factor)
+    check("dividend factor: returns differ on exactly one day", sum(1 for _, bp in r["worst"] if bp > 1) == 1
+          and r["worst"][0][0] == rows[200][0])
+    leg = tmp / "P01" / "left"
+    write_leg(leg, rows, {"provider": "SYN"})
+    write_leg(tmp / "P01" / "right", rows, {"provider": "SYN"})
+    text = leg.with_suffix(".csv").read_text(encoding="utf-8").replace(f"{rows[5][1]!r}", "inf")
+    leg.with_suffix(".csv").write_text(text, encoding="utf-8")
+    _, _, issues = read_leg(leg)
+    check("edited snapshot: sha256 mismatch and non-finite row reported",
+          any("sha256" in i for i in issues) and any("non-finite" in i for i in issues))
+    res = compare_dir(tmp)
+    yld = [(d, 4.0 + 0.001 * i) for i, (d, _) in enumerate(rows)]
+    r = compare_rows(PAIRS[10], yld, [(d, v + 0.02) for d, v in yld])
+    check("rates: a constant 2 bp spread reads 2 bp and matches a 3 bp tolerance",
+          abs(r["median_bp"] - 2.0) < 1e-6 and r["match_rate"] == 1.0)
+    bumped = [(d, v + (0.10 if i == 77 else 0.02)) for i, (d, v) in enumerate(yld)]
+    r = compare_rows(PAIRS[10], yld, bumped)
+    check("rates: a 10 bp print is the worst date", r["worst"][0] == (yld[77][0], 10.0))
+    r = compare_rows(PAIRS[15], [(d, v * 1.02) for d, v in rows], rows)
+    check("premium: +2 % reads +200 bp median", abs(r["premium_median_bp"] - 200) < 1e-6 and r["ok"])
+    check("compare_dir: fetched pair compared, others 'not fetched'",
+          res[0].get("n_common") == 299 and all(x.get("status") == "not fetched" for x in res[1:]))
+    return fails
+
+
+def main(argv=None) -> int:
+    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    sub = ap.add_subparsers(dest="cmd", required=True)
+    f = sub.add_parser("fetch")
+    f.add_argument("--out", required=True)
+    f.add_argument("--pairs", default="")
+    f.add_argument("--days", type=int, default=750)
+    c = sub.add_parser("compare")
+    c.add_argument("dir")
+    c.add_argument("--json", action="store_true")
+    c.add_argument("--strict", action="store_true")
+    sub.add_parser("selftest")
+    a = ap.parse_args(argv)
+    if a.cmd == "fetch":
+        fetch(Path(a.out), {x.strip() for x in a.pairs.split(",") if x.strip()} or None, a.days)
+        return 0
+    if a.cmd == "compare":
+        res = compare_dir(Path(a.dir), write_json=a.json)
+        print(render(res))
+        return 1 if a.strict and any(r.get("ok") is False for r in res) else 0
+    import tempfile
+    return 1 if selftest(Path(tempfile.mkdtemp(prefix="vendor_compare_"))) else 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
--- /dev/null
+++ b/tests/cache_vendor_acceptance.py
@@ -0,0 +1,291 @@
+"""Audit C-01 / V-01 regression tests (2026-10-27): cache read validation, cache schema and atomic writes, KIS token
+scoping, dry-run retrieval provenance, FX age in the kimchi premium, and the vendor-comparison harness.
+
+Hermetic: every provider touchpoint is patched; caches live in temp dirs. `python -m tests.cache_vendor_acceptance`.
+"""
+from __future__ import annotations
+
+import json
+import math
+import os
+import tempfile
+import time
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
+
+import config
+
+DATES = [(date(2026, 9, 1) + timedelta(days=i)).isoformat() for i in range(30)]
+CLOSES = [100.0 + i for i in range(30)]
+
+
+class _Env:
+    """Temp FICC cache dir, TTL 6 h; restores config and env on exit."""
+
+    def __enter__(self):
+        self.saved = (config.FICC_CACHE_TTL_SECONDS, os.environ.get("NEXTGEN_FICC_CACHE"))
+        self.dir = Path(tempfile.mkdtemp(prefix="c01_"))
+        os.environ["NEXTGEN_FICC_CACHE"] = str(self.dir)
+        config.FICC_CACHE_TTL_SECONDS = 21600.0
+        return self
+
+    def __exit__(self, *exc):
+        config.FICC_CACHE_TTL_SECONDS = self.saved[0]
+        if self.saved[1] is None:
+            os.environ.pop("NEXTGEN_FICC_CACHE", None)
+        else:
+            os.environ["NEXTGEN_FICC_CACHE"] = self.saved[1]
+
+
+def _history_payload(**over):
+    p = {"ts": time.time() - 60, "live": False, "symbol": "ABC", "source": "FMP", "note": "", "adjustment": "total",
+         "status": "", "dates": list(DATES), "closes": list(CLOSES)}
+    p.update(over)
+    return p
+
+
+def test_c01_history_cache_refuses_corrupt_payloads():
+    import core.quant.history as H
+    saved = (H._READY.copy(), H._may_be_trading, H._traded_since)
+    calls = []
+
+    def fetch(symbol, *, days):
+        calls.append(symbol)
+        return H.History(symbol, "FMP", tuple(DATES), tuple(CLOSES), adjustment="total")
+    try:
+        H._READY["FMP"] = lambda: True
+        H._may_be_trading = lambda *a, **k: False
+        H._traded_since = lambda *a, **k: False
+        bad = {"nan": _history_payload(closes=CLOSES[:-1] + [math.nan]),
+               "inf": _history_payload(closes=CLOSES[:-1] + [math.inf]),
+               "nonpositive": _history_payload(closes=[0.0, -1.0] + CLOSES[2:]),
+               "unsorted": _history_payload(dates=DATES[::-1]),
+               "duplicate": _history_payload(dates=DATES[:-1] + DATES[:1]),
+               "short": _history_payload(dates=DATES[:2], closes=CLOSES[:2]),
+               "empty": _history_payload(dates=[], closes=[]),
+               "foreign_key": _history_payload(key="HIST_FMP_MSFT_30"),
+               "future_schema": _history_payload(v=99),
+               "bad_dates": _history_payload(dates=["x"] * 30)}
+        with _Env() as env:
+            for name, payload in bad.items():
+                (env.dir / "HIST_FMP_ABC_30.json").write_text(json.dumps(payload), "utf-8")
+                n = len(calls)
+                h = H._cached("FMP", fetch, "ABC", 30)
+                assert len(calls) == n + 1, f"{name}: a corrupt cache file must be refetched, not served"
+                assert all(math.isfinite(c) and c > 0 for c in h.closes) and list(h.dates) == sorted(set(h.dates))
+            (env.dir / "HIST_FMP_ABC_30.json").write_text(json.dumps(_history_payload()), "utf-8")   # legacy v1
+            n = len(calls)
+            assert "cached" in H._cached("FMP", fetch, "ABC", 30).note and len(calls) == n, "a valid v1 file is served"
+    finally:
+        H._READY.clear()
+        H._READY.update(saved[0])
+        H._may_be_trading, H._traded_since = saved[1:]
+
+
+test_c01_history_cache_refuses_corrupt_payloads.test_ids = ["C-01"]
+
+
+def test_c01_history_cache_never_persists_non_finite_and_writes_atomically():
+    import core.quant.history as H
+    saved = (H._READY.copy(), H._may_be_trading)
+    try:
+        H._READY["FMP"] = lambda: True
+        H._may_be_trading = lambda *a, **k: False
+        with _Env() as env:
+            H._cached("FMP", lambda s, days: H.History(s, "FMP", tuple(DATES), tuple(CLOSES[:-1] + [math.inf])),
+                      "INF", 30)
+            assert not (env.dir / "HIST_FMP_INF_30.json").exists(), "an inf close must never be written to the cache"
+            H._cached("FMP", lambda s, days: H.History(s, "FMP", tuple(DATES), tuple(CLOSES)), "OK", 30)
+            p = json.loads((env.dir / "HIST_FMP_OK_30.json").read_text("utf-8"))
+            assert p["v"] == H._CACHE_SCHEMA and p["key"] == "HIST_FMP_OK_30"
+            assert not list(env.dir.glob("*.tmp")), "no temp file left behind"
+    finally:
+        H._READY.clear()
+        H._READY.update(saved[0])
+        H._may_be_trading = saved[1]
+
+
+test_c01_history_cache_never_persists_non_finite_and_writes_atomically.test_ids = ["C-01"]
+
+
+def test_c01_ficc_cache_refuses_corrupt_payloads_and_states_retrieved_at():
+    import core.ficc.data as D
+    from core.ficc.common import FICCError
+    saved = (D._fred_fetch, D._MEM.copy())
+
+    def down(*a, **k):
+        raise RuntimeError("provider down")
+    try:
+        D._fred_fetch = down
+        rows = [[d, 4.0 + i / 100] for i, d in enumerate(DATES)]
+        with _Env() as env:
+            key = D._cache_key("FRED", "AUDIT", 30)
+            for name, bad in {"nan": rows[:-1] + [[DATES[-1], math.nan]], "inf": rows[:-1] + [[DATES[-1], math.inf]],
+                              "unsorted": rows[::-1], "duplicate": rows + [[DATES[0], 9.0]],
+                              "short": rows[:2]}.items():
+                (env.dir / f"{key}.json").write_text(json.dumps({"ts": time.time() - 60, "rows": bad}), "utf-8")
+                D._MEM.clear()
+                try:
+                    s = D.load_series("AUDIT", source="fred", days=30)
+                except FICCError:
+                    continue
+                raise AssertionError(f"{name}: served {s.values[-3:]} from a corrupt cache file")
+            ts = time.time() - 120
+            (env.dir / f"{key}.json").write_text(json.dumps({"ts": ts, "rows": rows}), "utf-8")
+            D._MEM.clear()
+            s = D.load_series("AUDIT", source="fred", days=30)
+            want = datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
+            assert s.source == "FRED" and s.retrieved_at == want, "a cache hit carries the file's retrieval instant"
+    finally:
+        D._fred_fetch = saved[0]
+        D._MEM.clear()
+        D._MEM.update(saved[1])
+
+
+test_c01_ficc_cache_refuses_corrupt_payloads_and_states_retrieved_at.test_ids = ["C-01"]
+
+
+def _fresh_kis_client():
+    """A private copy of data/krx/kis_client.py: the hermetic guard replaces `KISClient._get` on the shared module,
+    and this test needs the real one, talking to the fake session below and nothing else."""
+    import importlib.util
+    import sys
+    import data.krx.kis_client as shared
+    spec = importlib.util.spec_from_file_location("_c01_kis_client", shared.__file__)
+    mod = importlib.util.module_from_spec(spec)
+    sys.modules[spec.name] = mod                      # dataclasses resolve annotations through sys.modules
+    try:
+        spec.loader.exec_module(mod)
+    finally:
+        sys.modules.pop(spec.name, None)
+    return mod
+
+
+def test_c01_kis_token_is_scoped_and_dropped_when_refused():
+    K = _fresh_kis_client()
+    saved = (config.kis_ready, config.kis_credentials)
+    posts, gets = [], []
+
+    class R:
+        def __init__(self, status, body):
+            self.status_code, self._b, self.headers = status, body, {}
+
+        def json(self):
+            return self._b
+
+    class S:
+        def post(self, url, **kw):
+            posts.append(kw["json"]["appkey"])
+            return R(200, {"access_token": f"T{len(posts)}", "expires_in": 86400})
+
+        def get(self, url, headers=None, **kw):
+            gets.append(headers["authorization"])
+            if headers["authorization"] == "Bearer OLD":
+                return R(500, {"rt_cd": "1", "msg_cd": "EGW00123", "msg1": "expired"})
+            return R(200, {"rt_cd": "0", "output": {"stck_prpr": "70000"}})
+    try:
+        tmp = Path(tempfile.mkdtemp(prefix="c01_kis_"))
+        K._TOKEN_PATH = tmp / "kis_token.json"
+        K.requests = K._once = S()
+        K._pace = lambda: None
+        config.kis_ready = lambda: True
+        config.kis_credentials = lambda: ("KEY_A", "SECRET")
+        c = K.KISClient()
+        K._TOKEN_PATH.write_text(json.dumps({"access_token": "OLD", "scope": c._scope(),
+                                             "expires_at": time.time() + 3600}), "utf-8")
+        try:
+            c.quote("005930")                       # the live quote makes one attempt (retry=False) ...
+        except K.KISError as exc:
+            assert "EGW00123" in str(exc)
+        else:
+            raise AssertionError("the refused call itself still fails")
+        assert not K._TOKEN_PATH.exists() and posts == [], "... but the refused token is dropped at once"
+        q = c.quote("005930")                       # ... so the next call mints a new token and succeeds
+        assert q.price == 70000.0 and gets == ["Bearer OLD", "Bearer T1"] and posts == ["KEY_A"]
+        gets.clear()
+        K._TOKEN_PATH.write_text(json.dumps({"access_token": "OLD", "scope": c._scope(),
+                                             "expires_at": time.time() + 3600}), "utf-8")
+        c._get("/uapi/domestic-stock/v1/quotations/inquire-price", "FHKST01010100", {})   # retry=True path
+        assert gets == ["Bearer OLD", "Bearer T2"] and posts == ["KEY_A", "KEY_A"], "retried once with a new token"
+        assert "OLD" not in K._TOKEN_PATH.read_text("utf-8")
+        config.kis_credentials = lambda: ("KEY_B", "SECRET")
+        assert K.KISClient().token() == "T3" and posts[-1] == "KEY_B", "a rotated app key mints its own token"
+        assert K.KISClient(base_url="https://openapivts.koreainvestment.com:29443").token() == "T4"
+        assert "KEY_" not in K._TOKEN_PATH.read_text("utf-8"), "the scope is a digest, never the key"
+        if os.name == "posix":
+            assert (K._TOKEN_PATH.stat().st_mode & 0o077) == 0, "the token file is owner-only"
+    finally:
+        config.kis_ready, config.kis_credentials = saved
+
+
+test_c01_kis_token_is_scoped_and_dropped_when_refused.test_ids = ["C-01"]
+
+
+def test_c01_dry_run_reads_retrieval_from_the_manifest_not_the_mtime():
+    """Synthetic vendor files; the same bytes with two different mtimes give the same PIT stamps when RETRIEVAL.json
+    pins the instant; without it the newest row is withheld (it may have been a running bar)."""
+    import hashlib
+    import core.skills.macro_daily as MD
+    saved = MD.DRY_RUN_CACHE
+    try:
+        src = Path(tempfile.mkdtemp(prefix="c01_dry_"))
+        days, d = [], date(2026, 10, 6)
+        while len(days) < 300:
+            if d.weekday() < 5:
+                days.append(d)
+            d -= timedelta(days=1)
+        days.reverse()
+        MD.DRY_RUN_CACHE = {"KRX_069500_OFFICIAL_CLOSE": ("syn_069500.csv", "Yahoo")}
+        f = src / "syn_069500.csv"
+        f.write_text("Date,v\n" + "\n".join(f"{x.isoformat()},{30000 + i}" for i, x in enumerate(days)), "utf-8")
+        U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
+        (src / MD.RETRIEVAL_FILE).write_text(json.dumps({"syn_069500.csv": {
+            "retrieved_at_utc": "2026-10-06T22:00:00Z", "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}}), "utf-8")
+        seen = []
+        for mtime in (U(2026, 10, 6, 22), U(2026, 10, 27, 3)):
+            os.utime(f, (mtime.timestamp(), mtime.timestamp()))
+            out = MD.dry_run(Path(tempfile.mkdtemp()), clock=lambda: U(2026, 10, 7, 9), cache_dir=src, markets=())
+            seen.append(out["ingested"]["KRX_069500_OFFICIAL_CLOSE"])
+        assert seen[0] == seen[1] and seen[0]["retrieved_at_source"] == "manifest", seen
+        (src / MD.RETRIEVAL_FILE).unlink()
+        out = MD.dry_run(Path(tempfile.mkdtemp()), clock=lambda: U(2026, 10, 7, 9), cache_dir=src, markets=())
+        rec = out["ingested"]["KRX_069500_OFFICIAL_CLOSE"]
+        assert rec["retrieved_at_source"] == "mtime" and rec["appended"] == seen[0]["appended"] - 1, rec
+    finally:
+        MD.DRY_RUN_CACHE = saved
+
+
+test_c01_dry_run_reads_retrieval_from_the_manifest_not_the_mtime.test_ids = ["C-01"]
+
+
+def test_v01_kimchi_premium_reports_and_caps_fx_age():
+    from core.crypto.analytics import kimchi_premium
+    end = date(2026, 10, 26)
+    ds = [(end - timedelta(days=i)).isoformat() for i in range(200)][::-1]
+    usd = {d: 60000.0 for d in ds}
+    krw = {d: 60000.0 * 1400.0 * 1.02 for d in ds}
+    fx = {d: 1400.0 for d in ds if date.fromisoformat(d).weekday() < 5 and d <= "2026-10-16"}
+    k = kimchi_premium(krw, usd, fx)
+    assert k.fx_age_days_last == 10 and "10 day(s) old" in k.note, "the FX age is stated, not 'a few hours'"
+    k4 = kimchi_premium(krw, usd, fx, max_fx_age_days=4)
+    assert k4.dates[-1] == "2026-10-20" and k4.fx_stale_dropped == 6 and k4.fx_age_days_max <= 4
+
+
+test_v01_kimchi_premium_reports_and_caps_fx_age.test_ids = ["V-01"]
+
+
+def test_v01_vendor_compare_selftest():
+    from tools import vendor_compare as VC
+    assert VC.selftest(Path(tempfile.mkdtemp(prefix="v01_"))) == [], "the harness must catch every planted defect"
+
+
+test_v01_vendor_compare_selftest.test_ids = ["V-01"]
+
+
+def tests():
+    return [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
+
+
+if __name__ == "__main__":
+    from tests.macro_acceptance import run_module
+    raise SystemExit(run_module(globals()))
```

