# Round 4 referee report: QA lens (Claude)

Spec under review: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 4 (working tree; HEAD
`4f5f18b` holds Revision 3). Repository code: QUANTGEN at `4f5f18b`, unchanged since `6f7c610` (`git diff --name-only
6f7c610 4f5f18b` lists only the spec folder). Nautilus: `nautilus_trader` 1.231.0 in `scratch:ntvenv`. `scratch:` is
`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`. Spec lines are `spec:<line>`.
My probes are in `scratch:referee4_qa/`.

Lens: is every done-when testable and unambiguous? Do fixtures and goldens reproduce? Does every guard have a
negative control that cannot pass for the wrong reason? Is any test vacuous? Does the suite follow house conventions,
and does no test write production state or touch protected data?

## Verdict

**AGREE**, with 6 minor issues.

Revision 4 resolves all twelve of my round-3 issues as ruled, and every round-1 and round-2 issue stays resolved. I
re-measured everything that carries a number, and all of it reproduces:
- F1, F2 and N1 through 4.3's exact POSIX launch contract, against the author's filled Revision-4 sandbox;
- two-process determinism of `fills.csv` for F1 and F2;
- all 52 scan results of 8.5, with my own verbatim cut of the 5.2.9 skeleton as the positive control, 0 real-tree hits
  and both pin digests;
- the three synthetic-series md5s, L2-12's new one included;
- 31 single-field input perturbations of my own, beyond the author's 63: 30 exit 20 (the one exit 0 is not a 6.1
  rule; see the notes).

I found no blocker and no major. Revision 4 introduced nothing that makes a done-when impossible by design or that
writes production state. The six minor issues are local fixes of one to three sentences each.

Two of them, QA-R4-1 and QA-R4-2, concern the binding house rule on protected data (no SPY row on or after 2004-12-01,
no real BTC price). In each, one plausible implementation slip makes Claude's own Step 6 or Step 7 tests read or hash a
real price file. No test catches the slip before the read happens. Both are pre-existing, not introduced by Revision 4,
and both fail closed afterwards (the run refuses). Even so, I ask that they be applied before the Step 6 RED tests are
written.

## Sections reviewed

All 1,772 lines of Revision 4, in order:
- Status, Inputs, Owner context, and section 2 (spec:1-107).
- Section 3 (spec:109-225), with the new per-test `QUANTGEN_MACRO_DIR` rule (spec:141-143) and the place rule of 3.9
  (spec:198-203).
- Section 4 (spec:227-303): `fixture_inputs` (spec:263-264), the probe and the egress record.
- 5.1 and 5.2.1 to 5.2.9 (spec:307-645), including the Revision-4 skeleton (spec:503-645).
- 5.3.1 to 5.3.5 (spec:647-778): the seams `tree_refusal`, `check_p0a`, `probe_cmd` and `write_record(replace=,
  sleep=)`; steps 0 to 17; `table_sha256` keying; the return-code contract.
- 5.4 and 5.5 (spec:780-863), with P13, `reference_drift` and G-08.
- 5.6 to 5.8 (spec:865-1010).
- Section 6 (spec:1012-1167), with `code_sha256` and the 6.8 golden rules.
- Section 7 (spec:1169-1219): every row and its control.
- Section 8 (spec:1221-1416): the stub child, the fixtures, the series code, every L1 and L2 row, the scan controls and
  8.6.
- Section 9 (spec:1418-1506): Steps 1a to 10, with 7A and its re-entry rule.
- Sections 10 to 13 and Appendices A and B (spec:1508-1772).

Code read against the spec:
- `core/quant/gate_package.py:30-42` (`HARNESS_SOURCES`, repo-relative strings);
- `config.py:176-178` (`macro_dir()` reads the variable on every call);
- `core/quant/gate_ledger.py:122-131, 240-262, 371-376`;
- `ui/strategy_lab_page.py:55-80`;
- `tests/run_all.py:55-150`;
- `docs/asset_expansion_study.py:38-110, 136-153, 821-844`;
- the committed `qa/acceptance_results.json` (commit `ac86705`).

Probes, all on synthetic data or no data. None read a price row of a real series, none wrote a ledger row, and none
ran `tests/run_all.py`. `git status --porcelain` and the md5 of `qa/acceptance_results.json`
(`16c9baa5a1777853521d485d5078e456`) were the same before and after.
- **Fixtures.** `drive_fx4.py` builds F1, F2 and N1 from 6.1 and 8.2 and runs them through 4.3's POSIX argv and
  five-key environment (`unshare -rn`, `-I -B -X utf8 -X importtime`) against `scratch:rev4_probe/sandbox_r4.py`.
