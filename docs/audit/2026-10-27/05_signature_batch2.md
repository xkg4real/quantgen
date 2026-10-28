# 소유자 서명 기록: 달력 2차 (kr_sessions · publication_schedules · source_skipped)

소유자가 2026-10-28 Claude Code 채팅으로 보낸 서명서를 그대로 옮겼습니다. 서명서 제출은 2차 감사 제안을 승인한 것으로 처리했습니다.

Claude는 다음 순서로 기록했습니다.

1. `calendar_batch2/proposed/`의 세 파일을 `core/calendars/data/`로 옮겼습니다.
2. MANIFEST의 해당 행을 1.0.0으로 올렸습니다.
3. `tools/sign_calendars.py`로 서명을 기록했습니다. 이때 `--expect`로 초안 지문 3개를 확인했습니다.

## 서명서 원문

```
[QUANTGEN 달력 서명서 · 2차 (kr_sessions · publication_schedules · source_skipped)]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 초안 지문:
  [v] kr_sessions.yaml            v1.0.0   94c8d4f57fe44fb20f31d5fff2bce567
  [v] publication_schedules.yaml  v1.0.0   14100e737e79154b737a8814f1c23675
  [v] source_skipped.yaml         v1.0.0   d4ac8e4147d6642859b3210881167f2e

확인 사항:
  [v] 2027-11-18 수능일 추가, 1995~1998 점심 휴장 11:30~13:00 (KS-01, KS-02)
  [v] 성금요일 예외를 H.15 전체로 확대, 2027-03-26 추가 (SS-01, SS-02)
  [v] 서명 후에도 VIX·BLS·BEA·ECOS 입력은 막혀 있음을 안다 (PS-02)
  [v] 2008년 이전 수능일, 1998년 이전 토요일 마감 시각, 2015년 이전 랜덤엔드 연장은 공백으로 둔다
      (holidays_KRX가 2026년부터라 지금은 쓰이지 않음)
  [v] KRX의 수능일 시간 공지가 설정(10:00~16:30)과 다르면 새 버전으로 다시 서명한다

서명 문장:
  "나 Geon Koh는 위 3개 파일의 날짜·시각·출처를 확인했으며, 이 파일들에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

## 기록 결과

| 파일 | 버전 | signed_utc | md5 |
|---|---|---|---|
| kr_sessions.yaml | 1.0.0 | 2026-10-28T08:47:25Z | `e72837e0c7b08a3cdacdd322c52669cc` |
| publication_schedules.yaml | 1.0.0 | 2026-10-28T08:47:25Z | `ee47ef6cb053f1fb0be7c39a3ae768b8` |
| source_skipped.yaml | 1.0.0 | 2026-10-28T08:47:25Z | `ed225d30c16c1dc641389ad39459577f` |

## 검증

- 서명 도구가 기록 직후 세 파일을 로더로 다시 읽어 정상 로드를 확인했습니다.
- `tests.macro_m1_calendars`: 18/22 통과, 실패 0, 미실행 4
- `tests.macro_m1_integration`: 7/7 통과
- `macro_m9_lab::test_t_crypto_01`: PASS

**서명 후 상태 (2026-10-28 기준)**

| 시장 | 상태 | 남은 거래일 | 비고 |
|---|---|---|---|
| US | signed=True | 292 | |
| KR | signed=False | 289 | `kr_regime_tags`만 남음 |

KR의 2026-11-19(수능) 결정 시각은 07:30Z(16:30 KST)입니다.
