# 캘린더 서명 키트 (2026-10-28)

> **대체됨 (2026-10-29): 이 키트로 서명하지 마십시오.** 소유자는 다른 Claude 세션의 감사본(방안 A, PR #5·#7)에 이미
> 서명했습니다. `holidays_KRX`·`holidays_NYSE`·`holidays_FED`·`holidays_SIFMA` v1.0.0은 2026-10-28T06:35:52Z(`3917bc0`)에,
> `kr_sessions`는 감사 2차(`7ea9a1b`)에서 서명됐습니다. 이 브랜치는 `main`을 병합하면서 이 키트가 전제한 PT-07 판(`d865c7f`,
> 미서명)의 달력 데이터·로더·테스트를 모두 `main`의 서명본으로 되돌렸습니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`,
> "PR #4 충돌 해결" 절). 아래 내용은 기록으로만 남깁니다. 표의 행과 md5는 지금 저장소의 파일과 맞지 않습니다.

저장 위치: `docs/calendar_signoff/SIGNING_KIT_2026-10-28.md`
대상 파일 5개: `holidays_KRX`, `holidays_NYSE`, `holidays_FED`, `holidays_SIFMA`, `kr_sessions`
마감: **2026-10-31T15:00:00Z = 2026-11-01(일) 00:00 KST**

이 문서는 서명 절차를 안내만 한다. 서명은 소유자가 직접 한다. Claude는 어떤 파일에도 서명하지 않았다.

---

## 0. 전제와 근거

**전제**
- 이 키트는 PT-07 diff가 저장소에 적용된 상태를 전제로 한다.
  - diff 파일: `calendar_pt07.diff`(이 키트와 같은 커밋으로 저장소에 적용됨)
  - md5: `3084ed0c9caf525962b47f8c8853317b`
  - 범위: 14개 파일, +563/−71줄
  - 적용 여부는 3.0절에서 확인한다.
- 따르는 결정과 문서:
  - 소유자 판정 ①-2: 감사 파일을 우선하여 달력 구현을 승인했다.
  - 감사 보고서 `docs/audit/2026-10-27-implementation-audit-report.md`의 10장, 11장(PT-07), 12.1(권고 (나)), 12.2.

**숫자의 출처: 버리는 사본에서 한 리허설 두 번**
리허설 서명자는 사람이 아니다. 모든 문장은 `REHEARSAL`로 시작한다.

| 리허설 | 서명자 | signed_utc | 한 일 | 결과 |
|---|---|---|---|---|
| 1 | `REHEARSAL` | `2026-10-28T07:16:59Z` | 감사 10.4(라) 순서대로 서명했다. 34개 테스트 모듈을 서명 전후로 비교했다 | store 5 signed / 11 REFUSED. PASS→FAIL 0건 |
| 1의 복사본 | (같음) | (같음) | 거버넌스 명령(5절), engine_acceptance 68–75, 핵심 값 확인 명령(4.3절)을 돌렸다 | 이 문서에 적은 기대값과 같다 |
| 2(키트 점검) | `REHEARSAL-KIT` | `2026-10-28T08:22:28Z` | 이 키트의 손 편집 순서를 그대로 따랐다: 행 정규식 치환, 두 줄짜리 status 교체, 2절의 서명 문장 5개 | store 5 signed / 11 REFUSED. `tests.macro_m1_calendars` 24/0/3. `tests.macro_m1_integration` 7/0/0 |

- 두 리허설의 md5는 서로 다르다. 서명 문장과 서명자가 다르기 때문이다. 소유자의 md5도 리허설 값과 다르다. 리허설 md5는 절차가 작동하는지 확인하는 용도로만 본다.

**출처 대조의 한계**
- Claude는 2026-10-28에 공식 출처와 대조했다. 그러나 원문은 한 번도 열지 못했다(WebFetch ENOTFOUND, curl 프록시 403).
- 그래서 아래 판정은 모두 공식 페이지의 검색 색인 발췌를 근거로 한다.
- 서명은 소유자가 "대조했다"고 증언하는 것이다. 소유자는 표의 출처를 직접 열어 본다.

**판정의 뜻**

| 판정 | 뜻 |
|---|---|
| 공식 확인 | 공식 출처의 검색 발췌가 행과 일치한다 |
| 공식 공지 전(근거 기재) | 발행 기관의 공지가 아직 없다. 근거(월력요항, 규정, 관행)를 적었다 |
| 확인 실패 | 공식 원문을 읽지 못했다. 검색 발췌로 일치만 봤거나 발췌가 없다 |
| 불일치 | HEAD의 행이 공식 출처와 다르다. PT-07이 고쳤다 |
| 미대조 | 2026-10-28 대조 범위 밖이다 |

**근거 로그**
저장소 사본(커밋됨): `docs/calendar_signoff/evidence/`
- `source_check_2026-10-28.json`: 공식 출처 대조 154행. 행마다 판정, 출처 URL, 조회 시각, 메모가 있습니다.
- `compare_final.txt`, `head_final.txt`, `impl_final.txt`, `rehearsal_final.txt`: 34개 모듈의 서명 전후 비교입니다.
- `probe_oldcode_m1_calendars.txt`: 새 테스트가 수정 전 코드에서 실패하는지 확인한 결과입니다.
- `rehearsal_checks.json`, `rehearsal_sign_log.json`, `manual_sign_sim.json`, `statements.json`: 서명 리허설 기록입니다.
- `engine_68_75.log`, `governance_run1.log`, `governance_run2.log`, `key_checks_rehearsal.log`, `manual_m1_calendars.log`, `manual_m1_integration.log`: 4절, 5절 명령의 리허설 출력입니다.

원본 작업 폴더(세션 스크래치 `calendar_impl/`)는 세션이 끝나면 사라집니다. 위 사본이 근거입니다.

---

## 1. 마감, 그리고 놓쳤을 때

### 1.1 마감
- 시각: 2026-10-31T15:00:00Z = 2026-11-01(일) 00:00 KST. 2026-10-28 기준으로 약 3일 남았다.
- 근거: spec L2101 "The 2027 KRX, NYSE, Fed and SIFMA files are signed off before 2026-11-01".
- 테스트 기준값: `tests/macro_m1_calendars.py`의 `DEADLINE_UTC = datetime(2026, 10, 31, 15, 0, tzinfo=UTC)`.
  - 비교는 datetime 비교이고 부등호가 엄격하다(`<`).
  - 그래서 `2026-10-31T14:59:59Z`는 통과하고, `2026-10-31T15:00:00Z`는 늦은 것이다.

### 1.2 대상
- 마감 대상 4개: `holidays_KRX`, `holidays_NYSE`, `holidays_FED`, `holidays_SIFMA`.
- 여기에 KR 시계 파일 `kr_sessions`를 더한다(`MARKET_FILES['KR']`).
- 테스트의 `SIGN_OFF_FILES`도 같은 5개다.

### 1.3 테스트가 통과하는 조건
`test_cal02_2027_files_signed_before_2026_11_01`이 PASS하려면 다음이 모두 참이어야 한다.
1. 5개 파일이 모두 거부 없이 로드된다.
2. 5개 파일의 `signed_utc`가 모두 마감보다 앞선다.
3. 마감 대상 4개는 `covers.to`가 2027-12-31 이후이고, 2026-11-01 이후 세션이 60개 이상이다.
4. 2026-11-02에 KR과 US를 ARM할 수 있다.

**권장 일정**
- 늦어도 2026-10-31 12:00Z(21:00 KST)까지 3절의 6단계와 4절의 증명 명령을 끝낸다.
- 오류를 고칠 시간을 남기기 위해서다.

### 1.4 놓쳤을 때 일어나는 일
1. **마감 시각부터 테스트가 FAIL이 된다.**
   - 미서명 파일이 하나라도 있으면 `test_cal02_2027_files_signed_before_2026_11_01`이 NOT_RUN에서 FAIL로 바뀐다.
   - 메시지: `OVERDUE: [...] still unsigned at <시각>; the deadline was 2026-10-31T15:00:00Z = 2026-11-01 00:00 KST (spec L2101)`.
   - 시계를 주입한 테스트로 확인했다. 마감 1초 전에는 NotRun이고, 마감 시각과 그 뒤에는 OVERDUE다.
2. **마감 뒤에 서명해도 FAIL이다.**
   - `signed_utc`가 마감 이후이면 `<file>: signed <signed_utc>, not before the deadline 2026-10-31T15:00:00Z`.
   - 리허설에서 kr_sessions를 2026-11-02로 서명해 이 AssertionError를 재현했다.
   - `signed_utc`를 앞당겨 적으면 거짓 서명이다.
   - 이 FAIL을 없애려면 spec L2101과 이 테스트를 바꾸는 소유자 결정(거버넌스 기록)이 필요하다.
3. **서명 형식이 틀리면 마감 전에도 FAIL이다.**
   - 파일이 거부되면 테스트는 `<file>: signed but refused: ...`로 FAIL한다.
   - 그래서 4절의 증명 명령은 마감 전에 돌린다.
4. **기능은 계속 멈춰 있다.**
   - 미서명이거나 거부된 파일은 계속 `CalendarUnsigned`다.
   - KR 파일(`kr_sessions`, `holidays_KRX`)이나 US 파일(`holidays_NYSE`)이 빠진 시장은 다음과 같다: 시계가 거부되고, `arm_precondition`이 False이며, 장부는 DISARMED로 남고, acting 입력은 fail-closed다.
   - FED나 SIFMA가 빠지면 `fed_business_day`와 `sifma_status`가 거부된다. 그 달력을 쓰는 발표 시각 입력은 fail-closed다.
   - 감사 12.1 (다): 지금 돈이 걸린 위험은 없다(모든 장부 DISARMED). 다만 서명 캘린더에 기대는 기능이 모두 멈춘 채로 남는다.
5. **전체 스위트 결과도 실패가 된다.** 전체 스위트의 종료 코드는 FAIL만 본다(감사 11.3). FAIL이 1건 생기므로 실패로 끝난다.

---

## 2. 파일별 내용

### 2.0 개요

| 파일 | version (지금 → 서명 후) | covers | 행 | Claude의 2026-10-28 대조 | 2026-11-01 이후 세션(리허설) |
|---|---|---|---|---|---|
| holidays_KRX | 0.1.0-draft → 1.0.0 | 2026-01-01..2027-12-31 | 33 | 33행: 공식 확인 18, 공식 공지 전 15 | 287 |
| holidays_NYSE | 0.1.0-draft → 1.0.0 | 2025-01-01..2027-12-31 | 37 | 37행 모두 공식 확인 | 293 |
| holidays_FED | 0.1.0-draft → 1.0.0 | 2015-01-01..2027-12-31 | 138 | 2026–2027년 23행 확인 실패, 2015–2025년 115행 미대조 | 290 |
| holidays_SIFMA | 0.1.0-draft → 1.0.0 | 2025-01-01..2027-12-31 | 50 | 공식 확인 37, 확인 실패 13(2027년). 넣지 않은 행 5 | 290 |
| kr_sessions | 0.1.0-draft → 1.0.0 | 1995-01-01..2027-12-31 | 23 | 2행 공식 공지 전, 21행 미대조 | (KRX 세트를 따름) |

**PT-07이 이미 바꾼 것**(모두 `signed_off_by: null`)
- holidays_KRX: 휴장 4행을 넣었다. 2026-06-03, 2026-07-17, 2027-05-03, 2027-07-19.
- holidays_SIFMA:
  - 2026-04-03을 closed에서 early_close `'12:00'`으로 바꿨다.
  - early_close `'14:00'` 5행을 넣었다. 2025-01-09, 2025-04-17, 2025-05-23, 2026-05-22, 2026-07-02.
- holidays_FED: 2027-12-31 closed를 넣었다.
- kr_sessions: csat_day 2027-11-18을 넣었다.
- holidays_NYSE: 행은 그대로이고 `how_to_sign`만 바꿨다.
- MANIFEST: 16행 모두에 `signed_utc: null` 자리를 넣었다.

**모든 파일에 공통으로 할 일**
- 바뀌지 않은 기존 행은 `source_url: null`이다. 옛 `UNVERIFIED ...` 문구도 남아 있다.
- 지금 `source_url: null`인 행 수: KRX 29, NYSE 37, FED 137, SIFMA 44, kr_sessions 22.
- 이 행들은 서명 전에 소유자가 채운다. 3.2절을 따른다.

**표 읽는 법**
- 아래 표의 "조회 시각"은 Claude가 2026-10-28에 대조한 시각이다(UTC).
- `retrieved_at_utc`에는 소유자가 출처를 실제로 연 시각을 적는다.
- `source_url`에 URL 여러 개를 넣을 때는 PT-07의 새 행처럼 `' | '`로 잇는다. 예: `'URL1 | URL2'`.

### 2.1 holidays_KRX

**출처 기호**

| 기호 | 출처 | URL |
|---|---|---|
| K1 | KRX 2026년 올빼미공시 안내(PDF) | https://kind.krx.co.kr/external/dst/notice/11637/[%ED%95%9C%EA%B5%AD%EA%B1%B0%EB%9E%98%EC%86%8C]%202026%EB%85%84%20%EC%98%AC%EB%B9%BC%EB%AF%B8%EA%B3%B5%EC%8B%9C%20%EC%95%88%EB%82%B4.pdf |
| K2 | KRX 휴장일 규정 | https://regulation.krx.co.kr/contents/RGL/04/04010102/RGL04010102.jsp |
| K3 | KRX 공매도 모의거래인증시스템 게시판 | https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list |
| G1 | 한국천문연구원 2026 월력자료 | https://astro.kasi.re.kr/kor/life/post/calendarData?year=2026 |
| G2 | 한국천문연구원 2027 월력자료 | https://astro.kasi.re.kr/kor/life/post/calendarData?year=2027 |
| G3 | 우주항공청 2026 월력요항 | https://www.kasa.go.kr/bbs/BBSMSTR_000000000010/view.do?nttId=B000000001860Pe2zT3 |
| G4 | 우주항공청 2027 월력요항(2026-06-29) | https://www.kasa.go.kr/prog/plcyBrf/brief/kor/sub01_01_04/view.do?plcyBrfNo=431 |
| G5 | 인사혁신처 보도자료 '올해부터 노동절, 제헌절 공휴일로' | https://www.korea.kr/briefing/pressReleaseView.do?newsId=156758983 |
| G6 | 「관공서의 공휴일에 관한 규정」 제·개정이유(대통령령 제36290호) | https://law.go.kr/LSW/lsRvsRsnListP.do?lsId=002404&chrClsCd=010102 |
| G7 | 중앙선거관리위원회(제9회 전국동시지방선거) | https://www.nec.go.kr/site/nec/ex/bbs/View.do?cbIdx=1104&bcIdx=289351 |
| G8 | 인사혁신처 공휴일 제도 | https://www.mpm.go.kr/mpm/info/infoService/BizService02/ |

**행 표**

| 날짜 | 내용 | 출처 | 조회 시각 | 판정 |
|---|---|---|---|---|
| 2026-01-01 | 신정(목). 관공서 공휴일이고 KRX는 이날 휴장 | G1, K2 | 2026-10-28T05:35:34Z | 공식 확인 |
| 2026-02-16 | 설 연휴. K1 표 '설(2/14~2/18)' | K1, G3 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-02-17 | 설날 | K1, G3 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-02-18 | 설 연휴 | K1, G3 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-03-02 | 3·1절(3/1 일)의 대체공휴일 | K1, G3 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-05-01 | 노동절(금). K1 '노동절(5/1~5/3)'. 대통령령 제36290호 | K1, G5 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-05-05 | 어린이날(화) | G1, K2 | 2026-10-28T05:35:34Z | 공식 확인 |
| 2026-05-25 | 부처님오신날(5/24 일)의 대체공휴일 | K1, G1 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-06-03 | 제9회 전국동시지방선거(새 행, CAL-01) | K3, G7, G8 | 2026-10-28T05:31:34Z | 공식 확인 |
| 2026-07-17 | 제헌절 공휴일 재지정(새 행, CAL-01) | G5, G6, K3 | 2026-10-28T05:31:34Z | 공식 확인 |
| 2026-08-17 | 광복절(8/15 토)의 대체공휴일 | K1, G3 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-09-24 | 추석 연휴 | K1, G1 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-09-25 | 추석 | K1, G1 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-10-05 | 개천절(10/3 토)의 대체공휴일 | K1, G3 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-10-09 | 한글날(금) | K1, G1 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-12-25 | 기독탄신일(금) | K1, G1 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2026-12-31 | 연말 휴장. 마지막 매매일은 12-30(수), 종료 15:30 | K1, K2 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2027-01-01 | 신정(금). K1 '새해(12.31~'27.01.03)' | K1, G4 | 2026-10-28T05:28:08Z | 공식 확인 |
| 2027-02-08 | 설 연휴(월) | G4, G2 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-02-09 | 설날(2/7 일)의 대체공휴일 | G4, G2 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-03-01 | 3·1절(월) | G4 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-05-03 | 노동절(5/1 토)의 대체공휴일(새 행, CAL-02) | G4, G6 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-05-05 | 어린이날(수) | G2 | 2026-10-28T05:30:37Z | 공식 공지 전(근거 기재) |
| 2027-05-13 | 부처님오신날(목) | G2 | 2026-10-28T05:30:37Z | 공식 공지 전(근거 기재) |
| 2027-07-19 | 제헌절(7/17 토)의 대체공휴일(새 행, CAL-02) | G4, G6 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-08-16 | 광복절(8/15 일)의 대체공휴일 | G4 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-09-14 | 추석 연휴 | G4, G2 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-09-15 | 추석 | G4, G2 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-09-16 | 추석 연휴 | G4, G2 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-10-04 | 개천절(10/3 일)의 대체공휴일 | G4 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-10-11 | 한글날(10/9 토)의 대체공휴일 | G4, G2 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-12-27 | 기독탄신일(12/25 토)의 대체공휴일 | G4 | 2026-10-28T05:29:52Z | 공식 공지 전(근거 기재) |
| 2027-12-31 | 연말 휴장(금). KRX 규정 | K2 | 2026-10-28T05:33:29Z | 공식 공지 전(근거 기재) |

**소유자가 직접 확인할 행**
1. **33행 전부**
   - 출처를 직접 연다.
   - 각 행에 `source_url`, `retrieved_at_utc`, `signed_off_by`를 쓴다. 이 중 29행은 지금 `source_url: null`이다.
   - 29행의 name 자리표시 `KRX holiday (name from the KRX notice at sign-off)`는 표의 "내용"으로 바꾸기를 권한다.
   - 29행의 `UNVERIFIED cross-check only ...` 문구는 지우거나 남은 의문만 적는다.
   - 이 모두를 md5를 읽기 전에 끝낸다.
2. **2026-06-03**
   - KRX 2026-05-20 휴장 공지 원문은 krx.co.kr 검색에서 찾지 못했다. 언론 보도만 있었다.
   - 판정의 근거는 K3 게시판 글('2026년 6월 3일(수요일)은 지방선거일로 임시공휴일 입니다', 2026-06-01 게시), G7, G8이다.
   - KRX 공지 원문을 찾으면 `source_url`에 더한다.
3. **2026-07-17**
   - 날짜(휴장)는 맞다.
   - 대통령령 제36290호의 시행일은 출처마다 갈린다(2026-05-01 / 2026-05-11). law.go.kr 부칙으로 확인하고 행의 `unverified`를 정리한다.
   - K3 게시판 문구는 2026-10-28 재검색에서 재현되지 않았다. 휴장 사실은 KRX 2026-05-20 휴장 공지 보도(bizwatch)로 확인된다.
   - K1 표에는 7/17 행이 없다. 법 개정 전에 작성된 것으로 보인다.
4. **2026-01-01, 2026-05-05**
   - KRX 자체 문서에서 이 날짜를 적은 발췌를 찾지 못했다. 하루짜리 휴장이라 K1 표의 대상이 아니다.
   - 정부 달력(G1)과 KRX 규정(K2)으로 판정했다.
5. **2027년 15행(공식 공지 전)**
   - 근거는 G4(2027 월력요항)와 K2다.
   - KRX 2027 휴장일 공지(2026년 12월 예상)가 나오면 다시 대조한다. 다르면 v1.0.1로 재서명한다. 6.3절의 테스트 문제를 먼저 본다.
   - 2027-12-31은 유가증권시장 업무규정 제5조 원문을 확보하지 못했다.
6. **2026-09-28(행 없음)**
   - 임시공휴일로 지정되지 않았다(언론 보도, 공식 의결 자료 없음). 그래서 행이 없다.
   - 지난 날짜이므로 그날 KRX가 열렸는지 확인한다.
7. **머리말 `unverified` 5줄**: 소유자 대조 결과에 맞게 고친다. 선택이며, md5를 읽기 전에 한다.

**서명 문장**(한 줄로 붙여 넣는다. `<성명>`, `<YYYY-MM-DD>`만 채운다)
```yaml
sign_off_statement: '본인 <성명>은 holidays_KRX v1.0.0의 모든 행을 KRX 2026년 올빼미공시 안내(kind.krx.co.kr), KRX 휴장일 규정(regulation.krx.co.kr), KRX 공매도 모의거래인증시스템 게시판(strn.krx.co.kr), 중앙선거관리위원회 제9회 전국동시지방선거 안내(nec.go.kr), 인사혁신처 공휴일 제도 안내와 보도자료(mpm.go.kr, korea.kr newsId=156758983), 「관공서의 공휴일에 관한 규정」 대통령령 제36290호(law.go.kr), 한국천문연구원 2026·2027 월력자료(astro.kasi.re.kr), 우주항공청 2026·2027 월력요항(kasa.go.kr)과 <YYYY-MM-DD>에 대조하였다. 2026-01-01부터 2027-12-31까지 휴장 행이 공식 출처와 일치함을 확인한다. 공식 공지가 아직 없는 2027년 행(2027-02-08, 2027-02-09, 2027-03-01, 2027-05-03, 2027-05-05, 2027-05-13, 2027-07-19, 2027-08-16, 2027-09-14, 2027-09-15, 2027-09-16, 2027-10-04, 2027-10-11, 2027-12-27, 2027-12-31)은 2027 월력요항(우주항공청 2026-06-29)과 KRX 휴장일 규정(관공서 공휴일 휴장, 12월 31일 휴장)에 따른 것이다. KRX 2027년 휴장일 공지가 나오면 다시 대조하고, 차이가 있으면 새 버전으로 재서명한다. 이 파일은 2026-01-01..2027-12-31 밖의 날짜를 보증하지 않는다.'
```

### 2.2 holidays_NYSE

**출처 기호**

| 기호 | 출처 | URL |
|---|---|---|
| N1 | NYSE Group 2025·2026·2027 휴장·조기폐장 발표(2024-11-08) | https://ir.theice.com/press/news-details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx |
| N2 | NYSE Group 2026·2027·2028 휴장·조기폐장 발표(2025-12-23) | https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx |
| N3 | 2025-01-09 국가 애도일 휴장 발표(2024-12-30) | https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx |

**행 표**(휴장 31행, 조기폐장 6행, 총 37행. 모두 공식 확인)

| 날짜 | 내용 | 출처 | 조회 시각 | 판정 |
|---|---|---|---|---|
| 2025-01-01 | New Year's Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-01-09 | 국가 애도일(Carter), 비정기 휴장 | N3 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2025-01-20 | Martin Luther King, Jr. Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-02-17 | Washington's Birthday | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-04-18 | Good Friday | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-05-26 | Memorial Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-06-19 | Juneteenth | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-07-04 | Independence Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-09-01 | Labor Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-11-27 | Thanksgiving Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-12-25 | Christmas Day | N1 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-01-01 | New Year's Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-01-19 | Martin Luther King, Jr. Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-02-16 | Washington's Birthday | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-04-03 | Good Friday. NYSE는 휴장이고, SIFMA는 12:00 조기폐장 | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-05-25 | Memorial Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-06-19 | Juneteenth | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-07-03 | Independence Day (observed) | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-09-07 | Labor Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-11-26 | Thanksgiving Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2026-12-25 | Christmas Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-01-01 | New Year's Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-01-18 | Martin Luther King, Jr. Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-02-15 | Washington's Birthday | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-03-26 | Good Friday | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-05-31 | Memorial Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-06-18 | Juneteenth (observed) | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-07-05 | Independence Day (observed) | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-09-06 | Labor Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-11-25 | Thanksgiving Day | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2027-12-24 | Christmas Day (observed) | N2 | 2026-10-28T05:28:48Z | 공식 확인 |
| 2025-07-03 | 조기폐장 13:00 ET(대상 옵션은 13:15) | N1 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2025-11-28 | 조기폐장 13:00 ET | N1 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2025-12-24 | 조기폐장 13:00 ET | N1 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2026-11-27 | 조기폐장 13:00 ET | N2 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2026-12-24 | 조기폐장 13:00 ET | N2 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2027-11-26 | 조기폐장 13:00 ET. 2027년 조기폐장은 이날 하나다 | N2 | 2026-10-28T05:27:47Z | 공식 확인 |
| 2027-12-31 | **행 없음 = 개장**. 2028-01-01이 토요일이라 신정 대체 휴장이 없다 | N2 | 2026-10-28T05:28:48Z | 공식 확인 |

**소유자가 직접 확인할 행**
1. **37행 전부**
   - 모두 `source_url: null`이다. 표의 N1, N2, N3을 연다.
   - 각 행의 `UNVERIFIED: derived by the statutory holiday rule ...` 문구를 지우거나 고친다.
   - 2025-01-09는 비정기 휴장이므로 이 문구가 **틀렸다**. 반드시 고친다.
2. **2027-12-31**
   - 행이 없어야 한다(개장).
   - N2의 각주 'no New Year's Day holiday is observed'를 확인한다.
   - 테스트 `MUST_NOT_CLOSED`가 이 상태를 지킨다.
3. **선택**: 2026-07-03, 2027-06-18, 2027-12-24의 name에 `(observed)`를 붙인다. md5를 읽기 전에만 한다.
4. **머리말 `unverified`**
   - 지금 문구는 `dates derived by rule ...; early closes 13:00 ET by the usual pattern`이다.
   - 대조를 마치면 사실과 맞지 않으므로 고친다. md5를 읽기 전에 한다.

**서명 문장**
```yaml
sign_off_statement: '본인 <성명>은 holidays_NYSE v1.0.0의 모든 행을 NYSE Group의 2025·2026·2027년 휴장·조기폐장 발표(ir.theice.com, 2024-11-08), 2026·2027·2028년 휴장·조기폐장 발표(ir.theice.com, 2025-12-23), 2025-01-09 국가 애도일 휴장 발표(ir.theice.com, 2024-12-30)와 <YYYY-MM-DD>에 대조하였다. 2025-01-01부터 2027-12-31까지 휴장 행과 13:00 ET 조기폐장 행이 공식 출처와 일치함을 확인한다. 공식 공지가 아직 없는 2027년 행은 없다. 2027년 행은 2025-12-23 발표의 2027년 일정에 따른 것이며, 2028-01-01이 토요일이라 신정 대체 휴장이 없으므로 2027-12-31은 개장일이다. NYSE가 일정을 바꾸면 다시 대조하고 새 버전으로 재서명한다. 이 파일은 2025-01-01..2027-12-31 밖의 날짜를 보증하지 않는다.'
```

### 2.3 holidays_FED

**출처 기호**

| 기호 | 출처 | URL |
|---|---|---|
| F1 | Federal Reserve Board K.8 휴무 일정 | https://www.federalreserve.gov/aboutthefed/k8.htm |
| F2 | OPM 연방 공휴일 표('Historical Data' 탭) | https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/ |

- F2는 2015–2025년 행에 쓸 출처 후보다.
- Claude는 F2를 검색 결과 목록에서만 봤다. 열어서 대조하지는 않았다.

**행 표: 2026–2027년 23행**
- 모두 출처는 F1, 조회 시각은 2026-10-28T05:33:59Z, 판정은 **확인 실패**다.
- 원문 열람이 차단됐다. 검색 발췌는 모든 행과 일치했다.
- 같은 수준의 근거로 KRX와 NYSE는 공식 확인을 받았지만, FED는 확인 실패로 남겼다.

| 날짜 | 내용 | 출처 | 조회 시각 | 판정 |
|---|---|---|---|---|
| 2026-01-01 | New Year's Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-01-19 | Birthday of Martin Luther King, Jr. | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-02-16 | Washington's Birthday | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-05-25 | Memorial Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-06-19 | Juneteenth | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-07-03 | Independence Day(7/4 토). Board는 휴무, Reserve Banks는 영업 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-09-07 | Labor Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-10-12 | Columbus Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-11-11 | Veterans Day. NYSE는 영업 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-11-26 | Thanksgiving Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2026-12-25 | Christmas Day. 2026-12-24 휴무 행정명령은 찾지 못했다 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-01-01 | New Year's Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-01-18 | Birthday of Martin Luther King, Jr. | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-02-15 | Washington's Birthday | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-05-31 | Memorial Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-06-18 | Juneteenth(6/19 토). Board는 휴무, Reserve Banks는 영업 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-07-05 | Independence Day(7/4 일). Banks와 Board 모두 휴무 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-09-06 | Labor Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-10-11 | Columbus Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-11-11 | Veterans Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-11-25 | Thanksgiving Day | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-12-24 | Christmas(12/25 토). Board는 휴무, Reserve Banks는 영업 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |
| 2027-12-31 | 새 행(CAL-05). New Year's Day 2028(토)의 대체일. Board는 휴무, Reserve Banks는 영업. K.8이 2026-07-08에 '2028'을 '2027'로 정정 | F1 | 2026-10-28T05:33:59Z | 확인 실패 |

**2015–2025년 115행: 미대조**
- 출처 후보는 F2다. 연도별 날짜는 다음과 같다.
  - 2015(10): 01-01, 01-19, 02-16, 05-25, 07-03, 09-07, 10-12, 11-11, 11-26, 12-25
  - 2016(10): 01-01, 01-18, 02-15, 05-30, 07-04, 09-05, 10-10, 11-11, 11-24, 12-26
  - 2017(10): 01-02, 01-16, 02-20, 05-29, 07-04, 09-04, 10-09, 11-10, 11-23, 12-25
  - 2018(10): 01-01, 01-15, 02-19, 05-28, 07-04, 09-03, 10-08, 11-12, 11-22, 12-25
  - 2019(10): 01-01, 01-21, 02-18, 05-27, 07-04, 09-02, 10-14, 11-11, 11-28, 12-25
  - 2020(10): 01-01, 01-20, 02-17, 05-25, 07-03, 09-07, 10-12, 11-11, 11-26, 12-25
  - 2021(12): 01-01, 01-18, 02-15, 05-31, 06-18, 07-05, 09-06, 10-11, 11-11, 11-25, 12-24, 12-31
  - 2022(10): 01-17, 02-21, 05-30, 06-20, 07-04, 09-05, 10-10, 11-11, 11-24, 12-26
  - 2023(11): 01-02, 01-16, 02-20, 05-29, 06-19, 07-04, 09-04, 10-09, 11-10, 11-23, 12-25
  - 2024(11): 01-01, 01-15, 02-19, 05-27, 06-19, 07-04, 09-02, 10-14, 11-11, 11-28, 12-25
  - 2025(11): 01-01, 01-20, 02-17, 05-26, 06-19, 07-04, 09-01, 10-13, 11-11, 11-27, 12-25
- 토요일 공휴일 때문에 금요일을 휴무로 둔 행: 2015-07-03, 2017-11-10, 2020-07-03, 2021-06-18, 2021-12-24, 2021-12-31.
  - 2022-01-01(토)은 2021-12-31로 당겼다. 그래서 2022년에는 01-01 행이 없다.
  - 2023-11-10도 같은 경우다.

**소유자가 직접 확인할 행**
1. **2026–2027년 23행**
   - 지금의 k8.htm을 열어 대조한다.
   - 2026-07-08 이전 사본이나 다른 곳에서 퍼 온 자료에는 '2028' 오기가 남아 있을 수 있다.
   - 22행은 `source_url: null`이다.
2. **2015–2025년 115행**
   - Claude는 대조하지 않았다.
   - 서명 문장은 2015-01-01..2027-12-31 전체를 대조했다고 말한다. 그래서 이 행들도 소유자가 F2 같은 공식 표와 대조해야 한다.
   - 대조하지 못하면 이 문장으로 서명하지 않는다(감사 12.1: "대조하지 않은 행에는 서명하지 않는다").
3. **행이 없는 날 가운데 확인할 후보**(Claude 미확인)
   - 연방 정부가 행정명령이나 국가 애도일로 쉰 날: 2018-12-05, 2018-12-24, 2019-12-24, 2020-12-24, 2025-01-09, 2025-12-24(대조 메모의 EO 14371).
   - 워싱턴 DC 지역 공무원의 취임일 휴일: 2017-01-20, 2021-01-20.
   - Board가 그날 휴무했으면 행을 넣고 서명한다. 휴무하지 않았으면 그대로 둔다.
4. **나머지 정리**
   - 137행의 `UNVERIFIED: derived by the statutory holiday rule ...`를 정리한다.
   - 머리말 첫 줄(`derived by the federal holiday rule ...; owner confirms ...`)도 고친다. 선택이며, md5를 읽기 전에 한다.

**서명 문장**
```yaml
sign_off_statement: '본인 <성명>은 holidays_FED v1.0.0의 모든 행을 연방준비제도 이사회 휴무 일정 K.8(federalreserve.gov/aboutthefed/k8.htm, 2026-07-08 정정 반영판)과 미국 인사관리처 연방 공휴일 표(opm.gov federal-holidays, 2015–2025년)와 <YYYY-MM-DD>에 대조하였다. 2015-01-01부터 2027-12-31까지 Board 휴무 행이 공식 출처와 일치함을 확인한다. 공휴일이 토요일이면 Board는 전 금요일에 휴무하고 Reserve Banks는 영업한다. 이 파일은 Board 게시 일정(fed_business_day)에 쓰이므로 그 금요일(2026-07-03, 2027-06-18, 2027-12-24, 2027-12-31 등)을 휴무로 둔다. 공식 공지가 아직 없는 2027년 행은 없다. 2027년 행은 K.8의 2027년 일정에 따른 것이며, 2027-12-31은 K.8 각주(2028-01-01 신정을 Board가 2027-12-31에 휴무)에 따른 것이다. K.8이 바뀌면 다시 대조하고 새 버전으로 재서명한다. 이 파일은 2015-01-01..2027-12-31 밖의 날짜를 보증하지 않는다.'
```
- 2015–2025년 행을 F2가 아닌 다른 공식 출처로 대조했으면, 문장의 "미국 인사관리처 연방 공휴일 표(opm.gov federal-holidays, 2015–2025년)" 부분을 그 출처로 바꾼다. md5를 읽기 전에 한다.

### 2.4 holidays_SIFMA

**출처 기호**
- 보도자료 URL은 모두 `https://www.sifma.org/news/press-releases/` 뒤에 아래 경로를 붙인다.

| 기호 | 경로 또는 URL |
|---|---|
| S0 | https://www.sifma.org/resources/guides-playbooks/holiday-schedule (holiday schedule. 2026·2027 U.S. 권고는 2025-12-17 발표) |
| S1 | sifma-recommends-early-market-close-on-december-31-and-a-full-market-close-on-january-1-2025-in-the-u-s-in-observance-of-the-new-years-day-holiday-2024 |
| S2 | sifma-recommends-early-market-close-on-january-9-2025-for-the-national-day-of-mourning-in-honor-of-former-president-carter |
| S3 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-the-u-s-martin-luther-king-day-2025 |
| S4 | sifma-fixed-income-market-close-recommendation-in-the-u-s-the-u-k-and-japan-for-presidents-day-2025 |
| S5 | sifma-recommends-an-early-market-close-on-april-17-and-a-full-market-close-on-april-18-in-the-u-s-in-observance-of-good-friday-2025 |
| S6 | sifma-recommends-an-early-market-close-on-may-23-and-a-full-market-close-on-may-26-in-the-u-s-in-observance-of-the-memorial-day-holiday-2025 |
| S7 | sifma-fixed-income-market-close-recommendation-in-the-u-s-the-u-k-and-japan-for-juneteenth-2025 |
| S8 | sifma-recommends-an-early-market-close-on-july-3-and-a-full-market-close-on-july-4-in-the-u-s-in-observance-of-the-independence-day-holiday-2025 |
| S9 | sifma-fixed-income-market-close-recommendation-in-the-u-s-the-u-k-and-japan-for-u-s-labor-day-holiday-2025 |
| S10 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-u-s-columbus-day-and-japan-health-and-sports-day-holidays-2025 |
| S11 | sifma-fixed-income-market-close-recommendation-in-the-u-s-the-u-k-and-japan-for-the-u-s-veterans-day-holiday-2025 |
| S12 | sifma-recommends-a-full-market-close-on-november-27-and-an-early-market-close-on-november-28-in-the-u-s-in-observance-of-the-thanksgiving-day-holiday |
| S13 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-the-christmas-day-and-u-k-boxing-day-holidays-2025 |
| S14 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-new-years-day-holiday-2025 |
| S15 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-the-u-s-martin-luther-king-day-2026 |
| S16 | sifma-fixed-income-market-close-recommendation-in-the-us-the-uk-and-japan-for-presidents-day-2026 |
| S17 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-good-friday-easter-monday-holidays-2026 |
| S18 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-the-u-s-memorial-day-holiday-2026 |
| S19 | sifma-fixed-income-market-close-recommendation-in-the-u-s-the-u-k-and-japan-for-juneteenth-2026 |
| S20 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-the-u-s-independence-day-holiday-2026 |
| S21 | sifma-fixed-income-market-close-recommendation-in-the-u-s-the-u-k-and-japan-for-u-s-labor-day-holiday-2026 |
| S22 | sifma-fixed-income-market-close-recommendations-in-the-u-s-the-u-k-and-japan-for-u-s-columbus-day-and-japan-health-and-sports-day-holidays-2026 |
| NYF | https://www.newyorkfed.org/markets/opolicy/operating_policy_260312 (2026-04-03의 보조 출처) |

**행 표**(50행)

| 날짜 | 내용 | 출처 | 조회 시각 | 판정 |
|---|---|---|---|---|
| 2025-01-01 | 휴장 | S1 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-01-09 | 조기폐장 14:00(Carter 국가 애도일). 새 행 | S2 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-01-20 | 휴장(MLK) | S3 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-02-17 | 휴장(Presidents Day) | S4 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-04-17 | 조기폐장 14:00. 새 행. 시각은 검색 요약에서 읽음 | S5 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-04-18 | 휴장(Good Friday) | S5 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-05-23 | 조기폐장 14:00. 새 행. 시각은 검색 요약에서 읽음 | S6 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-05-26 | 휴장(Memorial Day) | S6 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-06-19 | 휴장(Juneteenth) | S7 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-07-03 | 조기폐장 14:00 | S8 | 2026-10-28T05:40:23Z | 공식 확인 |
| 2025-07-04 | 휴장 | S8 | 2026-10-28T05:40:23Z | 공식 확인 |
| 2025-09-01 | 휴장(Labor Day) | S9 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-10-13 | 휴장(Columbus Day) | S10 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-11-11 | 휴장(Veterans Day) | S11 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-11-27 | 휴장(Thanksgiving) | S12 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-11-28 | 조기폐장 14:00 | S12 | 2026-10-28T05:42:04Z | 공식 확인 |
| 2025-12-24 | 조기폐장 14:00 | S13 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-12-25 | 휴장 | S13 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2025-12-31 | 조기폐장 14:00 | S14 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2026-01-01 | 휴장 | S14 | 2026-10-28T05:39:19Z | 공식 확인 |
| 2026-01-19 | 휴장(MLK) | S15 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-02-16 | 휴장 | S16 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-04-03 | 조기폐장 **12:00**(Good Friday, 고용지표 발표일). HEAD의 closed를 고침 | S17, S0, NYF | 2026-10-28T05:37:29Z | 공식 확인(HEAD 행은 불일치) |
| 2026-05-22 | 조기폐장 14:00. 새 행 | S18 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-05-25 | 휴장 | S18 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-06-19 | 휴장 | S19 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-07-02 | 조기폐장 14:00. 새 행 | S20 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-07-03 | 휴장 | S20 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-09-07 | 휴장 | S21 | 2026-10-28T05:43:01Z | 공식 확인 |
| 2026-10-12 | 휴장 | S22 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-11-11 | 휴장. 일정표 기준이고 개별 보도자료는 아직 없음 | S0 | 2026-10-28T05:43:01Z | 공식 확인 |
| 2026-11-26 | 휴장 | S0 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-11-27 | 조기폐장 14:00 | S0 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-12-24 | 조기폐장 14:00 | S0 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-12-25 | 휴장 | S0 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2026-12-31 | 조기폐장 14:00 | S0 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2027-01-01 | 휴장 | S0 | 2026-10-28T05:39:51Z | 공식 확인 |
| 2027-01-18 | 휴장(1월 셋째 월요일) | S0 | 2026-10-28T05:40:23Z | 확인 실패 |
| 2027-02-15 | 휴장 | S0 | 2026-10-28T05:40:23Z | 확인 실패 |
| 2027-03-26 | 휴장(Good Friday). 고용지표 발표일이면 12:00 조기폐장으로 바뀐다 | S0 | 2026-10-28T05:40:23Z | 확인 실패 |
| 2027-05-31 | 휴장 | S0 | 2026-10-28T05:40:23Z | 확인 실패 |
| 2027-06-18 | 휴장. **위험 행**(Juneteenth가 토요일) | S0 | 2026-10-28T05:40:23Z | 확인 실패 |
| 2027-07-05 | 휴장 | S0 | 2026-10-28T05:41:03Z | 확인 실패 |
| 2027-09-06 | 휴장 | S0 | 2026-10-28T05:41:03Z | 확인 실패 |
| 2027-10-11 | 휴장 | S0 | 2026-10-28T05:41:03Z | 확인 실패 |
| 2027-11-11 | 휴장 | S0 | 2026-10-28T05:41:03Z | 확인 실패 |
| 2027-11-25 | 휴장 | S0 | 2026-10-28T05:41:03Z | 확인 실패 |
| 2027-11-26 | 조기폐장 14:00 | S0 | 2026-10-28T05:41:03Z | 확인 실패 |
| 2027-12-24 | 휴장(12/25 토. 2021년 선례) | S0 | 2026-10-28T05:43:01Z | 확인 실패 |
| 2027-12-31 | 조기폐장 14:00(2028-01-01 토. 휴장 없음. 2021년 선례) | S0 | 2026-10-28T05:41:03Z | 확인 실패 |

**넣지 않은 행**(감사 7.1 제안)

| 날짜 | 제안 | 출처 | 조회 시각 | 판정과 처리 |
|---|---|---|---|---|
| 2026-04-02 | 조기폐장 14:00 | S0 | 2026-10-28T05:41:03Z | 확인 실패. 지난 날짜이고, 일정표의 2026 Good Friday 항목에는 04-03 12:00만 있다. **넣지 않는다.** 서명 문장에 "미확인으로 제외"로 적는다 |
| 2027-03-25 | 조기폐장 14:00 | S0 | 2026-10-28T05:41:03Z | 확인 실패. 일정표에 있을 때만 서명 전에 넣는다. 2027-03-26이 12:00 조기폐장이면 이 조기폐장은 없어질 수 있다 |
| 2027-05-28 | 조기폐장 14:00 | S0 | 2026-10-28T05:41:03Z | 확인 실패. 일정표에 있을 때만 서명 전에 넣는다 |
| 2027-07-02 | 조기폐장 14:00 | S0 | 2026-10-28T05:41:03Z | 확인 실패. 일정표에 있을 때만 서명 전에 넣는다 |
| 2027-12-23 | 조기폐장 14:00 | S0 | 2026-10-28T05:43:01Z | 확인 실패. 일정표에 있을 때만 서명 전에 넣는다 |

**행을 넣을 때 쓰는 틀**(예: 2027-03-25. 다른 날짜도 같은 형식)
```yaml
- effective_from: '2027-03-25'
  effective_to: '2027-03-25'
  source_url: 'https://www.sifma.org/resources/guides-playbooks/holiday-schedule'
  retrieved_at_utc: '<소유자가 연 시각, YYYY-MM-DDTHH:MM:SSZ>'
  signed_off_by: '<성명>'
  date: '2027-03-25'
  kind: early_close
  close_local: '14:00'
  name: 'day before Good Friday: SIFMA 14:00 ET early close'
```
- `close_local`은 반드시 따옴표로 감싼다. 따옴표가 없으면 로더가 `unquoted time`으로 거부한다.

**소유자가 직접 확인할 행**
1. **2027년 13행(확인 실패)**
   - S0 원문을 열어 대조한다.
   - **2027-06-18**
     - 2027년 Juneteenth(06-19)는 토요일이다.
     - 2021년 SIFMA는 토요일 Juneteenth에 휴장을 권고하지 않았다. X 게시물: "we will not recommend a #fixedincome market close" (https://x.com/SIFMA/status/1405594850272198657).
     - 일정표와 그 안의 'Policy on Juneteenth National Holiday'를 확인한다.
     - 휴장 권고가 없으면 행을 지운다. 그러면 2026-11-01 이후 SIFMA 세션이 290에서 291로 바뀐다.
   - **2027-03-26**
     - 그날이 고용지표 발표일이면 12:00 조기폐장이다. 2026-04-03이 같은 경우였다.
     - 그러면 `kind: early_close`, `close_local: '12:00'`으로 바꾼다.
     - 서명 문장의 "2026-04-03은 12:00 ET"를 "2026-04-03과 2027-03-26은 12:00 ET"로 고친다.
2. **넣지 않은 2027년 조기폐장 4건**
   - 일정표에 있는 것만 위 틀로 넣는다. md5를 읽기 전에 한다.
   - 서명 뒤에 넣으면 md5가 바뀌어 다시 서명해야 한다.
3. **2025-04-17, 2025-05-23**: 14:00은 검색 요약에서 읽은 값이다. 보도자료 원문으로 확인한다.
4. **나머지 정리**
   - 44행이 `source_url: null`이다.
   - 머리말 첫 줄 `full closes = federal holidays + Good Friday; 14:00 early closes by the usual SIFMA pattern; all to confirm`을 대조 결과로 고친다. 선택이다.

**서명 문장**
```yaml
sign_off_statement: '본인 <성명>은 holidays_SIFMA v1.0.0의 모든 행을 SIFMA의 미국 채권시장 휴장·조기폐장 권고 보도자료(sifma.org/news/press-releases)와 SIFMA holiday schedule(sifma.org/resources/guides-playbooks/holiday-schedule, 2026·2027년 U.S. 권고는 2025-12-17 발표)과 <YYYY-MM-DD>에 대조하였다. 2025-01-01부터 2027-12-31까지 휴장 행과 조기폐장 행(14:00 ET, 2026-04-03은 12:00 ET)이 공식 출처와 일치함을 확인한다. 공식 공지가 아직 없는 2027년 행은 없다. 2027년 행은 holiday schedule의 2027년 U.S. 권고에 따른 것이며, 일정표에 있는 휴장·조기폐장만 넣었다. 미확인으로 제외: 2026-04-02 조기폐장(공식 출처에서 찾지 못했다. 일정표의 2026년 Good Friday 항목은 2026-04-03 12:00 ET 조기폐장 하나다). SIFMA가 권고를 바꾸면 다시 대조하고 새 버전으로 재서명한다. 이 파일은 2025-01-01..2027-12-31 밖의 날짜를 보증하지 않는다.'
```
- 이 문장은 2027년 조기폐장 4건을 넣든 넣지 않든 그대로 쓸 수 있다. 일정표에 있는 것을 모두 넣었다면 참이다.
- 2027-03-26이 12:00 조기폐장으로 바뀌는 경우에만 괄호 안을 고친다.

### 2.5 kr_sessions

**출처 기호**

| 기호 | 출처 | URL |
|---|---|---|
| R1 | 교육부 보도자료: 2027학년도 수능 2026-11-19(목) | https://m.korea.kr/briefing/pressReleaseView.do?newsId=156646031 |
| R2 | 한국경제(언론): 2025-11-13 수능일 정규장 10:00~16:30 선례 | https://www.hankyung.com/article/2025111296366 |
| R3 | 교육부 보도자료(2025-06-01): 2028학년도 수능 2027-11-18(목) | https://www.korea.kr/briefing/pressReleaseView.do?newsId=156692078 |

**행 표**(대조한 2행)

| 날짜 | 내용 | 출처 | 조회 시각 | 판정 |
|---|---|---|---|---|
| 2026-11-19 | csat_day. 수능일 자체는 공식이다(교육부 발표, 평가원 기본계획 2026-03-31). KRX 매매시간 공지는 아직 없다 | R1, R2 | 2026-10-28T05:31:58Z | 공식 공지 전(근거 기재) |
| 2027-11-18 | csat_day. 새 행(CAL-03). 평가원 기본계획(2027년 3월 예상)과 KRX 공지는 아직 없다 | R3 | 2026-10-28T05:31:58Z | 공식 공지 전(근거 기재) |

**미대조 21행**
- csat_day 18행: 2008-11-13, 2009-11-12, 2010-11-18, 2011-11-10, 2012-11-08, 2013-11-07, 2014-11-13, 2015-11-12, 2016-11-17, 2017-11-23, 2018-11-15, 2019-11-14, 2020-12-03, 2021-11-18, 2022-11-17, 2023-11-16, 2024-11-14, 2025-11-13.
- regular_open 2행: 09:30(1995-01-01..1998-12-06), 09:00(1998-12-07부터).
- lunch_break 1행: 12:00–13:00(1995-01-01..2000-05-21).

**소유자가 직접 확인할 행**
1. **2026-11-19**: `source_url`이 null이다. 행의 `unverified`는 `UNVERIFIED: date from memory of the KRX CSAT-day notices`다. R1으로 바꾼다.
2. **2027-11-18**: R3가 실제로 그 보도자료(2028학년도 수능 2027-11-18)인지 연다. 다르면 정확한 URL로 바꾼다.
3. **미대조 21행**: Claude는 대조하지 않았다. 소유자가 평가원 연도별 시행기본계획과 KRX 매매시간 변경 공지로 대조한다.
   - **2017-11-23**: 포항 지진으로 2017-11-16에서 연기됐다(행 메모). 2017-11-16에 KRX가 정상 시간으로 열었는지 확인한다.
   - **2025-11-13**: 행 메모는 'the spec's example date (L2013)'다. 출처로 바꾼다.
4. **2008년 이전 수능일 행이 없다.** 서명 문장은 이 기간을 보증하지 않는다고 적는다.
5. **창은 이 파일이 아니다.** 수능일 매매 창 10:00–16:30은 `data/macro/rules_v2.0.0.json`의 `calendars.KR.csat_session_kst`(2016-08-01부터)가 정한다. 이 서명의 대상이 아니다.

**서명 문장**
```yaml
sign_off_statement: '본인 <성명>은 kr_sessions v1.0.0의 모든 행을 교육부 대학수학능력시험 시행일 발표(korea.kr 보도자료 newsId=156646031, newsId=156692078), 한국교육과정평가원 연도별 수능 시행기본계획(2009–2027학년도), KRX 유가증권시장 매매거래시간 변경 공지(정규시장 개장 시각, 점심 휴장)와 <YYYY-MM-DD>에 대조하였다. 수능일(csat_day) 20행(2008-11-13..2027-11-18), 정규시장 개장 시각(regular_open) 2행, 점심 휴장(lunch_break) 1행이 공식 출처와 일치함을 확인한다. 평가원 시행기본계획과 KRX 공지가 아직 없는 2027년 행(2027-11-18)은 교육부 발표(2025-06-01, 2028학년도 수능 2027-11-18 시행)에 따른 것이다. 수능일 매매시간 10:00–16:30은 이 파일이 아니라 data/macro/rules_v2.0.0.json의 calendars.KR.csat_session_kst가 정하며 KRX 관행(2025-11-13 정규장 10:00–16:30)을 따른다. KRX의 수능일 매매시간 공지(2026-11-19분, 2027-11-18분)가 나오면 다시 대조하고, 차이가 있으면 새 버전으로 재서명한다. 2008년 이전 수능일, 1998-12-12 이전 토요일 장 종료 시각, 2015-06-15 이전 랜덤엔드 연장, 2016-08-01 이전 수능일 매매 창은 이 파일에 행이 없으며 보증하지 않는다. 이 파일은 1995-01-01..2027-12-31 밖의 날짜를 보증하지 않는다.'
```

**다섯 문장에 공통인 규칙**
- 서명 문장에는 md5를 넣지 않는다(감사 10.4(다) 정정). 문장은 md5 계산에 들어간다. 문장 안에 md5를 적으면 적는 순간 md5가 바뀐다.
- 위 문장들에는 작은따옴표(`'`)가 없다. 소유자가 문장을 고치면서 작은따옴표를 넣으면 `''`처럼 두 번 쓴다. YAML 작은따옴표 문자열 규칙이다.
- 리허설 2에서 이 다섯 문장을 그대로 넣었다(`<성명>`=`REHEARSAL-KIT`, `<YYYY-MM-DD>`=2026-10-28, 앞에 `REHEARSAL` 문구를 붙임). YAML로 로드되고 서명 상태까지 갔다.

---

## 3. 필드 작성 순서 (감사 10.4(라))

순서가 중요하다. md5는 `signed_off_by`, `signed_utc`, `md5` 세 키를 **뺀** 모든 내용으로 계산한다. 그래서 행, 문장, status, name, unverified, how_to_sign 중 무엇이든 한 글자만 바뀌어도 md5가 바뀐다. 모든 내용을 확정한 뒤에 md5를 읽는다.

### 3.0 준비와 PT-07 적용 확인 (Windows PowerShell, 저장소 루트)

```powershell
Set-Location C:\<저장소 경로>\quantgen
git status
python -B -c "from datetime import datetime, timezone; n=datetime.now(timezone.utc); print(n.strftime('%Y-%m-%dT%H:%M:%SZ'), 'BEFORE deadline' if n < datetime(2026,10,31,15,tzinfo=timezone.utc) else 'AFTER deadline: stop')"
(Select-String -Path core\calendars\data\MANIFEST.yaml -Pattern '^ *signed_utc: null$').Count
Select-String -Path core\calendars\data\holidays_KRX.yaml -Pattern "date: '2026-06-03'"
python -B -m core.calendars.store | Select-String -Pattern '^(signed|REFUSED) +(holidays_(KRX|NYSE|FED|SIFMA)|kr_sessions)\.yaml' -Context 0,1
python -B -m tests.macro_m1_calendars
```

기대값:
- 시각 줄 끝에 `BEFORE deadline`이 나온다.
- MANIFEST의 `signed_utc: null` 개수가 `17`이다. 최상위 1개와 16행이다. PT-07을 적용했다는 표시다.
- KRX에서 2026-06-03 줄이 1개 나온다.
- 5개 파일이 모두 `REFUSED`이고 다음 줄에 `signed_off_by is empty; an unsigned calendar file is refused (T-CAL-01)`이 나온다.
- 테스트 마지막 줄이 `22/27 passed, 0 failed, 5 not run`이다. 마감 전, 서명 전의 값이다.

편집기:
- VS Code를 권한다. UTF-8(BOM 없음)과 LF를 유지한다.
- 저장소는 `.gitattributes`에 `* -text`가 있어 줄 끝을 바꾸지 않는다.
- 줄 끝이 바뀌어도 md5는 같다(파싱한 내용으로 계산한다). 그러나 git diff가 파일 전체로 커진다.

### 3.1 단계 1: 행 필드 (파일마다)

1. 파일을 연다. 예: `code core\calendars\data\holidays_KRX.yaml`.
2. 2절의 표를 따라 각 행을 채운다.
   - `source_url: '<URL>'`. URL이 여럿이면 `' | '`로 잇는다.
   - `retrieved_at_utc: '<소유자가 출처를 연 시각, YYYY-MM-DDTHH:MM:SSZ>'`. 반드시 따옴표로 감싼다.
   - `unverified`: 지우거나 남은 의문만 적는다. 이 키는 필수가 아니다.
   - KRX의 `name` 자리표시는 표의 내용으로 바꾸기를 권한다.
3. 행의 `signed_off_by`를 한 번에 바꾼다. 들여쓰기 2칸인 행만 바뀐다. 파일 수준(들여쓰기 없음)은 3.2에서 손으로 쓴다.
   - VS Code: Ctrl+H, 정규식 켜기(Alt+R). 찾기 `^  signed_off_by: null$`, 바꾸기 `  signed_off_by: '<성명>'`.
   - 또는 PowerShell. BOM 없는 UTF-8과 LF를 유지한다.
     ```powershell
     $p = (Resolve-Path core\calendars\data\holidays_KRX.yaml).Path
     $t = [IO.File]::ReadAllText($p, [Text.UTF8Encoding]::new($false))
     $t = [regex]::Replace($t, '(?m)^  signed_off_by: null$', "  signed_off_by: '<성명>'")
     [IO.File]::WriteAllText($p, $t, [Text.UTF8Encoding]::new($false))
     ```
4. 남은 자리표시를 센다.
   ```powershell
   $f = 'core\calendars\data\holidays_KRX.yaml'
   (Select-String -Path $f -Pattern '^  signed_off_by: null$').Count
   (Select-String -Path $f -Pattern '^  source_url: null$').Count
   (Select-String -Path $f -Pattern 'UNVERIFIED').Count
   ```
   - 앞의 두 값은 0이어야 한다. 세 번째 값은 남긴 의문만큼이다.
   - 시작할 때 값(signed_off_by / source_url / UNVERIFIED):

     | 파일 | signed_off_by | source_url | UNVERIFIED |
     |---|---|---|---|
     | KRX | 33 | 29 | 29 |
     | NYSE | 37 | 37 | 37 |
     | FED | 138 | 137 | 137 |
     | SIFMA | 50 | 44 | 44 |
     | kr_sessions | 23 | 22 | 20 |

   - SIFMA에 행을 넣었으면 signed_off_by 수가 그만큼 늘어난다.

### 3.2 단계 2: 파일 수준 필드

머리말을 다음처럼 바꾼다.
```yaml
version: 1.0.0
status: SIGNED
...
signed_off_by: '<성명>'
signed_utc: '<지금 UTC>'
md5: null
sign_off_statement: '<2절의 그 파일 문장>'
```

**status**
- 지금 값은 **두 줄**이다. `status: UNSIGNED DRAFT - refused at load ...` 줄과, 그다음 들여쓰기 줄 `  DISARMED until the owner verifies and signs`.
- 두 줄을 모두 지우고 `status: SIGNED` 한 줄로 바꾼다.
- status에 "UNSIGNED"가 남아 있으면 테스트가 거부한다.

**signed_off_by**
- 행에 쓴 것과 같은 문자열을 쓴다.
- "FIXTURE"라는 말이 들어가면 안 된다.

**signed_utc**
- 다음 명령의 출력을 따옴표로 감싸 넣는다.
  ```powershell
  python -B -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
  ```
- 형식은 반드시 `YYYY-MM-DDTHH:MM:SSZ`다(M-4 검사). 그리고 **2026-10-31T15:00:00Z보다 앞서야** 한다.
- 다섯 파일에 같은 값을 써도 된다.

**sign_off_statement**
- `md5: null` 바로 아래에 한 줄로 넣는다. 위치는 결과에 영향이 없다.

**선택 사항**: `unverified`(머리말)와 `how_to_sign`은 남기거나 고친다. 둘 다 md5에 들어가므로 지금 확정한다.

### 3.3 단계 3: md5 읽기

```powershell
python -B -m core.calendars.store | Select-String -Pattern '^(signed|REFUSED) +(holidays_(KRX|NYSE|FED|SIFMA)|kr_sessions)\.yaml' -Context 0,1
```

기대값(파일마다 두 줄):
```
> REFUSED  holidays_KRX.yaml                v1.0.0 md5=<32자리>
    holidays_KRX.yaml: md5 None != content md5 <같은 32자리>; an edit under an old signature is an unsigned change
```
- 사유 줄이 `md5 None != content md5 ...`일 때만 그 32자리를 쓴다.
- 사유가 다르면 먼저 고친다(3.9절).
- 서명 전 초안 상태의 md5(`signed_off_by is empty`가 함께 나오는 값)는 쓰지 않는다.
- 리허설에서 이 단계 출력이 위 형식대로 나온 것을 확인했다.

### 3.4 단계 4: 파일에 md5 쓰기

- `md5: null`을 `md5: '<3단계의 32자리>'`로 바꾼다. 따옴표를 붙인다.
- md5 키는 계산에서 빠진다. 그래서 이 줄을 써도 md5는 바뀌지 않는다.
- 다른 곳을 하나라도 고치면 3단계로 돌아간다.
- 이 단계 뒤 store의 기대 사유: `MANIFEST.yaml row (version '0.1.0-draft', md5 None) does not match the file ('1.0.0', <md5>)`.

### 3.5 단계 5: MANIFEST.yaml

`core\calendars\data\MANIFEST.yaml`의 다섯 행 블록을 다음으로 바꾼다. 기존 test_ids에 `T-CAL-01`과 `T-CAL-02`를 더한다.

```yaml
- file: holidays_KRX.yaml
  version: 1.0.0
  md5: '<KRX md5>'
  signed_off_by: '<성명>'
  signed_utc: '<파일과 같은 값>'
  test_ids:
  - T-CLOSE-02
  - T-SAT-01
  - T-TZ-02
  - T-CAL-01
  - T-CAL-02
- file: holidays_NYSE.yaml
  version: 1.0.0
  md5: '<NYSE md5>'
  signed_off_by: '<성명>'
  signed_utc: '<파일과 같은 값>'
  test_ids:
  - T-CLOSE-01
  - T-CLOSE-02
  - T-TZ-01
  - T-CAL-01
  - T-CAL-02
- file: holidays_FED.yaml
  version: 1.0.0
  md5: '<FED md5>'
  signed_off_by: '<성명>'
  signed_utc: '<파일과 같은 값>'
  test_ids:
  - T-H15-01
  - T-H10-02
  - T-AVAIL-01
  - T-CAL-01
  - T-CAL-02
- file: holidays_SIFMA.yaml
  version: 1.0.0
  md5: '<SIFMA md5>'
  signed_off_by: '<성명>'
  signed_utc: '<파일과 같은 값>'
  test_ids:
  - T-STALE-01
  - T-H15-01
  - T-CAL-01
  - T-CAL-02
```
- `kr_sessions.yaml` 행은 `holidays_SIFMA.yaml` 다음이 아니라 파일 뒤쪽(`market_closes.yaml` 앞)에 있다.
  ```yaml
  - file: kr_sessions.yaml
    version: 1.0.0
    md5: '<kr_sessions md5>'
    signed_off_by: '<성명>'
    signed_utc: '<파일과 같은 값>'
    test_ids:
    - T-CLOSE-01
    - T-CLOSE-02
    - T-SAT-01
    - T-CAL-01
    - T-CAL-02
  ```
- MANIFEST 최상위도 바꾼다.
  ```yaml
  version: 1.0.0
  signed_off_by: '<성명>'
  signed_utc: '<같은 값>'
  status: 'PARTIALLY SIGNED: holidays_KRX, holidays_NYSE, holidays_FED, holidays_SIFMA and kr_sessions signed by the owner; the other 11 files are unsigned drafts and refused'
  ```
  - 최상위 version이 `CalendarSet.version`이 된다. 이벤트의 `calendar_version`에 찍힌다.
- 나머지 11행은 그대로 둔다.
- 로더는 MANIFEST 행과 파일의 version, md5, signed_off_by, signed_utc가 모두 같은지 본다. test_ids가 비어 있으면 거부한다.

### 3.6 단계 6: 다시 확인

```powershell
python -B -m core.calendars.store | Select-String -Pattern '^(signed|REFUSED) +(holidays_(KRX|NYSE|FED|SIFMA)|kr_sessions)\.yaml'
(python -B -m core.calendars.store | Select-String -Pattern '^REFUSED ').Count
```
- 다섯 줄이 모두 `signed   ... v1.0.0 md5=<값>`이어야 한다.
- REFUSED 개수는 `11`이다.
- 리허설 1과 2 모두 5 signed / 11 REFUSED였다.

### 3.7 단계 7: 증명과 커밋

1. 4절의 증명 명령을 먼저 돌린다. 기대값을 본 뒤 커밋한다.
2. 파일을 올리고 확인한다.
   ```powershell
   git add core/calendars/data/holidays_KRX.yaml core/calendars/data/holidays_NYSE.yaml core/calendars/data/holidays_FED.yaml core/calendars/data/holidays_SIFMA.yaml core/calendars/data/kr_sessions.yaml core/calendars/data/MANIFEST.yaml
   git diff --cached --stat
   ```
   - `6 files changed`가 나와야 한다.
3. 커밋 메시지를 쓰고 커밋한다.
   ```powershell
   notepad "$env:TEMP\calendar_signoff_msg.txt"
   git commit -F "$env:TEMP\calendar_signoff_msg.txt"
   ```
4. 메시지 틀. 파일마다 version, md5, signed_utc, 서명 문장 전문을 남긴다(감사 10.4(라)7).
   ```
   캘린더 서명: holidays_KRX, holidays_NYSE, holidays_FED, holidays_SIFMA, kr_sessions v1.0.0

   signed_off_by: <성명>
   signed_utc: <signed_utc>

   holidays_KRX v1.0.0 md5 <md5>
     sign_off_statement: <문장 전문>
   holidays_NYSE v1.0.0 md5 <md5>
     sign_off_statement: <문장 전문>
   holidays_FED v1.0.0 md5 <md5>
     sign_off_statement: <문장 전문>
   holidays_SIFMA v1.0.0 md5 <md5>
     sign_off_statement: <문장 전문>
   kr_sessions v1.0.0 md5 <md5>
     sign_off_statement: <문장 전문>
   ```
5. 커밋 직후 5절의 거버넌스 명령을 한 번 실행한다.

### 3.8 Linux에서 같은 작업

```bash
cd /path/to/quantgen
python3 -B -c "from datetime import datetime, timezone; n=datetime.now(timezone.utc); print(n.strftime('%Y-%m-%dT%H:%M:%SZ'), 'BEFORE deadline' if n < datetime(2026,10,31,15,tzinfo=timezone.utc) else 'AFTER deadline: stop')"
grep -c '^ *signed_utc: null$' core/calendars/data/MANIFEST.yaml          # 17
python3 -B -m tests.macro_m1_calendars                                    # 22/27 passed, 0 failed, 5 not run

# 단계 1 (파일마다)
f=core/calendars/data/holidays_KRX.yaml
sed -i "s/^  signed_off_by: null$/  signed_off_by: '<성명>'/" "$f"        # 행만 (들여쓰기 2칸)
grep -c '^  signed_off_by: null$' "$f"; grep -c '^  source_url: null$' "$f"; grep -c 'UNVERIFIED' "$f"

# 단계 2: signed_utc 값
python3 -B -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"

# 단계 3과 단계 6
python3 -B -m core.calendars.store | grep -E -A1 '^(signed|REFUSED) +(holidays_(KRX|NYSE|FED|SIFMA)|kr_sessions)\.yaml'
python3 -B -m core.calendars.store | grep -c '^REFUSED '                  # 서명 뒤 11

# 단계 7
git add core/calendars/data/{holidays_KRX,holidays_NYSE,holidays_FED,holidays_SIFMA,kr_sessions,MANIFEST}.yaml
git diff --cached --stat                                                  # 6 files changed
git commit -F /tmp/calendar_signoff_msg.txt
```

### 3.9 store가 거부할 때 (`store.py`의 메시지)

| 사유 줄(앞부분) | 원인 | 고칠 것 |
|---|---|---|
| `signed_off_by is empty` | 파일 수준 서명자가 비었다 | 3.2 |
| `signed_utc is empty` / `signed_utc '…' is not an ISO-8601 UTC instant (YYYY-MM-DDTHH:MM:SSZ)` | 형식 오류 | `'2026-10-3xTHH:MM:SSZ'` 형식, 따옴표 |
| `unquoted date/time scalar; quote every date and time string` | 따옴표 없는 날짜나 시각 | 따옴표를 넣는다 |
| `line N: unquoted time '12:00' …` | 따옴표 없는 HH:MM | `'12:00'` |
| `md5 '<x>' != content md5 <y>` | md5를 읽은 뒤 내용을 고쳤다 | 3단계부터 다시 |
| `MANIFEST.yaml row (version …, md5 …) does not match the file` | MANIFEST 행이 다르다 | 3.5 |
| `MANIFEST.yaml signer does not match the file signer` | 서명자 문자열이 다르다 | 같게 쓴다 |
| `MANIFEST.yaml signed_utc '…' != file '…'` | signed_utc가 다르다 | 같게 쓴다 |
| `sign_off_statement is empty` | 문장이 없다 | 3.2 |
| `MANIFEST.yaml row names no test id` | test_ids가 비었다 | 3.5 |
| `rows[i] is unsigned` / `rows[i] lacks [...]` | 행의 서명자가 비었거나 필수 키가 없다 | 3.1 |

- YAML 문법 오류는 store가 Traceback으로 멈춘다. 대개 문자열 안의 작은따옴표 때문이다. 오류 메시지의 줄 번호를 보고 `''`로 고친다.

---

## 4. 증명 명령과 서명 뒤 기대값

모두 저장소 루트에서 실행한다. Windows는 `python`, Linux는 `python3`다. `tests/run_all.py`는 쓰지 않는다(감사 10.4(마)).

### 4.1 모듈별 명령

| 명령 | 서명 전(PT-07 적용, 마감 전) | 서명 뒤 기대값(리허설) |
|---|---|---|
| `python -B -m core.calendars.store` | 16개 모두 REFUSED | 5개 `signed`, 11개 `REFUSED` |
| `python -B -m tests.macro_m1_calendars` (약 30초) | `22/27 passed, 0 failed, 5 not run` | `24/27 passed, 0 failed, 3 not run` |
| `python -B -m tests.macro_m1_integration` | `7/7 passed, 0 failed, 0 not run` | `7/7 passed, 0 failed, 0 not run` |
| `python -B -m tests.macro_m9_lab` (느림) | `11/15 passed, 0 failed, 4 not run` | `11/15 passed, 0 failed, 4 not run` |
| `python -B -m tests.macro_m1_pit` | `24/31 passed, 0 failed, 7 not run` | `24/31 passed, 0 failed, 7 not run` |
| engine_acceptance 68–75(아래 명령) | 8 PASS | `8 PASS: [...]` |

**macro_m9_lab 실행 시간**
- 클라우드에서는 부하(load 13, 4코어) 때문에 1200초 제한을 넘었다.
- 3600초 제한으로 다시 돌려 통과했다. 개별 테스트 시간의 합은 약 614초다.

**engine_acceptance 68–75**
- 이 모듈에는 `__main__`이 없다. 그래서 프로세스 안에서 돌린다.
  ```powershell
  python -B -c "import tests.engine_acceptance as M; ok=[n for n, f in M.tests() if n[5:7] in {'68','69','70','71','72','73','74','75'} and f() is None]; print(len(ok), 'PASS:', ok)"
  ```
- 하나라도 실패하면 Traceback이 그 테스트를 가리킨다.
- 리허설 1 사본에서 `8 PASS`였다: test_68_korean_holidays_are_covered부터 test_75_holiday_check_is_a_constant_time_lookup까지.

### 4.2 macro_m1_calendars에서 볼 것

**서명 뒤 반드시 PASS인 새 테스트 4개**(감사 10.4(마)). 리허설 1과 2에서 모두 PASS였다.
- `test_cal01_shipped_files_signed_or_refused`
- `test_cal02_2027_files_signed_before_2026_11_01`: 서명 전에는 NOT_RUN이고, 서명하면 PASS로 바뀐다.
- `test_cal02_known_2026_2027_rows_present`
- `test_close02_on_the_real_signed_files`: 서명 전에는 NOT_RUN이고, 서명하면 PASS로 바뀐다.

**계속 PASS여야 하는 기존 3개**
- `test_cal01_unsigned_refused_signed_accepted`
- `test_cal01_calendar_change_governance_event`
- `test_cal02_coverage_warn_page_halt`

**서명 전후 모두 PASS인 PT-07 회귀 테스트**
- `test_cal01_manifest_pins_signed_utc_and_statement`
- `test_cal01_same_day_schedule_needs_its_signed_calendar`
- `test_cal01_signed_utc_must_be_iso_utc`
- `test_cal01_unquoted_time_refused_at_load`
- `test_cal02_deadline_clock_injected`

**서명 뒤에도 NOT_RUN으로 남는 3개**(서명과 무관)
- `test_print01_real_kospi_close_2026_03_09`: REFDATA. `krx_kospi_official_close_1997-01-03_2026-10-02.csv`가 `tests/fixtures/macro/MANIFEST.csv`에 없다.
- `test_sat01_real_kospi_completeness_and_variance_ratio`: 같은 REFDATA 사유다.
- `test_regime01_full_range_expected_values_file`: OWNER. `tests/fixtures/macro/kr_regime_tags_expected.csv`는 소유자가 만들 자료다. `kr_regime_tags`는 미서명이다.
- 소유자 PC에 위 REFDATA가 등록돼 있으면 개수가 달라질 수 있다.

**다른 모듈에서 NOT_RUN으로 남는 것**
- macro_m1_pit 7개. 그중 `test_avail_01_official_calendars_are_owner_signed`는 과거 구간(2015, 2025)의 서명 파일이 필요하다(CAL-11). 이번 서명 범위 밖이다.
- macro_m9_lab 4개:
  - REFDATA 2개: `test_i11_kospi_oos_2016_26_thresholds_refdata`, `test_i11_replay_kospi_path_refdata`.
  - OWNER 2개: `test_t_crypto_01_asof_join_with_staleness_labels_owner`(crypto sleeve, R-17), `test_t_fx_01_granularity_floor_needs_the_contract_multiplier_owner`(FX 선물 계약 승수).
- M-2의 두 테스트는 서명 전후 모두 PASS다: `test_unsigned_shipped_calendars_fail_acting_inputs_closed`, `test_t_crypto_01_clock_annualisation_and_no_crypto_sleeve`.

### 4.3 핵심 값 확인 (한 줄 명령)

```powershell
python -B -c "from datetime import date; from core.calendars import store, clocks, publication; c=store.CalendarSet(); print('sessions_left', {f: store.sessions_left(c, c.file(f), date(2026,11,1)) for f in ('holidays_KRX','holidays_NYSE','holidays_FED','holidays_SIFMA')}); print('fed_business_day 2027-12-31', publication.fed_business_day(date(2027,12,31), cal=c)); print('US is_session 2027-12-31', clocks.is_session('US', date(2027,12,31), cal=c)); print('sifma 2026-04-03', publication.sifma_status(date(2026,4,3), cal=c)); print('KR decision 2027-11-18', clocks.decision_time_utc('KR', date(2027,11,18), cal=c)); print('arm 2026-11-02', {m: store.arm_precondition(date(2026,11,2), m, cal=c) for m in ('KR','US')}); print('status signed', {m: store.status(m, date(2026,11,2), cal=c)['signed'] for m in ('KR','US')})"
```

리허설 결과:
```
sessions_left {'holidays_KRX': 287, 'holidays_NYSE': 293, 'holidays_FED': 290, 'holidays_SIFMA': 290}
fed_business_day 2027-12-31 False
US is_session 2027-12-31 True
sifma 2026-04-03 early_close
KR decision 2027-11-18 2027-11-18 07:30:00+00:00
arm 2026-11-02 {'KR': True, 'US': True}
status signed {'KR': False, 'US': False}
```
- **sessions_left**: SIFMA 2027년 행을 지우거나 휴장을 조기폐장으로 바꾸면 값이 1씩 늘어난다(290 → 291). 조기폐장 행을 더하는 것은 세션 수를 바꾸지 않는다.
- **fed_business_day 2027-12-31 = False**: 같은 서명 파일에서 2027-12-31 행을 빼면 True가 된다(리허설 확인). NYSE는 이날 개장한다(True).
- **status signed = False**: 의도한 결과다. `status()`는 미서명인 `kr_regime_tags`, `publication_schedules`, `source_skipped`도 본다. 반면 ARM은 `MARKET_FILES`만 보므로 True다.

### 4.4 34개 모듈 비교 (클라우드 사본)

- 비교한 사본 3개: HEAD(049306c), PT-07 적용(미서명), 리허설(5개 서명).
- 합계(PASS/FAIL/NOT_RUN): HEAD 545/5/110, 적용 551/5/110, 리허설 553/5/108.
- **PASS→FAIL은 0건**이다.
- macro_m1_calendars는 16/0/5 → 22/0/5 → 24/0/3으로 바뀌었다.
- 나머지 33개 모듈은 세 사본에서 결과가 같다.
- FAIL 5건은 세 사본에서 같다. 사본 환경 때문이며 이 변경과는 관계없다.
  - engine_acceptance test_81, 82, 89: hermetic 래퍼 안에서 네트워크 접점을 부른다.
  - macro_acceptance test_t_herm_02: 스냅샷이 없다.
  - macro_m8_pipeline `test_dry_run_end_to_end_on_the_local_cache`: 사본에서 캐시 4개를 지웠다.
  - 소유자 PC의 전체 스위트(감사 13.2 1)의 4))에서 다시 본다. NOT_RUN은 PASS로 세지 않는다.

