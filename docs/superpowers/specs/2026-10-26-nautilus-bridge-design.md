# NautilusTrader bridge: an independent backtest leg for QUANTGEN's gate (research only)

Date: 2026-10-26.

Status:
- **Revision 1 (draft for referee round 1).**
  - No referee has read it yet. Appendix B records each round.
  - Owner approval: **not given**. Section 2 lists rulings O1 to O13. Each carries the default this draft takes on
    the owner's behalf, and what that default costs if it is wrong.
- Next: referee round 1, then the owner's rulings and approval, then the test-first plan (Step 2).

Inputs (all at commit `6f7c610`, branch `claude/amazing-gauss-tdiguu`):
- `research_notes/QUANTGEN Nautilus bridge map/00_synthesis.md` ("synth"): the step plan, prerequisites O1 to O12,
  defaults 1 to 31, open questions, risks, measured parity, rejected alternatives, and section 10, the critic
  findings K1 to K15;
- `research_notes/QUANTGEN Nautilus bridge map/01_nautilus_backtest_api.md` (map01): the engine side, measured on
  synthetic data;
- `research_notes/QUANTGEN Nautilus bridge map/02_quantgen_gate_ledger_lab.md` (map02): the gate, the trial ledger
  and the Strategy Lab inputs;
- `research_notes/QUANTGEN Nautilus bridge map/03_pilot_and_parity.md` (map03): the pilot port and parity, measured
  on SPY data before 2004-12-01 only;
- `research_notes/QUANTGEN Nautilus bridge map/04_governance_constraints.md` (map04): every house rule the bridge
  touches, and every conflict.

Citation keys:
- `file:line` is a QUANTGEN path at `6f7c610`. Code lines are unchanged since `f5742ab`, the commit the maps cite:
  `git diff --stat f5742ab 6f7c610` lists only the four research notes.
- `nt:<path>:<line>` is `nautilus_trader` 1.231.0 as installed in the session venv,
  `scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/<path>`. Map 01 compared four files byte for byte with
  the `v1.231.0` tag (map01 §0).
- `map0N §n`, `synth §n` and `K<n>` point into the inputs.
- `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
- UNVERIFIED marks anything nobody in this session could check.

## Owner context

The owner replaced QuantConnect with NautilusTrader: "No, actually we're going to replace QuantConnect into Nautilus
trader". The owner then asked Claude to resume and "automatically start the remaining tasks".

What those words authorise:
- building the bridge on the feature branch `claude/amazing-gauss-tdiguu`;
- running it on synthetic data, and on SPY data before 2004-12-01 as the maps did;
- writing trial-ledger rows into temporary directories only.

What they do not authorise:
- a pilot run, or any row in the production ledger `~/.nextgen/macro/ledgers` (map02 §3.1);
- a merge of the branch;
- treating this spec as approved by the full referee panel.

Pilots wait for three things, in this order:
1. the GPT and Gemini referee rounds, or a substitute that the owner records in Appendix B;
2. the owner's explicit approval of this spec, written in the Status block above;
3. the hand-off step, Step 7A (section 9).

## 1. Purpose and scope

QUANTGEN decides strategy verdicts with its own gate. The gate reads a matrix of daily net returns from a
vectorised simulator (`core/quant/strategies.py:69-90, 379-389`; `core/quant/validate.py:345-381, 492-533`). The
bridge adds a second, independent engine for that matrix: a NautilusTrader `BacktestEngine`, event driven, with
simulated fills, whole shares and a cash account.

The bridge does three things:
1. It re-computes QUANTGEN's arithmetic in an independent engine, which catches bugs in the simulator and the port.
2. It feeds the Nautilus matrices to QUANTGEN's unchanged gate, and writes a card only when parity holds.
3. It reports one realism effect, a one-session fill delay, as a registered delta that never decides a verdict.

Scope:
- **Backtest only.** The bridge uses `BacktestEngine` against Nautilus's simulated exchange. Orders never leave the
  process.
- **Research only.** QUANTGEN "goes no further than paper trading"
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:25-27`).
- **Single-instrument long/flat rules only.** `simulate` holds constant weights of current equity with no turnover
  charged, so a multi-sleeve book cannot reach parity on an execution engine (`core/quant/strategies.py:83-90`;
  synth §6 risk 17).
- **Nautilus live trading belongs to TRADEGEN, never QUANTGEN.** `TradingNode`, live clients, every adapter, the
  network clients and API keys are TRADEGEN's domain (map04 §6). QUANTGEN never imports them. TRADEGEN never
  registers trials in QUANTGEN's ledger (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:142`).
- Two pilots: pilot 1, SPY trend switch, 12 settings; pilot 2, BTC-USD crypto trend, 5 settings, only if pilot 1
  passes parity.

## 2. Owner rulings

Each row is a ruling the owner must make. The default column is what this draft builds on until the owner rules.
O1 to O12 come from synth §3.1. O13 is new, from K5.

| # | Ruling asked | Default taken on the owner's behalf | What it costs if wrong |
|---|---|---|---|
| O1 | Dependency: may `nautilus_trader==1.231.0` and its closure, `pyarrow` included, be installed? "No new dependency without the owner" is written in five places, one of which bans `pyarrow` by name (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`; map04 §2.1). | Yes, in a separate hash-pinned venv outside the repo and OneDrive, run only as a subprocess. The global interpreter, `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` stay unchanged. The `pyarrow` ban is read as binding the global interpreter and the app, not this venv. | Steps 3 to 9 stop. The branch files (`requirements-nautilus.txt`, `tools/nautilus/`, two tests, golden files) are deleted. No global state changed, so nothing outside the branch needs undoing. |
| O2 | T-RO-01 amendment (section 5.6): one allow-listed sandbox file, receiver `self` only, 7 added order verbs, full dotted-name deny-list, `nautilus_trader` imports confined to the sandbox, string-constant rule on import-machinery arguments only. | As section 5.6. Placement in `tools/` (D2 of synth §1). | Too wide: an order path could pass the scan; the negative controls of section 8.5 bound that risk. Refused: the sandbox cannot live in a scanned tree, and the bridge stops (moving it outside the scan would be evasion, map01 §9.2). |
| O3 | Reading of DO-NOT-BUILD item 21: no "broker execution adapter, inside this programme" (`QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:6162`). | Restated with K5's facts. The wheel ships 15 adapter packages (map01 §9.1). Importing `BacktestEngine` loads the compiled adapter submodules (O13). No QUANTGEN file imports or configures an adapter. The child holds no credentials (section 4.3). The kernel refuses live data, risk and execution configs in a BACKTEST environment (`nt:system/kernel.py:373-377, 404-408, 437-441`). Linux showed zero socket calls (map04 §4.2). Default reading: this is not a broker adapter inside the programme. | The programme would host a broker adapter against the council's rule. Remedy: delete the venv and the branch files. No order can have left the machine: no credentials, no measured network call on Linux. Windows has no trace (UNVERIFIED). |
| O4 | Version: 1.231.0 or a 2.0 release candidate. | 1.231.0, hash-pinned; both wheels kept locally. A v2 migration is a later, separate task. | 1.231.0 is the last 1.x release. Critical backports continue "for approximately three months after the v2 cutover"; the cutover date is not stated (map01 §10.4). A migration re-runs F1, F2 and the parity grid. |
| O5 | Parity bars: the corrected bars of section 5.4, or the original 98% / 0.99 / 0.05. | Corrected bars; the original bars are printed next to them in every report. | Too strict: a false WITHHELD on legitimate engine noise. Measured margins are 100x on correlation and 7.7x on Sharpe (section 5.4.3). Kept original: a forgotten 2x cost passes all three original bars (corr 0.9991047, abs ΔSR 0.04958, synth §7.3). |
| O6 | Pilot-1 registration table (section 10.1): start, tsmom form, cash rate, costs, embargo, benchmark, capital, account, trial count, engine-tag placement. | As section 10.1. | Ledger rows are immutable (`core/quant/gate_ledger.py:337-355`). A wrong key field leaves 12 permanent extra trials in E1 and needs a second registration. |
| O7 | Realism leg: in scope? registered? which sizing rule? | In scope for pilot 1 only. 12 `timing_lag` rows, registered before any engine starts. Fill at the next close. Buy `floor(cash / (P (1 + c) (1 + g)))` with gap buffer g = 0.10, no borrowing. Reported as a delta, never gated. These 12 rows count in the parity verdict's trial count (K11a). Pilot 2 has no realism leg. | 12 permanent E1 rows raise N and lower the DSR, which is the conservative direction. If the owner wanted no realism leg, the rows cannot be removed. |
| O8 | Referees: wait for GPT (Codex quota resets 2026-10-30 14:40; `docs/superpowers/plans/2026-10-23-execution-record.md:158`) and Gemini (`agy` on the owner's machine; `tools/debate.py:46-47`), or record a substitute. | Wait. No substitute is recorded. | Step 1 finishes about four days later. A missing referee is REVIEW_INCOMPLETE, never "no objections" (map04 R24). |
| O9 | Create the venv on Windows outside OneDrive; set `QUANTGEN_NAUTILUS_PYTHON`; report Step 3 timings. | `%LOCALAPPDATA%\quantgen\ntvenv`; the key in `.env`; timings recorded at Step 7A. | Owner time. A venv inside OneDrive would sync about 940 MB (map01 §10.2). |
| O10 | Where pilots and the suite of record run. | The owner's Windows machine, against the production ledger. Linux rehearses on synthetic and pre-window data only. | The alternative, exporting `E1.jsonl` to the cloud and copying back the extended chain, risks a fork if both copies change (synth §5.1 q10). |
| O11 | Report the row counts of `E1.jsonl` and `C3.jsonl` (UNVERIFIED today). | Not needed in advance. The runner reads them at registration and prints three counts: `len(grid)`, family-wide `N_raw` and market-scoped `N_raw`. The DSR uses `max(len(grid), family N_raw)`; for pilot 2, `max(11, C3 N_raw)`. C3 also holds paper_live trend rows for US and KR (`paper_live/engine.py:64-69`; K12). | The family-wide count over-deflates when other markets inflate it. That can turn a pilot-2 PASS into a non-PASS. It never produces a false PASS. |
| O12 | How a WITHHELD result appears in Strategy Lab. | Deferred. Bridge cards and run records live in `docs/nautilus_bridge/`, which the Lab does not read (`ui/strategy_lab_page.py:31`). | The owner reads bridge results from files until a Lab loader is ruled on. A card with `decision: "WITHHELD"` would show as UNKNOWN today (`ui/strategy_lab_page.py:303-305`). |
| O13 | (new, K5) May the child tolerate the modules the kernel and the Rust core load in every backtest? `from nautilus_trader.backtest.engine import BacktestEngine` alone loads 7 `nautilus_trader.live.*` Python modules (`nt:system/kernel.py:75-77`) and `nautilus_trader.core.nautilus_pyo3` with 35 compiled submodules, among them `binance`, `bybit`, `okx`, `polymarket`, `interactive_brokers`, `kraken`, `dydx`, `hyperliquid`, `network`, `live` and `sandbox` (measured 2026-10-26 in `scratch:ntvenv`, import only, no data). | Tolerate exactly the module set of a golden baseline per platform, recorded from fixtures F1, F2 and N3 (section 5.2.7). A run that loads any module outside it, or any `nautilus_trader.adapters.*` or `nautilus_trader.network*` Python module, is invalid. No QUANTGEN code may name these modules in an import. | Ruled unacceptable: no 1.231.0 backtest can run, because the kernel and the compiled core load them unconditionally, and the bridge stops. Tolerated wrongly: a loaded but unused Rust client could open a socket. Linux measured zero socket calls; Windows is UNVERIFIED. |

## 3. Constraints that bind every step

### 3.1 Frozen pins

- The interpreter that runs the tests must keep numpy 2.3.5, scipy 1.18.0 and pandas 2.3.3 while a readout is
  pending (`tests/frozen_guard.py:85-91`). There is no warn-only branch.
- Nautilus is never installed into the global interpreter. An eager upgrade would move numpy to 2.5.4 and pandas to
  3.1.0 (map04 §5.2).
- The suite never runs under the venv interpreter. The venv has no scipy, so clause (d) would FAIL
  (`tests/frozen_guard.py:90`).
- The venv pins the same numpy 2.3.5 and pandas 2.3.3, so both processes share numerics.

### 3.2 Order path

- Exactly one file may place simulated orders: `tools/nautilus/sandbox.py`, and only through `self.submit_order` on a
  `Strategy` subclass (section 5.6).
- The sandbox never calls `modify_order`, `cancel_order`, `cancel_orders`, `cancel_all_orders`, `close_position`,
  `close_all_positions`, `market_exit` or `submit_order_list` (`nt:trading/strategy.pyx:805, 899, 1011, 1089, 1134,
  1215, 1351, 1418, 1750`).
- Orders fill against Nautilus's simulated exchange, as QUANTGEN's own paper fills pass through `OrderBook.fill`
  (`core/engine/orders.py:90, 169, 253-257`).
- No QUANTGEN file imports `nautilus_trader.live`, `.adapters`, `.network`, `.core.nautilus_pyo3` or
  `.backtest.node`.

### 3.3 Hermeticity

- T-HERM-01 patches the parent process only and cannot reach a child (`tests/macro_acceptance.py:52-98`; map04 §4.1).
- The child gets an explicit minimal environment, a fresh temporary working directory, no `.env` key, no file
  logging, no catalog, no streaming and no database (section 4.3).
- `config.py` loads `.env` into the parent (`config.py:25-29`). The parent therefore never passes `os.environ` to the
  child. The paper pipeline ruled the same for the referee CLIs (`docs/superpowers/plans/2026-10-23-execution-record.md:93`).
- Tests write ledgers only to temporary directories (`core/quant/gate_ledger.py:927-933`; map04 §4.3 item 8).

### 3.4 No-new-dependency shape

- One new dependency file, `requirements-nautilus.txt`, installs into the venv only. `requirements.txt`,
  `requirements-dev.txt` and `pyproject.toml` stay byte-identical. `.env.example` gains `QUANTGEN_NAUTILUS_PYTHON`.
- QUANTGEN code never imports `nautilus_trader`. The parent writes files, starts the child and reads files.

### 3.5 Determinism

- One child process per (variant, cost level). `FillModel` reseeds Python's global `random`
  (`nt:backtest/models/fill.pyx:75, 77`), so it must never share a process with anything else.
- `FillModel(random_seed=42)` always.
- No UUID, run id or wall-clock value enters any hash. Fills are recorded from fill events without their UUID
  (section 5.2.6). Manifests carry no time.
- The sandbox never iterates a set or a dict of strings in an order-dependent output. `-I` ignores `PYTHONHASHSEED`,
  so string hashing is randomised in the child.
- Two separate processes on the same input must give the same fills SHA-256 (map01 §6: `4443e95f46b89f8d` in the
  probe).

### 3.6 Windows standard precision (K1)

- The win_amd64 wheel is standard precision: `DEF HIGH_PRECISION = False` in its `core/rust/model.pxd:6`
  (`scratch:critic_win/`). The Linux wheel is high precision (`nt:core/rust/model.pxd:6`).
- In standard mode `FIXED_PRECISION` is 9 (`nt:core/rust/model.pxd:18-20`), `QUANTITY_MAX` is 18,446,744,073
  (`:93-94`), and `PRICE_MAX` and `MONEY_MAX` are 9,223,372,036 (`:61-62, 77-78`).
- `Quantity.__init__` raises above `QUANTITY_MAX` (`nt:model/objects.pyx:137-140`). The planned volume of 1e12 would
  raise on Windows. The bridge uses 1e9 (section 5.2.4).
- 9 price decimals sit exactly at the standard-mode limit. The sandbox asserts the limit.
- Every margin, golden value and timing in the maps was measured in high precision. Cross-precision equality of the
  goldens is UNVERIFIED until Step 7A. A Linux rehearsal with the official wheel cannot reproduce standard mode.

### 3.7 Encoding (K10)

- The house locale is cp949 (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`).
- `-I` ignores `PYTHONUTF8`, so the child is launched with `-X utf8`.
- Every `open`, `read_text` and `write_text` in `tools/nautilus/` and the new tests passes `encoding="utf-8"`. Text
  writes pass `newline="\n"`. Child output is decoded as UTF-8 with `errors="replace"`.
