# Round 1 referee report: quantitative methodology

Spec: `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md` (draft revision 1, 1,188 lines).
Date: 2026-10-27. Referee: Claude (quantitative methodology). Repository at `527cdf2`.
Scope: the trial classification rules; TOTAL against N_raw, N_eff and N_validation; the shadow DSR and its use of
`n_trials` and the cross-trial Sharpe dispersion; the ⑨-3c validation plan; every path by which the design could
silently change an existing verdict. Governing requirement: owner ruling R3 (`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:73-80`).

This review changed no repository file except this one. It wrote no ledger row and ran no test suite. It did not
open or hash the four excluded cache files. Its probes read card JSON and import `core.quant.validate` only; they
are in `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/r3_referee_quant/`.

---

## Verdict

**ACCEPT_WITH_CHANGES.** No blocker. Thirteen major issues and eight minor ones.

The architecture is sound. It has an append-only event log keyed by run ID, and the existing verdict is computed
unchanged. Shadow counts are labelled and never written to a card. Each verdict difference is attributed to count,
gate or data. These meet R3's separation requirement (T2, T15). The repository claims I re-checked hold. The numbers
I re-derived match the spec.

The majors fall in three groups.
1. **Paths to an unintended change of existing behaviour** (Q-01 to Q-03). The shadow writes `GATE` in a threaded
   page. Recorder hooks can raise inside `run_family`. The refactor of the production ledger writer has no golden
   test.
2. **Counting rules that misstate the history or contradict their sources** (Q-04 to Q-08). Card counts ignore
   time order and span. This contradicts the repository's own selection-factor rule. Adoption of ledger rows can
   count a configuration zero times. DATA_CHOICE inverts map03 R-6c. The E-variants use the pairing that map03 R-3d
   forbids. The behaviour fingerprint can double N_raw for a whole family with no strategy change.
3. **A validation plan that cannot answer the owner's question as written** (Q-09 to Q-13). The A1 tolerance
   loosens when replications are cut, and it fails a calibrated criterion by multiplicity. Layer A tests a statistic
   the gate never uses. A5 and A6 decide the outcome before any simulation. The A7 power metric will not
   discriminate. The Layer C "null" earns the cash rate.

---

## Sections reviewed

| Spec section | Checked against |
|---|---|
| Header, spot-checks, 1 (status, scope, separation) | `OWNER_RULINGS_LOG.md:71-88`; `core/quant/gate_package.py:36-38` (frozen list); `core/quant/validate.py:53-74` |
| 2 (traceability T1–T18) | R3 text; sections 3–9 |
| 3 (definitions) | `ui/strategy_lab_page.py:55-136`; `core/quant/gate_ledger.py:54-66`, `:168-171`, `:421-582`; `.gitattributes` |
| 4 (classification, readings, worked examples) | map03 §5 (R-1 to R-9, counting table, classification order); `core/quant/strategies.py:330-348`; `docs/asset_expansion_study.py:325-343` |
| 5 (data model, statuses, registration order) | `ui/strategy_lab_page.py:85-136`, `:227-279`; `gate_ledger.py:265-368` |
| 6 (shadow computation, diagnostics, stored cards, labelling) | `validate.py:211-237`, `:492-622`; `gate_ledger.py:505-557`, `:588-592`, `:688-733`; `core/quant/gate_stats.py:590-607`; card JSON |
| 7 (comparison report, expected content, Tier A/B) | card JSON (34 files, 16 with DSR); map01 §4.1 and §6 |
| 8 (validation plan) | map03 §4.3, R-3d, R-3 open point, §6 item 7; `core/quant/strategies.py:69-90` |
| 9 (modules, hooks, tests, steps) | `tests/paper_live_acceptance.py:333-359`; `ui/strategy_lab_page.py:227-279` |
| 10 (risks, questions, out of scope); references | as above; literature records |

### Checks run in this review

- **Replay.** The 16 DSR cards are rebuilt from stored `stats` and re-decided by `V._decide_strategy`. All 16
  reproduce decision, reason and revise target (probe `probe1.py`). This agrees with spec 6.6.
