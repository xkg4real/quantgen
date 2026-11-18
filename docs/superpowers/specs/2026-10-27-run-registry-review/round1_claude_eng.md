# Round 1 review: engineering and governance

Spec under review: `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md` (draft revision 1, 1,188
lines, read in full).
Referee: Claude, engineering and governance (frozen harness, byte identity of cards and Lab outputs, hermetic tests,
append-only chain and crash safety, Windows and OneDrive, run ID uniqueness, no ledger rewrite, owner decision
points, traceability to R3).
Date: 2026-10-27. Repository at `527cdf2`.

## Verdict

**ACCEPT_WITH_CHANGES.**

The design is careful. It keeps the existing verdict path and the frozen harness intact, and it traces every R3 clause.
Most repo claims check out (list below). Three defects must be fixed before the owner approves step 0, because each
one can cause damage that cannot be undone or that breaks a binding rule:

- ENG-01: the tests can write rows into the owner's production ledger.
- ENG-02: the refactor of the only production writer has no guard against drift.
- ENG-03: the done criteria require running a test module that imports `paper_live`.

Thirteen major and nine minor issues follow.

Counts: 3 blockers, 13 major, 9 minor.

## How this review was done

- I read the whole spec, the three maps, and every repo location cited below.
- I re-ran the spec's two read-only probes (`scratch:r3_spec_probe/replay.py` and `flip.py`). They read card JSON and
  import `core.quant.validate`. I also ran one probe of my own (`scratch:r3_review_eng/s6_n1.py`). It re-decides
  S_S6_pairs_hyundai_kia from its stored `stats`, with `dsr` replaced.
- No test was run. No ledger or registry row was written. No repository file was edited except this review.
- I did not open or hash the four excluded cache files. I listed tracked cache names with `git ls-files` only.

## Claims I verified

| Spec claim | Result |
|---|---|
| Frozen harness list (`core/quant/gate_package.py:36-38`) | Confirmed |
| Lab order of work and `n_trials=len(grid)` (`ui/strategy_lab_page.py:104-127`) | Confirmed |
| `config_id` excludes span; unknown row fields refused (`core/quant/gate_ledger.py:60-61`, `:168-171`, `:190-192`) | Confirmed |
| `RegisterResult.row_md5` is a line hash on append and the content hash on dedup; `res.row["row_md5"]` is the content hash on both paths (`gate_ledger.py:346`, `:349`, `:355`) | Confirmed |
| `FamilyLedger.rows()` and `.hash()` write nothing and create no lock file (`gate_ledger.py:276-282`, `:311-321`; the lock is opened only in `append`, `:342`) | Confirmed |
| `GATE["dsr_min"]` at `core/quant/validate.py:55`; GATE `bootstrap_B` is 2000 (`:54`) | Confirmed |
| Only `dsr` depends on `n_trials` (`validate.py:505-507`; `haircut_sr` at `:529` does not) | Confirmed |
| Replay of 16 of 16 DSR cards gives the stored decision, reason and revise target | Reproduced |
| Flip n of 769, 89 and 81 under normal moments | Reproduced |
| S_S6_pairs_hyundai_kia becomes REVISE (regime) at n = 1 | Confirmed: stored `ci90` [0.079, 0.748], `prob_loss_oos` 0.073, `sr_stress` 0.315, `years_positive` 0.579, `n_trades` 66; PSR 0.964 and 0.968 both give REVISE; 0.9406 gives REJECT |
| Tier B file list matches `CANDIDATES` (`docs/asset_expansion_study.py:723-736`) and the loaders; `REFRESH` is set at module level (`:844`) | Confirmed |
| `T-RUNREG-NN` ids pass the registry id format (`tests/macro_m0_harness.py:22`); milestone tag 0 (`tests/run_all.py:93-97`); `T-LEDGER-01` is M7 at `tests/macro_registry.csv:165` | Confirmed |
| Canonical JSON (`core/ficc/macro_schema.py:303-305`); `cards.chain_append` has no lock (`core/quant/cards.py:526-539`) | Confirmed |

## Sections reviewed

Status block; 1 (scope, ruling, separation); 2 (traceability); 3 (definitions); 4 (classification, decision table,
order, readings, worked examples); 5 (data model, chain, events, schema, run ID, status, series store, registration
order, prohibitions); 6 (shadow computation, invariants, variants, method, diagnostics, stored cards, display); 7
(comparison report, Tier A and Tier B); 8 (validation plan, from the engineering and governance side only); 9
(modules, Lab changes, tests, suite registration, migration, steps, implementer rules); 10 (risks, open questions,
out of scope); references.

