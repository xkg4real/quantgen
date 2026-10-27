# Round 2 referee report: quantitative methodology

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 2 (working tree; "spec:N" below is a
line of that file).
Referee: Claude, quantitative-methodology lens (parity bars, selection-matched walk-forward, trial counting, cost
checks, decision agreement, claim labels, expected verdicts).
Repo: QUANTGEN code at `6f7c610`. HEAD `a14954f` adds only the spec and the review folder. Engine: `nautilus_trader`
1.231.0 in `scratch:ntvenv`. `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probes, all in `scratch:referee2_quant/`. They use synthetic prices, hand-built scores, the DGS3MO rate file and the
stored cards' statistics only. No SPY row, no BTC price, no ledger row. QUANTGEN was imported read-only.
- `rf_probe.py`: the spec's rf formula against the study's `rf_daily`, on `fred_DGS3MO.csv` and a synthetic weekday
  calendar.
- `flags_probe.py`: hand-built `StrategyScore` objects through `validate._decide_strategy`, compared with the flag list
  of spec 5.5 step 5.
- `money_probe.py` (venv): how `Money` rounds to the cent.
- `round_probe.py`: `np.round(x, 9)` against `float(f"{x:.9f}")` on 800,000 synthetic prices.
- `stress_leg_probe.py`: a BTC-like 2x leg charged at 1x, against P2 and P3, on three synthetic seeds.

## Verdict

**ACCEPT_WITH_CHANGES.**

Revision 2 applies all eleven of my round-1 rulings. The core design is now sound from my lens:
- Both engines use QUANTGEN's selection, so engine noise no longer picks the card's out-of-sample columns.
- Both matrices are scored, and a card needs agreement.
- P7 checks the commission rate directly.
- The trial count is a union, not a maximum.
- P0 ties the input arrays to the study's loaders.

Two defects stop me from saying "build today with no further questions":
- **QUANT-R2-1 (major).** The cash-rate formula of 5.3.2 step 6, read as written, gives NaN on 36 NYSE-open
  bond-market holidays in pilot 1's window. R-06 then refuses pilot 1. No rehearsal or test would show this before the
  of-record run.
- **QUANT-R2-2 (major).** The agreement flags of 5.5 step 5 are not the predicates the gate's decision tree reads.
  They can withhold pilot 2's expected PASS on a statistic the gate ignores for 5 configurations. They miss the
  over-search predicate that gates pilot 2. They pass a run whose benchmark test was silently dropped.

Both fixes are a few lines. Neither changes gate code. Five minor issues follow.

## Sections reviewed

- Status, Owner context, section 1, section 2 (O5, O7, O11, O14).
- 3.5 and 3.9.
- 4.2.
- 5.2.3 to 5.2.5 (fees, rounding, the ports), against `core/quant/strategies.py:69-90, 111-116, 162-187, 330-348,
  379-398`.
- 5.3.2, all steps, against `docs/asset_expansion_study.py:41-58, 68-79, 94-104, 138-153, 172-215, 271-279, 329-343,
  724-732, 844`.
- 5.3.3, 5.3.4.
- 5.4.1 (P0 to P13), 5.4.2 (`select_matched`) and 5.4.3, against `core/quant/validate.py:137-143, 268-270, 332-381`.
- 5.5, against `core/quant/validate.py:456-623`, including `_decide_strategy` at `:536-623`.
- 6.3 to 6.6, against `core/quant/gate_ledger.py:60-64, 168-171, 333-386` and `ui/strategy_lab_page.py:50-82, 127`.
- Section 7 (R-06, R-13, G-01 to G-07).
- 8.2 (F1, F2, N4, N6, N7, N8), and 8.3 tests 1, 2, 7, 14, 20, 21, 29 and 30.
- 8.4 tests 7 and 11.
- Section 9 (Steps 7, 8, 9).
- 10.1 to 10.4, against the stored cards `S_C3_crypto_trend_btcusd`, `S_C3_crypto_trend_krwbtc`, `S_E1_trend_us` and
  `S_E1_trend_krx`.
- 11 (risks 9, 10, 11, 15, 16), Appendix A (K3, K8, K9, K12), Appendix B (the QUANT rows).

## Round-1 issues

- **QUANT-1: resolved.** P0a (spec:504) and P0b (spec:568) tie dates, closes, rf and the benchmark to the study's own
  loaders. `parity_scope` says parity validates the engine, not the data. Residuals: the protocol arguments are not
  tied to the study (QUANT-R2-5), and the rf formula itself is wrong (QUANT-R2-1).
- **QUANT-2: resolved in design.** Both matrices are always scored, and a card needs equal decisions and flags
  (spec:637-638, G-02). The flag list itself is wrong (QUANT-R2-2).
- **QUANT-3: resolved.**
  - `select_matched` (spec:592-599) reproduces `walk_forward`'s slicing, including `lo_i = max(0, o - w_is)` and the
    n_origins x G `is_sharpes` (`core/quant/validate.py:333-343, 371-379`).
  - L1-21 tests it bit for bit.
  - P11 is a diagnostic. The Step 7 done-when no longer asks for the same column at every origin.
- **QUANT-4: resolved.** `n_trials = family_n_raw + U` (spec:636). `n_raw` is `len(rows)` and `append` deduplicates
  on `config_id` (`core/quant/gate_ledger.py:333-346`), so the sum is the size of the union. Four counts are stored. The
  false "never a false PASS" claim is gone from O11.
- **QUANT-5: resolved for child-side errors.** P7 is hard and recomputed in the parent (spec:575). Two gaps remain in
  how it is anchored and how it rounds (QUANT-R2-3).
- **QUANT-6: resolved.** Cards carry `claim_label`, which also prefixes `hypothesis` (spec:876-877). Pilot 2's label is
  right. Pilot 1's label is new text that contradicts 10.4 (QUANT-R2-4).
- **QUANT-7: resolved.** Pilot 1 now puts INSUFFICIENT_DATA first, and the gate does return early on the trade floor
  (`core/quant/validate.py:586`). Pilot 2's paragraph still names `bench_p` as the likely flip (see Notes).
- **QUANT-8: resolved.** Moot: ruling C-1 deferred the realism leg.
- **QUANT-9: resolved.** The P10 bound (spec:578) is correct.
  - On an entry day, `q P (1 + c) <= E` gives `|x - 1| < c/(1 + c) + P/E`.
  - On held days, the residual cash is below `c/(1 + c)` for both pilots.
  - The rf term covers the overlay.
  - F1's t = 3 row: gap 0.0001742 against a bound of 0.0002284.
- **QUANT-10: resolved.** N6 (spec:1061) runs as L2-11, at Step 7 and again in the Windows full run at Step 7A. N6 has
  no cash rate (QUANT-R2-6).
- **QUANT-11: resolved.** `rules.engine` now says that walk-forward switches are executed in neither engine
  (spec:877).

## New issues

### QUANT-R2-1. The rf formula gives NaN on bond-market holidays, so R-06 refuses pilot 1

- **Severity:** major. It is fail-closed, so no wrong verdict results. But it blocks pilot 1 of record. Nothing before
  Step 8 would show it.
- **Section:** 5.3.2 step 6 (spec:503), R-06 (spec:963), 8.3 test 7 (spec:1078).
- **Problem.**
  - Step 6 says `rf = DGS3MO.reindex(dates, method="ffill") / 100 / 252`. R-06 refuses "NaN after the forward fill".
  - `fred_DGS3MO.csv` has an empty value on every bond-market holiday.
  - `reindex(..., method="ffill")` returns the exact-match value when the date exists in the source, even when that
    value is NaN. So every SPY session on a bond holiday gets NaN. Columbus Day and Veterans Day are two such holidays.
  - The study drops NaN first (`fred` returns `s.dropna()`, `docs/asset_expansion_study.py:104`) and then reindexes
    (`:150`). It never sees these NaNs.
  - Step 6 says only what the runner must not copy (the 3% fallback and the leading fill). It never says to drop NaN
    first. An engineer who reads the CSV and applies the line as written gets a refusal.
  - P0a would refuse too (R-13), because the arrays differ from the study's.
  - Steps 3 to 7 use synthetic rates, and L1-7 plants only a leading NaN. So the defect first shows when the owner runs
    pilot 1 of record. Fixing it then means a spec revision and a new sign-off.
- **Evidence.**
  - `rf_probe.py` on `fred_DGS3MO.csv` (md5 `661722143f24930a29b58c535d227c1b`, 9,583 rows, 395 empty, all on weekdays).
  - Over every weekday from 2004-12-01 to 2026-09-25:
    - the literal formula gives 233 NaN; the study gives 0;
    - the literal formula is NaN on all 36 Columbus Days and weekday Veterans Days from 2005 to 2025;
    - where the literal formula is finite, it is byte-equal to the study;
    - `DGS3MO.dropna().reindex(dates, method="ffill") / 100 / 252` is byte-equal to the study everywhere.
- **Proposed fix.**
  - Step 6: read DGS3MO as the study does (`read_csv(index_col=0, parse_dates=True).iloc[:, 0]`). Then compute
    `rf = DGS3MO.dropna().reindex(dates, method="ffill") / 100 / 252`, and cite `docs/asset_expansion_study.py:94-104,
    150`.
  - R-06 then refuses only a session before the first observation, which was the intent.
  - Add a control to L1-7: a synthetic DGS3MO with an empty value on a mid-series session date. Expect the value
    filled from the prior observation, P0a passing, and no refusal. Keep the leading-NaN control, which still refuses.

### QUANT-R2-2. The agreement flags do not mirror the gate's decision tree

- **Severity:** major.
- **Section:** 5.5 step 5 (spec:638), G-02 (spec:990), N8 (spec:1063), 8.3 tests 2 and 14 (spec:1073, 1085).
- **Problem.** Spec 5.5 step 5 lists 13 flags as "the thresholds the decision tree reads
  (`core/quant/validate.py:576-602`)". They are not. Four defects:
  1. **Raw PBO is in the list, though the tree ignores it for 5 configurations.** The tree reads PBO only when
     `n_configs >= pbo_min_configs` (8; `:544, 576-577`). For pilot 2 (5 columns), `pbo_ok` is `flat` and
     `pbo_reject` is False whatever the PBO. The stored card's PBO is 0.1909, 0.0091 below `pbo_reject`. An engine
     difference that moves PBO across 0.20 withholds pilot 2's expected PASS on a statistic the gate does not read.
  2. **`flat` is missing.** `flat = prob_loss_oos <= prob_loss_max` (`:545`) enters `pbo_ok` and `pbo_reject` in both
     pilots. For pilot 2 it is the whole over-search check. Step 9's own done-when says so (spec:1227). It is not in
     the list, so "every gate flag agrees" is false whenever only `flat` differs.
  3. **The min-track-record test is missing** (`n_sessions < mtr`, `:584, 606-607`). So are `math.isfinite(dsr)`
     (`:593`) and `has_bench` (`:557`).
  4. **A dropped benchmark test passes silently.** `score_strategy` drops the benchmark test when the series lengths
     differ (`:516, 520-521`). Then `bench_p` is NaN for both engines. The flag "false when NaN" is equal across
     engines, so a PASS card is written although "beats buy-and-hold" was never tested. P0b checks the benchmark's
     values, not its alignment to `wf.dates`.
- **Evidence.** `flags_probe.py`, using the gate's own `_decide_strategy` on hand-built scores near pilot 2's stored
  values:
  - A: 5 configurations, PBO 0.19 against 0.21. Decisions PASS / PASS. The spec's rule withholds.
  - B: 12 configurations, both REJECT on the benchmark, `prob_loss` 0.09 against 0.11. A gate predicate differs, but
    the spec's flags are equal and the card is written.
  - C: 5 configurations, `prob_loss` 0.09 against 0.11. Decisions PASS / REVISE. The spec's flags say "equal". Only the
    decision comparison catches it.
  - D: `bench_p` NaN on both. PASS / PASS, flags equal, card written.
  - Also, "a scorer seam" (N8, L1-14) names no parameter of `run(...)` (spec:488-490).
- **Proposed fix.**
  - Define `parity.gate_predicates(score, gate) -> dict[str, bool]` in `tools/nautilus/parity.py`. It recomputes
    exactly what `_decide_strategy` reads (`core/quant/validate.py:544-545, 557, 576-586, 592-593, 606-607`):
    - `ci_pos`, `dsr_ok`, `dsr_finite`;
    - `pbo_meaningful`, `flat`, and `pbo_ok` and `pbo_reject` as computed at `:576-577`;
    - `oos_is_ok`, `stress_ok`, `years_ok`, `plateau_ok`, `sample_ok`;
    - `floor_ok`, `n_years_ok`, `sessions_ok`;
    - `mtr_ok` (`n_sessions >= min_track_record(sr_oos, ci_level)`);
    - `has_bench`, `bench_ok`.
  - Agreement means equal decisions and equal predicate dicts.
  - When the table names a benchmark, require `has_bench` on both scores. Otherwise WITHHELD with "benchmark test
    dropped".
  - Replace the sentence "the thresholds the decision tree reads (...576-602)".
  - Make cases A to D fixtures N8a to N8d, with the expected outcomes: A card, B WITHHELD, C WITHHELD, D WITHHELD.
  - Test them through a pure `parity.agree(sc_qg, sc_nt, gate)`, and name the run-level seam (`hooks["score"]`) for
    L1-14.

### QUANT-R2-3. P7 is anchored to `input.json`, and its rounding rule is wrong

- **Severity:** minor.
- **Section:** 5.4.1 P7 and the paragraph below it (spec:575, 587-588), N7 (spec:1062).
- **Problem.**
  - **Anchor.** P7 takes `cost_bps` and `stress` "from `input.json`", which the parent itself writes, and checks that
    the manifest echoes them. If the parent writes stress "1" into the 2x leg, P7 passes by construction. The phrase
    "so a 2x leg reads stress 2" does not follow from the check. The ruling asked for exactly that guarantee
    (round1_rulings.md:93-95).
  - **Rounding.** The total uses expectations "rounded half-even". That mode is marked UNVERIFIED. It is now verified
    false:
    - `Money.__init__` converts any value to a double (`nt:model/objects.pyx:1190`);
    - the Rust core then rounds it (`:1205`);
    - the result is half away from zero: 0.025 gives 0.03, 1.125 gives 1.13, -0.015 gives -0.02 (`money_probe.py`,
      high precision).
- **Evidence.**
  - `stress_leg_probe.py`: a BTC-like 2x leg charged at 1x passes P2 on all 15 columns (3 seeds x 5 hysteresis
    values; corr 0.99991 to 0.99999). P3 catches it only for hysteresis 0.667 and below (dSR 0.0135 to 0.0708). At
    0.889, dSR is 0.0076 to 0.0097, inside the bar.
  - A run-wide parent bug is therefore still withheld through the other columns. A bug confined to one column is
    caught by nothing but a correctly anchored P7.
  - The rounding mismatch costs one cent per exact tie, inside the 1e-6 tolerance, so it is cosmetic.
- **Proposed fix.**
  - P7's `expected` uses the table's `cost_bps` and the leg's nominal stress (1 or 2, from the runner's own loop).
  - The parent also asserts that `input.json` and the manifest echo both values.
  - Extend N7 with a 2x leg whose `input.json` says stress "1": P7 must fail.
  - Replace "half-even ... UNVERIFIED" with "Money rounds the double half away from zero at the currency precision
    (`nt:model/objects.pyx:1190, 1205`)". Either keep the 1e-6 total tolerance and drop the mode claim, or round the
    expectations with `ROUND_HALF_UP`.

### QUANT-R2-4. Pilot 1's claim label contradicts 10.4 and omits the data reuse

- **Severity:** minor.
- **Section:** 10.1 (spec:1252), 6.5 `hypothesis` (spec:876), 10.4 (spec:1310-1312).
- **Problem.**
  - 10.1 fixes pilot 1's label as "engine replication of QUANTGEN's SPY trend grid". But no single-SPY QUANTGEN
    result exists to replicate. The card carries a new gate verdict on a single sleeve.
  - 10.4 calls the same claim "*pre-specified on historical data*, on a series already used inside a four-sleeve book".
    The label printed on the card omits that reuse. Reuse with the same 12-setting grid is the overfitting-relevant
    fact.
  - The house protocol labels each claim with one of three terms: "exploratory", "pre-specified on historical data" or
    "confirmatory" (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:448-449`). Neither
    pilot label starts with one of them.
