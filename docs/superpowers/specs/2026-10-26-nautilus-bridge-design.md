# NautilusTrader bridge: an independent backtest leg for QUANTGEN's gate (research only)

Date: 2026-10-26.

Status:
- **Revision 6 (Claude debate closed after round 5; GPT and Gemini pending, Step 1b).**
  - Five Claude personas (security, quant, QA, ops, governance) form one referee under D6
    (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:46`). Round 1, on Revision 1:
    1 REJECT, 4 ACCEPT WITH CHANGES. Round 2, on Revision 2: security AGREE, 4 ACCEPT WITH CHANGES. Round 3, on
    Revision 3: security, QA and governance AGREE, quant and ops ACCEPT WITH CHANGES. Round 4, on Revision 4:
    security, quant, QA and governance AGREE, ops ACCEPT WITH CHANGES; no blocker, 1 major (OPS-R4-1, the Step 7A
    re-entry) and 21 minor new issues, and the moderator's C-9. Round 5, targeted, on Revision 5: ops and security
    AGREE; no blocker, no major, 7 minor new issues. This revision applies every ruling of
    `docs/superpowers/specs/2026-10-26-nautilus-review/round5_rulings.md`; Appendix B maps each issue of all rounds.
  - Step 1a is done. Round 5 raised only minor issues, so under C-8 the moderator applied them in this revision and
    closed the Claude debate without a further round (`round5_rulings.md` §1). Final Claude verdicts: security AGREE
    (rounds 2 to 5), quant AGREE (round 4), QA AGREE (rounds 3 and 4), governance AGREE (rounds 3 and 4), ops AGREE
    (round 5). Steps 2 to 7 start now on the branch, on the section 2 defaults, with synthetic data and temp ledgers
    (GOVERNANCE-R2-1; section 9).
  - Step 1b is open. GPT (Codex CLI) and Gemini (`agy`) have reviewed no revision, because neither CLI exists in the
    cloud container: REVIEW_INCOMPLETE until both run on the owner's machine (Codex quota back 2026-10-30 14:40), or
    the owner records a substitute in Appendix B. Step 1b also needs the owner's approval with answers to O1 to O15
    (section 2). Step 7A waits for Step 1b.
  - Owner approval: **not given** (the whole spec). Owner sign-off sentence (Step 7A): **none recorded**.
  - Owner rulings received (verbatim, with channel and date):
    - **O1 approved**, 2026-10-27, Claude Code chat (cloud session), in Korean: "아뇨, Nautilus로 옮기는 걸 목표로
      하고 있습니다. 따라서 pyarrow를 포함한 새 의존성을 승인합니다." (English: "No, the goal is to move to
      Nautilus. Therefore I approve the new dependencies, including pyarrow.") This answers O1 only; the venv shape
      of O1's default (separate hash-pinned venv, global interpreter unchanged) stays the design. O2 to O15 remain
      open.
- Next: Step 2 (the plan) on the branch; in parallel, GPT and Gemini and the owner's rulings (Step 1b).

Inputs (QUANTGEN code at `6f7c610`, unchanged at HEAD `b7f991a`, which adds only this spec and the review folder;
branch `claude/amazing-gauss-tdiguu`): in `research_notes/QUANTGEN Nautilus bridge map/`, `00_synthesis.md` ("synth",
with the critic findings K1 to K15 in its section 10), `01_nautilus_backtest_api.md` (map01),
`02_quantgen_gate_ledger_lab.md` (map02), `03_pilot_and_parity.md` (map03, SPY before 2004-12-01 only) and
`04_governance_constraints.md` (map04); and the reports
`docs/superpowers/specs/2026-10-26-nautilus-review/round<k>_claude_<persona>.md` with their rulings.

Citation keys:
- `file:line` is a QUANTGEN path at `b7f991a`; code lines are unchanged since `f5742ab`.
- `nt:<path>:<line>` is `nautilus_trader` 1.231.0 in `scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
- `map0N §n`, `synth §n`, `K<n>` and referee ids (`SECURITY-1`, `QA-R2-4`, ...) point into the inputs.
- `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`;
  `scratch:rev2_probe/` to `scratch:rev4_probe/` hold the Revision-2 to Revision-4 probes, on synthetic data only.
- UNVERIFIED marks anything nobody in this session could check.

## Owner context

The owner replaced QuantConnect with NautilusTrader: "No, actually we're going to replace QuantConnect into Nautilus
trader". The owner then asked Claude to resume and "automatically start the remaining tasks". Both quotes come from
this session's chat; no repository file holds them, so a later reader cannot check them (UNVERIFIED).

The owner's words decide two things (GOVERNANCE-1): the engine is NautilusTrader, and Claude continues without stopping.
Everything else is a default taken on the owner's behalf, listed in section 2 with its cost if wrong. Branch work is
reversible: Claude builds on `claude/amazing-gauss-tdiguu` with synthetic data and temporary ledgers only, and deleting
the branch files undoes it. Two acts take effect only after the owner's sign-off sentence at Step 7A.1: the merge of the
branch into `main`, which is the owner's own act (GOVERNANCE-11), and the T-RO-01 exemption of section 5.6 outside the
branch. Claude records the sentence verbatim in the Status block. Its form: "I approve spec 2026-10-26 revision <n>, the
T-RO-01 exemption of its section 5.6 and the merge of claude/amazing-gauss-tdiguu into main. Geon Koh, <date>." Any code
change after the sentence needs a new one (GOVERNANCE-R4-2). Of-record runs, that is, rows in `~/.nextgen/macro/ledgers`
(map02 §3.1), are approved per table through `owner_confirmed`, written at Step 7A.3 after the Windows evidence exists
and quoting the table and code digests (6.6; GOVERNANCE-R2-2).

Branch work does not wait for Step 1b (GOVERNANCE-R2-1): once Step 1a closes, Steps 2 to 7 run on the section 2
defaults, and where the owner later rules otherwise, the affected branch work is redone or deleted before Step 7A.
Pilots wait for, in this order: (1) Step 1b, that is, the GPT and Gemini rounds, or a substitute the owner records in
Appendix B, and the owner's approval, recorded verbatim in the Status block with its channel and date in the form "I
approve spec 2026-10-26 revision <n> on the section 2 defaults, except: <O-number: ruling>. Geon Koh, <date>."
(GOVERNANCE-R3-5); (2) the sign-off sentence and the rest of Step 7A (section 9).

## 1. Purpose and scope

QUANTGEN decides strategy verdicts with its own gate, which reads a matrix of daily net returns from a vectorised
simulator (`core/quant/strategies.py:69-90, 379-389`; `core/quant/validate.py:345-381, 492-533`). The bridge adds a
second, independent engine for that matrix: a NautilusTrader `BacktestEngine`, event driven, with simulated fills,
whole shares and a cash account. It re-computes QUANTGEN's arithmetic in an independent engine, which catches bugs in
the simulator and the port; and it feeds the Nautilus matrices to QUANTGEN's unchanged gate, writing a card only when
parity holds and both engines reach the same verdict (5.5). A realism leg, such as a one-session fill delay, is
deferred to a later, separately specified step (ruling C-1): no latency code, no `timing_lag` rows, no realism fixture.

Scope:
- **Backtest only.** Three independent layers keep orders inside the process: the static scan (5.6), the strategy's
  refusal to start outside a BACKTEST kernel (5.2.5), and OS egress control on every child (4.4).
- **Research only.** QUANTGEN "goes no further than paper trading"
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:25-27`).
- **Single-instrument long/flat rules only.** `simulate` holds constant weights with no turnover charged, so a
  multi-sleeve book cannot reach parity on an execution engine (`core/quant/strategies.py:83-90`).
- **Nautilus live trading is outside QUANTGEN's scope.** `TradingNode`, live clients, adapters, network clients and API
  keys are TRADEGEN's domain (map04 §6); QUANTGEN never imports them, and TRADEGEN never registers trials in QUANTGEN's
  ledger (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:142`). A Nautilus `Strategy`
  runs unchanged under a `TradingNode` (`scratch:nt_docs/live.md:3`, doc version UNVERIFIED) and the venv holds every
  adapter; O3 says why that is not "something to switch on". Only cards and run records leave the bridge, read-only.
- Two pilots: SPY trend switch, 12 settings; BTC-USD crypto trend, 5 settings, only if pilot 1 passes parity.

## 2. Owner rulings

Each row is a ruling the owner must make. The default is what the owner is asked to accept; this revision builds on
it until the owner rules. O1 to O12 come from synth §3.1, O13 from K5, O14 and O15 from GOVERNANCE-8.

