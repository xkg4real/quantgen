# 03 — Counting trials: total runs versus effective experiments (methods survey and rule set)

Date: 2026-10-27. Scope: owner ruling R3 (2026-10-27), methods step. It grounds two things: the split between the
**total run count** and the **count of experiments valid for overfitting assessment**, and the treatment of simple
re-runs, failed runs, parameter searches and independent validations.

Status: read-only. No repository code was changed. No card verdict, GATE constant or ledger row was touched. No test
was run. The four excluded cache files were not opened. The synthetic checks in §4 use generated Gaussian data
only. They import the frozen modules read-only and run from the session scratchpad
(`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/neff_compare/`). They are not
part of the repository. `git status` was identical before and after each script.

Literature check: WebSearch worked; WebFetch and direct downloads did not (DNS failure and a proxy refusal for the
authors' hosts). Titles, journals, years and DOIs below were confirmed through search records unless marked
otherwise. Statements about a paper's **content** that were not confirmed this way are marked UNVERIFIED. Some
content of the DSR and PBO papers was verified earlier from the authors' preprints and is recorded in
`research_notes/QUANTGEN asset coverage expansion/validation_methodology.md:113-120`; this note cites that record.

Companion notes: `01_strategy_lab_and_cards.md` (how cards and the Lab count today, card-by-card flip margins) and
`02_gate_ledger_semantics.md` (what the frozen ledger can and cannot store).

---

## 0. Summary

1. **Every method needs more than a count.** DSR needs N **and** the cross-trial Sharpe dispersion. PBO, White's
   Reality Check, Hansen's SPA and every correlation-based N need the **return series of every trial**. A registry
   that stores only counts cannot feed any of them. It must store, per experiment, a result fingerprint and a
   reference to its daily P&L (or difference) series.
2. **Total runs and valid experiments are different units.** Total runs count executions. Valid experiments count
   distinct configurations whose performance was observed and could inform a choice. Correlated experiments are then
   reduced to an effective count. A third count, pre-registered validations, is kept apart from both.
3. **An identical re-run adds nothing to the experiment count.** This holds by construction: an exact duplicate does
   not change the maximum of a set. The expected maximum used by the repo's `N_equiv` is unchanged by duplicates
   (§4.2: 0.663 for 11 rows and for their 5 distinct rules). Bonferroni, the BLdP linear N, eigenvalue N's and PBO
   are **not** duplicate-invariant. So the registry must collapse duplicates before it counts.
4. **Failed runs split on one question: was a performance statistic produced and visible?** No statistic: a run, not
   an experiment. Statistic seen, then failure, abandonment or discard: an experiment (the file-drawer problem).
5. **Each distinct configuration in a search is a raw experiment.** Correlation reduces the effective count. The
   estimators disagree widely. On one synthetic 100-configuration grid they range from 10 to 89 (§4.1). This choice
   is contested and is the core of the separate validation the owner reserved.
6. **The dispersion term must be paired with the right N.** Using a correlation-reduced N together with the raw
   cross-trial Sharpe dispersion counts the correlation twice. In synthetic zero-skill tests this raised the false
   pass rate from 0.051 to 0.075 (flat plateau) and from 0.010 to 0.050 (block grid). The pairing used by
   `gate_ledger.step3` (null standard error × e(N_eff)) stayed at or below 0.050 (§4.3).
7. **An independent validation is not a search trial, under four conditions.** The configuration and the pass rule
   are fixed with an anchored timestamp first. The validation span was not touched by any family run before that.
   It is evaluated once. It is never re-tuned on that span. The repo already encodes the first two through `t_fix`
   and the any-overlap rule (`core/quant/gate_ledger.py:688-733`).
8. **The repo is not internally consistent on validations.** `selection_factor` gives f = 1 to a configuration fixed
   before any run touched its span (`gate_ledger.py:719-722`). The CRY-1 study, however, adds a pre-registered split
   and an ETH replication to C3's N as one trial each (`docs/techfund_study.py:83-85`, `:446`). The parallel
   computation should print both readings.
9. **A code or data change is a new experiment only when it changes what is being tested.** A refactor with an
   identical result fingerprint is a re-run. A change to signal logic is a new configuration. A gate change is a new
   gate version, not a trial. A bug fix and a data-source switch are contested: they depend on whether the change
   was chosen after seeing results. The repo already uses that test for package changes
   (`core/quant/gate_package.py:241-255`, `results_seen`).
10. **Two repo details matter for the parallel computation.** `validate.expected_max_sharpe` truncates N to an
    integer (`core/quant/validate.py:213`), so N_eff = 1.45 gives a hurdle of 0 instead of 0.317 (§4.5). The
    parallel computation can avoid this without editing a frozen file: use `gate_ledger.emax_iid` (real N) and
    `gate_stats.psr(sr0=...)`.
11. **White's Reality Check and Hansen's SPA are in `core/quant/tf_gov.py:257-291`, not in `gate_stats`.**
    `tf_gov.py` is not on the frozen list (`core/quant/gate_package.py:36-38`).

---

## 1. Terms used in this note

| Term | Meaning here |
|---|---|
| **Run** | One execution of the Lab or study code path, with a unique run ID, whatever its outcome. |
| **Configuration** | One evaluated rule instance: family, rule, parameter vector, universe, cost condition and the ledger's other key fields. This is the ledger's `config_id` key (`gate_ledger.py:60-61`, `:168-171`), plus the strategy-code version (see R-5). |
| **Evaluation context** | What a run evaluated the configuration on: code version, data snapshot hash, span, gate version, seed, bootstrap B, cash-rate convention. |
| **Result fingerprint** | A hash of the configuration's daily position (or P&L) series on a stated span. Equal fingerprints mean the same tested rule, whatever the parameter literals. |
| **Experiment** | A configuration whose performance statistic was produced and could be seen, on data that a selection could use. Counted once, however many runs evaluated it. |
| **TOTAL** | Number of runs. |
| **N_raw** | Number of distinct experiments in a scope (family-wide or market-scoped). |
| **N_eff** | The correlation-adjusted count of those experiments. The repo's rule is `max(N_clusters, N_equiv)` (`gate_ledger.py:574-582`; `core/rules/macro_rules.py:57`). |
| **N_validation** | Number of pre-registered evaluations on untouched data. Not part of N_raw. |
| **V** | Cross-trial variance of the experiments' Sharpe ratios (the DSR dispersion term). |

---

## 2. Methods: what each one needs from a trial record

### 2.1 Deflated Sharpe ratio (Bailey & López de Prado 2014)

- **Formula.** DSR is a probabilistic Sharpe ratio whose hurdle is the expected maximum Sharpe of N trials:
  `SR0 = sqrt(V[{SR_n}]) · [(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(N·e))]`, γ the Euler–Mascheroni constant. The paper's eq. 1
  is stated for N independent trials (record of the preprint: `validation_methodology.md:119-120`). The repo
  implements it at `core/quant/validate.py:211-237`.
- **Two inputs, not one.** The hurdle is the product of a dispersion term `sqrt(V)` and a count term `e(N)`. Both
  must describe the same set of trials. Correlated trials shrink V as well as N. This is why §4.3 matters.
- **Correlated trials.** The paper tabulates an "implied number of independent trials" against the average
  correlation and the number of trials M (its Exhibit 4; confirmed as a heading through search). The repo states the
  mapping as `N_hat = ρ̄ + (1 − ρ̄)·M`, "BLdP eq. 9 (linear)", and prints it as a bound only
  (`gate_ledger.py:468-470`; spec `research_notes/QUANTGEN v2 integration map/spec_M7_gate_package.md:91`). The exact
  equation in the paper was not re-read here: UNVERIFIED.
- **Record needed.** Per experiment: its Sharpe ratio on a common length (for V), and enough to compute correlation
  (for an effective N).

### 2.2 Probability of backtest overfitting, CSCV (Bailey, Borwein, López de Prado & Zhu 2017)

- **Method.** Form the T×N matrix of P&L series of all N trials. Split rows into S blocks. For every half/half split,
  rank the in-sample winner out of sample. PBO is the share of splits where it ranks below the median
  (`validation_methodology.md:113-115`; repo `validate.py:240-265`, `core/quant/gate_stats.py:651-724`).
- **Count enters through the matrix.** No separate N is passed. Correlation is handled implicitly, because the actual
  series are ranked. But exact or near duplicates change the ranks: unequal duplication lowers PBO (§4.4). The repo
  already notes that near-identical configurations push PBO toward 0.5 (`validate.py:59-67`).
- **Record needed.** The full daily P&L series of every experiment, on a common window. `gate_stats.pbo_on_claim`
  expects "family ledger union the frozen PC-6 grid" (`gate_stats.py:655-656`). The Lab today feeds only the current
  grid (`validate.py:508`).

### 2.3 False strategies and clustering of trials (López de Prado and co-authors)

- **López de Prado & Lewis (2019).** An unsupervised method (ONC, a k-means variant that selects the number of
  clusters) estimates the number of effectively uncorrelated trials K. Cluster-level returns give K Sharpe ratios.
  Their variance is the dispersion term for the DSR. Confirmed at abstract level through search; the weighting of
  cluster returns was not re-read (UNVERIFIED).
- **López de Prado (2019), "A Data Science Solution to the Multiple-Testing Crisis".** Frames the problem as two
  estimates: the number of effectively independent trials and the variance across them. The remedy is to disclose
  the intermediate results the researcher discarded (abstract, confirmed through search).
- **López de Prado & Bailey (2021), the False Strategy Theorem.** Secondary summaries state that the best outcome of
  an unknown number of simulations is unbounded above. The exact statement was not read (UNVERIFIED). The practical
  reading: an unknown trial count cannot be treated as zero (rule R-8).
- **López de Prado (2020), *Machine Learning for Asset Managers*.** Chapter 8, "Testing Set Overfitting" (p. 105),
  and Appendix B, the proof of the False Strategy theorem (p. 128) (table of contents, confirmed through search).
- **Repo.** `n_clusters` uses average-linkage hierarchical clustering cut at ρ ≥ 0.5, not ONC
  (`gate_ledger.py:473-483`). `N_eff = max(N_clusters, N_equiv)`. The ledger prints `V_trials` only when
  `N_clusters ≥ 30` (`gate_ledger.py:789-790`); below that the hurdle uses the null standard error `SE_null`
  (`gate_ledger.py:588-592`, `:768`).

### 2.4 Haircuts for the number of tests (Harvey & Liu 2015; Harvey, Liu & Zhu 2016)

- **Harvey & Liu (2015), "Backtesting".** Convert the Sharpe ratio to a t-ratio, adjust its p-value for multiple
  tests (Bonferroni, Holm, BHY), convert back, and read the haircut. Search records state that the haircut depends on
  how many strategies were tested and on how correlated they were. The exact correlation adjustment was not re-read
  (UNVERIFIED).
- **Harvey, Liu & Zhu (2016).** A new factor needs a t-statistic above 3.0. Their method "accommodates correlation
  among the tests and missing data" (search record of the abstract), that is, tests that were run but not published.
- **Repo.** `gate_stats.harvey_liu_haircut(z, M)` is Bonferroni only, with an integer M, printed and never gated
  (`gate_stats.py:537-550`). BY q-values and Holm adjustments are printed beside step 3 (`gate_stats.py:494-529`;
  `gate_ledger.py:669-670`).
- **Record needed.** M (raw or effective) and each experiment's p-value. The "missing data" point maps to rule R-8.

### 2.5 Effective number of tests from correlated statistics (statistical genetics)

These methods turn a correlation matrix C of M test statistics into M_eff, then apply Bonferroni or Šidák with M_eff.

| Method | M_eff | Source status |
|---|---|---|
| Cheverud (2001); Nyholt (2004) | `1 + (M − 1)(1 − Var(λ)/M)`, λ the eigenvalues of C | formula as given in secondary sources found through search |
| Li & Ji (2005) | `Σ f(|λ_i|)`, `f(x) = 1[x ≥ 1] + (x − ⌊x⌋)`; they argue Cheverud's estimate is too large | abstract confirmed; formula from memory (UNVERIFIED) |
| Galwey (2009) | `(Σ √λ_i⁺)² / Σ λ_i⁺`, negative eigenvalues set to 0 | eigenvalue-ratio form confirmed through search; exact form from memory (UNVERIFIED) |
| Conneely & Boehnke (2007), P_ACT | no M_eff; adjusts the minimum p-value by multivariate-normal integration with the full C | abstract confirmed |

- **Contested.** Salyakina et al. (2005) evaluated Nyholt's procedure critically. Halle et al. (2016, arXiv
  1612.04535) argue that M_eff methods in general do not control the familywise error rate. The repo's `N_equiv` is
  closest in spirit to Conneely & Boehnke: it simulates the expected maximum under C (`gate_ledger.py:486-502`) and
  inverts the iid curve (`:546-557`). It targets exactly the quantity the DSR hurdle uses.
