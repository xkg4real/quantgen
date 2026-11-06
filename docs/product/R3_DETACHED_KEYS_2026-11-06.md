# Detached R3 planned configuration keys

Bounded child **⑨-3a/keys/1** implements the pure key-builder portion of the
approved R3 revision 2, sections 9.1/9.2 and T-RUNREG-01b. It does not call the
existing Lab, register a run, count trials, resolve instruments or choose costs.
The existing registrar and frozen key helpers remain unchanged.

## Compatibility contract

`lab_config_ids(rule, is_pairs, symbols, grid, cost_bps)` consumes explicit
planned inputs and returns `{theta_index, config_id}` for each grid position. The caller supplies the rule ID and already resolved numeric
cost as an integer or float; booleans, unresolved costs and nonfinite values are refused, including for an empty grid. Symbols use the old registrar's strip/uppercase behavior; non-pairs sort
while pairs preserve their order. Duplicate symbols and duplicate grid entries
are preserved. Planned grid entries are not a deduplicated registration count.

The old JSON roundtrip with `default=str` is retained, including tuple/list
conversion and JSON object-key coercion. Supplied symbols and cost override the
same names in theta. Cost 50 and 50.0, and integer/float theta values, retain their
historical distinct bytes. The final canonical key JSON refuses nonfinite
numbers; the event codec's nonfinite-to-null behavior is not used for keys.

The nine-field recipe has `rule`, `params`, literal `COMPLIANT` timing and six
null optional fields. It hashes sorted compact UTF-8 JSON without a trailing
LF. Separately supplied top-level run metadata such as dates, provider/source,
timestamps, market, script, run anchor and results is not automatically imported
into this key. If the caller explicitly places those names inside theta, they
remain in params and affect the ID. The literal timing_class COMPLIANT is part
of the inherited key recipe, not an observed timing, regulatory or research
approval. This is historical key compatibility, not proof of
scientific equivalence, tradability, supplier identity, data rights or a verdict.

The helper initiates no storage, provider request, default-path lookup or clock.
Arbitrary caller-provided objects can have unstable or side-effecting string
conversion; this function is not a sandbox for their behavior. Inherited JSON
key-coercion collisions are not repaired by silently changing the registrar.

## Historical reference and verification boundary

The historical registrar at 527cdf24f90528a00a6b79901692ca926ceb4bc1,
`ui/strategy_lab_page.py`, and the current registrar relocated to
`core/research/strategy_workflow.py` have identical 1,708-byte function slices
including terminal LF, SHA-256
`8906e993263905b30a6bba2f9e977762bb8ec8e8f69545d822a825af7bb67fb3`.
The historical/current gate-ledger and canonical-JSON helper blobs also match.
The new builder does not import the broad workflow or ledger to compute keys.

The maintained acceptance module passed **13 guarded synthetic tests in
0.986 seconds, exit 0**. Literal source-derived historical fixtures contain
27 cases and 151 expected positions, including all 66 positions of the seven
family grids with integer/float cost variants. An independent generator used
whitelisted historical source and did not access the new builder; it passed its
final probe in 0.051 seconds. These fixtures were generated now from the pinned
historical source, not recovered from a historical production run.

The unchanged current registrar was actually invoked against explicit fresh
temporary ledgers for all 26 nonsynthetic-labelled fixture cases. All inputs
were synthetic. The default macro-directory path was patched to refuse access,
dotenv was disabled and runtime file/network guards remained active. A separate
SYNTHETIC-labelled case returned before registration and created no ledger.
The US table-value 50.0 input is pinned to the source literal without executing
a cost resolver, scoring gate or price loader.

Independent implementation review passed **7 private overlapping probes in
0.002 seconds, exit 0**. These are not added to the 13 acceptance count. Source,
test and fixture hashes remained fixed. Two earlier private historical-generator
setup failures are preserved: incorrect assumed grid counts and a missing
stdlib time import allowance. Correcting that reference setup did not change
product source or the historical writer. The initial 12 maintained tests also
passed before the source-literal cost provenance assertion was added.

The Runtime workflow adds this source/test/fixture path and bounded test module
while retaining every prior test-module count and timeout budget. Final-head
Windows/Ubuntu Runtime and Compliance must succeed before merge. All writer comparisons must use
explicit fresh temporary ledgers with synthetic inputs, disabled dotenv,
network denial and protection against default/actual data paths. No run_family,
score, study, actual ledger, protected cache or card execution is permitted.

A SYNTHETIC source makes the existing registrar return before writing; planned
keys can still be computed independently. Their existence proves no actual
registration, eligibility or trial count. Full T-RUNREG-01b and parent ⑨-3a,
canonical panels, recorder/Lab integration and scientific evidence remain open
unless separately established. Physical Windows/API/provider/legal/license/pilot
and frozen-research evidence are separate. Publication remains BLOCKED and
optional additional GPT/Gemini spec review remains NOT_PERFORMED.
