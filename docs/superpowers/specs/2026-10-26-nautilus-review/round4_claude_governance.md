# Round 4 referee report: governance and compliance (Claude)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 4. It is an uncommitted working copy
over `4f5f18b`, 1,772 lines, and I read all of it. I also re-read my round-1 to round-3 reports and the three rulings
files.

Citation keys:
- `file:line` is QUANTGEN at HEAD `4f5f18b`. `git diff --stat 6f7c610 4f5f18b` changes only files under
  `docs/superpowers/specs/`, so code lines are as in round 3.
- `spec:<line>` is Revision 4.
- `nt:<path>:<line>` is `nautilus_trader` 1.231.0 in `scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
- `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probe, in `scratch:referee4_governance/`: `code_digest_r4_probe.py`, with its output in `code_digest_r4_probe.out`.
- It imports `core.quant.gate_package` with `HOME` and `QUANTGEN_MACRO_DIR` set to temp dirs.
- It computes 6.6's Revision-4 `code_sha256` on a temp copy of the hashed files, changes one byte of the copy's
  `core/quant/validate.py`, and computes it again.
- It reads no price file and writes no ledger row. It writes nothing in the repository.

## Verdict

**AGREE**, with five minor issues.

All seven of my round-3 issues are resolved as ruled. Every round-1 and round-2 issue stays resolved.

Revision 4 brings no blocker and no major issue from my lens. The five new items are all minor:
- GOVERNANCE-R4-1: `--fingerprint` is the tool of the approval chain, and its behaviour is unspecified. Nothing says
  what it does without a family ledger or how it validates a table without owner fields, and no test covers it.
- GOVERNANCE-R4-2: after 7A.3, the scope of Claude's review commit and of Step 10's diff is open. The sign-off rule
  covers code changes only "after a failed Step 7A".
- GOVERNANCE-R4-3: the new Step 2 rule on owner fields has no scope, so it also forbids the test tables.
- GOVERNANCE-R4-4: pilot 2's precondition is procedural only. This gap predates Revision 4.
- GOVERNANCE-R4-5: the bookkeeping for round 4. 10.4 must record the quant referee's re-score on real KRX caches.

## Sections reviewed

- Status, Inputs, citation keys and Owner context (spec:1-60).
- §1 scope (spec:62-84) and §2 owner rulings O1 to O15 (spec:86-107).
- §3.1 to §3.12, all binding constraints (spec:109-225). In particular:
  - the new temp `QUANTGEN_MACRO_DIR` in 3.3 (spec:138-143);
  - the rehearsal place rule in 3.9 (spec:198-203).
- §4.1 to §4.4 (spec:227-303). This includes the parent's new import of `core.quant.gate_package` (spec:231-235).
- §5.1 and §5.2.1 to §5.2.9, the skeleton included (spec:305-645).
- §5.3.1 to §5.3.5 (spec:647-778):
  - the modes table and the `--fingerprint` mode;
  - the seams and the pure steps;
  - the order of operations;
  - the lifecycle, including R-17 keyed by `table_sha256` and `SetThreadExecutionState`.
- §5.4 to §5.8 (spec:780-1010).
- §6.1 to §6.8 (spec:1012-1167). In particular, 6.6's extended `code_sha256` (spec:1112-1120).
- §7, every row, R-01 to G-08 (spec:1169-1219).
- §8.1 to §8.6 (spec:1221-1416). In particular:
  - L1-9 (spec:1340);
  - L1-10 (spec:1341);
  - L1-19 (spec:1350);
  - L1-29 (spec:1360);
  - L2-12 (spec:1378).
- §9 Steps 1a to 10, every Step 7A item, the merge paragraph and the done-when (spec:1418-1506).
- §10.1 to §10.4 (spec:1508-1581), §11 (spec:1583-1598), §12, §13, and Appendices A and B (spec:1600-1772).
- House sources checked:
  - `core/quant/gate_package.py:17-38`, its import block and `HARNESS_SOURCES`;
  - `config.py:25-39, 176-178`, which is CRLF;
  - `ui/strategy_lab_page.py:55-77`;
  - `tests/macro_acceptance.py:20-30, 50-151, 200-201`;
  - `core/quant/gate_ledger.py:49, 168-171, 927-933`;
  - `core/ficc/macro_schema.py:300-305`;
  - `docs/asset_expansion_study.py:36-106, 173-175, 843-845` (code only);
  - `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:28-31`;
  - `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:25-27, 46, 85-91, 142-144, 177-181,
    442-452`;
  - `.gitattributes`, `.gitignore`;
  - the md5 of `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json` and the count of 34 cards.
