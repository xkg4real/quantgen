# 02. What QUANTGEN's gate, trial ledger and Strategy Lab expect as input

Scope: the input side of the NautilusTrader bridge. It covers what a Nautilus `BacktestEngine` run must hand to
QUANTGEN so that QUANTGEN's own gate, trial ledger and Strategy Lab can use it. Nautilus internals are out of
scope here.

Method: I read the code at commit `716bf7778fc3f604de9a684d61892e5d199f7304` (Linux clone). I ran no strategy and
no grid. I wrote no ledger row. A SPY-only trend grid run now, before registration, would itself be an
unregistered trial of the pilot. So I did not compute any SPY-only number. Every repo claim cites `file:line`.
Anything I could not check is marked UNVERIFIED.

---

## 0. Ten findings that shape the bridge

1. The gate takes arrays, not an engine. `walk_forward(pnl, dates, *, turnover, pnl_stress, w_is, w_oos,
   embargo, min_is)` takes a T x G matrix of daily net P&L, one column per configuration
   (`core/quant/validate.py:345-381`). A Nautilus leg has to produce that matrix, plus a 2x-cost twin and a
   turnover matrix of the same shape. It has to run every grid point over the full sample.
2. There is no separate purge parameter. "Purge + embargo" in QUANTGEN is one integer, `embargo`. It sets the
   number of sessions between the end of the in-sample window and the start of the out-of-sample block
   (`validate.py:347-351, 370-375`). The caller sets it to the holding period. The trend study uses 21
   (`docs/asset_expansion_study.py:278`); the crypto study uses 1 (`docs/asset_expansion_study.py:337`).
3. Today the DSR trial count does not come from the ledger. `score_strategy(..., n_trials=...)` takes a number
   (`validate.py:492-497, 507`). The study passes `len(grid)` or a hand-typed 11
   (`docs/asset_expansion_study.py:182, 339`). The Lab passes `len(grid)` even after it registers rows
   (`ui/strategy_lab_page.py:118, 127`). The Lab's own tooltip says so (`ui/strategy_lab_page.py:254-256`).
   The README says "the deflated Sharpe ratio for every trial ever run" (`README.md:258-259`). The code does not
   do that yet. The bridge must choose the count itself (open question Q1).
4. The Lab registers after the run, not before. It registers after `pnl_matrix` and `walk_forward` and before
   `score_strategy` (`ui/strategy_lab_page.py:114-118`). The comment says "registered before it is scored"
   (`ui/strategy_lab_page.py:117`). The bridge requirement is stricter: register before the engine starts.
   `register_trial` needs only metadata that is known before a run (section 3.2), so this is possible.
5. A SPY trend strategy files under family `E1`. The Lab maps `trend_switch` to `E1`
   (`ui/strategy_lab_page.py:50`). Test 17 pins family `E1` and market `US` for SPY
   (`tests/paper_live_acceptance.py:333-343`).
6. The ledger refuses unknown fields. A new `engine` or `run_id` column is refused
   (`core/quant/gate_ledger.py:190-192`). An engine tag can go in the free-text `source` field. That field is
   outside the configuration key, so N stays the same. It can also go in `params`. That makes a new
   configuration, so N rises by one per variant (section 3.5).
7. No stored SPY-only trend card exists. The 12-setting grid card `S_E1_trend_us` is a four-sleeve book: SPY,
   QQQ, TLT and GLD at 1/4 each (`docs/asset_expansion_study.py:243, 724`). Its stored verdict is REJECT
   (`docs/asset_expansion/manifest.json:46`). Pilot 1 (SPY alone) is a new set of configurations.
8. The Strategy Lab scorecard directory is closed to new cards. A test asserts that it holds exactly 34 files
   (`tests/macro_m7_cards.py:833`). The suite treats it as read-only (`tests/macro_acceptance.py:26-27`). The
   asset study rewrites every card in it (`docs/asset_expansion_study.py:775-780`). A Nautilus card needs its own
   directory, and the Lab needs a second loader.
9. The cost rows are US 50 bp per side and crypto 10 bp per side (`validate.py:78`). The cost is charged per unit
   of |Δw|, the initial entry included (`core/quant/strategies.py:20-22, 88-89`). A full SPY switch in and out
   costs 100 bp at 1x and 200 bp at 2x.
