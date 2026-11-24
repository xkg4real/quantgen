<!-- 조정 문서와 git 대조 (메인 워크플로 wf_831f72a0-085, 2026-11-24). 읽기 전용 분석 에이전트의 보고 원문(영어). 인수(handoff 8a93ce6) 전 시점 기준이라 '잠금' 관련 문장은 그 뒤 풀렸다. -->

# Coordination documents vs. git — 2026-11-24 18:05 KST

Read-only. Checked against `origin/main` b872d8c and `origin/handoff` 38ccd06 (both are the remote tips). Nothing was pushed, committed or sent.

## 0. What the main session needs first

- **Four of the five Claude sub-session branches are fully on main.** Only `claude/payments-pay0-20261120` (e869064, 12 docs) is not.
- **KEY-5/a review findings M1 and M2 are both fixed on main** (code read, and the five gateway suites ran 83 tests OK).
- **CURRENT.md is still `status: taken` by GPT** (last update 2026-11-23 12:43, 29 hours ago). `push_handoff.py` refuses a Claude publish over it (tools/handoff/push_handoff.py:341-343), so CURRENT and ledger `--done` rows cannot be published until GPT returns it or the owner approves `--force`. The lock does not go stale by itself.
- **Three sub-session documents would send their sessions to redo finished work.** PAYMENTS (L8, L30) says fix M1/M2; OS (L8, L130-136) says open the OS-F2 PR. Tell each session its ledger state before it resumes.
- **Owner items due within 24 hours or blocking a session: 6.** The threshold of 5 is met, and the last push was 2026-11-20 00:51 KST.
- **PR #148 exists and is in no coordination document** (`claude/quant-skills-20261123` @ 462f7df, opened today 17:10 KST by another Claude session, not a draft).
- **The 3-hourly pipeline check is disabled** (trigger `trig_01P2NBVZFChNHJGjVdtrDTyC`, last fired 2026-11-20 03:20 KST). Its prompt names three sub-sessions.

## 1. Git facts

### 1.1 Claude sub-session branches

| Branch (head) | Ancestor of main? | How it landed | Same files GPT changed afterwards |
|---|---|---|---|
| `claude/os-f2-data-dir-20261120` (e44c48e) | yes | PR #136 head 64ff58e → 72a055f | 4 of 14: `core/app_paths.py`, `data/krx/kis_client.py`, `data/krx/opendart_client.py`, `tests/app_paths_acceptance.py` |
| `claude/payments-key5a-20261120` (dc936d4) | yes | PR #139 head 0413cc5 → dec979a | 9 of 10: `core/gateway/{__init__,feed,remote}.py`, `GATEWAY_DESIGN.md`, `main.py`, four gateway tests |
| `claude/payments-pay0-20261120` (e869064) | **no**, 5 commits ahead of fa78df1 | no PR | none; all 12 files are absent from main and main has no commits in those two folders |
| `claude/ds-home-indicators-20261120` (f80b3b0) | yes | PR #137 head 4973111 → 6d25a33 | all 4: `runtime-smoke.yml`, `core/research/markets.py`, `HOME_INDICATORS_DATA_2026-11-20.md`, `tests/home_indicators_acceptance.py` |
| `claude/data-source-didm-20261117` (c206b10) | yes | PR #138 head 6cff168 → 53e5e72 | 13 of 42, including `core/didm/novelty.py`, `core/didm/store/__init__.py`, `core/didm/llm/schema.py`, `data/didm/alfred.py`, `tools/didm/collect_daily.py`, `VENDOR_EVAL_2026-11.md` |

`claude/os-pyside6-abort-20261119` (35e095f) is not an ancestor, but its five files are byte-identical on main through cherry-picks f9a3a75, a342cd2, 0b8f6c2, f993458 and 5b83262 inside PR #136.

### 1.2 KEY-5/a findings on main

| Finding | Verdict | Evidence |
|---|---|---|
| M1 stale FMP client | fixed | `core/gateway/feed.py:38-59`: the `fmp` property calls `gateway.blocked("fmp")` on every access and drops the client. `look_again` (61-66) discards even a working client. `_look_again` (85-94) runs on reload and on key set or delete (`core/gateway/__init__.py:226-257`). Tests at `tests/gateway_main_acceptance.py:327-346`. |
| M2 non-atomic `_refresh_krx` | fixed | `core/gateway/__init__.py:529-546`: the candidate is built unpublished, gated under `_lock`, then published with one assignment (546). `_KRX_BUILT` is read (534) and added to (525) under `_lock`. Tests at `gateway_main_acceptance.py:346, 370, 398`. |
| S1, S2, S3 | look fixed | `remote.py:89-91` and `130-137`; `feed.py:46-47, 55` |
| S4 to S7 | not checked | |

One thing I noticed: `GatedKRXGateway._run` holds the module lock across the provider call (`__init__.py:460-463`), so gateway calls serialise behind one slow KRX request. I did not measure the impact.

### 1.3 Tests I ran on main b872d8c (isolated HOME, `-B`)

| Suites | Result |
|---|---|
| five `tests.gateway_*_acceptance` | 83 OK |
| `tests.home_indicators_acceptance` | 23 OK |
| seven DIDM modules (schema, vendor_eval, store, ingest, sources, novelty, news) | 140 OK |
| `didm_eodhd`, `didm_alpaca_news`, `didm_massive_news` | 56 OK |
| `app_paths`, `app_storage_startup`, `credentials` | 93 OK, 3 skipped |
| `qt_port`, `qt_switch_day`, `app_identity`, `packaging_policy`, `third_party_notices` | 34 OK |
| `tests.handoff_doc_acceptance` | 16 OK |

