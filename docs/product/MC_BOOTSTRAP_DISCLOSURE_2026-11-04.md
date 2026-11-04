# Monte Carlo block bootstrap: say what the scheme is (§10 N-M1-02/a)

This is part (a) of §10 N-M1-02, done on product main `a32106b`. It went through
two steps:

- an analyst reproduced the finding;
- a separate reviewer tried to refute the reproduction and the proposed fix.

The text below includes the reviewer's corrections. **It changes disclosure only.**
The engine functions, the random draws, the convexity correction and every number
are unchanged. Part (b), the clustering limit itself, is disclosed here, but fixing it
is a maths change and stays open for the owner.

## Which limitation the ID names

N-M1-02 has no audit row. The model-limits register (`MODEL_LIMITS_REGISTER_2026-10-28.md`
on research commit `2da6469`) names it only in the "related errors" cell of model 9,
"M1-09 블록 부트스트랩 경로 모형":

> ARCHITECTURE_REVIEW C1(=N-M1-02, 감사 행 없음), D12-01, D12-02

The register lists four limitations for model 9. By elimination:

| Limitation | ID | In N-M1-02? |
| --- | --- | --- |
| L1. Every daily shock is one of the window's demeaned returns, so nothing beyond the demeaned sample's range is drawn. | none (inherent to resampling) | no |
| L2. Clustering longer than 5 sessions is cut, and the fan ignores the current vol level. | C1 | yes, C1(b) |
| L3. The docstring and primer 3.5 say "stationary block bootstrap"; the code uses fixed, circular blocks. | C1 | yes, C1(a) |
| L4. Contaminated input (duplicates, inf) is resampled as it is. | D12-01, D12-02 | no |

So N-M1-02 = ARCHITECTURE_REVIEW C1 = L3 + L2. C1's own text
(`docs/ARCHITECTURE_REVIEW.md:277`, `:585-594`) has two parts:

- (a) "Name it what it is";
- (b) "block length 5 truncates clustering the primer measures out to lag 20".

This change closes (a). For (b) it discloses the limit and changes no numbers.
Record it as **N-M1-02/a**, not as N-M1-02.

## What the code does

- `_simulate_bootstrap(rng, r, n_paths, horizon, block=5)` draws `ceil(H/5)` block
  starts per path, uniformly over the whole window. It takes five consecutive
  demeaned returns from each start, wraps from the sample end to its start, and cuts
  the path to H.
- `_bootstrap_correction(r, horizon, block=5)` is the exact block log-MGF increment.
  It assumes this fixed 5-step alignment.
- `run_monte_carlo` passes no block length.

This is a circular block bootstrap with fixed blocks of 5. It is not a stationary
bootstrap, which draws geometric (random) block lengths.

## Reproduction (analyst and reviewer probes, synthetic data)

**Block structure.** The sample was the indices 0..503, with 2,000 paths × 126 steps.
- Run-length histogram: {5: 49,797, 1: 1,997, 10: 100, 6: 3}. The 1s are the cut
  final block (126 = 25 × 5 + 1). The 10s and 6s are adjacent starts that happen to
  line up.
- New blocks start only at multiples of 5.
- 388 wrap joins (503 → 0) fall inside blocks.
- A stationary bootstrap with mean block 5 would give P(L = 5) = 0.082 and
  P(L = 1) = 0.200.

**Clustering.** The data were GARCH(1,1)-t6 synthetic series, and the measure is the
in-path autocorrelation of squared returns.
- Inside a path, lag k keeps (5-k)/5 of the sample's circular autocorrelation for
  k < 5 over a long horizon, and nothing from lag 5 at any horizon.
- On a short horizon the share is higher. A path of H sessions has
  floor(H/5)·(5-k) + max(0, (H mod 5) - k) same-block pairs out of H - k at lag k. That
  is never below (5-k)/5, equals 1 at H = 5 (one block), and is 0.889, 0.750, 0.571
  and 0.333 at H = 10. On this change's fixture (below; 20,000 paths, seed 11) the
  measured ratios were 1.046, 1.000, 0.948, 0.950 at H = 5, 0.926, 0.768, 0.562, 0.308
  at H = 10, 0.857, 0.658, 0.456, 0.247 at H = 20 and 0.792, 0.605, 0.403, 0.208 at
  H = 126. That is why the text says "over a horizon well beyond 5 sessions (more over
  a shorter one)".
- Reviewer, 20 seeds: paths/sample ratios 0.80, 0.61, 0.39, 0.20 at lags 1-4, and 0.01
  at lags 5, 10 and 20. The largest gap to the (5-k)/5 law was 0.0073.
