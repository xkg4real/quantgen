# Round 3 referee report: governance and compliance (Claude)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 3. It is an uncommitted working copy
over `7112351`, 1,663 lines, and I read all of it. I also re-read my round-1 and round-2 reports and both rulings
files.

Citation keys:
- `file:line` is QUANTGEN at HEAD `7112351`.
- `spec:<line>` is Revision 3.
- `nt:<path>:<line>` is `nautilus_trader` 1.231.0 in `scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
- `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probe, in `scratch:referee3_governance/`: `code_digest_probe.py`. It hashes a toy file set as 6.6's `code_sha256`
does, once with Windows path strings and once with POSIX ones. It reads no repository file and no price file.

## Verdict

**AGREE**, with seven minor concerns.

All 19 issues I raised in rounds 1 and 2 are resolved. Revision 3 brings no blocker and no major issue from my lens.
The seven new items are all minor:
- `owner_confirmed` does not cover the gate code;
- one test can write pilot rows into the production ledger by default;
- the rehearsal refusal misses two real BTC caches;
- Step 7A.3 and Step 10 disagree about the results file;
- nothing stops Claude from writing the owner's fields;
- the round-3 bookkeeping is missing;
- one citation is wrong.

## Sections reviewed

- Status, Inputs, citation keys and Owner context (spec:1-56).
- §1 scope (spec:58-80) and §2 owner rulings O1 to O15 (spec:82-103).
- §3.1 to §3.12, all binding constraints (spec:105-219).
- §4.1 to §4.4: architecture, launch contract and egress layer (spec:221-295).
- §5.1; §5.2.1 to §5.2.9, including the sandbox skeleton (spec:299-622).
- §5.3.1 modes, seams and pure steps; §5.3.2 order of operations; §5.3.5 lifecycle and re-runs (spec:624-737).
- §5.5 gate hand-off, §5.6 T-RO-01 amendment, §5.7 suite and §5.8 file table (spec:809-965).
- §6.3 run record, §6.4 ledger rows, §6.5 card, §6.6 registration table and digests, §6.7 venv reads (spec:1003-1104).
- §7 error table R-01 to R-17, C-01 to C-15 and G-01 to G-08 (spec:1117-1166).
- §8.1 stub child; §8.3 layer-1 tests 5, 6, 9, 10, 19 and 22 to 25; §8.5; §8.6 (spec:1168-1352).
- §9 Steps 1a to 10, Step 7A items 1 to 5, the merge paragraph and the done-when (spec:1354-1432).
- §10.1 to §10.4 (spec:1434-1505); §11 risks 13, 14, 19 and 20; §12; §13; Appendix B (spec:1507-1663).
- House sources checked:
  - `core/quant/gate_package.py:36-38` (`HARNESS_SOURCES`);
  - `core/quant/gate_ledger.py:122-131, 337-356`;
  - `core/quant/validate.py:53-74`;
  - `ui/strategy_lab_page.py:55-77`;
  - `tests/macro_acceptance.py:52-70, 112-122`;
  - `config.py:32-39, 176-178`;
  - `tests/run_all.py:35-38`;
  - `data/fmp/quote_client.py:108-116`;
  - `tests/macro_m7_cards.py:831-834`;
  - `docs/asset_expansion/study.log:27, 29`;
  - `grokteam/prereg.py:85-89`, read only;
  - `paper_live/*.py`, grep only;
  - `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:28-31`;
  - `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:85-91, 142-144`;
  - `.gitattributes`.
- Nautilus sources: `nt:common/actor.pyx:4584-4592`, `nt:system/kernel.py:160-171`, `nt:trading/trader.py:420-423` and
  `nt:common/component.pyx:1938-1971`.
- Git checks:
  - `git branch -a`;
  - `git merge-base --is-ancestor origin/main HEAD`;
  - `git ls-remote origin main`;
  - `git log origin/main..HEAD`;
  - `git show --stat 716bf77`;
  - `git ls-files qa/`;
  - `git diff --stat origin/main..HEAD -- docs/asset_expansion/cache/`.

## Earlier issues

- GOVERNANCE-1: **resolved**. The owner's words decide two things, and everything else is a default listed with its
  cost (spec:41-43).