- **Determinism and echoes.** `det4.py` (two processes per fixture) and `endts4.py` (`backtest_end`, row counts).
- **Input refusals.** `gap4.py`: 31 independent perturbations of 6.1 and of `bars.csv`.
- **Scan.** `scan4_copy.py`, the author's prototype, with my verbatim cut of spec:504-644 (`skeleton_from_rev4.py`) as
  the positive control. My cut is byte-identical to `scratch:rev4_probe/skeleton.py`.
- **Series.** `synth4.py` runs the series code of spec:1318-1325.
- **P0a.** `p0a_download.py` loads the study by path with `yfinance` and `pandas_datareader` replaced, beforehand, by
  stand-ins that record the call and raise. So no network call is possible.
- **Locks.** `lock_probe.py` measures same-process `flock` and `lockf` conflicts.

## Earlier issues

Round 3 (all resolved):
- **QA-R3-1: resolved.**
  - L1-5 is built at Step 7 (spec:1336) and listed in Step 7's done-when (spec:1432).
  - `fixture_inputs(name)` lands in `launch.py` at Step 5 (spec:263-264, 991), and Step 5's done-when requires it
    (spec:1430).
  - One residual of the same kind, in L1-3, is in QA-R4-5.
- **QA-R3-2: resolved.**
  - The parent re-derives C-01 to C-04 and C-15 (spec:460-463), and P13 names that re-derivation (spec:804).
  - Section 7 says "parent re-derives" (spec:1194-1197, 1208).
  - `--doctor` writes `valid: true` and exits 0, for C-01 and C-02 too (spec:1238-1240).
  - L1-27 asserts each id (spec:1358).
  - One residual, the source of C-02's comparison values, is in QA-R4-3.
- **QA-R3-3: resolved.**
  - `table_sha256` names the table in the run id, the lock, `earlier_runs` and R-17 (spec:750-753, 762, 1193).
  - The record keeps both digests (spec:1055).
  - L1-5 adds the new-`owner_confirmed` case and the BOM-and-CRLF case (spec:1336).
  - Step 0 runs R-17 before the freshness check (spec:700), so the R-17 cases do not collide with R-16.
- **QA-R3-4: resolved.**
  - L2-5a iterates one perturbation per 6.1 rule (spec:1374), and 63 cases were measured (spec:839).
  - I added 31 cases of my own (`gap4.py`): booleans as integers, `"1_005_001"`, `" 1005001"`, `"+1005001"`, `"NaN"`,
    `"Infinity"`, `"5e1"` and `"-0"` as strings, `"1e9"` volume, an extra params key, `"SMA"`, CRLF, BOM, a trailing
    blank line, an extra column, a renamed header, a zero or negative close, a `NaN` token, a non-object, crypto
    bounds, and a strategy/instrument mismatch.
  - All exit 20 except a duplicate JSON key (see the notes).
- **QA-R3-5: resolved.**
  - `probe_cmd` is explicit, the runner never derives it from `child_cmd`, and every layer-1 runner test passes both
    (spec:689-690).
  - The stub has `--probe` (spec:1237).
- **QA-R3-6: resolved.** `run()` returns its exit code, 5 after `ABORTED` included, and never re-raises. The CLI maps the
  code to `SystemExit` (spec:763-764).
- **QA-R3-7: resolved.**
  - `tree_refusal` (spec:680), `check_p0a` (spec:681-682, 707) and `write_record(..., replace=, sleep=)` (spec:756) are
    named.
  - L1-6, L1-20 and L1-34 use them (spec:1337, 1351, 1365).
- **QA-R3-8: resolved.**
  - Each reason begins with its section-7 id (spec:421, 458-459, 579, 1045).
  - Goldens and L1-33 compare by id (spec:1163, 1364).
  - Re-measured: N1's reasons are `["C-01: forced stop", "C-02: bars seen fewer than bars fed"]`.
- **QA-R3-9: resolved.** `plain_mean` is in both port rows (spec:437-438), the skeleton (spec:534-538) and the stub
  (spec:1234).
- **QA-R3-10: resolved as ruled.**
  - The question is in 13.1 (spec:1613-1614), 8.1 (spec:1240-1243) and Step 7A's done-when (spec:1498-1499).
  - One residual, how the fallback is chosen, is in QA-R4-4.
