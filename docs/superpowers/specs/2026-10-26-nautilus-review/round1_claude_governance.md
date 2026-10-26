# Round 1 referee report: governance and compliance (Claude)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 1 (untracked, 1,400 lines). I read all of it.
Repo: QUANTGEN at `6f7c610`, branch `claude/amazing-gauss-tdiguu`.
Referee: a Claude subagent with the governance and compliance persona. It ran read-only in the repo clone, not in a bundle.
Probes: `scratch:referee_governance/scan_probe.py` and `mods.py`. Neither used pilot-window data. Neither changed a tracked file.

Citation keys:
- `spec:<line>` is the spec under review.
- `file:line` is a QUANTGEN path at `6f7c610`.
- `nt:<path>:<line>` is `nautilus_trader` 1.231.0 in `scratch:ntvenv`.
- `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
- `council:` is `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`.
- `split-spec:` is `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`.
- `map04:` and `synth:` are files in `research_notes/QUANTGEN Nautilus bridge map/`.

## Verdict

**ACCEPT_WITH_CHANGES.**

No blocker. As written, nothing in the design must break a house rule. But seven major issues would let an engineer, or a
later Claude session, break a rule or decide something only the owner may decide. All seven can be fixed in the text of
the spec. None needs a new measurement.

The main findings:
- The authority statement claims more than the owner's two quoted sentences give. Code steps are not gated on the
  owner's rulings O1, O3 and O13 (GOVERNANCE-1).
- O3 asks the owner about DO-NOT-BUILD item 21 without the most relevant fact. A Nautilus `Strategy` is designed to go
  live with no code changes (GOVERNANCE-2).
- Nothing in the runner stops `--mode of-record` from running somewhere other than the owner's machine and production
  ledger (GOVERNANCE-3).
- The rehearsal guard on the unseen pilot windows is weak for BTC and has no rule for the SPY end date
  (GOVERNANCE-4).
- The spec decides on the owner's behalf that a gate run on real pre-window data is not a trial. It still offers the
  owner a 1995 start (GOVERNANCE-5).
- The card's verdict comes from the Nautilus matrix. Nothing checks it against QUANTGEN's own verdict when the two
  pick the same columns (GOVERNANCE-6).
- O1's own default, an unchanged global interpreter, is checked once on Linux and never on the interpreter of record
  (GOVERNANCE-7).

## Sections reviewed

- Header: Status, Inputs, citation keys, Owner context (spec:1-53).
- §1 scope and the TRADEGEN boundary (spec:55-79).
- §2 owner rulings O1 to O13 (spec:81-100), against synth §3.1 and map04 §9-§10.
- §3 binding constraints 3.1 to 3.11 (spec:102-203).
- §4.3 launch contract (spec:247-266).
- §5.1 requirements file and §5.2.7 module baseline (spec:270-295, 420-443).
- §5.3.1 and §5.3.2 runner modes and order of operations (spec:445-512).
- §5.4.2 and §5.5 selection and gate hand-off (spec:570-645).
- §5.6 T-RO-01 amendment (spec:647-729), checked with the repo's own `_offences`.
- §5.7 and §5.8 suite and registry (spec:731-786).
- §6.4 ledger rows (spec:869-896).
- §8.5 and §8.6 scan controls and container test rules (spec:1069-1100).
- §9 steps and done-when (spec:1102-1200).
- §10 pilots, expected verdicts and data-access history (spec:1202-1295).
- §11 risks 1, 2, 3, 13, 14 and 22 (spec:1297-1323).
- §12 out of scope, §13 open questions, and Appendices A and B (spec:1325-1400).
- House sources:
  - split-spec §2, §3.1 to §3.4 and the referee rules (split-spec:37-181, 395-531);
  - council item 21, §3.10, rule 01 and the T-RO-01 row (council:6162, 1255-1263, 464, 500, 5605);
  - `research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:52-56`;
  - `tests/frozen_guard.py`, `tests/macro_m0_harness.py`, `core/quant/gate_ledger.py` and `ui/strategy_lab_page.py`;
  - `README.md:30-38, 365-374, 924-929`;
  - `paper_live/engine.py`, `paper_live/replay.py` and `grokteam/book.py` (read only, never run);
  - `reports/Korean resident trading venue legality.md:15, 21, 100`.

## Issues

### GOVERNANCE-1: the authority statement claims more than the owner's words give, and code steps are not gated on the owner's rulings

- **Severity:** major.
- **Section:** header "Owner context" (spec:35-53); §2 preamble (spec:83); O1 (spec:88); §9 Steps 1 to 4
  (spec:1107-1138).
- **Problem:**
  - The Status block is accurate. It says owner approval is "not given". It says the plan starts after the owner's
    rulings (spec:8-10).
  - The Owner context then says the owner's words authorise "building the bridge on the feature branch"
    (spec:40-43).
  - §2 says the default column "is what this draft builds on until the owner rules" (spec:83).
  - O1's cost column assumes branch files already exist when O1 is refused: "The branch files ... are deleted"
    (spec:88).
  - Only Step 4 waits for a named ruling: "Claude, after ruling O2" (spec:1133). Step 3 waits for nothing, yet it adds
    `requirements-nautilus.txt` and installs Nautilus with `pyarrow` (spec:1123-1131).
  - Synth gated O1 before Step 3 and O3 before Step 1 (synth:282, 284). The spec dropped that "Blocks" column.
  - So a team starting today could build Steps 3 to 7 on the defaults before the owner rules. Five house sources say a
    new dependency needs the owner, and one bans `pyarrow` by name
    (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`; map04:134-140). Building first
    would decide O1, O3 and O13 on the owner's behalf.
  - The two quotes are in no repository file. A grep finds them only in this spec. A later reader cannot check them
    (UNVERIFIED). The 2026-10-23 precedent wrote the approval date and its scope into the Status block
    (split-spec:12-16).
