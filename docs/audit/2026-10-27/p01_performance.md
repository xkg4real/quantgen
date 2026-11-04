# P-01 성능 감사 보고서: 다자산 순차 호출, KIS 페이지 반복, 캐시, 계산·렌더 시간

- 감사일: 2026-10-27
- 대상: `/home/user/quantgen`. 감사 중 HEAD가 `527cdf2`에서 `859a983`으로 바뀌었다. 두 커밋은 문서만 추가했고 코드 차이는 없다(`git diff --stat 527cdf2..859a983`, 9개 파일 모두 `docs/`).
- 방식: 감사만 했다. 추적 파일은 고치지 않았다. 수정안은 아래 diff로만 제시한다(요청서 7절 8항).
- 비밀정보: `.env`를 열지 않았다. 키·토큰을 출력하지 않았다. 계측 하네스는 가짜 자격증명(`DUMMY`)만 쓴다.
- 네트워크: 시세 공급자에 실호출을 하지 않았다. 모든 시간은 오프라인 하네스에서 지연을 주입해 잰 값이다.
- 측정 환경: 클라우드 Linux, 4 vCPU(Intel Xeon 2.10GHz), Python 3.13.17, numpy 2.3.5, scipy 1.18.0, flet 0.85.2, matplotlib 3.11.2, yfinance 1.7.0, pandas_datareader 0.11.1. 소유자 Windows PC의 숫자와 다를 수 있다.

## 0. 요약

1. 요청서 P-01의 세 주장은 코드로 확인했다(사실). 포트폴리오(`ui/portfolio_page.py:111`)와 Strategy Lab(`ui/strategy_lab_page.py:104`)은 자산을 하나씩 순서대로 받는다. KIS 이력은 100행씩 페이지를 거슬러 받는다(`core/quant/history.py:203-220`).
2. 측정 결과, 가장 큰 대기는 두 종류다.
   - **KIS 요청 간격.** 모든 KIS 호출은 프로세스 전체에서 0.12초 간격으로 줄 선다(`data/krx/kis_client.py:83-95`). 그래서 지연이 0이어도 바닥 시간이 있다. KRX 20종목·504일은 120건, 14.3초다. Strategy Lab 기본값(5000일)은 891건, 107초(지연 0), 136초(지연 150ms)다. 파생 화면 옵션체인은 실행마다 320건, 38.4초가 바닥이다. 동시성으로 줄여도 바닥(요청 수 × 0.12초) 아래로는 못 간다. 간격 잠금이 전역이다(측정: 작업자 4개로 136 → 107초).
   - **Strategy Lab의 CPU 계산.** `pbo_cscv`가 실행 1회에 7.6~9.9초를 쓴다(캐시가 따뜻해도 같다). 실행 시간의 약 88%다(프로파일 11.83초 중 10.37초). 결과를 바꾸지 않는 벡터화 시안은 0.14~0.28초다. 기존 결과와 `pbo`·`prob_loss`가 완전히 같고 `slope` 차이는 3e-15 이하다.
3. FMP·Yahoo는 요청 수 × 지연으로 늘어난다(20종목, 150ms: 3.1초). 작업자 4개의 제한 동시성 시안은 0.8초다. 18개 시나리오 모두 결과 해시가 순차 실행과 같았다.
4. 캐시는 효과가 크다. 같은 입력 두 번째 실행은 20종목·5000일도 0.05초 이하, 요청 0건이다. 다만 캐시 키에 `days`가 들어가서 화면마다 창 길이가 다르면 다시 받는다(504 → 5000 → 4000 각각 5건 재요청).
5. 화면 전환 시 페이지 생성은 0.3~9ms이고 네트워크를 쓰지 않는다(16개 페이지). 네트워크 작업은 모두 `page.run_thread` 작업자 안에 있다. UI 스레드 차단은 찾지 못했다.
6. 범위 밖이지만 계측 중 확인한 결함 두 가지를 적는다. Strategy Lab Run은 차트에서 항상 `ValueError`로 멈춘다(FC-01과 같은 결함, 독립 재현). 전액 현금 구간의 Sharpe가 부동소수 잡음 때문에 약 3.5e16이 되어 walk-forward가 그 설정을 고른다(함수 수준 재현).
7. Flet 클라이언트의 실제 그리기 시간, 실제 공급자 지연, KIS·FMP·Yahoo의 공식 호출 한도는 여기서 잴 수 없었다(8절 미검증). 소유자 PC용 계측 스크립트와 명령을 7절과 부록 B에 둔다.

## 1. 범위

- 요청서 4절 P-01과 5절(속도 감사 계획) 전부.
- 대상 경로: 포트폴리오, Strategy Lab, 파생(옵션체인), ETF, FX 캐리, 크립토, 매크로 시트, 앱 시작, 페이지 생성.
- 코드: `core/quant/history.py`(라우팅·캐시·KIS 페이지), `data/krx/kis_client.py`(간격·재시도), `data/kis_markets.py`(KIS 페이지·옵션체인), `data/crypto/crypto_client.py`, `core/ficc/data.py`(Yahoo·FRED·FICC 캐시), `data/net.py`(재시도), `core/quant/validate.py`(PBO), `ui/*.py`, `main.py`.
- 제외: `paper_live/`, `grokteam/`(규칙상 열지 않음). 엔진 시세 폴링(`core/engine/feed.py`)의 틱 지연은 보지 않았다.
- 소유자 메모 "(-> 공급사필요)"와 "(-> FICC/BTC 모두 KIS에서 접근 가능한지 …)"는 공급자 선정 문제다. 이 차원에서는 성능 측면만 다룬다. KIS는 호출 간격이 병목이라 FICC·BTC 이력을 KIS로 옮기면 대기 시간이 늘 것으로 본다(추정: 0.12초/건, 해외선물 `ovf_daily`는 40행/건, `data/kis_markets.py:514-540`. P01-03, P01-04). 공급자 판단은 `c01_v01_cache_and_vendors.md`가 맡는다.

## 2. 방법

### 2.1 원칙

- 계측 없이 속도 문제를 확정하지 않았다(요청서 7절 5항). 아래 모든 시간은 하네스에서 측정했다. 요청 수 공식은 코드에서 유도했고 측정으로 확인했다.
- 실네트워크 대신 지연 주입: 공유 HTTP 세션 `data.net.session.get`(FMP·KIS·Upbit·Binance가 모두 이 객체를 쓴다)을 가짜로 바꿨다. 가짜는 요청마다 N ms를 쉬고 실제 응답 모양의 JSON을 돌려준다. Yahoo(`core.ficc.data._yf_fetch`)와 FRED(`_fred_fetch`)도 같은 방식이다.
- 데이터: `docs/asset_expansion/cache`의 CSV(QQQ, TLT, GLD, XL* 등). 금지 파일 4개(`yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`)는 이름으로 거부했고 열지 않았다. BTC 경로는 시드 고정 합성 가격을 썼다. `yf__KS200.csv`는 1행뿐이라 KOSPI200 지수 경로에는 `yf_069500.KS.csv`를 대신 썼다(시간 측정용).
- 격리: `HOME`, `NEXTGEN_FICC_CACHE`, `QUANTGEN_MACRO_DIR`, `MPLCONFIGDIR`를 작업 폴더로 돌렸다. 토큰·캐시·시행 장부는 저장소와 실제 홈에 쓰이지 않았다. `python3 -B`로 실행했다. 실행 후 `git status`에 이 감사가 만든 변경은 이 보고서 하나뿐이다.
- KIS 토큰은 `KISClient.token`을 더미로 바꿨다. KIS 간격 함수 `_pace`는 감싸서 대기 시간만 따로 쟀다. 원래 동작(0.12초 간격, 잠금)은 그대로다.

### 2.2 시간 분해

| 항목 | 정의 |
|---|---|
| 요청 수, 응답 크기 | 가짜 세션이 센 HTTP 요청 수와 JSON 바이트 |
| 네트워크 대기 | 주입한 지연의 합 |
| KIS 간격 대기 | `_pace` 안에서 쉰 시간의 합(크립토는 `_throttle`) |
| 파싱/CPU | 전체 fetch 시간 − 네트워크 − 간격 − 가짜 응답 생성 시간 |
| 계산 | `align_histories`, `optimize_portfolio`×4, `efficient_frontier`, `pnl_matrix`, `walk_forward`, `score_strategy` 등 페이지가 부르는 함수를 그대로 감싸서 잰 시간 |
| 렌더 | matplotlib PNG 생성 + Flet 컨트롤 생성(작업자 스레드). Flet 클라이언트의 그리기는 잴 수 없음(8절) |
| cold / warm | 빈 캐시에서 첫 실행 / 같은 입력의 두 번째 실행 |

### 2.3 요청 수 공식(코드 유도, 측정으로 확인)

| 경로 | 공식 | 근거 | 측정 |
|---|---|---|---|
| `kis_history(code, days)` | 약 ⌈days/100⌉쪽, 최대 `days//100+3` | `core/quant/history.py:203` | 504일 6건, 5000일 50건 |
| KIS 요청 1건의 최소 시간 | `max(지연, 0.12초)` | `data/krx/kis_client.py:83-95` | 지연 0에서 요청당 0.12초 |
| `option_chain(..., include_book=True)` | 시리즈당 2건, 시리즈 ≤ 160 | `data/kis_markets.py:392-430` | 320건, 38.4초 |
| `index_daily("2001", days=600)` | 50행/쪽, 약 12건 | `data/kis_markets.py:437-450` | 12건, 1.45초 |
| FMP 이력 | 종목당 1건 | `core/quant/history.py:133` | 일치 |
| Yahoo 이력(`yf_history`) | 종목당 `_yf_fetch` 1회 | `core/quant/history.py:272` | 일치 |
| `_yf_fetch([...])` 여러 종목 | 1회 호출이지만 HTTP는 종목 수만큼 순차 | `core/ficc/data.py:200`(`threads=False`), 설치된 yfinance 1.7.0 `_download_impl`의 `for i, ticker in enumerate(tickers): _download_one(...)` | 소스 확인 |
| `_fred_fetch([...])` | HTTP는 id 수만큼 순차 | `core/ficc/data.py:177`(requests 경로), pandas_datareader 0.11.1 `FredReader`의 `[fetch_data(url, n) for url, n in zip(urls, names)]` | 소스 확인 |

## 3. 요청서 주장 검증

| 요청서 주장 (P-01, 5절) | 판정 | 근거 |
|---|---|---|
| `ui/portfolio_page.py`에 여러 자산 이력을 순차 호출하는 경로가 있다 | 사실 | `ui/portfolio_page.py:111` `hists = [load_history(s, source=...) for s in syms]` |
| `ui/strategy_lab_page.py`에도 같은 경로가 있다 | 사실 | `ui/strategy_lab_page.py:104` `hists = [load_history(s, source=source, days=days) for s in symbols]` |
| KIS 이력은 구간 확보를 위해 반복 페이지 요청을 할 수 있다 | 사실 | `core/quant/history.py:203-220`(최대 `days//100+3`쪽), `data/kis_markets.py:180-205`(`_page_back`, 최대 `days//30+4`쪽). 측정: 504일 6쪽, 5000일 50쪽 |
| 종목 수와 네트워크 지연에 따라 대기시간이 누적될 가능성 | 사실(측정) | FMP·Yahoo: 시간 ≈ 종목 수 × 지연(4.1절). KIS: 지연과 무관한 0.12초/건 바닥이 추가로 있다 |
| (함의) 병목은 네트워크다 | 보완 | Strategy Lab은 캐시가 따뜻해도 7.4~9.7초가 걸린다. 원인은 CPU(`pbo_cscv`)다(P01-02). 요청서에 없던 병목이다 |
| 다른 화면에도 순차 경로가 있는가(요청서 미기재) | 사실 | `ui/fx_page.py:309-311`(통화쌍 7개 + 정책금리 8개), `ui/crypto_page.py:45-57`(요청 11~12건), `ui/etf_page.py:48-67, 97`, `ui/derivatives_page.py:59-73` |
| 3절 "UI 성능 계측은 아직 완료되지 않았다" | 사실(일부 해소) | 작업자 스레드의 fetch·계산·PNG 렌더는 이번에 쟀다. Flet 클라이언트 그리기는 여전히 미검증 |
| P-01 조치안 "요청 병합" | 보완 | Yahoo·FRED의 "한 번에 받기"(`load_many`)는 함수 호출 1회일 뿐이다. 실제 HTTP는 종목/ID마다 순차로 나간다(2.3절). 병합만으로는 대기가 줄지 않는다. 줄이려면 제한 동시성이 필요하다 |

## 4. 측정 결과

### 4.1 이력 수집 단계(`load_history`), cold 기준

`bench_fetch.py`. 단위 초. "요청"은 HTTP 요청 수. 괄호는 작업자 4개 동시성 시안(150ms에서만 측정). warm은 모든 경우 0.05초 이하, 요청 0건.

**days=504 (포트폴리오 기본값)**

| 공급자 | 종목 | 요청 | 응답 크기 | 지연 0 | 50ms | 150ms (동시 4) | 300ms | 파싱/CPU |
|---|---|---|---|---|---|---|---|---|
| FMP | 1 | 1 | 96 KB | 0.016 | 0.055 | 0.156 (0.156) | 0.306 | 0.003~0.008 |
| FMP | 5 | 5 | 482 KB | 0.042 | 0.278 | 0.775 (0.312) | 1.532 | 0.011~0.017 |
| FMP | 20 | 20 | 1.92 MB | 0.298 | 1.146 | 3.109 (0.808) | 6.134 | 0.058~0.081 |
| KIS | 1 | 6 | 156 KB | 0.604 | 0.770 | 0.986 (0.917) | 1.819 | 0.006~0.009 |
| KIS | 5 | 30 | 781 KB | 3.488 | 3.653 | 4.635 (3.800) | 9.066 | 0.025~0.048 |
| KIS | 20 | 120 | 3.11 MB | 14.306 | 14.463 | 18.336 (14.464) | 36.276 | 0.117~0.180 |
| Yahoo | 1 | 1 | — | 0.001 | 0.051 | 0.152 (0.153) | 0.302 | 0.001 |
| Yahoo | 5 | 5 | — | 0.008 | 0.261 | 0.759 (0.306) | 1.512 | 0.007~0.011 |
| Yahoo | 20 | 20 | — | 0.026 | 1.045 | 3.041 (0.770) | 6.038 | 0.017~0.035 |

KIS 지연 0에서 간격 대기는 14.04초다(전체의 98%). 지연 50ms에서는 간격 8.15초 + 네트워크 6.0초다.

**days=5000 (Strategy Lab 기본값)**