- Analyst, 40 seeds: largest gap 0.0087.
- A stationary bootstrap with mean block 5 would keep 0.8^k (lag 5: 0.032 against a
  sample 0.097), so renaming the scheme alone does not fix L2.

**Current vol level.** The same 504 returns were reordered to end calm or hot.
- The bootstrap's 90% band at step 21 was 17.81% (calm end) and 17.29% (hot end).
- GARCH-t on the same data gave 15.85% and 58.23%.
- The reviewer did not re-run these numbers. That the fan ignores the current level
  follows from the code: block starts are uniform over the whole window.

**Existing partial disclosure.** Under the default drift `premium`, and under `rf`,
the drift note already reads "(the empirical block log-MGF of the demeaned sample)".
The block length, fixed versus random lengths, the circular wrap and both limits
were shown nowhere.

**A sentence that was dropped.** The first draft said "No daily move outside the
sample's range is drawn". That is false for two reasons. Each shock is a demeaned
return r - mean(r), so on a sample with a non-zero mean one tail of the shocks already
reaches past the raw returns' range even with zero drift, when nothing is added. In the
other drift modes the drift is added on top as well.
- Premium drift on a negative-mean sample: sample max +0.04979, drawn max +0.05153.
- Zero drift on a positive-mean sample: sample min −0.05183, drawn min −0.05348. Here
  the drawn move is the demeaned shock itself.
- Re-run for this note (zero drift, 300 sessions, 2,000 × 60, seed 3): on a sample with
  mean +0.00210 the raw returns span [−0.02148, +0.03024] and the drawn moves
  [−0.02358, +0.02814], with 1,186 of 120,000 drawn days below the raw minimum; on a
  sample with mean −0.00290, 804 of 120,000 lie above the raw maximum.

The shipped text says instead that each shock is one of the sample's demeaned returns,
with the drift added on top. The primer's "it can never draw a move larger than any the
window contains" is replaced the same way (see the surface table).

**This change's test fixture.** GARCH-t seed 1034, 504 sessions; the product's
`run_monte_carlo`, 4,000 × 125, seed 11.

| Lag | 1 | 2 | 3 | 4 | 5 | 10 | 20 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sample r² autocorrelation | 0.201 | 0.158 | 0.220 | 0.220 | 0.310 | 0.199 | 0.057 |
| In-path / circular | 0.811 | 0.600 | 0.406 | 0.209 | 0.007 | −0.001 | −0.029 |

## The text

EN (`BOOTSTRAP_TEXT`):

> Block bootstrap: circular, fixed 5-session blocks of the demeaned daily log returns
> in the fit window, wrapping at the sample end (not a stationary bootstrap with
> random block lengths). Blocks are drawn independently from anywhere in the window,
> so volatility clustering is kept only within a block: at lags 1-4, lag k keeps about
> (5-k)/5 of the sample's over a horizon well beyond 5 sessions (more over a shorter
> one), and none is kept from lag 5. The fan does not start from the current
> volatility level. Each day's shock is one of the sample's demeaned daily returns,
> with the drift added on top.

KO (`BOOTSTRAP_TEXT_KO`):

> 블록 부트스트랩: 추정 구간의 일별 로그수익률에서 평균을 뺀 값을 5거래일 고정
> 길이 블록 단위로 다시 뽑으며, 표본 끝에 닿으면 처음으로 이어 붙이는 원형
> 방식입니다(블록 길이가 무작위인 정상(stationary) 부트스트랩이 아닙니다).
> 블록은 구간 어디에서나 서로 독립적으로 뽑으므로 변동성 군집은 한 블록 안에서만
> 유지됩니다. 시차 1-4에서는 분석 기간이 5거래일보다 충분히 길 때 시차 k에
> 표본의 약 (5-k)/5가 남고(기간이 짧으면 더 많이 남음), 시차 5부터는 전혀
> 남지 않습니다. 팬 차트는 현재 변동성 수준에서 출발하지 않습니다. 하루하루의
> 충격은 표본의 평균을 뺀 일별 수익률 가운데 하나이고, 그 위에 드리프트(추세
> 가정)를 더합니다.

The text uses "demeaned", as the drift note does. The Korean names the drift
"드리프트(추세 가정)", because Flet labels that input 드리프트 and Native labels it 추세 가정.
Both texts carry the same numbers (a test compares them). A native speaker has not
reviewed the Korean.

## What changed, by surface

