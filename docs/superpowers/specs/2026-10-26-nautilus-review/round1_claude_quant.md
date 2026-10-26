# Round 1 referee report: quantitative methodology

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 1.
Referee: Claude, quantitative-methodology lens (backtest overfitting, DSR/PBO, walk-forward, parity statistics).
Repo: QUANTGEN at `6f7c610`. Engine: `nautilus_trader` 1.231.0 in `scratch:ntvenv`.
`scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probes I ran (all synthetic data; no SPY row on or after 2004-12-01; no real BTC price; no ledger row; QUANTGEN
imported read-only):
- `scratch:referee_quant/cent_probe.py` (venv): 900 alternating buys and sells on a `CurrencyPair` CASH account with
  the spec's 8-decimal sizing, at 10 and 20 bp.
- `scratch:referee_quant/cost_gap_probe.py` (global interpreter): per-column 1x-to-2x Sharpe gaps, and exact
  in-sample ties in `walk_forward`, on synthetic SPY-like (5,488 bars) and BTC-like (4,392 bars) series.
- `scratch:referee_quant/tie_probe_fast.py` (global interpreter): how far the out-of-sample statistics move when
  exact in-sample ties are broken differently.
- A one-line inversion of the stored BTC card's DSR (command in the Notes).

## Verdict

**ACCEPT_WITH_CHANGES.**

The parity arithmetic is sound. The return identity of 5.3.3 matches `simulate` (`core/quant/strategies.py:82-90`).
The corrected P2 and P3 bars are well argued. P12's selection-matched series is the right construction. Registration
comes before any computation on the pilot windows. Nothing in the bridge changes the gate, so the gate's own
overfitting controls (DSR, PBO or losing-split share, plateau, OOS/IS) still apply.

I would not hand this to an engineering team today. Six things would let a bridge or runner error appear as a strategy
result, or weaken a guard the spec says is conservative:
- Parity cannot see errors in the inputs the runner feeds to both engines (QUANT-1).
- The gate decision is compared across engines only after an exempt selection flip (QUANT-2).
- The card's out-of-sample series is selected by engine noise wherever QUANTGEN has an exact tie. Exact ties are
  common (QUANT-3).
- `max(len_grid, N_raw)` under-counts trials. O11 claims the opposite (QUANT-4).
- No hard check verifies the commission rate directly (QUANT-5).
- The card carries no claim label, so an engine replication reads like new evidence (QUANT-6).

None is a blocker. Each has a cheap fix that changes no gate code.

## Sections reviewed

- Section 1 (purpose), section 2 (O5, O7, O11), 3.5 (determinism).
- 5.2.3 to 5.2.5 (fees, sizing, the ports' decision rules) against `core/quant/strategies.py:111-116, 146-187,
  330-348, 379-398`.
- 5.3.2 (order of operations), 5.3.3 (return reconstruction), 5.3.4 (matrices).
- 5.4.1 to 5.4.3 (P1 to P13, the near-tie rule, the evidence for the bars) against `core/quant/validate.py:137-143,
  345-381` and the maps (map03 §2.9, §3.3-3.5, §4.2-4.5; synth §7.3-7.5; K3).
- 5.5 (gate hand-off), 6.3 to 6.5 (run record, ledger rows, card) against `core/quant/validate.py:492-623, 802-834`,
  `core/quant/gate_ledger.py:168-214, 332-386` and `ui/strategy_lab_page.py:55-82, 127`.
- Section 7 (G-01 to G-05, Z-01), 8.2 and 8.3 (fixtures; layer-1 tests 2, 10, 13, 14), section 9 (Steps 7 to 9).
- 10.1 to 10.4 (registration tables, expected verdicts, data-access history) against
  `docs/asset_expansion_study.py:68-79, 138-153, 173-215, 271-279, 325-343, 723-731`, the stored cards
  `docs/asset_expansion/cards/S_E1_trend_us.json` and `S_C3_crypto_trend_btcusd.json`, and
  `docs/asset_expansion/results.md:9-16`.
- Appendix A, rows K3, K8, K9, K11, K12 and K15.

## Issues

### QUANT-1. Parity cannot detect errors in the inputs the runner feeds to both engines

- **Severity:** major.
- **Section:** 5.3.2 steps 4, 5 and 11; 5.4.1; 10.3.
- **Problem.**
  - P1 to P13 compare two engines that read the same runner-built arrays: prices, dates, `rf`, cost, embargo,
    benchmark and grid.
  - An error in those arrays changes both sides equally, so it passes every parity check. Examples: a wrong start
    filter, a wrong `dropna` order, a misaligned `rf` index, or a wrong embargo.
  - The gate then scores the wrong sample, and the card reports the result as a finding about the rule.
  - The spec never anchors the QUANTGEN reference to an independent result, although one exists for pilot 2.
- **Evidence.**
  - Both engines are fed from the same arrays: 5.3.2 steps 4, 5 and 11 build them, and 6.1 passes the same
    rounded closes to the child.
  - The stored card `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json` was computed by the study's own code
    on the same file and the same five configurations. Its values: `sr_oos` 1.18693264, `n_trades` 144,
    `n_sessions` 3634, `bench_p` 0.07, `chosen_last` `{"hysteresis": 0.0}`.
  - Section 10.3 assumes this reproduction ("If parity holds, the Nautilus matrix is close to QUANTGEN's, so the
    expected verdict is PASS") but never checks it.
  - The study's loaders have silent fallbacks the runner re-implements rather than reuses: the `rf` fallback and the
    leading-NaN fill (`docs/asset_expansion_study.py:148-153`), and the positive-value filter
    (`docs/asset_expansion_study.py:79`).
- **Proposed fix.**
  - **Pilot 2.** After registration and before any child, compute `sc_ref = score_strategy(wf_qg, ...)` with
    `n_trials=11`. Require equality with the stored card, at a tolerance of 1e-6 for floats and exact equality
    otherwise, on: `decision`, `chosen_last`, `n_trades`, `n_sessions`, `sr_oos`, `ci90`, `bench_p`, `pbo` and
    `prob_loss_oos`. A mismatch gives WITHHELD with the reason "reference does not reproduce
    S_C3_crypto_trend_btcusd". No new ledger row results, because the five `config_id`s are the bridge's own rows.
  - **Pilot 1.** No single-SPY card exists. Before registration, assert array equality between the runner's
    arrays and the study's own helpers, `_cached`, `panel`, `rf_daily` and the line-189 benchmark map
    (`docs/asset_expansion_study.py:68-79, 138-153, 186-190`). The arrays are panel dates, raw closes, `rf` and
    the benchmark. No signal or statistic is computed, so this stays inside 3.9.
  - Call those helpers only after the md5 check has confirmed that the files exist. Then `_cached` and `fred` never
    reach their download branches (`docs/asset_expansion_study.py:70-76, 98-102`). An `rf_daily` fallback makes the
    arrays unequal, so the run refuses.
  - Add both checks as R-13 (refusal before registration) and G-07 (WITHHELD after registration).
  - Add a layer-1 test that uses a synthetic cache directory.

### QUANT-2. The gate decision is compared across engines only after an exempt flip

- **Severity:** major.
- **Section:** 5.4.2 ("An exempt flip"), 5.5, 10.3 (pilot 2).
- **Problem.**
  - `score_strategy` runs on `wf_qg` only when P11 has an exempt mismatch. Otherwise the card is written from
    `wf_nt` alone.
  - P12 bounds the OOS series difference at corr >= 0.9999 and abs ΔSR <= 0.01. The gate, however, has hard
    thresholds that a ΔSR of 0.01 can cross when a statistic sits near its bar. These are `ci90[0] > 0`,
    `dsr >= 0.95`, `bench_p <= 0.10`, `oos_is >= 0.5`, the 0.60 positive-years share, and the plateau's half-Sharpe
    test (`core/quant/validate.py:578-583, 592-602`).
  - When that happens, the engines disagree on the verdict. The card states one decision as the gate's.
  - Section 10.3 anticipates exactly this case ("Engine noise could move it across"). It then says a non-PASS with
    parity passing "would be a finding to investigate". That treats an engine-tolerance artefact as a result.
- **Evidence.**
  - Exempt-flip-only dual scoring: spec 5.4.2, lines 581-584.
  - The decision tree's thresholds: `core/quant/validate.py:576-602`.
  - Computing `sc_qg` is cheap. `wf_qg` already exists for P11 and P12 (spec 5.4.2, line 572), and the bootstrap
    seed is shared, so the comparison is paired (`core/quant/validate.py:171, 196`).
- **Proposed fix.**
  - Always compute `sc_qg` and the card's score, both with `seed=11` and the same `n_trials`, `bench` and `domain`.
  - Store both in the run record's `gate` object.
  - If `sc_qg.decision` differs from the card's decision, give WITHHELD with the reason "decision not robust to
    engine tolerance", and write no card.
  - Print the per-statistic differences in the run record. Cover `sr_oos`, `ci90`, `dsr`, `pbo`, `prob_loss_oos`,
    `bench_p`, `n_trades`, `years_positive`, `plateau` and `sr_stress`.
  - This replaces the exempt-flip special case with one rule.
  - Add fixture N8: hand matrices whose `bench_p` sits within 1/2000 of the 0.10 bar, with a 1e-4 Nautilus
    perturbation. Expect WITHHELD.

### QUANT-3. At exact QUANTGEN ties, engine noise picks the card's out-of-sample columns

- **Severity:** major.
- **Section:** 5.4.2, 5.5 step 1, 6.5 `rules.selection`, Step 7 done-when.
- **Problem.**
  - Columns of a trend switch are often identical over a whole 756-session IS window, for example all fully long.
    QUANTGEN's `np.nanargmax` then takes the lowest index (`core/quant/validate.py:373`).
  - On the Nautilus side the same columns differ by about 1e-6 (whole shares on different equity paths, K3). Which
    column wins is then decided by the sign of that noise.
  - The tied columns diverge out of sample. So the card, written from `wf_nt` (5.5 step 1), has an OOS series
    partly chosen at random.
  - No hard check sees it. P12 is selection-matched by construction, and dual scoring (5.4.2) compares only the
    decision.
  - The spec frames near-ties as rare (two origins in 14 before 2004). They are routine.
- **Evidence.**
  - `scratch:referee_quant/cost_gap_probe.py`, synthetic SPY-like series with the pilot-1 grid, `GATE` windows,
    embargo 21 and 38 origins. Exact IS ties occurred at 5, 12 and 2 of the 38 origins (seeds 1, 2, 3). Gaps below
    0.005 occurred at 7, 15 and 2 origins.
  - `scratch:referee_quant/tie_probe_fast.py` broke the exact ties at random, 40 draws per seed. Results:
    - seed 2: `sr_oos` ranged 0.141 to 0.188, against 0.188 under argmax-first; `n_trades` ranged 40 to 41;
      `bench_p` ranged 0.990 to 0.996;
    - seed 1: `sr_oos` ranged 0.099 to 0.113.
  - A 0.047 Sharpe swing is about 5x the P12 bar of 0.01, with every hard check passing.
  - K3 measured the same effect on real pre-2004 matrices: columns 4, 5 and 9 tie exactly at origins 1512 and 1638.
    The Nautilus column 9 differs by about 1e-6 (synth §10.2 K3).
  - Step 7's done-when requires "picks the same column at all 14 origins" (spec line 1158). Under K3 that depends on
    the sign of the 1e-6 noise, so the done-when can fail on a correct bridge.
- **Proposed fix.**
  - Write the card from the selection-matched Nautilus walk-forward. Take `dataclasses.replace(wf_nt, chosen=
    wf_qg.chosen, dates=wf_qg.dates, pnl=<pnl_nt rows of P12>, pnl_stress=<pnl_stress_nt rows of P12>,
    turnover=<turnover_nt rows of P12>)`.
  - `WalkForward` is a public dataclass (`core/quant/validate.py:332-342`), so no gate code changes.
  - The card then uses the gate's own deterministic tie-break and Nautilus P&L. Its statistics differ from QUANTGEN's
    by no more than P12 allows.
  - Keep P11 as a hard detector. A non-exempt mismatch still fails.
  - Set `rules.selection` to `"QUANTGEN argmax on QUANTGEN IS Sharpe; Nautilus P&L"`, and list the exempt origins.
  - Change the Step 7 done-when to "no non-exempt P11 mismatch". Report exempt origins separately.
  - Re-derive the exemption gap of 0.005 on the Windows standard-precision run at Step 7A. Today it is about 7x the
    largest measured IS-Sharpe noise (0.00069, map03 §4.4), measured in high precision only.

### QUANT-4. `max(len_grid, N_raw)` under-counts trials, and O11's safety claim is false

- **Severity:** major. The practical effect on these two pilots is nil; see the evidence.
- **Section:** O11, 5.5 step 3, 10.1 and 10.2 ("Trial count"), risk 16.
- **Problem.**
  - The rule takes the larger of two counts. The two counts measure disjoint sets:
    - the study's trials, typed by hand into the stored cards and never registered (spec 10.4: "none from the
      study (`n_trials` typed by hand)");
    - the ledger rows.
  - For two disjoint sets, the maximum is a lower bound on the union, not the union. So the rule under-deflates
    whenever both sets are non-empty.
  - O11 says the rule "never produces a false PASS". That holds only for its comparison with the market-scoped
    count, not for the true trial count.
- **Evidence.**
  - Pilot 2: the stored card's 11 are 6 hysteresis values from runs 2 and 3, plus the 5 lattice values
    (`docs/asset_expansion_study.py:339-343`; the card's `trials.ledger`).
  - C3 also receives rows written by paper_live, so its `N_raw` includes trials the 11 do not (`paper_live/engine.py:64-69`).
  - The C3 family also holds `S_C3_crypto_trend_krwbtc`, the same grid on near-identical data
    (`docs/asset_expansion_study.py:732`), which is not in the ledger either.
  - Pilot 1: the E1 cards `S_E1_trend_us` and `S_E1_trend_krx` (24 configurations) were never registered either.
  - The ledger counts each row once and deduplicates by `config_id` (`core/quant/gate_ledger.py:333-334, 343-346`).
    So a union can be computed exactly.
  - No effect here. Inverting the stored BTC DSR (0.9999775, z = 4.08 at N = 11) keeps it at or above 0.9997 for
    N up to 1,000, for any denominator from 0.9 to 1.1. It would need E[max] of 7.5 or more standard deviations to
    fall below 0.95. Pilot 1 is expected to be a non-PASS on other grounds. The defect is in the stated rule, which
    later bridge runs will reuse.
- **Proposed fix.**
  - Define `n_trials = |config_ids(ledger after registration) ∪ config_ids(prior unregistered trials)|`.
  - List the prior set in the registration table, owner-confirmed, as explicit rows: the `params` of each typed-in
    trial. Compute each `config_id` with `gate_ledger.config_id` and the Lab's `params` expression (6.4).
  - Print all four counts: `len_grid`, family `N_raw`, market `N_raw` and the union.
  - Better: add an owner ruling O14 to back-register the study's typed-in trials, with `source` naming the study.
    Every later card then counts them.
  - Reword O11: "max() is a lower bound on the trial count; it can under-deflate."

### QUANT-5. No hard check verifies the commission rate

- **Severity:** major.
- **Section:** 5.2.3 (`BpFeeModel`), 5.3.3 cross-checks, 5.4.1 P7 and P10, 8.2 N7.
- **Problem.**
  - P7 is the direct check of the cost class, and it is a warning only. Its `c` is undefined: the table rate, or
    the leg's rate `c × s`. With the table rate, the 2x leg's ratio is 2 on a correct run, so P7 warns on every run.
    A "2x charged at 1x" bug would then read 1.0 and look clean.
  - The reconciliation of 5.3.3 rebuilds cash from the child's own `commission` column. A wrong rate therefore
    reconciles perfectly.
  - The only hard guard is P3's margin. The spec demonstrates that margin on one column at 50 bp (gap 0.0496,
    5.4.3). At 10 bp it is thin for low-turnover crypto columns.
- **Evidence.**
  - P7 definition: spec line 558. P10's `c` is "the leg's cost" (line 561); P7 does not say which.
  - Map 03 used the leg's rate: its 2x worst case is 0.9934, not about 2 (map03 §3.3).
  - `scratch:referee_quant/cost_gap_probe.py` measured the 1x-to-2x gap, which is the ΔSR a "2x charged at 1x" bug
    shows to P3. On BTC-like synthetic series, hysteresis 0.889 gave 0.0082, 0.0058 and 0.0063, all below the 0.01
    bar. Hysteresis 0.667 gave 0.013 to 0.014, a 1.3x margin. Only hysteresis 0 to 0.444 catch it comfortably.
  - On SPY-like series every column cleared 0.02, so pilot 1 is safe.
  - Synth §7.4 already named "the cost-ratio check P7 made hard" as the alternative.
- **Proposed fix.**
  - Add hard check P7h per fill, in the parent. Compute `expected = last_qty × last_px × Decimal(cost_bps) ×
    Decimal(stress) / 10000` from `input.json`, not from the manifest. Require `abs(commission - expected) <= 0.01`
    USD and `commission_ccy == "USD"`.
  - Have the manifest echo `cost_bps` and `stress`. Assert both equal the input.
  - Define `c_leg = cost_bps × stress / 1e4` once, and use it in P6, P7 and P10. State that P7 excludes bar T-1, as
    P6 does.
  - Extend N7 to a fee model with the wrong rate on a correct 2x input. Expect P7h to fail.

### QUANT-6. The card does not say it is an engine replication on reused data

- **Severity:** major.
- **Section:** 6.5 (card fields), 10.3, 10.4 ("Claim labels").
- **Problem.**
  - Pilot 2 re-runs the five configurations behind a stored PASS, on the same file. That grid was revised after a
    REVISE on the same file (`docs/asset_expansion_study.py:340-343`).
  - A Nautilus PASS adds no statistical evidence about the rule. It only shows that a second engine reproduces the
    arithmetic.
  - Section 10.4 says so, but the label lives only in the spec and the run record. The card, which is the artefact
    the owner reads and which O12 may later surface in the Lab, has no field for it.
  - A second PASS card on the same evidence invites double-counting. That is the overfitting failure the gate exists
    to prevent.
  - Pilot 1 has the same gap. Its SPY series was used inside `S_E1_trend_us` with the same 12-setting grid.
- **Evidence.**
  - `ModelCard` has no claim-label field (`core/quant/validate.py:802-826`).
  - The spec's card table sets `hypothesis` "from the table", and nothing else (spec 6.5, lines 900-917).
  - The house protocol requires the label on every claim: "exploratory, pre-specified on historical data, or
    confirmatory" (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:449-450`).