- **QA-R3-11: resolved.** N6, L2-7 and L2-12 are UNVERIFIED until Step 7, and a WITHHELD record must name its predicate
  (spec:1302, 1375, 1378).
- **QA-R3-12: resolved.**
  - O13 and 5.2.7 state equality (spec:105, 475-476).
  - L1-12 has a missing-TP-name case (spec:1343).
  - Step 8's evidence is the hash echo (spec:1504).

My round-3 notes were applied:
- goldens hold the price string at the instrument's precision (spec:1161-1162);
- L2-12 is in Step 7's done-when (spec:1432).

Rounds 1 and 2: all stay resolved. I re-checked each at its Revision-4 lines.
- **QA-1 and QA-R2-1.** Pure step functions on temp roots (spec:677-683). Seams are refused in argument validation
  before step 0 (spec:692-694). The guard digests both ledger paths and `docs/nautilus_bridge/` (spec:138-143). L1-19
  asserts that no `.locks` folder is created (spec:1350).
- **QA-2.** Re-measured N1:
  - 1 row, BUY 1000 @ `100.00`, commission `500.00`;
  - balance `904501.00`, quantity `1000`;
  - 4 of 12 bars seen, force stop true, exit 10.
  - `backtest_end` is bar 3's timestamp, earlier than `last_ts`, so the parent's C-02 re-derivation fires.
- **QA-6 and QA-R2-13.** The echo is in the manifest. Re-measured: `input.ledger_hash_after_registration` echoes
  `d751713988987e9331980363e24189ce`, which is `ledger_hash([])`, 32 hex.
- **QA-10 and QA-R2-14.** The identities are unchanged (spec:1146-1147).
- **QA-11.** The F1, F2 and N1 censuses are equal: 942 names each, census hash `c7ca00762389...`.
- **QA-12.** `stats_pnls_empty` is true in all three manifests.
- **QA-15.** All 52 scan results reproduce exactly (`scan4_rerun.out` equals `scratch:rev4_probe/scan4.out`). The pins
  are `2792ad4a...e49f` and `70bcf50f...da6c`.
- **QA-R2-7.** The `cents` rule is unchanged (spec:810-813).
- **QA-R2-12.** The md5s `adb735b9...`, `7b53fe60...` and the new L2-12 `c68986bf632dea074edb5c8ccef76a7d`
  reproduce. L2-12 runs from 398.59 to 60,000.00, with a maximum of 60,450.91, and every close passes the 9-decimal
  round trip.
- **Determinism (3.5, L2-4).** `fills.csv` hashes are equal across two processes for F1 (`ca3dcbf1...`) and F2
  (`a2d61988...`). `trade_id` is deterministic.

## New issues

All are minor.

### QA-R4-1 (minor; apply before Step 6): P0a fails open to a download of real prices on one naming slip

- **Section:** 5.3.2 step 7 (spec:707); 4.4's network sentence (spec:300-301); 3.9 (spec:195-203); 8.3 test 20
  (spec:1351); Step 2's Global Constraints (spec:1427).
- **Problem.** P0a points `study.CACHE` at a trimmed cache in the run's temp dir, "so `_cached` and `fred` never reach a
  download branch". That guarantee rests only on the trimmed file carrying exactly the name that `_cached` builds,
  `yf_<symbol>.csv`.
  - **The slip is easy and stays hidden for the pilots.** An implementer who names the trimmed file after
    `prices_file`'s basename gets `yf_SPY.csv` and `yf_BTC-USD.csv` right for both pilots. Every synthetic rehearsal
    then has a different name.
  - **The parent then downloads real data.** The study downloads the symbol's whole history from 1995 to today
    through `yfinance` and writes it into the temp cache. Layer-1 runner tests (L1-3, L1-5, L1-26, L1-27) and L2-7,
    L2-11 and L2-12 all pass step 7, in the parent, which has network.
  - **Nothing stops or detects it in time.** P0a then refuses (R-13), so the run fails closed. But the real SPY or BTC
    series has already been read. No control exists, and L1-20 calls `check_p0a` with a cache dir the test builds
    itself, so it never exercises the runner's naming.
  - **A smaller twin on the cash rate.** Step 7 copies DGS3MO "for pilot 1" only. A rehearsal that carries a synthetic
    rate (L2-7, N6) would reach `fred("DGS3MO")`'s download (`pandas_datareader`). `rf_daily` swallows every
    exception and returns 3% a year, so P0a refuses there too. That is fail-closed, but it is a parent network call
    that 4.4 says never happens.