10. The read-only scan blocks Nautilus strategy code inside the scanned trees. Nautilus strategies call
    `submit_order` / `cancel_order`. The installed 1.231.0 source defines them at
    `nautilus_trader/trading/strategy.pyx:805, 1089` (in the scratchpad venv; repository
    https://github.com/nautechsystems/nautilus_trader). Both names are forbidden calls in T-RO-01
    (`tests/macro_m0_harness.py:29, 45-46`). The scan covers `core/`, `data/`, `ui/`, `main.py`, `config.py`,
    top-level `docs/*.py`, `tools/` and `papers/` (`tests/acceptance.py:50-56`,
    `tests/macro_m0_harness.py:63-71`). `tests/acceptance.py:62-68` also greps raw text for `submit_order`,
    comments included.

---

## 1. (a) Walk-forward: parameters and the function that takes the P&L matrix

### 1.1 Parameters

| Item | Value | Where |
|---|---|---|
| In-sample window `w_is` | 756 sessions | `core/quant/validate.py:54` |
| Out-of-sample block `w_oos` | 126 sessions | `validate.py:54` |
| Short-sample fallback `min_is` | 504 sessions (used only when `T - w_is < w_oos + embargo`) | `validate.py:54, 365` |
| Embargo (the only "purge") | default 0; the caller passes the holding period | `validate.py:347`; trend 21 `docs/asset_expansion_study.py:278`; crypto 1 `:337`; Lab per family `ui/strategy_lab_page.py:35-45` |
| Origin step | `w_oos` (OOS blocks tile without overlap or gap) | `validate.py:350-351, 377` |
| Winner at each origin | argmax of the annualised Sharpe on `[o - w_is, o)` | `validate.py:371-373` |
| OOS block | `[o + embargo, o + embargo + w_oos)`, truncated at T | `validate.py:374-375` |
| Minimum length | `first + embargo + 21` P&L rows, else `ValueError` | `validate.py:366-367` |
| Annualisation | 252 (also for 7-day crypto) | `validate.py:48, 143` |

How it works: the IS window is `[o - 756, o)`. The OOS block starts `embargo` sessions after `o`. The next
origin is `o + 126`. Its IS window includes the previous OOS block. This is the usual rolling scheme. The
`embargo` sessions are dropped only once, at the first origin. After that the blocks are contiguous
(`validate.py:369-377`). No label-overlap purge exists. The columns are realised daily P&L, not forward labels.

### 1.2 The "about five years of OOS" rule

- `oos_years_min = 5` (`validate.py:56`).
- `n_years` counts whole anniversaries between the first and last OOS date (`validate.py:421-424, 437`). It is
  computed on `wf.dates`, the OOS dates (`validate.py:509`).
- The OOS block must also hold at least `round(5 x 252) = 1,260` sessions (`validate.py:585`).
- Fewer than 30 trades, fewer than 5 full years, or fewer than 1,260 OOS sessions gives INSUFFICIENT_DATA with
  the target "extend history" (`validate.py:586-591`).
- With embargo 21, a verdict therefore needs at least 756 + 21 + 1,260 = 2,037 P&L rows and 5 full calendar
  years of OOS dates. For 7-day crypto the 5-calendar-year clause binds (about 1,826 rows of OOS).
- Reference point: `S_E1_trend_us` on 2004-12-01 to 2026-09-25 had 5,489 sessions. It got 4,711 OOS sessions,
  19 full years and 38 origins (`docs/asset_expansion/cards/S_E1_trend_us.json`, fields `data`, `n_sessions`,
  `n_years`, `walk_forward`). 5,488 - 756 - 21 = 4,711, so the arithmetic above reproduces the card.

### 1.3 Signatures (verbatim)

```python
# core/quant/validate.py:345-347
def walk_forward(pnl: np.ndarray, dates: Sequence[str], *, turnover: Optional[np.ndarray] = None,
                 pnl_stress: Optional[np.ndarray] = None, w_is: int = GATE["w_is"],
                 w_oos: int = GATE["w_oos"], embargo: int = 0, min_is: int = GATE["min_is"]) -> WalkForward

# core/quant/validate.py:492-494
def score_strategy(wf: WalkForward, *, grid: Sequence[dict], full_pnl: np.ndarray, n_trials: int,
                   bench_daily: Optional[np.ndarray] = None, seed: int = 11,
                   domain: Optional[dict] = None) -> StrategyScore

# core/quant/strategies.py:379-380 (the vectorised producer of the three matrices)
def pnl_matrix(prices: np.ndarray, fn: Callable, grid: Sequence[dict], *, cost_bps: float,
               cash_daily: np.ndarray | float = 0.0, stress: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]
```

`WalkForward` holds the OOS `dates`, `pnl`, `pnl_stress`, `turnover`, `origins`, `chosen`, `is_sharpes`
(n_origins x G), `n_configs` and `note` (`validate.py:332-342`).

### 1.4 The input contract a Nautilus leg must meet

| Argument | Shape and meaning | Where it is defined |
|---|---|---|
| `pnl` (and `full_pnl`) | (T-1) x G float. Row i is the net return from close `dates[i]` to close `dates[i+1]`, as a fraction of equity. Column g is configuration `grid[g]`, run causally over the WHOLE sample. | `validate.py:335, 348-352`; `strategies.py:82-90` |
| `dates` | T-1 ISO strings `YYYY-MM-DD`, i.e. `panel.dates[1:]`. Row i is labelled with the date its return is earned. | `docs/asset_expansion_study.py:184`; `validate.py:357-358` (length check), `:423, 433` (string parsing) |
| `pnl_stress` | Same shape, same weights, costs x2. | `strategies.py:387`; `validate.py:336, 359` |
| `turnover` | Same shape. Sum over symbols of abs(Δw) per session. A session with any nonzero value counts as one "position change". | `strategies.py:88-90`; `validate.py:514` |
| `grid` | list of dicts, same order as the columns. The plateau test reads the axis values. | `validate.py:384-418, 510-511` |
| `n_trials` | int, the DSR trial count (see 2.3). | `validate.py:497, 507` |
| `bench_daily` | OOS-aligned benchmark daily returns, `len == len(wf.pnl)`. Otherwise the benchmark test is skipped silently. | `docs/asset_expansion_study.py:186-190`; `validate.py:516, 520-521` |
| `domain` | optional `{param: (lo, hi)}` natural limits (not an edge) | `validate.py:390-391, 404-406` |
| `seed` | 11 (study) | `docs/asset_expansion_study.py:61, 193` |

`full_pnl` must be the same 1x matrix that `walk_forward` saw. CSCV uses it (`validate.py:508`). So does the
DSR's trial dispersion (`validate.py:505-506`). The bootstrap uses `GATE["bootstrap_B"] = 2000` (`validate.py:54`).
The Lab lowers it to 1,000 for a run and then restores it (`ui/strategy_lab_page.py:124-129`). `techfund_study`
refuses to run if GATE was mutated (`docs/techfund_study.py:433-437`). The bridge should score at 2,000.

The study pipeline (`strategy_card`, `docs/asset_expansion_study.py:173-215`) runs in this order:
`pnl_matrix -> walk_forward(embargo) -> align benchmark to wf.dates -> score_strategy -> ModelCard`. The bridge
should keep the same order, with Nautilus producing the three matrices.

---

## 2. (b) The decision rules

### 2.1 Thresholds (`GATE`, `core/quant/validate.py:53-74`)

| Key | Value | Line |
|---|---|---|
| `ci_level` | 0.90 (studentised circular block bootstrap, block 10, B 2000) | 54 |
| `dsr_min` | 0.95 | 55 |
| `pbo_max` / `pbo_reject` | 0.05 / 0.20 | 55 |
| `oos_is_min` | 0.5 | 55 |
| `years_pos_min` | 0.60 | 55 |
| `plateau_min` | 0.5 | 56 |
| `trades_min` / `trades_floor` | 100 / 30 | 56 |
| `oos_years_min` | 5 | 56 |
| `haircut` / `cost_stress` | 0.6 / 2.0 | 57 |
| `pbo_min_configs` / `prob_loss_max` | 8 / 0.10 | 68 |
| `bench_p_max` | 0.10 | 71 |

### 2.2 Decision order (`_decide_strategy`, `validate.py:536-622`)

1. INSUFFICIENT_DATA if `n_trades < 30`, or `n_years < 5`, or `n_sessions < 1,260` (`:586-591`).
2. REJECT if any of the following holds (`:592-601`):
   - DSR < 0.95 (finite);
   - PBO is meaningful (G ≥ 8) AND PBO > 0.20 AND the in-sample winner loses OOS in more than 10 % of CSCV splits;
   - Sharpe at 2x costs ≤ 0 AND the 90 % interval's lower bound ≤ 0;
   - a benchmark was supplied and the paired-bootstrap one-sided p > 0.10.
3. PASS if all three hard checks pass and all five engineering checks pass (`:578-583, 602-605`):
   - hard: CI lower bound > 0; DSR ≥ 0.95; over-search OK;
   - engineering: OOS/IS ≥ 0.5; 2x-cost Sharpe > 0; positive-year share ≥ 0.60; plateau ≥ 0.5 and not on an edge;
     trades ≥ 100.
4. INSUFFICIENT_DATA if only the interval fails (DSR and PBO pass) and the OOS sessions are fewer than Lo's
   minimum track record (`:584, 606-612`).
5. Otherwise REVISE. The target is the first failed engineering check, in this order: over-search, execution,
   regime, plateau, sample. If none failed, the target is "interval" (`:613-622`).

### 2.3 DSR and where `n_trials` comes from

- DSR follows Bailey and López de Prado. It is computed on the OOS P&L. The expected maximum of `n_trials`
  null Sharpes uses the dispersion of the CURRENT grid's full-sample column Sharpes, per period
  (`validate.py:211-237, 505-507`). The dispersion uses only this run's G columns, even when `n_trials > G`.
- `n_trials` is a plain argument. Nothing in the strategy loop reads the ledger:
  - the asset study: `n_trials or len(grid)` (`docs/asset_expansion_study.py:182`); C3 hand-set to 11 (`:339`);
  - techfund CRY-1: card `N_total` + 3 (`docs/techfund_study.py:445-446`);
  - Strategy Lab: `len(grid)` (`ui/strategy_lab_page.py:127`).
- The ledger's N (`N_raw`, `N_eff = max(N_clusters, N_equiv)`) is used only by the v2 macro step 3
  (`core/quant/gate_ledger.py:574-582, 748-813`) and by v2 header commits (`core/quant/cards.py:615-624`).
- So "DSR with the ledger's trial count" is a new rule for the bridge. Options are in Q1.

### 2.4 The 2x-cost rule

- The stress matrix re-simulates the same weights at `cost_bps x 2` (`strategies.py:380, 387`).
- `sr_stress = sharpe(wf.pnl_stress)` (`validate.py:525`).
- REJECT when `sr_stress ≤ 0` and the interval includes zero (`validate.py:594`). Otherwise `sr_stress ≤ 0` fails
  the "execution" check, and the target is "never lower the cost assumption" (`validate.py:580, 617`).
- The Lab withholds the verdict when a typed cost is below the table rate or a symbol has no cost row
  (`ui/strategy_lab_page.py:87-103, 150-155`).

### 2.5 PBO and the plateau fix ("the earlier plateau fix")

- PBO uses CSCV on `full_pnl`. It uses S = 8 blocks when T < 2,000 and S = 16 otherwise (`validate.py:240-265, 508`).
  The 2004-2026 trend sample has about 5,488 rows, so S = 16 and there are C(16,8) = 12,870 splits.
- With fewer than 8 configurations PBO is reported only. The over-search check then uses the share of splits in
  which the IS winner loses OOS, which must be ≤ 0.10 (`validate.py:544-555, 576`). Pilot 2's five-point
  hysteresis lattice falls under this rule.
- PBO fix (run 2 → run 3): PBO alone used to reject flat plateaus. Now over-search passes when PBO ≤ 0.05 OR
  `prob_loss_oos ≤ 0.10`. REJECT needs PBO > 0.20 AND a losing winner (`validate.py:58-68, 576-577`;
  `docs/ASSET_EXPANSION_SPEC.md:109-112`; `README.md:310-312`).
- Plateau fix: an edge exists only on an axis with three or more values. A declared natural limit (`domain`) is
  not an edge (`validate.py:384-418`, especially `:406`; `docs/ASSET_EXPANSION_SPEC.md:111`).
- The plateau is read at the LAST origin, from its IS Sharpes and its chosen column (`validate.py:510-511`). It
  counts ±1-step neighbours with Sharpe ≥ half of the best's (`:416-417`).
- For the 12-grid, `rule` (2 values) and `step` (2 values) can never be edges. `lookback` {126, 210, 252} is an
  edge when the last winner sits at 126 or 252. `S_E1_trend_us` failed the plateau test this way: its last pick
  was `{sma, 126, 21}` with edge true (card `stats.chosen_last`, `stats.edge`).

### 2.6 What a SPY-only Pilot 1 is likely to meet (UNVERIFIED: no run was made, on purpose)

- Trades: the four-sleeve card made 82 position changes in 19 years (`docs/asset_expansion/results.md:9`). A
  one-sleeve book can only have the same number of switch days or fewer. Fewer than 100 fails the "sample" check;
  fewer than 30 gives INSUFFICIENT_DATA.
- Benchmark: for one sleeve the benchmark is SPY buy-and-hold (`docs/asset_expansion_study.py:275` with N = 1).
  Failing p ≤ 0.10 is a REJECT. That is what sank `S_E1_trend_us` (`docs/asset_expansion/results.md:9`).
- Edge: see 2.5.

---

## 3. (c) The trial ledger

### 3.1 Where and what

- One append-only, hash-chained JSONL file per family: `<ledger_dir>/<family_id>.jsonl`
  (`core/quant/gate_ledger.py:265-273, 375-376`).
- `ledger_dir` defaults to `config.macro_dir() / "ledgers"`, which is `~/.nextgen/macro/ledgers`. It can be moved
  with `QUANTGEN_MACRO_DIR` (`config.py:176-178`; Lab `ui/strategy_lab_page.py:67`; paper_live
  `paper_live/engine.py:103`).
- On this Linux clone `~/.nextgen` does not exist. Whether `E1.jsonl` exists on the owner's Windows machine, and
  how many rows it holds, is UNVERIFIED.

### 3.2 API: register before the run

```python
# core/quant/gate_ledger.py:375, 379
family_ledger(family_id: str, ledger_dir: Path) -> FamilyLedger
register_trial(ledger: FamilyLedger, row: Mapping, *, script: str | None = None) -> RegisterResult  # (row, appended, row_md5)
```

- `register_trial` delegates to `FamilyLedger.append` (`gate_ledger.py:337-355`). It validates the row, takes an
  OS file lock, verifies the whole chain, then either returns the existing row for a duplicate `config_id`
  (`appended=False`) or appends with fsync.
- It raises on a broken chain or a refused row. Nothing is written in that case (`gate_ledger.py:311-316, 340-346`).
  So the bridge can treat a raise as "do not run".
- Every required field is known before a run: rule, params, timing class, span, market, `run_utc`, phase and
  script. Precedent for registering first: `paper_live.register_trials` says it "raises on a broken ledger chain,
  before anything runs" (`paper_live/engine.py:96-113`).
- Other calls: `FamilyLedger.rows()`, `.verify_chain()`, `.hash()`, `.snapshot(hash)`, `.n_raw`
  (`gate_ledger.py:284-334`); `assert_hash_at_run` (`:389-396`); and a multi-family wrapper
  `tf_gov.TrialRegistry` with `global_n()` (`core/quant/tf_gov.py:350-379`).

### 3.3 Row fields (`gate_ledger.py:63-66, 182-214`)

| Kind | Fields |
|---|---|
| Required, non-empty | `rule, params (mapping), timing_class ∈ {VALUE, NON-COMPLIANT, COMPLIANT}, span [start, end] ISO dates, market, run_utc (tz-aware ISO, e.g. ...Z), phase ∈ {research, card}, script` |
| Optional | `estimator, window, cap, instrument_book, rebalance, start_convention, cost, results_md5, diff_series_ref, card_id, delta_sr, run_kind, run_utc_anchor, source` |
| Added by the ledger | `config_id, family_id, row_md5, prev_row_md5` |
| Refused | any other key (`:190-192`); `run_kind` in the null-distribution kinds (`:57-58, 200-201`) |
| Defaults | `run_kind = "trial"` (`:197, 211`); `run_utc_anchor = "UNVERSIONED"` when absent (`:212`) |

- Configuration key: `config_id = md5(canonical_json({rule, params, estimator, window, cap, instrument_book,
  rebalance, timing_class, start_convention}))` (`gate_ledger.py:60-61, 168-171`).
- `span`, `market`, `run_utc`, `script`, `source`, `cost`, `card_id` and `run_kind` are NOT in the key. A second
  registration that differs only in those fields is the same trial and appends nothing (`:343-346`).
- Test 17 relies on this. A changed span or symbol order does not add rows (`tests/paper_live_acceptance.py:341-343`).

The Lab's row for a SPY trend variant (`ui/strategy_lab_page.py:74-81`):
`rule="E1"`, `params = theta + {"symbols": sorted symbols, "cost_bps": 50.0}`, `timing_class="COMPLIANT"`,
`span=[first date, last date]`, `market="US"`, `run_utc=<now Z>`, `phase="research"`, `run_kind="variant"`,
`run_utc_anchor=repo_anchor()`, `source="Strategy Lab: <data sources>"`, `script="ui/strategy_lab_page.py"`.
Because `symbols` and `cost_bps` sit inside `params`, they ARE part of the key. Synthetic-data runs register
nothing (`:60-61`).

### 3.4 `repo_anchor` and UNVERSIONED

- `repo_anchor()` reads `.git/HEAD` and the loose ref file. It returns `git:<40-hex>` or `UNVERSIONED`
  (`gate_ledger.py:122-131`). On this clone it returned `git:716bf7778fc3f604de9a684d61892e5d199f7304`.
- It has no `packed-refs` fallback. It also fails when `.git` is a file (a worktree). In either case it returns
  UNVERSIONED although the repository is under git. This is by reading the code; I did not test it on Windows
  (UNVERIFIED there).
- Effect: UNVERSIONED rows do not stop the strategy loop. In v2 step 3, an overlapping UNVERSIONED row refuses the
  selection factor (`gate_ledger.py:713-716`). That refusal goes to the card's step 3, not to the ledger append.

### 3.5 Which family a SPY trend strategy belongs to

- `E1`. The Lab's `FAMILY_ID["trend_switch"] = "E1"` (`ui/strategy_lab_page.py:50`), and test 17 pins it
  (`tests/paper_live_acceptance.py:343`).
- `E1` is not in the v2 `RULE_FAMILY` map (`gate_ledger.py:79`). The Lab writes to `family_ledger("E1", ...)`
  directly and never calls `file_family`. `file_family("E1")` would refuse unless a difference series correlates
  ≥ 0.5 with another family (`gate_ledger.py:399-415`).
- Two neighbours exist and should not be confused with E1:
  - v2 macro card `MACRO-R28-US-TREND` (family R-28, US SMA-10-month on CME micro ES, CARD-P, forward-sim)
    (`core/quant/cards.py:129-133`);
  - paper_live files its own "trend" rule under `C3`, with market US/KR (`paper_live/engine.py:64-69`).

### 3.6 How to record a Nautilus run id or engine tag without breaking the chain or the package

The hash chain covers only the bytes already written. A new row never breaks it. Editing an existing row does
(`gate_ledger.py:284-309`). The choices:

| Where the tag goes | Effect on `config_id` and N | Recorded when the config is already registered? | Notes |
|---|---|---|---|
| `source` (free text, optional) | none; same trial | No: the first row stands, the new `source` is dropped (`:343-346`) | Best fit if the Nautilus and vectorised legs of one variant count as ONE trial. Write both engine names and the bridge run id into `source` on the first registration. |
| `script` | none | No | Same as `source`; holds a path. |
| `params.engine = "nautilus"` (or a run id inside params) | new `config_id` → +1 N_raw per variant (+12 for Pilot 1) | Yes, as a new row | Counts the second engine as a new trial. A run id in params makes every re-run a new trial and inflates N without bound. Do not do this. |
| `estimator` / `instrument_book` / `rebalance` / `start_convention` | in the key → new trial | Yes | Misuses fields that carry meaning in v2 (`gate_ledger.py:60-61`). |
| New top-level field (`engine`, `venue`, `run_id`) | refused (`LedgerRefused`) | No | Needs a `gate_ledger.py` edit. That is a harness source of the gate package (`core/quant/gate_package.py:36-38`). Avoid. |
| `results_md5` / `diff_series_ref` | not in the key | Only if known at registration | Unknown before the run. Rows are immutable, so post-run evidence cannot be added later. |

Recommendation (a design reading, for the owner to confirm):
- Register each variant once, before either engine runs, with Lab-shaped `params`. Use `cost_bps` = the table
  rate, not the 2x rate. Put the engine names, the `nautilus_trader` version and a bridge run id in `source`.
- Keep the per-engine results, the parity numbers and `results_md5` in a separate bridge run record. Key that
  record by `config_id` and `row_md5`. The card's `trials` dict can carry the family id, the config ids and
  `ledger_hash_at_run`, because `ModelCard.trials` is a free dict (`validate.py:812`).
- Do not register the 2x-cost rerun as its own row. A Lab-shaped row at 100 bp would be a new `config_id`,
  because `cost_bps` is inside `params`. The 2x leg is the gate's stress column (`GATE["cost_stress"]`), not a
  new hypothesis.

### 3.7 Does a new-engine trial change N_eff of an existing family?

- With the tag outside the key (in `source`): nothing is appended for an existing configuration. N_raw and N_eff
  do not change. A new configuration, such as SPY-only, adds one row per variant, whichever engine ran it.
- With the tag inside `params`: each Nautilus variant adds a row. N_raw rises by G.
  - N_eff = max(N_clusters, N_equiv) is computed from stored difference series (`gate_ledger.py:574-582`).
  - A Nautilus twin that passes parity (daily correlation ≥ 0.99) falls into its vectorised twin's cluster.
    The clustering cuts at ρ ≥ 0.5 (`:473-483`), so N_clusters stays the same.
  - E[max] rises only slightly when near-duplicate columns are added, so N_equiv moves a little (UNVERIFIED
    magnitude, not computed).
- For E1 today, N_eff cannot be computed. Lab rows carry no `diff_series_ref` (`ui/strategy_lab_page.py:74-81`),
  so `difference_series` raises `CorrUnavailable` (`gate_ledger.py:357-368`).
- In any case the strategy-loop DSR does not read N_eff (2.3).
- Committed v2 headers are protected. Step 3 reads the ledger prefix named by `ledger_hash_at_registration`
  (`gate_ledger.py:323-330, 762-763`), so rows appended later do not change an existing card's N.

### 3.8 The frozen gate package: what must not change

- The package manifest hashes three things:
  - (a) the `gate.*` store blocks;
  - (b) the harness sources `core/quant/{gate_stats, gate_ledger, cardp, cards, card_lines, instruments, costed,
    validate, strategies, gjr}.py` and `docs/macro_overlay_study.py` (`core/quant/gate_package.py:36-38, 75-101`);
  - (c)-(f) fixtures, seeds, family ledger hashes, the data cut-off and the council answers
    (`gate_package.py:4-7, 92`).
- `verify_package` raises `PackageMismatch` on any difference (`gate_package.py:165-184`). The test
  `tests/macro_m7_cards.py:737` shows that a changed ledger hash alone breaks it.
- Today the package is NOT_FROZEN: `data/macro/rules_v2.0.0.json:1555, 1566`, asserted by
  `tests/macro_m7_cards.py:837`.
- No production caller passes `ledger_hashes` today. The only caller, `docs/macro_overlay_study.py:80`, omits
  them. E1 is not a v2 family. So appending E1 rows does not touch the package. Whether a future freeze will hash
  E1 is UNVERIFIED.
- Rule for the bridge: add new modules only. Edit none of the harness sources above. `validate.py:52` says the
  thresholds change "here and nowhere else".

---

## 4. (d) Strategy Lab cards

### 4.1 Where the Lab reads them

- `CARDS_DIR = ROOT / "docs" / "asset_expansion" / "cards"` (`ui/strategy_lab_page.py:31`).
- `load_cards()` calls `validate.load_cards(CARDS_DIR)`. That reads every `*.json` in sorted order and skips
  unreadable files (`validate.py:847-856`). Each card is normalised by `_study_card`, and the list is sorted
  PASS, REVISE, REJECT, then the rest (`ui/strategy_lab_page.py:296-317`).
- The page's notice says the scorecard lists the asset-expansion study cards only (`ui/strategy_lab_page.py:201-202`).

### 4.2 Keys the page uses (`ui/strategy_lab_page.py:166-198, 296-312`)

| Key | Use | Fallback |
|---|---|---|
| `card_id` | row label, picker | "unnamed card" |
| `decision` | chip; must be in `validate.DECISIONS` = PASS, REVISE, REJECT, INSUFFICIENT_DATA (`validate.py:50`) | shown as `UNKNOWN` |
| `kind` (or `class`) | column | "unknown" |
| `hypothesis` (or `claim`) | italic line | "" |
| `decision_reason`, `revise_target` | decision line | "" |
| `stats` | only numeric values kept. If `stats.sr_oos` is numeric the row shows `SR · DSR · PBO` from `stats.sr_oos/dsr/pbo` | `{}` |
| `tests` | first three numeric values, shown when there is no `sr_oos` | `{}` |
| `lines`, `citations` | bullet list, sources line | `[]` |
| `seed`, `results_md5` | chips | none |

### 4.3 What a card JSON is

`validate.ModelCard` (`validate.py:802-834`) has these fields:
- required: `card_id, kind, hypothesis, rules, universe, data, costs, protocol, trials, seed, stats, tests,
  decision, decision_reason, revise_target, lines`;
- defaulted: `decay_haircut, created, author, results_file, results_md5, citations`.

The study fills them for a strategy as follows (`docs/asset_expansion_study.py:194-210`):
- `stats` = `asdict(StrategyScore)` minus `lines`, plus `regime`, `chosen_last`, `bench_sharpe`, `walk_forward`
  and `seconds`;
- `tests` = `{dsr, pbo, ci90, sr_stress}`;
- `protocol` = GATE's `w_is, w_oos, min_is, ci_level, bootstrap_B, block`;
- `trials` = `{N_planned, N_total, ledger: [free text]}`;
- `costs` = `{cost_bps, stress_multiplier}`.

### 4.4 Constraints on a Nautilus card

- Do not write it into `docs/asset_expansion/cards/`:
  - a test asserts that the directory holds exactly 34 files (`tests/macro_m7_cards.py:833`);
  - the directory is in the suite's `READ_ONLY_TREES` (`tests/macro_acceptance.py:26-27`);
  - the next `--only` study run would rewrite any foreign card's `results_file` / `results_md5` and list it in the
    manifest (`docs/asset_expansion_study.py:775-780, 813-816`).
- The Lab therefore needs a second card directory and a second loader. That is an edit to `ui/strategy_lab_page.py`.
  It is not a harness source, but it is still a tracked-file change outside this task.
- A parity failure must withhold the verdict, and the scorecard has no WITHHELD decision. A card with
  `decision: "WITHHELD"` would show as UNKNOWN (`ui/strategy_lab_page.py:303-305`). The live-run panel has a
  withheld path (`ui/strategy_lab_page.py:98-103, 150-155, 247-251`) that the bridge can copy. See open question Q3.

---

## 5. (e) The existing trend study: grid, data and stored result

### 5.1 Definition

- Grid: `S.grid_from(rule=["sma", "tsmom"], lookback=[126, 210, 252], step=[21, 42])`, 2 x 3 x 2 = 12
  (`docs/asset_expansion_study.py:274`). The Lab repeats it as `FAMILIES["trend_switch"]`
  (`ui/strategy_lab_page.py:35-36`).
- Rule (`strategies.trend_switch`, `core/quant/strategies.py:162-187`):
  - `sma`: hold when `P[t] > SMA(lookback)[t]`. The SMA includes close t (`:172, 178`; `_sma` `:111-116`).
  - `tsmom`: hold when `P[t]/P[t-lookback] - 1 - sum(rf[t-lookback:t]) > 0` (`:180-181`). `pnl_matrix` calls
    `fn(prices, **theta)` without `cash_rate_daily` (`strategies.py:384`). So in the study the tsmom signal uses
    rf = 0, while cash still earns DGS3MO.
  - Evaluated every `step` sessions on panel indices `arange(lookback, T, step)` (`:146-147, 176`). These are not
    calendar month-ends. The schedule moves if the data start moves.
  - Weight 1/N per sleeve that is "on". The rest is held in cash (`:182, 84-87`).
- Universe: `US_SLEEVES = ["SPY", "QQQ", "TLT", "GLD"]` (`docs/asset_expansion_study.py:243`). Card
  `S_E1_trend_us` runs `run_trend(US_SLEEVES, "us", "S_E1_trend_us", "2004-12-01")` (`:724`). This is NOT
  SPY-only.
- Costs: `COST["us"]` = 50 bp per side; 2x stress (`docs/asset_expansion_study.py:60, 278`; `validate.py:78`).
  Embargo 21 (`:278`).
- Benchmark: the equal-weight daily return of the sleeves, uncosted (`docs/asset_expansion_study.py:275`).
- Data: Yahoo `auto_adjust=True` closes (`:85`), cached at `docs/asset_expansion/cache/yf_*.csv`. The SPY cache
  runs 1995-01-03 to 2026-09-25 with 7,986 rows (checked). The panel is the intersection of dates from 2004-12-01
  (`:138-145`). Card data: 5,489 sessions, 2004-12-01 to 2026-09-25.
- Cash: FRED DGS3MO / 100 / 252, forward-filled; fallback 3 % (`:148-153, 273, 279`). The Lab uses a flat 3 %
  (`ui/strategy_lab_page.py:113`).

### 5.2 Stored result (run of record 2026-09-27, seed 11, results md5 `ca757e25f508b588cb2f361719ec83cd`)

`docs/asset_expansion/manifest.json:2-5, 46`; `docs/asset_expansion/results.md:9, 46-61`;
`docs/asset_expansion/results.csv:116-131`; `docs/asset_expansion/cards/S_E1_trend_us.json`.

| Item | Value |
|---|---|
| Decision | **REJECT**: "does not beat its benchmark (Sharpe difference -0.11, p 0.75)" |
| OOS Sharpe, 90 % CI | 0.84 [0.47, 1.20], Lo SE 0.23 |
| DSR (n_trials 12) | 1.00 |
| PBO / prob. IS winner loses | 0.59 / 0.00 (passes under the PBO fix) |
| OOS/IS | 0.70 |
| 2x costs Sharpe | 0.75 |
| Years positive | 74 % (19 full OOS years, 4,711 sessions, 38 origins) |
| Plateau | 100 %, on an edge (last pick `{sma, 126, 21}`): fails |
| Trades | 82: fails (needs 100) |
| Benchmark | SR 0.95; MDD -15 % vs -27 % |
| Turnover | 1.6x equity per year |

An earlier run (run 2) rejected it on "PBO above 0.20" (`docs/asset_expansion/results_run2.md:9`). The PBO fix
changed only the reason. README summary: "the ETF trend switch (protects the drawdown, does not beat buy-and-hold
on Sharpe)" (`README.md:290-291`).