---

## 5. 거버넌스 기록 (감사 10.4(바))

서명 직후 저장소 루트에서 **한 번** 실행한다. 운영 경로가 `record_calendar_changes`를 부르지 않기 때문이다(CAL-07).

```powershell
python -B -c "from datetime import datetime, timezone; import config; from core.calendars import store; print(store.record_calendar_changes(config.macro_dir() / 'governance_events.jsonl', ['holidays_KRX', 'holidays_NYSE', 'holidays_FED', 'holidays_SIFMA', 'kr_sessions'], lambda: datetime.now(timezone.utc)))"
```
Linux는 같은 명령을 `python3 -B -c "..."`로 실행한다.

**기대값**(리허설 1 사본의 복사본에서 확인)
- 32자리 hex 5개가 든 리스트가 나온다. 기록한 이벤트 줄의 md5다.
- 다시 실행하면 `[]`가 나온다. 같은 version과 md5는 건너뛴다.
- 미서명 파일은 기록하지 않는다.

**기록 위치**
- 경로는 `config.macro_dir()`이다. 기본값은 `~/.nextgen/macro`이고 `QUANTGEN_MACRO_DIR`로 바꿀 수 있다.
- 운영 경로의 로그(`core/skills/macro_daily.py`의 `governance_events.jsonl`)와 같은 파일이다.

