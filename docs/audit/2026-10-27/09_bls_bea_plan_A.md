# BLS·BEA 입력 개방 A안: 공식 발표일정 달력 (release_calendar)

- **작성:** 2026-10-28
- **요청:** 소유자 원문 "Bls Bea 열 A안을 따로 정리해서 지난번과 같이 승인양식과 함께 작성해주세요"
- **상태:** 설계안입니다. 승인 전에는 코드, 레지스트리, 데이터 어느 것도 바꾸지 않습니다(감사 요청서 7절 8번).

---

## 1. 지금 무엇이 막혀 있나

| 시리즈 | 내용 | 역할 | 발표처·시각 | 현재 |
|---|---|---|---|---|
| CPIAUCSL, CPILFESL | CPI, 근원 CPI | context | BLS, 08:30 ET | **수집 실패** (발표일 없음, KeyError) |
| UNRATE, PAYEMS | 실업률, 비농업고용 | context | BLS 고용보고서, 08:30 ET | 수집 실패 |
| SAHMREALTIME | Sahm 지표 | context | FRED 계산(고용보고서 날 실업률 기준) | 수집 실패 |
| ICSA | 신규 실업수당 청구 | context | **노동부(DOL)**, 매주 목요일 08:30 ET | 수집 실패 |
| PCEPI | PCE | context | BEA 개인소득·지출, 08:30 ET | 수집 실패 |
| PCEPILFE | 근원 PCE | **risk_model** (헤지 상태) | BEA, 08:30 ET | 수집 실패. T-HEDGE-01에 따라 헤지 크레딧이 꺼진 상태로 동작(북은 멈추지 않음) |

**원인.**

- 발표일 규칙(`release_calendar`)은 관측일마다 발표일이 있어야 합니다.
- 그런데 지금은 그 목록을 넣을 곳이 없습니다.
- 게다가 CPI, 고용보고서, 실업수당은 모두 `BLS` 일정 행 하나를 같이 씁니다. 세 발표는 날짜가 서로 다르므로 행 하나에 담을 수 없습니다.

**스펙의 근거.**

- L1448: BLS·BEA 발표일정은 `core/calendars`에 공식 일정으로 둡니다.
- L1372: 과거 데이터는 ALFRED의 최초 발표 vintage를 씁니다.
- L1851: BLS는 08:30 ET, BEA는 자체 발표일정을 따릅니다.

---

## 2. 설계

### (1) 새 서명 데이터 파일 `core/calendars/data/release_calendar.yaml`

- **구조:** 다른 달력 파일과 같은 형식입니다. 파일 정보, 서명 필드, 행마다 출처와 서명자가 들어갑니다.
- **행 필드:** `release`, `period`, `release_date`, `time`, `tz`
  - `period`는 FRED 관측일 기준입니다. 월간 지표는 그 달 1일, 주간 지표는 주가 끝나는 토요일입니다.
- **1단계 범위:** 2025-01-01 ~ 2027-12-31

| release | 발표 | 출처 | 예시(2027 공식 일정) |
|---|---|---|---|
| CPI | BLS 소비자물가 | bls.gov 발표 일정(2027년분 2026-10-09 갱신) | 2027년 2월분 → 2027-03-10 08:30 ET |
| EMPSIT | BLS 고용보고서 | 같음 | 2027년 2월분 → 2027-03-05 |
| PIO | BEA 개인소득·지출 | bea.gov 발표 일정(2027년분 2026-10-06 갱신) | 2027년 1월분 → 2027-02-25 |
| CLAIMS | 노동부 주간 실업수당 | dol.gov (매주 목요일, 목요일이 휴일이면 수요일) | 주 단위 |

- **2025년 셧다운:**
  - 2025년 10월 CPI는 발표되지 않았습니다. 레지스트리에도 `missing_months`로 이미 표시돼 있습니다. 그래서 행을 만들지 않고, "기대 관측 없음"으로 처리합니다.
  - 미뤄진 발표는 BLS가 공지한 변경 일정(bls.gov/bls/2025-lapse-revised-release-dates.htm)대로 적습니다.
- **예상 규모:** 약 260행입니다(CPI·EMPSIT·PIO 각 36행, CLAIMS 약 156행).

### (2) 시리즈 레지스트리 `data/macro/series_registry.yaml`: 8개 시리즈에 `release` 키 추가

| release | 시리즈 |
|---|---|
| CPI | CPIAUCSL, CPILFESL |
| EMPSIT | UNRATE, PAYEMS, SAHMREALTIME |
| CLAIMS | ICSA |
| PIO | PCEPI, PCEPILFE |

### (3) 코드

- **`core/calendars/adapter.py`** (약 20줄)
  - `_SERIES_KEYS`에 `release`를 추가합니다.
  - 일정 규칙이 `release_calendar`인 시리즈에는 `release_calendar` 파일에서 그 발표의 `{관측일: 발표일}`을 찾아 `release_dates`로 넣어 줍니다.
- **`core/calendars/store.py`:** US 커버리지 대상(`COVERAGE_FILES["US"]`)에 `release_calendar`를 추가합니다. 그러면 60일 경고와 20일 호출이 이 파일에도 적용됩니다.
- **테스트** (픽스처 사용)
  - (a) CPI 발표일 주입과 공개 시각
  - (b) 발표일이 없는 관측은 계속 KeyError로 수집을 거부(fail-closed 유지)
  - (c) 지연·취소 이벤트로 공개 시각이 옮겨지거나 관측이 없어지는 경로
  - (d) CLAIMS 주간 키
  - 테스트 레지스트리(`tests/macro_registry.csv`) 동기화