### 5.3 Pilot 2 reference (BTC-USD)

- Card `S_C3_crypto_trend_btcusd` is PASS (`docs/asset_expansion/manifest.json:53`):
  - grid `hysteresis ∈ {0, 0.222, 0.444, 0.667, 0.889}`, domain (0, 0.889), `n_trials = 11`, embargo 1, 10 bp per
    side, data 2014-09-17 to 2026-09-25 (`docs/asset_expansion_study.py:325-343, 731`);
  - SR 1.19 [0.72, 1.64], DSR 1.00, 144 trades, bench p 0.07.
- The Lab's crypto grid is still the old six-value grid `[0.05 ... 0.5]` (`ui/strategy_lab_page.py:42`). The spec
  calls that grid "three rules in six costumes" (`docs/ASSET_EXPANSION_SPEC.md:115-119`). A bridge must use the
  card's lattice, not the Lab's grid.
- `crypto_trend` evaluates daily and is long/flat with hysteresis (`strategies.py:330-348`). Paper_live also
  writes rows into the C3 family (`paper_live/engine.py:69`).

---

## 6. (f) Costs

| Class | bp per side | Applies to | Where |
|---|---|---|---|
| `us` | **50** | US shares and ETFs via KIS. `SPY` resolves here: alphabetic and not in `INSTRUMENTS` | `validate.py:78, 110-111`; `core/quant/instruments.py:81-84` |
| `crypto` | **10** | `BTC-USD`, `*-USDT`, `*-KRW`, `BTC-*` | `validate.py:78, 100-101` |
| `krx_etf` / `krx_stock` / `futures` / `fx` | 3 / 35 / 5 / 10 | (for completeness) | `validate.py:78` |