- **Flip thresholds.** Under normal moments, holding the backed-out dispersion fixed, the flip N is 769 for
  S_E8_pairs_kodex_tiger, 89 for S_E2_voltarget_kodex200 and 81 for S_E5_xsmom_sectors. For S_S6_pairs_hyundai_kia,
  DSR is 0.9406 at N = 2 and PSR is 0.9659 at N = 1. All agree with spec 7.3.
- **S_S6_pairs_hyundai_kia at n = 1.** Under each of the five moment scenarios of 6.6, `_decide_strategy` gives
  REVISE with target "regime". Its `ci90[0]` = 0.079 > 0, so the minimum-track-record branch (`validate.py:606-611`)
  is not reached. This agrees with spec 7.3.
- **Card dates.** All 16 DSR cards carry `created` = 2026-09-27 (card JSON). This matters for Q-04.
- **Float limit.** `validate.expected_max_sharpe(n, 1)` returns `inf` for n ≥ 1e16; at n = 1e15 it is 8.02. This
  matters for Q-18.
- **Literature records.** Bibliographic data for Bailey & López de Prado (2014), Bailey et al. (2017), Dwork et al.
  (2015), Harvey & Liu (2015), López de Prado (2019), López de Prado & Lewis (2019), Nosek et al. (2018), Rosenthal
  (1979), Simmons et al. (2011), White (2000) and Hansen (2005) match the spec's references as I know them. The
  Halle et al. (2016) arXiv record could not be reached from this container (arXiv: DNS failure; export API: proxy
  403). Its author list is UNVERIFIED in this review.

---

## Issues

Severity: **blocker** (must change before approval), **major** (must change before the stage it affects starts),
**minor** (fix in the next revision).

### Q-01 — major — 6.4 "Method", 6.1 item 6, 10.1 risk 6: the shadow writes module state the existing verdict reads

**Problem.**
- The shadow re-calls `V.score_strategy` inside a `V.GATE["bootstrap_B"]` override, restored in `finally` (6.4).
- The Lab runs each click in a thread (`ui/strategy_lab_page.py:279`, `page.run_thread(worker)`). Concurrent runs
  occur: the repo has a test for "a double-clicked Run" (`tests/paper_live_acceptance.py:347-359`).
- `score_strategy` reads `GATE["bootstrap_B"]` at `validate.py:501` and `:520`.
- Interleaving example. Shadow S saves 2000 and sets 1000. Existing run A saves 1000 and sets 1000. S restores 2000
  while A is between its override and line 501. A's **existing** `ci90` and `bench_p` are then computed with
  B = 2000. A's `finally` restores 1000, so `GATE` stays at 1000 for every later in-process caller.
- The module lock in 6.4 serialises shadows with each other only. The existing path takes no lock (10.1 risk 6).
  The design doubles the number of `GATE` windows per run. The invariance check protects the shadow, not the
  existing verdict.

**Fix.**
- The shadow must never write `GATE`. Only `dsr` depends on `n_trials`: it enters `score_strategy` at
  `validate.py:507` and in the stored field; `_decide_strategy` uses `s.n_trials` only in line text.
- Compute `sd` exactly as `validate.py:505-506`. Then compute `dsr_n = V.deflated_sharpe(wf.pnl, n_trials=max(n, 1),
  sr_sd_daily=sd)`. Then `s_n = dataclasses.replace(existing_score, dsr=dsr_n, n_trials=n, lines=[])` and
  `V._decide_strategy(s_n)`, which only reads `GATE`. This is exact. It costs no bootstrap or CSCV, so risk 12
  disappears.
- Keep T-RUNREG-06's equality against a fresh `score_strategy` call, inside the test process only.
- Remove 6.1 item 6 and the shadow module lock. They are then unnecessary.

### Q-02 — major — 9.2 item 3, 6.7 last bullet, 6.4 "Order and latency": recorder failures and latency inside `run_family`

**Problem.**
- The hooks run inside `run_family` (9.2 item 3). `started(...)` runs before `:104` and computes the behaviour
  fingerprint: the whole grid on a 1,500-day synthetic panel (5.4 "Parameters").
