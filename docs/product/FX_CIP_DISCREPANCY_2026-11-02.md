# M4-N6: FX forward discrepancy wording

The forward screen previously classified an implied basis below 5bp as
"within noise" and a larger difference as a "real funding premium" attributed
to one currency. Flet also colored the result as an error at that threshold.
Neither classification was supported by aligned quote timestamps, maturities,
rate conventions or an uncertainty estimate.

The English and Korean explanations now describe the existing result as a
signed annualized CIP discrepancy under the input rates. All values have the
same qualification; there is no magnitude-based significance label or error
color. The calculation remains:

```text
F_CIP = S * exp((r_quote - r_base) * T)
basis = ln(F_market / S) / T - (r_quote - r_base)
      = ln(F_market / F_CIP) / T
```

Rates are the existing continuously compounded annual inputs and T is the
existing year fraction. The value is a decimal per year, displayed in signed
basis points. Under the same quote/base convention, a positive value places the
market forward above the input-rate CIP forward; a negative value places it
below. Zero means the supplied inputs coincide with the model calculation;
it does not establish executable market parity. The app has not verified that
quote timestamps, maturities and rate/quote conventions are aligned, so the
difference alone does not establish a funding premium or statistical
significance. Flat rates across tenors remain explicitly disclosed.

Flet retains every existing numeric payload field and adds
`implied_basis_note`, containing the same qualification shown in its local
explanation and tooltip. When no market forward is supplied, the existing
`implied_basis` remains null and this note is null. No difference is inferred.
The native report already retains the canonical explanation and request
inputs; its JSON, ZIP and optional AI preview carry the same qualification.
Switching the display language changes only authored prose and preserves
numeric values and canonical report content.

## Verification and limits

`tests/fx_basis_disclosure_acceptance.py` covers no supplied forward, zero,
and ±4.9, ±5 and ±12bp. It checks the analytic result and sign, identical
English/Korean numeric tokens, actual native language changes, canonical
JSON/ZIP and AI-preview payloads, and the actual Flet analysis-panel boundary
with its remote analysis function replaced by a local test double. Existing
FX language and SABR acceptance suites remain applicable.

All data and responses are synthetic. This change does not validate provider
quotes, identify funding causes, run a live API request or pilot, alter a
pricing formula, change a research threshold, or promote the report's
`NOT_RUN` official verdict. Linux offscreen GUI tests do not replace owner
Windows execution verification. The parent task tracks website handoff and
publication separately; this source change does not assert deployment.
