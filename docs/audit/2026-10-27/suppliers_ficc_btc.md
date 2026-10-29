# 공급사 감사: FICC·BTC — KIS 접근 가능성과 최적 대체 공급사 (`suppliers_ficc_btc`)

> 작성 메모 (오케스트레이터): 하네스가 조사 에이전트의 보고서 파일 쓰기를 막아, 에이전트가 반환한 보고서 본문(report_md)을 내용 변경 없이 옮겼습니다.


- 감사일: 2026-10-27. 대상 HEAD `4665e6e`.
- 감사 차원: 요청서 6장 소유자 메모 두 줄. "(-> 공급사필요)", "(-> FICC/BTC 모두 KIS에서 접근 가능한지, 안된다면 다른 공급사 중 최적화된 공급사 알아서 파악해서 딱 깔끔하고 센스있게 implement 할 것.)"
- 성격: 감사 전용이다. 추적 파일은 하나도 고치지 않았다. 수정안은 부록 A의 diff와 8장의 설계로만 낸다. 구현 코드는 쓰지 않았다. (작업 중 `git status`에 보이는 `docs/audit/2026-10-27/artifacts/*.csv` 변경은 다른 감사 단위의 스크립트가 만든 것이다. 이 단위의 스크립트는 스크래치 폴더에만 쓴다.)
- 비밀정보: `.env`를 열지 않았다. 재현 스크립트는 `dotenv`를 빈 모듈로 바꾸고 키 환경변수를 지운 뒤 `config`를 import한다. 키·토큰을 출력하지 않았다.
- 네트워크: 시장 데이터 공급자에 접속하지 않았다. 재현 스크립트는 소켓과 공유 세션을 막는다. KIS 공식 샘플 저장소는 GitHub에서 받아 텍스트로만 읽었다(코드 실행 없음).
- 금지 파일: `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`는 열지도, 읽지도, 해시하지도 않았다. SF-06의 집계는 `git ls-files`의 파일 이름만 셌다. 패치 검증용 사본은 `docs/asset_expansion/cache`를 빼고 만들었다.
- 테스트: `tests/run_all.py`는 실행하지 않았다. 관련 테스트는 스크립트에서 함수 단위로 불렀다.
- 다른 보고서와의 관계: 아래 항목은 이미 보고됐으므로 다시 세지 않고 참조만 한다. C01 V01-01(김치 프리미엄 FX 나이), V01-03(ECOS·KOSIS 클라이언트 없음), C01 7장 공급자 표. D03-01(합성 FX로 김치 프리미엄), D03-08(출처 칩 규칙). FC-03(KIS 원화 금리 화면 미연결, OECD 월간 KRW 금리), FC-04(KRW 상품에 미국채 곡선), FC-05(미국채 곡선을 스왑 곡선으로). DF-03(진행 중 봉), DF-04(OECD 발표 지연), DF-06(USDT=USD). D-01(Upbit 결측 종가 0.0).

## 0. 요약

1. **KIS로 되는 것.** 국고채 지표금리(1·3·5·10·20·30년), CD 91일, 콜, 회사채 AA- 3년(시장 `I` 일봉과 `comp-interest` 스냅숏), 원/달러 KMB 고시(시장 `X`), KRX 국채·KOFR·미국달러 선물(시장 `CF`), 장내채권 시세·발행정보, 4개 평가사 민평(`avg-unit`, 허용목록 밖·미연결), CME BTC·ETH 선물 시세다. 근거는 코드와 공식 샘플이다. 실서버 응답은 미검증이다.
2. **KIS로 안 되는 것.** 원화 IRS·CRS, OTC 선도 스왑포인트·NDF, 금리 내재변동성, 가상자산 현물이다. 공식 KIS API 카탈로그 334건에 가상자산 항목이 0건이다(`r07`). 2026-09-09부터 한투 앱에 코인원 시세 화면이 붙었지만 앱 안의 링크이고 Open API가 아니다(언론 검색 요약, 미검증).
3. **최적 공급사(요지).** 원화 금리의 이력과 공식값은 **ECOS 817Y002**(무료 키)를 쓴다. 당일값과 교차 검증은 **KIS**를 쓴다. 종목별 크레딧 평가값은 **KIS `avg-unit`**(개인 BYOK)을 쓴다. 환율 현재값은 **KIS `FX@KRW`**, 공식 15:30 이력은 **ECOS 731Y003**이다. 선도는 **KRX 미국달러선물 스트립(KIS)**을 PROXY로 쓴다. 미국 금리는 **FRED + US Treasury XML**이다. BTC는 **Upbit(원화) + Coinbase BTC-USD(달러 다리)**로 하고 **Binance**(USDT·펀딩)는 유지한다. IRS·스왑포인트·금리 vol은 **유료 공급사**가 필요하다(R1 유료 전환과 법률 검토 뒤).
4. **새 발견 7건(P2 3, P3 4).** SF-01 원화 곡선 0.25년 점이 CD 91일. SF-06 벤더 CSV 46개가 라이선스 기록 없이 git에 있다(R1 배포 차단 조건). SF-07 IRS·선도·금리 vol 공급자 부재. SF-02 `bond_daily` 연속조회 무시. SF-03 `front_contract` 이름 충돌. SF-04 `futures_market` 두 갈래 판정. SF-05 크립토 호가통화 표기 오류.
5. SF-01·02·03·05 제안 패치는 스크래치 사본에서 `git apply --check`를 통과했다. 패치본에서 결함 검사 9개가 모두 OK다. 기존 관련 테스트 7개와 모듈 self-check 3개는 패치 전후 모두 PASS다(`r11`).
6. 구현 설계(8장)는 0~5단계다. 0단계는 공급사 추가 없는 소수정이다. 1단계는 ECOS 클라이언트다(V01-03 제안과 같은 모듈 하나로 합친다). 5단계(유료)는 R1 법률 검토 뒤로 미룬다.

## 1. 범위

| 항목 | 대상 |
|---|---|
| 요청서 | `audit_in/audit.txt` 전문. 특히 6장 메모 두 줄, 7장 검증 지시 |
| 연구 노트 | `research_notes/QUANTGEN asset coverage expansion/` 의 `kis_api_audit.md`, `crypto_wallets_connectivity.md`, `bonds_commodities.md`(데이터 원천 항목), `reference_map.md`(공급자 관련 내용 없음 확인) |
| 코드 | `config.py`(공급자 준비, `KIS_QUOTATION_ALLOWLIST`), `data/krx/kis_client.py`, `data/kis_markets.py`, `core/ficc/data.py`, `core/ficc/curve_models.py`, `core/crypto/analytics.py`, `data/crypto/crypto_client.py`, `core/quant/history.py`(라우팅), `ui/crypto_page.py`, `ui/rates_page.py`, `data/macro/series_registry.yaml`, `data/net.py` |
| 가드 | `tests/macro_m0_harness.py`(T-RO-01), `tests/macro_m1_pit.py:1039-1086`(T-RO-02), `tests/acceptance.py:62-75`(test_08/09), `tests/macro_acceptance.py:52-71`(hermetic 접점) |
| 외부 1차 자료 | 공식 저장소 `koreainvestment/open-trading-api` 커밋 `cd63caee`(2026-10-23 17:42 KST), `examples_llm` 333개 파일, `stocks_info` 마스터 헤더, `MCP/KIS Code Assistant MCP/data.csv`(공식 API 카탈로그 334행) |
| 제외 | `paper_live/`, `grokteam/`. 금지 파일 4개 |

## 2. 방법

1. 요청서 전문과 연구 노트 4개를 읽었다. 주장마다 코드 file:line을 확인했다.
2. 공식 KIS 저장소의 333개 샘플을 파싱했다(`kis_inventory.py`). REST 273개 중 계좌번호(`CANO`) 없는 것 200개, 있는 것 73개, 웹소켓 등 60개다. 공식 카탈로그 `data.csv`(334행)의 범주를 셌다.
3. 계열별로 공식 엔드포인트, 계좌번호 사용 여부, 허용목록 포함 여부, QUANTGEN 구현 함수, UI 호출 여부를 표로 만들었다(`r07`).
4. 가설은 합성 데이터와 가짜 전송 계층으로 재현했다(`r02`~`r11`). 허용 캐시 4개(`binance_ETHUSDT.csv`, `binance_funding_BTCUSDT.csv`, `fred_DEXKOUS.csv`, `fred_DGS3MO.csv`)만 읽었다(`r01`).
5. 읽기 전용 가드(T-RO-01, T-RO-02, test_08, test_09)를 HEAD에서 돌리고, 설계 골격을 T-RO-01 스캐너에 넣어 보았다(`r08`).
6. 제안 패치는 `git archive HEAD`로 만든 스크래치 사본 두 벌에서 비교 검증했다(`r11`).
7. 웹 조사: WebSearch 요약과 GitHub 코드 검색(공개 저장소의 ECOS·KRX·data.go.kr 호출 예)을 썼다. 2차 자료는 그렇게 표시했다.
8. 막힌 호스트: WebFetch DNS 실패 — `apiportal.koreainvestment.com`, `ecos.bok.or.kr`, `www.data.go.kr`, `openapi.krx.co.kr`, `docs.upbit.com`, `www.coingecko.com`, `core.asiae.co.kr`, `news.mtn.co.kr`, `bloomingbit.io`. 프록시 CONNECT 403 — `developers.binance.com`, `home.treasury.gov`, `fred.stlouisfed.org`, `docs.coingecko.com`, `apidocs.bithumb.com`, `www.kaiko.com`, `www.bok.or.kr`, `freesis.kofia.or.kr`, `www.kofiabond.or.kr`, `data.krx.co.kr`. `gh search code`는 세션 범위 제한(403)이라 GitHub MCP 코드 검색을 썼다.

## 3. 요청서·문서 주장 검증

