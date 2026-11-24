# macOS 차이 조사와 고침 초안 (OS-F4, 2026-11-24)

- 작성: OS_EXPANSION 세션. 기준: main `de32ea1`. 브랜치 `claude/os-macos-differences-20261124`.
- 범위: 네이티브 데스크톱(`quantgen_desktop/`)과 그것이 쓰는 `core/`, `tools/`, `packaging/`. Flet(`main.py`, `ui/`)은 기준 UI가 아니라 제외.
- 방법: `quantgen_desktop/**`·`tests/desktop_*`는 **읽기만** 했습니다(`git grep`으로 `sys.platform`, `os.name`, `startfile`/`xdg-open`, `QDesktopServices`, `QKeySequence`/`QShortcut`, `ControlModifier`/`MetaModifier`, `QFontDatabase`, `.ico`, `msvcrt`/`fcntl`을 찾은 뒤 해당 줄을 읽음). 고친 것은 `packaging/` 두 파일뿐이고, 화면 파일에 필요한 것은 4절의 요청 목록입니다.
- 이 컨테이너는 Linux라 macOS에서 실제로 실행해 보지 않았습니다. "macOS에서" 열은 Qt·macOS 문서상 동작이고, 실측은 `platform-build.yml`(수동 실행)과 소유자 Mac에서 합니다.

## 1. 표

| # | 영역 | 위치 | 지금 | macOS에서 | 조치 | 몫 |
|---|---|---|---|---|---|---|
| 1 | 메뉴 숨기기 단축키 | `quantgen_desktop/app.py:340` `QKeySequence("Ctrl+B")` | Ctrl+B | Qt가 "Ctrl"을 Command로 읽음 → **⌘B로 동작**(정상) | 동작은 그대로 | — |
| 2 | 단축키 표시 문구 | `app.py:249·314`, `owner_ui_language/common.py:8·10` "(Ctrl+B)" | 글자로 고정 | Mac 사용자에게는 실제 키(⌘B)와 다른 글자 | `QKeySequence("Ctrl+B").toString(QKeySequence.SequenceFormat.NativeText)`로 표시 | UI |
| 3 | 차트 확대 | `market_chart.py:336` `ControlModifier` + 휠 | Ctrl+휠 | **⌘+휠**로 동작. 트랙패드 핀치(`QNativeGestureEvent` ZoomNativeGesture)는 처리 안 함 | 핀치 확대 처리 추가 검토 | UI |
| 4 | 확대 안내 문구 | `owner_ui_language/stock.py:38·73·74`, `stock_detail.py:1013` "Ctrl+휠" | 글자로 고정 | 실제는 ⌘+휠 | 2번과 같이 플랫폼별 표시 | UI |
| 5 | 차트 화살표 키 | `stock_detail.py:583` Ctrl·Alt·Meta 조합은 넘김 | — | Mac의 Control 키는 Meta로 들어옴 → 같은 처리 | 없음 | — |
| 6 | 도움말 단축키 | `reading_panel.py:207` `QKeySequence('F1')` | F1 | Mac 키보드 기본 설정에서 F1은 화면 밝기 → **fn+F1**을 눌러야 함 | `QKeySequence.StandardKey.HelpContents`(Mac ⌘?)를 함께 연결 | UI |
| 7 | 파일 열기 | `macro_records.py:235` `QDesktopServices.openUrl` | Qt 공용 | 그대로 동작(Finder/기본 앱) | 없음. `core/`·`tools/`·`packaging/`에 `startfile`·`xdg-open`·`open` 호출 없음 | — |
| 8 | 창 아이콘 | `app.py` `app_icon()`(.ico 먼저, PNG) | QIcon | 창 아이콘은 되지만 **Dock·Finder 아이콘은 번들의 .icns**에서 옴. spec이 `icon=None`이었음 | **고침**: spec이 `assets/icon.png`를 넘겨 PyInstaller가 .icns로 변환 | OS |
| 9 | Windows 작업표시줄 ID | `windows_branding.py:14·24` | win32에서만 | 아무 일도 안 함(정상) | 없음 | — |
| 10 | 번들 정보 | `packaging/quantgen_desktop.spec` `info_plist` | 버전 "2.0.0" 직접 적음, 최소 OS 없음 | Finder "정보 가져오기" 버전이 pyproject와 어긋날 수 있음, macOS 13 이하에서 실행 시 알 수 없는 오류 | **고침**: 버전을 `pyproject.toml`에서 읽음, `CFBundleName`·`CFBundleDisplayName`·`CFBundleVersion`, `LSMinimumSystemVersion` 14.0(6.12 휠 최소 버전) | OS |
| 11 | 번들 ID | spec `bundle_identifier=None` | — | 번들 ID 없음 → Keychain·알림·설정 파일이 실행 파일 경로 기준 | `core/app_identity.BUNDLE_ID`(`com.quantgeneration.quantgen`)는 `BUNDLE_ID_CONFIRMED = False`. 소유자 확인 뒤 넣음 | 소유자 |
| 12 | 자격 증명 저장소 | `core/credentials` → keyring macOS backend(Keychain) | — | 패키지에 keyring 백엔드가 빠지면 키를 저장할 곳이 없음. PyInstaller `hook-keyring`이 모으지만 확인 단계가 없었음 | **고침**: selfcheck에 `os_credential_store`(지금은 모든 OS에서 **보고만**; 비밀값은 읽거나 쓰지 않음. Windows·macOS 빌드에서 `available: true`가 확인되면 필수로) | OS |
| 13 | Keychain 허용 창 | — | — | ad-hoc 서명은 빌드마다 서명이 달라 **업데이트마다 Keychain 접근 허용을 다시 물을 수 있음** | Developer ID 서명 뒤 해결(LICENSE_COMPLIANCE_PREP 4절) | 소유자(법인 뒤) |
| 14 | 자료 폴더 | `core/app_paths.py` | — | `~/Library/Application Support/QUANTGEN`, 이전은 `renamex_np(..., RENAME_EXCL=4)` | 값은 `<stdio.h>`의 RENAME_EXCL과 같음. 실제 Mac 실행은 미확인 | 확인만 |
| 15 | 파일 잠금 | `core/quant/gate_ledger.py`, `run_registry_store.py`, `run_registry_series_files.py` | Windows `msvcrt`, 그 밖 `fcntl.flock` | macOS는 `flock` 지원(APFS). SMB 같은 네트워크 폴더에서는 잠금이 약함 | 없음(자료 폴더는 로컬) | — |
| 16 | 글꼴 | `font_policy.py`, `__init__.py` | QG Interface OTF를 앱에 등록, 대체 글꼴 API | 등록은 같음. 한글 대체는 Apple SD Gothic Neo. 굵기·자간이 Windows와 다르게 보일 수 있음 | 소유자 Mac 화면 확인(OS-P0-f 글꼴 확인과 같은 방식) | 소유자 |
| 17 | 실행기 | 루트 `Start-QUANTGEN-Desktop.cmd`(Windows) | — | Mac용 실행기 없음. 소스 실행은 `python3 -m quantgen_desktop` | 필요하면 `Start-QUANTGEN-Desktop.command` 추가(루트 파일이라 메인 판단) | 메인 |
| 18 | 메뉴 막대 | 앱은 `QMenuBar`를 쓰지 않음 | — | 화면 위 메뉴 막대에 앱 메뉴만(종료 ⌘Q는 Qt 기본). 편집 메뉴 없음(⌘C·⌘V는 위젯 안에서 동작) | 선택: 표준 편집 메뉴 | UI(선택) |
| 19 | 첫 실행 | ad-hoc 서명 zip | — | 내려받은 zip은 격리 속성이 붙어 Gatekeeper가 "확인되지 않은 개발자"로 막음 → Finder에서 Control-클릭 → 열기 | 공증 전까지 설치 안내에 적음 | 소유자 |
| 20 | CPU 종류 | `platform-build.yml` `macos-latest` | arm64 러너 | **Apple Silicon 전용** 빌드. Intel Mac은 실행 안 됨 | Intel 지원이 필요하면 `macos-13`(x86_64) 러너 작업 추가 | 소유자 결정 |

