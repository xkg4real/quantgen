# PySide6 대비 화면 코드 점검표 (UI 세션용)

- 작성: 2026-11-17, OS_EXPANSION 세션 (QUANTGEN/MAIN의 하부 세션). 근거: 메인의 D9 보고서(handoff `plans/2026-11-17/D9_PYSIDE6_ESTIMATE.md` 4·7절)와 이 세션의 정식 시범 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md`.
- 목적: 소유자 D9 결정의 "나안" — 전환 병합은 F21 바로 뒤에 하고, 그때 남는 일을 줄이려고 **지금 UI 브랜치에서 PyQt6로도 그대로 도는 방식**으로 미리 고칩니다. 이 점검표의 모든 항목은 PyQt6 6.12.0에서도 동작이 같습니다.
- 이 세션은 `quantgen_desktop/**`와 `tests/desktop_*`를 고치지 않습니다. 아래 수정은 UI 세션이 자기 브랜치에서 합니다.
- 위험 위치 찾기: `python tools/qt_port/pyqt6_to_pyside6.py --lint` (작업 브랜치 `claude/os-prep-20261117`). 줄 끝의 `[묶음]`이 아래 번호입니다. `--ref origin/<브랜치>`로 체크아웃 없이도 됩니다.

## 새 화면 코드에서 지킬 것

| # | 하지 말 것 | 이렇게 (두 바인딩 모두 동작) | lint 묶음 |
|---|---|---|---|
| 1 | `document.print(printer)` | `(getattr(document, "print_", None) or document.print)(printer)` — PySide6에서는 이름이 `print_` | `1-print` |
| 2 | `w.findChildren((QComboBox, QSpinBox))` (타입 튜플) | 타입마다 따로: `[*w.findChildren(QComboBox), *w.findChildren(QAbstractSpinBox)]` | `2-findChildren` |
| 3 | `if self.receivers(self.open_requested) > 0:` | 연결할 때 직접 표시: `self._open_connected = True` 를 두고 그 값을 봄 | `3-receivers` |
| 4 | 콤보 항목 데이터에 str Enum을 넣고 `currentData()`를 그대로 Enum으로 씀 | 꺼낼 때 되돌림: `Side(combo.currentData())` (데이터가 `None`이면 그대로). PySide6는 str Enum을 평범한 str로 돌려줌 | `4-combo-data` (검토용, 모두 위험은 아님) |
| 5 | 이벤트 필터 안에서 `watched in self.roots`, `self.table[watched]`, `self.handlers.get(watched)` | Qt 객체를 집합·딕셔너리 키로 쓰지 않음: `any(watched is r for r in self.roots)`, 또는 `id(watched)`를 키로 쓰고 객체는 값으로 보관 (PySide6의 `QPointingDevice` 등은 해시 불가) | `5-qobject-key` |
| 6 | **`QTimer.singleShot(0, self.apply)`처럼 `self`의 메서드를 바로 넘김** (가장 먼저 고칠 것) | 객체의 자식 타이머를 씀: `__init__`에서 `self._apply_timer = QTimer(self); self._apply_timer.setSingleShot(True); self._apply_timer.timeout.connect(self.apply)`, 부를 때 `self._apply_timer.start(0)`. 타이머가 객체와 함께 지워지므로 객체가 사라진 뒤에는 불리지 않음. PyQt6는 객체가 지워지면 이 호출을 버리지만 PySide6는 그대로 부름 (실측: 세그폴트와 메모리 폭증의 원인). PySide6의 `singleShot(ms, self, self.apply)`는 PyQt6에 없어 지금은 못 씀. 람다(`lambda: ...`)로 넘기는 곳은 콜백 첫 줄에서 대상이 살아 있는지 확인 | `6-bound` (main 28곳, UI 29곳), `6-deferred` (검토용) |
| 7 | 슬롯 안 예외를 "앱이 멈추니 테스트가 잡겠지"라고 기대 | PyQt6는 슬롯 안 예외에서 앱을 멈추지만 PySide6는 출력만 하고 계속 감. 테스트는 `sys.excepthook`/`sys.unraisablehook`을 바꿔 예외를 모아 실패로 만듦 (`tests/desktop_stock_detail_acceptance.py`의 수집 방식처럼) | — |
| 8 | `QChar`, `QFontDatabase.addApplicationFallbackFontFamily` 등 대체 글꼴 4함수, `QRawFont.supportsCharacter("×")` (문자열) | `QChar` 쓰지 않음. 문자 검사는 `supportsCharacter(ord(ch))` (정수). 대체 글꼴은 `QFont.insertSubstitutions` (아래 "글꼴" 참고) | `8-font` |
| 9 | `table.setItemDelegateForColumn(0, MyDelegate(table))`처럼 Qt에 넘긴 객체를 바로 버림 | `self.identity_delegate = MyDelegate(table)` 후 넘김. 헤더(`setHorizontalHeader`)·모델·필터 객체도 같음 | `9-delegate` |
| 10 | 창이나 화면에서 떼어 낸 위젯(레이아웃 밖, `parent` 없음)을 창의 Python 속성으로만 들고 있음 | 떼어 낸 위젯은 부모를 주거나, 바꿀 때·창을 닫을 때 `deleteLater()`로 직접 지움. 앱 전체(`QApplication`)에 건 이벤트 필터는 창이 사라질 때 `removeEventFilter` | — (시범 실측, 아래) |
| 11 | `sip.isdeleted(x)`, `from PyQt6 import sip` | 새 코드에서는 쓰지 말고, 꼭 필요하면 한 도움 함수에 모음 (변환 도구가 `shiboken6.isValid`로 바꿈) | `sip` |
| 12 | `font.setWeight(600)`처럼 숫자를 그대로 넘김 | `font.setWeight(QFont.Weight(600))`. PySide6는 숫자를 받지 않고 TypeError를 냅니다. `paintEvent` 안에서 나면 그리기 도구(QPainter)가 닫히지 않아 앱이 죽습니다 (실측: UI `bonds.py:201`, 단계 6 세그폴트. 고친 뒤 20개 테스트 모두 통과, 2번 중 2번) | `10-int-enum` |
| 13 | 사용자 글자를 Qt 항목 데이터(`addItem(text, data)`, `setData`)에 넣은 뒤 꺼내 검사 | 검사는 Qt에 넣기 **전에** 합니다. 데이터에는 키만 넣고 원본은 Python 딕셔너리에 둡니다. PySide6는 짝 없는 서로게이트(`'\ud800'`)를 조용히 지웁니다. 딕셔너리째 넣어도 QVariantMap으로 바뀌며 지워집니다 (실측, PyQt6는 그대로 둠) | — (`4-combo-data`와 함께 검토) |

## 시범에서 드러난 세그폴트·메모리 폭증의 원인 (6번 항목의 근거, 2026-11-17 확정)

- **원인 한 곳:** `quantgen_desktop/localization.py`의 `LanguageController.schedule()`이 `QTimer.singleShot(0, self.apply)`를 겁니다. 테스트가 창을 지운 뒤에도 PySide6에서는 이 예약된 호출이 그대로 실행되고, `apply()`가 이미 지워진 `ResearchWindow`를 건드려 오류가 납니다. PySide6는 이 오류를 저장해 두었다가 다음 Python 호출에서 다시 던지는데, 앱 전체 이벤트 필터(`ReadingHelp`, `InlineMarketMenu`)가 이벤트마다 그 오류 메시지 앞에 "Error calling Python override ..."를 덧붙여 다시 저장합니다. 메시지가 끝없이 길어지면서 메모리가 27초 만에 3GB를 넘었습니다.
- **찾은 방법:** 단계 3의 두 테스트만 돌리고 py-spy로 스택을 떴습니다. 네이티브 스택은 `QTest::qWaitForWindowActive → sendThroughApplicationEventFilters → Shiboken::Errors::storePythonOverrideErrorOrPrint`였습니다. 이어서 이벤트 필터를 감싸 첫 예외를 기록하니, 출처가 `localization.py:130 apply → self.window.setLocale(...)`의 "already deleted"로 나왔습니다.
- **고친 결과 (임시 복사본에만 6번 방식 적용, 화면 코드는 고치지 않음):**

| 실행 (PySide6 6.12.0, Linux 오프스크린) | 고치기 전 | 고친 뒤 |
|---|---|---|
| UI 단계 3의 두 테스트, 최대 메모리 | 3GB를 넘어 강제 종료 | 0.52GB, 통과 |
| UI 단계 3 전체 | OOM 또는 rc 139 | rc 0, 59초, 0.54GB |
| UI 단계 5 전체 | OOM, 다시 돌려도 실패 1 + 오류 1 | 실패 1 (`receivers`, 3번 항목), `market_progressive` 오류는 사라짐, 0.74GB |
| main 세그폴트 재현 스크립트, 3번 | rc 139 1번 + 실패 2번 | **3번 모두 통과** |
| 같은 수정을 PyQt6에 적용한 UI 단계 3 | — | rc 0 (동작 같음) |

- 재현: `tools/qt_port/repro/shell_window_segfault.sh` (변환한 임시 복사본에서만).
- **별개의 누수는 남아 있음 (실측):** 6번을 고친 복사본에서도 `tools/qt_port/repro/window_survivors.py`의 결과는 같습니다. PySide6에서는 창을 지울 때마다 숨은 최상위 위젯이 6개씩 쌓입니다(창 0을 지운 뒤 6개, 창 1을 지운 뒤 12개). 남는 것은 `MarketChartPane`, `BondsPane.source` 콤보, 이름 없는 `QFrame`이고, 지운 창의 Python 객체가 아직 붙잡고 있습니다. 이 누수 때문에 테스트가 죽지는 않습니다. 다만 앱이 창을 다시 만들 때마다 메모리가 늘어나므로 10번 항목(떼어 낸 위젯은 부모를 주거나 `deleteLater()`)으로 고칩니다. gdb의 위임 객체 스택은 앞의 오류 연쇄 중에 생긴 것으로 보며(가설), 9번도 그대로 권장합니다.
- 전체 시범을 다시 돌린 결과는 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md`의 "재시범" 절에 있습니다.

## 글꼴 (8번 항목의 근거)

- `tools/qt_port/font_probe.py` 결과 (`docs/platform/font_probe/FONT_PROBE.md`, Linux 오프스크린): 지금 묶음 글꼴에서는 **QG Symbols의 문자가 모두 QG Interface에 이미 있음** (QG Symbols에만 있는 문자 0개). 그래서 앱 글꼴(`setFamilies`)과 `font-family: "QG Interface"` 위젯은 대체 등록이 있든 없든 같은 글꼴로 그립니다.
- 차이가 나는 경우는 **다른 글꼴을 지정한 위젯** 하나뿐입니다: 한글이 없는 글꼴(여기서는 DejaVu Sans, Windows에서는 Segoe UI 등)을 지정하면 지금(PyQt6 대체 등록)은 한글을 QG Interface로 그리지만, `setFamilies`만 쓰면 시스템 한글 글꼴로 그립니다.
- PySide6에서 지금과 같은 결과: `QFont.insertSubstitutions("QG Interface", ["QG Symbols"])`와 플랫폼 글꼴마다 `QFont.insertSubstitutions(<플랫폼 글꼴>, ["QG Interface", "QG Symbols"])`. 이 방식은 PyQt6에도 있어 지금 바꿔도 동작이 같습니다 (실측, Linux). Windows 표시는 소유자 확인 전 **미검증**.
- 새 화면에서는 `font-family`에 QG Interface 말고 다른 글꼴을 쓰지 않는 것이 가장 단순합니다.

## 바꾸지 않아도 되는 것 (D9 실측)

신호·슬롯 이름(변환 도구가 바꿈), 열거형 완전 표기(`Qt.AlignmentFlag.AlignCenter`), `exec()`, `QFileDialog` 반환 튜플, 고해상도 설정, `int(window.winId())`, `QSvgWidget`, `QTest`.
