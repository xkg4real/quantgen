# QUANTGEN Implementation Plans — Adversarial Referee Report

**Plans Reviewed:**
* **Plan A:** `docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md` (lines 1–3750)
* **Plan B:** `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md` (lines 1–5148)
* **Design Spec:** `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md` (lines 1–757)
* **Repository Baseline Checked:** `HEAD` (`238376a`) across 39 quoted-text edit blocks in 22 tracked files (`tests/run_all.py`, `tests/macro_m7_ledger.py`, `tests/acceptance.py`, `core/skills/__init__.py`, `config.py`, `ui/components.py`, `ui/settings_page.py`, `main.py`, `tests/macro_m8_pipeline.py`, `tests/macro_ui_components.py`, `.env.example`, `ui/krx_page.py`, `core/skills/pipeline.py`, `core/skills/macro_workflows/macro_daily.yaml`, `tests/macro_acceptance.py`, `docs/ARCHITECTURE_REVIEW.md`, `README.md`, `core/crypto/analytics.py`, `ui/crypto_page.py`, `tests/expansion_acceptance.py`, `docs/ASSET_EXPANSION_SPEC.md`, `docs/build_expansion_primer.py`, `core/ficc/insights.py`, `core/quant/insights.py`, `ui/macro_page.py`, `core/ficc/macro.py`, `tests/ficc_acceptance.py`, `pyproject.toml`, `tests/macro_m0_harness.py`). All single-plan edits match `HEAD` verbatim except the cross-plan collisions documented below. No step in either plan modifies `paper_live/`, `grokteam/`, or the byte-frozen `core/engine/` files, or invokes any forbidden live runner.

---

## Blockers

### [B1] Cross-plan edit collision in `tests/run_all.py` makes the second plan's Task 1 fail regardless of execution order
* **Plan:** Plan A (`docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md`) and Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Plan A Task 1 Step 3 & Task 5 Step 15 vs. Plan B Task 1 Step 12
* **Problem:** Plan B falsely states that Part A only touches `L41`, `L57`, and the word `cockpit` in `L111` of `tests/run_all.py`, claiming Plan B's edits apply cleanly before or after Part A. In fact, Plan A Task 1 Step 3 modifies the exact same three anchor lines (`L49–50`, `L64–65`, `L111`) to register the `guard` suite.
  * If Plan A runs first, `tests/run_all.py:65` no longer ends with `[(f"grokteam/{n}", f) for n, f in grokteam_tests()])` (it is followed by `+ [(f"guard/{n}", f) for n, f in guard_tests()])`), and `tests/run_all.py:111` ends with `paper, grokteam or guard")`, not `macro, paper or grokteam")`. Plan B Task 1 Step 12 Edit 2 and Edit 3 fail to match.
  * If Plan B runs first, Plan A Task 1 Step 3's quoted current text for `L49–50`, `L64–65`, and `L111` fails to match, AND Plan A Task 5 Step 15's verification script fails with `AssertionError` on `assert set(added) == ADDED` and `assert (len(now), total["PASS"], total["FAIL"], total["NOT_RUN"]) == (820, 699, 0, 121)` because the 43 `papers/*` tests and `macro/macro_m0_harness/test_t_ro_01_paper_and_debate_tools_and_agent_prompts_are_clean` are already in `qa/acceptance_results.json`.
