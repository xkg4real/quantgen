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

Child **⑨-3a/fold/2** (2026-11-11) records the owner's rulings 8 and 9 on two
questions this page had left open (section "Questions"). The fold's behaviour
is unchanged: only docstrings, test comments and one test's coverage changed.

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
  `SingleSegmentStore.read()` returns, or its first n events, is accepted as is,
  including non-ASCII text such as Korean symbols or error messages (the codec
  writes UTF-8 without escapes, and the fold re-encodes the same way). The key
  order of the caller's dicts does not matter: the canonical line sorts keys.
- Refused with `FoldError`, naming the event index: misordered, spliced, edited,
  duplicated or interior-dropped events, a slice that starts mid-chain (its first
  `prev_row_md5` is not null, also when it starts at a later run's STARTED),
  events without chain fields, non-dict items, and any event that does not
  re-encode to the verified canonical line (NaN, values JSON cannot encode such as
  sets or bytes, non-string or mixed keys, lone surrogates). Every chain refusal
  reads `event N: not a verified prefix of segment 0 (...)`.
- A value that re-encodes to the identical line, such as a tuple where the codec
  wrote a list, is accepted. The fold then folds the codec's decoded copy, so the
  result always comes from the verified bytes, never from the caller's objects.
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
PROGRESS stage. A last PROGRESS stage that differs from `stage_reached`, above or
below it, adds STATUS_STAGE_CONFLICT (scoping rule 3). No PROGRESS at or above
`stage_reached` also adds PROGRESS_MISSING, because the page writes a closing
PROGRESS at DISPLAYED or at the failure stage (5.3). A finished run with no
PROGRESS at all has no stage to compare, so it gets PROGRESS_MISSING only. Age is
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
in `open_by_family` and listed in `open_run_ids` (5.6: "left out of counts, with
a warning"). Owner ruling 8 of 2026-11-11 decided this: OPEN runs are in TOTAL,
and the separate OPEN report is what meets 5.6. TOTAL is family-wide only.

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
- **(f) TOTAL is family-wide only and includes OPEN runs** (owner ruling 8,
  2026-11-11); market-scoped TOTAL is deferred because runs that fail before
  PNL_COMPUTED have no market.
- Refinements of the scoping contract that change no count, recorded here:
  PROGRESS_MISSING is also set on a finished run of any status whose PROGRESS
  never reached `stage_reached` (rule 3 names it only for COMPLETED without a
  DISPLAYED PROGRESS); it is added next to STATUS_STAGE_CONFLICT, never instead
  of it. FAILED_AFTER_STATS below PNL_COMPUTED is flagged STATUS_STAGE_CONFLICT.
  An absent `planned` is treated as null. OPEN runs carry no keys. The result
  also reports `as_of`, `events_folded` and `tail_line_md5`. An outage orphan's
  REGISTERED_KEYS_MISSING is rule 5 applied as written (its keys are `planned`).
- Whole-fold refusals beyond the scoping list in rule 2 (a PROGRESS without a
  stage is within rule 2, since an absent stage is outside STAGES): `registered`
  in a PROGRESS whose stage is not PNL_COMPUTED, or in a second PROGRESS of the
  run; a non-STARTED event whose `family_id` differs from the run's STARTED; and
  a FINISHED `displayed` that is present and neither a bool nor null. They are
  kept because each would otherwise be folded silently from an ambiguous or
  malformed record (which `registered` to use; a run under two families; a
  `displayed` that is not a bool). The cost is that one such recorder defect
  refuses the whole prefix, not just one run. These refusals and the flag
  refinement above have not been reviewed by the critic or the owner; see
  question 3 below.

Design tension, now decided: 3.12 counts every STARTED event in TOTAL, while 5.6
says OPEN runs are left out of counts. This child follows 3.12 for TOTAL and
reports OPEN separately, and owner ruling 8 of 2026-11-11 confirmed that reading
(question 1 below).

## Questions

Questions 1 and 2 were put to the owner on 2026-11-11 as items 8 and 9 of a
decision table and are decided. The table, the owner's reply and how each answer
is taken are in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, section "2026-11-11,
Claude Code 채팅: 남은 결정 14건에 대한 답 (원문)". Question 3 was not in that
table and stays open. Neither ruling changes the fold's code.

1. **3.12 versus 5.6 (OPEN in TOTAL): decided, ruling 8.** The table's item 8 was
   "실행 중인 기록을 전체 수(TOTAL)에 넣을지", recommended "넣음(3.12, 현행 유지).
   시행 횟수를 적게 세면 과최적화를 덜 걸러냅니다. 5.6의 의도는 별도 표시 칸으로
   이미 충족됩니다." The owner answered "8-승인". As recorded in the log: "실행
   중(OPEN)인 기록을 전체 수에 넣습니다(설계 3.12, 현행). 5.6의 "제외"는 별도
   OPEN 수 표시로 충족한 것으로 봅니다." So `total_by_family` keeps counting OPEN
   runs, and `open_by_family` and `open_run_ids` keep reporting them separately.
   The test `test_open_runs_count_in_total_and_are_reported_separately` pins both.
2. **Outage orphan with a PROGRESS below PNL_COMPUTED: decided, ruling 9; the
   current rule is kept.** An orphan older than 6 hours whose last PROGRESS is
   below PNL_COMPUTED folds to FAILED_BEFORE_STATS with no keys, even when an
   outage record names it, because 5.6 gives an orphan the stage of its last
   PROGRESS and the outage rule applies only with no PROGRESS (scoping rule 4).
   Example: STARTED, PROGRESS DATA_LOADED, outage record, no FINISHED. The table's
   item 9 was "손익 계산 전 단계의 장애 기록", and its recommendation was the
   fail-closed alternative ("보수적으로 처리(fail closed): 장애 기록이 있으면 시행
   1회로 집계합니다"). The owner did not take the recommendation and answered
   "9-현행유지". As recorded in the log: "손익 계산 전 단계에서 끊긴 장애 실행은
   지금처럼 FAILED_BEFORE_STATS로 접습니다(Claude 권장인 fail closed는 채택하지
   않음). 이에 따라 기록기 단위는 `run_family` 안에서 PNL_COMPUTED보다 낮은 진행
   기록(PROGRESS)을 쓰지 않아야 합니다. 쓰게 되면 과소 집계가 생기므로 그때 다시
   여쭙니다."

   What follows from it. Under design 5.3 the kept rule cannot hide statistics:
   inside `run_family` the recorder writes only STARTED and the PNL_COMPUTED
   PROGRESS, and a failed append disables the recorder for the run (6.4), so a
   later PROGRESS below PNL_COMPUTED can only be the page's closing PROGRESS
   after `run_family` raised there. If a recorder wrote an in-run PROGRESS below
   PNL_COMPUTED (the scoping hook list names cost_resolved and data_loaded), an
   outage at the PNL_COMPUTED append would be under-counted. The recorder unit
   must therefore not write one inside `run_family`; if it needs one, the question
   goes back to the owner before that PROGRESS is written. The fail-closed
   alternative (an outage record with a last stage below PNL_COMPUTED counted as
   FAILED_AFTER_STATS with STAGE_UNKNOWN and planned keys) is not implemented.
   The test
   `test_outage_record_changes_neither_finished_runs_nor_orphans_with_progress`
   pins the kept rule for each of the three stages below PNL_COMPUTED
   (REQUESTED, COST_RESOLVED, DATA_LOADED).
3. **Acceptance of the refinements and extra refusals** listed in the deltas:
   still open, for the orchestrator or critic, to be recorded in the handoff
   document. It was not among the 14 items the owner answered on 2026-11-11.

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

- `tests.run_registry_fold_acceptance`: **47 tests**, Python 3.13, three runs of
  0.484 s, 0.510 s and 0.471 s (runner elapsed), exit 0 each; also 47 passed on
  Python 3.11 (0.397 s) and 3.12 (0.497 s). With `time.tzset` deleted before the
  run, to imitate Windows, 47 passed on 3.11, 3.12 and 3.13. Each of the nine
  test classes also passed when run alone. The tests include a 288-case property
  check that a conflict never lowers the effective status, a static import and
  name check, a call with `open`, `os.open`, `os.getenv`, `time.*`, `time.tzset`
  (a failing stand-in is created where the platform has none, as on Windows) and
  `socket.connect` patched to raise under a scoped audit hook, Korean text and
  reordered keys folded from the canonical bytes, and one round trip (with a
  Korean symbol) through `SingleSegmentStore` in a fresh temporary directory
  under a scoped audit hook that confines file access to that directory.
- Combined R3 run (fold 47 + series files 45 + series format 22 + series hash 15
  + source hash 8 + data hash 15 + keys 13 + store 16 + codec 17): **198 tests in
  4.198 s, exit 0**; `tests.runtime_syntax_acceptance` 1 test, exit 0. A first
  combined attempt failed 2 series-files tests because the scratch runner lacked a
  `__main__` guard, so spawned children replayed it; the runner was fixed and no
  product file changed.
- Mutation run on scratch copies: **63 of 63 mutants killed**, each under
  `PYTHONHASHSEED` 0, 7 and 11; the 8 mutants from the review round below were
  also killed under each of seeds 0 to 15. The first run killed 55 of 55 after one
  test was strengthened (a dict-subclass mutant had survived).
- Review round (same day, before merge): a review found that the purity test
  errored where `time.tzset` does not exist (all three Windows Runtime jobs), that
  the round-trip class failed when run alone (the codec's lazy `strptime` import
  read a standard-library file inside the temporary-root guard), and five
  surviving mutants: an unchecked first link, `ensure_ascii=True`,
  `sort_keys=False`, a refusal of decreasing `recorded_utc`, and an unsorted
  `unmatched_outage_run_ids` (survived under hash seed 7). Tests were added or
  changed for each, finished-run flags were aligned with scoping rule 3, and the
  questions above were recorded as open. No count or effective status changed.
- The module and test compiled on Python 3.11, 3.12 and 3.13, and
  `ast.parse(feature_version=(3, 10))` accepted them. A real 3.10 compile is the
  CI syntax job. Windows was not run locally.

Child fold/2 (2026-11-11, rulings 8 and 9). The module's code is identical
before and after apart from docstrings (its AST without docstrings was compared
with the previous commit's). The existing test for ruling 9 now also checks
REQUESTED and COST_RESOLVED: a scratch mutant that failed closed only below
DATA_LOADED survived the previous test and is killed by the extended one, while
mutants for the full fail-closed alternative and for OPEN runs left out of TOTAL
were already killed. `tests.run_registry_fold_acceptance`: still **47 tests**,
Python 3.13 three runs of 0.472 s, 0.377 s and 0.384 s, and 3.11 and 3.12 (0.362 s
each), exit 0 each, run with plain `python -B -m unittest` on Linux. Windows was
not run locally.

The Runtime workflow adds the new source and test paths and runs the new module
first in the existing R3 unittest command; every earlier entry and its order are
kept. Final-head Windows/Ubuntu Runtime and Compliance results must pass before
merge. Publication readiness remains BLOCKED. Optional additional GPT/Gemini
specification review remains NOT_PERFORMED.
