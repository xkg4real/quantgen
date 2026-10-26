# Round 4 referee report: quantitative methodology

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 4 (working tree; "spec:N" below is a
line of that file).
Referee: Claude, quantitative-methodology lens (parity bars, selection-matched walk-forward, trial counting, cost
checks, decision agreement, the pilot-2 reference, claim labels, expected verdicts).
Repo: QUANTGEN at HEAD `4f5f18b` (code unchanged since `6f7c610`). Engine: `nautilus_trader` 1.231.0 in
`scratch:ntvenv`. `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probes, all in `scratch:referee4_quant/`, run in the global interpreter (numpy 2.3.5, pandas 2.3.3, scipy 1.18.0) with
QUANTGEN imported read-only. None reads SPY or BTC prices, and none writes a ledger row or a repository file
(`git status` was unchanged after each one):
- `rescore_krx_probe.py` re-scores the stored card `S_E1_trend_krx` with today's gate. It reads a scratch copy of the
  four KRX ETF caches and `fred_DGS3MO.csv`, with `yfinance` and `pandas_datareader` replaced by modules that raise.
  It then applies G-08's comparison rules to the result. Output: `rescore_krx_probe.out`.
- `rescore_krx_rounded_probe.py` does the same after `np.round(prices, 9)`, the bridge's one rounding. Output:
  `rescore_krx_rounded_probe.out`.
- `l2_12_probe.py` builds the L2-12 synthetic crypto series and walk-forward of 8.2 and 8.4 test 12. Output:
  `l2_12_probe.out`.

## Verdict

**AGREE.**

Revision 4 resolves all three of my round-3 issues as ruled. G-08 now:
- compares the stored card's `n_years` with the calendar-year count that wrote it;
- compares floats within 1e-9 and `bench_p` within one bootstrap draw;
- pins the reference card by md5 before registration.

A new probe also closes the part of G-08's premise that round 3 left UNVERIFIED. Today's gate reproduces the stored
card `S_E1_trend_krx`, written on the same day as the pilot-2 reference:
- on the raw closes, G-08's drift list is empty, and every G-08 float is bit-equal;
- on 9-decimal closes (2,329 of 10,648 closes changed), the list is still empty, and the largest float gap is 7.4e-14.

I found no new blocker or major. Three minor issues remain, all fail-closed and cheap:
- **QUANT-R4-1.** L2-12's last assertion contradicts 5.5 step 5's year rule. On the L2-12 series, a correct bridge
  reports drift in `n_years`.
- **QUANT-R4-2.** `reference_drift(sc_qg, wf_qg, ref)` has no grid, so it cannot form `chosen_last`. And the spec
  never says what switches G-08 on.
- **QUANT-R4-3.** Wording.

## Sections reviewed

The whole of Revision 4 (1,772 lines), read in full. I checked these sections against code:
- Status, Owner context, and section 2 (O5, O6, O11, O14).
- 3.5, 3.6 and 3.9.
- 4.2.
- 5.2.3 to 5.2.5 and 5.2.9: the fee closure, `plain_mean`, the ports and their margins. Checked against
  `core/quant/strategies.py:111-116, 330-348, 379-389`.
- 5.3.2 (every step, especially steps 1, 5, 6, 7 and 13). Checked against `docs/asset_expansion_study.py:68-79,
  94-104, 138-153, 172-200, 326-343, 724-732`.
- 5.3.3 and 5.3.4.
- 5.4.1 to 5.4.3 (P0 to P13, `cents`, `select_matched`).
- 5.5 (every step, especially step 5: `gate_predicates`, `agree` and `reference_drift`). Checked against
  `core/quant/validate.py:240-270, 345-381, 421-437, 455-533` and the stored card
  `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json` (md5 `d0bb0882fb51dec361cf2ddb160186bb`, re-measured).
- 6.3 to 6.6.
- Section 7: R-06, R-11, R-13, R-17, G-01 to G-08.
- 8.2: F1, F1r, F2, N2, N4, N6 to N8, and the synthetic series, L2-12's included.
- 8.3: tests 1, 2, 7, 20, 21, 29 and 30.
- 8.4: tests 7, 11 and 12.
- Section 9: Steps 1a and 6 to 9.
- 10.1 to 10.4.
- 11: risks 9 to 11, 15 and 16.
- Appendix B: the quant rows, and the round-2 and round-3 interpretations.

## Earlier issues

Round 3 (all three resolved):

- **QUANT-R3-1: resolved.**
  - 5.5 step 5 (spec:858) compares the card's `n_years` with `len({d[:4] for d in wf_qg.dates})`, and records
    today's whole-year `sc_qg.n_years` beside it. G-08 (spec:1216), 6.3 `gate.reference` (spec:1059), L1-29
    (spec:1360) and 10.3 (spec:1561-1562) agree with it, and Appendix B corrects the round-2 interpretation
    (spec:1722-1726). It never compares `lines`, `reason` or `revise_target`.
  - New evidence that this was the only drift: `rescore_krx_probe.py` re-scores `S_E1_trend_krx` (created 2026-09-27,
    like the reference) through `study.run_trend`.
    - Data: 2,662 sessions from 2015-10-01 to 2026-09-23, equal to the card's.
    - `chosen_last`, `n_trades`, `n_sessions`, `sr_oos`, `ci90`, `oos_is`, `sr_stress`, `years_positive`, `plateau`,
      `pbo`, `prob_loss_oos` and `bench_p` all reproduce bit for bit. The decision is REJECT on both.
    - The calendar-year count gives 9 = the card's `n_years`. Today's `full_years` gives 7.
    - Of the card's 22 floats, 20 are bit-equal. The two that differ are `pbo_slope`, by 5.6e-16 (`np.polyfit`; G-08
      does not compare it), and `seconds`.
  - So today's gate and loaders, on this Linux build, reproduce floats that the owner's build wrote on 2026-09-27.
    This supports the ruled design: tolerances rather than bit equality, and the year count as the one rule change.
- **QUANT-R3-2: resolved as ruled, with one defect in the new test.**
  - Step 6 defines pilot 2's `rf = 0.0`, the study's default (spec:706; `docs/asset_expansion_study.py:175`; the
    crypto call at `:335-343` passes no `cash_daily`). 10.2 says the same (spec:1535).
  - L2-12 exists (spec:1378). Its series is specified at spec:1311-1314, and it is in Step 7's done-when
    (spec:1432).
  - I reproduced the series: start 398.59, end 60,000.00, maximum 60,450.91, md5
    `c68986bf632dea074edb5c8ccef76a7d`, and every close passes the round trip.
  - L2-12's final assertion contradicts 5.5 step 5 (QUANT-R4-1 below).
- **QUANT-R3-3: resolved.**
  - Integer and dict fields are compared exactly, floats within 1e-9, and `bench_p` within 1/2000 (spec:858).
  - `reference_card` and `reference_card_md5` are in 6.6 (spec:1109) and in 10.2 (spec:1538), whose md5 matches the
    file today.
  - Step 1 checks the md5 before registration (spec:701), R-11 names it (spec:1187), and L1-29 checks it
    (spec:1360).
  - The 1e-9 bound has a large margin: on 9-decimal closes, the KRX probe's largest G-08 float gap is 7.4e-14
    (`ci90[0]`), and the drift list stays empty (`rescore_krx_rounded_probe.out`).
  - None of G-08's fields depends on `n_trials`. Only `dsr` and `haircut_sr` do (`core/quant/validate.py:507`), and
    G-08 compares neither. So the bridge's larger `n_trials` cannot cause drift.

Rounds 1 and 2 (all closed in round 3; re-checked at their Revision-4 lines):
- QUANT-1: P0a and P0b (spec:707, 791).
- QUANT-2: both matrices scored; equal decisions and predicates (spec:858; G-02 at spec:1210).
- QUANT-3: `select_matched` (spec:818-825).
- QUANT-4: `n_trials` and its four counts (spec:857).
- QUANT-5 and QUANT-R2-3: P7 (spec:798, stated in Decimal at spec:810-813).
- QUANT-6 and QUANT-R2-4: claim labels (spec:1090, 1524, 1537; L1-30 at spec:1361).
- QUANT-7: 10.3 (spec:1546).
- QUANT-8: moot.
- QUANT-9: the P10 bound (spec:801).
- QUANT-10: N6 (spec:1302).
- QUANT-11: `rules.engine` (spec:1090).
- QUANT-R2-1: step 6, R-06 and L1-7 (spec:706, 1182, 1338).
- QUANT-R2-2: the predicate list (spec:858).
- QUANT-R2-5: (a) L1-29 (spec:1360); (b) closed by QUANT-R3-1.
- QUANT-R2-6: F1r, N6 and L2-7 (spec:1268-1271, 1302, 1310).
- QUANT-R2-7: one rounding (spec:390-391, 705).

All remain resolved. Revision 4 also applied my round-3 notes:
- P6 no longer claims `c_leg` (spec:786).
- P7 is stated in Decimal (spec:798).
- The crypto port uses the same plain loop (spec:438, 534-538).

## New issues

### QUANT-R4-1. L2-12 expects no reference drift, but its own reference counts years by today's rule

- **Severity:** minor.
  - The test fails at Step 7, on synthetic data, before anything of record. L1-29 stops the wrong fix, which would
    change `reference_drift` back to the whole-year rule.
  - L1-29 is enough for that: it requires no drift when the reference holds 11 and `sc_qg.n_years` is 9.
- **Section:** 8.4 test 12 (spec:1378); Appendix B's round-3 interpretation (spec:1758-1759).
- **Problem.**
  - L2-12 ends: "`reference_drift` against a reference the test builds with `validate.score_strategy` on QUANTGEN's
    matrix is empty".
  - A reference built that way holds today's whole-year `n_years`. But 5.5 step 5 compares the reference's `n_years`
    with the calendar years touched by `wf_qg.dates`, the rule that wrote the stored card.
  - On L2-12's series the two counts differ, so a correct bridge reports `n_years` drift and the test fails.
- **Evidence.** `l2_12_probe.py`, with the L2-12 series, the pilot-2 lattice, 10 bp, `cash_daily=0.0`, embargo 1 and
  the domain:
  - 7 origins, 842 OOS sessions, OOS from 2003-01-29 to 2005-05-19;
  - `sc.n_years` (whole years) is 2; calendar years touched are 3;
  - so the drift list holds `n_years`;
  - the decision is INSUFFICIENT_DATA, which L2-12 allows.
- **Second gap (from QUANT-R3-2).** The runner's own G-08 path never runs before pilot 2 of record. That path loads
  `reference_card`, checks its md5, takes `stats`, calls `reference_drift` and writes the WITHHELD. The ruling made the
  comparison a pure function, which L1-29 and L2-12 call directly (spec:1758-1759). A wiring bug there shows first as
  G-06 ERROR or a false "reference drift" after the 5 C3 rows exist.
  - It is fail-closed, and a re-run appends 0 rows (duplicate `config_id`s).
  - But the fix changes `code_sha256`, so it needs a new `owner_confirmed`.
- **Proposed fix.**
  1. In L2-12, build the reference as the stored card was built: `asdict(sc_ref)` plus
     `chosen_last = grid[wf_qg.chosen[-1]]`, with `n_years` replaced by `len({d[:4] for d in wf_qg.dates})`. Expect an
     empty list. Also assert that leaving the whole-year value gives exactly `["n_years"]` (2 against 3 on this
     series).
  2. Run that reference through the runner rather than beside it:
     - the test writes it as a temp card JSON (`{"stats": ...}`);
     - the rehearsal table names it in `reference_card`, with its md5 in `reference_card_md5`;
     - 6.6 allows a rehearsal `reference_card` under the temp dir;
     - expect `gate.reference` with an empty drift list in the run record.
  3. Add a layer-1 twin with the stub child, a synthetic crypto table and a temp card. One `stats` float is moved by
     2e-9, and the expected result is WITHHELD "reference drift", exit 1. It runs on every platform.

### QUANT-R4-2. `reference_drift` cannot form `chosen_last`, and nothing says what switches G-08 on

- **Severity:** minor (an underspecified interface; an implementer resolves it at Step 7).
- **Section:** 5.5 step 5 (spec:858); G-08 (spec:1216); 6.6 (spec:1109).
- **Problem.**
  - **The missing grid.** `chosen_last` is not a field of `StrategyScore` (`core/quant/validate.py:455-489`). The
    study adds it to the card as `grid[wf.chosen[-1]]` (`docs/asset_expansion_study.py:194, 197`). Neither `sc_qg` nor
    `wf_qg` holds the grid, so `reference_drift(sc_qg, wf_qg, ref)` as specified cannot form the dict
    `{"hysteresis": 0.0}` it must compare.
  - **The trigger.** 5.5 step 5 says "Pilot 2" applies G-08 but does not say what the runner keys on: the `pilot`
    value or a non-null `reference_card`. If it keys on `pilot == "C3-BTCUSD"`, no rehearsal can exercise it
    (QUANT-R4-1, point 2).
- **Proposed fix.**
  - Use the signature `reference_drift(sc_qg, wf_qg, grid, ref)`, with `chosen_last` compared as
    `grid[wf_qg.chosen[-1]] == ref["chosen_last"]`.
  - State: "G-08 applies whenever the table's `reference_card` is not null; of-record mode requires it for
    `C3-BTCUSD`."

### QUANT-R4-3. Wording

- **Severity:** minor.
- **Points.**
  - **Pilot 2's rf in P0a.** Step 7 (spec:707) builds `study.rf_daily` "for pilot 1", yet `check_p0a` "requires byte
    equality ... of rf". Add: "pilot 2: no rf comparison; the study passes the default `cash_daily=0.0`"
    (`docs/asset_expansion_study.py:175, 335-343`).
  - **Step 9's done-when (spec:1505).** It inherits Step 8's list of outcomes, which names only "decision mismatch".
    Add the WITHHELD "reference drift" (G-08) as a valid end of pilot 2.
  - **The 5.5 preamble (carried from rounds 2 and 3).** "Only when every hard check of 5.4.1 passes" (spec:852) comes
    before step 1, which builds the `wf_nt` that P12 needs. 4.2 row 16 has the right order. Say "steps 1 and 2 also
    serve P12; steps 3 to 9 run only when every hard check passes".
  - **Optional.** P0a calls `study.yf(symbol)` with its default `start`, while the study's BTC loader passes
    `"2014-09-17"` (`docs/asset_expansion_study.py:732`). Both read the same cache file, and `start` matters only on
    download. One clause would save a reader the check.

## Why I agree or not

I agree. Every issue I raised in rounds 1 to 3 is resolved in Revision 4. The one premise that round 3 had to leave
UNVERIFIED, that nothing in the gate drifted since the stored cards were written except the year count, now has direct
evidence: a same-day stored card re-scores with an empty G-08 drift list and bit-equal floats. G-08's tolerances also
hold on 9-decimal closes with five orders of magnitude to spare.

What is ready to build, in my lens:
- Both engines use QUANTGEN's selection. Both matrices are scored with the gate's exact predicates, and a card needs
  agreement.
- P7 checks every commission against the table and the leg's nominal stress, with `Money`'s rounding.
- The trial count is the union.
- P0 ties every array to the study's loaders.
- The claim labels are honest, and the expected verdicts are stated before the run.
- Pilot 2's comparison with the stored card now tests what the card actually computed.

The three new issues are minor:
- QUANT-R4-1 is a wrong expected value in one synthetic test, plus a cheap test of the runner's G-08 wiring.
- QUANT-R4-2 is an interface gap.
- QUANT-R4-3 is wording.

Each would surface at Step 7 on synthetic data, or fail closed. None is a reason to reopen Step 1a. I would take all
three in the moderator's closing edit.

## Notes

Data touched in this round, for 10.4 (one row for the round-4 referees):
- the stored cards `S_C3_crypto_trend_btcusd.json` (md5 re-measured) and `S_E1_trend_krx.json`;
- `docs/asset_expansion/manifest.json`, and the md5 of `results.csv`, which equals the cards' `results_md5`;
- the cache file names and sizes (a directory listing);
- a scratch copy of `yf_069500.KS.csv`, `yf_152380.KS.csv`, `yf_132030.KS.csv`, `yf_229200.KS.csv` and
  `fred_DGS3MO.csv`, on which the stored `S_E1_trend_krx` 12-setting grid was re-scored.
  - That re-scoring reproduced numbers already on the card, with no new configuration, and it wrote no ledger row.
  - KRX ETFs are not a pilot window and are outside the house rule on SPY and BTC.
- synthetic series and calendars.

I read no SPY price, no BTC price and no ledger row. I wrote no file outside `scratch:referee4_quant/` except this
report.

Checked and sound in Revision 4, beyond the issues above:
- `crypto_trend`'s composite: `np.mean` of nine votes in {-1, 0, 1} (`core/quant/strategies.py:343-347`) gives the
  same float as the port's `sum(votes) / len(votes)`, since the integer sum is exact. On the lattice, `comp > 0.222`
  means `comp >= 2/9`, the same in both.
- `pbo_cscv` is deterministic (`core/quant/validate.py:240-265`). With 4,392 rows, S is 16, so there are 12,870
  splits, and the card's PBO 0.190909... is 2,457 / 12,870. The 1e-9 bound is effectively exact there.
- The stored card's `turnover_annual` equals 144 / 3,634 x 252, so `n_trades` counts unit switches, as P4 and the
  rebuild assume.

UNVERIFIED:
- Whether `crypto_trend` itself changed between the card's run and the baseline commit. The only stored `crypto_trend`
  cards use BTC prices, which may be read only after registration. The trend-family evidence above does not cover the
  signal function.
- Standard-precision `Money` rounding on Windows (Step 7A).