| # | 주장 | 출처 | 판정 | 근거 |
|---|---|---|---|---|
| 1 | FICC/BTC를 KIS로 받을 수 있는가 | 요청서 6장 메모 | 부분 사실 | 4장 표. FICC 일부는 됨, IRS·스왑포인트·금리 vol·가상자산 현물은 안 됨 |
| 2 | KIS로 KTB·USD 선물(시장 `CF`), 원화 금리(시장 `I`), 원/달러(시장 `X`), CME BTC 일봉을 받는다 | `data/kis_markets.py:7-16, 50-64` | 코드 사실, 실응답 미검증 | 공식 샘플은 `I: 국채`, `X 환율`을 문서화(`overseas_stock/inquire_daily_chartprice.py:47`). `CF`는 샘플에 없음(샘플은 `F`, `O`, `JF`) |
| 3 | 2026-09-25 탐침에서 모든 엔드포인트가 응답했다 | `data/kis_markets.py:22-25`, `docs/ASSET_EXPANSION_SPEC.md:11-41` | 미검증 | 탐침 원자료가 저장소에 없다. 문서 기록만 있다 |
| 4 | KIS는 가상자산을 주지 않는다 | `docs/ASSET_EXPANSION_SPEC.md:40-44`, `kis_api_audit.md` KQ5 | 사실 | 공식 카탈로그 범주 8개(auth, domestic_bond, domestic_futureoption, domestic_stock, elw, etfetn, overseas_futureoption, overseas_stock). 가상자산 단어 0건(`r07`) |
| 5 | 원화 지표금리는 `comp-interest`와 `frgn_code.mst`의 `RY01xx`에서 온다 | `kis_api_audit.md:415`, `:166` | 사실(일치) | 코드의 `Y01xx`는 마스터 코드에서 분류문자 `R`을 뺀 형태(`kis_api_audit.md:174`의 추론과 같음). 마스터로 확인된 것은 RY0101~RY0104뿐 |
| 6 | 장내채권 일별은 날짜 인자 없이 한 번에 받는다 | `data/kis_markets.py:571-572` | 오류(부분) | 공식 샘플은 `tr_cont` 연속조회를 따른다(`domestic_bond/inquire_daily_price.py:102-110`). SF-02 |
| 7 | `avg-unit`으로 KIS·KBP·NICE·FnP 평가 단가·수익률을 받는다 | `kis_api_audit.md:412, 455` | 사실(샘플) | `chk_avg_unit.py`: `kis_unpr`, `kbp_unpr`, `nice_evlu_unpr`, `fnp_unpr`, `*_erng_rt`, 신용등급. 계좌번호 없음. 허용목록 밖, 미구현 |
| 8 | FICC 공급자는 FRED·Yahoo 두 개다 | `config.py:265-290` | 사실(표시 누락) | KIS의 FICC 기능이 FICC 공급자 목록에 없다. SF-07 |
| 9 | ECOS URL 형식 `…/StatisticSearch/{KEY}/json/kr/{from}/{to}/{stat}/{cycle}/{start}/{end}/{item}` | C01 7장(미검증 표시) | 2차 자료로 확인 | CRAN `ecos` `R/statSearch.R:71`, PublicDataReader `ecos/ecos.py`(독립 구현 2개). 공식 문서는 막힘 |
| 10 | ECOS 시장금리(일별) `817Y002`의 항목 코드 | 레지스트리 "OWNER input" | 2차 자료로 확인 | 국고채 1년 `010190000`, 2년 `010195000`, 3년 `010200000`, 5년 `010200001`, 10년 `010210000`, 20년 `010220000`, 30년 `010230000`, 회사채 AA- 3년 `010300000`, BBB- `010320000`, CD 91일 `010502000`, CP 91일 `010503000`, 콜 `010101000`, KORIBOR 3M `010150000`, 통안 91일 `010400000`, KOFR `010901000`. StatisticItemList 덤프(공개 저장소)에는 시작일: 콜·CD·CP 1995-01-03, 국고채 5년 2000-01-04, 통안 91일 2006-09-25 |
| 11 | 김치 프리미엄은 "FRED fixing"과 비교한다 | `README.md:234`, `core/crypto/analytics.py:106-107` | 사실 | V01-01이 FX 나이 결함을 다룸(반복 안 함). `r01`: 허용 캐시에서 `fred_DEXKOUS` 마지막 값 2026-09-18, `binance_ETHUSDT` 마지막 2026-09-25보다 7일 늦음 |
| 12 | C01 7장 표(KIS 가능 범위) | C01 보고서 | 대체로 사실, 보완 | 빠진 것: `avg-unit` 민평, KRX 미국달러선물의 선도 프록시, IRS·스왑포인트·금리 vol 부재, CD를 곡선 노드로 쓰는 문제(SF-01) |
| 13 | 한투 앱에서 가상자산 시세를 본다 | 언론(2026-09-09) | 사실(앱 한정, 2차) | 코인원이 직접 운영하는 페이지로 넘어가는 구조. KIS Open API 아님. 한투는 코인원 지분 약 20%. 원문은 막혀 검색 요약만 확인 |

## 4. 소유자 메모 답: FICC·BTC를 KIS로 받을 수 있는가

| 계열 | KIS 가능? | KIS 경로 (공식 엔드포인트, tr_id) | 계좌번호 | 허용목록 | QUANTGEN 구현 / 화면 연결 | 판정 |
|---|---|---|---|---|---|---|
| 국고채 지표금리·곡선 | 부분(1·3·5·10·20·30년) | `inquire-daily-chartprice` FHKST03030100, 시장 `I`, `Y01xx` | 없음 | 있음 | `krw_yield_daily`, `krw_curve_panel`(호출처 없음) / 화면 없음(FC-03) | 코드 사실, 응답 미검증. 2·50년 없음 |
| 지표금리 당일 스냅숏 | 됨 | `comp-interest` FHPST07020000 | 없음 | 있음 | `krw_yields_snapshot` / Derivatives의 CD 금리 | 코드 사실. 파라미터가 샘플과 다름(9장) |
| 단기금리 CD·콜 | 됨 | 시장 `I`, `Y0112`, `Y0114` | 없음 | 있음 | 위와 같음 | CP·KOFR·KORIBOR 이력 코드는 없음 |
| 회사채 지표 | 부분 | `Y0102`(AA- 3년), 마스터에 `RY0103`(BBB- 3년) | 없음 | 있음 | 코드표에 AA-만 | 부분 |
| 종목별 민평(평가 4사) | 됨(미연결) | `avg-unit` CTPF2005R | 없음 | **없음** | 없음 | 샘플 사실. 가장 쓸모 큰 미사용 경로 |
| 장내채권 시세·이력·발행정보 | 됨 | `inquire-price` FHKBJ773400C0, `inquire-daily-price` FHKBJ773404C0, `search-bond-info` CTPF1114R, (`inquire-daily-itemchartprice` FHKBJ773701C0, `issue-info` CTPF1101R) | 없음 | 앞 3개만 | `bond_quote`, `bond_daily`(SF-02), `bond_info` / 화면 없음 | 부분 |
| KTB·KOFR·통화·금 선물 | 됨(시장 `CF`) | `inquire-price` FHMIF10000000, `inquire-daily-fuopchartprice` FHKIF03020100 | 없음 | 있음 | `futures_quote`, `futures_daily`, `front_contract`(SF-03) | `CF`는 샘플 미문서, 탐침 기록만 |
| 원화 IRS·CRS | **안 됨** | 없음 | — | — | 없음 | 사실(카탈로그) |
| FX 현물·고시 | 됨 | 시장 `X` `FX@KRW`(KMB), 분봉 `inquire-time-indexchartprice` FHKST03030200(`X`·`KX`) | 없음 | 일봉만 | `usdkrw_daily` / 화면 없음 | 코드 사실 |
| FX 선도·스왑포인트·NDF | **직접은 안 됨** | KRX 미국달러선물(`A75…`, 시장 `CF`)로 거래소 선도 프록시 | 없음 | 있음 | 없음 | 프록시만 |
| 금리 내재변동성 | **안 됨** | 국내 금리옵션 엔드포인트 없음. 해외 금리선물·옵션은 주식계좌 키로 HTTP 500 기록(`kis_markets.py:13-15`) | — | — | 화면은 입력 vol | 사실(코드·기록) |
| 미국 금리 | 일부 | 시장 `I` `Y0202`(10년), `Y0201`(30년), `Y0204`(연방기금) | 없음 | 있음 | 코드표만 | 부분 |
| BTC 현물(원화·달러) | **안 됨** | 카탈로그에 없음. 앱의 코인원 페이지는 API 아님 | — | — | Upbit·Binance가 담당 | 사실 |
| CME BTC·ETH 선물 | 됨(시세만) | `daily-ccnl` HHDFC55020100 | 없음 | 있음 | `ovf_daily`(라우팅은 C01 7장 지적) | 응답 미검증 |

결론: KIS는 원화 금리 지표·국채선물·장내채권·KMB 고시·CME BTC 선물까지는 된다. 이력 깊이, 공식성, 라이선스(제3자 제공 시 KRX 정보이용계약 필요)는 약하다. IRS·스왑포인트·금리 vol·가상자산 현물은 안 된다. 그래서 공급사가 필요하다.

## 5. 발견사항

### 5.1 요약 표

| ID | 심각도 | 판정 | 파일·함수·라인 | 한 줄 |
|---|---|---|---|---|
| SF-01 | P2 | 사실(크기는 추정) | `data/kis_markets.py:62-63`, `core/ficc/curve_models.py:242-257` | 원화 국채 곡선의 0.25년 점이 은행 CD 91일이다 |
| SF-06 | P2 | 사실 | `docs/asset_expansion/cache/` | 벤더 CSV 46개가 라이선스 기록 없이 git에 있다(R1 배포 차단) |
| SF-07 | P2 | 사실 | `core/ficc/data.py:64, 621-632`, `ui/rates_page.py:394, 440`, `config.py:282-290` | 원화 IRS·CRS, 선도 포인트, 금리 vol 공급자가 어디에도 없다 |
| SF-02 | P3 | 사실 | `data/kis_markets.py:570-578` | `bond_daily`가 연속조회를 무시해 첫 쪽만 쓴다 |
| SF-03 | P3 | 추정 | `data/kis_markets.py:743-772` | `front_contract('GOLD')`가 KOFR 코드, `('KOFR')`는 None |
| SF-04 | P3 | 추정 | `data/kis_markets.py:247-253` | 선물 시장코드를 두 갈래로만 판정한다 |
| SF-05 | P3 | 사실 | `data/crypto/crypto_client.py:165, 226` | 크립토 호가통화 표기가 7개 중 5개 틀린다 |

### 5.2 상세

#### SF-01 · P2 · 사실(크기는 추정) — 원화 국채 곡선의 0.25년 점이 CD 91일이다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `data/kis_markets.py:62-63` `KRW_CURVE_TENORS`(첫 노드 `("Y0112", 0.25)`, `:59` 정의 "CD 91d"). `core/ficc/curve_models.py:242-257` `krw_curve_panel`(note `:257` "CD 91d + KTB …"), 모듈 문서 `:16` |
| 재현 단계 | `python3 -B …/r10_krw_curve_cd_basis.py`. `KISMarkets.krw_yield_daily`를 스텁으로 바꾼다. 합성 수준: KTB 1년 2.60, 3년 2.80, 5년 2.90, 10년 3.00, 20년 3.05, 30년 3.00 %. 통안 91일 2.50 %. CD 91일 2.80 %(통안+30bp는 가정) |
| 기대 결과 | 정부 곡선 노드는 무위험 금리만 쓴다. 3개월 점은 통안 91일(ECOS `817Y002/010400000`)이다. CD 91일은 IRS 변동금리 지표로 따로 둔다 |
| 실제 결과 | 패널 첫 점이 0.25년 CD다. 3개월 zero 2.7902 % 대 2.4922 %(+29.8bp). 3개월→1년 선도 2.5136 % 대 2.6138 %(−10.0bp). df(0.25) 0.993049 대 0.993789. 앞단이 3개월 > 1년으로 꺾인다 |
| 영향 | 지금은 호출처가 없다(잠복). FC-03과 FC-04 2단계가 이 함수를 화면에 연결하자고 제안한다. 연결되면 할인계수·선도·캐리·롤다운·구조화 쿠폰이 CD 신용 스프레드만큼 틀린다. FC-03의 제안 테스트 `tenors[0] == 0.25`는 이 결함을 고정한다 |
| 수정안 | 부록 A. `Y0112` 제거, 곡선은 1년부터(1년 미만 평탄 외삽, `r10b`에서 부트스트랩 정상 확인). ECOS 클라이언트 뒤에는 통안 91일을 0.25 노드로 추가. FC-03 테스트 조건 변경 |
| 회귀 테스트 | `test_krw_curve_has_no_cd_node`: `all(c != "Y0112" for c, _ in KRW_CURVE_TENORS)`, 스텁으로 `krw_curve_panel().tenors[0] == 1.0`, note에 "no CD 91d node". `r11`: HEAD BAD, 패치본 OK |

