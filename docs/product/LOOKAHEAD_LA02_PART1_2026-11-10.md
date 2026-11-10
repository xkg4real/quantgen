# Look-ahead audit LA-02, part 1 (⑨-1/2/b)

This is the first part of the LA-02 fix from the 2026-11-04 look-ahead audit
(`git show 7749450:docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md`, LA-02 at lines 279-284). LA-02 says that the
reference-data (REFDATA) and owner-input point-in-time tests stay NOT_RUN on every machine, and that their bodies could
not become PASS even after the data arrives: some raise `NotRun` whatever is present, and some fail as "unreachable" or
"not implemented" straight after their fixture gate. This part changes test files only. No test changes status today:
every real-data test below is still NOT_RUN until ⑨-2 lists its fixture (or the owner extends a calendar file).

## Authority and scope

- Owner ruling L-2 (2026-11-04, `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:546`, verbatim):
  "L-2 = (가) 높음 2건(LA-01, LA-02)부터 별도 브랜치에서 수정 시작, 병합은 동결 해제 뒤 [권고]". The log maps it to ⑨-1 at
  `:553`. The main freeze was lifted on 2026-11-04 (U4-나).
- The owner's reply of 2026-11-10, "전부 승인합니노.", was relayed with this task. This part relies on L-2 for its scope.
  It does not take up I-05 (`tests/macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata`):
  a real I-05 body needs the LA-07 harness change and the LA-30 ALFRED vintages, and the data is not here.
- Scope as rescoped before work started: T-B5-01 (`tests/macro_m3_estimators.py:531`, a full estimator replay) moves
  to a later part, and `tests/macro_m1_fixtures.py:483` (T-RO-02, an owner live-quote record) is dropped from LA-02
  because it already asserts once the owner's run record exists.

## What changed

| Test | Before | Now |
| --- | --- | --- |
| T-PRINT-01 real closes, `tests/macro_m1_calendars.py::test_print01_real_kospi_close_2026_03_09` | `require_fixture` then `AssertionError("unreachable ...")` | Gate, parse F01 in the declared layout, computed owner-calendar check, then `_check_print01` |
| T-SAT-01 real closes, `tests/macro_m1_calendars.py::test_sat01_real_kospi_completeness_and_variance_ratio` | `require_fixture` then `AssertionError("unreachable")` | Gate, parse F01, computed owner-calendar check for 1997-01-03..2026-10-02, then `_check_sat01`; the 1997-98 variance ratio is printed |
| T-PLACEBO-01 positive control, `tests/macro_m7_cardp.py::test_placebo_01_positive_control_fixture_refdata` | `require_fixture` then `AssertionError("... not implemented")` | Gate, parse the declared layout (`session_date`, `kr_return`, `gate_m`, `multiplier`, `cost_bp`), then `_check_placebo01_control` |
| T-AVAIL-01 official calendars, `tests/macro_m1_pit.py::test_avail_01_official_calendars_are_owner_signed` | `NotRun` whatever the calendar files hold | Computes every refusal and coverage gap of the signed files the golden rows read; with none, runs the same golden table through `core.calendars.adapter.CalendarClocks`. Any coverage or signing error inside the table is then a FAIL |
| T-REGIME-01 full range, `tests/macro_m1_calendars.py::test_regime01_full_range_expected_values_file` | `NotRun` saying the shipped `kr_regime_tags.yaml` "is an unsigned draft" | Still `NotRun` (OWNER); the reason now ends with the file's signing state as read: "kr_regime_tags.yaml v1.0.0 is signed (2026-10-28T13:27:00Z, covers 1995-01-01..2027-12-31)" |

T-REGIME-01 stays an owner NotRun because its expected-values file `kr_regime_tags_expected.csv` has no row in
`tests/fixtures/macro/ACQUISITION.csv` or `MANIFEST.csv` and no generator produces it. A `require_fixture` on that name
would fail T-HERM-01 (`test_every_required_fixture_is_generated_or_registered`), and ACQUISITION.csv is not edited here.

