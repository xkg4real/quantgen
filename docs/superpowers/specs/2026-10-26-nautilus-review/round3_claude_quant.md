# Round 3 referee report: quantitative methodology

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 3 (working tree; "spec:N" below is a
line of that file).
Referee: Claude, quantitative-methodology lens (parity bars, selection-matched walk-forward, trial counting, cost
checks, decision agreement, the pilot-2 reference, claim labels, expected verdicts).
Repo: QUANTGEN at HEAD `7112351` (code unchanged since `6f7c610`). Engine: `nautilus_trader` 1.231.0 in
`scratch:ntvenv`. `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probes, all in `scratch:referee3_quant/`, on synthetic data only:
- `nyears_probe.py` (global interpreter) runs `walk_forward` and `year_stats` on a synthetic calendar built from the
  stored card's own `start`, `end` and `sessions`. No price file is read.
- `f1r_n6_probe.py` checks F1 and F1r through `simulate` and the 5.3.3 rebuild, and the N6 and L2-7 series facts.
- `cents_probe.py` (venv) compares P7's `cents()` with `Money` on 80,006 synthetic values.
- I also ran `scratch:rev3_probe/agree_probe.py`, the moderator's N8 probe.

## Verdict

**ACCEPT_WITH_CHANGES.**

Revision 3 applies every round-2 ruling from my lens. I re-derived the new hand values and they hold:
- F1r: QUANTGEN's `pnl` and the rebuilt `R` both match 8.2.
- N6: start 79.53, end 556.04, maximum 677.47, and md5 `adb735b9...` all reproduce.
- N8: cases (a) to (d) give the outcomes 8.2 states.
- P7's `cents()` rule matches `Money` exactly.
- The predicate list of 5.5 step 5 is exactly what `_decide_strategy` reads.

One major defect stops me from saying AGREE. It came from my own round-2 proposal:
- **QUANT-R3-1 (major).** G-08 requires `sc_qg.n_years` to equal the stored card's `n_years` exactly.
  - The stored card was written under an older gate rule that counted calendar years touched. Today's gate counts whole
    years.
  - On pilot 2's out-of-sample span, today's code gives 9 and the card holds 11.
  - So G-08 withholds every correct pilot-2 run of record with "reference drift", after the 5 C3 rows are permanent.
    Nothing before Step 9 can show it.

The fix is one field in G-08. Steps 2 to 6 do not touch G-08 and can start today. The fix is needed before Step 7
builds G-08, and before the owner signs the revision at Step 7A. Two minor issues follow.

## Sections reviewed

- Status, Owner context, sections 1 and 2 (O5, O6, O11, O14).
- 3.5, 3.6 and 3.9.
- 4.2.
- 5.2.3 to 5.2.5 (fees, bars, sizing, the ports), against `core/quant/strategies.py:69-90, 162-187, 330-348,
  379-398`.
- 5.3.2 (all steps), against `docs/asset_expansion_study.py:67-104, 138-153, 172-200, 271-279, 329-343, 724-732`.
- 5.3.3 and 5.3.4.
- 5.4.1 to 5.4.3 (P0 to P13, `cents`, `select_matched`, the evidence for the bars), against
  `core/quant/validate.py:137-215, 268-270, 332-381`.
- 5.5 (all steps, including `gate_predicates`, `agree` and G-08), against `core/quant/validate.py:421-437, 492-622`
  and the stored card `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json`.
- 6.1, 6.3 to 6.6.
- Section 7: R-05, R-06, R-13, and G-01 to G-08.
- 8.1 (the stub child), 8.2 (F1, F1r, F2, N2, N4, N6, N7, N8, the synthetic series), 8.3 tests 1, 2, 7, 10, 20,
  21, 29 and 30, and 8.4 tests 7 and 11.
- Section 9: Steps 6 to 9.
- 10.1 to 10.4.
- 11 (risks 9 to 11, 15 and 16).
- Appendix B (the QUANT rows and the round-2 interpretations).

## Earlier issues

- QUANT-1: resolved. P0a (spec:676) and P0b (spec:750) tie the inputs to the study's loaders.
- QUANT-2: resolved. Both matrices are scored, and a card needs an equal decision and equal predicate dicts
  (spec:817; G-02 at spec:1158).
- QUANT-3: resolved. `select_matched` (spec:777-784) mirrors `walk_forward`'s slicing (`core/quant/validate.py:369-379`).
  P11 is a diagnostic.
- QUANT-4: resolved. `n_trials = family_n_raw + U`, with four counts stored (spec:816).
- QUANT-5: resolved. P7 is hard, and its expectation comes from the table and the runner's own loop (spec:757).
- QUANT-6: resolved. `claim_label` appears on the tables and the cards (spec:1043-1044, 1062, 1450, 1463).
- QUANT-7: resolved. Pilot 1 lists INSUFFICIENT_DATA first, and pilot 2's bench-p noise claim is gone (spec:1471-1487).
- QUANT-8: resolved. Moot under ruling C-1.
- QUANT-9: resolved. The P10 bound (spec:760) holds for F1 and F1r: the largest gap is 1.7416e-4, at t = 3, against
  a bound of 3.28e-4.
- QUANT-10: resolved. N6 has a stepped cash rate, and its stated facts reproduce (spec:1244, 1251-1265).
- QUANT-11: resolved. `rules.engine` says that walk-forward switches are executed in neither engine (spec:1044).
- QUANT-R2-1: resolved. Step 6 reads DGS3MO as `study.fred` does and drops NaN before the fill (spec:675). R-06
  (spec:1130) and L1-7 (spec:1277) match.
- QUANT-R2-2: resolved. The predicate list equals what `_decide_strategy` reads (`core/quant/validate.py:544-545, 557,
  576-577, 584-591`; `min_track_record` at `:156`). N8 reproduces.
- QUANT-R2-3: resolved. P7 is anchored to the table and the runner's loop. `cents()` matches `Money` on 80,006 values,
  ties included, in high precision.
- QUANT-R2-4: resolved. Both labels start with a house term (spec:1450, 1463), and L1-30 checks it (spec:1300).
- QUANT-R2-5: (a) resolved: L1-29 checks embargo, cost, grid, domain and benchmark (spec:1299). (b) **open**: G-08 is
  applied as ruled, but its exact `n_years` comparison cannot pass on pilot 2 (QUANT-R3-1).
- QUANT-R2-6: resolved. F1r (spec:1210-1213) reproduces through `simulate` and the 5.3.3 rebuild. N6 and L2-7 carry
  `synth_rf`.
- QUANT-R2-7: resolved. `closes = np.round(raw, 9)` is the one rounding, and the round trip is asserted (spec:382-383,
  674; R-05 at spec:1129).

## New issues

### QUANT-R3-1. G-08 compares `n_years` exactly against a card written under the old year rule

- **Severity:** major.
  - It is fail-closed, so no wrong verdict results.
  - But it withholds every correct pilot-2 run of record, after 5 permanent rows are in C3. Nothing before Step 9
    shows it.
  - A fix after the fact changes code, so it needs a new `owner_confirmed` and a re-run under R-17.
  - This is the class of QUANT-R2-1, which was ruled major.
- **Section:** 5.5 step 5 (spec:817), G-08 (spec:1164), 8.3 test 29 (spec:1299), 10.3 pilot 2 (spec:1481-1487),
  Appendix B's QUANT-R2-5 interpretation (spec:1644-1646).
- **Problem.**
  - G-08 requires `sc_qg` to reproduce the stored card's `chosen_last`, `n_trades`, `n_sessions` and `n_years`
    exactly.
  - The stored card was written on 2026-09-27, before the gate changed how it counts years:
    - today's `year_stats` returns `n_years = full_years(min(dates), max(dates))`, the whole years spanned
      (`core/quant/validate.py:421-437`);
    - the docstring records the change: "n_years used to count calendar years touched";
    - `tests/expansion_acceptance.py:310-316` pins the new rule.
  - On pilot 2's out-of-sample span, today's code gives 9 whole years. The card holds 11, the calendar years touched.
    So G-08 fails on a correct bridge, and the run is withheld as "reference drift".
  - L1-29 tests G-08 on hand-built scores only, and no rehearsal touches BTC (3.9). So nothing shows the mismatch
    before the of-record run.
  - The defect is in my own round-2 proposal (QUANT-R2-5(b)), which listed `n_years` among the exact fields.
- **Evidence.**
  - The stored card, `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json`:
    - statistics: `n_years` 11 (`:78`), `n_sessions` 3634 (`:76`), "29 origins" (`:108`);
    - data: 4,392 sessions from 2014-09-17 to 2026-09-25 (`:34-36`); `created` 2026-09-27 (`:140`).
  - The wording also shows the card's age:
    - its first line reads "over 3,634 sessions (11 years)" (`:124`);
    - today's gate writes "({s.n_years} full years)" (`core/quant/validate.py:540`);
    - the first line of every stored strategy card in `docs/asset_expansion/cards/` reads "(N years)", so all of
      them predate the change.
  - `nyears_probe.py`, on a complete daily calendar with the card's start, end and session count, and with
    `walk_forward(..., embargo=1)`:
    - 29 origins and 3,634 OOS sessions, both equal to the card;
    - OOS from 2016-10-14 to 2026-09-25;
    - `year_stats(...)["n_years"]` is **9**; calendar years touched are **11**.
    - The result does not depend on missing days: 2016-10 to 2026-09 is under 10 years either way.
  - No other compared field shows this kind of drift.
    - `years_positive` still groups by calendar year (`core/quant/validate.py:432-435`), consistent with the card's
      9/11 = 0.818.
    - Apart from "full", the card's line texts match today's `_decide_strategy` format (`:539-571`).
    - Any other drift is UNVERIFIED: checking it needs BTC prices, which may be read only after registration.
- **Effect on the expected verdict:** none. The decision tree reads 9 against `oos_years_min` 5
  (`core/quant/validate.py:586`), so 10.3's expected PASS stands. The bridge card will show `n_years` 9 where the
  stored card shows 11.
- **Proposed fix.**
  - In 5.5 step 5 and G-08, replace the exact `n_years` comparison with `len({d[:4] for d in wf_qg.dates})`, the rule
    that wrote the card, compared with the card's `n_years`. Record `sc_qg.n_years` beside it, labelled as the
    current whole-year rule.
  - Alternatively, drop `n_years` from G-08: `n_sessions`, `chosen_last` and the OOS date span already fix the sample.
  - State that G-08 never compares `lines`, `reason` or `revise_target` text, whose wording also changed.
  - L1-29 gains two cases. In both, the OOS dates run from 2016-10-14 to 2026-09-25 and the stored-card dict holds
    `n_years` 11, while `sc_qg.n_years` is 9.
    - Everything else equal: G-08 passes.
    - `n_sessions` off by one: G-08 fails.
  - In 10.3 pilot 2, add: "the card reports 9 whole years where the stored card reports 11 calendar years; the gate's
    five-year rule passes either way."
  - Correct the round-2 interpretation in Appendix B.

### QUANT-R3-2. The runner's crypto path first runs at pilot 2 of record, and a null cash rate is undefined

- **Severity:** minor. It is fail-closed (G-06 ERROR or a WITHHELD), but it can cost the pilot-2 run of record.
- **Section:** 5.3.2 steps 6 and 13 (spec:675, 682), 5.3.3 (spec:698), 6.6 `rf_file` (spec:1059), 10.2 (spec:1461),
  8.4 tests 7 and 11 (spec:1313, 1315), Step 7 done-when (spec:1368).
- **Problem.**
  - Step 6 defines the cash rate for pilot 1 only. Step 13 calls `simulate(..., cash_daily=rf)`, and 5.3.3 adds
    `(cash(t)/E-(t)) rf(t)`.
  - For pilot 2, 6.6 has `rf_file` null and 10.2 says "Cash rate: none". If `rf` becomes `None`, `simulate` raises a
    `TypeError`: `np.ndim(None)` is 0, so `cash = None`, and then `cash_w * cash` fails
    (`core/quant/strategies.py:85-86`). The study passes the default `cash_daily=0.0`
    (`docs/asset_expansion_study.py:175, 336-343`).
  - More broadly, every end-to-end rehearsal is a `trend_switch` table with a cash rate (L2-7, and L2-11 = N6). F2
    runs the crypto port in the child only. N8 and L1-29 use hand-built scores.
  - So the runner's crypto path first runs at pilot 2 of record. That path covers a null `rf`, `embargo=1`, `domain`,
    a 7-day calendar with bars at 00:00 UTC, 8-decimal quantities in the 5.3.3 rebuild, and G-08's card load and
    `chosen_last`.
- **Evidence.**
  - Probe: `simulate(P, W, cost_bps=10.0, cash_daily=None)` raises `TypeError: unsupported operand type(s) for *:
    'float' and 'NoneType'`, while `cash_daily=0.0` runs.
  - 8.4 lists no crypto rehearsal (spec:1310-1315).
- **Proposed fix.**
  - In step 6, add: "`rf_file` null: `rf = 0.0`, the study's default (`docs/asset_expansion_study.py:175`); the
    overlay term of 5.3.3 is zero; R-06 does not apply."
  - Add L2-12, a synthetic crypto rehearsal through the runner:
    - `synth_prices(5, 1600, 400.0, 60000.0)` on `pd.date_range(..., freq="D")`, with bars at 00:00 UTC the next day;
    - the pilot-2 grid, embargo 1, `domain`, 10 bp, `rf_file` null and a temp ledger;
    - expected outcome: a card, or a WITHHELD record that names its reason, with both scores in the run record.
  - Run G-08's comparison function inside L2-12, against a reference dict that the test builds from
    `validate.score_strategy` on QUANTGEN's matrix.
  - Add L2-12 to Step 7's done-when.

### QUANT-R3-3. G-08's reference is not pinned, and its exact path depends on an unrecorded build

- **Severity:** minor.
- **Section:** 5.5 step 5 (spec:817), G-08 (spec:1164), 6.6 (spec:1062-1069), Appendix B (spec:1644-1646).
- **Problem.**
  - **The exact path needs the card's build.** When `rounding_changed` is false, G-08 compares floats bit for bit with
    values written on 2026-09-27. Nothing records the numpy, scipy or CPU that produced them:
    - `docs/asset_expansion/study.log` holds an earlier run, which lists this card as REVISE;
    - `docs/asset_expansion/manifest.json` holds no versions.
    - Bit equality across numeric builds is UNVERIFIED.
  - **Exactness buys nothing.** A 1e-9 tolerance is ten million times tighter than P3's 0.01.
  - **The target can move.** The card's bytes are not pinned:
    - T-HERM-02 compares the 34 cards before and after its own module only (`tests/macro_m7_cards.py:830-835`);
    - `code_sha256` covers only `tools/nautilus/` and `requirements-nautilus.txt` (spec:1066-1068).
    - So a committed edit to the card would move G-08's target silently.
- **Proposed fix.**
  - Keep exact comparison for the integer and dict fields only. Compare floats always within 1e-9, and `bench_p`
    within one bootstrap draw (1/2000).
  - Add `reference_card` and `reference_card_md5` to the pilot-2 table. Today the md5 is
    `d0bb0882fb51dec361cf2ddb160186bb`. Step 1 refuses a mismatch (R-11), and L1-29 checks the value.

## Why I agree or not

I do not agree yet, for one reason: G-08 as written cannot pass a correct pilot-2 run (QUANT-R3-1).

Everything else in my lens is ready to build:
- Both engines use QUANTGEN's selection, so engine noise never picks the card's out-of-sample columns.
- Both matrices are scored, and a card needs the same decision and the same gate predicates. The predicates are
  exactly those the gate's decision tree reads.
- P7 checks every commission against the table and the leg's nominal stress, with `Money`'s own rounding.
- The trial count is the size of the union.
- P0 ties the arrays to the study's loaders, and L1-29 ties the protocol arguments to them.
- The claim labels are honest.
- The hand values I could re-derive all reproduce.

Steps 2 to 6 can start today. Two conditions apply to the fix of QUANT-R3-1, a one-field change:
- It must be in the revision before Step 7 builds G-08.
- It must be in the revision the owner signs at Step 7A.

QUANT-R3-2 and QUANT-R3-3 are cheap and fail-closed. I would take them in the same edit.

## Notes

Checked and sound in Revision 3:
- **The agreement predicates.** Each one in 5.5 step 5 maps to a line of `_decide_strategy`:
  - `pbo_meaningful` and `flat`: `:544-545`;
  - `has_bench`: `:557`;
  - `pbo_ok` and `pbo_reject`: `:576-577`;
  - the INSUFFICIENT_DATA conditions: `:586`;
  - `mtr`: `:584`.
  - `agree_probe.py` gives (a) a card, (b) and (c) "decision mismatch", and (d) "benchmark test dropped", as 8.2
    states.
- **Pilot 2's margins** on the stored values sit far from every bar the gate reads:
  - `ci90[0]` is 0.72;
  - `oos_is` is 0.895 against 0.5;
  - `years_positive` is 0.818 against 0.6;
  - `sr_stress` is 1.16;
  - `plateau` is 1.0, with no edge;
  - `n_trades` is 144 against 100;
  - the minimum track record is about 484 sessions against 3,634.
  - `bench_p` sits 60 draws below 0.10.
  - So an equal-predicate WITHHELD on engine noise is unlikely there.
- **`cents()`.** Over 80,006 synthetic fee products and exact half-cent ties, `Decimal(cents(v)) / 100` equals
  `Money(v, USD).as_decimal()` in high precision. This matches `nt:model/objects.pyx:1190, 1205`. Standard precision
  is UNVERIFIED until Step 7A.
- **F1r.** QUANTGEN's `pnl` at t = 0, 1, 2 and 6 is +0.0001, and at t = 5 it is -0.0049000. The rebuilt `R` at
  t = 5 is -0.0049005, and at t = 10 it is -0.0102035. The largest gap is 1.7416e-4, at t = 3. All match 8.2.
- **N6 and L2-7.**
  - The md5 values `adb735b9c3b6f1bab8e1728c38fff608` and `7b53fe601255972348aa60eccad550b7` reproduce on Linux.
  - Every N6 close passes the 9-decimal round trip.
  - Every planted bar, 252k, is a decision bar of all 12 pilot-1 columns.
  - L2-7 has about 2.9 OOS years, so it will card INSUFFICIENT_DATA. That is in `DECISIONS`, as its done-when allows.

Minor concerns, not raised as issues:
- **Carried from my round-2 notes.**
  - P1's exemption is still moot, because an exempt mismatch changes the fill days and P4, which has no exemption,
    withholds (spec:751, 754).
  - The preamble of 5.5 ("Only when every hard check of 5.4.1 passes", spec:811) comes before step 1, which builds the
    `wf_nt` that P12 needs. 4.2 row 16 has the right order.
  - U counts `study_configs` entries rather than distinct absent `config_id`s (spec:816). There are no duplicates
    today.
  - P11 never withholds. That is a design choice.
- **Predicates the decision path never reads.** Equal predicate dicts also compare predicates that the decision path
  never read.
  - For example, under pilot 1's expected INSUFFICIENT_DATA, the gate returns at `core/quant/validate.py:586` and
    never reaches the REJECT branch, so `dsr_ok` and `bench_ok` go unread.
  - Engine noise near one of those bars would withhold "decision mismatch" although the decisions agree.
  - It is fail-closed and rare, and it guarantees equal `revise_target` and `lines`, so I accept it.
- **Wording.**
  - 5.4.1 says `c_leg` is used in P6, but P6's formula does not use it.
  - P7's `commission == cents(expected) / 100` should be stated in Decimal, as
    `Decimal(commission) * 100 == cents(expected)`, so that no reader divides an int into a float.
  - The crypto port's `mean(P[i-n+1 : i+1])` names no summation. The trend port names a left-to-right loop, and the
    crypto port should say the same. At BTC prices a vote can differ from QUANTGEN's cumulative-sum SMA only when
    `|P - MA| / P` is below about 1e-13. That is within P1's exemption, but P4 would still withhold.

Data touched in this round, for 10.4:
- the stored cards' JSON (statistics and line text);
- `docs/asset_expansion/study.log`, `manifest.json` and `results.md` (line 16);
- synthetic calendars and series.

I read no SPY price, no BTC price and no ledger row. QUANTGEN was imported read-only.

UNVERIFIED:
- Whether any G-08 field other than `n_years` drifted between the code that wrote the card and today's code. Checking
  it needs BTC prices, which may be read only after registration.
- Bit equality of today's numerics with the card's build.
- Standard-precision `Money` rounding on Windows.
