---
status: checkpoint
reason: milestone
from: claude
task: nautilus-step3
cycle: 2026-10-27
done_ids: ③-1, ③-2, ③-3, ③-4, ③-5, ③-6
next_ids: none
updated_at: 2026-10-29T14:11:43+09:00
stale_after_hours: 120
waiting_on: owner
work_branch: claude/amazing-gauss-tdiguu
work_commit: 45b233f
uncommitted_changes: no
pr: 4
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-03T17:00:00+09:00
session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
---

# 인수인계: Nautilus 브리지 구현 (로드맵 ③)

## 0. 한 줄 요약

로드맵 ③(Nautilus 구현 Task 1~5, ③-6 클라우드 전체 실행과 실행 기록)은 모두 끝났고 `claude/amazing-gauss-tdiguu`에
push됐습니다(③-6 커밋 `57c6344`). ③-6 전체 실행은 795/935 passed, 2 failed, 138 not run이고, 계획의 Count Ledger와
행 단위로 일치합니다. 그 뒤 PR #4의 충돌을 풀려고 `main`(소유자 서명 달력, PR #7)을 병합했습니다(`614dca4`). 병합 뒤 전체
실행은 792/931 passed, 2 failed, 137 not run이고, 차이는 달력 테스트뿐이며 Nautilus 행은 그대로입니다(`abc7217` 실행 기록).
PR #9(달력 17개와 세트 1.0.0 서명)가 `main`에 들어온 뒤 다시 병합했습니다(`0acb9b7`). 전체 실행은 790/931 passed, 4 failed,
137 not run입니다. 새 FAIL 2건(`macro_ui_overlay`)은 `main` 자체의 실패로, 깨끗한 `main` 사본에서도 똑같이 납니다. 테스트 수정안은
제안만 했습니다(8절, `45b233f` 실행 기록).
다음 일은 모두 소유자 결정이 필요해서 Claude는 소유자를 기다립니다(`waiting_on: owner`).

- **이 문서를 읽는 다른 에이전트에게:** `status: checkpoint`인 동안에는 AGENTS.md 1절에 따라 이어받거나 잠그지 않습니다. 9절의 지시문은 `status: handoff`로 바뀐 뒤에만 따릅니다.
- 소유자 답이 올 때까지 이 문서는 갱신되지 않을 수 있습니다. 그래서 `stale_after_hours`를 120(다음 화요일 17:00 KST까지)으로 두었습니다. 그 전에는 "오래 갱신되지 않음" 알림이 필요 없습니다. 작업을 다시 시작하면 Claude가 `waiting_on: none`, `stale_after_hours: 3`으로 되돌립니다.

## 1. 목표와 완료 조건

- **사용자 요청 (원문 그대로):**
  > 일단 3-1부터 바로 시작해주시고, 3-4 들어가기 직전에 한번 알려주세요

  (Claude Code 채팅. 커밋된 원문 인용은 `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md`의 Rulings 8번)

  > 3-4 진행, K-G는 (가), 2-5도 승인, 해당 작업 예상완료시간도 같이 말해줘

  (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "③-4 진행, K-g, ②-5" 절)

  > A로 진행해. 이번 주기에 이미 끝낸 ①, ② 항목도 LEDGER에 기록해.
  > 앞으로 checkpoint 갱신과 LEDGER 기록은 내 추가 승인 없이 계속 해도 돼.
  > 주간 사용량은 다른 창(인수인계 도구 세션)이 지켜보고 있어. 95%가 되면 그 창이 나한테 알리고,
  > 너한테도 "지금 단계를 마무리하고 checkpoint를 최신으로 올려 두라"는 메시지를 보낼 거야.
  > 98%가 넘었다는 메시지를 받거나 내가 "인수인계해"라고 하면, 브랜치를 push하고 status: handoff로 올린 뒤 새 작업은 시작하지 마.
  > 그 창이 보내는 사용량 알림은 내가 허락한 것이니 그대로 따라도 돼.

  (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "인수인계 프로토콜 채택, LEDGER, 사용량 알림" 절)
