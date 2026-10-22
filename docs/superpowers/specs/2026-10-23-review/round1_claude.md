# Referee report: `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`

Reviewer: Claude (adversarial). Method: read-only. I used Read, Grep, Glob, `sha256sum` and `sed`, plus stdlib-only `python -c` run outside the repo to check package versions. I ran no repository Python.

## What checks out

- **`prereg.check()` scope.** It hashes exactly the 10 fixed files (`grokteam/prereg.py:32-36`, `77-78`, `159-160`). It also compares `RULES`, `ACCOUNTS`, `VERDICT`, `model_digest()` (`book.py:396-401`: garch.py bytes plus the source of `model_at`/`_group`) and the library versions. It does **not** enumerate directories, hash root `config.py` or read any README. Check mode is read-only.
- **Frozen files are intact today.** All 10 pinned files match `grokteam/out/frozen_book/`. `paper_live/engine.py` (642fc67b…) and `paper_live/config.py` (dc712a9d…) match both `out*/frozen_rule/` copies. The installed versions are numpy 2.3.5, scipy 1.18.0, pandas 2.3.3 and Python 3.13.14, which match `PREREG_book.json`.
- **Phase 1 does not void either study.** None of its files is pinned, in `paper_live/`, or in the test_s4 set. Root `config.py` keeps every name the frozen code reads: `macro_dir`, `HTTP_TIMEOUT_SECONDS`, `upbit_*` and `NO_DATA_GRACE_TICKS`.
- **The cockpit importer list is complete.** Non-cockpit importers are `main.py:46,67,69,70`, `ui/components.py:18`, `ui/settings_page.py:18-19`, `tests/acceptance.py` and `tests/macro_m8_pipeline.py:132`. There are no dynamic imports. `macro_daily`/`pipeline`/`alerts` import only each other, so emptying `core/skills/__init__.py` is safe. The `main.py` count assert (`macro_m8_pipeline.py:519`) survives.
- **The acceptance.py split is right.** There are 47 tests. Keeping test_08, 09, 13-18, 21 and 22 keeps 10 and removes 37. test_10-12 do import `core.skills.runner` (`acceptance.py:185-214`).
- **Line references are almost all correct:** crypto self-check L430-435; macro_ui_components L120-127; ficc_acceptance L668-675; README L674-678; krx_page L1/L189; ARCHITECTURE_REVIEW:60; ASSET_EXPANSION_SPEC:177; build_expansion_primer:662.
- **ficc_acceptance L668-675 needs no change.** It asserts only that `report_prompt` returns something truthy, not its wording.
- **Tectonic and Codex are installed.** Tectonic 0.17.0 is at `~/.local/bin`, and its cache already holds `kotex.sty`/`xetexko.sty`, so a Korean build has worked on this machine. Codex is codex-cli 0.163.0.

---

## MAJOR issues

### M1. Freeze protection relies on a partial hand list and a manual check, and nothing guards H2 (§3.1, §3.2, §4.1 Verification)
- **Problem.**
  - §3.1's list of "unpinned dependencies" is copied from split_map §4.1 and misses modules the frozen code imports at load time:
    - `core/quant/gjr.py`, imported at the top of `vol_estimators.py:32`, which `forecast_eval.py:35` imports at its top;
    - `core/rules/validation.py`, `core/rules/model.py` and `core/quant/instruments.py`, imported by `macro_rules.py:24-27`, which `forecast_eval.py:37` imports;
    - `core/quant/history.py`, imported at the top of `strategies.py:32` (on the H2 runtime path through `engine.py:275`). It also imports `config` and `core.markets` (`history.py:44-45`).
  - An implementer reading §3.1 would treat these as free to change. One bad import breaks the GROKTEAM look and the H2 readout.
  - §4.1's verification checks only GROKTEAM (prereg check plus pinned shas, which duplicate each other). Nothing checks H2.
- **Fix.** Replace the hand lists with a guard test of about 15 lines, `tests/frozen_guard.py`, registered in `run_all.py`:
  - `assert grokteam.prereg.check() == []`;
  - the sha256 of `paper_live/engine.py` and `paper_live/config.py` equals both `out*/frozen_rule/` copies;
  - optionally, the AST import closure of the 10 pinned files plus `paper_live/engine.py` imports cleanly.

  Every suite run then proves both freezes intact, including during Part B, and §4.1 can drop its manual sha bullet. State the protected set as "the import closure of the pinned and frozen files", not a list.

