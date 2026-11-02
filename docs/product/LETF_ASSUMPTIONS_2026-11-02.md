# LETF funding and dividend assumptions

The ETF analysis keeps its previous numbers as **ZERO_RATE_REFERENCE**: annual
funding rate zero, dividends omitted, and the existing fixed fee assumption.
This reference does not claim current market funding, verified fund expenses,
or observed fund/index tracking performance.

A separate user scenario requires an explicit annual funding rate and annual
fee plus a return comparison. The UI accepts percentages; the request and
calculation use annual **continuous decimal rates**, with time equal to trading
sessions divided by252. Negative funding rates are permitted. Fees and dividend
yields must be nonnegative and all inputs must be finite. A blank is not zero.

- **Total-return comparison:** distributions are already included in the
  comparison asset. An additional dividend yield is rejected to prevent double
  counting.
- **Price-return comparison:** the user must enter an explicit dividend yield,
  including an explicit zero when that is the intended assumption. The ideal
  self-financing model adds the signed contribution `beta * q * T`.

For leverage beta, integrated daily variance V, funding rate r, annual fee f
and time T, the log-return difference relative to beta times the selected
comparison return is:

```text
variance contribution = (beta - beta²) * V / 2
funding contribution  = (1 - beta) * r * T
fee contribution      = -f * T
dividend contribution = beta * q * T  [price return only; zero for total return]
```

Positive funding rates can produce a positive funding contribution for an
inverse scenario. A negative total is therefore not assumed. The formula is a
conditional model calculation, not a real-fund financing model or a holding
recommendation. The mapped index remains the variance input; selecting a
comparison does not establish that index as the fund's actual futures or
distribution benchmark.

Results and AI/export payloads keep the input values, conventions, user-assumed
provenance, separate variance/funding/fee/dividend contributions and the unchanged
zero-rate reference alongside the scenario. Missing index history remains
NOT_RUN; a scenario never creates market history or changes stored study cards,
research decisions, ledgers or the historical122630 study.

Synthetic verification includes beta2/-1/-2 at63 sessions,20% annual volatility,
funding3.21% and fee0.64%: funding contributions are respectively -80.25,
+160.50 and +240.75bp; the fee contributes -16bp. A deterministic self-financing
wealth calculation checks both return conventions independently.

```text
python -B -m unittest tests.letf_assumptions_acceptance tests.letf_disclosure_acceptance tests.letf_index_acceptance -v
```

These are synthetic/injected product checks. Live market assumptions,
provider verification and historical research-card evaluation remain outside
this change.