- **Proposed fix.**
  - Pilot 1: "pre-specified on historical data; the SPY series was used inside S_E1_trend_us with the same 12-setting
    grid; not confirmatory".
  - Pilot 2: "pre-specified on historical data, engine replication: stored card S_C3_crypto_trend_btcusd on the same
    file and configurations, grid revised on this file; not new evidence about the rule".
  - L1-30 asserts that each `claim_label` starts with one of the three house terms.

### QUANT-R2-5. The protocol arguments are not tied to the study, and pilot 2's stored card is unused

- **Severity:** minor.
- **Section:** 5.3.2 step 1 (spec:498), 10.2 and 10.3 (spec:1260-1295), 8.3 test 29 (spec:1100).
- **Problem.**
  - P0 ties the arrays to the study. Nothing ties the scoring arguments: `embargo`, `domain` and `cost_bps` (R-07
    checks only that the cost is at or above the floor). Step 1 asserts capital, precision, volume and seed only.
  - Suppose a table carried embargo 21 instead of 1 for pilot 2, or cost 20 instead of 10. Parity would still pass,
    the engines would agree, and a card for a different protocol would be written under the registered rows. `embargo`
    is not part of `config_id` (`core/quant/gate_ledger.py:60-61`).
  - 10.3 expects PASS "if parity holds and P0 shows the inputs equal the study's", but never checks that the reference
    reproduces the stored card.