## Issues

### ENG-01 — blocker — 9.3, 9.2 item 4, 6.1 (tests can append to the production ledger)

**Problem.**
- `run_family` has no ledger-directory parameter. `register_trials` writes to `QC.macro_dir() / "ledgers"` unless the
  caller passes a directory (`ui/strategy_lab_page.py:67`). `run_family` never passes one (`:118`).
- T-RUNREG-01, -03 and -04 run `run_family` on synthetic closes "labelled with a real source name" (9.3). They are not
  `SYNTHETIC`, so they register rows (`:60-61`). On the owner's machine those rows go into
  `~/.nextgen/macro/ledgers/<family>.jsonl`, the production ledger.
- The page builds `LabRecorder(QC.macro_dir() / "runs", ...)` (9.2 item 4). Step 4's "synthetic UI run" therefore
  writes to the production registry, because synthetic runs are recorded (4.2 row 12).
- T-HERM-02 does not prevent these writes. It compares a snapshot after the fact (`tests/macro_acceptance.py:145-153`,
  `:198-207`), and only when the aggregator runs. The ledger is append-only and never repaired (spec 9.6). One bad
  test run leaves fake rows there for good.
- The spec says "They use temporary directories only" but gives no mechanism.

**Fix.**
- Add `ledger_dir=None` to `run_family`. Pass it to `register_trials` and to the recorder. The default keeps today's
  path.
- Every test passes temporary directories explicitly. It also sets `QUANTGEN_MACRO_DIR` to a temporary directory
  inside try/finally (`config.macro_dir()` reads it on each call, `config.py:176-178`).
- The first test of the module asserts that `config.macro_dir()` resolves under `tempfile.gettempdir()`. If it does
  not, the test fails before any `run_family` call or page-worker call.
- State that T-HERM-02 detects writes after they happen and is never the means of prevention.

### ENG-02 — blocker — 9.2 items 1 and 2 (refactor of the production writer)

**Problem.**
- `register_trials` is the Lab's only writer of production ledger rows (`ui/strategy_lab_page.py:55-82`). The spec
  extracts `_lab_rows` from it and adds a `results=` argument.
- `config_id` is the MD5 of the canonical row-set key (`gate_ledger.py:168-171`). Any change in how `params` is built
  changes `config_id`: the upper-casing and sorting (`:68-70`), the JSON round trip with `default=str` (`:75-76`), or
  the type of `cost_bps`. After such a change, every later Lab run registers existing configurations again under new
  ids. That inflation is permanent.
- T-RUNREG-01 compares runs with and without a recorder. Both arms run the new code, so the test cannot detect drift
  from today's rows.

**Fix.**
- Do not modify `register_trials` in ⑨-3a. The ledger link can come from reads:
  - after registration, `FamilyLedger.rows()` gives each `config_id`'s stored `row_md5` on both paths
    (`gate_ledger.py:346`, `:349`);
  - `appended` is true when the `config_id` was absent from the read taken before registration.
- Build planned keys and card keys with a new pure function.
- Pin that function with a test. The test writes rows through the unchanged `register_trials` into a temporary
  ledger and compares `config_id`s for a fixed set of inputs: every family, pairs order, symbol case, cost 50 against
  50.0, typed cost against table cost, and `SYNTHETIC`.
- Also record golden `config_id`s computed at `527cdf2`.

### ENG-03 — blocker — 9.3 T-RUNREG-01, 9.7 step 2 (done criteria run a paper_live module)

**Problem.** Step 2 is done when "the existing Lab tests pass unchanged" (`tests/paper_live_acceptance.py:333-359`
and others). That module imports `paper_live.config`, `paper_live.engine` and `paper_live.grid` at module level
(`tests/paper_live_acceptance.py:19-21`). Running it, or importing it, executes `paper_live` modules. The binding
rules forbid that in this environment.

**Fix.**
- Copy the assertions of `test_17` and `test_18` (`:333-359`) into `tests/macro_r3_registry.py`. They need only
  `ui.strategy_lab_page` and `gate_ledger`.
- Mark `tests/paper_live_acceptance.py` as owner-run only.
- State both in 9.3 and in 9.7 step 2.

### ENG-04 — major — 9.2 item 3, 6.1, 6.7 (hook failures are not contained)

**Problem.**
- The recorder hooks run inside `run_family`. The spec does not say that a hook failure is contained. Examples:
  - `ledger_before()` calls `FamilyLedger.hash()`. On a broken chain it raises `LedgerRefused`
    (`gate_ledger.py:311-316`), before `register_trials` would have raised.
  - The STARTED append raises on a broken registry chain or a duplicate run ID (5.2, 5.5).
  - The series write can raise `PermissionError` on Windows (ENG-15).
