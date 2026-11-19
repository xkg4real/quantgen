---
status: handoff
reason: usage_limit_weekly
from: claude
task: os-expansion
cycle: 2026-11-17
done_ids: OS-P0-a, OS-P0-b, OS-P0-c, OS-P0-d, OS-P0-e, OS-P0-f
next_ids: OS-F2, OS-F1
updated_at: 2026-11-20T06:10:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/os-f2-data-dir-20261120
work_commit: e44c48e
uncommitted_changes: no
pr: none
usage_weekly_pct: 98.0
usage_5h_pct: unknown
usage_resets_at: 2026-11-24T08:00:00.000Z
session: https://claude.ai/code/session_016uB1jgXiwx42FSUU5ANwM7
---

# 인수인계: QUANTGEN/MAIN -> OS_EXPANSION (PySide6 전환 준비, 패키징, 모바일)

운영 기준: [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md). 지시문: `plans/2026-11-17/sessions/04_OS_EXPANSION.md` (이 세션의 첫 지시, 전체가 기준).

## 0. 한 줄 요약

**주간 사용량 98%로 인계 (2026-11-20 06:10 KST).** 메인이 MERGE_QUEUE 4e에 **병합: OS**를 적었습니다(handoff 811c995). 메인 지시(11-20 05:40 KST, 원문 요지): "`claude/os-f2-data-dir-20261120` @ f9a3a75 (OS-F2 + PySide6 종료 원인 기록)를 PR로 올려 main에 병합되게 준비. 1) main f065ec9 merge 2) config.py CRLF 유지·core/engine feed/state/runtime/__init__ 4개가 `_backup/QUANTGEN_pre_v2_2026-10-05.zip`과 바이트 같음 3) 바뀐 파일 관련 시험 + tests.gateway_*_acceptance 5종 통과, 진짜 ~/.nextgen을 열거나 쓰지 않음(확인 방법을 PR 본문에) 4) 기준선은 마지막에 다시 만들고 `python -B -m tools.compliance.check --check` PASS 5) code_sha256 바뀌면 새 값·이유를 PR 본문에 6) PR 열기(base main, merge commit). 하지 말 것: docs/asset_expansion/cache/ 열기, .env, tests/run_all.py·macro_m8_pipeline·macro_m9_lab·macro_m9_scenarios 실행, qa/acceptance_results.json 재생성, owner_confirmed·host_fingerprint 쓰기, 태그 push, UI 브랜치 수정. 끝나면 SESSION_PIPELINE 3절 형식으로 PR 번호·head SHA·검사 결과를 메인에 보고."

**멈춘 곳:** 1·2단계 끝 — `e44c48e`(main f065ec9 merge, 충돌 없음, push됨). main 대비 14파일 464+/24-(줄 끝 무시해도 같음). `file config.py` → CRLF. engine 4파일 zip과 바이트 같음(True×4). 3단계 회귀는 인계 직후 끝남(e44c48e vs main f065ec9, 임시 HOME, 37파일에서 macro_m8_pipeline 제외 + gateway 5종 + qt_port): 실패 81개 목록 main과 동일, 통과 870→884, 실행 전후 실제 홈 `stat -c %Y ~` 같음. main이 f065ec9 그대로면 6절 2번(회귀)은 끝난 것으로 보고 6절 3번(code_sha256 확인)부터. 4~6단계 안 함. PR 없음.

이전 결과(f9a3a75, main 8445187 기준): 관련 33파일 회귀 실패 83개가 main과 같음, code_sha256 main `10c27010176ad4772a5d4860064c552f21e55b2133923b1fd287a6cc1c4b3414` → 브랜치 `bcaf33d91adb5c3a2b1c4a181e0827ed17fe8768827539fe7bd8ecbaea0bb34c`(config.py 6줄, CRLF 유지). 작업 A 완료(UI 414eceb PySide6 320회 abort 0, PyQt6 18단계 5025c6f와 같음).

## 1. 목표와 완료 조건

- **소유자 원문 (2026-11-17, `owner_answer_1117.txt`):**
  > 2. D9 : 만약 개발이 F까지 완료된 뒤 Pyside6 전환 시 전환에 소요되는 예상 시간이 24시간을 초과한다면 지금 진행할 것. 그게 아니라면 권장대로 승인

  > 1. D6 : 현재 메인세션의 하부 세션 (QUANTGEN/TRADEGEN -> TRADEGEN_GITHUB 과 같은 구조)으로 3가지를 생성할 것. 이때 이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것.