- **Evidence:** spec:8-10, 40-48, 83, 88, 1107-1111, 1133; synth:282-284;
  `research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`;
  `research_notes/QUANTGEN v2 integration map/spec_tests_registry.md:401`; split-spec:12-16.
- **Proposed fix:**
  - Replace "What those words authorise" with one line: they authorise drafting this spec and running referee round 1,
    nothing more.
  - Add a "Blocks" column to §2:
    - O1 blocks Step 3; O2 blocks Steps 4 and 5;
    - O3 and O13 block Step 2 onward; O5 blocks Step 7;
    - O6, O7 and O11 block Step 8; the pilot-2 table (GOVERNANCE-8) blocks Step 9.
  - State: "No file outside `docs/superpowers/` changes before Step 1's done-when."
  - Reword spec:83 to "the default the owner is asked to accept".
  - Write down the date and channel of the owner's two quoted sentences.

### GOVERNANCE-2: O3 leaves out that a Nautilus strategy goes live with no code changes, and §1 drops map 04's boundary rules

- **Severity:** major.
- **Section:** O3 and O13 (spec:90, 100); §1 TRADEGEN bullet (spec:75-77); §12 (spec:1327-1328).
- **Problem:**
  - Item 21 forbids "Any order, cancel, withdrawal, deposit-address or transfer path, or a broker execution adapter,
    inside this programme" (council:6162). QUANTGEN rule 01 adds "and nothing to switch on" (council:464, 500, 1257).
  - O3 asks only about the adapter half. It does not read the order-path half or "nothing to switch on" together.
  - It also leaves out the fact that matters most for "nothing to switch on". The Nautilus docs say:
    - "NautilusTrader deploys backtested strategies to live markets with no code changes" (`scratch:nt_docs/live.md:3`);
    - "the same source code can be used for backtesting and live trading" (`scratch:nt_docs/strategies.md:34`).
    Which version these doc snapshots come from is UNVERIFIED.
  - The two sandbox ports are `Strategy` subclasses (spec:390, 399). The venv on the owner's machine will hold
    `TradingNode` and every live client.
  - I measured the import: `from nautilus_trader.backtest.engine import BacktestEngine` loads 7
    `nautilus_trader.live.*` modules and 35 `nautilus_pyo3` submodules. Among them are `binance`,
    `interactive_brokers`, `polymarket`, `sandbox`, `live` and `network` (`scratch:referee_governance/mods.py`). This
    confirms O13's numbers.
  - So QUANTGEN would hold a strategy that goes live with one `TradingNode` configuration. Only the static scan
    (rules C1 and D) and procedure stop that.
  - The legality report rates two of the bundled venues illegal for a Korean resident: Polymarket and foreign
    sportsbooks such as Betfair (`reports/Korean resident trading venue legality.md:15, 21`).
  - §1 says live trading "belongs to TRADEGEN". It drops map 04's boundary rules (map04:428-433):
    - only verdict artifacts cross to TRADEGEN, read-only;
    - QUANTGEN imports nothing from TRADEGEN;
    - TRADEGEN's Nautilus code is not copied into the sandbox.
  - §1 also does not cite council §3.10 point 3: "No backtest alone could enable it" (council:1261).
