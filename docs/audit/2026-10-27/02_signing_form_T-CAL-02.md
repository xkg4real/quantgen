# 서명 양식: T-CAL-02 (2027년 KRX·NYSE·FED·SIFMA 휴장일 파일)

- **기한:** 한국 시간 **2026-11-01(일) 09:00 전**. `signed_utc`가 2026-11-01T00:00:00Z보다 앞서야 합니다.
- **근거:** 감사 보고서 `01_calendar_T-CAL-02.md`. CAL-14는 2026-10-28에 소유자가 확인했습니다.
- **원칙:** 서명은 소유자가 합니다. 라이브러리와 빌드는 서명하지 않습니다(spec L2100).

---

## 1. 지금 서명할 문서 4개

| # | 파일 | 버전 | 행 | 기간 | 초안 지문(content md5) | 감사 반영 |
|---|---|---|---|---|---|---|
| 1 | `core/calendars/data/holidays_KRX.yaml` | 1.0.0 | 33 | 2026-01-01 ~ 2027-12-31 | `9c67594f0717fd8aad8161bc5db87609` | CAL-01·02·08·09 |
| 2 | `core/calendars/data/holidays_NYSE.yaml` | 1.0.0 | 37 | 2025-01-01 ~ 2027-12-31 | `acb21e1c20b929648fd0085a456ad5e1` | 날짜 변경 없음, 출처만 채움 |
| 3 | `core/calendars/data/holidays_FED.yaml` | 1.0.0 | 148 | 2015-01-01 ~ 2027-12-31 | `a1a6168be27f7a4b9fb1f44a241db8cb` | CAL-03·12·13·14 |
| 4 | `core/calendars/data/holidays_SIFMA.yaml` | 1.0.0 | 54 | 2025-01-01 ~ 2027-12-31 | `43e5bdc9cbf9ca3ed04f0aa462e5e7b2` | CAL-04~07·10·11 |

**초안 지문**은 서명하기 전 파일 내용의 md5입니다. 검토하신 파일과 서명할 파일이 같은지 확인하는 용도입니다.
서명하면 각 행에 서명자가 들어가므로, 파일에 기록되는 최종 `md5`는 이 값과 달라집니다.

---

## 2. 서명 양식 (복사해서 채우세요)

```
[QUANTGEN 달력 서명서 · T-CAL-02]

서명자 표기 (signed_off_by): ______________________

서명 대상과 초안 지문:
  [ ] holidays_KRX.yaml    v1.0.0   9c67594f0717fd8aad8161bc5db87609
  [ ] holidays_NYSE.yaml   v1.0.0   acb21e1c20b929648fd0085a456ad5e1
  [ ] holidays_FED.yaml    v1.0.0   a1a6168be27f7a4b9fb1f44a241db8cb
  [ ] holidays_SIFMA.yaml  v1.0.0   43e5bdc9cbf9ca3ed04f0aa462e5e7b2

확인 사항:
  [ ] 2027년 휴장일과 조기폐장 날짜 (감사 보고서 4절 그림)
  [ ] 출처 링크 (감사 보고서 8절)
  [x] CAL-14: 2018·2019·2020년 12월 24일 연준 이사회 휴무 (2026-10-28 소유자 확인)
  [ ] KRX가 12월에 낼 2027년 휴장일 공지가 이 파일과 다르면 새 버전으로 다시 서명한다

서명 문장:
  "나 ______은(는) 위 4개 파일의 날짜와 출처를 확인했으며, 이 파일들에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

---

## 3. 서명 방법 (둘 중 하나)

### A. 직접 실행 (권장, 약 1분)

저장소 루트에서 실행합니다. `--expect`를 주면 위 초안 지문과 다를 때 서명을 거부합니다.

```bash
python -m tools.sign_calendars --signer "<서명자 표기>" \
  --expect holidays_KRX=9c67594f0717fd8aad8161bc5db87609 \
  --expect holidays_NYSE=acb21e1c20b929648fd0085a456ad5e1 \
  --expect holidays_FED=a1a6168be27f7a4b9fb1f44a241db8cb \
  --expect holidays_SIFMA=43e5bdc9cbf9ca3ed04f0aa462e5e7b2 \
  holidays_KRX holidays_NYSE holidays_FED holidays_SIFMA