- **Evidence.**
  - The stored card holds every target that does not depend on `n_trials`: `chosen_last` `{"hysteresis": 0.0}`,
    `n_trades` 144, `n_sessions` 3634, `n_years` 11, `sr_oos` 1.18693264, `ci90` [0.72260097, 1.64132208], `pbo`
    0.19090909, `prob_loss_oos` 0.0, `bench_p` 0.07, `rules.embargo` 1, `costs.cost_bps` 10.0.
  - The study's own scoring call is `docs/asset_expansion_study.py:184-193, 334-339`.
  - The bridge's only input difference is 9-decimal rounding, so a 1e-6 tolerance suffices.
- **Proposed fix.**
  - (a) Extend L1-29: each pilot table's `embargo`, `cost_bps`, `grid`, `domain` and benchmark definition must equal
    the study's call. For E1 that is embargo 21 and `COST["us"]` at `:271-279`; for C3, embargo 1, `COST["crypto"]`
    and the domain at `:329-343`. For pilot 2, they must also equal the stored card's `rules` and `costs`.
  - (b) Add G-08 for pilot 2, after scoring. `sc_qg` must reproduce the stored card:
    - exactly on `chosen_last`, `n_trades`, `n_sessions` and `n_years`;
    - within 1e-6 on `sr_oos`, `ci90`, `oos_is`, `sr_stress`, `years_positive`, `plateau`, `pbo` and `prob_loss_oos`;
    - within 1/2000 on `bench_p`.
  - Otherwise WITHHELD with "reference does not reproduce S_C3_crypto_trend_btcusd". Pilot 1 has no single-SPY card,
    so (a) only.

