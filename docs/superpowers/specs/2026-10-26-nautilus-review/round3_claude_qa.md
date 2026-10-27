# Round 3 referee report: QA lens (Claude)

Spec under review: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 3 (working tree; HEAD
`7112351` holds Revision 2). Repository code: QUANTGEN at `7112351`. Nautilus: `nautilus_trader` 1.231.0 in
`scratch:ntvenv`. `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
Spec lines are `spec:<line>`. My probes are in `scratch:referee3_qa/`.

Lens: is every done-when testable and unambiguous? Do fixtures and goldens reproduce? Does every guard have a
negative control that cannot pass for the wrong reason? Is any test vacuous? Does the suite follow house conventions,
and does no test write production state?

## Verdict

**AGREE**, with 12 minor concerns.

Revision 3 closes every issue I raised in rounds 1 and 2:
- The of-record refusals are pure functions on temp roots.
- The stub child and the missing seams are specified.
- The freshness clash in L1-5 is resolved.
- The DGS3MO blanks are handled.
- The step order no longer needs code from later steps for the tests I flagged.

I re-measured the parts that carry numbers, and all of them reproduce:
- F1, F2 and N1 through the exact launch contract;
- both self-check modes;
- the synthetic-series md5s;
- the `cents` rule against `Money`;
- both wheel identities;
- all 52 scan controls and both pin digests.

An engineering team can start Step 2 today. The minor items below are one-sentence fixes. None needs an owner ruling
or a design change. Five of them (QA-R3-1 to QA-R3-5) should be folded in before the Step 6 and Step 7 RED tests are
written, because otherwise a done-when cannot pass or a control can pass for the wrong reason.

## Sections reviewed

- Status, Inputs, Owner context, section 2 (O1 to O15) (spec:1-104).
- 3.1 to 3.12, with focus on 3.3 hermeticity, 3.7 encoding, 3.8 never concurrent and 3.9 unseen windows
  (spec:105-220).
- 4.1 to 4.4: processes, data flow, launch contract, egress (spec:221-296).
- 5.1, and 5.2.1 to 5.2.9, including the new skeleton (spec:299-622).
- 5.3.1 to 5.3.5: modes, pure steps, seams, order of operations, reconstruction, lifecycle (spec:624-737).
- 5.4 parity, 5.5 hand-off (spec:739-822).
- 5.6 T-RO-01 amendment, 5.7 suite, 5.8 file table (spec:824-965).
- 6.1 to 6.8 data model (spec:967-1115).
- 7 error handling: every row and its control (spec:1117-1166).
- 8.1 to 8.6 testing, including the stub child, the series code, and every L1 and L2 row (spec:1168-1352).
- 9: Steps 1a to 10, including 7A (spec:1354-1432).
- 10.1 to 10.4, 11, 13, and Appendix B (spec:1434-1663).

Probes, all on synthetic data, with no ledger row written and the tree unchanged:
- **Fixtures.** `drive_fx.py` builds F1, F2 and N1 inputs from 6.1 and 8.2 myself. It runs them through 4.3's POSIX
  argv and environment (`unshare -rn`, `-I -B -X utf8 -X importtime`, `env` limited to the five keys) against the
  author's filled skeleton, `scratch:rev3_probe/sandbox_spec_filled.py`.
- **Skeleton.** `skeleton_extracted.py` is spec:487-621 cut verbatim. `imports_check.py` resolves every import in
  the venv and builds the msgspec config subclasses.
- **Schema.** `schema_gap.py` sends single-field perturbations of F1's `input.json`.
- **Series.** `synth_check.py` runs the series code of spec:1257-1265.
- **Money.** `cents_check.py` compares spec:769's `cents` with `Money` on 140,006 values.
- **Identity.** `ident.py` runs the 6.7 identity rule on both wheels.
- **Scan.** `scan3_copy.py` is the author's prototype, with my verbatim skeleton as the positive control.

## Earlier issues

Round 1:
- QA-1: resolved. The pure functions `take_lock`, `check_table`, `check_tree` and `check_egress_record` run on temp
  roots. Seams are refused in argument validation, before step 0. L1-19 asserts that no `.locks` folder is created. The
  guard digests both ledger paths (spec:134-138, 649-663, 1289).
- QA-2: resolved. The 6.8 format is defined. N1 re-measured: 1 row, BUY 1000 @ 100.00, commission 500.00; 904501.00;
  quantity 1000; 4 of 12 bars; force stop; exit 10.
- QA-3: resolved. Moot: N3 is retired.
- QA-4: resolved. 6.1 separates what the child accepts from the pilot values, and step 1 asserts the pilot values.
- QA-5: resolved. 6.6 has `start` and `end`, and step 5 filters by date text before parsing.
- QA-6: resolved. The evidence is the hash echo, and times have microseconds. A Step 8 wording remnant is in QA-R3-12.
- QA-7: resolved. `run()` has the `timeout`, `register_fn`, `score_fn` and `hooks` seams. The stub contract is in 8.1.
  `check_tree` takes `anchor_fn`, and `repo_anchor(root)` takes a root (`core/quant/gate_ledger.py:122`). A residual
  seam is in QA-R3-7.
- QA-8: resolved. Every row has a control or a reason. Two controls are weaker than they look (QA-R3-2, QA-R3-4).
- QA-9: resolved.
- QA-10: resolved. Recomputed: `a448cd20…f03f9` and `47d274d7…39555`, 764 entries each.
- QA-11: resolved. Census of F1 = F2 = N1: 942 names, identical hash.
- QA-12: resolved. `stats_pnls_empty` is true in all three manifests.
- QA-13: resolved.
- QA-14: resolved. `--check-env` reports `QUANTITY_MAX` and `PRICE_MAX` as floats. `int(x) + 1` still exceeds them.
- QA-15: resolved. All 52 multisets of 8.5 reproduce, with 0 real-tree hits.
- QA-16: resolved.
- QA-17: resolved.
- QA-18: resolved.
- QA-19: resolved.
- QA-20: resolved. Moot.
- QA-21: resolved.

Round 2:
- QA-R2-1: resolved. Same evidence as QA-1.
- QA-R2-2: resolved. Stub child, keywords, the L1-3 pass rule and the G-03 reason text are all specified. Residuals are
  in QA-R3-5 and QA-R3-6.
- QA-R2-3: resolved. L1-5 sets the mtime back with `os.utime`, and L1-25 has the 601-second pass case.
- QA-R2-4: resolved. The runner's `dropna().reindex(ffill) / 100 / 252` equals the study's `fred()` (which drops NaN,
  `docs/asset_expansion_study.py:94-104`) followed by `rf_daily` (`:148-153`), whenever there is no leading NaN.
- QA-R2-5: resolved for the tests I named. One new instance is in QA-R3-1.
- QA-R2-6: resolved. A residual about reason strings is in QA-R3-8.
- QA-R2-7: resolved. `cents` matches `Money` on 140,006 values, 40,000 exact half-cent ties among them.
- QA-R2-8: resolved.
- QA-R2-9: resolved.
- QA-R2-10: resolved.
- QA-R2-11: resolved.
- QA-R2-12: resolved. Both md5s reproduce: `adb735b9…` and `7b53fe60…`. The N6 range is 79.53 to 556.04, maximum
  677.47. The planted ratios are exactly 1.1 and 0.9. Every planted bar is a decision bar of all 12 columns.
- QA-R2-13: resolved.
- QA-R2-14: resolved. `require_fixture(name, *, manifest=...)` accepts the new manifest (`tests/notrun.py:68`). See
  Notes for its header.

## New issues

All are minor.

### QA-R3-1 (minor): two tests are placed before the code they need

- **Section:** 9 Steps 5 and 6; 8.3 test 5; 8.4 tests 4, 5a and 5b; 5.8.
- **Problem:**
  - L1-5 cannot pass at Step 6.
  - Step 5's tests need fixture inputs, and no builder for them exists before Step 6.
- **Evidence:**
  - **L1-5.**
    - The Step 6 done-when lists L1-5 (spec:1367).
    - L1-5 needs the second run of a table to be refused by R-17 (spec:1275).
    - R-17 does not refuse after an earlier `ERROR` record (spec:1141).
    - `parity.py` and 5.5 are built at Step 7 (spec:948, 1368). So a Step 6 run cannot pass steps 16 and 17. It ends
      `ERROR` by G-06 (spec:1162), or never starts if the runner imports `parity` eagerly. Either way the second run is
      not refused.
  - **Step 5 inputs.**
    - Step 5 needs L2-4, L2-5a and L2-5b (spec:1366). Each needs F1 or F2 `input.json` and `bars.csv`.
    - The only builder the spec names is `runner --fixtures` (spec:641-642), which is built at Step 6 (spec:948).
- **Proposed fix:**
  - Move L1-5 to Step 7. Alternatively, at Step 6 it plants a finished `CARD_WRITTEN` record as the "first run", and
    the two-run form waits for Step 7.
  - Put `fixture_inputs(name) -> (input_bytes, bars_bytes)` for F1, F1r, F2 and N1 into `launch.py`, built at Step 5.
    L2-4, L2-5a, L2-5b, `--fixtures`, `--write-goldens` and L1-33 all use it, so there is one builder.

### QA-R3-2 (minor): the doctored-manifest controls of child-side checks can pass for the wrong reason

- **Section:** 7 C-03, C-04 and C-15; 5.4.1 P13; 8.1 stub `--doctor`; 8.3 test 27.
- **Problem:** C-03, C-04 and C-15 are caught in the child. Their only control is a doctored stub manifest. If the stub
  writes `valid: false` and exits 10, the parent marks the run INVALID through C-06 ("non-zero exit"). That happens
  whatever the parent does with `orders_not_filled`, `denied`, `rejected` or `strategy_started`. A parent that ignores
  those fields passes L1-27.
- **Evidence:**
  - C-03, C-04 and C-15 have "Caught by: child", and their control is "L1-27 (doctored manifest)" (spec:1144-1145,
    1156).
  - C-06 covers any non-zero exit (spec:1147).
  - P13 says only that "the child's checks (5.2.7) … all pass" (spec:763). It does not say whether the parent
    re-derives them.
- **Proposed fix:**
  - The parent re-derives C-01 to C-04 and C-15 from the manifest's `result` fields and `strategy_started`. These are
    `force_stop`, `bars_seen` against `bars_fed`, `backtest_end`, `orders_not_filled`, `denied` and `rejected`.
  - The parent marks the run INVALID with that id even when `valid` is true and the exit code is 0.
  - `--doctor C-03|C-04|C-15` writes `valid: true` and exits 0.
  - L1-27 asserts the specific id in the run record.

### QA-R3-3 (minor): the re-run guard's table key is ambiguous, and one reading has a bypass

- **Section:** 5.3.5, 6.6, 7 R-16 and R-17, 8.3 test 5, Step 7A.4.
- **Problem:** The lock and the run id use the SHA-256 of the table's bytes. Earlier runs are matched by "the same
  table SHA-256". If that means bytes, then two routine actions make R-17 see no earlier run, so it neither refuses nor
  records `supersedes`:
  - a new `owner_confirmed`, which Step 7A.4 requires after any code change;
  - a whitespace edit in Notepad.

  Two runners on the same table with different bytes also take different locks.
- **Evidence:**
  - The run id and the lock use `sha256(table bytes)` (spec:716, 719).
  - Earlier runs are matched by "the same table SHA-256" (spec:727).
  - `table_sha256` is canonical, without the owner fields (spec:1065-1066).
  - A code change needs a new `owner_confirmed` (spec:1413-1414).
  - L1-5 has no case where the bytes differ but the table does not (spec:1275).
- **Proposed fix:**
  - Use `table_sha256` for the lock name, the run-id suffix and earlier-run matching.
  - Record both hashes.
  - L1-5 adds a second run whose table differs from the first only in `owner_confirmed` or in whitespace. It must
    still be refused by R-17.

### QA-R3-4 (minor): L2-5a pins 4 of 6.1's refusal rules; a sandbox that ignores the rest passes

- **Section:** 6.1, 7 C-05, 8.4 test 5a, 5.2.9 and 5.4.3 (evidence claims).
- **Problem:** 6.1 says the child refuses "everything else, unknown and missing fields included, with exit 20"
  (spec:971). L2-5a tests volume, capital, precision and `bars_sha256` only (spec:1312).
- **Evidence:** I ran `schema_gap.py` on the filled skeleton, which the spec cites as reproducing the fixtures and
  behaving on refusals (spec:482-484, 798):

  | Input change | Exit |
  |---|---|
  | Unknown field | 0 |
  | Schema string `"nautilus-bridge-input/9"` | 0 |
  | `stress` `"3"` | 0 |
  | Ledger hash `"xyz"` | 0 |
  | Missing ledger hash | 1 |
  | Close with 2 decimals at precision 9 | 1 |

  The same file passes all four L2-5a cases. The parent's echo checks (C-11, C-14, P7) limit the harm, so this is
  defence in depth. It is still the guard that C-05 names.
- **Proposed fix:** L2-5a iterates a table of single-field perturbations of F1's input, one per 6.1 rule. Each case
  expects exit 20. The rules to cover:
  - an unknown field, and each field missing;
  - a wrong type;
  - each range bound;
  - the schema string;
  - the close decimals, `n_bars`, and non-increasing timestamps;
  - the ledger-hash format.

  Each case costs about 1 s.

### QA-R3-5 (minor): layer-1 runner tests need a stub probe, and the stub child has no probe mode

- **Section:** 4.4 probe, 5.3.1 `probe_cmd`, 5.3.2 step 4, 8.1 stub child.
- **Problem:**
  - Step 4 launches the egress probe in both modes. Layer 1 has no venv.
  - The stub child's flags have no probe mode, and no runner test row says it passes `probe_cmd`.
  - Consider a runner that takes the probe's interpreter from `child_cmd`. On Linux it passes layer 1, because
    `unshare -rn` blocks even the global interpreter. On Windows the global interpreter has no firewall rule. It would
    connect, and every stub-based runner test would refuse with R-14 in the suite of record at Step 7A.
- **Evidence:**
  - Step 4 runs the probe in both modes (spec:287-288, 673).
  - The `probe_cmd` seam is defined at spec:659.
  - The stub's flags are listed at spec:1183-1185.
  - The only hint is "or a stub probe a test writes into its temp dir" (spec:1173-1174).
  - The firewall rule binds only `py313\python.exe` (spec:279-280).
- **Proposed fix:**
  - The stub child gains `--probe`, which prints `{"blocked": true, "errno": 101, "error": "stub"}` and exits 0.
  - Every layer-1 runner test passes both `child_cmd` and `probe_cmd`.
  - The runner never derives the probe's argv from `child_cmd`.

### QA-R3-6 (minor): `run()`'s KeyboardInterrupt contract is unstated, and the suite catches only `Exception`

- **Section:** 4.3 process row, 5.3.5 final write, 8.3 tests 26 and 27.
- **Problem:** Suppose `run()` writes `ABORTED` and then re-raises, which is the natural way to handle Ctrl-C. A
  layer-1 test that does not catch the exception then ends the owner's whole suite of record. The suite stops before
  `qa/acceptance_results.json` is written, and before the guard's last digest test runs.
- **Evidence:**
  - `run_child` re-raises (spec:262).
  - The final write "catches `BaseException`" (spec:725-726). The spec does not say whether `run()` then returns 5 or
    re-raises.
  - L1-26 and L1-27 expect "exit 5" (spec:1296-1297).
  - `tests/run_all.py:115-121` catches `NotRun` and `Exception` only. `OUT` is written at `tests/run_all.py:137`.
- **Proposed fix:** State that `run()` returns its exit code (5 after `ABORTED`) and never re-raises, and that the CLI
  maps that code to `SystemExit`. The alternative is to require L1-26 and L1-27 to catch `BaseException` themselves.

### QA-R3-7 (minor): three seams that tests use are not named

- **Section:** 5.3.1 pure steps and seams; 5.3.2 step 7; 5.3.5 `write_record`; 8.3 tests 6, 20 and 34.
- **Problem and evidence:**
  - **`check_tree` has no mode.** `check_tree(repo_root, anchor_fn, git_exe)` takes no mode argument (spec:651), and
    `run()` has no `repo_root` (spec:654-656). So L1-6's "in rehearsal the same states are recorded, not refused" on a
    temp repository (spec:1276) has no entry point.
  - **P0a has no seam.** L1-20 needs "a doctored `study.rf_daily`" (spec:1290). But the runner loads the study by path
    inside step 7 (spec:676), and no keyword reaches it.
  - **`write_record` has no seam.** L1-34 needs "an `os.replace` seam" (spec:1304), but `write_record(path, obj)` has
    none (spec:722). Patching `os.replace` for the whole process also touches the 3.3 guard. In the "always raising"
    case, each write sleeps up to 5 s.
- **Proposed fix:**
  - `tree_refusal(findings, mode) -> "R-01" | "R-02" | None`.
  - A pure `check_p0a(study_module, cache_dir, arrays)` that `run()` calls with the loaded module.
  - `write_record(path, obj, *, replace=os.replace, sleep=time.sleep)`.

### QA-R3-8 (minor): `invalid_reasons` has no vocabulary, but goldens compare it exactly

- **Section:** 5.2.7, 6.8, 8.2 N1, 8.3 test 33.
- **Problem:** Goldens hold `invalid_reasons` and compare strings exactly (spec:1108-1110). L1-33 types "8.2's tables"
  into the test (spec:1303). But 8.2 gives N1's reasons only as "(C-01, C-02)" (spec:1239), and 5.2.7 defines no text.
  The filled probe writes "forced stop" and "bars seen fewer than bars fed". The run record's `withheld_reasons` also
  wants check ids (spec:1008).
- **Proposed fix:** Each reason begins with its section-7 id, for example `"C-01: forced stop"`. Goldens, L1-33 and
  the run record compare the ids.

### QA-R3-9 (minor): the crypto port's moving-average summation is unspecified

- **Section:** 5.2.5 port table; 8.1 stub child.
- **Problem:** The sma row requires a plain left-to-right loop, because `sum()` is compensated on Python 3.12 and later
  (spec:428). The crypto row writes `mean(P[i-n+1 : i+1])` (spec:429). The probe that the spec cites uses `sum()`
  (`scratch:rev3_probe/sandbox_spec_filled.py:127`). The stub child "applies 5.2.5's rule" (spec:1180), so the stub and
  the sandbox can differ at near-ties.
- **Proposed fix:** Use the same plain loop for the crypto moving averages, stated in that row. The stub uses it too.

### QA-R3-10 (minor): the stub child's launch on Windows is UNVERIFIED, and 13.1 does not list it

- **Section:** 8.1 stub child, 4.3 Windows environment, O9, 13.1, Step 7A.
- **Problem:** Every stub-based layer-1 test on the owner's machine launches the global interpreter through 4.3's
  six-key environment. O9 says that interpreter is the Microsoft Store Python. Whether its `sys.executable` (an
  app-execution alias) starts with that environment is UNVERIFIED. 13.1 asks the same question for the venv launcher
  only.
- **Evidence:**
  - The stub's argv is `[sys.executable, "-I", …]` (spec:1179).
  - The Windows environment rows are at spec:264.
  - O9 is at spec:97.
  - 13.1 is at spec:1537-1539.
- **Proposed fix:**
  - Add this to 13.1 and to Step 7A's checks.
  - Name the fallback: the stub argv uses `%LOCALAPPDATA%\quantgen\py313\python.exe`. The stub needs only the
    standard library.

### QA-R3-11 (minor): L2-7 and N6 state outcomes that nobody has measured

- **Section:** 8.2 N6, 8.4 tests 7 and 11, Step 7.
- **Problem:**
  - L2-7 expects "a card" (spec:1313). A card needs equal decisions and equal predicate dicts (spec:817).
  - N6 expects "every hard check passes" (spec:1244).
  - Only the series md5s were measured (spec:1251-1254). Neither outcome is marked UNVERIFIED.
  - Nothing says what to do if a predicate near its threshold flips. Without a rule, the tempting fix is a new seed.
- **Proposed fix:**
  - Mark both outcomes UNVERIFIED until Step 7.
  - If L2-7 ends WITHHELD, the engineer records the differing predicate and its two values in the execution record.
    The expectation then becomes "a card, or a WITHHELD record that names the predicate", never a seed chosen after
    seeing the result.

### QA-R3-12 (minor): two wording points carried from my round-2 notes

- **Census rule.** O13 states a subset rule: a module "outside the baseline's … sets" (spec:101). 5.2.7 states an
  equality rule: the set "differs from the platform baseline's" (spec:462-463). L1-12 tests only an extra name
  (spec:1282). Proposed fix: keep equality, reword O13, and add a missing-TP-name case to L1-12.
- **Step 8 done-when.** It still requires `registered_utc` to precede `first_child_utc` (spec:1430). That compares
  wall-clock fields, while 8.1 says no test does (spec:1177), and the ruled evidence is the hash echo. Proposed fix:
  say "at or before", or drop the clause.

## Why I agree or not

I agree. Every round-1 and round-2 issue from my lens is resolved, and the mechanisms they asked for now exist with
named controls:
- the pure refusal functions;
- the stub-child contract;
- the seams;
- the `--write-goldens` path;
- the measured `Money` rounding;
- the series generators;
- the second manifest.

Everything with a number reproduces exactly. That covers F1, F2 and N1 through the launch contract, the self-checks,
both identities, the series md5s, 140,006 `cents` cases, and all 52 scan multisets with 0 real-tree hits. The suite
registration still follows `tests/run_all.py`. Production state is protected by the 3.3 guard, the of-record seam
refusal before step 0, and temp-only ledgers.

The twelve items above are minor. None changes the design or needs an owner ruling, and a team can start Step 2 with
them open. QA-R3-1 to QA-R3-5 should be folded in before the Step 6 and 7 RED tests are written. Without that fold-in,
L1-5 cannot pass at Step 6, and three controls (C-03/C-04/C-15, C-05's schema part, and R-17 across a table re-save)
can pass while the guard they test is broken.

## Notes

- **Skeleton.** It parses, every import in it resolves in `scratch:ntvenv`, and
  `PortConfig(StrategyConfig, frozen=True)` accepts required fields after `StrategyConfig`'s optional ones. My
  verbatim cut equals `scratch:rev3_probe/skeleton_from_spec.py`.
- **Fixture measurements** (`drive_fx.py`):
  - **F1:** 4 fills; commissions 5000.00, 4800.00, 4752.00 and 4656.00; balance `926593.00`; `final_qty` `"0"`.
  - **F2:** quantities `1.00000000` and `0.98812079`; balance `50343.77`.
  - **N1:** exit 10, with -89.45 only in the stderr log line.
  - Prices print as `"100.000000000"` at 9 decimals. L1-33's typed tables must use that form, not 8.2's `100.00`.
- **Ledger hash for fixtures.** `gate_ledger.ledger_hash([])` is `d751713988987e9331980363e24189ce`, which is 32 hex,
  as 6.1 requires.
- **Second fixture manifest.** `tests/fixtures/nautilus/MANIFEST.csv` must use the house 10-column header with
  non-empty `licence`, `owner` and `md5` (`tests/notrun.py:17-21, 49-65`).
  - On a changed fixture, `require_fixture` raises `NotRun("REFDATA: …")`, not FAIL. So a tampered `RECORD` turns
    L1-17 into NOT_RUN on Linux. Step 7A's "L2-5b the only NotRun allowed" catches it on Windows.
  - The default `unlisted()` check walks only `tests/fixtures/macro/` (`tests/notrun.py:17-18, 82-92`), so the new
    folder does not trip `tests/macro_m0_harness.py:308`.
- **T-RO-01 scope.** The scan covers `core`, `data`, `ui`, `main.py`, `config.py`, `docs/*.py`, `tools` and `papers`
  (`tests/acceptance.py:50-56`; `tests/macro_m0_harness.py:63-70`). It does not cover `tests/`, so the stub child and
  L1-22's `find_spec` are not scanned.
  - The runner's P0a loader calls `spec_from_file_location`, which is in `IMPORT_MACHINERY`. It passes rule E only
    while no string inside that call contains "nautilus".
  - Adding the loader's real call shape to 8.5's "runner positive" control would pin that.
- **README.** No existing test cross-checks README counts. The README tests at `tests/macro_ui_components.py:137-175`
  check phrases only. So Step 4's unchanged Total row cannot fail the suite.
- **`.gitignore`.** It already ignores `__pycache__/` and `*.pyc`. A Step 7A suite run therefore leaves R-01's
  porcelain check clean, apart from `qa/acceptance_results.json`, which 7A.3 commits.
- **Other referees.** I agree with QUANT-R3-2 (`round3_claude_quant.md`): no runner-level crypto rehearsal exists, and
  a null `rf` is undefined. From the QA side, add that L2-12 to Step 7's done-when, so that pilot 2 of record is not the
  first run of that path.
- **Data access in this round:** none from the cache. I read no SPY or BTC price and recomputed no data md5. I wrote
  no ledger row and did not run `tests/run_all.py`. `git status --porcelain` and the md5 of `qa/acceptance_results.json`
  (`16c9baa5a1777853521d485d5078e456`) were the same before and after the scan probe.
