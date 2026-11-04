# QUANTGEN: Product & Engineering Improvement Audit

**A PentPort-informed, repository-grounded strategy and implementation roadmap**  
**Review date:** 29 October 2026 (Asia/Seoul)  
**GitHub:** `xkg4real/quantgen`, `main`, observed HEAD `e28035fed8d19ce33b2e83d18e7d1abc21b28037`  
**Review basis:** public PentPort landing page and policies; GitHub repository source, README, acceptance results, active Nautilus roadmap and calendar manifest. **Read-only assessment; no code was modified.**

> **Core judgment:** QUANTGEN's bottleneck is not a shortage of quantitative models. It is the conversion of an impressive but fragmented research codebase into a coherent, traceable, reliable, usable workflow. PentPort is a benchmark for product clarity and accessibility, not evidence that its financial engines are technically superior.

## 1. Decision in one page

**Recommended positioning:** “QUANTGEN is a research operating system for quantitative finance: inspect data, formulate hypotheses, test strategies, evaluate model validity and risk, and export reproducible evidence.” Leave all real-money order routing to the separate TRADEGEN system; make any eventual companion application a read-only consumer of approved research outputs.

**Five highest-impact moves:**

1. **Close known correctness issues before UX expansion.** Complete the already-planned NautilusTrader independent backtest bridge, pre-run trial accounting, instrument/cost-class validation and vendor cross-checks. Do not replace existing validation gates or silently change a decision criterion.
2. **Create a single, generated status source.** Distinguish code-complete, hermetic-test PASS, reference-data NOT_RUN, formal-gate PASS, dry-run, paper study and public-release ready. Make README, UI, report headers and tests consume the same authoritative status records.
3. **Replace feature-first navigation with workflow-first navigation.** Organize the current 16 sidebar entries into Research Home, Markets, Build & Test, Risk & Portfolio, Research Library and System; retain all existing analytical pages inside their appropriate workspaces.
4. **Make a complete research run the main product object.** Each run should have a stable ID, data vintage and adjustments, assumptions, code commit, model/gate version, costs, seeds, baseline, verdict and exportable reproducibility pack. Existing ledgers, model cards and artifacts are the starting point.
5. **Treat public distribution as a separate gated project.** The October 27 roadmap records an intention to distribute free before potentially monetizing, while the current README still states personal-use only. Resolve the contradiction with legal/data-license review and a deliberate product boundary; do not ship QUANTGEN itself as a brokerage or advice service.

**What not to build now:** leaderboards, prizes, a social network, a U.S. payment-for-order-flow brokerage, real-order APIs in QUANTGEN, a new backtest engine replacing all existing engines, or another volatility model without an admissible comparative study.

## 2. What PentPort demonstrates—and what it does not prove

**Verified public product signals:** The PentPort landing page presents a single consumer promise (sharing order-flow revenue), a four-step interactive cost estimator, a claim that paper-trading competitions and leaderboards are live, visible audience navigation (Quants, HFT, Students, Educators, Advisors), and marketing for an API/Python package. Public competition rules describe simulation-only contests, ranking integrity, anti-abuse requirements, identity eligibility and corrections to inaccurate marks. A package named `pentport` is listed in the Python package ecosystem.

**Important limits:** I did not authenticate into PentPort, run its trading application, test its API/SDK, measure execution quality or inspect its private infrastructure. Marketing text and policy statements are evidence of positioning and commitments, not independent proof of latency, technical depth, security or actual returns. The planned brokerage is not equivalent to an operational, licensed broker. Do not copy PentPort's specific economics or use its claims as validated financial metrics.

| Product dimension | PentPort public presentation | QUANTGEN observed code | Actionable lesson |
|---|---|---|---|
| Primary promise | Immediately legible retail-trader economics | Precise but broad technical research identity | Publish one main use case, with evidence-based examples |
| First-run experience | Cost calculator and clear call-to-action | 16 specialized top-level navigation entries; defaults to Macro | Build guided onboarding and Research Home |
| User segmentation | Quants, HFT, students, educators, advisors | Primarily one expert/operator desktop persona | Separate novice explanation, researcher and operator views; do not duplicate calculation engines |
| Community | Competitions and leagues are advertised | Personal research workflows and simulated accounts | Optional later, not a current priority |
| Research depth | Cannot verify advanced research functions from public pages | FICC, asset research, scenario models, Monte Carlo, risk, gates and validation | This is QUANTGEN's differentiator—surface it coherently |
| Programmatic use | API/Python package advertised | Python package and internal APIs; no external service contract verified | Introduce a versioned **read-only** research artifact/SDK interface |
| Results integrity | Contest rulebook describes audit and correction powers | Formal validation, refusals, data provenance and frozen studies | Make trust mechanics visible to the user |
| Public readiness | Product website and policies | Personal-use, non-distribution README; separate future-market roadmap | Decide distribution scope before building public authentication/billing |

