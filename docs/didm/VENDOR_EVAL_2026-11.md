# DS-1 RavenPack 대안 평가표 (소유자 엑셀 기준, 2026-11)

- 작성: DATA_SOURCE_DIDM 세션 (QUANTGEN/MAIN 하부), 2026-11-17. 갱신 2026-11-18 (소유자 답 반영). 상태: **초안, 소유자 확인 대기 (8절).**
- 근거: 소유자 답 "5. D14 : Ravenpack의 대안책 3단계 (엑셀 파일 참고)의 자료들로 구성할 예정." (2026-11-17). 1차 자료는 소유자 엑셀 (원본 2026-11-18 업로드, 글 사본 handoff `plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt`)과 소유자 문서 "TRADEGEN MTFE — RavenPack 검토와 대체 데이터 공급원" (2026-11-11, 2026-11-18 업로드, 사본 handoff `plans/2026-11-18/OWNER_MTFE_RAVENPACK_REVIEW_2026-11-11.md`). 메인 분석은 handoff `plans/2026-11-17/D14_RAVENPACK_ALTERNATIVES.md`.
- **엑셀 값은 고치지 않습니다.** 공개 자료나 메인 분석이 다르면 옆 칸에 나란히 적습니다.
- **법률 자문이 아닙니다.** 약관·법규 칸은 확인할 질문입니다. 상업 이용 전에는 각 약관 원문과 변호사 의견으로 정합니다.
- 표시: O 제공 · X 제공 안 함 · ? 공개 자료로 확인 못함 (엑셀 범례와 같음). **미검증** = 원문을 직접 확인하지 못한 값.

## 0. 요약

| 항목 | 내용 |
|---|---|
| 엑셀 구조 | 시트 1개. O/X/? 줄은 **두 줄**뿐: "RAVENPACK 등" (기관용 또는 Bigdata.com 중 하나라도 제공하면 O)과 "대안책" (9개 대안 중 하나라도 제공하면 O). 대안별 O/X/?는 엑셀에 없고, 칸 메모 (F4~X4)와 대안별 설명 (D열)에 근거가 있습니다. |
| 이 문서가 한 일 | ① 두 줄 19칸을 그대로 옮김 (1절) ② 엑셀 메모·설명만으로 **대안 9개 × 19칸**을 풀어 적음 (2절, 칸마다 근거 기호) ③ 공개 자료·메인 분석과 다른 값을 옆에 (3절) ④ 소스별 약관 질문 (4절) ⑤ 키 이름 (5절) ⑥ 참고 열 (6절) |
| 대조 결과 | `python -m tools.didm.check_vendor_eval --excel <엑셀 사본>`: 엑셀 값이 바뀐 칸 **0개**, 2절 표가 엑셀 두 줄과 모순 0건 (7절). 2026-11-18 업로드된 엑셀 원본도 3·4행 38칸과 칸 메모 38개가 글 사본과 같음 (openpyxl, `-I`로 읽음). |
| "?" 칸 | 대안 쪽 14칸 + RavenPack 쪽 2칸. 소유자 답 2 (2026-11-18): **별도 처리 안 함.** Alpha Vantage 관련성 칸은 X로 확정. |
| 소유자 확정 열 | 엑셀 값과 다른 소유자 확정 3칸: 신규성 N = O, 영향 분석 W = O (자체 NLP가 직접 구현), 자산별 관련성 O = X. 엑셀 열 자체는 그대로 |
| 공개 자료 확인 | 이 세션 네트워크에서 `www.alphavantage.co`, `api.tiingo.com`, `cryptopanic.com`, `www.cmegroup.com`, `www.gdeltproject.org`, `fred.stlouisfed.org`, `docs.kalshi.com`, `data.gdeltproject.org`가 모두 막혀 (2026-11-17 22:00 KST, 프록시 거절), **검색 요약 기준**입니다. 원문 직접 확인은 미검증. |

## 0.1 소유자 답 (2026-11-18, 원문 그대로)

