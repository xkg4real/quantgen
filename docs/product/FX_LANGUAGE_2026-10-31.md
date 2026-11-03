# Native FX narrative localization — 13-8/b1

The global language selector from PR39 now also switches the authored forward,
option and SABR diagnostic prose in the native FX pane. Korean summaries retain
the original precision, signs, quoted units, rate/basis branches and caveats.
Solver state, active bounds, missing residuals, extrapolation scope and both
independent/arbitrage `NOT_RUN` states remain visible. No pricing, calibration,
threshold, formal verdict or authorization logic is changed.

`fx_narrative.py` reads existing output fields and uses the same display number
formatters as the English narrative. The UI stores an explicit Korean display
variant alongside the canonical English source. Switching back restores the
exact source; JSON/HTML report sections continue to contain the original. A
replacement source message discards its old display variant to avoid stale text.
FX field/metric captions and the ATM/delta-strike explanation are also localized.

Six focused tests cover forward carry/basis branches, call/put/wing cases,
unreported bounds and missing residuals, every rendered numeric token, repeated
language switching with unchanged export evidence, stale-message replacement and
explicit fallback for unsupported tools. Tests use synthetic inputs and injected
providers only. The language/SABR/desktop suites provide integration coverage;
the runtime matrix includes Windows Python 3.12/3.14 and Ubuntu Python 3.12.

The parent 13-8 remains incomplete: carry-basket, rates/bonds/portfolio and other
model-specific narratives, raw provider notes, stored records and external AI
responses still retain source language. Interactive Windows/DPI validation is
NOT_RUN. Flet and the public site are not changed by this native display patch.
UI-to-website records for merged PR38 and PR39 are included; supported cross-chat
delivery is unavailable, so their delivery status remains queued.