- **소유자 원문 (2026-11-16, Notion `34f5c916fe0c800b9b4af35c80ebe778`):**
  > 앱의 플랫폼 확장과 관련해서 다음과 같은 항목들을 고려해서 (1)문서 수정(할 필요 있으면 수정)할 것, (2) 당장 실행 가능한 것 (병렬로, github merge 순서 등에 따라 앱의 구성 등이 다르면 원래 주어진 급한 Task (i.e. Remaining Work))이 끝난 다음 진행하도록 미리 파이프라인 구축만 해놓을 것
- **완료 조건:** 지시문 `plans/2026-11-17/sessions/04_OS_EXPANSION.md` 7절·8절.
- **범위 밖:** `quantgen_desktop/**`·`tests/desktop_*`·UI 브랜치(UI 세션), 연구 브랜치, `config.py`·`data/**`(OS-F2 전), 결제·계정, main 병합(메인), 외부 변경.

## 2. 근거

| 종류 | 위치 | 쓰는 부분 |
|---|---|---|
| 지시문 | handoff `plans/2026-11-17/sessions/04_OS_EXPANSION.md` | 전체 |
| D9 보고서 | handoff `plans/2026-11-17/D9_PYSIDE6_ESTIMATE.md` | 4절 11묶음, 5절 시간, 7절 나안 |
| D7 보고서 | handoff `plans/2026-11-17/D7_ENV_STRUCTURE.md` 5.3·5.5절 | `app_identity`, 공개판 `.env` 금지 |
| 병합 순서 | handoff `MERGE_QUEUE.md` (`freeze: none`) | OS 전환 PR = F21 바로 뒤 첫 자리 |
| Notion 원문 | `6f75e02e0296483086927a73d45df697` (2026-11-11 판, 읽기만) | OS-P0-d 개정 대상, F2 환경변수 이름 |
| 시범 결과 | 작업 브랜치 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md` | 주간 지표 |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안 |
|---|---|---|
| 변환은 토큰 단위(이름·import·정확히 바인딩 이름인 문자열·문자열 안 파이썬 코드), 설명 문구 13곳은 안 바꿈 | 설명 문구는 OS-F1에서 의도해 고칠 대상 | D9 시범의 단어 전체 치환 |
| `--apply`는 `.git` 있는 폴더 거부(`.qt_port_scratch` 표시가 있을 때만 허용) | 저장소 체크아웃을 실수로 바꾸지 않게 | — |
| 시범 PySide6 쪽에만 글꼴 shim(스크래치) | D9와 같은 조건이어야 비교 가능 | shim 없음 — 거의 모든 테스트가 import에서 실패 |
| OOM으로 죽은 UI 단계 3·5는 상한 8GB로 단독 재실행한 값을 씀(원 로그 보관) | 동시 실행 탓인지 가리려고; 재실행에서도 단계 3은 세그폴트 | 첫 값 그대로 |
| `user_data_dir()` 재정의 이름은 Notion 계획 F2의 `QUANTGEN_DATA_DIR`, 그다음 `FLET_APP_STORAGE_DATA` | 기존 계획과 일치, 모바일 저장소 | 처음 쓴 `QG_USER_DATA_DIR` |
| `DATA_API_BASE`(빈 값)·`GATEWAY_PROFILE`(`personal`) 추가함 (`core/app_identity.py`, 시험 포함) | 소유자 D7-G 승인 (2026-11-18, 원문: "그러면 D7-G의 방식대로 진행하겠습니다"), 메인이 handoff `MASTER_WORK_DESIGN_2026-11-17.md`·`MERGE_QUEUE.md`에 기록 (`762150c`) | 소유자 답, 메인 기록 |
| 게시자·조직명 기본값 "QUANTGEN" (회사 접미사 없음) | 법인 전, 상법 제20조 지적(D11 2.1, 법률 자문 아님); 지금 QSettings 이름과 같아 설정 유지 | — |
| spec은 `git ls-files` + `stage.allowed()`로만 자료를 고름, 계산 해시 원본 3개를 자료 파일로 넣음 | 보호 폴더가 들어갈 수 없게; 패키지 앱의 `code_evidence()` 해시가 None이 되지 않게 | PyInstaller `collect_submodules` (홀드아웃 경로도 모을 수 있음) |
| `platform-build.yml`은 수동·`v*` 태그만, PR 안 엶 | 비공개 뒤 유료, 대기열 규칙 | push·PR 트리거 |
| compliance 기준선은 갱신하지 않음 (`--check` 지금 FAIL: 새 파일) | 지시문 9절 4번: 최신 main merge 뒤 PR 직전 맨 마지막 | 지금 갱신 — 다른 PR과 충돌 |

## 4. 진행 상황 (작업 브랜치, 모두 push됨, main 병합 전)

- [x] OS-P0-a 변환 도구·lint — `tools/qt_port/pyqt6_to_pyside6.py`, `tools/qt_port/__init__.py`, `tests/qt_port_acceptance.py` — `600fcb0`
- [x] OS-P0-e 정식 시범·점검표 — `docs/platform/PYSIDE6_TRIAL_2026-11-17.md`, `docs/platform/PYSIDE6_UI_CHECKLIST.md` — `6e92dbf` (소유자의 UI 세션 전달 대기)
- [x] OS-P0-f 글꼴 대안·세그폴트 — `tools/qt_port/font_probe.py`, `docs/platform/font_probe/`, `tools/qt_port/repro/` — `032c439` (Windows 확인은 소유자가 원할 때)
- [x] OS-P0-c — `core/app_paths.py`, `core/app_identity.py`, `tests/app_paths_acceptance.py`, `tests/app_identity_acceptance.py` — `0bca784`, `260f08d`
- [x] OS-P0-b — `packaging/quantgen_desktop.spec`, `packaging/launch_desktop.py`, `packaging/rthook_build_info.py.in`, `.github/workflows/platform-build.yml`, `tools/packaging/stage.py --profile mobile`, `mobile/` — `4f009aa`, `e65fd43`
- [x] (11-18 추가) OS-P0-b 계속: `packaging/selfcheck.py`(`QUANTGEN --selfcheck report.json`), 고지 생성기 `tools/packaging/third_party_notices.py` + `packaging/licenses/`(LGPL-3.0·GPL-3.0 FSF 원문), spec에 고지·계산 해시 기대값·`qa/` 제외·chardet `.py` 유지, 워크플로에 selfcheck와 Windows·macOS 글꼴 확인 잡(수동 실행만), `tests/third_party_notices_acceptance.py` — `d2befff`, `8097ca5`, `42be9b8`, `c12643b`
- [x] (11-18 추가) OS-P0-e/f 계속: 원인 확정(점검표 6·12·13번), lint `6-bound`·`10-int-enum`, 재시범(`PYSIDE6_TRIAL` 7절, 그래프 `docs/platform/trial_fix/`), `docs/platform/LICENSE_COMPLIANCE_PREP.md` — `bd38f93`, `5816125`
- [x] OS-P0-d — 소유자 승인 (2026-11-18, 원문: "개정 초안 승인합니다."). 저장소판 `docs/platform/PLATFORM_EXPANSION_2026-11-17.md` (`451db93`)을 Notion `6f75e02e0296483086927a73d45df697`에 반영함: 맨 앞 "개정 2판" 요약 + 4절 2행·7.1 F1 2단계·7.2 M2 의존 문장·8절 D9 행을 고침 (나머지 원문은 그대로)
- [x] (11-18 오후) 첫 PR 준비: 최신 main `7c33955` merge(충돌 없음), `runtime-smoke.yml` 경로 목록과 'Verify bounded source fixtures'에 시험 5개 모듈 추가 — `6f2feb9`, 이후 커밋들
- [x] (11-18 오후) **정정:** `qa/` 두 파일은 앱이 읽습니다. `quantgen_desktop/app.py` 시스템 화면의 "프로젝트 상태"가 `tools.status.snapshot.verify(application_root())`로 읽음. 그래서 데스크톱 번들에서 빼던 `42be9b8`을 되돌리고, selfcheck에 `recorded_project_status` 검사를 추가함. 두 바인딩 빌드 모두 11/11 통과 — `39a1642`. 메인에게 "휠에서 빼자" 제안은 철회함.
- [x] (11-18 오후) OS-F1 준비: `tools/qt_port/switch_day.py`(`--check`/`--apply`)가 .py 밖 7곳을 고침(pyproject desktop 고정, runtime-smoke 설치 줄, `.cmd` 14행, spec 기본값, platform-build 기본값 2곳, README). 시험 `tests/qt_switch_day_acceptance.py`. 스크래치 복사본에서 변환 도구와 함께 실행했더니, 남은 "PyQt6"는 설명 문장과 화면 문구 3곳(`app.py`·`translations.py`·`core/ui_legacy_messages.py`의 "PyQt6 네이티브: …", UI 세션 몫, 도구가 note로 알림)뿐임 — `219b815`
- [x] (11-18 밤) UI 세션 수정(`75336f3`) 재시범: lint 97→50. 그대로 돌리면 PySide6 세그폴트 7단계가 다시 남. 이분 탐색 결과 원인은 시스템 화면 커밋 `a00c856`의 `connections.py` `focus_order`(`nextInFocusChain()`으로 창 전체를 돌음). 그 한 곳을 `findChildren`으로 바꾼 복사본은 CI 18단계가 PyQt6와 모두 같고, 새 실패·세그폴트·지워진 객체 줄이 모두 0. 점검표 14번, lint `14-focus-walk` 추가, `PYSIDE6_TRIAL` 8절 — `d0bc363`
- [x] (11-19) 소유자 "F22까지 완료했습니다. 남은 일을 진행해주세요". main `6e077dc` merge(충돌 없음), compliance 기준선 갱신(consistency PASS, publication BLOCKED, FACTS.md 기록), PR 준비 완료 — `1f6a72e`. MERGE_QUEUE가 아직 freeze ON이라 PR은 열지 않고 메인에 자리 요청함
- [x] (11-19) UI `5025c6f`를 고치지 않고 재시범: CI 18단계 모두 PyQt6와 같은 종료 코드, 바인딩 때문에 새로 실패한 테스트 0, 세그폴트 0, 지워진 객체 줄 0, OOM 0(`PYSIDE6_TRIAL` 9절) — `6f928b1`
- [x] (11-19) 메인 "병합: OS" → main `56fe32a` merge, 기준선 재갱신, verify 단계 로컬 711 OK(새 시험 모듈 `-v` 앞 이동 수정 `090dcae`) → **PR #127 열림**, CI 녹색이면 메인이 병합
- [x] (11-19~20) **UI 세션 인계: PySide6 전용 간헐 비정상 종료** (UI `23a6371`, 파일 `docs/product/pyside6_abort_2026-11-19/`, 소유자 지시 원문 "그러면 OS세션에 인계할 프롬프트와 파일을 전달/작성해주세요").
  - 재현: `tests.desktop_market_tabs_acceptance` 4개 동시. 고치지 않은 PySide6 6.12.0에서 80번 중 1번, 72번 중 1번. 같은 `malloc_consolidate(): unaligned fastbin chunk detected`가 `delete_owned_widget`에서 남.
  - 배제: `jobs.py` 가설(Python QRunnable 하위 클래스 + 신호 객체 수명). `QThreadPool.start(callable)`과 `Jobs` 자식 신호 객체로 바꾼 사본도 132번 중 1번 같은 비정상 종료 → 원인 아님. 다른 스레드에서의 `JobSignals` 소멸 0건(112건 모두 화면 스레드), 기다리지 않은 Jobs 0건.
  - **원인 확정(소유자 "네 1번으로 진행해주세요")**: 테스트 보조 코드 3곳(`tests/desktop_market_chart_acceptance.py:60`, `tests/desktop_qscore_acceptance.py:53`, `tests/desktop_acceptance.py:443·450`)이 작업 스레드에서 `QThread.currentThread()` 래퍼를 만들어 보관. 그 기록만 빼면 0/96(그대로 7/96). 앱 코드 변경 없음. 고침은 `threading.get_ident()`, 패치는 `docs/platform/pyside6_abort_2026-11-19/ui_fix_thread_fixtures.patch`. 패치 적용 사본은 PySide6로 160번 연속 0(일반) + 160번 연속 0(tcache 끔), PyQt6 73개 통과. lint `15-thread-wrapper`, 점검표 15번, `PYSIDE6_TRIAL` 10-1절 — 브랜치 `claude/os-pyside6-abort-20261119` `8262d6c`. UI 세션이 반영함(`490562d`, `414eceb`). OS 재확인: `414eceb` PySide6 일반 160번 연속 0, tcache 끔 160번 연속 0, 모두 통과 → **9절 판정 복구**(`PYSIDE6_TRIAL` 10-2절, `1bf2508`). 이 브랜치(문서·lint 15)는 다음 OS PR 때 함께 병합 요청.
- [ ] OS-F1 (F21 뒤, MERGE_QUEUE가 자리 줌), OS-F2 (KEY-2 뒤)

**11-18 추가 검증 (`5816125`):**

```
python -m unittest tests.qt_port_acceptance tests.app_paths_acceptance tests.app_identity_acceptance tests.third_party_notices_acceptance tests.packaging_policy_acceptance -> OK
로컬 Linux PyInstaller 6.22.3, PyQt6 빌드·PySide6 빌드(변환+글꼴 임시 shim) 둘 다: QUANTGEN --selfcheck -> 10/10 통과
  (frozen, build_info, Qt 바인딩 하나, assets·글꼴 파일, code_evidence 해시 = 빌드 때 값 655dc375…, user_data_dir 계산만(만들지 않음), 보호 파일 없음,
   고지 파일·LGPL 원문·Qt Core 별도 파일, 오프스크린 글꼴 6개 등록, quantgen_desktop.app import)