> 1. 아뇨, 위 두 파일에서 나온 RavenPack 외 대안책으로 사용 가능한 데이터 공급원 9개를 의미하는 겁니다.
> 2. 네 가능합니다
> 3. 네 진행하세요. 진행하고 나서 만약 QUANTGEN 앱 내부 아키텍처 혹은 단순한 코드/파일을 바꿔야하는 부분이 있다면 저한테 알려주세요.
> 4. 네 Kalshi로 진행하겠습니다.

| 질문 | 답 | 이 문서에 반영 |
|---|---|---|
| 1. "3단계" = DIDM Stage 3? | **아님.** 두 파일 (엑셀, MTFE 문서)의 대안 공급원 9개. MTFE 문서는 이 9개를 세 층으로 나눔: 1층 시장가격·공식 통계 (CME FedWatch, FRED/ALFRED), 2층 사건 확률·발표 충격 (Polymarket·Kalshi, Trading Economics), 3층 뉴스 텍스트 (GDELT, Alpha Vantage, Tiingo, CryptoPanic, 자체 NLP) | 2절의 9개가 그 9개. "Stage 3 뒤"라고 쓴 곳은 DIDM 자체 규칙 (Notion 8.2 "업그레이드는 Stage 3 뒤")으로만 남기고, 소유자 말의 뜻으로 쓰지 않음 |
| 2. 비용 단계 | 승인: 지금 무료 + LLM 최소안 (월 약 $4~11), CME 종가판은 Stage 2, Alpha Vantage·Tiingo 유료는 그 뒤 | 5절. 유료 호출은 아직 0 |
| 3. EDGAR·OpenDART/KIND·ECOS 추가 | 승인 | 6절 "추가". 커넥터 커밋. KIND는 공개 API가 없어 OpenDART로 대신 (6절) |
| 4. Polymarket 보류, Kalshi | **Kalshi로 진행** | 2절의 "Polymarket" 열 이름은 엑셀 그대로 두고, 그 자리를 실제로 채우는 공급원은 Kalshi (엑셀 U4 메모 "Kalshi도 같은 유형"). Polymarket 커넥터는 꺼진 채 유지 |

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

읽는 법: 칸 = `값·근거`. "Polymarket" 열은 엑셀 이름 그대로이고, 소유자 답 4 (2026-11-18)로 이 자리의 실제 공급원은 **Kalshi**입니다 (엑셀 U4 메모의 "같은 유형"). 값은 엑셀 메모 기준이라 바꾸지 않았습니다. 이 표의 값은 **엑셀의 대안별 값이 아니라** (엑셀에는 대안별 값이 없음) 엑셀 메모와 설명을 대안별로 나눈 것입니다. 엑셀 두 줄은 3·4번째 열에 그대로 두었고, 7절 스크립트가 서로 모순이 없는지 봅니다 (엑셀 O → 대안 하나 이상 O, X → 모두 X, ? → O 없이 ? 하나 이상).

근거 기호:
- `F4`~`X4`: 엑셀 대안책 행의 그 열 칸 메모 (1절). 메모에 이름이 있으면 O, 메모가 "없음"이라 하거나 이름이 없으면 X, 메모가 "확인 못함"이라 하면 ?.
- `행CME`, `행FRED`, `행Poly`, `행TE`, `행Tiingo`, `행CP`, `행NLP`: 엑셀 "대안" 블록의 그 소스 설명 (D열). 예: 행FRED "뉴스·컨센서스 전망치·사건 해석은 못함", 행TE "유료", 행CME "종가판 월 $25", 행Tiingo "감성 점수는 반환 필드에 없음 … 재배포는 엔터프라이즈 없이 못함", 행CP "실시간 제공", 행NLP "비용은 LLM 호출료".
- `D1`: 소유자 답 1 (2026-11-18) "직접 구현이 필연적이므로, 표기를 X 대신 O로 해주세요". 자체 NLP가 직접 계산하는 칸 (감성 G, 엔티티 H, 거시 사건 탐지 K, 신규성 N, 영향 분석 W, 암호화폐 감성 X)을 O로 둡니다. 수집 F와 실시간 J는 자체 NLP가 하는 일이 아니라 (입력은 다른 공급원) X·`행NLP` 그대로입니다.
- `D2`: 소유자 답 2 (2026-11-18) "대안책의 자산별관련성점수의 경우 X로 확정". Alpha Vantage 관련성 칸과 자체 NLP 관련성 칸을 X로 둡니다 (DIDM 안의 `relevance_0_100`은 계속 계산하지만, 이 표에서는 "대안이 주는 점수"로 세지 않음).
- "대안책 (소유자 확정)" 열: `=`는 엑셀과 같음. 다른 칸 (N, O, W)은 소유자 답이고, 2절 대안 칸은 이 확정 값과 모순이 없어야 합니다 (7절 검사).

