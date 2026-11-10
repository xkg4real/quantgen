# Adoption strategy checks (⑨-4/2/a)

This is **⑨-4/2/a**, the first unit of the adoption module that owner ruling M-21 placed outside the Nautilus
fingerprint scope (`core/adoption/`). It adds `core/adoption/__init__.py` and `core/adoption/strategy_rules.py`:
pure functions that compute the strategy comparison lines S-2, S-3, S-4 and S-7 of the adoption criteria, the
borderline zones and the 2027-01-01 holdout guard, on daily OOS P&L arrays the caller supplies. It assigns no
adoption outcome, re-runs no gate, and is not connected to the Lab, the app, any ledger, card or register. The
parent item ⑨-4/2 stays open.

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
- This branch is based on main `ed8df4a`. PR #92 (docs only) merged after the branch point; it touches none of
  this unit's files.

## What it computes

All statistics come from existing functions; nothing in `core/quant` is edited (`git diff ed8df4a -- core/quant`
is empty).

| Function | Rule | Computation |
| --- | --- | --- |
| `check_sample_end(last_session)` | 4.0 rule 6, 3.3; M-14 | `holdout_touched = last_session > 2026-12-31`; `adopt_allowed = not holdout_touched`. Dates or ISO strings; a `datetime` is refused. |
| `gate_sr_sd_daily(full_pnl)` | S-2; M-3 | The gate's own dispersion term: population SD of the per-period full-sample Sharpe of each grid column (`validate.py:503-506`), through the public `validate.sharpe`. A helper only. |
| `dsr_two_n(oos_daily, *, n_grid, n_raw, sr_sd_daily, sr_sd_label)` | S-2; M-3, M-11 | `validate.deflated_sharpe` at N = G and at each supplied N_raw reading, against `GATE['dsr_min']`. |
| `classify_dsr(value, *, grid_status)` | S-2, 6.2, 6.4 | `pass` at dsr_min or above; `borderline` in [0.90, dsr_min) only while the grid DSR passes; `below` otherwise; `nan` for a NaN DSR. |
| `lw_compare(challenger, other, dates, other_dates, *, rule, other_label, counts, B, seed)` | S-3, S-4; M-2, M-6, M-11, M-19 | `gate_stats.pw_block_psi` (max(21, PW(psi)), fallback 250 kept in `block_events`), `gate_stats.lw_studentized_boot` with B = `GATE['bootstrap_B']` (2000) and seed = `gate_stats.SEED_STUDY` (11), `p = gate_stats.p_numeric(p_lw, B)` ("< 1/B" compares as 1/B). |
| `classify_comparison(d_sr, p)` | 4.0 rule 2, S-3, S-4, 6.2; M-2, M-11 | `win`: dSR > 0 and p <= 0.10; `borderline`: dSR > 0 and 0.10 < p <= 0.20; else `not_won`. |
| `power_line_s7(challenger, incumbent, dates, incumbent_dates, *, expected_dsr)` | S-7, 3.2 item 8, 5.3; M-6 | SE = `gate_stats.lw_hac_se(...).se`, MDE80 = `gate_stats.MDE_FACTOR` x SE, flag `MDE80 > expected dSR`, printed only. |
| `strategy_lines(*, kind, ...)` | 4.2.2; M-3, M-4, M-6, M-11, M-14, M-19, M-20 | Collects S-2, S-3 (replacement: counts; addition: printed only), one S-4 per registered baseline, S-7 and the holdout line into an immutable result with the L1 note and no outcome. |

Every result is a frozen dataclass whose collections are tuples. `lines()` renders the printable lines. The only
new constants are alpha 0.10, the borderline bounds 0.20 and 0.90, the last session 2026-12-31 and the note
"L1 미적용(브리지 미지원)"; `dsr_min` 0.95, B 2000, seed 11, the 21-session block floor and MDE factor 2.1232 are
read from `validate.GATE` and `gate_stats`.

## Readings and corrections applied

- **Dispersion term is an input.** The R3 design (section 4.4) says the dispersion pairing "is a criterion", and
  10.2 B Q1 reserves "which N, paired with which dispersion term" for ⑨-3d. `dsr_two_n` therefore takes
  `sr_sd_daily` and a required `sr_sd_label`, and prints the label on the S-2 line. `gate_sr_sd_daily` exists so
  the gate's term can be passed and named, not as a default.
- **Two N_raw readings.** `N_RAW_READINGS` names `L-FAM` (family ledger row count, `FamilyLedger.n_raw`, read on
  the owner PC) and `R-FAM` (R3 design 3.13 literal family-wide count, |K| + |L minus cfg(K)|). The caller supplies
  one or both as integers >= 1; a reading not supplied is shown as "not supplied". The module never opens a
  ledger.
- **N_raw below G is printed, not refused.** R3 design 10.2 B Q4 ("may a ledger-based N fall below G?") is
  reserved for ⑨-3d, so `below_grid` is a printed status. The scoping proposal to refuse it was dropped on review.
