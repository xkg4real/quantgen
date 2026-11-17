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
| 6 | `QTimer.singleShot(0, self.apply)` 뒤 대상이 이미 지워졌을 수 있음 | 실행할 때 확인: 콜백 첫 줄에서 대상 위젯이 살아 있는지 (`is_alive(widget)` 같은 작은 도움 함수를 두 바인딩용으로 하나 둠) 또는 `QTimer`를 위젯의 자식으로 만들어 위젯과 함께 사라지게 | `6-deferred` (검토용) |
| 7 | 슬롯 안 예외를 "앱이 멈추니 테스트가 잡겠지"라고 기대 | PyQt6는 슬롯 안 예외에서 앱을 멈추지만 PySide6는 출력만 하고 계속 감. 테스트는 `sys.excepthook`/`sys.unraisablehook`을 바꿔 예외를 모아 실패로 만듦 (`tests/desktop_stock_detail_acceptance.py`의 수집 방식처럼) | — |
| 8 | `QChar`, `QFontDatabase.addApplicationFallbackFontFamily` 등 대체 글꼴 4함수, `QRawFont.supportsCharacter("×")` (문자열) | `QChar` 쓰지 않음. 문자 검사는 `supportsCharacter(ord(ch))` (정수). 대체 글꼴은 `QFont.insertSubstitutions` (아래 "글꼴" 참고) | `8-font` |
| 9 | `table.setItemDelegateForColumn(0, MyDelegate(table))`처럼 Qt에 넘긴 객체를 바로 버림 | `self.identity_delegate = MyDelegate(table)` 후 넘김. 헤더(`setHorizontalHeader`)·모델·필터 객체도 같음 | `9-delegate` |
| 10 | 창이나 화면에서 떼어 낸 위젯(레이아웃 밖, `parent` 없음)을 창의 Python 속성으로만 들고 있음 | 떼어 낸 위젯은 부모를 주거나, 바꿀 때·창을 닫을 때 `deleteLater()`로 직접 지움. 앱 전체(`QApplication`)에 건 이벤트 필터는 창이 사라질 때 `removeEventFilter` | — (시범 실측, 아래) |
| 11 | `sip.isdeleted(x)`, `from PyQt6 import sip` | 새 코드에서는 쓰지 말고, 꼭 필요하면 한 도움 함수에 모음 (변환 도구가 `shiboken6.isValid`로 바꿈) | `sip` |

## 시범에서 드러난 세그폴트와 그 수정 방향 (10번 항목의 근거)

- 재현: `tools/qt_port/repro/shell_window_segfault.sh` (변환한 임시 복사본에서만). main `5888d05`, PySide6 6.12.0, Linux 오프스크린에서 3번 중 2번 rc=139, CI 단계 2 그대로는 3번 중 3번. PyQt6는 0번.
- C 스택 (gdb): `QTableView::timerEvent → updateEditorGeometries → QStyledItemDelegate::updateEditorGeometry → Shiboken::BindingManager::getOverride → 해제된 Python 래퍼 접근`. 크래시 대신 오류로 드러난 실행에서는 `Error calling Python override of QStyledItemDelegate::initStyleOption(): ReportActions.__init__.<locals>.<lambda>() ...`이 나옴 — 위임 객체 자리에 엉뚱한 Python 객체가 불림. **수명(소유권) 문제**입니다.
- 창을 지운 뒤 남는 위젯 (`tools/qt_port/repro/window_survivors.py`): PyQt6는 창마다 숨은 최상위 위젯 6개로 고정, PySide6는 창마다 6개씩 쌓임 (지운 창의 `MarketChartPane`, `BondsPane`의 `QComboBox`, `QFrame`; 지운 `ResearchWindow`의 Python 객체가 아직 붙잡고 있음).
- 메모리 폭증: 같은 날 PySide6 쪽 python이 10.8~12.9GB까지 커져 OOM으로 죽은 것이 4번 (PyQt6 0번). 이벤트 필터 오류가 100단계 넘게 겹친 출력이 함께 보여, 이벤트 필터 안에서 예외가 나면 그 처리 중 다시 이벤트가 생겨 필터가 서로를 부르는 연쇄로 봅니다 (가설). 5번 항목(필터 안 해시)을 고치고 필터 안 예외를 없애는 것이 우선입니다.
- 확인한 것: `gc.disable()`이어도 재현됨(가비지 수집 시점 문제 아님). 테스트 정리 뒤 `gc.collect()`를 강제하면 3번 중 0번. `watchlist.py`의 `_IdentityDelegate`를 `self.`에 붙잡는 것만으로는 2번 중 2번 여전히 재현.
- 수정 방향 (두 바인딩 모두): 9·10번 항목. 창을 닫을 때(`closeEvent`/정리 함수) 떼어 낸 차트 창·콤보·프레임을 `deleteLater()`하고, 창이 단 앱 전체 이벤트 필터를 떼고, 창 객체를 붙잡는 람다·바운드 메서드 연결을 끊음. 테스트 도움 함수 `tests/qt_fixture_cleanup.py`의 `delete_owned_widget` 뒤에 `gc.collect()`.
- 원인 객체를 하나로 특정하지는 못했습니다 (가설). 9·10번을 고친 뒤 위 재현 스크립트로 다시 봅니다.

## 글꼴 (8번 항목의 근거)

- `tools/qt_port/font_probe.py` 결과 (`docs/platform/font_probe/FONT_PROBE.md`, Linux 오프스크린): 지금 묶음 글꼴에서는 **QG Symbols의 문자가 모두 QG Interface에 이미 있음** (QG Symbols에만 있는 문자 0개). 그래서 앱 글꼴(`setFamilies`)과 `font-family: "QG Interface"` 위젯은 대체 등록이 있든 없든 같은 글꼴로 그립니다.
- 차이가 나는 경우는 **다른 글꼴을 지정한 위젯** 하나뿐입니다: 한글이 없는 글꼴(여기서는 DejaVu Sans, Windows에서는 Segoe UI 등)을 지정하면 지금(PyQt6 대체 등록)은 한글을 QG Interface로 그리지만, `setFamilies`만 쓰면 시스템 한글 글꼴로 그립니다.
- PySide6에서 지금과 같은 결과: `QFont.insertSubstitutions("QG Interface", ["QG Symbols"])`와 플랫폼 글꼴마다 `QFont.insertSubstitutions(<플랫폼 글꼴>, ["QG Interface", "QG Symbols"])`. 이 방식은 PyQt6에도 있어 지금 바꿔도 동작이 같습니다 (실측, Linux). Windows 표시는 소유자 확인 전 **미검증**.
- 새 화면에서는 `font-family`에 QG Interface 말고 다른 글꼴을 쓰지 않는 것이 가장 단순합니다.

## 바꾸지 않아도 되는 것 (D9 실측)

신호·슬롯 이름(변환 도구가 바꿈), 열거형 완전 표기(`Qt.AlignmentFlag.AlignCenter`), `exec()`, `QFileDialog` 반환 튜플, 고해상도 설정, `int(window.winId())`, `QSvgWidget`, `QTest`.