**The core benchmark:** PentPort reduces the number of decisions a newcomer must make to receive value. QUANTGEN should reduce the number of pages, data assumptions and research steps an analyst has to manage to reach a defensible result.

## 3. Repository audit: implemented strengths and observable gaps

### 3.1 Strengths worth preserving

- `core/ficc/` implements curves, bonds, rate/FX derivatives, options, structured products, risk and scenario analysis. `core/quant/` implements Monte Carlo, GARCH, strategy simulation, walk-forward validation, risk overlays, model cards, trial records and refused outcomes.
- `main.py` instantiates the Flet desktop application and its 16 sections. Analysis pages already share UI components and a consistent local narrative/deep-analysis panel (`ui/ai_panel.py`). Do **not** throw away the page implementations.
- `core/engine/` has simulated orders, persistent states and audit decisions; the research repository deliberately has no live-broker order path. `paper_live/` contains a separate paper-study harness.
- `core/quant/validate.py` already includes no-lookahead walk-forward procedures, DSR/PBO, cost sensitivity and distributional calibration checks. The macro gate uses explicit `NOT RUN`, `INSUFFICIENT DATA`, refusal and protective dispositions rather than pretending that every backtest is valid.
- The repository contains frozen studies, an experimental model-card registry, point-in-time macro contracts, regression fixtures and a broad test suite. Rebuilding these from scratch would create unnecessary risk.

### 3.2 Evidence and limitations as of the reviewed HEAD

| Finding ID | Observation | Why it matters | Evidence |
|---|---|---|---|
| F-01 | `qa/acceptance_results.json` contains **749 PASS / 121 NOT_RUN / 0 FAIL** over 870 recorded cases. README still reports 743 PASS / 121 NOT_RUN over 864. | A user cannot tell which snapshot is authoritative. Neither record represents a new test run performed by this audit. | `qa/acceptance_results.json`; `README.md` Verification |
| F-02 | Current `core/calendars/data/MANIFEST.yaml` identifies a signed owner-approved calendar set v1.0.0 with a 2026-10-29 timestamp; README still describes calendars as unsigned. | Operational readiness claims are contradictory. Signing the calendars does **not** by itself unblock missing reference datasets or formal research gates. | Calendar MANIFEST; `README.md` Data limitations |
| F-03 | Macro documentation reports the gate package as `NOT_FROZEN`, formal macro cards as not run, and upstream data/owner blockers. | Many research artifacts are indicative rather than formally admissible recommendations. Revalidate status against the current code and fresh data before presenting it. | `README.md` Macro integration, Card status |
| F-04 | `ui/strategy_lab_page.py` writes trial records but invokes `score_strategy(..., n_trials=len(grid))`; it does not use the historical trial count for scoring. | Multiple-testing corrections may understate cumulative research attempts. The owner's R3 decision requires **parallel output and approval before criterion changes**, not a blind switch. | Strategy Lab source; October 27 roadmap ②-6, ⑨-3a–d |
| F-05 | `cost_class('BTCUSD')` can fall through to the U.S.-equity symbol heuristic; the existing roadmap already flags this defect. | A misclassified instrument can receive incorrect assumed costs. Build canonical instrument IDs and table-driven provider aliases. | `core/quant/validate.py`; `core/quant/history.py`; October 27 roadmap |
| F-06 | `pyproject.toml` has package version `2.0.0` while README describes expansion versions 2 and 3, and packages only `core*`, `data*`, `ui*` without an explicit artifact-data contract. | Version ambiguity and potential missing bundled model cards in an installed build; this is a packaging **risk to test**, not a confirmed install failure. | `pyproject.toml`, UI references to `docs/asset_expansion/cards` |
| F-07 | No `.github/` entry appeared in the reviewed root directory. | A checked-in GitHub Actions CI workflow was not visible; check external workflow settings before declaring CI absent. | Root repository contents |
| F-08 | The existing roadmap already covers Nautilus independence, model limitation register, known-issues consolidation, ledger accounting, market-data parity and legal review. | Avoid redundant work and competing roadmaps. Extend existing IDs and references. | `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` |
| F-09 | Data load can explicitly fall back to labeled `SYNTHETIC` and distinguishes adjustment/source in `History`; however market datasets differ in dividend treatment and timestamp conventions. | Provenance must remain attached through every result and prevent synthetic/partial data from acquiring formal status. | `core/quant/history.py`; `README.md` Data sources |
| F-10 | AI analysis receives structured computed values via `ui/ai_panel.py`; core deterministic narrative remains available without an API key. | Preserve grounded AI architecture; add source links and refusal-aware answer constraints instead of giving the model raw authority. | `ui/ai_panel.py` |