- Any of these aborts `run_family`. The page then shows an error and no verdict, or a different error text than
  today (`ui/strategy_lab_page.py:236-240`). That breaks the promise of 6.7 and the identity claims of 6.1.
- `failed(stage, exc)` runs inside an `except` block. If it raises, its exception replaces the original one.
- The hooks receive mutable arrays (`M`, `wf`). An in-place operation, such as rounding for a fingerprint, would
  change the verdict.

**Fix.**
- Route every hook call through one wrapper. The wrapper catches `Exception`, records the error, disables the
  recorder for the rest of the run, and returns.
- Call `failed()` in a nested try, so that the original exception is re-raised unchanged.
- Pass read-only views to the hooks (`v = a.view(); v.flags.writeable = False`).
- Extend T-RUNREG-01 to the failure paths. Each must give the same exception type and message, and the same ledger
  bytes, with and without a recorder:
  - no symbols (`:91`) and no cost row (`:96`);
  - `HistoryError`;
  - a broken ledger chain;
  - a broken registry chain;
  - a recorder that raises in every hook.

### ENG-05 — major — 6.4, 6.1 item 6, 10.1 risks 6 and 12 (shadow re-scoring mutates GATE)

**Problem.**
- Each shadow variant calls `score_strategy` again inside a `GATE["bootstrap_B"]` override. `GATE` is module state,
  and its default B is 2000 (`validate.py:54`).
- The Lab's own override (`ui/strategy_lab_page.py:124-129`) does not take the shadow's lock. The Run button is never
  disabled (`:228`, `:279`, `:283`), so two runs can overlap. One interleaving:
  1. The shadow saves 2000 and sets 1000.
  2. A second Lab run saves 1000.
  3. The shadow restores 2000.
  4. The Lab run restores 1000.

  `GATE` then stays at 1000 for the rest of the process.
- Each variant also repeats the two bootstraps and the CSCV (`validate.py:501`, `:508`, `:520`). Latency grows with
  the number of distinct n.

**Fix.**
- Compute shadow decisions without re-scoring:
  1. Copy the existing `StrategyScore` with `dataclasses.replace`.
  2. Set `n_trials = n` and `dsr = V.deflated_sharpe(wf.pnl, n_trials=n, sr_sd_daily=s)`, where `s` is computed from
     `M` as at `validate.py:505-506`.
  3. Call `V._decide_strategy` on the copy (`validate.py:536`).
- This is the replay that 6.6 already uses for cards. It writes no `GATE` value, draws no bootstrap and takes
  milliseconds.
- Keep one full `score_strategy` call per variant in T-RUNREG-06 only, as a cross-check.
- The module lock and invariant 6.1 item 6 then become unnecessary.

### ENG-06 — major — 9.2 item 4, 6.7 (shadow card can land under another run)

**Problem.** The worker clears `host.controls` when a run starts (`ui/strategy_lab_page.py:228`) and fills it at the
end (`:277`). The spec appends the shadow card after the display, from the same worker. Suppose the operator starts
run B while run A's shadow is still computing. A's shadow card is then appended under B's verdict. A "would be
REJECT" line shown beside the wrong run is the hazard of risk 1.

**Fix.**
- Give each click a generation number. Before appending, the shadow checks that the host still shows its run (run ID
  match). If it does not, it writes FINISHED only.
- Disable the Run button until FINISHED is written, or queue runs.
- Add a test with two overlapping synthetic runs.

### ENG-07 — major — 5.2, 5.3, 5.6, 9.2 items 3 and 4 (crash safety and the event model)

**Problem (a): one late event holds everything.**
- The results, the existing verdict and the shadow all live in one FINISHED event, written after the shadow.
- The worker's lines after `run_family` (`ui/strategy_lab_page.py:241-277`) are outside its try. A crash, a closed
  window or a rendering exception there loses the record of a completed run. The fold then infers ABORTED after
  6 hours and counts it as FAILED_AFTER_STATS.
- The series file written at PNL_COMPUTED has no event that links it to its run.

**Problem (b): two writers for FINISHED.** Both `failed(stage, exc)` (9.2 item 3) and the page's `except` branches
(item 4) are said to record the failure. FINISHED is meant to be written once, but the store refuses duplicate STARTED
events only (5.5).

**Problem (c): a torn line stops the registry for good.**
- A power loss during an append can leave a torn last line. The chain then breaks.
- Reads and appends refuse a broken chain, and "the registry never repairs a chain" (5.2).
- The UI is fail-open, so recording stops silently, and no recovery procedure exists.

