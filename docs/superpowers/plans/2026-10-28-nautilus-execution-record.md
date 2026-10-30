# Execution record: NautilusTrader bridge, plan Tasks 1 to 5 (2026-10-28)

Branch `claude/amazing-gauss-tdiguu`. Plan: `docs/superpowers/plans/2026-10-26-nautilus-bridge.md`. Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, revision 6. Step 1b is still open: the GPT and Gemini rounds and the owner's approval have not happened.

The plan was executed in the cloud container one task at a time: one implementer and one verifier per task. Step ③-6 followed. It made one more cache-free full run, ran the `nautilus` suite with the key unset and with the key set, and compared every count with the Count Ledger.

Every decision made on the owner's behalf during Tasks 1 to 5 and ③-6 is listed below in the order it was made, with what it costs if wrong.

This file covers spec Steps 3 to 7. Spec Step 10's close-out record (`docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md`, which carries the data-access history of spec 10.4) comes after the pilots. It builds on this file.

## Commits

| Task | Spec step | Commit | Parent | Committed (UTC) | numstat (insertions/deletions) | Against the plan |
|---|---|---|---|---|---|---|
| 1 | 3 Environment | `e83ff6f` | `dd1244a` | 2026-10-28 11:58:49 | 12 files, 2868 insertions | `12 files changed, 2868 insertions(+)`: match |
| 2 | 4 Guard | `76295d0` | `e83ff6f` | 12:17:15 | `README.md` 2/1, `tests/macro_m0_harness.py` 491/1, `tests/macro_registry.csv` 1/1, `tests/nautilus_acceptance.py` 67/0, `tests/run_all.py` 17/2 | the plan's expected numstat, line for line: match |
| 3 | 5 Sandbox | `321b829` | `76295d0` | 12:39:49 | `tests/nautilus_acceptance.py` 471/0, `tools/nautilus/launch.py` 51/0, `tools/nautilus/sandbox.py` 249/8 | match |
| 4 | 6 Runner | `6b6b386` | `185b56c` | 16:40:41 | 7 files, 4095 insertions (runner 1773, stub 221, tests 1040, goldens 42 + 42 + 24, census 953) | `7 files changed, 4095 insertions(+)`; runner md5 `01b576997547d17d8f318fb67f26bac6`: match |
| 5 | 7 Parity and gate | `520d0db` | `6b6b386` | 17:14:27 | `RUNBOOK_windows.md` 181/0, `pilot1_E1_spy.json` 70/0, `pilot2_C3_btcusd.json` 50/0, `tests/nautilus_acceptance.py` 640/0, `tools/nautilus/parity.py` 523/0, `tools/nautilus/runner.py` 251/5 | md5s: `parity.py` `71258dfa6e253e07b51fa4d939bb3b8e`, `runner.py` `bffca79a6f40b5380b5e1a31a7fae2ad`, the tables `90c07844c6247da0e80c731d50f6a6aa` and `e6189fdb5f43beed34b5909e65009af1`, the runbook `df14943a64529da46963e093aff30a76`; the test module checked by numstat 640/0. All match (re-checked at ③-6) |

**Commits from other work streams.** Between Tasks 3 and 4, other work streams committed four times: `32f91e5` (the progress chart), `22bdc16` and `420af64` (②-5 queue step 2, under `docs/audit/2026-10-27/proposed_patches/`) and `185b56c` (owner rulings).

**Push and trailers.** All nine commits are on `origin/claude/amazing-gauss-tdiguu`, and the branch HEAD is `520d0db`. No tag was pushed. Each of the five task messages ends with the plan's two trailer lines.

**Frozen paths.** `git diff --stat dd1244a..HEAD` over `paper_live/`, `grokteam/`, `core/`, `docs/asset_expansion/` and `qa/acceptance_results.json` is empty. In particular, `core/quant/gate_ledger.py` is unchanged.

## Owner rulings that governed execution

- **2026-10-28, `185b56c`** (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, last section):
  - **③-4 go.**
  - **K-g option (a).** The runner refuses an UNVERSIONED anchor with R-02 before it writes to any ledger, as the spec and plan say. `core/quant/gate_ledger.py` is a frozen harness source (`core/quant/gate_package.py:36`) and is not edited. The Strategy Lab side of K-g (UNVERSIONED in ledger rows) is deferred to a later owner approval.
  - **②-5 queue order approved.** Claude reads this as approval of the order only. Each owner-decision item in it is still decided separately. Claude-only steps proceed in order.
- **Binding plan rulings for every task.** Three Stage B rulings bound every task:
  - X-1: every full run goes through the cache-free copy script `$S/full_run.sh`.
  - X-2: the clock and sign-off rows.
  - T5-1: every scratch clone is sparse.
- **Owner fields.** Claude did not write `owner_confirmed` or `host_fingerprint` in any committed table, wrote no ledger row outside a temp dir, and never ran of-record mode.

## Rulings (19)