- **Forbidden form.** The repo forbids the Kish design-effect form in code and on cards
  (`gate_ledger.py:851-865`; `core/rules/macro_rules.py:367-372`). Note for readers: that form is bounded above by
  1/ρ̄, so it cannot grow with a growing search.

### 2.6 Bootstrap max tests: White (2000), Hansen (2005), Romano & Wolf (2005)

- **White's Reality Check.** Tests whether the best model of a specification search beats a benchmark, with a
  bootstrap of the maximum performance statistic over all models (Econometrica record, confirmed).
- **Hansen's SPA.** Studentises and recentres the statistic to improve power over the Reality Check (secondary
  sources; the exact abstract wording was not read, UNVERIFIED).
- **Romano & Wolf (2005), StepM.** A stepwise procedure that controls the familywise error rate and captures the
  joint dependence of the statistics (Econometrica record, confirmed).
- **Sullivan, Timmermann & White (1999).** Apply the Reality Check to the **full universe** of technical rules
  examined, extending earlier work's 26 rules (search records). The lesson for a registry: the universe must include
  every rule that was tried, including those from earlier studies.
- **Counting.** These tests need no N: the joint bootstrap absorbs correlation, and an exact duplicate does not change
  the maximum. They do need every experiment's loss series on a common sample.
- **Repo.** `tf_gov.spa_test` gives the lower, consistent and upper SPA p-values, the naive consistent p and White's
  RC p from one stationary bootstrap (`core/quant/tf_gov.py:257-291`). `family_gate` rejects a whole family when the
  consistent p > 0.05 (`tf_gov.py:313-333`). These are GOV-2 tech-fund amendments, not steps of the strategy gate
  that writes the stored cards.

