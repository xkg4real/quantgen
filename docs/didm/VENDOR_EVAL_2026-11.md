# DS-1 RavenPack 대안 평가표 (소유자 엑셀 기준, 2026-11)

- 작성: DATA_SOURCE_DIDM 세션 (QUANTGEN/MAIN 하부), 2026-11-17. 상태: **초안, 소유자 확인 대기.**
- 근거: 소유자 답 "5. D14 : Ravenpack의 대안책 3단계 (엑셀 파일 참고)의 자료들로 구성할 예정." (2026-11-17). 1차 자료는 소유자 엑셀 `ravenpack_alt.xlsx`의 글 사본 (handoff 브랜치 `plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt`). 메인 분석은 handoff `plans/2026-11-17/D14_RAVENPACK_ALTERNATIVES.md`.
- **엑셀 값은 고치지 않습니다.** 공개 자료나 메인 분석이 다르면 옆 칸에 나란히 적습니다.
- **법률 자문이 아닙니다.** 약관·법규 칸은 확인할 질문입니다. 상업 이용 전에는 각 약관 원문과 변호사 의견으로 정합니다.
- 표시: O 제공 · X 제공 안 함 · ? 공개 자료로 확인 못함 (엑셀 범례와 같음). **미검증** = 원문을 직접 확인하지 못한 값.

## 0. 요약

| 항목 | 내용 |
|---|---|
| 엑셀 구조 | 시트 1개. O/X/? 줄은 **두 줄**뿐: "RAVENPACK 등" (기관용 또는 Bigdata.com 중 하나라도 제공하면 O)과 "대안책" (9개 대안 중 하나라도 제공하면 O). 대안별 O/X/?는 엑셀에 없고, 칸 메모 (F4~X4)와 대안별 설명 (D열)에 근거가 있습니다. |
| 이 문서가 한 일 | ① 두 줄 19칸을 그대로 옮김 (1절) ② 엑셀 메모·설명만으로 **대안 9개 × 19칸**을 풀어 적음 (2절, 칸마다 근거 기호) ③ 공개 자료·메인 분석과 다른 값을 옆에 (3절) ④ 소스별 약관 질문 (4절) ⑤ 키 이름 (5절) ⑥ 참고 열 (6절) |
| 대조 결과 | `python -m tools.didm.check_vendor_eval --excel <엑셀 사본>`: 엑셀 값이 바뀐 칸 **0개**, 2절 표가 엑셀 두 줄과 모순 0건 (7절). |
| "?" 칸 | 대안 쪽 15칸 + RavenPack 쪽 2칸. 처리: 무료 키 1회 호출로 확인 6칸 (DS-4b), 공급사 문의 11칸. |
| 공개 자료 확인 | 이 세션 네트워크에서 `www.alphavantage.co`, `api.tiingo.com`, `cryptopanic.com`, `www.cmegroup.com`, `www.gdeltproject.org`, `fred.stlouisfed.org`, `docs.kalshi.com`, `data.gdeltproject.org`가 모두 막혀 (2026-11-17 22:00 KST, 프록시 거절), **검색 요약 기준**입니다. 원문 직접 확인은 미검증. |

## 1. 엑셀 원래 값 (그대로)

엑셀 3행 (E열 "RAVENPACK 등")과 4행 (E열 "대안책")의 F~X열입니다. 칸 메모는 엑셀 사본의 `=== CELL COMMENTS` 절에 있습니다.

