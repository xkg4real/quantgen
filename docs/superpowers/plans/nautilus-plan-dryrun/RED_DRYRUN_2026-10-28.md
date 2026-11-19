# Nautilus plan: RED dry run record (②-2 stage C, 2026-10-28)

Each task ran in its own sparse scratch clone of HEAD `1f9c9e3` (T5-1 recipe; the four protected caches were skip-worktree entries and absent on disk). Earlier tasks' GREEN code was applied verbatim from the plan. The real clone was not modified.

## Task 1

The Task 1 RED dry run matched the plan at every RED point, so no edit is needed.

I ran it in a sparse scratch clone of HEAD 1f9c9e3 built with the T5-1 recipe. The four protected caches are skip-worktree 'S' entries and absent on disk; none was opened or hashed.

- **Step 3** (test module alone): Python cannot import `launch` from `tools.nautilus`, and the module exits 1, as planned.
- **Step 5** (after Step 4's `launch.py`): with the key unset, all 12 rows, the pyarrow line and `4/12 passed, 4 failed, 4 not run` with exit 1 match the plan. With the key set, the four L2 rows fail because `golden/env_pins.json` is missing, giving `0/4` and exit 1, as planned.
- **Step 10** (after Steps 6 to 9): with the key unset, the module gives `7/12 passed, 1 failed, 4 not run`, and the egress test fails because `egress_probe.py` is missing. With the key set, L2-1 and L2-8 fail because `sandbox.py` is missing, L2-9 fails with a JSONDecodeError, L2-10 passes, and the run gives `1/4` with exit 1, as planned.

The only differences were path prefixes, from substituting the clone root for /home/user/quantgen.

Every file and command check the plan states before Step 10 also held:
- `tests/nautilus_acceptance.py` md5 059691438a0adb121c782fb0d3f4dc9b;
- `launch.py` md5 c55ca113ea950f2333cd143be9a9b747;
- `requirements-nautilus.txt` sha256 7a720e24... with 43 lines, byte-equal to the plan's text block;
- `.env.example` md5 9969fe1e..., "6 insertions(+)" and "LF ok";
- the RECORD fixtures' md5s and sizes;
- MANIFEST.csv md5 f0d65970...;
- `env_pins.json` md5 fefda88c..., in the bridge's JSON bytes;
- `.gitignore` md5 54aed7ce...;
- the offline hashed install and `pip check` printed the expected lines.

The test code parses, imports only names Task 1 provides, and fails at each RED point for the reason the plan gives. The Count Ledger figures hold: 12 tests, 8 layer 1 and 4 layer 2. Steps 11 to 18 were not run. They come after the last RED point.

The clone is at /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task1/clone. /home/user/quantgen was not touched: `git status` is empty and its qa/acceptance_results.json md5 is still 16c9baa5a1777853521d485d5078e456. No full suite, ledger write, pip install into the global interpreter or commit took place.

| RED point | Matches | Observed |
|---|---|---|
| Step 1 check (setup before the first RED) | yes | ok |
| Step 3 (RED: Step 2's test module alone) | yes | Traceback ... File "<clone>/tests/nautilus_acceptance.py", line 35, in <module> from tools.nautilus import launch / ImportError: cannot import name 'launch' from 'tools.nautilus' (<clone>/tools/nautilus/__init__.py) / exit 1 |
| Step 5, first command (RED after Step 4's launch.py, key unset) | yes | The same 12 rows in the same order, with the same statuses and detail texts and the pyarrow line; then '4/12 passed, 4 failed, 4 not run' and 'exit 1' |
| Step 5, second command (RED after Step 4, key set) | yes | FAIL test_l2_01/08/09/10 each 'FileNotFoundError: [Errno 2] No such file or directory: '<clone>/tools/nautilus/golden/env_pins.json''; '0/4 passed, 4 failed, 0 not run'; 'exit 1' |
| Step 10, command 1 (RED after Steps 6 to 9, key unset) | yes | 7/12 passed, 1 failed, 4 not run |
| Step 10, command 2 | yes | FAIL test_px_egress_probe_imports_json_and_socket_only FileNotFoundError: [Errno 2] No such file or directory: '<clone>/tools/nautilus/egress_probe.py' |
| Step 10, command 3 (key set) | yes | FAIL test_l2_01_check_env_pins_identity_precision AssertionError: (2, "/tmp/claude-0/.../scratchpad/ntvenv_hash/bin/python: can't open file '<clone>/tools/nautilus/sandbox.py': [Errno 2] No such file or directory\n"); FAIL test_l2_08_guard_selftest_outcomes AssertionError: (2, '', "...same...\n"); FAIL test_l2_09_egress_probe_blocked JSONDecodeError: Expecting value: line 1 column 1 (char 0); PASS |

Prior GREEN applied: None. Task 1 has no prior task. I applied Task 1's own steps verbatim in the clone, each at its point. - Step 1: an empty tools/nautilus/__init__.py. - Step 2: tests/nautilus_acceptance.py, extracted from the plan's fenced block. 696 lines, md5 059691438a0adb121c782fb0d3f4dc9b, as the plan states. - Step 4 (GREEN, before the Step 5 RED): tools/nautilus/launch.py, extracted verbatim. 434 lines, md5 c55ca113ea950f2333cd143be9a9b747, as stated. - Step 6 (GREEN, before the Step 10 RED): requirements-nautilus.txt, built from the header heredoc plus $S/closure/requirements-nautilus.body.txt. sha256 is 7a720e24... with 43 lines, and the body is 49c1cee1...; both as stated. The file is byte-equal to the plan's text block. The offline --require-hashes install gave the expected "Successfully installed ..." line and "No broken requirements found." I wrote the heredoc temp file and the venv under the dry-run folder (plan_step2/red/task1/t1_req_header.txt and ntvenv_t1) rather than $S/t1_req_header.txt and $S/ntvenv_t1, so that no shared scratch file was overwritten. - Step 7: .env.example, changed with the Edit tool using the plan's old and new strings. The output was "1 file changed, 6 insertions(+)" and "LF ok", md5 9969fe1e6b8c5f9336a6fb87289ee5df, as stated. - Step 8: both RECORD fixtures, copied out of the wheels: bf0dd9ec... at 80255 bytes and 9cb7bcf1... at 78902 bytes, as stated. MANIFEST.csv has md5 f0d6597019cbd34e9abd03af82df12db, as stated. - Step 9: tools/nautilus/golden/env

## Task 2

Task 2's RED dry run passed: all three RED points and every intermediate check behaved as written. The one plan edit is for Step 1's commit grep.

RED points:
- **Step 3:** the two new T-RO-01 tests fail with NameError for NAUTILUS_SANDBOX, the registry test fails as quoted, the summary is 11/14, exit 1, and the skeleton md5 is 484ad92f.
- **Step 9:** L1-15 fails with NameError for encoding_offences, giving 0/1, exit 1.
- **Step 11:** `--suite nautilus` gives 0/0, exit 1, and the qa md5 stays 16c9baa5.

Intermediate checks that also matched word for word:
- **Step 6:** 13/14, only the registry test failing.
- **Step 7:** one registry row changed, the seven implemented_in lines, 14/14.
- **Step 8:** 0 hits, the four tools/nautilus files, test_08, test_09 and the flet guard ok (4).
- **Step 10:** L1-15 passes; 9/13 with the key unset, 13/13 with it set.
- **Step 13:** the run_all diff is 17/2; the import-failure line; the 15 key-unset lines; 13/13 with the key set.
- **Step 14:** the README diff is 2/1, the Total count is 0, the rows sit at lines 877 to 879, and macro_ui_components gives 11/11.

The numstats Step 16 expects already hold in the clone: README 2/1, harness 491/1, registry 1/1, nautilus_acceptance 67/0 and run_all 17/2.

The tests fail for their intended reasons. Each of the three mutations the plan cites makes its test fail: dropping F4, exempting every rule-A case, and removing api_key. `tests.macro_m1_fixtures` gives 13/15, as the notes say.

One edit, to Step 1: add -i to the case-sensitive commit grep, because Task 1's commit subject starts with lower-case "nautilus". Without it, T1 is empty and the start check fails.

Not edited, because they lie outside the RED scope, and reported here:
1. **Step 15 does not yet follow X-1 or X-2.** Its full run still calls `python3 -B $S/run_baseline.py $S/nb_task2_full.json` in the real clone instead of `bash "$S/full_run.sh" nb_task2_full`. It says "The only FAIL is B's environment-only papers/test_debate_run_kills_process_tree", but under the cache-free copy, B's FAIL set also holds `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`. Its comparison does not print the two clock and sign-off rows on their own line. X-1 names this edit as pending for Task 2's region.
2. **Coverage gap.** The T2-m3 lambda reading of rule A, under which a `self.submit_order` wrapped in a lambda is not exempt, is caught by none of the 51 controls. Reverting `_rule_a` to stop only at def still passes both T-RO-01 tests. The rule itself works: the direct lambda probe gives the A, CALL and TEXT tags. Adding a control would change the 51 of spec 8.5, so no edit is proposed.

Step 15's full run was not executed; it is not a RED step.

Files:
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/clone
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/step3_out.txt
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/run_baseline.py (the wrapper copy pointed at the clone)
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/nb_task2_red.json
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/nb_task2_nautilus.json
- /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/nb_task2_nautilus_key.json

| RED point | Matches | Observed |
|---|---|---|
| Task 2 Step 1 (start check, run without Task 1's commit) | NO | 16c9baa5...; 12/12 passed, 0 failed, 0 not run; 8/12 passed, 0 failed, 4 not run; 0 hits. In the clone, `git log --fixed-strings --grep` with a subject in the wrong case matched nothing; with `-i` it matched (git 2.43.0). Task 1 Step 18 commits the subject 'nautilus bridge, plan Task 1 (spec Step 3): ...' with a lower-case n, so the Step 1 grep finds no commit. T1 is then empty, and `git diff --na |
| Task 2 Step 3 (RED: harness module, then skeleton verbatim) | yes | Exactly the three FAIL lines. The registry line has 5 old entries against the 7 new ones (the two new tests added), with timing (1.6s). The two NameError lines are word for word, with (0.0s). Then 11/14 passed, 3 failed, 0 not run; exit=1. The stderr traceback ends `NameError: name 'NAUTILUS_SANDBOX' is not defined`. Then `skeleton verbatim 484ad92fbf352616078f26be4ff41121`. |
| Task 2 Step 6 (intermediate check after Steps 4 and 5: only the registry test fails) | yes | PASS test_t_ro_01_nautilus_allowlist_pinned (0.0s); PASS test_t_ro_01_nautilus_confined_to_the_sandbox (0.5s); PASS test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path (4.5s); the registry FAIL line; 13/14 passed, 1 failed, 0 not run; exit=1. |
| Task 2 Step 9 (RED: L1-15 before encoding_offences exists) | yes | FAIL test_l1_15_encoding_rules_hold NameError: name 'encoding_offences' is not defined, a blank line, 0/1 passed, 1 failed, 0 not run, exit=1 |
| Task 2 Step 11 (RED for 5.7: the nautilus suite is absent from the house runner) | yes | A blank line, then `0/0 passed, 0 failed, 0 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task2/nb_task2_red.json`, then exit=1. Both md5 lines 16c9baa5...; the output file holds []. |

Prior GREEN applied: Task 1 was applied in full and verbatim; no stubs were needed, because Task 1 gives every file whole. Every file was checked against the plan's md5: - Step 1: tools/nautilus/__init__.py, 0 bytes. - Step 2: tests/nautilus_acceptance.py, md5 059691438a0adb121c782fb0d3f4dc9b, 696 lines. - Step 4: tools/nautilus/launch.py, md5 c55ca113ea950f2333cd143be9a9b747. - Step 6: requirements-nautilus.txt (header block plus $S/closure/requirements-nautilus.body.txt), sha256 7a720e24..., 43 lines; the body sha256 is 49c1cee1.... - Step 7: the .env.example edit, made with the Edit tool; md5 9969fe1e6b8c5f9336a6fb87289ee5df, 6 insertions, LF. - Step 8: both RECORD fixtures copied out of the wheels (md5 bf0dd9ec..., 80255 bytes; md5 9cb7bcf1..., 78902 bytes) and MANIFEST.csv (md5 f0d65970...). - Step 9: tools/nautilus/golden/env_pins.json (md5 fefda88c...) and docs/nautilus_bridge/.gitignore (md5 54aed7ce...). - Step 11: tools/nautilus/egress_probe.py, md5 39eda690.... - Step 12: tools/nautilus/sandbox.py, md5 5818b883....  Task 1 GREEN was confirmed in the clone: the module CLI gave 8/12 passed, 0 failed, 4 not run (exit 0) with the key unset, and 12/12 with QUANTGEN_NAUTILUS_PYTHON=$NTPY. Task 1 has no run_all.py, registry or harness edits.  Task 2 GREEN steps applied at their points: - Step 4 (the 5.6 constants after ALLOWED_BARE_CALLS) and Step 5 (rules A to F), both by exact unique-string replacement from the plan text. The harness numstat is 491/1, as Step 16 expects. - Step 7: registry 

## Task 3

The Task 3 RED dry run matches the plan at every point, so I propose no edits. I ran it in a sparse scratch clone built with the T5-1 recipe; the four cache paths are skip-worktree entries, absent on disk.

Before running anything I applied every GREEN block of Tasks 1 and 2 verbatim. All published md5s, numstats and CRLF/LF checks matched, the registry resync changed exactly one row, and Task 3 Step 1's checks printed what the plan says. The only difference is the HEAD subject, because a dry run commits nothing.

- **Step 2 (test block):** it parses and adds 471 lines with 0 deletions.
- **Step 3 (first RED point):** key unset gives `0/5 passed, 2 failed, 3 not run`; key set gives `0/3 passed, 3 failed, 0 not run`; the whole module gives `9/18 passed, 2 failed, 7 not run`, with L1-15 and L1-32 passing.
- **Step 4 (GREEN):** the `fixture_inputs` block adds 51 lines with 0 deletions.
- **Step 5:** the fixture test and L1-15 give `2/2 passed`, and the key-set RED run gives `0/4 passed, 4 failed, 0 not run`.

At both RED points every expected line, including each failure message, matched what I observed. Every failure has the intended cause: first the missing `FIXTURES` and `fixture_inputs`, then Task 1's sandbox, which has no Port classes and refuses every input silently with exit 20. No test fails for an unintended reason, and no expected text is wrong.

The real clone /home/user/quantgen was not touched: its `git status` is empty and `qa/acceptance_results.json` keeps md5 16c9baa5.

| RED point | Matches | Observed |
|---|---|---|
| Task 3 Step 3, first bullet (key unset) | yes | Exactly the expected six lines, the blank line and '0/5 passed, 2 failed, 3 not run'; exit=1. stderr holds 2 tracebacks, one before each FAIL line. |
| Task 3 Step 3, second bullet (key set) | yes | Identical: three FAIL lines with that AttributeError, the blank line and '0/3 passed, 3 failed, 0 not run'; exit=1. stderr holds 3 tracebacks. |
| Task 3 Step 3, third bullet (whole module, key unset) | yes | '9/18 passed, 2 failed, 7 not run'; exit=1. PASS: L1-15, L1-16, L1-17, L1-22 (with its line '  pyarrow in the global interpreter: None'), the four Task 1 px tests and L1-32 (last). NOT_RUN: L2-01, 04, 05a, 05b, 08, 09, 10. FAIL: the two px tests, with the same details as the first bullet. |
| Task 3 Step 5, first bullet (GREEN check after Step 4, run at the RED point) | yes | PASS test_l1_15_encoding_rules_hold; PASS test_px_fixture_inputs_follow_6_1_and_8_2; blank line; '2/2 passed, 0 failed, 0 not run'; exit=0; stderr empty. |
| Task 3 Step 5, second bullet (RED point after GREEN Step 4) | yes | Identical: the four FAIL lines word for word, the blank line and '0/4 passed, 4 failed, 0 not run'; exit=1. stderr holds 4 tracebacks. |

Prior GREEN applied: Every Task 1 and Task 2 GREEN block was applied verbatim, extracted by line range from the plan. Tasks 1 and 2 give every function in full, so no stub was needed. Every published md5 and numstat matched.  Task 1: - Step 1: tools/nautilus/__init__.py, 0 bytes. - Step 2: tests/nautilus_acceptance.py, md5 059691438a0adb121c782fb0d3f4dc9b, 696 lines. - Step 4: tools/nautilus/launch.py, md5 c55ca113ea950f2333cd143be9a9b747. - Step 6: requirements-nautilus.txt, the heredoc header plus $S/closure/requirements-nautilus.body.txt. sha256 7a720e24..., 43 lines; the bytes equal the plan's text block. - Step 7: the .env.example edit, md5 9969fe1e6b8c5f9336a6fb87289ee5df, LF. - Step 8: both RECORD fixtures taken from the closure wheels (bf0dd9ec..., 80255 bytes; 9cb7bcf1..., 78902 bytes) and MANIFEST.csv (f0d65970...). - Step 9: tools/nautilus/golden/env_pins.json (fefda88c...) and docs/nautilus_bridge/.gitignore (54aed7ce...). - Step 11: tools/nautilus/egress_probe.py (39eda690...). - Step 12: the Task 1 part of tools/nautilus/sandbox.py (5818b883...).  Task 2: - Step 2: tests/macro_m0_harness.py Edit A (import hashlib) and Edit B (the skeleton, helpers and two tests before test_t_ro_01_artifact_writers_stamp_read_only). - Step 4: the 5.6 constants and rule B after ALLOWED_BARE_CALLS. - Step 5: rules A to F, with `return _nautilus_offences(tree, rel, hits)`. - After Step 5 the harness gave 13/14, with only the registry test failing, as Step 6 expects. - Step 7: `python3 -B -m tests.macro_

## Task 4

The RED dry run of Task 4 matches the plan at every RED point, so no plan edit is needed.

Starting state: a T5-1 sparse clone of HEAD 1f9c9e3. The four cache CSVs are skip-worktree (`S`) and absent on disk. Tasks 1 to 3 are applied verbatim, and every file matches the plan's md5 or sha256. The harness gives `14/14`, and the module gives `11/18` with the key unset.

Results at each RED point:
- **Step 2:** the module gives `11/42 passed, 21 failed, 10 not run` with the key unset and `18/42 passed, 24 failed, 0 not run` with it set. The 21 layer-1 tests and L2-2, L2-3 and L2-6 fail with exactly the stated ImportError. The pyarrow line sits where Plan ruling T4-R1 says. The key-set run took 1 min 47 s against the plan's "about 1.5 minutes".
- **Step 3:** the stub check on F1 and F2 prints the two expected lines byte for byte. With the stub present and the runner still missing, the module rows equal Step 2's.
- **Step 4:** with the runner created (md5 01b576997547d17d8f318fb67f26bac6, the value Task 5 relies on), the key-unset run gives the one L1-33 FileNotFoundError and `31/42`. The key-set run of the four tests gives the four stated FAIL lines and `0/4`.
- **Step 5:** `--write-goldens` writes goldens with the stated md5s. L2-6 then remains the one FAIL (`3/4`), and the repeat prints the `matches` and `never overwritten` lines.
- **Step 6:** `--record-baseline` writes a census of 942 names with md5 b7bccf50..., and L2-6 passes.
- **Step 8:** the module gives `32/42` with the key unset and `42/42` with it set.

Throughout, the real clone stayed untouched and `qa/acceptance_results.json` kept its md5.

One observation is outside the RED scope, so I made no edit for it. Task 4 Step 7 still spells `git clone -q /home/user/quantgen "$S/clone_task4"`, followed by `rm -f` of the four caches. That plain clone writes the four files to disk before they are deleted. Ruling T5-1 says this line is to be read as the sparse recipe, so an executor must substitute the T5-1 recipe there. If you want the text itself aligned with T5-1, that would be a separate edit.

| RED point | Matches | Observed |
|---|---|---|
| Task 4 Step 2 RED, key unset | yes | Exactly that, with the clone root in place of /home/user/quantgen. There are 21 ImportError FAIL lines in the stated order, the pyarrow line between 20a and 23, then the 10 NOT_RUN lines, an empty line and `11/42 passed, 21 failed, 10 not run`. The module exited 1. |
| Task 4 Step 2 RED, key set | yes | The three FAIL test_l2_02/03/06 lines, each with ImportError: cannot import name 'runner' from 'tools.nautilus' (<clone>/tools/nautilus/__init__.py), then `18/42 passed, 24 failed, 0 not run`. The full output has 21 FAIL test_l1 lines, all with that ImportError. The module exited 1, wall time 1 min 47 s. |
| Task 4 Step 3 stub check, the runner not yet created | yes | The same two lines, byte for byte. I then re-ran the key-unset module with the stub present and runner.py moved aside. Its non-PASS output is identical to Step 2's (diff empty). |
| Task 4 Step 4 RED point (runner created; no golden or baseline yet), key unset | yes | Exactly that line with the clone root, then `31/42 passed, 1 failed, 10 not run`. The module exited 1 after 18 s. |
| Task 4 Step 4 RED point, key set, four tests | yes | The four FAIL lines exactly as expected: L1-33 and L2-02 name golden/F1.json, L2-03 names golden/N1.json, and L2-06 gives the stated AssertionError. Then `0/4 passed, 4 failed, 0 not run`. Exit 1. |
| Task 4 Step 5 (the remaining RED is L2-6 after the goldens are written), in the scratch clone | yes | Every line as expected. The md5s are 6525ecbe771351571469df533c1c3c6c, 85199e69206182532ac8b5080e0b0150 and 0fc7830cf871e00a2f3a6cc891ceff03. The -k run gives three PASS lines, then `FAIL test_l2_06_census_matches_platform_baseline AssertionError: no census baseline ...` and `3/4 passed, 1 failed, 0 not run`. The repeat's last seven lines are exactly as expected. |
| Task 4 Step 6 (census baseline; the final residual RED turns green), in the scratch clone | yes | Every line as expected, including 942 `+ ` lines and md5 b7bccf501c8d1ca982dd4a429d407df0. |
| Task 4 Step 8 (GREEN confirmation of the test code written at Step 2) | yes | Key unset: the 10 NOT_RUN lines and `32/42 passed, 0 failed, 10 not run`. Key set: only `42/42 passed, 0 failed, 0 not run`, after 2 min 5 s. |

Prior GREEN applied: Everything for Tasks 1 to 3 was applied verbatim from the plan's code blocks. No stubs were needed, because the plan gives every function body in full. Each file was checked against the md5 or sha256 the plan states.  Task 1: - `tools/nautilus/__init__.py`: 0 bytes. - `tests/nautilus_acceptance.py`: block at plan line 1101, md5 059691438a0adb121c782fb0d3f4dc9b. - `tools/nautilus/launch.py`: block 1808, md5 c55ca113ea950f2333cd143be9a9b747. - `requirements-nautilus.txt`: the Step 6 header from the heredoc plus `$S/closure/requirements-nautilus.body.txt`. 43 lines, sha256 7a720e24..., byte-equal to the plan's text block 2273. - `.env.example`: the Step 7 edit, md5 9969fe1e6b8c5f9336a6fb87289ee5df. - Both RECORD fixtures, extracted from the wheels in `$S/closure`: md5 bf0dd9ec... and 9cb7bcf1.... - `tests/fixtures/nautilus/MANIFEST.csv`: md5 f0d65970.... - `tools/nautilus/golden/env_pins.json`: md5 fefda88c.... - `docs/nautilus_bridge/.gitignore`: md5 54aed7ce.... - `tools/nautilus/egress_probe.py`: block 2434. - `tools/nautilus/sandbox.py`, Task 1 part: block 2467. Task 3 replaces it.  Task 2: - `tests/macro_m0_harness.py`: Edit A (`import hashlib`), Edit B (the 2825 block before `def test_t_ro_01_artifact_writers_stamp_read_only():`), Step 4's constants after `ALLOWED_BARE_CALLS`, and Step 5's rules A to F. Numstat 491/1, as the plan says. - `tests/macro_registry.csv`: resynced with `python3 -B -m tests.macro_acceptance`. It printed `implemented_in rows changed: 1`; numstat 1/

## Task 5

The RED dry run of Task 5 matched the plan at every RED point, and the plan needs no edit.

I made a sparse scratch clone with the T5-1 recipe. `git ls-files -t` shows the four protected caches as 'S' (skip-worktree) entries, and none of them is on disk. I applied every GREEN code block of Tasks 1 to 4 verbatim, together with their file edits and generated files:
- the .env.example edit, the RECORD fixtures and their manifest;
- the macro_m0_harness edits and the registry resync;
- the tests/run_all.py and README.md edits, kept CRLF;
- the goldens from --write-goldens and the census baseline from --record-baseline.

No stubs were needed, because the plan gives every function in full. Every md5 and sha256 the plan states for those files matched: launch, sandbox, runner, stub, the goldens and the census baseline among them.

Task 5 Step 1's checks gave 3, 1 and `32/42 passed, 0 failed, 10 not run`. Step 2's block added 640 insertions and 0 deletions, which is the plan's numstat check. The file's md5s differ from the dry-run md5s, as the plan says they would for a file built from the plan.

The three RED points all matched their expected output line for line, with the clone root standing in for `<repo>`:
- **Step 3 (key unset):** `0/15 passed, 12 failed, 3 not run`, with the stated ImportError, G-06 and FileNotFoundError details.
- **Step 3 (key set):** `0/3 passed, 3 failed, 0 not run`, in about 50 s.
- **Step 6** (after Steps 4 and 5): `9/12 passed, 3 failed, 0 not run`, plus the N7 (i) line ending `max 0.07667`. parity.py has md5 71258dfa...
- **Step 8** (after Step 7, with the runner at md5 bffca79a...): the R-11, `exit 2`, `exit 2`, `STATUS REFUSED` and `exit 2` lines, and the R-03 text for `--timing`. No file was written.

Test ledgers were written only to /tmp temp dirs. /home/user/quantgen is unchanged and nothing was committed. The work files are in /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/plan_step2/red/task5/work, including s3a.out/err, s3b.out/err, s6.out/err and the extraction helpers.

| RED point | Matches | Observed |
|---|---|---|
| Task 5 Step 3, command 1 (key unset) | yes | The same 15 lines, line for line and in the same order, with <repo> = the clone root. Summary: 0/15 passed, 12 failed, 3 not run. Took 5 s. Every matched line came from stdout; stderr held only tracebacks. |
| Task 5 Step 3, command 2 (key set) | yes | Identical lines with <repo> = the clone root. Summary: 0/3 passed, 3 failed, 0 not run. Took 49.5 s. |
| Task 5 Step 6 (after GREEN Steps 4 and 5: parity.py and the seam) | yes | The same 12 lines with <repo> = the clone root. Summary: 9/12 passed, 3 failed, 0 not run. N7 line: `N7 (i): P12 2x {'corr': 0.9989206568469223, 'abs_dsr': 0.07763231205006826, 'pass': False, 'owner_pass': False}; P3 at 2x per column, max 0.07667 (bar 0.01)`. Took 12.7 s. |
| Task 5 Step 8 (after GREEN Step 7: the three runner edits; before the tables exist) | yes | Identical, line for line. A full `--timing` run printed `R-03: QUANTGEN_NAUTILUS_PYTHON is not set` and the R-03 remedy, then STATUS REFUSED exit=2 record=-, exit 2. No file was written: the untracked count went from 17 to 18, the one addition being parity.py. |

Prior GREEN applied: Every Task 1 to 4 block was applied verbatim from the plan. No stubs were needed, because the plan gives every function in full. Every md5 I could check matches the plan.  Task 1: - tools/nautilus/__init__.py: 0 bytes. - tests/nautilus_acceptance.py: fence 1101, md5 059691438a0adb121c782fb0d3f4dc9b. - tools/nautilus/launch.py: fence 1808, md5 c55ca113ea950f2333cd143be9a9b747. - requirements-nautilus.txt: fence 2273, sha256 7a720e24..., 43 lines. - .env.example: Step 7 edit, md5 9969fe1e6b8c5f9336a6fb87289ee5df. - Both RECORD fixtures: extracted from the $S/closure wheels with Step 8's command (bf0dd9ec..., 9cb7bcf1...). MANIFEST.csv: f0d65970.... - env_pins.json: fefda88c.... docs/nautilus_bridge/.gitignore: 54aed7ce.... - egress_probe.py: 39eda690.... sandbox.py (Task 1 part): 5818b883....  Task 2: - tests/macro_m0_harness.py: Edits A and B of Step 2, Step 4 (constants after ALLOWED_BARE_CALLS) and Step 5 (rules A to F). Numstat is 491/1, and the harness gave 13/14 before the resync, as Step 6 expects. - Step 7: `python3 -B -m tests.macro_acceptance` reported `implemented_in rows changed: 1`, the registry diff was 1+/1-, and the harness then gave 14/14. - tests/nautilus_acceptance.py: L1-15 (Step 9) and encoding_offences (Step 10) inserted before `def tests(`, 67 lines in all. - tests/run_all.py: the three CRLF edits of Step 12, numstat 17/2, CRLF ok. - README.md: the two CRLF edits of Step 14, numstat 2/1, CRLF ok. - run_all.tests() now collects 891 rows, 13 of them nautilu
