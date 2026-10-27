# 00. Synthesis: a research-only NautilusTrader bridge for QUANTGEN

This file replaces the earlier QuantConnect "results bridge" plan. The owner has replaced QuantConnect with
NautilusTrader. It is the architect's step plan, built from the four maps in this folder:

- `01_nautilus_backtest_api.md` (map 01): the engine side, measured on synthetic data.
- `02_quantgen_gate_ledger_lab.md` (map 02): the gate, trial ledger and Strategy Lab inputs.
- `03_pilot_and_parity.md` (map 03): the pilot port and parity, measured on pre-pilot SPY data.
- `04_governance_constraints.md` (map 04): every house rule the bridge touches, and every conflict.

Method. I read all four maps in full. I re-read the repo lines behind their key claims at commit
`f5742ab414696c8cfa8ce07d3dbcd8cf44af8b30` (list in section 9.2). I re-ran one measured claim that had no saved
output (section 7.3). That check used only SPY data from before the pilot window, and it imported QUANTGEN
read-only. I wrote no ledger row. I changed no tracked file. This file is the only file I wrote in the repo.

Citation keys. `file:line` is a QUANTGEN path at `f5742ab`. `nt:<path>:<line>` is the installed
`nautilus_trader` 1.231.0 wheel source, the same as
`https://github.com/nautechsystems/nautilus_trader/blob/v1.231.0/nautilus_trader/<path>`. `map0N §n` is a section of a
sibling map. Scratchpad paths are under
`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`, written `scratch:`.
UNVERIFIED marks anything nobody in this session could check.

---

## 1. Status

**Phase.** The "understand" phase is complete. Nothing is built. No owner ruling has been made yet.

**Feasibility.** The bridge is feasible as engineering. It is blocked by governance.

- The engine runs, is deterministic and is fast. Twelve runs of 5,600 daily bars take about 11 s (map01 §0
  finding 1).
- A MARKET order sent from `on_bar` fills at the close of the same bar (`nt:backtest/engine.pyx:1716, 1724,
  1727`). That is QUANTGEN's own timing: decide at close t, hold from t to t+1, pay the cost in the same row
  (`core/quant/strategies.py:3-5, 82-90`).
- Parity on real SPY data passes by about three orders of magnitude. This was measured on 1995-01-03 to
  2004-11-30 only, before the pilot window. All 12 settings at 1x and 2x cost: minimum correlation 0.99999901,
  maximum Sharpe difference 0.0013, 100% decision agreement (map03 §4.3).
- The blockers are rules, not code: the order-path scan T-RO-01, the "no new dependency" rule, the
  "no broker adapter inside this programme" rule, and the frozen-study library pins (map04 §9).

**What changed against the QuantConnect plan.** There is no cloud, no account, no API key, no subscription, no
upload and no vendor data terms. Six new risks replace them: a heavy new dependency (about 940 MB, with
`pyarrow`), the order-path rule, hermeticity of a child process, determinism, a Windows install nobody has
measured, and API churn (1.231.0 is the last 1.x release). Parity was a risk before and stays one.

**What the bridge can and cannot tell the owner.** In parity mode the bridge re-computes QUANTGEN's arithmetic
in an independent engine. It catches bugs in QUANTGEN's vectorized simulator and in the port. It adds little
realism by itself: whole shares, a cash constraint and cent rounding moved Sharpe by less than 0.0003 (map03
§4.2). The one material realism effect measured so far is timing. Filling one session later cost about 0.098
Sharpe on the pre-pilot window (map03 §4.2, run C3). So the plan keeps two legs apart. The parity leg feeds the
gate. A separately registered realism leg is reported as a delta and never decides a verdict.

**Discrepancies between the maps, and how this synthesis resolves them.**

| # | Discrepancy | Resolution |
|---|---|---|
| D1 | Map 01 names `core/quant/backtest.py` and `costed_path` as the local reference, and asks which initial-entry convention to use (map01 §5.1, §13 Q6). | The gate consumes `strategies.pnl_matrix`, which calls `simulate` (`docs/asset_expansion_study.py:183`; `core/quant/strategies.py:379-389`). `simulate` costs the initial entry (`core/quant/strategies.py:88-89`), as Nautilus does. `backtest.py` is the Signals page (`core/quant/backtest.py:107-119`). `costed_path` is the v2 macro path (`core/quant/costed.py:4-8, 130-160`). Neither is the reference. The question is closed. |
| D2 | Map 01 puts the sandbox at `core/bridge/` (map01 §9.3). Map 04 puts it at `tools/nautilus/sandbox.py` (map04 §3.3). | `tools/`. It stays inside T-RO-01's scan (`tests/macro_m0_harness.py:63`). It is outside the raw-text test_08/09 (`tests/acceptance.py:50-75`). It is not packaged (`pyproject.toml:22-24`). Under `core/`, test_08 would also fail. |
| D3 | Map 03 §3.5 reports how loose the owner's parity bars are, but saved no output for it. | I re-ran it (section 7.3). It reproduces: 27.5% and 16.5%, against map 03's 28% and 17%. |
| D4 | Map 01 measured with $100,000. Map 03 measured with $1,000,000. | $1,000,000. Whole-share error is at most P/E of equity: 0.08% at $1M for SPY up to about $770 (map03 §2.7). |
| D5 | The brief says the wheel is in `scratch:nt_dl/`. | `scratch:nt_dl/` holds the manylinux wheel. The win_amd64 wheel is in `scratch:nt_win/`. Both SHA-256 values match map 04 and PyPI (section 9.3). |

**Not done, on purpose.** No run touched SPY data on or after 2004-12-01. No run touched real BTC prices. A pilot
run before ledger registration would itself be an unregistered trial (map02 §0 finding 4; map04 R23).

---

## 2. Steps

### 2.1 From the QuantConnect steps to the Nautilus steps

| QuantConnect step | Nautilus step | What changed |
|---|---|---|
| Spec (design, debate, owner approval) | 1. Spec | Same process. The rulings are now about the dependency, T-RO-01 and DO-NOT-BUILD 21, not about cloud terms. |
| Plan (test-first, dry run on a scratch copy) | 2. Plan | Same. The dry run must use synthetic or pre-window data only. |
| Client (allow-listed API client) | 3. Environment | No API. A hash-pinned venv outside the repo replaces the client. |
| LEAN template (refuses live mode) | 4. Guard and 5. Sandbox | No live mode to refuse inside a backtest. The guard is a static scan amendment plus a runtime check. The sandbox is the one file that may place simulated orders. |
| Bridge (ledger first, run, pull equity) | 6. Runner | Same ledger-first rule. Returns are rebuilt from fills, never pulled from an equity report. |
| Gate (costs, parity, verdict) | 7. Parity and gate | Costs are applied inside the engine by a fee model. Parity bars are corrected (section 7). |
| (pilots inside "Bridge") | 8. Pilot 1, 9. Pilot 2 | Explicit steps. Pilot 2 runs only if pilot 1 passes parity. |
| (none) | 10. Close-out | The suite of record and frozen-guard evidence exist only on the owner's Windows machine. |

### 2.2 The steps

Each step names who does it. "Claude" means a session like this one. "Owner" means Geon Koh.

**Step 1. Spec: design, referee debate, owner approval.** Claude drafts; referees review; owner approves.

- What. Write `docs/superpowers/specs/2026-10-<dd>-nautilus-bridge-design.md` from this synthesis. It states the
  scope: backtest only, research only, no live or adapter code. It states the parent/child architecture, the
  T-RO-01 amendment text with its rationale, the dependency shape, the corrected parity bars with their evidence,
  the pilot registration table, the fail-closed rules and the owner rulings of section 3.1, each with what it
  costs if wrong. It records the pre-2004 probe of map 03 as data-access history (map04 R23).
- Debate. Claude referee here. GPT via the Codex CLI after its quota resets on 2026-10-30 14:40
  (`docs/superpowers/plans/2026-10-23-execution-record.md:158`, per map04 §7). Gemini via `agy` on the owner's
  machine (`tools/debate.py:46-47`, per map04 §7). A missing referee is REVIEW_INCOMPLETE unless the owner records a
  substitute (map04 R24).
- Done when: the spec file exists with a revision status; every issue from every referee has a ruling in an
  appendix; each referee report is saved in a review folder, or the owner's substitution is written in the spec;
  the owner's approval line and rulings O1 to O8 (section 3.1) are written in the spec.

**Step 2. Plan: test-first task plan, dry run on a scratch copy.** Claude.

- What. Write `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge.md` in the house format: Global Constraints,
  a file table, RED/GREEN steps for Steps 3 to 7 (map04 §7 step 4). Global Constraints must include: no global
  `pip install`; no edit to `paper_live/`, `grokteam/`, the gate-package harness sources
  (`core/quant/gate_package.py:36-38`) or `docs/asset_expansion/cards/`; no pilot-window data before
  registration; never run `python tests/run_all.py` in the Linux container (`tests/run_all.py:54`); CRLF files are
  edited only with the Edit tool (map04 R19).
- Dry run. Execute the plan in a scratch copy of the repo, with synthetic fixtures and temp ledgers only.
- Done when: the plan file exists; in the scratch copy every layer-1 and layer-2 test of the plan is GREEN and
  T-RO-01 passes; in the real repo, `git status` shows no change beyond the plan file and
  `qa/acceptance_results.json` is byte-identical.

