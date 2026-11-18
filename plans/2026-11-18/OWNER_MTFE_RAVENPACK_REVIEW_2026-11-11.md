# TRADEGEN MTFE — RavenPack 검토와 대체 데이터 공급원

Nov 11, 2026 · @GEON

## 요약과 판단

RavenPack은 탐색용으로는 Go, 운영 데이터 원천으로는 보류입니다. 도식의 거시경제 분석 칸은 뉴스 API 없이 시장가격과 공식 통계만으로 먼저 구현할 수 있습니다.

| 대상 | 판단 | 근거 |
| --- | --- | --- |
| Bigdata.com Pro로 품질 탐색 | Go | 월 $40\~50로 즉시 시작, 감성·토픽 품질을 직접 확인 가능 |
| Bigdata.com 셀프 요금제를 MTFE 운영 원천으로 | No-go | 저장·ML 학습·제품 구동을 막는 약관, Novelty 필드 부재, 감시 최소 주기 1시간 |
| RavenPack Analytics / EDGE | 보류 | 기능은 설계와 맞지만 가격과 소규모 팀 계약 가능 여부가 미확인. 메일로 확인 |
| 시장가격 기반 거시 신호 + 공식 통계 | Go, 우선 구현 | 무료이거나 월 $25 수준, 시점별 데이터로 백테스트 가능, 도식의 세 입력을 직접 수치화 |
| 뉴스 텍스트 계층 | 2단계 | 1단계 융합 모델 대비 추가 예측력이 검증될 때만 도입 |

권장 순서는 시장가격 기반 거시 신호로 A/B/C 모델을 먼저 돌리고, 그 결과를 기준선으로 삼아 뉴스 데이터의 추가 가치를 측정하는 것입니다. 계획서의 핵심 원칙인 "정보 추가가 곧 예측력 향상은 아니다"를 데이터 구매 전에 검증하는 구조입니다.

## RavenPack 상품 구조와 비용

RavenPack은 기관용 Analytics/EDGE와 셀프 가입형 Bigdata.com 두 갈래이며, 가격이 공개된 쪽은 Bigdata.com뿐입니다. 계획서 3.2가 전제하는 필드는 기관용 상품 쪽에 있습니다.

| 항목 | RavenPack Analytics / EDGE | Bigdata.com |
| --- | --- | --- |
| 대상 | 헤지펀드·은행 등 기관 | 개인·소규모 팀도 셀프 가입 |
| 가격 | 비공개, 영업 견적 | 공개 요금제 |
| Python | `ravenpackapi` | REST API (`bigdata-client`는 종료 예정) |
| 감성·관련성·신규성·이벤트 분류 | 제공 | 일부만 제공 |
| 실시간 | 스트리밍 지원 | 문서상 스트리밍 없음 |
| API 키 발급 | 고객 담당자 경유 | 가입 후 직접 발급 |

### Bigdata.com 요금제

| 요금제 | 월 요금(USD) | 포함 크레딧 | 비고 |
| --- | --- | --- | --- |
| Starter | 0 | $10, 1회 한정 | API 포함 여부가 문서마다 다름 |
| Pro | 40 (정가 50 표기) | 매월 $50 | API/MCP, 감성 신호, 프리미엄 뉴스 전체 |
| Max | 160 (정가 200 표기) | 매월 $200 | 레이트 리밋 5배, API 키 무제한 |
| Enterprise | 견적 | 연간 약정액을 할인 단가로 차감 | SLA, 맞젤 계약·라이선스 |