### 3.3 Maturity is not a single score

**Code presence** ≠ **unit-test PASS** ≠ **data-qualified dry run** ≠ **formal out-of-sample PASS** ≠ **pilot paper result** ≠ **public-release authorization**.

Create separate readiness lanes. In particular, 121 NOT_RUN cases are not equivalent to 121 defects, but they are evidence gaps. A default screen should never compress these states into one green “ready” label.

## 4. Recommended product model and information architecture

### 4.1 North-star workflow

```
RESEARCH QUESTION
   ↓
INSTRUMENT + DATA VINTAGE  → source quality / adjustment / calendar / license
   ↓
HYPOTHESIS + BASELINE     → preregistration / trial identity / parameter grid
   ↓
BACKTEST + INDEPENDENT CHECK → vectorized QUANTGEN vs Nautilus (eligible cases)
   ↓
VALIDATION & UNCERTAINTY → OOS, costs, multiple tests, calibration, refusals
   ↓
RISK REVIEW              → exposure, VaR/ES, drawdown, stress, capacity
   ↓
SIMULATED OBSERVATION    → paper only; separate frozen evaluation
   ↓
EVIDENCE PACKAGE         → run ID, sources, charts, verdict, limitations, export
          └── read-only consumer interface → companion app / TRADEGEN evidence intake
```

The central artifact is a **ResearchRun**, not an individual sidebar page. One run may call multiple existing calculation modules and produce a traceable set of outputs.

### 4.2 Proposed navigation: six workspaces, existing pages retained

| New workspace | Pages / actions inside it | Default question it answers |
|---|---|---|
| Research Home | Latest run, unresolved gates, provider status, compare two runs, quick-start templates | “What can I trust and work on next?” |
| Markets | Macro, Rates, Bonds, FX, Derivatives, ETF, Crypto, KRX | “What is happening and what data supports it?” |
| Build & Test | Strategy Lab, Signals, experiment wizard, backtest, paper-run records | “Does this strategy survive skeptical testing?” |
| Portfolio & Risk | Portfolio, Quant Lab, scenarios, risk overlay, stress comparison | “How can the strategy fail and how large is the risk?” |
| Research Library | Model cards, limitation register, run history, rejected hypotheses, source inventory, papers | “What has been tested, rejected, revised or proven?” |
| System | Data/credential health, signed calendars, version, tests, settings | “What is reliable and correctly configured?” |

Preserve `Structuring` under Markets / FICC and show the inherited `Execution` and `Rules` pages only in an explicitly labeled **Simulation Tools** sub-area. Do not make “Execution” look like a live broker connector. Keep expert quick-navigation (search / keyboard shortcut) as an alternative.

### 4.3 Two UX modes, one calculation engine

**Researcher mode:** full statistics, model parameters, data series, PBO/DSR, gate versions, source provenance and reproducibility controls. **Explain mode:** the same run shown as five panels—question, evidence, assumptions, potential failure, decision. The simplified mode must never hide a REJECT/NOT_RUN status or silently replace a data series.

A typical Strategy Lab result should lead with “NOT RUN — reference data missing”, “REJECT — fails 2x cost sensitivity”, or “PASS — bounded to this sample and cost assumption,” followed by detailed confidence intervals. Model performance must be framed as sample evidence, not guaranteed returns.

## 5. Target architecture: evolve, do not rewrite

```
                   Flet DESKTOP UI / future READ-ONLY companion
                       │  versioned query + export contracts
                       ▼
               RESEARCH WORKFLOW ORCHESTRATOR (new)
            Study / Run / Trial / Verdict / Artifact IDs
                  │                │                │
                  ▼                ▼                ▼
             DATA CATALOG      QUANT + FICC     VALIDATION / GATE
             source contracts  existing cores    existing model cards
             PIT + adjustment  models and sims   + append-only ledger
                  │                │                │
                  └──────────────┬─┴────────────────┘
                                 ▼
                      IMMUTABLE RUN BUNDLE (new)
            inputs + hashes + code SHA + seed + costs + results
                                 │
                  ┌──────────────┴─────────────┐
                  ▼                            ▼
           QUANTGEN paper study       read-only export/SDK
                                             │
                                        TRADEGEN boundary
                                 (no QUANTGEN live-order path)
```

**Implementation guidance:** Add an orchestration/contract layer around `core/quant`, `core/ficc`, `core/engine`, `data` and `docs` rather than moving their frozen or version-pinned implementation files. A FastAPI service is not a prerequisite; begin with an internal Python API and signed local JSON/Parquet exports. A future external HTTP API should be added only when a clear consumer and permission model exist.

**Proposed minimum JSON run manifest** (illustrative schema, not an existing format):

