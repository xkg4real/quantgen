# QUANTGEN whole-week recovery checkpoint — 2026-11-06 20:41 KST

Final checkpoint includes the owning execution's verified PR84 and PR85 final
CI, merges, bounded completion records and task-page read-backs through
20:41:24 KST. Earlier drafts and original failure receipts remain preserved.
This record is a partial progress checkpoint, **not a weekly `returned` event**
or an acknowledgement that another session has received it.

Keys PR84 and supplied-panel data-hash PR85 are complete within their bounded
scopes. The R3 parent and whole Remaining Work remain incomplete. The owning
execution is closing this prolonged execution by reserving remaining budget for
a recoverable handoff. No actual hard runtime-limit event or account-token
balance is claimed. No new large R3 unit is started here; approved later work
resumes through the prescribed ownership validation without a cooldown or
Thursday deferral. The source-digest candidate below remains unclaimed.

Remote facts below are observations supplied by the owning execution; local
verification is attributed separately. Final source and workflow identity matter:
an old branch success is not success for a newer source.

## Immediate recovery state

| Unit | Source / branch | Verified final result | Remaining boundary |
| --- | --- | --- | --- |
| Keys, bounded child `⑨-3a/keys/1`, PR84 | `a083f75138c44feaa9eca788d82d53215eed38c0`, `gpt/run-registry-keys-20261106` | Runtime `42205995118` all six and Compliance `42205995086` succeeded; merge `9660352d4984649c5937cc8d95d0f9f1f7d20fc1`, PR/main, LEDGER, CURRENT and local completion read-backs confirmed at 20:16:56 KST; both task-page bounded keys strikes read back at 20:20:40 KST | Preserve completion; no duplicate merge, completion row or strike |
| Supplied-panel data hash, bounded child `⑨-3a/data-hash/1`, PR85 | `8e6db5b0b385d486596e51dd94d155c4847cd3de`, `gpt/run-registry-data-hash-20261106` | Runtime `42208104232` all six and Compliance `42208104307` succeeded; merge `6ddf5146695de739e9f1ee5e2be609efd9d7be4c`, PR/main read-back; bounded LEDGER, CURRENT and local completion at 20:38:44 KST; both task-page bounded data-hash strikes read back at 20:41:24 KST | Preserve completion; detached helper only, not full R3 |

PR83, PR84 and PR85 bounded completion and their requested task-document updates
are verified. Only their verified children were struck through. No overall
Remaining Work, T-RUNREG or parent `⑨-3a`/R3 completion is claimed.

## Prior Claude/session work — attributed history

These earlier summaries were already represented in CURRENT/LEDGER. They are
prior-session reports, not independently rerun evidence from the present tests.
Preserve their ownership and later superseding changes.

| Prior work | Recorded evidence | Scope reminder |
| --- | --- | --- |
| Searchable technical guide | PR64; `7de46d4`, `9f7dc0e`, `ba3b6b2` | EN/KO terminology, search and chart chips |
| Asset tabs, search and zoom | PR65; `1682404` | Historical UI; later Markets redesign supersedes parts |
| Market-indicator charts | PR66; `c1a4e97` | Historical indicator layout, distinct from the later Watchlist view |
| A2 controls | Completion record ending `7fc53e2` | Input, wheel, amount, icons and AI notice; physical user-PC acceptance separate |
| Crypto missing-value handling | PR68; `ce77566` | Bounded missing values, observed scope and partial valuation; no blanket whole-model validation |
| Markets, Watchlist and typography | PR71; `d5e73ae` | Recorded UI children, not real-provider or full accessibility verification |
| Option disclosure | PR72; `a32106b` | Box, average-hedge and model-free-IV limitations |
| Model and ETF disclosure | PR73; `faf9f3b` | Bootstrap, undefined Sharpe and sleeve-convention limitations |
| Separate-session decisions | PR74; `a41fd7a` | Decision-table integration; no new pilot, supplier or frozen-study execution here |

The earlier Claude AI implementation was handed over with corrections pending.
Its reported 229-test result remains attributed implementation evidence. The
later PR75 corrections, independent checks and final CI below supersede that
pending implementation state without erasing the earlier report. Do not replay
older uncommitted work over these later replacements without an exact comparison.

