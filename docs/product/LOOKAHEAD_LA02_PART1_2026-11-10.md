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
| T-PLACEBO-01 positive control, `tests/macro_m7_cardp.py::test_placebo_01_positive_control_fixture_refdata` | `require_fixture` then `AssertionError("... not implemented")` | Gate, parse the declared layout, then `_check_placebo01_control` |
| T-AVAIL-01 official calendars, `tests/macro_m1_pit.py::test_avail_01_official_calendars_are_owner_signed` | `NotRun` whatever the calendar files hold | Computes every refusal and coverage gap of the signed files the golden rows read; with none, runs the same golden table through `core.calendars.adapter.CalendarClocks` |
| T-REGIME-01 full range, `tests/macro_m1_calendars.py::test_regime01_full_range_expected_values_file` | `NotRun` saying the shipped `kr_regime_tags.yaml` "is an unsigned draft" | Still `NotRun` (OWNER); the reason now reads the file's signing state (signed v1.0.0, 2026-10-28T13:27:00Z, covers 1995-01-01..2027-12-31) |

T-REGIME-01 stays an owner NotRun because its expected-values file `kr_regime_tags_expected.csv` has no row in
`tests/fixtures/macro/ACQUISITION.csv` or `MANIFEST.csv` and no generator produces it. A `require_fixture` on that name
would fail T-HERM-01 (`test_every_required_fixture_is_generated_or_registered`), and ACQUISITION.csv is not edited here.

The synthetic T-AVAIL-01 test now calls the same body, `_check_avail01_table(clk, clocks_for)`, with the stub clocks.
Its assertions are unchanged.

### Expected values and where they come from

`tests/fixtures/macro/goldens.csv` has no rows for these tests and is not edited. The values are declared in the tests
next to the spec lines they come from (`QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`):

- **T-PRINT-01** (L5631, L1382): the 2026-03-09 KOSPI close is 5,251.87, checked exactly (a price; Level 1 `price` is
  exact); the return against the previous session's row is -5.96% within the printed precision (±0.005 pp) and is not
  the -8.11% 10:31 print. The row must be the only one on that date, and `core.calendars.clocks.close_stamp` must accept
  its instants: `obs_utc` at the scheduled close, `available_at_utc` inside the close-print bound. An intraday print is
  refused as a close.
- **T-SAT-01** (L2097): every `is_session` date has exactly one close row and no row falls on a non-session
  (`clocks.completeness_check`). Every Saturday row lies before 1998-12-12, and the same rows without their Saturdays fail
  the check with exactly those Saturdays missing. The Monday / Tue-Fri variance ratio of 1997-98 (2.30 in the spec, EX2)
  is printed, not asserted.
- **T-PLACEBO-01** (L3430, L3444, L3461; evidence L3474): the control trips, meaning LP is at least 0.20 (`cardp.LP_MIN`).
  This is the pass condition. The dSR at L0 and at L1 must be within the Level 1 Sharpe tolerance (±0.01, L5734) of
  +0.317 and +0.035. There must be one family-ledger row per lag `[1, 2, 3, -1, 0]`, with the L ≤ 0 rows NON-COMPLIANT.
  The probe output must be tagged `synthetic_lookahead` with no lag-audit violation on an honest row. The probe runs
  only through `cardp.timing_probe(sandbox=True)` called from `tests/`.
- **T-AVAIL-01** (L2099, L5619, L3463): the existing four golden rows and the injected H.15-at-D registry error.

### Declared fixture layouts

Neither ACQUISITION.csv nor the spec names any columns, so each test declares the layout it reads. Each declaration is
an input contract that the owner can confirm or change when ⑨-2 builds the files.