- A registry error there raises inside `run_family`. Examples: a broken chain, a full disk, a lock timeout, a
  duplicate `run_id` (5.5), or an exception in a strategy on the canonical panel. The worker's `except` branches
  (`strategy_lab_page.py:236-240`) then show an error **instead of** the verdict.
- 6.7 promises the verdict is still shown. The only mechanism named is at page level (9.2 item 4).
- The fingerprint also delays the verdict. This contradicts 6.4 "with today's latency".

**Fix.**
- Wrap every hook call in a guard. On any exception it marks the recorder broken, records the reason and returns.
  `run_family`'s control flow and return value must never depend on the recorder.
- Compute behaviour fingerprints after DISPLAYED. They are classification inputs, not identity (3.4).
- Add T-RUNREG-01 cases with a recorder whose every hook raises and one whose hooks sleep. Assert byte-identical
  return values, `payload(r)` and `narrative(r)`.

### Q-03 — major — 9.2 item 1, 6.1 item 3, T-RUNREG-01: the refactor of the production ledger writer has no golden test

**Problem.**
- 9.2 item 1 extracts `_lab_rows` from `register_trials` (`strategy_lab_page.py:55-82`). That function writes the
  owner's production ledgers.
- No existing test pins `config_id` values. Test 17 checks dedup by case and order, and the market
  (`tests/paper_live_acceptance.py:333-344`). T-RUNREG-01 compares with and without a recorder, both on the
  refactored code.
- A refactor that changes any hashed value changes every `config_id`. Examples: the `json.dumps(..., default=str)`
  round trip, symbol normalisation, or `cost_bps` as int against float (canonical JSON of `50` and `50.0` differ).
  Every existing owner row would then look new. Dedup stops working, and L-FAM roughly doubles. No verdict changes,
  but the counting basis R3 asks for is corrupted silently.

**Fix.**
- Before the refactor, freeze golden `config_id`s computed at `527cdf2` for a fixed input set. Include an int and a
  float cost, lower-case and reordered symbols, the pairs order, and each of the seven families.
- Assert equality after the refactor (a new T-RUNREG-01b).
- Alternatively, do not refactor. Build the registry's keys with a new pure function, and assert in a test that it
  equals the rows `register_trials` writes to a temporary ledger.

### Q-04 — major — 6.6 "Counts for a card", 7.2 sections A and E, 7.3: card counts ignore time order and span

**Problem.**
- For a stored card the spec counts |family ledger `config_id`s ∪ card grid keys| at the report date (6.6).
- All 16 DSR cards were created on 2026-09-27 (card JSON `created`). Lab rows written after that date cannot have
  influenced how those cards were selected.
- The repository's own rule for a card counts only rows that overlap the card's evaluation span **and** have
  `run_utc < t_fix`. The docstring says so: "sensitivity rows run after the commit never count"
  (`gate_ledger.py:700-733`; `t_fix` at `:688-697`; map03 R-4, R-6a).
- Under the spec's rule, the E8 flip at n ≥ 769 (7.3) could come entirely from Lab runs on other pairs made after
  2026-09-27. The report would list it as a case where "trial history changes the verdict" (T16). That is not a
  selection effect on that card.
- Section E's attribution (COUNT, GATE, DATA) has no class for this case.

**Fix.**
- For stored cards, make the primary reading "as of the card". Count rows whose first `run_utc` (the ledger keeps
  the first row, `gate_ledger.py:337-346`) is earlier than the card's anchored fix time and whose span overlaps the
  card's span. The card's anchor is the commit that added it, as `t_fix` does.
- Print "as of the report date" as a secondary reading. Label it: "includes trials made after the card; relevant to
  the family's current best claim, not to this card's selection".
- Add attribution class POST_CARD to 7.2 E, so these rows are never reported as COUNT flips.
- Add a universe-scoped reading (the same symbol set) beside the market and family scopes. It answers most directly
  whether this card's configuration was chosen from more trials than its N.

### Q-05 — major — 4.2 rows 13 and 13a, 4.3 step 5, 6.2: adoption can count a configuration zero times, and new keys look adopted

**Problem.**
- Row 13 counts a ledger `config_id` "that no registry key holds" as +1. Row 13a ADOPTED counts 0 "because the
  ledger row already counts".