**Step 3. Environment: a pinned venv, outside the repo.** Claude writes the files; the owner installs on
Windows.

- What. Add `requirements-nautilus.txt` (LF, `--require-hashes`). It pins `nautilus_trader==1.231.0`,
  `numpy==2.3.5`, `pandas==2.3.3` and the full transitive closure, with markers for `uvloop` (not win32) and
  `colorama` (win32) (map04 §2.4). Its header says: never install into the global interpreter. Add
  `QUANTGEN_NAUTILUS_PYTHON` to `.env.example`. Add `tools/nautilus/check_env.py`, run by the venv interpreter,
  which prints the versions and the wheel hash as JSON. `requirements.txt`, `requirements-dev.txt` and
  `pyproject.toml` stay unchanged. The venv lives outside OneDrive, for example `%LOCALAPPDATA%\quantgen\ntvenv`.
- Done when: on the owner's Windows machine, `<venv>\Scripts\python -m pip install --require-hashes -r
  requirements-nautilus.txt` succeeds; `check_env.py` reports nautilus_trader 1.231.0, numpy 2.3.5, pandas 2.3.3
  and Python 3.13.x; the global interpreter still reports numpy 2.3.5, pandas 2.3.3, scipy 1.18.0 and no
  `nautilus_trader`; frozen_guard clause (d) passes on Windows (`tests/frozen_guard.py:85-91`); the import time of
  `BacktestEngine` and the time of 12 runs of 5,600 bars are recorded (both UNVERIFIED on Windows today); the same
  file installs into a scratch venv on Linux.

**Step 4. Guard: confine order calls and Nautilus imports.** Claude, after owner ruling O2.

- What. Amend `tests/macro_m0_harness.py` as the owner rules (map04 §3.3):
  - one allow-listed file, `tools/nautilus/sandbox.py`, may contain the text `submit_order` and the call
    `self.submit_order(...)`, with receiver `self` only;
  - add `modify_order`, `cancel_orders`, `cancel_all_orders`, `close_position`, `close_all_positions`,
    `market_exit` and `submit_order_list` to `FORBIDDEN_CALLS` (`tests/macro_m0_harness.py:44-50`); they stay
    forbidden in the sandbox too;
  - compare full dotted import names, not the first component (today: `:90-96`); `nautilus_trader` may be
    imported only in the sandbox, and only from the allow-listed prefixes (map04 §3.3);
  - deny `nautilus_trader.live`, `.adapters`, `.network`, `.core.nautilus_pyo3`, `.backtest.node` and
    `nautilus_pyo3` in every scanned file, including as string constants (catches `importlib`).

  Add a new test with positive and negative controls in a temp tree. Register a `nautilus` suite in
  `tests/run_all.py` the lazy way `papers_tests` does (`tests/run_all.py:57-71`). Resync
  `tests/macro_registry.csv` (map04 §3.3).
- Runtime part (in the child, built in Step 5): after `engine.run()`, assert that no `sys.modules` key starts
  with `nautilus_trader.adapters` or `nautilus_trader.network`. Do not block `nautilus_trader.live` at import:
  the kernel imports it (`nt:system/kernel.py:75-77`).
- Launch contract (in the parent, built in Step 6): `<venv python> -I -B tools/nautilus/sandbox.py <tempdir>`,
  working directory = the temp dir, and an explicit minimal environment (`PATH`, `SYSTEMROOT`, and
  `HOME`/`USERPROFILE`/`TMP`/`TEMP` pointing into the temp dir). No `.env` key reaches the child
  (`config.py:25-29` loads `.env` into the parent).
- Done when: the new test passes; the sandbox control gives 0 hits; the negative controls give hits (live import:
  5; `importlib` string: 1; a `nautilus_trader` import outside the sandbox: 1; `submit_order` outside the
  sandbox: 2; each of the 7 added verbs: at least 1); the real tree gives 0 hits; test_08/09 are unchanged and
  pass; the registry check passes (`python -m tests.macro_acceptance`); the suite reports NotRun, not PASS, when
  `QUANTGEN_NAUTILUS_PYTHON` is unset.

**Step 5. Sandbox: the engine side and the strategy ports.** Claude.

- What. Write `tools/nautilus/sandbox.py`. It imports only the standard library, numpy, pandas and allow-listed
  Nautilus modules, and nothing from QUANTGEN. It contains:
  - `BpFeeModel(cost_bps x stress)`: commission = |qty| x price x multiplier x bp / 1e4 in the quote currency
    (map03 §2.10); it refuses `stress < 1`;
  - `FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=<fixed>)` (map01 §5.2, finding 14);
  - bars with O = H = L = C = the adjusted close, 9 price decimals, volume 1e12 at the instrument's size
    precision, `ts_event = ts_init` at the bar close; the column order is asserted, because the wrangler reads
    columns by position (`nt:persistence/wranglers.pyx:779-791`);
  - independent ports of `trend_switch` and `crypto_trend` (`core/quant/strategies.py:162-187, 330-348`): a plain
    mean for the SMA, a logged decision on every decision bar, a trade only when the decision changes, buy
    `floor(cash / (close x (1 + c)))` in Decimal, sell the whole position, no end-of-run liquidation (map03 §2.5);
  - outputs to the temp dir: `fills.csv` with the UUID columns dropped, `decisions.csv`, `onbar_equity.csv`
    (cash + qty x close, recorded before trading), and `manifest.json` (versions, wheel hash, input md5, bars fed,
    bars seen, `backtest_end`, the force-stop flag, denied and rejected counts, fills SHA-256);
  - fail closed: a forced stop (`nt:common/component.pyx:619-620`), bars seen < bars fed, any order not FILLED,
    any denial or rejection, or an adapter or network module in `sys.modules` makes the run invalid.
- Done when: in the venv, fixture F1 reproduces its golden fills, commissions and final cash 926,593.00, and F2
  reproduces 0.98812079 BTC and final cash 50,343.77 (map03 §6.2-6.3); N1 (thin volume, 2 decimals) is reported
  invalid after 4 of 12 bars (map03 §6.4); two separate processes give the same fills SHA-256; no code path uses
  `AT_THE_CLOSE`, `allow_cash_borrowing=True` or the `PortfolioAnalyzer`; layer-2 tests are NotRun when the venv
  is absent.

**Step 6. Runner: ledger first, then the engines, then the matrices.** Claude.

- What. Write `tools/nautilus/runner.py`. It runs in the global interpreter and never imports `nautilus_trader`.
  In order:
  1. Load the price file, check its md5 against the registered value, build the panel with the study's rules
     (`docs/asset_expansion_study.py:138-145`), round once to 9 decimals, and assert identical date vectors.
  2. Refuse to go on if `repo_anchor()` returns UNVERSIONED (`core/quant/gate_ledger.py:122-131`): rows are
     immutable, so an UNVERSIONED row cannot be fixed later.
  3. Register every variant with `register_trial` (`core/quant/gate_ledger.py:379-386`) before any child starts.
     A raise stops the run (`core/quant/gate_ledger.py:337-346`). Record `appended` and `row_md5` for each row.
     Snapshot the ledger hash after registration.
  4. Start one child per (variant, cost level). One process per run isolates the global force-stop flag and the
     reseeded global `random` (`nt:backtest/models/fill.pyx:75, 77`).
  5. Rebuild returns from the fills and the same closes: E-(t) = cash(t-1) + q(t-1) P(t), then
     R(t) = E-(t+1)/E-(t) - 1 + (cash(t)/E-(t)) rf(t) (map03 §2.9). Cross-check against the child's
     `onbar_equity.csv` and the account balance, within $0.01 per fill.
  6. Build `pnl`, `pnl_stress` and `turnover` (T-1 x G) in `grid_from` column order
     (`core/quant/strategies.py:392-398`). Build the QUANTGEN reference with `pnl_matrix` in the same process.
- Done when: an ordering test passes (temp ledger; a stub child that fails if its `config_id` is not already in
  the ledger); a ledger with a broken chain stops the runner before any child starts; a second run of the same
  grid appends 0 rows and records `appended=False`; the run record carries the post-registration ledger hash, the
  data md5, the wheel hash and every child manifest; on F1 the rebuilt R matches the hand values of map03 §6.2 to
  1e-7.

**Step 7. Parity and gate.** Claude.

- What. Write `tools/nautilus/parity.py` with the checks of section 7.4, per column, at 1x and 2x, and on the
  walk-forward out-of-sample series. Then, only if every hard check passes:
  - `walk_forward(pnl, dates, turnover=..., pnl_stress=..., embargo=<holding period>)` with the GATE windows
    (`core/quant/validate.py:345-381`);
  - align the benchmark to `wf.dates` (`docs/asset_expansion_study.py:186-190`);
  - `score_strategy(..., full_pnl=<the 1x Nautilus matrix>, n_trials=max(len(grid), N_raw at the snapshot),
    seed=11)` with `GATE` unmutated, `bootstrap_B` 2000 (`core/quant/validate.py:53-74, 492-533`); print both
    trial counts;
  - `assert_hash_at_run` before writing anything (`core/quant/gate_ledger.py:389-396`);
  - write a `validate.ModelCard` (`core/quant/validate.py:802-834`) to a new folder,
    `docs/nautilus_bridge/cards/`, never to `docs/asset_expansion/cards/` (`tests/macro_m7_cards.py:833`).

  A parity failure on any column, at either cost level, writes no card. It writes a run record with status
  WITHHELD and the failed checks.
- Done when: unit tests on hand arrays pass: one flipped decision fails P1 and P4; two identical columns pass P11;
  the wrong cost level in the 2x engine fails P3 (section 7.3); a parity failure writes no card and one WITHHELD
  record; the synthetic end-to-end run writes a card whose decision is in `validate.DECISIONS`
  (`core/quant/validate.py:50`); `GATE` is unchanged after the run.

**Step 8. Pilot 1: SPY trend, 12 settings, 2004-12-01 to 2026-09-25.** Owner's machine (the ledger lives there).

- What. The owner confirms the registration table (section 4, rows 20-24). The runner registers the 12 parity
  variants in family E1, and the 12 realism variants if ruling O7 says so, all before any engine starts. It runs
  24 parity runs (12 settings x 1x and 2x). Parity, then the gate. The realism leg runs after the parity leg and
  is reported only.
- Inputs. `docs/asset_expansion/cache/yf_SPY.csv`, md5 `d2164597d576e1b2fcadde063065811d` (re-checked); grid
  `rule {sma, tsmom} x lookback {126, 210, 252} x step {21, 42}` (`docs/asset_expansion_study.py:274`); 50 bp per
  side (`core/quant/validate.py:78`), 100 bp at 2x; embargo 21 (`docs/asset_expansion_study.py:278`); benchmark SPY
  buy-and-hold; cash DGS3MO as the study (`docs/asset_expansion_study.py:148-153`).
- Done when: the E1 ledger holds the 12 parity config_ids (appended, or already there and recorded), registered
  before the first child started (the run record's timestamps show it); every hard parity check passes for all
  12 columns at 1x and 2x, or a WITHHELD record names the failing check; if parity passed, a card exists with the
  gate's decision, both trial counts and the manifest hashes; the realism delta, if run, is in a separate section
  of the run record and not in the card's decision.
- Expect a non-PASS verdict. The four-sleeve card made only 82 position changes in 19 years and failed its
  benchmark (`docs/asset_expansion/results.md:9`, per map02 §5.2). A one-sleeve book cannot have more switch days.
  Fewer than 100 trades fails the sample check; fewer than 30 gives INSUFFICIENT_DATA
  (`core/quant/validate.py:583, 586`). UNVERIFIED: no SPY-only number exists, on purpose. A REJECT here is a
  finding about the rule, not a failure of the bridge. Changing the grid after seeing it is a new trial.

**Step 9. Pilot 2: BTC-USD crypto trend, only if pilot 1 passed parity.** Owner's machine.

- What. Five hysteresis values `{0, 0.222, 0.444, 0.667, 0.889}` with domain (0, 0.889)
  (`docs/asset_expansion_study.py:333, 339`); family C3; 10 bp per side and 20 bp at 2x
  (`core/quant/validate.py:78`); embargo 1 (`docs/asset_expansion_study.py:337`); benchmark BTC buy-and-hold; no
  cash rate. Spot `CurrencyPair` BTC/USD on a CASH venue with `base_currency=None` (map01 §11), 8 size decimals,
  commission in USD. `n_trials = max(11, C3 N_raw)`, because the stored card already counts 11
  (`docs/asset_expansion_study.py:339-343`). Data `docs/asset_expansion/cache/yf_BTC-USD.csv`, md5
  `bc76f530ff24ab445367fe826150bc10` (re-checked).
- Done when: the same conditions as Step 8, for 5 columns at 10 and 20 bp. With fewer than 8 columns, PBO is
  reported only and over-search uses the share of splits where the in-sample winner loses
  (`core/quant/validate.py:576`; map02 §2.5).

**Step 10. Close-out: suite of record, documents, commit.** Owner runs; Claude writes the record.

- What. Run the full suite on the owner's Windows machine. Update the README test table and suite help
  (`README.md:851-856, 864-878`, per map04 §7). Write the execution record: every ruling made, each with what it
  costs if wrong (map04 §7 step 7).
- Done when: the Windows full run shows 0 FAIL with the `nautilus` suite counted; `qa/acceptance_results.json` is
  committed from that run only; frozen_guard (a), (b) and (d) pass there; the execution record is committed;
  `git diff` shows no change under `paper_live/`, `grokteam/`, `docs/asset_expansion/cards/` or the harness sources
  of `core/quant/gate_package.py:36-38`.

---

## 3. Prerequisites (owner vs Claude)

### 3.1 Owner

| # | Item | Why | Blocks |
|---|---|---|---|
| O1 | Dependency ruling: allow `nautilus_trader==1.231.0` in a separate hash-pinned venv, run only as a subprocess. Say whether it covers `pyarrow`. | "No new dependency without the owner" is written in five places; one bans `pyarrow` by name (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`). Nautilus requires `pyarrow>=25` (map04 §2.2). | Step 3 |
| O2 | T-RO-01 amendment ruling: the single allow-listed `tools/nautilus/sandbox.py`, full dotted-name deny-list, confinement of `nautilus_trader` imports, string-constant check, 7 added verbs. | The sandbox must call `self.submit_order` (`tests/macro_m0_harness.py:29, 45`). Today the scan also misses live and adapter imports (`:92, 95`). Moving the file out of the scan would be evasion. | Steps 4-5 |
| O3 | Reading of DO-NOT-BUILD item 21: an unimported library in a separate venv, behind O2's deny-list, is not "a broker execution adapter, inside this programme". | `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:6162` (re-checked). The wheel ships 15 adapter packages (map01 §9.1). | Step 1 |
| O4 | Version: 1.231.0 (recommended) or a 2.0 release candidate. | 1.231.0 is the last 1.x release; v2 changes import paths (map01 §10.4). | Step 3 |
| O5 | Parity bars: accept the corrected bars of section 7.4, or keep 98% / 0.99 / 0.05. | Measured evidence shows the original bars pass real bug classes (section 7.3). | Step 7 |
| O6 | Pilot-1 registration table: start, tsmom form, cash rate, costs, embargo, benchmark, capital, account, trial-count source, engine-tag placement (section 4, rows 14-24). | Each choice changes the configurations or the verdict. It must be fixed before registration (map03 §1.5). | Step 8 |
| O7 | Realism leg: in scope, registered, reported only? Which sizing rule? | It adds 12 rows to E1 and needs a sizing rule that survives a gap without borrowing (section 6, risk 16). | Step 8 |
| O8 | Referees: wait for GPT (quota resets 2026-10-30 14:40) and Gemini, or record a substitute. | A missing referee is REVIEW_INCOMPLETE (map04 R24). | Step 1 |
| O9 | Create the venv on Windows outside OneDrive; set `QUANTGEN_NAUTILUS_PYTHON`; report the Step 3 timings. | No Windows measurement exists (map01 §10.2). | Steps 3, 8 |
| O10 | Run pilots 1 and 2 and the suite of record on Windows. | The production ledger (`~/.nextgen/macro/ledgers`) and the `studies-of-record-2026-10-23` tag exist only there (map02 §3.1; map04 §5.2). | Steps 8-10 |
| O11 | Report the current row counts of `E1.jsonl` and `C3.jsonl`. | The trial count for the DSR depends on them. UNVERIFIED today. | Steps 8-9 |
| O12 | Say how a WITHHELD result should appear in Strategy Lab, or defer it. | The scorecard knows only PASS, REVISE, REJECT and INSUFFICIENT_DATA; anything else shows as UNKNOWN (`ui/strategy_lab_page.py:303-305`). | After Step 8 |

