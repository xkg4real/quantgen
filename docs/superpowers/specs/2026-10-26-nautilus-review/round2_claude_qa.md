# Round 2 referee report: QA lens (Claude)

Spec under review: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 2 (working tree on top of
`a14954f`). Repository: QUANTGEN at `6f7c610`; `git diff --stat 6f7c610` shows no change outside `docs/superpowers/specs/`,
so every `file:line` below holds at both commits. Nautilus: `nautilus_trader` 1.231.0 in `scratch:ntvenv`.
`scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`. Spec lines are
`spec:<line>`. My probes are in `scratch:referee2_qa/`.

Lens: is every done-when testable and unambiguous? Do fixtures and goldens reproduce on both precisions? Does every
guard and fail-closed condition have a negative control? Is any test vacuous? Does the suite follow the house
conventions, and does no test write production state?

## Verdict

**ACCEPT_WITH_CHANGES.**

Revision 2 fixed most of what I raised. These reproduce exactly:
- the wheel identity, for both wheels and both Linux venvs;
- both allow-list pin digests;
- all 52 scan controls of 8.5;
- F1, F2 and N1 under `unshare -rn`;
- the guard self-test.

The golden format, the table schema, the input ranges and the run-record lifecycle are now specified.

I would still not hand the spec to a team today. Five majors would send an engineer to build a test that cannot pass,
or to weaken a guard to make it pass:
- The of-record refusal tests write a lock file into the real repo before they refuse, so the suite guard fails. L1-6
  cannot reach R-01 at all (QA-R2-1).
- No stub-child contract exists for the layer-1 tests that must get past parity. Three seams named in the tests are
  missing from `run()` (QA-R2-2).
- R-16's freshness rule refuses the second run that L1-5 requires (QA-R2-3).
- Step 6 refuses the real pilot-1 cash-rate file: DGS3MO has blank values on SPY sessions, and no control covers this
  (QA-R2-4).
- The done-whens of Steps 3 to 6 need code that is scheduled for later steps (QA-R2-5).

None is a blocker. Each needs a short spec change.

## Sections reviewed

- Status, Inputs, Owner context, section 2 rulings O1 to O15 (spec:1-95).
- 3.1 to 3.12 constraints, with focus on 3.3 hermeticity, 3.7 encoding, 3.8 never concurrent, 3.9 unseen windows
  (spec:96-207).
- 4.1 to 4.4: processes, data flow, launch contract, egress layer (spec:209-286).
- 5.1 requirements; 5.2.1 to 5.2.8 sandbox (spec:288-464).
- 5.3.1 to 5.3.5 runner: modes, seams, order of operations, reconstruction, lifecycle (spec:466-555).
- 5.4 parity, 5.5 hand-off (spec:557-645).
- 5.6 T-RO-01 amendment, 5.7 suite, 5.8 file table (spec:647-786).
- 6.1 to 6.8 data model (spec:788-949).
- 7 error handling, every row and its Control column (spec:951-997).
- 8 testing strategy, all of it (spec:999-1172).
- 9 steps and done-when, including Step 7A (spec:1174-1228).
- 10.1, 10.2, 10.4; Appendix B issue map (spec:1230-1307, 1390-1501).

## Round-1 issues

- **QA-1: open.** The guard and `QUANTGEN_MACRO_DIR` protect the ledger. But of-record refusal tests take the table lock
  under the real repo's `docs/nautilus_bridge/runs/.locks/` before they refuse. That is a production write, and it
  trips the guard (QA-R2-1).
- **QA-2: resolved.** The golden format is defined (6.8). N1 is restated as measured. I reproduced it with the
  Revision-2 sandbox shape: 1 row (1000 @ 100.00, commission 500.00), 904501.00 USD, quantity 1000, 4 of 12 bars,
  force stop true, the order FILLED with filled_qty 10000, and the -89.45 only in the log. Residual details are in
  QA-R2-6.
- **QA-3: resolved.** Moot. N3 is retired with the realism leg (C-1).
- **QA-4: resolved.** 6.1 splits what the child accepts from the pilot values, and step 1 enforces the pilot values.
  The capital range is too wide for standard precision (QA-R2-8).