- **Proposed fix.**
  - Add `rules.claim` to the card, as a free dict key, so no gate code changes.
    - Pilot 2: `"engine replication of S_C3_crypto_trend_btcusd: same file, same five configurations, grid
      revised on this file; adds no evidence about the rule"`.
    - Pilot 1: `"pre-specified on historical data; series previously used inside S_E1_trend_us with the same
      grid; not confirmatory"`.
  - Prefix `hypothesis` with the same label.
  - Copy the data-access history of 10.4 into `data.access_history`.
  - Add a layer-1 test that a written card carries a non-empty `rules.claim`.

### QUANT-7. The expected verdicts misstate the decision order and overstate engine noise

- **Severity:** minor.
- **Section:** 10.3.
- **Problem.**
  - **Pilot 1.** The gate checks INSUFFICIENT_DATA before REJECT (`core/quant/validate.py:586` before `:593`).
    Below 30 trades it returns early, and the benchmark test is never reached.
    - A single sleeve trades far less than the four-sleeve book's 82 (`docs/asset_expansion/results.md:9`).
    - On synthetic SPY-like series the single-sleeve walk-forward made 26 and 40 trades
      (`scratch:referee_quant/tie_probe_fast.py`). Map 03 counted 3 to 23 switches per column in 10 pre-2004 years
      (map03 §4.3).
    - So INSUFFICIENT_DATA is a leading outcome, not a side case. REVISE on the sample check needs the benchmark test
      and the DSR to pass first, which 10.3 itself calls unlikely.
  - **Pilot 2.** "Engine noise could move [bench p] across" is not plausible. The bootstrap is paired, with the same
    blocks on both sides (`core/quant/validate.py:196-208`).
    - With `bench_diff` 0.30 and p 0.07, a normal approximation puts the density of the bootstrap difference at zero
      near 0.66 per unit. Engine ΔSR of about 0.0003 (map03 §4.5) then moves p by about 0.0002, less than one draw
      in 2,000.
    - The realistic causes of a non-PASS with parity passing are a reference error (QUANT-1) and a tie-break
      (QUANT-3).