| 공급자 | 종목 | 요청 | 응답 크기 | 지연 0 | 150ms (동시 4) | 파싱/CPU | 받은 세션 |
|---|---|---|---|---|---|---|---|
| FMP | 1 | 1 | 0.99 MB | 0.071 | 0.200 (0.205) | 0.019~0.036 | 5000 |
| FMP | 5 | 5 | 4.60 MB | 0.161 | 0.944 (0.475) | 0.084~0.100 | 5000 |
| FMP | 20 | 20 | 19.3 MB | 0.844 | 3.872 (1.333) | 0.43~0.46 | 5000 |
| KIS | 1 | 50 | 1.49 MB | 5.896 | 7.789 (7.713) | 0.05~0.07 | 5000 |
| KIS | 5 | 244 | 7.27 MB | 29.217 | 37.410 (30.757) | 0.24~0.32 | 5000 |
| KIS | 20 | 891 | 25.9 MB | 107.018 | 136.436 (107.475) | 0.86~1.45 | 5000 |
| Yahoo | 20 | 20 | — | 0.054 | 3.083 (0.796) | 0.05~0.07 | **2514** |

- 파싱 CPU는 26 MB를 받아도 1.5초 이하다. 수집 단계 시간은 네트워크와 KIS 간격이 정한다.
- 동시성 시안 18개 시나리오 모두 결과 해시(기호·출처·조정기준·날짜·종가)가 순차 실행과 같았다(`pool4_identical = True`).
- KIS는 동시성이 있어도 간격(0.12초 × 891 = 106.9초)에 막힌다.
- Yahoo 5000일 요청은 2514세션만 왔다. `_period_for(5000)`이 `"10y"`를 돌려주기 때문이다(P01-10).

### 4.2 화면 파이프라인

`bench_screens.py`, FMP 지연 150ms. 단위 초.

**포트폴리오** (페이지 상한 15종목, `ui/portfolio_page.py:106`)

| 종목 | fetch(요청) | align | 최적화 4종 | 효율적 경계 | 차트 2개 | 컨트롤 | PNG data URI | 페이지 작업자 전체 | warm 전체 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.347 (2) | 0.001 | 0.008 | 0.047 | 0.485 | 0.001 | 99 KB | 0.68 | 0.44 |
| 5 | 0.813 (5) | 0.002 | 0.026 | 0.217 | 0.368 | 0.002 | 182 KB | 1.44 | 0.62 |
| 15 | 2.478 (15) | 0.004 | 0.093 | 1.352 | 1.223 | 0.005 | 340 KB | 4.34 | 2.17 |

- "페이지 작업자 전체"는 실제 `build_portfolio_page`의 Optimize 버튼을 가짜 페이지로 누른 값이다. 단계 합과 맞는다.
- 15종목에서는 warm에도 2.2초가 남는다. 경계 1.35초, 상관 히트맵 0.92초다. 지금은 수정 대상으로 보지 않는다(관찰).
- KRX 코드(KIS)로 바꾸면 fetch만 2종목 1.85초(12건), 5종목 4.59초(30건), 15종목 13.72초(90건)다.

**Strategy Lab** (`run_family`, days=5000, bootstrap_B=1000, 그리드 12)

| 계열·종목 | cold 전체 | fetch(요청) | pnl_matrix | walk_forward | 장부 | score_strategy | 차트 | warm 전체 |
|---|---|---|---|---|---|---|---|---|
| trend_switch 1 | 10.44 | 0.40 (1) | 0.023 | 0.007 | 0.077 | **9.93** | 0.11 | 9.71 |
| trend_switch 5 | 8.80 | 1.04 (5) | 0.034 | 0.008 | 0.038 | **7.66** | 0.11 | 7.71 |
| trend_switch 20 | 12.74 | 4.02 (20) | 0.055 | 0.007 | 0.061 | **8.54** | 0.12 | 8.56 |
| xs_momentum 5 | 8.93 | 0.97 (5) | 0.035 | 0.006 | 0.021 | **7.88** | 0.11 | 8.34 |
| xs_momentum 20 | 12.05 | 3.96 (20) | 0.044 | 0.008 | 0.051 | **7.93** | 0.11 | 7.41 |

- cold와 warm의 결과(decision, SR, DSR, PBO)는 모두 같았다.
- 차트 시간은 날짜를 한 칸 맞춘 호출로 쟀다. 페이지의 실제 호출(`ui/strategy_lab_page.py:273`)은 매번 `ValueError`다(P01-01).
- cProfile(`profile_score.py`, 5종목): 전체 11.83초 중 `pbo_cscv` 10.37초, `_col_sharpe` 25,775회 호출 8.05초, `sharpe_diff_bootstrap` 0.60초, `block_bootstrap_ci` 0.52초.

### 4.3 KIS 경로 (`bench_kis.py`)

| 호출 | 요청 | 지연 0 | 지연 30ms | 간격 대기(30ms) |
|---|---|---|---|---|
| `option_chain` spot 1126, ±10%, 2.5pt, book=True | 320 | 38.36 | 38.50 | 28.75 |
| 같은 조건, book=False | 160 | 19.24 | 19.24 | 14.36 |
| spot 800, book=True | 260 | 31.26 | 31.26 | 23.34 |
| spot 800, book=False | 130 | 15.63 | 15.63 | 11.67 |
| `index_daily("2001", 600)` | 12 | 1.45 | 1.45 | 1.07 |
| `kis_history("005930", 504)` | 6 | 0.72 | 0.72 | 0.53 |
| `kis_history("005930", 5000)` | 50 | 6.01 | 6.02 | 4.37 |

- 옵션 마스터는 2.5pt 전 구간 격자로 바꿔 넣었다. 그래서 시리즈 수는 코드 상한(160)에 닿았다. 실제 상장 행사가 수는 마스터에 따라 다르다(추정).
- 지연 30ms에서도 시간이 같다. 간격(0.12초)이 지배한다.

### 4.4 캐시·중복 요청 (`bench_cache.py`)

| 점검 | 결과 |
|---|---|
| 같은 5종목, days 504 → 5000 → 4000 → 504 | 요청 5 → 5 → 5 → 0. 바이트 0.48 MB → 4.60 MB → 3.81 MB → 0 |
| 포트폴리오 Optimize 두 번 클릭(첫 실행 중) | 작업자 2개, 요청 10건(5종목). 버튼 비활성화 없음 |
| 같은 기호 중복(`QQQ, QQQ, TLT`) | 네트워크 2건(두 번째 QQQ는 캐시 적중). 상관행렬 행렬식 2.2e-16(특이). 가중치 0.098 / 0.098 / 0.804 |
| 장중 판정 `_may_be_trading`이 참인 비율(1주, 15분 간격) | FMP 미국 티커·KIS KRX·Yahoo `.KS`·KIS 해외: 22.3%. Yahoo 일반 티커(TLT)·선물(GC=F)·지수(^VIX): **73.2%**. 크립토: 100% |
| `_traded_since` 비용 | 호출당 0.01~1.2 ms(6시간·3일·30일 묵은 파일). 문제 없음 |

참이면 새로 받은 시계열은 10분만 캐시된다(`core/quant/history.py:435`). 거짓이면 6시간이다.

### 4.5 FICC·크립토·매크로 (`bench_ficc.py`, `bench_macro.py`, 지연 150ms)

| 경로 | cold | warm |
|---|---|---|
| FX 캐리 `do_carry` (`ui/fx_page.py:309-311`) | 2.29초. 공급자 호출 15회 = Yahoo 7 + FRED 8. 실제 HTTP = Yahoo 7 + FRED 12 | 0초, 0건 |
| 크립토 `_live(730)` (`ui/crypto_page.py:45-57`) | 1.89초, 12건(Upbit 4, Binance 캔들 2, 펀딩 3, 프리미엄 1, OI 1, FRED 1) | 1.74초, 11건. 캔들 캐시가 없다 |
| 매크로 시트 `macro_sheet` | 공급자 호출 FRED 1 + Yahoo 1. 실제 HTTP = FRED 16 + Yahoo 2, 순차 | 0초, 0건 |

### 4.6 앱 시작·페이지 생성 (`bench_startup.py`)

- `import main`(창을 열기 전 임포트): 3.00 / 2.90 / 3.11초(새 인터프리터 3회).
- `-X importtime` 상위: `ui.bonds_page` 누적 1.81초(그 안의 `core.ficc.insights` → `core.quant.insights` 1.20초 → `core.quant.garch` 0.76초 → `scipy.stats._stats_py` 0.47초). `flet` 0.58초. `ui.qcharts` 0.34초(`matplotlib.pyplot` 0.25초). `core.ficc.data` 0.23초(`yfinance` 0.22초).
- 16개 페이지 생성 시간: 0.3~9.0ms(최대 Strategy Lab 9.0ms, 카드 JSON 읽기). 생성 중 네트워크 요청 0건.
- 정적 확인: 네트워크를 쓰는 처리(`load_history`, `KISMarkets`, `load_*`, `macro_sheet`, `gateway.*`, 설정 점검)는 모두 `page.run_thread` 작업자 안에 있다. `ui/*.py`의 `page.run_thread(` 호출 20곳을 확인했다.

## 5. 발견사항

### 5.1 요약 표

| ID | 심각도 | 판정 | 파일·라인 | 한 줄 요약 |
|---|---|---|---|---|
| P01-01 | P1 | 사실 | `ui/strategy_lab_page.py:241-277, 273`, `ui/xcharts.py:76-78` | Strategy Lab Run은 렌더 단계에서 항상 `ValueError`로 멈춘다(FC-01과 동일, 독립 재현) |
| P01-02 | P2 | 사실(측정) | `core/quant/validate.py:240-271, 508` | `pbo_cscv`(S=16)가 Strategy Lab 실행마다 7.6~9.9초 CPU를 쓴다. 같은 결과의 벡터화로 0.14~0.28초 |
| P01-03 | P2 | 사실(측정) | `core/quant/history.py:192-226`, `data/krx/kis_client.py:83-95` | KIS 이력은 100행/쪽 × 전역 0.12초 간격. 20종목 504일 14.3초, 5000일 107~136초. 동시성으로도 바닥(건수×0.12초)은 그대로 |
| P01-04 | P2 | 사실(측정); 실제 시리즈 수는 추정 | `ui/derivatives_page.py:59-73`, `data/kis_markets.py:392-430, 437-450` | 파생 Run 1회에 KIS 약 335건, 바닥 약 40초. 캐시 없음 |
| P01-05 | P2 | 사실(측정) | `ui/portfolio_page.py:95-200`, `ui/strategy_lab_page.py:227-279` 외 13개 화면 | 실행 중 재클릭을 막지 않는다. 두 번 누르면 요청 2배, 작업자 2개가 같은 화면을 쓴다 |
| P01-06 | P3 | 사실(측정) | `ui/portfolio_page.py:111`, `ui/strategy_lab_page.py:104` | FMP·Yahoo 순차 수집: 시간 ≈ 종목 × 지연. 작업자 4개 시안 3.1 → 0.8초, 결과 동일 |
| P01-07 | P3 | 사실(측정) | `core/quant/history.py:427` | 캐시 키에 `days`가 있어 긴 창의 파일이 짧은 창을 대신하지 못한다 |
| P01-08 | P3 | 사실(측정) | `core/quant/history.py:371-387` | Yahoo 일반 티커는 한 주의 73.2% 동안 10분 TTL. 같은 ETF를 FMP로 받으면 22.3%(C01-07의 계측) |
| P01-09 | P3 | 사실(측정) | `data/kis_markets.py:437-450`, `ui/crypto_page.py:45-57`, `core/ficc/data.py:177, 200` | 지수 이력·크립토 캔들은 캐시가 없다. Yahoo·FRED "일괄"은 HTTP 순차다 |
| P01-10 | P3 | 사실(코드); 실제 행 수는 추정 | `core/ficc/data.py:435-440`, `core/quant/history.py:272` | Yahoo는 10년이 상한이라 Sessions 5000이 약 2,515세션이 된다(범위 밖: 데이터 완전성) |
| P01-11 | P3 | 사실(함수 수준); 실데이터 발생은 추정 | `core/quant/validate.py:268-270, 372` | 전액 현금 구간의 Sharpe가 약 3.5e16이다. walk-forward가 그 설정을 고른다(범위 밖: 금융 계산) |
| P01-12 | P3 | 사실(측정) | `ui/portfolio_page.py:102-111` | 중복 기호를 지우지 않아 상관행렬이 특이해진다(범위 밖: 입력 검증) |
| P01-13 | P3 | 사실(측정, 클라우드) | `main.py:51-66` | 앱 임포트 약 3초. 모든 페이지 모듈을 시작 시 임포트한다 |

### 5.2 상세

#### P01-01 · P1 · 사실 — Strategy Lab Run은 렌더에서 항상 멈춘다