- **Evidence:** council:464, 500, 1257-1263, 6162; `scratch:nt_docs/live.md:3`; `scratch:nt_docs/strategies.md:34`;
  probe output; `nt:system/kernel.py:75-77`; map04:428-433; split-spec:131-135.
- **Proposed fix:**
  - Restate O3 so it covers both halves of item 21 and rule 01's "nothing to switch on".
  - Give the owner the live-portability fact and the venv's contents, the illegal-venue adapters included.
  - Add four boundary rules to §1:
    - (a) The sandbox strategies and the venv belong to QUANTGEN alone. No QUANTGEN file, test or document runs them
      or tells anyone to run them under `TradingNode`.
    - (b) TRADEGEN never uses QUANTGEN's venv, because it has its own (split-spec:131-135). TRADEGEN does not take
      `sandbox.py` as live code.
    - (c) Only cards and run records cross, read-only. An NB card is a backtest. Under council §3.10 point 3 it cannot
      enable a live path on its own.
    - (d) Call Nautilus live trading "outside QUANTGEN's scope", not "TRADEGEN's domain". TRADEGEN's use is its own
      session's decision, under Korean law.

### GOVERNANCE-3: nothing ties `--mode of-record` to the owner's machine and production ledger

- **Severity:** major.
- **Section:** §5.3.1 modes table (spec:456-459); §5.3.2 steps 1, 2 and 8 (spec:471-494); §7 R-11; O10 (spec:97).
- **Problem:**
  - Of-record mode writes rows into `config.macro_dir() / "ledgers"`.
  - After Step 7A the tables carry `owner_confirmed` and are committed (spec:466-467, 1170-1171). Any clone of that
    commit then passes every refusal from R-01 to R-11:
    - the tree is clean and the anchor equals HEAD;
    - the SPY and DGS3MO md5 values match the shared cache;
    - the cost and the GATE checks pass.
  - The ledger checks pass too. A missing ledger file reads as an empty, valid chain with `n_raw` 0
    (`core/quant/gate_ledger.py:275-277, 284-310, 333-334, 375-376`).
  - So an of-record run in the Linux container, or by a later Claude session, would:
    - register the pilot rows in a fresh ledger;
    - run on the unseen pilot window;
    - deflate the DSR by the wrong N;
    - fork the trial record, which is the risk O10 names.
  - It would also break the house rule that Claude writes ledger rows only in temp directories. Today only procedure
    prevents this. The `owner_confirmed` field is a committed string, not a per-run owner act.
