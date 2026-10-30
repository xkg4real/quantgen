# LETF variance proxy and historical study scope — M4-N2 / NEW-M6-08

The ETF screen called the AZ formula evaluated at prior-quarter variance the
study's better reference. The historical study's comparator was actual prior-
quarter fund-versus-index realised log drag: these are different quantities.
The study concerns 122630 and cannot validate the current input fund or sample.
Source: MODEL_LIMITS_REGISTER_2026-10-28 Model95 at research ref2da6469.

The shared workflow, Flet, PyQt6, AI payload and JSON/ZIP now distinguish the
variance-based proxy from observed realised drag. Historical study decisions are
preserved, explicitly scoped to historical122630 and not promoted to a current
validation. The current proxy status is NOT_RUN. The unsupported better-guide
claim and README implication are removed; the recorded status snapshot is refreshed.

No formula, fund selection, rate, fee, dividend, index mapping or numerical output
changes. Both UI explanations expose current rate=0, fee=.64% and omitted dividends.
M4-N1 (KOSDAQ index mapping), M4-N3 (funding/dividend assumptions), M4-N10 (historical
index proxy), real-market validation and stored research records remain separate.
This closes only the misleading study-reference/display issue, not the LETF model.

Validation:
- Compare all existing result fields for five synthetic funds with the exact
  pre-change39d92ef workflow: identical arrays, numbers and stored decision fields.
- Independent constant-variance AZ formula agrees with all five prior-quarter proxies.
- Actual Flet text/AI payload and native JSON/ZIP preserve the scope and NOT_RUN state.
- Engine sources equity_deriv, GARCH, strategies, validation and ledger unchanged.
- Focused3 + native AR1/market regression13 = 16 passed; no market/provider/card-store,
  .env, protected cache, actual ledger, frozen or holdout access.

```sh
python -m unittest tests.letf_disclosure_acceptance tests.desktop_letf_disclosure_acceptance tests.desktop_ar1_decay_acceptance tests.desktop_market_acceptance -v
python -m tools.status.snapshot --check
```

Queue:11/67 canonical groups complete;56 remain, including partial NEW-M6-02.
The alias NEW-M6-08 counts once with M4-N2. Observation14 rows and ambiguous15
mappings are unchanged. Windows manual/live-provider acceptance is not established.
