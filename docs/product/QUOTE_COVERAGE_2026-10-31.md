# Option quote-check coverage (M4-N12)

After hours, the option board can retain last prints but have no usable
two-sided quotes. Previously static checks returned zero violation counts with
zero tested strikes; Flet rendered a green zero and the narrative said parity
held on `nan%` of strikes. One or two strikes also cannot support a butterfly
inequality, even though the same zero count was displayed.

The engine's existing counts and numerical decisions are unchanged. A shared
presentation layer now records the number of performed adjacent-pair (vertical)
and adjacent-triple (butterfly) checks separately for calls and puts. Untested
counts are null/NOT_RUN in the public payload and reports. If only one side
supports butterfly checks, the summary is PARTIAL; a zero there is neutral.
Parity reports its eligible spread-test denominator, or NOT_RUN when it is zero.

Flet, PyQt6, local narrative, AI input and JSON/HTML exports carry the same
coverage. The UI labels these as quoted-mid quality checks, not a proof of
tradable arbitrage or an official study verdict. The fitted SVI surface's
separate convexity diagnostic is unchanged.

Source: research Model88 (M4-11), `MODEL_LIMITS_REGISTER_2026-10-28.md` at
`2da6469d8b3d45eab61d682555ff630ce1f564f7`.

Validation: 19 focused/regression tests pass. Cases cover 0/1/2/3 eligible
strikes, one-sided coverage, moneyness exclusion, unequal strike spacing with
an injected butterfly violation, injected vertical violations, valid and empty
parity samples, full last-print workflow, actual Flet colors/payload and Qt
table/export status. The two full synthetic board scenarios retain all 3,579
existing values/arrays exactly against main `d4670f3`; equity_deriv engine
source is byte-identical. New checks are included in Windows/Linux CI.

No actual provider request, Windows manual acceptance, stored study/card,
formal ledger or research criterion was changed or run. The tests do not
validate live quotes, trading execution or new arbitrage detection methods.
