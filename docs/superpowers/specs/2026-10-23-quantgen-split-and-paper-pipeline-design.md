# QUANTGEN after the split, and the research-paper pipeline

Date: 2026-10-23.

Status:
- **Revision 3.**
  - Round 1: Claude said ACCEPT WITH CHANGES; GPT (Codex) and Gemini
    (Antigravity) said REJECT.
  - Round 2: Claude and Gemini said ACCEPT WITH CHANGES. GPT was *review
    incomplete*: the Codex quota is exhausted until 2026-10-27 19:16.
  - Appendices A and A2 rule on every issue.
- **Approved by the owner on 2026-10-23**: Parts A and B with the recommended
  defaults and the tag-based freeze. Two owner changes are folded in:
  - the weekly FICC note is rewritten in an academic register (section 4.1
    A3);
  - phone alerts for the H2 test (section 5A).
- Next: the implementation plan.

Inputs:
- `research_notes/QUANTGEN TRADEGEN split map/split_map.md`;
- `reports/Korean resident trading venue legality.md`.

## 1. Purpose

QUANTGEN is split in two:
- **QUANTGEN (this repo)** becomes a quantitative-finance research instrument.
  It goes no further than paper trading.
- **TRADEGEN** (`Desktop/TRADEGEN`) is a byte copy of QUANTGEN as of this date,
  developed in its own session for real-money trading within Korean law.

QUANTGEN gains one capability: on request, it turns a topic into a formal,
fully bilingual research paper. Each paper covers the topic's origin
literature, its current state of the art, how QUANTGEN implements it, and a
reproducible study. The papers build the owner's quant career portfolio, so
they must be correct, honestly labelled, and disclosed as AI-assisted.

## 2. Owner decisions (2026-10-22/23)

| # | Decision |
|---|---|
| D1 | The GrokBot BOOK study stays in QUANTGEN as the study of record, and TRADEGEN holds a working duplicate. |
| D2 | The NEXTGEN trading-skills cockpit moves to TRADEGEN only. |
| D3 | Strip only the trade-idea parts of the AI prompts. Deep analysis stays, as research commentary. |
| D4 | Papers are LaTeX, journal style, fully bilingual: two complete editions, English and Korean. |
| D5 | The TeX engine is Tectonic 0.17.0. |
| D6 | Referees are Claude, GPT via the Codex CLI and Gemini via the Antigravity CLI `agy`. They may also do bounded work, given the project history. |
| D7 | The owner names the first paper topic separately. |
| D8 | QUANTGEN is under git (baseline `eacd57d`). This is the owner action that ruling 3.1 asked for. |
| D9 | The two frozen studies run their readouts only from a git tag of `eacd57d`, so QUANTGEN's main line is free to change (section 3.1). |

## 3. Constraints that bind every step

### 3.1 Frozen studies: read out from a tagged snapshot (D9)

Two pre-registered studies exist:
- **GROKTEAM-BOOK.**
  - Its one look is on or after 2027-02-01 01:00 UTC.
  - `prereg.check()` pins 10 files, `RULES`, `ACCOUNTS`, `VERDICT`,
    `model_digest()` and numpy 2.3.5 / scipy 1.18.0 / pandas 2.3.3 /
    Python 3.13.
- **paper_live H2.**
  - `paper_live/engine.py` and `config.py` equal the `out*/frozen_rule/`
    copies.
  - The readout follows the 10 holdout sessions (about 2026-11-03). It must
    run by about **2026-12-19**, because the 5-minute bars it needs are kept
    for 60 days.

Both studies need far more than their pinned files. Their import closure is
about 57 modules, and they also read calendar and macro data files and use one
dynamic `importlib` load. Guarding all of that on the main line would freeze
most of QUANTGEN until February. Instead:

1. **The tag.** An annotated tag `studies-of-record-2026-10-23` is put on
   `eacd57d`. Appendix C has the evidence that `eacd57d` *is* both frozen
   states:
   - the 10 pinned files match PREREG;
   - the H2 files match `frozen_rule`;
   - no tracked code or data file changed after the H2 freeze, except
     paper_live's reporting files `analyze`, `report`, `narrative` and
     `compare`, which are off the readout path;
   - nothing changed after the GROKTEAM freeze.
2. **Both readouts run only from a local `git clone` checked out at that
   tag**, for example
   `git clone --branch studies-of-record-2026-10-23 QUANTGEN QUANTGEN-studies`.
   - Not `git worktree`: in a worktree `.git` is a file, so the pinned
     `gate_ledger.repo_anchor()`, which reads `<root>/.git/HEAD`, would write
     UNVERSIONED rows.
   - A clone's detached HEAD gives `git:<eacd57d…>`.
   - Never run a whole-tree `git checkout`, `reset`, `stash` or `clean` in
     the main repo, because they rewrite cache-file mtimes that one test
     relies on.
   - They use an interpreter with the pinned library versions: the global
     one while it still matches, otherwise a dedicated venv pinned to those
     versions.
   - They follow their own procedures: H2 is `REPLAY_HOLDOUT=1 python -m
     paper_live.replay`, then `python -m paper_live.verdict`, per profile.
     GROKTEAM is the first full `python -m grokteam.book` at or after the
     look time.
   - Their outputs are copied into the main line and committed as artifacts:
     `out*/replay_holdout`, `verdict.json`, `FORWARD_LOOK.json` and the
     readouts. Their ledger rows are anchored to the tag's commit.
3. **The main line is free to change any file**, including the pinned ones.
   On main, `grokteam.prereg` will report VOID once a pinned file changes.
   That is expected and harmless, because the record runs from the tag.
   - Main must never run `grokteam.book` on or after the look time.
   - Main must never run the H2 readout itself.
