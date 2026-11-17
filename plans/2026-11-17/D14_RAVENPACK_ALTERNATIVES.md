# D14 RavenPack 대안으로 짜는 데이터 소스 계획 (2026-11-17)

- 대상: 소유자. 데이터소스 세션(DIDM 포함)이 이 문서로 시작할 수 있게 썼습니다.
- 바탕: 소유자 답 "Ravenpack의 대안책 3단계 (엑셀 파일 참고)의 자료들로 구성할 예정." (`owner_answer_1117.txt` 5번)
- 1차 자료: 소유자 엑셀 `ravenpack_alt.xlsx`의 글 사본 `OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt` (모든 칸과 칸 메모). 이 문서는 엑셀을 고치지 않습니다. 공개 페이지와 다른 곳은 둘 다 적습니다.
- 표시: **미검증** = 원문을 직접 확인하지 못했거나 추정한 값.
- **법률 자문이 아닙니다.** 약관·법규 내용은 확인할 항목을 적은 것입니다. 상업 이용 전에는 변호사와 각 공급사 약관 원문으로 확인해야 합니다.

---

## 0. 결론

| 항목 | 판단 |
|---|---|
| 판정 | **조건부 GO.** 엑셀의 대안 9개만으로 DIDM 0~3단계를 시작할 수 있습니다. |
| "3단계"의 뜻 | DIDM 연구의 **Stage 3 (예측 가치 검증)** 로 읽었습니다. "3단계를 통과할 때까지는 RavenPack 대신 엑셀의 대안 자료로 구성한다"는 뜻입니다 (1절). Notion DIDM 원문과 맞습니다. 소유자 확인 한 줄이 필요합니다. |
| 대안이 채우는 것 | 뉴스 수집, 감성, 티커 태깅, 사건 분류, 실시간, 미국 거시 숫자 (금리 확률·통계·수정 이력·컨센서스·사건 확률), 암호화폐 감성 |
| 직접 만들어야 하는 것 | 신규성 점수, 관련성 점수(일부), 사건 영향 분석 → 자체 NLP와 "시장 반응 확인" 단계 (5·6절) |
| 못 채우는 것 | 2000~2014년 뉴스 점수 이력. 다만 DIDM 사전등록 구간이 2015년부터라 연구에는 지장이 없습니다. |
| 비용 | 최소 월 약 $4~11 (데이터 $0 + LLM). 권장 월 약 $112~127 (CME·Alpha Vantage·Tiingo 유료 + LLM). Trading Economics는 견적이라 뺐습니다. (7절) |
| 바뀌는 계획 | 초안의 D14-A (Bigdata.com Pro 2주 시험, `BIGDATA_API_KEY`, DS-2)는 빠집니다. RavenPack 견적(DS-3)은 3단계 통과 뒤로 미룹니다. (10절) |
| 새로 찾은 위험 | Polymarket이 2026-08-18부터 한국에서 접속 차단 대상입니다 (방송통신심의위원회). 한국에서 API를 쓸 수 있는지, 써도 되는지는 **미검증**입니다. (4·8절) |

---

## 1. "3단계"는 무엇인가

### 1.1 Notion에서 찾은 근거 (원문 인용)

DIDM 페이지 (`02e5c916fe0c821bb15701f648e9db87`, 2026-11-11 수정본, 2026-11-17 읽음):

- TL;DR: "The zero-budget stack is sufficient for a credible first verification (GDELT, SEC EDGAR, DART, FRED/ALFRED, ECOS, PRisk, EPU, GPR, Polymarket history, Upbit/Binance public data, chronologically consistent open models such as ChronoBERT/ChronoGPT), with a 16-week plan for two researchers; **commercial feeds (RavenPack, LSEG MarketPsych, Bloomberg) are an upgrade only after Stage 3 passes.**"
- 8.1 표의 RavenPack 줄: "RavenPack / LSEG MarketPsych / Bloomberg EDF / Dow Jones | Licensed news analytics | ... | Quote required | **Upgrade after Stage 3**"
- 8.2 제목: "**Zero/low-budget academic stack (sufficient for Stages 0–3)**". 업그레이드 순서: "(1) one licensed wire with true wire timestamps once Stage 3 passes; (2) vendor sentiment (RavenPack or MarketPsych) as a baseline to beat; (3) shared-analyst-coverage data for W."
- 10.6: "**licensed data \$0 until Stage 3 passes.**"
- 6.2 단계표: Stage 0 시뮬레이션, 1 측정 타당성 (정답 1,000~1,500건), 2 사건연구·LP (2015~2024), **3 예측 가치 (2019~2026 표본 밖)**, 4 전략 가치 (QUANTGEN 관문), 5 모의 운영.

DIDM_Research_Report 페이지 (`2045c916fe0c82ca8efe8157c0c70bd8`)도 같은 문장입니다 ("Commercial feeds (RavenPack, LSEG MarketPsych, Bloomberg) are an upgrade only after Stage 3 passes.").

초안도 같은 말을 씁니다: 소유자 보고서 D14 줄 "RavenPack 계약은 DIDM 3단계 뒤", 부록 D "Bigdata.com Pro는 DIDM 계획의 '3단계 전 유료 데이터 $0' 규칙과 월 $40만큼 어긋납니다."

### 1.2 해석

- 소유자 문장은 "(DIDM) 3단계까지는 RavenPack 대신 엑셀의 대안 자료로 구성한다"로 읽힙니다. 1.1의 Notion 규칙과 같고, D14-A(Bigdata.com 시험)를 고르지 않았다는 뜻도 됩니다.
- 다른 해석 "1단계 RavenPack 기관용 → 2단계 Bigdata.com → 3단계 무료·저가 대안" 같은 단계 사다리는 **찾지 못했습니다** (Notion 검색 "RavenPack 대안책 3단계", Types of Info 페이지, DIDM 두 페이지, 초안 전체). 엑셀에도 "단계"라는 글자가 없습니다 (openpyxl로 원본 확인: 시트 1개 `Sheet1`, 숨은 행·열 없음). 엑셀의 묶음은 "공통 / RavenPack 쪽만 / 대안 쪽만 / 확인 필요" 넷이고, 행은 "RAVENPACK 등"과 "대안책" 둘입니다.
- 어느 해석이든 지금 할 일은 같습니다: **엑셀 대안으로 만들고, RavenPack·Bigdata.com은 3단계 통과 뒤 "넘어야 할 기준선"으로 다시 봅니다.**
- Types of Info 페이지(`41b5c916fe0c80ddb4e2ce2e1d376003`, 2026-11-17 13:05 KST 수정)는 제목이 "Types of Info & Ravenpack's Role"이지만 본문에는 DIDM의 역할만 있고 RavenPack 단계 계획은 없습니다.

