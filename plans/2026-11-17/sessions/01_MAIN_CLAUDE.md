# 메인 세션 (Claude) 지시문 — Remaining Work + 병합 관리 + GitHub 정리

대상: Claude 메인 세션 (session_01H6RrzMUzF8vwK8xkX977mB, task `claude-resume-20261103`; `origin/handoff:CURRENT.md`가 이름 붙인 세션이며 판정 P2가 주어진 세션).
붙여넣기: 아래 "복사 시작"부터 "복사 끝"까지.

---- 복사 시작 ----

당신은 QUANTGEN 메인 세션입니다. Remaining Work, main 병합 관리(병합 관리자), GitHub 정리를 맡습니다.

## 소유자 요청 (원문)
- "노션 <11 16 업무 지시 필요한 부분> 이거 정독하세요. 당신이 할수있는것은 당신이, 다른 업무는 어떤 세션이 분담하는것이 좋은지, 모든 준비를 끝내고 정리해서 저한테 보고합니다. 제가 승인하면 해당 작업 일괄진행합니다."
- "Remaining Work를 전담하는 메인세션을 다시 검토할 것. (Remaining work 말고)무엇을 지시해야 하는지"
- "위 다이어그램을 바탕으로 업무 지시, 이때 깃헙 merge 등과 관련된 부분에 주의할 것."
- "모든 repository 비공개로 전환, exploit 우려 때문"
- "당장 필요없는 test_npu.py 파일 등 깃헙 내부적으로 파일 정리가 필요할 듯, AI한테 아키텍쳐 한번씩 훑고 현재 및 향후 개발단계, 그리고 프로그램 구동에 하나도 필요가 없으면 삭제 지시"

## 소유자 결정
해당 결정: D1~D6, D11 (정책 문서 PR), D12 (결정 메모). 소유자가 "전부승인"이면 ★권장안, 번호별로 답하면 그 답을 따릅니다. 승인 메시지는 원문 그대로 `CURRENT.md`에 적고, main의 `OWNER_RULINGS_LOG.md`에는 F21 뒤에 옮깁니다 (`PILOT_OWNER_RUN_2026-11-11.md:680`과 같은 이유). 답이 없는 결정에 걸린 작업은 시작하지 않습니다.
번호 구분: D = 이번 보고서 결정 (옛 Q 번호는 마스터 부록 G), "판정 기록 결정 N" = `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "결정표 N번" = `docs/product/DECISIONS_PILOT_CLOSE_MERGE_2026-11-11.md`.

## 공통 규칙
1. 시작: `python3 tools/handoff/push_handoff.py --show`, `--ledger`. 다른 담당이 taken이면 겹치는 일 금지.
2. `docs/asset_expansion/cache/`는 어떤 ref·어떤 체크아웃에서도 열기·목록·해시·검색 금지. git grep/ls-files에는 `':!docs/asset_expansion/cache'`. 저장소 전체 find, ls -R, tree, du, grep -r, rg 금지. 코드 작업은 마스터 4.1절의 sparse 클론에서 ("no cache folder" 확인 뒤). 아니면 `git status --porcelain -- <경로>`처럼 늘 경로를 줌. `git add`는 파일 이름으로만, `git add -A`·`git add .`·`git commit -a` 금지.
3. `.env`, `~/.nextgen` 열지 않음. 이름만, 값은 절대 쓰지 않음.
4. 클라우드에서 `tests/run_all.py` 실행 금지. `qa/acceptance_results.json` 쓰지 않음 (모든 커밋에서 바이트 동일, md5 전후 확인).
5. 기준선 갱신은 최신 main을 merge한 뒤 맨 마지막: `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상>"` → `--check`.
6. 병합: `origin/main`을 merge로 반영 (이미 push한 브랜치는 rebase 금지, force push 금지). 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 녹색일 때만 병합. 어떤 실행이든 도는 중에는 병합 금지.
7. 웹사이트 저장소는 수정하지 않음 (2026-11-03 판정, `OWNER_RULINGS_LOG.md:314-315`).
8. 연구 브랜치는 P2 범위만: 마감 기록, 스펙, README 두 줄, `docs/nautilus_bridge/runs/`. `tools/nautilus/**`, `tests/nautilus_*.py`, 표, `owner_confirmed`, `host_fingerprint`, `NB-*` 폴더는 손대지 않음 (`OWNER_RULINGS_LOG.md:757`).
9. `core/education/**`, `quantgen_desktop/**`, `tests/desktop_*`는 UI 세션 소유입니다. 예외는 T2의 `reading_cues.py` 45행 한 줄이며, UI 세션 동의가 기록된 뒤에만 합니다.

