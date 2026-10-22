# QUANTGEN after the split, and the research-paper pipeline

Date: 2026-10-23. Status: design approved by the owner on 2026-10-23; this spec
awaits the owner's review before the implementation plan is written.

Inputs:
- `research_notes/QUANTGEN TRADEGEN split map/split_map.md` (file-by-file map,
  sections 1-8 including the critic addendum);
- `reports/Korean resident trading venue legality.md`.

## 1. Purpose

QUANTGEN is split in two:

- **QUANTGEN (this repo)** becomes a quantitative-finance research instrument.
  It goes no further than paper trading.
- **TRADEGEN** (`Desktop/TRADEGEN`) is a byte copy of QUANTGEN as of this date.
  It is developed in its own session for real-money trading within Korean law.

QUANTGEN gains one new capability: on request, it turns a topic into a
formal, fully bilingual research paper. Each paper covers the topic's origin
literature, its current state of the art, how QUANTGEN implements it, and a
reproducible study. The papers build the owner's quant career portfolio.

## 2. Owner decisions (2026-10-22/23)

| # | Decision |
|---|---|
| D1 | The GrokBot BOOK study stays in QUANTGEN as the study of record, and TRADEGEN holds a working duplicate. |
| D2 | The NEXTGEN trading-skills cockpit (Skills, Workflows, Runs) moves to TRADEGEN only. |
| D3 | AI prompts: strip only the trade-idea parts. Deep analysis stays, as research commentary. |
| D4 | Papers are LaTeX, journal style, fully bilingual: two complete editions, English and Korean. |
| D5 | The TeX engine is Tectonic 0.17.0 (approved download). |
| D6 | Paper peer review uses Claude, GPT via the Codex CLI, and Gemini via the Antigravity CLI (`agy`). |
| D7 | The first paper topic will be named separately by the owner. |

## 3. Constraints that bind every step

1. **GROKTEAM-BOOK pre-registration** (look on or after 2027-02-01; D1 keeps
   it here). There are two kinds of protected file:
   - **Pinned (10 files):** `core/quant/garch.py`, `forecast_eval.py`,
     `validate.py`, `gate_stats.py`, `gate_ledger.py`,
     `data/crypto/crypto_client.py`, `data/net.py` and the three `grokteam`
     files. They stay byte-identical until the look.
   - **Unpinned dependencies:** `core/ficc/pit.py`, `macro_schema.py` and
     `schemas/`, `contracts.py`, `core/rules/governance.py`,
     `macro_rules.py`, `core/quant/risk_layer.py`, `vol_estimators.py`,
     `data/macro/*`, and root `config.py`. They may change only in ways that
     leave the names the frozen code uses behaving the same.
   - New quant code goes into new files.
   - numpy 2.3.5, scipy 1.18.0, pandas 2.3.3 and Python 3.13 in the global
     interpreter stay as they are. New tools install into separate
     environments.
2. **paper_live H2 holdout** (readout about 2026-11-03, confirmed with
   `verdict.holdout_sessions()`).
   - No byte change to `paper_live/engine.py` or `config.py`.
   - No behaviour change in garch, vol_estimators, risk_layer, instruments,
     validate (`cost_bp`), strategies (`crypto_trend`), gate_stats, gate_ledger,
     markets, calendars or root `config.macro_dir`.
   - Never run `paper_live.replay`, `grid`, `verdict` or `sameday` except for
     the readout.
3. **test_s4.**
   - `core/engine/state.py`, `runtime.py`, `feed.py` and `__init__.py` stay
     byte-identical.
   - `orders.py`, `evaluator.py` and `ui/trading_page.py` may only gain lines.
4. **Append-only hash-chained ledgers** (`~/.nextgen/macro/ledgers/*.jsonl`,
   `governance_events.jsonl`): never delete or rewrite rows.
5. **Byte-equality tests** (`tests/macro_tf_data.py`) between `reports/`,
   `docs/council/` and `QUANTGEN_Quant_Council_2026-10-03/`.
6. **Test-pinned research paths** (T-COUNCIL-DOCS-01):
   - `research_notes/QUANTGEN macro overlay research/council/` contains only
     `README.md`;
   - the technical-and-fundamental-signals README names the tech-fund bundle.
   - Papers therefore live in a new top-level `papers/`, not in
     `research_notes/`.