```json
{
  "schema_version": "research-run/1.0",
  "run_id": "...", "study_id": "...", "research_question": "...",
  "created_utc": "...", "code_commit": "...", "environment_lock_hash": "...",
  "data": [{"instrument_id": "KRX:069500", "source": "KIS", "as_of_utc": "...", "adjustment": "split", "dataset_sha256": "...", "tier": "vendor"}],
  "method": {"model_id": "...", "model_version": "...", "seed": 11, "baseline_id": "..."},
  "costs": {"model_id": "...", "per_side_bp": 3.0, "stress_multiplier": 2.0},
  "governance": {"gate_package_hash": "...", "trial_ledger_id": "...", "trial_count_method": "registered-v1", "holdout_status": "..."},
  "result": {"status": "NOT_RUN", "reason_code": "REFERENCE_DATA_MISSING", "artifact_hashes": []},
  "integrity": {"signature": null, "export_policy": "read_only"}
}
```

**Contract invariants:** No `PASS` without passing the designated frozen gate; no `OFFICIAL` label on vendor or synthetic data; no overwriting immutable run outputs; no unstated changes to cost classes; no automatic promotion of TRADEGEN observations into a QUANTGEN training set; no credentials, private account numbers or secret values in exports.

## 6. Prioritized implementation backlog

**Labels:** `P0` = integrity and release blockers; `P1` = high-value product/workflow; `P2` = useful expansion after proof. Effort is a **rough relative planning band** for a small team (S ≈ 1–2 focused workdays, M ≈ 3–10, L ≈ 2–4 weeks), **not a delivery promise**. `Existing` marks tasks already present in the October 27 roadmap. Finish or reconcile those IDs instead of starting duplicates. All work should occur in new branches; do not mutate frozen study tags, gate packages or original ledgers.

### P0. Integrity and foundational correctness

**QG-P0-01 — Release/status reconciliation [S; new].** Implement a generated `research_status.json` / structured status report based on test run, calendar `MANIFEST.yaml`, gate package, data contracts and owner decisions. Update README/Research Home from it. **Touch:** `README.md`, `qa/`, `core/calendars/data/MANIFEST.yaml`, new `tools/status/`, future `ui/home_page.py`. **Acceptance:** status summary agrees with actual QA file (749/870 recorded at the audited snapshot); signed calendars are correctly shown; macro formal gate remains NOT_FROZEN until truly changed; contradiction check fails CI.

**QG-P0-02 — Canonical instrument identity and cost mapping [M; existing ②-4 + ⑨].** Separate instrument identity (`asset_class`, `venue`, `native_symbol`, `currency`, `contract`, `cost_class`) from provider aliases. Explicitly test `BTCUSD`, `BTC-USD`, `BTCUSDT`, `KRW-BTC`, `NAS:AAPL`, `005930`, index futures and unknown symbols. Unknowns **fail closed**; don't guess a cheaper fee. **Touch:** `core/quant/validate.py`, `core/quant/history.py`, `core/quant/instruments.py`, `core/markets.py`, corresponding tests. **Acceptance:** table-driven alias/cost tests pass; `BTCUSD` never maps to `us`; reported cost tier matches the canonical object.

**QG-P0-03 — Experiment/trial accounting dual-run [L; existing R3 ②-6, ⑨-3a–d].** Record a pre-evaluation run-intent and trial-configuration family identity; use idempotent append-only records and classify reruns, invalid runs, parameter searches and genuine independent replications. Produce **both** old grid-count and new cumulative-trial statistics for owner review. **Touch:** `ui/strategy_lab_page.py`, `core/quant/gate_ledger.py`, `core/quant/validate.py`, roadmap R3. **Acceptance:** concurrent run IDs unique; same retry idempotent; no result is promoted before intent registration; old verdict remains unchanged until approved; diff report explains every changed verdict.

**QG-P0-04 — NautilusTrader independent parity [L; existing ③–⑦].** Complete the bridge already approved in spec rev 6, isolated venv, no live clock or network orders, deterministic fixtures, 1x/2x costs and paired strategy results. Use **the current design specification's acceptance bars**, not thresholds invented in this report. **Touch:** `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, `tools/nautilus/` (proposed), `tests/`. **Acceptance:** T-RO-01 security guard accepted by the owner; synthetic fixtures replay reproducibly; SPY pilot first, BTC pilot only after SPY passes; do not merge without the roadmap's owner signoffs.

**QG-P0-05 — Data provenance and provider parity [M; existing ⑤-2, ⑨-2].** Add dataset fingerprints, retrieval/vintage timestamps, corporate-action adjustment, timezone/calendar, license and source freshness to every backtest input; compare the exact SPY/BTC pilot samples across independent providers and produce dates of disagreement. **Touch:** `data/`, `core/quant/history.py`, `core/ficc/pit.py`, catalog artifacts. **Acceptance:** mixed adjustment conventions get a visible refusal or unambiguous conversion; any missing official/reference data yields NOT_RUN; vendor disagreements report exact dates and magnitude before pilot.

