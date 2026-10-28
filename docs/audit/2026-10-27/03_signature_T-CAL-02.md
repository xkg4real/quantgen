# 소유자 서명 기록: T-CAL-02

소유자가 2026-10-28 Claude Code 채팅으로 보낸 서명서를 그대로 옮겼습니다. Claude는 이 서명서에 따라 `tools/sign_calendars.py`로
서명을 기록했습니다. 실행 시 `--expect`로 초안 지문 4개를 확인했습니다.

## 서명서 원문

```
[QUANTGEN 달력 서명서 · T-CAL-02]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 초안 지문:
  [v] holidays_KRX.yaml    v1.0.0   9c67594f0717fd8aad8161bc5db87609
  [v] holidays_NYSE.yaml   v1.0.0   acb21e1c20b929648fd0085a456ad5e1
  [v] holidays_FED.yaml    v1.0.0   a1a6168be27f7a4b9fb1f44a241db8cb
  [v] holidays_SIFMA.yaml  v1.0.0   43e5bdc9cbf9ca3ed04f0aa462e5e7b2

확인 사항:
  [v] 2027년 휴장일과 조기폐장 날짜 (감사 보고서 4절 그림)
  [v] 출처 링크 (감사 보고서 8절)
  [v] CAL-14: 2018·2019·2020년 12월 24일 연준 이사회 휴무 (2026-10-28 소유자 확인)
  [v] KRX가 12월에 낼 2027년 휴장일 공지가 이 파일과 다르면 새 버전으로 다시 서명한다

서명 문장:
  "나 Geon Koh는 위 4개 파일의 날짜와 출처를 확인했으며, 이 파일들에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

## 기록 결과

| 파일 | 버전 | signed_utc | md5 |
|---|---|---|---|
| holidays_KRX.yaml | 1.0.0 | 2026-10-28T06:35:52Z | `ec68c21ffe77581fd51b2b4291be658a` |
| holidays_NYSE.yaml | 1.0.0 | 2026-10-28T06:35:52Z | `6ab0a539ee0461c20f8ee0d1ca50b395` |
| holidays_FED.yaml | 1.0.0 | 2026-10-28T06:35:52Z | `6c69a8acd75a44ed6c527c2f676b58aa` |
| holidays_SIFMA.yaml | 1.0.0 | 2026-10-28T06:35:52Z | `219f2a46ff84b405552c0e958e39fede` |

- **기한 대비:** 서명 시각은 기한(2026-11-01T00:00:00Z)보다 앞섭니다.
- **확인한 것:** 서명 도구는 기록 직후 로더로 네 파일을 다시 읽었고, 모두 정상적으로 로드됐습니다.
- **확인하지 않은 것:** 테스트 모음은 소유자가 실행을 중단해서 서명 후에는 아직 돌리지 않았습니다.