**이벤트 내용**(파일마다 1건)
- `kind`: `calendar_change`
- `key`: 파일 id
- `rule_id`: `R-20`
- `new`: `{version: 1.0.0, md5, signed_off_by, signed_utc}`
- `actor`: `owner`
- `reason`: `<파일> loaded at version 1.0.0 signed by <성명>`
- `refs`: `['R-20 rule 6', 'T-CAL-01']`
- reason은 코드가 정한다. 함수에 reason 인자는 없다.
- 서명 문장은 파일의 `sign_off_statement`와 커밋 메시지에 남는다.

**확인**
```powershell
Get-Content (python -B -c "import config; print(config.macro_dir() / 'governance_events.jsonl')") -Tail 5
```
Linux: `tail -n 5 "$(python3 -B -c "import config; print(config.macro_dir() / 'governance_events.jsonl')")"`

---

## 6. 서명하지 않는 것과 그 이유

### 6.1 행을 대조할 때까지 미서명으로 두는 3개 (감사 12.1, 10.4(가))

서명은 "대조했다"는 증언이다. 대조하지 않은 행에는 서명하지 않는다.

| 파일 | 이유 | 미서명일 때 동작 |
|---|---|---|
| `kr_regime_tags` | 58행이다. 2026년 행 대부분이 미검증이다. 기대값 파일 `tests/fixtures/macro/kr_regime_tags_expected.csv`(소유자 자료)가 없다. 2027 커버도 필요하다 | `regime_tags`가 `CalendarUnsigned`. `status('KR').signed`는 False |
| `publication_schedules` | 16행이다. BLS·BEA 발표 일정과 M1 측정 2건(FRED VIX 게시 지연, KODEX 200 바스켓 시각)이 필요하다 | `publication_instant`가 `CalendarUnsigned`(fail-closed). `status` KR·US의 signed는 False. CAL-12 수정으로 `same_day` 규칙도 발행처 달력의 서명을 요구한다 |
| `source_skipped` | 19행이고 마지막 행은 2025-04-18이다. CAL-09 수정을 기다린다: Good Friday 행을 `series: DGS10`에서 H.15 채널 전체로 바꾸고, SIFMA 2027 확인 뒤 2027-03-26 행을 더한다 | 그 파일을 읽는 입력은 fail-closed |

