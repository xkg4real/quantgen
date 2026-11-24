# Stage 2 사건 표본 계획: GDELT 2.0 + EDGAR 8-K 항목 코드 + OpenDART (D15, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 D15). **계획 문서**입니다. 공급사 호출·코드 변경 없음.
- 배경: Alpaca·Massive 뉴스는 약관상 개인·비상업 전용이라 연구 표본에서 뺐습니다 (`core/didm/ingest/terms.py`, `SAMPLE_EXPANSION_FEASIBILITY_2026-11-24.md` 9·10절). 남는 무료·상업 가능 경로가 이 세 수집원입니다.
- 표기: **확인** = 이 저장소 코드·시험 또는 원문으로 본 것. **어림** = 이 문서의 계산 (근거 적음). **미검증** = 확인 못 함.
- GDELT 약관 (원문, www.gdeltproject.org/about.html "Terms of Use" 절, 확인일 2026-11-24 (소유자 허용 호스트); 법률 자문 아님):
  - 상업 이용: "The GDELT Project is an open platform for research and analysis of global society and thus all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee."
  - 재배포·인용 의무: "You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form. However, any use or redistribution of the data must include a citation to the GDELT Project and a link to this website (https://www.gdeltproject.org/)." → 수집기는 이미 인용 문구 (`gdelt.ATTRIBUTION`)를 출력함; 제품·논문에 쓸 때도 같은 인용과 링크.
  - 모델 학습: **원문에 해당 조항 없음** (위 "unlimited and unrestricted use ... of any kind" 외에 학습을 따로 다루는 문장 없음). 데이터 페이지 (www.gdeltproject.org/data.html): "The entire GDELT database is 100% free and open".
  - 주의: 이 약관은 GDELT가 만든 자료 (사건·GKG 행)에 대한 것이며, 행이 가리키는 **기사 본문의 권리는 각 언론사**에 있음 (약관에 기사 본문 권리 언급 없음). 지금 원칙대로 제목·URL·메타데이터만 저장.

## 1. 무엇을 사건으로 쓰나

| 수집원 | 사건 단위 | 대상 (entity) | 사건 시각 | 이 저장소 상태 |
|---|---|---|---|---|
| EDGAR 8-K (미국) | 8-K 한 건 × 항목 코드 (`items`, 예 "2.02,9.01") | CIK (정확, 공시 주체) | `acceptanceDateTime` (초 단위), 없으면 접수일 (`time_precision` "date") | 확인: `--edgar-history` (D6), 행 payload에 `form`, `items`, `filing_date`, `cik`, `company` |
| OpenDART (한국) | 공시 한 건 (`report_nm`) | corp_code (정확) | 접수일만 (`rcept_dt`, `time_precision` "date") | 확인: `--opendart`, payload에 `report_nm`, `corp_code`, `stock_code`, `corp_cls` |
| GDELT 2.0 GKG | 기사 한 건 (기사 URL·제목·주제·조직·논조) | 없음 → 조직 이름을 별칭 사전으로 연결 (D12 8절, DIDM_DEV 규칙) | 15분 파일 시각 (`DATE`) | 확인: `--gdelt-day --gdelt-gkg`, payload에 `page_title`, `themes`, `organizations`, `tone`, `document_identifier` |
| GDELT 2.0 사건 (events) | CAMEO 사건 한 건 | 국가 (거시) | `DATEADDED` (15분) | 확인: payload에 `event_root_code`, `goldstein`, `num_articles`, `actor1/2_country` |

## 2. 필드 (표본 한 줄)

DIDM_DEV에 넘길 정규화 줄의 제안 (이름은 DIDM_DEV가 확정):

| 필드 | EDGAR 8-K | OpenDART | GDELT GKG | GDELT events |
|---|---|---|---|---|
| `event_id` | accession (+ 항목 코드) | rcept_no | GKGRECORDID | GLOBALEVENTID |
| `entity_id` | CIK | corp_code | 별칭 사전 연결 결과 (없으면 none) | 국가 코드 (거시) |
| `published_at` | acceptanceDateTime | 접수일 00:00 KST | 파일 시각 | DATEADDED |
| `available_at` (3절) | published_at + 지연 | 다음 거래일 | 파일 시각 | DATEADDED |
| `event_type_hint` (4절) | 항목 코드 규칙 | report_nm 규칙 | themes 규칙 | CAMEO root 규칙 |
| `title` (채점기 입력) | 합성 제목 ("8-K Item 2.02 Results of Operations — {company}") | report_nm (실제 제목, 한국어) | page_title (있을 때) | 없음 |
| `body` | null | null | null | null |
| `source_id` | `sec-edgar` | `opendart` | `gdelt-gkg2` | `gdelt-events2` |

## 3. 시점 규칙 (받은 시각이 없는 과거 자료)