- Charging rule in the gate path: cost = `cost_bps x 1e-4 x Σ|Δw|`, charged on the session the weight changes.
  The initial entry from zero is charged too (`core/quant/strategies.py:20-22, 88-89`).
- Per switch for a one-sleeve SPY book: 50 bp in, 50 bp out, so 100 bp round trip at 1x and 200 bp at 2x.
- In a 1/N book each sleeve switch costs 50/N bp.
- Weekend crypto slippage: a study card line says it is "set at 2x in the crypto backtests"
  (`docs/asset_expansion_study.py:595`). `strategies.simulate` has no weekend term (`strategies.py:69-90`).
  Treat that line as UNVERIFIED for the gate path.
- The v2 costed engine is a different convention. It leaves the initial entry uncosted (`core/quant/costed.py:5-7,
  154-158`). It is not used by the strategy loop. Do not mix the two in parity.
- The tick floor `max(table, commission + ½ tick/price + tax)` can raise a v2 cost and never lower it
  (`core/quant/instruments.py:1-6`). The strategy loop uses the flat table.
- Background, not binding: a research note puts the all-in cost of a US ETF via KIS at 50 bp commission plus two
  FX conversions, about 55-130 bp round trip (`research_notes/QUANTGEN asset coverage expansion/etf_strategies.md:204`).
  The gate table is the binding number (`validate.py:76-78`).