| 항목 | 내용 |
|---|---|
| ID | P01-01 (`functional_completeness.md`의 FC-01과 같은 결함. 이 차원에서는 렌더 시간을 재다가 독립 재현했다) |
| 심각도 | P1 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/strategies.py:93-94` `equity_curve`는 `[1.0] + cumprod`라 P&L보다 1점 길다. `ui/strategy_lab_page.py:130` `eq = S.equity_curve(wf.pnl)`. `:273` `xc.equity_chart(r["wf"].dates, r["equity"], ...)`. `ui/xcharts.py:76-78` `x = np.arange(len(dates))`, `ax.plot(x[-eq.size:], eq)`는 n개 x와 n+1개 y를 그리려 한다. 작업자의 try(`:231-240`)는 `run_family`만 감싸고 렌더(`:241-277`)는 감싸지 않는다 |
| 재현 단계 | `python3 -B repro_lab_chart.py` (5절 경로). 합성 데이터, 네트워크 없음 |
| 기대 결과 | 차트·통계·분석 패널이 나오고 진행 링이 꺼진다 |
| 실제 결과 | `len(wf.dates)=722, len(equity)=723`. `ValueError: x and y must have same first dimension, but have shapes (722,) and (723,)`. 예외가 작업자 밖으로 나가고 `busy.visible`이 `True`로 남는다. `bench_screens.py`의 5개 시나리오(FMP 가짜 데이터)에서도 매번 같은 오류 |
| 영향 | Run 결과가 한 번도 표시되지 않는다. 실데이터면 `register_trials`(`:118`)가 먼저 장부에 시행을 남긴다. 이용자가 다시 누르면 수집·계산(8~13초, KIS면 수십~수백 초)을 반복한다. 기존 `expansion/selfcheck_strategy_lab`은 PASS지만 차트를 부르지 않는다 |
| 수정안 | FC-01의 diff를 채택한다. 요지: (1) `equity_chart`가 날짜보다 1점 긴 곡선을 받아들인다. 예: `n = max(len(dates), eq.size, 0 if bench is None else len(bench))`, `x = np.arange(n)`, 눈금은 `n - len(dates)`만큼 민다. ETF 화면(`ui/etf_page.py:238`)은 길이가 같아 출력이 그대로다. (2) 렌더 블록을 try/except로 감싸 실패를 오류 안내로 바꾸고 링을 끈다 |
| 회귀 테스트 | `tests/macro_ui_views.py::test_strategy_lab_run_renders_on_synthetic`: 가짜 페이지(`run_thread`가 즉시 실행)로 `trend_switch`, `AAA, BBB, CCC`, `synthetic`, 1500일, 5bp를 Run한다. `assert busy.visible is False`, 결과 영역에 `ft.Image` 1개 이상, 오류 `notice` 없음. FC-01의 세 테스트와 같은 취지 |

#### P01-02 · P2 · 사실(측정) — `pbo_cscv`가 Strategy Lab 실행 시간의 대부분이다

| 항목 | 내용 |
|---|---|
| ID | P01-02 |
| 심각도 | P2 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `core/quant/validate.py:240-265` `pbo_cscv`: 분할마다 `_col_sharpe(M[tr])`, `_col_sharpe(M[te])`. `:508` `S=8 if len(full_pnl) < 2000 else 16`. S=16이면 C(16,8)=12,870 분할, `_col_sharpe` 25,740회. Strategy Lab 기본 5000세션은 늘 S=16이다 |
| 재현 단계 | (1) `python3 -B bench_screens.py --lat 0.15`: `score_strategy` 열. (2) `python3 -B profile_score.py trend_switch 5`: cProfile. (3) `python3 -B final_pbo_check.py`: 제안 구현 대 현재 구현 |
| 기대 결과 | 검증 게이트 계산이 수집보다 짧거나 비슷하다 |
| 실제 결과 | `score_strategy` 7.66~9.93초(5개 시나리오). warm에서도 7.4~9.7초. 프로파일 11.83초 중 `pbo_cscv` 10.37초(88%). 순수 numpy 호출 오버헤드(`std`·`mean` 각 약 2.6만 회)다 |
| 영향 | Strategy Lab Run마다 약 8~10초가 이 함수에서 나간다. 같은 함수를 쓰는 연구 스크립트(`docs/build_expansion_primer.py:147` 등)도 같다. P01-01을 고치면 이 대기가 화면에 그대로 드러난다 |
| 수정안 | 부록 A-1 diff. 블록별 합·편차제곱합을 한 번 구하고, 모든 분할의 평균·분산을 행렬곱으로 만든다(Chan 등의 합동 분산, 편차를 직접 계산해 `n·mean²` 상쇄를 피함). 측정: 현재 5.12~10.26초 → 제안 0.14~0.28초(24~67배). 9개 입력(T-PBO-01 레시피, 시드 난수 3개, 캐시 데이터의 5개 계열)에서 `pbo`·`prob_loss` 완전 일치, `slope` 차이 ≤ 3.1e-15. T-PBO-01 레시피는 6897/12870 그대로. 참고: `core/quant/gate_stats.py:686-695`에 이미 합 기반 빠른 경로가 있다. 다만 비중심 제곱합(`s2 − n·mean²`, `gate_stats.py:627`)이라 평탄한 열에서 상쇄 오차가 날 수 있다(추정: 같은 꼴의 식을 쓴 첫 시안이 상수 열 입력에서 불일치를 냈다). 두 곳이 같은 도우미를 쓰게 하는 편이 낫다 |
| 회귀 테스트 | `tests/macro_m7_stats.py::test_pbo_cscv_fast_path_matches_the_split_loop`: 현재 루프를 테스트 안의 기준 구현으로 둔다. (a) 시드 난수 (1500,12)·(5000,12)·(5000,24), S=8·16, 동일 열 1쌍 포함: `pbo`, `prob_loss`, `n_splits` 완전 일치, `abs(Δslope) <= 1e-12`. (b) 캐시 CSV 5종(QQQ, TLT, GLD, XLE, XLK)의 5개 계열 `pnl_matrix`: 같은 단언. (c) T-PBO-01 레시피: `pbo == 6897/12870`. (d) 시간: T=5000, G=12, S=16에서 1.5초 미만. 기존 `test_t_pbo_01_noise_control_reproduces`, `test_pbo01_noise_control_200_panels_and_objectives`는 그대로 통과해야 한다 |

#### P01-03 · P2 · 사실(측정) — KIS 이력은 페이지 수 × 0.12초가 바닥이다

| 항목 | 내용 |
|---|---|
| ID | P01-03 |
| 심각도 | P2 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `core/quant/history.py:192-226` `kis_history`: 100행/쪽, 최대 `days//100+3`쪽. `data/krx/kis_client.py:83` `_MIN_GAP_S = 0.12`, `:88-95` `_pace`(프로세스 전역 잠금), `:217-236` 매 GET 전에 `_pace()`. EGW00201이면 1초 쉬고 1회 재시도(`:234-236`). `:79-81` 주석: 2026-10-02 탐침에서 1초 안 10건으로 한도에 걸렸다 |
| 재현 단계 | `python3 -B bench_fetch.py`(KIS 행), `python3 -B bench_kis.py` |
| 기대 결과 | KRX 다종목 분석이 수 초 안에 끝난다 |
| 실제 결과 | 4.1절. 20종목 504일: 120건, 14.3초(지연 0), 18.3초(150ms), 36.3초(300ms). 20종목 5000일: 891건, 107.0초(지연 0), 136.4초(150ms). 작업자 4개는 107.5초. 간격에 막힌다 |
| 영향 | KRX 코드로 포트폴리오(최대 15종목, 90건, 10.8초 바닥)나 Strategy Lab(종목당 50건, 6초 바닥)을 돌리면 대기가 길다. 화면은 진행 링만 보인다. 엔진 시세 조회도 같은 간격을 나눠 쓴다(`kis_client.py:89-90` 주석) |
| 수정안 | (1) 간격 0.12초는 올리지 않는다. 공식 한도가 미검증이고, 저장소의 탐침이 더 낮은 실효 한도를 보였다. (2) P01-07(긴 창 파일 재사용)을 적용한다. Strategy Lab 5000일을 한 번 받으면 포트폴리오 504일은 0건이 된다. (3) 만료 시 꼬리만 갱신한다: 저장된 파일이 있으면 최신 1쪽(100행)만 받는다. 겹치는 날짜의 종가가 저장본과 모두 같을 때만 이어 붙인다. 하나라도 다르면(수정주가 재조정, 분할) 전체를 다시 받는다. 50건 → 1건. 수정주가는 과거 전체가 바뀔 수 있어 겹침 검사가 필수다. (4) 진행 표시에 "KIS n/N쪽"을 보여 기다림을 설명한다(선택) |
| 회귀 테스트 | `tests/quant_acceptance.py::test_kis_tail_refresh_splices_only_on_identical_overlap`: 가짜 `KISClient.daily`. (a) 저장 5000행 + 새 1쪽이 겹침에서 같으면 요청 1건, 결과가 전체 재수집과 `dates`·`closes` 완전 일치. (b) 겹침의 종가 하나를 바꾸면 전체 재수집(요청 50건), 결과는 새 데이터. (c) `_pace` 호출 수 == 요청 수 |

#### P01-04 · P2 · 사실(측정) — 파생 Run 1회에 KIS 약 335건, 바닥 약 40초

| 항목 | 내용 |
|---|---|
| ID | P01-04 |
| 심각도 | P2 |
| 판정 | 사실(요청 수 공식과 측정). 실제 시리즈 수는 마스터에 달려 추정 |
| 파일·함수·라인 | `ui/derivatives_page.py:61-73`: `option_expiries`(1), `front_contract`(마스터, 프로세스 캐시), `futures_quote`(1), `option_chain(..., width=0.10, step_pts=2.5, include_book=True)`, `krw_yields_snapshot`(1), `index_daily("2001", days=600)`(12). `data/kis_markets.py:392-430` `option_chain`: 시리즈마다 시세 1건 + 호가 1건, 최대 160 시리즈. `:437-450` `index_daily`: 캐시 없음 |
| 재현 단계 | `python3 -B bench_kis.py` |
| 기대 결과 | 옵션 화면 갱신이 수 초 안에 끝난다 |
| 실제 결과 | `option_chain` 320건 38.4초(지연 0과 30ms 동일). 호가 생략 시 160건 19.2초. spot 800이면 260건 31.3초. `index_daily(600)` 12건 1.45초. 합계 약 335건, 약 40초 바닥 |
| 영향 | 파생 화면은 실행마다 약 40초를 기다린다. 두 번 누르면 약 80초다(P01-05). 그동안 엔진의 KIS 시세 조회도 같은 간격 줄에 선다 |
| 수정안 | (1) `index_daily`에 10분 메모 캐시(부록 A-5). ETF 화면(`ui/etf_page.py:97`)과 파생 화면이 같은 시계열을 나눠 쓴다. 두 번째부터 12건 → 0건. (2) 호가 요청 생략 조건: `_top_of_book`(`data/kis_markets.py:673-700`)은 호가 접수시각 15:45~18:00이면 `(None, None)`을 돌려준다. 그 시간대에는 호가 요청이 결과를 바꾸지 못한다(추정: KIS 응답의 `aspr_acpt_hour`가 그 구간이라는 전제). 소유자가 7절 스크립트로 시간대별 호가 유효 비율을 먼저 잰다. 유효 비율 0인 시간대에서만 생략한다. 160건, 19초 절약. (3) 행사가 폭·간격은 결과를 바꾸므로 소유자 결정 사항이다(예: ±10% 밖은 5pt) |
| 회귀 테스트 | `tests/ficc_acceptance.py::test_index_daily_is_memoised_for_ten_minutes`: 가짜 `_get`, 같은 인자 두 번 호출에서 요청 수가 1회분, 반환 `Bars` 동일. `test_option_chain_skips_books_only_when_they_cannot_answer`: 가짜 호가 응답의 `aspr_acpt_hour="154500"`일 때 `include_book` 자동 생략 경로의 `OptionBoard`가 `include_book=True` 결과와 완전히 같고 요청 수가 절반 |

#### P01-05 · P2 · 사실(측정) — 실행 중 재클릭을 막지 않는다

| 항목 | 내용 |
|---|---|
| ID | P01-05 |
| 심각도 | P2 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `ui/portfolio_page.py:95-200` `run()`은 `busy.visible = True` 뒤 바로 `page.run_thread(worker)`. 재진입 검사와 버튼 비활성화가 없다. 같은 패턴 15곳(`grep "busy.visible = True" ui/*.py`). 예외는 `ui/macro_state_panel.py:677-685`(잠금 + 비활성화)뿐이다. `tests/paper_live_acceptance.py::test_18`은 "두 번 누른 Run이 장부 체인을 깨지 않는다"만 본다 |
| 재현 단계 | `python3 -B bench_cache.py` 2번 항목: 실제 스레드로 Optimize를 0.05초 간격 두 번 클릭 |
| 기대 결과 | 두 번째 클릭은 무시된다. 요청 5건 |
| 실제 결과 | 작업자 2개, 요청 10건. `button.disabled`는 `False` |
| 영향 | 요청·대기 2배(KIS 파생이면 40초 → 80초). 두 작업자가 같은 `result_host`를 덮어쓴다. matplotlib pyplot은 스레드 안전이 보장되지 않는다(추정 위험). 같은 캐시 파일을 동시에 쓴다(쓰기가 원자적이지 않음, C01-08). Strategy Lab이면 시행이 장부에 두 번 들어간다 |
| 수정안 | 부록 A-4 diff(포트폴리오 예시). 페이지마다 `threading.Lock`을 두고 `acquire(blocking=False)`가 실패하면 반환한다. 작업자 `finally`에서 해제한다. 버튼도 실행 중 `disabled=True`로 둔다. 15개 화면에 같은 패턴 |
| 회귀 테스트 | `tests/macro_ui_views.py::test_a_second_click_while_running_does_nothing`: 가짜 `run_thread`가 작업자를 멈춰 둔 채 두 번째 클릭. `assert` 작업자 수 1, 가짜 공급자 호출 수 == 종목 수, 첫 작업 종료 후 다시 누르면 실행됨 |

#### P01-06 · P3 · 사실(측정) — FMP·Yahoo 순차 수집

| 항목 | 내용 |
|---|---|
| ID | P01-06 |
| 심각도 | P3 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `ui/portfolio_page.py:111`, `ui/strategy_lab_page.py:104` 리스트 컴프리헨션. 같은 패턴: `ui/fx_page.py:309`(통화쌍 7개를 `load_fx_spot`로 하나씩) |
| 재현 단계 | `python3 -B bench_fetch.py` (FMP·Yahoo 행, `pool4` 열) |
| 기대 결과 | 종목 수가 늘어도 대기가 지연 몇 번 수준이다 |
| 실제 결과 | 20종목 150ms: FMP 3.11초, Yahoo 3.04초. 300ms: 6.1초, 6.0초. 작업자 4개 시안: 0.81초, 0.77초. 5000일 FMP 20종목 3.87 → 1.33초. 18개 시나리오 모두 결과 해시 동일 |
| 영향 | 포트폴리오 15종목에서 실제 지연이 300ms면 수집만 약 4.5초(추정: 4.1절 비례). 요청 수·일일 쿼터는 그대로라 비용은 늘지 않는다 |
| 수정안 | 부록 A-3 diff. `core/quant/history.py`에 `load_histories(symbols, *, source, days, workers=4)`를 둔다. 중복 제거(P01-12), 입력 순서 유지, 첫 실패를 입력 순서대로 다시 던진다. KIS는 전역 간격이 그대로 지켜진다. 크립토 `_throttle`(`data/crypto/crypto_client.py:105-109`)은 잠금이 없어 동시 호출 시 간격이 깨진다. 잠금을 함께 넣는다. FMP 분당 한도와 Yahoo 비공식 한도는 미검증이라 작업자 수는 4로 둔다 |
| 회귀 테스트 | `tests/quant_acceptance.py::test_load_histories_equals_the_sequential_loop`: 가짜 공급자(종목별 지연 다르게)로 20종목. `[h.__dict__ for h in load_histories(...)] == [load_history(s) ...]`(note의 "cached" 문구 제외), 실패 종목이 있으면 같은 `HistoryError` 메시지, 크립토 동시 4개에서 연속 호출 간격 ≥ 0.12초 |

#### P01-07 · P3 · 사실(측정) — 캐시 키의 `days` 때문에 재사용이 안 된다