**QG-P0-06 — Formal-gate blockers register [M; existing ⑨-2, ⑨-5].** Make each NOT_RUN test/card link to a distinct missing dataset, credential, owner input, legal entitlement, signed calendar or unbuilt dependency; calculate blockers *without* treating NOT_RUN as failure or PASS. **Touch:** `tests/notrun.py`, `tests/run_all.py`, `docs/macro_overlay/`, `ui/macro_cards_view.py`. **Acceptance:** all recorded 121 NOT_RUN entries have typed reasons and next steps; no macro card is labeled deployable until formal gate evidence exists.

**QG-P0-07 — Build/package smoke in a clean machine [M; new].** Test wheel/Windows standalone packaging for package data including `docs/asset_expansion/cards`, macro rules, calendar YAML, assets/icons, model primers and manifests. Align release number with capability and artifact schema versions. **Touch:** `pyproject.toml`, build process, new `tests/packaging_acceptance.py`. **Acceptance:** fresh clean Windows venv launches all workspaces with no secrets/network; static assets exist; no silent fallback to an empty cards directory; version appears on the System page.

**QG-P0-08 — CI with explicit environment tiers [M; new].** Add a checked-in GitHub Actions workflow (no `.github/` observed at audit), test matrix of hermetic Linux and Windows guards, isolated dependencies, schema checks, doc/status reconciliation and audit artifacts. Keep data-bound tests labeled NOT_RUN rather than faking datasets. **Touch:** `.github/workflows/`, `tests/run_all.py`, pins. **Acceptance:** PR blocks merges on FAIL; NOT_RUN count and reasons displayed; no network/secret tokens in hermetic runs; published results are tied to commit SHA. Never overwrite of-record local run files.

**QG-P0-09 — Distribution and entitlement gate [M; existing ⑩-1].** Before any public-facing pilot, commission current Korean legal review (personalized/advisory features, advertising, paid plans, signals, data redistribution) and per-provider licensing; separately review U.S. access if planned. **Touch:** release decision record, `README.md` Regulatory note, data-license register, companion app policy. **Acceptance:** written scope, no-go features, data license matrix, privacy/security requirements and owner signoff; read-only educational/research output is not assumed exempt merely because free.

### P1. Product experience and operating system

**QG-P1-01 — Research Home and guided first run [M; new].** New home view: one “Start research” CTA, three canned questions (SPY vol forecast; KRX ETF momentum; USD rates curve shock), recent runs, blockers, and honest data-tier banner. **Touch:** `main.py`, new `ui/home_page.py`, existing page builders. **Acceptance:** a fresh tester can complete an end-to-end synthetic example with no API key; the synthetic badge is persistent and cannot be misinterpreted as an investment signal.

**QG-P1-02 — Workflow-first navigation [M; new].** Group the existing 16 tabs into six workspaces without deleting analysis pages; allow command-palette search and favorites for expert users. **Touch:** `main.py`, `ui/components.py`. **Acceptance:** every existing page remains reachable; navigation survives a running simulation; automated tests assert all routes and no accidental engine resets.

**QG-P1-03 — Reproducible ResearchRun bundle [L; new].** Provide a stable object that composes existing ledger/run cards/artifacts: environment, datasets, model parameters, gates, seeds, costs, charts, interpretation, failure reasons. Export JSON + human report in a folder with hashes. **Touch:** new `core/research/run_contract.py`, `core/research/export.py`, adapters to existing modules. **Acceptance:** same frozen inputs produce byte-identical canonical data artifacts (excluding explicit wall-clock fields); changed code/data is detected and the comparison refuses to treat runs as equivalent.

**QG-P1-04 — Model Evidence Card v1 [M; partially existing ②-3].** Extend existing cards, not duplicate, with intended use, excluded use, assumptions, estimates, sample vintage, calibration, reference benchmark, known tail failure, cost sensitivity and gate status. **Touch:** `core/quant/cards.py`, `docs/asset_expansion/cards`, future `ui/model_evidence.py`. **Acceptance:** user can open every model's limitations from the result screen in one click; PASS/NOT_RUN/REJECT reason is visible without color dependence.

**QG-P1-05 — Run history and comparison explorer [M; new].** Add comparison view for same research question across model version, dataset or cost stress, with changed inputs highlighted, ΔSharpe/Δdrawdown and confidence interval clearly labeled. **Touch:** research run storage and `ui/research_view.py`. **Acceptance:** compare rejects “apples to oranges” when currency, adjustment or holdout split differs, unless explicitly marked exploratory.