| 열 | 정보 유형 | RAVENPACK 등 | 대안책 | 대안책 칸 메모 (엑셀 원문) |
|---|---|---|---|---|
| F | 뉴스 기사 수집 | O | O | F4: GDELT, Tiingo, Alpha Vantage, Cryptopanic |
| G | 뉴스 감성 점수 | O | O | G4: Alpha Vantage·Cryptopanic 감성, GDELT 논조(tone). Tiingo는 감성 필드 없음 |
| H | 엔티티·티커 태깅 | O | O | H4: Tiingo·Alpha Vantage 주식·FX·암호화폐 티커, GDELT 인물·조직·장소 |
| I | 사건·토픽 분류 | O | O | I4: GDELT 이벤트 데이터, Alpha Vantage 토픽(통화정책·거시 등), 자체 NLP |
| J | 분 단위 이내 실시간 갱신 | O | O | J4: Tiingo·Polymarket 실시간, FedWatch 장중판 60초, GDELT 15분 |
| K | 미국 거시 이벤트 감시 | O | O | K4: CME·FRED·Polymarket·Trad. Econ이 같은 사건을 숫자(확률·통계·컨센서스)로 제공 |
| L | Python에서 API 호출 | O | O | L4: 9개 모두 REST API로 호출 가능 |
| M | 무료 플랜 | O | O | M4: FRED·GDELT·Polymarket 무료, Alpha Vantage 하루 25건, Tiingo·Cryptopanic 무료 플랜 |
| N | 신규성 점수 | O | X | N4: 제공하는 소스 없음. 자체 NLP로 직접 구현해야 함 |
| O | 자산별 관련성 점수 | O | ? | O4: Alpha Vantage 응답에 관련성 필드가 있는지 공개 문서에서 확인 못함 |
| P | 2000년부터의 뉴스 점수 이력 | O | X | P4: GDELT 논조는 2013년 4월부터, Tiingo 유료 플랜 과거 뉴스는 3개월 |
| Q | 시장 내재 금리 확률 (FOMC) | X | O | Q4: CME FedWatch: 30일 연방기금금리 선물 기반, 2015년부터 |
| R | 공식 경제 통계 시계열 | X | O | R4: FRED(국채금리·달러지수·VIX·물가·고용·GDP), Alpha Vantage 거시 지표 |
| S | 발표 시점별 수정 이력 | X | O | S4: FRED의 ALFRED: 지표가 발표·수정된 시점별 값 |
| T | 발표치·컨센서스 수치 | X | O | T4: Trad. Econ: 발표치·이전치·컨센서스로 예상 대비 충격 계산 |
| U | 예정 사건 결과 확률 | X | O | U4: Polymarket(선거·연준 결정 등). Kalshi도 같은 유형 |
| V | 원문 저장·학습 허용 | X | O | V4: GDELT는 전체 데이터를 원본 파일로 공개. 다른 소스는 각 약관 확인 필요 |
| W | 자산 영향 분석 (Impact Analytics) | ? | X | W4: 제공하는 소스 없음. 계획서 4.1의 시장 반응 확인 단계로 자체 구현 |
| X | 암호화폐 뉴스 감성 | ? | O | X4: Cryptopanic, Alpha Vantage(CRYPTO:BTC 등 티커) |

## 2. 대안 9개 × 정보 유형 19개 (엑셀 근거로 풀어 씀)

읽는 법: 칸 = `값·근거`. 이 표의 값은 **엑셀의 대안별 값이 아니라** (엑셀에는 대안별 값이 없음) 엑셀 메모와 설명을 대안별로 나눈 것입니다. 엑셀 두 줄은 3·4번째 열에 그대로 두었고, 7절 스크립트가 서로 모순이 없는지 봅니다 (엑셀 O → 대안 하나 이상 O, X → 모두 X, ? → O 없이 ? 하나 이상).

근거 기호:
- `F4`~`X4`: 엑셀 대안책 행의 그 열 칸 메모 (1절). 메모에 이름이 있으면 O, 메모가 "없음"이라 하거나 이름이 없으면 X, 메모가 "확인 못함"이라 하면 ?.
- `행CME`, `행FRED`, `행Poly`, `행TE`, `행Tiingo`, `행CP`, `행NLP`: 엑셀 "대안" 블록의 그 소스 설명 (D열). 예: 행FRED "뉴스·컨센서스 전망치·사건 해석은 못함", 행TE "유료", 행CME "종가판 월 $25", 행Tiingo "감성 점수는 반환 필드에 없음 … 재배포는 엔터프라이즈 없이 못함", 행CP "실시간 제공", 행NLP "비용은 LLM 호출료".
- `N4규칙`: 엑셀은 자체 NLP가 직접 계산할 수 있는 것을 "제공"으로 세지 않습니다 (N4 "제공하는 소스 없음. 자체 NLP로 직접 구현", W4 같음). 그래서 자체 NLP는 메모에 이름이 있는 칸 (I4, L4)만 O이고, 나머지 직접 계산 항목은 X로 두고 DIDM-1 (`docs/didm/SCORE_SCHEMA_V0.md`)에서 만듭니다.

