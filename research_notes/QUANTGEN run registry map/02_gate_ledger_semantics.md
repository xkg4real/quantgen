# 02 — gate_ledger semantics, for the Strategy Lab run registry (owner ruling R3)

Date: 2026-10-27. Scope: a read-only map of `core/quant/gate_ledger.py` and every caller, so a run registry can be
designed around it without editing the frozen harness. No repository code was changed. Behaviour marked "probe" was
checked by a script that wrote ledgers to `tempfile` directories only
(`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ledger_probe/probe.py`).
No production ledger was opened for writing. This sandbox has no `~/.nextgen` directory, so the owner's ledgers
(E1, C3, ...) were not read here. Every statement about their contents is UNVERIFIED.

Binding requirement: owner ruling R3 (2026-10-27). Ledger-based counting is moved forward. Making existing card
verdicts stricter is a separate, later decision. Existing card verdicts and the GATE constants do not change here.

---

## 0. Answers in brief

1. **The ledger counts configurations, not runs.** One row per distinct `config_id` per family file. A second run of
   the same configuration appends nothing (`core/quant/gate_ledger.py:337-346`).
2. **`config_id` ignores the data period, the market, the run time, the script, the run kind, the phase and the
   top-level `cost` field** (`gate_ledger.py:60-61`, `:168-171`; pinned by `tests/macro_m7_ledger.py:502`). Only the
   first registration's `span`, `run_utc`, `script` and anchor survive.
3. **Unknown fields are refused** (`gate_ledger.py:190-192`; probe: `run_id`, `verdict`, `status`,
   `strategy_version`, `results`, `data_md5` are all refused). So the ledger cannot hold a run ID, a verdict or a run
   status. It holds parameters fully, and the strategy version, data period, cost and results only partly.
4. **`run_kind` is a label only.** Nothing in the ledger or in `step3` filters or weights by it
   (`gate_ledger.py:197-201`, `:211` are its only uses). `N_raw` counts a `quick_check` exactly like a `trial`.
5. **Strategy Lab's verdict does not read the ledger.** It deflates with `n_trials=len(grid)`
   (`ui/strategy_lab_page.py:127`). The ledger count is shown only as a chip (`ui/strategy_lab_page.py:254-256`).
6. **Lab rows carry no difference series** (`ui/strategy_lab_page.py:74-81`). So `N_eff` cannot be computed for Lab
   families from the ledger alone. Only `N_raw` (distinct configurations) is available.
7. **Therefore a separate append-only run registry is needed**, one row per run attempt, keyed to the ledger by
   `(family_id, config_id)` and the stored `row_md5`. Section 8 lists its fields.
8. **Existing ledgers can be read without being rewritten** through `FamilyLedger.verify_chain()`, `.rows()`,
   `.hash()`, `.snapshot()` and `.n_raw`. These never write. `append` / `register_trial` must never be called on a
   production ledger by the registry: even a deduplicated call creates the `<family>.jsonl.lock` sidecar (probe).

---

## 1. The file and its frozen status

- `core/quant/gate_ledger.py` is one of the eleven harness sources hashed into the gate package manifest
  (`core/quant/gate_package.py:36-38`, `:86`). After a freeze, any edit is a new package version re-run on every card
  (`gate_package.py:241-255`).
- It is also pinned by sha256 in the grokteam pre-registration (`grokteam/out/PREREG_book.json:45`). The current file
  hashes to the pinned value `018eaa96…be86` (checked with `sha256sum` this session). The frozen-study guard checks
  pins in the tagged tree (`tests/frozen_guard.py:1-15`).
- Consequence: the registry must import `gate_ledger` and never require an edit to it.
- The module has no wall clock and no `config` import; both are pinned (`tests/macro_m7_ledger.py:584-593`). The
  ledger directory is injected (`gate_ledger.py:26`).

---

## 2. Row schema

`REQUIRED_ROW` (`gate_ledger.py:63`), `OPTIONAL_ROW` (`:64-65`), `CHAIN_FIELDS` (`:66`). The harness adds
`config_id` and `family_id` (`:213`, `:341`). `validate_row` writes every optional key, `None` when absent
(`:209-210`), so every stored line has all 26 keys (probe).

