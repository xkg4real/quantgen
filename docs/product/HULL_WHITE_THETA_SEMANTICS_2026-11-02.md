# Hull–White parameter display

Hull–White simulation uses the time-dependent drift fitted from the input
curve. The stored `theta` from historical regression does not enter that drift.
Calling it the simulated long-run mean was misleading.

The native Rates view and Flet simulation now identify this value as a
regression mean unused by Hull–White drift. Native English/Korean text and
both authored narratives explain its role. Native reports/AI previews and
Flet AI payloads retain the value with explicit `role` and
`used_by_simulation: false` metadata. Vasicek/CIR retain their existing theta
display and use it as a long-run mean.

No calibration, simulation, pricing or loss calculation changes. Old saved
reports are not rewritten. Synthetic acceptance checks cover path invariance,
both native display languages, canonical report preservation, AI-preview
metadata and Flet labels/payloads. They do not establish live Windows execution,
external AI quality or website deployment.

Validation: three new semantics checks and thirteen existing rates-language
and revaluation checks passed. Changing only the unused Hull–White theta in a
synthetic simulation left terminal paths, every fan percentile and the horizon
curve exactly unchanged. `core/ficc/ratesim.py` is unchanged by this correction.
