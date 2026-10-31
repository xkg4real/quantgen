# UI implementation and handoff — 2026-10-31

Source PR: https://github.com/xkg4real/quantgen/pull/42
Branch: `gpt/indicator-guide-20261031`. Read the actual PR head and checks for the
current merge/CI state; this document is versioned with the implementation.

The owner requires app UI work to continue in the UI session. Website work for
**https://quantgeneration.com/** belongs to **웹사이트 작업공간(AWS)**, whose
existing authentication should be used there. Do not start a new AWS login in
this session. Include this UI work in the main session's Claude handoff.

## Implemented app work

- Home technical-indicator guide with visible multi-select SMA, EMA, RSI, MACD
  and Bollinger choices, one common historical instrument/period, price overlays
  and separate aligned RSI/MACD panels. Signals uses the same component on its
  actual loaded history. No substituted educational data enters research results.
- Selection letters/colours, solid/dashed line conventions, mouse/keyboard/slider
  reading, same-date interpretation, four-part explanations, selection reasons,
  limitations and explicit hindsight counterexamples. Reports save locally on
  request with canonical education metadata and a checksum manifest.
- 1,247 attributed USD/EUR reference observations from 2018–2022, checksum-pinned
  to a source revision. DEXUSEU reciprocal/four-decimal rounding is explicit;
  observed OHLCV is absent and never fabricated.
- Six Home plus 73 registered-series usage review with 13 provider policies and
  source links. Classification is a review status, not legal/publication approval.
- Per-window/page locale structure, Korean/English catalogues and explicit English
  fallback for other regional choices. 714 CLDR formats do not mean 714 translated
  languages. Native preferences persist, and main-session language/FX/carry work
  is preserved. Financial inputs, canonical evidence and existing jobs survive
  language changes.
- Actual visual fixes: SVG background now covers the complete Qt chart; source
  columns have adequate spacing and elision/tooltips; duplicate guide introduction
  was removed and the collapse button states the current action. Wide-chart cursor
  geometry, persisted fallback-language notice and regional existing-chart ticks
  are also corrected.

Design: `INDICATOR_GUIDE_DESIGN.md`. Translation rules and remaining coverage:
`UI_LOCALIZATION.md`. Rights evidence: `MARKET_DISPLAY_RIGHTS_2026-10-31.md`.

## Verification

- 226 local runtime checks passed: 104 source fixtures, 97 native regressions
  (including the main rates suite), five chart-painting checks and 20 education/locale
  checks. These are current bounded tests, not the historical QA ledger totals.
- After the final selected-date reading refinement, 24 guide/chart checks passed
  at 150% scale, including painted background pixels, keyboard cursor, common
  dates, prefix invariance, provenance and explicit local report export.
- Inspected 1100×820 light and 1000×700 dark/150% native captures.
- Allowlisted wheel build and installed application/native smoke passed outside
  checkout, including the sample, provenance, rights inventory and locale data.
- Full runtime-smoke source/native suites and GitHub Windows 3.12/3.14 + Ubuntu
  3.12 checks are required for the current PR head. Consult the PR for live results;
  neither a queued CI run nor this document establishes a successful merge.

## Remaining acceptance and website follow-up

Physical Windows input/display/installer checks and live Flet browser visual
acceptance remain. Korean/English are the shipped catalogues; additional language
packs and professional review require the documented checks. Legacy model
narratives beyond the main session's completed translations remain its ongoing
work and are explicitly displayed as source-language prose where applicable.

Website follow-up is in `ui_website_updates/PR-42.json` and the shared `handoff`
branch's `WEBSITE_AWS_HANDOFF.md`. Current tools cannot send messages to another
Codex chat: the record is queued, without a delivery receipt. Website source
application and actual deployment must be reported separately by the AWS session.

## Prior completed work and consolidated handoff

PR36 (`73131c9`) fixed native large-price ticks, legends and footers, with 39 local
checks plus Windows/Ubuntu CI. PR37 (`2999296`) added the immediate UI→website
follow-up workflow. The shared `handoff/UI_SESSION_CURRENT.md` links these and PR42
for the main session's consolidated Claude handoff. Do not replace its active
CURRENT task/execution ownership or research ledger. This UI work does not run
actual ledgers, holdouts, protected caches or order paths.
