# Round 2 referee report: governance and compliance (Claude)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 2. It is an uncommitted working copy
over `a14954f`, 1,500 lines, and I read all of it. I also read my round-1 report and `round1_rulings.md`.

Repo: QUANTGEN on branch `claude/amazing-gauss-tdiguu`. Code cites are at `6f7c610`; `a14954f` adds only review
documents. `nt:<path>:<line>` is `nautilus_trader` 1.231.0 in `scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
`scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
`spec:<line>` is Revision 2.

Probes, in `scratch:referee2_governance/`:
- `pin_check.py` recomputes the two T-RO-01 pin digests from the spec's constants (`consts.py` is copied out of
  spec:661-703).
- `guard_probe.py` builds a `BacktestEngine` under `unshare -rn` and reports the clock class a strategy receives.
- `rev1.md` is Revision 1, saved for comparison.

No probe read a price file.

## Verdict

**ACCEPT_WITH_CHANGES.**

Twelve of my 13 round-1 issues are resolved. GOVERNANCE-5 is still partly open. The revision adds three new major
issues and three minor ones. There is no blocker, and every fix is a change to the text.

Why I do not AGREE: a team starting today would still have three questions.
- May Steps 2 to 7 start before the owner rules? The Status block and Step 1 say no. The Owner context and the
  GOVERNANCE-1 ruling say yes (GOVERNANCE-R2-1).
- The owner's sign-off sentence and `owner_confirmed` are not tied to the code or table bytes they approve. The
  sign-off also comes before the Windows evidence it should rest on (GOVERNANCE-R2-2).
- 3.9 says map 03's real pre-2004 SPY probe is "never repeated". The runner still accepts a rehearsal on exactly that
  data, and a test checks that path (GOVERNANCE-R2-3).

## Sections reviewed

- Status, Inputs, citation keys and Owner context (spec:1-47).
- §1 scope and the TRADEGEN boundary (spec:49-71).
- §2 owner rulings O1 to O15 (spec:73-94).
- §3.1 to §3.12, all binding constraints (spec:96-207).
- §4.1 to §4.4 architecture, launch contract and egress layer (spec:209-286).
- §5.1 requirements header; §5.2.1, §5.2.2, §5.2.5 and §5.2.8 (spec:290-464).
- §5.3.1 modes and seams, §5.3.2 order of operations and §5.3.5 lifecycle (spec:468-555).
- §5.5 gate hand-off, §5.6 T-RO-01 amendment, §5.7 suite and §5.8 file table (spec:628-786).
- §6.3 run record, §6.4 ledger rows, §6.5 card and §6.6 registration table (spec:828-908).
- §7 error handling R-01 to R-16 and G-01 to G-07 (spec:951-997).
- §8.3 layer-1 tests 6, 9, 19, 22 to 24 and 32; §8.5 scan controls; §8.6 container rule (spec:1068-1172).
- §9 Steps 1 to 10 and the Step 7A hand-off (spec:1174-1228).
- §10.1 to §10.4 pilots, expected verdicts and data-access history (spec:1230-1312).
- §11 risks 1, 5, 13, 14, 19 to 22; §12; §13; Appendices A and B (spec:1314-1500).
- House sources checked:
  - `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md` lines 25-27, 46, 84-91, 142-144,
    177-181 and 442-452;
  - council item 21 and rule 01 (`QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:464,
    500, 1257, 1261, 6162`);
  - `research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`;
  - `core/quant/gate_ledger.py:122-131, 244-262, 284-310, 337-396`;
  - `config.py:25-39, 176-178`;
  - `ui/strategy_lab_page.py:117`;
  - `tests/macro_m0_harness.py:28-100`; `tests/macro_acceptance.py:277-295`; `tests/run_all.py:35-38, 57-71, 128-140`;
  - `tests/frozen_guard.py:3-15, 80-95`; `grokteam/prereg.py:31-36`;
  - `paper_live/replay.py:172` and `paper_live/engine.py:63-112`, read only;
  - `docs/asset_expansion_study.py:41-58, 844`;
  - `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:30`;
  - `README.md:850-855, 924-929`;
  - `git log`, `git branch -a` and `git merge-base`.

## Round-1 issues