- After adoption, a registry key holds the `config_id`. So row 13 no longer applies, and with the per-row deltas of
  4.2 the configuration counts zero times. T-RUNREG-05 asserts exactly these per-row deltas.
- Counts are computed after the run's own ledger registration (6.2). A genuinely new key then already has a ledger
  row that no earlier registry key holds. It meets the ADOPTED test (4.3 step 5) and is booked 0 instead of SEARCH +1.
- `hash_before` and `hash_after` (5.4 "Ledger link") are unlocked reads. `FamilyLedger.rows()` takes no lock
  (`gate_ledger.py:311-316`), so concurrent runs can interleave them.

**Fix.**
- Decide ADOPTED against SEARCH from `ledger_link.rows[].appended`, which `RegisterResult` gives per row
  (`gate_ledger.py:337-355`). `appended = True` means SEARCH. `appended = False` with no earlier registry key means
  ADOPTED.
- Define literal N_raw as a set cardinality: |registry experiment keys with a statistic| + |ledger `config_id`s held
  by no registry key|. An ADOPTED key counts in the first term. Rewrite the 13a delta as "+1 registry, −1
  LEDGER_ONLY".
- Make T-RUNREG-05 assert that a LEDGER_ONLY row counts exactly once before and after its adoption.
- Never derive a class from the difference of `hash_before` and `hash_after`.

### Q-06 — major — 4.2 rows 9a and 9b, 4.3 step 6, 4.4, Q6: the DATA_CHOICE primary reading inverts its source, and 9a and 9b overlap

**Problem.**
- map03 R-6c states: "A choice among sources, start dates or cash conventions after seeing results: that dimension
  was searched. Each alternative evaluated is an experiment." map03's counting table books R-6c under SEARCH (+1).
- The spec's primary reading for DATA_CHOICE is 0 and cites R-6c. It also breaks the spec's own principle 4.1.2,
  "default is to count".
- Row 9b's test ("differs from every earlier evaluation ... that was displayed") is exactly R-6c's "after seeing
  results" condition. The test is right; the count is not.
- The two rows overlap. In the Lab the data period is set by `days` (`strategy_lab_page.py:86`, `:223`). Raising
  `days` from 3,000 to 5,000 with the same source satisfies 9a ("a span that contains the earlier span") and 9b
  ("window differs"). No precedence is stated. Lowering `days` is a start-date choice.

**Fix.**
- Primary reading: DATA_CHOICE counts +k. Secondary: 0. Update 4.4 and Q6 to match.
- Precedence:
  1. Same `source` and `days` → 9a.
  2. Same source with `days` increased → 9a only when the earlier displayed decision was INSUFFICIENT_DATA with
     revise target "extend history". That is the gate's own instruction (`validate.py:590`, `:611`, `:621`).
  3. Otherwise → 9b.
- Record the rule in T-RUNREG-05 with one case per branch.

### Q-07 — major — 6.3 E-FAM, E-MKT and E-GRID; 6.5 first diagnostic; 7.3 S6 row; Q3 and Q4: the forbidden pairing is used, and E-GRID is not trial history

**Problem.**
- map03 R-3d: "Do not use (N_eff, raw dispersion)". In map03 §4.3, column (b) raises the false-pass rate in every
  correlated case: 0.075 at the plateau against 0.051 for (a); 0.050 against 0.010 for three blocks.
- The spec's E-variants pass ⌈N_eff⌉ with the current grid's `sr_sd` (6.4 "Dispersion"; `validate.py:505-506`). So
  does the "DSR at a real N" diagnostic of 6.5.
- The only REJECT→REVISE case in 7.3 (S_S6_pairs_hyundai_kia) arises only through E-GRID with n = 1.
- E-GRID uses this run's grid only. It reflects no trial history, which is what R3 asks about ("시행 이력을 반영했을
  때"). Presenting it among the flip cases mixes a correlation adjustment with the trial-history question.
- The N_raw variants (L-\*, R-\*) also pair a family-wide N with one grid's dispersion. 6.4 notes this, but the
  decision rows do not.
- When G = 1, `sr_sd` = 0 (`validate.py:506`) and every N-variant is vacuous (the S_V4 row of 7.3).

