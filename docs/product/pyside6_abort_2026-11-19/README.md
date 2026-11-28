# OS_EXPANSION 세션 인계 — PySide6 전용 간헐 비정상 종료 (UI 세션 → OS 세션, 2026-11-19)

소유자 지시(원문): "그러면 OS세션에 인계할 프롬프트와 파일을 전달/작성해주세요"

이 폴더의 파일은 작업 브랜치 `claude/friendly-bardeen-r6xe8f`에 있습니다(체크아웃 없이
`git show origin/claude/friendly-bardeen-r6xe8f:<경로>`로 읽을 수 있음).

| 파일 | 내용 |
|---|---|
| `docs/product/PYSIDE6_UI_VERIFICATION_2026-11-19.md` | UI 세션의 PySide6 직접 검증 보고서: 방법, 결과, 배제한 가설 |
| `docs/product/pyside6_abort_2026-11-19/setup_copy.sh` | UI 커밋을 PySide6 사본으로 만드는 스크립트(OS 변환 도구 사용, PyQt6 import 차단) |
| `docs/product/pyside6_abort_2026-11-19/repeat_module.sh` | 한 모듈(또는 테스트)을 동시에 여러 번 반복하고 비정상 종료를 세는 스크립트 |
| `docs/product/pyside6_abort_2026-11-19/gdb_until_abort.sh` | gdb 아래에서 비정상 종료가 날 때까지 반복하고, 모든 스레드의 스택을 남기는 스크립트 |
| `docs/product/pyside6_abort_2026-11-19/gdb_backtrace.txt` | 잡힌 비정상 종료 1건의 스택(메인 스레드) 발췌 |

---

## OS 세션에 줄 프롬프트