| 항목 | 내용 |
|---|---|
| ID | P01-07 |
| 심각도 | P3 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `core/quant/history.py:427` `HIST_{provider}_{SYMBOL}_{days}`. 포트폴리오는 기본 504(`:464`), Strategy Lab은 5000(`ui/strategy_lab_page.py:223`), Sessions 칸은 사용자가 바꾼다. 기존 테스트도 "다른 창은 다른 시계열"을 단언한다(`tests/quant_acceptance.py:129-130`) |
| 재현 단계 | `python3 -B bench_cache.py` 1번 항목 |
| 기대 결과 | 5000일을 받은 뒤 504일·4000일 요청은 파일에서 답한다 |
| 실제 결과 | 504 → 5000 → 4000 → 504: 요청 5 → 5 → 5 → 0, 4.6 MB와 3.8 MB를 다시 받음 |
| 영향 | 화면을 오가면 같은 종목을 다시 받는다. KIS는 종목당 6~50건(P01-03) |
| 수정안 | 부록 A-2 diff. 같은 공급자·기호의 더 긴 창 파일이 같은 TTL 규칙으로 유효하고 행이 충분하면 꼬리 `days`행을 돌려준다. FMP·KIS·CRYPTO만 적용한다. 이들은 오늘부터 거슬러 받으므로 짧은 요청의 결과가 긴 결과의 꼬리와 같다. Yahoo는 기간 버킷(`2y`가 약 502세션) 때문에 결과가 달라질 수 있어 뺀다. 기존 테스트 `tests/quant_acceptance.py:129-130`의 "a different window is a different series"(120일 뒤 60일)는 더 짧은 창일 때 재요청 0건으로 바뀐다. 테스트 수정은 소유자 승인 사항이다 |
| 회귀 테스트 | `tests/quant_acceptance.py::test_a_longer_cached_window_answers_a_shorter_one`: 가짜 FMP. `load_history("AAPL", days=5000)` 후 `days=504` 호출 수 0, 결과 `dates`·`closes`가 가짜 공급자의 직접 504 결과와 같음. YFINANCE는 여전히 재요청. 만료된 긴 파일은 쓰지 않음 |

#### P01-08 · P3 · 사실(측정) — Yahoo 일반 티커는 평일 내내 10분 캐시

| 항목 | 내용 |
|---|---|
| ID | P01-08 (`c01_v01_cache_and_vendors.md`의 C01-07 "성능 영향은 미계측"에 대한 계측) |
| 심각도 | P3 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `core/quant/history.py:371-387` `_may_be_trading`: 거래소를 정하는 분기는 FMP 비점(`.`) 기호, KIS 해외, KIS/Yahoo KRX뿐이다. Yahoo `TLT`는 거래소가 비어 `at.weekday() < 5`로 평일 내내 참이다 |
| 재현 단계 | `python3 -B bench_cache.py` 4번 항목 |
| 기대 결과 | 같은 미국 ETF는 공급자와 관계없이 미국 장중(+1시간)에만 10분 TTL |
| 실제 결과 | Yahoo `TLT`·`GC=F`·`^VIX` 73.2%, FMP `QQQ` 22.3% |
| 영향 | Yahoo로 받은 미국 ETF는 장 마감 후·아시아 시간에도 10분마다 전체(최대 10년)를 다시 받는다 |
| 수정안 | 부록 A-6 diff. Yahoo의 일반 미국 티커(영문자와 `-`만, `-USD`·`-KRW` 제외)는 거래소를 `US`로 본다. 선물·지수·FX는 달력이 없어 현재의 보수적 규칙을 유지한다. 이 변경은 결과값이 아니라 캐시 수명만 바꾼다 |
| 회귀 테스트 | `tests/quant_acceptance.py::test_the_cache_knows_when_a_market_may_be_trading`에 추가: `_may_be_trading("YFINANCE", "TLT", 토요일 12:00 UTC) is False`, 화요일 03:00 UTC `False`, 화요일 15:00 UTC `True`, `"BTC-USD"` 화요일 03:00 UTC `True`, `"GC=F"` 화요일 03:00 UTC `True` |

#### P01-09 · P3 · 사실(측정) — 캐시 없는 반복 수집과 "일괄"의 순차 HTTP

| 항목 | 내용 |
|---|---|
| ID | P01-09 |
| 심각도 | P3 |
| 판정 | 사실(측정, 라이브러리 소스 확인) |
| 파일·함수·라인 | `data/kis_markets.py:437-450` `index_daily`(캐시 없음, ETF `ui/etf_page.py:97`과 파생 `ui/derivatives_page.py:73`이 각각 호출). `ui/crypto_page.py:45-57` `_live`(캔들·펀딩 캐시 없음). `core/ficc/data.py:200` `_yf.download(..., threads=False)`와 `:177` FRED id별 루프. `core/ficc/data.py:674-676` `load_policy_rates`는 통화마다 `load_short_rate`를 따로 부른다 |
| 재현 단계 | `python3 -B bench_kis.py`, `python3 -B bench_ficc.py`, `python3 -B bench_macro.py` |
| 기대 결과 | 같은 화면 재실행은 캐시에서 답한다. 여러 시계열은 함께 받는다 |
| 실제 결과 | `index_daily(600)` 매번 12건. 크립토 매번 11건(1.74초). FX 캐리 cold HTTP 19건 순차(2.29초), warm 0건. 매크로 시트 cold HTTP 18건 순차 |
| 영향 | 각각 1~3초 수준(150ms 가정). 실제 FRED 지연이 크면 매크로·FX 첫 실행이 길어진다(미검증) |
| 수정안 | (1) `index_daily` 10분 메모(부록 A-5). (2) 크립토 `Candles`에 같은 방식의 10분 메모(크립토는 항상 장중이라 10분이 현재 규칙과 같다). (3) `_yf_fetch`에서 `threads=min(4, len(tickers))`. yfinance 1.7.0은 정수 스레드 수를 받는다. (4) FX 캐리의 `spots`를 `_provider_rows("YFINANCE", tickers, days)` 한 번으로 묶는 `load_fx_spots` 도우미(3과 함께여야 효과). (5) FRED는 id별 요청이 불가피하다. 작업자 2~4개로 병렬화하되 keyless `fredgraph.csv`의 한도는 미검증이다 |
| 회귀 테스트 | `tests/ficc_acceptance.py::test_fx_spots_batch_equals_one_by_one`: 가짜 `_yf_fetch`로 7개 통화쌍. 묶음 결과의 `Series`가 개별 `load_fx_spot` 결과와 같고(`dates`, `values`, `label`, `source`), `_yf_fetch` 호출 1회. 크립토: 가짜 세션으로 `_live` 두 번, 두 번째 요청 수 0 |

#### P01-10 · P3 · 사실(코드) — Yahoo는 10년이 상한

| 항목 | 내용 |
|---|---|
| ID | P01-10 (범위 밖: 데이터 완전성. 계측 중 발견) |
| 심각도 | P3 |
| 판정 | 사실(코드). 실제 Yahoo 행 수는 추정 |
| 파일·함수·라인 | `core/ficc/data.py:435-440` `_period_for`: 1260일 초과는 모두 `"10y"`. `core/quant/history.py:272` `yf_history`가 이것을 쓴다 |
| 재현 단계 | `python3 -B -c "import sys; sys.path.insert(0,'/home/user/quantgen'); from core.ficc.data import _period_for; print(_period_for(5000))"` → `10y`. `bench_fetch.py`의 Yahoo 5000일 행: 2514세션 |
| 기대 결과 | Sessions 5000이면 가능한 만큼(최대 5000) 받는다 |
| 실제 결과 | 약 2,515세션(10년)에서 멈춘다. 캐시 파일 이름은 `_5000`이다 |
| 영향 | Yahoo로 Strategy Lab을 돌리면 walk-forward OOS 기간이 절반가량으로 줄어든다. 화면의 "shared sessions" 칩에는 실제 수가 보인다 |
| 수정안 | 부록 A-7 diff. 2,500세션 초과는 `"max"`를 요청하고 호출자가 `days`로 자른다 |
| 회귀 테스트 | `tests/ficc_acceptance.py::test_period_for_long_windows_asks_for_max`: `_period_for(5000) == "max"`, `_period_for(2000) == "10y"`, `_period_for(504) == "2y"`. 가짜 `_yf_fetch`가 `"max"`에서 6000행을 주면 `yf_history(days=5000)`이 5000행 |

#### P01-11 · P3 · 사실(함수 수준) — 전액 현금 구간의 Sharpe가 약 3.5e16

| 항목 | 내용 |
|---|---|
| ID | P01-11 (범위 밖: 금융 계산. P01-02의 결과 동일성을 검사하다 발견) |
| 심각도 | P3 |
| 판정 | 사실(함수 수준 재현). 실데이터 발생은 추정(캐시 8개 시계열 × 3개 계열에서는 관측되지 않음) |
| 파일·함수·라인 | `core/quant/validate.py:268-270` `_col_sharpe`: `s > 0`이면 `m/s`. `core/quant/strategies.py:85-87` 비중 0이면 일별 P&L이 정확히 `cash_daily`(상수 0.03/252). 상수 열의 `np.std`는 0이 아니라 약 5e-20(부동소수 잡음)이다. `validate.py:372` walk-forward가 `np.nanargmax`로 IS 승자를 고른다 |
| 재현 단계 | `python3 -B repro_flat_sharpe.py` |
| 기대 결과 | 변동이 없는 열의 Sharpe는 0(또는 제외) |
| 실제 결과 | 756행 상수 현금 열 Sharpe 3.48e16. 2개 실제 설정(연 Sharpe 약 1.3~2.3)과 900일 현금 설정이 있으면 첫 두 원점에서 현금 설정을 고른다(`chosen = (2, 2, 1, 1, 2, 2)`, IS Sharpe `[-0.35, 2.34, 9.4e14]`). `pbo_cscv`도 같은 열을 항상 승자로 본다(상수 열이 있으면 PBO 0.0) |
| 영향 | IS 창 756세션 내내 시장 밖에 있던 설정이 있으면 그 설정이 선택되고 PBO가 왜곡된다. 드물다. P01-02의 빠른 구현이 이런 열에서만 현재 값과 달라지는 원인이다 |
| 수정안 | 부록 A-1에 포함. 상대 0분산 규칙 `s > 1e-12·max(|m|, 1e-12)`을 `_col_sharpe`와 빠른 PBO가 함께 쓴다. 실제 수익률 열(표준편차/평균 ≈ 10~100)에는 영향이 없다. 이 규칙을 넣은 루프 기준과 빠른 구현은 상수·0·반쪽 현금 열이 섞인 입력 12개에서 `pbo`·`prob_loss` 완전 일치, `slope` 차이 9.4e-15 이하였다(`edge_pbo_guarded.py`). 금융 계산 차원의 확인과 소유자 승인이 필요하다 |
| 회귀 테스트 | `tests/macro_m7_stats.py::test_flat_cash_configuration_has_zero_sharpe`: `_col_sharpe(np.full((756, 1), 0.03/252))[0] == 0.0`. 위 3열 행렬에서 `walk_forward(...).chosen[0] == 1`. 상수 열이 있는 행렬에서 빠른 PBO == 루프 PBO |

#### P01-12 · P3 · 사실(측정) — 중복 기호를 지우지 않는다

| 항목 | 내용 |
|---|---|
| ID | P01-12 (범위 밖: 입력 검증. 요청 중복 점검 중 확인) |
| 심각도 | P3 |
| 판정 | 사실(측정) |
| 파일·함수·라인 | `ui/portfolio_page.py:102-111`: 대문자화만 하고 중복은 그대로 `load_history`·`align_histories`로 간다 |
| 재현 단계 | `python3 -B bench_cache.py` 3번 항목 |
| 기대 결과 | `QQQ, QQQ, TLT`는 `QQQ, TLT`로 처리되거나 안내가 나온다 |
| 실제 결과 | 네트워크 2건(두 번째는 캐시 적중). 상관행렬 행렬식 2.2e-16. min_vol 가중치 0.098 / 0.098 / 0.804, `converged=True` |
| 영향 | 같은 자산이 두 줄로 보이고 가중치가 나뉜다. 사용자는 특이 공분산을 알 수 없다 |
| 수정안 | `load_histories`(부록 A-3)의 `dict.fromkeys` 중복 제거. 지운 기호는 `notice`로 알린다 |
| 회귀 테스트 | `tests/quant_acceptance.py::test_duplicate_symbols_are_dropped_once`: `load_histories(["QQQ", "qqq ", "TLT"])`의 기호가 `["QQQ", "TLT"]`, 가짜 공급자 호출 2회 |

#### P01-13 · P3 · 사실(측정, 클라우드) — 앱 임포트 약 3초

| 항목 | 내용 |
|---|---|
| ID | P01-13 |
| 심각도 | P3 |
| 판정 | 사실(클라우드 측정). Windows 수치는 미검증 |
| 파일·함수·라인 | `main.py:51-66`가 16개 페이지 모듈을 모두 시작 시 임포트한다. 그중 `ui.bonds_page` 경로가 `scipy.stats`·GARCH를 끌어온다(4.6절) |
| 재현 단계 | `python3 -B bench_startup.py`, `python3 -B -X importtime -c "import main"` |
| 기대 결과 | 첫 화면(매크로)에 필요한 모듈만 시작 시 읽는다 |
| 실제 결과 | 2.90~3.11초. 상위: bonds 경로 1.81초, flet 0.58초 |
| 영향 | 창이 뜨기 전 약 3초. 페이지 생성은 빠르다(9ms 이하) |
| 수정안 | `main.build()`에서 페이지 모듈을 처음 방문 때 임포트한다(예: `from ui.bonds_page import build_bonds_page`를 함수 안으로). 비용이 첫 방문으로 옮겨질 뿐 총합은 같다. 선택 사항이다 |
| 회귀 테스트 | `tests/flet_api_guard.py`에 `test_main_imports_only_the_start_page`: 새 인터프리터에서 `import main` 후 `"ui.bonds_page" not in sys.modules`. 전체 화면 생성 테스트는 그대로 통과 |

## 6. 문제없음으로 확인한 항목

- 페이지 생성 중 네트워크 없음(16개, 0건). 네트워크 작업은 모두 작업자 스레드 안.
- warm 캐시 적중은 빠르다: 20종목 × 5000세션 0.045초.
- JSON 파싱은 병목이 아니다: KIS 891쪽(26 MB) 0.86~1.45초.
- `_traded_since` 30분 표본 반복은 1.2ms 이하.
- KIS 간격은 스레드 간 잠금으로 지켜진다(`data/krx/kis_client.py:84-95`). 동시성 시안에서도 한도 이상으로 빨라지지 않았다.
- `data/net.py`의 재시도는 연결 실패와 502/503/504만, 최대 2회다. 429·500은 재시도하지 않는다. 실패 시 최악은 약 3 × 타임아웃(12초) + 1초다(`data/net.py:28-29`). 중복 요청을 만들지 않는다.
- 매크로 시트는 공급자 단위로 묶어 부른다(`core/ficc/macro.py:150-158`). 다만 HTTP는 id별 순차다(P01-09).

## 7. 소유자 Windows PC에서의 실측 절차

### 7.1 준비와 환경 기록 (PowerShell, 저장소 루트에서)