The Nautilus `code_sha256` recomputed on main with the 6.6 formula (27 inputs) is `bcaf33d9…b34c`. Both registration tables still carry `code f995600b36c75523`, and there is no `owner/*` branch.

### 1.4 Open PRs and unmerged work (GitHub REST)

| Item | Head | State |
|---|---|---|
| PR #148 skills and quant-analyst agent | 462f7df | not draft; consistency check success; only Vercel fails; 24 files, `CLAUDE.md` +13 |
| PR #147 GH-2 | bf78b6b | draft; consistency check FAIL ("documents need review: 1…20", 855 sources) |
| PR #140 UI | 3483b53 | draft; conflicts with main; Ubuntu 3.12 and Windows 3.11 fail at "Verify shared KIS charts and realtime lifecycle with offline fixtures"; Windows 3.12 and 3.14 cancelled |
| PR #12 | 45e2d3e | open since 10-29, conflicts |
| `gpt/android-apk-evidence-20261123` | c28194f | no PR; 6 files; its 8 tests OK when I ran them from an extracted copy |
| `gpt/didm-kalshi-input-validation-20261123` | 77c37c5 | no PR; 4 files; `didm_sources` 31 OK (22 on main) |
| `gpt/didm-alfred-vintage-period-20261123` | 593c943 | no PR; 2 files; `didm_ingest` 27 OK (24 on main) |

PR #140 contains Claude UI 414eceb and K2d 7d9a4d3 as ancestors. `platform-build.yml` has never run, and there are no `archive-*` tags.

## 2. Per track

| Track | Done since 11-20 (ledger ID, commit) | Still open | Blocked on the owner |
|---|---|---|---|
| MAIN | `--doc` lane publishing: PR #146 → b872d8c. Ledger has only PR-stage rows (`T8-6-pr-integration-c410`, 5200b6c), no merge row. | PR #148 review; GH-2 PR #147; PR #12; policy PR-2 (gate now open); rewrite of the three coordination documents; `LANE_DOCS` entries for new sessions; pipeline trigger; missing ledger rows | lock takeover; OA-17; OA-36, 37, 38 (never asked) |
| PAYMENTS | KEY-5/a: PR #139 → dec979a | PAY-0 and PAY-2 unmerged (e869064); KEY-5 request is based on 148504a; S4 to S7; T16 to T19b, W9, W10 | OA-03, 32, 39, 40, 41, 45, 11, 13 |
| OS | OS-F2: PR #136 → 72a055f, including the PySide6 abort records. Part of OS-A1: PR #141 → 666e006 (`OS-A1/gbm-preview/main`) | APK tool c28194f; no APK built; OS-F1; the owner's real data move never done; OS-F3, F4, F5, M2 | OA-18, OA-30, Windows check of PR #140, OA-19 |
| DATA SOURCING | DS-H/code: PR #137 → 6d25a33. DS-4a: PR #138 → 53e5e72. Parsers: EODHD #142 → d835d9f, Alpaca #143 → 5af3787, Massive #144 → 51b8298 | Kalshi 77c37c5 and ALFRED 593c943; DS-H parent; live collection and rights; DS-1, DS-4d, DS-4e are on main with no ledger row | OA-09, OA-46, OA-38, OA-31, OA-23 |
| DIDM | DIDM-1: PR #138 → 53e5e72. V0 ID and hash checks: PR #145 → 05f97df | real gold set and model evaluation; `MODEL_CUTOFFS.md` does not exist; DIDM-0 (`PREREG_V0.md`) is on main with no ledger row | OA-10 |
| UI | nothing merged; checkpoint rows only | PR #140 red and conflicting; KEY-5 screen sites are 44 on main and 25 on PR #140; ⑬-2/a3, ⑬-2/k, ⑬-1/c | Windows PC check; OA-16; OA-29; who continues PR #140 |
| WEBSITE | ACC-1 to ACC-8 on `xkg4real/website` `auth-preview` 2d3bf4c, flag off (session record of 11-20; other repository, not verified) | policy text regeneration; ACC-9; flag-on checklist; queued JSON | prod-pool manual test; dev-pool client ID; OA-04, 05, 33; W8 |
| RESEARCH | none | WORKBOARD 2.7 unchanged; ⑧-1 H-D5 due about 12-19 | OA-15, 19, 26, 27, 28 |

## 3. Stale rows and replacement text

Line numbers are from handoff 38ccd06.

### 3.1 MERGE_QUEUE.md

- **L1-250** (GPT narrative above the title): move below "규칙" as history. L1-3 still says the next slot is T8-6, which is merged.
- **L254**: `updated_at: 2026-11-24T18:05:00+09:00`
- **L256**: `coordinator: QUANTGEN/MAIN Claude (session_01H6RrzMUzF8vwK8xkX977mB). 2026-11-21~23은 메인 Codex가 맡음(아래 이력)`

