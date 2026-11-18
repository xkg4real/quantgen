# PySide6 직접 검증 — UI 브랜치 (2026-11-19, Claude UI 세션)

소유자 지시: "PySide6 직접 검증해". OS_EXPANSION 세션의 시범(`claude/os-prep-20261117`의
`docs/platform/PYSIDE6_TRIAL_2026-11-17.md` 9절, UI `5025c6f` "18단계 모두 PyQt6와 같음")과 별개로, 이 세션에서
PySide6를 설치해 같은 코드를 처음부터 다시 돌렸습니다.

## 방법

- 대상: UI 브랜치 `5025c6f` (지금 브랜치 끝 `2cd8477`의 `quantgen_desktop/`·`tests/`는 이것과 같습니다 — 아래
  "되돌린 수정" 참고).
- `git archive`로 사본을 만들고(`docs/`·`results/` 포함, `docs/asset_expansion/cache/`·`.env`·`tools/nautilus/` 제외),
  OS 브랜치의 `tools/qt_port/pyqt6_to_pyside6.py --apply`로 변환했습니다. PySide6-Essentials 6.12.0, Python 3.13,
  Linux offscreen.
- 섞임 방지: PySide6 실행에서는 `PyQt6` import를 막는 가짜 패키지를 `PYTHONPATH` 앞에 두었습니다.
- OS 시범과 다른 점: CI 단계 묶음이 아니라 **107개 모듈을 하나씩, 시간 제한 없이**(모듈당 최대 1시간) 돌렸습니다.
  OS 시범에서 두 바인딩 모두 25분 제한에 걸린 단계 9·13도 끝까지 돌았습니다. 모듈마다 종료 코드·최대 메모리·
  "이미 지워진 C++ 객체" 줄 수를 기록했습니다.

## 결과

| 항목 | PyQt6 | PySide6 |
|---|---|---|
| 실행한 테스트 (107개 모듈) | 1,117 | 1,117 |
| 실패·오류 | 0 | 0 |
| 건너뜀 | 1 (Windows 전용) | 1 (같은 것) |
| "이미 지워진 C++ 객체" 줄 | 0 | 0 |
| 모듈 하나의 최대 메모리 | 2.7 GB | 3.1 GB (같은 모듈: 시장 화면 47개 테스트) |
| 모듈별 테스트 수 차이 | — | 없음 |

**남은 문제 하나 — PySide6에서만, 드물게, 비정상 종료(메모리 손상).**

| 실행 | 결과 |
|---|---|
| `tests.desktop_market_tabs_acceptance` 모듈, PySide6, 부하 걸고 반복 | 66번 중 2번 SIGABRT (`malloc_consolidate(): unaligned fastbin chunk detected`) — `5025c6f` 사본 1번, 이후 커밋 사본 1번 |
| 같은 모듈, gdb 아래 | 8번 중 1번 SIGABRT |
| 같은 모듈, PyQt6 | 20번 중 20번 통과 |
| 문제 테스트 하나만, PySide6 | 60번 중 0번 |
| valgrind memcheck (테스트 하나, 모듈 전체) | 잘못된 쓰기·해제·해제 뒤 읽기 0건. 10종의 "Invalid read of size 16"은 모두 할당 범위 안 SIMD 문자열 미리 읽기(QMetaType::fromName, QMetaStringTable, QCss 파서) — 알려진 오탐 유형 |
| glibc 디버그 할당기(`MALLOC_CHECK_=3`, `MALLOC_PERTURB_`) + gdb | 121번 중 0번 |

- 위치: 두 번 모두 `SearchZoomTests.test_choosing_a_name_loads_and_connects_without_a_button`(종목 검색 → 불러오기 →
  실시간 연결) 뒤 정리 단계에서 창을 지울 때(`tests/qt_fixture_cleanup.delete_owned_widget` → `sendPostedEvents`
  → `QWidget::~QWidget` → `QBackingStore` → `QImage` → `QRasterPaintEngine` 소멸 중 `free`). 손상을 **발견한**
  곳이며 손상을 **만든** 곳은 그 전입니다.
- 그 순간 다른 스레드: Qt 스레드 풀 4개와 OpenBLAS 스레드 6개가 모두 대기 중이었고, Python 코드를 실행 중인 스레드는
  없었습니다. 로그에 Python 예외·"Error calling Python override"·QPainter 경고는 없었습니다.
- 해석(가설): 스레드를 한 줄로 실행하는 valgrind와 할당 순서가 바뀌는 디버그 할당기에서는 사라지므로, 타이밍에 따라
  드러나는 경합이나 해제 뒤 쓰기로 봅니다. **원인 위치는 아직 모릅니다.**
- 배제한 것:
  - `Job`(QRunnable) 이중 삭제. PySide6도 `QThreadPool.start`에서 소유권을 C++로 넘기고, 실행 뒤 풀이 지우면 Python
    래퍼가 무효가 됩니다(`shiboken6.isValid` 확인). 짧은 작업 300개의 정리도 모두 화면 스레드에서 일어났습니다.
  - Python 바이트를 Qt에 넘기는 SVG 로드. `QByteArray(bytes)`는 복사합니다.

## 되돌린 수정

OS 재시범 8절의 "창마다 숨은 최상위 위젯 21개"는 키 수치 등을 다시 그릴 때 떼어 낸 항목이 지연 삭제를 기다리는
것입니다. 실제 앱의 이벤트 루프에서는 지워지며, 지연 삭제를 처리하면 두 바인딩 모두 0개입니다. 지울 항목을 부모
아래 두는 수정(`336f8b1`, `01a6e96`)은 숨은 이전 언어 라벨을 기존 언어 테스트가 읽게 만들어
(`desktop_language_acceptance` 1건, 두 바인딩 공통) 되돌렸습니다(`1660d3a`, `2cd8477`).

## 판정

- 일반 테스트 기준: PySide6는 PyQt6와 같습니다(1,117개 모두 통과, 세그폴트·메모리 폭증 없음).
- 약 3% 확률의 PySide6 전용 비정상 종료가 남아 있어 **"전환 준비 완료"로 확정하지 않습니다.** PyQt6(현재 앱)에는
  영향이 없습니다.

## 다음 단계 (재현 방법)

변환한 사본의 루트에서 PySide6 venv로:

```bash
QT_QPA_PLATFORM=offscreen PYTHONFAULTHANDLER=1 gdb -q -batch -ex run -ex "thread apply all bt 40" --args python -m unittest tests.desktop_market_tabs_acceptance
```

4개를 동시에 반복하면 수십 번 안에 재현됩니다. 원인을 좁히려면:

1. 앞선 `MarketTabsTests`를 빼고 `SearchZoomTests`만 반복해서, 앞 테스트가 남긴 상태가 필요한지 확인합니다.
2. 반대로 문제 테스트만 빼고 모듈을 반복합니다.
3. 원인 후보 부분(시장 화면 차트 미리보기 `on_snapshot`, 실시간 연결, 오른쪽 열 카드 불러오기)을 하나씩 끈 변형으로
   반복합니다.
4. 필요하면 AddressSanitizer로 빌드한 Qt/PySide6로 돌립니다.
