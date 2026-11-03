# Windows desktop language consistency — 13-8/a

The native PyQt6 app previously mixed fixed Korean and English UI strings and
had no application-wide language selector. This change adds **Language / 언어**
below the theme selector, with English and 한국어 options. The default is English.
The executable entry point remembers the choice with Qt's application settings
(`QUANTGEN/QUANTGEN`, key `ui/language`) and restores it at the next launch.
This does not modify connection settings or environment variables.

## Completed implementation scope

- Navigation, headings, tabs, form labels, accessible names, placeholders,
  authored notices, supported dynamic execution/save messages and table headers.
- Explicit metric-caption columns and the Home/Markets indicator names,
  including the US 10-year yield label that was still Korean in English mode.
- Chart empty states, supported legends and axis descriptions; text space is
  recalculated with the existing font-metric layout after switching.
- App-authored save/confirmation dialog titles and supported prompts.
- Language switching without rebuilding forms, starting jobs, reading paper
  stores, changing input values or losing completed results.

`translations.py` matches complete authored messages or named templates, with
line-by-line handling for compound notices. Unknown source text stays unchanged.
`localization.py` retains source text separately from the displayed text and
coalesces Qt layout/model notifications for newly created result widgets.
Combination-box item data stays canonical; ordinary table cells are excluded.
Only columns explicitly tagged as captions are translated. Model/provider
identifiers, tickers, numeric values, order IDs and formal status codes remain
unchanged. No translation API or external AI call is made.

Portfolio and bond report generation uses retained source notes instead of the
translated label text. ToolPane sections and report data remain canonical. The
source-language notice is display-only and is not appended to exported sections.
No calculation, calibration, research gate, rule/confirmation state or execution
authorization is changed. The Flet browser is retained unchanged by this PR.

## Validation

Seven new offscreen tests cover initial chrome, repeated switching with preserved
inputs/request/item data, late FX results/metric captions/chart legends, isolated
settings/restart, window isolation/late controls, unknown source text/order IDs,
and portfolio/bond report preservation. The existing desktop integration and
chart-rendering suites also pass: **33 tests on the final local code**.
The runtime CI includes the new tests on Windows Python 3.12/3.14 and Ubuntu 3.12.
Actual interactive Windows installation/DPI acceptance remains **NOT_RUN**.

Manual reproduction on a Windows installation built from this source:

1. Launch the native app; choose English, then 한국어 in the sidebar.
2. Open Markets → FX, change an input and switch languages again. Verify that
   the input and selected tool/source remain unchanged.
3. Run only the synthetic demo and inspect the metric headings, captions and
   status. Switch after completion; values and export evidence must not change.
4. Close normally and reopen; the selected language must be restored.

## Remaining scope — 13-8/b, parent remains incomplete

Long model-specific research narratives, provider notes, stored records, raw
rule summaries and external AI responses retain their source language. The
result view identifies the analysis narrative as original-source text. Further
authored narrative/diagnostic vocabulary coverage is a separate pending subtask;
this PR does not claim complete bilingual coverage of every model/result.
Native operating-system dialog controls may follow the OS language. Flet has
no new language selector in this change. No update to a user's existing local
installation or public-site deployment has been performed.