```powershell
cd C:\path\to\quantgen
python --version
python -m pip freeze > $env:TEMP\audit-installed-packages.txt
# 부록 B의 스크립트를 저장소 밖에 저장한다. 예: $env:TEMP\qg_live_profile.py
```

### 7.2 앱 시작 시간

```powershell
python -B -c "import time; t=time.perf_counter(); import main; print('import main', round(time.perf_counter()-t, 3), 's')"
python -B -X importtime -c "import main" 2> $env:TEMP\importtime.txt
```

창이 뜨기까지와 첫 화면(매크로) 표시까지는 스톱워치나 화면 녹화로 잰다. Flet 클라이언트 그리기는 Python에서 잴 수 없다.

### 7.3 화면별 계측 (요청 수, 요청별 지연, 크기, 파싱, 계산, 렌더)

각 명령은 cold(빈 임시 캐시)와 warm(같은 입력 두 번째)을 차례로 돌리고 JSON에 저장한다. 요청은 호스트와 경로만 기록한다. 쿼리 문자열·헤더(키, 토큰)는 기록하지 않는다. Strategy Lab 시행은 임시 장부 폴더에 쓴다.

```powershell
$P = "$env:TEMP\qg_live_profile.py"
# 포트폴리오: 2 / 5 / 15 종목 (FMP 키가 있을 때)
python -B $P portfolio --symbols "AAPL,MSFT" --source fmp --out $env:TEMP\pf2.json
python -B $P portfolio --symbols "AAPL,MSFT,NVDA,TLT,GLD" --source fmp --out $env:TEMP\pf5.json
python -B $P portfolio --symbols "AAPL,MSFT,NVDA,TLT,GLD,AMZN,GOOGL,META,JPM,XOM,JNJ,PG,KO,IEF,LQD" --source fmp --out $env:TEMP\pf15.json
# 포트폴리오: KRX(KIS) 2 / 5 종목 (15종목도 같은 형식)
python -B $P portfolio --symbols "005930,000660" --source auto --out $env:TEMP\pfk2.json
python -B $P portfolio --symbols "005930,000660,035420,005380,069500" --source auto --out $env:TEMP\pfk5.json
# 포트폴리오: Yahoo 5 종목
python -B $P portfolio --symbols "SPY,QQQ,TLT,GLD,IEF" --source yfinance --out $env:TEMP\pfy5.json
# Strategy Lab: 1 / 5 / 20 종목, 기본 5000세션, bootstrap 1000
python -B $P lab --family trend_switch --symbols "QQQ" --source fmp --out $env:TEMP\lab1.json
python -B $P lab --family trend_switch --symbols "QQQ,TLT,GLD,IEF,XLE" --source fmp --out $env:TEMP\lab5.json
python -B $P lab --family xs_momentum --symbols "XLB,XLE,XLF,XLI,XLK,XLP,XLU,XLV,XLY,QQQ,TLT,GLD,IEF,LQD,HYG,EEM,EFA,VNQ,DBC,IAU" --source fmp --out $env:TEMP\lab20.json
python -B $P lab --family trend_switch --symbols "069500,152380" --source auto --out $env:TEMP\labk2.json
```

출력 JSON의 `runs.cold.network.by_host`에 호스트별 요청 수, 합계 초, p50/p95, 바이트, 200 이외 응답 수가 있다. `kis_pace_s`는 KIS 간격 대기, `yahoo_s`·`fred_s`는 세션을 쓰지 않는 두 공급자 시간이다. `stages`에 fetch·align·optimize·frontier·charts(포트폴리오), fetch·pnl_matrix·walk_forward·ledger·score·chart(Lab)가 있다. `parse_and_overhead_s`는 fetch 시간에서 네트워크·KIS 간격·Yahoo·FRED 대기를 뺀 값이다(파싱 추정). 현재 코드에서 Lab의 `chart_error`에는 P01-01의 `ValueError`가 기록된다.

파생·ETF·크립토 화면은 앱에서 Run을 누르고 스톱워치로 잰다. 요청 수 모델은 4.3절·4.5절과 같다.

### 7.4 개선 전후 결과 동일성 확인

```powershell
# 1) 패치 전: 결과를 고정할 캐시 폴더를 지정해 실행
python -B $P portfolio --symbols "AAPL,MSFT,NVDA,TLT,GLD" --source fmp --cache C:\qg_regress_cache --out $env:TEMP\before.json
# 2) 패치 적용 후, 같은 캐시 폴더로 같은 명령
python -B $P portfolio --symbols "AAPL,MSFT,NVDA,TLT,GLD" --source fmp --cache C:\qg_regress_cache --out $env:TEMP\after.json
# 3) 비교: 기호·출처·이력 해시·가중치(허용 1e-9)·Sharpe·Lab 결정·SR·DSR·PBO
python -B $P compare $env:TEMP\before.json $env:TEMP\after.json
```

- 마지막 줄이 `REGRESSION PASS`여야 한다. 차이가 있으면 `DIFF` 줄이 항목을 보여 준다.
- 장중에 받은 시계열은 10분만 캐시된다. 미국·한국 장이 모두 닫힌 시간(예: 주말)에 1)~2)를 한 번에 돌린다. 크립토는 항상 장중이라 이 비교에서 뺀다.
- 오프라인 자체 시험: `test_live_profile.py`에서 같은 입력은 `PASS`, 가중치 하나를 1e-6 바꾼 파일은 `FAIL`이었다.
- 저장소 단위 회귀: P01-02 패치 후 `tests/macro_m7_stats.py`, `tests/macro_m1_fixtures.py`의 PBO 테스트와 5.2절의 새 테스트를 함께 돌린다. 전체 스위트는 `qa/acceptance_results.json`을 다시 쓰므로 소유자가 직접 실행한다.

## 8. 미검증 항목

| 항목 | 이유 | 확인 방법 |
|---|---|---|
| 실제 공급자 지연·응답 크기(FMP, KIS, Yahoo, FRED, Upbit, Binance) | 클라우드에서 실호출 금지 | 7.3절 |
| Flet 클라이언트 그리기 시간, `page.update()` 전송 시간 | Flet 클라이언트가 없다 | 화면 녹화 또는 스톱워치. 작업자 쪽 렌더(PNG)는 4.2절에서 측정 |
| KIS 공식 호출 한도(실전·모의·해외) | 공식 포털 `apiportal.koreainvestment.com`, 제3자 `algolab.co.kr` 모두 이 환경에서 DNS 실패(ENOTFOUND). 공식 GitHub(`koreainvestment/open-trading-api`)는 "모의투자 계좌는 REST API 호출 제한이 낮다"고만 한다. 제3자 요약 검색 결과는 실전 초당 20건, 모의 2건, 해외 1건이라고 한다(미확인). 저장소 주석은 2026-10-02 탐침에서 1초 10건으로 EGW00201이 났다고 기록한다 | 소유자 계정으로 KIS 포털 확인. 간격 0.12초는 그대로 둘 것을 권한다 |
| FMP 플랜별 분당 한도, Yahoo 비공식 한도, keyless FRED `fredgraph.csv` 한도 | 문서 미확인 | 동시성 작업자 4개로 7.3절을 돌리며 429·비200 수를 본다 |
| 실제 KOSPI200 옵션 마스터의 ±10% 시리즈 수 | 마스터 다운로드 불가 | 소유자 PC에서 `len(option_codes(yyyymm))`와 범위 내 수 |
| 15:45~18:00 외 시간대 호가 유효 비율(P01-04 (2)) | 실호출 필요 | 7.3절 스크립트를 파생 경로로 확장하거나 앱 로그 |
| Windows에서의 임포트·계산 시간 | 다른 하드웨어 | 7.2절, 7.3절 |
| Yahoo 실제 `"10y"` 행 수, `"max"` 동작 | 실호출 필요. 하네스는 10년 = 2514행으로 모사 | 7.3절 Yahoo 5000일 Lab |
| P01-07의 "꼬리 = 짧은 요청 결과" 동일성(실데이터) | 가짜 공급자로만 확인 | 7.4절 비교를 504일과 5000일 순서로 |
| pyplot 동시 사용 시 실제 오류 발생 여부(P01-05) | 재현하지 않음 | 재진입 방지 후 문제 자체가 사라진다 |
| 엔진 시세 폴링(`core/engine/feed.py`)의 지연 | 이 차원 범위 밖 | 별도 |

## 9. 재현 스크립트 경로

모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/` 아래. 실행: 그 폴더에서 `python3 -B <파일>`.

| 파일 | 내용 |
|---|---|
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/common.py` | 공통: 격리 환경, 가짜 HTTP 세션(지연 주입, 요청·바이트 집계), 가짜 Yahoo·FRED, 금지 파일 거부 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_fetch.py` | 4.1절. 결과 `results_fetch.json`, 로그 `bench_fetch.log` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_screens.py` | 4.2절. 결과 `results_screens.json`, 로그 `bench_screens.log` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/profile_score.py` | Strategy Lab cProfile |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_kis.py` | 4.3절. 결과 `results_kis.json` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_cache.py` | 4.4절. 결과 `results_cache.json` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_ficc.py` | 4.5절 FX 캐리·크립토. 결과 `results_ficc.json` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_macro.py` | 4.5절 매크로 시트 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/bench_startup.py` | 4.6절. 결과 `results_startup.json`, `importtime.log` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/repro_lab_chart.py` | P01-01 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/proto_pbo.py` | P01-02 빠른 PBO 시안 대 현재(시드 난수, 캐시 데이터 4개 계열, T-PBO-01). 로그 `proto_pbo.log` |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/proto_pbo_exact.py` | 비트 동일 시안(분할 재사용 + 묶음 축소): 1.0~3.2배에 그침. 참고용 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/edge_pbo.py` | 0분산 규칙 없는 빠른 PBO가 상수 열에서 달라짐을 보임 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/edge_pbo_guarded.py` | 0분산 규칙을 양쪽에 넣으면 상수 열 포함 입력에서도 일치 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/final_pbo_check.py` | 부록 A-1 구현 대 현재 `validate.pbo_cscv`, 9개 입력 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/repro_flat_sharpe.py` | P01-11 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/patched_pbo_tests.py` | 부록 A-1을 메모리에서만 적용하고 기존 PBO 테스트 2개와 P01-11 예를 실행 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/qg_live_profile.py` | 부록 B, 소유자 PC용 실측 스크립트 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/test_live_profile.py` | 위 스크립트의 오프라인 자체 시험(가짜 공급자) |

## 부록 A. 제안 패치 (적용하지 않음)

### A-1. `core/quant/validate.py`: 빠른 PBO와 0분산 규칙 (P01-02, P01-11)

```diff
--- a/core/quant/validate.py
+++ b/core/quant/validate.py
@@ -246,28 +246,53 @@ def pbo_cscv(pnl: np.ndarray, *, S: int = 8) -> dict:
     M = np.asarray(pnl, dtype=float)
     T, G = M.shape
     if G < 2 or T < 2 * S:
         return {"pbo": float("nan"), "n_splits": 0, "prob_loss": float("nan"), "slope": float("nan")}
     blocks = np.array_split(np.arange(T), S)
-    logits, oos_sr, is_sr = [], [], []
-    for train in combinations(range(S), S // 2):
-        tr = np.concatenate([blocks[i] for i in train])
-        te = np.concatenate([blocks[i] for i in range(S) if i not in train])
-        sr_tr = _col_sharpe(M[tr])
-        sr_te = _col_sharpe(M[te])
-        best = int(np.nanargmax(sr_tr))
-        rank = float(np.sum(sr_te <= sr_te[best]))          # 1 = worst ... G = best
-        w = rank / (G + 1.0)
-        logits.append(math.log(w / (1.0 - w)))
-        oos_sr.append(float(sr_te[best]))
-        is_sr.append(float(sr_tr[best]))
-    logits = np.asarray(logits)
+    # Every half's Sharpe from per-block moments, one pass over the data instead of C(S, S/2) x 2 column
+    # reductions (12,870 x 2 at S = 16). Pooled variance (Chan et al.) with the between-block term taken from
+    # explicit deviations, so there is no n * mean^2 cancellation.
+    n_b = np.array([b.size for b in blocks], dtype=float)                        # S
+    sum_b = np.stack([M[b].sum(axis=0) for b in blocks])                         # S x G
+    mean_b = sum_b / n_b[:, None]
+    m2_b = np.stack([((M[b] - mean_b[i]) ** 2).sum(axis=0) for i, b in enumerate(blocks)])
+    splits = list(combinations(range(S), S // 2))
+    A = np.zeros((len(splits), S))
+    for k, train in enumerate(splits):
+        A[k, list(train)] = 1.0
+
+    def half_sharpe(mask: np.ndarray) -> np.ndarray:                            # K x G
+        n = mask @ n_b
+        mean = (mask @ sum_b) / n[:, None]
+        dev = mean_b[None, :, :] - mean[:, None, :]                              # K x S x G
+        m2 = mask @ m2_b + np.einsum("ks,s,ksg->kg", mask, n_b, dev ** 2)
+        return _sharpe_from_moments(mean, np.sqrt(np.maximum(m2, 0.0) / (n[:, None] - 1.0)))
+
+    sr_tr, sr_te = half_sharpe(A), half_sharpe(1.0 - A)
+    rows = np.arange(len(splits))
+    best = np.argmax(np.where(np.isnan(sr_tr), -np.inf, sr_tr), axis=1)        # first maximum, as nanargmax
+    oos_best, is_best = sr_te[rows, best], sr_tr[rows, best]
+    rank = (sr_te <= oos_best[:, None]).sum(axis=1).astype(float)               # 1 = worst ... G = best
+    w = rank / (G + 1.0)
+    logits = np.log(w / (1.0 - w))
+    oos_sr, is_sr = oos_best.tolist(), is_best.tolist()
     slope = float(np.polyfit(is_sr, oos_sr, 1)[0]) if len(set(is_sr)) > 1 else float("nan")
     return {"pbo": float(np.mean(logits < 0)), "n_splits": int(logits.size),
             "prob_loss": float(np.mean(np.asarray(oos_sr) < 0)), "slope": slope}
 
 
+def _sharpe_from_moments(m: np.ndarray, s: np.ndarray) -> np.ndarray:
+    """Annualised Sharpe. A column whose deviation is floating-point noise around its mean (a configuration in
+    cash all window: std ~1e-20 on a 1.2e-4 daily cash rate) has Sharpe 0, not ~1e16."""
+    ok = s > 1e-12 * np.maximum(np.abs(m), 1e-12)
+    return np.where(ok, m / np.where(ok, s, 1.0), 0.0) * math.sqrt(TRADING_DAYS)
+
+
 def _col_sharpe(M: np.ndarray) -> np.ndarray:
     m, s = M.mean(axis=0), M.std(axis=0, ddof=1)
-    return np.where(s > 0, m / np.where(s > 0, s, 1.0), 0.0) * math.sqrt(TRADING_DAYS)
+    return _sharpe_from_moments(m, s)
```