### 3.2 Claude

| # | Item | Why | Step |
|---|---|---|---|
| C1 | Draft the spec and the debate bundle; run the Claude referee round. | House process (map04 §7). | 1 |
| C2 | Write the plan; dry-run it on a scratch copy. | House process. | 2 |
| C3 | Collect the full hash closure for `requirements-nautilus.txt`, for both cp313 win_amd64 and manylinux. | Only the two nautilus wheel hashes are measured (map04 §2.4). | 3 |
| C4 | Implement the T-RO-01 amendment and its controls, after O2. | Section 2.2, Step 4. | 4 |
| C5 | Implement the sandbox, the runner, the parity module, fixtures F1, F2, N1-N5, and the `nautilus` suite. | Steps 5-7. | 5-7 |
| C6 | Rehearse end to end on Linux with synthetic and pre-window data and temp ledgers only. | Catch errors before the owner's run without an unregistered look at the pilot window. | 2, 7 |
| C7 | Write the execution record and the data-access history (including the pre-2004 probe). | House process; map04 R23. | 10 |

---

## 4. Defaults built in

These are the defaults the spec will carry unless the owner rules otherwise.

| # | Decision | Default | Rationale |
|---|---|---|---|
| 1 | Engine version | `nautilus_trader==1.231.0`, hash-pinned; keep a local copy of both wheels | Stable now; v2 import paths fail on it, so read the installed source (map01 §10.4). A local wheel copy guards against a PyPI yank. |
| 2 | Where Nautilus runs | A separate venv outside the repo and OneDrive; a subprocess per run; never in the global interpreter | Frozen pins (`tests/frozen_guard.py:85-91`); an eager upgrade moved numpy to 2.5.4 and pandas to 3.1.0 (map04 §5.2). |
| 3 | Sandbox location | `tools/nautilus/sandbox.py`, the only file that may call `self.submit_order` | Scanned by T-RO-01, not by test_08, not packaged (D2). |
| 4 | Parent-side code | `tools/nautilus/runner.py` and `parity.py`; they never import `nautilus_trader` | Keeps `.env` and QUANTGEN out of the child (map04 §2.4). Outside `core.quant.`, so the acting-module clock rule does not apply (`core/ficc/context_log.py:71-73`). |
| 5 | Version mismatch in the venv | FAIL, not NotRun | A silent engine change would move results (map04 §2.4 item 5). A missing venv is NotRun. |
| 6 | Child launch | `-I -B`, temp working directory, explicit minimal environment, no file logging | `.env` would leak otherwise (`config.py:25-29`); file logs land in the working directory with a UUID name (map04 §4.2). |
| 7 | Parity reference | `strategies.pnl_matrix` / `simulate`, the gate path | D1. Initial entry costed on both sides (`core/quant/strategies.py:88-89`). |
| 8 | Fill timing for parity and verdict | MARKET, GTC, from `on_bar`, `latency_model=None`: same-bar close | Matches `core/quant/strategies.py:82-90`; `AT_THE_CLOSE` is rejected in backtest (`nt:backtest/engine.pyx:5333-5339`). |
| 9 | SPY instrument and account | `Equity`, whole shares, CASH, $1,000,000, buy `floor(cash/(P(1+c)))` in Decimal | Closest match measured: ΔSharpe -0.00006 (map03 §2.7). The cash check ignores the fee (`nt:risk/engine.pyx:942-955`), so the buffer prevents forced stops. |
| 10 | BTC instrument and account | Spot `CurrencyPair` BTC/USD, CASH, `base_currency=None`, 8 size decimals, USD commission, $1,000,000 | A single-currency CASH venue refuses the pair (`nt:backtest/engine.pyx:762-770`). QUANTGEN's rule is long/flat spot (`core/quant/strategies.py:332-334`). |
| 11 | Bars | O=H=L=C=adjusted close; 9 price decimals; volume 1e12; close timestamps (21:00 UTC SPY; next day 00:00 UTC BTC); column order asserted | The cache has one close column (`docs/asset_expansion_study.py:85, 88-90`). Thin volume kills runs silently (map03 §4.2, C2). |
| 12 | Trading rule | Trade only on a decision change; no drift trades; no end-of-run liquidation | QUANTGEN charges no turnover for drift (`core/quant/strategies.py:88`). A re-target-every-bar loop made 401 fills for 0 switches (map01 §11). |
| 13 | Costs | Custom `BpFeeModel`; `prob_slippage=0`; `random_seed` fixed | Exact bp-of-notional (map01 §5.1). One number carries all cost, so 2x doubles one number. |
| 14 | 2x-cost rerun | A fresh engine at `stress=2.0`; refuse `stress < 1`; never a ledger row | No `change_fee_model` exists (map01 §2.2). The 2x leg is the gate's stress column (`core/quant/strategies.py:387`; map02 §3.6). |
| 15 | Cash interest | A QUANTGEN-side overlay (cash/E-) x rf on the Nautilus series; SPY uses DGS3MO as the study; BTC none | Nautilus pays no interest; the overlay measured TE 4e-5 a year (map03 §0 finding 13). |
| 16 | Returns | Rebuilt in the parent from fills and the same closes; cross-checked with the child's pre-trade equity and the account | `PortfolioAnalyzer` returns are wrong on CASH accounts (Sharpe +1.94 against a true -1.90, map01 §0 finding 5). |
| 17 | Ledger family and row shape | E1 for SPY trend, C3 for BTC; Lab-shaped params `{rule, lookback, step, symbols, cost_bps}` (or `{hysteresis, symbols, cost_bps}`) at the 1x table rate; `timing_class` COMPLIANT; `phase` research; `run_kind` variant | Matches the Lab (`ui/strategy_lab_page.py:50, 73-81`), so replicas get the same `config_id` (`core/quant/gate_ledger.py:60-61, 168-171`). |
| 18 | Engine tag | Engine names, Nautilus version and bridge run id in `source`; per-engine results in a bridge run record keyed by `config_id` and `row_md5` | `source` is outside the key, so N does not grow per engine; a new field is refused (`core/quant/gate_ledger.py:190-192`). |
| 19 | Ledger directory | Production `~/.nextgen/macro/ledgers` for the pilot of record; temp directories in every test | The trial count must be the true one; tests must not touch home state (map04 R10, R11). |
| 20 | DSR trial count | `max(len(grid), family N_raw at the post-registration snapshot)`; both printed | The owner asked for the ledger's count; `score_strategy` says `n_trials` counts every configuration ever tried (`core/quant/validate.py:495-497`); README claims the same (`README.md:258-259`). N_eff cannot be computed for E1 (map02 §3.7). |
| 21 | Pilot-1 sample | 2004-12-01 to 2026-09-25 from the md5-pinned cache | Comparable with `S_E1_trend_us` (`docs/asset_expansion_study.py:724`). Index-based decision dates depend on the start (`core/quant/strategies.py:146-147, 176`). |
| 22 | Pilot-1 tsmom form | Raw lookback return (rf = 0 in the signal), as the study runs it | `pnl_matrix` calls `fn(prices, **theta)` without a rate (`core/quant/strategies.py:384`). |
| 23 | Gate settings | `GATE` unchanged: 756 / 126 / 504, embargo 21 (trend) or 1 (crypto), `bootstrap_B` 2000, seed 11 | `core/quant/validate.py:53-74`; the Lab's lowered B is restored after each run (`ui/strategy_lab_page.py:124-129`). |
| 24 | Benchmark | SPY buy-and-hold for pilot 1; BTC buy-and-hold for pilot 2; uncosted | `docs/asset_expansion_study.py:275` with N = 1; `:334`. |
| 25 | Parity bars | Corrected bars of section 7.4; the owner's original bars printed alongside | Section 7.3. |
| 26 | A parity failure | Withholds the verdict for the whole grid; writes a WITHHELD run record and no card | CSCV and the DSR dispersion need every column (map03 §3.3). |
| 27 | Cards | `docs/nautilus_bridge/cards/`; Lab integration deferred | `docs/asset_expansion/cards/` must stay at 34 files (`tests/macro_m7_cards.py:833`) and is read-only (`tests/macro_acceptance.py:26-27`). |
| 28 | Realism leg | Next-close (1-session latency) on close-only data, registered as 12 `timing_lag` rows with `params.fill = "next_close"` before any run, reported as a delta, never gated | Timing is the only material realism effect measured (-0.098 Sharpe, map03 §4.2). `timing_lag` is a ledger run kind (`core/quant/gate_ledger.py:58`). Next-open needs an OHLC file that does not exist. |
| 29 | UNVERSIONED anchor | The runner refuses to register | Rows are append-only and hash-chained; editing one breaks the chain (map02 §3.6); a duplicate `config_id` never replaces the first row (`core/quant/gate_ledger.py:343-346`). `repo_anchor` has no packed-refs fallback (`:122-131`). |
| 30 | Pre-2004 probe | Recorded as data-access history in the spec and run record; no extra ledger rows | Its 12 configurations have the same `config_id`s as pilot 1, because `span` is not in the key (`core/quant/gate_ledger.py:60-61`). |
| 31 | Where pilots run | The owner's Windows machine; Linux rehearses on synthetic and pre-window data only | The production ledger and the frozen-guard tag are there (O10). |

