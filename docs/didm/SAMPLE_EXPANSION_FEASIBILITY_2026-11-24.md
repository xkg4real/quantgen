# DIDM 표본 확대 가능성 조사 (D12, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 D12). **조사 문서**입니다. 공급사 호출·키·코드 변경 없음. 소유자 결정 전 사전 조사.
- **2026-11-24 D14: 9절에 공급사 원문 확인 결과가 있고, 위 절과 다르면 9절이 우선합니다 (특히 Massive 약관 — 개인·비상업 전용, AI 학습 금지).**
- 출발점: DIDM Stage 0 모의실험 — 지연 반영을 검정력 80%로 보려면 **종목 약 820개 × 2,500거래일** 또는 **500개 × 5,000거래일** (근거: 브랜치 `claude/didm-dev-20261124`의 `docs/didm/PREREG_V0_1_PROPOSAL_2026-11-24.md` 6절; 이 세션은 그 수치를 다시 계산하지 않음).
- 표기: **확인** = 공급사 공식 문서·이 저장소 코드·소유자 PC 실측으로 본 것. **미검증** = 제3자 자료이거나 공식 문서를 직접 열지 못한 것. 가격은 공식 페이지에서 본 것만 적고, 못 본 것은 "공식 가격 못 봄".
- 이번 조사에서 웹 검색 요약만 썼고 공급사 페이지를 직접 열지는 않았습니다. 막힌 호스트는 없었습니다 (검색 요약으로 충분했던 항목만 적음).

## 0. 요약 (먼저 읽을 것)

| 질문 | 답 |
|---|---|
| 미국 500~1,000종목을 붙일 수 있나 | **공시 (EDGAR): 예** — 무료, 상장사 전체 CIK↔티커 표가 있고 2015~2024 과거 목록은 D6 코드로 받음. **뉴스: Alpaca (Benzinga)로 가능성 높음** — 2015년부터 (공급사 문서), 무료 조회 실측 성공 (AAPL), 종목 수 제한은 미검증. Massive 뉴스는 2021-04 이전이 거의 없어 2015~2020 표본에 못 씀 |
| 한국 500~1,000종목 | **공시 (OpenDART): 예** — 무료, 전체 상장사 고유번호 목록, 회사 지정 없이는 3개월씩 나눠 받음 (미검증, 제3자 자료). **뉴스: 지금 수집원 없음** (GDELT는 종목 태그 없음, 네이버·다음 수집 금지) |
| 2,500거래일 (약 10년, 2015~2024) | 미국 공시·Alpaca 뉴스·GDELT 2.0·ALFRED는 닿음. Kalshi (2021~)·Massive 뉴스 (실질 2021~)는 못 닿음 |
| 5,000거래일 (약 20년, 2005~2024) | **공시만 닿음** (EDGAR·OpenDART). 종목 뉴스는 무료 수집원으로 2005~2014를 채울 수 없음 (Massive의 Benzinga 묶음은 2009~, 유료 별도 요금) |
| 공급망·고객사 연결 | 무료: 10-K "주요 고객 (매출 10% 이상)" 공시 본문 (EDGAR) — 이름은 의무 아님, 본문 파싱 필요. 유료: FactSet Revere (2003~), Compustat Customer Segment, Bloomberg SPLC — 모두 공식 공개 가격 못 봄 (견적·학교 구독) |
| 결론 | **미국 820종목 × 2015~2024 (공시 + Alpaca 뉴스)가 무료로 가장 현실적인 경로.** 500 × 5,000일은 뉴스 없이 공시만으로 할 때만 무료로 가능. 한국은 공시 단독 표본만 가능 |

## 1. 종목 단위로 붙일 수 있는 종목 수

| 수집원 | 종목 연결 방법 | 미국 200 / 500 / 1,000 | 한국 200 / 500 / 1,000 | 근거·상태 |
|---|---|---|---|---|
| SEC EDGAR 공시 | CIK (회사 고유번호). `company_tickers.json` = SEC 공식 티커↔CIK 표 | O / O / O | — | 확인 (SEC API 문서: 키 없음, 회사별 submissions JSON, 전체 묶음 `submission.zip` 매일 재작성). 표의 회사 수는 미검증. 이 저장소: `--edgar`·`--edgar-history` (D6) |
| OpenDART 공시 | `corp_code` (고유번호 목록 `corpCode.xml`), 종목코드 함께 있음 | — | O / O / O | 확인 (이 저장소 `--opendart`, 소유자 PC 819건 실측 2026-11-18). 전체 목록 조회는 회사 지정 없으면 3개월씩 — 미검증 (제3자 정리) |
| Alpaca 뉴스 (Benzinga) | 기사마다 `symbols` 태그 | O / O(가능성 높음) / ?(미검증) | 해당 없음 (미국 종목) | 2015년부터: Alpaca 공식 문서 (확인, 검색 요약). 무료 조회: 소유자 PC 실측 성공 (AAPL 60건, 2026-11-24). 종목 수·호출 한도에 따른 소요 시간: 미검증 |
| Massive 뉴스 | `tickers` 태그 + 종목별 감성 | 2021-05 이후만 O | 해당 없음 | 무료 조회 실측 성공 (AAPL 200건, 모두 감성 있음). 과거: 공식 지식베이스 — 가장 오래된 기사 2016-06-22, **2021-04-22 이전 기사 500건 미만** (확인, 검색 요약) |
| GDELT 2.0 (사건·GKG) | 종목 태그 없음. 조직 이름 (GKG Organizations) → 회사 이름 대조가 필요 | △ (대형주만 이름 대조 실용적) | △ | 이름 대조는 이 저장소에 없음 (자체 연결 필요, SCORE_SCHEMA 2절 entity_id). 소형주는 언급 자체가 드묾 |
| Kalshi | 종목이 아니라 거시·사건 시장 | 해당 없음 (거시 요인) | 해당 없음 | 거시 요인 쪽 자료 |
| ALFRED·ECOS | 거시 계열 | 해당 없음 | 해당 없음 | 거시 요인 쪽 자료 |