- The child's working directory is the temp dir, so the script path is absolute.

### 3.8 Never concurrent with the suite

- A pilot writes `~/.nextgen/macro/ledgers`. While the suite runs, T-HERM-02 snapshots that state
  (`tests/macro_acceptance.py:25-27, 101-138`). A pilot and a suite run never overlap
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:143-144`).
- In the Linux container, `python tests/run_all.py` is never run, with or without `--suite`. Both forms rewrite
  `qa/acceptance_results.json` (`tests/run_all.py:128-137`; K13). Section 8.6 gives the only allowed form.

### 3.9 Unseen pilot windows

- Pilot 1's window is SPY from 2004-12-01; pilot 2's is the whole BTC-USD cache. Neither is computed on before
  registration (map02 §0 finding 4; map04 R23). Rehearsals use synthetic data or SPY before 2004-12-01, and the
  runner enforces this (section 5.3.1).

### 3.10 Ledger append-only

- Ledgers are append-only and hash-chained. A duplicate `config_id` never replaces the first row
  (`core/quant/gate_ledger.py:337-355`). Every variant is registered before its first engine run; a raise stops it.
- No bridge code edits `core/quant/gate_ledger.py` or another gate-package harness source
  (`core/quant/gate_package.py:36-38`).

### 3.11 Standing house rules

- Never edit `paper_live/` or `grokteam/`. Never run their replay, grid, verdict, sameday or calibrate modules, or
  `grokteam.book`.
- `tests/run_all.py`, `README.md`, `requirements.txt` and `pyproject.toml` are CRLF. They are edited only with the
  Edit tool, and never renormalised (map04 R19).
- `docs/asset_expansion/cards/` stays at 34 files and is read-only (`tests/macro_m7_cards.py:833`;
  `tests/macro_acceptance.py:26-27`).
- Bridge code contains no T-RO-01 text token. The case-sensitive token `CANO` also matches any upper-case
  identifier that contains it, such as `CANONICAL` (`tests/macro_m0_harness.py:35`).

## 4. Architecture

### 4.1 Two processes

- **Parent: the runner.** It runs in the global interpreter (numpy 2.3.5, pandas 2.3.3, scipy 1.18.0). It imports
  QUANTGEN read-only: `config`, `core.quant.strategies`, `core.quant.validate`, `core.quant.gate_ledger`. It never
  imports `nautilus_trader`; T-RO-01 rule C2 enforces that (section 5.6).
- **Child: the sandbox.** It runs in the pinned venv, one process per (variant, cost level, leg). It imports only
  allow-listed standard-library and `nautilus_trader` modules, and nothing from QUANTGEN.
- Files are the only interface. The parent writes `input.json` and `bars.csv` into a fresh temp dir. The child
  writes `fills.csv`, `decisions.csv`, `onbar_equity.csv` and `manifest.json` into the same dir. The parent reads,
  hashes and checks them, then deletes the dir.

### 4.2 Data flow

```
 owner's Windows machine: pilots of record          Linux container: rehearsal only (synthetic or SPY < 2004-12-01)

 +--- parent: global interpreter -- python -B -m tools.nautilus.runner --table T --mode {rehearsal|of-record} ---+
 |                                                                                                              |
 |  1  checks: table, git (clean, anchored), venv (--check-env vs pins), md5 pins, cost floor, GATE, chain      |
 |  2  register_trial for every variant  ------------------>  of-record: ~/.nextgen/macro/ledgers/<F>.jsonl     |
 |     (before any child starts)                              rehearsal: <tempdir>/ledgers/<F>.jsonl             |
 |  3  QUANTGEN reference: fn(prices, **theta) -> simulate via pnl_matrix (1x, 2x)                               |
 |  4  for each (column, cost level):  mkdtemp -> input.json + bars.csv ---------+                              |
 |                                                                               | launch contract (4.3)        |
 |  6  rebuild E- and R from fills + closes + rf; reconcile  <------------------+-- fills.csv, decisions.csv,  |
 |  7  parity P1-P13 (owner's bars printed too); module baseline check          |   onbar_equity.csv,          |
 |  8  all hard checks pass?                                                    |   manifest.json              |
 |       yes: walk_forward -> score_strategy (GATE unchanged) -> ModelCard      |                              |
 |       no : WITHHELD run record, no card                                      |                              |
 |  9  realism leg (pilot 1 only, after parity passes): delta in the run record |                              |
 +-------------------------------------------------------------------------------|------------------------------+
                                                                                 v
 +--- child: venv (QUANTGEN_NAUTILUS_PYTHON): nautilus_trader 1.231.0, numpy 2.3.5, pandas 2.3.3, no scipy -------+
 |  <venv python> -I -B -X utf8 <absolute path>/tools/nautilus/sandbox.py run --in <tempdir>                    |
 |  BacktestEngine(run_analysis=False) -> venue SIM (CASH, NETTING) -> port strategy -> self.submit_order       |
 |  BpFeeModel(cost_bps x stress), FillModel(seed 42), latency None (parity) or 1 ns (realism)                   |
 |  no network measured (Linux strace, map04 §4.2); no file logging; writes only into <tempdir>                  |
 +--------------------------------------------------------------------------------------------------------------+
```

### 4.3 Launch contract

The parent starts every child with exactly this call (`subprocess.run`):

| Item | Value |
|---|---|
| argv | `[<venv python>, "-I", "-B", "-X", "utf8", <absolute path of tools/nautilus/sandbox.py>, "run", "--in", <tempdir>]`; `--check-env` mode replaces the last three items with `"--check-env"` |
| venv python | `QUANTGEN_NAUTILUS_PYTHON`, read after `import config` loads `.env`, with the placeholder rules of `config._clean` (`config.py:32-39`); it must be an absolute path to an existing file |
| cwd | the fresh temp dir (`tempfile.mkdtemp(prefix="qgnb_")`) |
| env (Windows) | `SYSTEMROOT` (copied), `PATH` = `<venv Scripts dir>;%SYSTEMROOT%\System32`, `USERPROFILE` and `HOME` = `<tempdir>\home`, `TEMP` and `TMP` = `<tempdir>\tmp` |
| env (POSIX) | `PATH` = `<venv bin dir>:/usr/bin:/bin`, `HOME` = `<tempdir>/home`, `TMPDIR` = `<tempdir>/tmp`, `LANG` and `LC_ALL` = `C.UTF-8` |
| env, never | any `.env` key, `NAUTILUS_PATH`, any `PYTHON*` variable, any other inherited variable |
| stdin | `subprocess.DEVNULL` |
| stdout, stderr | captured; `encoding="utf-8"`, `errors="replace"`; the last 4,000 characters of each go into the run record |
| timeout | 900 s; a timeout kills the child and makes the run invalid |
| check | `False`; the parent reads the exit code (section 5.2.1) |

`-I` implies `-E`, `-P` and `-s`. So the child ignores `PYTHON*` variables and the user site, and the script's own
directory is not on `sys.path`. Nothing in `tools/nautilus/` can be imported by accident. Whether the venv launcher
works on Windows with this minimal environment is UNVERIFIED; Step 7A checks it.

## 5. Component design

### 5.1 `requirements-nautilus.txt`

- New file at the repo root, LF line endings.
- Header, verbatim:
  ```
  # QUANTGEN NautilusTrader bridge: a research-only backtest engine, run only as a subprocess (spec 2026-10-26).
  # NEVER install into the global interpreter: tests/frozen_guard.py clause (d) pins numpy 2.3.5, scipy 1.18.0,
  # pandas 2.3.3. Install into a dedicated venv outside the repo and OneDrive, for example
  #   %LOCALAPPDATA%\quantgen\ntvenv\Scripts\python -m pip install --require-hashes --only-binary=:all: -r requirements-nautilus.txt
  ```
- Body: every distribution pinned with `==` and `--hash=sha256:` lines for both the cp313 win_amd64 wheel and the
  cp313 manylinux x86_64 wheel (or the `py3-none-any` wheel where only one exists).
- Distributions, from the venv's resolution (map04 §2.2): `nautilus_trader==1.231.0`, `numpy==2.3.5`,
  `pandas==2.3.3`, `pyarrow==26.0.0`, `fsspec==2026.2.0`, `msgspec==0.22.0`, `click==8.5.0`, `portion==2.6.3`,
  `pytz==2026.5`, `tqdm==4.70.1`, `tzdata==2026.5`, `python-dateutil==3.0.0`, `six==1.17.0`,
  `sortedcontainers==2.4.0`, `uvloop==0.22.1 ; sys_platform != "win32"`, and `colorama==<collected> ; sys_platform
  == "win32"`.
- The two `nautilus_trader` hashes are measured and equal PyPI's (synth §9.3):
  - win_amd64: `5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf`;
  - manylinux_2_35_x86_64: `429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91`.
- The other hashes and the `colorama` version are collected in Step 3 with `pip download --only-binary=:all:
  --platform <tag> --python-version 3.13 --no-deps` per distribution, into a scratch folder (C3 of synth §3.2).
- The runner reads the expected versions of `nautilus_trader`, `numpy` and `pandas` from this file. It is the single
  source of the version pins.
- The owner keeps both `nautilus_trader` wheels outside the repo, for example `%LOCALAPPDATA%\quantgen\wheels\`, as a
  guard against a yank.

### 5.2 `tools/nautilus/sandbox.py`

#### 5.2.1 Modes and exit codes

```
<venv python> -I -B -X utf8 <abs>/tools/nautilus/sandbox.py --check-env
<venv python> -I -B -X utf8 <abs>/tools/nautilus/sandbox.py run --in <tempdir>
```

- `--check-env` prints one JSON object to stdout and writes nothing. Fields: `python`, `platform`, `versions`,
  `precision`, `wheel_identity`, `env_keys`, `sys_modules` (section 6.2). It replaces synth's
  `tools/nautilus/check_env.py`. A separate file would sit in a scanned tree and would have to import
  `nautilus_trader` outside the sandbox (K4).
- `run` reads `input.json` and `bars.csv`, runs one backtest and writes four files (section 5.2.6).
- Exit codes:
  - 0: run complete and valid by the child's own checks;
  - 10: run complete but invalid; `manifest.json` is written with `valid: false`;
  - 20: input refused before the engine was built (schema, SHA-256, a precision or volume limit);
  - any other value: a crash. The parent treats every non-zero code as an invalid run.

#### 5.2.2 Imports

Only these, all as `from <module> import <names>`:
- standard library: `__future__`, `argparse`, `csv`, `dataclasses`, `decimal`, `hashlib`, `importlib.metadata`,
  `json`, `math`, `os`, `pathlib`, `platform`, `sys`, `typing`;
- `nautilus_trader.backtest.engine`: `BacktestEngine`;
- `nautilus_trader.backtest.models`: `FeeModel`, `FillModel`, `LatencyModel`;
- `nautilus_trader.config`: `BacktestEngineConfig`, `LoggingConfig`, `StrategyConfig`;
- `nautilus_trader.trading.strategy`: `Strategy`;
- `nautilus_trader.common.component`: `is_backtest_force_stop`;
- any name from `nautilus_trader.model` and its submodules (`Bar`, `BarType`, `Price`, `Quantity`, `Money`, `Equity`,
  `CurrencyPair`, `USD`, `BTC`, enums, identifiers, and the constants `HIGH_PRECISION`, `FIXED_PRECISION`,
  `QUANTITY_MAX`, `PRICE_MAX` from `nautilus_trader.model.objects`, `nt:model/objects.pyx:76-84`).

Versions come from `importlib.metadata.version(...)`, never from `import nautilus_trader`. The import paths are the
1.231.0 ones; the v2 paths in the tag's docs fail on this wheel (map01 §10.4).

#### 5.2.3 Engine, venue, instrument, fees and fills

| Object | Exact construction |
|---|---|
| Engine | `BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), logging=LoggingConfig(log_level="ERROR"), run_analysis=False))`. `run_analysis` defaults to `True` (`nt:backtest/config.py:392`) and runs the analyzer at the end (`nt:backtest/engine.pyx:2143`); the bridge turns it off (K6). No `log_level_file`, no catalog, no streaming. The child asserts `config.environment.name == "BACKTEST"`. |
| Venue | `engine.add_venue(...)` with: `venue=Venue("SIM")`; `oms_type=OmsType.NETTING`; `account_type=AccountType.CASH`; `base_currency=USD` (SPY) or `None` (BTC/USD); `starting_balances=[Money(1_000_000, USD)]`, plus `Money(0, BTC)` for BTC/USD; `fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=42)`; `fee_model=BpFeeModel(cost_bps, stress)`; `latency_model=None` (parity) or `LatencyModel(base_latency_nanos=1)` (realism); `bar_execution=True`; `bar_adaptive_high_low_ordering=False`; `allow_cash_borrowing=False`. A `CurrencyPair` needs `base_currency=None` on a CASH venue (`nt:backtest/engine.pyx:762-770`). |
| SPY | `Equity(instrument_id=InstrumentId(Symbol("SPY"), Venue("SIM")), raw_symbol=Symbol("SPY"), currency=USD, price_precision=9, price_increment=Price.from_str("0.000000001"), lot_size=Quantity.from_int(1), ts_event=0, ts_init=0, maker_fee=Decimal(0), taker_fee=Decimal(0))`. Whole shares only (`nt:model/instruments/equity.pyx:115-117`). |
| BTC/USD | `CurrencyPair(instrument_id=InstrumentId(Symbol("BTC/USD"), Venue("SIM")), raw_symbol=Symbol("BTC/USD"), base_currency=BTC, quote_currency=USD, price_precision=9, size_precision=8, price_increment=Price.from_str("0.000000001"), size_increment=Quantity.from_str("0.00000001"), ts_event=0, ts_init=0, maker_fee=Decimal(0), taker_fee=Decimal(0))`. Spot, long/flat, commission in USD (map03 §5.2). |
| `BpFeeModel(FeeModel)` | `__init__(cost_bps: str, stress: str)`: `rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)`; raises `ValueError` when `Decimal(stress) < 1`. `get_commission(order, fill_qty, fill_px, instrument)` returns `Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate, instrument.quote_currency)`. A Python subclass works and equals `MakerTakerFeeModel` with `taker_fee = c` (map01 §5.1). |
| Fill model | `prob_slippage=0`: all cost sits in one number, so the 2x leg doubles one number (map01 §5.2). |
| Fill timing | MARKET, GTC, sent from `on_bar`. With no latency it fills at the same bar's close: the engine moves the book through the bar, calls the strategy, then settles (`nt:backtest/engine.pyx:1716, 1724, 1727`). `AT_THE_CLOSE` is rejected in backtest and never used (`nt:backtest/engine.pyx:5333-5339`). |

There is no `change_fee_model`, so each cost level is a fresh engine in a fresh process (map01 §2.2).

#### 5.2.4 Bars (K1)

- Built with the wrangler's own constructor calls (`nt:persistence/wranglers.pyx:779-791`), not from a DataFrame:
  `Bar(bar_type, Price.from_str(close_str), Price.from_str(close_str), Price.from_str(close_str),
  Price.from_str(close_str), Quantity(volume, size_precision), ts, ts)`. O = H = L = C = the adjusted close. This
  removes the positional-column hazard of the wrangler (map01 §2.4) instead of asserting around it.
- Bar types: `SPY.SIM-1-DAY-LAST-EXTERNAL` and `BTC/USD.SIM-1-DAY-LAST-EXTERNAL`. `EXTERNAL` is required for bar
  execution (`nt:backtest/engine.pyx:4757-4758`).
- Timestamps: `ts_event = ts_init` = the close. SPY: the date at 21:00 UTC. BTC: the next calendar day at 00:00 UTC.
  Parity does not depend on the hour (map03 §5.2).
- Prices: the parent rounds each close once to 9 decimals and writes it with `f"{x:.9f}"`. The child asserts
  `price_precision <= FIXED_PRECISION` before building anything; else exit 20.
- Volume: the constant 1,000,000,000 at the instrument's size precision. The child asserts
  `volume <= QUANTITY_MAX`; else exit 20. On a LAST bar the close carries a quarter of the volume, 2.5e8 units
  (`nt:backtest/engine.pyx:4804-4805, 4850-4880`). At $1M equity an order exceeds that only below $0.004 a unit, so
  the L1 quarter-volume rule never binds. Thin volume would cap fills and kill the run (map03 §4.2 C2).
- The child asserts strictly increasing timestamps and `n_bars` equal to `input.json`.

#### 5.2.5 Strategy ports

Both ports are independent re-implementations of `core/quant/strategies.py:162-187` and `:330-348`. They share these
rules:
- Decisions use the parent's float array, parsed from `bars.csv`. On every bar the child asserts that
  `bar.ts_event` equals the file's timestamp and that `bar.close == Price.from_str(close_str)` exactly. Both engines
  therefore decide on identical floats.
- A decision is logged on every decision bar (`decisions.csv`), with its margin.
- The strategy trades only when the decision differs from the held state. It never tops up or trims between
  decisions, because QUANTGEN charges no turnover for drift (`core/quant/strategies.py:88`). A re-target-every-bar
  loop made 401 fills for zero switches (map01 §11).
- Entry: buy `q = floor(cash / (P (1 + c s) (1 + g)))` in `Decimal`. `cash` is the account's USD balance as a
  Decimal. `P` is `Decimal(close_str)`. `c` is `cost_bps / 1e4`, `s` the stress, `g` the gap buffer (0 in parity,
  0.10 in realism). SPY floors to whole shares; BTC floors to 8 decimals with `ROUND_FLOOR`. If `q` is 0, no order
  is sent and the row says so.
- The buffer exists because the risk engine checks notional against cash but ignores the fee
  (`nt:risk/engine.pyx:942-955`). Without it the fee pushes cash below zero and the engine stops the backtest
  silently (`nt:backtest/engine.pyx:1742-1745`).
- Exit: sell the whole net position.
- No liquidation at the end. QUANTGEN never liquidates (map03 §2.5).
- If an order is still in flight on a decision bar, the run is invalid (C-13 in section 7). With steps of 21 or more
  sessions this cannot happen in the trend legs.
- The strategy's own state uses names other than `state`, which a Nautilus component already owns (map03 §2.5).

Trend switch (`TrendSwitchPort`), parameters `rule`, `lookback` L, `step` s:
- Bar counter i starts at 0 on the first panel row. Decision bars: `i >= L and (i - L) % s == 0`
  (`core/quant/strategies.py:146-147, 176`).
- `sma`: `on = P[i] > sum(P[i-L+1 : i+1]) / L`, a plain left-to-right sum. Margin: `abs(P[i] - mean) / P[i]`.
  QUANTGEN uses a cumulative-sum SMA (`core/quant/strategies.py:111-116`), so the two can differ in the last bits;
  P1's margin exemption covers that.
- `tsmom`: `on = (P[i] / P[i-L] - 1.0) > 0.0`, the study's raw form, because `pnl_matrix` passes no rate
  (`core/quant/strategies.py:180-181, 384`). Margin: `abs(P[i] / P[i-L] - 1.0)`.

Crypto trend (`CryptoTrendPort`), parameters `hysteresis` h, `lookbacks`, `mas`:
- Warm-up `max(max(lookbacks), max(mas))`; a decision on every bar from then on.
- Votes: `sign(P[i] - P[i-k])` for each k in `lookbacks`, and `sign(P[i] - mean(P[i-n+1 : i+1]))` for each n in
  `mas`, with `sign(x) = (x > 0) - (x < 0)`.
- `comp = sum(votes) / len(votes)`. The sum is an exact integer, so this equals `np.mean` on one column.
- State: 1 if `comp > h`, 0 if `comp < -h`, else unchanged (`core/quant/strategies.py:343-347`).
- Margin: the smallest relative distance `abs(P[i] - ref) / P[i]` over all votes.
- The pilot uses the study's defaults: lookbacks (7, 14, 21, 28), MAs (10, 20, 50, 100, 200).

#### 5.2.6 Outputs (all in the temp dir, UTF-8, LF)

| File | Columns or content |
|---|---|
| `fills.csv` | One row per `on_order_filled` event (`nt:trading/strategy.pyx:723`): `ts_event` (int ns), `order_side` (BUY or SELL), `last_qty` (str), `last_px` (str), `commission` (str amount), `commission_ccy` (str), `trade_id` (str), `venue_order_id` (str). No UUID column exists in this file. Trade ids are deterministic FNV-1a hashes (map01 §6). |
| `decisions.csv` | One row per decision bar: `i` (int), `ts_event` (int ns), `decision` (0 or 1), `margin` (float, `repr`), `action` (`buy`, `sell`, `hold`, or `skip_zero_qty`). |
| `onbar_equity.csv` | One row per bar, recorded in `on_bar` before any order: `i`, `ts_event`, `close` (str), `cash` (str), `qty` (str), `equity_pre` (str, `cash + qty x close` in Decimal). |
| `manifest.json` | Section 6.2. |

The child never calls `PortfolioAnalyzer` or reads the account report as equity. On a CASH account the analyzer's
returns are cash only; the probe printed a Sharpe of +1.94 for a run whose true Sharpe was -1.90 (map01 §0 finding 5).

#### 5.2.7 Checks in the child, and the module baseline

The child marks the run invalid (exit 10) when any of these holds:
- `is_backtest_force_stop()` is true after `engine.run()` (`nt:common/component.pyx:619-620`);
- bars seen by the strategy are fewer than bars fed;
- `engine.get_result().backtest_end` is earlier than the last bar's timestamp;
- any order is not FILLED. Realism leg only: an order submitted on the final bar and still in flight at the end is
  exempt, and counted in `inflight_last_bar_exempt` (K11b). No other exemption exists;
- any `OrderDenied` or `OrderRejected` event;
- an order was in flight on a decision bar.

`run` resets the force-stop flag at the start of each run (`nt:backtest/engine.pyx:1621-1622`), so K14's open item is
closed. One process per run stays, for the global `random` reseed.

The child records the full sorted `sys.modules` key list after `engine.run()` in `manifest.json`. It does not judge
it, so the sandbox contains no denied module name (K4). The parent judges it:
- a run is invalid if any loaded module is outside the golden baseline of its platform tag, recorded in
  `tools/nautilus/golden/modules_<platform tag>.json`;
- a run is invalid if any loaded module is `nautilus_trader.adapters` or `nautilus_trader.network`, or starts with
  either name followed by a dot.

The baseline for a platform is the union of the F1, F2 and N3 module lists on that platform; N3 covers the latency
path of the realism leg. Step 5 records the Linux baseline and Step 7A the Windows one. A new baseline is reviewed as
a diff against the other platform's before it is committed. Both are JSON files, which T-RO-01 never scans.

### 5.3 `tools/nautilus/runner.py`

#### 5.3.1 Command line and modes

```
python -B -m tools.nautilus.runner --table <registration.json> --mode rehearsal --ledger-dir <tmp> --out <tmp>
python -B -m tools.nautilus.runner --table <registration.json> --mode of-record
python -B -m tools.nautilus.runner --check-env
python -B -m tools.nautilus.runner --fixtures [--record-baseline]
```

| Mode | Ledger | Data | Tree | Outputs |
|---|---|---|---|---|
| `rehearsal` | `--ledger-dir` is required and must resolve under `tempfile.gettempdir()`; else refuse | synthetic tables, or SPY with every panel date before 2004-12-01; the real `yf_BTC-USD.csv` is refused | may be dirty | `--out`, required, under the temp dir |
| `of-record` | `config.macro_dir() / "ledgers"` (`config.py:176-178`); `--ledger-dir` is refused | the pinned files of the table | clean (5.3.2 step 2) | `docs/nautilus_bridge/runs/` and `docs/nautilus_bridge/cards/` |

- `--check-env` runs `sandbox.py --check-env` through the launch contract and compares it with the pins. It prints the
  result and exits 0 on a match, 2 on a mismatch.
- `--fixtures` runs F1, F2 and N1 through the launch contract and compares them with their goldens.
  `--record-baseline` also writes the platform's module baseline and its `env_pins.json` entry. Both are used once
  per platform, in Steps 5 and 7A.
- The registration table is a JSON file (section 10). Of-record tables live in `docs/nautilus_bridge/registration/`
  and are committed. A table needs a non-empty `owner_confirmed` field in of-record mode.

#### 5.3.2 Order of operations (of-record)

1. **Table.** Load and validate the table. Assert that its `grid` list equals `S.grid_from(**axes)` element by
   element (`core/quant/strategies.py:392-398`). Refuse without `owner_confirmed`.
2. **Git.** Refuse if `gate_ledger.repo_anchor()` returns UNVERSIONED (`core/quant/gate_ledger.py:122-131`), or if git
   is missing. Refuse if `git status --porcelain` lists anything other than untracked (`??`) paths under
   `docs/nautilus_bridge/runs/` or `docs/nautilus_bridge/cards/` (K2). The house study runner refuses a dirty tree
   for the same reason (`tools/paper/study.py:99-101`). Assert that the anchor's sha equals `git rev-parse HEAD`.
   Record the sha.
3. **Venv.** Refuse if `QUANTGEN_NAUTILUS_PYTHON` is unset or not a file. Run `--check-env`. Refuse unless
   `nautilus_trader`, `numpy` and `pandas` equal the `requirements-nautilus.txt` pins, Python is 3.13.x, and the
   wheel identity equals `tools/nautilus/golden/env_pins.json` for the platform tag (K7, section 6.2).
4. **Data.** Check the md5 of the price file against the table. Read it as the study does: first column as the index,
   `parse_dates=True`, `.iloc[:, 0]`, `dropna()`, keep values above zero (`docs/asset_expansion_study.py:68-79`).
   Apply the start filter, require at least 300 rows (`docs/asset_expansion_study.py:138-145`), and require strictly
   increasing unique dates. Round once to 9 decimals.
5. **Cash rate (K8).** Pilot 1 only. Check the md5 of `docs/asset_expansion/cache/fred_DGS3MO.csv` against the table
   (`661722143f24930a29b58c535d227c1b`, K8). Compute `rf = DGS3MO.reindex(dates, method="ffill") / 100 / 252`.
   Refuse if the file is missing, unreadable or of a different md5, or if any value is NaN after the forward fill.
   The study would silently fall back to a flat 3% on any exception, and fill a leading NaN with 0.03 percent
   (`docs/asset_expansion_study.py:148-153`); the bridge does neither.
6. **Cost (K15).** `floor, classes = validate.cost_floor_bp([symbol])` (`core/quant/validate.py:115-121`). Refuse if
   `floor` is None (an uncosted symbol). Refuse if the table's `cost_bps` is below `floor`. The bridge never
   hard-codes a rate. The Lab withholds in the same two cases (`ui/strategy_lab_page.py:87-103`).
7. **Gate.** Snapshot `validate.GATE` with `copy.deepcopy`. Refuse if `GATE["bootstrap_B"] != 2000`.
8. **Ledger.** `family_ledger(family_id, ledger_dir)`. Refuse if `verify_chain()` fails. Record `hash()` and `n_raw`.
9. **Register.** For each parity variant in grid order, then each realism variant: `register_trial(ledger, row,
   script="tools/nautilus/runner.py")` with the row of section 6.4 (`core/quant/gate_ledger.py:379-386`). Record
   `config_id`, `appended`, and the row's own `row_md5` field, `result.row["row_md5"]`. Do not use the third element
   of `RegisterResult`: for a fresh append it is the md5 of the whole stored line, chain fields included, while for a
   duplicate it is the row's content hash (`core/quant/gate_ledger.py:217-218, 346, 355`). A raise stops the run.
10. **Snapshot.** Record `hash()`, `n_raw` and the market-scoped count after registration, and the UTC time.
11. **Reference.** For each column: `W = fn(prices, **theta)`, then `pnl, turnover = simulate(prices, W,
    cost_bps=cost_bps, cash_daily=rf)` and the stress twin at `2 x cost_bps`. This is `pnl_matrix`, column by column,
    so the weights are kept for P1 and P4 (`core/quant/strategies.py:379-389`).
12. **Children.** One child per (column, cost level), sequentially: 1x and 2x for every column of the parity leg.
13. **Rebuild and check** each child (5.3.3, section 7).
14. **Parity** (5.4). Then the gate hand-off (5.5), or a WITHHELD record.
15. **Realism** (pilot 1): only after the parity leg passed every hard check. One 1x child per column. Reported in
    the run record only.
16. **Write** the run record, and the card if one was earned.

Rehearsal mode runs the same steps with these differences: a dirty tree is allowed; `owner_confirmed` is not needed;
the ledger and outputs live under the temp dir; the data rules of 5.3.1 apply.

#### 5.3.3 Return reconstruction

Let `P(t)` be the shared close, `q(t)` and `cash(t)` the position and cash after the fills of bar t, rebuilt from
`fills.csv` in Decimal: a buy subtracts `qty x px + commission`, a sell adds `qty x px - commission`. Start with
`cash(-1) = capital` and `q(-1) = 0`.

```
E-(t) = cash(t-1) + q(t-1) P(t)                         equity marked at close t, before the fills of bar t
R(t)  = E-(t+1) / E-(t) - 1 + (cash(t) / E-(t)) rf(t)   for t = 0 .. T-2, labelled dates[t+1]
TV(t) = sum over fills at bar t of qty x px / E-(t)      for t = 0 .. T-2; fills at bar T-1 are dropped
```

- This is the exact analogue of `pnl(t) = w(t) r(t+1) + (1 - w(t)) rf(t) - c abs(Δw(t))` (map03 §2.9;
  `core/quant/strategies.py:82-90`). The last term of R is the cash-interest overlay; Nautilus pays no interest
  (map03 §0 finding 13).
- A fill belongs to bar t when its `ts_event` equals bar t's timestamp. A fill at any other time makes the run
  invalid in the parity leg.
- Cross-checks: the rebuilt `E-(t)` equals `onbar_equity.csv` within $0.01 times the fills so far; the final rebuilt
  cash equals the manifest's account balance within $0.01 per fill. `Money` rounds each commission to the cent; the
  probe saw $0.018 over 13 fills (map03 §2.9).

#### 5.3.4 Matrices

- `pnl_nt` (T-1 x G, 1x), `pnl_stress_nt` (T-1 x G, 2x) and `turnover_nt` (T-1 x G, from the 1x run).
- Columns in `grid_from` order, the order of the registered rows.
- `dates = panel_dates[1:]`, ISO strings, as the study (`docs/asset_expansion_study.py:184`).
- The QUANTGEN reference `pnl_qg`, `pnl_stress_qg` and `turnover_qg` have the same shape, built in the same process.

### 5.4 `tools/nautilus/parity.py`

#### 5.4.1 Checks

Per column, at 1x and at 2x, unless the row says otherwise. Every hard failure withholds the verdict for the whole
grid, because CSCV and the DSR dispersion need every column (map03 §3.3). Every report prints the owner's original
bars next to the corrected ones.

| ID | Check | Owner bar | Corrected bar | Kind |
|---|---|---|---|---|
| P1 | Decision agreement on the decision bars: QUANTGEN's `W[t] > 0` at each decision bar against the child's logged `decision` (the decision, not the position) | >= 98% | = 100%, except a decision whose QUANTGEN margin is below 1e-9 relative; each exempt decision is listed | hard |
| P2 | Pearson correlation of `R` and `pnl` over all T-1 rows, flat days included | >= 0.99 | >= 0.9999 | hard |
| P3 | abs(`validate.sharpe(R)` - `validate.sharpe(pnl)`) (`core/quant/validate.py:137-143`) | <= 0.05 | <= 0.01 | hard |
| P4 | The set of bars with a fill, excluding bar T-1, equals `{t < T-1 : abs(Δw(t)) > 0}` | none | equal | hard |
| P5 | max abs(fill price / close - 1) | none | <= 1e-6 | warning |
| P6 | Turnover ratio: sum of `TV` over sum of abs(Δw), both excluding bar T-1 | none | in [0.99, 1.005] | warning |
| P7 | Cost ratio: sum of commission / E- over c times sum of abs(Δw) | none | in [0.99, 1.005] | warning |
| P8 | abs(MDD(R) - MDD(pnl)) on compounded curves | none | <= 0.005 | warning |
| P9 | Tracking error, std(R - pnl, ddof=1) x sqrt(252) | none | <= 0.001 | warning |
| P10 | Daily gap, per row | none | abs(R - pnl) <= c(c + abs(r))/(1 + c) + (P(t)/E-(t)) abs(r) + 1e-9, with c the leg's cost and r = r(t+1) | warning |
| P11 | Walk-forward chosen column per origin, from `walk_forward` on each 1x matrix | none | equal, except an exempt near-tie (5.4.2) | hard |
| P12 | P2 and P3 on the selection-matched OOS series, 1x and 2x (5.4.2) | none | as P2 and P3 | hard |
| P13 | Completeness: the child's checks (5.2.7), the module checks, the reconciliation (5.3.3), and the input SHA-256 match | none | all pass | hard |

P1's exemption covers a floating-point tie between a cumulative-sum SMA and a plain mean (map03 §3.4 source 7); none
occurred in 12 x 2,497 bars. P10 adds a one-share term to synth's bound, about 1e-4 abs(r) at $1M and SPY near $100;
P10 is a warning, so the term only removes false warnings.

#### 5.4.2 Selection: P11, P12 and the near-tie rule (K3)

- `wf_qg = walk_forward(pnl_qg, dates, turnover=turnover_qg, pnl_stress=pnl_stress_qg, embargo=E)` and `wf_nt`
  likewise from the Nautilus matrices, with the GATE windows (`core/quant/validate.py:345-381`).
- **P11.** For each origin k, compare `wf_qg.chosen[k]` with `wf_nt.chosen[k]`. A mismatch is exempt only when the
  QUANTGEN in-sample Sharpe gap between the two columns, `abs(wf_qg.is_sharpes[k, a] - wf_qg.is_sharpes[k, b])`, is
  below 0.005. An exact QUANTGEN tie is a gap of 0 and is exempt. Any other mismatch fails.
- **P12.** Build both OOS series with QUANTGEN's selection: for each origin k, the rows of `walk_forward`'s OOS block
  `[o_k + E, o_k + E + w_oos)`, truncated at the last row (`core/quant/validate.py:374-375`), of column
  `wf_qg.chosen[k]`, from `pnl_qg` and from `pnl_nt`; the same for the 2x matrices. Apply P2 and P3 to the two
  concatenations. P12 therefore never compares two different columns.
- **An exempt flip.** If P11 has at least one exempt mismatch, the runner scores both walk-forwards with identical
  inputs: `score_strategy(wf_qg, ...)` and `score_strategy(wf_nt, ...)`. If the two decisions differ, the run is
  WITHHELD with the reason "selection near-tie". If they agree, the card is written from `wf_nt` and names every
  exempt origin.
- **Why.** On map 03's pre-2004 matrices, two origins have a runner-up within 0.005: 1386 (gap 0.00059) and 2394
  (gap 0.00114). Had Nautilus taken the runner-up, P12 computed on two different columns would give corr 0.9465 and
  ΔSR +0.045, failing both corrected bars. Engine noise in in-sample Sharpe reached 0.00069 (map03 §4.4), larger than
  the smaller gap. At origins 1512 and 1638, columns 4, 5 and 9 tie exactly in QUANTGEN while Nautilus column 9
  differs by about 1e-6 (0.737800031 against 0.737801118) (K3, `scratch:critic_probe/wf_ties.py`).
- The card's `rules.selection` field states which selection the card used, and lists exempt origins.

#### 5.4.3 Evidence for the bars

Measured parity (synth §7.1):

| Evidence | Data | Result | Source |
|---|---|---|---|
| Synthetic SMA switch, whole shares, $100k | 600 seeded bars | agreement 1.000; corr 0.9999993; ΔSR 0.0021 (1x), 0.0056 (2x) | map01 §7 |
| Real SPY `sma/210/21`, $1M, 9 dp, CASH with buffer | 1995-01-03 to 2004-11-30, 2,497 sessions | agreement 109/109; corr 0.99999995; ΔSR -0.00006 (1x), +0.00013 (2x) | map03 §4.2 |
| Same, DGS3MO overlay | same | ΔSR -0.00006; TE 4e-5 a year | map03 §4.2 |
| All 12 settings x 1x and 2x | same | min corr 0.99999901; max abs ΔSR 0.0013; agreement 100%; max daily gap 3.80 bp; all runs complete | map03 §4.3 |
| Walk-forward selection | same, embargo 21 | the same column at all 14 origins; OOS corr 0.99999996; ΔSR +0.00004 (1x), +0.00036 (2x) | map03 §4.4 |
| Crypto trend, 5 hysteresis values, 10 and 20 bp | 1,500 synthetic calendar days | agreement 100% on 1,300 decisions; min corr 0.99999984; max abs ΔSR 0.0003 | map03 §4.5 |
| Fixtures F1 and F2 | hand-built | fills, commissions and final cash match hand arithmetic to the cent on both engines | map03 §6 |
| Failure modes | pre-2004 SPY | 2 dp: TE 0.085%/yr, passes; thin volume: run stopped at bar 211, fails; 1-session latency: corr 0.98295, ΔSR -0.098, fails by design | map03 §4.2 |

How loose the owner's bars are (synth §7.3: SPY 1995-01-03 to 2004-11-30, `sma/210/21`, 50 bp; one 21-session
decision block flipped at a time, 109 blocks, each standing in for a port bug):

| Quantity | Result |
|---|---|
| Correlation of a single-flip P&L with the true P&L | min 0.9591, median 0.9933, max 0.9983 |
| abs ΔSharpe of a single flip | median 0.0283, max 0.1554 |
| Share caught by corr < 0.99 / abs ΔSR > 0.05 / either | 27.5% / 16.5% / 36.7% (63% pass both) |
| Share caught by corr < 0.9999 / abs ΔSR > 0.01 | 100% / 86.2% |
| A 2x engine that charges 1x | corr 0.9991047, abs ΔSR 0.04958: passes both owner bars |

The whole 1x-to-2x Sharpe difference on that setting is 0.0496 (0.76802 against 0.71844), so a bridge that forgot to
double the cost passes the 0.05 bar; the corrected P3 catches it with a 5x margin. The corrected P2 keeps a 100x
margin over the worst measured 1 - ρ of 1e-6, and P3 a 7.7x margin over the worst measured 0.0013. No parity number
exists for the pilot windows, by design. The legitimate gap scales with c and abs(r) on entry days, so its Sharpe
effect should stay near 0.0013 at 2x (synth §7.5): UNVERIFIED until the pilot runs, and in standard precision.

### 5.5 Gate hand-off

Only when every hard check of 5.4.1 passes, at both cost levels, for every column:

1. `wf = wf_nt` (5.4.2).
2. Benchmark: `bench = P[1:] / P[:-1] - 1` (one column), aligned with `wf.dates` as the study does
   (`docs/asset_expansion_study.py:186-190, 275, 334`). Uncosted.
3. Trial counts: `len_grid`, `family_n_raw` (after registration) and `market_n_raw` (rows whose `market` equals the
   table's market). `n_trials = max(len_grid, family_n_raw)`; pilot 2 uses `max(11, family_n_raw)`, because the
   stored card already counts 11 (`docs/asset_expansion_study.py:339-343`). All three are printed and stored.
4. `sc = score_strategy(wf, grid=grid, full_pnl=pnl_nt, n_trials=n_trials, bench_daily=bench, seed=11,
   domain=<table domain or None>)` (`core/quant/validate.py:492-533`). Pilot 2 passes
   `domain={"hysteresis": (0.0, 0.889)}` (`docs/asset_expansion_study.py:339`).
5. Assert `validate.GATE == gate_snapshot` (deep equality) after scoring; a difference voids the run (no card).
6. `assert_hash_at_run(ledger, hash_after_registration)` before writing anything (`core/quant/gate_ledger.py:389-396`).
   A raise means the ledger moved after registration: no card, run record WITHHELD.
7. Write a `validate.ModelCard` (`core/quant/validate.py:802-834`) with `card.save(Path("docs/nautilus_bridge/cards"))`.
   Never into `docs/asset_expansion/cards/`.
8. Write the run record with status `CARD_WRITTEN`.

A WITHHELD result writes one run record and no card. The decision value WITHHELD is never written into a card,
because the scorecard knows only `validate.DECISIONS` (`core/quant/validate.py:50`).

### 5.6 T-RO-01 amendment (`tests/macro_m0_harness.py`)

Rationale for the amendment, to be quoted in the test's docstring: orders in a Nautilus backtest fill against a
simulated exchange inside one process, as QUANTGEN's own paper fills pass through `OrderBook.fill`
(`core/engine/orders.py:90, 169, 253-257`). The amendment lets exactly one file place such orders, and it closes two
holes of today's scan: it compares only the first dotted component of an import (`tests/macro_m0_harness.py:90-96`),
and it misses six Nautilus order verbs (map04 §3.2). The council spec is not edited; this spec amends T-RO-01's scope in
its own text, as the 2026-10-23 spec did (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:177-181`).

