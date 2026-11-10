# Look-ahead audit LA-02, part 3 (⑨-1/2/d): reference-data preparation

This is the third part of the LA-02 fix from the 2026-11-04 look-ahead audit
(`git show 7749450:docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md`, LA-02 at lines 279-284). Parts 1 and 2
(`docs/product/LOOKAHEAD_LA02_PART1_2026-11-10.md`, `docs/product/LOOKAHEAD_LA02_PART2_2026-11-10.md`) gave 13 of the 17
REFDATA or owner-input point-in-time tests a real body and left questions for the owner. On 2026-11-11 the owner
ruled on six points those parts had left open. This part carries the six rulings out: it removes the two conflicts that
would have stopped the reference files from being built or read, changes how a vendor price is compared, converts two
more tests, and lists what the owner has to sign. No test changes status today: every real-data test below is still
NOT_RUN until ⑨-2 lists its fixture, or until the owner extends a signed calendar file.

Three things are not finished:

- **A merge is blocked** by one stale cell of `MANIFEST.csv`. See "Follow-up needed before merge".
- **Ruling 2 is carried out for four of its five ids.** KS11, GSPC, 005930 and 000660 are stamped from their market
  calendar. KRWX (F16, Yahoo KRW=X) is declared and refused, because no calendar rule exists for an FX close. Both
  G-POST-01 sites gate on F16, so they cannot run on real data until the owner answers question 1.
- **The G-REF-01 body would FAIL on the real F20 as the spec describes it.** The body reads F20 in a layout this part
  assumed. The owner has to say where the R-11 record is archived and in what layout before ⑨-2 lists F20 (question 2).

A code review of the first two commits led to a merge of main and a fix commit. "/code-review fixes" lists what changed
and what was left for the owner.

## Authority and scope