## 맡는 경로
연구 브랜치 P2 범위, PR121·122 (GPT에서 인수), `.github/workflows/**`, `tools/handoff/**`, `CLAUDE.md`, `AGENTS.md`, `docs/nautilus_bridge/REMAINING_WORK_*.md`, 회원가입용 정책 문서 PR (`docs/compliance/**`), handoff 브랜치의 `MASTER_WORK_DESIGN.md`·`MERGE_QUEUE.md`·새 세션 인계 틀, 공유 파일 대기열 조정.

## 작업 (순서대로)

**T0. 승인 기록과 검증 체크포인트 (아무것도 바꾸기 전에).**
`CURRENT.md`를 `status: checkpoint`, `waiting_on: none`으로 다시 게시합니다 (준비 체크포인트 `0ae7045` 위에). 적을 내용 (모두 git으로 확인됨):
- 소유자 승인 메시지 원문.
- 파일럿 1 `a2ac79b`, 파일럿 2 `8a3d171`, Windows E `cdbbe61` (964행, 844 PASS, 0 FAIL, 120 NOT_RUN 모두 macro; `563db54` 대비 변화 0). `8a8c247`→`cdbbe61` 변경 파일은 GPT가 말한 5개뿐. 공급사 대조 요약 4개의 sha256이 GPT의 STEP10 검토표와 일치.
- 파일럿 2 run.json의 `engine.check_env.python` = 3.13.17 (venv 3.13.14, 런북 고정값 3.13.14). D3 답.
- main `e01e152`의 알려진 실패: '봉' 1개 + 옛 테스트 3개 (PR119 run 43454709190 설치 작업 4개 실패). PR121 (run 43478587544), PR122 (run 43478852671)는 '봉'에서 실패.
- 오늘 UI 세션의 `claude/friendly-bardeen-r6xe8f` `da0ea20`, 그 인계 handoff `c73ff11` (`waiting_on owner`, LEDGER 4행; 마스터 0절).
- next_ids 그대로 (⑦-1, ⑦-2, ⑨-3a/recorder/1, …). ID는 쉼표로, 백틱 없이.
완료 조건: 게시 결과 `verified`, 종료 코드 0.

**T1. 마스터·대기열·세션 틀 게시.**
- handoff 브랜치에 `MASTER_WORK_DESIGN.md` (초안 `MASTER_WORK_DESIGN_2026-11-17.md`), `MERGE_QUEUE.md` (`freeze: none`과 마스터 4.2절 표), `OS_SESSION_CURRENT.md`, `PAYMENTS_SESSION_CURRENT.md`, `DATA_SOURCE_SESSION_CURRENT.md`를 손으로 커밋합니다. 새 인계 파일 셋은 TEMPLATE.md 기반, **`status: idle`**, 첫 작업만 적음 (아직 시작하지 않은 레인이므로 `checkpoint`가 아님; `push_handoff.py:51`). force 없이 push, `git show origin/handoff:<파일>`로 다시 읽어 확인.
- Notion: QUANTGEN PROJECT 아래 마스터 사본 1쪽. REMAINING WORK의 낡은 줄 고침 (7-1, 9-3a의 "Runtime 대기" → 실패와 원인, 고칠 순서).
- 소유자가 "세션 생성 위임"이라고 썼다면: 지시문 04·05·06으로 Claude 세션 3개 (`xkg4real/quantgen`), 지시문 03으로 클라우드 세션 1개 (`xkg4real/website`)를 만들고 세션 주소를 보고.
완료 조건: `git show origin/handoff:MERGE_QUEUE.md`가 보이고, Notion 링크를 보고에 적음.