- **Proposed fix.**
  - Restate pilot 1: INSUFFICIENT_DATA if fewer than 30 OOS trades. Otherwise REJECT on the benchmark test. REVISE
    is unlikely.
  - Note that INSUFFICIENT_DATA says nothing about the benchmark claim.
  - Restate pilot 2's risks as QUANT-1 and QUANT-3. Drop the bench-p noise claim.

### QUANT-8. The realism delta mixes three effects

- **Severity:** minor.
- **Section:** O7, 5.2.5 (gap buffer), 6.3 `realism`, A-5.
- **Problem.**
  - The realism child holds about `1/((1 + c)(1.10))`, roughly 0.905 of equity, while long. The remaining 9.5% earns
    DGS3MO through the overlay.
  - Both comparators hold weight 1.0: "QUANTGEN same-close" and "QUANTGEN weights shifted one session". So the
    reported ΔSR combines the one-session delay, the exposure change and the cash interest.
  - A-5's "Sharpe is nearly invariant to a constant exposure scale" holds only when `rf = 0`. With the overlay,
    `R = x r + (1 - x) rf` on long days.
  - The confound is about `((1 - x)/x)·(mean rf / σ)`, roughly 0.1 × (mean rf / σ). With mean rf about 1.4% and σ
    about 15% a year, that is about 0.01 in Sharpe, near 10% of the -0.098 delay effect (map03 §4.2).
