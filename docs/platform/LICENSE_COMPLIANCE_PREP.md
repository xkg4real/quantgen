# 배포 라이선스·서명 준비 (OS-P0-b/3, 2026-11-17)

> **법률 자문이 아닙니다.** 이 문서는 패키지 메타데이터와 빌드 결과를 실측한 사실과, 변호사에게 물을 질문을 정리한 것입니다. 판매 전에 반드시 변호사 확인이 필요합니다.

- 작성: OS_EXPANSION 세션. 근거 커밋: 작업 브랜치 `claude/os-prep-20261117`의 `8097ca5`(고지 생성기·selfcheck), `c12643b`(chardet 처리).
- 관련 파일: `tools/packaging/third_party_notices.py`, `packaging/licenses/LGPL-3.0.txt`·`GPL-3.0.txt`(FSF 원문), `packaging/quantgen_desktop.spec`, `packaging/selfcheck.py`.

## 1. 실측한 사실

| 항목 | 값 (2026-11-17) | 근거 |
|---|---|---|
| PySide6-Essentials 6.12.0, shiboken6 6.12.0 | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | 휠 METADATA |
| PyQt6 6.12.0 | `GPL-3.0-only` (Riverbank 상용 라이선스 별도) | 휠 METADATA |
| PyQt6-Qt6 6.12.0 (Qt 라이브러리) | LGPL v3 | 휠 METADATA |
| PySide6 휠 안의 LGPL 원문 | **없음** (Windows 휠은 `LicenseRef-Qt-Commercial.txt`만, macOS 휠은 라이선스 파일 0개) | 휠 파일 목록 |
| PySide6 6.12 macOS 최소 버전 | macOS 14 (PyQt6 6.12.1도 macOS 14) — 전환해도 지원 범위 같음 | PyPI 파일명 |
| Qt 라이브러리 형태 | Windows `Qt6Core.dll` 등, macOS `QtCore.framework`, Linux `libQt6Core.so.6` — 모두 **별도 공유 라이브러리** | 휠 파일 목록, Linux 빌드 실측 |
| 빌드에 들어간 배포 패키지 | PyQt6 빌드 96개, PySide6 빌드 95개 | `THIRD_PARTY_NOTICES.txt` |
| copyleft·미표기 (PySide6 빌드) | PySide6/shiboken6 (LGPL), **chardet 5.2.0 (LGPL)**, certifi·tqdm (MPL-2.0), peewee (메타데이터 미표기, 원문은 MIT) | 같은 파일 |

## 2. 이미 구현한 것 (빌드에 자동으로 들어감)

1. **고지 파일**: 빌드할 때 PyInstaller가 실제로 넣은 모듈에서 배포 패키지를 찾아, 이름·버전·라이선스와 각 패키지가 가진 라이선스 원문을 `licenses/THIRD_PARTY_NOTICES.txt`로 넣습니다. Qt for Python이 들어 있으면 LGPL-3.0·GPL-3.0 원문과 "Qt 라이브러리 교체 방법·소스 위치" 안내를 덧붙입니다(PySide6 휠에 원문이 없기 때문).
2. **교체 가능성**: onedir 빌드라 Qt 라이브러리가 별도 파일로 남습니다. `--selfcheck`가 Qt Core 라이브러리가 아카이브 밖의 별도 파일인지 확인합니다. Linux에서는 두 바인딩 모두 통과했습니다.
3. **chardet(LGPL 순수 파이썬)**: 원래는 PYZ 압축 아카이브 안에 들어가 사용자가 바꿀 수 없었습니다. 이제 `module_collection_mode`로 `.py` 파일 43개를 앱 폴더에 그대로 둡니다(`c12643b`, 다시 빌드한 뒤 selfcheck 10/10 통과).
4. **onefile 금지**: 한 파일 빌드는 라이브러리를 임시 폴더에 풀기 때문에 교체가 어렵습니다. 그래서 spec은 onedir만 만듭니다.

## 3. 변호사에게 물을 것