4. **The guard.** `tests/frozen_guard.py` imports nothing from `paper_live`
   or `grokteam`; it uses only git through subprocess and hashlib. It reports
   `NotRun` if git is missing. It fails when:
   - (a) the tag is missing or no longer peels to `eacd57d…`;
   - (b) in the tagged tree (`git show <tag>:<path>`), a pinned file's
     sha256 differs from PREREG, or an H2 file differs from its
     `frozen_rule` copy;
   - (c) before 2027-02-01 01:00 UTC, `grokteam/out/book/FORWARD_LOOK.json`
     exists on main;
   - (d) the interpreter's numpy, scipy or pandas versions differ from the
     pins, while a look is still pending. There is no warn-only branch: a
     dedicated pinned venv is set up, and this clause rewritten, only if the
     global interpreter ever has to move before the looks.

   **Expiry.** Clauses (a) and (b) stay forever as provenance. Clauses (c)
   and (d) retire once both readouts are committed.

`verdict.holdout_sessions()` may be called as a function inside the tag clone.
Never run `paper_live.verdict` as a module before the readout, because it
writes `verdict.json`.

### 3.2 TRADEGEN must not touch QUANTGEN's records

These rules go in the TRADEGEN session's brief as hard prerequisites:
- **Nothing in TRADEGEN runs before isolation.** No app, test or script
  runs until TRADEGEN has its own venv and its own state root; the macro dir,
  trading dir, runs dir, FICC cache, grokteam data and ledger dir, and the
  hard-coded KIS-token and DART paths are all redirected in code.
- **TRADEGEN never takes the GROKTEAM forward look.** Disabling only the
  `FORWARD_LOOK.json` write is not enough, because `book.main` still computes
  and prints the forward results, so every later run would be another look.
  - Its copy keeps forward events **permanently blinded**: `forward_gate`
    always blinds, or events are cut at `frozen_utc`.
  - It never deletes its `PREREG_book.json` or `frozen_book/`, which would
    remove the gate entirely.
  - It never registers trials into `~/.nextgen/macro/ledgers`.
- **No concurrent runs.** While QUANTGEN's acceptance suite runs, no app
  from either program runs, because T-HERM-02 snapshots the home state.

### 3.3 Consequences of being under git (D8)

- `gate_ledger.repo_anchor()` now returns `git:<sha>` instead of
  `UNVERSIONED`, so new ledger rows are anchored. It is part of a pinned file,
  but neither frozen verdict reads the anchor. Neither `prereg.check()` nor
  `verdict.py` uses it.
- Tests that assert the folder is not a git repository (at least T-LEDGER-01,
  `tests/macro_m7_ledger.py:144`) are updated to follow the actual repo state.
  The measured list of affected tests is in Appendix B.
- `MA.GIT_HASH` and `lab.GIT_HASH` stay the constant `UNVERSIONED`. This
  keeps the macro freeze and admissions refused, exactly as today, and
  prevents a silent behaviour change in the overlay. Wiring them to git is a
  separate owner decision, out of scope here, and recorded as a known split.
- The git rules: `* -text`, autocrlf off, and never re-normalise. The tracked
  `qa/acceptance_results.json` is committed together with each change group.

### 3.4 Standing rules carried over

- `test_s4`:
  - `core/engine/state.py`, `runtime.py`, `feed.py` and `__init__.py` stay
    byte-identical;
  - `orders.py`, `evaluator.py` and `ui/trading_page.py` may only gain lines;
  - the S4 modules gain no wall-clock calls (`tests/macro_m5_integration.py:55-56`).
- Ledgers are append-only and hash-chained.
- The byte-equality tests in `tests/macro_tf_data.py` hold.
- The test-pinned research paths hold (T-COUNCIL-DOCS-01). That is why papers
  live in a new top-level `papers/`.
- Repository-wide guards bind all new code:
  - T-CTX-01, the acting-module import scan in `core/ficc/context_log.py`;
  - T-RO-01 and the safety test_08/09 order-path scans;
  - `tests/flet_api_guard.py`.
- **Order-path scans.** `tests/macro_m0_harness.py::_scan_files()`, which
  backs T-RO-01, is extended to `tools/` and `papers/`. `papers/` is added to
  `ORDERS_IMPORTERS_ALLOWED`, so a study may read the simulated fill model.
  `tests/acceptance.py::runtime_py()` is **not** extended: its raw-text scans
  would trip on docstrings that merely name a forbidden call.

## 4. Part A: the split

### 4.0 Phase 0: done 2026-10-23

- The QUANTGEN tree was copied to `Desktop/TRADEGEN`, and all 959 files have
  identical sha256.
- QUANTGEN was put under git at `eacd57d`.
- The spec draft is `39d522c`.

### 4.1 Phase 1 (each group is one commit; the full suite runs before and after it)

**A0. Tag and guard first.**
- Create the annotated tag `studies-of-record-2026-10-23` on `eacd57d`, with
  the Appendix C evidence in the tag message.
- Add `tests/frozen_guard.py` (section 3.1).
- Make the git-state test changes (section 3.3, Appendix B).
- The suite must be green apart from the known NOT_RUN rows.

**A1. Cockpit out (D2).**
- Delete:
  - `core/skills/{index,entrypoints,params,readiness,runner,runs,diagnose,workflows,decisions,insights,wiring}.py`;
  - `ui/{skills_page,workflows_page,runs_page,param_form,charts}.py`.
- `core/skills/__init__.py` becomes a docstring only. Keep `macro_daily`,
  `pipeline`, `alerts` and `macro_workflows/`.
- `main.py`:
  - drop the cockpit imports (L46, 67, 69, 70), the three NAV rows and their
    `build` branches, `reload_catalogue` and `on_reload=`;
  - simplify `navigate()` to `(name, *, rebuild=False)`, dropping `focus` and
    `**kwargs`;
  - fix the docstring at L3-4.
