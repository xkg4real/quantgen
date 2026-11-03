# Curve descriptor: 5y5y compounding disclosure

The curve-screen descriptor `5y5y` keeps its existing value and key. It is the
annualized **five-year simple-compounded forward**, calculated as
`(DF(5) / DF(10) - 1) / 5`. It applies one simple accrual over the full five-year
interval. It is neither a semiannually compounded rate nor the forward par swap
rate shown in the separate swap pricer.

For a flat nominal semiannual curve at 4%, this descriptor is approximately
4.3798884%; at 6%, it is approximately 6.8783276%. Converting those full-period
accumulations back to a semiannual equivalent recovers 4% and 6%. A forward par
swap rate instead uses the scheduled fixed-leg annuity and its payment frequency.
These rates must not be compared as though they have the same convention.

The native and Flet curve displays now name the convention and show its formula.
New native exports and optional AI payloads carry an additive
`descriptor_conventions` section; Flet AI payloads carry the same metadata beside
the unchanged numeric `descriptors` mapping. The local curve and weekly narratives,
and the weekly AI instruction, distinguish the simple rate from a forward par
swap rate. English/Korean native display switching does not reprice or mutate the
canonical export. Unknown or historical narrative text is retained verbatim.

This is an M3-N06 disclosure correction. Curve bootstrap, descriptor formula,
swap pricing, parameter schemas, official verdicts and approval conditions remain
unchanged. No new selectable compounding convention or alternate displayed metric
is introduced. Synthetic flat-curve oracles, both display languages, Flet payloads,
native AI preview and JSON/ZIP exports are checked without provider/API calls.
Physical Windows acceptance and external publication are separate evidence.