### 1.3 찾지 못한 것

- 엑셀 메모가 말하는 "계획서 3.2 (Impact Analytics)", "계획서 3.3 (미국 거시 이벤트 감시)", "계획서 4.1 (시장 반응 확인 단계)"의 **문서를 찾지 못했습니다** (Notion 검색, Drive 검색, `origin/main` docs 검색). 내용이 같은 곳은 Notion "NEW MACRO MODEL" (AMIE 명세, `4135c916fe0c80dbb7d5f10a6e09077b`)입니다:
  - 3절 ⑦ "시장 확인: 뉴스 전후 가격·거래량·변동성 확인; 이미 가격 반영됐는지 점검."
  - 8절 P1-1 "Asset impact + confirmation | 자산 매핑과 시장 반응 확인, 무관한 자산 신호 억제"
  - 3절 ④ "예상 대비 차이: 발표치와 사전 컨센서스 비교. 컨센서스가 없으면 surprise를 미상으로 표시."
- 아래에서 "계획서 4.1 시장 반응 확인"은 이 ⑦·P1-1과 DIDM Stage 2 (사건별 초과수익 CAR)를 뜻하는 것으로 씁니다.

---

## 2. 소유자 엑셀 요약 (대안 행만)

엑셀 범례: O 제공, X 제공 안 함, ? 공개 자료로 확인 못함. "대안책" 행은 9개 대안 중 하나라도 제공하면 O.

| 정보 유형 (엑셀 열) | RavenPack 등 | 대안책 | 엑셀 메모 (대안 쪽 출처) |
|---|---|---|---|
| 뉴스 기사 수집 (F) | O | O | GDELT, Tiingo, Alpha Vantage, Cryptopanic |
| 뉴스 감성 점수 (G) | O | O | Alpha Vantage·Cryptopanic 감성, GDELT 논조(tone). Tiingo는 감성 필드 없음 |
| 엔티티·티커 태깅 (H) | O | O | Tiingo·Alpha Vantage 주식·FX·암호화폐 티커, GDELT 인물·조직·장소 |
| 사건·토픽 분류 (I) | O | O | GDELT 이벤트, Alpha Vantage 토픽, 자체 NLP |
| 분 단위 이내 실시간 (J) | O | O | Tiingo·Polymarket 실시간, FedWatch 장중판 60초, GDELT 15분 |
| 미국 거시 이벤트 감시 (K) | O | O | CME·FRED·Polymarket·Trad. Econ이 숫자로 제공 |
| Python API (L) | O | O | 9개 모두 REST API |
| 무료 플랜 (M) | O | O | FRED·GDELT·Polymarket 무료, Alpha Vantage 하루 25건, Tiingo·Cryptopanic 무료 플랜 |
| 신규성 점수 (N) | O | **X** | 제공하는 소스 없음. 자체 NLP로 직접 구현 |
| 자산별 관련성 점수 (O) | O | **?** | Alpha Vantage 응답의 관련성 필드를 공개 문서에서 확인 못함 |
| 2000년부터 뉴스 점수 이력 (P) | O | **X** | GDELT 논조 2013년 4월부터, Tiingo 유료 플랜 과거 뉴스 3개월 |
| FOMC 시장 내재 금리 확률 (Q) | X | O | CME FedWatch, 2015년부터 |
| 공식 경제 통계 (R) | X | O | FRED, Alpha Vantage 거시 지표 |
| 발표 시점별 수정 이력 (S) | X | O | ALFRED |
| 발표치·컨센서스 (T) | X | O | Trading Economics |
| 예정 사건 결과 확률 (U) | X | O | Polymarket (Kalshi도 같은 유형) |
| 원문 저장·학습 허용 (V) | X | O | GDELT는 원본 파일 공개. 다른 소스는 약관 확인 필요 |
| 자산 영향 분석 Impact Analytics (W) | ? | **X** | 제공 소스 없음. 계획서 4.1 시장 반응 확인 단계로 자체 구현 |
| 암호화폐 뉴스 감성 (X) | ? | O | Cryptopanic, Alpha Vantage (CRYPTO:BTC 등) |

---

## 3. 정보 유형별 담당 소스 (요구 1)

비용·속도·기록 깊이는 **엑셀 메모가 1차 출처**입니다. 공개 페이지와 다르면 4절에 둘 다 적었습니다.

| 정보 유형 | 1순위 대안 | 보조 | 비용 (엑셀) | 갱신 속도 (엑셀) | 기록 깊이 (엑셀) | 엑셀 메모 |
|---|---|---|---|---|---|---|
| 뉴스 기사 수집 | GDELT (세계 뉴스 URL·메타데이터) | Tiingo (티커 붙은 뉴스), Alpha Vantage, Cryptopanic | GDELT 무료, Tiingo 월 $30(개인)·$50(사업자) | GDELT 15분, Tiingo 실시간 | GDELT 이벤트 1979년, GKG 2013년 4월; Tiingo 유료 3개월 | F4, J4, P4, GDELT·Tiingo 행 |
| 뉴스 감성 점수 | Alpha Vantage 뉴스 감성 (종목·암호화폐·외환) | GDELT 논조, Cryptopanic | AV 무료 하루 25건, 유료 월 $49.99부터 | 미검증 | AV 과거 뉴스 깊이 확인 못함 (엑셀) | G4, Alpha Vantage 행 |
| 엔티티·티커 태깅 | Tiingo (주식 65,000·FX 75·암호화폐 4,100+ 티커) | Alpha Vantage 티커, GDELT 인물·조직·장소 | Tiingo 월 $30/$50 | 실시간 | 3개월 (유료, 엔터프라이즈 없이) | H4, Tiingo 행 |
| 사건·토픽 분류 | 자체 NLP (DIDM 고정 사건 유형) | GDELT 이벤트 코드, Alpha Vantage 토픽 | LLM 호출료 | 수집 주기 따라감 | 직접 쌓은 만큼 | I4, 자체 NLP 행 |
| 분 단위 실시간 | Tiingo 뉴스, Polymarket 확률 | FedWatch 장중판 60초, GDELT 15분 | Tiingo 유료, Polymarket 무료, FedWatch 장중판 가격 미확인 | 실시간~15분 | 소스별 | J4 |
| FOMC 금리 확률 | CME FedWatch | Polymarket·Kalshi 연준 결정 시장 | 종가판 월 $25 | 장중판 60초 | 2015년부터 | Q4, CME 행 |
| 공식 경제 통계 | FRED | Alpha Vantage 거시 지표 | 무료 | 발표 시각 | 시리즈별 (수십 년) | R4, FRED 행 |
| 발표 시점별 수정 이력 | ALFRED | — | 무료 | 발표 시각 | 시리즈별 | S4 |
| 발표치·컨센서스 | Trading Economics | 없음 (없으면 "예상 대비 차이 미상") | 유료, 가격 공개 페이지에서 확인 못함 | 월 약 1,600건·150개국+ 캘린더 | 미검증 | T4, Trad. Econ 행 |
| 예정 사건 결과 확률 | Polymarket | Kalshi (엑셀 U4) | 무료 | 실시간 | 시장 개설 시점부터 | U4, Polymarket 행 |
| 원문 저장·학습 | GDELT (공개 파일) | 나머지는 약관 확인 | 무료 | — | — | V4 |
| 암호화폐 뉴스 감성 | Cryptopanic | Alpha Vantage CRYPTO:BTC | 무료 초당 5건 (엑셀) | 실시간 | 확인 못함 (엑셀) | X4, Cryptopanic 행 |
| 신규성 점수 | 자체 NLP (6절) | — | LLM 호출료 | — | 직접 쌓은 만큼 | N4 |
| 자산별 관련성 점수 | 자체 NLP + Alpha Vantage 필드 (있으면) | Tiingo 티커 태그 | — | — | — | O4 |
| 사건 영향 분석 | 시장 반응 확인 단계 (6.5절) | — | 기존 시세 데이터 | 시세 주기 | 시세 기록만큼 | W4 |