## Completed bounded work recorded in this execution

| Unit | Final source | Main merge | Final CI evidence |
| --- | --- | --- | --- |
| AI payload/commentary, PR75 | `a419db99baaf911d9e6f06890ab7bce6cb4b5447` | `e79ef2c1160242ddf86d5b381e1005f2ad627e16` | Runtime `42173460454`, Compliance `42173460398` succeeded |
| A1 terminology/display roles, PR76 | `2715d9e1aaee0d303ee483d11b9e6669459aa871` | `2a78ee3e972eefe1ec2063a13d52d05f092bf24c` | Runtime `42178486278`, Compliance `42178486098` succeeded |
| A3 result layout/reading help, PR77 | `bd7ee2a1b329320caf99fdff0ec61abb4cc443a4` | `655f1e1a7a9fafe63abd2135909157546cf4cc32` | Runtime `42190250542` all six jobs, Compliance `42190250754` succeeded |
| Existing status display, PR78 | `e03898833329fd64db0feecab485dffe0fa297c8` | `f180f697c646a39536b7b57886d58c3667b4a9af` | Runtime `42191023747` all six jobs, Compliance `42191023765` succeeded |
| Rates inline explanations, PR79 | `62246779f45b9e4eff37b7af6ac7e71354b5fd18` | `a63fffb20fed22d6d0d582d68167af818c94db0b` | Runtime `42194971104` all six jobs, Compliance `42194971102` succeeded |
| Detached instrument identity, PR80 | `386a0d75ce2b242873a5146eacebece66f1ae25e` | `2a7e51bcb742c785fd32f1e366cf60a2e957ef4b` | Runtime `42195764855` all six jobs, Compliance `42195765001` succeeded |
| Pure run-registry codec, PR81 | `f3d6c5e2a0de766ab79a73d392eb77bd307c9862` | `7274dedc3977b81546e085c4d0ff933b4188457b` | Runtime `42196016748` all six jobs, Compliance `42196016647` succeeded |
| Single-segment run-registry store, PR83 | `b5cbf6695b8430f89298e8c96294f2b83c4b0a85` | `d3f94b81b3e8c6ba0e9bb605d39b4726af62a392` | Runtime `42198946682` all six jobs, Compliance `42198946631` succeeded |
| Planned keys, PR84 | `a083f75138c44feaa9eca788d82d53215eed38c0` | `9660352d4984649c5937cc8d95d0f9f1f7d20fc1` | Runtime `42205995118` all six jobs, Compliance `42205995086` succeeded; bounded LEDGER completion recorded |
| Supplied-panel data hash, PR85 | `8e6db5b0b385d486596e51dd94d155c4847cd3de` | `6ddf5146695de739e9f1ee5e2be609efd9d7be4c` | Runtime `42208104232` all six jobs, Compliance `42208104307` succeeded; bounded completion and both task-page read-backs verified |

The owning execution recorded bounded IDs, merge verification and task-page
completion read-backs through PR85. Retain existing LEDGER rows; do not append
duplicate completion rows because this checkpoint repeats the evidence.
Only completed children were struck through; partial parents remain open.

“All six Runtime jobs” means the installed Windows 3.11/3.12/3.14 and Ubuntu 3.12
jobs plus syntax jobs for that source. It is not a physical user-PC run. Local
focused, integrated and independent test counts overlap and must not be summed
into an invented unique acceptance total.

Important retained bounds:

- AI has advisory numeric comparison, not semantic/sign/verdict verification.
  Its calculated-JSON UTF-8 byte cap is not an HTTP/token/cost cap. Valid values,
  end-turn-only success and redaction/withheld-check distinctions remain. Actual
  API permission/billing/model access is not proved by synthetic tests.
- A1 is the approved terminology/display-role subset, not complete native/Flet
  localization. A3 improves existing result layout/help, not all UI redesign,
  a new interpretation engine or complete transparency.
- Status displays existing owner-decision/technical/publication evidence; it
  does not change approval rules or turn missing publication into approval.
  Previously observed narrow System overflow of 58/44 remains recorded.