**정리:** 종목 수의 병목은 공시가 아니라 **뉴스**입니다. 미국은 Alpaca 뉴스가 820종목을 덮는지 (특히 소형주 기사 수)를 실측해야 하고, 한국은 종목 뉴스 수집원이 없습니다.

## 2. 과거 범위

| 수집원 | 가장 이른 날짜 | 2015~2024 | 2005~2014 | 시점 규칙 (received_at 문제) | 상태 |
|---|---|---|---|---|---|
| EDGAR | 전자 제출 1990년대 중반 (미검증) | O (D6) | O (D6 같은 명령, `--edgar-from 2005-01-01`) | `acceptanceDateTime` = 공개 시각 (초 단위). 없으면 접수일 + PREREG 5절 1항 +1거래일 | 날짜: 미검증. 코드: 확인 (D6 시험) |
| OpenDART | 미검증 (DART 1999년 시작으로 알려짐, 공식 확인 못함) | O (3개월씩) | 아마 O (미검증) | 접수일만 → +1거래일 지연 (이미 코드에 `time_precision` "date") | 미검증 |
| Alpaca 뉴스 | 2015 | O (실측 필요: 2015 첫 기사) | **X** | `created_at` + 1거래일. `updated_at`이 늦은 기사는 표시 (NEW_SOURCES_PLAN, DS-6) | 시작 연도 확인 (공식 문서), 실측 미완 |
| Massive 뉴스 | 2016-06 (실질 2021-04~) | 2021~2024만 | X | 위와 같음. 감성 점수는 PREREG 5절 5항 확인 전 과거 검증 불사용 | 확인 (공식 지식베이스) |
| Massive Benzinga 묶음 | 2009-04-27 | O | 2009~2014만 | 위와 같음 | 별도 요금제, 공식 가격 못 봄 |
| GDELT 2.0 | 2015-02-18~19 | O | X | 15분 파일 시각 = 공개 시각 (PREREG 5절 1항 예외) | 확인 (GDELT 블로그) |
| GDELT 1.0 사건 | 1979 (일별 파일은 2013-04~) | — | O (사건만, GKG 1.0은 2013-04~) | 날짜 단위 (일 파일) | 확인. 이 저장소 파서는 2.0 형식만 → 1.0은 코드 추가 필요 |
| Kalshi | 2021-07 공개 출시 (CFTC 지정 2020-11) | 2021~만 (D7, 미검증) | X | 일봉 = 기간 끝 시각 | 지정일 확인 (CFTC), 출시일 미검증 |
| ALFRED | 계열마다 (수십 년) | O | O | **진짜 빈티지** (재현 가능) | 확인 |
| ECOS | 계열마다 | O | O | 개정 이력 없음 → 발표 지연 가정 | 확인 |

**received_at 문제:** 과거 자료를 지금 받으면 `received_at`이 전부 수집일이라 저장소의 `as_of()`로 그 시점을 재현할 수 없습니다. 모든 과거 표본은 PREREG 5절 1항대로 `published_at` + 고정 지연 (GDELT 파일 시각, 그 밖 +1거래일)을 씁니다. 예외: ALFRED. 이 규칙은 위 표의 모든 공시·뉴스에 그대로 적용 가능합니다 (모두 공개 시각 또는 날짜를 줌).

## 3. 종목 사이 연결 (공급망·고객사)

| 공급원 | 내용 | 기간 | 비용 | 약관상 연구 저장 | 상태 |
|---|---|---|---|---|---|
| SEC 10-K "주요 고객" 공시 | 매출 10% 이상 고객 (ASC 280). **고객 이름 공개는 의무 아님** (Reg S-K 101(c)를 따로 봐야 함), 실무는 회사마다 다름 | EDGAR 전체 | 무료 | 공공 자료 (SEC 공정 접근 규칙만) | 규칙 확인 (Deloitte 해설), 실제 공개율 미검증. **본문 파싱 필요** — 지금 수집기는 본문을 저장하지 않으므로 정책 변경 (본문 일부 저장 또는 추출 결과만 저장) 결정 필요 |
| DART 사업보고서 "주요 매출처" | 한국 회사의 주요 고객 서술 | DART 전체 | 무료 | 공공 자료 | 정형화 안 됨, 본문 파싱 필요. 미검증 |
| Compustat Customer Segment (WRDS) | 고객 이름 (약어) + 매출, GVKEY 연결표 있음 | 수십 년 (미검증) | 학교 WRDS 구독 | 구독 계약에 따름 | 학계 사용 확인 (연준 FEDS Note). 공식 가격 못 봄 |
| FactSet Revere Supply Chain | 고객·공급사·경쟁사·파트너 관계 (전 세계 상장사) | 2003~ (WRDS 표기) | 유료 (Revere 구독) | 계약에 따름 | 시작 연도 확인 (WRDS 문서). 공식 가격 못 봄 |
| Bloomberg SPLC | 공급망 관계 | 미검증 | 터미널 구독 | 계약에 따름 | 공식 가격 못 봄 |