- **GOVERNANCE-1: resolved.** The authority statement is narrowed to two decisions (spec:37). The merge, any
  of-record run and the T-RO-01 exemption wait for a verbatim sign-off sentence (spec:40-44). The quotes are marked
  UNVERIFIED and their channel is named (spec:33-35). A new contradiction about gating is GOVERNANCE-R2-1.
- **GOVERNANCE-2: resolved.** O3 quotes both halves of item 21 and rule 01. It states the live-portability fact and
  the venv's contents (spec:82). C-2's guard sits in `on_start` (spec:386-396). My probe confirms that a strategy in a
  `BacktestEngine` holds a `TestClock`. The kernel picks `LiveClock` for SANDBOX and LIVE (`nt:system/kernel.py:163-166`).
  A raise in `on_start` leaves the strategy STARTING (`nt:common/component.pyx:1941-1965`).
- **GOVERNANCE-3: resolved.** Of-record mode now refuses a missing, empty or broken family ledger. It also refuses a
  host fingerprint that is off or a missing egress record (R-14, R-15; spec:498, 971-972). A container or a copied
  ledger cannot pass. How those refusals are tested is GOVERNANCE-R2-4.
- **GOVERNANCE-4: resolved.** Refusal is by content. The md5 values are pinned, and a table now has an `end` field.
  Dates are filtered before any value is parsed (spec:182-185, 502, 899). md5 equality is defeated by any changed
  byte, so Step 2's procedure rule is still the main guard. See Notes.
- **GOVERNANCE-5: open, in part.** O6 fixes the start at 2004-12-01 (spec:85). Step 7 is synthetic only (spec:1187),
  and 10.4 drops the rehearsal row. But the runner still accepts a rehearsal on real SPY up to 2004-11-30 (spec:476,
  183-184, 1080). So "never repeated" rests on procedure alone. See GOVERNANCE-R2-3.
- **GOVERNANCE-6: resolved.** Both engines are always scored. A card is written only when the decisions and the
  gate flag sets agree; otherwise the run is WITHHELD with "decision mismatch" (spec:638, 990).
- **GOVERNANCE-7: resolved.** L1-22 fails while the global interpreter can import `nautilus_trader` (spec:1093). R-03
  refuses a parent that has the distribution, and it refuses `include-system-site-packages = true` (spec:500, 917).
  `pyarrow` is reported only, as the ruling says.
- **GOVERNANCE-8: resolved.** O14 covers the pilot-2 table and O15 covers FAIL against NotRun (spec:93-94). The
  ruling silently dropped my third item, data licence. See Notes.
- **GOVERNANCE-9: resolved.** 3.8 and R-16 refuse while `C3.jsonl` or the family ledger is fresh (spec:170-173, 973).
  I checked the residual risk. paper_live registers once at start (`paper_live/replay.py:172`) and never calls
  `assert_hash_at_run`. A duplicate configuration appends nothing (`core/quant/gate_ledger.py:343-346`). So an overlap
  that R-16 misses cannot break the frozen readout.
- **GOVERNANCE-10: resolved.** 5.6 and O2 say this is T-RO-01's first exemption for a forbidden token or call, and
  what a PASS now means (spec:653-656). The README sentence I proposed was not added. See Notes.
- **GOVERNANCE-11: resolved.** The merge is the owner's act after the sign-off. The commands are written out, and the
  anchor commit is named in the done-when (spec:1193-1222). The git details that remain are in GOVERNANCE-R2-5.
- **GOVERNANCE-12: resolved.** The folder path is correct (spec:1181). Appendix B says round 1 ran in the repo
  clone (spec:1392-1394). The Status block counts the five personas as one referee under D6 (spec:7-8).
- **GOVERNANCE-13: resolved.** Step 2 copies all of section 3 verbatim and adds the four Claude-only rules
  (spec:1182). The cite `2026-10-23-quantgen-paper-pipeline.md:30` is correct.

## New issues

### GOVERNANCE-R2-1: the spec gives two answers to "may Steps 2 to 7 start before the owner rules?"

- **Severity:** major.
- **Section:** Status "Next" (spec:15); Owner context (spec:37-40, 46-47); §2 preamble (spec:75-76); O1 and O8 cost
  columns (spec:80, 87); §9 Step 1 done-when (spec:1181).