- Rates changes are five display-only EN/KO blocks. Provider notes, model codes,
  numeric results, canonical report and AI payload contracts are retained.
- Detached identity uses explicit caller evidence and controlled unknown or
  ambiguous results. It is not a verified provider/cost resolver or new cost
  calculation, market classification, trading permission or live integration.
- The codec validates a canonical envelope/line and supplied-byte MD5 chain.
  MD5 is compatibility/consistency, not authentication. An unanchored valid
  prefix cannot expose deletion of a complete suffix. This is not full event
  payload/lifecycle or owner-authority validation.
- The store uses an explicit trusted caller-selected directory, process/OS
  locking, full verification of one active segment, a five-machine-event
  allowlist and duplicate STARTED/FINISHED refusal. It does not enforce lifecycle
  or event-order transitions. Its per-segment byte cap is not retention/quota/rotation. Interrupted attempted writes can
  leave uncertain partial/full bytes; no blind retry/repair/deletion is promised.
  Exact-head hosted Windows locking/reopen/LF/hash tests are real hosted
  evidence, but do not complete R3 storage/recovery/durability/security.

## Current keys implementation and source transitions

The keys helper implements planned `{theta_index, config_id}` compatibility from
explicit caller rule/pair/cost and preserves the existing symbol normalization,
ordering, repeated positions, key/default-string behavior and numeric-type
identity distinctions. Metadata outside theta is not imported automatically;
the same names supplied inside theta remain ordinary parameters and affect the
ID. The inherited `COMPLIANT` recipe literal conveys no timing, regulatory,
research or owner approval. There is no new data fetch, production registration,
trial-count action, recorder or Lab hook.

Recorded local evidence includes maintained 13 PASS, independent 7 PASS and a
separate historical-source generator check; these overlap and are not summed.
The 27-case literal fixture has 151 expected positions. Its seven full family
grids contain 66 original positions, each evaluated at integer50 and float50.0:
132 positions within the151 total. The unchanged CURRENT relocated writer ran
26 nonsynthetic-labelled cases with wholly synthetic inputs and actual isolated
temporary ledgers, never the production default; the SYNTHETIC case wrote none.
Separately, the HISTORICAL source was AST-selected and executed with in-memory
capture to generate the literal fixture now. That historical-source generator
did not run those actual temporary ledger writes. Neither path establishes
archived production records or historical ledger contents. Reading a source cost constant is not executing a
real cost resolver.

Old keys source `246c9af2159880c45f59ed5e895e673be2a8180f` subsequently had all six
Runtime `42201679975` jobs and Compliance `42201680042` succeed. Separate UI82
main movement then required integration. Preserve that old success but do not
transfer it to current `a083f75138c44feaa9eca788d82d53215eed38c0`.

The latest integration has root's separate 46-core PASS receipt, the UI checks
below, and 20-policy consistency review PASS602 with publication BLOCKED. That
review is bounded implementation consistency, not legal/publication permission.
Current PR84 a083 has now independently completed all six Runtime jobs and
Compliance, merged at9660352 with PR/main read-back. Its bounded completion was
recorded at 20:16:56 KST with CURRENT/local-state read-backs; the two bounded
task-page updates were independently read back at 20:20:40 KST. Preserve those
separate receipts.

## Separate UI82 session and independently executed local integration

UI82's company marks, table/readability and typography work belongs to a
separate session. Its previous CURRENT/LEDGER observations and website handoff
attribution remain valid history. This execution integrated resulting main into
keys, without claiming ownership of the other session's original work.

Latest UI82 observation supplied by the owner of this execution identifies
source `4ce18` and reported merge `5b7988` (short identifiers as supplied).
The independent observer confirmed at11:16 UTC that Runtime `42204806984`
completed all six jobs and Compliance `42204806985` succeeded. This is final
source4ce18 evidence for the separate UI session, not success borrowed from
`92c7280` or `c028dd96`. Earlier pending observations remain historical. The
reported merge alone was insufficient; this later observed full CI is distinct.