과거 자료를 지금 받으면 `received_at`은 전부 수집일이라 저장소의 `as_of()`로 그 시점을 재현할 수 없습니다. PREREG_V0 5절 1항대로 **`available_at` = `published_at` + 고정 지연**을 씁니다.

| 수집원 | `available_at` | 근거 |
|---|---|---|
| GDELT (GKG·events) | 15분 파일 시각 그대로 | PREREG 5절 1항 예외 (파일이 그 시각에 공개) |
| EDGAR 8-K, `time_precision` "second" | acceptanceDateTime **다음 거래일 시가** (보수) — 장중 반응을 보려면 acceptance + 15분을 따로 사전등록 | PREREG 5절 1항 "+1 거래일 보수 지연". EDGAR 공개까지의 실제 지연은 **미검증** |
| EDGAR 8-K, "date" (acceptance 없음) | 접수일 다음 거래일 | 같음 |
| OpenDART | 접수일 다음 거래일 | 같음 (시각 없음, D6과 같은 규칙) |

수정·재게시: EDGAR 8-K/A, OpenDART 정정공시는 **별개 사건**으로 두고 원 공시와의 연결 (accession·rcept_no 참조)은 DIDM_DEV 규칙. 저장소는 덮어쓰지 않습니다.

## 4. 사건 유형 14개와의 대응 (규칙 힌트, 채점기 대체 아님)

| event_type | EDGAR 8-K 항목 | OpenDART report_nm (부분 문자열, 미검증 목록) | GDELT |
|---|---|---|---|
| earnings | 2.02 (실적), 4.02 (재작성) | "잠정실적", "영업(잠정)실적", "매출액또는손익구조" | themes `ECON_EARNINGSREPORT` (미검증 이름) |
| mergers_acquisitions | 2.01 (취득·처분 완료), 1.01 중 합병 계약 (본문 필요) | "합병", "분할", "주식교환", "영업양수", "타법인주식및출자증권취득" | themes `ECON_MERGERS` (미검증) |
| management | 5.02 (임원·이사 변경) | "대표이사변경", "임원" | — |
| regulation_litigation | 1.03 (파산), 3.01 (상장폐지 통지), 4.01 (감사인 변경) | "소송", "횡령", "배임", "상장폐지", "거래정지" | themes `LEGISLATION`, `TAX_` 등 (미검증) |
| supply_chain | 1.01/1.02 중 공급 계약 (본문 필요) | "단일판매ㆍ공급계약체결" | themes 공급망 관련 (미검증) |
| crypto_regulation_hack | 1.05 (사이버보안 사고, 2023-12~) — 암호화폐와 직접 연결 아님 | — | themes 암호화폐 (미검증) |
| monetary_policy · inflation · employment · growth · fiscal | — | — | 거시: 이 표본이 아니라 ALFRED·ECOS·FedWatch 발표 일정에서 (기존 수집원) |
| trade_tariffs · geopolitics · election_policy | — | — | CAMEO root (예: 14 시위, 16 관계 축소, 17 강압, 18~20 무력) + 국가 → 거시 사건 |
| none | 5.07 (주총 결과), 9.01 단독, 7.01·8.01 (본문 없이는 판단 불가) | 그 밖 | 그 밖 |

7.01 (Reg FD)·8.01 (기타)은 8-K에서 흔하지만 항목 코드만으로 유형을 정할 수 없습니다 → `none` 또는 "본문 필요"로 표시하고 표본 크기 추정에서 따로 셉니다.

## 5. 범위와 건수 추정 (2015~2024, **어림**)

| 수집원 | 대상 | 건수 어림 | 근거·확인 방법 |
|---|---|---|---|
| EDGAR 8-K | 미국 820종목 | 종목당 연 10~20건 → **약 8만~16만 건** (10년) | 어림. D13 `collection_status --by-entity`로 표본 60종목 실측 후 고침 (SAMPLE_EXPANSION 4절) |
| 그중 유형 판정 가능 (7.01·8.01·9.01 단독 제외) | | 절반 안팎 (미검증) | 같은 실측 |
| OpenDART | 한국 500~1,000종목 | 종목당 연 수십 건 (정기·주요사항·기타 포함) → 수십만 건, 주요사항보고서만이면 훨씬 적음 | 어림. `--opendart` 실측 (소유자 PC 2026-11-18: 하루치 전체 819건) |
| GDELT GKG | 전 세계 기사 | 하루 수십만 건 (미검증) → 10년 수억 건: **PC 저장소에 전부 넣을 수 없음** | 표본 날짜만 받거나, 주제·조직 거르기 뒤 저장. 아래 6절 |
| GDELT events | 전 세계 사건 | 하루 십만 건대 (미검증) | 같음 |

## 6. 저장 크기 (**어림**, 실측 전)

