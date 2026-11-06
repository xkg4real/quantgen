# Native Rates inline language

PR44 completed the Rates result narratives and explicitly left inline metadata
for later work. This follow-up, `⑬-8/b2/b/2`, supplies authored English/Korean
display variants for five existing blocks: source observation counts, swap
notional and payment frequency, option volatility and notional, swaption
direction, and simulation provenance with seed/path count.

The original mixed-language strings remain the canonical `ToolPane.text`
sources. Provider and model notes remain literal in both display languages,
including unfamiliar notes that resemble translation-catalog entries. Amount
precision, units, dates, IDs, model codes, ACT/365F, seed 7 and path-count
formatting are preserved. Synthetic disclosures remain visible; no mixed note
is folded. Report sections, export bytes, AI inputs, calculations and official
codes are unchanged. This does not complete all Rates, Flet or parent 13-8 work.

The existing Rates language module retains its eight narrative tests and adds
three actual-widget cases. These cover synthetic/unknown sources, both swap
directions, swaption/cap/floor and Bachelier/Black settings, and
Vasicek/CIR/Hull-White simulation metadata. EN/KO transitions verify literal
notes, canonical sources, numeric tokens and unchanged export/AI evidence;
job execution is refused. Before implementation, the new cases reproduced
19 failing subtests. After implementation, the complete module passed 11 tests
(110.673s, exit0), using synthetic data and isolated temporary state with
network, dotenv and protected stores blocked. An independent source review
found no blocking issue and confirmed the five canonical source expressions
match the prior code. The existing runtime workflow already runs this module.

The parent status-display correction is integrated before the final PR checks.
All 20 policy impacts are reviewed separately; source consistency does not
establish public-release readiness. Required exact-head Windows/Ubuntu CI,
PR merge and bounded completion receipts are recorded after their actual results.

No real Windows PC/DPI/assistive-technology, provider/API, legal/license,
supplier-parity, pilot, frozen-research or actual deployment evidence is added.
Extra GPT/Gemini specification review remains optional NOT_PERFORMED. Website
follow-up is a queued source record until a supported delivery receipt exists.

The status failure-test correction fa7c211 is integrated. Rates production and
test ASTs match the reviewed 3b175e1 exactly; the research-home test AST matches
the corrected and tested fa7c211. The merge changes no tested product behavior.

## Final status and A3 branch integration

The branch incorporates status d1a62a2 and responsive MC f7b4a73 through normal
merge. The Rates implementation and language tests remain AST-identical to the
11-PASS source; app, A3 helper and corrected research-home test matchd1a62a2.
The status/A3 integration passed41 guarded tests in96.053s. This is separate
from the Rates11-test run and is not a new41-test Rates result. Both complete
Rates and A3 policy/evidence sections were retained in the document conflict.

Final integrated-head Windows/Ubuntu Runtime and Compliance checks are required
before merge after PR77 and PR78. Prior a8d75b8 runtime contained the earlier
MC form and cannot verify this integrated head. Manual Windows, provider/API,
legal/license/pilot/frozen-research and website publication remain unverified.