7. **Git** (baseline `eacd57d`, `* -text`, autocrlf off). Never re-normalise
   line endings.

## 4. Part A: the split

### 4.0 Phase 0: done 2026-10-23

- QUANTGEN was copied to `Desktop/TRADEGEN`. All 959 files have identical
  sha256; only `__pycache__` and `.pytest_cache` were skipped.
- QUANTGEN was put under git with the baseline commit `eacd57d`.
- TRADEGEN's isolation (its own venv, `~/.tradegen` state root, KIS token
  path, ledger copies, git) belongs to the TRADEGEN session, not this repo.

### 4.1 Phase 1: now (one commit per bullet group, full suite after each)

**A1. Cockpit out (D2).**
- Delete:
  - `core/skills/{index,entrypoints,params,readiness,runner,runs,diagnose,workflows,decisions,insights,wiring}.py`;
  - `ui/{skills_page,workflows_page,runs_page,param_form,charts}.py`.
- Empty `core/skills/__init__.py` to a docstring. Keep `macro_daily.py`,
  `pipeline.py`, `alerts.py` and `macro_workflows/`.
- `main.py`: drop the cockpit imports, the three NAV rows and their branches,
  `reload_catalogue`, and `on_reload=`.
- `ui/settings_page.py`: drop the skills-root, skill-provider, runs-dir and
  reload blocks, and the ALPACA/FINVIZ `.env` lines.
- `ui/components.py`: inline a 4-value `State` enum.
- `config.py`: remove only the skills section (`_DEFAULT_SKILLS_ROOT` …
  `skill_provider_status`, `SKILL_CREDENTIALS`, `runs_dir`). Every name the
  frozen code reads stays untouched.
- `.env.example`: drop the skill-library provider block.
- `tests/acceptance.py`:
  - keep `_read`, `_code_only`, `runtime_py` and test_08, 09, 13-18, 21, 22
    (10 tests);
  - remove the other 37. Tests 10-12 import the cockpit runner (critic
    8.1-1).
- `tests/run_all.py`: rename the kept suite from `cockpit` to `safety`
  (8.4-12).
- `tests/macro_m8_pipeline.py:132`: becomes a negative existence check.
- `tests/macro_ui_components.py` L120-127: drop the Runs-page assertion and
  keep the rail-scroll assertion (8.1-2).
- Dangling text to update (8.4-11):
  - README L3-4, L354, ~L738-747, ~L777, ~L829;
  - `ui/krx_page.py` L1, L189;
  - the `config.py` docstring;
  - `docs/ARCHITECTURE_REVIEW.md:60`.
- QUANTGEN's real `.env` keeps its values; the owner deletes the
  `NEXTGEN_SKILLS_ROOT`, FINVIZ, ALPACA and FXMACRODATA lines when convenient.
  Claude does not edit `.env`.

**A2. Crypto regime score out.**
- `core/crypto/analytics.py`: remove `regime_score`, `RegimeComponent`,
  `RegimeScore` and `_sma`, plus its self-check lines L430-435 (8.1-3).
- `ui/crypto_page.py`: remove the `regime` uses at L77, 110, 122, 136, 141,
  164, 220, 225 and 233, and the tile.
- README crypto line.
- `docs/ASSET_EXPANSION_SPEC.md:177` and `docs/build_expansion_primer.py:662`
  get a "moved to TRADEGEN 2026-10-23" note. The already-built Expansion
  Primer PDF stays as a dated artifact.

**A3. Trade-idea prompt parts out (D3).**
- `core/ficc/insights.py`: remove the "Positioning ideas"/"Positioning"
  clauses that ask for trades with entry, stop and target. Keep
  `report_prompt()` and `deep_analysis()`, re-worded as research commentary
  (drivers, tensions, sensitivities, what would change the read).
- `core/quant/insights.py::_SYSTEM`: replace "personal quantitative trading
  application" and "what the trade expression would be" with research
  wording (8.2-5).
- README L674-678 follows.
- `tests/ficc_acceptance.py` L668-675 is adjusted only if it asserts the
  removed wording.

**A4. Identity.**
- "Personal quant trading application" becomes "quantitative finance research
  application" in pyproject, main.py docstrings and the README intro.