| Row | Replace with |
|---|---|
| L323 (5) | `\| 5 \| UI 7쪽 + PySide6 준비 + 11-21~23 UI 변경 + KEY-5 K1a~K2d \| PR #140 draft, gpt/ui-guide-chart-first-20261121 @ 3483b53 (414eceb 포함) \| CI 실패(Ubuntu 3.12·Windows 3.11), main과 충돌. 고친 뒤 소유자 Windows 확인 → 병합. 담당 미정 \|` |
| L327 (4g) | `\| 4g \| ~~DS·DIDM 코드 통합~~ \| PR #138 (6cff168) → **main 53e5e72** \| 완료 11-21 19:45. 원장 DIDM-1, DS-4a \|` |
| L328 (4h) | `\| 4h \| ~~KEY-5/a + 검토 M1·M2~~ \| PR #139 (0413cc5) → **main dec979a** \| 완료 11-21 22:00. 원장 KEY-5/a. 11-24 main에서 M1·M2 확인, 게이트웨이 시험 83 OK \|` |
| new 4i-4n | `\| 4i \| ~~DIDM EODHD 입력~~ \| PR #142 → d835d9f \| 완료 \|`<br>`\| 4j \| ~~Android 내부 프리뷰~~ \| PR #141 → 666e006 \| 완료. APK·기기 확인 남음 \|`<br>`\| 4k \| ~~Alpaca 뉴스 입력~~ \| PR #143 → 5af3787 \| 완료 \|`<br>`\| 4l \| ~~Massive 뉴스 입력~~ \| PR #144 → 51b8298 \| 완료 \|`<br>`\| 4m \| ~~DIDM V0 ID·해시 검사~~ \| PR #145 → 05f97df \| 완료 \|`<br>`\| 4n \| ~~push_handoff.py --doc~~ \| PR #146 → b872d8c \| 완료. 원장 병합 행 추가 필요 \|` |
| L329 (7) | `\| 7 \| KEY-5 남은 화면 접점 (PR #140 기준 8파일 25곳) \| 요청문 v2(PAYMENTS) + UI 구현 \| 5 뒤 \|` |
| L332 (GH-2) | `\| 11 \| GH-2 정리 \| PR #147 draft @ bf78b6b \| 문서 정합성 FAIL(문서 20개 재검토 표시) → 기준선 갱신 필요. _backup/·archive 태그는 범위 밖 \|` |
| new 9, 10, 12, 13, 14 | `\| 9 \| Claude 스킬·quant-analyst \| PR #148 @ 462f7df \| 문서 검사 성공. 메인 검토 뒤 병합 \|`<br>`\| 10 \| PAY-0·PAY-2 문서 12개 \| claude/payments-pay0-20261120 @ e869064 \| PR 없음. 병합: PAYMENTS 대기 \|`<br>`\| 12 \| Android APK 검사 도구 \| gpt/android-apk-evidence-20261123 @ c28194f \| PR 없음. 최신 main 합치고 기준선 다시 \|`<br>`\| 13 \| Kalshi 입력 검사 + ALFRED 개정값 기간 \| 77c37c5, 593c943 \| PR 없음. 한 PR로 묶기 제안 \|`<br>`\| 14 \| 새 세션 등록(LANE_DOCS에 DIDM·QUANTGPT, QGPT-00) \| 메인 \| push_handoff.py 63~69행은 세 세션 이름만 받음 \|` |

### 3.2 WORKBOARD.md

- **L1-262** (GPT blocks above the title): move to an appendix; the same text is duplicated in MERGE_QUEUE L42-250.
- **L274-275**: `기준 시각: 2026-11-24 18:05 KST` / `git 기준: main b872d8c · handoff 38ccd06 · PR #140 3483b53 · PR #147 bf78b6b · PR #148 462f7df`
- **L295-302** (session map): rows for MAIN, PAYMENTS_ACCOUNT_KEYS, OS_EXPANSION, `DATA_SOURCING (전 DATA_SOURCE_DIDM)`, `DIDM (새로 만듦)`, `QUANTGPT (새로 만듦)`, UI/UX (`PR #140 draft, 담당 미정`), WEBSITE/AWS (`11-20 계정 화면 구현, 그 뒤 기록 없음`), TRADEGEN (`QuantGPT 명세 공유 대상`).
- **L312**: `다음 리셋 2026-12-01 17:00 KST`
- **L314 and L568**: `24시간 안 열린 항목: 6개 (OA-47, OA-03, OA-04, OA-05, OA-09, OA-10)`
- **L574**: `정기 점검: trig_01P2NBVZFChNHJGjVdtrDTyC는 꺼져 있음(마지막 실행 11-20 03:20 KST). 다시 켤 때 지시문의 "하부 세션 3곳"을 5곳으로`
- **L318-332** (section 1): replace the whole list with the open items of 1.4 above plus the lock.