### 2.7 The research process: file drawer, forking paths, pre-registration, holdout reuse

- **File drawer (Rosenthal 1979).** Unreported null results bias the visible record. Applied here: a run discarded
  after its results were seen must still count (R-2b).
- **Researcher degrees of freedom (Simmons, Nelson & Simonsohn 2011; Gelman & Loken 2013).** Flexible analysis
  choices made after seeing data raise false positives, even without conscious fishing. Applied here: a choice of
  data source, start date, bug fix or seed made after seeing results is a hidden search dimension (R-1b, R-5, R-6).
- **Pre-registration (Nosek et al. 2018).** Fixing the hypothesis and analysis before the data are seen separates
  confirmatory from exploratory work. Applied here: rule R-4. (Bibliographic record only; content not read.)
- **Reusable holdout (Dwork et al. 2015).** Each adaptive look at a holdout leaks information; naive reuse invalidates
  it. Applied here: one validation per pre-registration; several configurations validated on one holdout are a search
  over that holdout (R-4).
- **Backtesting protocol (Arnott, Harvey & Markowitz 2019).** A research protocol for backtests in finance. Secondary
  summaries say there is no true out-of-sample except live and fresh data, and that a model should not be tweaked on
  live results. Exact wording not read (UNVERIFIED).
- **Advances in Financial Machine Learning (López de Prado 2018), ch. 11.** Sections 11.5 "A Few General
  Recommendations" and 11.6 "Strategy Selection" were confirmed as headings. The often-quoted advice to record every
  backtest run on a dataset, so that PBO can be estimated and the Sharpe ratio deflated, could not be confirmed
  verbatim (UNVERIFIED).
- **Earlier QUANTGEN position.** The methodology note already states that "every parameter combination tried, every
  REVISE loop, every regime filter added after seeing results is a trial", and that PBO must use the whole trial
  matrix (`validation_methodology.md:148`; also `:229`, `:283`).

### 2.8 What each method needs: one table

| Method | Count it uses | How correlation enters | Exact duplicates change it? | Minimum per-experiment record | In QUANTGEN |
|---|---|---|---|---|---|
| DSR | N | through N (effective) and through V | N_raw: yes; V: yes | Sharpe on a common length; series for correlation | `validate.py:211-237` (N = G, V from current grid); `gate_ledger.py:748-813` (N_eff, SE_null) |
| PBO / CSCV | columns of the matrix | implicit (ranks of real series) | yes, when unequal (§4.4) | full daily P&L | `validate.py:240-265` (current grid); `gate_stats.py:651-724` |
| Clustered DSR (LdP & Lewis) | K clusters | clusters; V across cluster Sharpes | no, if clustering merges them | full daily returns | hierarchical, not ONC: `gate_ledger.py:473-483` |
| Harvey–Liu haircut | M | M (and, per the paper, average correlation) | yes | Sharpe t or p | Bonferroni only: `gate_stats.py:537-550` |
| M_eff (Nyholt, Li–Ji, Galwey) | M_eff | eigenvalues of C | yes (§4.2) | series for C | not implemented |
| E[max]-equivalent N | N_equiv | simulated E[max] under C | **no** (§4.2) | series for C | `gate_ledger.py:486-582` |
| White RC / Hansen SPA / StepM | none | joint bootstrap | **no** | loss series vs a benchmark | `tf_gov.py:257-291` |
| BH / BY / Holm | m p-values | BY is built for dependent tests (Benjamini & Yekutieli 2001); Holm holds under any dependence (Holm 1979) | yes | p-value | `gate_stats.py:494-529`; `tf_gov.py:294-310` |

---

## 3. What QUANTGEN implements today, and where it differs

| Item | What the code does | Where | Consequence for the registry |
|---|---|---|---|
| Strategy gate N | `n_trials` passed by the caller; Lab passes `len(grid)` | `validate.py:492-497`, `:507`; `ui/strategy_lab_page.py:127` | Today's verdict counts only the current run's grid |
| Strategy gate V | `np.nanstd` of the current grid's full-sample Sharpes; 0 for one column | `validate.py:505-506` | A one-configuration run cannot be deflated by any N (01 note, S_V4) |
| Integer N | `n = max(int(n_trials), 1)` | `validate.py:213` | A fractional N_eff in [1, 2) becomes 1 and the hurdle becomes 0 |
| Ledger key | `config_id` = md5 of rule, params and seven other fields; no span, code version or result | `gate_ledger.py:60-61`, `:168-171` | A logic change or data change with the same params is the same row |
| Re-run | A duplicate `config_id` appends nothing; the first row stands | `gate_ledger.py:14-15`, `:337-346` | The ledger counts configurations, not runs; TOTAL is not recoverable from it |
| Null runs | placebo, shift panel, GJR null, D4 panel: never rows | `gate_ledger.py:56-58`, `:200-201` | Matches R-7 |
| Revisions | A revision count is never N; a static guard enforces it | `gate_ledger.py:819-826`, `:864` | Revisions count through their configurations, never as a counter |
| N_eff | `max(N_clusters, N_equiv)`; linear N printed only | `gate_ledger.py:468-582`; `macro_rules.py:57` | Needs a difference series per row; Lab rows have none (02 note §0 item 6) |
| Selection factor | f = 1 if no row of the reading overlaps the card span with `run_utc < t_fix`; else N_eff; max over market-scoped and family-wide readings | `gate_ledger.py:674-733` | Encodes R-4's "untouched data" and "fixed first" tests |
| Results-seen rule | A manifest change after a card result was seen is a new package version, re-run on every card, flips disclosed | `gate_package.py:241-255` | Precedent for "after results" tests in R-2b and R-5 |
| Pooled route after results | refused | `macro_rules.py:355-358` | Same precedent |
| Forward records | "can demote, never validate" | `macro_rules.py:359-366` | A forward record is not an R-4 validation |
| Global N | Sum over all family ledgers; a k-of-n composite counts n^k | `tf_gov.py:336-375` | A repo convention, not a literature rule (R-9) |
| CRY-1 additions | Control, pre-registered split and ETH replication each add 1 to C3's N | `docs/techfund_study.py:83-85`, `:446`, `:458-467` | Conflicts with the f = 1 logic of `selection_factor` (R-4) |
| Contamination log | Families and spans the labs examined; "the historical holdout is used up and only prospective incubation is a clean test" | `tf_gov.py:487-523` | The registry's source for "touched" spans outside the ledger |
| Incubation | ≥ 252 sessions from the first recorded session, never back-filled | `tf_gov.py:527-553` | The only clean validation once a span is contaminated |
| Lab bootstrap | Lab runs use B = 1,000; the gate default is 2,000 | `ui/strategy_lab_page.py:86`, `:124-129`; `validate.py:54` | Lab verdicts are evaluation re-draws of the gate-of-record verdict (R-1b) |

