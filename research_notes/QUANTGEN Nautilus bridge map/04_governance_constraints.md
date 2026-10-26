# 04. Governance: every QUANTGEN rule the Nautilus bridge must obey, and every conflict

Scope: the rules, guards and processes that bind a NautilusTrader bridge in QUANTGEN, and where the bridge collides
with them. It answers seven questions: (a) dependencies, (b) T-RO-01, (c) hermeticity, (d) the frozen-study pins,
(e) the QUANTGEN/TRADEGEN boundary, (f) the house process, (g) Korean law. The engine API is in map 01, the gate and
ledger in map 02, the pilot and parity in map 03. This map builds nothing and decides nothing. Every change it
proposes needs an owner ruling.

Method. I read the repo at commit `f5742ab` (Linux clone). I ran the repo's own T-RO-01 scanner, read-only, on probe
files in a temporary tree. I ran a small synthetic backtest in the session venv under `strace` and in a network-less
namespace. I asked pip to resolve a Nautilus install against the global package set in a throwaway
`--system-site-packages` venv (`--dry-run`, nothing installed). The global interpreter still has numpy 2.3.5,
pandas 2.3.3, scipy 1.18.0 and no `nautilus_trader` (checked after every probe). I wrote no ledger row and changed
no tracked file.

Citation keys.

- `file:line` with no prefix is a QUANTGEN path at `f5742ab`.
- `nt:<path>:<line>` is the installed wheel source, `site-packages/nautilus_trader/<path>`, version 1.231.0
  (same convention as map 01).
- `map01 §n`, `map02 §n`, `map03 §n` are the sibling maps in this folder.
- `gov:<name>` is a measured result from my probes. The scripts and logs are outside the repo, in
  `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/gov_probe/`
  (`herm_probe.py`, `run_*/strace.log`, `dryrun_report.json`, `dryrun_eager.json`, `scan/proto_scan.py`).
- The venv is the session's `scratchpad/ntvenv` (Python 3.13.17, nautilus_trader 1.231.0, numpy 2.3.5,
  pandas 2.3.3, no scipy; map01 §1). The task brief mentioned "the venv described below"; none was described, so I
  used this one.
- External claims cite a URL. Anything I could not check is marked UNVERIFIED.

---

## 0. Findings

1. **Adding Nautilus is a new dependency under every reading of the house rule.** The rule is written in five
   places. One of them bans `pyarrow` by name, and Nautilus requires `pyarrow>=25`
   (`research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55`; wheel METADATA). The rule has
   always been "not without the owner", not "never" (`research_notes/QUANTGEN v2 integration map/spec_tests_registry.md:401`).
   So the owner must rule. The cleanest shape changes nothing in the global interpreter, `requirements.txt`,
   `requirements-dev.txt` or `pyproject.toml`. It adds one hash-pinned `requirements-nautilus.txt` for a separate
   venv, called only as a subprocess (section 2).
2. **A plain global install would not move numpy, pandas or scipy. An eager upgrade would.** pip's default
   resolution adds 8 packages and leaves the three pins alone (`gov:dryrun_report.json`). With
   `--upgrade --upgrade-strategy eager` it moves numpy 2.3.5 to 2.5.4 and pandas 2.3.3 to 3.1.0
   (`gov:dryrun_eager.json`). That fails frozen_guard clause (d) (`tests/frozen_guard.py:85-91`). On Linux even the
   default install downgrades uvloop 0.23.0 to 0.22.1 (section 5).
3. **The sandbox strategy fails T-RO-01 today, and T-RO-01 misses the real danger.** Measured on
   `tools/nautilus/sandbox.py`: two hits, the text `submit_order` and the call `.submit_order()`
   (`tests/macro_m0_harness.py:29, 45, 85, 100-101`). A file that imports `TradingNode`, a Binance adapter and
   `nautilus_pyo3`, or that loads `nautilus_trader.adapters.betfair` through `importlib`, gets zero hits
   (`gov:scan`). This repeats map01 §9.2 and adds the dynamic-import case.
4. **The narrowest fix is one allow-listed file under `tools/`, not under `core/`.** `tools/` is in T-RO-01's scope
   (`tests/macro_m0_harness.py:63`) but not in the raw-text safety scans test_08/09 (`tests/acceptance.py:50-75`),
   and not in the app package (`pyproject.toml:22-24`). In `core/` the sandbox would also fail test_08, which scans
   comments too, and would need a second test change. A prototype amendment passes the sandbox, catches all four
   negative probes and finds zero hits in the real 154-file tree (`gov:scan`). This differs from map01 §9.3, which
   proposed `core/bridge/`.
5. **DO-NOT-BUILD item 21 needs its own owner reading.** It forbids "a broker execution adapter, inside this
   programme" (`QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:6162`). The Nautilus
   wheel ships 15 adapter packages, including Binance, Interactive Brokers, Betfair and Polymarket (map01 §9.1). The
   bridge never imports them, and they sit in a separate venv. The owner should still state that an unimported library
   in a separate venv is not "inside this programme".
6. **A backtest makes no network call and writes no file, as measured.** Under `strace -f`, a full synthetic run made
   zero `socket`, `connect`, `bind` or `sendto` calls and opened no file for writing (`gov:run_nofile/strace.log`).
   It also completed inside `unshare -n`, with no network at all (`gov:run_nonet`). HOME, TMPDIR and the working
   directory were empty afterwards. With file logging switched on, it writes one log into the **working directory**,
   named with the trader id, the date and a random UUID (`gov:run_filelog`;
   `nt:common/config.py:627-634`).
7. **T-HERM-01 cannot guard a subprocess.** Its patches are attributes of the running Python process
   (`tests/macro_acceptance.py:52-98`). A child process does not inherit them, and the Rust core would bypass them
   anyway. The bridge needs its own guard: a scrubbed environment, a temp working directory, a static deny-list and a
   post-run `sys.modules` check (section 4).
8. **`config.py` loads `.env` into the parent process.** A child started with the default environment would receive
   every API key (`config.py:25-29`). The paper pipeline already ruled against exactly this for the referee CLIs
   (`docs/superpowers/plans/2026-10-23-execution-record.md:93`, ruling R9). The Nautilus child must get an explicit,
   minimal environment.
9. **Live trading with Nautilus belongs to TRADEGEN, and most of its adapters are grey or illegal for a Korean
   resident.** Polymarket (illegal), Betfair sports betting (illegal), Binance/Bybit/OKX (grey or blocked),
   Hyperliquid (grey), a direct Interactive Brokers account (grey, leaning non-compliant)
   (`reports/Korean resident trading venue legality.md:15, 21, 27-28, 30, 50`). No KIS or Upbit adapter ships
   (map01 §9.1). That is TRADEGEN's problem, but it fixes the boundary: QUANTGEN never imports `live` or `adapters`.
