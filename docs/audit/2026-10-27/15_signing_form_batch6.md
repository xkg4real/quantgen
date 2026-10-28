# 서명 양식: 달력 6차 (JPX · SSE · HKEX · TWSE · CME 휴장일, market_closes)

- **근거:** 감사 보고서 `14_calendar_batch6.md`
- **기한:** 없습니다. T-CAL-02 기한(11/1)은 1차 서명으로 이미 충족했습니다.
- **원칙:** 서명은 소유자가 합니다. 라이브러리와 빌드는 서명하지 않습니다(spec L2100).
- **서명하면 열리는 것:** JP·CN·HK·TW 결정 시계, KR 공분산의 닛케이·상하이·항셍·가권 종가, CME 영업일 판단
- **서명해도 그대로인 것:** KR·US 운영. 이미 서명됐고, 이 6개 파일을 읽지 않습니다.

---

## 1. 서명할 문서 6개

| # | 파일 | 버전 | 행 | 기간 | 초안 지문(content md5) | 등급 A / B / C |
|---|---|---|---|---|---|---|
| 1 | `holidays_JPX.yaml` | 1.0.0 | 54 | 2025-01-01 ~ 2027-12-31 | `7a59a8f5234bbb82961627c69aced063` | 47 / 7 / 0 |
| 2 | `holidays_SSE.yaml` | 1.0.0 | 55 | 2025-01-01 ~ 2027-12-31 | `f6db741b0befcb4616ec848fafa4da01` | 37 / 0 / 18 |
| 3 | `holidays_HKEX.yaml` | 1.0.0 | 51 | 2025-01-01 ~ 2027-12-31 | `0c6c54491d59b4d9ffe638f97afff15b` | 31 / 20 / 0 |
| 4 | `holidays_TWSE.yaml` | 1.0.0 | 57 | 2025-01-01 ~ 2027-12-31 | `a6d054df859876c1061726f35560fd6e` | 38 / 17 / 2 |
| 5 | `holidays_CME.yaml` | 1.0.0 | 37 | 2025-01-01 ~ 2027-12-31 | `c7fbab0afedac6a8c0bc870d147b6bb3` | 23 / 4 / 10 |
| 6 | `market_closes.yaml` | 1.0.0 | 4 | 2015-01-01 ~ 2027-12-31 | `65896c0ef30da67167a22fe2826220a7` | 1 / 3 / 0 |

- **초안 지문:** 서명하기 전 파일 내용의 md5입니다. 검토하신 파일과 서명할 파일이 같은지 확인하는 용도입니다.
- **최종 md5는 다릅니다:** 서명하면 각 행에 서명자가 들어가므로, 파일에 기록되는 최종 `md5`는 이 값과 달라집니다.
- **제안 파일 위치:** `docs/audit/2026-10-27/calendar_batch6/proposed/`
- **현재 초안과의 차이:** `proposed.diff`

---

## 2. 서명 양식 (복사해서 채우세요)

```
[QUANTGEN 달력 서명서 · 6차 (JPX · SSE · HKEX · TWSE · CME · market_closes)]

서명자 표기 (signed_off_by): ______________________

서명 대상과 초안 지문:
  [ ] holidays_JPX.yaml    v1.0.0   7a59a8f5234bbb82961627c69aced063
  [ ] holidays_SSE.yaml    v1.0.0   f6db741b0befcb4616ec848fafa4da01
  [ ] holidays_HKEX.yaml   v1.0.0   0c6c54491d59b4d9ffe638f97afff15b
  [ ] holidays_TWSE.yaml   v1.0.0   a6d054df859876c1061726f35560fd6e
  [ ] holidays_CME.yaml    v1.0.0   c7fbab0afedac6a8c0bc870d147b6bb3
  [ ] market_closes.yaml   v1.0.0   65896c0ef30da67167a22fe2826220a7

확인 사항:
  [ ] 2027년 휴장일과 조기마감 (보고서 4절 그림)
  [ ] 출처 링크 (각 행의 source_url, 보고서 9절)
  [ ] HK-01: 홍콩 마감 16:10, 반일장 12:10 (종가 단일가 종료 시각; 2016-07-24 이전은 16:00)
  [ ] SSE-27: 상하이 2027년 18일은 추정(C)이며, 국무원·SSE 공지가 나오면 새 버전으로 다시 서명한다
  [ ] TW-27: 대만 2027-02-02·03 결제 전용일은 추정(C), 2026-07-10·10-23 태풍 휴장은 포함
  [ ] CME-01: CME = 주가지수 선물 정산일. 미국 공휴일 단축 거래, 2025-01-09, 2026-04-03은 휴장.
      2027년은 서명된 NYSE 목록을 따르며 CME 공지가 나오면 다시 확인한다
  [ ] SCOPE: 2025년 이전 이력은 이 버전 범위 밖이다

서명 문장:
  "나 ______은(는) 위 6개 파일의 날짜와 출처를 확인했으며, 이 파일들에 서명합니다."

서명 시각 (UTC): 서명 도구가 자동으로 기록
```

결정 하나만 다르게 하시려면 해당 칸에 표시해 주세요. 예: "HK-01: 16:00 유지". 그러면 Claude가 제안 파일을 다시 만들고 새 지문을 드립니다.

---

## 3. 서명 방법

### A. Claude에게 맡기기 (1~4차와 같은 방식)

위 양식을 채워 채팅으로 보내 주세요. 서명서를 보내시면 6차 제안을 승인한 것으로 처리합니다. Claude는 다음 순서로 진행합니다.

1. `calendar_batch6/proposed/`의 6개 파일을 `core/calendars/data/`로 옮기고, MANIFEST의 해당 행을 1.0.0으로 올립니다.
2. `tools/sign_calendars.py`로 서명을 기록합니다. 기록 전에 `--expect`로 위 초안 지문 6개가 맞는지 확인합니다.
3. 테스트를 돌립니다. 그다음 서명서 원문을 `17_signature_batch6.md`에 옮기고, 커밋하고 푸시합니다.

`signed_utc`는 도구를 실행한 시각입니다.

### B. 직접 실행

먼저 Claude가 1번(파일 이동과 MANIFEST 1.0.0)을 커밋해야 합니다. 그 뒤 저장소 루트에서 실행합니다.

```bash
python -m tools.sign_calendars --signer "<서명자 표기>" \
  --expect holidays_JPX=7a59a8f5234bbb82961627c69aced063 \
  --expect holidays_SSE=f6db741b0befcb4616ec848fafa4da01 \
  --expect holidays_HKEX=0c6c54491d59b4d9ffe638f97afff15b \
  --expect holidays_TWSE=a6d054df859876c1061726f35560fd6e \
  --expect holidays_CME=c7fbab0afedac6a8c0bc870d147b6bb3 \
  --expect market_closes=65896c0ef30da67167a22fe2826220a7 \
  holidays_JPX holidays_SSE holidays_HKEX holidays_TWSE holidays_CME market_closes
```

- 화면에 나온 지문을 확인한 뒤 `SIGN`을 입력합니다.
- 도구가 로더로 다시 읽어 봅니다. 하나라도 거부되면 모든 파일을 원래대로 되돌립니다.
- 다음 경우에는 서명하지 않습니다.
  - 서명자가 비어 있거나 테스트용 이름일 때
  - 이미 서명된 파일일 때
  - 초안 지문이 다를 때