- **Evidence.**
  - Code:
    - `_cached` calls `loader()` and `s.to_csv(f)` whenever the file is missing (`docs/asset_expansion_study.py:68-76`).
    - `yf`'s loader is `yfinance.download(symbol, start="1995-01-01", ...)` (`:82-91`).
    - `fred`'s loader is `web.DataReader(series_id, "fred", start)` (`:94-104`).
    - `rf_daily` catches `Exception` and returns `0.03 / 252` (`:148-153`).
  - `importlib.util.find_spec` finds both `yfinance` and `pandas_datareader` in the container's global interpreter.
    The owner's study ran them on Windows.
  - `p0a_download.py`, with recording stand-ins that raise. The trimmed cache holds `synth_prices.csv`, so it is
    named after `prices_file`. Output:
    - `study.yf("SPY")` and `study.yf("BTC-USD")` each reached `yfinance.download`;
    - `rf_daily` reached `DataReader('DGS3MO', 'fred')` and returned `0.00011905` per session, the 3% fallback.
  - Whether Yahoo is reachable through this container's proxy is UNVERIFIED. I did not try, by the house rule.
- **Proposed fix.**
  1. Inside `check_p0a`, or around the study calls at step 7, install raising stand-ins for `yfinance`,
     `pandas_datareader` and `pandas_datareader.data` in `sys.modules`, and restore them in `finally`. This is what the
     quant referee's round-4 probe did. A download branch then raises, and the run refuses with R-13 before any
     network call.
  2. Before calling the study, assert that `cache_dir / "yf_<symbol>.csv"` exists, named by `_cached`'s rule, and,
     whenever `rf_file` is set, `cache_dir / "fred_DGS3MO.csv"`.
  3. Step 7 reads "a DGS3MO copy whenever `rf_file` is set", not "for pilot 1".
  4. L1-20 gains two negative controls: a cache dir without `yf_<symbol>.csv`, and one without `fred_DGS3MO.csv`.
     Each refuses with R-13, and the stand-in records the blocked attempt.

### QA-R4-2 (minor; apply before Step 6): L1-9's tracked-file case can pass by content after hashing the real file

- **Section:** 3.9 (spec:198-203); 5.3.1 (spec:658); 7 R-10 (spec:1186); 8.3 test 9 (spec:1340); Step 2 (spec:1427).
- **Problem.**
  - L1-9 names a tracked cache file (`yf_SPY.csv`, `binance_BTCUSDT.csv`) and expects R-10 "by path before any read".
  - R-10 is caught at "5.3.1, step 5", the step that also checks the md5. The test cannot observe "before any read".
  - Suppose an implementation hashes first and checks the place second, and the test's table carries the real
    pinned md5 of `yf_SPY.csv` (`d2164597...`). The content rule then gives R-10, so L1-9 passes, but it has already
    hashed the whole real file, post-2004 rows included.
  - Step 2 forbids exactly that hash: "Claude never opens or hashes `yf_SPY.csv`, `yf_BTC-USD.csv`,
    `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv`".
  - With any other md5 in the table, the same wrong order gives R-04 and the test fails, but only after the hash.
- **Proposed fix.**
  - Judge the rehearsal place rule for `prices_file` in `check_table` (step 1), which opens no data file.
  - L1-9's tracked-file cases call `check_table`, and `run()` with `prices_md5` set to 32 zeros. They assert R-10, and
    that no `after_step1` hook fired.
  - A hash-first order then gives R-04 and fails the test. A correct order never opens the file.

### QA-R4-3 (minor): the parent re-derives C-02 from the child's own echoes

- **Section:** 5.2.7 (spec:460-463); 6.2 `input` (spec:1043); 7 C-02 and C-11 (spec:1195, 1204); 8.1 `--doctor`
  (spec:1238-1240).
- **Problem.**
  - The parent compares `bars_seen` with the manifest's `input.bars_fed`, and `backtest_end` with the manifest's
    `input.last_ts`. Both are values the child wrote.
  - The parent knows the true values: it wrote `n_bars` rows and their timestamps. Only `bars_sha256` is checked
    against the parent's own value (C-11).
  - So a manifest that lowers `bars_seen` and `bars_fed` together, and sets `last_ts` to the truncated bar, passes the
    re-derivation.
  - The stub's `--doctor C-02` presumably lowers `bars_seen` alone. So a parent that trusts the echo passes L1-27, which
    is the wrong-reason pass that QA-R3-2 set out to remove.
  - The reconciliation (C-09) does not close the gap. It compares the rebuilt `E-(t)` with `onbar_equity.csv` and does
    not say that the file must have T rows.
  - Measured on N1: the echo says `bars_fed` 12 and `last_ts` `979765200000000000`, so it is honest today.