첫 selfcheck에서 qa/acceptance_results.json·qa/research_status.json이 번들에 들어간 것을 잡음 -> 데스크톱 spec에서만 제외 (stage.py는 그대로)
PySide6 6.12.0 Windows·macOS 휠 정적 확인: insertSubstitutions·print_·supportsCharacter(int) 있음, QChar·대체 글꼴 API 없음, Qt 라이브러리 별도 파일, macOS 최소 14(PyQt6 6.12.1도 14)
메모리 폭증 원인: py-spy 네이티브 스택 QTest::qWaitForWindowActive -> sendThroughApplicationEventFilters -> Shiboken storePythonOverrideErrorOrPrint, 첫 예외 localization.py:130 (지워진 ResearchWindow)
고친 복사본: UI 단계 3 두 테스트 3GB+ -> 0.52GB 통과; main 세그폴트 재현 3/3 통과(고치기 전 rc139 1, 실패 2); UI 단계 6 setWeight 고친 뒤 20/20 두 번
전체 재시범(PySide6): 새 실패 13/9, 세그폴트 0/0, 실행 못 한 테스트 0/0, 지워진 객체 29/29, OOM 0 (PYSIDE6_TRIAL 7절)
window_survivors.py: 고친 뒤에도 창마다 숨은 최상위 위젯 6개 누수는 그대로 (점검표 10번, 별개 문제)
Android: 이 컨테이너 네트워크가 pypi.flet.dev·dl.google.com 거부(403) -> 빌드 못 함 (LICENSE_COMPLIANCE_PREP 6절)
```

**11-18 오후 검증 (`219b815`):** 시험 6개 모듈 OK; 두 바인딩 빌드 selfcheck 11/11 (프로젝트 상태 포함); `switch_day.py --check` 7곳 모두 "to do", 스크래치에서 `--apply` 뒤 `--check` rc 0; 화면 코드 변경 0; compliance `--check` FAIL(새 파일, PR 직전 기준선 갱신 예정)

**처음 검증 (`6e92dbf`):**

```
python -m unittest tests.qt_port_acceptance tests.app_paths_acceptance tests.app_identity_acceptance tests.packaging_policy_acceptance  -> OK
--check --ref origin/main (5888d05): files_importing=127, imports=333, signal=117, slot=62, sip=12, prose=13, changes=526 (D9: 127 파일, 약 531곳)
--check --ref UI bec272b: files_importing=132, imports=351, signal=135, slot=65, changes=565
--apply 두 번 (main·UI 스크래치): 두 번째 files changed=0, diff -r 0, compileall OK
--lint main: 83건 (UI 86) — D9 알려진 5곳 모두 잡음
로컬 Linux PyInstaller 6.22.3, QG_QT_BINDING=PySide6: 빌드 성공 596MB onedir, PyQt6·보호 파일 없음, 오프스크린 실행 25초 유지
stage.py --profile mobile: 362개 파일, Qt 막은 상태로 main.py + ui/ 36개 import 성공
git diff --stat origin/main -- quantgen_desktop 'tests/desktop_*' -> 빈 출력
python -m tools.compliance.check --check -> consistency FAIL (새 파일; PR 직전 기준선 갱신 예정)
```

## 5. 중단 지점

커밋 안 된 변경 없음. A의 PyQt6 실행 로그는 이 세션 스크래치에만 있음.

## 6. 다음 할 일 (순서대로, 브랜치 `claude/os-f2-data-dir-20261120` @ `e44c48e`에서)

1. main이 f065ec9보다 앞서 있으면 `git fetch origin main && git merge --no-edit origin/main`. 완료: 충돌 없음, `file config.py`가 CRLF.
2. 회귀: 임시 HOME으로(`HOME=$(mktemp -d) XDG_DATA_HOME=$HOME/.local/share QT_QPA_PLATFORM=offscreen python -m pytest -q` + 아래 파일) main과 브랜치에서 각각 돌려 FAILED/ERROR 목록 비교. 파일: tests/app_paths_acceptance.py credentials_acceptance gateway_acceptance gateway_boundary_acceptance gateway_main_acceptance gateway_remote_acceptance gateway_same_answer_acceptance qt_port_acceptance macro_acceptance macro_m0_rules engine_acceptance nautilus_acceptance packaging_policy_acceptance kis_stream_acceptance kis_workspace_acceptance (macro_m8_pipeline·macro_m9_* 금지). 완료: 실패 목록이 main과 같음(macro_m0_rules test_m0_15_e는 main에도 있는 기존 실패). PR 본문의 ~/.nextgen 근거: 임시 HOME 사용 + 실행 전후 실제 홈의 `stat -c %Y ~` 같음 + 시험이 임시 home만 씀(tests/app_paths_acceptance.py).
3. code_sha256: `from tools.nautilus.runner import code_sha256; code_sha256(Path('.'))` (dotenv.load_dotenv를 patch해서 import) — 브랜치가 bcaf33d9…인지.
4. 마지막에 `python -B -m tools.compliance.check --refresh-baseline` → `git add docs/compliance/source-review.json` 커밋 → `python -B -m tools.compliance.check --check` PASS → push.
5. PR(base main): 저장소에 PR 템플릿 없음. 본문 두 부분 — (가) OS-F2: 경로 순서(QUANTGEN_DATA_DIR → FLET_APP_STORAGE_DATA → `.quantgen-data-dir` 표시 있는 플랫폼 폴더 → 기존 ~/.nextgen → 플랫폼 폴더, 메인 결정 11-20), migrate_legacy_data(confirmed=True)만 이동·합치지 않음, code_sha256 변경과 이유(config.py), ~/.nextgen 근거; (나) PySide6 종료 원인 기록 5커밋(cherry-pick -x, docs/platform 3파일 + tools/qt_port/pyqt6_to_pyside6.py 15-thread-wrapper + tests/qt_port_acceptance.py). 화면 변화 없음 → ui_website_updates 없음. 메인에 PR 번호·head SHA·검사 보고.
6. OS-F1 (MERGE_QUEUE 6, UI 7쪽 PR 뒤): `switch_day.py --apply` + 리뷰.

## 7. 주간 지표 (D9 진척)

| 지표 | D9 시작값 | 11-17 시범 (main `5888d05` / UI `bec272b`) | 11-18 원인 2곳 고친 복사본 재시범 |
|---|---|---|---|
| 바인딩 때문에 새로 실패한 테스트 | 15 | 14 / 10 | **13 / 9** (원인 모름 0) |
| 세그폴트 (rc 139 단계) | 1 | 2 / 3 | **0 / 0** |
| 중간에 죽어 실행 못 한 테스트 | — | 104 / 102 | **0 / 0** |
| "이미 지워진 C++ 객체" 줄 | 223 | 223 / 188 | **29 / 29** |
| 메모리 폭증 OOM | — | 4회 | **0회** |
| 위험 패턴 (`--lint`, main `7c33955` / UI) | — | 83 / 86 | 83 / 87 (`6-bound` 28/29, `10-int-enum` 0/1 새로 나눔) |
| F21 뒤 남은 예상 시간 | 약 30시간 | 12~20 / 30~35시간 | **UI가 미리 고치면 약 8~14시간, 안 고치면 약 18~25시간** (추정) |

## 메인에게

- 대기열 요청: 지금은 없음. OS 전환 PR 자리(F21 바로 뒤)는 그대로 부탁드립니다. 그 전에 작업 브랜치의 도구·`app_identity`·패키징 초안만 담은 **작은 PR 하나**(공유 파일 `core/app_paths.py`, `runtime-smoke.yml` 경로 목록, `.github/workflows/platform-build.yml` 포함)를 언제 받을 수 있는지 `MERGE_QUEUE.md`에 적어 주세요. P3 전에 비면 P3 전, 아니면 F21 뒤.
- LEDGER 기록 요청: 없음 (병합된 ID 없음). 병합 뒤 넣을 문자열(초안):
  - `--done "OS-P0-a | PyQt6->PySide6 변환 도구 check/apply/lint | tools/qt_port/pyqt6_to_pyside6.py, tests/qt_port_acceptance.py | 600fcb0 | qt_port 12 OK, apply 두 번 diff 0, lint D9 5곳"`
  - `--done "OS-P0-c | app_paths user_data_dir/is_frozen, app_identity | core/app_paths.py, core/app_identity.py, tests/app_paths_acceptance.py, tests/app_identity_acceptance.py | 0bca784,260f08d | 10 OK"`
  - `--done "OS-P0-b | 바인딩 중립 spec, platform-build.yml, mobile stage | packaging/*, .github/workflows/platform-build.yml, tools/packaging/stage.py, mobile/* | 4f009aa,e65fd43 | 로컬 PySide6 빌드 성공, mobile import OK"`
  - `--done "OS-P0-e | PySide6 정식 시범·점검표 | docs/platform/PYSIDE6_TRIAL_2026-11-17.md, docs/platform/PYSIDE6_UI_CHECKLIST.md | 6e92dbf | 새 실패 14/10, 세그폴트 2/3, 지워진 객체 223/188"`
  - `--done "OS-P0-f | 글꼴 대안 판정·세그폴트 재현 | tools/qt_port/font_probe.py, tools/qt_port/repro/*, docs/platform/font_probe/* | 032c439 | insertSubstitutions = 현재와 동일(Linux), 세그폴트 PySide6만 재현"`
- **D7-G 소유자 승인 (2026-11-18, 이 세션에서 받음, 원문: "그러면 D7-G의 방식대로 진행하겠습니다")**: MASTER 또는 메인 공지에 기록해 주세요. 기록되면 결제·계정 세션의 KEY-2~5와 이 세션의 `app_identity` 값 자리가 시작됩니다. 소유자에게 D7-G 설명(공급원은 `personal` 길로 지금처럼 동작, 법인 뒤 `routes.json`과 서버 주소만)을 이 세션이 드렸습니다.
- **메인 답 (2026-11-18 05:18Z):**
  1. 작은 PR 자리는 `MERGE_QUEUE.md`에서 F21 뒤 첫 자리이고, 그다음이 PySide6 전환 PR입니다. P3 전에는 받지 않습니다(P3 후보가 main `7c33955` 기준).
  2. `qa/` 두 파일은 지금 그대로 둡니다. 그 작은 PR에서 근거와 함께 제안합니다. 준비해 둔 근거: 앱 코드(core·data·ui·quantgen_desktop·main.py·config.py)는 두 파일을 읽지 않고 문구에 이름만 나옴. `tests/packaging_policy_acceptance.py:18`은 `qa/research_status.json`이 허용 목록에 **있기를** 요구함. `pyproject.toml:55` data-files가 두 파일을 `share/quantgen/qa`로 넣음. 그래서 제안은 세 곳(stage.FILES, 테스트 18행, pyproject 55행)을 함께 고치는 형태가 됩니다.
  3. LEDGER는 main 병합 뒤 11-18 커밋을 더해 메인이 기록합니다.
  4. M2 "역방향 의존 없음" 정정은 다음 MASTER 개정 때 반영됩니다.
- 확인 요청 (11-18): `tools/packaging/stage.py`의 `FILES`가 `qa/acceptance_results.json`·`qa/research_status.json`을 휠에 넣습니다. 앱 코드는 이 파일을 읽지 않고 이름만 문구에 나옵니다. 데스크톱 빌드에서는 spec으로 뺐습니다. 휠에도 계속 둘지 메인이 정해 주세요(stage.py는 이 세션이 고치지 않음).
- 위 `--done` 초안의 OS-P0-b·e·f 커밋 칸에 11-18 커밋(`d2befff`, `8097ca5`, `42be9b8`, `c12643b`, `bd38f93`, `5816125`)을 더합니다.
- 알림: 메인 문서 `MASTER_WORK_DESIGN` 등에 있는 "역방향 의존 없음"(Notion 원문 M2)은 틀립니다: `ui/` 12개 파일 → `quantgen_desktop` 문구 모듈, `quantgen_desktop` 5개 파일 → `ui.*` (함수 안 import).

## UI 세션에 전할 것

(소유자가 그대로 붙여 주세요. 소유자가 전달했는지: **전달함 — 2026-11-18, 소유자 원문 "네 보냈습니다"**)

(2차 전달함 — 2026-11-18, 소유자 원문 "네 보냈습니다")

> (2차, 11-18 밤) OS_EXPANSION 재시범 결과(`75336f3`): 수정이 효과가 있었습니다. lint 97→50, `6-bound`·`receivers`·`setWeight`·이벤트 필터 해시가 모두 0입니다.
> 남은 세그폴트는 하나입니다. 7개 화면 디자인 중 시스템 화면의 `connections.py` `focus_order`가 `nextInFocusChain()`으로 창 전체 포커스 사슬을 도는 부분이 PySide6에서 앱을 죽입니다(점검표 14번). 사슬을 도는 대신 `part.findChildren(QWidget)`로 그 부분의 위젯만 모으면, CI 18단계가 PyQt6와 모두 같아지고 바인딩 때문에 새로 실패한 테스트가 0개가 됩니다(시스템 화면 시험 5개 포함, 두 바인딩 모두 통과).
> 점검표 9번(delegate 참조 10곳)도 고쳐 주세요. 이번 실행에서는 원인이 아니었지만, PySide6는 `setItemDelegate*`로 넘긴 객체를 붙잡지 않아 위험이 남습니다.
> 별도(바인딩 무관): 창을 지운 뒤 숨은 최상위 위젯이 창마다 21개씩 남습니다(`QWidget` 16, `sysPlain` 4, `CompactFieldGrid` 1, 두 바인딩 같음). 확인은 OS 브랜치의 `tools/qt_port/repro/window_survivors.py`로 합니다. 자세한 내용은 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md` 8절에 있습니다.