**Fix.**
- Make the matched pairing (N_eff, SE_null) of 6.5 the E decision row.
- Keep (⌈N_eff⌉, grid dispersion) only as a disclosure row labelled "mismatched pairing (map03 R-3d);
  anti-conservative in map03 §4.3(b)". Apply the same label to the 6.5 real-N diagnostic.
- Move E-GRID and the S6 case to a separate report section: "correlation adjustment of the current grid — not
  trial history".
- Label every L-\* and R-\* decision "assumes the family's cross-trial Sharpe dispersion equals this grid's". For
  Lab runs, add a dispersion sensitivity (×1, ×1.5, ×2), as the k column does for cards.
- Print "n-invariant (one configuration)" instead of "unchanged" when G = 1.

### Q-08 — major — 3.4, 3.7, 4.2 rows 8a and 8b, 10.1 risks 2 and 3: the behaviour fingerprint can double N_raw for a whole family

**Problem.**
- The experiment key contains `behaviour_sha256` (3.7). It is computed on a canonical panel that is regenerated from
  a seed (5.4).
- NumPy's policy does not guarantee that `Generator` distribution streams stay stable across NumPy versions (NEP 19,
  https://numpy.org/neps/nep-0019-rng-policy.html; stated from memory, UNVERIFIED in this session because the
  network is blocked).
- Any of three things changes every configuration's fingerprint at once:
  - the panel changes (a NumPy upgrade);
  - a platform float difference lands at a rounding boundary of 1e-10 or 1e-12;
  - a shared callee changes (`simulate`, `_sma`), which `fn_source_sha256` does not cover.
- By row 8b each configuration then becomes a new key. R-FAM and R-RULE roughly double for the family, although
  nobody changed a strategy. Risk 3 says the error "errs on the side of counting, and it is flagged". It is not
  bounded: it compounds with every environment change.

**Fix.**
- Generate the canonical panel once. Store its bytes under `runs/` and its hash in every STARTED event. Always load
  it; never regenerate it.
- Consult the behaviour fingerprint only when `fn_source_sha256` or a decision-path file digest (5.4 `files`)
  changed.
- When the code digests are equal but the panel hash, the NumPy version or the platform differ, treat the key as the
  same. Add the class ENV_CHANGE (TOTAL +1, N_raw 0, flagged), parallel to GATE_CHANGE.
- Record `numpy.__version__` and the platform in STARTED.

### Q-09 — major — 8.3, 8.5 A1, 8.6: the A1 tolerance rule is unusable as written

**Problem.**
- **Size.** 8.3 does not say which factors are crossed. Fully crossed, the null and mixed-null points per layer are
  3 distributions × 3 lengths × 13 correlation structures × 4 values of R × 2 between-run ρ × 4 null types = 3,744.
  The alternatives add 7,488. Layer A at 10,000 replications is about 3.7e7 replications, with up to R × K = 1,000
  columns of 5,040 days each. This is far beyond the 2-hour cap of 8.6.
- **Perverse cut.** 8.6 cuts replications to fit the cap. That raises the MCSE. A1's bound "0.05 + 2 · MCSE" then
  widens. The less simulation is run, the easier acceptance becomes.
- **Multiplicity.** A criterion whose true rate is exactly 0.05 exceeds 0.05 + 2 SE at one point with probability
  about 0.023. Over m points it passes everywhere with probability 0.977^m: 0.10 at m = 100, about 0 at m = 3,744.
  Only conservative criteria can pass, whatever their power.
- **Not a size-α test.** DSR ≥ 0.95 compares the observed Sharpe with the expected maximum, not with a quantile of
  the maximum (map03 §4.3, note under the table). "≤ 0.05" is therefore a ceiling, not calibration. Reporting
  pass or fail alone hides how conservative each criterion is.

**Fix.**
- Publish the design table: which factors are crossed. Use a fractional design.
- Fix a minimum precision for every A1 point (MCSE ≤ 0.005, so at least 1,900 replications). Cut design points by a
  pre-registered priority list, never replications.
- Restate A1: the point estimate is ≤ 0.05 at every point. Any point within 3 MCSE of the bound is re-run with fresh
  pre-registered seeds, and the re-run decides.