출처: [Bigdata.com Pricing](https://bigdata.com/pricing), [개발자 문서 Pricing](https://docs.bigdata.com/getting-started/bigdata_pricing)

- **실제 과금은 토큰 종량제입니다.** 토큰 단가표는 공개 페이지에 없고 로그인 후 Usage 화면에서만 보입니다.
- **공개 예시 기준 리서치 워크플로 1회가 $0.57\~1.82입니다.** 무료 $10은 이 기준으로 5\~17회 분량이며, 이 횟수는 추정치입니다.
- **프리미엄 뉴스가 가장 비쌉니다.** $1.70짜리 예시에서 프리미엄 뉴스 몫이 $0.46으로 콘텐츠 유형 중 최대였습니다. 대량 처리는 [배치 검색](https://docs.bigdata.com/getting-started/search/overview.md)을 쓰면 50% 낮아집니다.
- **요금 페이지에 연간 결제 20% 할인 토글이 있습니다.** 표의 $40·$160이 월 결제 기준인지 연간 결제 기준인지는 페이지에 명시돼 있지 않습니다.

### 기관용 상품 가격

공식 가격은 공개돼 있지 않습니다([G2](https://www.g2.com/products/ravenpack/pricing)). 떠도는 수치는 두 가지이고 둘 다 검증되지 않았습니다.

- 5년 전 [익명 게시판 글](https://www.econjobrumors.com/topic/academic-pricing-for-dow-jones-thomson-reuters-ravenpack-news-analytics): 학술용이 패키지에 따라 연 $20k\~40k
- [리뷰 사이트](https://smarterway.ai/tools/ravenpack): 기관 구독이 연 수십만\~수백만 달러

이 범위가 맞다면 소규모 팀 예산과는 자릿수가 다릅니다. 메일에서 스타트업·연구용 조건이 있는지를 가장 먼저 확인할 항목입니다.

## 무료 티어 품질과 지원 범위

Bigdata.com 무료 티어는 품질 확인용 맛보기이고, 계획서 3.2의 여섯 항목 가운데 온전히 제공되는 것은 감성과 엔티티 매핑 두 가지입니다.

- **크레딧이 1회성 $10입니다.** 지속 운용은 불가능합니다.
- **API 포함 여부가 불명확합니다.** 개발자 문서는 Starter도 앱·MCP·API로 쓸 수 있다고 하고, 요금 페이지는 API/MCP를 Pro 기능으로 적습니다. 가입 후 키 발급이 되는지 직접 확인해야 합니다.
- **레이트 리밋은 넉넉합니다.** 키당 분당 500건, IP당 분당 1,500건입니다([Rate limits](https://docs.bigdata.com/api-rest/rate_limits.md)).
- **감성 모델은 주식 편향입니다.** 청크마다 -1\~+1 점수가 붙지만 학습 데이터가 2014\~2023년의 주식·기업 이벤트 기사 위주입니다([Chunk sentiment](https://docs.bigdata.com/getting-started/search/chunk_sentiment.md)). 금리·지정학·암호화폐 뉴스에서 정확도가 떨어질 수 있다는 것은 이 학습 범위에서 나온 추론입니다.

### 계획서 3.2 항목별 대응

| 계획서 3.2 항목 | Bigdata.com이 주는 것 | 판정 |
| --- | --- | --- |
| News Sentiment | 청크 감성, 일별 엔티티 감성 | 가능 |
| Relevance | 0\~1 점수. 같은 검색 안에서만 비교 가능 | 부분 |
| Novelty | 검색 결과에 필드 없음. 일별 감성의 가중치로만 내부 반영 | 불가 |
| Event Classification | 7,000개 이상 토픽(기업·거시·지정학) 태그 | 부분 |
| Entity Mapping | 1,200만 개 이상 엔티티 | 가능 |
| Impact Analytics | 문서에서 확인되지 않음 | 불명 |

출처: [Search results](https://docs.bigdata.com/getting-started/search/search_results.md), [Entity sentiment signals](https://docs.bigdata.com/blog/market-data/entity-sentiment-signals.md), [Knowledge Graph](https://docs.bigdata.com/getting-started/knowledge_graph/introduction.md)

### 히스토리·지연·자산군

| 항목 | Bigdata.com | RavenPack Analytics / EDGE |
| --- | --- | --- |
| 히스토리 | 일별 엔티티 감성은 요청당 약 10년치, 예시는 2006년부터. 뉴스 원문은 소스별로 보존 기간이 다름 | 2000년 1월부터 |
| 지연 | 색인은 실시간, 수신은 폴링. 자동 감시(Monitor) 최소 주기 1시간, 전달은 이메일만 문서화 | 실시간 스트리밍 구독 |
| 자산군 | 감성 문서의 예시는 전부 기업. 통화·원자재·암호화폐가 엔티티로 다뤄지는지는 문서에서 미확인 | 통화 2,000개 이상, 원자재 100개 이상 |
| 소스 | 수천 개 웹사이트와 프리미엄 공급사 | 40,000개 이상 소스, 13개 언어 |

출처: [Monitors](https://docs.bigdata.com/getting-started/monitors/overview.md), [Source FAQ](https://docs.bigdata.com/faq/source_questions.md), [WRDS RavenPack](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/ravenpack/), [WRDS 소개 자료](https://wrds-www.wharton.upenn.edu/documents/1395/RavenPack.pdf), [python-api](https://github.com/RavenPack/python-api)

기관용 상품의 수치는 WRDS 자료 기준이며, 현재 판매 조건과 다를 수 있습니다.

## 계획서와 충돌하는 지점

Bigdata.com 셀프 요금제를 그대로 쓰면 계획서의 네 곳과 충돌합니다.

1. **Python SDK가 곧 종료됩니다.** `bigdata-client`는 2026년 12월 31일에 지원이 끝나고 해당 엔드포인트도 폐쇄됩니다([Changelog](https://docs.bigdata.com/release-notes/bigdata_client_changelog.md)). 처음부터 REST API로 짜야 합니다.
2. **저장 금지가 7.1절과 P1 완료 기준에 걸립니다.** 약관상 원본 콘텐츠는 소비 시점 이후 저장·캐시·보관할 수 없고, 콘텐츠 DB 구축과 체계적 다운로드도 금지입니다(4.2.3, 4.5.9, 4.5.10). "재현 가능한 원장"과 시점 정합 백테스트를 이 조건에서 만들기 어렵습니다.
3. **ML 학습 금지가 5.3절 방식 B에 걸립니다.** 서면 승인 없이는 콘텐츠로 모델을 학습·미세조정·평가할 수 없습니다(4.2.3(d), 4.5.8).
4. **상용화에는 별도 계약이 필요합니다.** 제품이나 서비스를 구동하는 용도는 엔터프라이즈 계약이 있어야 합니다(4.5.2). 약관에 자동매매를 직접 다룬 조항은 없습니다.

조항 번호는 [Bigdata.com Terms & Conditions](https://bigdata.com/terms-and-conditions) 기준입니다. 이 요약은 법률 검토가 아니므로, 자기 계좌 자동매매가 4.5.2에 해당하는지는 RavenPack에 서면으로 확인받아야 합니다.

## RavenPack 담당자에게 메일로 확인받을 항목

진행 중인 메일에서 아래 13개 항목의 답을 서면으로 받으면 보류 판단을 Go 또는 No-go로 확정할 수 있습니다. 가격보다 라이선스 네 항목이 결정적입니다.

### 상품과 가격

- [ ] Analytics/EDGE의 스타트업·연구용 요금과 최소 계약 금액
- [ ] 개인 또는 소규모 팀과의 계약 가능 여부, 최소 계약 기간
- [ ] 체험 데이터의 범위와 기간
- [ ] Bigdata.com Enterprise의 최소 연간 약정액

### 라이선스

- [ ] 수신 데이터를 자체 DB에 저장하고 백테스트에 재사용할 수 있는지
- [ ] 데이터로 ML 모델을 학습·평가할 수 있는지
- [ ] 자동매매 알고리즘의 입력으로 쓸 수 있는지, 자기 계좌 운용이 약관 4.5.2의 "제품·서비스 구동"에 해당하는지
- [ ] 파생 신호를 탑재한 제품을 제3자에게 판매할 때의 조건

### 데이터

- [ ] 시점별(point-in-time) 과거 데이터의 시작 연도와 타임스탬프 정밀도
- [ ] 암호화폐·통화·원자재·거시 토픽의 커버리지
- [ ] 실시간 전달 방식과 뉴스 발행부터 수신까지의 지연
- [ ] Novelty·Relevance·이벤트 분류 필드가 포함된 상품
- [ ] `bigdata-client` 종료 이후의 Python 지원 계획

## 도식 기준 필요 데이터 분해

도식의 거시경제 분석 칸에 적힌 세 입력은 모두 시장에서 직접 관측되는 수치여서, 뉴스를 해석하지 않고도 만들 수 있습니다. 뉴스가 꼭 필요한 곳은 예고 없이 터지는 사건 하나입니다.

| 도식·계획서의 입력 | 직접 측정하는 방법 | 데이터 원천 | 뉴스 필요 |
| --- | --- | --- | --- |
| 금리 기대 변화 | 연방기금금리 선물이 내재한 인상·인하 확률의 변화, 2년물 국채금리 변화 | CME FedWatch API, FRED, 예측시장 | 아니오 |
| 달러 약세 | 달러지수의 수익률과 추세 | FRED, 환율 시세 | 아니오 |
| 위험선호 개선 | VIX 수준과 변화, 신용 스프레드, 주식 대 채권 상대강도 | FRED, 시세 데이터 | 아니오 |
| 예상 대비 충격 (계획서 4.1) | 발표치에서 컨센서스를 뺀 값 | 경제 캘린더 API | 아니오 |
| 예정된 정치 이벤트의 결과 확률 | 예측시장 가격 | Polymarket, Kalshi | 아니오 |
| 예고 없는 사건 (전쟁, 제재, 관세) | 사건 탐지와 분류 | 뉴스·이벤트 데이터 | 예 |

이 분해가 비용 구조를 바꿉니다. 뉴스 계층의 일이 "세상의 모든 뉴스를 점수화"에서 "예고 없는 사건을 빨리 알아채고 분류"로 좁아지면, 기관용 뉴스 분석 피드 없이도 감당할 수 있는 범위가 됩니다.

시장가격에는 이미 뉴스가 반영돼 있다는 점도 같은 방향을 가리킵니다. 금리 선물과 달러지수는 FOMC 결과를 뉴스 감성 점수보다 먼저, 해석 없이 숫자로 줍니다. 다만 이 신호가 BTC 가격 자체와 얼마나 겹치는지는 도식의 "상관관계" 평가에서 확인해야 합니다.

## RavenPack 외 대안

대안은 뉴스가 필요 없는 것부터 세 층으로 나뉩니다. 윗층일수록 싸고 검증하기 쉽고, 아래로 갈수록 RavenPack이 하던 일에 가까워집니다.

### 1층: 시장가격과 공식 통계

| 대안 | 채우는 역할 | 비용 | 갱신 주기와 과거 데이터 |
| --- | --- | --- | --- |
| [CME FedWatch API](https://cmegroup.com/market-data/market-data-api/fedwatch-api.html) | 금리 기대 변화. FOMC 회의별 인상·동결·인하 확률 | 종가 기준 월 $25. 장중은 별도 가격 | 종가판은 일 1회, 장중판은 60초. 2015년부터 |
| [FRED / ALFRED](https://fred.stlouisfed.org/docs/api/fred/) | 국채금리, 달러지수, VIX, 물가·고용·GDP 등 공식 시계열 | 무료, API 키 필요 | 시리즈별로 일\~분기. ALFRED가 발표 시점별 값 제공 |

- **ALFRED가 7.1절의 시점 정합성을 해결합니다.** 거시 지표는 발표 후 수정되므로, 수정 전 값으로 백테스트해야 미래정보가 새지 않습니다. FRED API의 vintage 날짜 조회가 이 용도입니다.
- **FedWatch 요금은 조회량에 따라 오를 수 있습니다.** 반환 건수 1,000건 초과 시 월 $75라는 제3자 정리가 있어 가입 전 확인이 필요합니다.
- **선물 시세로 직접 계산하는 길도 있습니다.** 확률은 30일 연방기금금리 선물 가격에서 나오므로, 선물 시세를 이미 받고 있다면 자체 산출이 가능합니다.

### 2층: 사건 확률과 발표 충격

| 대안 | 채우는 역할 | 비용 | 갱신 주기와 과거 데이터 |
| --- | --- | --- | --- |
| [Polymarket·Kalshi 공개 API](https://prediction.com/blog/polymarket-kalshi-historical-data) | 선거, 금리 결정 등 예정된 사건의 결과 확률 | 무료 | 실시간. Polymarket은 시장 개설 시점부터, Kalshi는 2021년부터 |
| [Trading Economics API](https://docs.tradingeconomics.com/) | 발표치·이전치·컨센서스로 예상 대비 충격 계산 | 유료, 가격 미확인 | 준실시간 캘린더. 월 약 1,600건, 150개국 이상 |

- **예측시장은 계획서 3.3의 감시 대상을 확률 숫자로 바꿔 줍니다.** 미국 선거, 연준 결정처럼 날짜가 정해진 사건에 맞습니다.
- **두 거래소의 같은 사건을 짝짓는 일은 직접 구현해야 합니다.** Kalshi의 인증 요건도 제3자 정리 기준이라 공식 문서 확인이 필요합니다.
- **유동성이 얇은 시장의 확률은 잡음이 큽니다.** 거래량 하한을 두고 걸러야 합니다.

### 3층: 뉴스 텍스트

| 대안 | 채우는 역할 | 비용 | 갱신 주기와 과거 데이터 |
| --- | --- | --- | --- |
| [GDELT 2.0](https://www.gdeltproject.org/data.html) | 전 세계 사건 탐지, 기사량과 논조 | 무료 | 15분. 이벤트는 1979년, GKG는 2013년 4월부터 |
| [Alpha Vantage](https://www.alphavantage.co/premium/) | 종목·암호화폐·외환 뉴스와 감성 점수, 거시 지표 | 무료 하루 25건. 유료 월 $49.99\~249.99 | 유료는 분당 75\~1,200건 |
| [Tiingo News](https://www.tiingo.com/products/news-api) | 티커 태그가 붙은 뉴스 메타데이터. 주식 65,000+, 암호화폐 4,100+ | 개인 월 $30, 사업자 월 $50 | 실시간. 과거 3개월, 엔터프라이즈는 1995년부터 |
| [CryptoPanic](https://cryptopanic.com/developers/api/about) | 암호화폐 뉴스와 감성 | 무료 플랜 있음 | 실시간, 초당 5건 |
| 자체 NLP | 원문을 직접 모아 LLM이나 자체 모델로 사건 분류·감성 산출 | LLM 호출 비용 | 설계에 따름. 과거 데이터는 직접 축적 |

- **GDELT의 논조 점수는 금융 특화가 아닙니다.** 감성보다는 "어떤 사건이 얼마나 보도되고 있는가"를 재는 데 쓰는 편이 맞습니다. 검색용 DOC API는 최근 3개월만 다루고 5초당 1회로 제한된다는 제3자 정리가 있어, 과거 분석은 원본 파일이나 BigQuery를 써야 합니다.
- **Tiingo는 감성 점수를 주지 않습니다.** 반환 필드가 제목·설명·태그·티커·발행일이어서 자체 NLP와 짝을 이뤄야 합니다. 라이선스는 내부 이용 한정입니다.
- **Alpha Vantage와 CryptoPanic은 라이선스와 히스토리 깊이를 확인하지 못했습니다.** CryptoPanic 유료 요금도 미확인입니다.
- **자체 NLP는 개발 중인 DIDM이 들어갈 자리입니다.** 이 경우 사야 하는 것은 "점수화된 분석"이 아니라 "저장·학습이 허용된 원문"이므로, RavenPack에 묻는 질문도 라이선스 쪽으로 무게가 옮겨갑니다.
- **LLM으로 과거 뉴스를 점수화하면 미래정보가 샐 수 있습니다.** 모델이 학습 과정에서 그 뒤의 가격 흐름을 이미 봤을 수 있으므로, 검증 구간은 모델의 학습 종료 시점 이후로 잡아야 합니다.

Bloomberg, LSEG 같은 기관용 뉴스 분석 벤더는 이번 조사에 넣지 않았습니다.

## 권장 구성안과 단계별 도입

1단계는 월 $25 수준의 시장가격 기반 거시 신호만으로 A/B/C 모델을 돌리고, 뉴스 계층은 그 결과를 넘어서는 예측력이 확인될 때 교체 가능한 인터페이스 뒤에 붙이는 구성을 권합니다.

&#91;embedded content: 권장 데이터 구성 · 입력 3계층, 평가, 판단, 기존 위험관리\]

가운데 강조된 칸이 먼저 구현할 부분이고, 점선 칸은 공급원을 바꿔 끼울 수 있게 남겨 두는 부분입니다. 아래 세 칸은 보내 주신 도식과 계획서 6.3의 구조 그대로입니다.

1. **지금: 탐색과 회신 대기.** Bigdata.com Pro 한 달로 감성·토픽 품질을 샘플로 확인하고, RavenPack 메일에 위 13개 항목을 묻습니다. 연동 코드는 REST API 기준으로 작성합니다.
2. **1단계: 시장가격 기반 거시 신호.** FedWatch와 FRED/ALFRED로 금리 기대·달러·위험선호 특징량을 만들어 Model B와 C를 구축하고 A와 같은 조건에서 비교합니다. 결합 방식은 계획서 5.3의 방식 A(Macro Risk Overlay)부터 시작합니다.
3. **2단계: 사건 확률과 발표 충격.** 예측시장 확률과 경제 캘린더의 예상 대비 충격을 더하고, 제외 실험으로 각각의 기여도를 잽니다.
4. **3단계: 뉴스 계층.** 계획서 P1의 "대체 데이터 공급원 인터페이스"를 먼저 정의한 뒤 GDELT나 저가 뉴스 API와 자체 NLP로 시작합니다. RavenPack 계약이 성사되면 같은 인터페이스 뒤에서 교체합니다.
5. **채택 기준.** 각 단계는 독립 Holdout에서 거래비용 차감 후 성과가 직전 단계보다 나을 때만 켭니다.

이 순서에서는 RavenPack 회신이 늦거나 가격이 맞지 않아도 개발이 멈추지 않습니다. 1단계 비용은 FedWatch 종가판 월 $25와 무료인 FRED를 합한 값이며, 시세 데이터는 이미 받고 있다고 가정했습니다.

## 추가로 필요한 정보

아래 여섯 가지가 정해지면 권장 구성의 공급원과 예산을 확정할 수 있습니다.

- [ ] 데이터에 쓸 수 있는 월 또는 연 예산 상한
- [ ] 우선 대상 자산군. 도식의 예시는 BTC인데 암호화폐가 1순위인지
- [ ] 필요한 반응 속도. 초·분 단위인지, 시간·일 단위로 충분한지
- [ ] 자기 계좌 운용만인지, 판매용 제품에 탑재할 계획인지
- [ ] RavenPack 메일에서 지금까지 받은 답변. 가격, 체험 제공 여부, 상대가 제안한 상품
- [ ] 학교 도서관의 WRDS 구독에 RavenPack이 포함돼 있는지

마지막 항목이 예라면 2000년부터의 RavenPack 데이터로 연구용 백테스트를 돌려, 계약 전에 뉴스 신호의 추가 예측력을 측정할 수 있습니다. 학술 라이선스는 보통 상업적 이용을 막으므로 조건 확인이 먼저입니다.

## 출처

모든 가격과 조건은 2026년 11월 11일에 확인한 내용입니다.

### 직접 열어 확인한 페이지

- [Bigdata.com Pricing](https://bigdata.com/pricing)
- [Bigdata.com 개발자 문서: Pricing](https://docs.bigdata.com/getting-started/bigdata_pricing)
- [Bigdata.com Terms & Conditions](https://bigdata.com/terms-and-conditions)
- [bigdata-client Changelog](https://docs.bigdata.com/release-notes/bigdata_client_changelog.md)
- [Bigdata.com Rate limits](https://docs.bigdata.com/api-rest/rate_limits.md)
- [Entity sentiment signals](https://docs.bigdata.com/blog/market-data/entity-sentiment-signals.md)
- [Chunk sentiment](https://docs.bigdata.com/getting-started/search/chunk_sentiment.md)
- [Search results](https://docs.bigdata.com/getting-started/search/search_results.md)
- [Monitors overview](https://docs.bigdata.com/getting-started/monitors/overview.md)
- [Knowledge Graph](https://docs.bigdata.com/getting-started/knowledge_graph/introduction.md)
- [Source FAQ](https://docs.bigdata.com/faq/source_questions.md)
- [RavenPack python-api (GitHub)](https://github.com/RavenPack/python-api)
- [CME FedWatch API](https://cmegroup.com/market-data/market-data-api/fedwatch-api.html)
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/), [FRED API Keys](https://fred.stlouisfed.org/docs/api/api_key.html)
- [GDELT Data](https://www.gdeltproject.org/data.html)
- [Alpha Vantage Premium](https://www.alphavantage.co/premium/)
- [Tiingo News API](https://www.tiingo.com/products/news-api)
- [Polymarket·Kalshi 과거 데이터 정리 (prediction.com)](https://prediction.com/blog/polymarket-kalshi-historical-data)

### 검색 결과 발췌로만 확인한 페이지

아래에서 가져온 수치는 결정 전에 원문을 다시 확인해야 합니다.

- [WRDS: RavenPack](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/ravenpack/), [WRDS RavenPack 소개 자료](https://wrds-www.wharton.upenn.edu/documents/1395/RavenPack.pdf)
- [G2: RavenPack Pricing](https://www.g2.com/products/ravenpack/pricing)
- [EJMR 학술 가격 게시글](https://www.econjobrumors.com/topic/academic-pricing-for-dow-jones-thomson-reuters-ravenpack-news-analytics)
- [smarterway.ai RavenPack 리뷰](https://smarterway.ai/tools/ravenpack)
- [CryptoPanic API plans](https://cryptopanic.com/developers/api/about)
- [Trading Economics API 문서](https://docs.tradingeconomics.com/)
- [CME FedWatch 요금 제3자 정리 (findmymoat)](https://www.findmymoat.com/vs/cme-fedwatch-vs-financialdata-net)
- [GDELT DOC API 제한 제3자 정리 (jentic)](https://jentic.com/apis/api.gdeltproject.org/gdelt)
