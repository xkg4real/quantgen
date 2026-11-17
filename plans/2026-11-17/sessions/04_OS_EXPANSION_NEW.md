# OS 확장 세션 지시문 (신규)

대상: 새 Claude 세션 (D6-A). 저장소 `xkg4real/quantgen`을 붙여 시작.
붙여넣기: "복사 시작"부터 "복사 끝"까지.

---- 복사 시작 ----

당신은 QUANTGEN OS 확장 세션입니다. Windows 패키징, macOS, Android 시험, iOS 준비, 배포 목록(manifest) 형식, PyQt6→PySide6 변환 도구를 맡습니다. Remaining Work, 화면 (`quantgen_desktop/**`, UI 세션), 웹사이트, 결제, TRADEGEN은 맡지 않습니다.

## 소유자 요청 (원문, 2026-11-16 Notion)
"앱의 플랫폼 확장과 관련해서 다음과 같은 항목들을 고려해서 (1)문서 수정(할 필요 있으면 수정)할 것, (2) 당장 실행 가능한 것 (병렬로, github merge 순서 등에 따라 앱의 구성 등이 다르면 원래 주어진 급한 Task (i.e. Remaining Work))이 끝난 다음 진행하도록 미리 파이프라인 구축만 해놓을 것
- 전 플랫폼의 Module &BL이 Pyside6 기반이 맞는지
- 앱 개발 시 별도 기기 구입 등 (예외. android는 개인 핸드폰으로 실험 예정)의 항목 없이 순수하게 당장 실현할 수 있는 방법은 무엇인지
- 법인 설립 전/후로 앱 구성, architecuture나 개발 단계의 수정 등이 발생하는지, 발생한다면 이 부분도 고려해서 순수하게 할 수 있는 업무를 추려나가고 향후 개발 방향성에 맞게 조정할 것."

## 확정된 방향 (소유자 D9 답을 여기에 붙임; "전부승인"이면 아래)
- BL (`core/`, `data/`, `config.py`)은 UI 없는 공통 Python으로 유지. 지금도 UI import 0건.
- 데스크톱 (Windows·macOS) UI만 F 뒤 PyQt6 → PySide6. 모바일은 PySide6가 아님 (Qt for Python iOS는 numpy를 못 씀; PySide6 Android 빌드는 Linux/macOS 호스트 전용).
- 모바일은 Flet (Android 먼저, 소유자 폰). iOS는 법인 뒤.
- Phase 0는 지금 브랜치에서만. 변환 도구는 이 세션이 만들고, **전환일(OS-F1)에 도구를 실행하는 것은 UI 세션**입니다.
- ID는 `OS-` 접두어 (OS-F1, OS-M2, OS-A1 …). 연구 병합의 F1~F21, Bonds F1~F5, S1~S4와 겹치지 않게.
- 나중에 여쭐 것 (지금은 제안으로만 문서에 적음): Mac 없이 macOS (GitHub macOS 러너 수동·태그 + 확인 단계 클라우드 Mac 24시간 약 $21, us-east-1), 번들 ID `com.quantgeneration.quantgen`, 개인 명의 Apple 가입 안 함, Windows 서명은 법인 OV 인증서까지 대기.

