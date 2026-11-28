# Beginner chart and risk UI — 2026-11-21

This working UI branch adds compact explanations to the native desktop application. It is a preview candidate; manual owner PC acceptance, live-provider checks and publication approval remain separate.

## Visible changes

- Owner correction (2026-11-22): the original historical case chart appears first and remains visible on entry. A compact bottom-right legend shows the actual line, dash, dot, bar or band samples beside short indicator names, replacing the large text callouts and leaders. The case dates, source, cursor, zoom and report inputs are retained. Invented teaching diagrams are optional supplementary material below the case, initially folded; they never replace the case chart or its values.
- Presentation follows the existing market stock-detail screen: bundled QG Interface fonts, its type sizes and weights, palette, card spacing, numeric roles and disclosure controls. The investor/short-sale/order-book cards reuse that same presentation rather than independent fonts or native default buttons.
- All 27 guide indicators have a short reading and a limitation. EMA periods describe weighted spans; bounded oscillators keep their registered bounds; missing line segments stay missing. A band edge, crossing or high oscillator value does not guarantee a reversal or a continuing trend.
- Detached tooltips inherit the application font and theme, with logical-screen-aware wrapping. Numbers, source, observed/received times and literal Unicode text are retained.
- Stock detail groups PER/PBR/ROE/PSR definitions in a valuation card. PER/PBR use supplied quote values. ROE/PSR numeric fields remain unavailable until a verified provider contract is connected. Comparison averages require verified membership and matching metric period, unit and accounting basis; no theme members or averages are invented.
- PER/PBR include neutral, explicitly illustrative reference ranges and a current-value position, not universal company-quality grades or sector averages. Missing/nonpositive values have no favourable marker; earnings persistence, profitability and debt still matter.
- Investor bars use supplied gross buy and sell quantities. Net-only inputs remain labelled net quantities instead of being converted into a buy/sell percentage. Missing sessions and coverage stay visible.
- Short-sale volume share, a read-only order-book snapshot and trade execution-strength snapshots have concise reading notes. Short-sale volume is distinguished from outstanding short balances; order-book imbalance and execution strength are not predictive probabilities. Source and receipt/observation times stay distinct.
- The order book uses blue ask-quantity bars above red bid-quantity bars, with central prices and full quantities. All ten levels on both sides share one quantity scale; showing three or ten levels does not change that scale. No market probability or recommendation is inferred from bar length.
- Card, note, workspace-title and case-selector visibility is set after parenting, so hidden page construction does not expose temporary top-level windows. Component Show-event regressions distinguish construction from the intentional main-host display.
- VaR and CVaR explanations are connected to the relevant native views. Period, confidence, unit and loss convention come from actual result metadata. Saved records with missing metadata stay unconfirmed. The hedge view retains signed worst-tail P&L; the rates view retains monetary PV loss. Model calculations, stored result schemas and raw values are not changed by these explanations.

## Data and protection boundaries

The domestic ready-client profile path adds one order-book and one execution-snapshot request, with retry disabled and no new polling or streaming lifecycle. The execution endpoint is added to the existing read-only KIS allowlist. No order endpoint, credential policy, account path or confirmation rule is changed. Existing main OS storage protections must be preserved during integration.

No live KIS/API, real credential, private cache, owner database, real ledger, frozen study, AI spec disclosure, deployment or owner acceptance is performed by these cloud checks. Extra GPT/Gemini spec review remains optional and NOT_PERFORMED.

## Evidence recorded so far

- Educational V3 chart checks: 92 geometry observations, a separate 7 pure checks, one missing-segment check and two synthetic PNGs. These groups overlap and are not summed as a full-app test count.
- Stock/data V3: 19 targeted synthetic tests passed with no failures/errors/skips after preserving the initial widget-cleanup error and its correction. Provider constructors and real transports were not used.
- Tooltip: 64 actual offscreen observations at four Qt scales. All 32 observations with the bundled QG font fit. Overall 62/64 fit; two unregistered-font fallback cases clipped at 2x scaling and remain recorded failures. This does not establish Windows or arbitrary fallback-font acceptance.
- Stock risk copy and valuation definitions: 16 and 8 separate pure contracts passed. These do not replace container, risk adapter or full-app checks.
- Additional risk explanations: eight public contracts and four separate real-Qt component contracts passed, with a preserved harness-only failure before completion. Two stock-detail glue contracts passed on fixed synthetic profiles, using actual view methods and the real insights panel; this is not the complete StockDetail window.
- Container/export and focused public regression results are recorded as separate groups in the pull request. They are not inferred from, or added to, the earlier observations. A preselected-undocked-to-docked chip lifecycle error found by the container checks is corrected by rebuilding only chip widgets, preserving selection, focus, series and report/date inputs.

## Owner preview

After the integration and targeted checks are recorded, the coordinator supplies the exact preview branch and Windows launcher command. Preview approval does not merge the UI to main. The existing PC7 condition applies before that merge, and OS go-ahead applies before the OS-F1 Qt binding migration from PyQt6 to PySide6. OS-F2 storage-hardening code is already integrated; actual owner data migration remains separate. The website queue is a record of proposed updates, not proof that HTML was applied or deployed.

