# Native Bonds / Portfolio result language

When the Windows app language changed, the Bonds and Portfolio long result
narratives and constraint warnings stayed in English or mixed Korean/English.
The native panes now retain explicit English and Korean display variants and
switch them in place. No calculation, data load or AI request is triggered by
this change.

This is completed sub-scope **13-8/b2/c/a**, subject to the linked PR checks.
The parent 13-8 and remaining model/inline-text work stay incomplete.

## Display coverage

- Bonds: price/yield/duration/convexity, key-rate concentration (including a
  zero-sum/empty vector), z-spread, positive/zero/negative carry and roll,
  curve-based funding proxy versus executable repo, best/worst scenarios,
  and signed futures hedge counts/rounding/residual DV01 with no-order notice.
- Portfolio: all four objectives, leading allocations and risk contribution,
  missing risk contribution, convergence failure, non-positive Sharpe warning,
  feasibility-adjusted caps and selected-versus-comparison/frontier scope.
- Mixed total-return/price-return convention warning, synthetic data notice
  and common-session count.
- Exact known model-note sequences are translated as a whole. Unknown notes,
  provider descriptions, issuer names, symbols and scenario identifiers remain
  verbatim. A custom narrative does not get silently replaced by a generated
  translation. English display is explicit as well, keeping raw provider text
  outside broad string replacement.

## Evidence and boundaries

`tests/desktop_bonds_portfolio_language_acceptance.py` verifies displayed numbers,
signs and precision against existing English narratives, conditional warnings,
unknown-text preservation, repeated English/Korean switching, new results and
clearing, report/source immutability and unchanged tables/chart inputs. It uses
injected/synthetic data, blocks requests, and runs Qt offscreen. Runtime CI also
runs it on Windows 3.12/3.14 and Ubuntu 3.12.

The numeric calculation modules, canonical text/report sections, financial
identifiers, solver bounds, funding formula and official research verdicts are
unchanged. The display adapters consume existing results. Imported narrative
helpers format results only. No provider/key validation, new package, persistent
setting, external translator or order path is added.

Other model prose, remaining inline/table-unit strings, raw provider language,
Flet parity, manually inspected Windows/DPI layout, and the user's installed
version remain separate work. Shared locale/report integration from PR42 and
Claude error classification from PR46 are preserved. Native source changes are
queued for website review; they do not prove website application or deployment.