1. Task 1: Ruling (binding-driven, T5-1 and X-1): `$S/full_run.sh` was written with T5-1's sparse recipe instead of Step 0's literal heredoc.
   - The recipe: `git clone -q --no-checkout`, then `git sparse-checkout set --no-cone '/*'` with one exclusion per protected cache, then `git checkout -q`, then a `git ls-files -t` check that all four caches are skip-worktree entries.
   - The difference from the plan's text: one comment line, and the plain `git clone` line replaced by those four lines.
   - Reason: a plain clone writes `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv` to disk at checkout.
   - Every full run of Tasks 1 to 5 and of ③-6 used this script. At ③-6, every one of the seven clones (`$S/full_<name>`) showed `4` skip-worktree entries and `0` of the four files on disk.
   - Cost if wrong: none to the counts. The plain recipe deletes the same four files before any test runs, so the rows are the same.
2. Task 1: Ruling: Step 0 started at HEAD `dd1244a` (②-2 stage C). Step 0 accepts "`fa28059` or a later commit".
   - B was re-measured on the cache-free copy: `749/876 passed, 2 failed, 125 not run`, with M = 548 `macro` rows.
   - The FAIL set is `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache` (`AssertionError: `) and `papers/test_debate_run_kills_process_tree` (no `taskkill`).
   - Both X-2 clock rows are NOT_RUN. These are the same counts the Count Ledger measured on `659898b`.
   - Every later comparison reads this file, `$S/t1_baseline.json`.
   - `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` and `config.py` still match Step 0's sha256 (`$S/t1_pre_sha256.txt`, re-checked at ③-6).
   - Cost if wrong: none. ③-6 re-checked all six full runs against this file.
3. Task 4: Ruling (incidental): HEAD at Step 1 was `185b56c`, not Task 3's commit `321b829`.
   - X8's second part accepts a later HEAD when `git diff --name-only 321b829 185b56c` lists no File Structure path. The 16 listed paths are all under `docs/audit/2026-10-27/proposed_patches/` or `docs/nautilus_bridge/` (the rulings log and the progress chart).
   - Cost if wrong: none for code. Task 4's files are new, and its anchor in `tests/nautilus_acceptance.py` is unchanged since `321b829`.
4. Task 4: Ruling (incidental, method only): Step 2's insertion and the two new files were written byte-exact from the plan's code fences by a small script, not retyped into the Edit tool.
   - The scripts: `$S/t4_blocks/extract.py`, plus `$S/t2_blocks/apply.py`, which makes an exact one-occurrence replacement of the four-line `# CLI` anchor and refuses any file that contains `\r`.
   - The runner md5 `01b576997547d17d8f318fb67f26bac6` equals the plan's, and the test-module numstat is 1040/0.
   - The file is LF, not one of the CRLF files.
   - Cost if wrong: none. The bytes are identical.
5. Task 4: Ruling (binding-driven, X-1): Step 10's full run used `bash $S/full_run.sh t4_after` instead of the plan's literal `python3 -B $S/run_baseline.py $S/t4_after.json` in the real clone. The output files are the same (`$S/t4_after.json`, `$S/t4_after.log`). Cost if wrong: none. The run in the real clone would have opened protected caches.
6. Task 4: Ruling (binding-driven, T5-1 and X-6): Step 7's `--egress-record` scratch clone used the sparse recipe, with the `ls-files -t` check giving `4`. The plan's text was a plain `git clone` followed by `rm -f` of the four caches. Cost if wrong: none. The plain recipe writes the four files at checkout.
7. Task 4: Ruling (incidental): the commit message was passed as `git commit -q -F <file>`. The file was extracted verbatim from the plan's heredoc (`$S/t4_blocks/commit_msg.txt`), so the message bytes are the same. Cost if wrong: none.
8. Task 5: Ruling: Task 5 (③-5) ran on the owner's go-ahead for the ③ sequence. The owner asked Claude to start at ③-1 and to stop once, just before ③-4 ("일단 3-1부터 바로 시작해주시고, 3-4 들어가기 직전에 한번 알려주세요"), then said "3-4 진행". Claude read that as continuing in order through ③-6 and gave the owner completion estimates for ③-5 and ③-6 in its reply. The ②-5 queue-order approval is not what authorised it.
   - Step 1 found HEAD at Task 4's pushed commit `6b6b386`, which is the starting point Step 1 requires.
   - The computed task text had said only Tasks 1 to 3 were committed.
   - Cost if wrong: Task 5 landed before an owner review of Task 4. Task 5 changes only bridge files, and its commit can be reverted on its own.
9. Task 5: Ruling (incidental, method only): Step 2 and Step 7's edit 3 were applied with a Python exact-string replacement instead of the Edit tool.
   - Step 2 is the 640-line test block. Step 7's edit 3 replaces Task 4's `main` with the 283-line Task 5 block.
   - The script asserted exactly one occurrence of the old string, and both the old and the new text were extracted byte for byte from the plan's fences.
   - Step 7's edits 1 and 2 and the Step 5 seam used the Edit tool.
   - Both files are LF. Results: numstat 640/0 and `runner.py` md5 `bffca79a6f40b5380b5e1a31a7fae2ad`.
   - Cost if wrong: none. The bytes are the same.