- **QA-5: resolved.** The table schema has `start` and `end` (6.6), and step 5 filters both ends before parsing.
- **QA-6: resolved.** The evidence is now the ledger-hash echo. Times have microseconds. `bridge_run_id` has
  microseconds plus the table hash. The folder uses `exist_ok=False` and the card uses `open(..., "x")`.
- **QA-7: open.** Three gaps remain. L1-6 cannot run R-01, because R-01 exists only in of-record mode and of-record
  refuses `repo_root` and `anchor_fn` (QA-R2-1). No stub-child output contract exists. "Register seam", "scorer seam"
  and a 3 s timeout are used by tests but are not in `run()` (QA-R2-2).
- **QA-8: resolved.** Every row of section 7 has a control or a written reason. One clause, C-15's "self-test failed",
  has no runtime path (QA-R2-10). R-06 lacks a positive control for blank rate rows (QA-R2-4).
- **QA-9: resolved.** The card holds the run id. The run record holds the card's md5 (5.5 steps 8-9; L1-28).
- **QA-10: resolved.** I recomputed the digest with the 6.7 rule (no trailing newline):
  - the Linux wheel and both Linux venvs (`ntvenv`, `ntvenv_hash`): `a448cd20…f03f9`, 764 entries;
  - the win_amd64 wheel: `47d274d7…39555`, 764 entries;
  - with a trailing newline the digests would be `bda11531…` and `dd44b1ab…`, so the newline rule matters.
- **QA-11: resolved.** The baseline comes from F1 and F2 only, and STD names are exempt. Measured with `-X
  importtime` under `unshare -rn`: F1 and F2 give identical censuses (967 lines; NT 191, TP 508, STD 243 names), with
  no `adapters` or `network` name.
- **QA-12: resolved.** N4 is redefined. L1-14 mutates `GATE`. The manifest has `stats_pnls_empty` (the probe printed 0
  stats). The scan test asserts that the real sandbox exists.
- **QA-13: resolved.** The rationale is corrected (5.2.5), and C-04 carries a reason (spec:977).
- **QA-14: resolved.** L2-5 reads `QUANTITY_MAX` and `FIXED_PRECISION` at run time.
- **QA-15: resolved.** I ran a copy of `scan_proto.py`. Every multiset of 8.5 matched, the real tree gave 0 hits, and
  `git status` was unchanged. The F4 wording is ambiguous (QA-R2-9).
- **QA-16: resolved.** The spec has `lineterminator="\n"`, an `os_name` parameter for L1-16, and the parent creates
  `home` and `tmp`.
- **QA-17: resolved.** Refusal is by md5, date and resolved path. Both sides use `normcase(realpath)`.
- **QA-18: resolved.** Step 2 uses porcelain v1 `-z` with `--untracked-files=all`. Each run has a new folder, and the
  card is written exclusively.
- **QA-19: resolved.** P1's margin uses QUANTGEN's own arrays and `S._sma` (`core/quant/strategies.py:111-116`). The
  exemption has controls at 1e-10 and 2e-9.
- **QA-20: resolved.** Moot after QUANT-3.
- **QA-21: resolved.** The folder path is fixed, and the Step 2 dry run is defined.

## New issues

### QA-R2-1

- **Severity:** major.
- **Section:** 5.3.1, 5.3.2 steps 0-2, 5.3.5, 8.3 tests 6, 19, 23, 24 and 32.
- **Problem:** The of-record refusal tests cannot be built without writing into the real repo. L1-6's R-01 cases
  cannot be reached. Rehearsal-mode runner tests depend on the real repo's git state.
- **Evidence:**
  - `run()` refuses `anchor_fn`, `repo_root`, `probe_cmd` and `hooks` in of-record mode (spec:488-490). R-11, "a test
    seam in of-record mode", is checked at step 1 (spec:968).
  - R-01 exists only in of-record mode; rehearsal allows a dirty tree (spec:514). L1-6 tests R-01 "through `anchor_fn`
    and `repo_root`" (spec:1077), so it is refused at step 1 before step 2 runs.
  - Step 0 takes the lock before step 1 (spec:497). The lock is `<out root>/.locks/<hash>.lock` (spec:546). In
    of-record mode the out root is the repo's `docs/nautilus_bridge/runs/` (spec:477).
    - So L1-19 (of-record pilot values, `--child-cmd` in of-record), L1-23 (the egress-record case is of-record only,
      spec:501) and L1-24 (R-15) each create `docs/nautilus_bridge/runs/.locks/` in the real repo.
    - The 3.3 guard digests `docs/nautilus_bridge/` and fails on any change (spec:125-127; L1-32).
  - L1-23's record case reads `docs/nautilus_bridge/egress/<tag>.json` from the real repo. That file does not exist
    before Step 7A.
  - Rehearsal still runs step 2's R-02, with `repo_anchor()` and `git rev-parse HEAD` (spec:499, 514). So every
    rehearsal runner test needs `git` on PATH and a loose ref. Only L1-6 has the house's `NotRun("OWNER: git not on
    PATH")` path (`tests/frozen_guard.py:13-14`).