- GOVERNANCE-2: **resolved**. O3 quotes both halves (spec:91). The `on_start` clock guard rests on cites I re-checked:
  `nt:system/kernel.py:163-166`, `nt:trading/trader.py:422`, `nt:common/component.pyx:1941-1970`.
- GOVERNANCE-3: **resolved**. R-14, R-15 and the host fingerprint are in place (spec:670-673, 1138-1139). They are now
  testable through `check_table` and `check_egress_record` (L1-23, L1-24).
- GOVERNANCE-4: **resolved**. Refusal is by content, with dates filtered before parsing (spec:193-197, 674).
- GOVERNANCE-5: **resolved**. Rehearsal is synthetic only, and the md5 refusal applies whatever the `end`
  (spec:191-197, 635, 1279). The residual is GOVERNANCE-R3-3.
- GOVERNANCE-6: **resolved**. Both engines are scored, and a card needs equal decisions and equal predicates
  (spec:817, 1158).
- GOVERNANCE-7: **resolved**. L1-22 fails if `nautilus_trader` is in the global interpreter (spec:1292). R-03 refuses
  an installed parent distribution and a Store-Python base (spec:672, 1127).
- GOVERNANCE-8: **resolved**. O14 and O15 cover it (spec:102-103).
- GOVERNANCE-9: **resolved**. 3.8 and R-16 refuse while `C3.jsonl` or the family ledger is fresh (spec:181-184, 1140).
- GOVERNANCE-10: **resolved**. 5.6 and O2 say this is the first exemption (spec:90, 830-833).
- GOVERNANCE-11: **resolved**. The merge is the owner's own act, after the sign-off sentence (spec:44-46, 1417-1419).
- GOVERNANCE-12: **resolved**. Appendix B covers it (spec:1567-1570).
- GOVERNANCE-13: **resolved**. Step 2's Global Constraints are still all of section 3, verbatim (spec:1363).
- GOVERNANCE-R2-1: **resolved**. Steps 1a and 1b exist, and the Status, Owner context, O8 and §9 agree
  (spec:15-18, 53-56, 96, 1361-1362).
- GOVERNANCE-R2-2: **resolved**.
  - The sign-off sentence releases only the merge and the exemption, and a failed Step 7A needs a new sentence
    (spec:44-51, 1413-1414).
  - `owner_confirmed` quotes `table_sha256` and `code_sha256`, and R-11 refuses on a mismatch. L1-19 has both cases
    (spec:670, 1063-1069, 1289).
  - The scope of the code digest is GOVERNANCE-R3-1.
- GOVERNANCE-R2-3: **resolved** (spec:193-197, 635, 1134, 1279).
- GOVERNANCE-R2-4: **resolved**. The pure steps `take_lock`, `check_table`, `check_tree` and `check_egress_record`
  exist. The constraint reads "Claude never runs of-record mode; a call refused in argument validation is not a run"
  (spec:649-663, 1363).
- GOVERNANCE-R2-5: **resolved, as modified**.
  - The ruling is correct. `origin/main` is `716bf77` (confirmed by `git ls-remote`), and it is an ancestor of HEAD.
  - My round-2 premise came from the stale local `main`, `d330054`.
  - The spec now requires a merge commit (no squash, no rebase), keeps the branch ref, and adds 7A.5 (spec:1415-1419).
  - The merge timing is OPS-R3-7.
- GOVERNANCE-R2-6: **resolved**. I re-checked all four cites:
  - `data/fmp/quote_client.py:110, 115`;
  - `nt:common/actor.pyx:4588-4591` (re-raise);
  - the split spec's `:142`;
  - `tests/run_all.py:35-38`.

## New issues

### GOVERNANCE-R3-1: `owner_confirmed` does not bind the gate code that the of-record run executes

- **Severity:** minor.
- **Section:** §6.6 `code_sha256` (spec:1066-1069); §5.3.2 steps 1, 7 and 9 (spec:670, 676, 678); §5.5 step 6
  (spec:817); Step 7A merge and Step 10 (spec:1417-1419, 1432).