| # | Ruling asked | Default taken on the owner's behalf | What it costs if wrong |
|---|---|---|---|
| O1 | Dependency: may `nautilus_trader==1.231.0` and its closure, `pyarrow` included, be installed? "No new dependency without the owner" is written in five places, one of which bans `pyarrow` by name (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`; map04 §2.1). | Yes, in a separate hash-pinned venv outside the repo and OneDrive, created from a dedicated base interpreter (4.4), run only as a subprocess. The global interpreter, `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` stay unchanged. The `pyarrow` ban is read as binding the global interpreter and the app, not this venv. | Steps 3 to 9 stop; the branch files (5.8) are deleted. No global state changed. |
| O2 | T-RO-01 amendment (5.6): one allow-listed sandbox file; one AST-counted `self.submit_order` call; 7 added order verbs; a full dotted-name deny-list with a client-name pattern; a sandbox language restriction; both lists pinned by hash. It is the first exemption for a forbidden token or call in T-RO-01's history (GOVERNANCE-10). | As 5.6, placed in `tools/` (D2 of synth §1). It takes effect outside the branch only after the sign-off sentence. | Too wide: an order path could pass the scan; the egress layer (4.4) and the strategy guard (5.2.5) still bound it. Refused: the sandbox cannot live in a scanned tree, and the bridge stops. |
| O3 | Reading of DO-NOT-BUILD item 21, both halves: "Any order, cancel, withdrawal, deposit-address or transfer path, or a broker execution adapter, inside this programme" (`QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:6162`), with rule 01's "nothing to switch on" (same file :464, 500, 1257) (GOVERNANCE-2). | Facts: the venv holds `TradingNode` and every adapter (15 adapter packages, map01 §9.1; 35 compiled submodules load with `BacktestEngine`, O13); a Nautilus strategy runs unchanged under `TradingNode`. The bridge never constructs a node, client or adapter. The strategy refuses to start unless its kernel is BACKTEST (C-2, 5.2.5). Every child runs without network (4.4), so a switch-on fails. The parent passes no `.env` key; the sandbox opens only its temp dir (5.2.8); a key read anyway is useless without egress (SECURITY-3). Default reading: no broker adapter inside the programme, and nothing to switch on. | The programme would host a broker adapter against the council's rule. Remedy: delete the venv and the branch files. No order can leave: no credentials, no route out. |
| O4 | Version: 1.231.0 or a 2.0 release candidate. | 1.231.0, hash-pinned; the wheels kept locally. A v2 migration is a later, separate task. | 1.231.0 is the last 1.x release; the backport window after the v2 cutover is undated (map01 §10.4). A migration re-runs F1, F2 and the grid. |
| O5 | Parity bars: the corrected bars of 5.4, or the original 98% / 0.99 / 0.05. | Corrected bars, with the commission check P7 hard (QUANT-5); the original bars printed next to them. | Too strict: a false WITHHELD on engine noise; measured margins are 100x on correlation and 7.7x on Sharpe (5.4.3). Kept original: a forgotten 2x cost passes all three original bars (synth §7.3). |
| O6 | Pilot-1 registration table (10.1). | As 10.1. The start is 2004-12-01: map 03 already computed all 12 settings on 1995 to 2004, so an earlier start would make pilot 1 exploratory (GOVERNANCE-5). | Ledger rows are immutable (`core/quant/gate_ledger.py:337-355`); a wrong key field leaves 12 permanent extra trials in E1. |
| O7 | Realism leg (fill delay): in scope? | **Deferred** by ruling C-1: no latency code, no `timing_lag` rows, no realism fixture. | If the owner wants a realism number, a later spec adds it with its own registration. Nothing to undo. |
| O8 | Referees: wait for GPT (Codex quota resets 2026-10-30 14:40; `docs/superpowers/plans/2026-10-23-execution-record.md:158`) and Gemini (`agy`; `tools/debate.py:46-47`), or record a substitute. | Wait (Step 1b). Claude's rounds 1 to 5 are ruled and applied, and Step 1a is done: round 5 raised only minor issues, so the moderator closed the Claude debate (`round5_rulings.md` §1). Neither CLI exists in the cloud container, so both run on the owner's machine; no substitute is recorded. | Step 1b ends about four days later; Steps 2 to 7 go ahead meanwhile on the branch. A missing referee is REVIEW_INCOMPLETE, never "no objections" (map04 R24). |
| O9 | Windows environment and its location. | Base interpreter `%LOCALAPPDATA%\quantgen\py313` (python.org per-user install), venv `%LOCALAPPDATA%\quantgen\ntvenv`, firewall rule `QUANTGEN-nautilus-block-out` (4.4), the `.env` line of 3.4, timings at Step 7A. The Windows closure unpacks to about 506 MB, 0.5 to 0.6 GB with bytecode (OPS-14). The owner's global interpreter is the Microsoft Store Python 3.13 (`docs/asset_expansion/study.log:27, 29`; `grokteam/prereg.py:87-88`; UNVERIFIED until Step 7A prints `sys.executable`); it never creates the venv or runs pip for the bridge, and R-03 refuses a venv built on it (6.7; OPS-R2-2). | Owner time. A venv inside OneDrive would sync about 0.6 GB. |
| O10 | Where pilots and the suite of record run. | The owner's Windows machine, against the production ledger; of-record mode is tied to it by the host fingerprint and the egress record (5.3.2). Linux rehearses on synthetic data only. | Exporting `E1.jsonl` and copying back the extended chain risks a fork. |
| O11 | Trial count; row counts of `E1.jsonl` and `C3.jsonl` (UNVERIFIED today). | `n_trials = family N_raw after registration + U`; U counts the study's documented configurations (`study_configs`, 6.6) whose `config_id` is absent from the family ledger (QUANT-4). Four counts printed. Of-record mode refuses a missing, empty or broken family ledger (R-15). | Over-counting lowers the DSR, the conservative direction. If `E1.jsonl` is missing or empty on the owner's machine, pilot 1 waits for the owner's ruling on how that ledger starts. |
| O12 | How a WITHHELD result appears in Strategy Lab. | Deferred. Outputs live in `docs/nautilus_bridge/runs/<bridge_run_id>/`, which the Lab does not read (`ui/strategy_lab_page.py:31`). | The owner reads results from files. No card ever says WITHHELD (5.5). |
| O13 | May the child tolerate what the kernel and the Rust core load in every backtest? `from nautilus_trader.backtest.engine import BacktestEngine` loads 7 `nautilus_trader.live.*` modules (`nt:system/kernel.py:75-77`) and `nautilus_trader.core.nautilus_pyo3` with 35 compiled submodules, among them `binance`, `bybit`, `okx`, `polymarket`, `interactive_brokers`, `network`, `live` and `sandbox`. | Tolerate the import census of a per-platform golden baseline recorded from F1 and F2 (5.2.7). The census is drift detection only: it cannot see use of a module already loaded (SECURITY-2); the egress layer (4.4) bounds use. A run whose Nautilus or third-party import set differs from the baseline's, in either direction, or that imports any `nautilus_trader.adapters` or `.network` module, is invalid (QA-R3-12). | Ruled unacceptable: no 1.231.0 backtest runs, and the bridge stops. Tolerated wrongly: a loaded Rust client could try a socket; the egress layer makes it fail, and Step 7A's probe shows that on Windows. |
| O14 | Pilot-2 registration table (10.2). It writes 5 permanent rows into C3, which also holds paper_live's trend rows (`paper_live/engine.py:64-69`). | As 10.2. | As O6, in C3. |
| O15 | A configured venv off its pins (versions, Python minor, wheel identity): FAIL or NotRun in the suite? | FAIL (synth §4 default 5). A blank key stays NotRun. | A FAIL in the suite of record until the venv is fixed. NotRun would hide an engine change. |

## 3. Constraints that bind every step

### 3.1 Frozen pins

- The test interpreter keeps numpy 2.3.5, scipy 1.18.0 and pandas 2.3.3 while a readout is pending
  (`tests/frozen_guard.py:85-91`); there is no warn-only branch. The suite never runs under the venv interpreter, which
  has no scipy, so clause (d) would FAIL (`:91`). The venv pins the same numpy and pandas, so both share numerics.
- Nautilus is never installed into the global interpreter; an eager upgrade would move numpy to 2.5.4 and pandas to
  3.1.0 (map04 §5.2). A suite test fails while `nautilus_trader` is importable there; `pyarrow` there is reported,
  not failed, because other owner packages may bring it (OPS-5, GOVERNANCE-7; L1-22).

### 3.2 Order path

- Exactly one file places simulated orders: `tools/nautilus/sandbox.py`, through one `self.submit_order` call in one
  method of a `Strategy` subclass (`nt:trading/strategy.pyx:805`; 5.6 rule A); the strategy refuses to start unless
  its kernel is BACKTEST (5.2.5). Orders fill against Nautilus's simulated exchange, as QUANTGEN's paper fills pass
  through `OrderBook.fill` (`core/engine/orders.py:90, 169, 253-257`).
- The sandbox never calls `submit_order_list` (`nt:trading/strategy.pyx:899`), `modify_order` (:1011), `cancel_order`
  (:1089), `cancel_orders` (:1134), `cancel_all_orders` (:1215), `close_position` (:1351), `close_all_positions`
  (:1418) or `market_exit` (:1750). No QUANTGEN file imports `nautilus_trader.live`, `.adapters`, `.network`,
  `.core.nautilus_pyo3` or `.backtest.node`.

### 3.3 Hermeticity

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

### 3.4 No-new-dependency shape

One new dependency file, `requirements-nautilus.txt`, installs into the venv only; `requirements.txt`,
`requirements-dev.txt` and `pyproject.toml` stay byte-identical, and QUANTGEN code never imports `nautilus_trader`.
`.env.example` gains a heading and one line with single quotes, forward slashes and no `%VAR%` (OPS-4):
`QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'`. In double quotes,
python-dotenv would turn the `\n` of `\ntvenv` into a newline.

### 3.5 Determinism

One child process per (column, cost level), because `FillModel` reseeds Python's global `random`
(`nt:backtest/models/fill.pyx:75, 77`); `FillModel(random_seed=42)` always. No UUID, run id or wall-clock value enters
a result hash; fills are recorded without their UUID (5.2.6). The sandbox never iterates a set or dict of strings in an
order-dependent output (`-I` ignores `PYTHONHASHSEED`). Two processes on the same input give the same fills SHA-256
(map01 §6; the QA referee's F1 and F2 probe).

### 3.6 Windows standard precision (K1)

The win_amd64 wheel is standard precision (`DEF HIGH_PRECISION = False` in its `core/rust/model.pxd:6`,
`scratch:critic_win/`); the Linux wheel is high precision (`nt:core/rust/model.pxd:6`). In standard mode
`FIXED_PRECISION` is 9 (`:18-20`), `QUANTITY_MAX` 18,446,744,073 (`:93-94`), `PRICE_MAX` and `MONEY_MAX` 9,223,372,036
(`:61-62, 77-78`), and `Quantity.__init__` raises above `QUANTITY_MAX` (`nt:model/objects.pyx:137-140`). The bridge
uses volume 1e9 and 9 price decimals, the standard-mode limit; the sandbox refuses more (exit 20). Every margin and
golden value was measured in high precision; cross-precision equality is UNVERIFIED until Step 7A.

### 3.7 Encoding (K10, OPS-2, QA-16, OPS-11)

- The house locale is cp949 (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`). The child runs with
  `-X utf8`, because `-I` ignores `PYTHONUTF8`, and an absolute script path. At import, `tools/nautilus/runner.py`
  reconfigures `sys.stdout` and `sys.stderr` to UTF-8 with `errors="replace"`, as `tests/run_all.py:35-39` does.
- In `tools/nautilus/` and the new tests: every `open`, `read_text` and `write_text` passes `encoding="utf-8"`, and text
  writes pass `newline="\n"`; every text-mode `subprocess` call, `git` included, passes `encoding="utf-8",
  errors="replace"`; every `csv.writer` passes `lineterminator="\n"`, because it writes `"\r\n"` otherwise.
- The registration table, the only file the owner edits by hand, is read with `utf-8-sig`, so a BOM from Notepad or
  PowerShell 5.1 is tolerated. Every other file is read as plain `utf-8`.

### 3.8 Never concurrent

- A pilot writes `~/.nextgen/macro/ledgers`, which T-HERM-02 snapshots while the suite runs
  (`tests/macro_acceptance.py:25-27, 101-138`): a pilot and a suite run never overlap
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:143-144`).
- A pilot never runs while a frozen-study readout runs (GOVERNANCE-9); the H2 readout registers rows into C3
  (`paper_live/replay.py:172`). paper_live defines no lock file at `6f7c610`, so the runner refuses while
  `<ledger dir>/C3.jsonl` or the table's family ledger was modified less than 600 seconds ago (R-16). One runner per
  table at a time, through a per-table OS lock (5.3.5; OPS-15).
- In the Linux container, `python tests/run_all.py` is never run, with or without `--suite`
  (`tests/run_all.py:128-137`; K13); 8.6 gives the only allowed form.

### 3.9 Unseen pilot windows

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

### 3.10 Ledger append-only

Ledgers are append-only and hash-chained; a duplicate `config_id` never replaces the first row
(`core/quant/gate_ledger.py:337-355`). Every variant is registered before its first engine run. Of-record mode needs
an existing, non-empty family ledger whose chain verifies, and never creates one (GOVERNANCE-3; R-15). No bridge code
edits `core/quant/gate_ledger.py` or another harness source (`core/quant/gate_package.py:36-38`); helpers live in
`tools/nautilus/`.

### 3.11 Standing house rules

- Never edit `paper_live/` or `grokteam/`; never run their replay, grid, verdict, sameday or calibrate modules, or
  `grokteam.book`. `docs/asset_expansion/cards/` stays at 34 files and read-only (`tests/macro_m7_cards.py:833`).
- `tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml` and `config.py` are CRLF: edited only with the
  Edit tool and never renormalised (map04 R19). `config.py` is not edited.
- Bridge code contains no T-RO-01 text token; the case-sensitive `CANO` also matches identifiers such as `CANONICAL`
  (`tests/macro_m0_harness.py:35`).

### 3.12 Egress control (SECURITY-1)

Every child runs without network (`unshare -rn` on Linux, a firewalled dedicated interpreter on Windows; 4.4), and
of-record mode needs a passing probe in the same run and a matching Step 7A record (R-14). The scan is one layer of three.

## 4. Architecture

### 4.1 Two processes

- **Parent: the runner**, in the global interpreter (numpy 2.3.5, pandas 2.3.3, scipy 1.18.0). It imports QUANTGEN
  read-only (`config`, `core.quant.strategies`, `core.quant.validate`, `core.quant.gate_ledger`, and
  `core.quant.gate_package` for `HARNESS_SOURCES`, 6.6), loads
  `docs/asset_expansion_study.py` by path for P0 (5.3.2 step 7), never imports `nautilus_trader` (rule C2), and reads
  the venv's own files for versions and the wheel identity (6.7) through `tools/nautilus/launch.py`.
- **Child: the sandbox**, in the pinned venv, one process per (column, cost level). It imports only what 5.2.2 allows.
- Files are the only interface: the parent writes `input.json` and `bars.csv` into a fresh temp dir; the child writes
  `fills.csv`, `decisions.csv`, `onbar_equity.csv` and `manifest.json` there; the parent reads, hashes and checks them,
  parses the import census from the child's stderr (5.2.7), then deletes the dir.

### 4.2 Data flow

```
 parent (global interpreter): python -B -m tools.nautilus.runner --table T {--of-record | --rehearsal ...}
   0 lock, freshness, earlier runs  1 table, identity, digests  2 git  3 venv, --check-env, --guard-selftest  4 egress
   5 data md5, dates  6 cash rate  7 P0a vs the study's loaders  8 cost  9 GATE snapshot  10 ledger hash
  11 register_trial per variant -> of-record ~/.nextgen/macro/ledgers/<F>.jsonl | rehearsal <tmp>/ledgers/<F>.jsonl
  12 run record IN_PROGRESS   13 QUANTGEN reference (simulate, 1x and 2x)
  14 per (column, cost level): temp dir, input.json + bars.csv  --launch contract (4.3)-->  child
  15 rebuild returns, reconcile, judge census  <--  fills, decisions, equity, manifest.json, stderr census
  16 parity P0b-P13; wf_qg and selection-matched wf_nt; score both   17 card only on parity and agreement

 child (venv from a dedicated base interpreter; Windows: firewall rule on it):
   [unshare -rn] <venv python> -I -B -X utf8 -X importtime <abs>/tools/nautilus/sandbox.py run --in <dir>
   BacktestEngine(run_analysis=False), kernel BACKTEST asserted; SIM venue (CASH, NETTING); the port refuses to
   start without a TestClock; one self.submit_order; FillModel seed 42; no network; opens only <dir>/<name>
```

### 4.3 Launch contract

Every child, whether the sandbox, the egress probe or a test stub, starts through one function, `run_child`, in
`tools/nautilus/launch.py`, which also holds the venv and wheel-identity reads (6.7) and the census parser (5.2.7) and
is built at Step 3 (QA-R2-5). At Step 5 it gains `fixture_inputs(name) -> (input_bytes, bars_bytes)` for F1, F1r, F2
and N1, the one builder that L2-4, L2-5a, L2-5b, `--fixtures`, `--write-goldens` and L1-33 use (QA-R3-1).

| Item | Value | Item | Value |
|---|---|---|---|
| argv, POSIX | `[<unshare>, "-rn", <venv python>, "-I", "-B", "-X", "utf8", "-X", "importtime", <abs sandbox.py>, "run", "--in", <tempdir>]` | argv, Windows | the same without `<unshare>, "-rn"` |
| argv variants | `--check-env` and `--guard-selftest` replace the last three items with that flag and drop `"-X", "importtime"`. The egress probe replaces script and mode with `<abs tools/nautilus/egress_probe.py>` and drops `"-X", "importtime"`. A rehearsal `--child-cmd` replaces the items from `<venv python>` to the script path (5.3.1); its first item must be absolute, and its directory is the `<venv bin dir>` of the env rows. | unshare | `shutil.which("unshare")`, resolved once per run; it must exist and `unshare -rn true` must exit 0, else R-14 |
| venv python | `QUANTGEN_NAUTILUS_PYTHON`, resolved as 6.7 says | process | `subprocess.Popen(argv, cwd=<tempdir>, env=<env>, stdin=DEVNULL, stdout=PIPE, stderr=PIPE, text=True, encoding="utf-8", errors="replace")`, with `start_new_session=True` on POSIX and `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` on Windows. Everything from `Popen` to the end of `communicate` sits in `try/except BaseException`, which kills the tree, drains with `communicate(timeout=30)` and re-raises, so a `KeyboardInterrupt` leaves no child (OPS-R2-4). |
| timeout | `communicate(timeout=900)`, or the `timeout` a rehearsal test passes (5.3.1). On expiry: Windows `taskkill /T /F /PID <pid>`, POSIX `os.killpg(pid, SIGKILL)`; then `communicate(timeout=30)` drains; the run is INVALID (C-06). This extends `tools/debate.py:64-78` (OPS-1). | cwd | `os.path.realpath(tempfile.mkdtemp(prefix="qgnb_"))`; the parent creates `<tempdir>/home` and `<tempdir>/tmp` first |
| env, Windows | `SYSTEMROOT` (copied), `PATH` = `<venv Scripts dir>;` + `os.environ["SYSTEMROOT"]` + `\System32` (an env dict is not expanded; OPS-R2-8), `USERPROFILE` and `HOME` = `<tempdir>\home`, `TEMP` and `TMP` = `<tempdir>\tmp` | env, POSIX | `PATH` = `<venv bin dir>:/usr/bin:/bin`, `HOME` = `<tempdir>/home`, `TMPDIR` = `<tempdir>/tmp`, `LANG` and `LC_ALL` = `C.UTF-8` |
| env, never | any `.env` key, `NAUTILUS_PATH`, any `PYTHON*` variable, any other inherited variable; the builder asserts the dict holds exactly its branch's keys (C-10) | output | `import time:` lines of stderr form the census (5.2.7); the last 4,000 characters of the rest of each stream go into the run record |
| return code | read by the parent (5.2.1); on Windows a code at or above `0xC0000000` is also recorded as NTSTATUS hex, such as `0xC0000409` | cleanup | `shutil.rmtree(<tempdir>, onexc=...)`, up to 3 attempts 0.5 s apart; it never changes the status; leftovers go into the run record (OPS-9) |
| paths | every path comparison (egress record, `pyvenv.cfg`, temp-dir containment) uses `os.path.normcase(os.path.realpath(p))`; records keep the raw and the normalised form (OPS-R2-8) |  |  |

`-I` implies `-E`, `-P` and `-s`: no `PYTHON*` variables, no user site, no script directory on `sys.path`. Whether the
venv launcher works on Windows with this minimal environment is UNVERIFIED; Step 7A checks it.

### 4.4 Egress layer (SECURITY-1, SECURITY-4, OPS-13)

The static scan cannot bind the Rust core, whose network clients load in every backtest (O13); the OS does.
- **Linux.** Every child runs under `unshare -rn`, a new user and network namespace with no route out. Measured in
  `scratch:rev2_probe/`: the engine builds, F1 and F2 reproduce their fills, and a connect fails with errno 101.
- **Windows.** The venv comes from a dedicated base interpreter, `%LOCALAPPDATA%\quantgen\py313\python.exe`, installed
  only for the bridge; the venv's `Scripts\python.exe` redirector starts it. A firewall rule, display name
  `QUANTGEN-nautilus-block-out`, blocks outbound traffic for that file on all profiles. The global interpreter is a
  different file, so QUANTGEN's data fetches are unaffected. That the rule binds the redirector-started process is
  UNVERIFIED until Step 7A's probe. The runner refuses (R-03) a Windows venv whose `pyvenv.cfg` `executable` is the
  global interpreter's `sys._base_executable`, or whose `home` or `executable` lies under `WindowsApps` or
  `\Packages\PythonSoftwareFoundation.`: the Microsoft Store Python, the owner's global interpreter (O9; OPS-R2-2).
- **Probe.** `tools/nautilus/egress_probe.py` uses `json` and `socket` only: `socket.create_connection(("1.1.1.1",
  443), timeout=3)`; it prints `{"blocked": bool, "errno": int or null, "error": str}` and exits 0 when the connect
  failed, 1 when it connected (closing at once). It imports nothing from `nautilus_trader` or QUANTGEN and passes
  T-RO-01 (`socket` is not in `FORBIDDEN_IMPORTS`, `tests/macro_m0_harness.py:38-42`; 8.5). Before registration, in
  both modes, the runner launches it through the launch contract and refuses unless `blocked` is true (R-14).
- **Step 7A record.** `runner --egress-record` writes `docs/nautilus_bridge/egress/<platform tag>.json`: `schema`
  (`"nautilus-bridge-egress/1"`), `platform_tag`, `venv_python`, `base_python` (`pyvenv.cfg` `executable`), `layer`
  (`"unshare -rn"` or the rule name), `probe`, `recorded_utc`, and `control_connect`, the parent's own connect to
  1.1.1.1:443 (`{"ok": bool, "error": str}`), which must succeed so the record proves the rule, not an outage; it and
  the hand-off report's copy (5.3.1) are the only network calls the runner makes. `--egress-record` writes the record,
  then exits 2 (R-14) unless `probe.blocked` and `control_connect.ok` are both true (SECURITY-R4-3); when the control
  connect failed, it prints the control error before R-14's remedy (OPS-R5-4). Of-record mode
  refuses unless the file exists, `probe.blocked` and `control_connect.ok` are true, and `venv_python`, `base_python`
  and `layer` equal the current run's, paths compared as 4.3 says (R-14).

## 5. Component design

### 5.1 `requirements-nautilus.txt`

New file at the repo root, LF. Header, verbatim (OPS-5):
```
# QUANTGEN NautilusTrader bridge: a research-only backtest engine, run only as a subprocess (spec 2026-10-26).
# NEVER install with the global python: tests/frozen_guard.py clause (d) pins numpy 2.3.5, scipy 1.18.0 and
# pandas 2.3.3, and tests/nautilus_acceptance.py fails while nautilus_trader is importable there.
# Install only into the dedicated venv (spec section 4.4), never created with --system-site-packages:
#   cmd:        "%LOCALAPPDATA%\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "%LOCALAPPDATA%\quantgen\wheels" -r requirements-nautilus.txt
#   PowerShell: & "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels" -r requirements-nautilus.txt
```

Body: `scratch:closure/requirements-nautilus.body.txt`, copied verbatim. It pins 16 distributions with `==` and
`--hash=sha256:` lines for every wheel either platform uses; it installs with `--require-hashes` into a fresh Linux
venv (`scratch:ntvenv_hash`), and `pip check` is clean there. The list, with the number of hashes in brackets:
`click==8.5.0` [1]; `colorama==0.4.6 ; sys_platform == "win32"` [1]; `fsspec==2026.2.0` [1]; `msgspec==0.22.0` [2];
`nautilus-trader==1.231.0` [2]; `numpy==2.3.5` [2]; `pandas==2.3.3` [2]; `portion==2.6.3` [1]; `pyarrow==26.0.0` [2];
`python-dateutil==3.0.0` [1]; `pytz==2026.5` [1]; `six==1.17.0` [1]; `sortedcontainers==2.4.0` [1]; `tqdm==4.70.1`
[1]; `tzdata==2026.5` [1]; `uvloop==0.22.1 ; sys_platform != "win32"` [1].

The `nautilus-trader` hashes equal PyPI's (synth §9.3): win_amd64
`5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf`, manylinux_2_35_x86_64
`429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91`. The runner reads the expected versions of
`nautilus-trader`, `numpy` and `pandas` from this file (names normalised as PEP 503 does); it is the single source of
the pins. The owner keeps the Windows closure in `%LOCALAPPDATA%\quantgen\wheels\` (Step 7A); the firewall blocks the
venv's network, so every install is offline from that folder.

### 5.2 `tools/nautilus/sandbox.py`

#### 5.2.1 Modes and exit codes

The sandbox has three modes, `--check-env`, `--guard-selftest` and `run --in <tempdir>`, launched as 4.3 says; 5.2.9
gives the file's structure.
- `--check-env` builds one `BacktestEngine` (5.2.3), prints one JSON object and writes no file: `schema`
  (`"nautilus-bridge-check-env/1"`), `python`, `system`, `machine` (`platform.uname()`, never `platform.system()`, a
  call rule F6 flags by its name), `precision` (`HIGH_PRECISION`, `FIXED_PRECISION`, `QUANTITY_MAX`, `PRICE_MAX`),
  `environment` (`engine.kernel.environment.name`). The parent reads
  versions and the wheel identity itself (6.7), because the sandbox may not import `importlib` or `sys` (rule F).
- `--guard-selftest` runs the guard of 5.2.5 against non-backtest values (C-2): `require_backtest_environment` with
  `Environment.SANDBOX` and `Environment.LIVE`, and `require_backtest_clock` with `LiveClock()`, must each raise
  `RuntimeError`; with `Environment.BACKTEST` and `TestClock()` neither may raise. It prints case name to `"raised"`
  or `"passed"` and exits 30 if any case differs. Measured with the filled skeleton of 5.2.9: all five cases behave.
- `run` reads `input.json` and `bars.csv`, runs one backtest and writes four files (5.2.6).
- Exit codes: 0, run complete and valid by the child's checks; 10, complete but invalid (`manifest.json` written with
  `valid: false`); 20, input refused before the engine is built (schema, range, SHA-256, precision, volume, path
  containment); 30, a self-test case misbehaved; any other value, a crash. Every non-zero code is an invalid run.

#### 5.2.2 Imports and language

The sandbox holds exactly the import block of 5.2.9: one statement per entry of 5.6's allow-lists, with every listed
name (`import m` where `SANDBOX_STDLIB[m]` is None; `from m import <names>` for the other entries and every
`NAUTILUS_ALLOWED_FROM` module). All import in `scratch:ntvenv` (`scratch:rev2_probe/probe_imports.py`); they are the
1.231.0 paths, and the v2 paths in the tag's docs fail on this wheel (map01 §10.4). `LatencyModel` is gone (C-1).

Language rules, enforced by 5.6 rule F (SECURITY-1):
- no `os`, `sys` (except `from sys import argv, exit`), `importlib`, `builtins`, `ctypes`, `socket`, `ssl`, `http`,
  `urllib`, `asyncio`, `subprocess`, `gc`, `inspect` or `types`;
- no `getattr`, `setattr`, `delattr`, `vars`, `globals`, `locals`, `eval`, `exec`, `compile`, `__import__`,
  `breakpoint` or `open`; no subscript on a name bound by `ast.Import` (`import m`, a module alias), or on an attribute
  chain rooted at one; a name bound by `from ... import`, such as `argv`, is not a module alias (SECURITY-R2-1);
- no attribute whose name starts with `__`, so no `super().__init__`: the ports take their parameters from a
  `StrategyConfig` subclass and set their state in `on_start`, and the fee model is a closure (5.2.3, 5.2.9);
- no call named as a `SANDBOX_OS_CALLS` entry, so `platform.uname().system`, never `platform.system()` (F6);
- file access only through `inside(...)` (5.2.8).

Rule F rejects the direct spellings (`import sys`, module-alias subscripts, dunders, dynamic calls); an attribute path
through a loaded module can still reach `sys.modules`, which the scan cannot fully close; the egress layer bounds any
use (4.4; SECURITY-R4-1).

#### 5.2.3 Engine, venue, instrument, fees and fills

| Object | Exact construction | Object | Exact construction |
|---|---|---|---|
| Engine | `BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), logging=LoggingConfig(log_level="ERROR", log_colors=False), run_analysis=False))`. `run_analysis` defaults to `True` (`nt:backtest/config.py:392`) and runs the analyzer at the end (`nt:backtest/engine.pyx:2143`; K6). `log_colors` defaults to `True` (`nt:common/config.py:680`) and would put ANSI codes in the tails (OPS-10). No `log_level_file`, no catalog, no streaming. | Kernel check | Right after construction: `require_backtest_environment(engine.kernel.environment)`. `BacktestEngine.kernel`: `nt:backtest/engine.pyx:322-332`; `NautilusKernel.environment`: `nt:system/kernel.py:641-651`; `Environment`: `nt:common/__init__.py:33-40`. |
| Venue | `engine.add_venue(venue=Venue("SIM"), oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=USD` (SPY) or `None` (BTC/USD), `starting_balances=[Money(capital, USD)]` plus `Money(0, BTC)` for BTC/USD, `fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0, random_seed=42)`, `fee_model=make_fee_model(cost_bps, stress)`, `bar_execution=True`, `bar_adaptive_high_low_ordering=False`, `allow_cash_borrowing=False)`, with no `latency_model` argument (C-1). A `CurrencyPair` needs `base_currency=None` on a CASH venue (`nt:backtest/engine.pyx:762-770`). | SPY | `Equity(instrument_id=InstrumentId(Symbol("SPY"), Venue("SIM")), raw_symbol=Symbol("SPY"), currency=USD, price_precision=9, price_increment=Price.from_str("0.000000001"), lot_size=Quantity.from_int(1), ts_event=0, ts_init=0, maker_fee=Decimal(0), taker_fee=Decimal(0))`. Whole shares only (`nt:model/instruments/equity.pyx:115-117`). A fixture with another `price_precision` uses the matching increment. |
| BTC/USD | `CurrencyPair(instrument_id=InstrumentId(Symbol("BTC/USD"), Venue("SIM")), raw_symbol=Symbol("BTC/USD"), base_currency=BTC, quote_currency=USD, price_precision=9, size_precision=8, price_increment=Price.from_str("0.000000001"), size_increment=Quantity.from_str("0.00000001"), ts_event=0, ts_init=0, maker_fee=Decimal(0), taker_fee=Decimal(0))`. Spot, long/flat, commission in USD (map03 §5.2). | Fee model | `make_fee_model(cost_bps: str, stress: str) -> FeeModel` raises `ValueError` when `Decimal(stress) < 1`, sets `rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)`, and returns an instance of a class defined inside it, `BpFeeModel(FeeModel)`, whose one method `get_commission(self, order, fill_qty, fill_px, instrument)` returns `Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate, instrument.quote_currency)`. No `__init__`. It equals `MakerTakerFeeModel` with `taker_fee = c` (map01 §5.1). `prob_slippage=0` keeps all cost in one number, so the 2x leg doubles one number (map01 §5.2). |
| Fill timing | MARKET, GTC, sent from `on_bar`; it fills at the same bar's close: the engine moves the book through the bar, calls the strategy, then settles (`nt:backtest/engine.pyx:1716, 1724, 1727`). `AT_THE_CLOSE` is rejected in backtest and never used (`nt:backtest/engine.pyx:5333-5339`). |  |  |

There is no `change_fee_model`, so each cost level is a fresh engine in a fresh process (map01 §2.2).

#### 5.2.4 Bars (K1)

Bars are built with the wrangler's own constructor calls (`nt:persistence/wranglers.pyx:779-791`), not from a
DataFrame: `Bar(bar_type, Price.from_str(c), Price.from_str(c), Price.from_str(c), Price.from_str(c), Quantity(volume,
size_precision), ts, ts)` with `c` the close string, so O = H = L = C = the adjusted close. Bar types are
`SPY.SIM-1-DAY-LAST-EXTERNAL` and `BTC/USD.SIM-1-DAY-LAST-EXTERNAL`; `EXTERNAL` is required for bar execution
(`nt:backtest/engine.pyx:4757-4758`). `ts_event = ts_init` = the close: SPY at 21:00 UTC on the date, BTC at 00:00 UTC
the next calendar day. The parent rounds once, `closes = np.round(raw, p)`, asserts `float(f"{y:.{p}f}") == y` for
every close and writes `f"{y:.{p}f}"` (QUANT-R2-7; 5.3.2 step 5). The pilots use volume 1,000,000,000; on a LAST bar
the close carries a quarter of it, 2.5e8 units
(`nt:backtest/engine.pyx:4804-4805, 4850-4880`), which an order at $1M equity exceeds only below $0.004 a unit. Thin
volume caps fills and kills the run (N1). Before building anything the child refuses (exit 20) input outside 6.1's
ranges, and checks strictly increasing timestamps and `n_bars` rows.

#### 5.2.5 Strategy ports and the backtest guard

Both ports are independent re-implementations of `core/quant/strategies.py:162-187` and `:330-348`: subclasses of one
`Port(Strategy)`, each with a config subclass of a frozen `PortConfig(StrategyConfig, frozen=True)` carrying
`instrument_id`, `bar_type`, `cost_bps`, `stress`, the close strings and timestamps of `bars.csv`, and the parameters
(5.2.9).

**Backtest guard (C-2).** `require_backtest_environment(env)` raises `RuntimeError` unless `env is
Environment.BACKTEST`; `run` calls it on `engine.kernel.environment` right after building the engine.
`require_backtest_clock(clock)` raises `RuntimeError` unless `isinstance(clock, TestClock)`; each port calls it as the
first statement of `on_start`, and sets `strategy_started = True` as the last (C-15).
- Why a clock: a 1.231.0 strategy has no environment accessor (neither `nt:trading/strategy.pyx` nor
  `nt:common/actor.pyx` mentions "environment"). The trader gives each strategy a clock of the kernel's clock class
  (`nt:trading/trader.py:422`), and the kernel picks `TestClock` for BACKTEST and `LiveClock` for SANDBOX and LIVE
  (`nt:system/kernel.py:163-170`). Measured: a strategy added to a `BacktestEngine` holds a `TestClock`.
- Effect: `Component.start` logs and re-raises an `on_start` exception and leaves the strategy STARTING
  (`nt:common/component.pyx:1941-1970`); `handle_bar` calls `on_bar` only when RUNNING (`nt:common/actor.pyx:4586-4588`).
  Under a `TradingNode` the port never sees a bar and never places an order.

Shared rules:
- Decisions use `float(close_str)`, which equals the parent's rounded float. On every bar the child checks
  `bar.ts_event` against the file's timestamp and `bar.close == Price.from_str(close_str)`. The actor logs and re-raises
  an `on_bar` exception (`nt:common/actor.pyx:4588-4591`): measured, a `ValueError` planted at bar 5 of F1 ends the
  child with exit 1 (`scratch:rev3_probe/variants.py`; `scratch:rev4_probe/sandbox_raise.py`), an INVALID run by C-06
  (QA-R2-11). So a failed check appends its reason, which begins with its section-7 id (`"C-12: ..."`; QA-R3-8), to the
  port's `invalid_reasons` and returns, and the reason reaches the manifest.
- A decision is logged on every decision bar, with its margin. The strategy trades only when the decision differs from
  the held state, never topping up or trimming: QUANTGEN charges no turnover for drift (`core/quant/strategies.py:88`).
- Entry: buy `q = floor(cash / (P (1 + c s)))` in `Decimal`, with `cash` the account's USD balance, `P =
  Decimal(close_str)`, `c = cost_bps / 1e4`, `s` the stress; SPY floors to whole shares, BTC to 8 decimals with
  `ROUND_FLOOR`; if `q` is 0, no order is sent and the row says so. The fee-inclusive divisor keeps the balance
  non-negative after the fee (QA-13); otherwise the engine stops the backtest (`nt:backtest/engine.pyx:1740-1745`), and
  the risk engine does not catch it, because on bar-only data it has no price and skips MARKET-order checks ("Cannot
  check MARKET order risk: no prices", `nt:risk/engine.pyx:768-789`).
- Exit: sell the whole net position. No liquidation at the end; QUANTGEN never liquidates (map03 §2.5).
- One method places orders: `place(self, order)`, whose only statement is `self.submit_order(order)`. An order in
  flight on a decision bar makes the run invalid (C-13). The port's state never uses the name `state` (map03 §2.5).

| Port | Decision rule | Child margin |
|---|---|---|
| `TrendSwitchPort` (`rule`, `lookback` L, `step` s) | Bar counter i starts at 0 on the first panel row; decision bars `i >= L and (i - L) % s == 0` (`core/quant/strategies.py:146-147, 176`). `sma`: `on = P[i] > mean`, `mean = plain_mean(P[i-L+1 : i+1])`, a plain left-to-right loop (5.2.9), not `sum()`, which Python 3.12 and later compensates (measured on 3.13: `sum([1e16, 1.0, -1e16])` is 1.0, the loop 0.0). `tsmom`: `on = (P[i] / P[i-L] - 1.0) > 0.0`, the study's raw form, because `pnl_matrix` passes no rate (`:180-181, 384`). | `sma`: `abs(P[i] - mean) / P[i]`; `tsmom`: `abs(P[i] / P[i-L] - 1.0)` |
| `CryptoTrendPort` (`hysteresis` h, `lookbacks`, `mas`; pilot defaults (7, 14, 21, 28) and (10, 20, 50, 100, 200)) | Warm-up `max(max(lookbacks), max(mas))`, then a decision every bar. Votes `sign(P[i] - P[i-k])` per k in `lookbacks` and `sign(P[i] - plain_mean(P[i-n+1 : i+1]))` per n in `mas`, the same loop (QA-R3-9), `sign(x) = (x > 0) - (x < 0)`; `comp = sum(votes) / len(votes)`; state 1 if `comp > h`, 0 if `comp < -h`, else unchanged (`core/quant/strategies.py:343-347`). | the smallest `abs(P[i] - ref) / P[i]` over the votes |

#### 5.2.6 Outputs (in the temp dir, UTF-8, LF, `csv.writer(..., lineterminator="\n")`)

| File | Columns or content |
|---|---|
| `fills.csv` | One row per `on_order_filled` event (`nt:trading/strategy.pyx:723`): `ts_event` (int ns), `order_side` (`BUY` or `SELL`), `last_qty` (`str(ev.last_qty)`), `last_px` (`str(ev.last_px)`), `commission` (`f"{ev.commission.as_decimal():.2f}"`), `commission_ccy`, `trade_id`, `venue_order_id`. No UUID. |
| `decisions.csv` | One row per decision bar: `i`, `ts_event`, `decision` (0 or 1), `margin` (`repr(float)`), `action` (`buy`, `sell`, `hold`, `skip_zero_qty`). |
| `onbar_equity.csv` | One row per bar, in `on_bar` before any order: `i`, `ts_event`, `close`, `cash`, `qty`, `equity_pre` (`cash + qty x close`, Decimal). |
| `manifest.json` | 6.2. |

The child never calls `PortfolioAnalyzer` or reads the account report as equity: on a CASH account the analyzer's
returns are cash only, and the probe printed a Sharpe of +1.94 for a true -1.90 (map01 §0 finding 5).

#### 5.2.7 Checks in the child, and the import census

The child marks the run invalid (exit 10) when: `is_backtest_force_stop()` is true after `engine.run()`
(`nt:common/component.pyx:619-620`); bars seen are fewer than bars fed, or `get_result().backtest_end` is earlier than
the last bar; any order is not FILLED (`order.status.name != "FILLED"`), with no exemption; any `OrderDenied` or
`OrderRejected` (counted in `on_order_denied` and `on_order_rejected`); an order was in flight on a decision bar; the
port's `invalid_reasons` is non-empty or `strategy_started` is false. Each reason begins with its section-7 id, such as
`"C-01: forced stop"` (QA-R3-8). `run` resets the force-stop flag at the start (`nt:backtest/engine.pyx:1621-1622`;
K14); one process per run stays, for the `random` reseed. The parent re-derives C-01 to C-04 and C-15 from the manifest
(`result.force_stop`; `bars_seen` against the parent's own `n_bars`, and `backtest_end` against its own last timestamp;
`orders_not_filled`; `denied` and `rejected`; `strategy_started`) and marks the run INVALID with that id even when
`valid` is true and the exit code is 0 (QA-R3-2). The echoes `input.bars_fed`, `first_ts` and `last_ts` must equal the
parent's own values (C-11; QA-R4-3).

**Import census (SECURITY-2, QA-11, OPS-7).** The sandbox may not touch `sys.modules` (rule F), so the parent runs
`run` with `-X importtime` and reads the census from stderr: each line starting `import time:` splits on `|`, and its
third field, stripped, is a module name (the header field `imported package` is skipped). The census is the sorted set
of names: every attempted import, failed optional ones included (measured: `plotly` appears though not installed). It
omits the 35 compiled submodules `nautilus_pyo3` creates itself, which the wheel identity fixes (6.7). Measured on
Linux for an engine build: 964 lines, 940 names, 185 top-level names, 161 of them stdlib.

The census is drift detection, not a use guard: it cannot see use of a module already loaded. Each name has one class by
its top-level component: NT (`nautilus_trader`); STD (in the parent's `sys.stdlib_module_names`, `sitecustomize`,
`usercustomize`, or starting `_sysconfigdata`); TP (every other name). A run is invalid (C-08) when an NT name equals or
lies under `nautilus_trader.adapters` or `nautilus_trader.network`, or its NT or TP set differs from the platform
baseline's (`tools/nautilus/golden/modules_<platform tag>.json`). STD names may differ between 3.13.x patch levels and
platforms (QA-11). A platform's baseline is the union of its F1 and F2 censuses: Step 6 records Linux's, Step 7A
Windows'. Across platforms the NT sets must be equal, and the TP sets may differ only by `uvloop*` (POSIX only) and
`colorama*` (Windows only). `--record-baseline` prints that diff and never overwrites a baseline git tracks (`git
ls-files --error-unmatch <path>` exits 0): an existing equal one gives "unchanged" and exit 0; a different one writes
nothing, prints its diff and the removal line, `Remove-Item tools\nautilus\golden\modules_<tag>.json` on Windows or `rm
tools/nautilus/golden/modules_<tag>.json` on Linux (OPS-R4-5), to run only after Claude has reviewed that diff, and
exits 2 (OPS-R3-2). An untracked baseline is a leftover of a failed attempt: it is replaced, its diff is printed, and
the exit is 0 (OPS-R4-2, OPS-R5-3). A tracked path with no file, as after the printed removal line (git still lists
the path until a commit removes it), is written, with exit 0 (OPS-R5-3). The rule lives in the pure
`record_baseline(golden_dir, tag, census, *, tracked) -> (exit, diff_lines)`, which the CLI calls with `tracked` from
`git ls-files` (QA-R4-4). Claude reviews the Windows diff in the next session,
before any pilot (OPS-7).

#### 5.2.8 Path containment (SECURITY-3)

`run --in <dir>`: `<dir>` must be absolute and equal its own `Path.resolve()`, else exit 20; the parent passes the
`os.path.realpath` of the temp dir. `inside(root, name) -> Path`, `root` being that dir, builds every path the sandbox
opens: it returns `(root / name).resolve()` and raises `Refused` (exit 20) unless that path's parent equals `root`, so a
symlink pointing outside is refused. Every call of a `SANDBOX_FILE_METHODS` method must be on a receiver that is a call
to `inside` (rule F5); the builtin `open` is banned (F2). Negative control: L2-5b links `<tempdir>/input.json` to the
repo's `.env`; exit 20.

#### 5.2.9 Structure of `sandbox.py` (C-5)

Normative for structure, not for every line: the import block (verbatim), the classes and functions, the statement that
holds each guard, and how rule F is met (no `__init__` and no `super()`, the fee closure, `inside`, `platform.uname()`).
`...` marks a body that 5.2.3 to 5.2.8 specify. Revision 4 adds `plain_mean` (QA-R3-9), the id at the head of each
reason (QA-R3-8) and the `__main__` guard (SECURITY-R3-1; `__name__` is a `Name`, not an `Attribute`, so F3 does not
apply). Filled in, it reproduces F1, F2 and N1 and both self-checks under `unshare -rn`, exits 20 on each of 65
refusal cases of 6.1 and 5.2.8 (L2-5a, L2-5b), gives no scan hit, and is the positive control of 8.5
(`scratch:rev4_probe/skeleton.py`, `fill.py`, `sandbox_r4.py`, `drive.py`, `scan4.py`).

```python
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
```

### 5.3 `tools/nautilus/runner.py`

#### 5.3.1 Command line, modes and test seams

`python -B -m tools.nautilus.runner` takes `--table <t> --rehearsal --ledger-dir <tmp> --out-dir <tmp> [--child-cmd
<json list>]`, `--table <t> --of-record`, either with `[--rerun-of <id> --reason <text>]` (5.3.5), `--check-env`,
`--egress-record`, `--timing`, `--fixtures [--record-baseline | --write-goldens]`, `--handoff-report`, or `--fingerprint
--table <t>`.

| Mode | Ledger | Data | Tree | Outputs |
|---|---|---|---|---|
| `--rehearsal` | `--ledger-dir`, required, inside the temp root (3.9; OPS-R4-4) | synthetic only: `prices_file` and any `reference_card` inside the temp root, judged at step 1 (QA-R4-2), and the md5 refusal of 3.9 (GOVERNANCE-R3-3) | recorded, never refused (QA-R2-1) | `--out-dir`, required, inside the temp root |
| `--of-record` | `config.macro_dir() / "ledgers"` (`config.py:176-178`); `--ledger-dir` and `--out-dir` refused | the pinned files of the table | clean (5.3.2 step 2) | `docs/nautilus_bridge/runs/<bridge_run_id>/`, from the repo root, never the working directory |

- `--check-env` runs `sandbox.py --check-env` and `--guard-selftest` and the venv checks of 6.7 (exit 0 on a match, 2
  otherwise). `--egress-record` writes 4.4's record and exits as 4.4 says. `--timing` prints the `BacktestEngine`
  import time (the cumulative `-X importtime` figure of `nautilus_trader.backtest.engine`) and the wall time of 12
  synthetic runs of 5,600 bars. `--fingerprint` validates the table against 6.6 with both owner fields optional, opens
  no data file (`prices_file`, `rf_file`, `reference_card`), always prints `table_sha256` and `code_sha256`, prints
  `host_fingerprint` when the family ledger exists and holds a row and otherwise `null` with the reason, and exits 0
  when both digests are printed (GOVERNANCE-R4-1). `--fixtures` runs 8.2's F1, F2 and N1 through the launch contract
  against their goldens (6.8); `--record-baseline` then writes the census baseline only if all three match, else exits
  2 and writes nothing (OPS-R2-1), and treats an existing baseline as 5.2.7 says, through `record_baseline` (QA-R4-4);
  `--write-goldens` writes the goldens, on Linux only, never over an existing file (QA-R2-6). `--handoff-report`
  (OPS-8) writes `docs/nautilus_bridge/handoff/<tag>.json`, `<tag>` being the parent's `sysconfig.get_platform()` with
  `-` and `.` replaced by `_`, so `win_amd64` even without a venv (OPS-R3-4): the `--check-env` and `--guard-selftest`
  JSON; the parent's `sys.executable`, `sys._base_executable` and `sys.version`; `git rev-parse HEAD`, `git rev-parse
  origin/claude/amazing-gauss-tdiguu` and `git status --porcelain=v1` (OPS-R4-1); the stub interpreter 8.1 picks
  (QA-R4-4); a fresh probe and parent control connect, in the egress record's shape; on Windows, through `powershell
  -NoProfile -NonInteractive -Command`, whose `Format-List` output is English and ASCII under cp949 (OPS-R4-3):
  `Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Format-List DisplayName, Enabled, Direction, Action,
  Profile`, the same rule piped to `Get-NetFirewallApplicationFilter | Format-List Program`, and
  `Get-NetFirewallProfile | Format-List Name, Enabled`; each fixture's result, diff against its golden and child
  tails; the census diff against the Linux baseline; both timings; the FAIL rows and every `nautilus/*` row of
  `qa/acceptance_results.json`, with that file's mtime; each part records its own error instead of stopping. Only
  `--egress-record`, `--record-baseline`, `--write-goldens` and `--handoff-report` write files; `--egress-record` and
  `--handoff-report` overwrite theirs, and git keeps the history (OPS-R3-2).
- Pure steps (QA-1, QA-7, QA-R2-1, GOVERNANCE-R2-4). Steps 0 to 2 and step 4's record match are functions with explicit
  roots: `take_lock(out_root, table_sha256, ledger_paths, rerun_of)` (R-16, R-17), `check_table(table, mode, ledger_dir,
  hostname, repo_root)` (R-10's place rule, R-11, R-15; QA-R4-2), `check_tree(repo_root, anchor_fn, git_exe)`, whose
  findings `tree_refusal(findings, mode) -> "R-01" | "R-02" | None` judges (QA-R3-7), and
  `check_egress_record(record_dir, run_facts)` (R-14); step 7's comparison is `check_p0a(study_module, cache_dir,
  arrays)` (R-13), which `run()` calls with the study module it loaded. Of-record mode calls them with fixed arguments;
  tests call them on temp roots. In rehearsal, `tree_refusal` returns None, the findings are recorded, and a missing git
  records null.
- Test seams (QA-R2-2). `run(table_path, *, mode, ledger_dir=None, out_dir=None, child_cmd=None, probe_cmd=None,
  hooks=None, timeout=900, register_fn=gate_ledger.register_trial, score_fn=validate.score_strategy, rerun_of=None,
  reason=None)`. `child_cmd` (CLI `--child-cmd`, a JSON list) replaces the argv items from `<venv python>` to the script
  path; the runner appends the mode arguments. With it, step 3 launches the stub's `--check-env` and `--guard-selftest`
  and skips the venv file reads, the census judgement is skipped, and the run record says `stub_child: true` and a
  card's `rules.engine` `STUB`. `probe_cmd` replaces the probe's argv; the runner never derives it from `child_cmd`, and
  every layer-1 runner test passes both (QA-R3-5). `hooks` maps `after_step<n>` (n = 0 to 17) or `child_started` (called
  after `Popen`, before `communicate`) to a callable; `register_fn` and `score_fn` replace `register_trial` and
  `score_strategy`; `timeout` replaces 900 s. Of-record mode refuses every seam during argument validation, before step
  0 writes anything (R-11). Claude never runs of-record mode (Step 2); a call refused in argument validation is not a
  run.

#### 5.3.2 Order of operations (of-record)

| Step | What the runner does | Refusal |
|---|---|---|
| 0 Lock, freshness, re-run | Parses the table only to compute `table_sha256` (6.6; not JSON: R-11); takes the table lock (5.3.5); reads every earlier record of the table, best effort (`UNREADABLE` otherwise), and applies the re-run policy (5.3.5); reads the modification times of `<ledger dir>/C3.jsonl` and the family ledger | R-16: lock held, or a write under 600 s ago; R-17 |
| 1 Table, of-record identity | Loads the table with `utf-8-sig`; validates it against 6.6; in rehearsal, judges the place rule of 3.9 for `prices_file` and `reference_card` before any file is opened (QA-R4-2); checks `grid` equals `S.grid_from(**axes)` element by element (`core/quant/strategies.py:392-398`) and the pilot values (capital `"1000000"`, 9 price decimals, volume `"1000000000"`, seed 42); checks that `owner_confirmed` quotes this table's `table_sha256` and the tree's `code_sha256` (6.6; GOVERNANCE-R2-2); checks the family ledger exists, holds a row and verifies, and `host_fingerprint` equals this host's; when `reference_card` is set, checks the md5 of its bytes against `reference_card_md5` (QUANT-R3-3); of-record `C3-BTCUSD` needs a non-null `reference_card` (QUANT-R4-2) and an of-record `E1-SPY` record in `<repo root>/docs/nautilus_bridge/runs/*/run.json` with `parity.hard_pass` true for all 12 columns at both cost levels and this run's `code_sha256` (GOVERNANCE-R4-4) | R-10 (rehearsal place); R-11; R-15 |
| 2 Git | `check_tree`, judged by `tree_refusal`: runs `git status --porcelain=v1 -z --untracked-files=all`; every entry must be untracked (`??`) under `docs/nautilus_bridge/runs/`. Runs `gate_ledger.repo_anchor()` (`core/quant/gate_ledger.py:122-131`) and `git rev-parse HEAD`; the shas must match. When the anchor is UNVERSIONED, HEAD resolves and `.git` is a directory, the message says "the branch ref is packed: run `git commit --allow-empty -m "nautilus: re-anchor"`, then `git push`" (OPS-3, OPS-R3-9); when `.git` is a file, it names a worktree. Records the sha. | R-01; R-02 (both of-record only) |
| 3 Venv | Resolves the venv and reads its files (6.7); runs `--check-env` (Python 3.13.x, environment `BACKTEST`, precision recorded) and `--guard-selftest` (exit 0 and the five outcomes of 5.2.1; QA-R2-10), recording both JSON lines; checks the parent has no `nautilus-trader` distribution (`importlib.metadata.distribution` raises `PackageNotFoundError`; not `find_spec`, which rule E flags in `tools/` when given a `nautilus` string); records the parent's `pyarrow` version or null | R-03 |
| 4 Egress | Linux: `unshare -rn true`. Runs the probe; of-record also matches the Step 7A record (4.4) | R-14 |
| 5 Data | Checks the price file's md5; keeps the header and the lines whose leading date text lies in `[start, end]`, before any value is parsed; reads the kept text as the study does (first column as index, `parse_dates=True`, `.iloc[:, 0]`, `dropna()`, values above zero; `docs/asset_expansion_study.py:68-79`); requires 300 rows or more (`:138-145`) and strictly increasing unique dates; `closes = np.round(raw, 9)`, the one rounding of the bridge, with the round trip of 5.2.4 asserted; records `rounding_changed` (any close changed) (QUANT-R2-7) | R-04 (missing, unreadable, md5); R-05 |
| 6 Cash rate (K8) | When `rf_file` is set: checks it against the table's `rf_md5` (pilot 1: `docs/asset_expansion/cache/fred_DGS3MO.csv`, `661722143f24930a29b58c535d227c1b`; QA-R4-5); reads it as `study.fred` does (`read_csv(index_col=0, parse_dates=True).iloc[:, 0]`, `pd.to_datetime` index; `docs/asset_expansion_study.py:94-104`), then `rf = DGS3MO.dropna().reindex(dates, method="ffill") / 100 / 252` (`:150`), so a blank on a bond-market holiday takes the prior value (QUANT-R2-1). Never copies the study's silent 3% fallback or leading-NaN fill (`:148-153`). `rf_file` null (pilot 2): `rf = 0.0`, the study's default (`docs/asset_expansion_study.py:175`); the overlay of 5.3.3 is zero and R-06 does not apply (QUANT-R3-2) | R-06: missing, unreadable, md5, or a NaN left after the fill (a session before the first observation) |
| 7 P0a (QUANT-1) | Loads `docs/asset_expansion_study.py` by path (`importlib.util.spec_from_file_location`); its import only creates existing folders and reconfigures stdout (`:41-58`), verified to leave the tree unchanged. Asserts `study.REFRESH is False` (`:844`). Writes a trimmed cache in the run's temp dir (step 5's kept lines as `yf_<symbol>.csv`, the name `_cached` builds; a DGS3MO copy as `fred_DGS3MO.csv` whenever `rf_file` is set), asserts each name exists, and sets `study.CACHE` to it, so `_cached` and `fred` never reach a download branch (`:68-79, 94-104`); around the study calls, `sys.modules` holds raising stand-ins for `yfinance`, `pandas_datareader` and `pandas_datareader.data`, restored in `finally`, so a download branch raises before any network call (QA-R4-1). Builds `pn = study.panel({symbol: study.yf(symbol)}, start=start)` and, whenever `rf_file` is set, `study.rf_daily(pd.to_datetime(pn.dates))` (`:138-153`); with `rf_file` null (pilot 2) there is no rf comparison, as the study passes the default `cash_daily=0.0` (`:175, 335-343`; QUANT-R4-3). `check_p0a` requires byte equality of `pn.dates`, of `np.round(pn.prices[:, 0], 9)` and of rf with the runner's arrays (QA-R3-7). No signal, return or statistic is computed. | R-13 |
| 8 Cost (K15) | `floor, classes = validate.cost_floor_bp([symbol])` (`core/quant/validate.py:115-121`) | R-07: `floor` None, or the table's `cost_bps` below it |
| 9 Gate | Snapshots `validate.GATE` with `copy.deepcopy` | R-08: `GATE["bootstrap_B"] != 2000` |
| 10 Ledger | `family_ledger(family_id, ledger_dir)`; records `hash()` and `n_raw` | R-09: `verify_chain()` fails |
| 11 Register | For each variant in grid order, `register_trial(ledger, row, script="tools/nautilus/runner.py")` with the row of 6.4 (`core/quant/gate_ledger.py:379-386`); records `config_id`, `appended` and `result.row["row_md5"]`, never `RegisterResult`'s third element, whose meaning differs between an append and a duplicate (`:346, 355`; A-1) | R-12: a raise |
| 12 Snapshot | Records `hash()`, `n_raw`, the market-scoped count and the UTC time in microseconds; writes the run record with status `IN_PROGRESS` (5.3.5) | |
| 13 Reference | Per column: `W = fn(prices, **theta)`; `pnl, turnover = simulate(prices, W, cost_bps=cost_bps, cash_daily=rf)` and the stress twin at `2 x cost_bps`, which is `pnl_matrix` column by column (`core/quant/strategies.py:379-389`); keeps the weights for P1 and P4 | |
| 14 Children | One per (column, cost level), sequentially; every `input.json` carries the post-registration ledger hash (6.1); the run record is updated after each | |
| 15 to 17 | Rebuilds and checks each child (5.3.3, section 7); parity, selection and scoring (5.4, 5.5); writes the card if earned, then the final run record | |

Rehearsal runs the same steps, except: the git state is recorded, never refused; `owner_confirmed`,
`host_fingerprint`, an existing ledger and the egress record are not needed (the per-run probe is); ledger and outputs
live under the temp dir.

#### 5.3.3 Return reconstruction

Let `P(t)` be the shared close, and `q(t)` and `cash(t)` the position and cash after the fills of bar t, rebuilt from
`fills.csv` in Decimal: a buy subtracts `qty x px + commission`, a sell adds `qty x px - commission`, starting from
`cash(-1) = capital` and `q(-1) = 0`.

```
E-(t) = cash(t-1) + q(t-1) P(t)                         equity marked at close t, before the fills of bar t
R(t)  = E-(t+1) / E-(t) - 1 + (cash(t) / E-(t)) rf(t)   for t = 0 .. T-2, labelled dates[t+1]
TV(t) = sum over fills at bar t of qty x px / E-(t)      for t = 0 .. T-2; fills at bar T-1 are dropped
```

This is the exact analogue of `pnl(t) = w(t) r(t+1) + (1 - w(t)) rf(t) - c abs(Δw(t))` (map03 §2.9;
`core/quant/strategies.py:82-90`); the last term of R is the cash-interest overlay, which Nautilus does not pay. A fill
belongs to bar t when its `ts_event` equals bar t's timestamp; a fill at any other time is invalid (C-09). Cross-checks
(C-09): `onbar_equity.csv` has `n_bars` rows (QA-R4-3); the rebuilt `E-(t)` equals `onbar_equity.csv` within $0.01 times
the fills so far, and the final rebuilt cash equals the manifest's balance within $0.01 per fill, because `Money` rounds
each commission to the cent.

#### 5.3.4 Matrices

`pnl_nt` (T-1 x G, 1x), `pnl_stress_nt` (2x) and `turnover_nt` (from the 1x run), columns in `grid_from` order (the
order of the registered rows), `dates = panel_dates[1:]` as ISO strings (`docs/asset_expansion_study.py:184`). The
QUANTGEN reference `pnl_qg`, `pnl_stress_qg` and `turnover_qg` have the same shape.

#### 5.3.5 Run lifecycle (OPS-2, OPS-6, OPS-10, OPS-15, QA-6, QA-18)

- `bridge_run_id` = `NB-<UTC as %Y%m%dT%H%M%S%fZ>-<first 8 hex of table_sha256>`, such as
  `NB-20261026T143012123456Z-1a2b3c4d`; it sits outside every result hash. The folder `<out root>/<bridge_run_id>/`,
  made with `mkdir(exist_ok=False)`, holds `run.json` and any `<card_id>.json`; a re-run never overwrites a card.
- `table_sha256` (6.6), never the file's raw bytes, names the table in the run id, the lock, `earlier_runs` and R-17, so
  a new `owner_confirmed` or a BOM and CRLF re-save is still the same table; the record keeps both digests (6.3;
  OPS-R3-5, QA-R3-3).
- Lock: `<out root>/.locks/<first 16 hex of table_sha256>.lock`, held for the whole run with a non-blocking OS lock, as
  `core/quant/gate_ledger.py:244-262` locks: on POSIX `fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)`, never `lockf`,
  whose locks never conflict within one process (L1-25); on Windows `fh.seek(0)`, then `msvcrt.locking(fh.fileno(),
  msvcrt.LK_NBLCK, 1)` (QA-R4-6); a held lock refuses with "another runner is active" (R-16).
  `docs/nautilus_bridge/.gitignore` holds `runs/.locks/`.
- The run record is written by `write_record(path, obj, *, replace=os.replace, sleep=time.sleep)` (OPS-R2-3, QA-R3-7):
  `mkstemp` in the same folder, `fsync`, then `os.replace`, retried up to 10 times over 5 s on `PermissionError`
  (OneDrive, Defender and the indexer open new files). Writes right after registration (`IN_PROGRESS`) and after each
  child are best effort: a failure goes into `record_write_failures` and never changes the status. The final write sits
  in a `try/finally` that catches `BaseException` (`KeyboardInterrupt` writes `ABORTED`, G-07); if it still fails, it
  writes `run.final.<pid>.json` beside the record, and the `STATUS` line names that file. Earlier `<out
  root>/*/run.json` of the same `table_sha256` are read at step 0 into `earlier_runs`; each `IN_PROGRESS` or `ABORTED`
  one is printed. `run()` returns its exit code, 5 after `ABORTED` included, and never re-raises; the CLI maps the code
  to `SystemExit` (QA-R3-6).
- Sleep (OPS-R3-8): on Windows the runner calls `ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)`
  (`ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED`; the display flag guards a Modern Standby laptop,
  UNVERIFIED; OPS-R4-5) at step 0 and `SetThreadExecutionState(0x80000000)` after the final record. Windows drops the
  request when the process exits, so nothing needs restoring and no admin right is needed (UNVERIFIED here: no Windows
  host). `ctypes` is banned in the sandbox only (rule F1), and T-RO-01's `FORBIDDEN_IMPORTS` lacks it
  (`tests/macro_m0_harness.py:38-42`).
- Re-runs (OPS-R2-7): a run is refused (R-17) unless every earlier record of the table is `IN_PROGRESS`, `ABORTED`,
  `ERROR`, or `WITHHELD` for C-06 reasons only, or `--rerun-of <bridge_run_id> --reason "<text>"` is passed; the new
  record names that run in `supersedes`. The card of record is the latest `CARD_WRITTEN` card that no later record
  supersedes.
- Every refusal prints the offending items and section 7's remedy. Every mode's last console line is
  `STATUS <status> exit=<n> record=<path or ->`; an unexpected exception before registration prints its traceback tail
  and `STATUS REFUSED exit=2` (OPS-R2-6). Exit codes: 0 card written, a clean rehearsal or a mode's success; 1 WITHHELD;
  2 refused before registration, writing nothing to the repository or any ledger; 3 refused at registration; 4 ERROR;
  5 ABORTED.

### 5.4 `tools/nautilus/parity.py`

#### 5.4.1 Checks

Per column, at 1x and 2x unless the row says otherwise. Every hard failure withholds the verdict for the whole grid,
because CSCV and the DSR dispersion need every column (map03 §3.3). Reports print the owner's original bars next to
the corrected ones. `c_leg = cost_bps x stress / 1e4` is defined once and used in P7 and P10; P6 excludes bar T-1,
and P7 covers every fill. `L1-n` and `L2-n` are the tests of 8.3 and 8.4.

| ID | Check | Owner bar | Corrected bar | Kind | Control |
|---|---|---|---|---|---|
| P0 | Input provenance (QUANT-1). P0a: dates, rounded closes and rf equal the study's loaders byte for byte (5.3.2 step 7). P0b, after registration: the benchmark `P[1:] / P[:-1] - 1` from the rounded closes equals the study's expression (`docs/asset_expansion_study.py:275, 334`) on the study's rounded prices, byte for byte | none | equal | hard (P0a refuses, R-13; P0b withholds) | L1-20 |
| P1 | Decision agreement on decision bars: QUANTGEN's `W[t] > 0` against the child's logged decision | >= 98% | = 100%, except a decision whose QUANTGEN margin is below 1e-9 relative; each exemption listed | hard | L1-2 (N2; planted margins) |
| P2 | Pearson correlation of `R` and `pnl` over all T-1 rows | >= 0.99 | >= 0.9999 | hard | L1-2 (N2) |
| P3 | abs(`validate.sharpe(R)` - `validate.sharpe(pnl)`) (`core/quant/validate.py:137-143`) | <= 0.05 | <= 0.01 | hard | L1-2 (N7) |
| P4 | Bars with a fill, excluding bar T-1, equal `{t < T-1 : abs(Δw(t)) > 0}` | none | equal | hard | L1-2 (N2) |
| P5 | max abs(fill price / close - 1) | none | <= 1e-6 | warning | L1-2 (planted warning) |
| P6 | Turnover ratio: sum of `TV` over sum of abs(Δw) | none | in [0.99, 1.005] | warning | L1-2 |
| P7 | Commission recomputed in the parent (QUANT-5, QUANT-R2-3): per fill, `expected = last_qty x last_px x Decimal(cost_bps) x Decimal(s) / 10000`, with `cost_bps` from the table and `s` the leg's nominal stress (1 or 2) from the runner's own loop, never from `input.json` or the child; `input.json` and the manifest must echo both values | none | per fill `Decimal(commission) * 100 == cents(expected)` and `commission_ccy == "USD"`, so the totals are equal | hard | L1-2 (N7; the 0.125 tie) |
| P8 | abs(MDD(R) - MDD(pnl)) on compounded curves | none | <= 0.005 | warning | L1-2 |
| P9 | Tracking error, std(R - pnl, ddof=1) x sqrt(252) | none | <= 0.001 | warning | L1-2 |
| P10 | Daily gap, per row (QUANT-9) | none | abs(R - pnl) <= (c_leg/(1 + c_leg) + P(t)/E-(t)) (abs(r) + c_leg) + rf(t) + 1e-9, with r = r(t+1) | warning | L1-2 (F1) |
| P11 | Nautilus's own selection: `walk_forward` on `pnl_nt`; per origin its chosen column against `wf_qg.chosen`, with the QUANTGEN in-sample Sharpe gap of each mismatch (QUANT-3) | none | reported | diagnostic, never withholds | L1-2 (N4) |
| P12 | P2 and P3 on the selection-matched OOS series: `wf_qg.pnl` against `wf_nt.pnl`, and `pnl_stress` likewise (5.4.2) | none | as P2 and P3 | hard | L1-2 (N7 at 2x) |
| P13 | Completeness: the child's checks and the parent's re-derivation of C-01 to C-04 and C-15 (5.2.7), the census, the reconciliation (5.3.3), the input SHA-256 and the ledger-hash echo | none | all pass | hard | L1-27 |

P1's QUANTGEN margin is computed in the parent from QUANTGEN's own arrays (QA-19): `sma`, `abs(P[i] - S._sma(P,
L)[i]) / P[i]` with QUANTGEN's cumulative-sum SMA (`core/quant/strategies.py:111-116`); `tsmom`, `abs(P[i] / P[i-L] -
1.0)`; `crypto_trend`, the smallest `abs(P[i] - ref) / P[i]` over the votes, `ref` from `S._sma`. The exemption covers a
floating-point tie between a cumulative-sum SMA and a plain mean (map03 §3.4); none occurred in 12 x 2,497 bars. P7's
`cents(x) = int(Decimal(float(x) * 100.0).quantize(Decimal(1), rounding=ROUND_HALF_UP))` is how `Money` rounds
(QA-R2-7): it converts the value to a double (`nt:model/objects.pyx:1190, 1205`) and rounds half away from zero. It
matched `Money` on 400,005 values, ties included, in high precision (`scratch:rev3_probe/money_probe.py`); standard
precision is UNVERIFIED until Step 7A. Tie control: 25 at 1.00, 50 bp, 1x gives 0.125, which `Money` rounds to 0.13.
Warnings never withhold; they go into the run record and the card.

#### 5.4.2 Selection: QUANTGEN's choice on both matrices (QUANT-3)

`wf_qg = walk_forward(pnl_qg, dates, turnover=turnover_qg, pnl_stress=pnl_stress_qg, embargo=E)`
(`core/quant/validate.py:345-381`). `wf_nt = select_matched(pnl_nt, pnl_stress_nt, turnover_nt, dates, wf_qg,
embargo=E)`, in `tools/nautilus/parity.py`: for each k, `o = wf_qg.origins[k]`, `g = wf_qg.chosen[k]` and `a, b = o + E,
min(o + E + GATE["w_oos"], T)`, as `walk_forward` slices (`:373-375`); it concatenates `dates[a:b]`, `M[a:b, g]`,
`Ms[a:b, g]` and `To[a:b, g]`, and sets `is_sharpes[k] = validate._col_sharpe(M[max(0, o - GATE["w_is"]):o])`
(`:268-270`, a private helper used read-only); `origins`, `chosen` and `note` come from `wf_qg`, `n_configs = G`. It
returns `validate.WalkForward(...)`, a frozen dataclass built directly (`:332-342`); no gate code changes. Its test
(L1-21): on QUANTGEN's own matrices it reproduces `wf_qg` field by field, bit for bit.

The card is written from `wf_nt`: Nautilus P&L under QUANTGEN's deterministic tie-break (`np.nanargmax`, `:373`),
because exact in-sample ties are routine: on three synthetic SPY-like seeds with the pilot-1 grid they occurred at 5, 12
and 2 of 38 origins, and random tie-breaks moved `sr_oos` by up to 0.047, five times the P3 bar, with every hard check
passing (`scratch:referee_quant/tie_probe_fast.py`); map 03's pre-2004 columns 4, 5 and 9 tie at origins 1512 and 1638
(K3). P11 reports Nautilus's own selection and never withholds.

#### 5.4.3 Evidence for the bars

| Evidence (high precision) | Data | Result | Source | Evidence (high precision) | Data | Result | Source |
|---|---|---|---|---|---|---|---|
| Real SPY `sma/210/21`, $1M, 9 dp, CASH, fee-inclusive sizing | 1995-01-03 to 2004-11-30, 2,497 sessions | agreement 109/109; corr 0.99999995; ΔSR -0.00006 (1x), +0.00013 (2x) | map03 §4.2 | All 12 settings x 1x and 2x | same | min corr 0.99999901; max abs ΔSR 0.0013; agreement 100%; max daily gap 3.80 bp | map03 §4.3 |
| Walk-forward selection | same, embargo 21 | the same column at all 14 origins; OOS corr 0.99999996; ΔSR +0.00004 (1x), +0.00036 (2x) | map03 §4.4 | Crypto trend, 5 hysteresis values, 10 and 20 bp | 1,500 synthetic days | agreement 100% on 1,300 decisions; min corr 0.99999984; max abs ΔSR 0.0003 | map03 §4.5 |
| F1, F2 and N1; the 5.2.9 skeleton, filled, under `unshare -rn` | hand-built | fills, commissions and final cash match hand arithmetic to the cent; N1 as 8.2, its reasons C-01 and C-02 re-derived from the manifest; both self-checks behave; exit 20 for 63 single-field perturbations of 6.1 (QA-R3-4), a non-JSON and a linked `input.json`; one census for all three (942 names) | map03 §6; `scratch:rev4_probe/sandbox_r4.py`, `drive.py`, `drive.out` | Failure modes | pre-2004 SPY | 2 dp: TE 0.085%/yr, passes; thin volume: run stopped at bar 211; 1-session latency: corr 0.98295, ΔSR -0.098, fails | map03 §4.2 |

How loose the owner's bars are (synth §7.3, 109 single-block flips on `sma/210/21` at 50 bp): corr < 0.99 catches
27.5% of flips and abs ΔSR > 0.05 catches 16.5% (63% pass both), while corr < 0.9999 catches 100%; a 2x engine that
charges 1x gives corr 0.9991047 and abs ΔSR 0.04958 and passes both owner bars. The corrected P2 keeps a 100x margin
over the worst measured 1 - ρ of 1e-6, and P3 a 7.7x margin over the worst measured 0.0013. P7 now catches a wrong rate
directly: on BTC-like series a "2x charged at 1x" bug moved Sharpe by only 0.006 to 0.008 at hysteresis 0.889, inside
the P3 bar (`scratch:referee_quant/cost_gap_probe.py`). No parity number exists for the pilot windows, by design. N6
tests pilot-like prices on synthetic data; real margins stay UNVERIFIED until the registered run, and in standard
precision until Step 7A.

### 5.5 Gate hand-off (QUANT-2, GOVERNANCE-6, C-3)

Steps 1 and 2 also serve P12 and P0b; steps 3 to 9 run only when every hard check of 5.4.1 passes, at both cost levels,
for every column (QUANT-R4-3):

| Step | Action | Step | Action |
|---|---|---|---|
| 1 Walk-forwards | `wf_qg` and `wf_nt` as 5.4.2. | 2 Benchmark | `bench = P[1:] / P[:-1] - 1` (one column), aligned with `wf_qg.dates` as the study does (`docs/asset_expansion_study.py:186-190`), uncosted; P0b has checked it. |
| 3 Trial counts (QUANT-4) | `len_grid`; `family_n_raw` after registration; `market_n_raw` (rows whose `market` equals the table's); `U`, the number of `study_configs` (6.6) whose `config_id`, computed with `gate_ledger.config_id` from a row built as 6.4 builds one, is absent from the family ledger after registration; `n_trials = family_n_raw + U`. All printed and stored. | 4 Score both | `sc_qg = score_fn(wf_qg, grid=grid, full_pnl=pnl_qg, n_trials=n_trials, bench_daily=bench, seed=11, domain=<table domain or None>)`, and `sc_nt` likewise from `wf_nt` and `pnl_nt` (`core/quant/validate.py:492-533`). Pilot 2 passes `domain={"hysteresis": (0.0, 0.889)}` (`docs/asset_expansion_study.py:339`). |
| 5 Agreement, reference | `parity.gate_predicates(score, gate) -> dict[str, bool]` recomputes, from the GATE snapshot, exactly the predicates `_decide_strategy` reads (`core/quant/validate.py:536-622`; QUANT-R2-2): `ci_pos`, `dsr_ok`, `dsr_finite`, `pbo_meaningful` (`n_configs >= pbo_min_configs`), `flat` (`prob_loss_oos <= prob_loss_max`), `pbo_ok` and `pbo_reject` as `:576-577` compute them (below 8 configurations raw PBO is never read), `oos_is_ok`, `stress_ok`, `years_ok`, `plateau_ok`, `sample_ok`, `floor_ok`, `n_years_ok`, `sessions_ok`, `mtr_ok` (`n_sessions >= min_track_record(sr_oos, ci_level)`, `:156, 584`), `has_bench` (`isfinite(bench_p)`, `:557`) and `bench_ok`. `parity.agree(sc_qg, sc_nt, gate)` allows a card only if both scores have `has_bench` (both pilots name a benchmark; else WITHHELD "benchmark test dropped"), equal decisions and equal predicate dicts; otherwise WITHHELD "decision mismatch" (G-02). G-08 applies whenever the table's `reference_card` is not null; of-record mode requires it for `C3-BTCUSD` (QUANT-R2-5, QUANT-R3-1, QUANT-R3-3, QUANT-R4-2). `parity.reference_drift(sc_qg, wf_qg, grid, ref)` lists every field where `sc_qg` fails to reproduce `ref`, the stats of the table's md5-pinned `reference_card` (pilot 2: `S_C3_crypto_trend_btcusd`): `chosen_last` as `grid[wf_qg.chosen[-1]] == ref["chosen_last"]`, `n_trades` and `n_sessions` exactly; the card's `n_years` against `len({d[:4] for d in wf_qg.dates})`, the calendar-years rule that wrote it, with today's whole-year `sc_qg.n_years` (`core/quant/validate.py:421-437`) recorded beside it; `sr_oos`, `ci90`, `oos_is`, `sr_stress`, `years_positive`, `plateau`, `pbo` and `prob_loss_oos` within 1e-9 (absolute); `bench_p` within 1/2000, one bootstrap draw. It never compares `lines`, `reason` or `revise_target` text, whose wording changed. A non-empty list gives WITHHELD "reference drift" (G-08). Both scores, both predicate dicts and the comparison go into the run record. | 6 GATE | Assert `validate.GATE == gate_snapshot` (G-04). |
| 7 Ledger | `assert_hash_at_run(ledger, hash_after_registration)` (`core/quant/gate_ledger.py:389-396`); a raise means the ledger moved after registration: no card, WITHHELD (G-05). | 8 Card | `card.to_json()` of the card of 6.5, written by the bridge to `<run folder>/<card_id>.json` through `open(path, "x", encoding="utf-8", newline="\n")`; never `ModelCard.save`, which overwrites and writes platform newlines (`:830-834`; OPS-12), and never into `docs/asset_expansion/cards/`. |
| 9 Record | The final run record with the card's path and md5; status `CARD_WRITTEN` (QA-9). |  |  |

A WITHHELD result writes one run record and no card. WITHHELD is never a card decision, because the scorecard knows
only `validate.DECISIONS` (`core/quant/validate.py:50`).

### 5.6 T-RO-01 amendment (`tests/macro_m0_harness.py`)

Rationale, to be quoted in the tests' docstrings: orders in a Nautilus backtest fill against a simulated exchange
inside one process, as QUANTGEN's paper fills pass through `OrderBook.fill` (`core/engine/orders.py:90, 169,
253-257`). The amendment lets exactly one file place such orders, through exactly one call, and closes two holes of
today's scan: it compares only the first dotted component of an import (`tests/macro_m0_harness.py:90-96`), and it
misses seven Nautilus order verbs (map04 §3.2). It is the first exemption for a forbidden token or call in T-RO-01's
history (GOVERNANCE-10): the 2026-10-23 spec widened the scan to `tools/` and `papers/` and allowed one importer, but
exempted no forbidden token (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:177-181`).
After it, a T-RO-01 PASS means "no order path outside the one sandbox call". The council spec is not edited.

Constants, inserted after `ALLOWED_BARE_CALLS` (`tests/macro_m0_harness.py:56`):

```python
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
```

`FORBIDDEN_CALLS` (`tests/macro_m0_harness.py:44-50`) gains the 7 `NAUTILUS_ORDER_VERBS`, forbidden in every file,
the sandbox included (rule B). Rules added to `_offences`: every new hit starts with `[nautilus:<rule>]`, each rule adds
at most one hit per AST node it inspects, and existing hits keep their form. Imports are judged by full dotted name:
`import a.b.c` names `a.b.c`; `from m import n` names `m` and `m.n`; relative imports resolve against the file's
package. "Denied name" means in `NAUTILUS_DENIED_NAMES` (`NAUTILUS_BRIDGE_ONLY_NAMES` only under `tools/nautilus/`, as
`data/fmp/quote_client.py:110, 115` use `api_key`) or matching `NAUTILUS_DENIED_NAME_RE`.

| Rule | Where | Offence |
|---|---|---|
| A (SECURITY-7) | sandbox | Collect every AST node whose identifier contains `submit_order` in lower case (`Name.id`, `Attribute.attr`, function and class names, `arg.arg`, `keyword.arg`, import aliases) and every string constant containing it. Exempt only when exactly one node is collected, it is `Attribute(attr="submit_order")` on `Name(id="self")`, it is the `func` of an `ast.Call`, and its enclosing function is a method (a `FunctionDef` directly in a `ClassDef` body): then the `'submit_order'` text hit and that call's `.submit_order()` hit are dropped. Otherwise every hit stands, plus one `A` hit. |
| C1 | every file | an import name equal to a `NAUTILUS_DENIED_PREFIXES` entry or starting with it plus `.`; an imported name or alias that is a denied name |
| C2 | every file but the sandbox | an import name equal to or under `nautilus_trader` |
| C3 | sandbox | `import m` unless `SANDBOX_STDLIB[m] is None`; `from m import n` unless n is in `NAUTILUS_ALLOWED_FROM[m]` or in the set `SANDBOX_STDLIB[m]`; any `as` alias; any relative import. The existing first-component check against `FORBIDDEN_IMPORTS` stays. |
| D (SECURITY-6) | every file | a `Name.id`, `Attribute.attr`, `arg.arg` or `keyword.arg` that is a denied name. Today's 154 scanned files give 0 hits. |
| E (K4) | every file | a call whose callee (`Name.id` or `Attribute.attr`) is in `IMPORT_MACHINERY`: outside the sandbox when a string constant inside it contains `nautilus`, in the sandbox always; and, in the sandbox only, any string constant containing a `NAUTILUS_DENIED_PREFIXES` or `NAUTILUS_DENIED_NAMES` entry. Other strings are not checked, so the runner may name `nautilus_trader.adapters` in a `startswith` check. |
| F1 (SECURITY-1) | sandbox | an import whose top-level module is in `SANDBOX_BANNED_MODULES`, except `from sys import` names in `SANDBOX_STDLIB["sys"]` |
| F2 | sandbox | any `Name` in `SANDBOX_BANNED_NAMES`, called or not |
| F3 | sandbox | any `Attribute` whose attr starts with `__` |
| F4 (SECURITY-R2-1) | sandbox | any `Subscript` whose value is a `Name` bound by `ast.Import` (a module alias), or an `Attribute` chain rooted at one; never a name bound by `from ... import` |
| F5 (SECURITY-3) | sandbox | any call `X.<m>(...)` with `m` in `SANDBOX_FILE_METHODS` whose receiver `X` is not a call to `Name("inside")` |
| F6 | sandbox | any call whose callee is in `SANDBOX_OS_CALLS` |

Rule E is fail-closed against the sandbox's own text: maintainers keep its diagnostics free of every denied prefix and
name, so no error message names, say, `nautilus_pyo3` (SECURITY-R3-2).

Two new tests after `tests/macro_m0_harness.py:192`, both with `test_ids = ["T-RO-01"]`:
- `test_t_ro_01_nautilus_confined_to_the_sandbox` builds a temp tree in the pattern of
  `test_t_ro_01_scan_reaches_tools_and_papers` (`tests/macro_m0_harness.py:175-192`) and asserts the controls of 8.5.
  It also asserts that the real `tools/nautilus/sandbox.py` exists and gives no hit (QA-12).
- `test_t_ro_01_nautilus_allowlist_pinned` (SECURITY-5). `_canon(x)` maps a dict to a dict of canonical values, and a
  set, frozenset, tuple or list to the sorted list of its canonical items; other values stay. The digest is
  `sha256(json.dumps(_canon(obj), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()`. The dict of the
  allow-list `{NAUTILUS_SANDBOX, NAUTILUS_ALLOWED_FROM, NAUTILUS_DENIED_PREFIXES, NAUTILUS_DENIED_NAMES,
  SANDBOX_STDLIB}`, keyed by those names, must give `2792ad4af44c6af599092f81594a34d1f7d013cd17abf5882c8c6f72a042e49f`.
  The dict of the rule lists `{NAUTILUS_BRIDGE_ONLY_NAMES, NAUTILUS_DENIED_NAME_RE (its .pattern),
  NAUTILUS_ORDER_VERBS, IMPORT_MACHINERY, SANDBOX_BANNED_MODULES, SANDBOX_BANNED_NAMES, SANDBOX_FILE_METHODS,
  SANDBOX_OS_CALLS}` must give `70bcf50fbce5637a1854413618b6b9827c04dc10a59a0a25d274b4be1941da6c`. Both carry the
  comment "a change needs an owner ruling recorded in spec 2026-10-26 §5.6"; both were computed from the constants
  above in `scratch:rev2_probe/scan/scan_proto.py` and again in `scratch:rev3_probe/scan3.py` and
  `scratch:rev4_probe/scan4.py`.

`tests/acceptance.py::runtime_py()` is not extended; `tools/` is outside test_08 and test_09
(`tests/acceptance.py:50-75`), which stay unchanged and must keep passing.

### 5.7 The `nautilus` suite in `tests/run_all.py`

- New module `tests/nautilus_acceptance.py` with `def tests() -> list[(name, fn)]`; every test is wrapped by the guard
  of 3.3. `tests/run_all.py` gains `nautilus_tests()`, a copy of `papers_tests` (`tests/run_all.py:57-71`) for this
  module: it imports `tests.nautilus_acceptance` lazily, and an import failure becomes one FAIL row named `import`
  that never stops the other suites. `tests()` gains `[(f"nautilus/{n}", f) for n, f in nautilus_tests()]` last; the
  `--suite` help (`tests/run_all.py:131`) gains `nautilus`. The file is CRLF: Edit tool only.
- Layer-1 tests always run. Layer-2 tests raise `NotRun("OWNER: Nautilus venv not configured
  (QUANTGEN_NAUTILUS_PYTHON)")` when the key is blank, and `NotRun(f"OWNER: QUANTGEN_NAUTILUS_PYTHON points to a
  missing file: {value!r}")` when the resolved path does not exist (OPS-R3-9). A venv off its pins is a FAIL (O15).
- On Windows the module holds `ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)` (`ES_CONTINUOUS |
  ES_SYSTEM_REQUIRED`) while its layer-2 tests run and calls `SetThreadExecutionState(0x80000000)` in a `finally`
  after them, because only runs that go through `run()` hold the runner's request (5.3.5), and the Step 7A suite starts
  more than 100 children (OPS-R5-5).

### 5.8 Registry rows, README and the file table

`tests/macro_registry.csv:12` (T-RO-01): `implemented_in` gains both tests of 5.6, written by
`python -m tests.macro_acceptance` (`README.md:855`); `test_registry_implemented_in_matches_test_ids` fails until then
(`tests/macro_m0_harness.py:286-295`); no other registry row changes. README (C-4, CRLF, Edit tool only): at Step 4 the
cloud build adds `nautilus` to the `--suite` help line (`README.md:853`) and the row `| nautilus |
tests/nautilus_acceptance.py | <what it covers> | counted at the Windows run of record |`, leaving the Total row
unchanged; at Step 10 the owner's Windows full run fills that row and the Total row (`README.md:864-878`).

| File | Change | Step |
|---|---|---|
| `requirements-nautilus.txt`; `.env.example` (heading and the line of 3.4) | new, LF; edit | 3 |
| `tools/nautilus/__init__.py` (empty), `egress_probe.py`, `launch.py` (4.3, 5.2.7, 6.7; QA-R2-5; `fixture_inputs`, QA-R3-1) | new | 3; `fixture_inputs` 5 |
| `tools/nautilus/sandbox.py` | new; the only order-placing file | 3 (`--check-env`, `--guard-selftest`), 5 |
| `tools/nautilus/runner.py`; `tools/nautilus/parity.py` | new | 6; 7 |
| `tools/nautilus/golden/env_pins.json` | new; both platforms, computed offline (6.7) | 3 |
| `tools/nautilus/golden/F1.json`, `F2.json`, `N1.json`, `modules_<tag>.json` | new (6.8) | 6 (Linux), 7A (Windows census) |
| `tests/fixtures/nautilus/` | both wheels' `RECORD` files and a `MANIFEST.csv` with their md5s (6.7; QA-R2-14) | 3 |
| `tests/nautilus_stub_child.py` | the layer-1 stub child (8.1; QA-R2-2) | 6 |
| `tests/macro_m0_harness.py`; `tests/macro_registry.csv` | constants, rules A-F, two tests; row 12 resync | 4 |
| `tests/nautilus_acceptance.py` | new suite | 4 to 7 |
| `tests/run_all.py` | `nautilus_tests()`, `tests()`, `--suite` help (CRLF) | 4 |
| `docs/nautilus_bridge/.gitignore` | `runs/.locks/` | 3 |
| `docs/nautilus_bridge/RUNBOOK_windows.md` | the Step 7A commands of section 9, in PowerShell, with the pinned 3.13 patch of the base interpreter (OPS-R4-5) | 7 |
| `docs/nautilus_bridge/registration/pilot1_E1_spy.json`, `pilot2_C3_btcusd.json` | new tables (6.6) | 7; owner fields at 7A |
| `docs/nautilus_bridge/egress/<tag>.json`, `handoff/<tag>.json` | egress record; hand-off report (OPS-8) | 7A |
| `docs/nautilus_bridge/runs/<bridge_run_id>/` | outputs of record | 8, 9 |
| `README.md` | suite help and `nautilus` row (C-4) | 4, 10 |

Unchanged on purpose: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `config.py`, `core/quant/*.py`,
`ui/strategy_lab_page.py`, `tests/acceptance.py`, `paper_live/`, `grokteam/`, `docs/asset_expansion/` and
`docs/asset_expansion_study.py`.

## 6. Data model

### 6.1 `input.json` (parent to child; QA-4, QA-6)

The child accepts any value in range and refuses everything else, unknown and missing fields included, with exit 20.
The runner, not the child, asserts a registration table's pilot values (5.3.2 step 1).

| Field | Type | Child accepts | Pilot value |
|---|---|---|---|
| `schema` | str | `"nautilus-bridge-input/2"` | |
| `strategy` | str | `"trend_switch"` or `"crypto_trend"` | |
| `params` | object | trend: `rule` in {`sma`, `tsmom`}, `lookback` and `step` int 1..5000; crypto: `hysteresis` float in [0, 1), `lookbacks` and `mas` lists of 1 to 16 ints 1..5000 | the grid column |
| `instrument` | str | `"SPY"` or `"BTC/USD"` | |
| `capital_usd`, `cost_bps` | str | integer string 1 to `PRICE_MAX`, which equals `MONEY_MAX` in both precisions (3.6; QA-R2-8); decimal string 0 to 1000 | `"1000000"`; the table's rate |
| `stress`, `fill_seed` | str, int | `"1"` or `"2"`; 0 to 2**32 - 1 | 42 |
| `price_precision`, `size_precision` | int | each 0 to `FIXED_PRECISION` | 9; 0 (SPY) or 8 (BTC) |
| `volume` | str | integer string, 1 to `QUANTITY_MAX` | `"1000000000"` |
| `n_bars`, `bars_sha256` | int, str | 1 to 100,000, the rows of `bars.csv`; 64 lower-case hex, the SHA-256 of its bytes | |
| `ledger_hash_after_registration` | str | 32 lower-case hex | the hash of 5.3.2 step 12 |

`bars.csv`: header `i,ts_ns,close`, LF, one row per bar, `i` counting from 0, `ts_ns` strictly increasing, `close`
above zero with exactly `price_precision` decimals. The ledger
hash cannot exist before registration, so a child that echoes it was launched after registration (QA-6). Fixtures,
which register nothing, pass `gate_ledger.ledger_hash([])`, the hash of an empty ledger.

### 6.2 `manifest.json` (child)

| Field | Content | Field | Content |
|---|---|---|---|
| `schema`, `read_only`, `mode` | `"nautilus-bridge-manifest/2"`, `true` (map04 R22), `"run"` | `python`, `system`, `machine` | `platform.python_version()`; `platform.uname()` (5.2.1) |
| `precision` | `HIGH_PRECISION`, `FIXED_PRECISION`, `QUANTITY_MAX`, `PRICE_MAX` | `environment`, `strategy_started` | `engine.kernel.environment.name`; whether the port passed its `on_start` guard |
| `input` | `input_json_sha256`, `bars_sha256`, `bars_fed`, `first_ts`, `last_ts`, and echoes of `cost_bps`, `stress` and `ledger_hash_after_registration` | `engine` | `run_analysis` false, `log_level` "ERROR", `log_colors` false, `account_type` "CASH", `oms_type` "NETTING", `allow_cash_borrowing` false, `bar_execution` true, `fill_seed` 42 |
| `result` | `bars_seen`, `iterations`, `backtest_end` (int ns or null), `force_stop`, `orders_total`, `orders_filled`, `denied`, `rejected`, `orders_not_filled` (ids), `account_balance_usd` (`f"{balance.as_decimal():.2f}"`; QA-R2-6), `final_qty` (str), `stats_pnls_empty` (`get_result().stats_pnls` is empty: a witness that the analyzer did not run, QA-12) | `hashes` | SHA-256 of `fills.csv`, `decisions.csv`, `onbar_equity.csv` |
| `valid`, `invalid_reasons` | the child's own verdict (5.2.7); each reason begins with its section-7 id (QA-R3-8) |  |  |

No field holds a time of day. Versions, the wheel identity and the census come from the parent (6.7, 5.2.7).

### 6.3 Run record (`docs/nautilus_bridge/runs/<bridge_run_id>/run.json`)

| Field | Content | Field | Content |
|---|---|---|---|
| `schema`, `read_only` | `"nautilus-bridge-run/2"`, `true` | `bridge_run_id`, `mode`, `pilot`, `stub_child` | 5.3.5; `rehearsal` or `of-record`; `E1-SPY`, `C3-BTCUSD` or `rehearsal`; bool |
| `status`, `withheld_reasons` | `IN_PROGRESS`, `CARD_WRITTEN`, `WITHHELD`, `REFUSED_REGISTRATION`, `ERROR` or `ABORTED`; failed check ids and messages, `"decision mismatch"`, `"benchmark test dropped"`, `"reference drift"` or `"ledger moved after registration"` | `earlier_runs`, `supersedes`, `rerun_reason` | `{bridge_run_id, status}` of earlier records of the same table, read at step 0 (`UNREADABLE` when unreadable); 5.3.5 |
| `times` | `started_utc`, `registered_utc`, `first_child_utc`, `finished_utc`, ISO UTC with microseconds | `git`, `table` | `head`, `anchor`, `clean`, `porcelain_exempt`; path, `raw_sha256` of its bytes, `table_sha256` and `code_sha256` (6.6; GOVERNANCE-R4-4) and the full table (OPS-R3-5) |
| `data`, `provenance` | `prices_file`, `prices_md5`, `rf_file`, `rf_md5` or null, `start`, `end`, `sessions`, `rounding_changed`; the P0a and P0b results | `costs` | `cost_bps`, `floor_bp`, `classes`, `stress` (2.0), `source` (`"validate.cost_floor_bp"`) |
| `venv`, `egress`, `engine` | 6.7's reads; the parent's `pyarrow` version or null, `sys.executable`, `sys._base_executable` and `sys.version` (OPS-R2-2); the probe JSON, layer and record path, raw and normalised (4.3); the `--check-env` and `--guard-selftest` JSON | `registration` | `family_id`, `ledger_path`, `hash_before`, `hash_after`, `n_raw_before`, `n_raw_after`, `market_n_raw`, `rows`: `{col, config_id, row_md5, appended}` |
| `children` | per child: `col`, `stress`, `returncode` (with NTSTATUS hex), `seconds`, `manifest`, `census_sha256`, `fills` (all rows), `stdout_tail`, `stderr_tail` (census lines removed) | `census` | platform tag to the one sorted census, identical for every valid child |
| `parity` | per column and cost level: P0b to P10 and P13 values and flags; P11 per origin; P12 at 1x and 2x; `owner_bars`; `hard_pass`; `failed` | `gate` | `trial_counts` {`len_grid`, `family_n_raw`, `market_n_raw`, `U`, `n_trials`}; `quantgen` and `nautilus`, each {`decision`, `reason`, `revise_target`, `predicates`, `stats`}; `agree`; `reference` (G-08, whenever `reference_card` is set: the drift list, both year counts); `selection` |
| `card`, `cleanup_leftovers`, `record_write_failures` | `path` and the md5 of the bytes on disk, or null; 4.3; 5.3.5 |  |  |

Fills are kept in full; daily returns are not stored, because 5.3.3 rebuilds them exactly from the fills and the
md5-pinned closes and cash rate. Card md5s are never compared across platforms (OPS-12).

### 6.4 Ledger row fields used

| Field | Pilot value | In `config_id`? |
|---|---|---|
| `rule` | `"E1"` or `"C3"` (`ui/strategy_lab_page.py:50`) | yes |
| `params` | `json.loads(json.dumps(dict(theta, symbols=sorted(symbols), cost_bps=float(cost_bps)), default=str))`, the Lab's exact expression (`ui/strategy_lab_page.py:75-76`) | yes |
| `timing_class` | `"COMPLIANT"` | yes |
| `estimator`, `window`, `cap`, `instrument_book`, `rebalance`, `start_convention` | not set (null), as the Lab | yes |
| `span`, `market`, `run_utc` | `[first, last panel date]`; `"US"` or `"CRYPTO"` (`ui/strategy_lab_page.py:52`); registration time `%Y-%m-%dT%H:%M:%SZ` | no |
| `phase`, `script`, `run_kind`, `run_utc_anchor` | `"research"`, `"tools/nautilus/runner.py"`, `"variant"`, `repo_anchor()` | no |
| `source` | `"nautilus-bridge <pilot>; engines quantgen.simulate + nautilus_trader 1.231.0; run <bridge_run_id>"` | no |
| `cost`, `results_md5`, `diff_series_ref`, `card_id`, `delta_sr` | not set | no |

The key is `md5(canonical_json({rule, params, estimator, window, cap, instrument_book, rebalance, timing_class,
start_convention}))` (`core/quant/gate_ledger.py:60-61, 168-171`). `canonical_json` writes floats by `repr`, so `50.0`
and `50` hash differently (`core/ficc/macro_schema.py:303-305`; K9): `cost_bps` is always a Python float. The engine
tag sits in `source`, outside the key, so one variant is one trial whichever engine ran it; a duplicate returns the
first row and drops the new `source` (`core/quant/gate_ledger.py:343-346`). The 2x leg is never a row; it is the gate's
stress column (`core/quant/strategies.py:387`).

### 6.5 Card fields (`validate.ModelCard`, `core/quant/validate.py:802-834`)

| Field | Bridge value | Field | Bridge value |
|---|---|---|---|
| `card_id`, `kind` | `NB_E1_trend_spy` or `NB_C3_crypto_trend_btcusd`; `"strategy"` | `hypothesis` | the table's `claim_label`, a colon, then the table's hypothesis |
| `rules` | `family`, `grid`, `cost_bps_per_side`, `embargo`; `engine` = `"per-column event-driven replication (nautilus_trader 1.231.0 BacktestEngine, same-bar close); walk-forward column switches are not executed in either engine"` (QUANT-11); `selection` = `"QUANTGEN walk-forward selection (wf_qg.origins, wf_qg.chosen) applied to both engines' matrices"`; `claim_label` (QUANT-6); `parity_scope` = `"parity validates the engine, not the data; P0 ties the inputs to the study's loaders"` (QUANT-1); `parity_bars` = `"corrected, spec 2026-10-26 §5.4"` | `universe`, `data`, `costs` | `symbols`, `venue`; `sessions`, `start`, `end`, `source`, `prices_md5`, `rf_md5`; `cost_bps`, `stress_multiplier` (2.0) |
| `protocol` | GATE's `w_is`, `w_oos`, `min_is`, `ci_level`, `bootstrap_B`, `block` | `trials` | `N_planned` (= `len_grid`), `N_total` (= `n_trials`), `family_id`, `family_n_raw`, `market_n_raw`, `U`, `study_configs_absent`, `config_ids`, `row_md5s`, `ledger_hash_at_run`, `ledger` (free text) |
| `seed`, `tests` | 11; `dsr`, `pbo`, `ci90`, `sr_stress` | `stats` | `asdict(sc_nt)` minus `lines` and `regime`, plus `regime`, `chosen_last`, `bench_sharpe`, `walk_forward`, `parity` (summary), and `quantgen_score` (`asdict(sc_qg)` minus `lines`): the card shows both (QUANT-2) |
| `decision`, `decision_reason`, `revise_target`, `lines` | from `sc_nt`, whose decision equals `sc_qg`'s (5.5 step 5); `decision` is always in `validate.DECISIONS` | `citations` | the study's citations |
| `results_file`, `results_md5` | the `bridge_run_id`; `""`. The run record holds the card's md5, not the reverse (QA-9). | `created`, `author` | defaults; `created` is a date and sits outside every hash |

### 6.6 Registration table (QA-4, QA-5, GOVERNANCE-3, QUANT-4, QUANT-6)

One JSON object, `schema` `"nautilus-bridge-table/1"`, read with `utf-8-sig`. Every field is required in both modes,
except the last two, which only of-record mode requires and `--fingerprint` treats as optional (GOVERNANCE-R4-1).

| Field | Type | Meaning | Field | Type | Meaning |
|---|---|---|---|---|---|
| `pilot` | str | `E1-SPY`, `C3-BTCUSD` or `rehearsal` | `family_id`, `rule`, `market` | str | `E1`/`C3`; the same; `US`/`CRYPTO` |
| `strategy`, `symbol`, `instrument` | str | `trend_switch`/`crypto_trend`; QUANTGEN symbol (`SPY`, `BTC-USD`); Nautilus instrument | `prices_file`, `prices_md5` | str | repo-relative path; in rehearsal absolute and inside the temp root (3.9); md5 of its bytes |
| `start`, `end` | str | ISO dates, inclusive; both filter the panel (5.3.2 step 5) | `rf_file`, `rf_md5` | str or null | DGS3MO for pilot 1; null for pilot 2 |
| `axes`, `grid` | object, list | `grid_from` keywords; the expanded grid | `cost_bps`, `embargo` | float, int |  |
| `capital_usd`, `price_precision`, `size_precision`, `volume`, `fill_seed` | str, int, int, str, int | of-record asserts `"1000000"`, 9, 0 or 8, `"1000000000"`, 42 | `domain` | object or null | pilot 2: `{"hysteresis": [0.0, 0.889]}` |
| `hypothesis`, `claim_label`, `card_id` | str | `claim_label` text is fixed by 10.1 and 10.2 | `study_configs` | list | each `{source, symbols, cost_bps, params}`: a configuration the study ran and never registered |
| `reference_card`, `reference_card_md5` | str or null | pilot 2: the stored card G-08 compares with, and the md5 of its bytes (10.2; QUANT-R3-3); in rehearsal, a temp card inside the temp root (QUANT-R4-1); null otherwise |  |  |  |
| `owner_confirmed` | str | `"<name>, <date>, table <16 hex>, code <16 hex>"`, the first 16 hex of `table_sha256` and `code_sha256` as `--fingerprint` prints them; written by the owner at Step 7A.3 (GOVERNANCE-R2-2) | `host_fingerprint` | str | `sha256((socket.gethostname() + "\n" + first_row["row_md5"]).encode("utf-8")).hexdigest()`, `first_row` the family ledger's first row; printed by `--fingerprint` |

`table_sha256` is the SHA-256 of `json.dumps(t, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` in UTF-8,
`t` the table without `owner_confirmed` and `host_fingerprint`; it names the table everywhere (5.3.5). `code_sha256`
is the SHA-256 of the sorted lines `"<path>,<sha256 of its bytes>"`, `<path>` being
`path.relative_to(repo_root).as_posix()` (OPS-R3-6), joined with `"\n"`, over `tools/nautilus/**/*.py`,
`tools/nautilus/golden/*.json`, `requirements-nautilus.txt`, the files of `core.quant.gate_package.HARNESS_SOURCES`,
imported so the list has one home (`core/quant/gate_package.py:36-38`), `docs/asset_expansion_study.py` and
`config.py` (GOVERNANCE-R3-1): an edit to the gate, the study or the ledger-dir rule needs a new `owner_confirmed`.
`.gitattributes` is `* -text`, so bytes and digests match across platforms. Of-record mode recomputes both digests and
refuses a mismatch with `owner_confirmed` (R-11).

### 6.7 Venv reads and the wheel identity (QA-10, OPS-4, OPS-7, OPS-13)

**The venv python.** Read `QUANTGEN_NAUTILUS_PYTHON` after `import config` loads `.env`, through `config._clean`
(`config.py:32-39`, a private helper used read-only); expand `~` and `%VAR%` or `$VAR` with
`os.path.expanduser(os.path.expandvars(v))`; refuse any control character (code below 32, or 127); require an absolute
path to an existing file named `python.exe` or `python`. Every refusal prints `repr(value)` and the fix (R-03).
**Venv files.** The root is the parent of `Scripts` (Windows) or `bin` (POSIX). From `<root>/pyvenv.cfg`: refuse
`include-system-site-packages = true`; record `home`, `version` and `executable`; on Windows refuse an `executable`
equal to the parent's `sys._base_executable` (4.4), and a `home` or `executable` under `WindowsApps` or
`\Packages\PythonSoftwareFoundation.`, with "this venv was made from the Microsoft Store python; recreate it with
`<py313>\python.exe -m venv ...`" (OPS-R2-2). Paths compare as 4.3 says. Versions come from
each `*.dist-info/METADATA`'s `Version:` line in `<root>/Lib/site-packages` or `<root>/lib/python3.13/site-packages`;
the full installed set is recorded.

**Wheel identity**, from `nautilus_trader-1.231.0.dist-info`: `wheel_tag` is the `Tag:` line of `WHEEL`, whose
platform part names the platform in file names. `record_digest_sha256`: parse `RECORD` with `csv.reader`; keep rows
with a non-empty hash, no `__pycache__` in the path, and a path not ending in `/RECORD`, `/INSTALLER`, `/REQUESTED` or
`/direct_url.json`; form `f"{path},{hash}"` with the hash field verbatim (`sha256=<base64>`); sort; join with `"\n"`,
no trailing newline; encode UTF-8; SHA-256 hex. `record_entries` is the number of kept lines. These entries equal the
wheel's own `RECORD`, so the expected values were computed offline from the wheel files (`scratch:closure/linux/`,
`scratch:closure/win/`):

| Platform tag | `record_digest_sha256` | Entries |
|---|---|---|
| `manylinux_2_35_x86_64` | `a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9` | 764 |
| `win_amd64` | `47d274d79b85a43b79917e9b993fa3e68ebf68138c4a8b86527c5902cf439555` | 764 |

The installed `RECORD` in two Linux venvs, a hash-pinned install from local wheels and a plain local-wheel install,
gives the same `a448cd20...`: the identity does not depend on the install method on Linux. On Windows that is
UNVERIFIED until Step 7A. `tools/nautilus/golden/env_pins.json` holds, per platform tag, `python_minor` (`"3.13"`),
`versions` (`nautilus_trader`, `numpy`, `pandas`), `wheel_tag`, `record_digest_sha256` and `record_entries`. Both
entries are committed at Step 3; Step 7A verifies the Windows one and never records it. Both wheels' `RECORD` files sit
in `tests/fixtures/nautilus/`, md5-listed in its `MANIFEST.csv` and read through `tests/notrun.py::require_fixture`
(`tests/notrun.py:68-80`), so layer 1 checks both digests on either platform (QA-R2-14).

### 6.8 Golden files (QA-2)

- `F1.json`, `F2.json`, `N1.json`: `{schema: "nautilus-bridge-golden/1", fixture, status ("valid" or "invalid"),
  exit_code, bars_fed, bars_seen, force_stop, fills: [{date, side, qty, price, commission}], final_cash, final_qty,
  invalid_reasons}`, with `date` the UTC date of `ts_event`. Integers and strings compare exactly; `price` exactly as
  the string at the instrument's precision (F1's `"100.000000000"`, not 8.2's display `100.00`); money (`commission`,
  `final_cash`) within 0.005; `invalid_reasons` by their leading ids (QA-R3-8). `runner --fixtures
  --write-goldens` writes them from 8.2's inputs on Linux, never over an existing file, and L1-33 checks them against
  8.2's tables (QA-R2-6).
- `modules_<platform tag>.json`: `{schema: "nautilus-bridge-census/1", platform_tag, python, recorded_from: ["F1",
  "F2"], census: [sorted names]}` (5.2.7).

## 7. Error handling

Every fail-closed condition, where it is caught, what is written, its negative control (QA-8) and the remedy the
runner prints (OPS-R2-6; "-": the run record is the answer). `L1-n` and `L2-n` are the tests of 8.3 and 8.4; a
"reason" says why no valid input reaches the condition.

| # | Condition | Caught by | Written; exit or status | Control | Remedy |
|---|---|---|---|---|---|
| R-01 | Tracked change, or an untracked path outside `docs/nautilus_bridge/runs/` (of-record) | 5.3.2 step 2 | nothing; 2 | L1-6 | commit or remove the printed paths |
| R-02 | Git missing, anchor UNVERSIONED (packed refs or worktree, named), or anchor sha differs from HEAD (of-record) | step 2 | nothing; 2 | L1-6 | packed ref: `git commit --allow-empty -m "nautilus: re-anchor"`, then `git push` (OPS-R3-9); worktree: use the main clone |
| R-03 | Venv key unset, malformed or missing; `pyvenv.cfg` checks, a Store-Python base included; versions, Python minor or wheel identity off the pins; the guard self-test misbehaved (QA-R2-10); `nautilus-trader` installed in the parent | step 3 | nothing; 2 | L1-17, L1-22, L1-27, L2-1 | the `.env` line of 3.4; `<py313>\python.exe -m venv` and the offline install (5.1); for the parent exactly three lines (OPS-R3-1): `python -m pip uninstall -y nautilus-trader`, `python -m pip check`, and `python -c "import numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, scipy.__version__)"`, which must print `2.3.5 2.3.3 1.18.0`; other closure packages are reported, never uninstalled; if `pip check` or a version is off: stop, an owner ruling |
| R-04 | Price file missing, unreadable, or md5 differs | step 5 | nothing; 2 | L1-7 | restore the pinned bytes; new bytes need an owner ruling |
| R-05 | Panel under 300 rows, unsorted or duplicated dates (N5), or a close failing the round trip of 5.2.4 | step 5 | nothing; 2 | L1-7 | as R-04 |
| R-06 | DGS3MO missing, unreadable, off its md5, or a NaN left after the fill | step 6 | nothing; 2 | L1-7 | as R-04 |
| R-07 | Uncosted symbol, or table cost below `cost_floor_bp` | step 8 | nothing; 2 | L1-8 | a table cost at or above the printed floor |
| R-08 | `GATE["bootstrap_B"] != 2000` | step 9 | nothing; 2 | L1-18 | restore `GATE` (`git diff core/quant/validate.py`) |
| R-09 | Ledger chain broken | steps 1, 10 | nothing; 2 | L1-4 | stop; an owner ruling |
| R-10 | Rehearsal: ledger dir, output dir, prices file or reference card outside the temp root; a prices file with a pinned md5 (3.9) | 5.3.1; step 1, before any read (QA-R4-2); step 5 | nothing; 2 | L1-9 | temp dirs; synthetic data only |
| R-11 | Table not JSON, or its schema, grid or pilot values wrong; `reference_card_md5` off; of-record `owner_confirmed` missing or not quoting this table's and tree's digests; a test seam in of-record mode; of-record `C3-BTCUSD` with a null `reference_card` (QUANT-R4-2), or without an of-record `E1-SPY` record whose parity passed for all 12 columns at both cost levels under the same `code_sha256` (GOVERNANCE-R4-4) | argument validation; steps 0, 1 | nothing; 2 | L1-19, L1-29 | fix the printed field; after a change, `--fingerprint` and a new `owner_confirmed` (7A.3); pilot 1 first (Step 8) |
| R-12 | `register_trial` raises | step 11 | run record with the rows appended so far; 3, `REFUSED_REGISTRATION` | L1-26 | read the traceback; the rows stay; re-run under R-17 |
| R-13 | P0a: dates, closes or rf differ from the study's loaders | step 7 | nothing; 2 | L1-20 | stop; an owner ruling |
| R-14 | Linux without a working `unshare -rn`; the probe connected; `--egress-record` whose parent control connect failed (OPS-R5-4); of-record without a matching egress record | step 4; `--egress-record` (SECURITY-R4-3) | nothing (`--egress-record`: its record); 2 | L1-23, L2-9 | Control connect failed, either platform: the runner prints the control error first, then "this network does not reach 1.1.1.1:443, so the record cannot prove the rule; run Step 7A on a network that does, or ask Claude" (OPS-R5-4). Linux: a host with user namespaces. Windows: `Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out \| Get-NetFirewallApplicationFilter` and `Get-NetFirewallProfile \| Select Name, Enabled` (a third-party firewall can disable these rules); if the filter's `Program` is not `<printed path>\py313\python.exe`, or the rule is disabled or not `-Profile Any`, the two elevated firewall lines of 7A.2 again, the first removing the rule by name and the second creating it (OPS-R4-2, SECURITY-R4-3); then `--egress-record` |
| R-15 | Of-record: family ledger missing, empty or broken; host fingerprint differs | step 1 | nothing; 2 | L1-24 | the owner rules how the ledger starts (O11); `--fingerprint` on this host |
| R-16 | Another runner holds the table lock; `C3.jsonl` or the family ledger modified under 600 s ago | step 0 | nothing; 2 | L1-25 | wait the printed seconds, or end the runner holding the printed lock |
| R-17 | An earlier record of the same `table_sha256` that is not `IN_PROGRESS`, `ABORTED`, `ERROR` or a C-06-only `WITHHELD`, and no `--rerun-of` (5.3.5; OPS-R2-7) | step 0 | nothing; 2 | L1-5 | `--rerun-of <id> --reason "<text>"` |
| C-01 | Forced stop | child; parent re-derives (5.2.7) | manifest `valid: false`; child 10, run INVALID | L2-3 (N1); L1-27 | - |
| C-02 | Bars seen fewer than bars fed, or `backtest_end` before the last bar | child; parent re-derives against its own `n_bars` and last timestamp (QA-R4-3) | same | L2-3 (N1); L1-27 | - |
| C-03 | An order not FILLED | child; parent re-derives | same | L1-27 (doctored manifest, `valid: true`, exit 0; QA-R3-2); reason: at volume 1e9 every MARKET order fills on its bar | - |
| C-04 | An order denied or rejected | child; parent re-derives | same | L1-27 (as C-03); reason: on bar-only data the risk engine skips MARKET checks (5.2.5) | - |
| C-05 | Input schema, range, SHA-256, volume above `QUANTITY_MAX`, capital above `PRICE_MAX`, precision above `FIXED_PRECISION`, or path containment | child, before the engine | stderr only; 20 | L2-5a, L2-5b | - |
| C-06 | Non-zero exit (an `on_bar` raise included, 5.2.5), timeout (tree killed), missing output, unparsable JSON | parent | child tails in the run record; run INVALID | L1-27, L2-10 | - |
| C-07 | Manifest precision or environment differs from `--check-env` | parent | run record; run INVALID | L1-27 | - |
| C-08 | Census NT or TP set differing from the baseline's, either way, or an `adapters` or `network` module (5.2.7; QA-R3-12) | parent | run record, with the names; run INVALID | L1-12 | Claude reviews the names (5.2.7) |
| C-09 | Reconciliation off, a fill off a bar timestamp, or `onbar_equity.csv` without `n_bars` rows (QA-R4-3) | parent | run record; run INVALID | L1-27 | - |
| C-10 | The built child environment holds a key outside the contract | parent, before launch | nothing launched; run INVALID | L1-16 | - |
| C-11 | The manifest's `input.bars_sha256`, `bars_fed`, `first_ts` or `last_ts` differs from the parent's own value (QA-R4-3) | parent | run record; run INVALID | L1-27 | - |
| C-12 | `bar.ts_event` or `bar.close` differs from the input row | child | manifest `valid: false`; 10 | reason: bars are built from the rows they are compared with; only an engine change reaches it, which the identity pin excludes | - |
| C-13 | An order in flight on a decision bar | child | same | reason: without latency every order settles within its bar (5.2.3) | - |
| C-14 | The manifest's ledger-hash echo differs from the run's | parent | run record; run INVALID | L1-27 | - |
| C-15 | Environment not BACKTEST, or `strategy_started` false | child; parent re-derives | manifest or `--check-env`; 10, run INVALID | L2-8, L1-27 (as C-03) | - |
| G-01 | Any run INVALID (P13), or any hard check P0b, P1 to P4, P7, P12 failing | parity | run record, no card; 1, `WITHHELD` | L1-2, L1-13 | - |
| G-02 | Decisions or predicate dicts differ between `sc_qg` and `sc_nt`, or a score lacks `has_bench` | 5.5 step 5 | run record with both scores, no card; 1, `WITHHELD` ("decision mismatch", "benchmark test dropped") | L1-2 (N8) | - |
| G-03 | `walk_forward` or `score_strategy` raises anywhere after registration, in parity (P11, P12) or scoring (`core/quant/validate.py:366-367`) | 5.4, 5.5 | run record with the exception, no card; 1, `WITHHELD` | L1-31 | - |
| G-04 | `GATE` differs from its snapshot after scoring | 5.5 step 6 | run record, no card; 4, `ERROR` | L1-14 | - |
| G-05 | `assert_hash_at_run` raises: the ledger moved after registration | 5.5 step 7 | run record, no card; 1, `WITHHELD` | L1-26 | - |
| G-06 | An unexpected exception after registration | runner | run record with the traceback; 4, `ERROR` | L1-26 | - |
| G-07 | `KeyboardInterrupt` after registration | runner | run record; 5, `ABORTED` | L1-26, L1-27 | re-run under R-17 |
| G-08 | `reference_card` set (QUANT-R4-2): `reference_drift` is not empty: `sc_qg` does not reproduce the stored card (QUANT-R2-5, QUANT-R3-1) | 5.5 step 5 | run record, no card; 1, `WITHHELD` ("reference drift") | L1-29, L2-12 | - |

Warnings P5, P6, P8, P9 and P10 never withhold. A rehearsal with a stub child skips the census judgement (5.3.1). In
R-14's Remedy, `\|` is table escaping: the runner prints a plain `|` (OPS-R3-9).

## 8. Testing strategy

### 8.1 Two layers

**Layer 1**, the global interpreter, always runs: pure Python and numpy; no `nautilus_trader`, venv, network or cache
file except where a test says so; stub children are plain Python scripts (the stub child below, or a stub probe a
test writes into its temp dir). **Layer 2**, the venv through the launch contract, is NotRun when
`QUANTGEN_NAUTILUS_PYTHON` is blank or missing, and FAIL on a version or identity mismatch (O15). Both live in
`tests/nautilus_acceptance.py`, every test inside the guard of 3.3; the scan tests live in `tests/macro_m0_harness.py`.
No test compares a wall-clock field.

**Stub child** (`tests/nautilus_stub_child.py`; QA-R2-2), launched as `[<stub python>, "-I", <abs stub>, <flags>]`
through `child_cmd`. In `run` mode it reads `input.json` and `bars.csv`, applies 5.2.5's rule and fee-inclusive Decimal
sizing, with `plain_mean` for every moving average (QA-R3-9), fills every order at its bar's close, rounds each
commission with `cents` (5.4.1), and writes the four files of 5.2.6 with every manifest field of 6.2 and every echo, so
a correct table passes every hard check as with the sandbox; it answers `--check-env` and `--guard-selftest` as the
sandbox does, and `--probe` with `{"blocked": true, "errno": 101, "error": "stub"}` and exit 0 (QA-R3-5). Flags select
failure modes: `--exit 1`, `--sleep <s>`, `--no-manifest`, `--bad-json`, `--doctor
<C-01|C-02|C-03|C-04|C-07|C-09|C-11|C-14|C-15>`, each writing `valid: true` and exiting 0 so that only the parent's own
check can catch it (QA-R3-2; `C-02` lowers `bars_seen` and `bars_fed` together, QA-R4-3), `--fee-1x` (N7) and
`--selftest-wrong` (QA-R2-10). `<stub python>` is `sys.executable`, unless its `normcase(realpath)` lies under
`WindowsApps` and `%LOCALAPPDATA%\quantgen\py313\python.exe` exists, in which case the latter, since the stub needs only
the standard library; the hand-off report records the choice (QA-R3-10, QA-R4-4). Whether the Store Python's
`sys.executable`, an app-execution alias, starts under 4.3's minimal environment is UNVERIFIED until Step 7A.

### 8.2 Fixtures and golden values (map03 §6)

**F1, trend switch, 12 bars.** P = [97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97] on business days from
2001-01-02, bars at 21:00 UTC; `trend_switch(rule="sma", lookback=3, step=2)`; `cost_bps` `"50"`; capital
`"1005001"`; `Equity`, 9 price decimals, size precision 0, volume `"1000000000"`, seed 42.

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

Assertions: fills as the table; final cash 926,593.00 in the account and in the rebuild; every row inside the P10
bound (the largest gap is 1.74 bp at t = 3); P1 = 1; P4 holds once bar 11 is excluded.

**F1r** (QUANT-R2-6): F1's fills with rf = 0.0001 per session, so R gains the overlay `(cash(t) / E-(t)) rf(t)` of
5.3.3. Rows that change from F1: QUANTGEN pnl at t = 0, 1, 2, 6 becomes +0.0001 and at t = 5 -0.0049000; Nautilus R at
t = 0, 1, 2, 6 becomes +0.0001, at t = 5 -0.0049005 (955,201 / 960,001 x 1.0001 - 1) and at t = 10 -0.0102035. Rows
3, 4, 7, 8 and 9 move by under 1e-8 (cash of $1 or $49); every row stays inside the P10 bound.

**F2, crypto trend, 11 bars.** P = [50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800],
dates daily from 2021-01-01, bars at 00:00 UTC the next day; `crypto_trend(lookbacks=(1, 2), mas=(2, 3),
hysteresis=0.2)`, warm-up 3; `cost_bps` `"10"`; capital `"53053"`; `CurrencyPair`, 9 price and 8 size decimals.

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

**Negative and stress fixtures.**

| ID | Setup | Expected outcome | Layer |
|---|---|---|---|
| N1 | F1 with volume `"4000"` and 2 price decimals | as measured (QA-2): `fills.csv` has 1 row, BUY 1,000 @ 100.00, commission 500.00; account 904,501.00; quantity 1,000; 4 of 12 bars seen; force stop true; exit 10 with reasons `C-01: forced stop` and `C-02: bars seen fewer than bars fed`, which the parent re-derives (5.2.7). The second fill event, 9,000 @ 100.01, never reached `on_order_filled`; the -89.45 balance appears only in the log (map03 §2.11) | 2 |
| N2 | F1 inputs; QUANTGEN weights with one decision flipped | P1 < 1, P2 and P4 fail; WITHHELD | 1 |
| N3 | retired: the realism fixture (C-1) | none | none |
| N4 | QUANTGEN pair of identical columns; the Nautilus copy of the higher-index column raised by 1e-6 on every row (K3's 1512/1638 case) | P11 reports mismatches with QUANTGEN gap 0; nothing withholds; the card uses QUANTGEN's selection | 1 |
| N5 | A panel with one duplicated date; one with two dates swapped | R-05 before registration | 1 |
| N6 | Stress (QUANT-10, QA-R2-12): `synth_prices(2026, 5500, 80.0, 650.0, planted=range(252, 5292, 252))` with `synth_rf(5500)` (below); every planted bar is a decision bar of all 12 columns; the pilot-1 grid at 50 bp; 1x and 2x | every hard check passes (UNVERIFIED until Step 7; QA-R3-11); worst corr and abs ΔSR printed next to the bars and map 03's (0.99999901, 0.0013) | 2 |
| N7 | (i) `pnl_stress_nt` replaced by QUANTGEN's 1x matrix on `synth_prices(11, 1500, 100.0, 150.0)`, pilot-1 grid at 50 bp; (ii) F1 at stress 2 with every commission halved; (iii) F1's 2x leg whose `input.json` and manifest say stress `"1"`; (iv) the series of (i) with `pnl_nt = pnl_qg + 0.0001` on every row | (i) P3 and P12 at 2x reported (QA-R2-12); (ii) and (iii) P7 fails, (iii) because the expectation takes stress 2 from the runner's loop (QUANT-R2-3); (iv) correlations pass, P3 and P12's Sharpe check fail | 1 |
| N8 | `parity.agree` on hand-built `StrategyScore` pairs near pilot 2's stored values (QUANT-R2-2): (a) 5 configurations, PBO 0.19 against 0.21; (b) 12 configurations, both REJECT on the benchmark, `prob_loss_oos` 0.09 against 0.11; (c) 5 configurations, `prob_loss_oos` 0.09 against 0.11; (d) `bench_p` NaN on both | (a) card; (b) and (c) WITHHELD "decision mismatch"; (d) WITHHELD "benchmark test dropped" (measured: `scratch:rev3_probe/agree_probe.py`) | 1 |

The F1 and F2 goldens were verified in high precision at volume 1e12, and at 1e9 under `unshare -rn` with the filled
skeleton of 5.2.9 in Revisions 3 and 4 (5.4.3). Step 7A re-verifies them in standard precision.

**Synthetic series** (QA-R2-12): numpy 2.3.5's `default_rng`; dates `pd.bdate_range("2001-01-02", periods=n)` at 21:00
UTC. N6 runs from 79.53 to 556.04 (maximum 677.47); L2-7 is `synth_prices(7, 1500, 100.0, 150.0)` with `synth_rf(1500)`.
L2-12 (QUANT-R3-2) is `synth_prices(5, 1600, 400.0, 60000.0)` on `pd.date_range("2001-01-01", periods=1600, freq="D")`,
bars at 00:00 UTC the next day, no cash rate; it runs from 398.59 to 60,000.00 (maximum 60,450.91) and every close
passes the 9-decimal round trip. On Linux the md5s of `.tobytes()` are `adb735b9c3b6f1bab8e1728c38fff608` (N6),
`7b53fe601255972348aa60eccad550b7` (L2-7) and `c68986bf632dea074edb5c8ccef76a7d` (L2-12); Windows `exp` may differ in
the last bit, so tests assert outcomes, never these md5s.

```python
def synth_prices(seed, n, p0, p1, planted=()):                     # volatility clusters in 250-bar blocks
    lr = np.random.default_rng(seed).normal(0.0, np.where(np.arange(n) // 250 % 2 == 0, 0.008, 0.02))
    lr += (np.log(p1 / p0) - lr.sum()) / n                         # drift from about p0 to about p1
    for k, i in enumerate(planted):
        lr[i] = np.log(1.1 if k % 2 == 0 else 0.9)                 # planted +10 % and -10 % days
    return np.round(p0 * np.exp(np.cumsum(lr)), 9)
def synth_rf(n):                                                   # stepped: 0, 2, 5 and 1 % a year
    return np.repeat([0.0, 0.02, 0.05, 0.01], -(-n // 4))[:n] / 252
```

### 8.3 Layer-1 tests (`tests/nautilus_acceptance.py`)

| # | Test |
|---|---|
| 1 | Return reconstruction on F1, F1r and F2 from golden fills: R matches 8.2 to 1e-7. |
| 2 | Parity functions: N2, N4, N7, N8 (through `parity.agree`); the P10 bound on F1 and F1r; the P1 exemption with a planted 1e-10 QUANTGEN margin, and a 2e-9 margin that is not exempt; P7's tie (a 0.13 commission passes, 0.12 fails); a planted P5 warning still writes a card. |
| 3 | Ordering, with the stub child: a `child_started` hook reads the temp ledger and asserts that it holds every `config_id` of the table and that `input.json`'s hash equals `family_ledger(...).hash()` (QA-R4-4); no child exits 1, and the ledger held every `config_id` before the first child started (QA-R4-5). |
| 4 | A broken chain in the temp ledger stops the runner before any child starts (R-09). |
| 5 | Built at Step 7, when a first run can end `CARD_WRITTEN` (QA-R3-1). A second run of the same table without `rerun_of` refuses (R-17), and so does the same table with a new `owner_confirmed`, or re-saved with a BOM and CRLF (OPS-R3-5, QA-R3-3); after `os.utime` sets the ledger's mtime back 601 s (QA-R2-3) and with `rerun_of` and `reason`, it appends 0 rows, records `appended: false` for every row, and names the first run in `earlier_runs` and `supersedes`; a planted `IN_PROGRESS` record is printed. |
| 6 | R-01 and R-02 through `check_tree` and `tree_refusal` on a temp git repository: a modified tracked file and an untracked file outside `runs/` refuse; an untracked file under `runs/` passes; a `.git` file (worktree) and `git pack-refs --all` each refuse with their own message; in rehearsal `tree_refusal` returns None for the same findings. Without git: `NotRun("OWNER: git not on PATH")`. |
| 7 | R-04 (missing, unreadable, doctored md5), R-05 (N5; a close failing the round trip) and R-06 (missing, doctored md5, leading NaN) on synthetic files; a blank DGS3MO value on a mid-series session takes the prior value and P0a passes (QUANT-R2-1); no 3% fallback (K8). |
| 8 | R-07 for an uncosted symbol (`"VOD.L"`) and for 40 bp on SPY (K15). |
| 9 | R-10: a ledger or output dir outside the temp root (3.9); a synthetic file whose md5 the test plants as the pinned BTC md5; one planted as the pinned SPY md5 with `end` 2004-11-30 (GOVERNANCE-R2-3); a table naming any tracked file of `docs/asset_expansion/cache/`, such as `yf_SPY.csv` or `binance_BTCUSDT.csv`, with `prices_md5` set to 32 zeros, refused with R-10 by `check_table` and by `run()` with no `after_step1` hook fired, so a hash-first order fails with R-04 (GOVERNANCE-R3-3, QA-R4-2). No real price file is read. |
| 10 | K9: the bridge row's `config_id` for SPY `sma/127/21` at 50.0 equals the one `ui.strategy_lab_page.register_trials` writes with `ledger_dir=<another temp dir>` passed explicitly (`ui/strategy_lab_page.py:55-67`); the same for BTC-USD `hysteresis 0.333` at 10.0 in C3. Neither is a pilot configuration (GOVERNANCE-R3-2). |
| 11 | `RegisterResult` handling: the recorded `row_md5` equals `row["row_md5"]` for an appended row and for a duplicate. |
| 12 | Census judgement on doctored stderr: an extra TP name, a missing TP name (QA-R3-12) and `nautilus_trader.adapters.binance` each make the run INVALID; an extra STD name does not. |
| 13 | A parity failure writes no card and exactly one WITHHELD record into a temp output dir. |
| 14 | `GATE` is deep-equal before and after a synthetic end-to-end scoring; a `score_fn` that mutates `GATE` gives G-04, exit 4 and no card. |
| 15 | Encoding (AST) over `tools/nautilus/*.py` and the new tests: `encoding=` on every `open` (modes with `b` exempt; QA-R2-14), `read_text`, `write_text` and text-mode `subprocess` call; `lineterminator="\n"` on every `csv.writer`; no CSV the parent or fixtures write contains `b"\r"`. |
| 16 | The launch builder, given `os_name` `"nt"` and `"posix"`, builds exactly 4.3's argv and environment, with `unshare` on POSIX and each platform's process-group flag; `home` and `tmp` exist; an extra key gives C-10. No process starts. |
| 17 | Venv reads on a fake venv dir: `%VAR%` and `~` expansion, a control character, a wrong file name, `include-system-site-packages = true`, a Windows `executable` equal to the parent's or a `home` under `WindowsApps`, a version off its pin (R-03); the committed `RECORD` fixtures give `a448cd20...` and `47d274d7...`, 764 entries each (QA-R2-14). |
| 18 | R-08 with `GATE["bootstrap_B"]` set to 300 inside `try/finally`. |
| 19 | R-11 through `check_table`: a missing field, a wrong type, of-record pilot values off, a grid that differs from `grid_from(axes)`, a key field edited, a sandbox byte and a `core/quant/validate.py` byte changed after `owner_confirmed` (GOVERNANCE-R2-2, GOVERNANCE-R3-1); a `PureWindowsPath`-built path list gives the same `code_sha256` (OPS-R3-6); `run(mode="of-record", child_cmd=...)` refuses in argument validation, and `docs/nautilus_bridge/runs/.locks` is not created; of-record `C3-BTCUSD` on temp roots refuses without an of-record `E1-SPY` record, and with one WITHHELD for a parity failure (GOVERNANCE-R4-4). |
| 20 | P0 on a synthetic cache dir, through `check_p0a`: equal arrays pass; a doctored `study.rf_daily` refuses with R-13; a doctored benchmark withholds (P0b); a cache dir without `yf_<symbol>.csv`, and one without `fred_DGS3MO.csv`, each refuse with R-13 while the stand-in records the blocked download (QA-R4-1). |
| 21 | `select_matched` on QUANTGEN's own matrices reproduces `wf_qg` field by field, bit for bit (5.4.2). |
| 22 | The global interpreter has no `nautilus-trader` distribution and cannot import `nautilus_trader` (FAIL otherwise, with R-03's three remedy lines; OPS-R3-1); `pyarrow` presence is reported only. |
| 23 | R-14: a stub probe printing `{"blocked": false}` refuses; `check_egress_record` refuses a record with another `base_python` and, on Windows, accepts one differing only in case or slash direction (4.3). |
| 24 | R-15 through `check_table` on temp dirs: a missing ledger, an empty one, and a host fingerprint off by one character each refuse. |
| 25 | R-16 through `take_lock`: a held lock refuses; a `C3.jsonl` touched now refuses, one touched 601 s ago passes (QA-R2-3). |
| 26 | Lifecycle: `IN_PROGRESS` is on disk after registration; a hook raising `KeyboardInterrupt` gives `ABORTED`, exit 5; a hook appending a row after registration gives G-05 (Step 7); a hook raising `ValueError` gives G-06; a `register_fn` raising on the third row gives R-12 with two rows recorded. |
| 27 | Child failures: stubs that exit 1, sleep past `timeout=3` (the tree is killed and the call returns), write no manifest, or write invalid JSON (C-06); a `child_started` hook raising `KeyboardInterrupt` while a sleeping stub runs gives `ABORTED`, exit 5, and the temp dir is removed (OPS-R2-4); a stub whose `--guard-selftest` prints one wrong outcome gives R-03 (QA-R2-10); doctored manifests (`valid: true`, exit 0) for C-01, C-02, C-03, C-04, C-07, C-09, C-11, C-14 and C-15, each giving its own id in the run record (QA-R3-2). |
| 28 | Card and record: the record's card md5 equals the md5 of the card's bytes; `results_file` is the run id; the card has no `b"\r"`; writing a card to an existing path raises. |
| 29 | U count: both pilot tables' `study_configs` equal the stored cards' grids, symbols and costs (read-only reads of `docs/asset_expansion/cards/`, plus 10.2's run 2/3 values); on a temp ledger with planted rows, `n_trials = family_n_raw + U`. Protocol (QUANT-R2-5): each table's `embargo`, `cost_bps`, `grid` and `domain`, and 5.5's benchmark expression, equal the study's calls (`docs/asset_expansion_study.py:271-279, 329-343`, read with `ast` and `study.COST`), and pilot 2's equal the stored card's `rules` and `costs`. G-08 (QUANT-R3-1, QUANT-R3-3): `reference_drift` on hand-built scores whose OOS dates run from 2016-10-14 to 2026-09-25, with the reference's `n_years` 11 and `sc_qg.n_years` 9: all else equal gives no drift; `n_sessions` off by one, or a float off by 2e-9, gives drift; pilot 2's `reference_card_md5` equals the md5 of the card's bytes. A stub-child rehearsal of a synthetic crypto table whose temp `reference_card` has one `stats` float moved by 2e-9 ends WITHHELD "reference drift", exit 1 (QUANT-R4-1). |
| 30 | A written card carries `claim_label`, the engine text of 6.5, `parity_scope` and `stats.quantgen_score`; each table's `claim_label` starts with "exploratory", "pre-specified on historical data" or "confirmatory" (QUANT-R2-4). |
| 31 | G-03: a 400-row synthetic matrix makes `walk_forward` raise; the run is WITHHELD and the reason names the `walk_forward` exception (QA-R2-2). |
| 32 | The guard of 3.3 wraps every test; a last test compares the digests taken when the suite started (QA-1). |
| 33 | The committed F1, F2 and N1 goldens equal 8.2's tables, typed into the test with prices at each fixture's precision and reasons by id (QA-R2-6, QA-R3-8). |
| 34 | `write_record` with a `replace` seam raising `PermissionError` twice and a no-op `sleep` (QA-R3-7), then succeeding: written, status unchanged; always raising: intermediate writes are skipped and listed, the final write falls back to `run.final.<pid>.json` (OPS-R2-3). |
| 35 | `record_baseline` (5.2.7; OPS-R3-2, QA-R4-4) on a temp golden dir: a tracked equal baseline gives exit 0 "unchanged"; a tracked different one gives exit 2, the diff and the removal line, and leaves the file's bytes unchanged; an untracked different one is replaced and its diff printed, exit 0 (OPS-R4-2, OPS-R5-3); a tracked path with no file, as after the removal line, is written, exit 0 (OPS-R5-3). |
| 36 | `--fingerprint` (GOVERNANCE-R4-1), with the 3.3 guard's temp `QUANTGEN_MACRO_DIR`: on both committed pilot tables it prints both digests and `host_fingerprint` null with the reason, and exits 0; on a copy whose `prices_file` names a missing file it still exits 0, so it reads no data. |

### 8.4 Layer-2 tests

| # | Test | # | Test |
|---|---|---|---|
| 1 | `--check-env` and the parent's reads: pins and identity match; precision reported; environment `BACKTEST`. | 2 | F1 and F2 match their goldens; the manifest shows `run_analysis` false and `stats_pnls_empty` true (K6, QA-12). |
| 3 | N1 matches its golden. | 4 | Determinism: F1 and F2 each run in two separate processes and give the same `fills.csv` SHA-256. |
| 5a | Exit 20 before the engine is built, for one single-field perturbation of F1's input per 6.1 rule (QA-R3-4): an unknown field; each field missing; a wrong type; each range bound, the maxima `int(QUANTITY_MAX) + 1`, `int(PRICE_MAX) + 1` (QA-R2-8) and `FIXED_PRECISION + 1` read from `--check-env` at run time (QA-14); the schema string; close decimals, `n_bars`, row index and non-increasing timestamps; the hash formats and a doctored `bars_sha256`. Always runs; 63 such cases measured (5.4.3). | 5b | `input.json` linked to the repo's `.env` (SECURITY-3): exit 20. On WinError 1314, `NotRun("OWNER: enable Developer Mode, or accept this NotRun")` (OPS-R2-5). |
| 6 | The F1 and F2 censuses match the platform baseline under 5.2.7's rule. | 7 | A synthetic end-to-end rehearsal (8.2): `synth_prices(7, 1500, 100.0, 150.0)`, `synth_rf(1500)`, `grid_from(rule=["sma", "tsmom"], lookback=[126, 252], step=[21])` at 50 bp, embargo 21, temp ledger and outputs; a card whose decision is in `validate.DECISIONS`, or a WITHHELD record naming the differing predicate and its two values, which go into the execution record; never a new seed chosen after the result (UNVERIFIED until Step 7; QA-R3-11); both scores in the run record. |
| 8 | `--guard-selftest` exits 0: SANDBOX, LIVE and `LiveClock()` raised; BACKTEST and `TestClock()` passed (C-2). | 9 | The egress probe through the launch contract reports `blocked: true`. |
| 10 | `<venv python> -I -c "import time; time.sleep(120)"` through the launcher with timeout 3 returns within 15 s; the temp dir can be deleted, so no child survives (OPS-1). | 11 | N6 (QUANT-10). |
| 12 | Crypto rehearsal through the runner (QUANT-R3-2, QUANT-R4-1): the L2-12 series (8.2), the pilot-2 grid, embargo 1, `domain`, 10 bp, `rf_file` null, temp ledger and outputs. The test first builds the reference as the stored card was built: `asdict(sc_ref)` from `validate.score_strategy` on QUANTGEN's matrix, plus `chosen_last = grid[wf_qg.chosen[-1]]`, with `n_years` replaced by `len({d[:4] for d in wf_qg.dates})`; the table names it as a temp `reference_card` with its md5. Expected: a card, or a WITHHELD record naming its reason, with both scores and `gate.reference` holding an empty drift list (UNVERIFIED until Step 7); the same reference with the whole-year `n_years` left in gives exactly `["n_years"]` from `reference_drift`. |  |  |

### 8.5 Scan controls (`test_t_ro_01_nautilus_confined_to_the_sandbox`)

All in a temp tree, scanned with `_offences(path, tmp)`. Expected hits are exact multisets of tags (QA-15): a letter is
a `[nautilus:<rule>]` hit, `TEXT` an existing `FORBIDDEN_TEXT_CI` hit, `CALL` an existing `FORBIDDEN_CALLS` hit. They
were measured with `scratch:rev4_probe/scan4.py`, the Revision-2 prototype with the skeleton of 5.2.9, verbatim, as
the sandbox positive control; the filled sandbox gives no hit either. Every "sandbox +" control is that file plus the
listed code, inserted before its `if __name__` guard; each gives the multiset Revision 3 measured.

| Control | Path and content | Expected hits | Control | Path and content | Expected hits |
|---|---|---|---|---|---|
| sandbox positive | as above | none | runner positive | `tools/nautilus/runner.py`: `name.startswith('nautilus_trader.adapters')` (K4) | none |
| egress probe | `tools/nautilus/egress_probe.py`, the real file | none | key outside the bridge | `data/fmp/probe_key.py`: `def f(api_key): return api_key` | none |
| live leak | `tools/nautilus/live_leak.py`: `from nautilus_trader.live.node import TradingNode`, `import nautilus_trader.adapters.binance`, `from nautilus_trader.core import nautilus_pyo3`, `node = TradingNode(cfg)`, `node.run()` | C1 x3, C2 x3, D | dynamic | `tools/nautilus/dynamic.py`: `importlib.import_module('nautilus_trader.adapters.betfair')` | E |
| outside import | `core/quant/nt_runner.py`: `from nautilus_trader.backtest.engine import BacktestEngine` | C2 | outside submit | `tools/nautilus/other_submit.py`: `s.submit_order(o)` | TEXT, CALL |
| Rust client name | `tools/nautilus/client.py`: `m.BybitHttpClient(api_key='x', api_secret='y')` | D x3 | verbs | sandbox + a function calling each of the 7 verbs on `self` | A, CALL x8, TEXT |
| sandbox receiver | sandbox + `other.submit_order(o)` | A, CALL x2, TEXT | sandbox bare reference | sandbox + `f = self.submit_order` | A, CALL, TEXT |
| sandbox string | sandbox + `NAME = 'submit_order'` | A, CALL, TEXT | sandbox bare import | sandbox + `import nautilus_trader` | C3 |
| sandbox denied name | sandbox + `from nautilus_trader.config import TradingNodeConfig` | C1, C3 | sandbox relative | sandbox + `from . import runner` | C3 |
| sandbox `sys.modules` | sandbox + `from sys import modules` and `modules['nautilus_trader.core.' + 'nautilus_pyo3']` | C3, E, F1 | sandbox module chain | sandbox + `argparse._sys.modules['x']` | F4 |
| sandbox `__dict__` | sandbox + `Port.__dict__` | F3 | sandbox getattr | sandbox + `getattr(self, 'sub' + 'mit_order')(o)` | F2 |
| sandbox open | sandbox + `open('/repo/.env').read()` | F2 | sandbox path | sandbox + `Path('/repo/.env').read_text()` | F5 |
| sandbox os call | sandbox + `platform.os.system('x')` | F6 | sandbox `platform.system()` | sandbox + `x = platform.system()` | F6 |
| sandbox importlib | sandbox + `import importlib.metadata` | C3, F1 | banned modules, 14 controls | sandbox + `import <m>` for each m in `SANDBOX_BANNED_MODULES` | C3, F1 each |
| banned names, 12 controls | sandbox + `x = <n>` for each n in `SANDBOX_BANNED_NAMES` | F2 each |  |  |  |

Then the real tree gives no hit (measured with the amended rules: 0 hits over 154 files), and the real
`tools/nautilus/sandbox.py` exists and gives no hit.

### 8.6 Running tests in the Linux container (K13)

Never `python tests/run_all.py`, with or without `--suite`: `main` writes `OUT` on every run
(`tests/run_all.py:128-137`). Suite checks, every "reports NotRun" done-when included, go only through the redirecting
wrapper `scratch:run_baseline.py`, kept outside the repo, which imports `tests.run_all`, sets `R.OUT` to its first
argument and calls `R.main` with the rest: `python3 -B <scratch>/run_baseline.py <scratch>/out.json --suite nautilus`.
Single macro modules run with `python -m tests.<module>`, which prints only (map04 §7). After every check,
`md5sum qa/acceptance_results.json` equals its value before. The Linux full run has 8 environment FAILs (map04 §7);
only the Windows full run is the suite of record.

## 9. Steps and done-when

"Claude" means a session like this one; "owner" means Geon Koh. Every Claude step runs on the feature branch, with
synthetic data and temp ledgers only.

| Step | Who, what | Done when |
|---|---|---|
| 1a Claude rounds (**done**) | Claude drafts; the Claude referee rounds run and are ruled; Claude applies the rulings. | Each report is saved as `docs/superpowers/specs/2026-10-26-nautilus-review/round<k>_<name>.md` with its rulings file, and every issue has a ruling in Appendix B. Done when the moderator closes the Claude debate under C-8: a round with only minor issues is applied and closes it, and a new major reopens it (GOVERNANCE-R3-6). Round 4's major (OPS-R4-1) reopened it; the targeted round 5 by ops and security on Revision 5 raised only minor issues, which Revision 6 applies. **Done**: the moderator closed the Claude debate after round 5 (`round5_rulings.md` §1); rounds 1 to 5 are ruled and applied. Steps 2 to 7 start now on the branch, on the section 2 defaults, with synthetic data and temp ledgers (GOVERNANCE-R2-1). |
| 1b Outside review and approval | GPT and Gemini review on the owner's machine, as neither CLI exists in the cloud container, or the owner records a substitute in Appendix B; the owner approves. Required before Step 7A, not before Step 2. | Their reports and rulings are saved and mapped in Appendix B; the Status block carries the owner's approval in the form of the Owner context, verbatim with its channel and date, and answers to O1 to O15; branch work that an answer different from its default affects is redone or deleted. |
| 2 Plan and dry run | Claude: `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge.md` in the house format (Global Constraints, a file table, RED/GREEN steps for Steps 3 to 7); it names the spec revision it implements (GOVERNANCE-R3-6). Global Constraints = all of section 3, verbatim (GOVERNANCE-13), plus: Claude never runs of-record mode (GOVERNANCE-R2-4; 5.3.1) and writes ledger rows only under the system temp dir; no Claude commit includes `qa/acceptance_results.json` (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:30`); Claude reads no real BTC price and no SPY row on or after 2004-12-01; the pinned md5s come from this spec, and Claude never opens or hashes `yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv` or `upbit_KRW-BTC.csv` (GOVERNANCE-R3-3); Claude never writes or edits `owner_confirmed` or `host_fingerprint` in a committed table (`docs/nautilus_bridge/registration/`); tests write them only into tables under the system temp dir (GOVERNANCE-R3-5, GOVERNANCE-R4-3); no global `pip install`. Dry run (QA-21): the plan's own RED steps, run in a scratch clone with `scratch:ntvenv`; nothing is built twice. | The plan exists; its RED steps fail for the reason each states in the scratch clone; in the real repo `git status` shows no change beyond the plan file, and `qa/acceptance_results.json` keeps its md5. |
| 3 Environment | Claude on Linux (the Windows half is Step 7A): `requirements-nautilus.txt` (5.1); `.env.example`; `tools/nautilus/__init__.py`; `sandbox.py` with `--check-env` and `--guard-selftest`; `egress_probe.py`; `launch.py` (QA-R2-5); `env_pins.json` with both platforms and the `RECORD` fixtures (6.7); `docs/nautilus_bridge/.gitignore`. | The file pins 5.1's 16 distributions with hashes; `pip install --require-hashes --only-binary=:all: --no-cache-dir -r requirements-nautilus.txt` succeeds in a fresh scratch venv and `pip check` is clean; `launch.py`'s identity read gives `a448cd20...` with 764 entries; under `unshare -rn`, `--check-env` reports Python 3.13.x, `HIGH_PRECISION` true and environment `BACKTEST`, `--guard-selftest` exits 0, and the probe reports `blocked: true`; the global interpreter still reports numpy 2.3.5, pandas 2.3.3, scipy 1.18.0 and no `nautilus_trader`; `requirements.txt`, `requirements-dev.txt` and `pyproject.toml` are byte-identical. |
| 4 Guard | Claude, on ruling O2's default (in effect outside the branch only after the sign-off): 5.6; the suite registration (5.7); the registry resync and README text of 5.8. | Both new tests pass; every control of 8.5 gives exactly its multiset; the real tree and the real sandbox give no hit; test_08 and test_09 are unchanged and pass; `python -m tests.macro_acceptance` has resynced row 12 and `test_registry_implemented_in_matches_test_ids` passes; L1-15, L1-16, L1-17, L1-22 and L1-32 pass; through the wrapper, `--suite nautilus` reports its layer-2 tests NOT_RUN, not PASS, with `QUANTGEN_NAUTILUS_PYTHON` unset; the README Total row is unchanged. |
| 5 Sandbox | Claude: section 5.2 in full, in the structure of 5.2.9. | `launch.fixture_inputs` builds F1, F1r, F2 and N1 (QA-R3-1); in the Linux venv under `unshare -rn`, L2-1, L2-4, L2-5a, L2-5b and L2-8 to L2-10 pass; no code path uses `AT_THE_CLOSE`, `allow_cash_borrowing=True`, `LatencyModel`, the `PortfolioAnalyzer` or a report as equity; the real sandbox gives no scan hit; layer-2 tests report NotRun without the venv. |
| 6 Runner | Claude: section 5.3. | L1-1, L1-3, L1-4, L1-6 to L1-12, L1-16 to L1-19, L1-20's P0a cases, L1-22 to L1-27 (L1-26 without its G-05 case) and L1-33 to L1-35 pass; `--write-goldens` has written F1, F2 and N1, and `--record-baseline` `modules_manylinux_2_35_x86_64.json`, the union of the F1 and F2 censuses; L2-2, L2-3 and L2-6 pass (QA-R2-5); on F1 and F1r the rebuilt R matches 8.2 to 1e-7; the run record carries the post-registration ledger hash, both data md5s, the venv reads and every child manifest. |
| 7 Parity and gate | Claude, synthetic data only (GOVERNANCE-5): sections 5.4 and 5.5; both pilot tables without their owner fields; `docs/nautilus_bridge/RUNBOOK_windows.md`. | L1-2, L1-5 (QA-R3-1), L1-13, L1-14, L1-20's P0b case, L1-21, L1-26's G-05 case, L1-28 to L1-31 and L1-36 pass; L2-7, L2-11 and L2-12 pass (QUANT-R3-2); `GATE` is unchanged after every run; N6 reports its worst corr and abs ΔSR next to the bars and map 03's. Real-data parity evidence stays map 03's (5.4.3), never repeated. |

**Step 7A. Hand-off (K2, OPS-8, GOVERNANCE-11, GOVERNANCE-R2-2, GOVERNANCE-R2-5).** After Step 1b. Claude, then the
owner, in this order; the runbook file repeats it.
1. The owner writes the sign-off sentence (Owner context), which releases the merge and the T-RO-01 exemption only.
   Before recording it, Claude runs `git fetch origin` and `git merge-base --is-ancestor origin/main HEAD`, and if main
   has moved, merges `origin/main` into the branch first, so the sentence covers the merged branch (GOVERNANCE-R4-2).
   Claude records it verbatim in the Status block, commits, and asks the owner for approval to push; on approval, Claude
   pushes. Any Claude commit leaves `qa/acceptance_results.json` byte-identical and says so.
2. In the main clone, in a normal (not elevated) PowerShell, with power plugged in (OPS-R4-5; the runner and the
   suite's layer-2 tests also keep the machine awake, 5.3.5 and 5.7; OPS-R5-5), the owner runs the lines below one at
   a time; the python.org installer, at the 3.13 patch the runbook pins, is downloaded into `$q`, never into the clone
   (OPS-R3-3, OPS-R4-5). A throw in the five git lines stops the block: he sends Claude the message, because the
   hand-off needs the branch (OPS-R5-2). On a red error in any later line he skips to the last line (OPS-R2-1). The
   fast-forward line, the fifth git line, brings Claude's fixes and a new sign-off into a re-entry (OPS-R4-1,
   OPS-R5-2). Re-entry (OPS-R3-2, OPS-R4-1, OPS-R5-1, SECURITY-R5-1): if `$q\py313\python.exe` exists from an earlier
   attempt, the listed registry row is that install, and he skips from the registry line to the rule check line, whose
   output shows whether the `QUANTGEN-nautilus-block-out` rule exists (empty output: no rule). While no rule exists, he
   goes on to the `pip download` line whatever `$q\wheels` holds, because pip reuses every finished file whose hash it
   verifies; the rule exists only after an install has passed, because a red error at the install line skips to the
   last line. Once the rule exists, he re-enters at the `venv` line, because the rule blocks that interpreter's pip and
   the offline `--require-hashes` install re-checks every hash; if `$q\wheels` is then missing, he first runs the
   elevated `Remove-NetFirewallRule` line alone and re-enters at the download line. That a normal window can read the
   rule is UNVERIFIED; if it cannot, he takes the rule to exist once the elevated lines have run. The `venv`, install
   and runner lines are safe to repeat, the first firewall line removes any rule of that name before the second creates
   the rule (OPS-R4-2), and `--record-baseline` treats an existing baseline as 5.2.7 says. No line of this block has run
   in this session (UNVERIFIED until Step 7A). Never a whole-tree `checkout`, `reset`, `stash` or `clean` in the main
   repo (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:89-91`); `git switch`
   rewrites only files that differ, and the branch leaves `docs/asset_expansion/cache/` alone; never a worktree, which
   gives UNVERSIONED rows (same file :85-87). The download URL, the installer options and its `/log` switch are as
   python.org documents them (UNVERIFIED on the owner's machine); the base interpreter has the same 3.13 minor as the
   global one. The dedicated interpreter's pip downloads the wheels before the firewall rule exists; the global pip
   never runs (OPS-R2-2).
   ```
   git fetch origin; if ($LASTEXITCODE) { throw "fetch" }
   git merge-base --is-ancestor origin/main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "main has moved: ask Claude to merge origin/main into the branch first" }
   git merge-base --is-ancestor main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "local main has unpushed commits: push them, then ask Claude to merge origin/main" }
   git switch claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "switch" }
   git merge --ff-only origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "fast-forward: ask Claude" }
   $q = Join-Path $env:LOCALAPPDATA "quantgen"; New-Item -ItemType Directory -Force $q | Out-Null; $q   # note the printed path
   $u = "Microsoft\Windows\CurrentVersion\Uninstall\*"; Get-ItemProperty "HKCU:\Software\$u", "HKLM:\Software\$u", "HKLM:\Software\WOW6432Node\$u" -ErrorAction SilentlyContinue | ? DisplayName -like "Python 3.13*"
   #   first attempt: any row is a python.org 3.13 already registered; stop and report it (the Store package is not listed there)
   $v = "3.13.<x>"; $inst = "$q\python-$v-amd64.exe"   # <x>: the patch RUNBOOK_windows.md pins
   $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$v/python-$v-amd64.exe" -OutFile $inst
   if ((Get-AuthenticodeSignature $inst).Status -ne "Valid") { throw "signature" }   # signer: Python Software Foundation (UNVERIFIED)
   $p = Start-Process $inst -Wait -PassThru -ArgumentList "/quiet", "InstallAllUsers=0", "TargetDir=$q\py313", "PrependPath=0", "Include_launcher=0", "Shortcuts=0", "/log", "$q\py313-install.log"
   if ($p.ExitCode -ne 0) { throw "installer exit $($p.ExitCode); see $q\py313-install.log" }
   Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue   # rule check
   #   empty output (always on a first attempt): no rule, go on to the next line; a rule listed: skip to the venv line,
   #   unless $q\wheels is missing: then the elevated Remove-NetFirewallRule line alone first, then the next line
   & "$q\py313\python.exe" -m pip download --require-hashes --only-binary=:all: --no-deps -r requirements-nautilus.txt -d "$q\wheels"; if ($LASTEXITCODE) { throw "download" }
   & "$q\py313\python.exe" -m venv "$q\ntvenv"; if ($LASTEXITCODE) { throw "venv" }
   # the PowerShell install line of the requirements-nautilus.txt header (5.1), followed by: if ($LASTEXITCODE) { throw "install" }
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
3. The owner commits and pushes `docs/nautilus_bridge/handoff/win_amd64.json` whatever happened after the five git lines
   (OPS-8, OPS-R5-2). A null host
   fingerprint stops here (R-15, O11). If every line passed, he also pastes each fingerprint into its table's
   `host_fingerprint`, writes `owner_confirmed` as `"Geon Koh, <date>, table <16 hex>, code <16 hex>"` from the printed
   digests, which approves of-record runs of that table (GOVERNANCE-R2-2), and commits as one change group
   `tools/nautilus/golden/modules_win_amd64.json`, `docs/nautilus_bridge/egress/win_amd64.json`, both tables and
   `qa/acceptance_results.json` (GOVERNANCE-R3-4), each named in `git add`, never `git add -A` (OPS-R3-3); that commit
   also writes the branch's loose ref (OPS-3).
4. Claude reviews the hand-off report and the census diff in the next session; checks that the commit carrying the
   current sign-off sentence is an ancestor of the 7A.3 commit and lists the files `git diff --name-only <sentence
   commit> <7A.3 commit>` changes, which must be only 7A.3's (the census baseline, the egress record, the hand-off
   report, both tables and `qa/acceptance_results.json`); recomputes `code_sha256` on Linux at the 7A.3 commit with
   `--fingerprint` and compares it with both tables' `owner_confirmed` (OPS-R3-6, GOVERNANCE-R4-1, GOVERNANCE-R4-2); and
   records the review in Appendix B. Claude's review commit changes only this spec; a review that needs any other change
   means Step 7A has failed. No pilot runs before that review. Any code change after the sign-off sentence needs a new
   sentence and a new `owner_confirmed`.
5. The owner pulls Claude's review commit with `git pull --ff-only` before Step 8; the pilots anchor to that HEAD, and
   the run record stores it (GOVERNANCE-R2-5).
- Merge (GOVERNANCE-R2-5, OPS-R3-7): after Step 10 the owner merges the branch into `main` (`origin/main`, `716bf77`
  today, the branch's base) with a merge commit he makes himself, never a squash or a rebase, and keeps the branch ref,
  so every ledger anchor stays reachable: `git switch main`, `git pull --ff-only`, `git merge --no-ff
  claude/amazing-gauss-tdiguu`, `git push origin main`. Until then the clone stays on the branch; readouts wait, or run
  from a separate clone, never during a pilot (3.8).
- Done when: on Windows, `--check-env` reports the pinned versions, the `win_amd64` identity `47d274d7...` with 764
  entries, `HIGH_PRECISION` false and `FIXED_PRECISION` 9, and `--guard-selftest` behaves; the egress record shows
  `probe.blocked` and `control_connect.ok` true; F1, F2 and N1 run through the exact launch contract and match their
  goldens (K1), or the hand-off stops and no pilot runs; the census diff obeys 5.2.7 and Claude has reviewed it; the
  hand-off report holds the import time and the time of 12 synthetic runs of 5,600 bars; the full run shows 0 FAIL with
  the `nautilus` layer-2 tests PASS, L2-5b the only `nautilus/*` NotRun allowed (OPS-R2-5, QA-R4-5), and the stub
  children start through the interpreter 8.1's rule picks, recorded in the hand-off report (QA-R3-10, QA-R4-4);
  frozen_guard (a), (b) and (d) pass; `repo_anchor()` returns `git:<the 7A.5 HEAD>`; `git status --porcelain` is empty.

| Step | Who, what | Done when |
|---|---|---|
| 8 Pilot 1 | The owner runs `python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot1_E1_spy.json --of-record`, never while the suite or a readout runs, with power plugged in, updates paused (in Settings; no stable command, UNVERIFIED) and a console that stays open (OPS-6); the runner itself keeps the machine awake (5.3.5; OPS-R3-8); a re-run follows 5.3.5 (R-17); Claude reads the outputs after the owner pushes them. | E1 holds the 12 `config_id`s, appended or already present, and recorded; every manifest echoes the post-registration ledger hash, the evidence that every child ran after registration (QA-R3-12); every hard check passes for all 12 columns at 1x and 2x, or a WITHHELD record names the failing check; if parity passed, the run folder holds `NB_E1_trend_spy.json` with the decision both engines reached, the four trial counts, the manifest hashes and the selection used, or a WITHHELD record says "decision mismatch"; the owner has committed and pushed the run folder. |
| 9 Pilot 2 | The owner, only if pilot 1 passed parity, which R-11 enforces (GOVERNANCE-R4-4). | Step 8's conditions hold for 5 columns at 10 and 20 bp, a WITHHELD "reference drift" (G-08) being a valid end too (QUANT-R4-3); `NB_C3_crypto_trend_btcusd.json` reports PBO for information only, and over-search uses the share of splits where the in-sample winner loses (`core/quant/validate.py:576`; map02 §2.5). |
| 10 Close-out | The owner runs the full suite on Windows and updates the README counts and Total row from it (C-4); Claude writes `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md` with every ruling made, its cost if wrong, and the data-access history of 10.4. | The Windows full run shows 0 FAIL with the `nautilus` suite counted; `qa/acceptance_results.json` is committed only from an owner's Windows full run (Step 7A.2 and this step), never from Linux (GOVERNANCE-R3-4); frozen_guard (a), (b) and (d) pass there; run folders and the execution record are committed; `git diff --name-only` against the 7A.5 HEAD that the pilot run records store lists only paths under `docs/nautilus_bridge/runs/`, the execution record, `README.md`, `qa/acceptance_results.json` and this spec, so nothing under `paper_live/`, `grokteam/`, `docs/asset_expansion/cards/` or the harness sources of `core/quant/gate_package.py:36-38` changed (GOVERNANCE-R3-1, GOVERNANCE-R3-7, GOVERNANCE-R4-2). |

## 10. Pilots

Each table below becomes a committed JSON file in `docs/nautilus_bridge/registration/` in the form of 6.6. Claude
writes it at Step 7; the owner fills `owner_confirmed` and `host_fingerprint` at Step 7A. Changing a key field after a
run is a new trial.

### 10.1 Pilot 1: SPY trend switch (family E1)

| Item | Value | Source | Item | Value | Source |
|---|---|---|---|---|---|
| Family, rule, market | `E1`, `"E1"`, `"US"` | `ui/strategy_lab_page.py:50`; `tests/paper_live_acceptance.py:333-343` | Price file | `docs/asset_expansion/cache/yf_SPY.csv`, md5 `d2164597d576e1b2fcadde063065811d`; Yahoo close with `auto_adjust=True` | map03 §1.1; synth §9.2; `docs/asset_expansion_study.py:82-91` |
| Sample | `start` 2004-12-01, `end` 2026-09-25, the file's last date | `docs/asset_expansion_study.py:724`; O6 | Grid | `grid_from(rule=["sma", "tsmom"], lookback=[126, 210, 252], step=[21, 42])`, 12 columns; tsmom raw, rf = 0 in the signal | `docs/asset_expansion_study.py:274`; `core/quant/strategies.py:384` |
| Params per row | `{"rule", "lookback", "step", "symbols": ["SPY"], "cost_bps": 50.0}` | 6.4 | Cash rate | DGS3MO / 100 / 252, forward-filled, `fred_DGS3MO.csv` md5 `661722143f24930a29b58c535d227c1b`, no fallback | K8 |
| Cost | 50 bp per side from `cost_floor_bp(["SPY"])`; stress 100 bp | `core/quant/validate.py:78, 115-121` | Embargo, benchmark | 21; SPY buy-and-hold, uncosted | `docs/asset_expansion_study.py:275, 278` |
| Capital, account, instrument | $1,000,000; CASH, NETTING; `Equity`, whole shares, 9 dp; fee-inclusive sizing | 5.2.3, 5.2.5 | Gate | `GATE` unchanged: 756 / 126 / 504, B 2000, seed 11 | `core/quant/validate.py:53-74` |
| `study_configs` | `S_E1_trend_us`: the 12 settings with symbols `["GLD", "QQQ", "SPY", "TLT"]` at 50.0; `S_E1_trend_krx`: the 12 settings with `["069500.KS", "132030.KS", "152380.KS", "229200.KS"]` at 3.0 | `docs/asset_expansion/cards/S_E1_trend_us.json`, `S_E1_trend_krx.json` | Trial count; ledger | `E1 N_raw after registration + U`, U at most 24; `E1.jsonl` must exist, hold a row and verify (R-15) | O11; 5.5 step 3 |
| Claim label; card | `"pre-specified on historical data; the SPY series was used inside S_E1_trend_us with the same 12-setting grid; not confirmatory"`; `NB_E1_trend_spy` | QUANT-6, QUANT-R2-4; 6.5 | Before registration | md5 pins, date checks, 9-decimal rounding and P0a only; no signal, return or statistic | 3.9 |

From the row counts alone: 38 origins, the first OOS session at row 777, and 4,711 OOS sessions, about 18.7 years
(map02 §1.2). The five-year rule is met by construction.

### 10.2 Pilot 2: BTC-USD crypto trend (family C3)

| Item | Value | Source | Item | Value | Source |
|---|---|---|---|---|---|
| Family, rule, market | `C3`, `"C3"`, `"CRYPTO"` | `ui/strategy_lab_page.py:50-52` | Price file | `docs/asset_expansion/cache/yf_BTC-USD.csv`, md5 `bc76f530ff24ab445367fe826150bc10`; `start` 2014-09-17, `end` 2026-09-25, the whole file, 7-day calendar | map03 §5.1; `docs/asset_expansion_study.py:731` |
| Grid | `grid_from(hysteresis=[0.0, 0.222, 0.444, 0.667, 0.889])`; study defaults for lookbacks and MAs; domain (0, 0.889) | `docs/asset_expansion_study.py:333, 339` | Params per row | `{"hysteresis", "symbols": ["BTC-USD"], "cost_bps": 10.0}` | 6.4 |
| Cash rate; cost | none: `rf_file` null, so `rf = 0.0` (5.3.2 step 6); 10 bp per side from `cost_floor_bp(["BTC-USD"])`, stress 20 bp, flat, no weekend term | `docs/asset_expansion_study.py:335-343`; `core/quant/validate.py:78` | Embargo, benchmark | 1; BTC buy-and-hold, uncosted | `docs/asset_expansion_study.py:334, 337` |
| Capital, account, instrument | $1,000,000 USD and 0 BTC; CASH with `base_currency=None`; spot `CurrencyPair`, 9 price and 8 size decimals | 5.2.3 | `study_configs` | BTC-USD runs 2 and 3: hysteresis 0.05, 0.1, 0.2, 0.3, 0.4, 0.5 at 10.0 (6); KRW-BTC: the 5 lattice values at 10.0, symbols `["KRW-BTC"]`. The BTC-USD lattice equals the bridge's own rows and never counts in U. Whether runs 2 and 3 also ran on KRW-BTC is UNVERIFIED; the card's ledger note names BTC-USD only. | `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json` (`trials.ledger`), `S_C3_crypto_trend_krwbtc.json` |
| Trial count; ledger | `C3 N_raw after registration + U`, U at most 11; C3 also holds paper_live US and KR trend rows (K12); `C3.jsonl` must exist, hold a row and verify (R-15) | O11 | Claim label; card | `"pre-specified on historical data, engine replication: stored card S_C3_crypto_trend_btcusd on the same file and configurations, grid revised on this file; not new evidence about the rule"`; `NB_C3_crypto_trend_btcusd` | QUANT-6, QUANT-R2-4; 6.5 |
| Precondition | pilot 1 passed every hard parity check; R-11 enforces it (GOVERNANCE-R4-4) | synth §2.2 | Reference card | `reference_card` `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json`, `reference_card_md5` `d0bb0882fb51dec361cf2ddb160186bb` (G-08) | QUANT-R3-3 |

With 5 columns, PBO is reported only (`core/quant/validate.py:68, 576`). On a 365-day calendar the five-year rule binds
before the 1,260-session rule (map03 §5.2).

### 10.3 Expected verdicts, stated before the run

**Pilot 1: a non-PASS verdict is expected**, a statement about the rule made before any pilot-window SPY number exists.
In the gate's own order (QUANT-7): (1) **INSUFFICIENT_DATA first**: the gate checks the trade floor first and returns
below 30 OOS trades (`core/quant/validate.py:586`); a single sleeve trades only on its own switch days, map 03 counted 3
to 23 switches per column in 10 pre-2004 years (map03 §4.3), and synthetic single-sleeve walk-forwards made 26 and 40
trades (`scratch:referee_quant/tie_probe_fast.py`); INSUFFICIENT_DATA says nothing about the benchmark claim. (2)
**Otherwise REJECT on the benchmark test**: `S_E1_trend_us` did not beat its benchmark (Sharpe difference -0.11, p 0.75;
`docs/asset_expansion/results.md:9`), and SPY alone is measured against SPY buy-and-hold. (3) **REVISE is unlikely**: it
needs the benchmark test and the DSR to pass first. No SPY-only number exists, on purpose (UNVERIFIED). Any of these is
a finding about the rule, not a bridge failure; changing the grid after seeing the result is a new trial.

**Pilot 2.** The stored QUANTGEN card on the same file and five configurations is PASS: SR 1.19 [0.72, 1.64], DSR 1.00,
144 trades, benchmark p 0.07 (`docs/asset_expansion/manifest.json:53`; map02 §5.3). If parity holds, P0 shows the
inputs equal the study's and `sc_qg` reproduces the stored card (G-08), the expected verdict is PASS. What could change
it: the engines' scores differing in any gate predicate (5.5 step 5), which withholds "decision mismatch" rather than
carding; and `n_trials` exceeding 11 once U and the paper_live rows count (O11), though the
inverted stored DSR stays at or above 0.9997 up to N = 1,000 (quant referee's note). A non-PASS with parity passing
would be a finding to investigate, not a reason to tune anything. The card will report 9 whole years where the stored
card reports 11 calendar years; the gate's five-year rule passes either way (QUANT-R3-1).

### 10.4 Data-access history

This list goes verbatim into the execution record (map04 R23).

| When | Who | Data | What was computed | Ledger rows |
|---|---|---|---|---|
| 2026-09-27 and earlier | asset-expansion study | `yf_SPY.csv` 2004-12-01 to 2026-09-25, inside the four-sleeve book `S_E1_trend_us` | the 12-setting grid on SPY, QQQ, TLT and GLD at 1/4 each; REJECT | none (`n_trials` typed by hand) |
| 2026-09-27 and earlier | asset-expansion study | `yf_BTC-USD.csv`, whole file | runs 2 and 3 (6 hysteresis values), then the five lattice values; PASS | none |
| 2026-10-26 | map 03 probe | `yf_SPY.csv` 1995-01-03 to 2004-11-30 (2,497 sessions), `fred_DGS3MO.csv` | all 12 pilot-1 settings at 1x and 2x on both engines; walk-forward selection | none; their `config_id`s equal pilot 1's, because `span` is not in the key |
| 2026-10-26 | synthesis and critic | the same pre-2004 window and map 03's saved matrices | 109 single-block flips; walk-forward ties (K3) | none |
| 2026-10-26 | round-1 referees, Revision-2 probes | synthetic series only; the study module imported without reading data; no real BTC price | fixtures, ties, cost gaps, scan rules, egress | none |
| 2026-10-26 | round-2 referees, Revision-3 probes | synthetic series; `fred_DGS3MO.csv` (its NaN pattern); the stored cards' statistics; the first 3 lines of `yf_SPY.csv` (1995) and 4 pre-2004-12-01 dates in it (QA referee); no BTC price, no SPY row from 2004-12-01 | rf fill, gate predicates, rounding, `Money`, fixtures, scan | none |
| 2026-10-26 | round-3 referees, Revision-4 probes | synthetic series and calendars; the stored cards' JSON (statistics, line text, the S_C3 card's md5); `study.log`, `manifest.json` and `results.md`; the names and sizes, not the content, of `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv`; no price row of a real series | the `n_years` rule, `cents`, fixtures, 6.1 refusals, scan, remedies, digests | none |
| 2026-10-26 | round-4 referees | synthetic series; the four KRX ETF caches and `fred_DGS3MO.csv` (quant referee, re-scoring the stored `S_E1_trend_krx` grid, raw and 9-decimal); stored cards' JSON; no SPY row from 2004-12-01, no BTC price | G-08 rules on a stored card, P0a stand-ins, digests | none |
| 2026-10-26 | round-5 referees (ops, security) | closure wheels installed offline into scratch venvs, throwaway git repositories, extracts of this spec; lines 27 and 29 of `docs/asset_expansion/study.log` (the owner's profile path); no price file, no price cache, no ledger | pip and git re-entry, both pins, the 8.5 controls | none |
| Steps 3 to 7 | Claude | synthetic series only | rehearsals | temp only |

Claim labels in the house protocol's terms (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:442-452`):
pilot 1 is *pre-specified on historical data*, on a series already used inside a four-sleeve book; pilot 2 is an
engine replication of a stored card. Neither is confirmatory. Each card carries its label (6.5).

## 11. Risks

| # | Risk | Mitigation | # | Risk | Mitigation |
|---|---|---|---|---|---|
| 1 | The T-RO-01 amendment is drawn too wide and opens an order path. | One file; one AST-counted `self.submit_order` call; 7 verbs forbidden everywhere; full dotted names; denied identifiers and client-name pattern; rule F; both lists pinned by hash; the controls of 8.5. | 2 | Sandbox code reaches a loaded network client (SECURITY-1). | Rule F rejects the direct spellings (`import sys`, module-alias subscripts, dunders, dynamic calls); an attribute path through a loaded module can still reach `sys.modules`, which the scan cannot fully close; the egress layer bounds any use, as any socket fails (4.4; SECURITY-R4-1). The census is drift detection only. |
| 3 | The Rust adapter and network clients bypass Python checks (K5). | The egress layer: `unshare -rn` on Linux, the firewalled dedicated interpreter on Windows, a probe every run, a recorded probe at Step 7A. | 4 | Standard precision on Windows changes fills or breaks a run (K1). | Volume 1e9; precision and volume refusals; F1, F2 and N1 on Windows at Step 7A before any pilot. |
| 5 | A global install moves numpy and pandas, or adds `nautilus_trader` there. | The requirements header with both shells; L1-22; FAIL on mismatch. | 6 | `.env` keys reach the child. | Explicit environment (C-10); the sandbox opens only its temp dir (5.2.8); without egress a read key is inert. |
| 7 | A forced stop or thin volume truncates a run that returns normally. | C-01 to C-03; fee-inclusive sizing; volume 2.5e8 at the close. | 8 | Someone reads `PortfolioAnalyzer` or the account report as equity. | `run_analysis=False` with the `stats_pnls_empty` witness; returns rebuilt from fills. |
| 9 | The owner's original bars pass real bugs (5.4.3). | Corrected bars (O5); P4; P7 hard. | 10 | Engine noise picks different walk-forward columns (K3), or the verdict depends on one engine (C-3). | QUANTGEN's selection on both matrices (5.4.2); both scored, card only on agreement (5.5). |
| 11 | A convention mismatch looks like an engine error, or an input error passes parity. | One shared rounded array; checked bars; P0 against the study's loaders. | 12 | Yahoo restates adjusted history, or the DGS3MO file changes. | md5 pins; refusals (R-04, R-06). |
| 13 | An unregistered look at a pilot window. | Place and content refusals (R-10); synthetic-only Claude rehearsals; registration before any child; 10.4. | 14 | Pilot rows anchor a commit without the code (K2), or of-record runs on the wrong machine. | Step 7A; R-01, R-02; host fingerprint, existing ledger, egress record (R-14, R-15). |
| 15 | Replica rows get a different `config_id` (K9), or the trial count is wrong (QUANT-4, K12). | The Lab's exact params expression (L1-10); `N_raw + U`, four counts stored. | 16 | Pilot 1 ends non-PASS and is read as a bridge failure, or the grid is tuned after seeing it. | 10.3 states the expectation; any change is a new registration. |
| 17 | API churn: 1.231.0 is the last 1.x release. | Exact pin with hashes; all Nautilus calls in one file. | 18 | The Linux `run_all.py` rewrites the results file (K13). | 8.6. |
| 19 | A pilot runs alongside the suite, a readout or another runner. | 3.8; the table lock; the freshness refusal (R-16). | 20 | LGPL-3.0 duties if QUANTGEN is conveyed; FSCMA questions if results are published. | The README forbids distribution (`README.md:924-929`); publication needs an owner review; FSCMA is UNVERIFIED (map04 §8). |
| 21 | The firewall rule does not bind the redirector-started interpreter, or is deleted later. | The per-run probe refuses an open route (R-14); Step 7A records the proof. | 22 | `E1.jsonl` is missing or empty on the owner's machine. | R-15 refuses; the owner rules how the ledger starts (O11). |
| 23 | OneDrive, Defender or the indexer holds `run.json` during `os.replace` (OPS-R2-3). | `write_record`'s retries, best-effort intermediate writes and the `run.final.<pid>.json` fallback (5.3.5). |  |  |  |

## 12. Out of scope

Any Nautilus live surface (`TradingNode`, live clients, adapters including `sandbox`, network clients); a realism leg
of any kind (C-1); multi-sleeve books, including `S_E1_trend_us`, because `simulate`'s constant weights are a free
daily rebalance (synth §8); Strategy Lab integration (O12); NautilusTrader 2.x (O4); a pilot as a `/quantgen-paper`
study; `BacktestNode`, `ParquetDataCatalog`, streaming and Parquet, which is "never read" (`research_notes/QUANTGEN v2
integration map/00_coordinator_rulings.md:54-55`); a `Cfd` stand-in for fractional SPY, MARGIN accounts,
`allow_cash_borrowing=True`; a Python audit hook, which cannot see Rust sockets (map01 §9.3); any change to the gate,
its thresholds, the ledger code or the study.

## 13. Open questions

Only questions that the defaults of section 2 do not settle:
1. **Windows facts (Step 7A answers them):** does the venv launcher run with the minimal environment, and does the Store
   Python's `sys.executable` start the stub child with it (else the py313 fallback of 8.1; QA-R3-10); does the firewall
   rule bind the interpreter the redirector starts; are F1 and F2 identical in standard precision; is the Windows
   identity install-method independent; does the Store Python redirect the temp dir (3.9's two-form temp root accepts
   either answer; OPS-R4-4); can a normal window read the firewall rule (7A.2's rule check; OPS-R5-1); does the
   owner's network reach 1.1.1.1:443 (R-14; OPS-R5-4); what are the import and run times? All UNVERIFIED.
2. **The owner's ledgers:** do `E1.jsonl` and `C3.jsonl` exist with rows on the owner's machine? If not, R-15 blocks
   that pilot until the owner rules.
3. **Outside this spec:** should a gate-package freeze hash the E1 and C3 ledgers (no caller passes them today; map02
   §3.8)? A pilot as a paper needs its own ruling on "No new pip packages"
   (`.claude/workflows/quantgen-paper-write.js:37`) and `PACKAGES` (`tools/paper/study.py:30`; map04 C7). RELEASES.md
   does not date the v2 cutover, so the v1 backport end is unknown (map01 §10.4). GPLv3 section 2 and FSCMA Art. 101
   could not be fetched (map01 §10.1; map04 §8); they matter only before a publication.

## Appendix A: critic findings K1 to K15, and how this revision resolves them

| # | Finding (synth §10) | Resolution in this spec | # | Finding (synth §10) | Resolution in this spec |
|---|---|---|---|---|---|
| K1 | The Windows wheel is standard precision; volume 1e12 raises there. | Volume 1e9; precision and volume refusals (5.2.4, 6.1); F1, F2 and N1 on Windows through the launch contract before any pilot (Step 7A); cross-precision equality UNVERIFIED (3.6). | K2 | Pilots would run before the code is committed. | Step 7A before the pilots; R-01, R-02; Step 10 commits only outputs. |
| K3 | P11's near-tie exemption and P12 contradict each other. | Superseded by QUANT-3: both engines use QUANTGEN's selection (5.4.2); P11 is a diagnostic; the exempt-flip rule is removed; N4. | K4 | The string rule fails the sandbox's own guard; `check_env.py` would import `nautilus_trader` outside the sandbox. | Rule E covers import machinery outside the sandbox; the sandbox names no denied string; the census is judged in the parent; the parent reads versions and `--check-env` lives in the sandbox (5.6, 6.7). |
| K5 | Adapters are not "unimported"; the live tolerance needs a ruling. | O3 restated; O13; the census as drift detection (5.2.7); the egress layer bounds use (4.4). | K6 | The engine runs the analyzer by default. | `run_analysis=False`, with the `stats_pnls_empty` witness (5.2.3, 6.2). |
| K7 | An installed venv may not reveal its wheel hash. | The `RECORD` digest of 6.7, computed offline for both wheels; equal on Linux for two install methods. | K8 | The cash rate was not pinned and fell back silently to 3%. | DGS3MO md5 pinned; refusal on missing, mismatched or NaN data (R-06); P0 compares the rf array with the study's. |
| K9 | Replica `config_id` equality was untested and type-sensitive. | The Lab's exact `params` expression with `float(cost_bps)`; L1-10. | K10 | Windows encoding hazard; `-I` ignores `PYTHONUTF8`; a relative script path fails. | `-X utf8`; absolute script path; the rules of 3.7, checked by L1-15. |
| K11 | (a) Realism rows count in N. (b) A last-bar order is in flight under latency. | Moot: the realism leg is deferred (C-1). | K12 | Pilot 2's trial count mixes markets. | Family-wide `N_raw + U`; the market-scoped count printed and stored (5.5 step 3). |
| K13 | `--suite` also rewrites the results file. | The redirecting wrapper only; md5 check after every run (8.6). | K14 | The force-stop reset question is answerable. | Closed: `run` resets the flag (`nt:backtest/engine.pyx:1621-1622`). |
| K15 | The runner never said where the cost comes from. | `validate.cost_floor_bp`; refusals (R-07). |  |  |  |

Revision 1's own findings: A-1 (two meanings of `RegisterResult.row_md5`; the bridge records `result.row["row_md5"]`,
5.3.2 step 11); A-2 (bars from strings with the wrangler's constructors, 5.2.4); A-3 (decisions on the parent's floats,
bars checked, 5.2.5); A-4 (the study's 0.03-percent leading DGS3MO fill; the bridge refuses NaN, R-06); A-5 (moot, C-1).

## Appendix B: referee rounds

Each referee reviews the current revision. A referee who returns nothing is REVIEW_INCOMPLETE, never "no objections",
unless the owner records a substitution. The Claude referee ran with the repo clone as its working directory; the clone
holds no `.env` (GOVERNANCE-12). Reports (`round<k>_claude_<persona>.md`, 2026-10-26) and rulings
(`round<k>_rulings.md`) are in `docs/superpowers/specs/2026-10-26-nautilus-review/`.

| Referee | Channel | Round 1 (Revision 1) | Round 2 (Revision 2) | Round 3 (Revision 3) | Round 4 (Revision 4) | Round 5 (Revision 5, targeted) |
|---|---|---|---|---|---|---|
| Claude, security | subagent in the repo clone | REJECT (1 blocker) | AGREE (2 minor) | AGREE, pressed (2 minor) | AGREE (3 minor) | AGREE (2 minor) |
| Claude, quant | same | ACCEPT WITH CHANGES | ACCEPT WITH CHANGES (2 major, 5 minor) | ACCEPT WITH CHANGES (1 major, 2 minor) | AGREE (3 minor) | not run (AGREE in round 4) |
| Claude, QA | same | ACCEPT WITH CHANGES | ACCEPT WITH CHANGES (5 major, 9 minor) | AGREE (12 minor) | AGREE (6 minor) | not run (AGREE in round 4) |
| Claude, ops | same | ACCEPT WITH CHANGES | ACCEPT WITH CHANGES (2 major, 6 minor) | ACCEPT WITH CHANGES (2 major, 7 minor) | ACCEPT WITH CHANGES (1 major, 4 minor) | AGREE (5 minor) |
| Claude, governance | same | ACCEPT WITH CHANGES | ACCEPT WITH CHANGES (3 major, 3 minor) | AGREE (7 minor) | AGREE (5 minor) | not run (AGREE in round 4) |
| GPT | Codex CLI on the owner's machine (quota resets 2026-10-30 14:40) | pending | pending | pending | pending | pending |
| Gemini | `agy` on the owner's machine | pending | pending | pending | pending | pending |
| Owner-recorded substitute | | none | none | none | none | none |

**Round 1 issues** (rulings in `round1_rulings.md`; none rejected; C-n are the moderator's own items).

| Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C-1 | major | ACCEPT (moderator): defer the realism leg | 1, O7, 5.2.3, 5.2.5, 5.2.7, 6.1, 6.4, 8.2 (N3 retired), 12, App. A K11 | C-2 | major | ACCEPT (moderator): strategy refuses non-BACKTEST | 5.2.1, 5.2.3, 5.2.5, 7 C-15, 8.4 test 8 | C-3 | minor | ACCEPT (moderator): see QUANT-2 | 5.5, 11 risk 10 |
| C-4 | minor | ACCEPT (moderator): README counts | 5.8, Steps 4 and 10 | SECURITY-1 | blocker | ACCEPT | 3.12, 4.3, 4.4, 5.2.2, 5.6 rule F, 8.5, Step 7A | SECURITY-2 | major | ACCEPT | 5.2.7, O13, 11 risks 2-3 |
| SECURITY-3 | major | ACCEPT-MODIFIED | 5.2.8, 3.3, O3, 8.4 test 5 | SECURITY-4 | major | ACCEPT (folded into SECURITY-1) | 4.4, 12 | SECURITY-5 | major | ACCEPT | 5.6 (pin test), Step 4 |
| SECURITY-6 | minor | ACCEPT | 5.6 constants, rules C1 and D | SECURITY-7 | minor | ACCEPT-MODIFIED | 5.6 rule A | QUANT-1 | major | ACCEPT | 5.3.2 step 7, 5.4.1 P0, 6.5 `parity_scope` |
| QUANT-2 | major | ACCEPT | 5.5 steps 4-5, 6.3, 6.5 | QUANT-3 | major | ACCEPT | 5.4.2, 5.4.1 P11 and P12 | QUANT-4 | major | ACCEPT | O11, 5.5 step 3, 6.6, 10.1, 10.2 |
| QUANT-5 | major | ACCEPT | 5.4.1 P7 | QUANT-6 | major | ACCEPT | 6.5, 6.6, 10.1, 10.2 | QUANT-7 | minor | ACCEPT | 10.3 |
| QUANT-8 | minor | ACCEPT (moot, C-1) | 1 | QUANT-9 | minor | ACCEPT | 5.4.1 P10 | QUANT-10 | minor | ACCEPT | 8.2 N6, 8.4 test 11, Step 7 |
| QUANT-11 | minor | ACCEPT | 6.5 `rules.engine` | QA-1 | major | ACCEPT | 3.3, 5.3.1, 5.7, 8.3 test 32 | QA-2 | major | ACCEPT | 6.8, 8.2 (N1) |
| QA-3 | major | ACCEPT (moot for the realism parts) | 8.2 (N3 retired) | QA-4 | major | ACCEPT | 6.1, 6.6, 5.3.2 step 1 | QA-5 | major | ACCEPT | 6.6, 5.3.2 step 5 |
| QA-6 | major | ACCEPT | 6.1, 6.2, 5.3.5, Step 8 | QA-7 | major | ACCEPT | 5.3.1, 8.3 tests 3 and 6 | QA-8 | major | ACCEPT | 5.4.1 and 7 (Control columns), 8.2 N5 |
| QA-9 | major | ACCEPT | 5.5 steps 8-9, 6.3, 6.5 | QA-10 | major | ACCEPT | 6.7 | QA-11 | minor | ACCEPT-MODIFIED | 5.2.7, 6.8 |
| QA-12 | minor | ACCEPT | 8.2 N4, 8.3 test 14, 8.4 test 2, 5.6 | QA-13 | minor | ACCEPT | 5.2.5, 7 C-04 | QA-14 | minor | ACCEPT | 8.4 test 5 |
| QA-15 | minor | ACCEPT | 8.5 | QA-16 | minor | ACCEPT | 3.7, 4.3, 8.3 tests 15-16 | QA-17 | minor | ACCEPT | 3.9, 5.3.1, 7 R-10 |
| QA-18 | minor | ACCEPT | 5.3.2 step 2, 5.3.5 | QA-19 | minor | ACCEPT | 5.4.1 P1 | QA-20 | minor | ACCEPT (moot after QUANT-3) | 5.4.2, Step 7 |
| QA-21 | minor | ACCEPT | Steps 1a and 2 | OPS-1 | major | ACCEPT | 4.3, 8.4 test 10 | OPS-2 | major | ACCEPT | 3.7 |
| OPS-3 | major | ACCEPT | 5.3.2 step 2, 7 R-02, Step 7A | OPS-4 | major | ACCEPT | 3.4, 6.7 | OPS-5 | major | ACCEPT | 3.1, 5.1, 8.3 test 22 |
| OPS-6 | major | ACCEPT | 5.3.5, 6.3, 7 G-07, Step 8 | OPS-7 | major | ACCEPT | 5.2.7, 6.7, Step 7A | OPS-8 | major | ACCEPT | Step 7A, 5.8 (runbook file) |
| OPS-9 | minor | ACCEPT | 4.3 | OPS-10 | minor | ACCEPT | 4.3, 5.2.3, 5.3.2 steps 2 and 5, 5.3.5 | OPS-11 | minor | ACCEPT | 3.7, 6.6 |
| OPS-12 | minor | ACCEPT | 5.5 step 8, 6.3 | OPS-13 | minor | ACCEPT | 4.4, 6.7 | OPS-14 | minor | ACCEPT | O9, 3.1, 5.1 |
| OPS-15 | minor | ACCEPT | 3.8, 5.3.5 | GOVERNANCE-1 | major | ACCEPT | Owner context, Status | GOVERNANCE-2 | major | ACCEPT | O3, 1 |
| GOVERNANCE-3 | major | ACCEPT | 5.3.2 step 1, 6.6, 7 R-15 | GOVERNANCE-4 | major | ACCEPT | 3.9, 5.3.2 step 5, 7 R-10 | GOVERNANCE-5 | major | ACCEPT | 3.9, O6, Step 7, 10.4 |
| GOVERNANCE-6 | major | ACCEPT (as QUANT-2) | 5.5 | GOVERNANCE-7 | major | ACCEPT | 3.1, 8.3 test 22 | GOVERNANCE-8 | minor | ACCEPT | O14, O15 |
| GOVERNANCE-9 | minor | ACCEPT | 3.8, 7 R-16 | GOVERNANCE-10 | minor | ACCEPT | 5.6, O2 | GOVERNANCE-11 | minor | ACCEPT | Owner context, Step 7A |
| GOVERNANCE-12 | minor | ACCEPT | Step 1a, Appendix B | GOVERNANCE-13 | minor | ACCEPT | Step 2 |  |  |  |  |

Round 1, applied with a stated interpretation, each explained where applied: C-2 (no strategy environment accessor in
1.231.0, so `on_start` checks the clock class the kernel's environment selects, and `run` checks
`engine.kernel.environment`, 5.2.5); SECURITY-1 (with `import sys` banned, the census comes from `-X importtime`,
versions from the venv's files, and C-10 checks the built environment, 5.2.7, 6.7); SECURITY-6 (`api_key`, `api_secret`
denied under `tools/nautilus/` only, as `data/fmp/quote_client.py:110, 115` use `api_key`); SECURITY-5 (the five named
sets pinned as ruled, plus a second pin for the rule-F lists, pattern and verbs); QUANT-1 (P0a before registration
refuses, P0b after withholds); QUANT-5 (superseded by QUANT-R2-3 and QA-R2-7); GOVERNANCE-9 (no paper_live lock file
exists, so ledger modification times are checked); OPS-8 with SECURITY-1 (the venv comes from the dedicated interpreter
and installs offline).

**Round 2 issues** (rulings in `round2_rulings.md`; none rejected). The reports label 12 major and 25 minor new issues;
the rulings' tally says 26 minor. Four round-1 issues were still open and are closed here.

| Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in |
|---|---|---|---|---|---|---|---|---|---|---|---|
| QA-1 | major | ACCEPT (open from round 1; with QA-R2-1) | 3.3, 5.3.1, 8.3 tests 19, 32 | QA-7 | major | ACCEPT (open from round 1; with QA-R2-1) | 5.3.1, 8.3 tests 6, 23 to 25 | OPS-8 | major | ACCEPT (open from round 1) | 5.3.1 `--handoff-report`, 5.8, Steps 7A and 8 |
| GOVERNANCE-5 | major | ACCEPT (open from round 1; with GOVERNANCE-R2-3) | 3.9, 5.3.1, 7 R-10, 8.3 test 9 | SECURITY-R2-1 | minor | ACCEPT (interpreted, below) | 5.2.2, 5.6 rule F4 | SECURITY-R2-2 | minor | ACCEPT | 5.6, Appendix B |
| QUANT-R2-1 | major | ACCEPT | 5.3.2 step 6, 7 R-06, 8.3 test 7 | QUANT-R2-2 | major | ACCEPT | 5.5 step 5, 6.3, 7 G-02, 8.2 N8, 8.3 tests 2, 14 | QUANT-R2-3 | minor | ACCEPT | 5.4.1 P7, 8.2 N7 |
| QUANT-R2-4 | minor | ACCEPT | 10.1, 10.2, 8.3 test 30 | QUANT-R2-5 | minor | ACCEPT (interpreted, below) | 5.5 step 5, 6.3, 7 G-08, 8.3 test 29, 10.3 | QUANT-R2-6 | minor | ACCEPT | 8.2 F1r, N6 and series, 8.3 tests 1, 2, 8.4 test 7 |
| QUANT-R2-7 | minor | ACCEPT | 5.2.4, 5.3.2 step 5, 7 R-05 | QA-R2-1 | major | ACCEPT | 5.3.1, 5.3.2 steps 0 to 2, 8.3 tests 6, 19, 23 to 25 | QA-R2-2 | major | ACCEPT | 5.3.1, 8.1 stub child, 7 G-03, 8.3 tests 3, 26, 27, 31 |
| QA-R2-3 | major | ACCEPT | 8.3 tests 5, 25 | QA-R2-4 | major | ACCEPT (as QUANT-R2-1) | 5.3.2 step 6, 8.3 test 7 | QA-R2-5 | major | ACCEPT | 4.3, 5.8, Steps 3 to 7 |
| QA-R2-6 | minor | ACCEPT | 5.3.1, 6.2, 6.8, 8.3 test 33 | QA-R2-7 | minor | ACCEPT | 5.4.1 P7, 8.3 test 2 | QA-R2-8 | minor | ACCEPT | 6.1, 7 C-05, 8.4 test 5a |
| QA-R2-9 | minor | ACCEPT (as SECURITY-R2-1) | 5.2.2, 5.6 rule F4 | QA-R2-10 | minor | ACCEPT | 5.3.2 step 3, 7 R-03, 8.3 test 27 | QA-R2-11 | minor | ACCEPT | 5.2.5, 7 C-06 |
| QA-R2-12 | minor | ACCEPT | 8.2 series, N6, N7, 8.4 test 7 | QA-R2-13 | minor | ACCEPT | 3.3 | QA-R2-14 | minor | ACCEPT | 5.8, 6.7, 8.3 tests 15, 17 |
| OPS-R2-1 | major | ACCEPT | 5.3.1, Step 7A | OPS-R2-2 | minor | ACCEPT | O9, 4.4, 6.3, 6.7, Step 7A | OPS-R2-3 | major | ACCEPT | 5.3.5, 6.3, 8.3 test 34, 11 risk 23 |
| OPS-R2-4 | minor | ACCEPT | 4.3, 8.3 test 27 | OPS-R2-5 | minor | ACCEPT | 8.4 tests 5a, 5b, Step 7A | OPS-R2-6 | minor | ACCEPT | 5.3.5, 7 (Remedy column) |
| OPS-R2-7 | minor | ACCEPT (interpreted, below) | 5.3.1, 5.3.5, 6.3, 7 R-17, 8.3 test 5, Step 8 | OPS-R2-8 | minor | ACCEPT | 4.3, 4.4, 6.7, 8.3 test 23 | GOVERNANCE-R2-1 | major | ACCEPT | Status, Owner context, O8, Steps 1a and 1b |
| GOVERNANCE-R2-2 | major | ACCEPT (interpreted, below) | Owner context, 5.3.2 step 1, 6.6, 7 R-11, 8.3 test 19, Step 7A | GOVERNANCE-R2-3 | major | ACCEPT | 3.9, 5.3.1, 7 R-10, 8.3 test 9 | GOVERNANCE-R2-4 | minor | ACCEPT (interpreted, below) | 5.3.1, Step 2 |
| GOVERNANCE-R2-5 | minor | ACCEPT-MODIFIED: target `origin/main` | Owner context, Step 7A | GOVERNANCE-R2-6 | minor | ACCEPT | 1, 3.7, 5.2.5, 5.6, Appendix B | C-5 | minor | ACCEPT (moderator; finding below) | 5.2.1, 5.2.2, 5.2.9, 8.5 |
| C-6 | minor | ACCEPT (moderator; growth below) | whole spec |  |  |  |  |  |  |  |  |

Round 2, applied with a stated interpretation:
- QUANT-R2-5 (G-08 "exactly"): `sc_qg` scores the 9-decimal closes of QUANT-R2-7, so it can equal a card computed on
  unrounded closes bit for bit only if no close changed. G-08 is exact when `rounding_changed` is false, and otherwise
  uses the referee's tolerances (1e-6; one bootstrap draw for `bench_p`) on the float fields. Superseded in Revision 4
  by QUANT-R3-1 and QUANT-R3-3: `n_years` by the calendar-year rule, every float within 1e-9 whatever
  `rounding_changed` says, and no exact float comparison (5.5 step 5).
- SECURITY-R2-1 (F4 wording): F4 keeps its `Subscript` scope. Read alone, "an Attribute chain rooted at a module alias"
  would flag every `json.dumps`.
- QA-R2-2 with QUANT-R2-2: one scorer seam, `score_fn`, serves L1-14 and the run-level case; N8 tests the pure
  `parity.agree`. OPS-R2-7: the re-run policy binds rehearsal too, so L1-5 passes `rerun_of`.
- GOVERNANCE-R2-2: `owner_confirmed` quotes `code_sha256` as well as `table_sha256`, as the referee proposed.
  GOVERNANCE-R2-4: the constraint reads "Claude never runs of-record mode"; a call refused in argument validation is not
  a run (5.3.1).
- C-5 finding: the skeleton showed that `platform.system()` trips rule F6 (its callee name is in `SANDBOX_OS_CALLS`), so
  the sandbox uses `platform.uname()` (5.2.1, 5.2.2), and 8.5 gains that control. C-6: Revision 2 had 1,500 lines;
  Revision 3 has 1,663 (+10.9 percent; +23 percent in bytes, mostly the skeleton of 5.2.9,
  the Step 7A commands and the series code that C-5, OPS-R2-1 and QA-R2-12 require).

**Round 3 issues** (rulings in `round3_rulings.md`; none rejected). 3 major and 30 minor new issues, and the
moderator's C-7 and C-8; QUANT-R2-5(b), the one earlier issue still open, closes with QUANT-R3-1.

| Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C-7 | minor | ACCEPT (moderator): Revision 3's nine deviations stand | Appendix B (round 2) | C-8 | minor | ACCEPT (moderator): close after round 4 | Status, Owner context, O8, Step 1a | QUANT-R3-1 | major | ACCEPT (first option) | 5.5 step 5, 6.3, 7 G-08, 8.3 test 29, 10.3, Appendix B |
| QUANT-R3-2 | minor | ACCEPT | 5.3.2 step 6, 8.2 series, 8.4 test 12, 10.2, Step 7 | QUANT-R3-3 | minor | ACCEPT | 5.3.2 step 1, 5.5 step 5, 6.6, 7 R-11 and G-08, 8.3 test 29, 10.2 | OPS-R3-1 | major | ACCEPT | 7 R-03, 8.3 test 22 |
| OPS-R3-2 | major | ACCEPT | 5.2.7, 5.3.1, 8.3 test 35, Step 7A.2 | OPS-R3-3 | minor | ACCEPT | Step 7A.2, 7A.3 | OPS-R3-4 | minor | ACCEPT | 4.4, 5.3.1 `--handoff-report` |
| OPS-R3-5 | minor | ACCEPT | 5.3.1, 5.3.2 step 0, 5.3.5, 6.3, 6.6, 7 R-17, 8.3 test 5 | OPS-R3-6 | minor | ACCEPT | 6.6, 8.3 test 19, Step 7A.4 | OPS-R3-7 | minor | ACCEPT | Step 7A.2, Merge |
| OPS-R3-8 | minor | ACCEPT (`SetThreadExecutionState`) | 5.3.5, Step 8 | OPS-R3-9 | minor | ACCEPT | 3.7, 4.3, 5.3.2 step 2, 5.7, 7 R-02 and R-14 | QA-R3-1 | minor | ACCEPT | 4.3, 5.8, 8.3 test 5, Steps 5 to 7 |
| QA-R3-2 | minor | ACCEPT | 5.2.7, 5.4.1 P13, 7 C-01 to C-04 and C-15, 8.1, 8.3 test 27 | QA-R3-3 | minor | ACCEPT (as OPS-R3-5) | 5.3.5, 6.6, 8.3 test 5 | QA-R3-4 | minor | ACCEPT | 5.2.9, 5.4.3, 6.1, 8.4 test 5a |
| QA-R3-5 | minor | ACCEPT | 5.3.1, 8.1 | QA-R3-6 | minor | ACCEPT | 5.3.5 | QA-R3-7 | minor | ACCEPT | 5.3.1, 5.3.2 steps 2 and 7, 5.3.5, 8.3 tests 6, 20, 34 |
| QA-R3-8 | minor | ACCEPT | 5.2.5, 5.2.7, 5.2.9, 6.2, 6.8, 8.2 N1, 8.3 test 33 | QA-R3-9 | minor | ACCEPT | 5.2.5, 5.2.9, 8.1 | QA-R3-10 | minor | ACCEPT | 8.1, 13.1, Step 7A |
| QA-R3-11 | minor | ACCEPT | 8.2 N6, 8.4 tests 7 and 12 | QA-R3-12 | minor | ACCEPT | O13, 8.3 test 12, Step 8 | SECURITY-R3-1 | minor | ACCEPT | 5.2.9, 8.5 |
| SECURITY-R3-2 | minor | no change; one sentence | 5.6 | GOVERNANCE-R3-1 | minor | ACCEPT | 4.1, 6.6, 8.3 test 19, Step 10 | GOVERNANCE-R3-2 | minor | ACCEPT | 3.3, 8.3 test 10 |
| GOVERNANCE-R3-3 | minor | ACCEPT | 3.9, 5.3.1, 6.6, 7 R-10, 8.3 test 9, Step 2 | GOVERNANCE-R3-4 | minor | ACCEPT | Step 7A.3, Step 10 | GOVERNANCE-R3-5 | minor | ACCEPT | Owner context, Steps 1b and 2 |
| GOVERNANCE-R3-6 | minor | ACCEPT | Status, Steps 1a and 2, 10.4, Appendix B | GOVERNANCE-R3-7 | minor | ACCEPT | 3.10, Step 10 |  |  |  |  |

Round 3, applied with a stated interpretation:
- Choices the referee left open: L1-5 moves to Step 7 (QA-R3-1's first option); G-08's comparison is the pure
  `parity.reference_drift`, so L1-29 and L2-12 call it directly (QUANT-R3-1, QUANT-R3-2); L2-12's dates start
  2001-01-01; the hand-off tag on Linux is `linux_x86_64`, not the wheel's `manylinux_2_35_x86_64` (OPS-R3-4).
- QA-R3-2: `--doctor` also takes C-01 and C-02, so every check the parent re-derives has a layer-1 control.
- GOVERNANCE-R3-6 with C-8: Step 1a is open again, so Steps 2 to 7 wait for round 4 to close it.
- Applied from referee notes, not issues: P6 does not use `c_leg`, and P7 is stated in `Decimal` (quant); goldens hold
  prices at 9 decimals (QA); 13.1 asks whether the Store Python redirects the temp dir (ops).
- C-6 growth: Revision 3 had 1,663 lines; Revision 4 has 1,772 (+6.6 percent), mostly this table, the
  Step 7A re-entry lines and the new tests and seams.

**Round 4 issues** (rulings in `round4_rulings.md`; none rejected). 1 major and 21 minor new issues, and the
moderator's C-9; OPS-R3-2(a), the one earlier issue still open, closes with OPS-R4-1. Ops and security ran a targeted
round 5 on Revision 5 (below).

| Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C-9 | minor | ACCEPT (moderator): the quant probe's KRX re-score goes into 10.4 | 10.4 | OPS-R4-1 | major | ACCEPT (re-entry keyed on `$q\wheels` and the rule) | 5.3.1 `--handoff-report`, Step 7A.2 | OPS-R4-2 | minor | ACCEPT | 5.2.7, 7 R-14, 8.3 test 35, Step 7A.2 |
| OPS-R4-3 | minor | ACCEPT | 5.3.1 `--handoff-report` | OPS-R4-4 | minor | ACCEPT | 3.9, 5.3.1, 6.6, 13.1 | OPS-R4-5 | minor | ACCEPT | 5.2.7, 5.3.5, 5.8, Step 7A.2 |
| SECURITY-R4-1 | minor | ACCEPT (wording) | 5.2.2, 11 risk 2 | SECURITY-R4-2 | minor | ACCEPT (as OPS-R4-1) | Step 7A.2 | SECURITY-R4-3 | minor | ACCEPT | 4.4, 7 R-14, Step 7A.2 |
| QUANT-R4-1 | minor | ACCEPT | 6.6, 8.3 test 29, 8.4 test 12 | QUANT-R4-2 | minor | ACCEPT | 5.3.2 step 1, 5.5 step 5, 6.3, 7 R-11 and G-08 | QUANT-R4-3 | minor | ACCEPT | 5.3.2 step 7, 5.5, Step 9 |
| QA-R4-1 | minor | ACCEPT | 5.3.2 step 7, 8.3 test 20 | QA-R4-2 | minor | ACCEPT | 3.9, 5.3.1, 5.3.2 step 1, 7 R-10, 8.3 test 9 | QA-R4-3 | minor | ACCEPT | 5.2.7, 5.3.3, 7 C-02, C-09 and C-11, 8.1 |
| QA-R4-4 | minor | ACCEPT | 5.2.7, 5.3.1, 8.1, 8.3 tests 3 and 35, Step 7A | QA-R4-5 | minor | ACCEPT | 5.3.2 step 6, 8.3 tests 3 and 33, Step 7A | QA-R4-6 | minor | ACCEPT | 5.3.5 |
| GOVERNANCE-R4-1 | minor | ACCEPT | 5.3.1, 6.6, 8.3 test 36, Steps 7 and 7A | GOVERNANCE-R4-2 | minor | ACCEPT | Owner context, Steps 7A.1, 7A.4 and 10 | GOVERNANCE-R4-3 | minor | ACCEPT | Step 2 |
| GOVERNANCE-R4-4 | minor | ACCEPT | 5.3.2 step 1, 6.3, 7 R-11, 8.3 test 19, 10.2, Step 9 | GOVERNANCE-R4-5 | minor | ACCEPT | Status, O8, Step 1a, 10.4, Appendix B |  |  |  |  |

Round 4, applied with a stated interpretation:
- OPS-R4-1: the ruling's re-entry key, `$q\wheels`, replaces the referee's dist-info key. A download that failed
  halfway leaves the folder, and the install line, never passed before, then fails; Step 7A.2 adds that the owner
  deletes the folder and re-enters, which reaches the download line, as no rule exists before a first passing install.
- QA-R4-4 with OPS-R4-2: `record_baseline` takes a keyword `tracked`, which the CLI fills from `git ls-files`, so the
  function stays pure and L1-35 tests both cases.
- QUANT-R4-1: all three proposed points: the reference built as the card was (8.4 test 12), named in the rehearsal
  table as a temp `reference_card` (6.6), and a layer-1 twin (8.3 test 29). GOVERNANCE-R4-1's test is the new L1-36,
  at Step 7, where the committed tables exist.
- SECURITY-R4-1: wording only, as ruled; the optional rule-F hardening is not applied, so rules A to F, the 5.2.9
  skeleton and both pins are unchanged.
- C-6 growth: Revision 4 had 1,772 lines; Revision 5 has 1,849 (+4.3 percent; +6.5 percent in bytes), mostly this
  table, the Step 7A lines and the new test cases.

**Round 5 issues** (targeted: ops and security on Revision 5; rulings in `round5_rulings.md`; none rejected). Both
AGREE; no blocker, no major, 7 minor new issues; nothing open from earlier rounds. Under C-8 the moderator applied them
in Revision 6 and closed Step 1a without a further round (`round5_rulings.md` §1; Status, O8, Step 1a).

| Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in | Issue | Sev. | Ruling | Addressed in |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPS-R5-1 | minor | ACCEPT (one fix with SECURITY-R5-1): the re-entry key is whether the rule exists, shown by a rule check line | Step 7A.2, 13.1 | OPS-R5-2 | minor | ACCEPT: a throw in the five git lines stops the block; `git merge --ff-only origin/claude/amazing-gauss-tdiguu` | Steps 7A.2 and 7A.3 | OPS-R5-3 | minor | ACCEPT: exit 0 for a replaced untracked baseline and for a tracked path with no file | 5.2.7, 8.3 test 35 |
| OPS-R5-4 | minor | ACCEPT: the control-connect remedy, the control error printed first | 4.4, 7 R-14, 13.1 | OPS-R5-5 | minor | ACCEPT: "if absent"; the layer-2 tests hold `ES_CONTINUOUS` and `ES_SYSTEM_REQUIRED`; `$ProgressPreference` | 5.7, Step 7A.2 | SECURITY-R5-1 | minor | ACCEPT (as OPS-R5-1) | Step 7A.2, 7 R-14 |
| SECURITY-R5-2 | minor | ACCEPT; already met (below) | Step 7A.2, unchanged |  |  |  |  |  |  |  |  |

Round 5, applied with a stated interpretation:
- OPS-R5-1 with SECURITY-R5-1: the observable key replaces Revision 5's `$q\wheels` key and its delete-and-re-enter
  sentence, and so supersedes the round-4 interpretation of OPS-R4-1 above. The ruling's "elevated
  `Remove-NetFirewallRule` line" needs a line of its own, so the firewall line becomes two elevated lines, remove and
  then create, and R-14's remedy names both. The rule check sits just before the download line, so a first attempt runs
  it too and sees no rule. That a normal window can read the rule is UNVERIFIED (13.1). The ruling does not include
  the referee's other two proposals, a stop after a second failure of the same line and wheel and dist-info listings
  in the hand-off report, so they are not applied: a red error still skips to the hand-off, and a re-entry before the
  rule exists downloads only the files still missing.
- OPS-R5-2: the throw text is the referee's, "fast-forward: ask Claude"; Revision 5's "pull line" is now "the
  fast-forward line"; the hand-off line's comment and 7A.3's "whatever happened" now exclude a stop in the git lines.
- OPS-R5-3: the referee's optional 7A.4 `git rm` of a changed tracked baseline is not in the ruling and is not applied.
- OPS-R5-4: R-14's Condition column also names the failed control connect, which `--egress-record` already refuses
  (SECURITY-R4-3); the probe target stays fixed.
- OPS-R5-5: the ruling takes the suite-held request, not the referee's Settings sentence: `0x80000001` while the
  layer-2 tests run, reset with `0x80000000` in a `finally`.
- SECURITY-R5-2: Revision 5's line already read `python -B -m tools.nautilus.runner --fixtures --record-baseline; if
  ($LASTEXITCODE) { throw "fixtures" }`, as Revision 4's did and as the ops walk-through records; appending the throw
  again would duplicate it, so the line is unchanged and the ruling is met.
- Also updated: the Inputs and citation keys now name HEAD `b7f991a`, which adds only this spec and the review folder;
  10.4 gains the round-5 referees' row.
- C-6 growth: Revision 5 had 1,849 lines; Revision 6 has 1,906 (+3.1 percent; +3.3 percent in bytes), mostly
  this table and the Step 7A lines.

**Outside review.** GPT and Gemini review the current revision. Their issues and the owner's rulings go here.

| Issue | Raised by | Ruling | Addressed in |
|---|---|---|---|
| | | | |