**T2. PR121 + '봉' 45행 (D1-A).**
선행 조건: D1-A 승인과 UI 세션 동의 (`UI_SESSION_CURRENT.md`의 동의 줄, 또는 소유자가 채팅에 옮겨 준 UI 세션 답). 동의가 없으면 `core/education/**`를 고치지 않고 소유자에게 묻습니다.
1. PR121 (`gpt/r3-recorder-20261114`, head `ea3d596`)을 GPT에서 인수한다고 `CURRENT.md`에 적음 (GPT는 `returned` 상태).
2. sparse 클론에서 그 브랜치를 받고 `origin/main`을 merge (이미 최신이면 생략).
3. 커밋 하나: `core/education/reading_cues.py` 45행을 `da0ea20`과 바이트가 같은 문장으로. 확인: `git diff origin/claude/friendly-bardeen-r6xe8f -- core/education/reading_cues.py`에 45행이 나오지 않음. 19행·35행은 건드리지 않음 (UI 세션 몫, 02 UI-8).
4. 기준선 갱신 맨 마지막 → force 없이 push.
5. 모든 작업 녹색까지 기다림. 앞서 건너뛴 세 단계 ('recorded owner decision and readiness display', 'indicator education and locale contracts', 'Retain the verified installable wheel')의 결과도 확인. 새 실패가 나오면 고치기 전에 원인과 소유 세션을 보고.
6. 병합 → LEDGER `⑨-3a/recorder/1/lifecycle` (행에 45행 수정과 UI 세션 동의를 적음; 별도 ID 없음) → `UI_SESSION_CURRENT.md`에는 손대지 않고 소유자에게 "PR121 병합, UI 세션은 main을 merge할 때 시장 테스트를 자기 판으로" 한 줄 보고.
D1-B를 고르셨다면: UI PR이 먼저 병합된 뒤 PR121에 main을 merge하면서 `tests/desktop_home_markets_markets_acceptance.py`는 main(UI) 판을 쓰고 ea3d596의 그 두 블록은 버림. 나머지는 같음.
완료 조건: PR121 병합, CI 링크 기록, main 정확한 head의 Runtime 녹색.

**T3. ⑦-1 Step 10 마감 커밋 (연구 브랜치, T2와 병렬 가능).**
근거: 판정 P2 (`OWNER_RULINGS_LOG.md:757`)는 이 세션에 주어졌고, 결정 10 (:972)이 이 세션의 마감 커밋 push를 맡깁니다. 두 파일럿과 E가 올라온 뒤에만 올리고, 올릴 때마다 커밋 번호를 바로 보고합니다. 결정 11 (:973)은 후속 세션에만 적용되므로 이 세션에는 추가 승인이 필요 없습니다. 선행 조건: D3, D4 답.
`PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md` 2.2~2.10을 그대로 따릅니다.
1. 2.2의 캐시 없는 sparse 클론 (`'/*' '!/docs/asset_expansion/cache/'`), "no cache folder" 확인 뒤에만 진행. 브랜치 `claude/amazing-gauss-tdiguu` `cdbbe61`.
2. 2.9 diff 확인: BASE `8a8c247`. 필터한 `git diff --name-only 8a8c247 HEAD`가 비어야 함. 출력 기록.
3. `git show 77d2647:results/<run>/summary.json > docs/nautilus_bridge/runs/<run>/provider_parity_summary.json` (PP-20261111T051909Z-spy, PP-20261112T073747Z-spy, PP-20261111T075307Z-rf, PP-20261111T075328Z-btc). sha256을 STEP10_CHANGE_REVIEW 표와 대조. **결정 18 (:980):** SPY는 첫 요약 (PP-20261111T051909Z-spy, WITHHELD)과 나중 요약 (PP-20261112T073747Z-spy, PASS)을 **둘 다** `runs/`에 복사하고, 마감 기록에 **파일럿 1 관문에 쓴 것은 나중 요약**이라고 적음 (STEP10_CHANGE_REVIEW 13행과 대조).
4. README 937·938행만 바이트 교체 (nautilus 칸 '57 PASS'; Total '844/964 passed, 0 failed, 120 not run (2026-11-14, Windows)'). CRLF 유지. `git diff --numstat` = `2 2 README.md` (결정 12, 14).
5. 실행 기록 (파일 이름 유지, 결정 15)에 `## Step 10 close-out (<날짜>)`와 2.3의 11개 제목. 첫 문단에 근거 (P2, 결정 10)와 D3·D4 답 원문. §8 편차에 파일럿 2의 Python 3.13.17 (D3), §6에 첫 E 시도 (843/1 FAIL/120, L2-01)와 venv 업그레이드는 "소유자 보고, 미검증", §9에 11-11 두 번의 탐색 날짜·출력은 이 세션 채팅 기록에서 (없으면 "기록 없음", 결정 16), 11-12 보호 파일 이름 10개 자가 보고 (`OWNER_RULINGS_LOG.md:986`).
6. 스펙: Status 한 줄, 10.4의 ⑤-2 행, 부록 B 판정. 10.5 단락은 D4 답대로 (D4-A: 본문 그대로, 도구 위치·커밋·sha256을 Status와 마감 기록에).
7. 2.10 점검표 0~12줄. 경로를 이름으로 `git add`, ⑦-1을 적은 커밋, force 없이 push, **커밋 번호를 소유자에게 바로 보고** (결정 10).
8. 그 뒤에만 `push_handoff.py --done "⑦-1 | Step 10 closing record | <files> | <commit> | <checks>"`.
완료 조건: 연구 브랜치 head가 새 커밋, `qa/acceptance_results.json` md5 동일, README numstat `2 2`, `runs/`에 요약 4개 (SPY 둘).