#### SF-06 · P2 · 사실 — 벤더 CSV 46개가 라이선스 기록 없이 git에 있다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `docs/asset_expansion/cache/` 추적 파일 46개(yf_* 40, binance_* 3, fred_* 2, upbit_* 1; 이름만 집계). MANIFEST·licence 파일 없음. 비교: `tests/fixtures/macro/MANIFEST.csv:1`(licence, owner, md5 열)과 그 규칙 "a file without them is not a fixture". `README.md:573-576` |
| 재현 단계 | `git ls-files docs/asset_expansion/cache \| wc -l` → 46. 접두어 집계. 폴더에서 manifest/licence 검색 → 없음 |
| 기대 결과 | R1(지금 무료 배포) 전에 배포물의 제3자 데이터마다 출처·라이선스·재배포 가능 여부가 기록된다. 권리 없는 파일은 배포에서 빠진다 |
| 실제 결과 | 기록이 없다. Yahoo 유래 40개는 개인용 전제다. Upbit 문서 하단은 약관이 허용한 방법 밖의 사용·복제·배포를 금지한다(검색 요약). Binance Vision 약관 PDF는 열지 못했다. FRED 연준 자료 2개는 위험이 낮다(추정) |
| 영향 | 저장소를 그대로 배포하면 공급사 데이터를 재배포한다. 앱 기능 영향은 없다. R1 배포의 차단 조건이다(배포 시점에는 P1로 다룬다) |
| 수정안 | MANIFEST.csv(file, provider, series, retrieved_at_utc, licence, redistribution, owner, md5) 추가. 배포 패키징에서 `redistribution != yes` 제외. 사용자 기기에서 사용자 키로 받는 로컬 캐시로 이동. 목록을 ⑩-1 법률 검토에 넘김 |
| 회귀 테스트 | `test_r1_vendor_cache_has_licence_rows`: 폴더의 모든 데이터 파일이 MANIFEST에 있고 licence가 비어 있지 않으며 redistribution ∈ {yes, no, unknown}. git이 없어도 되게 파일시스템으로 검사 |

#### SF-07 · P2 · 사실 — 원화 IRS·CRS, 선도 포인트, 금리 vol 공급자가 없다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `core/ficc/data.py:64` `SOURCES`, `:621-632` `_SHORT_RATE_IDS`. `data/kis_markets.py` 전체(해당 엔드포인트 없음). `ui/rates_page.py:394, 440`(스왑션 vol은 입력, 기본 80bp/30 %). `config.py:282-290` `ficc_provider_status`(FRED·Yahoo만). FC-05는 반복하지 않음 |
| 재현 단계 | `python3 -B -I …/r07_kis_family_matrix.py <kis_repo> /home/user/quantgen`. 공식 카탈로그 334건 범주와 계열별 매트릭스 |
| 기대 결과 | IRS·CRS 곡선, 선도 포인트, 금리 vol은 이름 있는 공급자를 갖거나, "라이선스 공급사 필요" 상태로 명시된다 |
| 실제 결과 | 공급자가 없다. 무료 공식 API도 찾지 못했다(KMB·인포맥스 기사 표, cbonds 참고치는 API·공식 마감이 아님; 웹 검색 기준). Settings에 상태 표시도 없다 |
| 영향 | 원화 IRS 평가, CRS 베이시스, 선도 포인트, 스왑션·캡 vol이 시장값이 될 수 없다. 프록시를 시장값으로 오인할 수 있다 |
| 수정안 | 8장. 5단계 유료 공급사. 그 전에는 provider-status 비가용 행, PROXY 표기, KRX 미국달러선물 스트립, 실현변동성 프록시 |
| 회귀 테스트 | `test_ficc_provider_status_names_unavailable_families`: `krw_irs`, `fx_forward_points`, `rates_implied_vol` 행이 `ready is False`, `vars == ()`, note에 "licensed" |

#### SF-02 · P3 · 사실 — `bond_daily`가 연속조회를 무시한다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `data/kis_markets.py:570-578`. 소비 `core/quant/history.py:310-311`. 대조 공식 샘플 `domestic_bond/inquire_daily_price/inquire_daily_price.py:102-110` |
| 재현 단계 | `python3 -B …/r06_bond_daily_continuation.py`(가짜 30행×3쪽, `tr_cont` M, M, D) |
| 기대 결과 | `tr_cont` "M"이면 "N"으로 다음 쪽을 받는다(샘플 최대 깊이 10) |
| 실제 결과 | 호출 1회, 90행 중 30행. `days` 인자 없음 |
| 영향 | 채권 가격 이력이 첫 쪽으로 잘린다(탐침 기록 69세션). 실서버의 다중 쪽 여부는 미검증 |
| 수정안 | 부록 A(`max_pages=10` 루프) |
| 회귀 테스트 | `test_bond_daily_follows_tr_cont`: `len == 90`, 호출 `['', 'N', 'N']`. `r11`: HEAD 30행, 패치본 90행 |

#### SF-03 · P3 · 추정 — `front_contract`의 이름 충돌

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `data/kis_markets.py:743-756`(부분 문자열 비교 `:752`), `:759-760` `_FRONT_KEYWORDS`, `:763-772` |
| 재현 단계 | `python3 -B …/r02_kis_master_keywords_and_market_codes.py`, `r11`(KOFR 줄이 금 줄보다 먼저, 둘 다 근월물) |
| 기대 결과 | GOLD → 금선물, KOFR → KOFR선물 |
| 실제 결과 | '금' 검색이 '3개월무위험금리'를 잡는다. `front_contract('GOLD') = A69612`, `('KOFR') = None`. 실제 마스터 종목명은 내려받지 않았다(KIS 헤더의 `RFR : 3개월무위험금리` 근거) |
| 영향 | 잠복. 현재 호출은 KTB3뿐(`:633`). KOFR·금 선물을 쓰면 다른 계약이나 None이 조용히 나온다 |
| 수정안 | 부록 A. 이름 완전 일치. KOFR 이름은 캡처한 마스터 한 줄로 확정 |
| 회귀 테스트 | `test_front_contract_exact_names`: GOLD → A88612, KOFR → A69612, KTB3 → A65612 |

#### SF-04 · P3 · 추정 — 선물 시장코드 두 갈래 판정

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `data/kis_markets.py:247-253`. 진입 `core/quant/history.py:316`, `:338-349` |
| 재현 단계 | `r02`: A04612(VKOSPI) → CF, A08612(KRX300) → CF, A11610(주식선물) → CF |
| 기대 결과 | 지수 상품은 `F`(샘플 "F: 지수선물"), 주식선물은 `JF`(샘플 "JF: 주식선물"), `fo_com_code` 상품만 `CF` |
| 실제 결과 | 01/05/06/07만 F, 나머지는 CF. 서버 반응은 미검증 |
| 영향 | 해당 기호의 이력이 오류가 된다. 빈 응답은 예외로 끝나 틀린 값이 나가지는 않는다 |
| 수정안 | 마스터 소속으로 판정(`fo_com_code` → CF, `fo_stk_code_mts` → JF, 그 밖 F). 마스터가 없으면 추측하지 않고 오류 |
| 회귀 테스트 | `test_futures_market_by_master`: A04612 → F, A11610 → JF, A65612 → CF, 미지 코드 → KISError |

#### SF-05 · P3 · 사실 — 크립토 호가통화 표기 오류

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `data/crypto/crypto_client.py:165`(Upbit 'KRW quote' 고정), `:226`(`symbol[-4:]`). 경로 `core/quant/history.py:289`, `:333-335` |
| 재현 단계 | `python3 -B …/r09_quote_currency_labels.py` |
| 기대 결과 | note가 실제 호가통화를 적는다(요청서 6장 "quote currency") |
| 실제 결과 | USDT-BTC·BTC-ETH → "KRW quote", ETHBTC → "HBTC", BTCFDUSD → "DUSD", BTCTRY → "CTRY". 7개 중 5개 틀림 |
| 영향 | 출처 라벨 오류. USDT-BTC는 `load_history`로 닿는다. 값은 영향 없음 |
| 수정안 | 부록 A `_quote_ccy`. 설계에서는 `Candles.quote_ccy` 필드 |
| 회귀 테스트 | `test_crypto_quote_ccy_labels`: USDT-BTC → ", USDT quote", ETHBTC → ", BTC quote", BTCFDUSD → ", FDUSD quote" |

## 6. 공급사 비교 (계열별 채점)

채점 기준(각 0~3, 합 27). 점수는 판단이다. `?`는 원문을 확인하지 못한 항목이다.
- C 범위: 0 없음, 1 일부, 2 주요 만기·종목, 3 계열 전체.
- H 이력: 0 스냅숏, 1 2년 미만 또는 미상, 2 2~15년, 3 15년 이상.
- F 지연·빈도: 0 주간 이상 지연, 1 다음 영업일, 2 당일 장후, 3 장중.
- $ 비용: 3 무료, 2 무료(계좌 필요), 1 저가, 0 유료 계약.
- L R1 라이선스: 3 공공저작물·재배포 가능, 2 출처표시 조건(BYOK로 안전), 1 개인용·재배포 금지(BYOK만), 0 비공식·불명.
- S 안정성: 3 공식 문서 API, 2 공식이나 일부 미문서, 1 비공식·스크래핑, 0 API 없음.
- K 키: 3 무키, 2 무료 키, 1 계좌·약정 필요, 0 계약.
- A 국내 거주자 접근: 3 문제 없음, 2 차단 위험 공지, 1 제한, 0 불가.
- R 읽기 전용·T-RO-01 적합: 3 GET 시세만, 2 GET이나 키가 주문 권한일 수 있음(T-RO-02 소유자 확인 NOT_RUN), 1 계정 연동, 0 주문 경로 필요.

하드 게이트: (1) 용도에 맞는 F(현재값 표시는 F≥2, 공식 이력은 F≥1). (2) 배포물에 담는 데이터는 L≥2, BYOK 실시간 조회는 L≥1. (3) S≥2.

### 6.1 국고채 지표금리·곡선

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 | 근거 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ECOS 817Y002 | 3 | 3 | 1? | 3 | 2? | 3 | 2 | 3 | 3 | 23 | 1~30년(+50년), 통안, 1995/2000~ |
| KRX Open API `bon/kts_bydd_trd` | 2 | 2 | 1 | 3 | 1? | 3 | 2 | 3 | 3 | 20 | 국채전문유통시장 종목별 체결, 2010-01-04~ |
| 유료(연합인포맥스·Koscom CHECK·Bloomberg) | 3 | 3 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 21 | 계약 필요 |
| KIS 시장 I `Y01xx` | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 16 | 당일값, 이력 깊이 미상 |
| KOFIA 채권정보센터 | 3 | 3 | 2 | 3 | 1? | 0 | 3 | 3 | 3 | 21 | API 없음 → 제외 |

### 6.2 크레딧(회사채 지표·종목별 평가)

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 | 근거 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ECOS 817Y002 | 1 | 3 | 1? | 3 | 2? | 3 | 2 | 3 | 3 | 21 | AA-·BBB- 3년, 산금채, CP |
| 유료 민평(KIS채권평가·KBP·NICE P&I·FnPricing 직접 또는 인포맥스) | 3 | 3 | 2 | 0 | 3 | 3 | 0 | 3 | 3 | 20 | 재배포 계약 가능 |
| KRX `bon/bnd_bydd_trd` | 1 | 2 | 1 | 3 | 1? | 3 | 2 | 3 | 3 | 19 | 일반채권 체결(거래 얇음) |
| data.go.kr 채권시세정보 | 1 | 1? | 1 | 3 | 1~2? | 2 | 2 | 3 | 3 | 18 | `GetBondSecuritiesInfoService_V2/getBondPriceInfo_V2` |
| KIS `avg-unit` | 3 | 1? | 1 | 2 | 1 | 2 | 1 | 3 | 2 | 16 | 4사 평가 단가·수익률·등급, ISIN·기간 |