- **F01** `krx_kospi_official_close_1997-01-03_2026-10-02.csv` (T-PRINT-01, T-SAT-01). `docs/macro_fixtures.py` writes
  the reference file's columns followed by the section 4.1 provenance columns. The test reads the reference close from a
  column named `close`. It also requires these provenance columns: `series_id = KOSPI_OFFICIAL_CLOSE`,
  `value_status = official_close`, `available_at_source = calendar_bound`, `obs_date = session_date` (ISO), and
  `obs_utc` / `available_at_utc` written `YYYY-MM-DDTHH:MM:SSZ`. Rows must be in date order.
- **`KR_SOX_KRW_gate_B3.csv`** (T-PLACEBO-01). One row per KRX session: `session_date`, `kr_return` (the overlay-off
  KOSPI return earned on that session), `sox_close` and `usdkrw_close` dated that session, `gate_m`, and four rule
  parameters repeated on every row: `sox_threshold`, `krw_threshold`, `multiplier` and `cost_bp`. `gate_m` is the
  multiplier that R4 B3's rule sets from the inputs of the same date, which is the L = 0 timing that spec L1335 names as
  the forbidden case. The spec quotes R4 B3's rule but does not reproduce it
  (`research_notes/QUANTGEN v2 integration map/spec_M7_gate_package.md:686`, item 5). Whoever builds the fixture
  therefore applies the rule. The test re-times `gate_m` by L and refuses a `gate_m` value other than 1 or `multiplier`.

### Demonstrations on invented data

Each body is shown to PASS and to FAIL on invented in-memory rows (no KRX, SOX, FRED or R4 B3 data):

- `test_print01_body_passes_and_fails_on_invented_closes`: invented closes on the synthetic calendars. The pair
  5,584.71 → 5,251.87 passes. The 10:31 print (5,131.12, 01:31Z) fails whether it is stored as the close or beside it.
- `test_sat01_body_passes_and_fails_on_invented_closes`: one close per session from 1997-01-03 to 1998-12-31,
  Saturdays included, passes. The same rows without their Saturdays fail.
- `test_placebo_01_control_body_passes_and_fails_on_invented_rows`: an invented gate on synthetic returns, read on
  same-session inputs, trips the control. Its parameters were chosen so that L0 = 0.3173 and L1 = 0.0300, within
  Level 1 of the spec values; LP = 0.287. The same gate read on the previous session's inputs gives LP = 0.026, and the
  test asserts that the body raises the AssertionError "did not trip".
- `test_avail_01_official_path_passes_and_fails_on_a_synthetic_signed_set`: on the calendar module's temp-dir set,
  signed by the test itself, nothing is waiting and the golden table passes through `CalendarClocks`. The same clocks
  over a registry with H.15 posted at D fail it.

### Ratchet

`tests/macro_m1_fixtures.py::test_la02_converted_pit_bodies_stay_convertible` parses the named functions only, not
whole modules. Whole modules are excluded because the T-HERM-01 rule `test_no_golden_test_passes_on_its_fixture_gate_alone`
still allows other golden tests to "fail as not implemented" after their gate.

- **`LA02_CONVERTED`** (4 functions). Each must have no `NotRun` at the top level of its body and no NotRun before its
  fixture gate. It must have no "unreachable" or "not implemented" failure and no `assert False`, and it must call a
  module `_check_*` function that asserts.
- **`LA02_REMAINING`** (13 functions). Each must still exist and still be unconverted, so the list only shrinks.

The two lists together hold 17 sites: the 18 sites that the ⑨-1/2 scoping cited for LA-02, less the dropped T-RO-02
test. `test_la02_ratchet_refuses_the_old_forms` checks the rule on invented source snippets.

## What did not change

- No file under `core/` changed. That includes the frozen harness sources (`core/quant/strategies.py`, `validate.py`,
  `cardp.py`, `docs/macro_overlay_study.py`) and `gate_package.HARNESS_SOURCES`, so `definitions_md5` is unaffected.
- No data, registry or record file changed: `tests/fixtures/macro/goldens.csv`, `ACQUISITION.csv` and `MANIFEST.csv`,
  `tests/macro_registry.csv`, `qa/acceptance_results.json`, `data/macro`, the calendars, ledgers, cards and registers.
