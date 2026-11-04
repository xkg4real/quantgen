# 01 — Strategy Lab and the stored cards: how trials are counted and verdicts are reached today

Date: 2026-10-27. Scope: owner ruling R3 (2026-10-27), step 1 (map only).
Status: read-only map. No code was changed. No strategy returns were recomputed. No ledger row was written. The
study was not re-run. No test was run. The four excluded cache files were not opened.

R3 asks for three things. First, give every strategy run a unique ID and a full record. Second, separate the
**total run count** from the **count of experiments valid for overfitting assessment**. Third, compute the ledger
basis in parallel with today's verdicts, without changing today's criteria. This file maps what exists today. It
also shows, card by card, how far each DSR-dependent verdict sits from flipping.

---

## 0. Summary

1. **The gate has one trial-dependent predicate.** `n_trials` enters only the deflated Sharpe ratio (DSR) through
   `expected_max_sharpe(n_trials, sr_sd)` (`core/quant/validate.py:211-217`, `:507`). DSR feeds the PASS
   condition (`:578`, `:602`) and the REJECT condition (`:593-596`). PBO uses the grid size G, not `n_trials`
   (`:508`, `:544`).
2. **The dispersion term comes from the current grid only.** `sr_sd` is the spread of the current grid's
   full-sample Sharpes (`validate.py:505-506`). A one-configuration run has `sr_sd = 0`. Its DSR then does not move
   with N at all (S_V4_dollar_carry).
3. **The Strategy Lab always scores with N = grid size** (`ui/strategy_lab_page.py:127`). It writes one family
   ledger row per configuration (`:55-82`) and shows the family ledger count as a chip. That count is not used in
   the verdict (`:254-256`).
4. **The study scores with N = grid size, except for C3.** C3 uses a typed-in `n_trials=11`
   (`docs/asset_expansion_study.py:339`), with a free-text history (`:340-342`). The study writes nothing to the
   family ledger.
5. **There is no per-run record today.** The Lab persists only ledger rows. Those rows are de-duplicated by
   `config_id`, and `config_id` excludes the data span (`core/quant/gate_ledger.py:60-61`, `:343-346`). A rerun,
   an extended-data rerun or a rerun after a code change leaves no trace. No row carries a result, a verdict or a
   run status. The study overwrites each card file on every run (`docs/asset_expansion_study.py:778-780`).
6. **The stored DSR margins are wide, except on three cards.** With dispersion held at its backed-out value, N
   would have to reach about 1e8 or more to flip either C3 PASS card. Three cards are narrow:
   - S_E8_pairs_kodex_tiger: the DSR predicate fails at about N = 769 (range 320–3,505). The decision would go
     REVISE → REJECT.
   - S_E2_voltarget_kodex200: fails at about N = 89 (range 60–167).
   - S_E5_xsmom_sectors: fails at about N = 81 (range 70–97).

   E2 kodex200 and E5 are already REJECT on the benchmark test. For those two, only the reason text would change.
7. **A ledger basis can also loosen a verdict.** Suppose the valid-experiment count is correlation-adjusted (the
   ledger's `N_eff`, `gate_ledger.py:574-582`) and falls below the grid size. Then S_S6_pairs_hyundai_kia (REJECT on
   DSR at N = 8) passes the DSR predicate, but only at N = 1. Its decision would then become REVISE. No other card
   that fails DSR passes at N = 1.
8. **C3's 11 trials contain at most 5 distinct rules.** Reading `strategies.py:344-346`, the old 6-point grid
   holds 3 distinct rules, and all of them reappear in the new 5-point lattice. The Lab still uses the old 6-point
   grid (`ui/strategy_lab_page.py:42`).
9. **Exact parallel numbers need fields the cards lack.** No card stores the OOS skewness, kurtosis or `sr_sd`.
   The margins below are therefore estimates under stated moment assumptions. For 6 of the 16 DSR cards, an exact
   recomputation in this environment would open an excluded cache file (§9).

---

## 1. Where trials enter the verdict (`core/quant/validate.py`)

### 1.1 The DSR formula as implemented

- `deflated_sharpe(daily, n_trials, sr_sd_daily)` (`validate.py:220-237`):
  `DSR = Φ( (SR − SR0) · √(T−1) / √(1 − g3·SR + (g4−1)/4·SR²) )`.
- SR is the per-period Sharpe of the OOS P&L. T is the number of OOS sessions. g3 is skewness and g4 is kurtosis
  (non-excess) of the OOS P&L (`:226-232`).
- `SR0 = expected_max_sharpe(N, sr_sd) = sr_sd·[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(N·e))]` (`:211-217`). It is 0 at
  N = 1.
- N is truncated to an integer: `n = max(int(n_trials), 1)` (`:213`). A fractional `N_eff` in [1, 2) would become 1.
- The source is Bailey & López de Prado (2014), as the module docstring states (`validate.py:26-28`; see
  References).

### 1.2 What `score_strategy` feeds in (`validate.py:492-533`)