검증: `final_pbo_check.py`(이 구현 대 현재 구현, 9개 입력 완전 일치), `edge_pbo_guarded.py`(상수 열 포함 12개 입력, 규칙을 넣은 루프와 완전 일치). `patched_pbo_tests.py`는 이 diff를 메모리에서만 적용하고 저장소의 기존 테스트 `macro_m1_fixtures::test_t_pbo_01_noise_control_reproduces`와 `macro_m7_stats::test_pbo01_noise_control_200_panels_and_objectives`를 돌렸다. 둘 다 PASS. 같은 상태에서 P01-11의 3열 예는 `chosen = (1, 1, 1, 1, 2, 2)`가 되어 현금 설정을 더 고르지 않는다. T=5000, G=12, S=16 한 번에 0.12초. 메모리: K×S×G = 12,870×16×12 실수 약 20 MB.

### A-2. `core/quant/history.py`: 긴 창 파일의 꼬리 재사용 (P01-07)

```diff
--- a/core/quant/history.py
+++ b/core/quant/history.py
@@ -357,6 +357,10 @@ _READY = {"FMP": lambda: bool(config.fmp_key()), "KIS": lambda: config.kis_ready()}
 _CACHE_MIN_ROWS = 30
 
+# Providers that page back from today, so the last `days` bars of a longer answer ARE the shorter answer.
+# Yahoo is left out: its period buckets ("2y" is ~502 sessions) make a tail differ from a direct request.
+_TAIL_EXACT = {"FMP", "KIS", "CRYPTO"}
+
 
 _CACHE_LIVE_TTL = 600.0     # seconds a series fetched while its market may be trading is kept
@@ -402,7 +406,30 @@ def _traded_since(provider: str, symbol: str, ts: float) -> bool:
-def _cached(provider: str, fetch, symbol: str, days: int) -> History:
+def _read_hist(path, provider: str, symbol: str, ttl: float) -> History | None:
+    """The stored series at `path` when it is still valid under the rules of `_cached`, else None."""
+    try:
+        p = json.loads(path.read_text("utf-8"))
+        final = p.get("live") is False and not _traded_since(provider, symbol, float(p["ts"]))
+        limit = ttl if final else min(ttl, _CACHE_LIVE_TTL)
+        if 0 <= time.time() - float(p["ts"]) < limit and len(p["dates"]) == len(p["closes"]):
+            stamp = datetime.fromtimestamp(float(p["ts"])).strftime("%Y-%m-%d %H:%M")
+            note = "; ".join(x for x in (str(p.get("note") or ""), f"cached {stamp}") if x)
+            return History(str(p["symbol"]), str(p["source"]), tuple(p["dates"]),
+                           tuple(float(c) for c in p["closes"]), note=note,
+                           adjustment=str(p.get("adjustment") or ""),
+                           status=str(p.get("status") or ("provisional_intraday" if p.get("live") else "")))
+    except Exception:
+        pass                                  # absent, expired or unreadable
+    return None
+
+
+def _cached(provider: str, fetch, symbol: str, days: int) -> History:
@@ -427,21 +454,19 @@ def _cached(provider: str, fetch, symbol: str, days: int) -> History:
     name = re.sub(r"[^A-Za-z0-9_.-]", "_", f"HIST_{provider}_{symbol.upper()}_{days}")
     path = config.ficc_cache_dir() / f"{name}.json"
-    try:
-        p = json.loads(path.read_text("utf-8"))
-        # Only an explicit `"live": false` earns the full TTL (a file from
-        # before the flag existed does not), and only while the market has not
-        # traded since it was written.
-        final = p.get("live") is False and not _traded_since(provider, symbol, float(p["ts"]))
-        limit = ttl if final else min(ttl, _CACHE_LIVE_TTL)
-        if 0 <= time.time() - float(p["ts"]) < limit and len(p["dates"]) == len(p["closes"]):
-            stamp = datetime.fromtimestamp(float(p["ts"])).strftime("%Y-%m-%d %H:%M")
-            note = "; ".join(x for x in (str(p.get("note") or ""), f"cached {stamp}") if x)
-            return History(str(p["symbol"]), str(p["source"]), tuple(p["dates"]),
-                           tuple(float(c) for c in p["closes"]), note=note,
-                           adjustment=str(p.get("adjustment") or ""),
-                           status=str(p.get("status") or ("provisional_intraday" if p.get("live") else "")))
-    except Exception:
-        pass                                  # absent, expired or unreadable: fetch
+    hit = _read_hist(path, provider, symbol, ttl)
+    if hit is None and provider in _TAIL_EXACT:
+        stem = name[: -len(str(days))]                       # "HIST_FMP_QQQ_"
+        for other in sorted(path.parent.glob(f"{stem}*.json")):
+            tail = other.stem[len(stem):]
+            if tail.isdigit() and int(tail) > days:
+                big = _read_hist(other, provider, symbol, ttl)
+                if big is not None and len(big) >= days:
+                    hit = replace(big, dates=big.dates[-days:], closes=big.closes[-days:])
+                    break
+    if hit is not None:
+        return hit
     live = _may_be_trading(provider, symbol)  # judged before the request goes out
```

### A-3. 제한 동시성 수집 도우미와 크립토 간격 잠금 (P01-06, P01-12)

```diff
--- a/core/quant/history.py
+++ b/core/quant/history.py
@@ -511,0 +512,19 @@
+
+
+def load_histories(symbols, *, source: str = "auto", days: int = 504, workers: int = 4) -> list[History]:
+    """`load_history` for several symbols. Duplicates are dropped (first kept, order kept) and up to `workers`
+    are fetched at once: the same Histories as the one-by-one loop, and the first failure in input order is
+    raised. KIS calls stay spaced by the process-wide pacer (`kis_client._pace`); the crypto throttle holds a
+    lock for the same reason."""
+    syms = list(dict.fromkeys(s.strip() for s in symbols if s and s.strip()))
+    if len(syms) <= 1 or workers <= 1:
+        return [load_history(s, source=source, days=days) for s in syms]
+    from concurrent.futures import ThreadPoolExecutor
+    with ThreadPoolExecutor(max_workers=min(workers, len(syms))) as ex:
+        futures = [ex.submit(load_history, s, source=source, days=days) for s in syms]
+    return [f.result() for f in futures]
--- a/ui/portfolio_page.py
+++ b/ui/portfolio_page.py
@@ -19 +19 @@
-from core.quant.history import HistoryError, convention_warning, load_history
+from core.quant.history import HistoryError, convention_warning, load_histories
@@ -102,3 +102,3 @@ def build_portfolio_page(page: ft.Page,
-                syms = [s.strip().upper() for s in (symbols.value or "").split(",")
-                        if s.strip()]
+                syms = list(dict.fromkeys(s.strip().upper() for s in (symbols.value or "").split(",")
+                                          if s.strip()))
@@ -111 +111 @@
-                hists = [load_history(s, source=source.value or "auto") for s in syms]
+                hists = load_histories(syms, source=source.value or "auto")
--- a/ui/strategy_lab_page.py
+++ b/ui/strategy_lab_page.py
@@ -24 +24 @@
-from core.quant.history import HistoryError, convention_warning, load_history
+from core.quant.history import HistoryError, convention_warning, load_histories
@@ -104 +104 @@ def run_family(...):
-    hists = [load_history(s, source=source, days=days) for s in symbols]
+    hists = load_histories(symbols, source=source, days=days)
--- a/data/crypto/crypto_client.py
+++ b/data/crypto/crypto_client.py
@@ -37,2 +37,3 @@
 import json
+import threading
 import time
@@ -58 +59,2 @@
 _last_call = {"t": 0.0}
+_THROTTLE_LOCK = threading.Lock()
@@ -105,5 +107,6 @@
 def _throttle() -> None:
-    gap = time.monotonic() - _last_call["t"]
-    if gap < _MIN_GAP_S:
-        time.sleep(_MIN_GAP_S - gap)
-    _last_call["t"] = time.monotonic()
+    with _THROTTLE_LOCK:                 # one allowance for every thread, as KIS's _pace
+        gap = time.monotonic() - _last_call["t"]
+        if gap < _MIN_GAP_S:
+            time.sleep(_MIN_GAP_S - gap)
+        _last_call["t"] = time.monotonic()
```

주의: Strategy Lab의 pairs는 "y then x" 순서가 의미를 갖는다. 중복 제거는 순서를 유지하므로 영향이 없다. 같은 기호 두 개를 넣으면 지금처럼 오류가 난다(2개 필요).

### A-4. `ui/portfolio_page.py`: 재진입 방지 (P01-05, 다른 14개 화면도 같은 패턴)

```diff
--- a/ui/portfolio_page.py
+++ b/ui/portfolio_page.py
@@ -12,2 +12,3 @@
 from __future__ import annotations
 
+import threading
 from typing import Callable, Optional
@@ -92,2 +93,3 @@ def build_portfolio_page(page: ft.Page,
     busy = ft.ProgressRing(visible=False, width=20, height=20)
     result_host = ft.Column(spacing=14)
+    running = threading.Lock()                 # one run at a time: a second click while busy does nothing
 
     def run(e=None) -> None:
+        if not running.acquire(blocking=False):
+            return
         busy.visible = True
@@ -198,3 +202,9 @@
             page.update()
 
-        page.run_thread(worker)
+        def guarded() -> None:
+            try:
+                worker()
+            finally:
+                running.release()
+
+        page.run_thread(guarded)
```

버튼 `disabled` 토글을 함께 넣으면 사용자가 상태를 본다(선택).

### A-5. `data/kis_markets.py`: `index_daily` 10분 메모 (P01-04, P01-09)

```diff
--- a/data/kis_markets.py
+++ b/data/kis_markets.py
@@ -32,3 +32,4 @@
 import io
 import re
+import time
 import zipfile
@@ -437,4 +438,9 @@ class KISMarkets:
     def index_daily(self, code: str = "2001", *, days: int = 504) -> Bars:
         """KOSPI (0001) / KOSDAQ (1001) / KOSPI200 (2001) daily OHLCV; 50 rows per
-        call, paged on DATE_2."""
+        call, paged on DATE_2. Remembered for ten minutes per (code, days): the ETF and Derivatives pages
+        both read it, and its last bar may be a running print, so it is never kept longer."""
+        hit = _INDEX_MEMO.get((code, days))
+        if hit is not None and time.monotonic() - hit[0] < _INDEX_TTL_S:
+            return hit[1]
         def fetch(end):
@@ -447,4 +453,6 @@ class KISMarkets:
-        return _bars(f"INDEX:{code}", rows, {"date": "stck_bsop_date", "close": "bstp_nmix_prpr",
-                                              "open": "bstp_nmix_oprc", "high": "bstp_nmix_hgpr",
-                                              "low": "bstp_nmix_lwpr", "volume": "acml_vol"})
+        b = _bars(f"INDEX:{code}", rows, {"date": "stck_bsop_date", "close": "bstp_nmix_prpr",
+                                           "open": "bstp_nmix_oprc", "high": "bstp_nmix_hgpr",
+                                           "low": "bstp_nmix_lwpr", "volume": "acml_vol"})
+        _INDEX_MEMO[(code, days)] = (time.monotonic(), b)
+        return b
```

모듈 상단에 `_INDEX_MEMO: dict[tuple[str, int], tuple[float, Bars]] = {}`와 `_INDEX_TTL_S = 600.0`을 둔다. `Bars`는 `frozen=True`라 공유해도 안전하다.

### A-6. `core/quant/history.py`: Yahoo 일반 티커를 미국 거래소로 (P01-08)

```diff
--- a/core/quant/history.py
+++ b/core/quant/history.py
@@ -378,2 +378,5 @@ def _may_be_trading(provider: str, symbol: str, at: datetime | None = None) -> bool:
     elif provider in ("KIS", "YFINANCE") and _looks_krx(s):
         venue = "KRX"                 # cash equities only: KRX futures and FX keep other hours
+    elif provider == "YFINANCE" and s.replace("-", "").isalpha() and not s.endswith(("-USD", "-KRW")):
+        venue = "US"                  # a plain Yahoo ticker (TLT, BRK-B) is a US listing; ^, =F, =X, -USD
+                                      # and dotted suffixes keep the conservative any-weekday rule below
```

### A-7. `core/ficc/data.py`: 10년 초과 요청은 `"max"` (P01-10)

```diff
--- a/core/ficc/data.py
+++ b/core/ficc/data.py
@@ -435,6 +435,6 @@
 def _period_for(days: int) -> str:
     for n, p in ((5, "5d"), (21, "1mo"), (63, "3mo"), (126, "6mo"), (252, "1y"),
-                 (504, "2y"), (1260, "5y")):
+                 (504, "2y"), (1260, "5y"), (2500, "10y")):
         if days <= n:
             return p
-    return "10y"
+    return "max"                 # longer than ten years: Yahoo's whole history, cut to `days` by the caller
```

## 부록 B. 소유자 PC용 실측 스크립트 `qg_live_profile.py`