<!-- matrix:begin -->
| 열 | 정보 유형 | RAVENPACK 등 (엑셀) | 대안책 (엑셀) | CME | FRED | Polymarket | Trad. Econ | GDELT | Alpha Vantage | Tiingo | Cryptopanic | 자체 NLP | "?" 처리 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F | 뉴스 기사 수집 | O | O | X·행CME | X·행FRED | X·행Poly | X·행TE | O·F4 | O·F4 | O·F4 | O·F4 | X·N4규칙 | — |
| G | 뉴스 감성 점수 | O | O | X·행CME | X·행FRED | X·행Poly | X·행TE | O·G4 | O·G4 | X·G4 | O·G4 | X·N4규칙 | — |
| H | 엔티티·티커 태깅 | O | O | X·행CME | X·행FRED | X·행Poly | X·행TE | O·H4 | O·H4 | O·H4 | ?·H4 | X·N4규칙 | Cryptopanic: 무료 키 1회 호출로 확인 |
| I | 사건·토픽 분류 | O | O | X·행CME | X·행FRED | X·행Poly | X·행TE | O·I4 | O·I4 | ?·I4 | ?·I4 | O·I4 | Tiingo: 무료 키 1회 호출로 확인; Cryptopanic: 무료 키 1회 호출로 확인 |
| J | 분 단위 이내 실시간 갱신 | O | O | O·J4 | X·J4 | O·J4 | ?·J4 | O·J4 | ?·J4 | O·J4 | O·행CP | X·N4규칙 | Trad. Econ: 공급사 문의; Alpha Vantage: 무료 키 1회 호출로 확인 |
| K | 미국 거시 이벤트 감시 | O | O | O·K4 | O·K4 | O·K4 | O·K4 | X·K4 | X·K4 | X·K4 | X·K4 | X·N4규칙 | — |
| L | Python에서 API 호출 | O | O | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | — |
| M | 무료 플랜 | O | O | X·행CME | O·M4 | O·M4 | X·행TE | O·M4 | O·M4 | O·M4 | O·M4 | X·행NLP | — |
| N | 신규성 점수 | O | X | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | — |
| O | 자산별 관련성 점수 | O | ? | X·O4 | X·O4 | X·O4 | X·O4 | X·O4 | ?·O4 | X·행Tiingo | X·O4 | X·N4규칙 | Alpha Vantage: 무료 키 1회 호출로 확인 |
| P | 2000년부터의 뉴스 점수 이력 | O | X | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | — |
| Q | 시장 내재 금리 확률 (FOMC) | X | O | O·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | — |
| R | 공식 경제 통계 시계열 | X | O | X·R4 | O·R4 | X·R4 | ?·R4 | X·R4 | O·R4 | X·R4 | X·R4 | X·R4 | Trad. Econ: 공급사 문의 |
| S | 발표 시점별 수정 이력 | X | O | X·S4 | O·S4 | X·S4 | ?·S4 | X·S4 | ?·S4 | X·S4 | X·S4 | X·S4 | Trad. Econ: 공급사 문의; Alpha Vantage: 무료 키 1회 호출로 확인 |
| T | 발표치·컨센서스 수치 | X | O | X·T4 | X·행FRED | X·T4 | O·T4 | X·T4 | X·T4 | X·T4 | X·T4 | X·T4 | — |
| U | 예정 사건 결과 확률 | X | O | X·U4 | X·U4 | O·U4 | X·U4 | X·U4 | X·U4 | X·U4 | X·U4 | X·U4 | — |
| V | 원문 저장·학습 허용 | X | O | ?·V4 | ?·V4 | ?·V4 | ?·V4 | O·V4 | ?·V4 | X·행Tiingo | ?·V4 | X·행NLP | CME: 공급사 문의; FRED: 공급사 문의; Polymarket: 공급사 문의; Trad. Econ: 공급사 문의; Alpha Vantage: 공급사 문의; Cryptopanic: 공급사 문의 |
| W | 자산 영향 분석 (Impact Analytics) | ? | X | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | RAVENPACK 등: 공급사 문의 (DS-3, Stage 3 뒤) |
| X | 암호화폐 뉴스 감성 | ? | O | X·X4 | X·X4 | X·X4 | X·X4 | X·X4 | O·X4 | X·X4 | O·X4 | X·N4규칙 | RAVENPACK 등: 공급사 문의 (DS-3, Stage 3 뒤) |
<!-- matrix:end -->