10. **The full house process cannot finish in this container.** Codex, agy and Tectonic are absent (`which` found
    none). A Linux full run gives 738 PASS / 8 FAIL / 124 NOT_RUN against the committed 749 / 0 / 121
    (`scratchpad/baseline_results.json`; `qa/acceptance_results.json`). Three FAILs are frozen_guard, because this
    clone has no `studies-of-record-2026-10-23` tag. The spec, the Claude referee round, the plan, the code and the
    bridge's own tests can run here. GPT and Gemini rounds, the full run of record and clause (d) need the owner's
    Windows machine (section 7).
11. **Korean law adds little for a local engine.** There is no account, no platform terms and no upload. What remains:
    LGPL-3.0 if QUANTGEN is ever conveyed, data licences of the inputs, and the research-mode line of the legality
    report: no order routing, no published signals (`reports/Korean resident trading venue legality.md:100`). One new
    data-provenance item: the tech-fund scripts read a SPY file in QuantConnect Lean format whose licence is not
    recorded (`QUANTGEN_techfund_research_bundle/QUANTGEN_techfund_research/scripts/us_common.py:179-189`).

---

## 1. Rule register

Each row is a standing rule, where it is written, and what it means for the bridge. "Conflict" means the bridge as
planned breaks the rule's letter. "OK" means it can comply with no rule change.