- 이 셋이 미서명이면 KR과 US의 `status().signed`는 False로 남는다.
- 그래도 ARM은 된다(4.3절).
- 틀린 값을 내는 것보다 거부하는 편이 낫다(감사 10.4(가)).

### 6.2 행이 없거나 대조 전인 나머지 8개
- **빈 7개 세트**(CAL-06): `holidays_CBOE`, `holidays_CME`, `holidays_ECOS`, `holidays_HKEX`, `holidays_JPX`, `holidays_SSE`, `holidays_TWSE`.
  - 행이 0개라 서명할 수 없다.
  - JP, CN, HK, TW는 ARM할 수 없다.
  - 이 세트를 쓰는 시리즈는 context, risk_model, forward_sim 같은 비행동 바인딩이다. 그래서 라벨이 붙은 값으로 나온다.
  - KR·US ARM에는 영향이 없다.
  - 처리 방향(감사 12.2, PT-17): 공식 공지로 행을 만들고 서명한다. CME는 세트에서 뺀다. `COVERAGE_FILES`에 ECOS(KR)와 CBOE(US)를 더한다. SSE 2027은 국무원 공지 뒤에 만든다.
- **`market_closes`**: 3행이다. SSE, HKEX, TWSE 종가 시각이 미검증이다(CAL-13). CN, HK, TW만 쓴다.
- 이 11개 파일의 `how_to_sign`은 옛 절차 그대로다. 서명하기 전에 새 store 검사(`sign_off_statement`, MANIFEST `signed_utc`, ISO UTC)에 맞게 고친다.

