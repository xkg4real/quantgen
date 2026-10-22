Read-only audit completed; no Python, tests, studies, or model CLIs were run. All ten GROKTEAM source hashes currently match their pins, and the H2 engine/config files match both profiles’ frozen copies. The findings concern what this design would permit or fail to detect.

`spec` below means [the design specification](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md).

## MAJOR

**1. §3, §4.1 verification — The freeze checks do not establish unchanged frozen behavior.**

**Problem:** The dependency list is incomplete, frozen artifacts lack protection, and the prescribed prereg command does not fail on detected changes.

**Evidence:** `core/quant/vol_estimators.py:32` imports omitted `gjr.py`; `core/rules/macro_rules.py:27` imports omitted `validation.py`. [grokteam/prereg.py:148](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/grokteam/prereg.py:148) checks selected code and configuration, while lines 172–174 merely print differences without returning failure. `paper_live/engine.py:88–93` hashes engine bytes and effective rule parameters, not its complete dependencies. The prohibited-script list also misses `paper_live/calibrate.py:107–109`, which overwrites models/calibration subsequently loaded by `paper_live/replay.py:152–154`.

**Fix:** Add a separate, failing integrity checker covering the complete dependency closure and frozen records, restoration copies, models and input manifests for BOOK and both H2 profiles. Define the narrow root-config exception explicitly. Protect original study inputs/outputs from paper workflows by filesystem boundaries, with any ongoing collection separately authorized. Do not edit the pinned checker.

**2. §4.0 — TRADEGEN isolation cannot be deferred without an explicit launch prerequisite.**

**Problem:** A byte-identical copy still shares mutable state. Append-only ledgers can receive inappropriate additional trials; shared caches can be overwritten.

**Evidence:** `config.py:268–277` defaults to shared `.nextgen` directories; `grokteam/book.py:60` uses the shared BOOK cache. `main.py:247` starts the macro pipeline automatically. Trial writers use shared roots at `paper_live/engine.py:104–112` and `grokteam/book.py:737–740`; `core/quant/tf_gov.py:363–375` counts all family rows into global N. [grokteam/book.py:124](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/grokteam/book.py:124) uses a shared temporary filename and replacement without interprocess locking. `tests/macro_acceptance.py:113–121,198–207` can fail on concurrent home-state writes.

**Fix:** Require evidence that TRADEGEN’s environment, import paths, state directories and caches are isolated before launching it. Preserve complete ledger history in the copy. Run acceptance suites serially with application writers quiescent. Implementation can remain owned by the TRADEGEN session; the prerequisite belongs here.

**3. §4.2 — The stated Phase 2 readiness condition is already satisfied while both holdouts are pending.**

**Problem:** “Once `out*/verdict.json` exists” is not a completed-readout condition and conflicts with the section’s stronger requirement.

**Evidence:** `spec:179–180`; [paper_live/out/verdict.json:31](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/paper_live/out/verdict.json:31) reports H2 `pending`, zero of ten sessions. `paper_live/out_krx/verdict.json:38–41` does likewise. `paper_live/verdict.py:128–136` distinguishes pending, incomplete and invalid results; line 174 writes a verdict file for those states too.

**Fix:** Require completed, validated readouts for **both** profiles, with all planned sessions, matching frozen digests and archived evidence. A valid “not confirmed” result qualifies; pending/incomplete/invalid results do not. Define any abandonment separately before changing frozen rules.

**4. §4.1 A2 — The Crypto removal checklist leaves executable regime references behind.**

**Problem:** Following the enumerated removals can break page refresh while the registered suite remains green.

**Evidence:** The list at `spec:128–129` misses `ui/crypto_page.py:121` (`rs.components`), the entire [regime chart at line 190](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/ui/crypto_page.py:190), and assertions at lines 236 and 238. The chart lies outside the worker’s exception handler at lines 159–163. The page’s standalone self-check is not registered in the acceptance suite; `tests/flet_api_guard.py:53–95` checks Flet API usage, not undefined `rs`.

