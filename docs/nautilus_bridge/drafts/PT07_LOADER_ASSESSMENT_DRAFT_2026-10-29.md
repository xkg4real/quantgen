> **검증 전 초안 (2026-10-29).** 이 평가는 하위 에이전트의 초안입니다. 독립 검증 단계가 사용량 95% 때문에 중단됐으므로, 채택 전에 다시 검증해야 합니다. go=True, 소유자 승인 필요=False: No owner approval is needed. The go set (CAL-13 rejects unquoted afternoon HH:MM times when a calendar file is loaded, plus a matching pre-check in the sign tool; M-4 requires signed_utc to be an ISO-8601 UTC instant) changes none of the signed data and needs no re-signing. With the go-set loader, all 17 signed files load and MANIFEST still reads at set version 1.0.0. None of the touched files is in HARNESS_SOURCES (core/quant/gate_package.py:36-38). The owner delegated the PT-07 redesign with 'proceed if the benefit is large' (OWNER_RULINGS_LOG.md:490), and this design changes no behaviour the owner ruled on. CAL-14 (pinning signed_utc in MANIFEST rows, a required sign_off_statement) is left out. Adopting it later would need owner approval, because it means re-signing all 17 files or changing the format of the MANIFEST the owner signed as a set. CAL-12 is left out on the merits: it needs no approval, it just has too little benefit.

# PT-07 로더 강화 다시 검토하고 다시 설계하기 (CAL-12, CAL-13, CAL-14, M-4)

기준 판은 `HEAD 4709cf2`입니다. 달력 코드, 데이터, 서명 도구, 테스트가 마지막으로 바뀐 커밋은 `999dd26`(세트 서명)입니다. 실험 사본은 이 판과 바이트 단위로 같습니다(`diff -r` 결과 같음).

## 0. 한눈에 보기
- **채택(go): CAL-13과 M-4.** 서명된 파일 17개와 MANIFEST가 모두 그대로 로드됩니다. 다시 서명할 필요가 없습니다.
- **보류(no-go): CAL-12와 CAL-14.**
  - CAL-12 원안을 넣으면 과거 날짜의 발표 시각 계산이 새로 막힙니다. 대안을 써도 막을 수 있는 틀린 숫자가 없습니다.
  - CAL-14 원안을 넣으면 서명 파일 17개가 모두 거부됩니다.
- **소유자 승인:** 이번 설계에는 필요 없습니다. 이유는 6절에 적었습니다.
- 용어 풀이
  - 60진수 읽기: PyYAML 1.1은 따옴표 없는 `13:00`을 문자열이 아니라 숫자 780(13×60)으로 읽습니다.
  - md5: 파일 내용의 지문입니다. 서명은 이 지문에 묶여 있습니다.
  - fail closed: 근거가 불확실할 때 계산을 멈추는 방식입니다.

## 1. 네 검사가 지금 코드에서 막아 주는 것
**CAL-12 (same_day 규칙이 발행처 달력의 서명을 확인)**
- 지금 코드: same_day는 달력을 읽지 않고 바로 시각을 돌려줍니다(`core/calendars/publication.py:156-157`).
- 지금 막고 있는 곳: 결정 쪽은 이미 막혀 있습니다. `next_expected_obs`가 같은 달력으로 영업일을 따지기 때문입니다(`publication.py:219`).
- 실험 결과: CBOE 파일을 거부 상태로 만든 사본에서도 VIXCLS_CBOE 시각은 20:15Z로 나옵니다. 같은 사본에서 `next_expected_obs`는 CalendarUnsigned로 멈춥니다.

**CAL-13 (따옴표 없는 HH:MM을 로드할 때 거부)**
- 지금 코드: `read_yaml`은 `yaml.safe_load`를 씁니다(`core/calendars/store.py:121`).
- 날짜만 거부합니다(`store.py:103-111`). 시각은 쓰는 순간에야 `_hhmm`이 ValueError를 냅니다(`core/calendars/clocks.py:80-84`, `:141`).
- docstring에는 "시각도 거부한다"고 적혀 있지만 사실과 다릅니다(`store.py:19-20`).
- 현재 막고 있는 장치는 없습니다.

**CAL-14 (MANIFEST에 signed_utc를 고정하고 sign_off_statement를 필수로 함)**
- signed_utc는 md5 계산에서 빠져 있습니다(`store.py:37`, `:114-117`).
- MANIFEST 검사는 md5, 버전, 서명자, 테스트 ID만 봅니다(`store.py:146-155`).
- 현재 막고 있는 장치는 없습니다.

