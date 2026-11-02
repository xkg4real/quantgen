# Strategy interpretation and ADF compatibility — 2026-11-02

The live Strategy Lab now displays the assumptions behind its existing numbers
in native and Flet results, exported native reports and optional AI payloads.
Native authored notices have English and Korean variants. The calculation,
stored evidence and official decision are preserved.

| Finding | Implemented behavior | Scope |
| --- | --- | --- |
| N6 | Describes long/short pair weights as gross-normalized regression weights. Net exposure is generally nonzero; a negative hedge ratio can put both legs in the same direction. | Current function description and product interpretation corrected; weights unchanged. |
| N9 | Labels the high/low volatility split as retrospective: trailing volatility is compared with the whole-OOS median, which is unavailable at the historical observation time. | Current function description, result, report and AI interpretation corrected; split values unchanged. |
| N10 | Explicitly opts into the ADF result object where the installed statsmodels API supports it; retains the tuple contract on older supported versions. | Compatibility correction; identical ADF specification and p-values. No warning suppression or dependency-version change. |
| N3/a | States the fixed 3%/252 cash assumption, negative-cash borrowing, 252-session annualization and that Sharpe does not subtract a risk-free return. | Disclosure only. Historical rate curves and cash sensitivity validation remain open. |
| N14/a | Distinguishes zero cash rate in the momentum sign signal from the fixed 3% cash rate in P&L. Does not claim an exact historical excess-return reproduction of MOP. | Disclosure only. Signal definitions and model-adoption decisions are unchanged. |
| N5/a | Clearly separates ordinary residual-ADF rejection shares from an Engle–Granger cointegration test. Identifiable historical pair cards receive a separate reading note; their original text, statistics and decision remain intact. | Disclosure only. Formal cointegration diagnostics, historical validation and research decisions remain open. |

The historical compatibility field `share_cointegrated` retains its calculation
and name, with a docstring identifying it as an ordinary residual-ADF rejection
share. It is not converted into a new validation result. No historical card is
rewritten or regenerated. The whole N3, N5 and N14 groups remain incomplete.

N4 walk-forward switch-cost accounting and N17 scoring-rule changes are outside
this change. No stored grade, preregistered threshold, trial count, official
ledger, research approval, frozen study or holdout is modified or executed.

## Validation

- New core/Flet and native acceptance: 12 tests. Existing exposure regressions:
  6 tests. All use synthetic inputs, injected cards and isolated application
  state, with network/real-card/ledger access blocked.
- Six installed-library ADF cases match the previous p-values exactly and emit
  no return-contract FutureWarning. Separate legacy-tuple and new-object API
  tests preserve the AIC/intercept specification and missing-result behavior.
- Positive and negative pair-hedge-ratio cases use an independent net/gross
  exposure oracle. Adding future high-volatility observations reproduces the
  retrospective reclassification described by N9.
- Native EN/KO switching, Flet notices, canonical JSON/ZIP, optional AI payloads,
  cost-based verdict withholding and historical card immutability are checked.
- A separate pre-change comparison against `8b401043` preserves all pair weight
  arrays and diagnostic values across 12 synthetic panels (600 rows each,
  formation/trading/entry and long-only variants). All other calculation ASTs
  in `strategies.py` and `validate.py` are unchanged after docstrings are removed.

Run the focused suites in the configured isolated test environment:

```bash
python -m unittest tests.strategy_assumptions_acceptance tests.desktop_strategy_assumptions_acceptance tests.strategy_exposure_acceptance tests.desktop_strategy_exposure_acceptance
```

These are cloud synthetic and offscreen checks. They are not actual Windows
manual acceptance, provider verification, live API success or research execution.
