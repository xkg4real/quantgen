# Consistent parameters for rate-horizon revaluation

Previously, `horizon_pv_distribution(params, sim, ...)` ignored its `params`
argument. A caller could supply changed rate-model settings and receive results
calculated from the original simulation without an error.

Revaluation now requires the same `model`, `kappa`, `theta`, `sigma`, and `r0`
as `sim.params`. A mismatch raises `ValueError` before curve/path pricing and
names the differing fields. Descriptive `note` text is excluded from the check.
The comparison is exact: even a small numerical setting change requires a new
simulation, rather than silently reusing paths generated with another setting.

The native Rates service, Flet simulation page, and existing self-checks pass
the final `sim.params`. This matters for Hull–White: simulation sets `r0` to
the input curve's initial instantaneous forward rate. The calibrated input
`r0` can therefore differ legitimately from the final simulation value.

For identical calculation parameters, pricing, path selection, horizon loss
definition, percentile/CVaR calculation and zero clipping are unchanged. This
change does not introduce alternative-parameter repricing of existing paths.
To study changed settings, regenerate the simulation and use its final params.

`tests/rates_revaluation_params_acceptance.py` covers each parameter mismatch,
an adjacent representable float, note-only changes, recorded synthetic PV and
risk numbers, Hull–White normalization with/default curves, and native-service
versus Flet display/AI-payload parity for all three models and both instruments.
Tests use synthetic inputs and block network/provider calls.

Validation on 2026-11-02: all five new acceptance tests and five existing
focused ratesim/horizon-PV acceptance checks passed. Against pre-change commit
`0169c98`, twelve synthetic terminal arrays, twenty-four revaluation PV arrays,
and 144 summary values/notes matched exactly. The comparison spans Vasicek,
CIR and Hull–White, explicit/default curves, two horizons, and bond/swap values.

Run the new checks from the checkout with its development dependencies:

```sh
python -m unittest discover -s tests -p rates_revaluation_params_acceptance.py -v
```

This is a product API consistency fix. It changes no research decision rule,
execution approval, official ledger, holdout, or frozen artifact. Synthetic
service/Flet checks are not Windows execution evidence or website deployment.
Browser applicability: the Flet Rates simulation uses the same final-parameter
contract; the website workspace should review any independent revaluation caller.