| # | Rule | Source | Bridge impact | Status |
|---|---|---|---|---|
| R1 | No broker order path; QUANTGEN goes no further than paper trading | `README.md:34-38`; `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:25-27`; P0 `README.md:367-372` | Orders only inside `BacktestEngine` against Nautilus's simulated exchange | OK in substance; see R2 |
| R2 | T-RO-01 static scan: forbidden text, calls and imports in core/, data/, ui/, main.py, config.py, docs/*.py, tools/, papers/ and workflow YAML | `tests/macro_m0_harness.py:25-146`; council spec row `QUANTGEN_MACRO_INTEGRATION.md:5605` | `self.submit_order(...)` is forbidden text and a forbidden call | **Conflict** (section 3) |
| R3 | Safety test_08/09: raw-text scans of `runtime_py()` (core/, data/, ui/, main.py, config.py), comments included | `tests/acceptance.py:50-75` | Fails if any bridge file in core/ mentions `submit_order`, even in a comment | Avoidable: keep the sandbox in `tools/` |
| R4 | `core/engine/orders` reached only through the engine | `tests/macro_m0_harness.py:60, 149-172` | The bridge must not import QUANTGEN's `OrderBook`; it does not need to | OK |
| R5 | DO-NOT-BUILD item 21: no order path and no broker execution adapter "inside this programme"; refused shape `order_path_or_broker_adapter` | `QUANTGEN_MACRO_INTEGRATION.md:6162, 6235`; `core/rules/macro_rules.py:60-61, 283-286`; `data/macro/rules_v2.0.0.json:2165` | The Nautilus wheel contains broker adapters. Never imported, separate venv | **Owner reading needed** (finding 5) |
| R6 | "Never add a broker execution adapter, even behind a flag" | `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_V2_CLAUDE_CODE_TASKS.md:55` (TASK-M0-01) | Same as R5. A config switch that could select a Nautilus live client would breach it | OK if the deny-list holds |
| R7 | No new dependency without the owner | `research_notes/QUANTGEN v2 integration map/01_sprint_plan.md:45`; `.../00_coordinator_rulings.md:54-55` (names `pyarrow`); `docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md:20`; `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:20`; `.claude/workflows/quantgen-paper-write.js:37` | Nautilus plus 8 to 13 packages, `pyarrow` among them | **Conflict** (section 2) |
| R8 | numpy 2.3.5 / scipy 1.18.0 / pandas 2.3.3 in the test interpreter while a readout is pending | `tests/frozen_guard.py:11, 39, 85-91`; spec `:116-119` | Global install could move them (eager); venv install cannot | OK with a venv (section 5) |
| R9 | Never edit `paper_live/` or `grokteam/`; never run their replay, grid, verdict, sameday, calibrate or `grokteam.book` | spec `:102-106, 124-126`; plans `...split-phase1.md:21-22` | The bridge touches neither | OK |
| R10 | Hermetic suite: network touchpoints raise (T-HERM-01); shipped trees and `~/.nextgen/macro` unchanged (T-HERM-02) | `tests/macro_acceptance.py:25-27, 52-138, 159-207` | Subprocess not covered by the patches; tests must use temp ledgers | Needs its own guard (section 4) |
| R11 | No concurrent runs while the suite runs; TRADEGEN never registers trials in `~/.nextgen/macro/ledgers` | spec `:142-144` | A real pilot run writes ledger rows; never during a suite run | OK by procedure |
| R12 | Ledgers append-only and hash-chained | spec `:169`; `research_notes/QUANTGEN TRADEGEN split map/split_map.md:279` | Register every variant before it runs; never rewrite a row (map02 §3) | OK |
| R13 | test_s4: engine files byte-identical or add-only; no wall clock in S4 modules | spec `:164-168`; `tests/macro_m5_integration.py:55-58, 315-337` | Bridge touches no S4 file | OK |
| R14 | No `datetime.now()` in acting code; T-CTX-01 acting prefixes include `core.quant.` | `.../01_sprint_plan.md:45`; `core/ficc/context_log.py:71-73` | Nautilus stamps run ids and start/finish times by wall clock inside the library (map01 §6). Bridge code must not call the clock, and must keep those fields out of hashes | OK with care |
| R15 | No multiplier, weight or cap above 1.0 | P2 `README.md:383-391`; `data/macro/rules_v2.0.0.json` refused shape `multiplier_weight_or_cap_above_1` | Target weight in [0, 1]; no MARGIN leverage above 1 | OK |
| R16 | The gate is pre-registered and changed nowhere else; one cost table, `COST_BP_PER_SIDE`; 2x-cost survival | `README.md:255-266` | The bridge feeds `walk_forward`, never re-implements it; reads costs from QUANTGEN (map02 §1.4, §6) | OK |
| R17 | NOT_RUN is a third status, never PASS, never a positive claim | `tests/notrun.py:1-35`; `README.md:858-864`; spec `:450-452` | Venv absent means NotRun, never PASS (section 2.4) | OK |
| R18 | Suites are registered in `tests/run_all.py`; a missing third-party package is one NOT_RUN row | `tests/run_all.py:41-85, 131`; lazy pattern `:57-71` | New suite, e.g. `nautilus`, registered the same way | OK |
| R19 | Git: `* -text`, never renormalise; CRLF files edited only with the Edit tool; results file committed only after a full run | spec `:159-160`; `.gitattributes`; plans `...paper-pipeline.md:25-27` | `tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml` are CRLF; `requirements-dev.txt` is LF (`file` output) | OK by procedure |
| R20 | Personal use; do not distribute as a product | `README.md:924-929` | Keeps LGPL-3.0 conveyance duties dormant (section 8) | OK |
| R21 | Credentials only from `.env`, never logged, presence only | `config.py:1-19, 25-39`; `.env.example:1-3` | Child process must not inherit `.env` keys (finding 8) | Needs a scrubbed env |
| R22 | Every artifact carries `read_only: true` | council spec `QUANTGEN_MACRO_INTEGRATION.md:5605`; `tests/macro_m0_harness.py:196-223` | Bridge manifests should stamp it (the test checks only macro stores today) | OK by design |
| R23 | Register before the run; data-access history; holdouts after the freeze | spec `:442-452`; map02 §3.2; map03 header | A pilot-window run before registration is an unregistered trial. Map 03 used only pre-2004-12-01 SPY data for this reason | OK if kept |
| R24 | Referees: Claude, GPT via Codex CLI, Gemini via agy; a missing referee is REVIEW_INCOMPLETE, never "no objections" | spec `:46, 402-405, 659`; `tools/debate.py:45-47` | Applies to the bridge spec as house practice | Partly runnable here (section 7) |
| R25 | Research files live at test-pinned paths (T-COUNCIL-DOCS-01); papers in `papers/` | spec `:171-172`; `tests/macro_tf_data.py:338, 355` | This map's folder is new and unpinned | OK |

---

## 2. (a) Dependencies

### 2.1 Where the rule is written, and what it says

| Source | Text | Scope |
|---|---|---|
| `research_notes/QUANTGEN v2 integration map/01_sprint_plan.md:45` | "No new dependency; no order path; no multiplier above 1.0; no `datetime.now()` in acting code" | Definition of done, every v2 sprint |
| `research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55` | "**No new dependencies.** No `jsonschema`, `arch`, `pyarrow`, notifier packages. ... Parquet is never read." | Binding for every v2 implementer (`:1-5`) |
| `research_notes/QUANTGEN v2 integration map/spec_tests_registry.md:401` | "No new dependency ... without the owner; `core/` must not import them." | v2 tests brief |
| `docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md:20` and `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:20` | "No new pip dependencies. numpy 2.3.5, scipy 1.18.0, pandas 2.3.3 must not change (frozen studies)." | Plans A and B |
| `.claude/workflows/quantgen-paper-write.js:37` | "No new pip packages; numpy 2.3.5, scipy 1.18.0 and pandas 2.3.3 do not change." | Every paper's implementation stage, today |

Two readings exist. The narrow one: each source binds only its own sprint or plan. The broad one: it is a standing
house rule, repeated each time. Either way, the escape clause is the owner ("without the owner"). Nautilus brings
`pyarrow`, which the coordinator ruling names, so no reading lets the bridge add it silently.

### 2.2 What Nautilus brings

Wheel METADATA (both cp313 wheels, identical `Requires-Dist`): `click>=8.4.1,<9`, `fsspec==2026.2.0`,
`msgspec>=0.21.1,<1`, `numpy>=1.26.4`, `pandas>=2.3.3,<4`, `portion>=2.6.1`, `pyarrow>=25`, `pytz>=2026.2`,
`tqdm>=4.68.4,<5`, `tzdata>=2026.3`, and `uvloop==0.22.1` off Windows. Python `>=3.12,<3.15`. Licence
`LGPL-3.0-or-later`. The venv resolved to 16 distributions in total (`pip` included): click 8.5.0, fsspec 2026.2.0,
msgspec 0.22.0, nautilus_trader 1.231.0, numpy 2.3.5, pandas 2.3.3, portion 2.6.3, pyarrow 26.0.0,
python-dateutil 3.0.0, pytz 2026.5, six 1.17.0, sortedcontainers 2.4.0, tqdm 4.70.1, tzdata 2026.5, uvloop 0.22.1
(`importlib.metadata` in the venv). On Windows, tqdm also pulls `colorama` and uvloop is skipped.

### 2.3 Options, and why most of them fail

| Option | Problem |
|---|---|
| Add to `requirements.txt` / `pyproject.toml` | Installs into the global interpreter (the house runs one global interpreter, `...paper-pipeline.md:18`). Breaks the stated "Python 3.10+" (`README.md:841`; `pyproject.toml:9`), because Nautilus needs 3.12+. Adds `pyarrow`. Risks clause (d) on any eager upgrade (section 5). |
| Add to `requirements-dev.txt` | Its header says "Tools used to generate shipped data, never imported by the application" (`requirements-dev.txt:1`). In practice it is installed globally: `exchange_calendars` 4.13.2 is in the global interpreter (measured). Same risks as above. |
| Optional extra in `pyproject.toml` (`quantgen[nautilus]`) | `pip install .[nautilus]` installs into whichever interpreter runs pip, usually the global one. It also makes Nautilus part of the package metadata. |
| **Separate `requirements-nautilus.txt` + dedicated venv + subprocess** | Nothing changes in the global interpreter or the four existing dependency files. The only new tracked file is the requirements file itself. Recommended. |

### 2.4 The recommended shape (proposal, not built)

1. **New file `requirements-nautilus.txt`** (LF), installed only with
   `<venv>\Scripts\python -m pip install --require-hashes -r requirements-nautilus.txt`. In hash mode every
   transitive package must be pinned with `==` and a hash. Pin `nautilus_trader==1.231.0`, `numpy==2.3.5` and
   `pandas==2.3.3`, so that the venv's numerics match the global interpreter's. Use environment markers for
   `uvloop` (non-Windows) and `colorama` (Windows). The two nautilus wheel hashes, measured here and equal to PyPI's
   digests (`https://pypi.org/pypi/nautilus_trader/json`, `releases["1.231.0"]`):
   - `nautilus_trader-1.231.0-cp313-cp313-win_amd64.whl`:
     `sha256:5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf`
   - `nautilus_trader-1.231.0-cp313-cp313-manylinux_2_35_x86_64.whl`:
     `sha256:429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91`
   The other hashes are not collected yet. A file header should say: "Never install into the global interpreter
   (tests/frozen_guard.py clause (d))."
2. **The venv lives outside the repo.** The install is about 940 MB (map01 §10.2), and the repo is on OneDrive,
   which the house already keeps generated files away from (`.../01_sprint_plan.md:38`). Example:
   `%LOCALAPPDATA%\quantgen\ntvenv`.
3. **One new setting, `QUANTGEN_NAUTILUS_PYTHON`**: the venv interpreter's path. Document it in `.env.example`
   under its own heading. No test pins `.env.example`, `requirements*.txt` or `pyproject.toml` contents beyond the
   research-identity check (`tests/macro_ui_components.py:149-160`; grep of `tests/`).
4. **No lazy import, because there is no import.** QUANTGEN-side code never imports `nautilus_trader`. It writes
   inputs to a temp dir, runs `<venv python> -I -B tools/nautilus/sandbox.py <dir>`, and reads outputs back. The
   sandbox imports only the standard library, numpy, pandas and allow-listed Nautilus modules, and nothing from
   QUANTGEN. That keeps `config.py`'s `load_dotenv()` (`config.py:25-29`) out of the child, and keeps the venv free
   of flet, scipy and the rest.
5. **NotRun when absent, FAIL when wrong.** A bridge suite registered like `papers_tests` (`tests/run_all.py:57-71`)
   raises `NotRun("OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)")` when the setting is blank or
   the file is missing. I propose FAIL, not NotRun, when the venv reports any `nautilus_trader`, numpy or pandas
   version other than the pins: a silent engine change would move results. This is a proposal (open question 3).
6. **Every run manifest records** the Nautilus, Python, numpy and pandas versions of the child, the wheel hash, the
   input data hash and the output hashes (map01 §6, map01 §12).
7. **Global tests that never need the venv** (QUANTGEN-side parity math, ledger-first ordering, the T-RO-01
   amendment) run in every suite run, as map03 §6.1 proposes.

Residual conflicts even with this shape: the coordinator ruling's `pyarrow` ban (only if read as project-wide), the
paper-write RULES line if the pilot ever runs as a paper (`.claude/workflows/quantgen-paper-write.js:37`), and the
paper harness recording only `PACKAGES = ("numpy", "scipy", "pandas")` (`tools/paper/study.py:30`). All three need
the owner's dependency ruling to name them.

---

## 3. (b) T-RO-01

### 3.1 How it scans today

- **Files** (`tests/macro_m0_harness.py:66-70`): `runtime_py()` (every `*.py` under core/, data/, ui/, plus main.py
  and config.py; `tests/acceptance.py:50-56`), `docs/*.py` (top level only), and every `*.py` under `tools/` and
  `papers/` except `__pycache__` (`SCAN_TREES`, `:63`). Plus the macro workflow YAML (`:62, 112-132, 141-142`).
  The real tree is 154 files today (`gov:scan`). The test asserts more than 50 (`:139`).
- **Text** (`:83-87`): docstrings are stripped and comments vanish through `ast.unparse` (`tests/acceptance.py:33-47`).
  Then:
  - case-insensitive substrings `order_cash`, `order-cash`, `place_order`, `submit_order`, `tttc0802u`,
    `tttc0801u`, `vttc0802u`, `/v1/orders`, `/v1/withdraws`, `/v1/deposits/generate_coin_address`,
    `/api/v3/order`, `/sapi/v1/capital/withdraw`, `/sapi/v1/capital/deposit`, `private_key`, `seed_phrase`
    (`:28-34`);
  - case-sensitive substrings `KIS_ACCOUNT`, `CANO`, `ACNT_PRDT_CD` (`:35`). Note that `CANO` also matches any
    upper-case identifier containing it, such as `CANONICAL`;
  - the regex `/uapi/[^\s'"]*/trading/` (`:36`).
- **Imports** (`:90-96`): only the **first** dotted component is compared with `FORBIDDEN_IMPORTS`: `ccxt`, `web3`,
  `pyupbit`, `binance`, `python_binance`, `ib_insync`, `alpaca`, `alpaca_trade_api`, `mojito`, `pykis`, `kiwoom`,
  `okx`, `bybit`, `kucoin`, `coinbase`, `cbpro`, `MetaTrader5`, `oandapyV20`, `eth_account`, `bitcoinlib`,
  `bitcoin` (`:38-42`).
- **Calls** (`:97-108`): any attribute or bare call named `place_order`, `submit_order`, `create_order`,
  `send_order`, `new_order`, `order_cash`, `cancel_order`, `create_market_order`, `create_limit_order`,
  `buy_market_order`, `sell_market_order`, `buy_limit_order`, `sell_limit_order`, `withdraw`, `withdraw_coin`,
  `withdraw_krw`, `create_withdrawal`, `transfer`, `transfer_funds`, `deposit_address`, `get_deposit_address`,
  `create_deposit_address`, `fetch_deposit_address`, `generate_coin_address`, `sign_transaction`,
  `send_transaction`, `send_raw_transaction` (`:44-50`). Also `.post/.put/.delete/.patch` whose string arguments
  contain `order`, `withdraw`, `transfer` or `deposit` (`:51-52, 102-105`).
- **Exemptions**: only bare `fill_order` and `cancel_order` in `ui/trading_page.py` (`:56, 107`). There is no
  exemption mechanism for text hits or attribute calls.
- **Other T-RO-01 tests**: `core.engine.orders` imported only from `ORDERS_IMPORTERS_ALLOWED` (`:60, 149-172`); the
  scan reaches tools/ and papers/ (`:175-192`); artifacts stamp `read_only: true` (`:196-223`). The registry row
  lists all five implementing tests (`tests/macro_registry.csv:12`).

### 3.2 Would the sandbox fail it? Yes. Would it catch a live leak? No.

Measured with the repo's own `_offences` on probe files in a temp tree (`gov:scan`):

| Probe | Today's T-RO-01 |
|---|---|
| `tools/nautilus/sandbox.py`: a `Strategy` subclass calling `self.submit_order(o)` | 2 hits: text `'submit_order'`, call `.submit_order()` |
| `tools/nautilus/live_leak.py`: imports `nautilus_trader.live.node.TradingNode`, `nautilus_trader.adapters.binance`, `nautilus_trader.core.nautilus_pyo3`; calls `node.run()` | 0 hits |
| `tools/nautilus/dynamic.py`: `importlib.import_module('nautilus_trader.adapters.betfair')` | 0 hits |
| `core/quant/nt_runner.py`: imports `BacktestEngine` | 0 hits |
| `tools/nautilus/other_submit.py`: `s.submit_order(o)` outside the sandbox | 2 hits |

Map 01 measured the same two hits on `core/bridge/nautilus_sandbox.py` (map01 §9.2). In `core/`, safety test_08
fails too, because it scans raw text including comments (`tests/acceptance.py:62-68`).

Six Nautilus order methods are not in `FORBIDDEN_CALLS` at all: `modify_order`, `cancel_orders`,
`cancel_all_orders`, `close_position`, `close_all_positions`, `market_exit` (`nt:trading/strategy.pyx:1011, 1134,
1215, 1351, 1418, 1750`; map01 §8). `submit_order_list` is caught only by the `submit_order` substring. Adding all
of them to `FORBIDDEN_CALLS` gives zero hits on the current 154-file tree (measured).

### 3.3 The narrowest compliant design (proposal for the owner)

**Placement.** One file, `tools/nautilus/sandbox.py`, run only by the venv interpreter as a subprocess.

- `tools/` is in T-RO-01's scope (`tests/macro_m0_harness.py:63`), so the file stays scanned. Placing it outside
  every scanned tree would be evasion (map01 §9.2).
- `tools/` is not in `runtime_py()`, so test_08/09 need no change. The 2026-10-23 spec chose this split on purpose:
  "`tests/acceptance.py::runtime_py()` is **not** extended: its raw-text scans would trip on docstrings that merely
  name a forbidden call" (spec `:180-181`).
- `tools/` is not packaged (`pyproject.toml:22-24` includes only `core*`, `data*`, `ui*`), so the app never ships or
  imports it.
- It is not under `core.quant.`, so T-CTX-01's acting-module rules (`core/ficc/context_log.py:71-73`) and the S4
  wall-clock scan (`tests/macro_m5_integration.py:55-56`) do not apply to it.

**Static amendment to `tests/macro_m0_harness.py`.** A working prototype is `gov:scan/proto_scan.py`. The lines that
change:

| Line(s) | Change |
|---|---|
| after `:56` | `NAUTILUS_SANDBOX = "tools/nautilus/sandbox.py"`; `NAUTILUS_ALLOWED` (import prefixes: `nautilus_trader.backtest.engine`, `nautilus_trader.backtest.models`, `nautilus_trader.config`, `nautilus_trader.model`, `nautilus_trader.persistence.wranglers`, `nautilus_trader.trading.strategy`, `nautilus_trader.common.component`, bare `nautilus_trader` for `__version__`; map01 §9.3 item 2); `NAUTILUS_DENIED` (`nautilus_trader.live`, `.adapters`, `.network`, `.core.nautilus_pyo3`, `.backtest.node`, `nautilus_pyo3`; map01 §9.3 item 3) |
| `:44-50` | Add `modify_order`, `cancel_orders`, `cancel_all_orders`, `close_position`, `close_all_positions`, `market_exit`, `submit_order_list` to `FORBIDDEN_CALLS`. They stay forbidden in the sandbox too |
| `:85` | Exempt the `submit_order` text hit only when `rel == NAUTILUS_SANDBOX` |
| `:90-96` | Compare **full dotted names** (module and `module.name`) with `NAUTILUS_DENIED` in every file. Any `nautilus_trader` import outside the sandbox is an offence. Inside it, only `NAUTILUS_ALLOWED` prefixes |
| `:97-101` | Exempt `.submit_order()` only in the sandbox and only on the receiver `self` |
| new, in the `ast.walk` loop | Any string constant naming a denied module is an offence (catches `importlib.import_module("nautilus_trader.adapters...")`) |
| new test after `:192` | `test_t_ro_01_nautilus_confined_to_the_sandbox`, with positive and negative controls in a temp tree (the pattern of `:175-192`), `test_ids = ["T-RO-01"]` |
| `tests/macro_registry.csv:12` | Resync `implemented_in` with `python -m tests.macro_acceptance` (`README.md:855`; `tests/macro_acceptance.py:267-289`); `test_registry_implemented_in_matches_test_ids` fails until then (`tests/macro_m0_harness.py:286-295`) |

Prototype result (`gov:scan`): the sandbox probe passes with 0 hits; the live-leak probe gets 5 hits, the dynamic
import 1, the `core/quant` import 1, and `submit_order` outside the sandbox keeps its 2 hits. The real repo tree gives
0 hits. A sixth rule, map01 §9.3 item 4 (no `requests`, `socket`, `asyncio`, `subprocess` or `os.environ` in the
sandbox), is easy to add the same way. I did not prototype it.

**Runtime check inside the child** (map01 §9.3): after `engine.run()`, assert no `sys.modules` key starts with
`nautilus_trader.adapters` or `nautilus_trader.network`. Do **not** block `nautilus_trader.live` at import: the
kernel imports seven `live` modules in every backtest (`nt:system/kernel.py:75-77`; measured again in
`gov:run_nofile/out.txt`). A violation makes the run invalid and withholds the verdict.

**Do not edit the council spec.** Its T-RO-01 row says the scan "finds no order ... call"
(`QUANTGEN_MACRO_INTEGRATION.md:5605`). The 2026-10-23 spec amended T-RO-01's scope in its own text (spec
`:177-181`) without touching the council spec. The bridge spec should do the same, with the rationale: orders in a
Nautilus backtest fill against a simulated exchange, as QUANTGEN's own fills pass through `OrderBook.fill`
(`core/engine/orders.py:90, 169, 253-257`).

---

## 4. (c) Hermeticity

### 4.1 What T-HERM-01 and T-HERM-02 cover

- **T-HERM-01** patches, for the duration of each macro test: the FRED and Yahoo fetchers, every provider's
  `requests` handle, the shared `data.net.session.request`, `socket.socket.connect` and `connect_ex`, and sets the
  FICC cache TTL to 0 (`tests/macro_acceptance.py:52-71`). It is armed per test, not per process (`:7-9, 74-98`).
- **T-HERM-02** checks that `data/macro`, `core/rules`, `core/calendars/data`, `data/techfund`,
  `tests/fixtures/macro` and `docs/asset_expansion/cards` are byte-identical, and that `~/.nextgen/macro`,
  `~/.nextgen/trading/rules.json` and `QUANTGEN_MACRO_DIR` are untouched (`:25-27, 101-138, 198-207`).
- Neither reaches a child process. The patches are Python attributes in the parent. Nautilus's Rust core also has its
  own HTTP, WebSocket and socket clients (`nt:core/nautilus_pyo3.pyi`; map01 §9.1) that never touch Python's
  `socket` module.

### 4.2 What a Nautilus backtest does on the wire and on disk (measured, Linux)

Probe: synthetic 300-bar SPY series, a strategy that buys and sells 100 shares every 20 bars, CASH account,
`MakerTakerFeeModel`, `FillModel(random_seed=1)`, `LoggingConfig(log_level="ERROR")`, run with `env -i`, HOME,
TMPDIR and the working directory set to three empty temp dirs (`gov:herm_probe.py`).

| Check | Result |
|---|---|
| `strace -f -e trace=socket,connect,bind,sendto,openat,mkdir,mkdirat,rename*,unlink*,creat` over the whole process, from interpreter start | 0 `socket`, `connect`, `bind`, `sendto` calls. 0 `openat` with `O_WRONLY`, `O_RDWR` or `O_CREAT` outside `/dev` and `/proc`. 0 mkdir, rename or unlink. 15 fills (`gov:run_nofile`) |
| Same run inside `unshare -n` (a namespace with no network) | Completed, 15 fills, exit 0 (`gov:run_nonet`) |
| Files left in HOME, TMPDIR, working directory | none |
| Modules loaded after the run | 7 `nautilus_trader.live.*` modules; Python `asyncio`, `socket`, `ssl`, `uvloop`; no `nautilus_trader.adapters.*` or `nautilus_trader.network` (`gov:run_nofile/out.txt`) |
| Same run with `log_level_file="INFO"` | One file in the **working directory**: `QGGOV-001_2026-10-26_<uuid>.log`. No other write (`gov:run_filelog`) |

Supporting source facts:

- File logging is off unless `log_level_file` is set. `log_directory=None` means the current working directory
  (`nt:common/config.py:627-634, 674-676`). The docs say the same: "Log files are written to the current working
  directory by default", and the default name is `{trader_id}_{%Y-%m-%d}_{instance_id}.log`
  (`https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/docs/concepts/logging.md`).
- No `expanduser`, `Path.home()` or `~/.nautilus` in the installed `.py`, `.pyx` or `.pxd` sources, outside
  `adapters/` (grep). The compiled Rust library was not inspected; the `strace` run covers its behaviour for this
  run shape only.
- Environment reads outside `adapters/`: `NAUTILUS_PATH`, only in `ParquetDataCatalog.from_env`
  (`nt:persistence/catalog/parquet.py:101, 196-199`), and `SecureString.from_env` (`nt:common/secure.py:209`).
  The bridge uses neither.
- A Parquet catalog, `StreamingConfig` (feather files) and a cache or message-bus database are all opt-in
  (`nt:backtest/config.py:365-366`; `nt:cache/config.py:63`; `nt:common/config.py:468`).

### 4.3 Recipe for the bridge

1. Start the child with an **explicit environment**: `PATH`, `SYSTEMROOT` (Windows), and `HOME`/`USERPROFILE`,
   `TMP`/`TEMP`/`TMPDIR` pointing into a fresh `tempfile.TemporaryDirectory()`. No `.env` key, no
   `NAUTILUS_PATH` (finding 8).
2. Working directory = that temp dir. `-I` (isolated: ignores `PYTHON*` variables and user site) and `-B` (no
   `__pycache__` written next to `tools/nautilus/`; it is git-ignored anyway, `.gitignore:2-3`).
3. `LoggingConfig(log_level="ERROR")` and no `log_level_file`. If file logs are ever wanted, set both
   `log_directory` (the temp dir) and a fixed `log_file_name`, so no date or UUID enters a file name.
4. No catalog, no streaming, no database configs. `FillModel` always with `random_seed` (map01 §6, finding 14).
5. Inputs and outputs as CSV/JSON in the temp dir. The parent reads them back, hashes them, then deletes the dir.
   (Parquet would need `pyarrow` in the global interpreter; the coordinator ruling says "Parquet is never read",
   `00_coordinator_rulings.md:55`.)
6. Static deny-list (section 3.3) plus the post-run `sys.modules` check.
7. Optional, partial: a `sys.addaudithook` in the child that refuses `socket.connect`. It sees Python sockets only,
   not Rust ones (map01 §9.3). UNVERIFIED: not tested.
8. Tests write ledgers only to temp dirs (`tests/macro_m7_ledger.py:6` states the same rule for ledger tests). A
   real pilot run registers in `~/.nextgen/macro/ledgers` (map02 §3.1) and must never overlap a suite run (spec
   `:143-144`), or T-HERM-02 trips.

On Windows there is no `strace` or `unshare`. The Linux measurement, the deny-list and the `sys.modules` check are
the evidence there. UNVERIFIED: no Windows network or file trace was run.

---

## 5. (d) The frozen-study pins

### 5.1 What clause (d) checks

While any readout is pending, the versions of numpy, scipy and pandas in the interpreter **running the tests** must
equal the PREREG pins (`tests/frozen_guard.py:11, 39, 85-91`; spec `:116-119`). The pins are numpy 2.3.5,
scipy 1.18.0, pandas 2.3.3 (spec `:59-60`). There is no warn-only branch (spec `:117-119`). The readouts are
pending until the H2 verdicts and the GROKTEAM look (about 2026-11-03 and on or after 2027-02-01;
spec `:57, 64-66`).

### 5.2 Could installing Nautilus move them? Measured on the Linux global set

| pip command (run as `--dry-run` in a throwaway `--system-site-packages` venv, pip 26.2.2) | What it would install or change |
|---|---|
| `pip install nautilus_trader==1.231.0` (default strategy, only-if-needed) | adds nautilus_trader 1.231.0, fsspec 2026.2.0, msgspec 0.22.0, tqdm 4.70.1, portion 2.6.3, sortedcontainers 2.4.0, pyarrow 26.0.0; **uvloop 0.23.0 to 0.22.1** (downgrade). numpy, pandas, scipy unchanged (`gov:dryrun_report.json`) |
| `pip install --upgrade --upgrade-strategy eager nautilus_trader==1.231.0` | the above plus **numpy 2.3.5 to 2.5.4**, **pandas 2.3.3 to 3.1.0**, python-dateutil 2.9.0.post0 to 3.0.0 (`gov:dryrun_eager.json`). Clause (d) would fail |

Notes:

- Nautilus's floor `pandas>=2.3.3` is exactly the pin. Any later Nautilus that raises it would collide.
  `2.0.0rc7` lists no hard numpy or pandas requirement (map01 §10.4); not installed, UNVERIFIED in practice.
- The Windows global set was not measured. uvloop is not required on `win32` (wheel METADATA). UNVERIFIED for
  Windows: whether `fsspec==2026.2.0` or `pyarrow` conflicts with anything already installed there.
- **Never run the suite under the venv interpreter.** The venv has no scipy, so `version("scipy")` in
  `test_d_library_versions_match_the_pins_while_a_readout_is_pending` would raise and FAIL
  (`tests/frozen_guard.py:90`). It also lacks flet, yaml and the rest.
- With the separate venv, clause (d) reads the untouched global interpreter, so it holds. This matches spec 3.1
  point 2: readouts use "the global one while it still matches, otherwise a dedicated venv" (spec `:92-94`).
- **This clone cannot evaluate clause (d) at all.** It has no tag `studies-of-record-2026-10-23`, and the remote has
  no tags (`git tag`; `git ls-remote --tags origin` both empty). frozen_guard tests (a), (b) and (d) FAIL here with
  "Not a valid object name" (`scratchpad/baseline_results.json`). The owner's Windows repo has the tag (README
  `:47-52`). Clause (d) evidence for any bridge commit must come from there.

---

## 6. (e) The split: where Nautilus live trading belongs

QUANTGEN is "a quantitative-finance research instrument. It goes no further than paper trading". TRADEGEN is
"developed in its own session for real-money trading within Korean law" (spec `:25-29`; `README.md:39-42`).

| Nautilus surface | QUANTGEN | TRADEGEN |
|---|---|---|
| `BacktestEngine` with a simulated venue, `Strategy`, fee and fill models, wranglers | Yes, in the one sandbox file, in a separate venv, as a subprocess | Yes |
| `TradingNode`, `TradingNodeBuilder`, live data and execution clients (`nautilus_trader.live.*`, map01 §9.1) | Never imported by QUANTGEN code. The kernel's own internal import of `live` engines is tolerated (section 3.3) | Its domain |
| `nautilus_trader.adapters.*`, including `sandbox` (simulated fills on **live** data inside a `TradingNode`, `nt:adapters/sandbox/execution.py:58`) | Never. QUANTGEN's live paper trading already has its own engine (`core/engine/`) | Its domain, subject to Korean law (below) |
| `nautilus_trader.network`, `nautilus_pyo3` network clients, `adapters.env.get_env_key` | Never | Its domain |
| API keys in the Nautilus process | Never (scrubbed env, section 4.3) | Its own `.env`, its own venv |

Boundary rules that already exist and carry over:

- TRADEGEN runs nothing until it has its own venv and state root (spec `:131-135`).
- TRADEGEN never registers trials in QUANTGEN's `~/.nextgen/macro/ledgers` (spec `:142`). A Nautilus strategy
  developed in TRADEGEN is not a QUANTGEN trial unless it is re-registered and re-run inside QUANTGEN.
- No app of either program runs while QUANTGEN's suite runs (spec `:143-144`).
- What may cross from QUANTGEN to TRADEGEN is a **verdict artifact** (a card, a gate result), read-only. The council
  spec lists what would have to hold if a broker path were ever added: PASS cards only, fail-closed, 2x costs, its
  own gated forward record (`QUANTGEN_MACRO_INTEGRATION.md:1255-1268`). By analogy those are sensible TRADEGEN
  conditions. They are not QUANTGEN work (spec `:647`, "All TRADEGEN work" is out of scope).
- Proposed new rule: QUANTGEN imports nothing from TRADEGEN, and TRADEGEN's Nautilus code is not copied into
  QUANTGEN's sandbox. The repo states no such rule today.

Korean-law facts that shape TRADEGEN's use of the Nautilus adapters, from the in-repo legality report
(2026-10-23), by its compliance-matrix row:

| Nautilus 1.231.0 adapter (map01 §9.1) | Report status for a Korean-resident individual |
|---|---|
| `polymarket` | Illegal; also blocked by platform (row 1, `reports/Korean resident trading venue legality.md:15`) |
| `betfair` (sports and event betting) | Foreign sportsbooks: illegal (row 7, `:21`); National Sports Promotion Act Art. 48(3), up to 5 years or KRW 50M (`:59`) |
| `binance`, `bybit` | Grey (row 13, `:27`) |
| `okx` | Spot grey; derivatives and P2P blocked by platform (row 14, `:28`) |
| `hyperliquid` | Perps grey (row 16, `:30`); outcome markets hard-block (`:93`) |
| `interactive_brokers` (direct account) | Grey, leaning non-compliant unless every FX report is filed (row 36, `:50`) |
| `architect_ax`, `bitmex`, `deribit`, `dydx`, `kraken`, `databento`, `tardis` | Not rated in the report. UNVERIFIED |
| KIS, Upbit (the lawful routes, rows 10, 21, 31) | No adapter ships in 1.231.0 (map01 §9.1). TRADEGEN would have to write one |

---

## 7. (f) The house process, and what runs in this Linux container

The process, as the 2026-10-23 work ran it:

1. **Spec** in `docs/superpowers/specs/`, with revision status and owner decisions (spec `:3-17, 37-49`).
2. **Referee debate**: Claude, GPT via the Codex CLI, Gemini via the Antigravity CLI `agy` (D6, spec `:46`), round
   by round, every issue ruled in an appendix (spec `:664-743`; reports in
   `docs/superpowers/specs/2026-10-23-review/`). A referee that returns nothing leaves the review incomplete, never
   "no objections", unless the owner records a substitution (spec `:402-405, 659`).
3. **Owner approval** of the spec (spec `:12-17`).
4. **Test-first plan** with Global Constraints, a file table and RED/GREEN steps; "REQUIRED SUB-SKILL: Use
   superpowers:subagent-driven-development" (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:3, 17-27`).