### M2. TRADEGEN copies can contaminate QUANTGEN's study of record (§2 D1, §4.0, §3)
- **Problem.** D1 keeps the BOOK look in QUANTGEN, but TRADEGEN holds byte-identical `grokteam/` and `paper_live/` code.
  - **Two looks.** If TRADEGEN runs `grokteam.book` on or after 2027-02-01, it writes its own `FORWARD_LOOK.json` (`book.py:841-842`). The "one look" can then be taken twice, and a look can be chosen after the fact.
  - **Shared ledgers.** Both copies register trials in `config.macro_dir()/ledgers` by default, which is `~/.nextgen/macro/ledgers` (`book.py:739`, `paper_live/engine.py:104`).
  - **Shared cache.** Both share `~/.nextgen/grokteam` (`book.py:60`).
  - **False test failures.** If a TRADEGEN app starts (`on_app_start` writes `~/.nextgen/macro`) while QUANTGEN's suite runs, T-HERM-02 fails falsely (`tests/macro_acceptance.py:113-121`; split_map 8.3-6). That would corrupt the Phase 1 before/after counts.
  - §4.0 hands all of this to "the TRADEGEN session". QUANTGEN's records are the ones at risk.
- **Fix.** Add a §3 constraint:
  1. Nothing in TRADEGEN runs, app or tests, until its `.env` sets `QUANTGEN_MACRO_DIR`, `GROKTEAM_DATA`, `GROKTEAM_LEDGER_DIR` and `NEXTGEN_TRADING_DIR`.
  2. TRADEGEN never runs `grokteam.book` on or after `FORWARD_END`. Simplest: delete `grokteam/` from TRADEGEN, since the desk has no remaining work except the look, which D1 assigns here.

### M3. A3 is inconsistent with D3: deterministic trade calls and the trading-desk persona survive (§4.1 A3)
- **Problem.**
  - `core/ficc/insights.py::narrate_weekly_strategy` (L409-490) emits trade calls on every Macro page view: "Duration: lean long" (L421), "Curve: run steepeners/flatteners" (L446-450) and "Carry: long X … funder" (L480). README L670-673 advertises "the carry long and its funder".
  - `_SYSTEM` keeps "the voice of a sell-side rates/FX strategist writing for a trading desk" and "the operator knows financial risk is theirs" (`core/quant/insights.py:270-276`). The spec swaps only two phrases.
  - D3 says to strip "the trade-idea parts". These are the most explicit trade ideas left in the app, and the spec does not mention them. Split_map 3.3 recommended relabelling `narrate_weekly_strategy` as a "descriptive read".
- **Fix.** Get an explicit owner ruling. If relabelled (recommended), the descriptive version reads, for example, "10y +1.2σ above its 1y mean", "2s10s in a bull-steepener regime", "highest carry-to-vol: X; lowest carry: Y". Rewrite `_SYSTEM` as a research-commentary persona. Then update `tests/ficc_acceptance.py:744-763`, which asserts `f"long {best.ccy}"`, and possibly `:660-665`. Add both to the expected test changes.

### M4. "Reproducible" and "pre-registered" are not enforced (§5.2 step 5, §5.3 step 7)
- **Problem.**
  - `MANIFEST.json` hashes only the outputs. There is no snapshot of input data. FRED, Yahoo and KIS pulls change and expire, and `history.py` reads through the TTL cache `~/.nextgen/ficc_cache`.
  - Nothing records the environment or git commit.
  - "Frozen before the run" has no mechanism. The existing prereg style (`prereg.freeze`: refuse a rewrite, pin code shas, register ledger trials) is cited but not required.
  - There is no trial-ledger policy, so paper studies would not enter the honest global N.
  - Confirmatory tests on historical data the author (or Claude) has already used are not pre-registration in any strong sense. Several of the same series appear in `docs/asset_expansion/results.md` and `docs/vol_backtest/`.
- **Fix.**
  - `run.py` freezes raw inputs under `study/data/` with sha256, as `paper_live/engine.py` already does. It sets `NEXTGEN_FICC_CACHE` to a study-local directory and records `gate_ledger.repo_anchor()`, the library versions and the seeds in `MANIFEST.json`.
  - `run.py` refuses to run unless `prereg.json` is committed (it checks the git anchor and the file sha) and its pinned code shas match.
  - Confirmatory runs register their trials in a per-paper ledger family.
  - The paper states prior data exposure, and confirmatory claims use a holdout dated after the freeze where possible. Otherwise the paper calls them "pre-specified on historical data".