Constants, inserted after `ALLOWED_BARE_CALLS` (`tests/macro_m0_harness.py:56`):

```python
NAUTILUS_SANDBOX = "tools/nautilus/sandbox.py"   # the one file that may place simulated orders (spec 2026-10-26 §5.6)
NAUTILUS_ALLOWED_FROM = {                          # sandbox only: module -> names it may import
    "nautilus_trader.backtest.engine": frozenset({"BacktestEngine"}),
    "nautilus_trader.backtest.models": frozenset({"FeeModel", "FillModel", "LatencyModel"}),
    "nautilus_trader.config": frozenset({"BacktestEngineConfig", "LoggingConfig", "StrategyConfig"}),
    "nautilus_trader.trading.strategy": frozenset({"Strategy"}),
    "nautilus_trader.common.component": frozenset({"is_backtest_force_stop"}),
}
NAUTILUS_MODEL = "nautilus_trader.model"           # sandbox only: any name from this module or below
NAUTILUS_DENIED = ("nautilus_trader.live", "nautilus_trader.adapters", "nautilus_trader.network",
                   "nautilus_trader.core.nautilus_pyo3", "nautilus_trader.backtest.node", "nautilus_pyo3")
NAUTILUS_DENIED_NAMES = frozenset({
    "TradingNode", "TradingNodeBuilder", "TradingNodeConfig", "LiveExecClientConfig", "LiveDataClientConfig",
    "SandboxExecutionClient", "get_env_key", "get_env_key_or", "HttpClient", "WebSocketClient", "SocketClient",
    "nautilus_pyo3"})
NAUTILUS_ORDER_VERBS = frozenset({"modify_order", "cancel_orders", "cancel_all_orders", "close_position",
                                  "close_all_positions", "market_exit", "submit_order_list"})
IMPORT_MACHINERY = frozenset({"import_module", "__import__", "find_spec", "spec_from_file_location",
                              "module_from_spec", "run_module", "run_path", "resolve_name", "get_loader",
                              "find_loader", "reload"})
SANDBOX_IMPORTS = frozenset({"__future__", "argparse", "csv", "dataclasses", "decimal", "hashlib",
                             "importlib.metadata", "json", "math", "os", "pathlib", "platform", "sys", "typing"})
SANDBOX_DYNAMIC = frozenset({"getattr", "setattr", "delattr", "eval", "exec", "compile", "globals", "vars",
                             "__import__"})
SANDBOX_OS_CALLS = frozenset({"system", "popen", "startfile", "fork", "kill", "execv", "execve", "execvp",
                              "spawnv", "spawnve", "spawnl"})
```

