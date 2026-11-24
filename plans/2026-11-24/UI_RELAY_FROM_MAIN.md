# 메인 → UI 세션 전달문 (소유자가 UI 세션에 붙여 넣는 용도) · 2026-11-24

메인은 UI 세션에 직접 보내지 않는다(소유자 규칙). 아래는 UI PR #140(`gpt/ui-guide-chart-first-20261121` @ `3483b53`)을 이어가는 쪽이 누구든 알아야 할 것이다. 누가 이어갈지는 소유자 결정 대기(OA-48).

## 붙여 넣을 글

> 메인 세션이 PR #140에서 확인한 것입니다. 고칠 때 참고해 주세요.
>
> 1. **PySide6에서 깨지는 곳 1곳.** `quantgen_desktop/stock_insights.py:82`의 `self.metric = ...`이 `QWidget.metric()`(Qt 가상 함수)을 가립니다. PyQt6는 클래스만 봐서 괜찮지만 PySide6 6.12는 인스턴스 속성을 가상 함수 재정의로 불러 `Error calling Python override of QWidget::metric()`가 납니다. 속성 이름을 바꾸면 됩니다(예: `metric_key`). OS 세션이 이런 이름 충돌을 잡는 lint 규칙 16-shadow를 만들었고(브랜치 `claude/os-qt-lint-shadow-20261124` @ `0a92e58`, 곧 main), PR #140 전체에서 이 한 곳만 잡힙니다.
> 2. **지금 CI 실패는 위와 다른 문제입니다.** Ubuntu 3.12·Windows 3.11에서 `tests/desktop_stock_detail_acceptance.py:1527`(포커스 확인)이 실패합니다. 바인딩과 무관합니다. main과의 충돌도 있습니다.
> 3. **`config.py`의 KIS 허용 목록에 `inquire-ccnl`이 추가돼 있습니다.** 병합되면 Nautilus 코드 지문이 다시 바뀝니다. 필요한 변경이면 PR 본문에 이유를 적어 주세요(소유자 확인 항목 OA-53).
> 4. **KEY-5 남은 화면 접점.** 요청문 v2는 handoff `plans/2026-11-24/KEY5_UI_REQUEST_V2.md`입니다(PR #140 기준 8파일 25곳). PR #140이 main에 들어간 뒤 진행합니다.
> 5. **macOS 표시(급하지 않음).** 단축키 문구가 "Ctrl"로 고정돼 있습니다. `QKeySequence.toString(QKeySequence.NativeText)`로 바꾸면 Mac에서 ⌘로 보입니다. 도움말에 `QKeySequence.StandardKey.HelpContents` 추가, (선택) 트랙패드 핀치 확대, (선택) Mac 편집 메뉴. 근거는 `docs/platform/MACOS_DIFFERENCES_2026-11-24.md` 4절(브랜치 `claude/os-macos-differences-20261124`, 곧 main).
> 6. PR을 고친 뒤에는 `docs/product/ui_website_updates/PR-140.json`을 함께 갱신해 주세요.

## 메인이 확인한 근거

- 1번: OS 세션 실측(PySide6 6.12.0과 PyQt6 6.12.0에서 같은 위젯을 띄워 비교, 저장소 밖 실험)과 lint 결과(main 0건, PR #140 1건). 메인은 lint 브랜치의 시험 21개 통과를 통합 묶음에서 다시 확인했다.
- 2번: PR #140의 CI 기록(2026-11-24 메인 확인).
- 3번: `plans/2026-11-24/RESUME_GPT_VERIFY.md`.
- 5번: OS 세션의 화면 파일 읽기 조사. 실제 Mac 화면에서는 미검증.

## 덧붙임 (2026-11-24 21:00 KST, OS_EXPANSION O2 결과)

- `tests/desktop_stock_detail_acceptance.py:1527`(포커스 검사)는 **PyQt6 원본(PR #140 head `3483b53`)에서도 5회 중 5회 같은 단언으로 실패**한다. PySide6 사본에서는 먼저 `quantgen_desktop/stock_insights.py:82`의 `self.metric` 때문에 TypeError로 죽고, 그 속성 이름만 `_metric`으로 바꾸면 3회 중 3회 PyQt6와 같은 1527 단언에서 실패한다. 즉 1527은 PySide6 전환과 무관한 UI 쪽 포커스 로직 또는 시험 문제이고, `self.metric`은 별개의 PySide6 전용 문제다.
- PySide6 재확인: `tests.desktop_market_tabs_acceptance` 4개 동시 실행, 일반 160/160, tcache 끔 160/160, 비정상 종료 0. 전환 도구 `switch_day.py --check`는 7곳 모두 적용 가능(누락·모호 0).