### QUANT-R2-6. No fixture or test exercises the cash-interest overlay

- **Severity:** minor.
- **Section:** 5.3.3 (spec:525), 5.4.1 P10, 8.2 F1 and N6 (spec:1011-1030, 1061), 8.3 test 1, 8.4 test 7.
- **Problem.**
  - F1 and F2 have rf = 0. N6 and L2-7 name no rate.
  - So the overlay term `(cash(t)/E-(t)) rf(t)` and P10's rf term first run at pilot 1 of record. So does the
    reference's `cash_daily=rf`.
  - Suppose the overlay is omitted, or uses `cash(t-1)`. For a SPY switch flat about 30% of days, at a mean DGS3MO near
    1.3% and volatility near 12%, that is a ΔSR of about 0.03. This is my estimate, not a measurement. P3 then
    withholds pilot 1 of record. It is fail-closed, but it costs the of-record run.
- **Proposed fix.**
  - Add F1r: F1 with a constant rf of 0.0001 per session. Hand values for R on flat and entry days go into 8.2, checked
    by L1-1.
  - Give N6 and L2-7 a synthetic rf path (0 to 5% a year, with steps).

### QUANT-R2-7. The rounding function is not named

- **Severity:** minor.
- **Section:** 5.2.4 (spec:374), 5.2.5 (spec:399), 5.3.2 steps 5 and 7 (spec:502, 504).
- **Problem.**
  - Step 5 "rounds once to 9 decimals" and 5.2.4 writes `f"{x:.{p}f}"`, but no function is named. P0a then requires
    byte equality with `np.round(pn.prices[:, 0], 9)`.
  - `np.round` is not correctly rounded. Python's formatting, and `round()`, are.
  - An implementation that rounds by formatting fails P0a (R-13) on some real files.
