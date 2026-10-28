# 달력 서명 대장

- **작성:** 2026-10-29. 기준은 `main` @ `ce10fe7`이며, PR #7(서명 4차까지)과 PR #3을 반영한 상태입니다.
- **목적:** 서명 문서가 여러 파일에 흩어져 있어 한곳에 모았습니다.
  - **서명된 파일:** 무엇을, 언제, 어떤 지문으로 서명했는지
  - **아직 서명되지 않은 파일:** 서명 문서가 어디에 있는지
- **원칙:** 서명은 소유자만 합니다. 이 대장은 기록일 뿐이며, 서명 필드를 쓰지 않습니다(spec L2100).

---

## 1. 요약

| 구분 | 개수 | 파일 |
|---|---|---|
| 서명됨 | **10 / 16** | KRX, NYSE, FED, SIFMA, kr_sessions, publication_schedules, source_skipped, CBOE, ECOS, kr_regime_tags |
| 미서명 | 6 / 16 | JPX, SSE, HKEX, TWSE, CME, market_closes |
| 감사를 마쳤지만 아직 데이터 폴더에 없는 파일 | 1 | `release_calendar.yaml` (BLS·BEA A안 1단계). 감사와 서명 양식은 `12_release_calendar.md` |

- **KR·US 운영에 필요한 달력은 모두 서명됐습니다.**
- 미서명 6개는 다음 용도에만 쓰입니다.
  - 일본·중국·홍콩·대만 종가: KR 공분산과 시장 간 시점 규칙(T-XMKT-01)
  - CME 선물 달력
- `MANIFEST.yaml`의 파일 머리(전체 세트)는 미서명이라 `calendar_version`은 `unsigned`로 찍힙니다. 16개가 모두 서명되면 세트 버전을 정합니다.

---

## 2. 서명된 파일

서명자는 모두 **Geon Koh**입니다. `md5`는 서명 후 파일에 기록된 값이고, 로더는 이 값이 다르면 그 파일을 거부합니다.

| # | 파일 | 버전 | 행 | 기간 | 서명 시각 (UTC / KST) | md5 | 커밋 |
|---|---|---|---|---|---|---|---|
| 1 | `holidays_KRX.yaml` | 1.0.0 | 33 | 2026-01-01 ~ 2027-12-31 | 10-28 06:35:52Z / 15:35 | `ec68c21ffe77581fd51b2b4291be658a` | `3917bc0` |
| 2 | `holidays_NYSE.yaml` | 1.0.0 | 37 | 2025-01-01 ~ 2027-12-31 | 10-28 06:35:52Z / 15:35 | `6ab0a539ee0461c20f8ee0d1ca50b395` | `3917bc0` |
| 3 | `holidays_FED.yaml` | 1.0.0 | 148 | 2015-01-01 ~ 2027-12-31 | 10-28 06:35:52Z / 15:35 | `6c69a8acd75a44ed6c527c2f676b58aa` | `3917bc0` |
| 4 | `holidays_SIFMA.yaml` | 1.0.0 | 54 | 2025-01-01 ~ 2027-12-31 | 10-28 06:35:52Z / 15:35 | `219f2a46ff84b405552c0e958e39fede` | `3917bc0` |
| 5 | `kr_sessions.yaml` | 1.0.0 | 24 | 1995-01-01 ~ 2027-12-31 | 10-28 08:47:25Z / 17:47 | `e72837e0c7b08a3cdacdd322c52669cc` | `7ea9a1b` |
| 6 | `publication_schedules.yaml` | 1.0.0 | 16 | 1995-01-01 ~ 2027-12-31 | 10-28 08:47:25Z / 17:47 | `ee47ef6cb053f1fb0be7c39a3ae768b8` | `7ea9a1b` |
| 7 | `source_skipped.yaml` | 1.0.0 | 20 | 2015-01-01 ~ 2027-12-31 | 10-28 08:47:25Z / 17:47 | `ed225d30c16c1dc641389ad39459577f` | `7ea9a1b` |
| 8 | `holidays_CBOE.yaml` | 1.0.0 | 37 | 2025-01-01 ~ 2027-12-31 | 10-28 11:28:41Z / 20:28 | `5d9724d67cca74db7fa3b490bf805c78` | `83de7f6` |
| 9 | `holidays_ECOS.yaml` | 1.0.0 | 33 | 2026-01-01 ~ 2027-12-31 | 10-28 11:28:41Z / 20:28 | `603170d21048f8b81649324996887595` | `83de7f6` |
| 10 | `kr_regime_tags.yaml` | 1.0.0 | 63 | 1995-01-01 ~ 2027-12-31 | 10-28 13:27:00Z / 22:27 | `8336f69ca98c450c28eaaeea37495638` | `31758ad` |

**T-CAL-02 기한 조항:** 1~4번의 서명 시각이 기한(2026-11-01T00:00:00Z)보다 앞섭니다.
`test_cal02_2027_files_signed_before_2026_11_01`은 PASS입니다(2026-10-29 재실행).

---

## 3. 서명 묶음별 문서

모든 문서는 `docs/audit/2026-10-27/`에 있습니다. 서명서 원문은 소유자가 채팅으로 보낸 내용을 그대로 옮긴 것입니다.

