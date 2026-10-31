# M4-N8: solver convergence is not a fit-quality verdict

Source: Model81 of the model limits register on research commit
`2da6469d8b3d45eab61d682555ff630ce1f564f7`. Product baseline `94659fd`.
Synthetic EURUSD spot1.1, domestic3%, foreign2%, ATM8% reproduces:
6m RR0.5vp/BF−0.1vp and RR4vp/BF0.3vp reach rho's upper bound;
1/52-year RR−3vp/BF2vp reaches nu=5 with RMSE0.766508 vol points.
All report optimizer success. Historical audit results are separate evidence.

`SABRFit.active_bounds` now carries the selected SciPy result's `active_mask`;
this is the solver's existing tolerance, not an invented near-bound threshold.
SciPy versions can stop just inside a bound without marking it active. Exact
parameter values, existing solver limits and distances to those limits are
therefore exposed independently of that flag. No near-bound verdict is invented.
Legacy constructed fits without this metadata say "not reported", not "none".
The shared diagnostic computes quoted/fitted volatility and signed residuals
in vol points (100×volatility units), their RMSE and maximum absolute value.
It identifies whether the priced strike lies outside the actual quote range.
Missing quote evidence is NOT_RUN with null residual statistics, not zero.

Flet, PyQt6, commentary, AI input and native JSON/HTML exports expose the same
evidence. Solver success alone uses neutral styling. Active bounds, solver
failure and extrapolation are explicitly called out. Three quotes fit three
free parameters with beta fixed: a small in-sample residual does not validate
the smile elsewhere. Independent validation and arbitrage validation stay
NOT_RUN. Hagan wings/long expiries are not claimed to be validated. There is
no new numerical quality cutoff or formal approval rule.

Hagan/Garman-Kohlhagen formulas, objective, six starts, solver selection,
bounds and pricing/Greek calculations remain unchanged. Baseline comparison
checks 904 existing fields across four fits and40 call/put reports exactly.
All other FX functions are AST-identical. Focused synthetic/offscreen tests
cover bounded successful fits, unsuccessful metadata, missing quotes, range
endpoints/extrapolation, Flet payloads and native tables/JSON/HTML; existing
delta/smile/SABR pricing checks also pass. Live provider, independent study,
manual Windows and arbitrage validation remain outside this correction.