---

## 4. Synthetic checks (illustrations, not a validation)

All matrices and returns are generated. Repo estimators are called through the frozen modules
(`gate_ledger.n_clusters`, `emax_sim`, `n_equiv`, `n_eff`; `validate.expected_max_sharpe`, `pbo_cscv`;
`gate_stats.psr`). Cheverud–Nyholt, Li–Ji and Galwey were computed in the script with the forms in §2.5.

### 4.1 The estimators disagree

Population correlation matrices; `E_sim` with the repo's 200,000 draws and seed 11.

| Case | N_raw | ρ̄ | BLdP linear | Cheverud–Nyholt | Li–Ji | Galwey | N_clusters | E_sim | N_equiv | N_eff |
|---|---|---|---|---|---|---|---|---|---|---|
| A: 10 independent | 10 | 0.00 | 10.00 | 10.00 | 10.00 | 10.00 | 10 | 1.540 | 9.35 | 10.00 |
| B: 8 on a flat plateau (ρ 0.95) | 8 | 0.95 | 1.35 | 1.68 | 2.00 | 2.34 | 1 | 0.317 | 1.45 | 1.45 |
| C: 12 = 3 blocks of 4 (within 0.9, between 0.3) | 12 | 0.46 | 6.90 | 8.85 | 5.00 | 5.99 | 3 | 1.007 | 3.74 | 3.74 |
| D1: 11 rows that are 5 distinct rules (C3-like) | 11 | 0.74 | 3.64 | 5.31 | 4.00 | 3.16 | 1 | 0.663 | 2.35 | 2.35 |
| D2: the same 5 rules only | 5 | 0.66 | 2.38 | 3.21 | 3.00 | 3.34 | 1 | 0.663 | 2.35 | 2.35 |
| E: 100 = 10 blocks of 10 (within 0.9, between 0.2) | 100 | 0.26 | 73.90 | 89.11 | 20.00 | 33.23 | 10 | 1.807 | 16.21 | 16.21 |

- D1 maps 11 rows to rules [1,1,2,2,3,3,1,2,3,4,5], with AR(0.8) correlation between distinct rules. This mirrors the
  C3 reading in the 01 note (§2.3: 11 counted trials, at most 5 distinct rules).
- Case A shows a small-N bias: `N_equiv` = 9.35 for 10 independent trials, because the closed form overstates the
  expected maximum at small N (closed form e(10) = 1.575; simulated 1.540). The `max` with `N_clusters` repairs it.
- The same correlation estimated from T = 2,500 synthetic draws through `gate_ledger.n_eff` gave N_eff 3.70 (case C)
  and 2.33 (case D1), close to the population values.

### 4.2 Duplicates

- `E_sim` and `N_equiv` are identical for D1 and D2. Duplicates do not move the expected maximum.
- N_raw (11 vs 5), the linear N (3.64 vs 2.38), Cheverud–Nyholt (5.31 vs 3.21) and Li–Ji (4 vs 3) all move.
- The repo's own acceptance target makes the same point: padding QF3's 26 trials with 80 near-duplicates (ρ 0.99)
  moves `N_equiv` by less than 0.5 (`spec_M7_gate_package.md:595`, T-NEFF-01; REFDATA absent, not run here).

### 4.3 Pairing N with the dispersion term

Share of synthetic zero-skill data sets in which the best of M trials reaches DSR ≥ 0.95. T = 1,260 daily
observations; 2,000 data sets (1,000 for E); Monte Carlo standard error about 0.005 near 0.05. DSR via
`gate_stats.psr(sr, T, sr0 = sd × emax_iid(N), skew, kurt)`. N_eff and the clusters come from the population matrix.

| Case | (a) N_raw + raw dispersion | (b) N_eff + raw dispersion | (c) K clusters + dispersion of cluster Sharpes | (d) N_eff + null SE | (e) N_raw + null SE |
|---|---|---|---|---|---|
| A: 10 independent | 0.003 | 0.003 | 0.003 | 0.009 | 0.009 |
| B: 8 plateau | 0.051 | **0.075** | **0.083** | 0.050 | 0.004 |
| C: 12 in 3 blocks | 0.010 | **0.050** | **0.078** | 0.031 | 0.002 |
| E: 100 in 10 blocks | 0.000 | 0.010 | 0.032 | 0.008 | 0.001 |

- (a) is today's `validate` convention when N = G (`validate.py:505-507`).
- (b) mixes a correlation-reduced N with the raw dispersion of correlated trials. It raises the false pass rate in
  every correlated case.
- (c) is a **simplified** clustered DSR: equal-weight cluster returns and the repo's hierarchical cut, not ONC. It is
  not a test of López de Prado & Lewis's procedure. It shows that the cluster construction matters.
- (d) is the `gate_ledger.step3` pairing (hurdle `SE_null × e(N_eff)`, `gate_ledger.py:588-592`, `:768`).
- DSR ≥ 0.95 compares the observed Sharpe with an expected maximum, not with a quantile of the maximum, so rates far
  below 0.05 are expected for independent trials. The comparison across columns is the point.

### 4.4 PBO and duplicates

200 synthetic sets of 8 zero-skill configurations (T = 1,500, S = 8, `validate.pbo_cscv`):