- Nautilus sources:
  - `nt:system/kernel.py:160-171`;
  - `nt:trading/trader.py:420-423`;
  - `nt:common/actor.pyx:4584-4592`.
- Git checks:
  - `git ls-remote origin main` gives `716bf77`;
  - `git merge-base --is-ancestor origin/main HEAD` succeeds;
  - `git diff --stat 6f7c610 4f5f18b -- . ':!docs/superpowers/specs'` is empty;
  - `git check-ignore` on `tools/nautilus/__pycache__/`.
- The other round-4 reports:
  - `round4_claude_ops.md`, `round4_claude_quant.md` and `round4_claude_security.md`, verdicts and issue headings;
  - `round4_claude_qa.md`, QA-R4-1 to QA-R4-3 in full.

## Earlier issues

Round 3:
- GOVERNANCE-R3-1: **resolved**.
  - `code_sha256` now covers:
    - `core.quant.gate_package.HARNESS_SOURCES`, imported (spec:1116-1118; `core/quant/gate_package.py:36-38`);
    - `docs/asset_expansion_study.py`;
    - `config.py`.
  - The parent's import list names `gate_package` (spec:231-235). L1-19 gains the `validate.py` case (spec:1350).
  - Step 10 diffs against "the 7A.5 HEAD that the pilot run records store" (spec:1506). 6.3's `git.head` holds that
    HEAD (spec:1055).
  - Probe results:
    - Importing `gate_package` writes nothing under `HOME` or `QUANTGEN_MACRO_DIR`.
    - All 11 harness sources exist. Today's set is 13 files, because no `tools/nautilus` file exists yet.
    - One changed byte in the copy's `validate.py` changes the digest (`bbf9878a...` to `39090079...`).
    - The temp copy gives the same digest as the repository.
  - The residual window is GOVERNANCE-R4-2.
- GOVERNANCE-R3-2: **resolved**.
  - L1-10 passes `ledger_dir` explicitly and uses SPY `sma/127/21` and BTC-USD hysteresis 0.333. Neither is a pilot
    configuration (spec:1341).
  - The 3.3 guard sets a fresh temp `QUANTGEN_MACRO_DIR` per test and restores it in `finally` (spec:141-143).
  - The defaults that matter read the variable on every call:
    - `config.macro_dir()` reads it on each call (`config.py:176-178`), and the probe confirms this;
    - `register_trials` resolves its default at call time (`ui/strategy_lab_page.py:67`).
  - I found no module-level `macro_dir()` call in the modules the runner imports.
  - T-HERM-02's `home_listing` adds `QUANTGEN_MACRO_DIR` when it is set (`tests/macro_acceptance.py:120-121`). The
    guard restores the variable, so the root set it compares is unchanged.
- GOVERNANCE-R3-3: **resolved**.
  - A rehearsal `prices_file` must resolve under `tempfile.gettempdir()` (spec:198-203, 658, 1104, 1186).
  - L1-9 names a tracked cache file, `binance_BTCUSDT.csv` included (spec:1340).
  - Step 2 forbids opening or hashing the four real files (spec:1427).
  - QA-R4-2's ordering refinement completes this fix, and I concur with it (below).
- GOVERNANCE-R3-4: **resolved**.
  - 7A.3 names `qa/acceptance_results.json` (spec:1480).
  - Step 10 limits it to "an owner's Windows full run (Step 7A.2 and this step), never from Linux" (spec:1506).
- GOVERNANCE-R3-5: **resolved**.
  - Step 2 has the rule "Claude never writes or edits `owner_confirmed` or `host_fingerprint`" (spec:1427). Its scope
    is GOVERNANCE-R4-3.
  - The approval has a form, recorded verbatim with channel and date (spec:57-60, 1426).
- GOVERNANCE-R3-6: **resolved**.
  - Step 1a closes under C-8 (spec:15-18, 1425), and the plan names its revision (spec:1427).
  - Appendix B has a Round 3 column (spec:1650-1659) and the round-3 rulings table (spec:1739-1766).
  - 10.4 has one row per referee round (spec:1574-1576).
  - The round-4 bookkeeping is GOVERNANCE-R4-5.
