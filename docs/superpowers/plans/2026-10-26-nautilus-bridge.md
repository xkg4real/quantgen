# NautilusTrader Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the research-only NautilusTrader bridge of the spec on the branch `claude/amazing-gauss-tdiguu`: a hash-pinned venv run only as a subprocess, the T-RO-01 amendment that confines simulated orders to one sandbox file, the sandbox child, the ledger-first runner, and the parity checks and gate hand-off that write a QUANTGEN card only when parity holds and both engines reach the same verdict. Everything is tested on synthetic data with temporary ledgers, and the branch ends ready for the owner's Windows hand-off (spec Step 7A).

**Architecture:** Two processes that share only files (spec 4.1). The parent, `tools/nautilus/runner.py`, runs in the global interpreter, imports QUANTGEN read-only, registers every variant in its family ledger before any child starts, computes QUANTGEN's reference matrices with `simulate`, and starts one child per (column, cost level) through the single launch contract of `tools/nautilus/launch.py` (minimal environment, `-I -B -X utf8`, `unshare -rn` on Linux, tree kill on timeout). The child, `tools/nautilus/sandbox.py`, runs in the pinned venv, builds a `BacktestEngine` whose kernel must be BACKTEST, places orders through one `self.submit_order` call, and writes fills, decisions, equity and a manifest into its temp dir. The parent rebuilds daily returns from the fills (spec 5.3.3), runs parity checks P0 to P13 (`tools/nautilus/parity.py`), applies QUANTGEN's walk-forward selection to both matrices, scores both with the unchanged gate, and writes a card only on parity and agreement. The suite `nautilus` (`tests/nautilus_acceptance.py`) runs layer 1 in the global interpreter and layer 2 through the venv.

**Tech Stack:** Python 3.13 global interpreter (numpy 2.3.5, pandas 2.3.3, scipy 1.18.0, frozen); NautilusTrader 1.231.0 in a separate hash-pinned venv (16 distributions, `requirements-nautilus.txt`); the standard library (`subprocess`, `ast`, `csv`, `json`, `hashlib`, `decimal`); Linux `unshare -rn` for egress control; QUANTGEN's `core.quant.strategies`, `core.quant.validate` and `core.quant.gate_ledger`, read-only; the house runner `tests/run_all.py` (no pytest).

Spec: docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md revision 6 (Claude debate closed; GPT and Gemini pending)

**Plan order:** Task 1 = spec Step 3 (Environment), Task 2 = Step 4 (Guard), Task 3 = Step 5 (Sandbox), Task 4 = Step 6 (Runner), Task 5 = Step 7 (Parity, gate, pilot tables, runbook). Each task starts after the previous task's commit. Step 1b (GPT, Gemini, the owner's approval), Step 7A (the Windows hand-off) and Steps 8 to 10 (pilots, close-out) belong to the owner and are outside this plan; Task 5 writes the runbook that Step 7A follows.

**Plan status:** written 2026-10-26 at HEAD `b7f991a`; spec revision 6 is in the working tree, not yet committed, and no task stages it. Owner approval (Step 1b) is not given: branch work proceeds on the section 2 defaults (GOVERNANCE-R2-1). The dry run of this plan's RED steps in a scratch clone (spec Step 2 done-when, QA-21) has not run yet.

---

## Global Constraints

### Spec section 3, verbatim (GOVERNANCE-13)

Citation keys inside the quoted text (`file:line`, `nt:`, `scratch:`, `map0N`, `synth`, `K<n>`, referee ids) are the spec's (its header); bare section numbers refer to the spec.

#### 3.1 Frozen pins

- The test interpreter keeps numpy 2.3.5, scipy 1.18.0 and pandas 2.3.3 while a readout is pending
  (`tests/frozen_guard.py:85-91`); there is no warn-only branch. The suite never runs under the venv interpreter, which
  has no scipy, so clause (d) would FAIL (`:91`). The venv pins the same numpy and pandas, so both share numerics.
- Nautilus is never installed into the global interpreter; an eager upgrade would move numpy to 2.5.4 and pandas to
  3.1.0 (map04 §5.2). A suite test fails while `nautilus_trader` is importable there; `pyarrow` there is reported,
  not failed, because other owner packages may bring it (OPS-5, GOVERNANCE-7; L1-22).

#### 3.2 Order path

- Exactly one file places simulated orders: `tools/nautilus/sandbox.py`, through one `self.submit_order` call in one
  method of a `Strategy` subclass (`nt:trading/strategy.pyx:805`; 5.6 rule A); the strategy refuses to start unless
  its kernel is BACKTEST (5.2.5). Orders fill against Nautilus's simulated exchange, as QUANTGEN's paper fills pass
  through `OrderBook.fill` (`core/engine/orders.py:90, 169, 253-257`).
- The sandbox never calls `submit_order_list` (`nt:trading/strategy.pyx:899`), `modify_order` (:1011), `cancel_order`
  (:1089), `cancel_orders` (:1134), `cancel_all_orders` (:1215), `close_position` (:1351), `close_all_positions`
  (:1418) or `market_exit` (:1750). No QUANTGEN file imports `nautilus_trader.live`, `.adapters`, `.network`,
  `.core.nautilus_pyo3` or `.backtest.node`.

#### 3.3 Hermeticity

- T-HERM-01 patches the parent only and cannot reach a child (`tests/macro_acceptance.py:52-98`; map04 §4.1). The
  child gets an explicit minimal environment, a fresh temp working directory, no `.env` key, no file logging, no
  catalog, no streaming and no database (4.3). `config.py` loads `.env` into the parent (`config.py:25-29`), so the
  parent never passes `os.environ` on. The sandbox opens only files in its temp dir, where the parent copies every
  input (5.2.8).
- Tests write ledgers only to temp dirs (`core/quant/gate_ledger.py:927-933`). Every `nautilus` suite test runs inside a
  guard that digests, before and after, `~/.nextgen/macro/ledgers`, the production ledger dir `config.macro_dir() /
  "ledgers"` resolved once when the suite starts (`.env` may move it; `config.py:176-178`), and the repo's
  `docs/nautilus_bridge/`, and fails on any change (QA-1, QA-R2-13; L1-32). Having resolved those paths, the guard
  sets `QUANTGEN_MACRO_DIR` to a fresh temp dir for each test and restores it in `finally`, so a default ledger path
  inside a test lands in a temp dir; `macro_dir()` reads the variable on every call (GOVERNANCE-R3-2).

#### 3.4 No-new-dependency shape

One new dependency file, `requirements-nautilus.txt`, installs into the venv only; `requirements.txt`,
`requirements-dev.txt` and `pyproject.toml` stay byte-identical, and QUANTGEN code never imports `nautilus_trader`.
`.env.example` gains a heading and one line with single quotes, forward slashes and no `%VAR%` (OPS-4):
`QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'`. In double quotes,
python-dotenv would turn the `\n` of `\ntvenv` into a newline.

#### 3.5 Determinism