| Matrix | Mean PBO (sd) |
|---|---|
| 8 distinct columns | 0.508 (0.240) |
| every column duplicated once (16 columns) | 0.508 (0.240) |
| one column repeated 3 extra times (11 columns) | **0.458** (0.227) |

Unequal duplication biases PBO down, toward "not overfit". Semantic duplicates must be collapsed before CSCV.

### 4.5 Integer truncation

`e(N)` per unit of dispersion: `validate.expected_max_sharpe` gives N = 1: 0.000, 2: 0.520, 3: 0.853, 5: 1.193, 8:
1.459, 11: 1.622, 12: 1.665, 20: 1.901, 100: 2.531, 1000: 3.255. `gate_ledger.emax_iid` accepts a real N: 1.5:
0.344, 1.9: 0.526, 2.0: 0.520 (the documented drop at 2, `gate_ledger.py:519-527`). For case B, passing N_eff = 1.45
to `validate.deflated_sharpe` gives a hurdle of 0; the real-N value is 0.317. For case C, 0.853 instead of 1.007.

**Limits of §4.** Gaussian returns, block correlation, one seed per case, no walk-forward. These checks illustrate
mechanisms. They do not validate a criterion. The owner reserved that validation for a separate step.

---

## 5. Rule set

**Principle.** Every run adds 1 to TOTAL. A run adds to N_raw only for configurations that (i) produced a
performance statistic that was or could have been seen, (ii) are not already counted in the scope, and (iii) are not
a pre-registered validation. N_eff is then computed over N_raw's return series. **The default is to count.** An
exclusion needs a reason the registry can check from stored fields, or a recorded human reason (who, when, why). This
mirrors the ledger's fail-closed reading (`gate_ledger.py:311-316`).

**Status labels.** *Supported*: follows from the cited method or from the mathematics. *Reasoned*: an inference from
the cited literature, not stated there. *Contested*: sources or repo conventions disagree.

### R-1. Identical re-run

- **Rule.** Same configuration, same code version, same data snapshot hash, same cost condition, same gate version,
  same seed and B. TOTAL +1. N_raw +0. Status `RERUN`.
- **Check.** The result fingerprint must equal the earlier run's. If it differs, flag `NONDETERMINISTIC` (a defect to
  fix). It still adds nothing to N_raw.
- **Why.** An exact duplicate does not change the maximum of a set, so it cannot change the selection (§4.2). The
  ledger and the trial registry read it the same way (`gate_ledger.py:14-15`; `tf_gov.py:351-352`).
- **Status.** Supported. Caveat: count-based estimators are not duplicate-invariant, so the dedup must happen before
  counting (§4.2, §4.4).

### R-1b. Evaluation re-draw (only the seed or B differs)

- **Rule.** TOTAL +1. N_raw +0. Status `EVAL_REDRAW`. The verdict of record is the one at the pre-registered seed and B
  (GATE `bootstrap_B` 2,000, `validate.py:54`; study seed 11).
- **Check.** If verdicts differ across re-draws, flag "verdict unstable under resampling". The repo has a helper for
  near-threshold classes (`gate_stats.py:741-747`).
- **Why.** The strategy is unchanged, so no new hypothesis is tested. Choosing among re-draws would be a selection on
  outcome (Simmons et al. 2011; Gelman & Loken 2013).
- **Status.** Reasoned. Lab runs at B = 1,000 (`ui/strategy_lab_page.py:86`) fall here.

### R-2. Failed runs

- **R-2a. Failed before any performance statistic existed.** Examples: a fetch error, wrong symbol count, too few
  sessions, no cost row, an exception before the P&L matrix. TOTAL +1. N_raw +0. Status `FAILED_PRE_RESULT`.
  - Why: no outcome existed, so nothing could be selected on. DSR's N counts trials whose Sharpe enters the maximum
    (§2.1); CSCV needs their P&L columns (§2.2).
  - Status: supported.
- **R-2b. Failed, aborted or discarded after a statistic was produced.** Examples: an exception in scoring after the
  walk-forward ran, a cancel after IS Sharpes were shown, a run deleted because it looked bad. TOTAL +1. N_raw +1 per
  configuration with a statistic. Status `FAILED_POST_RESULT` or `ABANDONED`.
  - Why: this is the file-drawer case (Rosenthal 1979). López de Prado (2019) asks for the discarded intermediate
    results to be disclosed. Bailey et al. (2014, Notices AMS) note that configuration counts are rarely reported.
  - Check: the registry records the last pipeline stage reached. In the Lab the walk-forward runs before rows are
    registered and before scoring (`ui/strategy_lab_page.py:116-118`, `:127`). If the registry cannot show that no
    statistic was produced, it counts the run (fail closed).
  - Status: supported in direction; the stage cut-off is reasoned.
- **R-2c. Not failures.** INSUFFICIENT_DATA and a withheld verdict (cost sensitivity, `ui/strategy_lab_page.py:92-103`)
  are completed runs with visible statistics. They count under R-3.

### R-3. Parameter search

- **R-3a. Each distinct configuration evaluated is one raw experiment.** This includes every grid point, every point
  of a revised grid, every universe tried in search mode, every cost variant and every lag, estimator, book or band
  variant (spec: "every variant run is a row", `spec_M7_gate_package.md:78`). Earlier configurations stay counted
  after a grid revision. Status: supported (BLdP 2014; BBLZ 2017; Harvey & Liu 2015; López de Prado 2019).
- **R-3b. Semantic duplicates collapse.** Two configurations with equal result fingerprints are one tested rule,
  whatever their parameter literals (C3: 11 rows, at most 5 rules; 01 note §2.3). The registry links them. It prints
  N_raw under both readings, literal and distinct-rule. Status: supported for exact equality; a tolerance for "near"
  equality is contested and should be left to the correlation step.
- **R-3c. Correlation reduces the effective count.** N_eff is computed from the experiments' return or difference
  series. The repo rule is `max(N_clusters, N_equiv)` (`gate_ledger.py:574-582`), and other rules are refused
  (`macro_rules.py:367-369`). Status: the direction is supported (BLdP 2014; López de Prado & Lewis 2019; Harvey,
  Liu & Zhu 2016); the estimator is **contested** (§2.5, §4.1).
- **R-3d. Pair N with a matching dispersion term.** Use (N_raw, raw dispersion) or (N_eff, null standard error), or a
  consistently built cluster pair. Do not use (N_eff, raw dispersion). Status: reasoned from the DSR formula; the
  synthetic evidence is in §4.3; a formal check is the owner's separate validation.
- **R-3e. Scope.** Count under the market-scoped and the family-wide readings, and let the larger bind, as the
  ledger does (`gate_ledger.py:679-686`, `:708-709`). Status: repo convention.
