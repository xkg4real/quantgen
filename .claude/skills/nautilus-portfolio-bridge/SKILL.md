---
name: nautilus-portfolio-bridge
description: >
  QUANTGEN's map and rules for NautilusTrader and research-to-portfolio work: the tools/nautilus bridge
  (runner, launch, sandbox, parity), the reference engine and gate in core/quant, portfolio and risk modules,
  multi-asset data and analytics (equities, bonds/rates, FX, crypto, derivatives), ledgers and tests. Use for any
  QUANTGEN task that touches Nautilus, a backtest, a strategy, validation, a portfolio or risk number. Its rules win
  over the generic nautilus-trader, nautilus-authoring, strategy-workflow, tearsheet-generator and
  portfolio-optimizer skills.
---

# QUANTGEN: NautilusTrader bridge and research-to-portfolio workflow

Written 2026-11-23 from the repository itself. The governing document is
`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` ("the spec"); where this skill and the spec differ,
the spec wins. Status and next items: the newest `docs/nautilus_bridge/REMAINING_WORK_*.md`, the handoff ledger
(`CLAUDE.md`), and `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`.

## What the bridge is

A second, independent engine for QUANTGEN's gate. QUANTGEN decides verdicts from a matrix of daily net returns made
by its own vectorised simulator (`core/quant/strategies.py` `simulate`, `pnl_matrix`). The bridge re-runs the same
rules in a NautilusTrader `BacktestEngine` (event driven, simulated fills, whole shares, cash account), checks parity
between the two engines, and feeds the Nautilus matrices to the unchanged gate. A card is written only when parity
holds and both engines reach the same verdict (spec 5.5).

Scope (spec section 1): backtest only, research only, single-instrument long/flat rules only. Two pilots:
SPY trend switch (12 settings, family E1) and BTC-USD crypto trend (5 settings, family C3, only if pilot 1 passes).

## Hard rules (spec sections 3 and 5.6)

- **No live trading here.** `TradingNode`, live clients, adapters, network clients and API keys are TRADEGEN's
  domain. No QUANTGEN file imports `nautilus_trader.live`, `.adapters`, `.network`, `.core.nautilus_pyo3` or
  `.backtest.node`. Upstream skills that show live nodes, venue patches or leverage setters do not apply.
- **One file places simulated orders:** `tools/nautilus/sandbox.py`, through the one `self.submit_order` in
  `Port.place`. These seven verbs are forbidden in every scanned file, sandbox included: `modify_order`,
  `cancel_orders`, `cancel_all_orders`, `close_position`, `close_all_positions`, `market_exit`, `submit_order_list`.
  The T-RO-01 scan in `tests/macro_m0_harness.py` enforces this (constants `NAUTILUS_ALLOWED_FROM`,
  `NAUTILUS_DENIED_PREFIXES`, `NAUTILUS_DENIED_NAMES`, `NAUTILUS_ORDER_VERBS`) over `core/`, `data/`, `ui/`,
  `tools/`, `papers/`, `docs/*.py`, `main.py` and `config.py`. Bridge code also contains no T-RO-01 text token
  (the case-sensitive `CANO` matches `CANONICAL`).
- **Sandbox language** (spec 5.2.2, rule F): imports exactly the allow-list; no `os`, `sys` (except
  `from sys import argv, exit`), `subprocess`, `socket`, `importlib`; no `getattr`/`setattr`/`eval`/`exec`/`open`;
  no dunder attributes, so no `super().__init__`: parameters live in a frozen `PortConfig(StrategyConfig)`, state is
  set in `on_start`; file access only through `inside(...)`.
- **Two processes, files as the interface.** The parent (`tools/nautilus/runner.py`, global interpreter) never
  imports `nautilus_trader`; it launches one child per (column, cost level) through `tools/nautilus/launch.py`
  (`-I -B -X utf8`, minimal environment, fresh temp dir, no `.env` key, tree kill on timeout). The child gets
  `input.json` + `bars.csv` and writes `fills.csv`, `decisions.csv`, `onbar_equity.csv`, `manifest.json`. No catalog,
  no streaming, no database, no network (egress blocked: `tools/nautilus/egress_probe.py`).
- **Pinned versions.** `nautilus-trader==1.231.0`, hash-pinned in `requirements-nautilus.txt`, installed only into
  `%LOCALAPPDATA%\quantgen\ntvenv` (base interpreter `%LOCALAPPDATA%\quantgen\py313`), named by `.env` key
  `QUANTGEN_NAUTILUS_PYTHON`. Never install Nautilus, pyarrow or anything else into the global interpreter, which
  keeps numpy 2.3.5, scipy 1.18.0, pandas 2.3.3 (`tests/frozen_guard.py`). `requirements.txt`,
  `requirements-dev.txt` and `pyproject.toml` stay byte-identical. A new dependency needs the owner.