학술 주의: 세 상용 DB를 연구에 쓸 때의 방법론 문제가 정리돼 있음 (Culot et al., 2023, *Journal of Supply Chain Management*) — 쓰게 되면 읽고 사전등록에 반영.

**권장:** 무료로는 EDGAR 10-K 주요 고객 공시가 유일한 체계적 경로. 다만 (a) 이름이 없는 공시가 많고 (b) 본문 처리 정책 결정이 먼저입니다. 연결 자료는 표본 확대와 별개 결정으로 두는 것을 제안합니다.

## 4. 소형주로 넓힐 때 사건율 가늠 (지금 자료로)

지금 저장소의 `collection_status`는 공급원 단위로만 셉니다 (D4). 소형주 사건율을 보려면 **종목별 건수**가 필요합니다.

방법 (호출을 최소로):

1. **공시 사건율 (무료, 키 없음):** 시가총액 구간별로 종목을 뽑아 (예: 대형 20 / 중형 20 / 소형 20 CIK) `--edgar-history`로 2015~2024 8-K 등을 받고, 종목당 연간 건수를 비교. 시가총액 구간은 지금 저장소에 없으므로 소유자가 아는 목록 또는 무료 지수 구성 (S&P 500 / 400 / 600)으로 고름 — 구성 목록 출처는 미검증.
2. **뉴스 사건율:** 같은 60종목으로 `--alpaca-news SYM --news-start 2015-01-01 --news-max-pages N`을 돌려 종목당 기사 수·첫 날짜 비교.
3. **집계:** `collection_status`에 종목별 건수 옵션 (`--by-entity`, 읽기만)을 더하면 위 두 결과를 한 표로 볼 수 있음 → **후속 제안 D13** (작은 코드, 오프라인 시험).
4. **판단 기준:** 종목·일당 사건 확률 p가 구간별로 얼마인지 → 필요한 종목 수 ≈ 모의실험의 종목 수 × (대형주 p / 소형주 p). 사건율이 절반이면 같은 검정력에 종목 수가 약 2배.

## 5. 넓히는 데 드는 소유자 작업

| 작업 | 키·가입 | 비용 | PC 실행 시간 (어림, 미검증) |
|---|---|---|---|
| EDGAR 820종목 × 2015~2024 | 없음 (`SEC_EDGAR_USER_AGENT`만, 이미 있음) | 무료 | 종목당 1~3 요청, 초당 8회 → **몇 분** |
| EDGAR 2005~2024 | 같음 | 무료 | 과거 파일이 더 많음 → 수십 분 이내 |
| OpenDART 2015~2024 전체 | 이미 있는 키 | 무료 | 3개월 × 40구간 × 쪽 수, 일일 호출 한도 (공식 수치 미검증) → 하루 안에 끝나지 않을 수 있음 |
| Alpaca 뉴스 820종목 × 10년 | 무료 키 (발급 완료) | 무료 (실측) | 쪽당 50건, 호출 한도 미검증 → 종목당 수십~수백 쪽, **몇 시간** 가능. 종목 여럿을 한 요청에 묶는 방법 검토 필요 |
| Massive 뉴스 | 무료 키 (발급 완료) | 무료 | 분당 5회 → 2021~만 의미 있음 |
| 공급망 상용 DB | 학교 WRDS 계정 또는 계약 | 유료·견적 | — |
| Benzinga 2009~ (Massive 묶음) | 유료 요금제 | 공식 가격 못 봄 | — |

## 6. 소유자·DIDM_DEV에 묻는 것 (결정 필요, 8절 별칭 사전 관련 질문 포함)

1. 표본 목표: **미국 820 × 2015~2024 (공시+뉴스)** 와 **500 × 2005~2024 (공시만)** 중 어느 쪽인가.
2. 한국 표본을 공시 단독으로 둘 것인가.
3. 공급망 연결을 위해 EDGAR 10-K 본문 일부 처리 (주요 고객 문단 추출)를 허용할 것인가 — 지금은 본문 저장 없음이 원칙.
4. D13 (종목별 건수 집계 옵션) 진행 여부 → 메인 승인 (2026-11-24), 진행 중.
5. 별칭 사전 새 수집 옵션 8.4의 1~4 중 무엇을 할지, 공공데이터포털 키 발급 여부.
6. 군집화 글을 제목만으로 시작할지 (8.3 권장).
7. (D14) Massive·Alpaca 뉴스를 모형 학습·검증 자료에서 뺄지 (둘 다 개인·비상업),, 이미 저장한 200건 (2026-11-24 실측)을 보관할지 삭제할지 (9.2 1번). Alpaca 약관 PDF 확인을 위해 `files.alpaca.markets` 허용 여부 (9.2 2번).

## 7. 출처 (2026-11-24 검색 요약)

- Alpaca 뉴스 2015~: docs.alpaca.markets/us/docs/historical-news-data, alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news
- Massive 뉴스 과거 범위: massive.com/knowledge-base/article/how-far-back-does-massives-news-and-sentiment-data-go
- GDELT 판별 기간: blog.gdeltproject.org/the-datasets-of-gdelt-as-of-february-2016/, gdeltproject.org/data.html
- SEC API: sec.gov/edgar/sec-api-documentation, sec.gov/os/accessing-edgar-data
- OpenDART 3개월 제한 (제3자): wikidocs.net/269624, algolab.co.kr/blog/dart-preliminary-earnings-disclosure-bot-filter-2026
- Kalshi 지정: cftc.gov/PressRoom/PressReleases/8302-20
- 주요 고객 공시: dart.deloitte.com (ASC 280 roadmap 5.7)
- 공급망 DB: library.hbs.edu (FactSet Revere), wrds-www.wharton.upenn.edu (FactSet Data on WRDS), federalreserve.gov FEDS Notes 2019-06-26, Culot et al. 2023