<!-- matrix:begin -->
| 열 | 정보 유형 | RAVENPACK 등 (엑셀) | 대안책 (엑셀) | 대안책 (소유자 확정) | CME | FRED | Polymarket | Trad. Econ | GDELT | Alpha Vantage | Tiingo | Cryptopanic | 자체 NLP | "?" 처리 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F | 뉴스 기사 수집 | O | O | = | X·행CME | X·행FRED | X·행Poly | X·행TE | O·F4 | O·F4 | O·F4 | O·F4 | X·행NLP | — |
| G | 뉴스 감성 점수 | O | O | = | X·행CME | X·행FRED | X·행Poly | X·행TE | O·G4 | O·G4 | X·G4 | O·G4 | O·D1 | — |
| H | 엔티티·티커 태깅 | O | O | = | X·행CME | X·행FRED | X·행Poly | X·행TE | O·H4 | O·H4 | O·H4 | ?·H4 | O·D1 | Cryptopanic: 처리 안 함 (소유자 답 2) |
| I | 사건·토픽 분류 | O | O | = | X·행CME | X·행FRED | X·행Poly | X·행TE | O·I4 | O·I4 | ?·I4 | ?·I4 | O·I4 | Tiingo: 처리 안 함 (소유자 답 2); Cryptopanic: 처리 안 함 (소유자 답 2) |
| J | 분 단위 이내 실시간 갱신 | O | O | = | O·J4 | X·J4 | O·J4 | ?·J4 | O·J4 | ?·J4 | O·J4 | O·행CP | X·행NLP | Trad. Econ: 처리 안 함 (소유자 답 2); Alpha Vantage: 처리 안 함 (소유자 답 2) |
| K | 미국 거시 이벤트 감시 | O | O | = | O·K4 | O·K4 | O·K4 | O·K4 | X·K4 | X·K4 | X·K4 | X·K4 | O·D1 | — |
| L | Python에서 API 호출 | O | O | = | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | O·L4 | — |
| M | 무료 플랜 | O | O | = | X·행CME | O·M4 | O·M4 | X·행TE | O·M4 | O·M4 | O·M4 | O·M4 | X·행NLP | — |
| N | 신규성 점수 | O | X | O | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | X·N4 | O·D1 | — |
| O | 자산별 관련성 점수 | O | ? | X | X·O4 | X·O4 | X·O4 | X·O4 | X·O4 | X·D2 | X·행Tiingo | X·O4 | X·D2 | — |
| P | 2000년부터의 뉴스 점수 이력 | O | X | = | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | X·P4 | — |
| Q | 시장 내재 금리 확률 (FOMC) | X | O | = | O·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | X·Q4 | — |
| R | 공식 경제 통계 시계열 | X | O | = | X·R4 | O·R4 | X·R4 | ?·R4 | X·R4 | O·R4 | X·R4 | X·R4 | X·R4 | Trad. Econ: 처리 안 함 (소유자 답 2) |
| S | 발표 시점별 수정 이력 | X | O | = | X·S4 | O·S4 | X·S4 | ?·S4 | X·S4 | ?·S4 | X·S4 | X·S4 | X·S4 | Trad. Econ: 처리 안 함 (소유자 답 2); Alpha Vantage: 처리 안 함 (소유자 답 2) |
| T | 발표치·컨센서스 수치 | X | O | = | X·T4 | X·행FRED | X·T4 | O·T4 | X·T4 | X·T4 | X·T4 | X·T4 | X·T4 | — |
| U | 예정 사건 결과 확률 | X | O | = | X·U4 | X·U4 | O·U4 | X·U4 | X·U4 | X·U4 | X·U4 | X·U4 | X·U4 | — |
| V | 원문 저장·학습 허용 | X | O | = | ?·V4 | ?·V4 | ?·V4 | ?·V4 | O·V4 | ?·V4 | X·행Tiingo | ?·V4 | X·행NLP | CME: 처리 안 함 (소유자 답 2); FRED: 처리 안 함 (소유자 답 2); Polymarket: 처리 안 함 (소유자 답 2); Trad. Econ: 처리 안 함 (소유자 답 2); Alpha Vantage: 처리 안 함 (소유자 답 2); Cryptopanic: 처리 안 함 (소유자 답 2) |
| W | 자산 영향 분석 (Impact Analytics) | ? | X | O | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | X·W4 | O·D1 | RAVENPACK 등: 처리 안 함 (소유자 답 2) |
| X | 암호화폐 뉴스 감성 | ? | O | = | X·X4 | X·X4 | X·X4 | X·X4 | X·X4 | O·X4 | X·X4 | O·X4 | O·D1 | RAVENPACK 등: 처리 안 함 (소유자 답 2) |
<!-- matrix:end -->