---

## 5. Open questions

### 5.1 For the owner (each has a default in section 4)

1. Dependency ruling, including `pyarrow` (O1). Default: separate venv; global files unchanged.
2. T-RO-01 amendment and placement in `tools/` (O2). Default: as Step 4.
3. DO-NOT-BUILD item 21 reading (O3).
4. Version 1.231.0 or 2.0 rc (O4). Default: 1.231.0, with a separate v2 migration task later.
5. Corrected parity bars (O5). Default: section 7.4.
6. DSR trial count: family N_raw (default), market-scoped N_raw, or `len(grid)`?
7. Engine tag in `source` (default, one trial per variant) or in `params` (two trials per variant)?
8. Pilot-1 table (O6): start 2004-12-01 or 1995-01-03; tsmom raw or excess; DGS3MO; $1M; CASH with buffer or
   MARGIN without (both pass parity, map03 §2.7).
9. Realism leg (O7): in scope and registered (default), or deferred? If in scope, which sizing rule: a gap buffer,
   or quote-quantity orders (UNVERIFIED in 1.231.0 backtests)?
10. Ledger directory and run location (O10): production on Windows (default), or export `E1.jsonl` for a cloud run
    and copy back the extended chain? The second risks a fork if both copies change.
11. WITHHELD display in Strategy Lab (O12): deferred (default), a new loader for `docs/nautilus_bridge/cards/`, or
    a decision value added to the scorecard?