### 6.3 단기금리(CD·CP·콜·KOFR·KORIBOR·통안)

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 |
|---|---|---|---|---|---|---|---|---|---|---|
| ECOS 817Y002 | 3 | 3 | 1? | 3 | 2? | 3 | 2 | 3 | 3 | 23 |
| FRED OECD `IR3TIB01KRM156N` | 1 | 3 | 0 | 3 | 2 | 3 | 3 | 3 | 3 | 21(F 게이트 탈락) |
| KIS `Y0112`·`Y0114` | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 15 |

### 6.4 원화 IRS·CRS

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 |
|---|---|---|---|---|---|---|---|---|---|---|
| 유료(인포맥스·CHECK·Bloomberg·LSEG·Cbonds API) | 3 | 3 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 21 |
| 웹 공시(KMB, 인포맥스 기사 표, cbonds 참고치) | 2 | ? | 1 | 3 | 0 | 0 | 3 | 3 | 1 | — (게이트 탈락) |
| KIS, ECOS | 0 | — | — | — | — | — | — | — | — | 없음 |

### 6.5 FX 현물·고시

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ECOS 731Y001(매매기준율)·731Y003(15:30 종가) | 2 | 3 | 1? | 3 | 2? | 3 | 2 | 3 | 3 | 22 | 공식 이력 |
| FRED DEXKOUS(H.10) | 2 | 3 | 0 | 3 | 3 | 3 | 3 | 3 | 3 | 23 | 주간 공표 → 현재값 게이트 탈락(V01-01) |
| Yahoo `KRW=X` | 3 | 3 | 3 | 3 | 0 | 1 | 3 | 3 | 3 | 22 | 개인용·비공식 |
| KIS `FX@KRW` | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 16 | 당일 KMB 고시 |

### 6.6 FX 선도·스왑포인트·NDF

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CIP 모델(ECOS CD 91일 + FRED SOFR) | 2 | 3 | 1 | 3 | 2 | 3 | 2 | 3 | 3 | 22 | 모델값 → PROXY |
| 유료(서울외국환중개·인포맥스 스왑포인트, Bloomberg NDF) | 3 | 3 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 21 | 시장값 |
| KIS KRX 미국달러선물 스트립(`A75…`, 상장 월물 다수) | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 15 | 거래소 선도 → PROXY |

### 6.7 금리 변동성

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 실현변동성 프록시(ECOS 금리, KIS KTB 선물) | 1 | 3 | 1 | 3 | 2 | 3 | 2 | 3 | 3 | 21 | 내재 아님 → PROXY |
| 유료(ICE MOVE 라이선스, 스왑션 vol 벤더) | 3 | 3 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 21 | |
| Yahoo `^MOVE` | 1 | 3 | 2 | 3 | 0 | 1 | 3 | 3 | 3 | 19 | 개인용(`core/ficc/context_log.py:430`에서 사용) |
| KIS | 0 | — | — | — | — | — | — | — | — | — | 국내 금리옵션 없음, 해외 HTTP 500 기록 |

### 6.8 미국 금리

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 |
|---|---|---|---|---|---|---|---|---|---|---|
| US Treasury XML(`daily_treasury_yield_curve`) | 2 | 3 | 2 | 3 | 3? | 3 | 3 | 3? | 3 | 25 |
| FRED(현행) | 3 | 3 | 1 | 3 | 2? | 3 | 3 | 3 | 3 | 24 |
| KIS 시장 I | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 15 |

### 6.9 BTC 원화 현물

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 |
|---|---|---|---|---|---|---|---|---|---|---|
| Upbit(현행) | 3 | 3 | 3 | 3 | 1? | 3 | 3 | 3 | 3 | 25 |
| Bithumb(같은 `/v1/candles/days` 형식) | 3 | 2? | 3 | 3 | 1? | 3 | 3 | 3 | 3 | 24 |
| Coinone | 2 | 1? | 3 | 3 | 1? | 2 | 3 | 3 | 3 | 21 |
| KIS | 0 | — | — | — | — | — | — | — | — | 없음 |

### 6.10 BTC 달러 기준·파생

| 공급사 | C | H | F | $ | L | S | K | A | R | 합 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Binance spot·fapi(현행; `data-api.binance.vision`, 대량 `data.binance.vision`) | 3 | 3 | 3 | 3 | 1? | 3 | 3 | 2 | 3 | 24 | USDT 호가, 펀딩·OI |
| Coinbase Exchange `BTC-USD`, `USDT-USD` | 2 | 3 | 3 | 3 | 1? | 3 | 3 | 2? | 3 | 23 | **USD** 다리 |
| 유료(Kaiko·CoinDesk Data·Coin Metrics) | 3 | 3 | 3 | 0 | 3 | 3 | 0 | 3 | 3 | 21 | 재배포 계약 |
| Yahoo `BTC-USD` | 2 | 3 | 3 | 3 | 0 | 1 | 3 | 3 | 3 | 21 | 개인용 |
| CoinGecko Demo | 3 | 1 | 2 | 3 | 1 | 2 | 2 | 3 | 3 | 20 | 출처표시, 월 1만 호출(2차) |
| KIS CME BTC 선물 | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 2 | 15 | 규제 선물 기준가 |

## 7. 권장 공급사 (계열별)

| 계열 | 1순위 | 2순위·교차 검증 | 이유 |
|---|---|---|---|
| 국고채 곡선 | ECOS 817Y002 | KIS 시장 I(당일), KRX `kts_bydd_trd`(종목) | 공공기관 공표, 긴 이력, 무료 키, BYOK로 R1 안전. KIS는 당일성이 장점이나 이력·라이선스가 약함 |
| 곡선 3개월 점 | ECOS 통안 91일(`010400000`) | 없음(1년부터 시작) | CD는 무위험이 아님(SF-01) |
| 크레딧 지표 | ECOS AA-·BBB- 3년 | — | 공식 지표 |
| 종목별 크레딧 평가 | KIS `avg-unit`(개인 BYOK) | 유료 민평(배포 단계) | 4사 평가가 무료로 닿는 유일한 경로. 재배포는 불가 |
| 단기금리 | ECOS(CD, CP, 콜, KOFR, KORIBOR) | KIS `Y0112`·`Y0114`(당일) | FC-03의 OECD 월간 대체. KRW 단기금리는 용도별로 고른다: CIP·IRS 변동다리 = CD 91일, 무위험 = KOFR |
| 원화 IRS·CRS | 유료 1곳(인포맥스 또는 Bloomberg/LSEG) | — | 무료 공식 API 없음. 그 전에는 비가용 표시 |
| FX 현재값 | KIS `FX@KRW`(KIS 설정 시) | ECOS 731Y001 전일, Yahoo `KRW=X`(개인용 보조) | V01-01 순서와 같음 |
| FX 공식 이력 | ECOS 731Y003(15:30 종가) | FRED DEXKOUS(장기 연구용) | 레지스트리 `ECOS_1530_CLOSE`와 같음 |
| FX 선도 | KRX 미국달러선물 스트립(KIS, PROXY) | CIP 모델(ECOS CD + SOFR, PROXY) | OTC 포인트·NDF는 유료 |
| 금리 vol | 사용자 입력 유지 + 실현변동성 PROXY | 유료(배포 단계) | 무료 내재 원천 없음 |
| 미국 금리 | FRED(현행, SOFR 포함) | US Treasury XML(곡선 1차·공공저작물) | 배포 단계에서 Treasury가 라이선스상 유리(추정) |
| BTC 원화 | Upbit | Bithumb(교차 거래소) | FIU 신고 거래소, 2017-09-25~ 이력 |
| BTC 달러 | Coinbase `BTC-USD` | Binance `BTCUSDT`(USDT), KIS CME 선물(규제 기준) | DF-06 해결: 김치 프리미엄을 USD 기준으로 계산하고 USDT 프리미엄을 따로 분해 |
| 크립토 파생 | Binance fapi(현행) | — | 펀딩 2019-09-10~, OI 30일 |
| 배포 유료 단계(크립토) | Kaiko 또는 CoinDesk Data | Coin Metrics | 재배포 라이선스 |

## 8. 구현 설계 (승인용, 코드 미작성)

### 8.1 원칙

1. **BYOK.** 키는 사용자가 발급한다(ECOS 무료 키, KIS 앱키). 앱은 공급사 데이터를 배포물에 담지 않는다. 호스팅·중계 서버를 두지 않는다. KIS 시세를 제3자에게 보여 주려면 KIS 제휴와 KRX 정보이용계약이 필요하다(제휴 안내, 검색 요약).
2. **읽기 전용.** 모든 호출은 GET 시세·참조다. T-RO-01 스캐너가 새 모듈을 자동으로 검사한다(`core/`, `data/`, `ui/` 전체). 설계 골격(ECOS, Coinbase)은 스캐너 통과, 주문 URL POST 예시는 적발(`r08`).
3. **문구 주의.** `tests/acceptance.py:71-75` test_09는 주석까지 포함한 원문에서 계좌번호 필드 이름 세 개(`KIS_ACCOUNT` 등)를 금지한다. 새 코드의 주석·문서에도 이 단어를 쓰지 않는다(`r08`의 `bad_word.py` 예).
4. **단일 네트워크 접점.** 공급자마다 함수 하나만 소켓을 연다. `tests/macro_acceptance.py:52-71` `_touchpoints()`에 등록해 hermetic을 지킨다.
5. **키 노출 금지.** ECOS는 키가 URL 경로에 있다. 예외 문자열에 URL이 들어가므로 `core/quant/history.py`의 FMP `_redact` 방식을 따른다. `data/net.py:52`의 urllib3 로그 억제는 유지한다.

### 8.2 모듈