"?" 16칸 (대안 14 + RavenPack 2)의 처리 — 소유자 답 2 (2026-11-18) "?에 대해서 별도 처리할 필요는 없으나": **처리 안 함.** 아래 표는 답 전의 계획으로, 기록으로만 남깁니다.

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

소유자 MTFE 문서 (2026-11-11, 소유자가 그날 직접 연 페이지 기준)가 엑셀·D14와 다르거나 더 자세한 값 (엑셀은 그대로 두고 옆에 적음):

| 소스 | 엑셀 | MTFE 문서 | 이 문서의 처리 |
|---|---|---|---|
| Kalshi | U4 "Kalshi도 같은 유형" | 과거 데이터 **2021년부터**, 공개 API 무료·실시간. 두 거래소 같은 사건 짝짓기는 직접 구현. 유동성 얇은 시장은 잡음 → 거래량 하한 | Kalshi 연결 (`data/didm/kalshi.py`), 거래량 하한 1,000 (사전등록 제안) |
| Alpha Vantage | 유료 월 $49.99부터 | 유료 **$49.99~249.99**, 분당 75~1,200건 | 일치 (범위가 더 자세함) |
| Tiingo | 과거 3개월 초과는 엔터프라이즈 | 과거 3개월, **엔터프라이즈는 1995년부터**. 반환 필드 = 제목·설명·태그·티커·발행일. **라이선스는 내부 이용 한정** | Tiingo I열 "?"는 "태그" 필드가 있다는 MTFE 기술로 O 가능성이 큼 → DS-4b 1회 호출로 확정 (엑셀 값은 그대로) |
| CryptoPanic | 무료 플랜 초당 5건 | 무료 플랜 있음, 실시간 초당 5건 | 일치. D14의 "무료 플랜 중단 가능성"은 근거 약함 |
| GDELT | 15분, GKG 2013-04~ | 검색용 DOC API는 최근 3개월·5초당 1회 (제3자) → 과거는 원본 파일·BigQuery | 원본 파일 방식으로 이미 구현 (DS-4a) |
| CME FedWatch | 종가판 월 $25 | 1,000건 초과 시 월 $75 (제3자), 선물 시세로 직접 계산 가능 | Stage 2에서 가입 화면 가격 확인. 직접 계산 길은 미검토 |
| 미국 거시 이벤트 감시 (K) | CME·FRED·Polymarket·TE | 금리 기대·달러·위험선호·예상 대비 충격·예정 사건 확률은 **뉴스 없이 숫자로**, 뉴스가 꼭 필요한 것은 **예고 없는 사건** 하나 | 사전등록 2절 사건 유형에 그대로 맞음 (전쟁·지정학, 무역·관세 등이 뉴스 몫) |