1. 앱을 판매할 때 LGPL-3.0 4절(Combined Works) 의무가 위 2절로 충족되는지. 특히 다음 둘입니다.
   - 4(d)(1): 공유 라이브러리로 두는 것.
   - 6절(GPL-3.0 소스 제공): Qt 소스를 링크로 안내하는 것으로 충분한지, 아니면 우리가 직접 사본을 호스팅하거나 서면 제공 약속을 해야 하는지.
2. EULA 조항. LGPL 4절은 "수정과 그 수정의 디버깅을 위한 역공학"을 막지 않아야 한다고 요구합니다. 우리 EULA의 역공학 금지 조항을 Qt·chardet 부분에 대해서는 예외로 둬야 하는지.
3. 라이선스 키, 계정, 서명 검증(D7-G)이 사용자의 Qt 라이브러리 교체를 사실상 막는 효과가 있는지. 막는다면 LGPL 4(e) "Installation Information" 대상인지. 데스크톱은 보통 "User Product"가 아니지만 확인이 필요합니다.
4. PyQt6로 판매하는 경우. PyQt6 자체가 GPL-3.0이므로, 소스를 공개하지 않는 판매에는 Riverbank 상용 라이선스가 필요하다고 보는지. D9에서 PySide6로 바꾸는 이유가 바로 이 점입니다.
5. MPL-2.0인 certifi와 tqdm: 수정하지 않고 넣었을 때 고지만으로 충분한지.

## 4. macOS 서명·공증 설계 (아직 실행 안 함, Apple 계정 필요)

| 단계 | 지금 | 필요한 것 (소유자) |
|---|---|---|
| 서명 | ad-hoc(`codesign --sign -`). Gatekeeper가 경고함 | Apple Developer Program 가입(연 99달러, 법인 설립 뒤 법인 명의 권장)과 "Developer ID Application" 인증서 |
| hardened runtime | 없음 | PyInstaller spec의 `codesign_identity`·`entitlements_file`. Python 앱은 보통 `com.apple.security.cs.allow-unsigned-executable-memory`와 `disable-library-validation`을 검토(실측 필요) |
| 공증 | 없음 | `xcrun notarytool submit QUANTGEN.zip --wait` 후 `xcrun stapler staple QUANTGEN.app` |
| CI 비밀값 | 없음 | GitHub 저장소 비밀값: 인증서 p12(base64), p12 암호, App Store Connect API 키(ID·발급자·p8). 이름만 정하고 값은 소유자가 넣음 |

- 워크플로에서는 비밀값이 있을 때만 서명·공증 단계를 실행하는 조건 방식으로 넣을 예정입니다. 지금은 비밀값이 없으므로 넣지 않았습니다.
- Windows: SmartScreen 경고를 줄이려면 Authenticode 코드서명 인증서(OV 또는 EV)가 필요합니다. 법인 설립 뒤 진행합니다.

## 5. iOS·Android

- 모바일 앱은 Flet(Flutter + Python)이고 Qt를 쓰지 않습니다. 그래서 **iOS 정적 링크 문제(Qt for iOS는 정적 라이브러리라 LGPL 교체 의무를 지키기 어려움)는 지금 계획에서는 생기지 않습니다.** 모바일에 Qt를 쓰지 않는다는 방침을 유지하는 것이 가장 단순합니다.
- 모바일 묶음(`stage.py --profile mobile`)도 같은 고지 생성기로 고지를 만들 수 있습니다. 다만 Android 빌드는 아직 실행하지 않았습니다(6절).

## 6. Android 빌드를 여기서 못 한 이유 (실측)

이 클라우드 컨테이너의 네트워크 정책은 `pypi.flet.dev`(Flet 모바일 휠), `dl.google.com`(Android SDK), `www.gnu.org`를 거부합니다(프록시 403). PyPI의 numpy 2.5.5, pandas 3.1.1, PyYAML 6.0.3에는 Android/iOS 휠이 없습니다. 그래서 Android 빌드는 계획대로 GitHub Actions(`platform-build.yml`의 `android` 입력)나 소유자 PC에서 합니다. 이 컨테이너에서 하려면 위 호스트들을 환경 허용 목록에 추가해야 하고, 그것은 소유자 승인 사항입니다.