5. **Subagent-driven execution**: one implementer per task, task review, fix loop, final whole-branch review,
   dry run (`docs/superpowers/plans/2026-10-23-execution-record.md:3`).
6. **Full suite** before each commit group; the results file is committed only after a full run (plans
   `...paper-pipeline.md:25`; spec `:159-160`).
7. **Execution record**: every ruling made on the owner's behalf, "each with what it costs if wrong", then deferred
   findings (`docs/superpowers/plans/2026-10-23-execution-record.md:1-4`; style e.g. `:87, 93`).

| Step | Runs in this container? | Why, and what is left for the owner's machine |
|---|---|---|
| 1. Spec | Yes | Text only |
| 2a. Claude referee | Yes | A subagent with a disposable bundle as cwd |
| 2b. GPT via Codex CLI | **No** | `codex` is not installed here (`which`). The Codex quota resets 2026-10-30 14:40 machine-local time (`docs/superpowers/plans/2026-10-23-execution-record.md:158`; `tools/debate.py:33`). Until then a GPT round is REVIEW_INCOMPLETE anyway |
| 2c. Gemini via agy | **No** | `agy` is not installed; the runner defaults to a Windows path, `C:\Users\whydi\AppData\Local\agy\bin\agy.exe`, overridable by `QUANTGEN_AGY` (`tools/debate.py:46-47`) |
| 2d. A substitute referee (for example this session's `adversarial-spec` skill) | Possibly | Not a house referee (D6). Counts only if the owner records the substitution (spec `:402-405`) |
| 3. Owner approval | No | Owner only. So are the three rulings this map asks for (section 10) |
| 4. Plan | Yes | Text only |
| 5. Subagent-driven execution | Yes, for code and the bridge's own tests | The venv and `strace` exist here. Never run `python tests/run_all.py` here: it rewrites `qa/acceptance_results.json` (`tests/run_all.py:54, 136-137`). The baseline was taken with a wrapper that redirects `OUT` to the scratchpad (`scratchpad/run_baseline.py`). Single macro modules print only, via `python -m tests.<module>` (`tests/macro_acceptance.py:237-260`) |
| 6. Full suite of record | **No** | Linux: 738 PASS / 8 FAIL / 124 NOT_RUN of 870, about 10 minutes (`scratchpad/baseline.log`, `baseline_results.json`). Committed (Windows): 749 / 0 / 121 (`qa/acceptance_results.json`). The 8 FAILs: frozen_guard (a), (b), (d) (no tag in this clone); `papers/test_debate_run_kills_process_tree` (`taskkill` is Windows-only); `expansion/selfcheck_strategies`, `selfcheck_curve_models`, `selfcheck_crypto_analytics` and `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache` (NaN or empty results; likely the owner's local data cache is absent; cause UNVERIFIED). The 3 extra NOT_RUNs are the Tectonic compile tests ("tectonic binary absent") |
| 7. Execution record | Yes, as text | Its full-run lines must quote the Windows run |
| Windows-only measurements | No | Windows wheel import and run time (map01 §10.2, UNVERIFIED), a Windows dependency resolution (section 5.2), and a Windows network/file check (section 4.3) |

Also note: the README's test-table total is stale against the committed results file: it says
"743/864 passed, 0 failed, 121 not run (2026-10-23)" (`README.md:878`), while `qa/acceptance_results.json` has
749 / 870. A bridge commit that adds a suite will touch that table and `--suite` help text
(`README.md:851-856, 864-878`; `tests/run_all.py:131`). The only README test is about specific strings and stale
counts that do not include these (`tests/macro_ui_components.py:137-147`).

---

## 8. (g) Korean law and other regulatory notes for a local open-source engine

What goes away compared with QuantConnect: no account, no platform terms to accept, no upload of strategy code or
data to a third party, no KYC, no cloud execution, and no vendor data licence attached to the engine. The earlier
QuantConnect plan is not in this repo, so I cannot cite its specific terms issues. UNVERIFIED: the QuantConnect
terms were not fetched.

What remains:

1. **LGPL-3.0-or-later.** Duties attach when QUANTGEN **conveys** a combined work (LGPL section 4). A private
   instrument that is never distributed conveys nothing (map01 §10.1, with sources;
   `https://raw.githubusercontent.com/nautechsystems/nautilus_trader/v1.231.0/LICENSE`). The README already says
   "Do not distribute it as a product" (`README.md:924-929`). Publishing a paper's study code that imports Nautilus,
   without shipping Nautilus, should not convey the library. That is my reading, not legal advice. UNVERIFIED.
2. **Input data licences do not change.** Nautilus consumes whatever QUANTGEN feeds it. One item to settle before
   pilot 1: the tech-fund scripts load SPY from `spy_lean_daily.zip`, "QuantConnect Lean format (prices x 10,000, not
   dividend adjusted)" (`QUANTGEN_techfund_research_bundle/QUANTGEN_techfund_research/scripts/us_common.py:179-189`).
   If the pilot used that file, its licence must be recorded, as every QUANTGEN fixture records licence, owner and
   md5 (`tests/notrun.py:7-8, 19-22, 58-61`). Its licence is UNVERIFIED.
3. **Research mode stays on the safe side of the legality report.** The report's "May offer (research mode only)"
   row: "Paper-trading analytics on public ... data inside QUANTGEN, with no order routing and no published signals"
   (`reports/Korean resident trading venue legality.md:100`). A Nautilus backtest on SPY or public BTC/USD data is
   inside that row. Pilot 2 needs no exchange account.
4. **Gambling-law reason for the adapter deny-list.** The wheel carries Betfair and Polymarket adapters (map01
   §9.1). The report rates both venues illegal for a Korean resident, and flags tool-builder exposure under the
   National Sports Promotion Act Art. 26② for "designing or offering systems for similar acts"
   (`reports/Korean resident trading venue legality.md:59, 77`). Installing a library is not using a venue, and
   QUANTGEN builds no such system. Denying every `adapters` import (section 3.3) keeps it that way by construction.
5. **Publishing results.** Papers already carry "an AI-assistance statement and a not-investment-advice note"
   (`README.md:800-802`). The report lists, as not researched, whether sharing signals needs investment-advisory or
   유사투자자문업 registration under FSCMA (`reports/Korean resident trading venue legality.md:117`). A free academic
   paper on a generic trend rule is unlikely to be "advice for consideration", but I could not read FSCMA Art. 101:
   `law.go.kr` did not resolve from this session (DNS failure). UNVERIFIED.
6. **Overseas-trading and FX rules** (FSCMA Enforcement Decree Art. 184①; FX Transaction Regulation Art. 7-33④;
   report `:61, 67`) bind real orders only. They are TRADEGEN's concern (section 6).
7. **Commercial-software rules** (FSCMA, SEC): unchanged. The README states QUANTGEN is not designed to satisfy them
   and must not be distributed (`README.md:924-929`). Nautilus changes nothing here.

---

## 9. Conflict register

| # | Conflict | Rule (file:line) | Proposed resolution | Who decides |
|---|---|---|---|---|
| C1 | The sandbox must call `self.submit_order` | `tests/macro_m0_harness.py:29, 45, 85, 100-101` | One allow-listed file in `tools/`, `self` receiver only (section 3.3) | Owner |
| C2 | T-RO-01 misses `nautilus_trader.live/adapters/network` imports and dynamic imports | `tests/macro_m0_harness.py:90-96` (first component only) | Full dotted-name deny-list everywhere, string-constant check, confinement of `nautilus_trader` to the sandbox | Owner (same ruling as C1) |
| C3 | Six Nautilus order verbs are not in `FORBIDDEN_CALLS`, and `submit_order_list` only by substring | `tests/macro_m0_harness.py:44-50`; `nt:trading/strategy.pyx:1011-1750` | Add them; 0 hits on today's tree | Owner (same ruling) |
| C4 | A new dependency, including `pyarrow` | section 2.1 sources | Separate hash-pinned venv; global files untouched | Owner |
| C5 | DO-NOT-BUILD 21: "a broker execution adapter, inside this programme" vs adapters shipped in the wheel | `QUANTGEN_MACRO_INTEGRATION.md:6162`; `QUANTGEN_V2_CLAUDE_CODE_TASKS.md:55` | Rule that an unimported library in a separate venv, behind C2's deny-list and the runtime check, is not inside the programme | Owner |
| C6 | Clause (d) if anyone installs Nautilus globally | `tests/frozen_guard.py:85-91`; measured eager upgrade | Venv only; file header warning; never run the suite under the venv | Procedure |
| C7 | Paper-write RULES forbid new pip packages; study manifests record only numpy/scipy/pandas | `.claude/workflows/quantgen-paper-write.js:37`; `tools/paper/study.py:30` | Only if the pilot becomes a paper: the dependency ruling names the venv, and the paper's protocol records the Nautilus version | Owner, if relevant |
| C8 | Python floor: README and pyproject say 3.10+; Nautilus needs 3.12+ | `README.md:841`; `pyproject.toml:9` | Moot with the venv shape (Nautilus is not a project dependency) | none |
| C9 | T-HERM-01 cannot cover a subprocess or Rust sockets | `tests/macro_acceptance.py:52-98` | Section 4.3 recipe; Linux `strace`/`unshare` evidence | Plan |
| C10 | `.env` keys would leak into the child | `config.py:25-29`; precedent `execution-record.md:93` | Explicit minimal child environment | Plan |
| C11 | Nautilus file logs use the working directory and a date+UUID name | `nt:common/config.py:630-634` | File logging off, or `log_directory` = temp dir plus a fixed name | Plan |
| C12 | Wall-clock run ids and timestamps inside Nautilus | map01 §6; `.../01_sprint_plan.md:45` | Bridge code calls no clock; keep those fields out of every hash | Plan |
| C13 | Real pilot runs write `~/.nextgen/macro/ledgers` | `tests/macro_acceptance.py:113-138`; spec `:143-144` | Never during a suite run; tests use temp ledgers | Procedure |
| C14 | A pilot-window run before registration is an unregistered trial | spec `:442-447`; map02 §3.2; map03 header | Register first; probes only on pre-window or synthetic data | Procedure |
| C15 | Full suite of record and clause (d) cannot run in this clone | `scratchpad/baseline_results.json`; no tag | Run of record on the owner's Windows machine | Owner |
| C16 | GPT and Gemini referees unavailable here; GPT quota until 2026-10-30 14:40 | spec `:402-405`; `execution-record.md:158` | REVIEW_INCOMPLETE until then, or an owner-recorded substitution | Owner |
| C17 | Nautilus reseeds Python's global `random` | `nt:backtest/models/fill.pyx:75, 77` (map01 finding 14) | Already contained by the subprocess | none |

---

## 10. Owner decisions this map asks for

1. **Dependency ruling.** Allow `nautilus_trader==1.231.0` in a separate, hash-pinned venv, run only as a
   subprocess, with the global interpreter and all existing dependency files unchanged (section 2.4)? Does that
   ruling also cover `pyarrow` against `00_coordinator_rulings.md:54`?
2. **T-RO-01 amendment.** Approve the single allow-listed `tools/nautilus/sandbox.py`, the full-dotted-name
   deny-list, the confinement of `nautilus_trader` imports to that file, the string-constant check, and the seven
   added call names (section 3.3)? Placement in `tools/` (this map) or `core/bridge/` (map01 §9.3, which also needs
   a test_08 change)?
3. **Version mismatch in the venv.** FAIL (proposed) or NotRun?
4. **DO-NOT-BUILD item 21 reading** (C5).
5. **Referee substitution** while Codex and agy are unavailable: wait, or record a substitute?
6. **SPY data provenance** for pilot 1: which source, with which recorded licence (section 8 item 2)?