한국 범위: 엑셀의 9개 대안은 미국·세계·암호화폐 중심입니다. 한국 종목 뉴스·공시는 대안에 없습니다. DIDM 8.2가 쓰는 SEC EDGAR, OpenDART/KIND, ECOS는 엑셀에 없는 **무료 공식 소스**입니다. 저장소에는 이미 `data/krx/opendart_client.py`가 있습니다 (`origin/main` `e01e152`). 이것을 더할지는 소유자 확인이 필요합니다 (11절 질문 3).

---

## 4. 공개 페이지 대조 (2026-11-17 검색)

이 세션에서 `www.alphavantage.co`, `www.tiingo.com`, `cryptopanic.com` 직접 열기는 네트워크 설정에 막혔습니다 (호스트 미허용). 그래서 아래는 **검색 결과 요약 기준**이고 원문 페이지는 직접 읽지 못했습니다. 엑셀 값은 그대로 두었습니다.

| 소스 | 엑셀 값 | 공개 자료 (검색) | 판단 | 출처 |
|---|---|---|---|---|
| Alpha Vantage | 무료 하루 25건, 유료 월 $49.99부터 | 공식 premium 페이지: 무료 표준 한도 하루 25건. 최저 유료 $49.99/월 (분당 75건) — 제3자 사본 기준 | **일치** (원문 직접 확인은 못함) | alphavantage.co/premium, macroption.com, xpay.sh |
| Tiingo | 월 $30(개인)·$50(사업자), 과거 3개월 초과·재배포는 엔터프라이즈 | 공식 가격 페이지는 검색에 안 나옴. 제3자 비교에 "From $30/mo". Tiingo 뉴스 페이지: 1990년대부터의 과거 뉴스는 1년 약정(기관용), 대량 다운로드는 기관 고객만 | 가격 **미검증**. 과거 뉴스 제한의 방향은 엑셀과 같음 | api.tiingo.com/products/news-api, api.tiingo.com/documentation/news, findmymoat.com |
| CME FedWatch | 종가판 월 $25, 장중판 60초, 2015년부터 | CME 제품 페이지: 장중 60초 산출, 2015년부터 확장 이력. 종가판 $25/월은 2026-11-17 재검색에서 CME 공식 페이지로는 확인되지 않고 제3자 비교 사이트에만 있음 (0~1,000건 $25, 1,001~50,000건 $75의 구간제, findmymoat.com) → 가격 **미검증**. **그러나** 장중 API 문서는 "과거 데이터 2025-11-01부터 시작" | **일부 다름.** 2015년 이력은 종가판, 장중판 이력은 2025-11부터로 보임. 장중판 가격은 못 찾음 | cmegroup.com fedwatch-api, CME 개발자 위키 (Intraday API) |
| Cryptopanic | 무료 플랜 초당 5건 | 공식 API 플랜 페이지: 무료 초당 5건, Enterprise 초당 10건, 무료는 출처 표시 필요. **그러나** 제3자 SDK 글: 무료 Developer 플랜이 "중단"으로 표시됨 | **다를 수 있음.** 계정에서 무료 플랜 존재 확인 필요 | cryptopanic.com/developers/api/about, dev.to (cryptopanic-php) |
| GDELT | 65개 언어, 15분, 이벤트 1979년, GKG 2013년 4월 | GDELT 블로그: 2.0은 15분 갱신·65개 언어 실시간 번역 (2015-02 발표). 이벤트 1979년부터. GKG 1.0은 2013-04-01부터 일별, **GKG 2.0은 2015-02부터** | **둘 다 맞음 (판이 다름).** Notion DIDM은 "GKG 2.0 from 2015". 15분 단위 논조는 2015-02부터 | blog.gdeltproject.org (2.0, GKG 2.0), ONS GDELT 부록 |
| Trading Economics | 유료, 가격 공개 페이지에서 확인 못함 | 제3자 (2026-06): Standard $149/월, Professional $299/월 (연간 결제). 다른 리뷰: $199/월부터. 경제 캘린더는 하위 요금제에서 빠져 있다는 제3자 언급 | 엑셀 판단 유지. 제3자 값은 **미검증**. 컨센서스가 Enterprise에만 있을 수 있음 | tradingeconomics.com/analytics/pricing.aspx, businessquant.com, tradingtoolshub.com |
| FRED/ALFRED | 무료 | API 키 무료. 분당 120건 (제3자). ALFRED 빈티지는 같은 API의 실시간 기간 인자로 받음. 일부 시리즈는 상업 이용에 허락 필요 (제3자) | 일치. 상업 조건은 시리즈별 확인 | fred.stlouisfed.org/docs/api/fred/fred_vs_alfred.html |
| Polymarket | 무료·실시간, 가격 이력은 시장 개설부터 | 공식 문서: 일반 한도 10초당 15,000건. 시세 조회는 인증 없이 무료 (제3자). **한국 방송통신심의위원회가 2026-08-18 국내 접속 차단 결정** (도박 관련 정보) | 엑셀에 없는 위험. 한국에서 API 접속·이용 가능 여부 **미검증** | docs.polymarket.com rate-limits, koreatimes.co.kr (2026-08-19), cointelegraph.com |

---

## 5. 엑셀이 X·?로 표시한 빈칸과 채우는 방법 (요구 2)

