# T-CAL-02 달력 감사: 2027년 KRX·NYSE·FED·SIFMA 휴장일 파일

- **작성:** 2026-10-28 (UTC 05:31 기준 자료 확인)
- **근거 판정:** 소유자 선택 "방안 A"(2026-10-28). 감사 요청서(`00_request.md`) 6절 데이터 정확성 감사 중 달력 부분을 먼저 수행합니다.
- **규칙:** 요청서 7절 8번에 따라 `core/calendars/data/`는 **고치지 않았습니다.** 감사 결과와 제안 패치만 냅니다. 서명 필드
  (`signed_off_by`, `signed_utc`, `md5`)는 어디에도 쓰지 않았습니다.
- **기한:** `signed_utc`가 **2026-11-01T00:00:00Z 이전**이어야 합니다. 한국 시간으로 **11월 1일(일) 오전 9시 전**입니다.

---

## 1. 결론

| 파일 | 판정 | 2027년 행 오류 | 2025~2026년 행 오류 | 그 이전 행 오류 |
|---|---|---|---|---|
| `holidays_NYSE.yaml` | **그대로 서명 가능** (날짜 오류 0건, 출처만 채움) | 0 | 0 | — |
| `holidays_KRX.yaml` | **수정 후 서명** | 2건 누락 | 2건 누락 | 범위 밖(2026년부터) |
| `holidays_FED.yaml` | **수정 후 서명** | 1건 누락 | 3건 누락 | 7건 누락(3건은 추정) |
| `holidays_SIFMA.yaml` | **수정 후 서명** | 조기폐장 4건 누락 | 1건 오분류, 조기폐장 5건 누락 | 범위 밖(2025년부터) |

- 지금 초안대로 서명하면 **2027년 KRX 휴장일 이틀(5/3, 7/19)을 거래일로 서명**하게 됩니다.
- 제안 패치(v1.0.0)를 실제 로더에 **모의 서명**으로 올려 37개 항목을 확인했고, 모두 통과했습니다(5절).
- 원인은 하나입니다. 초안이 `exchange_calendars 4.13.2`와 법정 공휴일 규칙으로 만들어졌습니다. 이 라이브러리에는 2026년의
  법 개정(제헌절·노동절 공휴일화)과 선거일, 임시 휴무가 들어 있지 않습니다. 스펙 L2003이 "exchange_calendars는 출처가 될 수 없다"고
  정한 이유가 이번 감사에서 그대로 확인됐습니다.

**소유자께 필요한 것은 세 가지입니다(7절).** 패치 승인, FED 추정 3건 포함 여부, 서명 문장.

---

## 2. 범위와 방법

**범위.** 서명은 파일 단위로 하기 때문에, 2027년 행만이 아니라 **4개 파일의 모든 행**을 봤습니다.
KRX 29행, NYSE 37행, FED 137행, SIFMA 45행입니다.

**대조 방법.** 날짜마다 세 갈래로 확인했습니다.

1. **공식 출처.** 거래소·연준·SIFMA 공지, 우주항공청 2027년 월력요항(관보)을 확인했습니다.
2. **독립 교차 확인.** `pandas_market_calendars 5.5.0`(NYSE, SIFMAUS, XKRX), `python-holidays 0.107`(US, KR)을 썼습니다.
   별도 가상환경에 설치했고, 저장소의 고정 버전은 바꾸지 않았습니다.
3. **실측 데이터.** 저장소 캐시를 썼습니다.
   - KRX: `docs/asset_expansion/cache/yf_069500.KS.csv`, `yf_005930.KS.csv`(2026-09-23까지). 거래 기록이 없는 평일을 찾았습니다.
   - FED: `fred_DEXKOUS.csv`(H.10, 2017-01~2026-09). 값이 빈 평일을 찾았습니다.
   - SIFMA: `fred_DGS3MO.csv`(H.15 국채). 값이 빈 평일을 찾았습니다.

**한계.** 이 세션의 네트워크 정책이 `www.nyse.com`, `www.federalreserve.gov`, `www.sifma.org`를 막았습니다. 그래서 공식 문서는
**검색 엔진 발췌로만** 확인했고, 원문을 직접 열지 못했습니다. 서명하실 때 8절 링크를 직접 열어 확인하시기를 권합니다.
위 도메인을 허용 목록에 추가해 주시면 Claude가 원문으로 다시 확인합니다.