- **Proposed fix:**
  - Split steps 0-2 into functions with explicit roots, for example:
    - `take_lock(out_root, table_bytes)`;
    - `check_table(table, mode, ledger_dir, hostname)`;
    - `check_git(repo_root, anchor_fn, git_exe)`;
    - `check_egress_record(record_dir, run_facts)`.

    L1-6, L1-19, L1-23 and L1-24 call these directly on temp roots.
  - In `run()`, refuse a test seam during argument validation, before step 0. The only of-record `run()` test is then
    the seam refusal. That test asserts that `docs/nautilus_bridge/runs/.locks` was not created.
  - In rehearsal, record the git state without refusing on R-02. Otherwise give tests a `git_fn` seam. A runner test
    without `git` raises NotRun.

### QA-R2-2

- **Severity:** major.
- **Section:** 5.3.1, 8.1, 8.2 N8, 8.3 tests 3, 14, 26, 27, 28, 30 and 31.
- **Problem:** Several layer-1 runner tests must get past every hard parity check, but no stub child that can do this
  is specified. Three seams the tests use are not in `run()`.
- **Evidence:**
  - The only stub rules are "plain Python scripts written into the temp dir" (spec:1004) and the `--child-cmd` argv
    rule (spec:485-487).
  - These tests are reachable only after P0b to P13 pass (spec:630): L1-14 (G-04), L1-26's G-05 case, L1-28 and L1-30
    (a written card), and N8 (G-02).
    - A stub must therefore write fills, decisions, on-bar equity and a manifest that pass P1 to P4, P7 and P12.
    - It must also pass P13: reconciliation within $0.01, and the SHA-256 and ledger-hash echoes.
  - L1-3 says "the runner passes" (spec:1074), with no exit code or status.
  - Seams used by tests but missing from the `run(...)` signature (spec:488-489):
    - "a register seam raising on the third row" (L1-26, spec:1097);
    - "a scorer seam" (N8, spec:1063; L1-14, spec:1085);
    - a 3 s timeout (L1-27, spec:1098), while 4.3 fixes 900 s (spec:253).

    The `hooks` step names are not listed.
  - With `--child-cmd` and a blank `QUANTGEN_NAUTILUS_PYTHON`, the child's `PATH` entry `<venv bin dir>` is undefined
    (spec:255-256).
  - L1-31 expects G-03 (spec:1102). But parity already calls `walk_forward` for P11 and P12 (spec:579-580), before
    5.5. With a stub, the run can be WITHHELD for a parity reason or end as G-06 ERROR, so a test that checks only
    "WITHHELD" can pass for the wrong reason.
- **Proposed fix:**
  - Specify a layer-1 stub child, for example `tests/nautilus_stub_child.py`. It reads `input.json` and `bars.csv`,
    applies the port's rule and fee-inclusive sizing in Decimal, fills at the close, and rounds commissions as `Money`
    does (QA-R2-7). It writes the four files and a valid manifest with every echo. Flags select the failure stubs of
    L1-27.
  - Add `timeout`, `register_fn` and `score_fn` keywords to `run()`, refused in of-record mode. List the hook step
    names.
  - Define L1-3's pass: every child's return code is 0, and every `config_id` is in the ledger before the first child
    starts.
  - State that a `walk_forward` raise anywhere after registration is G-03. L1-31 asserts the reason text.

### QA-R2-3

- **Severity:** major.
- **Section:** 3.8, 5.3.2 step 0, 7 R-16, 8.3 tests 5 and 25.
- **Problem:** R-16 refuses the second run that L1-5 requires. The obvious workaround is to exempt rehearsal from
  freshness, which would weaken a guard.
