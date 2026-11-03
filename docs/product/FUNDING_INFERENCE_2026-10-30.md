# Funding inference safeguard — NEW-M6-02/a

The old event study treated overlapping 30-observation returns and clustered
funding-decile events as IID. Its bootstrap sign frequency was shown as a p-value
and alongside a historical green PASS. This change retires that statistic and
exposes a separate, explicitly conditional exploratory diagnostic.

## Current behavior

- Carry, historical percentile, event means and full-sample decile selection are
  unchanged. These are retrospective descriptions, not prospective signals.
- `FundingCarry.bootstrap_p` remains in its positional/API slot but is always
  NaN; AI/JSON export uses null with `RETIRED_INVALID_IID`. It is **not** an alias
  for a new p-value. `seed` remains accepted but exhaustive enumeration is deterministic.
- For n eligible ordered pairs, let w[t]=top[t]/n_top-bottom[t]/n_bottom and
  D[k]=sum(w[(t-k) mod n]*return[t]). Enumerate all n relative cyclic alignments,
  including k=0. The lower-tail probability is count(D[k] <= D[0])/n; ties use
  a conservative floating-point tolerance. FFT implements this enumeration.
- Each series' cyclic order, event clustering and overlapping-return dependence
  are preserved. The null assumes independent series with equiprobable relative
  cyclic phase. **Ordinary stationarity or zero correlation alone is insufficient.**
  Structural breaks, trends, wraparound and few effective episodes limit its
  interpretation. No automatic PASS/REJECT threshold is attached.
- Constant/tied overlapping groups, <=10 observations in either group, constant
  returns or missing calendar days make the diagnostic unavailable. Nonfinite
  funding/prices, nonpositive prices and invalid integer windows are rejected.
- Flet, PyQt6, AI and native JSON/ZIP include the method, limitations and sample
  counts. A historical funding card retains its stored decision, with a neutral
  historical/not-revalidated display. README no longer asserts BIS confirmation.

## Evidence

`python -m tools.status.funding_null_probe --repetitions 300` uses only synthetic
730-day histories: independently generated BTC log increments and funding AR(1)
phi=.98, burn-in1000, simulation seeds60000..60299. Both use trailing7 and forward30.
The old IID2000-resample algorithm uses seed3 per history. The fraction below.05
is **117/300 = .3900** for old IID and **13/300 = .04333** for circular phase.
This is a finite, single-scenario stress probe, not universal calibration or a
re-run of the historical audit's .373 figure. Production has no significance gate.

The direct rolling oracle matches FFT on two sample lengths including ties.
Exhausting every possible relative phase of a fixed synthetic pair controls
rejection at .01/.05/.1 under the *stated uniform-phase null*. This is distinct
from assuming that null applies to market data.

Focused+regression command (23 checks):

```sh
python -m unittest tests.funding_inference_acceptance tests.desktop_funding_inference_acceptance tests.crypto_hac_acceptance tests.ai_payload_acceptance tests.desktop_market_acceptance -v
```

Tests cover unchanged descriptive means/carry, seed independence, invalid/missing
inputs, actual Flet payload/historical-card display, Qt JSON/ZIP and clear behavior.
Other crypto functions' ASTs and validation/ledger source bytes are unchanged.
No market data, protected cache, .env, actual ledger or frozen study was opened.

## Scope still open

NEW-M6-02 is **partial**, not a completed canonical group. Historical M_C4 cards,
registered study code, official gates and owner approval rules are unchanged and
were not rerun. Before historical or real-market inference can be confirmed,
a separately reviewed validation design must address phase assumptions, structural
breaks, forward-only thresholds and effective event counts. An exploratory p-value
must not be wired into the old gate. No claim of general block-bootstrap correction,
Windows manual acceptance, live-provider acceptance or model approval is made.
