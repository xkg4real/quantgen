# Portfolio warnings and constraint scope — N-M1-09 / N-M1-10

The source is Model 23 in `docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md`
at research ref `2da6469d8b3d45eab61d682555ff630ce1f564f7`, cross-referenced by
the same ref's known-errors register §10. Product baseline: `ff421ea7`.
This closes the missing disclosure in these two entries, not a model redesign.

## Behavior

- Max-Sharpe warns when no asset has positive estimated excess return. In the
  documented negative-return basket, the solver still picks the 40%-volatility
  asset with Sharpe −0.20. The warning explains why maximizing non-positive
  Sharpe can favor volatility. Convergence failure remains a separate warning.
- Each result carries its requested and effective per-asset cap. The existing
  feasibility formula `min(max(requested, 1/N + 1e-9), 1)` is unchanged.
  A requested cap below that bound is explicitly disclosed as adjusted.
- Only the selected objective uses the user's cap. Other objective rows,
  the frontier curve and random cloud retain a 100% per-asset bound. All remain
  long-only and fully invested; equal weight remains fixed at 1/N.
- Flet and PyQt6 display the per-row cap and selected/comparison role, as well
  as the frontier's separate constraint scope. Max-Sharpe warnings are visible
  even when that objective is a comparison row.
- Flet's local narrative and AI payload, plus native JSON/ZIP and explicit AI
  report input, include the same scope and notes. No automatic AI call is added.
  Native exports retain `verdict=NOT_RUN` and `reproducibility=PARTIAL`.

## Validation

`python -m unittest tests.portfolio_scope_acceptance tests.desktop_portfolio_scope_acceptance tests.desktop_acceptance.AnalysisAdapterTests.test_portfolio_adapter_preserves_solver_comparisons_and_warnings -v`

Eight focused tests use analytic baskets, injected histories, Flet controls,
offscreen Qt and in-memory report exports. They cover negative/zero excess
returns, a nonconverged solve, analytic min-vol/risk-parity/equal weights,
each selected objective's actual cap, infeasible-cap adjustment, Flet's actual
payload, and native rows/JSON/ZIP/clear behavior. Network requests are blocked.

A separate bounded comparison against the baseline optimizer checks all four
objectives, caps 0.1/0.5/1.0 and positive/negative expected excess-return baskets
(24 cases): weights, risk contributions, return, volatility, Sharpe and
convergence match exactly. `_solve`, `efficient_frontier` and every R-15 function
are unchanged by AST comparison. CI adds the focused modules to existing
Windows/Ubuntu runtime packaging checks; its actual run result is recorded in
the PR and handoff ledger, rather than presumed here.

These checks do not validate live providers, actual Windows display/DPI,
future performance, formal research gates or deployment. M-02's log-return
convention, other model limitations and the full §10 backlog remain open.
The queue now records 6 of 67 canonical groups corrected; 61 groups and
14 observation-model rows remain, including 15 ambiguous ID mappings.