### 3.1 소유자 PC 첫 실행 (2026-11-18, `tools/didm/collect_daily.py`, 출력 원문 요약)

| 소스 | 결과 | 확인된 것 | 남은 것 |
|---|---|---|---|
| ALFRED (`FRED_API_KEY`) | CPIAUCSL 빈티지 3,364행 저장 | 키로 빈티지 수집이 됨 (S열 FRED O 확인) | — |
| SEC EDGAR (`SEC_EDGAR_USER_AGENT`) | CIK 320193 공시 147건 (8-K·6-K·10-Q·10-K) | 연락처 헤더로 수집이 됨 | — |
| Kalshi (키 없음) | KXFED 시장 200개 저장, 그러나 가격 없음·`liquid 0` | **한국 PC에서 키 없이 조회가 됨** (3절 "키 없이 조회 가능" 확인). 응답 필드가 현재 형식 (`yes_bid_dollars`, `volume_fp`)이라 옛 이름만 읽던 파서가 값을 못 읽음 → 파서 고침 (`kalshi-v0.2`), 첫 200행은 `parser` 없는 기록으로 남음 (추가 전용 저장소) | 다시 실행해 가격·거래량 확인, 200개는 한 쪽만 (다음 쪽 따라가기 추가) |
| GDELT (키 없음) | `HTTPError` | — | 어느 단계·몇 번 오류인지 출력하게 고침 → 다시 실행 |
| ECOS (`ECOS_API_KEY`) | 722Y001 관측치 0건 (오류는 아님) | 키는 통함 (잘못된 키면 오류가 남) | 통계표 코드가 기준금리가 맞는지 공개 자료끼리 다름 (722Y001 vs 060Y001) → `--ecos-items`로 항목·주기 확인 |
| OpenDART | `DARTUnavailable` | — | 새 폴더 (worktree)에는 `.env`가 없어 키가 없음. `setx OPENDART_API_KEY` 뒤 다시 실행 |

둘째 실행 (2026-11-18, 커밋 `23bb47c`):

| 소스 | 결과 | 판단 |
|---|---|---|
| Kalshi | KXFED 2쪽 (끝까지), 시장 236개, 가격 있음 236, 거래량 없음 0, 유동 (≥ 1,000) 80 | **해결.** 파서 `kalshi-v0.2` 정상 |
| ECOS 항목 조회 | `722Y001` 항목 `0101000` = **한국은행 기준금리** (주기 D 19990506~20261116, M 199905~202610, Q, A). `060Y001` = 데이터 없음 | 공개 자료끼리 달랐던 통계표 코드 확정: `722Y001` (현재 코드), `060Y001`은 옛 코드로 보임 |
| ECOS 시계열 | `722Y001/M/202401/202610/0101000`: INFO-200 "해당하는 데이터가 없습니다" | 항목·기간이 있는데도 0건 → 요청 형식 문제로 봄. `--ecos-probe`로 변형 4가지 (요청 건수 1000·100, 항목 코드 없음, 끝 '/') 비교 예정 |
| GDELT | 최신 목록에 있는 `20261118153000.export.CSV.zip`이 HTTP 404 | 목록에는 올라왔지만 파일이 아직 게시 전 (시간차). 404면 직전 두 칸 (30분)을 받게 고침. 또 하루치 96칸을 받는 `--gdelt-day` 추가 (기존은 실행 때마다 15분 한 칸만 받았음) |

셋째 실행 (2026-11-18, 커밋 `5fadc20`):