| Field | Req. | In `config_id` | Check (file:line) | Strategy Lab value (`ui/strategy_lab_page.py`) |
|---|---|---|---|---|
| `rule` | yes | yes | non-empty (`:187-189`) | family id, e.g. `E1` (`:75`, `:50-51`) |
| `params` | yes | yes | must be a mapping (`:202-203`) | grid point θ + `symbols` + `cost_bps` (`:75-76`) |
| `timing_class` | yes | yes | in `VALUE`/`NON-COMPLIANT`/`COMPLIANT` (`:54`, `:193-194`) | `COMPLIANT` (`:77`) |
| `span` | yes | **no** | `[start, end]` ISO dates, start ≤ end (`:174-179`) | first and last panel date (`:77`) |
| `market` | yes | **no** | non-empty | one market or `MULTI` (`:71-72`, `:78`) |
| `run_utc` | yes | **no** | tz-aware ISO instant (`:134-146`, `:204`) | wall clock (`:79`) |
| `phase` | yes | **no** | `research` or `card` (`:55`, `:195-196`) | `research` (`:79`) |
| `script` | yes | **no** | non-empty | `ui/strategy_lab_page.py` (`:81`) |
| `estimator`, `window`, `cap`, `instrument_book`, `rebalance`, `start_convention` | no | yes | none | all `None` |
| `cost` | no | **no** | none (seed loader casts to float, `:913-914`) | not set |
| `results_md5`, `diff_series_ref`, `delta_sr` | no | no | none | not set |
| `card_id` | no | no | none | not set |
| `run_kind` | no (default `trial`) | **no** | in `RUN_KINDS`; null kinds raise (`:197-201`) | `variant` (`:80`) |
| `run_utc_anchor` | no (default `UNVERSIONED`) | no | none at write; checked by step 3 | `GL.repo_anchor()` (`:80`) |
| `source` | no | no | none | `"Strategy Lab: " + vendors` (`:80`) |
| `config_id`, `family_id` | harness | — | recomputed on verify (`:305-306`) | — |
| `row_md5`, `prev_row_md5` | harness | — | chain (`:284-309`) | — |

Any other key raises `LedgerRefused("ledger row has unknown fields …")` (`:190-192`; `tests/macro_m7_ledger.py:136`).

---

## 3. Identity: `config_id`, `row_md5`, `family_id`

- **`config_id`** = md5 of the canonical JSON of the nine `ROW_SET_KEY` fields (`gate_ledger.py:60-61`,
  `:168-171`). Canonical JSON = sorted keys, no whitespace, `ensure_ascii=False`, NaN refused
  (`core/ficc/macro_schema.py:303-305`). A change to any `params` entry is a new configuration
  (`tests/macro_m7_ledger.py:496-501`). Lab sorts symbols (except pairs) before hashing, so case and order are not
  new configurations (`ui/strategy_lab_page.py:68-70`; pinned by `tests/paper_live_acceptance.py:333-344`).
- **Stored `row_md5`** = md5 of the canonical JSON of the row without the two chain fields (`gate_ledger.py:217-218`).
  It covers `family_id`, `span`, `run_utc`, `script`, `source` and so on. It is the stable identity of the row.
  Moving a row to another family file breaks it (probe).
- **`RegisterResult.row_md5` is not the same quantity in both paths.** On a fresh append it is the md5 of the whole
  line bytes, i.e. the next row's `prev_row_md5` (`:355`; pinned by `tests/macro_m7_ledger.py:85`). On a duplicate it
  is the stored content `row_md5` (`:346`). Probe: `res.row_md5 == res.row["row_md5"]` is False on append, True on
  dedup. **The registry must key on `res.row["row_md5"]`** (the stored field), which is the content hash in both
  paths (`:349`, `:346`).
- **`family_id`** = the file stem (`:271-273`). Dedup is per family file only.

---

## 4. Dedup behaviour

`append` takes the lock, re-reads and verifies the whole chain, and returns the existing row unchanged when any
stored row has the same `config_id` (`gate_ledger.py:337-346`). The first row stands (docstring reading, `:14-15`).

Probe results on one temp E1 ledger (first row: Lab-shaped, 50 bp in `params`):