### (4) 2단계 (별도 승인): 과거 발표일 1995~2024년

ALFRED vintage의 `realtime_start`(최초 발표일)로 과거 발표일을 만들고, 새 버전으로 서명합니다.
FRED와 ALFRED 접속이 필요하므로 네트워크 허용이 먼저 있어야 합니다. 그 전까지 1995~2024년 관측은 수집이 거부된 상태로 남습니다(미래 정보 사용은 없음).

---

## 3. 서명 후 동작

- **수집:** 예를 들어 CPIAUCSL 2027-02-01 관측은 공개 시각이 2027-03-10 08:30 ET(달력 기준)로 기록됩니다. 그 전에 읽으면 잠정값으로 표시됩니다.
- **목록에 없는 관측:** 발표일이 목록에 없으면 지금처럼 수집을 거부합니다. 추정한 날짜를 쓰지 않습니다.
- **발표 지연·취소:** 기존 이벤트 경로(`release_status`)가 공개 시각을 옮기거나 관측을 없앱니다. 셧다운 같은 일정 변경이 생기면 파일을 새 버전으로 고칩니다.
- **헤지 상태:** 근원 PCE가 수집되면 헤지 상태 판단이 다시 동작합니다. 발표가 두 번 빠지면 헤지 크레딧을 끄는 규칙은 그대로입니다.

---

## 4. 판단: Go

| 항목 | 내용 |
|---|---|
| 효과 | 막힌 8개 시리즈를 엽니다. 위험 모델 입력(근원 PCE)도 포함됩니다 |
| 안전성 | 공식 발표일만 씁니다. 미래 정보를 쓰지 않고, 목록에 없으면 거부합니다 |
| 스펙 정합 | L1448, L1372, L1851과 같은 방향입니다. M5 이벤트 저장소의 지연·취소 경로를 그대로 씁니다 |
| 준비 상태 | BLS와 BEA 모두 2027년 공식 일정이 2026년 10월에 공개됐습니다 |
| 위험 | ① 일정이 바뀌면 새 버전이 필요합니다. ② CLAIMS 행이 많습니다(규칙 기반 생성 후 휴일 예외만 대조). ③ 레지스트리 md5가 바뀝니다(거버넌스 이벤트로 기록) |
| 하지 않을 것 | B안("수집 시각을 공개 시각으로 간주"): 스펙 위반이고, 과거 데이터를 백테스트에 쓸 수 없게 됩니다 |
| 작업량 | 약 1세션입니다. 코드와 테스트, 발표일 수집과 감사를 합친 것입니다 |

**공식 일정 원문을 직접 대조하려면 네트워크 허용이 필요합니다.** `www.bls.gov`, `www.bea.gov`, `www.dol.gov`를 허용 목록에 넣어 주시면 원문과 대조합니다. 허용이 없으면 검색 발췌로 대조하고, 해당 행에 B등급으로 표시합니다.

---

## 5. 승인 양식

승인하시면 다음 순서로 진행합니다.

1. 코드, 레지스트리, `release_calendar.yaml` 제안본을 만듭니다.
2. 모의 서명으로 검증합니다.
3. 서명 양식을 드립니다.

`release_calendar.yaml`이 서명되기 전까지 US 상태가 `signed=False`가 되는 기간이 생길 수 있습니다. 이를 피하려고 코드 반영과 파일 서명을 같은 단계에서 진행합니다.

```
[QUANTGEN 설계 승인서 · BLS·BEA 발표일정 A안]

승인자: ______________________

승인 범위:
  [ ] 1단계: core/calendars/data/release_calendar.yaml 신설
      (2025-01-01~2027-12-31; CPI·EMPSIT·PIO·CLAIMS; 서명은 감사 후 별도 서명서로)
  [ ] 시리즈 레지스트리 8개 시리즈에 release 키 추가 (2절 (2) 매핑표)
  [ ] core/calendars/adapter.py, store.py 수정과 테스트 추가
  [ ] US 커버리지 대상에 release_calendar 포함 (코드 반영과 파일 서명을 같은 단계에서 진행)
  [ ] 2단계(1995~2024 ALFRED 이력)는 네트워크 허용 후 별도 승인

선택:
  [ ] 허용 도메인 추가 완료: www.bls.gov, www.bea.gov, www.dol.gov
      (2단계용: fred.stlouisfed.org, alfred.stlouisfed.org, api.stlouisfed.org)

승인 문장:
  "나 ______은(는) 위 범위의 A안을 승인합니다."
```

---

## 6. 출처

- BLS 2027 발표 일정: https://www.bls.gov/schedule/2027/home.htm
- BLS 2027년 8월 일정: https://www.bls.gov/schedule/2027/08_sched_list.htm
- BLS 2025 셧다운 변경 일정: https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm
- BEA 발표 일정(2027 개인소득·지출): https://www.bea.gov/news/schedule
- 백악관 OMB 2027 회계연도 주요 경제지표 발표일: https://www.whitehouse.gov/wp-content/uploads/2026/10/FY2027-PFEI.pdf
- 스펙: `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md` L1372, L1435~L1436, L1448, L1851
