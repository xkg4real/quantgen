# A3 result layout and local reading help

The owner approved the bounded A1/A3 recommendation on 2026-11-06: retain the
existing G1 panels, improve native result layout, and reuse the local glossary.
This document describes the A3 implementation and its observed cloud checks.
A1 supplies the approved display vocabulary and is to merge before A3; the
combined head still requires its own verification. This is not approval of G2
transparency, new financial interpretation, or a Flet-wide layout change.

## Result layout

- **Monte Carlo:** the existing result title precedes the chart and narrative;
  the metrics table follows them. `fit_result_table` measures the current header,
  visible rows and frame after data, font, style and width changes. It shows the
  existing seven rows, or eight for GARCH, without an internal vertical scroll.
- **Bonds:** the existing 12 metrics and actual key-rate DV01 rows sit in two
  equal-width G1 panels. `PairedResultPanels` uses a row at 820 px of available
  content width and stacks below that width. The panels share a height in the
  wide layout. The yield/price title precedes its chart and narrative; scenario
  and hedge outputs remain available.
- **Shared sizing:** `ChartStudy` retains its 2:1 chart/narrative split and
  820 px content-width breakpoint. Its height-for-width calculation measures
  the prose at the width it will receive, including when stacked. Only the
  small MC/Bonds result tables opt into content-based height and right-aligned
  value columns; other tables retain their scrolling behavior. Outer page
  scrolling remains available.

The layout moves existing widgets. It does not change calculation inputs,
number formatting, chart series, source narratives, report sections, exported
records, AI commentary inputs, or official verdicts. MC continues to display
`NOT_RUN` and its assumptions; the Bonds source/synthetic notes stay visible.

## Local reading help

`reading_panel.install_reading_help` installs one window-local controller after
the pages exist. F1 or the label/table context menu opens **Learn terms**; Esc
or Close dismisses it and returns focus to the original widget and table cell
when that origin still exists. Copy and Select all remain available in the
context menu. Page/tool changes, result resets, table resets and a destroyed
origin clear the quotation instead of retaining a stale result. Same-row result
replacement and same-size selected-label changes also clear the quote. Caption-only
table language changes retain the original source and exact displayed quotation.

The panel searches the existing `core.education.glossary` entries and requires
an explicit choice to display a definition. It adds no terms, definitions,
predictions, numeric interpretation or AI request. A selected table row is
quoted from its displayed cells; selected label text is quoted verbatim. Values
such as `3.000%`, `−0.00` and `—` are not reformatted. Unknown searches show a
local no-match message. EN/KO panel controls and glossary definitions follow
the current display language while the source data remains unchanged.

At window widths of at least 1280 px, the 340 px panel docks beside the page.
At narrower widths it overlays the page without changing the body's width or
scroll position. That window threshold is separate from the 820 px chart and
result-panel content breakpoints: docking can cause those layouts to stack.
The overlay uses an available vertical interval of at least 260 px and avoids
visible widgets marked `reading_help_keep_visible`. If no suitable space is
available, help stays closed and explains how to scroll or widen the window.
Ordinary result rows may be covered temporarily; important notices remain in
view. Explicit host protection also covers consent/AI warnings, legal status,
source/delayed/failure containers and official-status notices. On protected
pages the narrow panel may require scrolling or a wider window. This geometry contract is not a claim of full screen-reader acceptance.

## Explicit provenance folding

`ToolPane.text` and `result_table` accept optional display-role metadata. Only
an explicit `display_role='provenance'` enters the initially collapsed **Details**
area. No role is inferred by parsing translated text. Default, unknown, mixed,
assumption, synthetic, delayed and failure text remains in the main result;
important notice/assumption tables can also be marked to prevent overlay.
The metadata is not added to `sections` or report/AI payloads.

The connected production callsite is Macro's pure `As of` date and source-count
line. Its separate synthetic IDs, descriptive-use warning and short-sample
note remain visible when Details is closed. Mixed metadata and warnings in
Rates, Structuring, Derivatives, ETF, Crypto and Strategy were not folded.
Source labels, provider choices and warning semantics are not removed.

## Verification and remaining evidence

The focused modules are `tests.desktop_a3_layout_acceptance` (four tests) and
`tests.desktop_a3_reading_acceptance` (12 tests). The former checks title
order, real row counts, wide/narrow layout, larger fonts and empty/reset
results, while comparing values, charts, reports and commentary inputs. It
exercises KO/EN at 1360 and 1000 px; the Bonds matrix includes light/dark.
The latter checks F1/Esc and focus return, explicit glossary selection,
notice-safe overlays and no-room fallback, stale-context clearing, exact
quotations, source/report/AI preservation and the actual Macro fold. It
includes an actual native Bonds fixture at 1000 px and synthetic EN/KO,
light/dark overlay cases.

Observed local runs used the guarded cloud runner with network denied, dotenv
disabled, protected paths blocked and mutable state isolated:

| Run | Observed result |
| --- | --- |
| Layout plus responsive, typography, language and Bonds regressions | 38 of 39 passed in 186.789 s; all four A3 layout tests passed |
| Reading plus Macro language and glossary | 25 passed in 20.380 s |
| Focused reading rerun | 9 passed in 7.492 s |
| Independent-review stale-quote correction, including same-row/same-size refresh | 12 passed in 7.811 s |

After A1 integration, the final 14-module guarded run passed **131 tests**
(exit 0, 302.857 s), covering both A1/A3 modules, native calculation fixtures,
language/report/payload contracts, Macro, commentary, typography and market tabs.
A separate actual-host diagnostic passed: 12 narrow scroll positions across
Library/System/Home/Markets and four wide docks kept critical content uncovered;
viewport/scroll and reports remained unchanged. Four actual integrated synthetic
captures covered Korean MC/Bonds/narrow help and English dark help. These are
Linux offscreen fixtures, not owner-PC acceptance. All 20 source policies were
reviewed after the implementation and independent-review corrections.

These runs overlap and their counts must not be added. The one failing broader
check is `test_platform_wide_header_options_fit_without_losing_selection_or_text`
in `desktop_responsive_tools_acceptance`: its deliberately overflowing setup
expects `horizontalScrollBar().maximum() > 0`, but the observed value is zero.
It reproduces independently and on the unchanged baseline; it occurs before
the assertions for repaired layout. The test and baseline were not weakened
or changed as part of A3. This remains a recorded limitation of the broader
local run, not a passing result.

The runtime packaging workflow runs the two A3 modules in their own offscreen
step. Adding that step is not evidence that CI passed: consult the checks for
the final PR head after A1 integration. Physical Windows installation, user-PC
DPI behavior, manual keyboard/screen-reader acceptance and any broader manual
capture matrix remain separate evidence. These checks also establish no real
API/provider comparison, pilot, legal/license, frozen-research, release or
deployment result. Optional additional GPT/Gemini spec review remains
`NOT_PERFORMED`.

The code changes are native-only. Browser applicability must be reviewed and
recorded under [UI_WEBSITE_SYNC.md](UI_WEBSITE_SYNC.md); native implementation,
message delivery, website application and deployment are separate states.