- **Direction applies to the borderline zone.** Criteria 6.2 names only the p range (0.10, 0.20]; this unit also
  requires dSR > 0, reading the zone as the near-miss of a win under 4.0 rule 2. With a null-centred one-sided p,
  p <= 0.20 and dSR <= 0 should not occur in practice; the rule only removes the corner.
- **S-7 is printed only.** M-6 did not answer whether MDE80 above the expected dSR turns S-3 into
  INSUFFICIENT_DATA (criteria section 9, decision 6). The SE is the LW-HAC SE that criteria 5.3 used, not
  `gate_stats.power_line`, which takes the macro cards' SE plateau and accepts only CARD-O and CARD-P.
- **A replacement must carry its expected dSR** (criteria 3.2 item 8); an addition may omit it.
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
  converts S-3, which dispersion term pairs with N_raw, and which N_raw reading is of record.
- No S-1 (the gate is the caller's precondition), no S-5 SPA or S-6 break-even (`tf_gov`), no SMA-200 or 60/40
  baseline P&L (`core.quant.strategies` is never imported, so `config` and `.env` are never loaded), no forecast,
  risk, data or registration rules, no L2/L3.
- No file, ledger, clock, environment, network or process access. Imports: `core.quant.validate` and
  `core.quant.gate_stats` only (plus the standard library and numpy).

## Verification (local, synthetic)

Test module: `tests/adoption_strategy_rules_acceptance.py`, 29 tests, run through a scratch runner that installs
an audit hook refusing any `open` under `asset_expansion/cache` or a `.env` path and any `socket.connect`, and
replaces `dotenv.load_dotenv` with a no-op before imports.

- Python 3.13.17 (numpy 2.3.5, scipy 1.18.0), Linux: 29 tests OK in 2.75 s, 3.06 s and 3.08 s (three runs of the final code).
  Together with the eight R3 modules that CI already runs in the same step (`tests.run_registry_*`), 180 tests
  OK in 5.7 s.
- Golden equality: S-2 values equal direct `validate.deflated_sharpe` calls; S-2 with the gate's dispersion term
  reproduces `validate.score_strategy(...).dsr` on a synthetic walk-forward to 12 decimals; S-3/S-4 fields equal a
  direct `pw_block_psi` + `lw_studentized_boot` call (seed 11 and seed 12); S-7 equals `lw_hac_se`.
- Edges: p at 0.10 and 0.20 and the next float above each (also through resample counts 200, 201, 400, 401 of
  2000 with a stubbed bootstrap); DSR at 0.95 and 0.90 and the next float below each; "< 1/B"; a NaN DSR; N_raw
  below G; sessions ending 2026-12-31 versus 2027-01-01; misaligned, unequal, duplicate and reversed sessions.
- Scope: no `open`, socket, process or directory audit events while the functions run; `validate.GATE` and the
  gate functions unchanged after the run; an AST check that the module never assigns into or monkeypatches the
  gate; an isolated subprocess (`python -I`) importing the module loads only `core`, `core.quant`,
  `core.quant.validate`, `core.quant.gate_stats` and `core.adoption*`, and neither `config` nor `dotenv`.
- A mutation check (15 single-line mutants of the module: comparison edges, direction, borderline condition,
  holdout boundary, N_raw count passed, p source, alignment, block rule, MDE factor, datetime refusal, the
  replacement's expected dSR) was killed 15 of 15. The module was restored byte for byte afterwards.
- `compile()` and `ast.parse(feature_version=(3, 10))` of the three new Python files pass under Python 3.11
  (compilation only; Python 3.10 itself was not available here).
- A first combined run reported 2 failures in `tests.run_registry_series_files_acceptance` spawn tests; the cause
  was the scratch runner (no `__main__` guard, so spawned children re-ran the suite). With the guard added the
  same 180 tests pass. No product test failure was observed. The figures above are from the final code, after a
  last change that wraps a non-numeric P&L input in `AdoptionInputError`; the first runs (29 tests in 3.05 s,
  2.60 s and 2.77 s; 180 in 5.6 s; 15 of 15 mutants) also passed.

Not verified here: the CI matrix (Windows Python 3.11, 3.12, 3.14; Ubuntu 3.12), Python 3.10 execution, and any
real P&L. The owner-PC values of N_raw and the gate's inputs are outside this unit.

## CI and compliance

- `.github/workflows/runtime-smoke.yml`: `core/adoption/**` and the test file appended to the pull-request paths
  filter; `tests.adoption_strategy_rules_acceptance` appended to the existing "Verify bounded source fixtures"
  unittest command. No new step, no budget change.
- `docs/compliance/FACTS.md` gains a section for this unit. New source files map to all 20 compliance documents,
  so the source-review baseline is refreshed for documents 1 to 20; no policy text changes, because the module
  adds no data flow, storage, transfer or user-facing surface.

## Next units

Outcome assembly (after the owner answers the questions above), S-5/S-6 wrappers, the SMA-200 and 60/40
baselines (60/40 mechanics to be proposed), forecast rules (Clark-West question open), risk rules with the exact
zero-violation LR, D-4, and the registration loader (`docs/adoption/registrations/<card_id>.json`, M-15).