| Line | Replace with |
|---|---|
| L343 | `- [x] 병합 차례 4e~4h 끝 — 72a055f, 6d25a33, 53e5e72, dec979a. 그 뒤 GPT 병합 #142, #141, #143, #144, #145, #146(b872d8c). 지금 대기: MERGE_QUEUE 9~14` |
| L360 | `- [~] GH-2 — PR #147 draft(bf78b6b), 문서 정합성 FAIL. QuantGPT 명세 3.6절이 test_npu.py를 참조하므로 삭제 전 확인. 비밀 검사 CI는 OA-17` |
| L361 | `- [ ] 정책 문서 PR-2 — 관문 풀림: AWS 운영 풀 끝, 웹 계정 화면은 website auth-preview 2d3bf4c(플래그 꺼짐, 미검증)` |
| L363 | `- [x] 2.7 push_handoff.py --doc — PR #146 → main b872d8c. 원장 병합 행 없음 → 추가` |
| L408 | `- [x] KEY-5/a — PR #139 → main dec979a, 원장 KEY-5/a. M1·M2 고쳐짐(11-24 확인). S4~S7 미검증` |
| L409-410 | append `11-24 확인: e869064, main보다 5커밋 앞, 문서 12개 모두 main에 없음` |
| L427 | `- [x] PySide6 간헐 종료 기록 — PR #136에 5커밋 포함, 내용이 35e095f와 같음. 원장 OS-F1/a 행은 없음` |
| L429 | `- [x] OS-F2 — PR #136 → main 72a055f, 원장 OS-F2. code_sha256 bcaf33d9…(11-24 다시 계산). 실제 소유자 자료 이전은 안 함` |
| L435 | `- [~] OS-A1 — PR #141 → main 666e006. APK 검사 도구 c28194f 미병합. platform-build 실행 0회` |
| L441-442 | `- [~] DS-1 / DIDM-0 — 문서가 main에 있음(53e5e72). 원장 행 없음 → 닫을지 메인 판단` |
| L443-444 | `- [x] DIDM-1, DS-4a — PR #138 → main 53e5e72` |
| L447-448 | `- [~] DS-4d, DS-4e — 커넥터 main에 있음(53e5e72), 원장 행 없음. Kalshi 보완 77c37c5 미병합` |
| L449 | `- [~] DS-H — DS-H/code 끝(PR #137 → 6d25a33). 남음: OA-09, OA-46, UI 연결` |
| L464-470 | `- [~] UI 7쪽 + PySide6 준비 + KEY-5 K1a~K2d — PR #140(3483b53)에 포함. 화면 접점 44곳 → 25곳` |
| L493-502 | `- [~] ACC-1~ACC-8 — website auth-preview 2d3bf4c, 플래그 꺼짐(미검증)` / `- [!] ACC-9 — 개발 풀 웹 클라이언트 ID + 운영 풀 수동 1회` |
| L562 | append `(main b872d8c = bcaf33d9…, 표 두 개는 f995600b…. OS-F2 병합으로 선행 조건 풀림)` |

## 4. Next tasks for the three existing sub-sessions

Every instruction should start with: "Your own `*_SESSION_CURRENT.md` is out of date. OS-F2, DS-H/code, DIDM-1, DS-4a and KEY-5/a are in the ledger; do not redo them."

### PAYMENTS_ACCOUNT_KEYS

**P1. PAY-0 and PAY-2 documents ready for a PR**
- Goal: bring `claude/payments-pay0-20261120` (e869064) up to main.
- Files: `docs/commercial/inquiries/*.md` (8), `docs/commercial/payments/*.md` (4).
- Done when:
  - `git merge --no-edit origin/main` → no conflicts.
  - `git diff --name-only origin/main...HEAD` → exactly those 12 paths.
  - `grep -c 'docs/commercial' docs/compliance/source-review.json` → 0.
  - `python -B -m tools.compliance.check --check` → PASS. If it fails, report; do not refresh the baseline.
- Do not: open a PR before "병합: PAYMENTS_ACCOUNT_KEYS"; send inquiries; decide P2-01 to P2-15.

**P2. KEY-5 request v2 (handoff document only)**
- Goal: re-base `plans/2026-11-20/KEY5_UI_REQUEST.md` from 148504a onto main and PR #140.
- Done when the document lists the 25 remaining sites by file, row 14 points at `core.gateway.feed.QuoteFeed`, and it records that OA-41 has no owner answer. Check with:
  - main fixture `tests/fixtures/gateway/known_direct_calls.json` → 23 files, 45 entries.
  - `git show origin/gpt/ui-guide-chart-first-20261121:tests/fixtures/gateway/known_direct_calls.json` → totals `{'core_and_main': 1, 'files': 9, 'screens': 25}`.
- Do not: edit `quantgen_desktop/**`, `ui/**` or any `gpt/*` branch.

**P3. KEY-5/a close-out (S4 to S7)**
- Goal: check each small finding on main and add a test only where a gap is real.
- Done when there is a fixed / not-fixed table with file and line, and the five gateway suites report at least 83 tests, OK.
- Do not: touch `core/engine/**` or `config.py`.

### OS_EXPANSION

**O1. Android APK evidence tool PR**
- Goal: branch from c28194f, merge main, regenerate the baseline last.
- Files: `platform-build.yml`, `tools/packaging/android_apk_evidence.py`, `tests/android_apk_evidence_acceptance.py`, `ANDROID_INTERNAL_PREVIEW_VALIDATION_2026-11-23.md`, `FACTS.md`, `source-review.json`.
- Done when:
  - `python -B -m unittest tests.android_apk_evidence_acceptance` → Ran 8, OK.
  - the five packaging and qt_port suites → Ran 34, OK.
  - `git diff --name-only origin/main...HEAD` → those 6 paths.
  - `--check` → PASS.
- Do not: run `platform-build.yml`, sign anything, push to the `gpt/` branch.