"?" 17칸의 처리 요약:

| 처리 | 칸 | 언제 |
|---|---|---|
| 무료 키 1회 호출로 확인 | Cryptopanic H·I, Tiingo I, Alpha Vantage J·O·S (6칸) | DS-4b: 소유자가 무료 키를 만든 뒤 소유자 PC에서 `tools/didm/` 스크립트 1회 실행, 출력의 **필드 이름만** 붙여 줌 (키 값 없음). 필드 이름 확인이라 하루 25건 한도 안 |
| 공급사 문의 | (11칸) Trad. Econ J·R·S, V열 6칸 (CME, FRED, Polymarket, Trad. Econ, Alpha Vantage, Cryptopanic), RAVENPACK 등 W·X | 문의 발송은 소유자만 (지시문 5절). V열은 4절 질문과 같이 보냄. RAVENPACK 등은 DS-3 (Stage 3 통과 뒤) |
| 공급사 무응답 | 0칸 (아직 문의를 보내지 않음) | 문의 후 2주 무응답이면 이 표시로 바꿈 (제안) |

## 3. 엑셀 값과 다른 자료 (옆에 나란히)

엑셀 값은 그대로 둡니다. 확인 날짜는 모두 2026-11-17 (D14는 메인이 같은 날 검색, "이 세션"은 이 문서 작성 중 검색). 공급사 호스트는 직접 열 수 없어 검색 요약 기준입니다.