The synthetic T-AVAIL-01 test now calls the same body, `_check_avail01_table(clk, clocks_for)`, with the stub clocks.
Its assertions are unchanged.

`AVAIL01_NEEDS` lists the signed files and the date range each golden row reads, and it is the contract for T-AVAIL-01 on
the official calendars. While anything is waiting, the test is NOT_RUN and names each gap. Once nothing is waiting, a
`CalendarCoverageError` or `CalendarUnsigned` raised inside the table is a FAIL, not a NOT_RUN. Such an error means the
adapter read a file or a date that the list does not declare, for example a calendar read past the golden day.

### Expected values and where they come from

`tests/fixtures/macro/goldens.csv` has no rows for these tests and is not edited. The values are declared in the tests
next to the spec lines they come from (`QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`):

- **T-PRINT-01** (L5631, L1382): the 2026-03-09 KOSPI close is 5,251.87, checked exactly (a price; Level 1 `price` is
  exact); the return against the previous session's row is -5.96% within the printed precision (±0.005 pp) and is not
  the -8.11% 10:31 print. The row must be the only one on that date, and `core.calendars.clocks.close_stamp` must accept
  its instants: `obs_utc` at the scheduled close, `available_at_utc` inside the close-print bound. An intraday print is
  refused as a close.
- **T-SAT-01** (L2097): no row lies outside the span; every `is_session` date has exactly one close row and no row falls
  on a non-session (`clocks.completeness_check`). No Saturday row lies on or after 1998-12-12, and the same rows without
  their Saturdays fail the check with exactly those Saturdays missing. On a calendar that agrees with the rows, the last
  two clauses fail only when the calendar's Saturday rule is wrong (no Saturday sessions, or Saturday sessions after
  1998-12-11). The Monday / Tue-Fri variance ratio of 1997-98 (2.30 in the spec, EX2) is printed, not asserted.
- **T-PLACEBO-01** (L3430, L3444, L3461; evidence L3474): the control trips, meaning LP is at least 0.20 (`cardp.LP_MIN`).
  The spec states this trip as the failure condition (L3430: "Otherwise T-PLACEBO-01 fails"; L3444 records 0.28 as
  observed). The body also asserts the dSR at L0 and at L1 as Level 1 points (Sharpe ±0.01, L5734) at +0.317 and +0.035.
  Those are the bracketed values in L3461 and L3474, and `goldens.csv` has no row for them. **Asserting them as points is
  this part's reading of L3461**, for the owner to confirm before ⑨-2 lists the fixture (question 3 below). A correct
  detector on the real R4 B3 file could otherwise FAIL on a Sharpe or cost-convention difference. The body prints LP,
  L0 and L1 before it checks them. There must be one family-ledger row per lag `[1, 2, 3, -1, 0]`, with the L ≤ 0 rows
  NON-COMPLIANT. The probe output must be tagged `synthetic_lookahead` with no lag-audit violation on an honest row. The
  probe runs only through `cardp.timing_probe(sandbox=True)` called from `tests/`.
- **T-AVAIL-01** (L2099, L5619, L3463): the existing four golden rows and the injected H.15-at-D registry error.

### Declared fixture layouts

Neither ACQUISITION.csv nor the spec names any columns, so each test declares the layout it reads. Each declaration is
an input contract that the owner can confirm or change when ⑨-2 builds the files.

- **F01** `krx_kospi_official_close_1997-01-03_2026-10-02.csv` (T-PRINT-01, T-SAT-01). `docs/macro_fixtures.py` writes
  the reference file's columns followed by the section 4.1 provenance columns. The test reads the reference close from a
  column named `close`. It also requires these provenance columns: `series_id = KOSPI_OFFICIAL_CLOSE`,
  `value_status = official_close`, `available_at_source = calendar_bound`, `obs_date = session_date` (ISO), and
  `obs_utc` / `available_at_utc` written `YYYY-MM-DDTHH:MM:SSZ`. Rows must be in date order.
