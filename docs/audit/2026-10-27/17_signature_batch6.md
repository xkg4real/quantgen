# 소유자 서명 기록: 달력 6차 (JPX · SSE · HKEX · TWSE · CME 휴장일, market_closes)

소유자가 2026-10-29 Claude Code 채팅으로 보낸 서명서를 그대로 옮겼습니다. 서명서 제출은 6차 감사 제안(`14_calendar_batch6.md`)을 승인한 것으로 처리했습니다.

Claude는 다음 순서로 기록했습니다.

1. `calendar_batch6/proposed/`의 6개 파일을 `core/calendars/data/`로 옮겼습니다.
2. `MANIFEST.yaml`의 해당 6행을 1.0.0으로 올렸습니다. test_ids는 바꾸지 않았습니다(T-XMKT-01, CME는 T-AVAIL-01).
3. `tools/sign_calendars.py`로 서명을 기록했습니다. 기록 전에 `--expect`로 초안 지문 6개가 맞는지 확인했습니다.

## 서명서 원문

```
[QUANTGEN 달력 서명서 · 6차 (JPX · SSE · HKEX · TWSE · CME · market_closes)]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 초안 지문:
  [v] holidays_JPX.yaml    v1.0.0   7a59a8f5234bbb82961627c69aced063
  [v] holidays_SSE.yaml    v1.0.0   f6db741b0befcb4616ec848fafa4da01
  [v] holidays_HKEX.yaml   v1.0.0   0c6c54491d59b4d9ffe638f97afff15b
  [v] holidays_TWSE.yaml   v1.0.0   a6d054df859876c1061726f35560fd6e
  [v] holidays_CME.yaml    v1.0.0   c7fbab0afedac6a8c0bc870d147b6bb3
  [v] market_closes.yaml   v1.0.0   65896c0ef30da67167a22fe2826220a7

확인 사항:
  [v] 2027년 휴장일과 조기마감 (보고서 4절 그림)
  [v] 출처 링크 (각 행의 source_url, 보고서 9절)
  [v] HK-01: 홍콩 마감 16:10, 반일장 12:10 (종가 단일가 종료 시각; 2016-07-24 이전은 16:00)
  [v] SSE-27: 상하이 2027년 18일은 추정(C)이며, 국무원·SSE 공지가 나오면 새 버전으로 다시 서명한다
  [v] TW-27: 대만 2027-02-02·03 결제 전용일은 추정(C), 2026-07-10·10-23 태풍 휴장은 포함
  [v] CME-01: CME = 주가지수 선물 정산일. 미국 공휴일 단축 거래, 2025-01-09, 2026-04-03은 휴장.
      2027년은 서명된 NYSE 목록을 따르며 CME 공지가 나오면 다시 확인한다
  [v] SCOPE: 2025년 이전 이력은 이 버전 범위 밖이다

서명 문장:
  "나 Geon Koh 위 6개 파일의 날짜와 출처를 확인했으며, 이 파일들에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

## 기록 결과

| 파일 | 버전 | 행 | signed_utc | md5 |
|---|---|---|---|---|
| holidays_JPX.yaml | 1.0.0 | 54 | 2026-10-29T02:06:58Z | `bcc32846cb2e24d5c3a62928c466082f` |
| holidays_SSE.yaml | 1.0.0 | 55 | 2026-10-29T02:06:58Z | `e456838c578d04ff9ca6ff06ffe9fe9e` |
| holidays_HKEX.yaml | 1.0.0 | 51 | 2026-10-29T02:06:58Z | `303c93b40e529020c62bd1f149ccf946` |
| holidays_TWSE.yaml | 1.0.0 | 57 | 2026-10-29T02:06:58Z | `c3ef95bf79379b716fb52c9f3ec28958` |
| holidays_CME.yaml | 1.0.0 | 37 | 2026-10-29T02:06:58Z | `d707e9533bd61d995803a5ddbe6d8046` |
| market_closes.yaml | 1.0.0 | 4 | 2026-10-29T02:06:58Z | `bceb921be4b1419a3dc17a111ea3cd5d` |

## 검증

**달력 파일 17개가 모두 서명되어 로드됩니다.** 5차 `release_calendar`를 포함한 수입니다. `MANIFEST.yaml`의 파일 머리(세트 전체)는 아직 미서명이라 `calendar_version`은 `unsigned`로 찍힙니다.

**시장 상태 (2026-10-29 결정일 기준)**

| 시장 | signed | 남은 거래일 | 경보 | ARM 전제조건 | 결정 시각 (UTC) |
|---|---|---|---|---|---|
| KR | True | 288 | 없음 | True | 06:30 |
| US | True | 291 | 없음 | True | 20:00 |
| JP | True | 286 | 없음 | True | 06:30 |
| CN | True | 288 | 없음 | True | 07:00 |
| HK | True | 292 | 없음 | True | 08:10 (16:10 HKT, HK-01) |
| TW | True | 286 | 없음 | True | 05:30 |

**테스트:** 실제 저장소에서 매크로 테스트 모듈을 모두 돌렸습니다.

- **새로 생긴 실패는 없습니다.** 5차·6차 서명과 5차 코드 패치를 모두 반영한 저장소에서 38개 모듈을 돌렸고, 서명 전 기준선과 같았습니다.
  - `tests.macro_m1_calendars`: 18/22 통과, 실패 0, 미실행 4 (원본 데이터·소유자 자료 없음)
  - `tests.macro_m1_integration`: 8/8 통과
- **`macro_m0_harness`의 2건은 서명 전부터 있던 실패입니다.** 서명 전 `main`을 그대로 받은 사본에서도 같은 2건이 실패했습니다.
  - 등록표 동기화 T-OBS-03: `flet`이 없어 UI 테스트 모듈을 불러오지 못하는 환경 문제입니다.
  - `flet` 모듈 없음
- **나머지 서명 전부터 있던 실패도 그대로입니다.** 이번 서명과 무관합니다.
  - `macro_m8_pipeline::test_dry_run_end_to_end_on_the_local_cache`
  - `flet`이 필요한 UI 모듈 4개

## 남은 일

| 시기 | 할 일 |
|---|---|
| 2026년 11~12월 | 국무원·SSE 2027 공지가 나오면 SSE 2027년 18행을 바꾸고 새 버전(1.0.1)으로 다시 서명 |
| 곧 | TWSE 2027 일정표가 나오면 결제 전용일 2행 확인 |
| 2027년 중 | CME 2027 일정이 나오면 CME 2027년 10행 확인 |
| 12월 | KRX 2027 휴장 공지 확인(1차 서명 조건) |
| 2027년 9월 말까지 | 2028년 파일 서명. 6개 파일의 `warn`이 2027-10-04~08에 시작합니다 |

**다음 버전 과제:** 2025년 이전 이력(KR 공분산 기간)을 추가합니다.

**거버넌스 로그:** `calendar_change` 이벤트는 기록하지 않았습니다. 운영 로그가 소유자 PC의 `<macro_dir>`에 있기 때문입니다.