| 소스 | 엑셀 값 | 다른 자료 | 판단 | 출처 (확인 날짜) |
|---|---|---|---|---|
| CME FedWatch | "종가판 월 $25·장중판 60초 갱신·2015년부터" (행CME, Q4) | 장중 API 문서: 과거 데이터 **2025-11-01부터**. 2015년 이력은 종가판으로 보임. $25/월은 CME 공식 페이지로 확인 안 됨, 제3자에 구간제 (0~1,000건 $25, 1,001~50,000건 $75) | **일부 다름.** 2015년 이력 = 종가판, 장중판 이력 = 2025-11부터. 가격 **미검증** | D14 4절: cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/1054343170/CME+FedWatch+Intraday+API , findmymoat.com/vs/cme-fedwatch-vs-financialdata-net (2026-11-17) |
| Cryptopanic | "무료 플랜 초당 5건" (행CP, M4) | D14: 제3자 SDK 글에 무료 Developer 플랜 "중단" 표시. 이 세션 검색: 공식 API 페이지 요약에 "Free API" 5 req/sec, "Free + Pro Membership" (메타데이터 포함), Enterprise 10 req/sec. 페이지 날짜 없음 | **다를 수 있음.** 공식 페이지 요약은 엑셀과 같음. 지금도 가입되는지는 DS-4b 무료 키 가입 때 확인 | cryptopanic.com/developers/api/about (이 세션 검색 2026-11-17), dev.to/tigusigalpa/stop-fighting-the-cryptopanic-api-meet-cryptopanic-php-the-modern-php-sdk-1il2 (D14) |
| GDELT | "이벤트 1979년·GKG 2013년 4월부터", "15분마다" (행GDELT, P4) | GKG 1.0 = 2013-04-01부터 일별, **GKG 2.0 = 2015-02부터** 15분. Notion DIDM은 "GKG 2.0 from 2015" | **둘 다 맞음 (판이 다름).** 15분 논조는 2015-02부터. DIDM 구간 (2015~)에 지장 없음 | blog.gdeltproject.org/introducing-gkg-2-0-the-next-generation-of-the-gdelt-global-knowledge-graph/ (D14) |
| GDELT 약관 | V4 "전체 데이터를 원본 파일로 공개" | 공식 About 요약: 학술·상업·정부 용도 무료, "unlimited and unrestricted use", 재배포·재호스팅 허용, **인용과 링크 필수**. GDELT Cloud는 별도 회사·약관, 기사 원문은 언론사 권리 | 일치. 단 V "원문 저장·학습"의 원문 = GDELT 파일(URL·메타데이터)이지 기사 본문이 아님 | gdeltproject.org/about.html (이 세션 검색 2026-11-17), gdeltcloud.com/terms |
| Trading Economics | "유료이며 가격은 공개 페이지에서 확인 못함" (행TE) | 제3자: Standard $149/월, Professional $299/월 (연간), 다른 리뷰 $199/월부터. 하위 요금제에 캘린더가 없을 수 있음 | 엑셀 판단 유지. 제3자 값 **미검증**. 컨센서스가 상위 요금제에만 있을 수 있음 → T열 O는 요금제 조건부 | businessquant.com/resources/best-macroeconomic-data-providers , tradingtoolshub.com/review/tradingeconomics/ (D14) |
| Polymarket | "선거·연준 결정 등 … 무료·실시간" (행Poly, U4) | **방송통신심의위원회 2026-08-18 국내 접속 차단 결정** (보도) | 엑셀에 없는 위험. 한국에서 API 이용 가능·적법 여부 **미검증**. 실행 보류 (질문 4) | koreatimes.co.kr/business/companies/20260819/korea-moves-to-block-polymarket-over-illegal-gambling , cointelegraph.com/news/south-korea-block-polymarket-gambling-concerns (D14) |
| Kalshi (U4 메모의 같은 유형) | U4 "Kalshi도 같은 유형" (대안 9개에는 없음) | 공식 빠른 시작 문서 요약: 시세 조회 공개 엔드포인트는 **API 키 없이** 사용 (`external-api.kalshi.com/trade-api/v2`), 실시간 웹소켓은 인증 필요. 약관·한국 이용 가능 여부는 못 찾음 | 기술적으로 키 없이 조회 가능 (검색 요약). 약관·적법성 **미검증** | docs.kalshi.com/getting_started/quick_start_market_data , dwellir.com/guides/kalshi-api-guide (이 세션 검색 2026-11-17) |
| Alpha Vantage | O4 "관련성 필드가 있는지 공개 문서에서 확인 못함" | 이 세션 검색: 공식 문서는 못 열었고, 제3자 응답 예시에 종목별 `relevance_score` (0~1, 문자열), `ticker_sentiment_score`, `ticker_sentiment_label`, 구간 경계 ±0.35 | 엑셀 ? 유지. 제3자 예시상 필드가 있을 가능성이 큼 → DS-4b 1회 호출로 확인 | alphavantage.co/documentation/#news-sentiment (열지 못함), cdn.jsdelivr.net/npm/@saibolla/ada@0.1.3/skills/alpha-vantage/references/intelligence.md , glama.ai/mcp/servers/@ross-jill-ws/alphavantage (이 세션 검색 2026-11-17) |
| Alpha Vantage 가격 | "무료 하루 25건·유료 월 $49.99부터" (행AV) | 공식 premium 페이지 요약: 무료 하루 25건, 제3자 사본 최저 $49.99 | 일치 (원문 직접 확인 못함) | alphavantage.co/premium , macroption.com/alpha-vantage-api-limits/ (D14) |
| Tiingo | "월 $30(개인)·$50(사업자) … 과거 3개월 초과·재배포는 엔터프라이즈 없이 못함" (행Tiingo), M4 "무료 플랜" | 공식 문서 요약: "all accounts are free", 높은 한도·상업 용도는 Power/Commercial로. 제3자: 무료 Starter (월 500 종목, 시간당 50건). 뉴스 API가 무료에 들어가는지, Power 가격은 못 찾음. 뉴스 페이지: 1990년대부터 과거 뉴스는 기관용 1년 약정 | 가격 **미검증**. 무료 플랜의 뉴스 포함 여부 **미검증** (DS-4b) | api.tiingo.com/documentation , findmymoat.com/free/data-partners/tiingo , api.tiingo.com/products/news-api (이 세션 검색 2026-11-17) |
| FRED/ALFRED | "공식 통계와 발표 시점별 수정 이력(ALFRED)을 무료 제공" (행FRED) | API 키 무료, 분당 120건 (제3자), 일부 시리즈는 제3자 저작권 (예: 저장소 `data/backlog_registry.json`의 ICE 시리즈) | 일치. 상업 조건은 시리즈별 | fred.stlouisfed.org/docs/api/fred/fred_vs_alfred.html (D14) |