| 수집원 | 행 크기 | 10년 저장 |
|---|---|---|
| EDGAR 8-K 820종목 | 행당 약 0.5 KB (메타데이터만) | 약 40~80 MB |
| OpenDART 1,000종목 | 행당 약 0.5 KB | 수백 MB 이하 |
| GDELT GKG 전부 | 행당 약 1~3 KB (주제·조직 각 50개 상한) | **수백 GB~TB** → 불가. 15분 압축 파일 크기도 미검증 |
| GDELT GKG 거르기 뒤 (표본 820종목 조직 이름·금융 주제) | | 수 GB 이하 목표 (미검증) |

GDELT 권장: (a) 사건 연구 날짜 주변 창 (예: 8-K 사건일 ±1일)만 `--gdelt-day`로 받거나, (b) GDELT의 BigQuery 공개 자료에서 걸러 받기 (BigQuery 요금·약관은 GDELT와 별도, 미검증). 둘 다 새 수집 옵션이 필요 (거르기 조건을 받는 `--gdelt-day` 확장) → 메인 승인 뒤.

## 7. 기사 본문이 없다는 점이 채점기에 주는 영향

채점기 입력은 `title` (필수) + `body` (null 허용) (`SCORER_CONTRACT_V0.md` 2절). 이 표본은 **모든 줄이 body = null**입니다.

| 판단 필드 | 영향 |
|---|---|
| `p_subject` (대상이 주제인가) | 공시는 공시 주체가 곧 대상 → 거의 1 (채점기 불필요). GDELT는 제목에 회사 이름이 있을 때만 판단 가능; 없으면 낮게 나옴 |
| `event_type` | 공시는 항목 코드·report_nm 규칙 (4절)이 채점기보다 정확. 합성 제목 ("Item 2.02")을 LLM에 주면 규칙을 다시 맞히는 것에 그침. GDELT는 제목 + 주제 태그로 판단 |
| `direction_probs` (호재·악재) | **가장 큰 손실.** "8-K Item 2.02"만으로는 실적이 좋았는지 알 수 없음 → 방향은 거의 중립 (P(0) 높음) → ESS-like 점수가 정보가 없음. OpenDART report_nm도 대부분 방향 없음 (예외: "손실", "횡령" 등). GDELT 제목·논조 (tone)는 방향 단서가 있으나 기사 전체가 아님 |
| `claim_status` | 공시는 `confirmed` (당사자 공식 발표; PREREG_V0_1 제안 C2와 맞음). GDELT 보도는 `reported` |
| 신규성 | 시각·묶음 기반이라 본문 없이도 계산 가능 |

**결론:** 이 표본은 "사건이 **언제·무엇**이었나"는 정확하지만 "**좋은 소식인가 나쁜 소식인가**"는 거의 모릅니다. 그래서 Stage 2를 이 표본으로 하면:

1. 방향 대신 **시장 반응 (market_confirmation)** 으로 사건의 부호를 정하고, 지연 반영 (drift)을 사건 유형·시각 단위로 검정하는 설계가 맞습니다 (방향 예측력 검정은 불가).
2. 방향 신호가 꼭 필요하면 (a) 실적은 XBRL 재무값 (SEC companyfacts, 무료)의 전년 대비 변화로 대신하거나 — 컨센서스가 없어 "예상 대비"는 아님 — (b) 학습 권리가 있는 뉴스 텍스트 (Benzinga 직접 계약, SAMPLE_EXPANSION 10절)를 사야 합니다.
3. 8-K 첨부 보도자료 (Exhibit 99.1) 본문을 쓰면 방향을 읽을 수 있지만 "본문 저장 안 함" 원칙의 결정이 먼저입니다 (SAMPLE_EXPANSION 6절 3번).

## 8. 할 일 (제안, 승인 뒤)

| 순서 | 일 | 칸 | 호출 |
|---|---|---|---|
| 1 | 표본 60종목 (대·중·소 각 20)으로 8-K 항목 분포·건수 실측 (`--edgar-history` + `collection_status --by-entity`) | 소유자 PC 실행 + DATA_SOURCE 집계 | SEC (User-Agent) |
| 2 | 8-K 항목 코드·report_nm → event_type 힌트 규칙 (4절) | DIDM_DEV (규칙) / DATA_SOURCE (항목 코드 정규화) | 없음 |
| 3 | GDELT 거르기 수집 옵션 (날짜 창·조직 이름·주제) | DATA_SOURCE | GDELT |
| 4 | 820종목 × 2015~2024 8-K 전체 수집 | 소유자 PC | SEC |
| 5 | OpenDART 표본 종목 회사별 수집 (corp_code 지정이면 3개월 제한 없음, 최대 100개씩) | 소유자 PC | OpenDART |

## 9. 미검증

- GKG 하루 건수·파일 크기, GKG `page_title`이 2015년 초부터 채워지는지, 주제 (themes) 이름 목록.
- EDGAR 공개 지연 (acceptance → 공개), 종목당 연간 8-K 수, 7.01·8.01 비중.
- OpenDART report_nm 문구 목록 (4절은 부분 문자열 예시), 요청 한도의 집계 기간.
- BigQuery 경로의 요금·약관.
