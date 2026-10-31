# UI session supplement for the consolidated Claude handoff

Owner instruction (2026-10-31): app UI work continues in this UI session; website work belongs to 웹사이트 작업공간(AWS). Include UI-session changes in the main session's Claude handoff. This supplement does not transfer CURRENT ownership or modify its execution ID, research gates or ledger.

## Current implementation

- Branch: `gpt/indicator-guide-20261031`
- Saved source: `afffa4a7706052125df95dea42f76dab79d2b679`
- PR42: https://github.com/xkg4real/quantgen/pull/42 — ready for review; not yet merged at this checkpoint.
- Main integrated through `9d55e2ba350054759055c2f85b4332993a047e8d`, preserving PR39 language persistence, PR40 FX and PR43 carry translations.
- Current CI: https://github.com/xkg4real/quantgen/actions/runs/41180136658 (in progress when recorded).
- Local: 63 integration tests passed; final guide/chart refinement passed 24 tests at 150% scale; allowlisted wheel build and installed application/native smoke passed outside checkout. Full runtime regressions are being checked. Native light/dark screenshots inspected at 1100×820 and 1000×700/150%.
- Detailed, versioned progress: docs/product/UI_SESSION_PROGRESS_2026-10-31.md.
- Design/source evidence: INDICATOR_GUIDE_DESIGN.md, UI_LOCALIZATION.md and MARKET_DISPLAY_RIGHTS_2026-10-31.md under docs/product/.

Home has multi-select SMA/EMA/RSI/MACD/BB education on a shared historical sample, aligned panels, same-date cursor reading and explanations, four-part interpretation and hindsight counterexamples. Signals uses its own actual History with the same components. Partial SVG backgrounds and crowded source columns were reproduced visually and fixed. Native language/region settings persist and preserve financial inputs and original research evidence.

The sample is 1,247 actual 2018–2022 USD/EUR daily reference observations with pinned Fed/FRED mirror provenance and reciprocal/four-decimal disclosure, not OHLCV or live data. Six Home + 73 registry entries have provider-usage review policies, without publication/legal authorization. Korean/English catalogues ship; 714 CLDR regional choices are not 714 translated languages.

## Work to retain and complete

Finish current-head CI and remaining regression diagnosis, then merge only if successful. Preserve newer main-session narrative changes if main advances. Physical Windows display/input/installer and live Flutter browser visual acceptance remain; broader language packs/professional review and remaining legacy narratives are not marked complete. Main-session narrative work continues independently.

After merge, update this supplement with exact source/merge and CI. Do not repeat completed PR36/37 work or restart the guide from its early draft checkpoints. Do not mutate CURRENT merely to include this supplement.

## Completed prior work

PR36 merged at `73131c9e74b9ec61fca88845cbdad1525ebceef9`: native tick/legend/footer fixes, 39 local checks and Windows 3.12/3.14 + Ubuntu 3.12 CI passed.
PR37 merged at `2999296cae297da69b0198c4a72a9b49fe33ae95`: UI→website workflow and change queue.

## Website delegation

Confirmed site: https://quantgeneration.com/. Read WEBSITE_AWS_HANDOFF.md and the app's docs/product/ui_website_updates/PR-42.json.
The owner explicitly says website UI must be continued in the already authenticated AWS session while app UI continues here. The UI session's temporary AWS login was cancelled; do not request another login here.
Supported tools lack cross-chat send/wake: shared handoff is saved, delivery remains queued without receipt, and site application/deployment is unverified. A saved GitHub document is not a sent chat message.
No actual ledgers, protected cache, holdout/frozen study or order paths were executed.