| 모듈 | 내용 |
|---|---|
| `data/ecos/ecos_client.py`(신규, V01-03과 같은 모듈) | `_ecos_fetch(stat, cycle, start, end, item)` 하나. `ECOS_SERIES` 목록: QUANTGEN id → (통계표, 주기, 항목, 단위, 라벨). 국고채 1·2·3·5·10·20·30·50년, 통안 91일·364일, CD, CP, 콜, KOFR, KORIBOR 3M, 회사채 AA-·BBB- 3년, 기준금리 722Y001, 원/달러 731Y001·731Y003. 행 범위 페이징(요청시작·종료건수). `RESULT.CODE`(INFO-xxx/ERROR-xxx) → `ECOSError`(키 없는 메시지) |
| `config.py` | `ecos_key()`, `ecos_ready()`, `ECOS_BASE_URL`(https), `ficc_provider_status()`에 ECOS·KIS 금리 행과 비가용 행(`krw_irs`, `fx_forward_points`, `rates_implied_vol`) 추가. 값은 절대 반환하지 않음 |
| `core/ficc/data.py` | `SOURCES`에 `ecos`, `kis` 추가. `load_curve(market="KRW", source=…)`(FC-03 제안과 하나로) → ECOS 곡선(통안 91일 + 국고채), 실패 시 KIS 곡선(1년부터), 명시 공급자는 예외. `load_short_rate("KRW")` 선택지: ECOS CD 91일(일간) → KIS `Y0112` → FRED OECD(월간, 45일 초과면 note에 STALE) |
| `core/ficc/curve_models.py` | `krw_curve_panel` CD 노드 제거(SF-01). ECOS판 `krw_curve_panel_ecos` 또는 `load_curve`로 통합 |
| `data/kis_markets.py` | `bond_evaluations(isin or None, start, end)`(`avg-unit`, `CTX_AREA_NK30`·`FK100`·`tr_cont` 페이징; 필드 kis/kbp/nice/fnp 단가·수익률·등급). `bond_daily` 페이징(SF-02). `usd_futures_strip()`(마스터 USD 상장 월물 → `futures_quote`; 선도 포인트 = 선물 − 현물, PROXY). `front_contract` 완전 일치(SF-03), `futures_market` 마스터 판정(SF-04) |
| `data/crypto/crypto_client.py` | `CoinbasePublic.daily(product="BTC-USD")`(granularity 86400, 1회 300개, 무키). `Candles`에 `quote_ccy`, `bar_close_utc`, `complete`, `fetched_at` 추가. `_quote_ccy`(SF-05). 선택: `BithumbPublic`(Upbit 파서 재사용), Binance 월별 zip 대량 이력(체크섬 검증) |
| `core/crypto/analytics.py` | `kimchi_premium`에 USD 다리 입력(Coinbase) + USDT 프리미엄 분해(Upbit `KRW-USDT` ÷ USD/KRW − 1). V01-01의 FX 나이 제한 적용 |
| `data/treasury/ust_client.py`(선택) | Treasury XML `daily_treasury_yield_curve`, 연도별 GET. FRED와 교차 |
| `data/macro/series_registry.yaml` | 새 시리즈는 `display`/`context` 역할로만 등록. rules store가 우선이므로 소유자 승인 사항 |

### 8.3 허용 엔드포인트

| 공급자 | 엔드포인트 | 비고 |
|---|---|---|
| KIS(추가) | `/uapi/domestic-bond/v1/quotations/avg-unit` (CTPF2005R) | 허용목록 25 → 26. `tests/macro_m1_pit.py:1047`의 `len(allow) == 25`를 26으로. 같은 테스트가 `used == allow`를 `kis_client.py`, `kis_markets.py`, `docs/kis_quote_check.py` 세 파일에서만 세므로 호출부는 `data/kis_markets.py`에 둔다(다른 파일에 두면 실패, `r08` 확인) |
| KIS(선택) | `/uapi/domestic-bond/v1/quotations/inquire-daily-itemchartprice` (FHKBJ773701C0) | 필요할 때만. 분봉 FX(`inquire-time-indexchartprice`)는 일간 앱에 불필요 → 추가 안 함 |
| ECOS | `GET /api/StatisticSearch/{key}/json/kr/{s}/{e}/{stat}/{cycle}/{from}/{to}/{item}`, 검증용 `StatisticItemList` | https만 |
| Coinbase | `GET https://api.exchange.coinbase.com/products/{id}/candles` | 무키 |
| Binance(선택) | `GET https://data.binance.vision/data/spot/monthly/klines/{SYM}/1d/…zip` + `.CHECKSUM` | 무키 |
| US Treasury(선택) | `GET https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={yyyy}` | 무키 |

### 8.4 캐시

- 기존 FICC 디스크 캐시를 쓰되 C01의 강화안(스키마 버전, 읽기 검증, 원자적 쓰기)을 전제로 한다.
- 키: `provider_id_days` 그대로. ECOS는 하루 한 번 공표 → TTL 6시간. KIS 시장 I는 진행 중 봉 규칙(10분, `core/ficc/data.py:217-265`) 적용.
- KIS 마스터는 날짜를 키에 넣어 하루 단위로 새로 받는다(C01-08(4)).
- Binance 월별 zip은 불변 → 체크섬 일치 시 무기한.
- 합성 결과는 캐시하지 않는다(현행 유지).

### 8.5 출처 표기 (D-03·D-04 정합)

- 모든 시계열: `source`(ECOS, KIS, FRED, UST, YFINANCE, UPBIT, BINANCE, COINBASE, SYNTHETIC, ASSUMED, UNAVAILABLE), `unit`(pct, KRW_per_USD, KRW, USDT, USD), `note`(사유, 빈도, STALE).
- 시각: `obs_date`, `retrieved_at_utc`(= D-05의 `fetched_at`), 공표 규칙은 레지스트리 schedule id(ECOS는 `AS_POSTED`, Treasury는 `TREASURY_PAR`, KIS 스냅숏은 `LIVE_QUOTE`). 가능하면 `core.ficc.pit.ingest_rows`를 거친다.
- 크립토 봉: `venue`, `quote_ccy`, `bar_close_utc`, `complete`.
- 결과물: D-03 2단계의 `sources: tuple[str, ...]`.
- 프록시(선물 스트립 선도, CIP 선도, 실현변동성, KTB par를 스왑 곡선 대용): `note`가 "PROXY:"로 시작한다. 칩 토큰은 D-03 `SOURCE_TOKEN`에 `PROXY → warning`을 추가할지 소유자가 정한다.
- 라이선스: 시리즈마다 `licence` 짧은 id(예: `ecos-terms`, `kis-personal`, `yahoo-personal`, `us-gov-work`)를 note나 메타에 남긴다.

### 8.6 실패 동작

1. 명시 공급자 실패는 예외다(현행 규칙 유지).
2. `auto` 사슬: 원화 금리 ECOS → KIS → (단기금리만) FRED OECD(STALE 표기) → UNAVAILABLE.
3. 여러 공급자를 섞는 계산(김치 프리미엄, CIP 선도, 곡선)은 다리 하나라도 SYNTHETIC이면 계산을 거부하고 UNAVAILABLE을 낸다(D03-01과 같은 방향).
4. 오래된 실데이터 캐시는 합성보다 우선하고 STALE을 붙인다(D03-07 제안과 같음).
5. 키가 없으면 해당 행은 Settings에 "not configured"로만 나오고 화면은 배너로 말한다.

### 8.7 테스트 (모두 hermetic)

| 테스트 | 단정 |
|---|---|
| `test_v01_ecos_client_is_one_touchpoint_and_hermetic`(C01 제안과 동일) | `_touchpoints()`에 `_ecos_fetch`; 키 없으면 `ECOSUnavailable` |
| `test_ecos_key_never_in_errors` | URL에 키가 든 `ConnectionError` → 예외 문자열과 `Series.note`에 키 없음 |
| `test_ecos_parses_statisticsearch_rows` | 고정 JSON(`TIME` 20261023, `DATA_VALUE` "2.851", `UNIT_NAME` "연%") → `source == "ECOS"`, `unit == "pct"`, 날짜 ISO |
| `test_ecos_no_data_is_empty_not_synthetic` | `RESULT.CODE` 무자료 → 명시 `ecos`는 예외, `auto`는 다음 공급자 |
| `test_krw_curve_has_no_cd_node` | SF-01 |
| `test_krw_curve_front_is_msb_when_ecos` | ECOS 스텁 → `tenors[0] == 0.25`이고 note에 MSB |
| `test_load_short_rate_krw_prefers_daily` | ECOS 스텁 → `source == "ECOS"`, note "daily"; ECOS 실패+KIS 스텁 → "KIS"; 둘 다 실패 → FRED 월간, 45일 초과 시 "STALE" |
| `test_bond_daily_follows_tr_cont` | SF-02 |
| `test_bond_evaluations_pages_ctx_area` | `avg-unit` 가짜 2쪽 → 행 전부, 4사 필드 매핑 |
| `test_ro_02_kis_client_accepts_only_allowlisted_quotation_paths`(수정) | `len(allow) == 26`, `avg-unit` 사용처가 `data/kis_markets.py` |
| `test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path`(무수정) | 새 모듈 포함 통과 |
| `test_front_contract_exact_names` | SF-03 |
| `test_futures_market_by_master` | SF-04 |
| `test_crypto_quote_ccy_labels` | SF-05 |
| `test_kimchi_premium_uses_usd_leg` | Coinbase·Upbit 스텁, USDT 0.99 → USD 기준 프리미엄 0.00 %, USDT 프리미엄 따로 보고 |
| `test_candles_flag_incomplete_last_bar` | `bar_close_utc > fetched_at`이면 `complete is False` |
| `test_ficc_provider_status_names_unavailable_families` | SF-07 |
| `test_r1_vendor_cache_has_licence_rows` | SF-06 |

### 8.8 라이선스 메모 (R1: 지금 무료 배포, 법률 검토 뒤 유료)

| 공급자 | 무료 배포(BYOK) | 유료 단계 | 확인 상태 |
|---|---|---|---|
| ECOS | 사용자 키, 출처 "자료: 한국은행 ECOS" 표기 | 약관의 상업적 이용 조항 확인 필요 | 미검증(호스트 차단) |
| KIS | 사용자 본인 계좌·앱키로만. 앱이 KIS 데이터를 저장·배포·중계하지 않음 | 제3자 서비스는 KIS 제휴 + KRX·해외거래소 정보이용계약 | 제휴 안내 검색 요약 |
| KRX Open API | 사용자 키 | 약관 확인 | 미검증 |
| data.go.kr(FSC) | 사용자 키 | 데이터별 공공누리 유형 확인(2유형이면 상업적 이용 불가) | 미검증 |
| FRED | 사용자 기기 조회. 제3자 저작권 계열(ICE BofA OAS 등)은 개인용 외 소유자 허락 필요 | 공공 계열만 | 검색 요약 |
| US Treasury | 미 연방 저작물 | 재배포 가능성 높음 | 추정 |
| Yahoo | 개인용 | 유료 단계에서 제거 | 일반 원칙 |
| Upbit·Bithumb·Binance·Coinbase | 사용자 기기 조회만, 캐시 배포 금지 | 재배포는 유료 라이선스(Kaiko·CoinDesk Data 등) | 원문 미확인 |
| CoinGecko | Demo 출처표시 | 상업용은 유료 플랜 | 2차 |

### 8.9 단계와 순서

| 단계 | 내용 | 공급사 추가 | 선행 |
|---|---|---|---|
| 0 | SF-01·02·03·05 패치(부록 A), SF-04, SF-06 MANIFEST. FC-03 연결은 SF-01 뒤 | 없음 | 없음 |
| 1 | ECOS 클라이언트(V01-03과 통합), `load_curve`, `load_short_rate("KRW")` 교체 | ECOS | 소유자 ECOS 키 |
| 2 | KIS `avg-unit`, 채권 페이징, USD 선물 스트립, 허용목록 26 | 없음(KIS 확장) | 허용목록 변경 승인 |
| 3 | Coinbase USD 다리, `quote_ccy`·`complete`, 김치 분해, (선택) Bithumb·Binance 대량 | Coinbase | 없음 |
| 4 | US Treasury XML(선택) | Treasury | 없음 |
| 5 | IRS·CRS·스왑포인트·금리 vol, 크립토 재배포 라이선스 | 유료 1~2곳 | R1 유료 전환 + ⑩-1 법률 검토 + 견적 |

### 8.10 소유자 결정 사항

