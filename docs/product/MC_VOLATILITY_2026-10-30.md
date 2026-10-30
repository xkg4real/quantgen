# N-M1-03: identify the volatility being shown

Source: Model 5 / N-M1-03, model-limits register at research ref
`2da6469d8b3d45eab61d682555ff630ce1f564f7`. Product baseline `8ebf75d`.

`MCResult.sigma_annual` is the next-session conditional forecast for GARCH,
but the historical log-return sample standard deviation for GBM, jump and
bootstrap. The generic `Vol (ann.)` tile hid that distinction. The existing
GARCH horizon-average forecast is a third quantity, not total horizon volatility.

Flet now names the primary value `Next-session vol (ann.)` or `Sample vol
(ann.)`, with matching explicit basis in its AI payload. The GARCH diagnostics
name the horizon-average annualized forecast separately. PyQt6 displays the
same named quantities and basis in its result table/notes. Local narrative
identifies next-session rather than “today” volatility and calls the other
models' quantity historical sample log-return volatility. All use the existing
252-session annualization convention; this patch does not fix cross-market
annualization or other model assumptions.

`core/research/mc_disclosure.py` only names existing result values. Simulation,
GARCH fitting, horizon forecasting, prices, seeds and probabilities are unchanged.
The ResearchRun persisted seven-metric schema remains unchanged; extending it
to cover all model diagnostics is a separate unfinished task.

Validation: 4 new focused tests cover actual synthetic results for all four
models, distinct sample/conditional/horizon values, local narrative, actual
Flet tiles/AI payload and native worker/table/notes. The 5 terminal-target
regressions also pass (9 tests in the focused run). Tests block provider requests.

`python -m unittest tests.mc_volatility_acceptance tests.desktop_acceptance.NativeDesktopTests.test_native_volatility_labels_distinguish_sample_and_forecast tests.terminal_target_acceptance tests.desktop_acceptance.NativeDesktopTests.test_terminal_target_label_and_notes_preserve_research_contract -v`

With the same deterministic 300-return synthetic history, sample annualized
volatility is 12.2461%, next-session GARCH forecast is 27.9540% and its 20-session
average forecast is 26.8565%. These distinct values are retained and labeled;
they are not interchanged or recomputed by the display. CI adds the module to
Windows/Ubuntu packaging checks. Actual Windows manual/provider validation
and deployment are not claimed.

Latest queue: 8/67 groups corrected, 59 groups remaining, 14 observation-model
rows and 15 ambiguous mappings still open. Earlier per-PR counts are historical.
