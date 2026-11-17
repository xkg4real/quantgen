# Native UI interaction and reading revision · 2026-11-14

Markets submenu clicks could close the menu before the intended row received the mouse press. The application event filter now distinguishes the platform QWindow event from the eventual QWidget target. A regression test sends a mouse click through the real window path; it fails on the previous implementation and passes after the fix.

## Resulting behavior

- The rail remains initially collapsed below Markets. Stocks and ETFs disclose only Korea / US; rankings are chosen inside the destination page. Crypto, futures and corporate bonds open directly. Every destination remains in Markets. Keyboard navigation and outside-click dismissal remain supported.
- Analysis and Build/Test reuse the native detail/guide visual rules: quiet tabs, bounded page width, compact steps and common surfaces. The paper-trading action row wraps; this fixes an observed 74px horizontal overflow at 1000px in English. Calculation behavior is unchanged.
- Risk/reward: drag the region or entry line to move the drawing in time and price; drag left/right edges for width, stop/target for price, or a corner for both. Price distances remain constant during whole-region moves. Width is a drawing extent and does not affect the ratio. Click the drawing and press Delete to remove; Escape deselects. Delete in a price editor edits the number instead. User prices remain through streaming and resizing, and reset on instrument changes.
- The risk panel uses a compact guide-style card, direction chips, aligned inputs, ratio and conditional gain/loss readouts. Detailed controls and calculation exclusions are expandable. Qt 6.12 themed `NoButtons` produced a one-pixel numeric editor during visual verification; normal editor geometry with hidden subcontrols fixes this, with a regression check under both themes.
- All 27 supported study explanations now show the current observation, a study-specific cross-check and a concise limitation. For RSI, check 30/70 crossings against price highs/lows; for ADX, distinguish DI direction from ADX strength; for short-sale share, inspect the denominator. Existing full references and the five detected condition-event descriptions remain expandable. No length expansion, invented success rate, entry/exit instruction or new forecast model.

Approved QG Interface/Pretendard OTF typography remains unchanged. No new provider request, broker order, account configuration or policy commitment is added.

## Verification

- Before-fix actual-window submenu click reproduced failure; after-fix targeted suite: 34 tests passed in 146.894s (menu, drawing, explanations, workspace geometry).
- Final numeric-editor and existing guide/form/paper regressions: 59 tests PASS (185.232s); syntax: 1 PASS. The earlier 34-test pass preceded the numeric-editor correction. Groups overlap and must not be summed.
- Offline captures: `/workspace/shared/ui-menu-workspaces-20261114/` (1440px light/dark, 1000px chart, 1360px research workspaces). Linux offscreen capture is not owner Windows DPI or screen-reader confirmation.
- Multi-OS native regression checks are included in Runtime CI. Completion status belongs to the PR/hand-off evidence, not assumed from local results.
- Compliance review preserves 20 documents' publication blockers; source consistency is not legal or publication approval.

## Main delivery evidence

PR [119](https://github.com/xkg4real/quantgen/pull/119), source `b8d5ac889bc89372cac7cc8595c252fa6bc49705`, merged as `51d7ffb758d1393f1713cd4dafd32ed3673738c2`. Main ancestry was fetched and verified.

Runtime [43454709190](https://github.com/xkg4real/quantgen/actions/runs/43454709190): the new actual-window menu clicks, drawing/editor and research geometry checks, together with the early native/market integration step, passed on Windows Python 3.11/3.12/3.14 and Linux 3.12. Syntax Python 3.10/3.11 passed. **The long full runtime suite remains in progress at this delivery checkpoint.** Merge relied on these cross-platform feature checks, the local 59-test regression and prior baseline Runtime117's completed six-job success; the prior baseline does not substitute for completion of the new full run. Compliance [43454709248](https://github.com/xkg4real/quantgen/actions/runs/43454709248) passed. No required check was bypassed.

Website queue: [PR-119.json](ui_website_updates/PR-119.json). Delivery is queued, not sent.

## Delivery / remaining boundaries

Native source implementation only. Website impact is queued under `docs/product/ui_website_updates/` for 웹사이트 작업공간(AWS); no supported cross-chat messaging tool is available. A saved handoff is not a delivered message. Website source, preview and AWS deployment are separate and unverified here.

For the main/Claude session, see the latest `UI_SESSION_CURRENT.md` and appended `⑬-2/` rows on `handoff`. Existing research ownership and protected records are unchanged.

## Run after main merge

Quit the old application. In a PowerShell window enter `cmd` first. Choose the actual folder:

```bat
cd /d "C:\Users\skymi\OneDrive\문서\GitHub\quantgen"
```

or, on whydi:

```bat
cd /d "C:\Users\whydi\OneDrive\Desktop\QUANTGEN"
```

Then paste:

```bat
set "QG_GIT=git"
for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
"%QG_GIT%" switch main && "%QG_GIT%" --no-pager pull --ff-only origin main && "%QG_GIT%" --no-pager log -1 --oneline && call Start-QUANTGEN-Desktop.cmd
```

Keep existing `.env` and KIS keys. The launcher uses the existing native virtual environment; no new shortcut is required. A failed pull stops the chained launch rather than discarding local work.
