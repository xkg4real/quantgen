# 공통 규칙 (모든 세션 지시문에 이미 들어 있음, 참고용)

출처: `docs/product/PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md:93-110` (0.3절)과 2.2절, `CLAUDE.md`, `origin/handoff:OWNER_HANDOFF_POLICY_2026-11-13.md`, `origin/handoff:AGENTS.md` §6, `tools/compliance/check.py:278-286, 560-577`, 마스터 파일 0절·4절.

1. **시작.** `python3 tools/handoff/push_handoff.py --show`와 `--ledger`를 먼저 실행합니다. handoff 브랜치의 `MERGE_QUEUE.md`, `MASTER_WORK_DESIGN.md`, `UI_SESSION_CURRENT.md`도 읽습니다. 다른 담당이 `taken`이면 겹치는 일은 시작하지 않습니다. 소유자가 맡긴 범위만 합니다. 자동 인수는 없습니다 (2026-11-13 운영 지시).
2. **오늘의 UI 세션.** `claude/friendly-bardeen-r6xe8f`에서 Claude UI 세션이 소유자의 11-17 요청을 끝내고 (main 미병합, 인계 `c73ff11`) 소유자 PNG 확인을 기다립니다 (마스터 0절). `core/education/**`, `quantgen_desktop/**`, `tests/desktop_*`는 UI 세션 동의 없이 고치지 않습니다 (같은 화면을 두 에이전트가 따로 고치지 않음, handoff `AGENTS.md` §6).
3. **캐시 폴더.** `docs/asset_expansion/cache/`는 어떤 브랜치·어떤 체크아웃에서도 열기·목록·해시·검색 금지. `git grep`, `git ls-files`에는 `':!docs/asset_expansion/cache'`를 붙입니다. 저장소 전체 `find`, `ls -R`, `tree`, `du`, `grep -r`, `rg` 금지. 루트는 `git ls-tree --name-only origin/main` (`-r` 없이). `docs/`는 필요한 하위 폴더만.
   - 그 폴더가 디스크에 있는 체크아웃에서는 경로 없는 `git status`도 그 폴더를 훑습니다. 그래서 코드 작업은 그 폴더를 받지 않는 sparse 클론에서 합니다:
     ```bash
     git clone --no-checkout <저장소 URL 또는 로컬 경로> "$SCRATCH/wt"
     git -C "$SCRATCH/wt" sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
     git -C "$SCRATCH/wt" checkout <브랜치>
     test ! -e "$SCRATCH/wt/docs/asset_expansion/cache" && echo "no cache folder" || echo "STOP: the cache folder is on disk"
     ```
     "no cache folder"를 본 뒤에만 진행합니다. 로컬 경로에서 복제했다면 push 전에 `git -C "$SCRATCH/wt" remote set-url origin <GitHub URL>`.
   - sparse 클론을 못 쓰는 곳에서는 `git status --porcelain -- <경로>`, `git diff -- <경로>`처럼 늘 경로를 줍니다.
   - `git add`는 파일 이름으로만 합니다. `git add -A`, `git add .`, `git commit -a`는 쓰지 않습니다.
4. **비밀.** `.env`, `~/.nextgen`은 열지 않습니다. 변수 **이름**만 적습니다. 값은 문서·커밋·로그·채팅 어디에도 쓰지 않습니다.
5. **전체 테스트.** 클라우드에서 `tests/run_all.py` 실행 금지. `qa/acceptance_results.json`은 쓰지 않습니다 (소유자 Windows 실행 결과만). 개별 검사는 `python -m unittest tests.<모듈>`.
6. **준수 기준선.** 감시 파일을 바꾸면 최신 main을 merge한 뒤 **맨 마지막에**
   `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상 구체적 설명>"`
   → `python -m tools.compliance.check --check`. 파일을 더하거나 빼면 20개 문서 전부 재검토이므로 PR 설명에 적습니다.
7. **병합.**
   - handoff 브랜치 `MERGE_QUEUE.md`의 순서와 `freeze:` 줄을 따릅니다. `freeze: P3` 또는 `freeze: F`이면 병합도, 병합 지시도 하지 않습니다.
   - 최신 main은 `origin/main`을 브랜치에 **merge**해서 반영합니다. 이미 push한 브랜치는 **rebase하지 않습니다** (rebase에는 force push가 필요). force push 금지.
   - **녹색 = 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 성공.** 지금은 Compliance 1개, 그리고 Runtime이 뜨면 syntax 2개와 설치 4개입니다. GH-1 뒤에는 Runtime 작업 수가 줄어듭니다. 숫자가 아니라 "띄운 것 전부"가 기준입니다.
   - 어떤 실행이든 도는 중에는 병합하지 않습니다 (PR119 사례).
   - Runtime의 `pull_request` 경로 목록 (`.github/workflows/runtime-smoke.yml:5-9`)에 없는 경로만 바꾸면 Runtime이 뜨지 않습니다. 자기 테스트가 어느 CI 단계에서도 돌지 않는 PR은 병합하지 않습니다. 각 레인의 첫 코드 PR이 자기 경로와 테스트 모듈을 그 워크플로에 더합니다 (공유 파일이라 대기열 경유).
8. **LEDGER.** 덧붙이기만. 시작 전 ID 중복 확인, PR 병합 뒤 기록.
9. **인계.** 작업 단위마다 자기 인계 파일을 갱신합니다. `push_handoff.py`는 지금 `CURRENT.md`만 게시합니다. 다른 파일은 메인이 `--doc`을 추가하기 전까지 손으로 커밋합니다: handoff 브랜치를 받아 → 자기 파일만 수정 → `handoff: <세션> <상태>`로 커밋 → force 없이 push → `git show origin/handoff:<파일>`로 다시 읽어 확인. 아직 시작하지 않은 레인의 파일은 `status: idle`입니다. 일을 시작할 때 `checkpoint`로 바꿉니다.
10. **외부 변경 금지.** 웹사이트, AWS, 결제, 외부 계정, 저장소 설정은 소유자 승인 없이 바꾸지 않습니다.
11. **결정 번호.** `D1`~`D14`는 소유자 보고서(`OWNER_REPORT_2026-11-17.md`)의 결정입니다. 옛 `Q` 번호는 마스터 부록 G에서 찾습니다. 답이 없는 결정에 걸린 작업은 시작하지 않습니다.
