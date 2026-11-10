# Look-ahead audit LA-02, part 2 (⑨-1/2/c)

This is the second part of the LA-02 fix from the 2026-11-04 look-ahead audit
(`git show 7749450:docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md`, LA-02 at lines 279-284). It follows the pattern
of part 1 (`docs/product/LOOKAHEAD_LA02_PART1_2026-11-10.md`): each REFDATA or owner-input point-in-time test that used
to raise `NotRun` whatever the data held, or failed as "not implemented" after its gate, now runs a real body once its
input arrives. The body opens with its fixture gate or a computed owner check, parses a declared layout, and calls a
module `_check_*` helper. Every expected value in that helper comes from a cited spec line or from `goldens.csv`, read
only. Each body also has a demonstration that shows it PASS on invented in-memory rows and FAIL once for each value
clause. This part changes test files only. No test changes status today: every real-data test below is still NOT_RUN
until ⑨-2 lists its fixture, or until the owner extends a calendar file.

## Authority and scope

- Owner ruling L-2 (2026-11-04, `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:546`, verbatim):
  "L-2 = (가) 높음 2건(LA-01, LA-02)부터 별도 브랜치에서 수정 시작, 병합은 동결 해제 뒤 [권고]". The log maps it to ⑨-1 at
  `:553`. The main freeze was lifted on 2026-11-04 (U4-나).
- The owner's reply of 2026-11-10, "전부 승인합니노.", was relayed with this task. This part relies on L-2 for its scope.
- Base: `8e88814`, the part-1 branch (⑨-1/2/b, PR #96), which also carries main `be26c24`, fold PR #93 and adoption
  PR #95. Branch `claude/lookahead-la02-part2-20261110`.
- Four tracks edited the test files in parallel, and one integration step reviewed them. The integration step also
  updated the ratchet, ran the tests and wrote this record.
- Scope: the 13 sites that part 1 left in `LA02_REMAINING`. This part converts 9 of them. Four stay: T-FIX-01,
  T-REGIME-01 full range, I-05 and G-REF-01 (see "Next parts").

## What changed

| Test | Before | Now |
| --- | --- | --- |
| G-POST-01 M1 rows, `tests/macro_m1_pit.py::test_g_post_01_m1_data_rows_refdata` | One inline identity, then an unconditional `NotRun("REFDATA: ...")` | Gate on F13, F16 and F27, naming each absent file. Then each file is parsed in its declared layout, the part-1 owner-calendar gate `_official_calendar` runs over 2026-09-18..2026-10-02, and `_check_gpost01_m1` runs |
| G-POST-01 row replay, `tests/macro_m1_fixtures.py::test_g_post_01_m1_data_rows_refdata` | `_refdata(F01, F13, F16, F20, F27)`, then `NotRun("... wired by the M1 PIT package")` | The same gate. Then F01, F13, F16 and F27 are parsed (`_gpost_rows`), the same calendar gate runs, and `_check_g_post_01` replays the rows as of 06:30:30Z on 2 Oct |
| T-PRINT-01 on Yahoo ^KS11, `tests/macro_m1_pit.py::test_print_01_real_kospi_close_refdata` | Unconditional `NotRun` | `require_fixture(F13)`, then the part-1 owner-calendar gate `_official_calendar` over 2026-02-23..2026-03-09, then `_check_print01_ks11` |
| G-STALE-01 / T-STALE-01, `tests/macro_m1_pit.py::test_stale_01_g_stale_01_reference_table_refdata` | Unconditional `NotRun` | Gate on the four FRED files (REFDATA). Then a computed owner gate, `_stale01_waiting`, over the signed calendar files the body reads (OWNER). Then `_check_stale01` on a PIT store built from the files |
| T-MISS-01 CPI, `tests/macro_m1_pit.py::test_miss_01_cpi_yoy_3_353_refdata` | Unconditional `NotRun` | Gate on CPIAUCSL and UNRATE, then `_check_miss01` |
| T-CLOSE-02 on the signed files, `tests/macro_m1_calendars.py::test_close02_on_the_real_signed_files_is_owner_input` | `NotRun("OWNER: ...")` whatever the files held | `_close02_waiting` computes every refusal, coverage gap, missing owner-signed `kr_sessions` row, and `kr_sessions` row list that the file still names under `owner_must_sign` (the `random_end_extension` rows), among what the clauses read (`CLOSE02_NEEDS`). While anything waits, the test is NOT_RUN (OWNER). Once nothing waits, `_check_close02` runs on the shipped set, and a coverage or signing error inside it is a FAIL |
| T-VT-01 on 2 Oct, `tests/macro_m2_risk.py::test_vt_01_rv20_28_82_and_vt_0_694_on_2_oct_refdata` | `_refdata(F13)`, then `NotRun("... pinned to the frozen fixture ingest")` | The same gate. Then F13 is parsed, replayed through `R.market_vol_target` at the 2-Oct KRX close, and checked by `_check_vt01` |
| T-LABEL-01, `tests/macro_m2_risk.py::test_label_01_kospi_elevated_stressed_and_us_normal_refdata` | `_refdata(F13, F14)`, then `NotRun` | The same gate. Then F13 is replayed at the KRX close of 2 Oct and F14 at the NYSE close of 1 Oct, and `_check_label01` runs |
| T-B5-01 on KOSPI, `tests/macro_m3_estimators.py::test_t_b5_01_kospi_golden_refdata` | `require_fixture(KS11)`, then `AssertionError("... golden assertion not implemented")` | `require_fixture(KS11)`. The parsed closes go through the product B5 harness `docs/vol_backtest.spec_form` (read only), then `_check_b501` |

The ratchet in `tests/macro_m1_fixtures.py` moves these nine sites from `LA02_REMAINING` to `LA02_CONVERTED` and adds
them to `LA02_CONVERTED_FLOOR`. `LA02_SITES` is unchanged. The floor now holds 13 sites, and the new constant
`LA02_FLOOR_SIZE = 13` replaces the hard-coded 4 in the floor-size check, so lowering the floor fails the ratchet test.

Nine new demonstration tests, none with `test_ids`:

- `tests/macro_m1_pit.py`: `test_g_post_01_body_passes_and_fails_on_invented_rows`,
  `test_print_01_body_passes_and_fails_on_invented_ks11_closes`,
  `test_stale_01_body_passes_and_fails_on_invented_releases`, `test_miss_01_body_passes_and_fails_on_invented_cpi`.
- `tests/macro_m1_calendars.py`: `test_close02_body_passes_and_fails_on_invented_calendars`.
- `tests/macro_m1_fixtures.py`: `test_g_post_01_body_passes_and_fails_on_invented_rows`.
- `tests/macro_m2_risk.py`: `test_vt_01_body_passes_and_fails_on_invented_closes`,
  `test_label_01_body_passes_and_fails_on_invented_closes`.
- `tests/macro_m3_estimators.py`: `test_t_b5_01_body_passes_and_fails_on_invented_closes`.

### Expected values and where they come from

The spec is `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`. Golden rows are read from
`tests/fixtures/macro/goldens.csv` and asserted at their Level 1 kind tolerance, with one exception: the
`macro_m1_pit.py` bodies compare a vendor price (F13 ^KS11 7,003.74 and 5,251.87, F16 KRW=X 1,356.84) after rounding it
to two decimals, where Level 1 `price` is exact (L5735), and the `macro_m1_fixtures.py` site compares the same G-POST-01
rows exactly (question 4). The file is not edited.

- **G-POST-01, M1 rows** (spec L5819-5834). Both sites assert every `goldens.csv` G-POST-01 row whose `runs_from` is M1:
  - `kospi_close_2oct` 7003.74 (price, exact);
  - `kospi_return_2oct` 0.0046 (window_return ±0.01);
  - `drawdown_from_peak` -0.2316 (mdd ±0.01);
  - `close_over_200d` 1.107 (ratio ±0.01);
  - `samsung_close_2oct` 276000 and `hynix_close_2oct` 1841000 (price, exact);
  - `krwx_last_row` 1356.84 (price, exact);
  - `krwx_dlog20` -0.0011 (window_return ±0.01).

  Each site also asserts that the rows it computes are exactly `goldens.csv`'s M1 set. The constants come from the
  golden rows' own quantities and notes:
  - the peak 9,114.55 on 2026-06-22 (`drawdown_from_peak`; L5821);
  - the 200-close window (`close_over_200d` note);
  - the 20-observation dlog (`krwx_dlog20`; L5834);
  - the KRW=X last row dated 1 Oct, with the provisional 2-Oct row dropped (`krwx_last_row`; L5834, L6291);
  - the return's previous close (`kospi_return_2oct` note "7,003.74 / prev close - 1"): the row before 2 Oct (in
    `macro_m1_fixtures.py`, the previous visible row) must be dated the previous KRX session, `clocks.prev_session` on
    the signed calendar. Both bodies read it through the part-1 owner gate `_official_calendar` over 2026-09-18..
    2026-10-02, the fortnight T-PRINT-01 reads; the shipped `holidays_KRX` covers 2026, so the gate passes today.

  The `macro_m1_fixtures.py` site adds point-in-time visibility. Each file is read as of the decision at 06:30:30Z
  (L2096, L6278), and a row available later is invisible (L539). No visible row may be dated after 2 Oct. Each 2-Oct
  KOSPI and stock row must be stamped at the scheduled close 06:30:00Z (L1289); the pre-patch 6,943.66 was a
  10:56 KST intraday print (L6286). A row available before its own `obs_utc` is refused at the layout. That site also
  checks F01's official close against the same golden. The `macro_m1_pit.py` site ignores ^KS11 rows dated after
  2 Oct, and compares vendor prices (F13, F16) at two decimals and KRX won prices exactly (question 4).