- **Evidence:** spec:97, 456-459, 466-467, 471-494, 1170-1171; `core/quant/gate_ledger.py:275-277, 284-310, 333-334,
  375-376`.
- **Proposed fix:**
  - Add a table field `ledger_before` = {`hash`, `n_raw`}. The owner fills it at Step 7A.6 from his own E1 and C3
    files.
  - New refusal R-13: in of-record mode, refuse when the family ledger file is missing. Refuse when its `hash()` or
    `n_raw` differs from `ledger_before`.
  - Tie of-record mode to O10: refuse when `sys.platform != "win32"` unless the owner rules otherwise.
  - Add layer-1 tests: a missing ledger and a hash mismatch each refuse before registration.
  - This also closes O10's fork risk.

### GOVERNANCE-4: the rehearsal guard on the unseen pilot windows is weak for BTC and has no rule for the SPY end date

- **Severity:** major.
- **Section:** §3.9 (spec:181-185); §5.3.1 rehearsal row (spec:458); §5.3.2 step 4 (spec:481-484); R-10 (spec:937);
  layer-1 test 9 (spec:1043-1044).
- **Problem:**
  - §3.9 says the runner enforces the unseen-window rule. As specified, the enforcement is thin.
  - BTC is refused by file name: "the real `yf_BTC-USD.csv` is refused". Test 9 uses synthetic files "with those
    names". A renamed copy of the real file passes.
  - For SPY, step 4 defines only a start filter. No table field gives an end date. Yet a rehearsal needs every panel
    date before 2004-12-01.
  - So an engineer must invent the end filter and decide where R-10 is checked. A check placed after any computation
    would itself be a look at the pilot window.
- **Evidence:** spec:183-185, 458, 481-484, 937, 1043-1044, 1238 (the BTC md5 `bc76f530ff24ab445367fe826150bc10` is
  already in the spec).
- **Proposed fix:**
  - Add an `end` field to the table schema.
  - R-10 checks the declared `start` and `end` before it parses any price value. It checks again on the built panel.
  - In rehearsal mode, refuse any file whose md5 equals the pinned BTC md5, whatever its name.
  - In rehearsal mode, refuse any file under `docs/asset_expansion/cache/` other than `yf_SPY.csv` and
    `fred_DGS3MO.csv`.
  - Add a layer-1 test: a synthetic file is renamed and its md5 is patched in as the pinned value; the runner refuses
    it.

### GOVERNANCE-5: a gate run on real pre-window SPY is ruled "not a trial" on the owner's behalf, and O6 still offers a 1995 start

- **Severity:** major.
- **Section:** Step 7 done-when (spec:1157-1160); §10.4 (spec:1286, 1290, 1292-1295); O6 (spec:93).
- **Problem:**
  - Step 7 requires a rehearsal gate run of all 12 pilot-1 configurations on SPY from 1995-01-03 to 2004-11-30. The
    ledger is a temp one. The step says the verdict "goes into the data-access history only".
  - Map 03 already computed Sharpe levels and walk-forward picks for the same 12 configurations on that window
    (spec:1286).
  - The house practice is that "a run that computes is a trial; registered before it is scored"
    (`ui/strategy_lab_page.py:117`). The spec decides the opposite for real-data rehearsals, with no owner ruling.
  - O6 still lists "start" as the owner's choice. Synth offered "start 2004-12-01 or 1995-01-03" (synth:360-361). The
    spec never tells the owner that the 1995-2004 segment has already been scored.
  - If the owner chose a 1995 start, the "pre-specified on historical data" label (spec:1293-1295) would be false for
    that segment.
