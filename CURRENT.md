---
status: taken
reason: manual
from: gpt
task: owner-product-workflow-20261029
cycle: 2026-10-27
done_ids: ⑬-2/h, ⑬-2/g, ⑬-2/e, ⑬-2/f, ⑫-3, ⑬-1/a, ⑬-1/b, ⑬-2/b, ⑬-2/c, ⑬-2/d, ⑨-2/a, ⑩-1/a, ⑩-2/a, ⑪-1/a
next_ids: ⑬-2/i, ⑬-1/c, ⑨-2/b, ⑩-1/b, ⑩-2/b, ⑪-1/b, ⑫-2/b
updated_at: 2026-10-30T15:50:57+09:00
stale_after_hours: 3
waiting_on: none
work_branch: gpt/pyqt6-completion-20261030
work_commit: 6f5afa87417d0ca618b904971f018b3802f35f86
uncommitted_changes: yes
pr: https://github.com/xkg4real/quantgen/pull/17
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: unknown
session: codex
execution_id: 46096aec-0aea-49fd-8d87-7452618c5b51
handoff_id: 2026-10-27/owner-product-workflow-20261029/a45bca0b6c73178729d1c3d21a0cd7bbbb15bd75
---

# QUANTGEN owner-directed product continuation

## 0. 현재 결과
최신 진행: 6f5afa87417d0ca618b904971f018b3802f35f86 원격 read-back, draft PR17. ⑬-2/e·f·g·h 완료. Macro v2 기존 validated readers와 판정/용도 의미 유지; 45 native tests 및 CI41016023200 Windows/Ubuntu success. Notion h 취소선 반영. ⑬-2/i Rules/모의 Trading 현재 미커밋 구현·임시 저장소 검사 중. 실제 API/원장/Windows 육안/전체 이전은 미완료.
사용자가 남은 개발의 즉시 재개를 직접 요청하여 재개했습니다. 자동감시의 next_eligible_at은 이 직접 요청을 차단하지 않습니다. 새로운 실행 ID로 CURRENT를 CAS 선점한 뒤 gpt/pyqt6-completion-20261030에서 남은 native 화면/내보내기/패키징을 진행합니다. 기존 완료 ID는 재처리하지 않습니다.
공개 사이트용 A/F1 HTML은 내용을 보존해 완성하고 사용자에게 전달했습니다. 실제 사이트 업로드는 사용자가 맡으며 이 작업에서 제외했습니다.
기존 Flet A/F1 Home, ResearchRun 세션 기록/내보내기, 패키징 CI, F1 브라우저 아이콘은 PR #13/#14/#15로 main에 반영됐습니다.
PyQt6 데스크톱은 draft PR #16의 검증된 부분 구현입니다. 전체 기능 이전 완료가 아닙니다. 최신 commit c401e0d581d7439cba7580aa6b5d19b0ac6a9beb에서 로컬 native 검사 20개와 Ubuntu 3.12 / Windows 3.12·3.14 CI가 통과했습니다. 위 검증은 이전 실행의 결과이며 이번 실행에서 남은 구현을 계속합니다. 사용량 수치는 unknown이며 한도 소진을 주장하지 않습니다.

## 1. 최신 사용자 결정

