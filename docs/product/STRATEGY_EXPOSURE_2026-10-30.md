# N1: per-asset allocation and portfolio exposure

Source: Model26 and Model30 in `MODEL_LIMITS_REGISTER_2026-10-28.md`
on research commit `2da6469d8b3d45eab61d682555ff630ce1f564f7`.
The product comparison base is main `6bd4a208`. No stored study/card,
protected cache, actual ledger or holdout was read or regenerated.

## Result and scope

Strategy Lab's volatility target caps **each asset** at 1; crypto trend holds
0 or 1 **per asset**. Neither divides by N or limits portfolio gross to 1.
Both are single-asset rules. Multiple symbols produce an unnormalized sum
of sleeves, not a portfolio volatility target. The shared family labels,
pre-run help, Flet/PyQt6 results, AI payload/narrative and native JSON/ZIP
reports now state this scope.

The disclosure reports theoretical total upper bound, mean/max **OOS held
gross exposure**, and maximum borrowing as a multiple of equity. It uses
the configuration selected at each walk-forward origin, including embargo
and the final partial block. Return date i uses weight row i (held from
price i to price i+1); it never reports full-sample or final-winner exposure
as the stitched OOS result.

Cash is `1-sum(weights)` for these long-only rules. Negative cash borrows at
the existing Lab assumption of 3%/252 per session. The existing benchmark
is the arithmetic mean of daily asset returns: 1× equal-weight, **not
exposure-matched**. This patch discloses that comparison, not a leverage
or covariance normalization change.

N1 covers both families. The crypto grid duplication (N2), annualization,
registration timing, cumulative DSR trial counting and historical study
verdicts are separate open issues. Technical/owner approval boundaries and
O8/O11 pilot requirements remain unchanged.

## Necessary browser rendering correction

The real Flet result test initially failed: 322 OOS dates versus 323 equity
points. `equity_curve` includes initial wealth 1. The caller now prepends
the preceding price date for that initial point, without dropping returns
or changing equity. This is a narrow Strategy Lab rendering fix, not closure
of the entire historical functional-completeness audit.

## Verification

- Six focused tests: independent origin/embargo/held-row oracle; actual
  vol-target and crypto generators with one/four assets; independent P&L
  including borrowing/turnover and benchmark oracle; cost sensitivity
  withholding; actual Flet chart/notices/AI payload; native JSON/ZIP/clear.
- The four-asset low-volatility/uptrend fixture reaches gross 4× and
  borrowing 3×, while the single-asset fixture reaches gross 1×/borrowing 0.
- Five existing native Strategy Lab regressions pass, including all seven
  families, failed registration, gate restoration and withheld verdicts.
- Four before/after synthetic runs against exact main6bd4a208 match all
  existing score fields, WF arrays/choices, equities, grid, costs and trial
  counts exactly. `strategies.py`, `validate.py` and `gate_ledger.py` are
  byte-identical. No objective, weight generator, cost, gate or ledger
  logic changed.

These tests use synthetic/injected inputs and offscreen widgets. They do
not establish actual Windows visual/DPI or provider acceptance.
The queue becomes 9/67 corrected groups, 58 remaining, with 14 observation
model rows and 15 ambiguous ID mappings still open.