2절 표 안에서 메인 분석 (D14 3절)과 다르게 읽힐 수 있는 칸:

| 칸 | 2절 값 (엑셀 메모 그대로) | D14·공개 자료 | 처리 |
|---|---|---|---|
| Q / Polymarket | X·Q4 (Q4 메모는 CME만) | D14 3절은 Polymarket·Kalshi 연준 결정 시장을 FOMC 확률의 **보조**로 봄 | 엑셀 값 유지. Polymarket의 연준 결정 시장은 U열 (U4)로 셈 |
| U / CME | X·U4 (U4 메모는 Polymarket만) | FedWatch는 FOMC라는 예정 사건의 결과 확률이기도 함 | 엑셀 값 유지. Q열로 셈 |
| K / Alpha Vantage | X·K4 (K4 메모는 CME·FRED·Polymarket·TE만) | R4가 Alpha Vantage 거시 지표 (연방기금금리·CPI 등)를 적음 | 엑셀 값 유지. R열 O로 셈 |
| R / Trad. Econ | ?·R4 (R4 메모에 없음) | 행TE "경제지표 발표치·이전치" | 공급사 문의 (요금제별 이력 포함 여부) |

## 4. 소스별 약관 질문 (법률 자문이 아닙니다)

**법률 자문이 아닙니다.** 칸은 답이 아니라 확인할 질문입니다. 지금 아는 것은 3절과 D14 8절 (2026-11-17 검색 요약).

| 소스 | 저장 (받은 자료를 우리 PC·서버에 둬도 되나) | 재배포 (다른 사람에게 보여 주거나 넘겨도 되나) | 상업 이용 (법인·유료 앱에서) | 출처 표시 (어디에 어떻게) | 지금 아는 것 |
|---|---|---|---|---|---|
| CME FedWatch | 이력 저장 허용 범위? (종가판·장중판 따로) | 앱 화면 표시 = 별도 시세 라이선스? | 사업자 요금제·라이선스 필요 여부? | 필요 문구? | 계정·권한 부여 필요 (CME 문서, D14). 가격 미검증 |
| FRED / ALFRED | 빈티지 저장은 API 약관상 허용? | 시리즈별 제3자 저작권 (허락 필요 시리즈 목록)? | 앱마다 키 따로, 상업 약관 조건? | FRED 고지 문구 위치? | 키 무료. 일부 시리즈 제3자 소유 |
| Polymarket | 가격 이력 저장 허용? | 표시·재사용 허용 범위? | **한국 거주자 이용 자체의 적법성** (2026-08-18 차단 결정) | 필요 문구? | 실행 보류 (변호사 확인 전) |
| Trading Economics | 요금제별 저장 허용? | 재배포 = Enterprise? | 요금제별 컨센서스 포함, 상업 조건? | 필요 문구? | 견적. 제3자 값만 있음 |
| GDELT | 허용 (공식 About 요약) | 허용 (재배포·재호스팅) | 허용 (상업 용도 무료) | **인용 + gdeltproject.org 링크 필수**. 앱·문서 어디에 둘지 정해야 함 | 기사 본문은 언론사 저작물 → 본문 저장은 별도 질문 |
| Alpha Vantage | 뉴스·감성 저장 허용? | 재배포 허용? | 무료 키의 상업 이용 금지 여부, 유료 요금제 조건? | 필요 문구? | 엑셀: "상업 이용 조건과 과거 뉴스 깊이는 확인 못함" |
| Tiingo | 개인 요금제로 연구용 저장 허용? 3개월 초과 보관? | 엔터프라이즈 없이 불가 (엑셀) | 개인 $30 요금제의 사업 이용 금지 범위? | 필요 문구? | 엑셀: 개인 $30·사업자 $50 |
| Cryptopanic | 뉴스·투표 저장 허용? | 재배포 허용? | 상업 = Enterprise? | 무료 API는 뉴스 피드 위쪽에 출처 표시 필요 (공식 페이지, D14) | 무료 플랜 존재 확인 필요 |
| 자체 NLP (LLM 공급사) | 입력 기사 보관 (공급사 쪽)? | 출력 점수 사용 권리? | 상업 약관 | — | 입력 기사의 권리는 위 각 소스의 문제 |
| Kalshi (참고) | ? | ? | 한국 이용 가능 여부? | ? | 키 없이 시세 조회 가능 (검색 요약) |
| 한국 법 (공통) | — | 신호를 외부에 보이면 투자자문·유사투자자문 신고가 필요한가? | 같음 | — | DIDM 8.3: 법률 의견 전까지 DIDM 출력은 내부용 |

