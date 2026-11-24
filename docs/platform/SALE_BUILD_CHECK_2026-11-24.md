# 판매 빌드 구성 점검 (15-7, 2026-11-24)

> **법률 자문이 아닙니다.** 아래 라이선스 항목은 빌드 결과를 실측한 사실과 질문입니다. 판매 전 변호사 확인이 필요합니다(`docs/platform/LICENSE_COMPLIANCE_PREP.md` 3절).

- 작성: OS_EXPANSION 세션. 기준: main `de32ea1`. 브랜치 `claude/os-sale-build-check-20261124`.
- 범위: 데스크톱 판매 빌드(`packaging/quantgen_desktop.spec`, `packaging/selfcheck.py`)와 묶음 허용 목록(`tools/packaging/stage.py`, spec·wheel·모바일 묶음이 같이 씀). 고친 파일은 이 세 개뿐입니다.
- 실측: 이 컨테이너(Linux)에서 PyQt6 6.12.0, PyInstaller 6.22.3으로 **main 그대로**와 **이 브랜치**를 각각 빌드하고 `--selfcheck`를 실행했습니다.

## 1. 점검표

| # | 항목 | main `de32ea1` (실측) | 이 브랜치 (실측) | 어디에 반영 |
|---|---|---|---|---|
| 1 | flet-cli 전용 패키지 | `flet-cli` 배포가 들어감. `chardet`(LGPL) `.py` 43개가 앱 폴더에 있음 | `flet_cli`·`chardet`·`text_unidecode`·`slugify`·`cookiecutter`·`binaryornot` 모두 없음 | spec `FLET_CLI_ONLY`를 `excludes`에 넣음 |
| 2 | 그 근거 | — | 설치 의존 관계: `flet[all]` → `flet-cli` → `cookiecutter` → `python-slugify` → `text-unidecode`(Artistic), `binaryornot`·`flet-cli` → `chardet`(LGPL). `import flet`은 `flet_cli`를 불러오지 않음. `requests`는 chardet이 없으면 `charset-normalizer`(MIT)를 씀 | — |
| 3 | 고지 누락 | **chardet 파일은 들어갔는데 `THIRD_PARTY_NOTICES.txt`에 chardet이 없음**: `.py`로 두는 패키지는 `a.pure`에서 빠져 고지 수집에서 빠졌음 | chardet 자체가 빠져 해소. 앞으로 `.py`로 두는 패키지는 고지에도 들어가게 `collected`에 더함 | spec `collected \|= set(LGPL_PURE_PYTHON)` |
| 4 | 예전 NEXTGEN 로고 | `assets/nextgen_logo_dark.png`·`_light.png`가 들어감. 앱 코드(`quantgen_desktop`·`core`·`ui`·`main.py`·`mobile`)에서 쓰는 곳 없음 | 없음 | `stage.py` `RETIRED_ASSETS`(spec·wheel·모바일 묶음 공통) |
| 5 | 배포 패키지 수 | 75 | 74 (flet-cli 하나 줄어듦. chardet은 3번 이유로 원래 목록에 없었음) | 빌드 로그 "third-party notices for N distributions" |
| 6 | 자체 점검 | 기존 12항목 | `sale_build_contents` 추가: 위 패키지와 로고가 없을 것, 데이터 소스 프로필을 기록. 실측 `ok`, `gateway_profile: "personal"` | `packaging/selfcheck.py` |

## 2. PySide6 LGPL 점검 (OS-F1 전환 뒤 판매 빌드)

| 요건 | 지금 | 근거 |
|---|---|---|
| 동적 링크(공유 라이브러리) | onedir 빌드만 만듦(onefile 금지). Qt는 별도 파일: Windows `Qt6*.dll`, macOS `*.framework`, Linux `libQt6*.so*` | spec(onedir), selfcheck `licence_notices_and_separate_qt`가 Qt Core가 아카이브 밖 파일인지 확인 |
| 교체 가능성 | Qt 라이브러리·PySide6 모듈 파일을 사용자가 바꿀 수 있음. LGPL 순수 파이썬 패키지는 `.py`로 둠(지금은 해당 없음: chardet 제외) | spec `module_collection_mode`, `LGPL_PURE_PYTHON` |
| 고지 | 빌드에 실제로 들어간 패키지의 이름·버전·라이선스·원문을 `licenses/THIRD_PARTY_NOTICES.txt`로, PySide6가 있으면 LGPL-3.0·GPL-3.0 원문과 교체·소스 안내 추가 | `tools/packaging/third_party_notices.py`, selfcheck `lgpl_text` |
| macOS 서명 | Qt framework를 바꾸면 앱 서명이 깨짐 → 사용자가 ad-hoc 재서명 필요할 수 있음 | 변호사 질문 3(LICENSE_COMPLIANCE_PREP) |
| 남은 것 | 소스 제공 방식(링크로 충분한지), EULA 역공학 예외, MPL(certifi·tqdm) 고지 | LICENSE_COMPLIANCE_PREP 3절. 이 브랜치에서 바꾸지 않음 |

## 3. 표시권 없는 데이터 소스를 판매판에서 끄는 스위치

| 항목 | 지금 |
|---|---|
| 스위치 | `core/gateway/routes.json`의 `commercial` 프로필: `yahoo`, `fmp`, `gs_marquee`가 `off`. `personal`에서는 켜짐 |
| 누가 프로필을 고르나 | `core/app_identity.GATEWAY_PROFILE = "personal"` **코드 상수**. spec·rthook·`QG_BUILD_CHANNEL`과 연결이 없음 |
| 그 결과 | **판매(public) 빌드도 personal 프로필로 나감** → yahoo·fmp·gs_marquee가 켜진 채 판매될 수 있음. 이 브랜치의 selfcheck가 `gateway_profile`을 기록해 빌드마다 보이게 했음(실측 `"personal"`) |
| 고칠 곳 | `core/`(게이트웨이·앱 정보 소유 세션): `build_channel()`처럼 `core._build_info.GATEWAY_PROFILE`을 읽게 하고, spec이 `QG_GATEWAY_PROFILE`을 rthook에 넣음. 판매 빌드 규칙(public이면 commercial이어야 하는지)과 그 날짜는 소유자·메인 결정. **이 세션 범위(packaging·tools/packaging) 밖이라 요청으로 올림** |
| 표시권 검토 | `core/research/display_rights.json`: 79행 중 `rights_verify` 36, `rights_conditional` 34, `rights_replace` 9, `publication_authorization: false`. 이 기록은 화면 설명용이고 경로를 끄지 않음 |

## 4. 확인한 검사

- `tests.packaging_policy_acceptance`, `tests.third_party_notices_acceptance`, `tests.app_identity_acceptance` 통과.
- 이 브랜치 빌드(Linux, PyQt6; `collected |= set(LGPL_PURE_PYTHON)` 한 줄은 빌드 뒤에 더함 — 지금 목록이 비어 있어 결과에 영향 없음): PyInstaller rc 0, `--selfcheck` rc 0, 13항목 모두 ok(`sale_build_contents` 포함). `_internal`에 위 6개 패키지·로고 없음.
- main 빌드(같은 조건): `_internal/chardet` 43개 파일, 로고 2개, 고지에 chardet 없음 — 1표의 "main" 열.
- Windows·macOS 빌드와 PySide6 빌드는 `platform-build.yml`에서 확인(실행하지 않음).
