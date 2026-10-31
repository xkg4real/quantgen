# UI session checkpoint — 2026-10-31

Status: implementation in progress; this checkpoint is not a completion claim.
Branch: `gpt/indicator-guide-20261031`, starting from main `579aadb8fd219a25b543ea8c9a2c803d3a2cbece`.

The owner requested four connected tasks: a historical technical-indicator guide
on Home; a registered-market-data display/rights review; a shared selection and
chart grammar for guide and actual market histories; consistent multilingual UI,
regional formatting and reports. The owner also confirmed the introduction site
is **https://quantgeneration.com/** and requested including all UI work in the
main session's eventual Claude handoff.

## Already merged before this checkpoint

- PR #36, main `73131c9`: native chart tick clipping, legend overlap and footer
  fixes. 39 distinct local tests and Windows 3.12/3.14 + Ubuntu 3.12 CI passed.
  Physical Windows display acceptance remains pending.
- PR #37, main `2999296`: UI→website handoff instructions and PR-36 queue record.
  Chat messaging/wake tools are unavailable; queued does not mean sent/deployed.

## Current implementation, not yet accepted

- Shared `core.education`: one aligned series per selection, SMA20/50, EMA12/26,
  Wilder RSI14, MACD12/26/9 and BB20±2 population SD. Real observed OHLC/volume
  are optional; none is synthesized from closing/reference values.
- An offline, checksum-pinned 2018–2022 sample has 1,247 actual historical
  USD/EUR reference observations from a pinned public-domain Fed/FRED mirror.
  The mirror inverts DEXUSEU and rounds to four decimals. Attribution and the
  transformation are explicit. This is not exchange OHLC or live data.
- Native and Flet guides, Home entry points and market-history explorers in
  Signals share vector rendering, selection state, colours and time axes.
  Explanations include meaning, where to look, interpretation and limits;
  annotations show hindsight counterexamples without a trading/gate verdict.
- Data-usage review: six Home observations, 73 registry series and 13 provider
  policies. Free/paid, live/delayed, retention, export/redistribution, derived use,
  attribution and costs remain separate fields. Most uses are conditional,
  need replacement, or need further verification. This is not legal clearance.
- Per-view locale contexts, Korean/English baseline catalogues, explicit English
  fallback for missing packs, 714 CLDR regional choices, localized report views,
  in-place UI bindings and 42 generated legacy presentation templates. Wider
  translation packs and independent language review are not claimed complete.

## Verification state and next work

Initial existing suite: 31 tests ran; two expected integration failures exposed
the changed default Home language and an eager bundled-sample read during Flet
Home construction. The expectation now uses Korean, and the Flet guide is lazy
until explicitly opened. The rerun passed all 31 tests. Dedicated calculation/provenance/locale/rights,
Flet callbacks and native guide/export tests subsequently passed 17 tests.
The 17-test source and vector-cursor/report-integrity follow-ups are saved in
the next checkpoint; final combined CI and visual acceptance remain pending.

Still required: dedicated calculation/alignment, sample-integrity, UI binding,
locale/no-input-reset, report, rights and packaging regressions; desktop/browser
visual inspection at narrow widths and light/dark themes; code review, CI and
PR merge. Audit legacy translation coverage and any new chart layout defects.

The owner will continue website work in the already-authenticated AWS session.
Website tasks are saved at handoff:WEBSITE_AWS_HANDOFF.md. The UI session's
separate temporary login was cancelled; do not request another login here.
The deployed source/hosting is still unverified in this session. No website
modification or deployment is claimed. The app work remains independent.

## Main-session/Claude handoff

Include this branch's final commit/PR, checks, remaining items and the existing
website queue in the next consolidated Claude handoff. Keep the main session's
task/execution ID, research ledger, ownership and formal approval boundaries.
The UI session has not run actual ledgers, holdouts, orders or protected caches.
