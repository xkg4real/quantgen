# BLS·BEA A안 1단계: 진행 상황

- **작성:** 2026-10-28
- **승인:** 소유자 설계 승인서. 원문은 아래와 같습니다.
- **현재 상태:** 코드는 반영했습니다. 발표일정 데이터 파일은 네트워크가 열린 뒤에 만듭니다.

## 승인서 원문

```
[QUANTGEN 설계 승인서 · BLS·BEA 발표일정 A안]

승인자: Geon Koh

승인 범위:
  [v]1단계: core/calendars/data/release_calendar.yaml 신설
      (2025-01-01~2027-12-31; CPI·EMPSIT·PIO·CLAIMS; 서명은 감사 후 별도 서명서로)
  [v] 시리즈 레지스트리 8개 시리즈에 release 키 추가 (2절 (2) 매핑표)
  [v]core/calendars/adapter.py, store.py 수정과 테스트 추가
  [v]US 커버리지 대상에 release_calendar 포함 (코드 반영과 파일 서명을 같은 단계에서 진행)
  [v]2단계(1995~2024 ALFRED 이력)는 네트워크 허용 후 별도 승인

선택:
  [v]허용 도메인 추가 완료: www.bls.gov, www.bea.gov, www.dol.gov
      (2단계용: fred.stlouisfed.org, alfred.stlouisfed.org, api.stlouisfed.org)

승인 문장:
  "나 Geon Koh는 범위의 A안을 승인합니다."
```

## 반영한 것

| 항목 | 내용 |
|---|---|
| `core/calendars/adapter.py` | `release_dates(release, cal)` 함수를 추가했습니다. 서명된 `release_calendar` 파일에서 `{관측일: 발표일}`을 읽습니다. 공개 시각을 계산하는 `publication_instant`와 `usable_at`에서만, 레지스트리에 `release` 키가 있는 시리즈에 이 발표일을 넣어 줍니다. 월간 다음 관측일 계산은 발표일정 파일이 필요 없으므로 건드리지 않습니다. 관측일이 겹치는 행이나 행이 없는 발표 종류는 거부합니다. |
| `data/macro/series_registry.yaml` | 8개 시리즈에 `release` 키를 추가했습니다. CPIAUCSL·CPILFESL → CPI, UNRATE·PAYEMS·SAHMREALTIME → EMPSIT, ICSA → CLAIMS, PCEPI·PCEPILFE → PIO. 레지스트리 md5는 `307c3237…`에서 `d05610b3…`로 바뀝니다. |
| `tests/macro_m1_integration.py` | `test_release_calendar_supplies_bls_bea_release_dates`(T-AVAIL-01)를 추가했습니다. 아래 다섯 가지를 확인합니다. |
| `tests/macro_registry.csv` | T-AVAIL-01 행에 새 테스트를 등록했습니다. |

새 테스트가 확인하는 내용입니다.

1. 픽스처 발표일정으로 CPI·고용·PCE·실업수당의 공개 시각을 계산하면 08:30 ET(EST·EDT 반영)가 나옵니다.
2. 목록에 없는 관측월은 KeyError로 거부됩니다. 날짜를 추정하지 않습니다.
3. 수집하면 공개 시각이 달력 기준(`calendar_bound`)으로 찍힙니다. 공개 전에 수집한 값은 잠정치(`provisional_intraday`)로 표시됩니다.
4. 발표일정 파일이 없으면 BLS·BEA 입력은 CalendarUnsigned로 막힙니다.
5. 다른 일정(H.15)은 영향을 받지 않습니다.

**아직 반영하지 않은 것: `store.py`의 US 커버리지 대상 추가.** 승인 조건("코드 반영과 파일 서명을 같은 단계에서 진행")에 따라 `release_calendar.yaml` 서명과 같은 커밋에 넣습니다. 지금 넣으면 파일이 서명될 때까지 US 상태가 `signed=False`로 떨어집니다.

**지금의 동작.** 발표일정 파일이 없으므로 BLS·BEA 시리즈는 계속 막혀 있습니다. 오류만 KeyError에서 CalendarUnsigned("release_calendar")로 바뀌었습니다. 미래 정보를 쓰는 경로는 없습니다.

## 테스트

- **결과:** 전체 macro 테스트에서 새로 실패한 테스트는 없습니다.
- **수정 경위:** 처음에는 일정을 조회할 때마다 발표일을 넣었습니다. 그러자 `test_clocks_adapter_resolves_registry_schedules_on_signed_calendars`가 발표일정 파일이 없어 실패했습니다. 그래서 공개 시각을 계산하는 두 경로에서만 발표일을 넣도록 고쳤고, 고친 뒤 통과했습니다.
- **기존 실패 3건:** 이번 변경과 무관하며 원래부터 있던 것입니다.
  - `macro_m0_harness`: T-OBS-03 레지스트리 불일치, `flet` 모듈 없음
  - `macro_m8_pipeline`: 기존 실패

## 막힌 것: 네트워크

허용 도메인을 추가해 주셨지만, 이 세션의 프록시는 아직 다음 주소의 연결(CONNECT)에 403을 돌려줍니다.

- `www.bls.gov`, `www.bea.gov`, `www.dol.gov`
- `fred.stlouisfed.org`, `api.stlouisfed.org`

네트워크 정책 변경은 보통 새 세션이나 새 환경 컨테이너부터 적용됩니다.

검색 결과로 모은 발표일은 서명 파일에 쓰기에 부족했습니다.

| 발표 | 확인된 것 | 문제 |
|---|---|---|
| CPI | 2026년 12건이 두 사이트에서 일치 | 2027년은 3~6월·8월분만 확인 |
| 고용보고서 | — | 2026년 1월분 발표일이 2026년 셧다운 영향을 반영했는지 불분명하고, 2026년 7월·11월분이 비어 있음 |
| BEA | 2026년 9~11월분, 2027년 10건 | 2025년 셧다운 때 바뀐 일정이 일부만 확인됨 |

서명할 파일을 추정치로 채우지 않기 위해 데이터 작성을 멈췄습니다.

## 다음 순서

1. **새 세션 시작(소유자).** 네트워크 정책이 적용됐는지 Claude가 확인합니다.
2. **공식 일정 수집.** 아래 원문을 받아 2025~2027 발표일을 만듭니다.
   - BLS 연도별 일정 페이지(2025·2026·2027)와 셧다운 변경 일정 페이지
   - BEA 발표 일정
   - DOL 주간 실업수당 일정(목요일, 휴일이면 수요일)
3. **실제 발표일 대조.** 이미 발표된 2025-01~2026-10 구간은 ALFRED vintage의 최초 발표일(`realtime_start`)과 맞춰 봅니다.
4. **제안과 서명.** 감사 보고서, 제안 파일, 모의 서명 검증, 서명 양식을 드립니다.
5. **한 번에 반영.** 서명을 받으면 `release_calendar.yaml`, MANIFEST 행, US 커버리지 대상 추가를 한 커밋에 넣습니다.

## 갱신 (2026-10-28)

- **2~4번 완료:** 감사 보고서와 서명 양식은 `12_release_calendar.md`에 있습니다.
- **원문 확보 방법:** 프록시가 계속 막혀 있어 소유자가 공식 일정 PDF와 ALFRED 엑셀을 직접 내려받아 올렸습니다. 그 자료로 대조했습니다.
- **서명 전 결정 필요:** 감사 중 코드 수정이 2건 더 필요한 것으로 드러났습니다(행별 발표 시각, `usable_at` 탐색 시작점). 이 두 건은 서명 양식에서 승인받은 뒤 서명과 같은 커밋에 넣습니다.