## 8. 개체 연결용 별칭 사전 (DIDM_DEV 요청, 메인 전달 2026-11-24)

요청 형식: 줄마다 `(별칭, entity_id, firm|macro, 유효 시작일, 유효 종료일 또는 없음)`. 사명 변경과 티커 재사용이 날짜로 들어 있어야 함.

### 8.1 (a) 어디서 만들 수 있나, 과거 이력 깊이

| 공급원 | 주는 것 | 날짜 붙은 이력 | 깊이 | 비용·키 | 상태 |
|---|---|---|---|---|---|
| SEC submissions JSON (`data.sec.gov`, 지금 `--edgar`가 이미 받음) | CIK (불변 ID), 현재 이름, **이전 이름 (formerNames)**, 현재 티커·거래소 | 이전 이름에 날짜가 붙는 것으로 알려짐 (키 이름·from/to 둘 다인지는 **미검증**; 제3자 자료는 "이전 이름 + 변경일"만이라고 함) | EDGAR 등록 이후 | 무료, 키 없음 | SEC 공식: "current name, former name, tickers" 포함 (확인). 필드 구조 미검증 → 실제 JSON 한 건으로 확인 필요 |
| SEC `company_tickers.json` | 현재 티커↔CIK | **없음** (현재 표만) | 현재만 | 무료 | 확인 |
| 미국 티커 재사용 이력 | — | 무료 공식 출처 **못 찾음** | — | 유료: CRSP 이름·티커 이력 (WRDS 학교 구독, 가격 못 봄) | 미검증 |
| OpenDART `corpCode.xml` | corp_code (불변 ID), 정식 회사명, 영문명, 종목코드, `modify_date` (기업개황 최종 변경일) | **없음** (현재 이름 + 마지막 변경일만) | 현재만 | 기존 `OPENDART_API_KEY` | 필드: 제3자 정리 (미검증) |
| OpenDART 공시 목록 (지금 `--opendart`가 받음) | 공시마다 그때의 회사명·report_nm | 공시 날짜별 회사명 → **사명 변경 시점 추정 가능**; "상호변경" 관련 공시 제목으로 변경일 확인 | 공시 목록 깊이 (미검증) | 기존 키 | 방법은 이 저장소 자료로 가능, 공시 제목 문구는 미검증 |
| 금융위원회_KRX상장종목정보 (공공데이터포털 `data.go.kr` 15094775) | 기준일자별 단축코드, ISIN, 시장, 종목명, 법인명 | 기준일자를 바꿔 조회하면 **날짜별 종목명·코드 스냅숏** → 사명 변경·코드 재사용 구간 계산 가능 | 과거 기준일 조회 가능 여부·시작일 **미검증** | 무료, 공공데이터포털 키 필요 (새 키 이름) | 제공 항목·일 1회 갱신: 확인 (검색 요약). 과거 조회: 미검증 |
| KRX Open API (`openapi.krx.co.kr`) | 유가증권·코스닥 종목 기본정보 | 기준일 파라미터 미검증 | 미검증 | KRX 인증키 신청 | 미검증 |
| 거시 별칭 (FOMC, CPI, 기준금리 등) | 자체 목록 | 손으로 날짜 (예: 기관 개명) | — | 없음 | DIDM_DEV와 같이 작성 |

**정리:** 회사 단위 entity_id는 **미국 CIK, 한국 corp_code** (둘 다 불변)로 두는 것이 안전합니다. 이름 이력은 SEC formerNames (미국)·OpenDART 공시 목록과 KRX 기준일 스냅숏 (한국)으로 만들 수 있습니다. **티커 재사용**은 한국은 KRX 기준일 스냅숏으로 가능해 보이나 (미검증), 미국은 무료 출처가 없어 ① 지금부터 매일 `company_tickers.json`을 받아 쌓거나 ② CRSP (유료)를 써야 합니다.

### 8.2 (b) 대상 종목 범위

| 범위 | 미국 | 한국 |
|---|---|---|
| 200 / 500 / 1,000 | 모두 가능 (submissions JSON 종목당 1요청, 초당 8회 → 1,000종목 약 2~3분) | 모두 가능 (corpCode.xml 한 번 + 공시 목록은 이미 받는 자료) |
| 상장폐지 종목 포함 (생존 편향 방지) | CIK는 폐지 뒤에도 남음. **폐지 종목 목록 자체**는 `company_tickers.json`에 없음 → 과거 표본의 종목 목록 출처가 따로 필요 (미검증) | corpCode.xml에 폐지 회사 포함 여부 미검증; KRX 기준일 스냅숏이면 해결 |

### 8.3 (c) 군집화에 넘길 글 (제목만 / 제목+첫 문단) 저장 권리

법률 자문이 아닙니다. 지금 원칙은 모든 공급원에서 **본문·요약을 저장하지 않음** (`docs/compliance/08-third-parties.md` DIDM 행).