**QG-P1-06 — Unified risk cockpit [M; new aggregation].** Reuse Quant Lab, Portfolio, scenario library and macro risk results to show correlated exposures, drawdowns, VaR/ES and scenario losses in one panel with time horizon/measure visible. No new prediction algorithms in first cut. **Touch:** `ui/portfolio_page.py`, `ui/quant_lab_page.py`, `core/quant/risk_layer.py`, `core/quant/scenarios.py`. **Acceptance:** every number links back to a reproducible calculation and its historical calibration status.

**QG-P1-07 — Honest performance/progress UX [M; new].** Add cancellable background jobs, progress stage, elapsed time, data-source retry rationale, cache hit, approximate runtime plan and last valid output; ensure no stale result silently replaces fresh output. **Touch:** UI page builders, common task controller, `data/net.py`. **Acceptance:** user can cancel a Monte Carlo/backtest without corrupting ledgers; switch tabs during run; retry status and cancellation appear on screen; cross-thread UI updates pass the Flet guard suite.

**QG-P1-08 — Read-only research SDK contract [L; new, gated].** Expose `list_runs`, `get_run`, `get_model_card`, `get_status`, `verify_artifact` over versioned local Python functions/exports. Add HTTP only after consumer requires it. **Touch:** new `quantgen_api/` or `core/research/api.py`. **Acceptance:** no order/withdrawal/secret path; schema compatibility tests; consumer can reproduce/verifiably parse output on a clean environment without importing Flet.

**QG-P1-09 — TRADEGEN feedback quarantine [M; existing ⑪-1].** Implement an explicit one-way research export with a read-only consumer, and a **separate** observational feedback report. New QUANTGEN experiments prompted by observations require pre-registration and new evaluation data. **Touch:** split-map contract, new export adapter (not TRADEGEN execution code). **Acceptance:** permission tests prove TRADEGEN cannot write QUANTGEN's trial ledgers or mutate frozen studies; observational feedback cannot relabel the old holdout.

**QG-P1-10 — User testing & copy clarity [S then recurring; new].** Test 5–8 representative users from the eventual intended audience without offering advice or distributing restricted market data. Ask them to identify data tier, expected output, assumptions, confidence and next action. **Touch:** prototype, user-test scripts, content. **Acceptance:** ≥80% correctly distinguish vendor/synthetic and formal/not-run on first encounter; median time to first example under 5 minutes in an instrumented pilot. These are *proposed product targets*, not current measurements.

### P2. Conditional expansion

**QG-P2-01 — Scenario Storyboard [M].** Linked FICC/equity stress “what changes if 2y/10y, FX and vol move?” using current pricing and scenario engines, with decomposed drivers and no invented macro causality. **Acceptance:** cross-check P&L legs reconcile to standalone calculators and clearly separate pricing measure from physical forecast.

**QG-P2-02 — Teaching/explainer templates [M].** Public-facing teaching mode with signed synthetic fixtures and one example per asset class; promote only after the legal/data license gate. **Acceptance:** fixtures can be run offline, are never mixed with real trading results and include written assumptions.

**QG-P2-03 — Product analytics and opt-in privacy controls [M; gated].** Only for a public companion app, capture privacy-minimized events for onboarding/task completion, not raw portfolios or sensitive query payloads by default. **Acceptance:** explicit retention/deletion policy, consent and access controls; no personal telemetry in the private research desktop by default.

**QG-P2-04 — Public community/simulated challenges [L; defer].** Revisit only if user research proves community learning is essential and contest governance/compliance is affordable. Requires fraud, eligibility, fairness, data correction and competition-rule operations akin to PentPort's published rules. **Acceptance:** separately scoped legal and anti-abuse program. Otherwise, do not build.

**QG-P2-05 — Brokerage economics / PFOF [out of scope].** PentPort's proposed revenue-sharing economics are not a research advantage. QUANTGEN should not adopt U.S.-specific brokerage incentives or order routing as a proxy for product maturity.

## 7. Implementation sequence that respects the current roadmap

| Stage | Main deliverable | Existing workstream / dependency | Exit gate |
|---|---|---|---|
| 0 — Reconcile truth | Status generator, current QA/README consistency, model/blocker inventory | Calendar signing has progressed; keep existing frozen records | Every surfaced status agrees with machine-readable record |
| 1 — Fix foundations | Costs/symbol canonicalization; trial ledger design; independent Nautilus parity; pilot data cross-check | Existing ②-3, ②-4, ②-6, ③–⑦, ⑤-2 and ⑨-3 tasks | Owner-approved parity and research criteria; no silent verdict changes |
| 2 — Integrate experience | ResearchRun contract, six workspaces, guided workflow, evidence cards | Reuse `core/quant`, `core/ficc`, existing UI and model cards | One complete reusable end-to-end example in a clean environment |
| 3 — Separate app | Read-only local SDK or exported bundle; optional external UI | Existing ⑩-2 and ⑪-1 | Boundary guard passes; reports are verifiable without QUANTGEN internals |
| 4 — Public pilot | Legal/data entitlements, packaging, privacy, accessibility, pilot user testing | Existing ⑩-1 and owner signoff | Written legal/data release signoff + pilot UX targets met; otherwise internal only |

