# QUANTGEN 중앙 작업 현황 — 2026-11-21

갱신: 2026-11-21T12:10:34+09:00 · 총괄: 이 대화의 메인 Codex · execution a3da2627-8d65-4ade-9c47-a1594cb6db15
소유자 승인: “네 진행하세요.” (단일 요청 창구, 최대5하위담당, 구현·독립검토·검증·PR·조건통과후병합)

| 담당 | 실제 에이전트 | 현재 작업 | 상태 | 확인 근거 / 다음 단계 |
| --- | --- | --- | --- | --- |
| 총괄 | root | 소유권·승인·분담·대기열·실증범위 관리 | 진행 | CURRENT CAS/read-back, main f065ec92, 이 표/WORKBOARD 갱신 |
| OS·저장소 | os_f2_review | OS-F2 no-replace migration·marker·쓰기전경로준비 | 구현·회귀 중 | e44c48e 기반 로컬초안보존. 이전7 Linux PASS는 한정결과; 추가 QA 발견 marker 디렉터리 문제 보강 중 |
| 데이터·DIDM | didm_data_integration | 최신 DS-H/DIDM GPT브랜치 독립검토·통합준비 | 검토·격리검사 준비 | DSH7ce37917, DIDM87812679. 인계의131/132/147 PASS는 과거근거이며 새실행과 구분 |
| 네이티브 UI | native_ui_integration | 7화면·최신main 비교/구동검증, OS-F2 앱시작준비접점 | 검토·준비 중 | UI414eceb, 최신범주9개/QGfont유지. UI7화면PC확인·Qt전환조건은미완료 |
| 게이트웨이·결제 | key5a_reproduce | KEY5a stale FMP·KRX refresh fail-open 및S1~7 | 수정 준비 | dc936d4 기반. 기존4개합성실패재현보존; 신규수정/검사후보고 |
| 독립 검증 | independent_qa | OS-F2 우선, 후속각단위 독립검토 | 검토 중 | marker가 디렉터리일때 경로안정성 깨짐을 합성재현해구현담당에게전달 |

## 오늘의 진행 순서와 완료 조건

1. OS-F2: 경로조회는순수계산, 명시적 앱시작/쓰기준비에서mkdir+marker. 동결engine소스불변. marker실패/대상경합에도기존데이터보존·지원불가이동failclosed. 관련합성검사/독립QA/코드지문/준법정합성 → PR → 필수CI통과후병합.
2. DS-H: OS-F2병합뒤최신main반영·홈계약/실시간행오류격리검증·준법정합성 → PR/CI/검토.
3. DS·DIDM: DS-H병합뒤최신main반영. 사전등록/문턱/평가기준변경없이시점/스키마/확률검증. 실제성능·실제API근거로확대하지않음.
4. KEY5a: 수정/합성회귀는병렬, PR차례는위작업뒤. KEY5UI접점은별도UI담당과계약맞춤.
5. UI: 승인7화면회귀/캡처/최신main충돌점검. 기존PC확인·OSgo전최종UI병합/바인딩전환보류.
6. 사업/결제문서: 기존정책확정과PAY0/PAY2제안/미결목록구분. 새조사·발송·사업조건임의확정없음.

완료는 코드원격반영·검증·필요시병합까지근거가있을때만표시. 새소유자결정/PC실행/법률·라이선스·표시권/실제API·동결연구근거는합성검사로대체하지않는다.
현재 새 완료ID/새PR/main변경 없음. 자동감시·예약/run_now·외부배포 없음.

사용자는 이 표와 각PR·commit·검사로그·캡처를확인할수있다. 하위에이전트는이대화에딸린작업자이며독립채팅방자동생성을약속하지않는다.

## 원문과 인계

[CURRENT](CURRENT.md) · [WORKBOARD](WORKBOARD.md) · [MERGE_QUEUE](MERGE_QUEUE.md) · [DIDM인계](DATA_SOURCE_SESSION_CURRENT.md) · [UI인계](UI_TO_MAIN_CODEX_2026-11-21.md) · [기존승인안](GPT_WORK_ALLOCATION_APPROVAL_2026-11-21.md)
