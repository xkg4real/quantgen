# DS-4c 준비: CME FedWatch 종가판 커넥터 설계 (D5, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 D5). **설계만** 담았습니다. 코드와 실제 호출은 소유자 답 (OA-31, D14 질문 2: 가입·요금·이력 저장 허용 범위)이 온 뒤에 합니다.
- 근거: `docs/didm/VENDOR_EVAL_2026-11.md` 2절 Q열, 3절 CME 행 (이력·가격), 4절 약관 질문, 5절 키 이름; `docs/didm/PREREG_V0.md` "예상 대비 충격" 행 (FedWatch 확률 변화 사용, 승인 P3); 로드맵 `docs/nautilus_bridge/REMAINING_WORK_2026-11-17.md` DS-4c.
- **미검증 표시:** CME FedWatch API의 인증 방식, 응답 필드 이름, 종가판 갱신 시각, 요금은 이 세션에서 공식 문서로 확인하지 못했습니다. 그래서 아래 설계는 공급사 필드에 기대지 않는 **내부 정규 형식**을 먼저 정하고, 공급사 응답은 어댑터 하나에서만 이 형식으로 바꿉니다. 실제 필드는 소유자가 가입한 뒤 문서와 첫 응답 한 건으로 어댑터에만 반영합니다.

## 1. 무엇을 받는가

FOMC 회의별 목표금리 구간 확률. 하루 (거래일) 하나의 판을 받습니다.

| 개념 | 설명 |
|---|---|
| 거래일 `trade_date` | 확률을 계산한 선물 정산일 (종가판 기준) |
| 회의일 `meeting_date` | 확률이 가리키는 FOMC 회의 (보통 앞으로 8~12개) |
| 구간 `lower_bp`, `upper_bp` | 목표금리 구간, bp 정수 (예: 425–450) |
| 확률 `p` | 그 회의 뒤 목표금리가 그 구간일 확률, 0~1 |

## 2. 내부 정규 형식 (어댑터 출력)

```
FedWatchDay(
  trade_date: date,                      # 정산일
  published_at: datetime (UTC, aware),   # 3절 규칙
  meetings: tuple[MeetingDist, ...],     # 회의일 오름차순, 중복 없음
  source_variant: "eod",                 # 장중판은 V0 범위 밖
)
MeetingDist(meeting_date: date, buckets: tuple[(lower_bp:int, upper_bp:int, p:float), ...])
```

검사 (어기면 고치지 않고 거부, 거부 수를 셈):

1. 확률 각각 0~1, 회의별 합 1 (허용 오차 1e-4; 공급사가 퍼센트로 주면 어댑터가 /100).
2. 구간은 `upper_bp - lower_bp = 25`, 서로 겹치지 않음, 오름차순.
3. `meeting_date > trade_date` (지난 회의는 들어오면 거부).
4. `published_at`은 시간대가 있어야 하고 `trade_date`보다 앞서면 거부.

## 3. 시점 규칙 (point-in-time)

| 시각 | 값 | 이유 |
|---|---|---|
| `valid_at` | `trade_date` 00:00 UTC | 확률이 가리키는 거래일 (ALFRED와 같은 날짜 규칙) |
| `published_at` | 공급사가 판의 생성·갱신 시각을 주면 그 값. 주지 않으면 **보수적으로 `trade_date` 다음 날 00:00 UTC** | 종가판은 정산 뒤 나옴. 정확한 공개 시각을 모르면 늦게 잡아야 미래 정보 누출이 없음 (사전등록 원칙) |
| `received_at` | 수집기가 받은 시각 | 저장소 규칙 그대로 |

- 과거 이력 (2015~)을 한꺼번에 받으면 `received_at`은 전부 수신 당일입니다. 과거 시점 재현은 `published_at` 기준으로 합니다 (`COLLECTION_STATUS_GUIDE_2026-11-24.md` 2절과 같은 주의).
- 같은 거래일을 다시 받아 값이 다르면 (공급사 정정) 덮어쓰지 않고 새 행으로 쌓습니다 (저장소 규칙).

## 4. 저장 행 (`core/didm/ingest/fedwatch.py` 예정)

한 행 = 거래일 × 회의 하나.

