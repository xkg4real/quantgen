# 소유자 서명 기록: 달력 4차 (kr_regime_tags)

소유자가 2026-10-28 Claude Code 채팅으로 보낸 서명서를 그대로 옮겼습니다. 서명서 제출은 4차 감사 제안을 승인한 것으로 처리했습니다.

Claude는 다음 순서로 기록했습니다.

1. `calendar_batch4/proposed/kr_regime_tags.yaml`을 `core/calendars/data/`로 옮겼습니다.
2. MANIFEST의 해당 행을 1.0.0으로 올렸습니다.
3. `tools/sign_calendars.py`로 서명을 기록했습니다. 기록 전에 `--expect`로 초안 지문을 확인했습니다.

## 서명서 원문

```
[QUANTGEN 달력 서명서 · 4차 (kr_regime_tags)]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 초안 지문:
  [v] kr_regime_tags.yaml   v1.0.0   a43bd54cdd98f56a7f857fa96687e446

확인 사항:
  [v] 점심 휴장 1995~1998 11:30-13:00 (RT-01)
  [v] 공매도: 2011-08-10 시작, 금융주 금지 2009-06-01~2013-11-13을 partial_ban_financials로 표시 (RT-02)
  [v] 랜덤엔드: 2005-01-26 이전 none (RT-03)
  [v] fx_regime: market_average_rate / peg_1997(스펙) / free_float (RT-04)
  [v] 미확인으로 남긴 스펙 값을 그대로 둔다
      (1995~2019 거래세 0.30, ETF 1원 호가 2023-12-11, 2026-07-16 규칙, 2026-07-06 24시간 외환)
  [v]T-REGIME-01 전 기간 기대값 파일은 별도 과제로 남는다

서명 문장:
  "나 Geon Koh는 위 파일의 태그 값·시행일·출처를 확인했으며, 이 파일에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

## 기록 결과

| 파일 | 버전 | signed_utc | md5 |
|---|---|---|---|
| kr_regime_tags.yaml | 1.0.0 | 2026-10-28T13:27:00Z | `8336f69ca98c450c28eaaeea37495638` |

## 검증

**테스트**

- `tests.macro_m1_calendars`: 18/22 통과, 실패 0, 미실행 4
  - `test_regime01_point_clauses_and_fail_closed`: PASS
  - 전 기간 기대값 테스트(`test_regime01_full_range_expected_values_file`)는 기대값 파일이 아직 없어 미실행입니다. 소유자 과제로 남아 있습니다.
- `tests.macro_m1_integration`: 7/7 통과
- `macro_m9_lab::test_t_crypto_01`: PASS

**시장 상태 (2026-10-28)**

| 시장 | signed | 남은 거래일 | ARM 전제조건 |
|---|---|---|---|
| KR | True | 289 | True |
| US | True | 292 | True |

**KR 태그 예시 (2026-10-28)**

| 태그 | 값 |
|---|---|
| 가격제한폭 | 0.30 |
| 거래세 | 0.20% |
| 공매도 | none |
| 원/달러 거래시간 | 24h |
| 랜덤엔드 | unconditional_le_30s |

**서명된 달력 파일:** 16개 중 10개

남은 6개는 JPX, SSE, HKEX, TWSE, CME 휴장일과 market_closes입니다. KR·US 운영에는 필요하지 않습니다.
