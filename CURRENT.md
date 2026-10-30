---
status: taken
reason: manual
from: gpt
task: owner-product-workflow-20261029
cycle: 2026-10-27
done_ids: ②-5/§10-a, ②-5/NEW-M6-01, ⑦-4/BS-21, ⑬-2/j, ⑬-2/i, ⑬-2/h, ⑬-2/g, ⑬-2/e, ⑬-2/f, ⑫-3, ⑬-1/a, ⑬-1/b, ⑬-2/b, ⑬-2/c, ⑬-2/d, ⑨-2/a, ⑩-1/a, ⑩-2/a, ⑪-1/a
next_ids: ④-3/O11-A2, ②-5/§10-b, ⑬-2/k, ⑬-1/c, ⑨-2/b, ⑩-1/b, ⑩-2/b, ⑪-1/b, ⑫-2/b
updated_at: 2026-10-30T08:00:47Z
stale_after_hours: 3
waiting_on: none
work_branch: gpt/approved-research-followups-20261030
work_commit: 2da6469d8b3d45eab61d682555ff630ce1f564f7
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: unknown
session: codex
execution_id: 46096aec-0aea-49fd-8d87-7452618c5b51
handoff_id: 2026-10-27/owner-product-workflow-20261029/a45bca0b6c73178729d1c3d21a0cd7bbbb15bd75
---

# QUANTGEN owner-directed product continuation

## 0. 현재 결과
BS-21 완료: PR19 source 941455aa5a0b41d0941325846dab89a05d80b5e1 → main 0cc30c3ed1a7e25f1d06215a858d57bc199e9be6 병합/read-back. 합성 funding 8개, Qt adapter/calculator/export 3개, bond self-check PASS; CI41020717371 Windows3.12/3.14+Ubuntu3.12 success. PR18의 독립 회귀 사례를 보존하여 통합하고 중복 PR을 종료했습니다.
§10 첫 단위 완료: PR20 source0e7dd782c01707b0bd3cff78c4c7deb837f761eb → main ce12459eae1258e03270702092c839758cde91fa 병합/read-back, CI41022505498 Windows3.12/3.14+Ubuntu3.12 success. 71ID/67그룹/14관찰 초기 목록·순서, 합성 재현5개와 NEW-M6-01 HAC t-stat 교정. 독립 sandwich6사례 old FAIL/new PASS, 표본부족·Qt 회귀 PASS. 나머지66그룹·14관찰, 모호 매핑15개는 미완료.
현재 직접 작업: ④-3 O11 A2. 기존 gpt/approved-research-followups-20261030 @2da6469 재사용, 보호 경로가 없는 별도 allowlist checkout에서 등록 전용 초기화 구현/합성검증 및 승인 기록 반영. 이 연구 브랜치를 제품 main에 통째로 병합하지 않습니다. 그 다음 §10 잔여. O11은 현재 스펙/코드 열람까지이며 아직 구현하지 않았습니다. 원문/진행/재현/다음 시작점은 private reports/2026-10-30/WEEKLY_CONTINUATION_20261030.txt. 정상 재개는 이전 execution/task/handoff/branch/commit 일치와 새 CAS/read-back이 필요합니다. 직접 미완료 작업은 주간 반환/cooldown으로 막지 않습니다.
⑬-2/e~j native 구현/자동 검증을 완료했고 PR17을 main a1adf008568aa7475a9db5ff7a5c97b41b0a12fb에 병합했습니다. 소스 e1df541b35b320bf8360e80305503f72a6043ab0, 59 native tests, CI41018384446 Windows3.12/3.14 및 Ubuntu3.12 success; 원격 PR/main read-back 완료. PR16은 중복 방지로 닫았습니다.
Windows 앱은 PyQt6 선택 실행, 브라우저는 Flet 유지. 6 workspace, 기존 연구 도구, Macro v2/Strategy Lab, Rules/모의 Trading, 명시적 JSON/ZIP, 선택 AI 해설을 연결했습니다. 실제 API/AI·원장 실행·Windows 육안/DPI·서명 installer는 검증하지 않았고 ⑬-2/k는 미완료입니다. 공개 HTML/F1 묶음은 별도 전달됐고 실제 사이트 업로드는 사용자가 맡습니다.
Notion REMAINING WORK에는 완료한 하위 범위만 취소선 처리했습니다. 사용자 직접 작업은 returned/cooldown 때문에 대기하지 않습니다. 새 승인 전달 페이지(1절 링크)를 실제 읽고 private 보존했으며, §10 분류/순서·BS-21·O11 A2의 후속 구현과 O8 심사/실파일럿 승인 경계를 구분합니다. UI 병합에 해당 연구 변경을 섞지 않았습니다.