| Input | Where | Source |
|---|---|---|
| OOS P&L `p` | `:498` | concatenated walk-forward OOS blocks (`walk_forward`, `:345-381`) |
| `n_trials` | `:507` | caller argument; the docstring says "every configuration ever tried (grid size plus revisions)" (`:496-497`) |
| `sr_sd_daily` | `:505-506` | `np.nanstd` of the per-column full-sample Sharpes of the **current** grid; 0.0 for one column |
| PBO | `:508` | CSCV over the current grid `full_pnl` (G columns); independent of `n_trials` |
| `n_configs` | `:530` | `wf.n_configs` = G; decides whether PBO is gated (`:544`, `pbo_min_configs = 8` at `:68`) |

### 1.3 Which predicates depend on N (`_decide_strategy`, `validate.py:536-622`)

The decision order is fixed. Only the DSR term depends on `n_trials`.

| Order | Branch | Lines | Depends on N? |
|---|---|---|---|
| 1 | INSUFFICIENT_DATA: trades < 30, or full OOS years < 5, or sessions < 1,260 | `:586-591` | no |
| 2 | REJECT if **DSR < 0.95** (and finite), or PBO reject, or 2× costs ≤ 0 with the CI including 0, or benchmark p > 0.10 | `:593-601` | **yes (first disjunct)** |
| 3 | PASS if all hard checks (CI > 0, **DSR ≥ 0.95**, PBO ok) and all engineering checks pass | `:576-578`, `:602-605` | **yes** |
| 4 | INSUFFICIENT_DATA (CI includes 0 but **DSR** and PBO pass, sessions below the minimum track record) | `:606-612` | **yes** (needs `hard[1]`) |
| 5 | REVISE, with the first failed engineering check as the target | `:613-622` | no |

- The reason string prefers DSR. When DSR < 0.95, the reason is "deflated Sharpe below 0.95", even if the
  benchmark also fails (`:596-599`).
- `revise_target` follows `bench_fail`, not the reason (`:600`). This is why S_V3, S_V4, S_E1_trend_krx, S_B3 and
  S_V1 carry a DSR reason next to a benchmark revise target.
- The printed line is "Deflated Sharpe {dsr} after {n_trials} trials" (`:543`).
- Threshold: `GATE["dsr_min"] = 0.95` (`validate.py:56`). The gate constants are pre-registered and must not
  change in this stage.

---

## 2. How the stored cards were produced (`docs/asset_expansion_study.py`)

### 2.1 Card writers

| Writer | Lines | Trials stored | DSR? |
|---|---|---|---|
| `strategy_card` | `:173-215` | `{"N_planned": len(grid), "N_total": n_trials, "ledger": ledger or []}` (`:207`); `n_trials = n_trials or len(grid)` (`:182`) | yes (`:193`) |
| `run_fx` (own card) | `:391-446` | `N_total = len(grid)` (`:431`, `:440`) | yes |
| `model_card` | `:218-227` | placeholder `{"N_planned": 1, "N_total": 1}` (`:222`) | no |
| `error_card` | `:230-237` | `{}` (`:233`); decision INSUFFICIENT_DATA | no |

- Each card stores `created`, `seed`, `results_md5` and a `protocol` subset (`:206`). No card stores a code
  version, a gate version or a run ID (`validate.py:802-825`).
- `--quick` sets `V.GATE["bootstrap_B"] = 300` for the process (`:191-192`). The manifest records
  `"quick": false` (`docs/asset_expansion/manifest.json`).
- **Overwrite on every run.** `write_results` rewrites every card in the run (`:778-780`). It replaces the
  results.csv rows of every re-scored card (`:770-772`). A candidate that raises gets an `error_card`
  (`:835-836`), which overwrites the previous valid card of that ID.
- **No ledger writes.** The study never calls `gate_ledger.register_trial`. This contradicts the ledger
  docstring's "the harness is the only writer, research scripts included" (`gate_ledger.py:4-5`).

### 2.2 Run history visible in the repo

- The current results are from 2026-09-27. The last run re-scored only `M_O1_board_today`; the other cards were
  kept from earlier runs (`docs/asset_expansion/results.md:3`; `manifest.json` `"rescored"`).
- Two earlier stdout logs exist (`docs/asset_expansion/study_run2.log`, `docs/asset_expansion/study.log`), plus an
  earlier results table (`docs/asset_expansion/results_run2.md`). In `results_run2.md:155-185`, C3 BTC-USD is
  REVISE with "Deflated Sharpe 1.00 after 6 trials" and "on a grid edge: fails". C3 KRW-BTC is PASS after 6 trials.
- No log of the "run 4" that produced the current C3 cards is in the repo. UNVERIFIED whether one exists
  elsewhere.
- **The stored cards predate the current gate text.** Stored lines read "(11 years)"
  (`cards/S_C3_crypto_trend_btcusd.json`). `validate.py:540` now prints "(N full years)". `year_stats` now counts
  whole years, where the old code counted calendar years touched (`validate.py:427-437`). The stored cards are
  therefore not byte-reproducible by today's gate. Whether any verdict would change on a re-score is UNVERIFIED;
  it was not run. The repo history has a single commit for these files (`eacd57d`, 2026-10-23), so the gate
  version that wrote the cards cannot be recovered from git.

### 2.3 C3's typed trial count