10. Task 5: Ruling (incidental): Steps 4, 9 and 11 wrote `parity.py`, the two registration tables and `RUNBOOK_windows.md` by copying byte-exact extractions of the plan's blocks. All four md5s equal the plan's (re-checked at ③-6). Cost if wrong: none.
11. Task 5: Ruling (binding-driven, X-1): Step 14's full run used `bash $S/full_run.sh task5_full`. The four protected caches were never checked out or opened. The script exited 1 because the wrapper exits non-zero whenever B's two FAILs are present. The log and the counts are the expected ones. Cost if wrong: none.
12. Task 5: Ruling (incidental, anticipated by the plan): `tests/nautilus_acceptance.py` has md5 `5246f204d31234b9de8ec4c93bb8a13c`, not `3ee44de50bf4433063a392fef18d241d`.
    - Task 4's committed module was `f9ed827ef6b112ff51c201dc3fc45ff0`, not the scratch file `8694bc60...` that the plan's md5 was measured on.
    - For that case, the plan says to expect other md5s and to check numstat instead (640/0).
    - Cost if wrong: none.
13. Task 5: Ruling (incidental): Step 12's printed `--timing` numbers differ from the dry run. The total was 16.063 s against 15.2 s, and `import_us` was 727272 against about 0.86 s. The plan prints these numbers and asserts only 12 runs of 5,600 bars with exit 0. Cost if wrong: none. The Windows timing of Step 7A.2 is the one of record.
14. ③-6: Ruling: ③-6 ran on the same go-ahead as ruling 8. It is a Claude-only step. Its test runs wrote nothing into the repository; this file is its only commit. Cost if wrong: none. ③-6 ran only tests, through the wrapper and the cache-free copy.
15. ③-6: Ruling: the result files are named `$S/t6_full.json` (log `$S/t6_full.log`), `$S/t6_nautilus.json` (key unset) and `$S/t6_nautilus_key.json` (key set). The plan's Result-files list has no ③-6 entry, and no earlier file was overwritten. Cost if wrong: none.
16. ③-6: Ruling (finding about Task 4, accepted after the fact): Task 4 did not re-measure its baseline, although X8's third part asks for it.
    - X8's third part: a task re-measures its baseline when a path committed between tasks lies outside `docs/nautilus_bridge/`.
    - 14 of the 16 paths between `321b829` and `185b56c` lie under `docs/audit/2026-10-27/proposed_patches/`: a README and `.diff` files. None is Python, and nothing under `tests/`, `core/` or `tools/` names that folder.
    - Task 4 compared its run with `t1_baseline.json` and recorded "no baseline re-measure was needed".
    - Evidence that no row moved: `t4_after` (`185b56c` plus Task 4's files) and `t6_full` (which carries the same four commits) both equal B row for row outside the 59 bridge rows, with 0 removed and 0 changed. A re-measure at `185b56c` could only have shown a row that those commits moved, and none moved.
    - Cost if wrong: none for the counts. The cost is one 10-minute run that X8 asked for and that was not made.
17. ③-6: Ruling: ③-6's done-when in `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` reads "791/929 PASS, the only FAIL the Windows-only one". That is the 2026-10-26 reference example.
    - The binding criterion is the Count Ledger's: B plus the cumulative deltas, row for row, with B's FAIL set. That is `795/935 passed, 2 failed, 138 not run`.
    - The second FAIL, the m8 dry run, comes from the cache-free copy (X-1), not from the bridge.
    - Cost if wrong: none. The run of record is the owner's Windows run at Steps 7A.2 and 10, where the caches are present.
18. ③-6: Ruling: the file name. The computed task names `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md`, while spec Step 10 names `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md` for the close-out record. This file is the record of Steps 3 to 7. At Step 10 the close-out record either extends this file under the spec's name or cites it. Cost if wrong: one rename.
19. ③-6: Ruling: Tasks 1 to 3 are recorded from their commits, their result files and the scratch artifacts, all checked at ③-6, because their task reports (deviation lists) were not among ③-6's inputs.
    - Checks made:
      - the numstat equals the plan's;
      - the seven new text files of `e83ff6f` are byte-identical to the plan's fences as extracted to `$S/t1_blocks`, among them `tests/nautilus_acceptance.py` `059691438a0adb121c782fb0d3f4dc9b` (696 lines, as ruling T1-R1 states);
      - Task 3's `sandbox.py` equals `$S/t3_blocks/sandbox.py`;
      - `tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml` and `config.py` are still CRLF;
      - every count matches.
    - Task 1's module-CLI counts (`8/12`, `12/12`) were not kept in a result file. Task 1's 12 tests pass in every later `nautilus` run.
    - Cost if wrong: an incidental Task 1 to 3 deviation, such as a write method, is missing from this record. None can change a byte or a count, because those all match the plan.

## Full-run counts per task against the Count Ledger

**How these runs were made.** Every full run went through `bash $S/full_run.sh <name>` with the key unset. The script makes a sparse clone of the real clone, with the four caches skip-worktree and absent, and copies the uncommitted task paths over it. ③-6 recomputed every comparison from the result files with `$S/t6_compare.py`.

**Expected values.** Each comparison is row by row against `$S/t1_baseline.json`. The Count Ledger's cumulative deltas from B (rows/PASS/FAIL/NOT_RUN) are: Task 1 +0; Task 2 +15/+11/+0/+4; Task 3 +20/+13/+0/+7; Task 4 +44/+34/+0/+10; Task 5 +59/+46/+0/+13.

| Run | Result file | Clone of | Counts | Count Ledger | Added (PASS/FAIL/NOT_RUN) | Removed | Changed | `macro` rows | `nautilus` rows (PASS/NOT_RUN) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| B (Task 1 Step 0) | `t1_baseline.json` | `dd1244a` | `749/876 passed, 2 failed, 125 not run` | B | - | - | - | 548 (M) | 0 | - |
| Task 1 Step 16 | `t1_after.json` | `dd1244a` + Task 1 | `749/876 passed, 2 failed, 125 not run` | B, row for row | 0 | 0 | 0 | 548 | 0 | match |
| Task 2 | `nb_task2_full.json` | `e83ff6f` + Task 2 | `760/891 passed, 2 failed, 129 not run` | `760/891, 2, 129` | 15 (11/0/4) | 0 | 0 | 550 | 13 (9/4) | match |
| Task 3 | `task3_full.json` | `76295d0` + Task 3 | `762/896 passed, 2 failed, 132 not run` | `762/896, 2, 132` | 20 (13/0/7) | 0 | 0 | 550 | 18 (11/7) | match |
| Task 4 | `t4_after.json` | `185b56c` + Task 4 | `783/920 passed, 2 failed, 135 not run` | `783/920, 2, 135` | 44 (34/0/10) | 0 | 0 | 550 | 42 (32/10) | match |
| Task 5 | `task5_full.json` | `6b6b386` + Task 5 | `795/935 passed, 2 failed, 138 not run` | `795/935, 2, 138` | 59 (46/0/13) | 0 | 0 | 550 | 57 (44/13) | match |
| ③-6 | `t6_full.json` | `520d0db`, clean tree | `795/935 passed, 2 failed, 138 not run` | `795/935, 2, 138` | 59 (46/0/13) | 0 | 0 | 550 | 57 (44/13) | match |

**What the seven runs share.**
- Rows added outside `nautilus`: exactly `macro/macro_m0_harness/test_t_ro_01_nautilus_allowlist_pinned` and `macro/macro_m0_harness/test_t_ro_01_nautilus_confined_to_the_sandbox`, both PASS, from Task 2 on.
- PASS to FAIL: 0 in every run. The FAIL set is B's in every run.
- The three cache rows are FAIL, NOT_RUN and NOT_RUN in all seven runs, as the Count Ledger says: the m8 dry run, `macro_m3_estimators/test_g_b5_02_spy_refdata_with_smoke_on_local_cache` and `macro_tf_gov/test_cry1_study_runs_offline_end_to_end_on_the_local_caches`.
- The two X-2 rows are NOT_RUN in all seven runs: `macro/macro_m1_calendars/test_cal02_2027_files_signed_before_2026_11_01` and `macro/macro_m1_calendars/test_close02_on_the_real_signed_files`. The deadline 2026-10-31T15:00:00Z had not passed, and no signing commit had landed. So no X-2 exception was needed.

**Comparison bases.** The plan compares Task 3 with `nb_task2_full.json` (+5 rows, 2 PASS, 3 NOT_RUN). The difference between the Task 2 and Task 3 rows above gives the same result.

**Harness module.** `python3 -B -m tests.macro_m0_harness` gives `14/14 passed, 0 failed, 0 not run` at ③-6. That is H = 12 plus Task 2's two T-RO-01 tests.

## The final full run (③-6)

- **Command and time.** `bash $S/full_run.sh t6_full`, key unset, from 2026-10-28T17:23:49Z to 17:34:23Z.
- **The copy.** A clone of `520d0db`. The real clone's `git status --short` was empty, so nothing was overlaid. The four caches were skip-worktree (`4`) and absent (`0`).
- **Result.** `795/935 passed, 2 failed, 138 not run; $S/t6_full.json`. The script exited 1 because the wrapper exits non-zero on any FAIL.
- **The two FAILs.** Both are B's:
  - `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`, `AssertionError: `: the copy has no `yf_SPY.csv` (X-1).
  - `papers/test_debate_run_kills_process_tree`, `FileNotFoundError: [Errno 2] No such file or directory: 'taskkill'`: Linux has no `taskkill`.
- **Against `t1_baseline.json`.** 59 rows added (46 PASS, 13 NOT_RUN): 57 `nautilus` rows and 2 `macro` rows. 0 removed and 0 changed. 550 `macro` rows (M + 2).
- **Against `task5_full.json`.** 0 rows added, removed or changed.
- **Results file.** `md5sum qa/acceptance_results.json` printed `16c9baa5a1777853521d485d5078e456` before and after. The file was never staged.

## The `nautilus` suite (③-6; real clone, through the wrapper)

- **Key unset.** `env -u QUANTGEN_NAUTILUS_PYTHON python3 -B $S/run_baseline.py $S/t6_nautilus.json --suite nautilus` gave `44/57 passed, 0 failed, 13 not run` (59 s). Its 57 rows equal the full run's 57 `nautilus` rows, status for status.
- **Key set.** `QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B $S/run_baseline.py $S/t6_nautilus_key.json --suite nautilus` gave `57/57 passed, 0 failed, 0 not run` (220 s).
- **Count Ledger.** These equal the Task 5 row (`44/57` and `57/57`) and Task 5's own runs (`task5_nautilus.json`, `task5_nautilus_key.json`).
- **Lines kept for the Step 10 record.** They come from the key-set run and are identical to Task 5 Step 10's lines:
  - `L2-7: CARD_WRITTEN; quantgen INSUFFICIENT_DATA, nautilus INSUFFICIENT_DATA; worst corr 0.9999990510795416`
  - `N6: worst corr 0.99999962 (bar 0.9999, map 03 0.99999901); worst abs dSR 0.00058 (bar 0.01, map 03 0.0013); CARD_WRITTEN` (L2-11)
  - `L2-12: CARD_WRITTEN; quantgen INSUFFICIENT_DATA, nautilus INSUFFICIENT_DATA; reference n_years 3 calendar, 2 whole`
  - `N7 (i): P12 2x {'corr': 0.9989206568469223, 'abs_dsr': 0.07763231205006826, 'pass': False, 'owner_pass': False}; P3 at 2x per column, max 0.07667 (bar 0.01)` (L1-2)
  - `80 perturbations refused with exit 20` (L2-5a); `pyarrow in the global interpreter: None` (L1-22)
- **Clean afterwards.** `md5sum qa/acceptance_results.json` was `16c9baa5a1777853521d485d5078e456` before and after each run. `git status --short --untracked-files=all` was empty after each run.

## What stays NOT_RUN, and why (final full run: 138)

**13 `nautilus` layer-2 rows.** Their reason is `OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)`.
- `full_run.sh` unsets the key by design (Count Ledger).
- With the key set, all 13 pass (`57/57` above).
- On the owner's Windows run of record, they must pass with the key set. L2-5b is the only `nautilus/*` NOT_RUN allowed (spec Step 7A done-when).

**125 rows, unchanged from B.** None is caused by the bridge.
- **105 `macro` REFDATA.** Reference files are absent from `tests/fixtures/macro/MANIFEST.csv`, or local vendor caches are absent. Two of these rows exist only because the copy removes the caches (X-1): `test_g_b5_02_spy_refdata_with_smoke_on_local_cache` and `test_cry1_study_runs_offline_end_to_end_on_the_local_caches`.
- **16 `macro` OWNER.** Owner inputs, signatures and attestations. These include the two X-2 rows.
- **1 `macro` PENDING.** `test_sel01_e_card_run_f_vs_acceptance_report_f_after_freeze` waits for the gate freeze.
- **3 `papers` OWNER.** The tectonic binary is absent.

**The X-2 row.** While any of the five PT-07 calendar files is unsigned, `test_cal02_2027_files_signed_before_2026_11_01` turns from NOT_RUN to FAIL (`OVERDUE`) at 2026-10-31T15:00:00Z. Under X-2, a later full run that differs only in that row is still correct when its notes name the cause.

## Spec deviations to carry to Step 10 and the spec's next revision

These are the plan's "Spec deviations to record", plus the items its Stage B rulings add. All of them are implemented as ruled.

- **T1 CI 7.** Rule A of spec 5.6 gives no hit when no order-call node is collected. Under the literal 5.6, a sandbox with no order call would get one A hit.
- **T1 CI 9.** L1-17 tests `%VAR%` on Windows and `$VAR` on POSIX, because `os.path.expandvars` expands per platform (spec 8.3).
- **T2 CI 4.** C1 accepts `newline=""` for a csv writer that uses `lineterminator="\n"`. It writes the same LF bytes as spec 3.7's literal `newline="\n"`.
- **T3 CI 1.** From Task 3 on, an exit 20 writes no file, and its last stderr line is `C-05: <reason>`. Two lines of 5.2.9's `main` change.
- **T5 CI 1.** `parity.corr` counts two constant series that agree within 1e-12 as 1.0. P2's literal Pearson is undefined for a column that never trades when rf is 0.
- **T5 CI 3.** `--fingerprint` prints both digests. It exits 0 only for a table that validates against 6.6. An invalid table gets R-11 and exit 2.
- **T1-R4.** (a) `tests/nautilus_acceptance.py` is created at spec Step 3, although spec 5.8 names Steps 4 to 7. (b) `.env.example` gains a heading, three comment lines and the line, where spec 3.4 says "a heading and one line".
- **T2-m8.** `nautilus_tests()` calls `bridge_tests()` inside its `try`, so a collection failure becomes the single FAIL row `import`.
- **T4-R5 (spec gap).** `_earlier_runs` (R-17) and `e1_parity_passed` read only `<out root>/*/run.json`, never a `run.final.<pid>.json` fallback. When a STATUS line names a fallback, the owner renames it to `run.json` before any re-run or pilot-2 run. Spec 5.3.5 should name the fallback for both readers.
- **X8 (review T4-R7).** `--fingerprint`, `--timing` and `--handoff-report` moved from spec Step 6 to plan Task 5 (spec Step 7). So Task 4's commit holds all of 5.3 except these three modes.

## Hand-off state for Step 7A

**The branch.** HEAD is `520d0db`, pushed, with a clean working tree. `qa/acceptance_results.json` is byte-identical (`16c9baa5a1777853521d485d5078e456`) and was never staged.

**On the branch (spec Steps 3 to 7):**
- `requirements-nautilus.txt` (16 hash-pinned distributions) and the `.env.example` line.
- The launch contract (`tools/nautilus/launch.py`), the sandbox child (`tools/nautilus/sandbox.py`) and the egress probe.
- The runner (`tools/nautilus/runner.py`), with `--check-env`, `--egress-record`, `--fixtures [--write-goldens | --record-baseline]`, `--fingerprint`, `--timing` and `--handoff-report`.
- `tools/nautilus/parity.py`.
- The F1, F2 and N1 goldens and the `manylinux_2_35_x86_64` census baseline.
- The T-RO-01 amendment.
- Both registration tables, without `owner_confirmed` and `host_fingerprint`.
- `docs/nautilus_bridge/RUNBOOK_windows.md`, which pins Python 3.13.14. That python.org serves that installer is UNVERIFIED from the cloud.

**Step 7A outputs not yet made (Windows only):**
- `tools/nautilus/golden/modules_win_amd64.json`
- `docs/nautilus_bridge/egress/win_amd64.json`
- `docs/nautilus_bridge/handoff/win_amd64.json`
- both tables' owner fields
- the Windows `qa/acceptance_results.json`

No line of the 7A.2 PowerShell block has run on Windows (UNVERIFIED until Step 7A). On Linux, Task 5 Step 12 ran `--fingerprint` on both tables and `--timing` (12 runs of 5,600 bars, exit 0).

**Preconditions still open, in order:**
1. **Step 1b.** The GPT and Gemini rounds (the Codex quota resets 2026-10-30 14:40) or a substitute the owner records in Appendix B, and the owner's approval with answers to O1 to O15 (REMAINING_WORK ④-1, ④-2). If a ruling differs from the section 2 defaults, ④-3 adjusts the branch first.
2. **The owner's sign-off sentence (7A.1).** Before recording it, Claude checks that `origin/main` is an ancestor of the branch, and merges it first if main has moved. The T-RO-01 exemption takes effect outside this branch only after this sentence.
3. **Then 7A.2 to 7A.5.** Pilots wait for Claude's 7A.4 review, the owner's 7A.5 pull and ⑤-2 (the vendor comparison).

**The calendar sign-off.** The five PT-07 calendar files (①-2) must be signed before 2026-10-31T15:00:00Z. Otherwise `test_cal02_2027_files_signed_before_2026_11_01` FAILs in every full run from then on, including the owner's 7A.2 suite run, whose done-when requires 0 FAIL. In practice, signing them is a precondition of 7A.2 if 7A.2 runs after that time.

**Expected Linux-only differences on the owner's Windows run.** `papers/test_debate_run_kills_process_tree` FAILs only on Linux (no `taskkill`), and the m8 dry-run FAIL comes only from the cache-free copy.

## Data read by Tasks 1 to 5 and ③-6

- **Bridge work.** Synthetic data and temporary ledgers only, as spec 10.4 requires for Steps 3 to 7.
- **Full runs.** Every full run used a copy without the four protected caches. At ③-6 each of the seven clones showed `0` files present and `4` skip-worktree entries.
- **Real-clone runs.** The `nautilus` suite, the module CLIs and `tests.macro_m0_harness` ran in the real clone. No `nautilus` test opens a cache file: L1-9 names two cache paths and is refused before any open (Count Ledger).
- **Never opened or hashed.** Claude never opened or hashed `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv`.

## Open owner decisions (not decided here)

- **The X-1 disclosure: decided 2026-10-29, include** (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "(가), X-1, ②-5 …"). The Step 10 execution record and its 10.4 data-access history carry the entry under "Data-access history entry (X-1)" below.
- **Step 1b** (O1 to O15 and the approval sentence), and the Strategy Lab side of K-g.
- **①-2:** the calendar signatures, due before 2026-10-31T15:00:00Z.
  - Another Claude session works on ①-2 on `claude/relaxed-cerf-az755o`, from `main`'s calendar audit (option A, PR #5, `0849ca9`). It proposes four v1.0.0 files (without `kr_sessions`) and reads the deadline as `signed_utc` before 2026-11-01T00:00:00Z.
  - This branch carries PT-07 (`d865c7f`): five files, the signing kit `docs/calendar_signoff/SIGNING_KIT_2026-10-28.md`, and a test that reads the spec's "signed off before 2026-11-01" in KST, that is 2026-10-31T15:00:00Z.
  - Both change `core/calendars/data/`, so the owner chooses one implementation before the branches meet at ⑦-2. Signing before 2026-10-31T15:00:00Z satisfies both readings of the deadline.

## Task completions

- Task 1: complete (commits `dd1244a..e83ff6f`; verifier result not among ③-6's inputs; counts match)
- Task 2: complete (commits `e83ff6f..76295d0`; verifier result not among ③-6's inputs; counts match)
- Task 3: complete (commits `76295d0..321b829`; verifier result not among ③-6's inputs; counts match)
- Task 4: complete (commits `185b56c..6b6b386`; the other work streams' commits `32f91e5`, `22bdc16`, `420af64` and `185b56c` lie between `321b829` and it; verifier approve)
- Task 5: complete (commits `6b6b386..520d0db`; verifier approve)
- ③-6: complete. Every count matches the Count Ledger's Task 5 row. There is no PASS to FAIL, the FAIL set is B's, and the X-2 rows are unchanged. This file is its output and its only commit.

## Deferred minor findings (4)

- **REMAINING_WORK, ③-6 row.** `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` still shows ③-6's done-when as the 2026-10-26 reference numbers (791/929). The binding numbers are `795/935 passed, 2 failed, 138 not run`, with B's FAIL set (ruling 17). This is documentation only.
- **The plan's Task 1 Step 0 heredoc** still shows the plain-clone `full_run.sh`. T5-1 governs, and the script in use differs from that text (ruling 1). The plan's next revision should print the sparse script.
- **The plan's Result-files list** names no ③-6 files (ruling 15), and X8's third part has no Task 4 Step 1 text to apply it (ruling 16). Both are plan wording only.
- **Exit code.** `full_run.sh` exits 1 on every correct run while B has its two FAILs. A reader must check the counts, not the exit code. This is cosmetic.
## After ③-6: `main` merged into the branch (`614dca4`, 2026-10-29)

PR #4 (this branch into `main`) showed conflicts after PR #7 merged into `main` at 2026-10-28T17:54:58Z. PR #7 carries the owner-signed calendars: `holidays_KRX`, `holidays_NYSE`, `holidays_FED` and `holidays_SIFMA` v1.0.0 signed by Geon Koh at 2026-10-28T06:35:52Z (`3917bc0`), then `kr_sessions` and the rest of the KR and US sets. The owner asked Claude to decide by the two latest T-CAL-02 sessions (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "PR #4 충돌 해결").

- **Decision.** `main`'s signed calendars win, byte for byte. `core/calendars/data/`, `core/calendars/store.py`, `core/calendars/publication.py`, `data/calendars/KRX.json`, `data/calendars/index.json` and the three calendar test modules now equal `origin/main`. This withdraws PT-07 (`d865c7f`, unsigned). Its `store.py` would have refused the signed files, because they carry no `sign_off_statement` and no MANIFEST `signed_utc`. `tests/macro_registry.csv` is `main`'s file plus this branch's T-RO-01 row. `docs/calendar_signoff/SIGNING_KIT_2026-10-28.md` is marked superseded.
- **Bridge files.** No file under `tools/nautilus/`, `tests/nautilus_acceptance.py`, `tests/fixtures/nautilus/` or `requirements-nautilus.txt` changed in the merge.
- **Full run after the merge.** `bash $S/full_run.sh m1_full` on a clone of `614dca4`, key unset, started 2026-10-28T18:07:48Z: `792/931 passed, 2 failed, 137 not run`.
  - The four caches were skip-worktree (`4`) and absent.
  - The FAIL set is B's two rows.
  - PASS to FAIL: 0.
- **Against `t6_full.json`.**
  - All differences are `macro_m1_calendars` and `macro_m1_integration` rows.
  - 8 PT-07 rows removed (7 PASS, 1 NOT_RUN).
  - 4 `main` rows added (3 PASS, 1 NOT_RUN): `test_cal01_owner_sign_tool_on_a_copy`, `test_cal01_shipped_drafts_are_refused_and_acting_inputs_fail_closed`, `test_close02_on_the_real_signed_files_is_owner_input` (NOT_RUN) and `test_release_calendar_supplies_bls_bea_release_dates`.
  - 1 row changed: `test_cal02_2027_files_signed_before_2026_11_01` NOT_RUN to PASS (the files are signed).
  - So 935 − 8 + 4 = 931 rows and 795 − 7 + 3 + 1 = 792 PASS.
  - The 57 `nautilus` rows are unchanged (44 PASS, 13 NOT_RUN). The 14 `macro_m0_harness` rows pass. There are 546 `macro` rows.
- **What this changes above.**
  - The X-2 clock and sign-off rows are settled: `test_cal02` passes, and the deadline no longer threatens Step 7A.2's 0-FAIL done-when.
  - The calendar precondition under "Hand-off state for Step 7A" and the ①-2 item under "Open owner decisions" are closed.
  - The bridge's Count Ledger deltas still hold against the new baseline: every bridge row is unchanged.
- **Results file.** `qa/acceptance_results.json` stayed `16c9baa5a1777853521d485d5078e456`.

## Second `main` merge (`0acb9b7`, 2026-10-29): PR #9, every calendar file and the set signed

PR #9 merged into `main` at `e28035f`. It brings calendar audits 5 and 6 (`d4e9a42`, `f8c7467`) and the set signature 1.0.0 (`999dd26`): all 17 calendar files and the set are signed by Geon Koh.

- **Merge.** Only `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` conflicted. Both sides appended, so both were kept. `core/calendars/` and the calendar tests come from `main` unchanged. No bridge file changed.
- **Full run.** `bash $S/full_run.sh m2_full` on a clone of `0acb9b7`, key unset, started 2026-10-29T04:37:48Z: `790/931 passed, 4 failed, 137 not run`.
  - The four caches were skip-worktree (`4`).
  - Against `m1_full`, 0 rows were added or removed and 2 changed (PASS to FAIL):
    - `macro/macro_ui_overlay/test_every_owner_decision_d1_to_d6_is_listed_with_value_and_status`
    - `macro/macro_ui_overlay/test_view_selector_hosts_the_overlay_view_and_reads_nothing_into_home`
  - The 57 `nautilus` rows are unchanged (44 PASS, 13 NOT_RUN). The 14 `macro_m0_harness` rows pass.
  - `qa/acceptance_results.json` stayed `16c9baa5a1777853521d485d5078e456`.
- **The two new FAILs are `main`'s, not the bridge's.** Both fail the same way on a clean sparse clone of `main` at `e28035f` and at `f8c7467` (14/16).
  - The tests assert the unsigned state: a "Sign the calendar set" owner input, and "signed calendars" in the Live option's tooltip.
  - With all 17 files signed, `ui/macro_state_panel.py` correctly drops both.
  - A test-only fix that makes both assertions follow `core.calendars.store.describe()` passes 16/16 on `e28035f`. It is proposed to the owner and to the calendar session, and is not applied here, so the bridge PR does not widen.
  - The line `No event_calendar artifact yet (the calendar set is unsigned).` at `ui/macro_state_panel.py:501` is now stale wording. It is noted, not changed.

## Data-access history entry (X-1), for the Step 10 record and spec 10.4

The owner ruled on 2026-10-29 that this goes into the record ("1. X-1 공개 여부 포함").

- **What happened.** On 2026-10-26, before this plan, two cloud full-suite baseline runs ran in the real clone through the wrapper (`docs/audit/2026-10-27/artifacts/run_all_cloud_run1.log`, `run_all_cloud_run2.log`). Three existing `macro` tests opened protected caches while they ran:
  - `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`: `yf_SPY.csv`
  - `macro/macro_m3_estimators/test_g_b5_02_spy_refdata_with_smoke_on_local_cache`: `yf_SPY.csv`
  - `macro/macro_tf_gov/test_cry1_study_runs_offline_end_to_end_on_the_local_caches`: `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv`
- **What Claude saw.** Test names, PASS/FAIL statuses and counts only. No price value appears in either log. Run 1's dry-run failure detail is an empty `AssertionError`.
- **Rule affected.** Spec section 9, row 2 ("Claude reads no real BTC price and no SPY row on or after 2004-12-01"; "never opens or hashes ..."). The test processes opened the files.
- **Since then.** Every full run of this plan used a sparse clone where the four caches are skip-worktree and absent (X-1, T5-1): seven runs through ③-6 and three after the `main` merges. No bridge test opens a cache file.
- **Pilot relevance.** Pilot 1 (SPY) and pilot 2 (BTC-USD) are registered on these series. Claude's view was limited to statuses, so no design choice used their values. This entry exists so a reader of the pilot results can weigh that.
- **Later event (2026-10-29, about 05:50 UTC).** While reviewing the Bonds patch (②-5/b), a Claude sub-agent's first recursive `grep` (`--include='*.csv'`) did not exclude `docs/asset_expansion/cache/`, so the four protected caches were opened by grep. Nothing matched, nothing was printed and nothing was hashed; later searches excluded the folder (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "Claude 자진 보고 (2026-10-29)"). No value from the files reached Claude.

## Third `main` merge (`468d0fb`, 2026-10-29): PR #10, overlay tests fixed

PR #10 (`950f25e`) put the test-only fix into `main`, together with one stale UI line (`ui/macro_state_panel.py:501`). It was proposed in the section above and committed by the calendar session as `ace8f3b`.

- **Merge.** Clean merge into this branch at `468d0fb`.
- **Full run.** `bash $S/full_run.sh m3_full`, key unset, started 2026-10-29T05:34:28Z: `792/931 passed, 2 failed, 137 not run`.
  - Against `m2_full`, the two `macro_ui_overlay` rows went from FAIL to PASS, with nothing else changed.
  - The FAIL set is B's two rows. The 57 `nautilus` rows are unchanged.
  - `qa/acceptance_results.json` stayed `16c9baa5a1777853521d485d5078e456`.



## 2026-10-30 O8 follow-up applied (documentation; prior test history retained)

The initial Step 1b pending-review statements above describe their historical date. The owner subsequently
made additional GPT/Gemini review optional, with both NOT_PERFORMED and the waiver in Appendix B.
Missing optional reports alone no longer block Windows hand-off. Existing Claude review evidence and all
technical/Windows acceptance conditions remain. Ordinary approved fixes/tests need no repeated general
approval. Research verdict changes, formal ledger execution and external publication keep separate approval;
actual execution still needs current code/table-bound owner_confirmed after validation.

The O11 A2 implementation remains register_e1.py; no second initializer was added. This update does not
claim real Windows registration, engine integration, full-suite rerun, actual pilot or research-main merge.
Only disposable-ledger regression is run for the documentation integration; consult its exact commit's CI.