**O2. PySide6 re-check against PR #140 (read and test only)**
- Goal: the verdict in PYSIDE6_TRIAL section 9 was for 414eceb; the UI head is now 3483b53.
- Done when:
  - `python tools/qt_port/pyqt6_to_pyside6.py --lint --ref origin/gpt/ui-guide-chart-first-20261121` → counts per rule next to the 414eceb numbers.
  - `python tools/qt_port/switch_day.py --check` → 7 places "to do".
  - a scratch copy with PySide6 6.12.0 runs the four market-tab modules 160 times with 0 aborts.
- Do not: push to the UI branch, edit `quantgen_desktop/**` or `tests/desktop_*`, run `--apply` in a real checkout.

**O3. Owner step sheet for the data-folder move**
- Goal: one page from `docs/product/OS_DATA_STORAGE_2026-11-21.md` saying whether the owner should move at all (TRADEGEN shares the token file), how to check, how to undo.
- Done when the page exists on a branch and the three path suites → Ran 93, OK (skipped=3).
- Do not: open `~/.nextgen`.

### DATA_SOURCING (was DATA_SOURCE_DIDM)

**D1. Connector fixes in one PR**
- Goal: Kalshi input validation (77c37c5) and ALFRED vintage period (593c943) on top of main.
- Files: `core/didm/ingest/kalshi.py`, `data/didm/kalshi.py`, `core/didm/ingest/alfred.py`, two test files, `source-review.json` regenerated last.
- Done when:
  - `tests.didm_sources_acceptance` → Ran 31, OK.
  - `tests.didm_ingest_acceptance` → Ran 27, OK.
  - the seven-module DIDM list → OK (152 expected by arithmetic; not run on the merged tree).
  - the three parser suites → Ran 56, OK.
  - `git diff origin/main -- core ':!core/didm' ':!docs/asset_expansion/cache'` → empty.
- Do not: make live provider calls, enable Polymarket, touch `core/gateway` or `data/krx/**`.

**D2. One-command home-indicator diagnostic for the owner**
- Goal: replace the old H4 command now that `load_home_indicators` is on main (`core/research/markets.py:209`). It prints six rows with status and reason code only.
- Done when the command exits 0 in the cloud with six rows and no traceback, and `tests.home_indicators_acceptance` → Ran 23, OK.
- Do not: edit UI files or change `load_markets`.

**D3. Wiring plan for the three new providers (document only)**
- Goal: record what main has (pure parsers; no HTTP client for EODHD or Alpaca in `data/didm/`), the key names to request from PAYMENTS, and an owner sign-up table.
- Done when `python -m tools.didm.check_vendor_eval --excel <handoff copy>` → `excel cells changed: 0`.
- Do not: edit `core/credentials/**`.

## 5. OWNER_ACTIONS

### 5.1 Open and due within 24 hours or blocking a session now: 6

| ID | Item | Blocks |
|---|---|---|
| OA-47 (new) | Confirm GPT has stopped and approve taking over CURRENT.md with `--force`. Same question: who continues PR #140 and PR #147. | MAIN |
| OA-09 | Run the home-indicator diagnostic and paste the output (asked since 11-17) | DATA SOURCING |
| OA-10 | Three DIDM answers: (a) novelty side condition, (b) own-LLM base model and training cutoff, (c) two evaluation cells | DIDM |
| OA-03 | One-line answer on SES no-reply verification | PAYMENTS |
| OA-04 | Password rule "one special character": tell the website session whether the pool requires it | WEBSITE |
| OA-05 | Paste the policy-text regeneration prompt (PR-130.json); the session did resume on 11-20 | WEBSITE |

Suggested push text: `QUANTGEN: 오늘 직접 하실 일 6건 — GPT 인계 잠금 해제 확인, 홈 지표 진단 실행, DIDM 질문 3개, SES 한 줄 답, 웹사이트 글 2건 전달 (WORKBOARD 3절)`

Not counted: the Windows check of PR #140 (old OA-06), because the PR is red and conflicting, so there is no head worth checking yet.

### 5.2 Every other OA item

| ID | Status now |
|---|---|
| OA-01, 02, 07, 08, 42, 44 | done |
| OA-06 | superseded by the Windows check of PR #140; open, waits for a green head |
| OA-11, 45 | open |
| OA-12 | done in substance on 11-20 (website record; not verified in that repository) |
| OA-13 | T1 to T15 done. Next: one prod-pool manual test on the preview, T16 to T19b, W9, W10, dev-pool client ID, console checks C3, C4, C6, P10, P12 |
| OA-14, 15, 16, 20, 22, 23, 27, 28, 29 | open, no change |
| OA-17 | open; PR #147 has no secrets-check CI |
| OA-18 | on hold until the UI merge |
| OA-19 | on hold until the next recording run; OS-F2 precondition met; main is bcaf33d9…, tables f995600b… |
| OA-21, 31, 35 | on hold |
| OA-24, 25 | optional |
| OA-26 | open; warning 12-05, deadline about 12-19 |
| OA-30 | open; no platform build has run. Order: merge the APK tool, then the owner runs the Android-only build and checks the phone |
| OA-32, 39, 40 | open; PAYMENTS is told not to do new research until answered |
| OA-33 | open; three more JSON records now (PR-134, 140, 141) |
| OA-34 | unclear: GPT marked it unnecessary under its single-window rule |
| OA-36, 37, 38 | open, never asked |
| OA-41 | open; GPT proceeded with option 가 as a technical choice |
| OA-43 | cause resolved 11-20. Follow-ups open: CPU credits to Standard, narrow port 22, optional CPU alarm. No deadline. |
| OA-46 | open |
| QuantGPT U-01, U-02 | due 2026-11-30 (spec section 9); U-01 blocks QGPT-01 |