- **Problem:**
  - `code_sha256` covers `tools/nautilus/**/*.py`, `tools/nautilus/golden/*.json` and `requirements-nautilus.txt`.
  - An of-record run also executes QUANTGEN code whose output decides the card:
    - `core/quant/validate.py`: `GATE`, `walk_forward`, `score_strategy` and `cost_floor_bp`;
    - `core/quant/strategies.py`: `simulate` and `grid_from`;
    - `core/quant/gate_ledger.py`;
    - `docs/asset_expansion_study.py`, which is loaded by path and run for P0a;
    - `config.py`, whose `macro_dir()` picks the ledger directory.
  - Only one `GATE` value is pinned: R-08 checks `bootstrap_B` (spec:678, 1132). G-04 compares `GATE` with a snapshot
    taken in the same run (spec:817), so it cannot see a change made before the run.
  - So a commit between 7A.3 and Step 8 can change `dsr_min`, `bench_p_max` or `trades_floor`
    (`core/quant/validate.py:53-74`) and still pass R-11. The card's verdict then comes from a gate the owner did not
    confirm.
  - Such a commit is plausible:
    - `origin/main` moves through the owner's own uploads. `716bf77` "Upload project structure" (2026-10-26 22:30
      +0900) added two files after this session began.
    - OPS-R3-7's fix merges `origin/main` into the branch when main has moved.
  - The house already defines this set. `HARNESS_SOURCES` (`core/quant/gate_package.py:36-38`) lists the files where
    "an edit to any of them is a package change".
  - Step 10 checks the harness sources too late. It runs `git diff` "against the Step 7A commit" only after the
    pilots, when the rows are already permanent. "The Step 7A commit" could also mean any of three commits (7A.1, 7A.3
    or 7A.4).
- **Evidence:** spec:670, 676, 678, 817, 1066-1069, 1132, 1432; `core/quant/gate_package.py:36-38`;
  `core/quant/validate.py:53-74`; `git show --stat 716bf77`; `round3_claude_ops.md` OPS-R3-7.
- **Proposed fix:**
  - Extend `code_sha256` to the files of `core.quant.gate_package.HARNESS_SOURCES`, imported so the list has one home,
    plus `docs/asset_expansion_study.py` and `config.py`.
    - Then any later edit to the gate needs a new `owner_confirmed`, so the owner re-approves the gate he runs.
    - If the full harness list causes too much churn, use at least `validate.py`, `strategies.py`, `gate_ledger.py`,
      `costed.py`, the study file and `config.py`.
  - Add an L1-19 case: a byte changed in `core/quant/validate.py` after confirmation must refuse.
  - In Step 10, write "against the 7A.5 HEAD that the pilot run records store".

### GOVERNANCE-R3-2: L1-10 registers the pilots' own configurations through a function whose default is the production ledger

- **Severity:** minor.
- **Section:** §8.3 L1-10 (spec:1280); §3.3 (spec:134-138).
- **Problem:**
  - L1-10 compares the bridge's `config_id` with the one `ui.strategy_lab_page.register_trials` writes. It uses SPY
    `sma/126/21` at 50.0 and BTC-USD `hysteresis 0.222` at 10.0.
  - Both are pilot rows. `sma/126/21` is in pilot 1's grid (spec:1445), and 0.222 is in pilot 2's (spec:1460).
  - `register_trials` writes to `config.macro_dir() / "ledgers"` unless `ledger_dir` is passed. It registers nothing
    when `sources` contains "SYNTHETIC" (`ui/strategy_lab_page.py:55-67`). So the test must pass real-looking sources
    to get a row at all, and it must remember `ledger_dir`.
  - If the test forgets `ledger_dir`, a full suite run appends those two rows to the real `E1.jsonl` and `C3.jsonl`.
    - On the owner's machine that happens at Step 7A.2's `python tests/run_all.py` (spec:1402), before any pilot.
    - Rows are permanent, and a duplicate `config_id` returns the first row
      (`core/quant/gate_ledger.py:337-346`).
    - So pilot 1's `sma/126/21` row and pilot 2's 0.222 row would carry the test's `source`, `span` and anchor for
      good.
    - C3 also holds paper_live's frozen-study rows (K12).
  - The 3.3 guard and T-HERM-02 (`tests/macro_acceptance.py:112-121`) detect such a change after the fact. Neither
    prevents it. On Linux, a slip would most likely be caught at Step 6 first, so this is a defence-in-depth gap, not
    an expected failure.