(1차 전달 내용, 11-18 오후, 처리 완료)
> OS_EXPANSION 세션이 PySide6 전환 준비 결과를 올렸습니다. 브랜치 `claude/os-prep-20261117`의 `docs/platform/PYSIDE6_UI_CHECKLIST.md`(점검표)와 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md` 7절(재시범)을 읽어 주세요.
> 세그폴트와 메모리 폭증의 원인은 두 곳입니다. 먼저 고쳐 주세요(둘 다 PyQt6에서도 동작이 같음): ① `localization.py:80`의 `QTimer.singleShot(0, self.apply)`를 자식 `QTimer(self)`로 바꾸기(점검표 6번), ② `bonds.py:202`의 `setWeight(600)`를 `setWeight(QFont.Weight(600))`로 바꾸기(12번, `QFont` import 필요).
> 그다음 순서: 나머지 `6-bound` 31곳(UI `7902381` 기준) → 3번 `receivers`(`stock_detail.py:1470`) → 5번 이벤트 필터 해시 → 4번 `paper.py` 콤보 Enum → 1·2·8·13번 한 줄 수정 → 10번 창에서 떼어 낸 위젯 정리(누수).
> 위치는 OS 브랜치에서 `python tools/qt_port/pyqt6_to_pyside6.py --lint --ref origin/claude/friendly-bardeen-r6xe8f`로 봅니다(체크아웃 불필요). OS 세션은 `quantgen_desktop/**`를 고치지 않습니다.

## 소유자 Windows 글꼴 확인 (선택, OS-P0-f)

F에 쓰는 파이썬 환경과 다른 임시 venv 두 개를 `%TEMP%\qg-font-probe`에 만들고, 저장소 작업 트리는 바꾸지 않습니다(fetch와 archive만). F 진행 중에는 하지 마세요. 붙여 줄 것: 마지막 명령이 낸 표(12줄 이내)와 `PyQt6_fallback.png`·`PySide6_substitutions.png` 두 장.

```powershell
# QUANTGEN 글꼴 대체 확인 (OS-P0-f) — 소유자가 원할 때만. F 진행 중에는 하지 마세요.
# 저장소 작업 트리·F용 파이썬 환경은 건드리지 않습니다 (fetch와 archive만, 새 임시 venv 두 개는 %TEMP% 아래).
# QUANTGEN 저장소 폴더에서 PowerShell로:
$w = Join-Path $env:TEMP "qg-font-probe"
Remove-Item -Recurse -Force $w -ErrorAction SilentlyContinue; New-Item -ItemType Directory $w | Out-Null
git fetch origin claude/os-prep-20261117
git archive origin/claude/os-prep-20261117 assets/fonts tools/qt_port/font_probe.py -o "$w\probe.zip"
Expand-Archive "$w\probe.zip" "$w\src"
py -3.12 -m venv "$w\v6q"; py -3.12 -m venv "$w\v6s"
& "$w\v6q\Scripts\python.exe" -m pip install -q "PyQt6==6.12.0"
& "$w\v6s\Scripts\python.exe" -m pip install -q "PySide6-Essentials==6.12.0"
foreach ($m in "fallback","families","substitutions","none") {
  & "$w\v6q\Scripts\python.exe" "$w\src\tools\qt_port\font_probe.py" --binding PyQt6 --method $m --out "$w\out" --fonts "$w\src\assets\fonts"
  & "$w\v6s\Scripts\python.exe" "$w\src\tools\qt_port\font_probe.py" --binding PySide6 --method $m --out "$w\out" --fonts "$w\src\assets\fonts"
}
& "$w\v6q\Scripts\python.exe" "$w\src\tools\qt_port\font_probe.py" --compare "$w\out"
Get-Content "$w\out\FONT_PROBE.md" | Select-String -Pattern "Same as today" -Context 0,12
# 붙여 줄 것: 마지막 명령이 출력한 표(12줄 이내)와, $w\out 폴더의 PyQt6_fallback.png·PySide6_substitutions.png 두 장.
# 지울 때: Remove-Item -Recurse -Force $w
```

## 8. 주의사항 / 하지 말 것

- `docs/asset_expansion/cache/` 열기·목록·검색·해시 금지 (git 경로에 `':!docs/asset_expansion/cache'`). `.env`, `~/.nextgen` 열지 않음.
- `quantgen_desktop/**`, `tests/desktop_*`, UI 브랜치·`UI_SESSION_CURRENT.md`, 연구 브랜치 `claude/amazing-gauss-tdiguu` 고치지 않음.
- `CURRENT.md`(메인 소유)에 `push_handoff.py`를 파일 인자로 실행하지 않음. main 병합은 메인이 함. PR은 대기열 차례에만 (비공개 뒤 CI 유료). `platform-build.yml`은 병합 + 소유자 승인 뒤에만 실행.
- 미검증: Windows·macOS PySide6 동작과 글꼴, 패키지 앱 안의 `code_evidence()` 해시 값, Flet Android 빌드, keyring 백엔드, 라이선스(LGPL·공증·iOS 정적 링크, **법률 자문 아님**, 변호사 확인 필요).