- **Proposed fix.**
  - The parent checks the echoes `input.bars_fed`, `first_ts` and `last_ts` against its own `n_bars` and timestamps,
    with C-11.
  - It re-derives C-02 against its own values.
  - `--doctor C-02` lowers `bars_seen` and `bars_fed` together.
  - C-09 also requires `len(onbar_equity rows) == n_bars`.

### QA-R4-4 (minor): three test mechanisms are still unnamed

- **L1-35 golden dir.**
  - L1-35 runs `--record-baseline`'s existing-baseline rule "on a temp golden dir" (spec:1366).
  - The CLI writes `tools/nautilus/golden/modules_<tag>.json` (spec:476-482, 666), and in layer 1 it cannot run at all:
    it needs the venv and all three fixtures.
  - `tools/nautilus/golden/` is not in the 3.3 guard's digest, so a test that falls back to the real dir would go
    unnoticed.
  - Fix: a pure `record_baseline(golden_dir, tag, census) -> (exit, diff_lines)` that the CLI calls and L1-35 tests.
- **L1-3 ledger check.**
  - L1-3 says the stub "exits 1 unless every `config_id` of the table is in the ledger and `input.json` carries the
    post-registration hash" (spec:1334).
  - The stub's flags (spec:1238-1240) have no such mode. The stub runs with `-I` and the standard library only
    (spec:1232, 1242), so it cannot compute `gate_ledger.ledger_hash` (`core/quant/gate_ledger.py:371-372`).
  - Fix: L1-3 checks this in the parent, through the `child_started` hook. The hook reads the temp ledger, and compares
    `input.json`'s hash with `family_ledger(...).hash()`.
- **Stub interpreter on Windows (QA-R3-10 residual).**
  - Step 7A accepts "the recorded py313 fallback" (spec:1499), but nothing says who records it or how a test chooses it.
  - If the Store Python fails at 7A, the fix would be a code change after a failed Step 7A. That needs a new sign-off
    sentence (spec:1484-1485).
  - Fix: name the rule in the test helper now. Use `sys.executable`, unless its `normcase(realpath)` lies under
    `WindowsApps` and `%LOCALAPPDATA%\quantgen\py313\python.exe` exists, in which case use the latter. Record the
    choice in the hand-off report.

### QA-R4-5 (minor): four done-when wording points

- **L1-3 at Step 6** (spec:1334, 1431).
  - "The run passes when every child returns 0" cannot mean a clean rehearsal at Step 6, because `parity.py` and 5.5
    arrive at Step 7 (spec:993). This is the same kind of issue that QA-R3-1 fixed for L1-5.
  - Say "no child exits 1, and the ledger held every `config_id` before the first child started". Alternatively, name
    the Step-6 terminal status.
- **L1-33's "prices at 9 decimals"** (spec:1364).
  - This wording is wrong for N1, which has 2 price decimals. Measured: `last_px` `"100.00"`.
  - Say "at each fixture's precision", as 6.8 already does (spec:1161-1162).
- **Step 7A's "L2-5b the only NotRun allowed"** (spec:1498).
  - It must mean among `nautilus/*` rows. The committed full run, `qa/acceptance_results.json` at `ac86705`, has 121
    NOT_RUN rows in other suites (749 PASS, 0 FAIL).
  - Say "the only `nautilus/*` NotRun".
- **Step 6's rehearsal cash rate** (spec:706).
  - "Pilot 1: checks the md5 of `docs/asset_expansion/cache/fred_DGS3MO.csv` (`661722...`)" hard-codes the real file.
    But L1-7 and L2-7 use synthetic rate files (spec:1338, 1375).
  - Say "checks `rf_file` against the table's `rf_md5` (pilot 1: that file and `661722...`)". Rehearsal tables then
    work as written.

### QA-R4-6 (minor): name `flock`, not `lockf`, for the table lock

- **Section:** 5.3.5 lock (spec:753-755); 8.3 test 25 (spec:1356).
- **Problem.**
  - The spec names the flags `fcntl.LOCK_EX | fcntl.LOCK_NB`, which both `fcntl.flock` and `fcntl.lockf` accept.
  - L1-25's "a held lock refuses" runs in one process. POSIX record locks (`lockf`) never conflict within one process.
  - Measured (`lock_probe.py`): a second `flock` on a new handle is refused (errno 11), while a second `lockf` is
    granted.
  - The reference "as `core/quant/gate_ledger.py:244-262` locks" resolves it (`:254` uses `fcntl.flock`), but one word
    removes the trap.