- **Evidence.** `round_probe.py`, 200,000 draws per case:
  - `np.round(x, 9)` differs from `float(f"{x:.9f}")` by 1e-9 on 5 SPY-like and 970 BTC-like full-precision doubles,
    and on none that came from float32.
  - `float(f"{np.round(x, 9):.9f}") == np.round(x, 9)` held in 800,000 of 800,000 cases. So 5.2.5's claim, that the
    child's `float(close_str)` equals the parent's float, holds when the parent uses `np.round`.
  - Whether the cache's closes are full doubles is UNVERIFIED. I did not read the price files.
- **Proposed fix.**
  - Step 5: `closes = np.round(raw, 9)`, the one rounding of the bridge.
  - 5.2.4 writes `f"{y:.9f}"` of that array.
  - The runner asserts `float(f"{y:.9f}") == y` for every close before writing `bars.csv`.

## Notes

Checked and sound:
- **Selection-matched walk-forward.** `select_matched` takes origins, chosen columns, slicing and `is_sharpes` from
  `walk_forward` (`core/quant/validate.py:371-379`). `sc_nt`'s `sr_is`, `oos_is` and plateau then read Nautilus IS
  Sharpes at QUANTGEN's chosen columns (`:502, 510-511`). That is the consistent pairing.
- **Trade counts agree across engines.** `n_trades` counts OOS days with `|turnover| > 1e-12` (`:514`), and P4 forces
  equal fill days. So the trade-floor branch that gives pilot 1's expected INSUFFICIENT_DATA (`:586`) is
  engine-invariant.