- **Open within R-3.** When the reported series is a walk-forward OOS concatenation, today's code charges the whole
  grid as N (`validate.py:507`, `ui/strategy_lab_page.py:127`). Whether the grid or the walk-forward procedure is the
  "trial" is not settled in the cited literature. This note does not propose a change.

### R-4. Independent validation of a pre-registered configuration

- **Rule.** TOTAL +1. N_raw +0. N_validation +1. Status `VALIDATION`. All four conditions must hold:
  1. The configuration key and the pass rule (verdict criteria, seed, B) were recorded with an anchored timestamp
     before the run (repo: `t_fix`, anchored instants only, `gate_ledger.py:114-119`, `:688-697`).
  2. No family run touched the validation span before that timestamp, under the family-wide reading
     (`gate_ledger.py:674-676`, `:708-718`), and the span is not in the contamination log (`tf_gov.py:517-520`).
  3. It is the first evaluation of that configuration on that span.
  4. The result is recorded whatever it is.
- **No re-tuning.** Any change after the validation result is seen creates a new search experiment (R-3). The
  validation span then counts as touched for the family. The first result stays on record with status
  `VALIDATION_SPENT`. Only prospective incubation is clean after that (`tf_gov.py:487-489`, `:527-553`).
- **Several configurations on one holdout.** If more than one configuration is validated on the same span and the best
  is kept, the validations form a search over the holdout and count as experiments of a validation scope (Dwork et
  al. 2015).
- **Concurrent cross-market data is not new data.** BTC-USD and KRW-BTC on the same dates overlap under the
  family-wide reading, so the repo's selection factor does not give f = 1 there (`gate_ledger.py:708-722`,
  combined by max at `:679-686`).
- **Forward records.** A forward-simulation record cannot be cited as validation (`macro_rules.py:359-366`).
- **Why.** A pre-registered single test on untouched data involves no selection on that data (Nosek et al. 2018;
  Dwork et al. 2015). The repo's own f = 1 route encodes it (`gate_ledger.py:719-722`).
- **Status.** Contested inside the repo: CRY-1 counts a pre-registered split and an ETH replication as +1 trial each
  (`docs/techfund_study.py:83-85`, `:446`, `:503`). Print both readings in the parallel computation.

### R-5. Code changes

- **R-5a. Non-functional** (refactor, logging, UI): the result fingerprint is unchanged. Treat as R-1. Status:
  supported.
- **R-5b. Strategy logic** (signal formula, sizing, entry or exit, a new parameter): a new configuration, so R-3.
  The experiment key must carry a strategy-code hash, because `config_id` does not (`gate_ledger.py:60-61`).
  Status: supported.
- **R-5c. Bug fix that changes results** (accounting, cost model, a look-ahead fix). The hypothesis is the same; the
  measurement was wrong. The old run becomes `SUPERSEDED` and stays in TOTAL. The corrected run is the same
  experiment **only if** the fix is checkable on its own (for example, a test that shows the look-ahead) and is
  applied to every configuration of the family, not only to the ones that looked bad. Otherwise count it as a new
  experiment. Status: contested; reasoned from the forking-paths literature; the repo's `results_seen` test for
  package changes is the closest precedent (`gate_package.py:248-255`).
- **R-5d. Gate or statistics change** (a harness source, a GATE constant): not a strategy trial. Record a new gate
  version. Report verdict changes caused by the gate separately from changes caused by the trial count. Repo rule: a
  change after results were seen is a new package version re-run on every card with flips disclosed
  (`gate_package.py:241-255`); adoption is one counted revision, never N (`gate_ledger.py:829-845`). The stored cards
  already predate the current gate text (01 note §2.2). Status: supported by repo rule.

### R-6. Data changes

- **R-6a. Same source, span extended.** Same configuration. N_raw +0. The new segment is a validation (R-4) only if
  the configuration was fixed before that segment existed. Repo: span is not part of `config_id`
  (`gate_ledger.py:60-61`); overlap drives the selection factor (`:700-733`). Status: supported.
- **R-6b. Vendor revision of the same span** (snapshot hash changed): a re-measurement. N_raw +0. Store both hashes.
  Flag "data-fragile" if the verdict flips. Status: reasoned.
- **R-6c. A choice among sources, start dates or cash conventions after seeing results:** that dimension was
  searched. Each alternative evaluated is an experiment. The ledger key already has `start_convention`
  (`gate_ledger.py:60-61`). The Lab and the study differ in cash rate and start window, so a Lab run and a card are
  different configurations even with equal parameters (01 note §3.4). Status: reasoned (Gelman & Loken 2013).
- **R-6d. A different universe:** a different configuration, because symbols are in `params`
  (`ui/strategy_lab_page.py:68-76`). Search mode: R-3. Pre-registered on untouched data: R-4.

### R-7. Runs that are never experiments

Null-distribution runs (`gate_ledger.py:56-58`, `:200-201`) and synthetic-data runs (`ui/strategy_lab_page.py:60-61`).
TOTAL +1 only. Status: repo convention; consistent with the methods, which count trials on real data.

### R-8. Trials made before the registry existed

Back-fill them with provenance (`RECONSTRUCTED`, source, who), never as zero. C3's typed N = 11 with a free-text
history (`docs/asset_expansion_study.py:339-343`) is such a back-fill. The owner's ledgers under
`~/.nextgen/macro/ledgers` are not in this sandbox (UNVERIFIED contents). Why: an unknown number of trials cannot be
deflated (False Strategy Theorem, as summarised; Harvey, Liu & Zhu 2016 model unpublished tests). Status: reasoned.

### R-9. Revisions and composites

- A revision counter is never N (`gate_ledger.py:819-826`, `:864`). Revised configurations count through R-3.
  Status: supported.
- A k-of-n composite counts n^k (`tf_gov.py:336-347`). This counts the search space, not the configurations
  evaluated. Status: repo convention; contested as an N for DSR.

### Counting table

| Run class | TOTAL | N_raw | Enters N_eff | N_validation | Rule |
|---|---|---|---|---|---|
| `RERUN` (identical) | +1 | 0 | no | 0 | R-1 |
| `EVAL_REDRAW` (seed or B) | +1 | 0 | no | 0 | R-1b |
| `NONDETERMINISTIC` (same context, different result) | +1 | 0 | no | 0 | R-1, flagged |
| `FAILED_PRE_RESULT` | +1 | 0 | no | 0 | R-2a |
| `FAILED_POST_RESULT` / `ABANDONED` | +1 | +1 per configuration with a statistic | yes | 0 | R-2b |
| `SEARCH` (new configuration, incl. cost, universe, logic, revised grid) | +1 | +1 per new configuration | yes | 0 | R-3, R-5b, R-6c, R-6d |
| `SEMANTIC_DUPLICATE` | +1 | 0 (distinct-rule reading) / +1 (literal reading) | linked series | 0 | R-3b |
| `REMEASURE` (data extension or vendor revision, same configuration) | +1 | 0 | updates its series | 0 | R-6a, R-6b |
| `SUPERSEDED` → corrected run | +1 | 0 if R-5c holds, else +1 | yes | 0 | R-5c |
| `VALIDATION` | +1 | 0 | no | +1 | R-4 |
| `VALIDATION_SPENT` → re-tuned run | +1 | +1 | yes | 0 | R-4 |
| `NULL_OR_SYNTHETIC` | +1 | 0 | no | 0 | R-7 |
| `RECONSTRUCTED` | 0 (not a run here) | +k as recorded | if series exist | 0 | R-8 |