- Card grid: `hysteresis = [0.0, 0.222, 0.444, 0.667, 0.889]` (`:333`), with `domain = (0.0, 0.889)` and
  `n_trials=11` (`:339`).
- Free-text history (`:340-342`): "run 2/3: hysteresis [0.05, 0.1, 0.2, 0.3, 0.4, 0.5] (6 trials, three of them
  duplicates…) → REVISE on a grid edge for BTC-USD"; "run 4: the complete lattice …; N_total = 11".
- **The BTC-USD revision history was applied to the KRW-BTC card too.** Both cards carry N = 11, although KRW-BTC
  was already PASS in run 2/3 (`results_run2.md:171-185`).
- **Distinct rules.** The composite is the mean of nine ±1 votes (`strategies.py:344-345`). With no zero vote it
  takes odd ninths. The rule is long when the composite is above +h (`:346`). Under that reading:
  - The old grid pairs up as {0.05, 0.1}, {0.2, 0.3} and {0.4, 0.5}. That is 3 distinct rules, matching "three of
    them duplicates".
  - The new lattice holds 5 distinct rules (thresholds 1/9, 3/9, 5/9, 7/9 and 9/9), and it contains the old 3.
  - So the 11 counted trials are at most 5 distinct rules. A zero vote happens only on an exact price tie.
  - The study comment says 0.05, 0.1 **and 0.2** are one rule (`docs/asset_expansion_study.py:328-330`). That
    disagrees with this reading for 0.2. Not executed: UNVERIFIED by computation.

---

## 3. Strategy Lab today (`ui/strategy_lab_page.py`)

### 3.1 Run flow (`run_family`, `:85-136`)

1. **Cost floor.** `cost_bps=None` charges the table rate. A typed cost below the table rate runs as a
   sensitivity with the verdict withheld (`:92-103`).
2. **Data.** `load_history` per symbol (`:104`). The Lab uses its own cache, `config.ficc_cache_dir()`
   (`core/quant/history.py:428`), not `docs/asset_expansion/cache`.
3. **P&L matrix.** Built for the whole family grid with a constant cash rate of `0.03/252` (`:113-114`).
4. **Walk-forward** (`:116`).
5. **Register trials** (`:117-118`), before scoring. A broken ledger raises, and the worker shows the error with
   no verdict (`:238-240`).
6. **Benchmark.** Equal weight of the panel; none for pairs (`:119-123`).
7. **Bootstrap override.** `V.GATE["bootstrap_B"]` is set to the run's `bootstrap_B` (default 1000 at `:86`; the
   GATE default is 2000 at `validate.py:54`). It is restored in `finally` (`:124-129`).
8. **Score** with **`n_trials=len(grid)`** (`:127`).
9. **Return** a dict holding `ledger_n` (`:132-136`). Nothing is written to disk except the ledger rows.

### 3.2 Display

- The scorecard section reads the stored cards (`load_cards`, `:315-317`; `_study_card`, `:296-312`). It shows
  SR, DSR and PBO per card (`:185-196`). It does not show `trials.N_total`. The detail view shows the card lines,
  which include "after N trials" (`:166-178`).
- The run section shows the decision, or NO VERDICT for a sensitivity run (`:249-251`).
- The chip "{family} ledger: {ledger_n} configurations" has the tooltip "Every configuration ever run in this
  family. The deflated Sharpe above counts only this run's grid." (`:254-256`).
- The run section also shows the stat tiles (`:261-272`), the equity chart, the gate lines and the AI analysis
  panel (`:273-276`). The narrative states "{G} configurations = {n_trials} trials" (`:142`).
- **No persistence of results.** A grep of `ui/ai_panel.py` and `core/quant/insights.py` for `write_text`, `open(`,
  `to_csv`, `jsonl` and `sqlite` found no writes.

### 3.3 What a ledger row holds (`register_trials`, `:55-82`)

- **Ledger file:** `<macro_dir>/ledgers/<FAMILY_ID>.jsonl` (`:67`). `config.macro_dir()` is
  `$QUANTGEN_MACRO_DIR` or `~/.nextgen/macro` (`config.py:176-178`). The directory does not exist in this
  container, so the owner's ledger contents are unknown (UNVERIFIED).
- **Fields written:**
  - `rule` = family ID (E1, E2, E3, E5, E8, C3 or B3; `:50-51`).
  - `params` = θ + `symbols` + `cost_bps`. Symbols are upper-cased and sorted, except for pairs (`:68-70`).
  - `timing_class="COMPLIANT"`, `span=[first date, last date]` and `market` (KR, US, CRYPTO, FX, FUTURES or
    MULTI; `:71-72`).
  - `run_utc`, `phase="research"`, `run_kind="variant"`, `run_utc_anchor=git:<HEAD sha>` or `UNVERSIONED`
    (`gate_ledger.py:122-131`), `source` and `script` (`:73-81`).
  - The ledger adds `config_id`, `family_id`, `row_md5` and `prev_row_md5` (`gate_ledger.py:337-355`).
- **Not written:** the optional fields `cost`, `results_md5`, `delta_sr`, `card_id`, `diff_series_ref` and
  `estimator`/`window`/`cap`/`instrument_book`/`rebalance`/`start_convention` (`gate_ledger.py:64-65`).