- **Problem:**
  - The GOVERNANCE-1 ruling lets branch work go ahead on the defaults, because it is reversible.
  - The Owner context applies that ruling: "Claude continues without stopping", and "Claude builds on
    `claude/amazing-gauss-tdiguu`" (spec:37-40). §2 says "this revision builds on it until the owner rules"
    (spec:75-76). O1's cost column assumes branch files already exist when O1 is refused (spec:80). Line 46 lists
    only the pilots as waiting.
  - The Status block and Step 1 say the opposite:
    - "Next: GPT and Gemini round 1 on Revision 2; the owner's rulings and approval; then Step 2" (spec:15);
    - Step 1 is done only when "the Status block carries the owner's approval line and answers to O1 to O15"
      (spec:1181);
    - O8's default is to wait, and it costs "Step 1 ends about four days later" (spec:87), which is about 2026-10-30.
  - Under the first reading, Step 2 starts today. Under the second, nothing starts until GPT, Gemini and the owner's
    answers are in. A team cannot tell which, and the question decides whether `pyarrow` and the adapters reach the
    branch before O1 and O3 are ruled.
- **Evidence:** spec:15, 37-40, 46-47, 75-76, 80, 87, 1181; `round1_rulings.md`, GOVERNANCE-1.
- **Proposed fix:**
  - Write one rule in the Status block and in Step 1. To match the ruling, split Step 1:
    - **1a.** The Claude rounds are ruled and applied. Steps 2 to 7 may then start on the branch, on the section 2
      defaults, with synthetic data and temp ledgers.
    - **1b.** GPT and Gemini have run (or a substitute is recorded), and the owner has approved and answered O1 to
      O15. 1b is required before Step 7A, not before Step 2.
  - Change spec:15 to: "Next: Step 2 on the branch; in parallel, GPT and Gemini on Revision 2 and the owner's
    rulings."
  - Add one sentence: when a ruling differs from its default, the affected branch work is redone or deleted before
    Step 7A. O1's cost column already says this for O1.
  - If the owner wants the stricter reading instead, delete "Claude continues without stopping" and the "builds on"
    wording.

### GOVERNANCE-R2-2: the owner's approvals are not bound to the code or tables they approve, and the sign-off comes before the Windows evidence

- **Severity:** major.
- **Section:** Owner context (spec:40-44); Step 7A items 1 to 4 and done-when (spec:1189-1222); §6.6 `owner_confirmed`
  (spec:907); §5.3.2 step 1 and R-11 (spec:498, 968).
- **Problem:**
  - The sign-off sentence is the only owner act that releases the merge, the T-RO-01 exemption and of-record runs
    (spec:40-44). It is written at 7A.1 (spec:1190).
  - That is before the evidence it should rest on: the Windows run of F1, F2 and N1 in standard precision, the egress
    record (7A.2), and Claude's census review (7A.4, spec:1215).
  - When 7A.2 fails, "the hand-off stops and no pilot runs" (spec:1219-1220). Nothing says the recorded sentence then
    lapses. If code is fixed after that failure, the fixed code still sits under an approval given for earlier code.
  - The sentence names the spec revision and the table files by path. It names no commit and no table content. Code
    can change while the spec revision stays the same.
  - `owner_confirmed` is `"<name>, <date>"` (spec:907). The runner checks only that it is there (spec:498, 968). It
    is not tied to the table's bytes.
    - Step 1 checks the grid against the axes, and checks the pilot values. It does not check the axes, symbol,
      dates, cost or family against anything the owner saw.
    - A later commit could change a key field and keep the old `owner_confirmed`.
    - Ledger rows are permanent (`core/quant/gate_ledger.py:337-355`), and O6 says a wrong key field leaves permanent
      extra trials (spec:85).
- **Evidence:** spec:40-44, 85, 498, 907, 968, 1190, 1212-1222; `core/quant/gate_ledger.py:337-355`.
- **Proposed fix:**
  - Take "and of-record runs of <table files>" out of the 7A.1 sentence. The owner approves of-record runs through
    `owner_confirmed`, which is written at 7A.3, after the Windows evidence exists.
  - Have `--fingerprint` also print two digests:
    - `table_sha256`: the canonical JSON of the table without `owner_confirmed` and `host_fingerprint`;
    - `code_sha256`: the SHA-256 over the sorted `path,sha256` lines of `tools/nautilus/**/*.py`,
      `tools/nautilus/golden/*.json` and `requirements-nautilus.txt`.
  - `owner_confirmed` becomes `"<name>, <date>, table <16 hex>, code <16 hex>"`. R-11 recomputes both digests in
    of-record mode and refuses on any mismatch. Add two L1-19 cases: a key field edited after confirmation, and a
    sandbox byte changed after confirmation; each must refuse.
  - State that when 7A fails, the 7A.1 sentence does not cover any code changed afterwards, and a new sentence is
    needed.