| Surface | Change |
| --- | --- |
| `core/research/mc_disclosure.py` | Adds `BOOTSTRAP_BLOCK_SESSIONS = 5`, `BOOTSTRAP_TEXT`, `BOOTSTRAP_TEXT_KO` and `bootstrap_disclosure(model)`. The function is keyed on the model id and returns None unless the id is `'bootstrap'`. The record's fields: `method`, `block_sessions`, `block_length` (`fixed`), `resampled`, `within_block_lag_retention` (`(5-k)/5 for k=1..4 over a long horizon, more over a short one`), `clustering_from_lag` (5, none kept from there), `current_vol_level` (`not_used`) and `description`. The module does not import the engine. |
| `core/quant/montecarlo.py` | Module docstring only. The BOOTSTRAP bullet now describes the circular, fixed-5 scheme and its limits. Every function and class has the same AST as `a32106b`. |
| Flet Quant Lab (`ui/quant_lab_page.py`) | For bootstrap, the text is shown under the drift note. The AI payload gains `resampling_definition`: the record for bootstrap, None for the other models. `_MODEL_LABELS`, `_DRIFTS`, `_RF_ASSUMED` and the ERP field are unchanged, because the primer builder parses them. |
| Flet narrative (`core/quant/insights.py`) | For bootstrap, the text follows the calibration sentence. The other models' narratives are byte-identical. |
| Flet Korean | Adds the EN/KO pair to `core/ui_legacy_messages.py` (`EN_TO_KO`, `KO_TO_EN`). In the default `ko_KR` locale, `translate_controls` therefore shows the Korean line. |
| Native Monte Carlo notes (`quantgen_desktop/app.py`) | For bootstrap, the text follows the drift note. `quantgen_desktop/translations.py` carries the same pair, so the line is Korean in `ko`. The other MC note lines stay English, as before. |
| `README.md` model table | Says fixed, circular 5-session blocks, not a stationary bootstrap. Clustering is kept only partly, within 5-session blocks, and the fan does not start from today's vol. |
| `docs/build_models_primer.py` | Source only: section 3.5 and the comparison-table row now name the circular fixed-5 scheme. "Clustering survives exactly as far as it exists" is gone. "It can never draw a move larger than any the window contains" is gone: section 3.5 now says every daily shock is one of the demeaned returns, so no shock falls outside the demeaned sample's range, and that because of the demeaning and the drift a drawn daily move can still fall outside the range of the raw returns. The section 9.5 table of narrative sentences gains a row for `BOOTSTRAP_TEXT` (bootstrap only). **The PDF `docs/QUANTGEN_Models_Primer.pdf` was not rebuilt.** |

## Unchanged for valid inputs

These were checked by `tests/mc_bootstrap_disclosure_acceptance.py` and by a probe
against `a32106b`:

- **Bootstrap numbers.** On three synthetic histories and in all four drift modes,
  `run_monte_carlo` equals an independent rebuild of the documented recipe. The fan,
  terminal and sample-path arrays are `np.array_equal`. The risk scalars, `mu_annual`,
  `sigma_annual` and `correction_annual` are equal.
- **GBM, jump and GARCH-t.** In all four drift modes, every MCResult array and scalar
  equals the value assembled from the engine's untouched building blocks
  (`_simulate_gbm`, `_simulate_jump`, `fit_garch`/`simulate_returns`). That check moves
  with those building blocks, so the test also pins nine numbers per case (mean,
  median, p05, p95, VaR, CVaR, `mu_annual`, `sigma_annual`, `correction_annual`) for
  all four models under `premium` and `zero`. The values were computed with
  `a32106b`'s own `montecarlo.py` and equal the branch's exactly. The tolerance is
  1e-9 relative, and 1e-5 for GARCH-t, whose fit is an optimizer solve. With
  `_simulate_gbm` drawing at 1.01 σ (in memory only), the assembly check still passes
  and the pinned check fails.
- **Narratives.** On 3 histories × 4 drift modes, the 36 non-bootstrap narratives are
  byte-identical to `a32106b`. The 12 bootstrap narratives equal the old text plus
  this one sentence.
- **Flet.** On the volatility fixture with drift zero, for every model, every old
  payload value equals `a32106b`, and the on-page texts are identical except for the
  added line.
- **Native.** The metrics rows are identical. The notes are identical except for the
  added bootstrap line. This was compared with the disclosure switched off in the test,
  not against `a32106b`'s `app.py`.