- **Determinism.** `FillModel(random_seed=42)`; one process per cost level; no UUID, run id or clock value in a
  result hash. Windows wheels are standard precision: 9 price decimals, volume 1e9 (spec 3.6).
- **Ledgers are append-only and hash-chained** (`core/quant/gate_ledger.py`: `family_ledger`, `register_trial`,
  `ledger_hash`). Register every variant before its first engine run. Production ledgers live in
  `config.macro_dir() / "ledgers"` (default `~/.nextgen/macro/ledgers`, moved by `QUANTGEN_MACRO_DIR`); tests and
  rehearsals write ledgers only to temp dirs. Never edit `gate_ledger.py` or another harness source.
- **Unseen windows.** Pilot 1 is SPY from 2004-12-01, pilot 2 the whole BTC-USD cache: never computed on before
  registration. Claude's rehearsals use synthetic data in the temp root only; the runner refuses any file of
  `docs/asset_expansion/cache/` or a byte copy of one.
- **Never concurrent.** No pilot while the suite or a frozen-study readout runs; one runner per table (OS lock).
- **Who runs what.** Claude runs rehearsals and layer-1 tests. Of-record runs, Step 7A and `owner_confirmed` are the
  owner's, on the owner's Windows machine (`docs/nautilus_bridge/RUNBOOK_windows.md`). Never edit `paper_live/` or
  `grokteam/`, or run their replay, grid, verdict, sameday or calibrate modules.
- **Files.** `tests/run_all.py`, `README.md`, `requirements.txt`, `pyproject.toml`, `config.py` are CRLF: edit with
  the Edit tool only, never renormalise (`.gitattributes` is `* -text`); `config.py` is not edited. In bridge code
  every `open`/`read_text`/`write_text` passes `encoding="utf-8"`, text writes `newline="\n"`, `csv.writer`
  `lineterminator="\n"`, text-mode `subprocess` `encoding="utf-8", errors="replace"` (house locale cp949).

## Codebase map

| Area | Path | What is there |
|---|---|---|
| Bridge parent | `tools/nautilus/runner.py` | modes, registration, reference matrices, children, reconstruction; exit 0 card/clean, 1 WITHHELD, 2-3 refused, 4 ERROR, 5 ABORTED |
| Launch contract | `tools/nautilus/launch.py` | argv/env of every child, venv reads, wheel identity, import census |
| Sandbox child | `tools/nautilus/sandbox.py` | `build_engine`, `make_fee_model`, `make_instrument`, `PortConfig`, `Port`, `TrendSwitchPort`, `CryptoTrendPort`, backtest guards |
| Parity and gate | `tools/nautilus/parity.py` | checks P0b-P13, walk-forward selection on both matrices, card rules |
| Registration | `tools/nautilus/register_e1.py`, `docs/nautilus_bridge/registration/*.json` | E1 registration-only path (O11 A2); pilot tables (owner-edited, read as `utf-8-sig`) |
| Goldens | `tools/nautilus/golden/` | fixtures F1, F2, N1, env pins, import-census baselines per platform |
| Run outputs | `docs/nautilus_bridge/runs/<bridge_run_id>/` | run records; receipts are git-ignored |
| Reference engine | `core/quant/strategies.py` | `simulate`, `pnl_matrix`, `grid_from`, `trend_switch`, `crypto_trend`, `tsmom`, `xs_momentum`, `vol_target`, `risk_parity`, `pairs` |
| Gate and validation | `core/quant/validate.py` | `COST_BP_PER_SIDE`, `data_checks`, `walk_forward`, `deflated_sharpe`, `pbo_cscv`, `block_bootstrap_ci`, `score_strategy`, `ModelCard`; `gate_ledger.py`, `gate_package.py`, `gate_stats.py` |
| Costs | `core/quant/instruments.py`, `core/quant/costed.py` | cost floor (commission + half tick + table), costed golden engine |
| Portfolio | `core/quant/optimize.py`, `core/quant/sleeves.py` | `optimize_portfolio` (max-Sharpe, min-vol, risk parity), `efficient_frontier`, `ledoit_wolf_cov`, `inverse_vol_weights`; factor sleeves, `apply_overlays`, `build_specification_book`, `build_recommended_book` |
| Risk | `core/quant/risk.py`, `core/quant/risk_layer.py` | `analyze_history`, `portfolio_point`; vol target, composition, hedge state |
| Context only | `core/quant/scenarios.py`, `core/quant/montecarlo.py`, `core/quant/lab.py` | results carry `acts = False`; no sizing module may read them |
| Bridge tests | `tests/nautilus_acceptance.py`, `tests/macro_m0_harness.py` | layer 1 always runs; layer 2 needs the venv, else NotRun |

## Multi-asset coverage