- **Evidence:** spec:93, 1157-1160, 1286, 1290, 1293-1295; synth:360-361; `ui/strategy_lab_page.py:117`.
- **Proposed fix:**
  - (a) O6 fixes the start at 2004-12-01 and says why: 1995-2004 has been computed on, so a 1995 start would make
    pilot 1 exploratory.
  - (b) The real-data rehearsal in Step 7 stops after the parity checks P1 to P13. `walk_forward` may run for P11 and
    P12. `score_strategy` runs only on synthetic data; layer-2 test 7 already covers the gate end to end.
  - (c) Add the reading "a real-data rehearsal before registration is not a trial" as a numbered owner ruling, with
    what it costs if wrong.

### GOVERNANCE-6: the card's verdict comes from the Nautilus matrix, with no check against QUANTGEN's own verdict

- **Severity:** major.
- **Section:** §5.4.2 "An exempt flip" (spec:581-584); §5.5 step 1 (spec:628); §10.3 pilot 2 (spec:1270-1276).
- **Problem:**
  - The card's decision comes from `wf_nt` (spec:628).
  - QUANTGEN's own walk-forward, `wf_qg`, is scored only when P11 has an exempt flip (spec:581-584).
  - When both engines pick the same columns, nothing checks that they reach the same decision.
  - The spec expects one such case. Pilot 2's benchmark p is 0.07 against the 0.10 bar, and "Engine noise could move
    it across" (spec:1272-1273).
  - So the bridge could write a PASS card that QUANTGEN's own engine would score REVISE, or the reverse, and say
    nothing.
  - Which engine's verdict counts when the two disagree is the owner's decision. No ruling in §2 covers it.
- **Evidence:** spec:63-64, 581-584, 628, 1270-1276; `core/quant/validate.py:492-533`.
- **Proposed fix:**
  - Always score both walk-forwards with identical inputs. That costs one more `score_strategy` call.
  - If the decisions differ, the status is WITHHELD with the reason "engine verdict mismatch". Both decisions go into
    the run record.
  - Or put this to the owner as a new numbered ruling. Add a layer-1 test with hand matrices.

### GOVERNANCE-7: O1's own default, an unchanged global interpreter, has no lasting guard

- **Severity:** major.
- **Section:** O1 (spec:88); §3.1 (spec:104-112); §5.1 (spec:280-292); §5.3.2 step 3 (spec:478-480); Step 3 and
  Step 7A done-when (spec:1126-1131, 1172-1177).
- **Problem:**
  - O1's default says the global interpreter stays unchanged and the `pyarrow` ban binds it.
  - That is checked once, on Linux, at Step 3. Step 7A checks only frozen_guard clauses (a), (b) and (d). Clause (d)
    checks numpy, scipy and pandas only (`tests/frozen_guard.py:39, 85-91`).
  - `requirements-nautilus.txt` pins numpy 2.3.5 and pandas 2.3.3, the frozen versions. So suppose someone runs
    `pip install --require-hashes -r requirements-nautilus.txt` into the global interpreter by mistake:
    - clause (d) still passes;
    - `nautilus_trader` and `pyarrow` end up in the interpreter of record;
    - no test fails.
  - If `QUANTGEN_NAUTILUS_PYTHON` then points at that interpreter, `--check-env` still matches its pins.
  - `--check-env` compares three versions and the wheel identity. It does not compare the set of installed
    distributions. So adapter extras such as `[ib]` or `[polymarket]` would also pass, though the wheel METADATA lists
    them.
  - Measured on Linux today: the global interpreter has no `nautilus_trader`, `pyarrow`, `msgspec` or `fsspec`. The
    Windows global interpreter is UNVERIFIED. It may already hold `pyarrow` through `gs-quant` (`requirements.txt:11`).
- **Evidence:** spec:88, 104-112, 280-292, 478-480, 1126-1131, 1172-1177; `tests/frozen_guard.py:39, 85-91`;
  `requirements.txt:11`; METADATA `Requires-Dist` extras (`scratch:ntvenv/.../nautilus_trader-1.231.0.dist-info/METADATA`).