One child process per (column, cost level), because `FillModel` reseeds Python's global `random`
(`nt:backtest/models/fill.pyx:75, 77`); `FillModel(random_seed=42)` always. No UUID, run id or wall-clock value enters
a result hash; fills are recorded without their UUID (5.2.6). The sandbox never iterates a set or dict of strings in an
order-dependent output (`-I` ignores `PYTHONHASHSEED`). Two processes on the same input give the same fills SHA-256
(map01 §6; the QA referee's F1 and F2 probe).

#### 3.6 Windows standard precision (K1)

The win_amd64 wheel is standard precision (`DEF HIGH_PRECISION = False` in its `core/rust/model.pxd:6`,
`scratch:critic_win/`); the Linux wheel is high precision (`nt:core/rust/model.pxd:6`). In standard mode
`FIXED_PRECISION` is 9 (`:18-20`), `QUANTITY_MAX` 18,446,744,073 (`:93-94`), `PRICE_MAX` and `MONEY_MAX` 9,223,372,036
(`:61-62, 77-78`), and `Quantity.__init__` raises above `QUANTITY_MAX` (`nt:model/objects.pyx:137-140`). The bridge
uses volume 1e9 and 9 price decimals, the standard-mode limit; the sandbox refuses more (exit 20). Every margin and
golden value was measured in high precision; cross-precision equality is UNVERIFIED until Step 7A.

#### 3.7 Encoding (K10, OPS-2, QA-16, OPS-11)

- The house locale is cp949 (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`). The child runs with
  `-X utf8`, because `-I` ignores `PYTHONUTF8`, and an absolute script path. At import, `tools/nautilus/runner.py`
  reconfigures `sys.stdout` and `sys.stderr` to UTF-8 with `errors="replace"`, as `tests/run_all.py:35-39` does.
- In `tools/nautilus/` and the new tests: every `open`, `read_text` and `write_text` passes `encoding="utf-8"`, and text
  writes pass `newline="\n"`; every text-mode `subprocess` call, `git` included, passes `encoding="utf-8",
  errors="replace"`; every `csv.writer` passes `lineterminator="\n"`, because it writes `"\r\n"` otherwise.
- The registration table, the only file the owner edits by hand, is read with `utf-8-sig`, so a BOM from Notepad or
  PowerShell 5.1 is tolerated. Every other file is read as plain `utf-8`.

#### 3.8 Never concurrent

- A pilot writes `~/.nextgen/macro/ledgers`, which T-HERM-02 snapshots while the suite runs
  (`tests/macro_acceptance.py:25-27, 101-138`): a pilot and a suite run never overlap
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:143-144`).
- A pilot never runs while a frozen-study readout runs (GOVERNANCE-9); the H2 readout registers rows into C3
  (`paper_live/replay.py:172`). paper_live defines no lock file at `6f7c610`, so the runner refuses while
  `<ledger dir>/C3.jsonl` or the table's family ledger was modified less than 600 seconds ago (R-16). One runner per
  table at a time, through a per-table OS lock (5.3.5; OPS-15).
- In the Linux container, `python tests/run_all.py` is never run, with or without `--suite`
  (`tests/run_all.py:128-137`; K13); 8.6 gives the only allowed form.

#### 3.9 Unseen pilot windows

- Pilot 1's window is SPY from 2004-12-01; pilot 2's is the whole BTC-USD cache. Neither is computed on before
  registration (map02 §0 finding 4; map04 R23). Every rehearsal Claude runs uses synthetic data only; map 03's
  pre-2004 SPY probe is cited (5.4.3) and recorded in 10.4, never repeated (GOVERNANCE-5).
- The runner refuses by place and by content (GOVERNANCE-4, QA-17, GOVERNANCE-R2-3, GOVERNANCE-R3-3; R-10). In rehearsal
  a prices file must lie inside the temp root, judged in `check_table` (5.3.2 step 1) before any file is opened
  (QA-R4-2), so no file of `docs/asset_expansion/cache/` is accepted or read, and a byte copy, whose md5 equals a pinned
  real file's (SPY or BTC-USD), is refused whatever its `end`; DGS3MO is allowed only as the cash series. A real-data
  rehearsal would need its own owner ruling and 10.4 row. Both modes apply `start` and `end` to each line's date text
  before any price value is parsed (5.3.2 step 5).
- The temp root (OPS-R4-4) is computed once per process in two forms, `normcase(realpath(gettempdir()))` and
  `normcase(realpath(dirname(d)))`, `d = mkdtemp()` being removed at once. A path, as `normcase(realpath)`, is inside it
  when it lies under either form and not under the repository, so a Store Python that redirects the temp dir (13.1)
  still passes, and the repository stays excluded.

#### 3.10 Ledger append-only

Ledgers are append-only and hash-chained; a duplicate `config_id` never replaces the first row
(`core/quant/gate_ledger.py:337-355`). Every variant is registered before its first engine run. Of-record mode needs
an existing, non-empty family ledger whose chain verifies, and never creates one (GOVERNANCE-3; R-15). No bridge code
edits `core/quant/gate_ledger.py` or another harness source (`core/quant/gate_package.py:36-38`); helpers live in
`tools/nautilus/`.

#### 3.11 Standing house rules

- Never edit `paper_live/` or `grokteam/`; never run their replay, grid, verdict, sameday or calibrate modules, or
  `grokteam.book`. `docs/asset_expansion/cards/` stays at 34 files and read-only (`tests/macro_m7_cards.py:833`).
- `tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml` and `config.py` are CRLF: edited only with the
  Edit tool and never renormalised (map04 R19). `config.py` is not edited.
- Bridge code contains no T-RO-01 text token; the case-sensitive `CANO` also matches identifiers such as `CANONICAL`
  (`tests/macro_m0_harness.py:35`).

#### 3.12 Egress control (SECURITY-1)

Every child runs without network (`unshare -rn` on Linux, a firewalled dedicated interpreter on Windows; 4.4), and
of-record mode needs a passing probe in the same run and a matching Step 7A record (R-14). The scan is one layer of three.

### Step 2 additions (spec section 9, row 2), verbatim

- Claude never runs of-record mode (GOVERNANCE-R2-4; 5.3.1) and writes ledger rows only under the system temp dir.
- No Claude commit includes `qa/acceptance_results.json` (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:30`).
- Claude reads no real BTC price and no SPY row on or after 2004-12-01.
- The pinned md5s come from this spec, and Claude never opens or hashes `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv` (GOVERNANCE-R3-3).
- Claude never writes or edits `owner_confirmed` or `host_fingerprint` in a committed table (`docs/nautilus_bridge/registration/`); tests write them only into tables under the system temp dir (GOVERNANCE-R3-5, GOVERNANCE-R4-3).
- No global `pip install`.

### Plan rules (the cloud container this plan runs in)

- **Repository and shell.** Linux cloud container; clone `/home/user/quantgen`, branch `claude/amazing-gauss-tdiguu`. The global interpreter is `python3` (`/usr/bin/python3`, Python 3.13.17): numpy 2.3.5, pandas 2.3.3, scipy 1.18.0, statsmodels 0.15.0, python-dotenv 1.2.3; no `nautilus-trader`, no `pyarrow`. The clone holds no `.env`. Every command runs from the repo root; the working directory does not persist between commands, so paths are absolute where it matters. Every command below uses two shell variables, set at the start of each command line:
  - `S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad`
  - `NTPY=$S/ntvenv_hash/bin/python`: the Nautilus venv built from the hashed closure (Python 3.13.17, `nautilus_trader` 1.231.0, numpy 2.3.5, pandas 2.3.3; `pyvenv.cfg` `include-system-site-packages = false`). The hashed requirements body is `$S/closure/requirements-nautilus.body.txt`; the local wheels are in `$S/closure/linux/` and `$S/closure/win/`. A later session sets `S` to its own scratchpad, copies `closure/` there, and rebuilds the venv with Task 1's install line.
- **House rules (binding).** Never edit `paper_live/` or `grokteam/`; never run their replay, grid, verdict, sameday or calibrate modules, or `grokteam.book`. Never `pip install` into the global interpreter: installs go only into fresh venvs under `$S`, offline from the local wheels (`--no-index --find-links`). Never open or hash `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv`; a test may name such a path (L1-9) but never reads it. Never write a ledger row outside a temp dir.
- **Suite runs (cloud wrapper rule).** Never run `python3 tests/run_all.py`, with or without `--suite`: its `main` rewrites `qa/acceptance_results.json`. Every suite run goes through the redirecting wrapper, kept outside the repo: `python3 -B $S/run_baseline.py $S/<name>.json [--suite <suite>]`. Before and after each run, `md5sum qa/acceptance_results.json` prints `16c9baa5a1777853521d485d5078e456`. Single modules print only: `python3 -B -m tests.macro_m0_harness`, and from Task 1 `python3 -B -m tests.nautilus_acceptance [-k <substring>]`. Layer-2 checks put `QUANTGEN_NAUTILUS_PYTHON="$NTPY"` on the command line; without it layer 2 is NOT_RUN. A full run takes about 10 minutes: start it in the background and wait; nothing else from QUANTGEN runs meanwhile (T-HERM-02; spec 3.8).
- **Commands that write into the repository.** `runner --egress-record` and `runner --handoff-report` write under `docs/nautilus_bridge/` and run only in a scratch clone (`git clone /home/user/quantgen $S/clone_<task>`), never in the real clone; their outputs are Step 7A's, on Windows. `runner --fixtures --write-goldens` and `--fixtures --record-baseline` run in the real clone only at the Task 4 steps that name them.
- **CRLF files.** `tests/run_all.py` and `README.md` are CRLF (so are `requirements.txt`, `pyproject.toml` and `config.py`, which this plan never edits). Edit them only with the Edit tool, never with a tool that rewrites newlines, and check the line ends after every edit: `python3 -c "b = open('tests/run_all.py', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'tests/run_all.py must stay CRLF'; print('CRLF ok')"` (the same with `README.md`). Never renormalise. Every new file is UTF-8 with LF line ends; `.env.example`, `.gitignore`, `tests/macro_m0_harness.py` and `tests/macro_registry.csv` are LF and stay LF.
- **Commits.** Each task ends with one commit on the branch. Stage named paths only (`git add <path> ...`), never `git add -A` or `git add .`; before committing, `git status --short` shows exactly the task's paths, plus any path that was already modified or untracked before the task began and that no task owns (at this writing the spec, ` M docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, and this plan, `?? docs/superpowers/plans/2026-10-26-nautilus-bridge.md`); a task never stages those. The message ends with exactly these two lines:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
  ```
  No task pushes. Never push a tag: `studies-of-record-2026-10-23` in this clone is a local-only stand-in (an annotated tag) that lets `tests/frozen_guard.py` pass; it is never pushed, moved or deleted.
- **Cloud baseline, before this plan (HEAD `b7f991a`).** The first cloud full run (2026-10-26 13:51) gave `738/870 passed, 8 failed, 124 not run`; seven of the FAILs were environment-only and are gone: `expansion/selfcheck_strategies`, `selfcheck_curve_models` and `selfcheck_crypto_analytics` (statsmodels missing), `guard/test_a`, `test_b` and `test_d` (the tag missing), `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache` (cache mtimes). With statsmodels installed, the stand-in tag and the cache mtimes backdated, the re-run made for this plan (`$S/baseline2_results.json`) gives `745/870 passed, 1 failed, 124 not run`. Its differences from the owner's Windows record (`qa/acceptance_results.json`: 749 PASS, 121 NOT_RUN of 870) are environment-only: `papers/test_debate_run_kills_process_tree` FAIL (no `taskkill`) and the three `papers/test_compile_*` NOT_RUN (no tectonic); everything else passes. A task's full run is correct when it equals its Count Ledger row and its one FAIL is that row. `python3 -B -m tests.macro_m0_harness` gives `12/12 passed, 0 failed, 0 not run`.
- **Bridge text.** No bridge file contains a T-RO-01 token (spec 3.11): no `submit_order` outside the one `place` method of `tools/nautilus/sandbox.py` (added at Task 3, after Task 2's amendment), no upper-case `CANO` (as in `CANONICAL`), no `KIS_ACCOUNT` or `ACNT_PRDT_CD`. Diagnostics in `sandbox.py` name no `NAUTILUS_DENIED_PREFIXES` or `NAUTILUS_DENIED_NAMES` entry (rule E). The new tests follow the same rule, although `tests/` is not scanned.
- **Tests.** No pytest. Every test is a zero-argument module-level `test_*` function of `tests/nautilus_acceptance.py` (or, for the two T-RO-01 tests, `tests/macro_m0_harness.py`); helpers never start with `test_`. A test that cannot run raises `tests.notrun.NotRun(reason)`. Test names are fixed by the Count Ledger; a task adds exactly its listed tests.
- **Task format.** Each task section has: verified-before-writing notes; **Files** (create, modify, test); **Interfaces** (consumes, produces, by the names of the Interface Contract below); then steps `- [ ] **Step N: ...**` with exact commands and exact expected output. Tests come first, verbatim, and are run to fail for the stated reason (RED); then the code, verbatim, and the run that passes (GREEN). Each task ends with its suite counts checked against the Count Ledger and a commit step that names every path and gives the message with both trailer lines.

## File Structure

| File | Task | Responsibility |
|---|---|---|
| `requirements-nautilus.txt` | 1 | New, LF. Spec 5.1's header verbatim, then `$S/closure/requirements-nautilus.body.txt` verbatim: 16 distributions with `==` and `--hash=sha256:` lines; the single source of the version pins. Installs only into the venv. |
| `.env.example` | 1 | Edit (LF): a heading and the line of spec 3.4, `QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'`. |
| `tools/nautilus/__init__.py` | 1 | Empty package marker. |
| `tools/nautilus/egress_probe.py` | 1 | The egress probe of spec 4.4: `json` and `socket` only. |
| `tools/nautilus/launch.py` | 1; 3 | The launch contract (4.3): argv and environment builder, `run_child`, tree kill, temp dirs, `unshare`; the venv reads and wheel identity (6.7); the census parser (5.2.7); `BridgeRefusal` and `ChildInvalid`. Task 3 adds `fixture_inputs` (QA-R3-1). |
| `tools/nautilus/sandbox.py` | 1; 3 | The child and the only order-placing file. Task 1: the import block of 5.2.9 verbatim, `inside`, `plain_mean`, both guards, `make_fee_model`, `build_engine`, `check_env`, `guard_selftest`, `main` (`run` refuses every input with exit 20). Task 3: section 5.2 in full in the structure of 5.2.9 (configs, ports, the one `self.submit_order`, `run`). |
| `tools/nautilus/golden/env_pins.json` | 1 | Both platforms' pins and wheel identities, computed offline (6.7). |
| `tests/fixtures/nautilus/MANIFEST.csv`, `tests/fixtures/nautilus/nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD`, `tests/fixtures/nautilus/nautilus_trader-1.231.0.win_amd64.RECORD` | 1 | Both wheels' `RECORD` files, md5-listed and read through `tests.notrun.require_fixture(name, manifest=...)` (6.7; QA-R2-14). |
| `docs/nautilus_bridge/.gitignore` | 1 | `runs/.locks/` (5.3.5). |
| `tests/nautilus_acceptance.py` | 1 to 5 | Suite `nautilus`: the guard of 3.3, the layer-2 gate, `tests()`, the print-only CLI; Task 1 creates it, every task adds its tests (Count Ledger), Task 4 adds the stub and rehearsal helpers. Spec 5.8 lists steps 4 to 7: the plan creates it at Task 1 so that Task 1 is test-first; it joins `tests/run_all.py` at Task 2, so the full-suite counts do not move at Task 1. |
| `tests/macro_m0_harness.py` | 2 | The constants of 5.6 after `ALLOWED_BARE_CALLS`, the 7 verbs in `FORBIDDEN_CALLS`, rules A to F in `_offences`, the two new T-RO-01 tests after `test_t_ro_01_scan_reaches_tools_and_papers`. |
| `tests/macro_registry.csv` | 2 | Row 12 (`T-RO-01`) `implemented_in`, rewritten by `python3 -B -m tests.macro_acceptance`; no other row changes. |
| `tests/run_all.py` | 2 | CRLF: `nautilus_tests()` (a copy of `papers_tests` for `tests.nautilus_acceptance`, an import failure one FAIL row `import`), the `nautilus/` term last in `tests()`, `nautilus` in the `--suite` help. |
| `README.md` | 2 | CRLF: `nautilus` in the `--suite` help line (`README.md:853`) and the row `\| nautilus \| tests/nautilus_acceptance.py \| <what it covers> \| counted at the Windows run of record \|` after the `papers` row; the Total row unchanged (C-4). |
| `tools/nautilus/runner.py` | 4; 5 | The parent (5.3): CLI, steps 0 to 15, the pure refusal functions, return reconstruction, the census judgement, `record_baseline`, `write_record`, the run lifecycle and the `parity_and_gate` seam. Task 5 fills the seam (steps 16 and 17) and adds `--fingerprint`, `--timing` and `--handoff-report`. |
| `tests/nautilus_stub_child.py` | 4 | The layer-1 stub child (8.1; QA-R2-2), standard library only. |
| `tools/nautilus/golden/F1.json`, `F2.json`, `N1.json` | 4 | Goldens (6.8), written by `runner --fixtures --write-goldens` on Linux. |
| `tools/nautilus/golden/modules_manylinux_2_35_x86_64.json` | 4 | The Linux census baseline, the union of the F1 and F2 censuses, written by `runner --fixtures --record-baseline`. |
| `tools/nautilus/parity.py` | 5 | Checks P0b to P13 (5.4.1), `cents`, `select_matched` (5.4.2), `gate_predicates`, `agree`, `reference_drift` (5.5), and `hand_off`, steps 16 and 17. |
| `docs/nautilus_bridge/registration/pilot1_E1_spy.json`, `docs/nautilus_bridge/registration/pilot2_C3_btcusd.json` | 5 | The two registration tables (6.6, 10.1, 10.2), without `owner_confirmed` and `host_fingerprint`. |
| `docs/nautilus_bridge/RUNBOOK_windows.md` | 5 | The Step 7A commands of spec section 9 in PowerShell, with the pinned 3.13 patch of the base interpreter (OPS-R4-5). |
| `docs/superpowers/plans/2026-10-26-nautilus-bridge.md` | (Step 2) | This plan. |

Unchanged on purpose (spec 5.8): `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`, `core/quant/*.py`, `ui/strategy_lab_page.py`, `tests/acceptance.py`, `paper_live/`, `grokteam/`, `docs/asset_expansion/` and `docs/asset_expansion_study.py`; also `qa/acceptance_results.json`, which no Claude commit includes. Step 7A creates `tools/nautilus/golden/modules_win_amd64.json`, `docs/nautilus_bridge/egress/win_amd64.json` and `docs/nautilus_bridge/handoff/win_amd64.json` on the owner's machine; no task creates them.

## Interface Contract

Everything below crosses a task boundary. A task that provides an item implements it with exactly this module path, name, signature, return type and file shape; a task that consumes it relies on nothing else. Where the spec fixes a value, the section is cited and the spec governs. "Task n" names the task that first provides the item.

### C1. Shared conventions (all tasks)

- **Section-7 ids.** Every refusal or invalid reason is a string that begins with its section-7 id and `": "`, such as `"R-03: venv python is not absolute: 'C:/x'"` or `"C-08: TP name added: foo"` (QA-R3-8).
- **Exceptions** (`tools/nautilus/launch.py`, Task 1):
  ```python
  class BridgeRefusal(Exception):
      """A refusal R-01 to R-17 of spec section 7. `str(exc)` is f"{rid}: {message}"."""
      def __init__(self, rid: str, message: str, remedy: str = "") -> None: ...
      rid: str          # "R-01" .. "R-17"
      message: str
      remedy: str       # section 7's Remedy text, printed by the runner after the message

  class ChildInvalid(Exception):
      """A child-level invalid condition C-01 to C-15. `str(exc)` is f"{cid}: {message}"."""
      def __init__(self, cid: str, message: str) -> None: ...
      cid: str          # "C-01" .. "C-15"
      message: str
  ```
  The sandbox has its own `Refused` (exit 20, spec 5.2.9); it never imports `launch`.
- **Encoding (3.7).** Every `open`, `read_text` and `write_text` in `tools/nautilus/` and the new tests passes `encoding="utf-8"` (the registration table `utf-8-sig`), text writes pass `newline="\n"`, text-mode `subprocess` calls pass `encoding="utf-8", errors="replace"`, every `csv.writer` passes `lineterminator="\n"`.
- **JSON bytes.** `input.json` is `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`, no trailing newline, so the runner, `fixture_inputs` and the stub give identical bytes for identical objects. Every other JSON file the bridge writes is `json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"`, except the card (`ModelCard.to_json()`, 5.5 step 8).
- **Platform tags.** The wheel platform tag (`manylinux_2_35_x86_64`, `win_amd64`; the platform part of the `Tag:` line of `WHEEL`) keys `env_pins.json` and names the census baselines `modules_<wheel platform tag>.json`. The host tag, `launch.host_tag()` = `sysconfig.get_platform()` with `-` and `.` replaced by `_` (`linux_x86_64`, `win_amd64`), names `docs/nautilus_bridge/egress/<host tag>.json` and `docs/nautilus_bridge/handoff/<host tag>.json` (OPS-R3-4).
- **Version maps** are compared after PEP 503 normalisation of their keys (`re.sub(r"[-_.]+", "-", name).lower()`), so 6.7's `nautilus_trader` and 5.1's `nautilus-trader` are the same key.

### C2. `tools/nautilus/launch.py` (Task 1; `fixture_inputs` Task 3)

Constants:
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
SANDBOX = REPO_ROOT / "tools" / "nautilus" / "sandbox.py"
EGRESS_PROBE = REPO_ROOT / "tools" / "nautilus" / "egress_probe.py"
REQUIREMENTS = REPO_ROOT / "requirements-nautilus.txt"
GOLDEN_DIR = REPO_ROOT / "tools" / "nautilus" / "golden"
ENV_PINS = GOLDEN_DIR / "env_pins.json"
KEY = "QUANTGEN_NAUTILUS_PYTHON"
TIMEOUT_S = 900            # communicate(timeout=900), spec 4.3
DRAIN_S = 30               # communicate(timeout=30) after a kill
TAIL_CHARS = 4000          # stdout/stderr tails kept in the run record
ENV_KEYS = {"nt": frozenset({"SYSTEMROOT", "PATH", "USERPROFILE", "HOME", "TEMP", "TMP"}),
            "posix": frozenset({"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL"})}
FIXTURES = ("F1", "F1r", "F2", "N1")          # Task 3
```

Venv reads and identity (6.7):
```python
def venv_key() -> str
    # `import config` (which loads .env), then config._clean(KEY); "" when blank.
def resolve_venv_python(value: str) -> Path
    # os.path.expanduser(os.path.expandvars(value)); refuses a control character (code < 32 or 127), a relative
    # path, a missing file, a name other than python.exe or python: BridgeRefusal("R-03", ...) naming repr(value)
    # and the fix. Returns the path as given after expansion (not its realpath).
def venv_root(python: Path) -> Path                      # the parent of Scripts (nt) or bin (posix)
def expected_versions(path: Path = REQUIREMENTS) -> dict[str, str]
    # {"nautilus-trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"} read from the file's `==` pins (5.1)
def record_identity(record_text: str) -> tuple[str, int]
    # (record_digest_sha256, record_entries) by 6.7's rule: csv.reader; keep rows with a non-empty hash, no
    # __pycache__, a path not ending /RECORD, /INSTALLER, /REQUESTED or /direct_url.json; f"{path},{hash}"; sorted;
    # "\n".join, no trailing newline; UTF-8; sha256 hex
def read_venv(python: Path, *, os_name: str = os.name, parent_base_executable: str = sys._base_executable) -> dict
    # Refuses (R-03) include-system-site-packages = true; on nt an `executable` equal to parent_base_executable, or a
    # `home` or `executable` under WindowsApps or \Packages\PythonSoftwareFoundation. (OPS-R2-2); paths compared as
    # os.path.normcase(os.path.realpath(p)). Returns:
    # {"python": str, "python_norm": str, "root": str,
    #  "pyvenv": {"home": str, "version": str, "executable": str | None, "include_system_site_packages": bool},
    #  "python_minor": "3.13",                                   # from pyvenv.cfg `version`
    #  "installed": {pep503 name: version, ...},                 # every *.dist-info/METADATA `Version:`
    #  "versions": {"nautilus-trader": str, "numpy": str, "pandas": str},
    #  "wheel": {"wheel_tag": str, "platform_tag": str, "record_digest_sha256": str, "record_entries": int}}
def load_env_pins(path: Path = ENV_PINS) -> dict
def venv_mismatches(reads: dict, pins: dict | None = None, expected: dict | None = None) -> list[str]
    # [] on a match; else one "R-03: <field>: found <x>, expected <y>" per difference: python_minor, the three
    # versions against expected_versions() and env_pins, wheel_tag, record_digest_sha256, record_entries; an unknown
    # platform tag is a mismatch
def parent_nautilus() -> str | None                      # importlib.metadata.distribution("nautilus-trader") version
def parent_pyarrow() -> str | None
def host_tag() -> str                                     # C1
```

Launch contract (4.3):
```python
@dataclass(frozen=True)
class Launch:
    argv: list[str]
    env: dict[str, str]
    cwd: str
    popen_kwargs: dict        # stdin=DEVNULL, stdout=PIPE, stderr=PIPE, text=True, encoding="utf-8",
                              # errors="replace", and start_new_session=True (posix) or
                              # creationflags=subprocess.CREATE_NEW_PROCESS_GROUP (nt)

@dataclass(frozen=True)
class ChildResult:
    argv: list[str]
    returncode: int | None    # None only when the process could not be waited for
    ntstatus: str | None      # nt: f"0x{code:08X}" when code >= 0xC0000000, else None
    timed_out: bool           # True: the tree was killed after `timeout` (C-06)
    seconds: float
    stdout: str
    stderr: str
    census: list[str]         # parse_census(stderr)[0]; [] without -X importtime
    stdout_tail: str          # last TAIL_CHARS characters
    stderr_tail: str          # last TAIL_CHARS characters of stderr with the `import time:` lines removed

def make_tempdir() -> Path
    # Path(os.path.realpath(tempfile.mkdtemp(prefix="qgnb_"))), with <dir>/home and <dir>/tmp created
def resolve_unshare(os_name: str = os.name) -> str | None
    # nt: None. posix: shutil.which("unshare"), and `unshare -rn true` must exit 0, else BridgeRefusal("R-14", ...)
def assert_env_contract(env: Mapping[str, str], os_name: str) -> None
    # ChildInvalid("C-10", ...) unless set(env) == ENV_KEYS["nt" if os_name == "nt" else "posix"]
def build_launch(mode_args: Sequence[str], *, tempdir: Path, venv_python: Path | None, os_name: str = os.name,
                 unshare: str | None = None, child_cmd: Sequence[str] | None = None, script: Path = SANDBOX,
                 environ: Mapping[str, str] = os.environ) -> Launch
    # argv: [unshare, "-rn"] on posix (unshare required there), then either
    #   [venv_python, "-I", "-B", "-X", "utf8", *(["-X", "importtime"] if importtime), str(script)]
    #   or, with child_cmd, list(child_cmd) (its first item absolute) in place of those items;
    # then mode_args. importtime is on only when script is SANDBOX, mode_args[0] == "run" and child_cmd is None.
    # mode_args: ["--check-env"], ["--guard-selftest"], ["run", "--in", str(tempdir)]; the probe: script=EGRESS_PROBE,
    # mode_args=[]. The <venv bin dir> of PATH is dirname(child_cmd[0]) with child_cmd, else dirname(venv_python).
    # env exactly as 4.3's rows (nt: SYSTEMROOT copied from environ, PATH = <bin dir>;<SYSTEMROOT>\System32,
    # USERPROFILE and HOME = <tempdir>\home, TEMP and TMP = <tempdir>\tmp; posix: PATH = <bin dir>:/usr/bin:/bin,
    # HOME = <tempdir>/home, TMPDIR = <tempdir>/tmp, LANG and LC_ALL = C.UTF-8); calls assert_env_contract.
    # cwd = str(tempdir). Starts no process.
def run_child(launch: Launch, *, timeout: float = TIMEOUT_S, on_started: Callable[[], None] | None = None,
              os_name: str = os.name) -> ChildResult
    # Popen(launch.argv, cwd=launch.cwd, env=launch.env, **launch.popen_kwargs); on_started() after Popen and before
    # communicate; communicate(timeout); on expiry kill_tree, communicate(timeout=DRAIN_S), timed_out=True; everything
    # from Popen to the end of communicate in try/except BaseException, which kills the tree, drains and re-raises
    # (OPS-R2-4). Never deletes the temp dir.
def kill_tree(proc: subprocess.Popen, os_name: str = os.name) -> None
    # nt: ["taskkill", "/T", "/F", "/PID", str(proc.pid)]; posix: os.killpg(proc.pid, signal.SIGKILL)
def parse_census(stderr: str) -> tuple[list[str], str]
    # (sorted unique names: third `|` field, stripped, of every line starting "import time:", the header field
    # "imported package" skipped; the stderr with those lines removed)
def cleanup_tempdir(tempdir: Path) -> list[str]
    # shutil.rmtree(tempdir, onexc=...), up to 3 attempts 0.5 s apart; returns the paths still present; never raises
def fixture_inputs(name: str) -> tuple[bytes, bytes]                                   # Task 3
    # (input.json bytes, bars.csv bytes) for name in FIXTURES, from spec 8.2 and 6.1, ledger_hash_after_registration
    # = core.quant.gate_ledger.ledger_hash([]); F1r's child inputs are F1's (F1r differs only in the parent's rf,
    # 0.0001 per session); N1 is F1 with volume "4000" and 2 price decimals; raises KeyError for another name
```

### C3. `tools/nautilus/sandbox.py` command line and files (Task 1 for the two self-checks; Task 3 for `run`)

- **argv** as `build_launch` builds it; `<venv python> -I -B -X utf8 [-X importtime] <abs sandbox.py> <mode>`.
- **`--check-env`**: one JSON line on stdout, no file, exit 0:
  `{"schema": "nautilus-bridge-check-env/1", "python": str, "system": str, "machine": str, "environment": str, "precision": {"HIGH_PRECISION": bool, "FIXED_PRECISION": int, "QUANTITY_MAX": float, "PRICE_MAX": float}}`. Measured on Linux: `HIGH_PRECISION` true, `FIXED_PRECISION` 16, `QUANTITY_MAX` 34028236692093.0, `PRICE_MAX` 17014118346046.0, `environment` `"BACKTEST"`.
- **`--guard-selftest`**: one line `json.dumps(out, sort_keys=True)`, exit 0 exactly when it is `{"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}`, else exit 30.
- **`run --in <dir>`**: `<dir>` absolute and equal to its own `Path.resolve()`, else exit 20. Task 1's `run` refuses every input with exit 20; Task 3 implements it. Exit codes (5.2.1): 0 valid; 10 complete but invalid (`manifest.json` written with `valid: false`); 20 input refused before the engine is built; 30 a self-test case misbehaved; any other value a crash.
- **Inputs** in `<dir>`: `input.json` (C5) and `bars.csv` (header `i,ts_ns,close`, LF, one row per bar, `i` from 0, `ts_ns` strictly increasing, `close` above zero with exactly `price_precision` decimals).
- **Outputs** in `<dir>` (5.2.6; UTF-8, LF):
  - `fills.csv`, header `ts_event,order_side,last_qty,last_px,commission,commission_ccy,trade_id,venue_order_id`;
  - `decisions.csv`, header `i,ts_event,decision,margin,action` (`action` in `buy`, `sell`, `hold`, `skip_zero_qty`);
  - `onbar_equity.csv`, header `i,ts_event,close,cash,qty,equity_pre`;
  - `manifest.json` (C6).

### C4. `tools/nautilus/egress_probe.py` (Task 1)

`<venv python> -I -B -X utf8 <abs egress_probe.py>` through `build_launch(script=EGRESS_PROBE, mode_args=[])`. Imports `json` and `socket` only. `socket.create_connection(("1.1.1.1", 443), timeout=3)`; prints one line `{"blocked": bool, "errno": int | null, "error": str}`; exit 0 when the connect failed, 1 when it connected (closed at once).

### C5. `input.json` (spec 6.1; written by the runner at Task 4 and by `fixture_inputs` at Task 3)

Exactly these 14 keys, no other: `schema` (`"nautilus-bridge-input/2"`), `strategy` (`"trend_switch"` or `"crypto_trend"`), `params` (trend: `{"rule", "lookback", "step"}`; crypto: `{"hysteresis", "lookbacks", "mas"}`, the study defaults `[7, 14, 21, 28]` and `[10, 20, 50, 100, 200]` filled in by the runner when the grid names only `hysteresis`), `instrument` (`"SPY"` or `"BTC/USD"`), `capital_usd` (str), `cost_bps` (str), `stress` (`"1"` or `"2"`), `fill_seed` (int), `price_precision` (int), `size_precision` (int), `volume` (str), `n_bars` (int), `bars_sha256` (64 lower-case hex), `ledger_hash_after_registration` (32 lower-case hex). Ranges as 6.1.

### C6. `manifest.json` (spec 6.2; written by the sandbox at Task 3 and the stub at Task 4)

```
{"schema": "nautilus-bridge-manifest/2", "read_only": true, "mode": "run",
 "python": str, "system": str, "machine": str,
 "precision": {"HIGH_PRECISION": bool, "FIXED_PRECISION": int, "QUANTITY_MAX": float, "PRICE_MAX": float},
 "environment": str, "strategy_started": bool,
 "input": {"input_json_sha256": str, "bars_sha256": str, "bars_fed": int, "first_ts": int, "last_ts": int,
           "cost_bps": str, "stress": str, "ledger_hash_after_registration": str},
 "engine": {"run_analysis": false, "log_level": "ERROR", "log_colors": false, "account_type": "CASH",
            "oms_type": "NETTING", "allow_cash_borrowing": false, "bar_execution": true, "fill_seed": int},
 "result": {"bars_seen": int, "iterations": int, "backtest_end": int | null, "force_stop": bool,
            "orders_total": int, "orders_filled": int, "denied": int, "rejected": int,
            "orders_not_filled": [str], "account_balance_usd": str, "final_qty": str, "stats_pnls_empty": bool},
 "hashes": {"fills.csv": str, "decisions.csv": str, "onbar_equity.csv": str},
 "valid": bool, "invalid_reasons": [str]}
```
`engine.fill_seed` echoes the input's `fill_seed` (42 in every runner and fixture input). No field holds a time of day.

### C7. Golden and fixture files

- `tools/nautilus/golden/env_pins.json` (Task 1):
  ```
  {"schema": "nautilus-bridge-env-pins/1",
   "platforms": {"manylinux_2_35_x86_64": {"python_minor": "3.13",
                                           "versions": {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"},
                                           "wheel_tag": "cp313-cp313-manylinux_2_35_x86_64",
                                           "record_digest_sha256": "a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9",
                                           "record_entries": 764},
                 "win_amd64": {"python_minor": "3.13",
                               "versions": {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"},
                               "wheel_tag": "cp313-cp313-win_amd64",
                               "record_digest_sha256": "47d274d79b85a43b79917e9b993fa3e68ebf68138c4a8b86527c5902cf439555",
                               "record_entries": 764}}}
  ```
  Measured for this plan from the `WHEEL` and `RECORD` inside both wheel files of `$S/closure/` (the Linux digest also from `$NTPY`'s installed `RECORD`): `Tag: cp313-cp313-win_amd64`, `47d274d7...`, 764 entries; `Tag: cp313-cp313-manylinux_2_35_x86_64`, `a448cd20...`, 764 entries.
- `tests/fixtures/nautilus/` (Task 1): `nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD` and `nautilus_trader-1.231.0.win_amd64.RECORD`, each the wheel's own `nautilus_trader-1.231.0.dist-info/RECORD` bytes, and `MANIFEST.csv` with the header of `tests.notrun.MANIFEST_COLUMNS` and one row per file (md5, licence `LGPL-3.0`, owner, tests). Read only through `require_fixture(name, manifest=ROOT / "tests" / "fixtures" / "nautilus" / "MANIFEST.csv")`.
- `tools/nautilus/golden/F1.json`, `F2.json`, `N1.json` (Task 4): `{"schema": "nautilus-bridge-golden/1", "fixture", "status" ("valid" or "invalid"), "exit_code", "bars_fed", "bars_seen", "force_stop", "fills": [{"date", "side", "qty", "price", "commission"}], "final_cash", "final_qty", "invalid_reasons"}`, compared as 6.8 says.
- `tools/nautilus/golden/modules_<wheel platform tag>.json` (Task 4 for Linux): `{"schema": "nautilus-bridge-census/1", "platform_tag", "python", "recorded_from": ["F1", "F2"], "census": [sorted names]}`.

### C8. `tests/nautilus_acceptance.py` (Task 1 skeleton; helpers added at Task 4)

Task 1:
```python
ROOT = Path(__file__).resolve().parents[1]
FIXTURE_MANIFEST = ROOT / "tests" / "fixtures" / "nautilus" / "MANIFEST.csv"
LAST_TEST = "test_l1_32_every_test_guarded_and_ledgers_unchanged"
def guard_roots() -> tuple[Path, ...]
    # resolved once per process, at the first call: Path.home() / ".nextgen" / "macro" / "ledgers",
    # config.macro_dir() / "ledgers", ROOT / "docs" / "nautilus_bridge" (spec 3.3)
def digest_roots(roots: Sequence[Path]) -> dict[str, str]          # {path: md5 of bytes} of every file; {} if absent
def guarded(name: str, fn: Callable[[], None]) -> Callable[[], None]
    # digests before; QUANTGEN_MACRO_DIR = a fresh tempfile.mkdtemp(prefix="qgnb_macro_"), restored (or removed) in
    # finally; digests after; AssertionError naming every changed path. On nt, a test whose name starts "test_l2_"
    # runs between SetThreadExecutionState(0x80000001) and SetThreadExecutionState(0x80000000) in finally (5.7).
    # The wrapper carries `nautilus_guarded = True`.
def layer2() -> Path
    # value = launch.venv_key(); blank -> NotRun("OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)");
    # expanded path missing -> NotRun(f"OWNER: QUANTGEN_NAUTILUS_PYTHON points to a missing file: {value!r}");
    # else p = launch.resolve_venv_python(value); a non-empty launch.venv_mismatches(launch.read_venv(p)) raises
    # AssertionError (a FAIL, O15). Returns p. Every layer-2 test calls it first.
def tests() -> list[tuple[str, Callable[[], None]]]
    # every module-level callable named test_* except LAST_TEST, sorted by name, each guarded; then LAST_TEST, guarded
# CLI: python3 -B -m tests.nautilus_acceptance [-k <substring>] ...  runs the matching tests() entries, prints
# "PASS|FAIL|NOT_RUN <name> <detail>" per test and "<p>/<n> passed, <f> failed, <r> not run"; exit 1 on a FAIL or
# when nothing matched; never writes qa/acceptance_results.json.
```

Task 4 adds (Task 5 uses them):
```python
STUB = ROOT / "tests" / "nautilus_stub_child.py"
def stub_python() -> str
    # sys.executable, unless its normcase(realpath) lies under WindowsApps and
    # %LOCALAPPDATA%\quantgen\py313\python.exe exists, then that file (8.1; QA-R3-10)
def stub_cmd(*flags: str) -> list[str]            # [stub_python(), "-I", str(STUB), *flags]
def stub_probe_cmd() -> list[str]                  # stub_cmd("--probe")
def synth_prices(seed, n, p0, p1, planted=()) -> np.ndarray     # spec 8.2, verbatim
def synth_rf(n) -> np.ndarray                                    # spec 8.2, verbatim
def write_rehearsal_table(tmp: Path, *, like: str = "E1-SPY", prices: np.ndarray, dates: Sequence[str],
                          rf: np.ndarray | None = None, **fields) -> Path
    # Writes the prices file and, when rf is given, a DGS3MO-shaped file (percent: rf * 252 * 100) under tmp, and
    # <tmp>/table.json: a 6.6 table with pilot "rehearsal", every other field from pilot `like` ("E1-SPY": 10.1,
    # "C3-BTCUSD": 10.2), study_configs [], reference_card and reference_card_md5 null, md5s computed, no owner
    # fields; `fields` override any key. Returns the table path.
def run_rehearsal(table: Path, tmp: Path, *, flags: Sequence[str] = (), **run_kwargs) -> tuple[int, dict | None]
    # runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers", out_dir=tmp / "out",
    #            child_cmd=stub_cmd(*flags), probe_cmd=stub_probe_cmd(), **run_kwargs)
    # -> (exit code, the parsed run.json of the newest run folder under tmp / "out", or None)
```

### C9. `tests/nautilus_stub_child.py` (Task 4; spec 8.1)

`<stub python> -I <abs stub> [failure flags] <mode>`; the runner appends the mode. Modes: `--check-env`, `--guard-selftest` (output as C3), `--probe` (prints `{"blocked": true, "errno": 101, "error": "stub"}`, exit 0), `run --in <dir>` (reads C5 and `bars.csv`, applies 5.2.5's rules with `plain_mean` and fee-inclusive `Decimal` sizing, fills every order at its bar's close, rounds each commission with `cents`, writes the four files of C3 with every C6 field and echo; a correct input passes every hard check). Failure flags: `--exit <n>`, `--sleep <s>`, `--no-manifest`, `--bad-json`, `--doctor <C-01|C-02|C-03|C-04|C-07|C-09|C-11|C-14|C-15>` (writes `valid: true` and exits 0; `C-02` lowers `bars_seen` and `bars_fed` together), `--fee-1x` (charges the 1x rate at stress 2, N7), `--selftest-wrong` (one wrong `--guard-selftest` outcome, exit 0). Standard library only.

### C10. `tools/nautilus/runner.py` (Task 4; Task 5 fills the seam and adds three modes)

Command line (5.3.1), `python3 -B -m tools.nautilus.runner`:
- Task 4: `--table <t> --rehearsal --ledger-dir <tmp> --out-dir <tmp> [--child-cmd <json list>]`, `--table <t> --of-record` (Claude reaches only its argument-validation refusals), either with `[--rerun-of <id> --reason <text>]`, `--check-env`, `--egress-record`, `--fixtures [--record-baseline | --write-goldens]`.
- Task 5: `--fingerprint --table <t>`, `--timing`, `--handoff-report`.
- Exit codes: 0 card written, a clean rehearsal or a mode's success; 1 WITHHELD; 2 refused before registration; 3 refused at registration; 4 ERROR; 5 ABORTED. The last console line of every mode is `STATUS <status> exit=<n> record=<path or ->`.

Python API (Task 4 unless marked):
```python
STATUSES = ("IN_PROGRESS", "CARD_WRITTEN", "WITHHELD", "REFUSED_REGISTRATION", "ERROR", "ABORTED")
def main(argv: list[str] | None = None) -> int
def run(table_path: Path, *, mode: str, ledger_dir: Path | None = None, out_dir: Path | None = None,
        child_cmd: list[str] | None = None, probe_cmd: list[str] | None = None,
        hooks: dict[str, Callable[..., None]] | None = None, timeout: float = 900,
        register_fn=gate_ledger.register_trial, score_fn=validate.score_strategy,
        rerun_of: str | None = None, reason: str | None = None) -> int
    # mode "rehearsal" or "of-record"; returns the exit code and never re-raises (QA-R3-6). hooks keys:
    # "after_step0" .. "after_step17", each called as hook(ctx) with the RunContext from step 12 on and hook(None)
    # before it; "child_started", called as hook(launch) with the child's Launch (its cwd is the child's temp dir,
    # holding input.json) after Popen and before communicate. The step 16 and 17 hooks are called by Task 5's
    # hand_off. Of-record mode refuses every seam (child_cmd, probe_cmd, hooks, a non-default timeout, register_fn
    # or score_fn) in argument validation, before step 0 writes anything (R-11).
def table_sha256(table: dict) -> str          # 6.6: sha256 of json.dumps(t, sort_keys=True, separators=(",", ":"),
                                              # ensure_ascii=False) in UTF-8, t without owner_confirmed, host_fingerprint
def code_sha256(repo_root: Path) -> str       # 6.6, over tools/nautilus/**/*.py, tools/nautilus/golden/*.json,
                                              # requirements-nautilus.txt, gate_package.HARNESS_SOURCES,
                                              # docs/asset_expansion_study.py and config.py
def host_fingerprint(hostname: str, ledger: gate_ledger.FamilyLedger) -> str | None    # 6.6; None when no row
def bridge_run_id(now: datetime, table_sha256: str) -> str    # "NB-%Y%m%dT%H%M%S%fZ-<first 8 hex>"
class TableLock:
    def release(self) -> None
def take_lock(out_root: Path, table_sha256: str, ledger_paths: Sequence[Path], rerun_of: str | None
              ) -> tuple[TableLock, list[dict]]
    # R-16 (lock held; a ledger written under 600 s ago), R-17 (5.3.5); returns the lock and earlier_runs
    # [{"bridge_run_id", "status"}] ("UNREADABLE" status when a record cannot be read)
def check_table(table: Path, mode: str, ledger_dir: Path, hostname: str, repo_root: Path) -> dict
    # step 1: R-10 (rehearsal place rule, before any file is opened), R-11, R-15, R-09; returns the validated table
def check_tree(repo_root: Path, anchor_fn: Callable[[Path], str], git_exe: str | None) -> dict
    # step 2 findings: {"head": str | None, "anchor": str, "clean": bool, "porcelain": [str],
    #                   "porcelain_exempt": [str], "offending": [str], "anchor_problem": str | None}
def tree_refusal(findings: dict, mode: str) -> str | None       # "R-01" | "R-02" | None; None in rehearsal
def check_egress_record(record_dir: Path, run_facts: dict) -> None
    # R-14; run_facts = {"venv_python", "base_python", "layer"}; paths compared as 4.3 says
def check_p0a(study_module: types.ModuleType, cache_dir: Path, arrays: dict) -> None
    # R-13; arrays = {"dates": tuple[str, ...], "closes": np.ndarray, "rf": np.ndarray | None}
def judge_census(census: Sequence[str], baseline: Sequence[str], *,
                 stdlib: frozenset[str] = frozenset(sys.stdlib_module_names)) -> list[str]   # "C-08: ..." reasons
def record_baseline(golden_dir: Path, tag: str, census: Sequence[str], *, tracked: bool) -> tuple[int, list[str]]
def write_record(path: Path, obj: dict, *, replace=os.replace, sleep=time.sleep) -> None
    # mkstemp in the same folder, fsync, replace; up to 10 attempts over 5 s on PermissionError; then raises
def parse_fills(path: Path) -> list[dict]      # ts_event int; order_side, commission_ccy, trade_id, venue_order_id
                                               # str; last_qty, last_px, commission Decimal
def parse_decisions(path: Path) -> list[dict]  # i int, ts_event int, decision int, margin float, action str
def parse_equity(path: Path) -> list[dict]     # i int, ts_event int; close, cash, qty, equity_pre Decimal

@dataclass(frozen=True)
class Rebuilt:                                 # 5.3.3
    R: np.ndarray                              # (T-1,), R(t) labelled dates[t+1], cash overlay included
    TV: np.ndarray                             # (T-1,); fills at bar T-1 dropped
    E_minus: np.ndarray                        # (T,), E-(t) = cash(t-1) + q(t-1) P(t), as floats
    cash: list[Decimal]                        # (T,), after the fills of bar t
    q: list[Decimal]                           # (T,)
    fill_bars: list[int]                       # the bar index of every fill, in file order
    final_cash: Decimal
def rebuild_returns(fills: list[dict], closes: np.ndarray, ts: Sequence[int], rf: np.ndarray,
                    capital: Decimal) -> Rebuilt
    # ChildInvalid("C-09", ...) for a fill whose ts_event is not a bar timestamp

@dataclass
class Leg:                                     # one child: column `col`, cost level `stress` (1 or 2)
    col: int
    stress: int
    child: dict                                # the run record's `children` entry (6.3)
    manifest: dict | None
    fills: list[dict]                          # parse_fills
    decisions: list[dict]                      # parse_decisions
    equity: list[dict]                         # parse_equity
    rebuilt: Rebuilt | None
    invalid: list[str]                         # "C-nn: ..." from the child and the parent's re-derivation; [] = valid

@dataclass
class RunContext:                              # built by step 12; filled through step 15; read by Task 5
    mode: str                                  # "rehearsal" | "of-record"
    repo_root: Path
    table: dict                                # as validated by check_table
    table_sha256: str
    code_sha256: str
    bridge_run_id: str
    run_dir: Path                              # <out root>/<bridge_run_id>/
    record: dict                               # the run record (6.3) being built; Task 5 sets parity, gate, card
    dates: tuple[str, ...]                     # T panel dates, ISO
    ts: list[int]                              # T bar timestamps, ns (SPY 21:00 UTC; BTC 00:00 UTC next day)
    closes: np.ndarray                         # (T,), np.round(raw, 9)
    rf: np.ndarray                             # (T,), zeros when rf_file is null
    study: types.ModuleType                    # docs/asset_expansion_study.py as loaded at step 7
    study_pn: Any                              # the S.Panel that study.panel returned at step 7 (P0b)
    grid: list[dict]                           # registration order = column order
    fn: Callable                               # S.trend_switch or S.crypto_trend
    weights: np.ndarray                        # (T, G) QUANTGEN weights (P1, P4)
    pnl_qg: np.ndarray                         # (T-1, G), simulate at cost_bps
    pnl_stress_qg: np.ndarray                  # (T-1, G), at 2 x cost_bps
    turnover_qg: np.ndarray                    # (T-1, G)
    pnl_nt: np.ndarray                         # (T-1, G), Rebuilt.R of the 1x legs; NaN in a column whose leg is invalid
    pnl_stress_nt: np.ndarray                  # (T-1, G), from the 2x legs
    turnover_nt: np.ndarray                    # (T-1, G), Rebuilt.TV of the 1x legs
    legs: dict[tuple[int, int], Leg]           # (col, stress)
    gate_snapshot: dict                        # copy.deepcopy(validate.GATE) at step 9
    ledger: gate_ledger.FamilyLedger
    hash_after_registration: str
    score_fn: Callable
    hooks: dict
    stub_child: bool

@dataclass(frozen=True)
class Outcome:
    status: str                                # "CARD_WRITTEN" | "WITHHELD" | "ERROR"
    exit_code: int                             # 0 | 1 | 4
    withheld_reasons: list[str]

def parity_and_gate(ctx: RunContext) -> Outcome
    # The seam for steps 16 and 17. Task 4's body is exactly
    #     raise NotImplementedError("spec 5.4 and 5.5 are plan Task 5")
    # so a Task 4 run that reaches step 16 ends ERROR, exit 4 (G-06); no Task 4 test asserts the final status or exit
    # code of a run that reaches step 16. Task 5 replaces the body with
    #     from tools.nautilus import parity
    #     return parity.hand_off(ctx)
    # The run lifecycle (Task 4) then writes the final record with the Outcome's status, in its try/finally.
```

### C11. `tools/nautilus/parity.py` (Task 5)

```python
def cents(x) -> int            # int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP)), 5.4.1
def select_matched(pnl_nt: np.ndarray, pnl_stress_nt: np.ndarray, turnover_nt: np.ndarray, dates: Sequence[str],
                   wf_qg: validate.WalkForward, *, embargo: int) -> validate.WalkForward          # 5.4.2
def gate_predicates(score: validate.StrategyScore, gate: dict) -> dict[str, bool]
    # exactly the 18 keys ci_pos, dsr_ok, dsr_finite, pbo_meaningful, flat, pbo_ok, pbo_reject, oos_is_ok, stress_ok,
    # years_ok, plateau_ok, sample_ok, floor_ok, n_years_ok, sessions_ok, mtr_ok, has_bench, bench_ok (5.5 step 5)
def agree(sc_qg: validate.StrategyScore, sc_nt: validate.StrategyScore, gate: dict) -> tuple[bool, str | None]
    # (True, None) allows a card; else (False, "benchmark test dropped") or (False, "decision mismatch") (G-02)
def reference_drift(sc_qg: validate.StrategyScore, wf_qg: validate.WalkForward, grid: Sequence[dict],
                    ref: dict) -> list[str]                                                    # field names (G-08)
def hand_off(ctx: "RunContext") -> "Outcome"
    # steps 16 and 17: P0b to P13 per column and cost level, wf_qg and wf_nt, trial counts, both scores, agreement,
    # G-01 to G-05 and G-08, the card (open(path, "x", encoding="utf-8", newline="\n")); sets ctx.record["parity"],
    # ctx.record["gate"] and ctx.record["card"]; calls the after_step16 and after_step17 hooks
```

### C12. Other shapes (the spec governs, Task in brackets)

Run record `run.json` (6.3) [4, completed by 5]; ledger row (6.4) [4]; card (6.5) [5]; registration table (6.6) [4 reads, 5 commits two]; egress record (4.4) [4]; hand-off report (5.3.1) [5].

## Count Ledger

The `nautilus` suite starts at 0 rows. Every number below is a full row count; "key unset" means `QUANTGEN_NAUTILUS_PYTHON` is not set (layer 2 NOT_RUN), "key set" means `QUANTGEN_NAUTILUS_PYTHON="$NTPY"` on the command line. Full runs go through the wrapper with the key unset; the only FAIL is `papers/test_debate_run_kills_process_tree` (cloud baseline, above).

### Rows per task

| After | Tests added (layer 1 + layer 2) | `nautilus` rows (L1 + L2) | `macro` rows | Full suite, key unset (wrapper) | `--suite nautilus`, key unset | `--suite nautilus`, key set |
|---|---|---|---|---|---|---|
| Baseline (`b7f991a`) | - | 0 | 542 | 870: `745/870 passed, 1 failed, 124 not run` | 0 rows (suite absent) | - |
| Task 1 | 8 + 4 in `tests/nautilus_acceptance.py`, not yet registered | 12 (8 + 4), run only by `python3 -B -m tests.nautilus_acceptance` | 542 | 870: `745/870 passed, 1 failed, 124 not run` (unchanged) | module CLI: `8/12 passed, 0 failed, 4 not run` | module CLI: `12/12 passed, 0 failed, 0 not run` |
| Task 2 | 1 + 0 in `nautilus`; 2 in `tests/macro_m0_harness.py` | 13 (9 + 4) | 544 | 885: `756/885 passed, 1 failed, 128 not run` | `9/13 passed, 0 failed, 4 not run` | `13/13 passed, 0 failed, 0 not run` |
| Task 3 | 2 + 3 | 18 (11 + 7) | 544 | 890: `758/890 passed, 1 failed, 131 not run` | `11/18 passed, 0 failed, 7 not run` | `18/18 passed, 0 failed, 0 not run` |
| Task 4 | 21 + 3 | 42 (32 + 10) | 544 | 914: `779/914 passed, 1 failed, 134 not run` | `32/42 passed, 0 failed, 10 not run` | `42/42 passed, 0 failed, 0 not run` |
| Task 5 | 12 + 3 | 57 (44 + 13) | 544 | 929: `791/929 passed, 1 failed, 137 not run` | `44/57 passed, 0 failed, 13 not run` | `57/57 passed, 0 failed, 0 not run` |

`python3 -B -m tests.macro_m0_harness`: `12/12 passed, 0 failed, 0 not run` before Task 2, `14/14 passed, 0 failed, 0 not run` from Task 2 on. On the owner's Windows run of record (Step 7A and Step 10) the `nautilus` rows are all PASS with the key set, L2-5b the only `nautilus/*` NOT_RUN allowed (spec Step 7A done-when); those counts go into the README at Step 10, not in this plan.

### Test inventory

`L1-n` and `L2-n` are the tests of spec 8.3 and 8.4; `px` marks a plan-level test with no spec id, added where a task's done-when would otherwise have no test. L1-20 and L1-26 are split, because spec Steps 6 and 7 build their cases separately. `tests()` returns every test sorted by name, except `test_l1_32_every_test_guarded_and_ledgers_unchanged`, which always runs last.

| Task | Layer 1 (`tests/nautilus_acceptance.py`) | Layer 2 |
|---|---|---|
| 1 | `test_l1_16_launch_builder_matches_the_contract` (L1-16), `test_l1_17_venv_reads_and_wheel_identity` (L1-17), `test_l1_22_global_interpreter_has_no_nautilus` (L1-22), `test_l1_32_every_test_guarded_and_ledgers_unchanged` (L1-32), `test_px_requirements_nautilus_pins_and_header`, `test_px_env_example_and_env_pins`, `test_px_egress_probe_imports_json_and_socket_only`, `test_px_census_parser_reads_importtime_lines` | `test_l2_01_check_env_pins_identity_precision` (L2-1), `test_l2_08_guard_selftest_outcomes` (L2-8), `test_l2_09_egress_probe_blocked` (L2-9), `test_l2_10_timeout_kills_the_child_tree` (L2-10) |
| 2 | `test_l1_15_encoding_rules_hold` (L1-15); in `tests/macro_m0_harness.py`, both with `test_ids = ["T-RO-01"]`: `test_t_ro_01_nautilus_confined_to_the_sandbox`, `test_t_ro_01_nautilus_allowlist_pinned` | none |
| 3 | `test_px_fixture_inputs_follow_6_1_and_8_2`, `test_px_sandbox_avoids_excluded_constructs` | `test_l2_04_fills_identical_across_processes` (L2-4), `test_l2_05a_refusals_exit_20_before_the_engine` (L2-5a), `test_l2_05b_input_linked_to_env_refused` (L2-5b) |
| 4 | `test_l1_01_return_reconstruction_f1_f1r_f2`, `test_l1_03_children_start_after_registration`, `test_l1_04_broken_chain_stops_before_children`, `test_l1_06_tree_refusals_r01_r02`, `test_l1_07_data_refusals_r04_r05_r06`, `test_l1_08_cost_refusals_r07`, `test_l1_09_place_and_content_refusals_r10`, `test_l1_10_config_id_equals_strategy_lab`, `test_l1_11_register_result_row_md5`, `test_l1_12_census_judgement`, `test_l1_18_gate_bootstrap_b_refusal_r08`, `test_l1_19_table_refusals_r11`, `test_l1_20a_p0a_against_the_study_loaders`, `test_l1_23_egress_refusals_r14`, `test_l1_24_ledger_and_host_refusals_r15`, `test_l1_25_lock_and_freshness_r16`, `test_l1_26a_lifecycle_records_and_exits`, `test_l1_27_child_failures_and_doctored_manifests`, `test_l1_33_goldens_equal_the_spec_tables`, `test_l1_34_write_record_retries_and_fallback`, `test_l1_35_record_baseline_rules` | `test_l2_02_f1_f2_match_goldens` (L2-2), `test_l2_03_n1_matches_golden` (L2-3), `test_l2_06_census_matches_platform_baseline` (L2-6) |
| 5 | `test_l1_02_parity_functions`, `test_l1_05_rerun_policy_r17`, `test_l1_13_parity_failure_withholds_without_card`, `test_l1_14_gate_unchanged_and_g04`, `test_l1_20b_p0b_benchmark_withholds`, `test_l1_21_select_matched_reproduces_wf_qg`, `test_l1_26b_ledger_moved_g05`, `test_l1_28_card_and_record_bytes`, `test_l1_29_trial_counts_protocol_and_reference_drift`, `test_l1_30_card_labels_and_engine_text`, `test_l1_31_walk_forward_raise_g03`, `test_l1_36_fingerprint_reads_no_data` | `test_l2_07_synthetic_end_to_end_rehearsal` (L2-7), `test_l2_11_n6_stress` (L2-11), `test_l2_12_crypto_rehearsal_reference` (L2-12) |

Spec coverage: L1-1 to L1-36 and L2-1 to L2-12 (with 5a and 5b) each appear once; spec Step 4's done-when tests L1-16, L1-17, L1-22 and L1-32 are written at Task 1, with the code they test, and still pass at Task 2; the 8.5 controls are asserted inside `test_t_ro_01_nautilus_confined_to_the_sandbox`.

---

### Task 1: Environment (spec Step 3): requirements, venv reads, launch contract, sandbox self-checks, egress probe, suite skeleton

<!-- TASK 1 -->

---

### Task 2: Guard (spec Step 4): the T-RO-01 amendment, the `nautilus` suite registration, registry and README

<!-- TASK 2 -->

---

### Task 3: Sandbox (spec Step 5): section 5.2 in full, `fixture_inputs`

<!-- TASK 3 -->

---

### Task 4: Runner (spec Step 6): section 5.3, the stub child, goldens and the Linux census baseline

<!-- TASK 4 -->

---

### Task 5: Parity, gate, pilot tables, runbook (spec Step 7): sections 5.4 and 5.5, the two registration tables, `RUNBOOK_windows.md`

<!-- TASK 5 -->