## 1. 최신 사용자 결정

- 사용자 요청으로 전달한 [2026-10-30 승인 원문·O8 후속 질문·BS-21 추가 승인](https://app.notion.com/p/4095c916fe0c8173a4dae8156aa03ae4?pvs=204). BS-21 후속 승인 원문이 추가됐습니다. 메인세션이 원문 수신·읽기를 확인했습니다. BS-21 구현·검증·main 반영은 PR19, O11 A2 및 §10 후속은 별도 진행하며 O8 심사 생략/실파일럿 승인을 추정하지 않습니다.
- Windows 앱은 PyQt6, 브라우저는 기존 Flet 유지. 계산/데이터 코어 공유, A안 + F1.
- UI 수정, PR 생성, main 병합은 이미 허용됨. 과거의 UI 승인 대기를 되살리지 말 것.
- 공개 HTML은 사용자가 업로드. 호스팅 접근 요청·배포·공유 환경 변경은 제외.
- 정확성이 우선. 사용량/런타임 제약이 가까우면 새 작업을 시작하지 않고 검증 상태와 Claude 재개 문서를 남김. 실제 계정 사용량은 도구에 없어 unknown.
- 현재 기존 게시 환경과 이 작업 대화를 사용. 별도 새 환경 게시/이전은 중단된 결정이 유효.
- 2026-10-30 사용자 최신 지시: 직접 작업은 즉시 계속하고 기존 자동 예약을 매시간 재개용으로 갱신. 동일 예약 ID, DTSTART 2026-10-30 16:00 KST, HOURLY, enabled=true read-back. 로컬 PAUSED와 환경 설정은 유지.
- 매주 화요일 17:00 KST 전 또는 런타임 한도 전에 그 주 전체 작업을 Claude에게 인계. 이번 11-03 16시 마감 준비/17시 전 반환. 실제 계정 토큰 잔량은 unknown.
- 사용자 확인된 Notion REMAINING WORK(f77eb54f-725c-82b8-becb-81d7d61704bd)에 완료 범위 취소선과 현재 순서/종류를 반영. 기존 13개 하위 범위는 기록 근거로 완료, 전체 연구 검증 재실행 주장 없음. 새 작업도 완료 즉시 갱신.

## 2. 확인할 근거
현재 Qt 브랜치:
- docs/DESKTOP_MIGRATION_2026-10-30.md
- docs/product/PACKAGING_2026-10-29.md
- docs/product/RESEARCH_HOME_CONTRACT_2026-10-29.md
- docs/product/DATA_ACQUISITION_2026-10-29.md 및 DATA_READINESS_2026-10-29.json
- docs/product/DISTRIBUTION_REVIEW_2026-10-29.md
- docs/product/TRADEGEN_READ_ONLY_BRIEF_2026-10-29.md
- tests/desktop_acceptance.py, .github/workflows/runtime-smoke.yml
- PR #13, #14, #15, #17 (merged); #16 closed superseded; BS-21 #19 merged
이전 Claude/Nautilus 연구의 근거는 이전 작업 브랜치의 CONTINUATION_STATUS/REMAINING_WORK/HANDOFF_MANUAL/O2_O15_DECISION_FORM 및 LEDGER에 있습니다. 이 파일들은 현재 제품 main에 모두 들어 있지 않습니다. UI 작업을 이유로 누적 연구 브랜치를 통째로 병합하지 마세요.

## 3. 검증 근거와 한계
최신 native CI: https://github.com/xkg4real/quantgen/actions/runs/41018384446
- e1df541에서 Ubuntu Python3.12, Windows Python3.12/3.14 모두 success.
- allowlist wheel 빌드/설치, checkout 밖 runtime smoke, bounded source fixtures, native 59개 검사와 checkout 밖 Qt smoke.
- 합성/주입/임시 저장소만 사용. 설치 smoke는 network/protected path access를 차단합니다.
- 기존 Flet ETF 수정주가/fallback 검사 PASS. 로컬 light/dark와 1000x700 배치 확인, dark F1 대비 수정.
실제 공급자/AI/계좌/원장, 실제 Windows 화면/DPI, 서명 installer 성공의 증거는 아닙니다. 공식 gate/판정·TRADEGEN·환경/보안 정책을 변경하지 않았습니다.

## 4. 완료한 하위 작업
- ⑫-3: PR-F runtime wheel/resources/clean Windows·Ubuntu CI. PR13 main 00e0488fd9f7cf7be01b3bcc51de1a5f72727cc7.
- ⑬-1/a: Monte Carlo ResearchRun 관측 계약, 입력/코드 근거, JSON/report ZIP. verdict NOT_RUN, reproducibility PARTIAL 유지.
- ⑬-1/b: 명시적 데스크톱 저장 지속성. PR14 main 22ac580bb249e2b42c1d2bfae91d4e47ebc8f743.
- ⑬-2/b: A/F1 Home의 세션 결과·일별 지표 연결, 원래 Flet 16경로 유지. 시세 미조회/실패/오래됨 구분.
- ⑬-2/c: F1 favicon/PWA/Apple 아이콘과 호환 의존성. PR15 main ebb6d61fa8ee7813cca9dbd8df58cea96b80dc05.
- ⑬-2/d: 선택 실행하는 PyQt6 native 부분 구현, draft PR16. Home, Markets, 4개 Monte Carlo, 4개 portfolio objective, Bonds, Rates 4도구, FX 3도구, Structuring 4상품, Signals 3백테스트, Macro sheet/daily/weekly, Library JSON/ZIP, System. 계산은 기존 core를 호출. 단일 작업 큐, GUI-thread 전달, 중복/종료 가드, 오류 category 표시. 전체 native 완료는 아님.
- ⑨-2/a: 73 series/29 CSV 의존성 목록, receipt 검증·날짜 집합 일치 비교 도구. 원본 데이터 취득 완료가 아님.
- ⑩-1/a: 법령/데이터 약관 1차 검토와 전문 검토용 체크리스트. 법률 승인 아님.
- ⑩-2/a: 독립 offline companion 구조/제약 문서와 private prototype. 공개 MVP나 배포 완료 아님.
- ⑪-1/a: QUANTGEN 측 읽기 전용 export/consumer 인수 조건 문서. TRADEGEN consumer 구현 아님.
공개 HTML은 별도 private 전달물: 29 links, 71 controls, 4 scripts 유지; 저장된 애니메이션 heading wrapper 9개 정규화 후 의미 텍스트 동일. seeded 계산과 16 strategy cards 동일, light/dark/mobile/menu/FAQ/filter 검증. 원본에 빠진 analytics companion 참조는 보존했으며 사용자가 기존 부속 폴더를 유지해야 합니다.

## 5. 기존 기록과의 관계
이전 CURRENT의 “PR-F 미구현”, “UI PR/merge 승인 없음”, “Home 데이터 미연결”은 위 후속 작업으로 대체됐습니다.
기존 LEDGER의 ②-5/c PT-04, ⑫-2/a identity 설계, ①-2/4/a 및 이전 연구 결과는 지우지 않습니다. 별도 연구 브랜치 성과와 현재 main을 구분하세요.
Qt Rates는 현재 제품 main의 curve 함수를 호출합니다. 별도 PT-04 연구 패치를 몰래 포함하지 않았습니다.
이번 app.py/tools.py/tests/packaging 문서 재수정은 남은 native 화면 연결, 명시적 export, 배포 검증을 위해 필요합니다. 완료된 pricing/solver/gate 결과는 재작성하지 않습니다.

## 6. 다음 실행 순서
1. ⑬-2/k 실제 Windows 표시/DPI·키보드·파일 대화상자·선택 공급자 확인은 사용자 PC 인수가 필요합니다. 실행 안내 docs/DESKTOP_MIGRATION_2026-10-30.md; Start-QUANTGEN-Desktop.cmd. 서명 installer/공개 배포와 구분합니다.
2. 승인 연구 후속: BS-21/NEW-M6-01/§10 초기 단위는 완료. 다음은 ④-3 O11 A2 registration-only 초기화와 승인 기록 반영, 그 다음 §10 남은 현재 코드 재현/정정입니다. 기존 연구 브랜치 근거를 먼저 읽고 UI 변경과 구분합니다. 실파일럿/실원장/동결 연구는 실행하지 않습니다. O8 심사 생략은 승인된 것으로 보지 않습니다.
3. ⑬-1/c 전체 모델·과거 이력·canonical identity/공식 gate 연결은 승인 범위/근거별로 진행. 전체 ResearchRun 완료를 주장하지 않습니다.
4. ⑨-2/b 공식 데이터/rights/vintage, ⑩-1/b 법률·권리, ⑩-2/b 공개 MVP는 외부 근거/관문 이후. AWS 공식 download CONNECT403은 우회하지 않습니다.
5. ⑪-1/b TRADEGEN consumer는 별도 TRADEGEN 범위이며 현재 태스크에서 변경하지 않습니다.
6. 화요일 16시부터 주간 전체 완료/미완료를 정리하고 17시 전에 인계. 그 전 직접 미완료 작업은 기존 hourly 예약과 exact 소유권 확인으로 재개합니다.

## 7. 보호 범위
.env, 보호 캐시 4개, 실제 원장, 동결 연구/사전등록/holdout은 읽거나 해시하거나 변경하지 않습니다.
공식 gate/판정/owner approval 필드, 실제 주문 경로, TRADEGEN, 공유 환경/보안/네트워크 설정 변경 금지.
비공개 원문·첨부·보고서를 public repo에 올리지 않습니다. AUTO_STATE 수동 수정 금지.
미실행·실패·거절을 계산 COMPLETED 또는 하나의 초록 준비 완료 상태로 합치지 않습니다.

## 8. 결정과 외부 의존성
UI/PR/main 권한은 이미 해결됐고 native 잔여 구현을 막는 승인 대기가 아닙니다.
수신된 결정: O2–O15 rev6 기본값 + O11 A2/초기12+U(U≤24), O8 대체심사 기록, ②-5 §10 정식 범위·순서, BS-21 DF 수정. 이 승인에 대해 재질문하지 않습니다. 실제 O8 심사 결과/Appendix B와 owner Windows 파일럿 검증·별도 owner_confirmed는 아직 완료 증거가 없으며, 심사 생략 질문은 면제 승인이 아닙니다. PR-B 12.8/K-f/frozen-harness와 R3 rev2/10.2 A는 해당 별도 원문 범위로만 판단합니다.
공식 데이터 사용권과 전문 법률 의견을 임의로 승인 처리하지 않습니다. PyQt 공개/상업 배포 라이선스도 이후 배포 판단에 포함합니다.

## 9. Claude / Codex 재개
최신 handoff 6문서, STATE와 OS lock을 확인합니다. 예약 재개는 직전 execution/task/handoff ID/branch/commit을 대조한 뒤 새 execution ID CAS+read-back으로만 합니다. 현재 실행 ID는 위 front matter입니다.
제품 main은 ce12459eae1258e03270702092c839758cde91fa(PR20, PR19 BS-21, PR17 UI 포함). 구현 source gpt/pyqt6-completion-20261030 @ e1df541b35b320bf8360e80305503f72a6043ab0. UI와 별도 누적 연구 브랜치를 무조건 합치지 않습니다.
설치/실행: python -m pip install ".[desktop]" ; python -m quantgen_desktop. Windows cmd launcher도 제공. 브라우저는 기존 flet run main.py --web 명령.
검사: docs/DESKTOP_MIGRATION_2026-10-30.md의 bounded fixture 목록과 최신 CI를 사용. 전체 연구/실제 원장/보호 캐시/holdout 검사 금지.
주간 전체 인수인계는 계속 누적합니다. 사용자 요청은 완료된 범위/남은 외부 인수/새 승인 연구 범위를 구분하며 다시 승인 대기를 만들지 않습니다.