- **Proposed fix:**
  - Add a layer-1 test that always runs: `importlib.util.find_spec("nautilus_trader") is None` in the test
    interpreter.
  - `--check-env` reports `sys.prefix` and `sys.base_prefix`. The runner refuses if they are equal (not a venv), or if
    the child's `sys.prefix` equals the parent's.
  - `--check-env` lists every installed distribution with its version. The runner refuses unless that set equals
    `requirements-nautilus.txt` for the platform.
  - Record at Step 7A whether the Windows global interpreter has `pyarrow`. Do not assert it either way.

### GOVERNANCE-8: three owner questions from the maps were dropped from §2

- **Severity:** minor.
- **Section:** §2 (spec:86-100); §5.7 (spec:755-756); §10.2 (spec:1235-1249).
- **Problem:**
  - **The pilot-2 table has no ruling.** O6 covers pilot 1 only. Pilot 2 writes permanent rows into C3, which also
    holds paper_live's trend rows (`paper_live/engine.py:64-69`). Only `owner_confirmed` at Step 7A covers it.
  - **FAIL or NotRun on a venv mismatch.** Map 04 asked the owner this (map04:565), and synth listed it (synth:368).
    The spec decides FAIL with no ruling.
  - **Data provenance and licence.** Map 04 asked which source and licence the pilot data use (map04:506-510, 568).
    Both pilots use Yahoo caches (`docs/asset_expansion_study.py:13`). No licence is recorded in
    `docs/asset_expansion/`: a grep for "licen" finds none. The spec pins md5 values but records no licence.
- **Evidence:** spec:93, 755-756, 1235-1249; map04:506-510, 565, 568; synth:368; `paper_live/engine.py:64-69`.
- **Proposed fix:**
  - Add three rulings:
    - O6b for the pilot-2 table;
    - O14 for FAIL or NotRun, with FAIL as the default;
    - O15 for data provenance: Yahoo via `yfinance` and FRED, licence UNVERIFIED, personal research use only, and any
      publication needs its own owner ruling.
  - Add a `licence` field to both tables.

### GOVERNANCE-9: the "never concurrent" rule leaves out the frozen-study readouts, which write the same C3 ledger

- **Severity:** minor.
- **Section:** §3.8 (spec:173-179); Step 9.
- **Problem:**
  - §3.8 bans only a pilot running at the same time as the suite.
  - The H2 readout runs `paper_live.replay` from the tag clone (split-spec:95-97). That registers rows into C3 in the
    shared home ledger (`paper_live/replay.py:172`; `paper_live/engine.py:96-112`).
  - The readout is due between about 2026-11-03 and 2026-12-19 (split-spec:64-66). That is close to when pilot 2
    could run.
  - The rows are compatible, because `core/quant/gate_ledger.py` is unchanged since `eacd57d` (`git log` shows one
    commit). A concurrent pilot 2 would fail `assert_hash_at_run` and be WITHHELD, which is fail-closed. But the
    frozen study's run would then share a lock and a hash chain with a bridge run in the same minutes.
- **Evidence:** spec:173-179; split-spec:64-66, 95-97; `paper_live/replay.py:172`; `paper_live/engine.py:96-112`.
- **Proposed fix:** Extend §3.8: no pilot runs while a frozen-study readout runs. Recommend that pilot 2 run after the
  H2 readout is committed, unless the owner rules otherwise.

### GOVERNANCE-10: the T-RO-01 precedent is overstated, and the meaning of a T-RO-01 PASS changes without notice

- **Severity:** minor.
- **Section:** §5.6 rationale (spec:649-654); §5.8 and Step 10.
- **Problem:**
  - The spec says it amends T-RO-01 "as the 2026-10-23 spec did".
  - That spec widened the scan to `tools/` and `papers/` and let `papers/` import the simulated book
    (split-spec:177-181; `tests/macro_m0_harness.py:59-60`). It did so with the owner's approval recorded in its
    Status (split-spec:12-16).
  - It added no exemption for a forbidden text token or a forbidden call. This would be the first one (map04:234-235).
  - The council's pass condition is that the scan "finds no order ... call" (council:5605). After the amendment, a
    T-RO-01 PASS in `qa/acceptance_results.json` no longer means that.
  - The README says the static scans "hold the line" (`README.md:374`).