12. Version mismatch in the venv: FAIL (default) or NotRun?
13. Referees (O8): wait, or record a substitute?
14. If a pilot becomes a `/quantgen-paper` study: the paper-write rule "No new pip packages"
    (`.claude/workflows/quantgen-paper-write.js:37`) and `PACKAGES` in `tools/paper/study.py:30` need the
    dependency ruling to name them (map04 C7).
15. Should a future gate-package freeze include E1 and C3 ledger hashes? Today no caller passes them
    (map02 §3.8). UNVERIFIED for any future freeze.

### 5.2 UNVERIFIED items that matter

- Windows: install, dependency resolution, import time, run time, and any network or file trace (map01 §10.2;
  map04 §4.3, §5.2).
- Row counts of the owner's `E1.jsonl` and `C3.jsonl` (map02 §3.1).
- `repo_anchor()` on the owner's clone (packed refs, OneDrive) (map02 §3.4).
- Parity margins on the pilot window itself. They were measured only before 2004-12-01, on purpose.
- The v1 security-backport end date. RELEASES.md says "approximately three months after the v2 cutover"
  (`https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/RELEASES.md`, lines 5-24). The cutover
  date itself is not stated there.
- A MARGIN account at leverage 1 beyond the one map 03 run; `lot_size > 1`; an audit-hook socket guard (map01 §13).
- Whether the `is_backtest_force_stop()` flag resets between engines in one process. The default (one process
  per run) avoids the question.
- Whether `yfinance` `auto_adjust=True` scales open/high/low by the close factor (needed only for a next-open leg,
  map03 §2.6).
- GPLv3 section 2 text (gnu.org was blocked) and FSCMA Art. 101 (law.go.kr did not resolve) (map01 §10.1;
  map04 §8).

---

## 6. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | The T-RO-01 amendment is drawn too wide and opens an order path. | One file, receiver `self` only, 7 more verbs forbidden everywhere, full dotted-name deny-list, string-constant check, negative controls in the test (Step 4). |
| 2 | A live or adapter import slips in, statically or through `importlib`. Today's scan gives 0 hits on both (map04 §3.2). | Static deny-list (Step 4) plus the post-run `sys.modules` check (Step 5). |
| 3 | Rust sockets in `nautilus_pyo3` bypass Python patches and audit hooks. | The bridge never imports adapters or network modules. Linux `strace` and `unshare -n` showed 0 socket calls (map04 §4.2). Windows has no trace: UNVERIFIED. |
| 4 | Someone installs Nautilus globally with an eager upgrade: numpy 2.3.5 to 2.5.4, pandas 2.3.3 to 3.1.0 (map04 §5.2). | Requirements header warning; venv outside the repo; version check FAILs in the child; never run the suite under the venv (it has no scipy). |
| 5 | `.env` keys reach the child process. | Explicit minimal environment (Step 4); a test dumps the child's environment. |
| 6 | A forced stop or thin volume truncates a run, and it returns normally (map01 §4; map03 §4.2 C2). | Fail-closed checks: force-stop flag, bars seen, `backtest_end`, every order FILLED, cash reconciliation (Step 5). |
| 7 | Someone uses `PortfolioAnalyzer` or the account report as equity. | Returns are rebuilt in the parent from fills; the sandbox never calls the analyzer (Step 5 done-when). |
| 8 | The owner's parity bars pass real bugs (section 7.3). | Corrected bars and the fill-date check (section 7.4). |
| 9 | A walk-forward near-tie picks different columns on each side (gap 0.0006 against engine noise up to 0.00069, map03 §4.4). | P11 tolerates a mismatch only when QUANTGEN's in-sample gap is below 0.005. |
| 10 | Convention mismatch looks like an engine error: adjusted closes, cash interest, the tsmom rate, index-based decision dates, the initial entry. | One shared rounded price array, md5-pinned; asserted date vectors; the study's conventions copied (section 4, rows 7, 15, 21, 22). |
| 11 | Yahoo restates adjusted history after each dividend. | md5 pin at registration; the runner refuses a mismatch (Step 6). |
| 12 | An unregistered look at the pilot window. | Register first (Step 6); Linux rehearsal on synthetic and pre-window data only; the data-access history records the pre-2004 probe. |
| 13 | N is inflated (tag in params) or the engine tag is lost (`source` dropped for an already-registered row). | Tag in `source`; per-engine detail in the bridge run record keyed by `config_id` and `row_md5`. |
| 14 | Pilot 1 ends REJECT, REVISE or INSUFFICIENT_DATA, and that is read as a bridge failure, or the grid is tuned after seeing it. | Say so in the spec before the run (Step 8). Any grid change is a new registration. |
| 15 | API churn: 1.231.0 is the last 1.x release; v2 changes imports and some semantics (map01 §10.4). | Exact pin with hashes; all Nautilus calls in one file; a later v2 migration is its own task, re-runs F1/F2 and the parity grid. The engine is offline, which limits the security exposure after backports end. |
| 16 | The realism leg overdraws cash: sizing at close t and filling at t+1 needed borrowing in the probe (final cash -$14,309, `scratch:parity_probe/out/cmp_base0__C3_lag1.json`). | The spec fixes a sizing rule before the run and reports the resulting exposure difference. The realism leg is never gated. |
| 17 | Multi-sleeve books cannot reach parity. `simulate` holds constant weights as a fraction of current equity, a daily rebalance with no turnover charged (`core/quant/strategies.py:83-90`). | The bridge is limited to single-instrument long/flat rules until a separate drift convention is ruled on. |
| 18 | Wall-clock run ids and UUIDs enter hashes. | Drop `event_id`/`init_id`; strip the UUID suffix of closed NETTING `position_id`s; keep run times out of hashes (map01 §6). |
| 19 | `FillModel` reseeds Python's global `random` (`nt:backtest/models/fill.pyx:75, 77`). | One child process per run; a fixed seed. |
| 20 | Referees unavailable here: no `codex`, no `agy` (map04 §7). | Wait for the quota and the owner's machine, or an owner-recorded substitute; otherwise REVIEW_INCOMPLETE. |
| 21 | A Linux `run_all.py` rewrites `qa/acceptance_results.json` with 8 environment FAILs (map04 §7). | Never run it here; per-module runs or the redirected wrapper only. |
| 22 | A pilot run writes `~/.nextgen/macro/ledgers` while the suite runs, and T-HERM-02 trips (`tests/macro_acceptance.py:25-27`). | Procedure: never concurrent (map04 R11). |
| 23 | LGPL-3.0 duties if QUANTGEN is ever conveyed; FSCMA questions if results are published. | The README forbids distribution (map04 §8). Publication needs an owner review. FSCMA is UNVERIFIED. |
| 24 | Disk and sync: about 940 MB installed (map01 §10.2). | The venv lives outside OneDrive. |

---

## 7. Measured parity

### 7.1 Evidence from the maps

| Evidence | Data | Result | Source |
|---|---|---|---|
| Synthetic SMA switch, whole shares, $100k | 600 seeded bars | agreement 1.000; corr 0.9999993; ΔSR 0.0021 (1x), 0.0056 (2x) | map01 §7 |
| Synthetic, fractional Cfd | same | corr 0.9999996; ΔSR 0.0015 | map01 §7 |
| Real SPY `sma/210/21`, $1M, 9 dp, CASH with buffer | 1995-01-03 to 2004-11-30, 2,497 sessions | agreement 109/109; corr 0.99999995; ΔSR -0.00006 (1x), +0.00013 (2x) | map03 §4.2; re-read in `scratch:parity_probe/out/cmp_base0__A_base0.json` |
| Same, DGS3MO overlay | same | ΔSR -0.00006; TE 4e-5 a year | map03 §4.2 |
| All 12 settings x 1x and 2x | same | min corr 0.99999901; max abs ΔSR 0.0013; agreement 100%; max daily gap 3.80 bp; all runs complete | map03 §4.3 |
| Walk-forward selection | same, embargo 21 | the same column at all 14 origins; OOS corr 0.99999996; ΔSR +0.00004 (1x), +0.00036 (2x) | map03 §4.4 |
| Crypto trend, 5 hysteresis values, 10 and 20 bp | 1,500 synthetic calendar days | agreement 100% on 1,300 decisions; min corr 0.99999984; max abs ΔSR 0.0003 | map03 §4.5 |
| Fixtures F1 and F2 | hand-built | fills, commissions and final cash match hand arithmetic to the cent on both engines | map03 §6 |
| Failure modes | same window | 2 dp: TE 0.085%/yr, passes; thin volume: run stopped at bar 211, fails; 1-session latency: corr 0.98295, ΔSR -0.098, fails by design | map03 §4.2 |

### 7.2 Determinism

Fills reports hash the same across runs and processes once the UUID columns are dropped (`4443e95f46b89f8d`,
map01 §6). The positions report does not, unless the UUID suffix of closed NETTING `position_id`s is stripped.

### 7.3 Are the owner's bars well specified? My re-check

Map 03 §3.5 claims the 0.99 and 0.05 bars are loose, but saved no output. I re-ran the test:
`scratch:synth_check/flip_bars.py`, global interpreter, `python3 -I -B`, QUANTGEN imported read-only, SPY
1995-01-03 to 2004-11-30 only, `sma/210/21`, 50 bp. I flipped one 21-session decision block at a time (109 blocks)
and compared each flipped P&L with the true one. A flipped block stands in for a port bug.