`FORBIDDEN_CALLS` (`tests/macro_m0_harness.py:44-50`) gains the 7 names of `NAUTILUS_ORDER_VERBS`. They are
forbidden everywhere, the sandbox included. On today's 154-file tree they give 0 hits (map04 §3.2).

Rules added to `_offences`. Every new hit text starts with `[nautilus:<rule>]`, so a test can name the rule that
fired.

- **A. The one exemption.** In `NAUTILUS_SANDBOX` only, let k be the number of occurrences of `submit_order` in the
  lower-cased executable surface (`_code_only`), and m the number of `ast.Call` nodes whose `func` is
  `Attribute(attr="submit_order")` on `Name(id="self")`. When `k == m` and `m >= 1`, the `submit_order` text hit and
  the `.submit_order()` call hits on `self` are dropped. Otherwise every hit stands, and a hit tagged `A` is added. A
  call on any other receiver, a bare reference such as `f = self.submit_order`, or the text `submit_order_list`
  makes k exceed m.
- **B. Order verbs.** The 7 verbs are ordinary `FORBIDDEN_CALLS` entries, attribute or bare, in every file.
- **C. Imports, by full dotted name.** For `import a.b.c`, the name is `a.b.c`. For `from m import n`, the names are
  `m` and `m.n`. Relative imports resolve against the file's package.
  - C1, every file: a name equal to an entry of `NAUTILUS_DENIED`, or starting with that entry plus `.`, is an
    offence. An imported name (`alias.name`) in `NAUTILUS_DENIED_NAMES` is an offence.
  - C2, every file except the sandbox: a name equal to `nautilus_trader` or starting with `nautilus_trader.` is an
    offence.
  - C3, the sandbox only: an `import` statement naming `nautilus_trader` or below is an offence; a `from m import n`
    with m at or under `nautilus_trader` is allowed only if m is a key of `NAUTILUS_ALLOWED_FROM` and n is in its
    set, or m is `NAUTILUS_MODEL` or below; any other `import x` needs x in `SANDBOX_IMPORTS`, and any other
    `from m import n` needs m or `m.n` in it (so `from importlib import metadata` passes); a relative import is an
    offence.
  - The existing first-component check against `FORBIDDEN_IMPORTS` stays.