**T4. PR122.**
`gpt/r3-outage-20261114` (head `197c0e1`)에 새 main을 merge 커밋으로 반영 → 기준선 맨 마지막 → push → 모든 작업 녹색 → 병합. LEDGER `⑨-3a/recorder/1/outage`. Notion 9-3a 갱신.
완료 조건: 병합, CI 링크 기록.

**T5. REMAINING_WORK 새 판 (문서만).**
`docs/nautilus_bridge/REMAINING_WORK_2026-11-17.md`: 남은 Remaining Work ID와 새 접두어 (GH-, OS-, PAY-, KEY-, DS-, DIDM-, WEB-, 그리고 UI의 `⑬-2/page-redesign/<route>`), 각 레인 담당, 대기열 순서. LEDGER에 있는 ID는 넣지 않음. 감시 범위 밖이라 기준선 변화 없음 (`check.py:130-145`), Runtime도 뜨지 않음. Compliance 녹색 → 병합. PR122 바로 뒤에 둡니다 (그 전에 main을 움직이면 PR121·122가 다시 검사해야 함).
완료 조건: 병합, `CURRENT.md`에 "ID 출처 = 이 파일".

**T6. UI PR 자리 (D2).**
D2-A이고 소유자가 PR122 병합 전까지 시장 메인 화면 PNG와 지표 결론부 문구를 승인했다면 (화면 7개 시안과는 무관), `MERGE_QUEUE.md`의 4번에 UI PR을 두고 그 병합(UI 세션이 함)을 기다린 뒤 T7. 승인이 없으면 UI PR은 F21 뒤 (8번).

**T7. ⑦-2 P3 → 확인 문장 → 공지.**
시작할 때 `MERGE_QUEUE.md`를 `freeze: P3`로. 2.11의 1~9단계: 그날 main으로 리허설 → 병합 커밋 하나 (충돌 해결, Bonds F1~F5, 결정표 27번 문구, `qa/research_status.json` 재생성과 README 한 줄) → S1, S2, S3, S4 (bonds 33→37), 기준선은 별도 커밋 → 스펙 8.6 우회 래퍼로 캐시 없는 전체 검사 (run_all.py 직접 실행 금지) → 행 수·FAIL (예상: macro_m8 dry-run, papers taskkill 둘뿐; 다른 FAIL이면 먼저 질문, 답 X3)·커밋 목록 보고 → push → 40자 tip에 대한 확인 문장 요청 → 스펙 전용 커밋으로 Status에 기록 → E와 행 수 대조 (nautilus 57, guard 5, papers 49) → "병합해도 됩니다" + tip + 예상 행 수 공지, `freeze: F`. 공지에 소유자 PC `.agents` 이동 줄 (마스터 부록 H2) 포함. whydi PC 연구 클론이 연구 브랜치가 아니면 (소유자 진단 출력으로 확인) 되돌리는 줄도 같이.
완료 조건: 공지 전송, 동결 기록.