## 공통 규칙
1. 시작: `python3 tools/handoff/push_handoff.py --show`, `--ledger`, handoff 브랜치 `MERGE_QUEUE.md`, `MASTER_WORK_DESIGN.md` (특히 0절), `UI_SESSION_CURRENT.md`, `OWNER_HANDOFF_POLICY_2026-11-13.md` 읽기. 인계 파일은 `OS_SESSION_CURRENT.md` (`status: idle`로 만들어져 있음 → 시작할 때 `checkpoint`; 손으로 커밋, force 금지, 다시 읽어 확인).
2. `docs/asset_expansion/cache/`는 어떤 ref·어떤 체크아웃에서도 열기·목록·해시·검색 금지. git grep/ls-files에는 `':!docs/asset_expansion/cache'`. 저장소 전체 find, ls -R, grep -r, rg 금지. 코드 작업은 그 폴더를 받지 않는 sparse 클론에서 (마스터 4.1절, "no cache folder" 확인 뒤), 아니면 `git status --porcelain -- <경로>`처럼 늘 경로를 줌. `git add`는 파일 이름으로만, `git add -A`·`git add .` 금지.
3. `.env`, `~/.nextgen` 열지 않음. 비밀·서명 키·인증서를 커밋하지 않음.
4. 클라우드에서 `tests/run_all.py` 실행 금지. 개별 검사만.
5. 기준선 갱신은 최신 main을 merge한 뒤 맨 마지막 (`python -m tools.compliance.check --refresh-baseline --reviewed-by ... --review-note ...` → `--check`).
6. Phase 1 전에는 어떤 PR도 main에 병합하지 않습니다. 이후에는 `MERGE_QUEUE.md` 순서, 한 번에 PR 하나. `origin/main`은 merge로 반영 (이미 push한 브랜치는 rebase 금지, force push 금지). 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 녹색일 때만. 자기 테스트가 어느 CI 단계에서도 돌지 않으면 병합하지 않음: 첫 코드 PR에서 `tests/app_paths_acceptance.py` 등을 `runtime-smoke.yml`의 단계에 더함 (`core/app_paths.py`는 이미 경로 목록에 있음; 공유 파일이라 대기열 경유).
7. F 파일 금지 (F가 main에 들어가기 전): `quantgen_desktop/bonds.py`, `quantgen_desktop/bonds_portfolio_narrative.py`, `ui/bonds_page.py`, `ui/qcharts.py`, `.github/workflows/nautilus-registration.yml`, `qa/research_status.json`, README 상태 표.
8. 금지: `quantgen_desktop/**`·`tests/desktop_*` 수정 (UI 세션 소유), 서명 없는 빌드 공개 배포, Android 릴리스 키·Apple/Google 계정 생성 (법인 뒤 소유자), `runtime-smoke.yml` 수정 (OS-F1의 Qt 설치 줄과 규칙 6의 자기 테스트 추가만 예외; UI 브랜치·PR122 수정이 들어간 main 위에서), 웹사이트 `releases.json`·다운로드 쪽 수정 (웹사이트 세션).
9. 공유 파일 (`config.py`, `data/krx/kis_client.py`, `core/app_paths.py`, `pyproject.toml`, `.github/workflows/**`)은 대기열로 한 번에 PR 하나. `data/krx/kis_client.py`의 다음 수정 주인은 결제·계정 세션의 KEY-2이므로, 이 세션의 경로 수정은 KEY-2 병합 뒤입니다.

## 맡는 경로
`tools/packaging/**`, 새 `packaging/` (`build/`, `dist/` 이름은 준수 검사가 건너뛰므로 쓰지 않음), 새 `tools/qt_port/**`, `core/app_paths.py`, 새 `core/app_identity.py`, 새 `mobile/**`, `docs/platform/**`, 새 `.github/workflows/platform-build.yml`. 대기열을 거쳐 `config.py`·`data/krx/kis_client.py`·`data/krx/opendart_client.py`의 경로 줄 (OS-F2).

## Phase 0 (지금, 브랜치 `claude/os-prep-20261117`만, 병합 없음)
1. **OS-P0-a 변환 도구.** `tools/qt_port/pyqt6_to_pyside6.py`: `--check` (파일별 개수), `--apply` (여러 번 돌려도 같은 결과: import, `pyqtSignal→Signal`, `pyqtSlot→Slot`, `pyqtProperty→Property`, `sip.isdeleted(x)→not shiboken6.isValid(x)`). 지금 규모: 데스크톱 54개 모듈, 테스트 73개, 도구 1개, 'PyQt6' 352줄, pyqt*/sip 177줄. 알려진 동작 차이 3개: `paper.py`의 str Enum 항목 데이터, `tests/desktop_operation_fixes_acceptance.py`의 findChildren 튜플, `stock_detail.py`·`stock_detail_side.py`의 sip.isdeleted (줄 번호는 UI 브랜치에서 바뀔 수 있으니 이름으로 찾음). 화면 밖 수정 목록도 같이 만듦: `pyproject.toml` desktop 의존성, `runtime-smoke.yml`의 Qt 설치 줄, `Start-QUANTGEN-Desktop.cmd`, `README.md`, `AGENTS.md`와 handoff `AGENTS.md` §6, 준수 문서 약 15개의 PyQt6 표현, PyQt6 import가 있으면 실패하는 검사.
   완료 조건: `--check`가 개수를 출력. **임시 복사본에서만** `--apply` 뒤 `python -m compileall -q quantgen_desktop tests` 성공 (저장소 브랜치에는 `quantgen_desktop/**` 변경을 커밋하지 않음). PySide6로 데스크톱 검사 2~3개를 Linux 오프스크린에서 돌린 결과 기록. PySide6-Essentials 6.12.0에 QtSvgWidgets·QtTest가 있는지 `pip install` 후 import로 확인 (없으면 Addons 필요, 라이선스 LGPL 확인).
2. **OS-P0-b 빌드 파이프라인 초안.** `.github/workflows/platform-build.yml` (트리거: `workflow_dispatch`와 태그 `v*`만, concurrency cancel-in-progress): windows-latest PyInstaller onedir, macos-latest arm64 `.app` (ad-hoc 서명), Android는 Flet `flet build apk`. `packaging/launch_desktop.py`와 spec 초안. `tools/packaging/stage.py --profile mobile`: Flet 쪽이 쓰는 Qt 없는 `quantgen_desktop` 문구 모듈을 포함 (`ui/bonds_page.py:27` 외 8개 파일이 불러옴).
   완료 조건: 브랜치에 push, 워크플로 문법 확인. 실제 실행은 소유자 승인 뒤 (비공개 뒤에는 macOS 분당 $0.062).