### M5. Citation verification checks metadata, not claims, and keeps no evidence (§5.2 steps 2-3)
- **Problem.**
  - A DOI or Crossref match confirms that the entry exists. It does not confirm that the source supports the sentence citing it, which is where hallucinated citations do real damage.
  - A "verified" verdict from an LLM agent is just another unverifiable claim unless the evidence is stored.
  - Step 2(c) cites private course materials (EE364A slides, CS229 notes, STAT248 notes, `26년 2학기 수업자료`) and the owner's unpublished notes in a journal-style paper. These are weak sources in a paper and may raise permission issues.
- **Fix.**
  - Each bib entry carries a `verified` field (Crossref or publisher URL, retrieval date, fetched title), and `selfcheck` fails on any entry without one.
  - For each `\cite` in the results, model and literature sections, the draft keeps a claim → page/quote anchor in `refs_claims.md`, which a separate agent checks against the source.
  - Use the study materials to verify derivations. Cite the published book they correspond to (Shreve 2004, Boyd & Vandenberghe 2004) with page numbers, not the slides.

### M6. The layout does not deliver "fully bilingual", and `consistency.py` checks the wrong thing (§5.3 step 10, §5.4)
- **Problem.**
  - `ko/` has no `figures/` (§5.4), so the Korean edition reuses English-labelled matplotlib figures.
  - Both editions `\input` the same `numbers.tex`, so "same numbers.tex macros" is trivially true.
  - The real drift risk is a translator agent turning `\resultX` into a literal number, or dropping a sentence that carries a number. Nothing checks for that.
- **Fix.**
  - `run.py` renders each figure twice (`lang='en'|'ko'`) into `en/figures/` and `ko/figures/`. Matplotlib needs a Korean font (`malgun.ttf` is installed), or use language-neutral figures with translated captions only.
  - `consistency.py` compares macro **usage counts per section**, citation keys per section, labels and `\ref`s.
  - `consistency.py` fails on any bare digit run in a results or robustness paragraph that is not inside a macro, in either edition.

### M7. The Korean font choice will degrade or fail, and is not reproducible (§5.3 step 10)
- **Problem.**
  - `C:/Windows/Fonts/batang.ttc` holds Batang, BatangChe, Gungsuh and GungsuhChe, but **no bold weight**. Every `\textbf`, section heading and theorem label in Korean gets fake bold or a fontspec warning.
  - The installed Noto Sans KR is **`NotoSansKR-VF.ttf`, a variable font**. XeTeX/xdvipdfmx (Tectonic) loads only its default instance, so the requested bold is not available.
  - Batang is a Microsoft font that cannot be redistributed, so another machine cannot rebuild the PDF.
- **Fix.**
  - Use 함초롬바탕, which is installed as static `HANBatang.ttf` and `HANBatangB.ttf`, for the body. Use static Noto Sans KR or Malgun Gothic (`malgun.ttf`/`malgunbd.ttf`) for sans.
  - Better: put OFL static Noto Serif/Sans KR OTFs in `tools/paper/fonts/` and load them by path.
  - The two-page selfcheck sample must use Korean bold, `\emph`, display math, a booktabs table, a natbib citation and a listing, so a font problem fails there.

### M8. The `papers` suite in `run_all.py` makes the main suite depend on an external binary and the network (§5.5)
- **Problem.**
  - `run_all.py` imports every suite at load time (`tests/run_all.py:41-49`). An ImportError in `tools/paper/selfcheck.py` would kill the whole runner. Split_map §2 flagged exactly this failure mode for grokteam.
  - Compiling the sample needs `tectonic` on PATH and, on first use, network access. The Tectonic cache (51 MB) has kotex/xetexko but not natbib, hyperref, booktabs or listings.
  - A machine without Tectonic, such as TRADEGEN's or a fresh venv, would turn the suite red.
  - Each run already takes about 646 s.
- **Fix.**
  - Import lazily inside each test function.
  - Raise `tests.notrun.NotRun("tectonic not found")` when the binary or the network is missing.
  - Or keep the compile check out of `run_all` and run it as the first step of the write workflow. Only the pure-Python `consistency.py` and `debate.py` checks belong in `run_all`.
  - `tools/` and `tools/paper/` need `__init__.py`.

### M9. The referee panel cannot run as written, and its stop rule invites forking paths (§2 D6, §5.3 step 9)
- **Problem.**
  - `agy` is not installed. `which`/`where.exe` find nothing. `AppData/Local/Programs/antigravity/resources/bin` holds only `language_server.exe`. A `gemini` CLI shim exists in `AppData/Roaming/npm`.
  - The model id `gemini-4-argon-high` and the `agy` flags are unverified.
  - "Stop when no referee raises a major issue" almost never happens with LLM referees, so every paper will run 3 rounds.
  - Referees will ask for new analyses after the pre-registration. Unless those are labelled, they become undisclosed researcher degrees of freedom.
