# PT-07 loader revalidation — bounded CAL-13 / M-4 change

Base: main `950f25edd196189eac50a2ca39d5ff952656f353`. Work item: ①-2/4/a.
This implements the input-validation portion of ①-2/4; the parent item is not marked fully complete.

The owner delegated a useful PT-07 redesign in `OWNER_RULINGS_LOG.md` (2026-10-29),
and the handoff requested revalidation of the draft assessment. No signed data,
signature fingerprints, manifest schema, research criterion or approval policy is changed.

## Changes

- A local SafeLoader subclass refuses YAML 1.1 sexagesimal integers/floats before they
  become a numeric time such as 780. Quoted times, ordinary numbers and plain `09:30`
  strings retain their prior behavior. Global PyYAML constructors are unchanged.
- File-envelope `signed_utc` must be a valid ISO UTC instant with `T`, seconds and
  `Z` or `+00:00`. Dates, naive timestamps, nonzero offsets and invalid calendar dates
  are refused. This does not authenticate the signing time or add CAL-14's manifest binding.
- The signing tool validates every requested draft before any write and reports a
  malformed time as `SignRefused`. The synthetic test checks byte preservation,
  including CRLF, when a valid draft precedes an invalid one.
- Two T-CAL-01 fixture tests and their registry entries were added. CAL-12 and CAL-14
  remain outside this patch; no re-signing was performed.

## Verification performed

The two new tests failed on the prior loader with `expected CalendarUnsigned`, then passed.
Selected calendar, integration and point-in-time tests were compared with the unchanged
calendar source in the inherited branch (`0a91f26`, same calendar implementation as main).

| Check | Before | After |
|---|---:|---:|
| Selected tests PASS | 49 | 51 |
| Selected tests FAIL | 0 | 0 |
| Selected tests NOT_RUN | 12 | 12 |
| Original 61 test outcomes changed | — | 0 |
| Shipped calendar files accepted | 17/17 | 17/17 |
| Calendar set version | 1.0.0 | 1.0.0 |

The final comparison used `tests.macro_acceptance.hermetic()` around each selected test,
disabled dotenv loading, blocked direct yfinance/requests calls and refused protected
file reads with a Python audit hook. The first exploratory selected run did not wrap the
existing hermetic context: data-bound tests attempted Yahoo requests, which the shell
network sandbox refused. The comparison above was subsequently repeated with explicit
network blocking; no successful vendor retrieval is asserted.

All changed Python files passed AST parsing. `git -c core.whitespace=cr-at-eol diff --check`
passed; original CRLF conventions were retained. The signed calendar data directory has
no diff. The source QA result file was not regenerated.

**Full suite: NOT_RUN.** The current task excludes frozen-study and real-ledger access;
an unrestricted full-suite run would exceed that scope. The handoff's full-suite
PASS→FAIL criterion is therefore still pending, not inferred from these selected checks.
The owner-only signing/approval fields and any production ledgers remain untouched.

## Rollback

Revert this patch on its GPT branch; no data migration or signature repair is needed.
Main and the Claude work branch have not been modified by this patch. No PR or release
was created automatically.
