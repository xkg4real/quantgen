<!-- GPT 작업 검증 (메인 워크플로 wf_831f72a0-085, 2026-11-24). 읽기 전용 분석 에이전트의 보고 원문(영어). 인수(handoff 8a93ce6) 전 시점 기준이라 '잠금' 관련 문장은 그 뒤 풀렸다. -->

# GPT (Codex) work 2026-11-20..11-23, checked against git and GitHub

Checked 2026-11-24 about 18:05 KST. Main is `b872d8c`; the handoff branch is `38ccd06`, same as the remote.

**Bottom line:** GPT's 10 merges to main are real and were green in CI on exactly the merged trees. The frozen-engine, qa-results, owner_confirmed and secrets rules were not broken. But GPT left `CURRENT.md` as `status: taken`, so Claude's publish will be refused until the owner decides the lock.

## 1. Merged PRs since f065ec9

For all ten: the merge commit's tree equals the tested PR head's tree, and every check run on that head succeeded before the merge. No PR has a GitHub review object.

| PR | Merge (KST) | Merge / head | What it did | Ledger row | Verified |
|---|---|---|---|---|---|
| #136 | 11-21 14:16 | `72a055f` / `64ff58e` | OS-F2: user data folder selection, prepare-before-write, consent-only migration API; includes Claude's `e44c48e`. 25 files | OS-F2 (line 286) | Yes. 8/8 checks. `config.py` and `main.py` keep CRLF. |
| #137 | 11-21 17:33 | `6d25a33` / `4973111` | DS-H: six home indicators contract in `core/research/markets.py`, test, doc | DS-H/code (287) | Yes. 8/8. |
| #138 | 11-21 19:45 | `53e5e72` / `6cff168` | DIDM ingest, point-in-time store, score schema, novelty, connectors, collector CLI (Claude `c206b10` plus GPT fixes). 45 files | DIDM-1, DS-4a (288, 289) | Yes. 8/8. `PREREG_V0.md` unchanged. The DS-4a row names `core/didm/store.py` and `ingest.py`; they are packages. |
| #139 | 11-21 22:00 | `dec979a` / `0413cc5` | KEY-5/a: shared QuoteFeed, stale FMP client invalidation, atomic KRX refresh (Claude `dc936d4` plus `45db2be`) | KEY-5/a (290) | Yes. 10/10. |
| #142 | 11-23 03:15 | `d835d9f` / `90d3b4b` | DIDM EODHD supplied-input parser, no network code | "DIDM B6 EODHD 입력 코드 (하위 진척)" (316) | Yes. 8/8; 18 tests rerun OK. The ID shape is invalid. |
| #141 | 11-23 04:45 | `666e006` / `a35b2f8` | Android internal preview (`mobile/main.py`, staging, GBM example). Moves the `History` class body to new `core/quant/supplied_history.py`; lazy imports in `core/quant/montecarlo.py` | OS-A1/gbm-preview/main (325) | Commit and CI yes (8/8). The row lists `core/research`, which did not change. No APK or phone test. |
| #143 | 11-23 06:39 | `5af3787` / `5039835` | DIDM Alpaca news parser | DIDM/B6/alpaca-main/1 (335) | Yes. 20 tests rerun OK. |
| #144 | 11-23 08:34 | `51b8298` / `aa25d27` | DIDM Massive news parser | DIDM-B6/massive-news/main-20261123 (340) | Yes. 18 rerun OK. |
| #145 | 11-23 10:29 | `05f97df` / `91be74d` | DIDM V0 ID and hash `match` to `fullmatch` (2 lines) | DIDM-V0-145-main-c410 (345) | Yes. 26 rerun OK. |
| #146 | 11-23 12:24 | `b872d8c` / `5200b6c` | `push_handoff.py --doc` for sub-session documents | Only the pre-merge row (346) | Commit and CI yes; 16 tests rerun OK. **No ledger row for the merge.** |

Roadmap IDs now finished and not to be redone: OS-F2, DS-H/code, DIDM-1, DS-4a, KEY-5/a. None of `next_ids` is in the ledger.