| Second registration differs only in | Appended? |
|---|---|
| `span` (another data period) | no |
| top-level `cost` | no |
| `run_kind`, `phase`, `market`, `source`, `script`, `run_utc_anchor` | no |
| `results_md5`, `delta_sr` | no |
| `params.cost_bps` (Lab's cost encoding) | **yes** — a new configuration |

Consequences:

- A re-run of the same grid on a different period, vendor or session count leaves **no trace**. Paper_live relies
  on this and passes one fixed span everywhere (`paper_live/engine.py:96-100`; `tests/paper_live_acceptance.py:234-242`).
- A Lab cost-sensitivity run (cost below the table floor, verdict withheld, `ui/strategy_lab_page.py:92-103`) still
  registers, and with a new `cost_bps` it is a **new configuration** that raises `N_raw`.
- Results cannot be attached later. The ledger is append-only and the dedup returns the old row.
- Lab registers after the walk-forward and **before** scoring (`ui/strategy_lab_page.py:117-118`). A run that fails
  in data loading or the walk-forward registers nothing. A run that fails in `score_strategy` leaves its rows.
  Synthetic runs register nothing (`ui/strategy_lab_page.py:60-61`).

---

## 5. Hash chain, ledger hash, snapshot, locking

- **Line format.** Each line is the row's canonical JSON, LF-terminated, binary append, `flush` + `fsync`
  (`gate_ledger.py:350-354`).
- **Chain.** `prev_row_md5` = md5 of the previous line's bytes, `None` for the first (`:348`). `row_md5` = content
  hash (`:349`).
- **Verification** (`verify_chain`, `:284-309`) fails on: an unreadable line, a non-object, bytes ≠ canonical JSON
  (any reformat), a `prev_row_md5` mismatch (dropped, moved or edited earlier line), a `row_md5` mismatch (edited
  last line), a row `validate_row` now refuses, or a `config_id`/`family_id` that does not recompute. `rows()` raises
  `LedgerRefused` on any failure (fail closed, `:311-316`), and so does every `append` (`:343`).
- **Ledger hash** = md5 of the canonical JSON of the rows sorted by their canonical JSON (`:371-372`). It is
  order-independent.
- **Snapshot** = the shortest prefix whose hash equals a given value (`:323-330`). Headers pin
  `ledger_hash_at_registration` and `N_raw_at_registration` (`core/quant/cards.py:615-624`, `:627-656`, field set at `:648`).
- **Hash at run.** After a card run the card's `ledger_hash_at_run` must equal the stored hash
  (`gate_ledger.py:389-396`).
- **Locking.** `_exclusive` holds a process-wide `threading.Lock` plus an OS lock on a sidecar `<file>.lock`
  (`:239-262`). Pinned by `tests/paper_live_acceptance.py:347-357` (50 concurrent rows, chain intact). The sidecar is
  created on every `append`, including a deduplicated one (probe: `['E1.jsonl', 'E1.jsonl.lock']`). Pure reads
  create nothing (probe).
- **`n_raw`** = `len(rows())` (`:332-334`): all rows, all kinds, all markets, all writers.

---

## 6. `RUN_KINDS` and what each means in the repo

`RUN_KINDS = ("trial", "quick_check", "revision", "timing_lag", "variant") + NULL_DISTRIBUTION_KINDS`
(`gate_ledger.py:57-58`). The null kinds raise `NullDistributionRun` and append nothing (`:200-201`;
`tests/macro_m7_ledger.py:137-140`).

| Kind | Meaning (source) | Writers found | Tests |
|---|---|---|---|
| `trial` (default) | a run of a registered rule's code path (`:379-382`) | `paper_live/engine.py:96-112` (accounts: `paper_live/run_live.py:60`, `paper_live/replay.py:172`); `grokteam/book.py:724-733` (family `GROKTEAM-BOOK`, `:64`); `core/quant/forward_sim.py:316-349` (R-29 US-FUT card row, `phase: card`) | `tests/paper_live_acceptance.py:234-242`; `tests/macro_m8_forward.py:557-575` |
| `quick_check` | a quick check from a research script is a row (`tests/macro_m7_ledger.py:91-94`) | no production writer | `tests/macro_m7_ledger.py:92-94` |
| `revision` | listed in the docstring of `register_trial` (`:380-381`). A header revision itself is **never** a row and never N (`:816-826`, `:864`) | no writer found (grep) | none for the kind; adoption-is-not-a-row: `tests/macro_m7_ledger.py:522-538` |
| `timing_lag` | one row per lag of the R-34 timing profile, `phase: card`, lag inside `params` (`docs/macro_overlay_study.py:268-276`; `core/quant/cardp.py:992-1019`) | `docs/macro_overlay_study.py:273` | `tests/macro_m7_ledger.py:80-83`, `:477-484`; `tests/macro_m7_integration.py:146-149` |
| `variant` | a variant run (book, rebalance, band, estimator, grid point) | Strategy Lab (`ui/strategy_lab_page.py:80`); `paper_live/grid.py:130`; `core/quant/forward_sim.py:351-358` (logged 50 bp variants, `card_id: None`); `docs/techfund_study.py:455-463` (CRY-1 extra C3 trials) | `tests/macro_m8_forward.py:641-650`; `tests/paper_live_acceptance.py:333-344` |
| `acceptance_placebo`, `shift_panel`, `gjr_null`, `d4_panel` | null-distribution runs; never a row (`:56-57`, `:91-92`) | — | `tests/macro_m7_ledger.py:137-140` |

Facts that matter for R3:

- `run_kind` is not in `config_id`, so the same parameters under two kinds are one row (probe).
- Neither `n_raw`, `n_eff`, `selection_factor` nor `step3` reads `run_kind` (grep: only `:197-211`). Every kind
  counts with weight 1.
- `phase` is used once: `step3` drops the card's own rows (`card_id` equal **and** `phase == "card"`,
  `:762-763`). Those rows still count for a later card of the family (`tests/macro_m7_ledger.py:485-488`).
- `tools/paper/study.py` has its own run kinds (`exploratory`, `prespecified`, `confirmatory`; `:27`) and a
  paper-local ledger directory (`:159-160`). Those are not ledger `run_kind` values.

---

## 7. Counting: `N_raw`, `N_eff`, step 3 and the selection factor f

