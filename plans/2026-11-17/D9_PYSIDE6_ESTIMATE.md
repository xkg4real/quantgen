# D9. PySide6 전환 시간 추정 — F 뒤에 하면 24시간을 넘나

- 작성: 2026-11-17 (KST). 읽기 전용 조사. 저장소·GitHub·Notion·설정은 바꾸지 않았습니다.
- 기준: `origin/main` `e01e152` (PR #120, 2026-11-14), UI 브랜치 `origin/claude/friendly-bardeen-r6xe8f` `212f0dd` (2026-11-17 10:10Z).
- 실측: main을 임시 폴더(스크래치)에 두 벌 풀어, 한 벌은 그대로 PyQt6 6.12.0으로, 한 벌은 간단한 변환 스크립트 뒤 PySide6-Essentials 6.12.0으로 CI의 Qt 검사 17단계를 Linux 오프스크린에서 돌렸습니다 (4절).
- 표시: **(미검증)** = 직접 확인 못 함. **(추정)** = 계산·판단 값.

> 소유자 지시 (11-17): "만약 개발이 F까지 완료된 뒤 Pyside6 전환 시 전환에 소요되는 예상 시간이 24시간을 초과한다면 지금 진행할 것. 그게 아니라면 권장대로 승인"

---

## 0. 결론

| 질문 | 답 |
|---|---|
| F 뒤 전환에 걸리는 시간 | **예상 약 30시간** (낮음 약 15 / 높음 약 57). 작업 + CI 대기 + 소유자 Windows 확인, 밤·대기 제외 **(추정)** |
| 24시간과 비교 | **넘습니다.** 단, 셈에 CI 대기(약 4.8시간)와 소유자 Windows 확인(약 2시간)을 넣었을 때입니다. 이 둘을 빼고 사람·에이전트가 손대는 시간만 세면 예상 약 23.5시간 (범위 약 11~45)으로 24시간 바로 아래입니다 (5절). 범위가 넓고 위쪽 위험(세그폴트, 원인 미상 실패)이 커서 판정은 바꾸지 않았지만, 소유자께서 "작업 시간만"을 뜻하셨다면 답이 달라질 수 있습니다. |
| 소유자 규칙에 따른 답 | **지금 진행.** |
| 왜 예전 추정(약 2.5~3.5일)보다 커졌나 | 실제로 바꿔 돌려 보니, PySide6에는 앱이 쓰는 `QChar`와 글꼴 대체 등록 함수가 없어 처음엔 앱이 뜨지 않았고, 고친 뒤에도 **세그폴트 1건, 바인딩 때문에 새로 실패한 테스트 15개, '이미 지워진 객체' 오류 223줄**이 나왔습니다 (4절). |
| 권하는 "지금" | **작업은 오늘 시작하고, main 전환 병합은 F21 바로 뒤 첫 자리.** 두 바인딩에서 다 되는 수정은 지금 UI 브랜치에 넣어 F21 뒤에 남는 일을 약 12~20시간으로 줄입니다. P3·F는 늦추지 않습니다 (7절 나안). |
| main까지 지금 넣으면 | P3·F21이 약 4~5 작업일 늦어지고, UI 세션이 멈추고, 살아 있는 UI 브랜치(51파일)와 충돌하고, 소유자 PC의 F 환경에 PySide6를 새로 깔아야 합니다 (6절). 소유자가 "가"라고 하시면 이렇게 합니다. |

신호·슬롯 이름, 열거형, `exec`, `QFileDialog`, 고해상도 설정은 자동 치환이나 무수정으로 됩니다. 시간을 잡아먹는 것은 글꼴, 객체 수명, 원인 미상 실패, CI 왕복(회당 약 95분)입니다. PySide6 라이선스(LGPL v3)의 판매 조건은 변호사 확인이 필요하고, 이 문서는 법률 자문이 아닙니다.

---

## 1. 지금 PyQt6를 얼마나 쓰나 (origin/main `e01e152`)

명령: `git grep -l PyQt6 origin/main -- quantgen_desktop core ui tests tools main.py pyproject.toml requirements.txt .github` 등.

| 항목 | 개수 | 비고 |
|---|---|---|
| PyQt6가 나오는 파일 | 133 | `quantgen_desktop` 55, `tests` 73, `tools` 1, `core` 1 (문구), `pyproject.toml`, `runtime-smoke.yml`, `Start-QUANTGEN-Desktop.cmd` |
| 그중 PyQt6를 import하는 파일 | 127 | 데스크톱 54, 테스트 72, `tools/packaging/smoke_desktop.py` 1 |
| PyQt6 import 줄 / 전체 PyQt6 줄 | 333 / 353 | `main.py`, `ui/`(Flet), `core/` 계산 코드, `requirements.txt`에는 import 0건 |
| `quantgen_desktop` 크기 | 83개 .py, 29,927줄 | 10-31 4,584줄 → 11-14 29,927줄 (2주에 6.5배) |
| `pyqtSignal` | 117줄 / 22파일 | 이름만 `Signal`로 (자동) |
| `pyqtSlot` | 62줄 / 12파일 (데코레이터 50개) | 이름만 `Slot`으로 (자동) |
| `pyqtProperty` | 0 | — |
| `sip` | 14줄 / 5파일 (`sip.isdeleted` 7, `sip.delete` 1) | `stock_detail.py`, `stock_detail_side.py`, 테스트 3개 (`qt_fixture_cleanup.py` 포함) |
| `uic`, `.ui` 파일 | 0 | — |
| 열거형 `Qt.X.Y` 완전 표기 | 649줄 / 57파일 | PyQt6는 원래 완전 표기만 됨 → PySide6도 그대로 받음 (바꿀 것 없음) |
| `int(Qt...)` 변환, `.value` | 8줄 / 2줄 | PySide6 6.12에서 그대로 동작 (실측) |
| `exec_()` / `exec()` | 0 / 2 (`app.exec()`, `menu.exec()`) | PySide6도 `exec()` 지원 (실측: `exec_`도 남아 있음) |
| `QAction` | 테스트 1곳 (`QtGui`에서 import) | Qt6 위치 그대로, 문제 없음 |
| `QShortcut` | 2파일 | 문제 없음 |
| QtWebEngine / QtCharts | 0 / 0 (`QtWebEngineWidgets`는 "안 불러온다"는 검사 1줄뿐) | Essentials에 없어도 됨 |
| QtSvg / QtSvgWidgets | `QSvgWidget` 4파일 | PySide6-Essentials 6.12.0에 있음 (실측) |
| QtTest (`QTest`) | 31파일, 193줄 | Essentials에 있음 (실측) |
| 사용자 정의 `QStyle`/`QProxyStyle` 하위 클래스 | 0 | `QStyle.PixelMetric`·`drawControl` 사용 5줄뿐 |
| 스레드 | `QThreadPool`+`QRunnable` 1파일 (`jobs.py`), `QThread`는 테스트 3개에서 `currentThread()`만 | 구조 변경 없음 |
| `QFileDialog` 저장 대화상자 | 5곳, 모두 `(경로, 필터)` 튜플로 받음 | 두 바인딩 모두 튜플 (스텁 확인) |
| 고해상도(DPI) 설정 | `AA_*`·`setHighDpi*` 0건, `devicePixelRatioF` 1곳 | Qt6는 항상 고해상도. 같은 Qt 6.12라 그대로 |
| 글꼴 | `QFontDatabase` 19줄/5파일, 앱 전체 대체 글꼴 등록은 `font_policy.py` 한 곳 | **PySide6에 해당 API가 없음 (3절)** |
| `QSettings` | 32줄/14파일 | 저장 위치·키 같음 (Windows 실제 값 유지는 미검증) |
| 패키징 | PyInstaller spec **없음**. `pyproject.toml`의 `desktop = ["PyQt6==6.12.0"]`, `[project.gui-scripts] quantgen-desktop = "quantgen_desktop.app:main"`, `Start-QUANTGEN-Desktop.cmd`의 `import PyQt6` 확인 | 3곳 수정 |
| CI | `runtime-smoke.yml` 100행 `pip install "PyQt6==6.12.0"` 한 단계, 그 뒤 Qt 검사 12단계 (unittest 명령 17개, 오프스크린) | 설치 줄 1개 수정 |
| PyQt6를 찾는 테스트 | `find_spec("PyQt6")` 5파일, 금지 import 목록에 'PyQt6' 2파일 | 자동 치환 대상 |
| 문서 | `docs` 45파일 57줄 (준수 문서 `docs/compliance` 11파일, `docs/product` 33파일) + `README.md` | 준수 문서 11개와 `release-profile.json`은 고쳐야 함 (라이선스) |

## 2. 살아 있는 UI 브랜치 (`claude/friendly-bardeen-r6xe8f`)

| 항목 | 값 |
|---|---|
| main 대비 | 3커밋 (`da0ea20` 09:18Z, `263437c` 10:00Z, `212f0dd` 10:10Z), 51파일, +5,682/−259. PR 없음 |
| `quantgen_desktop` | 85개 .py, 32,231줄 (main보다 +2,304줄) |
| PyQt6 import 파일 | 132 (main 127 → +5: `market_hub.py` 969줄, `page_kit.py` 896줄, 테스트 3개) |
| 늘어난 사용 | `pyqtSignal` +13, `pyqtSlot` +3, 열거형 줄 +40. `sip`·`int(Qt…)`·`findChildren((…))`는 그대로 |
| main 변환과 겹치는 파일 | PyQt6 줄이 있고 UI 브랜치도 고친 파일 12개 (`app.py`, `form_layout.py`, `indicator_guide.py`, `indicator_picker.py`, `market_summary.py`, `stock_detail_style.py`, `tools.py`, 테스트 4개, `runtime-smoke.yml`) + PyQt6 문구가 있는 `docs/compliance/FACTS.md` + PyQt6로 새로 쓴 파일 5개 |
| 앞으로 | 시안 7개 (`draft_01_home` … `draft_07_system`)가 승인 뒤 화면 구현으로 들어옴. 11-16 항목(마이페이지, 홈 지표, API 키 화면), D11(정식 계정) 화면도 여기에 붙음 |

결론: UI 브랜치는 새 종류의 PyQt6 기능을 쓰지 않습니다. 같은 패턴의 코드가 늘 뿐입니다. 그래서 변환 도구가 하는 일은 같고, 늘어나는 것은 "실행해 봐야 드러나는 동작 차이"의 개수입니다.

## 3. 알려진 차이와 이 저장소에서 나오는지

| 차이 | PyQt6 | PySide6 6.12 | 여기서 | 확인 |
|---|---|---|---|---|
| 신호·슬롯 이름 | `pyqtSignal`, `pyqtSlot`, `pyqtProperty` | `Signal`, `Slot`, `Property` | 179줄, 자동 치환 | 실측 |
| 열거형 | 완전 표기만 (`Qt.AlignmentFlag.AlignCenter`) | 완전 표기와 짧은 표기 모두. 파이썬 `enum` (`IntFlag`·`IntEnum`) | 649줄 그대로. `int(...)` 8줄, `.value` 2줄도 그대로 동작 | 실측 |
| `QVariant` | 쓰지 않음 | 쓰지 않음 | 0건 | git grep |
| 삭제 확인 | `sip.isdeleted(x)`, `sip.delete(x)` | `not shiboken6.isValid(x)`, `shiboken6.delete(x)` | 8곳 (앱 2파일, 테스트 3파일) | 실측: `shiboken6`에 둘 다 있음 |
| `exec` | `exec()` | `exec()` (옛 `exec_()`도 남음) | 2곳, 수정 없음 | 실측 |
| `QFileDialog` 반환 | `(경로, 필터)` | `(경로, 필터)` | 5곳, 수정 없음 | 두 패키지의 `.pyi` |
| 고해상도 | Qt6 기본 | 같음 (같은 Qt 6.12) | 설정 코드 없음 | git grep. 실제 Windows 배율 표시는 소유자 확인 필요 |
| 글꼴 대체 등록 | `QFontDatabase.addApplicationFallbackFontFamily(QChar.Script…)` 있음 | **`QChar`도, 이 함수 4개도 없음** | `font_policy.py` 50~53행 (한글·그리스 문자 등 대체 글꼴) | 실측: `PySide6.QtGui.QFontDatabase`에 'fallback' 함수 0개, `from PySide6.QtCore import QChar` ImportError |
| `findChildren`에 타입 튜플 | 됨 | **TypeError** | 테스트 1곳 (`desktop_operation_fixes_acceptance.py` 119행) | 실측 |
| 콤보 항목 데이터로 str Enum | `currentData()`가 Enum 그대로 | **평범한 str로 바뀜** | `paper.py` `combo()` (모의매매 규칙의 Side·Comparator 등) | 실측 |
| 파이썬 예약어 이름 | `QTextDocument.print()` | `print_()` | `stock_report.py` 164행 | 시범 변환에서 실패로 드러남 |
| `winId()` | `sip.voidptr` | `int` | `int(window.winId())`로 써서 문제 없음 | 실측 |
| 슬롯 안 예외 | **앱 중단** (`qFatal`) | 출력하고 계속 | 테스트가 지금은 "중단"으로 오류를 잡음 → PySide6에선 오류가 조용히 지나갈 수 있음. 테스트 쪽 예외 훅 필요 | 실측 (같은 스크립트로 두 바인딩 비교) |
| 연결 안 된 슬롯 끊기 | TypeError | 경고만 (RuntimeWarning) | `except (TypeError, RuntimeError)`로 이미 감쌈 | 실측 (두 바인딩) |
| 객체 수명 (파이썬 쪽이 먼저 지워짐) | — | "Internal C++ object … already deleted" | 시범에서 여러 번 나옴 (4절) | 실측 |
| 라이선스 | GPL v3 또는 상용 | LGPL v3 | 준수 문서 11개, `release-profile.json` `QG-RIGHTS-003` | 문서. **법률 자문 아님** |

## 4. 시범 변환 결과 (임시 복사본, Linux, 오프스크린)

**방법.** `git archive origin/main`으로 앱·테스트를 스크래치 폴더에 두 벌 풀었습니다 (`.env`, `*.jsonl`, `holdout`, `frozen` 제외, `docs/` 안 넣음). 한 벌은 그대로 PyQt6 6.12.0, 다른 한 벌은 간이 변환 스크립트(`PyQt6→PySide6`, `pyqtSignal→Signal`, `pyqtSlot→Slot`, `sip→shiboken6`; 130개 파일, 치환 531곳) 뒤 PySide6-Essentials 6.12.0. 첫 실행에서 `QChar` ImportError가 263건 나와 거의 모든 Qt 테스트가 시작도 못 했기 때문에, PySide6 쪽만 `font_policy.py`의 대체 글꼴 등록을 건너뛰게 한 줄 고쳤습니다. 그다음 `runtime-smoke.yml`의 Qt 검사 12단계에 든 unittest 명령 17개(`-f`만 뺌, 아래에서 '단계')를 같은 순서로 돌렸습니다. Linux, Python 3.13.17, `QT_QPA_PLATFORM=offscreen`.

**결과 (같은 테스트를 두 바인딩으로).**

| 구분 | PyQt6 (기준) | PySide6 (변환 뒤) |
|---|---|---|
| 처음 실행 | 정상 | **`QChar` ImportError 263건**, 거의 모든 Qt 테스트가 시작 전에 실패 → 글꼴 줄을 고친 뒤에야 실행됨 (이 첫 실행 로그는 보관하지 않았습니다. 아래 수치는 모두 글꼴 줄을 고친 뒤의 `f2/trial/log_*`에서 나옴) |
| 단계 결과 | 17단계 중 13단계 통과. 실패 3단계는 바인딩과 무관 (아래 줄). 12단계는 108개 통과 뒤 한 테스트에서 멈춰 25분 제한에 걸림 (원인 미검증, 네트워크 대기로 보임) | 17단계 중 10단계 실패. 그중 12단계는 17번째 테스트에서 **세그폴트(rc 139)로 죽음** |
| 바인딩 때문에 새로 실패한 테스트 | — | **15개** (아래 표). 세그폴트로 그 단계(약 175개 테스트)의 나머지 약 160개는 실행조차 안 됨 |
| "이미 지워진 C++ 객체" 오류 출력 | 0 | **223줄** (대부분 `localization.py` 130행의 지연 호출). 지금은 테스트를 실패시키지 않고 출력만 됨 |
| 처리 안 된 예외 Traceback (로그에서 줄 첫머리 `Traceback` 수) | 7 (11단계 5, 14단계 1, 17단계 1) | 86 |
| 두 쪽이 똑같이 실패 | 11단계 5개 (시범 폴더에 `results/` 등이 없음), 14단계 '봉' 1개 (main의 이미 알려진 실패, PR121이 고침), 17단계 1개 (`docs/`를 안 넣음) | 같음 → 바인딩과 무관, 제외 |

**바인딩 때문에 새로 생긴 실패, 원인별로 묶음 (11묶음, 테스트 15개).**

| # | 원인 | 드러난 곳 | 고치기 | 난이도 |
|---|---|---|---|---|
| 1 | `QTextDocument.print` → `print_` | `stock_report.py` 164행 (보내기 테스트 1개, 두 단계에서 실패) | 한 줄 | 쉬움 |
| 2 | `findChildren((A, B))` 튜플 불가 | `desktop_operation_fixes_acceptance.py` 119행 | 한 줄 | 쉬움 |
| 3 | `QObject.receivers(바운드 신호)` 불가 | `stock_detail.py` 1470행 `_open` → 종목 화면 테스트 4개 (`desktop_stock_detail_acceptance`; 그중 2개는 "다른 종목이 열림"으로 드러남) | 연결 여부를 직접 기록 | 쉬움 |
| 4 | 콤보 항목 데이터의 str Enum이 str로 바뀜 | `paper.py` `combo()` → 모의매매 규칙 3개 테스트 (`'str' object has no attribute 'value'`) | `Side(value)` 식으로 되돌림 | 쉬움 (주문 쪽이라 확인 꼼꼼히) |
| 5 | QObject가 해시 안 됨 (`QPointingDevice`) | `market_menu.py` 203행 `watched in self.roots` → Ctrl+휠 확대 테스트 | 집합 대신 `id()`·isinstance 먼저 | 중간 (비슷한 이벤트 필터 17개 점검) |
| 6 | 창이 지워진 뒤 지연 호출 | `localization.py` 130행 등, 223줄 | 수신 객체 유효성 확인 | 중간 |
| 7 | 슬롯 안 예외 정책 차이 | 전체 (PyQt6는 중단, PySide6는 계속) | 테스트에 예외 훅 → 6번 같은 숨은 오류가 실패로 드러남 | 중간 |
| 8 | `QChar` 없음: 앱 대체 글꼴 등록 함수 4개 없음, `QRawFont.supportsCharacter`에 문자 전달 실패 | `font_policy.py` 50~53행, 글꼴 '×' 기호 테스트 | 글꼴 정책 다시 설계 + Windows 눈 확인 | 어려움 |
| 9 | **세그폴트** | `watchlist.py` 805행 (`setItemDelegateForColumn`, 창 만들기) | 객체 소유권 추적, 참조 유지 | 어려움 |
| 10 | 이벤트 필터 연쇄 속 `TypeError` ("`_loaded()` takes 2 positional arguments but 3 were given") | `market_destinations.py`·`market_menu.py`·`reading_panel.py` 연쇄 → 작업 공간 읽기 1개. 시장 검색·진행형 차트 2개(선택한 종목·차트가 끝내 안 열림)도 같은 원인으로 보임 (미검증) | 원인 미상 (간단한 재현은 실패) | 어려움 |
| 11 | AI 해설 미리보기 검사 실패 | `desktop_commentary_acceptance.py` 189행 | 원인 미상 | 중간 |

**이 시범이 말해 주는 것.** 이름 바꾸기만으로는 끝나지 않습니다. 처음엔 앱이 아예 뜨지 않고(8번), 고친 뒤에도 수명·소유권 문제(6·9번)와 원인 미상 실패(10·11번)가 남습니다. 세그폴트 뒤 못 돈 약 160개 테스트와 Windows 전용 검사에서 더 나올 수 있습니다. 반대로, 신호·슬롯·열거형·`sip`·파일 대화상자·DPI 쪽은 자동 치환으로 충분했습니다.

로컬 Linux 전체 Qt 검사 1회는 이 컴퓨터(4코어)에서 PyQt6 약 78분(12단계를 25분에서 끊은 값), PySide6 약 53분(세그폴트로 일부를 건너뛴 값)이었습니다. 두 실행을 동시에 돌려서 하나만 돌릴 때보다 느렸을 수 있습니다.

## 5. F 뒤 전환 시간 추정

**무엇을 셌나.** F21 뒤 전환 PR 하나(계획의 OS-F1, 대기열 11번)를 시작해서 main에 병합할 때까지, 사람·에이전트가 손대는 시간 + CI를 기다리는 시간 + 소유자 Windows 확인 시간. 밤과 소유자 답을 기다리는 시간은 넣지 않았습니다. 변환 도구(OS-P0-a)는 F 전에 이미 있다고 봤습니다 (그 제작 시간은 넣지 않음).

**F 때의 코드 (추정).** 그때는 UI PR(지금 +2,304줄)과 시안 7개 화면, 11-16 앱 항목, D11 계정 화면이 들어간 뒤입니다. 데스크톱 코드는 지금 29,927줄에서 약 35,000~45,000줄로 봅니다. 4절의 동작 차이 수정 시간에 1.0 (낮음) / 1.2 (예상) / 1.4 (높음)을 곱했습니다. 이름 바꾸기는 코드 양과 거의 무관합니다.

| 단계 | 낮음 | 예상 | 높음 | 근거 |
|---|---|---|---|---|
| 1. 도구 실행, diff 검토 (약 140개 파일) | 0.5 | 1 | 2 | 자동 치환 531곳 (4절) |
| 2. 쉬운 차이 (4절 1~4번, `sip`, 'PyQt6 네이티브' 문구 3곳) | 1 | 1.5 | 2 | 한두 줄씩 |
| 3. 글꼴 대체 다시 설계 (8번) | 1.5 | 3 | 5 | PySide6에 함수 자체가 없음. 한글·숫자·기호 표시가 걸림 |
| 4. 수명·소유권·예외 정책 (5·6·7·9번) | 3 | 6 | 11 | 세그폴트 1, 지연 호출 오류 223줄, 이벤트 필터 17개 점검 |
| 5. 원인 미상 + 아직 안 드러난 실패 (10·11번, 세그폴트로 못 돈 약 160개 테스트, Windows 전용) | 2 | 6 | 13 | 시범에서 원인 미상 2묶음, 숨은 범위 미상 |
| 6. 화면 밖 수정 (`pyproject.toml`, `runtime-smoke.yml` 설치 줄, `Start-QUANTGEN-Desktop.cmd`, `smoke_desktop.py`, README·AGENTS, 준수 문서 11개·`release-profile.json`·기준선) | 1.5 | 2.5 | 4 | 1절 개수 |
| 7. 로컬 Linux 전체 검사 (CI 전 확인, 일부는 수정과 겹침) | 1 | 2 | 4 | 1회 약 55~80분 실측 |
| 8. GitHub CI (1회 약 95분) | 2회 3.2 | 3회 4.8 | 5회 7.9 | run 43432023421: Windows 작업 각 약 94분 |
| 9. Windows 설치·패키징 확인 (wheel·`.[desktop]`; PyInstaller 초안이 있으면 그 빌드 1회) | 0.5 | 1 | 3 | main에 spec 없음 |
| 10. 소유자 Windows 확인 (설치, 화면 7~10개, 한글 글꼴, 배율, 설정 유지) | 1 | 2 | 4 | 글꼴을 바꾸므로 눈 확인 필수 |
| 11. 병합·기록·화면 잠금 해제 | 0.3 | 0.5 | 1 | — |
| **합계 (시간)** | **약 15** | **약 30** | **약 57** | |

- 4·5행에 곱한 배수(1.0/1.2/1.4)는 이미 들어가 있습니다.
- 달력으로는 예상 약 4~5 작업일입니다 (밤, 소유자 확인 일정 포함 시 더 김). 그동안 화면 PR은 멈춥니다 (마스터 규칙 5 "독점 창").
- 앞선 계획 초안의 "약 2.5~3.5일 + 화면 PR 1일 멈춤"(부록 B)은 시범 전 값입니다. 시범에서 세그폴트·`QChar`·원인 미상 실패가 나와 올려 잡았습니다.

**24시간과 비교.** 예상 약 30시간으로 24시간을 넘습니다. **셈 범위에 따른 차이:** 8행(CI 대기)과 10행(소유자 확인)을 빼면 낮음 약 11 / 예상 약 23.5 / 높음 약 45시간이라, 예상값은 24시간 바로 아래입니다. 이 문서는 "전환을 시작해 main에 넣기까지 걸리는 시간"으로 보고 둘을 넣었습니다. 소유자의 "전환에 소요되는 예상 시간"이 작업 시간만을 뜻한다면 결론이 경계선에 있으므로 확인이 필요합니다. 낮음(약 15시간)은 4절의 문제가 모두 금방 풀리고 CI 2회에 끝나는 경우입니다. 시범에서 이미 세그폴트와 원인 미상 실패가 나왔으므로 낮음 쪽일 가능성은 작다고 봅니다.

## 6. 지금 하면 드는 비용

"지금"은 P3 전에 main에 넣는다는 뜻입니다. 동결은 공식적으로 "병합해도 됩니다" 공지부터 F21까지이고, P3 리허설이 그날의 main을 쓰므로 P3 시작부터 사실상 멈춥니다 (`docs/product/PILOT_OWNER_RUN_2026-11-11.md` 686행 부근: "Claude가 알린 때부터 F21이 끝날 때까지 main에 다른 PR을 병합하지 않습니다").

| 비용 | 내용 | 크기 (추정) |
|---|---|---|
| 전환 작업 자체 | 오늘 코드(29,927줄)로 해도 5절과 거의 같음. 도구·화면 밖·CI·소유자 확인은 코드 양과 무관하고, 동작 수정만 약 10~25% 적음 | 5절 예상치에서 약 −2~4시간 |
| P3·F 지연 | 대기열 1~3 (PR121 → PR122 → REMAINING_WORK) 뒤, P3 전에 끼워야 함. 전환 PR 전체(5절 예상 약 30시간, CI 2~5회, 소유자 Windows 확인)가 P3 앞에 들어감 | P3·F21이 약 4~5 작업일 늦어짐 |
| PR121·PR122 | 작성 당시 진행 중 (PR121 브랜치 `de6178f`, 새 Runtime CI가 11-17 11:05Z 시작). 검토 시점에 PR121은 병합됨 (main `5888d05`, 11-17 21:33 KST); PR122는 남음. 전환을 그 앞에 넣으면 두 PR이 main을 다시 합치고 Windows 전체 검사를 각각 다시 | 앞에 넣으면 +2회 (약 3시간). 뒤에 넣으면 영향 없음 |
| UI 세션 | `quantgen_desktop/**`·`tests/desktop_*`의 주인. 변환 실행은 그 세션이 해야 함 (`origin/handoff:AGENTS.md` §6, 마스터 규칙 5). 지금은 PNG 확인 대기 중이고 시안 7개 구현을 앞둠 → 그 일을 멈춤 | 화면 작업 약 4~5 작업일 멈춤 |
| 살아 있는 UI 브랜치 | main을 합칠 때 12개 파일의 import 줄 충돌 + PyQt6로 새로 쓴 파일 5개 다시 변환 + 그 브랜치의 첫 전체 CI (지금까지 0회) | 3~6시간 + CI 1~2회 |
| 연구 브랜치와 F | P3에서 main이 연구 브랜치(`cdbbe61`, PyQt6 import 64파일)로 들어감. F1~F21은 소유자 PC에서 돕니다. 소유자 PC 파이썬에 PySide6를 새로 설치해야 하는데, F 실행 문서에는 그 단계가 없음 | 문서 수정 1~2시간 + 소유자 단계 추가 + F4·F18에서 멈출 위험 (**미검증**: F의 전체 검사가 데스크톱 테스트를 도는지) |
| 소유자 | 지금 Windows 확인 1회, F 때 다시 확인 | +1~2시간 |
| 얻는 것 | F까지 새로 쓰는 화면 코드(시안 7개, 계정 화면 등)가 처음부터 PySide6 → F 뒤 변환할 양이 줄어듦 | 약 2~7시간 절약 (5절 4·5행의 배수 차이) |

정리: main까지 지금 넣으면 전환 작업(약 28시간)은 거의 그대로 들고, 충돌 비용 약 8~15시간과 P3·F의 약 4~5 작업일 지연이 더해집니다. 얻는 것은 약 2~7시간입니다. 그래서 7절에서 "작업은 지금, main 병합은 F21 바로 뒤"라는 방식을 함께 드립니다.

## 7. 판정

**판정: 24시간 초과.** F 뒤 전환 예상 약 30시간 (낮음 약 15, 높음 약 57).

**소유자 규칙에 따른 권장: 지금 진행.** "지금"을 어떻게 하느냐에 따라 두 가지입니다.

| | 가. 지금 main까지 전환 | 나. 지금 시작, main 전환 병합은 F21 바로 뒤 (권장) |
|---|---|---|
| 지금 하는 일 | UI 세션이 전환 PR을 열고 P3 전에 병합 | OS 세션: 변환 도구 + 이 시범의 정식판을 UI 브랜치 최신 위에서 반복. UI 세션: 두 바인딩에서 다 되는 방식으로 4절 2~7·9~11번을 자기 브랜치에서 고침 (UI PR과 함께 main에 들어감). 새로 쓰는 화면은 아래 점검표를 지킴 |
| F21 뒤에 남는 일 | 없음 | 이름 바꾸기, 글꼴 마무리, 화면 밖 수정, CI 2~3회, 소유자 확인 → 약 12~20시간 **(추정)**, 24시간 아래. 근거: 5절 1·2·6~11행은 그대로 남고, 3~5행은 미리 고친 만큼 빠져 남은 몫 약 3~5시간 |
| P3·F | 약 4~5 작업일 늦어짐 | 그대로 |
| 소유자 PC의 F 환경 | PySide6 설치 단계와 F 문서 수정 필요 | 그대로 |
| UI 세션 | 화면 작업 4~5일 멈춤, 브랜치 충돌 정리 | 화면 작업 일부(약 1.5~3 작업일)를 수정에 씀 |
| D2 (UI PR을 P3 전에) | 사실상 불가 | 가능 (수정은 PyQt6에서도 도는 방식이라) |

새 화면 코드 점검표 (나안, UI 세션용): `findChildren`에 튜플 대신 한 타입씩, `receivers(신호)` 대신 연결 여부를 직접 기록, 콤보 항목 데이터에 Enum을 넣으면 꺼낼 때 Enum으로 되돌림, 델리게이트·헤더 등 Qt에 넘긴 객체는 `self.`에 참조 유지, 이벤트 필터에서 Qt 객체를 집합·딕셔너리 키로 쓰지 않음, 지연 호출(`QTimer.singleShot`)은 대상 위젯이 살아 있는지 확인, `QChar` 쓰지 않음, `QTextDocument.print`는 `getattr(document, "print_", None) or document.print`처럼 두 이름을 모두 받게 함.

**나안의 전제 (UI 세션).** 소유자 D6 지시("이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것")에 따라 메인과 하부 세션은 UI 세션의 브랜치·인계 파일·지시문을 고치지 않습니다. 나안에서 UI 세션이 할 수정과 점검표는 OS 세션이 문서로 만들고 **소유자가 UI 세션에 옮겨 주셔야** 시작됩니다. 옮기지 않으면 미리 고치는 몫이 빠져 F21 뒤 남는 일이 다시 약 30시간(5절 예상)에 가까워집니다.

소유자께 여쭐 것 한 줄: "D9는 24시간을 넘으니 지금 진행합니다. 방식은 나(작업 지금, main 병합은 F21 바로 뒤)로 하겠습니다. main까지 지금 넣기를 원하시면 '가'라고 답해 주세요. '24시간'이 CI 대기와 소유자 확인을 뺀 작업 시간만을 뜻하셨다면 알려 주세요 (그 경우 예상 약 23.5시간으로 경계선입니다)."

참고로 "24시간"을 달력 시간으로 보셔도 결과는 같습니다. 예상 약 30 작업시간은 달력으로 4~5일입니다.

## 8. 확인 못 한 것

- **Windows에서의 PySide6 동작 (미검증).** 시범은 Linux 오프스크린만 돌렸습니다. Windows 전용 검사(`desktop_windows_branding_acceptance` 등)와 실제 화면 배율·글꼴 표시는 CI Windows와 소유자 PC에서만 압니다.
- **F 때의 코드 크기 (추정).** F21 날짜를 모르고, 그때까지 UI 세션이 얼마나 더 쓸지도 모릅니다. 5절은 데스크톱 코드가 약 35,000~45,000줄이라고 보고 계산했습니다.
- **글꼴 대체 등록의 대안 (미검증).** PySide6에 `addApplicationFallbackFontFamily`가 없어서 `font_policy.py`를 다른 방식(`QFont.setFamilies`만, 또는 `QFont.insertSubstitutions`)으로 바꿔야 합니다. 그 대안이 Windows에서 한글·숫자·기호를 지금과 같게 그리는지는 아직 모릅니다. 5절 "높음"의 주된 이유입니다.
- **시범 변환은 간이판입니다.** `sip`을 `shiboken6`으로 바꾸는 부분은 한 줄짜리 대체물로 처리했고, `font_policy.py`는 대체 등록을 건너뛰게만 고쳤습니다. 실제 도구(`tools/qt_port/pyqt6_to_pyside6.py`, OS-P0-a)는 아직 없습니다.
- **CI의 다른 Python 버전 (확인함).** CI는 Windows 3.11·3.12·3.14를 씁니다. PyPI JSON에서 PySide6-Essentials 6.12.0은 `cp310-abi3-win_amd64` 휠 하나로 Python ">=3.10,<3.16"을 받습니다 (PyQt6 6.12.0도 같은 abi3 방식). 설치 자체는 막히지 않습니다. 실제 3.14 Windows에서 도는지는 CI 첫 회에서 압니다.
- **F 실행 문서와 데스크톱 테스트 (미검증).** F의 전체 검사가 소유자 PC에서 데스크톱(Qt) 테스트를 도는지, 소유자 PC 파이썬에 무엇이 깔려 있는지 확인하지 않았습니다. 6절 "연구 브랜치와 F" 행의 위험 크기는 이것에 달려 있습니다.
- **PyInstaller.** main에는 아직 spec이 없습니다. OS 세션이 F 전에 만들 초안이 PyQt6 기준이면 전환 때 다시 맞춰야 합니다 (5절 9행).
- **라이선스.** PySide6 LGPL v3로 소스를 닫고 팔 때의 조건(동적 링크, 교체 가능성, 고지)은 변호사 확인이 필요합니다. 이 문서의 라이선스 문장은 법률 자문이 아닙니다.

## 9. 출처

저장소 (모두 `git show`·`git grep`으로 읽음):
- `origin/main` `e01e152`: `pyproject.toml` 22~26행, `.github/workflows/runtime-smoke.yml` 100행과 Qt 검사 단계, `Start-QUANTGEN-Desktop.cmd` 14행, `tools/packaging/smoke_desktop.py`, `quantgen_desktop/font_policy.py` 12·50~53행, `quantgen_desktop/paper.py` `combo()`, `quantgen_desktop/stock_report.py` 164행, `quantgen_desktop/stock_detail.py`·`stock_detail_side.py` (`sip`), `tests/desktop_operation_fixes_acceptance.py` 119행, `tests/qt_fixture_cleanup.py`, `docs/product/PILOT_OWNER_RUN_2026-11-11.md` (동결 문단).
- `origin/claude/friendly-bardeen-r6xe8f` `212f0dd`, `origin/claude/amazing-gauss-tdiguu` `cdbbe61`, `origin/gpt/r3-recorder-20261114` `de6178f`.
- CI 시간: `gh run list`/`gh run view` (읽기만). run 43432023421 (녹색, 2026-11-13): Windows 작업 3개 각 약 94분, Ubuntu 약 39분, 전체 95분. run 43478587544 95분, 43478852671 97분.
- 계획 초안: 스크래치 `drafts/MASTER_WORK_DESIGN_2026-11-17.md` (2.2·4절, 부록 B "약 2.5~3.5일 + 화면 PR 1일 멈춤"), `drafts/sessions/02_UI_UX.md` (UI-7), `drafts/sessions/04_OS_EXPANSION_NEW.md` (OS-P0-a).

시범 실행 (저장소 밖, 메인 세션 작업 폴더 `w1117/f2/` 아래 — 하부 세션은 열 수 없음. 변환 시범 도구 두 개는 handoff `plans/2026-11-17/d9_trial_tools/`에 복사해 둠. 시범 로그가 필요하면 메인에 요청; 아래 `f2/`는 이 폴더):
- 변환 스크립트 `f2/tools/codemod_trial.py`, 실행기 `f2/tools/run_steps.sh`, 단계 목록 `f2/tools/qt_steps.txt` (`runtime-smoke.yml`에서 뽑고 `-f`만 뺌), 로그 `f2/trial/log_pyqt/`, `f2/trial/log_pyside/`.
- 패키지: PyQt6 6.12.0, PySide6-Essentials 6.12.0, shiboken6 6.12.0, Python 3.13.17 (Linux). CI는 Windows 3.11·3.12·3.14와 Ubuntu 3.12.

공개 자료 (2026-11-17 확인):
- PySide6-Essentials 6.12.0 (2026-10-08 공개, 라이선스 "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only", 포함 모듈 목록에 QtSvg·QtSvgWidgets·QtTest 있음, QtCharts·QtWebEngine 없음): https://pypi.org/project/PySide6-Essentials/6.12.0/
- PyQt6 6.12.0 (2026-10-28 공개, GPL v3 또는 상용 라이선스): https://pypi.org/project/PyQt6/6.12.0/
- PyQt 5.5부터 슬롯 안의 처리 안 된 예외는 `qFatal()` → 중단 (메일링 리스트): https://riverbankcomputing.com/pipermail/pyqt/2016-March/037129.html (검색 결과 요약으로만 확인. 이번 실측이 같은 동작을 보임)
- PySide6 열거형이 파이썬 enum으로 바뀜, `pyqtSignal`↔`Signal` 대응 (검색 결과 요약): https://help.autodesk.com/cloudhelp/2025/ENU/Maya-DEVHELP/files/Whats-New-Whats-Changed/2025-Whats-New-in-API/Qt6Migration.html , https://code.qt.io/cgit/pyside/pyside-setup.git/tree/sources/pyside6/doc/gettingstarted/porting_from2.rst
- `addApplicationFallbackFontFamily`는 Qt 6.8에서 생긴 C++ 함수 (검색 결과 요약): https://doc.qt.io/qt-6/qfontdatabase.html
- 이 세션에서 doc.qt.io, pythonguis.com, riverbankcomputing.com은 직접 열리지 않았습니다 (네트워크 허용 목록 밖). 위 세 곳은 검색 요약으로만 봤습니다.

법률 관련 문장은 법률 자문이 아닙니다.