**M-4 (signed_utc가 ISO-8601 UTC 형식인지 검사)**
- 지금 코드는 빈 값만 거부합니다(`store.py:140-141`).
- 마감 테스트는 이미 datetime으로 비교합니다(`tests/macro_m1_calendars.py:696-697`). 그래서 M-4의 테스트 쪽 절반은 HEAD에서 해결됐습니다.
- 로드할 때 형식을 검사하는 부분은 아직 없습니다.

**서명 파일과의 호환**
- MANIFEST 행에는 signed_utc가 없습니다(`core/calendars/data/MANIFEST.yaml:12-17`).
- 어느 파일에도 sign_off_statement가 없습니다. `core`, `tools`, `tests`를 검색한 결과 0건입니다.
- 17개 파일과 MANIFEST 머리의 signed_utc는 모두 `YYYY-MM-DDTHH:MM:SSZ` 형식입니다(`MANIFEST.yaml:3`, 각 파일 10행).
- 17개 파일 어디에도 60진수로 읽히는 값이 없습니다(스캔 결과 0건).

## 2. 실험 (사본에서만 실행했고, 저장소는 건드리지 않음)
- 기준 사본: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/pt07_probe`
- 검사별 사본: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/pt07_variants/<이름>`
- 사본을 만든 스크립트: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/scripts/make_variants.py`

| 사본 | 서명 파일 로드 | m1_calendars | m1_integration | m1_pit |
|---|---|---|---|---|
| HEAD 그대로 | 17/17 | 18/0/4 | 8/0/0 | 23/0/8 |
| d865c7f 원안 전체 | **0/17** | 1/16/5 | 3/5/0 | 23/0/8 |
| CAL-12 원안 | 17/17 | 18/0/4 | 8/0/0 | 23/0/8 |
| CAL-12 대안 (서명만 확인) | 17/17 | 18/0/4 | 8/0/0 | 23/0/8 |
| CAL-13 | 17/17 | 18/0/4 | 8/0/0 | 23/0/8 |
| CAL-14 signed_utc 고정 (필수) | **0/17** | 1/16/5 | 3/5/0 | 23/0/8 |
| CAL-14 signed_utc 고정 (행에 있을 때만) | 17/17 | 18/0/4 | 8/0/0 | 23/0/8 |
| CAL-14 sign_off_statement 필수 | **0/17** | 1/16/5 | 3/5/0 | 23/0/8 |
| M-4 | 17/17 | 18/0/4 | 8/0/0 | 23/0/8 |
| go 세트 (새 테스트 2개 포함) | 17/17 | **20/0/4** | 8/0/0 | 23/0/8 |

숫자는 통과/실패/미실행입니다. 원안 전체가 거부한 첫 사유는 "MANIFEST.yaml signed_utc None != file ..."입니다(`d865c7f:core/calendars/store.py:212`).

**검사별로 동작을 확인한 결과** (원본 기록: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/tmp/probe_<사본>.json`)
- **CAL-12 원안:** 아래 세 경우에 HEAD는 시각을 냅니다. 원안은 `CalendarCoverageError`를 냅니다.
  - ECOS_USDKRW 2025-06-02 (HEAD 06:30Z)
  - VIXCLS_CBOE 2024-06-03 (HEAD 20:15Z)
  - TREASURY_PAR 2024-06-03 (HEAD 22:00Z)
  - 이유: 원안이 `business_day`를 부르고(`d865c7f:core/calendars/publication.py:157`), `business_day`는 커버리지를 요구합니다(`publication.py:58`).
  - 커버리지 시작일: ECOS 2026-01-01(`holidays_ECOS.yaml:6`), CBOE와 SIFMA 2025-01-01(`holidays_CBOE.yaml:6`, `holidays_SIFMA.yaml:6`).
- **CAL-13, 서명된 파일:** NYSE 2025-07-03 조기폐장 시각 `13:00`에서 따옴표를 빼고 md5와 MANIFEST를 다시 맞췄습니다.
  - HEAD: 로드됩니다. 값은 780입니다. 평일 결정 시각은 정상입니다. 2025-07-03 하루만 ValueError가 납니다.
  - go 세트: 로드할 때 "line 306: unquoted time '13:00'"으로 거부합니다.
- **CAL-13, 서명 도구:** SIFMA 초안의 `14:00`에서 따옴표를 빼고 서명 도구에 넣었습니다.
  - HEAD: 서명에 성공합니다. 서명된 파일에는 `close_local: 840`이 기록됩니다.
  - go 세트: SignRefused로 거부합니다. 파일은 바이트 단위로 그대로입니다.