- The README gains a "Split from TRADEGEN (2026-10-23)" note.
- The README gains a "Research papers" section (Part B).

**A5. GrokBot labelling (D1).** No code change, and nothing new inside
`grokteam/`, because the prereg check's view of that folder is not verified.
- A README section says:
  - this is the frozen GROKTEAM-BOOK study of record, a benchmark of an outside
    LLM-bot guide;
  - the venue is illegal for Korean residents to trade, so it is
    research-only;
  - the one look is on or after 2027-02-01;
  - TRADEGEN's copy is not the record.

Verification for Phase 1:
- `python tests/run_all.py` before and after each group, recording pass,
  fail and notrun counts.
- The only expected drop is the removed cockpit tests: 37 tests plus the
  regime self-check.
- Every PREREG-pinned sha is unchanged.
- `python -m grokteam.prereg` (check mode) reports no change.
- `git diff --stat` touches none of the constraint-3 files.

### 4.2 Phase 2: after the H2 readout for both profiles

Apply split_map section 3.4 (LAZYOWEN out of `paper_live` code, report,
narrative and tests). Re-register the cost-gate hypothesis on QG-TACTICAL vs
TACT-NOGATE as a new freeze, tested only on sessions after it. LAZYOWEN ledger
rows stay. The readout and verdict of record are made in QUANTGEN (8.1-4).

This phase is not scheduled in this plan. It needs its own approval once
`out*/verdict.json` exists.

## 5. Part B: the research-paper pipeline

### 5.1 Shape

There are two saved workflows, so the owner approves the study before any
code changes:

| Command | Workflow | Output |
|---|---|---|
| `/quantgen-paper <topic>` | `.claude/workflows/quantgen-paper-research.js` | `papers/<date>-<slug>/scope/`: research questions, the module map, an annotated and verified bibliography, the integration analysis, the proposed study with a pre-registration draft, and the proposed new code if any. **Stops for owner approval.** |
| `/quantgen-paper write <slug>` | `.claude/workflows/quantgen-paper-write.js` | Implementation and tests (if approved), the study run, the English draft, referee rounds, the Korean edition, both PDFs and the portfolio update. |

A project skill, `.claude/skills/quantgen-paper/SKILL.md`, defines the
command. It tells Claude which workflow to run, and to run the approval
checkpoint between the two.

### 5.2 Research workflow stages

1. **Scope.** Map the topic onto the 52(+) topics in split_map section 6 and
   on to modules with file:line references. Write the research questions.
   Decide whether QUANTGEN already implements the model or new code is needed.
2. **Literature sweep.** Four parallel searchers, each blind to the others:
   - (a) the origin and canonical papers;
   - (b) the state of the art from 2023 to now: top journals, NBER, Fed, BIS,
     ECB, BoE and IMF working papers, arXiv q-fin, SSRN;
   - (c) the owner's study materials (`iCloudDrive/퀀트 학습 자료`,
     `26년 2학기 수업자료`), cited by document and page as the
     `[REF]` convention requires;
   - (d) textbook treatment.
   The four outputs are merged into one annotated BibTeX file.
3. **Citation verification.** Every entry is checked by an independent agent
   against DOI or Crossref, or the publisher or working-paper page: authors,
   year, title, venue and pages. Entries that can't be confirmed are dropped
   or marked; none is silently kept. A completeness critic asks what is
   missing.