- **De-duplication.** `config_id` is the md5 of `ROW_SET_KEY` = rule, params, estimator, window, cap,
  instrument_book, rebalance, timing_class and start_convention (`gate_ledger.py:60-61`, `:168-171`). Span, data
  source, run time, code version and result are not part of it. A repeated `config_id` appends nothing, and the
  first row stands (`:343-346`). The test asserts this only for case and symbol order
  (`tests/paper_live_acceptance.py:333-344`).
- **Synthetic runs register nothing** (`:60-61`). Cost-sensitivity runs do register, because the cost sits in
  `params`, so it changes `config_id`.
- **`N_eff` cannot be computed on Lab rows.** The rows have no `diff_series_ref`, so
  `difference_series` raises `CorrUnavailable` (`gate_ledger.py:357-368`).
- `gate_ledger.py` is frozen (`core/quant/gate_package.py:36-38`). `validate_row` refuses unknown fields
  (`gate_ledger.py:190-192`). A run ID, result or status therefore cannot be added to a ledger row without editing
  a frozen file.

### 3.4 Lab family versus card: the same name is not the same run

| Lab family (`:34-46`) | Lab grid (G) | Card(s) | Card grid | Differences that change results |
|---|---|---|---|---|
| trend_switch → E1 | 12 | S_E1_trend_us, _krx | same 12 (`study:274`) | cash: Lab 3 % constant, study FRED DGS3MO (`study:273,279`); start date (study fixed) vs Lab `days=5000`; bootstrap B 1000 vs 2000 |
| vol_target → E2 | 8 | S_E2_voltarget_spy, _kodex200 | same 8 (`study:285`) | cash; window; B |
| risk_parity → E3 | 8 | S_E3_riskparity_us | same 8 (`study:295`) | cash (study 0); window; B |
| xs_momentum → E5 | 12 | S_E5_xsmom_sectors | same 12 (`study:305`) | cash (study 0); window; B |
| tsmom → B3 | 12 | S_B3_tsmom_futures | same 12 (`study:316`) | cash; window; B |
| crypto_trend → C3 | **6: h = 0.05…0.5** (`:42`) | S_C3_crypto_trend_btcusd, _krwbtc | **5: h = 0…0.889** (`study:333`), `domain`, **N = 11** | different grid; Lab has 3 semantic duplicates; Lab passes no `domain` (`:127`), so plateau edges differ; cash (study 0) |
| pairs → **E8** | 8, long_only False (`:44-45`) | S_E8_pairs_* and **S_S6_pairs_*** | same 8; Samsung pref uses long_only True (`study:734`) | S6 cards file under E8 in the Lab; Lab never runs long_only; Lab has no benchmark for pairs |
| — | — | S_V1, S_V3, S_V4 | not in the Lab | — |

Whether the KRX code forms "069500" and "069500.KS" produce the same `h.symbol` (and so the same `config_id`) is
UNVERIFIED (`core/quant/history.py:475-494`).

---

## 4. Inventory of every stored card

### 4.1 The 16 DSR-bearing strategy cards

- **Margin** = DSR − 0.95.
- **N to flip** is the first integer N at which the DSR predicate changes, holding the backed-out dispersion
  fixed. The main figure assumes normal OOS moments; the range in brackets covers the moment scenarios in §5.
- **k** = the factor by which the hurdle `SR0 = sr_sd·f(N)` must grow to flip the predicate, through N, `sr_sd`
  or both.
- **PSR(N=1)** = the DSR value at N = 1, where `SR0 = 0`.
- **DSR at 2N** = the DSR if the counted trials doubled, for example one more full-grid run of the family under a
  family-wide reading (normal moments).