- **Proposed fix:** write `fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)`.

## Why I agree or not

I agree. Every issue I raised in rounds 1 to 3 is resolved, and the mechanisms they asked for exist with named
controls. Revision 4 closes the last structural gaps of my lens:
- the parent's re-derivation of the child-side checks, with a stub that cannot be caught by the exit code alone;
- `table_sha256` keying of the re-run guard;
- the per-rule input refusals;
- the explicit probe seam;
- the return-code contract;
- the three seams `tree_refusal`, `check_p0a` and `write_record`;
- reasons by id.

Everything with a number reproduces exactly on independent probes. That covers the fixtures through the launch
contract, determinism, the series md5s, the scan multisets and pins, and 31 extra refusal cases. Production state stays
protected by the 3.3 guard, the per-test `QUANTGEN_MACRO_DIR`, the seam refusal before step 0, and temp-only ledgers.

The six issues above are minor:
- None changes the design or needs an owner ruling.
- None makes a done-when impossible once its sentence is fixed.
- None writes production state.

QA-R4-1 and QA-R4-2 are the two I would not leave for the implementer to discover. Each is one guard plus one negative
control, and each keeps a house rule from depending on the implementer naming a file or ordering two checks correctly.
Under C-8 the moderator applies minor issues and closes Step 1a. I support closing on that basis, with QA-R4-1 to
QA-R4-5 folded in before the Step 6 RED tests are written.

### Notes and measurements

- **Fixture measurements** (`drive_fx4.py`, against `scratch:rev4_probe/sandbox_r4.py`):
  - **F1:** fills BUY 10000 @ `100.000000000` (5000.00), SELL 10000 @ `96.000000000` (4800.00), BUY 9600 @
    `99.000000000` (4752.00), SELL 9600 @ `97.000000000` (4656.00); balance `926593.00`; `final_qty` `"0"`.
  - **F2:** quantities `1.00000000` and `0.98812079`; commissions 53.00, 50.00, 49.90, 50.39; balance `50343.77`.
  - **N1:** exit 10, with -89.45 only in the stderr log line.
  - F1 decisions rows 5, `onbar_equity` rows 12. N1 decisions rows 1, `onbar_equity` rows 4.
- **Duplicate JSON key.** An `input.json` with a duplicate key exits 0, because `json.loads` keeps the last value. This
  is not a 6.1 field rule. The parent writes `input.json` with `json.dumps`, which never duplicates, and P13 checks the
  input SHA-256 echo. No change is needed.
- **3.3 per-test macro dir.** `config.macro_dir()` reads `QUANTGEN_MACRO_DIR` through `_clean` on every call
  (`config.py:176-178`). `ui.strategy_lab_page.register_trials` falls back to it when `ledger_dir` is None
  (`ui/strategy_lab_page.py:67`). So the rule does what 3.3 says.
- **`code_sha256` in tests.** `HARNESS_SOURCES` holds 11 repo-relative paths (`core/quant/gate_package.py:36-38`). L1-19
  can therefore build a temp `repo_root` from copies and change one byte of `core/quant/validate.py` there, never in
  the real tree.
- **Same-process lock on Windows.** `msvcrt.locking` byte locks are per handle, so L1-25 works in one process there too
  (UNVERIFIED here: no Windows host).
- **Other referees.**
  - I agree with QUANT-R4-1 (`round4_claude_quant.md`). L2-12's last assertion fails for a correct bridge, so a Step 7
    done-when cannot pass as written. That is the same class as QA-R4-5.
  - I agree with SECURITY-R4-2 and SECURITY-R4-3 (`round4_claude_security.md`) from the testability side.
    - A 7A re-entry line that a firewall rule from an earlier attempt blocks is not repeatable as written.
    - A 7A line guarded by `$LASTEXITCODE` needs a stated exit code: `--egress-record` should exit non-zero when
      `probe.blocked` or `control_connect.ok` is false.
- **Data access in this round.**
  - I read the stored `qa/acceptance_results.json` status counts, the study's source text, and no cache file.
  - I read no SPY or BTC price and hashed no cache file.
  - The P0a probe ran with download stand-ins installed before the study loaded, and its trimmed cache held only a
    synthetic series.
