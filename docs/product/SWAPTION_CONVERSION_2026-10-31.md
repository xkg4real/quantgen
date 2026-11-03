# M3-N04: unavailable comparison volatility must not discard a price

Source: Model65 of the model limits register on research commit
`2da6469d8b3d45eab61d682555ff630ce1f564f7`. Reproduced on product
`1180414`: a 10y×10y normal receiver with 1% curve, 0.1% strike and
100bp volatility fails cross-model inversion; 1y×5y deep ITM/OTM cases
with very small normal or Black volatility fail at the intrinsic boundary.
The primary price is valid, but its optional comparison used to abort the report.

`price_swaption` now retains the primary-model price and Greeks when the
comparison inversion refuses its domain or fails numerically. Only that
auxiliary call is caught. Invalid primary inputs still raise. Non-positive
forward/strike prevents Black comparison, as before, with a precise explanation.
The comparison is `UNAVAILABLE`, with NaN internally and null in serialized
payloads; it is never replaced by zero or an approximate implied volatility.
Flet and PyQt6 display the primary result and the reason, and AI/export data
carry the same distinction. Successful comparisons remain `COMPUTED`.

This does not extend the inversion domain or claim that an unavailable
cross-model volatility exists. The Black/Bachelier formulas, brackets,
intrinsic tolerances and rejection behavior of the public inversion helpers
are unchanged. Research gates, stored studies and actual ledgers are untouched.

Validation: 11 focused/UI/export/boundary tests pass; three existing pricing,
put-call parity and rejection checks pass. An independent normal-price formula
checks the high-price failure case. All existing report fields match exactly
in 24 ordinary baseline scenarios. Every other swaps function is AST-identical.
Windows CI uses offscreen widgets; live quotes and manual Windows acceptance
remain NOT_RUN.