**근거 등급.** 각 행의 `evidence` 필드 맨 앞에 붙입니다.

| 등급 | 뜻 |
|---|---|
| **A** | 발행 기관의 공지를 확인했고, 독립 교차 확인 또는 실측 데이터와도 일치함 |
| **B** | 공식 월력요항이나 규정, 교차 확인과 일치함. 다만 발행 기관 자체 공지는 아직 나오지 않음 |
| **C** | 추정. 넣어도 데이터가 **늦게** 쓰일 뿐, **일찍** 쓰이는 일은 없어서 보수적으로 포함함 |

---

## 3. 발견사항

심각도 기준은 다음과 같습니다.

- **P0:** 2027년 행. 실전 운영과 이번 기한에 영향을 줍니다.
- **P1:** 2025~2026년 행. 과거 데이터지만 파일에 포함되어 함께 서명됩니다.
- **P2:** 2024년 이전 행.
- **P3:** 메타데이터.

| ID | 심각도 | 파일 | 날짜 | 현재 | 제안 | 근거 | 등급 |
|---|---|---|---|---|---|---|---|
| CAL-01 | **P0** | KRX | 2027-05-03(월) | 거래일 | 휴장 · 노동절 대체공휴일 | 2027 월력요항: 노동절이 2026년부터 공휴일이 됐고, 2027-05-01이 토요일이라 대체공휴일이 생김. python-holidays도 같음 | B |
| CAL-02 | **P0** | KRX | 2027-07-19(월) | 거래일 | 휴장 · 제헌절 대체공휴일 | 2027 월력요항: 제헌절이 2026년부터 공휴일로 돌아왔고, 2027-07-17이 토요일 | B |
| CAL-03 | **P0** | FED | 2027-12-31(금) | 영업일 | 휴무 · 2028 신정 대체 | K.8 각주 "토요일 휴일이면 연준은행은 전 금요일 영업, **이사회는 휴무**". 같은 파일의 2021-12-31 행과 같은 처리 | A |
| CAL-04 | **P0** | SIFMA | 2027-03-25(목) | 정상 | 14:00 조기폐장(성금요일 전날) | pandas_market_calendars SIFMAUS, 보조 달력 2곳 | B |
| CAL-05 | **P0** | SIFMA | 2027-05-28(금) | 정상 | 14:00 조기폐장(메모리얼데이 전날) | 같음 | B |
| CAL-06 | **P0** | SIFMA | 2027-07-02(금) | 정상 | 14:00 조기폐장(독립기념일 대체휴일 전날) | 같음 | B |
| CAL-07 | **P0** | SIFMA | 2027-12-23(목) | 정상 | 14:00 조기폐장(성탄절 대체휴일 전날) | 같음 | B |
| CAL-08 | P1 | KRX | 2026-06-03(수) | 거래일 | 휴장 · 제9회 지방선거일 | 거래소 공지(2026-05-20 보도). 069500·005930 모두 그날 거래 기록 없음 | A |
| CAL-09 | P1 | KRX | 2026-07-17(금) | 거래일 | 휴장 · 제헌절 | 같은 공지. 두 종목 모두 거래 기록 없음 | A |
| CAL-10 | P1 | SIFMA | 2026-04-03(금) | **전일 휴장** | **12:00 조기폐장** | 3월 고용지표 발표일과 겹쳐 SIFMA가 조기폐장을 권고함(SIFMA 공지, 뉴욕연준 운영 공지). H.15 DGS3MO에 그날 값 3.71이 있음 | A |
| CAL-11 | P1 | SIFMA | 2025-01-09, 2025-04-17, 2025-05-23, 2026-05-22, 2026-07-02 | 정상 | 14:00 조기폐장 | SIFMA 개별 공지. 2025-01-09는 카터 전 대통령 국가애도일 | A |
| CAL-12 | P1 | FED | 2025-01-09, 2025-12-24, 2025-12-26 | 영업일 | 이사회 휴무 | 연준 이사회 일정·공지: "발표물은 다음 영업일로 연기" | A |
| CAL-13 | P2 | FED | 2017-01-20, 2018-12-05, 2021-01-20, 2024-12-24 | 영업일 | 이사회 휴무 | 취임식일, 부시 전 대통령 국가애도일(이사회 보도자료). 2021년은 의장 일정에 "Board holiday". 2024-12-24는 행정명령에 따른 휴무로, 이사회 일정에 "발표물 12/26로 연기"라고 나옴. 2017·2018·2021년 세 날은 H.10 값이 비어 있음 | A |
| CAL-14 | P2 | FED | 2018-12-24, 2019-12-24, 2020-12-24 | 영업일 | 이사회 휴무(**추정**) | 성탄 전날 연방기관 휴무 행정명령(2018·2019년은 확인됨). 이사회 휴무 여부는 직접 확인하지 못함 | **C** |
| CAL-15 | P3 | 4개 전부 | 모든 행 | `source_url: null`, KRX 이름이 자리표시자 | 출처 URL, 한글 공휴일 이름, `evidence` 채움 | — | — |