- **Evidence.** Sizing: spec line 377. Comparators: spec line 863. Overlay: spec 5.3.3, line 522.
- **Proposed fix.**
  - Report the delay effect against `simulate(prices, x_t · shift(W, 1), cash_daily=rf)`, where `x_t` is the realism
    child's own exposure path from `onbar_equity.csv`.
  - Report the exposure and cash-interest effect separately, as `SR(simulate(prices, x_t · W)) - SR(pnl_qg)`.
  - The leg stays ungated.

### QUANT-9. The P10 bound is incomplete, and its `c` is ambiguous at 2x

- **Severity:** minor.
- **Section:** 5.4.1 P10 and the paragraph below it.
- **Problem.**
  - On an entry day, `R - pnl = (x - 1)(r - c)` with `x = 1/(1 + c) - δ` and `0 <= δ < P/E`. The full bound is
    therefore `(c/(1 + c) + P/E)(|r| + c)`.
  - The spec's bound drops the `(P/E)·c` term, which is up to 6e-6 at 2x with SPY near $600 and $1M.
  - It also drops the `rf` earned on residual cash after a buy, up to `(P/E)·rf`.
  - Both exceed the 1e-9 slack. P10 is a warning, so the cost is false warnings, which teach readers to ignore P10.
- **Evidence.** The derivation follows from 5.3.3 and `core/quant/strategies.py:82-90`. The F1 golden row t = 3
  stays inside the spec's bound only because r is positive (`R - pnl = -0.0001742`; bound 0.0002279).
