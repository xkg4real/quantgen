# R3 detached run lifecycle fold

This is bounded child **⑨-3a/fold/1** of the approved R3 implementation (owner
rulings: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:302` and `:320`, which approve
R3 design revision 2 and the 10.2 A build questions at their stated defaults). It
adds `core/quant/run_registry_fold.py`: a pure, in-memory fold of machine events
into one lifecycle record per run, with the family-wide TOTAL and the OPEN runs.
It is not connected to the Lab, the recorder, any actual registry or ledger,
configuration, provider or owner-decision effect. It classifies no trial and
counts no N_raw or N_eff. Nothing consumes its output yet (Q17, shadow only).
The R3 parent remains open.

## Design reference

R3 design revision 2, blob `7ca8411f5f02b48bee35ff28291acd2f171a4001`
(`fa28059:docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`;
not on main): 3.12 (TOTAL), 3.13 (`as_of`), 5.2 (chain), 5.3 (event types), 5.6
(statuses, stages and the 6-hour orphan rule) and 4.3 steps 1 and 7. It builds on
the merged codec (`run_registry_codec.py`) and is checked against the merged
single-segment store (`run_registry_store.py`).

## Chain-trust boundary

The fold does not trust the caller's order. It re-encodes every supplied event to
its canonical line and passes the lines to the codec's `verify_event_lines` with
no predecessor. Each line must decode canonically with a matching `row_md5`, and
each `prev_row_md5` must be the MD5 of the line before it, starting from null.

- Accepted: a prefix, cut by position, of one segment-0 chain. The tuple
  `SingleSegmentStore.read()` returns, or its first n events, is accepted as is.
- Refused with `FoldError`, naming the event index: misordered, spliced, edited,
  duplicated or interior-dropped events, a slice that starts mid-chain, events
  without chain fields, non-dict items, and anything that cannot be re-encoded
  (NaN, non-JSON values, non-string or mixed keys, lone surrogates).
- Not detectable: removal of a complete suffix. That is how a caller cuts the chain
  at an earlier position, so the result names the prefix it folded:
  `events_folded` and `tail_line_md5` (the MD5 of the last folded line, which is
  the `prev_row_md5` the next event carries).
- MD5 detects inconsistent bytes; it is not authentication. The fold works on the
  freshly decoded copies, never on the caller's dicts, and never modifies input.

## Time: prefix by position, guard by `as_of`

`as_of` must be an exact `datetime` with UTC offset zero; naive, other-offset,
`date`, string and `datetime`-subclass values are refused. The result stores it
normalised to `timezone.utc`.

The fold never cuts by time. The caller chooses the prefix by position (for
example the chain length known at a ledger snapshot or at a card's anchored
commit, design 3.13 and Q21), and passes the instant it represents. Inside that
prefix, an event whose `recorded_utc` is after `as_of` is refused as a guard, so a
prefix and an instant that disagree cannot be folded. The order of `recorded_utc`
values along the chain is not checked: chain order rules, because each writer
stamps its own event before the lock.

## API

`fold_runs(events, *, as_of, outage_run_ids=frozenset()) -> Fold`

- `events`: a list or tuple of event dicts (the prefix above).
- `outage_run_ids`: a `frozenset` of valid LAB run IDs that an outage record names.
  Any other type or an invalid ID is refused.

`Fold` (frozen dataclass): `as_of`, `events_folded`, `tail_line_md5`, `runs`
(STARTED chain order), `total_by_family` and `open_by_family` (read-only mappings
sorted by family ID; `open_by_family` lists every family, 0 when none is open),
`open_run_ids` (chain order) and `unmatched_outage_run_ids` (sorted).

`RunRecord` (frozen dataclass): `run_id`, `family_id`, `started_utc` (as
recorded), `status`, `status_source` (`FINISHED`, `INFERRED` or `NONE`), `stage`,
`effective_status`, `flags` (sorted tuple), `keys` (tuple of `(theta_index,
config_id)` or None), `keys_source` (`registered`, `planned` or None),
`displayed` (FINISHED `displayed`, or None) and `event_count`.

Constants: `STAGES` (ordered), `FINISHED_STATUSES`, `EFFECTIVE_STATUSES`,
`FOLD_EVENTS` (equal to the store's `MACHINE_EVENTS`), `FLAGS`,
`ORPHAN_AGE = timedelta(hours=6)`. Errors: `FoldError(ValueError)`.

## Structural refusals

The whole fold is refused, naming the event index, when:

- the event is not STARTED, PROGRESS, FINGERPRINT, SHADOW or FINISHED (human
  events and SEGMENT_START are refused, so SUPERSEDED is never produced);
- a run's first event is not STARTED; a second STARTED or FINISHED; any event after
  FINISHED;
- STARTED `family_id` is missing or differs from the family segment of the run ID,
  or a later event's `family_id`, when present, differs from it;
- a PROGRESS without a known `stage`, a stage lower than the run's previous
  PROGRESS (equal stages are allowed), or a FINISHED `stage_reached` outside
  `STAGES`;
- a FINISHED `status` outside COMPLETED, FAILED_BEFORE_STATS, FAILED_AFTER_STATS,
  ABORTED, or a FINISHED `displayed` that is present and not a bool or null;
- `planned` or `registered` that is not null and not a list of exactly
  `{theta_index: int >= 0 (not bool), config_id: 32 lowercase hex}`; `registered`
  in a PROGRESS whose stage is not PNL_COMPUTED, or in a second PROGRESS of the run.

## Lifecycle rules

| Case | status / source | effective_status | flags |
| --- | --- | --- | --- |
| FINISHED COMPLETED | COMPLETED / FINISHED | COMPLETED, always | STATUS_STAGE_CONFLICT when the stage is not DISPLAYED; PROGRESS_MISSING when no DISPLAYED PROGRESS |
| FINISHED FAILED_BEFORE_STATS | as recorded | FAILED_AFTER_STATS if the stage is PNL_COMPUTED or later (with STATUS_STAGE_CONFLICT), else FAILED_BEFORE_STATS | |
| FINISHED FAILED_AFTER_STATS | as recorded | FAILED_AFTER_STATS, always | STATUS_STAGE_CONFLICT when the stage is below PNL_COMPUTED |
| FINISHED ABORTED (recorded) | ABORTED / FINISHED | FAILED_AFTER_STATS at PNL_COMPUTED or later, else FAILED_BEFORE_STATS | |
| No FINISHED, age <= 6 h | OPEN / NONE | OPEN | none; keys None |
| No FINISHED, age > 6 h, with PROGRESS | ABORTED / INFERRED | by the last PROGRESS stage, as above | |
| No FINISHED, age > 6 h, no PROGRESS, not in outage set | ABORTED / INFERRED | FAILED_BEFORE_STATS | STAGE_INFERRED; stage None |
| No FINISHED, age > 6 h, no PROGRESS, in outage set | ABORTED / INFERRED | FAILED_AFTER_STATS | STAGE_UNKNOWN; stage None |

For a finished run the stage is the larger of `stage_reached` and the last
PROGRESS stage. A PROGRESS stage above `stage_reached` adds STATUS_STAGE_CONFLICT.
No PROGRESS at or above `stage_reached` adds PROGRESS_MISSING, because the page
writes a closing PROGRESS at DISPLAYED or at the failure stage (5.3). Age is
`as_of` minus the STARTED `recorded_utc`; exactly 6 hours is still OPEN. A
conflict can raise FAILED_BEFORE_STATS to FAILED_AFTER_STATS; it never lowers an
effective status (fail closed, map03 R-2b).

Keys. FAILED_BEFORE_STATS and OPEN carry no keys. Otherwise the keys are
`registered` from the PNL_COMPUTED PROGRESS. If that is absent or null, they are
`planned` with REGISTERED_KEYS_MISSING. If `planned` is also null or absent, keys
are None with KEYS_UNAVAILABLE. Duplicate positions are kept as supplied; counting
is out of scope.

TOTAL. `total_by_family` counts every STARTED event in the prefix, OPEN runs
included (3.12: "every status and every class counts"). OPEN runs are also counted
in `open_by_family` and listed in `open_run_ids`, so a later count can leave them
out (5.6: "left out of counts, with a warning"). TOTAL is family-wide only.

## Deltas from the design and the scoping contract

- **(a) Outage records by run ID.** Design 5.2 lists no `run_id` in an outage
  record, but 5.6 needs one. The caller passes the IDs; the future outage writer
  must store `run_id` once STARTED was appended. An outage ID for a run that has
  FINISHED or PROGRESS changes nothing.
- **(b) Structural violations refuse the whole fold**, as a broken chain does.
- **(c) FINISHED versus PROGRESS disagreements fail closed** (table above).
- **(d) `as_of` is a guard, not a cut.** The caller cuts by position; a later
  `recorded_utc` inside the prefix is refused (review correction).
- **(e) Machine events only**: human and SEGMENT_START events are refused, so the
  SUPERSEDED status and segment rollover stay with later children.
- **(f) TOTAL is family-wide only and includes OPEN runs**; market-scoped TOTAL is
  deferred because runs that fail before PNL_COMPUTED have no market.
- Refinements of the scoping contract, recorded here: a PROGRESS stage below
  `stage_reached` is PROGRESS_MISSING rather than a conflict; FAILED_AFTER_STATS
  below PNL_COMPUTED is flagged; `registered` is accepted only once and only at
  PNL_COMPUTED; an absent `planned` is treated as null; an orphan with outage
  keys also carries REGISTERED_KEYS_MISSING; OPEN runs carry no keys; the result
  also reports `as_of`, `events_folded` and `tail_line_md5`.

Design tension kept visible: 3.12 counts every STARTED event in TOTAL, while 5.6
says OPEN runs are left out of counts. This child follows 3.12 for TOTAL and
reports OPEN separately; whether a later count includes them is that unit's rule.

## Purity

The fold's own code performs no I/O and reads no clock, environment,
configuration or random source; it imports only standard-library modules and the
codec. The codec parses times with `datetime.strptime`, whose standard-library
cache may call `time.tzset` once when it is first built in a process. The fold
parses `recorded_utc` from the codec-validated text without `strptime`.

## Boundaries

No recorder, outage writer, ledger link, canonical panel, fingerprint, lineage,
experiment key, trial class, N_raw, N_eff, shadow row, human event, segment,
report, Lab or UI integration is implemented. No verdict, GATE, card, ledger,
register, frozen file or holdout is read or changed. The eight existing helpers
(codec, store, keys, data hash, source hash, series hash, series format, series
files) are unchanged. No 01-20 policy row changes: the fold stores nothing.

## Verification

All local checks ran on Linux in a guarded runner (an audit hook installed before
any test import that refuses any `open` of an `asset_expansion/cache` or `.env`
path and every `socket.connect`/`socket.getaddrinfo`; it recorded 0 refusals),
with `-B` and no bytecode, synthetic events only.

- `tests.run_registry_fold_acceptance`: **45 tests**, Python 3.13, three runs of
  0.446 s, 0.437 s and 0.512 s (runner elapsed), exit 0 each; also 45 passed on
  Python 3.11 (0.347 s) and 3.12 (0.481 s). The tests include a 288-case
  property check that a conflict never lowers the effective status, a static
  import and name check, a call with `open`, `os.open`, `os.getenv`, `time.*`,
  `time.tzset` and `socket.connect` patched to raise under a scoped audit hook,
  and one round trip through `SingleSegmentStore` in a fresh temporary directory
  under a scoped audit hook that confines file access to that directory.
- Combined R3 run (fold 45 + series files 45 + series format 22 + series hash 15
  + source hash 8 + data hash 15 + keys 13 + store 16 + codec 17): **196 tests in
  3.843 s, exit 0**. A first combined attempt failed 2 series-files tests because
  the scratch runner lacked a `__main__` guard, so spawned children replayed it;
  the runner was fixed and no product file changed.
- Mutation run on scratch copies: **55 of 55 mutants killed** (one test was
  strengthened after a first run in which a dict-subclass mutant survived).
- The module and test compiled on Python 3.11 and 3.12, and
  `ast.parse(feature_version=(3, 10))` accepted them. A real 3.10 compile is the
  CI syntax job.

The Runtime workflow adds the new source and test paths and runs the new module
first in the existing R3 unittest command; every earlier entry and its order are
kept. Final-head Windows/Ubuntu Runtime and Compliance results must pass before
merge. Publication readiness remains BLOCKED. Optional additional GPT/Gemini
specification review remains NOT_PERFORMED.