- Every existing test keeps its name and its `test_ids`, so the `implemented_in` column stays in sync. The six new
  tests carry no `test_ids`.
- The tests read `tests/fixtures/macro` only through `require_fixture`, and the shipped calendar files only for their
  signing and coverage state or as the official calendar. They never read `docs/asset_expansion/cache`.
- On the next owner QA run, the NOT_RUN reasons of T-AVAIL-01 (official calendars) and T-REGIME-01 (full range) will read
  differently. The counts will rise by the six new tests (PASS where they run).

## Verification (Linux, 2026-11-10)

Tests ran one by one, by id, under a scratch runner that installs `sys.addaudithook`. The hook refuses any open,
listdir, scandir or mkdir under `docs/asset_expansion/cache`, any `.env` and anything under `~/.nextgen`, and it refuses
every `socket.connect`. The runner stubs `dotenv` before any import and runs each test inside
`tests.macro_acceptance.hermetic()`. Python 3.13.17, NumPy 2.3.5, SciPy 1.18.0. Result: 11 PASS, 5 NOT_RUN, 0 FAIL,
with no refusal recorded.

- PASS: the four demonstrations, the existing synthetic T-PRINT-01, T-SAT-01 and T-AVAIL-01 tests, the two ratchet tests,
  and the T-HERM-01 rules `test_every_required_fixture_is_generated_or_registered` and
  `test_no_golden_test_passes_on_its_fixture_gate_alone`.
- NOT_RUN:
  - T-PRINT-01, T-SAT-01 and T-PLACEBO-01 on real data: REFDATA, the fixture is not in MANIFEST.csv.
  - T-AVAIL-01 on the official calendars: OWNER. `holidays_KRX.yaml` v1.0.0 covers 2026-01-01..2027-12-31, but the
    golden rows need 2015-01-01..2015-01-06 and 2025-11-13.
  - T-REGIME-01 full range: OWNER, with the corrected reason.
- **Ratchet mutation check** (a scratch copy of the test files): it caught all five mutants. They were: T-PRINT-01
  reverted to "unreachable"; an unconditional NotRun added to T-AVAIL-01; the T-PLACEBO-01 body call removed; a remaining
  function renamed; and a remaining function converted without moving it to the converted list. The first version of
  the last mutant was built wrongly: it called a `_check_*` function that the module does not define, so it was not a
  conversion. The ratchet still counted that function as unconverted, which is correct, and the rebuilt mutant was
  caught.
- **End-to-end scratch probe** (not part of the suite): `require_fixture` was monkeypatched to an invented file, and the
  real test functions were run on it.
  - T-PRINT-01 passed on the shipped signed calendar.
  - T-SAT-01 stopped at OWNER: `holidays_KRX` starts in 2026.
  - T-PLACEBO-01 passed on the look-ahead rows and failed ("did not trip") on the honest rows.
- **Static checks**: before and after, every touched module carries the same `test_ids` per function and ends with the
  guarded `run_module` main.

### Not run, and unverified

- `tests/run_all.py`, the whole macro modules, `tests.macro_m9_lab` and `tests.macro_m8_pipeline` were not run.
- `tests/macro_m0_harness.py::test_registry_implemented_in_matches_test_ids` was not run, because it imports every macro
  module, including those two. That it still passes rests on the static `test_ids` comparison above.
- Windows behaviour is unverified, and no CI runs the macro suites.
- The declared layouts are this part's assumption. Whether the ⑨-2 files will have these columns (in particular a
  reference column named `close`, and a precomputed `gate_m`) is unverified.
- Whether R4 B3 rebuilt as declared reproduces L0 0.317 and L1 0.035 within ±0.01 cannot be checked without the file.
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

Each conversion moves its function from `LA02_REMAINING` to `LA02_CONVERTED` and adds a PASS/FAIL demonstration.