- **Evidence:**
  - Step 0 refuses when the family ledger was modified under 600 s ago (spec:172, 497, 973).
  - Rehearsal runs the same steps and does not exempt step 0 (spec:514-515).
  - L1-5 runs the same table twice (spec:1076). The first run appends to `<tmp>/ledgers/<F>.jsonl`
    (`core/quant/gate_ledger.py:337-355`), seconds before the second run starts.
- **Proposed fix:** L1-5 sets the ledger's mtime back by 601 s with `os.utime` between the runs, and the spec says so.
  An alternative is a `freshness_s` keyword that of-record mode refuses. Add an L1-25 case where a 601-second-old
  ledger passes.

### QA-R2-4

- **Severity:** major.
- **Section:** 5.3.2 step 6, 7 R-06, 8.3 test 7, 10.1.
- **Problem:** The cash-rate step, as written, refuses the real pilot-1 input. No control would show this before the
  owner's of-record run.
- **Evidence:**
  - `docs/asset_expansion/cache/fred_DGS3MO.csv` (md5 `661722143f24930a29b58c535d227c1b`, verified) has 395 blank
    values. They include 2003-10-13, 2003-11-11, 2004-10-11 and 2004-11-11.
  - `yf_SPY.csv` has a session on each of those four dates. I checked these pre-2004-12-01 dates only.
  - `reindex(method="ffill")` keeps a NaN that sits on an existing label. Probe `rf_nan_probe.py` (pandas 2.3.3) gives
    `[5.0, nan, 5.2]` without `dropna()` and `[5.0, 5.0, 5.2]` with it.
  - Step 6 states `rf = DGS3MO.reindex(dates, method="ffill") / 100 / 252` with no `dropna()` (spec:503). R-06 refuses
    "NaN after forward fill" (spec:963).
  - The study's `fred()` drops NaN after reading (`docs/asset_expansion_study.py:100-104`), before `rf_daily` reindexes
    (`:148-153`).
  - Bond-market holidays on which the NYSE trades recur every year. The pilot window almost certainly has the same
    pattern (UNVERIFIED: I read no SPY row after 2004-11-30).
  - L1-7's synthetic files have no blank value on a panel date (spec:1078).
- **Proposed fix:**
  - Step 6 reads DGS3MO exactly as `study.fred` does, then reindexes:
    `pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0].dropna()`.
  - R-06 means NaN after that fill.
  - L1-7 adds a synthetic rate file with a blank value on a panel date. It must be forward-filled and pass, next to
    the leading-NaN refusal.

### QA-R2-5

- **Severity:** major.
- **Section:** 9 Steps 3 to 6, 5.8 file table, 4.3.
- **Problem:** The done-whens of Steps 3, 4, 5 and 6 need code that is scheduled for later steps. The plan's RED/GREEN
  steps (Step 2) cannot be written in this order.
- **Evidence:**
  - `runner.py` is built at Step 6 (spec:771). It holds:
    - the launch function (spec:242-243);
    - the venv and wheel-identity reads (spec:215-216; 6.7);
    - `--fixtures` and `--record-baseline` (spec:482-484).
  - Step 3 needs "the parent's identity read gives `a448cd20...`" (spec:1183).
  - Step 4 needs L1-16, which tests the launch builder (spec:1184, 1087).
  - Step 5 needs:
    - L2-1, the parent's reads;
    - L2-2 and L2-3, goldens that `runner --fixtures` produces and checks;
    - L2-6, the baseline from `--record-baseline`;
    - L2-9 and L2-10, "through the launch contract" (spec:1185, 1109-1118).
  - Step 6 needs parts of three tests that depend on Step 7's `parity.py` and 5.5 (spec:771, 1186-1187):
    - L1-20's P0b case;
    - L1-26's G-05 case;
    - L1-28's written card.
- **Proposed fix:**
  - Move the launch builder, the venv and identity reads, and the census parser into `tools/nautilus/launch.py`, built
    at Step 3. Update 4.3 and the file table.
  - Give goldens and the baseline a Step-5 entry point, or move L2-2, L2-3 and L2-6 to Step 6.
  - Move L1-20's P0b case, L1-26's G-05 case and L1-28 to Step 7.

### QA-R2-6