1. ECOS 키 발급(무료, BYOK).
2. KIS 허용목록 25 → 26(`avg-unit`) 승인과 T-RO-02 테스트 수정.
3. D-03 출처 어휘에 `PROXY`(warning) 추가 여부.
4. 새 시리즈의 레지스트리 역할(display/context) — rules store가 우선.
5. R1 배포 형태: BYOK만, 벤더 캐시 미포함(SF-06).
6. KOFR 선물 마스터 한 줄 캡처(SF-03 확정용).
7. 유료 공급사 선택 시점과 예산(5단계).

## 9. 미검증 항목

- KIS 실서버 응답 전부: 시장 I의 `Y01xx` 코드(마스터 확인은 RY0101~RY0104뿐), 시장 `CF`, `comp-interest` 파라미터(코드는 `FID_DIV_CLS_CODE` "", 공식 샘플은 필수값 '1'), 이력 깊이, `avg-unit` 범위, CME BTC 선물 일봉, `bond_daily`의 실제 연속조회.
- KIS 마스터 내용(KOFR 종목명, prod_no가 B03인지 BM3인지).
- KIS 약관 원문(포털 DNS 실패). 한투 앱 코인원 시세(언론 원문 차단).
- ECOS 약관·호출 한도·공표 지연·무자료 응답 코드. 항목 코드는 공개 저장소(2차)로만 교차 확인. 731Y003/0000003을 매매기준율로 적은 저장소 1곳과 충돌.
- KRX Open API 약관·한도. data.go.kr 채권시세정보의 이용허락범위.
- Upbit·Bithumb·Binance·Coinbase·CoinGecko 재배포 조항 원문.
- 원화 IRS·CRS·스왑포인트의 무료 공식 API 부재(검색 기준).
- US Treasury 자료의 퍼블릭 도메인 여부(일반 원칙 기준 추정). FRED API 약관 세부(검색 요약).
- SF-01의 CD−통안 스프레드 크기(30bp 가정).
- KRX 국채선물옵션 상장 여부.
- Binance·Coinbase 호스트의 국내 도달성.
- 유료 공급사 가격과 재배포 조건.
- Coinbase 공개 캔들 한도·시작일, `data.binance.vision` 현물 타임스탬프 단위.

## 10. 재현 스크립트 경로

모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/` 아래다. 출력은 같은 폴더의 `*_output.txt`.

- 공통 가드: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/_hermetic.py`(dotenv 스텁, 소켓 차단)
- KIS 샘플 목록화: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/kis_inventory.py` → `kis_inventory.json`, `kis_inventory_output.txt`
- R01 캐시 공백·FX 지연: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r01_cache_gaps_and_fx_lag.py`
- R02 마스터 키워드·시장코드(SF-03, SF-04): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r02_kis_master_keywords_and_market_codes.py`
- R03 스왑 par = 미국채 par(FC-05 참고용): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r03_swap_par_is_treasury_par.py`
- R04 KRW 단기금리 나이(FC-03 참고용): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r04_krw_short_rate_staleness.py`
- R05 크립토 출처(참고용, D-01·DF-03·DF-06 영역 포함): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r05_crypto_provenance.py`
- R06 채권 연속조회(SF-02): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r06_bond_daily_continuation.py`
- R07 계열별 KIS 매트릭스(4장, SF-07): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r07_kis_family_matrix.py`
- R08 읽기 전용 가드와 설계 골격: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r08_readonly_guard_constraints.py` (골격: `design_skeletons/`)
- R09 호가통화 표기(SF-05): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r09_quote_currency_labels.py`
- R10 CD 노드 영향(SF-01): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r10_krw_curve_cd_basis.py`, 수정 확인 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r10b_curve_without_cd_node.py`
- R11 패치 전후 검증: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/r11_patch_verify.py` (사본: `patch/orig`, `patch/tree`; 패치 파일 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/suppliers_ficc_btc/patch/proposed_sf01_sf02_sf03_sf05.patch`)
- R11 결과: HEAD는 결함 검사 9개 중 7개 BAD(KTB3·KRW-BTC·BTCUSDT 3개만 OK), 패치본은 9개 모두 OK. 기존 테스트 7개(`test_kis_markets_paging_and_shapes`, `test_master_parsers`, `test_crypto_client_refusals_and_router`, T-RO-01, T-RO-02, test_08, test_09)와 `python -m` self-check 3개(`data.kis_markets`, `data.crypto.crypto_client`, `core.ficc.curve_models`)는 양쪽 모두 PASS. 클라우드 기준선(`baseline2_results.json`)에서도 이 테스트들은 PASS.

## 부록 A. 제안 패치 (SF-01, SF-02, SF-03, SF-05; HEAD `4665e6e`에서 `git apply --check` 통과, 미적용)

```diff
--- a/core/ficc/curve_models.py
+++ b/core/ficc/curve_models.py
@@ -13,8 +13,8 @@
                   half-life and ADF from `core.quant.strategies`
   bond_carry      Koijen, Moskowitz, Pedersen & Vrugt (2018) eq. (15):
                   carry = (y_T − r_short) + D_mod·(y_T − y_{T−h}) (slope + roll-down)
-  krw_curve_panel CD 91d + KTB 1/3/5/10/20/30y par yields from the KIS chart
-                  endpoint (percent → decimals), as a `CurvePanel`
+  krw_curve_panel KTB 1/3/5/10/20/30y par yields from the KIS chart endpoint
+                  (percent → decimals), as a `CurvePanel`; no CD 91d node
 
 Citations to the user's materials: Berkeley TS lecture 6 §1.1 (AR(1) forecast,
 half-life); 계량2 §2.4.1, §2.4.3 (forecast evaluation), §5.3 (unit roots);
@@ -240,8 +240,9 @@
 # KRW curve from KIS
 # --------------------------------------------------------------------------- #
 def krw_curve_panel(*, days: int = 504) -> CurvePanel:
-    """CD 91d and KTB 1/3/5/10/20/30y par yields from the KIS chart endpoint,
-    intersected on shared dates, percent → decimal."""
+    """KTB 1/3/5/10/20/30y par yields from the KIS chart endpoint, intersected
+    on shared dates, percent → decimal. CD 91d is a bank rate and is not a node
+    (`data.kis_markets.KRW_CURVE_TENORS`)."""
     from data.kis_markets import KISMarkets, KRW_CURVE_TENORS
     km = KISMarkets()
     series = {}
@@ -254,7 +255,8 @@
     tenors = tuple(t for _, t in KRW_CURVE_TENORS)
     Y = np.array([[series[t][d] / 100.0 for t in tenors] for d in common])
     return CurvePanel(source="KIS", dates=tuple(common), tenors=tenors, yields=Y,
-                      note="KRW par grid: CD 91d + KTB 1/3/5/10/20/30y (KIS chart endpoint, percent → decimal)")
+                      note="KRW par grid: KTB 1/3/5/10/20/30y (KIS chart endpoint, percent → decimal); "
+                           "below 1y the curve is flat-extrapolated, no CD 91d node")
 
 
 # --------------------------------------------------------------------------- #
--- a/data/crypto/crypto_client.py
+++ b/data/crypto/crypto_client.py
@@ -58,6 +58,18 @@
 _last_call = {"t": 0.0}
 
 
+_QUOTES = ("FDUSD", "USDT", "USDC", "TUSD", "BUSD", "BTC", "ETH", "BNB", "EUR", "TRY", "BRL", "JPY", "KRW")
+
+
+def _quote_ccy(symbol: str) -> str:
+    """Quote asset of a Binance pair by its known suffix (longest first); '?' when unknown.
+    Upbit/Bithumb markets are QUOTE-BASE, so their quote is the part before the dash."""
+    s = symbol.upper()
+    if "-" in s:
+        return s.split("-", 1)[0]
+    return next((q for q in sorted(_QUOTES, key=len, reverse=True) if s.endswith(q) and len(s) > len(q)), "?")
+
+
 class CryptoError(RuntimeError):
     """A provider was asked and could not answer; the message says why."""
 
@@ -162,7 +174,7 @@
         return Candles(symbol=market, dates=tuple(ds), close=g("trade_price"), open=g("opening_price"),
                        high=g("high_price"), low=g("low_price"), volume=g("candle_acc_trade_volume"),
                        quote_volume=g("candle_acc_trade_price"), source=self.source,
-                       note="Upbit daily candle, UTC date, KRW quote")
+                       note=f"Upbit daily candle, UTC date, {_quote_ccy(market)} quote")
 
     def ticker(self, markets: list[str] | str = "KRW-BTC") -> list[dict]:
         m = ",".join(markets) if isinstance(markets, list) else markets
@@ -223,7 +235,7 @@
         col = lambda i: tuple(float(rows[t][i]) for t in ts)                 # noqa: E731
         return Candles(symbol=symbol, dates=tuple(fmt(t) for t in ts), close=col(4), open=col(1),
                        high=col(2), low=col(3), volume=col(5), quote_volume=col(7), source=self.source,
-                       note=f"Binance {market} {interval} kline, UTC, {symbol[-4:]} quote")
+                       note=f"Binance {market} {interval} kline, UTC, {_quote_ccy(symbol)} quote")
 
     def funding(self, symbol: str = "BTCUSDT", *, days: int = 730) -> FundingSeries:
         """8-hourly funding history, paged by explicit windows (the endpoint
--- a/data/kis_markets.py
+++ b/data/kis_markets.py
@@ -59,8 +59,11 @@
     "Y0112": ("CD 91d", 0.25), "Y0114": ("Call 1d", 1 / 365), "Y0102": ("Corp AA- 3y", 3.0),
 }
 US_YIELD_CODES = {"Y0202": ("UST 10y", 10.0), "Y0201": ("UST 30y", 30.0), "Y0204": ("Fed funds", 1 / 365)}
-KRW_CURVE_TENORS = (("Y0112", 0.25), ("Y0104", 1.0), ("Y0101", 3.0), ("Y0105", 5.0),
-                    ("Y0106", 10.0), ("Y0116", 20.0), ("Y0117", 30.0))    # CD 91d + KTB par grid
+# KTB par grid only. CD 91d (Y0112) is a bank certificate-of-deposit rate (the KRW IRS floating index), not a
+# sovereign yield, so it is not a node of the government curve; read it on its own from KRW_YIELD_CODES. A 3-month
+# sovereign point, when wanted, is MSB 91d (통안증권) from ECOS, not CD.
+KRW_CURVE_TENORS = (("Y0104", 1.0), ("Y0101", 3.0), ("Y0105", 5.0),
+                    ("Y0106", 10.0), ("Y0116", 20.0), ("Y0117", 30.0))    # KTB par grid
 FX_KRW_CODE = "FX@KRW"          # 원/달러 (KMB) daily fixing, market X
 INDEX_CODES = {"SPX": "S&P 500", ".DJI": "Dow Jones"}
 
@@ -567,12 +570,20 @@
                 "prev_close": _f(o.get("bond_prdy_clpr")), "volume": _f(o.get("acml_vol")),
                 "as_of": date.today().isoformat()}
 
-    def bond_daily(self, isin: str) -> Bars:
-        """Daily prices per 10,000 face; one call returned 69 sessions (about 14
-        months). No date parameters; KIS decides the window."""
-        p = self._get("/uapi/domestic-bond/v1/quotations/inquire-daily-price", "FHKBJ773404C0",
-                      {"FID_COND_MRKT_DIV_CODE": MKT_BOND, "FID_INPUT_ISCD": isin})
-        return _bars(isin, p.get("output") or [], {"date": "stck_bsop_date", "close": "bond_prpr",
+    def bond_daily(self, isin: str, *, max_pages: int = 10) -> Bars:
+        """Daily prices per 10,000 face. No date parameters: KIS decides the
+        window and flags further pages in the tr_cont header, which this follows
+        like the official sample (domestic_bond/inquire_daily_price, depth 10)."""
+        path = "/uapi/domestic-bond/v1/quotations/inquire-daily-price"
+        params = {"FID_COND_MRKT_DIV_CODE": MKT_BOND, "FID_INPUT_ISCD": isin}
+        rows: list[dict] = []
+        p = self._get(path, "FHKBJ773404C0", params)
+        for page in range(max_pages):
+            rows += p.get("output") or []
+            if page + 1 == max_pages or not self._more_pages():
+                break
+            p = self._get(path, "FHKBJ773404C0", params, tr_cont="N")
+        return _bars(isin, rows, {"date": "stck_bsop_date", "close": "bond_prpr",
                                                     "open": "bond_oprc", "high": "bond_hgpr",
                                                     "low": "bond_lwpr", "volume": "acml_vol"},
                      note="price per 10,000 KRW face; thin trading shows flat days")
@@ -740,31 +751,36 @@
 _COM_RE = re.compile(r"^(\d\d)([A-Z0-9]{6})\s+(KR[A-Z0-9]{10})(.+?)\s+(F|SP)\s+(\S+)\s+(\d{9})")
 
 
-def commodity_futures_contracts(keyword: str = "3년국채") -> list[dict]:
+def commodity_futures_contracts(keyword: str = "3년국채", *, exact: tuple[str, ...] = ()) -> list[dict]:
     """KTB / KOFR / currency / gold futures from fo_com_code (fixed width):
-    [{code, isin, name, expiry_yyyymm, order}], order 1 = front month."""
+    [{code, isin, name, expiry_yyyymm, order}], order 1 = front month. `exact`
+    keeps only rows whose name equals one of the given names (no substring)."""
     out = []
     for line in load_master("fo_com_code"):
         m = _COM_RE.match(line)
         if not m or m.group(5) != "F":
             continue
         name = m.group(4).strip()
-        if keyword and keyword not in name:
+        if exact and name not in exact:
+            continue
+        if not exact and keyword and keyword not in name:
             continue
         out.append({"code": m.group(2), "isin": m.group(3), "name": name,
                     "expiry_yyyymm": m.group(6), "order": int(m.group(7)[-1] or 9)})
     return sorted(out, key=lambda r: (r["order"], r["expiry_yyyymm"]))
 
 
-_FRONT_KEYWORDS = {"KTB3": "3년국채", "KTB5": "5년국채", "KTB10": "10년국채", "KTB30": "30년국채",
-                   "USD": "미국달러", "KOFR": "KOFR", "GOLD": "금"}
+# Whole names, never substrings: "금" is inside "3개월무위험금리". The KOFR name follows the KIS master header
+# (RFR : 3개월무위험금리); both spellings stay until one captured master line settles it.
+_FRONT_NAMES = {"KTB3": ("3년국채",), "KTB5": ("5년국채",), "KTB10": ("10년국채",), "KTB30": ("30년국채",),
+                "USD": ("미국달러",), "KOFR": ("3개월무위험금리", "KOFR"), "GOLD": ("금",)}
 
 
 def front_contract(product: str = "KOSPI200") -> Optional[str]:
     """Front-month short code for a product family, from the live master."""
     try:
-        if product in _FRONT_KEYWORDS:
-            rows = commodity_futures_contracts(_FRONT_KEYWORDS[product])
+        if product in _FRONT_NAMES:
+            rows = commodity_futures_contracts(exact=_FRONT_NAMES[product])
         else:
             rows = index_futures_contracts(product)
     except Exception:
```