- 사용자 요청으로 전달한 [2026-10-30 승인 원문 및 O8 후속 질문](https://app.notion.com/p/4095c916fe0c8173a4dae8156aa03ae4?pvs=204). 메인세션 수신·반영 여부는 아직 확인되지 않았습니다.
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
- PR #13, #14, #15 (merged), #16 (open draft)
이전 Claude/Nautilus 연구의 근거는 이전 작업 브랜치의 CONTINUATION_STATUS/REMAINING_WORK/HANDOFF_MANUAL/O2_O15_DECISION_FORM 및 LEDGER에 있습니다. 이 파일들은 현재 제품 main에 모두 들어 있지 않습니다. UI 작업을 이유로 누적 연구 브랜치를 통째로 병합하지 마세요.

## 3. 검증 근거와 한계
최신 Qt Actions: https://github.com/xkg4real/quantgen/actions/runs/41004952793
- Windows Python 3.14 job 123897634125: completed/success
- Ubuntu Python 3.12 job 123897634272: completed/success
- Windows Python 3.12 job 123897634360: completed/success
각 job은 allowlist wheel 빌드/설치, checkout 밖 runtime smoke, bounded source fixtures, native 20 tests, checkout 밖 native smoke를 통과했습니다.
최초 Ubuntu Qt CI의 libEGL.so.1 누락은 CI job에 libegl1/libopengl0를 설치하도록 수정했고 이후 통과했습니다. 게시 환경 설정은 바꾸지 않았습니다.
로컬 검사와 화면 캡처는 합성/주입 데이터입니다. 실제 시장 API 성공, 실제 Windows 육안/DPI, 서명 installer 또는 모든 연구 gate 통과의 증거가 아닙니다. 기존 provider probe의 CONNECT 403은 별도 제약으로 남습니다.
가격·최적화·공식 gate 코드는 변경하지 않았습니다. README provenance digest 갱신은 기록된 테스트 수 변경이 아닙니다.

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
현재 우선: ⑬-2/i Rules/모의 Trading 검증 → 선택 AI → 전체 대응·실제 Windows 인수. e·f·g·h 완료 범위는 재작업하지 않습니다.
1. ⑬-2/e: Derivatives, ETF, Crypto를 native로 이전. 기존 UI 내부 계산 조립 로직·출처·단위를 먼저 매핑하고 공유 코어를 사용. 합성 fixture로 입력 가지와 계산값 비교. 실제 계정/저장 카드/보호 원장은 열지 않기.
2. Macro v2 Overlay/Model cards/Research register, Strategy Lab, KRX, paper Trading, Rules/Settings, optional AI 패널 이전. 레지스트리/판정/모의 엔진 lifetime 의미 보존. UI 이전을 연구 승인 변경으로 확대하지 않기.
3. portfolio/FICC 등의 native export와 전체 화면 feature parity, keyboard/resize/DPI, Windows 실행/installer·icon 점검. 그 후 기본 데스크톱 실행 방식 전환과 PR16 ready/merge 판단. Flet browser는 유지.
4. ⑬-1/c: cross-model/historical ResearchRun과 canonical identity/공식 gate 연결은 별도 증거와 연구 승인 범위에 맞춰 진행.
5. ⑨-2/b: official data/rights/vintage 증거 취득. 네트워크 정책을 우회하지 않기.
6. ⑩-1/b·⑩-2/b: 전문 법률 검토·데이터 권리·배포 허용 범위 후 공개 서비스 판단.
7. ⑪-1/b: 별도 TRADEGEN 작업에서 consumer 격리·dedup 검증. 이 태스크는 TRADEGEN을 변경하지 않음.

## 7. 보호 범위
.env, 보호 캐시 4개, 실제 원장, 동결 연구/사전등록/holdout은 읽거나 해시하거나 변경하지 않습니다.
공식 gate/판정/owner approval 필드, 실제 주문 경로, TRADEGEN, 공유 환경/보안/네트워크 설정 변경 금지.
비공개 원문·첨부·보고서를 public repo에 올리지 않습니다. AUTO_STATE 수동 수정 금지.
미실행·실패·거절을 계산 COMPLETED 또는 하나의 초록 준비 완료 상태로 합치지 않습니다.

## 8. 결정과 외부 의존성
UI/PR/main 권한은 이미 해결됐고 native 잔여 구현을 막는 승인 대기가 아닙니다.
남아 있는 별도 연구 의사결정: Nautilus O2–O15, PR-B 12.8/K-f/frozen-harness 범위, R3 rev2/10.2 A, ②-5 §10/BS-21 등. 최신 결정 기록을 확인하고 이미 승인된 것은 다시 묻지 않습니다.
공식 데이터 사용권과 전문 법률 의견을 임의로 승인 처리하지 않습니다. PyQt 공개/상업 배포 라이선스도 이후 배포 판단에 포함합니다.

## 9. Claude / Codex 재개
최신 handoff CURRENT/README/TEMPLATE/AGENTS/LEDGER/AUTO_STATE를 읽고 exact SHA CAS + 새 execution ID 원격 read-back으로 소유권 확인 후 시작합니다.
Qt source 시작점: gpt/pyqt6-desktop-20261030 @ c401e0d581d7439cba7580aa6b5d19b0ac6a9beb. 새 gpt 브랜치에서 이어갑니다.
설치/실행: python -m pip install ".[desktop]" ; python -m quantgen_desktop.
검사: python -m unittest tests.desktop_acceptance -v. packaging CI는 실제 최신 commit의 결과로 확인합니다.
현재 main ebb6d61...에는 PR16 내용이 아직 없습니다. 기존 Flet 앱 제거/재설치 요구 금지.
원래 자동 주기 next_eligible_at=2026-11-05T00:00:00+09:00은 이번 직접 요청 작업으로 초기화하지 않습니다. 이미 처리한 ID/commit을 보존하고 중복 작업하지 않습니다.