- **Severity:** minor.
- **Section:** 6.8, 5.3.1, 6.2, 8.4 tests 2 and 3.
- **Problem:** Who writes the goldens is contradictory. One manifest money format is undefined. The check against the
  hand arithmetic is manual.
- **Evidence:**
  - 6.8 says "`runner --fixtures` produces them" (spec:946). 5.3.1 says `--fixtures` runs against the goldens and that
    "Only `--egress-record` and `--record-baseline` write files" (spec:482-484).
  - `account_balance_usd (str)` has no format (spec:822). `str(Money)` gives `"926593.00 USD"` (probe), while the
    golden compares money numerically.
  - The golden has no `final_qty` and no `invalid_reasons`.
  - "Checked against 8.2's hand arithmetic before commit" (spec:946-947) is a manual step. A golden regenerated from a
    wrong run would still match itself.
- **Proposed fix:**
  - Add `--fixtures --write-goldens`, Linux only, which refuses to overwrite.
  - Fix `account_balance_usd` as `f"{balance.as_decimal():.2f}"`.
  - Add `final_qty` and `invalid_reasons` to the golden.
  - Add a layer-1 test that the committed F1, F2 and N1 goldens equal 8.2's tables, typed into the test.

### QA-R2-7

- **Severity:** minor.
- **Section:** 5.4.1 P7.
- **Problem:** `Money` does not round half-even. P7's total check can fail on a correct engine.
- **Evidence:**
  - `Money.__init__` converts the value to a double before `money_new` (`nt:model/objects.pyx:1190, 1205`).
  - Probe `money_probe.py` gives these results:

    | Value | Money | Half-even |
    |---|---|---|
    | `Decimal("0.125")` | 0.13 | 0.12 |
    | `12.345` | 12.35 | 12.34 |
    | `4752.125` | 4752.13 | 4752.12 |
    | `1.005` | 1.00 | (half-up gives 1.01) |

    Every result is consistent with rounding the double `float(x) * 100` half away from zero. The Rust internals are
    UNVERIFIED.
  - P7's total bar is 1e-6 of the total (spec:575). For F2's total of $203.29 that is $0.0002, so one tie fails P7
    hard. The per-fill bar of $0.01 still passes.
  - The spec marks the rounding mode UNVERIFIED (spec:587).
- **Proposed fix:**
  - Compute each expected commission as Money rounds it:
    `int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP))` cents.
  - Require the totals to be equal.
  - Add a tie control: quantity 25 at price 1.00, 50 bp at 1x, gives 0.125, which Money rounds to 0.13.
  - Replace the UNVERIFIED sentence with the measurement.

### QA-R2-8

- **Severity:** minor.
- **Section:** 6.1, 8.4 test 5.
- **Problem:** The child accepts a capital that standard precision cannot hold. The result is a crash, not exit 20.
- **Evidence:**
  - 6.1 accepts `capital_usd` up to 1e12 (spec:801).
  - Standard-mode `MONEY_MAX` is 9,223,372,036 (spec:149-150).
  - `Money` raises above `RUST_MONEY_MAX` (`nt:model/objects.pyx:1196-1199`).
  - In high precision `Money(1e12)` works (probe: `MONEY_MAX` = `PRICE_MAX` = 17,014,118,346,046). So the gap shows
    only on Windows.
- **Proposed fix:** Bound capital by `PRICE_MAX`, read at run time. It equals `MONEY_MAX` in both modes (3.6) and is
  already allow-listed, so the pin does not change. Add `int(PRICE_MAX) + 1` to L2-5.

### QA-R2-9

- **Severity:** minor.
- **Section:** 5.2.2, 5.6 rule F4.
- **Problem:** F4's wording does not match its controls.
- **Evidence:**
  - F4 is "a `Name` bound by an `import` statement" (spec:724; also spec:347). `from sys import argv` is an import
    statement.
  - The positive control uses `argv[2]` and must give no hit (spec:1126).
  - The prototype binds only `ast.Import` names (`scratch:rev2_probe/scan/scan_proto.py:136-140`). That is why the
    `sys.modules` control expects C3, E and F1 without F4 (spec:1150).
- **Proposed fix:** Say "a name bound by an `ast.Import` (`import m`, `import a.b`), not by `from … import`".

### QA-R2-10