**T8. F21 이후 (차례대로, 한 번에 PR 하나).**
1. 확인 문장과 이번 승인 원문을 main `OWNER_RULINGS_LOG.md`에 옮기는 main PR 하나 (README 전체 표, 상태 스냅샷, 기준선). LEDGER ⑦-2, Notion, `freeze: none`.
2. UI PR이 아직이면 그 차례 (UI 세션).
3. **GH-1 + GH-2 (한 PR, D5-A).** UI 세션의 107~108행과 PR122의 9·93행 수정이 들어간 main 위에서:
   - `runtime-smoke.yml`: `concurrency` (`runtime-smoke-${{ github.ref }}`, cancel-in-progress). pull_request에서는 ubuntu 3.12 + windows 3.12만, windows는 Linux 뒤 (`needs:`). 3.11/3.14 전체는 주간 schedule·workflow_dispatch. syntax 작업은 ubuntu로. wheel 업로드는 한 작업만, retention-days 2. 경로 목록과 테스트 줄은 그대로 유지.
   - `compliance-review.yml`: 보관 30일 → 7일.
   - `tools/compliance/export.py:49-51`: 링크는 유지, "저장소 접근 권한이 필요" 안내 추가.
   - 삭제: `test_npu.py`, `mindmap/`, `.claude/launch.json`의 `godseye-dev` 항목 (quantgen-web 항목은 유지). 소유자 기준 ("프로그램 구동에 하나도 필요가 없으면 삭제")대로, 목록은 마스터 부록 F.
   - 기준선 갱신 (파일 삭제 → 20개 문서 재검토, PR 설명에 적음). `python -m unittest tests.packaging_policy_acceptance tests.runtime_syntax_acceptance tests.compliance_acceptance`.
   - 병합 뒤 소유자에게 예산을 낮출지 여쭘 (마스터 8절).
   - D5-B를 고르셨다면 이 PR은 T5 다음 (P3 전)으로 당기고, 병합 뒤 "quantgen 비공개 전환 가능"을 알림.
   - `_backup/`은 `archive-2026-11` 태그 뒤 제거 (그 전에 `tests.macro_m5_integration`이 zip 없이 건너뛰는지 확인).
4. **회원가입 정책 문서 PR (D11-A).** `docs/compliance/` 06·17·18·20과 처리방침: 이메일만 받는 출시 알림 (만 14세 이상, 보유 알림 후 3개월), 운영자 정보는 소유자가 준 값만 (없으면 빈칸 유지하고 묻기). 웹사이트 세션의 WEB-3가 이 PR을 기다림. 소유자에게 변호사·118 확인을 먼저 권함.
5. **웹 거래 결정 메모 (D12-A, 문서만, ⑦-2 뒤; P4 `OWNER_RULINGS_LOG.md:759`).** 선택지 A/B/C, 쟁점, KIS·변호사에게 물을 것, M-12와의 관계. 그 뒤 M-12 주문 모듈 (20 거래일 모의 D-9, 변호사 의견서 D-14 전에는 배포 안 함).
6. `push_handoff.py --doc <파일>` 추가 (공유 파일 PR).

**계속 할 일.** 병합 관리 (대기열 유지, 각 레인의 첫 코드 PR이 CI 경로·테스트를 더했는지 확인), `paper_live/`·`grokteam/` 보관 계획 (2027-02-01 이후). D6: 소유자의 주간 Claude 사용량이 70%를 넘었다고 들으면 OS·결제 세션부터 멈추자고 권함 (메인이 F까지 핵심).

## 멈출 때
- `push_handoff.py` 종료 코드 3: 멈추고 소유자에게. 2: 입력 고쳐 다시. 4: `--show`, `--ledger` 먼저.
- 주간 사용량 98% 또는 끝내기 전: 작업 브랜치 push, 끝난 ID `--done`, `status: handoff`. GPT 후임은 소유자가 직접 쓴 결정 11 한 줄이 있어야 연구 브랜치를 만질 수 있다고 적음 (07).

## 보고할 것 (매 단계)
커밋 번호, PR 번호, CI run 번호와 결과, 확인한 것과 확인 못 한 것, 다음 단계.

---- 복사 끝 ----