## 2. In-flight work

PR #141 is merged, not open. Open PRs are #148, #147, #140 and #12.

| Item | State | What fails | What is left | Who |
|---|---|---|---|---|
| PR #140 UI | Draft; `gpt/ui-guide-chart-first-20261121` @ `3483b53`; 66 commits, 121 files; mergeable `dirty`; updated 11-23 11:25 | Runtime: ubuntu 3.12 FAIL and windows 3.11 FAIL on the same test (`tests/desktop_stock_detail_acceptance.py:1527`, focus assertion); windows 3.12 and 3.14 cancelled at the 120-minute limit; syntax 3.10/3.11 and document consistency pass | Fix the focus regression; get Windows under 120 minutes; merge main (conflicts in `runtime-smoke.yml` and `source-review.json`); owner Windows PC7 check | UI session through the owner. It also carries Claude UI `414eceb`, KEY-5 K1a-d/K2a-d and a `config.py` change, so the owner must route it. |
| PR #147 GH-2 | Draft; `gpt/gh2-unused-tools-20261123` @ `bf78b6b`; mergeable `unstable`; updated 11-23 12:27 | "Document and source consistency" FAIL (20 documents, 855 sources). No Runtime run (path filter) | Refresh `docs/compliance/source-review.json`; ledger row GH-2. `_backup/` only after an `archive-2026-11` tag, which does not exist | Claude main can continue. The PR removes only `test_npu.py`, five `mindmap/` files and the `godseye-dev` launcher entry, as the roadmap says. |
| ALFRED revision check | Branch `gpt/didm-alfred-vintage-period-20261123` @ `593c943`, one commit on `05f97df`, no PR | Nothing; its test module passes here (27 tests, Python 3.13) | Merge main, refresh source-review, PR, CI, ledger | Claude (data or DIDM sub-session) |
| Kalshi input validation | Branch `gpt/didm-kalshi-input-validation-20261123` @ `77c37c5`, no PR | Nothing; 31 tests pass here. Will conflict on `source-review.json` | Same | Claude (DIDM sub-session) |
| Android APK check tool | Branch `gpt/android-apk-evidence-20261123` @ `c28194f`, no PR; edits `platform-build.yml` | Nothing; 8 tests pass here | PR after GH-2; then the owner runs Platform build (Android only) and tests on a phone | OS sub-session, then owner |
| KEY-5 K3 (13 call sites) | Not started | | Waits for #140 and PC7 | PAYMENTS sub-session |
| OS-F1 PySide6 switch | Not started | | Waits for the UI merge and "OS go" | OS sub-session |
| PR #148 | Open, not draft; `claude/quant-skills-20261123` @ `462f7df`; mergeable `unstable`; document consistency passes; updated 11-24 17:10 | | Claude's own PR | Claude |
| PR #12 | Open since 10-29; `gpt/handoff-continuation-20261029` @ `45e2d3e`; not draft; no check runs; mergeable `unknown` | | Owner decision OA-36 | Owner |

## 3. Owner decisions GPT recorded, and rules that bind Claude

Only two documents quote the owner verbatim:

- `GPT_WORK_ALLOCATION_APPROVAL_2026-11-21.md`: "정리해서 당신이 어떻게 분담하여 어떤 업무를 진행할지, 정리해서 승인요청해주세요." The document itself still says approval is pending.
- `UI_TO_MAIN_CODEX_2026-11-21.md` section 0: "앞으로 QUANTGEN 메인 Codex 세션이 작업을 총괄합니다. … 새로운 구현은 시작하지 마세요. 메인 세션이 이어받습니다."

Paraphrased only (no owner wording):

- The owner made GPT's conversation the single request window and approved up to five roles, including conditional merges (`WEEKLY_HANDOFF_2026-11-21_a3da2627.md`).
- Product direction is the commercial app, and the Android target is the QUANTGEN commercial app, not TRADEGEN (`OWNER_COMMERCIAL_ANDROID_DIRECTION_2026-11-22.md`).
- The "B6" source set is the eight B3 sources plus EODHD Fundamentals, at $51-201 a month.
- UI direction: the original case chart shows first in the guide.
- Automatic monitoring stays cancelled.