### Classification order for one run

1. Synthetic data or a null-distribution generator? → `NULL_OR_SYNTHETIC`.
2. No performance statistic produced? → `FAILED_PRE_RESULT`.
3. For each configuration: compute the experiment key (ledger key + strategy-code hash) and the result fingerprint.
4. Pre-registered, untouched span, first evaluation? → `VALIDATION`.
5. Same key and identical evaluation context? → `RERUN` (or `EVAL_REDRAW` if only seed or B differ;
   `NONDETERMINISTIC` if the fingerprint differs).
6. Fingerprint equal to an existing experiment's? → `SEMANTIC_DUPLICATE`.
7. Same key, context differs only in data snapshot or span? → `REMEASURE`.
8. Otherwise → `SEARCH`. If the run then fails or is abandoned → `FAILED_POST_RESULT` / `ABANDONED`.

---

## 6. Contested points

1. **Which N_eff estimator.** On the same matrix the candidates range from 10 to 89 (§4.1, case E). Effective-number
   methods do not in general control the familywise error (Halle et al. 2016; Salyakina et al. 2005). The repo's
   E[max]-equivalent route is the only one in §4 that is duplicate-invariant.
2. **Which dispersion term to pair with N_eff** (§4.3). The simplified cluster pairing had the highest false pass
   rate here. The repo's `SE_null` pairing had the lowest among the correlation-adjusted options.
3. **May the ledger basis lower N below the grid size?** It loosens the S_S6_pairs_hyundai_kia predicate at N = 1
   (01 note §6). Under integer truncation any N_eff below 2 does that.
4. **Is a pre-registered replication a trial?** The repo answers both ways (R-4).
5. **Bug fixes and data-source switches** (R-5c, R-6c): whether they are new experiments depends on timing relative to
   results, which needs a recorded reason.
6. **Composite n^k** as an N (R-9).
7. **What the trial is under walk-forward** (R-3, open point).
8. **Near-duplicate tolerance** for R-3b.

---

## 7. What this means for the R3 parallel computation

No verdict criterion and no GATE constant changes in this stage. The following can be printed beside each existing
verdict without editing a frozen file:

1. The existing verdict, recomputed exactly as today (N as stored, `validate.score_strategy`).
2. TOTAL, N_raw (literal and distinct-rule readings), N_eff and N_validation for the card's scope.
3. DSR at (N_raw, raw dispersion) and at (N_eff, null SE). Compute the hurdle with `gate_ledger.emax_iid` and the
   probability with `gate_stats.psr(sr0=...)` to avoid the integer truncation at `validate.py:213`.
4. The decision that would follow, labelled hypothetical, with a reason code (which predicate moved, which run class
   moved the count).
5. A separate line for verdict changes caused by gate-version differences (R-5d), so that they are not read as
   trial-count effects.

Cards most exposed, from the 01 note §6: S_E8_pairs_kodex_tiger (REVISE → REJECT near N ≈ 769), S_E2_voltarget_kodex200
and S_E5_xsmom_sectors (reason text only), and S_S6_pairs_hyundai_kia (REJECT → REVISE only if N falls to 1).

---

## 8. Open questions for the owner

1. Which N_raw reading is the count of record: literal `config_id` or distinct rule (R-3b)?
2. Which pairing of N and dispersion should the parallel computation treat as primary (R-3d)?
3. May a correlation-adjusted N fall below the grid size (contested point 3)?
4. Should pre-registered replications count as trials (R-4 vs CRY-1)?
5. Who may record an R-5c "same experiment" reason, and where is it stored?
6. Should Lab runs at B = 1,000 carry a verdict, or only an `EVAL_REDRAW` label next to the gate-of-record verdict?

---

## References

### Repository (read on 2026-10-27; working tree not modified)

- `core/quant/validate.py`: GATE `:53-74` (PBO note `:59-67`); `expected_max_sharpe` `:211-217`; `deflated_sharpe`
  `:220-237`; `pbo_cscv` `:240-265`; `score_strategy` `:492-533`.
- `core/quant/gate_ledger.py`: readings `:10-24`; `ROW_SET_KEY` `:60-61`; anchors `:114-131`; `config_id` `:168-171`;
  `append` `:337-355`; linear N `:468-470`; clusters `:473-483`; E[max] and `n_equiv` `:486-557`; `n_eff` `:574-582`;
  `deflated_dsr` `:588-592`; `step3_lines` `:649-671`; overlap and readings `:674-686`; `t_fix` `:688-697`;
  `selection_factor` `:700-733`; `step3` `:748-813`; revisions `:819-845`; forbidden patterns `:851-888`.
- `core/quant/gate_stats.py`: BY and Holm `:494-529`; Harvey–Liu `:537-550`; `psr` `:590-607`; `dsr_vs_zero`
  `:610-617`; `pbo_on_claim` `:651-724`; `verdict_class` `:741-747`.
- `core/quant/tf_gov.py`: GOV-2 constants `:58-62`; `spa_test` `:257-291`; `bh_fdr` `:294-310`; `family_gate`
  `:313-333`; composites and `TrialRegistry` `:336-379`; `ContaminationLog` `:487-523`; `incubation` `:527-553`.
- `core/quant/gate_package.py`: frozen sources `:36-38`; `new_package_version`, `version_for_change` `:241-255`.
- `core/rules/macro_rules.py`: `N_GATE` `:57`; after-results and forward-record refusals `:355-366`; N rule `:367-372`.
- `ui/strategy_lab_page.py`: `register_trials` `:55-82`; `run_family` `:85-136`; ledger chip `:254-256`.
- `docs/techfund_study.py`: `EXTRA_TRIALS` `:83-85`; `run_cry1` `:440-510`.
- `docs/asset_expansion_study.py:339-343` (C3 typed N and history).
- `research_notes/QUANTGEN v2 integration map/spec_M7_gate_package.md:78`, `:83-127`, `:595`.
- `research_notes/QUANTGEN asset coverage expansion/validation_methodology.md:113-120`, `:148`, `:229`, `:283`.
- `research_notes/QUANTGEN run registry map/01_strategy_lab_and_cards.md`, `02_gate_ledger_semantics.md`.

