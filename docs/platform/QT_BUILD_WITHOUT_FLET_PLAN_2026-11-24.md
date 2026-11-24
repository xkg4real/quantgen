# Qt 빌드에서 Flet 빼기 계획 (O7, 2026-11-24)

- 작성: OS_EXPANSION 세션. 기준: main `de32ea1`. 이 문서는 **계획**입니다. 화면 파일(`quantgen_desktop/**`, `ui/**`)은 읽기만 했고, 실제 이동은 UI 세션·메인과 정한 뒤 합니다.
- 왜: 네이티브(PyQt6/PySide6) 판매 빌드에 Flet 실행 파일이 들어갑니다. 실측(Linux PyQt6 빌드, `be60b2a`): 앱 폴더 589 MB 중 `flet_desktop` 64 MB(Flutter·GTK 플러그인, glibc 2.38 요구 파일 포함), `flet` 0.3 MB, 그리고 flet-web → uvicorn을 거쳐 들어온 `uvloop` 16 MB·`httptools` 1.8 MB·`watchfiles` 1.2 MB. Windows·macOS 빌드도 같은 경로로 들어갑니다(`LINUX_DIFFERENCES_2026-11-24.md` 9번).

## 1. 원인 두 가지

1. **화면 코드가 `ui.*`를 부름**: `quantgen_desktop`의 다섯 모듈이 함수 안에서 `ui.*`를 import합니다(아래 2절). 그중 `ui.macro_state_panel`·`ui.macro_cards_view`·`ui.research_view`는 맨 위에서 `import flet`을 합니다. 실측: 앱 시작과 `quantgen_desktop` 전 모듈 import 때는 flet이 안 불러와지고, 매크로 기록 화면이 `ui.macro_cards_view`를 부르는 순간 불러와집니다.
2. **spec이 `ui/` 전체를 숨은 import로 넣음**: `packaging/quantgen_desktop.spec`의 `hidden`이 `core`·`data`·`ui`·`quantgen_desktop`의 모든 모듈을 넣으므로, 1번을 고쳐도 `ui/*.py`가 flet을 끌고 옵니다.

`ui/__init__.py`는 비어 있어, flet을 쓰지 않는 `ui.narrative_sections`는 불러와도 flet이 따라오지 않습니다(실측).

## 2. `quantgen_desktop`이 부르는 `ui.*` 이름 (전부)

| 부르는 곳 | `ui` 모듈 (맨 위 flet?) | 이름 | 순수? (flet 안 씀) | 딸려 가는 모듈 안 이름 | 옮길 곳(제안) |
|---|---|---|---|---|---|
| `macro_records.py:73,242,294` | `macro_state_panel` (**예**, 767줄) | `load_view` | 예 | `DECISIONS`, `ROOT`, `_newest_quarantine`, `_read`, `_with_live_acks`, `owner_items` (약 100줄) | `core/ficc/macro_state.py` (새) |
| 〃 | 〃 | `live_missing` | 예. **`config.kis_ready()`를 부름(키 접근 자리)** | — | 〃 |
| 〃 | 〃 | `verdict_of` | 예 | — | 〃 |
| 〃 | 〃 | `_book_ids` | 예 | `WEIGHT_BOOKS` | 〃 |
| 〃 | 〃 | `composition_lines` | 예 | `BOUND_KEY`, `_isnum`, `_num` | 〃 |
| `macro_records.py:67,188` | `macro_cards_view` (**예**, 483줄) | `load_inputs` | 예 | `ROOT`, `TF_DOCS`, `_json` | `core/ficc/macro_cards.py` (새) |
| 〃 | 〃 | `GROUPS`, `VERDICTS` (상수) | 예 | — | 〃 |
| 〃 | 〃 | `_group`, `_reason` | 예 | — | 〃 |
| `macro_records.py:70,218` | `research_view` (**예**, 303줄) | `load_inputs` | 예 | `COUNCIL`, `PAGES`, `ROOT`, `SPEC`, `council_resolutions`, `dnb_titles` | `core/research/macro_research_inputs.py` (새) |
| 〃 | 〃 | `DISCLAIMERS`, `WEIGHT_CAPTION`, `PAGES` (상수) | 예 | `COUNCIL`, `ROOT` | 〃 |
| `narrative_view.py:32`, `market_narrative_language.py:218`, `portfolio.py:135`, `risk_display.py:98,118,230` | `narrative_sections` (**아니오**, 456줄) | `ko_terms`, `organise`, `korean`, `_bound_note_korean`, `_jump_note_korean`, `drift_note_korean` | 예(모듈 전체가 `re`·`typing`만 씀) | — | `core/narrative_sections.py` (모듈째 이동) |

조사 방법: `git show origin/main:<파일>`을 AST로 읽어 `ui`로 시작하는 import를 모았고, 각 이름이 정의된 모듈 안에서 부르는 이름을 따라가며 import한 이름(`ft` 등)을 쓰는지 셌습니다. 20개 이름 모두 `ft`·`flet`을 쓰지 않습니다. `core/ficc/`·`core/research/`에 위 새 모듈 이름과 겹치는 파일은 없습니다.

## 3. 옮기는 순서 (UI 세션·메인과 정한 뒤)

