# Referee round 2 (Claude): spec revision 2, commit `f0ab9d9`

Method: read-only. I used Read, Grep, `sed`, `sha256sum`, `git ls-files`, and the `--help` output of `agy`, `codex exec` and `tectonic`. I also ran one script of my own, outside the repo, that walks the import graph with stdlib `ast` (scratchpad `closure.py`). It imports nothing from the repo. I ran no repository Python.

## 1. My round-1 MAJOR issues

| # | Status | Reason (where checked) |
|---|---|---|
| M1 freeze guard | **PARTIALLY** | `frozen_guard` plus a closure manifest (spec L46-77, A0 L143-146) is the right mechanism. The closure as defined still has holes on the H2 readout path; see 3a below. |
| M2 TRADEGEN contamination | **PARTIALLY** | The isolation prerequisites in §3.2 (L86-97) are good. "Disables the look's write path" is the wrong lever; see 2b below. |
| M3 D3 trade calls | **RESOLVED** | A3 (L235-250) relabels `narrate_weekly_strategy` and the `_SYSTEM` persona, keeps the prefixes the tests assert, names `ficc_acceptance.py:744-763`, and flags the change for the owner. |
| M4 reproducibility | **RESOLVED** | 5.3 step 7 (L373-386): `run.py` refuses an uncommitted prereg, freezes inputs, writes immutable runs and a full MANIFEST, uses a paper-local ledger, and requires an offline rerun. `protocol.md` records data-access history (L349-363). See the dirty-tree note in 4. |
| M5 citations | **RESOLVED** | `verify_bib.py` records plus the `claims.yaml` gate (L333-346). `unread` blocks release, and private materials are used only to check derivations (L328-332). |
| M6 bilingual | **RESOLVED** | Per-language figures and tables, shared `common/*.tex`, per-section `\qnum` counts, the bare-digit check and the fidelity review (L387-397, L440-449, layout L470). |
| M7 fonts | **RESOLVED** | Fonts load by path. `C:/Windows/Fonts/HANBatang.ttf` and `HANBatangB.ttf` exist (static, with a real bold), as do `malgun.ttf` and `malgunbd.ttf`. Remaining note on portability in 4. |
| M8 `papers` suite | **RESOLVED** | Lazy imports, `NotRun`, and `--only-cached` (L480-492). `tectonic -X compile --help` lists `-C/--only-cached`, `--keep-logs` and `-b/--bundle`. |
| M9 referees | **RESOLVED** (my finding is outdated; agy is installed) | `agy --help` lists `-p`, `--sandbox`, `--output-format json`, `--model` and `--print-timeout`. The rubric, the 2-round cap, the exploratory labelling and `REVIEW_INCOMPLETE` all address the loop. One new runtime defect is in 4 (codex in a non-git bundle). |
| M10 AI disclosure | **RESOLVED** | AI-assistance statement (L403-404) and the owner's release sign-off (L313-314). |

## 2. The two rulings marked rejected or not adopted

**2a. M-8.3, "`.claude/workflows/*.js` is not natively executed": rejected. Acceptable, with one condition.**
- The Workflow reference I have describes saved workflows invoked by name, and scripts auto-persisted under the session directory. It does not confirm `.claude/workflows/` as the registry location. The Workflow tool is also opt-in per session.
- The ruling asserts a fact the spec does not demonstrate. However, §5.5 (L494-496) requires a synthetic end-to-end run before the first real topic, and that run would falsify the claim cheaply.
- Two additions:
  1. `SKILL.md` gets a fallback that runs the same stages through the Agent tool when Workflow dispatch is unavailable.
  2. Workflow scripts have no filesystem access, so "refuses if any scope file changed after approval" (L304-306) must be a deterministic exit code from a script, for example `tools/paper/approval.py verify`. It cannot be an agent's judgment.

**2b. Delete `grokteam/` from TRADEGEN: not adopted (D1). The substitute is the wrong lever.**
- The forward results are computed and written whether or not `FORWARD_LOOK.json` is written. On or after `FORWARD_END`, `forward_gate` returns `"look"`, and `main` replays the forward events and writes them to `summary.json` and `readout.txt`, and prints them (`grokteam/book.py:816-819, 833, 852-855`).
- With only the LOOK write removed (L840-843), `LOOK.exists()` never becomes true. Every TRADEGEN run after `FORWARD_END` is then another look, with no limit.
- Today the run happens to self-blind: any edit to TRADEGEN's `book.py` changes its sha, so `prereg.check(fz)` at L818 returns diffs and the run is VOID (L761-764). But the VOID message itself says "restore grokteam/out/frozen_book, then rerun", which undoes the protection.
- Worse: deleting `PREREG_book.json` and `frozen_book/` in TRADEGEN gives `fz = None` and no forward gate at all (L800-820), so the forward events are replayed unblinded.
- **Fix:** in TRADEGEN, disable the *read* path. Make `forward_gate` always return the records up to the freeze (blinded), or cut `settled_events` at `frozen_utc`. Never delete TRADEGEN's `PREREG_book.json`. With that change, keeping the duplicate (D1) is fine.

## 3. New or still-missed MAJOR issues