| 공급원 | 제목 | 제목+첫 문단 | 근거·상태 |
|---|---|---|---|
| EDGAR·OpenDART | 공시 제목 (form, report_nm) 저장 중 | 공공 공시라 권리 문제는 작음. 단 **본문 처리 정책 결정** 필요 (6절 질문 3과 같음) | 정책 결정 사항 |
| Alpaca (Benzinga) | 저장 중 (headline) | **보류 권장**. Benzinga 라이선스 사본 (제3자 사이트에 올라온 C-1.0.0, 2026-09-21)은 "Benzinga 기능을 복제·경쟁하는 파생 데이터셋 금지", 귀속 표시 삭제 금지. 저장·캐시 조항은 그 사본에 없음. Alpaca 고객에게 적용되는 판인지 **미검증** | Alpaca 시장자료 약관 직접 확인 필요 |
| Massive | 저장 중 (title) | 공급사가 description 필드를 주지만 저장 안 함. 약관 **미검증** | massive.com 약관 확인 필요 |
| GDELT | GKG 페이지 제목 저장 중 | 첫 문단은 GDELT가 주지 않음 (기사 URL만) → 기사를 따라가 읽는 코드 경로 없음, 만들지 않음 | 기사 권리는 언론사 |

**권장:** 군집화는 우선 **제목 (+ 공급사 태그·시각)** 만으로 시작하고, 첫 문단은 Alpaca·Massive 약관을 직접 확인한 뒤 결정합니다.

### 8.4 (d) 칸 나눔과 필요한 새 수집 옵션

| 일 | 칸 | 내용 |
|---|---|---|
| 별칭 원자료 수집·정규화 | **DATA_SOURCE** | 공급원별 원자료를 시점 저장소에 `kind = entity_alias_source` 행으로 저장 (published_at = 그 이름·코드가 유효해진 날, received_at = 받은 날) |
| 별칭 사전 조립 (유효 구간 계산, 충돌 해결)·연결 규칙 (기사 → entity_id) | **DIDM_DEV** | `core/didm/` 쪽 (DIDM_DEV 칸) |
| 새 키 이름 | 결제·계정 세션 | 공공데이터포털 키 (예: `DATA_GO_KR_API_KEY`, 이름은 제안) |

새 수집 옵션 (제안, 소유자·메인 승인 뒤):

1. `--edgar-names CIK...` — 이미 받는 submissions JSON에서 현재 이름·이전 이름 (날짜)·현재 티커를 별칭 원자료 행으로. 새 호스트 없음.
2. `--sec-ticker-snapshot` — `company_tickers.json`을 하루 한 번 받아 날짜 붙은 스냅숏으로 (미국 티커 재사용 이력을 앞으로 쌓음). 새 호스트 `www.sec.gov` (지금 `data.sec.gov`만 씀).
3. `--opendart-corpcodes` — corpCode.xml 스냅숏 (기존 키).
4. `--krx-listing YYYYMMDD [...]` — 공공데이터포털 KRX상장종목정보, 기준일자별 스냅숏. 새 호스트 `apis.data.go.kr`, 새 키.

### 8.5 직접 열어 확인할 호스트 (메인이 환경 승인 요청)

| 호스트 | 확인할 것 |
|---|---|
| `www.sec.gov` (개발자 문서), `data.sec.gov` (submissions JSON 한 건) | formerNames 필드 구조·날짜 |
| `opendart.fss.or.kr` | corpCode.xml 필드, 공시 목록 3개월 제한, 자료 시작 연도 |
| `www.data.go.kr`, `apis.data.go.kr` | KRX상장종목정보 과거 기준일 조회 가능 여부·시작일 |
| `openapi.krx.co.kr` | 종목 기본정보 기준일 파라미터 |
| `alpaca.markets`, `docs.alpaca.markets` | 시장자료 약관 (뉴스 저장·제목·요약) |
| `massive.com` | 뉴스 약관, 무료 플랜 뉴스 이력 |

이 문서의 8절 출처 (검색 요약): sec.gov/edgar/sec-api-documentation, data.catalyst.coop (PUDL sec10k name changelog, 제3자), data.go.kr/data/15094775/openapi.do, dart-fss.readthedocs.io (corp_code 필드, 제3자), firecrawl.dev/terms/third-party-data/benzinga/C-1.0.0 (Benzinga 약관 사본, 제3자), docs.alpaca.markets/us/docs/streaming-real-time-news.

## 9. 원문 확인 (D14, 2026-11-24)

소유자가 승인한 문서 호스트 6개 (`docs.alpaca.markets`, `alpaca.markets`, `massive.com`, `opendart.fss.or.kr`, `www.data.go.kr`, `openapi.krx.co.kr`)에서 **문서·약관 페이지만** 읽었습니다 (키가 필요한 API 호출·파일 내려받기 없음). 확인일은 모두 2026-11-24. 약관은 문구 인용까지만이며 **법률 자문이 아닙니다.** 이 절이 위 1~8절과 다르면 이 절이 우선합니다.

### 9.1 확인한 사실