**Fix.**
- For (a), write PROGRESS events:
  - at PNL_COMPUTED: `series_ref`, per-configuration fingerprints, the data block;
  - at SCORED: the results and the existing verdict;
  - then a SHADOW event;
  - then FINISHED with the status.

  Infer an orphan's stage from its last PROGRESS event. Wrap the worker body after `run_family` in try/finally, so
  that FINISHED is always attempted.
- For (b), make the page the only writer of FINISHED. Refuse a second FINISHED per run ID under the lock, and pin
  that in T-RUNREG-02.
- For (c), define a recovery that never rewrites:
  - on a broken tail, the module refuses;
  - an owner-approved command starts a new segment, `run_registry.<n>.jsonl`;
  - the segment's first event records the old file's byte length, its MD5 and its last verified line;
  - the old file stays untouched.

  Pin it with a test that cuts a line in half in a temporary file.

### ENG-08 — major — 3.4, 5.4, 4.2 rows 1, 5 and 8b, 10.1 risk 3 (fingerprints drift with the environment)

**Problem (a): a library upgrade turns re-runs into new experiments.**
- The experiment key includes `behaviour_sha256` (3.7), and the canonical panel comes from a seeded generator.
- numpy's policy guarantees bit-generator streams across versions, not the output of distribution methods (NEP 19,
  https://numpy.org/neps/nep-0019-rng-policy.html; not re-read in this session: UNVERIFIED).
- Library versions also move the results of strategies that call numerical code: `risk_parity` calls
  `core.quant.optimize` (`core/quant/strategies.py:351-366`), and `pairs` runs ADF tests.
- After an upgrade, every fingerprint can change while the code stays the same. Every configuration then becomes a
  new key under row 8b, and the registry's literal N_raw doubles.
- That counts simple re-runs as new experiments, which R3's clause on re-runs forbids. Risk 3 names platform
  differences only.

**Problem (b): fingerprints run before STARTED.** They are computed for every grid point, before STARTED and before
the data load: G strategy calls on 1,500 × 4 sessions. This adds latency before the verdict, which contradicts "with
today's latency" (6.4). An exception while fingerprinting would also prevent STARTED from being written.

**Fix.**
- Store an `env` block in STARTED (Python, numpy, scipy and pandas versions; platform), together with the SHA-256 of
  the canonical panel's bytes.
- Generate the panel from integer bit-generator output with fixed mapping code, or ship it as a fixture.
- Add a rule: a fingerprint that changed while `fn_source_sha256` and the file digests did not is class ENV_DRIFT. It
  adds 0 to N_raw and is flagged. It is not row 8b.
- Compute fingerprints after the display, in their own event; they do not depend on real data. Cache them by
  (`fn_source_sha256`, file digests, θ, cost, panel hash, env).

### ENG-09 — major — 3.11, 4.2 rows 13 and 13a, 4.3, 6.2 (classification is not deterministic as written)

**Problem.**
- LEDGER_ONLY is "a `config_id` in the family ledger that no registry key holds". When FINISHED is written, the
  ledger already holds the run's own new rows (registered at `ui/strategy_lab_page.py:118`), and the run's STARTED
  event holds its keys. Read literally, either ADOPTED can never trigger, or every SEARCH becomes ADOPTED.
- Reports recompute classes as of an instant. Ledger rows carry the wall-clock `run_utc` (`:79`); registry events
  carry an injected clock. A time cut over both mixes two clocks.
- 4.3 step 6 covers cases where only one thing differs. It does not cover combinations. After a code update, the gate
  version and the data usually differ together.
- Planned keys (typed symbols) and registered keys (resolved symbols, `:118`) can differ. The spec does not say which
  set is classified.

**Fix.**
- The ledger state for a run is the snapshot named by its `hash_before` (`FamilyLedger.snapshot`,
  `gate_ledger.py:323-330`).
- For that run, a row is LEDGER_ONLY when its `config_id` is in that snapshot and in no earlier registry event. Rows
  the run appended (`ledger_link.rows[].appended`) are SEARCH.
- Reports cut the ledger at the latest `hash_after` recorded at or before `as_of`, never by `run_utc`.
- Classify registered keys. Use planned keys only when the run failed before registration.
- Set a precedence for combined differences: data first, then gate version, then seed or B. Add one T-RUNREG-05
  scenario per combination.

### ENG-10 — major — 4.1 principle 2, 4.2 rows 8c, 14 and 15, 5.3 (count-lowering events need owner sign-off)