| 빈칸 | 엑셀 | 채우는 방법 | 남는 한계 |
|---|---|---|---|
| 신규성 점수 | 대안 X | 자체 NLP: 같은 종목·같은 사건 유형·비슷한 문장의 기사를 24시간 창에서 한 묶음으로 봄. 첫 기사 100, 반복·후속은 할인 (6.3절). DIDM 5.3의 origin_cluster_id를 그대로 씀 | 기사 시각이 수집 시각이라 첫 보도 판정이 늦을 수 있음 (GDELT는 "crawl time, not wire time", DIDM 8.1) |
| 자산별 관련성 점수 | 대안 ? | 자체 NLP 질문 "이 종목이 기사의 주제인가" 확률 ×100 (DIDM 9절 질문 1). Alpha Vantage 응답에 종목별 관련성 필드가 있으면 보조 입력으로 씀 (필드 존재 **미검증**: 무료 키로 1회 호출해 확인) | 정답 집합으로 보정 전까지는 순위로만 사용 |
| 2000년부터 뉴스 점수 이력 | 대안 X | 채울 수 없음. 쓸 수 있는 구간: GDELT 이벤트 1979년~ (금융 감성 아님), GKG 논조 2013-04~ (1.0) / 2015-02~ (2.0). DIDM 사전등록 구간이 Stage 2 = 2015~2024, Stage 3 = 2019~2026이라 **연구 계획은 막히지 않음**. 앞으로의 점수는 지금부터 직접 쌓음 | 2000~2014년 위기 구간(2008 등) 검증은 불가 |
| 사건 영향 분석 (Impact Analytics) | 대안 X, RavenPack ? | 계획서의 시장 반응 확인 단계 (NEW MACRO MODEL ⑦·P1-1, DIDM Stage 2 CAR)로 직접 계산 (6.5절) | 사후 확인이라 "예측"이 아님. 같은 날 다른 사건과 섞임 |
| 원문 저장·학습 허용 | 대안 O (GDELT만) | GDELT 파일은 저장·재배포 허용 (출처 표시). 다른 소스는 **파생 특징만 저장** (DIDM 8.3: "store derived features, not raw text, where licences require it") | GDELT가 주는 것은 URL·메타데이터. 기사 본문은 언론사 저작물이라 따로 확인 필요 |
| 암호화폐 감성 (RavenPack ?) | 대안 O | Cryptopanic, Alpha Vantage로 충분 | Cryptopanic 무료 플랜 존재 확인 필요 (4절) |

### 5.1 LLM으로 과거 기사를 점수화할 때의 미래정보(look-ahead) 위험

- 문제: LLM은 학습 기준일 전의 사건 결과를 알고 있습니다. 그 전 기사를 점수화하면 "이미 아는 결과"가 점수에 섞여 백테스트가 좋게 나옵니다. 엑셀 메모도 같은 말을 합니다: "LLM 학습 시점 이전 구간은 미래정보 유출 위험으로 검증 못함."
- DIDM 규칙 (9절 원문): "Pre-cutoff backtests use ChronoGPT-type models or entity-masked prompts (Glasserman & Lin); frontier-model results count only on post-cutoff windows". 8.2: "a frontier API used only prospectively (post-cutoff windows)."
- 이 계획의 규칙:

| 구간 | 쓰는 점수 | 이유 |
|---|---|---|
| 모델 학습 기준일 이전 (과거 검증, Stage 2·3) | Loughran–McDonald 사전, FinBERT, ChronoBERT/ChronoGPT (해마다 그 시점까지만 학습한 모델), 종목명 가린 프롬프트 | 미래 결과를 모르는 모델만 사용. DIDM 9절 "Ablations": LM → FinBERT → LLM 순으로 각 단계가 값을 더해야 남김 |
| 기준일 이후 (앞으로 쌓는 점수, Stage 5) | 최신 LLM (Claude 등) | 기준일 이후 기사는 결과를 모름 |
| 공급사 점수 (Alpha Vantage 감성, GDELT 논조) | 보조 입력. 과거 값이 **당시 계산된 값인지, 나중 모델로 다시 계산한 값인지** 확인 전까지 과거 검증에 쓰지 않음 | DIDM 가정 A2와 같은 위험. Alpha Vantage 감성의 재계산 여부 **미검증** |

- 실무 규칙: 쓰는 LLM마다 공개된 학습 기준일을 기록하고, 그 날짜 + 여유 기간(예: 3개월, 사전등록에서 정함) 뒤 기사만 LLM 점수로 검증합니다. Claude 각 모델의 학습 기준일은 이 문서에서 확인하지 않았습니다 (**미검증**).
- 시각 기록: 모든 기록에 `published_at`(기사 시각)과 `received_at`(우리가 받은 시각)을 같이 저장하고, 검증은 `received_at` 기준으로 합니다. Tiingo 문서도 crawlDate와 publishedDate 차이가 크면 "나중에 채운(backfill) 기사"라고 설명합니다.

---

## 6. RavenPack 비슷한 점수 만들기 (요구 3)

RavenPack 기관용 점수의 공개된 이름(관련성 0~100, 감성 ESS 0~100에 50 중립, 신규성 ENS, 사건 분류)을 따라 DIDM 자체 형식으로 만듭니다 (초안 06 DIDM-1과 같음). RavenPack의 독점 분류표와 값은 저장소에 복사하지 않습니다.

### 6.1 한 기록의 필드

| 필드 | 뜻 | 계산 | 입력 소스 (엑셀 대안) |
|---|---|---|---|
| `relevance_0_100` | 종목이 기사 주제일 확률 ×100 | LLM 질문 확률을 정답 집합으로 보정. 보정 전 대체 규칙(예시, 사전등록에서 확정): 제목 언급 100, 첫 문단 80, 본문 40, 태그만 20. 75 이상만 신호로 씀 | Tiingo 티커 태그, Alpha Vantage 종목 태그·관련성(있으면), GDELT 조직명 |
| `ess_like_0_100` | 방향 감성. 50 중립 | 50 + 50 × (P(긍정) − P(부정)). 확률은 FinBERT 또는 LLM(기준일 뒤) | 기사 제목·요약 (Tiingo description, Alpha Vantage summary). GDELT 논조는 보조 |
| `novelty_24h_0_100` | 새 사건인지 반복 보도인지 | 6.3절 | 같은 입력 + 묶음 정보 |
| `event_type` | 고정 사건 유형 | 6.4절 | 자체 NLP, GDELT 사건 코드, Alpha Vantage 토픽 |
| `uncertainty_entropy` | 판단의 불확실성 | 유형·방향 확률의 엔트로피 | 자체 NLP |
| `p_credibility` | 소문·오보 가능성 | DIDM 5.3 베이즈 신뢰 상태 | 독립 출처 수, 공식 발표 여부 |
| `market_confirmation` | 시장이 실제로 반응했는지 (Impact Analytics 대체) | 6.5절 | 기존 시세 (KIS, Upbit, FRED, Yahoo 캐시) |
| `published_at`, `received_at`, `source_id`, `origin_cluster_id`, `model_version`, `prompt_sha256` | 시점·재현 정보 | DIDM 9절 "Determinism and replay" | — |

