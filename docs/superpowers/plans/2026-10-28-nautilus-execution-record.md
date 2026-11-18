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

## Step 10 close-out (2026-11-17)

Written by Claude in session_01H6RrzMUzF8vwK8xkX977mB, the main session (handoff task `claude-resume-20261103`). The
owner's ruling P2 of 2026-11-11 lets "이 세션" commit the Step 10 close-out record, the spec, `README.md` and
`docs/nautilus_bridge/runs/` on this branch (section 7, row 34), and decision 10 lets it push those closing commits.
The P2 section of the rulings log names no session id (`log-main:697-760`). That this is the session P2 names rests
on two commits made one second apart minutes after the owner's answer (07:1x KST, `log-main:746`): `45af437`
(2026-11-11 07:20:26 KST), the commit that wrote the answer into the rulings log (merged into `main` by PR #103,
`83046c1`), carries the trailer
`Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB`, and handoff commit `ede270e` (07:20:27
KST), the checkpoint published with it, names the task `claude-resume-20261103` and this session (its `CURRENT.md:5`,
`:19`) and records "**P2:** 이 세션이 연구 브랜치에 커밋 가능" (its `CURRENT.md:115`). That the session which asked P2
is the one that recorded the answer is inferred from these two commits; the log does not say it. The session told the
owner the same on 2026-11-17 (`report-1117:8`: "연구 브랜치 마감(Step 10)은 판정 P2·결정 10대로 이 메인 세션이
합니다"). The text was drafted by sub-agents of that session in a scratch clone of `cdbbe61` that never checked out
`docs/asset_expansion/cache/`.

This section and the ones after it are the close-out record that spec Step 10 names
`docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md`. It extends this file and keeps this file's
name. Ruling 18 above left two ways open, a rename to the spec's name or a new file that cites this one; the owner chose
on 2026-11-11 to keep the name and extend the file (decision 15 of `docs/product/DECISIONS_PILOT_CLOSE_MERGE_2026-11-11.md`
on main, answered "전부승인합노."; section 7, row 36). Everything here was read from pushed files with git, except these facts
of a helper's two walks of the protected folder on 2026-11-11 (section 9): who ran them and where, their times, commands
and output, and the helper's own words. They come from the main session's conversation records and are not verified from
git. Nothing was run on real data in the cloud, and no test was run for this close-out.

Source keys used below (line numbers as read on 2026-11-17):
- `spec`: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` at `8a8c247`, unchanged at `cdbbe61`, before
  this close-out's edits. In the spec as this close-out leaves it, lines 6 to 1706 are 41 lines further down and later
  lines 60 further down.
- `record`: this file at `cdbbe61` (lines 1 to 327, before this section).
- `log-rb`: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` at `cdbbe61`. `log-main`: the same file on `main` at `e01e152`.
- `rulings-main`: `results/RULINGS.md` on `main` at `e01e152`. `rulings-pp`: the same file on the run branch
  `claude/provider-parity-runs-20261111` at `77d2647`; its 251 lines are byte-identical to lines 1 to 251 of
  `rulings-main`, which adds the entry of 2026-11-13 (lines 254 to 307).
- `table`: `docs/product/DECISIONS_PILOT_CLOSE_MERGE_2026-11-11.md` on `main` at `e01e152` (row n is decision n).
- `prep`: `docs/product/PILOT_READOUT_AND_STEP10_PREP_2026-11-11.md` on `main` at `e01e152`.
- `run1`, `run2`: `docs/nautilus_bridge/runs/NB-20261112T153028389916Z-d76d2d73/run.json` at `a2ac79b` and
  `docs/nautilus_bridge/runs/NB-20261113T122642089406Z-e2ec073c/run.json` at `8a3d171` (unchanged at `cdbbe61`).
- `acc`: `qa/acceptance_results.json` at `cdbbe61`. `acc-7a`: the same file at `563db54`.
- `gpt-p1`, `gpt-p2`, `gpt-e`, `gpt-review`: GPT's readouts on the `handoff` branch at `212f68e`:
  `PILOT1_READOUT_2026-11-13_gpt.md`, `PILOT2_READOUT_2026-11-13_gpt.md`, `WINDOWS_E_READOUT_2026-11-14_gpt.md`,
  `STEP10_CHANGE_REVIEW_2026-11-14_gpt.md`. `ledger`: `LEDGER.md` on the same branch and commit.
- `report-1117`: the main session's report to the owner of 2026-11-17, `plans/2026-11-17/OWNER_REPORT_2026-11-17.md` on
  the `handoff` branch (added by handoff commit `8a66956`, unchanged at `212f68e`); decision rows D1 to D14 at its lines
  18 to 31. `answer-1117`: the owner's answer to it (2026-11-17, about 19:57 KST), verbatim in `CURRENT.md` on the
  same branch at `212f68e` (the commit that added it), lines 26 to 42; the main session's reading of it is line 44.
  Handoff `CURRENT.md` lines cited elsewhere are also at `212f68e` unless another commit is named.

### 1. Commits on this branch that this file does not name yet

In first-parent order (`git log --first-parent e089e59..cdbbe61`; `e089e59` of 2026-10-30 is the last commit that
changed this file before this close-out), with the earlier commits that this file never names. "Author" is the author
name git shows. File lists are `git diff --name-only <first parent> <commit>`, with the protected cache folder excluded
from the pathspec.

Commits that wrote this file but are not named in it: `57c6344` (③-6), `abc7217`, `45b233f`, `cad341c` (the X-1 entry),
`4709cf2` (row below) and `e089e59` (the O8 section).

| What | Commit | Author | Files |
|---|---|---|---|
| Entries of this file for the main merge after ③-6 (`614dca4`) and the second main merge (`0acb9b7`); earlier than `e089e59` | `abc7217`, `45b233f` | Claude | this file |
| Owner rulings of 2026-10-29, the X-1 entry, the third main merge verified; earlier than `e089e59` | `cad341c` | Claude | the rulings log, this file |
| Bonds screen patch (②-5/b); earlier than `e089e59` | `4709cf2` | Claude | `README.md`, `core/ficc/bonds.py`, `core/ficc/curves.py`, `core/ficc/data.py`, `core/ficc/insights.py`, the rulings log, this file, `tests/bonds_screen_acceptance.py`, `tests/run_all.py`, `ui/bonds_page.py`, `ui/qcharts.py` |
| Hand-off at 95 % usage (manual, decision form, explainer, drafts); earlier than `e089e59` | `0a91f26` | Claude | five documents under `docs/audit/2026-10-29/`, `docs/nautilus_bridge/` and `docs/superpowers/specs/`; no code |
| Sanitized session log for the next agent; earlier than `e089e59` | `2da6469` | Claude | `docs/nautilus_bridge/session_logs/CLAUDE_MAIN_SESSION_LOG_2026-10-26_to_10-29.md` |
| O11 A2 registration tool (on the second-parent side of `0510719`) | `d7b175f` | xkg4real | `.github/workflows/nautilus-registration.yml`, `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, the rulings log, the runbook, the spec, `tests/nautilus_registration_acceptance.py`, `tools/nautilus/register_e1.py` |
| O8 optional review applied (on the second-parent side of `0510719`) | `e089e59` | xkg4real | the workflow above, `O11_A2_REGISTRATION.md`, `O2_O15_DECISION_FORM_2026-10-29.md`, the rulings log, `REMAINING_WORK_2026-10-27.md`, the runbook, this file, the spec |
| O8 waiver test (second parent of `0510719`) | `36df786` | xkg4real | `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, `tests/nautilus_registration_acceptance.py` |
| Merge of pull request #21 (the three commits above) | `0510719` | xkg4real | against its first parent `2da6469`: the ten files of the three commits above (760 insertions, 61 deletions) |
| Merge of main `7fc53e2` for Step 7A.1 (⑤-1/a) | `92cc00f` | Claude | conflicts: `core/ficc/bonds.py` (main's BS-21 funding and the branch's RP-01 hold-to-maturity rule both kept), the rulings log (both sides in date order); semantic fixes without a conflict: `tests/bonds_screen_acceptance.py`, `tests/bond_funding_acceptance.py`; `qa/research_status.json` regenerated; `qa/acceptance_results.json` byte-identical (merge message) |
| L1-15 encoding fixes; committed tables may carry the owner fields (⑤-1/a) | `85d2e51` | Claude | `tests/nautilus_acceptance.py`, `tests/nautilus_registration_acceptance.py`, `tools/nautilus/register_e1.py` (inside `code_sha256`) |
| O11 A2 placed inside Step 7A.2; its receipt kept out of git (⑤-1/a) | `611c718` | Claude | `docs/nautilus_bridge/.gitignore`, `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, the runbook, the spec |
| Merge of main `bb35b3b`, the start of the merge freeze (⑤-1/a) | `c95b3aa` | Claude | no conflict; brings PR #69 (two macro UI tests, their compliance fingerprints, the freeze record); `qa/acceptance_results.json` byte-identical (merge message) |
| Step 7A prep: review follow-ups (⑤-1/a) | `2c299c9` | Claude | `core/ficc/bonds.py`, `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, the runbook, the spec, `quantgen_desktop/bonds.py`, `quantgen_desktop/bonds_portfolio_narrative.py`, `tests/bond_funding_acceptance.py`, `tests/desktop_bonds_portfolio_language_acceptance.py` |
| Step 7A.1 owner sign-off recorded verbatim (⑤-1/a) | `0bc9595` | Claude | the rulings log, the spec |
| Step 7A hand-off reports | `fe37e82`, `e3c61cb`, `9d8d9c6` | unknown (the owner's machine) | `docs/nautilus_bridge/handoff/win_amd64.json` |
| Step 7A re-entry fixes (⑤-1/b) | `e07da98` | Claude | `tests/macro_m8_pipeline.py`, `tests/nautilus_acceptance.py` |
| Step 7A records and both tables' owner fields | `563db54` | unknown (the owner's machine) | `docs/nautilus_bridge/egress/win_amd64.json`, both tables, `qa/acceptance_results.json`, `tools/nautilus/golden/modules_win_amd64.json` |
| Step 7A.4 review (⑤-1/c) | `83ee469` | Claude | the spec |
| Spec 10.5 (P-D3) | `8a8c247` | Claude | the spec |
| Pilot 1 run folder (2026-11-13 00:34:21 KST) | `a2ac79b` | unknown (the owner's machine) | `docs/nautilus_bridge/runs/NB-20261112T153028389916Z-d76d2d73/` (`run.json`, `NB_E1_trend_spy.json`) |
| Pilot 2 run folder (2026-11-13 21:31:47 KST) | `8a3d171` | unknown (the owner's machine) | `docs/nautilus_bridge/runs/NB-20261113T122642089406Z-e2ec073c/` (`run.json`, `NB_C3_crypto_trend_btcusd.json`) |
| Step 10 Windows full run (2026-11-14 01:13:32 KST) | `cdbbe61` | unknown (the owner's machine) | `qa/acceptance_results.json` |
| This close-out | not committed when this text was written | Claude | this file, the spec, `README.md`, `docs/nautilus_bridge/runs/PP-*/` |

No further pilot folder exists: `docs/nautilus_bridge/runs/` at `cdbbe61` holds the two `NB-` folders above and nothing
else, so no re-run and no exit-3, 4, 5 or `IN_PROGRESS` folder was committed (decision 5), and both records show
`earlier_runs` empty and `supersedes` null (`run1`, `run2`). No re-anchor commit was made.

### 2. Step 7A on Windows (2026-11-04), as recorded

- Full run at `563db54`: 844/964 passed, 0 failed, 120 not run; `nautilus` 57 PASS; `guard` 5 PASS (`spec:2101-2105`;
  recounted from `acc-7a` on 2026-11-17).
- `code_sha256` `f995600b36c75523fe6079ab5209e60d94c2b5d0ac44437673fe4bc71c055620`; `table_sha256`
  `d76d2d7301ffe92ca5198404ba1cbe07fd11890489c227e20cced8c4c4e07347` (E1) and
  `e2ec073c309cbfc75ff476c03dda96337c45b46ce3f18129df96fb4d74462aba` (C3). Both pilot records carry these values
  (`run1`, `run2`, `table.code_sha256` and `table.table_sha256`), and `git diff --name-only 563db54 cdbbe61` over the
  `code_sha256` inputs (`tools/nautilus/runner.py:183-190`) and over `docs/nautilus_bridge/registration` prints nothing.
- Timing from the hand-off report: engine import 1.94 s (`import_us` 1,936,529); 12 synthetic runs of 5,600 bars
  35.1 s (`spec:2097-2098`).
- O11 A2 registration: owner-reported, the receipt is private (`spec:2140-2143`). Pilot 1's record shows the 12 E1 rows
  already present: `registration.n_raw_before` 12, `n_raw_after` 12, `hash_before` equal to `hash_after`
  (`run1:11100-11105`).
- What the 7A.4 review left to the 7A.5 HEAD (`spec:2144-2147`), `repo_anchor()` and an empty `git status --porcelain`,
  each pilot record shows for its own HEAD: `git.clean` true, `offending` empty, `anchor_problem` null, `anchor`
  `git:<head>` (`run1:8262-8266`, `run2:18342-18346`).
- One 7A.4 value did not hold at pilot 2: `check_env` reported Python 3.13.14 at 7A.4 (`spec:2086`), 3.13.14 at pilot 1
  (`run1:7984`) and 3.13.17 at pilot 2 (`run2:18090`). See section 5 and section 8.

### 3. Provider parity (5-2, spec 10.5)

- Tool: `tools/provider_parity/parity_check.py`, first fixed version: commit `5202482e3c24de871b8483608b8a03beb07abe1e`,
  sha256 `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`, fixed by the owner's ruling P1
  (`rulings-main:26-30`). The three runs of record of 2026-11-11 used it: each of their summaries has this
  `tool.sha256`.
- Second fixed version, by the ruling SPY-가 (only the fmp fetch changed): commit
  `1be43ec191ce73bc4fbc7357a4b3438aca0e4bb1`, sha256
  `78dd1f508c713f9be138466bf69f5dd92d8bfdcc3afacfa37b21fc4bf28ca80c` (`rulings-main:91-92`, `log-main:876-878`).
  The second SPY run's summary has this `tool.sha256`.
- Where it lives (owner decision D4 of 2026-11-17: the current location, commit and sha256 go into the Status block and
  this record; 10.5's Tool bullet stays as written): on `main` (first version through PR #102, merge commit
  `9fc38175c79549b9cb2082193051832ab1d06f07`; second version through PR #105, merge commit `b97646d`) and on the run
  branch `claude/provider-parity-runs-20261111`, which was cut from `main` and holds the fixed commit
  (`rulings-main:36`). On 2026-11-17 the file on `main` (`e01e152`) has sha256 `78dd1f50…a80c`, and both `5202482` and
  `1be43ec` are ancestors of `main` (`e01e152`) and of the run branch as read for this record (`77d2647`)
  (`git merge-base --is-ancestor`). Spec 10.5 names `claude/provider-parity-5-2`; that branch holds the unfinished tool
  of 2026-11-05 and was not used (`prep:1256`; the branch itself was not read for this record).
- The BTC-USD diagnostic of ruling BTC-나: `tools/provider_parity/btc_diagnose.py`, sha256
  `1e44f3a791dd8c13a667bf46cda2933c7bb0810ac6f7bcaae884a16cc71bc6ea` (`rulings-main:171-172`; the file on `main`
  `e01e152` has that sha256).

Both SPY summaries are copied, and the record says which one the gate used (decision 18). Each copy is
`git show 77d2647:results/<run_id>/summary.json > docs/nautilus_bridge/runs/<run_id>/provider_parity_summary.json`; the
sha256 of the source blob and of the copy are equal, and so are their git blob ids.

| Series | Run (`run_id`) | Outcome | `tool.sha256` (which fixed version) | Used by the gate | sha256 of the summary | Copied to |
|---|---|---|---|---|---|---|
| SPY | `PP-20261111T051909Z-spy`, the run of record (the first) | WITHHELD | first, `f2fe72cd…`: yes | no: kept as the first run; the gate used the second run (ruling SPY-가) | `ca2f82c217f70505edb9e475e802ede17792895dd632fa248985f8b36a2dc665` | `docs/nautilus_bridge/runs/PP-20261111T051909Z-spy/provider_parity_summary.json` |
| SPY | `PP-20261112T073747Z-spy`, the second run, counted by ruling SPY-가 | PASS | second, `78dd1f50…`: yes | yes (pilot 1) | `4ad6c537fa5649a2f5d0ba069fd88a0d8e1a4398ca23308defcc017b118b3c02` | `docs/nautilus_bridge/runs/PP-20261112T073747Z-spy/provider_parity_summary.json` |
| DGS3MO | `PP-20261111T075307Z-rf` | PASS | first: yes | yes (pilot 1) | `e6fa0e73138cda68382f8b3a51ce1803dee7b46bfc2f202a0c418710845c9577` | `docs/nautilus_bridge/runs/PP-20261111T075307Z-rf/provider_parity_summary.json` |
| BTC-USD | `PP-20261111T075328Z-btc` | FAIL | first: yes | yes (the only BTC-USD run; pilot 2 went ahead by ruling BTC-라, "Gate" below) | `622894fdc50f2c902f45f146db17f8858e44ca7e53c23a5f82efbfad0268dc93` | `docs/nautilus_bridge/runs/PP-20261111T075328Z-btc/provider_parity_summary.json` |

The run ids and outcomes of 2026-11-11 are those of `log-main:776-785` and `rulings-main:51-55`, and they match the
pushed summaries. The four sha256 values equal those in GPT's review (`gpt-review:36-39`). Each summary's `pinned.md5_ok`
is true and its window is the table's (SPY and DGS3MO 2004-12-01 to 2026-09-25, BTC-USD 2014-09-17 to 2026-09-25).

- Providers not compared, with the reason: DGS3MO `h15` (optional), "h15 not compared: fetch_failed" (its
  `withheld_reasons`). The first SPY run: "no independent or cross pair was evaluated in full" (`fmp` and `kis` WITHHELD
  on coverage). The second SPY run: `kis` (cross) WITHHELD on coverage; `fmp` (independent) PASS on 5,489 common days
  with 0 above tolerance; `yahoo_now` PASS (`log-main:1084-1088`). BTC-USD: `binance` (diagnostic) WITHHELD on coverage.
- Warnings: DGS3MO `treasury` pair WARN on its `blanks` check (on 3 dates the pinned file has a value and treasury has
  none; `rulings-main:54`). No summary has any other non-PASS check than those named here.
- Later runs and whether they count: `PP-20261112T073747Z-spy` counts for the pilot-1 gate by ruling SPY-가
  (`rulings-main:108-109`); no other later run exists.
- Owner rulings from `results/RULINGS.md` (P-D9), verbatim, each with date (KST), series and `run_id`:
  - 2026-11-11, all series, before any run (P1): "1번으로 승인하겠노" (`rulings-main:26`).
  - 2026-11-11 (17:1x KST), SPY `PP-20261111T051909Z-spy` and BTC-USD `PP-20261111T075328Z-btc` (SPY-가, BTC-나):
    "SPY-가-승인, BTC-나-승인" and "그리고 BTC-나 에 따라 문제의 원인 파악 완료 후 자동으로 해결 및 pilot 2
    진행해주세요" (`rulings-main:77-78`, `rulings-main:162-163`; `log-main:809-810`).
  - 2026-11-13, BTC-USD `PP-20261111T075328Z-btc` (BTC-라): "그러면 라 옵션으로 가겠습니다" (`rulings-main:290`,
    `log-main:1113`). This entry was added by commit `a90c90b` and edited by `661c6b8` (author xkg4real, GPT's record;
    the edit left the quoted line as it was) and reached `main` with the merge `795165c` (PR #114; handoff ledger row
    ⑤-2/e/2). It is not in `rulings-pp`: the run branch's copy of `results/RULINGS.md` ends at the BTC-나 entry.
- BTC-USD diagnostic (ruling BTC-나), as recorded: both 20, coinbase_only 9, bitstamp_only 9, coinbase_edge 14,
  bitstamp_edge 12, coinbase_unpaired 0, bitstamp_unpaired 6; venues agree 20, differ 0 (`log-main:1103-1104`;
  `ledger` row ⑤-2/e). Under the reading rule written before the output (`rulings-main:197-237`), case 3 fails
  (43 − 9 = 34 > 20; 47 − 9 = 38 > 21) and case 4 fails (20 is not above both allowances), so it is case 5: the cause is
  not identified, and BTC-나 did not open the gate (`log-main:1105-1107`). The per-year numbers stayed in the chat
  (`ledger` row ⑤-2/e); this record does not hold them and they were not read for it.
- Gate: Step 8 started on 2026-11-12 (`run1` `started_utc` 15:30:28Z) with SPY PASS (the second run, by ruling SPY-가)
  and DGS3MO PASS. Step 9 started on 2026-11-13 (`run2` `started_utc` 12:26:42Z) with BTC-USD FAIL, passed by the owner's
  ruling BTC-라 of 2026-11-13, which lets pilot 2 go ahead with the disagreement noted here and in 10.4 (spec 10.5, Gate;
  `log-main:1115-1118`). The provider comparison itself stays FAIL, and its cause is not identified.

### 4. Pilot 1 (Step 8): E1-SPY

- Run: `NB-20261112T153028389916Z-d76d2d73`, `git.head` `8a8c2475b1a1480c7c6596a9d89619c755ab1e2a`, started
  2026-11-12T15:30:28.389360Z, finished 15:31:56.444006Z (`run1:11663-11666`), status `CARD_WRITTEN` (`run1:11183`),
  exit 0 (the owner's console line, `ledger` row ⑥-1; the exit code is not in `run.json`).
- Registration: 12 rows, 0 appended, 12 already present; E1 `n_raw` 12 to 12; `market_n_raw` 12 (`run1:11103-11105`).
- Children: 24, 24 valid (return code 0, none invalid or timed out, each echoes the post-registration ledger hash);
  59.8 s in total over the children.
- Parity: `hard_pass` true (`run1:8574`); worst corr 0.9999996240319662 (bar 0.9999); worst abs dSR
  0.0006384421130428697 (bar 0.01); P12 1x corr 0.9999999676773109, abs dSR 0.00011391013522676907; 2x corr
  0.9999997387778333, abs dSR 0.0005575618474775168 (`run1:8546`); P1 exemptions 0; warnings 0; `failed` empty. P11:
  the engines' independent choices differ at 2 of 38 origins (1764 and 2646), a diagnostic that is not a hard check.
- Trial counts: `len_grid` 12, `family_n_raw` 12, `market_n_raw` 12, `U` 24, `n_trials` 36 (`run1:8228-8232`).
- Decisions: quantgen REJECT, nautilus REJECT (`run1:8074`, `run1:8004`); `agree.ok` true (`run1:7999`). Both reasons:
  "does not beat its benchmark (Sharpe difference -0.15, p 0.81)". On both sides the predicates `bench_ok` and
  `sample_ok` (the soft trade count) are false and `floor_ok` is true with 31 OOS trades; `pbo_reject` is false, so PBO
  did not reject.
- Card: `NB_E1_trend_spy.json`, md5 `dd4e580addeea60359cdd0442f1e9932` (`run1:4`; the committed file has that md5),
  sha256 `56301f4f60e3bff3f6de3e12605825ed3b8784d931141cc760f49515558b428c`; decision REJECT; reason "does not beat its
  benchmark (Sharpe difference -0.15, p 0.81)".
- Against spec 10.3 (expected INSUFFICIENT_DATA, else REJECT; `spec:1672-1680`): as expected. The trade floor held, so
  the gate went on to the benchmark test and returned REJECT (`core/quant/validate.py:586-598`). This is a finding about
  the rule on SPY alone, not a bridge failure.
- Withheld reasons: none.
- Re-runs: none. Card of record: `NB-20261112T153028389916Z-d76d2d73`, the only `CARD_WRITTEN` record (spec 5.3.5).
- Against the synthetic margins kept for this record (`record:148-153`): N6's worst corr 0.99999962 and worst abs dSR
  0.00058 on synthetic data (`record:150`); pilot 1's 0.9999996240 and 0.00064 on real data. L2-7, the synthetic E1
  run, ended `CARD_WRITTEN` with INSUFFICIENT_DATA on both engines and worst corr 0.9999990510795416 (`record:149`);
  pilot 1 ended `CARD_WRITTEN` with REJECT on both engines and worst corr 0.9999996240319662.
- Read by GPT on 2026-11-13 (`gpt-p1:7-47`, 24 checklist items, all as above) and checked again from git for this record.

### 5. Pilot 2 (Step 9): C3-BTCUSD

- Run: `NB-20261113T122642089406Z-e2ec073c`, `git.head` `a2ac79b04bf2e31055c7bc486cb9cffb3727f2c4`, started
  2026-11-13T12:26:42.088872Z, finished 12:27:32.101745Z (`run2:22721-22724`), status `CARD_WRITTEN` (`run2:22537`),
  exit 0 (the owner's console, `gpt-p2:17`; not in `run.json`).
- Registration: 5 rows, 5 appended; C3 `n_raw` 17 to 22; `market_n_raw` 8 (`run2:22499-22501`).
- Children: 10, 10 valid (return code 0, none invalid or timed out, each echoes the post-registration ledger hash);
  26.2 s in total over the children.
- Parity: `hard_pass` true (`run2:18591`); worst corr 0.999999903862484; worst abs dSR 0.00027736487978979874; P12 1x
  corr 0.9999999907772481, abs dSR 4.1827024417129266e-05; 2x corr 0.9999999629645056, abs dSR 0.0001076051918691423
  (`run2:18563`); P1 exemptions 0; warnings 0; `failed` empty. P11: the independent choices agree at all 29 origins.
- Trial counts: `len_grid` 5, `family_n_raw` 22, `market_n_raw` 8, `U` 11, `n_trials` 33 (`run2:18321-18325`).
- Reference (G-08): drift empty; `n_years_calendar` 11, `n_years_whole` 9 (`run2:18251-18253`).
- PBO, for information only (5 configurations): `pbo` 0.19090909090909092 (QUANTGEN) and 0.19044289044289045
  (Nautilus), `prob_loss_oos` 0.0 on both (`run2:18228-18231`, `run2:18158-18161`), `pbo_meaningful` false.
- Decisions: quantgen PASS, nautilus PASS (`run2:18180`, `run2:18110`); `agree.ok` true (`run2:18105`); reason "every
  gate criterion met". Card: `NB_C3_crypto_trend_btcusd.json`, md5 `9eeacef79dc4f0d54c68622bc49bb6c0` (`run2:4`; the
  committed file has that md5), sha256 `7a697fce504c8fc262c4aede8b53e9c08ec1a65d07baa9fb9ece745b956c4718`.
- Against spec 10.3 (expected PASS; `spec:1682-1689`): as expected. The stored card says SR 1.19 [0.72, 1.64], 144
  trades, benchmark p 0.07; this run's Nautilus side has OOS Sharpe 1.1869744675362457, 144 trades and benchmark p
  0.07, with DSR 0.99996 at `n_trials` 33. It is an engine replication of the stored card on the same file and settings,
  not new evidence about the rule, and it says nothing about the accuracy of the BTC-USD file (section 3, BTC-라).
- Re-runs: none. Card of record: `NB-20261113T122642089406Z-e2ec073c`, the only `CARD_WRITTEN` record.
- Against the synthetic margins (`record:148-153`): L2-12's synthetic crypto rehearsal ended `CARD_WRITTEN` with
  INSUFFICIENT_DATA on both engines and reference `n_years` 3 calendar, 2 whole (`record:151`); pilot 2's real run ended
  `CARD_WRITTEN` with PASS on both engines and has 11 and 9. The failure-side controls of that run have no pilot
  counterpart: N7 (i), P12 at 2x with corr 0.9989206568469223 and abs dSR 0.07763231205006826, `pass` false
  (`record:152`), and 80 perturbations refused with exit 20 (`record:153`).
- Python 3.13.17 (owner decision D3 of 2026-11-17). Pilot 2's bridge interpreter ran Python 3.13.17: `check_env.python`
  (`run2:18090`) and every child manifest (`run2:4849` and nine more) say 3.13.17, while the venv's `pyvenv.cfg`
  recorded 3.13.14 (`venv.reads.pyvenv.version`, `run2:22754`) and the runbook pins 3.13.14
  (`docs/nautilus_bridge/RUNBOOK_windows.md:7`). Pilot 1 ran 3.13.14 throughout (`check_env`, `run1:7984`, and all 24
  child manifests, e.g. `run1:1409`); its `pyvenv.cfg` also recorded 3.13.14 (`run1:11696`). The installed packages
  and the wheel identity are the same in both records (`venv.reads`: nautilus-trader 1.231.0, numpy 2.3.5, pandas
  2.3.3; wheel `47d274d7…`, 764 entries). Why the base interpreter changed
  between the two pilots is not verified (no record). The runner did not refuse the run: the venv check reads the minor
  "3.13" only (`RUNBOOK_windows.md:8-9`). The owner's report of 2026-11-17 put this to him as D3, recommended answer
  "★A 차이로 기록하고 파일럿 2를 그대로 인정" (other answer: "B 3.13.14로 파일럿 2 다시 실행 (한 번 더 앉으셔야 함)";
  `report-1117:20`), and the owner approved every recommendation other than those he named, which do not include D3
  (`answer-1117`, handoff `CURRENT.md:26` and `:42`; section 7, row 42). So pilot 2 stands as run, with this difference
  recorded.

### 6. The Windows full run of record (Step 10)

- Commit `cdbbe61e689ea56904bb56c23e0824ba71ced0f5` by the owner (author `unknown`), 2026-11-14 01:13:32 KST
  (2026-11-13T16:13:32Z); it changes `qa/acceptance_results.json` only and its parent is `8a3d171`. 844/964 passed,
  0 failed, 120 not run; 964 unique test names (`acc`).
- Per suite (`acc`): safety 10, engine 92, ui 4, quant 53, ficc 57, bonds 33, expansion 20, macro 426 PASS and 120
  NOT_RUN, paper 21, grokteam 17, guard 5, papers 49, nautilus 57; no FAIL anywhere.
- `nautilus`: 57 PASS, 0 NOT_RUN; L2-01 (`test_l2_01_check_env_pins_identity_precision`, `acc:5787`) and L2-5b
  (`test_l2_05b_input_linked_to_env_refused`) PASS. `guard`: (a) `test_a_tag_is_annotated_and_peels_to_the_baseline`
  PASS, (b) `test_b_tagged_pins_match_prereg_and_frozen_rule` PASS, (c) `test_c_no_forward_look_before_it_opens` PASS,
  (d) `test_d_library_versions_match_the_pins_while_a_readout_is_pending` and
  `test_d_pending_readouts_retire_only_when_all_three_are_in` PASS.
- Against the 7A.2 run (`acc-7a`), test name by test name: 0 added, 0 removed, 0 changed; no NOT_RUN reason text changed.
- An earlier E run on the owner's machine ended 843 PASS, 1 FAIL, 120 NOT_RUN, exit 1; the FAIL was L2-01, whose check
  compares the interpreter's version with the venv's `pyvenv.cfg` version (`tests/nautilus_acceptance.py:693`): 3.13.17
  against 3.13.14 (the owner's diagnosis as GPT reports it, `gpt-e:47`). GPT then gave the owner the procedure
  `venv --upgrade --without-pip`, which keeps the installed packages; the run of record followed, and L2-01 passed in
  it (`gpt-e:47`). That earlier run was not committed. That the upgrade was run is not verified: its console output and
  a new print of `pyvenv.cfg` were not submitted (`gpt-e:47`). It is the same version difference as section 5.
- `qa/acceptance_results.json` was written by no Claude commit: `git log 563db54^..cdbbe61 -- qa/acceptance_results.json`
  lists `563db54` and `cdbbe61`, both authored `unknown` on the owner's machine. Its md5 before and after this close-out
  is `cda5e6fe2281170a4469139752ab2d68` (git blob `7fd16a6593c6a9a66eea3f67e9e975e915e2805c`, the one GPT read,
  `gpt-e:10`).
- The README's two rows (decision 12, decision 14): the `nautilus` row's last cell becomes `57 PASS` and the Total row's
  last cell `844/964 passed, 0 failed, 120 not run (2026-11-14, Windows)`. The date is the owner's commit date in KST;
  the results file carries no timestamp, so the day the run itself ended is not verified (in UTC the commit is on
  2026-11-13). The other rows still show the 2026-10-23 run and there is no `bonds` row; the whole table is rewritten on
  `main` after the owner's merge, from his Windows run of the merged branch (decisions 7 and 14).

### 7. Rulings since ruling 19, each with its cost if wrong

Sources read from where ruling 19 stops: `log-rb` from its section "2026-10-28, Claude Code 채팅: ③-4 진행, K-g, ②-5"
(line 406; that section is already this file's "Owner rulings that governed execution") to its end (line 687);
`log-main` from its section "2026-11-04, Claude Code 채팅: Step 7A 동안 main 병합 동결" (line 365) to its end (line 1130);
the spec's Status block and Appendix B; `rulings-main` and `rulings-pp`; `table`; `answer-1117`. Each owner ruling and
each decision made on the owner's behalf that bears on the bridge, its pilots or this close-out has a row. Main-side
rulings that do not bear on them are named in row 32 and not repeated. The "cost if wrong" cells are Claude's
assessment; no source gives them.

| # | Date | Ruling (verbatim where the owner's) | Source | Cost if wrong |
|---|---|---|---|---|
| 20 | 2026-10-28 | The handoff protocol: "A로 진행해. 이번 주기에 이미 끝낸 ①, ② 항목도 LEDGER에 기록해." and "앞으로 checkpoint 갱신과 LEDGER 기록은 내 추가 승인 없이 계속 해도 돼." | `log-rb:422-439` | None to the bridge: it governs the handoff branch only. |
| 21 | 2026-10-29 | PR #4 conflicts: on the owner's instruction "가장 최근 T-CAL-02 세션 두개를 참고해서 결정해주세요", Claude took `main`'s owner-signed calendars byte for byte and withdrew this branch's PT-07 (`614dca4`) | `log-rb:441-467`; this file, "After ③-6" | PT-07's loader hardening has to be redesigned against the signed files. No bridge file changed in the merge (`record:254`), so no pilot input moved. |
| 22 | 2026-10-29 | "(가) 결정으로 진행하겠습니다" with "1. X-1 공개 여부 포함" and "Bonds 패치 적용은 진행해주세요"; PT-07 redesign only if worthwhile; ④-2 before ④-1 | `log-rb:469-494` | X-1: none; it is disclosure (section 9). Bonds: `4709cf2` added 33 `bonds` rows and Bonds code that conflicts with `main`, which the P3 merge resolves under decisions 20 to 27; no `code_sha256` input changed. |
| 23 | 2026-10-30 | O2 to O15 at their revision-6 defaults, O8 (outside review optional; GPT and Gemini NOT_PERFORMED), O11 A2 (pilot 1's 12 E1 settings registered before any price read). The source is private (Notion page `4095c916-fe0c-8173-a4da-e8156aa03ae4`); the repository holds a scope summary only | `log-rb:508-532`; `spec:26-39` | If the summary misstates the private text, the runs still rest on the 7A.1 sentence and on each table's `owner_confirmed` (row 27). The O11 A2 rows are permanent: E1 holds 12 rows (`run1`). |
| 24 | 2026-11-03 | Order path: "QUANTGEN 직접 주문"; "네 직접 주문 가능하도록 하겠습니다. 기존 원칙을 고치거나 폐기해주세요." Claude changes the principle to "one isolated order module" in phase 3, not now | `log-rb:534-603` | None to the pilots: T-RO-01 and `test_08` are unchanged on this branch, and P4 (row 34) puts the order module after the merge. |
| 25 | 2026-11-04 | Step 7A session, the owner's choices: "연구 브랜치 push를 승인합니다"; pre-maintenance "이 세션에서 Claude가 인수 (Recommended)"; 7A.3 publication "그대로 push (Recommended)"; the hold-to-maturity bond rule "RP-01 유지, main 검사 수정 (Recommended)" (the rule's real id is BS-08); egress "핫스팟 결과 확인 시 True, 즉 1번 방식으로 확정하겠습니다" | `log-rb:655-679` | Publication: local Windows paths and package lists are public in the 7A.3 files. Egress: the record was made on a phone hotspot; each pilot's own probe was blocked (`egress.probe.blocked` true in `run1` and `run2`), so a different network at pilot time would have been refused, not passed. |
| 26 | 2026-11-03 to 2026-11-04 | Claude's decisions in Step 7A: merges `92cc00f` and `c95b3aa` (conflicts resolved as in section 1), fixes `85d2e51`, `611c718`, `2c299c9` and the re-entry fixes `e07da98` | the commits (section 1); `log-rb:655-687` | All precede `563db54`, so `code_sha256` `f995600b…` and both `owner_confirmed` cover them. A defect in them would show in the E run or the pilots; none showed (0 FAIL, both pilots `hard_pass` true). |
| 27 | 2026-11-04 | 7A.1 sign-off: "I approve spec 2026-10-26 revision 6, the T-RO-01 exemption of its section 5.6 and the merge of claude/amazing-gauss-tdiguu into main. Geon Koh, 2026-11-04." | `spec:17-25`; `log-rb:661-668` | It covers the branch as merged then; decision 8 (row 36) asks for a new confirmation sentence before the owner's merge, since `main` moved a great deal after it. |
| 28 | 2026-11-04 | `main` merge freeze during Step 7A ("(가)로 결정합니다. main 병합 동결은 다음 순서로 진행해 주세요." from PR #69 `bb35b3b`), and its lift: "U4 = (나) main 병합 동결을 지금 해제합니다." | `log-main:365-413`, `log-main:415-457`; `log-rb:605-653` | None to the pilots: the runner checks no `origin/main` ancestry (`log-main:436-447`). The freeze delayed other `main` PRs for about 13 hours (from `bb35b3b`, 2026-11-04 03:36:05 KST, to the lift merge `f455710`, 16:27:00 KST). |
| 29 | 2026-11-04 | "six.moves.winreg 판정 -> 승인" | `spec:2133-2134` | A wrongly allowed census line would hide a Windows import difference; each pilot's C-08 check compares with the Windows baseline only, and neither pilot recorded a failure: C-08 reasons go into a child's `invalid` list (`tools/nautilus/runner.py:1110`, `:1143` at `cdbbe61`), and every child's `invalid` list and `withheld_reasons` are empty in `run1` and `run2`. |
| 30 | 2026-11-04 | Second decision batch: "U1 = (가) 7A.5 직후 이번 주에 H2 판독 → 그다음 ⑤-2 대조 → Pilot 1 [권고]"; "U5 = (가) A: 7A 끝난 뒤 별도 클론에서 대조, 연구 브랜치에는 스펙만 바꾸는 커밋 하나 [권고]"; "H-D5 = (가) 동결 해제 뒤 별도 클론에서 PR. 7A.5부터 Step 10 병합까지는 main을 연구 브랜치에 합치지 않음 [권고]"; P-D2 to P-D9, among them "P-D3 = (가) 승인. 7A.4 검토 커밋 바로 뒤에 따로 넣음 [권고] …", "P-D7 = (가) 6.2 목록 승인. detail.json 처리는 Step 10 뒤에 정함 [권고]", "P-D8 = (가) Pilot 1 전에 세 시계열 모두 [권고]", "P-D9 = (가) 별도 브랜치의 results/RULINGS.md → Step 10에 반영 [권고]"; "M-21 = (가) Nautilus 지문 대상 밖의 새 모듈(예: core/adoption/), 7A.3과 동결 해제 전에는 만들지 않음 [권고]", with the memo "동결 해제 및 7A.3 완료한 점 참고해주세요." | `log-main:497-563`; `spec:2149-2196` | U1 only orders the work (the H2 readout, then ⑤-2, then pilot 1); a wrong order costs time, not a number. M-21: a new module inside the Nautilus fingerprint would change `code_sha256`; none did (section 2). H-D5 makes the P3 merge large (the rehearsal counted about 260 `main` commits, `table` row 8). P-D7 leaves `detail.json` on the owner's machine (section 11). P-D8 held pilot 1 until all three series ran, which found the fmp gap (row 35). |
| 31 | 2026-11-04 | Pilot anchor: "1. Continue with option(가)." (pull spec-only commits before each pilot; Step 10's diff rule reads from the earliest pilot HEAD) | `spec:2197-2203` | The earliest pilot HEAD is `8a8c247`, not `83ee469`; the diff check of section 10 uses `8a8c247`. Spec-only commits leave `code_sha256` unchanged, so nothing else moves. |
| 32 | 2026-11-04 to 2026-11-11 | Main-side rulings that do not bear on the bridge: the market screen request (`log-main:459-495`), NEW-M6-05 and the bootstrap hold (`log-main:565-606`), the approvals of 2026-11-10 ("전부 승인합니노.", `log-main:619-628`), the fourteen answers of 2026-11-11 (`log-main:630-673`). The same section of 2026-11-11 also holds the owner's instruction to move the pilots and the close forward ("그리고 Remaining Work에서 6. 실제파일럿 이랑 7. 마감/병합 부분은 도대체 언제 완료될까요? …", `log-main:656`), which the log takes as a question and a progress instruction, not a ruling (`log-main:673`). Two items of 2026-11-10 touch `HARNESS_SOURCES`, which feed `code_sha256`: the LA-07 change to `core/quant/cardp.py` and `docs/macro_overlay_study.py` (put after the merge by P4), and the after-the-fact approval of `696ee3c` to `core/quant/strategies.py`, which is in this branch since the `92cc00f` merge, before `563db54` | `log-main` as cited | None to the pilots: `git diff --name-only 563db54 cdbbe61` over the `code_sha256` inputs prints nothing (section 2). |
| 33 | 2026-11-11 | P1: "1번으로 승인하겠노": the tool's commit and sha256 are fixed on `main`'s side, and the research branch gets no commit for it | `log-main:675-695`; `rulings-main:17-43` | 10.5's Tool bullet stays stale on this branch; D4 (row 43) keeps it so and puts the facts in the Status block and section 3. |
| 34 | 2026-11-11 | P2, P3, P4: "전부승인" to the recommendations "이 세션이 맡음. 범위는 마감 기록·스펙·README·실행 기록 폴더로 한정합니다. …" (P2), "마감 확인 뒤 Claude가 main을 연구 브랜치에 합쳐 충돌을 풀고 전체 테스트를 돌립니다. …" (P3), "이 세 가지는 병합 뒤로 미룸" (P4) | `log-main:705-707`, `log-main:748`, `log-main:757-759` | P2 bounds this close-out to four kinds of path; the pre-commit checklist checks that. If the session that commits is not the one P2 names, decision 11 requires the owner's one-line approval first. |
| 35 | 2026-11-11 | SPY-가 and BTC-나: "SPY-가-승인, BTC-나-승인" / "그리고 BTC-나 에 따라 문제의 원인 파악 완료 후 자동으로 해결 및 pilot 2 진행해주세요"; the second fixed tool version; Claude's stop point for the second SPY fetch and its reading rules for the BTC-USD diagnostic, both written before any output | `log-main:770-926`; `rulings-main:61-251` | SPY: the second run counted for the gate; if that were wrong, pilot 1 would have started on a run that did not count, but it is PASS against an independent provider on all 5,489 days, and the first run stays on record. BTC: the diagnostic left the owner's machine as counts only. |
| 36 | 2026-11-11 | Decisions 1 to 27 and 13a, "전부승인합노.", every row as its 가: among them the record's name kept (15), README's two rows by Claude (12, 14), `--no-edit` (9), a second Windows full run of the merged branch at F (7), a confirmation sentence before the merge (8), what the P3 merge holds (13, 13a), the push of the closing commits (10), P2 not passed on (11), data-access history in full (16), both SPY summaries copied (18), `detail.json` left in place (19), the Bonds choices (20 to 27) | `table`; `log-main:928-984` | Rows 15, 12, 9 and 7 are spec deviations (section 8). Rows 1, 3, 4 and 5 were not needed: both pilots passed parity and wrote a card, with no re-run and no withheld record. |
| 37 | 2026-11-12 | X1 to X5, "X1~X5 모두 권장값으로 하겠습니다": a pilot-2 parity failure is reported and asked (X1); decision 4's re-run is one per pilot (X2); FAILs beyond the two known rows of the cache-free run are asked before the P3 push (X3); `main` moving before the sentence is recorded means merge again and ask again (X4); when L2-5b was NOT_RUN at E, the owner is told to turn Developer Mode on before F (X5) | `log-main:1002-1074` | X1 and X2 were not needed (row 36). X5 is not needed: L2-5b passed at E (section 6); F1a still checks the setting. X3 and X4 apply at P3. |
| 38 | 2026-11-12 | Claude, on the owner's behalf, applied its reading rule to the owner's BTC-USD diagnostic output: case 5, cause not identified; so BTC-나 did not open the gate, and Claude asked the owner (BTC-라, -마, -바) | `ledger` row ⑤-2/e; `log-main:1099-1107` | Had the rule been misapplied, the gate would have stayed closed for nothing; the owner's later ruling (row 39) decided it either way. |
| 39 | 2026-11-13 | BTC-라: "그러면 라 옵션으로 가겠습니다": record the mismatch and its unresolved cause in this record and in 10.4, and let pilot 2 go ahead under 10.5's owner-ruling gate; the BTC-USD comparison stays FAIL | `log-main:1109-1125`; `rulings-main:286-302` (on `main` only: added by `a90c90b`, edited by `661c6b8`, merged by `795165c`) | Pilot 2 ran on a pinned BTC-USD file whose disagreement with two venues has no identified cause; its PASS is engine parity on that file, not evidence the file is accurate. Its 5 C3 rows are permanent (`n_raw` 17 to 22). |
| 40 | 2026-11-13 | Pilot 2 to E (decision 6): pilot 2 ended `CARD_WRITTEN` with exit 0, so decision 6 let the owner go on to the full run without waiting for a readout. In the event GPT's readout was written at 21:40 KST, eight minutes after the pilot 2 commit (21:31:47 to 21:40:07 KST) and before the E commit (01:13:32 KST on 2026-11-14) | `table` row 6; `gpt-p2:3`, `gpt-p2:96-104` | None incurred: no readout found a reason to re-run pilot 2, so the E run follows the last pilot. |
| 41 | 2026-11-13 to 2026-11-14 (inferred from `8a3d171`, 21:31:47 KST, and `cdbbe61`, 01:13:32 KST; the guidance's own time: no record) | GPT's guidance after the first E run failed L2-01: `venv --upgrade --without-pip`, keeping the installed packages; the owner's run of record followed (that the upgrade was run: not verified) | `gpt-e:45-49` | If the upgrade had changed a package, L2-01's wheel-identity check and the other 56 `nautilus` rows would show it; all 57 passed. The upgrade's console output was not submitted (not verified). |
| 42 | 2026-11-17 | D3, pilot 2's Python 3.13.17. Recommended: "★A 차이로 기록하고 파일럿 2를 그대로 인정" (other: "B 3.13.14로 파일럿 2 다시 실행 (한 번 더 앉으셔야 함)"). The owner's answer: "다음 결과들을 제외한 나머지는 권장대로 승인한다." The exceptions he lists are D5, D9, D11, D13, D14 and D7; D6 he approves as recommended, with specifics ("다음 결과들은 다음과 같이 권장사항을 따르되 구체화한다."); neither list names D3. It ends "앞서 말한 것처럼 나머지는 권장대로 승인한다." The main session read it as "D1·D2·D3·D4·D8·D10·D12는 권장대로" | `report-1117:20`; `answer-1117`: handoff `CURRENT.md:26` (first line), `:28-33` (exceptions), `:37-39` (D6), `:42` (last line), `:44` (reading) | Pilot 2's two engines ran in the same interpreter, so their 10/10 parity is unaffected; whether the same run on 3.13.14 would give the same numbers is not verified. The runbook still pins 3.13.14 (section 11). |
| 43 | 2026-11-17 | D4, 10.5's Tool paragraph: recommended "★A 본문은 그대로, 지금 도구 위치·커밋·지문을 Status와 마감 기록에 적음" (other: "B 단락 본문을 고침"); approved by the same answer (not among the exceptions). It answers the question `table` left open ("스펙 10.5의 도구 문단을 Step 10에 고칠지", `table:77`) | `report-1117:21`; `answer-1117` (handoff `CURRENT.md:26-42`) | A reader of 10.5 alone sees "the tool is not written yet"; the Status bullet of 2026-11-17 and section 3 give the tool's place, commits and sha256. Fixing the paragraph later is a spec-only edit. |
| 44 | 2026-11-17 | Claude's decisions in this close-out, on the owner's behalf: (a) the README Total date is 2026-11-14, the KST date of `cdbbe61`, since the results file holds no timestamp; (b) every `git diff` of the diff checks adds `':!docs/asset_expansion/cache'`, which the prep's literal lines lack; (c) the commit table of section 1 names five commits more than the prep's list (`cad341c`, `0a91f26`, `2da6469`, `e089e59`, `36df786`); (d) main-side rulings without a bearing on the bridge are named in row 32, not one row each; (e) the spec's Appendix B gets the one entry `prep` 2.8 proposes in this change, not in the spec's next revision (the main session's decision before the commit; the drafting task had allowed only the spec's Status block and its 10.4 rows); dated 2026-11-17, it quotes P1 to P4, SPY-가, BTC-나 and the decision table's answer, adds BTC-라 and the answer of 2026-11-17 for D3 and D4, and lists what the closing commit changes (section 11); (f) the rows added to 10.4 are the same text in the spec and in section 9 | this record | (a) one README cell off by a day; fixed in the README rewrite after F or by a one-line commit. (b) a change under the protected folder between `8a8c247` and the closing commit would not be listed; the three owner commits in that range list only their own files with the folder excluded, and the folder was not inspected (not verified). (c) to (f): none to any number. |

### 8. Spec deviations

The ten items of "Spec deviations to carry to Step 10 and the spec's next revision" above (`record:171-184`: T1 CI 7,
T1 CI 9, T2 CI 4, T3 CI 1, T5 CI 1, T5 CI 3, T1-R4, T2-m8, T4-R5, X8) are carried unchanged; all are implemented as
ruled. Two bear on the pilot readout: T5 CI 1 (a column that never trades shows P2 1.0 by rule) and T4-R5 (the
`run.final.<pid>.json` fallback). Neither pilot wrote a fallback record (`record_write_failures` empty in `run1` and
`run2`).

Found since, each a difference between the spec's text and what was done or ruled (`prep:1419-1435` lists the first
twelve; each was checked against the sources named):

| Point | Spec text | What happened | Source |
|---|---|---|---|
| Tool branch | 10.5 names `claude/provider-parity-5-2` | the tool is on `main` and the run branch, by ruling P1; the research branch got no commit for it | `spec:1716`; `rulings-main:36-38` |
| Tool commit and sha256 | 10.5 leaves them out "until the tool exists" | fixed in `results/RULINGS.md` and the tool's README, not in 10.5; by D4 (2026-11-17) the paragraph stays as written and the Status block of 2026-11-17 and section 3 give the values | `spec:12` (the quoted words); `spec:1716-1719`; `rulings-main:29-30`, `rulings-main:91-92`; section 7, row 43 |
| Rulings file of the run branch | 10.5: each ruling goes into `results/RULINGS.md` on the tool's branch | the BTC-라 entry of 2026-11-13 is in `main`'s `results/RULINGS.md` only; the run branch's copy (`77d2647`) ends at the BTC-나 entry | `spec:1738-1747`; `rulings-main:254-307`; `rulings-pp` (251 lines) |
| Execution record's file name | `2026-10-<dd>-nautilus-bridge-execution-record.md` | this file is extended and keeps its name (decision 15) | `spec:1633`; `record:94`; `table` row 15 |
| Who updates the README counts | "The owner ... updates the README counts and Total row" | Claude changes the two rows from the owner's results file in the closing commit (decision 12) | `spec:1633`; `table` row 12 |
| Step 9 command | no literal command in the Step 9 row | the owner's run sheet gives one from the runner's usage line | `spec:1632`; `prep:1428` |
| "the manifest hashes" in the card | Step 8 Done-when lists them among the card's content | the card holds `row_md5s` and `ledger_hash_at_run`; the child manifests are in `run.json` (also `gpt-p1:53-54`) | `spec:1631`; `prep:1429` |
| "the selection used" and "PBO for information only" in the card | Step 8 and Step 9 Done-when | the card holds a fixed selection sentence, `stats.chosen_last`, `tests.pbo` and `stats.prob_loss_oos`; the origins, the chosen columns and the predicates are in `run.json` (`gate.selection`) | `spec:1631-1632`; `prep:1434` |
| Merge of `main` before the owner's merge | the runbook's four merge lines assume no conflict | ruling P3: Claude merges `main` into the branch after the Step 10 checks; decision 13: the merge commit also holds the review fixes F1 to F5, the rehearsal's Korean wording and the regenerated status snapshot, and S1 to S4 and the compliance baseline follow as separate commits | `prep:1430`; `log-main:758`; `table` rows 13, 13a |
| A second Windows full run | Step 10 names one Windows full run | decision 7: the owner runs the full suite once more on the merged branch at the start of his merge sitting and commits the results file before he merges | `spec:1633`; `table` row 7 |
| Merge message editor | the runbook's merge line has no `-m` and no `--no-edit` | decision 9: the owner's merge line carries `--no-edit` | `prep:1435`; `table` row 9 |
| Re-run after a C-06-only WITHHELD | 5.3.5 and R-17 allow such a re-run without `--rerun-of` | by the code as read, a plain re-run is refused (not verified on a real run); decision 4's re-run (one per pilot, answer X2) passes `--rerun-of`. Not exercised: neither pilot was withheld or re-run | `prep:1432` |
| WITHHELD with parity passed | Steps 8 and 9 name "decision mismatch" and "reference drift" as valid ends | the runner can also end WITHHELD for `benchmark test dropped`, G-03 and G-05; decision 3 does not count such a step as finished. Not exercised | `prep:1433`; `table` row 3 |
| Python patch of the bridge interpreter | Step 7A Done-when: `--check-env` reports the pinned versions; the runbook pins Python 3.13.14 | pilot 2 ran Python 3.13.17 (`check_env` and every child), with `pyvenv.cfg` still at 3.13.14; the owner accepted pilot 2 as run (D3, 2026-11-17). The first E run then failed L2-01 on the same difference; GPT gave the procedure `venv --upgrade --without-pip`, and L2-01 passed in E's run of record (that the upgrade was run: not verified) | `spec:1620`; `RUNBOOK_windows.md:7`; `run2:18090`, `run2:22754`; section 5; section 6; section 7, rows 41 and 42 |
| Status note on 10.4 | "The ⑤-2 rows of 10.4 are written at Step 10" | written in this close-out (10.4 and section 9), with the BTC-USD disagreement that 10.5's Gate asks for | `spec:9-10`; `spec:1745-1747` |

### 9. Data-access history (spec 10.4)

The table of spec 10.4, verbatim (`spec:1695-1706`), then the rows added at Step 10. The same added rows are written
into spec 10.4 in this close-out. Decision 16: every known event, written as it happened; what could not be found is
written "no record" (기록 없음), never left out.

| When | Who | Data | What was computed | Ledger rows |
|---|---|---|---|---|
| 2026-09-27 and earlier | asset-expansion study | `yf_SPY.csv` 2004-12-01 to 2026-09-25, inside the four-sleeve book `S_E1_trend_us` | the 12-setting grid on SPY, QQQ, TLT and GLD at 1/4 each; REJECT | none (`n_trials` typed by hand) |
| 2026-09-27 and earlier | asset-expansion study | `yf_BTC-USD.csv`, whole file | runs 2 and 3 (6 hysteresis values), then the five lattice values; PASS | none |
| 2026-10-26 | map 03 probe | `yf_SPY.csv` 1995-01-03 to 2004-11-30 (2,497 sessions), `fred_DGS3MO.csv` | all 12 pilot-1 settings at 1x and 2x on both engines; walk-forward selection | none; their `config_id`s equal pilot 1's, because `span` is not in the key |
| 2026-10-26 | synthesis and critic | the same pre-2004 window and map 03's saved matrices | 109 single-block flips; walk-forward ties (K3) | none |
| 2026-10-26 | round-1 referees, Revision-2 probes | synthetic series only; the study module imported without reading data; no real BTC price | fixtures, ties, cost gaps, scan rules, egress | none |
| 2026-10-26 | round-2 referees, Revision-3 probes | synthetic series; `fred_DGS3MO.csv` (its NaN pattern); the stored cards' statistics; the first 3 lines of `yf_SPY.csv` (1995) and 4 pre-2004-12-01 dates in it (QA referee); no BTC price, no SPY row from 2004-12-01 | rf fill, gate predicates, rounding, `Money`, fixtures, scan | none |
| 2026-10-26 | round-3 referees, Revision-4 probes | synthetic series and calendars; the stored cards' JSON (statistics, line text, the S_C3 card's md5); `study.log`, `manifest.json` and `results.md`; the names and sizes, not the content, of `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv`; no price row of a real series | the `n_years` rule, `cents`, fixtures, 6.1 refusals, scan, remedies, digests | none |
| 2026-10-26 | round-4 referees | synthetic series; the four KRX ETF caches and `fred_DGS3MO.csv` (quant referee, re-scoring the stored `S_E1_trend_krx` grid, raw and 9-decimal); stored cards' JSON; no SPY row from 2004-12-01, no BTC price | G-08 rules on a stored card, P0a stand-ins, digests | none |
| 2026-10-26 | round-5 referees (ops, security) | closure wheels installed offline into scratch venvs, throwaway git repositories, extracts of this spec; lines 27 and 29 of `docs/asset_expansion/study.log` (the owner's profile path); no price file, no price cache, no ledger | pip and git re-entry, both pins, the 8.5 controls | none |
| Steps 3 to 7 | Claude | synthetic series only | rehearsals | temp only |
| 2026-10-26 | Claude, two cloud full-suite baseline runs in the real clone through the wrapper (X-1, execution record) | `yf_SPY.csv`, `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv`, opened by three existing `macro` tests | test statuses and counts only; no price value in either log | none |
| 2026-10-29, about 05:50 UTC | Claude sub-agent reviewing the Bonds patch: one recursive `grep --include='*.csv'` without the cache exclusion (self-report, research branch rulings log) | the four protected caches, opened by grep | nothing matched, printed or hashed | none |
| 2026-10-29 to 2026-11-12 | Claude, cloud full runs after the X-1 entry (listed in the execution record, Step 10 close-out, section 9) | none of the protected caches: each run used a copy without them (for the runs of 2026-11-04 and 2026-11-05 inferred from the two known environment FAILs their ledger rows name) | test statuses and counts | none |
| 2026-11-11 04:06:04 and 04:13:18 KST (2026-11-10T19:06:04Z and 19:13:18Z) | a Claude helper of the main session, the sub-agent "fix:rulings" of workflow run `wf_e00ee1e6-d37`, in a non-sparse scratch worktree on branch `claude/owner-rulings-20261111`: two walks of the protected folder by name, one git index query and one `find` (the main session's conversation records, not git, checked 2026-11-17; the handoff line is in handoff commit `52eb246`) | at 04:06:04, git's index entries under the folder (`git ls-files 'docs/asset_expansion/cache'` piped to `grep -c "\.py$"`); at 04:13:18, the folder's directory entries, walked by `find . -name "__pycache__" -newer docs/compliance/source-review.json -not -path "./docs/asset_expansion/*"` (`-not -path` filters the output and does not prune); no file opened | a count of `.py` names, whose only output was 0; the `find` printed nothing; no file name was printed | none |
| 2026-11-11 | Claude, git commands (`status`, `add`, `commit`, `diff --check`) in two non-sparse scratch worktrees of the main clone (the merge rehearsal; the Step 10 working documents); in the helper's non-sparse worktree of the row above: no record (execution record, Step 10 close-out, section 9) | the protected folder's files, stat-ed by git, never opened by a command | nothing | none |
| 2026-11-11 | Claude, the merge rehearsal's Bonds test modules behind an audit hook that refuses and counts any open or listing of the protected folder, a `.env` file or `~/.nextgen` | none: the hook counted 0 in every run | test statuses | none |
| 2026-11-12, 00:3x KST | Claude, the lead of session_01H6RrzMUzF8vwK8xkX977mB: one `git ls-files` listing without the cache exclusion, in a sparse worktree without the folder (self-report, commit `c3101e5`) | ten file names of the protected folder from git's index; no content, size or hash; no file opened | nothing | none |
| 2026-11-04 | owner, Step 7A.2 on Windows | the O11 A2 registration (reads no price); synthetic fixtures and timing; the full suite with the caches present | registration; suite statuses | E1: 12 rows (owner-reported, Appendix B, 7A.4 review) |
| 2026-11-11 (SPY 05:19:09Z, DGS3MO 07:53:07Z, BTC-USD 07:53:28Z) and 2026-11-12 (SPY 07:37:47Z) | owner, provider parity tool (10.5): the first fixed version for the three runs of 2026-11-11, the second for the second SPY run | the three pinned files on the pilot windows; providers' series fetched on the same machine (`fmp`, `kis`, `yahoo_now`, and a new `fmp` fetch for the second SPY run; `treasury`, `fred_now`, and `h15`, whose fetch failed; `coinbase`, `bitstamp`, `binance`); the `kis` fetch reads, and may rewrite, the app's KIS access token `~/.nextgen/kis_token.json` and writes nothing else under `~/.nextgen` (10.5, Writes) | only the kinds the tool's `COMPUTES` table names (10.5, exception to 3.9); no observation dated on or after 2027-01-01 (10.5); four summaries of record | none |
| 2026-11-12 or before (read at 16:53 KST); exact time: no record | owner, BTC-USD diagnostic `tools/provider_parity/btc_diagnose.py` (sha256 `1e44f3a7…`) by ruling BTC-나 | `yf_BTC-USD.csv` and the `coinbase` and `bitstamp` files of the first sitting, through the tool's readers; no `detail.json` | counts per calendar year, the 99th percentile and the maximum of the level difference, group counts; pasted into the chat | none |
| 2026-11-11 to 2026-11-12 | Claude | the four `summary.json` (counts, dates, booleans, decade buckets) and the diagnostic's console output as pasted (counts) | read only; the reading rule written before the output: case 5, cause not identified | none |
| 2026-11-12 15:30:28Z to 15:31:56Z | owner, pilot 1 of record `NB-20261112T153028389916Z-d76d2d73` | `yf_SPY.csv` 2004-12-01 to 2026-09-25 (5,489 sessions), `fred_DGS3MO.csv` | the 12 registered settings at 1x and 2x on both engines; parity; walk-forward; both scores (REJECT, REJECT) | E1: 0 appended, 12 already present (`n_raw` 12 to 12) |
| 2026-11-13 | Claude, the main session (handoff ledger row ⑥-1, 00:35 KST), and GPT (readout at 16:58 KST) | Claude: the owner's console lines of pilot 1; GPT: the pushed `run.json` and card of pilot 1, the second SPY summary and the diagnostic's totals from the handoff document | readout only | none |
| 2026-11-11 to 2026-11-13 | BTC-USD gate (10.5): the run of record `PP-20261111T075328Z-btc` is FAIL (`coinbase` 43 days above 0.02, allowed 20; `bitstamp` 47, allowed 21; both outside the late level band); the diagnostic is case 5, cause not identified; owner ruling BTC-라 of 2026-11-13 ("그러면 라 옵션으로 가겠습니다") lets pilot 2 go ahead with this disagreement noted | `yf_BTC-USD.csv` against two venues, as in the rows above | nothing beyond the rows above; the summary stays FAIL | none |
| 2026-11-13 12:26:42Z to 12:27:32Z | owner, pilot 2 of record `NB-20261113T122642089406Z-e2ec073c` | `yf_BTC-USD.csv`, whole file (4,392 sessions) | the 5 registered settings at 10 and 20 bp on both engines; parity; reference comparison (G-08); both scores (PASS, PASS) | C3: 5 appended (`n_raw` 17 to 22) |
| 2026-11-13 (GPT readout at 21:40 KST) | GPT | the pushed `run.json` and card of pilot 2, the reference card's JSON, the owner's console lines | readout only | none |
| 2026-11-13 to 2026-11-14 (results commit `cdbbe61`, 01:13:32 KST) | owner, Step 10 Windows full suite, twice: a first run with one FAIL (not committed) and the run of record | the caches present on the owner's machine; X-1's `macro_m8_pipeline` dry run and `cry1` test ran there (PASS), `g_b5_02` NOT_RUN | suite statuses | none |
| 2026-11-14 (01:21 KST) | GPT | the pushed `qa/acceptance_results.json`; the four `summary.json` of the run branch at `77d2647` and `README.md`, copied byte for byte into a private draft `step10-draft-20261114` (handoff `STEP10_CHANGE_REVIEW_2026-11-14_gpt.md:30-39`; handoff `CURRENT.md:146` at `212f68e`) | readout; git blob and sha256 of the four summaries and their tool fingerprint; the README two-cell draft | none |
| 2026-11-17 (the main session's check of GPT's readouts, first recorded in handoff commit `0ae7045` at 18:31:08 KST, handoff `CURRENT.md:47-50` at `212f68e`; the time of the check itself: no record) and 2026-11-17 (this close-out) | Claude, session_01H6RrzMUzF8vwK8xkX977mB and its sub-agents, in scratch clones without the protected folder | the pushed `run.json` and cards of both pilots (statistics, parity, gate fields; no fill row printed), the four summaries, `qa/acceptance_results.json` | readout; sha256 of the four summaries | none |

The X-1 entry, as written above in "Data-access history entry (X-1), for the Step 10 record and spec 10.4"
(`record:290-302`), copied here because two of its six bullets fit no column of the table:

- **What happened.** On 2026-10-26, before this plan, two cloud full-suite baseline runs ran in the real clone through the wrapper (`docs/audit/2026-10-27/artifacts/run_all_cloud_run1.log`, `run_all_cloud_run2.log`). Three existing `macro` tests opened protected caches while they ran:
  - `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`: `yf_SPY.csv`
  - `macro/macro_m3_estimators/test_g_b5_02_spy_refdata_with_smoke_on_local_cache`: `yf_SPY.csv`
  - `macro/macro_tf_gov/test_cry1_study_runs_offline_end_to_end_on_the_local_caches`: `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv`
- **What Claude saw.** Test names, PASS/FAIL statuses and counts only. No price value appears in either log. Run 1's dry-run failure detail is an empty `AssertionError`.
- **Rule affected.** Spec section 9, row 2 ("Claude reads no real BTC price and no SPY row on or after 2004-12-01"; "never opens or hashes ..."). The test processes opened the files.
- **Since then.** Every full run of this plan used a sparse clone where the four caches are skip-worktree and absent (X-1, T5-1): seven runs through ③-6 and three after the `main` merges. No bridge test opens a cache file.
- **Pilot relevance.** Pilot 1 (SPY) and pilot 2 (BTC-USD) are registered on these series. Claude's view was limited to statuses, so no design choice used their values. This entry exists so a reader of the pilot results can weigh that.
- **Later event (2026-10-29, about 05:50 UTC).** While reviewing the Bonds patch (②-5/b), a Claude sub-agent's first recursive `grep` (`--include='*.csv'`) did not exclude `docs/asset_expansion/cache/`, so the four protected caches were opened by grep. Nothing matched, nothing was printed and nothing was hashed; later searches excluded the folder (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "Claude 자진 보고 (2026-10-29)"). No value from the files reached Claude.

"Since then", completed for every cloud full run found after the X-1 entry was written, one line per run as far as
the ledger tells runs apart. The sources are this file and the handoff ledger (`ledger`, rows found by searching for
"전체 실행", "full run" and "run_all"); a run that no ledger row records is not listed, and none other is known. Ledger
rows that share one time and one pull request quote one result cell; each such group is one line here and is taken as
one run (inferred; the ledger does not say). Most rows say the copy had no protected caches ("cache-free", "보호 캐시
없는 사본", "캐시 없는"); the rows of 2026-11-04 and 2026-11-05 say only "2 known env FAIL", and the `macro_m8_pipeline`
dry run fails only in a copy without `yf_SPY.csv` (`record:137`), so for them cache-free is inferred. No row says
whether the copy came from the whole-folder recipe of `prep` 2.2 or the four-file recipe of `record:41-46`: the recipe
is "no record" (기록 없음) on every line.

| Recorded (ledger time, KST) | Ledger rows | Where | Counts | How the copy was made |
|---|---|---|---|---|
| 2026-10-29 14:59:04 | ②-5/b | this branch, `4709cf2` | 825/964 passed, 2 failed, 137 not run | "보호 캐시 없는 사본"; recipe: no record |
| 2026-11-04 20:54:26 | ⑬-2/a4-b/2, ⑬-2/a4-c/2, ⑬-2/a4-d/2, ⑬-2/a4-e, ⑬-2/a3-type, ⑬-2/a3-rail, ⑬-2/a3-controls | `main` work branch of PR #71 (merge `d5e73ae`; the rows name CI on `3c0fd24`; the run's head is not named) | 746/872, the 2 known environment FAILs | cache-free inferred; recipe: no record |
| 2026-11-04 21:19:07 | ②-5/M4-N4, ②-5/M4-N7, ②-5/M4-N9 | PR #72 (merge `a32106b`; CI on `d88277a`; the run's head is not named) | 746/872, the 2 known environment FAILs | cache-free inferred; recipe: no record |
| 2026-11-05 01:38:33 | ②-5/N-M1-02/a, ②-5/NEW-M6-04, ②-5/NEW-M6-05 | PR #73 (merge `faf9f3b`; CI on `516953a`; the run's head is not named) | 746/872, the 2 known environment FAILs | cache-free inferred; recipe: no record |
| 2026-11-10 22:13:44 | ⑨-1/2/a | PR #94 (merge `be26c24`; the run's head is not named) | 747/873, the 2 known environment FAILs | "cache-free"; recipe: no record |
| 2026-11-10 23:22:25 | ⑨-1/2/b | `8e88814` | 754/880, the 2 known environment FAILs | "cache-free"; recipe: no record |
| 2026-11-11 02:23:34 | ⑨-1/2/c (two runs: "on both heads") | the row's two heads, not named by it (it names the PR #97 merge `e60daf5` and the head `a09735a`) | 763/889 on each, the 2 known environment FAILs | "cache-free"; recipe: no record |
| 2026-11-11 04:49:07 | ⑨-3a/series-files/2 | `e4b0772` | 763/889, the 2 known environment FAILs | "cache-free"; recipe: no record |
| 2026-11-11 06:01:07 | ⑨-1/2/d | `30f009d` | 769/895, the 2 known environment FAILs | "cache-free"; recipe: no record |
| 2026-11-11 12:22:49 | ⑤-2/b | PR #102 (merge tree = head `b92275f`; the run's head is not named) | 769/895 | "캐시 없는"; recipe: no record |
| 2026-11-11 13:53:48 | ⑨-3a/series-files/3 | PR #103 (merge tree = head `4d3cc16`; the run's head is not named) | 769/895 | "캐시 없는"; recipe: no record |
| 2026-11-11 15:12:24 | ⑥-1/prep | the merge rehearsal commit `a5f904a`, local: `prep:52` says the rehearsal was never pushed, and the commit's subject says "REHEARSAL ONLY, never push" | 987 rows: 843 PASS, 137 NOT_RUN, 7 FAIL | "캐시 없는"; recipe: no record |
| 2026-11-11 22:24:22 | ⑤-2/f | `c70426c` | 769/895 | "캐시 없는"; recipe: no record |
| 2026-11-12 02:30:58 | ⑨-1/2/d/2 | PR #107 (merge `f263fb2`, tree = head `f91c25b`; the run's head is not named) | 782/908, the 2 known environment FAILs | "캐시 없는"; recipe: no record |
| 2026-11-12 17:08:23 | ⑨-4/2/c | `351db88` | 782/908 | "캐시 없는"; recipe: no record |

No full run, and no test, was run for this close-out.

The two walks of the protected folder by a helper (row "2026-11-11 04:06:04 and 04:13:18 KST" above). Git holds one
line about them, in the handoff document: "하위 작업자가 보호 캐시 폴더를 이름으로 두 번 훑음(git 색인 조회, find). 파일을 열지는
않음. 이후 지시문에 제외 방법을 명시." It first appears in handoff commit `52eb246` (2026-11-10T19:49:08Z, that is
2026-11-11 04:49:08 KST), written by the main session (its `CURRENT.md:19`), and is not in its parent `56ffe71`; it is
still in the handoff document at `212f68e`. The owner's answer "규칙은 꼭 지키자" is in the same document. Git holds neither
the times of the two walks nor what each printed: the handoff document at `52eb246`, `74744d4` and `212f68e`, `log-main`
at `e01e152`, `log-rb` at `cdbbe61` and the GPT readouts were searched for them. As decision 16 asks, the main session
looked in its own conversation records on 2026-11-17 and found them there. Those records are not in the repository and
the drafter of this paragraph could not read them, so what follows is the main session's report of them (not verified
from git). The helper was the Fix-phase sub-agent "fix:rulings" of workflow run `wf_e00ee1e6-d37`
("owner-rulings-r3-adoption-and-reports"), working in a non-sparse scratch worktree on branch
`claude/owner-rulings-20261111`:
- 2026-11-10T19:06:04Z (2026-11-11 04:06:04 KST): `git ls-files 'docs/asset_expansion/cache' | grep -c "\.py$"`, a
  query of git's index whose only output was the count 0. No file name was printed and no file was opened.
- 2026-11-10T19:13:18Z (2026-11-11 04:13:18 KST), over that worktree:
  `find . -name "__pycache__" -newer docs/compliance/source-review.json -not -path "./docs/asset_expansion/*"`.
  `-not -path` filters the output but does not prune, so `find` walked the folder's directory entries. It printed
  nothing, and no file was opened.

By the same records (not verified from git), the sub-agent reported both walks itself in its result, quoted in part
("Twice I touched the protected cache path by name only, against the rule: ... No file there was opened or read."), and
the main session then wrote the handoff line above in `52eb246`.

Git commands in the helper's worktree: no record. Neither git nor the main session's report of its records says whether
any ran there. Git has two commits with the main session's `Claude-Session` trailer on that branch in the same minutes:
`ae7bb26` (2026-11-10T19:13:43Z, 04:13:43 KST), which changes `docs/compliance/source-review.json`, the file the `find`
compared against, and the merge `e4b0772` (19:15:29Z, 04:15:29 KST). Git does not record the worktree a commit was made
in. In a worktree that holds the protected folder, git commands such as `status`, `add` and `commit` stat the folder's
files (`prep:1467`: "Git stats every tracked file of a worktree, the protected folder included"); that is the event of
the row of git commands of 2026-11-11 above, which gives "no record" for the helper's worktree.

The 2026-11-12 self-report (`log-main:986-1000`, commit `c3101e5`): in a sparse worktree without the protected folder,
the lead of session_01H6RrzMUzF8vwK8xkX977mB ran `git ls-files -- 'docs/asset_expansion/*.csv'
'docs/asset_expansion/*.md' | head` without `':!docs/asset_expansion/cache'`; a git pathspec `*` crosses `/`, so ten file
names of the protected folder were printed from git's index. No content, size or hash was seen and no file was opened;
nothing was computed. The rule broken is the ban on listing the folder. Since then every such `git ls-files` and
`git grep` adds the exclusion. It is a row of the table above.

### 10. Step 10 Done-when, clause by clause

| Clause (`spec:1633`) | Evidence | Result |
|---|---|---|
| "The Windows full run shows 0 FAIL with the `nautilus` suite counted" | section 6: `cdbbe61`, 844/964 passed, 0 failed, 120 not run; `nautilus` 57 PASS | met |
| "`qa/acceptance_results.json` is committed only from an owner's Windows full run (Step 7A.2 and this step), never from Linux" | `git log --format='%h %an %s' 563db54^..cdbbe61 -- qa/acceptance_results.json`: `cdbbe61 unknown nautilus: Step 10 Windows full run (win_amd64)` and `563db54 unknown nautilus: Step 7A records (win_amd64), …`; none authored by Claude; the closing change leaves the file byte-identical (md5 `cda5e6fe2281170a4469139752ab2d68`) | met |
| "frozen_guard (a), (b) and (d) pass there" | section 6: the five `guard/` rows PASS | met |
| "run folders and the execution record are committed" | the run folders: `a2ac79b`, `8a3d171`; the record: the closing commit that carries this section | met when the closing commit lands |
| "`git diff --name-only` against the earliest HEAD that the pilot run records store … lists only paths under `docs/nautilus_bridge/runs/`, the execution record, `README.md`, `qa/acceptance_results.json` and this spec" | earliest HEAD `8a8c2475b1a1480c7c6596a9d89619c755ab1e2a` (`run1` `git.head`; `git merge-base --is-ancestor 8a8c247 a2ac79b` exits 0, and `a2ac79b` is `run2`'s head). To `cdbbe61`: the two run folders' four files and `qa/acceptance_results.json`. With this close-out's changes: those, plus this file, the spec, `README.md` and the four `PP-*` files. Paths outside the list: none. Over `paper_live`, `grokteam`, `docs/asset_expansion/cards` and the eleven harness sources of `core/quant/gate_package.py:36-38`: nothing. Every `git diff` adds `':!docs/asset_expansion/cache'` (section 7, row 44) | met in the scratch clone before the commit; to be repeated on the closing commit |

### 11. Still open after Step 10

- The merge of `main` into this branch (ruling P3; decisions 13 and 13a), its cache-free full test, the report and push
  (answer X3), then the owner's confirmation sentence (decision 8; answer X4 if `main` moves first), then the owner's step
  F: the Windows full run of the merged branch with decision 7's three conditions, the results commit, his `--no-edit`
  merge into `main` and the push (decisions 7 and 9). Developer Mode (answer X5) is not needed for L2-5b, which passed at
  E; F1a still checks it. The owner's clone holds an untracked `.agents/skills/quantgen-paper/SKILL.md` that must leave
  the clone before F's clean-tree check (`gpt-e:53`).
- After the owner's merge: README's whole test table, a `bonds` row included, and the status snapshot are rewritten on
  `main` from the merged run's results file in one pull request (decisions 7 and 14; `prep` 3.3); the confirmation
  sentence is copied into `main`'s rulings log (decision 8).
- `detail.json` and the fetch folders of the provider parity runs stay on the owner's machine until he is asked again
  after Step 10 (decision 19); their final disposal is his (P-D7).
- The BTC-USD provider disagreement: the run of record stays FAIL and its cause is not identified (ruling BTC-라). The
  BTC-라 entry is in `main`'s `results/RULINGS.md` only, not in the run branch's copy (section 8).
- Python: the runbook still pins 3.13.14 (`RUNBOOK_windows.md:7`), while the owner's bridge interpreter has been 3.13.17
  since pilot 2 and, after the upgrade, its venv too (not verified). Whether the pin text changes is not decided; the
  runbook is outside the four kinds of path P2 allows.
- Spec Appendix B: written in this close-out, so not open. The entry `prep` 2.8 proposes, quoting P1 to P4, SPY-가 and
  BTC-나 and the decision table's answer, is the spec's Appendix B entry of 2026-11-17; it adds BTC-라 and the answer of
  2026-11-17 for D3 and D4 and lists what the closing commit changes (section 7, row 44 (e)).
- Decision 16 also puts the same data-access history into the rulings log as a self-report (`log-main:978`,
  `prep:1479-1481`). The 2026-11-12 listing is there already (`log-main:986-1000`); the helper's two walks of the
  protected folder (section 9; who ran them and where, their times, commands and output, and the helper's words come
  from the main session's conversation records) and the git commands of 2026-11-11 in non-sparse scratch worktrees are
  not. They go into `main`'s `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, outside the four kinds of path P2 allows on
  this branch; not written yet.
- The owner's answer of 2026-11-17 (D3, D4 and the rest) is verbatim in full in the handoff document only
  (`answer-1117`; the spec's Appendix B entry of 2026-11-17 quotes its first line); the main session plans a
  decision-record pull request on `main` after this close-out (handoff `CURRENT.md:45`). Not written yet.
- `main` and this branch differ in `config.py`, an input of `code_sha256` (`git diff --name-only cdbbe61 e01e152` over
  the `code_sha256` inputs lists `config.py` besides the bridge's own files, which `main` does not have yet). What the P3
  merge does with it belongs to that step (the rehearsal's code-hash check); not checked here.
- The deferred minor findings of this file (`record:243-248`) still stand, and so does the Step 8 wording point of
  section 8 (the card versus `run.json`), for the spec's next revision.
- The handoff ledger rows for 7-1 (⑦-1) and the closing commit's id are recorded after the commit, not here.