### 6.3 서명 뒤에도 남는 일과 주의
1. **재서명과 마감 테스트가 충돌한다.**
   - KRX 2027 공지(12월 예상)나 SIFMA·K.8 변경 때문에 v1.0.1로 재서명하면 `signed_utc`가 마감 뒤가 된다.
   - 그러면 `test_cal02_2027_files_signed_before_2026_11_01`이 `not before the deadline`으로 FAIL한다.
   - 이 테스트는 지금 파일의 `signed_utc`만 본다.
   - 재서명 전에 이 테스트를 "최초 서명 시각" 기준(거버넌스 `calendar_change` 기록 등)으로 바꿀지 소유자가 정해야 한다.
2. **PT-08(M-1)은 들어가지 않았다.**
   - 엔진 `sessions_around`가 130일 창을 요구한다. 그래서 2027-08-24부터 hard stop이 ValueError로 끝난다.
   - PT-08이 없으면 2028 파일을 **2027-08-23까지** 서명해야 한다.
3. **PT-17이 남았다.**
   - CAL-07: 커버리지 경보(warn 60, page 20)가 운영에 연결되지 않았다.
   - CAL-11: 과거 커버가 짧다. KR 2025-11-13, US 2024-12-31에서 `CalendarCoverageError`가 난다.
   - M-3: 레거시 `data/calendars/{NSE,SGX,SSE,SZSE}.json`이 2026-12-31에 끝난다. 2027-01-01부터 engine_acceptance test_73이 FAIL이다.
   - D12-07, D12-15.
