---
status: checkpoint
reason: milestone
from: claude
task: os-expansion
cycle: 2026-11-17
done_ids: none
next_ids: OS-P0-a, OS-P0-e, OS-P0-f, OS-P0-c, OS-P0-b, OS-P0-d, OS-F1
updated_at: 2026-11-17T22:05:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/os-prep-20261117
work_commit: 600fcb0
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-24T17:00:00+09:00
session: https://claude.ai/code/session_016uB1jgXiwx42FSUU5ANwM7
---

# 인수인계: QUANTGEN/MAIN -> OS_EXPANSION (PySide6 전환 준비, 패키징, 모바일)

운영 기준: [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md). 지시문: `plans/2026-11-17/sessions/04_OS_EXPANSION.md` (이 세션의 첫 지시, 전체가 기준).

## 0. 한 줄 요약

OS-P0-a(변환 도구·위험 패턴 검사) 코드를 `claude/os-prep-20261117` `600fcb0`에 push했습니다(병합 전이라 LEDGER에는 아직 없음). 지금 OS-P0-e 정식 시범(main `5888d05`·UI `bec272b` × PyQt6/PySide6)이 이 세션 스크래치에서 돌고 있습니다.

## 1. 목표와 완료 조건

- **소유자 원문 (2026-11-17, `owner_answer_1117.txt`):**
  > 2. D9 : 만약 개발이 F까지 완료된 뒤 Pyside6 전환 시 전환에 소요되는 예상 시간이 24시간을 초과한다면 지금 진행할 것. 그게 아니라면 권장대로 승인

  > 1. D6 : 현재 메인세션의 하부 세션 (QUANTGEN/TRADEGEN -> TRADEGEN_GITHUB 과 같은 구조)으로 3가지를 생성할 것. 이때 이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것.
- **소유자 원문 (2026-11-16, Notion `34f5c916fe0c800b9b4af35c80ebe778`):**
  > 앱의 플랫폼 확장과 관련해서 다음과 같은 항목들을 고려해서 (1)문서 수정(할 필요 있으면 수정)할 것, (2) 당장 실행 가능한 것 (병렬로, github merge 순서 등에 따라 앱의 구성 등이 다르면 원래 주어진 급한 Task (i.e. Remaining Work))이 끝난 다음 진행하도록 미리 파이프라인 구축만 해놓을 것
- **완료 조건:** 지시문 7절(작업 1~3)과 8절 표의 ID별 완료 조건.
- **범위 밖:** `quantgen_desktop/**`·`tests/desktop_*`·`core/education/**`·`ui/**`·`assets/**` 커밋(UI 세션 소유), 연구 브랜치, `config.py`·`data/**`(OS-F2 전), 결제·계정 경로, main 병합(메인이 함), 외부 변경.

## 2. 근거

| 종류 | 위치 | 쓰는 부분 |
|---|---|---|
| 지시문 | handoff `plans/2026-11-17/sessions/04_OS_EXPANSION.md` | 전체 |
| D9 보고서 | handoff `plans/2026-11-17/D9_PYSIDE6_ESTIMATE.md` | 1절 개수, 4절 11묶음, 7절 점검표·나안 |
| 병합 순서 | handoff `MERGE_QUEUE.md` (2026-11-17T21:56, `freeze: none`) | OS 전환 PR은 F21 바로 뒤 첫 자리 |
| CI 단계 | main `.github/workflows/runtime-smoke.yml` (Qt 설치 줄 뒤 unittest 17개, UI 브랜치 18개) | 시범 단계 목록 |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안 |
|---|---|---|
| 변환은 토큰 단위(이름·import·정확히 바인딩 이름인 문자열·문자열 안 파이썬 코드)로, 설명 문구는 안 바꿈 | 설명 문구("PyQt6 네이티브" 등 13곳)는 OS-F1에서 의도해 고칠 대상이고, 정규식 전체 치환은 문서·주석까지 바꿈 | D9 시범의 단어 전체 치환 |
| `sip.isdeleted(x)` → `(not shiboken6.isValid(x))`, `not sip.isdeleted(x)` → `shiboken6.isValid(x)` | 괄호로 우선순위를 지키고 이중 부정을 없앰 | 대체 객체(`sip = SimpleNamespace(...)`) — 읽기 어렵고 lint가 못 잡음 |
| `--apply`는 `.git`이 있는 폴더를 거부 | 저장소 체크아웃을 실수로 바꾸지 않게 (`quantgen_desktop/**`는 UI 소유) | — |
| 시범의 PySide6 쪽은 `font_policy.py`에 시범 전용 shim(대체 글꼴 등록 건너뜀)을 스크래치에서만 적용 | D9와 같은 조건이어야 비교 가능, 안 하면 `QChar` ImportError로 거의 모든 Qt 테스트가 시작 전 실패 | shim 없이 실행 (D9가 이미 263건으로 기록) |
| compliance 기준선은 지금 갱신하지 않음 | 지시문 9절 4번: 최신 main merge 뒤 PR 직전 맨 마지막에 | 지금 갱신 — 다른 PR과 충돌 |

## 4. 진행 상황