- **T-PRINT-01 on F13** (L5631, L1382). Exactly one row on 2026-03-09, with close 5,251.87 at two decimals. The row
  before it must be on the previous KRX session of the signed calendar (`clocks.prev_session`). The return against that
  row must be -5.96% ±0.005 pp, the printed precision.
- **G-STALE-01 / T-STALE-01** (L1963, L5620, L5901-5908). Decisions are every session in 2016-01-04..2026-09-25 at the
  US and the KRX close-print bound, with knowledge equal to the decision. The checks:
  - (a) Without the source-exception list, every DTWEXBGS and DEXKOUS hit's missed date (`d_next`) is in
    `source_skipped`. Conversely, every decision after the no-list deadline of a listed date (R-19 step 3, the
    observation before it) and before the next stored release is a hit naming that date, so a check that never flags
    fails. A listed date published with later days of its week, such as the Wednesday 2018-12-05, flags no decision
    and is not required to. The ±0.01 band of the share golden alone would accept 0.
  - (b) With the list loaded, those hits raise no flag.
  - The share of flagged decisions is within Level 1 (ratio ±0.01) of `G-STALE-01/<series>_stale_schedule_<us|krx>`.
  - (a), (c): the share is at most 1% for DTWEXBGS, DEXKOUS and DGS10, and 0% for VIXCLS.

  The "schedule-aware" golden column is read as the share without the list, because T-STALE-01 (a) quotes the same
  0.42-0.89% for that case (question 7). The "1 trading day" and "3 days" columns and the median and max ages are
  printed nowhere and not asserted (question 8).