### 7.1 Difference series and correlation
- Inputs are per-configuration difference series (rule minus comparator), loaded through each row's
  `diff_series_ref` (`gate_ledger.py:357-368`) or passed as `series={config_id: series}`.
- `_aligned` builds a (T, K) matrix on the common window: index intersection for pandas Series, equal length
  otherwise; rows with any non-finite value are dropped; fewer than 20 observations raise `CorrUnavailable`
  (`:76`, `:421-444`).
- `diff_corr` = Pearson correlation; a constant series raises (`:447-457`).

### 7.2 Clusters
`n_clusters` (`:473-483`): distance `D = sqrt(0.5 · (1 − ρ))` (clipped at 0, zero diagonal), scipy average linkage,
cut at `sqrt(0.5 · (1 − 0.5)) = 0.5`. Configurations whose average linkage distance is ≤ 0.5 (correlation ≥ 0.5 on
the distance scale) share a cluster. `FILING_RHO = 0.5` (`:80`).

### 7.3 Equivalent N
- `emax_sim(C)` = mean over 200,000 draws of `max_k Z_k`, `Z ~ N(0, C)`, by eigen-decomposition (C may be
  singular), `default_rng(SeedSequence(11))`, chunks of 50,000 (`:73-75`, `:486-502`).
- `e(N)` = 0 for N ≤ 1; the exact integral for 1 < N < 2; the BLdP closed form
  `(1 − γ)Φ⁻¹(1 − 1/N) + γΦ⁻¹(1 − 1/(Ne))` from 2 (`:505-527`).
- `n_equiv(E)` inverts `e`: E ≤ 0 → 1; E < 0.51976 → bisect the exact integral on [1, 2); E in [0.51976, 0.56419]
  → 2; E ≥ e(10⁶) → 10⁶; else bisect the closed form on [2, 10⁶] (`:546-557`).

### 7.4 `N_eff`
`n_eff(series)` returns `N_raw = K`, `rho_bar`, `N_hat_linear = ρ̄ + (1 − ρ̄)K` (printed only, never the gate's N,
`:468-470`), `N_clusters`, `E_sim`, `N_equiv`, and **`N_eff = max(N_clusters, N_equiv)`** (`:574-582`). Padding with
near-duplicates moves `N_equiv` by < 0.5 and `N_clusters` not at all (`tests/macro_m7_ledger.py:211-220`). The Kish
design effect and a revision count used as N are forbidden by a static scan (`:851-888`;
`tests/macro_m7_ledger.py:315-343`).

### 7.5 Step 3 (macro CARD-O / CARD-P only)
`step3` (`:748-813`):
1. Header checks (`:736-745`): no declared `selection_factor`, a `ledger_hash_at_registration`, class CARD-O or
   CARD-P, `card_id`, `family_id`, `market`, `data_span`.
2. Rows = the snapshot named by the header, minus the card's own card-phase rows (`:762-763`).
3. `fixed_at = t_fix(...)` = the earliest **anchored** instant among the header commit and any SPEC version naming
   the `config_id`; an unanchored one raises `UnanchoredTimestamp` (`:688-697`).
4. `n_raw = len(rows)` (`:767`).
5. `selection_factor` (`:700-733`), per reading:
   - `market_scoped`: rows with the card's `market`; `family_wide`: all rows (`:62`, `:709`).
   - Every row whose `span` overlaps the card's span (closed intervals, `:674-676`) must be anchored, else
     `UnanchoredTimestamp` (`:713-716`).
   - If no overlapping row ran before `fixed_at`, f = 1.
   - Otherwise f = `N_eff` of **all** rows of the reading, not only the touching ones (`:725-731`; probe: 3 rows,
     1 touching, `N_raw` 3).
6. f = max over the readings and the acceptance report's f (`:679-685`, `:792`).
7. Fail closed: `CorrUnavailable` → CARD-O raises (no verdict written); CARD-P falls back to f = `N_raw`
   (`:778-788`). Probe: on Lab-shaped rows (no `diff_series_ref`) CARD-P gives f = `N_raw`, CARD-O raises.
   **Caveat (probe):** when a `loader` is passed and a row has no reference, `difference_series` raises at `:764-765`,
   before the `try` at `:772`. So CARD-P raises too on that path. A comparison script must pass `series=` or catch.
8. Deflated ΔSR = `Φ((ΔSR − SE_null · e(N_eff)) / SE_obs)` (`:588-592`); CARD-O passes iff ≥ 0.95 (`:69`,
   `:795-796`). CARD-P is not gated (`:797-798`). `V_trials` is printed only when `N_clusters` ≥ 30 and ≥ 30 rows
   carry `delta_sr` (`:789-790`).