### 6.2 감성 점수 대응

| 소스 | 원래 값 | ess_like로 바꾸는 법 | 용도 |
|---|---|---|---|
| 자체 모델 | P(긍정), P(부정) | 50 + 50·(P+ − P−) | 기본 |
| Alpha Vantage | 종목별 감성 점수 (구간 경계 ±0.35 등은 제3자 글 기준, **미검증**) | 공식 문서의 범위 확인 뒤 선형 변환 | 비교 기준선 |
| GDELT | 문서 평균 논조 (−100~+100) | 50 + tone/2 (단순 변환, 보정 필요) | 거시·지정학 배경 |
| Cryptopanic | 사용자 투표 (긍정·부정 등), 패닉 점수 (필드 이름 **미검증**) | (긍정 − 부정)/(긍정 + 부정) → 50 + 50·값 | 암호화폐 보조 |

### 6.3 신규성 점수 만드는 법

1. 기사마다 제목+요약의 문장 벡터(또는 MinHash)를 만듭니다.
2. 같은 종목 + 같은 `event_type` + 유사도 ≥ τ 이면 같은 묶음입니다. 창은 직전 24시간입니다.
3. 묶음의 첫 기사 = 100. k번째 기사 = 100 × δ^(k−1). τ와 δ는 DIDM-0 사전등록에서 정합니다 (예: τ 0.8, δ 0.5 — 예시값, **미검증**).
4. 같은 원문을 옮긴 기사(재게재)는 origin_cluster_id로 묶어 1건으로 셉니다 (DIDM 5.3).
5. 검증: 정답 집합에서 사람이 "새 사건"이라고 표시한 기사와 점수 100의 일치율을 잽니다 (Stage 1).

### 6.4 사건 유형

- DIDM 고정 열거형(K개)을 DIDM-0 사전등록에서 정합니다. 출발안: 통화정책, 물가, 고용, 성장, 재정, 무역·관세, 전쟁·지정학, 선거·정책, 실적, 인수합병, 경영진, 규제·소송, 공급망, 암호화폐 규제·해킹 (NEW MACRO MODEL ②의 "통화정책·인플레이션·전쟁·선거·산업 등"에 기업 사건을 더함).
- 대응표: GDELT 사건 코드(국가·지정학), Alpha Vantage 토픽(통화정책·거시 등, 엑셀 I4), RavenPack·Bigdata.com 범주는 **공개 문서의 이름만** 적습니다.

### 6.5 사건 영향 분석 대체: 시장 반응 확인

| 단계 | 계산 | 결과 |
|---|---|---|
| 기대 반응 | 종목 i, 시장 m: 사건 전 120거래일로 r_i = α + β·r_m 추정 | — |
| 초과 반응 | 사건 창 [0, +1]일 (거시 사건은 [0, +60분])의 초과수익 AR, 거래량 비율, 실현변동성 변화 | 숫자 |
| 판정 | 예측 방향과 같고 \|AR\| > 2σ → CONFIRMED. 반대 → CONTRADICTED. 사건 전 [−5, −1]에 이미 움직임 → ALREADY_PRICED. 그 밖 → PENDING (임계값은 사전등록, 예시값) | `market_confirmation` |
| 사용 | NEW MACRO MODEL 4절: "미확인 이벤트·충돌하는 증거·시장 반응 불일치 시 자동 매수 신호로 단정하지 않는다." | 위험 관문 입력 |

거시 사건의 "예상 대비 충격"은 Trading Economics 컨센서스가 있으면 (발표치 − 컨센서스)/과거 표준편차로 계산합니다. 없으면 NEW MACRO MODEL ④대로 "미상"으로 두고, 대신 FedWatch·Polymarket 확률 변화(사건 전후)를 충격으로 씁니다.

---

## 7. 지금 할 수 있는 것, 키가 필요한 것, 유료인 것 (요구 4)

### 7.1 구분

| 소스 | 지금 (계약·법인 없이) | 필요한 키 이름 (값은 적지 않음) | 법인·계약이 필요한 때 |
|---|---|---|---|
| GDELT 원본 파일 | 가능, 키 없음 | 없음 (BigQuery를 쓰면 Google 계정·요금) | 없음 (출처 표시) |
| FRED 그래프 CSV | 가능, 이미 앱에 있음 (`config.py:280`, 키 없음) | 없음 | 시리즈별 저작권 표시 확인 |
| ALFRED 빈티지 자동 수집 | 가능 (개인 무료 가입). 수동 다운로드는 키 없이 가능 (저장소 `docs/audit/2026-10-27/calendar_batch5/extract_alfred.py` 방식) | `FRED_API_KEY` (제안 이름) | 상업 이용 조건 확인 |
| Polymarket | 기술적으로 키 없음. **한국 접속 차단(2026-08-18) 때문에 이용 가능 여부 미검증** | 없음 (조회만) | 약관·한국 법 확인 전 사용 보류 권장 |
| Kalshi (엑셀 U4 메모의 같은 유형) | 공개 시세 조회 가능 여부 **미검증** | 미정 | 약관 확인 |
| Alpha Vantage | 무료 키 (하루 25건) | `ALPHAVANTAGE_API_KEY` | 상업 이용 조건 미확인 (엑셀) |
| Tiingo | 무료 플랜 (뉴스 API 포함 여부 **미검증**), 개인 $30 | `TIINGO_API_KEY` | 사업자 $50, 재배포·과거 3개월 초과는 엔터프라이즈 (엑셀) |
| Cryptopanic | 무료 플랜 (존재 여부 확인 필요) | `CRYPTOPANIC_API_KEY` | Enterprise 견적, 무료는 출처 표시 필요 |
| CME FedWatch | 유료 구독 ($25 종가판), CME 계정·권한 부여 필요 | `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET` (제안 이름, 인증 방식 **미검증**) | 앱 화면 표시·재배포는 별도 시세 라이선스일 가능성 (**미검증**) |
| Trading Economics | 유료, 견적 | `TRADINGECONOMICS_API_KEY` | 재배포는 Enterprise (제3자) |
| 자체 NLP (LLM) | 가능. 이미 `ANTHROPIC_API_KEY` 이름이 `.env.example`에 있음 | `ANTHROPIC_API_KEY` (기존) | 상업 약관 확인 |