- `config.py`: remove exactly these names, which are not contiguous:
  - `_DEFAULT_SKILLS_ROOT`, `skills_root`, `skills_root_valid`,
    `skill_python`, `SKILL_TIMEOUT_SECONDS`, `runs_dir`;
  - `SKILL_CREDENTIALS`, `KEYLESS_INTEGRATIONS`, `FILE_INPUT_INTEGRATIONS`,
    `skill_credential_present`, `skill_env`, `skill_provider_status`.
  - Keep the provider helpers between them (`fmp_ready`, `HTTP_TIMEOUT_SECONDS`
    and the rest).
  - **Move the FMP status row into `quant_provider_status()`**, because it is
    shown today only through the skill providers. Its `ready` becomes
    `fmp_ready()`, since `skill_credential_present` is deleted, and its note
    becomes "dividend-adjusted US end-of-day prices".
- `ui/settings_page.py`:
  - imports L18-19;
  - the skills-root block;
  - the readiness, Interpreter and Run-timeout rows (L181-187);
  - the skill-provider list;
  - the runs-dir row;
  - the `.env` snippet lines `NEXTGEN_SKILLS_ROOT`, `ALPACA_*`, `FINVIZ_*`
    and `FXMACRODATA_*` (L192-196);
  - the `_SIGNUP` entries finviz, alpaca and fxmacrodata;
  - the `on_reload` parameter and the reload button;
  - the docstring.
- `ui/components.py`: **delete** the readiness import, `STATE_STYLE`,
  `RUN_STATUS_STYLE`, `readiness_chip` and `run_status_chip`, because only the
  deleted pages used them. Reword the docstring.
- `.env.example`: drop the skill-provider block and fix the header at L3.
- `tests/acceptance.py`:
  - keep `_read`, `_code_only`, `runtime_py` and test_08, 09, 13-18, 21, 22
    (10 tests);
  - delete the other 37;
  - fix the docstring.
- `tests/run_all.py`: rename the suite `cockpit` to `safety`, including the
  `--suite` help text.
- `tests/macro_m8_pipeline.py:132-133`: replace both lines with
  `assert importlib.util.find_spec("core.skills.workflows") is None`.
- `tests/macro_ui_components.py:120-127`: drop the Runs-page read and keep the
  rail-scroll assertion.
- Dangling text:
  - README L3-4, L354, L738-747 (nineteen becomes sixteen entries), L763,
    L777 (the row becomes `safety`, 10), L786 (total), L829;
  - `ui/krx_page.py` L1, L3, L189;
  - the `config.py` docstring;
  - `tests/macro_acceptance.py:8,116`;
  - `docs/ARCHITECTURE_REVIEW.md:60`.
- Owner housekeeping, not done by Claude: remove `NEXTGEN_SKILLS_ROOT`,
  `FINVIZ_*`, `ALPACA_*`, `FXMACRODATA_*`, `KIS_ACCOUNT_PD` and the unused
  `TYPESAFE_API_KEY` from QUANTGEN's real `.env`.

**A2. Crypto regime score out.**
- `core/crypto/analytics.py`:
  - remove `regime_score`, `RegimeComponent`, `RegimeScore` and `_sma`;
  - remove the docstring L2 and L15-21;
  - remove only the regime assertions in the self-check (L430-435). The
    registered test `expansion/selfcheck_crypto_analytics` stays. Confirm
    after the run that `weekday_table`'s assertion is unaffected by the
    shifted rng stream.
- `ui/crypto_page.py`:
  - docstring L1;
  - `MAJORS` L24, with the `majors` draws in `_synthetic` (L39, and re-seed
    ETH directly at L41) and `_live` (L52-57, 61), so 8 Binance calls a load
    disappear;
  - L76-77 (`fa`, `out["regime"]`);
  - L110 and the whole `if rs:` block L120-123;
  - L136, 141-142;
  - L164, 182 (tile) and 189-192 (components chart);
  - L220, 225, 233, and the regime parts of L236 and L238.
- Register `ui/crypto_page.py`'s self-check as an expansion test, so the page
  is exercised from now on.
- README crypto line. `docs/ASSET_EXPANSION_SPEC.md:177` and
  `docs/build_expansion_primer.py:662` get a dated "moved to TRADEGEN" note.
  The built primer PDF stays as an artifact.

**A3. Trade-idea text out (D3).**
- `core/ficc/insights.py`:
  - remove the "Positioning ideas"/"Positioning" clauses that ask for trades
    with entry, stop and target;
  - keep `report_prompt()` and `deep_analysis()`, re-worded as research
    commentary.