- **`KR_SOX_KRW_gate_B3.csv`** (T-PLACEBO-01). One row per KRX session. The body reads `session_date`, `kr_return` (the
  overlay-off KOSPI return earned on that session), `gate_m`, and `multiplier` and `cost_bp`, which are repeated on every
  row. `gate_m` is the multiplier that R4 B3's rule sets from the inputs of the same date, which is the L = 0 timing that
  spec L1335 names as the forbidden case. The R4 B3 inputs and thresholds (`sox_close`, `usdkrw_close`,
  `sox_threshold`, `krw_threshold`) may ride along, but the body does not read or require them. The spec quotes R4 B3's
  rule but does not reproduce it (`research_notes/QUANTGEN v2 integration map/spec_M7_gate_package.md:686`, item 5), so
  the body cannot rebuild `gate_m` from the inputs. It trusts `gate_m`, refuses any value other than 1 or `multiplier`,
  and re-times `gate_m` by L. For a rule that reads its inputs' history the same way on every date, re-timing its output
  by L equals re-timing its inputs by L, which is what L3430 asks of `run(card, lag=L)`. A file built to
  ACQUISITION.csv:34's description alone (closes, thresholds, multiplier) fails at the layout check, "declared columns
  ['kr_return', 'gate_m'] absent" (question 1 below).

### Questions for the owner at ⑨-2

1. `KR_SOX_KRW_gate_B3.csv` must add `kr_return` and `gate_m`, which `tests/fixtures/macro/ACQUISITION.csv:34` does not
   list. ACQUISITION.csv is not edited here.
2. R4 B3's rule form (which inputs, the thresholds' units, how the multiplier applies). With it, a later part recomputes
   `gate_m` from the closes, the thresholds and the multiplier and asserts that it equals the column. Until then a file
   whose `gate_m` disagrees with its own inputs is not caught.