| 소스 | 결과 | 판단 |
|---|---|---|
| GDELT 최신 칸 | 2파일 (`20261118161500` 사건·GKG), 3,090행 | **해결** (앞선 404는 게시 전 시간차) |
| GDELT 하루치 (`--gdelt-day 20261117`, 사건만) | 96파일, 빠짐 0, 127,432행 | **해결.** 하루 전체 수집 가능 |
| ECOS | 항목 코드 없이 306행 받음. 항목 코드를 넣은 요청 경로가 `.../101000`으로 찍힘 | **원인 = PowerShell.** 따옴표 없는 쉼표 인자를 배열·숫자로 읽어 `0101000`의 앞자리 0을 지움. 요청 형식은 정상. 수집기가 6자리 숫자 항목 코드를 거부하고 따옴표를 쓰라고 안내하게 고침 |

넷째 실행 (2026-11-18, 커밋 `a790ce8`): ECOS `"722Y001,M,202401,202610,0101000"` (따옴표) → 기준금리 월별 34개월 저장 (**해결**). OpenDART `DARTUnavailable` (worktree 폴더에 `.env`가 없어 키 없음) → 앱 폴더의 `.env`를 읽는 `--env-file` 추가.

다섯째 실행 (2026-11-19, `--env-file ..\QUANTGEN\.env`): OpenDART 20261117~20261118 전체 공시 목록 9쪽, 819건 저장 (**해결**). 이로써 키 없는/무료 공식 공급원 6곳 (GDELT, ALFRED, SEC EDGAR, Kalshi, ECOS, OpenDART) 모두 소유자 PC에서 수집 확인. 남은 확인: 무료 키 3곳 (Alpha Vantage, Tiingo, CryptoPanic).

CryptoPanic 무료 플랜 (2026-11-20, 소유자 지적 확인; 검색 요약, 호스트는 이 세션에서 막힘):

| 엑셀 | 공개 자료 | 판단 |
|---|---|---|
| 행CP·M4 "무료 플랜 초당 5건" | 공식 API 요금 페이지 (cryptopanic.com/developers/api/plans, 2026-09 사본 기준): **유료만** — Growth (주간) $50/주 (600건/주), Growth $199/월 (연 결제 $179/월, 3,000건/월), Enterprise $899/월부터. 2026 리뷰: 무료 Developer API는 **2026-04-01 종료** 공지 (공식 공지문은 못 찾음) | 엑셀 값은 그대로. **지금은 무료 플랜 없음.** 소유자 답 2 (유료는 단계별)에 따라 CryptoPanic은 **보류** (DS-4b에서 뺌, 커넥터 코드는 남김). 암호화폐 뉴스 감성 (X열)은 엑셀 X4가 함께 적은 Alpha Vantage (`CRYPTO:BTC` 등)로 채움 → X열 대안책 O는 그대로 성립 |

여섯째 실행 (2026-11-20, OA-08, 소유자 PC, 무료 키):

| 소스 | 출력 (공급사 문구, 키 가림) | 판단 |
|---|---|---|
| Alpha Vantage `NEWS_SENTIMENT` (AAPL) | "Information: … This is a premium endpoint. You may subscribe to any of the premium plans …" | **뉴스 감성은 무료 키로 안 됨 (유료 전용).** 엑셀 "무료 하루 25건"은 다른 함수 (시세·거시 지표)에는 맞을 수 있으나 뉴스 감성에는 아님. 관련성 필드 확인 (O열)도 무료로는 불가 |
| Tiingo `/tiingo/news` (nvda) | "HTTP 403 (You do not have permission to access the News API)" | **무료 플랜에 뉴스 없음.** 엑셀 M4 "Tiingo 무료 플랜"은 시세에는 맞을 수 있으나 뉴스에는 아님 |

처리: CryptoPanic과 같이 **보류** (소유자 답 2 "Alpha Vantage·Tiingo 유료는 그 뒤"). 커넥터 코드는 남김. DS-4b (무료 키 뉴스 3곳)는 무료로 쓸 수 있는 곳이 0이라 **전체 보류**. 영향: 뉴스 수집·감성·엔티티는 GDELT (무료, 확인 끝)와 자체 NLP (`D1`)로, 공시 사건은 EDGAR·OpenDART로 채움 → 2절의 "대안책 O" 칸 (F·G·H·X)은 GDELT·자체 NLP로 그대로 성립. 엑셀 칸은 바꾸지 않음.

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