- [x] OS-P0-a 코드 — `tools/qt_port/pyqt6_to_pyside6.py`, `tools/qt_port/__init__.py`, `tests/qt_port_acceptance.py`, 커밋 `600fcb0` (push됨, 병합 전)
- [ ] OS-P0-e 정식 시범 ← **실행 중** (스크래치, 결과 문서 `docs/platform/PYSIDE6_TRIAL_2026-11-17.md`·`PYSIDE6_UI_CHECKLIST.md` 작성 예정)
- [ ] OS-P0-f 글꼴 대안·세그폴트 재현
- [ ] OS-P0-c, OS-P0-b, OS-P0-d, OS-F1 (지시문 8절 순서)

**마지막으로 통과한 검증 (작업 브랜치 `600fcb0`):**

```
python -m unittest tests.qt_port_acceptance                      -> Ran 12 tests OK
python tools/qt_port/pyqt6_to_pyside6.py --check --ref origin/main
  -> files_importing=127, imports=333, signal=117, slot=62, sip=12, prose=13, changes=526  (D9: 127 파일, 약 531곳)
python tools/qt_port/pyqt6_to_pyside6.py --check --ref origin/claude/friendly-bardeen-r6xe8f   (bec272b)
  -> files_importing=132, imports=351, signal=135, slot=65, sip=12, prose=13, changes=565
--apply 두 번 (git archive 임시 복사본, main·UI 각각) -> 두 번째 files changed=0, diff -r 0, compileall OK (Python 3.12, PySide6-Essentials 6.12.0)
--lint --ref origin/main -> 83건: 1-print 1, 2-findChildren 1, 3-receivers 1, 4-combo-data 25(검토), 5-qobject-key 11, 6-deferred 38(검토), 8-font 4, 9-delegate 2
  D9 알려진 위치 모두 잡음: stock_report.py:164 print, desktop_operation_fixes_acceptance.py:119 findChildren,
  stock_detail.py:1470 receivers, font_policy.py:12/50/52/53 QChar·대체 글꼴, market_menu.py:203 집합 비교
--lint --ref UI(bec272b) -> 86건 (6-deferred만 +3)
git diff --stat origin/main -- quantgen_desktop 'tests/desktop_*'  -> 빈 출력
python -m tools.compliance.check --check -> consistency FAIL (새 파일 2개; 기준선은 PR 직전에 갱신, 9절 4번)
```

## 5. 중단 지점

OS-P0-e 시범 실행 중 (이 세션 스크래치 `trial/`, 다른 세션은 볼 수 없음). 끊기면 아래 6절 1번 명령으로 다시 만듭니다. 커밋 안 된 변경 없음.

## 6. 다음 할 일 (순서대로)

1. OS-P0-e — 스크래치에 `git archive <ref> -- quantgen_desktop core data ui tests tools assets config.py main.py pyproject.toml requirements.txt ':!**/*.jsonl' ':!**/holdout/**' ':!**/frozen/**'`로 두 벌, 한 벌은 `--apply` + 시범용 글꼴 shim; `runtime-smoke.yml`의 Qt 설치 단계 뒤 `python -m unittest` 명령을 `-f`만 빼고 순서대로, 명령당 `timeout 1500`, HOME·XDG_*를 스크래치로, `QT_QPA_PLATFORM=offscreen`. 완료 기준: 지시문 7절 작업 2의 1~4.
2. OS-P0-f — `tools/qt_port/font_probe.py`, `tools/qt_port/repro/` 세그폴트 최소 재현. 완료 기준: 지시문 7절 작업 3.
3. 그다음 지시문 8절 표 순서 (OS-P0-c → OS-P0-b → OS-P0-d).

## 7. 주간 지표 (D9 진척)

| 지표 | D9 시작값 | 지금 |
|---|---|---|
| 바인딩 때문에 새로 실패한 테스트 | 15 | 측정 중 (OS-P0-e) |
| 세그폴트 | 1 | 측정 중 |
| "이미 지워진 C++ 객체" 줄 | 223 | 측정 중 |
| 위험 패턴 (`--lint`, main / UI) | — | 83 / 86 (검토용 4·6묶음 포함) |
| F21 뒤 남은 예상 시간 | 약 30시간 (D9) | 갱신 전 |

## 메인에게

- 아직 대기열 요청 없음 (PR은 MERGE_QUEUE에서 OS 차례가 올 때만). LEDGER 기록 요청 없음 (병합된 ID 없음).
- 이 세션 브랜치: `claude/os-prep-20261117` (지시문과 같은 이름).

## UI 세션에 전할 것

(OS-P0-e 시범 결과가 나오면 소유자가 그대로 옮길 3~5줄을 여기에 적습니다.)

## 8. 주의사항 / 하지 말 것

- `docs/asset_expansion/cache/` 열기·목록·검색·해시 금지 (git 경로에 `':!docs/asset_expansion/cache'`). `.env`, `~/.nextgen` 열지 않음.
- `quantgen_desktop/**`, `tests/desktop_*`, UI 브랜치·`UI_SESSION_CURRENT.md`, 연구 브랜치 `claude/amazing-gauss-tdiguu` 고치지 않음.
- `CURRENT.md`(메인 소유)에 `push_handoff.py`를 파일 인자로 실행하지 않음. main 병합은 메인이 함. PR은 대기열 차례에만 (비공개 뒤 CI 유료).