| Asset class | Analytics | Data |
|---|---|---|
| Equities and ETFs | `core/quant/*`, `core/market/*` | `data/krx/` (KIS quotes and bars, KRX snapshots, OpenDART), `data/fmp/` (non-Korean quotes), `docs/asset_expansion/cache/yf_*.csv` |
| Bonds and rates | `core/ficc/bonds.py`, `curves.py`, `curve_models.py`, `swaps.py`, `ratesim.py`, `pit.py` | `core/ficc/data.py` (FRED and the other FICC sources; the only network module in `core.ficc`) |
| FX | `core/ficc/fx.py`, `fx_styles.py`, `forward_conventions.py` | FRED via `core/ficc/data.py`; `fred_DEXKOUS.csv` cache |
| Crypto | `core/crypto/analytics.py`, `funding_diagnostic.py` | `data/crypto/` (keyless Upbit, Binance), `binance_*.csv` and `upbit_*.csv` caches |
| Derivatives | `core/ficc/equity_deriv.py`, `swaps.py` (swaptions, caps/floors), `vol_products.py`, `sabr_diagnostics.py`, `structured.py` | `data/kis_markets.py` (KIS domains beyond KRX stocks) |
| Macro context | `core/ficc/macro.py`, `macro_schema.py`, `macro_artifacts.py`, `data/macro/` | `data/macro/series_registry.yaml` |

The bridge itself covers only `Equity` (SPY) and spot `CurrencyPair` (BTC/USD), long/flat, one instrument per run.
Bonds, FX, swaps and options are analysed in `core/ficc`, not in Nautilus. A new instrument class, a multi-sleeve
book or a realism leg (fill delay) in the bridge is a spec change with an owner ruling, not a code edit.

## Research-to-portfolio workflow

1. **Hypothesis and registration.** State the rule, grid and window; check the ledger (`CLAUDE.md`) and
   `REMAINING_WORK_*` for an existing ID. Register every configuration in its family ledger before any run.
2. **Reference engine.** Write the rule as `prices (T x N) -> weights (T x N)`, decided from prices up to t and held
   over t to t+1; run `simulate` / `pnl_matrix` with `cost_bps` from `COST_BP_PER_SIDE` and the instrument floor.
3. **Validation.** `data_checks`, `walk_forward`, `deflated_sharpe` with `n_trials` from the family ledger,
   `pbo_cscv`, `block_bootstrap_ci`, then `score_strategy`. More trials lower the DSR; report the count used.
4. **Independent leg (single-instrument long/flat rules).** A port in `sandbox.py` re-implements the rule; rehearse:
   `python -B -m tools.nautilus.runner --table <t> --rehearsal --ledger-dir <tmp> --out-dir <tmp>`.
   Of-record (`--of-record`) is the owner's, on Windows. A card needs parity and agreement; WITHHELD is a result.
5. **Portfolio.** Combine validated sleeves with `core/quant/optimize.py` and `core/quant/sleeves.py`; risk with
   `core/quant/risk.py` and `risk_layer.py`. Scenarios, Monte Carlo and lab output are context and never feed sizing.
6. **Report.** Numbers come from QUANTGEN's engine and gate, each with its command and output path. The
   `tearsheet-generator` skill is for layout; its leverage maths is crypto-perp analysis, not an instruction.
7. **Record.** Push the work branch and publish the handoff document and ledger row as `CLAUDE.md` says.

## Checks

- `python -m tests.nautilus_acceptance` (layer 1; prints only) and `python -m tests.macro_m0_harness` (T-RO-01).
- Bridge self-checks that need the venv: `python -B -m tools.nautilus.runner --check-env`, `--fixtures`.
- Never `python tests/run_all.py` in a Linux container (it writes `qa/acceptance_results.json`); every commit leaves
  that file byte-identical. The Windows full run is the suite of record.
- Check a Nautilus API in the installed source (`%LOCALAPPDATA%\quantgen\ntvenv\Lib\site-packages\nautilus_trader`,
  `.pyx` included) before trusting the v1.222.0 docs in the `nautilus-trader` skill.

## The other skills and the agent

| Skill or agent | Use it for | QUANTGEN limit |
|---|---|---|
| `nautilus-trader` | generic Nautilus API and docs | docs are v1.222.0; QUANTGEN builds engines as spec 5.2.3 says |
| `nautilus-authoring` | Nautilus pitfalls, checked on 1.231.0 | the sandbox's language rules are stricter |
| `strategy-workflow` | hypothesis-to-OOS methodology | the gate and ledger decide, not "top K by Sharpe" |
| `tearsheet-generator` | report layout, MAE and leverage maths | presentation only |
| `portfolio-optimizer` | allocation checklist | implementations are in `core/quant/optimize.py` |
| `.claude/agents/quant-analyst.md` | delegated quant research | research and paper only; follows this skill |