| Card | Family | G | N used | Card N_total | OOS T | SR_oos | DSR | Margin | Decision (reason) | DSR predicate | N to flip | k | PSR(N=1) | DSR at 2N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S_C3_crypto_trend_btcusd | C3 | 5 | 11 (typed) | 11 | 3,634 | 1.187 | 0.99998 | +0.050 | **PASS** | pass | ~1e28 (1e17–1e72) | 5.3–11.1 | 1.0000 | 0.99997 |
| S_C3_crypto_trend_krwbtc | C3 | 5 | 11 (typed) | 11 | 2,530 | 1.216 | 0.99951 | +0.050 | **PASS** | pass | ~1e10 (1e8–1e16) | 3.4–5.2 | 0.9999–1.0000 | 0.9993 |
| S_E8_pairs_kodex_tiger | E8 | 8 | 8 | 8 | 3,504 | 0.552 | 0.9691 | +0.019 | **REVISE** (execution) | pass | **769 (320–3,505)** | 2.0–2.5 | 0.978–0.982 | 0.9659 |
| S_E2_voltarget_kodex200 | E2 | 8 | 8 | 8 | 3,496 | 0.531 | 0.9627 | +0.013 | REJECT (benchmark p 0.81) | pass | **89 (60–167)** | 1.6–1.9 | 0.974–0.978 | 0.9588 |
| S_E5_xsmom_sectors | E5 | 12 | 12 | 12 | 6,197 | 0.476 | 0.9695 | +0.020 | REJECT (benchmark p 0.97) | pass | **81 (70–97)** | 1.44–1.51 | 0.990–0.992 | 0.9627 |
| S_E1_trend_us | E1 | 12 | 12 | 12 | 4,711 | 0.840 | 0.99954 | +0.050 | REJECT (benchmark p 0.75) | pass | ~1e25 (1e17–1e48) | 5.1–8.8 | 0.9998–0.9999 | 0.9994 |
| S_E2_voltarget_spy | E2 | 8 | 8 | 8 | 7,208 | 0.634 | 0.99917 | +0.049 | REJECT (benchmark p 0.18) | pass | ~1e25 (1e17–1e45) | 5.9–9.7 | 0.9995–0.9997 | 0.9990 |
| S_E3_riskparity_us | E3 | 8 | 8 | 8 | 4,669 | 0.892 | 0.99981 | +0.050 | REJECT (benchmark p 0.25) | pass | ~1e28 (1e17–1e68) | 5.9–12.0 | 0.9999–1.0000 | 0.9998 |
| S_S6_pairs_samsung_pref | S6 (Lab: E8) | 8 | 8 | 8 | 4,422 | 0.831 | 0.99970 | +0.050 | REJECT (benchmark p 0.61) | pass | >1e100 | 14.7–136 | 0.9997–0.9998 | 0.9997 |
| S_S6_pairs_hyundai_kia | S6 (Lab: E8) | 8 | 8 | 8 | 4,615 | 0.426 | 0.8606 | −0.089 | REJECT (DSR) | fail | **passes only at N = 1** (DSR at N=2 ≈ 0.94) | — | 0.964–0.968 | 0.8185 |
| S_E1_trend_krx | E1 | 12 | 12 | 12 | 1,884 | 0.524 | 0.8416 | −0.108 | REJECT (DSR) | fail | fails even at N = 1 | — | 0.920–0.927 | 0.8212 |
| S_B3_tsmom_futures | B3 | 12 | 12 | 12 | 5,634 | 0.082 | 0.2705 | −0.680 | REJECT (DSR) | fail | fails even at N = 1 | — | 0.651 | 0.2117 |
| S_E8_pairs_gld_iau | E8 | 8 | 8 | 8 | 4,602 | −2.281 | 5.8e−165 | −0.950 | REJECT (DSR) | fail | fails at every N (SR < 0) | — | 0.0000 | 0.0000 |
| S_V1_vix_rolldown | — (not in Lab) | 8 | 8 | 8 | 3,197 | −0.143 | 0.2786 | −0.671 | REJECT (DSR) | fail | fails at every N (SR < 0) | — | 0.305–0.306 | 0.2725 |
| S_V3_fx_momentum | — (not in Lab) | 2 | 2 | 2 | 1,367 | −0.592 | 0.0623 | −0.888 | REJECT (DSR) | fail | fails at every N (SR < 0) | — | 0.081–0.089 | 0.0446 |
| S_V4_dollar_carry | — (not in Lab) | 1 | 1 | 1 | 1,429 | 0.273 | 0.7418 | −0.208 | REJECT (DSR) | fail | **N-invariant**: one column → `sr_sd = 0` (`validate.py:506`) → SR0 = 0 at every N | — | 0.740–0.744 | 0.7418 |

All stored values come from `docs/asset_expansion/cards/<card>.json` (`stats.sr_oos`, `stats.n_sessions`,
`stats.n_trials`, `stats.n_configs`, `stats.dsr`, `trials.N_total`, `decision`, `decision_reason`). Counts: 2 PASS,
1 REVISE, 13 REJECT. Of the 13 REJECTs, 7 are on DSR and 6 on the benchmark test.

### 4.2 The 18 cards with no DSR predicate

None of these predicates reads `n_trials` or `trials.N_total`. The stored `{"N_planned": 1, "N_total": 1}` is a
placeholder (`docs/asset_expansion_study.py:222`).

| Card | Kind | Decision | What decides it | Implicit search a run registry would see |
|---|---|---|---|---|
| S_B2_pca_fly | strategy (via `model_card`) | REVISE | ADF p, half-life, hit rate, P&L per trade vs cost, trades (`study:483-485`) | one fixed configuration (`study:482`) |
| D_C2_garch_btc / D_C2_gjr_btc / D_C2_skewt_btc | distribution | REVISE / REVISE / REVISE | Kupiec, Christoffersen, coverage, PIT, non-convergence (`validate.py:741-796`); stationarity override (`study:515-517`) | 3 model variants per asset (`study:742-750`) |
| D_Q_garch_spy / D_Q_gjr_spy / D_Q_skewt_spy | distribution | REJECT / REVISE / REVISE | same | 3 variants |
| D_Q_garch_kodex200 / D_Q_gjr_kodex200 / D_Q_skewt_kodex200 | distribution | REJECT / REJECT / REVISE | same | 3 variants |
| M_B1_dns | model | REJECT | maturities beaten and DM t (`study:456-458`) | one specification |
| M_C1_kimchi | model | REVISE | ADF, half-life, predictive t (`study:539-540`) | one |
| M_C4_funding | model | PASS | decile sign and bootstrap p (`study:560-561`) | one |
| M_C7_weekday | model | PASS | Bonferroni over weekdays (`study:591`) | multiplicity handled inside |
| M_C8_ethbtc | model | REJECT | ADF p (`study:578`) | one |
| M_E4_letf_drag | model | REVISE | MAE, slope, R² (`study:627`) | one |
| M_O1_board_today | model | REVISE | today's board checks (`study:672`); re-scored 2026-09-27, the earlier snapshot overwritten | daily snapshot; each run replaces the last |
| M_O2_basis_today | model | PASS | theo gap within the dividend band (`study:710`) | daily snapshot |