4. **레거시 `data/calendars/KRX.json`**
   - PT-07이 휴장 4일과 수능일 특수 세션 2개(10:00–16:30)를 더했다.
   - 서명 대상은 아니다(md5 없음).
   - 기존 특수 세션은 손대지 않았다. 2026-01-02 10:00 개장은 확인 실패(지난 날짜)이고, 2027-01-04 개장은 공식 공지 전이다.
5. **해마다 하는 일**: 두 단계로 한다(감사 12.2). 6월 월력요항으로 다음 해 행을 먼저 서명하고, 12월 KRX 공지로 다시 확인한다.

---

## 7. 최종 점검표

**준비 (3.0)**
- [ ] UTC 시각이 2026-10-31T15:00:00Z보다 앞선다(`BEFORE deadline`).
- [ ] PT-07이 적용돼 있다: MANIFEST `signed_utc: null` 17개, KRX에 2026-06-03 행, `tests.macro_m1_calendars` 22/0/5.

**출처 대조 (2절)**
- [ ] KRX 33행을 대조했다. 2026-06-03의 KRX 공지 원문을 찾아봤다. 2026-07-17의 시행일을 law.go.kr 부칙으로 확인했다. 2027년 15행의 근거를 문장에 적었다.
- [ ] NYSE 37행을 대조했다. 2025-01-09 행의 틀린 `unverified`를 고쳤다. 2027-12-31에 행이 없다.
- [ ] FED: 2026–2027년 23행을 현재 k8.htm과 대조했다. 2015–2025년 115행을 공식 표와 대조했다. 후보일(행정명령·애도일·취임일)의 Board 휴무 여부를 판단했다.
- [ ] SIFMA: 2027년 13행을 holiday schedule 원문과 대조했다(특히 2027-06-18, 2027-03-26). 넣지 않은 2027년 조기폐장 4건 가운데 일정표에 있는 것은 넣었다. 2026-04-02는 넣지 않았다.
- [ ] kr_sessions 23행을 대조했다. newsId=156692078이 맞는 보도자료인지 확인했다. 2017-11-16을 확인했다.

