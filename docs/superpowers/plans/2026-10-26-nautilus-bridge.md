# NautilusTrader Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the research-only NautilusTrader bridge of the spec on the branch `claude/amazing-gauss-tdiguu`: a hash-pinned venv run only as a subprocess, the T-RO-01 amendment that confines simulated orders to one sandbox file, the sandbox child, the ledger-first runner, and the parity checks and gate hand-off that write a QUANTGEN card only when parity holds and both engines reach the same verdict. Everything is tested on synthetic data with temporary ledgers, and the branch ends ready for the owner's Windows hand-off (spec Step 7A).

**Architecture:** Two processes that share only files (spec 4.1). The parent, `tools/nautilus/runner.py`, runs in the global interpreter, imports QUANTGEN read-only, registers every variant in its family ledger before any child starts, computes QUANTGEN's reference matrices with `simulate`, and starts one child per (column, cost level) through the single launch contract of `tools/nautilus/launch.py` (minimal environment, `-I -B -X utf8`, `unshare -rn` on Linux, tree kill on timeout). The child, `tools/nautilus/sandbox.py`, runs in the pinned venv, builds a `BacktestEngine` whose kernel must be BACKTEST, places orders through one `self.submit_order` call, and writes fills, decisions, equity and a manifest into its temp dir. The parent rebuilds daily returns from the fills (spec 5.3.3), runs parity checks P0 to P13 (`tools/nautilus/parity.py`), applies QUANTGEN's walk-forward selection to both matrices, scores both with the unchanged gate, and writes a card only on parity and agreement. The suite `nautilus` (`tests/nautilus_acceptance.py`) runs layer 1 in the global interpreter and layer 2 through the venv.

**Tech Stack:** Python 3.13 global interpreter (numpy 2.3.5, pandas 2.3.3, scipy 1.18.0, frozen); NautilusTrader 1.231.0 in a separate hash-pinned venv (16 distributions, `requirements-nautilus.txt`); the standard library (`subprocess`, `ast`, `csv`, `json`, `hashlib`, `decimal`); Linux `unshare -rn` for egress control; QUANTGEN's `core.quant.strategies`, `core.quant.validate` and `core.quant.gate_ledger`, read-only; the house runner `tests/run_all.py` (no pytest).

Spec: docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md revision 6 (Claude debate closed; GPT and Gemini pending)

**Plan order:** Task 1 = spec Step 3 (Environment), Task 2 = Step 4 (Guard), Task 3 = Step 5 (Sandbox), Task 4 = Step 6 (Runner), Task 5 = Step 7 (Parity, gate, pilot tables, runbook). Each task starts after the previous task's commit. Step 1b (GPT, Gemini, the owner's approval), Step 7A (the Windows hand-off) and Steps 8 to 10 (pilots, close-out) belong to the owner and are outside this plan; Task 5 writes the runbook that Step 7A follows.

**Plan status:** written 2026-10-26 at HEAD `b7f991a`; spec revision 6 and the skeleton are committed, and the five task bodies were integrated on 2026-10-28 at HEAD `f4085cd` (`git -C /home/user/quantgen log -1`). Owner approval (Step 1b) is not given: branch work proceeds on the section 2 defaults (GOVERNANCE-R2-1). Each task's RED and GREEN steps were dry-run in scratch clones only (spec Step 2 done-when, QA-21): Tasks 1 to 3 on clones of `fa28059` (Task 2 with stand-ins for Task 1's files), Tasks 4 and 5 on a clone that carried Tasks 1 to 3 as drafted, whose Task 3 part was an earlier draft (Plan rulings). Full-suite runs were not all repeated there, so their expected counts are the Count Ledger's deltas. The real clone was not touched.

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
  - `NTPY=$S/ntvenv_hash/bin/python`: the Nautilus venv built from the hashed closure (Python 3.13.17, `nautilus_trader` 1.231.0, numpy 2.3.5, pandas 2.3.3; `pyvenv.cfg` `include-system-site-packages = false`). The hashed requirements body is `$S/closure/requirements-nautilus.body.txt`; the local wheels are in `$S/closure/linux/` and `$S/closure/win/`. A later session sets `S` to its own scratchpad, copies `closure/`, `run_baseline.py` and every result file a later step compares with (`t1_baseline.json`, `nb_task2_full.json`; Result files, below) there, and rebuilds the venv with Task 1's install line.
- **House rules (binding).** Never edit `paper_live/` or `grokteam/`; never run their replay, grid, verdict, sameday or calibrate modules, or `grokteam.book`. Never `pip install` into the global interpreter: installs go only into fresh venvs under `$S`, offline from the local wheels (`--no-index --find-links`). Never open or hash `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv`; a test may name such a path (L1-9) but never reads it. Never write a ledger row outside a temp dir.
- **Suite runs (cloud wrapper rule).** Never run `python3 tests/run_all.py`, with or without `--suite`: its `main` rewrites `qa/acceptance_results.json`. Every suite run goes through the redirecting wrapper, kept outside the repo: `python3 -B $S/run_baseline.py $S/<name>.json [--suite <suite>]`. Before and after each run, `md5sum qa/acceptance_results.json` prints `16c9baa5a1777853521d485d5078e456`. Single modules print only: `python3 -B -m tests.macro_m0_harness`, and from Task 1 `python3 -B -m tests.nautilus_acceptance [-k <substring>]`. Layer-2 checks put `QUANTGEN_NAUTILUS_PYTHON="$NTPY"` on the command line; without it layer 2 is NOT_RUN. A full run takes about 10 minutes: start it in the background and wait; nothing else from QUANTGEN runs meanwhile (T-HERM-02; spec 3.8).
- **Result files.** Every wrapper run writes its rows to a named JSON file under `$S`, and no task deletes an earlier task's file: Task 1 `$S/t1_baseline.json` (Step 0; log `$S/t1_baseline.log`) and `$S/t1_after.json` (Step 16); Task 2 `$S/nb_task2_red.json`, `$S/nb_task2_nautilus.json`, `$S/nb_task2_nautilus_key.json` and `$S/nb_task2_full.json`; Task 3 `$S/task3_nautilus.json`, `$S/task3_nautilus_key.json` and `$S/task3_full.json`; Task 4 `$S/t4_nautilus.json` and `$S/t4_after.json`; Task 5 `$S/task5_nautilus.json`, `$S/task5_nautilus_key.json` and `$S/task5_full.json`. Each full run is compared row by row (added, removed, changed): Tasks 1, 2, 4 and 5 with `$S/t1_baseline.json`, expecting the cumulative Count Ledger rows added; Task 3 with `$S/nb_task2_full.json`, expecting its own 5 rows added. Nothing writes under `docs/nautilus_bridge/` while a `nautilus` or full run is in progress, the owner-rulings log and the progress chart included: it is a guard root of spec 3.3, so a change there FAILs the running test and L1-32.
- **Commands that write into the repository.** `runner --egress-record` and `runner --handoff-report` write under `docs/nautilus_bridge/` and run only in a scratch clone (`git clone /home/user/quantgen $S/clone_<task>`), never in the real clone; their outputs are Step 7A's, on Windows. `runner --fixtures --write-goldens` and `--fixtures --record-baseline` run in the real clone only at the Task 4 steps that name them.
- **CRLF files.** `tests/run_all.py` and `README.md` are CRLF (so are `requirements.txt`, `pyproject.toml` and `config.py`, which this plan never edits). Edit them only with the Edit tool, never with a tool that rewrites newlines, and check the line ends after every edit: `python3 -c "b = open('tests/run_all.py', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'tests/run_all.py must stay CRLF'; print('CRLF ok')"` (the same with `README.md`). Never renormalise. Every new file is UTF-8 with LF line ends; `.env.example`, `.gitignore`, `tests/macro_m0_harness.py` and `tests/macro_registry.csv` are LF and stay LF.
- **Commits.** Each task ends with one commit on the branch. Stage named paths only (`git add <path> ...`), never `git add -A` or `git add .`; before committing, `git status --short` shows exactly the task's paths, plus any path that was already modified or untracked before the task began and that no task owns ; none is expected, because spec revision 6 and this plan are committed, and Task 1 Step 0 records any that exist (each later task's Step 1 checks against that list); a task never stages those. The message ends with exactly these two lines:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
  ```
  No task pushes. Never push a tag: `studies-of-record-2026-10-23` is the owner's real annotated tag (tag object `6e7c1f7`, peeling to `eacd57d`), which the owner pushed to origin and this clone carries, so `tests/frozen_guard.py` passes; no stand-in exists any more, and Claude never pushes, moves or deletes the tag.
- **Cloud baseline, before this plan (HEAD `b7f991a`; a reference example only, Count Ledger).** The first cloud full run (2026-10-26 13:51) gave `738/870 passed, 8 failed, 124 not run`; seven of the FAILs were environment-only and are gone: `expansion/selfcheck_strategies`, `selfcheck_curve_models` and `selfcheck_crypto_analytics` (statsmodels missing), `guard/test_a`, `test_b` and `test_d` (the tag missing then; the clone now carries the owner's real tag), `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache` (cache mtimes). With statsmodels installed, a local stand-in of the tag (since replaced by the owner's real tag) and the cache mtimes backdated, the re-run made for this plan (`$S/baseline2_results.json`) gives `745/870 passed, 1 failed, 124 not run`. Its differences from the owner's Windows record (`qa/acceptance_results.json`: 749 PASS, 121 NOT_RUN of 870) are environment-only: `papers/test_debate_run_kills_process_tree` FAIL (no `taskkill`) and the three `papers/test_compile_*` NOT_RUN (no tectonic); everything else passes. ②-1 (`statsmodels>=0.14.2` in `requirements.txt`), PT-07's calendar tests in the `macro` suite and possibly the Bonds patch's suite change the suite before Task 1, so Task 1 Step 0 re-measures the baseline `B`, the `macro` row count `M` and the FAIL set, and a task's full run is correct when it is `B` plus the Count Ledger's deltas, row for row, with `B`'s FAIL set. `python3 -B -m tests.macro_m0_harness` gives `H/H passed, 0 failed, 0 not run`, `H` = 12 at `fa28059` (Count Ledger).
- **Bridge text.** No bridge file contains a T-RO-01 token (spec 3.11): no `submit_order` outside the one `place` method of `tools/nautilus/sandbox.py` (added at Task 3, after Task 2's amendment), no upper-case `CANO` (as in `CANONICAL`), no `KIS_ACCOUNT` or `ACNT_PRDT_CD`. Diagnostics in `sandbox.py` name no `NAUTILUS_DENIED_PREFIXES` or `NAUTILUS_DENIED_NAMES` entry (rule E). The new tests in `tests/nautilus_*.py` follow the same rule, although `tests/` is not scanned (Task 3 spells the one call `"submit" + "_order"`). `tests/macro_m0_harness.py` is the scanner: its Task 2 tests name the tokens in the 8.5 controls and in the embedded 5.2.9 skeleton, as its own `FORBIDDEN_TEXT_CI` and `FORBIDDEN_CALLS` already do.
- **Tests.** No pytest. Every test is a zero-argument module-level `test_*` function of `tests/nautilus_acceptance.py` (or, for the two T-RO-01 tests, `tests/macro_m0_harness.py`); helpers never start with `test_`. A test that cannot run raises `tests.notrun.NotRun(reason)`. Test names are fixed by the Count Ledger; a task adds exactly its listed tests.
- **Task format.** Each task section has: verified-before-writing notes; **Files** (create, modify, test); **Interfaces** (consumes, produces, by the names of the Interface Contract below); then steps `- [ ] **Step N: ...**` with exact commands and exact expected output. Tests come first, verbatim, and are run to fail for the stated reason (RED); then the code, verbatim, and the run that passes (GREEN). Each task ends with its suite counts checked against the Count Ledger and a commit step that names every path and gives the message with both trailer lines.

## File Structure

| File | Task | Responsibility |
|---|---|---|
| `requirements-nautilus.txt` | 1 | New, LF. Spec 5.1's header verbatim, then `$S/closure/requirements-nautilus.body.txt` verbatim: 16 distributions with `==` and `--hash=sha256:` lines; the single source of the version pins. Installs only into the venv. |
| `.env.example` | 1 | Edit (LF): a heading and the line of spec 3.4, `QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'`. |
| `tools/nautilus/__init__.py` | 1 | Empty package marker. |
| `tools/nautilus/egress_probe.py` | 1 | The egress probe of spec 4.4: `json` and `socket` only. |
| `tools/nautilus/launch.py` | 1; 3 | The launch contract (4.3): argv and environment builder, `run_child`, tree kill, temp dirs, `unshare`; the venv reads and wheel identity (6.7); the census parser (5.2.7); `BridgeRefusal` and `ChildInvalid`. Task 3 appends `FIXTURES`, `_FIXTURE_CLOSES`, `_fixture_ts` and `fixture_inputs` after `cleanup_tempdir`, the file's last function (QA-R3-1); nothing else in the file changes. |
| `tools/nautilus/sandbox.py` | 1; 3 | The child and the only order-placing file. Task 1: the import block of 5.2.9 verbatim, `inside`, `plain_mean`, both guards, `make_fee_model`, `build_engine`, `check_env`, `guard_selftest`, `main` (`run` refuses every input with exit 20). Task 3 rewrites the whole file: section 5.2 in full in the structure of 5.2.9 (configs, ports, the one `self.submit_order`, the 6.1 checks, `run`); of Task 1's definitions only `run` and `main` change, `main` now ending a refusal with `ArgumentParser.exit(20, "C-05: ...")` (C3). |
| `tools/nautilus/golden/env_pins.json` | 1 | Both platforms' pins and wheel identities, computed offline (6.7). |
| `tests/fixtures/nautilus/MANIFEST.csv`, `tests/fixtures/nautilus/nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD`, `tests/fixtures/nautilus/nautilus_trader-1.231.0.win_amd64.RECORD` | 1 | Both wheels' `RECORD` files, md5-listed and read through `tests.notrun.require_fixture(name, manifest=...)` (6.7; QA-R2-14). |
| `docs/nautilus_bridge/.gitignore` | 1 | `runs/.locks/` (5.3.5). |
| `tests/nautilus_acceptance.py` | 1 to 5 | Suite `nautilus`: the guard of 3.3, the layer-2 gate, `tests()`, the print-only CLI; Task 1 creates it, every task adds its tests (Count Ledger), Task 4 adds the stub and rehearsal helpers. Spec 5.8 lists steps 4 to 7: the plan creates it at Task 1 so that Task 1 is test-first; it joins `tests/run_all.py` at Task 2, so the full-suite counts do not move at Task 1. Anchors: Task 2 inserts `test_l1_15_encoding_rules_hold` and `encoding_offences` directly before the line that starts `def tests(`; Tasks 3, 4 and 5, in that order, each insert their block directly above the three-line `# CLI` banner before `def main(`; no task edits another task's lines, except a keyword that Task 2 Step 10 adds to a Task 1 line breaking C1. |
| `tests/macro_m0_harness.py` | 2 | `import hashlib`; the constants of 5.6 after `ALLOWED_BARE_CALLS`, the 7 verbs in `FORBIDDEN_CALLS`, rules A to F in `_offences`, the two new T-RO-01 tests after `test_t_ro_01_scan_reaches_tools_and_papers`. |
| `tests/macro_registry.csv` | 2 | Row 12 (`T-RO-01`) `implemented_in`, rewritten by `python3 -B -m tests.macro_acceptance`; no other row changes. |
| `tests/run_all.py` | 2 | CRLF: `nautilus_tests()` (a copy of `papers_tests` for `tests.nautilus_acceptance`, an import failure one FAIL row `import`), the `nautilus/` term last in `tests()`, `nautilus` in the `--suite` help. |
| `README.md` | 2 | CRLF: `nautilus` in the `--suite` help line (`README.md:853`) and the `nautilus` row of 5.8 (its path in backticks, as the table writes every suite path; last column `counted at the Windows run of record`) directly after the `papers` row; the Total row unchanged (C-4). |
| `tools/nautilus/runner.py` | 4; 5 | The parent (5.3): CLI, steps 0 to 15, the pure refusal functions, return reconstruction, the census judgement, `record_baseline`, `write_record`, the run lifecycle and the `parity_and_gate` seam. Task 5 edits it at four exact anchors: two module-docstring edits, the body of `parity_and_gate` (C10's Task 4 text) and Task 4's whole `main`, which it replaces with the three new modes (`--fingerprint`, `--timing`, `--handoff-report`) and a new `main`; nothing else of Task 4's text changes. |
| `tests/nautilus_stub_child.py` | 4 | The layer-1 stub child (8.1; QA-R2-2), standard library only. |
| `tools/nautilus/golden/F1.json`, `F2.json`, `N1.json` | 4 | Goldens (6.8), written by `runner --fixtures --write-goldens` on Linux. |
| `tools/nautilus/golden/modules_manylinux_2_35_x86_64.json` | 4 | The Linux census baseline, the union of the F1 and F2 censuses, written by `runner --fixtures --record-baseline`. |
| `tools/nautilus/parity.py` | 5 | Checks P0b to P13 (5.4.1), `cents`, `select_matched` (5.4.2), `gate_predicates`, `agree`, `reference_drift` (5.5), and `hand_off`, steps 16 and 17. |
| `docs/nautilus_bridge/registration/pilot1_E1_spy.json`, `docs/nautilus_bridge/registration/pilot2_C3_btcusd.json` | 5 | The two registration tables (6.6, 10.1, 10.2), without `owner_confirmed` and `host_fingerprint`: exact bytes, one key per line in 6.6's order, `axes` keys in the study's call order, never re-saved with `sort_keys` (C1). |
| `docs/nautilus_bridge/RUNBOOK_windows.md` | 5 | The Step 7A commands of spec section 9 in PowerShell, with the pinned 3.13 patch of the base interpreter (OPS-R4-5). |
| `docs/superpowers/plans/2026-10-26-nautilus-bridge.md` | (Step 2) | This plan. |

Unchanged on purpose (spec 5.8): `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`, `core/quant/*.py`, `ui/strategy_lab_page.py`, `tests/acceptance.py`, `paper_live/`, `grokteam/`, `docs/asset_expansion/` and `docs/asset_expansion_study.py`; also `qa/acceptance_results.json`, which no Claude commit includes. One owner-ruled change reached `requirements.txt` before Task 1: ②-1's `statsmodels>=0.14.2` (`6054b33`). "Byte-identical" (spec 3.4 and Step 3's done-when) therefore means byte-identical to the state Task 1 Step 0 records: the sha256 of `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`, `tests/run_all.py` and `README.md`, checked again at Task 1 Steps 14 and 17 (Task 2 then edits `tests/run_all.py` and `README.md`). Step 7A creates `tools/nautilus/golden/modules_win_amd64.json`, `docs/nautilus_bridge/egress/win_amd64.json` and `docs/nautilus_bridge/handoff/win_amd64.json` on the owner's machine; no task creates them.

## Interface Contract

Everything below crosses a task boundary. A task that provides an item implements it with exactly this module path, name, signature, return type and file shape; a task that consumes it relies on nothing else. Where the spec fixes a value, the section is cited and the spec governs. "Task n" names the task that first provides the item.

### C1. Shared conventions (all tasks)

- **Section-7 ids.** Every refusal or invalid reason is a string that begins with its section-7 id and `": "`, such as `"R-03: venv python is not absolute: 'C:/x'"` or `"C-08: TP name added: foo"` (QA-R3-8). A refusal the sandbox prints is C3's `C-05: ...` stderr line.
- **Withheld reasons** (the run record's `withheld_reasons`; Task 5 writes them, Task 4's re-run policy reads them): a leg that failed P13 contributes each of its own reasons, its `C-nn` id first, with ` (column <c> (<theta>), <s>x)` appended, so a WITHHELD whose reasons all start `C-06` stays re-runnable (5.3.5); a failed 5.4.1 check starts with its P id (`"P7: column 0 (rule=sma, lookback=126, step=21), 2x: {...}"`); a section-7 G condition starts `"G-02: "`, `"G-03: "`, `"G-05: "` or `"G-08: "`, followed by 6.3's literal text where it has one (`decision mismatch`, `benchmark test dropped`, `ledger moved after registration`, `reference drift`). G-04 is ERROR, exit 4: its `G-04: ...` message goes into `record["error"]["message"]` and the Outcome's reasons.
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
- **Encoding (3.7).** Every `open`, `read_text` and `write_text` in `tools/nautilus/` and the new tests passes `encoding="utf-8"` (the registration table `utf-8-sig`), text writes pass `newline="\n"` (or `newline=""` for a file a csv writer writes with `lineterminator="\n"`, the csv module's documented form, which writes the same LF bytes), text-mode `subprocess` calls pass `encoding="utf-8", errors="replace"`, every `csv.writer` passes `lineterminator="\n"`. L1-15 (Task 2) enforces this by AST and judges a `subprocess` call's text mode from its literal keywords: `run_child`'s `Popen(..., **launch.popen_kwargs)` is covered by L1-16's assertion on `popen_kwargs`, not by L1-15.
- **JSON bytes.** `input.json` is `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`, no trailing newline, so the runner, `fixture_inputs` and the stub give identical bytes for identical objects. Every other JSON file the bridge writes is `json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"`, except the card (`ModelCard.to_json()`, 5.5 step 8) and registration tables. A registration table keeps its key order, because `S.grid_from(**axes)` expands its keywords in their order and step 1 compares the grid element by element: tests write temp tables as `json.dumps(t, indent=1, ensure_ascii=False) + "\n"` (Task 4's `write_rehearsal_table` and `_of_record_table`), and the two committed tables are Task 5's exact bytes. `table_sha256` (6.6) sorts the keys, so key order never changes a digest.
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
CREATE_NEW_PROCESS_GROUP = 0x00000200          # subprocess.CREATE_NEW_PROCESS_GROUP, which exists only on Windows
PINNED = ("nautilus-trader", "numpy", "pandas")
VENV_FIX: str                                  # R-03's remedy for the key and the venv (Task 4's REMEDY["R-03"])
STORE_FIX: str                                 # R-03's remedy for a venv made from the Store python (6.7)
PARENT_NAUTILUS_REMEDY: str                    # R-03 for the parent, exactly three lines joined by "\n" (spec 7;
                                               # OPS-R3-1): "python -m pip uninstall -y nautilus-trader",
                                               # "python -m pip check" and 'python -c "import numpy, pandas, scipy;
                                               # print(numpy.__version__, pandas.__version__, scipy.__version__)"';
                                               # L1-22 asserts it, Task 4's check_venv passes it as the remedy
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
    # `home` or `executable` under WindowsApps or \Packages\PythonSoftwareFoundation. (OPS-R2-2). The Store test is a
    # case-insensitive substring test, with either slash, on the strings pyvenv.cfg records; only the equality with
    # parent_base_executable compares os.path.normcase(os.path.realpath(p)), because a Store parent's realpath of its
    # own redirected paths could resolve into \Packages\ (UNVERIFIED either way). Returns:
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
                              # creationflags=CREATE_NEW_PROCESS_GROUP (nt; launch's own constant, so the nt
                              # launch builds on a POSIX host too)

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
    # cwd = str(tempdir). Starts no process. Paths are split and joined with ntpath for os_name "nt" and posixpath
    # otherwise, and venv_python may be any PurePath (used through str()), so L1-16 builds both platforms' launches
    # on either host.
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

Scan constraints (Task 2's amended T-RO-01 scans Task 1's files): `launch.py` and `egress_probe.py` never import `nautilus_trader`, use no `NAUTILUS_DENIED_NAMES` identifier (no `api_key`, no `*HttpClient`), and call no `IMPORT_MACHINERY` function with a string containing `nautilus`; `parent_nautilus()` and `parent_pyarrow()` use `importlib.metadata` only, never `find_spec`. L1-15 (Task 2) reads `FIXTURES` and `fixture_inputs` through `getattr`, so it passes before Task 3 adds them and checks their bytes for `\r` after.

### C3. `tools/nautilus/sandbox.py` command line and files (Task 1 for the two self-checks; Task 3 for `run`)

- **argv** as `build_launch` builds it; `<venv python> -I -B -X utf8 [-X importtime] <abs sandbox.py> <mode>`.
- **`--check-env`**: one JSON line on stdout, no file, exit 0:
  `{"schema": "nautilus-bridge-check-env/1", "python": str, "system": str, "machine": str, "environment": str, "precision": {"HIGH_PRECISION": bool, "FIXED_PRECISION": int, "QUANTITY_MAX": float, "PRICE_MAX": float}}`. Measured on Linux: `HIGH_PRECISION` true, `FIXED_PRECISION` 16, `QUANTITY_MAX` 34028236692093.0, `PRICE_MAX` 17014118346046.0, `environment` `"BACKTEST"`.
- **`--guard-selftest`**: one line `json.dumps(out, sort_keys=True)`, exit 0 exactly when it is `{"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}`, else exit 30.
- **`run --in <dir>`**: `<dir>` absolute and equal to its own `Path.resolve()`, else exit 20. Task 1's `run` refuses every input with exit 20 and prints nothing; Task 3 implements it. From Task 3, exit 20 writes no file and the last line of stderr is `C-05: <reason>`: `C-05: input refused: <rule>` for a rule of 6.1 or 5.2.8 (the rule names of Task 3's `check_input`, `check_params` and `inside`, such as `input refused: n_bars differs from bars.csv`), and `C-05: run needs --in <an absolute directory equal to its own resolve()>` for the `--in` rule. `main` writes it with `argparse.ArgumentParser.exit(20, ...)`, because rule F1 allows the sandbox only `from sys import argv, exit` (section 7, C-05: stderr only). Exit codes (5.2.1): 0 valid; 10 complete but invalid (`manifest.json` written with `valid: false`); 20 input refused before the engine is built; 30 a self-test case misbehaved; any other value a crash.
- **Inputs** in `<dir>`: `input.json` (C5) and `bars.csv` (header `i,ts_ns,close`, LF, one row per bar, `i` from 0, `ts_ns` strictly increasing, `close` above zero with exactly `price_precision` decimals).
- **Outputs** in `<dir>` (5.2.6; UTF-8, LF):
  - `fills.csv`, header `ts_event,order_side,last_qty,last_px,commission,commission_ccy,trade_id,venue_order_id`;
  - `decisions.csv`, header `i,ts_event,decision,margin,action` (`action` in `buy`, `sell`, `hold`, `skip_zero_qty`);
  - `onbar_equity.csv`, header `i,ts_event,close,cash,qty,equity_pre`;
  - `manifest.json` (C6).
- **Scan (Task 2).** Task 1's `sandbox.py` holds 5.2.9's import block and functions without the `Port` classes and without `place`, so it holds no `submit_order` node, which the unamended T-RO-01 scan would fail on; under rules A to F it gives no hit, rule A collecting no node. Task 3 adds the one `self.submit_order` call in `Port.place`; from then on the real sandbox exercises rule A's exempt case.

### C4. `tools/nautilus/egress_probe.py` (Task 1)

`<venv python> -I -B -X utf8 <abs egress_probe.py>` through `build_launch(script=EGRESS_PROBE, mode_args=[])`. Imports `json` and `socket` only. `socket.create_connection(("1.1.1.1", 443), timeout=3)`; prints one line `{"blocked": bool, "errno": int | null, "error": str}`; exit 0 when the connect failed, 1 when it connected (closed at once).

### C5. `input.json` (spec 6.1; written by the runner at Task 4 and by `fixture_inputs` at Task 3)

Exactly these 14 keys, no other: `schema` (`"nautilus-bridge-input/2"`), `strategy` (`"trend_switch"` or `"crypto_trend"`), `params` (trend: `{"rule", "lookback", "step"}`; crypto: `{"hysteresis", "lookbacks", "mas"}`, the study defaults `[7, 14, 21, 28]` and `[10, 20, 50, 100, 200]` filled in by the runner when the grid names only `hysteresis`), `instrument` (`"SPY"` or `"BTC/USD"`), `capital_usd` (str), `cost_bps` (str), `stress` (`"1"` or `"2"`), `fill_seed` (int), `price_precision` (int), `size_precision` (int), `volume` (str), `n_bars` (int), `bars_sha256` (64 lower-case hex), `ledger_hash_after_registration` (32 lower-case hex). Ranges as 6.1. Fixtures register nothing and pass `gate_ledger.ledger_hash([])` = `d751713988987e9331980363e24189ce`, the md5 of `"[]"` (`core/quant/gate_ledger.py:371-372`), never the md5 of empty bytes (`d41d8cd9...`) that the Revision-4 probe used; Task 3 pins it as `EMPTY_LEDGER_HASH` and asserts it against the function.

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
# "PASS|FAIL|NOT_RUN <name> <detail>" per test, <detail> being f"{type(exc).__name__}: {exc}" for a FAIL and the
# NotRun reason for a NOT_RUN (as tests/run_all.py:117-120); then "<p>/<n> passed, <f> failed, <r> not run"; exit 1 on
# a FAIL or when nothing matched; never writes qa/acceptance_results.json.
def _refused(call: Callable[[], object], rid: str) -> launch.BridgeRefusal
def _invalid(call: Callable[[], object], cid: str) -> launch.ChildInvalid
    # each asserts the id and the "<id>: " prefix of str(exc) and returns the exception; Tasks 4 and 5 use them
```

Task 2 adds, directly before `def tests(`:
```python
def test_l1_15_encoding_rules_hold()
def encoding_offences(source: str, rel: str) -> list[str]   # "<rel>:<line>: <call>() <problem>" per broken call (C1)
```

Task 3 adds (Tasks 4 and 5 may use them and never redefine them):
```python
EMPTY_LEDGER_HASH = "d751713988987e9331980363e24189ce"     # C5
INPUT_KEYS: frozenset[str]                                  # C5's 14 keys
F1_INPUT: dict; F2_INPUT: dict                              # 8.2's F1 and F2 input objects
F_TABLES: dict                                              # 8.2's fills, decisions and balance of F1 and F2
OUTPUTS = ["decisions.csv", "fills.csv", "manifest.json", "onbar_equity.csv"]
MANIFEST_KEYS: set[str]; MANIFEST_RESULT_KEYS: set[str]; MANIFEST_ENGINE: dict; FILLS_HEADER: str
ORDER_CALL = "submit" + "_order"
def _canonical(obj: dict) -> bytes                          # C1's input.json bytes
def _sandbox_run(python: Path, raw: bytes, bars: bytes, *, prepare: Callable[[Path], None] | None = None,
                 in_arg: Callable[[Path], str] = str) -> tuple[launch.ChildResult, dict[str, bytes]]
def _check_run(name: str, raw: bytes, bars: bytes, result: launch.ChildResult, out: dict[str, bytes]) -> dict
    # F1 and F2 only
def _positive_control(python: Path, name: str) -> dict[str, bytes]
def _refused_before_engine(label: str, reason: str, result: launch.ChildResult, out: dict[str, bytes]) -> None
def _check_env_precision(python: Path) -> dict
def _link(name: str, target: Callable[[Path], Path]) -> Callable[[Path], None]
```

Task 4 adds (Task 5 uses them; Tasks 3 and 5 never redefine them):
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
    # fields; `fields` override any key (a new `axes` without `grid` recomputes the grid). Written without sort_keys,
    # so the axes keys keep the study's call order (C1). Returns the table path.
def run_rehearsal(table: Path, tmp: Path, *, flags: Sequence[str] = (), **run_kwargs) -> tuple[int, dict | None]
    # runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers", out_dir=tmp / "out",
    #            child_cmd=stub_cmd(*flags), probe_cmd=stub_probe_cmd(), **run_kwargs)
    # -> (exit code, the parsed run.json of the newest run folder under tmp / "out", or None)
def _runner() -> types.ModuleType                    # imports tools.nautilus.runner inside the calling test
def _bdates(n: int) -> list[str]                     # pd.bdate_range("2001-01-02", periods=n), ISO
def _md5(path: Path) -> str
def _small_table(tmp: Path, *, n: int = 320, axes: dict | None = None, with_rf: bool = True, **fields) -> Path
def _captured(fn: Callable[[], object]) -> tuple[object, str]                     # (result, stdout)
def _plain_row(rule: str, k: int) -> dict                                         # a plain ledger row to plant
def _fixture_series(name: str) -> tuple[str, list[int], np.ndarray]               # (capital, ts, closes), via C2
SPEC_FILLS: dict; ONE_SMA: dict; REHEARSAL_LIKE: dict; GOLDEN_SPEC: dict         # 8.2's tables; 10.1 and 10.2
```

### C9. `tests/nautilus_stub_child.py` (Task 4; spec 8.1)

`<stub python> -I <abs stub> [failure flags] <mode>`; the runner appends the mode. Modes: `--check-env`, `--guard-selftest` (output as C3), `--probe` (prints `{"blocked": true, "errno": 101, "error": "stub"}`, exit 0), `run --in <dir>` (reads C5 and `bars.csv`, applies 5.2.5's rules with `plain_mean` and fee-inclusive `Decimal` sizing, fills every order at its bar's close, rounds each commission with `cents`, writes the four files of C3 with every C6 field and echo; a correct input passes every hard check). Failure flags: `--exit <n>`, `--sleep <s>`, `--no-manifest`, `--bad-json`, `--doctor <C-01|C-02|C-03|C-04|C-07|C-09|C-11|C-14|C-15>` (writes `valid: true` and exits 0; `C-02` lowers `bars_seen` and `bars_fed` together), `--fee-1x` (charges the 1x rate at stress 2, N7), `--selftest-wrong` (one wrong `--guard-selftest` outcome, exit 0). Standard library only.

### C10. `tools/nautilus/runner.py` (Task 4; Task 5 fills the seam and adds three modes)

Command line (5.3.1), `python3 -B -m tools.nautilus.runner`:
- Task 4: `--table <t> --rehearsal --ledger-dir <tmp> --out-dir <tmp> [--child-cmd <json list>]`, `--table <t> --of-record` (Claude reaches only its argument-validation refusals), either with `[--rerun-of <id> --reason <text>]`, `--check-env`, `--egress-record`, `--fixtures [--record-baseline | --write-goldens]`.
- Task 5: `--fingerprint --table <t>`, `--timing`, `--handoff-report`. `--fingerprint` prints `table_sha256 <hex>` and `code_sha256 <hex>` as soon as the table parses as JSON (not JSON: R-11, exit 2, no digest); it then validates the table against 6.6 with both owner fields optional (Task 4's `_check_place` and `_check_values` in of-record mode, `_check_fields` with mode `"fingerprint"`), and a failure prints the R-11 refusal and exits 2 after the digests; it opens no `prices_file`, `rf_file` or `reference_card`; a valid table prints `host_fingerprint <hex>` or `host_fingerprint null (<reason>; R-15, O11)`, then `owner_confirmed form: <name>, <YYYY-MM-DD>, table <16 hex>, code <16 hex>` and `STATUS OK exit=0 record=-`, exit 0 with or without a fingerprint.
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
def check_p0a(study_module: types.ModuleType, cache_dir: Path, arrays: dict) -> Any
    # R-13; arrays = {"symbol": str, "start": str, "dates": tuple[str, ...], "closes": np.ndarray,
    # "rf": np.ndarray | None}; returns the S.Panel that study.panel built, which run() keeps in RunContext.study_pn
def judge_census(census: Sequence[str], baseline: Sequence[str], *,
                 stdlib: frozenset[str] = frozenset(sys.stdlib_module_names)) -> list[str]   # "C-08: ..." reasons
def record_baseline(golden_dir: Path, tag: str, census: Sequence[str], *, tracked: bool,
                    python: str | None = None) -> tuple[int, list[str]]
    # python: the census file's "python" field (C7), the venv's from --check-env; default platform.python_version()
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

# Task 4's module-level internals that Task 5 calls, with the signatures and behaviour of Task 4's text (Task 5 edits
# runner.py only at its four anchors, File Structure):
PRICE_DECIMALS = 9; CRYPTO_DEFAULTS: dict; GOLDEN_FIXTURES = ("F1", "F2", "N1"); EGRESS_SCHEMA: str; LAYER: str
REMEDY: dict; S (core.quant.strategies); pd (pandas)
def refuse(rid: str, message: str) -> BridgeRefusal                  # with REMEDY[rid]
def load_table(path: Path) -> tuple[dict, bytes]                     # utf-8-sig; R-11 unless one JSON object
def _check_place(t: dict, mode: str, repo_root: Path) -> None
def _check_fields(t: dict, mode: str) -> None                        # owner fields required only in "of-record"
def _check_values(t: dict, mode: str) -> None
def _print_refusal(exc: BridgeRefusal) -> int                        # prints, then "STATUS REFUSED exit=2 record=-"
def _venv_for_mode() -> tuple[Path, dict, str | None]                # (python, reads, unshare); R-03 off the pins
def venv_python_from_key() -> Path
def launch_once(mode_args: list[str], *, python: Path | None, child_cmd: list[str] | None, unshare: str | None,
                timeout: float, script: Path = launch.SANDBOX) -> tuple[launch.ChildResult, dict | None]
def run_fixture(name: str, python: Path, unshare: str | None, *, timeout: float = launch.TIMEOUT_S) -> dict
def compare_golden(got: dict, want: dict) -> list[str]
def load_baseline(tag: str, golden_dir: Path = launch.GOLDEN_DIR) -> list[str] | None
def census_diff(old: Sequence[str], new: Sequence[str]) -> list[str]
def control_connect(host: str = "1.1.1.1", port: int = 443, timeout: float = 3) -> dict
def _git(git_exe: str, repo_root: Path, *args: str) -> subprocess.CompletedProcess
def _utc_now() -> str
def child_params(table: dict, theta: dict) -> dict
def cost_text(cost_bps) -> str
def bars_bytes(closes: np.ndarray, ts: Sequence[int]) -> bytes
def input_bytes(table: dict, theta: dict, stress: int, bars: bytes, n_bars: int, ledger_hash: str) -> bytes
def bar_timestamps(dates: Sequence[str], instrument: str) -> list[int]
def ledger_row(table: dict, theta: dict, *, span: Sequence[str], run_utc: str, anchor: str, bridge_run_id: str) -> dict
def load_study(repo_root: Path) -> types.ModuleType
# Behaviour Task 5 relies on: _after_registration copies Outcome.withheld_reasons into the record and finishes with
# the Outcome's status and exit code; _new_record starts parity, gate, card and error at None; step 7 sets
# provenance = {"p0a": ..., "p0b": None}; a WITHHELD record whose reasons all start "C-06" is re-runnable without
# --rerun-of; e1_parity_passed reads parity.hard_pass (C12); record["costs"]["classes"], record["data"]["prices_md5"]
# and ["rf_md5"], and record["registration"] (rows with config_id and row_md5, n_raw_before, n_raw_after) are filled
# before step 16.
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
def corr(a, b) -> float
    # Pearson (P2, P12); a pair of constant series counts 1.0 when equal to 1e-12 and NaN otherwise: a column that never
    # trades with rf = 0 gives R = pnl = 0 on every row, and validate.sharpe gives 0.0 for both, so P3 holds too
def card_rules(table: dict, *, stub_child: bool) -> dict    # 6.5's rules; engine "STUB" with a stub child (5.3.1)
```
Withheld reasons follow C1; `parity.hard_pass` follows C12.

### C12. Other shapes (the spec governs, Task in brackets)

Two run-record fields are fixed here because Task 4 reads what Task 5 writes: `parity.hard_pass` is one bool, true only when every hard check (P0b, P1 to P4, P7, P12 and P13) passed for every column at both cost levels and no G-03 arose in the walk-forwards; Task 4's `e1_parity_passed` accepts an of-record `E1-SPY` record with `parity.hard_pass` true, 12 registration rows and this `code_sha256` (GOVERNANCE-R4-4). `withheld_reasons` follow C1.

Run record `run.json` (6.3) [4, completed by 5]; ledger row (6.4) [4]; card (6.5) [5]; registration table (6.6) [4 reads, 5 commits two]; egress record (4.4) [4]; hand-off report (5.3.1) [5].

## Count Ledger

The baseline moves before Task 1 (②-1's `statsmodels` line, PT-07's calendar tests in `tests/macro_m1_calendars.py`, possibly the Bonds patch's suite), so every full-suite count is a delta from the baseline that Task 1 Step 0 re-measures through the wrapper with the key unset and writes to `$S/t1_baseline.json`: `B` = `<P>/<N> passed, <F> failed, <R> not run` (N rows, R NOT_RUN), `M` its `macro/` rows, and its FAIL set (expected: `papers/test_debate_run_kills_process_tree` alone, as the container has no `taskkill`; any other FAIL is recorded with its detail and kept as part of `B`). `H` is the count of `python3 -B -m tests.macro_m0_harness`, 12 at `fa28059`; where a task writes `12/12` or `14/14`, read `H/H` and `H+2/H+2` if Task 1 Step 0 measures another `H`. The `nautilus` suite starts at 0 rows, so its counts are absolute. "Key unset" means `QUANTGEN_NAUTILUS_PYTHON` is not set (layer 2 NOT_RUN); "key set" means `QUANTGEN_NAUTILUS_PYTHON="$NTPY"` on the command line. A task's full run is correct when, compared row by row with `$S/t1_baseline.json` (Plan rules, Result files), it adds exactly the cumulative rows below with their statuses, removes none and changes none, so its FAIL set is `B`'s.

### Rows per task

| After | Tests added (layer 1 + layer 2) | `nautilus` rows (L1 + L2), absolute | `macro` rows | This task's delta, full suite, key unset (rows / PASS / FAIL / NOT_RUN) | Full suite, key unset (wrapper), cumulative | `--suite nautilus`, key unset | `--suite nautilus`, key set |
|---|---|---|---|---|---|---|---|
| Baseline (Task 1 Step 0) | - | 0 | M | - | `B` = `<P>/<N> passed, <F> failed, <R> not run` | 0 rows (suite absent) | - |
| Task 1 | 8 + 4 in `tests/nautilus_acceptance.py`, not yet registered | 12 (8 + 4), run only by `python3 -B -m tests.nautilus_acceptance` | M | +0 / +0 / +0 / +0 | `B`, row for row | module CLI: `8/12 passed, 0 failed, 4 not run` | module CLI: `12/12 passed, 0 failed, 0 not run` |
| Task 2 | 1 + 0 in `nautilus`; 2 in `tests/macro_m0_harness.py` | 13 (9 + 4) | M + 2 | +15 / +11 / +0 / +4: 13 `nautilus` rows (9 PASS, 4 NOT_RUN) and 2 `macro` PASS | `<P+11>/<N+15> passed, <F> failed, <R+4> not run` | `9/13 passed, 0 failed, 4 not run` | `13/13 passed, 0 failed, 0 not run` |
| Task 3 | 2 + 3 | 18 (11 + 7) | M + 2 | +5 / +2 / +0 / +3 | `<P+13>/<N+20> passed, <F> failed, <R+7> not run` | `11/18 passed, 0 failed, 7 not run` | `18/18 passed, 0 failed, 0 not run` |
| Task 4 | 21 + 3 | 42 (32 + 10) | M + 2 | +24 / +21 / +0 / +3 | `<P+34>/<N+44> passed, <F> failed, <R+10> not run` | `32/42 passed, 0 failed, 10 not run` | `42/42 passed, 0 failed, 0 not run` |
| Task 5 | 12 + 3 | 57 (44 + 13) | M + 2 | +15 / +12 / +0 / +3 | `<P+46>/<N+59> passed, <F> failed, <R+13> not run` | `44/57 passed, 0 failed, 13 not run` | `57/57 passed, 0 failed, 0 not run` |

The `--suite nautilus` columns hold for the wrapper (from Task 2 on) and for the module CLI, which collects the same rows. Reference example only: the same rows in absolute numbers, as measured on 2026-10-26 at `b7f991a`, before ②-1 and PT-07 (`B` = `745/870 passed, 1 failed, 124 not run`, `M` = 542):

| After | Tests added (layer 1 + layer 2) | `nautilus` rows (L1 + L2) | `macro` rows | Full suite, key unset (wrapper) | `--suite nautilus`, key unset | `--suite nautilus`, key set |
|---|---|---|---|---|---|---|
| Baseline (`b7f991a`) | - | 0 | 542 | 870: `745/870 passed, 1 failed, 124 not run` | 0 rows (suite absent) | - |
| Task 1 | 8 + 4 in `tests/nautilus_acceptance.py`, not yet registered | 12 (8 + 4), run only by `python3 -B -m tests.nautilus_acceptance` | 542 | 870: `745/870 passed, 1 failed, 124 not run` (unchanged) | module CLI: `8/12 passed, 0 failed, 4 not run` | module CLI: `12/12 passed, 0 failed, 0 not run` |
| Task 2 | 1 + 0 in `nautilus`; 2 in `tests/macro_m0_harness.py` | 13 (9 + 4) | 544 | 885: `756/885 passed, 1 failed, 128 not run` | `9/13 passed, 0 failed, 4 not run` | `13/13 passed, 0 failed, 0 not run` |
| Task 3 | 2 + 3 | 18 (11 + 7) | 544 | 890: `758/890 passed, 1 failed, 131 not run` | `11/18 passed, 0 failed, 7 not run` | `18/18 passed, 0 failed, 0 not run` |
| Task 4 | 21 + 3 | 42 (32 + 10) | 544 | 914: `779/914 passed, 1 failed, 134 not run` | `32/42 passed, 0 failed, 10 not run` | `42/42 passed, 0 failed, 0 not run` |
| Task 5 | 12 + 3 | 57 (44 + 13) | 544 | 929: `791/929 passed, 1 failed, 137 not run` | `44/57 passed, 0 failed, 13 not run` | `57/57 passed, 0 failed, 0 not run` |

`python3 -B -m tests.macro_m0_harness`: `H/H passed, 0 failed, 0 not run` (`12/12` at `fa28059`) before Task 2, `H+2/H+2 passed, 0 failed, 0 not run` (`14/14`) from Task 2 on. On the owner's Windows run of record (Step 7A and Step 10) the `nautilus` rows are all PASS with the key set, L2-5b the only `nautilus/*` NOT_RUN allowed (spec Step 7A done-when); those counts go into the README at Step 10, not in this plan.

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


## Plan rulings

Contract issues raised by Task 1
- **T1 CI 1.** Ruling: C2 gains `launch.PARENT_NAUTILUS_REMEDY`: R-03's three parent lines from spec 7, joined by "\n". L1-22 asserts it, and Task 4's `check_venv` passes it as the remedy. `VENV_FIX`, `STORE_FIX` and `PINNED` join C2 too, because Task 4 consumes `VENV_FIX`. - cost if wrong: low. A second, hand-typed copy could drift from spec 7's text without L1-22 noticing.
- **T1 CI 2.** Ruling: `launch.CREATE_NEW_PROCESS_GROUP = 0x00000200`. `build_launch` splits and joins paths with `ntpath` for os_name "nt" and with `posixpath` otherwise, and `venv_python` may be any PurePath. - cost if wrong: low. 0x200 is the Win32 value that `subprocess.CREATE_NEW_PROCESS_GROUP` carries, and L1-16 asserts the nt kwargs on Linux. A wrong value would first show at Step 7A, when L2-10's tree kill fails.
- **T1 CI 3.** Ruling: the Store-Python test is a case-insensitive substring test, with either slash, on the `home` and `executable` strings that pyvenv.cfg records. Only the equality with `parent_base_executable` compares `normcase(realpath)`. - cost if wrong: a Store-made venv whose recorded strings avoid both substrings passes this one check (UNVERIFIED until Step 7A, where `--check-env` and the egress record must still pass). The other reading could refuse a correct venv on the owner's machine.
- **T1 CI 4 (with T2 CI 7).** Ruling: every full-suite count in the Count Ledger is now a delta from `B`, which Task 1 Step 0 re-measures. `M` is the macro row count and `H` the harness count. `nautilus` counts stay absolute, and the 2026-10-26 table stays as a reference example. The deltas (rows/PASS/FAIL/NOT_RUN) are: Task 1 +0; Task 2 +15/+11/+0/+4; Task 3 +5/+2/+0/+3; Task 4 +24/+21/+0/+3; Task 5 +15/+12/+0/+3; cumulative +59/+46/+0/+13. - cost if wrong: low. A wrong delta shows up as a mismatch in the task's row diff and stops its commit.
- **T1 CI 5.** Ruling: "byte-identical" for `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` means identical to Task 1 Step 0's sha256, which is after ②-1's `6054b33`. The "Unchanged on purpose" paragraph names ②-1. - cost if wrong: none for this plan. A dependency change slipped in between Step 0 and Task 1 would not be seen, but none is pending.
- **T1 CI 6 (with T2 CI 6).** Ruling: three rules are updated. Plan status now says the spec and plan are committed and the dry runs have happened. The Commits rule has no pre-exempt path; Task 1 Step 0 records any that exist. The tag rule names the owner's real annotated tag `6e7c1f7` (it peels to `eacd57d`), which Claude never pushes, moves or deletes. The cloud-baseline paragraph keeps its numbers as a reference example. - cost if wrong: none.
- **T1 CI 7.** Ruling: rule A has three cases:
  - no collected node gives no hit;
  - exactly one qualifying `self.submit_order` call inside a method is exempt;
  - anything else keeps every hit and adds one A hit.

  Task 1's sandbox has no `place`, and Task 3 adds it; Task 2's `_rule_a` already behaves this way. This departs from spec 5.6's literal "Otherwise ... plus one A hit", which would flag a sandbox with no order call at all. All 51 controls in 8.5 contain `place`, so their measured multisets stand. The spec's next revision records the change. - cost if wrong: a sandbox with no order call passes the scan, and that grants no order path. The alternative, giving Task 1's sandbox a `place`, would FAIL T-RO-01 in the full suite between Task 1 and Task 2.
- **T1 CI 8.** Ruling: L1-15 decides whether a subprocess call is in text mode from its literal keywords only. `run_child`'s `**launch.popen_kwargs` is covered by L1-16, which asserts that the dict holds `text=True`, `encoding="utf-8"` and `errors="replace"`. There is no exemption list; Task 2's `encoding_offences` already behaves this way. - cost if wrong: a later text-mode call that passes its keywords through `**` without the encoding would escape L1-15. Only `run_child` uses that form.
- **T1 CI 9.** Ruling: L1-17 tests `%VAR%` on Windows and `$VAR` on POSIX, because `os.path.expandvars` expands per platform. No code changes; spec 8.3's next revision notes it. - cost if wrong: none. The Windows half runs at Step 7A.

Contract issues raised by Task 2
- **T2 CI 1 (with T3 CI 3).** Ruling: the Plan rules now hold one list of result-file names (Result files). The baseline is `$S/t1_baseline.json`, and each task keeps the names its steps already use. Task 3's proposed scheme, `$S/task<n>_full.json` for every task, is not adopted, because Tasks 1, 2 and 4 already name their files. Three changes follow:
  - Task 2 reads `t1_baseline.json` (three edits).
  - Task 3 reads `nb_task2_full.json` (two edits).
  - Task 5 adds a row diff against `t1_baseline.json`.

  A later session copies `run_baseline.py` and these files. - cost if wrong: a misnamed file makes a comparison command fail loudly; nothing is miscounted.
- **T2 CI 2.** Ruling: the Bridge text rule applies to `tests/nautilus_*.py`. `tests/macro_m0_harness.py`, the scanner, names the forbidden tokens in its constants, in the 8.5 controls and in the embedded 5.2.9 skeleton. - cost if wrong: none, because `tests/` is outside every scan.
- **T2 CI 3.** Ruling: L1-15 reads `launch.FIXTURES` and `launch.fixture_inputs` through `getattr`. At Task 2 it checks the committed bridge CSVs; once Task 3 adds the fixtures, it checks every fixture's bytes for `\r`. The `lineterminator` rule covers the runner's bars.csv statically. - cost if wrong: low. A CR in the runner's bars.csv would also break the sandbox's own line-end rule (exit 20), which the rehearsal runs would show.
- **T2 CI 4.** Ruling: C1 accepts `newline=""` for a file that a csv writer writes with `lineterminator="\n"`, and L1-15 accepts either constant. This departs from the literal `newline="\n"` of spec 3.7, but writes the same LF bytes. - cost if wrong: none in bytes. A reader who holds 3.7 literally will see the stub's `newline=""`.
- **T2 CI 5.** Ruling: C2 and C3 now state what Task 1's files avoid under rules A to F. Outside the sandbox, nothing imports `nautilus_trader`. No file uses a denied name. The parent checks use `importlib.metadata` only. Task 1's sandbox has no `submit_order` node. - cost if wrong: Task 2's T-RO-01 test fails on Task 1's code, and its Step 8 then says to fix that file, not the rules.
- **T2 CI 6.** See T1 CI 6.
- **T2 CI 7.** See T1 CI 4.
- **T2 CI 8.** Ruling: in C8, a FAIL's detail is `f"{type(exc).__name__}: {exc}"` and a NOT_RUN's is the NotRun reason, as in `tests/run_all.py:117-120`. - cost if wrong: none; RED texts would only read differently.

Contract issues raised by Task 3
- **T3 CI 1.** Ruling: from Task 3 on, an exit 20 writes no file, and the last stderr line is `C-05: <reason>`. The reason is either `input refused: <rule>` or the `--in` rule. The sandbox prints the line with `argparse.ArgumentParser.exit(20, ...)`. Only these two lines of 5.2.9's `main` change, because 5.2.9 governs structure and section 7 says C-05 goes to stderr only. Task 1's `run` stays silent. - cost if wrong: if the owner wants 5.2.9's `main` kept verbatim, the two lines are removed, and L2-5a falls back to checking the exit code and that no file was written, so it no longer knows which rule refused.
- **T3 CI 2.** Ruling: C8 lists Task 3's shared names; Tasks 4 and 5 may use them but never redefine them. Checked: no module-level name in `tests/nautilus_acceptance.py` is defined by two tasks. - cost if wrong: a silent rebinding would change Task 3's tests; none exists.
- **T3 CI 3.** See T2 CI 1.
- **T3 CI 4.** Ruling: C5 fixes the fixtures' ledger hash as `gate_ledger.ledger_hash([])` = `d751713988987e9331980363e24189ce`, the md5 of "[]". Task 3 pins it as `EMPTY_LEDGER_HASH` and asserts it against the function. - cost if wrong: none, because the test computes it from the function.

Contract issues raised by Task 4
- **T4 CI 1.** Ruling: registration tables are exempt from C1's sorted JSON bytes and keep their key order. Tests write temp tables with `json.dumps(t, indent=1, ensure_ascii=False) + "\n"`. The two committed tables are Task 5's exact bytes, one key per line, not that dump. `table_sha256` sorts keys, so key order never changes a digest. - cost if wrong: a table re-saved with `sort_keys` is refused R-11 at step 1 (measured), before registration, so it can never register in the wrong order.
- **T4 CI 2.** Ruling: `check_p0a`'s `arrays` also carry `symbol` and `start`. It returns the Panel that `study.panel` built, and `run()` stores it in `RunContext.study_pn` for P0b. - cost if wrong: none. The old signature could not call `study.panel` at all.
- **T4 CI 3.** Ruling: `record_baseline` gains `python: str | None = None`. `--record-baseline` passes the `python` that `--check-env` reports, and L1-35 passes it explicitly. - cost if wrong: the census file would name the parent's Python. On Linux that equals the venv's 3.13.17; on Windows it may not.
- **T4 CI 4.** Ruling: `parity.hard_pass` is one bool. It is true only when every hard check (P0b, P1 to P4, P7, P12, P13) passed for every column at both cost levels and no G-03 arose. `e1_parity_passed` accepts an of-record E1-SPY record that has `hard_pass` true, 12 rows and this `code_sha256`, whatever its status; a WITHHELD for G-02 counts, as L1-19 asserts. - cost if wrong: pilot 2 could start after a pilot 1 that was withheld for a decision mismatch. The spec's precondition names parity, not the verdict, so this reading follows the spec.
- **T4 CI 5.** Ruling: C8 lists Task 1's `_refused` and `_invalid` with their signatures. - cost if wrong: none.

Contract issues raised by Task 5
- **T5 CI 1.** Ruling: `parity.corr` counts two constant series that agree to within 1e-12 as 1.0. Any other constant case is NaN, which fails. Every other pair goes through `np.corrcoef`. This departs from P2's literal Pearson, which is undefined for a column that never trades when rf is 0 (pilot 2). `validate.sharpe` gives 0.0 for both series, so P3 passes there. - cost if wrong: none, because two identical constant series are exact agreement.
- **T5 CI 2.** Ruling: `parity.card_rules(table, stub_child=...)` builds 6.5's rules, with engine "STUB" when a stub child ran (5.3.1). L1-30 asserts both the stub card and the non-stub engine text, and L2-7 asserts the engine text of a card from the real sandbox. - cost if wrong: none.
- **T5 CI 3.** Ruling: `--fingerprint` behaves as follows:
  - As soon as the table parses, it prints both digests.
  - It then validates the table against 6.6, with the owner fields optional. A failure prints the R-11 refusal and exits 2.
  - A valid table exits 0, with or without a host fingerprint.
  - A table that is not JSON is R-11, and no digest is printed.

  The spec says "exits 0 when both digests are printed", but the same sentence asks the mode to validate the table. The exit-0 clause is therefore read as applying to a table that validates. - cost if wrong: the owner's 7A.2 block stops at an invalid committed table and skips to `--handoff-report` instead of continuing. Such a table could never run of-record anyway.
- **T5 CI 4.** Ruling: the format of withheld reasons goes into C1:
  - a P13 leg keeps its C id first, with the column and cost level appended;
  - a failed parity check starts with its P id;
  - G-02, G-03, G-05 and G-08 reasons start with their prefix, followed by 6.3's literal texts;
  - G-04 goes into `record["error"]`.

  - cost if wrong: Task 4's re-run policy would misread a reason. With this format, a WITHHELD whose reasons are all C-06 stays re-runnable, as 5.3.5 says.
- **T5 CI 5.** Ruling: C8 and C10 list the Task 4 internals that Task 5 calls and the behaviour it relies on, so Task 5's four Edit anchors in `runner.py` stay valid. Checked: Task 5's old strings are Task 4's text verbatim. They are the docstring line, the "which plan Task 5 fills" sentence, the `parity_and_gate` body and Task 4's whole `main`. - cost if wrong: an Edit anchor misses, and Task 5 stops at Step 5 or Step 7 before making any wrong change.
- **T5 CI 6.** Ruling: the hand-off report's `stub_interpreter` part imports `tests.nautilus_acceptance.stub_python` inside that part only. That is an import statement, not import machinery, so rule E does not apply, and rule C2 judges only `nautilus_trader` names. - cost if wrong: the part records its own import error, and the report is still written.

Cross-task decisions
- **X1 (letters).** Ruling: `B` = `<P>/<N> passed, <F> failed, <R> not run`, where N is the number of rows and R the number of NOT_RUN. `M` is the macro row count and `H` the harness count. Task 2's harness "M" becomes `H` (four edits), and Task 3's swapped R and N now match Tasks 1, 2 and 5 (one edit). - cost if wrong: confusion only.
- **X2 (earlier Task 3 draft).** Ruling: Tasks 4 and 5 were dry-run on a clone that carried an earlier Task 3 draft:
  - its sandbox lacked `write_outputs`, but behaved identically;
  - its test block had the same five test names, lacked `ORDER_CALL` and `_check_env_precision`, and had `_refused_before_engine(label, result, out)`.

  Checked: no Task 4 or Task 5 line uses any of the differing names, and no output, golden or census depends on the refactor. Task 4 now says so. Task 5's md5 claims for `tests/nautilus_acceptance.py` become a numstat check: 619 insertions, 0 deletions. - cost if wrong: a hidden dependency would show as a RED or GREEN mismatch during execution and stop that task before its commit.
- **X3 (guard root).** Ruling: nothing writes under `docs/nautilus_bridge/` while a nautilus run or a full run is in progress. That folder is a 3.3 guard root, and it now holds the owner-rulings log and the progress chart. - cost if wrong: a rulings-log update during a run FAILs a guarded test and L1-32. That is a false alarm costing one re-run.
- **X4 (Task 5 row diff).** Ruling: Task 5 Step 14 gains a row diff against `t1_baseline.json`, as every other task's full run has. It expects 59 rows added (46 PASS, 13 NOT_RUN, 2 of them macro), none removed and none changed. - cost if wrong: none.
- **X5 (H).** Ruling: `H` is re-measured at Task 1 Step 0; it is 12 at `fa28059`, and PT-07 adds no harness test. If it differs, each task's 12/12 and 14/14 read as H/H and H+2/H+2. - cost if wrong: none.
- **X6 (file ownership).** Ruling: the File Structure table now names the exact anchors:
  - `tests/nautilus_acceptance.py`: Task 2 inserts before `def tests(`; Tasks 3, 4 and 5 insert above `# CLI`, in that order.
  - `launch.py`: Task 3 appends after `cleanup_tempdir`.
  - `sandbox.py`: Task 3 rewrites the whole file; of Task 1's definitions, only `run` and `main` change.
  - `runner.py`: Task 5 edits at its four anchors.

  Checked: each anchor is unique at the point its task runs. - cost if wrong: an Edit fails loudly.
- **X7 (checks, no ruling needed).** Every consumed symbol is produced by an earlier task with the same signature:
  - Task 2 consumes Task 1's three files and C8.
  - Task 3 consumes C2, C8's `ROOT`, `layer2` and `tests`, and Task 2's `_offences`.
  - Task 4 consumes C2, including `VENV_FIX`, `PARENT_NAUTILUS_REMEDY`, `fixture_inputs` and the zero-argument `on_started`, which Task 4 wraps as `lambda: hook(lc)`. It also consumes C8's `_refused` and `_invalid`.
  - Task 5 consumes C10's `run`, hooks, `RunContext`, `Leg`, `Outcome`, `rebuild_returns` and the internals list.

  The counts in every task's GREEN steps equal the Count Ledger.
- **Spec deviations to record** in the Step 10 execution record and in the spec's next revision: T1 CI 7, T1 CI 9, T2 CI 4, T3 CI 1, T5 CI 1 and T5 CI 3.

## Coverage

| Spec step | Done-when item (spec section 9) | Task and step |
|---|---|---|
| 3 | The file pins 5.1's 16 distributions with hashes | Task 1 Step 6 (header plus closure body; sha256 checked); `test_px_requirements_nautilus_pins_and_header` (Steps 2, 13) |
| 3 | `pip install --require-hashes --only-binary=:all: --no-cache-dir -r requirements-nautilus.txt` succeeds in a fresh scratch venv, and `pip check` is clean | Task 1 Step 6 (offline install into `$S/ntvenv_t1`, `pip check`); Step 13 (the 4 layer-2 tests against that venv) |
| 3 | `launch.py`'s identity read gives `a448cd20...` with 764 entries | Task 1 Step 14 (`identity` line); L1-17 on the RECORD fixtures; L2-1 (Step 13) |
| 3 | Under `unshare -rn`, `--check-env` reports Python 3.13.x, `HIGH_PRECISION` true and environment `BACKTEST` | Task 1 Step 14; L2-1 (Steps 12, 13) |
| 3 | `--guard-selftest` exits 0 | Task 1 Step 14; L2-8 (Steps 12, 13) |
| 3 | The probe reports `blocked: true` | Task 1 Step 14; L2-9 (Step 11) |
| 3 | The global interpreter still reports numpy 2.3.5, pandas 2.3.3, scipy 1.18.0 and no `nautilus_trader` | Task 1 Steps 0 and 14; L1-22 |
| 3 | `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` are byte-identical | Task 1 Step 0 (sha256), Steps 14 and 17 (`sha256sum -c`; ruling T1 CI 5); `test_px_requirements_nautilus_pins_and_header` (no `nautilus` or `pyarrow` in them) |
| 4 | Both new tests pass | Task 2 Step 6, and Step 7 (`14/14`) |
| 4 | Every control of 8.5 gives exactly its multiset | Task 2 Step 6 (`test_t_ro_01_nautilus_confined_to_the_sandbox`, 51 controls) |
| 4 | The real tree and the real sandbox give no hit | Task 2 Step 6 (same test), Step 8 (`0 hits`); re-checked at Task 3 Step 9, Task 4 Step 9 and Task 5 Step 13 |
| 4 | test_08 and test_09 are unchanged and pass | Task 2 Step 8 (`git diff --exit-code`, direct run), Step 15 (`changed []`) |
| 4 | `python -m tests.macro_acceptance` has resynced row 12, and `test_registry_implemented_in_matches_test_ids` passes | Task 2 Step 7 |
| 4 | L1-15, L1-16, L1-17, L1-22 and L1-32 pass | Task 2 Steps 10 and 13 (L1-15 is written at Steps 9 and 10; the others come from Task 1) |
| 4 | Through the wrapper, `--suite nautilus` reports its layer-2 tests NOT_RUN, not PASS, with the key unset | Task 2 Step 13 (`9/13 passed, 0 failed, 4 not run`) |
| 4 | The README Total row is unchanged | Task 2 Step 14 (the Total count in the diff is 0) |
| 5 | `launch.fixture_inputs` builds F1, F1r, F2 and N1 | Task 3 Steps 4 and 5 (`test_px_fixture_inputs_follow_6_1_and_8_2`) |
| 5 | In the Linux venv under `unshare -rn`, L2-1, L2-4, L2-5a, L2-5b and L2-8 to L2-10 pass | Task 3 Steps 7 and 9 (`18/18` with the key set), Step 10 (wrapper with the key set) |
| 5 | No code path uses `AT_THE_CLOSE`, `allow_cash_borrowing=True`, `LatencyModel`, the `PortfolioAnalyzer` or a report as equity | Task 3 Step 7 (`test_px_sandbox_avoids_excluded_constructs`, mutation-checked) |
| 5 | The real sandbox gives no scan hit | Task 3 Step 9 (`macro_m0_harness` `14/14`); `_offences(SANDBOX) == []` inside the px test |
| 5 | Layer-2 tests report NotRun without the venv | Task 3 Step 9 (`11/18 passed, 0 failed, 7 not run`), Step 10 (wrapper) |
| 6 | L1-1, L1-3, L1-4, L1-6 to L1-12, L1-16 to L1-19, L1-20's P0a cases, L1-22 to L1-27 (L1-26 without its G-05 case) and L1-33 to L1-35 pass | Task 4 Step 8 (`32/42` with the key unset, `42/42` with it set; L1-16, L1-17 and L1-22 come from Task 1), Step 9 (wrapper) |
| 6 | `--write-goldens` has written F1, F2 and N1 | Task 4 Step 5 |
| 6 | `--record-baseline` has written `modules_manylinux_2_35_x86_64.json`, the union of the F1 and F2 censuses | Task 4 Step 6 |
| 6 | L2-2, L2-3 and L2-6 pass | Task 4 Steps 5, 6 and 8 |
| 6 | On F1 and F1r, the rebuilt R matches 8.2 to 1e-7 | L1-1 (Task 4 Steps 2 and 8) |
| 6 | The run record carries the post-registration ledger hash, both data md5s, the venv reads and every child manifest | Task 4 Step 7 (record of a real-venv rehearsal); L1-3 (with the stub) |
| 7 | L1-2, L1-5, L1-13, L1-14, L1-20's P0b case, L1-21, L1-26's G-05 case, L1-28 to L1-31 and L1-36 pass | Task 5 Step 6 and Step 10 (`44/57`, `57/57`), Step 14 (wrapper) |
| 7 | L2-7, L2-11 and L2-12 pass | Task 5 Step 10 |
| 7 | `GATE` is unchanged after every run | L1-14 (Task 5 Step 10); `hand_off`'s G-04 comparison after every hand-off (Step 4) |
| 7 | N6 reports its worst corr and abs ΔSR next to the bars and map 03's | The line L2-11 prints (Task 5 Step 10), kept for the execution record |
| 7 | Real-data parity evidence stays map 03's and is never repeated | Global Constraints (Step 2 additions; 3.9); every Task 5 run uses synthetic data; Step 12's `--fingerprint` opens no data file (L1-36) |
| 7 (what) | Both pilot tables without their owner fields; `RUNBOOK_windows.md` | Task 5 Steps 9 and 11; L1-30 asserts that neither table has an owner field; Step 11's script checks the runbook's block against 7A.2 |

## Tasks

---

### Task 1: Environment (spec Step 3): requirements, venv reads, launch contract, sandbox self-checks, egress probe, suite skeleton

**Verified before writing (2026-10-28, at HEAD `fa28059`, in scratch clones `$S/plan_step2/task1/clone*` only; the real clone was not touched):**
- HEAD `fa28059` follows `6054b33` (②-1: `statsmodels>=0.14.2` at `requirements.txt:10`); the working tree is clean; `md5sum qa/acceptance_results.json` prints `16c9baa5a1777853521d485d5078e456`; `studies-of-record-2026-10-23` is the owner's real annotated tag (`git cat-file -t` prints `tag`; it peels to `eacd57d`, `tests/frozen_guard.py:31-32`).
- `config.py:25-29` loads `.env` at import; `config.py:32-39` `_clean` strips one pair of quotes and blanks an unedited `<placeholder>`; `config.py:176-178` `macro_dir()` reads `QUANTGEN_MACRO_DIR` on every call. Hence `launch.venv_key()` is `import config; config._clean(KEY)`, and `guard_roots()` resolves `config.macro_dir() / "ledgers"` before any guard moves the variable.
- `tests/notrun.py:19-20` (`MANIFEST_COLUMNS`), `:25-30` (`NotRun`), `:49-65` (`load_manifest`), `:68-79` (`require_fixture(name, *, manifest=...)`: NotRun when a file is unlisted, absent or off its md5). The nautilus fixtures get their own `MANIFEST.csv` with that header.
- The unamended T-RO-01 scan already reads `tools/` (`tests/macro_m0_harness.py:63` `SCAN_TREES = ("tools", "papers")`, `:66-70`) with `submit_order` in `FORBIDDEN_TEXT_CI` (`:28-33`) and `FORBIDDEN_CALLS` (`:44-50`), case-sensitive `CANO` (`:35`), on code with docstrings and comments stripped (`tests/acceptance.py:33-46`). So Task 1's `sandbox.py` is spec 5.2.9 without the port classes and without `place`: its `self.submit_order` line would fail T-RO-01 until Task 2's amendment, and Task 3 adds it. With the four new `tools/nautilus/*.py` files, `python3 -B -m tests.macro_m0_harness` gave `12/12 passed, 0 failed, 0 not run` and `_offences` returned `[]` for each. `tests/` is outside the scan. test_08 and test_09 (`tests/acceptance.py:62-75`) read only `runtime_py()` (`:50-55`: `core/`, `data/`, `ui/`, `main.py`, `config.py`), which Task 1 does not touch; no flet file changes, so `tests/flet_api_guard.py` is not concerned.
- `tests/run_all.py` (CRLF) is not edited at Task 1: its `run` (`:110-125`) prints `"<STATUS> <name> <detail>"` and its `main` (`:128-142`) writes `OUT`. The new module's own CLI prints the same rows and the summary of `tests/macro_acceptance.py:237-264` (`run_module`), and writes nothing. No suite test reads the working tree's git status (git is read only for commits and tags), so the full run before the commit is valid with the task's files uncommitted.
- `tests/macro_acceptance.py:26-27` snapshots `tests/fixtures/macro`, not `tests/fixtures/nautilus`; `:113-130` (`home_listing`) adds `QUANTGEN_MACRO_DIR` when it is set, which is why the nautilus guard restores it in `finally`.
- `.env.example` is LF, 44 lines, the last `NEXTGEN_NO_DATA_GRACE=3`; its section headings are `# --- <name> ` padded with `-` to 78 or 79 characters. python-dotenv 1.2.3 (the global interpreter's) reads `K='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'` as written and turns the `\n` of `K="C:\Users\o\ntvenv\Scripts\python.exe"` into a newline (measured; spec 3.4).
- `.gitattributes` is `* -text`; `git check-ignore` matches none of the new paths (exit 1). `tools/__init__.py` exists. `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` contain neither `nautilus` nor `pyarrow`.
- `$NTPY`: Python 3.13.17; `pyvenv.cfg` `home = /usr/bin`, `include-system-site-packages = false`, `version = 3.13.17`, `executable = /usr/bin/python3.13`; `bin/python -> python3 -> /usr/bin/python3`, so `resolve_venv_python` keeps the unresolved path and `read_venv` finds the root from it. `/usr/bin/unshare -rn true` exits 0; under it the probe's connect fails with errno 101.
- Wheel identity by 6.7's rule, recomputed from both wheels in `$S/closure/`: `Tag: cp313-cp313-manylinux_2_35_x86_64`, `a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9`, 764 entries (the same from `$NTPY`'s installed `RECORD`); `Tag: cp313-cp313-win_amd64`, `47d274d79b85a43b79917e9b993fa3e68ebf68138c4a8b86527c5902cf439555`, 764. The `nautilus_trader-1.231.0.dist-info/RECORD` members are LF: 80,255 bytes, md5 `bf0dd9ec1cce4d6b67771d372ced5dfc` (Linux); 78,902 bytes, md5 `9cb7bcf1fd8ecd9f6f3d7f3b430f1d0e` (Windows). The wheel files' sha256s equal spec 5.1's PyPI hashes.
- `$S/closure/requirements-nautilus.body.txt`: 37 lines, ASCII, LF, sha256 `49c1cee13798cbc92104bd398af422f611334db1f79260231c0c357fd7d0b5e4`. Header plus body: 43 lines, sha256 `7a720e247bf1a5708aa19e79c1291b6baef87c837719c669ebe5f24e4a4a7e0e`. Its offline `--require-hashes` install into a fresh venv took 24 s; `pip check` printed `No broken requirements found.`; the 4 layer-2 tests pass against that venv too.
- `--check-env` on Linux printed `HIGH_PRECISION` true, `FIXED_PRECISION` 16, `QUANTITY_MAX` 34028236692093.0, `PRICE_MAX` 17014118346046.0, `environment` `BACKTEST`, one stdout line, empty stderr. The win_amd64 values in L2-1's table (9, 18446744073.0, 9223372036.0) are the comments of that wheel's `core/rust/model.pxd` (`scratch:critic_win/`), UNVERIFIED until Step 7A, where a mismatch is a FAIL (spec 3.6).
- The task was dry-run in that order in scratch clones of `fa28059`: every RED and GREEN output below is the observed one, with the paths of the real clone. Through the launch contract, Task 1's `run --in <tmp>` exited 20 with an import census of 942 names (spec 5.4.3: 942). A key-set module run took 6 to 20 s; L2-10 takes about 3 s.

**Files:**
- Create: `tools/nautilus/__init__.py` (0 bytes), `tools/nautilus/launch.py`, `tools/nautilus/egress_probe.py`, `tools/nautilus/sandbox.py` (Task 1 part), `tools/nautilus/golden/env_pins.json`, `requirements-nautilus.txt`, `tests/fixtures/nautilus/MANIFEST.csv`, `tests/fixtures/nautilus/nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD`, `tests/fixtures/nautilus/nautilus_trader-1.231.0.win_amd64.RECORD`, `docs/nautilus_bridge/.gitignore`. All new files are ASCII with LF line ends.
- Modify: `.env.example` (LF; append after line 44, Edit tool).
- Test: `tests/nautilus_acceptance.py` (new; 8 layer-1 and 4 layer-2 tests), run only by its module CLI until Task 2 registers suite `nautilus`.
- Not touched (checked at Steps 14 and 17 against Step 0's sha256): `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`, `tests/run_all.py`, `README.md`; also `qa/acceptance_results.json` (md5).

**Interfaces:**
- Consumes: `config._clean`, `config.macro_dir` (`config.py:32-39, 176-178`); `tests.notrun.NotRun`, `require_fixture` (`tests/notrun.py:25-30, 68-79`); `dotenv.dotenv_values` (the global interpreter's python-dotenv, test only); `$NTPY` and the wheels in `$S/closure/`.
- Produces, by Interface Contract name: C1 (`BridgeRefusal`, `ChildInvalid`; the JSON-bytes rule for `env_pins.json`; platform and host tags; PEP 503 keys); C2, all of it except `FIXTURES` and `fixture_inputs` (Task 3); C3 for `--check-env` and `--guard-selftest`, and `run --in <dir>` exiting 20 for every input; C4; C7 (`env_pins.json`, both `RECORD` fixtures and `MANIFEST.csv`); C8's Task 1 block (`ROOT`, `FIXTURE_MANIFEST`, `LAST_TEST`, `guard_roots`, `digest_roots`, `guarded`, `layer2`, `tests`, the CLI).
- Produces beyond the contract as first drafted (C2 now lists the `launch` names, C8 `_refused` and `_invalid`; Plan rulings): `launch.PARENT_NAUTILUS_REMEDY` (CONTRACT ISSUE 1), `launch.CREATE_NEW_PROCESS_GROUP = 0x00000200` (CONTRACT ISSUE 2), `launch.PINNED`, `launch.VENV_FIX`, `launch.STORE_FIX`; `egress_probe.probe(host="1.1.1.1", port=443, timeout=3) -> dict`; test helpers `_refused`, `_invalid`, `_fake_venv`, `_launch_venv`, `_gone` and the module constants of `tests/nautilus_acceptance.py`.

**Counts (Count Ledger as deltas, CONTRACT ISSUE 4).** Step 0 measures the full-suite baseline `B` = `<P>/<N> passed, <F> failed, <R> not run`, with `M` macro rows and the FAIL set. Task 1's delta is 0 everywhere: the full suite through the wrapper stays `B` row for row (`nautilus` is not registered until Task 2; `macro` stays `M`); `python3 -B -m tests.macro_m0_harness` stays `12/12 passed, 0 failed, 0 not run`; the new module CLI gives `8/12 passed, 0 failed, 4 not run` with the key unset and `12/12 passed, 0 failed, 0 not run` with `QUANTGEN_NAUTILUS_PYTHON="$NTPY"` (absolute: the suite starts at 0). Reference example only: on 2026-10-26 at `b7f991a`, `B` was `745/870 passed, 1 failed, 124 not run`, `M` 542, FAIL set `papers/test_debate_run_kills_process_tree`.

Every command block below starts with the line `S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen` (a later session puts its own scratchpad in `S`); the blocks repeat it.

- [ ] **Step 0: Re-measure the baseline (no file changes).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git log -1 --format='%h %s'; git status --short; git cat-file -t studies-of-record-2026-10-23
md5sum qa/acceptance_results.json
sha256sum requirements.txt requirements-dev.txt pyproject.toml config.py tests/run_all.py README.md > "$S/t1_pre_sha256.txt"
python3 -c "import numpy, pandas, scipy, statsmodels; print(numpy.__version__, pandas.__version__, scipy.__version__, statsmodels.__version__)"
test -x "$NTPY" || { python3 -m venv "$S/ntvenv_hash" && "$NTPY" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$S/closure/linux" -r "$S/closure/requirements-nautilus.body.txt" && "$NTPY" -m pip check; }
"$NTPY" -I -c "import nautilus_trader, numpy, pandas; print(nautilus_trader.__version__, numpy.__version__, pandas.__version__)"
unshare -rn true && echo "unshare ok"
```
  Expected: the HEAD line (record it; `fa28059` or a later commit); `git status --short` lists the paths already modified or untracked (record them: Step 18 leaves them unstaged; empty at `fa28059`); `tag`; `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`; `2.3.5 2.3.3 1.18.0 0.15.0`; `1.231.0 2.3.5 2.3.3`; `unshare ok`. Then the full suite, through the wrapper only, started with the Bash tool's `run_in_background` (about 10 minutes; nothing else from QUANTGEN runs meanwhile, T-HERM-02):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B "$S/run_baseline.py" "$S/t1_baseline.json" > "$S/t1_baseline.log" 2>&1; echo "exit $?"
```
  When it has finished:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
tail -1 "$S/t1_baseline.log"; md5sum qa/acceptance_results.json
python3 - "$S/t1_baseline.json" <<'EOF'
import json, sys
from collections import Counter
rows = json.load(open(sys.argv[1], encoding="utf-8"))
c = Counter(r["status"] for r in rows)
print(f"B = {c['PASS']}/{len(rows)} passed, {c['FAIL']} failed, {c['NOT_RUN']} not run; M = {sum(r['test'].startswith('macro/') for r in rows)} macro rows; nautilus rows {sum(r['test'].startswith('nautilus/') for r in rows)}")
print("FAIL", sorted(r["test"] for r in rows if r["status"] == "FAIL"))
EOF
python3 -B -m tests.macro_m0_harness | tail -1
```
  Expected: the wrapper's last line `<P>/<N> passed, <F> failed, <R> not run; <path of t1_baseline.json>`; the md5 unchanged (`16c9baa5...`); the `B = ...` line (record `B`, `M` and the FAIL set in the task's execution notes; `nautilus rows 0`); `12/12 passed, 0 failed, 0 not run`. The expected FAIL set is `['papers/test_debate_run_kills_process_tree']` (no `taskkill` in the container). Any other FAIL is recorded with its detail as part of `B`: Task 1 does not fix it, and Step 16 requires the same row status. Every later count in this task is `B` plus the deltas above.

- [ ] **Step 1: Create the package marker.** Create `tools/nautilus/__init__.py` as an empty (0-byte) file.
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -c "import tools.nautilus; print('ok')"
```
  Expected: `ok`.

- [ ] **Step 2: Write the failing suite module.** Create `tests/nautilus_acceptance.py` with exactly this content (LF; md5 `e149f34c4a3d73aa5371c6a425c97f58`). Test names are the Count Ledger's; helpers never start with `test_`. L2-10 keeps spec 8.4's child (`<venv python> -I -c ... time.sleep(120)` through the launcher, timeout 3, back within 15 s, temp dir deletable) and adds a sleeping grandchild and a pid file, so the tree kill is checked on Linux too (`/proc`), where a live process does not block the deletion. L1-17's variable expansion uses `$VAR` on POSIX and `%VAR%` on Windows, as `os.path.expandvars` expands per platform (C2, spec 6.7).
```python
"""Suite `nautilus`: the NautilusTrader bridge (spec docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md).

Layer 1 runs in the global interpreter on synthetic inputs only. Layer 2 starts children in the hash-pinned venv
named by QUANTGEN_NAUTILUS_PYTHON, through the launch contract of tools/nautilus/launch.py (spec 4.3): NOT_RUN
when the key is blank or names a missing file, FAIL when the venv is off its pins (O15).

Every test runs inside `guarded` (spec 3.3): the production ledger dirs and docs/nautilus_bridge/ are digested
before and after, and QUANTGEN_MACRO_DIR names a fresh temp dir while the test runs. `tests()` returns every test
sorted by name, then LAST_TEST, which compares the digests taken when the suite started (L1-32).

    python3 -B -m tests.nautilus_acceptance [-k <substring>] ...    prints only; never writes qa/acceptance_results.json
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Sequence

from tests.notrun import NotRun, require_fixture
from tools.nautilus import launch

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_MANIFEST = ROOT / "tests" / "fixtures" / "nautilus" / "MANIFEST.csv"
LAST_TEST = "test_l1_32_every_test_guarded_and_ledgers_unchanged"
_ROOTS: tuple[Path, ...] | None = None
_SUITE_START: dict[str, str] | None = None


# --------------------------------------------------------------------------- #
# The guard of spec 3.3 and the layer-2 gate
# --------------------------------------------------------------------------- #
def guard_roots() -> tuple[Path, ...]:
    """Resolved once per process, at the first call, before any guard moves QUANTGEN_MACRO_DIR (spec 3.3)."""
    global _ROOTS
    if _ROOTS is None:
        import config
        _ROOTS = (Path.home() / ".nextgen" / "macro" / "ledgers", config.macro_dir() / "ledgers",
                  ROOT / "docs" / "nautilus_bridge")
    return _ROOTS


def digest_roots(roots: Sequence[Path]) -> dict[str, str]:
    """{path: md5 of its bytes} for every file under each root; an absent root adds nothing."""
    out: dict[str, str] = {}
    for root in roots:
        if root.is_file():
            out[str(root)] = hashlib.md5(root.read_bytes()).hexdigest()
        elif root.is_dir():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    out[str(path)] = hashlib.md5(path.read_bytes()).hexdigest()
    return out


def guarded(name: str, fn: Callable[[], None]) -> Callable[[], None]:
    """Digests the guard roots before and after `fn`; while it runs, QUANTGEN_MACRO_DIR names a fresh temp dir, and
    on Windows a layer-2 test keeps the machine awake (spec 5.7). The first call records the suite-start digests."""
    def run() -> None:
        global _SUITE_START
        roots = guard_roots()
        before = digest_roots(roots)
        if _SUITE_START is None:
            _SUITE_START = before
        saved = os.environ.get("QUANTGEN_MACRO_DIR")
        macro_tmp = tempfile.mkdtemp(prefix="qgnb_macro_")
        awake = os.name == "nt" and name.startswith("test_l2_")
        os.environ["QUANTGEN_MACRO_DIR"] = macro_tmp
        try:
            if awake:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            fn()
        finally:
            if awake:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)   # ES_CONTINUOUS
            if saved is None:
                os.environ.pop("QUANTGEN_MACRO_DIR", None)
            else:
                os.environ["QUANTGEN_MACRO_DIR"] = saved
            shutil.rmtree(macro_tmp, ignore_errors=True)
        after = digest_roots(roots)
        changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
        assert not changed, f"{name} changed guarded files (spec 3.3): {changed}"
    run.__name__ = name
    run.nautilus_guarded = True
    return run


def layer2() -> Path:
    """The venv python for a layer-2 test: NotRun on a blank key or a missing file; a FAIL off the pins (O15)."""
    value = launch.venv_key()
    if not value:
        raise NotRun("OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)")
    if not Path(os.path.expanduser(os.path.expandvars(value))).is_file():
        raise NotRun(f"OWNER: QUANTGEN_NAUTILUS_PYTHON points to a missing file: {value!r}")
    python = launch.resolve_venv_python(value)
    bad = launch.venv_mismatches(launch.read_venv(python))
    assert not bad, "the Nautilus venv is off its pins (O15): " + "; ".join(bad)
    return python


def tests() -> list[tuple[str, Callable[[], None]]]:
    """Every module-level test_* sorted by name, LAST_TEST excepted; then LAST_TEST. Each one guarded."""
    guard_roots()
    found = sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f) and n != LAST_TEST)
    return [(n, guarded(n, f)) for n, f in found] + [(LAST_TEST, guarded(LAST_TEST, globals()[LAST_TEST]))]


# --------------------------------------------------------------------------- #
# Helpers (never named test_*)
# --------------------------------------------------------------------------- #
def _refused(call: Callable[[], object], rid: str) -> launch.BridgeRefusal:
    try:
        call()
    except launch.BridgeRefusal as exc:
        assert exc.rid == rid and str(exc).startswith(f"{rid}: "), exc
        return exc
    raise AssertionError(f"no {rid} refusal")


def _invalid(call: Callable[[], object], cid: str) -> launch.ChildInvalid:
    try:
        call()
    except launch.ChildInvalid as exc:
        assert exc.cid == cid and str(exc).startswith(f"{cid}: "), exc
        return exc
    raise AssertionError(f"no {cid}")


def _fake_venv(root: Path, *, os_name: str, record: str, tag: str, versions: dict | None = None,
               cfg: dict | None = None) -> Path:
    """A venv-shaped dir: pyvenv.cfg, an empty python file and the dist-info files read_venv reads."""
    versions = {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3", **(versions or {})}
    lines = {"home": str(root.parent / "base"), "include-system-site-packages": "false", "version": "3.13.17",
             "executable": str(root.parent / "base" / "python3.13"), **(cfg or {})}
    minor = ".".join(lines["version"].split(".")[:2])
    if os_name == "nt":
        python, site = root / "Scripts" / "python.exe", root / "Lib" / "site-packages"
    else:
        python, site = root / "bin" / "python", root / "lib" / f"python{minor}" / "site-packages"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"")
    (root / "pyvenv.cfg").write_text("".join(f"{k} = {v}\n" for k, v in lines.items()), encoding="utf-8",
                                     newline="\n")
    for name, version in versions.items():
        info = site / f"{name}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n\nVersion: 0.0\n",
                                       encoding="utf-8", newline="\n")
    info = site / f"nautilus_trader-{versions['nautilus_trader']}.dist-info"
    (info / "WHEEL").write_text(f"Wheel-Version: 1.0\nRoot-Is-Purelib: false\nTag: {tag}\n", encoding="utf-8",
                                newline="\n")
    (info / "RECORD").write_text(record, encoding="utf-8", newline="\n")
    return python


def _launch_venv(python: Path, mode_args: list[str], *, script: Path = launch.SANDBOX,
                 timeout: float = launch.TIMEOUT_S) -> launch.ChildResult:
    tmp = launch.make_tempdir()
    try:
        child = launch.build_launch(mode_args, tempdir=tmp, venv_python=python, unshare=launch.resolve_unshare(),
                                    script=script)
        result = launch.run_child(child, timeout=timeout)
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert left == [], left
    return result


def _gone(pid: int) -> bool:
    """Linux: True when the process has exited (no /proc entry, or a zombie nobody has reaped yet)."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return True
    return stat.rsplit(")", 1)[1].split()[0] == "Z"


# --------------------------------------------------------------------------- #
# Plan Task 1 (spec Step 3): layer 1
# --------------------------------------------------------------------------- #
LINUX_RECORD = "nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD"
WIN_RECORD = "nautilus_trader-1.231.0.win_amd64.RECORD"
LINUX_IDENTITY = ("a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9", 764)
WIN_IDENTITY = ("47d274d79b85a43b79917e9b993fa3e68ebf68138c4a8b86527c5902cf439555", 764)
PINS_JSON = {"schema": "nautilus-bridge-env-pins/1",
             "platforms": {"manylinux_2_35_x86_64": {
                               "python_minor": "3.13",
                               "versions": {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"},
                               "wheel_tag": "cp313-cp313-manylinux_2_35_x86_64",
                               "record_digest_sha256": LINUX_IDENTITY[0], "record_entries": 764},
                           "win_amd64": {
                               "python_minor": "3.13",
                               "versions": {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"},
                               "wheel_tag": "cp313-cp313-win_amd64",
                               "record_digest_sha256": WIN_IDENTITY[0], "record_entries": 764}}}
EXPECTED_VERSIONS = {"nautilus-trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"}
REQ_HEADER = (
    "# QUANTGEN NautilusTrader bridge: a research-only backtest engine, run only as a subprocess (spec 2026-10-26).",
    "# NEVER install with the global python: tests/frozen_guard.py clause (d) pins numpy 2.3.5, scipy 1.18.0 and",
    "# pandas 2.3.3, and tests/nautilus_acceptance.py fails while nautilus_trader is importable there.",
    "# Install only into the dedicated venv (spec section 4.4), never created with --system-site-packages:",
    r'#   cmd:        "%LOCALAPPDATA%\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes'
    r' --only-binary=:all: --no-cache-dir --no-index --find-links "%LOCALAPPDATA%\quantgen\wheels"'
    r' -r requirements-nautilus.txt',
    r'#   PowerShell: & "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes'
    r' --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels"'
    r' -r requirements-nautilus.txt',
)
REQ_PINS = {   # spec 5.1: name -> (version, environment marker, number of --hash lines)
    "click": ("8.5.0", "", 1), "colorama": ("0.4.6", 'sys_platform == "win32"', 1), "fsspec": ("2026.2.0", "", 1),
    "msgspec": ("0.22.0", "", 2), "nautilus-trader": ("1.231.0", "", 2), "numpy": ("2.3.5", "", 2),
    "pandas": ("2.3.3", "", 2), "portion": ("2.6.3", "", 1), "pyarrow": ("26.0.0", "", 2),
    "python-dateutil": ("3.0.0", "", 1), "pytz": ("2026.5", "", 1), "six": ("1.17.0", "", 1),
    "sortedcontainers": ("2.4.0", "", 1), "tqdm": ("4.70.1", "", 1), "tzdata": ("2026.5", "", 1),
    "uvloop": ("0.22.1", 'sys_platform != "win32"', 1)}
NAUTILUS_HASHES = {"5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf",    # win_amd64 (PyPI)
                   "429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91"}    # manylinux_2_35_x86_64
REQ_BODY_SHA256 = "49c1cee13798cbc92104bd398af422f611334db1f79260231c0c357fd7d0b5e4"
ENV_LINE = "QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'"
ENV_HEADING = "# --- NautilusTrader bridge (research only) ----------------------------------"
PRECISION = {"manylinux_2_35_x86_64": {"HIGH_PRECISION": True, "FIXED_PRECISION": 16,
                                       "QUANTITY_MAX": 34028236692093.0, "PRICE_MAX": 17014118346046.0},
             "win_amd64": {"HIGH_PRECISION": False, "FIXED_PRECISION": 9,              # spec 3.6; UNVERIFIED to 7A
                           "QUANTITY_MAX": 18446744073.0, "PRICE_MAX": 9223372036.0}}
SYSTEM = {"manylinux_2_35_x86_64": "Linux", "win_amd64": "Windows"}
SELFTEST = {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}


def test_l1_16_launch_builder_matches_the_contract():
    """L1-16: given os_name "nt" and "posix", build_launch builds exactly 4.3's argv and environment, with unshare on
    POSIX and each platform's process-group flag, and starts no process; make_tempdir creates home and tmp; a key
    outside the contract, or one missing, is C-10."""
    tmp = launch.make_tempdir()
    try:
        assert tmp.name.startswith("qgnb_") and str(tmp) == os.path.realpath(tmp), tmp
        assert (tmp / "home").is_dir() and (tmp / "tmp").is_dir()
        environ = {"PATH": "/x", "HOME": "/h", "SYSTEMROOT": r"C:\Windows", "PYTHONPATH": "/p", "NAUTILUS_PATH": "/n",
                   "QUANTGEN_NAUTILUS_PYTHON": "/v", "FMP_API_KEY": "k", "TMPDIR": "/t", "LANG": "ko_KR.UTF-8"}
        un, py = "/usr/bin/unshare", PurePosixPath("/opt/qg/ntvenv/bin/python")
        wpy = PureWindowsPath(r"C:\Users\o\AppData\Local\quantgen\ntvenv\Scripts\python.exe")
        sandbox, probe = str(launch.SANDBOX), str(launch.EGRESS_PROBE)
        posix_env = {"PATH": "/opt/qg/ntvenv/bin:/usr/bin:/bin", "HOME": f"{tmp}/home", "TMPDIR": f"{tmp}/tmp",
                     "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        nt_env = {"SYSTEMROOT": r"C:\Windows",
                  "PATH": r"C:\Users\o\AppData\Local\quantgen\ntvenv\Scripts;C:\Windows\System32",
                  "USERPROFILE": f"{tmp}\\home", "HOME": f"{tmp}\\home", "TEMP": f"{tmp}\\tmp", "TMP": f"{tmp}\\tmp"}
        pipes = {"stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True,
                 "encoding": "utf-8", "errors": "replace"}
        head = [un, "-rn", str(py), "-I", "-B", "-X", "utf8"]
        whead = [str(wpy), "-I", "-B", "-X", "utf8"]
        run_args = ["run", "--in", str(tmp)]
        stub = ["/usr/local/bin/python3", "-I", "/r/tests/nautilus_stub_child.py", "--exit", "1"]
        wstub = [r"C:\py313\python.exe", "-I", r"C:\r\tests\nautilus_stub_child.py"]

        def no_process(*_a, **_k):
            raise AssertionError("build_launch started a process")
        saved = (subprocess.Popen, subprocess.run)
        subprocess.Popen = subprocess.run = no_process
        try:
            def build(mode, os_name, **kw):
                kw.setdefault("venv_python", py if os_name == "posix" else wpy)
                return launch.build_launch(mode, tempdir=tmp, os_name=os_name, environ=environ, **kw)
            group = {"posix": {"start_new_session": True}, "nt": {"creationflags": 0x00000200}}  # NEW_PROCESS_GROUP
            cases = [
                ("posix", build(["--check-env"], "posix", unshare=un), head + [sandbox, "--check-env"], posix_env),
                ("posix", build(["--guard-selftest"], "posix", unshare=un), head + [sandbox, "--guard-selftest"],
                 posix_env),
                ("posix", build(run_args, "posix", unshare=un), head + ["-X", "importtime", sandbox, *run_args],
                 posix_env),
                ("posix", build([], "posix", unshare=un, script=launch.EGRESS_PROBE), head + [probe], posix_env),
                ("posix", build(run_args, "posix", unshare=un, venv_python=None, child_cmd=stub),
                 [un, "-rn", *stub, *run_args], {**posix_env, "PATH": "/usr/local/bin:/usr/bin:/bin"}),
                ("nt", build(["--check-env"], "nt"), whead + [sandbox, "--check-env"], nt_env),
                ("nt", build(run_args, "nt", unshare=un), whead + ["-X", "importtime", sandbox, *run_args], nt_env),
                ("nt", build([], "nt", script=launch.EGRESS_PROBE), whead + [probe], nt_env),
                ("nt", build(run_args, "nt", venv_python=None, child_cmd=wstub), [*wstub, *run_args],
                 {**nt_env, "PATH": r"C:\py313;C:\Windows\System32"}),
            ]
            for n, (os_name, got, argv, env) in enumerate(cases):
                assert got.argv == argv, (n, got.argv)
                assert got.env == env, (n, got.env)
                assert got.cwd == str(tmp), (n, got.cwd)
                assert got.popen_kwargs == {**pipes, **group[os_name]}, (n, got.popen_kwargs)
            _refused(lambda: build(["--check-env"], "posix", unshare=None), "R-14")
        finally:
            subprocess.Popen, subprocess.run = saved
        launch.assert_env_contract(posix_env, "posix")
        launch.assert_env_contract(nt_env, "nt")
        _invalid(lambda: launch.assert_env_contract({**posix_env, "PYTHONPATH": "/p"}, "posix"), "C-10")
        _invalid(lambda: launch.assert_env_contract({**nt_env, "FMP_API_KEY": "k"}, "nt"), "C-10")
        _invalid(lambda: launch.assert_env_contract({k: v for k, v in posix_env.items() if k != "LC_ALL"}, "posix"),
                 "C-10")
        _invalid(lambda: launch.assert_env_contract(posix_env, "nt"), "C-10")
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert left == [] and not tmp.exists(), left


def test_l1_17_venv_reads_and_wheel_identity():
    """L1-17: venv reads on fake venv dirs (variable and ~ expansion, a control character, a relative path, a wrong
    file name, include-system-site-packages = true, a Windows venv on the parent's or the Store's interpreter, a
    version, minor, tag or RECORD off its pin: R-03); the committed RECORD fixtures give both pinned identities.
    On POSIX the variable is $VAR, on Windows %VAR% (os.path.expandvars, spec 6.7)."""
    linux = require_fixture(LINUX_RECORD, manifest=FIXTURE_MANIFEST).read_text(encoding="utf-8")
    win = require_fixture(WIN_RECORD, manifest=FIXTURE_MANIFEST).read_text(encoding="utf-8")
    assert launch.record_identity(linux) == LINUX_IDENTITY and launch.record_identity(win) == WIN_IDENTITY
    noise = ("nautilus_trader/__pycache__/x.cpython-313.pyc,sha256=AAAA,1\n"
             "nautilus_trader-1.231.0.dist-info/INSTALLER,sha256=BBBB,4\n"
             "nautilus_trader-1.231.0.dist-info/REQUESTED,sha256=CCCC,0\n"
             "nautilus_trader-1.231.0.dist-info/direct_url.json,sha256=DDDD,9\n"
             "nautilus_trader-1.231.0.dist-info/RECORD,,\n"
             "nautilus_trader/unhashed.txt,,\n")
    assert launch.record_identity(linux + noise) == LINUX_IDENTITY
    assert launch.record_identity("\n".join(reversed(linux.splitlines())) + "\n") == LINUX_IDENTITY
    pins = launch.load_env_pins()
    with tempfile.TemporaryDirectory(prefix="qgnb_l117_") as name:
        tmp = Path(name)
        base = str(tmp / "other" / "python")
        lin = _fake_venv(tmp / "lin", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64")
        reads = launch.read_venv(lin, os_name="posix", parent_base_executable=base)
        assert reads["root"] == str(tmp / "lin") and launch.venv_root(lin) == tmp / "lin", reads["root"]
        assert reads["python_minor"] == "3.13" and reads["versions"] == EXPECTED_VERSIONS, reads
        assert reads["installed"] == EXPECTED_VERSIONS, reads["installed"]
        assert reads["pyvenv"]["include_system_site_packages"] is False and reads["pyvenv"]["version"] == "3.13.17"
        assert reads["wheel"] == {"wheel_tag": "cp313-cp313-manylinux_2_35_x86_64",
                                  "platform_tag": "manylinux_2_35_x86_64",
                                  "record_digest_sha256": LINUX_IDENTITY[0], "record_entries": 764}, reads["wheel"]
        assert launch.venv_mismatches(reads) == [] and launch.venv_mismatches(reads, pins) == []
        cfg_same = {"executable": base}                       # POSIX: a venv on the parent's own base is allowed
        same = _fake_venv(tmp / "same", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64",
                          cfg=cfg_same)
        launch.read_venv(same, os_name="posix", parent_base_executable=base)
        py313 = {"home": r"C:\qg\py313", "executable": r"C:\qg\py313\python.exe"}   # the dedicated base (4.4)
        wv = _fake_venv(tmp / "win", os_name="nt", record=win, tag="cp313-cp313-win_amd64", cfg=py313)
        wreads = launch.read_venv(wv, os_name="nt", parent_base_executable=base)
        assert wreads["wheel"]["platform_tag"] == "win_amd64" and launch.venv_mismatches(wreads) == [], wreads
        # off the pins: one "R-03: <field>: found <x>, expected <y>" per difference
        off = _fake_venv(tmp / "off", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64",
                         versions={"numpy": "2.3.4"}, cfg={"version": "3.12.9"})
        bad = launch.venv_mismatches(launch.read_venv(off, os_name="posix", parent_base_executable=base))
        assert "R-03: python_minor: found 3.12, expected 3.13" in bad, bad
        assert "R-03: numpy: found 2.3.4, expected 2.3.5" in bad and all(b.startswith("R-03: ") for b in bad), bad
        cut = "\n".join(linux.splitlines()[1:]) + "\n"
        rec = _fake_venv(tmp / "rec", os_name="posix", record=cut, tag="cp313-cp313-manylinux_2_35_x86_64")
        bad = launch.venv_mismatches(launch.read_venv(rec, os_name="posix", parent_base_executable=base))
        assert [b.split(":")[1].strip() for b in bad] == ["record_digest_sha256", "record_entries"], bad
        mac = _fake_venv(tmp / "mac", os_name="posix", record=linux, tag="cp313-cp313-macosx_14_0_arm64")
        bad = launch.venv_mismatches(launch.read_venv(mac, os_name="posix", parent_base_executable=base))
        assert len(bad) == 1 and bad[0].startswith("R-03: platform_tag: found macosx_14_0_arm64"), bad
        # pyvenv.cfg refusals
        sys_site = _fake_venv(tmp / "sys", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64",
                              cfg={"include-system-site-packages": "true"})
        _refused(lambda: launch.read_venv(sys_site, os_name="posix", parent_base_executable=base), "R-03")
        own = _fake_venv(tmp / "own", os_name="nt", record=win, tag="cp313-cp313-win_amd64", cfg={"executable": base})
        _refused(lambda: launch.read_venv(own, os_name="nt", parent_base_executable=base), "R-03")
        store = r"C:\Users\o\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0"
        home = _fake_venv(tmp / "store", os_name="nt", record=win, tag="cp313-cp313-win_amd64",
                          cfg={**py313, "home": store})
        exc = _refused(lambda: launch.read_venv(home, os_name="nt", parent_base_executable=base), "R-03")
        assert "Microsoft Store" in exc.message, exc
        pkg = r"C:\Users\o\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe"
        exe = _fake_venv(tmp / "pkg", os_name="nt", record=win, tag="cp313-cp313-win_amd64",
                         cfg={**py313, "executable": pkg})
        _refused(lambda: launch.read_venv(exe, os_name="nt", parent_base_executable=base), "R-03")
        # the key's value (6.7): expansion, then control characters, absolute path, file name, existence
        host = _fake_venv(tmp / "host", os_name=os.name, record=linux, tag="cp313-cp313-manylinux_2_35_x86_64")
        rel = host.relative_to(tmp).as_posix()
        token = "%QGNB_L117%" if os.name == "nt" else "$QGNB_L117"
        home_key = "USERPROFILE" if os.name == "nt" else "HOME"
        saved = {k: os.environ.get(k) for k in ("QGNB_L117", home_key)}
        os.environ["QGNB_L117"], os.environ[home_key] = str(tmp), str(tmp)
        try:
            assert launch.resolve_venv_python(f"{token}/{rel}") == host
            assert launch.resolve_venv_python(f"~/{rel}") == host
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        for value in (str(host) + "\n", str(host) + "\x7f", f"\t{host}"):
            exc = _refused(lambda: launch.resolve_venv_python(value), "R-03")
            assert repr(value) in exc.message and exc.remedy, exc
        (host.parent / "python3").write_bytes(b"")
        for value in (rel, str(host.parent / "python3"), str(tmp / "nowhere" / host.name)):
            exc = _refused(lambda: launch.resolve_venv_python(value), "R-03")
            assert repr(value) in exc.message and exc.remedy, exc


def test_l1_22_global_interpreter_has_no_nautilus():
    """L1-22: the global interpreter has no nautilus-trader distribution and cannot import nautilus_trader (FAIL, with
    R-03's three remedy lines; OPS-R3-1); pyarrow there is reported, never failed (OPS-5)."""
    found = launch.parent_nautilus()
    importable = importlib.util.find_spec("nautilus_trader") is not None
    assert found is None and not importable, (
        f"R-03: nautilus-trader in the global interpreter (distribution {found!r}, importable {importable}); run "
        f"exactly these three lines, and the last must print 2.3.5 2.3.3 1.18.0:\n{launch.PARENT_NAUTILUS_REMEDY}")
    lines = launch.PARENT_NAUTILUS_REMEDY.splitlines()
    assert lines == ["python -m pip uninstall -y nautilus-trader", "python -m pip check",
                     'python -c "import numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, '
                     'scipy.__version__)"'], lines
    print(f"  pyarrow in the global interpreter: {launch.parent_pyarrow()}")


def test_l1_32_every_test_guarded_and_ledgers_unchanged():
    """L1-32: the guard of 3.3 wraps every test, this test runs last, the guarded files equal the digests taken when
    the suite started, QUANTGEN_MACRO_DIR is a fresh temp dir inside each test, and a write under a guarded root is
    a FAIL that names the file (QA-1, QA-R2-13)."""
    global _ROOTS
    import config
    entries = tests()
    names = [n for n, _ in entries]
    assert names[-1] == LAST_TEST and names[:-1] == sorted(names[:-1]) and len(set(names)) == len(names), names
    assert all(getattr(f, "nautilus_guarded", False) for _, f in entries), names
    mine = os.environ.get("QUANTGEN_MACRO_DIR", "")
    assert Path(mine).name.startswith("qgnb_macro_") and Path(mine).is_dir() and config.macro_dir() == Path(mine), mine
    assert not any(str(r).startswith(mine) for r in guard_roots()), guard_roots()
    seen: list[str] = []
    saved_roots = _ROOTS
    with tempfile.TemporaryDirectory(prefix="qgnb_l132_") as name:
        root = Path(name)
        (root / "E1.jsonl").write_text("{}\n", encoding="utf-8", newline="\n")

        def appends():
            with (root / "E1.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
                fh.write("{}\n")
        _ROOTS = (root,)
        try:
            for _ in range(2):
                guarded("probe_reads", lambda: seen.append(os.environ["QUANTGEN_MACRO_DIR"]))()
            try:
                guarded("probe_appends", appends)()
            except AssertionError as exc:
                assert str(root / "E1.jsonl") in str(exc), exc
            else:
                raise AssertionError("a ledger append inside a guarded test passed")
        finally:
            _ROOTS = saved_roots
    assert len(set(seen)) == 2 and mine not in seen and not any(Path(s).exists() for s in seen), seen
    assert os.environ.get("QUANTGEN_MACRO_DIR") == mine
    assert _SUITE_START is not None
    now = digest_roots(guard_roots())
    changed = sorted(k for k in _SUITE_START.keys() | now.keys() if _SUITE_START.get(k) != now.get(k))
    assert not changed, f"guarded files changed since the suite started: {changed}"


def test_px_requirements_nautilus_pins_and_header():
    """Spec 5.1 and 3.4: requirements-nautilus.txt is the header verbatim, then the hashed closure body verbatim (16
    distributions with == pins and --hash lines; PyPI's nautilus-trader hashes); it is the single source of the
    version pins; QUANTGEN's own dependency files never name nautilus or pyarrow."""
    raw = (ROOT / "requirements-nautilus.txt").read_bytes()
    assert raw.isascii() and b"\r" not in raw and raw.endswith(b"\n"), "ASCII, LF line ends, a final newline"
    lines = raw.decode("ascii").splitlines()
    assert tuple(lines[:6]) == REQ_HEADER, lines[:6]
    body = "\n".join(lines[6:]) + "\n"
    assert hashlib.sha256(body.encode("ascii")).hexdigest() == REQ_BODY_SHA256, "body differs from the closure body"
    pins: dict[str, tuple[str, str, list[str]]] = {}
    current = None
    for line in lines[6:]:
        if line.startswith("    --hash=sha256:"):
            digest = line.split(":", 1)[1].rstrip(" \\")
            assert len(digest) == 64 and digest == digest.lower() and int(digest, 16) >= 0, line
            pins[current][2].append(digest)
            continue
        spec, _, marker = line.rstrip(" \\").partition(" ; ")
        current, _, version = spec.partition("==")
        pins[current] = (version, marker, [])
    assert {k: (v, m, len(h)) for k, (v, m, h) in pins.items()} == REQ_PINS, pins
    assert set(pins["nautilus-trader"][2]) == NAUTILUS_HASHES
    assert launch.REQUIREMENTS == ROOT / "requirements-nautilus.txt"
    assert launch.expected_versions() == EXPECTED_VERSIONS
    for name in ("requirements.txt", "requirements-dev.txt", "pyproject.toml"):
        text = (ROOT / name).read_text(encoding="utf-8").lower()
        assert "nautilus" not in text and "pyarrow" not in text, name


def test_px_env_example_and_env_pins():
    """Spec 3.4: .env.example gains the heading and the single-quoted, forward-slash line, which python-dotenv reads
    as written (double quotes would turn the \\n of \\ntvenv into a newline); spec 6.7 and C7: env_pins.json holds
    both platforms' pins in the bridge's JSON bytes."""
    raw = (ROOT / ".env.example").read_bytes()
    assert b"\r" not in raw, ".env.example must stay LF"
    lines = raw.decode("utf-8").splitlines()
    assert lines.count(ENV_LINE) == 1 and lines.count(ENV_HEADING) == 1, "heading or line missing or repeated"
    block = lines[lines.index(ENV_HEADING):lines.index(ENV_LINE) + 1]
    assert block and not any("%" in s for s in block), block                # no %VAR% (OPS-4)
    from dotenv import dotenv_values
    value = dotenv_values(ROOT / ".env.example")["QUANTGEN_NAUTILUS_PYTHON"]
    assert value == "C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe", repr(value)
    quoted = dotenv_values(stream=io.StringIO('K="C:\\Users\\o\\ntvenv\\Scripts\\python.exe"\n'))["K"]
    assert "\n" in quoted, repr(quoted)                        # the hazard the single quotes avoid
    pins_bytes = launch.ENV_PINS.read_bytes()
    assert pins_bytes == (json.dumps(PINS_JSON, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    assert launch.load_env_pins() == PINS_JSON
    for plat in PINS_JSON["platforms"].values():
        assert {k.replace("_", "-"): v for k, v in plat["versions"].items()} == launch.expected_versions()


def test_px_egress_probe_imports_json_and_socket_only():
    """Spec 4.4 and C4: the probe imports json and socket only, makes one create_connection to ("1.1.1.1", 443) with
    timeout 3, and reports a refused connect as blocked and an accepted one as not blocked (loopback only)."""
    tree = ast.parse(launch.EGRESS_PROBE.read_text(encoding="utf-8"))
    imports = sorted(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
    froms = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert imports == ["json", "socket"] and froms == [], (imports, froms)
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "create_connection"]
    assert len(calls) == 1, len(calls)
    spec = importlib.util.spec_from_file_location("qgnb_egress_probe", launch.EGRESS_PROBE)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    params = inspect.signature(probe.probe).parameters
    assert [(p.name, p.default) for p in params.values()] == [("host", "1.1.1.1"), ("port", 443), ("timeout", 3)]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        assert probe.probe("127.0.0.1", port, 3) == {"blocked": False, "errno": None, "error": ""}
    out = probe.probe("127.0.0.1", port, 10)                  # the listener is closed: refused (or timed out)
    assert out["blocked"] is True and out["error"] and (out["errno"] is None or isinstance(out["errno"], int)), out


def test_px_census_parser_reads_importtime_lines():
    """Spec 5.2.7: parse_census keeps the third `|` field of every `import time:` line, skips the header, sorts and
    de-duplicates the names, and returns the rest of stderr unchanged; a real -X importtime run parses too."""
    stderr = ("import time: self [us] | cumulative | imported package\n"
              "import time:       101 |        101 |   _io\n"
              "import time:        55 |        300 |     nautilus_trader.core\n"
              "Traceback (most recent call last):\n"
              "import time:        10 |         10 |       plotly\n"
              "import time:         7 |          7 |   _io\n"
              "ValueError: boom\n")
    assert launch.parse_census(stderr) == (["_io", "nautilus_trader.core", "plotly"],
                                           "Traceback (most recent call last):\nValueError: boom\n")
    assert launch.parse_census("") == ([], "")
    real = subprocess.run([sys.executable, "-I", "-X", "importtime", "-c", "import json"], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=60)
    names, rest = launch.parse_census(real.stderr)
    assert real.returncode == 0 and "json" in names and "json.decoder" in names and rest == "", (names[:5], rest)


# --------------------------------------------------------------------------- #
# Plan Task 1 (spec Step 3): layer 2
# --------------------------------------------------------------------------- #
def test_l2_01_check_env_pins_identity_precision():
    """L2-1: the parent's venv reads match the pins and the wheel identity; --check-env, launched through the launch
    contract, prints one JSON line with the venv's Python, the platform's precision and environment BACKTEST."""
    python = layer2()
    reads = launch.read_venv(python)
    tag = reads["wheel"]["platform_tag"]
    pin = launch.load_env_pins()["platforms"][tag]
    assert (reads["wheel"]["record_digest_sha256"], reads["wheel"]["record_entries"]) == (
        pin["record_digest_sha256"], pin["record_entries"]), reads["wheel"]
    result = _launch_venv(python, ["--check-env"])
    assert result.returncode == 0 and not result.timed_out, (result.returncode, result.stderr_tail)
    lines = result.stdout.splitlines()
    assert len(lines) == 1, result.stdout_tail
    out = json.loads(lines[0])
    assert set(out) == {"schema", "python", "system", "machine", "environment", "precision"}, out
    assert out["schema"] == "nautilus-bridge-check-env/1" and out["environment"] == "BACKTEST", out
    assert out["python"] == reads["pyvenv"]["version"] and out["python"].startswith("3.13."), out
    assert out["system"] == SYSTEM[tag] and out["precision"] == PRECISION[tag], out
    assert result.census == [], result.census[:5]


def test_l2_08_guard_selftest_outcomes():
    """L2-8 (C-2): --guard-selftest exits 0; SANDBOX, LIVE and LiveClock() raised; BACKTEST and TestClock() passed."""
    python = layer2()
    result = _launch_venv(python, ["--guard-selftest"])
    assert result.returncode == 0, (result.returncode, result.stdout_tail, result.stderr_tail)
    assert result.stdout.strip() == json.dumps(SELFTEST, sort_keys=True), result.stdout


def test_l2_09_egress_probe_blocked():
    """L2-9 (SECURITY-1): the egress probe, launched in the venv through the launch contract, reports blocked."""
    python = layer2()
    result = _launch_venv(python, [], script=launch.EGRESS_PROBE, timeout=60)
    out = json.loads(result.stdout.strip())
    assert result.returncode == 0 and out["blocked"] is True, (result.returncode, out, result.stderr_tail)
    assert set(out) == {"blocked", "errno", "error"} and out["error"], out


def test_l2_10_timeout_kills_the_child_tree():
    """L2-10 (OPS-1): a venv child that sleeps 120 s, with a sleeping grandchild, launched with timeout 3, returns
    within 15 s; the whole tree is gone (Linux: /proc; Windows: the temp dir, its cwd, can be deleted)."""
    python = layer2()
    code = ("import os, subprocess, sys, time; "
            "g = subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(120)']); "
            "open('pids.txt', 'w', encoding='utf-8').write(f'{os.getpid()} {g.pid}'); time.sleep(120)")
    tmp = launch.make_tempdir()
    try:
        child = launch.build_launch([], tempdir=tmp, venv_python=None, unshare=launch.resolve_unshare(),
                                    child_cmd=[str(python), "-I", "-c", code])
        started = time.monotonic()
        result = launch.run_child(child, timeout=3)
        took = time.monotonic() - started
        pids = [int(p) for p in (tmp / "pids.txt").read_text(encoding="utf-8").split()]
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert result.timed_out and result.returncode is not None and took < 15, (result.timed_out, result.returncode,
                                                                              took)
    assert left == [], left
    assert len(pids) == 2, pids
    if os.name != "nt" and Path("/proc").is_dir():
        assert all(_gone(p) for p in pids), pids


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    """Runs the tests() entries whose name contains any -k substring (all without -k); prints only."""
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="python3 -B -m tests.nautilus_acceptance")
    parser.add_argument("-k", dest="patterns", action="append", default=[],
                        help="run only the tests whose name contains this substring (repeatable)")
    args = parser.parse_args(argv)
    entries = [(n, f) for n, f in tests() if not args.patterns or any(p in n for p in args.patterns)]
    counts = {"PASS": 0, "FAIL": 0, "NOT_RUN": 0}
    for name, fn in entries:
        status, detail = "PASS", ""
        try:
            fn()
        except NotRun as exc:
            status, detail = "NOT_RUN", exc.reason
        except Exception as exc:                                        # noqa: BLE001
            status, detail = "FAIL", f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        counts[status] += 1
        print(f"{status} {name} {detail}".rstrip(), flush=True)
    print(f"\n{counts['PASS']}/{len(entries)} passed, {counts['FAIL']} failed, {counts['NOT_RUN']} not run")
    return 0 if entries and not counts["FAIL"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run it and see it fail (RED).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance; echo "exit $?"
```
  Expected: a traceback ending `ImportError: cannot import name 'launch' from 'tools.nautilus' (/home/user/quantgen/tools/nautilus/__init__.py)`, then `exit 1`. All 12 tests are RED here.

- [ ] **Step 4: Implement `tools/nautilus/launch.py`** (spec 4.3, 5.2.7, 6.7; C1, C2) with exactly this content (LF; md5 `c55ca113ea950f2333cd143be9a9b747`). Every function is short enough to give in full. Exit and error ids: `R-03` (`resolve_venv_python`, `venv_root`, `read_venv`, `venv_mismatches`), `R-14` (`resolve_unshare`; `build_launch` on POSIX without `unshare`), `C-10` (`assert_env_contract`, called by `build_launch`). CONTRACT ISSUE 2: `build_launch` uses `ntpath` or `posixpath` by `os_name`, and `creationflags=CREATE_NEW_PROCESS_GROUP` (0x200, the Windows value), so L1-16 builds both platforms' launches on either host. CONTRACT ISSUE 3: the Microsoft Store test of `read_venv` is a case-insensitive substring test on the strings `pyvenv.cfg` records; the equality with the parent's `sys._base_executable` compares `normcase(realpath)` as C2 says. CONTRACT ISSUE 1: `PARENT_NAUTILUS_REMEDY` holds R-03's three remedy lines for the parent.
```python
"""The launch contract of the NautilusTrader bridge (spec 2026-10-26 sections 4.3, 5.2.7 and 6.7).

Every child (the sandbox, the egress probe, a test stub) starts through `run_child`, with the argv and the minimal
environment that `build_launch` builds: `-I -B -X utf8`, an absolute script path, `unshare -rn` on POSIX, a fresh
temp working directory, no inherited variable, and a tree kill on timeout. This module also reads the venv's own
files for versions and the wheel identity (the parent never imports the engine), and parses the import census.
Standard library only; it runs in the global interpreter.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import io
import json
import ntpath
import os
import posixpath
import re
import shutil
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

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
CREATE_NEW_PROCESS_GROUP = 0x00000200          # subprocess.CREATE_NEW_PROCESS_GROUP, which exists only on Windows
PINNED = ("nautilus-trader", "numpy", "pandas")
VENV_FIX = ("set QUANTGEN_NAUTILUS_PYTHON in .env to the absolute path of the venv's python, in single quotes with "
            "forward slashes, as .env.example shows; build the venv with <py313>\\python.exe -m venv and the offline "
            "install of the requirements-nautilus.txt header (spec 5.1)")
STORE_FIX = ("this venv was made from the Microsoft Store python; recreate it with "
             "<py313>\\python.exe -m venv <venv dir> (spec 4.4, 6.7)")
PARENT_NAUTILUS_REMEDY = "\n".join((                # R-03 for the parent, exactly three lines (spec 7; OPS-R3-1)
    "python -m pip uninstall -y nautilus-trader",
    "python -m pip check",
    'python -c "import numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, scipy.__version__)"'))


class BridgeRefusal(Exception):
    """A refusal R-01 to R-17 of spec section 7. `str(exc)` is f"{rid}: {message}"."""

    def __init__(self, rid: str, message: str, remedy: str = "") -> None:
        super().__init__(f"{rid}: {message}")
        self.rid, self.message, self.remedy = rid, message, remedy


class ChildInvalid(Exception):
    """A child-level invalid condition C-01 to C-15. `str(exc)` is f"{cid}: {message}"."""

    def __init__(self, cid: str, message: str) -> None:
        super().__init__(f"{cid}: {message}")
        self.cid, self.message = cid, message


def _pep503(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))


def _store_python(path: str) -> bool:
    s = path.replace("/", "\\").lower()
    return "\\windowsapps\\" in s or s.endswith("\\windowsapps") or "\\packages\\pythonsoftwarefoundation." in s


# --------------------------------------------------------------------------- #
# Venv reads and the wheel identity (spec 6.7)
# --------------------------------------------------------------------------- #
def venv_key() -> str:
    """QUANTGEN_NAUTILUS_PYTHON after `import config` has loaded .env; "" when blank or an unedited <placeholder>."""
    import config
    return config._clean(KEY)


def resolve_venv_python(value: str) -> Path:
    """The venv python named by the key, after ~ and variable expansion; R-03 on a control character, a relative
    path, a file name other than python.exe or python, or a missing file. Not resolved through symlinks."""
    def refuse(why: str) -> BridgeRefusal:
        return BridgeRefusal("R-03", f"QUANTGEN_NAUTILUS_PYTHON {why}: {value!r}", VENV_FIX)
    bad = [c for c in value if ord(c) < 32 or ord(c) == 127]
    expanded = os.path.expanduser(os.path.expandvars(value))
    if bad or any(ord(c) < 32 or ord(c) == 127 for c in expanded):
        raise refuse("holds a control character")
    path = Path(expanded)
    if not path.is_absolute():
        raise refuse("is not an absolute path")
    if path.name not in ("python.exe", "python"):
        raise refuse("does not name python.exe or python")
    if not path.is_file():
        raise refuse("names a missing file")
    return path


def venv_root(python: Path) -> Path:
    """The parent of Scripts (Windows) or bin (POSIX)."""
    if python.parent.name not in ("Scripts", "bin"):
        raise BridgeRefusal("R-03", f"the venv python is not in Scripts or bin: {str(python)!r}", VENV_FIX)
    return python.parent.parent


def expected_versions(path: Path = REQUIREMENTS) -> dict[str, str]:
    """{"nautilus-trader", "numpy", "pandas"} -> version, from the == pins of requirements-nautilus.txt (5.1)."""
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)", line)
        if m and _pep503(m[1]) in PINNED:
            found[_pep503(m[1])] = m[2]
    missing = sorted(set(PINNED) - set(found))
    if missing:
        raise ValueError(f"{path.name} pins none of {missing}")
    return found


def record_identity(record_text: str) -> tuple[str, int]:
    """(record_digest_sha256, record_entries) of a wheel RECORD by the rule of spec 6.7."""
    kept = []
    for row in csv.reader(io.StringIO(record_text)):
        if len(row) < 2 or not row[1] or "__pycache__" in row[0]:
            continue
        if row[0].endswith(("/RECORD", "/INSTALLER", "/REQUESTED", "/direct_url.json")):
            continue
        kept.append(f"{row[0]},{row[1]}")
    kept.sort()
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest(), len(kept)


def _headers(path: Path) -> dict[str, str]:
    """The RFC 822 header lines of a METADATA or WHEEL file, up to the first blank line; first value wins."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            break
        key, sep, value = line.partition(":")
        if sep and not line[0].isspace():
            out.setdefault(key.strip(), value.strip())
    return out


def read_venv(python: Path, *, os_name: str = os.name, parent_base_executable: str = sys._base_executable) -> dict:
    """Reads pyvenv.cfg, every dist-info's METADATA and the nautilus_trader WHEEL and RECORD (spec 6.7). R-03 for
    include-system-site-packages = true and, on Windows, for a venv made from the parent's own interpreter or from
    the Microsoft Store python (4.4; OPS-R2-2). Opens no other file and starts no process."""
    root = venv_root(python)
    cfg_path = root / "pyvenv.cfg"
    if not cfg_path.is_file():
        raise BridgeRefusal("R-03", f"no pyvenv.cfg beside the venv python: {str(cfg_path)!r}", VENV_FIX)
    cfg = {}
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            cfg[key.strip().lower()] = value.strip()
    if cfg.get("include-system-site-packages", "false").lower() == "true":
        raise BridgeRefusal("R-03", f"{str(cfg_path)!r} says include-system-site-packages = true", VENV_FIX)
    home, executable = cfg.get("home", ""), cfg.get("executable")
    version = cfg.get("version") or cfg.get("version_info", "")
    if os_name == "nt":
        if executable and _norm(executable) == _norm(parent_base_executable):
            raise BridgeRefusal("R-03", f"the venv was made from the global interpreter {executable!r}", STORE_FIX)
        for found in (home, executable or ""):
            if _store_python(found):
                raise BridgeRefusal("R-03", f"pyvenv.cfg names {found!r}: {STORE_FIX}", STORE_FIX)
    minor = ".".join(version.split(".")[:2])
    site = root / "Lib" / "site-packages" if os_name == "nt" else root / "lib" / f"python{minor}" / "site-packages"
    installed = {}
    for meta in sorted(site.glob("*.dist-info/METADATA")):
        head = _headers(meta)
        if head.get("Name") and head.get("Version"):
            installed[_pep503(head["Name"])] = head["Version"]
    infos = sorted(site.glob("nautilus_trader-*.dist-info"))
    if len(infos) != 1:
        raise BridgeRefusal("R-03", f"{len(infos)} nautilus_trader dist-info dirs in {str(site)!r}", VENV_FIX)
    wheel_tag = _headers(infos[0] / "WHEEL").get("Tag", "")
    digest, entries = record_identity((infos[0] / "RECORD").read_text(encoding="utf-8"))
    return {"python": str(python), "python_norm": _norm(str(python)), "root": str(root),
            "pyvenv": {"home": home, "version": version, "executable": executable,
                       "include_system_site_packages": False},
            "python_minor": minor,
            "installed": installed,
            "versions": {name: installed.get(name) for name in PINNED},
            "wheel": {"wheel_tag": wheel_tag, "platform_tag": wheel_tag.split("-", 2)[-1],
                      "record_digest_sha256": digest, "record_entries": entries}}


def load_env_pins(path: Path = ENV_PINS) -> dict:
    pins = json.loads(path.read_text(encoding="utf-8"))
    if pins.get("schema") != "nautilus-bridge-env-pins/1":
        raise ValueError(f"{path.name}: schema {pins.get('schema')!r}")
    return pins


def venv_mismatches(reads: dict, pins: dict | None = None, expected: dict | None = None) -> list[str]:
    """[] when the venv matches requirements-nautilus.txt and env_pins.json; else one
    "R-03: <field>: found <x>, expected <y>" per difference (an unknown platform tag is one mismatch)."""
    pins = load_env_pins() if pins is None else pins
    expected = expected_versions() if expected is None else {_pep503(k): v for k, v in expected.items()}
    tag = reads["wheel"]["platform_tag"]
    if tag not in pins["platforms"]:
        return [f"R-03: platform_tag: found {tag}, expected one of {sorted(pins['platforms'])}"]
    pin = pins["platforms"][tag]
    pinned = {_pep503(k): v for k, v in pin["versions"].items()}
    out = []

    def check(field: str, found, want) -> None:
        if found != want:
            out.append(f"R-03: {field}: found {found}, expected {want}")
    check("python_minor", reads["python_minor"], pin["python_minor"])
    for name in PINNED:
        found = reads["versions"].get(name)
        check(name, found, expected.get(name))
        if expected.get(name) != pinned.get(name):
            check(f"{name} (env_pins.json)", found, pinned.get(name))
    for field in ("wheel_tag", "record_digest_sha256", "record_entries"):
        check(field, reads["wheel"][field], pin[field])
    return out


def parent_nautilus() -> str | None:
    """The nautilus-trader version installed in this (the global) interpreter, or None (spec 5.3.2 step 3)."""
    try:
        return importlib.metadata.distribution("nautilus-trader").version
    except importlib.metadata.PackageNotFoundError:
        return None


def parent_pyarrow() -> str | None:
    try:
        return importlib.metadata.distribution("pyarrow").version
    except importlib.metadata.PackageNotFoundError:
        return None


def host_tag() -> str:
    """sysconfig.get_platform() with - and . replaced by _: linux_x86_64, win_amd64 (C1)."""
    return sysconfig.get_platform().replace("-", "_").replace(".", "_")


# --------------------------------------------------------------------------- #
# The launch contract (spec 4.3)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Launch:
    argv: list[str]
    env: dict[str, str]
    cwd: str
    popen_kwargs: dict


@dataclass(frozen=True)
class ChildResult:
    argv: list[str]
    returncode: int | None
    ntstatus: str | None
    timed_out: bool
    seconds: float
    stdout: str
    stderr: str
    census: list[str]
    stdout_tail: str
    stderr_tail: str


def make_tempdir() -> Path:
    """realpath(mkdtemp(prefix="qgnb_")) with home/ and tmp/ inside: the child's cwd, HOME and TMP (4.3)."""
    tempdir = Path(os.path.realpath(tempfile.mkdtemp(prefix="qgnb_")))
    (tempdir / "home").mkdir()
    (tempdir / "tmp").mkdir()
    return tempdir


def resolve_unshare(os_name: str = os.name) -> str | None:
    """None on Windows. POSIX: the unshare binary, which must run `unshare -rn true` with exit 0, else R-14."""
    if os_name == "nt":
        return None
    exe = shutil.which("unshare")
    if exe is None:
        raise BridgeRefusal("R-14", "unshare is not on PATH", "a Linux host with user namespaces (spec 4.4)")
    probe = subprocess.run([exe, "-rn", "true"], stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=60)
    if probe.returncode != 0:
        raise BridgeRefusal("R-14", f"`unshare -rn true` exited {probe.returncode}: {probe.stderr.strip()[-300:]}",
                            "a Linux host with user namespaces (spec 4.4)")
    return exe


def assert_env_contract(env: Mapping[str, str], os_name: str) -> None:
    want = ENV_KEYS["nt" if os_name == "nt" else "posix"]
    if set(env) != want:
        raise ChildInvalid("C-10", f"child environment keys {sorted(env)}; the contract allows exactly {sorted(want)}")


def build_launch(mode_args: Sequence[str], *, tempdir: Path, venv_python: Path | None, os_name: str = os.name,
                 unshare: str | None = None, child_cmd: Sequence[str] | None = None, script: Path = SANDBOX,
                 environ: Mapping[str, str] = os.environ) -> Launch:
    """The argv, environment, cwd and Popen arguments of one child, exactly as spec 4.3's table. Starts no process."""
    pathmod = ntpath if os_name == "nt" else posixpath
    if child_cmd is not None:
        if not child_cmd or not pathmod.isabs(str(child_cmd[0])):
            raise ValueError(f"child_cmd must start with an absolute path: {list(child_cmd)!r}")
        command = [str(c) for c in child_cmd]
    else:
        if venv_python is None:
            raise ValueError("venv_python is required without child_cmd")
        importtime = Path(script) == SANDBOX and list(mode_args[:1]) == ["run"]
        command = [str(venv_python), "-I", "-B", "-X", "utf8", *(["-X", "importtime"] if importtime else []),
                   str(script)]
    bin_dir = pathmod.dirname(command[0])
    home, tmp = pathmod.join(str(tempdir), "home"), pathmod.join(str(tempdir), "tmp")
    pipes = {"stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True,
             "encoding": "utf-8", "errors": "replace"}
    if os_name == "nt":
        root = environ["SYSTEMROOT"]
        env = {"SYSTEMROOT": root, "PATH": f"{bin_dir};{root}\\System32", "USERPROFILE": home, "HOME": home,
               "TEMP": tmp, "TMP": tmp}
        argv = [*command, *mode_args]
        popen_kwargs = {**pipes, "creationflags": CREATE_NEW_PROCESS_GROUP}
    else:
        if not unshare:
            raise BridgeRefusal("R-14", "a POSIX child needs unshare -rn (spec 4.4)",
                                "a Linux host with user namespaces (spec 4.4)")
        env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": home, "TMPDIR": tmp, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        argv = [unshare, "-rn", *command, *mode_args]
        popen_kwargs = {**pipes, "start_new_session": True}
    assert_env_contract(env, os_name)
    return Launch(argv=argv, env=env, cwd=str(tempdir), popen_kwargs=popen_kwargs)


def kill_tree(proc: subprocess.Popen, os_name: str = os.name) -> None:
    """Windows: taskkill /T /F; POSIX: SIGKILL to the child's process group (start_new_session made it a leader)."""
    if os_name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], stdin=subprocess.DEVNULL,
                       capture_output=True, encoding="utf-8", errors="replace")
        if proc.poll() is None:
            proc.kill()
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        if proc.poll() is None:
            proc.kill()


def _drain(proc: subprocess.Popen) -> tuple[str, str]:
    try:
        return proc.communicate(timeout=DRAIN_S)
    except subprocess.TimeoutExpired as exc:
        def text(x) -> str:
            return x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "")
        return text(exc.stdout), text(exc.stderr)


def run_child(launch: Launch, *, timeout: float = TIMEOUT_S, on_started: Callable[[], None] | None = None,
              os_name: str = os.name) -> ChildResult:
    """Runs one child as `launch` says; a timeout or any BaseException after Popen kills the whole tree and drains the
    pipes; a BaseException is re-raised (OPS-R2-4). Never deletes the temp dir."""
    started = time.monotonic()
    proc = subprocess.Popen(launch.argv, cwd=launch.cwd, env=launch.env, **launch.popen_kwargs)
    timed_out = False
    try:
        if on_started is not None:
            on_started()
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc, os_name)
            out, err = _drain(proc)
    except BaseException:
        kill_tree(proc, os_name)
        _drain(proc)
        raise
    code = proc.poll()
    ntstatus = (f"0x{code & 0xFFFFFFFF:08X}" if os_name == "nt" and code is not None
                and (code & 0xFFFFFFFF) >= 0xC0000000 else None)
    census, rest = parse_census(err or "")
    return ChildResult(argv=list(launch.argv), returncode=code, ntstatus=ntstatus, timed_out=timed_out,
                       seconds=round(time.monotonic() - started, 3), stdout=out or "", stderr=err or "",
                       census=census, stdout_tail=(out or "")[-TAIL_CHARS:], stderr_tail=rest[-TAIL_CHARS:])


def parse_census(stderr: str) -> tuple[list[str], str]:
    """(sorted unique module names from the `import time:` lines, the stderr without those lines) (spec 5.2.7)."""
    names, rest = set(), []
    for line in stderr.splitlines(keepends=True):
        if line.startswith("import time:"):
            fields = line.split("|")
            name = fields[2].strip() if len(fields) >= 3 else ""
            if name and name != "imported package":
                names.add(name)
            continue
        rest.append(line)
    return sorted(names), "".join(rest)


def cleanup_tempdir(tempdir: Path) -> list[str]:
    """rmtree with up to 3 attempts 0.5 s apart; returns the paths still present ([] when gone); never raises."""
    def onexc(func, path, _exc) -> None:
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            pass
    for attempt in range(3):
        if attempt:
            time.sleep(0.5)
        try:
            shutil.rmtree(tempdir, onexc=onexc)
        except OSError:
            pass
        if not os.path.lexists(tempdir):
            return []
    try:
        return sorted(str(p) for p in Path(tempdir).rglob("*")) or [str(tempdir)]
    except OSError:
        return [str(tempdir)]
```

- [ ] **Step 5: Run the module: the launch tests pass, the data and child tests fail (RED for the data files, the probe and the sandbox).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance 2>/dev/null; echo "exit $?"
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_ 2>/dev/null; echo "exit $?"
```
  Expected, first command (the FAIL tracebacks go to stderr, discarded here):
```
PASS test_l1_16_launch_builder_matches_the_contract
FAIL test_l1_17_venv_reads_and_wheel_identity FileNotFoundError: [Errno 2] No such file or directory: '/home/user/quantgen/tests/fixtures/nautilus/MANIFEST.csv'
  pyarrow in the global interpreter: None
PASS test_l1_22_global_interpreter_has_no_nautilus
NOT_RUN test_l2_01_check_env_pins_identity_precision OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_08_guard_selftest_outcomes OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_09_egress_probe_blocked OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_10_timeout_kills_the_child_tree OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
PASS test_px_census_parser_reads_importtime_lines
FAIL test_px_egress_probe_imports_json_and_socket_only FileNotFoundError: [Errno 2] No such file or directory: '/home/user/quantgen/tools/nautilus/egress_probe.py'
FAIL test_px_env_example_and_env_pins AssertionError: heading or line missing or repeated
FAIL test_px_requirements_nautilus_pins_and_header FileNotFoundError: [Errno 2] No such file or directory: '/home/user/quantgen/requirements-nautilus.txt'
PASS test_l1_32_every_test_guarded_and_ledgers_unchanged

4/12 passed, 4 failed, 4 not run
exit 1
```
  Second command: the four `test_l2_*` rows each `FAIL ... FileNotFoundError: [Errno 2] No such file or directory: '/home/user/quantgen/tools/nautilus/golden/env_pins.json'` (`layer2()` reads the pins first), then `0/4 passed, 4 failed, 0 not run` and `exit 1`.

- [ ] **Step 6: Write `requirements-nautilus.txt`** (spec 5.1): the six header lines of 5.1 verbatim, then `$S/closure/requirements-nautilus.body.txt` byte for byte, no blank line between. The command writes it; the file must then be exactly:
```text
# QUANTGEN NautilusTrader bridge: a research-only backtest engine, run only as a subprocess (spec 2026-10-26).
# NEVER install with the global python: tests/frozen_guard.py clause (d) pins numpy 2.3.5, scipy 1.18.0 and
# pandas 2.3.3, and tests/nautilus_acceptance.py fails while nautilus_trader is importable there.
# Install only into the dedicated venv (spec section 4.4), never created with --system-site-packages:
#   cmd:        "%LOCALAPPDATA%\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "%LOCALAPPDATA%\quantgen\wheels" -r requirements-nautilus.txt
#   PowerShell: & "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels" -r requirements-nautilus.txt
click==8.5.0 \
    --hash=sha256:255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360
colorama==0.4.6 ; sys_platform == "win32" \
    --hash=sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6
fsspec==2026.2.0 \
    --hash=sha256:98de475b5cb3bd66bedd5c4679e87b4fdfe1a3bf4d707b151b3c07e58c9a2437
msgspec==0.22.0 \
    --hash=sha256:0739b068f31f2004a364f97679ba91f2f5ecd6ec2a5b4b890188ab5c57d20672 \
    --hash=sha256:c6c310ef83e7e291b01a63298828f848348bb99e84a1098c4b3923c05674d032
nautilus-trader==1.231.0 \
    --hash=sha256:5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf \
    --hash=sha256:429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91
numpy==2.3.5 \
    --hash=sha256:00dc4e846108a382c5869e77c6ed514394bdeb3403461d25a829711041217d5b \
    --hash=sha256:11e06aa0af8c0f05104d56450d6093ee639e15f24ecf62d417329d06e522e017
pandas==2.3.3 \
    --hash=sha256:f8bfc0e12dc78f777f323f55c58649591b2cd0c43534e8355c51d3fede5f4dee \
    --hash=sha256:318d77e0e42a628c04dc56bcef4b40de67918f7041c2b061af1da41dcff670ac
portion==2.6.3 \
    --hash=sha256:9f5a26de92ff1241c7ba7ab23da0b544e67308187100681512871a50d6d206f1
pyarrow==26.0.0 \
    --hash=sha256:3de30a7432b48b98b9decbd9e25a53bb9251d202c2e6c5a29a50869592ccb117 \
    --hash=sha256:240bd18a7487f8767616a948a69dd4e740a8bc36a1c9da49e4dc9a32c5c2faed
python-dateutil==3.0.0 \
    --hash=sha256:3c79630202e4152c6add678446984236efe4f57e84d8e892aab0637bab82e9fd
pytz==2026.5 \
    --hash=sha256:e658af3757f9e26a9d25dd2aff38335acd92bc9104f890a894b2c1ba28311b03
six==1.17.0 \
    --hash=sha256:4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274
sortedcontainers==2.4.0 \
    --hash=sha256:a163dcaede0f1c021485e957a39245190e74249897e2ae4b2aa38595db237ee0
tqdm==4.70.1 \
    --hash=sha256:c293e525e6fef9c20e8728fd4612df02a0aa31bb5fe91ecd93e123b1b7bffa73
tzdata==2026.5 \
    --hash=sha256:b683bd1b6659ddcd810ff02ad09ba821d4bf1065072805063eb35c49617905ac
uvloop==0.22.1 ; sys_platform != "win32" \
    --hash=sha256:0530a5fbad9c9e4ee3f2b33b148c6a64d47bbad8000ea63704fa8260f4cf728e
```
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
cat > "$S/t1_req_header.txt" <<'EOF'
# QUANTGEN NautilusTrader bridge: a research-only backtest engine, run only as a subprocess (spec 2026-10-26).
# NEVER install with the global python: tests/frozen_guard.py clause (d) pins numpy 2.3.5, scipy 1.18.0 and
# pandas 2.3.3, and tests/nautilus_acceptance.py fails while nautilus_trader is importable there.
# Install only into the dedicated venv (spec section 4.4), never created with --system-site-packages:
#   cmd:        "%LOCALAPPDATA%\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "%LOCALAPPDATA%\quantgen\wheels" -r requirements-nautilus.txt
#   PowerShell: & "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels" -r requirements-nautilus.txt
EOF
cat "$S/t1_req_header.txt" "$S/closure/requirements-nautilus.body.txt" > requirements-nautilus.txt
sha256sum "$S/closure/requirements-nautilus.body.txt" requirements-nautilus.txt; wc -l requirements-nautilus.txt
```
  Expected: `49c1cee13798cbc92104bd398af422f611334db1f79260231c0c357fd7d0b5e4` for the body, `7a720e247bf1a5708aa19e79c1291b6baef87c837719c669ebe5f24e4a4a7e0e  requirements-nautilus.txt`, `43 requirements-nautilus.txt`. Then the install check of spec Step 3's done-when, offline, into a fresh scratch venv (never the global interpreter):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
rm -rf "$S/ntvenv_t1" && python3 -m venv "$S/ntvenv_t1"
"$S/ntvenv_t1/bin/python" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$S/closure/linux" -r requirements-nautilus.txt 2>&1 | tail -1
"$S/ntvenv_t1/bin/python" -m pip check
```
  Expected (about 25 s): `Successfully installed click-8.5.0 fsspec-2026.2.0 msgspec-0.22.0 nautilus-trader-1.231.0 numpy-2.3.5 pandas-2.3.3 portion-2.6.3 pyarrow-26.0.0 python-dateutil-3.0.0 pytz-2026.5 six-1.17.0 sortedcontainers-2.4.0 tqdm-4.70.1 tzdata-2026.5 uvloop-0.22.1`, then `No broken requirements found.`

- [ ] **Step 7: Edit `.env.example`** (LF; spec 3.4) with the Edit tool. old_string:
```
NEXTGEN_NO_DATA_GRACE=3
```
  new_string (the heading block in the file's section style, then the one line; no `%VAR%`):
```
NEXTGEN_NO_DATA_GRACE=3

# --- NautilusTrader bridge (research only) ----------------------------------
# The python of the hash-pinned NautilusTrader venv (spec 2026-10-26, 4.4);
# blank leaves the nautilus layer-2 tests NOT_RUN. Single quotes and forward
# slashes only: in double quotes, python-dotenv reads \n in \ntvenv as a newline.
QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'
```
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git diff --stat .env.example; python3 -c "b = open('.env.example', 'rb').read(); assert b'\r' not in b and b.endswith(b\"python.exe'\n\"); print('LF ok')"
```
  Expected: `1 file changed, 6 insertions(+)` and `LF ok` (at `fa28059` the file's md5 becomes `9969fe1e6b8c5f9336a6fb87289ee5df`).

- [ ] **Step 8: Add both wheels' `RECORD` files as fixtures** (spec 6.7; QA-R2-14), copied byte for byte out of the wheel files, and their manifest.
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -I -c "
import sys, zipfile
from pathlib import Path
out = Path('tests/fixtures/nautilus'); out.mkdir(parents=True, exist_ok=True)
for wheel, tag in ((sys.argv[1], 'manylinux_2_35_x86_64'), (sys.argv[2], 'win_amd64')):
    (out / f'nautilus_trader-1.231.0.{tag}.RECORD').write_bytes(zipfile.ZipFile(wheel).read('nautilus_trader-1.231.0.dist-info/RECORD'))
" "$S/closure/linux/nautilus_trader-1.231.0-cp313-cp313-manylinux_2_35_x86_64.whl" "$S/closure/win/nautilus_trader-1.231.0-cp313-cp313-win_amd64.whl"
md5sum tests/fixtures/nautilus/*.RECORD; wc -c tests/fixtures/nautilus/*.RECORD | head -2
```
  Expected: `bf0dd9ec1cce4d6b67771d372ced5dfc  tests/fixtures/nautilus/nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD`, `9cb7bcf1fd8ecd9f6f3d7f3b430f1d0e  tests/fixtures/nautilus/nautilus_trader-1.231.0.win_amd64.RECORD`; 80255 and 78902 bytes. Then create `tests/fixtures/nautilus/MANIFEST.csv` with exactly this content (LF; md5 `f0d6597019cbd34e9abd03af82df12db`; the header is `tests.notrun.MANIFEST_COLUMNS`):
```text
file,source,series,span,retrieved_at_utc,value_status_rule,md5,licence,owner,tests
nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD,member nautilus_trader-1.231.0.dist-info/RECORD of nautilus_trader-1.231.0-cp313-cp313-manylinux_2_35_x86_64.whl (PyPI sha256 429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91),wheel RECORD,n/a,2026-10-26T14:52:07Z,not data (no value_status); the wheel identity of spec 2026-10-26 section 6.7,bf0dd9ec1cce4d6b67771d372ced5dfc,LGPL-3.0,nautilus bridge (spec 2026-10-26),test_l1_17_venv_reads_and_wheel_identity
nautilus_trader-1.231.0.win_amd64.RECORD,member nautilus_trader-1.231.0.dist-info/RECORD of nautilus_trader-1.231.0-cp313-cp313-win_amd64.whl (PyPI sha256 5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf),wheel RECORD,n/a,2026-10-26T14:52:22Z,not data (no value_status); the wheel identity of spec 2026-10-26 section 6.7,9cb7bcf1fd8ecd9f6f3d7f3b430f1d0e,LGPL-3.0,nautilus bridge (spec 2026-10-26),test_l1_17_venv_reads_and_wheel_identity
```

- [ ] **Step 9: Write `tools/nautilus/golden/env_pins.json` and `docs/nautilus_bridge/.gitignore`.** `env_pins.json` (C7, in the bridge's JSON bytes: `json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"`; md5 `fefda88ce53955eef99a2e793f0a6ce0`):
```json
{
 "platforms": {
  "manylinux_2_35_x86_64": {
   "python_minor": "3.13",
   "record_digest_sha256": "a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9",
   "record_entries": 764,
   "versions": {
    "nautilus_trader": "1.231.0",
    "numpy": "2.3.5",
    "pandas": "2.3.3"
   },
   "wheel_tag": "cp313-cp313-manylinux_2_35_x86_64"
  },
  "win_amd64": {
   "python_minor": "3.13",
   "record_digest_sha256": "47d274d79b85a43b79917e9b993fa3e68ebf68138c4a8b86527c5902cf439555",
   "record_entries": 764,
   "versions": {
    "nautilus_trader": "1.231.0",
    "numpy": "2.3.5",
    "pandas": "2.3.3"
   },
   "wheel_tag": "cp313-cp313-win_amd64"
  }
 },
 "schema": "nautilus-bridge-env-pins/1"
}
```
  `docs/nautilus_bridge/.gitignore` (spec 5.3.5; one line, LF; md5 `54aed7ce4481fd5ac8cdcd86cb6a6e52`):
```
runs/.locks/
```

- [ ] **Step 10: Run the module again: the data tests pass; the probe and the sandbox are still missing (RED).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance 2>/dev/null | tail -1
python3 -B -m tests.nautilus_acceptance -k test_px_egress 2>/dev/null | head -1
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_ 2>/dev/null; echo "exit $?"
```
  Expected: `7/12 passed, 1 failed, 4 not run`; `FAIL test_px_egress_probe_imports_json_and_socket_only FileNotFoundError: [Errno 2] No such file or directory: '/home/user/quantgen/tools/nautilus/egress_probe.py'`; then
```
FAIL test_l2_01_check_env_pins_identity_precision AssertionError: (2, "/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ntvenv_hash/bin/python: can't open file '/home/user/quantgen/tools/nautilus/sandbox.py': [Errno 2] No such file or directory\n")
FAIL test_l2_08_guard_selftest_outcomes AssertionError: (2, '', "/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ntvenv_hash/bin/python: can't open file '/home/user/quantgen/tools/nautilus/sandbox.py': [Errno 2] No such file or directory\n")
FAIL test_l2_09_egress_probe_blocked JSONDecodeError: Expecting value: line 1 column 1 (char 0)
PASS test_l2_10_timeout_kills_the_child_tree

1/4 passed, 3 failed, 0 not run
exit 1
```
  L2-10 needs only `launch.py` and the pins, so it is GREEN from here (its RED was Step 3 and Step 5).

- [ ] **Step 11: Implement `tools/nautilus/egress_probe.py`** (spec 4.4; C4) with exactly this content (LF; md5 `39eda6907eb209e50ad7092565c31f3c`). It imports `json` and `socket` only and passes the unamended T-RO-01 scan (`socket` is not in `FORBIDDEN_IMPORTS`, `tests/macro_m0_harness.py:38-42`).
```python
"""Egress probe of the NautilusTrader bridge (spec 2026-10-26 section 4.4; SECURITY-1).

Launched in the venv through tools/nautilus/launch.py, exactly as the sandbox is: one TCP connect to 1.1.1.1:443.
Prints one JSON line {"blocked": bool, "errno": int or null, "error": str}; exit 0 when the connect failed, 1 when
it connected (the socket is closed at once). Imports json and socket only: nothing from the engine or QUANTGEN.
"""
import json
import socket


def probe(host="1.1.1.1", port=443, timeout=3):
    try:
        conn = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return {"blocked": True, "errno": exc.errno, "error": f"{type(exc).__name__}: {exc}"}
    conn.close()
    return {"blocked": False, "errno": None, "error": ""}


if __name__ == "__main__":
    result = probe()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["blocked"] else 1)
```
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance -k test_px_egress
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_09
```
  Expected: `PASS test_px_egress_probe_imports_json_and_socket_only` and `1/1 passed, 0 failed, 0 not run`; `PASS test_l2_09_egress_probe_blocked` and `1/1 passed, 0 failed, 0 not run`.

- [ ] **Step 12: Implement `tools/nautilus/sandbox.py`, Task 1 part** (spec 5.2.1, 5.2.3 rows Engine, Kernel check and Fee model, 5.2.5's guard, 5.2.8's `inside`, 5.2.9; C3) with exactly this content (LF; md5 `5818b883a0dc3ebc453a346ab31201c2`). The import block, `VENUE`, `Refused`, `inside`, `plain_mean`, both guards, `make_fee_model`, `build_engine`, `check_env`, `guard_selftest`, `main` and the `__main__` guard are spec 5.2.9's text; the module docstring is new; `run` refuses every input (exit 20, C-05's code) until Task 3. Not here, and added by Task 3 between `build_engine` and `run` in 5.2.9's order: `PortConfig`, `TrendSwitchConfig`, `CryptoTrendConfig`, `Port` (with `place`), `TrendSwitchPort`, `CryptoTrendPort`, and `run`'s body. Exit codes: 0 (`--check-env`; `--guard-selftest` with the five expected outcomes), 20 (`run`, any input; a `--in` that is not absolute or not its own `resolve()`), 30 (`--guard-selftest` with a wrong outcome; the runner's R-03, QA-R2-10), 2 (argparse: an unknown argument, a crash code by 5.2.1). No string or name in it contains a T-RO-01 token, a `NAUTILUS_DENIED_PREFIXES` or a `NAUTILUS_DENIED_NAMES` entry (rule E, Task 2).
```python
"""The NautilusTrader sandbox child (spec 2026-10-26 section 5.2), run only in the hash-pinned venv and launched only
through tools/nautilus/launch.py:

    <venv python> -I -B -X utf8 [-X importtime] <abs sandbox.py> {--check-env | --guard-selftest | run --in <dir>}

Exit codes (5.2.1): 0 valid; 10 complete but invalid; 20 input refused before the engine is built; 30 a self-test
case misbehaved; any other value a crash. The structure is spec 5.2.9's. Plan Task 1 builds the two self-checks;
`run` refuses every input with exit 20 until plan Task 3 builds section 5.2 in full.
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy

VENUE = Venue("SIM")
class Refused(Exception): pass                     # input refused before the engine is built: exit 20
def inside(root, name):                             # 5.2.8: builds every path the sandbox opens
    p = (root / name).resolve()
    if p.parent != root:
        raise Refused(name)
    return p
def plain_mean(xs):                                 # 5.2.5, both ports: a left-to-right loop, never sum()
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)
def require_backtest_environment(env):              # 5.2.5 (C-2)
    if env is not Environment.BACKTEST:
        raise RuntimeError(f"kernel environment {env.name}, not BACKTEST")
def require_backtest_clock(clock):
    if not isinstance(clock, TestClock):
        raise RuntimeError("the strategy clock is not a TestClock")
def make_fee_model(cost_bps, stress):               # 5.2.3: a closure, so no __init__ and no super()
    if Decimal(stress) < 1:
        raise ValueError("stress below 1")
    rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)
    class BpFeeModel(FeeModel):
        def get_commission(self, order, fill_qty, fill_px, instrument):
            return Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate,
                         instrument.quote_currency)
    return BpFeeModel()
def build_engine():                                 # 5.2.3, rows Engine and Kernel check
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), run_analysis=False,
                                                 logging=LoggingConfig(log_level="ERROR", log_colors=False)))
    require_backtest_environment(engine.kernel.environment)
    return engine
def run(root):                                      # plan Task 1: every input is refused (exit 20); Task 3: 5.2
    raise Refused("run is built at plan Task 3")
def check_env():                                    # --check-env: one JSON line, no file (5.2.1)
    engine = build_engine()
    u = platform.uname()                            # not platform.system(): rule F6 flags any call named system
    print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                      "system": u.system, "machine": u.machine, "environment": engine.kernel.environment.name,
                      "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                                    "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX}}))
    engine.dispose()
    return 0
def guard_selftest():                               # --guard-selftest: exit 0, or 30 on a wrong outcome (5.2.1)
    out = {}
    env, clock = require_backtest_environment, require_backtest_clock
    for name, fn, arg in (("sandbox", env, Environment.SANDBOX), ("live", env, Environment.LIVE),
                          ("live_clock", clock, LiveClock()), ("backtest", env, Environment.BACKTEST),
                          ("test_clock", clock, TestClock())):
        try:
            fn(arg)
            out[name] = "passed"
        except RuntimeError:
            out[name] = "raised"
    print(json.dumps(out, sort_keys=True))
    return 0 if list(out.values()) == ["raised"] * 3 + ["passed"] * 2 else 30
def main():
    ap = argparse.ArgumentParser(prog="sandbox.py")
    ap.add_argument("--check-env", action="store_true"); ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv[1:])
    if a.check_env or a.guard_selftest:
        return check_env() if a.check_env else guard_selftest()
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute() or root != root.resolve():
        return 20
    try:
        return run(root)
    except Refused:
        return 20
if __name__ == "__main__":                          # SECURITY-R3-1: __name__ is a Name, not an Attribute (F3)
    exit(main())
```
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_01 -k test_l2_08
```
  Expected: `PASS test_l2_01_check_env_pins_identity_precision`, `PASS test_l2_08_guard_selftest_outcomes`, `2/2 passed, 0 failed, 0 not run`.

- [ ] **Step 13: Run the whole module (GREEN).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance; echo "exit $?"
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance | tail -1
QUANTGEN_NAUTILUS_PYTHON="$S/ntvenv_t1/bin/python" python3 -B -m tests.nautilus_acceptance -k test_l2_ | tail -1
QUANTGEN_NAUTILUS_PYTHON=/nonexistent/ntvenv/bin/python python3 -B -m tests.nautilus_acceptance -k test_l2_01 | head -1
python3 -B -m tests.nautilus_acceptance -k no_such_test | tail -1; echo "exit ${PIPESTATUS[0]}"
```
  Expected, first command:
```
PASS test_l1_16_launch_builder_matches_the_contract
PASS test_l1_17_venv_reads_and_wheel_identity
  pyarrow in the global interpreter: None
PASS test_l1_22_global_interpreter_has_no_nautilus
NOT_RUN test_l2_01_check_env_pins_identity_precision OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_08_guard_selftest_outcomes OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_09_egress_probe_blocked OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_10_timeout_kills_the_child_tree OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
PASS test_px_census_parser_reads_importtime_lines
PASS test_px_egress_probe_imports_json_and_socket_only
PASS test_px_env_example_and_env_pins
PASS test_px_requirements_nautilus_pins_and_header
PASS test_l1_32_every_test_guarded_and_ledgers_unchanged

8/12 passed, 0 failed, 4 not run
exit 0
```
  then `12/12 passed, 0 failed, 0 not run` (6 to 20 s), `4/4 passed, 0 failed, 0 not run` (the fresh venv of Step 6), `NOT_RUN test_l2_01_check_env_pins_identity_precision OWNER: QUANTGEN_NAUTILUS_PYTHON points to a missing file: '/nonexistent/ntvenv/bin/python'`, and `0/0 passed, 0 failed, 0 not run` with `exit 1` (nothing matched is not a pass).

- [ ] **Step 14: Check spec Step 3's done-when through the launch contract.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B - "$NTPY" <<'EOF'
import json, sys
from pathlib import Path
from tools.nautilus import launch
python = launch.resolve_venv_python(sys.argv[1])
reads = launch.read_venv(python)
print("identity", reads["wheel"]["wheel_tag"], reads["wheel"]["record_digest_sha256"], reads["wheel"]["record_entries"])
print("versions", reads["python_minor"], json.dumps(reads["versions"], sort_keys=True), "mismatches", launch.venv_mismatches(reads))
unshare = launch.resolve_unshare()
for mode, script in ((["--check-env"], launch.SANDBOX), (["--guard-selftest"], launch.SANDBOX), ([], launch.EGRESS_PROBE), (["run", "--in", None], launch.SANDBOX)):
    tmp = launch.make_tempdir()
    args = [str(tmp) if a is None else a for a in mode]
    r = launch.run_child(launch.build_launch(args, tempdir=tmp, venv_python=python, unshare=unshare, script=script), timeout=300)
    print(" ".join(r.argv[:2]), Path(script).name, *args[:1], "-> exit", r.returncode, r.stdout.strip() or "-", f"census {len(r.census)}", "left", launch.cleanup_tempdir(tmp))
EOF
python3 -c "import importlib.util, numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, scipy.__version__, importlib.util.find_spec('nautilus_trader'))"
sha256sum -c "$S/t1_pre_sha256.txt"
```
  Expected (about 4 s for the first command):
```
identity cp313-cp313-manylinux_2_35_x86_64 a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9 764
versions 3.13 {"nautilus-trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"} mismatches []
/usr/bin/unshare -rn sandbox.py --check-env -> exit 0 {"schema": "nautilus-bridge-check-env/1", "python": "3.13.17", "system": "Linux", "machine": "x86_64", "environment": "BACKTEST", "precision": {"HIGH_PRECISION": true, "FIXED_PRECISION": 16, "QUANTITY_MAX": 34028236692093.0, "PRICE_MAX": 17014118346046.0}} census 0 left []
/usr/bin/unshare -rn sandbox.py --guard-selftest -> exit 0 {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"} census 0 left []
/usr/bin/unshare -rn egress_probe.py -> exit 0 {"blocked": true, "errno": 101, "error": "OSError: [Errno 101] Network is unreachable"} census 0 left []
/usr/bin/unshare -rn sandbox.py run -> exit 20 - census 942 left []
```
  (a census count other than 942 is recorded, not a Task 1 failure: the census baseline is Task 4's); then `2.3.5 2.3.3 1.18.0 None`; then six lines `<file>: OK` for `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`, `tests/run_all.py` and `README.md` (byte-identical to Step 0, CONTRACT ISSUE 5).

- [ ] **Step 15: Guard checks (T-RO-01 before its amendment).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.macro_m0_harness | tail -1
python3 -B -c "
from tests.macro_m0_harness import _offences, _scan_files, ROOT
files = [p for p in _scan_files() if p.relative_to(ROOT).as_posix().startswith('tools/nautilus/')]
print([p.relative_to(ROOT).as_posix() for p in files], [h for p in files for h in _offences(p)])
"
```
  Expected: `12/12 passed, 0 failed, 0 not run`; `['tools/nautilus/__init__.py', 'tools/nautilus/egress_probe.py', 'tools/nautilus/launch.py', 'tools/nautilus/sandbox.py'] []`. test_08 and test_09 scan `runtime_py()` only and the flet guard `ui/` only; their rows are checked in Step 16's full run (unchanged from Step 0).

- [ ] **Step 16: Run the full suite through the wrapper and compare it with Step 0 (delta 0).** Background run, as in Step 0:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
md5sum qa/acceptance_results.json
python3 -B "$S/run_baseline.py" "$S/t1_after.json" > "$S/t1_after.log" 2>&1; echo "exit $?"
```
  When it has finished:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
tail -1 "$S/t1_after.log"; md5sum qa/acceptance_results.json
python3 - "$S/t1_baseline.json" "$S/t1_after.json" <<'EOF'
import json, sys
a, b = ({r["test"]: r["status"] for r in json.load(open(p, encoding="utf-8"))} for p in sys.argv[1:3])
print("added", sorted(set(b) - set(a)))
print("removed", sorted(set(a) - set(b)))
print("changed", sorted((k, a[k], b[k]) for k in a.keys() & b.keys() if a[k] != b[k]))
EOF
```
  Expected: the summary is `B` exactly (only the results path after `;` differs); the md5 is `16c9baa5a1777853521d485d5078e456` before and after; `added []`, `removed []`, `changed []` (so `safety/test_08_no_broker_order_path`, `safety/test_09_no_account_credentials_requested`, the `ui/` rows and every `macro/macro_m0_harness/test_t_ro_01_*` row keep Step 0's PASS).

- [ ] **Step 17: Line ends and untouched files.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -c "import sys; bad = [p for p in sys.argv[1:] if b'\r' in open(p, 'rb').read()]; print('LF ok' if not bad else bad)" requirements-nautilus.txt .env.example tests/nautilus_acceptance.py tools/nautilus/__init__.py tools/nautilus/launch.py tools/nautilus/egress_probe.py tools/nautilus/sandbox.py tools/nautilus/golden/env_pins.json tests/fixtures/nautilus/MANIFEST.csv tests/fixtures/nautilus/nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD tests/fixtures/nautilus/nautilus_trader-1.231.0.win_amd64.RECORD docs/nautilus_bridge/.gitignore
python3 -c "b = open('tests/run_all.py', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'tests/run_all.py must stay CRLF'; print('CRLF ok')"
python3 -c "b = open('README.md', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'README.md must stay CRLF'; print('CRLF ok')"
sha256sum -c --quiet "$S/t1_pre_sha256.txt" && echo "unchanged"
```
  Expected: `LF ok`, `CRLF ok`, `CRLF ok`, `unchanged`. Task 1 edits no CRLF file.

- [ ] **Step 18: Commit.** `git status --short` must show exactly these six lines, plus any path Step 0 recorded as already modified or untracked (left unstaged):
```
 M .env.example
?? docs/nautilus_bridge/.gitignore
?? requirements-nautilus.txt
?? tests/fixtures/nautilus/
?? tests/nautilus_acceptance.py
?? tools/nautilus/
```
  No `__pycache__` (ignored), no `qa/acceptance_results.json`, no `requirements.txt`. Then:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git add requirements-nautilus.txt .env.example tools/nautilus/__init__.py tools/nautilus/launch.py tools/nautilus/egress_probe.py tools/nautilus/sandbox.py tools/nautilus/golden/env_pins.json tests/fixtures/nautilus/MANIFEST.csv tests/fixtures/nautilus/nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD tests/fixtures/nautilus/nautilus_trader-1.231.0.win_amd64.RECORD tests/nautilus_acceptance.py docs/nautilus_bridge/.gitignore
git status --short
git commit -F - <<'EOF'
nautilus bridge, plan Task 1 (spec Step 3): environment and launch contract

requirements-nautilus.txt: spec 5.1's header and the hashed closure body
(16 distributions, PyPI hashes), for the venv only; .env.example: the
QUANTGEN_NAUTILUS_PYTHON line in single quotes. tools/nautilus/: launch.py
(the launch contract of spec 4.3 with unshare -rn and a tree kill, the venv
and wheel-identity reads of 6.7, the census parser of 5.2.7), sandbox.py
(5.2.9's import block, both backtest guards, the fee closure, --check-env
and --guard-selftest; run refuses every input with exit 20 until Task 3),
egress_probe.py (json and socket only), golden/env_pins.json (both
platforms); both wheels' RECORD files as md5-listed fixtures;
docs/nautilus_bridge/.gitignore. tests/nautilus_acceptance.py: the guard of
spec 3.3, the layer-2 gate and 12 tests (8 layer 1, 4 layer 2), run by its
module CLI until Task 2 registers the suite. Full suite unchanged against
the Step 0 baseline; qa/acceptance_results.json untouched.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
EOF
git show --stat HEAD | tail -1; git status --short; md5sum qa/acceptance_results.json
```
  Expected: the staged `git status --short` shows `M  .env.example` and `A  ` for the other 11 paths; `12 files changed, 2826 insertions(+)`; then only Step 0's pre-existing paths (empty at `fa28059`); `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`. No push.

---

### Task 2: Guard (spec Step 4): the T-RO-01 amendment, the `nautilus` suite registration, registry and README

**Verified before writing (2026-10-28, HEAD `fa28059` on `claude/amazing-gauss-tdiguu`). Files were read in the real clone. Every run happened in the scratch clone `$S/plan_step2/task2/clone`. Nothing in the repository was touched.**
- **Repository state.** The working tree is clean, and `md5sum qa/acceptance_results.json` prints `16c9baa5a1777853521d485d5078e456`. `studies-of-record-2026-10-23` is the owner's real annotated tag (object `6e7c1f7`, which peels to `eacd57d`); it is never pushed, moved or deleted. `requirements.txt` carries `statsmodels>=0.14.2` (`6054b33`). No file under `tests/` has changed since `b7f991a`.
- **`tests/macro_m0_harness.py`** is LF and ASCII before this task; the `§` that spec 5.6 writes in a comment makes it UTF-8.
  - Imports are at :9-17 and include no `hashlib`. `FORBIDDEN_CALLS` is at :44-50. `ALLOWED_BARE_CALLS` is at :56; spec 5.6 inserts the new constants after it.
  - `_scan_files` (:66-70) scans `runtime_py()`, `docs/*.py`, `tools/` and `papers/`.
  - `_offences` (:81-109) parses `_code_only(path)` (:83, :88) and ends with `return hits` (:109). That is the only `return hits` that follows the bare-call line :108. `_yaml_offences` (:112-133) also ends with `return hits` and reads `FORBIDDEN_CALLS` at :130.
  - `test_t_ro_01_scan_reaches_tools_and_papers` (:175-192) carries no `test_ids`. The next test starts at :195. `test_registry_implemented_in_matches_test_ids` is at :286-298.
  - `test_every_macro_module_runs_alone_under_the_guard` (:396-424) requires the three tail lines at :435-437.
  - `python3 -B -m tests.macro_m0_harness` gives `12/12 passed, 0 failed, 0 not run`.
- **`tests/acceptance.py`.** `_code_only` (:33-47) returns `ast.unparse` output with docstrings removed. String constants therefore come back single-quoted, and an existing text hit reads `<rel>: 'submit_order'`. `runtime_py` (:50-56) covers only `core/`, `data/`, `ui/`, `main.py` and `config.py`, so `tools/` stays outside test_08 (:62-68) and test_09 (:71-75). This task does not change either test.
- **Today's scan** gives 0 hits over 154 files. None of the seven `NAUTILUS_ORDER_VERBS` occurs in a scanned file or in `core/skills/macro_workflows/macro_daily.yaml`, so rule B adds no hit to the real tree.
- **`tests/macro_acceptance.py`.** `implemented_in` is at :267-274. `sync_registry` (:277-291) writes through `csv.DictWriter` with `lineterminator="\n"`. `python3 -B -m tests.macro_acceptance` imports the macro modules without running them and prints `implemented_in rows changed: <n>` (:294-295). `tests/macro_registry.csv:12` is the T-RO-01 row (LF), with 5 entries.
- **`tests/macro_m1_fixtures.py:205-215`** runs `literal_eval` on every module-level assignment of every `tests/macro_*.py` inside `suppress(ValueError, SyntaxError)`. The new constants are skipped, and `_SANDBOX_SKELETON` is a plain literal. That module gives `13/15 passed, 0 failed, 2 not run` before and after this task, the same as the cloud baseline.
- **`tests/run_all.py`** is CRLF, 146 lines. `papers_tests` is at :57-71. `tests()` is at :74-85, with the `papers/` term last (:85). The `--suite` help is at :131. `main` writes `OUT` at :136-137, which the wrapper redirects.
- **`README.md`** is CRLF. The `--suite` comment is at :853, the `papers` row at :877 and the Total row at :878 (`743/864 passed, 0 failed, 121 not run (2026-10-23)`). The README tests (`tests/macro_ui_components.py:137-180`) check only phrases, and `tests/flet_api_guard.py` reads only `ui/`.
- **Pending audit patches touch the same lines.** `docs/audit/2026-10-27/c01_v01_cache_and_vendors.md` adds a `cache` suite before `papers` and changes the help to `guard, cache or papers`. `docs/audit/2026-10-27/bonds_screen_audit.md:889-890` adds a `bonds` suite and its README entry. The anchors used below survive either patch: ` or papers")`, ` or papers`, the `papers/` term and the Total row.
- **Spec sources.** Spec 5.6's constants equal `scratch:rev4_probe/scan4.py:9-50`. The 5.2.9 block of the spec is byte-identical to `scratch:rev4_probe/skeleton.py`: 141 lines, md5 `484ad92fbf352616078f26be4ff41121`, ASCII, with no `'''` and no backslash. `scratch:rev4_probe/scan4.out` holds the multisets of 8.5 and both digests (`2792ad4a...` and `70bcf50f...`).
- **Dry run of every step below in the scratch clone.** Task 1 was replaced by stand-ins:
  - the 5.2.9 skeleton without the `Port` classes, with `run` refusing;
  - `scratch:rev2_probe/egress_probe.py`;
  - a small `launch.py` that obeys C1;
  - a C8-shaped `tests/nautilus_acceptance.py` carrying Task 1's 12 test names.

  Results:
  - Each RED step failed as stated.
  - After the resync the harness module gave `14/14`, and the resync changed only row 12.
  - All 51 controls gave their 8.5 multisets.
  - The real-tree scan gave 0 hits over 158 files.
  - `scratch:rev4_probe/sandbox_r4.py`, the filled Revision-4 sandbox, gave no scan hit and no L1-15 hit.
  - Each of three mutations made its test fail: dropping F4, exempting every rule-A case, and removing `api_key` from `NAUTILUS_DENIED_NAMES`.
  - `--suite nautilus`, run through a copy of the wrapper pointed at the clone, gave `9/13 passed, 0 failed, 4 not run` with the key unset.
  - `qa/acceptance_results.json` kept its md5.

**Files:**
- Modify `tests/macro_m0_harness.py` (LF):
  - add `import hashlib`;
  - insert the 5.6 constants and rule B after `ALLOWED_BARE_CALLS` (:56);
  - make `_offences` return `_nautilus_offences(tree, rel, hits)` (:109), with rules A to F after it;
  - insert the test block (skeleton, helpers, two tests) after :192.
- Modify `tests/macro_registry.csv` (LF): row 12 `implemented_in`, rewritten only by `python3 -B -m tests.macro_acceptance`.
- Modify `tests/nautilus_acceptance.py` (Task 1's file, LF): add `encoding_offences` and `test_l1_15_encoding_rules_hold` before `def tests(`.
- Modify `tests/run_all.py` (CRLF, Edit tool only): add `nautilus_tests()`, make the `nautilus/` term the last term of `tests()`, and extend the `--suite` help.
- Modify `README.md` (CRLF, Edit tool only): extend the `--suite` comment (:853) and add the `nautilus` row before the Total row. The Total row does not change.
- Modify only if Step 10 flags one: a Task 1 file and line that breaks C1, by adding the missing keyword.
- Test: `tests/macro_m0_harness.py` (suite `macro`) and `tests/nautilus_acceptance.py` (suite `nautilus`, registered here).

**Interfaces:**
- **Consumes:**
  - C1: the encoding convention that L1-15 enforces.
  - C2: `tools/nautilus/launch.py` exists. `FIXTURES` and `fixture_inputs` (added at Task 3) are read through `getattr`.
  - C3: `tools/nautilus/sandbox.py` exists as Task 1 left it, with no `submit_order` node (CONTRACT ISSUE 5).
  - C4: `tools/nautilus/egress_probe.py` is scanned as the "egress probe" control of 8.5.
  - C8: `ROOT`, `tests()`, the guard, the NotRun reasons of `layer2()`, and the CLI with `-k`.
  - The Count Ledger rows of Tasks 1 and 2, and Test inventory row 2.
- **Produces:** no Interface Contract item. For Tasks 3 to 5:
  - The amended `tests.macro_m0_harness._offences(path: Path, root: Path = ROOT) -> list[str]` (rules A to F; every new hit starts `[nautilus:<rule>]`) and the constants of spec 5.6. Every later bridge file must pass them; Task 3's filled sandbox is checked by `test_t_ro_01_nautilus_confined_to_the_sandbox`.
  - `tests.nautilus_acceptance.encoding_offences(source: str, rel: str) -> list[str]` and L1-15. Every later `tools/nautilus/*.py` and `tests/nautilus_*.py` must pass them, and L1-15 starts checking `launch.fixture_inputs` once Task 3 adds it.
  - `tests.run_all.nautilus_tests()`. From this task on, the full run counts `nautilus/<test>` rows.

- [ ] **Step 1: Confirm the starting point.** (Plan rules, Result files: this step reads the baseline file that Task 1 Step 0 writes, `$S/t1_baseline.json`.)
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git log -1 --format='%h %s'; git status --short; md5sum qa/acceptance_results.json
python3 -B -m tests.macro_m0_harness | tail -1
env -u QUANTGEN_NAUTILUS_PYTHON python3 -B -m tests.nautilus_acceptance | tail -1
python3 -B -c "import tests.macro_m0_harness as H; print(sum(len(H._offences(p)) for p in H._scan_files()), 'hits')"
python3 -B -c "import json, sys; r = json.load(open(sys.argv[1], encoding='utf-8')); n = len(r); p = sum(x['status'] == 'PASS' for x in r); f = sum(x['status'] == 'FAIL' for x in r); print(f'B = {p}/{n} passed, {f} failed, {n - p - f} not run;', sum(x['test'].startswith('macro/') for x in r), 'macro rows')" $S/t1_baseline.json
```
  Expected:
  - HEAD is Task 1's commit.
  - `git status --short` prints nothing. Any line it does print is a path no task owns: write it down and never stage it.
  - `16c9baa5a1777853521d485d5078e456`.
  - `H/H passed, 0 failed, 0 not run`, where H is the harness count (12 at `fa28059`; the Count Ledger's `H`, not `M`, the macro row count).
  - `8/12 passed, 0 failed, 4 not run`.
  - `0 hits`: Task 1's files pass today's scan.
  - The `B = ...` line that Task 1 Step 0 recorded. Reference: `B = 745/870 passed, 1 failed, 124 not run; 542 macro rows`.

  A FAIL in the harness module, or any hit, stops the task: it belongs to the task that caused it.

- [ ] **Step 2: Write the failing T-RO-01 tests.** Make two edits to `tests/macro_m0_harness.py` with the Edit tool. The file is LF and stays LF. (CONTRACT ISSUE 2: this module is the scanner. Its tests name the forbidden tokens in the 8.5 controls and in the embedded skeleton, as its own `FORBIDDEN_TEXT_CI` already does. `tests/` is outside every scan.)

  Edit A. Current text:
```python
import csv
import json
```
  New text:
```python
import csv
import hashlib
import json
```
  Edit B. The old text is the line `def test_t_ro_01_artifact_writers_stamp_read_only():`, which is unique. The new text is the block below, then two blank lines, then that same line. The block therefore follows `test_t_ro_01_scan_reaches_tools_and_papers` (:175-192) after two blank lines. The block, verbatim:
```python
# The 5.2.9 skeleton of tools/nautilus/sandbox.py, verbatim from spec 2026-10-26: the sandbox positive control of 8.5
# and the base of every "sandbox +" control (measured with scratch:rev4_probe/scan4.py).
_SANDBOX_SKELETON = '''import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy

VENUE = Venue("SIM")
class Refused(Exception): pass                     # input refused before the engine is built: exit 20
def inside(root, name):                             # 5.2.8: builds every path the sandbox opens
    p = (root / name).resolve()
    if p.parent != root:
        raise Refused(name)
    return p
def plain_mean(xs):                                 # 5.2.5, both ports: a left-to-right loop, never sum()
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)
def require_backtest_environment(env):              # 5.2.5 (C-2)
    if env is not Environment.BACKTEST:
        raise RuntimeError(f"kernel environment {env.name}, not BACKTEST")
def require_backtest_clock(clock):
    if not isinstance(clock, TestClock):
        raise RuntimeError("the strategy clock is not a TestClock")
def make_fee_model(cost_bps, stress):               # 5.2.3: a closure, so no __init__ and no super()
    if Decimal(stress) < 1:
        raise ValueError("stress below 1")
    rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)
    class BpFeeModel(FeeModel):
        def get_commission(self, order, fill_qty, fill_px, instrument):
            return Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate,
                         instrument.quote_currency)
    return BpFeeModel()
def build_engine():                                 # 5.2.3, rows Engine and Kernel check
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), run_analysis=False,
                                                 logging=LoggingConfig(log_level="ERROR", log_colors=False)))
    require_backtest_environment(engine.kernel.environment)
    return engine
class PortConfig(StrategyConfig, frozen=True):      # every parameter lives here, never in an __init__ (rule F3)
    instrument_id: str; bar_type: str; cost_bps: str; stress: str
    closes: list; ts: list                          # the close strings of bars.csv and their ts_ns
class TrendSwitchConfig(PortConfig, frozen=True):
    rule: str; lookback: int; step: int
class CryptoTrendConfig(PortConfig, frozen=True):
    hysteresis: float; lookbacks: list; mas: list
class Port(Strategy):                               # no __init__: Strategy's own stores the config
    def on_start(self):
        require_backtest_clock(self.clock)          # first statement (C-15)
        self.iid = InstrumentId.from_str(self.config.instrument_id)
        self.inst = self.cache.instrument(self.iid)
        self.px = [float(c) for c in self.config.closes]
        self.i, self.held, self.fills, self.decisions, self.equity, self.invalid_reasons = -1, 0, [], [], [], []
        self.denied = self.rejected = 0
        self.subscribe_bars(BarType.from_str(self.config.bar_type))
        self.strategy_started = True                # last statement (C-15)
    def on_bar(self, bar):                          # never raises: Nautilus re-raises, which ends the child
        self.i += 1
        if bar.ts_event != self.config.ts[self.i] or bar.close != Price.from_str(self.config.closes[self.i]):
            self.invalid_reasons.append(f"C-12: bar {self.i} differs from bars.csv")   # id first (QA-R3-8)
            return
        ...                                         # one onbar_equity row; decision, margin = self.decide(self.i)
        ...                                         # in-flight check (C-13); side and fee-inclusive Decimal q (5.2.5)
        self.place(self.order_factory.market(self.iid, side, Quantity(q, self.inst.size_precision),
                                             time_in_force=TimeInForce.GTC))
    def place(self, order):                         # the one exempt call (5.6 rule A)
        self.submit_order(order)
    def on_order_filled(self, ev):                  # one fills.csv row (5.2.6)
        ...
    def on_order_denied(self, ev): self.denied += 1
    def on_order_rejected(self, ev): self.rejected += 1
class TrendSwitchPort(Port):
    def decide(self, i):                            # -> (decision or None, margin), the table of 5.2.5
        ...
class CryptoTrendPort(Port):
    def decide(self, i):
        ...
def run(root):                                      # exit 0, 10 or 20 (5.2.1)
    inp = json.loads(inside(root, "input.json").read_text(encoding="utf-8"))
    ...                                             # every rule of 6.1, one by one (L2-5a): raise Refused
    engine = build_engine()
    engine.add_venue(..., fee_model=make_fee_model(inp["cost_bps"], inp["stress"]), allow_cash_borrowing=False)
    ...                                             # add_instrument; add_data (5.2.4); port.strategy_started = False;
    engine.run()                                    # add_strategy(TrendSwitchPort(TrendSwitchConfig(...))) or crypto
    ...                                             # 5.2.7 checks as "C-nn: ..." reasons; 5.2.6's files; dispose
    return 0 if valid else 10
def check_env():                                    # --check-env: one JSON line, no file (5.2.1)
    engine = build_engine()
    u = platform.uname()                            # not platform.system(): rule F6 flags any call named system
    print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                      "system": u.system, "machine": u.machine, "environment": engine.kernel.environment.name,
                      "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                                    "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX}}))
    engine.dispose()
    return 0
def guard_selftest():                               # --guard-selftest: exit 0, or 30 on a wrong outcome (5.2.1)
    out = {}
    env, clock = require_backtest_environment, require_backtest_clock
    for name, fn, arg in (("sandbox", env, Environment.SANDBOX), ("live", env, Environment.LIVE),
                          ("live_clock", clock, LiveClock()), ("backtest", env, Environment.BACKTEST),
                          ("test_clock", clock, TestClock())):
        try:
            fn(arg)
            out[name] = "passed"
        except RuntimeError:
            out[name] = "raised"
    print(json.dumps(out, sort_keys=True))
    return 0 if list(out.values()) == ["raised"] * 3 + ["passed"] * 2 else 30
def main():
    ap = argparse.ArgumentParser(prog="sandbox.py")
    ap.add_argument("--check-env", action="store_true"); ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv[1:])
    if a.check_env or a.guard_selftest:
        return check_env() if a.check_env else guard_selftest()
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute() or root != root.resolve():
        return 20
    try:
        return run(root)
    except Refused:
        return 20
if __name__ == "__main__":                          # SECURITY-R3-1: __name__ is a Name, not an Attribute (F3)
    exit(main())
'''


def _with(code: str) -> str:
    """The skeleton plus `code`, inserted before its `if __name__` guard (spec 8.5, "sandbox +")."""
    guard = '\nif __name__ == "__main__":'
    assert _SANDBOX_SKELETON.count(guard) == 1
    return _SANDBOX_SKELETON.replace(guard, "\n" + code + guard, 1)


def _tag(hit: str) -> str:
    """A hit's tag in spec 8.5: the rule of a `[nautilus:<rule>]` hit, TEXT for a FORBIDDEN_TEXT_CI hit, CALL for a
    FORBIDDEN_CALLS hit; any other hit is its own text, so a comparison that fails shows it."""
    rule = re.match(r"\[nautilus:(\w+)\] ", hit)
    if rule:
        return rule.group(1)
    if any(hit.endswith(f": {n!r}") for n in FORBIDDEN_TEXT_CI):
        return "TEXT"
    call = re.search(r":\d+: \.?(\w+)\(\)$", hit)
    return "CALL" if call and call.group(1) in FORBIDDEN_CALLS else hit


def _nautilus_controls() -> list[tuple[str, str, str, dict[str, int]]]:
    """(label, path, content, expected tags) for each of the 51 controls of spec 8.5."""
    sb = NAUTILUS_SANDBOX
    verbs = "def verbs(self):\n" + "".join(f"    self.{v}(1)\n" for v in sorted(NAUTILUS_ORDER_VERBS))
    probe = (ROOT / "tools" / "nautilus" / "egress_probe.py").read_text(encoding="utf-8")
    controls = [
        ("sandbox positive", sb, _SANDBOX_SKELETON, {}),
        ("runner positive", "tools/nautilus/runner.py",
         "def bad(name):\n    return name.startswith('nautilus_trader.adapters')\n", {}),
        ("egress probe", "tools/nautilus/egress_probe.py", probe, {}),
        ("key outside the bridge", "data/fmp/probe_key.py", "def f(api_key):\n    return api_key\n", {}),
        ("live leak", "tools/nautilus/live_leak.py",
         "from nautilus_trader.live.node import TradingNode\nimport nautilus_trader.adapters.binance\n"
         "from nautilus_trader.core import nautilus_pyo3\nnode = TradingNode(cfg)\nnode.run()\n",
         {"C1": 3, "C2": 3, "D": 1}),
        ("dynamic", "tools/nautilus/dynamic.py",
         "import importlib\nimportlib.import_module('nautilus_trader.adapters.betfair')\n", {"E": 1}),
        ("outside import", "core/quant/nt_runner.py", "from nautilus_trader.backtest.engine import BacktestEngine\n",
         {"C2": 1}),
        ("outside submit", "tools/nautilus/other_submit.py", "def f(s, o):\n    s.submit_order(o)\n",
         {"TEXT": 1, "CALL": 1}),
        ("Rust client name", "tools/nautilus/client.py",
         "def f(m):\n    return m.BybitHttpClient(api_key='x', api_secret='y')\n", {"D": 3}),
        ("verbs", sb, _with(verbs), {"A": 1, "CALL": 8, "TEXT": 1}),
        ("sandbox receiver", sb, _with("def other_call(other, o):\n    other.submit_order(o)\n"),
         {"A": 1, "CALL": 2, "TEXT": 1}),
        ("sandbox bare reference", sb, _with("def ref(self):\n    f = self.submit_order\n    return f\n"),
         {"A": 1, "CALL": 1, "TEXT": 1}),
        ("sandbox string", sb, _with("NAME = 'submit_order'\n"), {"A": 1, "CALL": 1, "TEXT": 1}),
        ("sandbox bare import", sb, _with("import nautilus_trader\n"), {"C3": 1}),
        ("sandbox denied name", sb, _with("from nautilus_trader.config import TradingNodeConfig\n"),
         {"C1": 1, "C3": 1}),
        ("sandbox relative", sb, _with("from . import runner\n"), {"C3": 1}),
        ("sandbox sys.modules", sb,
         _with("from sys import modules\nnet = modules['nautilus_trader.core.' + 'nautilus_pyo3']\n"),
         {"C3": 1, "E": 1, "F1": 1}),
        ("sandbox module chain", sb, _with("net = argparse._sys.modules['x']\n"), {"F4": 1}),
        ("sandbox __dict__", sb, _with("d = Port.__dict__\n"), {"F3": 1}),
        ("sandbox getattr", sb, _with("def g(self, o):\n    getattr(self, 'sub' + 'mit_order')(o)\n"), {"F2": 1}),
        ("sandbox open", sb, _with("def leak():\n    return open('/repo/.env').read()\n"), {"F2": 1}),
        ("sandbox path", sb, _with("def leak():\n    return Path('/repo/.env').read_text()\n"), {"F5": 1}),
        ("sandbox os call", sb, _with("def run_os():\n    platform.os.system('x')\n"), {"F6": 1}),
        ("sandbox platform.system()", sb, _with("x = platform.system()\n"), {"F6": 1}),
        ("sandbox importlib", sb, _with("import importlib.metadata\n"), {"C3": 1, "F1": 1}),
    ]
    controls += [(f"banned module {m}", sb, _with(f"import {m}\n"), {"C3": 1, "F1": 1})
                 for m in sorted(SANDBOX_BANNED_MODULES)]
    controls += [(f"banned name {n}", sb, _with(f"x = {n}\n"), {"F2": 1}) for n in sorted(SANDBOX_BANNED_NAMES)]
    return controls


def test_t_ro_01_nautilus_confined_to_the_sandbox():
    """Spec 2026-10-26 section 5.6, T-RO-01 amendment (owner ruling O2): "orders in a Nautilus backtest fill against a
    simulated exchange inside one process, as QUANTGEN's paper fills pass through `OrderBook.fill`
    (`core/engine/orders.py:90, 169, 253-257`). The amendment lets exactly one file place such orders, through exactly
    one call, and closes two holes of today's scan: it compares only the first dotted component of an import
    (`tests/macro_m0_harness.py:90-96`), and it misses seven Nautilus order verbs (map04 §3.2). It is the first
    exemption for a forbidden token or call in T-RO-01's history (GOVERNANCE-10) [...]. After it, a T-RO-01 PASS means
    'no order path outside the one sandbox call'."

    Every control of spec 8.5 gives exactly its multiset of tags in a temp tree, and the real sandbox exists and gives
    no hit (QA-12)."""
    from collections import Counter
    controls = _nautilus_controls()
    assert len(controls) == 51, len(controls)
    wrong = []
    with tempfile.TemporaryDirectory() as name:
        tmp = Path(name)
        for label, rel, text, want in controls:
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            got = dict(Counter(_tag(h) for h in _offences(path, tmp)))
            if got != want:
                wrong.append(f"{label}: {got} != {want}")
            path.unlink()
    assert not wrong, "scan controls off:\n  " + "\n  ".join(wrong)
    sandbox = ROOT / NAUTILUS_SANDBOX
    assert sandbox.is_file(), f"{NAUTILUS_SANDBOX} is missing"
    assert _offences(sandbox) == [], _offences(sandbox)


test_t_ro_01_nautilus_confined_to_the_sandbox.test_ids = ["T-RO-01"]


def _canon(x):
    """Spec 5.6: a dict maps to a dict of canonical values; a set, frozenset, tuple or list to the sorted list of its
    canonical items; any other value stays."""
    if isinstance(x, dict):
        return {k: _canon(v) for k, v in x.items()}
    if isinstance(x, (set, frozenset, tuple, list)):
        return sorted(_canon(v) for v in x)
    return x


def _pin(obj: dict) -> str:
    return hashlib.sha256(json.dumps(_canon(obj), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_t_ro_01_nautilus_allowlist_pinned():
    """Spec 2026-10-26 section 5.6, T-RO-01 amendment (owner ruling O2): "orders in a Nautilus backtest fill against a
    simulated exchange inside one process, as QUANTGEN's paper fills pass through `OrderBook.fill`
    (`core/engine/orders.py:90, 169, 253-257`). The amendment lets exactly one file place such orders, through exactly
    one call, and closes two holes of today's scan: it compares only the first dotted component of an import
    (`tests/macro_m0_harness.py:90-96`), and it misses seven Nautilus order verbs (map04 §3.2). It is the first
    exemption for a forbidden token or call in T-RO-01's history (GOVERNANCE-10) [...]. After it, a T-RO-01 PASS means
    'no order path outside the one sandbox call'."

    SECURITY-5: the allow-list and the rule lists are pinned by hash, so neither widens without an owner ruling; the
    seven order verbs are forbidden in every file, the sandbox included (rule B)."""
    allow = {"NAUTILUS_SANDBOX": NAUTILUS_SANDBOX, "NAUTILUS_ALLOWED_FROM": NAUTILUS_ALLOWED_FROM,
             "NAUTILUS_DENIED_PREFIXES": NAUTILUS_DENIED_PREFIXES, "NAUTILUS_DENIED_NAMES": NAUTILUS_DENIED_NAMES,
             "SANDBOX_STDLIB": SANDBOX_STDLIB}
    rules = {"NAUTILUS_BRIDGE_ONLY_NAMES": NAUTILUS_BRIDGE_ONLY_NAMES,
             "NAUTILUS_DENIED_NAME_RE": NAUTILUS_DENIED_NAME_RE.pattern, "NAUTILUS_ORDER_VERBS": NAUTILUS_ORDER_VERBS,
             "IMPORT_MACHINERY": IMPORT_MACHINERY, "SANDBOX_BANNED_MODULES": SANDBOX_BANNED_MODULES,
             "SANDBOX_BANNED_NAMES": SANDBOX_BANNED_NAMES, "SANDBOX_FILE_METHODS": SANDBOX_FILE_METHODS,
             "SANDBOX_OS_CALLS": SANDBOX_OS_CALLS}
    # a change needs an owner ruling recorded in spec 2026-10-26 §5.6
    assert _pin(allow) == "2792ad4af44c6af599092f81594a34d1f7d013cd17abf5882c8c6f72a042e49f", _pin(allow)
    # a change needs an owner ruling recorded in spec 2026-10-26 §5.6
    assert _pin(rules) == "70bcf50fbce5637a1854413618b6b9827c04dc10a59a0a25d274b4be1941da6c", _pin(rules)
    assert NAUTILUS_ORDER_VERBS <= FORBIDDEN_CALLS, sorted(NAUTILUS_ORDER_VERBS - FORBIDDEN_CALLS)


test_t_ro_01_nautilus_allowlist_pinned.test_ids = ["T-RO-01"]
```

- [ ] **Step 3: Run the harness module and see the new tests fail.** Then confirm that the embedded skeleton is verbatim.
````bash
cd /home/user/quantgen; python3 -B -m tests.macro_m0_harness; echo "exit=$?"
python3 -B - <<'EOF'
import hashlib
from pathlib import Path
import tests.macro_m0_harness as H
lines = Path("docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md").read_text(encoding="utf-8").split("\n")
i = lines.index("```python", lines.index("#### 5.2.9 Structure of `sandbox.py` (C-5)"))
j = lines.index("```", i + 1)
assert H._SANDBOX_SKELETON == "\n".join(lines[i + 1:j]) + "\n", "skeleton differs from spec 5.2.9"
print("skeleton verbatim", hashlib.md5(H._SANDBOX_SKELETON.encode("utf-8")).hexdigest())
EOF
````
  Expected for the first command: tracebacks, then exactly these three FAIL lines among the PASS lines, then `exit=1`. The two new tests fail with `NameError` because the constants do not exist yet. The registry test fails because both tests carry `test_ids = ["T-RO-01"]` and row 12 has not been resynced.
```
FAIL test_registry_implemented_in_matches_test_ids AssertionError: registry out of sync (python -m tests.macro_acceptance resyncs it): T-RO-01: 'tests/macro_m0_harness.py::test_t_ro_01_artifact_writers_stamp_read_only;...' != '...'
FAIL test_t_ro_01_nautilus_allowlist_pinned NameError: name 'NAUTILUS_SANDBOX' is not defined (0.0s)
FAIL test_t_ro_01_nautilus_confined_to_the_sandbox NameError: name 'NAUTILUS_SANDBOX' is not defined (0.0s)

11/14 passed, 3 failed, 0 not run
```
  In general the summary is `H-1/H+2 passed, 3 failed, 0 not run`. The second command prints `skeleton verbatim 484ad92fbf352616078f26be4ff41121`.

- [ ] **Step 4: Add the constants of spec 5.6 and rule B.** Use the Edit tool on `tests/macro_m0_harness.py`. The old text is the line `ALLOWED_BARE_CALLS = {"ui/trading_page.py": {"fill_order", "cancel_order"}}`. The new text is that line followed directly by the block below. The existing comment `# Only the engine package ...` still follows the block. The block, verbatim; its constants are spec 5.6's, character for character:
```python
# T-RO-01 amendment for the NautilusTrader bridge (spec 2026-10-26 section 5.6, owner ruling O2; outside the branch it
# takes effect only after the owner's sign-off sentence). The rules A to F live in `_nautilus_offences` below.
NAUTILUS_SANDBOX = "tools/nautilus/sandbox.py"   # the one file that may place simulated orders (spec 2026-10-26 §5.6)
NAUTILUS_ALLOWED_FROM = {                          # sandbox only: module -> the names it may import
    "nautilus_trader.backtest.engine": frozenset({"BacktestEngine"}),
    "nautilus_trader.backtest.models": frozenset({"FeeModel", "FillModel"}),
    "nautilus_trader.common": frozenset({"Environment"}),
    "nautilus_trader.common.component": frozenset({"LiveClock", "TestClock", "is_backtest_force_stop"}),
    "nautilus_trader.config": frozenset({"BacktestEngineConfig", "LoggingConfig", "StrategyConfig"}),
    "nautilus_trader.model.currencies": frozenset({"BTC", "USD"}),
    "nautilus_trader.model.data": frozenset({"Bar", "BarType"}),
    "nautilus_trader.model.enums": frozenset({"AccountType", "OmsType", "OrderSide", "TimeInForce"}),
    "nautilus_trader.model.identifiers": frozenset({"InstrumentId", "Symbol", "TraderId", "Venue"}),
    "nautilus_trader.model.instruments": frozenset({"CurrencyPair", "Equity"}),
    "nautilus_trader.model.objects": frozenset({"FIXED_PRECISION", "HIGH_PRECISION", "Money", "PRICE_MAX", "Price",
                                                "QUANTITY_MAX", "Quantity"}),
    "nautilus_trader.trading.strategy": frozenset({"Strategy"}),
}
NAUTILUS_DENIED_PREFIXES = ("nautilus_trader.live", "nautilus_trader.adapters", "nautilus_trader.network",
                            "nautilus_trader.core.nautilus_pyo3", "nautilus_trader.backtest.node", "nautilus_pyo3")
NAUTILUS_DENIED_NAMES = frozenset({
    "TradingNode", "TradingNodeBuilder", "TradingNodeConfig", "LiveNode", "LiveExecClientConfig",
    "LiveDataClientConfig", "SandboxExecutionClient", "get_env_key", "get_env_key_or", "HttpClient",
    "WebSocketClient", "SocketClient", "nautilus_pyo3", "api_key", "api_secret"})
NAUTILUS_BRIDGE_ONLY_NAMES = frozenset({"api_key", "api_secret"})   # denied under tools/nautilus/ only:
                                                                     # data/fmp/quote_client.py:110, 115 use api_key
NAUTILUS_DENIED_NAME_RE = re.compile(r"\w+(Http|WebSocket|Socket|Execution|Data)Client\b")
NAUTILUS_ORDER_VERBS = frozenset({"modify_order", "cancel_orders", "cancel_all_orders", "close_position",
                                  "close_all_positions", "market_exit", "submit_order_list"})
IMPORT_MACHINERY = frozenset({"import_module", "__import__", "find_spec", "spec_from_file_location",
                              "module_from_spec", "run_module", "run_path", "resolve_name", "get_loader",
                              "find_loader", "reload"})
SANDBOX_STDLIB = {"argparse": None, "csv": None, "hashlib": None, "json": None, "math": None, "platform": None,
                  "decimal": frozenset({"Decimal", "ROUND_FLOOR"}), "pathlib": frozenset({"Path"}),
                  "sys": frozenset({"argv", "exit"})}           # None: `import m`; a set: `from m import <names>`
SANDBOX_BANNED_MODULES = frozenset({"asyncio", "builtins", "ctypes", "gc", "http", "importlib", "inspect", "os",
                                    "socket", "ssl", "subprocess", "sys", "types", "urllib"})
SANDBOX_BANNED_NAMES = frozenset({"getattr", "setattr", "delattr", "vars", "globals", "locals", "eval", "exec",
                                  "compile", "__import__", "breakpoint", "open"})
SANDBOX_FILE_METHODS = frozenset({"open", "read_text", "read_bytes", "write_text", "write_bytes", "touch", "mkdir",
                                  "unlink", "rmdir", "rename", "replace", "symlink_to", "hardlink_to", "iterdir",
                                  "glob", "rglob", "chmod"})
SANDBOX_OS_CALLS = frozenset({"system", "popen", "startfile", "fork", "kill", "execl", "execv", "execve", "execvp",
                              "spawnl", "spawnlp", "spawnv", "spawnve", "posix_spawn", "posix_spawnp", "Popen",
                              "check_call", "check_output", "create_connection", "urlopen"})
FORBIDDEN_CALLS = FORBIDDEN_CALLS | NAUTILUS_ORDER_VERBS   # rule B: the 7 verbs are forbidden in every file, sandbox too
```

- [ ] **Step 5: Add rules A to F to `_offences`.** Use the Edit tool on `tests/macro_m0_harness.py`. Current text, which is unique (the end of `_offences`, :108-109):
```python
                    hits.append(f"{rel}:{node.lineno}: {func.id}()")
    return hits
```
  New text. It is followed by the existing two blank lines and `def _yaml_offences`:
```python
                    hits.append(f"{rel}:{node.lineno}: {func.id}()")
    return _nautilus_offences(tree, rel, hits)


# --------------------------------------------------------------------------- #
# T-RO-01 amendment: rules A to F for the NautilusTrader bridge (spec 2026-10-26 section 5.6)
# --------------------------------------------------------------------------- #
def _import_names(node: ast.Import | ast.ImportFrom, rel: str) -> list[str]:
    """Full dotted names (spec 2026-10-26 section 5.6): `import a.b.c` names a.b.c; `from m import n` names m and m.n;
    a relative import resolves against the file's package."""
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    module = node.module or ""
    if node.level:
        package = rel.split("/")[:-1]
        package = package[:max(len(package) - (node.level - 1), 0)]
        module = ".".join(package + ([module] if module else []))
    return [module] + [f"{module}.{a.name}" for a in node.names]


def _denied_module(name: str) -> bool:
    return any(name == p or name.startswith(p + ".") for p in NAUTILUS_DENIED_PREFIXES)


def _denied_name(name: str | None, bridge: bool) -> bool:
    """In NAUTILUS_DENIED_NAMES (NAUTILUS_BRIDGE_ONLY_NAMES only under tools/nautilus/), or matching the client pattern."""
    if not name:
        return False
    if name in NAUTILUS_BRIDGE_ONLY_NAMES:
        return bridge
    return name in NAUTILUS_DENIED_NAMES or NAUTILUS_DENIED_NAME_RE.search(name) is not None


def _identifiers(node: ast.AST) -> tuple[str | None, ...]:
    """What rule A reads on one node: a Name, Attribute, function or class name, arg, keyword, import alias or string."""
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (node.attr,)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return (node.name,)
    if isinstance(node, (ast.arg, ast.keyword)):
        return (node.arg,)
    if isinstance(node, ast.alias):
        return (node.name, node.asname)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    return ()


def _rule_a(tree: ast.AST, rel: str, hits: list[str]) -> list[str]:
    """Rule A (SECURITY-7), sandbox only. Exempt only when exactly one node names submit_order and it is
    `self.submit_order` called inside a method (a function directly in a class body): then its text hit and its call
    hit are dropped. Otherwise every hit stands, plus one A hit."""
    found = [n for n in ast.walk(tree) if any("submit_order" in (s or "").lower() for s in _identifiers(n))]
    if not found:
        return hits
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    node, call = found[0], parents.get(found[0])
    method = call
    while method is not None and not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
        method = parents.get(method)
    if (len(found) == 1 and isinstance(node, ast.Attribute) and node.attr == "submit_order"
            and isinstance(node.value, ast.Name) and node.value.id == "self"
            and isinstance(call, ast.Call) and call.func is node
            and method is not None and isinstance(parents.get(method), ast.ClassDef)):
        return [h for h in hits if h not in (f"{rel}: 'submit_order'", f"{rel}:{call.lineno}: .submit_order()")]
    return hits + [f"[nautilus:A] {rel}:{getattr(node, 'lineno', 0)}: {len(found)} node(s) name submit_order; only one "
                   "self.submit_order call in one method is exempt"]


def _import_rules(node: ast.Import | ast.ImportFrom, rel: str, sandbox: bool, bridge: bool) -> list[str]:
    """Rules C1, C2, C3 and F1 on one import statement."""
    where, names = f"{rel}:{node.lineno}", _import_names(node, rel)
    aliases = [n for a in node.names for n in (a.name, a.asname) if n]
    out = []
    if any(_denied_module(n) for n in names) or any(_denied_name(a, bridge) for a in aliases):
        out.append(f"[nautilus:C1] {where}: denied module or name in {names}")
    if not sandbox:
        if any(n == "nautilus_trader" or n.startswith("nautilus_trader.") for n in names):
            out.append(f"[nautilus:C2] {where}: nautilus_trader imported outside {NAUTILUS_SANDBOX}")
        return out
    if isinstance(node, ast.Import):
        allowed = all(a.name in SANDBOX_STDLIB and SANDBOX_STDLIB[a.name] is None and not a.asname for a in node.names)
        tops = {a.name.split(".")[0] for a in node.names}
    else:
        pool = NAUTILUS_ALLOWED_FROM.get(node.module) or SANDBOX_STDLIB.get(node.module) or frozenset()
        allowed = not node.level and all(a.name in pool and not a.asname for a in node.names)
        tops = set() if node.level else {(node.module or "").split(".")[0]}
    if not allowed:
        out.append(f"[nautilus:C3] {where}: sandbox import outside the allow-list: {names}")
    from_sys = (isinstance(node, ast.ImportFrom) and node.module == "sys"
                and all(a.name in SANDBOX_STDLIB["sys"] for a in node.names))
    if tops & SANDBOX_BANNED_MODULES and not from_sys:
        out.append(f"[nautilus:F1] {where}: banned module {sorted(tops & SANDBOX_BANNED_MODULES)}")
    return out


def _node_rules(node: ast.AST, rel: str, sandbox: bool, bridge: bool, modules: set[str]) -> list[str]:
    """Rules D, E and F2 to F6 on one AST node; `modules` are the names the file binds with `import m`."""
    where, out = f"{rel}:{getattr(node, 'lineno', 0)}", []
    ident = (node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute)
             else node.arg if isinstance(node, (ast.arg, ast.keyword)) else None)
    if _denied_name(ident, bridge):
        out.append(f"[nautilus:D] {where}: denied name {ident}")
    if isinstance(node, ast.Call):
        func = node.func
        callee = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if callee in IMPORT_MACHINERY and (sandbox or any("nautilus" in s for s in _strings_in(node))):
            out.append(f"[nautilus:E] {where}: import machinery {callee}()")
        if sandbox and isinstance(func, ast.Attribute) and func.attr in SANDBOX_FILE_METHODS and not (
                isinstance(func.value, ast.Call) and isinstance(func.value.func, ast.Name)
                and func.value.func.id == "inside"):
            out.append(f"[nautilus:F5] {where}: .{func.attr}() on a path that inside() did not build")
        if sandbox and callee in SANDBOX_OS_CALLS:
            out.append(f"[nautilus:F6] {where}: process or socket call {callee}()")
    if not sandbox:
        return out
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and any(
            entry in node.value for entry in (*NAUTILUS_DENIED_PREFIXES, *NAUTILUS_DENIED_NAMES)):
        out.append(f"[nautilus:E] {where}: denied module or name in a string")
    if isinstance(node, ast.Name) and node.id in SANDBOX_BANNED_NAMES:
        out.append(f"[nautilus:F2] {where}: {node.id}")
    if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
        out.append(f"[nautilus:F3] {where}: .{node.attr}")
    if isinstance(node, ast.Subscript):
        value = node.value
        while isinstance(value, ast.Attribute):
            value = value.value
        if isinstance(value, ast.Name) and value.id in modules:
            out.append(f"[nautilus:F4] {where}: subscript on the module {value.id}")
    return out


def _nautilus_offences(tree: ast.AST, rel: str, hits: list[str]) -> list[str]:
    """Rules A to F of spec 2026-10-26 section 5.6 on one parsed file. `hits` are the file's existing T-RO-01 hits,
    which keep their form (rule A may drop its two exempt ones); every new hit starts with `[nautilus:<rule>]`, and
    each rule adds at most one hit per AST node it inspects."""
    sandbox, bridge = rel == NAUTILUS_SANDBOX, rel.startswith("tools/nautilus/")
    if sandbox:
        hits = _rule_a(tree, rel, hits)
    modules = {a.asname or a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    out = list(hits)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out += _import_rules(node, rel, sandbox, bridge)
        out += _node_rules(node, rel, sandbox, bridge, modules)
    return out
```
  How the rules map to spec 5.6:
  - **Import names.** These are full dotted names, so `nautilus_trader.adapters.x` is judged in full and not by its first component.
  - **C3** also refuses `import m as x`, because "any `as` alias" is one of its offences.
  - **E outside the sandbox** fires on a string containing `nautilus`, which covers every denied prefix.
  - **The sandbox's own strings** are checked against every denied prefix and name.

- [ ] **Step 6: Run the harness module. Both new tests pass, and only the registry test fails.**
```bash
cd /home/user/quantgen; python3 -B -m tests.macro_m0_harness; echo "exit=$?"
```
  Expected:
  - `PASS test_t_ro_01_nautilus_allowlist_pinned`.
  - `PASS test_t_ro_01_nautilus_confined_to_the_sandbox`, about 1 s.
  - `PASS test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path`: the real tree under the amended rules.
  - One FAIL line, the `test_registry_implemented_in_matches_test_ids` line of Step 3.
  - `13/14 passed, 1 failed, 0 not run` (in general `H+1/H+2`), then `exit=1`.

- [ ] **Step 7: Resync registry row 12 (spec 5.8).**
```bash
cd /home/user/quantgen; python3 -B -m tests.macro_acceptance
git diff --stat tests/macro_registry.csv
python3 -c "import csv; r = {x['test_id']: x for x in csv.DictReader(open('tests/macro_registry.csv', encoding='utf-8', newline=''))}; print('\n'.join(r['T-RO-01']['implemented_in'].split(';')))"
python3 -c "b = open('tests/macro_registry.csv', 'rb').read(); assert b'\r' not in b; print('LF ok')"
python3 -B -m tests.macro_m0_harness | tail -1
```
  Expected:
  - `implemented_in rows changed: 1`.
  - ` 1 file changed, 1 insertion(+), 1 deletion(-)`.
  - These seven lines:
```
tests/macro_m0_harness.py::test_t_ro_01_artifact_writers_stamp_read_only
tests/macro_m0_harness.py::test_t_ro_01_nautilus_allowlist_pinned
tests/macro_m0_harness.py::test_t_ro_01_nautilus_confined_to_the_sandbox
tests/macro_m0_harness.py::test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path
tests/macro_m0_harness.py::test_t_ro_01_orders_module_reached_only_through_the_engine
tests/macro_m5_integration.py::test_s4_rulings_no_wall_clock_nothing_above_one_halted_outside_min_engine_untouched
tests/macro_m8_pipeline.py::test_yaml_loads_with_the_strict_runner_and_the_legacy_parser_is_untouched
```
  - `LF ok`.
  - `14/14 passed, 0 failed, 0 not run` (in general `H+2/H+2`).

  If the command reports any other number of changed rows, run `git checkout tests/macro_registry.csv`, then stop and report. Step 1 showed the registry in sync, so only row 12 may change, and no other row is ever committed by this task.

- [ ] **Step 8: Check T-RO-01, test_08, test_09 and the flet guard.**
```bash
cd /home/user/quantgen
python3 -B -c "import tests.macro_m0_harness as H; files = H._scan_files(); print(len([h for p in files for h in H._offences(p)]), 'hits;', sorted(p.relative_to(H.ROOT).as_posix() for p in files if 'tools/nautilus/' in p.as_posix()), H._offences(H.ROOT / H.NAUTILUS_SANDBOX))"
git diff --exit-code --stat tests/acceptance.py tests/flet_api_guard.py && echo "test_08, test_09 and the flet guard unchanged"
python3 -B -c "from tests import acceptance as A; A.test_08_no_broker_order_path(); A.test_09_no_account_credentials_requested(); print('test_08 test_09 ok')"
python3 -B -c "from tests.flet_api_guard import tests; [f() for _, f in tests()]; print('flet guard ok', len(tests()))"
```
  Expected:
  - `0 hits; ['tools/nautilus/__init__.py', 'tools/nautilus/egress_probe.py', 'tools/nautilus/launch.py', 'tools/nautilus/sandbox.py'] []`.
  - `test_08, test_09 and the flet guard unchanged`.
  - `test_08 test_09 ok`.
  - `flet guard ok 4`.

  A hit in a Task 1 file breaks C2 or C3 (CONTRACT ISSUE 5). Correct it in that file, not in the rules, and name the file in Step 16.

- [ ] **Step 9: Write the failing L1-15 test.** In `tests/nautilus_acceptance.py`, Task 1's LF file, use the Edit tool to insert the function below directly before the line that starts `def tests(` (C8's collector), with two blank lines on each side. Notes:
  - CONTRACT ISSUE 3: spec 8.3 #15's "no CSV the parent or fixtures write" covers writers that do not exist until Tasks 3 and 4. The test checks the committed bridge CSVs now, and every `launch.fixture_inputs(name)` for `name` in `launch.FIXTURES` once Task 3 adds them. The `lineterminator` rule covers every later CSV writer statically.
  - CONTRACT ISSUE 4: C1's `newline="\n"` is enforced, and `newline=""` is accepted. That is the csv module's documented form, which the filled sandbox uses, and it writes the same bytes.
```python
def test_l1_15_encoding_rules_hold():
    """L1-15 (spec 8.3 and 3.7; QA-R2-14): in tools/nautilus/*.py and tests/nautilus_*.py every open (a constant
    binary mode exempt), read_text and write_text passes encoding="utf-8" (or "utf-8-sig"), every text write newline=,
    every text-mode subprocess call encoding="utf-8" and errors="replace", every csv writer lineterminator="\\n"; no
    committed bridge CSV, and no file launch.fixture_inputs builds (plan Task 3), holds a carriage return."""
    planted = {'open(p, "w")': 2, "p.read_text()": 1, 'p.write_text(s, encoding="utf-8")': 1,
               "subprocess.run(a, text=True)": 1, "csv.writer(fh)": 1, 'open(p, "rb")': 0,
               'p.read_text(encoding="utf-8-sig")': 0, 'p.write_text(s, encoding="utf-8", newline="\\n")': 0,
               'subprocess.run(a, text=True, encoding="utf-8", errors="replace")': 0,
               "subprocess.run(a, capture_output=True)": 0, 'csv.writer(fh, lineterminator="\\n")': 0,
               'inside(root, "fills.csv").open("w", encoding="utf-8", newline="")': 0}
    for snippet, want in planted.items():
        got = encoding_offences(snippet, "planted.py")
        assert len(got) == want, (snippet, got)
    files = sorted((ROOT / "tools" / "nautilus").glob("*.py")) + sorted((ROOT / "tests").glob("nautilus_*.py"))
    assert ROOT / "tools" / "nautilus" / "launch.py" in files and Path(__file__).resolve() in files, files
    hits = [h for p in files for h in encoding_offences(p.read_text(encoding="utf-8"), p.relative_to(ROOT).as_posix())]
    assert not hits, "encoding rules of spec 3.7 broken:\n  " + "\n  ".join(hits)
    csvs = sorted((ROOT / "tests" / "fixtures" / "nautilus").glob("*.csv")) + sorted((ROOT / "tools" / "nautilus").rglob("*.csv"))
    assert csvs, "no committed bridge CSV"
    bad = [p.relative_to(ROOT).as_posix() for p in csvs if b"\r" in p.read_bytes()]
    from tools.nautilus import launch
    build = getattr(launch, "fixture_inputs", None)
    bad += [f"fixture_inputs({n!r})" for n in getattr(launch, "FIXTURES", ()) if build and b"\r" in b"".join(build(n))]
    assert not bad, f"carriage returns in {bad}"
```
  Run it:
```bash
cd /home/user/quantgen; env -u QUANTGEN_NAUTILUS_PYTHON python3 -B -m tests.nautilus_acceptance -k test_l1_15; echo "exit=$?"
```
  Expected (CONTRACT ISSUE 8: the FAIL detail is `<exception type>: <message>`):
```
FAIL test_l1_15_encoding_rules_hold NameError: name 'encoding_offences' is not defined
0/1 passed, 1 failed, 0 not run
exit=1
```

- [ ] **Step 10: Add `encoding_offences`.** Use the Edit tool to insert the function below directly before the line that starts `def tests(`, with two blank lines on each side. It therefore follows the test of Step 9.
```python
def encoding_offences(source: str, rel: str) -> list[str]:
    """The AST rules of L1-15 (spec 3.7) over one file's source: "<rel>:<line>: <call>() <problem>" per broken call.
    A mode is the `mode=` keyword or the first positional string that looks like one; `open` and `fdopen` default to
    "r", `read_text` reads, `write_text` writes. A subprocess call is in text mode when it passes `text=True`,
    `universal_newlines=True`, `encoding=` or `errors=`."""
    import ast
    import re
    out = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        kw = {k.arg: (k.value.value if isinstance(k.value, ast.Constant) else k.value) for k in node.keywords if k.arg}
        where = f"{rel}:{node.lineno}: {name}()"
        if name in ("open", "fdopen", "read_text", "write_text"):
            modes = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)
                     and re.fullmatch(r"[rwxab+t]{1,3}", a.value)]
            mode = {"read_text": "r", "write_text": "w"}.get(name, kw.get("mode", modes[0] if modes else "r"))
            if isinstance(mode, str) and "b" in mode:
                continue
            if kw.get("encoding") not in ("utf-8", "utf-8-sig"):
                out.append(f'{where} without encoding="utf-8"')
            if (not isinstance(mode, str) or set(mode) & set("wxa+")) and kw.get("newline") not in ("\n", ""):
                out.append(f'{where} writes text without newline="\\n"')
        elif name in ("run", "Popen", "check_output", "check_call", "call") and (
                kw.get("text") is True or kw.get("universal_newlines") is True or "encoding" in kw or "errors" in kw):
            if kw.get("encoding") != "utf-8" or kw.get("errors") != "replace":
                out.append(f'{where} in text mode without encoding="utf-8", errors="replace"')
        elif name in ("writer", "DictWriter") and kw.get("lineterminator") != "\n":
            out.append(f'{where} without lineterminator="\\n"')
    return out
```
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
env -u QUANTGEN_NAUTILUS_PYTHON python3 -B -m tests.nautilus_acceptance -k test_l1_15; echo "exit=$?"
env -u QUANTGEN_NAUTILUS_PYTHON python3 -B -m tests.nautilus_acceptance | tail -1
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance | tail -1
python3 -c "b = open('tests/nautilus_acceptance.py', 'rb').read(); assert b'\r' not in b; print('LF ok')"
```
  Expected: `PASS test_l1_15_encoding_rules_hold`, `1/1 passed, 0 failed, 0 not run`, `exit=0`; then `9/13 passed, 0 failed, 4 not run`; then `13/13 passed, 0 failed, 0 not run`; then `LF ok`.

  If the real-file part fails, its message lists `<file>:<line>: <call>() <problem>`. Each line is a C1 breach in a Task 1 file. For each one:
  - add only the missing keyword (`encoding="utf-8"`, `newline="\n"`, `errors="replace"` or `lineterminator="\n"`) with the Edit tool;
  - run both commands again;
  - stage that file in Step 16 and name it in the commit message.

- [ ] **Step 11: Show that the `nautilus` suite is absent from the house runner (RED for 5.7).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; cd /home/user/quantgen; md5sum qa/acceptance_results.json
env -u QUANTGEN_NAUTILUS_PYTHON python3 -B $S/run_baseline.py $S/nb_task2_red.json --suite nautilus; echo "exit=$?"
md5sum qa/acceptance_results.json
```
  Expected: an empty line, then `0/0 passed, 0 failed, 0 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/nb_task2_red.json`, then `exit=1`. Both md5 lines print `16c9baa5a1777853521d485d5078e456`.

- [ ] **Step 12: Register the suite in `tests/run_all.py` (spec 5.7).** The file is CRLF. Use the Edit tool only, which keeps the line ends, and never a tool that rewrites newlines. Make three edits. The current text quoted below is as at `fa28059`. If an audit patch has since added a suite (`cache` or `bonds`), make the same change to the lines as they stand. The rule is: `nautilus_tests()` directly before `def tests():`, the `nautilus/` term last in `tests()`, and the help ending `papers or nautilus")`.

  Edit 1. Current text (end of `papers_tests`, :70-74):
```python
        return [("import", import_failed)]
    return selfcheck_tests()


def tests():
```
  New text:
```python
        return [("import", import_failed)]
    return selfcheck_tests()


def nautilus_tests():
    """Suite `nautilus` (tests/nautilus_acceptance.py; spec 2026-10-26 section 5.7), imported here: an import failure
    is one FAIL row named `import` and never stops the other suites."""
    try:
        from tests.nautilus_acceptance import tests as bridge_tests
    except Exception as exc:
        reason = f"tests.nautilus_acceptance does not import ({type(exc).__name__}: {exc})"

        def import_failed():
            raise RuntimeError(reason)
        return [("import", import_failed)]
    return bridge_tests()


def tests():
```
  Edit 2. Current text (:85):
```python
            [(f"papers/{n}", f) for n, f in papers_tests()])
```
  New text:
```python
            [(f"papers/{n}", f) for n, f in papers_tests()] +
            [(f"nautilus/{n}", f) for n, f in nautilus_tests()])
```
  Edit 3. The current text is ` or papers")`, unique, at the end of the `--suite` help (:131). The new text is `, papers or nautilus")`.

- [ ] **Step 13: Verify the registration.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -c "b = open('tests/run_all.py', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'tests/run_all.py must stay CRLF'; print('CRLF ok')"
git diff --stat tests/run_all.py; grep -c 'papers or nautilus' tests/run_all.py
python3 -B -c "import sys; sys.modules['tests.nautilus_acceptance'] = None; import tests.run_all as R; R.run(R.nautilus_tests())" 2>&1 | tail -1
md5sum qa/acceptance_results.json
env -u QUANTGEN_NAUTILUS_PYTHON python3 -B $S/run_baseline.py $S/nb_task2_nautilus.json --suite nautilus; echo "exit=$?"
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B $S/run_baseline.py $S/nb_task2_nautilus_key.json --suite nautilus | tail -1
md5sum qa/acceptance_results.json
```
  Expected:
  - `CRLF ok`.
  - ` 1 file changed, 17 insertions(+), 2 deletions(-)`, then `1`.
  - The import-failure path prints `FAIL import RuntimeError: tests.nautilus_acceptance does not import (ModuleNotFoundError: import of tests.nautilus_acceptance halted; None in sys.modules)`.
  - Both md5 lines print `16c9baa5a1777853521d485d5078e456`.
  - The key-unset run prints exactly these lines, then `exit=0`. This satisfies spec Step 4's done-when: the layer-2 tests report NOT_RUN, not PASS.
```
PASS nautilus/test_l1_15_encoding_rules_hold
PASS nautilus/test_l1_16_launch_builder_matches_the_contract
PASS nautilus/test_l1_17_venv_reads_and_wheel_identity
PASS nautilus/test_l1_22_global_interpreter_has_no_nautilus
NOT_RUN nautilus/test_l2_01_check_env_pins_identity_precision OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN nautilus/test_l2_08_guard_selftest_outcomes OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN nautilus/test_l2_09_egress_probe_blocked OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN nautilus/test_l2_10_timeout_kills_the_child_tree OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
PASS nautilus/test_px_census_parser_reads_importtime_lines
PASS nautilus/test_px_egress_probe_imports_json_and_socket_only
PASS nautilus/test_px_env_example_and_env_pins
PASS nautilus/test_px_requirements_nautilus_pins_and_header
PASS nautilus/test_l1_32_every_test_guarded_and_ledgers_unchanged

9/13 passed, 0 failed, 4 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/nb_task2_nautilus.json
```
  - The key-set run prints `13/13 passed, 0 failed, 0 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/nb_task2_nautilus_key.json`.

- [ ] **Step 14: Update `README.md` (spec 5.8, C-4).** The file is CRLF; use the Edit tool only.
  - **Edit 1:** the current text is ` or papers`, unique, at the end of the `--suite` comment (:853). The new text is `, papers or nautilus`.
  - **Edit 2:** the current text is the start of the Total row, `| **Total** | `tests/run_all.py` | |`, which is unique and directly follows the `papers` row (:877-878). The new text is the two lines below, so the new row sits after the `papers` row. If a `bonds` or `cache` row now sits between `papers` and Total, insert the new line directly after the `papers` row instead.

  The table writes every suite path in backticks, so the row does too; spec 5.8 quotes it inside a code span.
```text
| nautilus | `tests/nautilus_acceptance.py` | The NautilusTrader bridge (spec 2026-10-26), research only, on synthetic data: layer 1 runs in this interpreter, where `nautilus_trader` must not be installed; layer 2 runs the sandbox through the hash-pinned venv that `QUANTGEN_NAUTILUS_PYTHON` names, NOT_RUN while that key is blank and FAIL when the venv is off its pins; every test runs inside a guard that keeps the ledgers and `docs/nautilus_bridge/` byte-identical | counted at the Windows run of record |
| **Total** | `tests/run_all.py` | |
```
```bash
cd /home/user/quantgen
python3 -c "b = open('README.md', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'README.md must stay CRLF'; print('CRLF ok')"
git diff --stat README.md; git diff -U0 README.md | grep -c 'Total'
grep -n '^| papers \|^| nautilus \|^| \*\*Total' README.md | cut -c1-40
python3 -B -m tests.macro_ui_components | tail -1
```
  Expected:
  - `CRLF ok`.
  - ` 1 file changed, 2 insertions(+), 1 deletion(-)`, then `0`: the Total row is unchanged.
  - Three consecutive line numbers: `877:| papers ...`, `878:| nautilus ...` and `879:| **Total** ...` at `fa28059`.
  - `11/11 passed, 0 failed, 0 not run`, the same as before the edit.

- [ ] **Step 15: Run the full suite. Expect baseline plus Task 2's delta.** (CONTRACT ISSUE 7.) The full run takes about 10 minutes. Start it in the background and wait. Nothing else from QUANTGEN may run meanwhile (T-HERM-02; spec 3.8).
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; cd /home/user/quantgen; md5sum qa/acceptance_results.json
env -u QUANTGEN_NAUTILUS_PYTHON python3 -B $S/run_baseline.py $S/nb_task2_full.json > $S/nb_task2_full.log 2>&1   # in the background
```
  When it ends:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; cd /home/user/quantgen
tail -1 $S/nb_task2_full.log; md5sum qa/acceptance_results.json
python3 -c "import json, sys; S = sys.argv[1]; old = {r['test']: r['status'] for r in json.load(open(S + '/t1_baseline.json', encoding='utf-8'))}; new = {r['test']: r['status'] for r in json.load(open(S + '/nb_task2_full.json', encoding='utf-8'))}; print('added', sorted((k, new[k]) for k in set(new) - set(old))); print('removed', sorted(set(old) - set(new))); print('changed', sorted((k, old[k], new[k]) for k in old.keys() & new.keys() if old[k] != new[k])); print(sum(k.startswith('macro/') for k in new), 'macro rows')" "$S"
```
  Expected:
  - **Summary line.** It is B plus this task's delta: 15 more rows, 11 more PASS, the same FAIL count, 4 more NOT_RUN. With B = `P/N passed, F failed, R not run` from Step 1, it reads `P+11/N+15 passed, F failed, R+4 not run; .../nb_task2_full.json`. Reference example, from the 2026-10-26 baseline: `756/885 passed, 1 failed, 128 not run`. The only FAIL is B's environment-only `papers/test_debate_run_kills_process_tree`.
  - **md5.** `16c9baa5a1777853521d485d5078e456`.
  - **Comparison.** `removed []`, `changed []`, macro rows equal to B's plus 2 (reference 544), and `added` exactly:
```
added [('macro/macro_m0_harness/test_t_ro_01_nautilus_allowlist_pinned', 'PASS'), ('macro/macro_m0_harness/test_t_ro_01_nautilus_confined_to_the_sandbox', 'PASS'), ('nautilus/test_l1_15_encoding_rules_hold', 'PASS'), ('nautilus/test_l1_16_launch_builder_matches_the_contract', 'PASS'), ('nautilus/test_l1_17_venv_reads_and_wheel_identity', 'PASS'), ('nautilus/test_l1_22_global_interpreter_has_no_nautilus', 'PASS'), ('nautilus/test_l1_32_every_test_guarded_and_ledgers_unchanged', 'PASS'), ('nautilus/test_l2_01_check_env_pins_identity_precision', 'NOT_RUN'), ('nautilus/test_l2_08_guard_selftest_outcomes', 'NOT_RUN'), ('nautilus/test_l2_09_egress_probe_blocked', 'NOT_RUN'), ('nautilus/test_l2_10_timeout_kills_the_child_tree', 'NOT_RUN'), ('nautilus/test_px_census_parser_reads_importtime_lines', 'PASS'), ('nautilus/test_px_egress_probe_imports_json_and_socket_only', 'PASS'), ('nautilus/test_px_env_example_and_env_pins', 'PASS'), ('nautilus/test_px_requirements_nautilus_pins_and_header', 'PASS')]
```

  Any other difference stops the task before the commit.

- [ ] **Step 16: Commit.** (CONTRACT ISSUE 6: no path is exempt any more by default; the spec and this plan are committed.)
```bash
cd /home/user/quantgen; git status --short; md5sum qa/acceptance_results.json
```
  Expected: exactly the lines below, plus any path Step 1 recorded and any Task 1 file Step 8 or Step 10 corrected. `qa/acceptance_results.json` is not listed, and its md5 is `16c9baa5a1777853521d485d5078e456`.
```
 M README.md
 M tests/macro_m0_harness.py
 M tests/macro_registry.csv
 M tests/nautilus_acceptance.py
 M tests/run_all.py
```
```bash
cd /home/user/quantgen
git add README.md tests/macro_m0_harness.py tests/macro_registry.csv tests/nautilus_acceptance.py tests/run_all.py
git commit -F - <<'EOF'
Nautilus bridge, plan Task 2 (spec Step 4): T-RO-01 amendment and the nautilus suite

tests/macro_m0_harness.py: the constants of spec 2026-10-26 section 5.6, the
seven Nautilus order verbs in FORBIDDEN_CALLS (rule B), rules A to F in
_offences, and two T-RO-01 tests: the 51 scan controls of section 8.5 with the
real sandbox, and the hash pins of the allow-list and the rule lists. Registry
row T-RO-01 resynced by python -m tests.macro_acceptance.
tests/nautilus_acceptance.py: L1-15, the encoding rules of section 3.7.
tests/run_all.py: suite nautilus, last; an import failure is one FAIL row.
README.md: nautilus in the --suite help and its suite row; Total unchanged.
The exemption takes effect outside this branch only after the owner's
sign-off sentence (spec Step 7A.1). qa/acceptance_results.json unchanged.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
EOF
git show --numstat --format='%h %s' HEAD; git status --short
```
  If Step 8 or Step 10 corrected a Task 1 file, add that path to `git add` and name it in the message before the trailer lines.

  Expected numstat, assuming two blank lines around each block inserted into `tests/nautilus_acceptance.py`:
```
2	1	README.md
487	1	tests/macro_m0_harness.py
1	1	tests/macro_registry.csv
61	0	tests/nautilus_acceptance.py
17	2	tests/run_all.py
```
  Afterwards `git status --short` prints nothing, apart from the paths Step 1 recorded. No push.

---

### Task 3: Sandbox (spec Step 5): section 5.2 in full, `fixture_inputs`

**Verified before writing (2026-10-28, a scratch clone of HEAD `fa28059` holding this plan's Task 1 and Task 2 drafts, `$S/plan_step2/task3/clone`; nothing in the real clone touched; HEAD has since moved to `049306c`, which changes only `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` and a chart):**
- Every expected output below comes from a full dry run of these steps in that clone: Steps 1 to 9 as written, and Step 10's `--suite nautilus` runs through a copy of the wrapper pointed at the clone. Step 10's full run was not repeated there. Its counts are Task 1 Step 0's baseline plus the Count Ledger delta.
- **What this task builds on from Task 1** (beyond C2 and C8): `tools/nautilus/sandbox.py` holds 5.2.9's import block verbatim and its functions, with `run` a stub that raises `Refused` (exit 20). `tools/nautilus/launch.py` imports `hashlib` and `json` at module level and ends with `cleanup_tempdir`. `tests/nautilus_acceptance.py` has the banner `# CLI` directly above `def main(`, and imports `ast`, `hashlib`, `json`, `os`, `Path`, `Callable`, `NotRun` and `launch` at module level. Step 1 checks these names. No Task 1 private helper (`_launch_venv`, `_refused`, `_fake_venv`) is used.
- **What it builds on from Task 2**: `tests/macro_m0_harness.py::_offences` applies rules A to F of spec 5.6. `test_t_ro_01_nautilus_confined_to_the_sandbox` asserts that the real `tools/nautilus/sandbox.py` exists and gives no hit, so it must still pass once this task adds the one order call. `test_l1_15_encoding_rules_hold` scans `tools/nautilus/*.py` and `tests/nautilus_*.py` for spec 3.7's rules. It reads `launch.FIXTURES` with `getattr`, so it passes before this task and, after Step 4, also checks the fixture bytes for `\r`.
- **Spec 5.2.9 governs structure, not every line** (spec :520-529). The sandbox below keeps 5.2.9's import block verbatim and its definitions in order (`Refused` to `main`, spec :554-672), with every line 5.2.9 shows. It fills each `...` from 5.2.3 to 5.2.8. It departs from the skeleton only in the three places below, each for the reason given; a comment and the spelling `return 0 if not reasons else 10` are not counted:
  - `main` (spec :666-669) returns 20 silently on a refusal. But section 7 C-05 says "stderr only; 20" (spec :1242), and rule F1 allows only `from sys import argv, exit`, so the sandbox cannot reach `sys.stderr`. `argparse.ArgumentParser.exit(20, message)` writes the message to stderr and exits 20, and the sandbox already imports `argparse`. **CONTRACT ISSUE 1.**
  - `run` reads `input.json` with `read_text` (spec :625). But an `input.json` that is not JSON must exit 20 (8.4 test 5a, spec :1420; 5.4.3, spec :878), and the manifest needs the SHA-256 of the bytes (6.2). So `run` reads the bytes and turns a `ValueError` into `Refused`.
  - `run` sets the port's six state attributes (and `denied`, `rejected`) before `add_strategy`, in addition to 5.2.9's `strategy_started = False`. `on_start` sets them again. Without this, an `on_start` that raised (C-15) would make the 5.2.7 checks fail on `port.i` and crash (exit 1, C-06), instead of writing a manifest with `C-15` (exit 10).
- **Rule F holds** (spec :949-961, :979-984):
  - The sandbox calls `SANDBOX_FILE_METHODS` methods only on `inside(...)`. That list includes `replace` and `open`, so the code never calls `str.replace`.
  - It names no `SANDBOX_BANNED_NAMES` entry, no dunder attribute and no `SANDBOX_OS_CALLS` callee.
  - No string constant holds a denied prefix or name (rule E), and exactly one node names the order call (rule A).
  - Measured: `_offences(launch.SANDBOX) == []`, and with the sandbox in place `python3 -B -m tests.macro_m0_harness` gives `14/14 passed, 0 failed, 0 not run`.
- **The empty-ledger hash** is `gate_ledger.ledger_hash([])`, which is the md5 of `canonical_json([])`, that is of `"[]"`: `d751713988987e9331980363e24189ce` (`core/quant/gate_ledger.py:371-372`). The Revision-4 probe passed the md5 of `b""` (`d41d8cd98f00b204e9800998ecf8427e`) under that name (`scratch:rev4_probe/drive.py:10`). This plan calls the function, as 6.1 and C2 say.
- **Measured in the Linux venv under `unshare -rn`**, with the sandbox of Step 6 and the inputs of Step 4. All three fixtures match 8.2 (spec :1292-1342):
  - **F1** exits 0. Fills: BUY 10000 @ `100.000000000`, fee 5000.00, at bar 3; SELL 10000 @ `96.000000000`, fee 4800.00, at bar 5; BUY 9600 @ `99.000000000`, fee 4752.00, at bar 7; SELL 9600 @ `97.000000000`, fee 4656.00, at bar 11. Balance `926593.00`. Decisions: 3 buy, 5 sell, 7 buy, 9 hold, 11 sell.
  - **F2** exits 0. Fills: BUY `1.00000000` @ 53000, fee 53.00 (bar 3); SELL `1.00000000` @ 50000, fee 50.00 (bar 5); BUY `0.98812079` @ 50500, fee 49.90 (bar 7); SELL `0.98812079` @ 51000, fee 50.39 (bar 9). Balance `50343.77`. Decisions: 3 buy, 4 hold, 5 sell, 6 hold, 7 buy, 8 hold, 9 sell, 10 hold.
  - **N1** exits 10. One fill: BUY 1000 @ `100.00`, fee 500.00. 4 bars seen, force stop, balance `904501.00`, quantity `1000`. Reasons `C-01: forced stop` and `C-02: bars seen fewer than bars fed`. Its stderr holds the engine's `Stopping backtest from AccountBalanceNegative(balance=-89.45, currency=USD)` line (map03 §2.11).
  - **Determinism**: two processes on the same input give byte-identical output files, stdout and stderr, and the same 942-name census. Trade ids are deterministic (`T-474e28fcce475f55-005`, `SIM-1-001`). One run takes 1.1 to 2.1 s.
- **L2-5a builds 77 perturbations.** Spec 8.4 test 5a counted 63. This list adds:
  - the lower bounds that 6.1 implies;
  - two hash-format cases;
  - `stress "0"` and `fill_seed` as a float;
  - a repeated timestamp and a missing final newline;
  - `lookbacks` item 5001;
  - a `bars.csv` that is not UTF-8.

  Each case was measured to be refused by its own rule, and the stderr line names that rule, so the test asserts the rule and not only the exit code. L2-5a starts 80 children and takes about 90 s on Linux. L2-4 takes about 8 s, L2-5b about 10 s, and the whole module with the key set about 1 min 50 s.
- **`test_px_sandbox_avoids_excluded_constructs` was mutation-checked.** Each of these eleven planted defects makes it FAIL: `allow_cash_borrowing=True`, `AT_THE_CLOSE`, a `latency_model` argument, `run_analysis=True`, `prob_slippage=0.5`, `AccountType.MARGIN`, a limit order, a second order call, an account report, the clock guard moved out of first place, and an `__init__` with `super()`.
- **Guards outside the bridge are unaffected.** `test_08` and `test_09` scan `runtime_py()`: `core/`, `data/`, `ui/`, `main.py` and `config.py` (`tests/acceptance.py:50-56, 62-75`), so `tools/` is outside them. `tests/flet_api_guard.py:40` reads `ui/*.py` only. Step 9 runs `test_08` and `test_09` anyway.
- **`docs/nautilus_bridge/` holds 7 tracked files at HEAD**, which the 3.3 guard digests. No test of this task writes there. L2-5b links to `ROOT / ".env"`, which the clone lacks and the sandbox never opens: `inside` refuses the link before any read.
- **QUANTGEN's rules** are at `core/quant/strategies.py:162-187` (`trend_switch`: decision bars `i >= L` and `(i - L) % s == 0`) and `:330-348` (`crypto_trend`: the state stays unchanged while the composite lies within the hysteresis band). The crypto port keeps that state in `self.held`, because map03 §2.5 forbids the name `state`.
- **Text and size rules**: the new tests hold no T-RO-01 text token (plan rule "Bridge text"); the order call is spelled `"submit" + "_order"`. No line exceeds 120 characters, and every new function is under 60 lines (`run` 59, `check_input` 38).

**Files:**
- Modify: `tools/nautilus/sandbox.py`. Step 6 writes the whole file. Of Task 1's definitions only `run` (the stub) and `main` (the C-05 stderr line) change; 5.2.9's ports and the 6.1 checks are added.
- Modify: `tools/nautilus/launch.py`. Append only: `FIXTURES`, `_FIXTURE_CLOSES`, `_fixture_ts`, `fixture_inputs` (51 lines).
- Modify: `tests/nautilus_acceptance.py`. Insert only: the Task 3 block before the `# CLI` banner (468 lines).
- Test: `tests/nautilus_acceptance.py` (suite `nautilus`, registered at Task 2):
  - layer 1: `test_px_fixture_inputs_follow_6_1_and_8_2`, `test_px_sandbox_avoids_excluded_constructs`;
  - layer 2: `test_l2_04_fills_identical_across_processes`, `test_l2_05a_refusals_exit_20_before_the_engine`, `test_l2_05b_input_linked_to_env_refused`.
- Unchanged: `tests/run_all.py`, `README.md`, `tests/macro_m0_harness.py`, `tests/macro_registry.csv` (since Task 2 the suite is registered and the sandbox is scanned), every CRLF file, and `qa/acceptance_results.json`.

**Interfaces:**
- Consumes:
  - C1: the section-7 id at the head of every reason, the `input.json` bytes, the encoding rules.
  - C2: `SANDBOX`, `make_tempdir`, `build_launch`, `run_child`, `resolve_unshare`, `cleanup_tempdir`, and `ChildResult.returncode`, `.timed_out`, `.stdout`, `.stderr_tail`, `.census`.
  - C3 (modes, exit codes, input and output files), C5 and C6.
  - C8: `ROOT`, `layer2`, `tests()` with `guarded`.
  - Task 2's `tests.macro_m0_harness._offences` (rules A to F).
  - `tests.acceptance._code_only` (`tests/acceptance.py:33`), read-only.
  - `core.quant.gate_ledger.ledger_hash`.
- Produces:
  - C2: `FIXTURES` and `fixture_inputs(name) -> tuple[bytes, bytes]`.
  - C3: `run --in <dir>` in full (exit 0, 10 or 20), with the four output files of C3 and the manifest of C6. On exit 20, no file is written and the last stderr line is `C-05: <reason>` (**CONTRACT ISSUE 1**).
  - Module-level names in `tests/nautilus_acceptance.py` that Task 4 may reuse and must not redefine (**CONTRACT ISSUE 2**): `_sandbox_run`, `_check_run`, `_positive_control`, `_refused_before_engine`, `_check_env_precision`, `_canonical`, `_link`, `EMPTY_LEDGER_HASH`, `INPUT_KEYS`, `F1_INPUT`, `F2_INPUT`, `F_TABLES`, `OUTPUTS`, `MANIFEST_KEYS`, `MANIFEST_RESULT_KEYS`, `MANIFEST_ENGINE`, `FILLS_HEADER`, `ORDER_CALL`.

Every command below is one line, run after the prefix `S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen && ` (plan rules). The module CLI prints a traceback on stderr before each `FAIL` line, and a blank line before its summary line.

- [ ] **Step 1: Check the starting point.** No file changes.
  - `git log -1 --format=%s` prints Task 2's commit subject.
  - `git status --short`: write its lines down. Step 11 expects exactly these lines plus this task's three paths.
  - `md5sum qa/acceptance_results.json` prints `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`.
  - `python3 -B -c "import tests.nautilus_acceptance as A; print(all(hasattr(A, n) for n in ('ast', 'hashlib', 'json', 'os', 'Path', 'Callable', 'NotRun', 'launch', 'ROOT', 'layer2')))"` prints `True`.
  - `python3 -B -c "import tools.nautilus.launch as L; print(all(hasattr(L, n) for n in ('hashlib', 'json', 'SANDBOX', 'make_tempdir', 'build_launch', 'run_child', 'resolve_unshare', 'cleanup_tempdir')), hasattr(L, 'fixture_inputs'))"` prints `True False`.
  - `python3 -B -m tests.nautilus_acceptance` ends `9/13 passed, 0 failed, 4 not run`.
  - `python3 -B -m tests.macro_m0_harness` ends `14/14 passed, 0 failed, 0 not run`.

- [ ] **Step 2: Write the failing tests.** Edit `tests/nautilus_acceptance.py` (LF) with the Edit tool. `old_string` is these four lines:
```python
# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(
```
  `new_string` is the block below, then two blank lines, then the same four lines. The block uses the module's own imports and adds none. `_refused_before_engine`, L2-5a and L2-5b assert the stderr line of **CONTRACT ISSUE 1**.
```python
# --------------------------------------------------------------------------- #
# Plan Task 3 (spec Step 5): the sandbox and fixture_inputs
# --------------------------------------------------------------------------- #
EMPTY_LEDGER_HASH = "d751713988987e9331980363e24189ce"      # gate_ledger.ledger_hash([]): the md5 of "[]" (6.1)
INPUT_KEYS = frozenset({"schema", "strategy", "params", "instrument", "capital_usd", "cost_bps", "stress",
                        "fill_seed", "price_precision", "size_precision", "volume", "n_bars", "bars_sha256",
                        "ledger_hash_after_registration"})                            # C5: exactly these 14
F1_DATES = ("2001-01-02", "2001-01-03", "2001-01-04", "2001-01-05", "2001-01-08", "2001-01-09", "2001-01-10",
            "2001-01-11", "2001-01-12", "2001-01-15", "2001-01-16", "2001-01-17")   # weekdays; bars 21:00 UTC
F2_DATES = tuple(f"2021-01-{d:02d}" for d in range(1, 12))                          # bars 00:00 UTC next day
F1_PRICES = (97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97)
F2_PRICES = (50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800)
F1_INPUT = {"schema": "nautilus-bridge-input/2", "strategy": "trend_switch",
            "params": {"rule": "sma", "lookback": 3, "step": 2}, "instrument": "SPY", "capital_usd": "1005001",
            "cost_bps": "50", "stress": "1", "fill_seed": 42, "price_precision": 9, "size_precision": 0,
            "volume": "1000000000", "n_bars": 12,
            "bars_sha256": "29844d2fd9185e1d303a1f56f981ccac3bb8f840e0064a8c920f0ef2bffaf93c",
            "ledger_hash_after_registration": EMPTY_LEDGER_HASH}
F2_INPUT = {"schema": "nautilus-bridge-input/2", "strategy": "crypto_trend",
            "params": {"hysteresis": 0.2, "lookbacks": [1, 2], "mas": [2, 3]}, "instrument": "BTC/USD",
            "capital_usd": "53053", "cost_bps": "10", "stress": "1", "fill_seed": 42, "price_precision": 9,
            "size_precision": 8, "volume": "1000000000", "n_bars": 11,
            "bars_sha256": "44b665f8590413aaaea02f2faa5f50e304c5432d7b84e5972aec8183b562bb25",
            "ledger_hash_after_registration": EMPTY_LEDGER_HASH}
N1_BARS_SHA256 = "a9e3bf5523d4536c93ae8431b7599fd5a83d70abe7e62bb4ecf224b73671ef39"
SANDBOX_IMPORTS = """import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy
"""                                                                                  # spec 5.2.9, verbatim
SANDBOX_DEFS = ("Refused", "inside", "plain_mean", "require_backtest_environment", "require_backtest_clock",
                "make_fee_model", "build_engine", "PortConfig", "TrendSwitchConfig", "CryptoTrendConfig", "Port",
                "TrendSwitchPort", "CryptoTrendPort", "run", "check_env", "guard_selftest", "main")   # 5.2.9's order
ORDER_CALL = "submit" + "_order"          # the one exempt call, spelled so this file holds no T-RO-01 token (3.11)
PORT_METHODS = {"on_start", "on_bar", "place", "on_order_filled", "on_order_denied", "on_order_rejected"}
EXCLUDED_TEXT = ("AT_THE_CLOSE", "LatencyModel", "latency_model", "PortfolioAnalyzer", "analyzer", "report",
                 "MARGIN", "BacktestNode", "ParquetDataCatalog", "catalog", "streaming", "log_level_file",
                 "modify_order", "cancel_order", "close_position", "market_exit")   # and ORDER_CALL + "_list"
VENUE_KEYWORDS = {"oms_type": "OmsType.NETTING", "account_type": "AccountType.CASH", "bar_execution": "True",
                  "bar_adaptive_high_low_ordering": "False", "allow_cash_borrowing": "False"}   # spec 5.2.3
OUTPUTS = ["decisions.csv", "fills.csv", "manifest.json", "onbar_equity.csv"]       # spec 5.2.6
MANIFEST_KEYS = {"schema", "read_only", "mode", "python", "system", "machine", "precision", "environment",
                 "strategy_started", "input", "engine", "result", "hashes", "valid", "invalid_reasons"}   # C6
MANIFEST_RESULT_KEYS = {"bars_seen", "iterations", "backtest_end", "force_stop", "orders_total", "orders_filled",
                        "denied", "rejected", "orders_not_filled", "account_balance_usd", "final_qty",
                        "stats_pnls_empty"}
MANIFEST_ENGINE = {"run_analysis": False, "log_level": "ERROR", "log_colors": False, "account_type": "CASH",
                   "oms_type": "NETTING", "allow_cash_borrowing": False, "bar_execution": True, "fill_seed": 42}
FILLS_HEADER = "ts_event,order_side,last_qty,last_px,commission,commission_ccy,trade_id,venue_order_id"
F_TABLES = {   # spec 8.2: per fill (bar, side, last_qty, last_px at 9 decimals, commission); decisions (bar, action)
    "F1": {"fills": [(3, "BUY", "10000", "100.000000000", "5000.00"), (5, "SELL", "10000", "96.000000000", "4800.00"),
                     (7, "BUY", "9600", "99.000000000", "4752.00"), (11, "SELL", "9600", "97.000000000", "4656.00")],
           "decisions": [(3, "buy"), (5, "sell"), (7, "buy"), (9, "hold"), (11, "sell")],
           "balance": "926593.00"},
    "F2": {"fills": [(3, "BUY", "1.00000000", "53000.000000000", "53.00"),
                     (5, "SELL", "1.00000000", "50000.000000000", "50.00"),
                     (7, "BUY", "0.98812079", "50500.000000000", "49.90"),
                     (9, "SELL", "0.98812079", "51000.000000000", "50.39")],
           "decisions": [(3, "buy"), (4, "hold"), (5, "sell"), (6, "hold"), (7, "buy"), (8, "hold"), (9, "sell"),
                         (10, "hold")],
           "balance": "50343.77"},
}


def _bar_ns(day: str, crypto: bool) -> int:
    """8.2's bar time, computed with datetime (launch uses integer day arithmetic): 21:00 UTC on the date, or 00:00
    UTC on the next calendar day for the crypto fixture."""
    from datetime import date, datetime, timedelta, timezone
    d = date.fromisoformat(day) + timedelta(days=1 if crypto else 0)
    return int(datetime(d.year, d.month, d.day, 0 if crypto else 21, tzinfo=timezone.utc).timestamp()) * 10**9


def _canonical(obj: dict) -> bytes:
    """C1's input.json bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sandbox_run(python: Path, raw: bytes, bars: bytes, *, prepare: Callable[[Path], None] | None = None,
                 in_arg: Callable[[Path], str] = str) -> tuple[launch.ChildResult, dict[str, bytes]]:
    """`sandbox.py run --in <in_arg(temp dir)>` through the launch contract, with these input.json and bars.csv
    bytes; `prepare(tmp)` may change the temp dir first. Returns the ChildResult and the bytes of every file the
    child left in the temp dir (input.json and bars.csv excluded); the temp dir is removed."""
    tmp = launch.make_tempdir()
    try:
        (tmp / "input.json").write_bytes(raw)
        (tmp / "bars.csv").write_bytes(bars)
        if prepare is not None:
            prepare(tmp)
        child = launch.build_launch(["run", "--in", in_arg(tmp)], tempdir=tmp, venv_python=python,
                                    unshare=launch.resolve_unshare())
        result = launch.run_child(child)
        out = {p.name: p.read_bytes() for p in sorted(tmp.iterdir())
               if p.is_file() and not p.is_symlink() and p.name not in ("input.json", "bars.csv")}
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert left == [], left
    return result, out


def _positive_control(python: Path, name: str) -> dict[str, bytes]:
    """The unperturbed fixture runs: exit 0 and the four output files of 5.2.6."""
    raw, bars = launch.fixture_inputs(name)
    result, out = _sandbox_run(python, raw, bars)
    assert result.returncode == 0 and sorted(out) == OUTPUTS, (
        f"positive control {name}: exit {result.returncode}, files {sorted(out)}, stderr {result.stderr_tail[-300:]!r}")
    return out


def _refused_before_engine(label: str, reason: str, result: launch.ChildResult, out: dict[str, bytes]) -> None:
    """C-05 (section 7): exit 20, no file written, and the last stderr line "C-05: <reason>"."""
    last = (result.stderr_tail.strip().splitlines() or [""])[-1]
    assert (result.returncode, out, last) == (20, {}, f"C-05: {reason}"), (
        f"{label}: exit {result.returncode}, files {sorted(out)}, stderr {result.stderr_tail[-300:]!r}")


def _check_env_precision(python: Path) -> dict:
    """The precision block that `sandbox.py --check-env` prints, read at run time (QA-14)."""
    tmp = launch.make_tempdir()
    try:
        result = launch.run_child(launch.build_launch(["--check-env"], tempdir=tmp, venv_python=python,
                                                      unshare=launch.resolve_unshare()))
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert result.returncode == 0 and left == [], (result.returncode, left, result.stderr_tail[-300:])
    return json.loads(result.stdout)["precision"]


def _check_run(name: str, raw: bytes, bars: bytes, result: launch.ChildResult, out: dict[str, bytes]) -> dict:
    """A valid run of fixture F1 or F2: exit 0; C6's manifest with every echo and hash; 8.2's fills and decisions."""
    table = F_TABLES[name]
    assert result.returncode == 0 and not result.timed_out and sorted(out) == OUTPUTS, (
        f"{name}: exit {result.returncode}, files {sorted(out)}, stderr {result.stderr_tail[-300:]!r}")
    assert out["manifest.json"].endswith(b"}\n") and all(b"\r" not in v for v in out.values()), name
    m = json.loads(out["manifest.json"])
    inp = json.loads(raw)
    ts = [int(line.split(",")[1]) for line in bars.decode("utf-8").splitlines()[1:]]
    assert set(m) == MANIFEST_KEYS and set(m["result"]) == MANIFEST_RESULT_KEYS, sorted(m)
    assert (m["schema"], m["read_only"], m["mode"], m["environment"]) == (
        "nautilus-bridge-manifest/2", True, "run", "BACKTEST"), m
    assert m["engine"] == MANIFEST_ENGINE and m["strategy_started"] is True, m["engine"]
    assert m["input"] == {"input_json_sha256": hashlib.sha256(raw).hexdigest(), "bars_sha256": inp["bars_sha256"],
                          "bars_fed": len(ts), "first_ts": ts[0], "last_ts": ts[-1], "cost_bps": inp["cost_bps"],
                          "stress": inp["stress"],
                          "ledger_hash_after_registration": inp["ledger_hash_after_registration"]}, m["input"]
    assert m["hashes"] == {f: hashlib.sha256(out[f]).hexdigest() for f in OUTPUTS if f != "manifest.json"}
    r = m["result"]
    assert (m["valid"], m["invalid_reasons"], r["bars_seen"], r["backtest_end"], r["force_stop"]) == (
        True, [], len(ts), ts[-1], False), (m["invalid_reasons"], r)
    assert (r["orders_total"], r["orders_filled"], r["denied"], r["rejected"], r["orders_not_filled"]) == (
        4, 4, 0, 0, []), r
    assert (r["account_balance_usd"], r["final_qty"], r["stats_pnls_empty"]) == (table["balance"], "0", True), r
    fills = out["fills.csv"].decode("utf-8").splitlines()
    assert fills[0] == FILLS_HEADER, fills[0]
    got = [(ts.index(int(f[0])), f[1], f[2], f[3], f[4], f[5]) for f in (row.split(",") for row in fills[1:])]
    assert got == [(*row, "USD") for row in table["fills"]], got
    decisions = out["decisions.csv"].decode("utf-8").splitlines()
    assert decisions[0] == "i,ts_event,decision,margin,action", decisions[0]
    got = [(int(d[0]), d[4]) for d in (row.split(",") for row in decisions[1:])]
    assert got == table["decisions"], got
    equity = out["onbar_equity.csv"].decode("utf-8").splitlines()
    assert equity[0] == "i,ts_event,close,cash,qty,equity_pre" and len(equity) - 1 == len(ts), equity[:2]
    return m


def _link(name: str, target: Callable[[Path], Path]) -> Callable[[Path], None]:
    """prepare(tmp): replace tmp/name by a symbolic link to target(tmp); WinError 1314 is a NotRun (OPS-R2-5)."""
    def prepare(tmp: Path) -> None:
        path, to = tmp / name, target(tmp)
        if path.exists():
            path.unlink()
        try:
            os.symlink(to, path, target_is_directory=to.is_dir())
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                raise NotRun("OWNER: enable Developer Mode, or accept this NotRun") from exc
            raise
    return prepare


def _put(key: str, value) -> Callable[[dict], None]:
    def change(inp: dict) -> None:
        inp[key] = value
    return change


def _put_param(key: str, value) -> Callable[[dict], None]:
    def change(inp: dict) -> None:
        inp["params"][key] = value
    return change


def _drop(key: str) -> Callable[[dict], None]:
    def change(inp: dict) -> None:
        del inp[key]
    return change


def _swap_ts(text: str) -> str:
    """bars.csv with the timestamps of rows 3 and 4 swapped."""
    lines = text.split("\n")
    a, b = lines[4].split(","), lines[5].split(",")
    a[1], b[1] = b[1], a[1]
    lines[4], lines[5] = ",".join(a), ",".join(b)
    return "\n".join(lines)


def _repeat_ts(text: str) -> str:
    """bars.csv whose row 4 repeats row 3's timestamp."""
    lines = text.split("\n")
    a, b = lines[4].split(","), lines[5].split(",")
    b[1] = a[1]
    lines[5] = ",".join(b)
    return "\n".join(lines)


def _l2_05a_cases(precision: dict) -> list[tuple[str, str, str, Callable[[dict], None] | None,
                                                 Callable[[str], str] | None]]:
    """(rule, label, base fixture, change to input.json, change to bars.csv): one single-field perturbation per rule
    of spec 6.1 (QA-R3-4), each refused by its own rule; the maxima come from --check-env (QA-14). A bars.csv change
    re-hashes bars_sha256, so only the rule named fails."""
    qmax, pmax, fp = int(precision["QUANTITY_MAX"]), int(precision["PRICE_MAX"]), precision["FIXED_PRECISION"]
    field = "unknown or missing field"
    cases = [(field, "unknown field", "F1", _put("extra", 1), None)]
    cases += [(field, f"missing {k}", "F1", _drop(k), None) for k in sorted(INPUT_KEYS)]
    cases += [(rule, label, "F1", change, None) for rule, label, change in (
        ("schema", "schema /1", _put("schema", "nautilus-bridge-input/1")),
        ("strategy", "strategy pairs", _put("strategy", "pairs")),
        ("params fields", "trend params under crypto_trend", _put("strategy", "crypto_trend")),
        ("params is not an object", "params a list", _put("params", [])),
        ("params fields", "params extra key", _put_param("x", 1)),
        ("params.rule", "params.rule ema", _put_param("rule", "ema")),
        ("params.lookback or params.step", "lookback 0", _put_param("lookback", 0)),
        ("params.lookback or params.step", "lookback 5001", _put_param("lookback", 5001)),
        ("params.lookback or params.step", "lookback a string", _put_param("lookback", "3")),
        ("params.lookback or params.step", "lookback a bool", _put_param("lookback", True)),
        ("params.lookback or params.step", "step 0", _put_param("step", 0)),
        ("params.lookback or params.step", "step 5001", _put_param("step", 5001)),
        ("instrument", "instrument QQQ", _put("instrument", "QQQ")),
        ("capital_usd", "capital 0", _put("capital_usd", "0")),
        ("capital_usd", "capital PRICE_MAX + 1", _put("capital_usd", str(pmax + 1))),
        ("capital_usd", "capital an int", _put("capital_usd", 1005001)),
        ("capital_usd", "capital leading zero", _put("capital_usd", "01005001")),
        ("cost_bps", "cost_bps -1", _put("cost_bps", "-1")),
        ("cost_bps", "cost_bps 1000.5", _put("cost_bps", "1000.5")),
        ("cost_bps", "cost_bps a float", _put("cost_bps", 50.0)),
        ("cost_bps", "cost_bps NaN", _put("cost_bps", "NaN")),
        ("cost_bps", "cost_bps empty", _put("cost_bps", "")),
        ("stress", "stress 0", _put("stress", "0")),
        ("stress", "stress 3", _put("stress", "3")),
        ("stress", "stress an int", _put("stress", 1)),
        ("fill_seed", "fill_seed -1", _put("fill_seed", -1)),
        ("fill_seed", "fill_seed 2**32", _put("fill_seed", 2**32)),
        ("fill_seed", "fill_seed a float", _put("fill_seed", 42.0)),
        ("price_precision", "price_precision -1", _put("price_precision", -1)),
        ("price_precision", "price_precision FIXED_PRECISION + 1", _put("price_precision", fp + 1)),
        ("size_precision", "size_precision -1", _put("size_precision", -1)),
        ("size_precision", "size_precision FIXED_PRECISION + 1", _put("size_precision", fp + 1)),
        ("volume", "volume 0", _put("volume", "0")),
        ("volume", "volume QUANTITY_MAX + 1", _put("volume", str(qmax + 1))),
        ("volume", "volume an int", _put("volume", 1000000000)),
        ("n_bars", "n_bars 0", _put("n_bars", 0)),
        ("n_bars", "n_bars 100001", _put("n_bars", 100001)),
        ("n_bars differs from bars.csv", "n_bars 11", _put("n_bars", 11)),
        ("bars_sha256 differs from bars.csv", "bars_sha256 doctored", _put("bars_sha256", "0" * 64)),
        ("bars_sha256 format", "bars_sha256 upper case", _put("bars_sha256", F1_INPUT["bars_sha256"].upper())),
        ("bars_sha256 format", "bars_sha256 63 hex", _put("bars_sha256", F1_INPUT["bars_sha256"][:63])),
        ("ledger_hash_after_registration format", "ledger hash not hex",
         _put("ledger_hash_after_registration", "xyz")),
        ("ledger_hash_after_registration format", "ledger hash 31 hex",
         _put("ledger_hash_after_registration", EMPTY_LEDGER_HASH[:31])),
        ("ledger_hash_after_registration format", "ledger hash upper case",
         _put("ledger_hash_after_registration", EMPTY_LEDGER_HASH.upper())))]
    cases += [(rule, label, "F1", None, change) for rule, label, change in (
        ("close 3", "close with 2 decimals at 9", lambda t: t.replace("100.000000000", "100.00", 1)),
        ("close 3", "close with 10 decimals", lambda t: t.replace("100.000000000", "100.0000000000", 1)),
        ("close 3", "close zero", lambda t: t.replace("100.000000000", "0.000000000", 1)),
        ("bars.csv header", "header i,ts,close", lambda t: t.replace("i,ts_ns,close", "i,ts,close", 1)),
        ("bars.csv line ends", "CRLF line ends", lambda t: t.replace("\n", "\r\n")),
        ("bars.csv line ends", "no final newline", lambda t: t[:-1]),
        ("timestamps not strictly increasing", "timestamps swapped", _swap_ts),
        ("timestamps not strictly increasing", "timestamp repeated", _repeat_ts),
        ("bars.csv row 3", "row index 4 for 3", lambda t: t.replace("\n3,", "\n4,", 1)))]
    cases += [(rule, label, "F2", change, None) for rule, label, change in (
        ("params.hysteresis", "hysteresis 1.0", _put_param("hysteresis", 1.0)),
        ("params.hysteresis", "hysteresis -0.1", _put_param("hysteresis", -0.1)),
        ("params.hysteresis", "hysteresis an int", _put_param("hysteresis", 0)),
        ("params.lookbacks", "lookbacks empty", _put_param("lookbacks", [])),
        ("params.lookbacks", "lookbacks item 5001", _put_param("lookbacks", [1, 5001])),
        ("params.mas", "mas 17 items", _put_param("mas", [2] * 17)),
        ("params.mas", "mas item 0", _put_param("mas", [0, 3])))]
    return cases


def test_px_fixture_inputs_follow_6_1_and_8_2():
    """Spec 8.2, 6.1, C1 and C5 (QA-R3-1): launch.fixture_inputs builds F1, F1r, F2 and N1 as C1's canonical
    input.json bytes with exactly the 14 fields, and LF bars.csv bytes whose rows, timestamps (21:00 UTC on
    weekdays from 2001-01-02; 00:00 UTC the day after each date from 2021-01-01) and closes are 8.2's; the ledger
    hash is an empty ledger's; F1r's child inputs are F1's; N1 is F1 with volume "4000" and 2 price decimals; any
    other name is a KeyError."""
    from core.quant import gate_ledger
    assert launch.FIXTURES == ("F1", "F1r", "F2", "N1"), launch.FIXTURES
    assert gate_ledger.ledger_hash([]) == EMPTY_LEDGER_HASH
    built = {name: launch.fixture_inputs(name) for name in launch.FIXTURES}
    for name, (raw, bars) in built.items():
        assert launch.fixture_inputs(name) == (raw, bars), f"{name}: two calls differ"
        inp = json.loads(raw)
        assert raw == _canonical(inp) and set(inp) == INPUT_KEYS, (name, raw[:80])
        assert b"\r" not in raw + bars and bars.endswith(b"\n") and not raw.endswith(b"\n"), name
        assert inp["bars_sha256"] == hashlib.sha256(bars).hexdigest(), name
        crypto = name == "F2"
        dates, prices = (F2_DATES, F2_PRICES) if crypto else (F1_DATES, F1_PRICES)
        decimals = "0" * inp["price_precision"]
        want = ["i,ts_ns,close"] + [f"{i},{_bar_ns(d, crypto)},{c}.{decimals}"
                                    for i, (d, c) in enumerate(zip(dates, prices))]
        assert bars.decode("utf-8").split("\n") == want + [""], (name, bars[:120])
    assert json.loads(built["F1"][0]) == F1_INPUT and json.loads(built["F2"][0]) == F2_INPUT
    assert built["F1r"] == built["F1"]
    n1 = json.loads(built["N1"][0])
    assert n1 == {**F1_INPUT, "volume": "4000", "price_precision": 2, "bars_sha256": N1_BARS_SHA256}, n1
    assert (_bar_ns("2001-01-02", False), _bar_ns("2021-01-01", True)) == (978469200000000000, 1609545600000000000)
    for other in ("F3", "f1", "N2", ""):
        try:
            launch.fixture_inputs(other)
        except KeyError:
            continue
        raise AssertionError(f"fixture_inputs({other!r}) did not raise KeyError")


def test_px_sandbox_avoids_excluded_constructs():
    """Spec Step 5 done-when, 5.2.3, 5.2.5, 5.2.9 (C-5) and 5.6: sandbox.py keeps 5.2.9's import block verbatim and
    its classes and functions in order, with no __init__ and no super(); on_start starts with the clock guard and
    ends by setting strategy_started; Port.place's one statement is the one order call; no code path uses
    AT_THE_CLOSE, allow_cash_borrowing=True, a latency model, the PortfolioAnalyzer, a report as equity, a MARGIN
    account or another order verb; the venue is NETTING and CASH with bar execution, FillModel(1.0, 0.0, seed) and
    the fee closure; the engine runs without the analyzer at log level ERROR without colours; orders are MARKET GTC;
    and the real sandbox gives no T-RO-01 hit."""
    from tests.acceptance import _code_only
    from tests.macro_m0_harness import _offences
    source = launch.SANDBOX.read_text(encoding="utf-8")
    assert SANDBOX_IMPORTS in source, "sandbox.py lost 5.2.9's import block"
    tree = ast.parse(source)
    defs = [n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
    order = [n for n in defs if n in SANDBOX_DEFS]
    assert order == list(SANDBOX_DEFS), f"sandbox.py keeps 5.2.9's classes and functions in order: {order}"
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    port = {f.name: f for f in classes["Port"].body if isinstance(f, ast.FunctionDef)}
    assert set(port) == PORT_METHODS, sorted(port)
    assert [ast.unparse(s) for s in port["place"].body] == [f"self.{ORDER_CALL}(order)"], ast.unparse(port["place"])
    start = port["on_start"].body
    assert (ast.unparse(start[0]), ast.unparse(start[-1])) == (
        "require_backtest_clock(self.clock)", "self.strategy_started = True"), ast.unparse(port["on_start"])
    for cls in ("TrendSwitchPort", "CryptoTrendPort"):
        assert [f.name for f in classes[cls].body if isinstance(f, ast.FunctionDef)] == ["decide"], cls
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    functions = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "__init__" not in functions and "super" not in names and "state" not in attrs, "rule F3; map03 2.5"
    code = _code_only(launch.SANDBOX)
    assert code.count(ORDER_CALL) == 1, code.count(ORDER_CALL)
    excluded = [w for w in (*EXCLUDED_TEXT, ORDER_CALL + "_list") if w in code]
    assert excluded == [], excluded
    every_call = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]

    def callee(c: ast.Call) -> str:
        return c.func.id if isinstance(c.func, ast.Name) else c.func.attr if isinstance(c.func, ast.Attribute) else ""
    kw: dict[str, list[str]] = {}
    for c in every_call:
        for k in c.keywords:
            kw.setdefault(k.arg, []).append(ast.unparse(k.value))
    flags = (kw["allow_cash_borrowing"], kw["run_analysis"], kw["log_level"], kw["log_colors"], kw["time_in_force"])
    assert flags == (["False"], ["False"], ["'ERROR'"], ["False"], ["TimeInForce.GTC"]), flags
    named = {n: [c for c in every_call if callee(c) == n] for n in ("add_venue", "FillModel", ORDER_CALL, "place")}
    assert {n: len(v) for n, v in named.items()} == dict.fromkeys(named, 1), {n: len(v) for n, v in named.items()}
    venue = {k.arg: ast.unparse(k.value) for k in named["add_venue"][0].keywords}
    assert {k: venue.get(k) for k in VENUE_KEYWORDS} == VENUE_KEYWORDS, venue
    assert venue["fee_model"] == "make_fee_model(inp['cost_bps'], inp['stress'])", venue["fee_model"]
    fill = {k.arg: ast.unparse(k.value) for k in named["FillModel"][0].keywords}
    assert (fill.get("prob_fill_on_limit"), fill.get("prob_slippage"), "random_seed" in fill) == (
        "1.0", "0.0", True), fill
    factory = sorted({callee(c) for c in every_call
                      if isinstance(c.func, ast.Attribute) and ast.unparse(c.func.value) == "self.order_factory"})
    assert factory == ["market"], factory
    assert _offences(launch.SANDBOX) == [], _offences(launch.SANDBOX)


def test_l2_04_fills_identical_across_processes():
    """L2-4 (spec 3.5): F1 and F2 each run in two separate processes through the launch contract and give the same
    fills.csv SHA-256; every output file and both import censuses are identical too; each run is valid, its
    manifest has C6's fields, echoes and hashes, and its fills and decisions are 8.2's."""
    python = layer2()
    for name in ("F1", "F2"):
        raw, bars = launch.fixture_inputs(name)
        runs = [_sandbox_run(python, raw, bars) for _ in range(2)]
        for result, out in runs:
            _check_run(name, raw, bars, result, out)
        (r1, o1), (r2, o2) = runs
        assert hashlib.sha256(o1["fills.csv"]).hexdigest() == hashlib.sha256(o2["fills.csv"]).hexdigest(), name
        assert o1 == o2, [f for f in OUTPUTS if o1[f] != o2[f]]
        assert r1.census == r2.census and len(r1.census) > 100, (name, len(r1.census), len(r2.census))


def test_l2_05a_refusals_exit_20_before_the_engine():
    """L2-5a (spec 6.1, 7 C-05; QA-R3-4, QA-14, QA-R2-8): F1 and F2 unperturbed exit 0; then each single-field
    perturbation of 6.1, an input.json that is not JSON and a bars.csv that is not UTF-8 exit 20 with no file written
    and the refusing rule on stderr ("C-05: input refused: <rule>"); QUANTITY_MAX, PRICE_MAX and FIXED_PRECISION are
    read from --check-env at run time."""
    python = layer2()
    for name in ("F1", "F2"):
        _positive_control(python, name)
    cases = _l2_05a_cases(_check_env_precision(python))
    for rule, label, name, change, bars_change in cases:
        raw, bars = launch.fixture_inputs(name)
        inp = json.loads(raw)
        if bars_change is not None:
            bars = bars_change(bars.decode("utf-8")).encode("utf-8")
            inp["bars_sha256"] = hashlib.sha256(bars).hexdigest()
        if change is not None:
            change(inp)
        result, out = _sandbox_run(python, _canonical(inp), bars)
        _refused_before_engine(label, f"input refused: {rule}", result, out)
    raw, bars = launch.fixture_inputs("F1")
    result, out = _sandbox_run(python, b"{not json", bars)
    _refused_before_engine("input.json not JSON", "input refused: input.json is not UTF-8 JSON", result, out)
    inp, bad = json.loads(raw), bars[:-1] + b"\xff\n"
    inp["bars_sha256"] = hashlib.sha256(bad).hexdigest()
    result, out = _sandbox_run(python, _canonical(inp), bad)
    _refused_before_engine("bars.csv not UTF-8", "input refused: bars.csv is not UTF-8", result, out)
    print(f"  {len(cases) + 2} perturbations refused with exit 20")


def test_l2_05b_input_linked_to_env_refused():
    """L2-5b (spec 5.2.8; SECURITY-3): with input.json a symbolic link to the repo's .env, the sandbox exits 20 with
    no file written, before it opens anything; so it does with bars.csv linked there, and with a --in that is
    relative or that is not its own resolve() (a link to the temp dir). F1 unlinked exits 0. Without the right to
    make a link on Windows (WinError 1314): NotRun (OPS-R2-5)."""
    python = layer2()
    _positive_control(python, "F1")
    raw, bars = launch.fixture_inputs("F1")
    in_rule = "run needs --in <an absolute directory equal to its own resolve()>"
    for label, reason, prepare, in_arg in (
            ("input.json linked to the repo's .env", "input refused: input.json",
             _link("input.json", lambda tmp: ROOT / ".env"), str),
            ("bars.csv linked to the repo's .env", "input refused: bars.csv",
             _link("bars.csv", lambda tmp: ROOT / ".env"), str),
            ("--in .", in_rule, None, lambda tmp: "."),
            ("--in a link to the temp dir", in_rule, _link("alias", lambda tmp: tmp), lambda tmp: str(tmp / "alias"))):
        result, out = _sandbox_run(python, raw, bars, prepare=prepare, in_arg=in_arg)
        _refused_before_engine(label, reason, result, out)
```
  Then `git diff --numstat tests/nautilus_acceptance.py` prints 468 insertions, 0 deletions and the path (tab-separated).

- [ ] **Step 3: Run the new tests and watch them fail.**
  - Key unset: `python3 -B -m tests.nautilus_acceptance -k test_px_fixture_inputs -k test_px_sandbox_avoids -k test_l2_04 -k test_l2_05`. Expected, exit 1:
```
NOT_RUN test_l2_04_fills_identical_across_processes OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_05a_refusals_exit_20_before_the_engine OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_05b_input_linked_to_env_refused OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
FAIL test_px_fixture_inputs_follow_6_1_and_8_2 AttributeError: module 'tools.nautilus.launch' has no attribute 'FIXTURES'
FAIL test_px_sandbox_avoids_excluded_constructs AssertionError: sandbox.py keeps 5.2.9's classes and functions in order: ['Refused', 'inside', 'plain_mean', 'require_backtest_environment', 'require_backtest_clock', 'make_fee_model', 'build_engine', 'run', 'check_env', 'guard_selftest', 'main']

0/5 passed, 2 failed, 3 not run
```
  - Key set: `QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_04 -k test_l2_05`. Expected, exit 1:
```
FAIL test_l2_04_fills_identical_across_processes AttributeError: module 'tools.nautilus.launch' has no attribute 'fixture_inputs'
FAIL test_l2_05a_refusals_exit_20_before_the_engine AttributeError: module 'tools.nautilus.launch' has no attribute 'fixture_inputs'
FAIL test_l2_05b_input_linked_to_env_refused AttributeError: module 'tools.nautilus.launch' has no attribute 'fixture_inputs'

0/3 passed, 3 failed, 0 not run
```
  - The rest of the suite is untouched: `python3 -B -m tests.nautilus_acceptance` ends `9/18 passed, 2 failed, 7 not run`. `test_l1_15_encoding_rules_hold` and `test_l1_32_every_test_guarded_and_ledgers_unchanged` still PASS.

- [ ] **Step 4: Build the fixtures (C2 `FIXTURES`, `fixture_inputs`).** Append to the end of `tools/nautilus/launch.py` two blank lines and then this block, verbatim, using the Edit tool on the file's last line or `cat >> tools/nautilus/launch.py`. Nothing else in the file changes. `hashlib` and `json` are the module's own imports. `datetime` and `core.quant.gate_ledger` are imported inside the functions, so importing `launch` still loads only the standard library.
```python
# --------------------------------------------------------------------------- #
# Fixtures F1, F1r, F2 and N1 (spec 8.2, 6.1; QA-R3-1): the one builder of their child inputs
# --------------------------------------------------------------------------- #
FIXTURES = ("F1", "F1r", "F2", "N1")
_FIXTURE_CLOSES = {"F1": (97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97),
                   "F2": (50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800)}


def _fixture_ts(name: str) -> list[int]:
    """The bar timestamps (ns) of a fixture (spec 8.2, 5.2.4): F1, F1r and N1 at 21:00 UTC on the 12 weekdays from
    2001-01-02; F2 at 00:00 UTC on the calendar day after each of its 11 dates from 2021-01-01."""
    from datetime import date, timedelta
    if name == "F2":
        days = [date(2021, 1, 2) + timedelta(days=k) for k in range(len(_FIXTURE_CLOSES["F2"]))]
        hour = 0
    else:
        days, d = [], date(2001, 1, 2)
        while len(days) < len(_FIXTURE_CLOSES["F1"]):
            if d.weekday() < 5:
                days.append(d)
            d += timedelta(days=1)
        hour = 21
    return [((d - date(1970, 1, 1)).days * 86400 + hour * 3600) * 10**9 for d in days]


def fixture_inputs(name: str) -> tuple[bytes, bytes]:
    """(input.json bytes, bars.csv bytes) of fixture `name` (spec 8.2 and 6.1), the one builder that L2-4, L2-5a,
    L2-5b, --fixtures, --write-goldens and L1-33 use (QA-R3-1). input.json is C1's canonical JSON, no trailing
    newline; bars.csv is LF. ledger_hash_after_registration is gate_ledger.ledger_hash([]), the hash of an empty
    ledger, since fixtures register nothing (6.1). F1r's child inputs are F1's: F1r differs only in the parent's rf,
    0.0001 per session (QUANT-R2-6). N1 is F1 with volume "4000" and 2 price decimals. KeyError for another name."""
    if name not in FIXTURES:
        raise KeyError(name)
    from core.quant.gate_ledger import ledger_hash
    crypto = name == "F2"
    p = 2 if name == "N1" else 9
    closes = _FIXTURE_CLOSES["F2" if crypto else "F1"]
    rows = ["i,ts_ns,close"] + [f"{i},{t},{c:.{p}f}" for i, (t, c) in enumerate(zip(_fixture_ts(name), closes))]
    bars = ("\n".join(rows) + "\n").encode("utf-8")
    if crypto:
        head = {"strategy": "crypto_trend", "params": {"hysteresis": 0.2, "lookbacks": [1, 2], "mas": [2, 3]},
                "instrument": "BTC/USD", "capital_usd": "53053", "cost_bps": "10", "size_precision": 8}
    else:
        head = {"strategy": "trend_switch", "params": {"rule": "sma", "lookback": 3, "step": 2},
                "instrument": "SPY", "capital_usd": "1005001", "cost_bps": "50", "size_precision": 0}
    inp = {**head, "schema": "nautilus-bridge-input/2", "stress": "1", "fill_seed": 42, "price_precision": p,
           "volume": "4000" if name == "N1" else "1000000000", "n_bars": len(closes),
           "bars_sha256": hashlib.sha256(bars).hexdigest(), "ledger_hash_after_registration": ledger_hash([])}
    return json.dumps(inp, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), bars
```
  Then `git diff --numstat tools/nautilus/launch.py` prints 51 insertions, 0 deletions and the path (tab-separated).

- [ ] **Step 5: Pass the fixture test, then watch the sandbox tests fail on the sandbox.**
  - `python3 -B -m tests.nautilus_acceptance -k test_px_fixture_inputs -k test_l1_15`. Expected: `PASS test_l1_15_encoding_rules_hold`, `PASS test_px_fixture_inputs_follow_6_1_and_8_2`, then `2/2 passed, 0 failed, 0 not run`.
  - `QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_04 -k test_l2_05 -k test_px_sandbox`. Expected, exit 1 (Task 1's `run` refuses every input, silently):
```
FAIL test_l2_04_fills_identical_across_processes AssertionError: F1: exit 20, files [], stderr ''
FAIL test_l2_05a_refusals_exit_20_before_the_engine AssertionError: positive control F1: exit 20, files [], stderr ''
FAIL test_l2_05b_input_linked_to_env_refused AssertionError: positive control F1: exit 20, files [], stderr ''
FAIL test_px_sandbox_avoids_excluded_constructs AssertionError: sandbox.py keeps 5.2.9's classes and functions in order: ['Refused', 'inside', 'plain_mean', 'require_backtest_environment', 'require_backtest_clock', 'make_fee_model', 'build_engine', 'run', 'check_env', 'guard_selftest', 'main']

0/4 passed, 4 failed, 0 not run
```

- [ ] **Step 6: Write the sandbox (spec 5.2 in the structure of 5.2.9).** Replace the whole of `tools/nautilus/sandbox.py` with exactly this content (Write tool; UTF-8, LF, one final newline). The lines that differ from 5.2.9's skeleton are in `run` (the byte read and the port-state lines) and in `main` (the two `ap.exit(20, ...)` lines, **CONTRACT ISSUE 1**); the notes above give the reasons.
```python
"""The NautilusTrader sandbox child (spec 2026-10-26 section 5.2), run only in the hash-pinned venv and launched only
through tools/nautilus/launch.py:

    <venv python> -I -B -X utf8 [-X importtime] <abs sandbox.py> {--check-env | --guard-selftest | run --in <dir>}

Exit codes (5.2.1): 0 valid; 10 complete but invalid (manifest.json says why); 20 input refused before the engine is
built (one "C-05: ..." line on stderr, no file written); 30 a self-test case misbehaved; any other value a crash.
The structure is spec 5.2.9's. This is the only file that places simulated orders: one call in Port.place (5.6
rule A). It opens only files that inside() builds in its temp dir (5.2.8).
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy

VENUE = Venue("SIM")
class Refused(Exception): pass                     # input refused before the engine is built: exit 20
def inside(root, name):                             # 5.2.8: builds every path the sandbox opens
    p = (root / name).resolve()
    if p.parent != root:
        raise Refused(name)
    return p
def plain_mean(xs):                                 # 5.2.5, both ports: a left-to-right loop, never sum()
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)
def require_backtest_environment(env):              # 5.2.5 (C-2)
    if env is not Environment.BACKTEST:
        raise RuntimeError(f"kernel environment {env.name}, not BACKTEST")
def require_backtest_clock(clock):
    if not isinstance(clock, TestClock):
        raise RuntimeError("the strategy clock is not a TestClock")
def make_fee_model(cost_bps, stress):               # 5.2.3: a closure, so no __init__ and no super()
    if Decimal(stress) < 1:
        raise ValueError("stress below 1")
    rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)
    class BpFeeModel(FeeModel):
        def get_commission(self, order, fill_qty, fill_px, instrument):
            return Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate,
                         instrument.quote_currency)
    return BpFeeModel()
def build_engine():                                 # 5.2.3, rows Engine and Kernel check
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), run_analysis=False,
                                                 logging=LoggingConfig(log_level="ERROR", log_colors=False)))
    require_backtest_environment(engine.kernel.environment)
    return engine
class PortConfig(StrategyConfig, frozen=True):      # every parameter lives here, never in an __init__ (rule F3)
    instrument_id: str; bar_type: str; cost_bps: str; stress: str
    closes: list; ts: list                          # the close strings of bars.csv and their ts_ns
class TrendSwitchConfig(PortConfig, frozen=True):
    rule: str; lookback: int; step: int
class CryptoTrendConfig(PortConfig, frozen=True):
    hysteresis: float; lookbacks: list; mas: list
class Port(Strategy):                               # no __init__: Strategy's own stores the config
    def on_start(self):
        require_backtest_clock(self.clock)          # first statement (C-15)
        self.iid = InstrumentId.from_str(self.config.instrument_id)
        self.inst = self.cache.instrument(self.iid)
        self.px = [float(c) for c in self.config.closes]
        self.i, self.held, self.fills, self.decisions, self.equity, self.invalid_reasons = -1, 0, [], [], [], []
        self.denied = self.rejected = 0
        self.subscribe_bars(BarType.from_str(self.config.bar_type))
        self.strategy_started = True                # last statement (C-15)
    def on_bar(self, bar):                          # never raises: Nautilus re-raises, which ends the child
        self.i += 1
        if bar.ts_event != self.config.ts[self.i] or bar.close != Price.from_str(self.config.closes[self.i]):
            self.invalid_reasons.append(f"C-12: bar {self.i} differs from bars.csv")   # id first (QA-R3-8)
            return
        i, close = self.i, self.config.closes[self.i]
        cash = self.portfolio.account(VENUE).balance_total(USD).as_decimal()
        qty = self.portfolio.net_position(self.iid)
        self.equity.append([i, bar.ts_event, close, str(cash), str(qty), str(cash + qty * Decimal(close))])
        decision, margin = self.decide(i)
        if decision is None:
            return
        if self.cache.orders_inflight_count() or self.cache.orders_open_count():
            self.invalid_reasons.append(f"C-13: bar {i}: an order in flight on a decision bar")
            return
        action = "hold"
        if decision != self.held:
            if decision == 1:                       # fee-inclusive sizing: q = floor(cash / (P (1 + c s)))
                c = Decimal(self.config.cost_bps) * Decimal(self.config.stress) / Decimal(10000)
                unit = Decimal(1).scaleb(-self.inst.size_precision)
                q = (cash / (Decimal(close) * (1 + c)) / unit).to_integral_value(rounding=ROUND_FLOOR) * unit
                side = OrderSide.BUY
            else:                                   # exit: the whole net position
                q, side = qty, OrderSide.SELL
            action = "skip_zero_qty"
            if q > 0:
                action = "buy" if decision == 1 else "sell"
                self.held = decision
        self.decisions.append([i, bar.ts_event, decision, repr(margin), action])
        if action not in ("buy", "sell"):
            return
        self.place(self.order_factory.market(self.iid, side, Quantity(q, self.inst.size_precision),
                                             time_in_force=TimeInForce.GTC))
    def place(self, order):                         # the one exempt call (5.6 rule A)
        self.submit_order(order)
    def on_order_filled(self, ev):                  # one fills.csv row (5.2.6), no UUID
        self.fills.append([ev.ts_event, ev.order_side.name, str(ev.last_qty), str(ev.last_px),
                           f"{ev.commission.as_decimal():.2f}", ev.commission.currency.code, str(ev.trade_id),
                           str(ev.venue_order_id)])
    def on_order_denied(self, ev): self.denied += 1
    def on_order_rejected(self, ev): self.rejected += 1
class TrendSwitchPort(Port):
    def decide(self, i):                            # -> (decision or None, margin), the table of 5.2.5
        L, s, P = self.config.lookback, self.config.step, self.px
        if i < L or (i - L) % s:
            return None, None
        if self.config.rule == "sma":
            mean = plain_mean(P[i - L + 1:i + 1])
            return (1 if P[i] > mean else 0), abs(P[i] - mean) / P[i]
        r = P[i] / P[i - L] - 1.0                   # tsmom, raw: pnl_matrix passes no rate
        return (1 if r > 0.0 else 0), abs(r)
class CryptoTrendPort(Port):
    def decide(self, i):
        P, cfg = self.px, self.config
        if i < max(max(cfg.lookbacks), max(cfg.mas)):
            return None, None
        refs = [P[i - k] for k in cfg.lookbacks] + [plain_mean(P[i - n + 1:i + 1]) for n in cfg.mas]
        votes = [(P[i] - ref > 0) - (P[i] - ref < 0) for ref in refs]
        comp = sum(votes) / len(votes)
        held = 1 if comp > cfg.hysteresis else 0 if comp < -cfg.hysteresis else self.held
        return held, min(abs(P[i] - ref) / P[i] for ref in refs)
FIELDS = frozenset({"schema", "strategy", "params", "instrument", "capital_usd", "cost_bps", "stress", "fill_seed",
                    "price_precision", "size_precision", "volume", "n_bars", "bars_sha256",
                    "ledger_hash_after_registration"})
def need(ok, what):                                 # one rule of 6.1; a refusal is exit 20 (C-05)
    if not ok:
        raise Refused(what)
def is_int(x, lo, hi):
    return type(x) is int and lo <= x <= hi
def int_text(x, lo, hi):
    return type(x) is str and x.isascii() and x.isdigit() and x == str(int(x)) and lo <= int(x) <= hi
def is_hex(x, n):
    return type(x) is str and len(x) == n and all(ch in "0123456789abcdef" for ch in x)
def check_params(inp):                              # 6.1, row params
    prm = inp["params"]
    need(type(prm) is dict, "params is not an object")
    if inp["strategy"] == "trend_switch":
        need(set(prm) == {"rule", "lookback", "step"}, "params fields")
        need(prm["rule"] in ("sma", "tsmom"), "params.rule")
        need(is_int(prm["lookback"], 1, 5000) and is_int(prm["step"], 1, 5000), "params.lookback or params.step")
        return
    need(set(prm) == {"hysteresis", "lookbacks", "mas"}, "params fields")
    need(type(prm["hysteresis"]) is float and 0.0 <= prm["hysteresis"] < 1.0, "params.hysteresis")
    for k in ("lookbacks", "mas"):
        v = prm[k]
        need(type(v) is list and 1 <= len(v) <= 16 and all(is_int(x, 1, 5000) for x in v), "params." + k)
def check_input(inp, bars_bytes):                   # 6.1, one rule at a time -> (close strings, ts_ns)
    need(type(inp) is dict and set(inp) == FIELDS, "unknown or missing field")
    need(inp["schema"] == "nautilus-bridge-input/2", "schema")
    need(inp["strategy"] in ("trend_switch", "crypto_trend"), "strategy")
    check_params(inp)
    need(inp["instrument"] in ("SPY", "BTC/USD"), "instrument")
    need(int_text(inp["capital_usd"], 1, PRICE_MAX), "capital_usd")
    c = inp["cost_bps"]
    need(type(c) is str and c != "" and c.strip(".") != "" and c.count(".") <= 1
         and all(ch in "0123456789." for ch in c) and Decimal(c) <= 1000, "cost_bps")
    need(inp["stress"] in ("1", "2"), "stress")
    need(is_int(inp["fill_seed"], 0, 2**32 - 1), "fill_seed")
    need(is_int(inp["price_precision"], 0, FIXED_PRECISION), "price_precision")
    need(is_int(inp["size_precision"], 0, FIXED_PRECISION), "size_precision")
    need(int_text(inp["volume"], 1, QUANTITY_MAX), "volume")
    need(is_int(inp["n_bars"], 1, 100000), "n_bars")
    need(is_hex(inp["bars_sha256"], 64), "bars_sha256 format")
    need(is_hex(inp["ledger_hash_after_registration"], 32), "ledger_hash_after_registration format")
    need(hashlib.sha256(bars_bytes).hexdigest() == inp["bars_sha256"], "bars_sha256 differs from bars.csv")
    try:
        text = bars_bytes.decode("utf-8")
    except ValueError:
        raise Refused("bars.csv is not UTF-8")
    need("\r" not in text and text.endswith("\n"), "bars.csv line ends")
    lines = text.split("\n")[:-1]
    need(lines[0] == "i,ts_ns,close", "bars.csv header")
    need(len(lines) - 1 == inp["n_bars"], "n_bars differs from bars.csv")
    p, closes, ts = inp["price_precision"], [], []
    for k, line in enumerate(lines[1:]):
        f = line.split(",")
        need(len(f) == 3 and f[0] == str(k) and int_text(f[1], 1, 2**63 - 1), f"bars.csv row {k}")
        whole, dot, frac = f[2].partition(".")
        need(whole.isascii() and whole.isdigit() and (len(frac) == p and frac.isascii() and frac.isdigit()
                                                      if p else dot == "") and Decimal(f[2]) > 0, f"close {k}")
        closes.append(f[2])
        ts.append(int(f[1]))
    need(all(b > a for a, b in zip(ts, ts[1:])), "timestamps not strictly increasing")
    return closes, ts
def make_instrument(inp):                           # 5.2.3: rows SPY and BTC/USD -> (instrument, base, balances)
    p, sp = inp["price_precision"], inp["size_precision"]
    if inp["instrument"] == "SPY":
        inst = Equity(instrument_id=InstrumentId(Symbol("SPY"), VENUE), raw_symbol=Symbol("SPY"), currency=USD,
                      price_precision=p, price_increment=Price(Decimal(1).scaleb(-p), p),
                      lot_size=Quantity.from_int(1), ts_event=0, ts_init=0, maker_fee=Decimal(0), taker_fee=Decimal(0))
        return inst, USD, [Money(int(inp["capital_usd"]), USD)]
    inst = CurrencyPair(instrument_id=InstrumentId(Symbol("BTC/USD"), VENUE), raw_symbol=Symbol("BTC/USD"),
                        base_currency=BTC, quote_currency=USD, price_precision=p, size_precision=sp,
                        price_increment=Price(Decimal(1).scaleb(-p), p),
                        size_increment=Quantity(Decimal(1).scaleb(-sp), sp), ts_event=0, ts_init=0,
                        maker_fee=Decimal(0), taker_fee=Decimal(0))
    return inst, None, [Money(int(inp["capital_usd"]), USD), Money(0, BTC)]
def write_csv(root, name, header, rows):            # 5.2.6: UTF-8, LF; returns the file's SHA-256
    with inside(root, name).open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    return hashlib.sha256(inside(root, name).read_bytes()).hexdigest()
def write_outputs(root, port):                      # 5.2.6's three CSV files -> {name: SHA-256}
    return {
        "fills.csv": write_csv(root, "fills.csv", ["ts_event", "order_side", "last_qty", "last_px", "commission",
                                                   "commission_ccy", "trade_id", "venue_order_id"], port.fills),
        "decisions.csv": write_csv(root, "decisions.csv", ["i", "ts_event", "decision", "margin", "action"],
                                   port.decisions),
        "onbar_equity.csv": write_csv(root, "onbar_equity.csv", ["i", "ts_event", "close", "cash", "qty",
                                                                 "equity_pre"], port.equity)}
def child_reasons(port, result, not_filled, n_bars, last_ts):   # 5.2.7: every reason starts with its id
    reasons = list(port.invalid_reasons)
    if is_backtest_force_stop():
        reasons.append("C-01: forced stop")
    if port.i + 1 < n_bars or result.backtest_end is None or result.backtest_end < last_ts:
        reasons.append("C-02: bars seen fewer than bars fed")
    if not_filled:
        reasons.append(f"C-03: {len(not_filled)} order(s) not FILLED")
    if port.denied or port.rejected:
        reasons.append(f"C-04: {port.denied} order(s) denied, {port.rejected} rejected")
    if not port.strategy_started:
        reasons.append("C-15: the strategy did not start")
    return reasons
def run(root):                                      # exit 0, 10 or 20 (5.2.1)
    raw = inside(root, "input.json").read_bytes()
    try:
        inp = json.loads(raw.decode("utf-8"))
    except ValueError:
        raise Refused("input.json is not UTF-8 JSON")
    closes, ts = check_input(inp, inside(root, "bars.csv").read_bytes())
    inst, base, balances = make_instrument(inp)
    bar_type = BarType.from_str(f"{inst.id}-1-DAY-LAST-EXTERNAL")
    bars = [Bar(bar_type, Price.from_str(c), Price.from_str(c), Price.from_str(c), Price.from_str(c),
                Quantity(Decimal(inp["volume"]), inp["size_precision"]), t, t) for c, t in zip(closes, ts)]
    engine = build_engine()
    engine.add_venue(venue=VENUE, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=base,
                     starting_balances=balances,
                     fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=inp["fill_seed"]),
                     fee_model=make_fee_model(inp["cost_bps"], inp["stress"]), bar_execution=True,
                     bar_adaptive_high_low_ordering=False, allow_cash_borrowing=False)
    engine.add_instrument(inst)
    engine.add_data(bars)
    common = dict(instrument_id=str(inst.id), bar_type=str(bar_type), cost_bps=inp["cost_bps"],
                  stress=inp["stress"], closes=closes, ts=ts)
    if inp["strategy"] == "trend_switch":
        port = TrendSwitchPort(TrendSwitchConfig(**common, **inp["params"]))
    else:
        port = CryptoTrendPort(CryptoTrendConfig(**common, **inp["params"]))
    port.i, port.held, port.fills, port.decisions, port.equity, port.invalid_reasons = -1, 0, [], [], [], []
    port.denied = port.rejected = 0                 # on_start sets these again; a start that raised keeps them
    port.strategy_started = False
    engine.add_strategy(port)
    engine.run()
    result, orders = engine.get_result(), engine.cache.orders()
    not_filled = sorted(str(o.client_order_id) for o in orders if o.status.name != "FILLED")
    reasons = child_reasons(port, result, not_filled, len(bars), ts[-1])
    hashes = write_outputs(root, port)
    u, balance = platform.uname(), engine.portfolio.account(VENUE).balance_total(USD)
    manifest = {
        "schema": "nautilus-bridge-manifest/2", "read_only": True, "mode": "run",
        "python": platform.python_version(), "system": u.system, "machine": u.machine,
        "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                      "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX},
        "environment": engine.kernel.environment.name, "strategy_started": port.strategy_started,
        "input": {"input_json_sha256": hashlib.sha256(raw).hexdigest(), "bars_sha256": inp["bars_sha256"],
                  "bars_fed": len(bars), "first_ts": ts[0], "last_ts": ts[-1], "cost_bps": inp["cost_bps"],
                  "stress": inp["stress"], "ledger_hash_after_registration": inp["ledger_hash_after_registration"]},
        "engine": {"run_analysis": False, "log_level": "ERROR", "log_colors": False, "account_type": "CASH",
                   "oms_type": "NETTING", "allow_cash_borrowing": False, "bar_execution": True,
                   "fill_seed": inp["fill_seed"]},
        "result": {"bars_seen": port.i + 1, "iterations": result.iterations, "backtest_end": result.backtest_end,
                   "force_stop": is_backtest_force_stop(), "orders_total": len(orders),
                   "orders_filled": len(orders) - len(not_filled), "denied": port.denied,
                   "rejected": port.rejected, "orders_not_filled": not_filled,
                   "account_balance_usd": f"{balance.as_decimal():.2f}",
                   "final_qty": str(engine.portfolio.net_position(inst.id)),
                   "stats_pnls_empty": not result.stats_pnls},
        "hashes": hashes, "valid": not reasons, "invalid_reasons": reasons}
    inside(root, "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                             encoding="utf-8", newline="\n")
    engine.dispose()
    return 0 if not reasons else 10
def check_env():                                    # --check-env: one JSON line, no file (5.2.1)
    engine = build_engine()
    u = platform.uname()                            # not platform.system(): rule F6 flags any call named system
    print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                      "system": u.system, "machine": u.machine, "environment": engine.kernel.environment.name,
                      "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                                    "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX}}))
    engine.dispose()
    return 0
def guard_selftest():                               # --guard-selftest: exit 0, or 30 on a wrong outcome (5.2.1)
    out = {}
    env, clock = require_backtest_environment, require_backtest_clock
    for name, fn, arg in (("sandbox", env, Environment.SANDBOX), ("live", env, Environment.LIVE),
                          ("live_clock", clock, LiveClock()), ("backtest", env, Environment.BACKTEST),
                          ("test_clock", clock, TestClock())):
        try:
            fn(arg)
            out[name] = "passed"
        except RuntimeError:
            out[name] = "raised"
    print(json.dumps(out, sort_keys=True))
    return 0 if list(out.values()) == ["raised"] * 3 + ["passed"] * 2 else 30
def main():
    ap = argparse.ArgumentParser(prog="sandbox.py")
    ap.add_argument("--check-env", action="store_true"); ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv[1:])
    if a.check_env or a.guard_selftest:
        return check_env() if a.check_env else guard_selftest()
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute() or root != root.resolve():
        ap.exit(20, "C-05: run needs --in <an absolute directory equal to its own resolve()>\n")
    try:
        return run(root)
    except Refused as exc:                          # C-05: stderr only, no file (section 7)
        ap.exit(20, f"C-05: input refused: {exc}\n")
if __name__ == "__main__":                          # SECURITY-R3-1: __name__ is a Name, not an Attribute (F3)
    exit(main())
```
  Checks:
  - `wc -l tools/nautilus/sandbox.py` prints `344 tools/nautilus/sandbox.py`.
  - `sha256sum tools/nautilus/sandbox.py` prints `979cf7cdc4b537eb791680f92d66bbbaa3fd007d89461254ce04b50e58939a29  tools/nautilus/sandbox.py`.
  - Only `run` and `main` of Task 1's definitions changed: `python3 -B -c "import ast, subprocess; old = subprocess.run(['git', 'show', 'HEAD:tools/nautilus/sandbox.py'], capture_output=True, encoding='utf-8', errors='replace').stdout; new = open('tools/nautilus/sandbox.py', encoding='utf-8').read(); seg = lambda src: {n.name: ast.get_source_segment(src, n) for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}; o, n = seg(old), seg(new); print(sorted(k for k in o if o[k] != n.get(k)))"` prints `['main', 'run']`.

- [ ] **Step 7: Run the new tests and watch them pass.**
  - Key unset: `python3 -B -m tests.nautilus_acceptance -k test_px_fixture_inputs -k test_px_sandbox_avoids -k test_l2_04 -k test_l2_05`. Expected, exit 0: the three `NOT_RUN test_l2_0... OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)` lines of Step 3, then `PASS test_px_fixture_inputs_follow_6_1_and_8_2`, `PASS test_px_sandbox_avoids_excluded_constructs` and `2/5 passed, 0 failed, 3 not run`.
  - Key set (about 1 min 45 s): `QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_px_fixture_inputs -k test_px_sandbox_avoids -k test_l2_04 -k test_l2_05`. Expected, exit 0:
```
PASS test_l2_04_fills_identical_across_processes
  77 perturbations refused with exit 20
PASS test_l2_05a_refusals_exit_20_before_the_engine
PASS test_l2_05b_input_linked_to_env_refused
PASS test_px_fixture_inputs_follow_6_1_and_8_2
PASS test_px_sandbox_avoids_excluded_constructs

5/5 passed, 0 failed, 0 not run
```

- [ ] **Step 8: Run N1 once by hand.** This is not a test; Task 4's L2-3 pins N1 against its golden.
```bash
python3 -B -c "
import json, sys
from pathlib import Path
from tools.nautilus import launch
raw, bars = launch.fixture_inputs('N1')
tmp = launch.make_tempdir()
try:
    (tmp / 'input.json').write_bytes(raw)
    (tmp / 'bars.csv').write_bytes(bars)
    r = launch.run_child(launch.build_launch(['run', '--in', str(tmp)], tempdir=tmp, venv_python=Path(sys.argv[1]), unshare=launch.resolve_unshare()))
    m = json.loads((tmp / 'manifest.json').read_text(encoding='utf-8'))
    res = m['result']
    print(r.returncode, res['bars_seen'], res['force_stop'], res['account_balance_usd'], res['final_qty'], m['invalid_reasons'])
    print((tmp / 'fills.csv').read_text(encoding='utf-8').splitlines()[1:])
finally:
    print(launch.cleanup_tempdir(tmp))
" "$NTPY"
```
  Expected, exactly (8.2's N1, spec :1342):
```
10 4 True 904501.00 1000 ['C-01: forced stop', 'C-02: bars seen fewer than bars fed']
['978728400000000000,BUY,1000,100.00,500.00,USD,T-474e28fcce475f55-005,SIM-1-001']
[]
```

- [ ] **Step 9: Run the whole module and the guards.**
  - `python3 -B -m tests.nautilus_acceptance` ends `11/18 passed, 0 failed, 7 not run`: the seven layer-2 tests are NOT_RUN, which is spec Step 5's "layer-2 tests report NotRun without the venv".
  - `QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance` (about 1 min 50 s) ends `18/18 passed, 0 failed, 0 not run`. So L2-1, L2-4, L2-5a, L2-5b and L2-8 to L2-10 pass under `unshare -rn` (spec Step 5 done-when, spec :1476).
  - T-RO-01: `python3 -B -m tests.macro_m0_harness` shows `PASS test_t_ro_01_nautilus_allowlist_pinned` and `PASS test_t_ro_01_nautilus_confined_to_the_sandbox`, and ends `14/14 passed, 0 failed, 0 not run`. The real sandbox, now with its one order call, gives no hit.
  - test_08 and test_09: `python3 -B -c "from tests.acceptance import test_08_no_broker_order_path as a, test_09_no_account_credentials_requested as b; a(); b(); print('test_08 test_09 ok')"` prints `test_08 test_09 ok`. The flet guard reads `ui/*.py` only, so it is not run.
  - No CRLF file is touched: `git diff --name-only` lists `tests/nautilus_acceptance.py`, `tools/nautilus/launch.py` and `tools/nautilus/sandbox.py`, plus only paths Step 1 already showed as modified. It lists none of `tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml` or `config.py`.
  - `md5sum qa/acceptance_results.json` still prints `16c9baa5a1777853521d485d5078e456`.

- [ ] **Step 10: Check the counts through the wrapper (Count Ledger, as deltas).** Nothing else from QUANTGEN runs meanwhile (spec 3.8). The file names are the Plan rules' Result files: `$S/task3_full.json`, `$S/task3_nautilus.json` and `$S/task3_nautilus_key.json`; the comparison reads Task 2's `$S/nb_task2_full.json`.
  - `python3 -B $S/run_baseline.py $S/task3_nautilus.json --suite nautilus` ends `11/18 passed, 0 failed, 7 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/task3_nautilus.json`.
  - `QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B $S/run_baseline.py $S/task3_nautilus_key.json --suite nautilus` ends `18/18 passed, 0 failed, 0 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/task3_nautilus_key.json`.
  - The full run, key unset, in the background (about 10 minutes): `python3 -B $S/run_baseline.py $S/task3_full.json`.
    - With Task 1 Step 0's baseline `B` = `<P>/<N> passed, <F> failed, <R> not run` (N rows, R NOT_RUN; Count Ledger), this run's summary is `<P+13>/<N+20> passed, <F> failed, <R+7> not run`.
    - Task 3's own delta over Task 2's run is +5 rows: +2 PASS, +3 NOT_RUN.
    - Reference example only, from the 2026-10-26 baseline (870 rows, 745 PASS, 1 FAIL, 124 NOT_RUN): `758/890 passed, 1 failed, 131 not run`.
    - Its FAIL rows are exactly Task 1 Step 0's (2026-10-26: `papers/test_debate_run_kills_process_tree`).
  - Compare with Task 2's full run: `python3 -B -c "import json, sys; old = {r['test']: r['status'] for r in json.load(open(sys.argv[1], encoding='utf-8'))}; new = {r['test']: r['status'] for r in json.load(open(sys.argv[2], encoding='utf-8'))}; print('added', sorted((k, new[k]) for k in new.keys() - old.keys())); print('removed', sorted(old.keys() - new.keys())); print('changed', sorted((k, old[k], new[k]) for k in old.keys() & new.keys() if old[k] != new[k]))" "$S/nb_task2_full.json" "$S/task3_full.json"`. Expected:
```
added [('nautilus/test_l2_04_fills_identical_across_processes', 'NOT_RUN'), ('nautilus/test_l2_05a_refusals_exit_20_before_the_engine', 'NOT_RUN'), ('nautilus/test_l2_05b_input_linked_to_env_refused', 'NOT_RUN'), ('nautilus/test_px_fixture_inputs_follow_6_1_and_8_2', 'PASS'), ('nautilus/test_px_sandbox_avoids_excluded_constructs', 'PASS')]
removed []
changed []
```
  - `md5sum qa/acceptance_results.json` prints `16c9baa5a1777853521d485d5078e456` before and after each run.

- [ ] **Step 11: Commit.** `git status --short` shows exactly Step 1's lines plus the three below. This task leaves no `??` path: no stray manifest, CSV or temp dir in the repo.
```
 M tests/nautilus_acceptance.py
 M tools/nautilus/launch.py
 M tools/nautilus/sandbox.py
```
  Then:
```bash
git add tools/nautilus/sandbox.py tools/nautilus/launch.py tests/nautilus_acceptance.py
git commit -F - <<'EOF'
nautilus bridge Task 3 (spec Step 5): the sandbox in full and fixture_inputs

tools/nautilus/sandbox.py: spec 5.2 in the structure of 5.2.9. Frozen
StrategyConfig subclasses and the trend and crypto ports (clock guard
first in on_start, plain_mean, fee-inclusive Decimal sizing, the one
order call in Port.place); every input rule of 6.1 refused with exit 20
and a C-05 line on stderr; the CASH, NETTING SIM venue with
FillModel(1.0, 0.0, seed), the fee closure and bar execution; the four
files of 5.2.6 and the manifest of 6.2; the checks of 5.2.7 as C-nn
reasons with exit 10. tools/nautilus/launch.py: FIXTURES and
fixture_inputs for F1, F1r, F2 and N1 (8.2). tests/nautilus_acceptance.py:
test_px_fixture_inputs_follow_6_1_and_8_2,
test_px_sandbox_avoids_excluded_constructs, L2-4, L2-5a and L2-5b.
qa/acceptance_results.json is unchanged.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
EOF
git show --stat HEAD
```
  Expected `git show --stat HEAD`: `3 files changed`. `tests/nautilus_acceptance.py` has 468 insertions and `tools/nautilus/launch.py` 51, neither with a deletion. `tools/nautilus/sandbox.py` has 247 insertions and 8 deletions, measured against Task 1's draft text; the figures differ if Task 1's docstring or stub differ. Do not push. `qa/acceptance_results.json` is not staged and keeps its md5.

---

### Task 4: Runner (spec Step 6): section 5.3, the stub child, goldens and the Linux census baseline

**Verified before writing (2026-10-28, at HEAD `fa28059`; Task 4 was built and run in the scratch clones `$S/plan_step2/task4/clone` and `$S/plan_step2/task4/red`, which carry Tasks 1 to 3 as drafted in `$S/plan_step2/task1/final`, `task2` and `task3`; the real clone was not touched):**
- Starting state (the clone carried an earlier draft of Task 3: its sandbox lacked this plan's `write_outputs` refactor, with the same behaviour, and its test block had the same five test names but lacked `ORDER_CALL` and `_check_env_precision` and had `_refused_before_engine(label, result, out)`; no Task 4 line uses any of those names): with Tasks 1 to 3 applied, `python3 -B -m tests.nautilus_acceptance` gave `11/18 passed, 0 failed, 7 not run` (Task 3's Count Ledger row). Every RED and GREEN output below is the observed one, with the real clone's paths substituted.
- `core/quant/gate_ledger.py`: `repo_anchor` `:122-131` returns UNVERSIONED when `.git` is a file (worktree) or the branch ref is packed (both measured with git 2.43.0); `config_id` `:168-171`; `verify_chain` `:284-309`; `rows` `:311-316` raises `LedgerRefused` on a broken chain; `hash` `:318-321`; `n_raw` `:332-334`; `append` `:337-355` returns `RegisterResult(row, appended, row_md5)`, whose third element is `r["row_md5"]` for a duplicate (`:346`) but the md5 of the appended line (the next row's `prev_row_md5`) for an append (`:355`); `ledger_hash` `:371-372`; `family_ledger` `:375-376`; `register_trial` `:379-386`; `_exclusive` uses `fcntl.flock`/`msvcrt.locking` (`:242-262`), the pattern `take_lock` copies with the non-blocking flags.
- `core/quant/strategies.py`: `simulate` `:69-90`, `trend_switch` `:162-187`, `crypto_trend` `:330-348`, `pnl_matrix` `:379-389`, `grid_from` `:392-398`, which expands its keywords in their order. `core/quant/validate.py`: `GATE["bootstrap_B"]` 2000 (`:53-54`); `cost_floor_bp` (`:115-121`) gives `(50.0, {'SPY': 'us'})`, `(None, {'VOD.L': None})`, `(10.0, {'BTC-USD': 'crypto'})`. `core/quant/gate_package.py:36-38` `HARNESS_SOURCES`; importing that module takes 1.1 s, so `code_paths` imports it lazily.
- `docs/asset_expansion_study.py`: its import (`:41-58`) inserts the repo root into `sys.path`, reconfigures stdout and `mkdir(exist_ok=True)`s existing folders; loading it by path took 1.3 s and left `git status` empty. `_cached` `:68-79` reads `CACHE / "yf_<symbol>.csv"` (`=`, `^`, `:`, `/` replaced); `fred` `:94-104`; `panel` `:138-145`; `rf_daily` `:148-153` catches every exception and returns 0.03/252, so a blocked `fred` download shows up as an rf mismatch (R-13), which L1-20a uses; the pilot-1 grid is `grid_from(rule=..., lookback=..., step=...)` at `:274` (rule-major); `REFRESH = False` at `:844`.
- `ui/strategy_lab_page.py`: `FAMILY_ID` `:50`, `register_trials` `:55-77` with the params expression `:75-76`; importing it imports flet (2.2 s, present in the container). `config.py:32-39` (`_clean`), `:176-178` (`macro_dir`).
- Task 1's draft `launch.run_child` calls `on_started()` with no argument (C2), so the runner calls the `child_started` hook as `lambda: hook(lc)`. Task 1 also defines `launch.VENV_FIX` and `launch.PARENT_NAUTILUS_REMEDY`, which the runner prints as R-03 remedies, and the test helpers `_refused` and `_invalid` (CONTRACT ISSUE 5).
- Through the Task 3 sandbox and the exact launch contract, `--fixtures` measured F1 exit 0, F2 exit 0, N1 exit 10, each with a 942-name census (508 TP, 243 STD, 191 NT; no `nautilus_trader.adapters` or `.network` module); N1 is spec 8.2's row exactly (BUY 1000 @ `100.00`, 500.00, account 904501.00, `final_qty` `1000`, 4 of 12 bars, force stop, C-01 and C-02); F1 and F2 `final_qty` `0`. A real-venv rehearsal through the runner (synthetic 1,500 bars, 4 columns) gave valid children, a census equal to the baseline, and a minimum correlation of 0.99999905 between the rebuilt R and QUANTGEN's pnl at 2x.
- The container: `/usr/bin/unshare -rn true` exits 0; under it the probe gets errno 101; the parent itself reaches 1.1.1.1:443, so `--egress-record` exits 0 here.
- `float(f"{y:.9f}") == y` held for every `np.round(x, 9)` tried (the synthetic series and 200,000 random values in [1e6, 1e8]); R-05's round-trip refusal is therefore tested on the pure `check_round_trip` with `0.1 + 0.2`.
- A registration table written with `sort_keys=True` reorders `axes` and so the grid: pilot 1's rule-major grid is then refused R-11 (measured) (CONTRACT ISSUE 1).
- Readings of the spec, without a contract change: of-record asserts the pilot values (6.6, "of-record asserts"); both modes require `price_precision` 9 (5.3.2 step 5 rounds to 9 decimals) and 6.1's child ranges; a rehearsal `rf_file` lies inside the temp root or is exactly `docs/asset_expansion/cache/fred_DGS3MO.csv` (3.9, "DGS3MO is allowed only as the cash series"); of-record with a seam, `--ledger-dir` or `--out-dir` is R-11 and rehearsal directories outside the temp root are R-10 (5.3.1); at of-record step 1 a broken family ledger is R-09 and a missing or empty one R-15; any exception before registration prints its traceback tail and `STATUS REFUSED exit=2` (5.3.5); the non-run modes end `STATUS OK` or `STATUS REFUSED`.
- `tests/macro_m0_harness.py` with Task 2's amendment gives no hit on `runner.py` (`14/14 passed`); `tests/` is not scanned, and the new test code and stub carry no T-RO-01 token either. test_08 and test_09 read `runtime_py()` only (`tests/acceptance.py:50-75`), which Task 4 does not touch; no `ui/` file changes, so the flet guard is not concerned.
- Timing: the module without the key took 17 s; with the key 2 min 2 s (the 3 new layer-2 tests about 25 s).

**Files:**
- Create: `tools/nautilus/runner.py` (LF), `tests/nautilus_stub_child.py` (LF, standard library only).
- Create by running the runner (LF, C1's JSON bytes): `tools/nautilus/golden/F1.json`, `F2.json`, `N1.json` (Step 5, `--fixtures --write-goldens`), `tools/nautilus/golden/modules_manylinux_2_35_x86_64.json` (Step 6, `--fixtures --record-baseline`).
- Modify: `tests/nautilus_acceptance.py` (LF): the Task 4 block, inserted immediately above the `# CLI` banner.
- Test: `tests/nautilus_acceptance.py`, 21 layer-1 and 3 layer-2 tests (Test inventory, Task 4).
- Not touched: `tools/nautilus/launch.py`, `tools/nautilus/sandbox.py`, `tests/run_all.py`, `README.md`, `tests/macro_m0_harness.py`, `tests/macro_registry.csv`, `requirements*.txt`, `pyproject.toml`, `config.py`, `qa/acceptance_results.json`.

**Interfaces:**
- Consumes: C1 (`BridgeRefusal`, `ChildInvalid`, the JSON-bytes rule, `launch.host_tag()`); C2 (`REPO_ROOT`, `SANDBOX`, `EGRESS_PROBE`, `GOLDEN_DIR`, `TIMEOUT_S`, `TAIL_CHARS`, `venv_key`, `resolve_venv_python`, `read_venv`, `venv_mismatches`, `expected_versions`, `parent_nautilus`, `parent_pyarrow`, `make_tempdir`, `resolve_unshare`, `build_launch`, `run_child`, `parse_census`, `cleanup_tempdir`, `fixture_inputs`), with Task 1's `VENV_FIX` and `PARENT_NAUTILUS_REMEDY`; C3 and C6 (the sandbox's modes, exit codes, output files and manifest); C4 (the probe's one JSON line); C8's Task 1 block (`ROOT`, `guarded`, `layer2`, `tests`) and Task 1's `_refused`, `_invalid` (CONTRACT ISSUE 5); `gate_ledger`, `validate`, `strategies`, `gate_package.HARNESS_SOURCES`, `config.macro_dir`, `ui.strategy_lab_page.register_trials` (read-only).
- Produces: C5 (`input_bytes` writes it); C7 (the three goldens and the Linux census baseline); C8's Task 4 additions (`STUB`, `stub_python`, `stub_cmd`, `stub_probe_cmd`, `synth_prices`, `synth_rf`, `write_rehearsal_table` (written without `sort_keys`, CONTRACT ISSUE 1), `run_rehearsal`); C9 (the stub child); C10's Task 4 part: the CLI, exit codes and STATUS line, `STATUSES`, `main`, `run`, `table_sha256`, `code_sha256`, `host_fingerprint`, `bridge_run_id`, `TableLock`, `take_lock`, `check_table`, `check_tree`, `tree_refusal`, `check_egress_record`, `check_p0a` (CONTRACT ISSUE 2), `judge_census`, `record_baseline` (CONTRACT ISSUE 3), `write_record`, `parse_fills`, `parse_decisions`, `parse_equity`, `Rebuilt`, `rebuild_returns`, `Leg`, `RunContext`, `Outcome`, `parity_and_gate` (body exactly C10's `raise NotImplementedError(...)`); C12's run record (6.3) and ledger row (6.4), and the reading of earlier E1 records' `parity.hard_pass` (CONTRACT ISSUE 4).
- Produces, beyond the contract: in `runner.py` the constants (`PINNED_REAL_MD5`, `LAYER`, `REMEDY`, `SCRIPT`, `PRICE_DECIMALS`, `FRESH_S`, `PILOTS`, `PILOT_VALUES`, `SHAPES`, `TABLE_TYPES`, `GOLDEN_FIXTURES`) and `refuse`, `temp_roots`, `inside_temp_root`, `code_paths`, `code_digest`, `load_table`, `e1_parity_passed`, `venv_python_from_key`, `launch_once`, `check_venv`, `run_probe`, `control_connect`, `Prices`, `bar_timestamps`, `check_round_trip`, `load_prices`, `load_rf`, `load_study`, `check_cost`, `check_gate`, `ledger_row`, `registration_entry`, `census_class`, `census_diff`, `load_baseline`, `reconcile`, `manifest_reasons`, `child_params`, `cost_text`, `bars_bytes`, `input_bytes`, `utc_date`, `golden_of`, `compare_golden`, `run_fixture`, `fixtures_mode`, `check_env_mode`, `egress_record_mode`; in the tests `GOLDEN_DIR`, `ONE_SMA`, `REHEARSAL_LIKE`, `SPEC_FILLS`, `SPEC_R`, `SPEC_PNL`, `GOLDEN_SPEC`, `_runner`, `_bdates`, `_md5`, `_write_prices`, `_write_rf`, `_small_table`, `_captured`, `_step_hooks`, `_plain_row`, `_code_root`, `_of_record_table`, `_fixture_series`. Task 5 uses `RunContext`, `Leg`, `Outcome`, the rehearsal helpers, `GOLDEN_SPEC` and `REHEARSAL_LIKE`.

**Counts (Count Ledger as deltas from `B`, the full-suite baseline Task 1 Step 0 recorded in `$S/t1_baseline.json`).** Task 4 adds 24 `nautilus` rows: 21 layer 1 (PASS) and 3 layer 2 (NOT_RUN with the key unset). After Task 4 the `nautilus` suite is 42 rows: `32/42 passed, 0 failed, 10 not run` with the key unset, `42/42 passed, 0 failed, 0 not run` with `QUANTGEN_NAUTILUS_PYTHON="$NTPY"` (absolute: the suite started at 0). The full suite through the wrapper is `B` plus Tasks 2 to 4: +44 rows, +34 PASS, +10 NOT_RUN, the FAIL count and FAIL set of `B` unchanged; `macro` stays `M + 2` (Task 2). `python3 -B -m tests.macro_m0_harness` stays `14/14 passed, 0 failed, 0 not run`. Reference example only: from 2026-10-26's `B` = `745/870 passed, 1 failed, 124 not run`, this is the ledger's `779/914 passed, 1 failed, 134 not run`.

Every command block below starts with the line `S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen`.

- [ ] **Step 1: Confirm the starting point (Task 3 committed).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git log -1 --format='%h %s'; git status --short; md5sum qa/acceptance_results.json
ls tools/nautilus tools/nautilus/golden
python3 -B -m tests.nautilus_acceptance 2>/dev/null | tail -1
```
  Expected: Task 3's commit at HEAD; `git status --short` shows only the paths Task 1 Step 0 recorded as pre-existing; `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`; `__init__.py egress_probe.py golden launch.py sandbox.py` and `env_pins.json`; `11/18 passed, 0 failed, 7 not run`.

- [ ] **Step 2: Write the failing tests (RED).** With the Edit tool, insert this block into `tests/nautilus_acceptance.py` immediately above the three-line `# CLI` banner that precedes `def main(argv: list[str] | None = None) -> int:`, followed by two blank lines (old_string: the banner and the `def main` line; new_string: the block, two blank lines, the same old_string). The module already imports everything the block uses at module level (`contextlib`, `hashlib`, `io`, `json`, `os`, `shutil`, `subprocess`, `sys`, `tempfile`, `time`, `Path`, `PureWindowsPath`, `Callable`, `Sequence`, `NotRun`, `launch`); numpy, pandas and QUANTGEN modules are imported inside the functions, and the runner through `_runner()`, so a missing runner fails only Task 4's tests.
```python
# --------------------------------------------------------------------------- #
# Plan Task 4 (spec Step 6): the runner, the stub child, goldens and the census baseline
# --------------------------------------------------------------------------- #
STUB = ROOT / "tests" / "nautilus_stub_child.py"
GOLDEN_DIR = ROOT / "tools" / "nautilus" / "golden"
ONE_SMA = {"rule": ["sma"], "lookback": [126], "step": [21]}            # a one-column grid: two children
REHEARSAL_LIKE = {                                                       # the fields of 10.1 and 10.2 a table copies
    "E1-SPY": {"family_id": "E1", "rule": "E1", "market": "US", "strategy": "trend_switch", "symbol": "SPY",
               "instrument": "SPY", "axes": {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]},
               "cost_bps": 50.0, "embargo": 21, "size_precision": 0, "domain": None, "card_id": "NB_E1_trend_spy",
               "claim_label": "pre-specified on historical data; the SPY series was used inside S_E1_trend_us with "
                              "the same 12-setting grid; not confirmatory"},
    "C3-BTCUSD": {"family_id": "C3", "rule": "C3", "market": "CRYPTO", "strategy": "crypto_trend",
                  "symbol": "BTC-USD", "instrument": "BTC/USD", "axes": {"hysteresis": [0.0, 0.222, 0.444, 0.667, 0.889]},
                  "cost_bps": 10.0, "embargo": 1, "size_precision": 8, "domain": {"hysteresis": [0.0, 0.889]},
                  "card_id": "NB_C3_crypto_trend_btcusd",
                  "claim_label": "pre-specified on historical data, engine replication: stored card "
                                 "S_C3_crypto_trend_btcusd on the same file and configurations, grid revised on "
                                 "this file; not new evidence about the rule"}}
SPEC_FILLS = {   # spec 8.2: (bar, side, last_qty, last_px, commission) of F1 and F2
    "F1": ((3, "BUY", "10000", "100.000000000", "5000.00"), (5, "SELL", "10000", "96.000000000", "4800.00"),
           (7, "BUY", "9600", "99.000000000", "4752.00"), (11, "SELL", "9600", "97.000000000", "4656.00")),
    "F2": ((3, "BUY", "1.00000000", "53000.000000000", "53.00"), (5, "SELL", "1.00000000", "50000.000000000", "50.00"),
           (7, "BUY", "0.98812079", "50500.000000000", "49.90"), (9, "SELL", "0.98812079", "51000.000000000", "50.39"))}
SPEC_R = {       # spec 8.2: Nautilus R (to 1e-7) and the QUANTGEN pnl of F1, F1r and F2
    "F1": (0, 0, 0, 0.0348258, -0.0769230, -0.0050000, 0, 0.0151256, 0.0198010, -0.0485413, -0.0102036),
    "F1r": (0.0001, 0.0001, 0.0001, 0.0348258, -0.0769230, -0.0049005, 0.0001, 0.0151256, 0.0198010, -0.0485413,
            -0.0102035),
    "F2": (0, 0, 0, -0.0085386, -0.0494297, -0.0010000, 0, 0.0286743, -0.0192308, -0.0009999)}
SPEC_PNL = {
    "F1": (0, 0, 0, 0.0350000, -0.0769231, -0.0050000, 0, 0.0152020, 0.0198020, -0.0485437, -0.0102041),
    "F1r": (0.0001, 0.0001, 0.0001, 0.0350000, -0.0769231, -0.0049000, 0.0001, 0.0152020, 0.0198020, -0.0485437,
            -0.0102041),
    "F2": (0, 0, 0, -0.0085472, -0.0494297, -0.0010000, 0, 0.0287030, -0.0192308, -0.0010000)}
GOLDEN_SPEC = {  # spec 8.2 and 6.8, typed in: prices at each fixture's precision, dates of ts_event in UTC
    "F1": {"schema": "nautilus-bridge-golden/1", "fixture": "F1", "status": "valid", "exit_code": 0, "bars_fed": 12,
           "bars_seen": 12, "force_stop": False,
           "fills": [{"date": "2001-01-05", "side": "BUY", "qty": "10000", "price": "100.000000000", "commission": "5000.00"},
                     {"date": "2001-01-09", "side": "SELL", "qty": "10000", "price": "96.000000000", "commission": "4800.00"},
                     {"date": "2001-01-11", "side": "BUY", "qty": "9600", "price": "99.000000000", "commission": "4752.00"},
                     {"date": "2001-01-17", "side": "SELL", "qty": "9600", "price": "97.000000000", "commission": "4656.00"}],
           "final_cash": "926593.00", "final_qty": "0", "invalid_reasons": []},
    "F2": {"schema": "nautilus-bridge-golden/1", "fixture": "F2", "status": "valid", "exit_code": 0, "bars_fed": 11,
           "bars_seen": 11, "force_stop": False,
           "fills": [{"date": "2021-01-05", "side": "BUY", "qty": "1.00000000", "price": "53000.000000000", "commission": "53.00"},
                     {"date": "2021-01-07", "side": "SELL", "qty": "1.00000000", "price": "50000.000000000", "commission": "50.00"},
                     {"date": "2021-01-09", "side": "BUY", "qty": "0.98812079", "price": "50500.000000000", "commission": "49.90"},
                     {"date": "2021-01-11", "side": "SELL", "qty": "0.98812079", "price": "51000.000000000", "commission": "50.39"}],
           "final_cash": "50343.77", "final_qty": "0", "invalid_reasons": []},
    "N1": {"schema": "nautilus-bridge-golden/1", "fixture": "N1", "status": "invalid", "exit_code": 10, "bars_fed": 12,
           "bars_seen": 4, "force_stop": True,
           "fills": [{"date": "2001-01-05", "side": "BUY", "qty": "1000", "price": "100.00", "commission": "500.00"}],
           "final_cash": "904501.00", "final_qty": "1000",
           "invalid_reasons": ["C-01: forced stop", "C-02: bars seen fewer than bars fed"]}}


def _runner():
    """tools.nautilus.runner, imported by each test that needs it, so a missing runner fails only Task 4's tests."""
    from tools.nautilus import runner
    return runner


def stub_python() -> str:
    """sys.executable, unless it lies under WindowsApps (the Store python) and the dedicated
    %LOCALAPPDATA%\\quantgen\\py313\\python.exe exists: then that file (8.1; QA-R3-10)."""
    py313 = Path(os.environ.get("LOCALAPPDATA") or "/nonexistent") / "quantgen" / "py313" / "python.exe"
    parts = [p.lower() for p in Path(os.path.normcase(os.path.realpath(sys.executable))).parts]
    return str(py313) if "windowsapps" in parts and py313.is_file() else sys.executable


def stub_cmd(*flags: str) -> list[str]:
    return [stub_python(), "-I", str(STUB), *flags]


def stub_probe_cmd() -> list[str]:
    return stub_cmd("--probe")


def synth_prices(seed, n, p0, p1, planted=()):                       # spec 8.2, verbatim
    import numpy as np
    lr = np.random.default_rng(seed).normal(0.0, np.where(np.arange(n) // 250 % 2 == 0, 0.008, 0.02))
    lr += (np.log(p1 / p0) - lr.sum()) / n                         # drift from about p0 to about p1
    for k, i in enumerate(planted):
        lr[i] = np.log(1.1 if k % 2 == 0 else 0.9)                 # planted +10 % and -10 % days
    return np.round(p0 * np.exp(np.cumsum(lr)), 9)


def synth_rf(n):                                                   # stepped: 0, 2, 5 and 1 % a year
    import numpy as np
    return np.repeat([0.0, 0.02, 0.05, 0.01], -(-n // 4))[:n] / 252


def _bdates(n: int) -> list[str]:
    """Spec 8.2's calendar: pd.bdate_range("2001-01-02", periods=n)."""
    import pandas as pd
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2001-01-02", periods=n)]


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _write_prices(path: Path, dates: Sequence[str], prices) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Date,Close\n" + "".join(f"{d},{p:.9f}\n" for d, p in zip(dates, prices)), encoding="utf-8",
                    newline="\n")
    return _md5(path)


def _write_rf(path: Path, dates: Sequence[str], rf) -> str:
    """A DGS3MO-shaped file: percent a year (rf * 252 * 100); a None value is a blank, as FRED leaves holidays."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "".join(f"{d},{'' if x is None else repr(float(x) * 252 * 100)}\n" for d, x in zip(dates, rf))
    path.write_text("DATE,DGS3MO\n" + rows, encoding="utf-8", newline="\n")
    return _md5(path)


def write_rehearsal_table(tmp: Path, *, like: str = "E1-SPY", prices, dates: Sequence[str], rf=None, **fields) -> Path:
    """The prices file, the DGS3MO-shaped file when rf is given, and <tmp>/table.json: a 6.6 table with pilot
    "rehearsal" and every other field from pilot `like` (10.1 or 10.2), study_configs [], no reference card, md5s
    computed, no owner field; `fields` override any key (a new `axes` without `grid` recomputes the grid). Written
    without sort_keys: the axes keys keep the study's call order, which fixes the grid's column order (CONTRACT ISSUE 1)."""
    from core.quant import strategies as S
    t = {"schema": "nautilus-bridge-table/1", "pilot": "rehearsal", **REHEARSAL_LIKE[like],
         "prices_file": str(tmp / "prices.csv"), "prices_md5": _write_prices(tmp / "prices.csv", dates, prices),
         "start": dates[0], "end": dates[-1], "rf_file": None, "rf_md5": None, "capital_usd": "1000000",
         "price_precision": 9, "volume": "1000000000", "fill_seed": 42,
         "hypothesis": "synthetic rehearsal: both engines give the same matrix", "study_configs": [],
         "reference_card": None, "reference_card_md5": None}
    if rf is not None:
        t.update(rf_file=str(tmp / "DGS3MO.csv"), rf_md5=_write_rf(tmp / "DGS3MO.csv", dates, rf))
    t.update(fields)
    t["grid"] = fields["grid"] if "grid" in fields else S.grid_from(**t["axes"])
    path = tmp / "table.json"
    path.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def run_rehearsal(table: Path, tmp: Path, *, flags: Sequence[str] = (), **run_kwargs) -> tuple[int, dict | None]:
    """runner.run in rehearsal mode with the stub child and the stub probe, ledger and outputs under tmp; returns
    the exit code and the newest run.json under tmp/out (None when no run folder holds one)."""
    code = _runner().run(table, mode="rehearsal", ledger_dir=tmp / "ledgers", out_dir=tmp / "out",
                         child_cmd=stub_cmd(*flags), probe_cmd=stub_probe_cmd(), **run_kwargs)
    runs = sorted((tmp / "out").glob("NB-*/run.json"))
    return code, (json.loads(runs[-1].read_text(encoding="utf-8")) if runs else None)


def _small_table(tmp: Path, *, n: int = 320, axes: dict | None = None, with_rf: bool = True, **fields) -> Path:
    """A synthetic SPY-like rehearsal table: synth_prices(7, n, 100, 150), synth_rf(n), one sma column by default."""
    return write_rehearsal_table(tmp, prices=synth_prices(7, n, 100.0, 150.0), dates=_bdates(n),
                                 rf=synth_rf(n) if with_rf else None, axes=axes or ONE_SMA, **fields)


def _captured(fn: Callable[[], object]) -> tuple[object, str]:
    """fn() with stdout captured: (its result, what it printed)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn()
    return out, buf.getvalue()


def _step_hooks(seen: list[int]) -> dict:
    """after_step0 .. after_step17, each appending its step number to `seen`."""
    return {f"after_step{n}": (lambda _ctx, n=n: seen.append(n)) for n in range(18)}


def _plain_row(rule: str, k: int) -> dict:
    return {"rule": rule, "params": {"k": k}, "timing_class": "COMPLIANT", "span": ["2001-01-02", "2002-03-01"],
            "market": "US", "run_utc": "2026-10-28T00:00:00Z", "phase": "research", "script": "tests/nautilus_acceptance.py"}


def _code_root(dst: Path) -> Path:
    """A temp copy of every file code_sha256 reads, so of-record checks run on a temp repository root."""
    for p in _runner().code_paths(ROOT):
        target = dst / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    return dst


def _of_record_table(path: Path, pilot: str, code: str, **fields) -> Path:
    """An of-record table under the system temp dir only (GOVERNANCE-R3-5), whose owner_confirmed quotes its own
    table_sha256 and `code`. It names the pilot's files; check_table never opens a data file."""
    from core.quant import strategies as S
    runner = _runner()
    e1 = pilot == "E1-SPY"
    t = {"schema": "nautilus-bridge-table/1", "pilot": pilot, **REHEARSAL_LIKE[pilot],
         "prices_file": "docs/asset_expansion/cache/" + ("yf_SPY.csv" if e1 else "yf_BTC-USD.csv"),
         "prices_md5": runner.PINNED_REAL_MD5["SPY" if e1 else "BTC-USD"],
         "start": "2004-12-01" if e1 else "2014-09-17", "end": "2026-09-25",
         "rf_file": "docs/asset_expansion/cache/fred_DGS3MO.csv" if e1 else None,
         "rf_md5": "661722143f24930a29b58c535d227c1b" if e1 else None, "capital_usd": "1000000", "price_precision": 9,
         "volume": "1000000000", "fill_seed": 42, "hypothesis": "of-record shape, temp only", "study_configs": [],
         "reference_card": None, "reference_card_md5": None, "host_fingerprint": "0" * 64}
    t.update(fields)
    t["grid"] = fields["grid"] if "grid" in fields else S.grid_from(**t["axes"])
    t.setdefault("owner_confirmed", f"Geon Koh, 2026-10-28, table {runner.table_sha256(t)[:16]}, code {code[:16]}")
    path.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def _fixture_series(name: str):
    """(capital, ts, closes) of an 8.2 fixture, from launch.fixture_inputs (C2)."""
    import numpy as np
    raw, bars = launch.fixture_inputs(name)
    rows = [r.split(",") for r in bars.decode("utf-8").splitlines()[1:]]
    return json.loads(raw)["capital_usd"], [int(r[1]) for r in rows], np.array([float(r[2]) for r in rows])


def test_l1_01_return_reconstruction_f1_f1r_f2():
    """L1-1 (5.3.3): R rebuilt from 8.2's fills matches 8.2's Nautilus R on F1, F1r and F2 to 1e-7, with the cash
    overlay on F1r; the final cash, the fill bars and TV (the bar T-1 fill dropped) follow; QUANTGEN's simulate gives
    8.2's pnl; a fill off every bar timestamp is C-09."""
    import numpy as np
    from decimal import Decimal
    from core.quant import strategies as S
    runner = _runner()
    rebuilt = {}
    for name in ("F1", "F1r", "F2"):
        capital, ts, closes = _fixture_series("F2" if name == "F2" else "F1")
        rf = np.full(len(ts), 0.0001 if name == "F1r" else 0.0)
        fills = [{"ts_event": ts[b], "order_side": side, "last_qty": Decimal(q), "last_px": Decimal(px),
                  "commission": Decimal(c), "commission_ccy": "USD", "trade_id": f"T{k}", "venue_order_id": f"O{k}"}
                 for k, (b, side, q, px, c) in enumerate(SPEC_FILLS["F2" if name == "F2" else "F1"])]
        rb = rebuilt[name] = runner.rebuild_returns(fills, closes, ts, rf, Decimal(capital))
        assert rb.R.shape == (len(ts) - 1,) and np.max(np.abs(rb.R - np.array(SPEC_R[name]))) <= 1e-7, (name, rb.R)
        assert rb.E_minus[0] == float(capital) and rb.fill_bars == [3, 5, 7, 9 if name == "F2" else 11], rb.fill_bars
        if name == "F2":
            W = S.crypto_trend(closes, lookbacks=(1, 2), mas=(2, 3), hysteresis=0.2)
            pnl, _ = S.simulate(closes, W, cost_bps=10.0, cash_daily=rf)
            assert rb.final_cash.quantize(Decimal("0.000001")) == Decimal("50343.770395"), rb.final_cash
            assert np.flatnonzero(rb.TV).tolist() == [3, 5, 7, 9], rb.TV
        else:
            W = S.trend_switch(closes, rule="sma", lookback=3, step=2)
            pnl, turnover = S.simulate(closes, W, cost_bps=50.0, cash_daily=rf)
            assert turnover.tolist() == [0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0], turnover
            assert rb.final_cash == Decimal("926593") and np.flatnonzero(rb.TV).tolist() == [3, 5, 7], rb.TV
            assert abs(rb.TV[3] - 1_000_000 / 1_005_001) < 1e-12, rb.TV[3]
        assert np.max(np.abs(pnl - np.array(SPEC_PNL[name]))) <= 1e-7, (name, pnl)
    moved = np.abs(rebuilt["F1r"].R - rebuilt["F1"].R)
    assert all(moved[t] < 1e-8 for t in (3, 4, 7, 8, 9)), moved
    capital, ts, closes = _fixture_series("F1")
    off = [{"ts_event": ts[3] + 1, "order_side": "BUY", "last_qty": Decimal(1), "last_px": Decimal(100),
            "commission": Decimal("0.50"), "commission_ccy": "USD", "trade_id": "T", "venue_order_id": "O"}]
    _invalid(lambda: runner.rebuild_returns(off, closes, ts, np.zeros(len(ts)), Decimal(capital)), "C-09")


def test_l1_03_children_start_after_registration():
    """L1-3 (QA-6, QA-R4-4, QA-R4-5): with the stub child, a child_started hook finds every config_id of the table in
    the temp ledger and input.json's ledger hash equal to family_ledger(...).hash(); no child exits 1; the record
    carries the post-registration hash, both data md5s and every child manifest echoing it."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l103_") as name:
        tmp = Path(name)
        table = _small_table(tmp, axes={"rule": ["sma", "tsmom"], "lookback": [126], "step": [21]})
        t = json.loads(table.read_text(encoding="utf-8"))
        expected = {gate_ledger.config_id({"rule": "E1", "params": dict(g, symbols=["SPY"], cost_bps=50.0),
                                           "timing_class": "COMPLIANT"}) for g in t["grid"]}
        seen = []

        def started(lc):
            ledger = gate_ledger.family_ledger("E1", tmp / "ledgers")
            rows = ledger.rows()
            inp = json.loads((Path(lc.cwd) / "input.json").read_text(encoding="utf-8"))
            seen.append(({r["config_id"] for r in rows}, inp["ledger_hash_after_registration"], ledger.hash(rows),
                         inp["stress"]))
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks={"child_started": started}))
        assert rec is not None and len(seen) == 4, out[-2000:]
        assert all(ids == expected and echoed == now for ids, echoed, now, _ in seen), seen
        assert [s for *_, s in seen] == ["1", "2", "1", "2"], seen
        assert [c["returncode"] for c in rec["children"]] == [0, 0, 0, 0], rec["children"]
        assert all(c["invalid"] == [] for c in rec["children"]), [c["invalid"] for c in rec["children"]]
        reg = rec["registration"]
        assert reg["hash_after"] == seen[0][1] and (reg["n_raw_before"], reg["n_raw_after"]) == (0, 2), reg
        assert {r["config_id"] for r in reg["rows"]} == expected and all(r["appended"] for r in reg["rows"]), reg
        assert all(c["manifest"]["input"]["ledger_hash_after_registration"] == reg["hash_after"]
                   for c in rec["children"])
        assert rec["times"]["registered_utc"] < rec["times"]["first_child_utc"], rec["times"]
        assert (rec["data"]["prices_md5"], rec["data"]["rf_md5"]) == (t["prices_md5"], t["rf_md5"]), rec["data"]
        assert rec["stub_child"] is True and rec["provenance"]["p0a"]["passed"] is True and rec["census"] == {}


def test_l1_04_broken_chain_stops_before_children():
    """L1-4 (R-09): a broken chain in the temp family ledger refuses at step 10, before registration and before any
    child; the ledger's bytes are unchanged and no run folder exists."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l104_") as name:
        tmp = Path(name)
        table = _small_table(tmp)
        ledger = gate_ledger.family_ledger("E1", tmp / "ledgers")
        gate_ledger.register_trial(ledger, _plain_row("E1", 1))
        ledger.path.write_bytes(ledger.path.read_bytes().replace(b'"US"', b'"KR"'))   # row_md5 no longer matches
        old = time.time() - 700
        os.utime(ledger.path, (old, old))                                               # not R-16's freshness
        before, steps, started = ledger.path.read_bytes(), [], []
        hooks = {**_step_hooks(steps), "child_started": started.append}
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks=hooks))
        assert (code, rec) == (2, None) and "R-09: " in out, out[-2000:]
        assert out.splitlines()[-1] == "STATUS REFUSED exit=2 record=-", out[-500:]
        assert steps == list(range(10)) and started == [], (steps, started)
        assert ledger.path.read_bytes() == before and not list((tmp / "out").glob("NB-*"))


def test_l1_06_tree_refusals_r01_r02():
    """L1-6 (5.3.2 step 2): check_tree and tree_refusal on a temp git repository: a modified tracked file and an
    untracked file outside docs/nautilus_bridge/runs/ refuse (R-01), an untracked file under runs/ passes, a worktree
    and packed refs refuse with their own messages (R-02), git missing is R-02; rehearsal returns None for each."""
    from core.quant import gate_ledger
    runner = _runner()
    git = shutil.which("git")
    if git is None:
        raise NotRun("OWNER: git not on PATH")
    with tempfile.TemporaryDirectory(prefix="qgnb_l106_") as name:
        tmp, repo = Path(name), Path(name) / "repo"

        def g(*args: str) -> str:
            out = subprocess.run([git, "-c", "user.name=qgnb", "-c", "user.email=qgnb@example.invalid", "-c",
                                  "commit.gpgsign=false", *args], cwd=repo, capture_output=True, encoding="utf-8",
                                 errors="replace", timeout=60)
            assert out.returncode == 0, (args, out.stderr)
            return out.stdout

        def judge(root: Path = repo):
            found = runner.check_tree(root, gate_ledger.repo_anchor, git)
            assert runner.tree_refusal(found, "rehearsal") is None, found
            return found, runner.tree_refusal(found, "of-record")
        repo.mkdir()
        g("init", "-q", "-b", "main")
        (repo / "a.txt").write_text("a\n", encoding="utf-8", newline="\n")
        g("add", "a.txt")
        g("commit", "-q", "-m", "a")
        found, rid = judge()
        assert rid is None and found["clean"] and found["anchor"] == f"git:{g('rev-parse', 'HEAD').strip()}", found
        runs = repo / "docs" / "nautilus_bridge" / "runs" / "NB-x"
        runs.mkdir(parents=True)
        (runs / "run.json").write_text("{}\n", encoding="utf-8", newline="\n")
        found, rid = judge()
        assert rid is None and found["porcelain_exempt"] == ["?? docs/nautilus_bridge/runs/NB-x/run.json"], found
        (repo / "a.txt").write_text("b\n", encoding="utf-8", newline="\n")
        found, rid = judge()
        assert rid == "R-01" and found["offending"] == [" M a.txt"], found
        g("checkout", "--", "a.txt")
        (repo / "b.txt").write_text("b\n", encoding="utf-8", newline="\n")
        found, rid = judge()
        assert rid == "R-01" and found["offending"] == ["?? b.txt"], found
        (repo / "b.txt").unlink()
        g("worktree", "add", "-q", str(tmp / "wt"))
        found, rid = judge(tmp / "wt")
        assert rid == "R-02" and "worktree" in found["anchor_problem"], found
        g("pack-refs", "--all")
        found, rid = judge()
        assert rid == "R-02" and "packed" in found["anchor_problem"], found
        assert 'git commit --allow-empty -m "nautilus: re-anchor"' in found["anchor_problem"], found
        found = runner.check_tree(repo, gate_ledger.repo_anchor, None)
        assert found["head"] is None and runner.tree_refusal(found, "of-record") == "R-02", found
        assert runner.tree_refusal(found, "rehearsal") is None


def test_l1_07_data_refusals_r04_r05_r06():
    """L1-7 (5.3.2 steps 5 and 6): R-04 (missing, unreadable, doctored md5), R-05 (N5's duplicated and swapped
    dates, under 300 rows, a close failing the round trip), R-06 (missing, doctored md5, a NaN before the first
    observation; no 3 % fallback, K8) on synthetic files; a blank DGS3MO value mid-series takes the prior value and
    P0a then passes (QUANT-R2-1); run() refuses R-04 and R-06 at their steps."""
    import numpy as np
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l107_") as name:
        tmp = Path(name)
        n, dates = 320, _bdates(320)
        prices = synth_prices(7, n, 100.0, 150.0)
        kw = {"start": dates[0], "end": dates[-1], "instrument": "SPY", "mode": "rehearsal"}
        good = _write_prices(tmp / "p.csv", dates, prices)
        p = runner.load_prices(tmp / "p.csv", md5=good, **kw)
        assert p.dates == tuple(dates) and p.closes.tobytes() == prices.tobytes() and not p.rounding_changed
        assert p.ts[:2] == [978469200 * 10**9, 978555600 * 10**9] and p.md5 == good, p.ts[:2]
        cut = runner.load_prices(tmp / "p.csv", md5=good, **dict(kw, start=dates[10], end=dates[-11]))
        assert cut.dates == tuple(dates[10:-10]), len(cut.dates)
        _refused(lambda: runner.load_prices(tmp / "missing.csv", md5=good, **kw), "R-04")
        _refused(lambda: runner.load_prices(tmp / "p.csv", md5="0" * 32, **kw), "R-04")
        (tmp / "bad.csv").write_bytes(b"\xff\xfe garbage")
        _refused(lambda: runner.load_prices(tmp / "bad.csv", md5=_md5(tmp / "bad.csv"), **kw), "R-04")
        for label, ds, ps in (("299 rows", dates[:299], prices[:299]),
                              ("duplicated", dates[:150] + [dates[149]] + dates[151:], prices),
                              ("swapped", dates[:150] + [dates[151], dates[150]] + dates[152:], prices)):
            md5 = _write_prices(tmp / f"{label}.csv", ds, ps)
            exc = _refused(lambda: runner.load_prices(tmp / f"{label}.csv", md5=md5, **kw), "R-05")
            assert ("300" in exc.message) == (label == "299 rows"), (label, exc)
        runner.check_round_trip(prices)
        _refused(lambda: runner.check_round_trip(np.array([100.0, 0.1 + 0.2])), "R-05")
        rf = synth_rf(n)
        rmd5 = _write_rf(tmp / "r.csv", dates, rf)
        got, data = runner.load_rf(tmp / "r.csv", md5=rmd5, dates=p.dates)
        assert data == (tmp / "r.csv").read_bytes() and np.max(np.abs(got - rf)) < 1e-15, np.max(np.abs(got - rf))
        _refused(lambda: runner.load_rf(tmp / "missing.csv", md5=rmd5, dates=p.dates), "R-06")
        _refused(lambda: runner.load_rf(tmp / "r.csv", md5="0" * 32, dates=p.dates), "R-06")
        late = _write_rf(tmp / "late.csv", dates[5:], rf[5:])
        _refused(lambda: runner.load_rf(tmp / "late.csv", md5=late, dates=p.dates), "R-06")
        blank = [None if k == 100 else x for k, x in enumerate(rf)]
        bmd5 = _write_rf(tmp / "blank.csv", dates, blank)
        got, _ = runner.load_rf(tmp / "blank.csv", md5=bmd5, dates=p.dates)
        assert got[100] == got[99] and not np.isnan(got).any(), got[98:102]
        for sub, fields, rid, upto in (("r04", {"prices_md5": "0" * 32}, "R-04", 4),
                                       ("r06", {"rf_md5": "0" * 32}, "R-06", 5)):
            steps = []
            table = _small_table(tmp / sub, **fields)
            (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / sub, hooks=_step_hooks(steps)))
            assert (code, rec) == (2, None) and f"{rid}: " in out and steps == list(range(upto + 1)), (rid, steps)
        steps = []
        table = _small_table(tmp / "blank", with_rf=False, rf_file=str(tmp / "blank.csv"), rf_md5=bmd5)

        def stop(_ctx):
            steps.append(7)
            raise RuntimeError("stop after P0a (planted)")
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "blank", hooks={"after_step7": stop}))
        assert (code, rec) == (2, None) and steps == [7] and "stop after P0a (planted)" in out, out[-2000:]
        assert not (tmp / "blank" / "ledgers" / "E1.jsonl").exists()


def test_l1_08_cost_refusals_r07():
    """L1-8 (K15): R-07 for an uncosted symbol (VOD.L) and for 40 bp on SPY; through run(), at step 8."""
    runner = _runner()
    exc = _refused(lambda: runner.check_cost("VOD.L", 50.0), "R-07")
    assert "VOD.L" in exc.message, exc
    exc = _refused(lambda: runner.check_cost("SPY", 40.0), "R-07")
    assert "below the floor 50" in exc.message, exc
    assert runner.check_cost("SPY", 50.0) == (50.0, {"SPY": "us"})
    assert runner.check_cost("BTC-USD", 10.0) == (10.0, {"BTC-USD": "crypto"})
    with tempfile.TemporaryDirectory(prefix="qgnb_l108_") as name:
        tmp, steps = Path(name), []
        table = _small_table(tmp, cost_bps=40.0)
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks=_step_hooks(steps)))
        assert (code, rec) == (2, None) and "R-07: cost_bps 40 is below the floor 50 bp for SPY" in out, out[-2000:]
        assert steps == list(range(8)) and not (tmp / "ledgers" / "E1.jsonl").exists(), steps


def test_l1_09_place_and_content_refusals_r10():
    """L1-9 (3.9; GOVERNANCE-R2-3, GOVERNANCE-R3-3, QA-R4-2): R-10 for a ledger or output dir outside the temp root
    (argument validation, nothing created); for a synthetic file whose md5 is planted as the pinned BTC md5, and one
    planted as the pinned SPY md5 with end 2004-11-30 (step 5); for a table naming a tracked file of
    docs/asset_expansion/cache/ with prices_md5 of 32 zeros, by check_table and by run() with no after_step1 hook,
    so the place is judged before any hash; for a reference card outside the temp root. No real file is read."""
    runner = _runner()
    locks = ROOT / "docs" / "nautilus_bridge" / "runs" / ".locks"
    had_locks = locks.exists()
    with tempfile.TemporaryDirectory(prefix="qgnb_l109_") as name:
        tmp = Path(name)
        table = _small_table(tmp / "a")
        outside = Path.home() / "qgnb_not_a_temp_dir"
        for kw in ({"ledger_dir": outside, "out_dir": tmp / "out"},
                   {"ledger_dir": tmp / "ledgers", "out_dir": ROOT / "docs" / "nautilus_bridge" / "runs"}):
            steps = []
            code, out = _captured(lambda: runner.run(table, mode="rehearsal", child_cmd=stub_cmd(),
                                                     probe_cmd=stub_probe_cmd(), hooks=_step_hooks(steps), **kw))
            assert code == 2 and "R-10: rehearsal needs --ledger-dir and --out-dir inside the temp root" in out, out
            assert steps == [], steps
        assert not outside.exists() and locks.exists() == had_locks
        md5 = json.loads(table.read_text(encoding="utf-8"))["prices_md5"]
        saved = dict(runner.PINNED_REAL_MD5)
        try:
            for symbol, sub, fields in (("BTC-USD", "a", {}), ("SPY", "b", {"end": "2004-11-30"})):
                runner.PINNED_REAL_MD5.update(saved)
                runner.PINNED_REAL_MD5[symbol] = md5                       # the synthetic file, planted as the pin
                planted = _small_table(tmp / sub, **fields)
                steps = []
                (code, rec), out = _captured(lambda: run_rehearsal(planted, tmp / sub, hooks=_step_hooks(steps)))
                assert (code, rec) == (2, None) and "is a byte copy of a pinned real series" in out, out[-2000:]
                assert "R-10: " in out and steps == [0, 1, 2, 3, 4], steps
        finally:
            runner.PINNED_REAL_MD5.clear()
            runner.PINNED_REAL_MD5.update(saved)
        for k, rel in enumerate(("docs/asset_expansion/cache/yf_SPY.csv", "docs/asset_expansion/cache/binance_BTCUSDT.csv")):
            for j, value in enumerate((rel, str(ROOT / rel))):
                sub = tmp / f"cache{k}{j}"
                bad = _small_table(sub, prices_file=value, prices_md5="0" * 32)
                exc = _refused(lambda: runner.check_table(bad, "rehearsal", sub / "ledgers", "qgnb-host", ROOT), "R-10")
                assert repr(value) in exc.message, exc
                steps = []
                (code, rec), out = _captured(lambda: run_rehearsal(bad, sub, hooks=_step_hooks(steps)))
                assert (code, rec) == (2, None) and "R-10: " in out and steps == [0], (steps, out[-1000:])
        card = "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json"
        bad = _small_table(tmp / "card", reference_card=str(ROOT / card), reference_card_md5="0" * 32)
        _refused(lambda: runner.check_table(bad, "rehearsal", tmp / "ledgers", "qgnb-host", ROOT), "R-10")


def test_l1_10_config_id_equals_strategy_lab():
    """L1-10 (K9): the bridge row's config_id for SPY sma/127/21 at 50.0 (E1) and BTC-USD hysteresis 0.333 at 10.0
    (C3) equals the one ui.strategy_lab_page.register_trials writes with ledger_dir given explicitly; neither is a
    pilot configuration (GOVERNANCE-R3-2). An int cost would be another configuration."""
    import ui.strategy_lab_page as lab
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l110_") as name:
        tmp, dates = Path(name), _bdates(320)
        for like, family, theta, cost, symbol in (
                ("E1-SPY", "trend_switch", {"rule": "sma", "lookback": 127, "step": 21}, 50.0, "SPY"),
                ("C3-BTCUSD", "crypto_trend", {"hysteresis": 0.333}, 10.0, "BTC-USD")):
            table = {**REHEARSAL_LIKE[like], "pilot": "rehearsal", "cost_bps": cost}
            row = runner.ledger_row(table, theta, span=(dates[0], dates[-1]), run_utc="2026-10-28T00:00:00Z",
                                    anchor=gate_ledger.repo_anchor(), bridge_run_id="NB-x")
            bridge = gate_ledger.register_trial(gate_ledger.family_ledger(row["rule"], tmp / "bridge"), row,
                                                script=runner.SCRIPT)
            n = lab.register_trials(family, [symbol], [theta], cost, dates, ["YAHOO"], ledger_dir=tmp / f"lab_{like}")
            lab_row = gate_ledger.family_ledger(lab.FAMILY_ID[family], tmp / f"lab_{like}").rows()[0]
            assert n == 1 and lab_row["config_id"] == bridge.row["config_id"], (lab_row, bridge.row)
            assert bridge.row["params"] == dict(theta, symbols=[symbol], cost_bps=cost), bridge.row["params"]
            assert type(bridge.row["params"]["cost_bps"]) is float and bridge.row["run_kind"] == "variant"
            assert bridge.row["source"] == ("nautilus-bridge rehearsal; engines quantgen.simulate + nautilus_trader "
                                            "1.231.0; run NB-x"), bridge.row["source"]
            as_int = dict(row, params=dict(row["params"], cost_bps=int(cost)))
            assert gate_ledger.config_id(as_int) != bridge.row["config_id"]


def test_l1_11_register_result_row_md5():
    """L1-11 (A-1): the recorded row_md5 is result.row["row_md5"] for an appended row and for a duplicate, never
    RegisterResult's third element, which on an append is the md5 of the line (the next row's prev_row_md5)."""
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l111_") as name:
        ledger = gate_ledger.family_ledger("E1", Path(name))
        first = gate_ledger.register_trial(ledger, _plain_row("E1", 1))
        second = gate_ledger.register_trial(ledger, _plain_row("E1", 2))
        dup = gate_ledger.register_trial(ledger, dict(_plain_row("E1", 1), run_utc="2026-10-28T01:00:00Z"))
        rows = ledger.rows()
        assert first.appended and second.appended and not dup.appended and len(rows) == 2
        assert first.row_md5 != first.row["row_md5"] and first.row_md5 == rows[1]["prev_row_md5"]
        assert dup.row_md5 == dup.row["row_md5"] == rows[0]["row_md5"]
        got = [runner.registration_entry(col, r) for col, r in enumerate((first, second, dup))]
        assert got == [{"col": 0, "config_id": rows[0]["config_id"], "row_md5": rows[0]["row_md5"], "appended": True},
                       {"col": 1, "config_id": rows[1]["config_id"], "row_md5": rows[1]["row_md5"], "appended": True},
                       {"col": 2, "config_id": rows[0]["config_id"], "row_md5": rows[0]["row_md5"], "appended": False}]


def test_l1_12_census_judgement():
    """L1-12 (5.2.7; QA-R3-12): on a census parsed from doctored -X importtime stderr, an extra TP name, a missing TP
    name, an extra NT name and nautilus_trader.adapters.binance (even in the baseline) each give C-08; an extra STD
    name does not."""
    runner = _runner()
    base = ["_io", "_sysconfigdata__linux_x86_64-linux-gnu", "json", "json.decoder", "msgspec", "nautilus_trader",
            "nautilus_trader.backtest.engine", "numpy", "numpy._core", "pandas", "sitecustomize"]
    stderr = "import time: self [us] | cumulative | imported package\n" + "".join(
        f"import time:        1 |          1 |   {n}\n" for n in reversed(base)) + "ValueError: boom\n"
    census, rest = launch.parse_census(stderr)
    assert census == base and rest == "ValueError: boom\n", (census, rest)
    assert [runner.census_class(n) for n in ("nautilus_trader.model", "zoneinfo", "_sysconfigdata_x", "uvloop")] == [
        "NT", "STD", "STD", "TP"]
    assert runner.judge_census(census, base) == []
    assert runner.judge_census(census + ["zoneinfo", "zoneinfo._common"], base) == []
    assert runner.judge_census(census + ["plotly"], base) == ["C-08: TP names added: plotly"]
    assert runner.judge_census([n for n in census if n != "msgspec"], base) == ["C-08: TP names missing: msgspec"]
    assert runner.judge_census(census + ["nautilus_trader.live.node"], base) == [
        "C-08: NT names added: nautilus_trader.live.node"]
    binance = "nautilus_trader.adapters.binance"
    assert runner.judge_census(census + [binance], base + [binance]) == [f"C-08: denied modules imported: {binance}"]


def test_l1_18_gate_bootstrap_b_refusal_r08():
    """L1-18: with GATE["bootstrap_B"] set to 300 inside try/finally, run() refuses R-08 at step 9, before
    registration; GATE is restored."""
    from core.quant import validate
    with tempfile.TemporaryDirectory(prefix="qgnb_l118_") as name:
        tmp, steps = Path(name), []
        table = _small_table(tmp)
        saved = validate.GATE["bootstrap_B"]
        try:
            validate.GATE["bootstrap_B"] = 300
            (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks=_step_hooks(steps)))
        finally:
            validate.GATE["bootstrap_B"] = saved
        assert (code, rec) == (2, None) and "R-08: GATE['bootstrap_B'] is 300, not 2000" in out, out[-2000:]
        assert steps == list(range(9)) and validate.GATE["bootstrap_B"] == 2000, steps
        assert not (tmp / "ledgers" / "E1.jsonl").exists()


def test_l1_19_table_refusals_r11():
    """L1-19 (6.6; GOVERNANCE-R2-2, GOVERNANCE-R3-1, GOVERNANCE-R4-4, OPS-R3-6): R-11 through check_table for a
    table that is not JSON, a missing or unknown field, a wrong type and a grid that differs from grid_from(axes);
    of-record: a pilot value off, a key field edited and a sandbox byte or a core/quant/validate.py byte changed
    after owner_confirmed; a PureWindowsPath-built path list gives the same code_sha256; run(mode="of-record") with
    a seam refuses in argument validation and creates no runs/.locks; of-record C3-BTCUSD on a temp root refuses
    without a reference card, without an of-record E1-SPY record and with one WITHHELD for a parity failure."""
    runner = _runner()
    locks = ROOT / "docs" / "nautilus_bridge" / "runs" / ".locks"
    had_locks = locks.exists()
    with tempfile.TemporaryDirectory(prefix="qgnb_l119_") as name:
        tmp = Path(name)
        table = _small_table(tmp / "r")
        good = json.loads(table.read_text(encoding="utf-8"))
        assert runner.check_table(table, "rehearsal", tmp / "ledgers", "qgnb-host", ROOT) == good

        def variant(change) -> Path:
            t = json.loads(json.dumps(good))
            change(t)
            path = tmp / "variant.json"
            path.write_text(json.dumps(t), encoding="utf-8", newline="\n")
            return path
        (tmp / "notjson.json").write_text("{not json\n", encoding="utf-8", newline="\n")
        for path in (tmp / "notjson.json", variant(lambda t: t.pop("embargo")), variant(lambda t: t.update(x=1)),
                     variant(lambda t: t.update(embargo="21")), variant(lambda t: t["grid"].pop()),
                     variant(lambda t: t.update(pilot="E1-SPY")), variant(lambda t: t.update(price_precision=2)),
                     variant(lambda t: t["grid"][0].update(lookback=0))):
            _refused(lambda: runner.check_table(path, "rehearsal", tmp / "ledgers", "qgnb-host", ROOT), "R-11")
        root = _code_root(tmp / "root")
        code = runner.code_sha256(root)
        assert code == runner.code_sha256(ROOT)
        win_root = PureWindowsPath("C:/Users/o/QUANTGEN")
        paths = runner.code_paths(ROOT)
        win = [win_root / PureWindowsPath(p.relative_to(ROOT).as_posix()) for p in paths]
        by_win = dict(zip(win, paths))
        assert runner.code_digest(win_root, win, lambda w: by_win[w].read_bytes()) == code
        e1 = _of_record_table(tmp / "e1.json", "E1-SPY", code)
        chk = lambda path: runner.check_table(path, "of-record", tmp / "ledgers", "qgnb-host", root)   # noqa: E731
        assert "does not exist" in _refused(lambda: chk(e1), "R-15").message      # R-11 passed, R-15 is next
        exc = _refused(lambda: chk(_of_record_table(tmp / "cap.json", "E1-SPY", code, capital_usd="999999")), "R-11")
        assert "capital_usd" in exc.message, exc
        t = json.loads(e1.read_text(encoding="utf-8"))
        t["embargo"] = 22
        (tmp / "edited.json").write_text(json.dumps(t), encoding="utf-8", newline="\n")
        assert "owner_confirmed" in _refused(lambda: chk(tmp / "edited.json"), "R-11").message
        for rel in ("tools/nautilus/sandbox.py", "core/quant/validate.py"):
            orig = (root / rel).read_bytes()
            (root / rel).write_bytes(orig + b"\n")
            try:
                assert "owner_confirmed" in _refused(lambda: chk(e1), "R-11").message, rel
            finally:
                (root / rel).write_bytes(orig)
        for seam in ({"child_cmd": stub_cmd()}, {"probe_cmd": stub_probe_cmd()}, {"hooks": {}}, {"timeout": 3},
                     {"ledger_dir": tmp / "ledgers"}, {"register_fn": lambda *a, **k: None}):
            code_, out = _captured(lambda: runner.run(e1, mode="of-record", **seam))
            assert code_ == 2 and "R-11: of-record mode takes no test seam" in out, (seam, out[-500:])
        assert locks.exists() == had_locks
        card = "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json"
        (root / card).parent.mkdir(parents=True, exist_ok=True)
        (root / card).write_bytes(b'{"card": "a temp stand-in"}\n')
        c3 = _of_record_table(tmp / "c3.json", "C3-BTCUSD", code, reference_card=card,
                              reference_card_md5=_md5(root / card))
        nocard = _of_record_table(tmp / "c3n.json", "C3-BTCUSD", code)
        assert "reference_card" in _refused(lambda: chk(nocard), "R-11").message
        assert "E1-SPY" in _refused(lambda: chk(c3), "R-11").message
        e1_record = {"mode": "of-record", "pilot": "E1-SPY", "status": "WITHHELD", "table": {"code_sha256": code},
                     "parity": {"hard_pass": False}, "registration": {"rows": [{}] * 12}}
        run_dir = root / "docs" / "nautilus_bridge" / "runs" / "NB-20261101T000000000000Z-00000000"
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps(e1_record), encoding="utf-8", newline="\n")
        assert "E1-SPY" in _refused(lambda: chk(c3), "R-11").message
        e1_record.update(status="WITHHELD", parity={"hard_pass": True})
        (run_dir / "run.json").write_text(json.dumps(e1_record), encoding="utf-8", newline="\n")
        assert "C3.jsonl does not exist" in _refused(lambda: chk(c3), "R-15").message   # the precondition holds


def test_l1_20a_p0a_against_the_study_loaders():
    """L1-20, P0a cases (QUANT-1, QA-R4-1): check_p0a on a synthetic cache dir: equal arrays pass and return the
    study's panel; a doctored study.rf_daily or a doctored close refuses R-13; a cache dir without yf_SPY.csv, and
    one without fred_DGS3MO.csv, refuse R-13 while the stand-in records the blocked download; REFRESH true is R-13;
    sys.modules holds no stand-in afterwards."""
    import numpy as np
    runner = _runner()
    study = runner.load_study(ROOT)
    with tempfile.TemporaryDirectory(prefix="qgnb_l120_") as name:
        tmp = Path(name)
        n, dates = 320, _bdates(320)
        cache = tmp / "cache"
        md5 = _write_prices(cache / "yf_SPY.csv", dates, synth_prices(7, n, 100.0, 150.0))
        rmd5 = _write_rf(cache / "fred_DGS3MO.csv", dates, synth_rf(n))
        p = runner.load_prices(cache / "yf_SPY.csv", md5=md5, start=dates[0], end=dates[-1], instrument="SPY",
                               mode="rehearsal")
        rf, _ = runner.load_rf(cache / "fred_DGS3MO.csv", md5=rmd5, dates=p.dates)
        arrays = {"symbol": "SPY", "start": dates[0], "dates": p.dates, "closes": p.closes, "rf": rf}
        pn = runner.check_p0a(study, cache, arrays)
        assert tuple(pn.dates) == p.dates and pn.prices.shape == (n, 1) and study.CACHE == cache
        assert runner.check_p0a(study, cache, dict(arrays, rf=None)).dates == pn.dates      # pilot 2: no rf

        def no_stand_ins() -> bool:
            return not any(isinstance(sys.modules.get(m), runner._Blocked)
                           for m in ("yfinance", "pandas_datareader", "pandas_datareader.data"))
        assert no_stand_ins()
        real = study.rf_daily
        try:
            study.rf_daily = lambda index: real(index) + 1e-12
            assert "rf differ" in _refused(lambda: runner.check_p0a(study, cache, arrays), "R-13").message
        finally:
            study.rf_daily = real
        closes = p.closes.copy()
        closes[200] += 1e-9
        assert "closes differ" in _refused(lambda: runner.check_p0a(study, cache, dict(arrays, closes=closes)),
                                           "R-13").message
        (tmp / "no_yf").mkdir()
        shutil.copy(cache / "fred_DGS3MO.csv", tmp / "no_yf" / "fred_DGS3MO.csv")
        exc = _refused(lambda: runner.check_p0a(study, tmp / "no_yf", arrays), "R-13")
        assert "yfinance.download" in exc.message and no_stand_ins(), exc
        (tmp / "no_fred").mkdir()
        shutil.copy(cache / "yf_SPY.csv", tmp / "no_fred" / "yf_SPY.csv")
        exc = _refused(lambda: runner.check_p0a(study, tmp / "no_fred", arrays), "R-13")
        assert "rf differ" in exc.message and "pandas_datareader.data" in exc.message and no_stand_ins(), exc
        study.REFRESH = True
        try:
            _refused(lambda: runner.check_p0a(study, cache, arrays), "R-13")
        finally:
            study.REFRESH = False
        assert np.array_equal(pn.prices[:, 0], p.raw)


def test_l1_23_egress_refusals_r14():
    """L1-23 (SECURITY-1, R-14): a stub probe printing {"blocked": false} refuses at step 4; check_egress_record
    refuses a missing record, another base_python, an unblocked probe, a failed control connect and another layer,
    and on Windows accepts paths differing only in case or slash direction (4.3)."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l123_") as name:
        tmp, steps = Path(name), []
        table = _small_table(tmp)
        probe = tmp / "open_probe.py"
        probe.write_text("print('{\"blocked\": false, \"errno\": null, \"error\": \"\"}')\n", encoding="utf-8",
                         newline="\n")
        code, out = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                 out_dir=tmp / "out", child_cmd=stub_cmd(),
                                                 probe_cmd=[stub_python(), "-I", str(probe)], hooks=_step_hooks(steps)))
        assert code == 2 and "R-14: the egress probe was not blocked" in out and steps == [0, 1, 2, 3], out[-2000:]
        nt = os.name == "nt"
        facts = {"venv_python": r"C:\Users\o\AppData\Local\quantgen\ntvenv\Scripts\python.exe" if nt
                 else "/opt/qg/ntvenv/bin/python",
                 "base_python": r"C:\Users\o\AppData\Local\quantgen\py313\python.exe" if nt else "/usr/bin/python3.13",
                 "layer": runner.LAYER}
        record_dir = tmp / "egress"
        record_dir.mkdir()
        _refused(lambda: runner.check_egress_record(record_dir, facts), "R-14")
        base = {"schema": "nautilus-bridge-egress/1", "platform_tag": launch.host_tag(), **facts,
                "probe": {"blocked": True, "errno": 101, "error": "unreachable"},
                "recorded_utc": "2026-10-28T00:00:00.000000Z", "control_connect": {"ok": True, "error": ""}}

        def put(**changes) -> None:
            (record_dir / f"{launch.host_tag()}.json").write_text(json.dumps({**base, **changes}), encoding="utf-8",
                                                                  newline="\n")
        put()
        runner.check_egress_record(record_dir, facts)
        for changes, word in (({"base_python": facts["base_python"] + "x"}, "base_python"),
                              ({"probe": {"blocked": False, "errno": None, "error": ""}}, "does not prove"),
                              ({"control_connect": {"ok": False, "error": "timeout"}}, "does not prove"),
                              ({"layer": "something else"}, "layer")):
            put(**changes)
            assert word in _refused(lambda: runner.check_egress_record(record_dir, facts), "R-14").message, changes
        if nt:
            put(**{k: facts[k].upper().replace("\\", "/") for k in ("venv_python", "base_python")})
            runner.check_egress_record(record_dir, facts)


def test_l1_24_ledger_and_host_refusals_r15():
    """L1-24 (GOVERNANCE-3; R-15): of-record check_table on temp dirs refuses a missing family ledger, an empty one
    and a host fingerprint off by one character (R-15), and a broken chain (R-09); with the right fingerprint the
    whole of-record table check passes. host_fingerprint is 6.6's sha256, None for a ledger without a row."""
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l124_") as name:
        tmp = Path(name)
        root = _code_root(tmp / "root")
        code, ledgers = runner.code_sha256(root), tmp / "ledgers"
        chk = lambda path: runner.check_table(path, "of-record", ledgers, "qgnb-host", root)   # noqa: E731
        table = _of_record_table(tmp / "t.json", "E1-SPY", code)
        assert "does not exist" in _refused(lambda: chk(table), "R-15").message
        ledgers.mkdir()
        (ledgers / "E1.jsonl").write_bytes(b"")
        assert "holds no row" in _refused(lambda: chk(table), "R-15").message
        ledger = gate_ledger.family_ledger("E1", ledgers)
        gate_ledger.register_trial(ledger, _plain_row("E1", 1))
        fp = runner.host_fingerprint("qgnb-host", ledger)
        assert fp == hashlib.sha256(("qgnb-host\n" + ledger.rows()[0]["row_md5"]).encode("utf-8")).hexdigest()
        assert runner.host_fingerprint("qgnb-host", gate_ledger.family_ledger("C3", ledgers)) is None
        t = json.loads(table.read_text(encoding="utf-8"))
        for value, rid in ((fp[:-1] + ("0" if fp[-1] != "0" else "1"), "R-15"), (fp, None)):
            t["host_fingerprint"] = value                    # outside table_sha256, so owner_confirmed still holds
            table.write_text(json.dumps(t), encoding="utf-8", newline="\n")
            if rid:
                assert "host_fingerprint" in _refused(lambda: chk(table), rid).message
            else:
                assert chk(table) == t
        raw = ledger.path.read_bytes()
        ledger.path.write_bytes(raw.replace(b'"US"', b'"KR"'))
        _refused(lambda: chk(table), "R-09")


def test_l1_25_lock_and_freshness_r16():
    """L1-25 (5.3.5; QA-R2-3, QA-R4-6): take_lock refuses while another handle holds the table lock (flock, not
    lockf, so it conflicts inside one process) and passes after release; a C3.jsonl or family ledger touched now
    refuses, one touched 601 s ago passes; a refused take_lock leaves no lock behind."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l125_") as name:
        tmp = Path(name)
        out, sha = tmp / "out", "ab" * 32
        c3, e1 = tmp / "ledgers" / "C3.jsonl", tmp / "ledgers" / "E1.jsonl"
        lock, earlier = runner.take_lock(out, sha, [c3, e1], None)
        assert earlier == [] and lock.path == out / ".locks" / f"{sha[:16]}.lock"
        try:
            assert "another runner is active" in _refused(lambda: runner.take_lock(out, sha, [c3, e1], None),
                                                          "R-16").message
        finally:
            lock.release()
        runner.take_lock(out, sha, [c3, e1], None)[0].release()
        old = time.time() - 601
        for path in (c3, e1):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")
            assert "wait" in _refused(lambda: runner.take_lock(out, sha, [c3, e1], None), "R-16").message, path
            os.utime(path, (old, old))
            runner.take_lock(out, sha, [c3, e1], None)[0].release()


def test_l1_26a_lifecycle_records_and_exits():
    """L1-26 without its G-05 case (5.3.5; G-06, G-07, R-12): IN_PROGRESS is on disk after registration; a hook
    raising KeyboardInterrupt gives ABORTED, exit 5; a hook raising ValueError gives ERROR, exit 4, G-06 with the
    traceback; a register_fn raising on the third row gives R-12, REFUSED_REGISTRATION, exit 3, two rows recorded."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l126_") as name:
        tmp, seen = Path(name), []
        table = _small_table(tmp / "a")

        def at12(ctx):
            rec = json.loads((ctx.run_dir / "run.json").read_text(encoding="utf-8"))
            seen.append((rec["status"], rec["registration"]["hash_after"], ctx.hash_after_registration,
                         len(rec["children"])))
            raise KeyboardInterrupt
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "a", hooks={"after_step12": at12}))
        h = rec["registration"]["hash_after"]
        assert seen == [("IN_PROGRESS", h, h, 0)] and (code, rec["status"]) == (5, "ABORTED"), (seen, out[-1000:])
        assert rec["error"]["message"] == "G-07: KeyboardInterrupt after registration", rec["error"]
        assert out.splitlines()[-1] == f"STATUS ABORTED exit=5 record={tmp / 'a' / 'out' / rec['bridge_run_id'] / 'run.json'}"
        table = _small_table(tmp / "c")

        def boom(_ctx):
            raise ValueError("planted after step 13")
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "c", hooks={"after_step13": boom}))
        assert (code, rec["status"], rec["children"]) == (4, "ERROR", []), out[-1000:]
        assert rec["error"]["message"] == "G-06: ValueError: planted after step 13" and "boom" in rec["error"]["traceback"]
        table = _small_table(tmp / "d", axes={"rule": ["sma"], "lookback": [126, 210, 252], "step": [21]})
        calls = []

        def third(ledger, row, *, script=None):
            calls.append(row)
            if len(calls) == 3:
                raise OSError("disk full (planted)")
            return gate_ledger.register_trial(ledger, row, script=script)
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "d", register_fn=third))
        assert (code, rec["status"]) == (3, "REFUSED_REGISTRATION"), out[-1000:]
        assert rec["error"]["message"] == "R-12: register_trial raised OSError: disk full (planted)", rec["error"]
        assert [r["col"] for r in rec["registration"]["rows"]] == [0, 1] and rec["children"] == []
        assert gate_ledger.family_ledger("E1", tmp / "d" / "ledgers").n_raw == 2


def test_l1_27_child_failures_and_doctored_manifests():
    """L1-27 (section 7): stubs that exit 1, sleep past timeout=3 (the tree is killed and the call returns), write
    no manifest or write invalid JSON give C-06; a child_started hook raising KeyboardInterrupt while a sleeping stub
    runs gives ABORTED, exit 5, and the temp dir is removed (OPS-R2-4); a wrong --guard-selftest outcome gives R-03
    (QA-R2-10); doctored manifests (valid true, exit 0) give their own id (QA-R3-2)."""
    dirs: list[Path] = []

    def rehearse(*flags: str, **kw):
        tmp = Path(tempfile.mkdtemp(prefix="qgnb_l127_"))
        dirs.append(tmp)
        (code, rec), out = _captured(lambda: run_rehearsal(_small_table(tmp), tmp, flags=flags, **kw))
        return code, rec, out
    try:
        for flags, want in ((("--exit", "1"), "C-06: exit 1"), (("--sleep", "60"), "C-06: timed out after 3 s"),
                            (("--no-manifest",), "C-06: manifest.json missing"),
                            (("--bad-json",), "C-06: manifest.json missing or not a JSON object")):
            started = time.monotonic()
            code, rec, out = rehearse(*flags, timeout=3)
            assert rec is not None and len(rec["children"]) == 2, (flags, out[-1000:])
            assert all(any(r.startswith(want) for r in c["invalid"]) for c in rec["children"]), (
                flags, [c["invalid"] for c in rec["children"]])
            assert time.monotonic() - started < 60 and rec["cleanup_leftovers"] == [], flags
        cwds = []

        def interrupt(lc):
            cwds.append(lc.cwd)
            raise KeyboardInterrupt
        code, rec, out = rehearse("--sleep", "60", hooks={"child_started": interrupt})
        assert (code, rec["status"]) == (5, "ABORTED") and len(cwds) == 1 and not Path(cwds[0]).exists(), out[-1000:]
        assert out.splitlines()[-1].startswith("STATUS ABORTED exit=5 record=")
        code, rec, out = rehearse("--selftest-wrong")
        assert (code, rec) == (2, None) and "R-03: --guard-selftest misbehaved" in out, out[-1000:]
        for cid in ("C-01", "C-02", "C-03", "C-04", "C-07", "C-09", "C-11", "C-14", "C-15"):
            code, rec, out = rehearse("--doctor", cid)
            assert rec is not None and len(rec["children"]) == 2, (cid, out[-1000:])
            for c in rec["children"]:
                assert c["returncode"] == 0 and c["manifest"]["valid"] is True, (cid, c["returncode"])
                assert any(r.startswith(f"{cid}: ") for r in c["invalid"]), (cid, c["invalid"])
    finally:
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)


def test_l1_33_goldens_equal_the_spec_tables():
    """L1-33 (QA-R2-6, QA-R3-8): the committed F1, F2 and N1 goldens, in C1's JSON bytes, equal 8.2's tables typed
    in above, compared as 6.8 says (strings and integers exactly, money within 0.005, reasons by id)."""
    runner = _runner()
    for name, want in GOLDEN_SPEC.items():
        raw = (GOLDEN_DIR / f"{name}.json").read_bytes()
        got = json.loads(raw)
        assert raw == (json.dumps(got, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"), name
        assert set(got) == set(want) and runner.compare_golden(got, want) == [], (
            name, runner.compare_golden(got, want))
    f1, n1 = GOLDEN_SPEC["F1"], GOLDEN_SPEC["N1"]
    assert runner.compare_golden(dict(f1, final_cash="926593.004"), f1) == []
    assert runner.compare_golden(dict(f1, final_cash="926593.006"), f1) == [
        "final_cash: '926593.006' != '926593.00'"]
    assert runner.compare_golden(dict(f1, fills=[dict(f1["fills"][0], price="100.00")] + f1["fills"][1:]), f1) == [
        "fill 0 price: '100.00' != '100.000000000'"]
    assert runner.compare_golden(dict(n1, invalid_reasons=["C-01: other words", "C-02: x"]), n1) == []


def test_l1_34_write_record_retries_and_fallback():
    """L1-34 (OPS-R2-3, QA-R3-7): write_record retries a replace that raises PermissionError twice (no-op sleep) and
    writes; one that always raises leaves the old bytes and raises after 10 attempts; a run whose every record write
    fails lists the intermediate writes and falls back to run.final.<pid>.json, which the STATUS line names."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l134_") as name:
        tmp = Path(name)
        path = tmp / "w" / "run.json"
        path.parent.mkdir()
        path.write_text("{}\n", encoding="utf-8", newline="\n")
        calls, sleeps = [], []

        def flaky(src, dst):
            calls.append(src)
            if len(calls) <= 2:
                raise PermissionError(13, "held by the indexer (planted)")
            os.replace(src, dst)
        obj = {"status": "IN_PROGRESS", "children": [1, 2]}
        runner.write_record(path, obj, replace=flaky, sleep=sleeps.append)
        assert json.loads(path.read_text(encoding="utf-8")) == obj and len(calls) == 3 and sleeps == [0.5, 0.5]
        assert b"\r" not in path.read_bytes() and sorted(p.name for p in path.parent.iterdir()) == ["run.json"]

        def never(src, dst):
            raise PermissionError(13, "always held (planted)")
        try:
            runner.write_record(path, {"status": "ERROR"}, replace=never, sleep=sleeps.append)
        except PermissionError:
            pass
        else:
            raise AssertionError("write_record did not raise after 10 attempts")
        assert json.loads(path.read_text(encoding="utf-8")) == obj and len(sleeps) == 2 + 9, len(sleeps)
        assert sorted(p.name for p in path.parent.iterdir()) == ["run.json"]
        table = _small_table(tmp / "r")
        real = runner.write_record
        runner.write_record = lambda p, o, **kw: real(p, o, replace=never, sleep=lambda _s: None)
        try:
            def stop(_ctx):
                raise KeyboardInterrupt
            (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "r", hooks={"after_step15": stop}))
        finally:
            runner.write_record = real
        finals = list((tmp / "r" / "out").glob("NB-*/run.final.*.json"))
        assert (code, rec) == (5, None) and [f.name for f in finals] == [f"run.final.{os.getpid()}.json"], out[-1000:]
        final = json.loads(finals[0].read_text(encoding="utf-8"))
        assert final["status"] == "ABORTED" and len(final["children"]) == 2, final["status"]
        assert [f.split(":")[0] for f in final["record_write_failures"]] == [
            "IN_PROGRESS", "child 0 x1", "child 0 x2", "final"], final["record_write_failures"]
        assert out.splitlines()[-1] == f"STATUS ABORTED exit=5 record={finals[0]}", out[-500:]


def test_l1_35_record_baseline_rules():
    """L1-35 (5.2.7; OPS-R3-2, OPS-R4-2, OPS-R5-3, QA-R4-4): record_baseline on a temp golden dir: a new file is
    written in C1's bytes; a tracked equal baseline gives exit 0 "unchanged"; a tracked different one gives exit 2,
    the diff and the removal line and leaves the bytes; an untracked different one is replaced, its diff printed,
    exit 0; a tracked path with no file, as after the removal line, is written, exit 0."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l135_") as name:
        golden = Path(name)
        census = ["_io", "json", "msgspec", "nautilus_trader", "nautilus_trader.backtest.engine"]
        path = golden / "modules_test_tag.json"
        assert runner.record_baseline(golden, "test_tag", census, tracked=False, python="3.13.17") == (
            0, ["+ STD _io", "+ STD json", "+ TP msgspec", "+ NT nautilus_trader",
                "+ NT nautilus_trader.backtest.engine", "written modules_test_tag.json"])
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written == {"schema": "nautilus-bridge-census/1", "platform_tag": "test_tag", "python": "3.13.17",
                           "recorded_from": ["F1", "F2"], "census": census}, written
        before = path.read_bytes()
        assert before == (json.dumps(written, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        assert runner.record_baseline(golden, "test_tag", list(reversed(census)), tracked=True) == (0, ["unchanged"])
        code, lines = runner.record_baseline(golden, "test_tag", census + ["plotly"], tracked=True)
        removal = ("Remove-Item tools\\nautilus\\golden\\modules_test_tag.json" if os.name == "nt"
                   else "rm tools/nautilus/golden/modules_test_tag.json")
        assert code == 2 and lines[0] == "+ TP plotly" and lines[-1] == removal and path.read_bytes() == before, lines
        assert runner.record_baseline(golden, "test_tag", census[:-1], tracked=False) == (
            0, ["- NT nautilus_trader.backtest.engine", "written modules_test_tag.json"])
        assert json.loads(path.read_text(encoding="utf-8"))["census"] == census[:-1]
        path.unlink()
        code, lines = runner.record_baseline(golden, "test_tag", census, tracked=True)
        assert code == 0 and lines[-1] == "written modules_test_tag.json" and path.is_file(), lines


def test_l2_02_f1_f2_match_goldens():
    """L2-2 (K6, QA-12): F1 and F2 through the exact launch contract match their committed goldens and 8.2; each
    manifest is valid with run_analysis false and stats_pnls_empty true."""
    python = layer2()
    runner = _runner()
    unshare = launch.resolve_unshare()
    for name in ("F1", "F2"):
        got = runner.run_fixture(name, python, unshare)
        want = json.loads((GOLDEN_DIR / f"{name}.json").read_text(encoding="utf-8"))
        assert runner.compare_golden(got["golden"], want) == [], (name, runner.compare_golden(got["golden"], want))
        assert runner.compare_golden(got["golden"], GOLDEN_SPEC[name]) == [], name
        m = got["manifest"]
        assert got["result"].returncode == 0 and m["valid"] is True, (name, got["result"].stderr_tail[-500:])
        assert m["engine"]["run_analysis"] is False and m["result"]["stats_pnls_empty"] is True, m["engine"]


def test_l2_03_n1_matches_golden():
    """L2-3 (QA-2): N1 (volume 4000, 2 price decimals) matches its golden: one fill, a forced stop, 4 of 12 bars,
    exit 10 with C-01 and C-02, which the parent re-derives from the manifest (5.2.7)."""
    python = layer2()
    runner = _runner()
    got = runner.run_fixture("N1", python, launch.resolve_unshare())
    want = json.loads((GOLDEN_DIR / "N1.json").read_text(encoding="utf-8"))
    assert runner.compare_golden(got["golden"], want) == [] and runner.compare_golden(got["golden"], GOLDEN_SPEC["N1"]) == []
    raw, bars = launch.fixture_inputs("N1")
    _, ts, _ = _fixture_series("N1")
    m = got["manifest"]
    reasons = runner.manifest_reasons(m, n_bars=12, first_ts=ts[0], last_ts=ts[-1],
                                      bars_sha256=hashlib.sha256(bars).hexdigest(),
                                      input_sha256=hashlib.sha256(raw).hexdigest(),
                                      ledger_hash=json.loads(raw)["ledger_hash_after_registration"],
                                      check_env={"precision": m["precision"], "environment": "BACKTEST"})
    assert [r.split(":")[0] for r in reasons] == ["C-01", "C-02"], reasons


def test_l2_06_census_matches_platform_baseline():
    """L2-6 (5.2.7; QA-R3-12): the F1 and F2 import censuses match this platform's committed baseline under 5.2.7's
    rule (NT and TP sets equal, no adapters or network module)."""
    python = layer2()
    runner = _runner()
    tag = launch.read_venv(python)["wheel"]["platform_tag"]
    path = GOLDEN_DIR / f"modules_{tag}.json"
    assert path.is_file(), f"no census baseline {path.name}: runner --fixtures --record-baseline records it"
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert (rec["schema"], rec["platform_tag"], rec["recorded_from"]) == ("nautilus-bridge-census/1", tag, ["F1", "F2"])
    assert rec["census"] == sorted(set(rec["census"])), "the census is sorted and unique"
    unshare = launch.resolve_unshare()
    for name in ("F1", "F2"):
        got = runner.run_fixture(name, python, unshare)
        assert got["census"] and runner.judge_census(got["census"], rec["census"]) == [], (
            name, runner.judge_census(got["census"], rec["census"]))
```
  Run them (RED):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance 2>/dev/null | grep -v '^PASS'
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance 2>/dev/null | grep -E '^FAIL test_l2|passed'
```
  Expected without the key: 21 lines `FAIL test_l1_<nn>_... ImportError: cannot import name 'runner' from 'tools.nautilus' (/home/user/quantgen/tools/nautilus/__init__.py)`, one per new layer-1 test (01, 03, 04, 06 to 12, 18, 19, 20a, 23 to 27, 33 to 35), then the 10 `NOT_RUN test_l2_... OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)` lines, an empty line and `11/42 passed, 21 failed, 10 not run`. L1-15 and L1-32 still pass (the block obeys spec 3.7, and no test touches a guarded root). With the key (about 1.5 minutes): the same 21 FAIL lines plus `FAIL test_l2_02_f1_f2_match_goldens`, `FAIL test_l2_03_n1_matches_golden` and `FAIL test_l2_06_census_matches_platform_baseline` with the same ImportError, and `18/42 passed, 24 failed, 0 not run`.

- [ ] **Step 3: Create the stub child.** Create `tests/nautilus_stub_child.py` with this exact content (LF):
```python
"""The layer-1 stub child of the NautilusTrader bridge (spec 2026-10-26 section 8.1; QA-R2-2). Standard library only.

    <stub python> -I <abs tests/nautilus_stub_child.py> [failure flags] {--check-env | --guard-selftest | --probe |
                                                                         run --in <dir>}

It answers the sandbox's two self-checks as the sandbox does, `--probe` as a blocked egress probe, and in `run` mode
reads input.json and bars.csv, applies the decision rules of spec 5.2.5 (plain_mean for every moving average, the
fee-inclusive Decimal sizing), fills every order at its bar's close, rounds each commission with `cents` (5.4.1) and
writes fills.csv, decisions.csv, onbar_equity.csv and manifest.json with every field of spec 6.2, so a correct input
passes every hard check. The failure flags select one failure mode each; a `--doctor <id>` manifest still says
`valid: true` and the stub exits 0, so only the parent's own re-derivation can catch it (QA-R3-2).
"""
import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from pathlib import Path

PRECISION = {"HIGH_PRECISION": True, "FIXED_PRECISION": 16, "QUANTITY_MAX": 34028236692093.0,
             "PRICE_MAX": 17014118346046.0}                   # the Linux wheel's, as --check-env prints them (C3)
SELFTEST = {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}
DOCTORS = ("C-01", "C-02", "C-03", "C-04", "C-07", "C-09", "C-11", "C-14", "C-15")
CRYPTO_DEFAULTS = {"lookbacks": [7, 14, 21, 28], "mas": [10, 20, 50, 100, 200]}


def text(d: Decimal) -> str:
    """A Decimal as plain digits, "0" for zero (never "0E-8" or "1E+4")."""
    return "0" if d == 0 else format(d, "f")


def cents(x) -> int:
    """How Money rounds a commission (spec 5.4.1): the value as a double, times 100, half away from zero."""
    return int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def plain_mean(xs) -> float:
    """A left-to-right loop, never sum() (spec 5.2.5)."""
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)


def decide(inp: dict, P: list[float], i: int, held: int):
    """(decision or None, margin) on bar i: the table of spec 5.2.5."""
    prm = inp["params"]
    if inp["strategy"] == "trend_switch":
        L, s = prm["lookback"], prm["step"]
        if i < L or (i - L) % s:
            return None, None
        if prm["rule"] == "sma":
            mean = plain_mean(P[i - L + 1:i + 1])
            return (1 if P[i] > mean else 0), abs(P[i] - mean) / P[i]
        r = P[i] / P[i - L] - 1.0
        return (1 if r > 0.0 else 0), abs(r)
    lookbacks, mas = prm.get("lookbacks", CRYPTO_DEFAULTS["lookbacks"]), prm.get("mas", CRYPTO_DEFAULTS["mas"])
    if i < max(max(lookbacks), max(mas)):
        return None, None
    refs = [P[i - k] for k in lookbacks] + [plain_mean(P[i - n + 1:i + 1]) for n in mas]
    votes = [(P[i] - ref > 0) - (P[i] - ref < 0) for ref in refs]
    comp = sum(votes) / len(votes)
    state = 1 if comp > prm["hysteresis"] else 0 if comp < -prm["hysteresis"] else held
    return state, min(abs(P[i] - ref) / P[i] for ref in refs)


def write_csv(path: Path, header: list[str], rows: list[list]) -> str:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simulate(inp: dict, closes: list[str], ts: list[int], fee_1x: bool) -> dict:
    """The port's bar loop with a fill at every order's bar close; returns the rows and the final state."""
    P = [float(c) for c in closes]
    sp = inp["size_precision"]
    unit = Decimal(1).scaleb(-sp)
    c_size = Decimal(inp["cost_bps"]) * Decimal(inp["stress"]) / Decimal(10000)
    c_fee = Decimal(inp["cost_bps"]) / Decimal(10000) if fee_1x else c_size
    cash, qty, held = Decimal(inp["capital_usd"]), Decimal(0), 0
    fills, decisions, equity = [], [], []
    for i, (close, t) in enumerate(zip(closes, ts)):
        px = Decimal(close)
        equity.append([i, t, close, text(cash), text(qty), text(cash + qty * px)])
        decision, margin = decide(inp, P, i, held)
        if decision is None:
            continue
        action = "hold"
        if decision != held:
            if decision == 1:
                q = (cash / (px * (1 + c_size)) / unit).to_integral_value(rounding=ROUND_FLOOR) * unit
            else:
                q = qty
            action = "skip_zero_qty"
            if q > 0:
                action = "buy" if decision == 1 else "sell"
                held = decision
                fee = Decimal(cents(q * px * c_fee)) / 100
                cash += -(q * px + fee) if decision == 1 else q * px - fee
                qty += q if decision == 1 else -q
                n = len(fills) + 1
                fills.append([t, "BUY" if decision == 1 else "SELL", f"{q:.{sp}f}", close, f"{fee:.2f}", "USD",
                              f"STUB-T{n}", f"STUB-O{n}"])
        decisions.append([i, t, decision, repr(margin), action])
    return {"fills": fills, "decisions": decisions, "equity": equity, "cash": cash, "qty": qty}


def manifest(inp: dict, raw: bytes, ts: list[int], sim: dict, hashes: dict) -> dict:
    """Every field of spec 6.2, valid by the child's own checks."""
    u = platform.uname()
    n = len(ts)
    return {"schema": "nautilus-bridge-manifest/2", "read_only": True, "mode": "run",
            "python": platform.python_version(), "system": u.system, "machine": u.machine,
            "precision": dict(PRECISION), "environment": "BACKTEST", "strategy_started": True,
            "input": {"input_json_sha256": hashlib.sha256(raw).hexdigest(), "bars_sha256": inp["bars_sha256"],
                      "bars_fed": n, "first_ts": ts[0], "last_ts": ts[-1], "cost_bps": inp["cost_bps"],
                      "stress": inp["stress"],
                      "ledger_hash_after_registration": inp["ledger_hash_after_registration"]},
            "engine": {"run_analysis": False, "log_level": "ERROR", "log_colors": False, "account_type": "CASH",
                       "oms_type": "NETTING", "allow_cash_borrowing": False, "bar_execution": True,
                       "fill_seed": inp["fill_seed"]},
            "result": {"bars_seen": n, "iterations": n, "backtest_end": ts[-1], "force_stop": False,
                       "orders_total": len(sim["fills"]), "orders_filled": len(sim["fills"]), "denied": 0,
                       "rejected": 0, "orders_not_filled": [], "account_balance_usd": f"{sim['cash']:.2f}",
                       "final_qty": text(sim["qty"]), "stats_pnls_empty": True},
            "hashes": hashes, "valid": True, "invalid_reasons": []}


def doctor(m: dict, sim: dict, cid: str) -> None:
    """One planted condition the parent must re-derive (spec 5.2.7, section 7); the manifest stays `valid: true`."""
    r = m["result"]
    if cid == "C-01":
        r["force_stop"] = True
    elif cid == "C-02":                                   # bars_seen and bars_fed lowered together (QA-R4-3)
        r["bars_seen"] -= 1
        m["input"]["bars_fed"] -= 1
    elif cid == "C-03":
        r["orders_not_filled"] = ["O-STUB-1"]
    elif cid == "C-04":
        r["denied"] = 1
    elif cid == "C-07":
        m["precision"] = dict(m["precision"], FIXED_PRECISION=9)
    elif cid == "C-09":                                   # the first fill one nanosecond off its bar
        sim["fills"][0][0] += 1
    elif cid == "C-11":
        m["input"]["bars_sha256"] = "0" * 64
    elif cid == "C-14":
        m["input"]["ledger_hash_after_registration"] = "0" * 32
    elif cid == "C-15":
        m["strategy_started"] = False


def run(root: Path, a: argparse.Namespace) -> int:
    if a.exit is not None:
        return a.exit
    if a.sleep:
        time.sleep(a.sleep)
    raw = (root / "input.json").read_bytes()
    inp = json.loads(raw.decode("utf-8"))
    lines = (root / "bars.csv").read_text(encoding="utf-8").splitlines()[1:]
    closes = [line.split(",")[2] for line in lines]
    ts = [int(line.split(",")[1]) for line in lines]
    sim = simulate(inp, closes, ts, a.fee_1x)
    m = manifest(inp, raw, ts, sim, {})
    if a.doctor:
        doctor(m, sim, a.doctor)
    m["hashes"] = {
        "fills.csv": write_csv(root / "fills.csv", ["ts_event", "order_side", "last_qty", "last_px", "commission",
                                                    "commission_ccy", "trade_id", "venue_order_id"], sim["fills"]),
        "decisions.csv": write_csv(root / "decisions.csv", ["i", "ts_event", "decision", "margin", "action"],
                                   sim["decisions"]),
        "onbar_equity.csv": write_csv(root / "onbar_equity.csv", ["i", "ts_event", "close", "cash", "qty",
                                                                  "equity_pre"], sim["equity"])}
    if a.no_manifest:
        return 0
    body = "{not json\n" if a.bad_json else json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    (root / "manifest.json").write_text(body, encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="nautilus_stub_child.py")
    ap.add_argument("--exit", type=int)
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--no-manifest", action="store_true")
    ap.add_argument("--bad-json", action="store_true")
    ap.add_argument("--doctor", choices=DOCTORS)
    ap.add_argument("--fee-1x", action="store_true")
    ap.add_argument("--selftest-wrong", action="store_true")
    ap.add_argument("--check-env", action="store_true")
    ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv)
    if a.check_env:
        u = platform.uname()
        print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                          "system": u.system, "machine": u.machine, "environment": "BACKTEST",
                          "precision": PRECISION}))
        return 0
    if a.guard_selftest:
        out = dict(SELFTEST, sandbox="passed") if a.selftest_wrong else dict(SELFTEST)
        print(json.dumps(out, sort_keys=True))
        return 0
    if a.probe:
        print(json.dumps({"blocked": True, "errno": 101, "error": "stub"}))
        return 0
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute():
        return 20
    return run(root, a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```
  Check it on F1 and F2 through the launch contract (the runner does not exist yet, so every test row stays as in Step 2):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -c "
import json, sys
from pathlib import Path
from tools.nautilus import launch
for name in ('F1', 'F2'):
    raw, bars = launch.fixture_inputs(name)
    tmp = launch.make_tempdir()
    (tmp / 'input.json').write_bytes(raw)
    (tmp / 'bars.csv').write_bytes(bars)
    child = launch.build_launch(['run', '--in', str(tmp)], tempdir=tmp, venv_python=None, unshare=launch.resolve_unshare(),
                                child_cmd=[sys.executable, '-I', str(Path('tests/nautilus_stub_child.py').resolve())])
    res = launch.run_child(child, timeout=60)
    m = json.loads((tmp / 'manifest.json').read_text(encoding='utf-8'))
    fills = [r.split(',')[1:5] for r in (tmp / 'fills.csv').read_text(encoding='utf-8').splitlines()[1:]]
    print(name, res.returncode, m['valid'], m['result']['account_balance_usd'], m['result']['final_qty'], fills, launch.cleanup_tempdir(tmp))
"
```
  Expected (spec 8.2's fills, to the cent):
```
F1 0 True 926593.00 0 [['BUY', '10000', '100.000000000', '5000.00'], ['SELL', '10000', '96.000000000', '4800.00'], ['BUY', '9600', '99.000000000', '4752.00'], ['SELL', '9600', '97.000000000', '4656.00']] []
F2 0 True 50343.77 0 [['BUY', '1.00000000', '53000.000000000', '53.00'], ['SELL', '1.00000000', '50000.000000000', '50.00'], ['BUY', '0.98812079', '50500.000000000', '49.90'], ['SELL', '0.98812079', '51000.000000000', '50.39']] []
```

- [ ] **Step 4: Create the runner.** Create `tools/nautilus/runner.py` with this exact content (LF). Every function is under 60 lines. It holds spec 5.3: the CLI, argument validation, steps 0 to 15 as one pure function or one short step function each, the census judgement, `record_baseline`, `write_record`, the run lifecycle with its `try/finally`, and the `parity_and_gate` seam whose body is exactly C10's; Task 5 replaces only that body. CONTRACT ISSUE 2 is in `check_p0a` (its `arrays` also carry `symbol` and `start`; it returns the Panel), CONTRACT ISSUE 3 in `record_baseline`'s `python` keyword, CONTRACT ISSUE 4 in `e1_parity_passed`.
```python
"""The parent of the NautilusTrader bridge (spec 2026-10-26 section 5.3), run in the global interpreter.

    python -B -m tools.nautilus.runner --table <t> --rehearsal --ledger-dir <tmp> --out-dir <tmp> [--child-cmd <json>]
    python -B -m tools.nautilus.runner --table <t> --of-record [--rerun-of <id> --reason <text>]
    python -B -m tools.nautilus.runner --check-env | --egress-record | --fixtures [--record-baseline | --write-goldens]

A run registers every variant in its family ledger before any child starts, computes QUANTGEN's reference matrices
with `simulate`, starts one child per (column, cost level) through the launch contract of launch.py, rebuilds each
child's daily returns from its fills (5.3.3) and checks every child (section 7). Steps 16 and 17 (parity, gate and
card) sit behind `parity_and_gate`, which plan Task 5 fills. Exit codes: 0 card written, a clean rehearsal or a
mode's success; 1 WITHHELD; 2 refused before registration; 3 refused at registration; 4 ERROR; 5 ABORTED. The last
console line of every mode is `STATUS <status> exit=<n> record=<path or ->`. The runner never imports the engine
(spec 5.6 rule C2); it reads the venv's own files through launch.py.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import types
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path, PurePath
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

from core.quant import gate_ledger, validate
from core.quant import strategies as S
from tools.nautilus import launch
from tools.nautilus.launch import BridgeRefusal, ChildInvalid

for _stream in (sys.stdout, sys.stderr):              # spec 3.7: the house locale is cp949
    with contextlib.suppress(Exception):
        _stream.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = launch.REPO_ROOT
STUDY_FILE = Path("docs") / "asset_expansion_study.py"
DGS3MO_FILE = "docs/asset_expansion/cache/fred_DGS3MO.csv"
SCRIPT = "tools/nautilus/runner.py"
STATUSES = ("IN_PROGRESS", "CARD_WRITTEN", "WITHHELD", "REFUSED_REGISTRATION", "ERROR", "ABORTED")
SELFTEST = {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}
TABLE_SCHEMA, INPUT_SCHEMA, RUN_SCHEMA = "nautilus-bridge-table/1", "nautilus-bridge-input/2", "nautilus-bridge-run/2"
GOLDEN_SCHEMA, CENSUS_SCHEMA = "nautilus-bridge-golden/1", "nautilus-bridge-census/1"
EGRESS_SCHEMA = "nautilus-bridge-egress/1"
FRESH_S = 600                                       # R-16: a ledger written less than 600 s ago
PRICE_DECIMALS = 9                                  # 5.3.2 step 5: closes = np.round(raw, 9), the one rounding
PINNED_REAL_MD5 = {"SPY": "d2164597d576e1b2fcadde063065811d", "BTC-USD": "bc76f530ff24ab445367fe826150bc10"}
LAYER = "QUANTGEN-nautilus-block-out" if os.name == "nt" else "unshare -rn"
GOLDEN_FIXTURES = ("F1", "F2", "N1")
DENIED_CENSUS = ("nautilus_trader.adapters", "nautilus_trader.network")      # 5.2.7 (C-08)
CRYPTO_DEFAULTS = {"lookbacks": [7, 14, 21, 28], "mas": [10, 20, 50, 100, 200]}
FN = {"trend_switch": S.trend_switch, "crypto_trend": S.crypto_trend}
SHAPES = {"trend_switch": {"family_id": "E1", "instrument": "SPY", "keys": ({"rule", "lookback", "step"},)},
          "crypto_trend": {"family_id": "C3", "instrument": "BTC/USD",
                           "keys": ({"hysteresis"}, {"hysteresis", "lookbacks", "mas"})}}
PILOTS = {"E1-SPY": {"strategy": "trend_switch", "family_id": "E1", "rule": "E1", "market": "US", "symbol": "SPY",
                     "instrument": "SPY", "size_precision": 0},
          "C3-BTCUSD": {"strategy": "crypto_trend", "family_id": "C3", "rule": "C3", "market": "CRYPTO",
                        "symbol": "BTC-USD", "instrument": "BTC/USD", "size_precision": 8}}
PILOT_VALUES = {"capital_usd": "1000000", "price_precision": 9, "volume": "1000000000", "fill_seed": 42}
TABLE_TYPES = {                                     # spec 6.6: field -> (types, null allowed)
    "schema": ((str,), False), "pilot": ((str,), False), "family_id": ((str,), False), "rule": ((str,), False),
    "market": ((str,), False), "strategy": ((str,), False), "symbol": ((str,), False), "instrument": ((str,), False),
    "prices_file": ((str,), False), "prices_md5": ((str,), False), "start": ((str,), False), "end": ((str,), False),
    "rf_file": ((str,), True), "rf_md5": ((str,), True), "axes": ((dict,), False), "grid": ((list,), False),
    "cost_bps": ((int, float), False), "embargo": ((int,), False), "capital_usd": ((str,), False),
    "price_precision": ((int,), False), "size_precision": ((int,), False), "volume": ((str,), False),
    "fill_seed": ((int,), False), "domain": ((dict,), True), "hypothesis": ((str,), False),
    "claim_label": ((str,), False), "card_id": ((str,), False), "study_configs": ((list,), False),
    "reference_card": ((str,), True), "reference_card_md5": ((str,), True)}
OWNER_FIELDS = ("owner_confirmed", "host_fingerprint")
FILLS_HEADER = ("ts_event", "order_side", "last_qty", "last_px", "commission", "commission_ccy", "trade_id",
                "venue_order_id")
DECISIONS_HEADER = ("i", "ts_event", "decision", "margin", "action")
EQUITY_HEADER = ("i", "ts_event", "close", "cash", "qty", "equity_pre")
REMEDY = {                                          # section 7's Remedy column, printed after the message
    "R-01": "commit or remove the printed paths",
    "R-02": 'packed ref: git commit --allow-empty -m "nautilus: re-anchor", then git push; worktree: use the main clone',
    "R-03": launch.VENV_FIX,
    "R-04": "restore the pinned bytes; new bytes need an owner ruling",
    "R-05": "as R-04: restore the pinned bytes; new bytes need an owner ruling",
    "R-06": "as R-04: restore the pinned bytes; new bytes need an owner ruling",
    "R-07": "a table cost at or above the printed floor",
    "R-08": "restore GATE (git diff core/quant/validate.py)",
    "R-09": "stop; an owner ruling",
    "R-10": "temp dirs; synthetic data only",
    "R-11": "fix the printed field; after a change, --fingerprint and a new owner_confirmed (7A.3); pilot 1 first "
            "(Step 8)",
    "R-12": "read the traceback; the rows stay; re-run under R-17",
    "R-13": "stop; an owner ruling",
    "R-14": ("Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Get-NetFirewallApplicationFilter and "
             "Get-NetFirewallProfile | Select Name, Enabled (a third-party firewall can disable these rules); if the "
             "filter's Program is not <printed path>\\py313\\python.exe, or the rule is disabled or not -Profile Any, "
             "the two elevated firewall lines of 7A.2 again, the first removing the rule by name and the second "
             "creating it; then --egress-record" if os.name == "nt" else "a Linux host with user namespaces"),
    "R-15": "the owner rules how the ledger starts (O11); --fingerprint on this host",
    "R-16": "wait the printed seconds, or end the runner holding the printed lock",
    "R-17": '--rerun-of <id> --reason "<text>"'}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_HEX = {32: re.compile(r"[0-9a-f]{32}"), 64: re.compile(r"[0-9a-f]{64}")}
_MISSING = object()
_TEMP_ROOTS: tuple[str, str] | None = None


def refuse(rid: str, message: str) -> BridgeRefusal:
    """A section-7 refusal with its remedy: `raise refuse("R-05", "...")`."""
    return BridgeRefusal(rid, message, REMEDY[rid])


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(path))


def _under(path: str, root: str) -> bool:
    return path.startswith(root.rstrip(os.sep) + os.sep)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _json_text(obj) -> str:
    """C1: every JSON file the bridge writes, except input.json and the card."""
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def _int_text(x, lo: int, hi: float) -> bool:
    return isinstance(x, str) and x.isascii() and x.isdigit() and x == str(int(x)) and lo <= int(x) <= hi


def _is_int(x, lo: int, hi: int) -> bool:
    return type(x) is int and lo <= x <= hi


# --------------------------------------------------------------------------- #
# Temp root, digests, run id (spec 3.9, 6.6, 5.3.5)
# --------------------------------------------------------------------------- #
def temp_roots() -> tuple[str, str]:
    """The temp root in its two forms, computed once per process (3.9; OPS-R4-4)."""
    global _TEMP_ROOTS
    if _TEMP_ROOTS is None:
        d = tempfile.mkdtemp(prefix="qgnb_root_")
        os.rmdir(d)
        _TEMP_ROOTS = (_norm(tempfile.gettempdir()), _norm(os.path.dirname(d)))
    return _TEMP_ROOTS


def inside_temp_root(path) -> bool:
    """True for an absolute path under either form of the temp root and not under the repository (3.9)."""
    if not os.path.isabs(str(path)):
        return False
    p = _norm(path)
    return any(_under(p, root) for root in temp_roots()) and not _under(p, _norm(REPO_ROOT)) and p != _norm(REPO_ROOT)


def table_sha256(table: dict) -> str:
    """6.6: the SHA-256 of the table's sorted, compact JSON without owner_confirmed and host_fingerprint."""
    t = {k: v for k, v in table.items() if k not in OWNER_FIELDS}
    return hashlib.sha256(json.dumps(t, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def code_paths(repo_root: Path) -> list[Path]:
    """6.6: tools/nautilus/**/*.py, tools/nautilus/golden/*.json, requirements-nautilus.txt, the harness sources,
    docs/asset_expansion_study.py and config.py, sorted."""
    from core.quant.gate_package import HARNESS_SOURCES
    root = Path(repo_root)
    found = set((root / "tools" / "nautilus").rglob("*.py")) | set((root / "tools" / "nautilus" / "golden").glob("*.json"))
    found |= {root / p for p in ("requirements-nautilus.txt", *HARNESS_SOURCES, STUDY_FILE.as_posix(), "config.py")}
    return sorted(found)


def code_digest(repo_root: PurePath, paths: Sequence[PurePath], read: Callable[[PurePath], bytes]) -> str:
    """6.6: the SHA-256 of the sorted lines "<path relative to the root, as posix>,<sha256 of its bytes>"."""
    lines = sorted(f"{p.relative_to(repo_root).as_posix()},{hashlib.sha256(read(p)).hexdigest()}" for p in paths)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def code_sha256(repo_root: Path) -> str:
    return code_digest(Path(repo_root), code_paths(repo_root), lambda p: Path(p).read_bytes())


def host_fingerprint(hostname: str, ledger: gate_ledger.FamilyLedger) -> str | None:
    """6.6: sha256(hostname + "\\n" + the family ledger's first row_md5); None when the ledger holds no row."""
    rows = ledger.rows()
    if not rows:
        return None
    return hashlib.sha256((hostname + "\n" + rows[0]["row_md5"]).encode("utf-8")).hexdigest()


def bridge_run_id(now: datetime, table_sha256: str) -> str:
    """5.3.5: NB-<UTC %Y%m%dT%H%M%S%fZ>-<first 8 hex of table_sha256>; outside every result hash."""
    return f"NB-{now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{table_sha256[:8]}"


# --------------------------------------------------------------------------- #
# Step 0: lock, freshness, earlier runs (5.3.5; R-16, R-17)
# --------------------------------------------------------------------------- #
class TableLock:
    """A non-blocking OS lock on <out root>/.locks/<16 hex>.lock, held for the whole run."""

    def __init__(self, path: Path, fh) -> None:
        self.path, self._fh = path, fh

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fh, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            self._fh.close()
            self._fh = None


def _earlier_runs(out_root: Path, table_sha: str) -> tuple[list[dict], list[str]]:
    """Every earlier run record of this table, best effort, and the ones the re-run policy does not pass."""
    earlier, blocking = [], []
    for path in sorted(out_root.glob(f"NB-*-{table_sha[:8]}/run.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            if rec["table"]["table_sha256"] != table_sha:
                continue
            entry = {"bridge_run_id": rec["bridge_run_id"], "status": rec["status"]}
            reasons = rec.get("withheld_reasons") or []
            ok = rec["status"] in ("IN_PROGRESS", "ABORTED", "ERROR") or (
                rec["status"] == "WITHHELD" and bool(reasons) and all(str(r).startswith("C-06") for r in reasons))
        except (OSError, ValueError, KeyError, TypeError):
            entry, ok = {"bridge_run_id": path.parent.name, "status": "UNREADABLE"}, False
        earlier.append(entry)
        if not ok:
            blocking.append(f"{entry['bridge_run_id']} {entry['status']}")
    return earlier, blocking


def take_lock(out_root: Path, table_sha256: str, ledger_paths: Sequence[Path], rerun_of: str | None
              ) -> tuple[TableLock, list[dict]]:
    """Step 0: the table lock (R-16 when held), the freshness of C3.jsonl and the family ledger (R-16 under 600 s),
    the earlier records of this table and the re-run policy (R-17). Returns the lock and earlier_runs."""
    locks = Path(out_root) / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    path = locks / f"{table_sha256[:16]}.lock"
    fh = open(path, "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise refuse("R-16", f"another runner is active: it holds {path}")
    lock = TableLock(path, fh)
    try:
        now = time.time()
        for ledger in ledger_paths:
            if Path(ledger).exists() and now - Path(ledger).stat().st_mtime < FRESH_S:
                wait = FRESH_S - (now - Path(ledger).stat().st_mtime)
                raise refuse("R-16", f"{ledger} was modified less than {FRESH_S} s ago; wait {wait:.0f} s")
        earlier, blocking = _earlier_runs(Path(out_root), table_sha256)
        if blocking and rerun_of is None:
            raise refuse("R-17", f"earlier runs of this table: {', '.join(blocking)}")
        if rerun_of is not None and rerun_of not in {e["bridge_run_id"] for e in earlier}:
            raise refuse("R-17", f"--rerun-of {rerun_of} names no earlier run of this table")
        return lock, earlier
    except BaseException:
        lock.release()
        raise


# --------------------------------------------------------------------------- #
# Step 1: the registration table (6.6; R-10, R-11, R-15, R-09)
# --------------------------------------------------------------------------- #
def load_table(path: Path) -> tuple[dict, bytes]:
    """The table as one JSON object, read with utf-8-sig (3.7), and its raw bytes; R-11 otherwise."""
    try:
        raw = Path(path).read_bytes()
        table = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise refuse("R-11", f"the table {path} is not readable JSON: {exc}") from exc
    if not isinstance(table, dict):
        raise refuse("R-11", f"the table {path} is not a JSON object")
    return table, raw


def _check_place(t: dict, mode: str, repo_root: Path) -> None:
    """R-10 (rehearsal) and R-11 (of-record) by place alone, before any data file is opened (QA-R4-2)."""
    named = {k: t.get(k) for k in ("prices_file", "rf_file", "reference_card") if t.get(k) is not None}
    if any(not isinstance(v, str) for v in named.values()):
        raise refuse("R-11", f"file fields must be strings: {named}")
    if mode == "rehearsal":
        bad = [k for k in ("prices_file", "reference_card") if k in named and not inside_temp_root(named[k])]
        rf = named.get("rf_file")
        if rf is not None and not inside_temp_root(rf) and _norm(Path(repo_root) / rf) != _norm(Path(repo_root) / DGS3MO_FILE):
            bad.append("rf_file")
        if bad:
            raise refuse("R-10", f"rehearsal files outside the temp root {temp_roots()}: "
                                 + ", ".join(f"{k}={named[k]!r}" for k in bad))
        return
    root = _norm(repo_root)
    bad = [k for k, v in named.items() if os.path.isabs(v) or not _under(_norm(Path(repo_root) / v), root)]
    if bad:
        raise refuse("R-11", "of-record files must be repo-relative paths inside the repository: "
                             + ", ".join(f"{k}={named[k]!r}" for k in bad))


def _check_fields(t: dict, mode: str) -> None:
    """R-11: exactly 6.6's fields, each of its type; the owner fields are required in of-record mode only."""
    unknown = sorted(set(t) - set(TABLE_TYPES) - set(OWNER_FIELDS))
    required = list(TABLE_TYPES) + (list(OWNER_FIELDS) if mode == "of-record" else [])
    missing = [k for k in required if k not in t]
    if unknown or missing:
        raise refuse("R-11", f"table fields: unknown {unknown}, missing {missing}")
    types_ = dict(TABLE_TYPES, **{k: ((str,), False) for k in OWNER_FIELDS})
    wrong = [k for k, (allowed, null) in types_.items() if k in t and not (
        (t[k] is None and null) or (isinstance(t[k], allowed) and not isinstance(t[k], bool)))]
    if wrong:
        raise refuse("R-11", "wrong types: " + ", ".join(f"{k}={t[k]!r}" for k in wrong))


def _check_column(strategy: str, theta) -> bool:
    """One grid column has exactly the strategy's keys, each in the child's range (6.1)."""
    if not isinstance(theta, dict) or set(theta) not in SHAPES[strategy]["keys"]:
        return False
    if strategy == "trend_switch":
        return theta["rule"] in ("sma", "tsmom") and _is_int(theta["lookback"], 1, 5000) and _is_int(theta["step"], 1, 5000)
    lists = [theta.get(k, CRYPTO_DEFAULTS[k]) for k in ("lookbacks", "mas")]
    return (type(theta["hysteresis"]) is float and 0.0 <= theta["hysteresis"] < 1.0
            and all(isinstance(v, list) and 1 <= len(v) <= 16 and all(_is_int(x, 1, 5000) for x in v) for v in lists))


def _check_values(t: dict, mode: str) -> None:
    """R-11: schema, pilot shape and values, dates, digests' form, child ranges and grid == grid_from(**axes)."""
    bad = []
    if t["schema"] != TABLE_SCHEMA:
        bad.append(f"schema {t['schema']!r}")
    if (mode == "of-record") != (t["pilot"] in PILOTS) or (mode == "rehearsal" and t["pilot"] != "rehearsal"):
        bad.append(f"pilot {t['pilot']!r} in {mode} mode")
    shape = SHAPES.get(t["strategy"])
    if shape is None or t["family_id"] != shape["family_id"] or t["rule"] != t["family_id"] or t["instrument"] != shape["instrument"]:
        bad.append(f"strategy {t['strategy']!r}, family_id {t['family_id']!r}, rule {t['rule']!r}, "
                   f"instrument {t['instrument']!r} do not form a pilot shape")
    if mode == "of-record" and t["pilot"] in PILOTS:
        bad += [f"{k} {t.get(k)!r} (pilot value {v!r})" for k, v in {**PILOTS[t["pilot"]], **PILOT_VALUES}.items()
                if t.get(k) != v]
    if not (_DATE.fullmatch(t["start"]) and _DATE.fullmatch(t["end"]) and t["start"] <= t["end"]):
        bad.append(f"start {t['start']!r} and end {t['end']!r}")
    if not _HEX[32].fullmatch(t["prices_md5"]) or (t["rf_file"] is None) != (t["rf_md5"] is None) or (
            t["rf_md5"] is not None and not _HEX[32].fullmatch(t["rf_md5"])):
        bad.append("prices_md5, rf_file or rf_md5")
    if (t["reference_card"] is None) != (t["reference_card_md5"] is None):
        bad.append("reference_card and reference_card_md5 go together")
    if not re.fullmatch(r"[A-Za-z0-9.^=-]+", t["symbol"]):
        bad.append(f"symbol {t['symbol']!r}")
    if not (0.0 <= float(t["cost_bps"]) <= 1000.0) or t["embargo"] < 0:
        bad.append(f"cost_bps {t['cost_bps']!r} or embargo {t['embargo']!r}")
    if not (_int_text(t["capital_usd"], 1, 9223372036) and t["price_precision"] == PRICE_DECIMALS
            and _is_int(t["size_precision"], 0, 9) and _int_text(t["volume"], 1, 18446744073)
            and _is_int(t["fill_seed"], 0, 2**32 - 1)):
        bad.append("capital_usd, price_precision (9), size_precision, volume or fill_seed outside spec 6.1 and 3.6")
    if not all(isinstance(v, list) for v in t["axes"].values()) or t["grid"] != S.grid_from(**t["axes"]):
        bad.append("grid differs from grid_from(**axes), whose order follows the axes keys (keep the study's call order)")
    elif shape is not None and not (t["grid"] and all(_check_column(t["strategy"], g) for g in t["grid"])):
        bad.append("a grid column has the wrong keys or a value outside spec 6.1")
    if not all(isinstance(c, dict) and set(c) == {"source", "symbols", "cost_bps", "params"} for c in t["study_configs"]):
        bad.append("study_configs entries are {source, symbols, cost_bps, params}")
    if bad:
        raise refuse("R-11", "; ".join(bad))


def _check_reference(t: dict, repo_root: Path) -> None:
    """R-11: the reference card's bytes match reference_card_md5 (QUANT-R3-3)."""
    if t["reference_card"] is None:
        return
    path = Path(t["reference_card"]) if os.path.isabs(t["reference_card"]) else Path(repo_root) / t["reference_card"]
    try:
        found = hashlib.md5(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise refuse("R-11", f"reference_card {t['reference_card']!r} cannot be read: {exc}") from exc
    if found != t["reference_card_md5"]:
        raise refuse("R-11", f"reference_card md5 {found} differs from reference_card_md5 {t['reference_card_md5']}")


def e1_parity_passed(repo_root: Path, code: str) -> bool:
    """GOVERNANCE-R4-4: an of-record E1-SPY record under <repo>/docs/nautilus_bridge/runs/ with parity.hard_pass
    true, 12 registered columns and this code_sha256."""
    for path in sorted((Path(repo_root) / "docs" / "nautilus_bridge" / "runs").glob("*/run.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            if (rec["mode"], rec["pilot"], rec["table"]["code_sha256"]) == ("of-record", "E1-SPY", code) and (
                    rec["parity"]["hard_pass"] is True and len(rec["registration"]["rows"]) == 12):
                return True
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return False


def _check_of_record(t: dict, ledger_dir: Path, hostname: str, repo_root: Path) -> None:
    """R-11 (owner_confirmed, the pilot-2 preconditions), R-15 and R-09 (the family ledger), R-15 (the host)."""
    tsha, code = table_sha256(t), code_sha256(repo_root)
    m = re.fullmatch(r"(.+), (\d{4}-\d{2}-\d{2}), table ([0-9a-f]{16}), code ([0-9a-f]{16})", t["owner_confirmed"])
    if not m or (m[3], m[4]) != (tsha[:16], code[:16]):
        raise refuse("R-11", f"owner_confirmed {t['owner_confirmed']!r} does not quote this table and tree: "
                             f"table {tsha[:16]}, code {code[:16]}")
    if t["pilot"] == "C3-BTCUSD" and t["reference_card"] is None:
        raise refuse("R-11", "of-record C3-BTCUSD needs a reference_card (QUANT-R4-2)")
    if t["pilot"] == "C3-BTCUSD" and not e1_parity_passed(repo_root, code):
        raise refuse("R-11", f"of-record C3-BTCUSD needs an of-record E1-SPY record whose parity passed for all 12 "
                             f"columns at both cost levels under code {code[:16]} (GOVERNANCE-R4-4)")
    ledger = gate_ledger.family_ledger(t["family_id"], ledger_dir)
    if not ledger.path.is_file():
        raise refuse("R-15", f"the family ledger {ledger.path} does not exist")
    check = ledger.verify_chain()
    if not check:
        raise refuse("R-09", f"{ledger.path}: chain broken at line {check.first_bad_line}: {check.reason}")
    if check.n_rows == 0:
        raise refuse("R-15", f"the family ledger {ledger.path} holds no row")
    found = host_fingerprint(hostname, ledger)
    if t["host_fingerprint"] != found:
        raise refuse("R-15", f"host_fingerprint {t['host_fingerprint']!r} is not this host's {found}")


def check_table(table: Path, mode: str, ledger_dir: Path, hostname: str, repo_root: Path) -> dict:
    """Step 1 (5.3.2): the validated table. In rehearsal the place rule of 3.9 is judged first, before any file the
    table names is opened (R-10); then 6.6's fields and values (R-11), the reference card's md5 (R-11) and, in
    of-record mode, owner_confirmed, the pilot-2 preconditions (R-11), the family ledger (R-15, R-09) and the host
    fingerprint (R-15)."""
    t, _ = load_table(table)
    _check_place(t, mode, repo_root)
    _check_fields(t, mode)
    _check_values(t, mode)
    _check_reference(t, repo_root)
    if mode == "of-record":
        _check_of_record(t, Path(ledger_dir), hostname, repo_root)
    return t


# --------------------------------------------------------------------------- #
# Step 2: git (R-01, R-02)
# --------------------------------------------------------------------------- #
def _git(git_exe: str, repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([git_exe, "-C", str(repo_root), *args], stdin=subprocess.DEVNULL, capture_output=True,
                          encoding="utf-8", errors="replace", timeout=120)


def check_tree(repo_root: Path, anchor_fn: Callable[[Path], str], git_exe: str | None) -> dict:
    """Step 2's findings: HEAD, the ledger anchor, the porcelain entries (untracked under docs/nautilus_bridge/runs/
    exempt) and what is wrong with the anchor. Judged by tree_refusal."""
    found = {"head": None, "anchor": anchor_fn(repo_root), "clean": False, "porcelain": [], "porcelain_exempt": [],
             "offending": [], "anchor_problem": None}
    if git_exe is None:
        found["anchor_problem"] = "git is not on PATH"
        return found
    head = _git(git_exe, repo_root, "rev-parse", "HEAD")
    found["head"] = head.stdout.strip() if head.returncode == 0 else None
    status = _git(git_exe, repo_root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = status.stdout.split("\0") if status.returncode == 0 else [f"!! git status failed: {status.stderr.strip()}"]
    skip = False
    for entry in entries:
        if skip or not entry:
            skip = False
            continue
        skip = entry[0] in "RC"                         # a rename or copy: the source path follows
        found["porcelain"].append(entry)
        exempt = entry.startswith("?? docs/nautilus_bridge/runs/")
        found["porcelain_exempt" if exempt else "offending"].append(entry)
    found["clean"] = not found["offending"]
    git_path = Path(repo_root) / ".git"
    if found["head"] is None:
        found["anchor_problem"] = "git rev-parse HEAD failed"
    elif found["anchor"] == gate_ledger.UNVERSIONED and git_path.is_file():
        found["anchor_problem"] = f"the anchor is UNVERSIONED: {git_path} is a file, so this is a worktree; use the main clone"
    elif found["anchor"] == gate_ledger.UNVERSIONED and git_path.is_dir():
        found["anchor_problem"] = ('the anchor is UNVERSIONED: the branch ref is packed: run '
                                   '`git commit --allow-empty -m "nautilus: re-anchor"`, then `git push`')
    elif found["anchor"] != f"git:{found['head']}":
        found["anchor_problem"] = f"the anchor {found['anchor']} differs from HEAD {found['head']}"
    return found


def tree_refusal(findings: dict, mode: str) -> str | None:
    """R-02 (git missing, HEAD unreadable, anchor problem), R-01 (an offending entry); None in rehearsal."""
    if mode != "of-record":
        return None
    if findings["head"] is None:
        return "R-02"
    if findings["offending"]:
        return "R-01"
    return "R-02" if findings["anchor_problem"] else None


# --------------------------------------------------------------------------- #
# Steps 3 and 4: venv self-checks and egress (R-03, R-14)
# --------------------------------------------------------------------------- #
def venv_python_from_key() -> Path:
    """The venv python named by QUANTGEN_NAUTILUS_PYTHON (6.7); R-03 when the key is blank."""
    value = launch.venv_key()
    if not value:
        raise refuse("R-03", "QUANTGEN_NAUTILUS_PYTHON is not set")
    return launch.resolve_venv_python(value)


def launch_once(mode_args: list[str], *, python: Path | None, child_cmd: list[str] | None, unshare: str | None,
                timeout: float, script: Path = launch.SANDBOX) -> tuple[launch.ChildResult, dict | None]:
    """One short child in a fresh temp dir; returns its result and its last stdout line as JSON (or None)."""
    tmp = launch.make_tempdir()
    try:
        child = launch.build_launch(mode_args, tempdir=tmp, venv_python=python, unshare=unshare, child_cmd=child_cmd,
                                    script=script)
        res = launch.run_child(child, timeout=timeout)
    finally:
        launch.cleanup_tempdir(tmp)
    try:
        out = json.loads(res.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        out = None
    return res, out if isinstance(out, dict) else None


def check_venv(*, child_cmd: list[str] | None, unshare: str | None, timeout: float) -> dict:
    """Step 3: no nautilus-trader in the parent; the venv's reads match the pins (skipped with a stub child); the
    child's --check-env reports Python 3.13.x and BACKTEST; --guard-selftest exits 0 with 5.2.1's five outcomes.
    R-03 otherwise. Returns {"python", "reads", "check_env", "guard_selftest"}."""
    if launch.parent_nautilus() is not None:
        raise BridgeRefusal("R-03", f"nautilus-trader {launch.parent_nautilus()} is installed in the global "
                                    "interpreter", launch.PARENT_NAUTILUS_REMEDY)
    python = reads = None
    if child_cmd is None:
        python = venv_python_from_key()
        reads = launch.read_venv(python)
        bad = launch.venv_mismatches(reads)
        if bad:
            raise refuse("R-03", "the venv is off its pins: " + "; ".join(b.removeprefix("R-03: ") for b in bad))
    res, env = launch_once(["--check-env"], python=python, child_cmd=child_cmd, unshare=unshare, timeout=timeout)
    if res.returncode != 0 or env is None or env.get("schema") != "nautilus-bridge-check-env/1" or not str(
            env.get("python", "")).startswith("3.13.") or env.get("environment") != "BACKTEST" or set(
            env.get("precision") or {}) != {"HIGH_PRECISION", "FIXED_PRECISION", "QUANTITY_MAX", "PRICE_MAX"}:
        raise refuse("R-03", f"--check-env: exit {res.returncode}, output {res.stdout_tail[-300:]!r}, "
                             f"stderr {res.stderr_tail[-300:]!r}")
    res, sel = launch_once(["--guard-selftest"], python=python, child_cmd=child_cmd, unshare=unshare, timeout=timeout)
    if res.returncode != 0 or sel != SELFTEST:
        raise refuse("R-03", f"--guard-selftest misbehaved (QA-R2-10): exit {res.returncode}, outcomes {sel}")
    return {"python": python, "reads": reads, "check_env": env, "guard_selftest": sel}


def run_probe(*, python: Path | None, probe_cmd: list[str] | None, unshare: str | None) -> dict:
    """Step 4: the egress probe through the launch contract (probe_cmd replaces its argv); R-14 unless blocked."""
    if probe_cmd is None and python is None:
        python = venv_python_from_key()
    res, out = launch_once([], python=None if probe_cmd else python, child_cmd=probe_cmd, unshare=unshare,
                           timeout=60, script=launch.EGRESS_PROBE)
    if res.returncode != 0 or out is None or out.get("blocked") is not True:
        raise refuse("R-14", f"the egress probe was not blocked: exit {res.returncode}, output "
                             f"{res.stdout.strip()[-300:]!r}")
    return out


def check_egress_record(record_dir: Path, run_facts: dict) -> None:
    """Of-record step 4: the Step 7A record <record_dir>/<host tag>.json exists, proves the rule (probe blocked, the
    control connect ok) and names this run's venv python, base python and layer, paths compared as 4.3 says. R-14."""
    path = Path(record_dir) / f"{launch.host_tag()}.json"
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
        proved = rec["probe"]["blocked"] is True and rec["control_connect"]["ok"] is True
        named = {k: rec[k] for k in ("venv_python", "base_python", "layer")}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise refuse("R-14", f"no readable Step 7A egress record at {path}: {exc}") from exc
    if not proved:
        raise refuse("R-14", f"{path} does not prove the rule: probe {rec['probe']}, control {rec['control_connect']}")
    off = [k for k in ("venv_python", "base_python") if _norm(str(named[k] or "")) != _norm(str(run_facts[k] or ""))]
    off += ["layer"] if named["layer"] != run_facts["layer"] else []
    if off:
        raise refuse("R-14", f"{path} differs from this run in " + ", ".join(
            f"{k} (record {named[k]!r}, run {run_facts[k]!r})" for k in off))


def control_connect(host: str = "1.1.1.1", port: int = 443, timeout: float = 3) -> dict:
    """The parent's own connect for the egress record (4.4): it must succeed, so the record proves the rule."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"ok": True, "error": ""}
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------- #
# Steps 5 to 9: data, cash rate, P0a, cost, gate (R-04 to R-08, R-10, R-13)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Prices:
    md5: str
    kept: bytes                                     # the header and the kept lines, as read (P0a's trimmed cache)
    dates: tuple[str, ...]
    raw: np.ndarray
    closes: np.ndarray                              # np.round(raw, 9)
    ts: list[int]
    rounding_changed: bool


def bar_timestamps(dates: Sequence[str], instrument: str) -> list[int]:
    """5.2.4: SPY at 21:00 UTC on the date; BTC/USD at 00:00 UTC on the next calendar day (ns)."""
    epoch, day = date(1970, 1, 1), 86_400
    if instrument == "BTC/USD":
        return [((date.fromisoformat(d) - epoch).days + 1) * day * 10**9 for d in dates]
    return [((date.fromisoformat(d) - epoch).days * day + 21 * 3_600) * 10**9 for d in dates]


def check_round_trip(closes: np.ndarray, p: int = PRICE_DECIMALS) -> None:
    """5.2.4: float(f"{y:.{p}f}") == y for every close, so bars.csv carries the parent's floats exactly; R-05."""
    bad = [i for i, y in enumerate(np.asarray(closes, dtype=float)) if float(f"{y:.{p}f}") != y]
    if bad:
        raise refuse("R-05", f"{len(bad)} close(s) fail the {p}-decimal round trip, first at row {bad[0]}")


def load_prices(path: Path, *, md5: str, start: str, end: str, instrument: str, mode: str) -> Prices:
    """Step 5: the md5 (R-04; in rehearsal a pinned real md5 is R-10), the [start, end] filter on each line's date
    text before any value is parsed, the study's read (first column as index, dropna, values above zero), at least
    300 strictly increasing unique dates (R-05), the one rounding and its round trip (R-05)."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise refuse("R-04", f"the prices file is missing or unreadable: {exc}") from exc
    found = hashlib.md5(data).hexdigest()
    if mode == "rehearsal" and found in PINNED_REAL_MD5.values():
        raise refuse("R-10", f"{path} is a byte copy of a pinned real series (md5 {found}); rehearsals use "
                             "synthetic data only")
    if found != md5:
        raise refuse("R-04", f"{path}: md5 {found} differs from the table's {md5}")
    try:
        lines = data.decode("utf-8").splitlines(keepends=True)
        kept = "".join([lines[0]] + [x for x in lines[1:] if _DATE.fullmatch(x[:10]) and start <= x[:10] <= end])
        s = pd.read_csv(io.StringIO(kept), index_col=0, parse_dates=True).iloc[:, 0].dropna()
        s.index = pd.to_datetime(s.index)
        s = s[s > 0]
        raw = s.to_numpy(dtype=float)
    except (UnicodeDecodeError, ValueError, TypeError, IndexError, KeyError) as exc:
        raise refuse("R-04", f"{path} cannot be read as the study reads it: {exc}") from exc
    if len(s) < 300:
        raise refuse("R-05", f"{len(s)} sessions in [{start}, {end}]; the study needs 300")
    if not (s.index.is_monotonic_increasing and s.index.is_unique):
        raise refuse("R-05", "the dates are not strictly increasing and unique (a duplicated or swapped date)")
    closes = np.round(raw, PRICE_DECIMALS)
    check_round_trip(closes)
    dates = tuple(d.strftime("%Y-%m-%d") for d in s.index)
    return Prices(found, kept.encode("utf-8"), dates, raw, closes, bar_timestamps(dates, instrument),
                  bool(np.any(closes != raw)))


def load_rf(path: Path, *, md5: str, dates: Sequence[str]) -> tuple[np.ndarray, bytes]:
    """Step 6 (K8): DGS3MO read as study.fred reads it, dropna, forward-filled onto the panel dates, / 100 / 252;
    R-06 for a missing, unreadable or off-md5 file and for a NaN left after the fill. No 3 % fallback."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise refuse("R-06", f"the cash-rate file is missing or unreadable: {exc}") from exc
    if hashlib.md5(data).hexdigest() != md5:
        raise refuse("R-06", f"{path}: md5 {hashlib.md5(data).hexdigest()} differs from the table's {md5}")
    try:
        s = pd.read_csv(io.BytesIO(data), index_col=0, parse_dates=True).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        rf = (s.dropna().reindex(pd.to_datetime(list(dates)), method="ffill") / 100.0 / 252.0).to_numpy(dtype=float)
    except (ValueError, TypeError, IndexError, KeyError) as exc:
        raise refuse("R-06", f"{path} cannot be read as study.fred reads it: {exc}") from exc
    if np.isnan(rf).any():
        raise refuse("R-06", f"no DGS3MO observation on or before {dates[int(np.argmax(np.isnan(rf)))]}")
    return rf, data


def load_study(repo_root: Path) -> types.ModuleType:
    """docs/asset_expansion_study.py loaded by path (5.3.2 step 7); its import creates no file and reads no data."""
    spec = importlib.util.spec_from_file_location("qgnb_asset_expansion_study", Path(repo_root) / STUDY_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Blocked(types.ModuleType):
    """A raising stand-in for a download module (QA-R4-1): an attribute read records the attempt and raises."""

    def __getattr__(self, attr: str):
        if attr.startswith("__"):
            raise AttributeError(attr)
        self.log.append(f"{self.__name__}.{attr}")
        raise RuntimeError(f"download blocked: {self.__name__}.{attr}")


def check_p0a(study_module: types.ModuleType, cache_dir: Path, arrays: dict) -> Any:
    """Step 7, P0a (QUANT-1): with study.CACHE at cache_dir and raising stand-ins for yfinance and pandas_datareader
    in sys.modules (restored in finally), the study's own loaders must give byte-equal dates, 9-decimal closes and
    (when arrays["rf"] is not None) rf. arrays: symbol, start, dates, closes, rf. Returns study.panel's Panel; R-13."""
    if getattr(study_module, "REFRESH", None) is not False:
        raise refuse("R-13", "study.REFRESH is not False")
    study_module.CACHE = Path(cache_dir)
    log: list[str] = []
    names = ("yfinance", "pandas_datareader", "pandas_datareader.data")
    saved = {n: sys.modules.get(n, _MISSING) for n in names}
    for n in names:
        sys.modules[n] = stand = _Blocked(n)
        stand.log = log
    try:
        pn = study_module.panel({arrays["symbol"]: study_module.yf(arrays["symbol"])}, start=arrays["start"])
        rf = None if arrays["rf"] is None else np.asarray(study_module.rf_daily(pd.to_datetime(pn.dates)), dtype=float)
    except Exception as exc:                        # noqa: BLE001 - any loader failure is R-13
        raise refuse("R-13", f"the study's loaders raised {type(exc).__name__}: {exc}; blocked downloads {log}") from exc
    finally:
        for n, m in saved.items():
            if m is _MISSING:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
    diff = [] if tuple(pn.dates) == tuple(arrays["dates"]) else ["dates"]
    if np.round(np.asarray(pn.prices, dtype=float)[:, 0], 9).tobytes() != np.asarray(arrays["closes"], float).tobytes():
        diff.append("closes")
    if rf is not None and rf.tobytes() != np.asarray(arrays["rf"], dtype=float).tobytes():
        diff.append("rf")
    if diff:
        raise refuse("R-13", f"{', '.join(diff)} differ from the study's loaders; blocked downloads {log}")
    return pn


def check_cost(symbol: str, cost_bps: float) -> tuple[float, dict]:
    """Step 8 (K15): validate.cost_floor_bp; R-07 for an uncosted symbol or a table cost below the floor."""
    floor, classes = validate.cost_floor_bp([symbol])
    if floor is None:
        raise refuse("R-07", f"QUANTGEN has no cost row for {symbol} (classes {classes})")
    if cost_bps < floor:
        raise refuse("R-07", f"cost_bps {cost_bps:g} is below the floor {floor:g} bp for {symbol}")
    return floor, classes


def check_gate() -> dict:
    """Step 9: a deep copy of validate.GATE; R-08 unless bootstrap_B is 2000."""
    snapshot = copy.deepcopy(validate.GATE)
    if snapshot["bootstrap_B"] != 2000:
        raise refuse("R-08", f"GATE['bootstrap_B'] is {snapshot['bootstrap_B']}, not 2000")
    return snapshot


# --------------------------------------------------------------------------- #
# Step 11: the ledger row (6.4)
# --------------------------------------------------------------------------- #
def ledger_row(table: dict, theta: dict, *, span: Sequence[str], run_utc: str, anchor: str, bridge_run_id: str) -> dict:
    """6.4: the Lab's params expression (ui/strategy_lab_page.py:75-76) with cost_bps a float, so config_id equals
    the Lab's (K9); the engine tag sits in source, outside the key."""
    nt = launch.expected_versions()["nautilus-trader"]
    params = json.loads(json.dumps(dict(theta, symbols=sorted([table["symbol"]]), cost_bps=float(table["cost_bps"])),
                                   default=str))
    return {"rule": table["rule"], "params": params, "timing_class": "COMPLIANT", "span": [span[0], span[-1]],
            "market": table["market"], "run_utc": run_utc, "phase": "research", "script": SCRIPT,
            "run_kind": "variant", "run_utc_anchor": anchor,
            "source": f"nautilus-bridge {table['pilot']}; engines quantgen.simulate + nautilus_trader {nt}; "
                      f"run {bridge_run_id}"}


def registration_entry(col: int, result: gate_ledger.RegisterResult) -> dict:
    """The run record's row: result.row["row_md5"], never RegisterResult's third element (A-1)."""
    return {"col": col, "config_id": result.row["config_id"], "row_md5": result.row["row_md5"],
            "appended": result.appended}


# --------------------------------------------------------------------------- #
# The import census (5.2.7; C-08)
# --------------------------------------------------------------------------- #
def census_class(name: str, stdlib: frozenset[str] = frozenset(sys.stdlib_module_names)) -> str:
    """NT (nautilus_trader), STD (the parent's stdlib, site customisation, _sysconfigdata*) or TP."""
    top = name.split(".")[0]
    if top == "nautilus_trader":
        return "NT"
    if top in stdlib or top in ("sitecustomize", "usercustomize") or top.startswith("_sysconfigdata"):
        return "STD"
    return "TP"


def judge_census(census: Sequence[str], baseline: Sequence[str], *,
                 stdlib: frozenset[str] = frozenset(sys.stdlib_module_names)) -> list[str]:
    """C-08 reasons: a module at or under nautilus_trader.adapters or .network; an NT or TP set that differs from the
    baseline's, in either direction. STD names may differ (QA-11)."""
    out = []
    denied = sorted(n for n in census if any(n == p or n.startswith(p + ".") for p in DENIED_CENSUS))
    if denied:
        out.append(f"C-08: denied modules imported: {', '.join(denied)}")
    for cls in ("NT", "TP"):
        mine = {n for n in census if census_class(n, stdlib) == cls}
        base = {n for n in baseline if census_class(n, stdlib) == cls}
        if mine - base:
            out.append(f"C-08: {cls} names added: {', '.join(sorted(mine - base))}")
        if base - mine:
            out.append(f"C-08: {cls} names missing: {', '.join(sorted(base - mine))}")
    return out


def census_diff(old: Sequence[str], new: Sequence[str]) -> list[str]:
    """"+ <class> <name>" and "- <class> <name>" lines, sorted."""
    a, b = set(old), set(new)
    return [f"+ {census_class(n)} {n}" for n in sorted(b - a)] + [f"- {census_class(n)} {n}" for n in sorted(a - b)]


def load_baseline(tag: str, golden_dir: Path = launch.GOLDEN_DIR) -> list[str] | None:
    path = Path(golden_dir) / f"modules_{tag}.json"
    return json.loads(path.read_text(encoding="utf-8"))["census"] if path.is_file() else None


def record_baseline(golden_dir: Path, tag: str, census: Sequence[str], *, tracked: bool,
                    python: str | None = None) -> tuple[int, list[str]]:
    """5.2.7 (OPS-R3-2, OPS-R4-2, OPS-R5-3): a tracked equal baseline gives (0, ["unchanged"]); a tracked different
    one writes nothing and gives (2, its diff and the removal line); an untracked one, or a tracked path with no
    file, is written and gives (0, its diff and "written <name>")."""
    path = Path(golden_dir) / f"modules_{tag}.json"
    new = sorted(set(census))
    old = None
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))["census"]
        except (OSError, ValueError, KeyError, TypeError):
            old = []
    diff = census_diff(old or [], new)
    if old is not None and tracked:
        if old == new:
            return 0, ["unchanged"]
        removal = (f"Remove-Item tools\\nautilus\\golden\\{path.name}" if os.name == "nt"
                   else f"rm tools/nautilus/golden/{path.name}")
        return 2, diff + [f"{path.name} is tracked and differs; review the diff above, then remove it with:", removal]
    obj = {"schema": CENSUS_SCHEMA, "platform_tag": tag, "python": python or platform.python_version(),
           "recorded_from": ["F1", "F2"], "census": new}
    path.write_text(_json_text(obj), encoding="utf-8", newline="\n")
    return 0, diff + [f"written {path.name}"]


# --------------------------------------------------------------------------- #
# The run record (5.3.5; OPS-R2-3)
# --------------------------------------------------------------------------- #
def write_record(path: Path, obj: dict, *, replace=os.replace, sleep=time.sleep) -> None:
    """mkstemp in the same folder, fsync, replace; up to 10 attempts 0.5 s apart on PermissionError; then raises."""
    data = _json_text(obj)
    last: PermissionError | None = None
    for attempt in range(10):
        if attempt:
            sleep(0.5)
        fd, tmp = tempfile.mkstemp(prefix=".run.", suffix=".tmp", dir=Path(path).parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            replace(tmp, path)
            return
        except PermissionError as exc:
            last = exc
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
    raise last


# --------------------------------------------------------------------------- #
# Child outputs, return reconstruction and reconciliation (5.2.6, 5.3.3; C-09)
# --------------------------------------------------------------------------- #
def _rows(path: Path, header: tuple[str, ...]) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != header:
            raise ValueError(f"{Path(path).name}: header {reader.fieldnames}, expected {list(header)}")
        return list(reader)


def parse_fills(path: Path) -> list[dict]:
    return [{"ts_event": int(r["ts_event"]), "order_side": r["order_side"], "last_qty": Decimal(r["last_qty"]),
             "last_px": Decimal(r["last_px"]), "commission": Decimal(r["commission"]),
             "commission_ccy": r["commission_ccy"], "trade_id": r["trade_id"], "venue_order_id": r["venue_order_id"]}
            for r in _rows(path, FILLS_HEADER)]


def parse_decisions(path: Path) -> list[dict]:
    return [{"i": int(r["i"]), "ts_event": int(r["ts_event"]), "decision": int(r["decision"]),
             "margin": float(r["margin"]), "action": r["action"]} for r in _rows(path, DECISIONS_HEADER)]


def parse_equity(path: Path) -> list[dict]:
    return [{"i": int(r["i"]), "ts_event": int(r["ts_event"]), "close": Decimal(r["close"]), "cash": Decimal(r["cash"]),
             "qty": Decimal(r["qty"]), "equity_pre": Decimal(r["equity_pre"])} for r in _rows(path, EQUITY_HEADER)]


@dataclass(frozen=True)
class Rebuilt:                                      # 5.3.3
    R: np.ndarray
    TV: np.ndarray
    E_minus: np.ndarray
    cash: list[Decimal]
    q: list[Decimal]
    fill_bars: list[int]
    final_cash: Decimal


def _px(closes) -> list[Decimal]:
    return [Decimal(f"{c:.{PRICE_DECIMALS}f}") for c in np.asarray(closes, dtype=float)]


def rebuild_returns(fills: list[dict], closes: np.ndarray, ts: Sequence[int], rf: np.ndarray,
                    capital: Decimal) -> Rebuilt:
    """5.3.3: cash and position after each bar's fills, in Decimal, from cash(-1) = capital and q(-1) = 0;
    E-(t) = cash(t-1) + q(t-1) P(t); R(t) = E-(t+1) / E-(t) - 1 + (cash(t) / E-(t)) rf(t) and
    TV(t) = sum of qty x px at bar t / E-(t), for t = 0 .. T-2. C-09 for a fill off every bar timestamp."""
    bar = {t: i for i, t in enumerate(ts)}
    per_bar: list[list[dict]] = [[] for _ in ts]
    fill_bars = []
    for f in fills:
        if f["ts_event"] not in bar or f["order_side"] not in ("BUY", "SELL"):
            raise ChildInvalid("C-09", f"fill at ts_event {f['ts_event']} side {f['order_side']} is not on a bar")
        per_bar[bar[f["ts_event"]]].append(f)
        fill_bars.append(bar[f["ts_event"]])
    P, cash, q = _px(closes), Decimal(capital), Decimal(0)
    e_minus, cash_l, q_l, traded = [], [], [], []
    for t in range(len(ts)):
        e_minus.append(cash + q * P[t])
        value = Decimal(0)
        for f in per_bar[t]:
            notional = f["last_qty"] * f["last_px"]
            value += notional
            if f["order_side"] == "BUY":
                cash, q = cash - notional - f["commission"], q + f["last_qty"]
            else:
                cash, q = cash + notional - f["commission"], q - f["last_qty"]
        traded.append(value)
        cash_l.append(cash)
        q_l.append(q)
    T = len(ts)
    R = np.array([float(e_minus[t + 1] / e_minus[t]) - 1.0 + float(cash_l[t] / e_minus[t]) * float(rf[t])
                  for t in range(T - 1)])
    TV = np.array([float(traded[t] / e_minus[t]) for t in range(T - 1)])
    return Rebuilt(R=R, TV=TV, E_minus=np.array([float(e) for e in e_minus]), cash=cash_l, q=q_l,
                   fill_bars=fill_bars, final_cash=cash)


def reconcile(rebuilt: Rebuilt, equity: list[dict], closes: np.ndarray, ts: Sequence[int], capital: Decimal,
              balance: str) -> list[str]:
    """5.3.3's cross-checks (C-09): onbar_equity.csv has n_bars rows on the bar timestamps; the rebuilt E-(t) equals
    its equity_pre within $0.01 per fill so far; the final cash equals the manifest's balance within $0.01 per fill."""
    if len(equity) != len(ts):
        return [f"C-09: onbar_equity.csv has {len(equity)} rows; n_bars is {len(ts)}"]
    P, done, out = _px(closes), Counter(rebuilt.fill_bars), []
    so_far = 0
    for t, row in enumerate(equity):
        exact = (Decimal(capital) if t == 0 else rebuilt.cash[t - 1]) + (Decimal(0) if t == 0 else rebuilt.q[t - 1]) * P[t]
        if (row["i"], row["ts_event"]) != (t, ts[t]) or abs(exact - row["equity_pre"]) > Decimal("0.01") * so_far:
            out.append(f"C-09: bar {t}: equity_pre {row['equity_pre']} against the rebuilt {exact}")
            break
        so_far += done[t]
    if abs(rebuilt.final_cash - Decimal(balance)) > Decimal("0.01") * len(rebuilt.fill_bars):
        out.append(f"C-09: final cash {rebuilt.final_cash} against the account's {balance}")
    return out


def manifest_reasons(m: dict, *, n_bars: int, first_ts: int, last_ts: int, bars_sha256: str, input_sha256: str,
                     ledger_hash: str, check_env: dict) -> list[str]:
    """The parent's re-derivation from manifest.json (5.2.7, QA-R3-2, QA-R4-3): C-01 to C-04, C-15, C-07, C-11 and
    C-14, whatever the manifest's own `valid` says. A field missing is C-06."""
    try:
        r, inp, out = m["result"], m["input"], []
        if r["force_stop"] is not False:
            out.append("C-01: forced stop (re-derived from the manifest)")
        if r["bars_seen"] < n_bars or r["backtest_end"] is None or r["backtest_end"] < last_ts:
            out.append(f"C-02: bars seen {r['bars_seen']} of {n_bars}, backtest_end {r['backtest_end']}")
        if r["orders_not_filled"]:
            out.append(f"C-03: orders not FILLED: {r['orders_not_filled']}")
        if r["denied"] or r["rejected"]:
            out.append(f"C-04: {r['denied']} denied, {r['rejected']} rejected")
        if m["strategy_started"] is not True or m["environment"] != "BACKTEST":
            out.append(f"C-15: environment {m['environment']}, strategy_started {m['strategy_started']}")
        if m["precision"] != check_env["precision"] or m["environment"] != check_env["environment"]:
            out.append(f"C-07: manifest precision {m['precision']} differs from --check-env's {check_env['precision']}")
        echo = {"bars_sha256": bars_sha256, "bars_fed": n_bars, "first_ts": first_ts, "last_ts": last_ts,
                "input_json_sha256": input_sha256}
        off = [k for k, v in echo.items() if inp[k] != v]
        if off:
            out.append(f"C-11: manifest echoes differ from the parent's: {off}")
        if inp["ledger_hash_after_registration"] != ledger_hash:
            out.append(f"C-14: ledger hash echo {inp['ledger_hash_after_registration']} is not {ledger_hash}")
    except (KeyError, TypeError) as exc:
        return [f"C-06: manifest.json lacks a field of spec 6.2: {exc!r}"]
    return out


# --------------------------------------------------------------------------- #
# The run context and the seam for steps 16 and 17
# --------------------------------------------------------------------------- #
@dataclass
class Leg:                                          # one child: column `col`, cost level `stress` (1 or 2)
    col: int
    stress: int
    child: dict
    manifest: dict | None
    fills: list[dict]
    decisions: list[dict]
    equity: list[dict]
    rebuilt: Rebuilt | None
    invalid: list[str]


@dataclass
class RunContext:                                   # built by step 12; filled through step 15; read by Task 5
    mode: str
    repo_root: Path
    table: dict
    table_sha256: str
    code_sha256: str
    bridge_run_id: str
    run_dir: Path
    record: dict
    dates: tuple[str, ...]
    ts: list[int]
    closes: np.ndarray
    rf: np.ndarray
    study: types.ModuleType
    study_pn: Any
    grid: list[dict]
    fn: Callable
    weights: np.ndarray
    pnl_qg: np.ndarray
    pnl_stress_qg: np.ndarray
    turnover_qg: np.ndarray
    pnl_nt: np.ndarray
    pnl_stress_nt: np.ndarray
    turnover_nt: np.ndarray
    legs: dict[tuple[int, int], Leg]
    gate_snapshot: dict
    ledger: gate_ledger.FamilyLedger
    hash_after_registration: str
    score_fn: Callable
    hooks: dict
    stub_child: bool


@dataclass(frozen=True)
class Outcome:
    status: str                                     # "CARD_WRITTEN" | "WITHHELD" | "ERROR"
    exit_code: int                                  # 0 | 1 | 4
    withheld_reasons: list[str]


def parity_and_gate(ctx: RunContext) -> Outcome:
    """Steps 16 and 17 (spec 5.4, 5.5): plan Task 5 replaces this body with parity.hand_off(ctx)."""
    raise NotImplementedError("spec 5.4 and 5.5 are plan Task 5")


# --------------------------------------------------------------------------- #
# Child inputs (6.1) and one leg (steps 14 and 15)
# --------------------------------------------------------------------------- #
def child_params(table: dict, theta: dict) -> dict:
    """6.1's params: the grid column, with the study's crypto defaults filled in when it names only hysteresis."""
    if table["strategy"] == "crypto_trend":
        return {"hysteresis": float(theta["hysteresis"]), "lookbacks": list(theta.get("lookbacks", CRYPTO_DEFAULTS["lookbacks"])),
                "mas": list(theta.get("mas", CRYPTO_DEFAULTS["mas"]))}
    return {"rule": theta["rule"], "lookback": int(theta["lookback"]), "step": int(theta["step"])}


def cost_text(cost_bps) -> str:
    """The table's float cost as 6.1's decimal string: 50.0 -> "50", 12.5 -> "12.5"."""
    return format(Decimal(repr(float(cost_bps))).normalize(), "f")


def bars_bytes(closes: np.ndarray, ts: Sequence[int]) -> bytes:
    """bars.csv (C3): header i,ts_ns,close, LF, closes at 9 decimals."""
    rows = ["i,ts_ns,close"] + [f"{i},{t},{c:.{PRICE_DECIMALS}f}" for i, (t, c) in enumerate(zip(ts, closes))]
    return ("\n".join(rows) + "\n").encode("utf-8")


def input_bytes(table: dict, theta: dict, stress: int, bars: bytes, n_bars: int, ledger_hash: str) -> bytes:
    """input.json (C5): exactly 6.1's 14 keys, C1's compact sorted JSON, no trailing newline."""
    obj = {"schema": INPUT_SCHEMA, "strategy": table["strategy"], "params": child_params(table, theta),
           "instrument": table["instrument"], "capital_usd": table["capital_usd"], "cost_bps": cost_text(table["cost_bps"]),
           "stress": str(stress), "fill_seed": table["fill_seed"], "price_precision": PRICE_DECIMALS,
           "size_precision": table["size_precision"], "volume": table["volume"], "n_bars": n_bars,
           "bars_sha256": hashlib.sha256(bars).hexdigest(), "ledger_hash_after_registration": ledger_hash}
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _judge_leg(st: "_State", leg: Leg, res: launch.ChildResult, tmp: Path, raw: bytes, bars: bytes) -> None:
    """Step 15 for one child: C-06 (exit, timeout, missing or unparsable output), the manifest's own reasons, the
    parent's re-derivation, the census (C-08; skipped with a stub child) and the rebuild and reconciliation (C-09)."""
    c, bad, ctx = leg.child, leg.invalid, st.ctx
    c.update(returncode=res.returncode, ntstatus=res.ntstatus, timed_out=res.timed_out, seconds=res.seconds,
             stdout_tail=res.stdout_tail, stderr_tail=res.stderr_tail,
             census_sha256=hashlib.sha256("\n".join(res.census).encode("utf-8")).hexdigest())
    if res.timed_out:
        bad.append(f"C-06: timed out after {st.timeout:g} s; the process tree was killed")
    elif res.returncode not in (0, 10):
        bad.append(f"C-06: exit {res.returncode}" + (f" ({res.ntstatus})" if res.ntstatus else ""))
    try:
        m = json.loads((tmp / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(m, dict):
            raise ValueError("not a JSON object")
        leg.manifest = c["manifest"] = m
    except (OSError, ValueError) as exc:
        bad.append(f"C-06: manifest.json missing or not a JSON object: {type(exc).__name__}")
    parsed = False
    try:
        c["fills"] = _rows(tmp / "fills.csv", FILLS_HEADER)
        leg.fills, leg.decisions = parse_fills(tmp / "fills.csv"), parse_decisions(tmp / "decisions.csv")
        leg.equity, parsed = parse_equity(tmp / "onbar_equity.csv"), True
    except (OSError, ValueError, ArithmeticError) as exc:
        bad.append(f"C-06: an output CSV is missing or unreadable: {type(exc).__name__}: {exc}")
    m = leg.manifest
    if m is None:
        return
    bad += [r for r in m.get("invalid_reasons") or [] if r not in bad]
    if res.returncode in (0, 10) and (res.returncode == 0) != (m.get("valid") is True):
        bad.append(f"C-06: exit {res.returncode} with valid {m.get('valid')!r}")
    bad += manifest_reasons(m, n_bars=len(ctx.ts), first_ts=ctx.ts[0], last_ts=ctx.ts[-1],
                            bars_sha256=hashlib.sha256(bars).hexdigest(), input_sha256=hashlib.sha256(raw).hexdigest(),
                            ledger_hash=ctx.hash_after_registration, check_env=st.check_env_out)
    if not ctx.stub_child:
        tag = st.reads["wheel"]["platform_tag"]
        bad += (judge_census(res.census, st.baseline) if st.baseline is not None
                else [f"C-08: no census baseline modules_{tag}.json"])
    if parsed and not any(r.startswith("C-06") for r in bad):
        try:
            leg.rebuilt = rebuild_returns(leg.fills, ctx.closes, ctx.ts, ctx.rf, Decimal(ctx.table["capital_usd"]))
            bad += reconcile(leg.rebuilt, leg.equity, ctx.closes, ctx.ts, Decimal(ctx.table["capital_usd"]),
                             m["result"]["account_balance_usd"])
        except ChildInvalid as exc:
            bad.append(str(exc))
        except (ArithmeticError, KeyError, TypeError) as exc:
            bad.append(f"C-09: the rebuild failed: {type(exc).__name__}: {exc}")
    if not bad and not ctx.stub_child:
        st.record["census"].setdefault(st.reads["wheel"]["platform_tag"], res.census)


def _run_leg(st: "_State", col: int, stress: int) -> Leg:
    """Step 14 for one (column, cost level): a fresh temp dir with input.json and bars.csv, the launch contract,
    the child_started hook after Popen, then _judge_leg; the temp dir is removed whatever happens (OPS-R2-4)."""
    ctx = st.ctx
    bars = bars_bytes(ctx.closes, ctx.ts)
    raw = input_bytes(ctx.table, ctx.grid[col], stress, bars, len(ctx.ts), ctx.hash_after_registration)
    child = {"col": col, "stress": stress, "returncode": None, "ntstatus": None, "timed_out": False, "seconds": None,
             "manifest": None, "census_sha256": None, "fills": [], "stdout_tail": "", "stderr_tail": "", "invalid": []}
    leg = Leg(col, stress, child, None, [], [], [], None, child["invalid"])
    tmp = launch.make_tempdir()
    try:
        (tmp / "input.json").write_bytes(raw)
        (tmp / "bars.csv").write_bytes(bars)
        try:
            lc = launch.build_launch(["run", "--in", str(tmp)], tempdir=tmp, venv_python=st.python,
                                     unshare=st.unshare, child_cmd=st.child_cmd)
        except ChildInvalid as exc:                 # C-10: nothing launched
            leg.invalid.append(str(exc))
            return leg
        hook = st.hooks.get("child_started")
        st.record["times"]["first_child_utc"] = st.record["times"]["first_child_utc"] or _utc_now()
        res = launch.run_child(lc, timeout=st.timeout, on_started=(lambda: hook(lc)) if hook else None)
        _judge_leg(st, leg, res, tmp, raw, bars)
    finally:
        st.record["cleanup_leftovers"].extend(launch.cleanup_tempdir(tmp))
    return leg


# --------------------------------------------------------------------------- #
# The run lifecycle (5.3.2, 5.3.5)
# --------------------------------------------------------------------------- #
@dataclass
class _State:
    table_path: Path
    mode: str
    ledger_dir: Path | None
    out_dir: Path | None
    child_cmd: list[str] | None
    probe_cmd: list[str] | None
    hooks: dict
    hooks_given: bool
    timeout: float
    register_fn: Callable
    score_fn: Callable
    rerun_of: str | None
    reason: str | None
    repo_root: Path = REPO_ROOT
    out_root: Path | None = None
    record: dict = field(default_factory=dict)
    table: dict | None = None
    table_sha: str = ""
    run_id: str = ""
    lock: TableLock | None = None
    run_dir: Path | None = None
    python: Path | None = None
    reads: dict | None = None
    unshare: str | None = None
    check_env_out: dict | None = None
    prices: Prices | None = None
    rf: np.ndarray | None = None
    rf_bytes: bytes | None = None
    pn: Any = None
    study: Any = None
    p0a_dir: Path | None = None
    gate: dict | None = None
    ledger: Any = None
    baseline: list[str] | None = None
    ctx: RunContext | None = None
    awake: bool = False


def _new_record(st: _State) -> dict:
    return {"schema": RUN_SCHEMA, "read_only": True, "bridge_run_id": None, "mode": st.mode, "pilot": None,
            "stub_child": st.child_cmd is not None, "status": None, "withheld_reasons": [], "earlier_runs": [],
            "supersedes": st.rerun_of, "rerun_reason": st.reason,
            "times": {"started_utc": _utc_now(), "registered_utc": None, "first_child_utc": None, "finished_utc": None},
            "git": None, "table": None, "data": None, "provenance": None, "costs": None, "venv": None, "egress": None,
            "engine": None, "registration": None, "children": [], "census": {}, "parity": None, "gate": None,
            "card": None, "cleanup_leftovers": [], "record_write_failures": [], "error": None}


def _check_arguments(st: _State) -> None:
    """Argument validation, before step 0 writes anything: R-11 (mode, re-run pair, a seam or a directory in
    of-record mode, a malformed child_cmd), R-10 (rehearsal directories outside the temp root)."""
    if st.mode not in ("rehearsal", "of-record"):
        raise refuse("R-11", f"mode must be rehearsal or of-record, not {st.mode!r}")
    if (st.rerun_of is None) != (st.reason is None) or (st.reason is not None and not st.reason.strip()):
        raise refuse("R-11", "--rerun-of and a non-empty --reason go together")
    if st.mode == "of-record":
        seams = [n for n, used in (("child_cmd", st.child_cmd is not None), ("probe_cmd", st.probe_cmd is not None),
                                   ("hooks", st.hooks_given), ("timeout", st.timeout != launch.TIMEOUT_S),
                                   ("register_fn", st.register_fn is not gate_ledger.register_trial),
                                   ("score_fn", st.score_fn is not validate.score_strategy),
                                   ("ledger_dir", st.ledger_dir is not None), ("out_dir", st.out_dir is not None))
                 if used]
        if seams:
            raise refuse("R-11", f"of-record mode takes no test seam and no directory: {seams}")
        import config
        st.ledger_dir, st.out_root = config.macro_dir() / "ledgers", st.repo_root / "docs" / "nautilus_bridge" / "runs"
        return
    outside = [f"{n}={p!r}" for n, p in (("ledger_dir", st.ledger_dir), ("out_dir", st.out_dir))
               if p is None or not inside_temp_root(p)]
    if outside:
        raise refuse("R-10", f"rehearsal needs --ledger-dir and --out-dir inside the temp root {temp_roots()}: "
                             f"{', '.join(outside)}")
    for cmd in (st.child_cmd, st.probe_cmd):
        if cmd is not None and not (isinstance(cmd, list) and cmd and all(isinstance(c, str) for c in cmd)):
            raise refuse("R-11", f"a child or probe command must be a non-empty list of strings: {cmd!r}")
    st.ledger_dir, st.out_root = Path(st.ledger_dir), Path(st.out_dir)


def _hook(st: _State, n: int) -> None:
    fn = st.hooks.get(f"after_step{n}")
    if fn is not None:
        fn(st.ctx if n >= 12 else None)


def _step0(st: _State) -> None:
    """Lock, freshness and earlier runs (5.3.5): the table is parsed only for table_sha256 (R-11 when not JSON)."""
    table, _ = load_table(st.table_path)
    st.table_sha = table_sha256(table)
    st.run_id = bridge_run_id(datetime.now(timezone.utc), st.table_sha)
    fid = table.get("family_id")
    family = [st.ledger_dir / f"{fid}.jsonl"] if isinstance(fid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", fid) else []
    st.lock, earlier = take_lock(st.out_root, st.table_sha, [st.ledger_dir / "C3.jsonl", *family], st.rerun_of)
    st.record.update(bridge_run_id=st.run_id, earlier_runs=earlier)
    for e in earlier:
        if e["status"] in ("IN_PROGRESS", "ABORTED"):
            print(f"earlier run {e['bridge_run_id']} ended {e['status']}")
    if os.name == "nt":                             # OPS-R3-8: keep the machine awake while the run lasts
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
        st.awake = True


def _step1(st: _State) -> None:
    st.table = check_table(st.table_path, st.mode, st.ledger_dir, socket.gethostname(), st.repo_root)
    raw = st.table_path.read_bytes()
    st.record.update(pilot=st.table["pilot"], table={
        "path": str(st.table_path), "raw_sha256": hashlib.sha256(raw).hexdigest(), "table_sha256": st.table_sha,
        "code_sha256": code_sha256(st.repo_root), "table": st.table})


def _step2(st: _State) -> None:
    found = check_tree(st.repo_root, gate_ledger.repo_anchor, shutil.which("git"))
    rid = tree_refusal(found, st.mode)
    if rid is not None:
        raise refuse(rid, "; ".join(found["offending"]) if rid == "R-01" else str(found["anchor_problem"]))
    st.record["git"] = found


def _step3(st: _State) -> None:
    st.unshare = launch.resolve_unshare()
    v = check_venv(child_cmd=st.child_cmd, unshare=st.unshare, timeout=st.timeout)
    st.python, st.reads, st.check_env_out = v["python"], v["reads"], v["check_env"]
    st.record["venv"] = {"reads": v["reads"], "parent_pyarrow": launch.parent_pyarrow(), "sys_executable": sys.executable,
                         "sys_base_executable": sys._base_executable, "sys_version": sys.version}
    st.record["engine"] = {"check_env": v["check_env"], "guard_selftest": v["guard_selftest"]}


def _step4(st: _State) -> None:
    probe = run_probe(python=st.python, probe_cmd=st.probe_cmd, unshare=st.unshare)
    egress = {"probe": probe, "layer": LAYER, "unshare": st.unshare, "record_path": None, "record_path_norm": None}
    if st.mode == "of-record":
        record_dir = st.repo_root / "docs" / "nautilus_bridge" / "egress"
        check_egress_record(record_dir, {"venv_python": str(st.python), "layer": LAYER,
                                         "base_python": st.reads["pyvenv"]["executable"]})
        egress["record_path"] = str(record_dir / f"{launch.host_tag()}.json")
        egress["record_path_norm"] = _norm(egress["record_path"])
    st.record["egress"] = egress


def _step5_6(st: _State, step: int) -> None:
    t = st.table
    if step == 5:
        path = Path(t["prices_file"]) if st.mode == "rehearsal" else st.repo_root / t["prices_file"]
        st.prices = load_prices(path, md5=t["prices_md5"], start=t["start"], end=t["end"], instrument=t["instrument"],
                                mode=st.mode)
        st.record["data"] = {"prices_file": t["prices_file"], "prices_md5": st.prices.md5, "rf_file": t["rf_file"],
                             "rf_md5": None, "start": t["start"], "end": t["end"], "sessions": len(st.prices.dates),
                             "rounding_changed": st.prices.rounding_changed}
    elif t["rf_file"] is None:
        st.rf = np.zeros(len(st.prices.dates))      # pilot 2: rf = 0.0, no overlay (QUANT-R3-2)
    else:
        path = Path(t["rf_file"]) if os.path.isabs(t["rf_file"]) else st.repo_root / t["rf_file"]
        st.rf, st.rf_bytes = load_rf(path, md5=t["rf_md5"], dates=st.prices.dates)
        st.record["data"]["rf_md5"] = hashlib.md5(st.rf_bytes).hexdigest()


def _step7(st: _State) -> None:
    """P0a: the trimmed cache in the run's temp dir, the study loaded by path, check_p0a (R-13)."""
    t = st.table
    st.p0a_dir = Path(tempfile.mkdtemp(prefix="qgnb_p0a_"))
    name = "yf_" + re.sub(r"[=^:/]", "_", t["symbol"]) + ".csv"          # the name study._cached builds
    (st.p0a_dir / name).write_bytes(st.prices.kept)
    names = [name]
    if st.rf_bytes is not None:
        (st.p0a_dir / "fred_DGS3MO.csv").write_bytes(st.rf_bytes)
        names.append("fred_DGS3MO.csv")
    missing = [n for n in names if not (st.p0a_dir / n).is_file()]
    if missing:
        raise refuse("R-13", f"the trimmed cache lacks {missing}")
    st.study = load_study(st.repo_root)
    arrays = {"symbol": t["symbol"], "start": t["start"], "dates": st.prices.dates, "closes": st.prices.closes,
              "rf": None if t["rf_file"] is None else st.rf}
    st.pn = check_p0a(st.study, st.p0a_dir, arrays)
    st.record["provenance"] = {"p0a": {"passed": True, "cache_files": names}, "p0b": None}


def _step8_10(st: _State, step: int) -> None:
    t = st.table
    if step == 8:
        floor, classes = check_cost(t["symbol"], float(t["cost_bps"]))
        st.record["costs"] = {"cost_bps": float(t["cost_bps"]), "floor_bp": floor, "classes": classes, "stress": 2.0,
                              "source": "validate.cost_floor_bp"}
    elif step == 9:
        st.gate = check_gate()
    else:
        st.ledger = gate_ledger.family_ledger(t["family_id"], st.ledger_dir)
        check = st.ledger.verify_chain()
        if not check:
            raise refuse("R-09", f"{st.ledger.path}: chain broken at line {check.first_bad_line}: {check.reason}")
        st.record["registration"] = {"family_id": t["family_id"], "ledger_path": str(st.ledger.path),
                                     "hash_before": st.ledger.hash(), "n_raw_before": check.n_rows, "hash_after": None,
                                     "n_raw_after": None, "market_n_raw": None, "rows": []}


def _before_registration(st: _State) -> None:
    """Steps 0 to 10, each followed by its after_step<n> hook (called with None)."""
    steps = [_step0, _step1, _step2, _step3, _step4, lambda s: _step5_6(s, 5), lambda s: _step5_6(s, 6), _step7,
             lambda s: _step8_10(s, 8), lambda s: _step8_10(s, 9), lambda s: _step8_10(s, 10)]
    for n, step in enumerate(steps):
        step(st)
        _hook(st, n)


def _step11(st: _State) -> None:
    """Register every column in grid order (6.4); the run folder exists from here on (R-12's record)."""
    run_dir = st.out_root / st.run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    st.run_dir = run_dir
    t, rows = st.table, st.record["registration"]["rows"]
    run_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    anchor = gate_ledger.repo_anchor(st.repo_root)
    for col, theta in enumerate(t["grid"]):
        row = ledger_row(t, theta, span=(st.prices.dates[0], st.prices.dates[-1]), run_utc=run_utc, anchor=anchor,
                         bridge_run_id=st.run_id)
        rows.append(registration_entry(col, st.register_fn(st.ledger, row, script=SCRIPT)))


def _step12(st: _State) -> None:
    """The post-registration snapshot, the RunContext and the IN_PROGRESS record."""
    reg, rows = st.record["registration"], st.ledger.rows()
    reg.update(hash_after=st.ledger.hash(rows), n_raw_after=len(rows),
               market_n_raw=sum(r.get("market") == st.table["market"] for r in rows))
    st.record["times"]["registered_utc"] = _utc_now()
    st.record["status"] = "IN_PROGRESS"
    T, G = len(st.prices.dates), len(st.table["grid"])
    nan = np.full((T - 1, G), np.nan)
    st.ctx = RunContext(
        mode=st.mode, repo_root=st.repo_root, table=st.table, table_sha256=st.table_sha,
        code_sha256=st.record["table"]["code_sha256"], bridge_run_id=st.run_id, run_dir=st.run_dir, record=st.record,
        dates=st.prices.dates, ts=st.prices.ts, closes=st.prices.closes, rf=st.rf, study=st.study, study_pn=st.pn,
        grid=st.table["grid"], fn=FN[st.table["strategy"]], weights=np.zeros((T, G)), pnl_qg=nan.copy(),
        pnl_stress_qg=nan.copy(), turnover_qg=nan.copy(), pnl_nt=nan.copy(), pnl_stress_nt=nan.copy(),
        turnover_nt=nan.copy(), legs={}, gate_snapshot=st.gate, ledger=st.ledger,
        hash_after_registration=reg["hash_after"], score_fn=st.score_fn, hooks=st.hooks,
        stub_child=st.child_cmd is not None)
    _write_best_effort(st, "IN_PROGRESS")


def _step13_15(st: _State, step: int) -> None:
    ctx, cost = st.ctx, float(st.table["cost_bps"])
    if step == 13:                                  # QUANTGEN's reference: pnl_matrix column by column
        for g, theta in enumerate(ctx.grid):
            W = np.asarray(ctx.fn(ctx.closes, **theta), dtype=float).reshape(len(ctx.closes), -1)
            ctx.weights[:, g] = W[:, 0]
            ctx.pnl_qg[:, g], ctx.turnover_qg[:, g] = S.simulate(ctx.closes, W, cost_bps=cost, cash_daily=ctx.rf)
            ctx.pnl_stress_qg[:, g] = S.simulate(ctx.closes, W, cost_bps=cost * 2.0, cash_daily=ctx.rf)[0]
    elif step == 14:                                # one child per (column, cost level), sequentially
        st.baseline = None if ctx.stub_child else load_baseline(st.reads["wheel"]["platform_tag"])
        for col in range(len(ctx.grid)):
            for stress in (1, 2):
                leg = ctx.legs[(col, stress)] = _run_leg(st, col, stress)
                st.record["children"].append(leg.child)
                _write_best_effort(st, f"child {col} x{stress}")
    else:                                           # the Nautilus matrices from the valid legs (5.3.4)
        for (col, stress), leg in ctx.legs.items():
            if leg.invalid or leg.rebuilt is None:
                continue
            if stress == 1:
                ctx.pnl_nt[:, col], ctx.turnover_nt[:, col] = leg.rebuilt.R, leg.rebuilt.TV
            else:
                ctx.pnl_stress_nt[:, col] = leg.rebuilt.R


def _write_best_effort(st: _State, what: str) -> None:
    """An intermediate record write: a failure is listed and never changes the status (5.3.5)."""
    try:
        write_record(st.run_dir / "run.json", st.record)
    except Exception as exc:                        # noqa: BLE001
        st.record["record_write_failures"].append(f"{what}: {type(exc).__name__}: {exc}")


def _finish(st: _State, status: str, code: int, message: str | None, tb: str | None) -> int:
    """The final record, in a try that catches BaseException; run.final.<pid>.json when it still fails."""
    st.record["status"] = status
    if message:
        print(message)
        st.record["error"] = {"message": message, "traceback": (tb or "")[-launch.TAIL_CHARS:]}
    st.record["times"]["finished_utc"] = _utc_now()
    if st.run_dir is None:                          # the run folder could not be made: nothing to write
        print(f"STATUS {status} exit={code} record=-")
        return code
    path = st.run_dir / "run.json"
    try:
        write_record(path, st.record)
    except BaseException as exc:                    # noqa: BLE001 - G-07 included
        st.record["record_write_failures"].append(f"final: {type(exc).__name__}: {exc}")
        path = st.run_dir / f"run.final.{os.getpid()}.json"
        try:
            with open(path, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(_json_text(st.record))
        except BaseException as exc2:               # noqa: BLE001
            print(f"the run record could not be written: {type(exc2).__name__}: {exc2}")
            path = "-"
    print(f"STATUS {status} exit={code} record={path}")
    return code


def _after_registration(st: _State) -> int:
    """Steps 11 to 17: R-12 (exit 3), G-06 (ERROR, 4), G-07 (ABORTED, 5), else the Outcome of steps 16 and 17."""
    try:
        _step11(st)
    except Exception as exc:                        # noqa: BLE001
        return _finish(st, "REFUSED_REGISTRATION", 3, f"R-12: register_trial raised {type(exc).__name__}: {exc}",
                       traceback.format_exc())
    except BaseException as exc:                    # noqa: BLE001
        return _finish(st, "ABORTED", 5, f"G-07: {type(exc).__name__} during registration", traceback.format_exc())
    try:
        _hook(st, 11)
        _step12(st)
        _hook(st, 12)
        for step in (13, 14, 15):
            _step13_15(st, step)
            _hook(st, step)
        outcome = parity_and_gate(st.ctx)
    except Exception as exc:                        # noqa: BLE001
        return _finish(st, "ERROR", 4, f"G-06: {type(exc).__name__}: {exc}", traceback.format_exc())
    except BaseException as exc:                    # noqa: BLE001
        return _finish(st, "ABORTED", 5, f"G-07: {type(exc).__name__} after registration", traceback.format_exc())
    st.record["withheld_reasons"] = list(outcome.withheld_reasons)
    return _finish(st, outcome.status, outcome.exit_code, None, None)


def _print_refusal(exc: BridgeRefusal) -> int:
    print(str(exc))
    if exc.remedy:
        print(f"remedy: {exc.remedy}")
    print("STATUS REFUSED exit=2 record=-")
    return 2


def run(table_path: Path, *, mode: str, ledger_dir: Path | None = None, out_dir: Path | None = None,
        child_cmd: list[str] | None = None, probe_cmd: list[str] | None = None,
        hooks: dict[str, Callable[..., None]] | None = None, timeout: float = launch.TIMEOUT_S,
        register_fn=gate_ledger.register_trial, score_fn=validate.score_strategy,
        rerun_of: str | None = None, reason: str | None = None) -> int:
    """One run of a registration table (5.3.1, 5.3.2, 5.3.5); returns the exit code and never re-raises (QA-R3-6).
    Before registration a refusal or an unexpected exception prints its reason, writes nothing and returns 2."""
    st = _State(Path(table_path), mode, ledger_dir, out_dir, child_cmd, probe_cmd, dict(hooks or {}), hooks is not None,
                timeout, register_fn, score_fn, rerun_of, reason)
    st.record = _new_record(st)
    try:
        try:
            _check_arguments(st)
            _before_registration(st)
        except BridgeRefusal as exc:
            return _print_refusal(exc)
        except BaseException:                       # noqa: BLE001 - OPS-R2-6
            print(traceback.format_exc()[-2000:])
            print("STATUS REFUSED exit=2 record=-")
            return 2
        return _after_registration(st)
    finally:
        if st.lock is not None:
            st.lock.release()
        if st.p0a_dir is not None:
            launch.cleanup_tempdir(st.p0a_dir)
        if st.awake:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


# --------------------------------------------------------------------------- #
# Modes: --fixtures, --check-env, --egress-record (5.3.1)
# --------------------------------------------------------------------------- #
def utc_date(ts_ns: int) -> str:
    return (date(1970, 1, 1) + timedelta(days=ts_ns // (86_400 * 10**9))).isoformat()


def golden_of(name: str, exit_code: int | None, manifest: dict | None, fills: list[dict]) -> dict:
    """6.8's golden shape from one fixture run: fills as their CSV text, money as the manifest's strings."""
    m = manifest or {}
    r = m.get("result") or {}
    return {"schema": GOLDEN_SCHEMA, "fixture": name,
            "status": "valid" if exit_code == 0 and m.get("valid") is True else "invalid", "exit_code": exit_code,
            "bars_fed": (m.get("input") or {}).get("bars_fed"), "bars_seen": r.get("bars_seen"),
            "force_stop": r.get("force_stop"),
            "fills": [{"date": utc_date(int(f["ts_event"])), "side": f["order_side"], "qty": f["last_qty"],
                       "price": f["last_px"], "commission": f["commission"]} for f in fills],
            "final_cash": r.get("account_balance_usd"), "final_qty": r.get("final_qty"),
            "invalid_reasons": list(m.get("invalid_reasons") or [])}


def _money_close(a, b) -> bool:
    try:
        return abs(Decimal(str(a)) - Decimal(str(b))) <= Decimal("0.005")
    except ArithmeticError:
        return False


def compare_golden(got: dict, want: dict) -> list[str]:
    """6.8: integers and strings exactly, the price as its string, money within 0.005, reasons by leading id."""
    out = [f"{k}: {got.get(k)!r} != {want.get(k)!r}" for k in ("schema", "fixture", "status", "exit_code", "bars_fed",
                                                               "bars_seen", "force_stop", "final_qty")
           if got.get(k) != want.get(k)]
    if not _money_close(got.get("final_cash"), want.get("final_cash")):
        out.append(f"final_cash: {got.get('final_cash')!r} != {want.get('final_cash')!r}")
    gf, wf = got.get("fills") or [], want.get("fills") or []
    if len(gf) != len(wf):
        out.append(f"fills: {len(gf)} rows != {len(wf)}")
    for n, (a, b) in enumerate(zip(gf, wf)):
        out += [f"fill {n} {k}: {a.get(k)!r} != {b.get(k)!r}" for k in ("date", "side", "qty", "price")
                if a.get(k) != b.get(k)]
        if not _money_close(a.get("commission"), b.get("commission")):
            out.append(f"fill {n} commission: {a.get('commission')!r} != {b.get('commission')!r}")
    ids = [[str(r).split(":")[0] for r in d.get("invalid_reasons") or []] for d in (got, want)]
    if ids[0] != ids[1]:
        out.append(f"invalid_reasons ids: {ids[0]} != {ids[1]}")
    return out


def run_fixture(name: str, python: Path, unshare: str | None, *, timeout: float = launch.TIMEOUT_S) -> dict:
    """One fixture of spec 8.2 through the exact launch contract: {"golden", "census", "manifest", "result"}."""
    raw, bars = launch.fixture_inputs(name)
    tmp = launch.make_tempdir()
    try:
        (tmp / "input.json").write_bytes(raw)
        (tmp / "bars.csv").write_bytes(bars)
        res = launch.run_child(launch.build_launch(["run", "--in", str(tmp)], tempdir=tmp, venv_python=python,
                                                   unshare=unshare), timeout=timeout)
        try:
            manifest = json.loads((tmp / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = None
        try:
            fills = _rows(tmp / "fills.csv", FILLS_HEADER)
        except (OSError, ValueError):
            fills = []
    finally:
        launch.cleanup_tempdir(tmp)
    return {"golden": golden_of(name, res.returncode, manifest, fills), "census": res.census, "manifest": manifest,
            "result": res}


def _venv_for_mode() -> tuple[Path, dict, str | None]:
    python = venv_python_from_key()
    reads = launch.read_venv(python)
    bad = launch.venv_mismatches(reads)
    if bad:
        raise refuse("R-03", "the venv is off its pins: " + "; ".join(b.removeprefix("R-03: ") for b in bad))
    return python, reads, launch.resolve_unshare()


def fixtures_mode(*, record: bool = False, write: bool = False, golden_dir: Path = launch.GOLDEN_DIR,
                  repo_root: Path = REPO_ROOT) -> int:
    """--fixtures: F1, F2 and N1 against their goldens (6.8); --write-goldens writes missing goldens on Linux, never
    over a file (QA-R2-6); --record-baseline writes the census baseline only when all three match (OPS-R2-1)."""
    try:
        python, reads, unshare = _venv_for_mode()
        env = launch_once(["--check-env"], python=python, child_cmd=None, unshare=unshare, timeout=launch.TIMEOUT_S)[1]
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    tag, runs, ok = reads["wheel"]["platform_tag"], {}, True
    for name in GOLDEN_FIXTURES:
        runs[name] = run_fixture(name, python, unshare)
        path = Path(golden_dir) / f"{name}.json"
        want = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        diff = ["no golden file"] if want is None else compare_golden(runs[name]["golden"], want)
        print(f"{name}: exit {runs[name]['result'].returncode}, census {len(runs[name]['census'])} names, "
              + ("matches its golden" if not diff else "differs: " + "; ".join(diff)))
        ok = ok and not diff
    if write:
        if not tag.startswith("manylinux"):
            return _print_refusal(BridgeRefusal("R-11", f"--write-goldens runs on Linux only, not {tag}"))
        for name in GOLDEN_FIXTURES:
            path = Path(golden_dir) / f"{name}.json"
            if path.exists():
                print(f"{path.name} exists; never overwritten")
                continue
            with open(path, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(_json_text(runs[name]["golden"]))
            print(f"written {path.name}")
        print("STATUS OK exit=0 record=-")
        return 0
    baseline = load_baseline(tag, golden_dir)
    for name in ("F1", "F2"):
        if baseline is not None:
            print(f"{name} census against modules_{tag}.json: {judge_census(runs[name]['census'], baseline) or 'equal'}")
    if record:
        if not ok:
            print("--record-baseline writes nothing: a fixture differs from its golden (OPS-R2-1)")
            print("STATUS REFUSED exit=2 record=-")
            return 2
        union = sorted(set(runs["F1"]["census"]) | set(runs["F2"]["census"]))
        rel = f"tools/nautilus/golden/modules_{tag}.json"
        git = shutil.which("git")
        tracked = git is not None and _git(git, repo_root, "ls-files", "--error-unmatch", rel).returncode == 0
        code, lines = record_baseline(golden_dir, tag, union, tracked=tracked, python=(env or {}).get("python"))
        for other in sorted(Path(golden_dir).glob("modules_*.json")):
            if other.name != f"modules_{tag}.json":
                print(f"against {other.name}: {census_diff(load_baseline(other.stem[8:], golden_dir), union) or 'equal'}")
        print("\n".join(lines))
        print(f"STATUS {'OK' if code == 0 else 'REFUSED'} exit={code} record={Path(golden_dir) / f'modules_{tag}.json'}")
        return code
    print(f"STATUS {'OK' if ok else 'REFUSED'} exit={0 if ok else 2} record=-")
    return 0 if ok else 2


def check_env_mode() -> int:
    """--check-env: the venv checks of 6.7, --check-env and --guard-selftest; exit 0 on a match, 2 otherwise."""
    try:
        v = check_venv(child_cmd=None, unshare=launch.resolve_unshare(), timeout=launch.TIMEOUT_S)
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    print(json.dumps(v["check_env"], sort_keys=True))
    print(json.dumps(v["guard_selftest"], sort_keys=True))
    print(json.dumps({"python": str(v["python"]), "python_minor": v["reads"]["python_minor"],
                      "versions": v["reads"]["versions"], "wheel": v["reads"]["wheel"]}, sort_keys=True))
    print("STATUS OK exit=0 record=-")
    return 0


def egress_record_mode(repo_root: Path = REPO_ROOT) -> int:
    """--egress-record (4.4): writes docs/nautilus_bridge/egress/<host tag>.json, then exits 2 (R-14) unless the
    probe is blocked and the parent's control connect succeeded; a failed control connect is printed first."""
    try:
        python, reads, unshare = _venv_for_mode()
        res, probe = launch_once([], python=python, child_cmd=None, unshare=unshare, timeout=60,
                                 script=launch.EGRESS_PROBE)
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    control = control_connect()
    rec = {"schema": EGRESS_SCHEMA, "platform_tag": launch.host_tag(), "venv_python": str(python),
           "base_python": reads["pyvenv"]["executable"], "layer": LAYER,
           "probe": probe or {"blocked": False, "errno": None, "error": f"exit {res.returncode}: {res.stdout_tail[-200:]}"},
           "recorded_utc": _utc_now(), "control_connect": control}
    path = Path(repo_root) / "docs" / "nautilus_bridge" / "egress" / f"{launch.host_tag()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_text(rec), encoding="utf-8", newline="\n")
    print(json.dumps(rec, sort_keys=True))
    if rec["probe"].get("blocked") is True and control["ok"]:
        print(f"STATUS OK exit=0 record={path}")
        return 0
    if not control["ok"]:
        print(f"control connect failed: {control['error']}")
        print("this network does not reach 1.1.1.1:443, so the record cannot prove the rule; run Step 7A on a "
              "network that does, or ask Claude")
    exc = refuse("R-14", f"the record does not prove the rule: probe blocked {rec['probe'].get('blocked')}, "
                         f"control connect ok {control['ok']}")
    print(str(exc))
    print(f"remedy: {exc.remedy}")
    print(f"STATUS REFUSED exit=2 record={path}")
    return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -B -m tools.nautilus.runner")
    ap.add_argument("--table")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--of-record", action="store_true")
    ap.add_argument("--ledger-dir")
    ap.add_argument("--out-dir")
    ap.add_argument("--child-cmd", help="rehearsal only: a JSON list replacing <venv python> ... <sandbox.py>")
    ap.add_argument("--rerun-of")
    ap.add_argument("--reason")
    ap.add_argument("--check-env", action="store_true")
    ap.add_argument("--egress-record", action="store_true")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--record-baseline", action="store_true")
    ap.add_argument("--write-goldens", action="store_true")
    a = ap.parse_args(argv)
    modes = [bool(a.table), a.check_env, a.egress_record, a.fixtures]
    if sum(modes) != 1 or (a.table and a.rehearsal == a.of_record) or (
            (a.record_baseline or a.write_goldens) and not a.fixtures) or (a.record_baseline and a.write_goldens):
        ap.print_usage()
        print("STATUS REFUSED exit=2 record=-")
        return 2
    if a.check_env:
        return check_env_mode()
    if a.egress_record:
        return egress_record_mode()
    if a.fixtures:
        return fixtures_mode(record=a.record_baseline, write=a.write_goldens)
    child_cmd = None
    if a.child_cmd is not None:
        try:
            child_cmd = json.loads(a.child_cmd)
        except ValueError:
            return _print_refusal(refuse("R-11", f"--child-cmd is not a JSON list: {a.child_cmd!r}"))
    return run(Path(a.table), mode="rehearsal" if a.rehearsal else "of-record",
               ledger_dir=Path(a.ledger_dir) if a.ledger_dir else None, out_dir=Path(a.out_dir) if a.out_dir else None,
               child_cmd=child_cmd, rerun_of=a.rerun_of, reason=a.reason)


if __name__ == "__main__":
    raise SystemExit(main())
```
  Run the module (no golden or baseline exists yet):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance 2>/dev/null | grep -E '^FAIL|passed'
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k l1_33 -k l2_02 -k l2_03 -k l2_06 2>/dev/null | grep -E '^FAIL|passed'
```
  Expected without the key (about 20 s): one line `FAIL test_l1_33_goldens_equal_the_spec_tables FileNotFoundError: [Errno 2] No such file or directory: '/home/user/quantgen/tools/nautilus/golden/F1.json'` and `31/42 passed, 1 failed, 10 not run`. With the key: `FAIL test_l1_33_...` as above, `FAIL test_l2_02_f1_f2_match_goldens FileNotFoundError: ... golden/F1.json'`, `FAIL test_l2_03_n1_matches_golden FileNotFoundError: ... golden/N1.json'`, `FAIL test_l2_06_census_matches_platform_baseline AssertionError: no census baseline modules_manylinux_2_35_x86_64.json: runner --fixtures --record-baseline records it`, and `0/4 passed, 4 failed, 0 not run`.

- [ ] **Step 5: Write the goldens (Linux, in this clone; plan rules).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --fixtures --write-goldens; echo "exit $?"
md5sum tools/nautilus/golden/F1.json tools/nautilus/golden/F2.json tools/nautilus/golden/N1.json
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k l1_33 -k l2_02 -k l2_03 -k l2_06 2>/dev/null | grep -E '^(PASS|FAIL)|passed'
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --fixtures --write-goldens | tail -4
```
  Expected: `F1: exit 0, census 942 names, differs: no golden file`, the same for F2 and `N1: exit 10, ...`, then `written F1.json`, `written F2.json`, `written N1.json`, `STATUS OK exit=0 record=-`, `exit 0`; the md5s `6525ecbe771351571469df533c1c3c6c`, `85199e69206182532ac8b5080e0b0150`, `0fc7830cf871e00a2f3a6cc891ceff03`; `PASS` for L1-33, L2-2 and L2-3, `FAIL test_l2_06_...` as in Step 4, `3/4 passed, 1 failed, 0 not run`; the repeat prints `F1.json exists; never overwritten` (the same for F2 and N1) and `STATUS OK exit=0 record=-` (QA-R2-6).

- [ ] **Step 6: Record the Linux census baseline.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --fixtures --record-baseline > "$S/t4_baseline.out"; echo "exit $?"
head -3 "$S/t4_baseline.out"; grep -c '^+ ' "$S/t4_baseline.out"; tail -2 "$S/t4_baseline.out"
python3 -c "import json; d = json.load(open('tools/nautilus/golden/modules_manylinux_2_35_x86_64.json', encoding='utf-8')); print(d['schema'], d['platform_tag'], d['python'], d['recorded_from'], len(d['census']), [n for n in d['census'] if n.startswith(('nautilus_trader.adapters', 'nautilus_trader.network'))])"
md5sum tools/nautilus/golden/modules_manylinux_2_35_x86_64.json
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k l2_06 2>/dev/null | tail -1
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --fixtures | tail -3
```
  Expected: `exit 0`; the three `matches its golden` lines (`F1: exit 0, census 942 names, matches its golden`, F2 likewise, `N1: exit 10, ...`); `942` diff lines starting `+ ` (the file is untracked and new); `written modules_manylinux_2_35_x86_64.json` and `STATUS OK exit=0 record=/home/user/quantgen/tools/nautilus/golden/modules_manylinux_2_35_x86_64.json`; `nautilus-bridge-census/1 manylinux_2_35_x86_64 3.13.17 ['F1', 'F2'] 942 []`; md5 `b7bccf501c8d1ca982dd4a429d407df0` measured in the scratch clone (another name count or md5 is recorded, not a failure, as long as L2-6 passes); `1/1 passed, 0 failed, 0 not run`; then `F1 census against modules_manylinux_2_35_x86_64.json: equal`, the same for F2, `STATUS OK exit=0 record=-`.

- [ ] **Step 7: The other modes and a real-venv rehearsal (done-when evidence; no test asserts a run that reaches step 16).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --check-env; echo "exit $?"
python3 -B -m tools.nautilus.runner --check-env | tail -1; echo "exit ${PIPESTATUS[0]}"
T=$(mktemp -d "$S/t4_smoke_XXXX")
python3 -B -c "import sys; from pathlib import Path; import tests.nautilus_acceptance as A; A.write_rehearsal_table(Path(sys.argv[1]), prices=A.synth_prices(7, 1500, 100.0, 150.0), dates=A._bdates(1500), rf=A.synth_rf(1500), axes={'rule': ['sma'], 'lookback': [126], 'step': [21]})" "$T"
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --table "$T/table.json" --rehearsal --ledger-dir "$T/ledgers" --out-dir "$T/out" | tail -2; echo "exit ${PIPESTATUS[0]}"
python3 - "$T" <<'EOF'
import glob, json, sys
rec = json.load(open(glob.glob(sys.argv[1] + "/out/NB-*/run.json")[0], encoding="utf-8"))
reg = rec["registration"]
print(rec["status"], rec["stub_child"], reg["n_raw_after"], len(reg["hash_after"]), rec["data"]["prices_md5"] is not None, rec["data"]["rf_md5"] is not None)
print(rec["venv"]["reads"]["wheel"]["record_digest_sha256"][:8], rec["venv"]["reads"]["versions"])
print([(c["col"], c["stress"], c["returncode"], c["invalid"], c["manifest"]["input"]["ledger_hash_after_registration"] == reg["hash_after"]) for c in rec["children"]])
print({k: len(v) for k, v in rec["census"].items()}, rec["egress"]["probe"]["blocked"])
EOF
rm -rf "$T"
rm -rf "$S/clone_task4"; git clone -q /home/user/quantgen "$S/clone_task4" && cp tools/nautilus/runner.py "$S/clone_task4/tools/nautilus/"
(cd "$S/clone_task4" && QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --egress-record | tail -1; echo "exit ${PIPESTATUS[0]}")
rm -rf "$S/clone_task4"
git status --short
```
  Expected: three JSON lines (`{"environment": "BACKTEST", "machine": "x86_64", "precision": {"FIXED_PRECISION": 16, "HIGH_PRECISION": true, "PRICE_MAX": 17014118346046.0, "QUANTITY_MAX": 34028236692093.0}, "python": "3.13.17", "schema": "nautilus-bridge-check-env/1", "system": "Linux"}`, the five self-test outcomes, and the venv python, `python_minor` `3.13`, the three pinned versions and the wheel identity `a448cd20...`, 764 entries), `STATUS OK exit=0 record=-`, `exit 0`; without the key `STATUS REFUSED exit=2 record=-` after `R-03: QUANTGEN_NAUTILUS_PYTHON is not set` and its remedy, `exit 2`. The rehearsal (about 5 s) ends `G-06: NotImplementedError: spec 5.4 and 5.5 are plan Task 5` and `STATUS ERROR exit=4 record=<T>/out/NB-<UTC>-<8 hex>/run.json`, `exit 4` (Task 5 fills the seam); the record shows `ERROR False 1 32 True True`, `a448cd20 {'nautilus-trader': '1.231.0', 'numpy': '2.3.5', 'pandas': '2.3.3'}`, `[(0, 1, 0, [], True), (0, 2, 0, [], True)]` and `{'manylinux_2_35_x86_64': 942} True`: the post-registration ledger hash, both data md5s, the venv reads and every child manifest (spec Step 6 done-when). `--egress-record` runs only in the scratch clone (plan rules): its last line is `STATUS OK exit=0 record=<S>/clone_task4/docs/nautilus_bridge/egress/linux_x86_64.json`, `exit 0`, when the container reaches 1.1.1.1:443 (measured 2026-10-28); where it does not, the output shows `control connect failed: ...`, the network line, the R-14 line and `STATUS REFUSED exit=2 record=...`, also a correct result. The real clone's `git status --short` shows only Task 4's paths (Step 12) and the pre-existing ones.

- [ ] **Step 8: The module in both key states.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.nautilus_acceptance 2>/dev/null | grep -E '^(FAIL|NOT_RUN)|passed'
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance 2>/dev/null | grep -E '^(FAIL|NOT_RUN)|passed'
```
  Expected: the 10 `NOT_RUN test_l2_... OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)` lines and `32/42 passed, 0 failed, 10 not run`; then, after about 2 minutes, only `42/42 passed, 0 failed, 0 not run`. Both runs keep L1-15 (spec 3.7 over `tools/nautilus/*.py` and `tests/nautilus_*.py`, now including `runner.py` and the stub) and L1-32 (no guarded file changed) passing.

- [ ] **Step 9: Guards: T-RO-01, bridge text, the suite registration.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.macro_m0_harness | tail -1
python3 -B -c "
from tests.macro_m0_harness import _offences, _scan_files, ROOT
files = [p for p in _scan_files() if p.relative_to(ROOT).as_posix().startswith('tools/nautilus/')]
print([p.relative_to(ROOT).as_posix() for p in files], [h for p in files for h in _offences(p)])
"
python3 - <<'EOF'
from pathlib import Path
src = Path("tests/nautilus_acceptance.py").read_text(encoding="utf-8")
texts = {"runner": Path("tools/nautilus/runner.py").read_text(encoding="utf-8"),
         "stub": Path("tests/nautilus_stub_child.py").read_text(encoding="utf-8"),
         "tests": src[src.index("# Plan Task 4 (spec Step 6)"):src.index("\n# CLI\n")]}
print({k: [t for t in ("submit_order", "CANO", "KIS_ACCOUNT", "ACNT_PRDT_CD") if t in v] for k, v in texts.items()})
EOF
md5sum qa/acceptance_results.json
python3 -B "$S/run_baseline.py" "$S/t4_nautilus.json" --suite nautilus 2>/dev/null | tail -1
md5sum qa/acceptance_results.json
```
  Expected: `14/14 passed, 0 failed, 0 not run`; `['tools/nautilus/__init__.py', 'tools/nautilus/egress_probe.py', 'tools/nautilus/launch.py', 'tools/nautilus/runner.py', 'tools/nautilus/sandbox.py'] []`; `{'runner': [], 'stub': [], 'tests': []}`; `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json` before and after; `32/42 passed, 0 failed, 10 not run; /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/t4_nautilus.json` (Task 2's `nautilus_tests()` collects the same 42 rows). test_08, test_09 and the flet guard read no file Task 4 touches; Step 10 shows their rows unchanged.

- [ ] **Step 10: Run the full suite through the wrapper and compare it with Step 0's baseline.** Background run (about 10 minutes; nothing else from QUANTGEN runs meanwhile):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
md5sum qa/acceptance_results.json
python3 -B "$S/run_baseline.py" "$S/t4_after.json" > "$S/t4_after.log" 2>&1; echo "exit $?"
```
  When it has finished:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
tail -1 "$S/t4_after.log"; md5sum qa/acceptance_results.json
python3 - "$S/t1_baseline.json" "$S/t4_after.json" <<'EOF'
import json, sys
a, b = ({r["test"]: r["status"] for r in json.load(open(p, encoding="utf-8"))} for p in sys.argv[1:3])
added = sorted(set(b) - set(a))
print("added", len(added), sum(k.startswith("nautilus/") for k in added), [k for k in added if not k.startswith("nautilus/")])
print("added statuses", {s: sum(b[k] == s for k in added) for s in ("PASS", "FAIL", "NOT_RUN")})
print("removed", sorted(set(a) - set(b)))
print("changed", sorted((k, a[k], b[k]) for k in a.keys() & b.keys() if a[k] != b[k]))
EOF
```
  Expected: the summary is `B` plus 44 rows, 34 PASS and 10 NOT_RUN, with `B`'s FAIL count (only the results path after `;` differs in form); md5 `16c9baa5a1777853521d485d5078e456` before and after; `added 44 42 ['macro/macro_m0_harness/test_t_ro_01_nautilus_allowlist_pinned', 'macro/macro_m0_harness/test_t_ro_01_nautilus_confined_to_the_sandbox']`, `added statuses {'PASS': 34, 'FAIL': 0, 'NOT_RUN': 10}`, `removed []`, `changed []` (so `safety/test_08_no_broker_order_path`, `safety/test_09_no_account_credentials_requested`, the `ui/` rows and every earlier `macro/macro_m0_harness/test_t_ro_01_*` row keep Step 0's status).

- [ ] **Step 11: Line ends and untouched files.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -c "import sys; bad = [p for p in sys.argv[1:] if b'\r' in open(p, 'rb').read()]; print('LF ok' if not bad else bad)" tools/nautilus/runner.py tests/nautilus_stub_child.py tests/nautilus_acceptance.py tools/nautilus/golden/F1.json tools/nautilus/golden/F2.json tools/nautilus/golden/N1.json tools/nautilus/golden/modules_manylinux_2_35_x86_64.json
python3 -c "b = open('tests/run_all.py', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'tests/run_all.py must stay CRLF'; print('CRLF ok')"
python3 -c "b = open('README.md', 'rb').read(); assert b.count(b'\r\n') == b.count(b'\n'), 'README.md must stay CRLF'; print('CRLF ok')"
git diff --quiet HEAD -- tools/nautilus/launch.py tools/nautilus/sandbox.py tests/run_all.py README.md tests/macro_m0_harness.py tests/macro_registry.csv requirements.txt requirements-dev.txt requirements-nautilus.txt pyproject.toml config.py qa/acceptance_results.json && echo untouched
```
  Expected: `LF ok`, `CRLF ok`, `CRLF ok`, `untouched`. Task 4 edits no CRLF file.

- [ ] **Step 12: Commit.** `git status --short` must show exactly these seven lines, plus any path Task 1 Step 0 recorded as pre-existing (left unstaged):
```
 M tests/nautilus_acceptance.py
?? tests/nautilus_stub_child.py
?? tools/nautilus/golden/F1.json
?? tools/nautilus/golden/F2.json
?? tools/nautilus/golden/N1.json
?? tools/nautilus/golden/modules_manylinux_2_35_x86_64.json
?? tools/nautilus/runner.py
```
  No `docs/nautilus_bridge/egress/`, no `runs/`, no `qa/acceptance_results.json`. Then:
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git add tools/nautilus/runner.py tests/nautilus_stub_child.py tests/nautilus_acceptance.py tools/nautilus/golden/F1.json tools/nautilus/golden/F2.json tools/nautilus/golden/N1.json tools/nautilus/golden/modules_manylinux_2_35_x86_64.json
git status --short
git commit -F - <<'EOF'
nautilus bridge, plan Task 4 (spec Step 6): runner, stub child, goldens, Linux census

tools/nautilus/runner.py: spec 5.3, steps 0 to 15: the table lock,
freshness and re-run policy; the table, tree, venv, egress, data,
cash-rate, P0a, cost, gate and ledger checks (R-01 to R-17); registration
before any child; the QUANTGEN reference; one child per column and cost
level through the launch contract; the return reconstruction of 5.3.3 and
the C-01 to C-15 judgements, census included; the run record with
write_record's retries and fallback; the parity_and_gate seam that Task 5
fills; the --check-env, --egress-record and --fixtures [--write-goldens |
--record-baseline] modes. tests/nautilus_stub_child.py: the layer-1 stub
child of spec 8.1. tools/nautilus/golden/: the F1, F2 and N1 goldens and
the manylinux_2_35_x86_64 census baseline, written by the runner.
tests/nautilus_acceptance.py: the rehearsal helpers and 24 tests (21
layer 1, 3 layer 2). Registration tables keep their axes order (no
sort_keys). qa/acceptance_results.json untouched.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
EOF
git show --stat HEAD | tail -1; git status --short; md5sum qa/acceptance_results.json
```
  Expected: the staged status shows `M  tests/nautilus_acceptance.py` and `A  ` for the six other paths; `7 files changed, 4095 insertions(+)` (measured with a 942-name census: 1,773 + 221 + 1,040 + 42 + 42 + 24 + 953 lines); then only the pre-existing paths; `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`. No push, no tag.

---

### Task 5: Parity, gate, pilot tables, runbook (spec Step 7): sections 5.4 and 5.5, the two registration tables, `RUNBOOK_windows.md`

**Verified before writing (2026-10-28, at HEAD `049306c`, then `f4085cd`, which adds only `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`: no Task 5 step reads or writes it, and the 3.3 guard sees it unchanged; dry run in the scratch clones `$S/plan_step2/task5/clone` (GREEN) and `$S/plan_step2/task5/red` (RED), both copies of Task 4's scratch clone: commit `48ec6eb` "scratch: Tasks 1-3 drafts" plus Task 4's draft, `tools/nautilus/runner.py` md5 `01b576997547d17d8f318fb67f26bac6`, `tests/nautilus_acceptance.py` md5 `8694bc609a52865257309d513d234297`, `tests/nautilus_stub_child.py` md5 `9ff240c01117062c36189839ee072d63`; the real clone was not touched, and no real price row was read):**
- **Task 4's hand-over** (line numbers of that draft). `parity_and_gate` raises `NotImplementedError("spec 5.4 and 5.5 are plan Task 5")` (`tools/nautilus/runner.py:1068-1070`). `_after_registration` (`:1486-1508`) calls it after the `after_step15` hook; an `Exception` becomes G-06 (ERROR, exit 4), a `BaseException` G-07 (ABORTED, exit 5); otherwise it copies `Outcome.withheld_reasons` into the record (`:1507`) and finishes with the Outcome's status and exit code. `_new_record` (`:1227-1234`) starts `parity`, `gate`, `card` and `error` at None, and step 7 sets `provenance = {"p0a": ..., "p0b": None}` (`:1362`). `_earlier_runs` (`:242-259`) lets a WITHHELD record be re-run without `--rerun-of` only when every withheld reason starts with `C-06` (`:252-253`), so P13's reasons keep the leg's own C-id first (**CONTRACT ISSUE 4**). `e1_parity_passed` (`:412-423`) reads `rec["parity"]["hard_pass"] is True` with 12 registration rows, so `parity.hard_pass` is one bool over every column at both cost levels (P0b and P12 included). `_check_values` (`:360-396`) requires `grid == S.grid_from(**axes)`, whose column order follows the axes' key order (`:389-390`), and study_configs entries with exactly the keys `source, symbols, cost_bps, params` (`:393-394`). `write_rehearsal_table` writes tables without `sort_keys` for that reason (`tests/nautilus_acceptance.py:1228-1246`, Task 4's CONTRACT ISSUE 1); the two pilot tables follow the same rule. `main` (`:1733-1769`) knows four modes.
- **Gate, read only.** `validate.walk_forward` (`core/quant/validate.py:345-381`) sets `first = w_is if T - w_is >= w_oos + embargo else min_is`, raises `ValueError(f"need at least {first + embargo + 21} sessions for one walk-forward step, got {T}")` (`:365-367`), and per origin slices `a, b = o + embargo, min(o + embargo + w_oos, T)` and picks `np.nanargmax(_col_sharpe(M[max(0, o - w_is):o]))` (`:370-377`); `WalkForward` is a frozen dataclass (`:332-342`); `_col_sharpe` is `:268-270`. `_decide_strategy` (`:536-622`) reads exactly the 18 predicates of `parity.gate_predicates`: `ci90[0] > 0` and `dsr >= dsr_min` (`:578`), `isfinite(dsr)` (`:593`), `pbo_meaningful` and `flat` (`:544-545`), `pbo_ok` and `pbo_reject` (`:576-577`), the five engine checks (`:579-583`), `min_track_record` (`:584`), the trade floor, whole years and sessions (`:585-586`), `has_bench` (`:557`) and `bench_ok` (`:592`). `score_strategy` is `:492-533`; `ModelCard.to_json` is `:827-828`, and `ModelCard.save` (`:830-834`) overwrites, so the bridge never calls it.
- **Ledger.** `FamilyLedger.snapshot(hash)` (`core/quant/gate_ledger.py:323-330`) returns the registration-time prefix, on which U is counted; `assert_hash_at_run` (`:389-396`) raises `LedgerRefused` (`:87`) when the ledger moved; `config_id` (`:168-171`) hashes `ROW_SET_KEY` with absent keys as None, so a study configuration's row `{rule, params, timing_class}` gives the Lab's id.
- **Strategies.** `S._sma` (`core/quant/strategies.py:111-116`) needs a 2-D array (`np.vstack` of a `(1,)` zero row and a 1-D series raises), so P1's QUANTGEN margins call it on `P[:, None]`. `crypto_trend`'s defaults `(7, 14, 21, 28)` and `(10, 20, 50, 100, 200)` (`:330-331`) equal the runner's `CRYPTO_DEFAULTS`. `Panel` is a frozen dataclass (`:40-48`), so L1-20b replaces `ctx.study_pn` with `dataclasses.replace`.
- **Study, read only.** `run_trend` (`docs/asset_expansion_study.py:271-279`): grid `:274`, benchmark `(pn.prices[1:] / pn.prices[:-1] - 1.0).mean(axis=1)` `:275`, `cost_bps=COST[cost_key], embargo=21` `:278`, called with `"us"` for `S_E1_trend_us` (`:724`). `run_crypto_trend` (`:325-343`): grid `:333`, benchmark `pn.prices[1:, 0] / pn.prices[:-1, 0] - 1.0` `:334`, `cost_bps=COST["crypto"], embargo=1` `:337`, `domain={"hysteresis": (0.0, 0.889)}, n_trials=11` `:339`. The benchmark is aligned with the OOS dates by `bd = dict(zip(dates, bench)); b = np.array([bd[d] for d in wf.dates])` (`:189-190`); `CIT["trend"]` and `CIT["crypto_trend"]` are `:247-254`; `COST` is `V.COST_BP_PER_SIDE` (us 50.0, crypto 10.0).
- **Stored cards** (read only; `docs/asset_expansion/cards/` keeps its 34 files): `S_E1_trend_us.json` (md5 `37e8d72051f0d3d0c29b0a9d39aca11a`; symbols SPY, QQQ, TLT, GLD; the 12-setting grid; 50.0), `S_E1_trend_krx.json` (`3018fd5adb34fde2dcba1015cde86146`; 069500.KS, 152380.KS, 132030.KS, 229200.KS; 3.0), `S_C3_crypto_trend_btcusd.json` (`d0bb0882fb51dec361cf2ddb160186bb`, 10.2's pin; the five lattice values, embargo 1, 10.0; `trials.ledger[0]` names run 2/3's six values), `S_C3_crypto_trend_krwbtc.json` (`40b1e7bfadf6d16246e0012495064704`; KRW-BTC; the lattice; 10.0). The pilot tables' study_configs give 24 distinct config_ids (E1) and 11 (C3): U is at most 24 and 11 (10.1, 10.2).
- **Measured in the dry run (synthetic data only).** F1's 11 rows give P2 0.99999886 and abs ΔSR 0.0145, above P3's 0.01 (11 rows are too few for a Sharpe), so L1-2 asserts 8.2's F1 assertions (P1 = 1; P4 with bar 11 excluded; P7; every row inside P10, largest gap 1.742e-4 at t = 3), not every hard check. N7 (i): P12 at 2x has corr 0.99892 and abs ΔSR 0.0776, P3 at 2x up to 0.0767. The card table of L1-2, L1-5, L1-14, L1-26b, L1-28 and L1-30 (stub child, 1,000 bars, 4 columns) ends CARD_WRITTEN in 2.5 s with both scores INSUFFICIENT_DATA (222 OOS sessions) and worst corr 0.99999968. L2-7: CARD_WRITTEN, both INSUFFICIENT_DATA, worst corr 0.99999905. L2-11 (N6): CARD_WRITTEN, worst corr 0.99999962, worst abs ΔSR 0.00058, 61 s. L2-12: CARD_WRITTEN, drift `[]`, 3 calendar and 2 whole years. `--timing`: 12 runs of 5,600 bars in 15.2 s (1.14 to 1.61 s each), `BacktestEngine` import 0.81 to 0.86 s. `--handoff-report` (scratch clone): every part without error, F1, F2 and N1 equal to their goldens, census diff `[]` against `modules_manylinux_2_35_x86_64.json` (942 names), probe blocked (errno 101), control connect ok, 22 s. Module CLI: `44/57 passed, 0 failed, 13 not run` key unset (35 s), `57/57 passed, 0 failed, 0 not run` key set (3 min 35 s); the same counts through a copy of the redirecting wrapper pointed at the scratch clone (`--suite nautilus`), with `qa/acceptance_results.json` keeping md5 `16c9baa5a1777853521d485d5078e456`.
- **Guards.** With `parity.py` and the new runner modes, `python3 -B -m tests.macro_m0_harness` gives `14/14 passed, 0 failed, 0 not run` (the amended scan, Task 2): no `submit_order`, no upper-case `CANO`, no `nautilus_trader` import, no `IMPORT_MACHINERY` call with a `nautilus` string (the hand-off report's `from tests.nautilus_acceptance import stub_python` is an import statement; rule C2 judges only names under `nautilus_trader`), no denied name. L1-15 passes on the new code. Nothing in `core/`, `data/`, `ui/`, `main.py` or `config.py` changes, so test_08 and test_09 (`tests/acceptance.py:62-75`, `runtime_py()` `:50-55`) and `tests/flet_api_guard.py` are not concerned.
- **Runbook.** python.org is not reachable from the container (the proxy answers 403), so the pinned installer `python-3.13.14-amd64.exe` is UNVERIFIED; 3.13.14 is the patch the owner's own interpreter reported at the tag (`grokteam/out/PREREG_book.json:126`), and `python_minor` "3.13" is all the venv check reads. The runbook's PowerShell block equals spec 7A.2's 31 lines with the two substitutions the spec names (the `$v` patch and the header's PowerShell install line), checked by Step 11's script.

**Files:**
- Create: `tools/nautilus/parity.py`; `docs/nautilus_bridge/registration/pilot1_E1_spy.json`; `docs/nautilus_bridge/registration/pilot2_C3_btcusd.json`; `docs/nautilus_bridge/RUNBOOK_windows.md`. UTF-8 with LF line ends; all ASCII except the `§` of `PARITY_BARS_TEXT` (6.5's text).
- Modify: `tools/nautilus/runner.py` (LF): the module docstring (two edits), `parity_and_gate`'s body, and Task 4's `main` replaced by the three new modes and the new `main`. `tests/nautilus_acceptance.py` (LF): the Task 5 block inserted before the CLI section.
- Test: `tests/nautilus_acceptance.py`, 12 layer-1 and 3 layer-2 tests (the Count Ledger's Task 5 names).
- Not touched: every CRLF file (`tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml`, `config.py`), `tools/nautilus/{launch,sandbox,egress_probe}.py`, `tests/nautilus_stub_child.py`, the goldens, `core/`, `docs/asset_expansion/`, `paper_live/`, `grokteam/`, and `qa/acceptance_results.json` (md5 `16c9baa5a1777853521d485d5078e456` before and after every step).

**Interfaces:**
- Consumes: C1 (`BridgeRefusal`, section-7 ids, the JSON bytes of `write_record`, host and platform tags); C2 (`make_tempdir`, `build_launch`, `run_child`, `cleanup_tempdir`, `resolve_unshare`, `read_venv`, `venv_mismatches`, `parent_nautilus`, `parent_pyarrow`, `host_tag`, `EGRESS_PROBE`, `GOLDEN_DIR`, `TIMEOUT_S`); C3 and C6 (the child's modes, the manifest's `input.cost_bps` and `input.stress` echoes); C8's Task 4 helpers (`stub_python`, `stub_cmd`, `stub_probe_cmd`, `synth_prices`, `synth_rf`, `write_rehearsal_table`, `run_rehearsal`) and Task 4's private test helpers of **CONTRACT ISSUE 5**; C10 (`run` and its hooks, `RunContext`, `Leg`, `Outcome`, `rebuild_returns`, `table_sha256`, `code_sha256`, `host_fingerprint`, `judge_census`, `write_record`) and the Task 4 runner internals of **CONTRACT ISSUE 5**; `core.quant.validate`, `core.quant.gate_ledger`, `core.quant.strategies` and the study module, read only.
- Produces: C11 in full (`cents`, `select_matched`, `gate_predicates`, `agree`, `reference_drift`, `hand_off`); C10's Task 5 part (the seam's body; `--fingerprint --table <t>`, `--timing`, `--handoff-report`); C12's card (6.5), the run record's `parity`, `gate`, `card` and `provenance.p0b` (6.3), the hand-off report and the two registration tables (6.6).
- Produces beyond the contract: in `parity`, the constants `BARS`, `OWNER_BARS`, `HARD`, `WARNINGS`, `ENGINE_TEXT`, `SELECTION_TEXT`, `PARITY_SCOPE`, `PARITY_BARS_TEXT`, `CLAIM_PREFIXES`, `STUDY_BENCH`, `CITATIONS`, `REFERENCE_FLOATS`, `PROTOCOL_KEYS` and the functions `plain`, `corr` (**CONTRACT ISSUE 1**), `mdd`, `pair_checks`, `decision_bars`, `qg_margins`, `p1`, `p7`, `leg_checks`, `study_benchmark`, `p0b`, `p11`, `p12`, `study_config_ids`, `trial_counts`, `card_rules` (**CONTRACT ISSUE 2**), `parity_summary`, `build_card`, `write_card`, `check_parity`; in `runner`, `HANDOFF_SCHEMA` (`"nautilus-bridge-handoff/1"`), `BRANCH`, `TIMING_BARS`, `TIMING_ENGINE`, `TIMING_GRID`, `FIREWALL_COMMANDS`, `fingerprint_mode` (**CONTRACT ISSUE 3**), `timing_inputs`, `import_micros`, `run_timing`, `timing_mode`, `handoff_report`, `handoff_mode` and their private helpers.

**Withheld reasons and exit codes** (section 7; the record's `withheld_reasons`, **CONTRACT ISSUE 4**): a leg that failed P13 contributes its own `C-nn: ...` reasons with ` (column <c> (<theta>), <s>x)` appended (G-01); a failed hard check `P0b`, `P1` to `P4`, `P7` or `P12` contributes `P<n>: ...` (G-01); `G-03: walk_forward raised ...`, `G-03: walk_forward (P11, Nautilus's own selection) raised ...` or `G-03: score_strategy raised ...`; `G-02: decision mismatch: quantgen <d>, nautilus <d>; predicates differ: <name> <qg>/<nt>, ...` or `G-02: benchmark test dropped`; `G-08: reference drift: <fields>`; `G-05: ledger moved after registration: <LedgerRefused>`. Any of them gives WITHHELD, exit 1, no card. G-04 (`GATE` differs from the snapshot, checked at the end of every hand-off) gives ERROR, exit 4, no card, with `record["error"]["message"]` = `G-04: GATE differs from its snapshot after scoring: [<keys>]`. Otherwise CARD_WRITTEN, exit 0. Warnings P5, P6, P8, P9 and P10 go into `record["parity"]["warnings"]` and the card's `stats.parity` and never withhold. An unexpected exception inside `hand_off` stays Task 4's G-06 (ERROR, 4); a `KeyboardInterrupt` G-07 (ABORTED, 5).

**Counts (Count Ledger as deltas).** Task 1 Step 0 measured the full-suite baseline B = `<P>/<N> passed, <F> failed, <R> not run`. At Task 4's commit, where this task starts, the full suite through the wrapper is `<P+34>/<N+44> passed, <F> failed, <R+10> not run`, and the module CLI gives `32/42 passed, 0 failed, 10 not run` (key unset). Task 5 adds 15 `nautilus` rows (12 layer 1 PASS, 3 layer 2 NOT_RUN with the key unset) and no `macro` row. After Task 5: full suite `<P+46>/<N+59> passed, <F> failed, <R+13> not run` with B's FAIL set; `--suite nautilus` `44/57 passed, 0 failed, 13 not run` (key unset) and `57/57 passed, 0 failed, 0 not run` (key set), absolute, because the suite started at 0; `python3 -B -m tests.macro_m0_harness` stays `14/14 passed, 0 failed, 0 not run`. Reference example only: with B = `745/870 passed, 1 failed, 124 not run` (2026-10-26), the Task 5 row is `791/929 passed, 1 failed, 137 not run`.

Every command block starts with the line `S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen` (a later session puts its own scratchpad in `S`).

- [ ] **Step 1: Check the starting point** (no file changes).
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git log -1 --format='%h %s'; git status --short --untracked-files=all; md5sum qa/acceptance_results.json
ls tools/nautilus/parity.py docs/nautilus_bridge/registration docs/nautilus_bridge/RUNBOOK_windows.md 2>&1 | grep -c 'No such file'
grep -c 'raise NotImplementedError("spec 5.4 and 5.5 are plan Task 5")' tools/nautilus/runner.py
python3 -B -m tests.nautilus_acceptance 2>&1 | tail -1
```
Expected: HEAD is Task 4's commit; `git status` lists only the paths Task 1 Step 0 recorded as already modified or untracked (no `tools/nautilus/` or `docs/nautilus_bridge/` entry); `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`; `3`; `1`; `32/42 passed, 0 failed, 10 not run`.

- [ ] **Step 2: Write the failing tests.** In `tests/nautilus_acceptance.py` (LF), with the Edit tool, `old_string` is these four lines:
```python
# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
```
and `new_string` is the block below followed by the same four lines. The block uses Task 4's helpers `_runner`, `_bdates`, `_md5`, `_small_table`, `_captured`, `_plain_row`, `_fixture_series` and `SPEC_FILLS` (**CONTRACT ISSUE 5**). Every new test is guarded by `tests()`; temp dirs only; no real price file is read (L1-29 reads the four stored cards' JSON and the study's source with `ast`, and loads the study module as Task 4's `load_study` does). With Task 4's file at md5 `8694bc609a52865257309d513d234297`, the result has md5 `baffe7564cb291040d81028f859f39b9`. Both were measured on Task 4's scratch clone, which carried an earlier draft of Task 3's test block (Plan status), so the file built from this plan has other md5s; the check is then `git diff --numstat tests/nautilus_acceptance.py`, which prints 619 insertions and 0 deletions.
```python
# --------------------------------------------------------------------------- #
# Plan Task 5 (spec Step 7): parity, selection, gate hand-off, card, pilot tables and the three new runner modes
# --------------------------------------------------------------------------- #
REGISTRATION = ROOT / "docs" / "nautilus_bridge" / "registration"
PILOT_TABLES = {"E1-SPY": REGISTRATION / "pilot1_E1_spy.json", "C3-BTCUSD": REGISTRATION / "pilot2_C3_btcusd.json"}
CARDS = ROOT / "docs" / "asset_expansion" / "cards"
CARD_AXES = {"rule": ["sma", "tsmom"], "lookback": [126, 252], "step": [21]}   # the L2-7 grid: four columns
PILOT1_AXES = {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]}
PILOT2_AXES = {"hysteresis": [0.0, 0.222, 0.444, 0.667, 0.889]}
ENGINE_6_5 = ("per-column event-driven replication (nautilus_trader 1.231.0 BacktestEngine, same-bar close); "
              "walk-forward column switches are not executed in either engine")
SCOPE_6_5 = "parity validates the engine, not the data; P0 ties the inputs to the study's loaders"
F1_DECISIONS = ((3, 1, "buy"), (5, 0, "sell"), (7, 1, "buy"), (9, 1, "hold"), (11, 0, "sell"))      # spec 8.2
N8_BASE = {"sr_oos": 1.19, "se_lo": 0.3, "ci90": (0.72, 1.64), "sr_is": 1.3, "oos_is": 0.9, "dsr": 0.9999, "pbo": 0.19,
           "pbo_slope": 0.0, "prob_loss_oos": 0.0, "sr_stress": 1.16, "turnover_annual": 10.0, "n_trades": 144,
           "n_sessions": 3634, "years_positive": 0.82, "n_years": 11, "max_year_share": 0.2, "plateau": 1.0,
           "edge": False, "regime": {}, "total_return": 5.0, "max_drawdown": -0.5, "haircut_sr": 0.7, "bench_sr": 0.9,
           "n_trials": 11, "n_configs": 5, "bench_diff": 0.3, "bench_p": 0.07}     # near pilot 2's stored card (N8)


def _parity():
    """tools.nautilus.parity, imported by each test that needs it, so a missing module fails only Task 5's tests."""
    from tools.nautilus import parity
    return parity


def _days(n: int) -> list[str]:
    """Spec 8.2's crypto calendar: pd.date_range("2001-01-01", periods=n, freq="D")."""
    import pandas as pd
    return [d.strftime("%Y-%m-%d") for d in pd.date_range("2001-01-01", periods=n, freq="D")]


def _card_table(tmp: Path, **fields) -> Path:
    """A synthetic SPY-like table whose stub-child rehearsal ends CARD_WRITTEN: synth_prices(7, 1000, 100, 150),
    synth_rf(1000), the four columns of CARD_AXES at 50 bp, embargo 21."""
    return write_rehearsal_table(tmp, prices=synth_prices(7, 1000, 100.0, 150.0), dates=_bdates(1000),
                                 rf=synth_rf(1000), axes=CARD_AXES, **fields)


def _rehearse(table: Path, tmp: Path, **kw) -> tuple[int, dict | None, str]:
    """run_rehearsal with stdout captured: (exit code, the newest run.json, what the runner printed)."""
    (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, **kw))
    return code, rec, out


def _f1_leg(stress: int, *, rf, commissions=None, echo_stress=None):
    """A Leg of F1 (spec 8.2) from its golden fills, rebuilt by the runner; commissions and the manifest's stress echo
    can be planted."""
    from decimal import Decimal
    runner = _runner()
    capital, ts, closes = _fixture_series("F1")
    fills = [{"ts_event": ts[b], "order_side": side, "last_qty": Decimal(q), "last_px": Decimal(px),
              "commission": Decimal(c if commissions is None else commissions[k]), "commission_ccy": "USD",
              "trade_id": f"T{k}", "venue_order_id": f"O{k}"} for k, (b, side, q, px, c) in enumerate(SPEC_FILLS["F1"])]
    decisions = [{"i": i, "ts_event": ts[i], "decision": d, "margin": 0.0, "action": a} for i, d, a in F1_DECISIONS]
    manifest = {"input": {"cost_bps": "50", "stress": str(echo_stress or stress)}}
    rebuilt = runner.rebuild_returns(fills, closes, ts, rf, Decimal(capital))
    return runner.Leg(0, stress, {}, manifest, fills, decisions, [], rebuilt, [])


def _f1_checks(leg, weights, rf) -> dict:
    """parity.leg_checks on F1 with QUANTGEN's pnl at the leg's cost level from `weights`."""
    from core.quant import strategies as S
    _, _, closes = _fixture_series("F1")
    pnl, turnover = S.simulate(closes, weights[:, None], cost_bps=50.0 * leg.stress, cash_daily=rf)
    return _parity().leg_checks(leg, strategy="trend_switch", theta={"rule": "sma", "lookback": 3, "step": 2},
                                closes=closes, rf=rf, weights=weights, pnl=pnl, turnover=turnover, cost_bps=50.0)


def _failed(x: dict) -> list[str]:
    return [p for p in _parity().HARD if p in x and not x[p]["pass"]]


def _qg_matrices(closes, fn, grid, cost: float, rf):
    """QUANTGEN's pnl, pnl at 2x and turnover, column by column as the runner's step 13 computes them."""
    import numpy as np
    from core.quant import strategies as S
    cols = [S.simulate(closes, np.asarray(fn(closes, **g), dtype=float), cost_bps=cost, cash_daily=rf) for g in grid]
    stress = [S.simulate(closes, np.asarray(fn(closes, **g), dtype=float), cost_bps=2 * cost, cash_daily=rf)[0]
              for g in grid]
    return np.column_stack([c[0] for c in cols]), np.column_stack(stress), np.column_stack([c[1] for c in cols])


def _same_wf(a, b) -> list[str]:
    """The fields where two WalkForward objects differ, arrays compared by their bytes."""
    import numpy as np
    out = []
    for k in ("dates", "origins", "chosen", "n_configs", "note"):
        out += [k] if getattr(a, k) != getattr(b, k) else []
    for k in ("pnl", "pnl_stress", "turnover", "is_sharpes"):
        x, y = np.asarray(getattr(a, k)), np.asarray(getattr(b, k))
        out += [k] if x.shape != y.shape or x.dtype != y.dtype or x.tobytes() != y.tobytes() else []
    return out


def _reference_stats(closes, dates, grid, *, cost: float, embargo: int, n_trials: int, domain) -> tuple:
    """The stored-card reference as the study built it (L2-12, L1-29): asdict(score_strategy) of QUANTGEN's matrix,
    plus chosen_last, with n_years by the calendar-years rule that wrote the stored cards. Returns (stats, sc, wf)."""
    import numpy as np
    from dataclasses import asdict
    from core.quant import strategies as S, validate
    pnl, stress, turnover = _qg_matrices(closes, S.crypto_trend, grid, cost, np.zeros(len(closes)))
    wf = validate.walk_forward(pnl, dates[1:], turnover=turnover, pnl_stress=stress, embargo=embargo)
    bench = dict(zip(dates[1:], closes[1:] / closes[:-1] - 1.0))
    sc = validate.score_strategy(wf, grid=grid, full_pnl=pnl, n_trials=n_trials,
                                 bench_daily=np.array([bench[d] for d in wf.dates]), seed=11, domain=domain)
    stats = {k: v for k, v in asdict(sc).items() if k not in ("lines", "regime")}
    stats.update(chosen_last=grid[wf.chosen[-1]], n_years=len({d[:4] for d in wf.dates}))
    return stats, sc, wf


def _write_card_file(path: Path, stats: dict) -> str:
    path.write_text(json.dumps({"card_id": "S_REHEARSAL_reference", "stats": stats}, indent=1, ensure_ascii=False),
                    encoding="utf-8", newline="\n")
    return _md5(path)


def _crypto_table(tmp: Path, n: int, **fields) -> Path:
    """A synthetic BTC-like table (spec 8.2's L2-12 generator, n days from 2001-01-01), pilot 2's grid, no rf."""
    return write_rehearsal_table(tmp, like="C3-BTCUSD", prices=synth_prices(5, n, 400.0, 60000.0), dates=_days(n),
                                 axes=PILOT2_AXES, **fields)


def test_l1_02_parity_functions():
    """L1-2 (5.4.1, 5.5; N2, N4, N7, N8): F1 and F1r meet 8.2's assertions (P1 = 1, P4, P7) and stay inside the P10
    bound; N2 fails P1, P2 and P4; the P1 exemption takes a 1e-10 QUANTGEN margin, not 2e-9; P7's tie (0.13 passes,
    0.12 fails) and N7 (ii) to (iv); N4's P11 mismatches at gap 0 with QUANTGEN's selection kept; N8 through
    parity.agree; a planted P5 warning still writes a card."""
    import numpy as np
    from decimal import Decimal
    from core.quant import strategies as S, validate
    parity = _parity()
    _, ts, closes = _fixture_series("F1")
    W = np.asarray(S.trend_switch(closes, rule="sma", lookback=3, step=2), dtype=float)[:, 0]
    for rf in (np.zeros(12), np.full(12, 0.0001)):                      # F1, F1r: 8.2's assertions
        x = _f1_checks(_f1_leg(1, rf=rf), W, rf)
        assert x["P1"]["value"] == 1.0 and x["P10"]["rows_over"] == [] and x["P4"]["pass"] and x["P7"]["pass"], x
        assert x["P4"]["fill_bars"] == [3, 5, 7] and abs(x["P10"]["max_gap"] - 1.742e-4) < 1e-6, x["P10"]
    flipped = W.copy()
    flipped[9:11] = 0.0                                                 # N2: the hold at bar 9 flipped to off
    x = _f1_checks(_f1_leg(1, rf=np.zeros(12)), flipped, np.zeros(12))
    assert x["P1"]["value"] < 1 and {"P1", "P2", "P4"} <= set(_failed(x)), x
    margins = np.full(12, 0.5)
    for planted, exempt in ((1e-10, True), (2e-9, False)):
        margins[9] = planted
        got = parity.p1(_f1_leg(1, rf=np.zeros(12)).decisions, flipped, margins, [3, 5, 7, 9, 11])
        assert got["pass"] is exempt and got["mismatches"] == [9] and len(got["exempt"]) == int(exempt), got
    tie = [{"last_qty": Decimal(25), "last_px": Decimal("1.00"), "commission": Decimal(c), "commission_ccy": "USD"}
           for c in ("0.13", "0.12")]
    echo = {"input": {"cost_bps": "50", "stress": "1"}}
    assert parity.cents(Decimal("0.125")) == 13 and parity.p7(tie[:1], echo, cost_bps=50.0, stress=1)["pass"]
    assert not parity.p7(tie[1:], echo, cost_bps=50.0, stress=1)["pass"]
    half = [c for *_, c in SPEC_FILLS["F1"]]                            # 1x commissions on a 2x leg
    x = _f1_checks(_f1_leg(2, rf=np.zeros(12), commissions=half), W, np.zeros(12))
    assert x["P7"]["bad_fills"] == [0, 1, 2, 3] and x["P7"]["echo"] is True and "P7" in _failed(x), x["P7"]   # N7 (ii)
    x = _f1_checks(_f1_leg(2, rf=np.zeros(12), commissions=half, echo_stress=1), W, np.zeros(12))
    assert x["P7"]["bad_fills"] == [0, 1, 2, 3] and x["P7"]["echo"] is False, x["P7"]               # N7 (iii)
    n = 1500
    dates, closes2 = _bdates(n)[1:], synth_prices(11, n, 100.0, 150.0)
    grid = S.grid_from(**PILOT1_AXES)
    pnl, stress, turnover = _qg_matrices(closes2, S.trend_switch, grid, 50.0, 0.0)
    wf_qg = validate.walk_forward(pnl, dates, turnover=turnover, pnl_stress=stress, embargo=21)
    wf_i = parity.select_matched(pnl, pnl, turnover, dates, wf_qg, embargo=21)                       # N7 (i)
    p12_i = parity.p12(wf_qg, wf_i)
    p3_2x = [parity.pair_checks(pnl[:, g], stress[:, g])["abs_dsr"] for g in range(len(grid))]
    print(f"N7 (i): P12 2x {p12_i['2x']}; P3 at 2x per column, max {max(p3_2x):.5f} (bar 0.01)")
    assert p12_i["1x"]["pass"] and not p12_i["2x"]["pass"] and max(p3_2x) > parity.BARS["P3"], (p12_i, p3_2x)
    shifted = pnl + 0.0001                                                                            # N7 (iv)
    wf_iv = parity.select_matched(shifted, stress + 0.0001, turnover, dates, wf_qg, embargo=21)
    pairs = [parity.pair_checks(shifted[:, g], pnl[:, g]) for g in range(len(grid))]
    assert all(p["corr"] >= parity.BARS["P2"] and p["abs_dsr"] > parity.BARS["P3"] for p in pairs), pairs
    p12_iv = parity.p12(wf_qg, wf_iv)["1x"]
    assert p12_iv["corr"] >= parity.BARS["P2"] and p12_iv["abs_dsr"] > parity.BARS["P3"] and not p12_iv["pass"], p12_iv
    base = np.random.default_rng(3).normal(0.0004, 0.01, size=(1000, 1))                            # N4
    M = np.hstack([base, base])
    Mn = M.copy()
    Mn[:, 1] += 1e-6
    d4 = _bdates(1001)[1:]
    wf4 = validate.walk_forward(M, d4, turnover=np.zeros_like(M), pnl_stress=M, embargo=21)
    own = validate.walk_forward(Mn, d4, turnover=np.zeros_like(M), pnl_stress=Mn, embargo=21)
    rep = parity.p11(wf4, own)
    assert rep and all(r["quantgen"] == 0 and r["nautilus"] == 1 and r["is_sharpe_gap"] == 0.0 for r in rep), rep
    matched = parity.select_matched(Mn, Mn, np.zeros_like(M), d4, wf4, embargo=21)
    assert matched.chosen == wf4.chosen and parity.p12(wf4, matched)["1x"]["pass"], matched.chosen

    def scored(**kw):
        s = validate.StrategyScore(**dict(N8_BASE, **kw))
        validate._decide_strategy(s)
        return s
    gate = validate.GATE
    assert parity.agree(scored(pbo=0.19), scored(pbo=0.21), gate) == (True, None)                     # N8 (a)
    assert parity.agree(scored(n_configs=12, bench_p=0.5, prob_loss_oos=0.09),
                        scored(n_configs=12, bench_p=0.5, prob_loss_oos=0.11), gate) == (False, "decision mismatch")
    assert parity.agree(scored(prob_loss_oos=0.09), scored(prob_loss_oos=0.11), gate) == (False, "decision mismatch")
    assert parity.agree(scored(bench_p=float("nan")), scored(bench_p=float("nan")), gate) == (
        False, "benchmark test dropped")
    preds = parity.gate_predicates(scored(), gate)
    assert len(preds) == 18 and all(type(v) is bool for v in preds.values()), preds

    def plant_p5(ctx):                       # one fill 2e-6 above its close; its commission recomputed, so P7 holds
        leg = ctx.legs[(0, 1)]
        f = leg.fills[0]
        f["last_px"] = (f["last_px"] * Decimal("1.000002")).quantize(Decimal("0.000000001"))
        f["commission"] = Decimal(parity.cents(f["last_qty"] * f["last_px"] * Decimal("0.005"))) / 100
    with tempfile.TemporaryDirectory(prefix="qgnb_l102_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_card_table(tmp), tmp, hooks={"after_step15": plant_p5})
        assert (code, rec["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        assert [w for w in rec["parity"]["warnings"] if w.startswith("P5: column 0")] and rec["parity"]["hard_pass"]


def test_l1_05_rerun_policy_r17():
    """L1-5 (5.3.5; OPS-R2-7, OPS-R3-5, QA-R3-3, QA-R2-3): after a first run ends CARD_WRITTEN, the same table
    refuses with R-17, also with a new owner_confirmed and re-saved with a BOM and CRLF; with --rerun-of and a reason
    it appends 0 rows, records appended false for every row, names the first run in earlier_runs and supersedes, and
    prints a planted IN_PROGRESS record."""
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l105_") as name:
        tmp = Path(name)
        table = _card_table(tmp)
        code, first, out = _rehearse(table, tmp)
        assert (code, first["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        ledger = tmp / "ledgers" / "E1.jsonl"
        old = time.time() - 601
        os.utime(ledger, (old, old))                    # R-16's freshness passes from here on (QA-R2-3)
        t = json.loads(table.read_text(encoding="utf-8"))
        sha = runner.table_sha256(t)
        signed = tmp / "signed.json"
        confirmed = f"Geon Koh, 2026-10-28, table {sha[:16]}, code {'0' * 16}"
        signed.write_text(json.dumps(dict(t, owner_confirmed=confirmed), indent=1, ensure_ascii=False),
                          encoding="utf-8", newline="\n")
        bom = tmp / "bom.json"
        crlf = json.dumps(t, indent=1, ensure_ascii=False).replace("\n", "\r\n")
        bom.write_bytes(b"\xef\xbb\xbf" + crlf.encode("utf-8"))
        for path in (table, signed, bom):
            code, rec, out = _rehearse(path, tmp)
            assert code == 2 and rec["bridge_run_id"] == first["bridge_run_id"], (path.name, out[-800:])
            assert f"R-17: earlier runs of this table: {first['bridge_run_id']} CARD_WRITTEN" in out, out[-800:]
        planted = tmp / "out" / f"NB-20000101T000000000000Z-{sha[:8]}"
        planted.mkdir()
        (planted / "run.json").write_text(json.dumps({"bridge_run_id": planted.name, "status": "IN_PROGRESS",
                                                      "table": {"table_sha256": sha}}), encoding="utf-8", newline="\n")
        code, rec, out = _rehearse(table, tmp, rerun_of=first["bridge_run_id"], reason="L1-5 re-run")
        assert code == 0 and rec["bridge_run_id"] != first["bridge_run_id"], out[-1500:]
        assert f"earlier run {planted.name} ended IN_PROGRESS" in out, out[-1500:]
        assert rec["supersedes"] == first["bridge_run_id"] and rec["rerun_reason"] == "L1-5 re-run", rec["supersedes"]
        assert {e["bridge_run_id"] for e in rec["earlier_runs"]} == {first["bridge_run_id"], planted.name}
        reg = rec["registration"]
        assert reg["n_raw_before"] == reg["n_raw_after"] == 4 and not any(r["appended"] for r in reg["rows"]), reg
        assert gate_ledger.family_ledger("E1", tmp / "ledgers").n_raw == 4


def test_l1_13_parity_failure_withholds_without_card():
    """L1-13 (G-01): a parity failure (the stub's --fee-1x charges 1x at stress 2, N7) writes no card and exactly one
    WITHHELD record into the temp output dir, exit 1."""
    with tempfile.TemporaryDirectory(prefix="qgnb_l113_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_small_table(tmp, n=600), tmp, flags=("--fee-1x",))
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert any(r.startswith("P7: column 0 (rule=sma, lookback=126, step=21), 2x") for r in rec["withheld_reasons"])
        assert rec["parity"]["hard_pass"] is False and rec["gate"]["quantgen"] is None, rec["gate"]
        assert sorted(p.name for p in (tmp / "out").iterdir() if p.name != ".locks") == [rec["bridge_run_id"]]
        assert sorted(p.name for p in (tmp / "out" / rec["bridge_run_id"]).iterdir()) == ["run.json"]
        assert out.splitlines()[-1].startswith("STATUS WITHHELD exit=1 record=")


def test_l1_14_gate_unchanged_and_g04():
    """L1-14 (5.5 step 6): GATE is deep-equal before and after a synthetic end-to-end scoring that writes a card; a
    score_fn that mutates GATE gives G-04: ERROR, exit 4, no card."""
    import copy
    from core.quant import validate
    saved = copy.deepcopy(validate.GATE)

    def mutating(wf, **kw):
        validate.GATE["dsr_min"] = 0.5
        return validate.score_strategy(wf, **kw)
    try:
        with tempfile.TemporaryDirectory(prefix="qgnb_l114_") as name:
            tmp = Path(name)
            code, rec, out = _rehearse(_card_table(tmp / "a"), tmp / "a")
            assert (code, rec["status"]) == (0, "CARD_WRITTEN") and validate.GATE == saved, out[-1500:]
            code, rec, out = _rehearse(_card_table(tmp / "b"), tmp / "b", score_fn=mutating)
            assert (code, rec["status"], rec["card"]) == (4, "ERROR", None), out[-1500:]
            want = "G-04: GATE differs from its snapshot after scoring: ['dsr_min']"
            assert rec["error"]["message"] == want, rec["error"]
            assert not list((tmp / "b" / "out" / rec["bridge_run_id"]).glob("NB_*.json"))
            assert out.splitlines()[-1].startswith("STATUS ERROR exit=4 record=")
    finally:
        validate.GATE.clear()
        validate.GATE.update(saved)


def test_l1_20b_p0b_benchmark_withholds():
    """L1-20's P0b case (5.4.1; QUANT-1): the benchmark from the runner's rounded closes equals the study's
    expression on the study's prices, byte for byte; a doctored study panel (one price moved by 1e-6 after step 15)
    withholds with P0b, exit 1, and the record's provenance says so."""
    import dataclasses
    from types import SimpleNamespace
    import numpy as np
    parity = _parity()
    closes = synth_prices(7, 600, 100.0, 150.0)
    assert parity.p0b("trend_switch", closes, closes[:, None])["pass"] and parity.p0b("crypto_trend", closes,
                                                                                    closes[:, None])["pass"]
    for strategy, text in parity.STUDY_BENCH.items():
        pn = SimpleNamespace(prices=closes[:, None])
        expected = np.asarray(eval(text, {"pn": pn}))                # the study's own text, evaluated
        assert parity.study_benchmark(strategy, closes[:, None]).tobytes() == expected.tobytes(), strategy

    def doctor(ctx):
        prices = np.array(ctx.study_pn.prices, dtype=float)
        prices[300, 0] += 1e-6
        ctx.study_pn = dataclasses.replace(ctx.study_pn, prices=prices)
    with tempfile.TemporaryDirectory(prefix="qgnb_l120b_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_small_table(tmp / "a", n=600), tmp / "a")
        assert rec["provenance"]["p0b"]["pass"] is True, rec["provenance"]
        assert not any(r.startswith("P0b") for r in rec["withheld_reasons"]), rec["withheld_reasons"]
        code, rec, out = _rehearse(_small_table(tmp / "b", n=600), tmp / "b", hooks={"after_step15": doctor})
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert rec["provenance"]["p0b"] == {"pass": False, "rows": 599, "study_rows": 599, "first_difference": 299}
        assert any(r.startswith("P0b: the benchmark differs") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


def test_l1_21_select_matched_reproduces_wf_qg():
    """L1-21 (5.4.2): select_matched on QUANTGEN's own matrices reproduces walk_forward's result field by field, bit
    for bit, for pilot 1's grid (embargo 21, with a cash rate) and pilot 2's (embargo 1)."""
    import numpy as np
    from core.quant import strategies as S, validate
    parity = _parity()
    cases = (("trend", synth_prices(7, 1500, 100.0, 150.0), _bdates(1500), S.trend_switch, PILOT1_AXES, 50.0,
              synth_rf(1500), 21),
             ("crypto", synth_prices(5, 1600, 400.0, 60000.0), _days(1600), S.crypto_trend, PILOT2_AXES, 10.0,
              np.zeros(1600), 1))
    for label, closes, dates, fn, axes, cost, rf, embargo in cases:
        grid = S.grid_from(**axes)
        pnl, stress, turnover = _qg_matrices(closes, fn, grid, cost, rf)
        wf = validate.walk_forward(pnl, dates[1:], turnover=turnover, pnl_stress=stress, embargo=embargo)
        got = parity.select_matched(pnl, stress, turnover, dates[1:], wf, embargo=embargo)
        assert len(wf.origins) > 3 and _same_wf(got, wf) == [], (label, _same_wf(got, wf))


def test_l1_26b_ledger_moved_g05():
    """L1-26's G-05 case (5.5 step 7): an after_step16 hook that appends a row to the family ledger after
    registration makes assert_hash_at_run raise: WITHHELD "ledger moved after registration", exit 1, no card."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l126b_") as name:
        tmp = Path(name)

        def append(ctx):
            gate_ledger.register_trial(ctx.ledger, _plain_row("E1", 99), script="tests/nautilus_acceptance.py")
        code, rec, out = _rehearse(_card_table(tmp), tmp, hooks={"after_step16": append})
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert [r for r in rec["withheld_reasons"] if r.startswith("G-05: ledger moved after registration: E1:")], (
            rec["withheld_reasons"])
        assert gate_ledger.family_ledger("E1", tmp / "ledgers").n_raw == 5
        assert not list((tmp / "out" / rec["bridge_run_id"]).glob("NB_*.json"))


def test_l1_28_card_and_record_bytes():
    """L1-28 (5.5 steps 8 and 9; QA-9, OPS-12): the record's card md5 equals the md5 of the card's bytes; results_file
    is the run id; the card has no carriage return; writing a card to an existing path raises."""
    parity = _parity()
    with tempfile.TemporaryDirectory(prefix="qgnb_l128_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_card_table(tmp), tmp)
        assert (code, rec["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        path = Path(rec["card"]["path"])
        raw = path.read_bytes()
        assert path.parent.name == rec["bridge_run_id"] and path.name == "NB_E1_trend_spy.json", path
        assert rec["card"]["md5"] == hashlib.md5(raw).hexdigest() and b"\r" not in raw
        card = json.loads(raw.decode("utf-8"))
        assert (card["results_file"], card["results_md5"]) == (rec["bridge_run_id"], ""), card["results_file"]
        assert card["card_id"] == "NB_E1_trend_spy", card["card_id"]
        assert card["decision"] == rec["gate"]["nautilus"]["decision"] == rec["gate"]["quantgen"]["decision"]
        try:
            parity.write_card(path, "{}")
        except FileExistsError:
            pass
        else:
            raise AssertionError("write_card overwrote an existing card")
        assert path.read_bytes() == raw


def test_l1_29_trial_counts_protocol_and_reference_drift():
    """L1-29 (QUANT-4, QUANT-R2-5, QUANT-R3-1, QUANT-R3-3, QUANT-R4-1): both pilot tables' study_configs equal the
    stored cards' grids, symbols and costs and 10.2's run 2/3 values; n_trials = family_n_raw + U on planted rows;
    each table's embargo, cost, grid, domain and the benchmark expression equal the study's calls; reference_drift on
    hand-built scores; pilot 2's reference md5; a stub rehearsal whose reference moves one float by 2e-9 is WITHHELD
    "reference drift", exit 1."""
    import ast
    import numpy as np
    from core.quant import gate_ledger, validate
    parity, runner = _parity(), _runner()
    tables = {k: json.loads(p.read_text(encoding="utf-8-sig")) for k, p in PILOT_TABLES.items()}
    cards = {n: json.loads((CARDS / f"{n}.json").read_text(encoding="utf-8")) for n in (
        "S_E1_trend_us", "S_E1_trend_krx", "S_C3_crypto_trend_btcusd", "S_C3_crypto_trend_krwbtc")}

    def from_card(c):
        return [(sorted(c["universe"]["symbols"]), c["costs"]["cost_bps"], g) for g in c["rules"]["grid"]]
    have = {k: [(c["symbols"], c["cost_bps"], c["params"]) for c in t["study_configs"]] for k, t in tables.items()}
    assert have["E1-SPY"] == from_card(cards["S_E1_trend_us"]) + from_card(cards["S_E1_trend_krx"])
    runs23 = [(["BTC-USD"], 10.0, {"hysteresis": h}) for h in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5)]
    assert have["C3-BTCUSD"] == runs23 + from_card(cards["S_C3_crypto_trend_krwbtc"])
    ledger_note = cards["S_C3_crypto_trend_btcusd"]["trials"]["ledger"][0]
    assert "run 2/3: hysteresis [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]" in ledger_note, ledger_note
    t1 = tables["E1-SPY"]
    with tempfile.TemporaryDirectory(prefix="qgnb_l129_") as name:
        ledger = gate_ledger.family_ledger("E1", Path(name))
        for g in t1["grid"][:3]:                                    # three bridge rows
            gate_ledger.register_trial(ledger, runner.ledger_row(t1, g, span=("2004-12-01", "2026-09-25"),
                                                                 run_utc="2026-10-28T00:00:00Z", anchor="UNVERSIONED",
                                                                 bridge_run_id="NB-test"))
        for c in t1["study_configs"][:2] + t1["study_configs"][12:13]:    # two US Lab rows and one KRX row
            params = dict(c["params"], symbols=sorted(c["symbols"]), cost_bps=float(c["cost_bps"]))
            gate_ledger.register_trial(ledger, dict(_plain_row("E1", 0), params=params,
                                                    market="US" if c["cost_bps"] == 50.0 else "KR"))
        counts = parity.trial_counts(t1, ledger.rows())
    assert {k: counts[k] for k in ("len_grid", "family_n_raw", "market_n_raw", "U", "n_trials")} == {
        "len_grid": 12, "family_n_raw": 6, "market_n_raw": 5, "U": 21, "n_trials": 27}, counts
    assert len(set(parity.study_config_ids(t1))) == 24 and len(set(parity.study_config_ids(tables["C3-BTCUSD"]))) == 11
    study = runner.load_study(ROOT)
    tree = ast.parse((ROOT / "docs" / "asset_expansion_study.py").read_text(encoding="utf-8"))
    fns = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}

    def calls(fn, name):
        return [n for n in ast.walk(fns[fn]) if isinstance(n, ast.Call) and ast.unparse(n.func).endswith(name)]

    def bench_text(fn):
        return [ast.unparse(n.value) for n in ast.walk(fns[fn]) if isinstance(n, ast.Assign)
                and ast.unparse(n.targets[0]) == "bench"][0]
    for fn, pilot, cost_key, strategy in (("run_trend", "E1-SPY", "us", "trend_switch"),
                                          ("run_crypto_trend", "C3-BTCUSD", "crypto", "crypto_trend")):
        t = tables[pilot]
        axes = {k.arg: ast.literal_eval(k.value) for k in calls(fn, "grid_from")[0].keywords}
        card_kw = {k.arg: k.value for k in calls(fn, "strategy_card")[0].keywords}
        domain = ast.literal_eval(card_kw["domain"]) if "domain" in card_kw else None
        assert t["axes"] == axes and t["grid"] == runner.S.grid_from(**axes) and list(t["axes"]) == list(axes), pilot
        assert t["embargo"] == ast.literal_eval(card_kw["embargo"]) and t["cost_bps"] == study.COST[cost_key], pilot
        cost_text = ast.unparse(card_kw["cost_bps"])
        assert cost_text in ("COST[cost_key]", f"COST[{cost_key!r}]"), cost_text
        assert (t["domain"] is None and domain is None) or {k: tuple(v) for k, v in t["domain"].items()} == domain
        assert bench_text(fn) == parity.STUDY_BENCH[strategy], (fn, bench_text(fn))
    ref_card = cards["S_C3_crypto_trend_btcusd"]
    t2 = tables["C3-BTCUSD"]
    assert (t2["grid"], t2["embargo"], t2["cost_bps"]) == (ref_card["rules"]["grid"], ref_card["rules"]["embargo"],
                                                          ref_card["costs"]["cost_bps"])
    assert t2["reference_card_md5"] == _md5(ROOT / t2["reference_card"]) == "d0bb0882fb51dec361cf2ddb160186bb"
    dates = tuple(d.strftime("%Y-%m-%d") for d in runner.pd.date_range("2016-10-14", "2026-09-25", freq="D"))
    wf = validate.WalkForward(dates=dates, pnl=np.zeros(len(dates)), pnl_stress=np.zeros(len(dates)),
                              turnover=np.zeros(len(dates)), origins=(756,), chosen=(0,), is_sharpes=np.zeros((1, 5)),
                              n_configs=5)
    sc = validate.StrategyScore(**dict(N8_BASE, n_years=9, n_sessions=len(dates)))
    grid = runner.S.grid_from(**PILOT2_AXES)
    ref = dict(N8_BASE, n_years=11, n_sessions=len(dates), ci90=[0.72, 1.64], chosen_last={"hysteresis": 0.0})
    assert parity.reference_drift(sc, wf, grid, ref) == []
    assert parity.reference_drift(sc, wf, grid, dict(ref, n_sessions=len(dates) + 1)) == ["n_sessions"]
    assert parity.reference_drift(sc, wf, grid, dict(ref, sr_oos=1.19 + 2e-9)) == ["sr_oos"]
    assert parity.reference_drift(sc, wf, grid, dict(ref, ci90=[0.72, 1.64 - 2e-9], n_years=9)) == ["n_years", "ci90"]
    n, crypto = 900, runner.S.grid_from(**PILOT2_AXES)
    closes, days = synth_prices(5, n, 400.0, 60000.0), _days(n)
    stats, _sc, _wf = _reference_stats(closes, days, crypto, cost=10.0, embargo=1, n_trials=5,
                                       domain={"hysteresis": (0.0, 0.889)})
    with tempfile.TemporaryDirectory(prefix="qgnb_l129e_") as name:
        tmp = Path(name)
        card = tmp / "reference_card.json"
        md5 = _write_card_file(card, dict(stats, sr_oos=stats["sr_oos"] + 2e-9))
        code, rec, out = _rehearse(_crypto_table(tmp, n, reference_card=str(card), reference_card_md5=md5), tmp)
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert rec["gate"]["reference"]["drift"] == ["sr_oos"], rec["gate"]["reference"]
        assert "G-08: reference drift: sr_oos" in rec["withheld_reasons"], rec["withheld_reasons"]


def test_l1_30_card_labels_and_engine_text():
    """L1-30 (6.5; QUANT-6, QUANT-11, QUANT-R2-4): a written card carries the claim label, the engine text (STUB with
    the stub child, 6.5's text otherwise), parity_scope and stats.quantgen_score; every committed table's claim_label
    starts with "exploratory", "pre-specified on historical data" or "confirmatory"."""
    parity = _parity()
    for pilot, path in PILOT_TABLES.items():
        t = json.loads(path.read_text(encoding="utf-8-sig"))
        assert t["pilot"] == pilot and t["claim_label"].startswith(parity.CLAIM_PREFIXES), (pilot, t["claim_label"])
        assert "owner_confirmed" not in t and "host_fingerprint" not in t, pilot          # GOVERNANCE-R4-3
        assert parity.card_rules(t, stub_child=False)["engine"] == ENGINE_6_5
    with tempfile.TemporaryDirectory(prefix="qgnb_l130_") as name:
        tmp = Path(name)
        table = _card_table(tmp)
        t = json.loads(table.read_text(encoding="utf-8"))
        code, rec, out = _rehearse(table, tmp)
        assert (code, rec["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        card = json.loads(Path(rec["card"]["path"]).read_text(encoding="utf-8"))
        assert card["rules"] == parity.card_rules(t, stub_child=True) and card["rules"]["engine"] == "STUB", card["rules"]
        assert card["rules"]["claim_label"] == t["claim_label"] and card["rules"]["parity_scope"] == SCOPE_6_5
        assert card["hypothesis"] == f"{t['claim_label']}: {t['hypothesis']}" and card["kind"] == "strategy"
        q = card["stats"]["quantgen_score"]
        assert q["decision"] == card["decision"] and "lines" not in q and q["n_configs"] == 4, q
        assert card["stats"]["parity"]["hard_pass"] is True and card["trials"]["N_planned"] == 4, card["trials"]
        assert card["decision"] in ("PASS", "REVISE", "REJECT", "INSUFFICIENT_DATA")


def test_l1_31_walk_forward_raise_g03():
    """L1-31 (G-03; QA-R2-2): a 400-row synthetic table makes walk_forward raise after registration; the run is
    WITHHELD, exit 1, and the reason names the walk_forward exception."""
    with tempfile.TemporaryDirectory(prefix="qgnb_l131_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_small_table(tmp, n=400), tmp)
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        want = "G-03: walk_forward raised ValueError: need at least 546 sessions for one walk-forward step, got 399"
        assert rec["withheld_reasons"] == [want] and rec["gate"]["error"] == want, rec["withheld_reasons"]
        assert rec["parity"]["hard_pass"] is False and rec["parity"]["failed"] == [], rec["parity"]["failed"]


def test_l1_36_fingerprint_reads_no_data():
    """L1-36 (GOVERNANCE-R4-1), with the 3.3 guard's temp QUANTGEN_MACRO_DIR: --fingerprint on both committed pilot
    tables prints table_sha256, code_sha256 and host_fingerprint null with the reason and exits 0; on a copy whose
    prices_file names a missing file it still exits 0; an invalid table exits 2 after printing both digests."""
    runner = _runner()
    code_sha = runner.code_sha256(ROOT)
    with tempfile.TemporaryDirectory(prefix="qgnb_l136_") as name:
        tmp = Path(name)
        missing = tmp / "missing.json"
        t = json.loads(PILOT_TABLES["E1-SPY"].read_text(encoding="utf-8"))
        missing.write_text(json.dumps(dict(t, prices_file="docs/asset_expansion/cache/yf_NOT_THERE.csv"), indent=1),
                           encoding="utf-8", newline="\n")
        bad = tmp / "bad.json"
        bad.write_text(json.dumps(dict(t, cost_bps=40.0, pilot="E1-SPY", volume="5")), encoding="utf-8", newline="\n")
        for path in (*PILOT_TABLES.values(), missing, bad):
            table = json.loads(path.read_text(encoding="utf-8-sig"))
            code, out = _captured(lambda: runner.main(["--fingerprint", "--table", str(path)]))
            lines = out.splitlines()
            assert lines[:2] == [f"table_sha256 {runner.table_sha256(table)}", f"code_sha256 {code_sha}"], lines
            if path == bad:
                assert code == 2 and lines[-1] == "STATUS REFUSED exit=2 record=-" and "R-11" in out, out
                continue
            ledger = Path(os.environ["QUANTGEN_MACRO_DIR"]) / "ledgers" / f"{table['family_id']}.jsonl"
            want = f"host_fingerprint null (the family ledger {ledger} does not exist; R-15, O11)"
            assert code == 0 and lines[2] == want, lines
            assert lines[-1] == "STATUS OK exit=0 record=-", lines


def test_l2_07_synthetic_end_to_end_rehearsal():
    """L2-7 (8.4; QA-R3-11): synth_prices(7, 1500, 100, 150) and synth_rf(1500), the four columns of CARD_AXES at
    50 bp, embargo 21, through the real sandbox: every hard check passes, both scores are in the run record, and the
    run ends with a card whose decision is in validate.DECISIONS and whose engine text is 6.5's, or WITHHELD naming
    the differing predicates with their two values (G-02); never a new seed after the result."""
    from core.quant import validate
    layer2()
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l207_") as name:
        tmp = Path(name)
        table = write_rehearsal_table(tmp, prices=synth_prices(7, 1500, 100.0, 150.0), dates=_bdates(1500),
                                      rf=synth_rf(1500), axes=CARD_AXES)
        (code, out) = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                   out_dir=tmp / "out"))
        rec = json.loads(next((tmp / "out").glob("NB-*/run.json")).read_text(encoding="utf-8"))
        assert rec["stub_child"] is False and rec["parity"]["hard_pass"] is True, (rec["withheld_reasons"], out[-1500:])
        assert rec["gate"]["quantgen"]["stats"] and rec["gate"]["nautilus"]["stats"] and len(rec["children"]) == 8
        worst = min(x["P2"]["value"] for x in rec["parity"]["legs"])
        print(f"L2-7: {rec['status']}; quantgen {rec['gate']['quantgen']['decision']}, nautilus "
              f"{rec['gate']['nautilus']['decision']}; worst corr {worst}")
        if code == 0:
            card = json.loads(Path(rec["card"]["path"]).read_text(encoding="utf-8"))
            assert card["decision"] in validate.DECISIONS and card["rules"]["engine"] == ENGINE_6_5, card["rules"]
        else:
            assert code == 1 and rec["withheld_reasons"] and all(
                r.startswith("G-02: decision mismatch: ") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


def test_l2_11_n6_stress():
    """L2-11 (N6; QUANT-10, QA-R2-12): synth_prices(2026, 5500, 80, 650, planted every 252 bars from 252) with
    synth_rf(5500), pilot 1's 12 columns at 50 bp, 1x and 2x through the real sandbox: every hard check passes; the
    worst correlation and absolute Sharpe gap are printed next to the bars and map 03's (0.99999901, 0.0013)."""
    layer2()
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l211_") as name:
        tmp = Path(name)
        table = write_rehearsal_table(tmp, prices=synth_prices(2026, 5500, 80.0, 650.0, planted=range(252, 5292, 252)),
                                      dates=_bdates(5500), rf=synth_rf(5500), axes=PILOT1_AXES)
        (code, out) = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                   out_dir=tmp / "out"))
        rec = json.loads(next((tmp / "out").glob("NB-*/run.json")).read_text(encoding="utf-8"))
        legs = rec["parity"]["legs"]
        worst_corr, worst_dsr = min(x["P2"]["value"] for x in legs), max(x["P3"]["value"] for x in legs)
        print(f"N6: worst corr {worst_corr:.8f} (bar 0.9999, map 03 0.99999901); worst abs dSR {worst_dsr:.5f} "
              f"(bar 0.01, map 03 0.0013); {rec['status']}")
        assert len(legs) == 24 and rec["parity"]["hard_pass"] is True, (rec["parity"]["failed"], out[-1500:])
        assert code in (0, 1) and all(r.startswith("G-02") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


def test_l2_12_crypto_rehearsal_reference():
    """L2-12 (QUANT-R3-2, QUANT-R4-1): the L2-12 series (8.2), pilot 2's grid, embargo 1, domain, 10 bp, no cash
    rate, through the real sandbox, with a temp reference card built as the stored card was built: both scores in
    the record and gate.reference holding an empty drift list; a card, or WITHHELD naming its reason (G-02 only);
    the same reference with the whole-year n_years left in gives exactly ["n_years"]."""
    layer2()
    parity, runner = _parity(), _runner()
    n, grid = 1600, runner.S.grid_from(**PILOT2_AXES)
    closes, days = synth_prices(5, n, 400.0, 60000.0), _days(n)
    stats, sc, wf = _reference_stats(closes, days, grid, cost=10.0, embargo=1, n_trials=5,
                                     domain={"hysteresis": (0.0, 0.889)})
    whole = dict(stats, n_years=sc.n_years)                    # the whole-year count left in
    assert parity.reference_drift(sc, wf, grid, whole) == ["n_years"], (sc.n_years, stats["n_years"])
    with tempfile.TemporaryDirectory(prefix="qgnb_l212_") as name:
        tmp = Path(name)
        card = tmp / "reference_card.json"
        md5 = _write_card_file(card, stats)
        table = _crypto_table(tmp, n, reference_card=str(card), reference_card_md5=md5)
        (code, out) = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                   out_dir=tmp / "out"))
        rec = json.loads(next((tmp / "out").glob("NB-*/run.json")).read_text(encoding="utf-8"))
        assert rec["parity"]["hard_pass"] is True and rec["gate"]["reference"]["drift"] == [], (
            rec["withheld_reasons"], rec["gate"]["reference"], out[-1500:])
        gate = rec["gate"]
        assert gate["quantgen"]["stats"]["n_sessions"] == stats["n_sessions"] and gate["nautilus"]["stats"], gate
        print(f"L2-12: {rec['status']}; quantgen {gate['quantgen']['decision']}, nautilus {gate['nautilus']['decision']}; "
              f"reference n_years {gate['reference']['n_years_calendar']} calendar, "
              f"{gate['reference']['n_years_whole']} whole")
        assert code in (0, 1) and all(r.startswith("G-02") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


```

- [ ] **Step 3: Run the new tests and watch them fail (RED).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
K="-k test_l1_02 -k test_l1_05 -k test_l1_13 -k test_l1_14 -k test_l1_20b -k test_l1_21 -k test_l1_26b -k test_l1_28 -k test_l1_29 -k test_l1_30 -k test_l1_31 -k test_l1_36 -k test_l2_07 -k test_l2_11 -k test_l2_12"
python3 -B -m tests.nautilus_acceptance $K 2>&1 | grep -E '^(PASS|FAIL|NOT_RUN) |passed,'
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance -k test_l2_07 -k test_l2_11 -k test_l2_12 2>&1 | grep -E '^(PASS|FAIL|NOT_RUN) |passed,'
```
Expected (the first message line of each FAIL; `<repo>` is `/home/user/quantgen`; the runner's G-06 line is the tail of its output, which each assertion prints):
```
FAIL test_l1_02_parity_functions ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
FAIL test_l1_05_rerun_policy_r17 AssertionError: G-06: NotImplementedError: spec 5.4 and 5.5 are plan Task 5
FAIL test_l1_13_parity_failure_withholds_without_card AssertionError: G-06: NotImplementedError: spec 5.4 and 5.5 are plan Task 5
FAIL test_l1_14_gate_unchanged_and_g04 AssertionError: G-06: NotImplementedError: spec 5.4 and 5.5 are plan Task 5
FAIL test_l1_20b_p0b_benchmark_withholds ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
FAIL test_l1_21_select_matched_reproduces_wf_qg ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
FAIL test_l1_26b_ledger_moved_g05 AssertionError: G-06: NotImplementedError: spec 5.4 and 5.5 are plan Task 5
FAIL test_l1_28_card_and_record_bytes ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
FAIL test_l1_29_trial_counts_protocol_and_reference_drift ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
FAIL test_l1_30_card_labels_and_engine_text ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
FAIL test_l1_31_walk_forward_raise_g03 AssertionError: G-06: NotImplementedError: spec 5.4 and 5.5 are plan Task 5
FAIL test_l1_36_fingerprint_reads_no_data FileNotFoundError: [Errno 2] No such file or directory: '<repo>/docs/nautilus_bridge/registration/pilot1_E1_spy.json'
NOT_RUN test_l2_07_synthetic_end_to_end_rehearsal OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_11_n6_stress OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
NOT_RUN test_l2_12_crypto_rehearsal_reference OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)
0/15 passed, 12 failed, 3 not run
FAIL test_l2_07_synthetic_end_to_end_rehearsal TypeError: 'NoneType' object is not subscriptable
FAIL test_l2_11_n6_stress TypeError: 'NoneType' object is not subscriptable
FAIL test_l2_12_crypto_rehearsal_reference ImportError: cannot import name 'parity' from 'tools.nautilus' (<repo>/tools/nautilus/__init__.py)
0/3 passed, 3 failed, 0 not run
```
L2-7 and L2-11 reach step 16 through the real sandbox and end ERROR (G-06), so the record's `parity` is None. The second command takes about 50 s.

- [ ] **Step 4: Write `tools/nautilus/parity.py`** (spec 5.4 and 5.5; C11) with exactly this content (Write tool; UTF-8, LF; md5 `660377b31b61f22ed5d784ae609b2d08`). Every function is under 60 lines, so all are given in full. It imports `tools.nautilus.runner` at module level for `cost_text`, `child_params`, `PRICE_DECIMALS`, `Leg`, `RunContext` and `Outcome`; the runner imports `parity` only inside `parity_and_gate`, so loading either module first works. Steps 16 and 17 in `hand_off`, as numbered steps of spec 5.4 and 5.5:
  1. `check_parity`: per (column, cost level), in key order, P13 from the leg (Task 4's `Leg.invalid` and `Leg.rebuilt`); for a valid leg P1 (decision bars equal 5.2.5's, every mismatch exempt only below a 1e-9 QUANTGEN margin), P2 and P3 (`pair_checks`), P4 (fill bars without bar T-1 equal the bars with `abs(dw) > 0`), P5, P6, P7 (`p7`: `Decimal(commission) * 100 == cents(qty * px * cost * stress / 1e4)`, USD, and the manifest's echo of `cost_text(cost_bps)` and the runner's own stress), P8, P9, P10; then P0b (`p0b` on `ctx.study_pn.prices`). Hard failures become withheld reasons (G-01), warnings a list.
  2. `_walk_forwards`: `wf_qg = walk_forward(pnl_qg, dates[1:], turnover, pnl_stress, embargo)`; a raise is G-03. When every leg passed P13: `wf_nt = select_matched(...)`, P12 at 1x and 2x, then P11 from `walk_forward` on the Nautilus matrices (a raise there is G-03 too).
  3. `hard_pass` = no hard failure, no G-03 and P12 computed. Only then, `_score`: the benchmark from the rounded closes aligned with `wf_qg.dates` as the study does; trial counts on `ledger.snapshot(hash_after_registration)` (G-05 if no prefix has that hash); both scores through `ctx.score_fn` with `seed=11`, the table's domain as tuples and `n_trials = family_n_raw + U` (a raise is G-03).
  4. The record's `parity`, `provenance.p0b` and `gate` (`trial_counts`, `quantgen`, `nautilus`, `selection`, `error`), all made JSON-ready by `plain`; then the `after_step16` hook.
  5. When both scores exist: `agree` (G-02, with the differing predicates and both values), and, when the table names a reference card, its md5 again and `reference_drift` on the card's `stats` (G-08).
  6. G-04: `validate.GATE` against the snapshot, after every hand-off; a difference is ERROR, exit 4, before any card.
  7. When both scores exist: `assert_hash_at_run` (G-05).
  8. No reason left: `build_card` (6.5; `rules.engine` "STUB" with a stub child) and `write_card` (`open(path, "x", encoding="utf-8", newline="\n")`), and `record["card"] = {"path", "md5"}`.
  9. The `after_step17` hook; the Outcome (CARD_WRITTEN 0, or WITHHELD 1 with the reasons). Task 4's lifecycle writes the final record.
```python
"""Parity checks and the gate hand-off of the NautilusTrader bridge (spec 2026-10-26 sections 5.4 and 5.5).

Steps 16 and 17 of the runner (5.3.2), reached through runner.parity_and_gate: per column and cost level the checks
P1 to P10 and P13 of 5.4.1, the benchmark check P0b, QUANTGEN's walk-forward selection applied to both engines'
matrices (5.4.2) with P11 and P12, both matrices scored by the unchanged gate (5.5), and a card only when every hard
check passes for every column at both cost levels and both engines reach the same verdict. Nothing here edits the
gate, the ledger or the study; validate._col_sharpe is a private helper used read-only (5.4.2).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Sequence

import numpy as np

from core.quant import gate_ledger, validate
from core.quant import strategies as S
from tools.nautilus import runner as R

BARS = {"P1": 1e-9, "P2": 0.9999, "P3": 0.01, "P5": 1e-6, "P6": (0.99, 1.005), "P8": 0.005, "P9": 0.001,
        "P10": 1e-9}                                 # 5.4.1's corrected bars (P1: the exempt QUANTGEN margin)
OWNER_BARS = {"P1": 0.98, "P2": 0.99, "P3": 0.05}    # the owner's original bars, printed next to them
HARD = ("P0b", "P1", "P2", "P3", "P4", "P7", "P12", "P13")
WARNINGS = ("P5", "P6", "P8", "P9", "P10")
ENGINE_TEXT = ("per-column event-driven replication (nautilus_trader 1.231.0 BacktestEngine, same-bar close); "
               "walk-forward column switches are not executed in either engine")
SELECTION_TEXT = "QUANTGEN walk-forward selection (wf_qg.origins, wf_qg.chosen) applied to both engines' matrices"
PARITY_SCOPE = "parity validates the engine, not the data; P0 ties the inputs to the study's loaders"
PARITY_BARS_TEXT = "corrected, spec 2026-10-26 §5.4"
CLAIM_PREFIXES = ("exploratory", "pre-specified on historical data", "confirmatory")
STUDY_BENCH = {"trend_switch": "(pn.prices[1:] / pn.prices[:-1] - 1.0).mean(axis=1)",     # study :275
               "crypto_trend": "pn.prices[1:, 0] / pn.prices[:-1, 0] - 1.0"}             # study :334
CITATIONS = {"trend_switch": "trend", "crypto_trend": "crypto_trend"}                   # keys of study.CIT
REFERENCE_FLOATS = ("sr_oos", "ci90", "oos_is", "sr_stress", "years_positive", "plateau", "pbo", "prob_loss_oos")
PROTOCOL_KEYS = ("w_is", "w_oos", "min_is", "ci_level", "bootstrap_B", "block")


def plain(x):
    """JSON-ready values for the run record: numpy scalars and arrays, tuples and Decimals become Python values."""
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, np.ndarray):
        return [plain(v) for v in x.tolist()]
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, Decimal):
        return str(x)
    return x


# --------------------------------------------------------------------------- #
# 5.4.1: the checks
# --------------------------------------------------------------------------- #
def cents(x) -> int:
    """How Money rounds a commission (5.4.1; QA-R2-7): the value as a double, times 100, half away from zero."""
    return int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def corr(a, b) -> float:
    """Pearson correlation; a pair of constant series counts 1.0 when equal to 1e-12 and NaN otherwise (CONTRACT
    ISSUE 1: a column that never trades with rf = 0 gives R = pnl = 0 on every row)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.size < 2 or not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return float("nan")
    if float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return 1.0 if float(np.max(np.abs(a - b))) <= 1e-12 else float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def mdd(x) -> float:
    """Maximum drawdown of the compounded curve, as score_strategy computes it (P8)."""
    eq = np.cumprod(1.0 + np.asarray(x, dtype=float))
    return float(np.min(eq / np.maximum.accumulate(eq) - 1.0)) if eq.size else float("nan")


def pair_checks(a, b) -> dict:
    """P2 and P3 on one pair of series (also P12): correlation and the absolute Sharpe gap, both bars."""
    c, d = corr(a, b), abs(validate.sharpe(a) - validate.sharpe(b))
    return {"corr": c, "abs_dsr": d, "pass": bool(c >= BARS["P2"] and d <= BARS["P3"]),
            "owner_pass": bool(c >= OWNER_BARS["P2"] and d <= OWNER_BARS["P3"])}


def decision_bars(strategy: str, theta: dict, T: int) -> list[int]:
    """The bars on which a port decides (5.2.5): trend i >= L and (i - L) % s == 0; crypto every bar from warm-up."""
    if strategy == "trend_switch":
        return list(range(int(theta["lookback"]), T, int(theta["step"])))
    p = R.child_params({"strategy": strategy}, theta)
    return list(range(max(max(p["lookbacks"]), max(p["mas"])), T))


def qg_margins(strategy: str, theta: dict, closes: np.ndarray) -> np.ndarray:
    """P1's QUANTGEN margin per bar from QUANTGEN's own arrays (QA-19): sma abs(P - S._sma(P, L)) / P; tsmom
    abs(P[i] / P[i-L] - 1); crypto_trend the smallest abs(P - ref) / P over the votes, ref from S._sma. NaN where
    a bar has no margin."""
    P = np.asarray(closes, dtype=float)
    out = np.full(P.size, np.nan)
    if strategy == "trend_switch":
        L = int(theta["lookback"])
        if theta["rule"] == "sma":
            return np.abs(P - S._sma(P[:, None], L)[:, 0]) / P
        out[L:] = np.abs(P[L:] / P[:-L] - 1.0)
        return out
    p = R.child_params({"strategy": strategy}, theta)
    warm = max(max(p["lookbacks"]), max(p["mas"]))
    refs = [np.concatenate([np.full(k, np.nan), P[:-k]]) for k in p["lookbacks"]]
    refs += [S._sma(P[:, None], n)[:, 0] for n in p["mas"]]
    out[warm:] = np.min(np.abs(P[None, warm:] - np.vstack(refs)[:, warm:]), axis=0) / P[warm:]
    return out


def p1(decisions: list[dict], weights: np.ndarray, margins: np.ndarray, expected_bars: Sequence[int]) -> dict:
    """P1: the child's logged decision against QUANTGEN's W[t] > 0 on every decision bar; a mismatch whose QUANTGEN
    margin is below 1e-9 relative is exempt and listed; the logged bars must be the decision bars."""
    bars = [d["i"] for d in decisions]
    mism = [d["i"] for d in decisions if int(weights[d["i"]] > 0) != d["decision"]]
    exempt = [{"bar": i, "margin": float(margins[i])} for i in mism
              if np.isfinite(margins[i]) and margins[i] < BARS["P1"]]
    agree = (len(bars) - len(mism)) / len(bars) if bars else 1.0
    same_bars = bars == list(expected_bars)
    return {"value": agree, "decision_bars": len(bars), "same_bars": same_bars, "mismatches": mism,
            "exempt": exempt, "pass": same_bars and len(exempt) == len(mism), "owner_pass": agree >= OWNER_BARS["P1"]}


def p7(fills: list[dict], manifest: dict | None, *, cost_bps, stress: int) -> dict:
    """P7 (QUANT-5, QUANT-R2-3): each commission recomputed from the table's cost and the runner's own stress, as
    Money rounds it; USD only; the manifest echoes both values."""
    rate = Decimal(R.cost_text(cost_bps)) * Decimal(stress) / Decimal(10000)
    bad = [k for k, f in enumerate(fills) if f["commission"] * 100 != cents(f["last_qty"] * f["last_px"] * rate)
           or f["commission_ccy"] != "USD"]
    echo = (manifest or {}).get("input") or {}
    echoed = echo.get("cost_bps") == R.cost_text(cost_bps) and echo.get("stress") == str(stress)
    return {"bad_fills": bad, "echo": echoed, "pass": not bad and echoed}


def leg_checks(leg: "R.Leg", *, strategy: str, theta: dict, closes: np.ndarray, rf: np.ndarray, weights: np.ndarray,
               pnl: np.ndarray, turnover: np.ndarray, cost_bps) -> dict:
    """P1 to P10 and P13 for one child (5.4.1); weights is QUANTGEN's (T,) column, pnl the (T-1,) column at this
    leg's cost level, turnover QUANTGEN's (T-1,) abs(dw). An invalid leg gets only P13."""
    out = {"col": leg.col, "stress": leg.stress, "P13": {"pass": not leg.invalid and leg.rebuilt is not None,
                                                         "reasons": list(leg.invalid)}}
    if not out["P13"]["pass"]:
        return out
    T, rb, P = len(closes), leg.rebuilt, np.asarray(closes, dtype=float)
    c = float(R.cost_text(cost_bps)) * leg.stress / 1e4
    out["P1"] = p1(leg.decisions, weights, qg_margins(strategy, theta, P), decision_bars(strategy, theta, T))
    pair = pair_checks(rb.R, pnl)
    out["P2"] = {"value": pair["corr"], "pass": pair["corr"] >= BARS["P2"],
                 "owner_pass": pair["corr"] >= OWNER_BARS["P2"]}
    out["P3"] = {"value": pair["abs_dsr"], "pass": pair["abs_dsr"] <= BARS["P3"],
                 "owner_pass": pair["abs_dsr"] <= OWNER_BARS["P3"]}
    fill_bars, traded = sorted(set(rb.fill_bars) - {T - 1}), sorted(int(t) for t in np.flatnonzero(turnover > 0))
    out["P4"] = {"fill_bars": fill_bars, "dw_bars": traded, "pass": fill_bars == traded}
    gaps = [abs(float(f["last_px"]) / float(P[b]) - 1.0) for f, b in zip(leg.fills, rb.fill_bars)]
    out["P5"] = {"value": max(gaps, default=0.0), "pass": max(gaps, default=0.0) <= BARS["P5"]}
    tv, dw = float(np.sum(rb.TV)), float(np.sum(turnover))
    ratio = tv / dw if dw > 0 else (1.0 if tv == 0 else float("inf"))
    out["P6"] = {"value": ratio, "pass": BARS["P6"][0] <= ratio <= BARS["P6"][1]}
    out["P7"] = p7(leg.fills, leg.manifest, cost_bps=cost_bps, stress=leg.stress)
    out["P8"] = {"value": abs(mdd(rb.R) - mdd(pnl)), "pass": abs(mdd(rb.R) - mdd(pnl)) <= BARS["P8"]}
    te = float(np.std(rb.R - pnl, ddof=1) * math.sqrt(validate.TRADING_DAYS))
    out["P9"] = {"value": te, "pass": te <= BARS["P9"]}
    r_next = np.abs(P[1:] / P[:-1] - 1.0)
    bound = (c / (1.0 + c) + P[:-1] / rb.E_minus[:-1]) * (r_next + c) + np.asarray(rf, dtype=float)[:-1] + BARS["P10"]
    over = [int(t) for t in np.flatnonzero(np.abs(rb.R - pnl) > bound)]
    out["P10"] = {"max_gap": float(np.max(np.abs(rb.R - pnl))), "rows_over": over, "pass": not over}
    return out


def study_benchmark(strategy: str, study_prices: np.ndarray) -> np.ndarray:
    """The study's benchmark expression (STUDY_BENCH) on the study's prices rounded to 9 decimals (P0b)."""
    P = np.round(np.asarray(study_prices, dtype=float), R.PRICE_DECIMALS)
    if strategy == "trend_switch":
        return (P[1:] / P[:-1] - 1.0).mean(axis=1)
    return P[1:, 0] / P[:-1, 0] - 1.0


def p0b(strategy: str, closes: np.ndarray, study_prices: np.ndarray) -> dict:
    """P0b (QUANT-1): the benchmark from the runner's rounded closes equals the study's expression, byte for byte."""
    mine = np.asarray(closes, dtype=float)[1:] / np.asarray(closes, dtype=float)[:-1] - 1.0
    theirs = study_benchmark(strategy, study_prices)
    same = mine.shape == theirs.shape and mine.tobytes() == theirs.tobytes()
    first = None if same or mine.shape != theirs.shape else int(np.flatnonzero(mine != theirs)[0])
    return {"pass": same, "rows": int(mine.size), "study_rows": int(theirs.size), "first_difference": first}


# --------------------------------------------------------------------------- #
# 5.4.2: QUANTGEN's selection on both matrices; P11 and P12
# --------------------------------------------------------------------------- #
def select_matched(pnl_nt: np.ndarray, pnl_stress_nt: np.ndarray, turnover_nt: np.ndarray, dates: Sequence[str],
                   wf_qg: validate.WalkForward, *, embargo: int) -> validate.WalkForward:
    """wf_qg's origins and chosen columns applied to the Nautilus matrices, sliced as walk_forward slices
    (core/quant/validate.py:373-375); on QUANTGEN's own matrices it reproduces wf_qg bit for bit (L1-21)."""
    M, Ms, To = (np.asarray(x, dtype=float) for x in (pnl_nt, pnl_stress_nt, turnover_nt))
    T, G = M.shape
    w_is, w_oos = validate.GATE["w_is"], validate.GATE["w_oos"]
    out_d, out_p, out_s, out_t, is_sr = [], [], [], [], []
    for o, g in zip(wf_qg.origins, wf_qg.chosen):
        a, b = o + embargo, min(o + embargo + w_oos, T)
        out_d.extend(dates[a:b]); out_p.extend(M[a:b, g]); out_s.extend(Ms[a:b, g]); out_t.extend(To[a:b, g])
        is_sr.append(validate._col_sharpe(M[max(0, o - w_is):o]))
    return validate.WalkForward(dates=tuple(out_d), pnl=np.asarray(out_p), pnl_stress=np.asarray(out_s),
                                turnover=np.asarray(out_t), origins=wf_qg.origins, chosen=wf_qg.chosen,
                                is_sharpes=np.asarray(is_sr), n_configs=G, note=wf_qg.note)


def p11(wf_qg: validate.WalkForward, wf_own: validate.WalkForward) -> list[dict]:
    """P11 (diagnostic): per origin, Nautilus's own choice against QUANTGEN's, with QUANTGEN's in-sample Sharpe gap."""
    out = []
    for k, (o, g) in enumerate(zip(wf_qg.origins, wf_qg.chosen)):
        h = wf_own.chosen[k] if k < len(wf_own.chosen) else None
        gap = None if h is None else float(wf_qg.is_sharpes[k, g] - wf_qg.is_sharpes[k, h])
        out.append({"origin": o, "quantgen": g, "nautilus": h, "match": g == h, "is_sharpe_gap": gap})
    return out


def p12(wf_qg: validate.WalkForward, wf_nt: validate.WalkForward) -> dict:
    """P12: P2 and P3 on the selection-matched OOS series, at 1x and at 2x."""
    return {"1x": pair_checks(wf_nt.pnl, wf_qg.pnl), "2x": pair_checks(wf_nt.pnl_stress, wf_qg.pnl_stress)}


# --------------------------------------------------------------------------- #
# 5.5: trial counts, predicates, agreement, reference drift, card
# --------------------------------------------------------------------------- #
def study_config_ids(table: dict) -> list[str]:
    """config_id of every study_configs entry, from a row built as 6.4 builds one (QUANT-4)."""
    out = []
    for c in table["study_configs"]:
        params = json.loads(json.dumps(dict(c["params"], symbols=sorted(c["symbols"]), cost_bps=float(c["cost_bps"])),
                                       default=str))
        out.append(gate_ledger.config_id({"rule": table["rule"], "params": params, "timing_class": "COMPLIANT"}))
    return out


def trial_counts(table: dict, rows: Sequence[dict]) -> dict:
    """5.5 step 3 on the family ledger's rows after registration: n_trials = family_n_raw + U."""
    present = {r["config_id"] for r in rows}
    absent = sorted({i for i in study_config_ids(table) if i not in present})
    return {"len_grid": len(table["grid"]), "family_n_raw": len(rows),
            "market_n_raw": sum(r.get("market") == table["market"] for r in rows), "U": len(absent),
            "n_trials": len(rows) + len(absent), "study_configs_absent": absent}


def gate_predicates(score: validate.StrategyScore, gate: dict) -> dict[str, bool]:
    """Exactly the 18 predicates _decide_strategy reads (core/quant/validate.py:536-622), from the GATE snapshot."""
    g, s = gate, score
    meaningful, flat = s.n_configs >= g["pbo_min_configs"], s.prob_loss_oos <= g["prob_loss_max"]
    out = {"ci_pos": s.ci90[0] > 0, "dsr_ok": s.dsr >= g["dsr_min"], "dsr_finite": math.isfinite(s.dsr),
           "pbo_meaningful": meaningful, "flat": flat,
           "pbo_ok": (s.pbo <= g["pbo_max"] or flat) if meaningful else flat,
           "pbo_reject": meaningful and s.pbo > g["pbo_reject"] and not flat,
           "oos_is_ok": s.oos_is >= g["oos_is_min"], "stress_ok": s.sr_stress > 0,
           "years_ok": s.years_positive >= g["years_pos_min"],
           "plateau_ok": s.plateau >= g["plateau_min"] and not s.edge,
           "sample_ok": s.n_trades >= g["trades_min"], "floor_ok": s.n_trades >= g["trades_floor"],
           "n_years_ok": s.n_years >= g["oos_years_min"],
           "sessions_ok": s.n_sessions >= round(g["oos_years_min"] * validate.TRADING_DAYS),
           "mtr_ok": s.n_sessions >= validate.min_track_record(s.sr_oos, g["ci_level"]),
           "has_bench": math.isfinite(s.bench_p), "bench_ok": s.bench_p <= g["bench_p_max"]}
    return {k: bool(v) for k, v in out.items()}


def agree(sc_qg: validate.StrategyScore, sc_nt: validate.StrategyScore, gate: dict) -> tuple[bool, str | None]:
    """5.5 step 5 (G-02): a card needs a benchmark test in both scores, equal decisions and equal predicate dicts."""
    if not (math.isfinite(sc_qg.bench_p) and math.isfinite(sc_nt.bench_p)):
        return False, "benchmark test dropped"
    if sc_qg.decision != sc_nt.decision or gate_predicates(sc_qg, gate) != gate_predicates(sc_nt, gate):
        return False, "decision mismatch"
    return True, None


def _close(a, b, tol: float) -> bool:
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return (math.isnan(a) and math.isnan(b)) or abs(a - b) <= tol


def reference_drift(sc_qg: validate.StrategyScore, wf_qg: validate.WalkForward, grid: Sequence[dict],
                    ref: dict) -> list[str]:
    """G-08: every field where sc_qg fails to reproduce the stored card's stats `ref` (5.5 step 5): chosen_last,
    n_trades and n_sessions exactly; n_years by the calendar-years rule that wrote the card; the floats within 1e-9;
    bench_p within 1/2000. Never the lines, reason or revise_target text."""
    out = [] if wf_qg.chosen and grid[wf_qg.chosen[-1]] == ref.get("chosen_last") else ["chosen_last"]
    out += [k for k in ("n_trades", "n_sessions") if getattr(sc_qg, k) != ref.get(k)]
    out += [] if len({d[:4] for d in wf_qg.dates}) == ref.get("n_years") else ["n_years"]
    for k in REFERENCE_FLOATS:
        mine, theirs = getattr(sc_qg, k), ref.get(k)
        pairs = list(zip(mine, theirs)) if k == "ci90" and isinstance(theirs, (list, tuple)) and len(theirs) == 2 else [
            (mine, theirs)]
        out += [] if all(_close(a, b, 1e-9) for a, b in pairs) else [k]
    return out + ([] if _close(sc_qg.bench_p, ref.get("bench_p"), 1.0 / 2000) else ["bench_p"])


def card_rules(table: dict, *, stub_child: bool) -> dict:
    """6.5's rules; `engine` is STUB when a stub child ran (5.3.1)."""
    return {"family": table["strategy"], "grid": table["grid"], "cost_bps_per_side": float(table["cost_bps"]),
            "embargo": table["embargo"], "engine": "STUB" if stub_child else ENGINE_TEXT, "selection": SELECTION_TEXT,
            "claim_label": table["claim_label"], "parity_scope": PARITY_SCOPE, "parity_bars": PARITY_BARS_TEXT}


def parity_summary(parity: dict) -> dict:
    """The card's stats.parity: the worst values over every column and cost level, P12, the warnings."""
    legs = [x for x in parity["legs"] if x["P13"]["pass"]]
    return {"hard_pass": parity["hard_pass"], "worst_corr": min((x["P2"]["value"] for x in legs), default=None),
            "worst_abs_dsr": max((x["P3"]["value"] for x in legs), default=None),
            "max_daily_gap": max((x["P10"]["max_gap"] for x in legs), default=None), "P12": parity["P12"],
            "warnings": parity["warnings"], "bars": "corrected (spec 2026-10-26 §5.4); owner bars in the run record"}


def build_card(ctx: "R.RunContext", wf_nt: validate.WalkForward, sc_qg: validate.StrategyScore,
               sc_nt: validate.StrategyScore, counts: dict, ledger_hash_at_run: str) -> validate.ModelCard:
    """6.5's card from sc_nt, whose decision equals sc_qg's; both scores shown (QUANT-2)."""
    t, reg = ctx.table, ctx.record["registration"]
    stats = {k: v for k, v in asdict(sc_nt).items() if k not in ("lines", "regime")}
    stats.update(regime=sc_nt.regime, chosen_last=ctx.grid[wf_nt.chosen[-1]] if wf_nt.chosen else {},
                 bench_sharpe=sc_nt.bench_sr, walk_forward=wf_nt.note,
                 parity=plain(parity_summary(ctx.record["parity"])),
                 quantgen_score={k: v for k, v in asdict(sc_qg).items() if k != "lines"})
    trials = {"N_planned": counts["len_grid"], "N_total": counts["n_trials"], "family_id": t["family_id"],
              "family_n_raw": counts["family_n_raw"], "market_n_raw": counts["market_n_raw"], "U": counts["U"],
              "study_configs_absent": counts["study_configs_absent"],
              "config_ids": [r["config_id"] for r in reg["rows"]], "row_md5s": [r["row_md5"] for r in reg["rows"]],
              "ledger_hash_at_run": ledger_hash_at_run,
              "ledger": (f"{t['family_id']}.jsonl: {reg['n_raw_before']} rows before registration, "
                         f"{reg['n_raw_after']} after; U = {counts['U']} of {len(t['study_configs'])} study "
                         "configurations absent")}
    return validate.ModelCard(
        card_id=t["card_id"], kind="strategy", hypothesis=f"{t['claim_label']}: {t['hypothesis']}",
        rules=card_rules(t, stub_child=ctx.stub_child),
        universe={"symbols": [t["symbol"]], "venue": ctx.record["costs"]["classes"].get(t["symbol"])},
        data={"sessions": len(ctx.dates), "start": ctx.dates[0], "end": ctx.dates[-1], "source": t["prices_file"],
              "prices_md5": ctx.record["data"]["prices_md5"], "rf_md5": ctx.record["data"]["rf_md5"]},
        costs={"cost_bps": float(t["cost_bps"]), "stress_multiplier": ctx.gate_snapshot["cost_stress"]},
        protocol={k: ctx.gate_snapshot[k] for k in PROTOCOL_KEYS}, trials=trials, seed=11, stats=stats,
        tests={"dsr": sc_nt.dsr, "pbo": sc_nt.pbo, "ci90": sc_nt.ci90, "sr_stress": sc_nt.sr_stress},
        decision=sc_nt.decision, decision_reason=sc_nt.reason, revise_target=sc_nt.revise_target, lines=sc_nt.lines,
        citations=list(ctx.study.CIT[CITATIONS[t["strategy"]]]), results_file=ctx.bridge_run_id, results_md5="")


def write_card(path: Path, text: str) -> str:
    """5.5 step 8: open(path, "x"), so a card is never overwritten; LF only (OPS-12). Returns the md5 on disk."""
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Steps 16 and 17
# --------------------------------------------------------------------------- #
def _theta_text(theta: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in theta.items())


def check_parity(ctx: "R.RunContext") -> dict:
    """5.4.1 per column and cost level, and P0b; the hard failures as withheld reasons (G-01)."""
    t, failed, warnings, legs = ctx.table, [], [], []
    for (col, stress), leg in sorted(ctx.legs.items()):
        pnl = ctx.pnl_qg[:, col] if stress == 1 else ctx.pnl_stress_qg[:, col]
        x = leg_checks(leg, strategy=t["strategy"], theta=ctx.grid[col], closes=ctx.closes, rf=ctx.rf,
                       weights=ctx.weights[:, col], pnl=pnl, turnover=ctx.turnover_qg[:, col], cost_bps=t["cost_bps"])
        where = f"column {col} ({_theta_text(ctx.grid[col])}), {stress}x"
        if not x["P13"]["pass"]:                    # the leg's own ids first, so a C-06-only WITHHELD stays re-runnable
            failed += [f"{r} ({where})" for r in x["P13"]["reasons"]] or [f"P13: no rebuild ({where})"]
        failed += [f"{p}: {where}: {plain(x[p])}" for p in HARD if p in x and not x[p]["pass"]]
        warnings += [f"{p}: {where}: {plain(x[p])}" for p in WARNINGS if p in x and not x[p]["pass"]]
        legs.append(x)
    bench = p0b(t["strategy"], ctx.closes, ctx.study_pn.prices)
    failed += [] if bench["pass"] else [f"P0b: the benchmark differs from the study's expression: {bench}"]
    return {"bars": BARS, "owner_bars": OWNER_BARS, "legs": legs, "P0b": bench, "P11": None, "P12": None,
            "failed": failed, "warnings": warnings, "hard_pass": False}


def _walk_forwards(ctx: "R.RunContext", parity: dict):
    """wf_qg, then (when every leg is valid) wf_nt, P11 and P12; G-03 when walk_forward raises (QA-R2-2)."""
    dates, E = ctx.dates[1:], int(ctx.table["embargo"])
    try:
        wf_qg = validate.walk_forward(ctx.pnl_qg, dates, turnover=ctx.turnover_qg, pnl_stress=ctx.pnl_stress_qg,
                                      embargo=E)
    except Exception as exc:                        # noqa: BLE001 - G-03
        return None, None, f"G-03: walk_forward raised {type(exc).__name__}: {exc}"
    if not all(x["P13"]["pass"] for x in parity["legs"]):
        return wf_qg, None, None
    wf_nt = select_matched(ctx.pnl_nt, ctx.pnl_stress_nt, ctx.turnover_nt, dates, wf_qg, embargo=E)
    parity["P12"] = p12(wf_qg, wf_nt)
    parity["failed"] += [f"P12: {k}: {plain(v)}" for k, v in parity["P12"].items() if not v["pass"]]
    try:
        own = validate.walk_forward(ctx.pnl_nt, dates, turnover=ctx.turnover_nt, pnl_stress=ctx.pnl_stress_nt,
                                    embargo=E)
    except Exception as exc:                        # noqa: BLE001 - G-03 in parity (P11)
        return wf_qg, wf_nt, f"G-03: walk_forward (P11, Nautilus's own selection) raised {type(exc).__name__}: {exc}"
    parity["P11"] = p11(wf_qg, own)
    return wf_qg, wf_nt, None


def _hook(ctx: "R.RunContext", n: int) -> None:
    fn = ctx.hooks.get(f"after_step{n}")
    if fn is not None:
        fn(ctx)


def _score(ctx: "R.RunContext", wf_qg, wf_nt, gate: dict) -> dict:
    """5.5 steps 2 to 4 on the rows of the ledger as registration left it; G-03 (scoring), G-05 (no snapshot)."""
    bench = ctx.closes[1:] / ctx.closes[:-1] - 1.0
    by_date = dict(zip(ctx.dates[1:], bench))
    b = np.array([by_date[d] for d in wf_qg.dates])
    try:
        rows = ctx.ledger.snapshot(ctx.hash_after_registration)
    except gate_ledger.LedgerRefused as exc:
        return {"error": f"G-05: ledger moved after registration: {exc}"}
    counts = trial_counts(ctx.table, rows)
    domain = None if ctx.table["domain"] is None else {k: tuple(v) for k, v in ctx.table["domain"].items()}
    kw = {"grid": ctx.grid, "n_trials": counts["n_trials"], "bench_daily": b, "seed": 11, "domain": domain}
    try:
        sc_qg = ctx.score_fn(wf_qg, full_pnl=ctx.pnl_qg, **kw)
        sc_nt = ctx.score_fn(wf_nt, full_pnl=ctx.pnl_nt, **kw)
    except Exception as exc:                        # noqa: BLE001 - G-03 in scoring
        return {"error": f"G-03: score_strategy raised {type(exc).__name__}: {exc}", "trial_counts": counts}
    return {"trial_counts": counts, "sc_qg": sc_qg, "sc_nt": sc_nt,
            "quantgen": {"decision": sc_qg.decision, "reason": sc_qg.reason, "revise_target": sc_qg.revise_target,
                         "predicates": gate_predicates(sc_qg, gate),
                         "stats": {k: v for k, v in asdict(sc_qg).items() if k != "lines"}},
            "nautilus": {"decision": sc_nt.decision, "reason": sc_nt.reason, "revise_target": sc_nt.revise_target,
                         "predicates": gate_predicates(sc_nt, gate),
                         "stats": {k: v for k, v in asdict(sc_nt).items() if k != "lines"}}}


def _mismatch_text(gate_rec: dict) -> str:
    q, n = gate_rec["quantgen"], gate_rec["nautilus"]
    diff = [f"{k} {q['predicates'][k]}/{n['predicates'][k]}" for k in q["predicates"]
            if q["predicates"][k] != n["predicates"][k]]
    return f"quantgen {q['decision']}, nautilus {n['decision']}; predicates differ: {', '.join(diff) or 'none'}"


def _reference(ctx: "R.RunContext", sc_qg, wf_qg) -> dict:
    """G-08 whenever the table names a reference card: the drift list and both year counts."""
    t = ctx.table
    path = Path(t["reference_card"]) if os.path.isabs(t["reference_card"]) else ctx.repo_root / t["reference_card"]
    raw = path.read_bytes()
    drift = [] if hashlib.md5(raw).hexdigest() == t["reference_card_md5"] else ["reference_card_md5"]
    drift += reference_drift(sc_qg, wf_qg, ctx.grid, json.loads(raw.decode("utf-8"))["stats"])
    return {"card": t["reference_card"], "drift": drift, "n_years_calendar": len({d[:4] for d in wf_qg.dates}),
            "n_years_whole": sc_qg.n_years}


def hand_off(ctx: "R.RunContext") -> "R.Outcome":
    """Steps 16 and 17 (5.4, 5.5): parity, selection, both scores, agreement, reference, GATE, ledger, card."""
    rec, gate = ctx.record, ctx.gate_snapshot
    parity = rec["parity"] = check_parity(ctx)
    rec["provenance"]["p0b"] = parity["P0b"]
    wf_qg, wf_nt, wf_error = _walk_forwards(ctx, parity)
    parity["hard_pass"] = not parity["failed"] and wf_error is None and parity["P12"] is not None
    rec["gate"] = {"trial_counts": None, "quantgen": None, "nautilus": None, "agree": None, "reference": None,
                   "selection": None if wf_qg is None else {"origins": wf_qg.origins, "chosen": wf_qg.chosen,
                                                            "note": wf_qg.note}, "error": wf_error}
    reasons = list(parity["failed"]) + ([wf_error] if wf_error else [])
    scored = _score(ctx, wf_qg, wf_nt, gate) if parity["hard_pass"] else {}
    rec["gate"].update({k: v for k, v in scored.items() if k in ("trial_counts", "quantgen", "nautilus")})
    if "error" in scored:
        rec["gate"]["error"] = scored["error"]
        reasons.append(scored["error"])
    rec["parity"], rec["gate"] = plain(parity), plain(rec["gate"])
    _hook(ctx, 16)
    card_ok = False
    if "sc_qg" in scored:
        ok, why = agree(scored["sc_qg"], scored["sc_nt"], gate)
        rec["gate"]["agree"] = {"ok": ok, "reason": why}
        detail = f": {_mismatch_text(rec['gate'])}" if why == "decision mismatch" else ""
        reasons += [] if ok else [f"G-02: {why}{detail}"]
        if ctx.table["reference_card"] is not None:
            ref = rec["gate"]["reference"] = plain(_reference(ctx, scored["sc_qg"], wf_qg))
            reasons += [f"G-08: reference drift: {', '.join(ref['drift'])}"] if ref["drift"] else []
        card_ok = True
    if validate.GATE != gate:                       # G-04 (5.5 step 6), checked after every run
        diff = sorted(k for k in set(gate) | set(validate.GATE) if gate.get(k) != validate.GATE.get(k))
        rec["error"] = {"message": f"G-04: GATE differs from its snapshot after scoring: {diff}", "traceback": ""}
        _hook(ctx, 17)
        return R.Outcome("ERROR", 4, reasons + [rec["error"]["message"]])
    if card_ok:
        try:
            stored = gate_ledger.assert_hash_at_run(ctx.ledger, ctx.hash_after_registration)
        except gate_ledger.LedgerRefused as exc:
            stored, reasons = None, reasons + [f"G-05: ledger moved after registration: {exc}"]
    if card_ok and not reasons:
        card = build_card(ctx, wf_nt, scored["sc_qg"], scored["sc_nt"], scored["trial_counts"], stored)
        path = ctx.run_dir / f"{card.card_id}.json"
        rec["card"] = {"path": str(path), "md5": write_card(path, card.to_json())}
    _hook(ctx, 17)
    if rec["card"] is not None:
        return R.Outcome("CARD_WRITTEN", 0, [])
    return R.Outcome("WITHHELD", 1, reasons)
```

- [ ] **Step 5: Fill the seam.** In `tools/nautilus/runner.py`, Edit tool, `old_string`:
```python
def parity_and_gate(ctx: RunContext) -> Outcome:
    """Steps 16 and 17 (spec 5.4, 5.5): plan Task 5 replaces this body with parity.hand_off(ctx)."""
    raise NotImplementedError("spec 5.4 and 5.5 are plan Task 5")
```
`new_string` (C10's body):
```python
def parity_and_gate(ctx: RunContext) -> Outcome:
    """Steps 16 and 17 (spec 5.4, 5.5): tools/nautilus/parity.py."""
    from tools.nautilus import parity
    return parity.hand_off(ctx)
```

- [ ] **Step 6: Run the layer-1 tests: parity passes; the tests that need the pilot tables still fail.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
K="-k test_l1_02 -k test_l1_05 -k test_l1_13 -k test_l1_14 -k test_l1_20b -k test_l1_21 -k test_l1_26b -k test_l1_28 -k test_l1_29 -k test_l1_30 -k test_l1_31 -k test_l1_36"
python3 -B -m tests.nautilus_acceptance $K 2>&1 | grep -E '^(PASS|FAIL|NOT_RUN) |passed,'
```
Expected:
```
PASS test_l1_02_parity_functions
PASS test_l1_05_rerun_policy_r17
PASS test_l1_13_parity_failure_withholds_without_card
PASS test_l1_14_gate_unchanged_and_g04
PASS test_l1_20b_p0b_benchmark_withholds
PASS test_l1_21_select_matched_reproduces_wf_qg
PASS test_l1_26b_ledger_moved_g05
PASS test_l1_28_card_and_record_bytes
FAIL test_l1_29_trial_counts_protocol_and_reference_drift FileNotFoundError: [Errno 2] No such file or directory: '<repo>/docs/nautilus_bridge/registration/pilot1_E1_spy.json'
FAIL test_l1_30_card_labels_and_engine_text FileNotFoundError: [Errno 2] No such file or directory: '<repo>/docs/nautilus_bridge/registration/pilot1_E1_spy.json'
PASS test_l1_31_walk_forward_raise_g03
FAIL test_l1_36_fingerprint_reads_no_data FileNotFoundError: [Errno 2] No such file or directory: '<repo>/docs/nautilus_bridge/registration/pilot1_E1_spy.json'
9/12 passed, 3 failed, 0 not run
```
(L1-2 also prints its `N7 (i): P12 2x {...}; P3 at 2x per column, max 0.07667 (bar 0.01)` line.)

- [ ] **Step 7: Add `--fingerprint`, `--timing` and `--handoff-report` to the runner** (spec 5.3.1; GOVERNANCE-R4-1, OPS-8, OPS-R3-4, OPS-R4-3; C10). Three Edits in `tools/nautilus/runner.py`; with Task 4's file at md5 `01b576997547d17d8f318fb67f26bac6`, the result of Steps 5 and 7 has md5 `bffca79a6f40b5380b5e1a31a7fae2ad`.
  1. Docstring, `old_string`:
     ```
         python -B -m tools.nautilus.runner --check-env | --egress-record | --fixtures [--record-baseline | --write-goldens]
     ```
     `new_string` (that line, then one more):
     ```
         python -B -m tools.nautilus.runner --check-env | --egress-record | --fixtures [--record-baseline | --write-goldens]
         python -B -m tools.nautilus.runner --fingerprint --table <t> | --timing | --handoff-report
     ```
  2. Docstring, `old_string` `card) sit behind `parity_and_gate`, which plan Task 5 fills. Exit codes`, `new_string` `card) sit behind `parity_and_gate`, in tools/nautilus/parity.py. Exit codes`.
  3. Task 4's `main`, the whole function (its text below is `old_string`), is replaced by the block after it (`new_string`): the three modes, then the new `main`.

  Behaviour and exit codes:
  - `--fingerprint --table <t>` (`fingerprint_mode`): a table that is not JSON is R-11 (exit 2, nothing printed but the refusal). Otherwise it prints `table_sha256 <64 hex>` and `code_sha256 <64 hex>` first, then validates the table with Task 4's `_check_place(t, "of-record")`, `_check_fields(t, "fingerprint")` (both owner fields optional) and `_check_values(t, "of-record")`; a failure is R-11, exit 2 after the digests (**CONTRACT ISSUE 3**). It opens no `prices_file`, `rf_file` or `reference_card`. It prints `host_fingerprint <64 hex>` from `config.macro_dir() / "ledgers" / "<family>.jsonl"`, or `host_fingerprint null (<reason>; R-15, O11)` when that ledger is missing, empty or broken; then `owner_confirmed form: <name>, <YYYY-MM-DD>, table <16 hex>, code <16 hex>` and `STATUS OK exit=0 record=-`.
  - `--timing` (`timing_mode`): R-03 (exit 2) without a venv on its pins; else 12 sandbox runs of 5,600 bars (pilot 1's grid at 50 bp on spec 8.2's generator, seed 2026, 80 to 650, business days from 2001-01-02, 1x, the empty-ledger hash) through the exact launch contract, one JSON line `{"bars", "runs", "exit_codes", "seconds", "total_s", "timed_module", "import_us"}`, `import_us` being the cumulative `-X importtime` microseconds of `nautilus_trader.backtest.engine` in the first run; exit 0 when the 12 runs exit 0 and that line was found, else `STATUS REFUSED exit=2`. It writes nothing.
  - `--handoff-report` (`handoff_mode`): writes `docs/nautilus_bridge/handoff/<host tag>.json` through `write_record` (overwritten; git keeps the history), schema `nautilus-bridge-handoff/1`, parts in order `parent`, `git` (HEAD, `origin/claude/amazing-gauss-tdiguu`, `git status --porcelain=v1`), `venv`, `unshare`, `venv_mismatches`, `check_env`, `guard_selftest`, `stub_interpreter` (the suite's own `stub_python()`), `egress` (a fresh probe and the parent's control connect, in the egress record's shape), `firewall` (the three `powershell -NoProfile -NonInteractive -Command ... | Format-List` commands on Windows, `{"skipped": ...}` elsewhere), `fixtures` (F1, F2, N1: golden diff, exit code, census, tails), `census` (diff and C-08 judgement of the F1+F2 union against the Linux baseline), `timing`, `suite` (the FAIL rows and every `nautilus/*` row of `qa/acceptance_results.json`, with its mtime). Each part records `{"error", "traceback"}` instead of stopping. Exit 0 when the file is written (it prints `parts with an error: ...`), else `STATUS ERROR exit=4 record=-`. It writes into the repository, so Claude runs it only in a scratch clone (Step 17).
  - Any other combination of modes prints the usage and `STATUS REFUSED exit=2 record=-`; `--fingerprint` needs `--table` and neither `--rehearsal` nor `--of-record`.

  `old_string` (Task 4's `main`):
```python
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -B -m tools.nautilus.runner")
    ap.add_argument("--table")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--of-record", action="store_true")
    ap.add_argument("--ledger-dir")
    ap.add_argument("--out-dir")
    ap.add_argument("--child-cmd", help="rehearsal only: a JSON list replacing <venv python> ... <sandbox.py>")
    ap.add_argument("--rerun-of")
    ap.add_argument("--reason")
    ap.add_argument("--check-env", action="store_true")
    ap.add_argument("--egress-record", action="store_true")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--record-baseline", action="store_true")
    ap.add_argument("--write-goldens", action="store_true")
    a = ap.parse_args(argv)
    modes = [bool(a.table), a.check_env, a.egress_record, a.fixtures]
    if sum(modes) != 1 or (a.table and a.rehearsal == a.of_record) or (
            (a.record_baseline or a.write_goldens) and not a.fixtures) or (a.record_baseline and a.write_goldens):
        ap.print_usage()
        print("STATUS REFUSED exit=2 record=-")
        return 2
    if a.check_env:
        return check_env_mode()
    if a.egress_record:
        return egress_record_mode()
    if a.fixtures:
        return fixtures_mode(record=a.record_baseline, write=a.write_goldens)
    child_cmd = None
    if a.child_cmd is not None:
        try:
            child_cmd = json.loads(a.child_cmd)
        except ValueError:
            return _print_refusal(refuse("R-11", f"--child-cmd is not a JSON list: {a.child_cmd!r}"))
    return run(Path(a.table), mode="rehearsal" if a.rehearsal else "of-record",
               ledger_dir=Path(a.ledger_dir) if a.ledger_dir else None, out_dir=Path(a.out_dir) if a.out_dir else None,
               child_cmd=child_cmd, rerun_of=a.rerun_of, reason=a.reason)


```
  `new_string`:
```python
# --------------------------------------------------------------------------- #
# Modes added by plan Task 5: --fingerprint, --timing, --handoff-report (5.3.1)
# --------------------------------------------------------------------------- #
HANDOFF_SCHEMA = "nautilus-bridge-handoff/1"
BRANCH = "claude/amazing-gauss-tdiguu"
TIMING_BARS, TIMING_ENGINE = 5600, "nautilus_trader.backtest.engine"
TIMING_GRID = {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]}      # pilot 1's 12 columns
FIREWALL_COMMANDS = (                               # 5.3.1 (OPS-R4-3): Format-List output is English and ASCII
    "Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Format-List DisplayName, Enabled, Direction, "
    "Action, Profile",
    "Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Get-NetFirewallApplicationFilter | Format-List "
    "Program",
    "Get-NetFirewallProfile | Format-List Name, Enabled")


def fingerprint_mode(table_path: Path, repo_root: Path = REPO_ROOT) -> int:
    """--fingerprint (GOVERNANCE-R4-1): prints table_sha256 and code_sha256 once the table parses, then validates it
    against 6.6 with both owner fields optional (R-11, exit 2), opens no prices_file, rf_file or reference_card, and
    prints host_fingerprint, or null with the reason, from the production family ledger; exit 0."""
    try:
        t, _ = load_table(table_path)
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    tsha, code = table_sha256(t), code_sha256(repo_root)
    print(f"table_sha256 {tsha}")
    print(f"code_sha256 {code}")
    try:
        _check_place(t, "of-record", repo_root)
        _check_fields(t, "fingerprint")
        _check_values(t, "of-record")
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    import config
    ledger = gate_ledger.family_ledger(t["family_id"], config.macro_dir() / "ledgers")
    try:
        found = host_fingerprint(socket.gethostname(), ledger) if ledger.path.is_file() else None
        why = (f"the family ledger {ledger.path} does not exist" if not ledger.path.is_file()
               else f"the family ledger {ledger.path} holds no row")
    except gate_ledger.LedgerRefused as exc:
        found, why = None, f"the family ledger {ledger.path} does not verify: {exc}"
    print(f"host_fingerprint {found}" if found else f"host_fingerprint null ({why}; R-15, O11)")
    print(f"owner_confirmed form: <name>, <YYYY-MM-DD>, table {tsha[:16]}, code {code[:16]}")
    print("STATUS OK exit=0 record=-")
    return 0


def timing_inputs(n_bars: int = TIMING_BARS) -> list[tuple[bytes, bytes]]:
    """(input.json, bars.csv) of the 12 synthetic --timing runs: pilot 1's grid at 50 bp on 5,600 business days of
    spec 8.2's generator (seed 2026, 80 to 650), 9 decimals, the fixtures' empty-ledger hash (6.1)."""
    rng = np.random.default_rng(2026)
    lr = rng.normal(0.0, np.where(np.arange(n_bars) // 250 % 2 == 0, 0.008, 0.02))
    lr += (np.log(650.0 / 80.0) - lr.sum()) / n_bars
    closes = np.round(80.0 * np.exp(np.cumsum(lr)), PRICE_DECIMALS)
    dates = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2001-01-02", periods=n_bars)]
    bars = bars_bytes(closes, bar_timestamps(dates, "SPY"))
    table = {"strategy": "trend_switch", "instrument": "SPY", "capital_usd": "1000000", "cost_bps": 50.0,
             "fill_seed": 42, "size_precision": 0, "volume": "1000000000"}
    return [(input_bytes(table, theta, 1, bars, n_bars, gate_ledger.ledger_hash([])), bars)
            for theta in S.grid_from(**TIMING_GRID)]


def import_micros(stderr: str, module: str = TIMING_ENGINE) -> int | None:
    """The cumulative -X importtime figure, in microseconds, of `module` in a child's stderr; None if absent."""
    for line in stderr.splitlines():
        fields = line.split("|")
        if line.startswith("import time:") and len(fields) == 3 and fields[2].strip() == module:
            return int(fields[1])
    return None


def run_timing(python: Path, unshare: str | None) -> dict:
    """--timing's numbers: 12 sandbox runs of 5,600 bars through the exact launch contract, wall time each, and the
    BacktestEngine import time read from the first run's -X importtime lines."""
    seconds, codes, micros = [], [], None
    for raw, bars in timing_inputs():
        tmp = launch.make_tempdir()
        try:
            (tmp / "input.json").write_bytes(raw)
            (tmp / "bars.csv").write_bytes(bars)
            started = time.perf_counter()
            res = launch.run_child(launch.build_launch(["run", "--in", str(tmp)], tempdir=tmp, venv_python=python,
                                                       unshare=unshare))
            seconds.append(round(time.perf_counter() - started, 3))
            codes.append(res.returncode)
            micros = micros if micros is not None else import_micros(res.stderr)
        finally:
            launch.cleanup_tempdir(tmp)
    return {"bars": TIMING_BARS, "runs": len(seconds), "exit_codes": codes, "seconds": seconds,
            "total_s": round(sum(seconds), 3), "timed_module": TIMING_ENGINE, "import_us": micros}


def timing_mode() -> int:
    """--timing (5.3.1): prints run_timing's JSON; exit 0 when all 12 runs exit 0 and the import line was found."""
    try:
        python, _reads, unshare = _venv_for_mode()
    except BridgeRefusal as exc:
        return _print_refusal(exc)
    out = run_timing(python, unshare)
    print(json.dumps(out, sort_keys=True))
    ok = out["import_us"] is not None and out["exit_codes"] == [0] * len(out["exit_codes"]) and out["runs"] == 12
    print(f"STATUS {'OK' if ok else 'REFUSED'} exit={0 if ok else 2} record=-")
    return 0 if ok else 2


def _part(report: dict, name: str, fn: Callable[[], Any]) -> Any:
    """One part of the hand-off report: its value, or its own error, never a stop (5.3.1)."""
    try:
        report[name] = fn()
    except Exception as exc:                        # noqa: BLE001 - each part records its own error
        report[name] = {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-2000:]}
    return report[name]


def _git_lines(repo_root: Path, *args: str) -> dict:
    git = shutil.which("git")
    if git is None:
        return {"error": "git is not on PATH"}
    res = _git(git, repo_root, *args)
    return {"exit": res.returncode, "stdout": res.stdout.splitlines(), "stderr": res.stderr.strip()[-500:]}


def _powershell(command: str) -> dict:
    res = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], stdin=subprocess.DEVNULL,
                         capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    return {"command": command, "exit": res.returncode, "stdout": res.stdout.splitlines(), "stderr": res.stderr[-500:]}


def _fixture_part(python: Path, unshare: str | None, golden_dir: Path) -> dict:
    out = {}
    for name in GOLDEN_FIXTURES:
        run_ = run_fixture(name, python, unshare)
        path = Path(golden_dir) / f"{name}.json"
        want = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        res = run_["result"]
        out[name] = {"golden": run_["golden"], "diff": ["no golden file"] if want is None else compare_golden(
            run_["golden"], want), "returncode": res.returncode, "ntstatus": res.ntstatus, "census": res.census,
            "stdout_tail": res.stdout_tail, "stderr_tail": res.stderr_tail}
    return out


def _suite_rows(repo_root: Path) -> dict:
    path = Path(repo_root) / "qa" / "acceptance_results.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return {"path": str(path), "mtime_utc": mtime, "rows": [r for r in rows if r.get("status") == "FAIL"
                                                            or str(r.get("test", "")).startswith("nautilus/")]}


def _need(python: Path | None) -> Path:
    if python is None:
        raise RuntimeError("no venv python: see the venv part")
    return python


def _venv_part() -> dict:
    python = venv_python_from_key()
    return {"python": str(python), "reads": launch.read_venv(python)}


def _child_json(mode_args: list[str], python: Path, unshare: str | None) -> dict:
    res, out = launch_once(mode_args, python=python, child_cmd=None, unshare=unshare, timeout=launch.TIMEOUT_S)
    return {"returncode": res.returncode, "json": out, "stdout_tail": res.stdout_tail, "stderr_tail": res.stderr_tail}


def _stub_part() -> dict:
    from tests.nautilus_acceptance import stub_python          # the interpreter the suite's stub children use (8.1)
    return {"python": stub_python(), "sys_executable": sys.executable}


def _egress_part(python: Path, venv: dict, unshare: str | None) -> dict:
    probe = launch_once([], python=python, child_cmd=None, unshare=unshare, timeout=60, script=launch.EGRESS_PROBE)[1]
    return {"schema": EGRESS_SCHEMA, "platform_tag": launch.host_tag(), "venv_python": str(python),
            "base_python": venv["reads"]["pyvenv"]["executable"], "layer": LAYER, "probe": probe,
            "recorded_utc": _utc_now(), "control_connect": control_connect()}


def _firewall_part():
    if os.name != "nt":
        return {"skipped": f"not Windows ({launch.host_tag()})"}
    return [_powershell(c) for c in FIREWALL_COMMANDS]


def _census_part(fixtures: dict, golden_dir: Path) -> dict:
    union = sorted(set(fixtures["F1"]["census"]) | set(fixtures["F2"]["census"]))
    linux = load_baseline("manylinux_2_35_x86_64", golden_dir)
    return {"against": "modules_manylinux_2_35_x86_64.json", "union_F1_F2": len(union),
            "diff": census_diff(linux or [], union), "judgement": judge_census(union, linux or [])}


def handoff_report(repo_root: Path = REPO_ROOT, golden_dir: Path = launch.GOLDEN_DIR) -> dict:
    """The Step 7A hand-off report (5.3.1; OPS-8): every part in order, each recording its own error, never a stop."""
    rep: dict = {"schema": HANDOFF_SCHEMA, "host_tag": launch.host_tag(), "recorded_utc": _utc_now()}
    _part(rep, "parent", lambda: {"sys_executable": sys.executable, "sys_base_executable": sys._base_executable,
                                  "sys_version": sys.version, "nautilus_trader": launch.parent_nautilus(),
                                  "pyarrow": launch.parent_pyarrow()})
    _part(rep, "git", lambda: {"head": _git_lines(repo_root, "rev-parse", "HEAD"),
                               "origin_branch": _git_lines(repo_root, "rev-parse", f"origin/{BRANCH}"),
                               "status": _git_lines(repo_root, "status", "--porcelain=v1")})
    venv = _part(rep, "venv", _venv_part)
    python = Path(venv["python"]) if "python" in venv else None
    unshare = _part(rep, "unshare", launch.resolve_unshare)
    unshare = unshare if isinstance(unshare, str) else None
    _part(rep, "venv_mismatches", lambda: launch.venv_mismatches(venv["reads"]))
    _part(rep, "check_env", lambda: _child_json(["--check-env"], _need(python), unshare))
    _part(rep, "guard_selftest", lambda: _child_json(["--guard-selftest"], _need(python), unshare))
    _part(rep, "stub_interpreter", _stub_part)
    _part(rep, "egress", lambda: _egress_part(_need(python), venv, unshare))
    _part(rep, "firewall", _firewall_part)
    fixtures = _part(rep, "fixtures", lambda: _fixture_part(_need(python), unshare, golden_dir))
    _part(rep, "census", lambda: _census_part(fixtures, golden_dir))
    _part(rep, "timing", lambda: run_timing(_need(python), unshare))
    _part(rep, "suite", lambda: _suite_rows(repo_root))
    return rep


def handoff_mode(repo_root: Path = REPO_ROOT) -> int:
    """--handoff-report: writes docs/nautilus_bridge/handoff/<host tag>.json (overwritten; git keeps the history)."""
    from tools.nautilus import parity
    report = handoff_report(repo_root)
    path = Path(repo_root) / "docs" / "nautilus_bridge" / "handoff" / f"{launch.host_tag()}.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_record(path, parity.plain(report))
    except Exception as exc:                        # noqa: BLE001
        print(f"the hand-off report could not be written: {type(exc).__name__}: {exc}")
        print("STATUS ERROR exit=4 record=-")
        return 4
    failed = sorted(k for k, v in report.items() if isinstance(v, dict) and "error" in v)
    print(f"parts with an error: {', '.join(failed) or 'none'}")
    print(f"STATUS OK exit=0 record={path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -B -m tools.nautilus.runner")
    ap.add_argument("--table")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--of-record", action="store_true")
    ap.add_argument("--ledger-dir")
    ap.add_argument("--out-dir")
    ap.add_argument("--child-cmd", help="rehearsal only: a JSON list replacing <venv python> ... <sandbox.py>")
    ap.add_argument("--rerun-of")
    ap.add_argument("--reason")
    ap.add_argument("--check-env", action="store_true")
    ap.add_argument("--egress-record", action="store_true")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--record-baseline", action="store_true")
    ap.add_argument("--write-goldens", action="store_true")
    ap.add_argument("--fingerprint", action="store_true", help="with --table: table_sha256, code_sha256, host_fingerprint")
    ap.add_argument("--timing", action="store_true")
    ap.add_argument("--handoff-report", action="store_true")
    a = ap.parse_args(argv)
    run_mode = bool(a.table) and not a.fingerprint
    modes = [run_mode, a.fingerprint, a.check_env, a.egress_record, a.fixtures, a.timing, a.handoff_report]
    if sum(modes) != 1 or (run_mode and a.rehearsal == a.of_record) or (a.fingerprint and (
            not a.table or a.rehearsal or a.of_record)) or (
            (a.record_baseline or a.write_goldens) and not a.fixtures) or (a.record_baseline and a.write_goldens):
        ap.print_usage()
        print("STATUS REFUSED exit=2 record=-")
        return 2
    if a.fingerprint:
        return fingerprint_mode(Path(a.table))
    if a.timing:
        return timing_mode()
    if a.handoff_report:
        return handoff_mode()
    if a.check_env:
        return check_env_mode()
    if a.egress_record:
        return egress_record_mode()
    if a.fixtures:
        return fixtures_mode(record=a.record_baseline, write=a.write_goldens)
    child_cmd = None
    if a.child_cmd is not None:
        try:
            child_cmd = json.loads(a.child_cmd)
        except ValueError:
            return _print_refusal(refuse("R-11", f"--child-cmd is not a JSON list: {a.child_cmd!r}"))
    return run(Path(a.table), mode="rehearsal" if a.rehearsal else "of-record",
               ledger_dir=Path(a.ledger_dir) if a.ledger_dir else None, out_dir=Path(a.out_dir) if a.out_dir else None,
               child_cmd=child_cmd, rerun_of=a.rerun_of, reason=a.reason)


```

- [ ] **Step 8: Check the new modes' argument handling** (before the tables exist; no file is written).
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tools.nautilus.runner --fingerprint --table /nonexistent/table.json; echo "exit $?"
python3 -B -m tools.nautilus.runner --fingerprint > /dev/null 2>&1; echo "exit $?"
python3 -B -m tools.nautilus.runner --timing | tail -1; echo "exit ${PIPESTATUS[0]}"
```
Expected:
```
R-11: the table /nonexistent/table.json is not readable JSON: [Errno 2] No such file or directory: '/nonexistent/table.json'
remedy: fix the printed field; after a change, --fingerprint and a new owner_confirmed (7A.3); pilot 1 first (Step 8)
STATUS REFUSED exit=2 record=-
exit 2
exit 2
STATUS REFUSED exit=2 record=-
exit 2
```
(`--timing` without the key prints `R-03: QUANTGEN_NAUTILUS_PYTHON is not set` and its remedy first.)

- [ ] **Step 9: Write the two registration tables** (spec 6.6, 10.1, 10.2; O6, O14): exactly these bytes (Write tool; UTF-8, LF, ASCII). One key per line, one grid column or study configuration per line, keys in 6.6's order, no `owner_confirmed` and no `host_fingerprint` (GOVERNANCE-R4-3: Claude never writes them into a committed table; the owner adds them at 7A.3, as the runbook shows). Never re-save them with `sort_keys`: the `axes` keys keep the study's call order, which fixes the grid's column order. Their `table_sha256` is the same on every platform: `d76d2d7301ffe92ca5198404ba1cbe07fd11890489c227e20cced8c4c4e07347` (pilot 1) and `e2ec073c309cbfc75ff476c03dda96337c45b46ce3f18129df96fb4d74462aba` (pilot 2).

  `docs/nautilus_bridge/registration/pilot1_E1_spy.json` (md5 `90c07844c6247da0e80c731d50f6a6aa`):
```json
{
 "schema": "nautilus-bridge-table/1",
 "pilot": "E1-SPY",
 "family_id": "E1",
 "rule": "E1",
 "market": "US",
 "strategy": "trend_switch",
 "symbol": "SPY",
 "instrument": "SPY",
 "prices_file": "docs/asset_expansion/cache/yf_SPY.csv",
 "prices_md5": "d2164597d576e1b2fcadde063065811d",
 "start": "2004-12-01",
 "end": "2026-09-25",
 "rf_file": "docs/asset_expansion/cache/fred_DGS3MO.csv",
 "rf_md5": "661722143f24930a29b58c535d227c1b",
 "axes": {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]},
 "grid": [
  {"rule": "sma", "lookback": 126, "step": 21},
  {"rule": "sma", "lookback": 126, "step": 42},
  {"rule": "sma", "lookback": 210, "step": 21},
  {"rule": "sma", "lookback": 210, "step": 42},
  {"rule": "sma", "lookback": 252, "step": 21},
  {"rule": "sma", "lookback": 252, "step": 42},
  {"rule": "tsmom", "lookback": 126, "step": 21},
  {"rule": "tsmom", "lookback": 126, "step": 42},
  {"rule": "tsmom", "lookback": 210, "step": 21},
  {"rule": "tsmom", "lookback": 210, "step": 42},
  {"rule": "tsmom", "lookback": 252, "step": 21},
  {"rule": "tsmom", "lookback": 252, "step": 42}
 ],
 "cost_bps": 50.0,
 "embargo": 21,
 "capital_usd": "1000000",
 "price_precision": 9,
 "size_precision": 0,
 "volume": "1000000000",
 "fill_seed": 42,
 "domain": null,
 "hypothesis": "Faber SMA / MOP sign trend switch on SPY alone (long or cash) beats SPY buy-and-hold on Sharpe; the S_E1_trend_us grid on one sleeve",
 "claim_label": "pre-specified on historical data; the SPY series was used inside S_E1_trend_us with the same 12-setting grid; not confirmatory",
 "card_id": "NB_E1_trend_spy",
 "study_configs": [
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "sma", "lookback": 126, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "sma", "lookback": 126, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "sma", "lookback": 210, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "sma", "lookback": 210, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "sma", "lookback": 252, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "sma", "lookback": 252, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "tsmom", "lookback": 126, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "tsmom", "lookback": 126, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "tsmom", "lookback": 210, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "tsmom", "lookback": 210, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "tsmom", "lookback": 252, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_us.json", "symbols": ["GLD", "QQQ", "SPY", "TLT"], "cost_bps": 50.0, "params": {"rule": "tsmom", "lookback": 252, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "sma", "lookback": 126, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "sma", "lookback": 126, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "sma", "lookback": 210, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "sma", "lookback": 210, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "sma", "lookback": 252, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "sma", "lookback": 252, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "tsmom", "lookback": 126, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "tsmom", "lookback": 126, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "tsmom", "lookback": 210, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "tsmom", "lookback": 210, "step": 42}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "tsmom", "lookback": 252, "step": 21}},
  {"source": "docs/asset_expansion/cards/S_E1_trend_krx.json", "symbols": ["069500.KS", "132030.KS", "152380.KS", "229200.KS"], "cost_bps": 3.0, "params": {"rule": "tsmom", "lookback": 252, "step": 42}}
 ],
 "reference_card": null,
 "reference_card_md5": null
}
```
  `docs/nautilus_bridge/registration/pilot2_C3_btcusd.json` (md5 `e6189fdb5f43beed34b5909e65009af1`):
```json
{
 "schema": "nautilus-bridge-table/1",
 "pilot": "C3-BTCUSD",
 "family_id": "C3",
 "rule": "C3",
 "market": "CRYPTO",
 "strategy": "crypto_trend",
 "symbol": "BTC-USD",
 "instrument": "BTC/USD",
 "prices_file": "docs/asset_expansion/cache/yf_BTC-USD.csv",
 "prices_md5": "bc76f530ff24ab445367fe826150bc10",
 "start": "2014-09-17",
 "end": "2026-09-25",
 "rf_file": null,
 "rf_md5": null,
 "axes": {"hysteresis": [0.0, 0.222, 0.444, 0.667, 0.889]},
 "grid": [
  {"hysteresis": 0.0},
  {"hysteresis": 0.222},
  {"hysteresis": 0.444},
  {"hysteresis": 0.667},
  {"hysteresis": 0.889}
 ],
 "cost_bps": 10.0,
 "embargo": 1,
 "capital_usd": "1000000",
 "price_precision": 9,
 "size_precision": 8,
 "volume": "1000000000",
 "fill_seed": 42,
 "domain": {"hysteresis": [0.0, 0.889]},
 "hypothesis": "Short-horizon sign votes plus price/MA ratios (long/flat with hysteresis) beat buy-and-hold BTC on Sharpe with a 25 % smaller drawdown",
 "claim_label": "pre-specified on historical data, engine replication: stored card S_C3_crypto_trend_btcusd on the same file and configurations, grid revised on this file; not new evidence about the rule",
 "card_id": "NB_C3_crypto_trend_btcusd",
 "study_configs": [
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json trials.ledger, run 2/3", "symbols": ["BTC-USD"], "cost_bps": 10.0, "params": {"hysteresis": 0.05}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json trials.ledger, run 2/3", "symbols": ["BTC-USD"], "cost_bps": 10.0, "params": {"hysteresis": 0.1}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json trials.ledger, run 2/3", "symbols": ["BTC-USD"], "cost_bps": 10.0, "params": {"hysteresis": 0.2}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json trials.ledger, run 2/3", "symbols": ["BTC-USD"], "cost_bps": 10.0, "params": {"hysteresis": 0.3}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json trials.ledger, run 2/3", "symbols": ["BTC-USD"], "cost_bps": 10.0, "params": {"hysteresis": 0.4}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json trials.ledger, run 2/3", "symbols": ["BTC-USD"], "cost_bps": 10.0, "params": {"hysteresis": 0.5}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_krwbtc.json", "symbols": ["KRW-BTC"], "cost_bps": 10.0, "params": {"hysteresis": 0.0}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_krwbtc.json", "symbols": ["KRW-BTC"], "cost_bps": 10.0, "params": {"hysteresis": 0.222}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_krwbtc.json", "symbols": ["KRW-BTC"], "cost_bps": 10.0, "params": {"hysteresis": 0.444}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_krwbtc.json", "symbols": ["KRW-BTC"], "cost_bps": 10.0, "params": {"hysteresis": 0.667}},
  {"source": "docs/asset_expansion/cards/S_C3_crypto_trend_krwbtc.json", "symbols": ["KRW-BTC"], "cost_bps": 10.0, "params": {"hysteresis": 0.889}}
 ],
 "reference_card": "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json",
 "reference_card_md5": "d0bb0882fb51dec361cf2ddb160186bb"
}
```

- [ ] **Step 10: Run the Task 5 tests and the whole module (GREEN).**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
K="-k test_l1_02 -k test_l1_05 -k test_l1_13 -k test_l1_14 -k test_l1_20b -k test_l1_21 -k test_l1_26b -k test_l1_28 -k test_l1_29 -k test_l1_30 -k test_l1_31 -k test_l1_36 -k test_l2_07 -k test_l2_11 -k test_l2_12"
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance $K 2>&1 | grep -E '^(PASS|FAIL|NOT_RUN) |passed,|^(N6|N7|L2-7|L2-12)'
python3 -B -m tests.nautilus_acceptance 2>&1 | tail -1
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tests.nautilus_acceptance 2>&1 | tail -1
```
Expected: the first command prints 15 PASS lines, `15/15 passed, 0 failed, 0 not run` and these lines (measured on Linux; the numbers are printed, never asserted beyond the bars):
```
N7 (i): P12 2x {'corr': 0.9989206568469223, 'abs_dsr': 0.07763231205006826, 'pass': False, 'owner_pass': False}; P3 at 2x per column, max 0.07667 (bar 0.01)
L2-7: CARD_WRITTEN; quantgen INSUFFICIENT_DATA, nautilus INSUFFICIENT_DATA; worst corr 0.9999990510795416
N6: worst corr 0.99999962 (bar 0.9999, map 03 0.99999901); worst abs dSR 0.00058 (bar 0.01, map 03 0.0013); CARD_WRITTEN
L2-12: CARD_WRITTEN; quantgen INSUFFICIENT_DATA, nautilus INSUFFICIENT_DATA; reference n_years 3 calendar, 2 whole
```
The whole module gives `44/57 passed, 0 failed, 13 not run` (key unset, about 35 s) and `57/57 passed, 0 failed, 0 not run` (key set, about 3.5 min). Spec Step 7's done-when: L1-2, L1-5, L1-13, L1-14, L1-20's P0b case, L1-21, L1-26's G-05 case, L1-28 to L1-31, L1-36, L2-7, L2-11 and L2-12 pass; GATE is unchanged after every run (L1-14 and the G-04 check in every hand-off); N6 printed its worst corr and abs ΔSR next to the bars and map 03's. The L2-7, L2-11 and L2-12 lines go into the execution record (spec Step 10). If a later run of L2-7 ends WITHHELD, it must name the differing predicates and their two values (G-02), and nobody picks a new seed after the result (QA-R3-11).

- [ ] **Step 11: Write `docs/nautilus_bridge/RUNBOOK_windows.md`** (spec 9 Step 7A, 5.8's file table; OPS-R4-5) with exactly this content (Write tool; UTF-8, LF, ASCII; md5 `df14943a64529da46963e093aff30a76`), then check its PowerShell block against spec 7A.2.

````markdown
# NautilusTrader bridge: Step 7A on Windows

This runbook repeats Step 7A of `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` (section 9, revision 6)
in the order the spec gives it, with the PowerShell lines of 7A.2. Where this file and the spec differ, the spec
governs. No line below has run on Windows yet (UNVERIFIED until Step 7A).

**Pinned base interpreter: Python 3.13.14**, the python.org per-user amd64 installer `python-3.13.14-amd64.exe`,
installed into `%LOCALAPPDATA%\quantgen\py313` and used only for the bridge (spec 4.4, O9). It has the same 3.13
minor as the global interpreter, which is all the venv check reads (`python_minor` "3.13"). 3.13.14 is the patch the
owner's own interpreter reported when the studies of record were frozen (`grokteam/out/PREREG_book.json:126`), so a
Windows build of it exists. That python.org serves this file at the URL of the download line is UNVERIFIED: the
cloud container cannot reach python.org. If the download line fails, stop and ask Claude to pin another 3.13 patch
here; changing this file changes no digest (it is not in `code_sha256`, spec 6.6).

## Before Step 7A

- Step 1b is done: the GPT and Gemini rounds (or a substitute the owner recorded in Appendix B) and the owner's
  approval, recorded verbatim in the spec's Status block. Step 7A waits for it.
- Nothing else from QUANTGEN runs meanwhile: no suite run, no frozen-study readout, no pilot (spec 3.8).
- Power is plugged in. The runner and the suite's layer-2 tests also keep the machine awake (spec 5.3.5, 5.7).

## 7A.1 The sign-off sentence (the owner, then Claude)

1. The owner writes, in the chat, the sentence of the spec's Owner context:
   "I approve spec 2026-10-26 revision <n>, the T-RO-01 exemption of its section 5.6 and the merge of
   claude/amazing-gauss-tdiguu into main. Geon Koh, <date>."
   It releases the merge and the T-RO-01 exemption only.
2. Before recording it, Claude runs `git fetch origin` and `git merge-base --is-ancestor origin/main HEAD`; if main
   has moved, Claude merges `origin/main` into the branch first, so the sentence covers the merged branch.
3. Claude records the sentence verbatim in the spec's Status block, commits, and asks the owner for approval to push;
   on approval, Claude pushes. Every Claude commit leaves `qa/acceptance_results.json` byte-identical and says so.
   Any code change after the sentence needs a new sentence.

## 7A.2 The PowerShell block (the owner)

In the main clone, in a normal (not elevated) PowerShell window, run the lines below one at a time.

- **A throw in the five git lines** stops the block: send Claude the message, because the hand-off needs the branch.
- **A red error in any later line**: skip to the last line (`--handoff-report`), which always runs.
- **The fifth git line** (the fast-forward) brings Claude's fixes and a new sign-off into a re-entry.
- **Never** a whole-tree `checkout`, `reset`, `stash` or `clean` in the main clone, and never a worktree. `git switch`
  rewrites only files that differ; the branch leaves `docs/asset_expansion/cache/` alone.
- The installer is downloaded into `$q`, never into the clone. The dedicated interpreter's pip downloads the wheels
  before the firewall rule exists; the global pip never runs.

**Re-entry** (a second attempt after a failed one):
- If `$q\py313\python.exe` exists from an earlier attempt, the registry line lists that install: skip from the
  registry line to the rule check line.
- The rule check line shows whether the rule `QUANTGEN-nautilus-block-out` exists (empty output: no rule).
- While no rule exists, go on to the `pip download` line whatever `$q\wheels` holds: pip reuses every finished file
  whose hash it verifies. The rule exists only after an install has passed, because a red error at the install line
  skips to the last line.
- Once the rule exists, re-enter at the `venv` line: the rule blocks that interpreter's pip, and the offline
  `--require-hashes` install re-checks every hash. If `$q\wheels` is then missing, first run the elevated
  `Remove-NetFirewallRule` line alone, then re-enter at the download line.
- That a normal window can read the rule is UNVERIFIED; if it cannot, take the rule to exist once the elevated lines
  have run.
- The `venv`, install and runner lines are safe to repeat; the first firewall line removes any rule of that name
  before the second creates it; `--record-baseline` treats an existing baseline as spec 5.2.7 says.

```powershell
git fetch origin; if ($LASTEXITCODE) { throw "fetch" }
git merge-base --is-ancestor origin/main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "main has moved: ask Claude to merge origin/main into the branch first" }
git merge-base --is-ancestor main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "local main has unpushed commits: push them, then ask Claude to merge origin/main" }
git switch claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "switch" }
git merge --ff-only origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "fast-forward: ask Claude" }
$q = Join-Path $env:LOCALAPPDATA "quantgen"; New-Item -ItemType Directory -Force $q | Out-Null; $q   # note the printed path
$u = "Microsoft\Windows\CurrentVersion\Uninstall\*"; Get-ItemProperty "HKCU:\Software\$u", "HKLM:\Software\$u", "HKLM:\Software\WOW6432Node\$u" -ErrorAction SilentlyContinue | ? DisplayName -like "Python 3.13*"
#   first attempt: any row is a python.org 3.13 already registered; stop and report it (the Store package is not listed there)
$v = "3.13.14"; $inst = "$q\python-$v-amd64.exe"   # the patch this runbook pins
$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$v/python-$v-amd64.exe" -OutFile $inst
if ((Get-AuthenticodeSignature $inst).Status -ne "Valid") { throw "signature" }   # signer: Python Software Foundation (UNVERIFIED)
$p = Start-Process $inst -Wait -PassThru -ArgumentList "/quiet", "InstallAllUsers=0", "TargetDir=$q\py313", "PrependPath=0", "Include_launcher=0", "Shortcuts=0", "/log", "$q\py313-install.log"
if ($p.ExitCode -ne 0) { throw "installer exit $($p.ExitCode); see $q\py313-install.log" }
Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue   # rule check
#   empty output (always on a first attempt): no rule, go on to the next line; a rule listed: skip to the venv line,
#   unless $q\wheels is missing: then the elevated Remove-NetFirewallRule line alone first, then the next line
& "$q\py313\python.exe" -m pip download --require-hashes --only-binary=:all: --no-deps -r requirements-nautilus.txt -d "$q\wheels"; if ($LASTEXITCODE) { throw "download" }
& "$q\py313\python.exe" -m venv "$q\ntvenv"; if ($LASTEXITCODE) { throw "venv" }
& "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels" -r requirements-nautilus.txt; if ($LASTEXITCODE) { throw "install" }
# elevated PowerShell, same Windows account, the printed path written out in full; both lines, then close that window:
Remove-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "QUANTGEN-nautilus-block-out" -Direction Outbound -Action Block -Program "<printed path>\py313\python.exe" -Profile Any
# back in the normal window: add the .env line of 3.4 with the owner's path if absent, then:
python -B -m tools.nautilus.runner --check-env; if ($LASTEXITCODE) { throw "check-env" }
python -B -m tools.nautilus.runner --egress-record; if ($LASTEXITCODE) { throw "egress" }
python -B -m tools.nautilus.runner --fixtures --record-baseline; if ($LASTEXITCODE) { throw "fixtures" }
python -B -m tools.nautilus.runner --timing; if ($LASTEXITCODE) { throw "timing" }
python tests/run_all.py; if ($LASTEXITCODE) { throw "suite" }
python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot1_E1_spy.json; if ($LASTEXITCODE) { throw "fingerprint" }
python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot2_C3_btcusd.json; if ($LASTEXITCODE) { throw "fingerprint" }
python -B -m tools.nautilus.runner --handoff-report                      # always, last, whatever failed after the git lines
```

**The `.env` line** (spec 3.4): single quotes, forward slashes, no `%VAR%`. In double quotes python-dotenv would turn
the `\n` of `\ntvenv` into a newline. This line prints it with your path, ready to paste into `.env`:

```powershell
"QUANTGEN_NAUTILUS_PYTHON='" + ("$q\ntvenv\Scripts\python.exe" -replace '\\', '/') + "'"
```

**What each runner line must show:**
- `--check-env`: the pinned versions, the `win_amd64` identity `47d274d7...` with 764 entries, `HIGH_PRECISION`
  false and `FIXED_PRECISION` 9; `--guard-selftest`'s five outcomes; `STATUS OK exit=0`.
- `--egress-record`: writes `docs\nautilus_bridge\egress\win_amd64.json` with `probe.blocked` and
  `control_connect.ok` both true. A failed control connect prints its error first: this network does not reach
  1.1.1.1:443, so the record cannot prove the rule; run Step 7A on a network that does, or ask Claude.
- `--fixtures --record-baseline`: F1, F2 and N1 match their goldens, and `tools\nautilus\golden\modules_win_amd64.json`
  is written. A differing fixture writes nothing and exits 2; the hand-off stops and no pilot runs.
- `--timing`: the `BacktestEngine` import time and the wall time of 12 synthetic runs of 5,600 bars.
- `python tests/run_all.py`: 0 FAIL, the `nautilus` layer-2 tests PASS, `nautilus/test_l2_05b_input_linked_to_env_refused`
  the only `nautilus/*` NOT_RUN allowed (it needs Developer Mode for a symbolic link).
- `--fingerprint` (each table): `table_sha256`, `code_sha256`, then `host_fingerprint <64 hex>`; a
  `host_fingerprint null (...)` stops here (R-15, O11): the family ledger is missing or empty on this machine, and
  the owner rules how it starts.
- `--handoff-report`: writes `docs\nautilus_bridge\handoff\win_amd64.json`, each part with its own result or error.

## 7A.3 Commit what Step 7A produced (the owner)

1. Whatever happened after the five git lines, commit and push the hand-off report:
   ```powershell
   git add docs/nautilus_bridge/handoff/win_amd64.json
   git commit -m "nautilus: Step 7A hand-off report (win_amd64)"
   git push
   ```
   A null host fingerprint stops here (R-15, O11).
2. If every line passed, fill both tables, then commit them with the Step 7A outputs as one change group. In each of
   `docs/nautilus_bridge/registration/pilot1_E1_spy.json` and `pilot2_C3_btcusd.json`, the last line before the
   closing `}` is `"reference_card_md5": ...`. Add a comma at its end and these two lines after it, with the values
   that table's `--fingerprint` printed (the first 16 hex of each digest, as the `owner_confirmed form:` line shows):
   ```
    "owner_confirmed": "Geon Koh, <YYYY-MM-DD>, table <16 hex>, code <16 hex>",
    "host_fingerprint": "<64 hex>"
   ```
   `owner_confirmed` approves of-record runs of that table. Then:
   ```powershell
   git add tools/nautilus/golden/modules_win_amd64.json docs/nautilus_bridge/egress/win_amd64.json docs/nautilus_bridge/registration/pilot1_E1_spy.json docs/nautilus_bridge/registration/pilot2_C3_btcusd.json qa/acceptance_results.json
   git commit -m "nautilus: Step 7A records (win_amd64), owner fields of both pilot tables"
   git push
   ```
   Name each path; never `git add -A`. This commit also writes the branch's loose ref.

## 7A.4 Claude's review (the next session)

Claude reviews the hand-off report and the census diff; checks that the commit carrying the current sign-off sentence
is an ancestor of the 7A.3 commit and that `git diff --name-only <sentence commit> <7A.3 commit>` lists only 7A.3's
files (the census baseline, the egress record, the hand-off report, both tables and `qa/acceptance_results.json`);
recomputes `code_sha256` on Linux at the 7A.3 commit with `python3 -B -m tools.nautilus.runner --fingerprint --table
<table>` and compares it with both tables' `owner_confirmed`; and records the review in the spec's Appendix B.
Claude's review commit changes only the spec; a review that needs any other change means Step 7A has failed. No pilot
runs before that review.

## 7A.5 Before Step 8 (the owner)

```powershell
git pull --ff-only
```
The pilots anchor to that HEAD, and every pilot run record stores it.

## After Step 10: the merge (the owner)

A merge commit the owner makes himself, never a squash or a rebase, keeping the branch ref so every ledger anchor stays
reachable:
```powershell
git switch main
git pull --ff-only
git merge --no-ff claude/amazing-gauss-tdiguu
git push origin main
```
Until then the clone stays on the branch; readouts wait, or run from a separate clone, never during a pilot.

## Done when (spec Step 7A)

On Windows, `--check-env` reports the pinned versions, the `win_amd64` identity `47d274d7...` with 764 entries,
`HIGH_PRECISION` false and `FIXED_PRECISION` 9, and `--guard-selftest` behaves; the egress record shows
`probe.blocked` and `control_connect.ok` true; F1, F2 and N1 run through the exact launch contract and match their
goldens, or the hand-off stops and no pilot runs; the census diff obeys spec 5.2.7 and Claude has reviewed it; the
hand-off report holds the import time and the time of 12 synthetic runs of 5,600 bars; the full run shows 0 FAIL with
the `nautilus` layer-2 tests PASS, L2-5b the only `nautilus/*` NOT_RUN allowed, and the stub children start through
the interpreter spec 8.1's rule picks, recorded in the hand-off report; frozen_guard (a), (b) and (d) pass;
`repo_anchor()` returns `git:<the 7A.5 HEAD>`; `git status --porcelain` is empty.
````

```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B - <<'EOF'
from pathlib import Path
spec = Path("docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md").read_text(encoding="utf-8").splitlines()
start = spec.index('   git fetch origin; if ($LASTEXITCODE) { throw "fetch" }')
want = [line[3:] for line in spec[start:spec.index("   ```", start)]]
ps = next(l for l in Path("requirements-nautilus.txt").read_text(encoding="utf-8").splitlines()
          if l.startswith("#   PowerShell: "))[len("#   PowerShell: "):]
pin = '$v = "3.13.14"; $inst = "$q\\python-$v-amd64.exe"   # the patch this runbook pins'
expected = [pin if l.startswith('$v = "3.13.<x>"') else ps + '; if ($LASTEXITCODE) { throw "install" }'
            if l.startswith("# the PowerShell install line") else l for l in want]
raw = Path("docs/nautilus_bridge/RUNBOOK_windows.md").read_bytes()
block = raw.decode("utf-8").split("```powershell\n", 1)[1].split("\n```", 1)[0].splitlines()
assert b"\r" not in raw and raw.endswith(b"\n") and b"<x>" not in raw, "LF only, no <x>"
assert block == expected, [(a, b) for a, b in zip(block, expected) if a != b] or (len(block), len(expected))
print(f"runbook block = spec 7A.2 ({len(want)} lines), 3.13.14 pinned")
EOF
```
Expected: `runbook block = spec 7A.2 (31 lines), 3.13.14 pinned`.

- [ ] **Step 12: Run the Step 7A modes that write nothing, on Linux.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
T=$(mktemp -d); for t in pilot1_E1_spy pilot2_C3_btcusd; do QUANTGEN_MACRO_DIR=$T python3 -B -m tools.nautilus.runner --fingerprint --table docs/nautilus_bridge/registration/$t.json; echo "exit $?"; done; rmdir $T
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B -m tools.nautilus.runner --timing; echo "exit $?"
git status --short --untracked-files=all
```
Expected: for each table five lines, `table_sha256` as Step 9 states, `code_sha256 <64 hex>` (the same for both tables; it changes with every byte of the files 6.6 lists), `host_fingerprint null (the family ledger <T>/ledgers/E1.jsonl does not exist; R-15, O11)` (C3.jsonl for pilot 2), `owner_confirmed form: <name>, <YYYY-MM-DD>, table d76d2d7301ffe92c, code <16 hex>` (`e2ec073c309cbfc7` for pilot 2), `STATUS OK exit=0 record=-`, then `exit 0`. `--timing` prints one JSON line with `"runs": 12`, `"bars": 5600`, twelve exit codes 0 and an integer `import_us` (dry run: 15.2 s in all, import 0.86 s), then `STATUS OK exit=0 record=-` and `exit 0`. `git status` is unchanged by these commands (Step 15 lists it).

- [ ] **Step 13: Guard checks.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B -m tests.macro_m0_harness 2>&1 | tail -1
grep -nE 'submit_order|CANO|KIS_ACCOUNT|ACNT_PRDT_CD|import_module|find_spec|nautilus_pyo3' tools/nautilus/parity.py tools/nautilus/runner.py; echo "token lines: $?"
python3 -B -m tests.nautilus_acceptance -k test_l1_15 -k test_l1_32 2>&1 | tail -1
```
Expected: `14/14 passed, 0 failed, 0 not run` (the amended T-RO-01 scan reaches `tools/nautilus/parity.py` and the new runner code, with no hit); `token lines: 1` (grep found nothing); `2/2 passed, 0 failed, 0 not run` (L1-15's encoding rules over the new code; L1-32's guard over every test). test_08, test_09 and the flet guard read no file this task changes (notes above); the full run of Step 14 shows them PASS.

- [ ] **Step 14: Check the counts through the wrapper (Count Ledger, as deltas).** Nothing else from QUANTGEN runs meanwhile (spec 3.8). File names as the Plan rules' Result files list them (`$S/task5_full.json`, `$S/task5_nautilus.json`, `$S/task5_nautilus_key.json`).
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
md5sum qa/acceptance_results.json
python3 -B $S/run_baseline.py $S/task5_nautilus.json --suite nautilus 2>/dev/null | tail -1
QUANTGEN_NAUTILUS_PYTHON="$NTPY" python3 -B $S/run_baseline.py $S/task5_nautilus_key.json --suite nautilus 2>/dev/null | tail -1
md5sum qa/acceptance_results.json
```
Expected: `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json` twice; `44/57 passed, 0 failed, 13 not run; <S>/task5_nautilus.json` and `57/57 passed, 0 failed, 0 not run; <S>/task5_nautilus_key.json`. Then the full run, in the background (about 10 minutes; wait for it before anything else):
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -B $S/run_baseline.py $S/task5_full.json > $S/task5_full.log 2>&1; tail -1 $S/task5_full.log; grep '^FAIL' $S/task5_full.log; md5sum qa/acceptance_results.json
python3 -c "import json,sys; r=json.load(open(sys.argv[1], encoding='utf-8')); print(sum(x['test'].startswith('nautilus/') for x in r), sum(x['test'].startswith('macro/') for x in r))" $S/task5_full.json
```
Expected: `<P+46>/<N+59> passed, <F> failed, <R+13> not run; <S>/task5_full.json` with B of Task 1 Step 0; the FAIL lines are exactly B's FAIL set (at the reference baseline, `papers/test_debate_run_kills_process_tree` alone); the md5 unchanged; `57 <M+2>` (the `nautilus` rows and the `macro` rows, M from Task 1 Step 0, plus Task 2's two T-RO-01 tests). Then compare it row by row with the baseline (Plan rules, Result files): `python3 -B -c "import json, sys; a, b = ({r['test']: r['status'] for r in json.load(open(p, encoding='utf-8'))} for p in sys.argv[1:3]); added = sorted(set(b) - set(a)); print(len(added), {s: sum(b[k] == s for k in added) for s in ('PASS', 'FAIL', 'NOT_RUN')}, [k for k in added if not k.startswith('nautilus/')]); print('removed', sorted(set(a) - set(b))); print('changed', sorted((k, a[k], b[k]) for k in a.keys() & b.keys() if a[k] != b[k]))" "$S/t1_baseline.json" "$S/task5_full.json"` prints `59 {'PASS': 46, 'FAIL': 0, 'NOT_RUN': 13} ['macro/macro_m0_harness/test_t_ro_01_nautilus_allowlist_pinned', 'macro/macro_m0_harness/test_t_ro_01_nautilus_confined_to_the_sandbox']`, then `removed []` and `changed []`.

- [ ] **Step 15: Line ends and untouched files.**
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
python3 -c "
from pathlib import Path
for p in ('tools/nautilus/parity.py', 'tools/nautilus/runner.py', 'tests/nautilus_acceptance.py', 'docs/nautilus_bridge/RUNBOOK_windows.md', 'docs/nautilus_bridge/registration/pilot1_E1_spy.json', 'docs/nautilus_bridge/registration/pilot2_C3_btcusd.json'):
    b = Path(p).read_bytes(); assert b'\r' not in b and b.endswith(b'\n'), p
for p in ('tests/run_all.py', 'README.md'):
    b = Path(p).read_bytes(); assert b.count(b'\r\n') == b.count(b'\n'), p + ' must stay CRLF'
print('LF ok; CRLF ok')"
git diff --stat
md5sum tools/nautilus/parity.py tools/nautilus/runner.py tests/nautilus_acceptance.py docs/nautilus_bridge/registration/*.json docs/nautilus_bridge/RUNBOOK_windows.md
```
Expected: `LF ok; CRLF ok`; `git diff --stat` names only `tests/nautilus_acceptance.py` and `tools/nautilus/runner.py`; the md5s of Steps 2, 4, 7, 9 and 11 (the runner's and the test module's only when Task 4's files had the md5s those steps name).

- [ ] **Step 16: Commit.** `git status --short --untracked-files=all` shows exactly Step 1's lines plus these six, and no temp dir, card, run folder or hand-off file in the repository:
```
 M tests/nautilus_acceptance.py
 M tools/nautilus/runner.py
?? docs/nautilus_bridge/RUNBOOK_windows.md
?? docs/nautilus_bridge/registration/pilot1_E1_spy.json
?? docs/nautilus_bridge/registration/pilot2_C3_btcusd.json
?? tools/nautilus/parity.py
```
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
git add tools/nautilus/parity.py tools/nautilus/runner.py tests/nautilus_acceptance.py docs/nautilus_bridge/registration/pilot1_E1_spy.json docs/nautilus_bridge/registration/pilot2_C3_btcusd.json docs/nautilus_bridge/RUNBOOK_windows.md
git commit -F - <<'EOF'
nautilus: parity checks, gate hand-off, pilot tables and the Windows runbook (plan Task 5, spec Step 7)

tools/nautilus/parity.py: P0b to P13 per column and cost level, QUANTGEN's walk-forward selection on both
matrices (select_matched), both scores through the unchanged gate, agreement on the 18 gate predicates,
reference drift (G-08), the GATE and ledger checks (G-04, G-05) and a card written only on parity and agreement.
The runner fills its seam with parity.hand_off and gains --fingerprint, --timing and --handoff-report. The two
registration tables carry no owner field. RUNBOOK_windows.md repeats Step 7A with Python 3.13.14 pinned.
Synthetic data and temp ledgers only; qa/acceptance_results.json unchanged.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB
EOF
git log -1 --format='%h %s'; git status --short --untracked-files=all; md5sum qa/acceptance_results.json
```
Expected: the new commit on `claude/amazing-gauss-tdiguu`; `git status` shows only Step 1's lines; `16c9baa5a1777853521d485d5078e456  qa/acceptance_results.json`. No push.

- [ ] **Step 17: Run `--handoff-report` once in a scratch clone of the commit** (it writes into the repository; spec Step 7A runs it on Windows), then delete the clone.
```bash
S=/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad; NTPY=$S/ntvenv_hash/bin/python; cd /home/user/quantgen
rm -rf $S/clone_task5 && git clone -q /home/user/quantgen $S/clone_task5 && cd $S/clone_task5
T=$(mktemp -d); QUANTGEN_NAUTILUS_PYTHON="$NTPY" QUANTGEN_MACRO_DIR=$T python3 -B -m tools.nautilus.runner --handoff-report; echo "exit $?"
python3 -c "
import json; r = json.load(open('docs/nautilus_bridge/handoff/linux_x86_64.json', encoding='utf-8'))
print(r['schema'], [k for k, v in r.items() if isinstance(v, dict) and 'error' in v])
print({n: (f['returncode'], f['diff']) for n, f in r['fixtures'].items()}, r['census']['diff'], r['egress']['probe']['blocked'], r['timing']['runs'])"
cd /home/user/quantgen && rm -rf $S/clone_task5 $T && md5sum qa/acceptance_results.json
```
Expected: `parts with an error: none`, `STATUS OK exit=0 record=<S>/clone_task5/docs/nautilus_bridge/handoff/linux_x86_64.json`, `exit 0`; then `nautilus-bridge-handoff/1 []`, `{'F1': (0, []), 'F2': (0, []), 'N1': (10, [])} [] True 12`; the md5 unchanged. The `git` part names the scratch clone's HEAD (the new commit) and its `origin/claude/amazing-gauss-tdiguu` (the real clone's branch). The real clone's `docs/nautilus_bridge/` gains nothing.