**Problem.**
- Three paths change counts on a person's statement alone:
  - an ANNOTATION can remove a configuration from N_raw (4.1 principle 2);
  - an ANNOTATION plus a SUPERSEDED event turns a logic change into "the same trial" (row 8c);
  - a BACKFILL event adds reconstructed trials (row 14).
- Each needs only "who, when, why". Anyone with write access to the file, Claude included, can lower the primary
  count. That is the selection freedom R3 is meant to remove.
- No module or command writes these events (9.1 lists none). In practice they would be written by ad hoc scripts that
  bypass the schema checks.

**Fix.**
- A count-lowering event enters the primary reading only when it carries an `owner_ruling` field. That field cites a
  verbatim entry in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, with channel and date.
- Without that field, the event appears only in a secondary reading, "with unratified annotations".
- Add `tools/r3/annotate.py`. It writes these events through `run_registry`'s lock and validation.
- The report lists every count-changing human event and its effect.

### ENG-11 — major — 6.6 "Counts for a card", 7.3, traceability T16 (a card's trial history has no time bound)

**Problem.**
- A card's count is |ledger `config_id`s ∪ card grid keys|, with no filter on time or span. A Lab run made after a
  card was written, on another universe, then counts as that card's trial history.
- The repo's own rule counts only rows that ran before the fix time and overlap the evaluation span (`selection_factor`,
  `gate_ledger.py:700-722`: `parse_utc(r["run_utc"]) < fixed_at` and `overlaps(...)`).
- Cards store `created` (for example `docs/asset_expansion/cards/S_E8_pairs_kodex_tiger.json:179`, `2026-09-27`) and a
  data span.
- So 7.3's "what would flip it" can blame a flip on trials that could not have influenced the card's selection. The
  reason that R3 asks for ("그 근거") would then be wrong.
- The union also ignores the study's own sibling cards in a family: E8 holds 4 cards (32 configurations), E1 holds 2
  and E2 holds 2. That is the only trial history that is actually stored.

**Fix.** Print three readings per card:

1. **Pre-card:** rows with `run_utc` before `created` whose span overlaps the card's data span, plus the sibling
   cards' grid keys.
2. **All-time:** today's definition.
3. **Stored N.**

Section E labels a flip COUNT only under reading 1. A flip that appears only under reading 2 is labelled
LATER_SEARCH. The owner's list states which reading is of record.

### ENG-12 — major — 10.2, 9.7 step 0 (decision points are not staged)

**Problem.**
- Step 0 asks the owner to answer Q1 to Q15 before ⑨-3a starts.
- Q1 to Q4 and Q8 choose verdict criteria: which N, which scope, which rounding, whether N may fall below G, and
  whether a validation is a trial. R3 puts those choices after the separate validation, at ⑨-3d.
- Q3 is posed together with its outcome: "This decides S_S6_pairs_hyundai_kia". Choosing a rule while seeing which
  card it flips is the forking-paths problem the spec itself cites (Gelman & Loken 2013).
- Q9 to Q14, by contrast, are build decisions that are needed now.

**Fix.**
- Split 10.2 into two lists:
  - **needed before ⑨-3a:** Q5 to Q7 as display conventions, Q9 to Q14, the fail-open choice (ENG-16) and the scope
    questions (ENG-23);
  - **decided at ⑨-3d**, by the pre-registered criteria of ⑨-3c: Q1 to Q4, Q8 and Q15.
- Remove the card's name from Q3. The ⑨-3c acceptance criteria choose the rounding rule.

### ENG-13 — major — 8.5 A1, 8.6, 9.7 steps 6 and 8 (the validation can be loosened or shaped after the fact)

**Problem.**
- (a) A1 accepts a false-positive rate of at most 0.05 + 2 · MCSE. 8.6 cuts replications when a layer runs longer
  than 2 hours. Fewer replications widen the MCSE, which loosens A1, so an under-run criterion passes more easily.
- (b) The of-record ⑨-3b report (step 6) comes before the ⑨-3c study (step 8). Nothing freezes the ⑨-3c designs,
  criteria and seeds first. The validation could therefore be shaped after the flips are known.

**Fix.**
- (a) A1 uses the planned MCSE: 0.0022 for Layer A, 0.005 for Layer B. A layer whose replications were cut is
  reported as "inconclusive", never as a pass.
- (b) Before step 6, freeze section 8 (designs, criteria, seeds, rounding candidates) in a commit, and record its hash
  in the rulings log. The null study refuses to run when the design hash differs.

### ENG-14 — major — 9.4, 9.7 step 1, 5.1 (no permitted command checks T-HERM-02)