### GOVERNANCE-R2-3: the runner still accepts a rehearsal on real pre-2004 SPY, which 3.9 says is never repeated

- **Severity:** major.
- **Section:** §3.9 (spec:179-185); §5.3.1 modes table (spec:476); §8.3 L1-9 (spec:1080); §10.4 (spec:1299-1308).
- **Problem:**
  - 3.9 says every rehearsal Claude runs uses synthetic data only. It says map 03's pre-2004 SPY probe is "recorded
    in 10.4, never repeated" (spec:180-181). The GOVERNANCE-5 ruling says the same.
  - The runner still accepts that run:
    - the rehearsal row allows "synthetic, or SPY with `end` at most 2004-11-30" (spec:476);
    - the SPY md5 refusal applies only "when the table's `end` is after 2004-11-30" (spec:183-184);
    - L1-9 tests only `end` 2004-12-01 (spec:1080), so a rehearsal on real SPY ending 2004-11-30 is a designed and
      tested path.
  - A rehearsal runs every step through 5.5: registration into a temp ledger, both engines, both walk-forwards and
    two `score_strategy` calls (spec:514-515). On real SPY from 1995 to 2004, that is a scored gate run on real data
    outside the ledger of record.
  - The house rule is "a run that computes is a trial; registered before it is scored" (`ui/strategy_lab_page.py:117`).
    The run would also add a 10.4 row that the spec says will never exist. So the spec still decides on the owner's
    behalf that such a run is not a trial, which was the original GOVERNANCE-5 problem.
  - No step needs this path: Step 7 is synthetic, Step 7A runs only fixtures, and N6 is synthetic (spec:1061, 1187,
    1207).
  - This allowance was already in Revision 1 (rev 1, line 458). Revision 2's new "never repeated" sentence now
    contradicts it.
- **Evidence:** spec:180-185, 476, 514-515, 1080, 1187, 1305; `ui/strategy_lab_page.py:117`;
  `scratch:referee2_governance/rev1.md:458`.
- **Proposed fix:**
  - In rehearsal mode, refuse any prices file whose md5 equals the pinned SPY md5, whatever its `end`, as for BTC.
  - Change the 5.3.1 Data cell to "synthetic only; the content refusals of 3.9".
  - Change L1-9 to plant the SPY md5 with `end` 2004-11-30, and expect R-10.
  - If the owner ever wants a real-data rehearsal, it is a new numbered ruling with its own 10.4 row.

### GOVERNANCE-R2-4: as specified, the of-record refusals R-01 and R-14 cannot be tested, and "Claude never runs --of-record" does not say whether tests count

- **Severity:** minor.
- **Section:** §5.3.1 test seams (spec:485-491); §5.3.2 rehearsal note (spec:514-515); §7 R-01 and R-14 (spec:958,
  971); §8.3 L1-6 and L1-23 (spec:1077, 1094); Step 2 Global Constraints (spec:1182).
- **Problem:**
  - Of-record mode refuses the seams `anchor_fn`, `repo_root`, `probe_cmd` and `hooks` (spec:490; R-11).
  - **R-01.** The dirty-tree refusal exists only in of-record mode, because rehearsal allows a dirty tree
    (spec:514). L1-6 tests R-01 "through `anchor_fn` and `repo_root`" (spec:1077).
    - In of-record mode, that call stops at R-11.
    - In rehearsal mode, R-01 cannot fire.
    - So R-01 has no reachable negative control.
  - **R-14.** The record match is checked only in of-record mode.
    - To reach step 4 in of-record mode, step 3 must pass, and step 3 needs the venv.
    - Layer 1 has no venv, and `hooks` and `probe_cmd` are refused in of-record mode.
    - So L1-23's second case cannot run in layer 1 (spec:1094).
  - These refusals are what make the GOVERNANCE-3 fix trustworthy. The QA-8 ruling requires a negative control, or
    a written reason, for every fail-closed condition.
  - Step 2 adds "Claude never runs `--of-record`" (spec:1182). Yet L1-19, L1-24 and the cases above call the runner
    in of-record mode. The spec does not say whether a test call of `run(mode="of-record")` counts.