### Literature

"Confirmed" means the bibliographic data were matched in a search record this session. Content claims not confirmed
are marked in the text.

- Arnott, R., Harvey, C. R., & Markowitz, H. (2019). A backtesting protocol in the era of machine learning. *Journal
  of Financial Data Science* 1(1), 64–74. https://doi.org/10.3905/jfds.2019.1.064 (confirmed).
- Benjamini, Y., & Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under
  dependency. *Annals of Statistics* 29(4), 1165–1188 (from memory, not searched this session: UNVERIFIED).
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). Pseudo-mathematics and financial
  charlatanism: The effects of backtest overfitting on out-of-sample performance. *Notices of the AMS* 61(5),
  458–471 (confirmed; DOI 10.1090/noti1105 from memory, UNVERIFIED).
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). The probability of backtest overfitting.
  *Journal of Computational Finance* 20(4), 39–69. https://doi.org/10.21314/JCF.2016.322 (confirmed).
- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest
  overfitting, and non-normality. *Journal of Portfolio Management* 40(5), 94–107.
  https://doi.org/10.3905/jpm.2014.40.5.094 (confirmed).
- Cheverud, J. M. (2001). A simple correction for multiple comparisons in interval mapping genome scans. *Heredity*
  87(1), 52–58 (confirmed; DOI 10.1046/j.1365-2540.2001.00901.x from memory, UNVERIFIED).
- Conneely, K. N., & Boehnke, M. (2007). So many correlated tests, so little time! Rapid adjustment of P values for
  multiple correlated tests. *American Journal of Human Genetics* 81(6), 1158–1168.
  https://doi.org/10.1086/522036 (confirmed).
- Dwork, C., Feldman, V., Hardt, M., Pitassi, T., Reingold, O., & Roth, A. (2015). The reusable holdout: Preserving
  validity in adaptive data analysis. *Science* 349(6248), 636–638. https://doi.org/10.1126/science.aaa9375
  (confirmed).
- Galwey, N. W. (2009). A new measure of the effective number of tests, a practical tool for comparing families of
  non-independent significance tests. *Genetic Epidemiology* 33(7), 559–568 (confirmed; DOI 10.1002/gepi.20408 from
  memory, UNVERIFIED).
- Gelman, A., & Loken, E. (2013). The garden of forking paths: Why multiple comparisons can be a problem, even when
  there is no "fishing expedition" or "p-hacking" and the research hypothesis was posited ahead of time. Working
  paper, Columbia University (title confirmed). The *American Scientist* 102(6) version (2014) is UNVERIFIED.
- Halle, K. K., Djurovic, S., Andreassen, O. A., & Langaas, M. (2016). Is the familywise error rate in genomics
  controlled by methods based on the effective number of independent tests? arXiv:1612.04535 (confirmed).
- Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics* 23(4),
  365–380 (confirmed; DOI 10.1198/073500105000000063 from memory, UNVERIFIED).
- Harvey, C. R., & Liu, Y. (2015). Backtesting. *Journal of Portfolio Management* 42(1), 13–28.
  https://doi.org/10.3905/jpm.2015.42.1.013 (confirmed; one secondary record lists the volume as 41(1)).
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). … and the cross-section of expected returns. *Review of Financial Studies*
  29(1), 5–68. https://doi.org/10.1093/rfs/hhv059 (confirmed).
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*
  6(2), 65–70 (from memory, not searched this session: UNVERIFIED).
- Li, J., & Ji, L. (2005). Adjusting multiple testing in multilocus analyses using the eigenvalues of a correlation
  matrix. *Heredity* 95(3), 221–227. https://doi.org/10.1038/sj.hdy.6800717 (confirmed via the publisher record).
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. ISBN 978-1-119-48208-6 (chapter 11
  headings confirmed).
- López de Prado, M. (2019). A data science solution to the multiple-testing crisis in financial research. *Journal
  of Financial Data Science* 1(1), 99–110. https://doi.org/10.3905/jfds.2019.1.099 (confirmed).
- López de Prado, M. (2020). *Machine Learning for Asset Managers*. Cambridge University Press (Elements in
  Quantitative Finance). https://doi.org/10.1017/9781108883658 (confirmed).
- López de Prado, M., & Bailey, D. H. (2021). The false strategy theorem: A financial application of experimental
  mathematics. *American Mathematical Monthly* 128(9). https://doi.org/10.1080/00029890.2021.1965068 (confirmed via
  the eScholarship record; pages UNVERIFIED).
- López de Prado, M., & Lewis, M. J. (2019). Detection of false investment strategies using unsupervised learning
  methods. *Quantitative Finance* 19(9), 1555–1565 (confirmed; DOI 10.1080/14697688.2019.1622311 from memory,
  UNVERIFIED).
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. *PNAS*
  115(11), 2600–2606. https://doi.org/10.1073/pnas.1708274114 (confirmed; author list beyond Nosek from memory,
  UNVERIFIED).
- Nyholt, D. R. (2004). A simple correction for multiple testing for single-nucleotide polymorphisms in linkage
  disequilibrium with each other. *American Journal of Human Genetics* 74(4), 765–769.
  https://doi.org/10.1086/383251 (confirmed).
- Romano, J. P., & Wolf, M. (2005). Stepwise multiple testing as formalized data snooping. *Econometrica* 73(4),
  1237–1282. https://doi.org/10.1111/j.1468-0262.2005.00615.x (confirmed).
- Rosenthal, R. (1979). The file drawer problem and tolerance for null results. *Psychological Bulletin* 86(3),
  638–641. https://doi.org/10.1037/0033-2909.86.3.638 (confirmed).
- Salyakina, D., Seaman, S. R., Browning, B. L., Dudbridge, F., & Müller-Myhsok, B. (2005). Evaluation of Nyholt's
  procedure for multiple testing correction. *Human Heredity* 60(1), 19–25 (confirmed; findings not read, UNVERIFIED).
- Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: Undisclosed flexibility in data
  collection and analysis allows presenting anything as significant. *Psychological Science* 22(11), 1359–1366.
  https://doi.org/10.1177/0956797611417632 (confirmed).
- Sullivan, R., Timmermann, A., & White, H. (1999). Data-snooping, technical trading rule performance, and the
  bootstrap. *Journal of Finance* 54(5), 1647–1691 (confirmed; DOI 10.1111/0022-1082.00163 from memory, UNVERIFIED).
- White, H. (2000). A reality check for data snooping. *Econometrica* 68(5), 1097–1126.
  https://doi.org/10.1111/1468-0262.00152 (confirmed).
