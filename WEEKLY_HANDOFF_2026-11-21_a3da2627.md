# QUANTGEN 중앙 Codex 인계 — 2026-11-21T12:33:42+09:00

## 현재 상태

소유자가 이 대화를 단일 요청 창구로 지정하고 5개 하위 담당의 구현·검토·검증·PR·조건부 병합을 승인했습니다. 실행 ID는 **a3da2627-8d65-4ade-9c47-a1594cb6db15**입니다. STATE와 OS 잠금, 최신 인계 6문서, 이전 실행·완료 원장을 대조한 뒤 CURRENT의 최신 SHA로 CAS 및 원격 read-back을 거쳐 인수했습니다.

**현재는 OS-F2 PR #136의 새 전체 Runtime CI를 기다리는 부분 반환입니다.** 새 main 병합이나 완료 ID는 없습니다. 마지막으로 확인한 main은 `f065ec92dbce1e1b34e4adb0b6dbed724305a2f4`입니다. 계정 사용량은 알 수 없습니다.

| 담당 | 이번 결과 | 남은 작업 |
| --- | --- | --- |
| 총괄 root | 승인·소유권 확인, 5담당 배정, 원격 검증, Notion 및 인계 갱신 | 아래 순서에 따른 CI 판독·통합 |
| OS | [PR136](https://github.com/xkg4real/quantgen/pull/136), 최신 **64ff58e** | 새 전체 Runtime CI 통과 후 병합 |
| DATA/DIDM | DS-H **7ce3791** 검증, DIDM **abd10c6** 수정·게시 | OS-F2 → DS-H → DIDM 순으로 최신 main 반영·준법 검토·PR |
| KEY/결제 | KEY5a **45db2be** 수정·게시 | 앞 작업 병합 뒤 최신 main·준법 검토·PR |
| UI | 로컬 통합 후보의 회귀 수정, 선택 검사와 캡처 | 준법 충돌 2개·기존 PC 확인·OS go·전체 CI·웹 영향 기록 |
| 독립 QA | OS·DS-H·KEY·DIDM의 한정 합성 검증 | 후속 변경·CI에서 새 실패가 생기면 추가 검토 |

이전 DIDM·UI 채팅은 실제 인계 및 구현 중단 상태를 확인했습니다. 이 작업은 본 대화의 하위 에이전트에게 배정했습니다. 별도 채팅에 직접 명령을 보내거나 수신을 확인했다고 주장하지 않습니다. 자동감시·예약·run_now·외부 배포는 하지 않았습니다.

## OS-F2와 PR136

최신 원격 브랜치는 `gpt/os-f2-data-dir-20261121`, 커밋은 **64ff58ed8e6e657d76f9c2f2d946632b03184892**입니다. 첫 구현 `74dce42`는 Claude의 `e44c48e`를 부모로 한 14파일 변경이며, 후속 `64ff58e`는 시험과 source-review의 2파일 변경입니다. 부모·변경 경로·blob SHA·브랜치 head와 핵심 본문을 원격에서 대조했습니다.

경로 조회는 순수 계산으로 유지했습니다. 네이티브/Flet 앱 시작과 기본 KIS/OpenDART 파일 쓰기 전에 선택한 자료 폴더를 명시적으로 준비합니다. 표시 파일에는 앱 이름·생성일·형식만 기록하며, 손상·링크·비정규 파일이면 거절합니다.

분리된 이전 API는 명시적 동의 뒤 독점 rename만 사용합니다. 대상 경합·EXDEV·미지원 상황에서는 복사/삭제로 우회하지 않습니다. 거절된 이전은 기존 폴더에 작은 표시 파일을 남길 수 있습니다. 실제 자료 자동 이전, 새 동의 화면, 삭제 기능, crash-durability 또는 적대적 파일시스템 보장을 제공한 것은 아닙니다.

동결 engine 4파일은 main과 동일합니다. config.py와 main.py의 CRLF를 보존했습니다. 실제 27개 코드 입력으로 계산한 지문은 **bcaf33d91adb5c3a2b1c4a181e0827ed17fe8768827539fe7bd8ecbaea0bb34c**입니다. 기존에 승인된 config 경로 변경으로 달라진 값이며 owner_confirmed/host_fingerprint를 대신 쓰지 않았습니다. 다른 standalone trading/macro/FICC 호출자는 저장소를 만들기 전에 명시적 준비 API를 호출해야 합니다.

로컬 검증은 초기 합동107 PASS(경로33 포함), 시작6 PASS, compliance/export47 PASS입니다. 실제 Qt6.12 앱 모듈 import와 진입 함수도 확인했습니다. 성공 시 실제 QApplication/event loop와 합성 창으로 진행하고, 준비 실패 시 GUI 전에 종료합니다. 공급원·연구 화면은 합성 fixture이며 전체 앱 인수 검증은 아닙니다.

### Windows CI 실패와 수정

첫 head `74dce42`의 Compliance44860609139는 성공했습니다. Runtime44860609205의 Windows 3개 job은 bounded 단계에서 실패했습니다. 직접 읽은 Windows3.12 job136712871169은 863검사 중 실패1·skip15였습니다. 기존 credentials sentinel 시험이 홈만 임시화하고 host LOCALAPPDATA는 격리하지 않아 새 경로 정책과 충돌했습니다.

제품의 경로 우선순위는 유지하고 시험만 고쳤습니다. HOME/USERPROFILE 재할당을 없애고 Path.home·LOCALAPPDATA·APPDATA·XDG·QUANTGEN/Flet 재정의를 임시 fixture로 격리했습니다. 기존52개 시험과 assertion을 보존하고 격리 시험2개를 추가했습니다. **경로·시작·credentials 합동93 PASS, keyring 설치 상태에서 skip0**입니다. 독립 fixture 검사5개도 통과했습니다.

새 head의 [Compliance44861453813](https://github.com/xkg4real/quantgen/actions/runs/44861453813)는 **성공**,20문서·807소스·publication BLOCKED입니다. [Runtime44861453849](https://github.com/xkg4real/quantgen/actions/runs/44861453849)는 아직 진행 중입니다. 일부 단계 성공을 네 installed job 전체 성공으로 기록하지 않습니다.

추가 독립 경로18·시작6 검사는 기존 acceptance와 겹칩니다. 숫자를 합쳐 고유 시험 수를 만들지 않습니다. 초기 환경 누락·상위 격리 patch 충돌·asyncio sandbox 대기 및 실패 로그도 보존했습니다.

구현과 한계: [OS_DATA_STORAGE](https://github.com/xkg4real/quantgen/blob/64ff58ed8e6e657d76f9c2f2d946632b03184892/docs/product/OS_DATA_STORAGE_2026-11-21.md).

## 병렬 작업 결과

**홈 지표 DS-H:** `gpt/ds-home-indicators-20261121` / **7ce37917102af9793d3ccbe851c0554058089df9**. 제품 변경 없이 홈23을 포함한 공통131 PASS와 독립 경계6 PASS를 새로 확인했습니다. 실제 공급원·키링·사용자 홈은 사용하지 않았습니다.

**DIDM:** `gpt/data-source-didm-20261121` / **abd10c6f8a53df5be8c8eff9d89ecb9eb6837de0**, 부모8781267·3파일입니다. 같은 수신시각/payload에 다른 kind/pub/valid가 들어와도 조용히 중복 처리하던 계약 불일치를 합성 EDGAR 경로로 재현했습니다. 같은 버전만 False로 반환하고, 상충한 메타데이터는 StoreError 및 rollback으로 거절하도록 고쳤습니다. 나중 수신시각의 정정과 과거 as-of 답은 유지합니다. 수정 전 새 회귀5건 실패 → store13/DIDM137 PASS, 독립8 PASS입니다. 공급사 대조147도 합성 검증으로 통과했습니다. 엑셀171칸과 V0는 그대로이며 schema/UNIQUE/asof SQL/사전등록/평가기준은 바꾸지 않았습니다.

**KEY5a:** `gpt/key5a-fixes-20261121` / **45db2be73e7f87954cab6782ca4b2717dc97fc62**, 부모dc936d4·8파일입니다. 삭제/교체/off/company 전환 시 성공한 FMP client도 무효화하고 매 접근 시 gate를 확인합니다. KRX는 외부에 노출된 객체를 재초기화하지 않고 비공개 후보를 gate한 뒤 pointer를 교체합니다. 공용 잠금, 생성 실패의 fail-closed, 예외 코드·requests 분류와 시험·설명을 보강했습니다. gateway83 PASS, 관련123 PASS와21 subtests, 독립4 PASS입니다.

DIDM과 KEY는 부모·경로·blob SHA·브랜치 head·핵심 본문 read-back을 확인했습니다. 두 작업의 준법 기준선과 PR은 아직 대기열 차례 전이며 main에 병합하지 않았습니다.

**UI:** Claude UI414eceb와 mainf065ec9의 격리된 미커밋 merge 후보입니다. bonds 충돌은 기능을 보존해 해결했고, 되살아난 옛 portfolio 안내문은 이미 승인된 main의 한영 문구로 복원했습니다. 서로 다른 실행에서 고유14개 선택 case가 통과했고, 7페이지의 한·영14개 PNG를 만들었습니다. Linux offscreen·합성 자료·조회 전 화면입니다. FACTS/source-review 충돌2개, 소유자 PC 확인, OS go, 최신 의존 main 통합, 전체 CI 및 웹 영향 기록은 남아 있습니다. 원격 UI 코드 push/PR은 없습니다. 앱 시작 준비 부분만 OS136에 선별 포함했습니다.

**사업·결제:** 기존 사업 방향·정책·KEY1~4a 완료와 PAY0/PAY2 문서 초안을 대조했습니다. 새 조사·문의 발송·사업 조건 확정은 하지 않았습니다. OA32/39, 법인·규제·PG·표시권·법률 및 운영 검증은 기존 조건으로 남깁니다.

## 복구 자료와 Notion

- OS: /workspace/work/quantgen-os-f2-20261121 /64ff58e. KEY: /workspace/work/quantgen-key5a-20261121 /45db2be. DIDM: /workspace/work/quantgen-didm-central-20261121 /abd10c6(detached). 세 폴더는 보호 경로를 제외한 상태가 깨끗합니다. 원격과 파일 내용이 일치함을 확인한 뒤 로컬 ref/index만 맞췄고 작업 파일을 덮어쓰지 않았습니다.
- UI: /workspace/work/quantgen-ui-central-20261121의 미커밋 merge와2충돌을 보존합니다. 캡처 목록은 /workspace/shared/ui-central-20261121/manifest.json입니다.
- private monitor: CENTRAL_EXECUTION_a3da2627.json, UI_CENTRAL_REPORT_a3da2627.md, UI_CENTRAL_EVIDENCE_a3da2627.json, NATIVE_STARTUP_REAL_a3da2627.log.
- /workspace/work/didm-central-evidence-20261121, /workspace/work/key5a-review-679bce35, /workspace/work/quantgen-qa-a3da2627에 각 재현·초기 실패·최종 검증·source 지문과 보고서를 보존했습니다.
- sapientia Remaining Work15-2에는 부분 진행, PR136의 새 head, 첫 Windows 실패와 fixture 수정, 새 문서 CI 성공과 전체 CI 대기를 최소 반영했습니다. 경고 없는 성공 응답을 private NOTION_SYNC_QUEUE의 os-f2-central-20261121에 원문·변경·응답·revision과 함께 원자 저장했습니다. 검증만을 위한 재-fetch는 하지 않았습니다.
- 실제 .env·홈 저장소·보호 캐시·계정·공급원·원장·동결 실험에 접근하거나 변경하지 않았습니다. 허용된 고정 코드 지문 소스만 읽기 검증했습니다. 새 완료 ID·부모 취소선·main 병합은 없습니다.

## 다음 안전 시작점

1. 같은 승인 범위인지 STATE·OS 잠금·실행/task/handoff·최신6문서·branch/commit·LEDGER를 대조하고, 최신 CURRENT SHA CAS와 새 실행 ID read-back 후 진행합니다. 다른 taken이나 잠금은 선점하지 않습니다.
2. PR136 **64ff58e**의 모든 필수 CI를 판독합니다. 실패는 해당 head/job 로그로 확인합니다. 통과하면 최신 main·freeze OFF·실소유권·독립검토를 재확인하고 merge commit으로 병합합니다.
3. 병합한 OS-F2 하위만 원장/WORKBOARD/Notion 완료로 기록합니다. 다음 DS-H7ce3791을 최신 main과 통합하고 필요한 시험·준법 검토를 마지막에 수행한 뒤 PR을 만듭니다.
4. 그 뒤 DIDM **abd10c6**, KEY **45db2be** 순서로 같은 절차를 수행합니다. 옛 Claude head나 DIDM8781267에서 다시 작업하면 이번 수정이 빠집니다.
5. 옛 private credentials 실행기는 import 시 HOME 설정을 전제로 한 adapter였습니다. 새 OS module fixture를 그대로 실행하도록 맞추고, 기존 assertions를 약화하지 않습니다.
6. UI 후보의 미커밋 코드·충돌·캡처를 보존하고 최신 의존 main 이후 통합합니다. 기존 PC 확인·OS go·전체 CI·웹 영향 기록 조건과 미결 사업/연구/권리 조건을 유지합니다.
7. 진행표·CURRENT·STATE·원격 head를 checkpoint하고 세션 종료 전 상세 인계 및 read-back 후 잠금을 해제합니다. 자동감시나 예약을 재개하지 않습니다.

이전 이력은 CURRENT, LEDGER, [11월14일 누적 인계](WEEKLY_HANDOFF_2026-11-14_2c285afe.md)와 Claude11월20일 인계에 보존했습니다. 이미 끝난 E/Pilot/Step10/P3/F를 다시 요구하지 않습니다.