| Quantity | Result |
|---|---|
| Correlation of a single-flip P&L with the true P&L | min 0.9591, median 0.9933, max 0.9983 |
| abs ΔSharpe of a single flip | median 0.0283, max 0.1554 |
| Share caught by the owner's corr < 0.99 | 27.5% |
| Share caught by the owner's abs ΔSR > 0.05 | 16.5% |
| Share caught by either owner bar | 36.7%; so 63% of single-flip bugs pass both |
| Share caught by corr < 0.9999 | 100% |
| Share caught by abs ΔSR > 0.01 | 86.2% |
| A wrong cost level in the 2x engine (1x charged where 2x is due) | corr 0.9991047 and abs ΔSR 0.04958: passes both owner bars |

The last row matters. The whole difference between the 1x and 2x Sharpe on this setting is 0.0496
(0.76802 against 0.71844). A bridge that forgot to double the cost would pass the 0.05 bar.

### 7.4 Corrected parity bars (proposal for ruling O5)

Each bar is computed per column, at 1x and at 2x, and again on the walk-forward OOS series. Any failure withholds
the verdict for the whole grid. The owner's original bars are printed next to them in every report.

| ID | Check | Owner bar | Corrected bar | Why the correction |
|---|---|---|---|---|
| P1 | Decision agreement on decision dates (the logged decision, not the position) | >= 98% | **= 100%**, except where QUANTGEN's decision margin is below 1e-9 relative (logged) | In parity mode both sides compute one rule on one array. Measured disagreements: 0 in all 24 SPY runs (109 decisions for `sma/210/21`) and 0 in all 10 crypto runs (1,300 decisions each). 98% tolerates 2 wrong decisions of 109, and one wrong decision moved Sharpe by up to 0.155. The margin exemption covers a floating-point tie between a cumulative-sum SMA and a plain mean (map03 §3.4, source 7). |
| P2 | Correlation of daily net returns | >= 0.99 | **>= 0.9999** | Measured worst 0.99999901 (1 - ρ = 1e-6), so 100x margin. 0.99 passed 72.5% of single-flip bugs and the wrong-cost bug (0.9991). 0.9999 caught all 109 flips. |
| P3 | abs ΔSharpe (`validate.sharpe`, `core/quant/validate.py:137-143`) | <= 0.05 | **<= 0.01** | Measured worst 0.0013, so 7.7x margin. 0.05 passed the wrong-cost bug (0.0496) and 83.5% of single flips. |
| P4 | Fill dates equal the dates with abs Δw > 0, excluding the last bar | (none) | **equal** (hard) | Catches a flipped decision directly (map03 §3.3). |
| P11 | Walk-forward chosen column per origin | (none) | **equal**, unless QUANTGEN's in-sample gap is < 0.005 (hard) | A near-tie of 0.0006 was seen (map03 §4.4). |
| P12 | P2 and P3 on the OOS concatenation, 1x and 2x | (none) | as P2, P3 (hard) | The gate reads the OOS series (`core/quant/validate.py:498-525`). |
| P13 | Completeness: no forced stop, bars seen = bars fed, every order FILLED, cash reconciles within $0.01 per fill | (none) | **all** (hard) | A truncated run looks like a flat strategy (map03 §2.11). |
| P5-P9 | Fill price, turnover ratio, cost ratio, drawdown, tracking error | (none) | warnings at map 03's bounds (map03 §3.3) | Diagnostic. |
| P10 | Daily gap | (none) | warning at the analytic bound c(c + abs r)/(1 + c) + 1e-9 per row, not a flat 5 bp | On a 2008 entry day with r = 10% at 2x, the legitimate gap is about 10.9 bp, so a flat 5 bp bar would warn falsely. |

If the owner keeps the original bars, P1 = 100% and P4 alone still catch the flipped-decision class. Nothing in
the original bars catches the wrong-cost class. P3 at 0.01 (or the cost-ratio check P7 made hard) would.

### 7.5 Not measured

No parity number exists for the pilot windows (SPY from 2004-12-01; real BTC). That is deliberate. The legitimate
divergence comes from the entry-day buffer gap and scales with c and with abs r on entry days. Its effect on
Sharpe is a rate, so it should stay near the measured 0.0013 at 2x. UNVERIFIED until the registered pilot runs.

---

## 8. Alternatives rejected