---

## 5. How the margins were computed, and their limits

- **Missing inputs.** No card stores the OOS skewness g3, the kurtosis g4, `sr_sd_daily` or the per-configuration
  Sharpe vector. They are computed inside `score_strategy` and discarded (`validate.py:505-507`, `:231-232`).
- **Back-out.** Write `s = √(denom/(T−1))` and `z_obs = Φ⁻¹(DSR)`. The DSR formula (§1.1) then gives:
  - `SR0_obs = SR − z_obs·s` (the hurdle the stored DSR implies);
  - `sr_sd = SR0_obs / f(N)`;
  - the predicate holds iff `SR0 ≤ SR0_crit = SR − 1.6449·s`;
  - `k = SR0_crit / SR0_obs`;
  - N to flip solves `f(N) = SR0_crit / sr_sd`.
  `f` is the gate's own `expected_max_sharpe(N, 1)`. It was imported and checked equal to the closed form at each
  stored N.
- **Moment scenarios (g3, g4):** (0, 3) normal; (0, 10); (−1, 10); (+1, 10); (0, 30). A scenario that implies
  `sr_sd < 0` contradicts the stored DSR and is dropped. This happened once: S_S6_pairs_samsung_pref under
  (−1, 10).
- **Sensitivity is small for most cards.** Daily SR² is small, so `denom` stays near 1. The skew term g3·SR
  dominates the spread. The flip-N ranges in §4.1 are wide only where the hurdle growth k is large.
- **One identity check.** At N = 1, SR0 = 0, so the stored DSR identifies `denom` exactly. For S_V4,
  `denom = 1.00454`; the normal value would be 1.00015.
- **One non-normal outlier.** S_E8_pairs_gld_iau implies an annualised `sr_sd` of 2.6–3.2 under every scenario.
  This suggests strong non-normality or a large grid spread. Its verdict cannot depend on it, because SR < 0 fails
  at every N.
- **Dispersion held fixed.** The flip N assumes `sr_sd` does not change. A ledger basis that also widens `sr_sd`
  (for example, family-wide over several universes) flips earlier. The k column gives the combined factor needed.
- **Status.** These are estimates conditional on assumed moments, not recomputations. The script that produced
  them is outside the repo (scratchpad). It reads only the card JSON files and imports
  `core.quant.validate`.

---

## 6. Cases where reflecting trial history would change a verdict

This is sensitivity only. The criteria and the GATE constants are unchanged.

| Card | Today | Trigger | Decision then | Why |
|---|---|---|---|---|
| S_E8_pairs_kodex_tiger | REVISE (execution) | N ≥ ~769 (320–3,505) at fixed `sr_sd`; or hurdle × 2.0–2.5 | **REJECT** (DSR) | DSR margin 0.019; REJECT outranks REVISE (`validate.py:593` before `:613`) |
| S_E2_voltarget_kodex200 | REJECT (benchmark) | N ≥ ~89 (60–167); or hurdle × 1.6–1.9 | REJECT (**reason → DSR**, revise target unchanged) | DSR margin 0.013; reason order (`:596-599`) |
| S_E5_xsmom_sectors | REJECT (benchmark) | N ≥ ~81 (70–97); or hurdle × 1.44–1.51 | REJECT (**reason → DSR**) | DSR margin 0.020 |
| S_S6_pairs_hyundai_kia | REJECT (DSR) | a valid-experiment count **N = 1** (for example `N_eff < 2`, which `int()` truncates to 1) | **REVISE** (target "regime") | PSR(N=1) 0.964–0.968 ≥ 0.95. Then no REJECT disjunct holds: PBO 0.2006 > 0.20 but `prob_loss` 0.073 ≤ 0.10, so not a PBO reject; stress SR 0.31 > 0; no benchmark. PASS fails on years+ 58 %, plateau 0 % and trades 66 (`:579-583`). Whether this card's 8 configurations are correlated enough for `N_eff < 2` is UNVERIFIED: no difference series is stored |
| S_C3 ×2 (PASS) | PASS | N ~1e8 (KRW-BTC) to ~1e17 (BTC-USD) or more; or hurdle × 3.4–11 | unchanged at any realistic N | DSR at N = 17 (11 + one Lab C3 grid) is 0.99937 (KRW) and 0.99997 (BTC) |
| S_E1_trend_krx | REJECT (DSR) | none | unchanged | fails even at N = 1 |
| S_V4_dollar_carry | REJECT (DSR) | none under the current code | unchanged | `sr_sd = 0` makes DSR independent of N |
| all other DSR cards | — | — | unchanged | margins of order 1e17+ trials, or SR < 0 |