3. Whether T-PLACEBO-01 asserts L0 0.317 and L1 0.035 as Level 1 points (this part's reading of L3461) or only prints
   them, leaving the trip as the sole failure condition.
4. Whether F01's reference close is a column named `close`, as declared here.

### Demonstrations on invented data

Each body is shown to PASS and to FAIL on invented in-memory rows (no KRX, SOX, FRED or R4 B3 data):

Each FAIL case asserts the message of the clause it targets.

- `test_print01_body_passes_and_fails_on_invented_closes`: invented closes on the synthetic calendars. The pair
  5,584.71 → 5,251.87 passes. It fails when:
  - the 10:31 print (5,131.12, 01:31Z) is stored as the close ("not an official close") or beside it ("2 rows");
  - the close is 5,251.88 with correct stamps ("close 5251.88 != 5251.87 (spec L5631)");
  - the previous close is 5,560 ("return -5.5419% != -5.96%");
  - the 2026-03-06 row is missing ("no row for the previous session 2026-03-06").

  The owner-calendar gate `_official_calendar(lo, hi, live)` returns a covering synthetic set. On a set whose
  `holidays_KRX.yaml` is unsigned, it raises the NotRun "OWNER: ... holidays_KRX.yaml refused (...)".
- `test_sat01_body_passes_and_fails_on_invented_closes`: one close per session from 1997-01-03 to 1998-12-31, Saturdays
  included, passes. It fails when:
  - the Saturday closes are dropped (completeness);
  - the stated span ends before the last row;
  - on a calendar config with no Saturday sessions, the rows lack Saturdays ("do not fail the completeness check");
  - on a config with Saturday sessions until 1999-07-03, the rows carry 1998-12-12 ("a Saturday close on or after
    1998-12-12").

  The gate names the gap of a synthetic set whose `holidays_KRX` covers 2026-27 only, as the shipped file does. The
  wrong-rule calendars are new `CalendarSet` objects with an injected config; no module global is patched.
- `test_placebo_01_control_body_passes_and_fails_on_invented_rows`: an invented gate on synthetic returns, read on
  same-session inputs, trips the control. Its parameters were chosen so that L0 = 0.3173 and L1 = 0.0300, within
  Level 1 of the spec values; LP = 0.287. It fails when:
  - the same gate is read on the previous session's inputs (LP 0.026, "did not trip");
  - a same-session gate on the KR return below -3% trips with L0 0.334;
  - the same gate below -3.4% trips with L0 0.315 but L1 0.062;
  - a probe wrapper drops the L = 0 ledger row, or files the L = -1 row as COMPLIANT;
  - one `gate_m` value is 0.9;
  - the file has only ACQUISITION.csv:34's columns.
- `test_avail_01_official_path_passes_and_fails_on_a_synthetic_signed_set`: on the calendar module's temp-dir set,
  signed by the test itself, nothing is waiting and the golden table passes through `CalendarClocks`. The same clocks
  over a registry with H.15 posted at D fail it. The waiting list is pinned exactly. On the 2026-27 `holidays_KRX` set it
  names only the 2015 row's gap and the CSAT row's gap. On the unsigned set it names the refusal for the three rows that
  read `holidays_KRX`.
- `test_regime01_full_range_reason_reads_the_signing_state`: the T-REGIME-01 full-range NotRun reason ends with the tag
  file's signing state as read now and, while the shipped file loads, never contains "unsigned draft". The state text is
  checked on a signed and on a refused synthetic set.

### Ratchet

`tests/macro_m1_fixtures.py::test_la02_converted_pit_bodies_stay_convertible` parses the named functions only, not
whole modules. Whole modules are excluded because the T-HERM-01 rule `test_no_golden_test_passes_on_its_fixture_gate_alone`
still allows other golden tests to "fail as not implemented" after their gate.

- **`LA02_CONVERTED`** (4 functions). Each must have no NotRun that runs whatever the inputs: none at the top level, none
  inside `with` or the `try` body, and none under an `if` or `while` whose test is a constant (`if True:`). It must
  also have no NotRun before its fixture gate. No raised exception may say "unreachable" or "not implemented", in any
  letter case and on any exception class, and there may be no `NotImplementedError` and no constant-false `assert`.
  It must call a module `_check_*` function that asserts. The parking rules also apply to every module function it calls,
  followed through the module's own functions. That covers the gate helpers `_official_calendar` and `_avail01_waiting`.
- **`LA02_REMAINING`** (13 functions). Each must still exist and still be unconverted.
- **Frozen sets.** `LA02_SITES` holds the 17 sites and is never edited. `LA02_CONVERTED_FLOOR` holds the 4 conversions
  of this part. The two lists must partition `LA02_SITES`, and `LA02_CONVERTED` must contain the floor. So a converted
  site cannot move back to `LA02_REMAINING`, and no site can be added. A later part that converts a site adds it to the
  floor as well. `LA02_REMAINING` only shrinks; the guarantee rests on the floor not being lowered, which a reviewer sees.

The 17 sites are the 18 that the ⑨-1/2 scoping cited for LA-02, less the dropped T-RO-02 test.
`test_la02_ratchet_refuses_the_old_forms` checks the rules on invented source snippets. The snippets include each
evasion the review found: `if True: raise NotRun`, `RuntimeError("unreachable")`, `AssertionError("Unreachable")`, a
gate helper with `if True:`, and a converted site moved back to the remaining list.

## What did not change

- No file under `core/` changed. That includes the frozen harness sources (`core/quant/strategies.py`, `validate.py`,
  `cardp.py`, `docs/macro_overlay_study.py`) and `gate_package.HARNESS_SOURCES`, so `definitions_md5` is unaffected.
- No data, registry or record file changed: `tests/fixtures/macro/goldens.csv`, `ACQUISITION.csv` and `MANIFEST.csv`,
  `tests/macro_registry.csv`, `qa/acceptance_results.json`, `data/macro`, the calendars, ledgers, cards and registers.
- Every existing test keeps its name and its `test_ids`, so the `implemented_in` column stays in sync. The seven new
  tests carry no `test_ids`.
- The new and changed tests read `tests/fixtures/macro` only through `require_fixture`, and the shipped calendar files
  only for their signing and coverage state or as the official calendar. None of them reads
  `docs/asset_expansion/cache`. The whole `tests/macro_m1_pit.py` module does read it, in an existing test this part does
  not change: `test_stale_01_schedule_aware_clauses_and_local_smoke` opens
  `docs/asset_expansion/cache/fred_DEXKOUS.csv` (`tests/macro_m1_pit.py:674-679`) for its local DEXKOUS smoke. Running
  `tests.macro_m1_pit` whole therefore touches the cache.
- On the next owner QA run, the NOT_RUN reasons of T-AVAIL-01 (official calendars) and T-REGIME-01 (full range) will read
  differently. The counts will rise by the seven new tests (PASS where they run).

## Review fixes (second commit)

A review of the first commit (`7ba714d`) made ten findings. All ten are fixed in a second commit; nothing was amended.

- **T-PLACEBO-01 inputs.** The body read `gate_m` only, yet it required the SOX and USD/KRW closes and the thresholds,
  and nothing constrained them. Those columns are no longer required, and the owner questions above record that the
  file must add `kr_return` and `gate_m`. A FAIL case now pins the `gate_m` ∈ {1, multiplier} check. The rule form
  for recomputing `gate_m` waits for the owner.
- **FAIL cases for the spec values.** The demonstrations now fail on each value clause: the close, the return, the
  previous session, the Saturday clauses and the span, L0 alone, L1 alone, the ledger lags, the ledger timing class,
  and the layout.
- **Ratchet evasions.** The ratchet now refuses `if True: raise NotRun`, `RuntimeError("unreachable")` and
  `AssertionError("Unreachable")`, and it follows helpers. The frozen floor makes "only shrinks" hold: a converted site
  moved back to the remaining list fails.
- **T-AVAIL-01 errors.** A coverage or signing error raised inside the table, after nothing is waiting, is a FAIL.
- **Cache sentence.** It now covers the new and changed tests only, and names the existing DEXKOUS cache smoke in
  `tests/macro_m1_pit.py`.
- **`_official_calendar`.** It takes `live`. Both demonstrations pin both branches, through `_official_calendar_on`, so
  a NotRun on a covering set fails.
- **T-PLACEBO-01 L0 and L1.** The Level 1 point checks stay. They are recorded as this part's reading of L3461 for the
  owner to confirm.
- **NotRun reasons.** `test_regime01_full_range_reason_reads_the_signing_state` pins the T-REGIME-01 reason. The
  T-AVAIL-01 demonstration pins the exact waiting list.

## Verification (Linux, 2026-11-10, after the review fixes)

Tests ran one by one, by id, under a scratch runner that installs `sys.addaudithook`. The hook refuses any open,
listdir, scandir or mkdir under `docs/asset_expansion/cache`, any `.env` and anything under `~/.nextgen`, and it refuses
every `socket.connect`. The runner stubs `dotenv` before any import and runs each test inside
`tests.macro_acceptance.hermetic()`. Python 3.13.17, NumPy 2.3.5, SciPy 1.18.0. Result for the 17 named ids: 12 PASS,
5 NOT_RUN, 0 FAIL, with no refusal recorded.

- PASS:
  - the five demonstrations (four bodies, plus the T-REGIME-01 reason check);
  - the existing synthetic T-PRINT-01, T-SAT-01 and T-AVAIL-01 tests;
  - the two ratchet tests;
  - the T-HERM-01 rules `test_every_required_fixture_is_generated_or_registered` and
    `test_no_golden_test_passes_on_its_fixture_gate_alone`.
- NOT_RUN:
  - T-PRINT-01, T-SAT-01 and T-PLACEBO-01 on real data: REFDATA, the fixture is not in MANIFEST.csv.
  - T-AVAIL-01 on the official calendars: OWNER. `holidays_KRX.yaml` v1.0.0 covers 2026-01-01..2027-12-31, but the
    golden rows need 2015-01-01..2015-01-06 and 2025-11-13.
  - T-REGIME-01 full range: OWNER, with the corrected reason.
- **Mutation check.** A scratch driver applied 23 mutants to the four test files in place, ran the named ids for each
  under the guarded runner, and restored each file. The files were verified byte-equal afterwards. Every mutant was
  caught. The mutants cover each review finding:
  - the close, return and previous-session clauses (B1-B3);
  - the Saturday, late-Saturday and span clauses (B4 and two more);
  - `_official_calendar` with `if True:` (M18) and with `if False:`;
  - the stale T-REGIME-01 clause, appended or substituted (M17);
  - `_avail01_waiting` returning `[]` (M13), with coverage disabled (B8), or always reporting a gap (M19);
  - the L0 and L1 points, the trip, the ledger lags, the timing class and the `gate_m` check (B5-B7, M11);
  - the ratchet evasions C1, C2, C3 and C5.

  Under M13 and B8, T-AVAIL-01 on the official calendars now FAILs with `CalendarCoverageError`, where it used to report
  NOT_RUN. The first commit's five ratchet mutants (all caught) are described in this record as of that commit
  (`git show 7ba714d:docs/product/LOOKAHEAD_LA02_PART1_2026-11-10.md`).
- **End-to-end scratch probe** (not part of the suite): `require_fixture` was monkeypatched to invented files, and the
  real test functions were run on them.
  - T-PRINT-01 passed on the shipped signed calendar with 5,251.87, and failed with 5,251.88 ("close 5251.88 !=
    5251.87 (spec L5631)").
  - T-SAT-01 stopped at OWNER: `holidays_KRX` starts in 2026.
  - T-PLACEBO-01 passed on the look-ahead rows and failed on the honest rows ("did not trip"). It failed at the layout
    on a file with ACQUISITION.csv:34's columns only ("declared columns ['kr_return', 'gate_m'] absent").
- **Static checks.** Against `main` (`ed8df4a`) and against the first commit, every touched module carries the same
  `test_ids` per function and ends with the guarded `run_module` main. The CRLF files `tests/macro_m1_fixtures.py` and
  `tests/macro_m7_cardp.py` stay CRLF.

### Not run, and unverified

- `tests/run_all.py`, the whole macro modules, `tests.macro_m9_lab` and `tests.macro_m8_pipeline` were not run.
- `tests/macro_m0_harness.py::test_registry_implemented_in_matches_test_ids` was not run, because it imports every macro
  module, including those two. That it still passes rests on the static `test_ids` comparison above.
- Windows behaviour is unverified, and no CI runs the macro suites.
- The declared layouts are this part's assumption, and the owner questions above are open. Whether the ⑨-2 files will
  have these columns (in particular a reference column named `close`, and `kr_return` and a precomputed `gate_m`) is
  unverified.
- Whether R4 B3 rebuilt as declared reproduces L0 0.317 and L1 0.035 within ±0.01 cannot be checked without the file.
  Whether `gate_m` agrees with its own inputs is not checked until the owner gives the rule form.
- The audit's count of 19 LA-02 tests is not reproduced; the ratchet lists 17 named sites.

## Next parts (⑨-1/2/c onward)

Still unconverted, as listed in `LA02_REMAINING`:

- T-B5-01;
- G-POST-01 (two tests);
- T-PRINT-01 on Yahoo ^KS11;
- G-STALE-01;
- T-MISS-01;
- T-VT-01;
- T-LABEL-01;
- G-REF-01;
- T-CLOSE-02 on the signed files;
- T-REGIME-01 full range, which needs an ACQUISITION row for the expected-values file;
- T-FIX-01, which needs the council archive outside the repository;
- I-05, which needs LA-07 and the LA-30 vintages.

Each conversion moves its function from `LA02_REMAINING` to `LA02_CONVERTED`, adds it to `LA02_CONVERTED_FLOOR`, and
adds a PASS/FAIL demonstration with a FAIL case per value clause.