| 공급원 | 항목 | 원문 (인용·요약) | URL | 상태 |
|---|---|---|---|---|
| Alpaca | 무료 계정 | Trading API 구독은 Basic (Free)·Algo Trader Plus ($99/월). "The Basic plan serves as the default option for both Paper and Live trading accounts ... with zero cost" | docs.alpaca.markets/docs/about-market-data-api | 확인. 소유자 PC 실측 (뉴스 60건)과 일치 |
| Alpaca | 호출 한도 | 표의 "Historical API calls": Basic 200/min, Algo Trader Plus 10,000/min (주식·옵션 표). 뉴스 전용 한도는 이 표에 없음. 출시 블로그: "200 calls per minute for Free plans" (뉴스 API 베타 당시) | 위 + alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news | 주식 한도 확인; 뉴스 한도는 블로그 (옛 베타 문구) 기준 |
| Alpaca | 과거 깊이 | 문서 v1.4.2: "historical news data dating back to 2015 ... average of 130+ news articles per day. All news data is currently provided directly by Benzinga". 현재 판 문서는 시작 연도를 적지 않음 | docs.alpaca.markets/us/v1.4.2/docs/historical-news-data, docs.alpaca.markets/us/docs/historical-news-data | 2015는 옛 판 문서 기준. 실제 첫 기사 날짜는 소유자 PC 실측 필요 |
| Alpaca | 용도 안내 | 현재 판 문서 "Sentiment analysis: Build a labeled dataset from past headlines, summaries, and content, and train models that score the sentiment of new articles" | docs.alpaca.markets/us/docs/historical-news-data | 확인 (사용 예시일 뿐, 약관이 아님) |
| Alpaca | **약관 (이용 범위)** | 소유자 허용 (2026-11-24)으로 PDF를 읽음. "Personal and Non-Commercial Usage: ... you agree to use the Services and Content solely for your own personal and non-commercial purposes. Should you wish to use the Services and Content for any other purposes, including without limitation commercial usage, or making the Services and Content available to others through your own application (a 'User Application'), you shall provide Alpaca with 30 days advance written notice"; "Content is provided exclusively for personal and noncommercial access and use. No part of the Service or Content may be copied, reproduced, republished ... for publication or distribution or for any commercial enterprise, without Alpaca's express prior written consent." 'General news' 와 Third-Party Content (Benzinga)가 Content에 포함. AI·ML 학습 조항은 이 문서에 없음. 문서에 판 날짜 표시 없음 | s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf (Alpaca 문서 바닥글의 'Terms & Conditions' 링크; `files.alpaca.markets` 직접 주소는 이 환경에서 막힘) | 확인 |
| Massive | 과거 깊이 | "ticker news starts on 22 June 2016, with all history on Stocks Starter and above and **2 years on Stocks Basic**, but it is sparse until late April 2021" — 2016-06-22~2021-04-21 500건 미만, 2016~2019 연 50건 미만, 2020 약 200건 | massive.com/knowledge-base/article/how-far-back-does-massives-news-and-sentiment-data-go | 확인 |
| Massive | 감성 (insights) | "the insights sentiment field starts with articles published on 2 July 2024" (17:46 UTC 이전 기사에는 없음, 과거 기사에 덧붙일 방법 없음). 뉴스 끝점은 1시간마다 갱신, 게재 뒤 1시간 미만~수 시간 늦게 도착 | 위 | 확인 |
| Massive | Benzinga 묶음 | 지식베이스: 2009-04-27부터. 요금 페이지: "Benzinga ... $99/month per dataset" | 위 + massive.com/pricing | 확인 |
| Massive | **이용 범위** | 개인 약관 (Last Updated 2026-11-03): "solely for your own personal, non-commercial, and non-business purposes". 시장자료 약관: 저장 허용은 "solely for your own personal, non-business and non-commercial use ... does not permit you to ... develop or provide a service or application to other users, use Information for an employer or any other organization, or use it in professional or commercial work" | massive.com/legal/individuals-terms-of-service, massive.com/legal/market-data-terms-of-service | 확인 |
| Massive | **AI 학습** | 시장자료 약관 5(g): 금지 — "Use Information to train, fine-tune or distill an artificial-intelligence or machine-learning model unless expressly permitted and all applicable Third Party Provider requirements are satisfied" | massive.com/legal/market-data-terms-of-service | 확인 |
| Massive | 종료 뒤 삭제 | "When your license to any Information ends, you must stop using it and delete it promptly, and in any event within thirty (30) days, including downloaded files, stored copies and caches" (자동 백업은 90일 이내) | 위 | 확인 |
| OpenDART | 기간 제한 | 공시검색 `bgn_de`: "고유번호(corp_code)가 없는 경우 검색기간은 3개월로 제한" | opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001 | 확인 |
| OpenDART | 요청 한도 | 오류 020 "요청 제한을 초과하였습니다. 일반적으로는 20,000건 이상의 요청에 대하여 이 에러 메시지가 발생" (집계 기간은 이 페이지에 없음); 오류 021 "조회 가능한 회사 개수가 초과 (최대 100건)" | 위 | 한도 수치 확인, 기간 (일 단위인지) **미검증** |
| OpenDART | 약관 | 제16조: 서비스·프로그램 저작권은 금융감독원, "약관에 명시되지 않은 저작권과 관련된 사항은 저작권법 및 공공데이터법에 따릅니다". 가입 정보에 "기업용으로 신청할 경우" 항목이 있음. 상업 이용을 금지하는 조항은 이 페이지 검색에서 찾지 못함 | opendart.fss.or.kr/intro/terms.do | 확인 (찾지 못한 것은 "없음"이 아니라 "이 페이지에 없음") |
| 공공데이터포털 KRX상장종목정보 | 과거 기준일 | 요청변수 `basDt` (일치), `beginBasDt` ("기준일자가 검색값보다 크거나 같은"), `endBasDt` ("작은"), `likeBasDt` | www.data.go.kr/data/15094775/openapi.do | 기간 조회 변수 있음 확인. **자료가 언제부터 있는지는 미검증** (페이지 "시간범위 -") |
| 공공데이터포털 KRX상장종목정보 | **이용 조건** | "공공누리 4유형 ... 출처표시 + 상업적 이용금지 + 변경금지", "상업적 목적 여부와 상관 없이 제3자 무단 제공 및 재배포가 엄격히 금지", "상업적 목적으로 이용할 경우 ... KRX Data Marketplace(data.krx.co.kr)에서 유료로 구매". 갱신: 기준일 다음 영업일 오후 1시 이후. 트래픽 개발계정 10,000 | 위 | 확인 |
| KRX Open API | **이용 조건** | "API Users may only use the API Service for non-commercial purposes", "may not provide the data provided by the KRX to any third parties", 계약 종료 뒤 사용 금지, "maximum number of requests for one (1) key shall be 10,000 a day" | openapi.krx.co.kr/contents/OPP/INFO/OPPINFO005.jsp | 확인 |