- **Evidence:** spec:476-477, 485-491, 514-515, 958, 968, 971, 1077, 1090, 1094, 1095, 1182.
- **Proposed fix:**
  - Move the of-record checks into pure functions: `check_tree(repo_root, run_git)` for R-01 and R-02, and
    `check_egress_record(record, current)` for R-14.
  - In of-record mode the runner calls them with fixed arguments. L1-6 and L1-23 test the functions directly.
  - Reword the constraint: "Claude never runs the CLI with `--of-record`. A test may call `run(mode="of-record")` only
    with `QUANTGEN_MACRO_DIR` on a temp dir, and the 3.3 guard fails the test otherwise."

### GOVERNANCE-R2-5: the hand-off names the wrong merge target, allows squash merges that orphan anchors, and leaves the anchor commit unnamed

- **Severity:** minor.
- **Section:** Step 7A items 2 to 4 and done-when (spec:1193-1222); Step 8 (spec:1226).
- **Problem:**
  - **Merge target.** 7A.2 says "merging it into master" (spec:1193-1194).
    - The remote's default branch is `main`, and `origin/main` shares no commit with the feature branch:
      `git merge-base main HEAD` prints nothing.
    - `main` is a history of web uploads and deletions, from `9333894 Add files via upload` to
      `d330054 Delete montecarlo.py`.
    - That the owner has a local `master` is UNVERIFIED; `ac86705`'s message names it.
  - **Squash or rebase merges.** Ledger rows anchor to `git:<sha>` (`core/quant/gate_ledger.py:122-131`).
    - After a squash or rebase merge, only the branch ref reaches the anchored commit.
    - If that ref is deleted, the pilot rows point to no code. That is K2's risk again.
  - **Anchor commit.** In 7A.4, Claude records its census review in Appendix B, a new commit after the owner's 7A.3
    commit.
    - The spec does not say whether the owner pulls that commit before Step 8.
    - The done-when says "`git:<the new commit>`" without saying which commit (spec:1222).
    - If the owner does not pull it, his Step 8 push of the run folder is rejected as a non-fast-forward.
- **Evidence:** spec:1193-1199, 1212-1222, 1226; `git branch -a`; `git merge-base main HEAD` (empty); `git log
  --oneline main`; `core/quant/gate_ledger.py:122-131`.
- **Proposed fix:**
  - Name the target: "the owner's local `master`; never `origin/main`, which has an unrelated history."
  - Add: "Merge with a merge commit, not a squash or a rebase, and keep the branch ref, so every anchor stays
    reachable."
  - Add 7A.5: "The owner pulls Claude's review commit, fast-forward only, before Step 8. The pilots anchor to that
    HEAD, and the run record stores it."

### GOVERNANCE-R2-6: four citation slips

- **Severity:** minor.
- **Section:** §1 (spec:68); §3.7 (spec:158); §5.2.5 (spec:400-401); §5.6 and Appendix B (spec:684, 711, 1490).
- **Problem:**
  - `data/fmp/quote_client.py:64-65` is cited three times for `api_key`. Lines 64-65 are dataclass fields. `api_key`
    is at `:110` and `:115`.
  - 5.2.5 says "The actor catches and logs every `on_bar` exception (`nt:common/actor.pyx:4586-4590`)". The code logs
    the exception and then re-raises it (`nt:common/actor.pyx:4591`). The design choice, never relying on a raise,
    is still right. The stated reason is wrong: a raise would propagate, not be swallowed.
  - §1's "(same spec, :142)" follows a cite to map 04 §6, so it reads as map 04. It means the 2026-10-23 split spec.
    Line 142 there is correct.
  - `tests/run_all.py:33-37` should be `:35-38`.
- **Evidence:** `data/fmp/quote_client.py:110, 115`; `nt:common/actor.pyx:4586-4591`;
  `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:142`; `tests/run_all.py:35-38`.
- **Proposed fix:** Correct the four cites. In 5.2.5, write: "the actor logs and re-raises an `on_bar` exception,
  which would stop the run; so a failed check appends its reason and returns."

## Notes

