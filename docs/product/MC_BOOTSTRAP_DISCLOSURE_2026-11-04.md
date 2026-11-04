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
| L1. It cannot draw a shock larger than the sample contains. | none (inherent to resampling) | no |
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
  k < 5, and nothing from lag 5.
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
sample's range is drawn". That is false, because the drift is added to each
demeaned shock.
- Premium drift on a negative-mean sample: sample max +0.04979, drawn max +0.05153.
- Zero drift on a positive-mean sample: sample min −0.05183, drawn min −0.05348.

The shipped text says instead that each shock is one of the sample's demeaned returns,
with the drift added on top.

**This change's test fixture.** GARCH-t seed 1034, 504 sessions; the product's
`run_monte_carlo`, 4,000 × 125, seed 11.

| Lag | 1 | 2 | 3 | 4 | 5 | 10 | 20 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sample r² autocorrelation | 0.201 | 0.158 | 0.220 | 0.220 | 0.310 | 0.199 | 0.057 |
| In-path / circular | 0.811 | 0.600 | 0.406 | 0.209 | 0.007 | −0.001 | −0.029 |

## The text

EN (`BOOTSTRAP_TEXT`):

> Block bootstrap: circular, fixed 5-session blocks of the demeaned daily log returns in
> the fit window, wrapping at the sample end (not a stationary bootstrap with random
> block lengths). Blocks are drawn independently from anywhere in the window, so
> volatility clustering is only partly kept at lags 1-4 (lag k keeps (5-k)/5 of the
> sample's) and is lost from lag 5, and the fan does not start from the current
> volatility level. Each day's shock is one of the sample's demeaned daily returns,
> with the drift added on top.

KO (`BOOTSTRAP_TEXT_KO`):

> 블록 부트스트랩: 추정 구간의 일별 로그수익률에서 평균을 뺀 값을 5거래일 고정 길이 블록으로
> 원형 재표본합니다. 표본 끝에 닿으면 처음으로 이어지며, 블록 길이가 무작위인 정상(stationary)
> 부트스트랩이 아닙니다. 블록은 구간 어디에서나 서로 독립으로 뽑으므로 변동성 군집은 시차 1-4에서
> 일부만 남고(시차 k에서는 표본의 (5-k)/5만 남음) 시차 5부터는 사라지며, 팬 차트는 현재 변동성
> 수준에서 출발하지 않습니다. 하루하루의 충격은 표본의 평균을 뺀 일별 수익률 가운데 하나이고,
> 그 위에 드리프트를 더합니다.

The text uses "demeaned", as the drift note does. A native speaker has not reviewed
the Korean.

## What changed, by surface

| Surface | Change |
| --- | --- |
| `core/research/mc_disclosure.py` | Adds `BOOTSTRAP_BLOCK_SESSIONS = 5`, `BOOTSTRAP_TEXT`, `BOOTSTRAP_TEXT_KO` and `bootstrap_disclosure(model)`. The function is keyed on the model id and returns None unless the id is `'bootstrap'`. The record's fields: `method`, `block_sessions`, `block_length` (`fixed`), `resampled`, `within_block_lag_retention` (`(5-k)/5 for k=1..4`), `clustering_from_lag` (5, none kept from there), `current_vol_level` (`not_used`) and `description`. The module does not import the engine. |
| `core/quant/montecarlo.py` | Module docstring only. The BOOTSTRAP bullet now describes the circular, fixed-5 scheme and its limits. Every function and class has the same AST as `a32106b`. |
| Flet Quant Lab (`ui/quant_lab_page.py`) | For bootstrap, the text is shown under the drift note. The AI payload gains `resampling_definition`: the record for bootstrap, None for the other models. `_MODEL_LABELS`, `_DRIFTS`, `_RF_ASSUMED` and the ERP field are unchanged, because the primer builder parses them. |
| Flet narrative (`core/quant/insights.py`) | For bootstrap, the text follows the calibration sentence. The other models' narratives are byte-identical. |
| Flet Korean | Adds the EN/KO pair to `core/ui_legacy_messages.py` (`EN_TO_KO`, `KO_TO_EN`). In the default `ko_KR` locale, `translate_controls` therefore shows the Korean line. |
| Native Monte Carlo notes (`quantgen_desktop/app.py`) | For bootstrap, the text follows the drift note. `quantgen_desktop/translations.py` carries the same pair, so the line is Korean in `ko`. The other MC note lines stay English, as before. |
| `README.md` model table | Says fixed, circular 5-session blocks, not a stationary bootstrap. Clustering is kept only partly, within 5-session blocks, and the fan does not start from today's vol. |
| `docs/build_models_primer.py` | Source only: section 3.5 and the comparison-table row now name the circular fixed-5 scheme. "Clustering survives exactly as far as it exists" is gone. "It can never draw a move larger than any the window contains" now says "daily shock", with the drift added on top. **The PDF `docs/QUANTGEN_Models_Primer.pdf` was not rebuilt.** |

## Unchanged for valid inputs

These were checked by `tests/mc_bootstrap_disclosure_acceptance.py` and by a probe
against `a32106b`:

- **Bootstrap numbers.** On three synthetic histories and in all four drift modes,
  `run_monte_carlo` equals an independent rebuild of the documented recipe. The fan,
  terminal and sample-path arrays are `np.array_equal`. The risk scalars, `mu_annual`,
  `sigma_annual` and `correction_annual` are equal.
- **GBM, jump and GARCH-t.** In all four drift modes, every MCResult array and scalar
  equals the value assembled from the engine's untouched building blocks
  (`_simulate_gbm`, `_simulate_jump`, `fit_garch`/`simulate_returns`).
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

## Checks

`tests/mc_bootstrap_disclosure_acceptance.py` has 14 tests and runs offline. Run it
with `python -B -m unittest tests.mc_bootstrap_disclosure_acceptance -v`. It covers:

- the constant against both engine defaults, plus an AST check that `run_monte_carlo`
  passes no block length;
- the fixed, circular block structure on index input;
- the (5-k)/5 retention on the fixture above;
- unchanged numbers for all four models;
- the record;
- the narrative;
- Flet in English and Korean, and the payload;
- Native notes in `en` and `ko`;
- the docstring.

A mutation run with block length 6 in the engine made the four engine tests fail.

## Not verified

- Real provider data and the Windows screen.
- A native speaker's review of the Korean text.
- The primer PDF output.
- Whether stored study cards mention this scheme. No bootstrap MC is a gate input,
  but card contents were not searched.
