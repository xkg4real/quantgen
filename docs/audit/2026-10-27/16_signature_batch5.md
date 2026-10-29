# 소유자 서명 기록: 달력 5차 (release_calendar)

소유자가 2026-10-29 Claude Code 채팅으로 보낸 서명서를 그대로 옮겼습니다. 서명서 제출은 5차 감사 제안(`12_release_calendar.md`)과 체크한 코드 패치를 승인한 것으로 처리했습니다.

Claude는 다음 순서로 기록했습니다. 감사 보고서 7절의 순서입니다.

1. `calendar_batch5/proposed/release_calendar.yaml`을 `core/calendars/data/`로 옮겼습니다.
2. `MANIFEST.yaml`에 `release_calendar.yaml` 행을 추가했습니다(1.0.0, test_ids `T-AVAIL-01`).
3. `calendar_batch5/proposed_code.diff`를 `git apply`로 적용했습니다. 체크한 3건이 모두 들어 있습니다.
   - F-01: `adapter.py` 행별 발표 시각
   - F-02: `publication.py` `usable_at` 탐색 시작점
   - `store.py`: `COVERAGE_FILES["US"]`에 `release_calendar` 추가
4. `tools/sign_calendars.py`로 서명을 기록했습니다. 기록 전에 `--expect`로 초안 지문을 확인했습니다.

## 서명서 원문

```
[QUANTGEN 달력 서명서 · 5차 (release_calendar)]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 초안 지문:
  [v] release_calendar.yaml   v1.0.0   1faf621a5b443f1c9f3627c2a98f1054
      (264행: CPI 35 · EMPSIT 36 · PIO 36 · CLAIMS 157; 2025-01-01~2027-12-31)

확인 사항:
  [v] 과거 발표일은 ALFRED 최초 vintage와 공식 일정이 일치함 (124건, 불일치 0)
  [v] 2025 셧다운: 10월 CPI 행 없음, 10월 고용 → 2025-12-16, 실업수당 7주 → 2025-11-20 (F-03)
  [v] BEA 10:00 ET 발표 4건(2025-04-30, 2025-12-05, 2026-01-22 ×2)을 행의 시각으로 기록 (F-01)
  [v] 2025-12-24 실업수당 발표(연방 휴무일이지만 실제 발표) 유지 (F-05)
  [v] 2028년 버전은 2027-12-22 전에 서명해야 함을 확인 (F-06)

결정:
  2027년 실업수당 52행 (규칙 기반, C등급) (F-04):
    [v] 넣는다 (권고)     [ ] 뺀다 (지문이 바뀌어 서명서를 다시 받음)
  코드 패치:
    [v] F-01 adapter.py 행별 발표 시각 적용 (필수)
    [v] F-02 publication.py usable_at 탐색 시작점 (권고)
    [v] store.py US 커버리지 대상에 release_calendar 추가 (A안 승인 범위)

서명 문장:
  "나 Geon Koh는 위 파일의 발표일·시각·출처를 확인했으며, 이 파일에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

## 기록 결과

| 파일 | 버전 | 행 | signed_utc | md5 |
|---|---|---|---|---|
| release_calendar.yaml | 1.0.0 | 264 | 2026-10-29T02:05:33Z | `0d89f161ac0b61712b2c1ed25bc9eadb` |

## 검증

- **테스트:**
  - `tests.macro_m1_integration`: 8/8 통과
  - `tests.macro_m1_calendars`: 18/22 통과, 실패 0, 미실행 4. 미실행은 원본 데이터나 소유자 자료가 없어서입니다.
- **모의 서명 재실행** (`calendar_batch5/simulate_signed.py`, 패치된 코드): 실패 0입니다.
  - BEA 10:00 ET 발표가 행의 시각대로 들어갑니다. PCEPILFE 2025-03분은 2025-04-30 14:00Z, 2025-10분은 2026-01-22 15:00Z입니다.
- **US 상태 (2026-10-29):** `signed=True`, 남은 거래일 291, 경보 없음.
  - 커버리지 대상은 NYSE, FED, SIFMA, publication_schedules, source_skipped, release_calendar입니다.
- **전체 매크로 테스트:** 6차 서명까지 기록한 뒤 한 번에 돌렸습니다. 결과는 `17_signature_batch6.md`에 있습니다.

## 남은 일

- **2028년 판(F-06):** 2027-12-22 전에 서명해야 합니다. 그 뒤로는 근원 PCE(PCEPILFE) 읽기가 막혀 헤지 크레딧이 꺼집니다.
- **거버넌스 로그:** `calendar_change` 이벤트는 기록하지 않았습니다. 운영 로그(`<macro_dir>/governance_events.jsonl`)가 소유자 PC에 있기 때문입니다. 소유자 PC에서 `record_calendar_changes`로 남깁니다.