## 2. 고친 것 (이 브랜치)

1. `packaging/quantgen_desktop.spec` (darwin 분기만): `icon`에 `assets/icon.png`(PyInstaller가 .icns로 변환, Pillow는 matplotlib 의존으로 설치됨). `info_plist`에 `CFBundleName`·`CFBundleDisplayName`·`CFBundleShortVersionString`·`CFBundleVersion`(모두 `pyproject.toml`의 version), `LSMinimumSystemVersion` "14.0". `bundle_identifier`는 소유자 확인 전이라 그대로 None.
2. `packaging/selfcheck.py`: `os_credential_store` 점검. `core.credentials.keyring_available()`만 부르므로 Keychain 안의 값은 읽지 않습니다. **이번 판은 보고만** 합니다(메인 검토 2026-11-24): PyInstaller `hook-keyring`이 `keyring.backends`를 모으지만, 동결 빌드에서 참이 된다는 Windows·macOS 실측이 아직 없습니다(이 컨테이너의 Linux 빌드 환경에는 keyring이 설치되지 않아 근거가 되지 못함). `platform-build.yml` 실행에서 `available: true`가 나오면 win32·darwin 필수로 바꿉니다.

## 3. 확인한 것

- spec 구문 확인(`ast.parse`). Windows·Linux 분기는 바뀌지 않음.
- `tests.packaging_policy_acceptance`, `tests.third_party_notices_acceptance`, `tests.app_identity_acceptance`, `tests.credentials_acceptance` 통과(임시 HOME).
- selfcheck를 소스에서 실행해 `os_credential_store`가 Linux에서 `{"available": false, "required": false, "expected_on_this_platform": false}`, ok로 기록됨을 봄(보고만 판).
- 실제 .app 빌드·Dock 아이콘·Keychain은 Mac에서만 확인됩니다: `platform-build.yml`을 macos 입력으로 수동 실행(소유자 또는 메인이 정할 때) → selfcheck JSON의 `os_credential_store` detail `available`이 true(그 뒤 필수 전환), 내려받은 .app의 Dock 아이콘과 "정보 가져오기" 버전 2.0.0.

## 4. UI 세션에 보낼 요청 (소유자 경유)

1. 단축키 표시를 플랫폼별로(1표 2·4번): "Ctrl+B", "Ctrl+휠" 글자 대신 `QKeySequence(...).toString(QKeySequence.SequenceFormat.NativeText)`, 휠은 Mac에서 "⌘+휠".
2. 도움말 열기에 `QKeySequence.StandardKey.HelpContents`를 F1과 함께(6번).
3. (선택) 차트에서 트랙패드 핀치 확대(`QEvent.Type.NativeGesture`, `Qt.NativeGestureType.ZoomNativeGesture`)(3번).
4. (선택) Mac 메뉴 막대 편집 메뉴(18번).