* **Evidence:**
  * `tests/run_all.py:49-50`, `tests/run_all.py:64-65`, `tests/run_all.py:111`
  * `docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md:239-256` (Plan A Task 1 Step 3 edits `L49–50`, `L64–65`, `L111`)
  * `docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md:3545-3568` (Plan A Task 5 Step 15 hard-codes `ADDED` and `(820, 699, 0, 121)`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:75`, `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:868-895` (Plan B Task 1 Step 12 quotes pre-Plan-A `L64–65` and `L111`)
* **Fix:** Specify a deterministic execution order (Plan A before Plan B) and provide post-Plan-A anchors in Plan B Task 1 Step 12 (`from tests.frozen_guard import tests as guard_tests`, `+ [(f"guard/{n}", f) for n, f in guard_tests()])`, and `paper, grokteam or guard"` -> `paper, grokteam, guard or papers"`), or provide explicit pre-Plan-A / post-Plan-A variants in both plans.

---

### [B2] Stage 4 (`debate`) and Stage 9 (`review`) workflows never invoke the Claude panelist sub-agent, causing `gate_debate` and `gate_review` to fail closed on missing `critique_claude.md` / `review_claude.md`
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 3 Step 10 (`tools/paper/panel.py`), Task 5 Step 3 (`quantgen-paper-research.js`), Task 5 Step 4 (`quantgen-paper-write.js`), and Task 5 Steps 31 & 34 (dry-run)
* **Problem:** Per Spec §4.3 and §4.4, the 3-model panel consists of two external CLIs (`gpt_codex`, `gemini_agy`) run by `tools/paper/panel.py` plus an in-session Claude sub-agent (`paper-critic` in Stage 4 writing `debate/round_<r>/critique_claude.md`; a fresh isolated `paper-referee-claude` in Stage 9 given ONLY `reviews/round_<r>/bundle/` writing `reviews/round_<r>/review_claude.md`). `tools/paper/panel.py` (`run_debate` and `run_review`) only runs the two external CLIs and checks `claude_path.is_file()` afterward (recording `"claude_present": False`). However, neither `.agents/workflows/quantgen-paper-research.js` nor `.agents/workflows/quantgen-paper-write.js` ever invokes a `paper-critic` or `paper-referee-claude` sub-agent to write `critique_claude.md` or `review_claude.md`. Instead:
  1. `quantgen-paper-research.js` `prompts.debate` falsely tells `paper-chair`: `"tools.paper.panel has written ${REL}/debate/round_1/manifest.json and the three critique_*.md files. 1. Read every Blocker and Major across critique_gpt.md, critique_gemini.md and critique_claude.md."`
  2. `quantgen-paper-write.js` `stagePrompts.review` tells `paper-chair`: `"Read ${rel(ctx)}/reviews/round_${round}/manifest.json and the three review_*.md files."`
  3. Immediately after `ctx.agent.run` finishes, `cliGate(ctx, "debate")` / `cliGate(ctx, "review")` calls `gate_debate` / `gate_review`, which require `critique_claude.md` (>= 80 chars) and `review_claude.md` (>= 120 chars) for all three `PANEL_ROLES = ("gpt", "gemini", "claude")`, failing closed every time.
* **Evidence:**
  * `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:391-409`, `449-468`
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:3153-3156`, `3213-3292` (`tools/paper/panel.py` runs only `D.DEFAULT_REFEREES` = `gpt_codex`, `gemini_agy`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:1940-1959`, `2043-2065` (`gate_debate` and `gate_review` require `critique_claude.md` and `review_claude.md`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4135-4146`, `4173-4185` (`quantgen-paper-research.js` never invokes `paper-critic`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4227-4236`, `4265-4274`, `4364-4382` (`quantgen-paper-write.js` omits `paper-referee-claude` from `ROLES` and never invokes it before `stagePrompts.review`)
* **Fix:** In `quantgen-paper-research.js` (Stage 4 `debate`), invoke `ctx.agent.run({ role: "paper-critic", ... })` using `tools.paper.panel.debate_prompt` to write `debate/round_1/critique_claude.md` before `cliPanel` (or before `paper-chair` runs), so `manifest.json` records `claude_present: true`. In `quantgen-paper-write.js` (Stage 9 `review`), add `claudeReferee: "paper-referee-claude"` to `ROLES` and invoke a fresh sub-agent restricted to `reviews/round_${r}/bundle/` with `tools.paper.panel.review_prompt` to write `reviews/round_${r}/review_claude.md` before `paper-chair` synthesises the three reports.

---

### [B3] `quantgen-paper-write.js` Stage 6 (`implement`) and Stage 7 (`study`) dirty the git working tree before `start_run` and `gate_archive`, causing `StudyRefused` and `gate_archive` failures
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 2 Step 10 (`tools/paper/study.py` & `tools/paper/gates.py`) and Task 5 Step 4 (`quantgen-paper-write.js` Stages 6, 7, 11)
* **Problem:** Two step sequences in `quantgen-paper-write.js` leave tracked files modified and uncommitted in the working tree while downstream gates require a clean tree:
  1. **Stage 6 -> Stage 7 (`qa/acceptance_results.json` dirtied):** Stage 6 (`implement`) Step 2 instructs the agent to run `python tests/run_all.py --suite <each suite you touched>`. Every invocation of `tests/run_all.py` unconditionally overwrites the git-tracked file `qa/acceptance_results.json` (`tests/run_all.py:92, 123`). Stage 6 Step 3 instructs: `"Commit the core/ and tests/ files"`, and global Rule 2 forbids `git add -A` / `git add .`. When Stage 7 (`study`) then calls `tools.paper.study.start_run(paper_dir, ...)`, `start_run` runs `_git(root, "status", "--porcelain")` across the entire repo root (`tools/paper/study.py:2461`) and immediately raises `StudyRefused("dirty working tree; commit or stash before start_run")` because `qa/acceptance_results.json` is modified.
  2. **Stage 7 Step 4 -> Step 5 (`study/numbers.json` dirtied by offline rerun):** Stage 7 Step 2 specifies that `study/run.py` calls `write_numbers` at the end of the run with `source: "runs/<run_id>/results.json:<field>"`. In Step 4, the online run writes `study/numbers.json` with the first `run_id` and commits `study/data`, `study/runs`, `study/ledgers`, `study/numbers.json`, and `study/numbers.tex`. In Step 5, the offline rerun (`python ${REL}/study/run.py --offline --now <a later UTC time>`) generates a new `run_id` and overwrites `study/numbers.json` with `source` pointing to the second `run_id`. Step 5 then instructs: `"Commit the second run directory."` This leaves `study/numbers.json` modified and uncommitted in the working tree, which causes any subsequent `start_run` (in Stage 10 `revise`) and `gate_archive` (`git status --porcelain -- <paper_dir>`) to fail.
* **Evidence:**
  * `tests/run_all.py:92`, `tests/run_all.py:123` (`OUT = ROOT / "qa" / "acceptance_results.json"` written on every `--suite` run)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:2461-2464` (`tools/paper/study.py:start_run` checks repo-wide `_git(root, "status", "--porcelain")`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:2131-2140` (`tools/paper/gates.py:gate_archive` checks `git status --porcelain -- <paper_dir>`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4310-4326` (`quantgen-paper-write.js` Stage 6 Steps 2–3 and Stage 7 Steps 2, 4, 5)
* **Fix:**
  1. In Stage 6 Step 2, either restore `qa/acceptance_results.json` (`git checkout -- qa/acceptance_results.json`) after running `--suite`, or scope `start_run`'s cleanliness check in `tools/paper/study.py:2461` to `paper_dir`, `core/`, `data/`, and `tools/`.
  2. In Stage 7 Step 5, commit `study/numbers.json` and `study/numbers.tex` alongside the second run directory (which also ensures `study/numbers.json` matches `runs[-1]` bundled by `tools/paper/bundle.py:3126-3127`).

---

### [B4] Plan B Task 6 Step 2 `README.md` edit anchor does not exist after Plan A and omits the `+1` `macro_m0_*` test count increase
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 6 Step 2 (`README.md`) and Task 5 Step 27 (`tests/macro_m0_harness.py`)
* **Problem:**
  1. Plan B Task 6 instructs running Task 6 *after* Part A's README commit if Part A is executed (`line 4955`), claiming *"the anchors below are chosen so they survive that edit"* (`line 4958`). However, Task 6 Step 2 Edit 1 quotes `expansion, macro, paper or grokteam` (`README.md:763`), which Plan A Task 5 Step 17 Edit 2 already replaced with `expansion, macro, paper, grokteam or guard`. The anchor does not exist after Plan A, and applying Plan B's replacement (`expansion, macro, paper, grokteam or papers`) would erase `guard`.
  2. Plan B Task 5 Step 27 adds `test_t_ro_01_paper_and_debate_tools_and_agent_prompts_are_clean` to `tests/macro_m0_harness.py`. Because `tests/macro_acceptance.py` auto-discovers every `test_*` function in `tests/macro_*.py`, the `macro` suite PASS count increases by `+1` (from `418` to `419` without Plan A, or from `419` to `420` after Plan A, and `macro_m0_*` in `README.md:798` increases from `37 / 2` to `38 / 2`, or `38 / 2` to `39 / 2` after Plan A). Task 6 Step 2 updates the `**Total**` row (`786/907` or `743/864`) and adds `| papers | ... | 43 PASS |`, but never updates the `| macro |` row (`README.md:783`) or the `| macro_m0_* |` row (`README.md:798`), leaving the table's row sum inconsistent with `**Total**`.
  3. Neither Task 5 Step 38 nor Task 6 Step 4 stages `qa/acceptance_results.json` after Task 5 Step 29 runs `python tests/run_all.py`, leaving `qa/acceptance_results.json` dirty at the end of Plan B.
* **Evidence:**
  * `README.md:763`, `README.md:783`, `README.md:786`, `README.md:798`
  * `docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md:3595-3645` (Plan A Task 5 Step 17 edits `README.md:763, 783, 786, 798`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4739-4755` (Task 5 Step 27 adds 1 test to `tests/macro_m0_harness.py`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4955-5016` (Task 6 Step 2 & Step 4)
* **Fix:** In Plan B Task 6 Step 2, provide both pre-Plan-A (`paper or grokteam` -> `paper, grokteam or papers`) and post-Plan-A (`paper, grokteam or guard` -> `paper, grokteam, guard or papers`) anchors for `README.md:763`, update the `| macro |` row (`420 PASS / 121 NOT_RUN` post-Plan-A, `419 PASS / 121 NOT_RUN` pre-Plan-A) and the `| macro_m0_* |` row (`39 / 2` post-Plan-A, `38 / 2` pre-Plan-A), and stage `qa/acceptance_results.json` in Task 6 Step 4.

---

## Majors

### [M1] `quantgen-paper-write.js` silently skips Stage 10 (`revise`) when invoked with `from: "revise"` and runs the full multi-round loop in `mode: "rereview"`
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 5 Step 4 (`.agents/workflows/quantgen-paper-write.js`)
* **Problem:**
  1. In `quantgen-paper-write.js`, `stages` is `["implement", "study", "draft", "review", "revise", "archive"]`, advertising `from: "revise"` as a valid resume point (as required by Spec §4.6 `--from <stage>`). However, inside the stage loop (`line 4417`), the code has `if (name === "revise") continue;` because `revise` is handled inside `reviewLoop` when starting from `review` or earlier. If an engineer resumes from `from: "revise"`, `review` is sliced off before the loop, `revise` is skipped by `continue`, and execution jumps straight to `archive`, which immediately fails `gate_archive` because Stage 10 and Round 2 review never ran.
  2. When `mode === "rereview"` (`line 4400`), `quantgen-paper-write.js` calls `reviewLoop(ctx)`, which does not stop after re-running the requested review round `r` — if the synthesis is not `"ready"`, it proceeds into Stage 10 (`revise`) and subsequent rounds.
* **Evidence:**
  * `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:490-491`
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4364-4425` (`quantgen-paper-write.js`)
* **Fix:** In `quantgen-paper-write.js`, when `start === "revise"`, run Stage 10 (`revise`) for `Number(a(ctx).round || 1)` and then enter `reviewLoop(ctx)` starting at `round + 1` before advancing to `archive`. When `mode === "rereview"`, run only the single round `Number(a(ctx).round || 1)` of `cliPanel` + Claude referee + `stagePrompts.review` + `cliGate("review")` and return.

---

### [M2] Referee `--only` filter in `tools/paper/panel.py` rejects the spec's `gpt|gemini|claude` names and contradicts `selfcheck.py`
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 3 Step 10 (`tools/paper/panel.py`), Task 5 Step 2 (`tools/paper/selfcheck.py`), and Spec §4.6
* **Problem:** Spec §4.6 specifies `--only gpt|gemini|claude`, and `test_b5_workflow_scripts_follow_the_rules_and_their_gates_hold` in `tools/paper/selfcheck.py` passes `only=["gpt"]` to `quantgen-paper-write.js` (`line 3982`), which forwards `--only gpt` to `python -m tools.paper.panel review`. However, `tools/paper/panel.py:_select` checks `want` against `{r.name for r in referees}` where `DEFAULT_REFEREES` has names `"gpt_codex"` and `"gemini_agy"` (`ROLE_TAGS = {"gpt_codex": "gpt", "gemini_agy": "gemini"}`). Passing `--only gpt`, `--only gemini`, or `--only claude` to `panel.py` raises `ValueError: unknown referee in ['gpt']; known here: ['gemini_agy', 'gpt_codex']`.
* **Evidence:**
  * `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:491`
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:2902-2915` (`tools/debate.py` `DEFAULT_REFEREES`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:3162`, `3201-3209` (`tools/paper/panel.py` `ROLE_TAGS` and `_select`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:3982` (`tools/paper/selfcheck.py` passes `only=["gpt"]`)
* **Fix:** In `tools/paper/panel.py:_select`, accept both the full referee names (`"gpt_codex"`, `"gemini_agy"`) and their short role tags (`"gpt"`, `"gemini"`), and ignore `"claude"` in external CLI selection (while handling `"claude"` in the workflow script so `--only claude` skips external CLIs and runs only the Claude referee sub-agent).

---

### [M3] Missing `supplement.tex` template in Task 4 and missing creation step in `quantgen-paper-write.js` Stage 8 (`draft`)
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 4 (`papers/_templates/`) and Task 5 Step 4 (`quantgen-paper-write.js` Stage 8 & Stage 11)
* **Problem:** `quantgen-paper-write.js` Stage 8 Step 3 instructs the agent to: `"Compile ${REL}/paper/paper.tex and ${REL}/paper/supplement.tex through tools.paper.compile.build_pdf"`, and `gate_archive` (`tools/paper/gates.py:2117`) requires `"paper/supplement.pdf"` in `MANIFEST.json`. However, Task 4 creates `papers/_templates/paper.tex` without any `papers/_templates/supplement.tex`, and Stage 8 Steps 1–2 instruct the agent to copy `paper.tex`, `references.bib`, `claims.json` and write `sections/01_introduction.tex .. 07_conclusion.tex`, `tables/*.tex`, `figures/*.pdf`, and `appendix/*.tex`—never instructing the agent to create `${REL}/paper/supplement.tex`. Calling `build_pdf` on a non-existent `${REL}/paper/supplement.tex` in Step 3 raises `CompileError: missing TeX file`.
* **Evidence:**
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:2117` (`gate_archive` requires `paper/supplement.pdf`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:3455-3695` (Task 4 creates 6 templates, no `supplement.tex`)
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4331-4340` (`quantgen-paper-write.js` Stage 8 Steps 1–3)
* **Fix:** Either add `papers/_templates/supplement.tex` in Task 4 and copy it in Stage 8 Step 1, or explicitly instruct the agent in Stage 8 Step 2 to write `${REL}/paper/supplement.tex` (inputting `../study/numbers.tex` and `appendix/*.tex`) before Step 3 compiles it.

---

### [M4] Plan B Task 3 Step 13 PowerShell smoke command uses `<` input redirection, which fails on Windows PowerShell
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 3 Step 13
* **Problem:** The Windows PowerShell smoke command on line 3025 uses `< <prompt_file>`:
  `$env:QUANTGEN_CODEX_REASONING="medium"; codex exec --skip-git-repo-check -s read-only - < <prompt_file>`
  In Windows PowerShell (`powershell.exe` and `pwsh`), the `<` operator is reserved and throws `ParserError: The '<' operator is reserved for future use.`
* **Evidence:**
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:3025`
* **Fix:** Replace `< <prompt_file>` in the PowerShell command with `Get-Content <prompt_file> -Raw | codex exec --skip-git-repo-check -s read-only -`.

---

### [M5] Plan B Task 5 Steps 30–37 dry-run in a `git worktree` leaks git tags/branches into the main repository and runs before Task 5's `tests/macro_m0_harness.py` commit
* **Plan:** Plan B (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md`)
* **Task / Step:** Task 5 Steps 30–37
* **Problem:**
  1. Step 30 creates the scratch worktree at `HEAD` (`git worktree add C:/Users/whydi/AppData/Local/Temp/quantgen-dryrun -b dryrun/fixture HEAD`) *before* Step 38 commits Task 5's files. Inside the worktree, Stage 11 (`archive`, `quantgen-paper-write.js:4350`) creates an annotated git tag `paper/2026-dryrun-fixture/v1`, and `quantgen-paper-research.js:4031` instructs the agent to commit on branch `paper/2026-dryrun-fixture`. Because git worktrees share the parent repository's `.git/refs/tags` and `.git/refs/heads`, Step 37 (`git worktree remove --force ...` and `git branch -D dryrun/fixture`) leaves the dry-run tag `paper/2026-dryrun-fixture/v1` (and branch `paper/2026-dryrun-fixture`, if created) permanently in the main repository.
  2. Step 37 states that `git status --porcelain` is expected to list only `tools/paper/selfcheck.py`, `tests/macro_m0_harness.py`, and `.agents/`, overlooking `M qa/acceptance_results.json` modified by Step 29 (`python tests/run_all.py`).
* **Evidence:**
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4031`, `4350`
  * `docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4812-4925` (Task 5 Steps 29–38)
* **Fix:** In Task 5 Step 37, also run `git tag -d paper/2026-dryrun-fixture/v1` (and `git branch -D paper/2026-dryrun-fixture 2>/dev/null || true`), and include `qa/acceptance_results.json` in the expected `git status --porcelain` output (or commit Task 5 before the dry-run worktree step).

---

## Minor

* **Plan A Task 5 Step 15 (`docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md:3547`):** `subprocess.check_output(["git", "show", "HEAD:qa/acceptance_results.json"], text=True)` omits `encoding="utf-8"`, using Windows `cp949` by default (works today because `qa/acceptance_results.json` is ASCII, but violates the repo's explicit-encoding convention).
* **Plan B Task 5 Step 4 (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4031` vs. `4102, 4118, 4131, 4144, 4158`):** `RULES` Rule 2 says *"After a stage passes its gate, make one git commit"*, whereas the stage prompts instruct the agent to commit *inside* `ctx.agent.run` *before* `cliGate` runs.
* **Plan B Task 5 Step 4 (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4348`):** Typo in Stage 11 (`archive`) prompt Step 3: `"Call tools.paper. study / manifest helper or write ${REL}/MANIFEST.json"` (there is no manifest helper in `tools.paper.study`).
* **Plan B Task 5 Step 4 (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:4350`):** Stage 11 Step 5 stages only `MANIFEST.json`, `README.md`, `paper.pdf`, and `supplement.pdf`; if Step 1 recompiled the PDFs, `paper.log`/`paper.synctex.gz`/`supplement.log`/`supplement.synctex.gz` must also be staged or ignored so `gate_archive` does not fail on dirty files under `paper/`.

VERDICT: READY WITH FIXES