- **Evidence:** spec:649-654; split-spec:12-16, 177-181; `tests/macro_m0_harness.py:56-60`; council:5605; map04:234-235;
  `README.md:374`.
- **Proposed fix:**
  - Say how this amendment differs from 2026-10-23: it is the first exemption for a forbidden call, and it needs O2.
  - At Step 10, add one sentence to README P0 and to the test's docstring: "T-RO-01 exempts exactly one file,
    `tools/nautilus/sandbox.py`, for simulated orders against a Nautilus backtest venue (spec 2026-10-26 §5.6)."

### GOVERNANCE-11: the Step 7A git hand-off leaves a merge decision implicit

- **Severity:** minor.
- **Section:** Step 7A items 2 and 7 (spec:1163-1171); Owner context (spec:47).
- **Problem:**
  - Item 2 says the owner "pulls the branch into the main clone". The owner's main clone is on master (`ac86705` "QA:
    full run on merged master"). There, `git pull origin claude/amazing-gauss-tdiguu` merges the branch into master.
  - The Owner context lists a merge as not authorised, and the spec never says the merge is the owner's own decision.
  - Item 7 says the owner "commits the code". But the code arrives as commits Claude already pushed.
  - The spec does not say which commit the pilot rows anchor to: the branch tip or a merge commit.
  - The split rules also forbid a whole-tree `checkout`, `reset`, `stash` or `clean` in the main repo (split-spec:89-91).
- **Evidence:** spec:47, 1163-1171, 1177; split-spec:89-91; `git log` at `ac86705`.
- **Proposed fix:**
  - Spell out the owner's commands. For example, `git fetch origin`, then either `git switch claude/amazing-gauss-tdiguu`
    or a merge into master. Say that the choice is the owner's and is recorded in Appendix B.
  - Say what the owner commits at 7A.7: the Windows goldens, the tables with `owner_confirmed`, and the results file.
  - Say that the pilots anchor to that commit.

### GOVERNANCE-12: the referee-process text does not match practice, and external referees could not check the citations

- **Severity:** minor.
- **Section:** Step 1 done-when (spec:1108-1111); Appendix B (spec:1383-1394).
- **Problem:**
  - Step 1 names the folder `docs/superpowers/specs/2026-10-26-review/`. The folder in use is
    `docs/superpowers/specs/2026-10-26-nautilus-review/`.
  - Appendix B says the Claude referee runs in a disposable, secret-free bundle. This round ran with the repo clone as
    its working directory. This clone has no `.env`; I checked.
  - A bundle holding "this file and the five inputs" cannot check the spec's `file:line` claims, so GPT and Gemini
    would have to trust them.
  - Round 1 has several Claude personas. Under D6 they count as one referee (split-spec:46). They cannot stand in for
    GPT or Gemini.
- **Evidence:** spec:1109, 1383-1384, 1391; split-spec:46, 505-512; `ls` of the review folder.
- **Proposed fix:**
  - Correct the folder path.
  - Describe the real Claude channel.
  - Give external referees a secret-free snapshot: `git archive 6f7c610` without `.env`, plus the `nt:` files the spec
    cites.
  - Record that the Claude personas are one D6 referee.

### GOVERNANCE-13: Step 2's Global Constraints copy only part of §3