- **D. Identifiers.** In every file, an `ast.Name.id` or `ast.Attribute.attr` in `NAUTILUS_DENIED_NAMES` is an
  offence. None of these names occurs in today's scanned tree (grep, 2026-10-26).
- **E. String constants, on import machinery only (K4).** For every `ast.Call` whose callee (`Name.id` or
  `Attribute.attr`) is in `IMPORT_MACHINERY`:
  - every file: a string constant inside the call that equals or starts with a `NAUTILUS_DENIED` entry is an offence;
  - every file except the sandbox: a string constant inside the call that contains `nautilus` is an offence;
  - the sandbox: the call itself is an offence.
  String constants anywhere else are not checked. So the runner may name `nautilus_trader.adapters` in a
  `startswith` check, and the golden module lists, which are JSON, are never scanned.
- **F. Dynamic code in the sandbox.** In the sandbox, a call whose callee is a `Name` in `SANDBOX_DYNAMIC` or
  `SANDBOX_OS_CALLS`, or an `Attribute` in `SANDBOX_OS_CALLS`, is an offence.

New test, after `tests/macro_m0_harness.py:192`: `test_t_ro_01_nautilus_confined_to_the_sandbox`, with `test_ids =
["T-RO-01"]`. It builds a temp tree in the pattern of `test_t_ro_01_scan_reaches_tools_and_papers`
(`tests/macro_m0_harness.py:175-192`) and asserts the controls of section 8.5.

`tests/acceptance.py::runtime_py()` is not extended. `tools/` is outside test_08 and test_09
(`tests/acceptance.py:50-75`), which stay unchanged and must keep passing.

### 5.7 The `nautilus` suite in `tests/run_all.py`

- New module `tests/nautilus_acceptance.py` with `def tests() -> list[(name, fn)]`, as every suite has.
- `tests/run_all.py` imports it lazily, in the pattern of `papers_tests` (`tests/run_all.py:57-71`):

```python
def nautilus_tests():
    """Suite `nautilus` (tests/nautilus_acceptance.py), imported here: an import failure is one FAIL row and never
    stops the other suites. Its venv tests raise NotRun when QUANTGEN_NAUTILUS_PYTHON is not configured."""
    try:
        from tests.nautilus_acceptance import tests as nautilus_suite
    except Exception as exc:
        reason = f"tests.nautilus_acceptance does not import ({type(exc).__name__}: {exc})"

        def import_failed():
            raise RuntimeError(reason)
        return [("import", import_failed)]
    return nautilus_suite()
```
- `tests()` gains `[(f"nautilus/{n}", f) for n, f in nautilus_tests()]` last. The `--suite` help text
  (`tests/run_all.py:131`) gains `nautilus`. The file is CRLF: Edit tool only.
- Layer-1 tests always run. Layer-2 tests raise `NotRun("OWNER: Nautilus venv not configured
  (QUANTGEN_NAUTILUS_PYTHON)")` when the key is blank, and `NotRun("OWNER: QUANTGEN_NAUTILUS_PYTHON points to a
  missing file")` when the path does not exist.
- A configured venv with another `nautilus_trader`, `numpy`, `pandas` or Python minor version, or a wheel identity off
  its pin, is a FAIL, not NotRun (synth §4 default 5): a silent engine change would move results.

### 5.8 Registry rows and the file table

- `tests/macro_registry.csv:12` (T-RO-01): `implemented_in` gains
  `tests/macro_m0_harness.py::test_t_ro_01_nautilus_confined_to_the_sandbox`, written by `python -m
  tests.macro_acceptance` (`README.md:855`). `test_registry_implemented_in_matches_test_ids` fails until then
  (`tests/macro_m0_harness.py:286-295`).
- No other registry row changes. The `nautilus` suite's tests carry no `test_ids`, because the registry lists the
  council spec's test ids only.

| File | Change | Step |
|---|---|---|
| `requirements-nautilus.txt` | new, LF | 3 |
| `.env.example` | one heading and `QUANTGEN_NAUTILUS_PYTHON=` | 3 |
| `tools/nautilus/__init__.py` | new, empty | 3 |
| `tools/nautilus/sandbox.py` | new; the only order-placing file | 3 (`--check-env`), 5 |
| `tools/nautilus/runner.py` | new | 6 |
| `tools/nautilus/parity.py` | new | 7 |
| `tools/nautilus/golden/env_pins.json`, `modules_<tag>.json`, `F1.json`, `F2.json`, `N1.json` | new | 3, 5, 7A |
| `tests/macro_m0_harness.py` | constants, rules A-F, one test | 4 |
| `tests/macro_registry.csv` | T-RO-01 `implemented_in` resync | 4 |
| `tests/nautilus_acceptance.py` | new suite | 4 to 7 |
| `tests/run_all.py` | `nautilus_tests()`, `tests()`, `--suite` help (CRLF) | 4 |
| `docs/nautilus_bridge/registration/pilot1_E1_spy.json`, `pilot2_C3_btcusd.json` | new tables | 7A |
| `docs/nautilus_bridge/runs/`, `docs/nautilus_bridge/cards/` | outputs of record | 8, 9 |
| `README.md` | test table and suite help (`README.md:851-855, 864-878`) | 10 |

