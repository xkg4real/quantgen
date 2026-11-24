# 공시 사건 유형 규칙 V0 (DS-9, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 DS-9). 코드: `core/didm/ingest/event_rules.py` (표의 유일한 코드 사본), 시험: `tests/didm_event_rules_acceptance.py` — **이 문서의 표와 코드 상수가 다르면 시험이 실패합니다.**
- 근거: `STAGE2_EVENT_SAMPLE_PLAN_2026-11-24.md` 4절 힌트 표. 사건 유형은 `core/didm/llm/schema.py` `EventType` (14개 + none).
- 이것은 **힌트**입니다. 공시는 주체가 곧 대상이고 항목·보고서명이 사건 종류를 말해 주지만, 좋은 소식인지 나쁜 소식인지는 말하지 않습니다 (D15 7절).

## 1. 규칙

1. 한 제출에 유형이 여럿이면 모두 돌려주되 **우선순위** 순으로, 중복 없이. 첫 번째가 주 유형 (`primary`).
   우선순위: `earnings` > `mergers_acquisitions` > `management` > `regulation_litigation` > `supply_chain`.
   이유: 시장 반응이 큰 것을 앞에 (실적 발표가 같은 제출의 임원 변경보다 가격에 먼저 반영된다는 가정 — 사전등록에서 바꿀 수 있음).
2. 맞는 항목·보고서명이 없으면 `none`. `none`은 다른 유형과 함께 나오지 않음.
3. 8-K 7.01 (Regulation FD), 8.01 (기타), 9.01 (첨부)은 `none`: 항목 코드만으로는 무슨 일인지 알 수 없고 본문은 저장하지 않음.
4. 정정공시 (8-K/A, OpenDART 정정 표시)는 **별개 사건**이고 `amendment = True`. 원 공시와 잇는 일은 DIDM_DEV 규칙.
5. 8-K가 아닌 서식 (10-K, 10-Q 등)은 이 규칙에서 `none` (정기 보고서는 따로 다룸).
6. OpenDART 보고서명은 공백을 지운 뒤 부분 문자열로 맞춤.

## 2. EDGAR 8-K 항목 → 유형

항목 번호와 이름은 SEC Form 8-K 기준이며, 이 환경에서는 sec.gov를 열지 않아 **원문 미확인** (이름은 일반적으로 알려진 것).

<!-- edgar-items:start -->
| 항목 | 유형 | 항목 이름 |
|---|---|---|
| `1.03` | regulation_litigation | 파산·법정관리 |
| `2.01` | mergers_acquisitions | 자산 취득·처분 완료 |
| `2.02` | earnings | 실적·재무 상태 |
| `3.01` | regulation_litigation | 상장폐지 통지·상장 규정 미충족 |
| `4.01` | regulation_litigation | 감사인 변경 |
| `4.02` | earnings | 기존 재무제표 신뢰 불가 (재작성) |
| `5.02` | management | 이사·임원 퇴임·선임 |
<!-- edgar-items:end -->

`none`으로 둔 항목 (예시, 표에 없는 항목은 모두 none): <!-- edgar-none:start -->`1.01`, `1.02`, `1.04`, `1.05`, `5.07`, `7.01`, `8.01`, `9.01`<!-- edgar-none:end -->. 1.01·1.02 (중요 계약 체결·종료)는 합병·공급 계약일 수 있으나 본문 없이는 구분 불가; 1.05 (사이버보안 사고)는 암호화폐 해킹과 직접 연결되지 않음.

## 3. OpenDART 보고서명 (부분 문자열) → 유형

실제 OpenDART 보고서명 목록과 대조하지 못했습니다 → **모든 행 미검증**. "임원"은 넣지 않음: "임원ㆍ주요주주특정증권등소유상황보고서" (내부자 지분 보고)를 경영진 변경으로 잘못 셀 수 있어서. "분할"만으로는 "주식분할"과 섞여 "회사분할"로 좁힘.

<!-- opendart-names:start -->
| 보고서명 부분 | 유형 | 상태 |
|---|---|---|
| `잠정실적` | earnings | 미검증 |
| `(잠정)실적` | earnings | 미검증 ("영업(잠정)실적" 형태; 괄호 때문에 위 줄로는 안 맞음) |
| `매출액또는손익구조` | earnings | 미검증 |
| `합병` | mergers_acquisitions | 미검증 |
| `회사분할` | mergers_acquisitions | 미검증 |
| `주식교환` | mergers_acquisitions | 미검증 |
| `영업양수` | mergers_acquisitions | 미검증 |
| `타법인주식및출자증권취득` | mergers_acquisitions | 미검증 |
| `대표이사변경` | management | 미검증 |
| `소송` | regulation_litigation | 미검증 |
| `횡령` | regulation_litigation | 미검증 |
| `배임` | regulation_litigation | 미검증 |
| `상장폐지` | regulation_litigation | 미검증 |
| `거래정지` | regulation_litigation | 미검증 |
| `단일판매ㆍ공급계약체결` | supply_chain | 미검증 (가운뎃점 문자 `ㆍ` 표기도 미검증) |
<!-- opendart-names:end -->

정정 표시 (보고서명 맨 앞, 미검증): <!-- opendart-amend:start -->`[기재정정]`, `[첨부정정]`, `[정정명령부과]`, `[정정제출요구]`<!-- opendart-amend:end -->.

## 4. 확인할 것

- 소유자 PC의 OpenDART 실측 목록 (`--opendart`)에서 보고서명 빈도를 뽑아 3절 표를 고침 (이름은 공시 제목이라 출력해도 됨; 회사명은 출력하지 않음).
- 8-K 항목 분포는 D13 `--by-entity`와 표본 60종목 실측 (D15 8절 1번)으로.