Rules:

- `CLAUDE.md` and `AGENTS.md` on main, and `README.md`, `AGENTS.md`, `TEMPLATE.md`, `SESSION_PIPELINE.md` on handoff, are unchanged.
- The one tool change is `tools/handoff/push_handoff.py --doc FILE` (#146). Its `LANE_DOCS` table lists only the three existing sub-session documents plus UI and website. The DIDM and QuantGPT sub-sessions cannot use `--doc` until that table is extended.
- `CURRENT.md` is `status: taken`, `from: gpt`, last updated 2026-11-23 12:43:31. Its `work_branch` and `pr` still point at the merged #141. The tool refuses another agent's publish over `taken` (exit 3) however old it is; `--force` needs the owner's say-so.
- `CURRENT.md` is now 42 lines without the template sections; details are in the `WEEKLY_HANDOFF_2026-11-2x_*.md` files.
- `OS_SESSION_CURRENT.md` and `PAYMENTS_SESSION_CURRENT.md` still show Claude's 11-20 state although #136 and #139 merged.

## 4. Claims I could not verify

- "Independent review" of each PR: no GitHub reviews; the evidence is in GPT's private files.
- Local test counts and screenshots (93, 172, 137, 53 Qt tests and so on) and Linux timings. I reran only the five small test modules above on main, plus one each from the three unmerged branches.
- The count split for ALFRED ("16 each on 3.12 and 3.13, 18 boundary cases").
- The signed-APK check with the real Android SDK 34, and the Flutter download 403.
- Owner approval of the five-role allocation, the B6 table and its cost and coverage numbers, and the T8-5 private draft.
- Notion updates, the website "NOT_SENT" state and AWS cost figures.
- "Five desktop model configurations matched previous results" for #141.
- "20 documents flagged" on #147: the log shows the FAIL with 20 documents in scope; I did not read the report artifact.

## 5. Conflicts with standing rules

Held:

- **Engine freeze:** `core/engine/feed.py`, `state.py`, `runtime.py`, `__init__.py` are byte-identical to the members of `_backup/QUANTGEN_pre_v2_2026-10-05.zip` and untouched on every GPT branch. The zip is still on main.
- **`qa/`:** no change on main or any GPT branch.
- **owner_confirmed:** no write. The Nautilus code fingerprint is now `bcaf33d91adb…` (recomputed here, 27 inputs) because of the planned `config.py` change, so the owner's two owner_confirmed lines must be rewritten before the next of-record run (OA-19).
- **Secrets:** a pattern scan of added lines on main and five branches found only test markers. The scan is heuristic.
- **CI:** no test removed, no timeout raised; no new tags.

Problems and risks:

1. **Lock.** GPT left `taken` instead of `returned`.
2. **Ledger.** GPT appended 11 malformed rows (a 4-column "in-progress UI" table at lines 295-305, three 5-cell rows, one invalid ID) and many in-progress rows. The tool still parses 277 IDs.
3. **Ruling C-Q12 gap (#141).** The ruling fixes seven source files for run identity (`OWNER_RULINGS_LOG.md:992`, `:1041`). The `History` return calculations now live in `core/quant/supplied_history.py`, outside that list. The recorder is not wired to the Lab yet, so the effect is latent.
4. **Policy documents edited (#136).** GPT appended an "OS-F2 implementation review" section to `docs/compliance/01-privacy-policy.md`, `07`, `20` and `FACTS.md`. Publication stays BLOCKED.
5. **`config.py` in the UI PR.** #140 adds `/uapi/domestic-stock/v1/quotations/inquire-ccnl` to `KIS_QUOTATION_ALLOWLIST` and changes `data/krx/kis_client.py`. It is a read-only endpoint, but merging will change the Nautilus fingerprint again.
6. **New vendors.** The EODHD, Alpaca and Massive parsers are outside the vendors assessed in `docs/didm/VENDOR_EVAL_2026-11.md` (EODHD appears once, "미검증"). They are offline parsers only.
7. **OA-43.** Claude commits on handoff (11-20 22:58-23:08 KST) record the AWS CPU cause as found and fixed; GPT's later documents still list cost attribution as open.

Scripts and scratch copies used are in `<메인 세션 임시 폴더>`.

## KEY FACTS
- Main is b872d8c; GPT merged 10 PRs since f065ec9: #136, #137, #138, #139, #142, #141, #143, #144, #145, #146.
- For all 10 merges the merge tree equals the tested PR head tree, and every check run on that head succeeded before the merge (8/8; 10/10 for #139).
- Roadmap IDs finished by GPT and in the ledger with matching commits: OS-F2 (72a055f), DS-H/code (6d25a33), DIDM-1 and DS-4a (53e5e72), KEY-5/a (dec979a).
- The #146 merge (b872d8c) has no ledger row; only the pre-merge row T8-6-pr-integration-c410 at 5200b6c exists.
- Handoff CURRENT.md is status: taken, from: gpt, updated 2026-11-23T12:43:31+09:00; work_branch and pr still point at the merged #141.
- push_handoff.py refuses another agent's publish over 'taken' (exit 3) regardless of age; --force needs the owner's say-so.
- The only rule or tool change is push_handoff.py --doc (#146). Its LANE_DOCS table covers OS, PAYMENTS, DATA_SOURCE, UI and WEBSITE documents only, so DIDM and QuantGPT sub-session documents are refused until it is extended.
- CLAUDE.md and AGENTS.md on main, and README.md, AGENTS.md, TEMPLATE.md, SESSION_PIPELINE.md on handoff, are unchanged since Claude stopped.
- S4 freeze holds: core/engine feed.py, state.py, runtime.py, __init__.py are byte-identical to _backup/QUANTGEN_pre_v2_2026-10-05.zip on main and untouched on every GPT branch; the zip is still on main.
- No change under qa/ on main or any GPT branch; no owner_confirmed or host_fingerprint write; no new tags.
- Nautilus code_sha256 on main is now bcaf33d91adb5c3a2b1c4a181e0827ed17fe8768827539fe7bd8ecbaea0bb34c (recomputed, 27 inputs) because of the planned config.py change in OS-F2; config.py and main.py keep CRLF.
- PR #141 is merged (666e006), not open. Open PRs are #148 (Claude skills), #147 (GH-2, draft), #140 (UI, draft) and #12 (old).
- PR #140: head 3483b53, draft, mergeable 'dirty', 66 commits, 121 files. Ubuntu 3.12 and Windows 3.11 fail the same test (tests/desktop_stock_detail_acceptance.py:1527); Windows 3.12 and 3.14 were cancelled at 120 minutes; document consistency passes.
- PR #140 contains Claude UI 414eceb, the KEY-5 K1a-d and K2a-d branches, and adds /uapi/domestic-stock/v1/quotations/inquire-ccnl to KIS_QUOTATION_ALLOWLIST in config.py.
- PR #147 (GH-2): head bf78b6b, draft, base b872d8c; 'Document and source consistency' fails; it removes only test_npu.py, five mindmap/ files and the godseye-dev launcher entry; it does not touch _backup/.
- Unmerged GPT branches with no PR: ALFRED 593c943 (2 files), Kalshi 77c37c5 (4 files), Android APK check tool c28194f (6 files). Their test modules pass locally on Python 3.13 (27, 31 and 8 tests).
- Reran on main (Python 3.13): didm_eodhd 18, didm_alpaca_news 20, didm_massive_news 18, didm_schema 26, handoff_doc 16 tests, all OK.
- PR #141 moved the History class body from core/quant/history.py to new core/quant/supplied_history.py, which is outside the seven C-Q12 source-identity files in core/quant/run_registry_recorder.py SOURCE_PATHS.
- PR #136 appended an 'OS-F2 implementation review' section to docs/compliance/01-privacy-policy.md, 07-data-minimization.md, 20-deletion.md and FACTS.md.
- The ledger parses (277 IDs), but GPT appended 11 malformed rows and many in-progress rows; no next_ids entry is already in the ledger.
- OS_SESSION_CURRENT.md and PAYMENTS_SESSION_CURRENT.md still show Claude's 2026-11-20 handoff state although OS-F2 and KEY-5/a merged.
- No merged or open GPT PR has a GitHub review object.

## OWNER ACTIONS
- [24h] Decide the handoff lock: either tell Claude it may publish over GPT's 'status: taken' CURRENT.md with --force, or have GPT publish 'returned' first. — push_handoff.py refuses Claude's publish (exit 3) while CURRENT.md is taken by gpt; CLAUDE.md allows --force only with the owner's say-so. Until then Claude cannot publish checkpoints or ledger rows. (src: handoff CURRENT.md front matter; tools/handoff/push_handoff.py line 341; CLAUDE.md handoff protocol)
- [24h] Say which session continues UI PR #140 (UI session, or Claude main and sub-sessions), and whether its KEY-5 wiring and config.py allowlist change stay in that PR. — #140 is failing CI and conflicts with main; KEY-5 K3 (PAYMENTS) and OS-F1 (OS) both wait on it, and the UI session is reached only through the owner. (src: PR #140 check runs and diff; WEEKLY_HANDOFF_2026-11-22_6e1ca7eb.md; CLAUDE.md session pipeline)
- [24h] Run the home-indicator diagnostic command (OA-09) and paste the output. — GPT merged only the DS-H code; the DS-H parent stays open until the real diagnostic is read. WORKBOARD flagged it 'now' on 11-20; I did not check whether it has been done since. (src: WORKBOARD.md OA-09; WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md)
- [24h] Answer the three remaining DIDM questions (OA-10): majority-class baseline as a pass condition; base model and last training date for the own LLM; role split in the vendor table. — The new DIDM sub-session needs them before model cutoff and evaluation work. WORKBOARD flagged it within 24h on 11-20; current state not checked. (src: WORKBOARD.md OA-10; WEEKLY_HANDOFF_2026-11-22_6e1ca7eb.md)
- [later] Confirm the 'B6' vendor set GPT used (eight B3 sources plus EODHD Fundamentals; Alpaca and Massive news; Atlanta Fed MPT) and give the source table. — GPT built parsers for vendors outside those assessed in VENDOR_EVAL_2026-11.md from a table that is not in the repository; collectors and paid plans should not follow without confirmation. (src: WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md; OWNER_COMMERCIAL_ANDROID_DIRECTION_2026-11-22.md; docs/didm/VENDOR_EVAL_2026-11.md)
- [later] After PR #140 is green, run the preview on the Windows PC (PC7 check: startup, stock detail, guide chart, tooltips, order book, window flicker). — GPT kept #140 in draft for this check; UI merge, KEY-5 K3 and OS-F1 follow it. Not useful before the failing test is fixed. (src: PR #140 body; handoff CURRENT.md)
- [later] Run GitHub Actions 'Platform build' on main with only Android enabled, install the APK on a phone and check the first screen and the example calculation (101.01 / 104.69 / 108.95). — The Android preview code is on main (#141) but no APK was built or tested; GPT could not dispatch the workflow. (src: WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md; PR #141 body)
- [later] Rewrite the two owner_confirmed lines before the next Nautilus of-record run (OA-19). — code_sha256 is now bcaf33d9… after OS-F2 changed config.py; it will change again if PR #140 merges with its config.py edit. (src: recomputed fingerprint on main b872d8c; MERGE_QUEUE.md lines 352-353)
- [later] Decide on ruling C-Q12: add core/quant/supplied_history.py to the seven source-identity files, or move the History code back into core/quant/history.py. — PR #141 moved the History return calculations outside the registered list, so later edits there would not count as a new trial. (src: git diff d835d9f..666e006; docs/nautilus_bridge/OWNER_RULINGS_LOG.md lines 992 and 1041; core/quant/run_registry_recorder.py SOURCE_PATHS)
- [later] Payments and AWS decisions GPT left open: send the seven inquiries (OA-32), PAY-2 decisions P2-01..15 (OA-39), server location (OA-40), and the same-period Usage type by Region cost table (OA-43). — GPT did no new payment work and says these block PAY-0, PAY-2, PAY-3 and the cost attribution. (src: WEEKLY_HANDOFF_2026-11-23_bf4cc1f1.md; WORKBOARD.md)
- [later] Decide whether GH-2 adds a secret-scan CI step (OA-17) and when to create the archive-2026-11 tag so that _backup/ can be removed. — PR #147 covers only the file removals; _backup/ removal waits for the tag, and _backup holds the zip used for the engine freeze check. (src: docs/nautilus_bridge/REMAINING_WORK_2026-11-17.md line 43; WORKBOARD.md line 360)

## OPEN QUESTIONS
- Did the owner actually approve GPT's five-role allocation with conditional merges on 2026-11-21? The approval document still says pending and later documents only paraphrase.
- Is GPT's session still working? The 'taken' lock is about 29 hours old, with no handoff or main commit after 2026-11-23 12:43 KST.
- Should the KEY-5 UI wiring (K1a-d, K2a-d) stay inside UI PR #140 or be split out for the PAYMENTS sub-session?
- Is the KIS allowlist addition (inquire-ccnl) in PR #140 covered by an owner ruling?
- Was the edit of the privacy policy and other compliance documents in #136 acceptable without owner review?
- What is the 'B6' source table? It is not in the repository or the handoff plans, and 'B3'/'B6' in the owner's QuantGPT spec mean benchmark and option labels.
- Is OA-43 closed? Claude commits on 11-20 record the cause as found and fixed, but GPT still lists cost attribution as open.
- How should DATA_SOURCE_SESSION_CURRENT.md and the 'data-source-didm' task name in LANE_DOCS be split when DIDM becomes its own sub-session?
- Should GPT's malformed and in-progress ledger rows stay as they are (the ledger is append-only), and who adds the missing rows for #146 and GH-2?
- Does the new QuantGPT sub-session need the mindmap/ macro documents that GH-2 PR #147 deletes from main?

## UNVERIFIED
- GPT's 'independent review' of each PR (no GitHub review objects; evidence only in GPT's private files).
- GPT's local test counts, screenshots and Linux timings beyond the eight modules rerun here (five on main, three on unmerged branches).
- The ALFRED count split ('16 each on Python 3.12 and 3.13, 18 boundary cases'); the module has 27 tests, which pass on 3.13.
- The Kalshi count split ('27 selected, 143 price and 129 count/page independent cases'); the module has 31 tests, which pass on 3.13.
- The signed-APK verification with the real Android SDK 34 and the Flutter download 403 in GPT's cloud.
- Owner approval of the five-role allocation and conditional merges on 2026-11-21 (paraphrased, not quoted).
- The owner's commercial-app and Android direction of 2026-11-22 (recorded without the owner's words).
- The B6 source table and its cost ($51-201 a month) and coverage (83/100) figures.
- The T8-5 private draft on brokerage screen guidance and KIS or legal questions.
- Notion updates GPT says it made or queued; website PR-140 and PR-141 records being 'NOT_SENT'.
- AWS cost figures and the OA-43 state.
- 'Five existing desktop model configurations matched their previous results' for PR #141.
- That exactly 20 documents were flagged on PR #147 (the log shows consistency FAIL with 20 documents in scope; the report artifact was not read).
- Current state of owner items OA-03..OA-06, OA-09 and OA-10 (taken from WORKBOARD as of 2026-11-20).
- That no secret exists anywhere in GPT's changes (pattern scan of added lines only).
- That GPT never ran tests/run_all.py or the macro lab modules (no qa/ change is the only evidence).
- The Windows 3.12 and 3.14 failure cause on PR #140 (jobs were cancelled at the time limit; logs not read).