- **T-MISS-01** (L5624, L1353). Neither CPIAUCSL nor UNRATE has a month after Aug-2026: section 11's current state on
  2 Oct prints U-3 for Aug-2026 (L6347) and the Aug-2026 CPI YoY (L1355, L5624, L6348), so a later month is a later
  vintage (question 18). On the snapshot, the Oct-2026 YoY clause below therefore has no endpoint to test. Neither
  series has an Oct-2025 value. The Aug-2026 CPI YoY is computed,
  not flagged, and differs from the positional shift(12) value. It equals `goldens.csv` S11/cpi_yoy_aug2026 0.03353
  ±1e-4 (L5624's "±0.01" in percent). YoY for Oct-2025 and Oct-2026, MoM for Oct and Nov 2025, and the Sahm 3-month
  means of UNRATE for Oct-Dec 2025 must be NaN and flagged. The positional value and S11/cpi_yoy_wrong_lag (3.713%,
  `print_only`) are printed only.
- **T-CLOSE-02 on the signed files** (L2096, L5618; L2010-2016, L1289, L2039, L2064, L2021-2023, L2070, L1967, L2087,
  L1340, L2090, L5505). These are the clauses of the synthetic `test_close02_effective_dated_clocks`, plus the 2026-10-02
  bound. A value the spec states is asserted at that value. Where the spec defers to the signed calendar, the expected
  value is read from the signed rows of the set: the pre-2016 CSAT window, the Saturday close, a conditional-era
  random-end extension, the 1999 lunch-break window and the HKEX close (checked against a floor of 08:00Z). Each of
  these needs exactly one signed row; with none or two, the expected value is the text "one signed ... row (n)", so
  the clause fails whatever the clock returns. `goldens.csv` has no T-CLOSE-02 rows.
- **T-VT-01** (L5673; R-06 L1561-1563). The decision reads the 2-Oct close stamped 06:30:00Z / 06:30:30Z (L1289,
  L2096). `market_vol_target` must return status `ok` on 20 valid returns with that row as `close_t`. Then
  `G.assert_golden` checks G-POST-01 `rv20_2oct` 0.2882 (vol_level ±0.001) and `vt_2oct` 0.694 (weight ±0.02).
- **T-LABEL-01** (L5643; R-06 card L1565). `G.assert_golden` checks G-POST-01 `label_relative_2oct` "elevated",
  `label_q1` 0.157, `label_q2` 0.1855, `label_q3` 0.336 (vol_level ±0.001) and `label_percentile` 70 (percentile
  ±5). The quartiles are `np.quantile` over the trailing 756 sigma values of the closes the decision may read. The
  percentile is the share of those values at or below sigma(t), with t included (question 11). The KOSPI absolute label
  and the US relative label on 2026-10-01 are read from `goldens.csv` G-B5-04: `kospi_absolute_label` "stressed" and
  `us_relative_label` "normal" (L5804; the same as L5643). G-B5-04 also holds the US sigma 0.107, quartiles 0.105 /
  0.127 / 0.152 and the 28th percentile (`us_sigma`, `us_q1`..`us_q3`, `us_percentile`; L1565, L5804), each listing
  T-LABEL-01 in its `tests` column. The body prints those figures and does not assert them, because the rows name
  `F13;U1` as their inputs, and U1 is French Mkt-RF to 2026-08 spliced with ^GSPC for Sep-2026 (ACQUISITION.csv:33),
  while the replay reads F14 ^GSPC alone (questions 11 and 12).
- **T-B5-01** (L5642, L5801, L3207, L5737). Every value is read from `goldens.csv`:
  - G-B5-01/`sample_origins` 2594 (count_exact);
  - G-B5-01/`sma20_exceed` 0.047 (exceedance ±0.003);
  - G-B5-01/`sma20_pit_p` 0.107 (p_hi ±0.01), with G-POST-01/`gb501_pit_p` asserted equal to it;
  - G-B5-01/`sma20_verdict` PASS.

  When a statistic lies within tolerance of its B5 threshold, the verdict is a class, either PASS or FAIL (L5737; the
  repository's `tests/golden_tools.py` and `core/quant/gate_stats.py` cite the same rule as L5738, a blank line in the
  current spec; neither is changed here). The
  window is KOSPI 2016-03 -> 2026-10-02. The SMA20 forecast scaled by 0.7 must fail B5 (L5642). The pool is
  standardised by the unscaled sigma, as in the synthetic test (brief F-16). The normal-form and EWMA(0.94) lines are
  printed beside their goldens, not asserted (question 13).

### Declared fixture layouts

Neither `tests/fixtures/macro/ACQUISITION.csv` nor the spec names any columns, so each body declares the layout it
reads. `docs/macro_fixtures.py` writes each file as the reference file's own columns followed by the section 4.1
provenance columns. Each declaration is an input contract that the owner can confirm or change when ⑨-2 builds the
files. Every declared provenance value is pinned to `docs/macro_fixtures.REFERENCE_FILES` by a demonstration: the
`macro_m1_fixtures.py` and `macro_m2_risk.py` bodies read it from there, the `macro_m1_pit.py` demonstrations compare
their declarations with it, and the T-B5-01 demonstration compares `B501_PROVENANCE` with the F13 row.

- **F13** `yahoo_KS11_1996-12_2026-10-02.csv` (G-POST-01, T-PRINT-01, T-VT-01, T-LABEL-01, T-B5-01). The close is in
  a column named `close`. Every row is `KS11 / vendor_close / calendar_bound`, with `obs_date = session_date` (ISO) and
  one row per date in date order. The `macro_m1_fixtures.py`, `macro_m2_risk.py` and `macro_m3_estimators.py` bodies
  also read `obs_utc` and `available_at_utc`, written `YYYY-MM-DDTHH:MM:SSZ`. The `macro_m1_fixtures.py` and
  `macro_m2_risk.py` demonstrations assert that their column tuple equals part 1's `F01_COLUMNS`, and so does the
  `macro_m3_estimators.py` demonstration. The `macro_m1_fixtures.py` and `macro_m3_estimators.py` layouts refuse a row
  whose `available_at_utc` is before its `obs_utc`. The `macro_m1_pit.py` bodies do not read the instants. A blank or
  "." cell reads as missing there.
- **F14** `yahoo_GSPC_1990_2026-10-01.csv` (T-LABEL-01). The same layout, with `GSPC / vendor_close / calendar_bound`.
- **F16** `yahoo_KRWX_2004_2026-10-01.csv` (G-POST-01). The same layout, with `KRWX / vendor_close / calendar_bound`.
- **F27** `krx_005930_000660_closes_mcap.csv` (G-POST-01). Long form: one row per code and KRX session, with `code`
  (005930 or 000660) and its `close`. The `series_id` is either id of "005930;000660", with
  `official_close / calendar_bound`. The market-cap columns ride along and are not read.
- **F01** `krx_kospi_official_close_1997-01-03_2026-10-02.csv` (the `macro_m1_fixtures.py` G-POST-01 site). This is
  part 1's layout.
- **F18** `fred_snapshot_2026-10-02/<id>.csv`: DTWEXBGS, DEXKOUS, DGS10, CPIAUCSL, UNRATE. The value column is named
  by the FRED id (FRED's own header), with `<id> / first_release / calendar_bound`. A blank or "." cell is no
  observation. The monthly files carry `obs_date` on the first of the month, one row per month. That column is read as
  the value FRED served on 2026-10-02; no vintage column is read, and a long file with a row per month and vintage
  fails at `_monthly` (question 18).
- **F07** `fred_VIXCLS_VXVCLS_2007-12-04_2026-09-30.csv` (G-STALE-01). A `VIXCLS` column; VXVCLS rides along. Rows
  are `VIXCLS / vendor_close / calendar_bound`.
- **F20** `results/QX_DLA_postpatch.csv` is gated by the `macro_m1_fixtures.py` G-POST-01 site, because `goldens.csv`
  lists it for `kospi_close_2oct`. Its layout is not declared and no body reads it.

The G-STALE-01 body re-stamps each FRED row at its publication instant on the signed calendars (`CalendarClocks`), as
the existing DEXKOUS smoke does. It does not read the fixture's own instants.

### Questions for the owner at ⑨-2

Layouts and generation:

1. The `close` column name for F13, F14 and F16; the F27 long form (`code` plus `close`) rather than a wide layout;
   the F18 value column named by the FRED id; the F07 `VIXCLS` column. The F18 and F07 names are declared by one
   track only.
2. **F13 column conflict.** The product's own fixture reader `docs/vol_backtest.fixture_lines` reads `obs_date` /
   `value`, while every F13 body here reads `close`. Once F13 is listed, either vol_backtest's section (d) lines fail
   on a `close` file, or the F13 bodies fail at the layout on a `value` file. One side needs a change, and
   `docs/vol_backtest.py` is product code that this part does not edit.
3. **Generator gap** (read from the code; `generate` was not run). `docs/macro_fixtures.calendar_available_at` raises
   `KeyError` for a series id that is not registered. KS11, KRWX, GSPC and the bare 005930 are not in
   `data/macro/series_registry.yaml`, so the generator cannot stamp F13, F14, F16 or F27 as written. Should the files
   carry these ids, or the registered R-06 ids (`KOSPI_OFFICIAL_CLOSE`, `US_SLEEVE_OFFICIAL_CLOSE`,
   `KRX_005930_OFFICIAL_CLOSE`)?
4. Is comparing vendor prices at their two-decimal printed precision acceptable (F13 5,251.87 and 7,003.74; KRW=X
   1,356.84)? Level 1 `price` is exact (L5735), but a Yahoo file may carry float artefacts. The two G-POST-01 sites
   disagree on this: `macro_m1_pit.py` rounds to two decimals and `macro_m1_fixtures.py` compares exactly, so one F13 or
   F16 file with a float artefact on 7,003.74 or 1,356.84 would PASS the first site and FAIL the second on the same
   golden row. Which rule should both use?
5. F20 is gated but not read. Should the replay also compare against F20's rows? That needs F20's layout.
6. Stale carries. DQ-11 lists a flat zero-volume ^KS11 row on 2024-09-12, inside the trailing-756 label window. Spec
   L1324 says a stale carry is never read as a zero return. The T-VT-01, T-LABEL-01 and T-B5-01 bodies read every row as
   a close. Should ⑨-2 drop such rows from F13, or should the layout add open, high, low and volume so the bodies can
   flag them?

Readings to confirm:

7. G-STALE-01: decisions are each market's sessions at the close-print bound, with knowledge equal to the decision.
   Rows are re-stamped at their publication instant. The "schedule-aware" column is the share without the
   source-exception list. A decision with no visible record counts in the denominator, unflagged.
8. G-STALE-01: should the v1.2-rule columns ("1 trading day", "3 days") and the median and max ages be defined, or left
   unasserted? The spec does not say which trading calendar the 1-day rule counts on, or on which date an age is
   measured. `results/QX_DLA_staleness.csv` has no ACQUISITION row.
9. T-MISS-01: the vendor-tag clause (a vendor value across the gap is `vendor_derived_across_gap`) is not asserted on
   real data. The old reason named SAHMCURRENT, which has no fixture; `docs/macro_fixtures.FRED_IDS` lists SAHMREALTIME.
   Should SAHMREALTIME.csv be added to the body?
10. Two G-POST-01 sites now compute the same eight golden rows from the same files. The `macro_m1_fixtures.py` one adds
    point-in-time visibility, F01 and the F20 gate. Should both stay, or should one delegate to the other?
11. T-LABEL-01: is the percentile the share of trailing-756 values at or below sigma(t), with t included? The ±5
    tolerance absorbs the at-or-below versus strictly-below choice (about 0.13). `goldens.csv` already holds G-B5-04
    rows for the US figures (`us_sigma` 0.107, `us_q1` 0.105, `us_q2` 0.127, `us_q3` 0.152, `us_percentile` 28), each
    listing T-LABEL-01 in its `tests` column; the body asserts only G-B5-04's two labels. Should T-LABEL-01 assert the
    US rows too, once question 12 settles their input? Should the replay run on `CalendarClocks` over the signed files,
    behind a computed owner gate, rather than on the module's stub calendars? A probe found the stub sessions equal to
    the signed sessions over both replay windows.
12. T-VT-01 / T-LABEL-01: the replay files the ^GSPC rows as `VT_SERIES['US'] = US_SLEEVE_OFFICIAL_CLOSE` (a Yahoo
    `vendor_close` in a backtest declaring Yahoo), because the spec's US label is on the S&P 500 (L6304). But
    `goldens.csv` names `F13;U1` as the inputs of every G-B5-04 row, and U1 is French Mkt-RF from 1990-02-01 to 2026-08
    spliced with ^GSPC for Sep-2026 (F10 + F14; ACQUISITION.csv:33), not F14 alone. Which input should the US label
    replay read, F14 or U1? The answer decides whether the G-B5-04 US rows can be asserted (question 11).
13. T-B5-01: the origin count is asserted exactly (2,594) using the harness's own convention: origins from 2016-03-01,
    origin t forecasts t+1, the last origin the session before 2026-10-02. Is that the council's convention? The PIT p
    is read as the chi-square p (L3207, `forecast_eval.b5`), not the KS p. Should a later part assert the other
    G-B5-01 lines (normal form, EWMA(0.94), every-7th subsample, GARCH)?

Calendar inputs (owner-signed files):

14. T-CLOSE-02 waits for a signed `kr_sessions` `saturday_close` row effective on 1997-06-07 and a signed `csat_window`
    row for 2015-11-12. Spec L2015, L2063 and L2067 put both on the owner from the KRX notice, and the shipped file
    records both as absent. Is waiting for them the intended contract? The conditional-era bounds (2015-06-12,
    2014-06-02 and the 1997-06-07 Saturday) are asserted as close + 30 s + the extension the file signs for the session.
    The shipped `core/calendars/data/kr_sessions.yaml` says two things about those rows. Under `unverified`:
    "random_end_extension rows (conditional random end before 2015-06-15) are absent: no extension is assumed". Under
    `owner_must_sign`: "random_end_extension rows for sessions before 2015-06-15 whose conditional random end was
    triggered". So the three clauses wait while `owner_must_sign` still lists `random_end_extension` rows. Is the
    contract that the owner removes that entry once the triggered sessions are signed, or once the owner rules that the
    list is empty and final?
15. Extending signed coverage. `holidays_KRX` would have to start by 1997-01-01 for T-CLOSE-02, and by 2015-12-04 for
    G-STALE-01. `holidays_JPX` would have to start by 2024-10-28. `holidays_NYSE` and `holidays_CBOE` would have to
    start by 2015-12-04. Is that extension planned?
16. HKEX: spec L2023 says 16:00 HKT, but the signed `market_closes` row says 16:10 (closing auction). The body asserts
    the signed row and a floor of 08:00Z (L1967). Confirm.
17. TSE: the old Tokyo close is read on the last TSE session of 2024-10-28..2024-11-04, because 2024-11-04 (the
    synthetic test's date) was a Tokyo exchange holiday. That rests on this track's own knowledge; the shipped
    `holidays_JPX` starts in 2025. Confirm when the 2024 Japan calendar is signed.

Fixture vintages (added at review):

18. T-MISS-01 reads one CPIAUCSL and one UNRATE value per month, from the column named by the id. ACQUISITION.csv:22
    lists the FRED snapshot "with ALFRED vintages; vintages as of 2026-10-02", and spec L1435 (CPI) and L1436 (UNRATE)
    name a first release (`output_type=4`) and a current value. Which vintage column should the body read for
    CPIAUCSL and UNRATE, and in which form: long (one row per month and vintage, which `_monthly` refuses today) or
    wide (one column per vintage)? Which vintage was S11/`cpi_yoy_aug2026` (3.353%) computed on? Until then the body
    reads the `<id>` column as the value FRED served on 2026-10-02. It also refuses any month after Aug-2026 (L6347,
    L1355). If the snapshot was taken after a 2 October release of the September household survey, a Sep-2026 UNRATE
    row would be refused; should it be?

### Demonstrations on invented data

Each body is shown to PASS and to FAIL on invented in-memory rows; no KRX, Yahoo, FRED or QX data is used. Each FAIL
case asserts the message of the clause it targets.

- **G-POST-01** (`macro_m1_pit.py`). Rows built to the golden values pass on the synthetic signed set, also with a
  float32 artefact on the close and with a ^KS11 row of 9,500 dated 2026-10-05 (not read). The row exactly 200 closes
  back moves the ratio by its share of the mean; the row 201 back does not move it. Sixteen value cases fail:
  - the 6,943.66 print stored as the close, or beside it;
  - two ^KS11 rows on 2026-09-01;
  - a previous close of 7,100, or the 1-Oct row missing with 30-Sep at the previous close's level;
  - a peak of 9,300, or of 9,200 (inside the drawdown tolerance, caught by the peak clause), or on 2026-06-23;
  - a lower 200-day base;
  - Samsung 273,750 or SK hynix 1,832,000;
  - no 2-Oct stock rows, or a stock row coded 005935;
  - a KRW=X last row of 1,360.63, or the provisional 2-Oct KRW=X row kept;
  - the KRW=X value 20 observations back off by 2%.

  A layout case without `code` also fails. The calendar gate covers the fortnight on the synthetic set and refuses
  the unsigned one.
- **G-POST-01** (`macro_m1_fixtures.py`). 260 weekday KS11 closes, 40 KRW=X closes, F01's last five rows and the stock
  closes, built from the golden values, pass on the synthetic signed set. Twenty-two edited-row cases fail:
  - visibility and stamps: a 2-Oct row not visible at 06:31Z; intraday prints at 10:56 KST in F13 and F01; F27 rows
    not visible or stamped 05:00Z; a later KS11 row visible;
  - values: closes of 7,003.75 and 6,943.66, a previous close of 6,800, peaks of 9,300 and 9,200, the peak moved by a
    day, a flat level +200, Samsung 276,001 and SK hynix 1,840,000, KRW=X 1,356.85, the KRW=X row 20 back at 1,400, the
    provisional 2-Oct KRW=X row visible;
  - the previous visible KS11 row not 1 Oct: that row missing with 30 Sep at its level, or stamped available at
    07:00Z;
  - row counts: 150 KS11 rows, 15 KRW=X rows.

  The row exactly 200 closes back moves the ratio; the row 201 back does not. Five layout cases also fail, one of them
  a 2-Oct row available at 06:00Z, before its 06:30Z close. While any fixture is absent, the test checks that the real
  test's REFDATA reason names each absent id.
- **T-PRINT-01 on F13**. Invented closes on the synthetic signed calendars: 5,584.71 then 5,251.87 pass, also with a
  float artefact, and so does a previous close of 5,585.01 (-5.9649%, inside the printed precision). It fails on:
  - the 10:31 print stored as the close, or beside it;
  - 5,251.88;
  - a previous close of 5,560, or of 5,585.05 (-5.9656%, just outside ±0.005 pp);
  - the 2026-03-06 row missing;
  - rows marked `official_close`.

  The calendar gate covers the fortnight on the synthetic set and refuses the unsigned set.
- **G-STALE-01**. Invented releases on every expected date over 2016-06-01..2018-11-30 pass at both closes. The DEXKOUS
  2017-01-20 and DTWEXBGS 2018-03-02 source skips flag four decisions each without the list and none with it; the
  demonstration checks the exact instants (the US and KRX closes of 25, 26, 27 and 30 January 2017 and of 7, 8, 9 and
  12 March 2018), which move if the decision instant moves. The Wednesday DEXKOUS skip of 2018-12-05 flags none. It
  fails on:
  - a Friday H.10 release deleted on a date not in the list (a);
  - a staleness check that never flags (the converse of (a));
  - no-skip clocks standing in for the loaded list (b);
  - DEXKOUS over Q1 2017 at 6.45% (outside the golden band);
  - DTWEXBGS over 2018 at 1.59% (above 1%);
  - two DGS10 releases deleted (1.16%);
  - two VIXCLS closes deleted (0.47% > 0%);
  - F07 read with F18 provenance.

  `_stale01_waiting` is pinned: empty on the synthetic set, exactly the `holidays_KRX` gap on the short-KRX set, and
  the refusal on the drafts set.
- **T-MISS-01**. Invented CPI growing 3.353% a year, with Oct-2025 written as FRED's ".", and invented UNRATE pass. It
  fails on:
  - a Sep-2026 CPI or UNRATE row;
  - an Oct-2025 CPI or UNRATE value;
  - an Aug-2026 CPI giving 3.37%;
  - broken stand-ins for `core.ficc.pit`'s functions: an over-strict YoY, a positional YoY, a carry-forward YoY or MoM,
    and a 3-month mean over the members present;
  - a CPIAUCSL file carrying `series_id` CPILFESL, and two Aug-2026 rows (one per vintage) at `_monthly`.
- **T-CLOSE-02**. `_check_close02` passes on the synthetic set. It also passes on `close02_signed_set()`, which holds
  only `CLOSE02_FILES` plus an invented signed 2015-11-12 `csat_window`; there nothing waits, and the signed row sets
  the close. It passes too with a Tokyo holiday on 2024-11-04. The waiting list is pinned exactly on the synthetic,
  short-KRX and drafts sets, and on that signed set with the shipped `owner_must_sign` entry for `random_end_extension`
  rows added, where exactly the three conditional-era clauses wait. A `holidays_KRX` file starting 2016-06-01 is a gap
  for the 2016 clause, and the clauses on it raise `CalendarCoverageError`. Thirty-eight table cases and an
  unknown-market case fail, one per value clause. Each uses a wrong injected config, a wrong signed file or a wrong
  clock; the added one is two overlapping signed 2015-11-12 `csat_window` rows read by a clock that takes the first.
- **T-VT-01**. Sixty invented closes whose last 20 returns give rv20 exactly 0.2882 pass, with vt = 0.20 / 0.2882. It
  fails on:
  - rv20 0.2895, with vt still inside its tolerance;
  - a vt target of 0.25, with rv20 inside its tolerance;
  - the 2-Oct row missing, an intraday print at 01:56Z, or the row available at 06:31Z;
  - a missing session inside the window (`MissingInput`);
  - a 2026-10-06 row available at the decision;
  - 15 closes (`insufficient_history`);
  - three layout cases.
- **T-LABEL-01**. Invented KOSPI and US closes built to the golden quartiles pass: 0.157 / 0.1855 / 0.336, sigma 0.2882
  at the 69.97th percentile, "elevated" and "stressed"; and US "normal". It fails on:
  - each quartile alone, and the percentile alone;
  - sigma(t) 0.35;
  - an expanding history at 0.30;
  - a US sigma(t) of 0.16;
  - 700 KOSPI rows (680 sigma values);
  - a US intraday print;
  - an F14 row dated 2 Oct available at the 1-Oct decision.

  A KOSPI row 650 sessions back (inside the trailing 756, outside the 20-return vt window), stamped available at
  07:00Z with its close × 1.5, passes on a block layout (`LABEL01_KR_BLOCKS_Q1_EDGE`) where reading it would move Q1
  from 0.157 to 0.166: neither `market_vol_target` nor the body reads it.
- **T-B5-01**. An invented Student-t(6) path (seed 293) with invented holidays leaves 2,594 sessions in the window and
  passes: exceedance 0.0486, PIT p 0.1031, PASS. It fails on:
  - the path ending on 2026-10-01;
  - one extra session (2,595 origins);
  - seed 9 (exceedance 0.0544) and seed 8 (PIT p 0.9987);
  - a wrapped harness reporting FAIL;
  - the x 0.7 run left unscaled;
  - the close in a column named `value`, a row carrying F01's id, and rows out of order.

  The demonstration also compares `B501_PROVENANCE` with the F13 row of `docs/macro_fixtures.REFERENCE_FILES` and
  `B501_COLUMNS` with part 1's `F01_COLUMNS`.

### Ratchet

The rules are those of part 1. `test_la02_converted_pit_bodies_stay_convertible` parses the named functions and the
module helpers they call. It refuses:

- an unconditional NotRun, including one under a constant `if`;
- a NotRun before the fixture gate;
- an "unreachable" or "not implemented" failure;
- a body that calls no `_check_*` helper that asserts.

Converted, 13 sites, all on the floor:

- part 1's four;
- `macro_m1_pit.py`: G-POST-01, T-PRINT-01 on F13, G-STALE-01, T-MISS-01;
- `macro_m1_calendars.py`: T-CLOSE-02 on the signed files;
- `macro_m1_fixtures.py`: G-POST-01;
- `macro_m2_risk.py`: T-VT-01, T-LABEL-01;
- `macro_m3_estimators.py`: T-B5-01.

Remaining, 4 sites:

- T-FIX-01;
- T-REGIME-01 full range;
- I-05;
- G-REF-01. Its label now records why it stays.

`LA02_SITES` (17) is unchanged. The lists still partition it. `LA02_FLOOR_SIZE` makes the floor's size a stated number
that a later part raises.

## What stays NOT_RUN today, and why

The guarded run below shows each of the nine converted sites NOT_RUN:

- REFDATA, because a fixture is not in `MANIFEST.csv`:
  - G-POST-01 in `macro_m1_pit.py` (F13, F16, F27) and in `macro_m1_fixtures.py` (F01, F13, F16, F20, F27);
  - T-PRINT-01 on F13;
  - G-STALE-01 (DTWEXBGS, DEXKOUS, DGS10, F07);
  - T-MISS-01 (CPIAUCSL, UNRATE);
  - T-VT-01 (F13);
  - T-LABEL-01 (F13, F14);
  - T-B5-01 (F13).
- OWNER: T-CLOSE-02. The signed `holidays_KRX` covers 2026-01-01..2027-12-31, against needs from 1997, 1999, 2014, 2015,
  2016 and 2025. `kr_sessions` has no signed `csat_window` row on 2015-11-12 and no `saturday_close` row on 1997-06-07,
  and still lists `random_end_extension` rows under `owner_must_sign`. The signed `holidays_JPX` covers 2025 onward,
  against 2024-10-28..2024-11-05.

Once the fixtures are listed:

- T-PRINT-01 on F13 and both G-POST-01 sites pass their calendar gate today: the shipped `holidays_KRX` covers 2026
  (a probe of `_official_calendar` over 2026-09-18..2026-10-02 returned the shipped set, with 2026-10-01 the previous
  KRX session of 2 Oct).
- G-STALE-01 would be NOT_RUN (OWNER) on the shipped calendars. `holidays_CBOE` and `holidays_NYSE` cover
  2025-01-01..2027-12-31 and `holidays_KRX` covers 2026-01-01..2027-12-31, against 2015-12-04..2026-10-25 (computed by a
  probe of `_stale01_waiting`).
- The `macro_m1_fixtures.py` G-POST-01 site also waits for F20, whose ACQUISITION source is the council archive outside
  the repository.

The four remaining sites stay NOT_RUN for the reasons in "Next parts".

## What did not change

- No product code changed: nothing under `core/`, `data/`, `ui/` or `docs/*.py`. That includes the frozen harness
  sources (`core/quant/strategies.py`, `validate.py`, `cardp.py`, `docs/macro_overlay_study.py`); `definitions_md5` is
  unaffected. `docs/vol_backtest.py` and `docs/macro_fixtures.py` are imported and called, never edited.
- No data, registry or record file changed: `tests/fixtures/macro/goldens.csv`, `ACQUISITION.csv` and `MANIFEST.csv`,
  `tests/macro_registry.csv`, `qa/acceptance_results.json`, `data/macro`, the calendars, ledgers, cards and registers.
- Every existing test keeps its name and its `test_ids`, checked statically against `HEAD` for all five modules. The
  nine new tests carry no `test_ids`, so the `implemented_in` column stays in sync. Each module still ends with the
  guarded `run_module` main. `tests/macro_m1_fixtures.py` stays CRLF; the other four stay LF and ASCII.
- The new and changed tests read the data fixtures under `tests/fixtures/macro` only through `require_fixture`. They
  read `goldens.csv` directly through `tests/golden_tools` (`G.golden`, `G.assert_golden`, `golden`) and `MANIFEST.csv`
  through `load_manifest()` (the `macro_m1_fixtures.py` and `macro_m2_risk.py` demonstrations), both read only. They read
  the shipped calendar files only for their signing, coverage and `owner_must_sign` state, or as the official calendar.
  None of them reads `docs/asset_expansion/cache`. Two existing tests that this part does not change do read it:
  - `tests/macro_m1_pit.py::test_stale_01_schedule_aware_clauses_and_local_smoke` opens `fred_DEXKOUS.csv`;
  - `tests/macro_m3_estimators.py::test_g_b5_02_spy_refdata_with_smoke_on_local_cache` reads `yf_SPY.csv`.

  Running either module whole therefore touches the cache.
- Two `test_g_post_01_body_passes_and_fails_on_invented_rows` functions now exist, one in `macro_m1_pit.py` and one in
  `macro_m1_fixtures.py`. Results are keyed by module (`macro/<module>/<test>`), so the names do not collide.
- On the next owner QA run, the counts rise by the nine new tests (PASS where they run). Five NOT_RUN reasons read
  differently, because each now names the inputs it waits for as computed: G-POST-01, T-PRINT-01 on F13, G-STALE-01 and
  T-MISS-01 in `macro_m1_pit.py`, and T-CLOSE-02. The other four converted sites keep their gate, so their reasons are
  unchanged.

## Verification (Linux, 2026-11-10)

All runs used part 1's scratch runner. It installs `sys.addaudithook`, which refuses any open, listdir, scandir or
mkdir under `docs/asset_expansion/cache`, any `.env` and anything under `~/.nextgen`, and refuses every
`socket.connect`. The runner stubs `dotenv` before any import and runs each test inside
`tests.macro_acceptance.hermetic()`. Python 3.13.17, NumPy 2.3.5, SciPy 1.18.0.

- **Integration run, by id.** 129 test functions: every test in the five touched modules except the two cache readers
  named above. That covers the nine converted sites, the nine demonstrations, the T-HERM-01 rules and both LA-02
  ratchet tests. Result: 94 PASS, 35 NOT_RUN, 0 FAIL, no guard refusal.
  - The 35 NOT_RUN are the nine converted sites, part 1's NOT_RUN sites, and unchanged REFDATA or OWNER tests of
    these modules.
  - `test_la02_converted_pit_bodies_stay_convertible` and `test_la02_ratchet_refuses_the_old_forms` PASS with the
    updated lists.
  - `test_every_required_fixture_is_generated_or_registered` and `test_no_golden_test_passes_on_its_fixture_gate_alone`
    PASS.
  - The slowest new tests: the T-CLOSE-02 demonstration (20.4 s) and the T-LABEL-01 demonstration (8.1 s).
- **Integration mutation probe.** One mutant per converted body, each compiled in memory into a fresh module object;
  the worktree files were never written. All 9 were caught by the site's demonstration:
  - the G-POST-01 golden comparison disabled (both sites);
  - the T-PRINT-01 close compared to the hundreds;
  - the VIXCLS 0% bound relaxed to 1%;
  - an Oct-2025 CPI value accepted;
  - a tautological 2016-07-29 T-CLOSE-02 close;
  - the T-VT-01 goldens not asserted;
  - the US T-LABEL-01 label not asserted;
  - the T-B5-01 x 0.7 clause disabled.
- **Track checks, reported by the four conversion tracks** (not re-run at integration, and against the other tracks'
  files as they stood at the time):
  - in-memory mutation checks: 30/30, 22/22 and 14/14 caught; 11/12 for T-B5-01, where the survivor drops
    `origins_from` from the x 0.7 run and changes no verdict;
  - end-to-end probes: the real test functions run with `require_fixture` pointed at invented files, for T-CLOSE-02
    (on the shipped files re-signed in a temp dir with widened coverage and invented owner rows), T-VT-01, T-LABEL-01
    and T-B5-01;
  - a probe in which the parallel G-POST-01 track's invented files pass the `macro_m1_pit.py` layout and body;
  - a calendar probe: the stub sessions equal the signed sessions over the T-VT-01 / T-LABEL-01 replay windows.
- **Static checks.** `test_ids` per function are identical to `HEAD` in all five modules. The only added tests are the
  nine demonstrations. `ruff --select F` finds no new finding: the unused imports it reports were already present at
  `HEAD`.

### Review fixes (second commit)

A review of the first commit found sixteen points. The second commit, a new commit on the same branch, fixes all of
them, two in a different form from the one suggested (G-STALE-01's converse and the window demonstrations, below):

- G-POST-01 (both sites): the return's previous row must be the previous KRX session on the signed calendar (the
  owner gate as above). `macro_m1_fixtures.py` also refuses a row available before its `obs_utc`. Both demonstrations
  test the 200-close window's boundary rows; the `macro_m1_pit.py` one also tests a later ^KS11 row and two rows on
  one date.
- T-PRINT-01: a demonstration case on each side of the ±0.005 pp edge.
- G-STALE-01: the converse of clause (a) in `_check_stale01`, and exact flagged instants in its demonstration. The
  review suggested requiring a hit for every listed date in the span. On the shipped list that would fail on real
  data: a skip that is not the last observation of its H.10 week (DEXKOUS 2018-12-05, 2018-12-24, 2019-01-14,
  2019-02-20 and 2021-01-20; DTWEXBGS 2018-12-05) is published with the later days of that week, so no decision sees
  it missing. The demonstration shows this for DEXKOUS 2018-12-05 on the synthetic set; for the shipped dates it is
  reasoned from the H.10 weekly rule, not run. The converse is therefore stated over the decisions between the missed
  date's deadline and the next stored release.
- T-MISS-01: months after Aug-2026 are refused, and the vintage reading is declared (question 18).
- T-CLOSE-02: the `random_end_extension` gate and the one-row rule for the pre-2016 CSAT window (question 14).
- T-LABEL-01: the labels come from G-B5-04; a late-row demonstration case; questions 11 and 12 rewritten.
- T-B5-01: L5737; the provenance and columns are pinned.
- This record: the two-decimal exception, question 4, the layout and read-path statements.

The review suggested that the G-POST-01 window demonstrations move `close_over_200d` by more than 0.01. No single
row can do that: closes are positive and at most the 9,114.55 peak, so one row moves the ratio by at most about
0.006. The demonstrations instead assert the exact ratio, which a 199- or 201-close window changes; they type the 200
of the golden note rather than reading `GPOST01_SMA_N` / `GPOST_SMA_N`, so a changed constant is caught too.

Checks of the second commit, with the same guarded runner:

- The same 129 test ids as the integration run: 94 PASS, 35 NOT_RUN, 0 FAIL, no guard refusal. Every status is
  unchanged. The only NOT_RUN reason that changed is T-CLOSE-02's, which now also names the three conditional-era
  clauses waiting on `owner_must_sign`.
- A mutation probe, 20 mutants each compiled in memory from the module source (the worktree files were never written):
  19 caught by their demonstration. They cover the ^KS11 look-ahead filter, the 199- and 201-close windows (both
  sites), the duplicate-date guard, the previous-session clauses (both sites), the T-PRINT-01 tolerance widened to
  0.40 pp, G-STALE-01 decisions moved by 20 h or by 1 min, the converse removed, the T-MISS-01 month cap removed, the
  `available_at_utc >= obs_utc` layout check removed, the T-LABEL-01 availability filter removed, the US G-B5-04
  label dropped, the CSAT first-row expectation restored, the extension gate removed and `B501_PROVENANCE` changed.
  The survivor reads G-STALE-01 with knowledge a day after the decision. It is equivalent on this body: every stored
  row is first seen at its publication instant, so visibility depends on the decision alone.
- Static: `test_ids` per function identical to the first commit in all five modules, no test added or removed,
  `tests/macro_m1_fixtures.py` still CRLF, the other four still ASCII; `ruff --select F,E9` reports the same four
  pre-existing unused imports as before.

### Not run, and unverified

- `tests/run_all.py`, the whole macro modules, `tests.macro_m9_lab` and `tests.macro_m8_pipeline` were not run.
  `tests/macro_m0_harness.py::test_registry_implemented_in_matches_test_ids` was not run, because it imports every
  macro module; that it still passes rests on the static `test_ids` comparison.
- The two cache-reading tests named above were not run.
- Windows behaviour is unverified, and no CI runs the macro suites.
- No real fixture exists, so no converted body has run on real data. Every number checked comes from invented rows.
  These are unverified:
  - whether the ⑨-2 files will have the declared columns and provenance (the `close` column, the F27 long form, FRED's
    missing marker, monthly `obs_date` on the first of the month, the calendar-bound stamps);
  - whether the real files reproduce the golden values: the G-POST-01 M1 rows, 5,251.87 and -5.96%, rv20 0.2882 and
    vt 0.694, the label quartiles and percentile, 2,594 origins with exceedance 4.70% and PIT p 0.107, the CPI YoY
    3.353%, and the G-STALE-01 shares;
  - whether Yahoo's ^KS11 carries the 2026-03-06 row and the 2026-10-01 row;
  - whether the F18 snapshot holds any month after Aug-2026 (question 18);
  - whether R4 dropped the 2024-09-12 flat ^KS11 row when it computed the label quartiles. If it did and F13 keeps the
    row, the quartiles could move by an unknown amount;
  - whether real DTWEXBGS has gaps beyond the signed `source_skipped` list, and whether real VIXCLS is complete on every
    CBOE session;
  - the G-STALE-01 run time on ten years of data (about 43,000 `is_stale` calls; not measured).
- The G-STALE-01 OWNER path on fully signed 2015-2026 calendars, and T-CLOSE-02 on the owner's real Saturday-close and
  pre-2016 CSAT rows, were exercised only on synthetic or re-signed temp sets with invented rows.
- That 2024-11-04 was a Tokyo exchange holiday rests on a track's own knowledge (question 17).
- The `KeyError` in `docs/macro_fixtures.calendar_available_at` for KS11, KRWX, GSPC and 005930 is read from the code;
  the generator was not run (question 3).

## Next parts

Still unconverted, as listed in `LA02_REMAINING`:

- **T-FIX-01** (`tests/macro_m1_pit.py::test_fix_01_regeneration_at_level_1_tolerance_refdata`). It needs the council
  archive outside the repository (`CATALOG.md`, `scripts/`, `results/QX_DLA_postpatch.csv`), plus an ACQUISITION and
  MANIFEST path for it.
- **T-REGIME-01 full range** (`tests/macro_m1_calendars.py::test_regime01_full_range_expected_values_file`). It needs
  an ACQUISITION row for `kr_regime_tags_expected.csv`; part 1 corrected its reason.
- **I-05** (`tests/macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata`). It needs the
  LA-07 harness change and the LA-30 ALFRED vintages first.
- **G-REF-01** (`tests/macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata`). No product harness computes the R-11
  record: `core/quant/refusal.py` holds it as archived DL-A records, "never recomputed here". A replay would have to
  invent the R4b recipe: the VT20 on/off/S/2x books per cost, the DEXKOUS-to-KRX timing, and the onset exposure and
  threshold. It also needs signed FED and KRX holiday calendars from 1997-04, F16 in its gate, and an owner ruling on
  whether the DL-A values are to be reproduced at all.

Each conversion moves its function from `LA02_REMAINING` to `LA02_CONVERTED`, adds it to `LA02_CONVERTED_FLOOR`,
raises `LA02_FLOOR_SIZE`, and adds a PASS/FAIL demonstration with a FAIL case per value clause.