**변경하지 않은 것.**

- **NYSE 37행 전부.** ICE의 2024년·2025년 휴장일 발표, pandas_market_calendars와 모두 일치했습니다.
- **FED 2021-06-18.** H.10 값은 있지만, 이사회 보도자료상 그날 이사회는 휴무였습니다. 유지합니다.
- **H.10 KRW 값이 빈 날 3일(2019-01-14, 2019-02-20, 2020-11-27).** 연방 휴일도, 이사회 공지도 없어서 원화 시리즈만의 공백으로 봤습니다.
  추가하지 않습니다.

**영향.** 해당 파일들이 서명되어 실제로 쓰이기 시작한 뒤를 기준으로 합니다.

- **CAL-01·02:** KR 결정 시계가 휴장일을 거래일로 봅니다. 그날 KR 북이 존재하지 않는 종가로 결정을 내리려 합니다.
- **CAL-03·12~14:** FED 달력은 H.15(다음 영업일 16:15 ET)와 H.10(주 다음 월요일)의 발표 시점을 정합니다(`publication_schedules.yaml`).
  이사회 휴무가 빠지면 데이터를 실제보다 **하루 일찍** 쓸 수 있다고 계산합니다. 즉 미래 정보 사용(look-ahead)입니다.
  거꾸로 휴무를 하나 더 넣으면 하루 **늦게** 쓸 뿐입니다. CAL-14를 보수적으로 넣자고 권하는 이유입니다.
- **CAL-10:** `TREASURY_PAR` 일정이 SIFMA 달력을 씁니다. 2026-04-03을 휴장으로 두면 그날 실제로 발표된 국채 수익률을 달력 밖의 값으로 처리합니다.
- **CAL-04~07·11:** 지금은 `sifma_status`를 호출하는 코드가 없어서 영향이 잠재적입니다. 다만 서명은 데이터의 정확성을 보증하는 것이므로 지금 고칩니다.

---

## 4. 2027년 한눈에

![2027 holiday files proposed for signing](calendar_2027.png)

빗금 친 주황색 칸이 이번 감사로 추가되거나 바뀐 날입니다. 그림은 `calendar_T-CAL-02/plot_calendar_2027.py`로 만들었습니다(matplotlib 사용).

---

## 5. 제안 패치(v1.0.0)와 검증

**파일.** 모두 `docs/audit/2026-10-27/calendar_T-CAL-02/`에 있습니다.

| 파일 | 내용 |
|---|---|
| `build_proposed.py` | 변경 목록이 코드로 적혀 있습니다. 현재 초안을 읽어 `proposed/`를 다시 만듭니다. 서명 필드가 비어 있는지 스스로 확인합니다 |
| `proposed/holidays_{KRX,NYSE,FED,SIFMA}.yaml` | 제안 파일입니다. 서명 필드는 모두 `null`입니다 |
| `proposed.diff` | 현재 초안과의 차이입니다. 3,601줄인데 대부분 행마다 출처와 근거를 채운 줄입니다 |
| `simulate_signed.py`, `simulate_signed.log` | 아래 검증의 스크립트와 결과입니다 |
| `calendar_2027.png`, `plot_calendar_2027.py` | 4절 그림과 그 스크립트입니다 |

**행 수.**

| 파일 | 현재 | 제안 |
|---|---|---|
| KRX | 29 | 33 |
| NYSE | 37 | 37 |
| FED | 137 | 148 |
| SIFMA | 45 | 54 |

**행 형식 변경.** 행의 `unverified` 필드를 `evidence`(등급 + 근거)로 바꿨습니다. 로더는 추가 필드를 허용하고, `md5`는 이 필드까지 포함해 계산됩니다.
파일 머리의 `version`은 `1.0.0`, `status`는 "AUDITED, UNSIGNED"로 바꿨습니다. `unverified` 목록에는 남은 단서만 적었습니다.