- **Two directions.** A ledger basis can tighten the DSR predicate (higher raw N, or a wider `sr_sd`). It can also
  loosen it (a correlation-adjusted N below G).
- **The C3 count shows the gap between counting choices.** A literal `config_id` count gives 11. A count of
  distinct decision rules gives 5. DSR barely moves between the two (BTC-USD 0.999986 at N = 5 vs 0.999978 at
  N = 11).

---

## 7. Per-run record today versus the R3 field list

| R3 field | Lab ledger row today | Stored card today | Gap |
|---|---|---|---|
| Unique run ID | none. `config_id` identifies a configuration, not a run, and one run writes G rows with no shared key | none (`card_id` is reused across runs) | **absent** |
| Strategy version | `run_utc_anchor` = repo HEAD sha of the **first** run only; it misses uncommitted changes; `UNVERSIONED` without `.git` | none (`created` date only) | **absent / partial** |
| Data period | `span` of the **first** run only (not in `config_id`) | `data.start/end/sessions` of the last run | stale on reruns |
| Parameters | θ + symbols in `params` | `rules.grid`, `chosen_last` | present |
| Cost conditions | `cost_bps` inside `params`; no flag for table rate vs sensitivity; no stress multiplier | `costs.cost_bps`, `stress_multiplier` | partial |
| Results | none (`results_md5`, `delta_sr` unused) | `stats`, `tests` of the last run | Lab absent |
| Verdict | none | `decision`, `decision_reason`, `revise_target` | Lab absent |
| Run status | none; rows are written before scoring (`:117-118`) | `kind="error"` card on failure, overwriting the prior card | **absent** |
| Total run count | not countable | not countable (logs are ad hoc stdout captures) | **absent** |
| Valid-experiment count | `n_raw` (distinct `config_id` per family, all universes and costs, semantic duplicates included), shown but not used | `trials.N_total` (= G, or typed 11 for C3) | two unreconciled bookkeepings |

---

## 8. How today's code treats the R3 trial categories

| Case | Strategy Lab | Study / cards | Enters the gate's N today? |
|---|---|---|---|
| Simple rerun (same config, data, code) | no row (de-dup); no trace of the run | card overwritten; N unchanged | no |
| Rerun on extended or different data | no row; span stays the first run's | card overwritten; N unchanged | no |
| Rerun after a code change | no row unless params change | card overwritten; no code hash | no |
| Failed run, before walk-forward (data, symbol count, too few sessions) | nothing recorded (`:104-116` precede `:118`) | `error_card` overwrites the prior card | no |
| Failed run, after registration (scoring error) | G rows stand, with no status | — | Lab `n_raw` yes; N no |
| Parameter search within a run | one row per grid point | N = G (`study:182`) | yes, N = G |
| Grid revision after seeing results | new `config_id` rows (family-wide) | typed N only (C3 `study:339`) and free text | Lab no; study C3 only |
| Semantic duplicates (different literals, same rule) | separate `config_id` rows (literal md5, `gate_ledger.py:168-171`) | counted (C3: 11 for ≤ 5 rules) | yes |
| Cost sensitivity (cost below table) | registered (cost in params); verdict withheld | not run | Lab `n_raw` yes; N no |
| Same rule, new universe (a candidate "independent validation") | new rows in the same family file, with a `market` label | a separate card with its own N; C3 KRW-BTC inherits BTC-USD's revision | no cross-card N |
| Pre-registered hold-out check of a fixed configuration | no such concept | no such concept | — |
| Synthetic data | not registered (`:60-61`) | — | no |
| Null-distribution runs (placebo, shift panel) | — | — | refused as rows (`gate_ledger.py:57`, `:200-201`) |

The ledger keeps revision counting apart from trial counting by design: `bump_revision` "never N"
(`gate_ledger.py:819-826`), and a static guard forbids assigning a revision count to N (`:864`). The ledger
also defines `run_kind` values `trial`, `quick_check`, `revision`, `timing_lag` and `variant` (`:58`). The Lab
uses only `variant`.

---

## 9. Constraints this map found for the registry design

1. **Frozen files.** `core/quant/validate.py`, `gate_ledger.py` and `strategies.py` are frozen
   (`gate_package.py:36-38`). `ui/strategy_lab_page.py` and `docs/asset_expansion_study.py` are not on that list.
2. **A parallel computation is possible without frozen edits.** The public calls cover it:
   - `V.deflated_sharpe(wf.pnl, n_trials=N_valid, sr_sd_daily=…)`;
   - `V.expected_max_sharpe`;
   - `V.score_strategy(…, n_trials=…)`;
   - the ledger readers (`family_ledger`, `rows`, `n_raw`, `n_eff`).

   The existing verdict stays the one `score_strategy` returns with N = G (or 11 for C3).
3. **The run record cannot live in ledger rows.** `validate_row` refuses unknown fields (`gate_ledger.py:190-192`),
   and de-duplication drops reruns (`:343-346`). A run registry needs its own store. It can reference ledger
   `config_id`s.
4. **Dispersion has no ledger source today.** Lab rows carry no per-trial Sharpe (`delta_sr` unused) and no
   `diff_series_ref`. A ledger-wide `sr_sd` or `N_eff` therefore cannot be computed from existing rows.