**Problem.**
- `python -m tests.macro_r3_registry` calls `run_module`, which applies only the T-HERM-01 guard
  (`tests/macro_acceptance.py:237-264`).
- T-HERM-02 runs only as the last test of the aggregator (`:216-234`). The aggregator is reached through
  `tests/run_all.py`, which rewrites `qa/acceptance_results.json` (`tests/run_all.py:136-137`) and is barred here.
- So step 1's done criterion "T-HERM-02 passes" has no permitted command.
- 9.4 says the aggregator "wraps every test in the T-HERM-01 and T-HERM-02 guard". That is inaccurate. `_wrap` takes
  the snapshot; T-HERM-02 is a separate final check (`:145-153`, `:198-207`). It detects writes; it does not prevent
  them (ENG-01).

**Fix.**
- Give the module its own first and last tests. They take and compare `macro_acceptance.snapshot()` (`tree_md5s` and
  `home_listing`), so that `run_module` checks T-HERM-02's conditions.
- Name the exact command to use in the container.
- Import `ui` modules lazily, and return NotRun when `flet` is missing.

### ENG-15 — major — 3.3, 5.1, 5.2, 5.7, 9.6 (Windows and OneDrive are not handled)

**Problem.** The registry and the of-record report run on the owner's Windows machine. The repository sits under
OneDrive (`research_notes/QUANTGEN v2 integration map/code_tests_data.md:684`). Beyond the lock pattern, the spec
has no Windows handling:

- **(a) Replacing files.** `os.replace` of a series file can fail with `PermissionError` while Defender, OneDrive or
  the indexer holds a new file. The Nautilus spec retries 10 times over 5 seconds for exactly this
  (`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:795-797`, OPS-R2-3).
- **(b) Hashing sources.** The house precedent hashes source text with CRLF normalised to LF, because OneDrive or an
  editor can change bytes (`research_notes/QUANTGEN v2 integration map/spec_M7_gate_package.md:712`). The spec relies
  on `.gitattributes`, which governs git checkouts, not editors.
- **(c) The repo anchor.** `repo_anchor` reads only a loose ref file (`gate_ledger.py:124-131`). A packed ref gives
  UNVERSIONED. This is already flagged for the owner's clone
  (`research_notes/QUANTGEN Nautilus bridge map/02_quantgen_gate_ledger_lab.md:557`).
- **(d) Sync folders.** The OS byte lock does not work across machines. If `QUANTGEN_MACRO_DIR` points into a sync
  folder, two machines fork the chain through conflict copies.
- **(e) False T-HERM-02 failures.** Every Lab run now writes under `~/.nextgen/macro`, which T-HERM-02 snapshots. Using
  the Lab during the owner's suite run trips it falsely. This failure mode was already seen with the cockpit's writes
  (`tests/macro_acceptance.py:113-117`).

**Fix.**
- (a) Use a retry wrapper like the Nautilus spec's. If it still fails, record `series_error` and keep the run.
- (b) Hash LF-normalised text for `fn_source_sha256` and `files`. Store the raw-byte hashes too.
- (c) State that `repo_anchor` may read UNVERSIONED on the owner's clone, and that the `files` digests then carry the
  version.
- (d) Refuse a runs directory whose resolved path lies under a OneDrive root (the `OneDrive`, `OneDriveConsumer` or
  `OneDriveCommercial` environment variables), unless the owner overrides.
- (e) Document that the owner must not use the Lab during a full suite run, or move the registry outside the
  snapshot (an owner question).

### ENG-16 — major — 6.7 last bullet, 10.1 risk 11 (fail-open leaves silent gaps)

**Problem.**
- When the registry fails, the run proceeds unrecorded. The only trace is a muted notice on screen.
- TOTAL and the failed-run counts then have silent gaps. After a torn tail (ENG-07), every later run is unrecorded.
- The spec says blocking "would change today's behaviour, which R3 forbids". R3 forbids changing verdict criteria; it
  says nothing about availability. Fail-open is an owner choice, not a given.

**Fix.**
- Keep fail-open as the default, but record outages. On any registry failure, append one line to a separate file,
  `runs/unrecorded.jsonl`, that does not depend on the chain: time, family and error. If that write also fails, show
  the notice in the error colour.
- The report prints the outage windows, with the ledger's growth inside them as a lower bound.
- Add the choice between fail-open and fail-closed to the owner's list.

### ENG-17 — minor — 3.1, 4.2 row 3, 5.6, 5.8 (stage boundaries contradict each other)

**Problem.**
- STARTED is written "before `:104`". But `run_family` raises for no symbols (`:91`) and for no cost row (`:96`) before
  that point. By 3.1 these are not runs, yet row 3 lists "no cost row" as FAILED_BEFORE_STATS.
