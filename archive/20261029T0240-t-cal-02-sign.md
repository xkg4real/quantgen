---
status: checkpoint
reason: milestone
from: claude
task: t-cal-02-sign
cycle: 2026-10-27
done_ids: none
next_ids: ①-2
updated_at: 2026-10-29T02:40:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/relaxed-cerf-az755o
work_commit: 2b2cbbc
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: unknown
session: https://claude.ai/code/session_016uB1jeWXD51mcf3fjeTN6g
---

# 인수인계: T-CAL-02 2027년 달력 4개 파일 서명 (①-2)

## 0. 한 줄 요약

감사(방안 A)는 끝나 `main`에 있습니다(PR #5, 커밋 0849ca9). 지금은 소유자 결정 3건(패치 승인, CAL-14 포함 여부, 서명 문장)을
기다리는 동안 서명 적용 스크립트와 서명 뒤 테스트를 준비하고 있습니다. 서명 기한은 `signed_utc` < 2026-11-01T00:00:00Z
(한국 시간 11월 1일 09:00)입니다.

## 1. 목표와 완료 조건

- **사용자 요청 (원문 그대로):**
  > T-CAL-02 세션의 연장입니다
- **앞선 판정 (원문, `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`):**
  > 예, 다만 다음 첨부한 파일(감사파일)을 우선시해서 달력 implementation을 승인합니다.

  > A로 시작하겠습니다. 그리고 지금 작업을 시작해주세요
- **완료 조건:** `core/calendars/data/holidays_{KRX,NYSE,FED,SIFMA}.yaml`이 소유자 서명(v1.0.0)으로 실제 로더에 로드되고,
  `signed_utc` < 2026-11-01T00:00:00Z, `covers.to` >= 2027-12-31, MANIFEST 행에 md5·서명자·T-CAL-02가 있음.
  `test_cal02_2027_files_signed_before_2026_11_01`이 NOT_RUN이 아니라 PASS.
- **범위 밖:** `kr_sessions`, `kr_regime_tags`, `publication_schedules`, `source_skipped`와 나머지 달력 파일의 서명
  (보고서 6절). 감사 요청서의 나머지 항목(D-01~D-05, P-01, C-01, V-01, 공급사 조사).

## 2. 근거

| 종류 | 위치 | 이 작업에서 쓰는 부분 |
|---|---|---|
| 감사 보고서 | `docs/audit/2026-10-27/01_calendar_T-CAL-02.md` | 3절 발견사항 CAL-01~15, 7절 소유자 결정과 서명 절차 |
| 제안 파일 | `docs/audit/2026-10-27/calendar_T-CAL-02/proposed/` | 서명할 v1.0.0 파일 4개 |
| 소유자 판정 | `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` ①-2 | 감사 우선 조건부 승인, 방안 A |
| 스펙 | `research_notes/QUANTGEN v2 integration map/spec_M1_calendars.md` | T-CAL-02 기한 조항 |
| 로더 | `core/calendars/store.py` `parse_file`, `content_md5` | 서명 검증 규칙(행·파일 서명, md5, MANIFEST) |
| 테스트 | `tests/macro_m1_calendars.py` `test_cal02_2027_files_signed_before_2026_11_01`, `test_cal01_shipped_drafts_...` | 서명 뒤 바꿀 테스트 |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안과 이유 |
|---|---|---|
| 서명 전 준비만 함(적용 스크립트, 테스트 초안, 가짜 서명 사본에서 검증) | 기한이 짧아 서명 문장을 받으면 바로 적용하려고 | 서명 없이 `core/calendars/data` 수정: 요청서 7절 8번과 로더 규칙 위반 |
| 공식 원문 재확인은 하지 않음 | `www.federalreserve.gov`, `www.sifma.org`, `ir.theice.com` 등이 이 세션 네트워크 정책에서 여전히 차단됨(2026-10-29 확인) | — |

## 4. 진행 상황

- [x] 감사 보고서와 제안 패치 — 커밋 0849ca9 (`main`, PR #5)
- [ ] ①-2 서명 적용 스크립트 `apply_signature.py` ← **여기서 작업 중**
- [ ] ①-2 서명 뒤 테스트 변경 초안과 가짜 서명 사본 검증
- [ ] ①-2 소유자 결정 3건 수령 → 서명 적용, 테스트, 커밋, 푸시

**마지막으로 통과한 검증:**

```
python -m tests.macro_m1_calendars   (scipy를 넣은 임시 venv)
16/21 passed, 0 failed, 5 not run
python -m tests.macro_m1_integration
7/7 passed
```

## 5. 중단 지점

없음. 커밋되지 않은 변경 없음.

## 6. 다음 할 일 (순서대로)

1. ①-2 소유자 결정 3건이 없으면 기다립니다(보고서 7절). 서명 문장 없이 서명 필드를 쓰지 않습니다.
   — 완료 기준: 서명 문장, `signed_off_by` 표기, CAL-14 포함/제외를 원문으로 받음
2. ①-2 받으면 `python docs/audit/2026-10-27/calendar_T-CAL-02/apply_signature.py --signer "<표기>" --signed-utc <소유자 메시지 UTC> --cal14 include|exclude`
   (스크립트가 커밋된 뒤) — 완료 기준: 4개 파일이 로더에 로드됨
3. ①-2 테스트 변경을 넣고 `python -m tests.macro_m1_calendars`, `python -m tests.macro_m1_integration` 통과,
   OWNER_RULINGS_LOG에 서명 문장 원문 기록, 커밋, 푸시 — 완료 기준: T-CAL-02 기한 조항 PASS

## 7. 주의사항 / 하지 말 것

- 소유자 서명 문장 없이 `signed_off_by`, `signed_utc`, `md5`를 쓰지 않습니다(가짜 서명은 임시 사본에서만 씁니다).
- `signed_utc`는 소유자 메시지 시각(UTC)입니다. 스크립트가 정한 시각을 쓰지 않습니다.
- 나머지 달력 파일(`kr_sessions` 등)은 서명 대상이 아닙니다.

## 8. 사용자에게 물어야 할 것

- 결정 1: CAL-01~CAL-15를 반영한 `proposed/` 4개 파일 승인 여부
- 결정 2: FED 추정 3건(CAL-14) 포함/제외 (권장: 포함)
- 결정 3: 서명 문장과 `signed_off_by` 표기

## 9. 이어받는 에이전트에게 주는 지시문

```
너는 xkg4real/quantgen 레포의 "T-CAL-02 2027년 달력 4개 파일 서명 (①-2)" 작업을 이어받는다.
1. handoff 브랜치의 CURRENT.md, AGENTS.md, LEDGER.md를 먼저 읽어라. LEDGER.md에 있는 ID는 다시 하지 마라.
2. CURRENT.md의 status를 taken으로, from을 gpt로 바꾸고 updated_at을 갱신해 handoff 브랜치에 push해라.
3. AGENTS.md 2절 5번에 따라 시작 지점을 정해 gpt/t-cal-02-sign 브랜치를 만들어 작업해라. 보통은 claude/relaxed-cerf-az755o의 work_commit이다.
4. docs/audit/2026-10-27/01_calendar_T-CAL-02.md 7절을 읽어라. 소유자의 서명 문장(원문)이 없으면 서명 필드를 절대 쓰지 말고 8절 질문을 사용자에게 하라. 서명 문장이 있으면 6절 2~3번을 그대로 실행하라.
5. ID 하나를 끝낼 때마다 LEDGER.md에 한 줄을 덧붙이고 CURRENT.md를 같은 양식으로 갱신해라. 끝나거나 멈출 때, 늦어도 화요일 17:00(KST) 전에 status를 returned로 바꿔라.
```

## 10. 결과 확인 방법

```
python -m core.calendars.store        # holidays_KRX/NYSE/FED/SIFMA가 signed, v1.0.0
python -m tests.macro_m1_calendars    # test_cal02_2027_files_signed_before_2026_11_01 PASS
```
