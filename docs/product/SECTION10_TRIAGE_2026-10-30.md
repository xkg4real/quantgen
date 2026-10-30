# §10: initial triage and first correction

The owner's 2026-10-30 decision includes §10 findings in the formal correction
scope and authorizes ordering the work. This document records an initial slice;
it does not close the full §10 list or change any gate, stored card or holdout.

Sources are `KNOWN_ERRORS_REGISTER_2026-10-28.md` §10 and
`MODEL_LIMITS_REGISTER_2026-10-28.md` §6 on research commit
`2da6469d8b3d45eab61d682555ff630ce1f564f7`, under `docs/nautilus_bridge/`.
Current-code diagnostics start from product main `0cc30c3`. Historical audit
results are distinguished from these fresh synthetic reproductions.

## Inventory and ordering

`SECTION10_QUEUE_2026-10-30.json` retains all **71 IDs** and **14 observation
models**. Four aliases explicitly stated by the source are deduplicated:
NEW-M6-06 → M4-N1; NEW-M6-07 → M4-N3; NEW-M6-08 → M4-N2;
NEW-M6-09 → N2. This yields **67 groups**, not 67 verified defects. The 14
observation models can each contain multiple issues; they are not 14 atomic bugs.
N-M1-10's N16 reference is related evidence, not an extra §10 row.

Fifteen IDs lack a standalone description in the error table. Their model
register limitations have been consulted, but where several limitations share
an ID list the exact attribution still needs confirmation. These retain
`mapping_needs_disambiguation=true`; none is silently discarded or marked fixed.

Priority is based on impact and dependencies:

1. Reproduce decision-boundary and payload issues first. Gate/ledger changes
   remain outside this patch; compare in isolation, preserve stored decisions.
   Check Flet and Qt payloads separately: native filtering alone does not close
   NEW-M6-18 for the browser.
2. Correct reproducible numerical/display faults outside protected harnesses.
   **NEW-M6-01** is the first such unit. Next candidates include missing-result
   displays and ETF underlying/rate conventions, with independent oracles.
3. Separate model choices from arithmetic bugs. Gross exposure from per-asset
   caps and negative-Sharpe optimization require clear conventions and warnings;
   replacing their objectives would be a separate model change.
4. Resolve remaining source, disclosure and compatibility gaps, then narrow
   regressions. A warning about a future library return type is not a current
   numerical failure. Each untested row remains `NOT_RUN`.

## Five bounded reproductions

Run `python -m tools.status.section10_probes`. It uses deterministic synthetic
inputs, disables dotenv loading, blocks socket connections, and never starts a
research run or reads an actual ledger. Results before the correction and the
corrected HAC result are in `SECTION10_PROBE_RESULTS_2026-10-30.json`.

| ID | Observation at product main 0cc30c3 | Disposition |
| --- | --- | --- |
| N-M1-01 | 200 observations, zero exceptions, alpha .01: current p=.155218; boundary LR p=.044960 | Reproduced; gate/harness unchanged |
| N1 | Four synthetic assets, per-asset cap 1: maximum gross exposure 4 | Reproduced; model/label distinction, not silently normalized |
| N-M1-09 | All excess returns negative: max-Sharpe puts weight 1 in the 40%-vol asset, Sharpe -.20, empty warning | Reproduced; mathematically consistent objective, disclosure/design issue |
| NEW-M6-01 | 443 regression observations: reported t=5.263134 versus independent HAC t=.250059; ratio=sqrt(443) | Corrected in this change |
| NEW-M6-03 | Synthetic stationary AR(1), phi=-.7: infinite half-life | Reproduced; an oscillating process must not be described as non-stationary solely from this output |

## NEW-M6-01 correction

`_hac_var(score, lag)` returns the variance of the **sample mean**, i.e. the
long-run variance divided by n. The regression denominator is `sum(x_centered²)`.
The standard error therefore uses `sqrt(_hac_var) * n / denominator`.
The previous `sqrt(_hac_var * n) / denominator` understated the standard error
by sqrt(n), overstating the absolute t statistic by the same factor.

The slope, premium level, sample alignment, lag convention, annualization and
data-provider path are unchanged. The shared crypto workflow exposes the
corrected statistic to both Flet and Qt. Historical cards and frozen studies
are not regenerated, and statistical significance is not presented as a trading
instruction.

Validation: the independent full matrix Newey-West sandwich test failed on the
old code for all six combinations of sample length 180/540 and horizon 1/7/14.
It passes after the correction. The insufficient-sample test and native public
crypto adapter regression pass as well. The corrected diagnostic ratio is 1.
These are synthetic arithmetic checks, not live-provider or research validation.

The remaining 66 groups and 14 observation models are not marked corrected.
The five initial probes do not constitute full §10 reproduction coverage.

## Subsequent verified units

The preceding counts and probe observations describe the initial PR20 slice.
PR22 corrected NEW-M6-18; PR23 corrected M4-N5 and M3-N07. The portfolio
disclosure follow-up closes N-M1-09/N-M1-10's missing warnings/constraint scope
without changing objectives or weights; see `PORTFOLIO_SCOPE_2026-10-30.md`.
The current machine-readable queue therefore records **6/67** corrected groups,
**61** remaining groups and **14** observation-model rows. Fifteen ambiguous
ID mappings remain unresolved. The original five-probe JSON is historical
evidence and is not overwritten with later results.

The subsequent N-M1-11 wording correction is described in
`TERMINAL_TARGET_2026-10-30.md`: target probability is the terminal event,
not pathwise crossing. This raises the latest queue to **7/67** corrected
groups and **60** remaining groups; the 14 observation rows and 15 ambiguous
mappings remain open. The solver and simulation mathematics are unchanged.

N-M1-03 then distinguishes sample/next-session/horizon-average annualized
volatility across Flet, PyQt6 and commentary without changing any estimator;
see `MC_VOLATILITY_2026-10-30.md`. Latest queue: **8/67** corrected, **59**
remaining groups; 14 observation rows and 15 ambiguous mappings remain open.

N1 now discloses per-asset caps, stitched OOS gross/borrowing and the 1×
equal-weight benchmark scope for vol_target and crypto_trend; see
`STRATEGY_EXPOSURE_2026-10-30.md`. Weight/score/ledger math is unchanged.
The latest queue is **9/67** corrected and **58** remaining groups, with
14 observation rows and 15 ambiguous mappings still open. A narrow Flet
initial-equity/date alignment fix is included, not full audit closure.

NEW-M6-03 corrects negative stable AR(1) amplitude half-life and its ETF/Crypto
interpretation; see `AR1_DECAY_2026-10-30.md`. Missing/non-decaying estimates
are no longer described as slow reversion. Positive-phi results and pairs
weights/gates are unchanged. Latest queue: **10/67** corrected, **57**
remaining groups; 14 observation rows and 15 ambiguous mappings remain.

## Funding inference partial safeguard

NEW-M6-02/a removes the invalid IID p-value, introduces an explicitly conditional
circular-phase diagnostic, and distinguishes historical funding cards in both UIs,
AI and exports. See `FUNDING_INFERENCE_2026-10-30.md`. Synthetic independent-null
300-case fractions below .05: old .3900, exploratory .04333. Real-market assumptions
and historical validation remain open: **10/67** complete and **57** remaining
(including NEW-M6-02); **7** additional IDs reproduced. This is a completed sub-scope,
not closure of the full inference defect.