### 9.2 바뀌는 판단

1. **Massive 무료 (개인) 플랜은 DIDM에 쓰기 어렵습니다.** QUANTGEN은 상업 앱이고 DIDM은 모형 학습이 목적인데, 개인 약관은 비상업·비업무 용도만 허용하고 시장자료 약관 5(g)는 AI·ML 학습을 금지합니다. 또 무료 Basic은 뉴스 2년치만, 감성은 2024-07-02부터입니다. → **제안: Massive 뉴스는 수집 연결 확인 (2026-11-24 실측) 까지로 두고, 모형 학습·검증 자료로는 쓰지 않음. 쓰려면 사업자 (Businesses) 약관·요금 확인이 먼저.** 이미 저장한 200건의 처리 (보관·삭제)는 소유자 결정 사항입니다.
2. **Alpaca 무료 계정도 개인·비상업 전용입니다** (9.1 약관 인용). 상업 목적이면 30일 전 서면 통지, 콘텐츠를 상업 사업에 복제·이용하려면 Alpaca의 사전 서면 동의가 필요합니다. AI 학습 조항은 없지만 상업 사업 안의 복제 금지에 걸릴 수 있습니다. → 2절의 "미국 820 × 2015~2024 (공시 + Alpaca 뉴스)" 경로는 **Alpaca의 서면 동의 없이는 공시 단독으로 줄어듭니다.** 대안은 10절.
3. **KRX 계열 (공공데이터포털·KRX Open API)은 비상업 전용입니다.** 8.4의 `--krx-listing`은 상업 앱 연구에 그대로 쓰기 어렵고, 상업 이용은 KRX Data Marketplace 유료 구매. → 한국 별칭 사전은 OpenDART (공시 목록의 날짜별 회사명 + corpCode.xml) 중심으로.
4. **OpenDART 10년치 전체 목록:** 회사 지정 없이 3개월씩 (40구간 이상) + 쪽 나눔, 요청 한도 20,000건 (기간 미검증). 회사 지정 (corp_code, 최대 100개)이면 기간 제한이 풀리므로 표본 종목을 정한 뒤 회사별로 받는 편이 호출이 적을 수 있습니다.

### 9.3 아직 미검증 (필요 호스트)

| 항목 | 필요 호스트 |
|---|---|
| Alpaca 시장자료 계약 (Nasdaq·NYSE, 시세용) | 뉴스와 무관해 이번에 보지 않음 |
| Massive 사업자 약관·요금 (상업·학습 허용 여부) | `massive.com` (허용됨, 이번 범위 밖이라 다음에) |
| Benzinga 원 라이선스 (Alpaca 고객 적용 판) | Alpaca 약관 안에 있을 가능성 |
| KRX상장종목정보 자료 시작일 | 키가 필요한 API 호출 (이번 규칙상 안 함) |
| OpenDART 요청 한도의 집계 기간 | `opendart.fss.or.kr` 다른 안내 페이지 |
| SEC formerNames 구조, EDGAR 시작 연도 | `www.sec.gov`·`data.sec.gov` (연락처 User-Agent 필요 → 소유자 PC) |


## 10. Massive 대안 (소유자 요청 2026-11-24)

조건: QUANTGEN은 상업 앱이고 DIDM은 모형 학습이 목적 → **상업 이용**과 **학습 이용**이 약관상 가능해야 함. 그다음 종목 태그, 과거 깊이 (2015~), 시각 (공개 시각), 비용. 확인 방법: 웹 검색 요약 (해당 공급사 호스트는 이 환경에서 막혀 원문을 직접 열지 못함 → 행마다 "검색 요약"). 예외: GDELT 행은 원문 (2026-11-24). 법률 자문이 아닙니다.