- 키는 이름만 씁니다. 값은 채팅·저장소·로그에 쓰지 않습니다. 보관 방식은 D7 결정(OS 키 보관함)을 따릅니다.
- `.env.example`에 새 이름을 더하는 일은 공유 파일이라 병합 대기열을 거칩니다.
- DIDM 출력과 공급사 점수는 내부 연구용입니다. 앱 화면에 공급사 데이터를 보여 주지 않으면, 법인 뒤에도 구조 변경 없이 키만 사업자 요금제로 바꿉니다 (D7 조건과 맞음). 고객 화면 표시·재배포를 하려면 계약과 서버 중계(D7 부록 C의 C안)가 필요할 수 있습니다.
- 클라우드 세션 네트워크: 이 세션에서는 `www.alphavantage.co`, `www.tiingo.com`, `cryptopanic.com`이 막혔습니다. 데이터소스 세션이 직접 시험하려면 환경에 호스트 허용이 필요합니다. 아니면 초안의 방식대로 소유자 PC에서 스크립트를 돌리고 출력만 붙입니다.

### 7.2 월 비용 (USD)

LLM 가정: 기사 1건 = 입력 1,500토큰 + 출력 200토큰, 하루 1,000~3,000건 (월 3만~9만 건). 가격은 Anthropic 공개 가격의 2026-11-03 기준 사본입니다 (Claude Haiku 5.5 입력 $0.10, 출력 $0.50 / 100만 토큰; Claude Sonnet 5.5 $2 / $10; Batch는 50%). 사고(thinking) 토큰이 출력으로 더 붙을 수 있어 실제는 더 높을 수 있습니다 (**추정**).

| 항목 | 최소 (Stage 0~2, "3단계 전 $0" 규칙 지킴) | 권장 (앞으로 쌓기 시작) | 근거 |
|---|---|---|---|
| GDELT | $0 | $0 | 엑셀, gdeltproject.org |
| FRED/ALFRED | $0 | $0 | 엑셀 |
| Polymarket | $0 (한국 이용 가능 확인 뒤) | $0 | 엑셀 |
| CME FedWatch | $0 (대신 Polymarket·Kalshi 연준 시장) | $25 (종가판, 2015년 이력; 월 1,000건 넘게 받으면 $75일 수 있음, **미검증**) | 엑셀, 제3자 (CME 가격표 미확인) |
| Alpha Vantage | $0 (하루 25건) | $49.99 | 엑셀, 공식 페이지 (검색) |
| Tiingo | $0 (무료 플랜) | $30 (개인) | 엑셀 |
| Cryptopanic | $0 | $0 | 엑셀 |
| Trading Economics | $0 (안 씀, 충격은 "미상") | 제외 (견적. 제3자 $149~$299/월, **미검증**) | 엑셀, 4절 |
| LLM (Haiku 5.5) | Batch $3.75~11.25 | 실시간 $7.50~22.50 | 위 가정 |
| **합계** | **약 $4~11** | **약 $112~127** | |

참고: 같은 양을 Claude Sonnet 5.5로 돌리면 월 $150~450 (Batch $75~225)입니다. 정답 집합 1,000~1,500건 비교 채점은 Sonnet 5.5로 1회 약 $5~8입니다. 과거 구간 점수화는 미래정보 규칙(5.1절) 때문에 로컬 모델(FinBERT, ChronoBERT)로 하므로 API 비용이 없습니다 (DIDM 10.6: "ChronoBERT/ChronoGPT inference runs on the existing local GPU/NPU path").

권장안은 DIDM의 "3단계 통과 전 유료 데이터 $0" 규칙과 월 약 $105만큼 어긋납니다. 그래서 단계별로 켜는 것을 제안합니다:

| 시점 | 켜는 것 | 이유 |
|---|---|---|
| 지금 | 무료 전부 + Haiku Batch | 앞으로의 점수는 "직접 쌓은 만큼"이라 하루라도 빨리 쌓기 시작 |
| Stage 2 시작 (FOMC 사건연구) | CME 종가판 1~2개월 ($25~50), 약관이 이력 저장을 허락하면 | 2015년 이후 FOMC 확률 이력 |
| Stage 3 통과 뒤 | Tiingo·Alpha Vantage 유료, Trading Economics 견적, RavenPack·Bigdata.com 기준선 비교 | DIDM 8.2 업그레이드 순서 |

---

## 8. 상업 이용 전에 확인할 약관 (요구 5)

**법률 자문이 아닙니다.** 아래는 확인할 질문 목록입니다. 답은 각 약관 원문과 변호사 의견으로 정합니다.

| 소스 | 확인할 것 | 지금 아는 것 |
|---|---|---|
| GDELT | 출처 표시 방법, 기사 본문(언론사 저작물)을 받아 저장해도 되는지 | 공식 약관: 학술·상업·정부 용도 무제한·무료, 재배포 허용, 인용과 링크 필수 (gdeltproject.org/about). GDELT Cloud는 별도 서비스·별도 약관 |
| FRED/ALFRED | API 약관, 앱마다 키 따로 쓰기, 시리즈별 저작권(제3자 소유 시리즈는 허락 필요) | 키 무료. 저장소 기록에 "ICE licence (FRED copy starts 2023-10)" 같은 시리즈가 있음 (`data/backlog_registry.json`) |
| Polymarket | 약관, 데이터 재사용·표시 허용 범위, **한국 접속 차단 결정의 영향**, 국내 이용자가 데이터를 받는 것 자체의 문제 여부 | 방송통신심의위원회 2026-08-18 국내 접속 차단 결정 (형법·국민체육진흥법 관련 보도). 한국 거주자의 API 사용은 변호사 확인 전 보류 권장 |
| Kalshi | 약관, 한국에서 이용 가능 여부 | 확인 안 함 |
| CME FedWatch | 시세 라이선스 (내부 이용과 화면 표시 구분), 이력 저장 허용, FedWatch 웹 화면 수집 금지 여부 | 권한 부여 필요 (CME 문서). 종가판 $25/월 (엑셀·제3자 값, 응답 건수 구간제일 수 있음)과 나머지는 **미검증** |
| Trading Economics | 요금제별 캘린더·컨센서스 포함 여부, 저장·재배포 | 재배포는 Enterprise 맞춤 가격 (제3자) |
| Alpha Vantage | 상업 이용 조건, 과거 뉴스 깊이, 과거 감성의 재계산 여부 | 엑셀: "상업 이용 조건과 과거 뉴스 깊이는 확인 못함" |
| Tiingo | 개인 요금제의 사업 이용 금지 범위, 재배포, 뉴스 과거 기간 | 엑셀: 개인 $30·사업자 $50, 재배포·3개월 초과는 엔터프라이즈 |
| Cryptopanic | 무료 플랜 존재, 출처 표시 위치, 상업 이용 = Enterprise 여부 | 공식 페이지: 무료는 뉴스 피드 위쪽에 출처 표시 필요 |
| 자체 NLP (LLM 공급사) | 상업 약관, 입력 데이터 보관, 출력 사용 권리 | 입력 기사 본문의 권리는 위 각 소스의 문제 |
| 한국 법 (공통) | 신호를 외부에 보이면 투자자문·유사투자자문 신고가 필요한지 | DIDM 8.3: "DIDM outputs stay internal until that opinion exists." 법률 의견 전까지 내부용 |