**필드 작성 (3.1–3.6)**
- [ ] 모든 행에 `source_url`, `retrieved_at_utc`(소유자가 연 시각, 따옴표), `signed_off_by`를 썼다. 행 `signed_off_by: null` 0개, `source_url: null` 0개.
- [ ] 파일 수준: `version: 1.0.0`, `status: SIGNED`(두 줄 모두 교체), `signed_off_by`, `signed_utc`(따옴표, 마감 전), 서명 문장(`<성명>`과 `<YYYY-MM-DD>`를 채움, md5 없음), `md5: null`.
- [ ] 3단계 사유 줄이 `md5 None != content md5 …`일 때 그 md5를 읽었다. 그 뒤로 내용을 고치지 않았다.
- [ ] 파일 `md5: '<값>'`과 MANIFEST 다섯 행(version, md5, signed_off_by, signed_utc, test_ids + T-CAL-01, T-CAL-02), MANIFEST 최상위를 썼다.
- [ ] store: 5 signed, 11 REFUSED.

**증명과 기록 (4–5)**
- [ ] `tests.macro_m1_calendars` 24/0/3. 새 증명 테스트 4개 PASS, 기존 3개 PASS.
- [ ] `tests.macro_m1_integration` 7/0/0. `tests.macro_m9_lab` 11/0/4. `tests.macro_m1_pit` 24/0/7. engine_acceptance 68–75 8 PASS.
- [ ] 4.3절 값이 리허설과 같다. SIFMA 행을 바꿨다면 sessions_left 차이를 설명할 수 있다.
- [ ] 6개 파일을 커밋했다. 메시지에 파일별 md5, signed_utc, 서명 문장이 있다.
- [ ] 거버넌스 명령을 한 번 실행했다. 5건이 기록됐고, 다시 실행하면 `[]`다.

**서명하지 않은 것 (6)**
- [ ] `kr_regime_tags`, `publication_schedules`, `source_skipped`, `market_closes`와 빈 7개 세트는 미서명으로 남겼다. KR·US `status().signed`가 False인 것은 의도한 결과다.
- [ ] 재서명(v1.0.1) 전에 마감 테스트를 어떻게 다룰지 정했다(6.3의 1).
- [ ] 2028 파일 마감(PT-08이 없으면 2027-08-23)을 일정에 넣었다.