- Report the estimated rate with its MCSE at every point, not only pass or fail.

### Q-10 — major — 8.2, 8.3 Layer A, 8.5 A1, 6.5 second diagnostic: the estimand differs from the gate's statistic, and a candidate is missing

**Problem.**
- Layer A applies the DSR to the best configuration's **full-sample** series. The gate applies it to the
  **walk-forward OOS** series (`validate.py:499-507`; `strategy_lab_page.py:116`, `:127`). A1 must hold in both
  layers.
- Within one walk-forward, the OOS segment is not selected on, so G is not obviously the selection count. map03
  leaves this open (R-3, "Open within R-3"; §6 item 7).
- Requiring calibration in Layer A favours criteria built for a statistic the gate never computes. It can also
  reject a criterion that is right for the gate.
- The candidate list (8.2) lacks the count that matches the OOS statistic: the number of distinct walk-forward
  experiments whose OOS result was seen in scope (runs with new keys, R in 8.3), with the hurdle
  SE_null(T_oos) · e(R).
- 6.5 defines SE_null on T_full without a reason. The tested statistic has T_oos observations.

**Fix.**
- Make Layer B, confirmed by Layer C, the layer of record for A1 and A7.
- Keep Layer A as a formula check: C0 at R = 1 must reproduce map03 §4.3 column (a) within MCSE.
- Add candidate C7: N = distinct walk-forward experiments seen in scope; hurdle SE_null(T_oos) · e(N).
- Evaluate C4 and C5 with both T_oos and T_full. Justify the choice in 6.5, or print both.

### Q-11 — major — 8.5 A5 and A6, 8.2, Q11: A5 and A6 decide the recommendation before any simulation

**Problem.**
- **A5** ("N and the dispersion term describe the same set of trials") is false by construction for C1, C1r and C3,
  which use the current grid's dispersion. So the owner's own "ledger basis" (L-FAM, close to C1) can never be
  recommended, whatever its error rates and power.
- **A6** requires series coverage of at least 95 %. LEDGER_ONLY rows have no series (4.2 row 13), and Q11's default
  is not to re-run them. So C2, C3 and C4 fail A6 on the owner's data.
- The survivors are C0, which ignores R by design, and C5. The fallback in 8.5 keeps C0. The outcome is largely
  fixed before ⑨-3c runs.

**Fix.**
- Make A5 a reported property, not a filter.
- Judge A1 to A4 and A7 on simulation results alone.
- Report A6 separately, as an operational constraint with its named fallback (for example: the criterion is
  recommended, and it is computable for k of n owner runs; the others use a stated fallback).
- State in 8.5, before the study runs, which candidates can still be recommended.

### Q-12 — major — 8.3 alternatives, 8.4, 8.5 A7: the power metric will not discriminate between criteria

**Problem.**
- The alternatives are true annual Sharpe 0.3, 0.5, 0.8 and 1.0 for one configuration or a block of four.
- At T = 1,260, T_oos is about 500 sessions after the first 756-session in-sample window. A single strategy's
  t-statistic is then about 0.3 · √2 ≈ 0.4 to 1.0 · √2 ≈ 1.4. The in-sample window rarely selects the true
  configuration among K = 100 nulls.
- The median power over alternatives (A7) will be near zero for every criterion. Ties will decide the
  recommendation.
- Power of the DSR predicate alone ignores the other predicates. PASS also needs `ci_ok`, `pbo_ok` and the five
  engineering checks (`validate.py:576-604`). "Without destroying power" is a gate-level question.

**Fix.**
- Choose alternatives so that C0's power spans about 0.2 to 0.9 at each T.
- Use a summary that separates criteria: the area under the power curve, or the minimum detectable Sharpe at 50 %
  power.
- Report power at two levels: the DSR predicate in Layer B, and the rates of PASS and of "not rejected for DSR" in
  Layer C.
- Report the power loss against C0 with its MCSE at every point.

### Q-13 — major — 8.3 Layer C: the Layer C null earns the cash rate, so it is not a null

**Problem.**
- `simulate` credits the unallocated fraction of a long-only book with `cash_daily` (`core/quant/strategies.py:84-87`).
  The Lab uses 0.03/252 (`strategy_lab_page.py:113`).