- **M-4:** JPX의 signed_utc를 '10/30/2026', '2026-10-30T09:00:00+09:00', '2026-10-30'으로 바꿨습니다. HEAD는 셋 다 로드합니다. M-4는 셋 다 거부합니다.
- **다른 모듈:** m5_fills_events, m5_integration, m6_context, m9_lab도 HEAD 사본과 go 세트의 결과가 같습니다.

## 3. 얻는 것, 일어날 가능성, 드는 비용
**CAL-13 (효용 큼)**
- 얻는 것: 서명까지 통과한 파일 속에 숨은 시한폭탄을 막습니다. 지금은 조기폐장일 하루만 결정 계산이 ValueError로 멈춥니다.
- 서명 도구가 숫자를 그대로 서명하는 일도 막습니다(`tools/sign_calendars.py:34-35`, `:75-80`).
- 가능성: 낮지 않습니다.
  - 데이터에 close_local 값이 50개 있고, 모두 1로 시작하는 오후 시각입니다. 따옴표가 하나만 빠져도 숫자로 바뀝니다.
  - 재서명 일정이 이미 잡혀 있습니다: SSE 2027, KRX·ECOS 12월, TWSE, CME, 2028년 판(`13_signature_register.md:102-107`).
- 비용: store.py 약 25줄, sign_calendars.py 5줄, 테스트 1개입니다. 서명 파일이 거부될 위험은 0입니다.

**M-4 (효용 작음, 비용 거의 0)**
- 얻는 것: 형식이 틀린 서명 시각이 거버넌스 기록(`store.py:471`)과 앞으로의 마감 비교에 조용히 들어가는 일을 막습니다.
- 가능성: 낮습니다.
  - 서명 도구는 항상 Z 형식으로 씁니다(`sign_calendars.py:66`). 실제 서명도 이 도구로 했습니다(`16_signature_batch5.md:13`, `17_signature_batch6.md:9`).
  - 다만 세트 서명은 손으로 채웠습니다(`18_signature_set.md:9`).
- 비용: store.py 약 12줄과 테스트 1개입니다. CAL-13과 같은 자리를 고치므로 더 드는 비용이 거의 없습니다.

**CAL-12 (막아 주는 틀린 숫자 없음)**
- same_day 시각은 "관측일 + 고정 시각"이라 달력 내용과 상관없습니다(`publication.py:156-157`).
- 감사 보고서도 "스탬프만 영향을 받는다"고 적었습니다(`docs/audit/2026-10-27-implementation-audit-report.md:223`).
- 원안의 비용: 과거 구간 계산이 새로 막힙니다.
- 대안의 비용: 파일이 깨지면 데이터 수집이 멈추는 지점이 하나 더 생깁니다.

**CAL-14 (가능성 낮고 비용 큼)**
- 막는 것: 누군가 md5 밖에 있는 signed_utc를 고쳐 마감 증빙을 꾸미는 일입니다.
- 가능성: 낮습니다. 서명 시각은 git 이력과 서명 대장에 따로 남아 있습니다(`13_signature_register.md:31-47`).
- 비용: 17개 파일을 다시 서명하거나, MANIFEST 형식을 바꿔야 합니다.
- 서명 문장은 이미 서명 문서에 있습니다(`18_signature_set.md:55-56`).

## 4. 검사별 판정
| 검사 | 판정 | 이유 |
|---|---|---|
| CAL-13 | **go** | 실제로 일어날 수 있는 조용한 실패를 로드·서명 시점으로 앞당깁니다. 서명 파일 영향은 0입니다. 키 이름이 아니라 값으로 거부하므로 `kr_regime_tags`의 `value`도 잡습니다(감사 지적 `docs/audit/2026-10-27/calendars.md:1047`). |
| M-4 | **go** (CAL-13과 함께) | 비용이 거의 0이고 서명 파일 영향도 0입니다. |
| CAL-12 | **no-go** | 막아 주는 틀린 숫자가 없습니다. 원안은 과거 구간을 깨뜨립니다. same_day 시각이 달력 내용에 따라 달라지는 규칙이 생기면 그때 다시 봅니다. |
| CAL-14 | **no-go (보류)** | 원안은 서명 파일을 모두 거부합니다. 대안 "행에 signed_utc가 있을 때만 일치 검사"는 17/17 통과합니다. 하지만 효과가 생기려면 서명 도구가 MANIFEST 행에 signed_utc를 써야 합니다. 이것은 서명 기록 형식을 바꾸는 일이라 그때 소유자 승인이 필요합니다. |