```

1. 화면에 4개 파일의 버전, 행 수, 기간, 초안 지문이 나옵니다. 확인한 뒤 `SIGN`을 입력합니다.
2. 도구가 순서대로 기록합니다.
   - 모든 행과 파일 머리에 `signed_off_by`
   - `signed_utc`(현재 UTC 시각)
   - `md5`(위 두 가지를 쓴 뒤 계산)
   - `MANIFEST.yaml`의 해당 행
3. 도구가 로더로 다시 읽어 봅니다. 하나라도 거부되면 **모든 파일을 원래대로 되돌립니다.**
4. 확인하고 푸시합니다.

```bash
python -m tests.macro_m1_calendars        # test_cal02_2027_files_signed_before_2026_11_01 → PASS
git add core/calendars/data && git commit -m "Owner sign-off: 2027 KRX, NYSE, FED, SIFMA calendars (T-CAL-02)"
git push
```

거버넌스 로그 경로가 있으면 `--governance-log <경로>/governance_events.jsonl`을 붙이세요. `calendar_change` 이벤트가 파일마다 한 줄씩 남습니다.

다음 경우 도구가 서명을 거부합니다.

- 서명자가 비어 있거나 `TEST-FIXTURE`, `SIMULATION`처럼 테스트용 이름인 경우
- 이미 서명된 파일인 경우
- 초안 지문이 다른 경우

### B. Claude에게 맡기기

위 양식의 **서명자 표기와 서명 문장**을 채팅으로 보내 주세요. Claude가 같은 도구로 기록하고, 테스트를 돌린 뒤 푸시합니다.
이때 `signed_utc`는 Claude가 도구를 실행한 시각입니다. 기한(11/1 09:00 KST) 전에 보내 주셔야 합니다.

---

## 4. 이후에 서명할 문서 (기한 없음, 시장을 열려면 필요)

4개 파일을 서명하면 T-CAL-02 기한 조항은 충족됩니다. 하지만 **KR 실행 입력은 계속 막혀 있습니다.** 아래 파일들이 아직 감사도 서명도 되지 않았기 때문입니다.

| 파일 | 필요한 시장 | 현재 | 서명 전에 필요한 것 |
|---|---|---|---|
| `publication_schedules.yaml` | KR, US | v0.1.0-draft, 16행 | 감사. BLS·BEA 발표일정은 소유자가 제공 |
| `source_skipped.yaml` | KR, US | v0.1.0-draft, 19행 | 감사 |
| `kr_sessions.yaml` | KR | v0.1.0-draft, 22행 | 감사. 수능일 시간, 1998년 이전 토요일 마감 시각, 점심휴장 기간 등 소유자 사실 입력 |
| `kr_regime_tags.yaml` | KR | v0.1.0-draft, 58행 | 감사. 가격제한폭·세율·공매도 공식 공지 대조, T-REGIME-01 기대값 파일 |
| `market_closes.yaml` | CN, HK, TW | v0.1.0-draft, 3행 | 감사 |
| `holidays_JPX`, `holidays_SSE`, `holidays_HKEX`, `holidays_TWSE` | JP, CN, HK, TW | 0행, 기간 없음 | 데이터 작성부터 |
| `holidays_CBOE`, `holidays_CME`, `holidays_ECOS` | (현재 필수 아님) | 0행, 기간 없음 | 데이터 작성부터 |

**다음 감사 순서 권장:**

1. `publication_schedules`와 `source_skipped` — 이번 4개 파일과 함께 서명하면 **US**가 열립니다.
2. `kr_sessions`와 `kr_regime_tags` — 그다음 **KR**이 열립니다.