## 6. Contradictions between documents

1. **CURRENT.md front matter vs its body.** `work_branch` and `pr` point at #141, merged 11-23 04:45; the body describes #146, #147 and #140. `status: taken` sits next to `returned_at`.
2. **MERGE_QUEUE L1-3 and WORKBOARD L9 vs git.** Both say T8-6 is next or open; PR #146 is merged, and GH-2 already has PR #147.
3. **Sub-session documents vs ledger.** PAYMENTS (`next_ids: KEY-5/a`, dc936d4) and OS (`next_ids: OS-F2`, e44c48e) list finished IDs as next.
4. **Who coordinates and how UI is reached.** MERGE_QUEUE L256 and WORKBOARD L308 say main Codex and a single window for UI; SESSION_PIPELINE sections 1 and 6 say Claude main and UI only through the owner.
5. **"KEY-5 K3, 13 sites remain"** (WORKBOARD L70, L150) vs the fixture on PR #140: 25 screen sites in 8 files. The 12 outside K3 are in `ui/settings_page.py` (8), `paper.py`, `crypto_page.py`, `macro_page.py`, `macro_state_panel.py`.
6. **OA-43.** Its row says resolved; the header (L568) still counts it; GPT's blocks (L8, L20) keep it open for cost attribution. Inside the row the credit mode is "changed to Standard" and later "to be set back to Standard".
7. **Owner-item count.** L314 says 10, L568 says 7.
8. **Pipeline check.** SESSION_PIPELINE 2-6 and WORKBOARD L574 describe a running 3-hourly task; the trigger is disabled.
9. **Ledger shape.** Rows after L290 use IDs not in `REMAINING_WORK_2026-11-17.md` (T8-5, T8-6, B6, UI-140/…, PC7). Rows L311, L313, L315 have no cycle column. The DS-4a row names `core/didm/store.py` and `core/didm/ingest.py`; main has packages.
10. **Missing ledger rows.** PR #146 merge, DS-1, DIDM-0, DS-4d, DS-4e, OS-F1/a.
11. **QuantGPT spec vs current rules.** Section 1.1 has the sub-session write `--done` itself; WORKBOARD L310 says sub-sessions do not write the ledger. Section 3.6 cites `test_npu.py`, which PR #147 deletes. `LANE_DOCS` has no file name for DIDM or QUANTGPT.
12. **PR #148** is in no document.