## 5. 설계 (go 세트)
1. **`core/calendars/store.py`** (이 파일은 CRLF 줄끝이므로 그대로 유지)
   - `import re`를 추가합니다.
   - `_SEXAGESIMAL`, `_UNQUOTED_TIME_TAG`, `_UnquotedTime`, `CalendarLoader(yaml.SafeLoader)`, `_calendar_resolvers()`, `_refuse_unquoted_time()`를 추가합니다. d865c7f와 같은 방식이며, 값을 기준으로 거부합니다.
   - `read_yaml`은 `yaml.load(..., Loader=CalendarLoader)`를 씁니다. `_UnquotedTime`이 나면 `CalendarUnsigned("<파일>: line N: unquoted time '13:00' ...")`로 바꿉니다.
   - `utc_instant(text, where) -> datetime`을 추가하고, `parse_file`의 빈 값 검사 바로 뒤에서 부릅니다.
   - docstring 19-20행을 사실대로 고칩니다. `09:30`은 YAML에서도 문자열이라 허용됩니다.
   - md5 정의, `SIGNATURE_FIELDS`, MANIFEST 검사는 바꾸지 않습니다.
2. **`tools/sign_calendars.py`의 `sign()`**
   - 파일을 쓰기 전에 각 초안을 `store.read_yaml`로 읽습니다. `CalendarUnsigned`가 나면 `SignRefused`로 바꿔 냅니다(5줄).
   - 이것이 없으면 오류가 `main()`을 뚫고 나갑니다. `main()`은 SignRefused만 잡기 때문입니다(`sign_calendars.py:118-122`).
3. **`tests/macro_m1_calendars.py`** (+56줄, 헬퍼 `_resign_in_place` 포함)
   - `test_cal01_unquoted_time_refused_at_load` (T-CAL-01)
     - NYSE `close_local: 13:00`과 kr_regime_tags `value: 15:30`은 md5를 다시 맞춰도 거부됩니다.
     - `09:30`은 로드됩니다.
     - 서명 도구는 SignRefused를 내고 파일을 그대로 둡니다.
   - `test_cal01_signed_utc_must_be_iso_utc` (T-CAL-01)
     - 세 가지 잘못된 형식은 거부되고, Z 형식은 로드됩니다.
     - MANIFEST 머리의 signed_utc도 검사를 통과합니다.
   - 두 테스트는 HEAD에서 FAIL, go 세트에서 PASS임을 확인했습니다.
4. **`tests/macro_registry.csv`**: T-CAL-01 행(21행)의 implemented_in에 두 함수를 넣습니다. `python -m tests.macro_acceptance`로 동기화합니다. 빠뜨리면 `test_registry_implemented_in_matches_test_ids`가 FAIL입니다(`tests/macro_m0_harness.py:776-784`).
5. **기대 결과**
   - m1_calendars: 18/0/4 → 20/0/4.
   - 다른 모듈: 변화 없음.
   - 전체 실행: 825/964 → 827/966 (+2 PASS, 바뀐 행 0). 기준은 `4709cf2` 커밋 메시지 20행입니다.
6. **사본에서 만든 diff**
   - `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/go_set_store.diff`
   - `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/go_set_sign.diff`
   - `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/owner1029/go_set_tests.diff`
7. **조율**
   - core/calendars와 서명 도구는 `main`의 달력 세션이 맡고 있습니다.
   - 이 브랜치에 직접 넣으면 다음 main 병합에서 다시 충돌합니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:455-465`).
   - 그래서 `origin/main`에서 새 브랜치를 만들어 PR로 넣습니다. 달력 세션에도 알립니다. 병합된 뒤 main을 이 브랜치로 가져옵니다.
   - 다음 재서명(SSE 2027) 전에 들어가야 효과가 큽니다.

## 6. 소유자 승인이 필요 없는 이유
- 서명된 데이터를 바꾸지 않습니다. 다시 서명할 일도 없습니다. 17/17이 그대로 로드되고 md5도 그대로입니다.
- 고정된 하네스 파일이 아닙니다. `core/calendars`와 `tools/sign_calendars.py`는 `HARNESS_SOURCES`에 없습니다(`core/quant/gate_package.py:36-38`).
- 소유자가 정한 동작을 바꾸지 않습니다. 소유자는 "효용이 크면 진행"으로 맡겼습니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:490`).
- 서명 도구는 따옴표 없는 오후 시각이 든 초안만 거부합니다. 서명할 내용은 바뀌지 않습니다.
- CAL-14를 나중에 되살리려면, 그때 서명 형식 변경이나 재서명에 대해 승인을 받아야 합니다.
