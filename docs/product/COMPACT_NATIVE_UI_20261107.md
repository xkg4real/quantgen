# Native UI density and hinted Korean type — 2026-11-07

Buttons and short inputs previously expanded across the window. Categories now keep natural text widths and wrap; input panels use up to3/4 columns of approximately224px, with native reflow and height-for-width. Result columns follow content instead of equal Stretch, minimum34px rows grow for wrapped content, and paired summaries are bounded to960px. Raw request/result/export data and provider behavior stay unchanged.

Native fonts are renamed Gothic A1 hinted TrueType real400/500/600, all11172Hangul, with a separate offline Pretendard-derived symbol supplement. Flet OTF remains unchanged. See assets/fonts/README.txt for pinned source, SHA256 and SIL OFL notices. No runtime font download.

## Verification

The initial31-test run passed29; two historical fixture preconditions assumed unbounded panels. Their injected oversized content is still tested, while the new bounded behavior retains full request/choice/wrapped-text assertions. The corrected fixture checks plus typography/compact UI suite pass19 tests in83.537s. Packaging/policy tests pass50 in3.777s; source consistency passes20documents/622sources with publication BLOCKED. The initial29 successful cases and the two corrected cases cover the original31-test suite without counting overlapping cases twice. Windows CI and actual display confirmation remain separate. Actual Windows screen rendering at the owner's display settings is not proven by Linux offscreen checks.

## Website handoff

Native-only source. AWS should review density/type equivalents against actual browser source; never copy Qt code directly. No website HTML or deployment is included. Direct cross-chat sending is unavailable, so a saved queue is not a delivery receipt.

## 2026-11-10 correction: 224px is a base, not a ceiling

Runtime CI on PR89 (run 42245900881) failed in `tests.desktop_a3_layout_acceptance` on all four platforms: with 18px combo fonts the Monte Carlo form showed 2 columns at a 1360px window. PR89 capped every compact form at a fixed `max_columns*224+gaps` (696px for 3 columns, panel 730px), so native control minima above about 224px forced fewer columns at any window width.

`quantgen_desktop/form_layout.py` now caps a compact form at the larger of the 224px base and the width its full column count needs from the real control minima, and the bounded panel follows the visible form. With default fonts on Linux the widths are unchanged (Monte Carlo 696/730, Bonds 932/966); on Windows, where some default control minima are already above 224px, forms may be slightly wider than 696px instead of dropping a column. Narrow windows still reflow to 2 or 1 columns. Column choice still follows the A3 rule (actual minima plus spacing). Values, field order, reports and requests are unchanged. Windows rendering was checked only through hosted CI, not on a user PC.

