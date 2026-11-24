# Linux 배포 차이 조사 (OS-F3, 2026-11-24)

- 작성: OS_EXPANSION 세션. 기준: main `de32ea1`. 브랜치 `claude/os-linux-differences-20261124`. 형식은 `MACOS_DIFFERENCES_2026-11-24.md`와 같습니다.
- 범위: 네이티브 데스크톱(`quantgen_desktop/`)과 그것이 쓰는 `core/`·`tools/`·`packaging/`. 화면 파일은 **읽기만** 했고, 고친 것은 새 도구 `tools/packaging/linux_runtime_report.py`와 그 시험뿐입니다.
- **실측 환경**: 이 컨테이너(Ubuntu 24.04.5, glibc 2.39, 데스크톱 세션·D-Bus 없음)에서 PyInstaller 6.22.3·PyQt6 6.12.0으로 만든 빌드(`claude/os-sale-build-check-20261124`의 `be60b2a`)를 `linux_runtime_report.py`로 검사했습니다. 일반 데스크톱 배포판(GNOME/KDE가 있는 PC)에서는 실행해 보지 않았습니다.

## 1. 표

| # | 영역 | 위치 | 지금 | Linux에서 (실측/문서) | 조치 | 몫 |
|---|---|---|---|---|---|---|
| 1 | 배포 빌드 | `.github/workflows/platform-build.yml` | Windows·macOS·Android 작업만 | **Linux 데스크톱 배포 작업 없음**. Linux는 `runtime-smoke`(offscreen 시험)와 이 세션 빌드에서만 확인 | Linux를 판매 대상으로 할지 먼저 결정 | 소유자 |
| 2 | glibc 최소 버전 | PyInstaller가 빌드 머신의 시스템 라이브러리를 함께 묶음 | — | **실측: ELF 421개 중 35개가 `GLIBC_2.38` 요구**(libX11, libfontconfig, libdbus-1, libcrypto, libcairo, Flet의 flutter 플러그인 등). Ubuntu 22.04(2.35)·Debian 12(2.36)에서는 시작하지 못함 | 지원할 가장 오래된 배포판(예: Ubuntu 22.04 러너)에서 빌드하거나, 시스템 라이브러리를 빼는 묶음 방식 결정 | 소유자·메인 |
| 3 | Qt 화면 플러그인(X11) | `PyQt6/Qt6/plugins/platforms/libqxcb.so` | 시스템 라이브러리에 기댐 | **실측: 8개 없음** — libxkbcommon-x11.so.0, libxcb-cursor.so.0, libxcb-icccm.so.4, libxcb-util.so.1, libxcb-image.so.0, libxcb-keysyms.so.1, libxcb-render-util.so.0, libxcb-xkb.so.1. Qt 6.5부터 X11에는 libxcb-cursor0가 필요하고, 데스크톱 배포판에도 빠진 경우가 있음 | 설치 안내에 `sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxcb-util1`(Debian/Ubuntu) | 소유자(안내) |
| 4 | Qt 화면 플러그인(Wayland) | `libqwayland.so` | — | 실측: 빠진 라이브러리 없음. Wayland 세션에서는 Qt가 이것을 고름 | 없음 | — |
| 5 | 키 보관함 | `core/credentials` → keyring Secret Service(GNOME Keyring)·KWallet | — | **실측: D-Bus 세션이 없으면 keyring이 `fail` 백엔드를 고르고, `keyring_available()` False, `credentials.set()`은 `CredentialStoreUnavailable`**. 판매(public) 빌드는 `.env`를 읽지 않으므로 키를 넣을 곳이 환경변수뿐. SSH·최소 창 관리자·컨테이너가 이 경우 | 키 화면(KEY-5)이 이 오류를 "OS 키 보관함이 없음 — gnome-keyring 또는 KWallet 필요"로 보여 줘야 함. 지금 화면에서 키를 저장하는 곳은 없음 | UI·PAYMENTS |
| 6 | 키 보관함 잠금 | — | — | 로그인 키링이 잠겨 있으면 첫 접근 때 잠금 해제 창이 뜸(데스크톱 환경 몫) | 안내만 | — |
| 7 | 자료 폴더 | `core/app_paths.py` | `$XDG_DATA_HOME/quantgen`, 없으면 `~/.local/share/quantgen` | 새로 만드는 폴더는 0700, 표시 파일. 위쪽 `~/.local/share`는 umask 그대로 | 없음 | — |
| 8 | 자료 폴더 이전 | `_rename_no_replace` | `renameat2(RENAME_NOREPLACE)` | 커널 3.15+, ext4·btrfs·xfs·tmpfs 지원. NFS 같은 일부 파일 시스템은 지원 안 함 → **거부**(복사 대체 없음, 자료 그대로) | 없음(안전한 쪽) | — |
| 9 | Flet 실행 파일이 Qt 빌드에 들어감 | `quantgen_desktop/macro_records.py:67~294`, `narrative_view.py:32`, `market_narrative_language.py:218`, `portfolio.py:135`가 `ui.*`(Flet 화면 모듈)를 import | — | **실측: `_internal/flet_desktop` 64 MB**(Flutter·GTK 플러그인, 2번의 GLIBC_2.38 파일 일부 포함). 모든 OS 빌드에 해당 | 공용 순수 함수를 `ui/`에서 `core/`로 옮기면 spec에서 `flet`·`flet_desktop`을 뺄 수 있음 | UI·메인 |
| 10 | 시스템 라이브러리 중복 | libX11·libfontconfig·libdbus 등이 앱 폴더에 | — | 사용자 PC의 설정 파일 형식과 버전이 다르면 경고(예: fontconfig) 또는 오작동 가능 | 2번 결정과 같이 | 소유자·메인 |
| 11 | 창 아이콘·작업 표시줄 | `app.py` `app_icon()` | QIcon | Wayland(GNOME)는 창 아이콘을 `.desktop` 파일에서 가져옴. `.desktop` 파일과 앱 ID(`QGuiApplication.setDesktopFileName`)가 없어 기본 아이콘 | `.desktop` 파일(packaging)과 `setDesktopFileName("quantgen")`(화면) | UI·OS |
| 12 | 글꼴 | `font_policy.py` | QG Interface(Pretendard OTF)를 앱에 등록 | 한글은 묶은 글꼴로 그려짐. 기호·기타 문자는 시스템 글꼴(fontconfig)에 기댐. 실측 컨테이너 119개 글꼴, selfcheck `qt_offscreen_fonts` ok | 최소 설치 PC는 화면 확인 필요 | 소유자 |
| 13 | 로캘 | — | — | **실측: `LANG`이 없으면(C 로캘) Qt가 "switched to C.UTF-8" 경고를 냄** | 실행기에서 `LANG=C.UTF-8` 기본값 | OS(실행기 생길 때) |
| 14 | 파일 열기 | `macro_records.py:235` `QDesktopServices.openUrl` | Qt 공용 | Linux에서는 `xdg-open`(xdg-utils)에 맡김. 실측 컨테이너에는 없음 → 열리지 않고 조용히 실패 | 설치 안내에 xdg-utils | 소유자(안내) |
| 15 | 파일 잠금 | `gate_ledger.py`, `run_registry_*` | `fcntl.flock` | 로컬 파일 시스템 정상. 홈이 NFS면 잠금이 약함 | 없음 | — |
| 16 | 단축키 | `app.py:340` Ctrl+B 등 | — | Windows와 같음(Meta = Super 키) | 없음 | — |
| 17 | CPU | — | x86_64 빌드만 | aarch64 Linux는 별도 빌드 | 1번 결정과 같이 | 소유자 |
| 18 | 실행기 | 루트 `Start-QUANTGEN-Desktop.cmd`(Windows) | — | Linux 실행기 없음. 소스 실행은 `python3 -m quantgen_desktop` | 판매 대상이 되면 실행기·`.desktop` 파일 | 메인 |