### 7.6 How this relates to the Strategy Lab verdict
- The Lab and the asset-expansion cards use a different deflated Sharpe: `validate.deflated_sharpe` with
  `expected_max_sharpe(n_trials, sr_sd)` (`core/quant/validate.py:211-237`). Its `n_trials` is "every configuration
  ever tried (grid size plus revisions)" by its docstring (`validate.py:492-497`). The Lab passes `len(grid)`
  (`ui/strategy_lab_page.py:127`).
- The study cards record their N by hand: `trials = {N_planned, N_total, ledger: [...]}`
  (`docs/asset_expansion_study.py:207`, `:440`). For example C3 has `N_total` 11 with a text log
  (`docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json:51`); E1 has 12 (`S_E1_trend_us.json:99`). These are
  not read from any `gate_ledger` file.
- Precedent for "count more, keep the verdict": CRY-1 added three C3 trials to the registry and printed
  "`<decision>`, unchanged (D-24: additions are governance lines; the stored verdict is not rewritten)"
  (`docs/techfund_study.py:445-471`).
- So the R3 parallel computation is: the existing verdict (n_trials = grid or `N_total`) beside a ledger-based
  count fed to the same `validate.deflated_sharpe`, printed, not gating. `step3` is not the Lab's verdict path.

---

## 8. The owner's record fields against the ledger

| Owner field (R3) | Ledger field(s) | Can the ledger hold it? | Limit |
|---|---|---|---|
| Run ID | none | **No** | `run_id` refused (`:190-192`, probe). `config_id` names a configuration; `row_md5` names its first registration. A second run appends nothing (`:343-346`). |
| Strategy version | `script`, `run_utc_anchor`, `source` | **Partly** | No code hash. `repo_anchor` = HEAD sha only; uncommitted edits are invisible (`:122-131`). A worktree (`.git` is a file) or packed refs read `UNVERSIONED` (`tests/macro_m7_ledger.py:146-148`). First registration only. |
| Data period | `span` | **Partly** | Not in `config_id`; first registration only. No vendor or data hash; `source` is free text. |
| Parameters | `params` + six key fields + `timing_class` | **Yes** | Lab folds `symbols` and `cost_bps` into `params` (`ui/strategy_lab_page.py:75-76`). |
| Cost conditions | `cost` (not in key); Lab: `params.cost_bps` | **Partly** | The table floor, the withheld flag and the 2× stress run are not recorded. A top-level `cost` change is not a new row (`tests/macro_m7_ledger.py:502`). |
| Results | `results_md5`, `delta_sr`, `diff_series_ref` | **Pointer only** | First registration only; Lab sets none; metrics are unknown fields. |
| Verdict | none (`card_id` is a reference) | **No** | Refused (probe). |
| Run status | none (`run_kind` is a kind) | **No** | Refused (probe). A failure leaves rows or nothing, depending on the stage (section 4). |

Putting a version or run identity inside `params` is not acceptable. It changes `config_id`, so every existing
configuration would be counted again under a new id, and macro step 3 on shared families would see inflated
`N_raw`.

### What must live in a separate append-only run registry
One row per run **attempt**, written whether the run completes or not. Minimum content:

- **Identity:** `run_id` (unique per attempt); `parent_run_id` for a re-run; `recorded_utc` (injected clock).
- **Ledger link:** `family_id`; ledger path; `ledger_hash` and `n_raw` before and after; for every grid point
  `{config_id, row_md5 (= res.row["row_md5"]), appended}`. This is the key back to the ledger.
- **Strategy version:** HEAD sha, a dirty-tree flag, and sha256 of the code that decides the result
  (`core/quant/strategies.py`, `core/quant/validate.py`, `ui/strategy_lab_page.py`).
- **Data period:** symbols, vendor per symbol, requested sessions, actual first/last date, number of sessions,
  sha256 of the aligned panel.
- **Parameters:** the full grid and the chosen point (`ui/strategy_lab_page.py:135`).
- **Cost conditions:** `cost_bps`, the table floor and cost classes (`ui/strategy_lab_page.py:92-103`), the withheld
  flag, the stress multiplier.
- **Results:** the `StrategyScore` numbers and a results hash.
- **Verdict:** decision, `WITHHELD`, or none, with the reason.
- **Run status and class:** status (`COMPLETED`, `FAILED` with stage and error class, `WITHHELD`, `SYNTHETIC`) and
  the run class of section 9.
- **Chain:** `prev_row_md5`, with a lock. `cards.chain_append` can be imported for the chain but has no lock
  (`core/quant/cards.py:526-539`); `tf_gov.ContaminationLog` shows the pattern (`core/quant/tf_gov.py:487-506`).

Prior art for keying an external record to `config_id`: the grokteam pre-registration stores
`{account, config_id, appended}` per account (`grokteam/out/PREREG_book.json:135`). `tf_gov.TrialRegistry`
(`core/quant/tf_gov.py:350-379`) is only a directory of family ledgers with a weighted global N; it does not record
runs.

---

## 9. Classes of run, as the ledger sees them