**Checked and correct:**
- **Pin digests.** Both T-RO-01 pin digests recompute exactly from the constants printed at spec:661-703:
  `2792ad4a...` and `70bcf50f...` (`scratch:referee2_governance/pin_check.py`).
- **Item 21 and rule 01.** They are at council:6162, and at 464, 500 and 1257. Council:1261 holds "No backtest
  alone could enable it". The `pyarrow` ban is at `00_coordinator_rulings.md:54-55`.
- **Order verbs.** The verbs and `on_order_filled` sit at the cited `nt:trading/strategy.pyx` lines (723, 805, 899,
  1011, 1089, 1134, 1215, 1351, 1418, 1750).
- **Licence.** The wheel's METADATA reads `License: LGPL-3.0-or-later`.
  - The repository holds no Nautilus code: only names, hashes and module-name lists.
  - The README says "Do not distribute it as a product" (`README.md:929`).
  - So Risk 20's LGPL note is accurate.
- **Frozen studies.** The bridge edits no file in `grokteam/prereg.py:31-36` or `paper_live/`. frozen_guard (a) and
  (b) read the tagged tree, so main-line edits cannot trip them (`tests/frozen_guard.py:7-11`).
- **Study import.** Importing `docs/asset_expansion_study.py` for P0a only runs `mkdir(exist_ok=True)` on existing
  folders and reconfigures stdout (`:41-58`). `REFRESH = False` is at `:844`.
- **Registry resync.** `python -m tests.macro_acceptance` writes only `tests/macro_registry.csv`, with LF endings
  (`tests/macro_acceptance.py:277-295`). It does not touch `qa/acceptance_results.json`.
- **The `git switch` in 7A.2.** The split spec forbids a whole-tree `checkout`, `reset`, `stash` or `clean` because
  they rewrite cache mtimes (split-spec:89-91). A branch switch rewrites only the files that differ. The branch does
  not change `docs/asset_expansion/cache/`, so the runbook is consistent with that rule.
- **Ledger facts behind R-15.** `host_fingerprint` uses `row_md5`, which every row carries. A missing ledger verifies
  as an empty chain (`core/quant/gate_ledger.py:276-277, 284-310`), so R-15's "missing or empty" refusal is needed
  and correct.

**Minor concerns (no issue raised):**
- **Data licence.** Round 1 asked for a data-licence record (GOVERNANCE-8, third part). The ruling dropped it
  without a word. The cards record "Yahoo" as the source, but no licence is recorded anywhere. Risk 20's "publication
  needs an owner review" covers it only loosely. One line in O15 or §12 would close it.
- **README.** Revision 2 does not add the README P0 sentence on the T-RO-01 exemption that GOVERNANCE-10 proposed.
  `README.md:374` still says the static scans "hold the line" with no exemption named.
- **"TRADEGEN's domain".** §1 calls `TradingNode`, adapters and API keys "TRADEGEN's domain" (spec:66-67). That reads
  as QUANTGEN endorsing TRADEGEN's use of them, Polymarket and Betfair adapters included. Those venues are rated
  illegal for a Korean resident (`reports/Korean resident trading venue legality.md:15, 21`). "Outside QUANTGEN's
  scope" alone would be safer.
- **Rehearsal md5 refusal.** It catches only byte-identical copies. A copy of a pilot file with one byte changed
  passes. Step 2's rule "Claude reads no real BTC price and no SPY row on or after 2004-12-01" stays the main guard.
- **Procedure-only rules.** Two rules rest on procedure alone: pilot 2's precondition (pilot 1 passed parity,
  spec:1272) and "no pilot before Claude's census review" (spec:1215-1216). Both are owner-run steps, so that is
  acceptable.
- **Installed set.** The venv's full installed set is recorded but not compared with the 16 pinned distributions
  (spec:919-920). With `--require-hashes`, offline installs and the firewall, that risk is small.

**UNVERIFIED in this review:**
- the owner's two quoted sentences;
- the owner's local branch name and tip;
- whether `E1.jsonl` exists on the owner's machine (open question 2);
- the licence of the Yahoo and FRED caches;
- whether the GitHub remote is private;
- every Windows fact that Step 7A is meant to answer.

**House rules kept during this review:**
- no file under `paper_live/` or `grokteam/` was edited or run;
- no `pip install`;
- no `tests/run_all.py`;
- no price file was read;
- no ledger row was written;
- no commit;
- the only tracked-tree write is this report.