- GOVERNANCE-R3-7: **resolved**. `core/quant/gate_package.py:36-38` is now cited at spec:210, 1117 and 1506. The
  tuple spans exactly those lines.

Rounds 1 and 2, re-checked against Revision 4. All stay resolved:
- GOVERNANCE-1 and GOVERNANCE-11: spec:43-53, 1488-1492.
- GOVERNANCE-2: O3 at spec:95. The clock guard's cites still match `nt:system/kernel.py:163-166`,
  `nt:trading/trader.py:422` and `nt:common/actor.pyx:4586-4591`.
- GOVERNANCE-3: R-15 at spec:1191.
- GOVERNANCE-4 and GOVERNANCE-5: spec:195-203.
- GOVERNANCE-6: spec:858.
- GOVERNANCE-7: L1-22 at spec:1353.
- GOVERNANCE-8: O14 and O15.
- GOVERNANCE-9: R-16 at spec:1192.
- GOVERNANCE-10: spec:871-873.
- GOVERNANCE-12: spec:1646-1647.
- GOVERNANCE-13: spec:1427.
- GOVERNANCE-R2-1: spec:55-56, 1425-1426.
- GOVERNANCE-R2-2: spec:1110-1120, 1187.
- GOVERNANCE-R2-3: L1-9.
- GOVERNANCE-R2-4: spec:692-694.
- GOVERNANCE-R2-5: spec:1486-1492. `origin/main` is still `716bf77` and is an ancestor of HEAD.
- GOVERNANCE-R2-6: the cites at spec:902 and 929.

## New issues

### GOVERNANCE-R4-1: `--fingerprint` carries the approval chain but has no specified behaviour, exit code or test

- **Severity:** minor.
- **Section:**
  - 5.3.1 (spec:664);
  - 6.6 (spec:1110-1120);
  - Step 7A.2's two `--fingerprint` lines (spec:1472-1473);
  - 7A.3 and 7A.4 (spec:1476-1485);
  - 8.3.
- **Problem:**
  - The owner writes `owner_confirmed` from `--fingerprint`'s output at 7A.3. Claude's 7A.4 review "recomputes
    `code_sha256` on Linux". The spec says only that `--fingerprint` "prints 6.6's host fingerprint, `table_sha256`
    and `code_sha256`".
  - **The ledger.** `host_fingerprint` needs the family ledger's first row (spec:1110). This container has no
    `~/.nextgen/macro/ledgers` (checked with `ls`).
    - Nothing says whether `--fingerprint` still prints the two digests there, or refuses.
    - 7A.4 names no other way for Claude to recompute.
    - The same question arises on the owner's machine if `E1.jsonl` or `C3.jsonl` is missing (O11, R-15).
  - **The table.** Nothing says how `--fingerprint` validates the table.
    - At 7A.2 the tables have no owner fields, and their `prices_file` is repo-relative.
    - The rehearsal rule of 3.9 refuses that path. Of-record validation requires the owner fields (spec:1098-1099).
    - So an implementation that reuses `check_table` in either mode refuses both pilot tables, and the owner cannot
      get the digests he must quote.
  - **The exit code and the test.**
    - Both 7A.2 `--fingerprint` lines lack the `if ($LASTEXITCODE) { throw ... }` that every other runner line carries
      (spec:1467-1471).
    - No test in 8.3 runs `--fingerprint`.
    - So a failure shows only as a missing number at 7A.3. A code fix then costs another Windows attempt and a new
      sign-off sentence (spec:50-51, 1484-1485).
- **Evidence:** spec:664, 1098-1099, 1110, 1467-1473, 1476-1485; `ls ~/.nextgen/macro/ledgers` reports that the path
  does not exist.
- **Proposed fix:**
  - `--fingerprint`:
    - validates the table against 6.6 with both owner fields optional;
    - never opens `prices_file`, `rf_file` or `reference_card`;
    - always prints `table_sha256` and `code_sha256`;
    - prints `host_fingerprint` when the family ledger exists and holds a row, and otherwise prints `null` with the
      reason;
    - exits 0 when both digests are printed.
  - Each 7A.2 line gains `if ($LASTEXITCODE) { throw "fingerprint" }`. 7A.3 adds: "a null host fingerprint stops here
    (R-15, O11)".
  - Add an L1 case (L1-36, or within L1-19). With the 3.3 guard's temp `QUANTGEN_MACRO_DIR`, `--fingerprint` on both
    committed pilot tables prints both digests and `host_fingerprint: null`, and exits 0. On a copy whose `prices_file`
    names a missing file, it still exits 0, which shows that it reads no data.
  - 7A.4 names this command as Claude's recomputation route.