**검증(`simulate_signed.py`).**

1. `core/calendars/data/` 전체를 임시 폴더에 복사합니다.
2. 4개 파일을 제안 파일로 바꿉니다.
3. 모든 파일에 `"SIMULATION - not a signature"`라는 **가짜 서명자**를 넣습니다.
4. 실제 로더(`CalendarSet`)로 읽어 확인합니다.

결과는 **37/37 통과**입니다. 원본 `core/calendars/data/`는 md5로 확인했고 바뀌지 않았습니다.
실행 환경은 클라우드 세션의 Python입니다. 로더가 불러오는 `scipy`는 세션 컨테이너에만 임시로 설치했고, 저장소는 바꾸지 않았습니다.

- 4개 파일이 모두 거부 없이 로드됩니다.
- KR 휴장 7일, 거래일 4일이 기대와 같습니다.
- NYSE 4일, FED 6일, SIFMA 10일이 기대와 같습니다. SIFMA 2026-04-03의 마감 시각은 12:00입니다.
- 2026-10-28 기준 **KR: signed=True, 남은 거래일 289. US: signed=True, 남은 거래일 292.**
  단, 이것은 다른 파일들도 가짜 서명했을 때의 값입니다(6절 참고).
- 2027년 파일의 커버리지 경보 시점:

| 파일 | `warn`(남은 거래일 60 이하) 시작 | `page`(20 이하) 시작 |
|---|---|---|
| KRX | 2027-10-05 | 2027-12-01 |
| NYSE | 2027-10-06 | 2027-12-02 |
| FED | 2027-10-01 | 2027-12-01 |
| SIFMA | 2027-10-04 | 2027-12-02 |

→ **2028년 파일은 2027년 9월 말까지 서명해야 경보 없이 넘어갑니다.**

---

## 6. 서명 후에도 남는 것 (이번 범위 밖)

1. **4개 파일만 서명해서는 KR·US 실행 입력이 풀리지 않습니다.** 기한 조항은 충족되지만 시장은 계속 막혀 있습니다.
   - KR은 `kr_sessions`, `kr_regime_tags`, `publication_schedules`, `source_skipped`도 서명되어야 합니다.
   - US는 `publication_schedules`, `source_skipped`도 서명되어야 합니다.
2. **KRX 2027년 공식 공지(보통 12월)가 나오면 다시 대조합니다.** 임시공휴일이 추가되는 등 차이가 있으면 새 버전(1.0.1)과 새 서명이 필요합니다.
3. **아직 나오지 않은 임시 휴무**(예: 2026·2027년 성탄 전날 행정명령, 국가애도일)는 변경 통제 절차에 따라 새 버전으로 반영합니다.
4. **KRX 1995~2025년 휴장일**은 이 파일에 없습니다. T-CLOSE-02 골든값(2015, 2016, 2025년)에 필요하며 다음 버전 과제입니다.
5. `tests/macro_m1_calendars.py`의 `test_cal02_2027_files_signed_before_2026_11_01`은 지금 무조건 NOT_RUN입니다.
   서명 뒤에는 다음 세 가지를 실제로 검사하도록 바꿉니다(서명 후 구현 단계에 포함).
   - 4개 파일이 로드되는지
   - `signed_utc`가 2026-11-01T00:00:00Z보다 이른지
   - `covers.to`가 2027-12-31 이후인지

---

## 7. 소유자 결정과 서명 절차

**결정 1. 패치 승인.** CAL-01~CAL-15를 반영한 `proposed/` 4개 파일을 승인하시는지 답해 주세요.

**결정 2. FED 추정 3건(CAL-14) 포함 여부.**

- **권장: 포함.** 실제로 휴무가 아니었다면 2018·2019·2020년 성탄 전날 사흘 동안 H.15·H.10이 하루 늦게 쓰일 뿐입니다.
- 반대로 빼 두었는데 실제로 휴무였다면, 그 사흘에 대해 백테스트가 하루 앞선 데이터를 씁니다.

**결정 3. 서명 문장.** 아래 형식으로 한 문장을 주시면 됩니다. `signed_off_by`에 들어갈 표기(예: 실명 또는 `owner:xkg4real`)도 함께 정해 주세요.