**Fix:** Remove the complete regime dependency chain: calculation, unpacking, local variables, narrative, payload, tile, chart and assertions. Add a synthetic refresh/render check that exercises the remaining page.

**5. §5.3(9) — The referee invocation can write into the repository it is reviewing.**

**Problem:** `agy --sandbox` is not a read-only boundary. A referee attempting reproduction or correction could alter frozen files or results.

**Evidence:** `spec:247–257` specifies direct CLI execution without an immutable review workspace. Google documents that the CLI sandbox permits workspace writes, and headless workspace file writes are automatically allowed. [Sandbox documentation](https://www.antigravity.google/docs/sandbox?tab=cli), [headless permissions](https://www.antigravity.google/docs/cli/headless/).

**Fix:** Give reviewers immutable, secret-free bundles containing the manuscript, source evidence, code snapshot and approved results. Capture reports through the parent process. Original frozen trees and live state must be inaccessible. Any reproduction must run in a disposable copy with explicit output roots.

**6. §5.3(9), §7 — The review loop explicitly allows unresolved correctness failures through.**

**Problem:** Three rounds do not turn a major error into an acceptable limitation. Missing reviewers can also disappear from the effective acceptance condition.

**Evidence:** `spec:252–254` moves remaining major disagreements into limitations; `spec:323` continues after CLI failure; `spec:271–275` then updates the portfolio. `spec:304` tests only that missing/timeout cases do not crash.

**Fix:** Introduce `DRAFT`, `REVIEW_INCOMPLETE`, `BLOCKED_MAJOR` and `RELEASED` states. Round limits stop work, not vetoes. Unresolved correctness/provenance issues block release. Require the specified panel or a recorded substitution, and evidence-backed resolution of stable issue IDs. Missing output must never mean “no major issues.”

**7. §5.2(5), §5.3(7) — The reproducibility and number-provenance contract is insufficient.**

**Problem:** Hashing unspecified outputs does not reconstruct a study. Generated macros can faithfully print the wrong sample, column, units, gross/net result or stale run. Figures and tables have no explicit lineage requirement.

**Evidence:** The entire contract at `spec:234–236` is `results.*`, a SHA manifest and `numbers.tex`; the layout at `spec:284–290` requires no raw-input snapshot or environment lock. Existing [docs/vol_backtest.py:166](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/docs/vol_backtest.py:166) already records input hashes, seed, mode and qualification; `docs/quant_lab_grading.py:88–90` records configuration and result qualification. Dependency declarations remain open-ended in `requirements.txt:7–14`.

**Fix:** Define a manifest schema binding immutable input vintages/content, code including imported dependencies, configuration, environment, seeds, calendar/time-zone conventions and execution command. Use immutable run IDs and refuse overwrites. Map every reported result, figure and table to its source field, selection, units and rounding. Require a clean offline rerun with declared numerical tolerances.

**8. §5.2(5) — “Use QUANTGEN’s gate” is not an adequate statistical protocol.**

**Problem:** The gate may not fit the topic. Freezing JSON before rerunning already-examined historical data does not create independent confirmation. The pipeline also lacks rules preventing smoke, blocked or insufficient-data results from becoming positive scientific claims.

**Evidence:** `spec:220–225`. `core/quant/validate.py:48–56` assumes 252-day annualization and a strategy gate requiring five OOS years; lines 492 onward implement a particular strategy evaluation. [grokteam/prereg.py:64](/C:/Users/whydi/OneDrive/Desktop/QUANTGEN/grokteam/prereg.py:64) explicitly declines that gate because its sample cannot qualify. `tests/run_all.py:97–100,118–122` permits a successful process exit with `NOT_RUN` results.

**Fix:** Require a topic-specific analysis protocol: estimand, observation unit, eligibility, data-access history, untouched holdout where claimed, leakage controls, dependence correction, power, multiplicity and all tried variants. Distinguish exploratory replication from confirmation. Propagate scientific status into abstracts, results, conclusions and the index; software-test success cannot clear scientific blockers.

**9. §5.2(3) — Citation verification checks bibliography metadata, not evidentiary support.**

**Problem:** A real DOI does not prove that a source supports the manuscript’s equation, numerical assertion, historical attribution or interpretation. Later revisions can introduce unchecked claims.

**Evidence:** `spec:212–216` checks authors, year, title, venue and pages only. It permits unconfirmed entries to be “marked,” whereas `spec:320` promises they are dropped.

**Fix:** Maintain a claim-to-source ledger with the exact source version, page/equation/table locator and supporting passage or derivation. Distinguish working papers from published revisions and lecture notes from original research. Mark inaccessible full text as unread, not verified. Block unsupported claims and recheck changed passages after revision and translation.

**10. §5.3(10) — The bilingual gate cannot establish scientific equivalence.**

**Problem:** Matching keys, labels and equation counts permits reversed inequalities, lost negation, altered assumptions and overstated significance. Korean is produced after the scientific review, with no semantic review of that edition.

**Evidence:** `spec:246–265` places translation after referee rounds and lists only structural checks. `spec:288–289` places figures only under `en/`, leaving translated figure text unspecified.

**Fix:** Share mathematical source where feasible and align corresponding passages by stable IDs. Require independent bilingual technical review of signs, units, qualifications and conclusions. Translate captions, table headings, axes and appendices. Add negative fixtures that change an inequality or negation while retaining every current structural invariant.

**11. §5.3(9), §5.5 — The external CLI protocol is underspecified for the promised JSON parser.**

**Problem:** The AGY invocation does not request JSON or a report schema. CLI success, usable structured output and a completed review are different conditions.

**Evidence:** `spec:247–257` promises JSON parsing; `spec:304` covers only missing binaries and timeout. AGY defaults to text; structured output requires explicit format/schema options. Tool denial can still leave exit status zero. [Official headless contract](https://www.antigravity.google/docs/cli/headless/). Read-only command discovery found no `agy` in this shell’s PATH.

**Fix:** Define versioned adapters with executable/model/authentication preflight, UTF-8 input/output, schema validation, explicit permission handling and Windows process-tree timeout cleanup. Preserve raw output and actual versions. Test valid success, malformed/truncated output, authentication failure and tool denial. Keep real-provider smoke tests separate from ordinary acceptance tests.

**12. §5.3(10–11), §5.5 — The Windows TeX build does not yet implement its claimed quality or reproducibility guarantees.**

**Problem:** Tectonic plus koTeX is plausible, but pinning the executable alone leaves package bundles and system fonts uncontrolled. The stated compile command does not itself enforce the promised warning failures.

**Evidence:** `spec:259–269,300` specifies font names and a two-page compile. Tectonic 0.17’s driver treats TeX warnings as nonfatal and can ignore BibTeX errors; logs require explicit retention. [Versioned driver source](https://github.com/tectonic-typesetting/tectonic/blob/tectonic%400.17.0/src/driver.rs), [compile options](https://tectonic-typesetting.github.io/book/latest/v2cli/compile.html). XeTeXko has distinct Hangul/Hanja font settings and package dependencies. [Package documentation](https://ctan.org/tex-archive/macros/xetex/generic/xetexko).

**Fix:** Pin the executable, TeX bundle and exact font files/versions, with a distributable fallback. Configure Hangul fonts explicitly. Retain and parse final `.log`/`.blg` files for unresolved citations/references, missing glyphs and overfull thresholds. Test Korean headings, bibliography, bold text, equations, tables, figures and long URLs, followed by an offline clean build. A successful two-page compile alone is insufficient.

## MINOR

**1. §4.1 verification — The test-count reduction is misstated.**

**Problem/evidence:** `spec:166–167` says 37 tests “plus the regime self-check.” `tests/expansion_acceptance.py:343` registers one whole analytics self-check; `core/crypto/analytics.py:423–450` includes several unrelated analyses alongside regime assertions.

**Fix:** Expect **37 fewer registered tests**, before adding new coverage. Remove only regime assertions and retain the analytics suite entry. Compare test identities as well as totals.

**2. §4.1 A1 — The configuration deletion shorthand is unsafe.**

**Problem/evidence:** `spec:102–104` describes `_DEFAULT_SKILLS_ROOT` through `skill_provider_status`, but these occupy separated regions: `config.py:50–123` and `244–260`. The intervening region includes retained provider helpers and `HTTP_TIMEOUT_SECONDS` at line 225.

**Fix:** Use the exact symbol list from `split_map.md:97–102`; explicitly preserve the intervening definitions. The preservation clause helps, but a deletion plan should not resemble one contiguous range.

**3. §4.1 A1 — Settings cleanup omits explicit import and residual-field removal.**

**Problem/evidence:** `ui/settings_page.py:18–19` imports the modules being deleted; lines 186–187 call skill interpreter/timeout helpers; lines 192 and 196 advertise `NEXTGEN_SKILLS_ROOT` and `FXMACRODATA_API_KEY`. `spec:99–100` does not enumerate these, unlike `split_map.md:112–116`.

**Fix:** Explicitly remove those imports, initialization, repository fields and obsolete example entries. Verify Settings import and rendering after deletion.

**4. §3.3 and §4.1 — Constraint and cross-reference details need correction.**

**Problem/evidence:** `test_s4` also forbids new wall-clock calls in the modules listed at `tests/macro_m5_integration.py:55–56`, enforced at lines 331–337. The spec omits this. Its critic references at `spec:112,116` are also wrong: suite renaming is split-map item **10**, dangling text item **9** (`split_map.md:525–532`).

**Fix:** Include the complete test constraint and correct the references.

**5. §4.1 A1 — Cloning the readiness enum retains dead cockpit code.**

**Problem/evidence:** `spec:101` proposes an inline `State`. Its maps/helpers at `ui/components.py:22–35,62–69` are used by the deleted Skills, Workflows and Runs pages.

**Fix:** Delete the unused readiness/run-status helpers and maps instead of reproducing their enum. Retain generic shared components.

**6. §5.1, §5.4–5.5 — Workflow execution, approval persistence and output paths need a concrete contract.**

**Problem/evidence:** `spec:190–196` names JavaScript workflows without identifying their executor or binding approval to an immutable proposal. `spec:191,234,284` alternates dated and undated paper directories. `spec:288–289` promises `paper_en.pdf`/`paper_ko.pdf` although the inputs are both `paper.tex`. `spec:306` postpones workflow validation until the first real paper.

**Fix:** Define one `paper_id`, an approved-scope hash, resume/invalidation behavior, the execution runtime and exact output naming. Prove dispatch through release using a synthetic fixture first. Keep compiler/provider integration tests isolated from fast, offline acceptance checks.

**7. §5.2–5.3 — Cut mandatory machinery that does not establish scientific quality.**

**Problem/evidence:** Four fixed searchers (`spec:203–210`), compulsory UI/Primer integration (`229–233`), design critique and a styled HTML portfolio (`270–275`) expand scope before one topic validates the process.

**Fix:** Start with one bounded paper, two templates, reproducible evidence, claim verification, the owner-selected referee panel and `INDEX.md`. Make search parallelism topic-dependent; defer portfolio styling and separately scope product integration. Also narrow “every number” to reported empirical/computational results rather than publication years and equation constants.

**8. §4.1 A5 — The proposed legal wording overstates its own input.**

**Problem/evidence:** `spec:158–159` calls the venue categorically illegal. BOOK concerns non-sports Kalshi BTC contracts (`grokteam/book.py:1–2`), while `reports/Korean resident trading venue legality.md:16` labels that category **“Grey, treat as illegal”**, with medium-low confidence. This is a source-fidelity discrepancy, not a new legal determination.

**Fix:** Preserve the research-only restriction while accurately attributing and dating the input report’s uncertainty; do not convert a conservative operating policy into an established legal fact.

VERDICT: REJECT