- On driftless prices, a long/flat rule earns cash while flat. Its true Sharpe is positive, and while it is fully
  flat its P&L is a constant.
- 8.3 sets the cost to 0 for calibration but says nothing about cash. False-pass rates "under the null" would be
  inflated and blamed on the criteria.

**Fix.**
- Run Layer C calibration with `cash_daily = 0`. Alternatively, drift prices at the cash rate and test excess
  returns.
- State the choice in 8.3. Add a Layer C smoke check: C0's PASS rate under the null is at most its Layer B
  predicate rate.

### Q-14 — minor — 4.2 row 2: EVAL_REDRAW drops the half of map03 R-1b that makes "0" safe

**Problem.**
- map03 R-1b counts a re-draw 0 **because** "the verdict of record is the one at the pre-registered seed and B", and
  it flags "verdict unstable under resampling".
- The spec keeps the 0 but drops both conditions. Its stated reason ("choosing among re-draws would select on
  outcome") then argues against counting zero.
- The seed moves `ci90` and `bench_p` (`validate.py:501`, `:520`), not the DSR.

**Fix.**
- Restore both conditions in row 2.
- Note that the Lab always uses B = 1,000 and seed 11 (`strategy_lab_page.py:86`; `validate.py:493`). So no Lab run
  produces EVAL_REDRAW today.

### Q-15 — minor — 3.1, 4.2 row 3, 5.6, 5.8: the failure stages contradict each other

**Problem.**
- "No cost row" is listed as FAILED_BEFORE_STATS (4.2 row 3; 4.5). But `run_family` raises it at
  `strategy_lab_page.py:96`, before the `started()` hook placed before `:104` (9.2 item 3). By 3.1 it is therefore
  not a run.
- 5.8 says a failure "in `pnl_matrix`" is FAILED_AFTER_STATS. 5.6 defines that status as stage ≥ PNL_COMPUTED. A
  failure inside `pnl_matrix` leaves the stage at DATA_LOADED.

**Fix.**
- Either call `started()` at the top of `run_family`, or drop the example.
- In 5.8, write "failure after `pnl_matrix` returned".

### Q-16 — minor — 4.2 rows 7 and 7b, 4.3 step 6: two gaps in the classification table

**Problem.**
- (a) A validated key counts 0 in N_raw (row 7). When the validation is spent (row 7b), re-evaluating the same key
  on an overlapping span is a "seen" key. It becomes REMEASURE (0), so the key never enters N_raw although its
  result was looked at twice. map03's counting table books "VALIDATION_SPENT → re-tuned run" as +1.
- (b) 4.3 step 6 has no branch for a seen key with the same data where both (seed or B) and the gate version differ.

**Fix.**
- (a) When a validation is spent, count its keys +1 in N_raw from the validation run.
- (b) Add a catch-all: REMEASURE with the flag MULTI_CHANGE. Alternatively, apply the default-to-count rule and
  make it SEARCH; state which.

### Q-17 — minor — 4.5 "C3", 4.2 row 6, T-RUNREG-05: the C3 lattice argument assumes no zero vote

**Problem.**
- `np.sign` returns 0 on equal prices (`core/quant/strategies.py:344`). The composite then takes even ninths, for
  example 2/9 ≈ 0.222, which lies between 0.2 and 0.3.
- So "0.2 and 0.3 are one rule" holds only when no zero vote occurs. KRW prices are integers, so ties can occur.
- On a continuous synthetic panel zero votes almost never occur. T-RUNREG-05 therefore cannot "settle" the study
  comment (`docs/asset_expansion_study.py:325-330`) for real data.

**Fix.**
- State the assumption in 4.5.
- Settle semantic duplicates on the real-data fingerprint whenever both ran on the same `data_md5` (row 6 already
  requires this).
- Add a panel with tied closes to T-RUNREG-05.

### Q-18 — minor — 7.3 "Flip n" column, 6.6: the large flip values cannot come from the stated formula

**Problem.**
- 6.6 defines e(n) as `validate.expected_max_sharpe(n, 1)`. That function returns `inf` for n ≥ 1e16, because
  1 − 1/n rounds to 1 (checked in this review).
- So "~1e28 (1e17–1e72)", "~1e25" and "> 1e100" in 7.3 come from some other computation, which the spec does not
  name. T-RUNREG-07 pins only 769, 89 and 81.

**Fix.**
- Print "> 1e6: no realistic n". Alternatively, compute with `norm.isf(1/n)` in log space and name the formula.

### Q-19 — minor — 6.4 "Predicates": the predicate helper omits the minimum-track-record branch

**Problem.**
- The helper mirrors `validate.py:576-583` and `:592-594`.
- When `dsr_ok` turns true while `ci_ok` is false, `_decide_strategy` can return INSUFFICIENT_DATA instead of REVISE
  (`validate.py:606-611`). The report's "reason in words" would then be wrong.

**Fix.**
- Add the minimum-track-record test to the helper and to the report's reason.
- Take the decision itself only from `_decide_strategy`. The spec already intends this; say so explicitly.

### Q-20 — minor — 3.12, 6.2, 6.3: N_eff will often be unavailable or estimated on a short window

**Problem.**
- `gate_ledger.n_eff` uses one common window over all series: the intersection of their indices
  (`gate_ledger.py:421-444`). It refuses below 20 observations (`:76`).
- A family-wide scope that mixes markets, pairs and eras can fail outright or rest on a short window.
- The function is documented for difference series (`gate_ledger.py:447-449`; module docstring `:16-17`), not raw
  net P&L. Its calibration targets (map03 §4.2, T-NEFF-01) do not transfer automatically.
- With LEDGER_ONLY rows and Q11 = no, E-FAM and E-MKT are unavailable on the owner's data.

**Fix.**
- Say so in 6.3. Print the common-window length with every N_eff.
- State that the input is raw net P&L, as dated series (pass dated Series, not arrays).

### Q-21 — minor — 8.3 "Research process", mixed null in Layer B: no adaptive revision, and the "selected configuration" is undefined

**Problem.**
- Real Lab use follows the gate's revise targets ("coarsen the grid", "move to the plateau centre and re-run",
  `validate.py:616-621`).