- **Scoring call.** It matches the study's: `score_strategy(wf, grid=, full_pnl=M, n_trials=, bench_daily=, seed=11,
  domain=)` (`docs/asset_expansion_study.py:193`). The dict-map bench alignment is at `:189`.
- **Study import for P0a.** It is safe as specified: `CACHE` and `REFRESH` are module globals read at call time
  (`:69-70, 99`), and `REFRESH = False` is set at import (`:844`). `panel` filters `>= start` after `dropna`
  (`:138-145`), as step 5 describes.
- **`study_configs`.** They match the stored cards. The E1 four-sleeve symbols sort to `["GLD", "QQQ", "SPY", "TLT"]`
  at 50.0. KRX is at 3.0. KRW-BTC is at 10.0 with `N_total` 11. No other stored E1 or C3 card exists. U should count
  *distinct* absent `config_id`s; the text says "the number of `study_configs`". No duplicate exists today.
- **Pilot-2 DSR.** It stays at or above 0.9997 up to N = 1,000. The round-1 inversion holds.

Minor concerns, not raised as issues:
- **P1's exemption is moot.** An exempt P1 mismatch changes the Nautilus fill days, so P4 (hard, no exemption)
  withholds anyway (spec:569, 572). Either let P4 inherit P1's exemptions, or say that an exempt mismatch still
  withholds. Measured frequency is nil (0 in 12 x 2,497 bars).
- **P11 never withholds, so a localized engine divergence is visible only as a warning.** By my estimate (not a
  measurement), P3's full-sample bound of 0.01 still allows a bias confined to one 756-session window to reach a ΔSR
  of about 0.07 inside that window. Suggest: a P11 mismatch where QUANTGEN's in-sample gap exceeds 0.005 becomes a
  warning on the card.
- **Pilot 2's risk paragraph (spec:1291-1293) still points at `bench_p` near 0.10.** The bootstrap is paired (`core/quant/validate.py:186-210`).
  An engine ΔSR of about 3e-4 moves p by about one draw in 2,000, against a margin of 60 draws. The closer statistic to
  a bar is PBO (0.1909 against 0.20), which QUANT-R2-2 removes from the agreement set.
- **Ordering in 5.5.** The preamble says "only when every hard check passes", but P12 needs `wf_qg` and `wf_nt`, which
  5.5 step 1 builds. 4.2 row 16 has the right order. Align 5.5's wording with it.
- **Card field.** The card carries no `data.access_history`. 10.4's history is in the run record only. This is
  acceptable; noted for O12.

Data touched in this round, for 10.4:
- `fred_DGS3MO.csv`, all dates; only its NaN pattern was computed.
- The four stored cards' statistics.
- No SPY price, no BTC price, no ledger row.

UNVERIFIED:
- Whether the cache's SPY and BTC closes are full doubles (QUANT-R2-7).
- Standard-precision `Money` rounding on Windows.
- The ΔSR estimates in QUANT-R2-6 and the P11 note. They are arithmetic, not measurements.