**Conflict-avoidance instructions:** Before opening a new issue or coding, check `CLAUDE.md`, the `handoff` branch's current task/ledger and `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md`. Do not duplicate a task already owned by Claude or Codex. Do not push directly to `main` or edit `studies-of-record-2026-10-23`/frozen fixtures. All research gates and criterion changes require owner-approved decisions.

## 8. Proposed measurement dashboard (targets, not observed results)

| Measurement | Why it matters | Initial target / rule |
|---|---|---|
| Truth consistency | Wrong status destroys trust | 0 contradictory status claims across UI, README, QA and manifest |
| Auditability | Every claim has origin | 100% exported runs contain code SHA, data source, vintage, cost, seed and gate version |
| Provenance labels | Prevent synthetic/live confusion | 0 unlabeled synthetic, provisional or license-restricted results |
| Formal admissibility | Prevent unsupported advice/signal promotion | 0 PASS without frozen gate and required reference inputs |
| Experiment accounting | Contain selection bias | 100% real-data experiment intents registered before result scoring |
| Backtest parity | Cross-engine confidence | All eligible pilot cases pass the Nautilus spec's stated bars |
| Reproducibility | Make runs comparable | 100% hash matches for deterministic same-input goldens |
| User comprehension | PentPort-like clarity | ≥80% first-time testers can distinguish run status and evidence tier |
| Time to first value | Reduce onboarding cost | Median < 5 minutes to a fully labeled example, measured in pilot |
| Packaging | Make demos trustworthy | Clean install opens every core workspace without private config |
| Operational safety | Preserve research/live split | 0 QUANTGEN live broker routes, 0 credential leaks, 0 TRADEGEN writes to research ledger |

Do not set a performance SLA or promise a model's Sharpe ratio until a representative workload, hardware baseline and admissible datasets are defined. Operational targets should be established through profiling, not selected to look attractive on a marketing page.

## 9. Implementation starting package: the first six pull requests

1. **PR-A `status-source-of-truth`:** machine-readable QA/calendar/gate readiness snapshot + status consistency tests; no numerical model change.
2. **PR-B `instrument-identity-cost-audit`:** alias mapping, cross-venue cost classification and regression test for `BTCUSD`, based on the existing issue register; do not change approved cost values without a governance decision.
3. **PR-C `ledger-r3-shadow`:** pre-run intent + dual-output cumulative trial count; old verdict remains authoritative until owner decision ⑨-3d.
4. **PR-D `run-contract-v1`:** schema only and adapters, no UI rewrite; export one real-data or explicitly synthetic example with full provenance.
5. **PR-E `research-home-shell`:** six-workspace router + Home, reuse all existing views, 3 guided examples, visible status and provider-tier labels.
6. **PR-F `packaging-ci-smoke`:** reproducible clean install, offline UI smoke, README/generated status check, documentation, no release or live-network side effects.

**Dependency order:** PR-A and PR-B may be independent; PR-C must follow owner R3 design; PR-D should use the validated instrument IDs; PR-E uses PR-A/PR-D statuses; PR-F runs throughout and becomes a merge gate. The existing Nautilus bridge can proceed in parallel on its approved branch without conflicting with the UI redesign.

## 10. Risks, rejected shortcuts, and owners' decisions

| Risk / tempting shortcut | Recommended handling |
|---|---|
| “Add more AI predictions” | Do not promote AI wording to a signal; all numerics are computed deterministically with cited assumptions and calibration. |
| “Green means ready” | Separate code PASS, reference-data NOT_RUN, gate PASS, indicative and release authorization. |
| “Just use more market data” | Track contractual entitlement, data vendor, adjustment, vintage and effective timestamp before scaling ingestion. |
| “Replace Flet with an entirely new frontend now” | Not justified by the evidence. First validate workflows and exports within Flet; consider PyQt/web only with measured UX/performance requirements. |
| “Nautilus should replace the original engines” | Current roadmap uses it as independent comparator. Preserve research engine invariants and frozen record boundaries. |
| “TRADEGEN P&L proves a QUANTGEN model works” | It is observational evidence, not a new blinded holdout; register changes as new trials and preserve quarantine. |
| “Make QUANTGEN public because PentPort is public” | Product/marketing decision is separate from legal authority, market-data redistribution and investment-advice restrictions. |
| “Social trading will make QUANTGEN competitive” | Community features only matter if validated target users need them; they create extensive fairness/compliance operations. |