| 묶음 | 대상 | 감사 보고서 | 서명 양식 | 서명서 원문과 기록 결과 |
|---|---|---|---|---|
| 1차 (T-CAL-02) | KRX, NYSE, FED, SIFMA | `01_calendar_T-CAL-02.md` | `02_signing_form_T-CAL-02.md` | `03_signature_T-CAL-02.md` |
| 2차 | kr_sessions, publication_schedules, source_skipped | `04_calendar_batch2.md` | 보고서 안 | `05_signature_batch2.md` |
| 3차 | CBOE, ECOS | `06_calendar_batch3.md` | 보고서 6절 | `07_signature_batch3.md` |
| 4차 | kr_regime_tags | `08_kr_regime_tags.md` | 보고서 안 | `10_signature_batch4.md` |

**서명서 원문에 남아 있는 소유자 확인 사항**

- **1차:**
  - CAL-14(2018·2019·2020년 12월 24일 연준 이사회 휴무)를 포함합니다.
  - KRX가 12월에 2027년 휴장일을 공지했을 때 이 파일과 다르면 새 버전으로 다시 서명합니다.
- **2차:**
  - 2027-11-18 수능일을 넣고, 1995~1998년 점심 휴장(11:30~13:00)을 넣습니다.
  - 성금요일 예외를 H.15 전체로 넓힙니다.
  - 2008년 이전 수능일, 1998년 이전 토요일 마감 시각, 2015년 이전 랜덤엔드 연장은 공백으로 둡니다.
- **3차:**
  - CBOE는 NYSE 휴장일을 따르고, 조기폐장은 13:15 ET입니다.
  - 2026-05-25와 09-07은 GTH 시세가 있어도 휴장으로 둡니다.
  - ECOS는 KRX 휴장일과 12/31 외환시장 휴장을 따릅니다.
- **4차:**
  - 공매도, 랜덤엔드, fx_regime 값은 감사안대로 둡니다.
  - 미확인으로 남은 스펙 값은 그대로 둡니다.
  - T-REGIME-01 전 기간 기대값 파일은 별도 과제로 남깁니다.

---

## 4. 아직 서명되지 않은 파일

| 파일 | 지금 상태 | 쓰는 곳 | 서명하지 않았을 때 | 서명 문서 |
|---|---|---|---|---|
| `holidays_JPX.yaml` | 0행, 기간 없음 | JP 결정 시계, KR 공분산(닛케이) | JP 시계와 닛케이 종가 입력이 막힘 | `14_calendar_batch6.md`, 양식 `15_signing_form_batch6.md` |
| `holidays_SSE.yaml` | 0행, 기간 없음 | CN 결정 시계, KR 공분산(상하이) | 같음 | `14_calendar_batch6.md`, 양식 `15_signing_form_batch6.md` |
| `holidays_HKEX.yaml` | 0행, 기간 없음 | HK 결정 시계, KR 공분산(HSI) | 같음 | `14_calendar_batch6.md`, 양식 `15_signing_form_batch6.md` |
| `holidays_TWSE.yaml` | 0행, 기간 없음 | TW 결정 시계, KR 공분산(TAIEX) | 같음 | `14_calendar_batch6.md`, 양식 `15_signing_form_batch6.md` |
| `holidays_CME.yaml` | 0행, 기간 없음 | CME 선물(`CME_micro_ES`), T-AVAIL-01 | CME 휴장일 판단 불가 | `14_calendar_batch6.md`, 양식 `15_signing_form_batch6.md` |
| `market_closes.yaml` | 3행(SSE 15:00, HKEX 16:00, TWSE 13:30), 출처 없음 | CN·HK·TW 마감 시각 | CN·HK·TW 시계가 막힘 | `14_calendar_batch6.md`, 양식 `15_signing_form_batch6.md` |
| `release_calendar.yaml` | 감사 완료, 제안 v1.0.0 264행(지문 `1faf621a5b443f1c9f3627c2a98f1054`). 코드 패치 `calendar_batch5/proposed_code.diff`와 함께 반영 | BLS·BEA 발표일(CPI, 고용, PCE, 실업수당) | BLS·BEA 입력이 막힘. 근원 PCE가 없으면 헤지 크레딧이 꺼짐 | `12_release_calendar.md` 8절(5차 서명 양식) |

- **미서명 파일이 KR 북을 멈추지는 않습니다.** 공분산에만 쓰이는 입력은 실패하면 최대 5번의 결정 동안 마지막 값을 '오래됨' 표시와 함께 쓰고, 그 뒤에는 공분산에서 빠집니다(스펙 L1877).
- **`release_calendar.yaml`:**
  - 다른 세션이 소유자가 올린 BLS·BEA 공식 일정과 ALFRED 기록으로 감사했습니다(`d1c9296`, `5f669cb`).
  - 이 세션이 다시 돌려 확인했습니다. 지문이 맞고, 현재 코드로는 4항목이 실패하고 코드 패치를 적용하면 0입니다.
  - 패치는 서명과 같은 커밋에 넣어야 합니다. 서명 없이 `store.py` 부분만 넣으면 US 상태가 미서명으로 떨어지기 때문입니다.

---

## 5. 서명 상태를 직접 확인하는 방법

```bash
python -m core.calendars.store          # 파일마다 signed / REFUSED, 버전, content md5
python -m tests.macro_m1_calendars      # test_cal02_2027_files_signed_before_2026_11_01 → PASS
```

서명된 파일을 한 글자라도 고치면 md5가 달라져 로더가 그 파일을 거부합니다. 고칠 때는 새 버전으로 만들어 다시 서명합니다(change_control).