| Alternative | Why rejected |
|---|---|
| Keep the QuantConnect bridge | The owner replaced it (user request). |
| Add Nautilus to `requirements.txt`, `requirements-dev.txt` or a `pyproject.toml` extra | Installs into the global interpreter; adds `pyarrow`; Nautilus needs Python 3.12+ while the project says 3.10+ (`pyproject.toml:9`); an eager upgrade breaks the frozen pins (map04 §2.3, §5.2). |
| Import Nautilus inside QUANTGEN's process | Reseeds global `random` (`nt:backtest/models/fill.pyx:75, 77`); drags `.env` and the frozen pins into one process. |
| Sandbox under `core/bridge/` | Also fails the raw-text test_08 (`tests/acceptance.py:62-68`) and ships in the app package (D2). |
| Sandbox outside every scanned tree | Evasion of T-RO-01 (map01 §9.2). |
| Block `nautilus_trader.live` at import time | Breaks every backtest: the kernel imports three `live` engines (`nt:system/kernel.py:75-77`). |
| `PortfolioAnalyzer` or account-report returns | Cash-only on CASH accounts; calendar-day resampling; wrong Sharpe sign in the probe (map01 §0 finding 5). |
| `AT_THE_CLOSE` or a market-on-close type | Rejected in backtest; no MOC type exists (`nt:backtest/engine.pyx:5333-5339`). |
| Next-open or next-close fills as the parity mode | A timing difference, not an engine error; fails 0.99 by design (map03 §4.2 C3). Kept as a reported realism leg. |
| `allow_cash_borrowing=True` or MARGIN without a buffer | Passes parity, but is an implicit loan that changes the economics (map01 §4; map03 §2.7). |
| `Cfd` fractional stand-in for SPY | Not needed at $1M (whole-share error at most 0.08%); misuses an instrument type (map03 §2.7). |
| Re-target the weight every bar | Many small drift trades that QUANTGEN does not charge (map01 §2.5, §11). |
| Engine tag in `params`, or a new ledger field | `params` adds a trial per engine and a run id adds one per re-run; a new field is refused and needs a harness edit (map02 §3.6). |
| Register the 2x rerun as its own row | It is the gate's stress column, not a hypothesis (map02 §3.6). |
| Write bridge cards into `docs/asset_expansion/cards/` | Breaks the 34-file test and the read-only tree; the study rewrites the folder (`tests/macro_m7_cards.py:833`; `docs/asset_expansion_study.py:775-780`). |
| Build on a 2.0 release candidate | Still moving; nobody installed or ran it here (map01 §10.4). Kept as a later migration task. |
| Replicate the four-sleeve `S_E1_trend_us` card as pilot 0 | `simulate` holds constant 1/N weights of current equity with no turnover charged, which is a free daily rebalance (`core/quant/strategies.py:83-90`). An execution engine must trade the drift. Parity would fail on convention, not on engine error. For N = 1 and w in {0, 1}, constant weight is buy-and-hold, so SPY alone is exact. |
| Nautilus `BacktestNode`, `ParquetDataCatalog` or streaming | Not needed; Parquet is "never read" under the coordinator ruling (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`); `NAUTILUS_PATH` is read only by the catalog (map04 §4.2). |
| The Nautilus `sandbox` adapter for paper trading | It is a live-node adapter on live data (`nt:adapters/sandbox/execution.py:58`); QUANTGEN has its own paper engine. |
| The QuantConnect Lean-format SPY file in the tech-fund scripts | Licence not recorded; not dividend-adjusted (map04 §8 item 2). |
| Running the suite under the venv | The venv has no scipy; frozen_guard (d) would FAIL (`tests/frozen_guard.py:90`). |
| A flat 5 bp daily-gap bar | Warns falsely on large-move entry days at 2x (section 7.4, P10). |

---

## 9. Sources

### 9.1 Maps (this folder)

- `01_nautilus_backtest_api.md`, `02_quantgen_gate_ledger_lab.md`, `03_pilot_and_parity.md`,
  `04_governance_constraints.md`. Map 02 is in commit `f5742ab`; maps 01, 03 and 04 are untracked notes.

### 9.2 Repo lines I re-checked at `f5742ab` (all matched the maps unless noted)

- `core/quant/validate.py:50, 52, 53-74, 78, 137-143, 345-381, 384-418, 492-533, 576-622, 802-812`.
- `core/quant/gate_ledger.py:55-70, 122-131, 165-215, 335-396`.
- `core/quant/strategies.py:1-23, 69-90, 146-187, 328-348, 377-398`.
- `core/quant/costed.py:1-10, 128-160`; `core/quant/backtest.py:105-120` (basis for D1).
- `core/quant/gate_package.py:30-40`; `data/macro/rules_v2.0.0.json:1555, 1566` (`NOT_FROZEN`).
- `docs/asset_expansion_study.py:85, 88-90, 138-153, 173-193, 243, 270-280, 325-343, 592-596, 720-732, 775-780`.
- `ui/strategy_lab_page.py:31, 35-52, 60-82, 110-130, 254-256, 300-306`.
- `tests/macro_m0_harness.py:25-110`; `tests/acceptance.py:30-75`; `tests/frozen_guard.py:1-15, 35-42, 80-95`.
- `tests/macro_m7_cards.py:830-838`; `tests/macro_acceptance.py:22-30`; `tests/run_all.py:41-90`;
  `tests/paper_live_acceptance.py:333-343`.
- `paper_live/engine.py:96-113` (read only; register-before-run precedent).
- `config.py:20-30`; `pyproject.toml:5-26`; `README.md:255-266`.
- `core/engine/orders.py:90, 169, 253-257`; `core/ficc/context_log.py:66-76`.
- `research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:52-56`.
- `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:6160-6163`.
- `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:175-181`.
- md5 of `docs/asset_expansion/cache/yf_SPY.csv` = `d2164597d576e1b2fcadde063065811d` and of
  `docs/asset_expansion/cache/yf_BTC-USD.csv` = `bc76f530ff24ab445367fe826150bc10`.

Noted, not a contradiction: a shorter copy of the council file at `mindmap/QUANTGEN_MACRO_INTEGRATION.md` has no
line 6162. The maps cite the `QUANTGEN_Quant_Council_2026-10-03/` copy, which does.

### 9.3 Scratchpad evidence (outside the repo)

- Wheels: `scratch:nt_dl/nautilus_trader-1.231.0-cp313-cp313-manylinux_2_35_x86_64.whl`, SHA-256
  `429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91`;
  `scratch:nt_win/nautilus_trader-1.231.0-cp313-cp313-win_amd64.whl`, SHA-256
  `5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf`. Both match map 04 §2.4.
- Map 01 probes: `scratch:nt_probe/`. Map 03 probes: `scratch:parity_probe/` and `scratch:parity_probe/out/`
  (I re-read `cmp_base0__A_base0.json`, `cmp_base0__A_stress_stress.json`, `cmp_base0__C2_thin.json` and
  `cmp_base0__C3_lag1.json`). Map 04 probes: `scratch:gov_probe/`.
- My check: `scratch:synth_check/flip_bars.py` (section 7.3).
- The v1.231.0 release note as fetched by map 01: `scratch:nt_docs/RELEASES.md`, lines 1-24.

### 9.4 External

- PyPI metadata: `https://pypi.org/pypi/nautilus_trader/json`; `https://pypi.org/pypi/nautilus_trader/2.0.0rc7/json`.
- Release notes, v2 transition: `https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/RELEASES.md`
  (lines 5-24).
- Licence: `https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/LICENSE` (LGPL-3.0, section 4
  at lines 78-125, per map 01).
- Bar execution and timestamps:
  `https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/docs/concepts/backtesting/bar-execution.md`.
- Logging defaults: `https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/docs/concepts/logging.md`.
- Accounts and margin; positions:
  `https://github.com/nautechsystems/nautilus_trader/blob/master/docs/concepts/backtesting/accounts-and-margin.md`;
  `https://github.com/nautechsystems/nautilus_trader/blob/master/docs/concepts/positions.md`.
- v2 roadmap: `https://github.com/nautechsystems/nautilus_trader/issues/4042`.
- Source at the tag: `https://github.com/nautechsystems/nautilus_trader/blob/v1.231.0/nautilus_trader/<path>`
  (map 01 compared four files byte for byte with the installed wheel).
- UNVERIFIED in this session (blocked): `https://www.gnu.org/licenses/gpl-3.0.html`; law.go.kr (FSCMA Art. 101).

---

## 10. Critic findings (completeness review, 2026-10-26)

Method. I read this synthesis and the four maps. I re-read the repo lines behind their key claims at `f5742ab`.
I read the installed `nautilus_trader` 1.231.0 source in `scratch:ntvenv/`. I read `core/rust/model.pxd` from the
win_amd64 wheel (extracted to `scratch:critic_win/`). I ran two small probes in `scratch:critic_probe/`. One ran in
the venv and imported only allow-listed modules. The other, `wf_ties.py`, ran in the global interpreter, imported
`core.quant.validate` read-only and used only map 03's saved pre-2004 outputs. I wrote no ledger row. I changed no
tracked file. I appended only this section.

What held up. Every repo `file:line` I spot-checked says what the maps claim. That covers the T-RO-01 scan,
test_08/09, frozen_guard (d), `simulate` and `pnl_matrix`, the gate constants, `walk_forward`, `score_strategy`,
the ledger key, `repo_anchor` and `register_trial`, the Lab's family map and rows, the study lines 183-184, 274-278,
333-339 and 724-731, the 34-card test, `READ_ONLY_TREES`, `config.py:25-29` and `pyproject.toml:22-24`. The cache
md5s match. Every Nautilus line I checked also matches: the same-bar fill order (`nt:backtest/engine.pyx:1716,
1724, 1727`), the AT_THE_CLOSE rejection (`:5332-5339`), the CurrencyPair check (`:762-770`), the FillModel reseed
(`nt:backtest/models/fill.pyx:75, 77`), the cash-only balance impact (`nt:accounting/accounts/cash.pyx:482-495`),
the order-method lines in `nt:trading/strategy.pyx` and the missing `change_fee_model`. 1.231.0 is still the
newest 1.x release on PyPI, and the win_amd64 SHA-256 matches
(`https://pypi.org/pypi/nautilus_trader/json`). cp313 win_amd64 wheels exist for numpy 2.3.5, pandas 2.3.3,
pyarrow 26.0.0 and msgspec 0.22.0 (`https://pypi.org/pypi/<name>/<version>/json`).

### 10.1 Blocker

**K1. The Windows wheel runs in standard precision. The plan's bar volume of 1e12 raises an error there, and no
measurement covers that mode.**

- Evidence. The PyPI description says: "On Windows, only standard-precision (64-bit) Python wheels are available
  because MSVC's C/C++ frontend does not support `__int128`" (`https://pypi.org/pypi/nautilus_trader/json`,
  `info.description`, "Precision mode"). The win_amd64 wheel's `nautilus_trader/core/rust/model.pxd:6` reads
  `DEF HIGH_PRECISION = False`. The Linux venv reads `True` (`nt:core/rust/model.pxd:6`). At runtime it reports
  `HIGH_PRECISION=True`, `FIXED_PRECISION=16` and `QUANTITY_MAX=34028236692093` (measured).
- In standard mode `QUANTITY_MAX` is 18,446,744,073 (`nt:core/rust/model.pxd:92-94`). `Quantity.__init__` raises
  `ValueError` above it (`nt:model/objects.pyx:137-140`). The wrangler builds the volume as
  `Quantity(values[4], size_precision)` (`nt:persistence/wranglers.pyx:788`). The probe builds
  `Quantity(vol, ...)` with a default of 1e12 (`scratch:parity_probe/nt_side.py:157, 211`).
- Section 4 row 11, Step 5 and map03 §2.3 and §5.2 all set the volume to 1e12. So F1, F2, N1 and every pilot run
  raise on the owner's machine. Pilots run only there (O10).
- All parity margins, goldens and timings were measured in high-precision mode. A Linux rehearsal with the
  official wheel cannot reproduce standard mode. Standard mode also caps price precision at 9
  (`nt:core/rust/model.pxd:18-20`), so the planned 9 decimals sit exactly at the limit.
- Fix.
  - Set the volume to a constant at or below `QUANTITY_MAX` at the instrument's size precision, for example 1e9.
    1e9 is still more than four times any order: about 10^4 SPY shares or 10^3 BTC at $1M.
  - In the sandbox, assert the volume against `nautilus_trader.model.objects.QUANTITY_MAX` and assert price
    precision <= `FIXED_PRECISION`.
  - Record `HIGH_PRECISION` and `FIXED_PRECISION` in `manifest.json`.
  - Add to Step 3's done-when: on Windows, F1, F2 and N1 run through the runner's exact launch contract and match
    their goldens.
  - Mark cross-precision equality of the goldens UNVERIFIED until that run.

### 10.2 Major

**K2. The pilots run before the bridge code is committed. Every pilot ledger row would then anchor a commit that
does not contain the code.**