SF-06 제안 테스트(설명형, 새 파일 `tests/vendor_cache_licence.py`):

```python
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "docs" / "asset_expansion" / "cache"

def test_r1_vendor_cache_has_licence_rows():
    rows = {r["file"]: r for r in csv.DictReader(open(CACHE / "MANIFEST.csv", encoding="utf-8"))}
    data = [p.name for p in CACHE.iterdir() if p.is_file() and p.name != "MANIFEST.csv"]
    missing = [n for n in data if n not in rows or not rows[n]["licence"].strip()]
    assert not missing, missing
    assert all(rows[n]["redistribution"] in ("yes", "no", "unknown") for n in data)
```

SF-04는 설명형 수정안만 낸다(5.2). 마스터 소속 판정은 `_MASTERS`에 `fo_stk_code_mts`를 더해야 하므로 마스터 형식을 캡처한 픽스처와 함께 작업한다.

## 부록 B. 웹 출처 (2차 자료 포함)

- KIS 공식 저장소: https://github.com/koreainvestment/open-trading-api (커밋 cd63caee, 로컬 클론으로 확인)
- 코인원·한투 앱 시세 협업(검색 요약): https://news.mtn.co.kr/news-detail/2026090916174491257 , https://www.fnnews.com/news/202609090914515687 , https://news.mtn.co.kr/news-detail/2026072709383951611
- KIS 제휴 안내(검색 요약): https://apiportal.koreainvestment.com/provider , https://apiportal.koreainvestment.com/provider-apply
- ECOS 항목 코드(공개 저장소 2차): github.com/kgcrom/cluefin `packages/cluefin-openapi/src/cluefin_openapi/ecos/_constants.py`, github.com/seokhoonj/pyecos `tools/curation_design.tsv`, github.com/SignalInvest/bond-insight `data/raw/ecos/market_rate_items.csv`, github.com/openbq-org/OpenBB `openbb_cftc/utils/fixings.py`(KOFR 010901000), 731Y003: github.com/eddmpython/dartlab, github.com/kpubdata-lab/kpubdata(매매기준율로 표기, 충돌)
- KRX Open API 채권 엔드포인트(2차): github.com/kyo504/krx-cli `src/cli/commands/bond.ts`, github.com/wodnjsv/day-trading-agent `KRX_openapi/Spec (15).md`
- 금융위원회 채권시세 API(2차): github.com/kojaeseong/clisa_bond `scripts/daily.py`, github.com/hk99915-bot/market-screener `screener/fsc_bond.py`; 공공누리 2유형 사례(검색 요약): https://www.data.go.kr/data/15043462/openapi.do
- FRED 약관(검색 요약): https://fred.stlouisfed.org/legal/terms/ , https://fred.stlouisfed.org/docs/api/fred/v2/
- US Treasury XML(검색 요약): https://home.treasury.gov/treasury-daily-interest-rate-xml-feed
- Binance Vision 약관(존재만 확인): https://data.binance.vision/Binance_Vision-Terms_of_Use.pdf
- CoinGecko Demo 한도(검색 요약): https://docs.coingecko.com/changelog.md
- 원화 IRS 참고치(검색 요약): https://cbonds.hk/indexes/219685/

<!-- verifier-section -->

## 독립 검증 결과