> 나 ○○○은 `docs/audit/2026-10-27/01_calendar_T-CAL-02.md`와 `proposed/holidays_{KRX,NYSE,FED,SIFMA}.yaml`(v1.0.0)의
> 날짜와 출처를 확인했으며, 이 4개 파일에 서명합니다. 표기: `<signed_off_by 값>`. CAL-14: 포함 / 제외.

**그 뒤 Claude가 할 일.** 소유자 승인 후 같은 브랜치에서 진행합니다.

1. `proposed/` 4개 파일을 `core/calendars/data/`로 옮깁니다. CAL-14를 제외하시면 해당 3행을 빼고 다시 생성합니다.
2. 모든 행과 파일 머리에 `signed_off_by`를 쓰고, `signed_utc`(소유자 메시지 시각, UTC)를 씁니다.
3. `md5`를 계산합니다(`python -m core.calendars.store`가 출력하는 content md5).
4. `MANIFEST.yaml`의 해당 행을 갱신합니다. version은 1.0.0이고 md5와 서명자를 넣으며, test_ids에 `T-CAL-02`를 추가합니다.
5. `test_cal02_...`를 실제 검사로 바꾸고 테스트를 돌린 뒤 커밋하고 푸시합니다.
6. 거버넌스 로그에 `calendar_change` 이벤트를 남깁니다(`record_calendar_changes`).

---

## 8. 출처

2026-10-28에 검색 엔진 발췌로 확인했습니다. 원문 직접 열람은 네트워크 정책으로 막혔습니다.

**KRX·한국 공휴일**

- 2027 월력요항(우주항공청 보도자료): https://www.kasa.go.kr/prog/plcyBrf/brief/kor/sub01_01_04/view.do?plcyBrfNo=431
- 한국천문연구원 달력자료 2027: https://astro.kasi.re.kr/kor/life/post/calendarData?year=2027 (2026: `?year=2026`)
- 거래소 2026-06-03·07-17 휴장(데일리안, 2026-05-20): https://www.dailian.co.kr/news/view2/1646567/%ED%95%9C%EA%B5%AD%EA%B1%B0%EB%9E%98%EC%86%8C-%EC%A7%80%EB%B0%A9%EC%84%A0%EA%B1%B0%EC%9D%BC%EC%A0%9C%ED%97%8C%EC%A0%88-%EC%A6%9D%EC%8B%9C-%ED%9C%B4%EC%9E%A5-2026
- 제헌절 공휴일 재지정(주LA 총영사관 안내): https://losangeles.mofa.go.kr/us-losangeles-ko/brd/m_4365/view.do?seq=1348306
- 노동절 공휴일 지정(고용노동부): https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19193

**NYSE**

- 2025~2027년 휴장일 발표: https://ir.theice.com/press/news-details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx
- 2026~2028년 휴장일 발표: https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx
- 2025-01-09 카터 국가애도일 휴장: https://www.businesswire.com/news/home/20241230579727/en

**연준 이사회(FED)**

- K.8 휴일표: https://www.federalreserve.gov/aboutthefed/k8.htm
- 2018-12-05 휴무: https://www.federalreserve.gov/newsevents/pressreleases/other20181203a.htm
- 2021-06-18 휴무: https://www.federalreserve.gov/newsevents/pressreleases/other20210617b.htm
- 2021-01-20 "Board holiday": https://www.federalreserve.gov/foia/chair-powell-calendar-012021.htm
- 2024-12-24: https://www.federalreserve.gov/newsevents/2024-december.htm
- 2025-01-09: https://www.federalreserve.gov/newsevents/2025-january.htm
- 2025-12-24·26: https://www.federalreserve.gov/newsevents/2025-december.htm
- 2017-01-20: https://www.op-f.org/media/0i0pw22x/federal-reserve-board-holidays.pdf

**SIFMA**

- 휴일 권고표: https://www.sifma.org/resources/guides-playbooks/holiday-schedule
- 2025-01-09 조기폐장: https://www.sifma.org/news/press-releases/sifma-recommends-early-market-close-on-january-9-2025-for-the-national-day-of-mourning-in-honor-of-former-president-carter
- 2026-04-03 조기폐장(12:00): https://www.sifma.org/news/press-releases/sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-good-friday-easter-monday-holidays-2026
- 2025년 개별 권고(4/17, 5/23, 7/3): `build_proposed.py`의 `SIFMA` 사전에 있습니다
- 뉴욕연준 운영 공지(2026-04-03): https://www.newyorkfed.org/markets/opolicy/operating_policy_260312