공통 원칙 (DIDM 8.3, 지시문 5절): 네이버·다음 스크래핑 금지, 소셜 원문 재배포 금지, 약관상 필요하면 파생 특징만 저장, 공급사 점수와 DIDM 출력은 내부용, 공급사의 독점 분류표·값을 저장소에 복사하지 않음 (필드 이름은 공개 문서에서만).

## 5. 키 이름 (값 없음)

값은 소유자 PC에만 둡니다 (채팅·저장소·로그 금지). KEY-2 (결제·계정 세션) 병합 전에는 환경변수 **이름**만, 병합 뒤에는 `core/credentials`. `.env.example`에 더하는 일은 공유 파일이라 대기열을 거쳐 한 PR로 모읍니다.

| 소스 | 키 이름 | 지금 필요? | 비고 |
|---|---|---|---|
| CME FedWatch | `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET` | 아니요 (Stage 2 + 질문 2 답 뒤) | 인증 방식 **미검증**. 제안 이름 |
| FRED / ALFRED | `FRED_API_KEY` | 선택 (없으면 수동 다운로드 파일을 읽는 길) | 그래프 CSV는 키 없이 이미 앱에 있음 (`config.py`) |
| Polymarket | 없음 (조회만) | 아니요 (질문 4) | 실행 보류 |
| Trading Economics | `TRADINGECONOMICS_API_KEY` | 아니요 (Stage 3 뒤 견적) | 제안 이름 |
| GDELT | 없음 | 아니요 | 원본 파일, 키 없음 |
| Alpha Vantage | `ALPHAVANTAGE_API_KEY` | DS-4b (무료 키) | 제안 이름 |
| Tiingo | `TIINGO_API_KEY` | DS-4b (무료 키) | 제안 이름 |
| Cryptopanic | `CRYPTOPANIC_API_KEY` | DS-4b (무료 키) | 제안 이름 |
| 자체 NLP | `ANTHROPIC_API_KEY` (기존) | 유료 호출은 질문 2 답 뒤 | 이미 `.env.example`에 있음 |

## 6. 참고 열 (대안이 아님, Stage 3 뒤 기준선)

메인 초안 (handoff `MASTER_WORK_DESIGN_2026-11-17.md` 부록 D, 2026-11-17)의 공급사 비교를 **참고로만** 둡니다. D14 결정으로 Bigdata.com 시험 (DS-2)은 없고, RavenPack 견적 (DS-3)은 DIDM Stage 3 통과 뒤입니다. 이 열의 값은 메인 초안 그대로이며 이 세션이 다시 확인하지 않았습니다 (**미검증**).