The operation verifier independently ran the following exact local tree before
the later integration commits: HEAD
`246c9af2159880c45f59ed5e895e673be2a8180f` plus uncommitted MERGE_HEAD
`e4ec6ef9ed8ea1dc16ae7f06a8e75ec9bc0f1944`.

| Local scope | Result | Process outcome |
| --- | --- | --- |
| `tests.desktop_watchlist_acceptance` (22), `tests.desktop_markets_watchlist_acceptance` (16), `tests.desktop_typography_acceptance` (14), `tests.stock_profile_acceptance` (34) | 86 PASS, unittest 106.513 seconds | exit 0; wall time 112.545 seconds |
| `tests.desktop_responsive_tools_acceptance` | 5 PASS, unittest 33.338 seconds | exit 0; wall time 38.180 seconds |

Before/after SHA256 checks on 410 allowlisted Python source/test files matched
for each run. No code or test was edited by the verifier. Real widget, keyboard,
language, theme, search, fake-provider and temporary-persistence paths were
exercised. These were Linux offscreen runs under an existing guarded runner,
with external I/O and actual protected data blocked. The runner's pre-existing
polling accommodation is not a product patch or Windows result. Do not relabel
this earlier local tree as a separate rerun of the later a083 commit.

The incoming responsive test derives its deliberately oversized minimum width
from the actual viewport plus 100 pixels, with a floor of 710. It proves induced
overflow, restores the production policy, then checks zero overflow and retained
request/selection/tooltip/accessibility in EN/KO/EN. This resolves the test's
new-viewport precondition for this tree; the earlier A3 30 PASS + 1 baseline FAIL
is retained below. Browser application, website delivery and deployment remain
separate from the native UI code and queued metadata.

## Completed bounded supplied-panel data hash, PR85

Implementation files:

- `core/quant/run_registry_data_hash.py`
- `tests/run_registry_data_hash_acceptance.py`
- `docs/product/R3_DETACHED_DATA_HASH_2026-11-06.md`

`data_md5(dates, symbols, closes)` is a detached caller-input compatibility
helper. It uses the approved byte contract without extra JSON, shape/dtype
framing, timestamps, metadata or a trailing newline. It preserves literal
ordering and raw float64 bit distinctions, including signed zero and distinct
NaN payloads, with no floating-point canonicalization or input mutation.

The documented supported domain is nonempty ordinary list/tuple string labels,
valid ASCII calendar dates and exact two-dimensional float64 ndarrays whose
shape matches the labels. Unsupported tokens, types, coercion hooks, subclasses,
memmaps and empty axes are refused. Supported endian/layout/stride conversion
preserves bits. Calendar format validation is not a trading-session assertion;
NaN bit preservation is not a claim that NaNs are valid prices. Caller input
must remain stable during the call; there is no concurrent-mutation snapshot or
hostile-memory sandbox guarantee.

Saved implementation/review receipts freeze these SHA256 values:

| File | SHA256 |
| --- | --- |
| Source | `f78a28ea0709f3d10a593aa82f77b8ef601b171f17e3ff89e54bcf237c360699` |
| Maintained test | `b4907328da604bbcf6e9e4acb99c54b16fe4cc40190e47661e75255d4b5fa8ad` |
| Product document | `5d8e934360afcf777810a57221a1a1205b8be14bcadd6daffd3f4f13c8eab327` |

Local results read from the saved receipts, not rerun for this checkpoint:

- Maintained helper acceptance: 15 PASS in 0.013 seconds, exit 0.
- Independent implementation probes: 10 PASS in 0.009 seconds, exit 0; no
  material blocker within the supported-input contract.
- Root combined data-hash/keys/store/codec run: 61 PASS in 1.382 seconds, exit 0.
  It includes the maintained 15 and must not be added to them as unique coverage.
- Separate stdlib literal-preimage preparation was setup evidence, not additional
  product acceptance. Independent probes fixed their own literal before product
  execution; they did not derive expected values by calling the helper.
- Source review: all 20 policy checks GO, consistency PASS605, publication BLOCKED.
  Earlier test commands/budgets are preserved; exactly one new acceptance module
  was added to the Runtime workflow. This does not establish legal clearance.

