# Adoption strategy checks (⑨-4/2/a)

This is **⑨-4/2/a**, the first unit of the adoption module that owner ruling M-21 placed outside the Nautilus
fingerprint scope (`core/adoption/`). It adds `core/adoption/__init__.py` and `core/adoption/strategy_rules.py`:
pure functions that compute the strategy comparison lines S-2, S-3, S-4 and S-7 of the adoption criteria, the
borderline zones and the 2027-01-01 holdout guard, on daily OOS P&L arrays the caller supplies. It assigns no
adoption outcome, re-runs no gate, and is not connected to the Lab, the app, any ledger, card or register. The
parent item ⑨-4/2 stays open.

**⑨-4/2/b** (2026-11-11) names the N_raw reading of record after owner ruling 7: R-FAM, the R3 run-registry count.
Both readings are still shown and the second DSR stays provisional until the R3 recorder exists. No threshold,
status, gate or outcome rule changed; see the section "⑨-4/2/b" below. **⑨-4/2/b/2** (2026-11-11) is the
/code-review fix to it: the reading of record is stored in one place (the "/code-review fix" block of that
section).

**⑨-4/2/c** (2026-11-12) adds the outcome assembly, `strategy_outcome`: from the caller's gate verdict and the
collected lines it names one of the criteria 6.1 outcomes, under the owner's answers B-Q1, B-Q2 and B-Q3 of
2026-11-11, or names none (`NO_OUTCOME`, with the reason) where the criteria and the module leave the case
undecided. Every outcome is provisional. See the section "⑨-4/2/c" below.

## Sources and rulings

- Criteria: `docs/nautilus_bridge/MODEL_ADOPTION_CRITERIA_DRAFT_2026-11-04.md` (commits `c96f338`, `c814d22`),
  approved by the owner on 2026-11-10 ("전부 승인합니노.") and merged to main in PR #92 (`f4e034d`). Sections used:
  3.3 (locked holdout), 4.0 (common rules), 4.2.2 (S-2, S-3, S-4, S-7; add versus replace), 6.2 (borderline),
  6.4 (N12) and 8.2 (L1 note). The file name keeps the word DRAFT for existing references; its status line is
  lifted.
- Rulings (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, batch 2 of 2026-11-04 and the 2026-11-10 section):
  M-2 (one-sided 0.10), M-3 (나) (DSR at G and at the ledger N, provisional), M-4 (baselines as in table 2.3),
  M-6 (가) (`gate_stats.lw_studentized_boot`), M-11 (가) (borderline defined, never adopted), M-14 (가) (sample
  ends by 2026-12-31), M-19 (가) (add versus replace), M-20 (나) ("L1 미적용"), M-21 (가) (new module outside
  the fingerprint; its two preconditions are met per the M-21 memo and log reflection).
- 2026-11-10 owner answer, as recorded in the log: the meaning of "ledger N_raw" in M-3 was **not** decided
  (the question offered two readings). This unit therefore takes N_raw as a caller input under either or both
  readings, shows both, and labels the second DSR provisional.
- 2026-11-11 owner ruling 7 (log section "2026-11-11, Claude Code 채팅: 남은 결정 14건에 대한 답 (원문)"): the
  meaning is decided. R-FAM is the reading of record; until the R3 recorder exists both readings are still shown
  (⑨-4/2/b, below).
- This branch is based on main `ed8df4a`. PR #92 (docs only) merged after the branch point; it touches none of
  this unit's files.

## What it computes

All statistics come from existing functions; nothing in `core/quant` is edited (`git diff ed8df4a -- core/quant`
is empty).