- `core/quant/backtest.py` (the Signals page) is not on the gate path. Its default is 10 bp
  (`core/quant/backtest.py:107-108`).

---

## 7. Input-side conventions a Nautilus leg must reproduce for parity

| Convention | QUANTGEN | Where |
|---|---|---|
| Decision and fill timing | Weight decided on close t from prices up to and including t, held t to t+1. Cost charged in the same row. Equivalent to a fill at close t. | `strategies.py:3-5, 82-90` |
| Prices | Yahoo adjusted closes (dividends in the price). Raw closes would lose about the dividend yield. | `docs/asset_expansion_study.py:85` |
| Cash | Unallocated long-only weight earns `cash_daily` (DGS3MO in the study, 3 % in the Lab). Whether Nautilus credits interest on idle cash is UNVERIFIED. | `strategies.py:84-87`; `docs/asset_expansion_study.py:148-153` |
| tsmom signal | rf = 0 in the study (see 5.1) | `strategies.py:384` |
| Rebalance schedule | panel-index `arange(lookback, T, step)` | `strategies.py:146-147, 176` |
| Sizing | Fractional weights 1/N. A share-quantity engine rounds, so returns differ slightly. | `strategies.py:182` |
| Initial entry | costed | `strategies.py:88` |
| 2x leg | same weights, costs x2 | `strategies.py:387` |
| Annualisation | 252, also for 7-day crypto | `validate.py:48` |
| Data checks | `validate.data_checks` flags short, duplicate, non-positive, stale-print, ±50 % jump and gap problems | `validate.py:298-326` |
| On/off series for the 98 % agreement test | `W[t]` at the rebalance indices of each grid column | `strategies.py:176-187` |