| 공급원 | 정보 | 기록 시작 | 점수 | 비용 | 이 계획에서 |
|---|---|---|---|---|---|
| RavenPack RPA 1.0 / Edge | 뉴스·공시·통화록의 종목별 사건 | DJ판 2000, Web판 2007 | ESS 0~100 (50 중립), 관련도 0~100, 새로움 ENS, 사건 분류 | 견적만 | Stage 3 뒤 견적·기준선. 점수 **이름**만 DIDM-1에서 따름 |
| Bigdata.com | 뉴스·통화록·공시 검색, 종목 일별 감성 | 미검증 | 문단 -1~+1 | Pro $40/월 (검색 요약) | Stage 3 뒤 기준선. 시험 없음 |
| LSEG MarketPsych | 뉴스·소셜 감성 지수 | 1998 | 지수 | 견적 | Stage 3 뒤 후보 |
| Bloomberg EDF | 기사별 종목 감성 | 2007 | -1/0/+1 + 확신도 | 견적 | 해당 없음 (과함) |
| Dow Jones Factiva | 뉴스 원문 | 매우 김 | 없음 | 견적 | 해당 없음 |
| EODHD / FMP 뉴스 | 뉴스 + 일별 감성 | 미검증 | -1~1 | $19.99/월~ | 해당 없음 (엑셀 밖) |
| BigKinds | 한국 뉴스 | 2016 | 키워드·주제 | 무료 | 해당 없음 (엑셀 밖, 약관 검토 필요) |

엑셀 밖 무료 공식 소스 — **질문 3 답 전까지 "제외"**:

| 소스 | 채우는 것 | 상태 |
|---|---|---|
| SEC EDGAR | 미국 공시 (사건 원천, 정확한 접수 시각) | 제외 (질문 3 대기). 쓰게 되면 초당 10회 이하, User-Agent에 일반 연락처 |
| OpenDART / KIND | 한국 공시. 저장소에 `data/krx/opendart_client.py` 있음 | 제외 (질문 3 대기). 한국 종목은 이것 없이 비어 있음 |
| ECOS (한국은행) | 한국 공식 통계 | 제외 (질문 3 대기) |

## 7. 대조 검사

```
python -m tools.didm.check_vendor_eval --excel <handoff의 plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt>
```

2026-11-17 실행 결과 (작업 브랜치 `claude/data-source-didm-20261117`):

```
columns 19, alternative cells 171, '?' cells 15, excel compared: yes
excel cells changed: 0
OK
```

- 엑셀 두 줄 38칸이 1·2절과 같고 (바뀐 칸 0), 2절 171칸 (대안 쪽 ? 15칸)이 모두 `O|X|?·근거` 꼴이며, ? 칸마다 처리 방법이 하나 있고, 엑셀 값과 모순 0건입니다.
- 같은 검사가 `tests/didm_vendor_eval_acceptance.py`에 있습니다 (네트워크 없음; 엑셀 값은 스크립트 안의 사본으로 비교).

## 8. 소유자 확인 (완료 조건 4)

1. 2절처럼 엑셀 메모를 대안별로 나눈 방식 (특히 자체 NLP를 "제공"으로 세지 않는 `N4규칙`, 3절 끝의 Q/U/K 칸)이 뜻하신 것과 맞습니까?
2. "?" 칸 처리 (무료 키 1회 호출 6칸, 공급사 문의 11칸)를 이대로 진행해도 됩니까? 문의 발송과 무료 키 가입은 소유자가 합니다.
3. (지시문 질문 1~4는 메인이 여쭙니다. 답이 오면 이 문서의 6절 "제외"와 5절 "지금 필요?"를 고칩니다.)

## 9. 출처

- 소유자 엑셀 글 사본: handoff `plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt` (2026-11-17).
- 메인 분석: handoff `plans/2026-11-17/D14_RAVENPACK_ALTERNATIVES.md` 2·3·4·7·8·13절, `MASTER_WORK_DESIGN_2026-11-17.md` 부록 D (2026-11-17).
- 이 세션 검색 (2026-11-17, 검색 요약; 공급사 호스트는 직접 열기 막힘): Alpha Vantage NEWS_SENTIMENT 필드 (제3자 사본), Cryptopanic API 플랜 (공식 페이지 요약), Tiingo 무료 계정 (공식 문서 요약·제3자), Kalshi 공개 시세 (공식 빠른 시작 요약), GDELT 약관 (공식 About 요약). URL은 3절 표에.