저장소 밖(예: `%TEMP%\qg_live_profile.py`)에 저장하고 저장소 루트에서 실행한다. 이 환경에서 가짜 공급자로 자체 시험을 마쳤다(`test_live_profile.py`). 원본: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/p01/qg_live_profile.py`.

```python
"""QUANTGEN P-01 live profiling, read-only. Save this file OUTSIDE the repository and run it from the repo root.

  python -B qg_live_profile.py portfolio --symbols "AAPL,MSFT,NVDA,TLT,GLD" --source auto --out pf5.json
  python -B qg_live_profile.py lab --family trend_switch --symbols "SPY,QQQ,TLT,GLD" --source yfinance --out lab4.json
  python -B qg_live_profile.py compare before.json after.json

Each run is done twice: 'cold' (an empty, temporary history cache) then 'warm' (the same cache, same input).
Logged per HTTP request: host, path, status, seconds, bytes - never the query string or headers, so no key
or token is ever written. KIS pacing waits, Yahoo/FRED calls (which do not use the shared session) and the
stages (fetch / align / optimise / frontier / walk-forward / score / chart) are timed separately.
Strategy Lab trials are registered in a temporary ledger directory, never in the real one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import sys
import tempfile
import time
from urllib.parse import urlsplit

LOG: list[dict] = []
EXTRA: dict[str, float] = {"kis_pace_s": 0.0, "yahoo_s": 0.0, "yahoo_calls": 0, "yahoo_tickers": 0,
                           "fred_s": 0.0, "fred_calls": 0, "fred_ids": 0}


_DONE = []


def _instrument() -> None:
    if _DONE:                                  # once per process
        return
    _DONE.append(True)
    import data.net as net
    import core.ficc.data as fd
    import data.krx.kis_client as kc
    orig_get = net.session.get

    def get(url, *a, **k):
        t0 = time.perf_counter()
        status, size = None, 0
        try:
            r = orig_get(url, *a, **k)
            status, size = r.status_code, len(r.content or b"")
            return r
        finally:
            u = urlsplit(str(url))
            LOG.append({"host": u.netloc, "path": u.path, "status": status,
                        "s": round(time.perf_counter() - t0, 4), "bytes": size})
    net.session.get = get

    for name, key in (("_yf_fetch", "yahoo"), ("_fred_fetch", "fred")):
        orig = getattr(fd, name)

        def timed(ids, arg, _orig=orig, _key=key):
            t0 = time.perf_counter()
            try:
                return _orig(ids, arg)
            finally:
                EXTRA[f"{_key}_s"] += time.perf_counter() - t0
                EXTRA[f"{_key}_calls"] += 1
                EXTRA[f"{_key}_tickers" if _key == "yahoo" else "fred_ids"] += len(ids)
        setattr(fd, name, timed)

    orig_pace = kc._pace

    def pace():
        t0 = time.perf_counter()
        orig_pace()
        EXTRA["kis_pace_s"] += time.perf_counter() - t0
    kc._pace = pace


def _reset():
    LOG.clear()
    for k in EXTRA:
        EXTRA[k] = 0 if k.endswith(("calls", "tickers", "ids")) else 0.0


def _net_summary() -> dict:
    by_host: dict[str, dict] = {}
    for r in LOG:
        h = by_host.setdefault(r["host"], {"requests": 0, "s": 0.0, "bytes": 0, "lat": [], "non200": 0})
        h["requests"] += 1
        h["s"] += r["s"]
        h["bytes"] += r["bytes"]
        h["lat"].append(r["s"])
        h["non200"] += r["status"] != 200
    for h in by_host.values():
        lat = sorted(h.pop("lat"))
        h["p50_s"] = round(statistics.median(lat), 4)
        h["p95_s"] = round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 4)
        h["s"] = round(h["s"], 3)
    return {"session_requests": len(LOG), "by_host": by_host, **{k: round(v, 4) if isinstance(v, float) else v
                                                                  for k, v in EXTRA.items()}}


def _digest(hists) -> str:
    h = hashlib.sha256()
    for x in hists:
        h.update(repr((x.symbol, x.source, x.adjustment, x.dates, x.closes)).encode())
    return h.hexdigest()[:16]


def run_portfolio(syms, source):
    from core.quant.history import load_history
    from core.quant.optimize import OBJECTIVES, efficient_frontier, optimize_portfolio
    from core.quant.risk import align_histories
    import ui.qcharts as qcharts
    st = {}
    t = time.perf_counter(); hists = [load_history(s, source=source) for s in syms]; st["fetch_s"] = time.perf_counter() - t
    t = time.perf_counter(); stats = align_histories(hists); st["align_s"] = time.perf_counter() - t
    t = time.perf_counter()
    ports = {o: optimize_portfolio(stats, objective=o, rf_rate=0.03, max_weight=1.0) for o in OBJECTIVES}
    st["optimize4_s"] = time.perf_counter() - t
    t = time.perf_counter(); fr = efficient_frontier(stats, rf_rate=0.03); st["frontier_s"] = time.perf_counter() - t
    t = time.perf_counter()
    qcharts.frontier_chart(fr, list(ports.values())); qcharts.corr_heatmap(stats.corr, stats.symbols)
    st["charts_s"] = time.perf_counter() - t
    result = {"history_digest": _digest(hists), "sources": [h.source for h in hists], "sessions": stats.sessions,
              "weights": {o: [float(w) for w in p.weights] for o, p in ports.items()},
              "sharpe": {o: float(p.sharpe) for o, p in ports.items()}}
    return st, result


def run_lab(family, syms, source, days, B):
    import ui.strategy_lab_page as SL
    import ui.xcharts as xc
    from core.quant import strategies as S
    from core.quant import validate as V
    acc: dict[str, float] = {}
    saved = []
    for mod, name, label in ((SL, "load_history", "fetch_s"), (S, "align_panel", "align_s"),
                             (S, "pnl_matrix", "pnl_matrix_s"), (V, "walk_forward", "walk_forward_s"),
                             (SL, "register_trials", "ledger_s"), (V, "score_strategy", "score_s")):
        orig = getattr(mod, name)

        def w(*a, _o=orig, _l=label, **k):
            t0 = time.perf_counter()
            try:
                return _o(*a, **k)
            finally:
                acc[_l] = acc.get(_l, 0.0) + time.perf_counter() - t0
        setattr(mod, name, w)
        saved.append((mod, name, orig))
    try:
        t = time.perf_counter()
        r = SL.run_family(family, syms, source=source, days=days, bootstrap_B=B)
        acc["run_family_total_s"] = time.perf_counter() - t
    finally:
        for mod, name, orig in saved:
            setattr(mod, name, orig)
    t = time.perf_counter()
    try:
        xc.equity_chart(r["wf"].dates, r["equity"], r["bench_equity"], title="x")
        acc["chart_error"] = ""
    except Exception as exc:                  # strategy_lab_page.py:273 as it stands
        acc["chart_error"] = f"{type(exc).__name__}: {exc}"
    acc["chart_s"] = time.perf_counter() - t
    sc = r["score"]
    result = {"sources": r["sources"], "sessions": len(r["panel"]), "decision": sc.decision,
              "sr_oos": float(sc.sr_oos), "dsr": float(sc.dsr), "pbo": float(sc.pbo),
              "chosen": str(r["chosen"]), "equity_last": float(r["equity"][-1])}
    return acc, result


def compare(a_path, b_path) -> int:
    a, b = (json.load(open(p, encoding="utf-8")) for p in (a_path, b_path))
    bad = []
    for phase in ("cold", "warm"):
        ra, rb = a["runs"][phase]["result"], b["runs"][phase]["result"]
        for k in ra:
            x, y = ra[k], rb.get(k)
            if isinstance(x, float):
                if abs(x - y) > 1e-9 * max(1.0, abs(x)):
                    bad.append((phase, k, x, y))
            elif isinstance(x, dict) and x and isinstance(next(iter(x.values())), list):
                for o in x:
                    if max(abs(p - q) for p, q in zip(x[o], y[o])) > 1e-9:
                        bad.append((phase, f"{k}.{o}", x[o], y[o]))
            elif x != y:
                bad.append((phase, k, x, y))
    for row in bad:
        print("DIFF", *row)
    print("REGRESSION", "FAIL" if bad else "PASS", f"({a_path} vs {b_path})")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", choices=("portfolio", "lab", "compare"))
    ap.add_argument("files", nargs="*")
    ap.add_argument("--symbols", default="AAPL,MSFT,NVDA,TLT")
    ap.add_argument("--source", default="auto")
    ap.add_argument("--family", default="trend_switch")
    ap.add_argument("--days", type=int, default=5000)
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--out", default="qg_profile.json")
    ap.add_argument("--cache", default="", help="reuse this history cache dir (before/after regression runs); "
                                                "default: a new empty temp dir, so the first pass is cold")
    a = ap.parse_args(argv)
    if a.scenario == "compare":
        return compare(*a.files[:2])
    tmp = tempfile.mkdtemp(prefix="qg_prof_")
    os.environ["NEXTGEN_FICC_CACHE"] = a.cache or os.path.join(tmp, "cache")   # cold, then warm on the same dir
    os.environ["QUANTGEN_MACRO_DIR"] = os.path.join(tmp, "macro")          # trials go to a throwaway ledger
    sys.path.insert(0, os.getcwd())
    _instrument()
    syms = [s.strip() for s in a.symbols.split(",") if s.strip()]
    out = {"scenario": a.scenario, "symbols": syms, "source": a.source, "python": sys.version.split()[0],
           "platform": platform.platform(), "runs": {}}
    for phase in ("cold", "warm"):
        _reset()
        t = time.perf_counter()
        if a.scenario == "portfolio":
            st, res = run_portfolio(syms, a.source)
        else:
            st, res = run_lab(a.family, syms, a.source, a.days, a.bootstrap)
        wall = time.perf_counter() - t
        net = _net_summary()
        waited = sum(h["s"] for h in net["by_host"].values()) + net["kis_pace_s"] + net["yahoo_s"] + net["fred_s"]
        st["parse_and_overhead_s"] = st["fetch_s"] - waited      # fetch time not spent waiting on the network
        out["runs"][phase] = {"wall_s": round(wall, 3),
                              "stages": {k: round(v, 4) if isinstance(v, float) else v for k, v in st.items()},
                              "network": net, "result": res}
        n = out["runs"][phase]["network"]
        print(f"{phase:4s} wall {wall:7.2f}s  stages {out['runs'][phase]['stages']}  "
              f"requests {n['session_requests']} (+yahoo {n['yahoo_tickers']}, fred {n['fred_ids']})  "
              f"kis pacing {n['kis_pace_s']}s", flush=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("written", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

<!-- verifier-section -->

## 독립 검증 결과

- 검증자: p01_performance 적대적 검증. 감사만 했다. 추적 파일은 고치지 않았다(`git status` 깨끗함).
- 재현 스크립트와 로그는 모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_p01_performance/` 아래에 있다(`v*.py`, `m*.py`, 같은 이름의 `.log`). 하네스 `venv.py`는 HOME·캐시·장부를 작업 폴더로 돌린다. `data.net.session`의 실호출을 막는다. 자격증명은 `DUMMY`다.
- 비밀정보: `.env`를 열지 않았다. 다만 첫 스크립트(`v01_lab_chart.py`)는 `dotenv` 차단을 넣기 전에 실행했다. 그 프로세스에서 `config`의 `load_dotenv()`가 돌았을 수 있다. 출력은 없었고, 합성 데이터만 썼고, 네트워크도 쓰지 않았다. 그 뒤 스크립트는 모두 `dotenv`를 빈 함수로 바꿔서 실행했다.
- 금지 파일 4개는 열지 않았다. 실데이터 확인에는 허용된 캐시 CSV만 썼다(GLD, IAU, XLE, XLB, XLK, QQQ, VIXY, NG_F, ZC_F, ZN_F, ZF_F, GC_F, SI_F, TLT, 005930.KS, 005935.KS).
- 웹 조사는 하지 않았다. yfinance 과거 버전은 PyPI wheel을 내려받아 소스만 읽었다. 실행하지 않았다(`dl_yf/`).

### 발견사항별 판정

| id | 유지 여부 | 정정 판정 | 정정 심각도 | 근거 |
|---|---|---|---|---|
| P01-01 | 유지 | 사실 | P1 | `v01_lab_chart.py`: trend_switch·xs_momentum·pairs 세 계열 모두 `equity_chart`에서 `ValueError ... (722,) and (723,)`가 난다(pairs는 738/739). 실제 페이지에서 Run을 누르면 예외가 작업자 밖으로 나가고 `busy.visible=True`로 남는다. 추가로 확인한 점: 실패할 때마다 matplotlib figure가 1개씩 닫히지 않는다. 25번 실패하면 열린 figure가 25개다(`m03_fig_leak.log`). `_fig()` 뒤, `_to_image()`의 `plt.close` 전에 예외가 나기 때문이다. 수정안과 회귀 테스트는 타당하다. 실패 전 `busy=True`로 FAIL, 수정 후 PASS |
| P01-02 | 유지 | 사실 | P2 | `v02_pbo.py`: (5000,12) S=16에서 현재 구현 7.1~8.8초, A-1 0.14~0.28초. (5000,24)는 9.7초 대 0.40초. 무작위·동일열·공통요인 입력에서 `pbo`·`prob_loss`·`n_splits`가 완전히 같다. Δslope는 7.6e-15 이하다. 상수 현금열이 있는 입력만 다르다(0.000 대 0.098). 이 차이는 P01-11 규칙 때문이고 의도된 것이다. A-1을 메모리에서만 적용하고 기존 테스트 2개를 돌렸다. 둘 다 PASS(`v02b_patched_tests.log`). 주의할 점: 완전 일치는 시드를 고정한 입력에서만 보장된다. 거의 같은 값끼리는 1e-16 차이로 순위가 바뀔 수 있다. A-1은 K×S×G 배열을 만든다(G=12면 약 20 MB). 큰 G에서는 나눠서 계산해야 한다 |
| P01-03 | 유지 | 사실 | P2 | `v03_kis.py`(가짜 KIS, 100행/쪽, 지연 0): 504일 6건 0.60초, 5000일 50건 6.01초. 작업자 4개로 5종목×504일을 받아도 30건 3.60초다. 즉 30×0.12초 바닥 그대로다. 속도 제한을 지키려는 설계상 비용이다. 수정안 (1) 간격 유지, (2) 긴 창 재사용, (3) 겹침을 검사한 뒤 꼬리만 갱신하는 방식은 타당하다 |
| P01-04 | 유지 | 사실(요청 수). 실제 시리즈 수는 추정 | P2 | `v04_kis_markets.py`: 2.5pt 간격 전체 격자 마스터, spot 1126에서 160개 시리즈, 320건 38.34초. 호가를 빼면 160건 19.23초. `index_daily(600)`는 두 번째 호출도 12건이다. 합계 335건은 코드와 맞는다(1+1+320+1+12). 회귀 테스트 2번(`test_option_chain_skips_books_only_when_they_cannot_answer`)은 설계가 모순이다. 호가를 생략할지는 요청 전에 로컬 시계로 정해야 한다. 그런데 테스트는 응답의 `aspr_acpt_hour`를 쓴다. 시계 주입(`now=`)으로 바꿔야 한다. 참고(추정): 38초에 걸쳐 순차로 받기 때문에 같은 보드의 시세 시각이 최대 38초 벌어진다. `as_of`는 루프가 끝난 뒤의 시각이다(`data/kis_markets.py:429`) |
| P01-05 | 유지 | 사실 | P2 | `v05_double_click.py`: 실제 스레드에서 Optimize를 0.05초 간격으로 두 번 누르면 작업자 2개, `load_history` 10회, `button.disabled=False`다. `busy.visible = True` 패턴은 15개 파일에 있다. 추가 근거: 겹친 Strategy Lab 실행 2개가 끝난 뒤 사전 등록 게이트 `V.GATE["bootstrap_B"]`가 2000으로 돌아오지 않는다(V-P01-M3) |
| P01-06 | 유지 | 사실 | P3 | `v06_fmp_seq.py`(지연 150ms, 디스크 캐시 끔): 순차 1/5/20종목은 0.16/0.76/3.06초다. 작업자 4개는 0.15/0.31/0.78초다. 결과는 같다. 다만 수정안 A-3을 Yahoo에 적용하면 yfinance 1.4 미만에서 안전하지 않다. requirements는 `>=0.2`를 허용한다(V-P01-M1). 크립토 `_throttle`에 잠금이 없다는 지적은 맞다(`data/crypto/crypto_client.py:105-109`) |
| P01-07 | 유지 | 사실 | P3 | `core/quant/history.py:427`의 키에 `days`가 들어 있다. A-2 전제는 FMP·KIS에서 성립한다. 둘 다 오늘부터 거슬러 받고, 수정주가는 공급자 쪽 값이다. 따라서 꼬리가 짧은 요청의 결과와 같다. 기존 테스트 `tests/quant_acceptance.py:129-130`과 충돌한다(보고서에 적혀 있다). 그 테스트의 가짜 공급자 `synthetic_history`는 꼬리가 짧은 요청 결과와 같지 않을 수 있다. 그래서 테스트 고정값도 함께 바꿔야 한다 |
| P01-08 | 유지 | 사실 | P3 | `v08_may_be_trading.py`: 1주 15분 간격 표본에서 Yahoo TLT·GC=F 73.2%(=123/168), FMP QQQ 22.3%다. 재현된다. 하지만 수정안 A-6은 Yahoo의 비USD 크립토 쌍(ETH-EUR, BTC-JPY)을 73.2%에서 22.3%로 바꾼다. 24시간 시장을 미국 장 시간으로 판정하게 된다. 정규식을 `^[A-Z]{1,5}(-[A-Z])?$`로 좁혀야 한다(V-P01-M2). 회귀 테스트에 ETH-EUR 사례를 더해야 한다 |
| P01-09 | 유지 | 사실 | P3 | `index_daily`를 다시 불러도 12건이 나간다(`v04`). `crypto_client.py`에는 캐시가 없다(grep). `_yf_fetch`는 `threads=False`다(`core/ficc/data.py:200`). FRED는 id마다 따로 요청한다(`:177`) |
| P01-10 | 유지 | 사실 | P3 | `v10_period.log`: `_period_for(5000)='10y'`, `_period_for(1261)='10y'`. 참고로 `_period_for(504)='2y'`는 약 502세션이라 504보다 적다 |
| P01-11 | 유지(상향) | 사실 | P2 | 함수 수준(`v11_flat_sharpe.py`): 상수 현금열의 Sharpe는 3.47e16~4.65e16이다. walk-forward는 처음 두 원점에서 현금열을 고른다. 상수열이 있으면 PBO는 0.0이다. 보고서는 "실데이터 미관측(추정)"이라고 했다. 이 판단은 틀렸다(`v11b_real_cash_columns.py`). 허용 캐시 VIXY에 trend_switch를 돌리면 평탄한 IS 셀이 40개다. 26개 원점 중 12개가 전액 현금 설정을 고른다. XLE/XLB pairs에서도 1개 원점이 그렇다. 화면 숫자도 바뀐다(`v11c_guard_effect.py`). VIXY의 OOS Sharpe는 현재 −0.418, 0분산 규칙을 넣으면 −0.292다. DSR은 0.034 대 0.074다. 두 사례 모두 결정은 바뀌지 않았다. 실데이터에서 보이는 숫자가 부동소수 잡음에 좌우되므로 P2다. 연구 기록 카드(`S_V1_vix_rolldown`)가 영향을 받는지는 미검증이다. `yf_SPY.csv`가 필요해서 돌리지 않았다 |
| P01-12 | 유지 | 사실 | P3 | `v12_dupes.py`(합성 QQQ, QQQ, TLT): `det(corr)=-4.4e-16`, min_vol 0.334/0.334/0.331, max_sharpe 0.012/0.012/0.976, converged=True |
| P01-13 | 유지(수정안 정정) | 사실(측정). 수정안 효과는 오류 | P3 | `v13_import.py`: `import main`은 3.09~3.65초다. 하지만 시작 화면 `ui.macro_page` 하나만 임포트해도 2.66~2.70초다. 이때 이미 scipy.stats와 `core.quant.garch`를 읽는다(`v13b`). importtime 기준으로 `core.ficc.insights → core.quant.insights` 1.21초, 그 안의 garch 0.75초다(`v13c_importtime.log`). 보고서가 원인으로 본 "bonds 경로 1.81초"는 bonds가 먼저 임포트되어 누적 시간이 그쪽에 잡힌 것일 뿐이다. 페이지를 늦게 임포트해도 0.5초 안팎밖에 줄지 않는다(추정). 정정한 수정안: `core/quant/insights.py:30-35`의 타입용 임포트(BacktestResult, MCResult, OptimizedPortfolio, RiskReport, SignalReport)를 `if TYPE_CHECKING:` 아래로 옮긴다. 이 파일은 `from __future__ import annotations`를 쓰므로 주석에만 쓰이는 이름이다. `LR_5PCT`·`NU_NORMAL`은 `_narrate_garch` 안에서 임포트한다. 회귀 테스트: 새 인터프리터에서 `import ui.macro_page` 후 `"core.quant.garch" not in sys.modules` |

추가 측정(누락 점검). 투자자가 재지 않은 화면의 CPU 시간을 합성 입력, 기본값으로 쟀다(`m01_compute_screens.log`). Quant Lab MC 0.08~0.28초, 파생 합성 보드 0.04~0.11초, Rates 시뮬 0.29~0.35초, Structuring 0.12초, ETF 0.06초, Crypto 0.25초였다. 병목은 없다. pyplot 차트 도우미를 8개 스레드에서 25회씩 동시에 불러도 오류 0건, PNG 불일치 0건이었다(`m02_pyplot_threads.log`). P01-05의 "pyplot 스레드 위험"은 재현되지 않았다(추정 유지).

### 투자자가 놓친 발견사항

#### V-P01-M1 · P2 · 추정 — 수정안 A-3(Yahoo 동시 수집)은 yfinance 1.4 미만에서 결과를 잃는다

| 항목 | 내용 |
|---|---|
| 파일·함수·라인 | 부록 A-3 `load_histories`(ThreadPoolExecutor로 `load_history` 동시 호출) → `core/quant/history.py:272` `yf_history` → `core/ficc/data.py:194-200` `_yf_fetch`(`_yf.download(..., threads=False)`). 허용 버전은 `requirements.txt:13`·`pyproject.toml:16`의 `yfinance>=0.2` |
| 재현 단계 | `pip download yfinance==<v> --no-deps`로 0.2.54, 0.2.66, 1.0, 1.2.0, 1.3.0, 1.4.0, 1.5.2, 1.6.0을 받아 `unzip -p <whl> yfinance/multi.py`의 소스만 읽었다(실행 안 함). 0.2.54~1.3.0은 `download()`가 시작할 때 전역 `shared._DFS = {}`, `shared._ERRORS = {}`로 초기화한다(0.2.54 `multi.py:141-143`). 끝에서는 `_pd.concat(shared._DFS.values(), ...)`로 결과를 만든다(`:214-219`). 1.4.0부터는 호출마다 `_DownloadCtx`를 쓴다. 클라우드 설치본은 1.7.0이라 문제가 드러나지 않는다 |
| 기대 결과 | 허용되는 모든 yfinance 버전에서 동시 수집 결과가 순차 수집과 같다 |
| 실제 결과 | (추정) 1.4 미만에서 스레드 B의 초기화가 스레드 A가 넣은 종목을 지운다. 그러면 A의 `_yf_fetch`가 `{}`나 다른 종목 열을 돌려준다. `yf_history`는 `.get(symbol)`이 비어 `HistoryError("... returned only 0 usable sessions")`를 낸다 |
| 영향 | A-3을 적용한 뒤 Portfolio·Strategy Lab의 Yahoo 기호에서 간헐적 실패가 난다. 소유자 PC의 yfinance 버전은 모른다. 현재 코드(순차 수집)에는 문제가 없다. 제안된 패치가 만드는 위험이다 |
| 수정안 | `requirements.txt:13`과 `pyproject.toml:16`을 `yfinance>=1.4`로 올린다. 또는 `load_histories`에서 YFINANCE로 가는 기호를 풀에서 빼고 `_yf_fetch(list, period)` 한 번으로 묶는다(`threads=min(4, n)`). 예: `-yfinance>=0.2` / `+yfinance>=1.4   # download() keeps per-call state from 1.4.0; load_histories calls it from several threads` |
| 회귀 테스트 | `tests/quant_acceptance.py::test_parallel_yahoo_needs_per_call_download_state`: requirements.txt와 pyproject의 yfinance 하한이 1.4 이상인지 단언한다. 설치된 `yfinance.__version__ >= 1.4`도 단언한다. 그리고 가짜 `_yf_fetch`로 동시 진입 수를 잰다. `__version__`을 "1.3.0"으로 바꾸면 `load_histories`가 최대 동시 진입 1이어야 한다. 현재 저장소(하한 0.2)에서는 FAIL, 수정 후 PASS |

#### V-P01-M2 · P3 · 사실(함수 수준), FMP의 BTCUSD·EURUSD 제공 여부는 추정 — FMP 크립토·FX 기호를 미국 주식 장 시간으로 판정한다. A-6은 같은 오류를 Yahoo 크립토로 넓힌다

| 항목 | 내용 |
|---|---|
| 파일·함수·라인 | `core/quant/history.py:374` `if provider == "FMP" and "." not in s: venue = "US"`. `:493-512` auto 라우팅: `BTCUSD`·`EURUSD`는 KRX·크립토·Yahoo·KIS 모양이 아니어서 FMP로 간다. 부록 A-6 |
| 재현 단계 | `m04_fmp_crypto_venue.py`: 시계를 토요일 2026-10-24 12:00Z로 고정하고 가짜 `fmp_history`를 쓴다. `load_history("BTCUSD")`를 부르고, 5.5시간 뒤 다시 부른다. `v08_may_be_trading.py`: A-6을 메모리에서만 적용한다 |
| 기대 결과 | 크립토(24/7)와 FX(평일 24시간)는 받은 시점의 마지막 봉이 진행 중일 수 있다. 그러니 `provisional_intraday`로 표시하고 10분 TTL을 써야 한다 |
| 실제 결과 | BTCUSD·EURUSD 첫 응답의 status가 `''`다(진행 중 표시 없음). 5.5시간 뒤 호출도 캐시에서 나온다(`cached`). FMP EURUSD는 수요일 02:00Z(아시아 장)에 "장 아님"으로 판정된다. Yahoo `EURUSD=X`는 True다. A-6을 적용하면 Yahoo ETH-EUR·BTC-JPY의 장중 판정 비율이 73.2%에서 22.3%로 떨어진다 |
| 영향 | FMP 형식의 크립토·FX 기호는 최대 6시간(TTL) 묵은 시계열이 될 수 있다. 진행 중인 봉이 종가처럼 남는다. 화면 칩에 "cached"가 보이므로 완전히 숨겨지지는 않는다. A-6을 그대로 적용하면 같은 문제가 Yahoo 비USD 크립토에도 생긴다 |
| 수정안 | `-    if provider == "FMP" and "." not in s:` / `+    if provider == "FMP" and re.fullmatch(r"[A-Z]{1,5}(-[A-Z])?", s):` / `         venue = "US"` / `+    elif provider == "FMP" and "." not in s:` / `+        return True                   # FX (EURUSD) and crypto (BTCUSD) trade outside US hours: keep the short TTL`. A-6은 `elif provider == "YFINANCE" and re.fullmatch(r"[A-Z]{1,5}(-[A-Z])?", s): venue = "US"`로 좁힌다(`re`는 이미 임포트되어 있다) |
| 회귀 테스트 | `tests/quant_acceptance.py::test_the_cache_knows_when_a_market_may_be_trading`에 추가: `_may_be_trading("FMP","BTCUSD", 토 12:00Z) is True`, `_may_be_trading("FMP","EURUSD", 수 02:00Z) is True`, `_may_be_trading("FMP","QQQ", 토 12:00Z) is False`. A-6 적용 시 `_may_be_trading("YFINANCE","ETH-EUR", 화 03:00Z) is True`, `("YFINANCE","TLT", 화 03:00Z) is False`. 첫 단언은 현재 FAIL, 수정 후 PASS |

#### V-P01-M3 · P3 · 사실 — Strategy Lab이 사전 등록 게이트를 잠금 없이 바꾼다. 겹친 실행 뒤 원래 값으로 돌아오지 않는다

| 항목 | 내용 |
|---|---|
| 파일·함수·라인 | `ui/strategy_lab_page.py:124-129`: `saved_b = V.GATE["bootstrap_B"]`, `V.GATE["bootstrap_B"] = bootstrap_B`, `finally`에서 복원한다. 주석은 "a Lab run must not leave it changed"다. `core/quant/validate.py:54`의 기본값은 `bootstrap_B: 2000`이다. `:501`과 `:520`이 이 전역을 읽는다 |
| 재현 단계 | `v05_double_click.py` 2부: 합성 데이터로 `run_family` 스레드 2개를 0.15초 간격으로 시작한다. `score_strategy`는 0.3초 늦춘다 |
| 기대 결과 | 실행이 끝난 뒤 `V.GATE["bootstrap_B"] == 2000` |
| 실제 결과 | `GATE bootstrap_B before: 2000`, `after two overlapping Lab runs: 100`. 실행 B가 A가 바꾼 값을 저장하고, 마지막에 그 값으로 복원한다. UI 기본값이면 1000으로 남는다 |
| 영향 | P01-05(재클릭 미차단)에서 이어지는 결과다. 지금 UI에서 이 전역을 읽는 곳은 Lab뿐이다. Lab은 매번 자기 값을 넣으므로 화면 숫자는 바뀌지 않는다. 같은 프로세스에서 이 값을 읽는 다른 코드는 잘못된 B를 쓴다. 지금은 `validate.py:880-898` 자체 점검뿐이다. 사전 등록 규칙도 깨진다. 두 실행의 B가 다르면 한 실행의 CI가 다른 실행의 B로 계산될 수 있다 |
| 수정안 | 전역을 바꾸지 말고 인자로 넘긴다. `validate.py`: `score_strategy(..., domain=None, bootstrap_B: Optional[int] = None)`, `B = int(bootstrap_B or GATE["bootstrap_B"])`를 두고 `:501`·`:520`에서 `B=B`를 쓴다. `strategy_lab_page.py:124-129`: save/set/restore를 지운다. 그 자리에 `sc = V.score_strategy(wf, grid=grid, full_pnl=M, n_trials=len(grid), bench_daily=bench, bootstrap_B=bootstrap_B)` |
| 회귀 테스트 | `tests/macro_ui_views.py::test_two_overlapping_lab_runs_leave_the_gate_unchanged`: 합성 `run_family` 스레드 2개를 겹치게 돌린다. `score_strategy`는 늦춘다. 끝난 뒤 `V.GATE["bootstrap_B"] == 2000`을 단언한다. 각 결과의 `sr_oos`·`ci90`이 순차 실행 결과와 같아야 한다. 현재 FAIL(100), 수정 후 PASS |
