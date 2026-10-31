# Native carry-basket language — 13-8/b2/a

The Windows/PyQt6 carry pane now switches its authored ranking, costed-backtest
summary, latest long/short positions, stale-rate warning and captions between
English and Korean. The known engine disclosure also explains aligned rates,
one-observation lag of monthly averages, accrual, no lookahead and top-N clipping
in Korean. A full-string match protects unknown/extended source notes: they
remain verbatim. Provider notes, raw table values and currency/pair IDs remain
source evidence.

This is display-only. Existing core calculations, weights, costs, signals,
benchmark and source narrative are unchanged. English restores the exact source;
JSON/HTML report data remain canonical. Six focused regressions use injected
synthetic histories and compare all displayed numeric tokens with the existing
English narrative, stale/missing dates, negative scores, clipped/unclipped top-N,
empty/missing evidence, unknown notes, repeated language switches, table values,
equity arrays and report contents. The runtime CI matrix runs them alongside the
existing native language, FX and desktop tests on Windows 3.12/3.14 and Ubuntu
3.12. Interactive Windows/DPI acceptance is NOT_RUN.

13-8/b2 and 13-8 remain incomplete: rates, bonds, portfolio and other model
narratives need separate coverage. External AI/provider prose is not silently
translated. This patch does not change Flet or deploy the public website.

The separate UI-session draft PR42 changes common localization and report
formatting. It must preserve the explicit localized variants, exact source
restoration and canonical reports established by PR39/40 and this patch when
integrating. This patch does not edit that draft or its shared controller files.
Its UI session supplement belongs in the consolidated Claude handoff.