These rules state what the ledger already does and what only the registry can see. The class names and the
experiment-count rule are a PROPOSAL for the owner. They do not change any verdict.

| Class | Test (registry, against the ledger) | Ledger effect | Total runs | Valid experiments (proposal) |
|---|---|---|---|---|
| Simple re-run | every `config_id` of the grid already present; same data hash and code hash as an earlier COMPLETED run | nothing appended | +1 | +0 |
| Failed run, before registration | status FAILED at data load or walk-forward | nothing appended | +1 | +0 |
| Failed run, after registration | status FAILED in scoring | rows appended (section 4) | +1 | +0 in the registry count; the ledger count keeps the new rows. Both are printed. |
| Parameter search | ≥ 1 `config_id` new to the family | new rows | +1 | + number of new `config_id`s (the ledger's own rule) |
| Independent validation | all `config_id`s already present; data span disjoint from every earlier span of those configurations (`GL.overlaps`, `:674-676`); declared before the run | nothing appended (span is not in the key) | +1 | +0 to the selection count; reported as validation |
| Same configs, other overlapping data (period, vendor, length) | all `config_id`s present; data hash differs; spans overlap | nothing appended | +1 | open question (section 12) |
| Cost sensitivity (withheld) | cost below the floor | new rows (cost is in `params`) | +1 | open question (section 12) |
| Synthetic | any `SYNTHETIC` source | nothing (`ui/strategy_lab_page.py:60-61`) | not counted | +0 |

Reasoning anchors. The deflated Sharpe ratio needs the number of trials actually tried and the dispersion of their
Sharpe ratios; under-counting trials inflates it (Bailey and López de Prado 2014). A run that produced no outcome
cannot have influenced a selection; that reading is ours, not a literature claim.

---

## 10. Reading existing ledgers (E1, C3, …) without rewriting them

- **Location.** `config.macro_dir()/ledgers/<FAMILY>.jsonl`, where `macro_dir()` is `QUANTGEN_MACRO_DIR` or
  `~/.nextgen/macro` (`config.py:176-178`; `ui/strategy_lab_page.py:67`; `paper_live/engine.py:104`).
- **Families that may exist on the owner's machine (UNVERIFIED):** Lab E1, E2, E3, E5, E8, C3, B3
  (`ui/strategy_lab_page.py:50-51`); C3 is also written by paper_live `trend` (`paper_live/engine.py:69`) and by
  CRY-1 (`docs/techfund_study.py:71`, `:459`); LAZYOWEN, QG-TACTICAL, QG-CORE (`paper_live/engine.py:69`);
  GROKTEAM-BOOK (`grokteam/book.py:64`); macro R-xx families (`gate_ledger.py:79`); paper-local `PAPER-<id>` under
  `papers/<id>/study/ledgers` (`tools/paper/study.py:159-160`).
- **Read-only calls.** `FamilyLedger(path).verify_chain()`, `.rows()`, `.hash()`, `.snapshot(h)`, `.n_raw`. None of
  them writes or creates the lock sidecar (probe).
- **Never** call `append`, `register_trial` or `TrialRegistry.register` on a production ledger from the registry or
  the comparison. Never `temp_copy(..., directory=<the ledger dir>)`. Use `GL.temp_copy(ledger)` (default
  `mkdtemp`, `:927-933`) for any what-if.
- **Separating writers inside a shared family.** Lab rows: `script == "ui/strategy_lab_page.py"` and `source`
  starting `"Strategy Lab: "` (`ui/strategy_lab_page.py:80-81`). Paper_live: `source` starting `"paper_live "`
  (`paper_live/engine.py:111`). CRY-1: `script == "docs/techfund_study.py"`. The Lab chip today shows the whole
  family's `n_raw`, all writers mixed (`ui/strategy_lab_page.py:82`, `:254`).
- **Pin what was read.** Store the `ledger_hash` and `n_raw` at read time; `snapshot(hash)` re-proves it later.
- **Broken chain.** `rows()` raises; report "ledger unreadable at line N" and stop. A repair is a rewrite; never do
  it.
- **Back-fill.** Each existing Lab row can become one registry entry of class `LEDGER_ONLY`, keyed by `config_id` and
  stored `row_md5`. The ledger tells the first span, first `run_utc` and anchor. It does not tell how many times the
  configuration ran, its results or its verdict; those stay null, never invented.
- **Anchors.** Rows written before the repository was under git carry `UNVERSIONED` (`paper_live/engine.py:64-68`).
  Step 3 refuses them for overlapping spans; a count of `N_raw` does not need anchors.

---

## 11. Tests that pin ledger behaviour

| Test | Pins |
|---|---|
| `tests/macro_m7_ledger.py:75-119` (T-LEDGER-01) | chain links, hash changes per row, snapshot, quick check is a row, re-run is the same trial, hash at run, tamper of last / middle / dropped line |
| `tests/macro_m7_ledger.py:125-149` | refusals (timing class, span, phase, `run_utc`, unknown field), null kinds append nothing, unanchored row is still a row, `repo_anchor` |
| `tests/macro_m7_ledger.py:155-162` | family filing by rule or correlation ≥ 0.5 |
| `tests/macro_m7_ledger.py:171-239` (T-NEFF-01) | `e(N)`, `n_equiv` round trip, clusters 5 on a 5×5 block panel, padding, `N_eff = max`, common-window rules |
| `tests/macro_m7_ledger.py:257-309` (T-STEP3-01, T-DSR-02) | inline deflated numbers, break-even N, units |
| `tests/macro_m7_ledger.py:315-343` (T-STEP3-02) | header refusals, static Kish / revision-count scan over `core`, `docs`, `config.py`, `main.py` |
| `tests/macro_m7_ledger.py:366-506` (T-SEL-01) | f = N_eff vs 1, anchors, SPEC versions, readings, own-row exclusion, max rule, five params = five configs, `config_id` ignores `run_utc`/`script`/`cost` (`:502`) |
| `tests/macro_m7_ledger.py:522-538` | adoption is a revision and a governance event, never a row |
| `tests/macro_m7_ledger.py:550-578` | seed files load; null value rows are not registrable (REFDATA, NOT_RUN) |
| `tests/macro_m7_ledger.py:584-593` | no wall clock, no `config` import in `gate_ledger.py` |
| `tests/macro_m7_integration.py:105-149` | card run registers three `timing_lag` rows; `ledger_hash_at_run` equals the stored hash |
| `tests/macro_m7_integration.py:199-230` | header commit records the family hash and `N_raw_at_registration` |
| `tests/macro_m8_forward.py:557-575`, `:641-650` | R-29 card row registered once; logged `variant` rows with `card_id None`, cost 50 |
| `tests/macro_tf_gov.py:171-184` (T-TF-GOV-02) | `TrialRegistry` dedup, global N with k-of-n composite = nᵏ, tamper refused |
| `tests/macro_m4_sleeves.py:202-212` | R-03 rows register only through `register_trial` |
| `tests/paper_live_acceptance.py:234-242` | one row per account; a re-run with another span appends nothing |
| `tests/paper_live_acceptance.py:333-344` | Lab: synthetic registers nothing; symbol case and order are not new configs; market `US` |
| `tests/paper_live_acceptance.py:347-357` | 5 threads × 10 rows keep the chain |

A registry built beside the ledger leaves all of these unchanged, because it does not edit `gate_ledger.py` and does
not change what the Lab passes to `register_trial`.

---

## 12. Hermeticity rules a new registry must follow

- **T-HERM-01** (`tests/macro_acceptance.py:52-71`, `:157-195`): inside the guard every network touchpoint raises
  (FRED, Yahoo, KIS, crypto, FMP, OpenDART, KRX, the shared session, raw sockets; the FICC cache TTL is 0). Registry
  tests must use in-memory or synthetic panels, never `load_history` against a vendor.
- **T-HERM-02** (`tests/macro_acceptance.py:25-27`, `:101-140`, `:198-207`):
  - the read-only trees `data/macro`, `core/rules`, `core/calendars/data`, `data/techfund`, `tests/fixtures/macro`,
    `docs/asset_expansion/cards` must be byte-identical. The registry and the comparison must never write a card file.
    `tests/macro_m7_cards.py:830-840` also pins the 34 legacy cards.
  - `~/.nextgen/macro`, `~/.nextgen/trading/rules.json` and `QUANTGEN_MACRO_DIR` must have no file added, removed or
    changed (path, size, `mtime_ns`). A default registry path under `macro_dir()` is therefore allowed only for real
    UI runs. Every test injects a `tempfile` directory (precedents: `tests/macro_m7_ledger.py:38-39`,
    `tests/paper_live_acceptance.py:236`, `:335`).
  - A `register_trial` on a real ledger creates a `.lock` file even on dedup (section 5). That alone would trip
    T-HERM-02.
- **Guard scope.** The aggregator wraps every `test_*` of `tests/macro_*.py` (`tests/macro_acceptance.py:216-234`) and
  `run_module` does the same for a single module (`:237-265`). A new `tests/macro_*.py` registry module is wrapped
  automatically. The snapshot is taken at the first macro test (`:145-153`).
- **Outside the guard.** `tests/expansion_acceptance.py:28-33`, `:338` runs `ui/strategy_lab_page.py` `__main__`
  in-process. Today those synthetic runs write nothing (`ui/strategy_lab_page.py:60-61`, `:320-330`). If the registry
  records synthetic runs, the self-check must not write to the default directory: inject the directory, or keep
  synthetic runs out of the production registry.
- **Design habits from the ledger:** no wall clock in the module (clock injected), no `config` import (directory
  injected), fail closed on a broken chain, a lock around read-verify-append.
- **Session rules:** never run `python tests/run_all.py` (it rewrites `qa/acceptance_results.json`). New test ids need
  rows in `tests/macro_registry.csv`; `sync_registry` rewrites that file (`tests/macro_acceptance.py:277-295`).

---

## 13. Findings and risks (numbered)

1. **F1 Data period invisible on re-runs.** `span` is not in `config_id`; a re-run on another period or vendor
   leaves no record (`gate_ledger.py:60-61`, `:343-346`). Only a registry can record it.
2. **F2 Cost-sensitivity runs inflate `N_raw`.** Lab puts `cost_bps` in `params` (`ui/strategy_lab_page.py:75-76`),
   so a withheld run below the floor adds new configurations.
3. **F3 Stage-dependent failure footprint.** Registration sits between the walk-forward and scoring
   (`ui/strategy_lab_page.py:116-127`).
4. **F4 `run_kind` has no effect on any count.** A future "valid experiments" count cannot be read from the ledger
   by kind.
5. **F5 `RegisterResult.row_md5` changes meaning** between append and dedup (`gate_ledger.py:346`, `:355`). Key on
   `res.row["row_md5"]`.
6. **F6 `step3` with `loader` raises before its fail-closed block** when a row lacks `diff_series_ref`
   (`gate_ledger.py:764-765` vs `:772-783`). Frozen; callers must pass `series=` or catch. Reported, not fixed.
7. **F7 Lock sidecar on every append** (`gate_ledger.py:247`). Any accidental production call leaves a file.
8. **F8 f uses all rows of a reading once one row touches the span** (`gate_ledger.py:725-731`). By design; worth
   stating in any comparison report.
9. **F9 Shared families.** C3 mixes Lab, paper_live and CRY-1 rows; the Lab chip mixes them too.
10. **F10 Strategy version is weak.** HEAD sha only, no dirty flag, no code hash (`gate_ledger.py:122-131`).
11. **F11 No series for Lab rows.** Only `N_raw` is available for Lab families; `N_clusters` / `N_equiv` need the
    registry to keep per-configuration return series (or a reproducible pointer).
12. **F12 Two N's disagree today.** The Lab deflates with `len(grid)` (`ui/strategy_lab_page.py:127`) while
    `validate.score_strategy` documents "every configuration ever tried (grid size plus revisions)"
    (`core/quant/validate.py:495-497`). R3 keeps the verdict as is and prints the ledger-based figure beside it.

---

## 14. Open questions for the owner

1. Does a run of the same configurations on **overlapping but different data** (another period, vendor or length)
   add experiments? The ledger says no. A strict reading of selection bias says it can.
2. Does a **cost-sensitivity run** (withheld, below the floor) count as an experiment? The ledger counts it today.
3. Does a **failed run that already registered rows** count? The ledger keeps the rows; the proposal prints both
   counts.
4. Which code files define the **strategy version** hash (the three named in section 8, or the whole harness list of
   `gate_package.py:36-38`)?
5. For a ledger-based `validate.deflated_sharpe`, which **trial dispersion** goes with the larger N: the current
   grid's (`validate.py:503-506`) or the dispersion across all registered configurations (which needs stored
   series)?
