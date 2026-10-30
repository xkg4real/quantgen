# §10 FICC corrections: M4-N5 and M3-N07

Source findings: research commit `2da6469`, MODEL_LIMITS_REGISTER §6 entries
M4-08 (Fama) and M3-15 (cap/floor). Fresh reproductions use product main
`450fa00`, synthetic rate/spot inputs and disposable test processes only.

## M4-N5: Fama slope uncertainty

The module promised a HAC statistic but returned the homoskedastic OLS one.
Its unused calculation tested the mean score, which is zero by the OLS normal
equations. The slope and rate/spot alignment were already independent of that
unused result.

The slope standard error now uses a lag-1 Bartlett/Newey-West sandwich. With
`u_t = residual_t * (x_t - mean(x))`, its variance is
`(sum(u_t²) + sum(u_t * u_(t-1))) / sum((x_t-mean(x))²)²`.
The lag term includes `2 * weight(1) = 2 * 0.5`; no finite-sample correction is
applied. The reported t tests a **zero slope**. It is not a test against UIP's
predicted slope −1; the contradictory +1 comment was corrected.

Six independent full-matrix sandwich cases, with 60/140 monthly observations
and negative/zero/positive error dependence, fail on the old statistic and pass
on the corrected one. The slope, observations, rate convention and mean carry
are unchanged. Constant/short samples remain unreported. The lag-1 choice keeps
the existing intended bandwidth; this is not a general model-selection result.

## M3-N07: a cap/floor with no remaining caplets

A spot-start quarterly cap of three months or less has no unfixed caplet under
the existing rule that drops the first, already fixed period. It previously
returned a normal report with premium 0 and an ATM rate.

The core now raises FICCError before constructing a report when the actual
schedule has no unfixed caplet. The native request also rejects these short
spot-start tenors before loading a curve. Flet receives the same core refusal
through its existing error path. A forward-start three-month cap still has one
caplet and agrees with an independent normal-option formula.

This change preserves the existing cap ATM definition and all valid-caplet
prices. It does **not** close the separate M-04/FC-02 ATM/stub-convention issue,
change Black/normal model bounds or regenerate any stored study/card.

## Validation and remaining scope

`python -B -m unittest tests.ficc_boundary_acceptance -v` covers five tests with
six HAC scenarios, four empty schedules, the valid forward-start case, native
pre-fetch refusal and short/constant-regression cases. Existing Rates adapter
and Black/normal/parity tests also exercise valid paths. The exact PR head is
checked by the bounded Windows/Ubuntu packaging workflow.

Four of 67 canonical §10 groups now have implemented corrections: NEW-M6-01,
NEW-M6-18, M4-N5 and M3-N07. The remaining 63 groups, 14 observation-model entries
and 15 ambiguous source-ID mappings stay open. Gate rules, actual ledgers,
frozen research, holdouts and TRADEGEN are outside this change.