- **Evidence:** spec:134-138, 1280, 1402, 1445, 1460; `ui/strategy_lab_page.py:55-77`;
  `core/quant/gate_ledger.py:337-356`; `tests/macro_acceptance.py:112-122`.
- **Proposed fix:**
  - L1-10 passes `ledger_dir=<temp>` explicitly. It uses configurations outside both pilot grids, for example SPY
    `sma/127/21` and BTC-USD `hysteresis 0.333`. K9 is about types and ordering, not these particular values.
  - The 3.3 guard resolves the real production dir once, then sets `QUANTGEN_MACRO_DIR` to a fresh temp dir for each
    `nautilus` test and restores it in `finally`. A default path inside a test then lands in a temp dir. The
    before/after digest of the real dirs stays as the detector.

### GOVERNANCE-R3-3: the rehearsal refusal names two real files, and the cache holds two more real BTC series

- **Severity:** minor.
- **Section:** §3.9 (spec:193-197); §5.3.1 rehearsal row (spec:635); §7 R-10 (spec:1134); §8.3 L1-9 (spec:1279);
  Step 7 (spec:1368).
- **Problem:**
  - In rehearsal, the runner refuses a prices file in two cases:
    - its md5 equals the pinned SPY or BTC-USD md5;
    - its resolved path is `yf_SPY.csv` or `yf_BTC-USD.csv`.
  - The tracked cache also holds `docs/asset_expansion/cache/binance_BTCUSDT.csv` (68,632 bytes) and
    `upbit_KRW-BTC.csv` (75,588 bytes). By their names and the study's cache they are real BTC price series. I did not
    open them, per the house rule.
  - Their sizes differ from `yf_BTC-USD.csv`'s 120,553 bytes, so their md5s differ, and neither path is named. A
    rehearsal table that names either file passes R-10. It then runs a scored `crypto_trend` gate run on real BTC
    prices, outside the ledger of record.
  - Step 2's rule "Claude reads no real BTC price" still forbids this. So the guard rests on procedure again, the
    shape of GOVERNANCE-R2-3. The harm is smaller here: the study has already scored the BTC window (10.4, second row),
    and pilot 2 is labelled an engine replication.
  - A related gap: Step 7 writes both tables with `prices_md5` but does not say where Claude gets the value. Hashing
    `yf_SPY.csv` or `yf_BTC-USD.csv` reads every byte of the pilot windows, yet both values are already in the spec
    (spec:1444, 1459).
- **Evidence:** spec:193-197, 635, 1134, 1279, 1368, 1444, 1459; `git ls-files` (the two caches are tracked);
  `ls -l` sizes.
- **Proposed fix:**
  - In rehearsal, `prices_file` must resolve (`normcase(realpath)`) under `tempfile.gettempdir()`, as `--ledger-dir`
    and `--out-dir` already must. Keep the md5 refusal, which catches byte copies.
    - Every planned rehearsal input is already a synthetic file in a temp dir (L1-9, L2-7, N6 and the stub runs), so
      none of them changes.
    - `rf_file` may still name the real DGS3MO file.
  - Add an L1-9 case: a table that names any file under `docs/asset_expansion/cache/` refuses by path before any read.
  - Add a Claude-only rule to Step 2: "the pinned md5s come from this spec; Claude never opens or hashes `yf_SPY.csv`,
    `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv`".

### GOVERNANCE-R3-4: Step 7A.3 and Step 10 disagree on when `qa/acceptance_results.json` is committed