3. **OS-P0-c 경로와 앱 정체성 (코어만).** `core/app_paths.py`에 `is_frozen()`, `user_data_dir()` (지금 `~/.nextgen`이 `config.py:180,187,288`, `data/krx/kis_client.py:54`, `data/krx/opendart_client.py:44`에 박혀 있음; 기존 위치 우선). `tests/app_paths_acceptance.py`. `core/app_identity.py`: 조직명, 번들 ID, 게시자 표시명, 업데이트 목록 주소, Cognito 도메인·클라이언트 ID 자리, 라이선스 공개키 자리. 호출하는 쪽 연결은 나중: 앱의 QSettings 이름과 `windows_branding.py`는 UI 세션, spec·Flet `[tool.flet]`은 이 세션, `config.py`·`kis_client.py`·`opendart_client.py`의 경로 줄은 KEY-2 뒤 OS-F2.
   완료 조건: 검사 통과, 브랜치 push.
4. **OS-P0-d 문서.** Notion "QUANTGEN 플랫폼 확장 실행 계획" (6f75e02e0296483086927a73d45df697) 개정 2판 초안 (소유자 승인 뒤에만 Notion 수정). 고칠 것 9가지: ① §4 규모 (quantgen_desktop 83개 29,927줄, ui/ 36개 13,245줄, core/ 185개) ② "역방향 의존 없음"은 틀림 (마스터 2.3) ③ CI 시간 120분 제한, 실측 Windows 약 286분·Linux 약 39분 ④ F1 규모 갱신과 세 번째 동작 차이 ⑤ ID를 OS- 접두어로 ⑥ 소유자 결정 UI-D1 (네이티브만 UI 기준)과의 관계: 모바일 Flet은 축소판 동반 앱 ⑦ 사실 갱신, 출처와 함께: Android 개발자 인증 2026-09-30 4개국, 2027 전 세계; 인증서 최대 460일; Azure Artifact Signing은 한국 미지원이라는 Microsoft Q&A 답변 (공식 문서로 확인 못 함); Play 개인 계정 12명 14일 시험; Play 금융 앱은 조직 계정이 맞다고 봄 (추론); pyside6-android-deploy는 Linux/macOS 호스트 ⑧ iOS의 PySide6는 정적 링크라 LGPL 조건을 지키기 어렵다고 봄, macOS 강화 런타임·공증도 함께 **변호사 확인 필요** ⑨ 병합 순서 절과 런치 플랜 8~11단계 연결, 전환은 UI 세션이 실행. 저장소 문서 `docs/platform/PLATFORM_EXPANSION_<날짜>.md`는 Phase 1 첫 PR과 함께.

## Phase 1 (관문: F가 main에 들어가고 LEDGER에 기록됨, PR121·122 처리됨, UI 세션의 열린 데스크톱 PR 0개, 소유자 "OS go")
1. **OS-F1 전환일.** 이 세션은 도구와 화면 밖 수정 목록을 넘기고 (`UI_SESSION_CURRENT.md`에 동결 공지 요청), UI 세션이 최신 main 위에서 `--apply` → 동작 차이 3개 → 화면 밖 수정 → 기준선 마지막 → PR 하나. 이 세션은 리뷰와 화면 밖 수정 확인을 맡습니다.
   완료 조건: `git grep -n PyQt6 -- quantgen_desktop tests tools pyproject.toml .github Start-QUANTGEN-Desktop.cmd`가 0건, 정확한 head에서 모든 작업 녹색, 병합, 동결 해제.
2. 그다음 하나씩: OS-F2 (경로; KEY-2 뒤) → `app_identity` 연결 (화면 쪽은 UI 세션) → OS-F4 (macOS 차이) → OS-F5 (macOS는 `platform-build.yml`에만) → OS-M2 (`.app` 결과물) → OS-A1 Android 시험 2일 (APK 크기, 첫 실행 시간, import 성공, Quant Lab 결과 1개를 데스크톱과 비교) → OS-F3 키 저장은 결제·계정 세션의 KEY-2와 함께.

## Phase 2 (법인 뒤)
서명 (D-U-N-S → Apple 조직 → Windows OV), Android 업로드 키, 스토어 등록. iOS는 결제 결정 (iOS는 앱 내 결제 규정) 뒤.

## 보고할 것
브랜치와 커밋, 각 완료 조건 결과, 확인 못 한 것 (PySide6-Essentials 구성, Flet 0.85.2 빌드 옵션, macOS 러너 실행 시간), 소유자에게 남은 질문. `OS_SESSION_CURRENT.md`에 기록.

---- 복사 끝 ----
