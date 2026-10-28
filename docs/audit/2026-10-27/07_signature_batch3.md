# 소유자 서명 기록: 달력 3차 (holidays_CBOE · holidays_ECOS)

소유자가 2026-10-28 Claude Code 채팅으로 보낸 서명서를 그대로 옮겼습니다. 서명서 제출은 3차 제안을 승인한 것으로 처리했습니다.

Claude가 처리한 순서는 다음과 같습니다.

1. `calendar_batch3/proposed/`의 두 파일을 `core/calendars/data/`로 옮겼습니다.
2. MANIFEST의 해당 행을 1.0.0으로 올렸습니다.
3. `tools/sign_calendars.py`로 서명을 기록했습니다. `--expect`로 초안 지문 2개가 일치하는지 확인한 뒤 기록했습니다.

## 서명서 원문

```
[QUANTGEN 달력 서명서 · 3차 (holidays_CBOE · holidays_ECOS)]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 초안 지문:
  [v] holidays_CBOE.yaml   v1.0.0   42adf7c4ea0acb12c796e6c70090246a
  [v] holidays_ECOS.yaml   v1.0.0   ba7fbdafca12f7d6a420a6f76b81d04b

확인 사항:
  [v] CBOE = 서명된 NYSE 휴장일. 조기폐장은 13:15 ET.
      2026-05-25와 09-07은 GTH 시세가 있어도 공식 종가가 없으므로 휴장
  [v] ECOS = 서명된 KRX 휴장일(공휴일·노동절·12/31 외환시장 연말 휴장)
  [v] 2025년 이전 ECOS, 2025년 이전 CBOE는 이 버전 범위 밖이다

서명 문장:
  "나 Geon Koh 는 위 2개 파일의 날짜와 출처를 확인했으며, 이 파일들에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

## 기록 결과

| 파일 | 버전 | signed_utc | md5 |
|---|---|---|---|
| holidays_CBOE.yaml | 1.0.0 | 2026-10-28T11:28:41Z | `5d9724d67cca74db7fa3b490bf805c78` |
| holidays_ECOS.yaml | 1.0.0 | 2026-10-28T11:28:41Z | `603170d21048f8b81649324996887595` |

## 검증 (실제 서명 데이터 기준)

**테스트**

- `tests.macro_m1_calendars`: 18/22 통과, 실패 0, 미실행 4
- `tests.macro_m1_integration`: 7/7 통과

**입력별 결과**

| 입력 | 결과 |
|---|---|
| ECOS_1530_CLOSE (forward_sim, R-29) | 읽힘. `PITValue` 1391.2. 서명 전에는 `MissingInput`이었음 |
| VIXCLS | 데이터 지연 판단이 정상 동작함 (stale=False) |
| CPIAUCSL, PCEPILFE | 아직 수집 단계에서 막힘. BLS·BEA 설계안 A 승인을 기다림 |

**서명된 파일:** 모두 9개입니다.
CBOE, ECOS, FED, KRX, NYSE, SIFMA, kr_sessions, publication_schedules, source_skipped