- The table in 5.8 counts a failure in `pnl_matrix` as FAILED_AFTER_STATS. By 5.6 that failure sits below
  PNL_COMPUTED, because the hook runs after `:114`, so it is FAILED_BEFORE_STATS.
- "Too few sessions" is raised in two places: in `align_panel` before any statistic exists
  (`core/quant/strategies.py:60`), and in `walk_forward` after the P&L matrix exists (`core/quant/validate.py:367`).

**Fix.**
- Either write STARTED at function entry, with cost and keys nullable, or state that validation errors raised before
  the load are not runs.
- Correct the 5.8 row.
- List both "too few sessions" sites, each with its class.

### ENG-18 — minor — 3.12, 6.2, 6.3 (N_eff computability is under-specified)

**Problem.**
- N_eff over series from different runs needs one aligned matrix. `n_eff` aligns dated pandas Series by index
  intersection. It refuses unequal undated arrays, a common window under 20 rows, and a constant column
  (`gate_ledger.py:421-457`).
- A configuration that never trades has a constant cash P&L column. That one column makes the whole scope
  CorrUnavailable.
- LEDGER_ONLY rows make E-FAM and E-MKT unavailable for every family that existed before the registry.

**Fix.**
- State that series are passed as pandas Series indexed by the stored day number.
- State how CorrUnavailable is handled: print the reason, and exclude constant columns only in a labelled secondary
  reading.
- State the expected availability of E-FAM on the owner's machine, probably none before Q11.

### ENG-19 — minor — 6.1 item 3, 6.4, T-RUNREG-01, T-RUNREG-06 (equality checks fail on NaN)

**Problem.**
- Plain equality fails on NaN. `bench_p`, `bench_diff` and `bench_ci` are NaN for pairs (`validate.py:482-484`,
  `:521`), so pairs runs would fail the invariance checks.
- 6.1 item 3 exempts only `run_utc`. T-RUNREG-01 exempts `run_utc`, `row_md5` and `prev_row_md5`.
- If both arms of T-RUNREG-01 use one temporary ledger, the second arm only dedups and writes nothing to compare.

**Fix.**
- Use NaN-aware equality: both values NaN, or compare canonical representations.
- Make 6.1 item 3 match T-RUNREG-01.
- Use two temporary ledgers in T-RUNREG-01.

### ENG-20 — minor — 4.5, T-RUNREG-05 (the C3 lattice argument assumes no ties)

**Problem.**
- The odd-ninths argument holds only when no vote is zero. `np.sign` returns 0 on an exact tie
  (`core/quant/strategies.py:344-345`).
- With one zero vote, the composite takes even ninths. h = 0.2 and h = 0.3 then act differently, because 2/9 ≈ 0.222
  lies between them.
- Upbit KRW-BTC closes are tick-rounded, so ties are possible (UNVERIFIED for the cached series).
- A continuous canonical panel has no ties, so it cannot "settle" the study comment.

**Fix.**
- Say that the canonical panel shows the tie-free case only.
- C3's semantic duplicates stand only with equal real-data fingerprints. Row 6 already requires those when both runs
  share a `data_md5`.
- Add a tick-rounded series to the canonical panel or to T-RUNREG-05.

### ENG-21 — minor — 7.4, T-RUNREG-09 (Tier B allow-list needs hardening)

**Problem.**
- (a) When a cache file is missing, `_cached` calls the network loader and writes a CSV
  (`docs/asset_expansion_study.py:70-76`). `yfinance` and `curl_cffi` are installed here. Whether T-HERM-01's socket
  patch stops curl_cffi's libcurl transport is UNVERIFIED.
- (b) `rf_daily` swallows any `Exception` from `fred` and substitutes 3 % (`:148-153`). An allow-list refusal there
  would silently change the result, and the drift check would mislabel it as GATE drift.
- (c) T-RUNREG-09 says only `tier_b.py` names the excluded files. The test itself must name them in order to scan for
  them. An allow-list needs no deny list at all.

**Fix.**
- The wrapper raises before `exists()` for any name outside the list, and also when a listed file is missing. It never
  calls the loader.
- Its exception derives from `BaseException`, so that `except Exception` cannot swallow it. The tool asserts that each
  listed file was read exactly once.
- In the test, build the excluded names from fragments, or scan for the allow-list instead.

### ENG-22 — minor — 5.2, 5.7, 10.1 risk 5 (verification cost grows with history)

**Problem.**
- Every append and every count re-reads and re-verifies the whole event log, as the ledger does.
- FINISHED events are large: grid, per-configuration fields, stats, classes and eight variants. The spec sizes only the
  series store.