- **`narrate_weekly_strategy` (L409-490)**, which is deterministic, says
  "lean long", "run steepeners" and "Carry: long X … funder". It is rewritten
  as an **academic descriptive read** (owner ruling, 2026-10-23).
  - **Register.** A formal, third-person, journal-style register. No
    imperative verbs, no position language (long, short, run, fund, size,
    cut, entry) and no forecasts.
  - **Content.**
    - Each quantity is stated with its definition and window: the z-score
      against the trailing 252-session mean, and the 1-week change in bp.
    - The curve is described by level, slope and curvature in the sense of
      Litterman & Scheinkman (1991), and by the 2s10s regime, labelled as
      "bull/bear steepening/flattening over N sessions".
    - The 5y5y forward is compared with the 2y/5y/10y level as a measured
      spread, never as "priced for cuts".
    - The dollar is described by its regime, change and z-score.
    - Carry is ranked by carry-to-volatility as defined by Koijen, Moskowitz,
      Pedersen & Vrugt (2018), reported as a cross-sectional observation.
  - **Sources and limits.** Short-form citations are allowed only for the
    definition of a measure, and the two above are already in split_map
    section 6, rows 38 and 40. The note closes with one sentence stating that
    it is descriptive and makes no recommendation.
  - **Example:** "Duration: The 10-year Treasury yield stands at 4.31%,
    1.2 standard deviations above its trailing one-year mean, following a
    +12 bp change over the week."
  - It keeps the `Duration:`/`Curve:`/`FX:`/`Carry:` section prefixes the
    tests assert.
  - The `FX:` line at L464-469 ("USD longs against low-yielders", "fading
    dollar strength into high-carry currencies") is also rewritten as a
    description.
  - Updated to match:
    - `tests/ficc_acceptance.py:744-763`, which asserts `long {best.ccy}`;
    - `tests/ficc_acceptance.py:660-665`;
    - the module's own self-check at `core/ficc/insights.py:691-696`, which
      asserts exact trade-call sentences.
  - This is called out for the owner's confirmation in the review note. D3
    named the AI prompts, and this is deterministic text.
- `core/quant/insights.py::_SYSTEM` (L263-279): change the persona from a
  "sell-side strategist writing for a trading desk" to an academic research
  analyst who writes in the same register as the weekly note. Remove "trade
  expression". The FICC report prompts follow the same register.
- README L670-678.
- **Reviewed and kept** (2026-10-23 plan review):
  - `narrate_carry`'s "top-N long/short carry basket" defines how the carry
    strategy is constructed;
  - `narrate_fx_forward`'s "being long EUR earns …" explains forward points.
  - Both describe method, not a recommendation, so D3 does not apply to them.

**A4. Identity.**
- "Personal quant trading application" becomes "quantitative finance research
  application" in pyproject, the main.py docstrings and the README intro.
- The README gains a "Split from TRADEGEN (2026-10-23)" note and a "Research
  papers" section.

**A5. GrokBot labelling (D1).** No code change; a root README section only.
- It is the GROKTEAM-BOOK study of record: a benchmark of an outside LLM-bot
  guide, research-only.
- Its Kalshi non-sports venue is rated "grey, treat as illegal" for Korean
  residents. No Korean ruling exists; see the legality report, confidence
  medium-low.
- The one look is on or after 2027-02-01.
- TRADEGEN's copy is not the record.
- (A note inside `grokteam/` would also be safe, since `check()` hashes a
  fixed tuple, but the README is enough.)

**Verification for Phase 1:**
- The suite runs before and after each group. The outcome compares test
  identities as well as totals.
- The expected outcome is **37 fewer registered tests** (848 becomes 811,
  with PASS 727 becoming 690 and NOT_RUN staying 121), plus the new guard and
  crypto-page tests.
- `frozen_guard` passes.
- `git diff --stat eacd57d -- paper_live grokteam core/engine` is empty
  (Phase 1 has no reason to touch them).
- The README test table (L763-786) is updated **once**, in the last Phase 1
  commit, with the measured totals. That avoids stale counts between groups.

### 4.2 Phase 2: LAZYOWEN out of paper_live (separate approval)

**Precondition:** completed and valid H2 readouts for **both** profiles.
- That means all planned holdout sessions, matching frozen digests, and
  archived evidence.
- A valid "not confirmed" result qualifies. A pending, incomplete or invalid
  result does not; today both `out*/verdict.json` say pending.

**The readout is time-critical.** The holdout replay pulls 5-minute bars with
60-day retention, so it must run by about **2026-12-19**.

Then apply split_map section 3.4, and re-register a cost-gate hypothesis on
QG-TACTICAL vs TACT-NOGATE as a new freeze. LAZYOWEN's ledger rows stay.

## 5. Part B: the research-paper pipeline

### 5.1 Shape and control

| Command | Executor | Output |
|---|---|---|
| `/quantgen-paper <topic>` | Claude Code's Workflow tool runs the saved script `.claude/workflows/quantgen-paper-research.js`. The date comes in through `args`, and agents do all file I/O. | `papers/<paper_id>/scope/`, with `paper_id` = `YYYY-MM-DD-<slug>` |
| `/quantgen-paper write <paper_id>` | `.claude/workflows/quantgen-paper-write.js` | the study, both editions, review records and release state |

- **The project skill** `.claude/skills/quantgen-paper/SKILL.md` defines the
  command, runs the approval checkpoint, and resolves a bare slug by glob.
  - If the Workflow tool is unavailable in a session, the skill runs the same
    stages with the Agent tool.
  - The synthetic dry run (section 5.5) proves the dispatch path first.
- **Approval** is recorded in `scope/approval.json` (the sha256 of every scope
  file plus the owner's words). The refusal is deterministic:
  `python -m tools.paper.approval check <paper_id>` exits non-zero if any
  scope file changed after approval, and the write workflow's first stage
  stops on that exit code. It does not rest on an agent's judgment.
- **Release states:**
  `DRAFT → REVIEW_INCOMPLETE | BLOCKED_MAJOR → OWNER_REVIEW → RELEASED`.
  - A referee who returns nothing means `REVIEW_INCOMPLETE`, never "no
    objections", unless the owner records a substitution.
  - An unresolved major issue means `BLOCKED_MAJOR`. A round limit stops the
    work; it does not clear a veto.
  - Only `RELEASED` papers enter `papers/INDEX.md`. Release requires the
    owner's sign-off: "I have read the paper and accept every claim".

### 5.2 Research workflow (scope only; no repo code changes)

1. **Scope.**
   - Map the topic to split_map section 6 and to modules with file:line
     references.
   - Write the research questions.
   - Decide whether QUANTGEN already implements the method.
2. **Literature.** Three blind searchers plus a completeness critic. The
   count depends on the topic and may be fewer.
   - (a) canonical and textbook treatment;
   - (b) the state of the art from 2023 to now: journals, NBER, Fed, BIS,
     ECB, BoE and IMF working papers, arXiv q-fin, SSRN;
   - (c) the owner's study materials at `C:\Users\whydi\iCloudDrive\퀀트 학습 자료`
     and `C:\Users\whydi\iCloudDrive\26년 2학기 수업자료`. These are used to
     **check derivations**, and the paper cites the published book or paper
     they correspond to, with page numbers. Slides, lecture notes and the
     owner's unpublished notes are not cited.
3. **Reference and claim verification.**
   - `tools/paper/refs.py` (`python -m tools.paper.refs verify|bib`) queries doi.org/Crossref and the arXiv API.
     It writes a `verified` record per entry: method, URL, retrieval date and
     fetched title. Entries it can't reach (SSRN often blocks bots; books
     have no DOI) are marked `manual` with a URL and are checked by an agent.
   - The selfcheck fails on an entry with no record.
   - Every `\cite` in the literature, model and results sections has a row in
     `claims.yaml`: claim id, paragraph id, source key, locator
     (page/equation/table), the supporting passage or derivation, and a status.
     - A claim whose source was not read is marked `unread`.
     - `unread` and `unsupported` claims block release.
     - An independent agent checks the rows, and rechecks changed paragraphs
       after revision and translation.
   - Working papers and their published versions are kept apart.
4. **Integration analysis.** How QUANTGEN implements the method, the gaps,
   and the guardrails, all visible.
5. **Analysis protocol (`scope/protocol.md`).**
   - It states: estimand, observation unit, sample and eligibility, data
     access history (has this series been used before in `docs/*`?), holdout
     (dated after the freeze where a confirmatory claim is made), leakage
     controls, dependence correction, power and MDE, multiplicity, and every
     variant to be tried.
   - It labels each claim *exploratory*, *pre-specified on historical data*,
     or *confirmatory (post-freeze holdout)*.
   - A NOT_RUN, smoke-only or insufficient-data result can never become a
     positive claim. Its status propagates to the abstract, conclusion and
     index.
   - It uses QUANTGEN's gates where they fit the topic, and says so where
     they don't (for example, the 5-year strategy gate).
   - Proposed new code, if any, is listed with the guards it must pass
     (section 3.4).

### 5.3 Write workflow

6. **Implementation (only if approved).**
   - Reusable models go in new modules with acceptance tests (lazy imports in
     `run_all.py`).
   - Paper-specific code stays in `papers/<paper_id>/study/`.
   - Any file on the main line may change (section 3.1). A defect found in a
     pinned file is fixed on main, and the paper notes that the study of
     record runs from the tag.
   - UI and Primer integration is scoped separately; it is not mandatory.
7. **Study run (`study/run.py`).**
   - It refuses to run unless `scope/prereg.json` is committed (git anchor
     and sha) and its pinned code shas match.
   - For pre-specified or confirmatory runs, it also refuses a dirty working
     tree, because `repo_anchor()` reads only HEAD and would otherwise anchor
     uncommitted code.
   - It freezes raw inputs into `study/data/` with sha256, and sets
     `NEXTGEN_FICC_CACHE` to a study-local folder.
   - It writes `study/runs/<run_id>/` (and refuses to overwrite) with
     `MANIFEST.json`, which records: input content hashes and vintages, the
     git commit plus a clean-tree flag, the study-code shas, config, Python and
     package versions, seeds, time zone and calendar conventions, the command,
     and the qualification status.
   - Trials go to a paper-local ledger family `PAPER-<paper_id>`, unless
     formally registered in an existing family.
   - A second, offline rerun from the frozen data must match within declared
     tolerances.
8. **Numbers and figures.**
   - `run.py` writes `numbers.json`. For each key it records the value,
     source file and field, selection, units and rounding.
   - `numbers.tex` defines `\qnum{key}` through `\csname`, so keys may
     contain digits and underscores.
   - Figures are rendered twice (`lang='en'|'ko'`, with matplotlib using the
     installed Korean font), or they are language-neutral and only the
     captions are translated.
   - Tables are generated from `numbers.json` with per-language headers.
   - Equations live in shared `common/*.tex` files that both editions
     `\input`.
9. **English draft.**
   - `tools/paper/template_en.tex`: article 11pt A4, natbib with `plainnat`
     and BibTeX (never biblatex/biber), amsmath, booktabs, hyperref, xurl.
   - Front matter: title, Geon Koh, Korea University, abstract, keywords and
     JEL codes.
   - An **AI-assistance statement** naming the tools and their roles
     (drafting, simulated refereeing, translation).
   - A "not investment advice" note.
   - Every paragraph carries a stable `% id:` comment.
10. **Referee panel.**
    - **Bundle.** Each round builds an immutable, secret-free bundle in a
      temp folder: the manuscript, `numbers.json`, `MANIFEST.json`, the study
      code snapshot and the refs. Quotes from private materials are removed
      unless the owner allows them.
    - **Isolation.** Referees run with that bundle as cwd, never the repo.
      The bundle is disposable, because agy's sandbox allows writes to its
      workspace. The invocations:
      - `codex exec --skip-git-repo-check --sandbox read-only -C <bundle>
        --output-last-message <file>` (the bundle is not a git repo);
      - `<agy path> -p … --model <id> --sandbox --disable-slash-commands
        --output-format json --print-timeout <t>`. The `agy` path is absolute
        (`tools/debate.py`, overridable by the `QUANTGEN_AGY` environment
        variable), because `agy` may not be on PATH in every shell.
        The JSON envelope supplies `status`, and its `response` is the
        Markdown report.
    - **Prompt.** The prompt is short and points at the files, which avoids
      the Windows command-line length limit.
    - **Report format.** Reports are Markdown with `## Major` and `## Minor`
      headings, and each issue carries a stable ID. Raw output and CLI versions
      are kept.
    - **Severity rubric.** *Major* means the result, conclusion or
      provenance would change.
    - **Revision.** Responses go in `review/response_round<k>.md`, and the
      loop runs at most 2 rounds. Analyses requested by referees go only into
      an "Exploratory analyses requested in review" section, through `run.py`
      with a new MANIFEST. Pre-specified results are never altered.
    - **Runner.** `tools/debate.py` is about 50 lines:
      - a subprocess call with UTF-8 input and output;
      - a timeout that kills the process tree;
      - branches for a missing CLI, an auth failure and **an exhausted
        quota**. It recognises Codex's "usage limit" message together with
        its reset time and records `REVIEW_INCOMPLETE` with that time.
      - On 2026-10-23 the owner's ChatGPT quota ran out until
        2026-10-27 19:16, so this case is real.
    - **Bounded work (D6).** Codex and agy may also take bounded drafting
      tasks in a bundle. Each gets a written brief carrying the project
      history and the exact task. Their output is reviewed before anything is
      merged.
11. **Korean edition.**
    - Template `tools/paper/template_ko.tex`: kotex/xetexko. Fonts load **by
      file path**: 함초롬바탕 (`HANBatang.ttf`/`HANBatangB.ttf`, static, with a
      real bold) for the body, and Malgun Gothic (`malgun.ttf`/`malgunbd.ttf`)
      for sans.
    - The translation is aligned paragraph by paragraph (by `% id:`), guided
      by `tools/paper/glossary_ko.yaml`. kotex's automatic particle commands
      are used after `\qnum`/`\cite`.
    - `tools/paper/consistency.py` fails when:
      - per-section `\qnum` usage counts differ between editions;
      - citation keys per section differ;
      - labels or refs differ;
      - any bare digit run appears in a results or robustness paragraph or a
        table body of either edition.
    - **Bilingual fidelity review.** Claude and Gemini read the aligned
      paragraph pairs and check signs, negations, qualifiers, units and claims
      of significance. The Korean edition passes the same release gate as the
      English one.
12. **Build.**
    - `tools/paper/build.py` runs `tectonic -X compile --keep-logs` with
      Tectonic 0.17.0 and a pinned bundle URL.
    - It parses `.log`/`.blg`, and fails on undefined references or
      citations, `Missing character`, BibTeX errors or overfull boxes over
      10 pt.
    - It records the sha256 of every font file used, with the Tectonic
      version, the bundle URL and the PDF's sha256, in `en/build.json` and
      `ko/build.json`. Malgun Gothic and 함초롬바탕 are system fonts, so the
      PDF is reproducible on this machine.
      Before any public release, the font files are swapped for OFL fonts kept
      in `tools/paper/fonts/`.
13. **Index.** `papers/INDEX.md` lists only released papers: title, both
    abstracts, PDFs, code, results and scientific status. An HTML portfolio
    waits until there are about five papers.

### 5.4 Layout

```
papers/INDEX.md
papers/<paper_id>/
  scope/   questions.md, literature.md, lit_*.md, integration.md, protocol.md, prereg.json, approval.json
  refs.yaml, refs.bib, claims.yaml, meta.yaml, .gitignore
  study/   run.py, data/, runs/<run_id>/{results.json, MANIFEST.json}, ledgers/, cache/ (ignored),
           numbers.json, numbers.tex
  common/  equations and shared tables (*.tex)
  en/      paper_en.tex, figures/, tables/, paper_en.pdf, build.json
  ko/      paper_ko.tex, figures/, tables/, paper_ko.pdf, build.json
  review/  round<k>_<name>.{md,json}, fidelity_<name>.{md,json}, response_round<k>.md,
           substitution.json, signoff.json, raw/
  STATUS   (DRAFT | REVIEW_INCOMPLETE | BLOCKED_MAJOR | OWNER_REVIEW | RELEASED)
tools/__init__.py, tools/debate.py
tools/paper/ __init__.py, qgpaper.sty, template_en.tex, template_ko.tex, glossary_ko.yaml,
             build.py, numbers.py, consistency.py, approval.py, refs.py, claims.py, study.py,
             bundle.py, panel.py, index.py, selfcheck.py
.claude/skills/quantgen-paper/SKILL.md
.claude/workflows/quantgen-paper-research.js, quantgen-paper-write.js
```

### 5.5 Tests and the first run

`tools/paper/selfcheck.py` is registered as suite `papers` with lazy imports.
It covers:
- `\qnum` keys with digits;
- `consistency.py` catching a planted bare digit, a missing citation key, a
  per-section macro-count drift and a dropped paragraph id;
- `refs.py` (reference verification) on an offline fixture;
- `debate.py` handling a missing CLI, a timeout, malformed output and a
  non-zero exit.

The compile check runs `tectonic --only-cached` on a sample that uses Korean
bold, `\emph`, display math, booktabs, natbib, a listing and a long URL. It
reports `NotRun` only when the Tectonic binary is absent or the cache is
missing a file. A font error or a TeX error is still a FAIL. The suite never
needs the network.

**Before the first real topic**, a synthetic fixture topic runs through both
workflows end to end, to prove that dispatch, the approval hash, the release
states and the build all work.

## 5A. Owner alerts (owner request, 2026-10-23)

The owner asked to be told on their phone, through Claude mobile, when the H2
cost-gate test is ready. Two local scheduled tasks (Claude desktop) are set:
- **`h2-holdout-ready-alert`**, one-shot at 2026-11-04 09:00 KST. Both
  profiles' 10 holdout sessions end on 2026-11-03, as computed with
  `verdict.holdout_sessions()` on 2026-10-23.
  - It reads both `out*/verdict.json` read-only.
  - It sends one push notification, "H2 holdout complete; readout ready; run
    by about 2026-12-19".
  - It runs nothing in `paper_live`.
- **`h2-readout-deadline-warning`**, one-shot at 2026-12-05 09:00 KST. It
  pushes only if H2 is still pending, two weeks before the 5-minute bars
  expire.

Push delivery relies on Remote Control, which is on for new sessions. The
originating session is also notified when each task completes. Scheduled tasks
run while the Claude app is open; a task that is due while the app is closed
runs at the next launch.

## 6. Out of scope

- An in-app Papers page and an HTML portfolio (later).
- Wiring `MA.GIT_HASH` to git (a separate owner decision).
- Any change to the frozen studies.
- All TRADEGEN work.
- Automatic publication.

## 7. Risks

| Risk | Mitigation |
|---|---|
| An edit silently changes frozen behaviour | Readouts run only from the tagged snapshot. `frozen_guard` checks the tag, the tagged pins, that no early look exists, and the library versions. |
| TRADEGEN writes into QUANTGEN's state or takes a second look | Hard prerequisites in the TRADEGEN brief (section 3.2) |
| Hallucinated or unsupported citations | `refs.py` verification records plus the `claims.yaml` gate; `unread` blocks release |
| Numbers drift from results | `numbers.json` provenance, `\qnum` only, bare-digit check, offline rerun |
| The Korean edition says something different | Shared math and tables, aligned paragraph ids, bilingual fidelity review, the same release gate |
| A referee CLI fails | `REVIEW_INCOMPLETE`; never read as "no objections" |
| A referee changes repo files | Disposable bundle as cwd; codex read-only |
| Researcher degrees of freedom | Protocol, prereg, a paper-local ledger, and requested analyses labelled exploratory |
| An undisclosed AI-written paper damages the portfolio | AI-assistance statement plus owner sign-off before release |

## Appendix A: referee round 1, issue by issue

C = Claude (ACCEPT WITH CHANGES), G = GPT/Codex (REJECT), M = Gemini/agy
(REJECT). Every issue below is accepted unless it is marked otherwise.

| Issue | Raised by | Ruling |
|---|---|---|
| Freeze protection uses an incomplete hand list; nothing guards H2; the prereg check prints instead of failing | C-M1, G-1 | Revision 2 added `frozen_guard` plus a closure manifest. Revision 3 replaced that with readouts from a tagged snapshot (section 3.1, Appendix A2). |
| TRADEGEN shares state and can take a second look | C-M2, G-2, M-2 | Section 3.2 prerequisites in the TRADEGEN brief |
| Phase 2 condition already met while pending | G-3 | Section 4.2 precondition; 2026-12-19 deadline (C-m7) |
| Regime removal incomplete | G-4, M-3, C-m2 | Full line list plus a registered crypto-page self-check |
| Referees can write into the repo | G-5 | Disposable bundles as cwd |
| The review loop lets unresolved majors through | G-6 | Release states; vetoes are not cleared by round limits |
| Reproducibility and number provenance too thin | G-7, C-M4, M-7.1 | MANIFEST schema, frozen inputs, immutable runs, offline rerun, `numbers.json`, `\qnum` via csname |
| "Use QUANTGEN's gate" is not a protocol | G-8, C-M4 | `protocol.md` with claim labels and status propagation |
| Citation checks metadata, not support | G-9, C-M5, M-7.2 | `verified` records plus `claims.yaml`; private materials only check derivations |
| Bilingual gate is structural only; figures English-only | G-10, C-M6, M-7.3 | Shared math, per-language figures, aligned ids, fidelity review |
| CLI protocol underspecified; Windows command-line length | G-11, M-8.1-2 | `debate.py` contract; short prompts pointing at files |
| TeX build guarantees not real; Batang has no bold; Noto KR is a variable font; biber missing | G-12, C-M7, M-6, C-m15 | Fonts by path (HANBatang/Malgun), natbib with plainnat, log parsing, pinned bundle, full-feature sample |
| The papers suite could kill `run_all` or need the network | C-M8 | Lazy imports, `NotRun`, `--only-cached` |
| Referee stop rule and forking paths | C-M9 | Severity rubric, max 2 rounds, requested analyses labelled exploratory |
| No AI-assistance disclosure | C-M10 | Disclosure plus owner sign-off |
| `git init` changed `repo_anchor` and broke T-LEDGER-01 | M-1 | Section 3.3 and Appendix B |
| Stage 6 code must pass T-CTX-01/T-RO-01/flet guards; trial ledgers | M-5, C-m12 | Section 3.4; paper-local ledger; scans extended to `tools/` and `papers/` |
| FMP disappears from Settings | M-4 | Moved into `quant_provider_status()` |
| `narrate_weekly_strategy` and `_SYSTEM` still trade-calling | C-M3, M-m4 | Section 4.1 A3; flagged for the owner |
| main.py `navigate`/`focus`, settings leftovers, components dead code, test docstrings, `macro_m8_pipeline` L133 | M-m1/2/3/5, C-m3/4/5/6 | Section 4.1 A1 |
| Test-count arithmetic; wrong critic references; A5 rationale; A5 legal wording | G-m1, M-m5, C-m1/9/10, G-m8 | Fixed (37 fewer tests, 811/690/121) |
| `config.py` deletion described as a range | G-m2 | Exact symbol list |
| `test_s4` wall-clock clause missing | G-m4 | Section 3.4 |
| Workflow contract (`paper_id`, approval hash, naming, dates in args) | G-m6, C-m14 | Section 5.1 |
| Over-engineering: four searchers, HTML portfolio, PNG critique, JSON parsing, mandatory UI | G-m7, M-m6, C-cut | Three searchers plus critic; `INDEX.md` only; log checks; Markdown headings; UI optional |
| Sending private course quotes to OpenAI/Google | C-m16 | Stripped from bundles unless the owner allows |
| `.claude/workflows/*.js` "not natively executed" | M-8.3 | **Rejected.** Claude Code's Workflow tool runs saved scripts from `.claude/workflows/`. The executor is now named in section 5.1. |
| Delete `grokteam/` from TRADEGEN | C-M2 option | **Not adopted**, because D1 says to keep a duplicate. In revision 3, TRADEGEN's copy keeps forward events permanently blinded (section 3.2). |

## Appendix B: git-state test impact (measured)

The full suite was run on 2026-10-23 after `git init`. Result: 725/848 PASS,
2 FAIL, 121 NOT_RUN. The baseline before git was 727 PASS, 0 FAIL, 121
NOT_RUN, so exactly two tests changed, and both read the live repo state:

| Test | Why it fails now | Fix in A0 (test-only; `gate_ledger.py` stays pinned and untouched) |
|---|---|---|
| `macro_m7_ledger::test_ledger01_refusals_and_null_distribution_runs` (L144) | It asserts `GL.repo_anchor() == UNVERSIONED`, which is "not a git repo". | Use `GL.repo_anchor(<temp dir without .git>) == UNVERSIONED`, and assert that `GL.anchored(GL.repo_anchor())` equals `(GL.REPO_ROOT / ".git").exists()`. |
| `macro_m7_ledger::test_sel01_b_…_only_anchored` (L410-412) | Its "unanchored commit" case relies on `t_fix`'s default commit, which is `repo_anchor()` and is now `git:<sha>`, so `UnanchoredTimestamp` is no longer raised. | Pass an explicit `commit=GL.Anchor(card["created_utc"], GL.UNVERSIONED, "header_commit")` for that case. The intent stays the same: an unanchored commit refuses step 3. |

All other tests that assert `UNVERSIONED` read the constants
`MA.GIT_HASH`/`lab.GIT_HASH`, which stay the same (section 3.3), and they pass.

## Appendix A2: referee round 2, issue by issue

**Verdicts.**
- C = Claude: ACCEPT WITH CHANGES. Of its 10 round-1 majors, 8 are resolved
  and 2 partly resolved; it raised 2 new ones.
- M = Gemini: ACCEPT WITH CHANGES. Of its 8, 5 are resolved and 3 partly
  resolved; it raised 5 new ones.
- G = GPT: **review incomplete**, because the Codex quota is exhausted until
  2026-10-27 19:16. GPT's round-1 issues are all answered in Appendix A.
  Under section 5.1's own rule, this is recorded as a gap, not as agreement.
  If the owner wants it, a GPT check of revision 3 can run after the quota
  resets.

| Issue | Raised by | Ruling |
|---|---|---|
| The closure misses the H2 readout scripts (`replay`, `verdict`, `power`), calendar and macro data files, and a dynamic import | C-3a | Superseded: readouts run from the tag (section 3.1), so nothing on main needs guarding |
| A guard freezing about 57 files until February leaves broken pages unfixable | C-3b | **Accepted in full**: tag plus a local clone at the tag (D9; a clone rather than a worktree, so ledger rows stay anchored). Main is free. The guard is down to four clauses with stated expiry. |
| "Disable the look write" in TRADEGEN still recomputes and prints the forward results on every run | C-2b | Section 3.2: forward events permanently blinded; PREREG never deleted |
| Workflow location unconfirmed; the approval check must be deterministic | C-2a | Section 5.1: Agent-tool fallback; `tools.paper.approval check` exit code |
| FMP row calls the deleted `skill_credential_present` | M-new1 | Section 4.1 A1: `fmp_ready()` and a new note |
| `FX:` trade wording (L464-469) and the insights self-check (L691-696) | M-new2 | Section 4.1 A3 |
| Extending `runtime_py()` scans would trip on docstrings; papers need the fill model | M-new3 | Section 3.4: only `_scan_files()` is extended; `papers/` allowed to import orders |
| The guard must not import `paper_live.engine` (it silences warnings at import) | M-new4 | Section 3.1: the guard uses git and hashlib only |
| README test table goes stale between commits; agy JSON vs Markdown; agy not on PATH | M-new5 | Section 4.1: one README update at the end. Section 5.3: JSON envelope plus Markdown body; absolute agy path |
| Codex refuses a non-git bundle | C-minor | `--skip-git-repo-check -C <bundle>` |
| Dirty-tree anchors | C-minor | Section 5.3 step 7: confirmatory runs refuse a dirty tree |
| Font portability | C-minor | Font sha256 recorded; OFL fonts before any public release |
| NotRun masking a real font failure | C-minor | Section 5.5: NotRun only when the binary or a cache file is missing |
| Guard clause expiry | C-minor | Section 3.1 (4) |

## Appendix C: evidence that `eacd57d` is both frozen states

Measured on 2026-10-23 from the git-tracked tree:
- The 10 PREREG-pinned files match their pins, for example `garch.py`
  2a8a0737, `book.py` b92c8af0.
- `paper_live/engine.py` (642fc67b) and `config.py` (dc712a9d) equal both
  `out*/frozen_rule/` copies.
- File modification times of tracked code and data, excluding outputs,
  backups and research text:
  - **After the H2 freeze (2026-10-20 01:11 UTC):** 12 files changed, all
    outside the readout path:
    - `paper_live/analyze.py`, `report.py`, `narrative.json`,
      `compare_text.json` and `compare_pdf.py` (the section-3 report
      corrections);
    - `.claude/launch.json`, `tests/paper_live_acceptance.py` and
      `tests/run_all.py`;
    - the new `grokteam/*` package, finished before its own freeze.
    - No file in `core/`, `data/` or root `config.py` changed, and neither
      did `paper_live/engine.py`, `config.py`, `replay.py`, `verdict.py` or
      `power.py`.
  - **After the GROKTEAM freeze (2026-10-22 04:30 UTC):** no tracked code or
    data file changed.