공통 원칙 (DIDM 8.3, 초안 06 규칙 7·9): 네이버·다음 스크래핑 금지, 소셜 원문 재배포 금지, 파생 특징만 저장, 공급사 점수와 DIDM 출력은 내부용, 공급사의 독점 분류표·값을 저장소에 복사하지 않음.

---

## 9. 데이터소스 세션의 첫 3개 작업 (요구 6)

ID는 초안 체계(`DS-`, `DIDM-`)를 따릅니다. 시작 전 원장(ledger)에서 같은 ID와 파일을 찾아 이미 끝난 일인지 확인합니다.

### 작업 1. DS-1 대안 평가표 (엑셀 기준으로 다시 씀)

- 파일: `docs/didm/VENDOR_EVAL_2026-11.md` (새 파일).
- 내용: 엑셀의 9개 대안 × 19개 정보 유형의 O/X/?를 **그대로** 옮기고, 옆 칸에 공개 페이지 확인 결과(URL·확인 날짜)를 둡니다. 4절의 다른 값 4건(CME 장중 이력, Cryptopanic 무료 플랜, GDELT GKG 판, Trading Economics 가격)과 Polymarket 한국 차단을 포함합니다. 8절 약관 질문을 소스별 칸으로 둡니다.
- 엑셀에 없는 무료 공식 소스(EDGAR, OpenDART/KIND, ECOS)는 소유자 답(11절 질문 3)에 따라 넣거나 "제외"로 적습니다.
- 완료 조건: (1) 모든 칸이 O/X/? 중 하나와 출처를 가짐 (2) "?" 칸마다 "무료 키 1회 호출로 확인", "공급사 문의", "공급사 무응답" 중 처리 방법이 적힘 (3) 엑셀 원래 값이 바뀐 칸이 0개 (다른 값은 옆 칸에만) (4) 소유자 확인.

### 작업 2. DIDM-0 + DIDM-1 사전등록과 점수 스키마

- 파일: `docs/didm/PREREG_V0.md`, `docs/didm/SCORE_SCHEMA_V0.md`, `core/didm/llm/schema.py`, `tests/didm_schema_acceptance.py` (저장소 이름 규칙 따름).
- 내용: 6절의 필드, 사건 유형 K개, 신규성의 τ·δ, 관련성 75 기준, 시장 반응 판정 임계값, 5.1절 미래정보 규칙(모델별 학습 기준일 + 여유 기간), 대응표 (DIDM 필드 → 엑셀 대안 필드 → RavenPack 공개 필드 이름). Bigdata.com 대응 열은 "3단계 뒤"로 둡니다.
- 완료 조건: (1) 대응표의 모든 DIDM 필드에 대안 쪽 입력 또는 "자체 계산"이 적힘 (2) 스키마 테스트가 네트워크 없이 통과하고 잘못된 기록을 거부함 (3) Stage 1 정답 집합 형식 1건 예시가 스키마를 통과 (4) 사전등록 문서를 소유자가 승인 (5) 첫 코드 PR이 `core/didm/**` 경로를 `runtime-smoke.yml`의 경로 목록에, 테스트를 CI 단계에 더함 (초안 06 규칙 6).

### 작업 3. DS-4a 키 없는 첫 커넥터 + 시점 저장소

- 파일: `core/didm/store/` (받은 시각 기록), `core/didm/ingest/gdelt.py`, `core/didm/ingest/alfred.py`, 고정 자료 테스트.
- 대상: GDELT 2.0 (15분 이벤트·GKG 파일, 2015-02 이후), ALFRED (빈티지; `FRED_API_KEY`가 없으면 소유자 수동 다운로드 파일을 읽는 길). Polymarket은 8절 확인 전까지 커넥터만 만들고 실행은 보류합니다.
- 앞으로의 점수를 쌓기 위해, 수집 → 6절 점수(로컬 FinBERT 기준선) → 저장까지 하루 1회 도는 최소 경로를 만듭니다. 실행은 소유자 PC 또는 호스트가 허용된 환경에서 합니다.
- 완료 조건: (1) 같은 "as of" 질의를 두 번 해도 같은 기록 (초안 06 DS-4 기준) (2) 모든 기록에 `published_at`과 `received_at`이 있음 (3) 테스트는 고정 자료만, 네트워크 없음 (4) `docs/compliance/08-third-parties.md`에 GDELT·FRED 행 추가 (공유 파일 PR로 모음) (5) GDELT 출처 표시 문구 포함.

(초안 06의 DS-H 홈 지표 작업은 그대로 진단 출력 뒤에 합니다. 이 3개와 겹치지 않습니다.)

---

## 10. 초안에서 바꿀 곳 (D14-A → 엑셀 대안)

| 파일 | 지금 | 바꿀 내용 |
|---|---|---|
| `OWNER_REPORT_2026-11-17.md` 31행 | D14 ★A Bigdata.com Pro 2주 시험 | 소유자 답: 엑셀 대안으로 구성, RavenPack·Bigdata.com은 DIDM 3단계 뒤 |
| 같은 파일 55행 | "(D14-A면) Bigdata.com 계정 ... `BIGDATA_API_KEY`" | 삭제. 대신 "필요 시 무료 키 가입: `FRED_API_KEY`, `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY` (값은 PC에만)" |
| `MASTER_WORK_DESIGN` 101행 (다이어그램) | DS-2 Bigdata.com 시험 | DS-4a 무료 커넥터 (GDELT, ALFRED) |
| 같은 파일 320·321행 | DS-3 RavenPack 견적 문안, 소유자 "Bigdata.com" | DS-3은 "3단계 통과 뒤". 소유자 할 일에서 Bigdata.com 삭제 |
| 같은 파일 부록 D 519·521행 | D14-A 중단 조건, DS-2 시험 방법 | 삭제하고 이 문서 0·7절 요약으로 대체. 부록 D 표에 엑셀 대안 9개 줄 추가 (또는 이 문서 링크) |
| 같은 파일 561행 | "35 둘 중 하나 선택 / 권장 Bigdata.com / D14" | "엑셀 대안 (소유자 D14)" |
| `sessions/06_DATA_SOURCE_DIDM_NEW.md` 3·17~19·65·67행 | D14-A, 키 처리, DS-2, DS-3 지금 | "확정된 방향"을 이 문서 0절로 바꾸고, 작업 순서를 9절로. DS-2 삭제, DS-3은 3단계 뒤 |
| 같은 파일 42·51·53·54행 | DS-1 대상 14개 공급사, 대응표의 Bigdata.com 열, "3단계에서 Bigdata.com daily_sentiment를 넘어야 할 기준선" | DS-1은 엑셀 9개 기준 (기존 14개는 참고 열). 3단계 기준선은 "LM 사전·FinBERT·Alpha Vantage 감성", RavenPack·Bigdata.com은 3단계 뒤 |