- **Proposed fix.** Use `c_leg` (QUANT-5) and the bound
  `(c_leg/(1 + c_leg) + s(t))(|r| + c_leg) + s(t)·rf(t) + 1e-9`, where
  `s(t) = max(P(t), P(entry)) (1 + c_leg) / E-(t)`.

### QUANT-10. The rehearsal does not cover pilot-window conditions

- **Severity:** minor.
- **Section:** 5.4.3 (last paragraph), Step 7 done-when, Step 7A.
- **Problem.**
  - Every margin was measured on 1995-2004 SPY, where adjusted prices are about $26 to $110. That data has no 2008 or
    2020 days.
  - The pilot window reaches about $650. At that price the whole-share residual is up to 6.5e-4 of equity. Its
    entry days include returns of ±10% or more.
  - The spec marks the effect UNVERIFIED but plans no test of it before the of-record run.
- **Evidence.** Spec lines 618-622; map03 §2.7 ("at most 0.08% at $1M for SPY prices up to about $770").
- **Proposed fix.**
  - Add a synthetic stress rehearsal to Step 7: about 5,500 seeded bars, a price path from about 80 to 650, volatility
    clusters, and planted ±10% days on decision bars. Run both engines at 1x and 2x.
  - Report worst corr, ΔSR, P6, P7 and P10 next to the bars.
  - Repeat it in standard precision at Step 7A. No pilot-window data is touched.