- **Fix.**
  - Verify the Gemini route (install `agy` or use `gemini -p`) and the flags with `--help` before the plan is written.
  - Define a severity rubric: "major" means the result or conclusion changes.
  - Any analysis added in response to a referee goes in an "Exploratory analyses requested in review" section. Its numbers come only through `run.py` with a new MANIFEST, and the confirmatory results stay untouched.

### M10. The papers carry no AI-assistance disclosure (§5.3 step 8)
- **Problem.** Each paper is drafted, revised, refereed and translated by LLMs and published under "Geon Koh, Korea University" for a career portfolio. Elsevier, Springer Nature and arXiv policies require AI-use disclosure and human accountability. If an undisclosed AI-written paper surfaced in hiring, it would hurt the portfolio's credibility more than any single error.
- **Fix.**
  - Add an "AI assistance" statement to the front matter of both editions, naming the tools and their roles: drafting, referee simulation, translation.
  - Add an owner sign-off checkpoint ("I have read and verified every claim") before the PDFs count as final and enter `INDEX.md`.

---

## MINOR issues

| # | Spec section | Problem | Evidence | Fix |
|---|---|---|---|---|
| m1 | §4.1 Verification | "37 tests plus the regime self-check" is wrong. `expansion/selfcheck_crypto_analytics` stays a test; only L430-435 inside it go. | `tests/expansion_acceptance.py:343`; `qa/acceptance_results.json` (848 = 727 PASS + 121 NOT_RUN) | Expect 811 = 690 PASS + 121 NOT_RUN after A1-A5. Removing L434-435 shifts the rng stream feeding `weekday_table` (L438-439). The 50-point weekday offset makes that assertion robust, but confirm it in the after-run. |
| m2 | §4.1 A2 | Missed regime uses in `ui/crypto_page.py`: docstring L1, components bar chart L189-191, self-check L236 (`"regime score" in t`) and L238 (`p["regime"]`). Also the `analytics.py` docstring L2 and L15. The crypto_page self-check is not registered, so it would rot silently. | `ui/crypto_page.py:1,182,189-191,236,238`; `core/crypto/analytics.py:2,15`; registration list `tests/expansion_acceptance.py:334-343` | Add these lines to A2. |
| m3 | §4.1 A1 | "Inline a 4-value State enum" adds code. `STATE_STYLE`, `readiness_chip`, `RUN_STATUS_STYLE` and `run_status_chip` are used only by the deleted cockpit pages. | `ui/components.py:18,22-36,62-69`; users only `ui/skills_page.py:32`, `workflows_page.py:51`, `runs_page.py:16` | Delete them and the import, and reword the module docstring (L1-6, "for the cockpit"). |
| m4 | §4.1 A1 | settings_page `.env` snippet: the spec names only the ALPACA/FINVIZ lines; `NEXTGEN_SKILLS_ROOT=` and `FXMACRODATA_API_KEY=` are also there. The readiness count rows and the Interpreter and Run-timeout rows use `skill_python`/`SKILL_TIMEOUT_SECONDS`. | `ui/settings_page.py:181-187,192-196` | List the whole range. |
| m5 | §4.1 A1 | The negative check is L132-**133**: L133 dereferences `W`. | `tests/macro_m8_pipeline.py:132-133` | Replace both lines with `assert importlib.util.find_spec("core.skills.workflows") is None`. |
| m6 | §4.1 A1 | Dangling text not listed: README "all nineteen entries" (L746, inside the ~L738-747 range but the count must become sixteen); L763 `--suite` list; L777 row (47 → 10, renamed safety); L786 Total; `.env.example:3` "KRX/skills pages"; `tests/acceptance.py:1`; `tests/macro_acceptance.py:8,116`; `ui/krx_page.py:3` ("72 skills"). The `focus` path in `main.py:161-166` becomes dead. | the cited lines | Add them to the A1 text list and drop `focus`. |
| m7 | §3.2 | "No byte change to `paper_live/engine.py` or `config.py`" reads as root `config.py`, which A1 edits. "Confirmed with `verdict.holdout_sessions()`" could be misread as running `python -m paper_live.verdict`, whose `main()` writes `verdict.json`. | `paper_live/verdict.py:68-80,174` | Write `paper_live/config.py`. Say "call the function; never run the module before the readout". Also note the readout deadline: the holdout replay pulls 5-minute bars with 60-day retention, so it must run by about 2026-12-19 (`paper_live/replay.py:41,147`). |
| m8 | §4.1 Verification | "touches none of the constraint-3 files" is ambiguous: §3 item 3 or all of §3? `qa/acceptance_results.json` is tracked, so every suite run dirties the tree. | `git ls-files qa` | Give an explicit `git diff --stat eacd57d -- paper_live grokteam core/quant core/engine core/calendars core/markets.py core/ficc/pit.py …` that must be empty. Say whether the results file is committed with each group. |
| m9 | §4.1 A5 | The rationale "the prereg check's view of that folder is not verified" is false. `check()` hashes a fixed tuple. A README inside `grokteam/` would not void the look; a new `.py` would only be scanned by `selfcheck.test_no_paper_live_import`. | `grokteam/prereg.py:32,77-78,159-160`; `grokteam/selfcheck.py:279-282` | Keep the root-README decision and correct the reason. |
| m10 | §4.1 A5 | "The venue is illegal for Korean residents to trade" overstates the legal research. Kalshi non-sports contracts are rated "Grey, treat as illegal", with no Korean ruling. | `reports/Korean resident trading venue legality.md:16,112` | Write "treated as unlawful for Korean residents (no ruling yet; see the legality report)". |
| m11 | §4.1 A1 | The owner's `.env` clean-up omits the broker-adjacent `KIS_ACCOUNT_PD` and the unused `TYPESAFE_API_KEY`. | split_map 8.3-7 | Add them to the owner's list. |
| m12 | §5.4 / §3 | The P0 order-path scans cover only `core/`, `data/`, `ui/`, `main.py`, `config.py` and `docs/*.py`. New `papers/**/study/*.py` and `tools/debate.py` (subprocess) escape them. | `tests/acceptance.py:48-54`; `tests/macro_m0_harness.py:63-65` | Add `tools/` and `papers/` to `_scan_files()`. |
| m13 | §5.3 step 6 | Likely first topics (#1 GARCH, #5 forecast evaluation, #11-13 the gate) sit on files pinned until 2027-02-01. | split_map §6 rows 1, 5, 11-13 | State that defects found in pinned code go to the paper's limitations with the pinned sha, not into fixes, until the look is taken. |
| m14 | §5.1 | Workflow scripts cannot call `Date.now()`/`new Date()` and have no filesystem access. `/quantgen-paper write <slug>` does not match the `papers/<date>-<slug>/` folder name. | workflow-authoring reference | Pass the date in `args`; resolve the slug by glob. |
| m15 | §5.3 step 11 | Tectonic does not fail on undefined references, undefined citations or overfull boxes; it only warns. No component parses the log. The bib style is unnamed. | n/a | Use `tectonic -X compile --keep-logs` plus a log grep of about 10 lines in the build script. Use `plainnat`, and `xurl` for bibliography URLs. |
| m16 | §5.3 step 9 | Sending paper drafts that quote the owner's course materials to OpenAI and Google CLIs. | n/a | Strip private-material quotes from what referees receive, or get the owner's explicit OK. |

---

## Over-engineering to cut

1. **`papers/index.html`, `build_index.py`, design-system tokens and the `design:design-critique` pass.** A LaTeX article template fixes its own layout, and with one paper a hand-kept `INDEX.md` is enough. Add the page when there are five papers.
2. **The pypdfium2 PNG renders.** Drop them unless a person or agent actually reviews the images. The log checks (m15) catch the real build defects.
3. **JSON parsing in `debate.py`.** Ask referees for Markdown with `## Major` and `## Minor` headings, and split on the headings. `debate.py` reduces to `subprocess.run(..., timeout=)` plus a missing-CLI branch, about 20 lines.
4. **The inlined State enum** (m3). Delete the code instead.
5. **Four blind literature searchers.** Origin papers (a) and textbook treatment (d) overlap heavily. Use three searchers plus the completeness critic.
6. **Duplicate freeze checks** ("pinned sha unchanged" and "prereg check"). One guard test (M1) replaces both and also covers H2.

Keep the two-workflow design plus the skill. The approval checkpoint between scope and write is what justifies it, and workflow scripts cannot pause for input.

---

VERDICT: ACCEPT WITH CHANGES

Phase 1 (A1-A5) is safe for both frozen studies as written. Apply the MINOR line fixes (m1-m11) and the M1 guard test before running it. Resolve M3 with the owner before A3. Part B (§5) needs M2 and M4-M10 fixed before an implementation plan is written. As specified, it would produce papers that are neither reproducible nor fully bilingual, with citations checked only for metadata and no AI-assistance disclosure.
