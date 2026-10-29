# 소유자 서명 기록: 달력 세트 1.0.0 (MANIFEST.yaml 파일 머리)

## 근거

17개 파일이 모두 서명된 뒤, 세트 버전을 정해 서명할지 소유자께 물었습니다. 소유자는 2026-10-29 Claude Code 채팅에서 이렇게 답했습니다.

> 2. 저는 서명에 동의한 걸로 간주하셔서 (양식이 동일하다면) 이름란에 Geon Koh, 체크란에 "v" 표시를 넣으세요

이 지시에 따라 Claude는 1~6차와 같은 양식으로 서명서를 만들고, 이름란과 확인란을 채웠습니다. 소유자가 직접 써서 보낸 서명서가 아니라 **소유자 위임으로 채운 서명서**입니다.

## 세트를 이루는 파일 (서명 시점)

| 파일 | 버전 | md5 |
|---|---|---|
| holidays_CBOE.yaml | 1.0.0 | `5d9724d67cca74db7fa3b490bf805c78` |
| holidays_CME.yaml | 1.0.0 | `d707e9533bd61d995803a5ddbe6d8046` |
| holidays_ECOS.yaml | 1.0.0 | `603170d21048f8b81649324996887595` |
| holidays_FED.yaml | 1.0.0 | `6c69a8acd75a44ed6c527c2f676b58aa` |
| holidays_HKEX.yaml | 1.0.0 | `303c93b40e529020c62bd1f149ccf946` |
| holidays_JPX.yaml | 1.0.0 | `bcc32846cb2e24d5c3a62928c466082f` |
| holidays_KRX.yaml | 1.0.0 | `ec68c21ffe77581fd51b2b4291be658a` |
| holidays_NYSE.yaml | 1.0.0 | `6ab0a539ee0461c20f8ee0d1ca50b395` |
| holidays_SIFMA.yaml | 1.0.0 | `219f2a46ff84b405552c0e958e39fede` |
| holidays_SSE.yaml | 1.0.0 | `e456838c578d04ff9ca6ff06ffe9fe9e` |
| holidays_TWSE.yaml | 1.0.0 | `c3ef95bf79379b716fb52c9f3ec28958` |
| kr_regime_tags.yaml | 1.0.0 | `8336f69ca98c450c28eaaeea37495638` |
| kr_sessions.yaml | 1.0.0 | `e72837e0c7b08a3cdacdd322c52669cc` |
| market_closes.yaml | 1.0.0 | `bceb921be4b1419a3dc17a111ea3cd5d` |
| publication_schedules.yaml | 1.0.0 | `ee47ef6cb053f1fb0be7c39a3ae768b8` |
| release_calendar.yaml | 1.0.0 | `0d89f161ac0b61712b2c1ed25bc9eadb` |
| source_skipped.yaml | 1.0.0 | `ed225d30c16c1dc641389ad39459577f` |

**세트 지문:** `62e802f2d3d7f1f18bae5c3d7eac1cd0`

- MANIFEST 17행의 (파일, 버전, md5, 서명자)를 파일 이름순으로 정렬해 JSON으로 만든 값의 md5입니다.
- 이 지문은 이 문서에만 기록됩니다. 로더는 세트 지문을 검사하지 않고, 파일마다 md5와 서명을 검사합니다.

## 서명서

```
[QUANTGEN 달력 서명서 · 세트 1.0.0 (MANIFEST.yaml)]

서명자 표기 (signed_off_by): Geon Koh

서명 대상과 지문:
  [v] MANIFEST.yaml 세트 버전 1.0.0
      (파일 17개, 모두 v1.0.0; 세트 지문 62e802f2d3d7f1f18bae5c3d7eac1cd0)

확인 사항:
  [v] 17개 파일이 모두 소유자 서명으로 로드됨 (13_signature_register.md 2절)
  [v] 세트 버전 1.0.0이 event_calendar.calendar_version과 시장 상태의 version에 찍힘
  [v] 파일 하나라도 새 버전으로 다시 서명하면 세트 버전을 올려 다시 서명한다
      (예: SSE 2027 공지 반영 1.0.1 → 세트 1.0.1)

서명 문장:
  "나 Geon Koh는 위 17개 파일로 이루어진 달력 세트 1.0.0에 서명합니다."

서명 시각 (UTC): 2026-10-29T04:29:39Z (기록 시각)
```

## 기록 결과

`core/calendars/data/MANIFEST.yaml` 파일 머리를 다음처럼 바꿨습니다. 각 행은 그대로입니다.

| 항목 | 이전 | 이후 |
|---|---|---|
| version | 0.1.0-draft | 1.0.0 |
| signed_off_by | null | Geon Koh |
| signed_utc | null | 2026-10-29T04:29:39Z |
| status | UNSIGNED DRAFT ... (낡은 문구) | SIGNED SET v1.0.0 ... |

- `CalendarSet.version`이 `unsigned`에서 `1.0.0`으로 바뀌었습니다. 이 값이 `event_calendar.calendar_version`에 찍힙니다.
- **테스트 추가:** `test_cal01_shipped_drafts_...`에 세트 검사를 넣었습니다. 세트가 서명돼 있으면 다음을 확인합니다.
  - 모든 파일이 서명돼 있는지
  - `calendar_version`이 MANIFEST 버전과 같은지
  - 서명자가 테스트용 이름이 아닌지

## 검증

| 테스트 | 결과 |
|---|---|
| `tests.macro_m1_calendars` | 18/22 통과, 실패 0, 미실행 4 (세트 검사 포함) |
| `tests.macro_m1_integration` | 8/8 통과 |
| `tests.macro_m5_fills_events` (event_calendar 생성) | 9/14 통과, 실패 0, 미실행 5 |
| `tests.macro_m5_integration` | 5/6 통과, 실패 0, 미실행 1 |

**전체 매크로 테스트 38개 모듈:** 세트 서명 전과 결과가 같습니다(`diff` 차이 없음). 남은 실패는 모두 이전부터 있던 것입니다.

- `flet` 없음
- `macro_m8_pipeline` 1건
- `macro_m0_harness` 2건 (손대지 않은 `main`에서도 재현)
