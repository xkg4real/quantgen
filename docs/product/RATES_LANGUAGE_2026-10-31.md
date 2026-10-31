# Native Rates result prose — 13-8/b2/b

Korean display variants now cover the authored result paragraphs for yield
curves/PCA, pay/receive swaps, Bachelier/Black swaptions, caps/floors and
Vasicek/CIR/Hull-White simulations with optional horizon valuation. The existing
English number formatters preserve units, precision and signs. Classification
names describe the existing result; no curve fitting, pricing, simulation,
threshold or approval rule is changed.

Synthetic-curve disclosure, conditional carry/roll language, missing PCA,
unavailable auxiliary volatility, optional threshold probability and horizon
valuation remain conditional on their original evidence. Engine/provider notes,
contract labels, unit identifiers and unknown classification names remain verbatim.
Those source notes and other inline messages are still separate translation scope.

Eight regression methods cover all curve fits, payer/receiver and fixed/par swaps,
both option models and instrument types, unavailable conversion, all simulation
models, missing evidence and repeated display switches with unchanged report
sections. They use synthetic inputs and injected providers only. The runtime CI
matrix runs these on Windows 3.12/3.14 and Ubuntu 3.12. Actual Windows/DPI review is
NOT_RUN. English restores the exact canonical source; saved reports remain source
evidence, not translated replacement records.

Parent 13-8/b2 remains incomplete: Bonds/Portfolio and other model prose, original
notes, remaining inline captions and manual acceptance are separate work. The
public website and Flet are unchanged. Draft PR42's separate common-localization
work must retain this explicit display variant and source/report separation.