- Evidence.
  - Steps 8-9 register and run. The only commit step is Step 10, which comes after them.
  - `repo_anchor()` reads HEAD only (`core/quant/gate_ledger.py:122-131`).
  - Rows are immutable: a duplicate `config_id` never replaces the first row (`:343-346`).
  - The house spec already refuses a dirty tree for this reason: "it also refuses a dirty working tree, because
    `repo_anchor()` reads only HEAD and would otherwise anchor uncommitted code"
    (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:470-473`).
  - `qa/acceptance_results.json` is committed with each change group (`:159-160`), only after a full run. That
    run is possible only on Windows (map04 §7).
- Fix. Insert a hand-off step between Steps 7 and 8.
  1. With the owner's approval, Claude pushes the branch.
  2. The owner pulls it on Windows and runs the full suite there.
  3. The owner commits the code and the results file.
  4. Only then does the owner run the pilots.
- The runner refuses a dirty tree (non-empty `git status --porcelain`) and writes the HEAD sha into the run record.
  A fresh commit also writes the loose branch ref that `repo_anchor()` reads (`gate_ledger.py:126-128`). That
  lowers the packed-refs UNVERSIONED risk (map02 §3.4).
- Step 10 then commits only the outputs: cards, run records and the execution record.

**K3. P11's near-tie exemption and P12, as defined, contradict each other.**

- Whenever P11 tolerates a different chosen column, P12 compares two different columns' OOS returns, and P12
  fails.
- Measured on map 03's saved pre-2004 matrices (`scratch:critic_probe/wf_ties.py`):
  - Two origins have a runner-up within P11's 0.005 gap that is a different OOS column: 1386 (gap 0.00059) and
    2394 (gap 0.00114). If Nautilus took that runner-up, P12 would give a correlation of 0.9465 and a ΔSharpe of
    +0.045. Both fail the corrected bars (>= 0.9999 and <= 0.01).
  - Map 03 measured engine noise in in-sample Sharpe of up to 0.00069 (map03 §4.4). That is larger than the 0.00059
    gap, so a flip on the pilot's 38 origins is plausible.
  - Exact QUANTGEN ties are not safe either. At origins 1512 and 1638, columns 4, 5 and 9 tie exactly in QUANTGEN.
    Nautilus column 9 differs by about 1e-6 (0.737800031 against 0.737801118) because of whole-share rounding on a
    different equity path. The sign of that noise alone decided the match.
- Fix.
  - Compute P12 on a selection-matched OOS series: apply QUANTGEN's `wf.chosen` to both matrices.
  - Keep P11 as its own check.
  - If an exempt flip occurs, score both matrices. Require the same decision, or write WITHHELD with the reason
    "selection near-tie".
  - The card states which selection it used.
  - Add a unit test with a planted near-tie.

**K4. The T-RO-01 amendment fails the bridge's own files.**

- String-constant rule.
  - The rule flags any string constant at or under a denied prefix. In the prototype, that is
    `_under(n.value.strip(), NT_DENIED)` (`scratch:gov_probe/scan/proto_scan.py`).
  - The runtime guard of Step 4 lives in the sandbox and must name `nautilus_trader.adapters` and
    `nautilus_trader.network`. So the real sandbox gets hits.
  - The done-when "sandbox control gives 0 hits; the real tree gives 0 hits" passes at Step 4 only because the
    control lacks that guard. It fails once Step 5 lands.
- Version check.
  - Step 3's `tools/nautilus/check_env.py` sits in a scanned tree (`tests/macro_m0_harness.py:63`).
  - If it imports `nautilus_trader` to print the version, it breaks Step 4's rule that only the sandbox may import
    it.
- Fix.
  - Apply the string rule only to arguments of import machinery: `importlib.import_module`, `__import__`,
    `importlib.util.find_spec`, `runpy.run_module` and `pkgutil`. Or exempt one named constant tuple in the
    sandbox and test that it is used only in a `startswith` check.
  - Put the guard in the positive control.
  - Make the version check a `--check-env` mode of `sandbox.py`, or read versions only through
    `importlib.metadata`.

**K5. O3 and risks 2-3 rest on a false premise. The adapters are not "unimported", and the live-module tolerance
needs its own owner ruling.**

- Measured in the venv: `from nautilus_trader.backtest.engine import BacktestEngine` alone loads
  `nautilus_trader.core.nautilus_pyo3` and 35 compiled submodules (`scratch:critic_probe`). They include
  `binance`, `bybit`, `okx`, `polymarket`, `interactive_brokers`, `kraken`, `dydx`, `hyperliquid`, `network`,
  `live` and `sandbox`.
- So the Rust broker and network clients are loaded in the child of every backtest.
- The planned runtime check looks only at `nautilus_trader.adapters` and `nautilus_trader.network` (Step 4). It
  can never see these modules. Map 04's probe filter did not look for them either (`gov:run_nofile/out.txt`,
  `nt_net_or_live_modules`).
- The brief says nothing from Nautilus live or adapter execution may be imported. Yet the kernel imports seven
  `nautilus_trader.live` modules (`nt:system/kernel.py:75-77`). The synthesis settles that tolerance itself (Step 4).
- Mitigating facts the synthesis does not cite:
  - The kernel refuses live data, risk and execution engine configs in BACKTEST (`nt:system/kernel.py:373-377,
    404-408, 437-441`).
  - The child has no credentials (Step 4 launch contract).
  - Linux showed 0 socket calls (map04 §4.2).
- Fix.
  - Restate O3 with these facts.
  - Add a ruling (O13) on the kernel's live imports and the loaded Rust adapter submodules.
  - Write the full sorted `sys.modules` list into `manifest.json`. Fail any run that loads a module outside a
    golden baseline taken from F1.
  - Keep "no network on Windows" UNVERIFIED. Windows has no `strace` or `unshare` equivalent in the plan.

### 10.3 Minor

| # | Finding | Evidence | Fix |
|---|---|---|---|
| K6 | Step 5's done-when "no code path uses the `PortfolioAnalyzer`" fails by default. The engine runs the analyzer itself at the end. | `run_analysis: bool = True` (`nt:backtest/config.py:392`); engine end (`nt:backtest/engine.pyx:2143`) | `BacktestEngineConfig(run_analysis=False)`, asserted in a test. |
| K7 | An installed venv may not reveal its "wheel hash" (Step 3 `check_env.py`; Step 5 manifest). pip writes `direct_url.json` with the archive hash only for a direct URL or file install. The scratch venv has one because it came from a local file. | `https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/specifications/direct-url.rst`, lines 21-22: "MUST NOT be created when installing ... name plus version specifier"; `scratch:ntvenv/.../nautilus_trader-1.231.0.dist-info/direct_url.json` | Install from the kept local wheel paths. Otherwise record the SHA-256 of the dist-info `RECORD` and name it that. |
| K8 | The cash-rate input is not pinned, and it fails silently. `rf_daily` reads the DGS3MO cache and falls back to a flat 3% on any exception. Only the SPY and BTC md5s are pinned. | `docs/asset_expansion_study.py:94-104, 148-153`; `docs/asset_expansion/cache/fred_DGS3MO.csv` md5 `661722143f24930a29b58c535d227c1b`, last row 2026-09-23 | Pin that md5 in the run record. The runner refuses the fallback. |
| K9 | "Replicas get the same `config_id`" (row 17) is untested and type-sensitive. `canonical_json` gives `{"cost_bps":50.0}` and `{"cost_bps":50}` different hashes. The Lab's `default=str` turns a numpy integer into a string. A mismatch would append 12 extra immutable rows. | `core/ficc/macro_schema.py:303-305`; `ui/strategy_lab_page.py:75-76`; measured | Step 6 done-when: the bridge row's `config_id` for SPY `sma/126/21` at 50 bp equals the one from the Lab's `register_trials` in a temp ledger. |
| K10 | Windows encoding hazard. `-I` ignores `PYTHONUTF8`, and the house locale is cp949. test_17 checks only `tests/acceptance.py` and `tests/run_all.py`, so nothing guards `tools/nautilus/`. Because the working directory is the temp dir, a relative script path would also fail. | `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`; `tests/acceptance.py:123-129` | Launch with `-X utf8` and an absolute script path. Pass `encoding="utf-8"` on every open. Decode child output as UTF-8. Add this to Step 2's Global Constraints. |
| K11 | (a) Realism rows count in the parity verdict's trial count. `n_raw` counts every row, and Step 8 registers the 12 `timing_lag` rows before the gate (row 20). (b) Under latency, an order sent on the last bar is still in flight at the end, so "any order not FILLED" voids the realism run. | `core/quant/gate_ledger.py:332-334`; Step 5 fail-closed list | State (a) in O7. For (b), exempt only an order submitted on the final bar. |
| K12 | The pilot-2 trial count `max(11, C3 N_raw)` mixes markets. C3 also holds paper_live trend accounts on US and KR equities. | `paper_live/engine.py:64-69` | Name this in O11 and open question 6 (market-scoped `N_raw`). |
| K13 | `python tests/run_all.py --suite <name>` also rewrites `qa/acceptance_results.json`, because `main` writes `OUT` on every run. | `tests/run_all.py:128-137` | Step 2 constraint: check every "suite reports NotRun" done-when only through the redirecting wrapper (`scratch:run_baseline.py`). |
| K14 | The UNVERIFIED item in 5.2 on resetting the force-stop flag can be checked. `run` resets the flag at the start of each run. | `nt:backtest/engine.pyx:1621-1622` | Drop it from 5.2. Keep one process per run for the global `random` reseed. |
| K15 | Step 6 never says where the cost comes from. Map 01 required the runner to read QUANTGEN's table and never hard-code a rate. | map01 §12; `core/quant/validate.py:78`; `ui/strategy_lab_page.py:87-103` | The runner takes `cost_bps` from `validate.cost_floor_bp(symbols)`. It refuses a lower rate, and it refuses an uncosted symbol. |

UNVERIFIED in this review:
- Windows behaviour of the minimal child environment through the venv launcher.
- Whether F1 and F2 give byte-identical fills in standard precision.
- Whether a Windows firewall rule can confine the venv child. The venv's `python.exe` is a redirector, and the
  rule may have to target the base interpreter.
