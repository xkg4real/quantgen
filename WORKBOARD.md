# QUANTGEN WORKBOARD — 전체 업무 구조도와 체크리스트

## 최신 중앙 Codex 배정 — 2026-11-21T12:10:34+09:00

소유자 단일요청창구·5담당계획 승인후메인Codex가총괄한다. [실제담당·진행·검증근거표](CENTRAL_CODEX_STATUS_2026-11-21.md)를 우선한다. DIDM/UI기존세션은handoff/새구현중지확인완료. 데이터는최신GPT DSH7ce37917/DIDM87812679를이어받는다. 구현·회귀는병렬, 병합은OS-F2→DS-H→DS/DIDM→KEY5a순차. 아래과거시각의중단·대기·배정문구는이력이며자동완료로바꾸지않는다. 현재새완료ID/병합은없다.


상시 지침: `SESSION_PIPELINE.md` (메인·하부 세션 연결 규칙). 이 문서는 메인이 작업 하나가 끝날 때마다 고친다.

기준 시각: 2026-11-20 05:40 KST (2.1·2.2·세션 지도 갱신) / 첫판 2026-11-20 00:45 KST (첫판: 메인 세션 조사 workflow wf_0be17a88-d74 + 완결성 검토, 그 뒤 메인이 KEY-4·OA-01 갱신)
git 기준: main 9f76b07 · PR #133 head 148504a · UI 브랜치 490562d · OS 브랜치 8262d6c · DS 브랜치 df05b21
자료: REMAINING_WORK_2026-11-17.md(공식 ID 출처, 10-27판의 열린 ID도 그대로 유효), REMAINING_WORK_2026-10-27.md, LEDGER.md(KEY-3까지 280줄), CURRENT.md, MERGE_QUEUE.md, 하부 세션 CURRENT 문서 5개, 하부 세션 대화 기록, Notion "REMAINING WORK"(11-19 15:10), GitHub REST. 참고만: REMAINING_WORK_2026-10-29.md(GPT PR #12 브랜치에만, main 미병합)
원칙: 자료끼리 다르면 git(원장·병합 대기열·PR 상태)을 따른다. 다른 점은 별도 "충돌" 목록에 있다.

---

## 0) 읽는 법

| 기호 | 뜻 |
|---|---|
| [x] | 완료 (원장 행 또는 main 병합 커밋 있음. 웹사이트는 다른 저장소라 handoff 기록 커밋으로 대신) |
| [~] | 진행 중, 또는 끝났다는 근거(원장 행·병합 커밋)가 아직 없음 |
| [ ] | 대기 (앞 작업이나 차례를 기다림) |
| [!] | 막힘. 소유자 손이 필요함 |
| [-] | 보류 또는 쓰지 않음 |

**세션 지도**

| 세션 | 종류 | 연락 방법 | 지금 |
|---|---|---|---|
| MAIN | 메인(조정·병합) | — | 11-20 05:50 KST: **주간 98% → GPT 인계**(CURRENT.md). PR #134 병합(f065ec9), 4e OS-F2 OS가 e44c48e까지, KEY-5/a 검토 결과 plans/2026-11-20/KEY5A_REVIEW.md |
| PAYMENTS_ACCOUNT_KEYS | 하부 (D6) | 메인이 직접 | KEY-4/a 병합(f065ec9), KEY-5/a dc936d4 메인 검토 대기(push 보류), PAY-2 재검증 0a24f02 끝 → OA-39 대기 |
| OS_EXPANSION | 하부 (D6) | 메인이 직접 | 18:42부터 쉼 (문서상 waiting_on owner, 실제로는 UI가 490562d로 패치를 이미 반영함 → 메인이 알려야 함) |
| DATA_SOURCE_DIDM | 하부 (D6) | 메인이 직접 | 15:00부터 쉼, 소유자 PC 실행을 기다림. KEY-3 병합 소식 아직 못 받음 |
| UI/UX | 별도 세션 | 소유자를 거쳐서만 (MERGE_QUEUE 규칙) | 소유자 실행 확인을 기다림 |
| WEBSITE/AWS | 별도 세션 | 소유자를 거쳐서만 (MERGE_QUEUE 규칙) | 11-13 이후 멈춤 |

**규칙 요약**
- PR은 한 번에 하나만 병합을 기다린다. 병합 버튼은 메인이 누른다. 하부 세션은 자기 행이 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 연다.
- 공유 파일(source-review.json, FACTS.md, config.py, workflows)은 PR 하나씩만 바꾼다. 앞 PR이 병합되면 최신 main을 합치고 기준선을 다시 만든다.
- UI/UX·웹사이트 세션의 브랜치와 인계 파일은 아무도 고치지 않는다. 다른 세션이 그 브랜치를 시험할 때는 읽기·시험만 하고 push하지 않는다. 그 세션에 줄 요청은 소유자를 거친다.
- 원장에 있는 ID는 끝난 것이다. 다시 하지 않는다. 추가 작업은 `/2`, 부분 작업은 `/a`를 붙인다.
- 하부 세션은 LEDGER를 직접 쓰지 않고 `--done` 문자열을 자기 인계 파일에 적어 메인에 알린다 (REMAINING_WORK_2026-11-17 0절).
- 하나가 끝나면: 작업 브랜치 push → 메인이 ledger `--done` → CURRENT next_ids에서 빼고 done_ids로 → 이 문서에 [x] → MERGE_QUEUE 줄 긋기 → Notion.
- 주간 사용량 98%면 handoff (CLAUDE.md). 다음 리셋 2026-11-24 17:00 KST.
- 11-13 소유자 방침(자동 감시·자동 인수 취소)과 11-19 요청이 다르다: 메인→하부 3세션의 자동 배정은 11-19 요청을 따르고, UI·웹사이트는 계속 소유자 경유.
- 소유자가 24시간 안에 손으로 할 일이 5개 이상이면 Claude 앱 푸시 알림을 보낸다. **지금 10개라서 알림 대상이다** (3절).

---

## 1) 지금 진행 중

**11-20 00:50 KST 메인 배정:** OS — UI 브랜치에서 종료 고침 재확인(읽기·시험만) + OS-F2 브랜치 시작 / DATA — main 9f76b07 합치기·시험·인계 문서 갱신(PR 직전 상태로 준비) / PAYMENTS — KEY-4 push 보류, PAY-0 초안 병행

형식: ID — 무엇 — 담당 세션 — 다음 행동 — 근거

- [x] **KEY-4** — PR #133 → main `8445187` (11-20 03:27 KST), 원장 KEY-4 (handoff 4aa4d10). 후속: 4d 메인 문서 PR, 4d' KEY-4/a, 4e OS-F2, 4f KEY-5/a
- [~] **소유자 AWS 운영 풀** — Golden Hour Code 계정의 시드니 사용자 풀 — PAYMENTS가 안내, 소유자가 실행 — MFA 결정(1/2/3) → 15단계 계정 복구 → 16·17단계 앱 클라이언트 quantgen-web, Client ID → T1 시험 — 세션 기록 22:04–23:52 KST. 13·14단계 끝
- [~] **PySide6 간헐 종료 고침** (OS-F1 선행, ID 없음) — 시험 도우미가 QThread.currentThread() 객체를 붙잡고 있던 문제를 threading.get_ident()로 바꿈 — OS(재확인), UI(반영 끝) — 메인이 OS에 "UI가 490562d로 반영함"을 전달 → OS가 UI 브랜치를 읽기·시험만(push 금지)으로 다시 시험 → PYSIDE6_TRIAL 9절 판정 복구 → OS 브랜치 8262d6c(5파일: lint 15, 점검표 15, TRIAL 10-1, 패치)의 main 자리를 메인이 정함(OS-F1 PR에 묶거나 작은 PR) — OS 8262d6c, UI 브랜치 head 490562d(23:24 KST)
- [!] **UI 7쪽 + PySide6 준비 병합** (MERGE_QUEUE 5) — claude/friendly-bardeen-r6xe8f — UI(소유자 경유) — 소유자가 PC 2대(skymi, whydi)에서 실행 확인 → UI 세션에 "PR 만들어" → 메인이 '병합: UI' — MERGE_QUEUE 5행. OS-F1과 KEY-5가 이것을 기다림
- [!] **DS·DIDM 브랜치** (DS-1, DIDM-0, DIDM-1, DS-4a, DS-4b, DS-4d, DS-4e) — 코드 끝, **main 9f76b07 합침 완료(f60e314) → head eb4f3a5, PR 직전 상태** (DIDM 시험 98 OK, 게이트웨이·자격증명 208 OK = main과 같음, core/ 밖 변경 0줄; 메인 확인 11-20 00:25) — DATA_SOURCE_DIDM — 남은 것: 소유자 PC 결과(OA-07, OA-08) 반영 → 8행 차례에 최신 main 합치기·기준선·PR — DATA 보고 11-20 00:23
- [!] **웹사이트 정책 문구 다시 만들기** — PR-130.json 반영 — WEBSITE(소유자 경유) — 소유자가 받은 프롬프트를 웹사이트 세션에 붙이기 — CURRENT "웹사이트 세션 전달은 소유자 경유"
- [ ] **OS-F2** — config.py·data/krx/kis_client.py·data/krx/opendart_client.py의 ~/.nextgen 경로 전환 — OS(브랜치), MAIN(자리) — 관문 KEY-2(3249af7) 풀림. KEY-4와 파일 겹침 없음(KEY-4는 config.py·data/krx를 바꾸지 않음) → OS 브랜치 작업은 지금 시작 가능. 메인은 MERGE_QUEUE에 행 추가, owner_confirmed 다시 쓰기는 그 뒤로 — MERGE_QUEUE에 행 없음

---

## 2) 트랙별 체크리스트

### 2.1 MAIN (조정·병합·결정 기록)

**관문**
- [x] F 동결 — 2026-11-19 01:32 해제, main 6e077dc (소유자 F22 완료 보고)
- [x] D7-G — 소유자 승인 2026-11-18 14:15 ("D7-G의 방식대로"), ⑦-1/rulings/2 002a658
- [~] 병합 차례 — PR 하나씩, 메인이 병합. 4d' KEY-4/a 병합(f065ec9). **지금 4e OS-F2 (병합: OS, 05:40)** → 4f DS-H → 4g DS·DIDM → 4h KEY-5/a
- [~] F21 뒤 목록 — GH-1, KEY-2, KEY-3 끝. KEY-4, OS-F1, KEY-5, DS·DIDM 남음
- [!] G1 법인 설립 — 소유자. D-U-N-S, Apple 조직, Windows OV, PAY-4의 관문
- [!] G2 유사투자자문업 — 소유자(변호사와)
- [!] G3 PG 심사 — G1 뒤
- [!] L 변호사 의견서 — 규제, Polymarket·Kalshi, LGPL, 웹 거래
- [!] 표시권 — 공급처별 표시·재배포 권리

**F21 뒤 병합 (1–4b 끝)**
- [x] ⑦-2/a — PR #126, 56fe32a
- [x] OS 작은 PR (OS-P0-a~f) — PR #127, c28b1d7
- [x] KEY-2 — PR #128, 3249af7 / KEY-2/b — PR #129, ca5da08
- [x] 정책 PR-1 (원장 PAY-A2/a) — PR #130, edbe9f7
- [x] GH-1 — PR #131, ab24dec. 공개 유지, runtime-smoke 겹친 실행 취소
  - 빠진 범위: Compliance 결과물 보관 30→7일(compliance-review.yml 73·92행 아직 30), export.py 링크 안내. 필요하면 GH-1/2로 새로 잡기
- [x] KEY-3/design, KEY-3 — PR #132, 9f76b07
- [x] KEY-4 — PR #133 → main 8445187, 원장 KEY-4 (handoff 4aa4d10)
- [ ] GH-2 — test_npu.py, mindmap/, .claude/launch.json 'godseye-dev'(12행) 삭제. archive-2026-11 태그(아직 없음) 뒤 _backup/ 삭제. 비밀 검사 CI를 넣을지는 소유자 결정. 로드맵은 "GH-1과 한 PR"이었으나 GH-1은 따로 닫힘
- [ ] 정책 문서 PR-2 — 계정 서비스 설명(시드니 저장, 탈퇴, 보안 기록, 처리 위탁). AWS 풀과 웹 계정 화면이 생긴 뒤
- [ ] 2.7 웹 거래 결정 메모 (D12-A) → M-12 — ⑦-2 뒤 관문 풀림. 변호사·KIS 문의는 소유자
- [ ] 2.7 push_handoff.py --doc — 하부 세션 문서 게시용 (main 9f76b07에 아직 없음)

**결정 기록**
- [x] 2.7 결정 기록 PR — ⑦-1/rulings(7c33955), ⑦-1/rulings/2(002a658). 11-19분은 56fe32a, edbe9f7, ab24dec에 포함
- [x] 2.7 P3·F 뒤 main PR — ⑦-2, ⑦-2/a
- [~] 2.7 회원가입 정책 문서 PR — PR-1 끝, PR-2 남음
- [x] 기록 — PR #135 → main fa78df1: 세션 연결 지시, 계정 결정 3건, OA-42·OA-44, 메인 결정 2건 (원장 SESSION-PIPELINE). 남은 기록: D9 답, OA-38, OA-46

**메인 문서 손볼 것**
- [x] MERGE_QUEUE — 4c head·상태, 7행 KEY-5만, 윗표 줄 긋기, "비공개 뒤 CI 유료" 규칙 정정, 4d·OS-F2·OS 종료 원인 기록·정책 PR-2 행 — 11-20 메인 (WORKBOARD 첫판과 같은 handoff 커밋)
- [ ] CURRENT.md — next_ids에 진행 중 ID 넣기(KEY-4, KEY-5, OS-F1, OS-F2, GH-2, PAY-0, PAY-2, DS-1 등, 원장 ID는 빼고). 낡은 "PR121 상태" 줄 정리
- [ ] "역방향 의존 없음" 정정 확인 — MASTER_WORK_DESIGN에는 그 문장이 없음(검색 0건). Notion 플랫폼 계획 7.2 M2 문장은 OS가 11-18 개정 2판에서 고쳤다고 기록(OS_SESSION_CURRENT) → 메인이 확인하고 닫기
- [ ] D14_RAVENPACK_ALTERNATIVES.md 1절 "3단계" 고치기 (= 대안 9개. DIDM 3단계 아님) — 4d 메인 문서 PR에 넣음. DS-3 관문은 확인 끝(2.4절)
- [ ] OS-F3 판단 — KEY-2(3249af7)로 끝난 것으로 적을지, macOS·모바일 키체인 범위를 새로 잡을지
- [ ] OS-P0-d Notion 기록 맞추기 (원장은 "소유자 몫", OS는 "이미 반영")
- [ ] Notion REMAINING WORK 갱신 (충돌 목록 참고)
- [ ] 변호사 질문 묶음 — L, G2, ⑩-1/b, Polymarket·Kalshi, LGPL 5문항, D12, 15-12, 투자 자문 경계
- [ ] 오래 열린 GPT PR #12 (gpt/handoff-continuation-20261029) 처리 여부를 소유자에게 묻기. 이 브랜치의 REMAINING_WORK_2026-10-29가 ⑫-4, ⑬-3~⑬-7, ⑭-1~⑭-3을 정의하므로 공식 ID 출처로 쓸지도 함께 정함
- [ ] 원장에 없는 상위 ID 정리 — ④-2, ④-3, ⑤-2, ⑨-1, ⑨-4, ⑨-3a/recorder/1: 닫을지(원장 행) 남은 범위를 적을지

**상품·이월 (MAIN 담당)**
- [~] ⑩-1 규제·외부 공개 검토 — ⑩-1/a 끝 / [!] ⑩-1/b 전문가 의견
- [~] ⑩-2 동반 앱 MVP — ⑩-2/a 끝 / [ ] ⑩-2/b (Notion의 ⑩-2/b-private-offline-mvp는 근거 커밋 7e9e112가 어느 원격에도 없음)
- [x] 10-3 상업 README·현황 문서 — 51bac97 (main에 있음, 원장 행 없음)
- [~] ⑩-4 비교·상업화 보고서 — Notion은 지웠지만 본문은 "최종본 미완료". ⑩-4/a 초안은 Notion에서만 완료 (원장 행·커밋 없음)
- [~] ⑪-1 TRADEGEN 연계 요약 — ⑪-1/a 끝, 소유자 승인 남음
- [~] 11-2, 11-3 TRADEGEN PR #14, #15, #16 (다른 저장소)
- [~] M-12 주문 안전 설계 — M-12/design-draft/1 끝(eba94f0). D8, D10, 계좌 평가 정의 남음
- [ ] 14-1 ⑫–⑭ 후속 범위 확인
- [ ] ⑭-1 시나리오 스토리보드, ⑭-2 교육 템플릿(공개는 ⑩-1 뒤), ⑭-3 선택형 제품 분석 — 10-29판 ID(PR #12에만). 14-1에서 범위 확인
- [!] 12-7 감사 12절 상품 우선순위 승인 (소유자)

### 2.2 PAYMENTS (PAYMENTS_ACCOUNT_KEYS)

- [x] KEY-1 — docs/commercial/ENV_NAMES.md — 3249af7 (PR #128)
- [x] PAY-A1 — ADMIN_GUIDE.md — 3249af7. v0.2는 부록 C 결과 뒤
- [x] PAY-A2 — ACCOUNT_SETUP.md, OWNER_STEPS.md — 3249af7 (OWNER_STEPS는 PR #133에서 v1.3.2, 로컬 6a489aa에서 v1.4)
- [x] PAY-A2/a — 정책 PR-1 — edbe9f7 (PR #130)
- [x] KEY-2 — core/credentials (환경변수 → OS 키 보관함 → 개발 빌드만 .env) — 3249af7. code_sha256 ec72fab3→10c27010
- [x] KEY-2/b — KEY-2 검토 후속 — ca5da08 (PR #129)
- [x] KEY-3/design — GATEWAY_DESIGN.md v0.2 — 9f76b07
- [x] KEY-3 — core/gateway + 경계 시험 — 9f76b07 (PR #132)
- [x] KEY-4 — PR #133 → main 8445187, 원장 KEY-4
- [x] KEY-4/a — 계정 문서 고침(F1–F9) + OA-42·OA-44 반영 + 자체 시험 1줄 — PR #134 @ aa4be94 → **main f065ec9** (11-20 05:36 KST), CI 7개 녹색, 원장 KEY-4/a (handoff 40b9378)
- [~] KEY-5 — 화면 쪽 22파일/44곳 + quantgen_desktop/paper.py + 키·연결 화면(gateway.status()) — 구현은 UI 세션 몫(소유자 경유). **요청문 초안 끝: handoff `plans/2026-11-20/KEY5_UI_REQUEST.md` (0df90ec, PAYMENTS)** — KEY-4 병합 뒤 메인 확정 신호 → 줄 번호 재정렬 → 소유자가 UI 세션에 붙여 넣음. OS-F1 뒤 적용 권장. 앞서 정할 것: set_backend(None) 가/나 안(OA-41)
- [~] KEY-5/a — KEY-5 앞 gateway 준비 3건 (G1 data.kis_stream 입구, G2 kis_workspace 순수 값 목록, G3 main.py QuoteFeed 하위 클래스를 공용 모듈로 → paper.py 재사용) — PAYMENTS, KEY-4 병합 뒤 main에서 브랜치, 대기열 **4h**. **코드 끝: `claude/payments-key5a-20261120` @ `dc936d4`** (main 8445187에서, 10파일, + PR #133 3차 검토 C 항목 A1R3-1/4/5·F2/F5/F6/F7). 메인 확인 11-20 04:10: 동결 엔진 4개 바이트 같음, main.py CRLF, code_sha256 10c27010 그대로, 게이트웨이 시험 71 OK. 메인 검토 결과 handoff `plans/2026-11-20/KEY5A_REVIEW.md` (주요 M1·M2, 작은 것 S1–S7) → PAYMENTS/이어받는 쪽이 고침
- [~] PAY-0 — 문의 7건 초안 + 목록 표 (docs/commercial/inquiries/, 문서 8개) — **초안 끝: `claude/payments-pay0-20261120` @ `7f8939c`** (main 9f76b07에서, 메인 확인 11-20 01:00: 문서만, 비밀값·다른 연락처 없음). PR은 대기열 자리 뒤, 원장은 병합 때. 발송은 소유자(OA-32)
- [~] PAY-2 — 결제 설계(시나리오 A) — **초안 끝: `claude/payments-pay0-20261120` @ `d0da1b2`** (docs/commercial/payments/ 4개: PAYMENT_DESIGN, PG_COMPARISON, PRIVACY_POLICY_PROPOSAL, README; 메인 확인 11-20 01:05: 문서만). 소유자 결정 P2-01..P2-15(OA-39), 법률 확인 걸린 것 P2-05·06·08·09·10·11·12·14. 약관 02 제4조·03·01 반영은 정책 PR-2. PR은 PAY-0과 함께 대기열 자리 뒤 **재검증 11-20: `0a24f02`** (main fa78df1 합침 909a3fa 위, PAYMENT_DESIGN·PG_COMPARISON만): 정기결제 증액·유료 전환 동의 30일(2025-02-14 시행) 확인, 다크패턴 시행일 확인, 디지털콘텐츠 철회 제한 요건 해설로 확인(조문 원문 미확인), PG 수수료·정산 주기는 미검증 유지 → PAY-0 03 문의 회신으로 확정. 메인 확인 04:15: 문서 2개만, 비공개 정보 없음. 후속 `e869064`: 2026-12-17 전자금융거래법 개정 건은 PG 문의 질문 후보(미검증)로만.
- [!] PAY-1 — 데스크톱 로그인 core/account/** — 웹 계정 공개(AUTH_UI_ENABLED) 뒤
- [!] PAY-3 — 회사 데이터 서버 — 법인·계약 전에는 설계만. 위치는 소유자에게 묻기
- [!] PAY-4 — 카드 PG 연동 — G1, G3 뒤
- [ ] 15-11 앱 계정·구독 화면 — 사업자 등록, 통신판매 신고, PG 뒤
- [ ] 15-12 서버 기능 플래그 (requires_filing / filing_accepted) — 법무 확인 뒤
- [ ] 15-13 앱·웹 주문 기반 — M-12, 모의 거래 20거래일, 변호사 의견(D-14), KIS 답 뒤
- [~] 소유자 AWS 안내 (OWNER_STEPS 25단계) — 13·14단계 끝, MFA는 이메일 MFA 유지로 결정(OA-01 완료), 15–17단계 진행 중(OA-02)

### 2.3 OS (OS_EXPANSION)

- [x] OS-P0-a — tools/qt_port 변환 도구 — c28b1d7 (PR #127)
- [x] OS-P0-b — packaging/, 바인딩 중립 spec, platform-build.yml(수동·v* 태그만), stage.py --profile mobile — c28b1d7
- [x] OS-P0-c — core/app_paths.py, core/app_identity.py — c28b1d7 (Notion 15-3의 파일 만들기도 이것으로 끝)
- [x] OS-P0-d — 플랫폼 계획 2판 — c28b1d7
- [x] OS-P0-e — PySide6 정식 시범, UI 점검표 — c28b1d7
- [x] OS-P0-f — 글꼴 대안, 세그폴트 최소 재현 — c28b1d7
- [~] PySide6 간헐 종료 고침 — UI 브랜치 414eceb에서 OS 재시험 끝(PySide6 160×2회 abort 0, PyQt6 18단계 종료코드 5025c6f와 같음, 9절 판정 복구). 기록 5커밋은 OS-F2 PR(4e)에 묶음. 병합 때 원장 OS-F1/a
- [!] OS-F1 — PySide6 전환 날 (UI는 pyqt6_to_pyside6 --apply, OS는 switch_day.py --apply, 그날 quantgen_desktop/**와 tests/desktop_* 잠금) — MERGE_QUEUE 6행. UI 7쪽 병합, 고침 확인, 소유자 "OS go"가 필요
- [~] OS-F2 — ~/.nextgen 경로 → core.app_paths.user_data_dir — **브랜치 `claude/os-f2-data-dir-20261120` @ `f9a3a75`** (main 8445187 합침, abort 기록 5커밋 묶음, 14파일; 관련 33파일 실패 목록 main과 같음, 통과 855→868; 지문 bcaf33d9…). 대기열 4e, owner_confirmed는 이것 병합 뒤
- [ ] OS-F3 — 키 저장, KEY-2와 맞춤 — KEY-2로 덮였는지 메인이 판단
- [ ] OS-F4 — macOS 차이 — OS-F1, OS-F2 뒤
- [ ] OS-F5 — macOS CI (로드맵은 "범위 미기재", 플랫폼 계획 2판이 정함) — OS-F4 뒤
- [ ] OS-M2 — macOS .app (ad-hoc 서명) — OS-F4, OS-F5 뒤
- [ ] OS-M3 — "Mac 없이 macOS" 질문 시점. 클라우드 Mac 24시간 약 $21 승인
- [ ] OS-A1 — Android(Flet) 2일 시험 — OS-F2 뒤. 컨테이너에서 pypi.flet.dev, dl.google.com이 막힘(403)
- [ ] 15-7 판매 빌드 준비 (제외 목록, PySide6 LGPL 점검표)
- [ ] 15-3 남은 것 — app_identity와 QSettings·windows_branding.py 연결. OS 순서(04 8절 "app_identity 연결")에 있지만 quantgen_desktop/windows_branding.py는 UI 세션 파일 → 소유자 경유

### 2.4 DATA_SOURCE/DIDM

- [~] DS-1 — VENDOR_EVAL_2026-11.md (대안 9개 × 정보 19종). 소유자 답(8절) 반영. 브랜치에만 있음
- [~] DIDM-0 — PREREG_V0.md. 소유자 승인 11-18. 열린 질문 2개
- [~] DIDM-1 — SCORE_SCHEMA_V0.md, core/didm/llm/schema.py (14종, novelty_0_100)
- [~] DS-4a — GDELT, ALFRED + 시점 저장소. 소유자 PC 확인 끝
- [-] DS-4b — Alpha Vantage·Tiingo·CryptoPanic 모두 무료로 뉴스 불가(소유자 PC 11-20) → 보류, 커넥터 코드는 남김. 뉴스·감성·엔티티는 GDELT+자체 NLP, 공시는 EDGAR·OpenDART (c206b10). 유료 공급원은 Stage 3 뒤 판단(소유자 답 2)
- [ ] DS-4c — CME FedWatch 종가판. DIDM 2단계 시작 때 (약 $25/월)
- [x] DS-4d — OpenDART·KIND(→OpenDART), SEC EDGAR, ECOS — 6곳 모두 소유자 PC 확인 끝 (OpenDART 819건, c6fda98, 11-20). 원장은 DS·DIDM PR 병합 때
- [~] DS-4e — Kalshi 브랜치에 있음(236개 시장). Polymarket은 변호사 확인 전까지 꺼둠
- [~] DS-H — 홈 지표 6개 데이터 계층 — **브랜치 끝: `claude/ds-home-indicators-20261120` @ `f80b3b0`** (main 8445187에서, 4파일, gateway 경유 확인, 새 시험 20 OK, 회귀 묶음 main과 같음; 메인 확인 11-20 03:5x). 대기열 4f. 남은 것: OA-09 진단 반영, BTC 단위 결정(OA-46), 병합 뒤 UI 세션에 계약 전달(소유자 경유)
- [-] DS-3 — RavenPack RPA 1.0 견적, Bigdata.com 비교. **관문 확인 끝(11-20 메인):** 소유자 11-18 답(OWNER_RULINGS_LOG 2026-11-18 절, 질문 1)으로 D14 "3단계" = RavenPack 대안 9개(DIDM Stage 3 아님), D14는 대안으로 구성·Bigdata.com 시험 안 함 → DS-3은 계획에 없음. 소유자가 RavenPack 견적을 원하면 다시 엶 (OA-38)
- [-] DS-2 — Bigdata.com Pro 시범. 쓰지 않음
- [ ] DS 앱 연결 (ID 없음) — 공급처마다 core/gateway/routes.json 한 줄 + display_rights.json + 법률 의견. 표시권, L 뒤. 구조 변경이라 소유자에게 먼저 알림
- [ ] core/didm/novelty.py — DS·DIDM PR에 포함
- [ ] DIDM 키를 Windows 자격 증명 관리자로 옮기기 (선택. KEY-3 병합으로 이제 가능. DATA 세션에 아직 안 알림)

### 2.5 UI (UI/UX 세션, 소유자 경유)

**main에 있음**
- [x] ⑬-2/market-rail-categories-only, ⑬-2/market-hub/1, ⑬-2/indicator-scroll-stability/1, ⑬-2/indicator-conclusions/1 (da0ea20) → ⑬-2/market-hub/main (8e026ab, PR #124)

**UI 브랜치에만 있음 (main 병합은 MERGE_QUEUE 5)**
- [x] ⑬-2/page-redesign/quant, ⑬-2/page-redesign/home, ⑬-2/page-redesign/tools, ⑬-2/page-redesign/guide, ⑬-2/page-redesign/risk, ⑬-2/page-redesign/library, ⑬-2/page-redesign/system (7902381)
- [x] ⑬-2/pyside6-prep/1 (75336f3), ⑬-2/pyside6-prep/2 (5025c6f), ⑬-2/pyside6-verify/1 (847b25c)
- [~] 종료 고침 반영 490562d (원장 행 없음, main 미병합. OS 재확인과 5행 병합 뒤 [x])

**남은 일**
- [!] UI 7쪽 + PySide6 준비 main 병합 — 소유자 실행 확인
- [ ] ⑬-2/page-redesign/system/2 — API 키 화면. KEY-5와 묶어서
- [ ] ⑬-2/page-redesign/home 실데이터 연결 — DS-H 뒤. 새 하위 ID는 UI 세션이 정함 (UI 문서는 `<route>/2`를 소유자 피드백용으로 씀)
- [ ] KEY-5 UI 몫
- [ ] OS-F1 전환 날 UI 몫 (pyqt6_to_pyside6 --apply, 화면 문구 3곳)
- [!] 용어 "캔들 차트 · 봉" 이름 바꾸기 (소유자 결정. "봉"은 금지어)
- [!] 지표 결론 문구·근거 수준 검토, 투자 자문 경계 법률 검토 (공개는 막혀 있음)

**예전 로드맵**
- [x] ⑬-2/a ~ ⑬-2/j, ⑬-2/a4-a, a4-b, a4-c, a4-d, a2, a4-b/2, a4-c/2, a4-d/2, a4-e, a3-type, a3-rail, a3-controls, a3-layout-reading, a1, compact-ui (19a7375), ⑬-2/k/cloud-runtime
- [x] 11-11~11-14 UI 원장 33행: ⑬-2/owner-14-flet, ⑬-2/owner-14-native, ⑬-2/owner-14-native/2, ⑬-2/ui-base-owner-decision, ⑬-2/ui-d7-home-markets-rail, ⑬-2/ui-d8-stock-detail, ⑬-2/us-market-cap, ⑬-2/compliance-ui-d7-d8, ⑬-2/ui-d9-stock-detail, ⑬-2/chart-test-midnight-flake, ⑬-2/ui-d10-markets, ⑬-2/compliance-ui-d7-d8/2, ⑬-2/ui-ci-windows, ⑬-2/ui-d12-chart-zoom-drag, ⑬-2/ui-d9-side-overflow, ⑬-2/ui-d11-rail/a, ⑬-2/ui-d11-review/b, ⑬-2/ui-d11-review/c, ⑬-2/ui-d13-score, ⑬-2/ui-d14-report, ⑬-2/ui-d15-rank, ⑬-2/ui-progressive-guide, ⑬-2/market-nav-v2, ⑬-2/guide-catalog-v2, ⑬-2/taskbar-brand-v2, ⑬-2/market-first-paint, ⑬-2/chart-risk-reward, ⑬-2/indicator-signal-context, ⑬-2/market-menu-click/1, ⑬-2/market-menu-depth/1, ⑬-2/research-workspace-readability/1, ⑬-2/chart-risk-reward/2, ⑬-2/indicator-reading-cues/1 (11-17~11-19 15행은 위 두 묶음)
- [x] ⑬-8/ui-handoff-40, ⑬-8/ui-handoff-43-44, ⑬-8/ui-handoff-49, ⑬-8/ui-handoff-51, ⑬-9/ui-handoff-46 — 웹사이트 검토용 JSON 기록만 끝. 원장이 "실제 전달 미완료"라고 적음 (2.6 전달 목록)
- [~] ⑬-2/a3 — 남은 A3: UI-12 설명, UI-9/11b 결과표, "더 알아보기" 창. **담당 MAIN (CURRENT next_ids, a3-* 앞부분도 MAIN이 함)**. 화면 파일이 UI 브랜치와 겹치므로 시작 전 소유자 경유로 UI 세션과 범위 확인
- [!] ⑬-2/k — 13-7 Windows 실화면, DPI, 키보드, 파일 대화상자, 실데이터·AI 확인 (소유자 PC). 담당 MAIN (CURRENT next_ids)
- [~] ⑬-1 — ⑬-1/a, ⑬-1/b 끝 / [ ] ⑬-1/c (담당 MAIN, CURRENT next_ids)
- [~] ⑬-8 — 끝: ⑬-8/a, b1, b2/a, b2/b, b2/b/2, b2/c/a, b2/c/b/a, b2/c/b/b/native. 남음: 13-8/b, b2, b2/c, b2/c/b
- [~] ⑬-9 — ⑬-9/a 끝 / [!] 13-9/b Windows에서 실제 Claude 요청 성공 확인
- [ ] ⑬-3 모델 증거 카드 확장, ⑬-4 실행 비교, ⑬-5 통합 위험 보기, ⑬-6 취소 가능한 작업, ⑬-7 읽기 전용 SDK — 10-29판 ID(GPT PR #12 브랜치에만). 공식 ID인지부터 정함 (14-1, OA-36). Notion의 13-7·13-8 번호와 다름

### 2.6 WEBSITE/AWS (소유자 경유, 다른 저장소 xkg4real/website)

- [x] W1–W6 — 법인 전 준비, M365 안내, ZIP, KO/EN 정책 HTML 검토본 (handoff dfb6a58, 84daa39, 9d0e678)
- [x] P1–P2 — 저장소, Amplify, Cloudflare DNS, 공개 배포 (SHA 1dbd9ded…, 599bd8c. 다른 저장소라 여기서 확인 못 함)
- [~] W7 — 웹 기록을 handoff에 쌓고 Notion REMAINING WORK 갱신 (상시, 11-13 뒤 기록 없음)
- [x] R1 AWS 읽기 확인 일부 — 시드니 SES·DKIM 정상, quantgen-dev 풀 있음, 서울은 SCP로 막힘
- [-] R1 남은 것 — api.quantgeneration.com/healthz 읽기 확인 (보류)
- [!] ACC-1 가입 화면 — 붙인 날짜 기록 없음 (이 저장소에서 확인 불가)
- [!] ACC-2 메일 인증 (6자리, 재전송)
- [!] ACC-3 로그인 (SRP, MFA, 드러내지 않는 오류 문구)
- [!] ACC-4 비밀번호 찾기·새 비밀번호
- [!] ACC-5 계정 페이지 (메일·비밀번호 변경, 2FA, 마케팅 메일, 탈퇴, 데이터 내려받기)
- [!] ACC-6 머리글·문구 (플래그 뒤 로그인·가입. 운영자 문구는 정책 PR-1 병합으로 관문 풀림)
- [!] ACC-7 보안 (고정 라이브러리, CSP, 토큰 저장)
- [!] ACC-8 바닥글 (개인정보 처리방침 강조, 개인정보 문의 메일)
- [!] ACC-9 시험 (개발 풀 자동 e2e, 운영 풀 수동 1회)
- [!] ACC-10 앱 클라이언트 설정 점검표와 플래그 전 점검표를 소유자에게
- [ ] WEB-0 웹 CI — 상태 모름
- [ ] WEB-1 색 추가 (D10-A) — 상태 모름
- [ ] WEB-2 문구 정리 — 상태 모름. 뜻이 바뀌면 main docs/compliance 먼저
- [-] WEB-3 출시 알림 폼 — ACC로 대체
- [-] WEB-4 자체 로그인 UI — ACC로 대체
- [ ] WEB-5 로그인 뒤 화면 틀 — ACC 뒤
- [ ] 15-6 releases.json 스키마 2
- [!] 웹사이트 세션 재개와 전달 — 정책 문구 다시 만들기(PR-130.json), 비밀번호 규칙 "특수문자 1개 이상", ACC 묶음, 풀 ID·Client ID, 그리고 docs/product/ui_website_updates/ JSON 43개(모두 delivery.status queued, 전달 기록 없음). 11-13 뒤 것: PR-112, PR-115, PR-117, PR-119, PR-124, PR-130
- [ ] 가격 이름 충돌 (Free/Pro/Ultra와 Research/Pro/Team Pilot)
- [ ] Track A (Cognito/SES/API) 범위
- [!] W8 Microsoft 365 (구매, 테넌트, Cloudflare 라우팅, 법률 검토). contact@ 선택으로 바뀔 수 있음
- [ ] AUTH_UI_ENABLED 켜기 전 점검 (ACC-10, 출시 전 8항목)

### 2.7 RESEARCH/Nautilus 로드맵

- [x] ① 묶음 — ①-1 (완료 시각 미검증), ①-2, ①-2/2, ①-2/3, ①-3, ①-4, ①-5, ①-2/4/a
- [ ] ①-2/4 — Notion 1-7은 지웠지만 원장에는 ①-2/4/a만 있음. 범위 확인
- [x] ② 묶음 — ②-1, ②-1/b, ②-2, ②-3, ②-4, ②-5/a (4.1 대기열 순서 승인, 185b56c), ②-5/b, ②-5/c, ②-6
- [x] ②-5 하위 31묶음 — ②-5/§10-a, NEW-M6-01, NEW-M6-18, M4-N5, M3-N07, N-M1-09, N-M1-10, N-M1-11, N-M1-03, N1, NEW-M6-03, NEW-M6-02/a, M4-N2, M4-N1, M4-N12, M3-N04, M4-N8, M3-N08, M4-N3, M4-N6, M4-N11, N11, M3-N06, NEW-M6-14/15/22, M4-N4/N7/N9, N-M1-02/a, NEW-M6-04, NEW-M6-05, NEW-M6-12, NEW-M6-19
- [~] ②-5 상위 — §10 결함 67묶음 중 31 끝, 36 남음 (관찰 모델 14, ID 대응 15 포함)
- [-] ②-5/N-M1-02/b — 소유자 보류 (11-05)
- [x] 2-8 R3 rev2/10.2 A 범위 — 소유자 "전부 다 승인" (db07005)
- [x] ③-1 ~ ③-6
- [~] 3-7 기존 가드 기술 조건 확인 — Notion에서만 완료. 원장 행·커밋 없음 → 근거 찾아 원장으로 닫기
- [-] ④-1 GPT·Gemini 추가 심사 — NOT_PERFORMED, 소유자 면제 (원장 행 없음)
- [x] ④-2/a O2~O15 결정 양식 (0a91f26) / [~] ④-2 상위 — 판정은 받음(⑤-1이 끝남), 원장 행 없음
- [x] ④-3/O11-A2/a, ④-3/O8/a, ④-3/O11-A2/c (0510719, main)
- [~] 4-3/O11-A2/b 실제 Windows 등록 — Notion에서만 완료. 원장 행·커밋 없음
- [~] ④-3 상위 — 하위는 끝, 상위 원장 행 없음. 닫을지 결정
- [x] ⑤-1, ⑤-1/a (원장: Claude 7A 사전 작업), ⑤-1/b, ⑤-1/c
- [x] ⑤-2/a, ⑤-2/a2, ⑤-2/b, ⑤-2/b/2, ⑤-2/d, ⑤-2/e, ⑤-2/e/2, ⑤-2/f, ⑤-2/g
- [~] ⑤-2 상위 — 원장 행으로 닫기 (BTC FAIL 원인 미확인 기록은 남김)
- [x] ⑥-1 (a2ac79b), ⑥-1/readout, ⑥-1/prep, ⑥-1/prep/2, ⑥-1/rulings, ⑥-1/rulings/2, ⑥-2 (8a3d171), ⑥-2/readout
- [x] ⑦-1 (efe5bb2), ⑦-1/E-readout, ⑦-2/p3 (888f121), ⑦-2 (888f121, d895873, 13f4dea, 6e077dc)
- [ ] ⑦-2 후속 — F7 종료 코드 1 원인 미검증. F6·F7 다시 돌릴지 소유자 답 ("F7 재실행 생략 승인" 문구 또는 재실행)
- [x] ⑦-4/BS-21 (Notion 9-7) — 0cc30c3
- [~] ⑧-1 H2 holdout — ⑧-1/a(판독 준비), ⑧-1/b(판독 완료·유효, 11-05 소유자 PC. 커밋 칸 a76af7d는 main 커밋 안내서) 끝. H-D5 main 커밋 남음. 기한 약 2026-12-19, 경고 작업 12-05
- [ ] ⑧-2 2027-01-01부터 잠금 holdout 규칙 (상시 규칙)
- [ ] ⑧-3 GROKTEAM 전망 — 2027-02-01 뒤 태그 클론에서 한 번
- [ ] ⑧-4 분리 명세 2단계 (LAZYOWEN) — ⑧-1 뒤
- [x] ⑨-1/a (7749450), ⑨-1/2/a, ⑨-1/2/b, ⑨-1/2/c, ⑨-1/2/d, ⑨-1/2/d/2, ⑨-1/2/e
- [~] ⑨-1 상위 — 원장 행 없음. [!] L-2 남은 것 — T-FIX-01 보류, I-05 (LA-30 데이터 필요), A-2 파일 이름 답
- [~] ⑨-2 거시 데이터·라이선스 — ⑨-2/a, ⑨-2/c 끝. 실제 데이터와 라이선스 확인 남음
- [~] ⑨-3 상위
- [x] ⑨-3a 하위 — codec/1, store/1, keys/1, data-hash/1, source-digests/1, series-digest/1, series-format/1, series-files/1, series-files/2, series-files/3, fold/1, fold/2, recorder/1/lifecycle (5888d05), recorder/1/outage (f058145)
- [ ] ⑨-3a/recorder/1 상위 — 끝난 것으로 기록할지, 남은 부분을 정할지
- [ ] ⑨-3a 상위 — 병행 산출 완료 기준 확인 뒤 원장
- [ ] ⑨-3b R3 비교 보고서 — ⑨-3a 뒤
- [ ] ⑨-3c R3 과최적화 보정 기준 타당성 검증 (DSR 시행 수 정의, 유효 시행 수, 시뮬레이션) — ⑨-3b 뒤
- [ ] ⑨-3d R3 판정 기준 변경 여부 (소유자 결정) — ⑨-3c 뒤
- [ ] 9-4 Q8, Q15, 판단 기준 B 묶음 — Notion은 지웠지만 본문은 "나중에 따로 결정" (⑨-3d와 묶여 있음)
- [x] ⑨-4/a (c814d22), ⑨-4/2/a, ⑨-4/2/b, ⑨-4/2/c (5f08973 등)
- [~] ⑨-4 상위 — 원장 행 없음. [!] 남은 것 — Q1–Q5, Q7, N_raw 뜻 답
- [ ] ⑨-5 거시 카드 실행, 기술주 펀드 판정 — ⑨-2 뒤
- [ ] 9-7/b 채권 화면 수동 검토, 실제 자금 가격 확인
- [x] ⑫-0, ⑫-1/a, ⑫-1/a/2, ⑫-3, ⑫-2/a, ⑫-2/b/1, ⑫-1/display-owner-decision
- [!] 12-5 (⑫-2 상위, ⑫-2/b) PR-B 실제 resolver — 12.8/K-f와 동결 하네스 결정
- [~] 12-6 (⑫-1 상위) 남은 범위
- [ ] ⑫-4 형식 관문 막힘 대장 — 10-29판 ID(PR #12에만), ⑨-2·⑨-5 뒤. 14-1에서 범위 확인
- [!] owner_confirmed 두 줄 다시 쓰기 — 다음 Nautilus 기록 실행 직전에 한 번, OS-F2 뒤 (지금 code_sha256 10c27010)

---

## 3) 소유자 수동 작업 (OWNER_ACTIONS)

**24시간 안 열린 항목: 7개 (OA-03 ~ OA-06, OA-09, OA-10, OA-43). 기준 5개 이상 → Claude 앱 푸시 알림 (SESSION_PIPELINE 5절).**

push_log:
- 2026-11-20 00:51 KST 메인 — 9건 (OA-02~OA-10) — PushNotification "Mobile push requested"
- 2026-11-20 01:40 KST 메인 — OA-02 완료, OA-43 추가로 9건 그대로. 마지막 알림 뒤 6시간 안이라 다시 보내지 않음 (다음 가능 07:51)

정기 점검: 메인 세션 예약 작업 "QUANTGEN pipeline check (3h)" (trig_01P2NBVZFChNHJGjVdtrDTyC, 매 3시간 :20, 첫 실행 11-20 03:20 KST)

### 3.1 24시간 안 (지금 세션을 막고 있음)

| ID | 무엇 | 요청한 세션 | 요청 시각 | 기한(24h 안?) | 상태 |
|---|---|---|---|---|---|
| OA-01 | 회원 MFA·계정 복구 결정 | PAYMENTS | 11-19 23:43 | — | **완료** 소유자 "지금 그대로: 이메일 MFA 유지" 선택(11-20 00:00 무렵, PAYMENTS 전달). OWNER_RULINGS_LOG 기록은 메인의 다음 PR |
| OA-02 | AWS 운영 풀 단계 (Golden Hour Code 계정) | PAYMENTS | 11-19 22:45 | — | **완료** 1~23c·25 끝(11-20, PAYMENTS 보고; 23a/23b는 CloudShell 명령, 24는 기존 월 예산 사용). 기록은 OWNER_STEPS 1-2 |
| OA-03 | SES no-reply@가 바로 Verified였는지, Cloudflare 규칙이 필요했는지 한 줄 답 | PAYMENTS | 11-19 23:09 | 24h 안 | 대기 |
| OA-04 | 웹사이트 세션에 "비밀번호 규칙에 특수문자 1개 이상 추가" 문장 붙이기 | PAYMENTS | 11-19 23:37 | 24h 안 | 대기 |
| OA-05 | 웹사이트 세션 재개 지시 + 정책 문구 다시 만들기 프롬프트(PR-130.json) 붙이기 | MAIN | 11-19 | 24h 안 | 대기 |
| OA-06 | UI 7쪽을 skymi, whydi PC에서 실행 확인 → UI 세션에 "PR 만들어" | UI, OS, MAIN | 11-18, 11-19 03:13, 05:11 | 지금 (KEY-4 다음 차례를 막음) | 대기 |
| OA-07 | OpenDART 확인 다시 실행 | DATA | 11-19 01:29 | — | **완료** 소유자 PC: 9쪽, 공시 819건 저장 (DATA 보고 11-20 01:57, VENDOR_EVAL 3.1 기록 c6fda98). 공식·무료 공급원 6곳 모두 확인 끝 |
| OA-08 | 무료 키 확인 | DATA | 11-19 15:00 | — | **완료** 소유자 PC 재실행(11-20): Alpha Vantage 뉴스 = 유료 전용(premium endpoint), Tiingo 뉴스 = 403 권한 없음 → 무료로 되는 뉴스 공급원 0 → DS-4b 전체 보류(코드 남김), 뉴스·감성은 GDELT+자체 NLP로 (c206b10) |
| OA-09 | 마스터 부록 H4 홈 지표 진단 명령 실행, 출력 붙이기 | DATA (명령은 MAIN) | 11-17 22:13 (4번 요청, 마지막 11-19 15:00) | 지금 (DS-H 막힘) | 대기 |
| OA-10 | DIDM 질문 답: (a) novelty 보조 조건을 정식으로? (b) 자체 LLM 기반 모델과 학습 데이터 마지막 날짜 (c) 평가표 판단 2칸(자체 NLP 열의 수집 F·실시간 J = X, 자체 NLP 관련성 = X)이 맞는지 — 세 개 모두 DATA 인계 8절에 있음 | DATA | 11-19 00:09 (11-20 00:23 갱신) | 24h 안 | 대기 |
| OA-43 | AWS 비용 출처 확인 — 소유자 11월 막대(11-20 01:5x 공유): EC2-Other $39.47(81%), EC2-Instances $5.55, VPC $2.11, Amplify $1.57, 합 $48.71 → 하루 약 $2.6, 이대로면 월 약 $77–81. 메인 추정(미검증): 작은 인스턴스 1대(t3.micro 급, 약 17.5일)+공인 IPv4 1개(약 17.6일)가 함께 켜져 있고, EC2-Other는 NAT 게이트웨이 또는 t3 unlimited CPU 크레딧 초과(CPU 100% 지속 시 하루 약 $2.16 — 폭주 프로세스나 침해 가능성)와 금액이 맞음. 다음: Cost Explorer EC2-Other를 '사용 유형'으로 묶은 화면 → 메인이 판정. 끄거나 지우지 않음 | PAYMENTS→MAIN | 11-20 01:39 | 24h 안 (권장) | **11-20 소유자 확인**: 음수는 Charge type=Credit 필터 → 크레딧이 갚는 중, 현재 청구 $0.00. CPU 그래프 100% 고정 확인 → 소유자가 크레딧 사양 Unlimited→**Standard로 바꿈**(초과 요금 멈춤). 보안 그룹 인바운드 22·80·443 모두 0.0.0.0/0, IAM 사용자 없음, CloudTrail RunInstances 2026-10-12 20:27 KST, 만든 주체 = 소유자 콘솔 역할 세션(임시 키). 10월 크레딧 요금 약 $5.2 → 100%는 10월 말(약 10-28~29)부터로 추정(미검증). 메인 판단: 원인 미확정(헛도는 프로그램 또는 SSH 침입 뒤 채굴), 22번 전체 개방 + 출시 2주 뒤 갑자기 100%라 침입 가능성 배제 못 함. 다음(소유자): 이 서버를 웹사이트가 쓰는지 확인 → 안 쓰면 Stop / 쓰면 22번을 My IP로 좁히고 로그인해 top으로 프로세스 확인(모르는 프로세스면 정리하지 말고 새로 만들기), Billing Credits 잔액·만료일, CPU 그래프 기간 늘려 100% 시작일 확인 / **11-20 DNS 확인**: 이 EC2 = `api.quantgeneration.com` (Cloudflare 프록시 켬), 본 사이트는 CloudFront(Amplify) → 웹사이트 API 서버라 Stop 대신 ① 22번 Source를 소유자 IP로 ② 접속해 읽기 전용 명령으로 CPU 프로세스·cron·로그인 기록 확인(지우거나 끄지 않음) → 결과 보고 판정. 원 서버 IP는 공개 저장소에 적지 않음(Cloudflare 뒤 원 IP 노출 방지). 뒤에 할 것: 80/443을 Cloudflare IP 대역으로 좁히기 / **11-20 접속 시도**: 소유자가 CloudShell에서 먼저 실행(서버 아님) → EC2 Instance Connect 'Failed to connect'(CPU 묶임 추정). 시스템 로그(Amazon Linux 2023, t3.micro급 913MB, 재부팅 없음, OOM 없음): 10-21 19:0x KST 포트 80 SYN flooding, 10-30 14:2x KST debugfs tracing 자동 마운트(보통 API 서버에 없음, 100% 시작 추정 시점과 가까움), 10-31 SSM Agent 재시작, **11-11 18:4x KST 1GB swapfile 추가 + daemon-reload 여러 번(누가 했는지 소유자 확인 필요)**. 시각은 부팅=생성 시각 가정(추정). 다음: Unlimited 잠깐 되돌려 재접속 → 안 되면 Session Manager(SSM Agent 있음, IAM 역할 필요) 또는 Reboot / 11-20: CPU credit balance 0 고정 확인(접속 실패 원인 추정 맞음). 11-11 스왑은 소유자 작업, 이유 "메모리가 부족해서" → 그때 이미 자원 부족. 원인(앱 헛돎 vs 침입) 미정, 2단계(Unlimited 잠깐 → 접속 → 프로세스 확인) 대기 / **11-20 원인 확정(메인 판단)**: 서버 안 프로세스 목록에서 `sudo nano /usr/share/nginx/html/index.html` 2개(root)가 각각 CPU 약 63%, 실행 21일 8시간 → 시작 10-30 14:26 KST무렵 = 시스템 로그 10-30 기록·10월 크레딧 요금 역산과 일치. 브라우저 터미널을 닫으며 남은 편집기(sudo) 프로세스가 헛도는 것으로 판단. 침입 흔적 없음: 낯선 프로세스·/tmp 파일 없음, 서비스는 nginx·postgresql·quantgen-api(QUANTGEN Account API)·SSM 등 정상, 로그인 성공은 AWS 브라우저 접속 대역과 소유자 IP뿐, 11-13~15 ssh-rsa 거절(인증 전 실패)만. 다음(소유자): 두 프로세스 kill → CPU 하락 확인 → 크레딧 Standard 유지 → 22번 My IP+EC2 Instance Connect 목록, CPU 경보. 뒤에: 이 서버 PostgreSQL(계정 API) 백업 여부를 웹사이트 세션에 확인 / **11-20 23:0x KST 해결**: 소유자가 두 프로세스 종료(SIGTERM 무시 → kill -9로 종료). 직후 CPU 100% idle, load 3.6→1.8 하락, quantgen-api·nginx·postgresql active. `index.html.save`(1바이트, 10-30 05:26 UTC)로 편집기 시작 시각 재확인. 남은 것(소유자): 크레딧 Standard로 되돌림, 10~30분 뒤 CPU 그래프 확인, 22번 좁히기, (선택) CPU 경보, .save 파일 정리 |
| OA-44 | 이메일 MFA 회원 분실(두 번째 확인 수단 없음) | PAYMENTS→MAIN | 11-20 02:0x | — | **완료** 소유자 "2로 권장합니다. Payment세션에다가 전달해주세요"(2026-11-20 02:04:06 KST) → ② 관리자가 옛 계정을 지우고 같은 이메일로 재가입. PAYMENTS에 전달, OWNER_RULINGS_LOG는 4d |
| OA-45 | OWNER_STEPS T14: CloudTrail 회원 쪽 이벤트 하나를 View event로 열어 username/sub가 있는지 확인 (6.1 ② 확정용) | PAYMENTS | 11-20 02:0x | 아님 | 대기 |
| OA-46 | 홈 BTC 단위: 실시간은 Upbit 원화, 일별·그래프는 Yahoo 달러(D8 BTC-USD) → ① 지금처럼 따로 표시 / ② 일별도 Upbit 원화 / ③ 실시간을 해외 거래소 달러로 (메인 권장 ③ 검토: D8과 같은 달러 기준, 원화가는 김치 프리미엄이 섞여 다름 — 표시권 미검증) | DATA→MAIN | 11-20 03:5x | 아님 | 대기 |

### 3.2 나중 또는 조건부

| ID | 무엇 | 요청한 세션 | 요청 시각 | 기한(24h 안?) | 상태 |
|---|---|---|---|---|---|
| OA-11 | 관리 계정의 시험 풀 2개 삭제 (OWNER_STEPS 1-3 경우 1: 삭제 보호 끄기 → Delete) | PAYMENTS | 11-19 22:23 (11-20 갱신) | 아님 | 대기 |
| OA-12 | 웹사이트 세션에 ACCOUNT_SETUP 3부 블록 + OWNER_STEPS 2단계 메시지(풀 ID·클라이언트 ID 채워짐, ACC-3/ACC-4 새 문구 포함) 전달 — PR #133 병합 뒤 최신본으로 | PAYMENTS | 11-20 (KEY-4 3차 반영) | 아님 | 대기 |
| OA-13 | ADMIN_GUIDE 부록 C 시험(C1~C8), T1 시험, 출시 전 8항목·118문항 | PAYMENTS | 11-18, 11-19 | 아님 (풀 완성 뒤) | 대기 |
| OA-14 | D9 "예상 시간"이 작업 시간만인지 한 줄 답 (지금은 나안으로 진행) | MAIN | 11-17 (11-18, 11-19 다시) | 아님 | 대기 |
| OA-15 | ⑦-2 F6·F7 다시 실행할지 ("F7 재실행 생략 승인" 문구로 생략 가능) | MAIN | 11-19 01:18 | 아님 | 대기 |
| OA-16 | 용어 "봉" 바꾸기, 지표 결론 문구 검토 | UI | 11-17 | 아님 | 대기 |
| OA-17 | GH-2에 비밀 검사 CI 넣을지 | MAIN | 11-17 | 아님 | 대기 |
| OA-18 | 전환 날 "OS go" | OS | 미래 | 아님 (UI 병합 뒤) | 보류 |
| OA-19 | owner_confirmed 두 줄 다시 쓰기 (--fingerprint, owner/nautilus-confirm-<날짜> 브랜치 PR). 소유자의 15:30 "완료" 답은 실제와 다름(표는 아직 f995600b, 브랜치 없음) → 지금은 하지 말고 다음 기록 실행 직전에 하라고 알림 | MAIN | 11-19 | 아님 (다음 기록 실행 직전, OS-F2 뒤) | 보류 |
| OA-20 | 변호사 질문: 규제·G2·⑩-1/b, Polymarket·Kalshi, LGPL·공증·iOS 5문항, D12 웹 거래(+KIS), 15-12, 투자 자문 경계 | OS, DATA, MAIN | 11-18 02:43 등 | 아님 | 대기 |
| OA-21 | G1 법인 설립 → "법인 설립 완료: <이름>" 알리기. 이어서 G3 PG, 사업자 등록, 통신판매 신고 | PAYMENTS, MAIN | 상시 | 아님 | 보류 |
| OA-22 | G2 유사투자자문업 판단·신고 | MAIN | 상시 | 아님 | 대기 |
| OA-23 | 표시권 확보, DIDM 결과를 앱에 언제 넣을지 | DATA, MAIN | 상시 | 아님 | 대기 |
| OA-24 | Windows 글꼴 확인 (선택) | OS | 11-18 00:21 | 아님 | 선택 |
| OA-25 | DIDM 키를 자격 증명 관리자로 옮기기 (선택) | DATA | 11-19 15:00 | 아님 | 선택 |
| OA-26 | ⑧-1 H-D5 main 커밋을 소유자 PC의 별도 클론에서 (판독 ⑧-1/b는 끝, 안내서 a76af7d 검토), 12-05 경고 작업 처리 | MAIN | 11월 | 아님 (약 2026-12-19) | 대기 |
| OA-27 | 연구 답: ⑨-4 Q1–Q5·Q7·N_raw, ⑨-1 A-2·LA-30 데이터, ⑨-2 데이터·라이선스, 12-5, 12-7, ②-5/N-M1-02/b 재개 여부, 9-4 | MAIN | 11-05~11-11 | 아님 | 대기 |
| OA-28 | M-12 D8·D10·계좌 평가 정의, ⑪-1 승인, TRADEGEN PR #14·#15·#16 병합과 승인 명령 | MAIN | 11월 | 아님 | 대기 |
| OA-29 | Windows 확인: ⑬-2/k (13-7), 13-9/b | MAIN, UI | 11월 | 아님 | 대기 |
| OA-30 | 빌드 승인: platform-build.yml 실행, 클라우드 Mac 약 $21, Android 폰 시험, 네트워크 허용(pypi.flet.dev, dl.google.com, docs.aws.amazon.com 선택) | OS, PAYMENTS | 11-18 | 아님 | 보류 |
| OA-31 | 유료: CME FedWatch(2단계, 약 $25/월), Trading Economics 견적(3단계 뒤) | DATA | 11-19 15:00 | 아님 | 보류 |
| OA-32 | PAY-0 문의 7건(docs/commercial/inquiries/) 검토·발송과 각 "보내는 방법" 창구 확인, 01 세무사 선정, 07 금융위 문의 전 변호사 검토 여부 결정; 이어서 PAY-2 확인, PAY-3 서버 위치 | PAYMENTS | 11-20 01:00 (초안 7f8939c) | 아님 | 대기 |
| OA-33 | 웹사이트: W8 Microsoft 365, Track A 범위, 가격 이름 충돌, healthz 확인, 전달 대기 JSON(PR-112, PR-115, PR-117, PR-119, PR-124 등 43개 모두 queued) 전달 | WEBSITE | 11-13 | 아님 | 대기 |
| OA-34 | KEY-5 요청을 UI 세션에 전달 | PAYMENTS | KEY-4 뒤 | 아님 | 보류 |
| OA-35 | ⑧-3 GROKTEAM 한 번 실행 | MAIN | — | 아님 (2027-02-01 뒤) | 보류 |
| OA-36 | 오래 열린 GPT PR #12 닫을지, 그 안의 REMAINING_WORK_2026-10-29 ID(⑫-4, ⑬-3~⑬-7, ⑭-1~⑭-3)를 쓸지 | MAIN | 아직 묻지 않음 (메인이 물을 것) | 아님 | 대기 |
| OA-37 | GPT 로컬 커밋 a2d93c2(Notion ⑤-1/a), 7e9e112(Notion ⑩-2/b-private-offline-mvp)가 남아 있는지, push할지 버릴지 | MAIN | 아직 묻지 않음 | 아님 | 대기 |
| OA-38 | DS-3(RavenPack 견적·Bigdata.com 비교)을 계획에서 빼도 되는지 한 줄 확인 (11-18 D14 답 기준 메인 해석: 뺌) | MAIN | 아직 묻지 않음 | 아님 | 대기 |
| OA-39 | PAY-2 소유자 결정 P2-01..P2-15 (docs/commercial/payments/PAYMENT_DESIGN.md 결정 표; 특히 P2-08 단순 해지 일할 환불 없음, P2-09 7일 철회 반환 기준, P2-10 가격 인상 미동의 시 종료 — 법률 확인과 함께), PAY-0 03번 PG 문의에 PG_COMPARISON 3절 질문 6개 추가 여부 | PAYMENTS | 11-20 01:05 | 아님 | 대기 |
| OA-40 | PAY-3 회사 데이터 서버 위치: A 시드니(같은 AWS 계정) / B 서울 / C Cloudflare Workers — 장단점·비용(미검증)은 handoff plans/2026-11-20/KEY5_UI_REQUEST.md 부록, 제안 A | PAYMENTS | 11-20 01:10 | 아님 | 대기 |
| OA-41 | KEY-5 전: core.credentials.set_backend(None) 가 안(시험에서만) / 나 안(앱도 .env만) — 같은 파일 0절 3항 | PAYMENTS | 11-20 01:10 | 아님 (KEY-5 전) | 대기 |
| OA-42 | 이메일 MFA 회원의 비밀번호 분실 처리(ADMIN_GUIDE 6.1) — 임시 비밀번호가 MFA 코드와 같은 메일함으로 가는 맞교환 | MAIN (3차 검토 DOC3-3) | 11-20 01:24 | — | **완료** 소유자 "권장으로 가겠습니다"(11-20 01:25:49 KST) → ② 발급 전 두 번째 확인 + 강제 변경 때 인증 앱 권장. PAYMENTS가 KEY-4 같은 push에 반영, OWNER_RULINGS_LOG는 4d |

---

## 4) 병합 순서 (MERGE_QUEUE 거울)

MERGE_QUEUE.md의 번호를 그대로 둔다. 번호 없는 "제안" 행은 메인 정리안이고 MERGE_QUEUE.md에 행을 넣어야 한다.

| 순서 | 무엇 | 세션 | 상태 | 근거 |
|---|---|---|---|---|
| 1 | ⑦-2/a | MAIN | [x] | PR #126, 56fe32a |
| 2 | OS 작은 PR (OS-P0-a~f) | OS | [x] | PR #127, c28b1d7 |
| 3 | KEY-2 | PAYMENTS | [x] | PR #128, 3249af7 |
| 3b | KEY-2/b | PAYMENTS | [x] | PR #129, ca5da08 |
| 4 | 정책 PR-1 (PAY-A2/a) | PAYMENTS | [x] | PR #130, edbe9f7 |
| 4a | GH-1 + CI concurrency | MAIN | [x] | PR #131, ab24dec |
| 4b | KEY-3 | PAYMENTS | [x] | PR #132, 9f76b07 |
| 4c | KEY-4 | PAYMENTS | [~] | PR #133 148504a, 메인 3차 재검증 중 |
| 4d | 메인 문서 PR: CLAUDE.md(SESSION_PIPELINE 포인터, "법인 설립 완료" → INCORPORATION_CHECKLIST.md), OWNER_RULINGS_LOG(11-19 계정 결정 3건) | MAIN | [ ] | KEY-4 바로 뒤 (11-20 메인이 정함) |
| 5 | UI 7쪽 + PySide6 준비 (+490562d) | UI (소유자 경유) | [!] | 소유자 실행 확인 뒤 |
| 6 | OS-F1 PySide6 전환 | UI + OS | [ ] | 5 뒤, 소유자 "OS go" |
| 7 | KEY-5 (MERGE_QUEUE의 "KEY-3 → KEY-4 → KEY-5"는 낡음 → KEY-5만) | PAYMENTS(요청) + UI(구현, 소유자 경유) | [ ] | 6 뒤 권장 |
| 8 | DS·DIDM | DATA | [ ] | MERGE_QUEUE 8행 "차례가 오면" |
| 제안 | OS-F2 경로 전환 | OS | [ ] | MERGE_QUEUE.md에 행 없음. 브랜치 작업은 지금 가능. Nautilus 지문이 바뀜 |
| 제안 | OS PySide6 종료 원인 기록 (claude/os-pyside6-abort-20261119 8262d6c, 5파일) | OS | [ ] | 행 없음. OS-F1 PR에 묶거나 작은 PR |
| 제안 | 정책 PR-2 | MAIN/PAYMENTS | [ ] | AWS 풀 + 웹 계정 화면 뒤 |
| 미정 | GH-2 정리 PR | MAIN | [ ] | 빈 자리에 |
| 뒤 | owner_confirmed 소유자 PR | 소유자 | [-] | 다음 기록 실행 직전, OS-F2 뒤 |

메모
- UI 소유자 확인이 늦어지면 DS·DIDM(8)을 5보다 앞으로 당길지 메인이 정한다. DS는 소유자 PC 결과만 있으면 준비된다. 브랜치끼리 겹치는 파일은 공유 파일뿐이다(runtime-smoke.yml: KEY-4·UI·DS, source-review.json: KEY-4·UI).
- PR을 여는 조건: 자기 행이 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때. 최신 main 합치기 → 시험 → compliance 기준선은 맨 마지막 → --check PASS → PR.
- 병합 뒤: ledger --done → 이 문서 [x] → MERGE_QUEUE 줄 긋기 → Notion.

---

## 5) 최종 단계 — 가상환경 시험과 파일 전달

모든 트랙이 끝나면(2절에 [ ], [~], [!]가 없고 [-]만 남으면) 메인이 아래를 한다.

**빌드 목록 (자료에 나온 것)**

| 앱/빌드 | 만드는 곳 | 지금 | 최종 시험 (가상환경) | 넘길 파일 |
|---|---|---|---|---|
| 데스크톱 Windows | packaging/quantgen_desktop.spec (PyInstaller), platform-build.yml (수동·v* 태그) | 초안 끝(OS-P0-b), 실제 실행 아직 | 새 venv에서 설치 → runtime-smoke 묶음 → packaging/selfcheck.py → Windows 러너 산출물 실행 확인 | 실행 파일/설치본, packaging/licenses 제3자 고지. 코드 서명(Windows OV)은 G1 뒤 |
| 데스크톱 macOS | platform-build.yml, 클라우드 Mac | OS-F4, OS-F5, OS-M2 대기 | ad-hoc .app 실행 확인 (클라우드 Mac 24시간) | .app 또는 .dmg. 공증은 법인·Apple 조직 뒤 |
| 데스크톱 Linux | 컨테이너 로컬 빌드 | selfcheck 11/11 (PyQt6·PySide6). 판매 대상인지 미정 | 새 venv selfcheck | 소유자가 원하면 |
| Android APK | Flet, stage.py --profile mobile | OS-A1 시험 전. 컨테이너 네트워크 막힘 | 소유자 폰: 크기, 첫 실행 시간, import, Quant Lab 결과 1개 데스크톱과 비교 | debug .apk |
| iOS | — | 계획 없음 (LGPL 정적 링크 변호사 확인 전) | — | — |
| 웹사이트 | xkg4real/website, Amplify (다른 저장소) | 공개 페이지 배포됨, 계정 화면(ACC) 대기 | 개발 풀 e2e, 운영 풀 수동 1회(ACC-9), 배포 커밋 대조 | 배포 주소와 커밋 |
| 동반 앱 MVP (⑩-2) | 별도 | ⑩-2/b 남음 | 합성 데이터 시험 | 소유자가 원하면 |
| TRADEGEN | 다른 저장소 | PR #14–#16 대기 | 이 보드 범위 밖 | — |

**최종 점검표**
- [ ] main 전체 CI 녹색, compliance --check PASS
- [ ] Nautilus 지문 확인, owner_confirmed 두 줄이 지금 지문과 맞음
- [ ] 빌드마다 새 가상환경(또는 새 VM)과 빈 사용자 데이터 폴더에서 설치·실행 시험
- [ ] 결과 보고와 파일을 소유자에게 전달, 원장에 기록
- 주의: Windows·macOS 빌드는 이 컨테이너에서 직접 못 만든다 → platform-build.yml 실행(소유자 승인). Android는 네트워크 허용이 필요하다(pypi.flet.dev, dl.google.com). 환경 변경도 소유자 승인.