### QUANT-11. "Engine" in the card overstates what Nautilus executed

- **Severity:** minor.
- **Section:** 6.5 `rules.engine`, section 1 item 2.
- **Problem.**
  - Nautilus executes each grid column on its own. The walk-forward strategy switches columns at each origin.
  - Those switches are never executed or charged, in either engine: `walk_forward` takes the chosen column's own
    turnover (`core/quant/validate.py:375`).
  - The card's `"nautilus_trader 1.231.0 BacktestEngine, same-bar close"` can be read as an event-driven execution of
    the selected strategy. It is not.
- **Proposed fix.** Write `rules.engine` as `"per-column P&L from nautilus_trader 1.231.0 BacktestEngine
  (same-bar close); walk-forward column switches are not executed or charged (validate.py:375)"`.

## Notes

What I checked and found sound:
- **Return identity.** R(t), TV(t) and the drop of bar T-1 match `simulate` and `turnover[:-1]`
  (`core/quant/strategies.py:82-90`). The F1 values reproduce by hand: t = 3, `x = 1,000,000/1,005,001`,
  `R = x·0.035 = 0.0348258`.
- **tsmom raw form.** It is correct: `pnl_matrix` passes only `theta` (`core/quant/strategies.py:384`), so
  `cash_rate_daily` stays 0 (`:173, 180`).