**Decisions requiring explicit owner approval:** final target persona for any public companion; whether to distribute QUANTGEN itself or only read-only approved outputs; the R3 cumulative-trial scoring criterion; any changes to model gates or frozen holdouts; signed data licenses; the regulatory release opinion; any live trading functionality exclusively on the TRADEGEN side.

## 11. Final recommendation

**Position QUANTGEN as an evidence-first research operating system, not as a weaker copy of PentPort.** Its defensible advantage is the breadth of finance analytics joined to transparent experimental discipline: models that refuse to overclaim are a product feature. PentPort's lesson is packaging: an understandable starting point, a compelling user journey, audience-sensitive presentation and an API surface that makes the value accessible.

**Do first:** reconcile conflicting status sources, finish known integrity work, and demonstrate one end-to-end research run whose inputs, gate, costs, limitations and results are independently reproducible. **Do second:** build the workflow shell and read-only export interface. **Do last:** evaluate commercial distribution, new product surfaces and social features only with user evidence and legal clearance.

## 12. Codex / Claude handoff: bounded first implementation task

The following text is designed to be copied into a **new, authorized coding session**. It is intentionally smaller than the overall roadmap; its purpose is to establish a reliable baseline without overlapping the Nautilus bridge or changing quantitative conclusions.

> Read `CLAUDE.md`, the live `handoff` branch record and `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` before editing. Respect existing ownership and freeze rules. Work only on a new branch. First inspect current `main`; do not assume the audit snapshot is still current. Propose the smallest PR to establish a generated status source (QG-P0-01). It should reconcile the repository's recorded test totals, signed calendar manifest, macro gate/package status and open prerequisite reasons into a machine-readable, read-only report; no external network calls, no broker orders, no trial scoring changes and no modification of studies-of-record artifacts. Add tests that fail on contradictions between generated status, README assertions and UI readiness labels. Use fixtures for offline validation. Show before/after evidence and the exact test commands/results. Do not merge, push to `main` or change any protected criterion without explicit owner approval. If there is a collision with another agent's task, stop and report the conflict rather than proceeding.

**Definition of done for the first PR:**

1. The status model has documented fields for `code_test`, `data_readiness`, `formal_gate`, `paper_study`, `distribution_policy` and timestamp/source provenance.
2. It distinguishes PASS, FAIL, NOT_RUN, INDICATIVE and NOT_FROZEN; it never collapses them into a single readiness boolean.
3. Tests reproduce the observed audit discrepancy as a fixture and demonstrate that corrected generated output is internally consistent.
4. No calculation, model gate, data vendor price series, frozen study or real-money capability changes.
5. PR description links old/current file paths, states why its scope does not duplicate Nautilus tasks, and includes rollback instructions.

This first patch should be intentionally conservative. Once it is reviewed, follow the backlog's dependency order: instrument identity, trial-ledger shadow run, research-run contract, workflow shell, and clean-install/release validation.

---

## Source register and review notes

**QUANTGEN repository (observed `main` HEAD):**

- Q1. [Repository](https://github.com/xkg4real/quantgen)
- Q2. [README](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/README.md)
- Q3. [Flet entry/navigation](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/main.py)
- Q4. [Strategy Lab](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/ui/strategy_lab_page.py)
- Q5. [Validation and cost map](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/core/quant/validate.py)
- Q6. [History/provenance](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/core/quant/history.py)
- Q7. [AI panel](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/ui/ai_panel.py)
- Q8. [Current recorded QA](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/qa/acceptance_results.json)
- Q9. [Calendar manifest](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/core/calendars/data/MANIFEST.yaml)
- Q10. [October 27 roadmap](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md)
- Q11. [Nautilus design specification](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md)
- Q12. [Package configuration](https://github.com/xkg4real/quantgen/blob/e28035fed8d19ce33b2e83d18e7d1abc21b28037/pyproject.toml)

**PentPort/public benchmark:**

- P1. [PentPort landing page (public product copy and calculator)](https://pentport.com/)
- P2. [PentPort legal documents, including competition integrity rules](https://pentport.com/docs)
- P3. [PentPort team](https://pentport.com/team)
- P4. [Python package ecosystem listing](https://www.piwheels.org/project/pentport/)

**Regulatory context:**

- L1. [Korean Financial Services Commission (13 August 2024): investment-advice oversight](https://www.fsc.go.kr/no010101/82887)

**Methodology and caveats:** This is a targeted source/documentation and code-path inspection, not a fresh full-suite execution, performance benchmark, pen test, professional legal opinion, independent backtest validation or authenticated PentPort usability test. A few currently active task statuses may change on other branches or after this snapshot. All new task IDs in this document are **proposals**, not changes made to the repository. Where existing roadmap IDs overlap, use those source-of-truth work items rather than creating duplicates.