## KEY FACTS
- origin/main is b872d8c (PR #146 merge, 2026-11-23 12:24 KST) and origin/handoff is 38ccd06 (2026-11-23 12:43 KST); both checkouts match the remote tips.
- GPT merged 10 PRs after f065ec9: #136 72a055f, #137 6d25a33, #138 53e5e72, #139 dec979a, #142 d835d9f, #141 666e006, #143 5af3787, #144 51b8298, #145 05f97df, #146 b872d8c.
- Four Claude sub-session branches are ancestors of main: os-f2 e44c48e (via PR #136), key5a dc936d4 (via PR #139), ds-home-indicators f80b3b0 (via PR #137), data-source-didm c206b10 (via PR #138). GPT amended files in each on top.
- claude/payments-pay0-20261120 @ e869064 is NOT merged: 5 commits ahead of merge-base fa78df1, 12 docs under docs/commercial/inquiries and docs/commercial/payments, none on main, no overlapping commits on main.
- KEY-5/a review finding M1 is fixed on main: core/gateway/feed.py:38-66 re-checks gateway.blocked('fmp') on every access and look_again discards even a working client; listener registered at line 94.
- KEY-5/a review finding M2 is fixed on main: core/gateway/__init__.py:529-546 builds an unpublished candidate, gates it under _lock and publishes with one assignment; _KRX_BUILT is accessed under _lock.
- Tests run by me on main b872d8c with isolated HOME: gateway 5 suites 83 OK; home indicators 23 OK; DIDM 7 modules 140 OK; EODHD/Alpaca/Massive 56 OK; app_paths/storage/credentials 93 OK (3 skipped); qt_port group 34 OK; handoff_doc 16 OK.
- CURRENT.md on handoff is status: taken, from: gpt, updated 2026-11-23T12:43:31+09:00; tools/handoff/push_handoff.py:341-343 refuses a publish from another agent over a taken lock regardless of staleness unless --force.
- Open PRs: #148 (claude/quant-skills-20261123 @ 462f7df, not draft, opened 2026-11-24 17:10 KST, consistency check success), #147 (GH-2 draft @ bf78b6b, consistency check FAIL: 20 documents need review), #140 (UI draft @ 3483b53, conflicts with main, Ubuntu 3.12 and Windows 3.11 failures, Windows 3.12/3.14 cancelled), #12 (open since 10-29).
- Unmerged verified GPT branches with no PR: android-apk-evidence c28194f (8 tests OK), didm-kalshi-input-validation 77c37c5 (sources 31 OK vs 22 on main), didm-alfred-vintage-period 593c943 (ingest 27 OK vs 24 on main).
- PR #140 head contains Claude UI 414eceb and K2d 7d9a4d3 as ancestors; KEY-5 screen call sites are 44 in 22 files on main and 25 in 8 files on PR #140 head.
- Nautilus code_sha256 recomputed on main = bcaf33d91adb5c3a2b1c4a181e0827ed17fe8768827539fe7bd8ecbaea0bb34c; both registration tables still carry code f995600b36c75523; no owner/* branch exists.
- The PySide6 abort records are on main by cherry-pick inside PR #136 (f9a3a75, a342cd2, 0b8f6c2, f993458, 5b83262); the five files are byte-identical to claude/os-pyside6-abort-20261119 @ 35e095f.
- push_handoff.py --doc exists on main (line 595) but LANE_DOCS (lines 63-69) only accepts OS, PAYMENTS, DATA_SOURCE, UI and WEBSITE file names; DIDM and QUANTGPT have none.
- Trigger trig_01P2NBVZFChNHJGjVdtrDTyC (3-hourly pipeline check) is disabled; last fired 2026-11-19T18:20Z; its prompt names three sub-sessions.
- platform-build.yml has 0 workflow runs; no archive-* tags exist on the remote.
- docs/commercial and .claude are not referenced in docs/compliance/source-review.json (0 matches each), so the PAY-0/PAY-2 docs and PR #148 do not contend for the baseline file.
- Ledger has rows OS-F2, DS-H/code, DIDM-1, DS-4a, KEY-5/a (lines 286-290). It has no row for the PR #146 merge, DS-1, DIDM-0, DS-4d, DS-4e, OS-F1/a, PAY-0 or PAY-2.
- Owner items open and due within 24 hours or blocking a session now: 6 (lock takeover, OA-09, OA-10, OA-03, OA-04, OA-05). Last push was 2026-11-20 00:51 KST.

## OWNER ACTIONS
- [24h] OA-47 (new): confirm GPT has stopped and approve Claude taking over CURRENT.md with --force (or have GPT publish status: returned). In the same answer say who continues UI PR #140 and GH-2 PR #147. — CURRENT.md is status: taken by gpt since 2026-11-23 12:43 KST. The publishing tool refuses a Claude publish over it, so CURRENT and ledger rows cannot be written. Blocks the main session now. (src: handoff CURRENT.md L2-9 (38ccd06); tools/handoff/push_handoff.py:341-343; CLAUDE.md handoff protocol)
- [24h] OA-09: run the home-indicator diagnostic on the owner PC and paste the output. — DS-H parent stays open without it; DS-H/code is merged (6d25a33) but the cause of the empty Home indicators is not identified. Asked since 2026-11-17. (src: WORKBOARD.md L588; DATA_SOURCE_SESSION_CURRENT.md L88, L256)
- [24h] OA-10: answer three DIDM questions: (a) make the novelty side condition formal or not, (b) own-LLM base model and training-data cutoff, (c) confirm two evaluation-table cells. — Blocks the new DIDM session's evaluation plan and MODEL_CUTOFFS.md (not on main). The QuantGPT spec names Qwen3 candidates but fixes neither model nor cutoff. (src: WORKBOARD.md L589; DATA_SOURCE_SESSION_CURRENT.md L249-255; QuantGPT spec sections 3.6 and 4 (D5))
- [24h] OA-03: one-line answer whether SES no-reply was Verified at once or needed a Cloudflare rule. — Open since 2026-11-19, marked 24h in WORKBOARD; PAYMENTS records it in OWNER_STEPS. (src: WORKBOARD.md L582)
- [24h] OA-04: tell the website session whether the Cognito pool requires one special character in passwords. — The website session's password hint list lacks the rule and asks to be told if it was turned on. (src: WORKBOARD.md L583; WEBSITE_AWS_SESSION_CURRENT.md L77)
- [24h] OA-05: paste the policy-text regeneration prompt (PR-130.json) into the website session. — The website session resumed on 2026-11-20 but the public policy still shows the old operator wording; regeneration is item 1 of its flag-on checklist. (src: WORKBOARD.md L584; WEBSITE_AWS_SESSION_CURRENT.md L93)
- [later] Windows PC check of UI PR #140 (replaces OA-06). — Needed before the UI merge, which gates OS-F1 and the rest of KEY-5. Not actionable today: head 3483b53 has failing CI and conflicts with main. (src: GitHub check-runs for 3483b53; WORKBOARD.md L6, L585; MERGE_QUEUE.md L323)
- [later] OA-43 follow-ups: set EC2 CPU credits to Standard, narrow SSH port 22 to the owner IP, optional CPU alarm. — Cause was resolved 2026-11-20 (two orphaned editor processes killed). These are hygiene steps with no deadline and block no session. (src: WORKBOARD.md L590; task brief)
- [later] OA-30: after the APK evidence tool is merged, run platform-build.yml with Android only and check first launch and the example calculation on the phone. — No platform build has ever run; the Android internal preview (PR #141, 666e006) has no APK or device evidence. (src: GitHub Actions API (0 runs); WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md L17)
- [later] OA-32, OA-39, OA-40: review and send the 7 payment inquiries, decide P2-01 to P2-15, choose the company data server location. — PAYMENTS is instructed not to do new research on PAY-0/PAY-2 until these are answered. (src: WORKBOARD.md L620, L627, L628; PAYMENTS_SESSION_CURRENT.md L31)
- [later] OA-13 next steps: one manual test on the production pool through the locked preview, then T16 to T19b and W9 to W10; give the dev pool web client ID; confirm console items C3, C4, C6, P10, P12. — The website account screens are built with the flag off and wait for these before the flag can be turned on. (src: WEBSITE_AWS_SESSION_CURRENT.md L66-97; PAYMENTS_SESSION_CURRENT.md L32)
- [later] OA-46: choose the Home BTC unit (KRW live and USD daily shown separately, or one unit). — Needed to close the DS-H parent and for the UI wiring of the home indicators. (src: WORKBOARD.md L593)
- [later] QuantGPT U-01 and U-02: approve or create the private quantgpt repository with a CI deploy key; create a Hugging Face account and store the read token locally. — Spec deadline 2026-11-30. U-01 blocks QGPT-01. (src: QuantGPT spec v1.0 section 9)
- [later] OA-19: rewrite the two owner_confirmed lines right before the next Nautilus recording run. — main's code fingerprint is now bcaf33d9… after OS-F2; the tables still say f995600b…. The OS-F2 precondition is met; no run is scheduled. (src: recomputed on main b872d8c; docs/nautilus_bridge/registration/*.json; WORKBOARD.md L607)
- [later] OA-26: make the ⑧-1 H-D5 main commit from a separate clone on the owner PC. — Deadline about 2026-12-19, warning date 2026-12-05. (src: WORKBOARD.md L539, L614)
- [later] OA-17, OA-36, OA-37, OA-38, OA-41: secrets-check CI for GH-2; close old PR #12 and whether to use its IDs; two unpushed GPT commits; confirm DS-3 dropped; set_backend option. — OA-36, 37 and 38 were never asked. For OA-41 GPT proceeded with option 가 without an owner answer. (src: WORKBOARD.md L605, L624-626, L629)

## OPEN QUESTIONS
- Does the owner's request today count as the say-so for --force over GPT's taken lock, or should the main session ask one explicit yes/no first? GPT's last note says it was still reproducing the PR #140 Ubuntu failure, so it may hold unpushed work.
- Who continues UI PR #140 (red CI, conflicts with main): GPT, the separate Claude UI session through the owner, or the main session? GPT's 2026-11-21 single-window rule and SESSION_PIPELINE sections 1 and 6 disagree.
- Should DS-1, DIDM-0, DS-4d and DS-4e get ledger rows now? Their files are on main at 53e5e72 and owner-PC checks are recorded, but GPT recorded only DIDM-1 and DS-4a.
- Should the PR #146 merge and the PySide6 abort records (planned ID OS-F1/a) get their own ledger rows?
- Should GH-2 PR #147 keep deleting test_npu.py while QuantGPT spec section 3.6 cites it as the existing NPU test path?
- In what order should the UI merge, OS-F1 and the remaining 25 KEY-5 sites go? 12 of the 25 are outside the K3 step GPT named.
- May QUANTGPT and DIDM sub-sessions write the ledger with --done themselves (QuantGPT spec 1.1) or only through the main session (WORKBOARD L310)?
- Which file names and task names should the new sessions use in LANE_DOCS, and does DATA_SOURCE_SESSION_CURRENT.md keep the task name data-source-didm after the split?
- Should PAY-0 and PAY-2 drafts merge to the public main before the owner has reviewed the inquiry letters (OA-32)?
- Is the EC2 instance currently on Standard or Unlimited CPU credits? The OA-43 row says both at different points.
- Where are the IDs T8-5, T8-6, B3/B6 and PC7 defined? They are not in docs/nautilus_bridge/REMAINING_WORK_2026-11-17.md.
- How does the main session reach the TRADEGEN session to share the QuantGPT material: directly or through the owner?

## UNVERIFIED
- Everything in the xkg4real/website repository (auth-preview 2d3bf4c, ACC-1 to ACC-8, preview lock, public site hash): taken from WEBSITE_AWS_SESSION_CURRENT.md only.
- KEY-5/a small findings S4 to S7; S1 to S3 were judged from a short code read, not from tests written for them.
- Performance impact of GatedKRXGateway._run holding the module lock during a provider call.
- Whether python -B -m tools.compliance.check --check passes locally on main; I did not run the checker. The GitHub consistency check on b872d8c reports success.
- Why no Runtime packaging smoke check-run is attached to the main head b872d8c.
- The expected 152 tests for the seven DIDM modules after merging both connector branches is arithmetic (140 + 9 + 3), not a run on the merged tree.
- That merging origin/main into claude/payments-pay0-20261120 is conflict-free and needs no baseline change; inferred from path absence and zero source-review references.
- GPT's own test counts and independent-review claims beyond the suites I re-ran, including all Windows results.
- tests.mobile_startup_acceptance, the PySide6 lint counts on PR #140 head and the provider-parity suites were not run.
- T8-5 private draft, B6_PROVIDER_MAPPING and other private GPT files named in the handoff are not in the repository.
- Whether the owner ran the PR #140 preview on a Windows PC; the documents record owner feedback on 11-22 but every note still lists the PC check as not done.
- State of the sub-sessions themselves (alive, idle, archived); I did not query them.
- Notion REMAINING WORK page contents and GPT's Notion sync claims.
- Whether the malformed ledger rows (L311, L313, L315) affect the tool's duplicate-ID check.
- Research-track status beyond the absence of new commits to the fingerprint inputs other than config.py.