### GOVERNANCE-R4-2: after 7A.3, what Claude's review commit may change and what Step 10 checks are open

- **Severity:** minor.
- **Section:**
  - Owner context (spec:50-51);
  - Step 7A.1, 7A.2's ancestry line, 7A.4 and 7A.5 (spec:1436-1438, 1453, 1482-1487);
  - Step 10 (spec:1506);
  - 6.6 (spec:1112-1120).
- **Problem:**
  - At run time, `code_sha256` binds the bridge and gate code. An of-record run also executes code outside it. Two
    examples:
    - `core/ficc/macro_schema.py:303-305` (`canonical_json`) forms every `config_id`, `row_md5` and ledger hash
      (`core/quant/gate_ledger.py:49, 168-171, 218, 372`).
    - `core/quant/gate_package.py` holds the list itself.
  - The house's own `HARNESS_SOURCES` accepts the same residual, so I do not ask for a wider digest. The gap is
    procedural:
    - 7A.4 does not say what Claude's review commit may change, and 7A.5 has the owner pull it before Step 8.
    - Step 10's `git diff` lists four protected areas, not the allowed paths.
    - So a review commit that touched `core/ficc/macro_schema.py` or `tests/macro_m0_harness.py` would pass R-11, R-01
      and Step 10.
  - The renewal rule for the sign-off sentence is narrower than the act it releases:
    - The Owner context and 7A.4 renew the sentence only for a code change "after a failed Step 7A".
    - A fix after a successful 7A, such as one before a 5.3.5 re-run of pilot 1, gets a new `owner_confirmed`. The
      sentence that released the T-RO-01 exemption and the merge is not renewed.
    - The owner makes the merge himself, so this is bounded.
  - The ancestry check runs at 7A.2, after 7A.1's sentence, so a merge of `origin/main` that it forces is already a
    code change after the sentence.
  - OPS-R4-1(b) shows a related path. An owner who merges a non-fast-forward 7A.3 push gets a 7A.3 commit whose code
    is not the code the sentence names. 7A.4's recompute "at the 7A.3 commit" does not detect it.
- **Evidence:** spec:50-51, 1112-1120, 1436-1438, 1453, 1482-1487, 1506; `core/ficc/macro_schema.py:303-305`;
  `core/quant/gate_ledger.py:49, 168-171`; `round4_claude_ops.md:180-194`.
- **Proposed fix:**
  - 7A.1: before recording the sentence, Claude runs `git fetch` and `git merge-base --is-ancestor origin/main HEAD`.
    If main has moved, Claude merges `origin/main` first, so the sentence covers the merged branch.
  - 7A.4:
    - Claude checks that the commit carrying the current sentence is an ancestor of the 7A.3 commit.
    - Claude checks that `git diff --name-only <sentence commit> <7A.3 commit>` lists only 7A.3's files: the census
      baseline, the egress record, the hand-off report, both tables and `qa/acceptance_results.json`.
    - Claude's review commit changes only this spec. A review that needs any other change means Step 7A has failed.
  - Step 10: `git diff --name-only <7A.5 HEAD>` lists only paths under `docs/nautilus_bridge/runs/`, the execution
    record, `README.md`, `qa/acceptance_results.json` and this spec.
  - Owner context and 7A.4: "any code change after the sign-off sentence needs a new one".

### GOVERNANCE-R4-3: the new Step 2 rule on owner fields has no scope

- **Severity:** minor (wording).
- **Section:** Step 2 Global Constraints (spec:1427); L1-19, L1-24 and L1-26 (spec:1350, 1355, 1357).
- **Problem:**
  - Read literally, "Claude never writes or edits `owner_confirmed` or `host_fingerprint`" forbids the test tables.
    L1-19 and L1-24 must build them in temp dirs with those fields, matching and mismatching.
  - The rule goes verbatim into the plan's Global Constraints, so an implementing agent will read it literally.
- **Evidence:** spec:1350, 1355, 1427.
- **Proposed fix:** "Claude never writes or edits `owner_confirmed` or `host_fingerprint` in a committed table (in
  `docs/nautilus_bridge/registration/`); tests write them only into tables under the system temp dir."

### GOVERNANCE-R4-4: pilot 2's precondition is procedural only, yet its rows are permanent and shared