| Function | Rule | Computation |
| --- | --- | --- |
| `check_sample_end(last_session)` | 4.0 rule 6, 3.3; M-14 | `holdout_touched = last_session > 2026-12-31`; `adopt_allowed = not holdout_touched`. Dates or ISO strings; a `datetime` is refused. |
| `gate_sr_sd_daily(full_pnl)` | S-2; M-3 | The gate's own dispersion term: population SD of the per-period full-sample Sharpe of each grid column, formed exactly as `validate.score_strategy` forms it (`validate.py:503-506`) with the same `validate._col_sharpe`. It reports the gate's value as is, including the case below. |
| `dsr_two_n(oos_daily, *, n_grid, sr_sd_grid, n_raw, sr_sd_daily, sr_sd_label)` | S-2, 6.2; M-3, M-11 | `validate.deflated_sharpe` at N = G with `sr_sd_grid` (the gate's term, so the line equals the gate's DSR) and at each supplied N_raw reading with the labelled `sr_sd_daily`, each against `GATE['dsr_min']`. The N_raw statuses are keyed on the N = G line. |
| `classify_dsr(value, *, grid_status)` | S-2, 6.2, 6.4 | `pass` at dsr_min or above; `borderline` in [0.90, dsr_min) only while the grid DSR passes; `below` otherwise; `nan` for a NaN DSR. |
| `lw_compare(challenger, other, dates, other_dates, *, rule, other_label, counts, B, seed)` | S-3, S-4; M-2, M-6, M-11, M-19 | `gate_stats.pw_block_psi` (max(21, PW(psi)), fallback 250 kept in `block_events`), `gate_stats.lw_studentized_boot` with B = `GATE['bootstrap_B']` (2000) and seed = `gate_stats.SEED_STUDY` (11), `p = gate_stats.p_numeric(p_lw, B)` ("< 1/B" compares as 1/B). Another B or seed (tests only) sets `conforms_to_registration=False` and the line says OFF-REGISTRATION (criteria 3.2 item 11). |
| `classify_comparison(d_sr, p)` | 4.0 rule 2, S-3, S-4, 6.2; M-2, M-11 | `win`: dSR > 0 and p <= 0.10; `borderline`: dSR > 0 and 0.10 < p <= 0.20; else `not_won`. |
| `power_line_s7(challenger, incumbent, dates, incumbent_dates, *, expected_dsr)` | S-7, 3.2 item 8, 5.3; M-6 | SE = `gate_stats.lw_hac_se(...).se`, MDE80 = `gate_stats.MDE_FACTOR` x SE, flag `MDE80 > expected dSR`, printed only. |
| `strategy_lines(*, kind, ...)` | 4.2.2, 2.3; M-3, M-4, M-6, M-11, M-14, M-19, M-20 | Collects S-2, S-3 (replacement: counts; addition: printed only), one S-4 per registered baseline (a series, or `CASH_BASELINE`, printed as replaced by the gate's Sharpe-interval check), S-7 and the holdout line into an immutable result with the L1 note and no outcome. B and seed are fixed at the registration's values; there is no override. |

Every result is a frozen dataclass whose collections are tuples. `lines()` renders the printable lines. The only
new constants are alpha 0.10, the borderline bounds 0.20 and 0.90, the last session 2026-12-31, the note
"L1 미적용(브리지 미지원)" (printed on the collected `strategy_lines` result) and the marker `CASH_BASELINE`;
`dsr_min` 0.95, B 2000, seed 11, the 21-session block floor and MDE factor 2.1232 are read from `validate.GATE`
and `gate_stats`.

## Readings and corrections applied

- **Two dispersion terms.** Criteria 6.2 makes the second DSR borderline only while the gate's DSR at N = G is
  0.95 or above, so the N = G line must be the gate's DSR: it always uses `sr_sd_grid`, the gate's own term
  (`gate_sr_sd_daily(full_pnl)`), and is printed as "[the gate's own term]". The R3 design (section 4.4) says the
  dispersion pairing "is a criterion", and 10.2 B Q1 reserves "which N, paired with which dispersion term" for
  ⑨-3d, so the N_raw lines take a separate `sr_sd_daily` with a required `sr_sd_label`, printed on each N_raw
  line. The caller may pass the gate's term there too, under its own label.
- **The gate's term is reproduced, not repaired.** A grid column that is constant up to floating noise and not
  zero (a configuration that stays in cash and earns the Lab's cash rate) has a sample SD at floating-noise level.
  The gate's term is then enormous (about 6e13 to 1.4e14 for cash rates 1e-4 to 3%/252 per day in a T 1400
  synthetic probe), and the public `validate.sharpe` computes the noise differently (0.016 to 2e15 in the same
  probe). `gate_sr_sd_daily` therefore uses `validate._col_sharpe`, the function `score_strategy` uses (validate.py
  is a frozen harness source), and equals the gate's term exactly; an exactly zero column gives Sharpe 0 in both.
- **Cash baseline (criteria 2.3, M-4).** Pairs (E8, S6) take cash as their baseline, and criteria 2.3 replaces
  that comparison with the gate's existing check that the Sharpe interval excludes 0, which is part of S-1. A
  constant cash series cannot be tested (the LW test refuses a zero-variance book), so `strategy_lines` accepts
  `baselines={"cash": CASH_BASELINE}` and prints "S-4 vs cash: REPLACED (...)" with status `replaced`; no LW test
  is run. A constant series passed as a baseline stays NOT_RUN, and its reason names `CASH_BASELINE`. PCA
  butterfly (B2) also has cash, but no gate daily P&L column (criteria 2.3: "구현 없음"), so it is outside this
  unit.
- **B and seed are the registration's.** Criteria 3.2 item 11 fixes seed 11 and B 2,000, and 6.4 says the
  adoption evaluation uses B 2,000. `strategy_lines` has no B or seed input. `lw_compare` keeps them for tests;
  any other value marks the result `conforms_to_registration=False` and its line OFF-REGISTRATION.
- **Two N_raw readings.** `N_RAW_READINGS` names `L-FAM` (family ledger row count, `FamilyLedger.n_raw`, read on
  the owner PC) and `R-FAM` (R3 design 3.13 literal family-wide count, |K| + |L minus cfg(K)|). The caller supplies
  one or both as integers >= 1; a reading not supplied is shown as "not supplied". The module never opens a
  ledger. Since ⑨-4/2/b, `N_RAW_READING_OF_RECORD` names R-FAM as the reading of record and each line prints its
  role.
- **N_raw below G is printed, not refused.** R3 design 10.2 B Q4 ("may a ledger-based N fall below G?") is
  reserved for ⑨-3d, so `below_grid` is a printed status. The scoping proposal to refuse it was dropped on review.
- **Direction applies to the borderline zone.** Criteria 6.2 names only the p range (0.10, 0.20]; this unit also
  requires dSR > 0, reading the zone as the near-miss of a win under 4.0 rule 2. With a null-centred one-sided p,
  p <= 0.20 and dSR <= 0 should not occur in practice; the rule only removes the corner.
- **S-7 is printed only.** M-6 did not answer whether MDE80 above the expected dSR turns S-3 into
  INSUFFICIENT_DATA (criteria section 9, decision 6). The SE is the LW-HAC SE that criteria 5.3 used, not
  `gate_stats.power_line`, which takes the macro cards' SE plateau and accepts only CARD-O and CARD-P.
- **A replacement must carry its expected dSR** (criteria 3.2 item 8); an addition may omit it. Whenever an
  expected dSR is supplied it must be finite and > 0; an addition that supplies one without an incumbent gets a
  note that no S-7 line is printed.
- **Input types.** P&L arrays must have an integer or float dtype: numeric strings, booleans, complex and object
  arrays are refused. A session string must match `YYYY-MM-DD` before `date.fromisoformat`, so the compact and week
  forms that Python 3.11 accepts and 3.10 refuses (`20270101`, `2027-W01-5`) are refused on every version.
- **Undefined statistics are NOT_RUN.** A zero HAC SE, a block longer than the sample or fewer than 30 sessions
  makes the comparison line `not_run` with the gate function's own reason. Misaligned or unequal sessions,
  non-finite values and bad counts are refused (`AdoptionInputError`), never trimmed.
- **Names kept clear of the static guard.** No code matches `gate_ledger.forbidden_patterns()` (the design-effect
  shape, its author's name, a revision count assigned to N); the test runs `scan_forbidden` on both the code-only
  and the raw text of `core/adoption/*.py`. `gate_ledger.record_adoption` (gate-package adoption) is a different
  concept and is not used.

## What it does not do

- No outcome (ADOPT, KEEP, REVISE, REJECT, INSUFFICIENT_DATA). Outcome assembly waits for owner answers: the gate
  passing at G with the second DSR below 0.90 (criteria 6.1 maps it to neither KEEP nor REJECT), whether S-7
  converts S-3, and which dispersion term pairs with N_raw. Which N_raw reading is of record was the fourth
  question; ruling 7 of 2026-11-11 answered it (R-FAM). The other three were answered on 2026-11-11 (B-Q1,
  B-Q3, B-Q2) and ⑨-4/2/c assembles the outcome; the collected lines of this unit still assign none.
- No S-1 (the gate is the caller's precondition), no S-5 SPA or S-6 break-even (`tf_gov`), no SMA-200 or 60/40
  baseline P&L (`core.quant.strategies` is never imported, so `config` and `.env` are never loaded), no forecast,
  risk, data or registration rules, no L2/L3.
- No file, ledger, clock, environment, network or process access. Imports: `core.quant.validate` and
  `core.quant.gate_stats` only (plus the standard library and numpy).

## Verification (local, synthetic)

Test module: `tests/adoption_strategy_rules_acceptance.py`, 32 tests, run through a scratch runner that installs
an audit hook refusing any `open` under `asset_expansion/cache` or a `.env` path and any `socket.connect`, and
replaces `dotenv.load_dotenv` with a no-op before imports.

- Python 3.13.17 (numpy 2.3.5, scipy 1.18.0), Linux, after the review fixes: 32 tests OK in 3.54 s, 3.98 s and
  3.89 s (three runs), and with `-W error::RuntimeWarning` once more OK. Together with the eight R3 modules that CI
  already runs in the same step (`tests.run_registry_*`), 183 tests OK in 8.3 s. Before the review fixes: 29 tests
  OK in 2.75 s, 3.06 s and 3.08 s, and 180 with the R3 modules in 5.7 s.
- Golden equality: S-2 values equal direct `validate.deflated_sharpe` calls; the N = G line with the gate's
  dispersion term equals `validate.score_strategy(...).dsr` exactly on a synthetic walk-forward, also when the
  N_raw lines use another labelled term (review case: gate DSR 0.9619 passes, L-FAM 17 at term 0.01595 is 0.9082
  and reads borderline; the contract review's case T 1260, G 12, terms 0.010 and 0.020 also reads pass and
  borderline); `gate_sr_sd_daily` equals the gate's term exactly, constant cash columns included; S-3/S-4 fields
  equal a direct `pw_block_psi` + `lw_studentized_boot` call (seed 11 and seed 12); S-7 equals `lw_hac_se`.
- Edges: p at 0.10 and 0.20 and the next float above each (also through resample counts 200, 201, 400, 401 of
  2000 with a stubbed bootstrap); DSR at 0.95 and 0.90 and the next float below each; "< 1/B"; a NaN DSR; N_raw
  below G; MDE80 equal to the expected dSR (not flagged) and the next float below it (flagged); sessions ending
  2026-12-31 versus 2027-01-01; misaligned, unequal, duplicate and reversed sessions; a challenger with fewer
  values than sessions; string, boolean, complex and object P&L; compact and week date strings; an addition's
  S-4 lines counting; the declared cash baseline; an off-registration B or seed.
- Scope: no `open`, socket, process or directory audit events while the functions run; `validate.GATE` and the
  gate functions unchanged after the run; an AST check that the module never assigns into or monkeypatches the
  gate; an isolated subprocess (`python -I`) importing the module loads only `core`, `core.quant`,
  `core.quant.validate`, `core.quant.gate_stats` and `core.adoption*`, and neither `config` nor `dotenv`.
- A mutation check (15 single-line mutants of the module: comparison edges, direction, borderline condition,
  holdout boundary, N_raw count passed, p source, alignment, block rule, MDE factor, datetime refusal, the
  replacement's expected dSR) was killed 15 of 15. The module was restored byte for byte afterwards. After the
  review fixes, 16 further single-line mutants on a scratch copy (the three that survived review: S-7 `>=`, an
  addition's S-4 not counting, the challenger's length check dropped; the two dispersion terms swapped or merged;
  the helper back on `validate.sharpe`; the cash marker ignored; the conformity flag forced or seed-blind; the
  dtype whitelist widened twice; the expected-dSR sign check and the date pattern removed; three earlier edges)
  were killed 16 of 16.
- `compile()` and `ast.parse(feature_version=(3, 10))` of the three new Python files pass under Python 3.11.17
  and 3.13.17, also after the review fixes (compilation only; Python 3.11 here has no numpy, and Python 3.10 itself
  was not available).
- A first combined run reported 2 failures in `tests.run_registry_series_files_acceptance` spawn tests; the cause
  was the scratch runner (no `__main__` guard, so spawned children re-ran the suite). With the guard added the
  same 180 tests pass. No product test failure was observed. The pre-review figures are from the first commit's
  final code, after a last change that wraps a non-numeric P&L input in `AdoptionInputError`; the first runs (29
  tests in 3.05 s, 2.60 s and 2.77 s; 180 in 5.6 s; 15 of 15 mutants) also passed.

Not verified here: the CI matrix (Windows Python 3.11, 3.12, 3.14; Ubuntu 3.12), Python 3.10 execution, and any
real P&L. The owner-PC values of N_raw and the gate's inputs are outside this unit.

## Review round 1 (second commit)

Nine review findings (two of them the same defect) were each reproduced on the first commit before the fix:

| Finding | Reproduced | Fix |
| --- | --- | --- |
| One dispersion term for both S-2 lines (major, reported twice) | T 1400, G 4: gate DSR 0.9619 (pass), but with the labelled term 0.01595 the module printed the N = G line as 0.9497 (below) and L-FAM 17 at 0.9082 as below; criteria 6.2 gives borderline | `sr_sd_grid` (the gate's term) for the N = G line, the labelled `sr_sd_daily` for N_raw only, N_raw status keyed on the gate's line; two tests with the reviewers' numbers |
| `gate_sr_sd_daily` differs from the gate on constant columns | cash 3%/252: gate 6.18e13, helper 2.07e15; 2.5%/252: gate 1.38e14, helper 0.0159 | uses `validate._col_sharpe` as the gate does; exact equality test on four cash rates; docstring and this page describe the floating-noise case |
| No path for the cash baseline | 0 and 3%/252 constant series: NOT_RUN ("a book has zero variance") | `CASH_BASELINE` marker, status `replaced`, line names criteria 2.3 and S-1; a constant series' NOT_RUN reason points to the marker; B2 out of scope |
| Any B or seed reported without a flag | B 50 printed a normal S-3 line | `conforms_to_registration` and an OFF-REGISTRATION line; `strategy_lines` has no B or seed input |
| Three surviving mutants (S-7 `>=`, an addition's S-4 `counts`, the challenger length check) | per the review's scratch mutation run | three tests; the three mutants are now killed |
| Loose input validation | numeric strings gave DSR 0.846, booleans 0.99999; `20270101` and `2027-W01-5` accepted on 3.13; an addition's `expected_dsr=-5` ignored | integer/float dtype whitelist; `YYYY-MM-DD` pattern before `date.fromisoformat`; `expected_dsr` checked whenever supplied, with a note when no incumbent |
| S-7 boundary untested | (same as the S-7 mutant) | `expected_dsr = mde80` is not flagged; the next float below is |
| `L1_NOTE` comment said "every result" | only `StrategyLines` carries it | comment and docstrings now say the collected `strategy_lines` result |

No finding was rejected.

## ⑨-4/2/b: R-FAM is the N_raw reading of record (2026-11-11)

The ruling. Item 7 of the decision table of 2026-11-11 asked for the meaning of "ledger N_raw" and the ⑨-4
questions Q1 to Q5 and Q7. Its recommendation was "R-FAM을 공식 기준으로 하고, R3 기록기가 완성될 때까지는 둘 다
표시(현행 유지). 시행 횟수를 크게 잡는 쪽이 더 보수적인 판정이고, R3의 목적이 원장 기반 시행 횟수입니다. Q1~Q5·Q7은
내용이 길어 별도 표로 다시 보고하겠습니다." The owner answered "7-권장대로 요청". The log takes this as the
recommendation (R-FAM of record, both readings shown until the R3 recorder is complete) together with a request
for the Q1 to Q5 and Q7 table, and asks the owner to say so if it meant something else. The Q table is reported
separately and is not part of this unit.

What changed in `core/adoption/strategy_rules.py`:

- `N_RAW_READING_OF_RECORD = "R-FAM"`, a key of `N_RAW_READINGS`.
- `RawReading.of_record` (True for R-FAM only) and `RawReading.role()`; `DsrTwoN.reading_of_record`. Since the
  /code-review fix below these are read-only values computed from the constant, not stored fields.
- The printed N_raw lines carry the role. With both readings supplied (synthetic input):

  ```
  S-2 [provisional] DSR at N_raw L-FAM = 17 [shown for comparison]: 0.9736 (pass); dispersion term 0.012 per period [caller term]
  S-2 [provisional] DSR at N_raw R-FAM = 11 [reading of record (owner ruling 7, 2026-11-11)]: 0.9774 (pass); dispersion term 0.012 per period [caller term]; N_raw 11 < G 12: printed only
  ```

  With R-FAM not supplied, its line reads "... [reading of record (owner ruling 7, 2026-11-11)]: not supplied; the
  reading of record was not supplied, so this result has no second DSR of record and stays provisional". A missing
  L-FAM reads "[shown for comparison]: not supplied".
- The provisional note now says that R-FAM is the reading of record and that both readings are shown until the R3
  recorder exists; it no longer says the meaning is undecided.

What did not change:

- No threshold, zone, status or gate rule. Each reading's DSR is still `validate.deflated_sharpe` at its own N
  with the caller's labelled dispersion term, classified by the same `classify_dsr` against the N = G line. The
  reading of record gets no different treatment, and `dsr_min`, 0.90, alpha and the borderline bounds are
  untouched. The module still assigns no outcome.
- Every result stays provisional (`provisional=True`), with or without R-FAM. No R3 recorder exists, so an R-FAM
  count is a caller input like L-FAM and does not come from the registry itself. Lifting the label belongs to the
  unit that connects the recorder (⑨-3c, ⑨-3d).
- Imports are the same (`core.quant.validate` and `core.quant.gate_stats` only), and `core/quant` is not edited.

Verification (local, synthetic, Linux, Python 3.13.17):

- `tests.adoption_strategy_rules_acceptance`: **33 tests** (32 before; one added, one extended), three runs of
  3.931 s, 3.614 s and 3.659 s and one with `-W error::RuntimeWarning` (3.599 s), all OK. The new test checks the
  constant, the role on each line with both, only L-FAM and only R-FAM supplied, the missing-record wording,
  `provisional=True` in each case, and that numbers and statuses equal direct `validate.deflated_sharpe` and
  `classify_dsr` calls, including a stubbed case where both readings sit in the borderline zone.
- Together with the fold, the series files and the seven other R3 modules: **239 tests in 7.338 s, OK**
  (overlapping; not added together).
- The static guard: `macro_m7_ledger::test_step3_02_no_ledger_hash_refused_and_no_kish_anywhere`, which scans
  `core/**/*.py` and `docs/**/*.py` with `gate_ledger.scan_forbidden`, passed in the guarded runner. The runner
  refused the test's two attempts to list `docs/asset_expansion/cache` (its guard does that by design), so files
  under that directory were not part of the scan, and the runner exits 1 for the recorded refusals although the
  test itself passed.
- Mutation run on a scratch copy: 11 single-change mutants (the constant set to L-FAM, roles swapped, the missing
  note dropped or put on the other reading, the flag never set, the role not printed, `provisional` False, the
  old "undecided" note, the reading of record classified without the grid line, the record line dropped when
  missing) were all killed by the reading-of-record tests. One unrelated test fails in the scratch copy because
  the copy has no schema JSON files; it passes in the repository and was not counted.
- `compile()` and `ast.parse(feature_version=(3, 10))` of the module and its test pass under Python 3.11.17,
  3.12.3 and 3.13.17; `tests.runtime_syntax_acceptance` passed.

/code-review fix (roadmap ⑨-4/2/b/2, 2026-11-11, pull request #100 at `e4b0772`): one source for the reading of
record. ⑨-4/2/b was closed when pull request #100 merged, so this fix has its own ID.

- The finding. The reading of record was stored three times: the constant, an `of_record` field on each
  `RawReading` and a `reading_of_record` field on `DsrTwoN`. `lines()` read only the per-reading field. Reproduced
  on `e4b0772`: `dataclasses.replace(result, reading_of_record="L-FAM")` gave a result whose field named L-FAM
  while its printed lines still named R-FAM as the reading of record.
- The fix. `N_RAW_READING_OF_RECORD` is the only place the reading of record is stored. `RawReading.of_record` and
  `DsrTwoN.reading_of_record` are read-only properties computed from it, and `role()` follows `of_record`. The
  constructors of both classes are those of main before pull request #100 (`7ddb568`): `RawReading` takes six
  arguments again, and `DsrTwoN` has no `reading_of_record` argument, so `dataclasses.replace` with either name
  raises `TypeError`.
- Correction from the verification of this fix. This block first said the constructors "are the ones main has".
  That was no longer true when the fix was committed (2026-11-10 20:15 UTC): pull request #100 had merged into
  main 26 minutes earlier (`1a8b29f`, 19:48 UTC), so main then had the `e4b0772` classes, with a seventh
  `RawReading` field (`of_record`) and a `DsrTwoN.reading_of_record` field. Checked with `dataclasses.fields` on
  both classes: the lists at this fix and at `7ddb568` are equal, and those at `e4b0772`, `1a8b29f` and the later
  main `96cca1f` are equal to each other and have the two extra fields. The code was right and only the sentence
  was wrong; the same wording is corrected in FACTS and in two comments of the test.
- The printed lines are the same text. The SHA-256 of all lines for three inputs (both readings, only L-FAM, only
  R-FAM) is equal before and after, and a new test pins the three S-2 lines in full for each input.
- Checks: `tests.adoption_strategy_rules_acceptance`, **35 tests** (33 before; two added), three runs of 3.691 s,
  4.215 s and 4.597 s and one with `-W error::RuntimeWarning` (3.754 s), all OK. The new one-source test fails on
  `e4b0772` and passes now. Together with the fold, the series files and the seven other R3 modules: 255 tests in
  10.129 s, OK (overlapping; not added together). Mutation run on a scratch copy: 11 of 11 killed (a stored field
  or flag put back, a second literal copy of "R-FAM" in either property, the flag always false or inverted, roles
  swapped, not printed or reworded, the constant set to L-FAM, the missing note on the other reading). The static
  guard `macro_m7_ledger::test_step3_02_no_ledger_hash_refused_and_no_kish_anywhere` passed in the guarded
  runner, which again refused the test's two listings of `docs/asset_expansion/cache` and therefore exits 1.
  `compile()` and `ast.parse(feature_version=(3, 10))` pass under Python 3.11.17, 3.12.3 and 3.13.17.

Not verified here: the CI matrix (Windows, Python 3.10 execution), any real P&L, and any real R-FAM or L-FAM
count. The R3 recorder that would produce R-FAM does not exist yet.

## ⑨-4/2/c: outcome assembly (2026-11-12)

### The rulings

Source: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, section "2026-11-11, Claude Code 채팅: 결정 요청 P·A·B·C·D
묶음에 대한 답 "전부승인"". The owner's answer, verbatim: "전부승인". The log takes it as every bundle approved
as recommended. The three rows this unit applies, verbatim (number, question, recommendation):

| 번호 | 내용 | 권장 (원문) |
| --- | --- | --- |
| B-Q1 | 둘째 DSR이 0.90 아래일 때 결과 이름 | 기각(REJECT)으로 적고 "잠정 기준" 표시. 기존 심사도 같은 점수 미달을 기각으로 처리합니다. |
| B-Q2 | 둘째 DSR에 쓸 분산 값 | 기존 심사와 같은 값으로 판정하고, 더 엄격한 값은 참고 줄로만 인쇄. 엄격한 값은 검증(⑨-3c) 전이라 판정에 쓰기 이릅니다. |
| B-Q3 | 검정력이 부족할 때 현직 비교 | 이겼더라도 "자료 부족"으로 두고 교체하지 않음. 힘이 부족한 검사의 승리는 우연일 가능성이 큽니다. |

The log's own reading, verbatim: "결과 조립 단위에서 Q1(REJECT, 잠정 표시)·Q2(게이트와 같은 분산 값으로 판정,
SE_null 짝은 참고 줄)·Q3(검정력 부족이면 이겼더라도 자료 부족)을 적용합니다." Q4 (forecast, Clark-West), Q5
(registration) and Q7 (60/40) belong to later units and are not implemented here.

### What it does

`strategy_outcome(*, gate_verdict, lines, reference_s2=None)` in `core/adoption/strategy_rules.py` is a pure
function: no I/O, no recorder, no UI, no new import. It takes the gate's own verdict (S-1, one of
`validate.DECISIONS`: PASS, REVISE, REJECT, INSUFFICIENT_DATA; a caller input, never re-decided), the
`strategy_lines` result of the same run, and optionally a `dsr_two_n` result of the same series with another
dispersion term. It recomputes no statistic and returns a frozen `StrategyOutcome`: `outcome` (one of `OUTCOMES`
= ADOPT, KEEP, REVISE, REJECT, INSUFFICIENT_DATA, or `NO_OUTCOME`), `basis` (the rule that named it, or why none
was named), the reason lines, the B-Q2 reference lines and the collected lines themselves (`strategy`, the same
object, unchanged). `provisional`, `provisional_basis` (B-Q1), `replaces_incumbent`, `not_covered` (`NOT_COVERED`
= S-5, S-6, D-4) and `kind` are read-only values derived from the outcome and the collected lines, not stored.
Before any step the collected lines are checked against what `strategy_lines` gives: every status must be one the
producing function gives and the one its own value gives (`classify_dsr`, `classify_comparison`), the S-7 line
must be against the S-3 incumbent with its flag equal to `MDE80 > expected dSR`, and the holdout line must equal
`check_sample_end` of its own last session; anything else is refused, never read as a win.

The rules, applied in this order:

| Step | Condition | Outcome | Source |
| --- | --- | --- | --- |
| 1 | Gate REVISE and the DSR at N = G is NaN | INSUFFICIENT_DATA | 6.4 N12 ("DSR NaN은 S-2 미충족, INSUFFICIENT_DATA") |
| 1a | Gate REVISE, R-FAM below 0.90 | REJECT, labelled "잠정 기준" | B-Q1; the gate rejects a DSR shortfall before REVISE (`validate.py:592-622`) |
| 1b | Gate REVISE, R-FAM not supplied, or R-FAM NaN while the gate's DSR is finite | NO_OUTCOME | B-Q1 may apply / N12 and REVISE are not ordered |
| 1c | Gate INSUFFICIENT_DATA with the gate's DSR passing, R-FAM below 0.90 or not supplied | NO_OUTCOME | the gate's sample floor comes before a DSR REJECT and its minimum record after it; the lines do not say which |
| 2 | Any other gate verdict that is not PASS | the gate's verdict | 6.1 (REVISE, REJECT, INSUFFICIENT_DATA rows) |
| 3 | Gate PASS, R-FAM (the reading of record) not supplied | NO_OUTCOME | ruling 7: L-FAM only compares |
| 4 | R-FAM DSR NaN | INSUFFICIENT_DATA | 6.4 N12 |
| 5 | R-FAM DSR below 0.90 (with the gate's dispersion term) | REJECT, labelled "잠정 기준" | B-Q1, M-3 |
| 6 | Replacement, S-7 MDE80 above the registered expected dSR | INSUFFICIENT_DATA, incumbent not replaced, whatever S-3 and S-4 say (each S-4 result is printed) | S-7, B-Q3, 4.2.2, 4.0 rule 5 |
| 7 | Replacement, S-7 not run | NO_OUTCOME | B-Q3 cannot be applied |
| 8 | R-FAM borderline [0.90, 0.95), or a counting S-3 / S-4 borderline or not won | KEEP | 6.1 KEEP ("경계 사례 포함"), 6.2, M-11 |
| 9 | A counting comparison not run | NO_OUTCOME | 6.1 names no outcome for it |
| 10 | Sample ends after 2026-12-31 (HOLDOUT_TOUCHED) | NO_OUTCOME | 4.0 rule 6, M-14: no ADOPT, and 6.1 names nothing else |
| 11 | Otherwise | ADOPT (basis "criteria 6.1 ADOPT (S-5, S-6, D-4 not checked)"); a replacement replaces the incumbent, an addition nothing | 6.1 ADOPT, 4.2.2, M-19 |

The counting comparisons are the S-3 of a replacement and every S-4 (criteria 4.2.2, M-19). An addition's S-3 is
printed only and never counted. A declared cash baseline (`replaced`, criteria 2.3) is met by the gate's PASS.

Printed form (synthetic input; the DSRs and the bootstrap are stubbed as in the tests):

```
⑨-4/2/c strategy outcome (replace) [provisional]: REJECT [잠정 기준]
S-1 gate verdict (the caller's): PASS; DSR at N = G = 12: 0.9700 (pass) [the gate's own term]
S-2 DSR at N_raw L-FAM = 17: 0.9600 (pass); shown for comparison; decides nothing (owner ruling 7)
S-2 DSR at N_raw R-FAM = 11: 0.8500 (below); the second DSR of record, with the gate's dispersion term (B-Q2)
B-Q1 (owner answer of 2026-11-11, "전부승인"): the second DSR of record is below 0.90: REJECT, 잠정 기준 (provisional (M-3): ...)
provisional (M-3): every outcome stays provisional while the second DSR is provisional (until the ⑨-3c report and ⑨-3d)
not part of this outcome: S-5 (SPA when one registration has more than one rule), S-6 (break-even cost) and D-4 are later units
```

### How each ruling is applied

- **B-Q1.** After a gate PASS or a gate REVISE, R-FAM below 0.90 is REJECT. The header carries "[잠정 기준]", the
  reason line carries the module's provisional note (M-3), and `provisional_basis` is True (it is True for basis
  B-Q1 only). A gate REJECT is not B-Q1 and carries no such label. L-FAM below 0.90 decides nothing while R-FAM
  passes (ruling 7). Every outcome, the gate's own included, prints the S-2 N_raw lines, so a second DSR shortfall
  is visible whatever names the outcome.
- **B-Q2.** The second DSR that decides is R-FAM computed with the gate's own dispersion term, the term the N = G
  line already uses. `strategy_outcome` therefore refuses lines whose N_raw term differs from the gate's
  (`sr_sd_daily != sr_sd_grid`) and says how to collect them. Any other term (the log names the SE_null pairing)
  is passed as `reference_s2` and printed as "S-2 reference only (B-Q2, never decides): ..." lines; it never
  changes the outcome. A reference for another series, G, gate term or N_raw counts, or one using the gate's own
  term, is refused. `dsr_two_n` and `strategy_lines` still accept any labelled term (the ⑨-3d criterion stays
  open); only the outcome is decided on the gate's term.
- **B-Q3.** For a replacement, MDE80 above the registered expected dSR makes the outcome INSUFFICIENT_DATA and
  `replaces_incumbent` False, also when S-3 won. MDE80 equal to the expected dSR is not short (criteria S-7,
  "크면"), so a won comparison is then adopted. An addition has no S-7 and is not affected.

### Readings (where the text needed one) and undecided cases

- **B-Q1 before B-Q3.** When R-FAM is below 0.90 and S-7 is short, B-Q1 ("둘째 DSR이 0.90 아래일 때 결과 이름")
  and criteria 4.2.2 ("S-3이 INSUFFICIENT_DATA면 결과도 INSUFFICIENT_DATA") both name an outcome. This unit gives
  REJECT: B-Q1 answers the outcome's name without a condition and gives the gate's handling as its reason, and
  the gate itself rejects a DSR shortfall before it considers a short record (`validate.py:584-622`); M-17 keeps a
  short-record DSR REJECT as REJECT in adoption. Neither name adopts or replaces. If the owner meant otherwise,
  only step 5 and step 6 swap.
- **B-Q1 after a gate REVISE or INSUFFICIENT_DATA (review round 2).** B-Q1 gives its reason as "기존 심사도 같은
  점수 미달을 기각으로 처리합니다", and the gate's order (`validate.py:584-622`) is: sample floor
  INSUFFICIENT_DATA, then REJECT (a finite DSR below 0.95 among others), then PASS, then the minimum-record
  INSUFFICIENT_DATA, then REVISE. Read the same way, R-FAM below 0.90 turns a gate REVISE into REJECT
  [잠정 기준] (step 1a). A gate INSUFFICIENT_DATA with the gate's own DSR passing can be either the sample floor
  (before REJECT: INSUFFICIENT_DATA stands) or the minimum record (after it: B-Q1's REJECT would come first), and
  the lines do not say which, so with R-FAM below 0.90 no outcome is named (step 1c). With the gate's DSR below
  0.95 or NaN, a gate INSUFFICIENT_DATA can only be the sample floor and stands. With R-FAM not supplied, a gate
  REVISE or such an INSUFFICIENT_DATA names nothing either, because B-Q1 might apply. This is a reading for the
  owner to confirm next to "B-Q1 before B-Q3"; if the owner wants the gate's verdict to stand, steps 1a to 1c go.
  A caller that knows the gate's branch could pass it later; this unit takes no such input.
- **Short power outranks KEEP.** 4.2.2 makes the result INSUFFICIENT_DATA whenever S-3 is INSUFFICIENT_DATA, and
  the S-7 row sets S-3 to INSUFFICIENT_DATA without a condition on S-3's own result, so a borderline or lost S-3
  with short power, a borderline R-FAM with short power, or a borderline or lost S-4 with short power, is
  INSUFFICIENT_DATA, not KEEP. B-Q3 itself is about the incumbent comparison; the lost-S-4 case follows from
  4.2.2's unconditional "결과도 INSUFFICIENT_DATA", and 6.1 KEEP also matches it. Neither adopts or replaces, and
  the reason lines print every S-4 result next to the B-Q3 line, so a baseline loss is not hidden. Owner question:
  should a lost or borderline S-4 give KEEP ahead of B-Q3?
- **A borderline second DSR is KEEP.** 6.1 KEEP includes the borderline cases, and 6.2 lists the second DSR in
  [0.90, 0.95) while the gate's DSR passes among them (the reading the earlier units' questions already used: only
  the case below 0.90 was unmapped).
- **6.4 N12.** A NaN DSR does not meet S-2 and is INSUFFICIENT_DATA: for R-FAM after a gate PASS, and for the
  gate's own DSR when the gate gave REVISE (the gate's mislabelled REVISE of N12). A gate REJECT or
  INSUFFICIENT_DATA with a NaN DSR stays as the gate said.
- **No outcome named (`NO_OUTCOME`, with the reason in `basis` and the header):** R-FAM not supplied (an L-FAM-only
  result), whatever L-FAM says, after a gate PASS or REVISE, or after a gate INSUFFICIENT_DATA whose DSR passes;
  steps 1b and 1c; a replacement whose S-7 did not run; a counting comparison that did not run while nothing else
  gives KEEP; a sample touching the 2027-01-01 holdout when everything else is met. A gate REJECT is named in each
  of these cases, and a KEEP stays KEEP with a touched holdout (the holdout only forbids ADOPT).
- **A comparison that did not run is not S-3 INSUFFICIENT_DATA.** 4.0 rule 5 makes INSUFFICIENT_DATA the result
  when "검정력이 모자라 판단할 수 없으면" (power is short), and S-7 is the registered power check. A NOT_RUN line has
  no statistic at all, for reasons that are not all about power (a zero HAC SE, a block longer than the sample,
  fewer than 30 sessions), so this unit does not name INSUFFICIENT_DATA for it: a replacement's S-3 not run gives
  NO_OUTCOME (never ADOPT, never replaced), and with another check lost or borderline KEEP, since KEEP is then
  named by that check alone. Owner question: should a NOT_RUN S-3 (or S-7) be read as INSUFFICIENT_DATA under
  4.0 rule 5? If so, it would also outrank KEEP, as short power does.
- **Refused (`AdoptionInputError`):** a gate verdict outside `validate.DECISIONS` (including "pass", "ADOPT",
  " PASS", empty or not a string); a verdict `validate.score_strategy` cannot give for the status of its own DSR
  at N = G (PASS with that DSR below 0.95 or NaN, REVISE with it below 0.95: the gate rejects a finite DSR below
  0.95 unless its sample floor gave INSUFFICIENT_DATA first); lines that `strategy_lines` would not produce (a
  replacement without a counting S-3 or without S-7, an addition whose S-3 counts, no S-4, an unknown kind, no
  R-FAM line, an unknown reading, a status outside those the producing function gives or not the one its value
  gives, a comparison ending on another session than the sample, a cash baseline not replaced by S-1, an S-7 line
  against another incumbent or whose flag, MDE80 or status is not what `power_line_s7` gives, a holdout line that
  is not `check_sample_end` of its own last session, an OFF-REGISTRATION comparison); B-Q2 pairing not met; a
  reference S-2 that does not match (series, G, session count, gate term, gate DSR, N_raw counts).
- **Provisional.** `provisional` is derived from the collected lines (True while the module says the second DSR
  is provisional, that is until the R3 recorder exists), so every outcome is provisional, the gate's own included.
- **Not covered.** S-5 (SPA when one registration has more than one rule), S-6 (break-even cost, a pre-gate
  REJECT) and D-4 are later units; every outcome prints a line saying so, `not_covered` lists them, and an ADOPT's
  basis reads "criteria 6.1 ADOPT (S-5, S-6, D-4 not checked)". An ADOPT here, and `replaces_incumbent`, are not
  actionable until those units exist.
  4.0 rule 4 (a tie keeps the simpler) needs no step: a tie is not a win, so it is KEEP.

### What changed in the earlier units' text

- The note printed on every `strategy_lines` result said "no outcome label: the outcome assembly (criteria 6.1)
  waits for the owner's answers on a second DSR below 0.90 and on S-7". This unit makes that false, so it now reads
  "no outcome label on these lines: strategy_outcome (⑨-4/2/c) assembles the outcome of criteria 6.1 from them
  and the gate's verdict", and a test pins the new text. The collected lines still carry no outcome word.
- Docstrings: the module docstring describes the outcome assembly; `power_line_s7` says that B-Q3 answered what
  M-6 left open and that `strategy_outcome` applies it.
- Unchanged: every threshold, status, number and other printed line. The S-7 line keeps "[printed only]": on the
  collected lines it decides nothing; the outcome reads its flag. Imports are the same (`core.quant.validate` and
  `core.quant.gate_stats` only) and `core/quant` is not edited.

### Verification (local, synthetic, Linux, Python 3.13.17)

- `tests.adoption_strategy_rules_acceptance`: **42 tests** (35 before; 7 added in the class `OutcomeAssembly`, and
  two scope tests extended: the docstring map names `strategy_outcome`, and the no-effects audit also runs it).
  Runs of 4.666 s, 5.795 s and 4.542 s, and one with `-W error::RuntimeWarning` (5.843 s), all OK; after three
  long test lines were wrapped (no test changed), once more 4.335 s and with `-W error::RuntimeWarning` 4.667 s, OK.
- The new tests: each outcome name and `NO_OUTCOME` reached; B-Q1 (R-FAM at the next float below 0.90 is REJECT
  "[잠정 기준]", at 0.90 KEEP, at 0.96 ADOPT; REJECT also with short power, a lost S-3, an addition's borderline
  S-4; L-FAM below 0.90 decides nothing; a gate REJECT has no label); B-Q2 (the gate's term decides ADOPT while
  the reference SE_null-style term puts both readings below 0.90; the reference lines pinned in full; lines with
  another N_raw term refused even under a gate REJECT; five bad references refused); B-Q3 (won S-3 with short
  power INSUFFICIENT_DATA and not replaced, powered ADOPT and replaced, MDE80 equal to the expected dSR ADOPT and
  the next float below INSUFFICIENT_DATA, borderline or lost S-3 and borderline R-FAM with short power
  INSUFFICIENT_DATA, an addition's won or lost S-3 claims nothing); the 6.2 edges (resample counts 200, 201, 400,
  401 of 2000 through `lw_compare`; R-FAM at 0.95, the next float below, 0.90 and the next float below; a borderline
  S-3; a gate DSR below 0.95 is the gate's REJECT and a PASS or REVISE with it is refused); the undecided cases and
  refusals listed above; and, on real unstubbed numbers, that the collected lines, the reference lines and every
  field are equal before and after (also equal to a fresh `strategy_lines` call), that the printed R-FAM and G
  values are `validate.deflated_sharpe`'s, and that the outcome is immutable.
- Mutation run (in place, from a backup, restored byte for byte and checked by SHA-256): 18 distinct single-change
  mutants of the new code (B-Q1 removed or moved after B-Q3, B-Q2 pairing unchecked or the reference deciding,
  B-Q3 removed or only for a lost S-3, borderline R-FAM or comparisons adopted, missing R-FAM passed, holdout
  ignored, N12 dropped, the gate check dropped, not run read as a win, L-FAM deciding, provisional dropped,
  OFF-REGISTRATION accepted, S-7 not run ignored, an addition replacing) were all killed by `OutcomeAssembly`.
  One further run was a duplicate of "B-Q1 removed" under another label and is not counted.
- `tools.compliance.check --check`: FAIL before the baseline refresh (documents 1 to 20 need review, as expected
  for changed monitored sources), PASS after it (publication BLOCKED, as before); only the four changed files'
  source hashes moved and no document hash changed. `tests.compliance_acceptance` and
  `tests.compliance_export_acceptance`: 47 tests OK. `compile()` and `ast.parse(feature_version=(3, 10))` of the
  module and its test pass under Python 3.11.17 and 3.12.3; `git diff --check` is clean.

Not verified here: the CI matrix (Windows, Python 3.10, 3.11, 3.12, 3.14 execution), any real gate verdict, P&L,
R-FAM or L-FAM count, and any caller: nothing in the app, Lab or R3 calls `strategy_outcome` yet.

### Review round 2 of ⑨-4/2/c (second commit)

Seven verifier findings, each reproduced on the first commit (`5f08973`) before the fix:

| Finding | Reproduced | Fix |
| --- | --- | --- |
| B-Q1 only after a gate PASS (major) | gate 0.97, R-FAM 0.85: PASS gave REJECT [잠정 기준], REVISE gave REVISE and INSUFFICIENT_DATA gave INSUFFICIENT_DATA, and neither printed the R-FAM line | steps 1a to 1c above, read from the gate's order and recorded as a reading for the owner; the S-2 N_raw lines are printed in every outcome; `provisional_basis` is True for basis B-Q1 only; tests for REVISE, INSUFFICIENT_DATA with the gate's DSR passing, below and NaN, R-FAM missing or NaN |
| No test for a replacement's S-3 not run | the mutant that checks only S-4 for NOT_RUN survived and gave ADOPT with "S-3 vs incumbent: win" | test: NO_OUTCOME, not replaced, "S-3 vs incumbent: not run (HAC SE is zero)", no "win" line |
| 18 further surviving mutants | gate map, provisional, `provisional_basis`, `_same`, reference checks, S-3/S-4 shape checks, N12 basis, the S-7 "within" line | assertions for each (gate INSUFFICIENT_DATA with the gate's DSR below and NaN; provisional from both flags; the label on B-Q3, N12, KEEP and gate outcomes; a NaN-grid reference; session count and gate term of a reference; an L-FAM-only reference; S-3 and S-4 rule and counting flags; the full S-7 line) |
| Statuses trusted, fail open | hand-built S-3 "won" or "replaced", S-4 "WIN", a "win" with dSR -0.5 and p 0.9, R-FAM "pass" at 0.5 or "PASS", S-7 against another incumbent, a flag disagreeing with MDE80, MDE80 NaN, a 2027-03-01 sample marked not touched: each gave ADOPT | whitelist and re-derivation described under "What it does"; the ADOPT reasons print each comparison's own status; a test refuses 22 malformed shapes |
| B-Q3 hid a lost S-4 | short power with S-4 not won gave INSUFFICIENT_DATA naming only S-3 | every other counting comparison is printed with the B-Q3 line; the reading names the lost S-4 and asks the owner |
| S-3 NOT_RUN versus 4.0 rule 5 | S-3 not run gave NO_OUTCOME, with a lost S-4 KEEP | kept, with the reason stated under "Readings" and an owner question |
| ADOPT without S-5, S-6 | ADOPT and `replaces_incumbent` carried no limit | `NOT_COVERED`, the `not_covered` property, the ADOPT basis and the reason line name S-5, S-6 and D-4; docstrings say an ADOPT is not actionable until they exist |

No finding was rejected. Verification of this round (local, Linux, Python 3.13.17): the module has **46 tests**
(42 before; in `OutcomeAssembly` 4 added, 3 extended and 2 adjusted as below), OK in 4.052 s and 4.044 s, and with `-W
error::RuntimeWarning` in 4.004 s. Two existing cases built an inconsistent S-3 by hand (`status="borderline"` and
`"not_won"` on a won comparison); the new checks refuse those, so they now take the S-3 of a stubbed run that is
borderline or lost, with the same expected outcomes. A mutation run on a scratch copy (43 single-change mutants:
the 33 of this round's new code and the 10 survivors of the verifier's run that still apply) killed 43 of 43; the
copy was checked equal to the worktree file by SHA-256 afterwards. `tools.compliance.check --check`: FAIL before
the baseline refresh (documents 1 to 20 need review), PASS after it (publication BLOCKED, as before), with only the
four changed files' source hashes moved; `tests.compliance_acceptance` and `tests.compliance_export_acceptance` 47
OK; `compile()` and `ast.parse(feature_version=(3, 10))` of the module and its test pass under Python 3.11.17 and
3.12.3; `git diff --check` is clean. Not verified: the CI matrix, any real gate verdict, P&L or N_raw count.

## CI and compliance

- `.github/workflows/runtime-smoke.yml`: `core/adoption/**` and the test file appended to the pull-request paths
  filter; `tests.adoption_strategy_rules_acceptance` appended to the existing "Verify bounded source fixtures"
  unittest command. No new step, no budget change.
- `docs/compliance/FACTS.md` gains a section for this unit. New source files map to all 20 compliance documents,
  so the source-review baseline is refreshed for documents 1 to 20; no policy text changes, because the module
  adds no data flow, storage, transfer or user-facing surface.
- ⑨-4/2/c: no workflow change. The new tests are in the module CI already runs, and `core/adoption/**` is already
  in the paths filter. FACTS gains a row for the outcome assembly and the sentences it made false are corrected;
  the source-review baseline is refreshed again for documents 1 to 20, with no policy text change (still no data
  flow, storage, transfer or user-facing surface).

## Next units

Outcome assembly is done (⑨-4/2/c, above). Owner questions from it: the order of B-Q1 against B-Q3 and against
a gate REVISE or INSUFFICIENT_DATA (steps 1a to 1c, 5 and 6), whether a lost or borderline S-4 with short power is
KEEP rather than INSUFFICIENT_DATA, and whether a NOT_RUN S-3 or S-7 is INSUFFICIENT_DATA under 4.0 rule 5. Still
to come: S-5/S-6 wrappers (until then an ADOPT does not cover them: its basis, `not_covered` and last line say so,
and neither the ADOPT nor `replaces_incumbent` is actionable), the SMA-200 and 60/40 baselines (B-Q7 of 2026-11-11: rebalanced every 21
trading days, costs only on what is traded), forecast rules (B-Q4: decided by the existing DM test, Clark-West
printed as a reference line only), risk rules with the exact zero-violation LR, D-4, and the registration loader
(`docs/adoption/registrations/<card_id>.json`, M-15; B-Q5: all 12 items required, Claude drafts and the owner
reviews and commits, R-FAM and L-FAM both written). Connecting the outcome to the R3 recorder (an R-FAM count from
the registry) and lifting the provisional label belong to ⑨-3c and ⑨-3d.
