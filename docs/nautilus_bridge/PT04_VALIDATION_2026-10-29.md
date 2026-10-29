# PT-04 partial FRED coverage — ②-5/c

A curve ending at 10 years previously reported the 10-year minus 5-year spread as
5s30s and could extrapolate a price beyond the observed long end. Partial FRED
curves now carry an explicit observed maturity bound through bootstrap, NS/NSS
fits and shocks. Long-end descriptors display n/a; out-of-coverage pricing refuses
with FICCError. Rates tables/charts and explanation payloads withhold missing values
(JSON null). The data-provider note identifies missing tenors.

Validation on Linux/Python 3.12: 6 focused fixture tests PASS; existing FICC 57 and
Bonds 33 checks PASS (96 total, 0 FAIL). Tests used synthetic inputs; network,
.env, protected cache, holdout and actual-ledger access were blocked. Against
parent e1271a71d45d5b8b7da095d427b526a5f051349f, complete FRED and synthetic
curve descriptors, changes and zero rates were exactly equal. The partial fixture
previously gave a plausible 5s30s of 0.0014285714285714249; it now gives n/a.

No full suite, provider request, Windows run or production deployment was performed.
No frozen harness, statistical gate or cost assumption was changed. Other ②-5
queue items remain separate. Run the focused tests with dotenv disabled and the
project's protected-path guard; never run tests/run_all.py on the source checkout.