## 2. 고친 것 (이 브랜치)

1. `tools/packaging/linux_runtime_report.py` (새 도구): 빌드된 앱 폴더만 읽어 (가) 묶인 ELF 파일이 요구하는 가장 높은 glibc 버전과 그 파일들, (나) Qt 화면 플러그인(`libqxcb.so`, `libqwayland*.so`)에서 `ldd`가 찾지 못한 라이브러리를 JSON으로 보고합니다. 사용자의 홈·자료 폴더는 읽지 않습니다. `objdump`·`ldd`가 없으면 그렇다고 적고 끝냅니다. 항상 종료 코드 0(보고 도구).

   ```
   python tools/packaging/linux_runtime_report.py dist/QUANTGEN --json linux-runtime.json
   ```

2. `tests/linux_runtime_report_acceptance.py`: objdump·ldd 출력 해석, 빈 폴더, 실제 ELF 하나(`/bin/true` 사본).

## 3. 확인한 것

- 새 시험 4개 통과.
- 위 빌드에 도구 실행: `glibc_required: GLIBC_2.38`(35개 파일), xcb 플러그인 빠진 라이브러리 8개, Wayland 플러그인 0개. 약 2초.
- 키 보관함: keyring 25.x를 새 venv에 설치해 `keyring.get_keyring()` → `keyring.backends.fail.Keyring`(priority 0), Secret Service는 "DBUS_SESSION_BUS_ADDRESS is unset"으로 사용 불가, `core.credentials.keyring_available()` False, `set("FMP_API_KEY", ...)` → `CredentialStoreUnavailable`(아무 저장소에도 쓰지 않음).

## 4. 요청 목록

- **소유자·메인**: Linux를 판매 대상으로 할지(1번). 한다면 빌드 기준 배포판(2·10번)과 CPU(17번).
- **UI(소유자 경유)**: 키 화면에서 `CredentialStoreUnavailable` 안내(5번), `setDesktopFileName`(11번), `ui.*`에서 쓰는 순수 함수를 `core/`로(9번, 메인과 같이).
- **OS(판매 대상이 되면)**: `.desktop` 파일·실행기(`LANG` 기본값 포함)를 `packaging/`에, `platform-build.yml`에 Linux 작업과 이 도구 실행.