- **Severity:** minor.
- **Section:** Step 7A item 3 (spec:1407-1411); Step 10 (spec:1432).
- **Problem:**
  - 7A.2 runs `python tests/run_all.py` (spec:1402). That rewrites `qa/acceptance_results.json`, which is tracked
    (`git ls-files qa/`).
  - 7A.3 commits "the results file" together with the baseline, the egress record and the tables. It has to: otherwise
    R-01 refuses Step 8 for a tracked change (spec:1125).
  - Step 10 says the file "is committed from that run only", meaning Step 10's own run.
  - The house rule is "committed only right after a full run"
    (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:30`), and both runs are full runs.
  - "The results file" is never named in 7A.3, so it can be misread as the hand-off report.
- **Evidence:** spec:1125, 1402, 1407-1411, 1432; `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:30`.
- **Proposed fix:**
  - 7A.3 names `qa/acceptance_results.json`.
  - Step 10 reads: "is committed only from an owner's Windows full run (Step 7A.2 and this step), never from Linux".

### GOVERNANCE-R3-5: no rule stops Claude from writing the owner's fields, and the Step 1b approval has no form

- **Severity:** minor.
- **Section:** Step 2 Claude-only rules (spec:1363); §6.6 (spec:1063); Step 1b (spec:1362); Status (spec:16-17).
- **Problem:**
  - `owner_confirmed` is the owner's approval of of-record runs.
    - R-11 checks only that it quotes the right digests (spec:1135), and `--fingerprint` prints those digests for
      anyone who runs it.
    - So its authenticity rests only on who made the commit that wrote it.
    - Step 7 says Claude writes the tables "without their owner fields" (spec:1368). The Claude-only rules of Step 2 do
      not forbid a later Claude edit.
  - Step 1b gates Step 7A on "the owner's approval line and answers to O1 to O15" in the Status block (spec:1362).
    - That line has no form, and no rule says who writes it.
    - The sign-off sentence has both (spec:46-48).
    - The Owner context already notes that chat quotes cannot be checked later (spec:37-39).
- **Evidence:** spec:37-39, 46-48, 1063, 1135, 1362-1363, 1368.
- **Proposed fix:**
  - Add a Claude-only rule to Step 2: "Claude never writes or edits `owner_confirmed` or `host_fingerprint`".
  - Give the approval a form, recorded verbatim with its channel and date, as the sign-off sentence is: "I approve
    spec 2026-10-26 revision <n> on the section 2 defaults, except: <O-number: ruling>. Geon Koh, <date>."

### GOVERNANCE-R3-6: the Status and Appendix B do not account for a Claude round 3, and 10.4 has no row for it

- **Severity:** minor.
- **Section:** Status (spec:5-18); Step 1a (spec:1361); §10.4 (spec:1489-1501); Appendix B, Round 3 (spec:1659-1663).
- **Problem:**
  - The Status says Step 1a is done and Step 2 is next (spec:15, 18), and Step 1a's done-when says "Done for rounds 1
    and 2" (spec:1361).
  - A Claude round 3 on Revision 3 is running now: four round-3 reports already sit in the review folder.
    - If round 3 leads to a Revision 4, the Status is stale.
    - The Step 2 plan could then be written against the wrong revision.
  - Appendix B's Round 3 table covers GPT and Gemini only (spec:1659).
  - 10.4 goes "verbatim into the execution record" (spec:1491). It has no row for the round-3 referees' probes.
- **Evidence:** spec:15, 18, 1361, 1491, 1659-1663; the review folder listing.
- **Proposed fix:**
  - Step 1a is done when the moderator closes the Claude debate, by every persona agreeing or by a ruling.
  - Step 2's plan names the spec revision it implements.
  - Appendix B gains the Claude round-3 rows.
  - 10.4 gains one row per referee round.

### GOVERNANCE-R3-7: one citation slip

- **Severity:** minor.
- **Section:** §3.10 (spec:204); Step 10 (spec:1432).
- **Problem:**
  - `core/quant/gate_package.py:35-37` should be `:36-38`.
  - Line 35 is a comment.
  - Line 38 holds the last harness source, `docs/macro_overlay_study.py`. The current range leaves it out.
- **Evidence:** `grep -n HARNESS_SOURCES core/quant/gate_package.py` gives line 36, and the tuple ends at line 38.
- **Proposed fix:** cite `core/quant/gate_package.py:36-38` in both places.

## Why I agree or not

I agree. A team could start Steps 2 to 7 today without asking me anything:
- The authority chain is consistent everywhere it appears. Step 1a releases branch work, Step 1b gates Step 7A, the
  sign-off sentence releases the merge and the exemption, and `owner_confirmed` releases each table's of-record run.
- Every fail-closed condition that guards governance has a reachable negative control, either through the pure
  functions or through argument-validation refusal.
- The rehearsal path cannot take the real SPY or BTC-USD pilot files by content or by name.

The seven new items are tightenings, not contradictions in what is built:
- R3-1, R3-2 and R3-3 each widen an existing check or test by a few lines.
- R3-4, R3-5 and R3-6 are wording and bookkeeping in owner-run steps.
- R3-7 is a citation fix.

Every owner-side gap I found fails closed or is caught by an existing detector before a pilot's verdict is used. The
one exception is GOVERNANCE-R3-1, and Step 10 catches that afterwards.

## Notes

**Checked and correct:**
- **Merge target.** `origin/main` is `716bf77` (from `git ls-remote origin main`). `git merge-base --is-ancestor
  origin/main HEAD` succeeds, and the branch adds four commits (`f5742ab` to `7112351`).
- **Line endings.** `.gitattributes` is `* -text`, as 6.6 says, so file bytes are identical across platforms.
- **Nautilus cites.** These match the installed source:
  - the actor re-raises an `on_bar` exception (`nt:common/actor.pyx:4589-4591`);
  - the kernel's clock choice (`nt:system/kernel.py:163-166`);
  - the per-component clock (`nt:trading/trader.py:422`);
  - `start` re-raises and leaves the component STARTING (`nt:common/component.pyx:1941-1970`).
- **O9.** `docs/asset_expansion/study.log:27, 29` show numpy under
  `...\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\...`, and `grokteam/prereg.py:87-88` names the
  Store interpreter (read only). This supports O9's statement and R-03's Store refusal.
- **3.11.** `docs/asset_expansion/cards/` holds 34 files, as `tests/macro_m7_cards.py:833` asserts.
- **3.8.** No `paper_live/*.py` file defines a lock (grep only).
- **Step 7A.2.** The branch changes nothing under `docs/asset_expansion/cache/`, so `git switch` leaves the cached
  mtimes alone.
- **`docs/quant_lab/SPY.json`.** It is a grading report (`ui/quant_lab_page.py:192`; `docs/quant_lab_grading.py:12`),
  not a price file. I did not open it.
- **Re-run policy (5.3.5).** A re-run after a code change needs a new `owner_confirmed`, because the code digest
  changes. So "re-run until the card is favourable" needs the owner each time, and the `supersedes` chain records it.

**Concurrence with other round-3 referees:**
- **OPS-R3-6** (the `code_sha256` path separator). My probe agrees: the same bytes give `481ec3f7...` with POSIX paths
  and `6da96816...` with Windows `str()` paths, and `as_posix()` makes them equal
  (`scratch:referee3_governance/code_digest_probe.py`). This matters for governance: without `as_posix()`, Claude's
  7A.4 review on Linux cannot confirm that `owner_confirmed` names the reviewed tree. I do not raise it again.
- **OPS-R3-7** (merge after Step 10, and a check that `origin/main` has not moved before the switch). From my lens, it
  also closes most of GOVERNANCE-R3-1's window.

**Minor concerns carried from my round-2 notes.** I never raised these as issues, so none has a ruling, and all are
still open:
- **Data licence.** No licence record exists for the Yahoo or FRED caches that the cards cite.
- **README.** No README sentence names the T-RO-01 exemption.
- **"TRADEGEN's domain".** §1 still calls `TradingNode`, adapters and API keys "TRADEGEN's domain" (spec:75-76).
  "Outside QUANTGEN's scope" would avoid seeming to endorse venues that `reports/Korean resident trading venue
  legality.md` rates illegal for a Korean resident (round-2 note).

**UNVERIFIED in this review:**
- the owner's quoted sentences;
- the owner's local branch names and whether his main clone already has a local `claude/amazing-gauss-tdiguu`;
- whether `E1.jsonl` and `C3.jsonl` exist with rows on his machine;
- the content of `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv` (inferred from their names and the study's cache; not
  opened);
- the data licences;
- whether the GitHub remote is private;
- every Windows fact that Step 7A is meant to answer.

**House rules kept during this review:**
- no file under `paper_live/` or `grokteam/` was edited or run;
- no `pip install`;
- no `tests/run_all.py`;
- no SPY row and no real BTC price was read (only file names and sizes);
- no ledger row was written;
- no commit;
- the only tracked-tree write is this report;
- the probe sits in `scratch:referee3_governance/`.