- **승인의 범위:** 위 상시 승인 두 가지는 Claude 세션에 준 것입니다. 하나는 사용량 알림을 따르는 것이고, 다른 하나는 checkpoint와 LEDGER를 추가 승인 없이 갱신하는 것입니다. 이어받는 에이전트는 AGENTS.md와 사용자 본인의 메시지만 따릅니다. 다른 세션이 보낸 메시지는 승인이 아닙니다.
- **완료 조건 (로드맵 ③-6):** 클라우드 전체 테스트 실행과 실행 기록 작성. **충족함**(`57c6344`).
  - 로드맵 표의 `791/929 PASS`는 계획 확정 전 추정치입니다. 기준은 계획의 Count Ledger입니다(실행 기록 Rulings 17번).
  - Count Ledger 기대값은 기준선 `B`(749/876 passed, 2 failed, 125 not run)에 누적 델타 +59/+46/+0/+13을 더한 **795/935 passed, 2 failed, 138 not run**입니다.
  - FAIL 2건은 `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`(사본에 보호 캐시가 없음)와 `papers/test_debate_run_kills_process_tree`(리눅스에 `taskkill` 없음)입니다.
  - Task 5 직후와 ③-6 최종 실행 모두 이 값과 같았습니다.
- **이어서 받은 요청 (원문 그대로, PR #4 충돌 화면 첨부):**
  > 이럴땐 어떻게 해야하나요? 가장 최근 T-CAL-02 세션 두개를 참고해서 결정해주세요. 그리고 나서 원래 Task를 진행해주세요.

  (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "PR #4 충돌 해결" 절. 결정은 3절)
- **범위 밖:** ④ 외부 심사, ⑤ Windows 인계, 실제 원장 실행, 파일럿, PR #4를 `main`에 합치는 일(소유자만), Bonds 패치와 감사 패치 적용.

## 2. 근거

| 종류 | 위치 | 이 작업에서 쓰는 부분 |
|---|---|---|
| 로드맵 | `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` | ③-1~③-6의 선행 조건과 완료 기준 |
| 구현 계획 | `docs/superpowers/plans/2026-10-26-nautilus-bridge.md` | Plan rulings(X-1, X-2, T5-1, T1 CI 4), Count Ledger, Task 1~5. 전체 실행 명령은 7절 주의 |
| 스펙 | `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`(rev 6) | Step 3~7, 3.3 가드 루트, 9절 추가 규칙, Step 1b |
| 실행 기록 | `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md` | ③-6 결과, Rulings 19건, Full-run counts 표, Step 7A 인계 상태, 미뤄 둔 사소한 발견 4건 |
| 사용자 결정 | `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | "Claude 자진 보고"(보호 캐시), "③-4 진행, K-g, ②-5", "인수인계 프로토콜 채택, LEDGER, 사용량 알림" 절 |
| 오류 대장 | `docs/nautilus_bridge/KNOWN_ERRORS_REGISTER_2026-10-28.md` | 4.1 ②-5 대기열, 4.4 소유자 결정 27건, 10절(②-3에서 새로 확인한 결함) |
| 모델 한계 대장 | `docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md` | ②-3 결과 |
| R3 설계 | `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`(rev 2) | 10.2 소유자 질문(A: 지금, B: ⑨-3d) |
| 감사 | `docs/audit/2026-10-27-implementation-audit-report.md` | 감사 항목 141건, 11절 PT/물결, 12절 소유자 결정 |
| 달력 서명 키트 | `docs/calendar_signoff/SIGNING_KIT_2026-10-28.md` | ①-2 소유자 서명 절차 |
| 구현 코드 | `tools/nautilus/`, `tests/nautilus_acceptance.py`, `requirements-nautilus.txt`, `tests/fixtures/nautilus/`, `docs/nautilus_bridge/RUNBOOK_windows.md`, `docs/nautilus_bridge/registration/` | ③-1~③-5 산출물 |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안과 이유 |
|---|---|---|
| 모든 전체 실행은 보호 캐시 4개를 뺀 sparse 사본에서 함(X-1, T5-1) | 기존 macro 테스트 3개가 보호 캐시를 열기 때문(소유자에게 자진 보고함) | 실제 클론 실행: 보호 파일을 읽게 되어 금지 |
| 테스트 수는 기준선 `B`에 대한 델타로 판정(T1 CI 4) | ②-1, PT-07 달력 등으로 Task 1 전에 스위트가 바뀜 | 고정 절대값: 로드맵의 791/929처럼 어긋남 |
| K-g는 (가): `repo_anchor()`를 고치지 않습니다. 기준점이 UNVERSIONED면 러너가 원장 쓰기 전에 R-02로 거절하고, 해결은 re-anchor 빈 커밋입니다 | `core/quant/gate_ledger.py`는 동결 하네스 파일(`core/quant/gate_package.py:36` `HARNESS_SOURCES`) | 먼저 `repo_anchor()` 수정: 동결 파일이라 기각 |
| ②-5 승인은 대기열 순서 승인으로 해석. 4.4 결정은 하나씩 따로 받음 | 소유자 원문이 "2-5도 승인" 한 줄 | 4.4 전부 승인으로 해석: 근거 부족 |
| PR #4 충돌은 `main`(PR #7)의 소유자 서명 달력을 바이트 그대로 채택하고 PT-07(`d865c7f`)의 달력 데이터, 로더, 테스트를 걷어내 해결(`614dca4`) | 서명은 md5로 내용에 묶임. PT-07의 `store.py`는 서명 파일에 없는 `sign_off_statement`와 MANIFEST `signed_utc`를 요구해 서명본을 거부함. ①-2는 `main`에서 끝남 | PT-07 유지 또는 섞기: 서명 무효, 소유자 재서명 필요 |
| Task 5와 ③-6은 ③-4 진행 지시에 이어 순서대로 진행 | 소유자가 ③-4 직전 한 번만 멈추라고 함(실행 기록 Rulings 8, 14) | ③-4 뒤 다시 멈춤: 지시에 없음 |

## 4. 진행 상황

- [x] ③-1 Task 1 환경과 실행 계약 — 커밋 `e83ff6f`, LEDGER 기록함
- [x] ③-2 Task 2 T-RO-01 개정과 nautilus 스위트 — 커밋 `76295d0`, LEDGER 기록함
- [x] ③-3 Task 3 샌드박스 — 커밋 `321b829`(골든은 `6b6b386`), LEDGER 기록함
- [x] ③-4 Task 4 러너(원장 선등록) — 커밋 `6b6b386`, LEDGER 기록함
- [x] ③-5 Task 5 패리티, 게이트 인계, 파일럿 등록표, Windows 런북 — 커밋 `520d0db`, LEDGER 기록함
- [x] ③-6 클라우드 전체 실행과 실행 기록 — 커밋 `57c6344`, LEDGER 기록함
- [x] PR #4 충돌 해결: `main` 병합 `614dca4`, 병합 뒤 전체 실행 기록 `abc7217` (로드맵 ID 없음)
- [x] ①-2/2 기록: 달력 5·6차 서명(다른 세션, `claude/relaxed-cerf-az755o`의 `d4e9a42`, `f8c7467`)을 Claude가 sparse 클론에서 확인하고 LEDGER에 기록
- [x] PR #4 2차 충돌 해결: PR #9 병합 뒤 `main` 병합 `0acb9b7`(결정 로그만 충돌), 실행 기록 `45b233f`
- [x] ①-2/3 기록: 세트 1.0.0 서명(`999dd26`, 소유자 위임으로 채운 서명서)
- [ ] 다음: 소유자 결정 대기 ← **여기서 멈춤** (8절)

이번 주기에 끝난 ①·② 항목도 소유자 지시로 LEDGER에 기록했습니다. ①-1, ①-3, ①-4, ①-5, ②-1~②-4, ②-5/a, ②-6입니다. ①-2는 T-CAL-02 세션이 먼저 기록했습니다(`handoff` 브랜치 `ebe89d6`). 그 세션의 5·6차 서명(달력 17개 전부 서명)은 그 세션의 요청에 따라 Claude가 확인해 ①-2/2로 기록했습니다.

- 이 작업의 ID가 아니므로 `done_ids`에는 넣지 않았습니다.
- 소유자가 수행한 항목은 "한 일" 칸이 `소유자 수행:`으로 시작합니다. "누가" 칸은 기록한 쪽(claude)입니다.
- Claude가 올린 행(16행, 이어서 ①-2/2)은 "완료 시각" 칸이 기록한 시각입니다. 실제 완료 시각은 "확인 방법과 결과" 칸에 KST로 적었습니다.
- ①-2는 다른 Claude 세션(PR #5, #7)과 소유자 서명으로 `main`에서 끝났습니다. 병합 뒤 Claude도 `test_cal02` PASS를 확인했습니다(실행 기록 `abc7217`).
- ②-5 전체(10절 결함 분류 여부와 4.4 결정 미결)는 끝나지 않아 기록하지 않았습니다. ②-5/a는 소유자가 승인한 4.1 대기열 순서만 뜻합니다.

**③-6 검증 (보호 캐시 없는 사본, 키 미설정):**

```
bash "$S/full_run.sh" t6_full          # 2026-10-29T02:23:49+09:00 ~ 02:34:23+09:00, 520d0db의 깨끗한 클론
795/935 passed, 2 failed, 138 not run  # B 대비 59행 추가(PASS 46, NOT_RUN 13), 제거 0, 변경 0
nautilus 스위트: 키 미설정 44/57, 키 설정 57/57; python3 -B -m tests.macro_m0_harness 14/14
qa/acceptance_results.json md5 16c9baa5a1777853521d485d5078e456 (변경 없음)
```

**1차 `main` 병합 뒤 검증 (614dca4 클론, 키 미설정):**

```
bash "$S/full_run.sh" m1_full          # 2026-10-29T03:07:48+09:00 시작
792/931 passed, 2 failed, 137 not run  # t6 대비: PT-07 달력 행 8개 제거, main 행 4개 추가, test_cal02 NOT_RUN -> PASS
nautilus 57행 변화 없음(44 PASS, 13 NOT_RUN); macro_m0_harness 14/14; FAIL은 B의 2건; md5 변경 없음
```

**마지막 검증 (2차 `main` 병합 뒤, 0acb9b7 클론, 키 미설정):**

```
bash "$S/full_run.sh" m2_full          # 2026-10-29T13:37:48+09:00 시작
790/931 passed, 4 failed, 137 not run  # m1 대비 추가·제거 0, PASS -> FAIL 2(macro_ui_overlay, main 자체의 실패)
nautilus 57행 변화 없음(44 PASS, 13 NOT_RUN); macro_m0_harness 14/14; md5 변경 없음
macro_ui_overlay: main e28035f 사본 14/16(같은 2건 FAIL), 테스트 수정안 적용 시 16/16
```

## 5. 중단 지점

- ③은 끝났습니다. 커밋되지 않은 변경은 없습니다.
- 다음 작업은 모두 소유자 결정이 필요해서 `waiting_on: owner`로 멈췄습니다.
  - ④-1 GPT·Gemini 심사: 로드맵 표기 "10-30 14:40"(Codex 할당량 재설정, 시간대 표기 없음) 이후, 소유자 PC에서 실행.
  - ②-5 대기열(`docs/nautilus_bridge/KNOWN_ERRORS_REGISTER_2026-10-28.md` 4.1) 상태:
    - 끝남: 0단계(②-1, `6054b33`), 2단계(스크래치 diff 보존, `22bdc16`, `420af64`), 4단계(Nautilus ②-2~③-6, `57c6344`까지).
    - 1단계(①-2 달력 서명)는 `main`에서 끝났습니다(소유자 서명 `3917bc0`, 이 브랜치에는 `614dca4`로 병합).
    - 나머지 달력(5차 `release_calendar`, 6차 JPX·SSE·HKEX·TWSE·CME·`market_closes`)과 세트 1.0.0도 서명돼 `main`(PR #9, `e28035f`)에 들어왔고, 이 브랜치에는 `0acb9b7`로 병합됐습니다. 달력 17개가 모두 서명됐습니다.
    - 3단계(Bonds 패치)는 패치 적용 여부와 ⑦-4 세 가지 결정이 필요합니다.
    - 5단계(PT-01·PT-02·K-f)는 12.8 결정과 K-f 앞당김 결정이 필요하고, 동결 하네스 파일(`core/quant/validate.py`, `core/quant/instruments.py`)도 고칩니다.
    - 7단계(PT-04)는 3단계 뒤입니다.
- 이 세션의 스크래치 파일(`full_run.sh`, 결과 JSON)은 레포 밖이라 이어받는 쪽에는 없습니다. 다시 돌려야 하면 6절의 도구를 만듭니다.

## 6. 다음 할 일 (순서대로)

이 작업(nautilus-step3)에는 남은 ID가 없습니다. 그래서 `next_ids`는 none입니다. 아래 항목은 이 작업 밖이며, 모두 소유자 결정이나 소유자 PC가 필요합니다. 소유자 지시 없이 시작하지 않습니다.

1. ④-1 GPT·Gemini 심사. 로드맵: "사용자 PC에서 실행 → Claude가 판정하고 스펙에 반영". 판정과 스펙 반영은 Claude가 돌아와서 합니다.
2. ④-2 소유자 O2~O15 판정과 스펙 승인 문장(스펙 Step 1b). 이어서 ④-3: 판정이 기본값과 다르면 브랜치를 수정합니다. 완료 기준은 "브랜치가 판정과 일치"입니다.
3. ⑤-1 Windows 인계(Step 7A), `docs/nautilus_bridge/RUNBOOK_windows.md`. 로드맵 순서는 "Claude: 사인오프 기록 → 사용자: 런북 실행, 인계 보고서 커밋 → Claude: 검토 → 사용자: 파일럿 실행 승인 기록"입니다. 실행 기록의 "Hand-off state for Step 7A"를 따릅니다.
4. ②-5 나머지(로드맵 "1-4 우선순위 결정"). 10절 결함 분류 여부와 4.4 결정을 막는 순서대로 받습니다. 그 뒤 대기열 3단계부터 진행합니다.

### 전체 실행을 다시 확인해야 할 때만

**환경 조건.** 다음 조건이 다르면 수치가 달라집니다. 환경 때문에 생긴 차이는 보고만 하고 고치지 않습니다.

- 리눅스입니다. `taskkill`과 `tectonic`이 없어야 합니다.
- git은 2.35 이상이어야 합니다(`sparse-checkout set --no-cone`).
- 얕지 않은 로컬 클론이어야 하고, 소유자 태그가 있어야 합니다. `git rev-parse 'studies-of-record-2026-10-23^{commit}'`이 `eacd57d…`이어야 합니다.
- Python은 `requirements.txt`를 설치한 가상환경을 씁니다(statsmodels 포함). 전역 `pip install`은 하지 않습니다.

**도구 만들기.** 레포 밖에 새 디렉터리를 만들어 `S`로 둡니다. 계획에 나오는 `S=/tmp/claude-0/...` 경로는 이 세션 전용이라 쓰지 않습니다.

```
S=<레포 밖 새 디렉터리>; mkdir -p "$S"
```

`$S/full_run.sh`에 아래 전문을 그대로 저장합니다.

- 계획 Task 1 Step 0의 코드 블록은 T5-1 결정 이전 판이라 쓰지 않습니다. 일반 `git clone`이라 보호 캐시가 사본에 체크아웃됩니다.
- 이 판은 sparse checkout을 써서 캐시 4개를 아예 쓰지 않습니다.

```
#!/bin/bash
# full_run.sh <name>: one full-suite run (key unset) of the real clone's working tree on a cache-free scratch clone
# $S/full_<name>; rows to $S/<name>.json (plan Count Ledger, "Cache-free copy"). Never opens the four caches.
# The clone is sparse (plan ruling T5-1): the four caches are skip-worktree and never written.
set -euo pipefail
S=$(cd "$(dirname "$0")" && pwd); NAME=$1; REPO=${2:-/home/user/quantgen}; C="$S/full_$NAME"
CACHES='^docs/asset_expansion/cache/(yf_SPY|yf_BTC-USD|binance_BTCUSDT|upbit_KRW-BTC)\.csv$'
rm -rf "$C" && git clone -q --no-checkout "$REPO" "$C"
git -C "$C" sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/yf_SPY.csv' '!/docs/asset_expansion/cache/yf_BTC-USD.csv' '!/docs/asset_expansion/cache/binance_BTCUSDT.csv' '!/docs/asset_expansion/cache/upbit_KRW-BTC.csv'
git -C "$C" checkout -q
test "$(git -C "$C" ls-files -t | grep -cE '^S docs/asset_expansion/cache/(yf_SPY|yf_BTC-USD|binance_BTCUSDT|upbit_KRW-BTC)\.csv$')" = 4
{ git -C "$REPO" diff --name-only --diff-filter=d -z HEAD; git -C "$REPO" ls-files -o --exclude-standard -z; } |
    { grep -zvE "$CACHES" || true; } | tar -C "$REPO" -c --null -T - | tar -C "$C" -x
git -C "$REPO" diff --name-only --diff-filter=D -z HEAD | (cd "$C" && xargs -0 -r rm -f --)
rm -f "$C"/docs/asset_expansion/cache/{yf_SPY,yf_BTC-USD,binance_BTCUSDT,upbit_KRW-BTC}.csv
sed "s#\"/home/user/quantgen\"#\"$C\"#" "$S/run_baseline.py" > "$S/run_copy_$NAME.py"
grep -qF "\"$C\"" "$S/run_copy_$NAME.py"
cd "$C" && env -u QUANTGEN_NAUTILUS_PYTHON python3 -B "$S/run_copy_$NAME.py" "$S/$NAME.json"
```

`$S/run_baseline.py`에 아래를 저장합니다. `tests/run_all.py`의 결과 경로만 바꾸는 래퍼라 `qa/acceptance_results.json`을 덮어쓰지 않습니다.

```
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/quantgen")
import tests.run_all as R
R.OUT = Path(sys.argv[1])
sys.exit(R.main(sys.argv[2:]))
```

- `"/home/user/quantgen"`은 `full_run.sh`가 사본 경로로 바꾸는 자리표시입니다. 그대로 둡니다. 레포 경로가 다르면 `full_run.sh`의 두 번째 인자로 줍니다.
- 실제 클론에서 `run_baseline.py`를 직접 쓰는 것은 `--suite nautilus` 같은 스위트 실행뿐입니다. `--suite` 없는 전체 실행은 반드시 `full_run.sh`로 합니다(7절).

**실행.** 약 10~12분 걸립니다.

```
PATH=<venv>/bin:$PATH bash "$S/full_run.sh" check_full [<레포 경로>]
```

- 종료 코드 1이 정상입니다. 래퍼는 FAIL이 하나라도 있으면 1로 끝납니다. 판정은 마지막 줄의 집계로 합니다.
- 기대값(`0acb9b7` 이후, 달력 17개와 세트 서명됨): `790/931 passed, 4 failed, 137 not run`. FAIL은 1절의 2건과 `macro_ui_overlay`의 2건(`test_every_owner_decision_d1_to_d6_is_listed_with_value_and_status`, `test_view_selector_hosts_the_overlay_view_and_reads_nothing_into_home`, `main` 자체의 실패, 8절)입니다. 그 테스트 수정이 들어오면 `792/931 passed, 2 failed, 137 not run`이 됩니다. 이 밖의 결과는 보고만 하고 고치지 않습니다.
- `md5sum qa/acceptance_results.json`은 `16c9baa5a1777853521d485d5078e456`이어야 합니다.

## 7. 주의사항 / 하지 말 것

- **보호 캐시 4개:** `docs/asset_expansion/cache/`의 `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`는 열거나 읽거나 해시하지 않습니다.
  - 계획의 전체 실행 명령은 그대로 쓰지 않습니다. 해당 명령은 Task 2 Step 15, Task 3 Step 10, Task 4 Step 10, Task 5 Step 14(`python3 -B $S/run_baseline.py $S/<name>.json`, `--suite` 없음)입니다.
  - 이 명령들은 실제 클론에서 돌아 macro 테스트 3개가 보호 캐시를 엽니다. 전체 실행은 6절의 `full_run.sh`로만 합니다(실행 기록 Rulings 5, 11).
- **비밀 정보:** `.env`는 열지 않습니다. 변수 이름만 적습니다(예: `QUANTGEN_NAUTILUS_PYTHON`).
- **결과 파일:** `tests/run_all.py`를 직접 실행하지 않습니다. `qa/acceptance_results.json`을 덮어쓰기 때문입니다. 이 파일의 md5는 `16c9baa5a1777853521d485d5078e456`로 유지하고 커밋하지 않습니다.
- **가드 루트:** `nautilus` 실행이나 전체 실행 중에는 `docs/nautilus_bridge/` 아래에 아무것도 쓰지 않습니다. 가드 루트라서 실행 중인 테스트가 FAIL합니다.
- **동결 하네스:** `core/quant/gate_ledger.py`를 포함한 동결 하네스 파일(`core/quant/gate_package.py:36` `HARNESS_SOURCES`)은 소유자 승인 없이 고치지 않습니다.
- **제안 패치:** 감사 제안 패치(`docs/audit/2026-10-27/proposed_patches/`)와 Bonds 패치(`docs/audit/2026-10-27/bonds_screen/proposed_patch/`)는 소유자 승인 없이 적용하지 않습니다.
- **낡은 서명 키트:** `docs/calendar_signoff/SIGNING_KIT_2026-10-28.md`는 대체된 문서입니다. 이 키트로 서명하거나 그 행을 적용하지 않습니다.
- **손대지 않는 곳:** `paper_live/`, `grokteam/`은 고치지 않습니다. 전역 `pip install`을 하지 않습니다. Nautilus 가상환경은 `requirements-nautilus.txt`의 해시 고정으로만 만듭니다.
- **태그:** 태그를 push, 이동, 삭제하지 않습니다(소유자 태그 `6e7c1f7`).
- **소유자 전용 필드:** `owner_confirmed`, `host_fingerprint`를 쓰지 않습니다. 달력의 `signed_off_by`, `signed_utc`, `md5`, 서명 문장은 소유자만 정합니다.
- **브랜치:** `claude/amazing-gauss-tdiguu`와 `main`에는 직접 push하지 않습니다. 이어받는 쪽은 `gpt/<task>`를 씁니다. PR을 만들지 않습니다.

## 8. 사용자에게 물어야 할 것

- **X-1 공개.** 2026-10-26 클라우드 기준선 실행 2회에서 macro 테스트 3개가 보호 캐시 파일을 읽었습니다. Claude는 PASS/FAIL만 봤습니다.
  - 이 사실을 Step 10 실행 기록과 스펙 10.4의 데이터 접근 이력에 남길지 정해 주십시오(`OWNER_RULINGS_LOG.md` "Claude 자진 보고" 절).
  - Claude 권고는 사실대로 기록하는 것입니다. ③-6 실행 기록에는 "Open owner decisions"로 사실만 적어 두었고 결정은 하지 않았습니다.
- **`macro_ui_overlay` 테스트 2건(`main`의 실패).** 두 테스트가 달력 미서명 상태를 단언해서, 17개가 모두 서명된 `main`에서 실패합니다. 서명문서 세션이 Claude의 수정안을 `claude/relaxed-cerf-az755o`의 `ace8f3b`에 넣었습니다(테스트 9줄과 `ui/macro_state_panel.py:501` 문구 1줄, 그 세션 보고 16/16). PR로 `main`에 넣을지는 소유자가 정합니다. 들어오면 PR #4에 `main`을 다시 병합합니다(`git merge-tree`로 충돌 없음 확인). 그 뒤 기대값은 `792/931 passed, 2 failed, 137 not run`입니다. 이 브랜치에는 같은 수정을 따로 넣지 않습니다.
- **PT-07 로더 강화.** PR #4 병합에서 걷어낸 PT-07의 로더 검사(CAL-12 same_day 달력 서명, CAL-13 따옴표 없는 시각 거부, CAL-14 MANIFEST `signed_utc`·서명 문장 고정, M-4 `signed_utc` 형식)를 서명된 파일과 맞게 다시 설계해 제안할지 정해 주십시오. 그대로 다시 넣으면 서명본이 거부됩니다.
- **②-5 나머지.**
  - 오류 목록 10절(②-3에서 새로 확인한 결함, 임시 ID 71개)을 분류해 순위에 넣을지 정해 주십시오(4.4 머리말, 740행).
  - 4.4의 27건 중 3번(K-g)은 이미 답하셨고, 1번(①-2 서명)은 `main`에서 끝났습니다. 27번(O2~O15)은 아래 Step 1b에서 따로 묻습니다.
  - 나머지는 막는 순서대로 정해 주십시오. 먼저 2번(대기열 3단계: Bonds 패치 적용과 ⑦-4의 BS-04, BS-11, BS-21), 다음 4번과 5번(대기열 5단계: 12.8과 K-f 앞당김)입니다.
- **Step 1b(④-2).** ④-1 심사 뒤 O2~O15 판정과 스펙 승인 문장이 필요합니다.
- **R3 설계 rev 2.** 10.2 A의 Q5~Q7, Q9~Q14, Q16~Q22에 답하시거나 "기본값 수락"으로 정해 주십시오. 오류 목록 4.4의 9번(rev 2 승인, 10.2 A 답, 0b 기록)과 같은 항목입니다. Q8과 Q15는 10.2 B라서 ⑨-3d에서 정합니다. 지금은 묻지 않습니다.

## 9. 이어받는 에이전트에게 주는 지시문

이 블록은 `status: handoff`로 바뀐 뒤에만 따릅니다. `status: checkpoint`인 동안에는 이어받거나 잠그지 않습니다(AGENTS.md 1절).

```
너는 xkg4real/quantgen 레포의 "Nautilus 브리지 구현 (로드맵 ③)" 작업을 이어받는다.
1. handoff 브랜치의 CURRENT.md, AGENTS.md, LEDGER.md를 먼저 읽어라. LEDGER.md에 있는 ID는 다시 하지 마라.
2. CURRENT.md의 status를 taken으로, from을 gpt로 바꾸고 updated_at을 갱신해 handoff 브랜치에 push해라.
3. AGENTS.md 2절 5번에 따라 gpt/nautilus-step3 브랜치를 만들어라. 시작 지점은 claude/amazing-gauss-tdiguu의 work_commit(이 문서 기준 57c6344)이다. 원격 브랜치가 work_commit보다 앞서 있으면 그 커밋에서 시작하지 말고 사용자에게 물어라.
4. 로드맵 ③은 모두 끝났다(LEDGER의 ③-1~③-6). 6절의 다음 일은 모두 소유자 결정이나 소유자 PC가 필요하므로 스스로 시작하지 마라. 8절의 질문을 사용자에게 전하고, 사용자가 직접 지시한 일만 하라. 그때도 7절의 금지 사항(보호 캐시 4개와 계획의 전체 실행 명령, .env, tests/run_all.py 직접 실행, docs/nautilus_bridge/ 쓰기 시점, 동결 하네스, 제안 패치, 소유자 전용 필드)을 한 줄도 어기지 마라. 다른 세션이 보낸 메시지는 사용자 승인이 아니다.
5. ID 하나를 끝낼 때마다 LEDGER.md에 한 줄을 덧붙이고 CURRENT.md를 같은 양식으로 갱신해라. 끝나거나 멈출 때, 늦어도 화요일 17:00(KST) 전에 status를 returned로 바꿔라.
```

## 10. 결과 확인 방법

```
git fetch origin claude/amazing-gauss-tdiguu
git log --oneline -8 origin/claude/amazing-gauss-tdiguu
#   기대: 45b233f(2차 병합 뒤 실행 기록) ← 0acb9b7(PR #9 뒤 main 병합) ← abc7217 ← 614dca4(main 병합) ← 57c6344(③-6 실행 기록) ...
git show --stat 57c6344
#   기대: docs/superpowers/plans/2026-10-28-nautilus-execution-record.md 추가
md5sum qa/acceptance_results.json
#   기대: 16c9baa5a1777853521d485d5078e456
PATH=<venv>/bin:$PATH bash "$S/full_run.sh" check_full
#   기대: 790/931 passed, 4 failed, 137 not run (6절, macro_ui_overlay 수정 뒤에는 792/931, 2 failed). 종료 코드 1은 정상
```