- Independent runs, or runs sharing a factor, do not model a next grid centred on the previous winner. That is where
  N_raw over-counts most and where selection is most adaptive.
- In Layer B the chosen configuration changes across origins. "A pass whose selected configuration has a true Sharpe
  ≤ 0" is therefore undefined there.

**Fix.**
- Add an adaptive design: grid r + 1 is centred on the in-sample winner of grid r.
- In Layer B, define a mixed-null false positive by the OOS-length-weighted true Sharpe of the stitched series being
  ≤ 0.

---

## Claims verified without objection

- The frozen harness list and the design's import-only use of it (`core/quant/gate_package.py:36-38`).
- `config_id` excludes span, run time and code (`gate_ledger.py:60-61`, `:168-171`). Unknown row fields are refused
  (`:190-192`). Dedup keeps the first row (`:337-346`).
- `RegisterResult.row_md5` is a line hash on append and the stored content hash on dedup (`gate_ledger.py:346`,
  `:355`).
- `FamilyLedger.rows()`, `.hash()` and `.n_raw` read without a lock and write nothing (`gate_ledger.py:276-335`).
- `n_trials` affects the decision only through `dsr` (`validate.py:507`; `dsr` is read at `:578`, `:593`, `:596`
  and, through `hard[1]`, at `:606`). Integer truncation is at
  `validate.py:213`.
- `gate_stats.psr` uses the same denominator and √(T − 1) as `validate.deflated_sharpe`
  (`gate_stats.py:590-607`; `validate.py:220-237`). `gate_ledger.emax_iid` equals the closed form for N ≥ 2
  (`gate_ledger.py:519-527`). So the T-RUNREG-06 consistency test is well posed. Compare with a tolerance, such as
  1e-12.
- The Lab's verdict call uses `n_trials=len(grid)` with the B = 1,000 override (`strategy_lab_page.py:124-129`).
  The study comment at `validate.py:496-497` says `n_trials` "counts every configuration ever tried (grid size plus
  revisions)". The Lab's current practice is therefore narrower than the gate's own documentation. This supports
  R3's direction; it is not a defect of the spec.
