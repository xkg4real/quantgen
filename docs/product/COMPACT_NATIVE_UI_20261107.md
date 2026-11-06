# Native UI density and hinted Korean type — 2026-11-07

Buttons and short inputs previously expanded across the window. Categories now keep natural text widths and wrap; input panels use up to3/4 columns of approximately224px, with native reflow and height-for-width. Result columns follow content instead of equal Stretch, minimum34px rows grow for wrapped content, and paired summaries are bounded to960px. Raw request/result/export data and provider behavior stay unchanged.

Native fonts are renamed Gothic A1 hinted TrueType real400/500/600, all11172Hangul, with a separate offline Pretendard-derived symbol supplement. Flet OTF remains unchanged. See assets/fonts/README.txt for pinned source, SHA256 and SIL OFL notices. No runtime font download.

## Verification

The initial31-test run passed29; two historical fixture preconditions assumed unbounded panels. Their injected oversized content is still tested, while the new bounded behavior retains full request/choice/wrapped-text assertions. The corrected fixture checks plus typography/compact UI suite pass19 tests in83.537s. Packaging/policy tests pass50 in3.777s; source consistency passes20documents/622sources with publication BLOCKED. The initial29 successful cases and the two corrected cases cover the original31-test suite without counting overlapping cases twice. Windows CI and actual display confirmation remain separate. Actual Windows screen rendering at the owner's display settings is not proven by Linux offscreen checks.

## Website handoff

Native-only source. AWS should review density/type equivalents against actual browser source; never copy Qt code directly. No website HTML or deployment is included. Direct cross-chat sending is unavailable, so a saved queue is not a delivery receipt.