- 검증일: 2026-10-27. 대상 HEAD `4665e6e`. 추적 파일은 고치지 않았다.
- 방법: 인용된 코드를 직접 읽었다. 재현은 `git archive HEAD`로 만든 스크래치 사본 두 벌(`head`, 제안 패치를 적용한 `patched`)에서 다시 짰다. 네트워크·`.env`·키는 막았다(`_guard.py`). 금지 파일 4개는 열지 않았다. SF-06은 `git ls-files`의 파일 이름만 셌다.
- 스크립트 폴더: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/`. 출력은 그 위 폴더의 `v_*_output.txt`.

### 1. 발견사항별 판정

| id | 유지 여부 | 정정 판정 | 정정 심각도 | 근거 |
|---|---|---|---|---|
| SF-01 | 유지 | 사실(크기는 추정) | P2 → **P3** | `data/kis_markets.py:62` 첫 노드가 `("Y0112", 0.25)`이고 `:59` 라벨이 "CD 91d"다. 스텁 재현에서 HEAD는 `Y0112`를 받아 `tenors[0]=0.25`, 패치본은 `tenors[0]=1.0`이고 note에 "no CD 91d node"다(`v_sf01_output.txt`). 다만 `krw_curve_panel`은 저장소 어디에서도 호출되지 않는다(grep: `core/`, `ui/`, `docs/*.py` 모두 0건). 지금 화면에 나오는 숫자가 없으므로 P3다. FC-03 연결(`functional_completeness.md:147`의 `tenors[0] == 0.25` 테스트) 전에 고치지 않으면 P2가 된다 |
| SF-06 | 유지 | 사실(배포 경로는 추정) | P2 유지 | 추적 파일 46개(yf 40, binance 3, fred 2, upbit 1). 전부 `.csv`. 폴더에 MANIFEST·licence 없음. `docs/asset_expansion/manifest.json`은 스터디 결과 목록이다(`run, seed, results_md5, ...`). 단, `pyproject.toml`의 setuptools 패키지는 `core*, data*, ui*`만 담는다. 배포물에 들어가는 것은 저장소 공유나 `[tool.flet] path="."` 빌드일 때다(추정). 수정안 보완: MANIFEST의 md5 열을 금지 파일 4개(다른 프로젝트의 미공개 구간)에 요구하면 그 보호 규칙과 충돌한다. 4개는 폴더 밖으로 옮기거나 md5를 비우고 `redistribution=no`로 둔다. 제안 테스트는 `unknown`도 통과시키므로 배포 차단은 패키징 제외 규칙(예: flet 빌드 제외 목록) 검사가 따로 필요하다 |
| SF-07 | 유지 | 사실(무료 공식 API 부재는 미검증) | P2 → **P3** | `core/ficc/data.py:64` `SOURCES`, `:621-632` KRW는 OECD 월간만. `config.py:282-290` FRED·Yahoo 두 행. `ui/rates_page.py:394, 440` vol은 입력값. 그러나 README `:104`는 선도를 "CIP … from the two funding rates", 크로스커런시 베이시스를 "if a market forward is supplied"로 이미 밝힌다. vol도 사용자가 넣는 값이다. 시장값으로 위장된 숫자가 없으므로 결함이 아닌 공급 공백이다. 또 "KIS FICC 기능이 Settings에 없다"는 부분은 과장이다. `ui/settings_page.py:220-224` KIS 안내문이 "KRW benchmark yields and exchange-traded bonds"를 적는다(FICC 목록에만 없다) |
| SF-02 | 유지 | 사실 → **추정** | P3 유지 | 코드가 `tr_cont`를 무시하는 것은 사실이다(`data/kis_markets.py:570-578`, 가짜 3쪽에서 HEAD 30행·호출 `['']`, 패치본 90행·`['', 'N', 'N']`; `v_sf02_output.txt`). 그러나 근거로 든 공식 샘플의 `if tr_cont == "M"` 재귀는 생성형 상용구다. 334개 중 180개 샘플에 있고, 단건 응답인 `domestic_bond/inquire_price.py:100`, `search_bond_info.py:101`에도 있다. 이 엔드포인트가 실제로 여러 쪽을 주는지, 그래서 이력이 잘리는지는 증거가 없다. 3장 #6의 "오류(부분)"도 "미검증"으로 고친다. 수정안 보완: 같은 쪽이 반복되면 멈추는 가드(`option_board`처럼 새 날짜가 없으면 중단)를 넣는다. 지금 패치는 서버가 계속 "M"을 주면 같은 요청을 10번 보낸다 |
| SF-03 | 유지 | 추정 | P3 유지 | `:752` 부분 문자열 비교, `:759-760` `"GOLD": "금"`, `"KOFR": "KOFR"`. 저장소 픽스처 형식(`tests/expansion_acceptance.py:142`)으로 합성 마스터를 만들어 확인했다(`v_sf03_output.txt`). KOFR 종목명이 "3개월무위험금리"이고 금과 만기가 같으면 HEAD는 GOLD=A69612, KOFR=None. 금 만기가 더 이르면 GOLD는 맞고 KOFR만 None. 종목명이 "KOFR"이면 둘 다 맞다. 연구 노트 `kis_api_audit.md:160`은 내려받은 마스터에 "`A69` 3개월무위험금리"가 있다고 적어 KOFR=None 쪽을 뒷받침한다. 실제 종목명 문자열은 저장소에 없다. 호출처는 `KTB3`(`:633`)뿐이다. 패치는 4개 경우 모두 맞다. 단, 완전 일치는 GOLD·USD·KTB5/10/30의 실제 이름을 확인하지 않았으므로 실패 방식이 "다른 계약"에서 "None"으로 바뀐다(더 안전한 쪽) |
| SF-04 | 유지 | 추정 | P3 유지 | `:248-253` `01/05/06/07`만 F. A04612·A08612·A09612·A11610 → CF(`v_sf04_sf05_output.txt`). 공식 샘플은 `F: 지수선물`, `JF: 주식선물`만 문서화하고 `CF`는 없다(`inquire_asking_price.py:25`). 서버 반응은 미검증. 덧붙임: `:251` `prod = c[1:3] if c[:1].isalpha() else c[1:3]`는 두 갈래가 같다. 연구 노트의 마스터 상품 목록(`kis_api_audit.md:159`)에 `07`은 없다. 수정 시 `tests/expansion_acceptance.py:146`(A05610→F, A67612→CF)을 지켜야 한다 |
| SF-05 | 유지 | 사실 | P3 유지 | `data/crypto/crypto_client.py:165` "KRW quote" 고정, `:226` `symbol[-4:]`. USDT-BTC·BTC-ETH → "KRW quote", ETHBTC → "HBTC", BTCFDUSD → "DUSD", BTCTRY → "CTRY". 패치본은 USDT/BTC/BTC/FDUSD/TRY로 맞다. note는 Quant Lab 칩으로 보인다(`ui/quant_lab_page.py:326`). 값은 영향 없음 |

공통 확인:
- 제안 패치는 `git apply --check`를 통과했다. 패치 전후 모두 관련 테스트 7개(`test_kis_markets_paging_and_shapes`, `test_master_parsers`, `test_crypto_client_refusals_and_router`, T-RO-02, T-RO-01, `test_08_no_broker_order_path`, `test_09_no_account_credentials_requested`)와 self-check 3개가 PASS다(`v_tests_output.txt`). 클라우드 기준선 `baseline2_results.json`에서도 같은 테스트가 PASS다.
- 각 제안 회귀 테스트는 HEAD에서 실패하고 패치본에서 통과한다: SF-01, SF-02, SF-03, SF-05 확인. SF-04, SF-06, SF-07은 새 코드가 필요한 설명형이다. 단, SF-03·SF-04의 기대값(A69612=KOFR, A04612→F, A11610→JF)은 합성 가정이다.
- 보고서의 다른 주장 확인: 공식 카탈로그 334행, 범주 8개, "가상자산·코인·BTC·IRS·스왑·NDF" 0건(사실). `avg-unit` 샘플 필드 `kis_unpr`·`kbp_unpr`·`nice_evlu_unpr`·`fnp_unpr`(사실). 허용목록 25개이고 `avg-unit` 없음(사실). `comp-interest`의 `FID_DIV_CLS_CODE`를 코드는 `""`로, 샘플은 필수(예 '1')로 둔다(사실, 영향은 미검증).
- 검토 중 찾은 Derivatives의 "CD 91d 없음 → 하드코딩 3%를 `input`으로 표시"는 이미 D03-05로 보고됐다. 다시 세지 않는다(재현: `v_m01_deriv_rate.py`, 출력 `rate=0.0300 rate_source='input'`).

### 2. 놓친 발견사항

#### SFV-01 · P2 · 사실 — Crypto 화면의 실데이터 실행이 Binance 선물 호스트(fapi) 하나에 묶여 있다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `ui/crypto_page.py:45-57` `_live`(펀딩 `:51`, `premium_index` `:56`, `open_interest_hist` `:57`), `analyze` `:60-61`, 표시 `:168`. `data/crypto/crypto_client.py:53` `BINANCE_FAPI` 단일 호스트, `:228-270`. 대조: 현물은 `:50` 두 호스트이고, 모듈 문서 `:9-12`는 "Korean network blocks … announced for the main domains"라 적는다. `provider_status` `:337`, `probe` `:350`도 차단 가능성을 따로 점검한다 |
| 재현 단계 | `VROOT=…/verify_suppliers_ficc_btc/head python3 -B …/scripts/v_m02_fapi_spof.py`. 가짜 전송: Upbit·Binance 현물은 응답, `fapi.binance.com`만 `CryptoError`(실제 `_get`이 네트워크 오류에서 내는 형태). FX는 스텁 |
| 기대 결과 | 선물 다리가 막혀도 현물·김치 프리미엄·추세·GARCH는 LIVE로 계산된다. 펀딩·프리미엄·OI 칸만 "unavailable"로 표시된다 |
| 실제 결과 | 모든 호스트 응답: `OK source=LIVE kimchi_last=2.00% n=730`. fapi 차단: `CryptoError: Binance funding BTCUSDT: ConnectionError`로 `analyze` 전체가 실패한다. 화면은 오류 안내 하나만 보인다 |
| 영향 | 국내망에서 fapi가 막히면 BTC 화면 전체를 못 쓴다. 현물과 FX가 정상이어도 김치 프리미엄이 사라진다. 조사자 7장의 "크립토 파생 = Binance fapi(현행)" 권고가 이 단일 실패점을 다루지 않는다. 실제 차단 여부는 미검증이다(코드 자신이 위험을 적는다) |
| 수정안 | 스크래치 사본에서 확인한 diff(`m02_proposed.diff`):<br>`_live`: `from data.crypto.crypto_client import BinancePublic, CryptoError, UpbitPublic`; `try: fund = bn.funding(...).daily(); prem, oi, deriv_error = bn.premium_index("BTCUSDT"), bn.open_interest_hist("BTCUSDT"), ""` / `except CryptoError as exc: fund, prem, oi, deriv_error = {}, None, [], f"Binance USD-M futures unavailable ({exc})"`; 반환 dict에 `"premium_index": prem, "oi": oi, "deriv_error": deriv_error`.<br>`analyze` `:78`: `out["deriv_error"] = d.get("deriv_error", "")`. 기존 `funding_carry`는 빈 입력에서 `ValueError`를 내므로 `:64-67`이 `funding=None`으로 받는다(확인).<br>표시 `:168`: `stat("Perp premium", f"{a['premium_index']['premium_pct']:+.3f}%" if a["premium_index"] else "unavailable")`와 `deriv_error` 안내문. 0으로 채우지 않는다. 선택: 펀딩 이력은 `data.binance.vision`의 월별 fundingRate zip(무키)으로 대체 |
| 회귀 테스트 | `test_crypto_live_survives_fapi_block`: 가짜 `_get`이 fapi URL에서 `CryptoError` → `a = analyze(source="live")`; `a["source"] == "LIVE"`, `a["kimchi"].n > 0`, `a["funding"] is None`, `"unavailable" in a["deriv_error"]`. HEAD FAIL, 수정 사본 PASS(`v_m02_output.txt`) |

#### SFV-02 · P3 · 추정 — KIS 점검과 대체값에 만기가 있는 계약 코드가 박혀 있다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `data/kis_markets.py:631` `"index_futures": futures_quote("A01612")`(마스터를 보지 않음), `:633` `front_contract("KTB3") or "A65612"`, `:637` `ovf_contract_detail(["VXV26"])`. `ui/derivatives_page.py:65` `front_contract("KOSPI200") or "A01612"`. `front_contract` `:763-772`는 모든 예외를 삼키고 None을 낸다 |
| 재현 단계 | `VROOT=…/head python3 -B …/scripts/v_m01_hardcoded_contracts.py`. 거래소 규칙으로 최종거래일을 계산하고, 마스터 내려받기 실패를 흉내 낸다 |
| 기대 결과 | 점검과 대체 경로가 마스터나 날짜 규칙으로 근월물을 고른다. 모르면 "마스터 없음"이라고 말한다 |
| 실제 결과 | VXV26(CBOE VIX 2026-10)은 2026-10-21에 이미 만기다(감사일 6일 전). A01612(KOSPI200 2026-12)는 2026-12-10, A65612(KTB3 2026-12)는 2026-12-15에 만기다. 마스터 실패 시 `front_contract`는 None이고 호출부는 이 고정 코드를 쓴다 |
| 영향 | Settings의 KIS 상태가 만기 계약 조회 결과로 나온다. `overseas_futures`는 `len(output2)`로 판정하므로 빈 행이면 거짓 성공, 행이 없으면 거짓 실패다. 12-10 이후 마스터 장애가 나면 Derivatives가 만기 계약을 조회한다. KIS가 만기 코드에 빈 응답을 주면 오류로 끝난다. 마지막 체결값을 주면 과거 값이 현재처럼 쓰인다. 어느 쪽인지 미검증이라 추정이다 |
| 수정안 | `data/kis_markets.py`: `_front_or_raise(product)` 추가(`code = front_contract(product)`; 없으면 `KISError(f"{product}: front month unknown (KIS master unavailable); no dated fallback is used")`). probe를 `futures_quote(_front_or_raise("KOSPI200"))`, `futures_quote(_front_or_raise("KTB3"))`, `ovf_contract_detail([_vx_front_code(date.today())])`로 바꾼다. `_vx_front_code`: 다음 달 셋째 금요일 30일 전 수요일이 지나면 다음 월물(`"FGHJKMNQUVXZ"`). 확인: 2026-09-25 → VXV26, 2026-10-27 → VXX26, 2026-12-20 → VXF27. `ui/derivatives_page.py:65`: `code = front_contract("KOSPI200")`; 없으면 `FICCError("KIS master unavailable: the front KOSPI200 future is unknown")` |
| 회귀 테스트 | `test_kis_no_dated_contract_literals`: `data/kis_markets.py`의 `probe`와 `ui/derivatives_page.py` 원문에 `r'"A\d{5}"'`, `r'"VX[FGHJKMNQUVXZ]\d\d"'` 문자열이 없다. `load_master`를 실패 스텁으로 바꾸면 `snapshot(source="kis")`가 "master unavailable"을 담은 `FICCError`를 낸다. `_vx_front_code(date(2026,10,27)) == "VXX26"` |

### 3. 재현 파일

- 가드: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/_guard.py`
- SF-01: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_sf01.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_sf01_output.txt`
- SF-02: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_sf02.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_sf02_output.txt`
- SF-03: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_sf03.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_sf03_output.txt`
- SF-04·SF-05: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_sf04_sf05.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_sf04_sf05_output.txt`
- 기존 테스트·self-check: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_tests.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_tests_output.txt`
- SFV-01: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_m02_fapi_spof.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_m02_output.txt`, diff `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/m02_proposed.diff`(표시 줄 `:168` 변경은 위 표에 따로 적음)
- SFV-02: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_m01_hardcoded_contracts.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_m01_hardcoded_output.txt`
- D03-05 중복 확인: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/scripts/v_m01_deriv_rate.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_suppliers_ficc_btc/v_m01_output.txt`