- **Severity:** minor.
- **Section:** 7 C-15, 5.3.2 step 3.
- **Problem:** C-15 makes a run INVALID when "the guard self-test failed", but no run launches the self-test.
- **Evidence:**
  - `--guard-selftest` appears only at spec:249, 321, 326, 770, 988 and 1116.
  - Step 3 runs `--check-env` only (spec:500).
  - The runner's modes do not include the self-test (spec:470-472).
- **Proposed fix:**
  - Step 3 also runs `--guard-selftest`. It refuses with R-03 unless the exit is 0 and all five outcomes are as
    expected, and it records the JSON.
  - Add a layer-1 control with a stub that prints one wrong outcome.

### QA-R2-11

- **Severity:** minor.
- **Section:** 5.2.5 shared rules.
- **Problem:** The rationale for "never raise in `on_bar`" cites behaviour that Nautilus does not have.
- **Evidence:**
  - The spec says the actor "catches and logs every `on_bar` exception" (spec:400-402).
  - The code logs and re-raises (`nt:common/actor.pyx:4589-4591`).
  - Probe `proto_raise.py` plants a `ValueError` at bar 5 of F1 under `unshare -rn`. The child exits 1 with the
    traceback.
- **Proposed fix:** State the measured behaviour: an `on_bar` exception ends the child with exit 1, which C-06 makes an
  INVALID run. Keep the never-raise design so that reasons reach the manifest.

### QA-R2-12

- **Severity:** minor.
- **Section:** 8.2 N6 and N7, 8.4 test 7.
- **Problem:** Three fixtures are described but not specified. Their expected outcomes cannot be reproduced across
  machines or engineers.
- **Evidence:**
  - N6 is "a price path from about 80 to about 650 with volatility clusters, ±10% days planted on 20 decision bars"
    (spec:1061). The cash rate and the dates are not given.
  - L2-7 is "1,500 seeded bars" (spec:1115).
  - N7's "hand arrays" (spec:1062) must make corrected P3 fail at 2x. The quant probe found the 1x-for-2x Sharpe gap
    inside the P3 bar on BTC-like series (spec:622-624), so the expected outcome depends on arrays the spec does not
    give.
- **Proposed fix:** Give the generators as code (`numpy.random.default_rng(seed)`, model and parameters, planted
  indices, business-day dates from 2001-01-02, rf = 0), or commit the series as fixtures with md5s. Give N7's arrays,
  or reduce its expectation to "P7 fails on both; P3 and P12 reported".

### QA-R2-13

- **Severity:** minor.
- **Section:** 3.3, 8.3 test 32.
- **Problem:** The guard digests a fixed path, and the production ledger can live elsewhere.
- **Evidence:**
  - The guard digests `~/.nextgen/macro/ledgers` (spec:125-127).
  - The production ledger is `config.macro_dir() / "ledgers"`. `.env` can move it with `QUANTGEN_MACRO_DIR`, which is
    read at call time (`config.py:176-178`).
  - Tests set `QUANTGEN_MACRO_DIR` to a temp dir (spec:490-491). A guard that resolves the path late digests the temp
    dir.
  - The macro suite's `home_listing()` adds `QUANTGEN_MACRO_DIR` when set (`tests/macro_acceptance.py:113-121`).
- **Proposed fix:**
  - Resolve the production path once, when the suite starts and before any test changes the environment.
  - Digest both `~/.nextgen/macro/ledgers` and that path.
  - Every test that sets `QUANTGEN_MACRO_DIR` restores it in `finally`.

### QA-R2-14

- **Severity:** minor.
- **Section:** 8.3 tests 15 and 17.
- **Problem:** L1-17's fixture has no location. L1-15 as worded would flag correct binary I/O.
- **Evidence:**
  - L1-17 needs "a copy of the real wheel's `RECORD`" in layer 1, which has no venv (spec:1088). The spec gives no
    path for it.
  - House fixtures are md5-listed in a manifest (`tests/notrun.py:1-6, 49-80`).
  - L1-15 requires `encoding=` on every `open` (spec:1086). The lock file is opened in binary mode, as
    `core/quant/gate_ledger.py:247` does, and binary mode cannot take an encoding.
- **Proposed fix:**
  - Commit both wheels' `RECORD` files under a named fixture folder with md5s.
  - Check both `a448cd20…` and `47d274d7…` in layer 1 on both platforms.
  - L1-15 exempts modes that contain `b`.

## Notes