5. **Integer truncation of N.** `validate.expected_max_sharpe` truncates N (`:213`), while
   `gate_ledger.emax_iid` accepts a real N (`:519-527`). Passing a fractional `N_eff` to the study gate floors it.
6. **Re-running the study overwrites the published cards and results.** It rewrites `cards/*.json`,
   `results.csv`, `results.md` and `manifest.json` (`study:770-817`). A parallel run must write elsewhere.
7. **Excluded cache files.** An exact parallel re-score of these cards would read files that must not be opened:

   | Cache file | Read by | Cards |
   |---|---|---|
   | `yf_SPY.csv` | `yf("SPY")` | S_E1_trend_us, S_E2_voltarget_spy, S_E3_riskparity_us, S_V1_vix_rolldown, D_Q_*_spy |
   | `yf_BTC-USD.csv` | | S_C3_crypto_trend_btcusd, D_C2_*_btc |
   | `upbit_KRW-BTC.csv` | | S_C3_crypto_trend_krwbtc, M_C1_kimchi |
   | `binance_BTCUSDT.csv` | | M_C1_kimchi, M_C4_funding, M_C8_ethbtc |

   Sources: `study:69-79`, `:91`, `:112`, `:120`, `:724-752`. For these cards, the analytic route in §5 is the only
   one allowed here. That covers 6 of the 16 DSR cards, including both PASS cards.
8. **The owner's ledger is not here.** It lives under `~/.nextgen/macro/ledgers` on the owner's machine. Actual
   Lab trial counts per family are unknown to this map.

---

## 10. Open questions for the owner or the next steps

1. What is one "valid experiment"? Candidates: a literal `config_id`; a distinct decision rule (C3: 5 vs 11); a
   cluster of correlated configurations (`N_eff`). Is the reading market-scoped or family-wide
   (`gate_ledger.py:62`, `:700-733`)?
2. May a ledger basis lower N below G? This decides whether S_S6_pairs_hyundai_kia can move REJECT → REVISE.
3. Where does `sr_sd` come from on the ledger basis: the current grid (today) or all counted trials? The second
   needs per-trial Sharpes stored in the run record.
4. Should one asset's revision count on another asset's card (C3 KRW-BTC carrying BTC-USD's run 2/3)?
5. Should a cost-sensitivity run, which has no verdict, count as an experiment?
6. Is the Lab's crypto_trend grid (`strategy_lab_page.py:42`) meant to differ from the card grid
   (`study:333`)? Should Lab pairs runs on KRX stocks file under E8 rather than S6?
7. The stored cards were written by an earlier gate text (§2.2). Should the parallel comparison use the stored
   numbers (analytic), or a re-score of the non-excluded cards into a separate folder?

---

## References

Repository (all read on 2026-10-27, working tree at `eacd57d`):
- `core/quant/validate.py`: DSR `:211-237`; `score_strategy` `:492-533`; `_decide_strategy` `:536-622`; GATE
  `:53-74`; ModelCard `:802-834`.
- `ui/strategy_lab_page.py`: FAMILIES `:34-46`; FAMILY_ID `:50-51`; `register_trials` `:55-82`; `run_family`
  `:85-136`; display `:158-293`; card loading `:296-317`.
- `docs/asset_expansion_study.py`: card writers `:173-237`; candidates `:271-758`; `write_results` `:764-817`;
  `main` `:820-841`.
- `core/quant/gate_ledger.py`: row schema `:56-65`; `config_id` `:168-171`; append and de-dup `:337-355`;
  `n_raw` `:332-334`; `N_eff` `:574-582`; step 3 `:748-813`; revisions `:819-826`.
- `core/quant/gate_package.py:36-38` (frozen sources); `config.py:176-178` (ledger directory);
  `core/quant/strategies.py:330-348` (crypto_trend); `core/quant/history.py:402-428`, `:464-494`.
- `docs/asset_expansion/cards/*.json` (34 files), `manifest.json`, `results.md`, `results_run2.md`, `study.log`,
  `study_run2.log`.
- `tests/paper_live_acceptance.py:333-344` (`register_trials` test; read, not run).

Literature:
- Bailey, D. H., & López de Prado, M. (2014). The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest
  Overfitting, and Non-Normality. *Journal of Portfolio Management* 40(5), 94–107.
  https://doi.org/10.3905/jpm.2014.40.5.094. This is the formula implemented at `validate.py:220-237` and cited at
  `validate.py:26-28`. The paper defines N as the number of *independent* trials; that reading is from memory and
  was not re-checked in this step (UNVERIFIED).
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). The Probability of Backtest Overfitting.
  *Journal of Computational Finance* 20(4), 39–69. https://doi.org/10.21314/JCF.2016.322. Cited at
  `validate.py:29`, `:62-67` (PBO by CSCV).
- López de Prado, M., & Lewis, M. J. (2019). Detection of false investment strategies using unsupervised learning
  methods. *Quantitative Finance* 19(9), 1555–1565. https://doi.org/10.1080/14697688.2019.1622311. Context for
  clustering trials into an effective N (compare `gate_ledger.py:473-483`). UNVERIFIED: cited from memory, not
  re-checked.
