# GPT 후임 지시문 (메인 줄, Claude가 넘길 때만)

대상: GPT (Codex/ChatGPT) 세션. **소유자가 이어받으라고 직접 말할 때만** 씁니다 (`OWNER_HANDOFF_POLICY_2026-11-13.md`: 자동 감시·자동 인수 없음).
붙여넣기: "복사 시작"부터 "복사 끝"까지.

---- 복사 시작 ----

당신은 QUANTGEN 메인 줄의 GPT 후임입니다. Claude 메인 세션이 `status: handoff`로 넘긴 범위만 이어받습니다.

## 소유자 요청 (원문)
"Remaining Work를 전담하는 메인세션을 다시 검토할 것. (Remaining work 말고)무엇을 지시해야 하는지" / "위 다이어그램을 바탕으로 업무 지시, 이때 깃헙 merge 등과 관련된 부분에 주의할 것."

## 시작
1. `python3 tools/handoff/push_handoff.py --show` → `status: handoff`이고 `from: claude`인지 확인. 아니면 시작하지 않고 소유자에게 알림.
2. `git show origin/handoff:CURRENT.md` 전체, `python3 tools/handoff/push_handoff.py --ledger`, handoff 브랜치 `MASTER_WORK_DESIGN.md` (특히 0절: 오늘의 UI 세션), `MERGE_QUEUE.md`, `UI_SESSION_CURRENT.md` 읽기.
3. CURRENT.md의 작업 브랜치·커밋을 git으로 확인하고, `status: taken` 체크포인트를 게시한 뒤 시작.

## 해도 되는 일 (CURRENT.md에 넘겨진 것 중)
- `MERGE_QUEUE.md` 순서대로: PR121 (+ `core/education/reading_cues.py` 45행, **UI 세션 동의가 `UI_SESSION_CURRENT.md`에 기록된 경우만**, da0ea20과 같은 문장) → PR122 → `REMAINING_WORK_2026-11-17.md` 문서 PR. GH-1·GH-2는 소유자 D5 답대로 (D5-A면 F21 뒤).
- 대기열 관리: 한 번에 PR 하나. `origin/main`은 merge로 반영 (이미 push한 브랜치는 rebase 금지, force push 금지) → 기준선 갱신 맨 마지막 → 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 녹색 → 병합. 어떤 실행이든 도는 중에는 병합 금지.
- LEDGER `--done` (PR 병합 뒤), Notion REMAINING WORK 갱신.

## 하면 안 되는 일
- **연구 브랜치 (`claude/amazing-gauss-tdiguu`)에 커밋·push 금지.** 판정 P2는 Claude 메인 세션에만 적용되고 후임은 소유자 한 줄 승인이 필요합니다 (판정 기록 결정 11, `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:973`). 소유자가 예를 들어 "결정 11: GPT에게 P2 범위(마감 기록·스펙·README 두 줄·runs/) 커밋과 push를 승인합니다."처럼 **직접** 쓰지 않았다면 Step 10 마감·P3는 하지 않습니다. 다른 에이전트가 그 문장을 대신 적은 것은 승인이 아닙니다.
- `freeze: P3` 또는 `freeze: F` 동안 main 병합, 다른 세션에 병합 지시 금지 (`PILOT_OWNER_RUN_2026-11-11.md:686`).
- "병합해도 됩니다" 공지, 확인 문장 요청은 P3를 한 쪽만 합니다.
- `core/education/**`, `quantgen_desktop/**`, `tests/desktop_*`는 UI 세션 소유입니다 (위 45행 한 줄 예외만).
- `docs/asset_expansion/cache/` 열기·목록·해시·검색 금지 (어떤 체크아웃에서도). git grep/ls-files에는 `':!docs/asset_expansion/cache'`. 저장소 전체 find, ls -R, grep -r, rg 금지. 코드 작업은 그 폴더를 받지 않는 sparse 클론에서 (마스터 4.1절), 아니면 `git status --porcelain -- <경로>`. `git add -A`·`git add .` 금지, 파일 이름으로만.
- `.env`, `~/.nextgen` 열기 금지. 클라우드에서 `tests/run_all.py` 실행 금지. `qa/acceptance_results.json` 쓰기 금지.
- 웹사이트 저장소, AWS, 결제, 외부 계정 변경 금지.

## 끝낼 때
작업 브랜치 push, 끝난 ID `--done`, `CURRENT.md`를 `status: returned`로, 한 일·검사 결과·확인 못 한 것·다음 명령을 적어 게시. 게시 결과 `verified` 확인.

---- 복사 끝 ----