Verified as stated (probes in `scratch:referee2_qa/`, synthetic data only):
- **Wheel identity** (`wheel_identity.py`): values as in QA-10, and the `Tag:` lines match the table in 6.7.
- **Pin digests** (`pin_digest.py`, constants cut verbatim from spec:660-703): `2792ad4a…e49f` and `70bcf50f…da6c`.
- **Scan controls** (`scan/scan_proto.py`, a copy): all 52 multisets of 8.5 and 0 real-tree hits. The tree was
  unchanged.
- **F1, F2 and self-test** (`proto.py`, a copy of `rev2_sandbox_proto.py`), run under `env -i` plus `unshare -rn` with
  `-I -B -X utf8 -X importtime`:
  - F1 and F2 fills, commissions and cash match 8.2: 926593.00 and 50343.77.
  - The guard self-test raises for SANDBOX, LIVE and LiveClock, and passes BACKTEST and TestClock.
  - `stats_pnls` is empty.
- **N1** (`proto_n1.py`): as in QA-2.
- **Census** (`census_cmp.py`):
  - The third-field parse works.
  - Failed optional imports appear as TP names: `plotly`, `cloudpickle`, `isal`, `lz4`, `lzmaffi`, `snappy`,
    `substrait`, `zstandard`.
  - `dateutil.tz.win` is attempted on Linux too.
  - The kernel imports `uvloop` inside try/except (`nt:system/kernel.py:91-93`). Windows may therefore log a failed
    `uvloop` attempt, which the `uvloop*` allowance covers (UNVERIFIED on Windows).
- **Repo facts:**
  - `config.macro_dir()` honours `QUANTGEN_MACRO_DIR` at call time (`config.py:176-178`).
  - `ledger_hash` is a 32-hex md5 (`core/quant/gate_ledger.py:371-372`), as 6.1 expects.
  - `validate_row` accepts UNVERSIONED anchors (`:214`).
  - `register_trials` takes `ledger_dir` (`ui/strategy_lab_page.py:55-56`), so L1-10 can be built. The Lab imports
    `flet`, which the global interpreter here has.
  - The four study cards match the `study_configs` of 10.1 and 10.2 (12 settings at 50.0; 12 at 3.0; 5 at 10.0 with
    the run 2/3 note; 5 at 10.0 for KRW-BTC), so L1-29 can be built.
  - `.gitattributes` is `* -text`, and the cache files are CRLF in the index. md5 pins are therefore byte-stable
    across platforms.
- **`walk_forward`:** its slicing and its `n_origins x G` `is_sharpes` match 5.4.2 (`core/quant/validate.py:367-381`),
  so L1-21's bit-for-bit claim is plausible.

Observations outside the issue list:
- **Census rule wording.** O13 says a run is invalid when it imports a module "outside" the baseline (a subset rule).
  5.2.7 says when its set "differs" (an equality rule). F1 and F2 are identical today, so the two rules agree. Pick one
  and test the other direction in L1-12.
- **Step 8 done-when.** It still requires `registered_utc` to precede `first_child_utc` (spec:1226). The ruled evidence
  is the hash echo, and a wall clock can step back. Say "at or before", or drop the condition.
- **5.5 step 5 flag list.** It omits two thresholds the decision tree reads: `prob_loss_oos <= prob_loss_max` (`flat`,
  `core/quant/validate.py:545, 576`) and the `n_sessions < mtr` branch (`:584, 607`). For pilot 2's five
  configurations, `flat` is the over-search check. Decision equality catches any crossing that changes the decision.
  This is a quant-lens point.
- **Positive-control `argv` index.** The scan positive control uses `IN = Path(argv[2])` (spec:1126). Under the launch
  argv `... sandbox.py run --in <dir>`, the directory is `argv[3]`. This is harmless in a scan fixture, but it must not
  be copied into the real sandbox.
- **`unshare -rn` on other Linux hosts.** It works in this container. Hosts that restrict unprivileged user namespaces
  would refuse every layer-1 runner test with R-14. This does not affect the Windows suite of record.

Data access in this round: the first 3 lines of `yf_SPY.csv` (1995), and a count of 4 dates before 2004-12-01 in it. I
grepped `fred_DGS3MO.csv` for blank values. I read no BTC file, recomputed no SPY or BTC md5, wrote no ledger row, and
did not run `tests/run_all.py`.