Unchanged on purpose: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`,
`core/quant/*.py`, `ui/strategy_lab_page.py`, `tests/acceptance.py`, `paper_live/`, `grokteam/`,
`docs/asset_expansion/`.

## 6. Data model

### 6.1 `input.json` (parent to child)

| Field | Type | Value |
|---|---|---|
| `schema` | str | `"nautilus-bridge-input/1"` |
| `leg` | str | `"parity"` or `"realism"` |
| `strategy` | str | `"trend_switch"` or `"crypto_trend"` |
| `params` | object | `{"rule", "lookback", "step"}` or `{"hysteresis", "lookbacks", "mas"}` |
| `instrument` | str | `"SPY"` or `"BTC/USD"` |
| `capital_usd` | str | `"1000000"` |
| `cost_bps` | str | table rate, for example `"50.0"` |
| `stress` | str | `"1"` or `"2"` |
| `fill` | str | `"same_close"` or `"next_close"` |
| `gap_buffer` | str | `"0"` or `"0.10"` |
| `fill_seed` | int | 42 |
| `price_precision` | int | 9 |
| `size_precision` | int | 0 (SPY) or 8 (BTC) |
| `volume` | str | `"1000000000"` |
| `n_bars` | int | rows of `bars.csv` |
| `bars_sha256` | str | SHA-256 of the bytes of `bars.csv` |

`bars.csv`: header `i,ts_ns,close`, LF, one row per bar, `close` with exactly 9 decimals.

### 6.2 `manifest.json` (child)

| Field | Type | Content |
|---|---|---|
| `schema` | str | `"nautilus-bridge-manifest/1"` |
| `read_only` | bool | `true` (map04 R22) |
| `mode` | str | `"run"` or `"check-env"` |
| `python` | str | `platform.python_version()` |
| `platform` | str | `sys.platform` |
| `versions` | object of str | `nautilus_trader`, `numpy`, `pandas`, `pyarrow`, `msgspec`, from `importlib.metadata` |
| `precision` | object | `HIGH_PRECISION` (bool), `FIXED_PRECISION` (int), `QUANTITY_MAX` (float), `PRICE_MAX` (float) |
| `wheel_identity` | object | `wheel_tag` (str, the `Tag:` line of `nautilus_trader-1.231.0.dist-info/WHEEL`), `record_digest_sha256` (str), `record_entries` (int), `direct_url_sha256` (str or null) |
| `env_keys` | list of str | sorted names of the child's environment variables, no values |
| `input` | object | `input_json_sha256`, `bars_sha256`, `bars_fed` (int), `first_ts`, `last_ts` (int ns) |
| `engine` | object | `run_analysis` (false), `log_level` ("ERROR"), `account_type` ("CASH"), `oms_type` ("NETTING"), `latency_ns` (int or null), `allow_cash_borrowing` (false), `bar_execution` (true), `fill_seed` (42) |
| `result` | object | `bars_seen` (int), `iterations` (int), `backtest_end` (int ns or null), `force_stop` (bool), `orders_total`, `orders_filled`, `denied`, `rejected`, `inflight_last_bar_exempt` (int), `orders_not_filled` (list of str ids), `account_balance_usd` (str), `final_qty` (str) |
| `hashes` | object | SHA-256 of `fills.csv`, `decisions.csv`, `onbar_equity.csv` |
| `sys_modules` | list of str | sorted `sys.modules` keys after `engine.run()` (after the imports, in `--check-env`) |
| `valid` | bool | the child's own verdict (5.2.7) |
| `invalid_reasons` | list of str | empty when valid |

No field holds a time of day. `wheel_identity` answers K7: pip writes `direct_url.json` only for a URL or file install,
not for `name==version` (`https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/specifications/direct-url.rst`,
lines 21-22). The record digest is the SHA-256 of the sorted lines `path,hash` of the installed `RECORD` rows under
`nautilus_trader/` that carry a hash. Those hashes come from the wheel itself. Measured in `scratch:ntvenv`
(manylinux, installed from the local wheel file): `0ad0bfc426d243f6334b0883b8a05e223199c6f6275359bbcd0c3cfa308407fb`
over 761 entries; `direct_url.json` there carries the wheel hash `429ea61c…ab91`. That the digest is the same for every
install method is UNVERIFIED; Step 3 installs the same wheel by name and by path and compares.

### 6.3 Run record (`docs/nautilus_bridge/runs/<bridge_run_id>.json`)

`bridge_run_id` = `NB-<YYYYMMDDTHHMMSSZ>-<first 8 hex of sha256(table bytes)>`. It sits outside every result hash.

| Field | Type | Content |
|---|---|---|
| `schema`, `read_only` | str, bool | `"nautilus-bridge-run/1"`, `true` |
| `bridge_run_id`, `mode`, `pilot` | str | id; `rehearsal` or `of-record`; `E1-SPY` or `C3-BTCUSD` |
| `status` | str | `CARD_WRITTEN`, `WITHHELD`, `REFUSED_REGISTRATION` or `ERROR` |
| `withheld_reasons` | list of str | the failed check ids and messages, or `"selection near-tie"`, or `"ledger moved after registration"` |
| `started_utc`, `registered_utc`, `first_child_utc`, `finished_utc` | str | ISO UTC; `registered_utc < first_child_utc` is the ordering evidence |
| `git` | object | `head` (40-hex), `anchor` (str), `clean` (bool), `porcelain_exempt` (list of str) |
| `table` | object | path, SHA-256, and the full table |
| `data` | object | `prices_file`, `prices_md5`, `rf_file`, `rf_md5` (or null), `start`, `end`, `sessions` (int) |
| `costs` | object | `cost_bps` (float), `floor_bp` (float), `classes` (object), `stress` (2.0), `source` (`"validate.cost_floor_bp"`) |
| `registration` | object | `family_id`, `ledger_path`, `hash_before`, `hash_after` (str), `n_raw_before`, `n_raw_after`, `market_n_raw` (int), `rows`: list of {`col` (int), `leg` (str), `run_kind` (str), `config_id` (str), `row_md5` (str, the row's own field), `appended` (bool)} |
| `engine` | object | the `--check-env` JSON |
| `children` | list | per child: `col`, `leg`, `stress`, `returncode`, `seconds`, `manifest` (with `sys_modules` replaced by its SHA-256), `fills` (all rows), `stdout_tail`, `stderr_tail` |
| `sys_modules` | object | platform tag to the one full sorted list (identical for every valid child) |
| `parity` | object | per column and cost level: P1 to P10, P13 values and pass flags; P11 per origin; P12 at 1x and 2x; `owner_bars` with the 98% / 0.99 / 0.05 results; `hard_pass` (bool); `failed` (list) |
| `gate` | object or null | `trial_counts` {`len_grid`, `family_n_raw`, `market_n_raw`, `n_trials`}, `decision`, `reason`, `revise_target`, `selection`, `exempt_origins`, and the second decision when an exempt flip was scored |
| `realism` | object or null | per column: corr, ΔSR against QUANTGEN same-close, ΔSR against QUANTGEN weights shifted one session, mean exposure, child validity; never read by the gate |
| `card` | object or null | `path`, `md5` |

Fills are kept in full. Daily returns are not stored: the reconstruction of 5.3.3 rebuilds them exactly from the fills,
the md5-pinned closes and the md5-pinned cash rate.

### 6.4 Ledger row fields used

| Field | Pilot value | In `config_id`? |
|---|---|---|
| `rule` | `"E1"` or `"C3"` (`ui/strategy_lab_page.py:50`) | yes |
| `params` | `json.loads(json.dumps(dict(theta, symbols=sorted(symbols), cost_bps=float(cost_bps)), default=str))`, the Lab's exact expression (`ui/strategy_lab_page.py:75-76`); realism rows add `"fill": "next_close"` and `"gap_buffer": 0.1` | yes |
| `timing_class` | `"COMPLIANT"` | yes |
| `estimator`, `window`, `cap`, `instrument_book`, `rebalance`, `start_convention` | not set (null), as the Lab | yes |
| `span` | `[first panel date, last panel date]` | no |
| `market` | `"US"` or `"CRYPTO"` (`ui/strategy_lab_page.py:52`) | no |
| `run_utc` | registration time, `%Y-%m-%dT%H:%M:%SZ` | no |
| `phase` | `"research"` | no |
| `script` | `"tools/nautilus/runner.py"` | no |
| `run_kind` | `"variant"` (parity) or `"timing_lag"` (realism) (`core/quant/gate_ledger.py:57-58`) | no |
| `run_utc_anchor` | `repo_anchor()` | no |
| `source` | `"nautilus-bridge <pilot> <leg>; engines quantgen.simulate + nautilus_trader 1.231.0; run <bridge_run_id>"` | no |
| `cost`, `results_md5`, `diff_series_ref`, `card_id`, `delta_sr` | not set | no |

- The key is `md5(canonical_json({rule, params, estimator, window, cap, instrument_book, rebalance, timing_class,
  start_convention}))` (`core/quant/gate_ledger.py:60-61, 168-171`). `canonical_json` writes floats by `repr`, so
  `50.0` and `50` hash differently (`core/ficc/macro_schema.py:303-305`; K9). `cost_bps` is therefore always a
  Python float.
- The engine tag goes in `source`, outside the key, so one variant is one trial whichever engine ran it. If the
  configuration already exists, `append` returns the first row and the new `source` is dropped
  (`core/quant/gate_ledger.py:343-346`). The run record keeps the per-engine detail, keyed by `config_id` and the
  row's `row_md5`.
- The 2x leg is never a row. It is the gate's stress column (`core/quant/strategies.py:387`).
- A new top-level field would be refused (`core/quant/gate_ledger.py:190-192`).

### 6.5 Card fields (`validate.ModelCard`, `core/quant/validate.py:802-834`)

| Field | Type | Bridge value |
|---|---|---|
| `card_id` | str | `NB_E1_trend_spy` or `NB_C3_crypto_trend_btcusd` |
| `kind` | str | `"strategy"` |
| `hypothesis` | str | from the table |
| `rules` | dict | `family`, `grid`, `cost_bps_per_side`, `embargo`, `engine` (`"nautilus_trader 1.231.0 BacktestEngine, same-bar close"`), `selection` (`"wf_nt"`, with exempt origins if any), `parity_bars` (`"corrected, spec 2026-10-26 §5.4"`) |
| `universe` | dict | `symbols`, `venue` (`"us"` or `"crypto"`) |
| `data` | dict | `sessions`, `start`, `end`, `source`, `prices_md5`, `rf_md5` |
| `costs` | dict | `cost_bps`, `stress_multiplier` (2.0) |
| `protocol` | dict | GATE's `w_is`, `w_oos`, `min_is`, `ci_level`, `bootstrap_B`, `block` |
| `trials` | dict | `N_planned`, `N_total` (= `n_trials`), `family_id`, `family_n_raw`, `market_n_raw`, `config_ids`, `row_md5s`, `ledger_hash_at_run`, `ledger` (free text) |
| `seed` | int | 11 |
| `stats` | dict | `asdict(StrategyScore)` minus `lines` and `regime`, plus `regime`, `chosen_last`, `bench_sharpe`, `walk_forward`, `parity` (summary), `manifest_sha256` (list) |
| `tests` | dict | `dsr`, `pbo`, `ci90`, `sr_stress` |
| `decision`, `decision_reason`, `revise_target` | str, str, str or null | from `score_strategy`; `decision` is always in `validate.DECISIONS` |
| `lines`, `citations` | list of str | from `score_strategy`; the study's citations |
| `results_file`, `results_md5` | str | the run record path and its md5 |
| `created`, `author` | str | defaults; `created` is a date and sits outside every hash |

## 7. Error handling

Every fail-closed condition, where it is caught and what is written. Runner exit codes: 0 card written (or a clean
rehearsal), 1 WITHHELD, 2 refused before registration, 3 refused at registration, 4 ERROR. A refusal before
registration writes nothing to the repository or any ledger. After registration, every outcome writes a run record,
because the rows exist and the record must explain them.

| # | Condition | Caught by | Written | Exit / status |
|---|---|---|---|---|
| R-01 | Dirty tree beyond the exempt output paths (of-record) | runner 5.3.2 step 2 | nothing | 2 |
| R-02 | Anchor UNVERSIONED, git missing, or anchor sha differs from HEAD | step 2 | nothing | 2 |
| R-03 | Venv unset, missing, or `--check-env` off its pins (versions, Python minor, wheel identity) | step 3 | nothing | 2 |
| R-04 | Price md5 differs from the table | step 4 | nothing | 2 |
| R-05 | Panel under 300 rows, unsorted or duplicated dates, or a date vector that differs between the two sides (N5) | step 4 | nothing | 2 |
| R-06 | DGS3MO missing, unreadable, off its md5, or NaN after forward fill | step 5 | nothing | 2 |
| R-07 | Uncosted symbol, or table cost below `cost_floor_bp` | step 6 | nothing | 2 |
| R-08 | `GATE["bootstrap_B"] != 2000` | step 7 | nothing | 2 |
| R-09 | Ledger chain broken | step 8 | nothing | 2 |
| R-10 | Rehearsal: ledger or output dir outside the temp dir, pilot-window SPY dates, or the real BTC-USD file | 5.3.1 | nothing | 2 |
| R-11 | Of-record: table without `owner_confirmed`, or grid differs from `grid_from(axes)` | step 1 | nothing | 2 |
| R-12 | `register_trial` raises | step 9 | run record with the rows appended so far | 3, `REFUSED_REGISTRATION` |
| C-01 | Forced stop | child | manifest `valid: false` | child 10; run INVALID |
| C-02 | Bars seen fewer than bars fed, or `backtest_end` before the last bar | child | same | 10 |
| C-03 | An order not FILLED (realism: except one submitted on the final bar) | child | same | 10 |
| C-04 | An order denied or rejected | child | same | 10 |
| C-05 | Input schema, SHA-256, volume above `QUANTITY_MAX`, or price precision above `FIXED_PRECISION` | child, before the engine | stderr only | 20 |
| C-06 | Non-zero exit, timeout (900 s), missing output, unparsable JSON | parent | child tails in the run record | run INVALID |
| C-07 | Manifest versions, precision or wheel identity differ from `--check-env` | parent | run record | run INVALID |
| C-08 | A module outside the platform baseline, or any `nautilus_trader.adapters` or `nautilus_trader.network` module | parent | run record, with the extra modules | run INVALID |
| C-09 | Reconciliation off by more than $0.01 per fill, or a parity-leg fill off a bar timestamp | parent | run record | run INVALID |
| C-10 | `env_keys` hold a name outside the launch-contract set; the interpreter's own `__PYVENV_LAUNCHER__` is tolerated (whether 3.13 sets it on Windows is UNVERIFIED) | parent | run record | run INVALID |
| C-11 | Bars fed differ from the parent's bars (SHA-256) | parent | run record | run INVALID |
| C-12 | `bar.ts_event` or `bar.close` differs from the input row | child | manifest `valid: false` | 10 |
| C-13 | An order in flight on a decision bar | child | manifest `valid: false` | 10 |
| G-01 | Any parity-leg run INVALID (P13), or any hard check P1 to P4, P11, P12 failing | parity | run record, no card | 1, `WITHHELD` |
| G-02 | Exempt selection flip with different decisions | 5.4.2 | run record, both decisions, no card | 1, `WITHHELD` ("selection near-tie") |
| G-03 | `walk_forward` or `score_strategy` raises (for example too few rows, `core/quant/validate.py:366-367`) | 5.5 | run record with the exception, no card | 1, `WITHHELD` |
| G-04 | `GATE` differs from its snapshot after scoring | 5.5 step 5 | run record, no card | 4, `ERROR` |
| G-05 | `assert_hash_at_run` raises: the ledger moved after registration | 5.5 step 6 | run record, no card | 1, `WITHHELD` |
| G-06 | An unexpected exception after registration | runner | run record with the traceback | 4, `ERROR` |
| Z-01 | A realism child INVALID | realism section | that column marked INVALID in `realism`; status unchanged | none |

Warnings P5 to P10 never withhold. They are listed in the run record and in the card's `stats.parity`.

## 8. Testing strategy

### 8.1 Two layers

- **Layer 1: the global interpreter, always run.** Pure Python and numpy. No `nautilus_trader`, no venv, no network,
  no cache file except where a test says so. These tests run in every suite run.
- **Layer 2: the venv, through the launch contract.** NotRun when `QUANTGEN_NAUTILUS_PYTHON` is unset or missing.
  FAIL on a version or identity mismatch. The global interpreter never imports `nautilus_trader`.
- Both layers live in `tests/nautilus_acceptance.py`. The scan test lives in `tests/macro_m0_harness.py`.
- Fixtures write their prices inline. Goldens are JSON in `tools/nautilus/golden/`.

### 8.2 Fixtures and golden values (map03 §6)

**F1, trend switch, 12 bars.** P = [97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97] on business days from
2001-01-02; `trend_switch(rule="sma", lookback=3, step=2)`; c = 50 bp; capital $1,005,001; CASH; buffer sizing;
`Equity`, 9 dp.

| t | P | SMA3 | decision | fill | cash after |
|---|---|---|---|---|---|
| 3 | 100 | 99.000 | on | BUY 10,000 @ 100.00, fee 5,000.00 | 1.00 |
| 5 | 96 | 100.000 | off | SELL 10,000 @ 96.00, fee 4,800.00 | 955,201.00 |
| 7 | 99 | 96.667 | on | BUY 9,600 @ 99.00, fee 4,752.00 | 49.00 |
| 9 | 103 | 101.000 | on (hold) | none | 49.00 |
| 11 | 97 | 99.333 | off | SELL 9,600 @ 97.00, fee 4,656.00 | 926,593.00 |

```
QUANTGEN pnl       0, 0, 0, +0.0350000, -0.0769231, -0.0050000, 0, +0.0152020, +0.0198020, -0.0485437, -0.0102041
QUANTGEN turnover  0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0          (the t = 11 sell is dropped, strategies.py:89-90)
Nautilus R         0, 0, 0, +0.0348258, -0.0769230, -0.0050000, 0, +0.0151256, +0.0198010, -0.0485413, -0.0102036
```

Assertions: fills exactly as the table; final cash 926,593.00 in the account and in the rebuild; every abs(R - pnl)
within the P10 bound (the largest is 1.74 bp at t = 3); P1 = 1; P4 holds once bar 11 is excluded.

**F2, crypto trend, 11 bars.** P = [50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800],
daily from 2021-01-01; `crypto_trend(lookbacks=(1, 2), mas=(2, 3), hysteresis=0.2)`, warm-up 3; c = 10 bp; capital
$53,053; `CurrencyPair`, 8 size decimals.

| t | P | votes (k1, k2, MA2, MA3) | mean | state | fill |
|---|---|---|---|---|---|
| 3 | 53,000 | + + + + | 1.00 | 1 | BUY 1.00000000 @ 53,000, fee 53.00, cash 0.00 |
| 4 | 52,600 | - + - + | 0.00 | 1 (hold) | none |
| 5 | 50,000 | - - - - | -1.00 | 0 | SELL 1.00000000 @ 50,000, fee 50.00, cash 49,950.00 |
| 7 | 50,500 | + + + + | 1.00 | 1 | BUY 0.98812079 @ 50,500, fee 49.90 |
| 9 | 51,000 | - + - - | -0.50 | 0 | SELL 0.98812079 @ 51,000, fee 50.39 |

```
QUANTGEN pnl  0, 0, 0, -0.0085472, -0.0494297, -0.0010000, 0, +0.0287030, -0.0192308, -0.0010000
Nautilus R    0, 0, 0, -0.0085386, -0.0494297, -0.0010000, 0, +0.0286743, -0.0192308, -0.0009999
final cash    50,343.77 (account) = 50,343.770395 (rebuild, before cent rounding)
```

Hand check: 49,950 / (50,500 x 1.001) = 0.9881207901, floored to 8 decimals 0.98812079.

**Negative fixtures.**

| ID | Setup | Expected outcome | Layer |
|---|---|---|---|
| N1 | F1 with volume 4,000 and 2 price decimals | 1,000 @ 100.00 then 9,000 @ 100.01; cash -89.45; the engine stops after 4 of 12 bars; child exit 10; run INVALID (C-01, C-02) | 2 |
| N2 | F1 inputs; QUANTGEN weights with one decision flipped | P1 < 1 and P4 fails; WITHHELD | 1 |
| N3 | F1 with `fill = next_close` (1 ns latency) | each fill one bar later; P1 (decisions) = 1; P4 fails; labelled timing, not parity | 2 |
| N4 | Two identical grid columns | P11 tolerates the tie; no false selection flag | 1 |
| N5 | Date vector with one missing row on one side | the runner refuses before registration (R-05) | 1 |
| N6 | Hand matrices with a planted near-tie (gap 0.0006) and the Nautilus side choosing the runner-up | P11 exempt; both scored; same decision: card notes the origin; a variant with different decisions: WITHHELD "selection near-tie" (K3) | 1 |
| N7 | Hand arrays where the "2x" column was charged at 1x | owner bars pass; corrected P3 fails | 1 |

The F1 and F2 goldens were verified with volume 1e12 in high precision. Step 5 re-verifies them at 1e9, and Step 7A
in standard precision.

### 8.3 Layer-1 tests (`tests/nautilus_acceptance.py`)

1. Return reconstruction on F1 and F2 from golden fills: R matches the values above to 1e-7.
2. Parity functions on N2, N4, N6 and N7; P10 bound on F1.
3. Runner ordering: a temp ledger and a stub child script (plain Python, written to the temp dir) that exits 1 unless
   its `config_id` is already in the ledger; the runner passes.
4. A broken chain in the temp ledger stops the runner before any child starts (R-09).
5. A second run of the same table appends 0 rows and records `appended: false` for every row.
6. Refusals R-01 and R-02 in a temp git repository (dirty file; detached `.git` file as in a worktree).
7. Refusals R-04 and R-06 with a doctored md5 and a missing DGS3MO copy; no 3% fallback (K8).
8. Refusal R-07 for an uncosted symbol (`"VOD.L"`) and for 40 bp on SPY (K15).
9. Refusal R-10 for a ledger dir outside the temp dir, a SPY date of 2004-12-01, and the name `yf_BTC-USD.csv`.
   The test never reads either real price file; it uses synthetic files with those names.
10. K9: the bridge row's `config_id` for SPY `sma/126/21` at 50.0 equals the one `ui.strategy_lab_page.register_trials`
    writes into another temp ledger; the same for BTC-USD `hysteresis 0.222` at 10.0 in C3.
11. `RegisterResult` handling: the run record's `row_md5` equals `row["row_md5"]` for an appended row and for a
    duplicate.
12. Module checks on doctored manifests: an extra module, and `nautilus_trader.adapters.binance`, each make the run
    INVALID (C-08).
13. A parity failure writes no card and exactly one WITHHELD record into a temp output dir.
14. `GATE` is deep-equal before and after a synthetic end-to-end scoring.
15. Encoding: every `open`, `read_text` and `write_text` call in `tools/nautilus/*.py` and
    `tests/nautilus_acceptance.py` passes `encoding=` (AST check; binary modes exempt) (K10).
16. The launch contract builds exactly the argv and environment of section 4.3 (checked on the built call, without
    starting a process).

### 8.4 Layer-2 tests

1. `--check-env`: pins match; `HIGH_PRECISION` and `FIXED_PRECISION` are reported; `env_keys` pass C-10.
2. F1 and F2 match their goldens: fills, commissions, final cash; manifest `engine.run_analysis` is false (K6).
3. N1 is INVALID after 4 of 12 bars; N3 fills one bar later.
4. Determinism: F1 and F2 each run in two separate processes and give the same `fills.csv` SHA-256.
5. Volume above `QUANTITY_MAX` gives exit 20 before the engine is built (K1).
6. The F1, F2 and N3 module lists are subsets of the platform baseline.
7. A synthetic end-to-end rehearsal: 1,500 seeded bars, a 4-column grid, temp ledger, temp outputs; a card is
   written whose decision is in `validate.DECISIONS`.

### 8.5 Scan controls (`test_t_ro_01_nautilus_confined_to_the_sandbox`)

All in a temp tree, scanned with `_offences(path, tmp)`:

| Control | Content | Expected rule tags |
|---|---|---|
| positive | `tools/nautilus/sandbox.py`: a `Strategy` subclass calling `self.submit_order(order)`, only allowed imports, `importlib.metadata.version("nautilus_trader")`, and `name.startswith("nautilus_trader.adapters")`, a denied string outside import machinery (K4) | no hit |
| live leak | `tools/nautilus/live_leak.py`: `from nautilus_trader.live.node import TradingNode`, `import nautilus_trader.adapters.binance`, `from nautilus_trader.core import nautilus_pyo3`, `node = TradingNode(cfg)`, `node.run()` | C1, C2, D |
| dynamic | `tools/nautilus/dynamic.py`: `importlib.import_module("nautilus_trader.adapters.betfair")` | E |
| outside import | `core/quant/nt_runner.py`: `from nautilus_trader.backtest.engine import BacktestEngine` | C2 |
| outside submit | `tools/nautilus/other_submit.py`: `s.submit_order(o)` | the existing text and call hits |
| verbs | a sandbox copy calling each of the 7 verbs on `self` | one call hit per verb, plus A for `submit_order_list` |
| sandbox receiver | sandbox copy with `other.submit_order(o)` | A |
| sandbox bare import | sandbox copy with `import nautilus_trader` | C3 |
| sandbox denied name | sandbox copy with `from nautilus_trader.config import TradingNodeConfig` | C1, C3 |
| sandbox socket | sandbox copy with `import socket` | C3 |
| sandbox dynamic | sandbox copy with `getattr(self, "sub" + "mit_order")(o)` and with `os.system("x")` | F |
| sandbox importlib | sandbox copy with `importlib.import_module("json")` | E |

Then: the real tree gives no hit (as `test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path` already asserts), and
the real `tools/nautilus/sandbox.py`, once it exists, gives no hit.

### 8.6 Running tests in the Linux container (K13)

- Never `python tests/run_all.py`, with or without `--suite`. `main` writes `OUT` on every run
  (`tests/run_all.py:128-137`).
- Suite checks, including every "reports NotRun" done-when, go only through the redirecting wrapper
  `scratch:run_baseline.py`, kept outside the repo. It imports `tests.run_all`, sets `R.OUT` to its first argument
  and calls `R.main` with the rest: `python3 -B <scratch>/run_baseline.py <scratch>/out.json --suite nautilus`.
- Single macro modules run with `python -m tests.<module>`, which prints only (map04 §7).
- After every check, `md5sum qa/acceptance_results.json` must equal its value before.
- The Linux full run has 8 environment FAILs (map04 §7). Only the Windows full run is the suite of record.

## 9. Steps and done-when

"Claude" means a session like this one. "Owner" means Geon Koh. Every Claude step runs on the feature branch, with
synthetic or pre-window data and temp ledgers only.

**Step 1. Spec.** Claude drafts; referees review; the owner approves.
- Done when: this file has a revision status; each referee report is saved in
  `docs/superpowers/specs/2026-10-26-review/round<k>_<name>.md`, or the owner's substitution is written in
  Appendix B; every issue has a ruling in Appendix B; the Status block carries the owner's approval line and the
  owner's answers to O1 to O13.

**Step 2. Plan and dry run.** Claude.
- What: `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge.md` in the house format: Global Constraints, a file
  table, RED/GREEN steps for Steps 3 to 7. Global Constraints include: no global `pip install`; never edit
  `paper_live/`, `grokteam/`, `docs/asset_expansion/cards/` or the gate-package harness sources; no pilot-window data;
  never `python tests/run_all.py` in the container (section 8.6); CRLF files with the Edit tool only; `encoding="utf-8"`
  on every open and `-X utf8` with an absolute script path (K10).
- Done when: the plan exists; in a scratch copy of the repo every layer-1 and layer-2 test of the plan is GREEN and
  T-RO-01 passes; in the real repo `git status` shows no change beyond the plan file and `qa/acceptance_results.json`
  has the same md5 as before.

**Step 3. Environment.** Claude on Linux; the owner's Windows half runs at Step 7A.
- What: `requirements-nautilus.txt` (5.1); `.env.example`; `tools/nautilus/__init__.py`; the `--check-env` mode of
  `sandbox.py`; `tools/nautilus/golden/env_pins.json` with the Linux identity.
- Done when: the file holds a hash for every distribution, for both platforms; `pip install --require-hashes
  --only-binary=:all: -r requirements-nautilus.txt` succeeds in a fresh scratch venv on Linux; `--check-env` there
  reports nautilus_trader 1.231.0, numpy 2.3.5, pandas 2.3.3, Python 3.13.x and `HIGH_PRECISION` true; the record
  digest of a by-name install equals that of a by-path install, or the difference is explained and the pin defined
  accordingly; the global interpreter still reports numpy 2.3.5, pandas 2.3.3, scipy 1.18.0 and no
  `nautilus_trader`; `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` are byte-identical.

**Step 4. Guard.** Claude, after ruling O2.
- What: section 5.6; the `nautilus` suite registration (5.7); the registry resync (5.8).
- Done when: the new test passes; every control of 8.5 fires exactly its listed rule tags; the real tree gives no hit;
  test_08 and test_09 are unchanged and pass; `python -m tests.macro_acceptance` has resynced row 12 and
  `test_registry_implemented_in_matches_test_ids` passes; through the wrapper, `--suite nautilus` reports its venv
  tests as NOT_RUN, not PASS, when `QUANTGEN_NAUTILUS_PYTHON` is unset.

**Step 5. Sandbox.** Claude.
- What: section 5.2 in full.
- Done when, in the Linux venv: F1 reproduces its golden fills, commissions and final cash 926,593.00 at volume 1e9;
  F2 reproduces 0.98812079 BTC and 50,343.77; N1 is INVALID after 4 of 12 bars; N3 fills one bar later; two separate
  processes give the same fills SHA-256 for F1 and for F2; the manifest shows `run_analysis` false and the precision
  fields; volume above `QUANTITY_MAX` exits 20; `modules_manylinux_2_35_x86_64.json` is the union of the F1, F2 and
  N3 lists; no code path uses `AT_THE_CLOSE`, `allow_cash_borrowing=True`, the `PortfolioAnalyzer` or a report as equity;
  the real sandbox gives no scan hit; layer-2 tests report NotRun when the venv is absent.

**Step 6. Runner.** Claude.
- What: section 5.3.
- Done when: layer-1 tests 1 and 3 to 12 of 8.3 pass; on F1 the rebuilt R matches map03 §6.2 to 1e-7; the run record
  carries the post-registration ledger hash, both data md5s, the wheel identity and every child manifest.

**Step 7. Parity and gate.** Claude.
- What: sections 5.4 and 5.5.
- Done when: layer-1 tests 2, 13 and 14 pass; layer-2 test 7 writes a card whose decision is in `validate.DECISIONS`;
  `GATE` is unchanged after the run; a rehearsal on SPY 1995-01-03 to 2004-11-30 with a temp ledger passes every hard
  check for all 12 columns at 1x and 2x, picks the same column at all 14 origins, and reports its worst correlation
  and worst abs ΔSR next to map 03's (0.99999901 and 0.0013). That rehearsal's verdict is not a result: it goes into
  the data-access history only.

**Step 7A. Hand-off (K2).** Claude, then the owner.
1. Claude asks the owner for approval to push. On approval, Claude pushes `claude/amazing-gauss-tdiguu`. No merge.
   Any commit Claude made on the branch leaves `qa/acceptance_results.json` byte-identical and says so in its message.
2. The owner pulls the branch into the main clone, not a worktree (a worktree gives UNVERSIONED rows,
   `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:85-87`).
3. The owner creates the venv (O9) and installs with `--require-hashes`.
4. `python -B -m tools.nautilus.runner --check-env`, then `--fixtures --record-baseline`.
5. The owner runs the full suite, `python tests/run_all.py`.
6. The owner fills `owner_confirmed` in both registration tables.
7. The owner commits the code, the golden files, the tables and the results file as one change group.
- Done when: on Windows, `--check-env` reports the pinned versions, `HIGH_PRECISION` false and `FIXED_PRECISION` 9;
  the win_amd64 identity and module baseline are recorded, and the baseline's diff against the Linux one shows only
  platform modules; F1, F2 and N1 run through the exact launch contract and match their goldens (K1), or the hand-off
  stops and no pilot runs; the import time of `BacktestEngine` and the time of 12 synthetic runs of 5,600 bars are
  recorded; the full run shows 0 FAIL with the `nautilus` layer-2 tests PASS; frozen_guard (a), (b) and (d) pass;
  `repo_anchor()` returns `git:<the new commit>`; `git status --porcelain` is empty.

**Step 8. Pilot 1.** The owner runs; Claude reads the outputs.
- What: `python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot1_E1_spy.json --mode
  of-record`, never while the suite runs.
- Done when: E1 holds the 12 parity and 12 realism `config_id`s, appended or already present and recorded; the run
  record shows `registered_utc` before `first_child_utc`; every hard parity check passes for all 12 columns at 1x and
  2x, or a WITHHELD record names the failing check; if parity passed, `docs/nautilus_bridge/cards/NB_E1_trend_spy.json`
  exists with the gate's decision, the three trial counts, the manifest hashes and the selection used; the realism
  delta sits only in the run record's `realism` section.

**Step 9. Pilot 2.** The owner; only if pilot 1 passed parity.
- Done when: the conditions of Step 8 hold for 5 columns at 10 and 20 bp, with no realism leg; the card
  `NB_C3_crypto_trend_btcusd.json` reports PBO for information only, and over-search uses the share of splits where
  the in-sample winner loses (`core/quant/validate.py:576`; map02 §2.5).

**Step 10. Close-out.** The owner runs; Claude writes the record.
- What: the full suite on Windows; the README test table and suite help (`README.md:851-855, 864-878`); the execution
  record `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md`, with every ruling made, each with
  what it costs if wrong, and the data-access history of section 10.4.
- Done when: the Windows full run shows 0 FAIL with the `nautilus` suite counted; `qa/acceptance_results.json` is
  committed from that run only; frozen_guard (a), (b) and (d) pass there; cards, run records and the execution record
  are committed; `git diff` against the Step 7A commit shows no change under `paper_live/`, `grokteam/`,
  `docs/asset_expansion/cards/` or the harness sources of `core/quant/gate_package.py:36-38`.

## 10. Pilots

Each table below becomes a committed JSON file in `docs/nautilus_bridge/registration/`. The owner confirms it at
Step 7A by filling `owner_confirmed`. Changing any key field after a run is a new trial.

### 10.1 Pilot 1: SPY trend switch (family E1)

| Item | Value | Source |
|---|---|---|
| Family, rule, market | `E1`, `"E1"`, `"US"` | `ui/strategy_lab_page.py:50`; `tests/paper_live_acceptance.py:333-343` |
| Price file | `docs/asset_expansion/cache/yf_SPY.csv`, md5 `d2164597d576e1b2fcadde063065811d` | map03 §1.1; re-checked in synth §9.2 |
| Price meaning | Yahoo close with `auto_adjust=True` (splits and dividends in the price) | `docs/asset_expansion_study.py:82-91` |
| Sample | panel rows from 2004-12-01 to the file's end (2026-09-25); span `["2004-12-01", "2026-09-25"]` | `docs/asset_expansion_study.py:724`; map03 §1.1 |
| Grid | `grid_from(rule=["sma", "tsmom"], lookback=[126, 210, 252], step=[21, 42])`, 12 columns, column = 6 x rule + 2 x lookback index + step index | `docs/asset_expansion_study.py:274`; map03 §1.2 |
| Params per row | `{"rule", "lookback", "step", "symbols": ["SPY"], "cost_bps": 50.0}` | section 6.4 |
| tsmom form | raw lookback return, rf = 0 in the signal | `core/quant/strategies.py:384` |
| Cash rate | DGS3MO / 100 / 252, forward-filled, `fred_DGS3MO.csv` md5 `661722143f24930a29b58c535d227c1b`, no fallback | K8 |
| Cost | 50 bp per side from `cost_floor_bp(["SPY"])`; stress 100 bp | `core/quant/validate.py:78, 115-121` |
| Embargo | 21 | `docs/asset_expansion_study.py:278` |
| Benchmark | SPY buy-and-hold, uncosted | `docs/asset_expansion_study.py:275` |
| Capital, account, instrument | $1,000,000; CASH, NETTING; `Equity`, whole shares, 9 dp; buffer sizing | section 5.2.3; map03 §2.7 |
| Gate | `GATE` unchanged: 756 / 126 / 504, B 2000, seed 11 | `core/quant/validate.py:53-74` |
| Trial count | `max(12, E1 N_raw after registration)`; three counts printed | O11 |
| Engine tag | in `source` | section 6.4 |
| Realism leg | 12 `timing_lag` rows, params plus `"fill": "next_close"`, `"gap_buffer": 0.1`; next close; reported only | O7 |
| Card | `NB_E1_trend_spy` | section 6.5 |
| Before registration | md5 pins, the date checks of R-05 and the 9-decimal rounding only; no signal, return or statistic is computed | section 3.9 |

From the row counts alone: 38 origins, the first OOS session at row 777, and 4,711 OOS sessions, about 18.7 years
(map02 §1.2; map03 §1.5). So the five-year rule is met by construction.

### 10.2 Pilot 2: BTC-USD crypto trend (family C3)

| Item | Value | Source |
|---|---|---|
| Family, rule, market | `C3`, `"C3"`, `"CRYPTO"` | `ui/strategy_lab_page.py:50-52` |
| Price file | `docs/asset_expansion/cache/yf_BTC-USD.csv`, md5 `bc76f530ff24ab445367fe826150bc10`; the whole file, 2014-09-17 to 2026-09-25, 7-day calendar | map03 §5.1; `docs/asset_expansion_study.py:731` |
| Grid | `grid_from(hysteresis=[0.0, 0.222, 0.444, 0.667, 0.889])`; study defaults for lookbacks and MAs; domain (0, 0.889) | `docs/asset_expansion_study.py:333, 339` |
| Params per row | `{"hysteresis", "symbols": ["BTC-USD"], "cost_bps": 10.0}` | section 6.4 |
| Cash rate | none | `docs/asset_expansion_study.py:335-343` |
| Cost | 10 bp per side from `cost_floor_bp(["BTC-USD"])`; stress 20 bp; flat, no weekend term | `core/quant/validate.py:78`; map03 §0 finding 14 |
| Embargo | 1 | `docs/asset_expansion_study.py:337` |
| Benchmark | BTC buy-and-hold, uncosted | `docs/asset_expansion_study.py:334` |
| Capital, account, instrument | $1,000,000 USD and 0 BTC; CASH with `base_currency=None`; spot `CurrencyPair` BTC/USD, 9 price and 8 size decimals; commission in USD | section 5.2.3 |
| Trial count | `max(11, C3 N_raw after registration)`; the stored card already counts 11; C3 also holds paper_live US and KR trend rows | `docs/asset_expansion_study.py:339-343`; K12 |
| Realism leg | none | O7 |
| Card | `NB_C3_crypto_trend_btcusd` | section 6.5 |
| Precondition | pilot 1 passed every hard parity check | synth §2.2 Step 9 |

With 5 columns, PBO is reported only (`core/quant/validate.py:68, 576`). On a 365-day calendar the five-year rule binds
before the 1,260-session rule (map03 §5.2).

### 10.3 Expected verdicts, stated before the run

**Pilot 1: a non-PASS verdict is expected.** This is a statement about the rule, made before any SPY number from the
pilot window exists. The reasons:
- The four-sleeve card `S_E1_trend_us` made 82 position changes in 19 years and failed the sample check, which needs
  100 (`docs/asset_expansion/results.md:9`; map02 §5.2). A single sleeve trades only on its own switch days. Fewer than
  100 trades fails the sample check; fewer than 30 gives INSUFFICIENT_DATA (`core/quant/validate.py:583, 586`).
- That card was rejected because it did not beat its benchmark (Sharpe difference -0.11, p 0.75). SPY alone is
  measured against SPY buy-and-hold.
- Its last pick sat on a lookback edge, so it failed the plateau test (map02 §2.5).
- UNVERIFIED: no SPY-only number exists, on purpose. The most likely outcomes are REJECT on the benchmark test, or
  REVISE on the sample check.

A REJECT, REVISE or INSUFFICIENT_DATA here is a finding about the rule, not a failure of the bridge. The bridge works if
parity holds. Changing the grid after seeing the result is a new trial and a new registration.

**Pilot 2.** The stored QUANTGEN card on the same file and the same five configurations is PASS: SR 1.19 [0.72, 1.64],
DSR 1.00, 144 trades, benchmark p 0.07 (`docs/asset_expansion/manifest.json:53`; map02 §5.3). If parity holds, the
Nautilus matrix is close to QUANTGEN's, so the expected verdict is PASS. Two things can change it, both stated now:
- The benchmark p of 0.07 sits near the 0.10 bar. Engine noise could move it across.
- `n_trials` may exceed 11 (O11), which lowers the DSR. The stored DSR is 1.00, so this is unlikely to bind.

A non-PASS in pilot 2 with parity passing would be a finding to investigate, not a reason to tune anything.

### 10.4 Data-access history

This list goes verbatim into each run record's table and into the execution record (map04 R23).

| When | Who | Data | What was computed | Ledger rows |
|---|---|---|---|---|
| 2026-09-27 and earlier | asset-expansion study | `yf_SPY.csv` 2004-12-01 to 2026-09-25, inside the four-sleeve book `S_E1_trend_us` | the 12-setting grid on SPY, QQQ, TLT and GLD at 1/4 each; REJECT | none from the study (`n_trials` typed by hand) |
| 2026-09-27 and earlier | asset-expansion study | `yf_BTC-USD.csv`, whole file | the same five hysteresis settings; PASS | none from the study |
| 2026-10-26 | map 03 probe | `yf_SPY.csv` 1995-01-03 to 2004-11-30 (2,497 sessions), `fred_DGS3MO.csv` | all 12 pilot-1 settings at 1x and 2x on both engines; walk-forward selection; Sharpe levels exist in `scratch:parity_probe/out/results_summary.json` | none; their `config_id`s equal pilot 1's, because `span` is not in the key (synth default 30) |
| 2026-10-26 | synthesis check | same pre-2004 window, `sma/210/21` | 109 single-block flips (synth §7.3) | none |
| 2026-10-26 | critic probe | map 03's saved pre-2004 matrices | walk-forward ties (K3) | none |
| 2026-10-26 | all maps | synthetic series only for crypto | no real BTC price was read | none |
| Step 7 | rehearsal | SPY 1995-01-03 to 2004-11-30 again, temp ledger | parity and a rehearsal gate run; not a result | temp only |

Claim labels, in the house protocol's terms
(`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:442-452`): pilot 1 is
*pre-specified on historical data*, on a series already used inside a four-sleeve book; pilot 2 is an engine
replication of a stored card. Neither is confirmatory.

## 11. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | The T-RO-01 amendment is drawn too wide and opens an order path. | One file; receiver `self`, counted; 7 verbs forbidden everywhere; full dotted names; denied identifiers; import-machinery strings; sandbox import allow-list and dynamic-call ban; 12 controls (8.5). |
| 2 | A live or adapter module is imported, statically or through `importlib`. | Rules C1 to E; the parent's module baseline and prefix check (5.2.7). |
| 3 | Rust adapter and network clients are loaded in every backtest (K5) and bypass Python patches. | No QUANTGEN code references them; the child has no credentials; the kernel refuses live configs in BACKTEST; Linux showed 0 socket calls (map04 §4.2). Windows: UNVERIFIED (O13). |
| 4 | Standard precision on Windows changes fills or breaks a run (K1). | Volume 1e9 with an assertion; precision assertion; F1, F2 and N1 on Windows at Step 7A before any pilot. |
| 5 | A global install with an eager upgrade moves numpy and pandas (map04 §5.2). | Requirements header; venv outside the repo; FAIL on mismatch; the suite never runs under the venv. |
| 6 | `.env` keys reach the child. | Explicit environment; `env_keys` checked in every manifest (C-10). |
| 7 | A forced stop or thin volume truncates a run that returns normally (map01 §4; map03 §4.2). | C-01 to C-03; buffer sizing; volume 2.5e8 at the close. |
| 8 | Someone reads `PortfolioAnalyzer` or the account report as equity. | `run_analysis=False`; returns rebuilt in the parent from fills. |
| 9 | The owner's original bars pass real bugs (5.4.3). | Corrected bars (O5); P4. |
| 10 | A walk-forward near-tie picks different columns (K3). | Selection-matched P12; P11 with the exemption; both scored on an exempt flip. |
| 11 | A convention mismatch looks like an engine error: adjusted closes, cash interest, the tsmom rate, index-based decision dates, the initial entry. | One shared rounded array; asserted bars; the study's conventions copied (5.2.5, 10.1). |
| 12 | Yahoo restates adjusted history, or the DGS3MO file changes. | md5 pins for prices and the cash rate; refusal on mismatch (R-04, R-06). |
| 13 | An unregistered look at a pilot window. | Rehearsal-mode refusals (R-10); registration before any child; data-access history. |
| 14 | Pilot rows anchor a commit without the code (K2). | Step 7A; R-01 and R-02. |
| 15 | Replica rows get a different `config_id` and add immutable trials (K9). | The Lab's exact params expression; layer-1 test 10. |
| 16 | The trial count is wrong: realism rows (K11a), other markets in C3 (K12). | Family-wide count, conservative; three counts printed and stored. |
| 17 | Pilot 1 ends non-PASS and is read as a bridge failure, or the grid is tuned after seeing it. | Expectation stated in 10.3; any change is a new registration. |
| 18 | API churn: 1.231.0 is the last 1.x release (map01 §10.4). | Exact pin with hashes; all Nautilus calls in one file; a v2 migration re-runs F1, F2 and the grid. |
| 19 | The realism leg overdraws cash on a gap (synth §6 risk 16). | 10% gap buffer, no borrowing; an overdraw makes that realism column INVALID and never touches the verdict. |
| 20 | The Linux `run_all.py` rewrites the results file with environment FAILs (K13). | Section 8.6. |
| 21 | A pilot writes the ledger while the suite runs. | Never concurrent (3.8). |
| 22 | LGPL-3.0 duties if QUANTGEN is ever conveyed; FSCMA questions if results are published. | The README forbids distribution (`README.md:924-929`). Publication needs an owner review. FSCMA is UNVERIFIED (map04 §8). |
| 23 | About 940 MB in the venv; OneDrive sync. | The venv lives outside OneDrive (O9). |

## 12. Out of scope

- Any Nautilus live surface: `TradingNode`, live clients, adapters (the `sandbox` adapter too), network clients. They
  belong to TRADEGEN (section 1).
- Multi-sleeve books, including `S_E1_trend_us`: `simulate`'s constant weights are a free daily rebalance (synth §8).
- A next-open realism leg; it needs an adjusted OHLC file that does not exist (map03 §2.6).
- Strategy Lab integration (O12); migration to NautilusTrader 2.x (O4); running a pilot as a `/quantgen-paper` study.
- `BacktestNode`, `ParquetDataCatalog`, streaming and Parquet, which is "never read"
  (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`).
- A `Cfd` stand-in for fractional SPY, MARGIN accounts, `allow_cash_borrowing=True`, a firewall rule or audit hook.
- Any change to the gate, its thresholds, the ledger code or the study.

## 13. Open questions

Only questions that the defaults of section 2 do not settle:

1. **Windows facts (Step 7A answers them).** Does the venv launcher run with the minimal environment? Are F1 and F2
   byte-identical in standard precision? What are the import and run times? All UNVERIFIED.
2. **Wheel identity (Step 3 answers it).** Is the `RECORD` digest the same for a by-name and a by-path install?
3. **A future gate-package freeze.** Should it hash the E1 and C3 ledgers? No caller passes them today (map02 §3.8).
4. **A pilot as a paper.** The paper rule "No new pip packages" (`.claude/workflows/quantgen-paper-write.js:37`) and
   `PACKAGES` in `tools/paper/study.py:30` would need their own ruling (map04 C7).
5. **The v1 backport end date.** RELEASES.md does not date the v2 cutover (map01 §10.4).
6. **Legal texts.** GPLv3 section 2 and FSCMA Art. 101 could not be fetched (map01 §10.1; map04 §8). They matter
   only before a publication.

## Appendix A: critic findings K1 to K15, and how this revision resolves them

| # | Finding (synth §10) | Resolution in this spec |
|---|---|---|
| K1 | The Windows wheel is standard precision; volume 1e12 raises there; nothing was measured in that mode. | Volume 1e9, asserted against `QUANTITY_MAX`; price precision asserted against `FIXED_PRECISION`; both recorded in the manifest (5.2.4, 6.2); F1, F2 and N1 on Windows through the launch contract before any pilot (Step 7A); cross-precision equality marked UNVERIFIED (3.6). |
| K2 | Pilots would run before the bridge code is committed, so rows would anchor a commit without it. | Step 7A inserted before the pilots; the runner refuses a dirty tree and an UNVERSIONED anchor and records HEAD (5.3.2 step 2, R-01, R-02); Step 10 commits only outputs. |
| K3 | P11's near-tie exemption and P12 contradict each other. | P12 uses QUANTGEN's `wf.chosen` on both matrices; P11 stays separate; an exempt flip scores both and requires the same decision, else WITHHELD "selection near-tie"; the card names the selection; fixture N6 (5.4.2, 8.2). |
| K4 | The string-constant rule fails the sandbox's own guard; `check_env.py` would import `nautilus_trader` outside the sandbox. | The string rule applies only to import-machinery calls (rule E); the module check moved to the parent, so the sandbox names no denied module; the version check is `sandbox.py --check-env`; the positive control includes a `startswith` check (5.6, 8.5). |
| K5 | Adapters are not "unimported": `BacktestEngine` loads `nautilus_pyo3` and 35 compiled submodules; the live tolerance needs a ruling. | O3 restated with the kernel's BACKTEST refusals; new ruling O13; full sorted `sys.modules` in every manifest, judged against per-platform golden baselines; "no network on Windows" stays UNVERIFIED (2, 5.2.7). |
| K6 | The engine runs the analyzer by default. | `BacktestEngineConfig(run_analysis=False)`, recorded in the manifest and asserted by layer-2 test 2 (5.2.3). |
| K7 | An installed venv may not reveal its wheel hash. | `wheel_identity` = wheel tag, `RECORD` digest (measured on Linux), and the `direct_url.json` hash when present; pinned per platform in `env_pins.json`; install-method stability checked in Step 3 (6.2). |
| K8 | The cash rate was not pinned and fell back silently to 3%. | DGS3MO md5 pinned in the table; missing, mismatched or NaN data refuses (R-06); no fallback (5.3.2 step 5). |
| K9 | Replica `config_id` equality was untested and type-sensitive. | The Lab's exact `params` expression with `float(cost_bps)`; layer-1 test 10 compares with `register_trials` in temp ledgers for E1 and C3 (6.4). |
| K10 | Windows encoding hazard; `-I` ignores `PYTHONUTF8`; a relative script path fails. | `-X utf8`; absolute script path; `encoding="utf-8"` everywhere, checked by layer-1 test 15; UTF-8 decoding of child output (3.7, 4.3). |
| K11 | (a) Realism rows count in the parity verdict's N. (b) A last-bar order is in flight under latency. | (a) Stated in O7 and accepted as conservative. (b) Exemption for an order submitted on the final bar, realism leg only (5.2.7, C-03). |
| K12 | Pilot 2's trial count mixes markets. | O11: family-wide count used, market-scoped count printed and stored (5.5 step 3). |
| K13 | `--suite` also rewrites the results file. | Only the redirecting wrapper in the container; md5 of the results file checked after every run (8.6). |
| K14 | The force-stop reset question is answerable. | Closed: `run` resets the flag (`nt:backtest/engine.pyx:1621-1622`); one process per run stays for the `random` reseed (5.2.7). |
| K15 | The runner never said where the cost comes from. | `validate.cost_floor_bp`; refuses an uncosted symbol and a lower rate (5.3.2 step 6, R-07). |

Further findings made while writing this revision:

| # | Finding | Resolution |
|---|---|---|
| A-1 | `RegisterResult.row_md5` has two meanings. For a fresh append it is the md5 of the stored line, chain fields included; for a duplicate it is the row's content hash (`core/quant/gate_ledger.py:217-218, 346, 355`). Synth Step 6 said "record `row_md5`" without saying which. | The bridge records `result.row["row_md5"]` in both cases (5.3.2 step 9); layer-1 test 11. |
| A-2 | The wrangler reads columns by position (map01 §2.4). Asserting the order guards one call site only. | Bars are built with the wrangler's own `Bar`, `Price` and `Quantity` calls, from strings, so no column order exists (5.2.4). |
| A-3 | `float(bar.close)` and the parent's float may differ in the last bit, which could flip a near-tie decision. | Decisions use the parent's floats; the child asserts exact `Price` equality on every bar (5.2.5, C-12). |
| A-4 | The study fills a leading DGS3MO gap with 0.03 in percent units, that is 0.03% a year, not 3% (`docs/asset_expansion_study.py:150`). | Irrelevant to the pilot window, but the bridge refuses any NaN instead of copying the fill (R-06). |
| A-5 | Synth's realism leg had no sizing rule that keeps the weight at or below 1.0 (map04 R15) without borrowing. | 10% gap buffer, no borrowing; Sharpe is nearly invariant to a constant exposure scale, and the record also reports the delta against QUANTGEN's weights shifted one session (O7, 6.3). |

## Appendix B: referee rounds

Round 1 reviews Revision 1. Each referee gets a secret-free bundle with this file and the five inputs, and runs with
the bundle as its working directory (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:505-531`).
A referee who returns nothing is REVIEW_INCOMPLETE, never "no objections", unless the owner records a substitution.

**Round 1 verdicts.**

| Referee | Channel | Verdict | Report | Date |
|---|---|---|---|---|
| Claude | subagent, disposable bundle | | | |
| GPT | Codex CLI (quota resets 2026-10-30 14:40) | | | |
| Gemini | `agy` on the owner's machine | | | |
| Owner-recorded substitute (if any) | | | | |

**Round 1 issues.**

| Issue | Raised by | Ruling |
|---|---|---|
| | | |