- **Decision schedule.** `arange(L, T, s)` (`core/quant/strategies.py:146-147, 176`) equals the port's
  `i >= L and (i - L) % s == 0`.
- **Embargo.** There is no leakage at embargo 21 with step 42. IS rows end at o - 1 and use prices up to o. OOS rows
  start at o + 21 (`core/quant/validate.py:370-375`). Each column is causal, so a position held across the origin is
  out-of-sample P&L, not look-ahead.
- **P12.** The truncation and indexing match `core/quant/validate.py:374-375`.
- **Bench alignment.** It matches the study's dict map (`docs/asset_expansion_study.py:186-190`). If the lengths ever
  differed, `score_strategy` would drop the benchmark test silently (`core/quant/validate.py:516, 520-521`). I suggest
  asserting `math.isfinite(sc.bench_p)` in 5.5. It is cheap.
- **Realism rows in N (K11a).** They are conservative, and the cost stays inside the bridge. The Lab scores with
  `n_trials=len(grid)` (`ui/strategy_lab_page.py:127`), and the study types N by hand.
- **Constant-scale sizing bugs.** They cannot change the decision: the gate's statistics are scale-invariant except
  the reported `total_return`, `max_drawdown` and `turnover_annual`. A large mis-sizing is caught by P2 anyway,
  because a fixed-share position with idle cash drifts.
- **Cent rounding on 8-decimal BTC sizing.** It did not overdraw the CASH account: 900 synthetic buys, 0 forced
  stops, minimum cash 0.00 (`scratch:referee_quant/cent_probe.py`). The engine refuses a negative balance
  (`nt:accounting/accounts/cash.pyx:155-156`). Standard precision on Windows is UNVERIFIED, as 3.6 says.
- **Pilot-2 DSR sensitivity.** Command:
  `python3 -I -B -c` with `z = Φ⁻¹(0.9999775)`, `sr = 1.18693/√252`, `T = 3634` and the house `expected_max_sharpe`
  formula. Result: DSR >= 0.9997 at N = 50, 200 and 1,000 for denominators 0.9 to 1.1.

UNVERIFIED in this review:
- Row counts of `E1.jsonl` and `C3.jsonl`. I did not read the production ledgers.
- Whether the pilot-window SPY single-sleeve trade count is below 30. I estimated it from synthetic data and from the
  four-sleeve card only.
- Whether `docs/asset_expansion_study.py` imports cleanly under the runner. Its top level imports `config` and
  `core.quant` only (`:49-52`), and `REFRESH = False` is set at `:844`. I did not import it.

Housekeeping, outside my lens:
- Step 1's done-when names `docs/superpowers/specs/2026-10-26-review/round<k>_<name>.md` (spec line 1109). This round
  writes to `docs/superpowers/specs/2026-10-26-nautilus-review/`. One of the two should change.
- `card.save(Path("docs/nautilus_bridge/cards"))` in 5.5 step 7 is relative to the working directory. Anchor it at
  the repo root.