These runs are Linux synthetic evidence only. No actual provider, production
ledger, recorder/Lab, lifecycle/count/scoring operation, holdout, frozen study or
owner-ruling action was executed. MD5 is compatibility identification, not
security/authentication or proof of source/price/adjustment rights. The separate
series SHA256 framing and full R3 semantics remain unresolved by this unit.
No failing executed test is recorded for this bounded implementation; that does
not erase earlier failures in other units.

Final PR85 source `8e6db5b0b385d486596e51dd94d155c4847cd3de` has Runtime
`42208104232` all six completed/success and Compliance `42208104307` success.
The independent observer confirmed full job completion, including post-job and
Complete job steps, at 11:38:19 UTC. Each of the four installed-platform logs
shows the 15 data-hash tests passing within its 245-test aggregate: Windows
3.11 26.103 seconds, 3.12 21.913 seconds, 3.14 25.085 seconds and Ubuntu
15.961 seconds. Counts overlap; these are not additional unique tests. The hosted
numeric job-exit field was not exposed; the recorded result is whole-job success.

The source head, CI merge checkout `88f38811c322421c66b777743e2688b30e2793bd`
and final main merge `6ddf5146695de739e9f1ee5e2be609efd9d7be4c` have the same
Git tree `f0534744fd88eea3cf3a0eb48c3fc5a2b720d453`, verified by the owning
execution. PR/main read-backs and bounded LEDGER completion were recorded;
CURRENT/local completion at 20:38:44 KST and both task-page data-hash-only strikes
at 20:41:24 KST were read back. This establishes this detached child, not full R3.

## Preserved failure/correction history

1. A3 Windows source `67a8838` overflowed by 286 pixels. An inactive-tab correction
   still had Monte Carlo minimum-width/overflow failures. An intermediate
   three-column/minimum-width solution passed focused tests but an independent
   18px/1000px render still overflowed by 14. Later measured 3→2→1 reflow passed
   the recorded focused/independent checks; earlier failures remain real.
2. The old fixed-width forced-overflow local suite was 30 PASS + 1 baseline FAIL,
   83.636 seconds, exit 1. It reproduced on the unchanged baseline. New UI82's
   actual-viewport test and separate 5 PASS are different source/test evidence,
   not a retrospective conversion to 31 PASS.
3. A3 source `f7b4a73` had installed-platform assertion successes but Windows3.14
   printed 31 OK then exited 1; other Windows jobs reached a time boundary.
   Test-only exact-receiver cleanup reduced retained windows/controllers to
   zero. The old shutdown cause remains unproven. Intermediate cleanup errors
   are preserved; final successful CI is separate evidence.
4. Rates `578d35d406cd6001190d0400caeab7f93cab3096`, Runtime `42191259285`, and
   identity `b79d56d5aedd0a7d854421c933d87b31338e5177`, Runtime `42191579626`,
   printed their A1 18-test successes then segfaulted with exit 139 on Ubuntu.
   Their whole workflows failed. Later test cleanup and final-head CI succeeded;
   neither printed OK nor Compliance alone made the old runs successful.
5. Status had a legacy expectation failure corrected in a later source. A
   separate integration invocation typo caused a loader error before a corrected
   run passed. Both are retained, with product and invocation failures distinct.
6. Identity initially accepted ASCII-case-equivalent FX self-pairs. The targeted
   refusal fix retained returned evidence strings; it did not change cost math.
7. An independent codec probe initially expected incorrect escaped-pointer sort
   order. Product lexical order was correct; the private fixture was corrected.
   That is a test-authoring failure, not a discovered codec defect.
8. An earlier status/Rates update overstated pending workflow completion and was
   corrected. Later actual final CI/merge evidence supports completion; the
   original overstatement is not evidence and is not silently erased.
9. A local state serialization trailing-escape error was repaired immediately
   with history preserved and parse/read-back verification under continuous
   ownership. It was an operational correction, not a code/ledger completion.
10. AI's initial 229 assertions were followed by cleanup exit 1; a later run had
    checker failures before final 239 PASS plus a separate overlapping 47 PASS.
    Redaction, advisory numeric checking and fixed-instruction limits remain.