6. Should the registry live beside the ledgers (`macro_dir()/ledgers/` sibling) or in its own directory? Either way
   tests inject a temp directory.

---

## References

- Bailey, D. H., and López de Prado, M. (2014). The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest
  Overfitting, and Non-Normality. *Journal of Portfolio Management* 40(5), 94–107.
  https://doi.org/10.3905/jpm.2014.40.5.094 — the DSR needs the number of trials and the variance of their Sharpe
  ratios. (DOI not re-fetched this session: UNVERIFIED link; the equation number "eq. 9" cited in
  `gate_ledger.py:469` for the linear N̂ is UNVERIFIED.)
- Bailey, D. H., Borwein, J. M., López de Prado, M., and Zhu, Q. J. (2017). The Probability of Backtest Overfitting.
  *Journal of Computational Finance* 20(4), 39–69. https://doi.org/10.21314/JCF.2016.322 — CSCV / PBO, used by
  `validate.pbo_cscv`. (DOI not re-fetched: UNVERIFIED link.)
- López de Prado, M., and Lewis, M. J. (2019). Detection of False Investment Strategies Using Unsupervised Learning
  Methods. *Quantitative Finance* 19(9), 1555–1565. https://doi.org/10.1080/14697688.2019.1622311 — clustering
  trials to estimate an effective number of independent trials. `gate_ledger.n_clusters` uses fixed-cut average
  linkage, not that paper's algorithm. (DOI not re-fetched: UNVERIFIED link.)
- Harvey, C. R., and Liu, Y. (2015). Backtesting. *Journal of Portfolio Management* 42(1), 13–28.
  https://doi.org/10.3905/jpm.2015.42.1.013 — Sharpe-ratio haircuts grow with the number of tests. (DOI not
  re-fetched: UNVERIFIED link.)