> 이 메시지는 UI 세션(Claude UI, `claude/friendly-bardeen-r6xe8f`)이 소유자 지시로 보내는 인계입니다. 소유자 원문:
> "그러면 OS세션에 인계할 프롬프트와 파일을 전달/작성해주세요".
>
> **무엇:** UI 세션이 PySide6-Essentials 6.12.0으로 UI 브랜치를 직접 검증한 결과, 107개 모듈 1,117개 테스트는
> PyQt6와 같았습니다(실패 0, "이미 지워진 C++ 객체" 0, 최대 3.1GB). 그런데 **PySide6에서만 드물게 앱이 비정상
> 종료**합니다. OS 시범 9절의 판정("UI `5025c6f`, 18단계 모두 PyQt6와 같음 → 전환 준비 끝")은 이 문제가 해결될
> 때까지 보류해야 합니다.
>
> **사실:**
> - 모듈: `tests.desktop_market_tabs_acceptance`. 4개를 동시에 반복(4코어 Linux, offscreen)하면 PySide6에서
>   66번 중 2번 SIGABRT가 납니다(`malloc_consolidate(): unaligned fastbin chunk detected`). 그중 1번은 `5025c6f`
>   사본, 1번은 그 뒤 커밋 사본에서 났습니다. 지금 브랜치의 `quantgen_desktop/`·`tests/`는 `5025c6f`와 같습니다.
> - 같은 모듈을 PyQt6로 20번 돌리면 20번 모두 통과합니다. 문제 테스트 하나만 PySide6로 60번 돌리면 0번입니다.
> - 위치: 두 번 모두 `SearchZoomTests.test_choosing_a_name_loads_and_connects_without_a_button`(종목 검색 → 불러오기
>   → 실시간 연결) 뒤 정리 단계에서 창을 지울 때입니다. 경로는 `delete_owned_widget` → `sendPostedEvents` →
>   `QWidget::~QWidget` → `QBackingStore` → `QImage` → `QRasterPaintEngine` 소멸 → `free`입니다. 여기는 손상을
>   **발견한** 곳이고, 손상을 **만든** 곳은 그 전입니다. 그 순간 다른 스레드는 Qt 풀 4개·OpenBLAS 6개 모두 대기
>   중이었고, Python 예외나 QPainter 경고는 없었습니다(`gdb_backtrace.txt`).
> - 재현되지 않는 조건: valgrind memcheck(잘못된 쓰기·해제 0건, 남은 10종은 SIMD 미리 읽기 오탐), glibc 디버그
>   할당기(`MALLOC_CHECK_=3`, `MALLOC_PERTURB_`) 121회 0건. 그래서 타이밍에 따라 드러나는 경합이나 해제 뒤 쓰기로
>   보지만, 이는 가설입니다.
> - 배제한 것: `jobs.Job`(QRunnable) 이중 삭제. PySide6도 `QThreadPool.start`에서 소유권을 C++로 넘기고, 실행 뒤
>   래퍼가 무효가 됩니다(`shiboken6.isValid`로 확인). 짧은 작업 300개의 정리도 모두 화면 스레드에서 일어났습니다.
>   SVG 로드(`QByteArray(bytes)`는 복사함)도 배제했습니다.
> - 8절의 "창마다 숨은 최상위 위젯 21개"는 다시 그릴 때 떼어 낸 항목이 지연 삭제를 기다리는 것입니다. 실제 이벤트
>   루프에서는 지워지고, `sendPostedEvents(None, DeferredDelete)`를 하면 두 바인딩 모두 0개가 됩니다. UI 세션이
>   부모를 유지하는 수정을 해 봤지만 기존 언어 테스트(`desktop_language_acceptance`)를 두 바인딩에서 깨뜨려
>   되돌렸습니다. 앱 쪽 수정은 필요 없다고 봅니다.
>
> **요청:**
> 1. 위 파일로 재현합니다.
>    `setup_copy.sh <checkout> origin/claude/friendly-bardeen-r6xe8f <새 폴더> <tools/qt_port 경로>` 다음
>    `repeat_module.sh <새 폴더> tests.desktop_market_tabs_acceptance 80`, 또는 `gdb_until_abort.sh`.
> 2. 원인을 좁힙니다. 다음을 각각 반복해 봅니다.
>    - `SearchZoomTests`만 실행해서, 앞 테스트(`MarketTabsTests`)가 남긴 상태가 필요한지 확인
>    - 모듈에서 문제 테스트만 빼고 실행
>    - 사본에서 후보를 하나씩 끈 변형: 차트 미리보기 `on_snapshot`, 실시간 연결, 오른쪽 열 카드 불러오기, 상세
>      프로필 불러오기
>    - 필요하면 ASan으로 빌드한 Qt/PySide6
> 3. 두 바인딩에서 다 되는 고침을 정합니다. OS 세션은 `quantgen_desktop/**`·`tests/desktop_*`를 고치지 않으므로,
>    위치와 고침을 UI 세션에 넘기거나(인계 문서 또는 세션 메시지) 소유자에게 보고합니다.
> 4. 고친 뒤 같은 부하로 PySide6에서 같은 모듈을 **연속 150번 이상** 돌려 비정상 종료 0을 확인합니다(재현율 약 3%를
>    놓칠 확률 1% 미만). PyQt6 결과가 바뀌지 않았는지도 확인합니다. `PYSIDE6_TRIAL_2026-11-17.md`에 절을 추가하고,
>    9절 판정에 이 문제를 적습니다.
>
> **지킬 것:** `.env`(이름만, 값 금지), `docs/asset_expansion/cache/`, `~/.nextgen`, `tools/nautilus/**`, 고정 하네스,
> 연구 브랜치는 건드리지 않습니다. 패키지 저장소 말고 새 네트워크 호스트를 쓰지 않습니다. 인계 기록에는 비밀 값을
> 쓰지 않습니다. 한국어로 보고합니다.
>
> **끝 기준:** 원인 위치(파일:줄 또는 Qt/PySide6 쪽 원인)와 근거, 두 바인딩에서 같은 고침, PySide6 150회 연속 0건과
> PyQt6 불변 기록이 OS 브랜치 문서와 handoff LEDGER(OS 측 ID)에 남은 상태.