- **Severity:** minor. The gap predates Revision 4.
- **Section:** §1 (spec:84); Step 9 (spec:1505); 10.2 "Precondition" (spec:1538); 7A.3 (spec:1476-1481); O14
  (spec:106).
- **Problem:**
  - Pilot 2 runs "only if pilot 1 passed parity". Nothing in the runner enforces this:
    - 7A.3 writes `owner_confirmed` for both tables at once;
    - both tables share one `code_sha256`;
    - R-11 checks neither the existence nor the outcome of a pilot-1 record.
  - So the runner accepts pilot 2 after pilot 1 refused, errored or failed a hard parity check.
  - Pilot 2 appends 5 permanent rows to `C3.jsonl`, which also holds paper_live's frozen-study rows (O14, K12).
    Registering them on an engine that failed parity on SPY leaves trials that test nothing.
- **Evidence:** spec:84, 106, 1476-1481, 1505, 1538; 5.3.2 step 1 (spec:701), which has no such check.
- **Proposed fix:**
  - Of-record `C3-BTCUSD` refuses with R-11 unless `<out root>/*/run.json` holds an of-record `E1-SPY` record that
    meets two conditions:
    - `parity.hard_pass` is true for all 12 columns at both cost levels;
    - its `code_sha256` equals this run's.
  - 6.3 records `code_sha256` explicitly, beside `table_sha256`.
  - Add an L1 case on temp roots: refused without such a record, and refused with a WITHHELD-for-parity record.
  - The owner may rule a looser link, for example to any earlier code. The strict link is the default.

### GOVERNANCE-R4-5: round-4 bookkeeping, including a real-data computation that 10.4 must record

- **Severity:** minor (bookkeeping).
- **Section:** Status (spec:5-20); Step 1a (spec:1425); 10.4 (spec:1564-1577); Appendix B (spec:1650-1659).
- **Problem:** Closing round 4 under C-8 needs four changes:
  - the Status and the Next line;
  - Step 1a's "Rounds 1 to 3 are ruled and applied";
  - a Round 4 column in Appendix B and a round-4 rulings table;
  - a 10.4 row, which "goes verbatim into the execution record" (spec:1566).

  That row has real content this time:
  - The quant referee re-scored the stored card `S_E1_trend_krx`. That run read four KRX ETF caches and
    `fred_DGS3MO.csv`, once on raw and once on 9-decimal closes (`round4_claude_quant.md:13-17, 229-235`).
  - This is allowed by the house rules: KRX is not a pilot window, and it is neither SPY nor BTC.
  - It adds no configuration. It is the stored card's 12 settings, symbols and cost, which pilot 1's U already counts
    through `study_configs` (spec:1523).
  - It is still a computation on real data in this session, so map04 R23 requires the row.
  - QA's P0a probe used stand-in downloaders and no real series (`round4_claude_qa.md:74, 189-192`).
  - My own review read no price file.
- **Evidence:** spec:15-20, 1425, 1566-1577, 1650-1659; `round4_claude_quant.md:13-17, 229-235`.
- **Proposed fix:**
  - Update the Status and Step 1a.
  - Add the Round 4 column and the rulings table.
  - Add the 10.4 row: "2026-10-26 | round-4 referees | synthetic series; the four KRX ETF caches and
    `fred_DGS3MO.csv` (quant referee, re-scoring the stored `S_E1_trend_krx` grid, raw and 9-decimal); stored cards'
    JSON; no SPY row from 2004-12-01, no BTC price | G-08 rules on a stored card, P0a stand-ins, digests | none".

### Concurrence with other round-4 referees

- **QA-R4-1** (P0a can fall through to a real download).
  - I concur, and from my lens it matters more than its label suggests:
    - the reader would be Claude's own Step 6 and 7 tests;
    - the data would be the full real SPY and BTC histories;
    - 3.9 calls them unseen;
    - no record would survive, because the temp cache is deleted.
  - I checked the code. The study imports `yfinance` and `pandas_datareader` lazily inside its loaders
    (`docs/asset_expansion_study.py:84, 96`), and `_cached` downloads whenever the named file is missing (`:68-76`). So
    stand-ins installed around the `study.yf`, `study.fred` and `study.rf_daily` calls are enough.
  - C-8 applies minor rulings before Step 2, so the minor label still gets it fixed in time.