- Verification time grows linearly with history.

**Fix.**
- Estimate the bytes per event.
- Keep an in-process cache of the verified prefix (byte offset and the MD5 of the last line), and verify only the new
  tail.
- State a segment size at which the segment mechanism of ENG-07 also rolls over.

### ENG-23 — minor — 1.2, 10.3, traceability T1 and T3 (two readings of R3 are taken without asking)

**Problem.**
- (a) "전환" (switch) is implemented as shadow only; the Lab's displayed N stays G until ⑨-3d. This is a defensible
  reading of "기존 카드의 판정 기준은 이 단계에서 변경하지 말고". But the Lab's live verdict is not an existing card.
- (b) "각 전략 실행에 고유 ID" is applied to Lab runs only. Study runs and bridge runs are out of scope (10.3), yet the
  cards come from study runs.

**Fix.** Add both as owner questions, with the drafted defaults.

### ENG-24 — minor — 1.1, 9.7 (locked holdout and audit-first order)

**Problem.**
- (a) Rule ⑧-2 locks all data from 2027-01-01 for every design
  (`docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:122`). The Lab always loads the latest sessions
  (`ui/strategy_lab_page.py:104`), so from 2027 every real-data Lab run touches the locked holdout. The registry
  records spans but flags nothing.
- (b) Ruling ①-2 puts the audit first (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:42-47`). Audit item P-01 names
  `ui/strategy_lab_page.py`. D-01 and D-02 target `core/quant/history.py` and will change cleaned data
  (`docs/audit/2026-10-27/00_request.md:20-23`). ⑨-3a edits the same page and hashes `history.py`.

**Fix.**
- (a) Flag HOLDOUT_TOUCHED when a span ends on or after 2027-01-01, and list such runs in the report.
- (b) State the order: ⑨-3a's edits to `ui/strategy_lab_page.py` start after the audit's proposed patches to that file
  are decided. A D-01 or D-02 fix is a data change, recorded as REMEASURE.

### ENG-25 — minor — 5.4, 5.5, 6.7, 7.1, 8.5 (small consistency items)

- **5.5 duplicate run ID.** On a duplicate run ID, the recorder draws a new token and retries a bounded number of
  times; it does not fail. The regex should use `[0-9]`, because Python's `\d` matches all Unicode digits.
- **5.4 writer.** `writer` is fixed to the Lab page. Events written by a person need their own writer and identity
  fields.
- **5.4 Data.** `per_symbol` omits `History.adjustment` (`core/quant/history.py:55-64`). That field says whether the
  closes are total-return or split-only.
- **7.1 card loading.** `V.load_cards` skips unreadable files silently (`core/quant/validate.py:847-856`). `compare.py`
  must assert 34 cards and 16 DSR cards, and list any file it skipped.
- **6.7 scorecard line.** The scorecard reads report CSVs from `macro_dir()` when the page is built. Inject the path,
  as tests already patch `CARDS_DIR` (`tests/macro_ui_views.py:263-283`). Show the report's `as_of`, and survive a
  malformed CSV.
- **8.5 A8.** Byte identity holds on one platform with pinned library versions. Say so.

## Traceability to R3 (engineering view)

| R3 clause | Traced in the spec | Remaining gap |
|---|---|---|
| T1: move counting to a ledger basis | Yes (shadow) | Shadow-only reading not confirmed by the owner (ENG-23) |
| T2: keep it apart from stricter verdicts | Yes | Holds only if hooks are contained (ENG-04) and GATE is not mutated (ENG-05) |
| T3: a unique ID per run | Yes | Lab runs only (ENG-23); collision retry (ENG-25) |
| T4 to T10: the record fields | Yes | Strategy version weakened by environment drift (ENG-08); data adjustment missing (ENG-25); status lost on crash (ENG-07) |
| T11: TOTAL apart from valid experiments | Yes | Gaps when the registry fails open (ENG-16) |
| T12: criteria per kind of trial | Yes | Re-runs after a library upgrade counted as search (ENG-08); combined differences (ENG-09); human overrides (ENG-10) |
| T13 and T14: compute in parallel and compare | Yes | Replay instead of re-scoring (ENG-05) |
| T15: do not change card criteria | Yes | — |
| T16: the cases that flip, with reasons | Yes | Card trial history not time-bounded (ENG-11) |
| T17: validate the criterion separately | Yes | Pre-registration and the MCSE loophole (ENG-13) |
| T18: the owner decides afterwards | Yes | Criteria questions asked too early (ENG-12) |
