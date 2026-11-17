---
status: checkpoint
reason: milestone
from: claude
task: os-expansion
cycle: 2026-11-17
done_ids: none
next_ids: OS-P0-a, OS-P0-e, OS-P0-f, OS-P0-c, OS-P0-b, OS-P0-d, OS-F1, OS-F2
updated_at: 2026-11-18T02:45:00+09:00
stale_after_hours: 3
waiting_on: owner
work_branch: claude/os-prep-20261117
work_commit: 5816125
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-24T17:00:00+09:00
session: https://claude.ai/code/session_016uB1jgXiwx42FSUU5ANwM7
---

# 인수인계: QUANTGEN/MAIN -> OS_EXPANSION (PySide6 전환 준비, 패키징, 모바일)

운영 기준: [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md). 지시문: `plans/2026-11-17/sessions/04_OS_EXPANSION.md` (이 세션의 첫 지시, 전체가 기준).

## 0. 한 줄 요약

지시문 7·8절 작업 6개를 작업 브랜치 `claude/os-prep-20261117`에 push했습니다(최신 `5816125`, **main 병합 전**이라 LEDGER에 없음). 2026-11-18 소유자 요청 "5번 항목(미검증)들에 대해서 지금 당장 검증해서 실현/구현/계획/설계 가능한 부분들은 바로 진행해주세요"에 따라 미검증 항목을 이어서 했습니다. **PySide6 세그폴트와 메모리 폭증의 원인 두 곳을 확정했습니다**: `localization.py`의 `QTimer.singleShot(0, self.apply)`와 UI 브랜치 `bonds.py`의 `setWeight(600)`. 이 둘만 임시 복사본에서 고치자 세그폴트·OOM·실행 못 한 테스트가 모두 0이 되었습니다. 패키지 앱 자체 점검(`--selfcheck`)과 라이선스 고지도 구현해 두 바인딩 빌드에서 10/10 통과했습니다. 지금은 소유자 확인을 기다립니다.

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
| `DATA_API_BASE`·`GATEWAY_PROFILE` 넣지 않음 | D7-G 승인이 handoff에 아직 기록되지 않음 | — |
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
- [ ] OS-P0-d — 저장소판 초안 `docs/platform/PLATFORM_EXPANSION_2026-11-17.md` (`6e92dbf`) ← **소유자 확인 대기**; Notion 수정은 승인 뒤
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

커밋 안 된 변경 없음. 시범 로그·venv는 이 세션 스크래치에만 있음(다른 세션은 볼 수 없음; 필요하면 `PYSIDE6_TRIAL` 6절대로 다시 만듦).

## 6. 다음 할 일 (순서대로)

1. 소유자: 아래 "UI 세션에 전할 것"을 UI 세션에 붙임 → 붙였는지 이 파일에 기록.
2. OS-P0-d — 소유자가 `docs/platform/PLATFORM_EXPANSION_2026-11-17.md`를 확인하면 Notion `6f75e02e0296483086927a73d45df697` 개정 2판 반영 (승인 뒤에만). 완료 기준: 소유자 확인.
3. UI 세션이 점검표 수정을 push하면: `python tools/qt_port/pyqt6_to_pyside6.py --lint --ref origin/claude/friendly-bardeen-r6xe8f` 와 `PYSIDE6_TRIAL` 6절 시범을 다시 돌려 주간 지표 갱신.
4. 첫 PR(대기열 차례에만): 최신 main merge → `runtime-smoke.yml` 경로 목록에 `tools/qt_port/**`·`tests/qt_port_acceptance.py`·`tests/app_identity_acceptance.py`·`tests/app_paths_acceptance.py`, 'Verify bounded source fixtures'에 세 테스트 모듈 추가 → 맨 마지막에 `python -m tools.compliance.check --refresh-baseline ...` → `--check`.
5. OS-F1 (F21 뒤): UI 세션이 최신 main에서 `--apply` 실행, 이 세션은 화면 밖 수정(`pyproject.toml` desktop extra, `runtime-smoke.yml` Qt 설치 줄, `Start-QUANTGEN-Desktop.cmd` 14행, `tools/packaging/smoke_desktop.py`, README) 브랜치와 리뷰. 완료 기준: 지시문 8절 OS-F1 행.

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
- 확인 요청 (11-18): `tools/packaging/stage.py`의 `FILES`가 `qa/acceptance_results.json`·`qa/research_status.json`을 휠에 넣습니다. 앱 코드는 이 파일을 읽지 않고 이름만 문구에 나옵니다. 데스크톱 빌드에서는 spec으로 뺐습니다. 휠에도 계속 둘지 메인이 정해 주세요(stage.py는 이 세션이 고치지 않음).
- 위 `--done` 초안의 OS-P0-b·e·f 커밋 칸에 11-18 커밋(`d2befff`, `8097ca5`, `42be9b8`, `c12643b`, `bd38f93`, `5816125`)을 더합니다.
- 알림: 메인 문서 `MASTER_WORK_DESIGN` 등에 있는 "역방향 의존 없음"(Notion 원문 M2)은 틀립니다: `ui/` 12개 파일 → `quantgen_desktop` 문구 모듈, `quantgen_desktop` 5개 파일 → `ui.*` (함수 안 import).

## UI 세션에 전할 것

(소유자가 그대로 붙여 주세요. 소유자가 전달했는지: **아직 기록 없음**)

> OS_EXPANSION 세션이 PySide6 전환 준비 결과를 올렸습니다. 브랜치 `claude/os-prep-20261117`의 `docs/platform/PYSIDE6_UI_CHECKLIST.md`(점검표)와 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md` 7절(재시범)을 읽어 주세요.
> 세그폴트와 메모리 폭증의 원인은 두 곳입니다. 먼저 고쳐 주세요(둘 다 PyQt6에서도 동작이 같음): ① `localization.py:80`의 `QTimer.singleShot(0, self.apply)`를 자식 `QTimer(self)`로 바꾸기(점검표 6번), ② `bonds.py:201`의 `setWeight(600)`를 `setWeight(QFont.Weight(600))`로 바꾸기(12번, `QFont` import 필요).
> 그다음 순서: 나머지 `6-bound` 27~28곳 → 3번 `receivers`(`stock_detail.py:1470`) → 5번 이벤트 필터 해시 → 4번 `paper.py` 콤보 Enum → 1·2·8·13번 한 줄 수정 → 10번 창에서 떼어 낸 위젯 정리(누수).
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