- **Severity:** minor.
- **Section:** Step 2 (spec:1113-1121).
- **Problem:** The list leaves out four house rules:
  - never run paper_live's or grokteam's replay, grid, verdict, sameday or calibrate modules, or `grokteam.book` (§3.11);
  - Claude writes ledger rows only in temp directories and never runs of-record mode;
  - no Claude commit includes `qa/acceptance_results.json`
    (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:27`);
  - no real BTC price is read.
- **Evidence:** spec:196-197, 1114-1118; `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:27`.
- **Proposed fix:** Write "Global Constraints = all of §3, verbatim, plus the following". Then add the three Claude-only
  rules above.

## Notes

**Checked and correct:**
- `00_coordinator_rulings.md:54-55` bans `pyarrow` by name and says "Parquet is never read". The spec keeps Parquet,
  the catalog and streaming out of scope (spec:1332-1333).
- Item 21 is at council:6162. Rule 01's "nothing to switch on" is at council:464, 500 and 1257.
- The README regulatory note is at `README.md:924-929`, and the file is CRLF.
- `nautilus_trader` 1.231.0 METADATA reads `License: LGPL-3.0-or-later`.
  - No Nautilus code is committed. The golden module lists hold names only. The wheels stay outside the repo.
  - So LGPL duties stay dormant while QUANTGEN is not conveyed, as Risk 22 says.
  - Whether the GitHub remote `xkg4real/quantgen` is private is UNVERIFIED.
- The frozen-study guard is respected:
  - no bridge file touches `paper_live/`, `grokteam/` or a file pinned by `grokteam/prereg.py:31-36`;
  - clause (d) reads the test interpreter only (`tests/frozen_guard.py:85-91`);
  - `core/quant/gate_ledger.py` is unchanged since `eacd57d`, so bridge rows stay readable by the tag clone;
  - `paper_live/verdict.py` reads no ledger;
  - GROKTEAM uses its own family, `GROKTEAM-BOOK` (`grokteam/book.py:64`).
- The append-only rule is respected:
  - every row is registered before any child starts (spec:495-499);
  - no bridge code edits `gate_ledger.py`;
  - rehearsal ledgers must resolve under `tempfile.gettempdir()` (spec:458);
  - `ui.strategy_lab_page.register_trials` takes `ledger_dir`, so layer-1 test 10 can use a temp ledger
    (`ui/strategy_lab_page.py:55-56`).
- T-RO-01: I ran the repo's own `_offences` on the real tree with the 7 proposed verbs added to `FORBIDDEN_CALLS`.
  - 154 files are scanned; 0 hits, YAML included.
  - 0 identifier hits for `NAUTILUS_DENIED_NAMES`.
  - No scanned file mentions "nautilus" (`scratch:referee_governance/scan_probe.py`).
- The kernel's BACKTEST refusals are at `nt:system/kernel.py:373-377, 404-408, 437-441`, as cited.
- The order verbs sit at the cited `nt:trading/strategy.pyx` lines.
- `git diff --stat f5742ab 6f7c610` lists only the four research notes, as the header says.

**Small citation slip:** `core/quant/gate_package.py:36-38` should be `:35-37`, where `HARNESS_SOURCES` is defined.

**For the security referee:** the sandbox may import `os` and `pathlib`. So "writes only into `<tempdir>`"
(spec:243) is not enforced. Only rule F's partial list of `os` calls limits it: `spawnlp`, `execl`, `posix_spawn` and
others are missing.

**ModelCard has no `read_only` field** (`core/quant/validate.py:802-834`). The existing asset-expansion cards lack it
too, and the T-RO-01 artifact test checks only the macro stores (`tests/macro_m0_harness.py:196-223`). So this is not
a new breach.

**UNVERIFIED in this review:**
- the owner's two quoted sentences;
- the Windows global interpreter's packages;
- the version of the Nautilus doc snapshot in `scratch:nt_docs/`;
- the licence of the Yahoo caches;
- the visibility of the GitHub remote.

**House rules kept during this review:**
- no tracked file changed;
- no `pip install`;
- no `tests/run_all.py`;
- no paper_live or grokteam module run;
- no SPY data on or after 2004-12-01 and no BTC price read;
- no ledger row written;
- no commit.