4. **Integration analysis.** How QUANTGEN implements the model, the gaps
   against the literature, and the guardrails, which must be visible (the
   owner's standing rule).
5. **Study proposal.**
   - The hypotheses, data, metrics and decision rule.
   - Confirmatory claims get a pre-registration JSON in the existing
     prereg style, frozen before the run.
   - Studies use QUANTGEN's own gate (`validate`, `gate_stats`, `forecast_eval`)
     by import only, so the pinned files are unchanged.

### 5.3 Write workflow stages

6. **Implementation (only if approved).**
   - New module(s) with an acceptance test registered in `tests/run_all.py`.
   - Guardrails surfaced in the UI and narrative.
   - The Models Primer is extended when new estimation machinery appears.
   - Constraint 3.1 means new files, not edits to pinned or dependency files.
7. **Study run.** `papers/<slug>/study/run.py` writes `results.*` plus
   `MANIFEST.json` (sha256). Every number in the paper is generated from these
   files into `numbers.tex` macros. No hand-typed results.
8. **English draft.**
   - Template `tools/paper/template_en.tex`: article 11pt A4, natbib
     author-year, amsmath, booktabs, hyperref.
   - Front matter: title, author (Geon Koh, Korea University), abstract,
     keywords and JEL codes.
   - Sections: introduction, literature, model, implementation in QUANTGEN
     (with listings), data and method, results, robustness, limitations,
     conclusion, references and a reproducibility appendix.
   - A "not investment advice" footnote.
9. **Referee panel**, at most 3 rounds.
   - Claude (a separate reviewer agent), GPT (`codex exec`) and Gemini
     (`agy -p --model gemini-4-argon-high --sandbox --disable-slash-commands`)
     each write a structured referee report, sorted into major and minor
     issues.
   - A revision agent answers every point in `review/response_round<k>.md`.
   - The loop stops when no referee raises a major issue. Otherwise, after 3
     rounds, the remaining disagreements are listed in the paper's
     limitations and in the response letter.
   - The runner is `tools/debate.py`, a small subprocess wrapper with a
     timeout and JSON parsing. The project calls the CLIs directly rather than
     patching the plugin.
10. **Korean edition.**
    - Template `tools/paper/template_ko.tex`: kotex/xetexko with Batang as the
      body font and Noto Sans KR as the sans font.
    - A full translation guided by `tools/paper/glossary_ko.yaml`, which
      covers finance terms (변동성, 조건부 이분산, 최우추정, …).
    - `tools/paper/consistency.py` then checks that the two editions have the
      same `numbers.tex` macros, citation keys, equation count, figure and
      table labels, and section structure. Any mismatch fails the build.
11. **Build and QA.**
    - `tectonic -X compile` for both editions. The build fails on undefined
      references, undefined citations, or overfull boxes over 10 pt.
    - Pages are rendered to PNG with pypdfium2.
    - A `design:design-critique` pass reviews the layout.
12. **Portfolio.**
    - `tools/paper/build_index.py` regenerates `papers/INDEX.md` and a static
      `papers/index.html`, styled with design-system tokens and listing each
      paper's title, both abstracts, EN and KO PDFs, code and results links,
      and date.
    - Publishing it as a private shareable page happens only when the owner
      asks.

### 5.4 Folder layout

```
papers/
  INDEX.md, index.html
  2026-MM-DD-<slug>/
    scope/      questions.md, integration.md, study_proposal.md, prereg.json
    refs.bib
    study/      run.py, results.*, MANIFEST.json, numbers.tex
    en/         paper.tex, figures/, paper_en.pdf
    ko/         paper.tex, paper_ko.pdf
    review/     round<k>_<model>.md, response_round<k>.md
tools/paper/    template_en.tex, template_ko.tex, glossary_ko.yaml,
                consistency.py, build_index.py, selfcheck.py
tools/debate.py
```

### 5.5 Tests

`tools/paper/selfcheck.py` is registered as suite `papers` in
`tests/run_all.py`. It checks four things:
- a two-page EN and KO sample compiles;
- `consistency.py` catches a planted number mismatch and a missing citation
  key;
- `build_index.py` lists the sample;
- `debate.py` handles a missing CLI and a timeout without crashing.

The paper workflows themselves are checked by producing the first real paper.

## 6. Out of scope

- An in-app Papers page. It can be added later if wanted.
- Any change to the frozen studies.
- TRADEGEN work of any kind (its own session).
- Automatic publication of papers.

## 7. Risks

| Risk | Mitigation |
|---|---|
| A Phase 1 edit silently changes frozen behaviour | Constraint list in section 3; a pinned-sha check and a prereg check after every commit |
| Hallucinated references in a portfolio paper | Independent citation verification stage; unverifiable entries dropped |
| Hand-typed numbers drift from results | Numbers only enter through generated `numbers.tex` |
| The two editions drift apart | `consistency.py` gate |
| An external CLI fails or rate-limits mid-review | `debate.py` timeout; the review continues with the remaining referees and records the gap |
| Korean font or package issues in Tectonic | Selfcheck compiles a Korean sample before any real paper |