| 대안 | 상업 이용 | 학습 이용 | 종목 태그 | 과거 | 비용 | 판단 |
|---|---|---|---|---|---|---|
| **GDELT 2.0** (이미 연결) | 허용 — 원문: "The GDELT Project is an open platform for research and analysis of global society and thus all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee." 재배포·사용 시 인용과 링크 필수: "You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form. However, any use or redistribution of the data must include a citation to the GDELT Project and a link to this website (https://www.gdeltproject.org/)." (www.gdeltproject.org/about.html "Terms of Use" 절, 확인일 2026-11-24 (소유자 허용 호스트)) | **원문에 학습 조항 없음** ("unlimited and unrestricted use ... of any kind"만) | 없음 (조직 이름 → 자체 연결) | 2015-02~ | 무료 | **Go** — 지금 바로. 단 기사 본문 권리는 언론사, 저장은 제목·메타데이터만 (지금 원칙) |
| **SEC EDGAR 8-K (+ 보도자료 첨부 Exhibit 99.1)** (이미 연결, D6) | 공공 공시 | 공시 메타데이터 (서식·항목 코드·시각)는 문제 작음. 첨부 보도자료 본문은 회사 저작물 — 본문 처리는 정책 결정 (6절 3번) | CIK (정확) | 공시 전체 (D6) | 무료 | **Go** — 8-K 항목 코드 (2.02 실적, 5.02 임원 등)가 사실상 "회사 뉴스 사건". 본문 없이도 사건 시각·유형은 정확 |
| **OpenDART** (한국, 이미 연결) | 약관에 상업 금지 조항 못 찾음 (9.1) | 같음 | corp_code (정확) | 3개월씩 | 무료 | **Go** (한국) |
| **Benzinga 직접 계약** | 사업자 계약 | **학습용 데이터셋을 따로 판매** ("Fully licensed ... datasets - ideal for training Large Language Models", 검색 요약). 단 제3자 (Firecrawl) 경유 판은 "일반 AI 모형 학습 금지, 비공개 인스턴스만" | 있음 | 미검증 (Massive의 Benzinga 묶음은 2009-04~) | 견적 (공개 가격 없음) | **조건부 Go** — Alpaca·Massive 뉴스의 원 출처와 같은 자료를 학습 권리째 사는 길. 견적·이력 깊이·학습 조항을 서면으로 받은 뒤 결정 |
| **Tiingo Commercial** | "Commercial accounts ... licensed for internal commercial usage", 재배포 금지 (Tiingo 문서, 검색 요약) | 언급 없음 (미검증) | 있음 | 요금표상 Power·Commercial은 뉴스 **3개월**만, 1995~ 전체는 상위 (Enterprise) — 표가 모호 | Commercial $50/월 (검색 요약) | **보류** — 내부 상업 이용은 되나 과거 뉴스가 3개월이면 표본 (2015~)에 못 씀. 상위 요금 견적 필요 |
| **EODHD 상업 라이선스** | 별도 상업 라이선스 (문의) | 언급 없음 (미검증) | 있음 + 일별 감성 | 미검증 | 견적 | **보류** — 무료·개인 요금은 상업 불가. DS-5a (N1)와 묶어 견적 |
| RavenPack (WRDS 학교 구독) | 학술 연구만 (학교 계약) | 학교 계약 범위 | 있음 (엔티티 ID) | 2000~ (미검증) | 학교 구독 | **No-go (제품용)** — 상업 앱에 못 씀. 학술 논문용 기준선으로만 |
| Finnhub 무료 | 개인 전용이라는 자료가 다수 (검색 요약) | 미검증 | 있음 | 1~2년 | 무료/유료 | **No-go** (무료) |
| FNSPID (공개 연구 데이터셋, 1999~2023, 1,570만 건) | **CC BY-NC 4.0 — 상업 이용 금지** (Hugging Face 판) | — | 있음 | 1999~2023 | 무료 | **No-go** (제품용) |
| Massive Basic / Alpaca Basic | 개인·비상업 (9.1 원문) | Massive는 학습 금지 | 있음 | Massive 2년 / Alpaca 2015~ | 무료 | **No-go** (상업·학습). Alpaca는 서면 동의를 받으면 재검토 |
| 공공데이터포털·KRX Open API | 비상업 (9.1 원문) | — | 종목 목록 | — | 무료 | **No-go** (상업) |

### 10.1 권장 순서

1. **지금 (무료, 권리 문제 작음):** GDELT 2.0 + EDGAR 8-K 항목 코드 (미국) + OpenDART (한국)로 Stage 2 사건 표본을 만듭니다. "뉴스"보다 좁지만 시각·유형이 정확하고 상업·학습 제약이 없습니다 (GDELT는 인용 필수).
2. **뉴스 텍스트가 꼭 필요하면:** Benzinga에 학습 권리 포함 견적을 요청 (이력 깊이·종목 태그·학습·보관 조항을 서면으로). Alpaca에는 상업 이용 서면 동의를 문의하는 길도 있으나 Benzinga 원 약관 (학습 제한) 이 따라올 수 있어 Benzinga 직접 계약이 더 깔끔합니다.
3. **비교용:** Tiingo 상위 요금·EODHD 상업 라이선스 견적은 DS-5a (N1) 결정 때 함께.
4. **이미 받은 자료:** Massive 200건·Alpaca 60건은 개인·비상업 조건으로 받은 것이므로 학습·검증에 쓰지 않고, 보관·삭제는 소유자 결정 (Massive는 플랜 종료 뒤 30일 안 삭제 의무).

출처 (검색 요약, 2026-11-24): benzinga.com/apis/datasets-for-training-llms-and-ai-applications, firecrawl.dev/terms/third-party-data/benzinga/C-1.0.0, api.tiingo.com/documentation, api.tiingo.com/products/news-api, eodhd.com/financial-apis/terms-conditions, gdeltproject.org/about.html, huggingface.co/datasets/khaihernlow/fnspid, wrds-www.wharton.upenn.edu (RavenPack), massive.com/compare/massive-vs-finnhub. 원문 확인이 필요한 호스트: www.benzinga.com, api.tiingo.com, eodhd.com. (GDELT는 2026-11-24 원문 확인 완료.)