**3a. The guard's closure misses runtime inputs on the H2 readout path (§3.1, L56-67).**
- **The readout's own code is not a root.** The roots are the 10 pinned files plus `paper_live/engine.py` and `config.py`. The H2 readout also runs `paper_live/replay.py` (`REPLAY_HOLDOUT`, L125-147), `verdict.py` and `power.py`. My AST closure from the spec's roots has 57 files, and none of these three is among them. So an edit to `verdict.py` (for example `GATED, BASE` at L31, or the test at L139-141) changes H2 with the guard still green.
- **Data files are read at runtime and are not imports.**
  - `verdict.holdout_sessions()` (L68-80) and `engine.config_sha()` (L34-46) depend on `data/calendars/*.json`, loaded by `core/calendars/__init__.py:32, 99-121`.
  - A malformed file is skipped silently (L121, `except Exception: continue`). `is_trading_day` then returns `None`, which `holdout_sessions` counts as a trading day, so the holdout sample shifts.
  - The same applies to `core/calendars/data/*.yaml`, `data/macro/*` and `core/ficc/schemas/*`, which split_map §4.1 had listed.
- **A dynamic import escapes the AST walk.** `core/calendars/__init__.py:222-229` loads `clocks`, `publication`, `regime`, `store`, `events` and `adapter` through `importlib`.
- **Minimum fix.** Add as manifest roots `paper_live/{replay,verdict,power,sameday,calibrate}.py`, the six `core/calendars/*.py` submodules, and the trees `data/calendars/`, `core/calendars/data/`, `data/macro/` and `core/ficc/schemas/`.

**3b. The closure freezes about 57 files, including the data layer, until at least 2027-02-01, and the spec does not say so (§3.1 L75-77, §5.3 L371).**
- With lazy imports counted (the spec counts them: `history.py` is reachable only lazily), the protected set includes:
  - `core/ficc/data.py`, `core/ficc/fx.py` and `core/quant/history.py`;
  - `data/krx/{kis_client,gateway,krx_market_client,opendart_client}.py`, `data/kis_markets.py` and `data/fmp/quote_client.py`;
  - `core/engine/{books,orders,evaluator,state}.py`;
  - `core/quant/{optimize,risk,sleeves,strategies,risk_layer}.py`.
- Under the rule "defects … not fixed until both looks are taken", a Yahoo, KIS or FMP API change would leave QUANTGEN's pages broken for three months or more.
- **Cheaper and stronger design.** Everything both studies need is tracked at `eacd57d`: `grokteam/out/` (21 files) and `paper_live/out*` (140 files, including `frozen_rule/`, `HYPOTHESES_frozen.json`, `live/sigmas.json` and `verdict.json`), plus `data/calendars` (23 files).
  1. Tag `eacd57d` as `frozen-studies`.
  2. Run the H2 readout and the GROKTEAM look from `git worktree add <dir> frozen-studies`, using the same global interpreter with the pinned numpy, scipy and pandas.
  3. Copy `verdict.json` and `FORWARD_LOOK.json` back to main and commit them.
- The guard then shrinks to three checks:
  1. the tag still resolves to `eacd57d`;
  2. the library versions are unchanged;
  3. no `FORWARD_LOOK.json` exists on main before the worktree look (one-look integrity).
- The main tree can then evolve, and 3a disappears as well.
- If the owner keeps the in-tree freeze instead, the spec must at least list the protected files and state the git-worktree route as the remedy for any defect.

## 4. MINOR issues (new or residual)

- **Codex will refuse the bundle.** `codex exec` in the temp-folder bundle (L408-414) needs `--skip-git-repo-check`, which `codex exec --help` lists. Without it Codex refuses to run outside a git repo, and every round ends `REVIEW_INCOMPLETE`. Use `-C <bundle>` as well.
- **agy flags.** Use `--print-timeout` alongside the process-tree kill. Confirm that `-p` can read the bundle files without `--dangerously-skip-permissions`; `--mode plan` may be the read-only mode.
- **Dirty-tree anchors.**
  - `gate_ledger.repo_anchor()` reads only HEAD (`gate_ledger.py:122-131`). A ledger row registered from a dirty tree therefore claims a `git:` anchor for code that was never committed.
  - Rule: commit before any run that registers trials (the readouts, the Strategy Lab, `run.py`).
  - `run.py` should *refuse*, not just flag, a dirty tree for confirmatory runs (L380).
- **Font portability.** The PDFs depend on Windows system fonts; Malgun Gothic cannot be redistributed. Record each font file's sha256 in MANIFEST, or bundle OFL static fonts.
- **NotRun masking.** In the `--only-cached` selfcheck, map only "resource not in cache" errors to `NotRun`. A real Korean-font failure must still FAIL.
- **Guard expiry.** State when each guard clause retires: the H2 clause once valid `verdict.json` files exist for both profiles and Phase 2 is approved; the GROKTEAM clause once the record's `FORWARD_LOOK.json` exists.
- **Phase 1 arithmetic is now consistent.** Appendix B shows 725 PASS + 2 FAIL. A0 restores 727 PASS. A1-A5 give 811 = 690 PASS + 121 NOT_RUN, plus the guard and crypto-page tests (813 rows). Phase 1 touches no closure file except root `config.py`, which matches my closure output.
- **A2 synthetic draws.** Removing the `majors` draws in `ui/crypto_page.py:39` shifts the synthetic rng stream for `eth` and `volume` (L40-42). The newly registered self-check's assertions (kimchi `n`, GARCH `n`, weekday rows) do not depend on those values.

VERDICT: ACCEPT WITH CHANGES