11. Rates inline initially had 19 failed display subcases before the bounded
    correction and its final 11-test success. The failed receipt is retained.
12. Keys fixture generation first assumed incorrect family-grid counts, then
    refused an original stdlib `time` import because of its narrow test allowlist.
    Corrected generation passed. These setup failures do not show a missing
    `datetime` import, changed historical writer or product-key divergence.
13. A handoff draft overstated the store as enforcing event transitions and
    conflated the current writer's temporary-ledger run with historical-source
    in-memory fixture generation. Policy review corrected those reporting claims,
    including66 original grid positions ×2 costs =132 of151. Product code and
    test results were not changed by this document correction.

Do not delete, reclassify or overwrite these earlier receipts. A successful
later head is a new observation, not proof of an unverified old failure cause.

## Next safe actions and ownership continuity

1. Reconcile latest CURRENT, saved task/branch/commit and execution lineage before
   further actions. Repeated operating text is steering, not permission to take
   over another owner; `from=gpt` alone is not ownership.
2. Preserve PR84 a083 final CI, merge9660352, bounded LEDGER/CURRENT/local-state
   read-backs and both task-page strikes. These are complete; do not redo them.
3. Preserve PR85 8e6 final CI, merge6ddf514, source/CI/main tree equivalence,
   bounded LEDGER/CURRENT/local-state read-backs and both task-page strikes.
   These are complete; do not repeat the merge or create duplicate completion.
4. The owning execution records the final recoverable checkpoint through latest
   CURRENT blob/head CAS and execution read-back, preserving existing LEDGER
   history and atomically saving local progress, next safe start and identifiers
   before lock release. This document does not itself mutate ownership.
5. This checkpoint closes the two completed units for this prolonged execution;
   no further large unit starts here. Remaining R3 work has existing approval.
   No actual hard runtime limit, token balance or new blanket approval blocker
   is asserted. A subsequent source change requires its own relevant checks.
6. A partial checkpoint is not weekly `returned`: do not apply cooldown, change
   next eligibility or postpone directly assigned work to Thursday. At a later
   continuation, validate task/claim/execution lineage, local state, environment
   and private access, obtain the prescribed OS exclusive lock and reconcile
   latest same-ref six handoff documents/history/LEDGER. Resume only through
   latest-SHA CAS and remote execution read-back. A foreign lock/taken owner or
   uncertain lineage requires stopping rather than claiming work.
7. A genuine weekly return remains a separate remote state change with detailed
   handoff/read-back. This checkpoint proves neither that return nor a receiving
   session's acknowledgement. Preserve earlier pause and bootstrap evidence.

A new large R3 unit is not part of the current two-unit closing plan. After
PR84/85 completion records and latest ownership/LEDGER are reconciled, the next concrete
candidate is a **detached supplied-source raw/LF SHA256 helper** under the already
approved source-identity work (§3.3), before the larger series store. A proposed
child name is `⑨-3a/source-digests/1`; it is not claimed/reserved by this checkpoint.

That small unit would accept caller-supplied text/bytes and return raw and
CRLF-pairs-to-LF digests. Preserve lone CR, whitespace, BOM, trailing-newline
presence and Unicode; strict UTF-8 for text. Do not strip/dedent/normalize an AST,
add hash framing, inspect live functions, read files/git/environment or collect
actual protected strategy sources. A separately authorized collector would be
needed for real strategy provenance. Recheck the current tree for an equivalent
helper before claiming; the existing provenance collector has different
side effects and a different recipe and must not be silently repurposed.
Meaningful synthetic checks include independently fixed literal digests,
CRLF/LF/mixed/lone-CR cases, empty/BOM/Unicode/final-newline inputs, strict
refusals, no mutation and no I/O/clock. No new dependency or Lab hook is needed.

Subsequent approved engineering preparation remains distinct:

- Series store (§5.7): write a concrete format/API note and independent literal
  fixtures for dtype/shape/hash framing, endian/raw-bit policy, packed metadata,
  existing-target integrity, atomic-write failure behavior and bounded retry
  semantics. Do not assume the data-MD5 recipe or hash an NPY file and call it
  the array-content hash. Use only caller-specified temporary paths initially;
  no deletion/default-path/environment behavior is implied.
- Lifecycle/fold (§5.6): write a transition and nested-payload contract before
  code. Preserve event-order/stage refusals, strict more-than-six-hours orphan
  boundary with explicit supplied time/evidence, and the existing human-ruling
  authority and previous terminal status. The envelope codec never claimed full
  payload validity; do not silently tighten its existing contract. Keep file
  access, counting and owner effects separate from any pure supplied-event fold.

These framing/API/table choices are ordinary engineering work within approved
R3, **not a newly established owner-approval blocker**. The owning engineer can
make explicit, reviewable choices within the existing contract. Do not ask the
owner again for blanket R3 approval or call all of R3 blocked. Changes to an
approved persistent contract, research criterion or authority rule must remain
separate proposals. Actual damaged-ledger recovery, permission-specific reruns,
Lab-page preconditions, formal recording and real research execution retain
existing decisions/limits; synthetic helper tests do not grant those permissions.
No next unit is implemented, claimed or marked complete by this checkpoint.

## Reproduction boundaries

Run only selected maintained suites in an isolated checkout with the existing
approved offline runner: temporary mutable directories/settings, dotenv
suppressed, providers/socket access blocked, actual protected data/ledger paths
refused. Keep the source untouched and preserve each log and process exit code.
Do not run the blanket suite, actual ledgers, frozen studies or provider probes.

For the current R3 helper stack, the maintained module names are:

```text
python -B <approved-offline-runner> <isolated-checkout> tests.run_registry_codec_acceptance tests.run_registry_store_acceptance tests.run_registry_keys_acceptance tests.run_registry_data_hash_acceptance
```

For the recorded UI integration, the selected names are:

```text
python -B <approved-offline-runner> <isolated-checkout> tests.desktop_watchlist_acceptance tests.desktop_markets_watchlist_acceptance tests.desktop_typography_acceptance tests.stock_profile_acceptance
python -B <approved-offline-runner> <isolated-checkout> tests.desktop_responsive_tools_acceptance
```

The runner and checkout placeholders must resolve to authorized existing
isolated tooling; they are not product paths or instructions to create a new
environment. Tests in a newer tree are new evidence. Retain the earlier local
uncommitted-tree provenance and exact CI heads instead of retrospectively
assigning their results to a different source.

## Genuine remaining evidence and approvals

- Hosted installed Windows checks do not prove physical user Windows installation,
  DPI, IME, manual keyboard or screen-reader behavior. Linux offscreen geometry
  and font tests are useful bounded evidence, not those missing observations.
- Real source parity, market/adjustment conventions, model/API access, billing,
  supplier entitlement and data accuracy remain unverified here. Existing API
  error handling does not prove a specific key/account can call a real model.
- Policy consistency checks retain publication BLOCKED. Actual legal, license,
  operator/business and data-rights evidence remains separate; no external
  release, site application, HTML publication or deployment is claimed.
- No real order path, formal ledger, pilot, preregistration, holdout, frozen
  study, scoring threshold or owner-confirmation operation was changed/executed
  by these detached helpers. Existing technical/Windows and execution gates
  remain in force.
- Additional external GPT/Gemini specification disclosure/review remains optional
  and `NOT_PERFORMED`; it is not marked passed and its absence alone does not
  block Windows handoff. Internal implementation review is distinct from that
  optional external specification process.
- Whole Remaining Work and R3 remain incomplete. A receipt for a merged child,
  registered automation, queue count or historical success is not whole-project
  completion. Preserve earlier local monitoring pause and all existing recovery
  evidence; no duplicate schedule or immediate forced run was created.

This document contains newly written implementation/progress summaries for
review. It neither copies private research source material nor includes account
information, connection identifiers, environment/session identifiers or private
filesystem paths. Ownership/checkpoint mutations are recorded separately through
the repository's required CAS/read-back procedure; this report is not a receiving
session's acknowledgement or a weekly return.