| 필드 | 값 |
|---|---|
| `source_id` | `cme-fedwatch` |
| `kind` | `fedwatch_meeting_dist` |
| `item_id` | `{meeting_date}@{trade_date}` |
| `payload` | `meeting_date`, `trade_date`, `buckets` [[lower_bp, upper_bp, p], ...], `p_hike`, `p_cut`, `p_hold` (현재 구간 대비, 어댑터가 받은 "현재 목표 구간"으로 계산; 모르면 None), `expected_mid_bp` (Σ p × 구간 중간값), `parser` `fedwatch-v0.1` |

`p_hike`·`p_cut`·`expected_mid_bp`는 PREREG "예상 대비 충격"의 확률 변화 계산에 쓸 파생값입니다. 계산은 저장 시 한 번만 하고, 원래 구간 확률도 함께 남깁니다.

## 5. 파일 배치 (D7-G 경계 지킴)

| 파일 | 역할 | 네트워크 |
|---|---|---|
| `data/didm/fedwatch.py` | HTTP·인증 (키 이름 `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET`, `data/didm/keys.py` RESEARCH_KEYS에 이미 있음). 응답 JSON을 그대로 돌려줌. 오류는 `SourceError` + `safe_detail` (키 가림) | 있음 |
| `core/didm/ingest/fedwatch.py` | 어댑터 (공급사 JSON → `FedWatchDay`)와 저장 행 변환, 2절 검사 | 없음 |
| `tools/didm/collect_daily.py` | `--fedwatch [YYYY-MM-DD ...]` (거래일 생략 시 최신판), `--fedwatch-from/--fedwatch-to` (이력, 쪽 상한) | 옵션 실행 시만 |
| `tests/didm_fedwatch_acceptance.py` | 6절 시험 | 없음 |

`core/gateway`, `core/credentials`는 건드리지 않습니다.

## 6. 시험 계획 (네트워크 없음, 합성 자료)

| 번호 | 확인 | 합성 입력 |
|---|---|---|
| T1 | 정상 판 → 회의 수만큼 행, `item_id`·`valid_at`·`published_at` 규칙 | 회의 2개 × 구간 3개 |
| T2 | 퍼센트 입력 (합 100)을 0~1로 바꿈 | 같은 판, 값 ×100 |
| T3 | 확률 합 ≠ 1, 음수, 1 초과 → 거부 | 각각 하나씩 |
| T4 | 구간 폭 ≠ 25bp, 겹침, 역순 → 거부 | 각각 |
| T5 | 지난 회의 (`meeting_date ≤ trade_date`) → 거부 | 하나 |
| T6 | 공개 시각 없음 → 다음 날 00:00 UTC; 있으면 그 값; 시간대 없음 → 거부 | 세 경우 |
| T7 | `p_hike`/`p_cut`/`p_hold`/`expected_mid_bp` 계산 | 현재 구간 425–450, 확률 0.2/0.7/0.1 |
| T8 | 같은 거래일 정정 → 저장소에 두 판, `as_of` 이전 시각은 옛 값 | 두 번 수신 |
| T9 | HTTP 클라이언트: 키가 URL·출력에 없고 헤더 (또는 공급사 지정 방식)에만; 401/403 문구에서 키 가림 | `session.get` 모의 |
| T10 | 수집기 옵션: 주입한 fetch로 거래일 범위·쪽 상한, 완료 여부 출력 | 주입 함수 |

T9의 인증 방식만 실제 문서 확인 뒤 고정합니다. 나머지는 지금 형식으로 그대로 씁니다.

## 7. 소유자 답 뒤 순서

1. 소유자: 종가판 가입 여부·요금 확인 (OA-31), 키 발급, `setx CME_FEDWATCH_API_ID` / `setx CME_FEDWATCH_API_SECRET`. 이력 저장이 약관상 허용되는지 확인 (D14 질문 2, VENDOR_EVAL 4절). 법률 자문이 아닙니다.
2. DATA_SOURCE: 공식 API 문서로 인증·필드·갱신 시각 확인 → 어댑터 작성 → T1~T10 → 소유자 PC에서 최신판 1회 + 하루치 이력 1회 실행 안내.
3. 대안 (가입하지 않을 때): 30일 연방기금금리 선물 (ZQ) 정산가로 같은 확률을 직접 계산하는 길. FedWatch 공개 방법론을 따르면 가능하지만, 선물 정산가 출처와 그 이용 조건을 따로 확인해야 해서 이 문서 범위 밖입니다 (VENDOR_EVAL 3절 "직접 계산 길은 미검토").