The authority is the owner's reply of 2026-11-11 to Claude's table of 14 remaining decisions. The reply and Claude's
reading of each answer are recorded in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` by commit `275ec93`, section
"2026-11-11, Claude Code 채팅: 남은 결정 14건에 대한 답 (원문)". That commit reached main with PR #100 (`1a8b29f`)
and this branch with the merge of main (`7611064`), so the cited section is in the tree. The reply, verbatim, for the
six decisions this part covers: "1-승인, 2-승인, 3-승인, 4-승인, 5-승인, 6-승인". The table rows the reply answers, each
with its recommendation as the owner read it (verbatim):

1. **자료 파일 열 이름.** "`close`로 통일하고 `fixture_lines` 한 곳만 수정. 1부의 F01 형식과 같고, 시험 5곳이 이미 이
   형식이라 고칠 곳이 가장 적습니다. 생성기가 실제로 쓰는 열 이름은 수정 전에 확인하겠습니다." Answer form `1-승인`.
2. **생성기의 미등록 시계열 거부.** "생성기 수정, 레지스트리는 그대로. 레지스트리는 운용 신호의 입력 목록이라 참조용
   시계열을 넣으면 운용 범위가 넓어집니다. 생성기만 참조 파일의 시각을 시장 달력으로 계산하게 바꾸는 편이 범위가
   좁습니다." Answer form `2-승인`.
3. **공식 달력 서명 범위.** "서명 범위 확장. 서명 전에는 해당 시험이 계속 '소유자 대기'로 남아 누출 감사(LA-02)가 실제로
   닫히지 않습니다. 서명은 소유자 작업이고, 필요한 행 목록은 제가 미리 뽑아 드리겠습니다." Answer form
   `3-승인(행 목록 요청)`.
4. **가격 비교 정밀도.** "공급사(Yahoo) 가격만 소수 둘째 자리로 비교하고, KRX 공식가는 정확 일치를 유지. 기대값 자체가
   소수 둘째 자리로 인쇄돼 있어 반올림 비교로 잃는 정보가 없습니다. 스펙 문구와 다르게 적용하는 것이라 승인이
   필요합니다." Answer form `4-승인`.
5. **G-REF-01 재현 여부.** "재현하지 않음. 시험은 기록이 있는지와 값이 일치하는지만 확인합니다. 재현하려면 계산 방법을
   새로 만들어야 해서 '기록'의 의미가 흐려집니다." Answer form `5-승인`.
6. **T-REGIME-01·T-FIX-01.** "T-REGIME-01은 ACQUISITION 행 추가를 승인해 주시면 바로 시험할 수 있습니다. T-FIX-01은
   보류를 권합니다. 외부 자료의 크기와 이용 조건을 먼저 확인해야 합니다." Answer form `6-승인(REGIME 추가, FIX 보류)`.

Ruling 12 of the same reply ("12-함께") puts the LA-30 point-in-time data that I-05 needs with the reference-data
stage ⑨-2; it is cited under "What is left".

- Branch `claude/refdata-prep-20261111`, started from main `5f1ead5` (parts 1 and 2 are on main). Main `1a8b29f`
  (PR #98, the owner UI review, and PR #100, owner rulings 7 to 10) was merged in by `7611064`. Against that main the
  branch changes 14 files: the 13 of the first two commits and the part 2 record, which gained a note.
- Four commits. `5926eeb` carries rulings 1 and 2 (product code under `docs/` and their tests). `8ed8112` carries
  rulings 3 to 6 (test files, one register row, the signing request and this record). `7611064` merges main. The
  fourth carries the review fixes.
- Scope: the four sites part 2 left in `LA02_REMAINING`. This part converts two (T-REGIME-01 full range, G-REF-01).
  T-FIX-01 stays, held by the owner (ruling 6). I-05 stays, waiting for data (ruling 12).

## What changed

| Item | Before | Now |
| --- | --- | --- |
| Ruling 1. The product's F13 reader, `docs/vol_backtest.fixture_lines` | Read `obs_date` / `value` and skipped blank cells; a probe on `5f1ead5` showed an `IndexError` on a file with a `close` column, the layout every part 2 body reads | `fixture_closes` reads `obs_date` / `close` (`FIXTURE_COLUMNS`). It raises `ValueError` naming file and line for an absent column, a blank, "." or non-positive close, an `obs_date` not written YYYY-MM-DD, a repeated or out-of-order date, or fewer than two rows. No row is skipped. `fixture_lines` takes an optional manifest |
| Ruling 1. The generator, `docs/macro_fixtures.py` | Copied a reference file's own header and named no value column, so whether F13 carried `close` depended on the reference file alone | `CLOSE_LAYOUT` declares `close` for F13, F14 and F16 and `code`, `close` for F27. `generate` refuses a reference file whose header lacks a declared column. Nothing is renamed. Since the review fix it also refuses a row a reader would refuse (`CLOSE_FILES`, below), and it stamps an F27 row with its own code as `series_id` |
| Ruling 2. The generator's instants, `calendar_available_at` | `KeyError` for KS11, GSPC, KRWX, 005930 and 000660, which are not registered, so F13, F14, F16 and F27 could not be stamped (part 2 question 3) | The five ids are declared reference series (`REFERENCE_SERIES`, derived from `REFERENCE_FILES`). Four are stamped at the scheduled close and the close-print bound of the market their `REFERENCE_FILES` row names: KS11, 005930 and 000660 on KR, GSPC on US. The fifth, KRWX, is refused by name: its row names the market FX, and no FX clock exists (question 1). `calendar_check_fixture` runs the post-close check on the same market. An id that is neither registered nor declared is refused with the same error text. The registries are unchanged |
| Review fix. A generator run, `generate` and the command line | Wrote the whole set or nothing, and wrote each file as it went: a run refused at F02 left F01's fixture in the output directory with no manifest row | `--only F13 F14 F27` (or `only=`) writes the files of the named fixture ids. Every file is built and checked in a temporary directory, and the output directory is written only when the last one passed |
| Ruling 4. Price comparison at both G-POST-01 sites and in T-PRINT-01 on F13 | Every price exact (spec L5735), so a float artefact such as 7003.740234375 failed | A Yahoo vendor price (the ^KS11 closes of F13, the KRW=X closes of F16) is compared after rounding to two decimals. A KRX official price (the won closes of F27, the official KOSPI close of F01) stays exact. One rule, `tests.macro_m1_calendars.price_as_compared` |
| Ruling 5. G-REF-01, `tests/macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata` (ids G-REF-01, G-KR-05, G-KR-05s, G-POST-01) | Gated on F13 and `DEXKOUS.csv`, then an unconditional `NotRun` | Gate on the archived record table F20 `QX_DLA_postpatch.csv`. It is read in a declared layout and `_check_g_ref_01` compares the record with `goldens.csv` at Level 1. Nothing is recomputed and no price or FX history is read |
| Ruling 6. T-REGIME-01 full range, `tests/macro_m1_calendars.py::test_regime01_full_range_expected_values_file` | Unconditional `NotRun("OWNER: ...")`: the expected-values file had no register row, so a fixture gate on it would have failed T-HERM-01 | `require_fixture("kr_regime_tags_expected.csv")`, the file read in a declared layout, a computed OWNER gate on the signed `kr_regime_tags.yaml` (`_regime01_signed`), then `_check_regime01` |
| Ruling 6. `tests/fixtures/macro/ACQUISITION.csv` | No row for the expected-values file | One row added. It is an open row (licence, owner and md5 blank): it does not say the file exists |
| Ruling 3. Signing request | Part 2 named the calendar gaps inside its NOT_RUN reasons and its question 15 | `docs/product/CALENDAR_SIGNING_REQUEST_2026-11-11.md` (in Korean, for the owner): per file, the span to sign, the rows and `owner_must_sign` entries, the tests waiting, the spec lines, and what each gate returned today |
| Ratchet lists in `tests/macro_m1_fixtures.py` | 13 converted, 4 remaining, `LA02_FLOOR_SIZE = 13` | 15 converted, 2 remaining (T-FIX-01, I-05), `LA02_FLOOR_SIZE = 15`. `LA02_SITES` is unchanged |

New tests, none with `test_ids`:

- First commit, `tests/macro_m1_fixtures.py`: `test_macro_fixtures_stamps_reference_series_from_the_market_calendar`,
  `test_macro_fixtures_close_layout_is_one_layout_for_three_readers`.
- Second commit: `tests/macro_m1_calendars.py::test_regime01_full_range_body_passes_and_fails_on_invented_expected_values`
  and `tests/macro_m8_forward.py::test_g_ref_01_body_passes_and_fails_on_an_invented_record`.
- Fix commit, `tests/macro_m1_fixtures.py`: `test_macro_fixtures_refuses_close_rows_no_reader_accepts` and
  `test_macro_fixtures_writes_nothing_when_refused_and_only_the_selected_files`.

Existing tests whose bodies changed (name and `test_ids` kept):

- `tests/macro_m1_integration.py::test_fixture_generator_instants_from_calendars_and_check_fixture_on_csv` (T-FIX-01)
  pinned the old refusal of KS11. It now asserts the KR stamp of KS11 and the unchanged refusal of an undeclared id.
- `tests/macro_m1_calendars.py::test_regime01_full_range_reason_reads_the_signing_state` pinned the old OWNER text. It
  now pins both computed reasons of the converted test.
- The three part 2 demonstrations that showed a float artefact FAIL
  (`test_g_post_01_body_passes_and_fails_on_invented_rows` in `macro_m1_pit.py` and in `macro_m1_fixtures.py`,
  `test_print_01_body_passes_and_fails_on_invented_ks11_closes`) now show it PASS, and a value one cent away FAIL.
- Fix commit. The two generator tests of the first commit pinned 005930 as the `series_id` of every F27 row; they now
  pin the row's own code. The T-REGIME-01 reason test also reads the real test's source. The T-REGIME-01 and G-REF-01
  demonstrations gained cases (see "Demonstrations on invented data").

### Expected values and where they come from

The spec is `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md`. Golden rows are read from
`tests/fixtures/macro/goldens.csv`, which is not edited.

- **Ruling 4, vendor prices.** The expected values are unchanged: G-POST-01 `kospi_close_2oct` 7003.74 and
  `krwx_last_row` 1356.84 (`goldens.csv`, kind `price`; L5819-5834), the peak 9,114.55 on 2026-06-22 (the
  `drawdown_from_peak` quantity; L5821) and the T-PRINT-01 close 5,251.87 (L5631). What changed is the comparison.
  Spec L5735 says "prices exact". Owner ruling 4 approves an exception for vendor prices only: a Yahoo price is rounded
  to two decimals and then compared exactly with the expected value. The reason given with the ruling is that the
  expected values are themselves printed at two decimals; the demonstrations assert that each of the four values equals
  its own two-decimal rounding. The KRX won prices, `samsung_close_2oct` 276000 and `hynix_close_2oct` 1841000, and
  F01's official KOSPI close against `kospi_close_2oct`, are still compared exactly.

  Which rule a price gets is decided by the file it is read from, not by the row's name. `GPOST_PRICE_FILES` in
  `tests/macro_m1_fixtures.py` names the file of each M1 price row, and `price_as_compared(fid, price)` rounds for F13
  and F16 and returns the price unchanged for F01 and F27. It checks the file's `value_status` in
  `docs/macro_fixtures.REFERENCE_FILES` (`vendor_close` or `official_close`) and refuses a file the ruling does not name:
  F14 (^GSPC) is a vendor file, but no body compares a ^GSPC price and the ruling names only ^KS11 and KRW=X.
  `check_gpost01_rows` also asserts that the rows with a rule are exactly the M1 rows of kind `price` in `goldens.csv`.
  Both G-POST-01 sites return their rows as read, unrounded.
- **Ruling 5, G-REF-01.** Every expected value is a `goldens.csv` row, asserted through `tests/golden_tools.assert_golden`
  at the row's Level 1 tolerance (L5734-5735): 28 rows of G-REF-01 (L5879-5882), 17 of G-KR-05 (L5776), 18 of G-KR-05s
  (L5777) and the one M8 row of G-POST-01, `gkr05_share` 0.967 (L5830; L5577 assigns it to M8). That is 64 values: counts
  exact, Sharpe differences ±0.01, drawdown differences ±0.01, shares ±0.03, ratios ±0.01, verdicts as text.
  The record is read from two places.
  - The product record, `core/quant/refusal.REFUSAL_RECORDS["R-11"]`. The module says of it: "Archived council records
    ...: values are records, never recomputed here." It holds, for each of the four timings, the de-clustered onsets,
    the drawdown difference in percentage points and the tail ratio, plus one verdict. The body maps those onto 16
    G-REF-01 rows (`GREF01_TIMINGS`, `GREF01_PRODUCT_FIELDS`). The drawdown difference is read as the ETF 3 bp column
    of the G-REF-01 table: the record's -1.7 / -1.3 / -1.3 / +0.3 are that column's values (L1647, L5879-5882), and the
    stock 35 bp column reads -1.7 / -1.4 / -1.5 / -0.4. The record's percentage points are multiplied by 0.01 to match the
    golden rows, which are decimal fractions.
  - The archived result table F20, `results/QX_DLA_postpatch.csv`. Spec L5815 gives it as the source of G-POST-01.
  The body asserts three things: the product record equals its 16 golden rows; every value F20 records under the four
  golden ids equals its golden row; and every one of the 64 golden rows has a record, in F20 or (for those 16) in the
  product record. A golden row with no record is a FAIL that names it. This is the ruling's "기록이 있는지".
- **Ruling 6, T-REGIME-01** (L2098). The expected values are the cells of the owner's expected-values file. The body also
  asserts the eight values the spec prints, on the signed tags: `price_limit` 0.08 on 1997-06-02, 0.12 on 1998-06-01, 0.15
  on 1999-06-01 and 0.30 on 2015-06-15; `fx_regime` `peg_1997` on 1997-10-01; `etf_available` false on 2002-01-02;
  `short_sale_ban` true on 2024-06-03; `sell_tax_pct` 0.20 on 2026-10-02 (`REGIME01_POINTS`). The span, 1995-01-01 to
  2026-12-31, is the spec's. A probe showed the shipped signed file returns all eight today.
- **Rulings 1 and 2** (first commit). The instants are the spec's: a KRX close at 06:30:00Z with the bound 06:30:30Z
  (L1289), an NYSE close at 20:00:00Z plus 30 s (L1290, L1310), the post-close rule of bound plus 10 minutes (L1493 rule
  5). Every other instant is compared with `core.calendars.clocks.close_stamp` on the synthetic signed set. The five ids
  and the column names are the owner ruling's.

### Declared fixture layouts

- **Close layout (ruling 1).** Part 2 declared it in the tests. The generator and the product reader now hold the same
  declaration: `close` for F13, F14 and F16, and `code` plus `close` for F27. Three readers read it:
  `tests.macro_m1_calendars.read_close_layout`, `docs/vol_backtest.fixture_closes` and the generator's refusal. The
  product reader also reads F15 (SPY) for G-B5-02, so F15 must carry `close` too, although no ruling names it.
  - The generator's `CLOSE_FILES` is every file read in this layout: the four of the ruling, F01 and F15. For each it
    applies the readers' rules to the reference rows before it writes anything: a close is a finite number above
    zero; rows are in date order and no date repeats (F27: no date and code pair repeats, and every code is one of
    005930 and 000660); F13 and F15, which the product reader reads, hold at least two rows and every other file at
    least one. F01 and F15 declare no reference series: `REFERENCE_SERIES` is still the ruling's five ids, and SPY is
    still refused when stamped.
  - An F27 row carries its own code in `series_id`. Before the fix the generator wrote 005930 on every row, the
    000660 rows included. The shared reader accepts either id of the file (question 5).
- **F20 `QX_DLA_postpatch.csv` (ruling 5).** Nothing declares its layout: the generator copies a result table byte for
  byte, and part 2 gated the file without reading it. The layout the G-REF-01 body reads is therefore this part's
  assumption (question 2 below):
  - a header with the columns `golden_id`, `sub_id` and `value`; other columns ride along;
  - one row per recorded value, keyed as `goldens.csv` keys it, no key twice;
  - `value` in the golden row's own unit: a decimal fraction where `goldens.csv` holds one, a count as a number, a
    verdict as its text.

  Rows of other goldens are not read. A G-POST-01 row of another milestone is not read either. A row under one of the
  four ids whose key `goldens.csv` does not hold is refused, and so are a blank key, a key recorded twice, a blank value
  and a value that is not a number where the golden is one. A UTF-8 byte-order mark before the header is ignored.

  This is not the layout the spec describes. L5815-5834 print F20 as the DL-A section 7 table, one row per item with
  a pre-patch and a post-patch column, and of the 64 values it holds only the G-KR-05 share. On such a file the body
  FAILs: "declared columns ['golden_id', 'sub_id', 'value'] absent". If the file instead holds every G-POST-01 row in
  the assumed layout, the body FAILs with "47 golden value(s) have no record". Both are in the demonstration. F20 is
  also a gate of the G-POST-01 data-row test in `tests/macro_m1_fixtures.py`, so listing F20 for that test turns
  G-REF-01 red until question 2 is answered.
- **`kr_regime_tags_expected.csv` (ruling 6).** Neither the spec nor ACQUISITION.csv names its columns. The layout the
  body reads is declared in `tests/macro_m1_calendars.py`:
  - a header of exactly `date` and one column for each of the 15 tags of `core.calendars.regime.TAGS`, in any order;
  - one row for every calendar date from 1995-01-01 to 2026-12-31 (11,688 rows), in date order, none missing and none
    repeated, the date written YYYY-MM-DD;
  - a cell states the tag's value on that date: `true` or `false` for a boolean tag, a plain decimal number for a
    numeric tag (compared as a number, so 0.30 is 0.3), the text itself for a text tag, and an empty cell where the
    signed file holds null;
  - the file is UTF-8. A byte-order mark before the header, which a spreadsheet's "CSV UTF-8" export writes, is
    ignored. CRLF line ends are read as LF.

### What ruling 1 changed beyond one place

The recommendation the owner approved said "`close`로 통일하고 `fixture_lines` 한 곳만 수정". Carrying it out changed more
than that one place. Each change follows from one layout for every reader, and the owner can object to any of them:

1. **The product reader is stricter, not only renamed.** `docs/vol_backtest.fixture_closes` used to skip a blank
   cell. It now raises `ValueError` for a blank, "." or non-positive close, a repeated or out-of-order date, a date not
   written YYYY-MM-DD and a one-row file.
2. **The generator refuses files it used to copy.** A reference file whose header lacks `close` (or `code` for F27)
   is refused, so the columns of a raw Yahoo file, `Date` and `Close`, have to be renamed before it is used. Since the
   review fix a reference row that a reader would refuse is refused too.
3. **F15 (SPY) and F01 are held to the same layout.** The same product reader reads F15 for G-B5-02, and the same
   test reader reads F01. No ruling names either file. The generator's row rules apply to both; neither is declared
   a reference series.

### Questions for the owner

Questions 1, 2 and 3 block ⑨-2 for the tests they name: the answer is needed before the file is built or listed.

1. **KRW=X has no calendar. Blocks G-POST-01 on real data, at both sites.** Ruling 2 names KRWX among the ids to be
   stamped from the market calendar, and it is the one id not stamped. `REFERENCE_FILES` names the market FX for F16,
   and neither the spec's market clocks (L1289-1291: KRX, NYSE, CRYPTO) nor `core.calendars` holds an FX clock, so
   there is no rule to choose from and the generator refuses F16 by name. Which signed calendar stamps a Yahoo KRW=X
   daily close? (a) The NYSE calendar: rows dated on NYSE holidays would then be refused as non-sessions, and 16:00 ET
   is before the FX day ends. (b) A new signed FX close rule in the calendar files. (c) Leave F16 out; G-POST-01 then
   stays NOT_RUN. Nothing is implemented until the answer.
2. **Where is the R-11 record, and in what layout? Blocks G-REF-01, and blocks listing F20 for any test.** The body
   assumes F20 records, in the keyed layout above, every one of the 64 values except the 16 the product record holds.
   The spec only says F20 holds the DL-A section 7 post-patch values (L5815), which include the G-KR-05 share. It
   does not say which archive file holds the G-REF-01 table (DL-A's long-history refusal legs) or the R4 and R4b
   values of G-KR-05 and G-KR-05s (section 11 names `R4_golden_values.csv` and `R4b_golden_values_net.csv`). The
   generator copies a result table unchanged, so the archived F20 cannot be expected to carry this part's column
   names. On an F20 shaped as the spec prints it the body FAILs whatever the record says, and F20 is also a gate of the
   G-POST-01 data-row test in `tests/macro_m1_fixtures.py`. Two ways out, both the owner's call:
   - a keyed transcription of the record under its own file name, with its own ACQUISITION row (a new row needs
     approval), and the gate pointed at it instead of F20;
   - or the body reads from F20 only the one row the spec gives it (G-POST-01 `gkr05_share`), and the owner names the
     archive files that hold the other 47 values.
3. **`price_limit` before April 1995. To settle before the expected-values file is built.** The spec asks for a full
   tag set equal to a file built from the notices "including `price_limit` before Apr-1995" (L2098). The signed
   `kr_regime_tags.yaml` holds null there (its `unverified` list: "a 17-step fixed-amount schedule, no single
   fraction"). As the body stands, an expected file that leaves those cells empty PASSes on the shipped signed file
   (run through the real test's gates on a scratch file), so the full-range clause can pass with a null tag. That
   reading of L2098 is this part's, not the owner's. If the expected file states a number instead, the 90 dates from
   1995-01-01 to 1995-03-31 FAIL (run with 0.046). Should a null tag be accepted there, or should the signed row carry
   a value in a new version and the body refuse a null?
4. **Whether ⑨-2 builds the reference files one at a time.** The spec has the fixtures "generated once, at M1's exit"
   (L22). Since the review fix the tool can write a chosen subset (`--only F13 F14 F27`), which is what makes rulings
   1 and 2 reachable from the command line; without `--only` it still writes the whole set or nothing. A whole-set
   run is refused today whatever is signed: on the shipped calendars 24 of the 40 data rows cannot be stamped by rule
   (17 ids that are neither registered nor declared, F16, and 6 as-posted ids with no scheduled publication instant;
   probed on one 2026 date). On the synthetic set 6 BLS and BEA ids are refused as well, because that set has no
   release calendar. Those rows need rulings of their own before the whole set can be generated.
5. **F27's `series_id`: please confirm.** Since the review fix a row carries its own code, so a 000660 row reads
   000660, not 005930. This follows rulings 1 and 2 as recorded (F27 carries `code`, `series_id` and `close`; 000660 is
   one of the five ids stamped from the market calendar), but the owner did not rule on it in these words. F27 has
   never been generated, so no md5 depends on it yet. If the file's first id on every row is wanted, say so before
   ⑨-2 builds F27.
6. Part 2's questions 5 to 18 are still open. Its questions 1 to 4 are answered by rulings 1, 2 and 4. Question 14 (the
   `owner_must_sign` contract) and question 15 (extending signed coverage) are restated in the signing request.

### Demonstrations on invented data

Each converted body is shown to PASS and to FAIL on invented in-memory rows. No KRX, Yahoo, FRED, QX or council data is
used. Each FAIL case asserts the message of the clause it targets.

- **Vendor prices (ruling 4).** At both G-POST-01 sites, a float32 artefact passes on the 2-Oct close
  (7003.740234375), on KRW=X's last row (1356.8399658203125) and on the peak (9114.5498046875), and so does 7,003.7449,
  which rounds to 7,003.74. These fail: a close of 7,003.75, and 7,003.7451, which rounds to it; a KRW=X last row of
  1,356.85; a peak of 9,114.56, which is inside the drawdown tolerance and fails the peak clause; a Samsung close of
  276,000.004 and an SK hynix close of 1,841,000.004, less than a cent off; and, at the point-in-time site, F01's
  official close carrying the artefact that F13 may carry. In T-PRINT-01 on F13, 5251.8701171875 passes and 5,251.88 and
  5,251.86 fail. `price_as_compared` is pinned directly, and it refuses F14.
- **G-REF-01 (ruling 5).** A record table holding the 64 golden values, one row each, passes with the shipped product
  record. It also passes without the 16 rows the product record holds, with rows of other goldens riding along (a
  G-POST-01 M1 row at a wrong value is not read), and with five values moved inside their tolerance. It fails:
  - for each of the 64 recorded values in turn, moved just outside its Level 1 tolerance (the tolerance plus 0.001; a
    count by one; a verdict changed);
  - for each of the 48 values only the table records, when its row is absent;
  - for a key that `goldens.csv` does not hold, and for a value that is not a number;
  - on an edited copy of the product record: each of its 12 numbers moved just outside tolerance (a count by one, the
    drawdown by 1.1 percentage points, the tail by 0.011), another verdict, a missing timing, a missing field, other
    golden ids, and no R-11 record;
  - at the layout: a missing column, a blank key, a key recorded twice, a blank value, a file with no row.

  The demonstration also parses the real test: it opens one fixture, `GREF01_RECORD`, and neither it nor its helpers
  name any of the stores, books, cost or refusal-leg tools the module builds for its other tests.

  Since the review fix it also shows the two failures on a spec-shaped F20 named under "Declared fixture layouts", and
  that a byte-order mark before the header changes nothing.
- **T-REGIME-01 full range (ruling 6).** Expected rows that state the synthetic signed set's own tags pass on that set:
  11,688 dates, 175,320 tag values, also with the columns in another order. It fails:
  - when one cell of any one tag is changed, each of the 15 tags in turn, on a different day for each;
  - on a boolean written `True` or `1`, a number written `15%` or with a space, a text in another letter case or left
    empty; 0.150 passes for 0.15;
  - when the signed file differs from the expected rows on one day (the `value_up` split signed a day late);
  - on a set that signs `price_limit` before April 1995 as null: an empty cell passes, 0.046 fails on its 90 dates, and
    the message lists the first five;
  - for each of the eight spec values, on a signed set that carries it wrong, also when the expected rows state the same
    wrong value;
  - on a stand-in for `regime_tags` that drops a tag;
  - at the layout: an absent, an extra and a repeated column, a row short of cells, a first row after 1995-01-01, a
    missing, a repeated and an out-of-order date, a last row before or after 2026-12-31, a date not written YYYY-MM-DD.

  The reason test pins the two computed reasons: REFDATA naming the file while it is not listed, and OWNER naming a
  refusal (the unsigned synthetic set) or a coverage gap (a set signed for 1996-2027 only).

  Since the review fix: a text cell with a space before or after it fails; a byte-order mark before the header is
  ignored and one inside the file is not; and the reason test reads the real test's source and asserts that it opens
  the one fixture, takes its calendar from `_regime01_signed()` with no argument and builds no calendar set itself.
- **Rulings 1 and 2** (first commit). On invented rows over the synthetic signed set the generator stamps F13, F14 and
  F27 at the scheduled close and the close-print bound, refuses F16, and refuses an id that is neither registered nor
  declared. `generate` writes the four files in the declared layout and the shared test reader accepts each; from F13
  the product reader reads the same dates and closes. `generate` refuses a reference header without a declared column
  (Yahoo's own `Close`; F27 without `code`). The product reader refuses the old `value` column, a blank, "." or
  negative close, a repeated or badly written date and a one-row file, and `fixture_lines` raises on a listed file in
  the old layout: it does not report NOT_RUN.
- **Generator row rules and runs (fix commit).** On invented rows over the synthetic signed set, through
  `generate(only=...)` with the real calendar function and the post-close check:
  - 18 reference files are refused with the file and line named, and for each the same rows stamped the old way are
    refused by the shared test reader: in F13 a blank, "null", ".", zero, negative, nan or inf close, a repeated date,
    newest-first dates and a header with no rows; a header-only F14; in F27 a code 005935, a code "5930", a repeated
    date and code pair, rows out of date order and a blank close; in F01 a "." close and a repeated date. A one-row F13
    is refused too; the test reader takes that file and the product reader does not. A one-row F15 and a blank F15
    close are refused, and a well-formed F15 is still refused when stamped ("SPY: not a registered series id").
  - A good F13, a one-row F14 and a good F27 are written. The shared test reader reads each back, and the product
    reader reads F13. Each F27 row carries its own code.
  - A whole invented set is refused at F02 and no output directory exists afterwards. A refused regeneration leaves
    an earlier generation of 50 files byte for byte as it was, although F01's reference had changed.
  - With `only=("F13", "F14", "F27")` a reference directory holding `CATALOG.md` and those three files is enough.
    The three fixtures are written in `REFERENCE_FILES` order and frozen. Without `only` the same directory is
    refused. An unknown id and an empty selection are refused. A selection that includes F16, or one retrieved one
    second before its bound plus 10 minutes, writes none of its files. The command line with `--only` writes the same
    three files and manifest rows; it refuses `--only F12`, and with a selected file absent it lists that file only.

### Ratchet

The rules are those of part 1; no rule changed. Converted, 15 sites, all on the floor: part 1's four, part 2's nine, and
this part's two (`macro_m1_calendars.py::test_regime01_full_range_expected_values_file`,
`macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata`). Remaining, 2 sites: T-FIX-01 and I-05. `LA02_SITES` (17) is
unchanged, the lists still partition it, and `LA02_FLOOR_SIZE` is 15.

## What stays NOT_RUN today, and why

- **T-REGIME-01 full range**: REFDATA. `kr_regime_tags_expected.csv` is not in `MANIFEST.csv`; it is an owner
  deliverable that does not exist yet. Its calendar gate passes today: the shipped `kr_regime_tags.yaml` is signed for
  1995-01-01..2027-12-31.
- **G-REF-01**: REFDATA. `QX_DLA_postpatch.csv` is not in `MANIFEST.csv`; its ACQUISITION source is the council archive
  outside the repository.
- **The 13 sites of parts 1 and 2**: unchanged. With ruling 4, a real Yahoo file that carries float artefacts no longer
  fails G-POST-01 or T-PRINT-01 for that reason once F13 and F16 are listed.
- **What the signed calendars still do not cover** is in the signing request. In short: `holidays_KRX` from 1997 (four
  tests wait on it), rows and four `owner_must_sign` entries of `kr_sessions` (T-CLOSE-02), `holidays_NYSE` and
  `holidays_CBOE` from 2015-12-04 (G-STALE-01), and `holidays_JPX` from 2024-10-28 (one T-CLOSE-02 clause).
  T-AVAIL-01 on the official calendars needs no fixture: it runs as soon as `holidays_KRX` covers 2015-01-01..2015-01-06
  and 2025-11-13.

## Follow-up needed before merge

`tests/fixtures/macro/MANIFEST.csv` lists `ACQUISITION.csv` with its md5, and `tests/fixtures/macro/README.md` says
that every edit of the register refreshes its manifest row. Adding the row ruling 6 approves changed the md5 of
`ACQUISITION.csv` from `05aee15bfb9d70ef58db7c1535fb5a2f` to `bfa8526ef8515de38af34fb41d06233a`. The task that produced
the second commit was not allowed to edit `MANIFEST.csv`, and neither was the fix commit, so the manifest row is still
stale. `tests/macro_m0_harness.py::test_manifest_lists_every_fixture_with_a_matching_md5` (T-HERM-01) FAILs with
"stale md5 ['ACQUISITION.csv: bfa8526e... != 05aee15b...']". It passed on the first commit; it failed on the second,
on the merge and on the fix commit, run by id each time. The fix is one cell: the md5 of the `ACQUISITION.csv` row of
`MANIFEST.csv`, set to the current `md5sum tests/fixtures/macro/ACQUISITION.csv`, with nothing else in the file
changed. It needs the owner's or the orchestrating session's say-so, and the branch must not merge before it. After
it, this section, the opening of this record, the verification list and the FACTS.md row "병합 전 후속" have to be
corrected and the compliance baseline refreshed.

## What did not change

- No product code changed in the second commit: nothing under `core/`, `data/`, `ui/` or `docs/*.py`. The first commit
  changed `docs/vol_backtest.py` and `docs/macro_fixtures.py` only, and the fix commit `docs/macro_fixtures.py` only;
  neither file is in `core/quant/gate_package.HARNESS_SOURCES` or in the source tuple of
  `tests/macro_m7_integration.py`. `core/quant/refusal.py` is read, not edited. The merge brought main's files in
  unchanged.
- No signature was written and no calendar file under `core/calendars/data` changed.
- `goldens.csv`, `MANIFEST.csv`, `tests/macro_registry.csv`, the `data/macro` registries and rules,
  `qa/acceptance_results.json`, ledgers, cards and registers are unchanged. `ACQUISITION.csv` gained exactly one row.
- Every existing test keeps its name and its `test_ids`, checked statically against `5f1ead5`, against the first
  commit and, for the fix commit, against the merge, for the seven test modules involved. The six new tests carry no
  `test_ids`, so the `implemented_in` column stays in sync. `tests/macro_m1_fixtures.py` stays CRLF; the other modules
  stay LF; `macro_m1_calendars.py` and `macro_m1_pit.py` stay ASCII. The `REFERENCE_FILES` table of
  `docs/macro_fixtures.py` stays on lines 44 to 75; comments in `macro_m1_pit.py` and `macro_m3_estimators.py` cite
  its rows by line.
- The new and changed tests read the data fixtures only through `require_fixture`, `goldens.csv` through
  `tests/golden_tools`, and the shipped calendar files only for their signing and coverage state. None reads
  `docs/asset_expansion/cache`.

## Verification (Linux, 2026-11-11 KST)

The lists below down to "/code-review fixes" are the runs of the first two commits, as they were reported then. The
runs on the merged tree and on the fix commit are under "/code-review fixes".

All runs used the scratch runner of parts 1 and 2. It installs `sys.addaudithook`, which refuses any open, listdir,
scandir or mkdir under `docs/asset_expansion/cache`, any `.env` and anything under `~/.nextgen`, and refuses every
`socket.connect`; it stubs `dotenv` and runs each test inside `tests.macro_acceptance.hermetic()`. Python 3.13.

- **By id, second commit.** 165 test functions: every test of `macro_m1_pit.py`, `macro_m1_calendars.py`,
  `macro_m1_fixtures.py`, `macro_m2_risk.py`, `macro_m3_estimators.py`, `macro_m1_integration.py` and
  `macro_m8_forward.py`, except the two that read the cache, plus
  `tests/macro_acceptance.py::test_t_herm_01_every_touchpoint_raises`. Result: 124 PASS, 41 NOT_RUN, 0 FAIL, no guard
  refusal.
  - Excluded, because they open files under `docs/asset_expansion/cache`:
    `macro_m1_pit.py::test_stale_01_schedule_aware_clauses_and_local_smoke` (`fred_DEXKOUS.csv`) and
    `macro_m3_estimators.py::test_g_b5_02_spy_refdata_with_smoke_on_local_cache` (`yf_SPY.csv`).
  - Against the first commit's run (133 ids: 98 PASS, 35 NOT_RUN): all 133 keep their status. One NOT_RUN reason
    changed, T-REGIME-01's, from the fixed OWNER text to "REFDATA: kr_regime_tags_expected.csv not in
    tests/fixtures/macro/MANIFEST.csv".
  - The 32 ids new to this run are this part's regime demonstration, the seven other tests of `macro_m1_integration.py`
    and the 24 tests of `macro_m8_forward.py`: 26 PASS, 6 NOT_RUN (G-REF-01, and five REFDATA or OWNER tests of
    `macro_m8_forward.py` that this part does not touch).
  - Both LA-02 ratchet tests, `test_every_required_fixture_is_generated_or_registered`,
    `test_no_golden_test_passes_on_its_fixture_gate_alone` and `test_acquisition_csv_integrity` PASS.
  - Outside that list, `macro_m0_harness.py::test_manifest_lists_every_fixture_with_a_matching_md5` was run on its own:
    PASS before the ACQUISITION row, FAIL after it (see "Follow-up needed before merge").
- **Mutation probe, second commit.** 49 mutants, each compiled in memory from a test module's source into a fresh
  module object; the worktree files were never written. 48 are caught by a demonstration, and the unmutated
  demonstrations pass before and after. They include: vendor prices exact again, at one decimal, at three decimals;
  every price rounded; a won price or F01's close treated as a vendor price; KRW=X treated as an official price; the
  peak exact or not compared; the recorded values or the product record not compared; a golden row with no record
  accepted; every G-POST-01 row asserted; the product drawdown read as a fraction; tolerances doubled; an unknown key
  or a non-number skipped; a boolean read case-insensitively; a number compared as text; a null passing on any cell; a
  tag not compared; the spec values not asserted; dates not consecutive; the gate ignoring coverage or a refusal. The
  survivor drops the assertion that the price rows with a rule are exactly the `goldens.csv` price rows. It is
  equivalent while the two lists agree, and the demonstration pins the list.

  Two more mutants survived a first run, and the demonstrations were tightened until they were caught: doubled
  tolerances (the value cases now sit just outside Level 1) and a text tag compared ignoring case.
- **End to end.** The two converted real test functions ran past their fixture gates, the gate pointed at invented
  files in a scratch directory (a scratch manifest; module globals rebound in the probe process only).
  - T-REGIME-01 on the shipped signed `kr_regime_tags.yaml`: PASS on rows stating the shipped tags (175,320 values on
    11,688 dates); FAIL on one changed cell; FAIL with 90 differing values when `price_limit` before April 1995 is
    0.046; NOT_RUN (REFDATA) when the file is not listed.
  - G-REF-01 on the shipped product record: PASS on a table holding the 64 golden values; FAIL on `value_onsets`
    recorded as 75; FAIL listing 47 values with no record on a table holding the G-POST-01 share row only; NOT_RUN
    (REFDATA) when the file is not listed.
- **Calendar gates on the shipped set.** Each gate the signing request cites was run on `CalendarSet()` and its output
  pasted there: 23 waiting lines for T-CLOSE-02, 3 for G-STALE-01, 2 for T-AVAIL-01, one for T-SAT-01, none for T-VT-01,
  T-LABEL-01, T-PRINT-01, G-POST-01 and T-REGIME-01.
- **Static.** `ruff check --select F,E9` on the four test files of the second commit reports the same two unused
  imports as before it and nothing new.
- **First commit** (reported by its own run, not repeated here except through the 165 ids): 133 ids, 98 PASS, 35
  NOT_RUN, 0 FAIL; the 131 ids that exist at `5f1ead5` keep their status and NOT_RUN reason. On `5f1ead5` a probe showed
  the `KeyError` for the five ids and the `IndexError` of the product reader. 27 in-memory mutants of the two product
  files were all caught. For registered series, old against new `calendar_available_at` over 108 ids, 8 dates and 8
  statuses gave 6,592 identical calls of 6,912; the other 320 are the five declared ids. `generate` wrote the same 50
  files byte for byte on one reference set.

### /code-review fixes (merge `7611064` and the fix commit)

A code review of the first two commits reported 19 findings from two reviewers, 14 distinct. A probe reproduced every
code finding on the merged tree before any change. What was done, by defect:

1. **The stale manifest row (blocker, both reviewers). Confirmed, not fixed.** The fix stage was not allowed to edit
   `MANIFEST.csv` either. See "Follow-up needed before merge".
2. **The branch was behind main (major, both).** Main `1a8b29f` is merged in by `7611064`. The only files both sides
   change are `docs/compliance/FACTS.md` and `docs/compliance/source-review.json`. Main's FACTS text is kept
   unchanged and this part's section follows it; the baseline was regenerated with the refresh command, not merged by
   hand. On the merged tree the 165 ids keep their status and NOT_RUN reason.
3. **The cited rulings section was not in the tree (minor, both).** It arrived with the merge: PR #100, which carries
   `275ec93`, had reached main.
4. **G-REF-01 would FAIL on a spec-shaped F20 (major, both). Left for the owner; stated plainly.** The body is
   unchanged. Question 2 now says it blocks listing F20, the layout declaration says what the spec describes, and
   the demonstration shows both failures.
5. **Ruling 2 covers four of five ids (major). Left for the owner; stated plainly.** No calendar is chosen for KRW=X.
   The opening, the table and question 1 no longer say that all five are stamped.
6. **The command line could not write F13, F14 or F27, and a refused run left a stray file (major). Fixed.**
   `generate(only=...)` and `--only`; every file is built and checked in a temporary directory first.
7. **The generator wrote close files the readers refuse (minor). Fixed.** `fixture_rows` applies the readers' rules
   to F01, F13, F14, F15, F16 and F27. F01 and F15 are added to the declaration (`CLOSE_FILES`), not left out.
8. **F27's 000660 rows carried `series_id` 005930 (minor, both). Changed, pending the owner's confirmation.** A row
   carries its own code; the two assertions that pinned the old label now pin the new one. Question 5 asks the
   owner to confirm.
9. **Two mutants survived the demonstrations (minor). Fixed.** The reason test checks the real T-REGIME-01 test's
   source for both gates, and the demonstration has a text cell with a space on either side.
10. **A null tag passes the full-range clause (minor). Left for the owner.** The signed calendar file cannot be
    edited here, and refusing a null would make the clause unpassable until the owner signs a value. Question 3 now
    says the reading is not owner-approved.
11. **A byte-order mark broke the two hand-built files' readers (minor). Fixed.** Both readers ignore one before
    the header. The close-layout readers are not changed: they do not read the first column.
12. **Ruling 1 changed more than one place (minor). Stated.** See "What ruling 1 changed beyond one place".
13. **The signing request asked for a `saturday_close` row per Saturday (minor). Reworded.** One effective-dated row
    is enough if the close time never changed.
14. **Part 2's text is out of date (minor). Noted there.** A note at the top of the part 2 record and one in its
    FACTS.md row point here. The old text is not rewritten.

Verification of the merge and the fix commit:

- **By id, fix commit.** 167 test functions: the 165 of the second commit's list and the two new tests. Result: 126
  PASS, 41 NOT_RUN, 0 FAIL, no guard refusal. The 165 keep the status and the NOT_RUN reason they had on `8ed8112` and
  on the merge. Run on its own, `macro_m0_harness.py::test_manifest_lists_every_fixture_with_a_matching_md5` FAILs as
  stated above. Both ratchet tests, `test_every_required_fixture_is_generated_or_registered`,
  `test_no_golden_test_passes_on_its_fixture_gate_alone`, `test_acquisition_csv_integrity` and
  `macro_acceptance.py::test_t_herm_01_every_touchpoint_raises` PASS.
- **Before and after.** One probe script ran on the merged tree before the fixes and again after them. Before: the
  stray F01 file, no `only`, each of the bad F13 and F27 references written, 000660 rows labelled 005930, both
  byte-order-mark failures, and both demonstrations passing on the two surviving mutants. After: each is refused,
  written correctly or caught. The KRWX refusal, the two failures on a spec-shaped F20 and the PASS with a null tag
  are the same before and after, as intended.
- **Mutants on disk.** 76 mutants, each applied to a scratch copy of the tree (never the worktree) and run against 20
  demonstrations: the reviewer's 47, one of them re-targeted at a line this commit rewrote, and 29 of the new code.
  All 76 are caught. A first run caught 75. The survivor made the command line ignore the calendars it is given; the
  test could not tell, because the shipped calendars stamp the same 2026 instants. The test now counts the use of the
  calendars it passes, and the full run was repeated. The reviewer's two survivors are caught now.
- **Compliance.** `python -m tools.compliance.check --check`: consistency PASS, publication BLOCKED, 20 documents,
  662 source files, after the refresh of the merge and again after the refresh of the fix commit.
- **Static.** `ruff check --select F,E9` on the four files the fix commit changes under `tests/` and `docs/*.py`: one
  unused import in `tests/macro_m1_fixtures.py`, the same as on the merge, and nothing new.

### Not run, and unverified

- `tests/run_all.py`, whole macro modules, `tests.macro_m9_lab` and `tests.macro_m8_pipeline` were not run.
  `tests/macro_m0_harness.py::test_registry_implemented_in_matches_test_ids` was not run, because it imports every macro
  module; that it still passes rests on the static `test_ids` comparison. The two cache-reading tests were not run.
- Windows behaviour is unverified, and no CI runs the macro suites.
- No real fixture exists here, so no converted body has run on real data. These are unverified:
  - whether the owner's Yahoo and KRX reference files carry `close` (and `code` for F27); raw Yahoo CSVs use `Date` and
    `Close`, which the generator now refuses;
  - whether the real Yahoo files carry float artefacts, and whether two decimals reproduce 7,003.74, 9,114.55,
    5,251.87 and 1,356.84 on them;
  - what the real `QX_DLA_postpatch.csv` holds and how its columns are named (question 2);
  - what the owner's expected-values file will state, the pre-April-1995 `price_limit` in particular (question 3).
- That the product record's drawdown field is the ETF 3 bp column is read from the spec's two tables. At the Level 1
  drawdown tolerance (±1 percentage point) the test cannot tell the two columns apart: a mutant that compared it with
  the stock 35 bp column changed no comparison and was caught only because the count of unrecorded values changed.
- The stamping of rulings 1 and 2 was checked on the synthetic signed calendars with invented rows. The coverage the
  generator needs (the KR files from 1 January of each row's year, so from 1996-01-01 for F13; `holidays_NYSE` from 1990
  for F14) was probed on the shipped set and on a cut synthetic set for single dates, not on real files.
- `docs/vol_backtest.run()` and its CLI were not executed (they read `docs/asset_expansion/cache`).
  `docs/macro_fixtures.main()` has run end to end only in the new test, on invented rows and the synthetic signed
  calendars; it has never run on the shipped calendars or on real reference files.
- Two things seen in `docs/macro_fixtures.py` and not changed, because no finding names them. A result table is read
  with `read_text`, which turns CRLF line ends into LF, so "copied byte for byte" holds for an LF table only. A
  reference date that is not ISO raises a plain `ValueError` without the file name.
- The generator's row rules were written from the two readers' code and are checked against the shared test reader
  case by case, and against the product reader for the one-row file. That the three stay in step later rests on the
  new test.
- The real G-REF-01 and T-REGIME-01 bodies' gate wiring is checked by the end-to-end probe and, for G-REF-01, by parsing
  the source. A mutant of the gate lines themselves cannot be judged by the in-memory harness, because the parse reads
  the file on disk.
- Statements in the part 2 record that this part makes out of date are left as written there: its questions 1 to 4, its
  last "unverified" bullet (the generator's `KeyError`), its "Next parts" list and its counts. Since the fix commit a
  note at the top of that record, and one in its FACTS.md row, say so and point here.

## What is left

Still unconverted, as listed in `LA02_REMAINING`:

- **T-FIX-01** (`tests/macro_m1_pit.py::test_fix_01_regeneration_at_level_1_tolerance_refdata`). Held by the owner
  (ruling 6): the size and the terms of use of the council archive outside the repository are to be checked first.
- **I-05** (`tests/macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata`). It needs the
  LA-07 harness change and the LA-30 ALFRED vintages. By ruling 12 the LA-30 data is acquired with the reference-data
  stage ⑨-2.

Before this branch can merge: the one-cell manifest follow-up above.

Before ⑨-2 can run the converted bodies on real data: the owner's answers to questions 1 to 3, each before the file
it names is built or listed (F16; F20; the expected-values file); the answers to questions 4 and 5 before the
generator is run; the signatures listed in the signing request; and the reference files themselves.
