# Round 1 referee report: QA lens (Claude)

Spec under review: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 1.
Repository: QUANTGEN at HEAD `6f7c610`. Nautilus: `nautilus_trader` 1.231.0 in `scratch:ntvenv`.
`scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
Spec line numbers are given as `spec:<line>`.

Lens: is every done-when testable and unambiguous? Can the goldens be reproduced? Does every guard have a negative
control? Is any test vacuous, or does it depend on wall-clock time, the network, the home directory or the
production ledger? Does the suite follow the `tests/run_all.py` conventions?

## Verdict

**ACCEPT_WITH_CHANGES.**

The architecture is testable. The QUANTGEN side of F1 and F2 reproduces exactly. The Nautilus side of F1 and F2
also reproduces exactly at volume 1e9 in high precision, through the minimal launch environment. The suite
registration follows `tests/run_all.py`.

I would not hand the spec to a team today. Ten majors would send an engineer to build the wrong thing or a weak test:
- The N1 golden does not match the spec's own output files. I measured this.
- N3 run as literally specified (parity sizing) force-stops. I measured this.
- `input.json` mixes pilot values with schema values.
- The registration table has no schema and no end date.
- Two done-whens depend on wall-clock resolution.
- Layer-1 test 3 cannot be built as written.
- Most guards have no negative control.
- The card and the run record each need the other's md5.
- The wheel-identity comparison is undefined.
- Suite tests can reach the production ledger if a refusal regresses.

None of these is a blocker. Each needs a short spec change.

## Sections reviewed

- Status, Inputs and Owner context (spec:1-53).
- 3.1 Frozen pins, 3.3 Hermeticity, 3.5 Determinism, 3.6 Windows standard precision, 3.7 Encoding, 3.8 Never
  concurrent, 3.9 Unseen windows (spec:104-192).
- 4.3 Launch contract (spec:247-266).
- 5.1 to 5.2.7 Sandbox: imports, construction, bars, ports, outputs, checks, module baseline (spec:270-443).
- 5.3 Runner: modes, order of operations, reconstruction (spec:445-540).
- 5.4 Parity checks and selection (spec:542-622).
- 5.5 Gate hand-off (spec:624-645).
- 5.6 T-RO-01 amendment and 8.5 scan controls (spec:647-729, 1069-1089).
- 5.7 Suite registration, 5.8 Registry (spec:731-786).
- 6.1 to 6.5 Data model (spec:788-917).
- 7 Error handling (spec:919-961).
- 8 Testing strategy, all of it (spec:963-1100).
- 9 Steps and done-when, Steps 1 to 10 (spec:1102-1200).
- 10.4 Data-access history, Appendix A (spec:1278-1379).

Probes I ran (all read-only, synthetic inline prices, no pilot-window data, no real BTC prices):
- `scratch:referee_qa/fx_probe.py` builds F1, F2, N1 and N3 exactly as spec 5.2.3 to 5.2.5 describe. It runs under
  `env -i` with the POSIX launch-contract variables and `-I -B -X utf8`.
- `scratch:referee_qa/fx_probe_ev.py` adds the order events from the cache.
- `scratch:referee_qa/fx_probe_warn.py` runs at log level WARNING.
- `scratch:referee_qa/fx_probe_stats.py` and `fx_probe_stats_on.py` print `BacktestResult` stats with
  `run_analysis` off and on.
- `scratch:referee_qa/qg_ref.py` runs QUANTGEN's `trend_switch`, `crypto_trend` and `simulate` in the global
  interpreter, and the 5.3.3 reconstruction from the golden fills.

## Issues

### QA-1

- **Severity:** major.
- **Section:** 3.3, 5.3.1, 5.7, 8.1, 8.3 tests 6 and 9.
- **Problem:** Some layer-1 tests must run the runner in of-record mode. If the refusal under test regresses,
  nothing stops the run from writing the production ledger and the repository's card folder. The run would do this
  during the owner's suite of record. Nothing brackets the `nautilus` suite against home-directory writes.
- **Evidence:**
  - R-01 (dirty tree) and R-11 (`owner_confirmed`) exist only in of-record mode (spec:928, 938; 5.3.2 steps 1-2).
  - Of-record mode writes `config.macro_dir() / "ledgers"` (spec:459). That defaults to `~/.nextgen/macro`
    (`config.py:176-178`).
  - Of-record mode writes `docs/nautilus_bridge/runs/` and `docs/nautilus_bridge/cards/` inside the repository
    (spec:459).
  - T-HERM-02 brackets only the macro suite (`tests/macro_acceptance.py:216-234`). `nautilus` is appended after it
    (spec:750).
  - Ledger rows are immutable (`core/quant/gate_ledger.py:337-355`). One stray append leaves permanent trials in E1.
- **Proposed fix:**
  - Every `nautilus` test sets `QUANTGEN_MACRO_DIR` to a fresh temp dir before it imports the runner, and passes an
    explicit output root.
  - Each test runs inside `tests.macro_acceptance.hermetic()`.
  - A last test compares `macro_acceptance.home_listing()` before and after the suite. It also asserts that the run
    created no file under `docs/nautilus_bridge/`.
  - Tests of of-record refusals also assert that the temp ledger file does not exist after the refusal.

### QA-2

- **Severity:** major.
- **Section:** 8.2 N1, 5.2.6, 5.3.1 `--fixtures`, Step 5, Step 7A.
- **Problem:**
  - The N1 golden cannot be produced from the files the spec defines.
  - The golden file format and the comparison rule are not defined anywhere.
  - Step 7A stops the hand-off unless F1, F2 and N1 "match their goldens" (spec:1174-1175). That gate is therefore
    undefined.
- **Evidence:**
  - Probe `fx_probe_ev.py f1 --vol 4000 --pxprec 2`:
    - the single BUY order holds two `OrderFilled` events, 1,000 @ 100.00 and 9,000 @ 100.01, and its status is
      FILLED;
    - `on_order_filled` reached the strategy once, for the 1,000 only;
    - `balance_total(USD)` is `904501.00 USD` and the net position is 1,000;
    - bars seen are 4 of 12, the force-stop flag is true, there were 3 iterations, and `backtest_end` is bar 3's
      timestamp;
    - "-89.45" appears only in the log line `Stopping backtest from AccountBalanceNegative(balance=-89.45 ...)`.
  - `fills.csv` takes one row per `on_order_filled` event (spec:412). So it holds 1 row.
  - The manifest's `account_balance_usd` is 904,501.00.
  - The golden "1,000 @ 100.00 then 9,000 @ 100.01; cash -89.45" (spec:1021) matches neither file. Map 03 already
    warned: "in N1 the account showed one fill while the fill events showed two" (map03 §2.11).
  - The format of `commission` is "(str amount)" (spec:412):
    - `str(Money)` gives `"5000.00 USD"`;
    - `Money.as_decimal()` gives `5000` and `49.9`, because it divides the raw integer by `10**FIXED_PRECISION`
      (`nt:model/objects.pyx:1561-1571`).
- **Proposed fix:**
  - Define the golden JSON. Fields: `fills` (rows with fixed string formats, commission as `f"{x:.2f}"`),
    `account_balance_usd`, `final_qty`, `bars_fed`, `bars_seen`, `force_stop`, `backtest_end`, `exit_code`, `valid`,
    `invalid_reasons`.
  - Say which fields must match on both precisions. Trade ids are FNV-1a hashes of venue, raw id and `ts_init`
    (`nt:backtest/engine.pyx:8552`). They do not depend on precision, so they can stay in the golden. Their equality
    on Windows is UNVERIFIED.
  - Restate N1 as measured: `fills.csv` has 1 row (1,000 @ 100.00, commission 500.00); account 904,501.00; quantity
    1,000; 4 of 12 bars; force stop true; exit 10 with C-01 and C-02.
  - Optionally record the cache's order-event fills as a separate manifest field, so the discrepancy is visible.

### QA-3

- **Severity:** major.
- **Section:** 8.2 N3, 8.4 test 3, Step 5, 5.2.7 (K11b).
- **Problem:** N3 is "F1 with `fill = next_close` (1 ns latency)" (spec:1023). It does not state the leg or the gap
  buffer. An engineer who keeps F1's parity sizing gets a force-stopped run, not "each fill one bar later". The K11b
  exemption has no positive or negative control.
- **Evidence:**
  - Probe `fx_probe.py f1 --latency 1`, buffer 0:
    - `AccountBalanceNegative(balance=-40199)` at bar 4;
    - the strategy saw no fill;
    - 5 bars seen and exit 10.
  - Probe with `--gap 0.10`:
    - BUY 9,090 @ 104 (bar 4), SELL 9,090 @ 95 (bar 6), BUY 8,352 @ 101 (bar 8);
    - the bar-11 SELL is still `SUBMITTED` at the end;
    - cash 66,376.69 and quantity 8,352.
  - So N3 needs `leg = realism`, `gap_buffer = 0.10` and the final-bar exemption.
- **Proposed fix:**
  - Define N3 as `leg = "realism"`, `fill = "next_close"`, `gap_buffer = "0.10"` at 1x.
  - Give it a golden, `N3.json`, with the three fills above, `inflight_last_bar_exempt = 1` and `valid = true`.
  - Add N3p: the same input with `leg = "parity"`. Expect INVALID with C-03, because the exemption is realism-only.

### QA-4

- **Severity:** major.
- **Section:** 6.1, 5.2.4, 8.2, 8.4 test 5.
- **Problem:** `input.json` lists pilot values as if they were the schema. The fixtures need other values. If the
  child refuses non-pilot values, F1, F2, N1 and layer-2 test 5 cannot run. If it accepts any value, no layer checks
  the pilot values.
- **Evidence:**
  - Spec 6.1 gives these as "Value": `capital_usd` `"1000000"`, `price_precision` 9 and `volume` `"1000000000"`
    (spec:799-807).
  - `bars.csv` must carry "close with exactly 9 decimals" (spec:811).
  - 5.2.4 calls the volume "the constant 1,000,000,000" (spec:360).
  - F1 needs capital 1,005,001 (spec:978) and F2 needs 53,053 (spec:999).
  - N1 needs volume 4,000 and 2 decimals (spec:1021).
  - Test 5 needs a volume above `QUANTITY_MAX` (spec:1064).
  - Exit 20 covers a "schema" refusal (spec:314), with no definition of the schema.
- **Proposed fix:**
  - Split 6.1 into two parts:
    - what the child validates: type, range, `0 <= price_precision <= FIXED_PRECISION`, close decimals equal
      `price_precision`, `volume <= QUANTITY_MAX`;
    - what the runner asserts for a registration table in both modes: capital 1e6, 9 decimals, volume 1e9, seed 42.
  - Record both in the run record.

### QA-5

- **Severity:** major.
- **Section:** 5.3.1, 5.3.2 step 4, 10, R-10, Step 7.
- **Problem:**
  - The registration table is "a JSON file (section 10)" (spec:466), but no field names exist.
  - The data step applies only a start filter.
  - The Step 7 rehearsal (SPY 1995-01-03 to 2004-11-30) therefore cannot be written as specified. A panel built from
    `yf_SPY.csv` with no end bound contains 2004-12-01 and later, and R-10 must refuse it.
  - Most layer-1 tests and layer-2 test 7 need synthetic tables in a format nobody has defined.
- **Evidence:**
  - 5.3.2 step 4 says "Apply the start filter, require at least 300 rows" (spec:483).
  - R-10 refuses "pilot-window SPY dates" (spec:937).
  - Step 5 of 5.3.2 runs for "Pilot 1 only" (spec:485). No table field says which pilot a table is.
  - 10.1 and 10.2 are prose tables (spec:1209-1249).
- **Proposed fix:**
  - Publish the table schema with names, types and the modes in which each field is required. For example:
    `schema`, `pilot`, `family_id`, `rule`, `market`, `strategy`, `symbol`, `prices_file`, `prices_md5`, `start`,
    `end`, `rf_file`, `rf_md5`, `axes`, `grid`, `cost_bps`, `embargo`, `capital_usd`, `realism`, `domain`,
    `hypothesis`, `card_id`, `owner_confirmed`.
  - In rehearsal, apply `end` on the date index before any value is used. Run R-10 on the filtered panel.
  - Add a layer-1 test that refuses a malformed table before registration.

### QA-6

- **Severity:** major.
- **Section:** 6.3, 6.4, Step 8, 8.3 tests 3 and 5.
- **Problem:**
  - The ordering evidence is `registered_utc < first_child_utc` (spec:852). Step 8's done-when requires it
    (spec:1183).
  - The resolution of these timestamps is not stated. At one-second resolution the two stamps will usually be equal,
    because only in-memory work runs between registration and the first child (5.3.2 steps 10-12).
  - `bridge_run_id` also has one-second resolution (spec:844). Two runs of one table in the same second, as in
    layer-1 test 5, get the same run-record path. The second run silently overwrites the first.
- **Evidence:**
  - The ledger's `run_utc` uses `%Y-%m-%dT%H:%M:%SZ` (spec:879; `ui/strategy_lab_page.py:79`).
  - A complete F1 child took 0.99 s wall time on Linux (probe). Registration and reference work take milliseconds.
  - `ModelCard.save` overwrites (`core/quant/validate.py:830-834`). The spec gives no exclusive-create rule for run
    records.
- **Proposed fix:**
  - Record an event list in the run record: `{seq, kind, utc}`, with microsecond UTC.
  - Make the evidence `seq(registered) < seq(first_child)` plus `utc(registered) <= utc(first_child)`.
  - Create run records with exclusive open mode `"x"`. On a collision, add a counter suffix.
  - State that no test compares a wall-clock field.

### QA-7

- **Severity:** major.
- **Section:** 8.3 tests 3 to 6 and 13, 4.3, 5.3.
- **Problem:** Several layer-1 tests need to run the runner without Nautilus. The spec defines no seam for that.
  Test 3 cannot be built as written.
- **Evidence:**
  - The launch contract fixes the interpreter (`QUANTGEN_NAUTILUS_PYTHON`) and the script
    (`tools/nautilus/sandbox.py`) (spec:253-254).
  - Test 3's stub "exits 1 unless its `config_id` is already in the ledger" (spec:1036-1037). But `input.json`
    carries neither a `config_id` nor a ledger path (spec:792-809).
  - Rehearsal runs "the same steps" (spec:511), including step 3, `--check-env` against `env_pins.json`. A stub
    must therefore also fake the wheel identity.
  - `repo_anchor()` reads `REPO_ROOT` by default (`core/quant/gate_ledger.py:122-131`). Test 6, "in a temp git
    repository", therefore needs a repo-root parameter.
  - Test 6 needs `git`. The house convention for a missing `git` is NotRun (`tests/frozen_guard.py:13-14, 44`).
- **Proposed fix:**
  - Define the runner's callable API with test-only keyword arguments: `repo_root`, `ledger_dir`, `out_dir`,
    `child_python`, `sandbox_path`, and a `check_env` override. The CLI must not reach these in of-record mode.
  - Define the stub contract. The test writes the stub's source with the ledger path and the expected
    `config_id`s baked in. The stub writes a minimal valid manifest and empty output files.
  - When `git` is missing, test 6 raises `NotRun("OWNER: git not on PATH")`.

### QA-8

- **Severity:** major.
- **Section:** 7, 8.2 to 8.4.
- **Problem:** Most fail-closed conditions have no negative control. Some checks have only a positive test. N5 is
  listed but no test uses it, and N5 cannot occur where the spec places it.
- **Evidence:**
  - Rows of section 7 with a control:
    - layer 1: R-01, R-02, R-04, R-06 (missing file), R-07, R-09, R-10 (ledger dir, SPY date, BTC file name),
      C-08, G-01;
    - layer 2: C-01 and C-02 (N1), C-05 (volume only).
  - Parity checks with a control: P1 and P4 (N2), P3 (N7), P11 near-tie (N6).
  - Rows with no control:
    - runner: R-03 (layer-2 test 1 is positive only), R-05, R-06 (md5 mismatch, leading NaN), R-08, R-10 (output
      dir), R-11, and R-12 (partial registration, exit 3);
    - child and parent: C-03, C-04, C-05 (precision, schema, SHA-256), C-06 (timeout, missing output, bad JSON),
      C-07, C-09, C-10, C-11, C-12, C-13;
    - gate and realism: G-03, G-04 (test 14 never changes `GATE`), G-05, G-06, Z-01;
    - parity: a non-exempt P11 mismatch, P12, and "P5 to P10 never withhold";
    - K11b: the final-bar exemption, and its absence in the parity leg.
  - N5 is a "date vector with one missing row on one side" and maps to R-05 (spec:932, 1025). Both sides come from
    the one panel the parent builds before registration, so this cannot happen there. The real check is C-11, after
    the child runs. N5 appears in no test of 8.3 or 8.4.
- **Proposed fix:**
  - Add a table in 8 that maps every row of section 7 and every P-check to one named test.
  - Most can be layer-1 tests. They can use doctored manifests, fills or bars, or the stub child of QA-7.
  - Redefine N5 as a panel with a duplicated or unsorted date (R-05). Add a separate C-11 test with a doctored
    `bars_sha256`.
  - Add N6b: gap 0.006, so P11 fails and the result is WITHHELD.
  - Add a planted-warning run that still writes a card.
  - Add G-04 and G-05 tests: a scorer that mutates `GATE`, and a ledger append between registration and
    `assert_hash_at_run`.
  - Add an overdraw fixture: `gap_buffer = "-0.05"` force-stops at bar 3 in the probe. It is a second path into
    C-01, distinct from thin volume.

### QA-9

- **Severity:** major.
- **Section:** 5.5 steps 7-8, 6.3 `card`, 6.5 `results_file` and `results_md5`.
- **Problem:** The card and the run record each need the other's md5. Neither can be written first.
- **Evidence:**
  - The card is written at 5.5 step 7 with `results_md5` = "the run record path and its md5" (spec:916).
  - The run record is written at step 8 and holds `card: {path, md5}` (spec:864).
  - `ModelCard.save` writes the card once (`core/quant/validate.py:830-834`).
- **Proposed fix:**
  - Write a results file first, for example `runs/<id>.results.json` with the matrix hashes, parity and gate
    outputs. The card's `results_file` and `results_md5` point to it.
  - The run record, written last, holds the md5s of the card and of the results file.
  - Add a layer-1 test that recomputes all three md5s.

### QA-10

- **Severity:** major.
- **Section:** 6.2 `wheel_identity`, 5.3.2 step 3, Step 3.
- **Problem:**
  - The record digest is defined only as "the SHA-256 of the sorted lines `path,hash`" (spec:836-837). The joiner
    and the final newline decide the value.
  - `direct_url_sha256` is not defined: the file's SHA-256, or the archive hash inside it? It is also not stated
    whether it takes part in the `env_pins.json` equality.
  - A false R-03 refusal, or a layer-2 FAIL, follows depending on how a venv was installed.
- **Evidence:**
  - I reproduced the spec's `0ad0bfc4…07fb` over 761 entries only as `sha256(("\n".join(sorted(lines)) +
    "\n").encode())`.
  - Without the final newline the digest is `81de6b39…3c94`.
  - `scratch:ntvenv` has a `direct_url.json` whose `url` embeds the local wheel path. That makes its file hash depend
    on the install path.
  - A by-name `--require-hashes` install writes no `direct_url.json`. The spec says so itself (spec:834-835).
  - Step 3's fresh venv (null) and the existing scratch venv (non-null) would therefore disagree, if the field is
    compared.
- **Proposed fix:**
  - Define `record_digest_sha256 = sha256(("\n".join(sorted(f"{path},{hash}" for each RECORD row under
    nautilus_trader/ with a hash)) + "\n").encode("utf-8"))`.
  - Define `direct_url_sha256` as `archive_info.hashes.sha256` or null.
  - Compare `wheel_tag`, `record_digest_sha256` and `record_entries` only.
  - When `direct_url_sha256` is present, require it to equal that platform's hash in `requirements-nautilus.txt`.

### QA-11

- **Severity:** minor.
- **Section:** 5.2.7, 5.3.1, Step 5, Step 7A, 8.4 test 6.
- **Problem:**
  - The baseline is "the union of the F1, F2 and N3 module lists" (spec:441). But `--fixtures --record-baseline`
    runs F1, F2 and N1 (spec:463-465), and Step 7A records the Windows baseline with that command (spec:1168).
  - The latency path of the realism leg is never run on Windows before pilot 1.
  - The baseline includes the standard library and `sitecustomize`, while R-03 pins Python to 3.13.x only. A patch
    upgrade can make every child of a pilot INVALID after registration.
  - Layer-2 test 6 compares the three lists from which the baseline was built. It can only catch drift.
- **Evidence:**
  - Probe: F1, F2, N1 (2 decimals, thin volume) and N3 (1 ns) each load the same 976 modules. The sorted lists have
    one SHA-256, `8cf7402f…9d`.
  - The list includes 166 stdlib top-level packages and `_sysconfigdata__x86_64-linux-gnu`. It also includes
    `sitecustomize`, from `/usr/lib/python3.13/sitecustomize.py`, which loads even under `-I`.
- **Proposed fix:**
  - `--record-baseline` runs F1, F2, N1 and N3, and records their union.
  - The parent judges only `nautilus_trader*`, `nautilus_pyo3*` and modules under the venv's site-packages. The
    alternative is to pin the full Python version in `env_pins.json`.
  - Step 7A also runs one synthetic 5,600-bar set (1x, 2x and realism) through the runner with the module checks on.

### QA-12

- **Severity:** minor.
- **Section:** 8.2 N4, 8.3 test 14, 8.4 tests 2 and 6, 8.5 last paragraph.
- **Problem:** Some tests pass by construction:
  - **N4.** "Two identical grid columns" (spec:1024). If both matrices carry the identical pair,
    `walk_forward`'s `np.nanargmax` takes the lower index on both sides (`core/quant/validate.py:373`). No mismatch
    occurs, so the gap-0 exemption is never exercised.
  - **Test 14.** It asserts that `GATE` is unchanged after scoring, but never makes it change.
  - **Layer-2 test 2.** It checks `run_analysis` in the manifest, which the child writes from its own config.
  - **8.5.** The real sandbox gives no hit "once it exists" (spec:1089). That passes when the file is missing.
- **Evidence:** Probe `fx_probe_stats.py`: with `run_analysis=False`, `get_result().stats_pnls` is `{}`. With
  `True` it holds USD statistics. So an engine-side witness exists.
- **Proposed fix:**
  - N4: QUANTGEN's pair is identical, and the Nautilus copy of the higher column is raised by 1e-6. This is K3's
    1512/1638 case. Expect an exempt mismatch with gap 0.
  - Test 14 adds a scorer that mutates `GATE`. Expect G-04, exit 4 and no card.
  - The manifest records `stats_pnls_empty` from `get_result()`.
  - After Step 5, the scan test asserts that `tools/nautilus/sandbox.py` exists.

### QA-13

- **Severity:** minor.
- **Section:** 5.2.5 (buffer rationale), 7 C-04.
- **Problem:**
  - The spec says the risk engine "checks notional against cash but ignores the fee" (spec:381-383). On bar-only
    data the risk engine skips MARKET orders entirely.
  - C-04 therefore has no reachable trigger. The only overdraw guard is the force stop (C-01, C-02).
- **Evidence:**
  - `nt:risk/engine.pyx:768-789`: no quote or trade tick is cached, so it logs "Cannot check MARKET order risk: no
    prices" and runs `continue`.
  - Probe at WARNING level: the warning is printed for every order. The ERROR log level hides it.
  - Probe with `--gap -0.05`: BUY 10,526 @ 100 is a notional of 1,052,600 against cash of 1,005,001. It was not
    denied. It filled, and the engine force-stopped.
- **Proposed fix:**
  - Correct the rationale. The buffer prevents a negative balance and the force stop that follows.
  - Keep C-04 as defence in depth and say no fixture can reach it.
  - Count risk-engine warnings in the manifest, at WARNING level or through a log filter.

### QA-14

- **Severity:** minor.
- **Section:** 8.4 test 5, 7 C-05.
- **Problem:**
  - The exit-20 volume test depends on the platform. `QUANTITY_MAX` is 34,028,236,692,093 in high precision and
    18,446,744,073 in standard precision (`nt:core/rust/model.pxd:89-94`). A hard-coded 1e12 exits 20 on Windows
    and runs on Linux.
  - No control covers `price_precision > FIXED_PRECISION`.
- **Evidence:** Probe with volume 1e14 on Linux: exit 20.
- **Proposed fix:**
  - Derive the volume from the `--check-env` precision block, for example `int(QUANTITY_MAX) * 10`.
  - Add a control with `price_precision = FIXED_PRECISION + 1`.

### QA-15

- **Severity:** minor.
- **Section:** 5.6, 8.5.
- **Problem:** The expected hits of some controls are partial, or depend on how the control is written. "Exactly
  its listed rule tags" (spec:1135) cannot be checked as written.
- **Evidence:**
  - **"verbs" and "sandbox receiver".** Once rule A fires, "every hit stands" (spec:696). The existing
    `'submit_order'` text hit and the `.submit_order()` call hits are therefore also present. The table lists
    neither.
  - **"sandbox importlib".** It also gets C3 unless `importlib` is bound by `import importlib.metadata`.
  - **Import form.** 5.2.2 says every sandbox import is a `from` import (spec:319). The positive control calls
    `importlib.metadata.version(...)` (spec:1075).
  - **Evasion.** No rule or control covers `sys.modules["nautilus_trader.live.node"].__dict__[...]` in the sandbox.
    `sys` is allowed. The live modules are loaded in every run (probe: 7 `nautilus_trader.live.*` modules).
- **Proposed fix:**
  - Give each control's exact source text and its full expected hit multiset.
  - State the import form of the positive control.
  - Extend rule F to ban `sys.modules` subscripts and `__dict__` access in the sandbox, and add a control for each.

### QA-16

- **Severity:** minor.
- **Section:** 3.7, 6.1, 8.3 tests 15 and 16, 4.3.
- **Problem:**
  - `csv.writer` writes `"\r\n"` by default, whatever `newline` the file was opened with. Test 15 checks only that
    `encoding=` is passed. A CRLF `bars.csv` or output file would pass it, against the spec's "LF".
  - Test 16 asserts only the host platform's environment branch.
  - Nothing says whether the parent creates `<tempdir>/home` and `<tempdir>/tmp`.
- **Evidence:** spec:408, 811, 1053-1056, 256-257.
- **Proposed fix:**
  - Require `lineterminator="\n"`.
  - Assert `b"\r" not in` every CSV the parent or the fixtures write.
  - Give the launch builder an `os_name` argument and test both branches on both machines.
  - State that the parent creates both directories.

### QA-17

- **Severity:** minor.
- **Section:** 5.3.1 R-10, 8.3 tests 7 and 9.
- **Problem:**
  - R-10 detects the real BTC file by name. Test 9 confirms this design. A renamed copy passes.
  - `--ledger-dir` "must resolve under `tempfile.gettempdir()`". On Windows `%TEMP%` can hold 8.3 short names while
    `Path.resolve()` returns long names. Both sides must be resolved. Whether this happens on the owner's machine
    is UNVERIFIED.
  - Test 7's doctored-md5 case does not say it uses a synthetic file.
- **Evidence:** spec:458, 937, 1041-1044.
- **Proposed fix:**
  - Compare resolved paths on both sides.
  - In rehearsal, also refuse a prices file whose resolved path is the cache's `yf_BTC-USD.csv`, and any BTC-USD
    table whose file is outside the temp dir.
  - Test 7 uses synthetic files only.

### QA-18

- **Severity:** minor.
- **Section:** 5.3.2 step 2, 5.5 step 7.
- **Problem:**
  - By default `git status --porcelain` collapses a wholly untracked directory to one line, for example
    `?? docs/nautilus_bridge/runs/`. The exemption must handle that, and a collapsed line can hide a stray file.
  - A re-run overwrites `cards/<card_id>.json` (`core/quant/validate.py:830-834`), including a committed card after
    Step 10.
  - Test 6 has no case for the exemption itself.
- **Evidence:** spec:474-476, 640.
- **Proposed fix:**
  - Use `--untracked-files=all`.
  - Refuse of-record when the target card already exists.
  - Add pass and fail cases for the exemption to test 6.

### QA-19

- **Severity:** minor.
- **Section:** 5.4.1 P1.
- **Problem:** P1 exempts a decision "whose QUANTGEN margin is below 1e-9 relative" (spec:552). Only the child's
  margin formula is given (5.2.5). The parent's formula is missing; it must use the cumulative-sum SMA
  (`core/quant/strategies.py:111-116`).
- **Evidence:** spec:393-397, 552.
- **Proposed fix:** Define the parent-side margin for sma, tsmom and crypto_trend. Test the exemption with a planted
  1e-10 margin.

### QA-20

- **Severity:** minor.
- **Section:** Step 7.
- **Problem:**
  - The done-when requires the rehearsal to pick "the same column at all 14 origins" (spec:1158).
  - Synth K3 says that at origins 1512 and 1638 "the sign of that noise alone decided the match" (`research_notes/
    QUANTGEN Nautilus bridge map/00_synthesis.md:673-675`). The design accepts an exempt flip there.
  - A correct implementation whose rounding differs from the probe can fail this done-when while passing every hard
    check.
- **Evidence:** map03 §4.4 lists the chosen columns as (1, 1, 2, 2, 3, 3, 4, 4, 6, 9, 9, 6, 9, 4).
- **Proposed fix:** Done when every hard check passes. P11 mismatches are allowed only as listed exemptions. Report
  them next to map 03's (none).

### QA-21

- **Severity:** minor.
- **Section:** Step 1, Step 2.
- **Problem:**
  - Step 1 saves reports in `docs/superpowers/specs/2026-10-26-review/round<k>_<name>.md` (spec:1109). This round
    writes to `docs/superpowers/specs/2026-10-26-nautilus-review/`, where `round1_claude_security.md` already sits.
  - Step 2's done-when requires every layer-1 and layer-2 test GREEN in a scratch copy before Step 3 (spec:1119).
    That means building the whole bridge once before Steps 3 to 7 build it again, and before ruling O2, which Step
    4 waits for.
  - In the 2026-10-23 plan, the dry run was a fixture run after implementation
    (`docs/superpowers/plans/2026-10-23-execution-record.md:3, 51`).
- **Evidence:** spec:1107-1121.
- **Proposed fix:**
  - Use one review path.
  - State what the Step 2 dry run covers: the plan's RED tests failing for the right reason, or a post-Step-7 run.
    Also state which venv it uses (`scratch:ntvenv`, not hash-installed).

## Notes

Verified as stated:
- **F1, QUANTGEN side.** `pnl` and `turnover` match spec:989-990 to 7 decimals. The weights are
  (0,0,0,1,1,0,0,1,1,1,1,0) (`qg_ref.py`).
- **F1, Nautilus side, 1e9 volume, high precision.**
  - Fills: BUY 10,000 @ 100, SELL 10,000 @ 96, BUY 9,600 @ 99, SELL 9,600 @ 97.
  - Commissions: 5,000, 4,800, 4,752 and 4,656.
  - Account balance: 926,593.00.
  - Bars seen: 12 of 12. Force stop: false.
  - The rebuilt R matches spec:991. The largest gap is 1.742 bp, at t = 3. Every row is inside the P10 bound.
- **F2, Nautilus side.**
  - Fills: 1.00000000 @ 53,000, 1.00000000 @ 50,000, 0.98812079 @ 50,500, 0.98812079 @ 51,000.
  - Commissions: 53, 50, 49.90 and 50.39.
  - Account: 50,343.77. Rebuild: 50,343.770395.
  - The R values match spec:1011.
- **Determinism.** Two separate `-I` processes, each with its own hash seed, gave the same fills hash for F1 and
  for F2.
- **Engine config.** `nautilus_trader.config` exports `BacktestEngineConfig`, `LoggingConfig` and `StrategyConfig`.
  `config.environment.name` is `"BACKTEST"`.
- **Venv.** It holds exactly the 15 distributions of spec 5.1, at the stated versions, plus pip 26.2.2. It has no
  scipy.
- **Record digest.** The value and the count of 761 reproduce with a final newline (QA-10).
- **Scan.** The tree has 154 scanned files and 0 current hits. The 7 new verbs and the denied identifiers occur
  nowhere in the scanned tree or in `core/skills/macro_workflows/*.yaml`.
- **Line endings.** `tests/run_all.py`, `README.md`, `requirements.txt` and `pyproject.toml` are CRLF.
  `tests/macro_registry.csv` and `.env.example` are LF.
- **Linux container baseline.** 8 FAILs (`scratch:baseline_results.json`), as map04 §7 says.
- **Committed results file.** `qa/acceptance_results.json` has md5 `16c9baa5a1777853521d485d5078e456`. It was not
  touched.

Suite registration (5.7):
- `nautilus_tests()` follows `papers_tests()` (`tests/run_all.py:57-71`).
- `NotRun` is `tests.notrun.NotRun(reason)` with `.reason`. `run()` records it as NOT_RUN.
- An import failure is one FAIL row.
- The `OWNER:` prefix matches the README's categories (`README.md:858-862`).
- `R.OUT` patching works, because `main` reads the global `OUT` at call time (`tests/run_all.py:137`).
- `config.py` stays unchanged, so the runner must call the private `config._clean`. That is acceptable, but should
  be stated.

Unverified and other observations:
- **Standard precision.** Cross-precision equality of the F1 and F2 strings is UNVERIFIED. `as_decimal()` divides raw
  by `10**FIXED_PRECISION` in both modes (`nt:model/objects.pyx:1561-1571`), so the normalised strings should match.
  `Price` strings are formatted at the instrument precision.
- **Repo anchor.** `repo_anchor()` reads only loose ref files (`core/quant/gate_ledger.py:122-131`). After
  `git gc` packs refs it returns UNVERSIONED, and R-02 would refuse. Step 7A's done-when (`git:<commit>`) will
  surface this. The refusal message should name the cause.
- **Citations.** The verb lines in 3.2 (spec:119-120) list 9 line numbers for 8 verbs. Line 805 is `submit_order`.
  The order also differs from the names: 899 is `submit_order_list` and 1011 is `modify_order`.