**2026-11-19 갱신 (소유자 승인: 연구용 키 이름을 자격 증명 저장소에, KEY-3 PR):** DIDM 연결 코드는 모두 `data/didm/keys.py`로 키를 읽습니다. 저장소 (`core.credentials`: 환경변수 → Windows 자격 증명 관리자 → 개발판 `.env`)가 그 이름을 알면 저장소에서, 모르면 환경변수에서 읽습니다. **KEY-3이 main `9f76b07`로 병합되어 (2026-11-19) 연구용 9개 이름은 이제 모두 저장소 경로입니다** (`tests/didm_news_acceptance.py` `RealStoreRoundTrip`). 저장은 `python -m tools.didm.keys set <이름>` (입력이 화면에 안 보임). 현황은 `python -m tools.didm.keys status` (이름·있음/없음·출처만).

값은 소유자 PC에만 둡니다 (채팅·저장소·로그 금지). KEY-2 (결제·계정 세션) 병합 전에는 환경변수 **이름**만, 병합 뒤에는 `core/credentials`. `.env.example`에 더하는 일은 공유 파일이라 대기열을 거쳐 한 PR로 모읍니다.

| 소스 | 키 이름 | 지금 필요? | 비고 |
|---|---|---|---|
| CME FedWatch | `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET` | 아니요 (Stage 2 + 질문 2 답 뒤) | 인증 방식 **미검증**. 제안 이름 |
| FRED / ALFRED | `FRED_API_KEY` | 선택 (없으면 수동 다운로드 파일을 읽는 길) | 그래프 CSV는 키 없이 이미 앱에 있음 (`config.py`) |
| Polymarket | 없음 (조회만) | 아니요 | 소유자 답 4로 Kalshi가 대신함. 커넥터 꺼진 채 유지 |
| Kalshi | 없음 (공개 조회) | 지금 (DS-4e) | 계정·거래 없음 |
| SEC EDGAR | `SEC_EDGAR_USER_AGENT` (키 아님, 연락처 문자열) | 지금 (DS-4d) | SEC 공정 접근 규칙 |
| OpenDART | `OPENDART_API_KEY` (기존) | 지금 (DS-4d) | 1인 1키 |
| ECOS | `ECOS_API_KEY` | 지금 (DS-4d) | 무료 가입 |
| Trading Economics | `TRADINGECONOMICS_API_KEY` | 아니요 (Stage 3 뒤 견적) | 제안 이름 |
| GDELT | 없음 | 아니요 | 원본 파일, 키 없음 |
| Alpha Vantage | `ALPHAVANTAGE_API_KEY` | **보류** (뉴스 감성은 유료 전용, 2026-11-20 소유자 PC 확인) | 유료 단계에서 다시 판단 |
| Tiingo | `TIINGO_API_KEY` | **보류** (무료 플랜 News API 403, 2026-11-20 소유자 PC 확인) | 유료 단계에서 다시 판단 |
| Cryptopanic | `CRYPTOPANIC_API_KEY` | **보류** (무료 플랜 없음, 최저 $50/주·$199/월, 2026-11-20 확인) | 유료 단계에서 다시 판단 |
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

엑셀 밖 무료 공식 소스 — **추가 (소유자 답 3, 2026-11-18)**:

| 소스 | 채우는 것 | 상태 | 키·설정 이름 |
|---|---|---|---|
| SEC EDGAR | 미국 공시 (8-K 등). SEC 접수 시각이 초 단위라 사건 시각 기준으로 좋음 | 커넥터 커밋 (`data/didm/edgar.py`, 초당 8회로 제한). 실제 호출은 소유자 PC | `SEC_EDGAR_USER_AGENT` (일반 연락처, 개인정보 금지) |
| OpenDART | 한국 공시 전체 목록 (날짜 단위 접수일) | 커넥터 커밋 (`data/didm/opendart.py`, 기존 `data/krx/opendart_client.py` 재사용, 고치지 않음) | `OPENDART_API_KEY` (기존) |
| KIND (거래소 공시) | 한국 공시 | **연결 안 함.** 공개 API를 찾지 못했고, 웹 화면 수집은 약관 위험 (DIDM 8.3의 스크래핑 금지 취지). 같은 공시는 OpenDART로 받음 | — |
| ECOS (한국은행) | 한국 공식 통계 (기준금리, GDP 등) | 커넥터 커밋 (`data/didm/ecos.py`). 빈티지·발표 시각이 없어 `published_at` = 받은 시각 | `ECOS_API_KEY` (새 이름) |
| Kalshi (답 4) | 예정 사건 확률 (연준 결정 등) | 커넥터 커밋 (`data/didm/kalshi.py`, 키 없음, 조회만). 필드 이름 **미검증** | 없음 |

엑셀 밖 새 공급사 (2026-11-24): EODHD Economic Events, Alpaca News, Massive ticker news — 파서만 main에 있음, 쓸지 여부는 소유자 확인 대기. 계획과 가입 표는 `docs/didm/NEW_SOURCES_PLAN_2026-11-24.md`.

## 7. 대조 검사

```
python -m tools.didm.check_vendor_eval --excel <handoff의 plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt>
```

2026-11-18 실행 결과 (작업 브랜치 `claude/data-source-didm-20261117`):

```
columns 19, alternative cells 171, '?' cells 14, excel compared: yes
excel cells changed: 0
owner-confirmed columns differing from the Excel: N, O, W
OK
```

- 엑셀 글 사본의 두 줄 38값이 1절과 같고 (바뀐 값 0), 이 메모·설명에서 파생한 2절 171칸 (대안 쪽 ? 14칸)이 모두 `O|X|?·근거` 꼴이며, ? 칸마다 처리 방법이 하나 있고, 소유자 확정 값 (확정이 없으면 엑셀 값)과 모순 0건입니다.
- 같은 검사가 `tests/didm_vendor_eval_acceptance.py`에 있습니다 (네트워크 없음; 엑셀 값은 스크립트 안의 사본으로 비교).

이번 중앙 통합의 재검사는 글 사본의 원문 38값과 파생 평가표 171칸을 구분해 수행하며, 실제 XLSX 파일은 다시 열지 않았습니다. 0절의 2026-11-18 openpyxl 원본 대조는 당시 이력으로 보존합니다.

## 8. 소유자 확인 (완료 조건 4)

소유자 답 (2026-11-18, 원문 그대로):

> 1. 네 맞습니다. 다만 직접 구현이 필연적이므로, 표기를 X 대신 O로 해주세요
> 2. ?에 대해서 별도 처리할 필요는 없으나, 대안책의 자산별관련성점수의 경우 X로 확정입니다.

반영: 2절 `D1`·`D2` 칸, "대안책 (소유자 확정)" 열 (N = O, O = X, W = O), "?" 처리 안 함. 엑셀 열은 그대로 (7절 검사: 바뀐 칸 0). **완료 조건 4 충족 (소유자 확인).**
3. ~~지시문 질문 1~4~~ → 2026-11-18 답함 (0.1절).

## 9. 출처

- 소유자 엑셀 글 사본: handoff `plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt` (2026-11-17).
- 메인 분석: handoff `plans/2026-11-17/D14_RAVENPACK_ALTERNATIVES.md` 2·3·4·7·8·13절, `MASTER_WORK_DESIGN_2026-11-17.md` 부록 D (2026-11-17).
- 이 세션 검색 (2026-11-17, 검색 요약; 공급사 호스트는 직접 열기 막힘): Alpha Vantage NEWS_SENTIMENT 필드 (제3자 사본), Cryptopanic API 플랜 (공식 페이지 요약), Tiingo 무료 계정 (공식 문서 요약·제3자), Kalshi 공개 시세 (공식 빠른 시작 요약), GDELT 약관 (공식 About 요약). URL은 3절 표에.