Process boundary:
- The scratchpad venv holds `nautilus_trader`, numpy 2.3.5 and pandas 2.3.3, but no scipy.
- `validate.py` imports scipy (`validate.py:46`).
- So the hand-off can be arrays written to files: the three matrices, the dates and the grid. The global
  interpreter, pinned by `tests/frozen_guard.py` clause (d), then scores them. Nothing needs installing globally.

---

## 8. Open questions for the owner

- **Q1. DSR trial count.** Which number goes in `n_trials`?
  - `len(grid)` = 12. This is today's convention in the study and the Lab.
  - E1 `N_raw` after the pilot's registration. This is all markets and all Lab runs, and it matches
    `README.md:258-259`.
  - Market-scoped `N_raw` (US). This mirrors step 3's `market_scoped` reading (`gate_ledger.py:709`).
  - My suggestion: use max(len(grid), E1 N_raw at the snapshot) and print both.
- **Q2. Engine tag.** Should the two engines' legs of one variant count as ONE trial (tag in `source`) or two
  (tag in `params`)? See 3.6.
- **Q3. Verdict withheld.** How does a withheld verdict appear in the scorecard? The options are a new card
  directory with its own loader, or no card at all until parity passes.
- **Q4. Ledger directory.** Use `~/.nextgen/macro/ledgers/E1.jsonl` on the owner's machine (production), or a
  bridge-local directory for the pilots? A test of the bridge must use a temp copy (`gate_ledger.temp_copy`,
  `gate_ledger.py:927-933`).
- **Q5. Where the strategy code lives.** The Nautilus strategy code must sit outside the T-RO-01 scan trees, or the
  owner amends the scan. Nothing from Nautilus live or adapter packages may be imported. No such guard exists yet.
  `FORBIDDEN_IMPORTS` does not list `nautilus_trader` (`tests/macro_m0_harness.py:38-42`).

## 9. UNVERIFIED items

- The contents and row counts of the owner's `~/.nextgen/macro/ledgers/*.jsonl` on Windows.
- `repo_anchor()` on the owner's Windows clone (packed refs, OneDrive).
- How a SPY-only 12-grid behaves: trades, edge, benchmark p. Deliberately not run before registration.
- How much N_equiv moves when near-duplicate engine twins are added.
- Whether Nautilus accrues interest on idle cash, and how it sizes fractional or integer quantities. This belongs
  to the Nautilus API map, not this file.
- Whether a future package freeze will include E1 in `ledger_hashes`.
- The "weekend slippage 2x" line in the crypto cards (no code found in `strategies.simulate`).