1. 위 이름과 딸린 정의를 새 `core` 모듈로 **그대로 옮김**(내용 변경 없음).
2. 원래 `ui` 모듈은 그 자리에서 `from core.ficc.macro_state import load_view, ...`처럼 **다시 내보냄** → Flet 앱(`main.py`, `ui/**`)과 기존 시험은 바뀐 것을 모름.
3. `quantgen_desktop` 다섯 모듈의 import를 `core` 쪽으로 바꿈(UI 세션 파일).
4. spec: `hidden`에서 `ui`를 빼고, `excludes`에 `flet`, `flet_desktop`, `flet_web`, `flet_cli`, `fastapi`, `uvicorn`, `starlette`, `uvloop`, `httptools`, `watchfiles`를 더함(OS 몫). `selfcheck.sale_build_contents`에 이 이름들이 없을 것을 더함.

## 4. 동작이 같음을 고정할 시험

| 시험 | 무엇 |
|---|---|
| 새 `tests/qt_build_no_flet_acceptance.py` | (가) 옮긴 이름마다 `ui.X.name is core.Y.name`(같은 객체 — 다시 내보내기가 사본이 아님). (나) `quantgen_desktop`·`core`·`data`의 모든 `.py`를 AST로 읽어 `ui`·`flet`을 import하는 곳이 0. (다) 새 프로세스에서 `quantgen_desktop` 전 모듈 + 옮긴 `core` 모듈을 import해도 `"flet" not in sys.modules` |
| 기존 그대로 통과해야 할 것 | `tests.desktop_macro_acceptance`, `tests.macro_ui_views`, `tests.macro_ui_overlay`, `tests.macro_ui_rulings`, `tests.flet_korean_narratives_acceptance`, `tests.desktop_bonds_portfolio_language_acceptance`, `tests.chart_reading_acceptance`, `tests.strategy_lab_display_acceptance`(이 모듈 이름들을 직접 부르는 시험) |
| **함께 고칠 것** | `tests.gateway_boundary_acceptance`: `SCREEN_FILES`에 `ui/macro_state_panel.py`가 있고, 옮길 `live_missing`이 `config.kis_ready()`(키 함수)를 부름 → 키 접근 자리가 화면 파일에서 `core`로 옮겨 감. 경계 시험의 셈(`SCREEN_CEILING` 22파일/44곳)과 KEY-5 계획을 PAYMENTS가 맞춰야 함 |
| 빌드 | Linux PyQt6 빌드 + `--selfcheck`(`sale_build_contents`에 flet 없음), `tools/packaging/linux_runtime_report.py`로 glibc 하한 재측정, 매크로 기록 화면을 여는 데스크톱 시험(`tests.desktop_macro_acceptance`)을 동결 빌드 밖에서 통과 |

## 5. spec에서 flet을 뺄 수 있게 되는 조건

1. 4절 (나) 시험이 통과: `quantgen_desktop`·`core`·`data` 어디에서도 `ui`·`flet`을 import하지 않음.
2. `hidden`에 `ui`가 없음(`packaging/quantgen_desktop.spec`).
3. 빌드한 앱의 selfcheck가 통과하고(앱 import), `_internal`에 `flet*`·`uvicorn`·`uvloop` 등이 없음.
4. 매크로 기록 화면이 동결 빌드에서 열림(수동 또는 offscreen 시험).

순서상 1·2를 같은 PR에서 해야 합니다. 1만 하면 2 때문에 여전히 flet이 들어가고, 2만 하면 매크로 기록 화면이 동결 빌드에서 `ModuleNotFoundError`가 납니다.

## 6. 모바일(Flet) 빌드에 미치는 영향

| 항목 | 영향 |
|---|---|
| 동작 | 없음: `ui` 모듈이 같은 이름을 다시 내보내므로 `main.py`·`ui/**`는 그대로 |
| 묶음 | `tools/packaging/stage.py --profile mobile`은 `core/**/*.py`를 이미 넣으므로 새 `core` 모듈이 자동으로 들어감. 크기 변화는 옮긴 코드만큼(수백 줄)이며 늘거나 줄지 않음 |
| Qt 없음 검사 | 모바일 묶음은 `quantgen_desktop` 중 Flet이 부르는 모듈에 Qt import가 있으면 거부함. 새 `core` 모듈은 Qt를 쓰지 않으므로 영향 없음 |
| Flet 의존 | 모바일 앱은 계속 flet을 씀. 이번 계획은 **Qt 빌드에서만** flet을 뺌 |

## 7. 얻는 것과 몫

- 예상 감소(Linux 실측 기준): `flet_desktop` 64 MB + `uvloop`·`httptools`·`watchfiles` 약 19 MB + `flet`·`fastapi`·`uvicorn`·`starlette`(순수 파이썬, 압축 아카이브 안). 판매 빌드에 Flutter·GTK 계열 고지와 glibc 2.38 파일 일부가 빠짐. 실제 수치는 옮긴 뒤 다시 빌드해 확인.
- 몫: 1~3단계(이름 이동·다시 내보내기·`quantgen_desktop` import 변경)는 UI 세션과 `core` 소유 세션(메인이 정함), 게이트웨이 경계 셈은 PAYMENTS, 4단계 spec·selfcheck와 빌드 확인은 OS.