- **Stored run.** The ResearchRun keeps the same 7 metrics, verdict NOT_RUN and the
  export round-trip.
- **Elsewhere.** `MODELS`, `DRIFTS`, `MCResult`, `volatility_disclosure` and the label
  블록 부트스트랩 are unchanged.

One expected difference: the montecarlo.py bytes changed, so
`code.calculation_sha256` (and the computation fingerprint) differ for new runs. Old
exports keep their hash. No test pins the value.

## Still open

- **C1(b), the maths fix.** Options are a block length from the r² autocorrelation
  (the first lag inside ±2/√T) or stationary (geometric) block lengths. Either one
  changes every bootstrap number. It also needs `_bootstrap_correction` re-derived,
  and the martingale test values move. It needs the owner's approval. C1's own test
  (the lag-5 autocorrelation of the paths matches the sample) is not added here.
  Conditioning on the current vol level would need a different model, such as a
  volatility-filtered bootstrap.
- **L4: inf and duplicate dates are resampled as they are.** These stay with D12-01
  and D12-02 (history cleaning). The PT-18 ownership is unverified.
- **Primer PDF.** Not rebuilt. Rebuilding writes `docs/` and needs its data source.
  Until it is rebuilt, the shipped PDF still says "stationary".
- **Stale archive text.** The reviewer found that
  `research_notes/QUANTGEN TRADEGEN split map/split_map.md:391` still says "stationary
  block bootstrap". It was not re-checked or edited here.
- **Bookkeeping, left to the main session.** This branch does not do these:
  - the SECTION10 queue and triage entries;
  - the compliance baseline refresh: new monitored files change the inventory digest
    of all 20 documents, and `--check` exits 1 until it is refreshed;
  - the `ui_website_updates` record;
  - adding the new test module to `runtime-smoke.yml`;
  - the `qa/research_status.json` snapshot, which is affected because `README.md`
    changed.
- **Native AI commentary payload.** It stays at parameters, metrics and data, as in
  the earlier MC fixes. Adding the record there is the owner's call.
- **Exports.** A bootstrap ResearchRun exported as JSON or as a ZIP bundle
  (`research-run.json`, `report.html` in either locale) carries no scheme text: the run
  stores parameters, metrics and data, and `core/research/export.py` and
  `core/research/runs.py` add no Monte Carlo note. The screen shows the text, the
  export does not. N-M1-03 left the export the same way. Adding it changes the export
  format and is the owner's call.
- **Primer section 9.5, calibration row.** The row "Calibration: annualized volatility
  x%." was already out of date before this change (the narrative says "historical
  sample log-return volatility (annualized, 252 sessions)"). It is not changed here.

## Checks

`tests/mc_bootstrap_disclosure_acceptance.py` has 15 tests and runs offline. Run it
with `python -B -m unittest tests.mc_bootstrap_disclosure_acceptance -v`. It covers:

- the constant against both engine defaults, plus an AST check that `run_monte_carlo`
  passes no block length;
- the fixed, circular block structure on index input;
- the (5-k)/5 retention on the fixture above, and a higher share on a 10-session
  horizon;
- unchanged numbers for all four models, including values pinned from `a32106b`;
- the record, and that the EN and KO texts carry the same numbers;
- the narrative;
- Flet in English and Korean, and the payload;
- Native notes in `en` and `ko`;
- the docstring.

A mutation run with block length 6 in the engine made the four engine tests fail
(before review; not re-run after it). A mutation of `_simulate_gbm` (1.01 σ) fails the
pinned-number test.

## Review corrections

Three reviewers read the first version. What changed after their findings:

- Primer 3.5 still said the bootstrap "can never draw a daily shock larger than any the
  window contains". In its natural reading that is false, because of the demeaning (see
  "A sentence that was dropped"). It now says the shock is one of the demeaned returns.
  This note's L1 row and its account of the dropped sentence were corrected the same
  way.
- "Lag k keeps (5-k)/5" holds only over a long horizon. The EN and KO texts, the record
  field, the montecarlo.py docstring and primer 3.5 now say so.
- The Korean text says 드리프트(추세 가정) and uses plainer verbs ("다시 뽑으며",
  "서로 독립적으로").
- Primer 9.5 gains the narrative row, and "Still open" names the export surface.
- The test pins numbers from `a32106b`, so a change inside a model's simulator fails it.

## Not verified

- Real provider data and the Windows screen.
- A native speaker's review of the Korean text.
- The primer PDF output.
- Whether stored study cards mention this scheme. No bootstrap MC is a gate input,
  but card contents were not searched.