---

## 11. 소유자에게 확인할 것 (한 줄씩 답하면 됩니다)

1. "3단계" = DIDM Stage 3 (예측 가치 검증) 맞습니까? (아니면 뜻하신 단계 구분을 알려 주세요.)
2. 비용: 최소안(월 약 $4~11)으로 시작하고, CME $25는 Stage 2에서, Alpha Vantage·Tiingo 유료는 3단계 뒤에 켜도 됩니까? (권장안 전체를 지금 켜면 월 약 $112~127.)
3. 엑셀 밖의 무료 공식 소스 (SEC EDGAR, OpenDART/KIND, ECOS)를 더해도 됩니까? 한국 종목은 이것 없이는 비어 있습니다.
4. Polymarket은 한국 차단 때문에 변호사 확인 전까지 보류하고, Kalshi를 같은 역할로 검토해도 됩니까?

---

## 12. 미검증 목록

- Tiingo 가격 ($30/$50)과 무료 플랜의 뉴스 API 포함 여부.
- CME FedWatch 종가판 가격 ($25는 엑셀·제3자 값, 구간제일 수 있음), 장중판 가격, 장중판 이력 시작일(문서상 2025-11-01), API 인증 방식, 이력 저장 허용.
- Cryptopanic 무료 플랜이 지금도 있는지, 감성·패닉 점수 필드 이름.
- Alpha Vantage 종목별 관련성 필드 존재, 과거 뉴스 깊이, 과거 감성의 재계산 여부, 상업 조건.
- Trading Economics 가격과 요금제별 컨센서스 포함 여부.
- Polymarket API의 한국 내 접속·이용 가능 여부. Kalshi 전부.
- FRED 분당 120건 (제3자), 시리즈별 상업 조건.
- Claude 각 모델의 학습 기준일, 사고 토큰을 포함한 실제 LLM 비용.
- 엑셀 메모의 "계획서 3.2·3.3·4.1" 원문 문서.
- 6절의 예시 임계값 (관련성 규칙 점수, τ, δ, 2σ, 사건 창). 모두 사전등록에서 정할 값입니다.

---

## 13. 출처

내부 (2026-11-17 읽음):
- 소유자 답: handoff `CURRENT.md`의 "소유자 답: 11-16 결정 D1~D14" 절 5번.
- 소유자 엑셀 글 사본: `plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt` (handoff 브랜치) (원본 `ravenpack_alt.xlsx`, 시트 1개 확인).
- Notion: DIDM `02e5c916fe0c821bb15701f648e9db87` (TL;DR, 6.2, 8.1, 8.2, 8.3, 9, 10.6), DIDM_Research_Report `2045c916fe0c82ca8efe8157c0c70bd8`, Types of Info & Ravenpack's Role `41b5c916fe0c80ddb4e2ce2e1d376003`, NEW MACRO MODEL `4135c916fe0c80dbb7d5f10a6e09077b` (3절 ④·⑦, 4절, 8절 P1-1), QUANTGEN PROJECT `34f5c916fe0c800b9b4af35c80ebe778` (11/16 DIDM 요청).
- 초안: `OWNER_REPORT_2026-11-17.md` 31·55행, `MASTER_WORK_DESIGN_2026-11-17.md` 부록 D, `sessions/06_DATA_SOURCE_DIDM_NEW.md`.
- 저장소 `origin/main` `e01e152`: `config.py:280` (FRED 키 없는 CSV), `.env.example` (키 이름), `data/krx/opendart_client.py`, `docs/audit/2026-10-27/calendar_batch5/extract_alfred.py`, `data/backlog_registry.json`.
- LLM 가격: Anthropic 공개 가격의 2026-11-03 사본 (claude-api 도구 안내). 결제 화면에서 다시 확인 필요.

공개 웹 (모두 2026-11-17 검색. 직접 열기는 일부 호스트가 막혀 검색 결과 기준):
- Alpha Vantage: https://alphavantage.co/premium , https://www.macroption.com/alpha-vantage-api-limits/ , https://www.xpay.sh/agent-ready-index/alphavantage/
- Tiingo: https://api.tiingo.com/products/news-api , https://api.tiingo.com/documentation/news , https://www.findmymoat.com/vs/seeking-alpha-vs-tiingo , https://www.github.com/smartcontractkit/external-adapters-js/blob/main/packages/sources/tiingo/README.md
- CME FedWatch: https://www.cmegroup.com/market-data/market-data-api/fedwatch-api.html , https://www.cmegroup.com/market-data/browse-data/catalog/fedwatch-data.html , https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/1054343170/CME+FedWatch+Intraday+API , https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457320466/CME+FedWatch+API , 종가판 가격 구간 (제3자, 검토 때 2026-11-17 검색) https://www.findmymoat.com/vs/cme-fedwatch-vs-financialdata-net
- Cryptopanic: https://cryptopanic.com/developers/api/about , https://dev.to/tigusigalpa/stop-fighting-the-cryptopanic-api-meet-cryptopanic-php-the-modern-php-sdk-1il2
- GDELT: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/ , https://blog.gdeltproject.org/introducing-gkg-2-0-the-next-generation-of-the-gdelt-global-knowledge-graph/ , https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/methodologies/globaldatabaseofeventslanguageandtonegdeltappendix , https://www.gdeltproject.org/about.html
- Trading Economics: https://tradingeconomics.com/analytics/pricing.aspx , https://businessquant.com/resources/best-macroeconomic-data-providers , https://tradingtoolshub.com/review/tradingeconomics/
- FRED/ALFRED: https://fred.stlouisfed.org/docs/api/fred/fred_vs_alfred.html , https://fred.stlouisfed.org/docs/api/fred/fred.html
- Polymarket: https://docs.polymarket.com/api-reference/rate-limits , https://koreatimes.co.kr/business/companies/20260819/korea-moves-to-block-polymarket-over-illegal-gambling , https://cointelegraph.com/news/south-korea-block-polymarket-gambling-concerns