- **QA-R4-2** (the place rule judged in `check_table`). I concur. It completes my GOVERNANCE-R3-3: a correct order
  never opens the real file, and a hash-first order now fails the test.
- **OPS-R4-1(b) and (c)** (the block never pulls; the hand-off records no HEAD). I concur, and I take no view on the
  severity.
  - For governance it fails closed: R-11 at Step 8 refuses an `owner_confirmed` that quotes stale code.
  - Recording HEAD in the hand-off report also lets 7A.4 tie Claude's review to the code that ran.
  - GOVERNANCE-R4-2's ancestry and diff checks cover the merged non-fast-forward case that OPS-R4-1(b) describes.

## Why I agree or not

I agree. Revision 4 applies every governance ruling of round 3 exactly. The authority chain is consistent in every place
it appears:
- Status;
- Owner context;
- O2 and O8;
- Steps 1a, 1b, 4 and 7A;
- the merge paragraph.

The chain runs in this order:
1. Step 1a releases branch work.
2. Step 1b's approval, in its stated form, gates Step 7A.
3. The sign-off sentence releases only the merge and the exemption.
4. `owner_confirmed` releases each table's of-record runs, and it now binds the gate code as well as the bridge
   (verified by probe).

The protections against an unregistered look at a pilot window now work by place, by content and by Claude-only rule.
QA-R4-1 and QA-R4-2 close the last two implementation slips.

None of my five items contradicts what is built:
- R4-1 specifies one CLI mode and adds one test.
- R4-2 adds three git checks in owner-run steps.
- R4-3 is wording.
- R4-4 adds one refusal before registration.
- R4-5 is bookkeeping.

Each gap fails closed or is caught before a pilot verdict is used, apart from two:
- GOVERNANCE-R4-4, where the owner's procedure is the only guard;
- the history row of GOVERNANCE-R4-5, which is a record, not a guard.

Neither needs another referee round. I support closing Step 1a under C-8 once the moderator has ruled the ops major.

## Notes

**Checked and correct:**
- **Revision 4 tallies.**
  - The round-3 tally of 3 major and 30 minor matches the reports: majors are quant 1 and ops 2; minors are
    2 + 7 + 12 + 2 + 7.
  - Appendix B's round-3 column matches `round3_rulings.md`.
  - The line count of 1,772 is right.
- **The reference card.** `md5(docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json)` is
  `d0bb0882fb51dec361cf2ddb160186bb`, as 10.2 pins. The cards directory still holds 34 files.
- **`.gitignore`.** It ignores `__pycache__/` and `*.pyc` (`git check-ignore`). So `python tests/run_all.py` without
  `-B` at 7A.2 leaves no untracked file that R-01 would refuse, and `code_sha256`'s `**/*.py` excludes bytecode.
- **`.gitattributes`.** It is still `* -text`, so `config.py`'s CRLF bytes digest the same on both platforms.
- **The rf default.** `rf = 0.0` in pilot 2 is the study default (`docs/asset_expansion_study.py:175`). `REFRESH = False`
  is at `:844`.

**Minor concerns carried from my round-2 and round-3 notes.** None was raised as an issue. Status:
- **"TRADEGEN's domain".** The §1 bullet now leads with "outside QUANTGEN's scope" (spec:79). It still calls live
  surfaces "TRADEGEN's domain" (spec:80). Part of this is done.
- **Data licence.** There is still no licence record for the Yahoo and FRED caches the cards cite.
- **README.** No README sentence names the T-RO-01 exemption (5.8 adds only the suite row).
- **Privacy.** The egress record and the hand-off report are committed and pushed:
  - they hold Windows paths under the owner's user profile and the firewall rule dump;
  - whether the GitHub remote is private is UNVERIFIED;
  - the host fingerprint is safe to push, because it is salted with a ledger row hash that stays local.

**UNVERIFIED in this review:**
- the owner's quoted sentences;
- whether `E1.jsonl` and `C3.jsonl` exist with rows on his machine;
- every Windows fact 13.1 lists;
- the data licences;
- whether the GitHub remote is private;
- whether Yahoo is reachable through this container's proxy (not tried, by the house rule).

**House rules kept during this review:**
- no file under `paper_live/` or `grokteam/` was edited or run;
- no `pip install`;
- no `tests/run_all.py`;
- no price file was opened or hashed, and no SPY row or BTC price was read;
- no ledger row was written;
- no commit;
- the only tracked-tree write is this report;
- the probe and its output sit in `scratch:referee4_governance/`.
