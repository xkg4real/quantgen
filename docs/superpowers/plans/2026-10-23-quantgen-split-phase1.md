# QUANTGEN Split, Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tag the studies-of-record snapshot, then remove the non-quant parts (trading-skills cockpit, crypto regime score, trade-idea text) from QUANTGEN and relabel it as a research application, with the test suite green after every task.

**Architecture:** Frozen studies are protected by an annotated git tag plus a stdlib-only guard test, which frees the main line; each removal is one commit verified by the repo's own runner (tests/run_all.py).

**Tech Stack:** Python 3.13, Flet UI, git, the repo's acceptance runner (no pytest).

**Spec:** docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md (rev 4, approved 2026-10-23), sections 3 and 4.1; Appendices B and C.

**Plan order:** this plan (Plan A) runs completely first; its Task 1 tag must land before 2026-11-04 00:00 UTC. Plan B (docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md) then starts from this plan's A5 commit and quotes `tests/run_all.py` and `README.md` as this plan leaves them.

---

## Global Constraints

- Repo: C:/Users/whydi/OneDrive/Desktop/QUANTGEN (git, HEAD 238376a). Windows 11, Python 3.13 global interpreter (no venv). Always open text files with encoding="utf-8" (the locale default is cp949).
- No new pip dependencies. numpy 2.3.5, scipy 1.18.0, pandas 2.3.3 must not change (frozen studies). Available: numpy, scipy, pandas, matplotlib, reportlab, pypdf, pypdfium2, yaml (PyYAML), jinja2, requests.
- Never edit: anything under paper_live/ or grokteam/ (Part A Phase 2 is out of scope); core/engine/state.py, runtime.py, feed.py, __init__.py (byte-identical, test_s4). core/engine/orders.py, evaluator.py, ui/trading_page.py: insert-only (test_s4). core/ficc/macro_artifacts.py GIT_HASH and core/quant/lab.py GIT_HASH stay "UNVERSIONED".
- Never run: python -m paper_live.replay/grid/verdict/sameday/calibrate, python -m grokteam.book.
- Tests: no pytest. Each acceptance module exposes def tests() -> list[(name, fn)]; tests/run_all.py aggregates suites (cockpit->renamed safety in Part A, engine, ui, quant, ficc, expansion, macro, paper, grokteam). Run one suite: python tests/run_all.py --suite <name>. Full run ~11 minutes: python tests/run_all.py. A test raising tests.notrun.NotRun(reason) is NOT_RUN. Every suite run rewrites the tracked qa/acceptance_results.json: commit it with the change group.
- Baseline counts at 238376a: 725 PASS, 2 FAIL (macro/macro_m7_ledger test_ledger01 and test_sel01_b, caused by git init), 121 NOT_RUN, 848 total.
- Repo-wide guards bind all new code: T-CTX-01 (core/ficc/context_log.py acting-module import scan), T-RO-01 (tests/macro_m0_harness.py order-path scans), tests/flet_api_guard.py (ui AST checks), safety test_08/09 (tests/acceptance.py runtime_py scans).
- Git: .gitattributes is "* -text", autocrlf false; never renormalize line endings. Commit messages end with the line: Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Read the spec (C:/Users/whydi/OneDrive/Desktop/QUANTGEN/docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md) sections relevant to your task group, and the split map (C:/Users/whydi/OneDrive/Desktop/QUANTGEN/research_notes/QUANTGEN TRADEGEN split map/split_map.md) sections 3 and 8, before writing.
- Line endings at HEAD (keep each file's own; edit with the Edit tool, never with a formatter or a whole-file converter): CRLF are README.md, main.py, config.py, pyproject.toml, ui/settings_page.py, ui/components.py, ui/macro_page.py, tests/acceptance.py, tests/run_all.py, core/quant/insights.py, docs/build_expansion_primer.py, qa/acceptance_results.json; every other file this plan edits is LF. One check covers any set of edited, unstaged paths: `git ls-files --eol -- <paths> | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'` must print nothing.
- Count ledger (full suite after each task; every task ends at 0 FAIL and 121 NOT_RUN): Task 1 732/853, Task 2 695/816, Task 3 696/817, Task 4 697/818, Task 5 A4 commit 698/819, Task 5 A5 commit 699/820.
- Deadline: Task 1 (the tag) lands before 2026-11-04 00:00 UTC. The scheduled task h2-holdout-ready-alert fires then and tells the owner to read H2 out from a local git clone checked out at the tag `studies-of-record-2026-10-23`.
- Never run a whole-tree `git checkout -- .`, `git reset --hard`, `git stash` or `git clean` in the repo: `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache` reads the mtime of `docs/asset_expansion/cache/*.csv` as the data's retrieval instant, and rewriting those files makes it fail. Restore only the single file you edited (`git checkout -- <file>`).
- No QUANTGEN or TRADEGEN app runs during any full-suite run (T-HERM-02 snapshots `~/.nextgen`). Code blocks below are flush left on purpose: copy them as they are (a heredoc's closing `EOF` must start the line).
- Before Task 1, commit this plan file alone (`git add docs/superpowers/plans/2026-10-23-quantgen-split-phase1.md`, message "Plan: QUANTGEN split, Phase 1" plus the trailer). Every "`git status` prints nothing" expectation below assumes it is committed, and "the plan commit" below means that commit, directly on `238376a`.

## File Structure

| Path | Task | Responsibility after Phase 1 |
|---|---|---|
| `tests/frozen_guard.py` (create) | 1 | Suite `guard`: the tag, the tagged pins, no early GROKTEAM look, the library pins while a readout is pending. git + hashlib only. |
| tag `studies-of-record-2026-10-23` (git object) | 1 | Annotated tag on `eacd57d` carrying the Appendix C evidence; both readouts run from it. |
| `tests/run_all.py` | 1, 2 | Registers suite `guard` (Task 1); renames `cockpit` to `safety` (Task 2). |
| `tests/macro_m7_ledger.py` | 1 | T-LEDGER-01 and T-SEL-01 (b) follow the real repo state (Appendix B). |
| `qa/acceptance_results.json` | 1-5 | The full-suite result committed with each change group. |
| `core/skills/{index,entrypoints,params,readiness,runner,runs,diagnose,workflows,decisions,insights,wiring}.py` (delete) | 2 | Cockpit modules, moved to TRADEGEN. |
| `ui/{skills_page,workflows_page,runs_page,param_form,charts}.py` (delete) | 2 | Cockpit pages, moved to TRADEGEN. |
| `core/skills/__init__.py` | 2 | Docstring only; the package keeps `macro_daily`, `pipeline`, `alerts`, `macro_workflows/`. |
| `core/skills/pipeline.py`, `core/skills/macro_workflows/macro_daily.yaml` | 2 | Docstring and comment no longer name the deleted parser as present. |
| `main.py` | 2, 5 | 16-entry rail, simpler `navigate()` (Task 2); research identity in the docstring (Task 5). |
| `config.py` | 2 | No skill settings; FMP presence row in `quant_provider_status()`. |
| `.env.example` | 2 | No skill-provider block. |
| `ui/settings_page.py`, `ui/components.py`, `ui/krx_page.py` | 2 | Settings without the repository block; no readiness chips; KRX text without the skill library. |
| `tests/acceptance.py` | 2 | Suite `safety`: 10 tests and the shared `_read`, `_code_only`, `runtime_py`. |
| `tests/macro_m8_pipeline.py`, `tests/macro_ui_components.py`, `tests/macro_acceptance.py` | 2, 5 | Follow the deleted parser and Runs page (Task 2); `macro_ui_components` gains the A4 and A5 README tests (Task 5). |
| `docs/ARCHITECTURE_REVIEW.md` | 2 | Dated split note under the application map. |
| `README.md` | 2, 3, 4, 5 | Cockpit text (2), crypto paragraph (3), weekly note and AI layers (4), identity, split note, Research papers, GrokBot, test tables (5). |
| `core/crypto/analytics.py`, `ui/crypto_page.py` | 3 | No regime score; the page self-check is a registered test. |
| `tests/expansion_acceptance.py` | 3 | Registers `expansion/selfcheck_crypto_page`. |
| `docs/ASSET_EXPANSION_SPEC.md`, `docs/build_expansion_primer.py` | 3 | Dated "moved to TRADEGEN" notes; the built PDF is not rebuilt. |
| `core/ficc/insights.py` | 4 | Academic weekly note; research-commentary report prompts. |
| `core/quant/insights.py` | 4 | `_SYSTEM`: academic research analyst persona. |
| `tests/ficc_acceptance.py` | 4 | Weekly-note tests (57 ficc tests). |
| `ui/macro_page.py`, `core/ficc/macro.py` | 4 | The weekly report is labelled "Weekly rates and FX note" (kind key unchanged). |
| `pyproject.toml` | 5 | Research-application description. |

---

### Task 1: A0: studies-of-record tag, frozen_guard suite, git-state test fixes

**Files:**
- Create: `tests/frozen_guard.py`
- Modify: `tests/run_all.py`: L49-50 (imports), L64-65 (`tests()` tail), L111 (`--suite` help). CRLF.
- Modify: `tests/macro_m7_ledger.py`: L144 (T-LEDGER-01), L410-412 (T-SEL-01 (b)). LF.
- Modify (regenerated by the suite run): `qa/acceptance_results.json`
- Git object (not a file): annotated tag `studies-of-record-2026-10-23` on `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`
- Test: `python tests/run_all.py --suite guard`, the two `macro_m7_ledger` tests called directly, then `python tests/run_all.py`
- Deadline: commit before 2026-11-04 00:00 UTC (see Global Constraints).

**Interfaces:**
- Consumes:
  - the `git` CLI on PATH, called as `git -C <ROOT> cat-file -t <tag>`, `git rev-parse --verify <tag>^{commit}` and `git show <tag>:<path>`;
  - `tests.notrun.NotRun(reason: str)`;
  - at the tag, `grokteam/out/PREREG_book.json` keys `code: dict[path, sha256hex]` (10 entries) and `versions: {"numpy": "2.3.5", "scipy": "1.18.0", "pandas": "2.3.3", "python": "3.13.14"}`;
  - on main, `paper_live/out/verdict.json` and `paper_live/out_krx/verdict.json`, key `H2.status`. The final values are `"confirmed"` or `"not confirmed"`; today both are `"pending"`;
  - `importlib.metadata.version(name) -> str`;
  - from `core.quant.gate_ledger`: `repo_anchor(root: Path = REPO_ROOT) -> str`, `anchored(anchor) -> bool`, `REPO_ROOT: Path`, `UNVERSIONED = "UNVERSIONED"`, `Anchor(utc: str, anchor: str, what: str = "header_commit", config_ids: tuple = ())` and `UnanchoredTimestamp`.
- Produces:
  - In `tests/frozen_guard.py`:
    - constants `TAG = "studies-of-record-2026-10-23"`, `TAG_COMMIT = "eacd57d2b0821ad796ab9b66d2d2c96a3d71081f"` and `LOOK_OPENS = datetime(2027, 2, 1, 1, 0, tzinfo=timezone.utc)`;
    - `pending_readouts(root: Path = ROOT) -> list[str]`;
    - `tests() -> list[tuple[str, Callable[[], None]]]`, with **five** tests: `test_a_tag_is_annotated_and_peels_to_the_baseline`, `test_b_tagged_pins_match_prereg_and_frozen_rule`, `test_c_no_forward_look_before_it_opens`, `test_d_library_versions_match_the_pins_while_a_readout_is_pending` and `test_d_pending_readouts_retire_only_when_all_three_are_in`.
  - Suite `guard` in `tests/run_all.py` (`guard/<name>`), 5 rows.
  - Full run after this task: 732/853 passed, 0 failed, 121 not run.

- [ ] **Step 1: Baseline full suite run (the "before" run of spec 4.1)**

No app from QUANTGEN or TRADEGEN may run during this run (T-HERM-02). From the repo root:
```
python tests/run_all.py
```
This takes about 11 minutes. Expected last line: `725/848 passed, 2 failed, 121 not run; ...qa\acceptance_results.json`. The only FAIL rows should be:
- `macro/macro_m7_ledger/test_ledger01_refusals_and_null_distribution_runs`
- `macro/macro_m7_ledger/test_sel01_b_configuration_fixed_before_any_row_touched_its_span_gives_f_1_only_anchored`

Save the result outside the repo so test identities can be compared later:
```
python -c "import shutil, tempfile; shutil.copy('qa/acceptance_results.json', tempfile.gettempdir() + '/a0_before.json')"
```

- [ ] **Step 2: Write the guard (the failing test)**

`tests/frozen_guard.py` (whole file):
```python
"""Frozen-study guard (spec 2026-10-23 section 3.1 point 4; D9).

The GROKTEAM-BOOK and paper_live H2 readouts run only from a local git clone checked out at the annotated tag TAG on the baseline
commit, so the main line is free to change. This module imports nothing from paper_live or grokteam (importing
paper_live.engine silences warnings): it reads git through subprocess and hashes with hashlib. It fails when

  (a) TAG is missing, is not an annotated tag, or no longer peels to TAG_COMMIT;
  (b) in the tagged tree, a PREREG-pinned file's sha256 differs from PREREG, or paper_live/engine.py or config.py
      differs from either out*/frozen_rule copy;
  (c) before LOOK_OPENS, grokteam/out/book/FORWARD_LOOK.json exists on main (an early look);
  (d) the interpreter's numpy, scipy or pandas differ from the PREREG pins while a readout is still pending.

Expiry: (a) and (b) stay forever as provenance; (c) and (d) retire once both readouts are committed. NotRun when
git is not on PATH. Clause (d) has no warn-only branch yet: the spec names no place where a pinned venv is recorded.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from tests.notrun import NotRun

ROOT = Path(__file__).resolve().parents[1]
TAG = "studies-of-record-2026-10-23"
TAG_COMMIT = "eacd57d2b0821ad796ab9b66d2d2c96a3d71081f"
PREREG = "grokteam/out/PREREG_book.json"
H2_FILES = ("engine.py", "config.py")
H2_PROFILES = ("paper_live/out", "paper_live/out_krx")
LOOK = "grokteam/out/book/FORWARD_LOOK.json"
LOOK_OPENS = datetime(2027, 2, 1, 1, 0, tzinfo=timezone.utc)
H2_FINAL = ("confirmed", "not confirmed")
LIBS = ("numpy", "scipy", "pandas")


def _git(*args: str) -> bytes:
    if shutil.which("git") is None:
        raise NotRun("OWNER: git is not on PATH; frozen_guard reads the tagged snapshot through git")
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    if r.returncode:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def _tagged(path: str) -> bytes:
    return _git("show", f"{TAG}:{path}")


def pending_readouts(root: Path = ROOT) -> list[str]:
    """Readouts not yet committed on main: the GROKTEAM look, and each H2 profile without a final verdict."""
    out = [] if (root / LOOK).exists() else ["GROKTEAM-BOOK forward look"]
    for d in H2_PROFILES:
        v = root / d / "verdict.json"
        status = json.loads(v.read_text(encoding="utf-8")).get("H2", {}).get("status") if v.exists() else None
        if status not in H2_FINAL:
            out.append(f"H2 {d}")
    return out


def test_a_tag_is_annotated_and_peels_to_the_baseline():
    kind = _git("cat-file", "-t", TAG).decode().strip()
    peeled = _git("rev-parse", "--verify", f"{TAG}^{{commit}}").decode().strip()
    assert kind == "tag" and peeled == TAG_COMMIT, f"{TAG} is a {kind} on {peeled}; want an annotated tag on {TAG_COMMIT}"


def test_b_tagged_pins_match_prereg_and_frozen_rule():
    pins = json.loads(_tagged(PREREG))["code"]
    bad = [p for p, h in sorted(pins.items()) if hashlib.sha256(_tagged(p)).hexdigest() != h]
    bad += [f"{d}/frozen_rule/{f}" for d in H2_PROFILES for f in H2_FILES
            if _tagged(f"paper_live/{f}") != _tagged(f"{d}/frozen_rule/{f}")]
    assert len(pins) == 10 and not bad, f"{TAG}: {len(pins)} pins; differs from its freeze: {bad}"


def test_c_no_forward_look_before_it_opens():
    early = datetime.now(timezone.utc) < LOOK_OPENS and (ROOT / LOOK).exists()
    assert not early, f"{LOOK} exists before {LOOK_OPENS.isoformat()}: the one GROKTEAM look was taken early"


def test_d_library_versions_match_the_pins_while_a_readout_is_pending():
    pending = pending_readouts()
    if not pending:
        return                                                    # both readouts committed: clause (d) retired
    pins = json.loads(_tagged(PREREG))["versions"]
    drift = [f"{lib} {version(lib)} != {pins[lib]}" for lib in LIBS if version(lib) != pins[lib]]
    assert not drift, f"{drift} while pending: {pending}; read out from a venv pinned to {pins}"


def test_d_pending_readouts_retire_only_when_all_three_are_in():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert pending_readouts(root) == ["GROKTEAM-BOOK forward look", "H2 paper_live/out", "H2 paper_live/out_krx"]
        (root / LOOK).parent.mkdir(parents=True)
        (root / LOOK).write_text("{}", encoding="utf-8")
        for d, status in zip(H2_PROFILES, ("not confirmed", "pending")):
            (root / d).mkdir(parents=True)
            (root / d / "verdict.json").write_text(json.dumps({"H2": {"status": status}}), encoding="utf-8")
        assert pending_readouts(root) == ["H2 paper_live/out_krx"]
        (root / H2_PROFILES[1] / "verdict.json").write_text(json.dumps({"H2": {"status": "confirmed"}}), encoding="utf-8")
        assert pending_readouts(root) == []


def tests():
    return sorted((n, v) for n, v in globals().items() if n.startswith("test_") and callable(v))
```
Then confirm the guard imports neither frozen package:
```
grep -nE "^\s*(from|import)\s+(paper_live|grokteam)" tests/frozen_guard.py
```
Expected: no output (exit code 1).

- [ ] **Step 3: Register suite `guard` in `tests/run_all.py`**

`tests/run_all.py` Edit 1 (L49-50). Replace:
```python
from grokteam.selfcheck import tests as grokteam_tests             # noqa: E402
from tests.notrun import NotRun                             # noqa: E402
```
with:
```python
from grokteam.selfcheck import tests as grokteam_tests             # noqa: E402
from tests.frozen_guard import tests as guard_tests         # noqa: E402
from tests.notrun import NotRun                             # noqa: E402
```
`tests/run_all.py` Edit 2 (L64-65). Replace:
```python
            [(f"paper/{n}", f) for n, f in paper_tests()] +
            [(f"grokteam/{n}", f) for n, f in grokteam_tests()])
```
with:
```python
            [(f"paper/{n}", f) for n, f in paper_tests()] +
            [(f"grokteam/{n}", f) for n, f in grokteam_tests()] +
            [(f"guard/{n}", f) for n, f in guard_tests()])
```
`tests/run_all.py` Edit 3 (L111). Replace:
```python
    parser.add_argument("--suite", help="run one suite: cockpit, engine, ui, quant, ficc, expansion, macro, paper or grokteam")
```
with:
```python
    parser.add_argument("--suite", help="run one suite: cockpit, engine, ui, quant, ficc, expansion, macro, paper, grokteam or guard")
```

- [ ] **Step 4: Run the guard suite before the tag exists. Expected: FAIL**
```
python tests/run_all.py --suite guard
```
Expected:
- `FAIL guard/test_a_tag_is_annotated_and_peels_to_the_baseline AssertionError: git cat-file -t studies-of-record-2026-10-23: fatal: Not a valid object name studies-of-record-2026-10-23`
- `FAIL guard/test_b_tagged_pins_match_prereg_and_frozen_rule AssertionError: git show studies-of-record-2026-10-23:grokteam/out/PREREG_book.json: fatal: invalid object name ...`
- `PASS guard/test_c_no_forward_look_before_it_opens`
- `FAIL guard/test_d_library_versions_match_the_pins_while_a_readout_is_pending AssertionError: git show studies-of-record-2026-10-23:...`
- `PASS guard/test_d_pending_readouts_retire_only_when_all_three_are_in`
- last line: `2/5 passed, 3 failed, 0 not run`

This run rewrites `qa/acceptance_results.json` to 5 rows. Step 11 overwrites it again.

- [ ] **Step 5: Create the annotated tag carrying the Appendix C evidence (the implementation)**

Run this in Git Bash (the Bash tool), from the repo root. The repo-local `user.name`/`user.email` (Geon Koh) sign the tag. `-F -` reads the message from stdin.
```bash
git tag -a studies-of-record-2026-10-23 eacd57d2b0821ad796ab9b66d2d2c96a3d71081f -F - <<'EOF'
Studies of record: GROKTEAM-BOOK and paper_live H2 (spec 2026-10-23, section 3.1, D9)

Both pre-registered readouts run only from a local git clone checked out at this tag, with
numpy 2.3.5, scipy 1.18.0, pandas 2.3.3 and Python 3.13. The main line is
free to change; tests/frozen_guard.py (suite "guard") checks this tag.

Evidence that eacd57d is both frozen states (spec Appendix C, measured
2026-10-23 from the git-tracked tree):

GROKTEAM-BOOK: grokteam/out/PREREG_book.json, frozen_utc 2026-10-22T04:30:22Z.
The 10 pinned files match their PREREG sha256:
  7c203d7052e2de06b70edf482afab2a05206246515b7b119165ce979e7fb359e  core/quant/forecast_eval.py
  2a8a07377c0b82ec7f9fbd5874f4029d561d1396207e51f3a1acd81465ed4527  core/quant/garch.py
  018eaa960b2411dca13301c7353adcfb0bc160e494d9eb8e6e68f20d4c10be86  core/quant/gate_ledger.py
  3ae17e23e4cb07136d6603a4fe572041c26abbc44369698897603c051e15286a  core/quant/gate_stats.py
  68bc480f655d8297ae5326e08c3a19d36cdabf569452b93c97be5f634d239cf9  core/quant/validate.py
  f799c510e754292d1467004b87266e08b48afa00cc9d7138d7ee1c7c4396f04b  data/crypto/crypto_client.py
  549c1af65ee12e8617089b912e157d7b9e65ccbc1d359fbcf22c60943cbae025  data/net.py
  31c2a482c9800912e92cee271f72e1f3fbc32f1528064af178f67dcc8b718d7d  grokteam/__init__.py
  b92c8af0e3ffe8fb9d504af51f980d39872052dde306973fb17751a7c7af0b59  grokteam/book.py
  caf55f47585dbab6af0f4e42ca218395b654baf0433e4217b2f8ff86d726631a  grokteam/prereg.py

paper_live H2: out/HYPOTHESES_frozen.json frozen_utc 2026-10-20T01:11:07Z,
out_krx/HYPOTHESES_frozen.json frozen_utc 2026-10-20T01:11:09Z.
Both out*/frozen_rule copies equal the live files:
  642fc67b103998870b55c4c9f12c0c0f9189163ee482bdfe029ea2079f418199  paper_live/engine.py
  dc712a9d167e6fb59e162aaf33a0fb65d817fd572e18cb4df018bdaf4cd26ee2  paper_live/config.py

Tracked code and data changed after the H2 freeze (2026-10-20 01:11 UTC),
excluding outputs, backups and research text: 12 files, all off the readout
path: paper_live/analyze.py, report.py, narrative.json, compare_text.json and
compare_pdf.py (the section-3 report corrections); .claude/launch.json,
tests/paper_live_acceptance.py and tests/run_all.py; the new grokteam/*
package, finished before its own freeze. No file in core/, data/ or root
config.py changed, and neither did paper_live/engine.py, config.py,
replay.py, verdict.py or power.py.

After the GROKTEAM freeze (2026-10-22 04:30 UTC): no tracked code or data
file changed.
EOF
git cat-file -t studies-of-record-2026-10-23
git rev-parse --verify "studies-of-record-2026-10-23^{commit}"
git tag -n3 -l studies-of-record-2026-10-23
```
Expected:
- `tag`;
- `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`;
- the tag name followed by the first message lines.

No remote is configured, so nothing is pushed.

- [ ] **Step 6: Run the guard suite again. Expected: PASS**
```
python tests/run_all.py --suite guard
```
Expected: all five rows `PASS guard/...`, last line `5/5 passed, 0 failed, 0 not run`.

- [ ] **Step 7: Reproduce the two git-state failures. Expected: FAIL**
```
python -c "
from tests import macro_m7_ledger as M
for n in ('test_ledger01_refusals_and_null_distribution_runs',
          'test_sel01_b_configuration_fixed_before_any_row_touched_its_span_gives_f_1_only_anchored'):
    try: getattr(M, n)(); print('PASS', n)
    except Exception as e: print('FAIL', n, type(e).__name__, e)
"
```
Expected, in about 6 s:
- `FAIL test_ledger01_refusals_and_null_distribution_runs AssertionError `, because `repo_anchor()` is now `git:<sha>`;
- `FAIL test_sel01_b_configuration_fixed_before_any_row_touched_its_span_gives_f_1_only_anchored AssertionError UnanchoredTimestamp not raised`.

- [ ] **Step 8: Fix T-LEDGER-01 (`tests/macro_m7_ledger.py` L144, spec Appendix B row 1)**

`tempfile` and `Path` are already imported at L12-13. `repo_anchor()` reads `<root>/.git/HEAD` and then a loose ref file, so the comparison is against `.git/HEAD` being a file, not against `.git` existing: in a git worktree `.git` is a file and the anchor reads UNVERSIONED.

`tests/macro_m7_ledger.py` (L144). Replace:
```python
    assert GL.repo_anchor() == GL.UNVERSIONED            # this folder is not a git repository (rulings 3.1)
```
with:
```python
    with tempfile.TemporaryDirectory() as d:
        assert GL.repo_anchor(Path(d)) == GL.UNVERSIONED                    # a folder without .git
    # follows the repo (spec 3.3). repo_anchor() reads <root>/.git/HEAD and a loose ref: a worktree (.git is a file)
    # reads UNVERSIONED; packed refs would too, and fail here on purpose, since new ledger rows would be unanchored.
    assert GL.anchored(GL.repo_anchor()) == (GL.REPO_ROOT / ".git" / "HEAD").is_file()
```

- [ ] **Step 9: Fix T-SEL-01 (b) (`tests/macro_m7_ledger.py` L410-412, spec Appendix B row 2)**

`tests/macro_m7_ledger.py` (L410-412). Replace:
```python
    # unanchored: the commit (this folder is UNVERSIONED) or a row
    e = _raises(lambda: GL.step3(card, lg, SEED, **kw), GL.UnanchoredTimestamp, "owner must place the repository under git")
    assert GL.UNVERSIONED in str(e)
```
with:
```python
    # unanchored: the commit (an UNVERSIONED header commit; the repo itself is under git since D8) or a row
    unversioned = GL.Anchor(card["created_utc"], GL.UNVERSIONED, "header_commit")
    e = _raises(lambda: GL.step3(card, lg, SEED, commit=unversioned, **kw), GL.UnanchoredTimestamp,
                "owner must place the repository under git")
    assert GL.UNVERSIONED in str(e)
```
`core/quant/gate_ledger.py` is not touched.

- [ ] **Step 10: Re-run the two tests. Expected: PASS**

Run the Step 7 command again. Expected:
- `PASS test_ledger01_refusals_and_null_distribution_runs`
- `PASS test_sel01_b_configuration_fixed_before_any_row_touched_its_span_gives_f_1_only_anchored`

The raised message, for reference, is `header_commit at 2026-10-20T00:00:00Z is UNVERSIONED: owner must place the repository under git or name an external anchor (TASK-M7-05; rulings 3.1)`.

- [ ] **Step 11: Full suite (the "after" run) and identity comparison**

No app may run meanwhile.
```
python tests/run_all.py
```
Expected last line: `732/853 passed, 0 failed, 121 not run; ...`. That is 727 PASS, after the two fixes, plus 5 guard tests.

Then compare test identities with Step 1:
```
python -c "import json, tempfile, pathlib; L = lambda p: {r['test']: r['status'] for r in json.loads(pathlib.Path(p).read_text(encoding='utf-8'))}; b = L(tempfile.gettempdir() + '/a0_before.json'); a = L('qa/acceptance_results.json'); print('added', sorted(set(a) - set(b))); print('removed', sorted(set(b) - set(a))); print('changed', sorted((t, b[t], a[t]) for t in set(a) & set(b) if a[t] != b[t]))"
```
Expected:
- `added`: the five `guard/test_*` names;
- `removed []`;
- `changed`: exactly the two `macro/macro_m7_ledger/...` rows, `FAIL` -> `PASS`.

- [ ] **Step 12: Scope checks (no renormalisation, frozen trees untouched)**
```
git ls-files --eol -- tests/run_all.py tests/macro_m7_ledger.py qa/acceptance_results.json | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'
git diff --numstat
git diff --stat eacd57d -- paper_live grokteam core/engine
git status --short
```
Expected:
- the `awk` line prints nothing;
- `git diff --numstat` shows `4 2` for `tests/run_all.py` and `9 3` for `tests/macro_m7_ledger.py`, and a large count for `qa/acceptance_results.json`. A count near a source file's whole length (126 lines for `run_all.py`) means its line endings were rewritten: `git checkout -- <file>` and redo the edit with the Edit tool;
- `git diff --stat eacd57d -- paper_live grokteam core/engine` is empty;
- `git status --short` shows only those three modified files plus `?? tests/frozen_guard.py`.

- [ ] **Step 13: Commit (one commit for group A0)**
```bash
git add tests/frozen_guard.py tests/run_all.py tests/macro_m7_ledger.py qa/acceptance_results.json
git commit -F - <<'EOF'
A0: studies-of-record tag, frozen_guard suite, git-state test fixes

Annotated tag studies-of-record-2026-10-23 on eacd57d carries the
Appendix C evidence. tests/frozen_guard.py (suite "guard", 5 tests)
checks spec 3.1 point 4 clauses (a)-(d) with git and hashlib only, and
imports nothing from paper_live or grokteam. T-LEDGER-01 and T-SEL-01 (b)
in macro_m7_ledger follow the actual repo state (Appendix B);
gate_ledger.py is untouched.

Suite: 732/853 PASS, 0 FAIL, 121 NOT_RUN.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```
Expected: one new commit on `master` on top of the plan commit.

---

### Task 2: A1: cockpit out (spec 4.1 A1, owner decision D2)

Line endings differ by file (`.gitattributes` is `* -text`). CRLF: `main.py`, `config.py`, `ui/settings_page.py`, `ui/components.py`, `tests/acceptance.py`, `tests/run_all.py`, `README.md`. LF: `.env.example`, `core/skills/__init__.py`, `core/skills/pipeline.py`, `core/skills/macro_workflows/macro_daily.yaml`, `ui/krx_page.py`, `tests/macro_acceptance.py`, `tests/macro_m8_pipeline.py`, `tests/macro_ui_components.py`, `docs/ARCHITECTURE_REVIEW.md`. Use the Edit tool for every partial edit (it keeps each file's EOL). The two whole-file rewrites are `tests/acceptance.py` (converted to CRLF in Step 9) and `core/skills/__init__.py` (stays LF). Step 11 compares every edited file's EOL with HEAD. Line numbers are at `238376a`; Task 1 edited `tests/run_all.py`, so every `run_all.py` edit below matches on text, not on line numbers. Run every command from the repo root in Git Bash: `cd /c/Users/whydi/OneDrive/Desktop/QUANTGEN`.

**Files:**
- Delete (`git rm`), 16 files:
  - `core/skills/{index,entrypoints,params,readiness,runner,runs,diagnose,workflows,decisions,insights,wiring}.py`
  - `ui/{skills_page,workflows_page,runs_page,param_form,charts}.py`
- Modify:
  - `core/skills/__init__.py`: the whole file, L1-29, becomes a docstring only.
  - `core/skills/pipeline.py`: module docstring L12-13 and `load_pipeline` docstring L73-74 (docstrings only).
  - `core/skills/macro_workflows/macro_daily.yaml`: comment L2 (a YAML comment; `safe_load` ignores it).
  - `main.py`:
    - L3-6 (docstring);
    - L46, L67 and L69-70 (imports);
    - L89-90 and L92 (NAV);
    - L124 (`build` signature);
    - L148-153 and L157-159 (`build` branches);
    - L161-177 (`navigate`, `reload_catalogue`).
  - `config.py`:
    - L1-20 (docstring);
    - L47-125 (skills repository and skill-provider credentials, deleted);
    - L244-261 (`skill_provider_status`, deleted);
    - L267 (comment);
    - L328-333 (`quant_provider_status` gains the FMP row).
  - `ui/settings_page.py`:
    - L1-5 (docstring);
    - L13-22 (imports);
    - L28-30 (`_SIGNUP`);
    - L52-57 (signature and skills-root block);
    - L177-196 (`repo_block` and the `.env` snippet);
    - L209-212 (skills-root notice);
    - L245-248 (skill-provider list);
    - L273-277 (Repository block and reload button).
  - `ui/components.py`:
    - L1-7 (docstring);
    - L18 (readiness import);
    - L21-36 (`STATE_STYLE`, `RUN_STATUS_STYLE`);
    - L62-69 (`readiness_chip`, `run_status_chip`).
  - `.env.example`: L3 (header) and L12-17 (skill-provider block).
  - `tests/acceptance.py`: the whole file, L1-958, is rewritten.
    - Kept verbatim: L18-19, L21-55, L166-183, L225-271, L318-331 and L956-958.
    - Replaced: L1-17 (docstring), L217-223 (test_13) and L273-275 (section header).
    - Deleted: L20 (`import os`), L57-164, L185-215, L276-316 and L333-955.
  - `tests/run_all.py`: L41, L57 and L111 (text after Task 1).
  - `tests/macro_m8_pipeline.py`: L132-133.
  - `tests/macro_ui_components.py`: L120-127.
  - `ui/krx_page.py`: L1-6 and L189-190.
  - `tests/macro_acceptance.py`: L8 and L116-117.
  - `docs/ARCHITECTURE_REVIEW.md`: a dated note goes after the diagram's closing fence (L97). It covers the rail at L60.
  - `README.md`: L4-5, L354, L738-747 and L829-830. **Not** L6-8 (Task 5 rewords the "recommends" sentence with the A4 identity) and **not** L763-786 (Task 5 updates the test table once, at the end of Phase 1).
  - `qa/acceptance_results.json`: rewritten by the full run.
- Test:
  - `tests/acceptance.py` (suite `safety`);
  - `tests/macro_m8_pipeline.py::test_yaml_loads_with_the_strict_runner_and_the_legacy_parser_is_untouched`;
  - `tests/macro_ui_components.py`;
  - `tests/flet_api_guard.py` (suite `ui`);
  - the full `python tests/run_all.py`.

**Interfaces:**
- Consumes:
  - `config.fmp_ready() -> bool` (config.py L136-137, unchanged);
  - Task 1's committed `qa/acceptance_results.json`, a full run (853 rows: 732 PASS, 0 FAIL, 121 NOT_RUN), as the "before" run.
- Produces:
  - `config.quant_provider_status() -> list[dict]`. Its first row is now `{"id": "fmp", "label": "Financial Modeling Prep", "ready": fmp_ready(), "vars": ("FMP_API_KEY",), "note": "dividend-adjusted US end-of-day prices"}`, followed by the existing `anthropic` and `gs` rows.
  - `ui.settings_page.build_settings_page(page: ft.Page) -> ft.Control`. The `on_reload` keyword is gone.
  - `main.NAV`: 16 entries.
  - Inside `main.main()`:
    - `build(name: str) -> ft.Control`;
    - `navigate(name: str, *, rebuild: bool = False) -> None`.
  - `tests.acceptance`:
    - `_read(path: Path) -> str`, `_code_only(path: Path) -> str` and `runtime_py() -> list[Path]`, all unchanged;
    - `tests() -> list[tuple[str, Callable]]` with exactly 10 entries.
  - `tests/run_all.py` registers that module as suite `safety` (it was `cockpit`), so `--suite safety` works.
  - Full run after this task: 695/816 passed, 0 failed, 121 not run.
- Removed names:
  - from `config`: `_DEFAULT_SKILLS_ROOT`, `skills_root`, `skills_root_valid`, `skill_python`, `SKILL_TIMEOUT_SECONDS`, `runs_dir`, `SKILL_CREDENTIALS`, `KEYLESS_INTEGRATIONS`, `FILE_INPUT_INTEGRATIONS`, `skill_credential_present`, `skill_env`, `skill_provider_status`;
  - from `ui.components`: `STATE_STYLE`, `RUN_STATUS_STYLE`, `readiness_chip`, `run_status_chip`;
  - from `core.skills`: every re-export and `reload_all`.
- Kept for later tasks: `core.skills.macro_daily`, `core.skills.pipeline`, `core.skills.alerts` and `core/skills/macro_workflows/`, behaviour unchanged.

- [ ] **Step 1: Record the baseline (clean tree, registered-test count)**

```bash
git status --short
python -B -c "from tests.run_all import tests; import collections; t=tests(); print(len(t), dict(collections.Counter(n.split('/')[0] for n,_ in t)))"
```
Expected:
- `git status` prints nothing.
- The second command prints `853 {'cockpit': 47, 'engine': 92, 'ui': 4, 'quant': 53, 'ficc': 56, 'expansion': 19, 'macro': 539, 'paper': 21, 'grokteam': 17, 'guard': 5}`.

- [ ] **Step 2: Write the failing tests**

(a) `tests/acceptance.py` test_13 (L217-223). Replace:
```python
def test_13_settings_page_shows_presence_not_values():
    """No credential value may reach a widget."""
    source = _read(ROOT / "ui" / "settings_page.py")
    assert "kis_credentials()" not in source
    assert "opendart_key()" not in source
    assert "_clean(" not in source
```
with:
```python
def test_13_settings_page_shows_presence_not_values():
    """No credential value may reach a widget. FMP, shown before the split only
    among the cockpit's skill providers, is a presence row in the quant list."""
    import config
    source = _read(ROOT / "ui" / "settings_page.py")
    assert "kis_credentials()" not in source
    assert "opendart_key()" not in source
    assert "_clean(" not in source
    assert "fmp_key()" not in source and "core.skills" not in source
    fmp = [p for p in config.quant_provider_status() if p["id"] == "fmp"]
    assert len(fmp) == 1 and fmp[0]["vars"] == ("FMP_API_KEY",), fmp
    assert fmp[0]["ready"] == config.fmp_ready()
```

(b) `tests/macro_m8_pipeline.py` (L132-133). Replace:
```python
    import core.skills.workflows as W
    assert W.__file__.endswith("workflows.py") and callable(W.all_workflows) and hasattr(W, "Step")
```
with:
```python
    import importlib.util
    assert importlib.util.find_spec("core.skills.workflows") is None    # the legacy parser left with the cockpit (TRADEGEN, 2026-10-23)
```
The function name stays `test_yaml_loads_with_the_strict_runner_and_the_legacy_parser_is_untouched`, because `tests/macro_registry.csv` row T-RO-01 lists it in `implemented_in`. A stale `core/skills/__pycache__/workflows.cpython-313.pyc` does not make `find_spec` succeed: Python ignores a `__pycache__` file whose source is gone.

- [ ] **Step 3: Run the two tests and watch them fail**

```bash
python -B -c "from tests.acceptance import test_13_settings_page_shows_presence_not_values as t; t()"
python -B -c "from tests.macro_m8_pipeline import test_yaml_loads_with_the_strict_runner_and_the_legacy_parser_is_untouched as t; t()"
```
Expected:
- Both raise `AssertionError`.
- The first fails at `assert "fmp_key()" not in source and "core.skills" not in source`, because `settings_page.py` L18-19 still import `core.skills`.
- The second fails at the `find_spec` line, because `core/skills/workflows.py` still exists.

- [ ] **Step 4: Delete the cockpit modules and empty the package `__init__`**

```bash
git rm core/skills/index.py core/skills/entrypoints.py core/skills/params.py core/skills/readiness.py core/skills/runner.py core/skills/runs.py core/skills/diagnose.py core/skills/workflows.py core/skills/decisions.py core/skills/insights.py core/skills/wiring.py ui/skills_page.py ui/workflows_page.py ui/runs_page.py ui/param_form.py ui/charts.py
```
Expected: 16 `rm '…'` lines.

`core/skills/__init__.py` (whole file, L1-29; LF, keep LF). Replace:
```python
"""Skill catalog, readiness, execution and history for the NEXTGEN cockpit."""
# `entrypoints` is exported under an alias: binding the function to that name
# here would shadow the submodule of the same name for every later importer.
from core.skills.entrypoints import Entrypoint, is_runnable, primary
from core.skills.entrypoints import entrypoints as skill_entrypoints
from core.skills.index import Integration, SkillMeta, all_skills, by_id, categories
from core.skills.readiness import Readiness, State, evaluate, summarize
from core.skills.runner import RunHandle, RunResult, Status, describe_args, run_skill
from core.skills.runs import RunRecord, latest_for_skill, recent, record
from core.skills.workflows import Step, WorkflowMeta, all_workflows

__all__ = [
    "Entrypoint", "skill_entrypoints", "is_runnable", "primary",
    "Integration", "SkillMeta", "all_skills", "by_id", "categories",
    "Readiness", "State", "evaluate", "summarize",
    "RunHandle", "RunResult", "Status", "describe_args", "run_skill",
    "RunRecord", "latest_for_skill", "recent", "record",
    "Step", "WorkflowMeta", "all_workflows",
]


def reload_all() -> None:
    """Re-read the repository after the operator changes its location."""
    from core.skills import (entrypoints as _ep, index as _idx,
                             readiness as _rd, workflows as _wf)
    _idx.reload()
    _wf.reload()
    _ep.reload()
    _rd.reload()
```
with:
```python
"""The macro pipeline: `macro_daily` (steps, gates, app-start hook), `pipeline` (the strict YAML runner),
`alerts`, and the `macro_workflows/` YAML.

Docstring only, so these modules import without the NEXTGEN skill cockpit (catalogue, readiness, argument
reader, runner, run history, workflows, gate decisions), which moved to TRADEGEN on 2026-10-23.
"""
```

- [ ] **Step 5: `config.py`: drop the skill settings and move the FMP row into `quant_provider_status()`**

`config.py` Edit 1 (L1-20, docstring). Replace:
```python
"""Local configuration for the NEXTGEN skill cockpit.

Two independent credential families, deliberately kept apart:

  * SKILL providers (FINVIZ / Alpaca / FXMacroData) — consumed by the scripts
    inside the trading-skills repository. NEXTGEN never reads the values itself;
    it only reports presence and forwards them to a subprocess env.

  * FMP is BOTH. The skill library forwards it to subprocesses, and the trading
    system reads it directly to quote non-Korean venues. One key, two consumers
    — worth stating, because the rest of this module keeps the two credential
    families apart and FMP is the deliberate exception.

  * KRX providers (KIS / OpenDART / KRX marketplace) — consumed by NEXTGEN's own
    read-only Korean market data layer, because the skill library has no KRX
    coverage at all.

A blank value keeps that provider unavailable. Nothing is ever logged, echoed
into a run transcript, or written to a run artifact.
"""
```
with:
```python
"""Local configuration for QUANTGEN.

Every credential is read from `.env` or the process environment, and only its
presence is ever reported:

  * FMP — read-only US end-of-day prices and quotes for every venue outside
    Korea.

  * KRX providers (KIS / OpenDART / KRX marketplace) — QUANTGEN's own
    read-only Korean market data layer.

  * Quant analysis (Claude API, GS Marquee), crypto (keyless public data and an
    optional read-only Upbit key) and FICC (keyless FRED / Yahoo).

A blank value keeps that provider unavailable. Nothing is ever logged or
written to an artifact. The NEXTGEN skill-cockpit settings (skills root, skill
interpreter, run timeout, runs directory, skill-provider keys) moved to
TRADEGEN on 2026-10-23.
"""
```

`config.py` Edit 2 (delete L47-125). Replace:
```python
# --------------------------------------------------------------------------- #
# Trading-skills repository
# --------------------------------------------------------------------------- #
_DEFAULT_SKILLS_ROOT = (
    Path.home() / "Downloads" / "claude-trading-skills-main" / "claude-trading-skills-main"
)


def skills_root() -> Path:
    """Filesystem root of the trading-skills repository."""
    override = _clean("NEXTGEN_SKILLS_ROOT")
    return Path(override) if override else _DEFAULT_SKILLS_ROOT


def skills_root_valid(root: Path | None = None) -> bool:
    root = root or skills_root()
    return (root / "skills-index.yaml").is_file() and (root / "skills").is_dir()


# Interpreter used to run skill scripts. Defaults to the one running NEXTGEN.
def skill_python() -> str:
    import sys
    return _clean("NEXTGEN_SKILL_PYTHON") or sys.executable


SKILL_TIMEOUT_SECONDS = float(_clean("NEXTGEN_SKILL_TIMEOUT") or "300")

# Where run transcripts and artifacts are written.
def runs_dir() -> Path:
    override = _clean("NEXTGEN_RUNS_DIR")
    return Path(override) if override else (Path.home() / ".nextgen" / "runs")


# --------------------------------------------------------------------------- #
# Skill-provider credentials (forwarded to subprocesses, never read for value)
# --------------------------------------------------------------------------- #
# Maps a skills-index integration id -> the env var(s) that satisfy it.
SKILL_CREDENTIALS: dict[str, tuple[str, ...]] = {
    "fmp": ("FMP_API_KEY",),
    "finviz": ("FINVIZ_API_KEY",),
    "alpaca": ("ALPACA_API_KEY", "ALPACA_SECRET_KEY"),
    "fxmacrodata": ("FXMACRODATA_API_KEY",),
}

# Integration ids that need no credential at all.
KEYLESS_INTEGRATIONS = frozenset({
    "local_calculation", "public_csv", "coingecko", "binance_funding",
    "yfinance", "websearch",
})

# Integration ids satisfied by a file the operator supplies at run time.
FILE_INPUT_INTEGRATIONS = frozenset({
    "prices_json", "user_input", "chart_image", "mt5_local_files",
    "news_events_json", "catalyst_events_json", "profiles_json",
})


def skill_credential_present(integration_id: str) -> bool:
    names = SKILL_CREDENTIALS.get(integration_id)
    if not names:
        return False
    return all(_present(n) for n in names)


def skill_env() -> dict[str, str]:
    """Environment handed to a skill subprocess: inherited os.environ plus any
    configured provider keys. Values are copied straight through and are never
    inspected, logged, or persisted by NEXTGEN."""
    env = dict(os.environ)
    for names in SKILL_CREDENTIALS.values():
        for name in names:
            value = _clean(name)
            if value:
                env[name] = value
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return env


# --------------------------------------------------------------------------- #
# FMP — NEXTGEN's own read-only quotes for every venue outside Korea
```
with:
```python
# --------------------------------------------------------------------------- #
# FMP — NEXTGEN's own read-only quotes for every venue outside Korea
```

`config.py` Edit 3 (delete `skill_provider_status`, L244-261, and reword the comment at L267). Replace:
```python
                 "returns HTTP 403, so the free Open API key is required."},
    ]


def skill_provider_status() -> list[dict]:
    return [
        {"id": "fmp", "label": "Financial Modeling Prep",
         "ready": skill_credential_present("fmp"), "vars": ("FMP_API_KEY",),
         "note": "Required by 28 skills."},
        {"id": "finviz", "label": "FinViz Elite",
         "ready": skill_credential_present("finviz"), "vars": ("FINVIZ_API_KEY",),
         "note": "Required by 4 screener skills."},
        {"id": "alpaca", "label": "Alpaca",
         "ready": skill_credential_present("alpaca"),
         "vars": ("ALPACA_API_KEY", "ALPACA_SECRET_KEY"),
         "note": "Portfolio and broker-side planning skills."},
        {"id": "fxmacrodata", "label": "FXMacroData",
         "ready": skill_credential_present("fxmacrodata"),
         "vars": ("FXMACRODATA_API_KEY",),
         "note": "Macro release calendar."},
    ]


# --------------------------------------------------------------------------- #
# Trading system storage
# --------------------------------------------------------------------------- #
# Rules the operator authored, the simulated order book, and the engine's halt
# state. Kept beside the run transcripts, on this machine only.
```
with:
```python
                 "returns HTTP 403, so the free Open API key is required."},
    ]


# --------------------------------------------------------------------------- #
# Trading system storage
# --------------------------------------------------------------------------- #
# Rules the operator authored, the simulated order book, and the engine's halt
# state. Kept under ~/.nextgen, on this machine only.
```

`config.py` Edit 4 (`quant_provider_status`, L329-331). Replace:
```python
    """Presence-only report for the Settings page. No values are returned."""
    return [
        {"id": "anthropic", "label": "Claude API (deep analysis)",
```
with:
```python
    """Presence-only report for the Settings page. No values are returned."""
    return [
        {"id": "fmp", "label": "Financial Modeling Prep",
         "ready": fmp_ready(), "vars": ("FMP_API_KEY",),
         "note": "dividend-adjusted US end-of-day prices"},
        {"id": "anthropic", "label": "Claude API (deep analysis)",
```
The note text is the spec's own wording. `core/quant/history.py` L131 reads `/historical-price-eod/dividend-adjusted`. `os` stays imported in `config.py` (other helpers use it).

- [ ] **Step 6: `ui/components.py` and `ui/settings_page.py`: remove the cockpit pieces**

`ui/components.py` Edit 1 (L1-7). Replace:
```python
"""Shared presentation atoms for the cockpit.

Kept in one place because the three pages must agree on what "ready" looks like.
A skill that is blocked on a key and a workflow that is blocked on a key should
be the same colour, the same word, and the same shape, or the operator has to
re-learn the interface on every tab.
"""
```
with:
```python
"""Shared presentation atoms for every QUANTGEN page.

Kept in one place because the pages must agree on what a status looks like: the
same state should be the same colour, the same word, and the same shape on every
tab, or the operator has to re-learn the interface on each one.
"""
```

`ui/components.py` Edit 2 (L16-39). Replace:
```python
import flet as ft

from core.skills.readiness import State
from core.theme import RADII, active

# One vocabulary for readiness, used by every surface.
STATE_STYLE: dict[State, tuple[str, str]] = {
    State.READY:       ("Ready", "success"),
    State.NEEDS_INPUT: ("Needs input", "accent"),
    State.MISSING_KEY: ("Key required", "error"),
    State.DOC_ONLY:    ("Reference only", "muted"),
}

RUN_STATUS_STYLE: dict[str, tuple[str, str]] = {
    "ok":        ("Succeeded", "success"),
    "failed":    ("Failed", "error"),
    "timeout":   ("Timed out", "error"),
    "cancelled": ("Cancelled", "muted"),
    "error":     ("Could not start", "error"),
    "running":   ("Running", "accent"),
}


def _colour(token: str) -> str:
```
with:
```python
import flet as ft

from core.theme import RADII, active


def _colour(token: str) -> str:
```

`ui/components.py` Edit 3 (L62-72). Replace:
```python
def readiness_chip(state: State, *, tooltip: str = "") -> ft.Container:
    label, token = STATE_STYLE[state]
    return chip(label, token, tooltip=tooltip)


def run_status_chip(status: str) -> ft.Container:
    label, token = RUN_STATUS_STYLE.get(status, (status or "unknown", "muted"))
    return chip(label, token)


def section(title: str, *, subtitle: str = "") -> ft.Column:
```
with:
```python
def section(title: str, *, subtitle: str = "") -> ft.Column:
```

`ui/settings_page.py` Edit 1 (L1-5). Replace:
```python
"""Settings: credential presence, repository location, and a real KRX probe.

Presence only — no value is ever read into a widget, and there is no field to
type a key into. Credentials come from `.env` or the process environment, which
keeps them out of NEXTGEN's own state and out of any screenshot.
```
with:
```python
"""Settings: credential presence and live probes of the KRX, FICC, KIS and crypto providers.

Presence only — no value is ever read into a widget, and there is no field to
type a key into. Credentials come from `.env` or the process environment, which
keeps them out of QUANTGEN's own state and out of any screenshot.
```

`ui/settings_page.py` Edit 2 (L11-22). Replace:
```python
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

import config
from core.skills.index import all_skills
from core.skills.readiness import State, summarize
from core.theme import RADII, active
from data.krx.krx_market_client import KRXMarketClient
from ui.components import chip, key_value, notice, section
```
with:
```python
from __future__ import annotations

import flet as ft

import config
from core.theme import RADII, active
from data.krx.krx_market_client import KRXMarketClient
from ui.components import chip, notice, section
```

`ui/settings_page.py` Edit 3 (`_SIGNUP`, L27-31). Replace:
```python
    "fmp": "financialmodelingprep.com",
    "finviz": "elite.finviz.com",
    "alpaca": "alpaca.markets",
    "fxmacrodata": "fxmacrodata.com",
    "kis": "apiportal.koreainvestment.com",
```
with:
```python
    "fmp": "financialmodelingprep.com",
    "kis": "apiportal.koreainvestment.com",
```

`ui/settings_page.py` Edit 4 (L52-59). Replace:
```python
def build_settings_page(page: ft.Page, *, on_reload: Optional[Callable] = None) -> ft.Control:
    pal = active()
    root = config.skills_root()
    valid = config.skills_root_valid(root)
    skills = all_skills()
    counts = summarize(skills) if skills else {}

    probe_host = ft.Row(spacing=8)
```
with:
```python
def build_settings_page(page: ft.Page) -> ft.Control:
    pal = active()

    probe_host = ft.Row(spacing=8)
```

`ui/settings_page.py` Edit 5 (L177-196). Replace:
```python
    repo_block = ft.Column([
        key_value("Repository", str(root)),
        key_value("Index", "skills-index.yaml found" if valid else "NOT FOUND"),
        key_value("Skills", str(len(skills))),
        key_value("Runnable now", str(counts.get(State.READY, 0))),
        key_value("Needs input", str(counts.get(State.NEEDS_INPUT, 0))),
        key_value("Key required", str(counts.get(State.MISSING_KEY, 0))),
        key_value("Reference only", str(counts.get(State.DOC_ONLY, 0))),
        key_value("Runs directory", str(config.runs_dir())),
        key_value("Interpreter", config.skill_python()),
        key_value("Run timeout", f"{config.SKILL_TIMEOUT_SECONDS:.0f}s"),
    ], spacing=6)

    env_help = (
        "# .env — NEXTGEN reads these from this machine only.\n"
        "NEXTGEN_SKILLS_ROOT=\n"
        "FMP_API_KEY=\n"
        "FINVIZ_API_KEY=\n"
        "ALPACA_API_KEY=\nALPACA_SECRET_KEY=\n"
        "FXMACRODATA_API_KEY=\n"
```
with:
```python
    env_help = (
        "# .env — QUANTGEN reads these from this machine only.\n"
        "FMP_API_KEY=\n"
```

`ui/settings_page.py` Edit 6 (L206-212). Replace:
```python
    controls: list[ft.Control] = [
        section("Settings", subtitle="Credential presence only. No key is ever displayed here."),
    ]
    if not valid:
        controls.append(notice(
            f"No skills-index.yaml under {root}. Set NEXTGEN_SKILLS_ROOT in .env "
            "and restart.", "error", icon=ft.Icons.FOLDER_OFF_OUTLINED))
```
with:
```python
    controls: list[ft.Control] = [
        section("Settings", subtitle="Credential presence only. No key is ever displayed here."),
    ]
```

`ui/settings_page.py` Edit 7 (L245-250). Replace:
```python
        ft.Text("Skill providers", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        ft.ResponsiveRow([ft.Container(provider_row(p), col={"xs": 12, "md": 6})
                          for p in config.skill_provider_status()],
                         spacing=10, run_spacing=10),

        ft.Text("Korean market providers", size=15, weight=ft.FontWeight.W_600, color=pal.text),
```
with:
```python
        ft.Text("Korean market providers", size=15, weight=ft.FontWeight.W_600, color=pal.text),
```

`ui/settings_page.py` Edit 8 (L273-280). Replace:
```python
        ft.Divider(color=pal.border),
        ft.Text("Repository", size=15, weight=ft.FontWeight.W_600, color=pal.text),
        repo_block,
        ft.Row([ft.Button("Reload catalogue", icon=ft.Icons.REFRESH,
                          on_click=lambda e: on_reload and on_reload())], spacing=8),

        ft.Divider(color=pal.border),
        ft.Text("Environment template", size=15, weight=ft.FontWeight.W_600, color=pal.text),
```
with:
```python
        ft.Divider(color=pal.border),
        ft.Text("Environment template", size=15, weight=ft.FontWeight.W_600, color=pal.text),
```

- [ ] **Step 7: `main.py`: drop the cockpit pages and simplify `navigate`**

`main.py` Edit 1 (L3-6, docstring). Replace:
```python
Built on the NEXTGEN base (its rule engine, simulated order book, KRX data
layer, and skill cockpit all survive intact) and upgraded with the thing the
client build was contractually forbidden from having: an opinion. Three new
equity surfaces —
```
with:
```python
Built on the NEXTGEN base (its rule engine, simulated order book and KRX data
layer survive intact; the skill cockpit moved to TRADEGEN on 2026-10-23) and
upgraded with the thing the client build was contractually forbidden from
having: an opinion. Three new equity surfaces —
```

`main.py` Edit 2 (L45-47). Replace:
```python
import config
from core.skills import reload_all
from core.theme import BREAKPOINTS, RADII, TRANSITION_MS, active, set_mode
```
with:
```python
import config
from core.theme import BREAKPOINTS, RADII, TRANSITION_MS, active, set_mode
```

`main.py` Edit 3 (L66-70). Replace:
```python
from ui.trading_page import build_trading_page
from ui.runs_page import build_runs_page
from ui.settings_page import build_settings_page
from ui.skills_page import build_skills_page
from ui.workflows_page import build_workflows_page
```
with:
```python
from ui.trading_page import build_trading_page
from ui.settings_page import build_settings_page
```

`main.py` Edit 4 (NAV, L88-93). Replace:
```python
    ("rules", "Rules", ft.Icons.RULE_FOLDER_OUTLINED),
    ("workflows", "Workflows", ft.Icons.ACCOUNT_TREE_OUTLINED),
    ("skills", "Skills", ft.Icons.EXTENSION_OUTLINED),
    ("krx", "KRX", ft.Icons.SHOW_CHART_ROUNDED),
    ("runs", "Runs", ft.Icons.HISTORY),
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED),
```
with:
```python
    ("rules", "Rules", ft.Icons.RULE_FOLDER_OUTLINED),
    ("krx", "KRX", ft.Icons.SHOW_CHART_ROUNDED),
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED),
```

`main.py` Edit 5 (L124). Replace:
```python
    def build(name: str, **kwargs) -> ft.Control:
```
with:
```python
    def build(name: str) -> ft.Control:
```

`main.py` Edit 6 (L145-177). Replace:
```python
        if name == "rules":
            return build_rules_page(page, rule_store,
                                    on_changed=lambda: cache.pop("trading", None))
        if name == "workflows":
            return build_workflows_page(page, on_open_settings=lambda: navigate("settings"),
                                        on_open_skill=lambda sid: navigate("skills", focus=sid))
        if name == "skills":
            return build_skills_page(page, on_open_settings=lambda: navigate("settings"),
                                     focus_skill=kwargs.get("focus", ""))
        if name == "krx":
            return build_krx_page(page, gateway, locale=LOCALE,
                                  on_open_settings=lambda: navigate("settings"))
        if name == "runs":
            return build_runs_page(page)
        return build_settings_page(page, on_reload=reload_catalogue)

    def navigate(name: str, *, focus: str = "", rebuild: bool = False) -> None:
        # Runs and Skills-with-focus must reflect state that changed elsewhere;
        # everything else keeps its live view so a pipeline survives a tab switch.
        if rebuild or name in ("runs", "trading") or (name == "skills" and focus):
            cache.pop(name, None)
        if name not in cache:
            cache[name] = build(name, focus=focus)
        current["page"] = name
        content.content = ft.Container(cache[name], padding=24, expand=True)
        render_nav()
        page.update()

    def reload_catalogue() -> None:
        reload_all()
        cache.clear()
        navigate("settings", rebuild=True)

```
with:
```python
        if name == "rules":
            return build_rules_page(page, rule_store,
                                    on_changed=lambda: cache.pop("trading", None))
        if name == "krx":
            return build_krx_page(page, gateway, locale=LOCALE,
                                  on_open_settings=lambda: navigate("settings"))
        return build_settings_page(page)

    def navigate(name: str, *, rebuild: bool = False) -> None:
        # Execution must reflect state that changed elsewhere; everything else
        # keeps its live view so a pipeline survives a tab switch.
        if rebuild or name == "trading":
            cache.pop(name, None)
        if name not in cache:
            cache[name] = build(name)
        current["page"] = name
        content.content = ft.Container(cache[name], padding=24, expand=True)
        render_nav()
        page.update()

```
These edits keep three test-pinned strings in `main.py`:
- `cache[name] = build(` (safety test_15);
- `page.on_resize =` (test_14);
- the single `core.skills.macro_daily` app-start call (`tests/macro_m8_pipeline.py` L518-519).

- [ ] **Step 8: Run the two tests (now PASS) and smoke-check the removals**

```bash
python -B -c "from tests.acceptance import test_13_settings_page_shows_presence_not_values as t; t(); print('test_13 PASS')"
python -B -c "from tests.macro_m8_pipeline import test_yaml_loads_with_the_strict_runner_and_the_legacy_parser_is_untouched as t; t(); print('m8 yaml PASS')"
python -B -c "import config; print('left:', [n for n in ('_DEFAULT_SKILLS_ROOT','skills_root','skills_root_valid','skill_python','SKILL_TIMEOUT_SECONDS','runs_dir','SKILL_CREDENTIALS','KEYLESS_INTEGRATIONS','FILE_INPUT_INTEGRATIONS','skill_credential_present','skill_env','skill_provider_status') if hasattr(config, n)]); print([p['id'] for p in config.quant_provider_status()])"
python -B -c "import ui.components as C; print([n for n in ('STATE_STYLE','RUN_STATUS_STYLE','readiness_chip','run_status_chip','State') if hasattr(C, n)])"
python -B -c "import main; print(len(main.NAV), [n for n, _, _ in main.NAV])"
python -B -c "from ui.settings_page import build_settings_page; print(len(build_settings_page(None).controls))"
```
Expected:
```
test_13 PASS
m8 yaml PASS
left: []
['fmp', 'anthropic', 'gs']
[]
16 ['macro', 'rates', 'bonds', 'fx', 'structuring', 'derivatives', 'etf', 'crypto', 'lab', 'quant', 'portfolio', 'signals', 'trading', 'rules', 'krx', 'settings']
21
```
The Settings page had 27 controls at HEAD (measured with a valid skills root). Six are removed: the two "Skill providers" rows, and the Repository divider, title, block and reload row. That leaves 21.

- [ ] **Step 9: Split `tests/acceptance.py`, rename the suite, fix the rail test; run safety, ui and macro_ui_components**

Rewrite `tests/acceptance.py` (958 lines at HEAD). Every function except test_13 is copied verbatim from HEAD:
- `_read`, `_code_only`, `runtime_py`: L27-54;
- test_08 and test_09: L169-182;
- test_14 to test_18: L228-270;
- test_21 and test_22: L318-330;
- `tests()`: L956-958.

Removed from the HEAD file:
- the 37 tests:
  - test_01 to test_07 and test_07b (L57-164);
  - test_10, 11 and 12 (L185-215);
  - test_19 and 20 (L273-316);
  - test_23 to test_46 (L333-955);
- `import os` (L20), which is no longer used.

`tests/acceptance.py` (whole file):
```python
"""Safety acceptance checks, run as the `safety` suite.

The ten checks that stayed when the NEXTGEN skill cockpit, with the 37 tests of
its catalogue, runner, argument reader and workflow gates, moved to TRADEGEN
(2026-10-23). Three groups:

  * **Safety** — the invariants this build promises: no broker order path, no
    account credential requested, no key printed to a screen.
  * **Regression** — the defects found in the previous build's review. All were
    silent failures, so each gets a test that fails loudly.
  * **KRX gateway** — a provider that is missing or declines says why.

`_read`, `_code_only` and `runtime_py` are shared: seven `tests/macro_*` modules
import them.

Every file read here passes `encoding="utf-8"` explicitly. The previous suite
did not, and five of its tests died with `UnicodeDecodeError: 'cp949'` on this
machine — the target machine — because Windows Korean locale picks cp949 as the
default and `main.py` contains an em dash.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _code_only(path: Path) -> str:
    """Source with docstrings and comments stripped.

    Several checks below assert that a token does not appear in the code. The
    same token is discussed in prose in the very files being checked — naming
    the defect is the point of the comment — so scanning raw text produces false
    positives. `ast` gives us the executable surface instead.
    """
    import ast
    tree = ast.parse(_read(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def runtime_py() -> list[Path]:
    files: list[Path] = []
    for base in (ROOT / "core", ROOT / "data", ROOT / "ui"):
        if base.is_dir():
            files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    files.extend([ROOT / "main.py", ROOT / "config.py"])
    return [p for p in files if p.is_file()]


# --------------------------------------------------------------------------- #
# Safety
# --------------------------------------------------------------------------- #
def test_08_no_broker_order_path():
    """KIS is a brokerage API; this build implements quotations only."""
    needles = ["order_cash", "order-cash", "place_order", "submit_order",
               "TTTC0802U", "TTTC0801U", "VTTC0802U"]
    blob = "\n".join(_read(p) for p in runtime_py()).lower()
    hits = [n for n in needles if n.lower() in blob]
    assert not hits, f"broker order surface present: {hits}"


def test_09_no_account_credentials_requested():
    """Order submission needs an account number. Never ask for one."""
    blob = "\n".join(_read(p) for p in runtime_py())
    for name in ("KIS_ACCOUNT", "CANO", "ACNT_PRDT_CD"):
        assert name not in blob, f"{name} implies an order path"


def test_13_settings_page_shows_presence_not_values():
    """No credential value may reach a widget. FMP, shown before the split only
    among the cockpit's skill providers, is a presence row in the quant list."""
    import config
    source = _read(ROOT / "ui" / "settings_page.py")
    assert "kis_credentials()" not in source
    assert "opendart_key()" not in source
    assert "_clean(" not in source
    assert "fmp_key()" not in source and "core.skills" not in source
    fmp = [p for p in config.quant_provider_status() if p["id"] == "fmp"]
    assert len(fmp) == 1 and fmp[0]["vars"] == ("FMP_API_KEY",), fmp
    assert fmp[0]["ready"] == config.fmp_ready()


# --------------------------------------------------------------------------- #
# Regression — defects found reviewing the previous build
# --------------------------------------------------------------------------- #
def test_14_page_resize_handler_matches_the_flet_api():
    """The old build assigned a handler to an attribute Flet 0.85 does not
    define, so the compact layout never ran at any width. Assert against the
    live API and against the assignment in code, not against prose — the
    misspelling is named in comments here and in main.py on purpose."""
    import flet as ft
    assert hasattr(ft.Page, "on_resize"), "Flet renamed the resize event again"
    source = _code_only(ROOT / "main.py")
    assert re.search(r"page\.on_resize\s*=", source), "no resize handler is attached"
    assert not re.search(r"page\.on_resiz(ed|e_d)\s*=", source), \
        "main.py attaches a handler to an attribute Flet does not define"


def test_15_views_are_cached_across_navigation():
    """Rebuilding a view on every nav click discarded live state."""
    source = _read(ROOT / "main.py")
    assert "cache" in source and "cache[name] = build(" in source


def test_16_every_source_file_is_utf8_readable():
    """The previous suite read files with the platform default and died on cp949."""
    for path in runtime_py() + [ROOT / "tests" / "acceptance.py", ROOT / "tests" / "run_all.py"]:
        try:
            _read(path)
        except UnicodeDecodeError as exc:
            raise AssertionError(f"{path} is not valid UTF-8: {exc}") from None


def test_17_tests_never_read_without_an_encoding():
    """Lock the cp949 fix: reading a file with no explicit encoding here is what
    killed five tests in the previous suite."""
    for name in ("acceptance.py", "run_all.py"):
        source = _code_only(ROOT / "tests" / name)
        assert not re.search(r"read_text\(\s*\)", source), \
            f"{name} reads a file without specifying an encoding"


def test_18_eodhd_is_gone_from_the_runtime():
    """No EODHD *usage*. The name still appears in prose that explains what this
    build replaced, which is why this scans code rather than raw text."""
    blob = "\n".join(_code_only(p) for p in runtime_py()).lower()
    for token in ("eodhd", "quartr"):
        assert token not in blob, f"{token} is still used in the runtime surface"


# --------------------------------------------------------------------------- #
# KRX gateway
# --------------------------------------------------------------------------- #
def test_21_krx_gateway_degrades_with_a_reason():
    """No provider configured must yield an actionable reason, never a blank."""
    from data.krx import KRXGateway
    gateway = KRXGateway()
    for answer in (gateway.daily("005930"), gateway.filings("005930")):
        if not answer.ok:
            assert answer.reason.strip(), "a failed answer must explain itself"


def test_22_krx_status_is_reported_per_provider():
    from data.krx import KRXGateway
    providers = {s["provider"] for s in KRXGateway().status()}
    assert providers == {"KIS", "OpenDART", "KRX"}


def tests():
    return sorted((n, v) for n, v in globals().items()
                  if n.startswith("test_") and callable(v))
```

`tests/acceptance.py` is CRLF at HEAD. Convert this one rewrite to CRLF (the converter is idempotent; never run it on any other file, and never on an LF file):
```bash
python -c "import pathlib; p = pathlib.Path('tests/acceptance.py'); p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))"
```
`core/skills/__init__.py` (Step 4) stays LF, as it is at HEAD.

`tests/run_all.py` Edit 1 (L41). Replace:
```python
from tests.acceptance import tests as cockpit_tests        # noqa: E402
```
with:
```python
from tests.acceptance import tests as safety_tests         # noqa: E402
```

`tests/run_all.py` Edit 2 (L57). Replace:
```python
    return ([(f"cockpit/{n}", f) for n, f in cockpit_tests()] +
```
with:
```python
    return ([(f"safety/{n}", f) for n, f in safety_tests()] +
```

`tests/run_all.py` Edit 3 (L111, as Task 1 left it). Replace:
```python
    parser.add_argument("--suite", help="run one suite: cockpit, engine, ui, quant, ficc, expansion, macro, paper, grokteam or guard")
```
with:
```python
    parser.add_argument("--suite", help="run one suite: safety, engine, ui, quant, ficc, expansion, macro, paper, grokteam or guard")
```

`tests/macro_ui_components.py` (L120-127). The function name stays, so the test identity holds. Replace:
```python
def test_shell_fixes_runs_page_delegates_and_the_rail_scrolls():
    runs_src = (ROOT / "ui" / "runs_page.py").read_text(encoding="utf-8")
    assert "open_path(path)" in runs_src and "startfile" not in runs_src
    tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    rail = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "Column"
            and any(isinstance(a, ast.Name) and a.id == "nav_host" for a in ast.walk(n))]
    assert rail and any(k.arg == "scroll" for k in rail[0].keywords), "the rail column must scroll (19 entries, 620 px)"
    assert "on_app_start(background=True)" in (ROOT / "main.py").read_text(encoding="utf-8")
```
with:
```python
def test_shell_fixes_runs_page_delegates_and_the_rail_scrolls():
    # The Runs page left with the cockpit (TRADEGEN, 2026-10-23); the name is kept so the test identity holds.
    tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    rail = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "Column"
            and any(isinstance(a, ast.Name) and a.id == "nav_host" for a in ast.walk(n))]
    assert rail and any(k.arg == "scroll" for k in rail[0].keywords), "the rail column must scroll (16 entries, 620 px)"
    assert "on_app_start(background=True)" in (ROOT / "main.py").read_text(encoding="utf-8")
```

Run:
```bash
python - <<'EOF'
import ast, subprocess
old = ast.parse(subprocess.run(["git", "show", "HEAD:tests/acceptance.py"], capture_output=True, check=True).stdout.decode("utf-8"))
new = ast.parse(open("tests/acceptance.py", encoding="utf-8").read())
o = {f.name: ast.unparse(f) for f in old.body if isinstance(f, ast.FunctionDef)}
n = {f.name: ast.unparse(f) for f in new.body if isinstance(f, ast.FunctionDef)}
same = [k for k in n if k != "test_13_settings_page_shows_presence_not_values"]
assert all(n[k] == o[k] for k in same), [k for k in same if n[k] != o[k]]
print(len(n), "functions;", sum(k.startswith("test_") for k in n), "tests; kept verbatim:", len(same))
EOF
python tests/run_all.py --suite safety
python tests/run_all.py --suite ui
python -B -m tests.macro_ui_components
```
Expected:
- The AST check prints `14 functions; 10 tests; kept verbatim: 13`.
- The safety suite prints 10 `PASS safety/test_…` lines, then `10/10 passed, 0 failed, 0 not run`.
- The ui suite prints `4/4 passed, 0 failed, 0 not run`.
- macro_ui_components prints `9/9 passed, 0 failed, 0 not run`.

The two `run_all --suite` runs overwrite `qa/acceptance_results.json` with partial results. Step 12's full run rewrites it before the commit.

- [ ] **Step 10: Dangling text (`.env.example`, KRX page, pipeline docstrings, macro YAML comment, macro_acceptance, ARCHITECTURE_REVIEW, README)**

`.env.example` Edit 1 (L3). Replace:
```
# labeled synthetic data and the KRX/skills pages report what is missing.
```
with:
```
# labeled synthetic data and the KRX and Settings pages report what is missing.
```

`.env.example` Edit 2 (L10-18). Replace:
```
KRX_API_KEY=

# --- Skill-library providers (forwarded to skill subprocesses) --------------
FINVIZ_API_KEY=
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
FXMACRODATA_API_KEY=

# --- Quant analysis ---------------------------------------------------------
```
with:
```
KRX_API_KEY=

# --- Quant analysis ---------------------------------------------------------
```

`ui/krx_page.py` Edit 1 (L1-6). Replace:
```python
"""KRX: the Korean coverage the skill library does not have.

Every one of the 72 skills targets US equities, crypto or CME futures — a grep
for KOSPI/KOSDAQ/KRX across the whole repository returns nothing. This page is
NEXTGEN's own read-only Korean data surface, sitting on KIS, OpenDART and the
KRX Open API.
```
with:
```python
"""KRX: QUANTGEN's own read-only Korean market data surface.

It sits on KIS, OpenDART and the KRX Open API. It was first built for NEXTGEN
because the trading-skills library (now in TRADEGEN) had no Korean coverage.
```

`ui/krx_page.py` Edit 2 (L189-190). Replace:
```python
        notice("The skill library has no KRX coverage; this page is NEXTGEN's own. "
               "No order or account-mutation path exists in this build.",
```
with:
```python
        notice("No order or account-mutation path exists in this build.",
```

`core/skills/pipeline.py` Edit 1 (module docstring L12-13; docstring only). Replace:
```
`macro.run_record` is the runner's epilogue. Nothing here imports Flet, `core.skills.runner` or
`core.skills.workflows` (the legacy parser is untouched); clock, calendars and paths are injected.
```
with:
```
`macro.run_record` is the runner's epilogue. Nothing here imports Flet or the legacy skill runner and workflow
parser (both moved to TRADEGEN on 2026-10-23); clock, calendars and paths are injected.
```

`core/skills/pipeline.py` Edit 2 (`load_pipeline` docstring L73-74). Replace:
```python
    """Strict reader of `core/skills/macro_workflows/*.yaml` (section 3.9 shape: name, runs, run_mode, steps of
    `skill:` or `gate:`). Never routed through `core.skills.workflows` (code_skills_workflows D.2)."""
```
with:
```python
    """Strict reader of `core/skills/macro_workflows/*.yaml` (section 3.9 shape: name, runs, run_mode, steps of
    `skill:` or `gate:`). Never routed through the legacy workflow parser (code_skills_workflows D.2), which moved
    to TRADEGEN on 2026-10-23."""
```

`core/skills/macro_workflows/macro_daily.yaml` (comment L2). Replace:
```
# core/skills/macro_daily (in-process, headless). Never routed through core/skills/workflows.py or the Flet page.
```
with:
```
# core/skills/macro_daily (in-process, headless). Never routed through the legacy workflow parser (moved to
# TRADEGEN on 2026-10-23) or the Flet page.
```

`tests/macro_acceptance.py` Edit 1 (L8). Replace:
```
process: `engine/test_82` serves a loopback HTTP server through `data.net.session` and `cockpit/test_21`
```
with:
```
process: `engine/test_82` serves a loopback HTTP server through `data.net.session` and `safety/test_21`
```

`tests/macro_acceptance.py` Edit 2 (L116-117). Replace:
```
    QUANTGEN_MACRO_DIR when set. Not all of `~/.nextgen`: the legacy cockpit tests write `~/.nextgen/runs` by
    design, so a concurrent full run tripped T-HERM-02 falsely (Sprint 4 coordinator ruling)."""
```
with:
```
    QUANTGEN_MACRO_DIR when set. Not all of `~/.nextgen`: the cockpit tests (now in TRADEGEN) write `~/.nextgen/runs`
    by design, so a concurrent full run tripped T-HERM-02 falsely (Sprint 4 coordinator ruling)."""
```

`docs/ARCHITECTURE_REVIEW.md` (the rail at L60): add a dated note after the diagram's closing fence, L97. The box art is not redrawn: removing three cells would misalign every line from L58 to L97. Replace:
````
```

### 1.2 The Quant Lab pipeline (as built today)
````
with:
````
```

> **2026-10-23, split (D2).** The Workflows, Skills and Runs rail entries, `param_form`, `charts`, all eleven
> `core/skills` cockpit modules (index, entrypoints, params, readiness, runner, runs, diagnose, workflows,
> decisions, insights, wiring) and the skill env in `config.py` moved to TRADEGEN. The map above shows the
> application before the split. The rail now has 16 entries, and `core/skills` keeps only `macro_daily`,
> `pipeline`, `alerts` and `macro_workflows/`.

### 1.2 The Quant Lab pipeline (as built today)
````

`README.md` Edit 1 (L4-5). Replace:
```
simulated order book, KRX data layer, and skill cockpit all survive intact —
with the one organ the client build was contractually forbidden from having:
```
with:
```
simulated order book and KRX data layer all survive intact (the skill cockpit
moved to TRADEGEN on 2026-10-23) — with the one organ the client build was
contractually forbidden from having:
```

`README.md` Edit 2 (L354). Replace:
```
verdict. Static scans (T-RO-01, cockpit test_08 / test_09) hold the line.
```
with:
```
verdict. Static scans (T-RO-01, safety test_08 / test_09) hold the line.
```

`README.md` Edit 3 (L738-747). Replace:
```
## Everything inherited from NEXTGEN

Execution, Rules, Workflows, Skills, KRX, Runs, and Settings are the NEXTGEN
surfaces, unchanged: the DISARMED→ARMED→HALTED engine, frozen rules with
edit-revokes-confirmation, the simulated order book (there is still **no
broker order path** in this repository), the 72-skill cockpit, and the
KIS/OpenDART/KRX data layer. The macro overlay does not run through this
engine: each v2 book has its own runtime state (see [Statuses](#statuses)).
The navigation rail scrolls, so all nineteen entries are reachable at the
620 px minimum window height.
```
with:
```
## Inherited from NEXTGEN

Execution, Rules, KRX and Settings are the NEXTGEN surfaces: the
DISARMED→ARMED→HALTED engine, frozen rules with edit-revokes-confirmation, the
simulated order book (there is still **no broker order path** in this
repository) and the KIS/OpenDART/KRX data layer. The skill cockpit (Workflows,
Skills, Runs and the 72-skill catalogue) moved to TRADEGEN on 2026-10-23. The
macro overlay does not run through this engine: each v2 book has its own
runtime state (see [Statuses](#statuses)). The navigation rail scrolls, so all
sixteen entries are reachable at the 620 px minimum window height.
```
No link in the repo targets the old `#everything-inherited-from-nextgen` anchor (checked by grep).

`README.md` Edit 4 (L829-830). Replace:
```
price against NAV). The skill-insight bars (`ui/charts.py`) and the v2
multiplier bar (`ui/components.py`) are drawn with containers, not matplotlib.
```
with:
```
price against NAV). The v2 multiplier bar (`ui/components.py`) is drawn with
containers, not matplotlib.
```

Two README lines still say `cockpit` on purpose, until Task 5: the `--suite` list at L763 and the table row at L777. The intro sentence "QUANTGEN computes analysis, ranks outcomes, and recommends" (README L6) is reworded by Task 5 Step 5.

- [ ] **Step 11: Static checks (no importer left, EOL as at HEAD, frozen dirs untouched, count 816)**

```bash
grep -rnE "^\s*(from|import) (core\.skills\.(index|entrypoints|params|readiness|runner|runs|diagnose|workflows|decisions|insights|wiring)|ui\.(skills_page|workflows_page|runs_page|param_form|charts))\b|from core\.skills import .*(reload_all|all_skills|readiness|runner|workflows)" --include=*.py core data ui tests docs main.py config.py
git ls-files --eol -- main.py config.py .env.example core/skills/__init__.py core/skills/pipeline.py core/skills/macro_workflows/macro_daily.yaml ui/settings_page.py ui/components.py ui/krx_page.py tests/acceptance.py tests/run_all.py tests/macro_m8_pipeline.py tests/macro_ui_components.py tests/macro_acceptance.py docs/ARCHITECTURE_REVIEW.md README.md | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'
git diff --stat HEAD -- paper_live grokteam core/engine ui/trading_page.py
python -B -c "from tests.run_all import tests; import collections; t=tests(); print(len(t), dict(collections.Counter(n.split('/')[0] for n,_ in t)))"
```
Expected:
- The grep prints nothing.
- The `awk` line prints nothing. `i/` is HEAD's EOL (nothing is staged yet except the `git rm` deletions) and `w/` is the working copy's. If a file is listed, `git checkout -- <file>` and redo that file's edits with the Edit tool (for `tests/acceptance.py`, rewrite it and rerun the Step 9 converter). Never run the converter on an LF file.
- `git diff --stat` prints nothing.
- The last command prints `816 {'safety': 10, 'engine': 92, 'ui': 4, 'quant': 53, 'ficc': 56, 'expansion': 19, 'macro': 539, 'paper': 21, 'grokteam': 17, 'guard': 5}`.

- [ ] **Step 12: Full suite and identity comparison**

```bash
python tests/run_all.py
```
This takes about 11 minutes and may run in the background. Don't run any QUANTGEN or TRADEGEN app meanwhile (T-HERM-02).

Expected summary line: `695/816 passed, 0 failed, 121 not run; ...`.

Compare identities and statuses with the committed "before" run. Run this before committing, so `HEAD` is still Task 1's commit:
```bash
python - <<'EOF'
import collections, json, subprocess
KEPT = {"test_08_no_broker_order_path", "test_09_no_account_credentials_requested",
        "test_13_settings_page_shows_presence_not_values", "test_14_page_resize_handler_matches_the_flet_api",
        "test_15_views_are_cached_across_navigation", "test_16_every_source_file_is_utf8_readable",
        "test_17_tests_never_read_without_an_encoding", "test_18_eodhd_is_gone_from_the_runtime",
        "test_21_krx_gateway_degrades_with_a_reason", "test_22_krx_status_is_reported_per_provider"}
before = json.loads(subprocess.run(["git", "show", "HEAD:qa/acceptance_results.json"],
                                   capture_output=True, check=True).stdout.decode("utf-8"))
after = json.load(open("qa/acceptance_results.json", encoding="utf-8"))
norm = lambda t: "safety/" + t[len("cockpit/"):] if t.startswith("cockpit/") else t
b = {norm(r["test"]): r["status"] for r in before}
a = {r["test"]: r["status"] for r in after}
removed, added = sorted(set(b) - set(a)), sorted(set(a) - set(b))
changed = sorted(n for n in set(a) & set(b) if a[n] != b[n])
print("before", len(b), dict(collections.Counter(b.values())))
print("after ", len(a), dict(collections.Counter(a.values())))
print("removed", len(removed), "added", added, "status changed", changed)
assert len(removed) == 37 and all(n.startswith("safety/") and n[len("safety/"):] not in KEPT for n in removed), removed
assert not added and not changed, (added, changed)
assert {n[len("safety/"):] for n in a if n.startswith("safety/")} == KEPT
assert (len(a), collections.Counter(a.values())["PASS"]) == (816, 695), len(a)
print("OK: exactly the 37 cockpit tests left; every other identity and status is unchanged")
EOF
```
Expected:
- `before 853 {'PASS': 732, 'NOT_RUN': 121}`, `after  816 {'PASS': 695, 'NOT_RUN': 121}`;
- `removed 37 added [] status changed []`, then the `OK:` line.

If any status changed, stop and investigate before committing. This task touches no code that those tests read, except `main.py`, `config.py`, `core/skills/__init__.py`, the two `core/skills` docstrings and the `ui/` files edited above.

- [ ] **Step 13: Commit**

```bash
git add main.py config.py .env.example core/skills/__init__.py core/skills/pipeline.py core/skills/macro_workflows/macro_daily.yaml ui/settings_page.py ui/components.py ui/krx_page.py tests/acceptance.py tests/run_all.py tests/macro_m8_pipeline.py tests/macro_ui_components.py tests/macro_acceptance.py docs/ARCHITECTURE_REVIEW.md README.md qa/acceptance_results.json
git status --short
git commit -F - <<'EOF'
A1: move the skill cockpit out of QUANTGEN (D2)

Delete the cockpit modules (core/skills index, entrypoints, params,
readiness, runner, runs, diagnose, workflows, decisions, insights, wiring)
and the Workflows, Skills and Runs pages with param_form and charts;
core/skills keeps macro_daily, pipeline, alerts and macro_workflows/.
config.py loses the skill settings; the FMP row moves into
quant_provider_status() with ready = fmp_ready(). tests/acceptance.py keeps
the 10 safety and regression checks, registered as suite "safety"; the 37
cockpit tests leave with the code. Dangling text fixed (pipeline docstrings
and the macro_daily.yaml comment included); the README test table is
updated in the last Phase 1 commit.

Suite: 695/816 PASS, 0 FAIL, 121 NOT_RUN.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
Expected:
- Before the commit, `git status --short` shows 16 `D ` lines and 17 `M ` lines, and nothing unstaged or untracked.
- The commit succeeds.

Owner housekeeping, not done by Claude: remove these keys from QUANTGEN's real `.env`:
- `NEXTGEN_SKILLS_ROOT`, `FINVIZ_*`, `ALPACA_*`, `FXMACRODATA_*`;
- `KIS_ACCOUNT_PD`;
- the unused `TYPESAFE_API_KEY`.

---

### Task 3: A2: crypto regime score out (spec 4.1 A2)

**Files:**
- Modify: `core/crypto/analytics.py` (LF). Module docstring L1-4 and L15-21; the "Regime score" block L174-278 (`RegimeComponent`, `RegimeScore`, `_sma`, `regime_score`); the self-check's regime lines L430-435. L429 (`majors = ...`) stays because `eth_btc_test` at L436 reads `majors["ETH"]`.
- Modify: `ui/crypto_page.py` (LF). Docstring L1-3; `MAJORS` L24; `_synthetic` L38-41; `_live` L52-61; `analyze` L76-77; `narrative` L110 and L121-123; `payload` L136 and L141-142; `build_crypto_page` L164, L182, L190-192, L220-222 and L225; self-check L231-239.
- Modify: `tests/expansion_acceptance.py` (LF) L343-344 (register the page self-check).
- Modify: `README.md` (CRLF) L215-216 (crypto paragraph).
- Modify: `docs/ASSET_EXPANSION_SPEC.md` (LF) L177 (dated "moved to TRADEGEN" note).
- Modify: `docs/build_expansion_primer.py` (CRLF) L616 (dated comment above the regime paragraph) and L662 (dated comment plus the row text). Do not rebuild `docs/QUANTGEN_Expansion_Primer.pdf`; it stays as the built artifact.
- Modify (regenerated by the run): `qa/acceptance_results.json`.
- Test: new registered test `expansion/selfcheck_crypto_page` (runs `ui/crypto_page.py`'s `__main__` block); existing `expansion/selfcheck_crypto_analytics` stays registered.
- Not in this task: the README test table (L763-786) is updated once, in the last Phase 1 commit.
- Line numbers versus the spec. The spec's "`if rs:` block L120-123" is really L121-123: there is no `if rs:`, and L120 ends the funding sentence, which stays. The spec's "189-192" chart is really L190-192, because L189 ends the funding chart, which stays. The empty-state text at "L220" spans L220-222.

**Interfaces:**
- Consumes: `tests.expansion_acceptance._selfcheck(rel: str)` (L28-33, unchanged), which runs `runpy.run_path(ROOT / rel, run_name="__main__")`. Also `core.crypto.analytics.kimchi_premium`, `funding_carry`, `eth_btc_test` and `weekday_table`, all unchanged. Task 2's committed full results (816 rows: 695 PASS) as the "before" run.
- Produces:
  - `ui.crypto_page.analyze(*, days: int = 730, source: str = "live") -> dict` without the key `"regime"`.
  - `ui.crypto_page._synthetic() -> dict` and `_live(days: int) -> dict` without the key `"majors"`. The synthetic `"eth"` series is byte-identical to HEAD.
  - `ui.crypto_page.narrative(a: dict) -> str` without the regime sentence.
  - `ui.crypto_page.payload(a: dict) -> dict` without the key `"regime"`.
  - Removed names: `core.crypto.analytics.regime_score`, `RegimeComponent`, `RegimeScore` and `_sma`, and `ui.crypto_page.MAJORS`. The 8 Binance `daily(sym, days=400)` calls per live load go with them.
  - New suite row: `expansion/selfcheck_crypto_page`.
  - Full run after this task: 696/817 passed, 0 failed, 121 not run.

- [ ] **Step 1: Save the "before" results of the full suite**

The previous change group's commit holds a full-suite `qa/acceptance_results.json`. Copy it outside the repo:

```bash
git status --short
python - <<'EOF'
import json, os, shutil, tempfile
r = json.load(open("qa/acceptance_results.json", encoding="utf-8"))
assert len(r) == 816, f"{len(r)} rows: not Task 2's full run; run `python tests/run_all.py` first, then repeat this step"
dst = os.path.join(tempfile.gettempdir(), "quantgen_task3_before.json")
shutil.copy("qa/acceptance_results.json", dst)
print(len(r), "rows saved to", dst)
EOF
```

Expected: `git status --short` prints nothing. The script prints `816 rows saved to ...\quantgen_task3_before.json`.

- [ ] **Step 2: Write the failing test (register the page self-check and assert the regime is gone)**

`tests/expansion_acceptance.py` (L343-344). Replace:

```python
        ("selfcheck_crypto_analytics", _selfcheck("core/crypto/analytics.py")),
    ]
```

with:

```python
        ("selfcheck_crypto_analytics", _selfcheck("core/crypto/analytics.py")),
        ("selfcheck_crypto_page", _selfcheck("ui/crypto_page.py")),
    ]
```

`ui/crypto_page.py` self-check (L231-239). Replace:

```python
if __name__ == "__main__":
    a = analyze(source="synthetic")
    assert a["source"] == "SYNTHETIC" and a["kimchi"].n > 800 and a["regime"].zone in ("RISK_ON", "NEUTRAL", "RISK_OFF")
    assert a["garch"]["n"] == 730 and len(a["weekday"]["rows"]) == 7
    t = narrative(a)
    assert "Korea pays" in t and "regime score" in t and "SYNTHETIC" in t
    p = payload(a)
    assert p["regime"]["components"] and p["kimchi"]["n"] == a["kimchi"].n
    print("ok")
```

with:

```python
if __name__ == "__main__":
    a = analyze(source="synthetic")
    assert a["source"] == "SYNTHETIC" and a["kimchi"].n > 800 and "regime" not in a
    assert "MAJORS" not in globals() and "majors" not in _synthetic()
    assert not any(hasattr(CA, k) for k in ("regime_score", "RegimeScore", "RegimeComponent", "_sma"))
    assert a["garch"]["n"] == 730 and len(a["weekday"]["rows"]) == 7
    t = narrative(a)
    assert "Korea pays" in t and "regime" not in t.lower() and "SYNTHETIC" in t
    p = payload(a)
    assert "regime" not in p and p["kimchi"]["n"] == a["kimchi"].n
    print("ok")
```

- [ ] **Step 3: Run the expansion suite and confirm the new test fails**

Run: `python tests/run_all.py --suite expansion` (about 2 minutes)

Expected:
- the 19 existing rows PASS;
- `FAIL expansion/selfcheck_crypto_page AssertionError:`, with a traceback ending at `ui/crypto_page.py`, line 233 (`... and "regime" not in a`);
- the summary `19/20 passed, 1 failed, 0 not run`, and exit code 1.

This run rewrites `qa/acceptance_results.json` with 20 rows. Do not commit until the full run in Step 11.

- [ ] **Step 4: Remove the regime from `ui/crypto_page.py`**

Make these 14 edits in `ui/crypto_page.py` (LF; keep it).

4a. `ui/crypto_page.py` docstring, L1-3. Replace:

```python
"""Crypto — the kimchi premium, funding as carry, the market-regime score,
the app's GARCH(1,1)-t on Bitcoin, the ETH/BTC test, the weekday table and,
when an Upbit read-only key is configured, the holdings with their cost basis.
```

with:

```python
"""Crypto — the kimchi premium, funding as carry, the app's GARCH(1,1)-t on
Bitcoin, the ETH/BTC test, the weekday table and, when an Upbit read-only key
is configured, the holdings with their cost basis.
```

4b. `ui/crypto_page.py` `MAJORS`, L24-25. Replace:

```python
MAJORS = ("ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "TRXUSDT", "LINKUSDT")
CRYPTO_DAYS = 365
```

with:

```python
CRYPTO_DAYS = 365
```

4c. `ui/crypto_page.py` `_synthetic`, L38-41. ETH was the first of the old majors, so drawing it directly at the same point keeps the synthetic ETH series byte-identical. Only the later `volume` draw shifts. Replace:

```python
    fund = rng.normal(0.0002, 0.0004, n)
    majors = {k: 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.04, n))) for k in MAJORS}
    return {"dates": ds, "upbit": dict(zip(ds, kr)), "binance": dict(zip(ds, us)), "usdkrw": dict(zip(ds, fx)),
            "funding_daily": dict(zip(ds, fund)), "majors": majors, "eth": dict(zip(ds, majors["ETHUSDT"])),
```

with:

```python
    fund = rng.normal(0.0002, 0.0004, n)
    eth = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.04, n)))    # the same draw ETHUSDT had as the first major
    return {"dates": ds, "upbit": dict(zip(ds, kr)), "binance": dict(zip(ds, us)), "usdkrw": dict(zip(ds, fx)),
            "funding_daily": dict(zip(ds, fund)), "eth": dict(zip(ds, eth)),
```

4d. `ui/crypto_page.py` `_live`, L51-61. This removes 8 Binance calls per load. Replace:

```python
    btc = bn.daily("BTCUSDT", days=days)
    majors = {}
    for sym in MAJORS:
        try:
            majors[sym] = np.asarray(bn.daily(sym, days=400).close)
        except Exception:
            continue
    fund = bn.funding("BTCUSDT", days=min(days, 1500)).daily()
    fx = load_series("DEXKOUS", source="auto", days=days + 100)
    return {"dates": btc.dates, "upbit": dict(zip(up.dates, up.close)), "binance": dict(zip(btc.dates, btc.close)),
            "usdkrw": dict(zip(fx.dates, fx.values)), "usdkrw_source": fx.source, "funding_daily": fund, "majors": majors,
```

with:

```python
    btc = bn.daily("BTCUSDT", days=days)
    fund = bn.funding("BTCUSDT", days=min(days, 1500)).daily()
    fx = load_series("DEXKOUS", source="auto", days=days + 100)
    return {"dates": btc.dates, "upbit": dict(zip(up.dates, up.close)), "binance": dict(zip(btc.dates, btc.close)),
            "usdkrw": dict(zip(fx.dates, fx.values)), "usdkrw_source": fx.source, "funding_daily": fund,
```

4e. `ui/crypto_page.py` `analyze`, L75-78. Replace:

```python
    btc = np.array([d["binance"][k] for k in sorted(d["binance"])])
    fa = out["funding"].last_ann_pct if out["funding"] else None
    out["regime"] = CA.regime_score(btc, d["majors"], funding_ann_pct=fa)
    out["ethbtc"] = CA.eth_btc_test(d["eth"], d["binance"])
```

with:

```python
    btc = np.array([d["binance"][k] for k in sorted(d["binance"])])
    out["ethbtc"] = CA.eth_btc_test(d["eth"], d["binance"])
```

4f. `ui/crypto_page.py` `narrative`, L110-111. The two-line context is needed because L164 holds the same assignment at a deeper indent. Replace:

```python
    kp, fc, rs, g = a["kimchi"], a["funding"], a["regime"], a["garch"]
    parts = [
```

with:

```python
    kp, fc, g = a["kimchi"], a["funding"], a["garch"]
    parts = [
```

4g. `ui/crypto_page.py` `narrative`, L121-123. Delete:

```python
    live = [c for c in rs.components if c.score is not None]
    parts.append(f"The regime score is {rs.score:.0f}/100 ({rs.zone}) from {len(live)} components: " +
                 "; ".join(f"{c.label} {c.score:.0f} ({c.signal})" for c in live) + ". " + rs.note)
```

4h. `ui/crypto_page.py` `payload`, L136. Replace:

```python
    kp, fc, rs = a["kimchi"], a["funding"], a["regime"]
```

with:

```python
    kp, fc = a["kimchi"], a["funding"]
```

4i. `ui/crypto_page.py` `payload`, L141-142. Replace:

```python
            "premium_index": a["premium_index"], "regime": {"score": rs.score, "zone": rs.zone, "components":
                                                            [{"key": c.key, "score": c.score, "signal": c.signal} for c in rs.components]},
```

with:

```python
            "premium_index": a["premium_index"],
```

4j. `ui/crypto_page.py` `build_crypto_page`, L164-165. Replace:

```python
            kp, fc, rs, g = a["kimchi"], a["funding"], a["regime"], a["garch"]
            blocks: list[ft.Control] = []
```

with:

```python
            kp, fc, g = a["kimchi"], a["funding"], a["garch"]
            blocks: list[ft.Control] = []
```

4k. `ui/crypto_page.py` the Regime tile, L182. Delete:

```python
                stat("Regime", f"{rs.score:.0f} · {rs.zone}", token="success" if rs.zone == "RISK_ON" else "error" if rs.zone == "RISK_OFF" else "text"),
```

4l. `ui/crypto_page.py` the components chart, L190-192. Delete:

```python
            blocks.append(card(xc.bars_chart([c.label for c in rs.components], [c.score for c in rs.components],
                                             title=f"Regime components (score {rs.score:.0f}, {rs.zone})",
                                             annotate=[c.signal for c in rs.components])))
```

4m. `ui/crypto_page.py` the empty-state text, L220-222. Replace:

```python
    host.controls = [empty_state("Refresh the crypto sheet", "Kimchi premium, perpetual funding as carry, the six-component regime "
                                 "score, GARCH-t on Bitcoin, the ETH/BTC test and the weekday table, all from keyless Upbit and "
                                 "Binance data; Upbit holdings when a read-only key is set.", icon=ft.Icons.CURRENCY_BITCOIN,
```

with:

```python
    host.controls = [empty_state("Refresh the crypto sheet", "Kimchi premium, perpetual funding as carry, GARCH-t on Bitcoin, "
                                 "the ETH/BTC test and the weekday table, all from keyless Upbit and Binance data; Upbit "
                                 "holdings when a read-only key is set.", icon=ft.Icons.CURRENCY_BITCOIN,
```

4n. `ui/crypto_page.py` the section subtitle, L225. Replace:

```python
        section("Crypto", subtitle="Kimchi premium, funding carry, regime, GARCH-t on Bitcoin — read-only."),
```

with:

```python
        section("Crypto", subtitle="Kimchi premium, funding carry, GARCH-t on Bitcoin — read-only."),
```

- [ ] **Step 5: Run the page self-check and confirm only the analytics assertion still fails**

Run: `python -c "import runpy, sys; sys.path.insert(0, '.'); runpy.run_path('ui/crypto_page.py', run_name='__main__')"` (about 1 minute)

Expected: an `AssertionError` with a traceback at `ui/crypto_page.py`, line 218 (`assert not any(hasattr(CA, k) ...`). The page itself no longer touches the regime; `core/crypto/analytics.py` still defines it.

- [ ] **Step 6: Remove the regime from `core/crypto/analytics.py`**

6a. `core/crypto/analytics.py` docstring, L1-4. Replace:

```python
"""Crypto analytics on keyless Upbit / Binance data: the kimchi premium, funding
as carry, a six-component market-regime score, the ETH/BTC ratio test, the
weekday table, and an out-of-sample scorecard for the app's GARCH(1,1)-t on
Bitcoin. Nothing here trades; every number carries its sample size.
```

with:

```python
"""Crypto analytics on keyless Upbit / Binance data: the kimchi premium, funding
as carry, the ETH/BTC ratio test, the weekday table, and an out-of-sample
scorecard for the app's GARCH(1,1)-t on Bitcoin. Nothing here trades; every
number carries its sample size.
```

6b. `core/crypto/analytics.py` docstring, L15-21. Delete:

```python
  regime_score        the six components of the crypto-regime-analyzer skill
                      (trend 25 %, alt breadth 20 %, dominance 15 %, funding
                      15 %, drawdown & vol 15 %, thrust 10 %) re-authored with
                      explicit thresholds; the skill itself says its bands are
                      "heuristic descriptive bands, not validated allocation
                      rules", and candidate C6's gate decides whether the
                      posture line ships.
```

6c. `core/crypto/analytics.py` the "Regime score" block (L171-280: from the last line of `funding_carry` through the "ETH/BTC and weekday" banner title). Replace:

```python
                        bottom_decile_fwd30=float(bot.mean()) if bot.size else float("nan"), bootstrap_p=p, n=n)


# --------------------------------------------------------------------------- #
# Regime score
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RegimeComponent:
    key: str
    label: str
    weight: float
    score: Optional[float]          # 0–100, None when unavailable
    signal: str


@dataclass(frozen=True)
class RegimeScore:
    score: float
    zone: str                       # RISK_ON | NEUTRAL | RISK_OFF
    components: tuple[RegimeComponent, ...]
    effective_weights: dict[str, float]
    as_of: str
    note: str = ("Heuristic descriptive bands re-authored from the crypto-regime-analyzer skill; not validated "
                 "allocation rules until candidate C6 passes its gate.")


def _sma(x: np.ndarray, n: int) -> float:
    return float(np.mean(x[-n:])) if x.size >= n else float("nan")


def regime_score(btc: np.ndarray, majors: dict[str, np.ndarray], *, funding_ann_pct: Optional[float] = None,
                 dominance_30d_change: Optional[float] = None, as_of: str = "") -> RegimeScore:
    """`btc` and each major: daily closes (≥ 200). Components with missing
    inputs are dropped and their weight redistributed proportionally."""
    comps: list[RegimeComponent] = []
    p = float(btc[-1])
    s50, s200 = _sma(btc, 50), _sma(btc, 200)
    slope200 = (s200 / _sma(btc[:-20], 200) - 1.0) if btc.size >= 220 else float("nan")
    if math.isfinite(s200):
        if p > s50 > s200 and slope200 > 0:
            sc, sig = 100.0, "price above a rising 50/200 stack"
        elif p > s200 and p > s50:
            sc, sig = 75.0, "price above both averages, 50 below 200"
        elif p > s200 or p > s50:
            sc, sig = 45.0, "price above one average only"
        elif p < s50 < s200 and slope200 < 0:
            sc, sig = 0.0, "price below a falling 50/200 stack"
        else:
            sc, sig = 20.0, "price below both averages"
        comps.append(RegimeComponent("trend", "BTC trend structure", 0.25, sc, sig))
    else:
        comps.append(RegimeComponent("trend", "BTC trend structure", 0.25, None, "insufficient history"))
    above200 = [float(x[-1]) > _sma(x, 200) for x in majors.values() if x.size >= 200]
    above50 = [float(x[-1]) > _sma(x, 50) for x in majors.values() if x.size >= 50]
    if above200:
        breadth = 100.0 * np.mean(above200)
        bonus = 10.0 if above50 and np.mean(above50) > 0.5 else 0.0
        comps.append(RegimeComponent("breadth", "Alt breadth (above 200-DMA)", 0.20, min(100.0, breadth + bonus),
                                     f"{np.mean(above200):.0%} of {len(above200)} majors above their 200-DMA"))
    else:
        comps.append(RegimeComponent("breadth", "Alt breadth (above 200-DMA)", 0.20, None, "no major with 200 sessions"))
    if dominance_30d_change is not None and math.isfinite(s200):
        up = p > s200
        if up:
            sc, sig = (60.0, "dominance rising in an uptrend: BTC-led") if dominance_30d_change > 0 else (85.0, "dominance falling in an uptrend: broad participation")
        else:
            sc, sig = (30.0, "dominance rising in a downtrend: flight to BTC") if dominance_30d_change > 0 else (10.0, "dominance falling in a downtrend: broad liquidation")
        comps.append(RegimeComponent("dominance", "BTC dominance direction", 0.15, sc, sig))
    else:
        comps.append(RegimeComponent("dominance", "BTC dominance direction", 0.15, None, "no dominance history yet (accumulates daily)"))
    if funding_ann_pct is not None and math.isfinite(funding_ann_pct):
        a = abs(funding_ann_pct)
        if a > 30:
            sc, sig = 20.0, f"funding {funding_ann_pct:+.0f} %/yr: leverage crowded"
        elif a > 10:
            sc, sig = 50.0, f"funding {funding_ann_pct:+.0f} %/yr: elevated"
        else:
            sc, sig = 80.0, f"funding {funding_ann_pct:+.0f} %/yr: sane"
        comps.append(RegimeComponent("funding", "Perpetual funding", 0.15, sc, sig))
    else:
        comps.append(RegimeComponent("funding", "Perpetual funding", 0.15, None, "funding unavailable"))
    if btc.size >= 250:
        dd = 1.0 - p / float(np.max(btc[-365:]))
        r = np.diff(np.log(btc[-366:]))
        rv = np.array([np.std(r[i - 30:i]) for i in range(30, r.size)]) * math.sqrt(CRYPTO_DAYS)
        vol_pct = float(np.mean(rv <= rv[-1])) if rv.size else 0.5
        sc = 90.0 if dd < 0.10 else 70.0 if dd < 0.25 else 40.0 if dd < 0.50 else 15.0
        if vol_pct > 0.9:
            sc = max(0.0, sc - 20.0)
        comps.append(RegimeComponent("drawdown", "Drawdown & volatility position", 0.15, sc,
                                     f"{dd:.0%} below the 1-year high; 30-day vol at the {vol_pct:.0%} percentile"))
    else:
        comps.append(RegimeComponent("drawdown", "Drawdown & volatility position", 0.15, None, "insufficient history"))
    pos30 = [float(x[-1]) > float(x[-31]) for x in list(majors.values()) + [btc] if x.size >= 31]
    if pos30:
        comps.append(RegimeComponent("thrust", "30-day momentum thrust", 0.10, 100.0 * float(np.mean(pos30)),
                                     f"{np.mean(pos30):.0%} of the universe up over 30 days"))
    else:
        comps.append(RegimeComponent("thrust", "30-day momentum thrust", 0.10, None, "insufficient history"))
    live = [c for c in comps if c.score is not None]
    wsum = sum(c.weight for c in live) or 1.0
    eff = {c.key: c.weight / wsum for c in live}
    score = float(sum(c.score * eff[c.key] for c in live)) if live else float("nan")
    zone = "RISK_ON" if score >= 80 else "RISK_OFF" if score < 40 else "NEUTRAL"
    return RegimeScore(score=score, zone=zone, components=tuple(comps), effective_weights=eff,
                       as_of=as_of or date.today().isoformat())


# --------------------------------------------------------------------------- #
# ETH/BTC and weekday
```

with:

```python
                        bottom_decile_fwd30=float(bot.mean()) if bot.size else float("nan"), bootstrap_p=p, n=n)


# --------------------------------------------------------------------------- #
# ETH/BTC and weekday
```

`Optional`, `date`, `field` and `math` are all still used (by `garch_scorecard`, `weekday_table`, the dataclasses and the self-check), so the imports at L36-45 stay.

6d. `core/crypto/analytics.py` the self-check, L430-435: only the six regime lines go. L429 `majors = ...` stays, because L436 `eth_btc_test` reads `majors["ETH"]`. Delete:

```python
    rs = regime_score(us[-400:], majors, funding_ann_pct=8.0, dominance_30d_change=-0.01)
    assert 0 <= rs.score <= 100 and rs.zone in ("RISK_ON", "NEUTRAL", "RISK_OFF") and abs(sum(rs.effective_weights.values()) - 1) < 1e-9
    rs2 = regime_score(us[-400:], majors)
    assert rs2.components[2].score is None and rs2.components[3].score is None and abs(sum(rs2.effective_weights.values()) - 1) < 1e-9
    down = 100 * np.exp(np.cumsum(rng.normal(-0.004, 0.03, 400)))
    assert regime_score(down, {"ETH": down}).score < regime_score(100 * np.exp(np.cumsum(rng.normal(0.004, 0.02, 400))), {"ETH": majors["ETH"]}).score
```

- [ ] **Step 7: Run the expansion suite and confirm it passes**

Run: `python tests/run_all.py --suite expansion` (about 2 minutes)

Expected:
- every row PASS, including `PASS expansion/selfcheck_crypto_analytics` and `PASS expansion/selfcheck_crypto_page`;
- the summary `20/20 passed, 0 failed, 0 not run`, and exit code 0.

- [ ] **Step 8: Confirm that `weekday_table` is unaffected by the shifted rng stream**

Deleting L434-435 removes two 400-draw `rng.normal` calls. The self-check's `rng.random(n)` volume draw for `weekday_table` (L438) therefore reads a later part of the `default_rng(4)` stream. `eth_btc_test` (whose inputs are drawn before L430) and `garch_scorecard` (its own `seed=3`) are unaffected.

Run:

```bash
python -c "import runpy, sys; sys.path.insert(0, '.'); g = runpy.run_path('core/crypto/analytics.py', run_name='__main__'); wt = g['wt']; print(len(wt['rows']), round(wt['weekend_volume_ratio'], 4), '%.2e' % wt['weekend_volume_p'], g['eb']['n'], round(float(g['sc'].hits95.mean()), 4))"
```

Expected: `ok`, then `7 0.4831 1.37e-90 400 0.0613`.
- At HEAD the same values were `7 0.5069 1.35e-78 400 0.0613`.
- The assertion at L439 needs 7 rows, a ratio below 1.0 and p below 0.01, so it holds with a wide margin.
- The page's synthetic weekday table (Step 4c shifts its `volume` draw) is asserted only for 7 rows, which Step 7 confirmed.

- [ ] **Step 9: Update the README crypto paragraph and add the dated docs notes**

`README.md` L215-216 (CRLF; keep it). Replace:

```markdown
a bootstrap; a six-component regime score whose missing components redistribute
their weight; GARCH(1,1)-t on bitcoin with its out-of-sample verdict and the
```

with:

```markdown
a bootstrap; GARCH(1,1)-t on bitcoin with its out-of-sample verdict and the
```

`docs/ASSET_EXPANSION_SPEC.md` L177. Replace:

```markdown
| `core/crypto/analytics.py` | kimchi premium, funding carry, regime score, ETH/BTC, weekday, GARCH / GJR / skew-t scorecard | `core.quant.garch`, `validate` |
```

with:

```markdown
| `core/crypto/analytics.py` | kimchi premium, funding carry, ETH/BTC, weekday, GARCH / GJR / skew-t scorecard (the regime score moved to TRADEGEN on 2026-10-23) | `core.quant.garch`, `validate` |
```

`docs/build_expansion_primer.py` L616 (CRLF; keep it; a comment inside the paragraph list, so the source no longer presents the regime score as current). Replace:

```python
            "<b>Regime score</b>: six components (trend, funding, open interest, the premium, realised vol, breadth) each "
```

with:

```python
            # 2026-10-23: the regime score moved to TRADEGEN (split spec 4.1 A2); the built PDF predates this.
            "<b>Regime score</b>: six components (trend, funding, open interest, the premium, realised vol, breadth) each "
```

`docs/build_expansion_primer.py` L662. Replace:

```python
        ["Crypto", "kimchi premium, funding carry, regime score, GARCH-t on bitcoin with its verdict, ETH/BTC, weekday table, "
```

with:

```python
        # 2026-10-23: the regime score moved to TRADEGEN (split spec 4.1 A2); the built PDF predates this and still lists it.
        ["Crypto", "kimchi premium, funding carry, GARCH-t on bitcoin with its verdict, ETH/BTC, weekday table, "
```

Run: `python -c "import ast; ast.parse(open('docs/build_expansion_primer.py', encoding='utf-8').read()); print('parses')"`

Expected: `parses`. Do not run `docs/build_expansion_primer.py`.

- [ ] **Step 10: Check line endings, scope and leftovers**

```bash
git ls-files --eol -- core/crypto/analytics.py ui/crypto_page.py tests/expansion_acceptance.py docs/ASSET_EXPANSION_SPEC.md README.md docs/build_expansion_primer.py | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'
git diff --numstat
git diff --stat HEAD -- paper_live grokteam core/engine
grep -rn "regime_score\|RegimeScore\|RegimeComponent\|MAJORS" core ui tests --include=*.py
```

Expected:
- the `awk` line prints nothing;
- `git diff --numstat` shows, in git's path order (added, deleted):
  - `1 2 README.md`
  - `3 121 core/crypto/analytics.py`
  - `1 1 docs/ASSET_EXPANSION_SPEC.md`
  - `3 1 docs/build_expansion_primer.py`
  - a `qa/acceptance_results.json` row, from Step 7's run
  - `1 0 tests/expansion_acceptance.py`
  - `19 34 ui/crypto_page.py`
- The `paper_live grokteam core/engine` diff is empty.
- The grep prints only `ui/crypto_page.py:217` (`"MAJORS" not in globals()`) and `ui/crypto_page.py:218` (the `hasattr(CA, k)` assertion).

- [ ] **Step 11: Run the full suite and compare test identities with Step 1**

Run: `python tests/run_all.py` (about 12 minutes). Expected last line: `696/817 passed, 0 failed, 121 not run; ...`.

Then:

```bash
python - <<'EOF'
import json, os, tempfile
from collections import Counter
old = {r["test"]: r["status"] for r in json.load(open(os.path.join(tempfile.gettempdir(), "quantgen_task3_before.json"), encoding="utf-8"))}
new = {r["test"]: r["status"] for r in json.load(open("qa/acceptance_results.json", encoding="utf-8"))}
print("before", len(old), dict(Counter(old.values())))
print("after ", len(new), dict(Counter(new.values())))
print("added  ", sorted(set(new) - set(old)))
print("removed", sorted(set(old) - set(new)))
print("changed", sorted((k, old[k], new[k]) for k in set(old) & set(new) if old[k] != new[k]))
assert set(new) - set(old) == {"expansion/selfcheck_crypto_page"} and not set(old) - set(new)
assert all(old[k] == new[k] for k in old) and new["expansion/selfcheck_crypto_page"] == "PASS"
EOF
```

Expected:
- `before 816 {'PASS': 695, 'NOT_RUN': 121}` and `after  817 {'PASS': 696, 'NOT_RUN': 121}`;
- `added   ['expansion/selfcheck_crypto_page']`, `removed []` and `changed []`;
- no assertion error.

If any status changed, stop and investigate before committing. This change touches only crypto files and docs text.

- [ ] **Step 12: Commit**

```bash
git add core/crypto/analytics.py ui/crypto_page.py tests/expansion_acceptance.py README.md docs/ASSET_EXPANSION_SPEC.md docs/build_expansion_primer.py qa/acceptance_results.json
git status --short
git commit -F - <<'EOF'
A2: crypto regime score out

Remove regime_score, RegimeComponent, RegimeScore and _sma from
core/crypto/analytics.py (docstring, block and the regime self-check
lines), and every regime use in ui/crypto_page.py: the MAJORS universe
and its 8 Binance calls a load, the analyze key, the narrative
sentence, the payload key, the tile, the components chart and the page
text. The synthetic ETH series is unchanged.

Register the Crypto page self-check as expansion/selfcheck_crypto_page;
it now asserts the regime is gone. weekday_table's self-check assertion
holds on the shifted rng stream (ratio 0.48, p 1e-90).

README crypto paragraph updated; dated moved-to-TRADEGEN notes in
docs/ASSET_EXPANSION_SPEC.md and docs/build_expansion_primer.py (the
regime paragraph and the summary row). The built primer PDF stays as an
artifact.

Suite: 696/817 PASS, 0 FAIL, 121 NOT_RUN.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

Expected: `git status --short` before the commit lists exactly the seven staged paths (`M `), and the commit succeeds.

---

### Task 4: A3: weekly FICC note in an academic register, trade-idea text out of the AI prompts (spec 4.1 A3, D3)

One change group, one commit (spec 4.1), with the full suite before (Task 3's committed run) and after (Step 16).

**Files:**
- Modify: `core/ficc/insights.py` (LF)
  - module docstring L11-13
  - `narrate_weekly_strategy`, L409-497 at HEAD. The spec says L409-490, but the function body runs to L497. It is replaced, and three private helpers are inserted just before it.
  - `REPORT_PROMPTS` entries L541-556
  - `report_prompt` docstring L561
  - self-check comment L683 and assertions L691-696
- Modify: `core/quant/insights.py` (CRLF): `_SYSTEM` L263-280. The spec says L263-279, but the closing paren is on L280.
- Modify: `ui/macro_page.py` (CRLF): docstring L6 and the `_REPORTS` row L51 (the button title; the kind key `weekly_fi_fx_strategy` stays, because tests and `report_prompt` use it).
- Modify: `core/ficc/macro.py` (LF): docstring L2 (the note's name).
- Modify: `tests/ficc_acceptance.py` (LF):
  - L662-665, in `test_weekly_strategy_states_its_views`
  - a new test inserted after L665
  - L668-670, in `test_report_prompt_and_deep_analysis_degrade_without_network`
  - L744-746 and L758-760, in `test_weekly_strategy_names_a_positive_carry_long`, which is renamed
- Modify: `README.md` (CRLF): L14-15, L57-59, and L671-679 inside the block L669-679 (the spec says L670-678). Every README edit is anchored on quoted text, so a line shift from another Phase 1 task does not matter.
- Modify: `qa/acceptance_results.json`, which every suite run rewrites.
- Test: `tests/ficc_acceptance.py`, plus the module self-checks `python -m core.ficc.insights` and `python -m ui.macro_page`, then the full suite.

Use the Edit tool for every change (it keeps each file's own EOL). Never rewrite a whole file, and never run a formatter.

**Interfaces:**
- Consumes (unchanged, at HEAD):
  - `core.ficc.macro.MacroSheet`:
    - `.row(id) -> MacroRow | None`, where a row has `.last`, `.unit`, `.z_1y` (z against the last 252 observations, `macro._Z_WINDOW`), `.chg_1w` (5 obs) and `.chg_1m` (21 obs);
    - `.regime.summary`, `.regime.curve` (a 20-session `curves._regime` label) and `.regime.dollar` (strong/weak beyond ±1.5% over 1m, range otherwise);
    - `.synthetic_ids` and `.as_of`.
  - `core.ficc.macro.CURVE_REGIMES`.
  - `core.ficc.curves.CurveReport` (frozen dataclass): `.descriptors["level"|"2s10s"|"2s5s10s_fly"|"5y5y"]`, `.changes["2s10s"]`, `.regime`, `.lookback`.
  - `core.ficc.fx.CarryRow` (frozen dataclass): `.ccy`, `.carry` (r_ccy − r_usd), `.carry_to_vol`, `.vol_3m` (annualised 63-session realised vol), `.mom_3m`, `.score`.
  - The module helpers `_level`, `_chg`, `_pct`, `_bp` and `BP`.
  - Task 3's committed full results (817 rows: 696 PASS) as the "before" run.
- Produces:
  - `narrate_weekly_strategy(sheet: MacroSheet, curve_report: CurveReport | None = None, carry_rows: list[CarryRow] | None = None) -> str`. The signature is unchanged and the text is new:
    - it starts `"Weekly rates and FX note, data to {as_of}."`;
    - it keeps the `Duration:`, `Curve:`, `FX:` and `Carry:` prefixes;
    - it ends with `"This note is descriptive and makes no recommendation."`.
  - New private helpers: `_CURVE_MOVE: dict[str, str]`, `_curve_move(regime: str, n: int) -> str` and `_sd(z: float) -> str`.
  - `REPORT_PROMPTS` keeps the keys `"daily_market_commentary"` and `"weekly_fi_fx_strategy"`.
  - These signatures are unchanged: `report_prompt(kind: str) -> str` and `deep_analysis(kind: str, payload: dict, *, question: str = "") -> Analysis`.
  - `core.quant.insights._SYSTEM: str` gets a new academic-analyst persona.
  - `ui.macro_page._REPORTS["weekly"] == ("Weekly rates and FX note", "weekly_fi_fx_strategy")`.
  - Test identity change in the ficc suite (56 tests become 57):
    - removed: `ficc/test_weekly_strategy_names_a_positive_carry_long`;
    - added: `ficc/test_weekly_strategy_ranks_positive_carry_first`, which is the rename;
    - added: `ficc/test_weekly_note_has_no_position_language`.
  - Full run after this task: 697/818 passed, 0 failed, 121 not run.

- [ ] **Step 1: Confirm the starting state and the line endings**

```bash
git status --short
python -c "import json, subprocess, collections; r = json.loads(subprocess.run(['git', 'show', 'HEAD:qa/acceptance_results.json'], capture_output=True, check=True).stdout.decode('utf-8')); c = collections.Counter(x['status'] for x in r); print(len(r), dict(c)); assert (len(r), c['PASS']) == (817, 696), 'HEAD does not carry the Task 3 full run'"
git ls-files --eol core/ficc/insights.py core/quant/insights.py tests/ficc_acceptance.py README.md ui/macro_page.py core/ficc/macro.py
```
Expected:
- `git status` prints nothing;
- `817 {'PASS': 696, 'NOT_RUN': 121}` (the "before" run Step 16 compares with);
- the EOL listing:
```
i/crlf  w/crlf  attr/-text            	README.md
i/lf    w/lf    attr/-text            	core/ficc/insights.py
i/lf    w/lf    attr/-text            	core/ficc/macro.py
i/crlf  w/crlf  attr/-text            	core/quant/insights.py
i/lf    w/lf    attr/-text            	tests/ficc_acceptance.py
i/crlf  w/crlf  attr/-text            	ui/macro_page.py
```

- [ ] **Step 2: Write the failing weekly-note tests in `tests/ficc_acceptance.py`**

`tests/ficc_acceptance.py` Edit 2a (L663-665). Replace:
```python
    assert "Duration:" in t and "Curve:" in t and "FX:" in t and "Carry:" in t
    assert f"{_report().descriptors['2s10s'] / BP:+.0f}bp" in t
    _clean(insights.narrate_weekly_strategy(_sheet()))
```
with:
```python
    assert "Duration:" in t and "Curve:" in t and "FX:" in t and "Carry:" in t
    assert f"{_report().descriptors['2s10s'] / BP:+.0f}bp" in t
    assert "Litterman & Scheinkman (1991)" in t and "Koijen, Moskowitz, Pedersen & Vrugt (2018)" in t
    assert "trailing 252-session mean" in t and "change over the week (5 sessions)" in t
    assert t.endswith("This note is descriptive and makes no recommendation."), t[-200:]
    _clean(insights.narrate_weekly_strategy(_sheet()))


def test_weekly_note_has_no_position_language():
    """The weekly note is an academic descriptive read (spec 4.1 A3): no position
    word appears as a whole word, on any branch of the function, and the Macro
    page button names it a note."""
    import dataclasses
    import re
    from pathlib import Path
    words = re.compile(r"\b(long|short|run|fund|funded|size|cut|entry|lean|fade|buy|sell)\b",
                       re.IGNORECASE)
    sheet, rows = _sheet(), fx.carry_table(*_carry_inputs())
    # every carry negative, and the lowest carry-to-vol given the top score: the
    # no-positive-carry branch and the carry-plus-momentum sentence both render.
    negative = [dataclasses.replace(r, carry=c, carry_to_vol=c / r.vol_3m)
                for r in rows for c in [-abs(r.carry) - 0.001]]
    worst = min(negative, key=lambda r: r.carry_to_vol)
    negative = [dataclasses.replace(r, score=99.0) if r is worst else r for r in negative]
    notes = [insights.narrate_weekly_strategy(sheet),
             insights.narrate_weekly_strategy(sheet, carry_rows=negative)]
    notes += [insights.narrate_weekly_strategy(sheet, dataclasses.replace(_report(), regime=g), rows)
              for g in macro.CURVE_REGIMES]
    assert "no currency has positive carry against USD" in notes[1], notes[1]
    assert "carry-plus-momentum score" in notes[1], notes[1]
    for text in notes:
        hits = words.findall(text)
        assert not hits, f"position language {sorted(set(hits))}: {text}"
    page = (Path(__file__).resolve().parents[1] / "ui" / "macro_page.py").read_text(encoding="utf-8")
    assert '"weekly": ("Weekly rates and FX note", "weekly_fi_fx_strategy")' in page   # the button names a note
```
(`macro`, `fx` and `insights` are already imported at L23. The two blank lines that already follow L665 stay between the new test and `test_report_prompt_and_deep_analysis_degrade_without_network`.)

`tests/ficc_acceptance.py` Edit 2b (L744-746). Replace:
```python
def test_weekly_strategy_names_a_positive_carry_long():
    """The carry line must be a carry trade: whenever some currency earns positive
    carry the named long has positive carry, whatever the momentum score says."""
```
with:
```python
def test_weekly_strategy_ranks_positive_carry_first():
    """The carry line names, whenever some currency earns positive carry, the highest
    carry-to-volatility among the positive-carry currencies, whatever the momentum
    score says."""
```

`tests/ficc_acceptance.py` Edit 2c (L758-760). Replace:
```python
        assert f"long {best.ccy}" in text, text[text.index("Carry:"):][:200]
    else:
        assert "no currency in the basket earns positive carry" in text
```
with:
```python
        assert f"among currencies with positive carry is {best.ccy} (" in text, \
            text[text.index("Carry:"):][:400]
    else:
        assert "no currency has positive carry against USD" in text
```

- [ ] **Step 3: Run the ficc suite and confirm the expected failures**

```bash
python tests/run_all.py --suite ficc
```
Expected: 3 FAIL, ending `54/57 passed, 3 failed, 0 not run; ...qa/acceptance_results.json`. The FAIL lines:
- `FAIL ficc/test_weekly_note_has_no_position_language AssertionError: Weekly rates/FX strategy, data to ...`
- `FAIL ficc/test_weekly_strategy_ranks_positive_carry_first AssertionError: Carry: long <CCY> (...) funded in ...`
- `FAIL ficc/test_weekly_strategy_states_its_views AssertionError:`

- [ ] **Step 4: Rewrite `narrate_weekly_strategy` in `core/ficc/insights.py` (L409-497)**

`core/ficc/insights.py` (L409-497, the whole current function). Replace:
```python
def narrate_weekly_strategy(sheet: MacroSheet, curve_report: CurveReport | None = None,
                            carry_rows: list[CarryRow] | None = None) -> str:
    """Sell-side tone: a duration, a curve and an FX view, each hung on a number.
    Rules are deliberately simple and stated with the number that drives them."""
    r = sheet.row
    ten, slope = r("DGS10"), r("T10Y2Y")
    lines = [f"Weekly rates/FX strategy, data to {sheet.as_of}. {sheet.regime.summary}"]

    # Duration: where the 10y sits in its 1y range decides the lean.
    if ten is not None:
        z, lvl, w = ten.z_1y, _level(ten), _chg(ten, "chg_1w")
        if z > 1.0:
            view = (f"Duration: lean long. The 10y at {lvl} is {z:+.1f} sigma above its 1y "
                    f"mean after {w} on the week; the entry is the level, the risk is a "
                    f"rising-breakeven trend (breakevens are currently "
                    f"{sheet.regime.inflation}).")
        elif z < -1.0:
            view = (f"Duration: stay short or underweight. The 10y at {lvl} is {z:+.1f} sigma "
                    f"below its 1y mean ({w} on the week); rallies from here need a risk-off "
                    f"tape to persist; the tape is currently {sheet.regime.risk}.")
        else:
            view = (f"Duration: neutral. The 10y at {lvl} sits {z:+.1f} sigma from its 1y "
                    f"mean ({w} on the week), not enough to pay for a directional position.")
        lines.append(view)

    # Curve: the regime and the level of 2s10s.
    if curve_report is not None:
        s10 = curve_report.descriptors["2s10s"]
        ds = curve_report.changes.get("2s10s", 0.0)
        regime, win = curve_report.regime, f"{curve_report.lookback} sessions"
    elif slope is not None:
        s10, ds = slope.last, (slope.chg_1m or 0.0)
        regime, win = sheet.regime.curve, "a month"
    else:
        s10 = None
    if s10 is not None:
        if "steepener" in regime:
            trade = "run steepeners"
        elif "flattener" in regime:
            trade = "run flatteners"
        else:
            trade = "no curve trade"
        line = (f"Curve: {trade}. 2s10s at {s10 / BP:+.0f}bp has moved {_bp(ds)} over {win}, "
                f"a {regime}")
        if curve_report is not None:
            d = curve_report.descriptors
            term = ("still carries a term premium" if d["5y5y"] > d["level"]
                    else "is priced for cuts")
            line += (f"; 5y5y at {_pct(d['5y5y'])} against a 2y/5y/10y level of "
                     f"{_pct(d['level'])} says the long end {term}")
        lines.append(line + ".")

    # FX: the dollar regime, then the carry ranking if there is one.
    usd = r("DTWEXBGS")
    if usd is not None:
        lean = {"strong": "USD longs against low-yielders",
                "weak": "fading dollar strength into high-carry currencies"
                }.get(sheet.regime.dollar, "range trades rather than trend")
        lines.append(f"FX: the broad dollar is {sheet.regime.dollar} at {_level(usd)} "
                     f"({_chg(usd, 'chg_1m')} over a month, z {usd.z_1y:+.1f}); in a "
                     f"{sheet.regime.risk} tape that favours {lean}.")
    if carry_rows:
        # A carry trade is named by its carry: the long is the best carry-to-vol
        # among positive-carry currencies, the funder the most negative carry.
        # The carry-plus-momentum score is reported beside it, never instead of it.
        by_ctv = sorted(carry_rows, key=lambda x: x.carry_to_vol, reverse=True)
        positive = [x for x in by_ctv if x.carry > 0]
        top = positive[0] if positive else by_ctv[0]
        low = min(carry_rows, key=lambda x: x.carry)
        best = max(carry_rows, key=lambda x: x.score)
        if positive:
            head = (f"Carry: long {top.ccy} ({_pct(top.carry)} p.a., carry-to-vol "
                    f"{top.carry_to_vol:+.2f}) funded in {low.ccy} ({_pct(low.carry)})")
        else:
            head = (f"Carry: no currency in the basket earns positive carry against USD; "
                    f"the least negative is {top.ccy} ({_pct(top.carry)} p.a.), the funder "
                    f"of choice {low.ccy} ({_pct(low.carry)})")
        tail = (f"; size for {top.vol_3m * 100:.0f}% realised vol"
                + (" and cut if risk turns off." if sheet.regime.risk != "risk-off"
                   else ", and keep it small while risk is off."))
        if best.ccy != top.ccy:
            tail += (f" On carry plus momentum the top score is {best.ccy} "
                     f"({best.score:+.2f}, momentum {best.mom_3m * 100:+.1f}%), a trend "
                     f"call rather than a carry call.")
        lines.append(head + tail)
    if sheet.synthetic_ids:
        lines.append(f"Caveat: {len(sheet.synthetic_ids)} inputs are SYNTHETIC; the views "
                     "above describe simulated data.")
    return " ".join(lines)
```
with (the two blank lines before the `# ---...# Structured products` banner stay):
```python
_CURVE_MOVE = {"parallel up": "a parallel rise", "parallel down": "a parallel fall",
               "unchanged": "unchanged"}


def _curve_move(regime: str, n: int) -> str:
    """A `curves._regime` label as a measured move: 'bear steepener' -> 'bear
    steepening over 20 sessions'."""
    tone, _, kind = regime.partition(" ")
    what = (f"{tone} {kind[:-2]}ing" if kind in ("steepener", "flattener")
            else _CURVE_MOVE.get(regime, regime))
    return f"{what} over {n} sessions"


def _sd(z: float) -> str:
    """A 1y z-score in words, with its window (`core.ficc.macro._Z_WINDOW`)."""
    return (f"{abs(z):.1f} standard deviations {'above' if z >= 0 else 'below'} its trailing "
            f"252-session mean")


def narrate_weekly_strategy(sheet: MacroSheet, curve_report: CurveReport | None = None,
                            carry_rows: list[CarryRow] | None = None) -> str:
    """Academic descriptive read: formal and third person, each measure stated with
    its definition and window, no position language and no forecast, closing with
    one sentence that the note makes no recommendation. The Duration:/Curve:/FX:/
    Carry: prefixes are kept for the tests and the report layout."""
    r = sheet.row
    ten, slope = r("DGS10"), r("T10Y2Y")
    lines = [f"Weekly rates and FX note, data to {sheet.as_of}. {sheet.regime.summary}"]

    # Duration: the 10y level, its 1y z-score and its 1-week change.
    if ten is not None:
        lines.append(f"Duration: The 10-year Treasury yield stands at {_level(ten)}, "
                     f"{_sd(ten.z_1y)}, following a {_chg(ten, 'chg_1w')} change over the "
                     f"week (5 sessions).")

    # Curve: level, slope and curvature (Litterman & Scheinkman 1991) and the 2s10s regime.
    if curve_report is not None:
        d = curve_report.descriptors
        lines.append(
            f"Curve: On the observable proxies for the level, slope and curvature factors of "
            f"Litterman & Scheinkman (1991), the curve has a level (mean of the 2y, 5y and 10y "
            f"par yields) of {_pct(d['level'])}, a slope (2s10s, 10y minus 2y) of "
            f"{d['2s10s'] / BP:+.0f}bp and a curvature (2s5s10s butterfly, twice the 5y minus "
            f"the 2y and the 10y) of {_bp(d['2s5s10s_fly'])}. The slope changed by "
            f"{_bp(curve_report.changes.get('2s10s'))}, which the 2s10s regime classifies as "
            f"{_curve_move(curve_report.regime, curve_report.lookback)} (bull or bear as "
            f"yields fell or rose, steepening or flattening as 2s10s widened or narrowed, "
            f"each beyond 5bp). The 5y5y forward rate is {_pct(d['5y5y'])}, a measured spread "
            f"of {_bp(d['5y5y'] - d['level'])} to the 2y/5y/10y level.")
    elif slope is not None:
        lines.append(
            f"Curve: The slope of the Treasury curve, measured by 2s10s (10y minus 2y), stands "
            f"at {slope.last / BP:+.0f}bp after a {_chg(slope, 'chg_1m')} change over 21 "
            f"sessions; the 2s10s regime classifies the move as "
            f"{_curve_move(sheet.regime.curve, 20)} (bull or bear as yields fell or rose, "
            f"steepening or flattening as 2s10s widened or narrowed, each beyond 5bp).")

    # FX: the broad dollar by its regime, change and z-score.
    usd = r("DTWEXBGS")
    if usd is not None:
        lines.append(f"FX: The broad trade-weighted dollar index stands at {_level(usd)}, "
                     f"{_chg(usd, 'chg_1m')} over 21 sessions and {_sd(usd.z_1y)}; its regime "
                     f"is classified as {sheet.regime.dollar} (strong or weak for a 21-session "
                     f"change beyond 1.5% in either direction, range otherwise).")

    # Carry: a cross-sectional observation, ranked by carry-to-volatility.
    if carry_rows:
        by_ctv = sorted(carry_rows, key=lambda x: x.carry_to_vol, reverse=True)
        positive = [x for x in by_ctv if x.carry > 0]
        top = positive[0] if positive else by_ctv[0]
        low = min(carry_rows, key=lambda x: x.carry)
        best = max(carry_rows, key=lambda x: x.score)
        line = (f"Carry: Following Koijen, Moskowitz, Pedersen & Vrugt (2018), carry is the "
                f"return earned if the spot rate is unchanged, here the interest-rate "
                f"differential against USD; carry-to-volatility divides it by the annualised "
                f"63-session realised volatility. In the cross-section of {len(carry_rows)} "
                f"currencies against USD, ")
        if positive:
            line += (f"the highest carry-to-volatility among currencies with positive carry is "
                     f"{top.ccy} ({_pct(top.carry)} p.a., carry-to-volatility "
                     f"{top.carry_to_vol:+.2f}, realised volatility {top.vol_3m * 100:.0f}%)")
        else:
            line += (f"no currency has positive carry against USD; the highest "
                     f"carry-to-volatility is {top.ccy} ({_pct(top.carry)} p.a., "
                     f"carry-to-volatility {top.carry_to_vol:+.2f})")
        line += f", and the lowest carry is {low.ccy} ({_pct(low.carry)} p.a.)."
        if best.ccy != top.ccy:
            line += (f" On the composite carry-plus-momentum score (carry-to-volatility plus "
                     f"the 63-session spot return over volatility) the highest-ranked "
                     f"currency is {best.ccy} ({best.score:+.2f}, 63-session spot return "
                     f"{best.mom_3m * 100:+.1f}%), so the two rankings differ.")
        lines.append(line)
    if sheet.synthetic_ids:
        lines.append(f"Data note: {len(sheet.synthetic_ids)} inputs are SYNTHETIC (simulated), "
                     "so the quantities above describe the generator, not the market.")
    lines.append("This note is descriptive and makes no recommendation.")
    return " ".join(lines)
```
Sample output on the suite's synthetic fixtures (`_sheet()`, `_report()`, carry table), for reference:
- Duration: "Duration: The 10-year Treasury yield stands at 3.80%, 0.1 standard deviations above its trailing 252-session mean, following a -6.7bp change over the week (5 sessions)."
- Curve: "Curve: On the observable proxies for the level, slope and curvature factors of Litterman & Scheinkman (1991), the curve has a level (...) of 5.38%, a slope (...) of -62bp ... classifies as bear flattening over 20 sessions ..."
- Ending: "... This note is descriptive and makes no recommendation."

- [ ] **Step 5: Relabel the weekly report as a note (`ui/macro_page.py` L6 and L51, `core/ficc/macro.py` L2)**

`ui/macro_page.py` docstring (L6). Replace:
```
commentary" and "Weekly rates/FX strategy" swap that card for the report's
```
with:
```
commentary" and "Weekly rates and FX note" swap that card for the report's
```

`ui/macro_page.py` `_REPORTS` (L51). Replace:
```python
    "weekly": ("Weekly rates/FX strategy", "weekly_fi_fx_strategy"),
```
with:
```python
    "weekly": ("Weekly rates and FX note", "weekly_fi_fx_strategy"),
```

`core/ficc/macro.py` docstring (L2). Replace:
```
commentary and the weekly rates/FX strategy note. CONTEXT only (v2.0, section
```
with:
```
commentary and the weekly rates and FX note. CONTEXT only (v2.0, section
```

- [ ] **Step 6: Update the module docstring (`core/ficc/insights.py` L11-13)**

`core/ficc/insights.py` (L11-13). Replace:
```
data; `narrate_weekly_strategy` is a strategist's read of the numbers it is
handed, not a forecast. `report_prompt(kind)` is the format instruction the
Daily/Weekly report buttons append to the operator's question.
```
with:
```
data; `narrate_weekly_strategy` is an academic descriptive read of the numbers
it is handed: no position language, no forecast, no recommendation.
`report_prompt(kind)` is the research-commentary format the Daily/Weekly report
buttons append to the operator's question.
```

- [ ] **Step 7: Update the module self-check (`core/ficc/insights.py` L683, L691-696)**

`core/ficc/insights.py` (L683). Replace:
```python
    # (3) regime labels never supply the direction of a causal sentence.
```
with:
```python
    # (3) the sign of z picks the word; regime labels never become a causal claim.
```
`core/ficc/insights.py` (L691-696). Replace:
```python
    t = narrate_weekly_strategy(_sheet(-1.5, "risk-on", "falling"))
    assert "need a risk-off tape to persist; the tape is currently risk-on" in t
    assert "need risk-on" not in t
    t = narrate_weekly_strategy(_sheet(1.5, "risk-on", "falling"))
    assert "a rising-breakeven trend (breakevens are currently falling)" in t
    assert "falling breakeven trend" not in t
```
with:
```python
    t = narrate_weekly_strategy(_sheet(-1.5, "risk-on", "falling"))
    assert "1.5 standard deviations below its trailing 252-session mean" in t, t
    assert t.endswith("This note is descriptive and makes no recommendation."), t
    t = narrate_weekly_strategy(_sheet(1.5, "risk-on", "falling"))
    assert "1.5 standard deviations above its trailing 252-session mean" in t, t
    assert "tape" not in t and "lean" not in t, t
```
The `_sheet` stub at L684-690 is unchanged.

- [ ] **Step 8: Run the self-check and the ficc suite; expect everything to pass**

```bash
python -m core.ficc.insights
python tests/run_all.py --suite ficc
```
Expected: the first prints `ok`. The second ends `57/57 passed, 0 failed, 0 not run; ...qa/acceptance_results.json`. Do not commit yet: A3 is one commit, after Step 16.

- [ ] **Step 9: Write the failing prompt test (`tests/ficc_acceptance.py`, `test_report_prompt_and_deep_analysis_degrade_without_network`, L668-670 at HEAD)**

`tests/ficc_acceptance.py` (L668-670). Replace:
```python
def test_report_prompt_and_deep_analysis_degrade_without_network():
    assert insights.report_prompt("daily_market_commentary")
    assert insights.report_prompt("weekly_fi_fx_strategy") and insights.report_prompt("bond") == ""
```
with:
```python
def test_report_prompt_and_deep_analysis_degrade_without_network():
    from core.quant.insights import _SYSTEM
    assert insights.report_prompt("daily_market_commentary")
    assert insights.report_prompt("weekly_fi_fx_strategy") and insights.report_prompt("bond") == ""
    for text in (*insights.REPORT_PROMPTS.values(), _SYSTEM):      # research commentary (spec 4.1 A3)
        assert "Positioning" not in text and "trade expression" not in text, text
        assert "do not recommend" in text, text
```

- [ ] **Step 10: Run the suite and confirm the expected failure**

```bash
python tests/run_all.py --suite ficc
```
Expected: it ends `56/57 passed, 1 failed, 0 not run; ...`, with `FAIL ficc/test_report_prompt_and_deep_analysis_degrade_without_network AssertionError: Write a daily market commentary in this format: a one-line headline; ...`.

- [ ] **Step 11: Remove the Positioning clauses from `REPORT_PROMPTS` (`core/ficc/insights.py` L541-556) and reword the `report_prompt` docstring (L561)**

`core/ficc/insights.py` `REPORT_PROMPTS` (L541-556). Replace:
```python
    "daily_market_commentary": (
        "Write a daily market commentary in this format: a one-line headline; a 'Rates' "
        "paragraph (levels in percent, 1d and 1w changes in bp, the curve regime); an 'FX' "
        "paragraph (broad dollar, the majors, the risk regime); then 'Positioning ideas': two "
        "or three trades, each with an entry level, a stop and a target given as numbers taken "
        "from the payload (e.g. a stop one week's move beyond the entry, a target at the 1y "
        "mean implied by the z-score), and the observation that would invalidate it. Date the "
        "note to as_of and flag any ids listed under synthetic_ids as simulated."),
    "weekly_fi_fx_strategy": (
        "Write a weekly fixed-income and FX strategy note in this format: a one-line headline; "
        "'Duration view', 'Curve view' and 'FX view' paragraphs, each anchored to a number in "
        "the payload (10y level and z-score, 2s10s and its change, 5y5y, the dollar's 1m change, "
        "the carry ranking); a 'Positioning' list of two to four trades with entry, stop and "
        "target as numbers derived from the payload and the size rationale; and 'Risks to the "
        "view' naming the data that would flip each call. Date it to as_of and flag any "
        "synthetic_ids as simulated."),
```
with:
```python
    "daily_market_commentary": (
        "Write a daily market commentary as research commentary, in a formal, third-person "
        "register, in this format: a one-line headline; a 'Rates' paragraph (levels in "
        "percent, 1-day and 1-week changes in bp, the 20-session curve classification); an "
        "'FX' paragraph (broad dollar, the majors, the volatility and credit read); then "
        "'Observations': the two or three quantities in the payload that are most extended "
        "against their trailing 252-session distribution, each stated with its definition "
        "and window, and the observation that would revise the reading. Describe, do not "
        "recommend: no trades, positions, entry or exit levels, sizing or forecasts. Date the "
        "note to as_of and flag any ids listed under synthetic_ids as simulated."),
    "weekly_fi_fx_strategy": (
        "Write a weekly fixed-income and FX research note in a formal, third-person, "
        "journal-style register, in this format: a one-line headline; 'Duration', 'Curve' and "
        "'FX' paragraphs, each anchored to a number in the payload and stating the measure's "
        "definition and window (the 10y level and its z-score against the trailing "
        "252-session mean, the 1-week change in bp, the level, slope and curvature of the "
        "curve in the sense of Litterman & Scheinkman (1991), the 5y5y forward as a measured "
        "spread to the 2y/5y/10y level, the dollar's 1-month change, the carry-to-volatility "
        "cross-section with carry as defined by Koijen, Moskowitz, Pedersen & Vrugt (2018)); "
        "an 'Interpretation' paragraph on where the measures agree or disagree and which "
        "assumption or window they are most sensitive to; and 'What would revise this "
        "reading', naming the data that would change each description. Describe, do not "
        "recommend: no trades, positions, entry or exit levels, sizing or forecasts. Date it "
        "to as_of and flag any synthetic_ids as simulated."),
```
The word "headline" must appear exactly once in the daily prompt, because self-check L715 asserts `q.count("headline") == 1`; the text above satisfies this.

`core/ficc/insights.py` `report_prompt` docstring (L561). Replace:
```python
    """Format instruction appended to the operator's question for report kinds."""
```
with:
```python
    """Research-commentary format appended to the operator's question for report kinds."""
```
`report_prompt()` and `deep_analysis()` stay; their bodies are unchanged.

- [ ] **Step 12: Change the `_SYSTEM` persona (`core/quant/insights.py` L263-280, CRLF)**

`core/quant/insights.py` `_SYSTEM` (L263-280). Replace:
```python
_SYSTEM = (
    "You are the analysis engine inside QUANTGEN, a personal quantitative "
    "trading application covering equities and FICC: rates, government and "
    "corporate bonds, interest-rate swaps and swaptions, FX spot, forwards and "
    "options, structured notes, and the macro regime. You receive computed "
    "results (Monte Carlo simulations, risk metrics, optimizer output, "
    "technical signals, backtests, yield-curve descriptors, DV01/key-rate "
    "risk, option Greeks, carry tables, macro z-scores) as JSON. Write a "
    "sharp, concrete interpretation for the operator, in the voice of a "
    "sell-side rates/FX strategist writing for a trading desk: what the "
    "numbers jointly imply, where they disagree, what regime or assumption "
    "they are most sensitive to, what the trade expression would be, and "
    "what would invalidate the read. Use only the numbers provided — never "
    "invent data; quote rates in percent and changes in basis points. 3–6 "
    "short paragraphs, no headers, no bullet lists, no disclaimers about "
    "being an AI; the operator knows financial risk is theirs. If the "
    "operator's question asks for a report format, follow that format."
)
```
with:
```python
_SYSTEM = (
    "You are the analysis engine inside QUANTGEN, a quantitative finance "
    "research application covering equities and FICC: rates, government and "
    "corporate bonds, interest-rate swaps and swaptions, FX spot, forwards and "
    "options, structured notes, and the macro regime. You receive computed "
    "results (Monte Carlo simulations, risk metrics, optimizer output, "
    "technical signals, backtests, yield-curve descriptors, DV01/key-rate "
    "risk, option Greeks, carry tables, macro z-scores) as JSON. Write "
    "research commentary in the voice of an academic research analyst, in a "
    "formal, third-person, journal-style register: what the numbers jointly "
    "show, where they disagree, which assumption, estimation window or "
    "regime classification they are most sensitive to, and which "
    "observation would revise the reading. State each measure with its "
    "definition and window when it first appears. Describe; do not "
    "recommend: no trades, positions, entry or exit levels, sizing or "
    "forecasts. Use only the numbers provided — never invent data; quote "
    "rates in percent and changes in basis points. 3–6 short paragraphs, no "
    "headers, no bullet lists, no disclaimers about being an AI. If the "
    "operator's question asks for a report format, follow that format."
)
```
No string is added inside the `_requests.post(...)` call, so the T-RO-01 mutating-HTTP scan is unaffected.

- [ ] **Step 13: Run the self-checks and the suite; expect everything to pass**

```bash
python -m core.ficc.insights
python -m ui.macro_page
python tests/run_all.py --suite ficc
```
Expected: `ok`, then `ok` (the macro page self-check asserts that `report_prompt(kind)` is non-empty for both `_REPORTS` kinds), then `57/57 passed, 0 failed, 0 not run; ...`.

- [ ] **Step 14: Update the README (`README.md`, CRLF)**

`README.md` (L14-15). Replace:
```
treasuries and credit, pricing, structuring, and the weekly rates/FX strategy
read.
```
with:
```
treasuries and credit, pricing, structuring, and the weekly rates and FX
note.
```

`README.md` (L57-59). Replace:
```
**Daily market commentary** and **Weekly rates/FX strategy** — a local
narrative immediately, and the Claude deep read with a strategist's report
format when a key is set.
```
with:
```
**Daily market commentary** and **Weekly rates and FX note** — a local
narrative immediately, and the Claude deep read with a research-commentary
report format when a key is set.
```

`README.md` (L671-679). Replace:
```
   computed upstream. The FICC narratives speak the desk's language: the curve
   regime in basis points, the swaption premium in bp of notional, the carry
   long and its funder with carry-to-vol.
2. **Deep analysis** (with `ANTHROPIC_API_KEY`) — the same structured payload
   goes to the Claude API for a generative read in the voice of a sell-side
   rates/FX strategist: cross-metric tensions, sensitivity, the trade
   expression, what would invalidate the view. The Macro page's two report
   buttons append a report format (headline, rates, FX, positioning with
   levels) to whatever question you attach.
```
with:
```
   computed upstream. The FICC narratives state each measure with its
   definition and window: the curve regime in basis points, the swaption
   premium in bp of notional, the carry cross-section by carry-to-volatility.
   The weekly rates and FX note is an academic descriptive read (level, slope
   and curvature after Litterman & Scheinkman 1991; carry after Koijen,
   Moskowitz, Pedersen & Vrugt 2018) and closes by stating that it makes no
   recommendation.
2. **Deep analysis** (with `ANTHROPIC_API_KEY`) — the same structured payload
   goes to the Claude API for research commentary in the voice of an academic
   research analyst: cross-metric tensions, sensitivity to assumptions and
   windows, what would revise the reading. It describes and does not
   recommend. The Macro page's two report buttons append a report format
   (headline, rates, FX, observations, what would revise the reading) to
   whatever question you attach.
```
Do not touch the README test table (L763-786). Task 5 updates it once, in the last Phase 1 commit; its ficc row goes from 56 to 57 there.

- [ ] **Step 15: Run the repo-wide guards on the changed text**

```bash
python -c "import tests.acceptance as A, tests.macro_m0_harness as H, tests.macro_m6_context as C; A.test_08_no_broker_order_path(); A.test_09_no_account_credentials_requested(); H.test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path(); C.test_ctx_01_static_import_scan_and_positive_controls(); print('guards ok')"
python -c "import tests.macro_ui_components as M; M.test_readme_carries_both_disclaimers_and_no_stale_counts(); print('readme ok')"
git ls-files --eol -- core/ficc/insights.py core/quant/insights.py tests/ficc_acceptance.py README.md ui/macro_page.py core/ficc/macro.py | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'
```
Expected: `guards ok`, then `readme ok`, then nothing from the `awk` line.

- [ ] **Step 16: Full suite (the A3 "after" run) and identity comparison**

No app may run meanwhile. Run (about 11 minutes; it may run in the background):
```bash
python tests/run_all.py
```
Expected last line: `697/818 passed, 0 failed, 121 not run; ...`.

Then, before committing (so `HEAD` is still Task 3's commit):
```bash
python - <<'EOF'
import collections, json, subprocess
before = json.loads(subprocess.run(["git", "show", "HEAD:qa/acceptance_results.json"],
                                   capture_output=True, check=True).stdout.decode("utf-8"))
after = json.load(open("qa/acceptance_results.json", encoding="utf-8"))
b = {r["test"]: r["status"] for r in before}
a = {r["test"]: r["status"] for r in after}
removed, added = sorted(set(b) - set(a)), sorted(set(a) - set(b))
changed = sorted((k, b[k], a[k]) for k in set(a) & set(b) if a[k] != b[k])
print("before", len(b), dict(collections.Counter(b.values())))
print("after ", len(a), dict(collections.Counter(a.values())))
print("removed", removed, "added", added, "changed", changed)
assert removed == ["ficc/test_weekly_strategy_names_a_positive_carry_long"], removed
assert added == ["ficc/test_weekly_note_has_no_position_language",
                 "ficc/test_weekly_strategy_ranks_positive_carry_first"], added
assert not changed and all(a[k] == "PASS" for k in added), (changed, added)
assert (len(a), collections.Counter(a.values())["PASS"]) == (818, 697), len(a)
print("OK: A3 changes exactly the two weekly-note identities")
EOF
```
Expected:
- `before 817 {'PASS': 696, 'NOT_RUN': 121}` and `after  818 {'PASS': 697, 'NOT_RUN': 121}`;
- the `removed`/`added` lists above, `changed []`, then the `OK:` line.

If any status changed, stop and investigate before committing.

- [ ] **Step 17: Commit A3 (one commit), then check that only the intended lines changed**

```bash
git add core/ficc/insights.py core/quant/insights.py ui/macro_page.py core/ficc/macro.py tests/ficc_acceptance.py README.md qa/acceptance_results.json
git status --short
git commit -F - <<'EOF'
A3: weekly FICC note as academic research; no trade ideas in the AI prompts

narrate_weekly_strategy now states each measure with its definition and
window (z against the trailing 252-session mean, 1-week change in bp). It
describes the curve by level, slope and curvature after Litterman &
Scheinkman (1991) and by the 2s10s regime, the 5y5y as a measured spread,
the dollar by regime, change and z, and carry by carry-to-volatility after
Koijen, Moskowitz, Pedersen & Vrugt (2018). No position language; it
closes with a no-recommendation sentence. The Macro page button reads
"Weekly rates and FX note" (kind key unchanged).

REPORT_PROMPTS drop the Positioning clauses (entry, stop, target, size);
report_prompt() and deep_analysis() stay, as research commentary.
core/quant/insights._SYSTEM gets an academic research analyst persona,
and "trade expression" is removed. README follows.

Tests: a new ficc test scans every branch of the note for position words;
test_weekly_strategy_names_a_positive_carry_long is renamed
test_weekly_strategy_ranks_positive_carry_first.
Suite: 697/818 PASS, 0 FAIL, 121 NOT_RUN.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git ls-files --eol core/ficc/insights.py core/quant/insights.py tests/ficc_acceptance.py README.md ui/macro_page.py core/ficc/macro.py
git diff --numstat HEAD~1 HEAD
```
Expected:
- `git status --short` before the commit lists exactly the seven staged paths (`M `);
- the EOL listing is identical to Step 1;
- the numstat over the A3 commit is (measured by applying this task's edits to a scratch clone):
```
18	13	README.md
106	89	core/ficc/insights.py
1	1	core/ficc/macro.py
13	11	core/quant/insights.py
<large>	<large>	qa/acceptance_results.json
43	5	tests/ficc_acceptance.py
2	2	ui/macro_page.py
```
A count near a source file's whole length means its line endings were rewritten. In that case, `git reset --soft HEAD~1`, restore Task 3's version with `git checkout HEAD -- <file>`, redo that file's edits with the Edit tool, rerun Step 16 and commit again.

---

### Task 5: A4 identity, A5 GrokBot labelling, README test table and Phase 1 verification

Task 5 makes two commits, because the spec puts one commit on each group:
- the **A4 commit** carries the identity text (including the README intro's "recommends" sentence), the split note, the Research papers section and the A4 test;
- the **A5 commit** carries the GrokBot section, the A5 test, the one README test-table update with the measured totals, and the Phase 1 verification. Spec 4.1 says the table update goes in the last Phase 1 commit, so it rides with A5.

The full suite runs after each group. The "before" run for A4 is Task 4's committed full run.

**Files:**
- Modify: `pyproject.toml` (CRLF) L8 (`description`).
- Modify: `main.py` (CRLF) L1 (first line of the module docstring).
- Modify: `README.md` (CRLF), in these places:
  - L6-9: the "recommends" sentence of the intro (Task 2 left it for this task);
  - L33-35: the identity paragraph, which also gains the split note;
  - a new section inserted before `## Setup` (L749 at HEAD): `## Research papers` (A4), then `## GrokBot: the GROKTEAM-BOOK study of record` (A5);
  - L763: the `--suite` list;
  - L777: the cockpit row, which becomes the safety row;
  - L781: the ficc row (56 becomes 57);
  - L782: the expansion row;
  - L783: the macro row;
  - after L785: a new guard row;
  - L786: the Total row;
  - L809: the `macro_ui_*` row.
- Modify: `tests/macro_ui_components.py` (LF), inserting between L147 (the last line of `test_readme_carries_both_disclaimers_and_no_stale_counts`) and L150 (`if __name__ == "__main__":`).
- Modify: `qa/acceptance_results.json`, rewritten by the two full runs.
- Test: `tests/macro_ui_components.py`. The macro suite discovers it automatically through `tests/macro_acceptance.py::tests()`, so `run_all.py` needs no edit.

**Interfaces:**
- Consumes:
  - **From Task 1:**
    - The annotated tag `studies-of-record-2026-10-23` peels to `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`.
    - `tests/frozen_guard.py::tests() -> list[tuple[str, Callable[[], None]]]` returns **5** tests (clauses a, b, c, and two for d). They are registered in `tests/run_all.py` as suite `guard` (rows `guard/<name>`).
    - The two `macro_m7_ledger` FAILs are fixed, and the test names are unchanged.
  - **From Task 2:**
    - The `cockpit` suite is renamed `safety`, and keeps exactly the 10 function names `test_08_no_broker_order_path`, `test_09_no_account_credentials_requested`, `test_13_…` to `test_18_…`, `test_21_…` and `test_22_…`.
    - Task 2 edited README L4-5, L354, L738-747 and L829-830, and did not touch README L6-9, L33-35, L749-751 or L759-814, `main.py` L1, or `tests/macro_ui_components.py` L138-152.
  - **From Task 3:** one new expansion test, `expansion/selfcheck_crypto_page` (expansion 19 becomes 20).
  - **From Task 4:** ficc 56 becomes 57 (`ficc/test_weekly_strategy_names_a_positive_carry_long` renamed `ficc/test_weekly_strategy_ranks_positive_carry_first`, plus `ficc/test_weekly_note_has_no_position_language`); quant stays 53.
  - **The last commit of Tasks 1-4** tracks a full-run `qa/acceptance_results.json` at 697/818 passed, 0 failed, 121 not run.
- Produces:
  - `tests/macro_ui_components.py::test_readme_and_package_name_the_research_identity() -> None`
  - `tests/macro_ui_components.py::test_readme_labels_the_grokbot_study_with_the_legality_rating() -> None`
  - README anchors that Plan B (Part B) will update when the pipeline exists:
    - `**Split from TRADEGEN (2026-10-23).**`;
    - `## Research papers`, whose sentence "is not built yet, so no paper exists" Plan B replaces;
    - `## GrokBot: the GROKTEAM-BOOK study of record`.
  - Measured Phase 1 totals: 699/820 passed, 0 failed, 121 not run. Of these, 5/5 are `guard` PASS.

- [ ] **Step 1: Confirm the starting state (Tasks 1-4 landed)**

Before every full run in this task, close every QUANTGEN and TRADEGEN app. T-HERM-02 snapshots `~/.nextgen`.

Run (Git Bash):
```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && git status --short && git rev-parse "studies-of-record-2026-10-23^{commit}" && python - <<'EOF'
import collections, json
r = json.load(open("qa/acceptance_results.json", encoding="utf-8"))
c = collections.Counter(x["status"] for x in r)
print(len(r), dict(c))
assert (len(r), c["PASS"], c["FAIL"], c["NOT_RUN"]) == (818, 697, 0, 121), "Tasks 1-4 did not leave a green full run"
EOF
```
Expected:
- `git status` prints nothing;
- the tag line prints `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`;
- the script prints `818 {'PASS': 697, 'NOT_RUN': 121}`.

If the assertion fires while `git status` is clean, Task 4 committed something other than its full run: go back to Task 4 Steps 16-17 and fix that commit before starting this task.

- [ ] **Step 2: Write the failing A4 test**

`tests/macro_ui_components.py` (L147-150). Replace:
```python
    assert "MACRO-R06-US" in text and "REJECT (instrument: US shares via KIS, 50 bp, daily)" in text


if __name__ == "__main__":
```
with:
```python
    assert "MACRO-R06-US" in text and "REJECT (instrument: US shares via KIS, 50 bp, daily)" in text


def test_readme_and_package_name_the_research_identity():
    """Split spec 4.1 A4: pyproject, the main.py docstring and the README intro call QUANTGEN a quantitative
    finance research application; the README carries the split note and the Research papers section."""
    for rel in ("pyproject.toml", "main.py", "README.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "personal quant trading application" not in text, rel
        assert "quantitative finance research application" in text, rel
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "ranks outcomes, and recommends" not in readme
    assert "**Split from TRADEGEN (2026-10-23).**" in readme
    assert "`studies-of-record-2026-10-23`" in readme
    assert "\n## Research papers\n" in readme


if __name__ == "__main__":
```

- [ ] **Step 3: Run it and see it fail**

Run: `cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python -m tests.macro_ui_components`

Expected:
- `FAIL test_readme_and_package_name_the_research_identity AssertionError: pyproject.toml`;
- summary `9/10 passed, 1 failed, 0 not run`;
- exit status 1.

- [ ] **Step 4: Change the identity in pyproject and main.py**

`pyproject.toml` L8. Replace:
```toml
description = "QUANTGEN — personal quant trading application: rates, bonds, FX, structured products, equities, and AI analysis"
```
with:
```toml
description = "QUANTGEN — quantitative finance research application: rates, bonds, FX, structured products, equities, and AI analysis"
```

`main.py` L1. Keep the em dash, because `tests/acceptance.py` documents it. Replace:
```python
"""QUANTGEN — the operator's personal quant trading application.
```
with:
```python
"""QUANTGEN — the operator's quantitative finance research application.
```

- [ ] **Step 5: Rewrite the README intro and add the split note**

`README.md` L6-9 (the intro's claim that QUANTGEN "recommends"; it becomes a description). Replace:
```markdown
**an opinion**. QUANTGEN computes analysis, ranks outcomes, and recommends. On
the macro overlay it recommends only what a frozen gate has passed, and today
nothing has: see
[Macro integration](#macro-integration-quant-council-specification-v20).
```
with:
```markdown
**an opinion**. QUANTGEN computes and validates analysis and ranks outcomes; on
the macro overlay it displays a recommendation only for what a frozen gate has
passed, and today nothing has: see
[Macro integration](#macro-integration-quant-council-specification-v20).
```

`README.md` L33-35. Replace:
```markdown
This is a personal instrument, not a client deliverable. It is not for
commercial distribution, and every trading decision it informs remains the
operator's own.
```
with:
```markdown
QUANTGEN is a quantitative finance research application: models, estimation,
validation, FICC pricing, portfolio theory, backtests and gates. It goes no
further than paper trading, and there is no broker order path in this
repository. It is a personal instrument, not a client deliverable and not for
commercial distribution, and nothing in it is investment advice.

**Split from TRADEGEN (2026-10-23).** On 2026-10-23 this repository was copied
byte for byte to `Desktop/TRADEGEN` (959 files, identical sha256), and the two
programs separated. TRADEGEN is developed in its own session for real-money
trading within Korean law; QUANTGEN keeps the research. Phase 1 of the split
removed the NEXTGEN trading-skills cockpit and the crypto regime score from
QUANTGEN, and rewrote the trade-idea text of the AI prompts and the weekly
FICC note as academic research commentary; TRADEGEN keeps the originals. The
LAZYOWEN accounts leave `paper_live/` only after the H2 holdout readout.
QUANTGEN has been under git since the split (baseline `eacd57d`). The two
frozen studies, the GROKTEAM-BOOK forward look and the paper_live H2 cost-gate
holdout, read out only from a local git clone at the annotated tag
`studies-of-record-2026-10-23` on `eacd57d`, so this main line is free to
change, and `tests/frozen_guard.py` checks the tag and the tagged pins. The
split is specified in
`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`
and mapped file by file in
`research_notes/QUANTGEN TRADEGEN split map/split_map.md`.
```

- [ ] **Step 6: Add the Research papers section**

`README.md` L749-751 (the Setup heading). Replace:
```markdown
## Setup

1. Python 3.10+
```
with:
```markdown
## Research papers

QUANTGEN's research output is a series of formal papers. Each covers its
topic's origin literature, the current state of the art, how QUANTGEN
implements the method, and a reproducible study, and each comes in two
complete editions, English and Korean, typeset in LaTeX (Tectonic 0.17.0).
Papers live in the top-level `papers/` folder, one folder per paper
(`papers/<YYYY-MM-DD-slug>/`), and `papers/INDEX.md` lists only released
papers. The pipeline is specified in section 5 of the split spec and is not
built yet, so no paper exists. Its rules hold from the first paper:

- **Scope before work.** `/quantgen-paper <topic>` writes the scope: the
  research questions, how QUANTGEN implements the method, and an analysis
  protocol that labels every claim exploratory, pre-specified on historical
  data, or confirmatory. Nothing is built or run until the owner approves the
  scope, and a scope file changed after approval stops the write workflow.
- **Every citation is checked.** References are verified against doi.org,
  Crossref or the arXiv API, and each cited claim has a row in `claims.yaml`
  with its locator. An unread or unsupported claim blocks release.
- **Every number has a source.** Study runs are immutable and record their
  inputs, code and environment in `MANIFEST.json`; the text takes numbers only
  from `numbers.json`, and an offline rerun must reproduce them.
- **Three referees.** Claude, GPT (Codex CLI) and Gemini (Antigravity CLI)
  referee each round. A referee that returns nothing leaves the paper
  `REVIEW_INCOMPLETE`, never "no objections".
- **Disclosure and sign-off.** Every paper carries an AI-assistance statement
  and a not-investment-advice note, and is released only after the owner has
  read it and accepts every claim.

A paper that uses a frozen study cites its readout from the tagged snapshot;
it never reruns the study on the main line.

## Setup

1. Python 3.10+
```

- [ ] **Step 7: Run the test and see it pass; check line endings**

Run: `cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python -m tests.macro_ui_components`

Expected: `10/10 passed, 0 failed, 0 not run`, exit 0.

Then run the line-ending check. `README.md`, `main.py` and `pyproject.toml` are CRLF and `tests/macro_ui_components.py` is LF; none of them may be renormalised.
```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && git ls-files --eol -- README.md main.py pyproject.toml tests/macro_ui_components.py | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'; git diff --numstat
```
Expected:
- the `awk` part prints nothing;
- `git diff --numstat` shows `1 1` for `main.py` and for `pyproject.toml`, `58 6` for `README.md` and `14 0` for `tests/macro_ui_components.py`. No whole-file rewrite.

- [ ] **Step 8: Run the full suite (A4 after-run)**

Close every QUANTGEN and TRADEGEN app first. The run takes about 11 minutes, so start it with `run_in_background: true` and wait for the exit notice:
```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python tests/run_all.py > "$TEMP/quantgen_a4_full.log" 2>&1; tail -n 1 "$TEMP/quantgen_a4_full.log"; grep -c "^FAIL" "$TEMP/quantgen_a4_full.log"
```
Expected:
- last line `698/819 passed, 0 failed, 121 not run; C:\Users\whydi\OneDrive\Desktop\QUANTGEN\qa\acceptance_results.json`;
- FAIL count `0`.

- [ ] **Step 9: Commit A4**

```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && git add pyproject.toml main.py README.md tests/macro_ui_components.py qa/acceptance_results.json && git commit -F - <<'EOF'
A4: QUANTGEN is a quantitative finance research application

pyproject, the main.py docstring and the README intro drop "personal quant
trading application"; the intro no longer says QUANTGEN "recommends" (it
displays a recommendation only for what a frozen gate has passed). The
README gains the "Split from TRADEGEN (2026-10-23)" note and a Research
papers section stating the spec-5 rules (pipeline not built yet). A
macro_ui test pins the identity text.
Suite: 698/819 passed, 0 failed, 121 not run.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

- [ ] **Step 10: Write the failing A5 test**

`tests/macro_ui_components.py` (the end of the Step 2 test). Replace:
```python
    assert "\n## Research papers\n" in readme


if __name__ == "__main__":
```
with:
```python
    assert "\n## Research papers\n" in readme


def test_readme_labels_the_grokbot_study_with_the_legality_rating():
    """Split spec 4.1 A5 (D1): the GrokBot section names the study of record, its one look, TRADEGEN's copy as not
    the record, and the Kalshi rating in the legality report's own words."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    _, sep, section = readme.partition("\n## GrokBot: the GROKTEAM-BOOK study of record\n")
    assert sep, "GrokBot section missing"
    section = section.split("\n## ", 1)[0]
    for phrase in ("research-only", "study of record", "2027-02-01", "TRADEGEN's copy is not the record",
                   '"grey, treat as illegal"', "No Korean court or regulator has", "medium-low",
                   "reports/Korean resident trading venue legality.md"):
        assert phrase in section, phrase
    report = (ROOT / "reports" / "Korean resident trading venue legality.md").read_text(encoding="utf-8")
    assert "**Grey, treat as illegal.**" in report, "the legality report no longer carries the Kalshi rating"


if __name__ == "__main__":
```

- [ ] **Step 11: Run it and see it fail**

Run: `cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python -m tests.macro_ui_components`

Expected:
- `FAIL test_readme_labels_the_grokbot_study_with_the_legality_rating AssertionError: GrokBot section missing`;
- summary `10/11 passed, 1 failed, 0 not run`;
- exit status 1.

- [ ] **Step 12: Add the GrokBot section (A5; no code change, nothing under `grokteam/` is touched)**

`README.md` (the Setup heading, now just after the Research papers section). Replace:
```markdown
## Setup

1. Python 3.10+
```
with:
```markdown
## GrokBot: the GROKTEAM-BOOK study of record

`grokteam/` ("GrokBot") is a research-only benchmark of an outside LLM-bot
trading guide, lazyowen's 7-bot Grok guide (published 2026-10-20). Its BOOK
desk paper-replays the guide's BOOK and SIZE rules on Kalshi KXBTCD hourly
bitcoin binaries against a seasonal GARCH-t digital probability. It reads
public market data only, places no order on any venue, and nothing in
`core/`, `data/`, `ui/` or `paper_live/` imports it.

- **The study of record.** QUANTGEN holds the GROKTEAM-BOOK study of record,
  pre-registered and frozen on 2026-10-22. `prereg.check()` pins 10 files,
  the rules, the accounts, the verdict, the model digest and the
  numpy/scipy/pandas/Python versions.
- **One look.** The forward look is taken once, on or after 2027-02-01
  01:00 UTC, by the first full `python -m grokteam.book` run in a local git clone at
  the tag `studies-of-record-2026-10-23`, never on this main line. On the main
  line `grokteam.prereg` reports VOID once a pinned file changes. That is
  expected, because the record runs from the tag.
- **TRADEGEN's copy is not the record.** TRADEGEN keeps a working duplicate.
  Its brief keeps the duplicate's forward events permanently blinded and
  forbids it to take the look or to register trials in QUANTGEN's ledgers.
- **Venue legality.** For a Korean resident, Kalshi's non-sports event
  contracts are rated **"grey, treat as illegal"**. Korea is absent from
  Kalshi's restricted list, but its Member Agreement §VI excludes members for
  whom trading is unlawful where they live, and the police reasoning used
  against Korean Polymarket users fits. No Korean court or regulator has
  ruled on Kalshi, and the confidence is medium-low. Kalshi sports contracts
  are rated illegal. Source:
  `reports/Korean resident trading venue legality.md` (2026-10-23),
  compliance matrix rows 2 and 3. The study is a benchmark, not a reason to
  open a Kalshi account.

## Setup

1. Python 3.10+
```

- [ ] **Step 13: Run the test and see it pass**

Run: `cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python -m tests.macro_ui_components`

Expected: `11/11 passed, 0 failed, 0 not run`, exit 0.

- [ ] **Step 14: Run the full suite (A5 after-run, which is also the Phase 1 verification run)**

Close every QUANTGEN and TRADEGEN app first. Start the run with `run_in_background: true` (about 11 minutes):
```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python tests/run_all.py > "$TEMP/quantgen_phase1_full.log" 2>&1; tail -n 1 "$TEMP/quantgen_phase1_full.log"; grep -c "^FAIL" "$TEMP/quantgen_phase1_full.log"; date +%F
```
Expected:
- `699/820 passed, 0 failed, 121 not run; C:\Users\whydi\OneDrive\Desktop\QUANTGEN\qa\acceptance_results.json`;
- FAIL count `0`;
- the date, which Step 17's Total row uses.

- [ ] **Step 15: Compare test identities and per-suite counts against the baseline**

The baseline is the 848-row result file tracked at `238376a` (the pre-git run: 727 PASS, 0 FAIL, 121 NOT_RUN). The kept cockpit tests are mapped to `safety/`.
```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python - <<'EOF'
import collections, json, subprocess
KEPT = {"test_08_no_broker_order_path", "test_09_no_account_credentials_requested",
        "test_13_settings_page_shows_presence_not_values", "test_14_page_resize_handler_matches_the_flet_api",
        "test_15_views_are_cached_across_navigation", "test_16_every_source_file_is_utf8_readable",
        "test_17_tests_never_read_without_an_encoding", "test_18_eodhd_is_gone_from_the_runtime",
        "test_21_krx_gateway_degrades_with_a_reason", "test_22_krx_status_is_reported_per_provider"}
GUARD = ("test_a_tag_is_annotated_and_peels_to_the_baseline", "test_b_tagged_pins_match_prereg_and_frozen_rule",
         "test_c_no_forward_look_before_it_opens", "test_d_library_versions_match_the_pins_while_a_readout_is_pending",
         "test_d_pending_readouts_retire_only_when_all_three_are_in")
ADDED = {f"guard/{t}" for t in GUARD} | {
    "expansion/selfcheck_crypto_page",
    "ficc/test_weekly_note_has_no_position_language", "ficc/test_weekly_strategy_ranks_positive_carry_first",
    "macro/macro_ui_components/test_readme_and_package_name_the_research_identity",
    "macro/macro_ui_components/test_readme_labels_the_grokbot_study_with_the_legality_rating"}
base = json.loads(subprocess.run(["git", "show", "238376a:qa/acceptance_results.json"], capture_output=True,
                                 check=True).stdout.decode("utf-8"))
now = json.load(open("qa/acceptance_results.json", encoding="utf-8"))


def ident(name):
    suite, _, rest = name.partition("/")
    return f"safety/{rest}" if suite == "cockpit" and rest in KEPT else name


b = {ident(r["test"]): r["status"] for r in base}
n = {r["test"]: r["status"] for r in now}
removed, added = sorted(set(b) - set(n)), sorted(set(n) - set(b))
cockpit_out = [x for x in removed if x.startswith("cockpit/")]
print("removed (not cockpit):", [x for x in removed if x not in cockpit_out])
print("added:", added)
assert len(cockpit_out) == 37, "exactly the 37 deleted cockpit tests leave"
assert set(removed) - set(cockpit_out) == {"ficc/test_weekly_strategy_names_a_positive_carry_long"}, removed
assert set(added) == ADDED, sorted(set(added) ^ ADDED)        # 5 guard + 1 crypto page + 2 ficc + 2 README
changed = sorted((k, b[k], n[k]) for k in set(b) & set(n) if b[k] != n[k])
assert not changed, changed
assert all(n[k] == "PASS" for k in added), [(k, n[k]) for k in added]
per = collections.defaultdict(collections.Counter)
for r in now:
    per[r["test"].split("/", 1)[0]][r["status"]] += 1
got = {k: dict(v) for k, v in per.items()}
expected = {"safety": {"PASS": 10}, "engine": {"PASS": 92}, "ui": {"PASS": 4}, "quant": {"PASS": 53},
            "ficc": {"PASS": 57}, "expansion": {"PASS": 20}, "macro": {"PASS": 420, "NOT_RUN": 121},
            "paper": {"PASS": 21}, "grokteam": {"PASS": 17}, "guard": {"PASS": 5}}
assert got == expected, got
groups = collections.Counter()
for r in now:
    if r["test"].startswith("macro/macro_"):
        groups[("_".join(r["test"].split("/")[1].split("_")[:2]), r["status"])] += 1
table = {"macro_m0": (37, 2), "macro_m1": (68, 14), "macro_m2": (24, 21), "macro_m3": (12, 8),
         "macro_m4": (19, 7), "macro_m5": (25, 13), "macro_m6": (14, 2), "macro_m7": (61, 35),
         "macro_m8": (40, 7), "macro_m9": (17, 8), "macro_tf": (59, 4), "macro_ui": (42, 0)}
sub = {g: (groups[(g, "PASS")], groups[(g, "NOT_RUN")]) for g in table}
assert sub == table, sub
total = collections.Counter(r["status"] for r in now)
assert (len(now), total["PASS"], total["FAIL"], total["NOT_RUN"]) == (820, 699, 0, 121), total
print("Phase 1 measured: 699/820 passed, 0 failed, 121 not run; frozen guard 5/5 PASS")
EOF
```
Expected:
- `removed (not cockpit): ['ficc/test_weekly_strategy_names_a_positive_carry_long']`;
- `added:` lists the 10 names of `ADDED`;
- the last line is `Phase 1 measured: 699/820 passed, 0 failed, 121 not run; frozen guard 5/5 PASS`.

Any assertion error means a regression or a count that differs from Tasks 1-4's stated interface. If one fires, stop: fix the cause, or reconcile with the task that changed the count. Do not edit the README numbers to match.

- [ ] **Step 16: Check that the frozen studies' trees are untouched**

```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && git diff --stat eacd57d -- paper_live grokteam core/engine; git status --porcelain -- paper_live grokteam core/engine; git rev-parse "studies-of-record-2026-10-23^{commit}"
```
Expected:
- the first two commands print nothing (spec 4.1 Phase 1 verification);
- the third prints `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`.

- [ ] **Step 17: Update the README test tables once, with the measured totals**

Seven edits to `README.md`. In the Total row, use the date printed in Step 14. The text below shows `2026-10-23`.

`README.md` L763. Replace:
```
python tests/run_all.py --suite macro    # one suite: cockpit, engine, ui, quant, ficc, expansion, macro, paper or grokteam
```
with:
```
python tests/run_all.py --suite macro    # one suite: safety, engine, ui, quant, ficc, expansion, macro, paper, grokteam or guard
```

`README.md` L777. Replace:
```markdown
| cockpit | `tests/acceptance.py` | The inherited NEXTGEN cockpit, including the read-only scans (no order path, no account credentials requested, Settings shows presence not values) | 47 PASS |
```
with:
```markdown
| safety | `tests/acceptance.py` | The read-only scans kept from the NEXTGEN cockpit suite (no broker order path, no account credentials requested, Settings shows presence not values), the resize handler and the view cache, UTF-8 sources and explicit encodings, EODHD gone from the runtime, the KRX gateway's per-provider status | 10 PASS |
```

`README.md` L781. Replace:
```markdown
| ficc | `tests/ficc_acceptance.py` | Bootstrap round-trips, monotone discount factors, Nelson-Siegel fits, PCA, duration and KRD, carry and roll, scenario convexity, swap and swaption parity, Black ↔ Bachelier, caps and floors, Garman-Kohlhagen, SABR, CIP, the carry backtest, CIR and Hull-White, structured products, narratives, every chart renders | 56 PASS |
```
with:
```markdown
| ficc | `tests/ficc_acceptance.py` | Bootstrap round-trips, monotone discount factors, Nelson-Siegel fits, PCA, duration and KRD, carry and roll, scenario convexity, swap and swaption parity, Black ↔ Bachelier, caps and floors, Garman-Kohlhagen, SABR, CIP, the carry backtest, CIR and Hull-White, structured products, narratives (the weekly rates and FX note free of position language on every branch, the report prompts free of trade ideas), every chart renders | 57 PASS |
```

`README.md` L782. Replace:
```markdown
| expansion | `tests/expansion_acceptance.py` | Fake KIS and crypto transports for every new asset domain, the gate's own checks (a planted edge passes, noise is rejected, the deflated Sharpe orders them, the distribution loop calibrates), the t+1 causality of every strategy family, the five-year rule counted in whole years, the table cost floor and the Strategy Lab's withheld verdict below it, the module self-checks | 19 PASS |
```
with:
```markdown
| expansion | `tests/expansion_acceptance.py` | Fake KIS and crypto transports for every new asset domain, the gate's own checks (a planted edge passes, noise is rejected, the deflated Sharpe orders them, the distribution loop calibrates), the t+1 causality of every strategy family, the five-year rule counted in whole years, the table cost floor and the Strategy Lab's withheld verdict below it, the module self-checks and the Crypto page self-check | 20 PASS |
```

`README.md` L783. Replace:
```markdown
| macro | `tests/macro_acceptance.py` over `tests/macro_*.py` | The v2 build, below | 418 PASS / 121 NOT_RUN |
```
with:
```markdown
| macro | `tests/macro_acceptance.py` over `tests/macro_*.py` | The v2 build, below | 420 PASS / 121 NOT_RUN |
```

`README.md` L786 (inserts the guard row after the grokteam row, L785, which is unchanged). Replace:
```markdown
| **Total** | `tests/run_all.py` | | 727/848 passed, 0 failed, 121 not run (2026-10-22) |
```
with:
```markdown
| guard | `tests/frozen_guard.py` | The frozen-study guard, by git and hashlib only (no `paper_live` or `grokteam` import): the tag `studies-of-record-2026-10-23` peels to `eacd57d`, the tagged tree's pinned files match PREREG and its H2 files match `frozen_rule`, no `FORWARD_LOOK.json` on the main line before 2027-02-01 01:00 UTC, and the numpy/scipy/pandas pins while a readout is pending (with a check of the pending rule itself) | 5 PASS |
| **Total** | `tests/run_all.py` | | 699/820 passed, 0 failed, 121 not run (2026-10-23) |
```

`README.md` L809. Replace:
```markdown
| `macro_ui_*` | The v2 tokens and shared components, the Macro page views, the README claims, the effective rules store | 40 / 0 |
```
with:
```markdown
| `macro_ui_*` | The v2 tokens and shared components, the Macro page views, the README claims (disclaimers, research identity, GrokBot labelling), the effective rules store | 42 / 0 |
```

- [ ] **Step 18: Re-run the README tests and the line-ending check**

`run_module` does not write `qa/acceptance_results.json`, so the Step 14 result file stays the committed one.
```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && python -m tests.macro_ui_components && git ls-files --eol -- README.md tests/macro_ui_components.py | awk 'substr($1,3) != substr($2,3) {print "EOL CHANGED:", $0}'; git status --short
```
Expected:
- `11/11 passed, 0 failed, 0 not run`;
- nothing from the `awk` part;
- `git status` lists only ` M README.md`, ` M qa/acceptance_results.json` and ` M tests/macro_ui_components.py`.

- [ ] **Step 19: Commit A5, the test table and the Phase 1 close**

```bash
cd C:/Users/whydi/OneDrive/Desktop/QUANTGEN && git add README.md tests/macro_ui_components.py qa/acceptance_results.json && git commit -F - <<'EOF'
A5: label GrokBot as the study of record; Phase 1 test table

New README section on the GROKTEAM-BOOK study of record: a research-only
benchmark of an outside LLM-bot guide, one look on or after 2027-02-01 from
the tag, TRADEGEN's copy not the record, and Kalshi non-sports rated "grey,
treat as illegal" per the legality report (no Korean ruling; confidence
medium-low). No code change. The README test tables carry the measured
Phase 1 totals: 699/820 passed, 0 failed, 121 not run; frozen guard 5/5
PASS; ficc 57, expansion 20, macro 420 + 121 NOT_RUN; no diff against
eacd57d in paper_live, grokteam or core/engine.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git status --short && git log --oneline -7
```
Expected:
- `git status` prints nothing;
- the log shows, newest first, the A5, A4, A3, A2, A1 and A0 commits, then the plan commit.

Left out on purpose: no note inside `grokteam/`. The spec says the README is enough, and `grokteam/` must not be edited.

---

## Self-Review

**Spec coverage**

| Spec section | Requirement | Task |
|---|---|---|
| 3.1 point 1 | Annotated tag `studies-of-record-2026-10-23` on `eacd57d` with the Appendix C evidence | Task 1 Steps 5-6 |
| 3.1 point 2 | Readouts run only from a local git clone at the tag (spec rev 4.1: a worktree would write UNVERSIONED ledger rows), with pinned libraries | Not Plan A code (readout runbook). Task 1 creates the tag before the 2026-11-04 alert; anchoring resolved by the clone (Review notes) |
| 3.1 point 3 | Main line free to change; never run `grokteam.book` or the H2 readout on main | Global Constraints ("Never run") |
| 3.1 point 4 (a)-(d), expiry | `tests/frozen_guard.py`, git + hashlib only, NotRun without git | Task 1 Steps 2-6 (5 tests). The warn-only branch of (d) is not built; see Review notes |
| 3.2 | TRADEGEN brief; no concurrent runs | TRADEGEN brief is out of scope; "no app during a full run" is in Global Constraints and every full-run step |
| 3.3 | `repo_anchor` tests follow the repo; `MA.GIT_HASH` / `lab.GIT_HASH` stay `UNVERSIONED`; `* -text`, never renormalise; results file committed per group | Task 1 Steps 7-10; Global Constraints; the EOL check in Tasks 1-5; every commit step |
| 3.4 | test_s4, ledgers, `macro_tf_data` byte tests, T-COUNCIL-DOCS-01, repo-wide guards | Global Constraints; Task 2 Step 11 and Task 5 Step 16 (`git diff` on `core/engine`, `ui/trading_page.py` empty); Task 4 Step 15 (T-RO-01, T-CTX-01, safety 08/09) |
| 3.4 | `_scan_files()` extended to `tools/` and `papers/`; `papers/` in `ORDERS_IMPORTERS_ALLOWED` | Plan B, before its first `tools/` or `papers/` file (see Review notes) |
| 4.1 A0 | Tag, guard, git-state test fixes, suite green | Task 1 |
| 4.1 A1 | Cockpit out: 16 deletions, `__init__`, `main.py`, `config.py` (FMP row), Settings, components, `.env.example`, acceptance split (10 kept / 37 out), suite rename, `macro_m8`, `macro_ui_components`, dangling text, owner `.env` housekeeping | Task 2 |
| 4.1 A1 dangling text | README L3-4, L354, L738-747, L829; `krx_page`; `config` docstring; `macro_acceptance` L8/L116; `ARCHITECTURE_REVIEW` L60 | Task 2 Step 10 (plus `pipeline.py` docstrings and the `macro_daily.yaml` comment) |
| 4.1 A1 dangling text | README L763, L777, L786 | Task 5 Step 17 (the one table update) |
| 4.1 A2 | Regime score out of `analytics.py` and `crypto_page.py`; page self-check registered; README, `ASSET_EXPANSION_SPEC`, primer notes; rng-shift check | Task 3 |
| 4.1 A3 | Positioning clauses out; `report_prompt` / `deep_analysis` kept as research commentary; `narrate_weekly_strategy` academic rewrite; FX line; tests and self-check; `_SYSTEM` persona; README L670-678 | Task 4 (plus the "Weekly rates and FX note" label) |
| 4.1 A4 | Identity in pyproject, `main.py`, README intro; split note; Research papers section | Task 5 Steps 2-9 (plus the README "recommends" sentence) |
| 4.1 A5 | GrokBot README section, legality rating, one look, TRADEGEN copy not the record | Task 5 Steps 10-13, 19 |
| 4.1 Verification | Before/after full runs with identity comparison; frozen_guard passes; no diff against `eacd57d` in `paper_live grokteam core/engine`; README table once at the end | Task 1 Step 11, Task 2 Step 12, Task 3 Step 11, Task 4 Step 16, Task 5 Steps 8, 14-17 |
| Appendix B | T-LEDGER-01 and T-SEL-01 (b) fixes, `gate_ledger.py` untouched | Task 1 Steps 8-9 |
| Appendix C | Evidence in the tag message | Task 1 Step 5 |
| 5A | H2 phone alerts | No task: both scheduled tasks exist and are enabled; Task 1 must land first (Global Constraints, Deadline) |

**Placeholder scan:** searched the plan for `TBD`, `TODO`, `FIXME`, `similar to Task`, `add error handling`, `fill in` and `...` used as an elided code line. None found in any instruction or code block; the only `...` are inside quoted expected-output lines (`...qa\acceptance_results.json`, `AssertionError: Weekly rates/FX strategy, data to ...`), where they stand for printed text that varies by path or data.

**Type and name consistency:** every name a later task consumes is produced by an earlier one with the same spelling: `guard_tests` and suite `guard` (Task 1) appear in Task 2 Step 11, Task 5 Steps 15 and 17; `safety_tests` and suite `safety` (Task 2) in Task 4 Step 15 and Task 5; the five guard test names in Task 1 match Task 5 Step 15's `GUARD`; `expansion/selfcheck_crypto_page` (Task 3) matches Task 5 Step 15; `ficc/test_weekly_note_has_no_position_language` and `ficc/test_weekly_strategy_ranks_positive_carry_first` (Task 4) match Task 4 Step 16 and Task 5 Step 15; the two `macro_ui_components` tests (Task 5) match Step 15's `ADDED`; `_REPORTS["weekly"]` text is the same in Task 4 Steps 2 and 5. Signatures: `build_settings_page(page)`, `navigate(name, *, rebuild=False)`, `quant_provider_status()`, `narrate_weekly_strategy(sheet, curve_report=None, carry_rows=None)`, `report_prompt(kind)` and `deep_analysis(kind, payload, *, question="")` are unchanged or changed in exactly one task and used consistently after it.

**Dry run:** every Replace/Delete/whole-file block of Tasks 1-5 was applied in order, by script, to a scratch clone of `238376a`: all 105 blocks matched exactly once and every edited file kept its HEAD line endings. In that clone (tag created locally) the stated results reproduced: Task 1 Step 4 (2/5, the three quoted FAILs), Task 2 Steps 3 and 8 (both FAIL, then the printed smoke output, 16 NAV entries, 21 Settings controls), Task 3 Steps 3, 5, 7, 8 and 10 (line 233, line 218, 20/20, `7 0.4831 1.37e-90 400 0.0613`, grep lines 217-218), Task 4 Steps 3, 8, 10 and 13 (54/57 with the three FAILs, 57/57, 56/57, `ok ok 57/57`), Task 5 Steps 3, 11 and 13 (9/10, 10/11, 11/11); registered tests 820 with the per-suite counts of Task 5 Step 15; guard 5/5, safety 10/10, ui 4/4; T-RO-01, T-CTX-01, safety 08/09 PASS; the numstat figures quoted in Tasks 1, 3, 4 and 5. The full suite in that clone ended 698/820 with one FAIL, `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`, which fails the same way on an unmodified clone of `238376a`: `macro_daily` takes a cache file's mtime as its retrieval instant (`core/skills/macro_daily.py` L1412), and a fresh clone stamps `docs/asset_expansion/cache/*.csv` with today's date, after the test's fixed clock (2026-10-07). In the repo `yf_SPY.csv` is dated 2026-09-26 and the test passes (it is in the 725 baseline PASS). Counting that row as it runs in the repo, Task 5 Step 15's script passed unchanged on the clone's results: 699/820, guard 5/5, and every per-suite and macro-group count as stated.

## Review notes

Every review issue was checked against the code at `238376a` before it was applied.

1. **Task 5 counts (blocker): correct, applied.** Task 1 registers 5 guard tests and Task 4 takes ficc from 56 to 57, so the ledger is 853 → 816 → 817 → 818 → 819 → 820 (PASS 732 → 695 → 696 → 697 → 698 → 699). Task 5 Step 1 asserts (818, 697, 0, 121); Steps 8 and 14 expect 698/819 and 699/820; Step 15 now asserts the exact added and removed identity sets (10 added, 37 cockpit plus one renamed ficc test removed) instead of a difference of counts; the README guard row says 5 PASS and the Total row 699/820. Its Step 1 fallback no longer loops: a clean tree that fails the assertion sends the executor back to Task 4.
2. **Task 2 line endings (blocker): correct, applied.** `git ls-files --eol` shows `.env.example`, `core/skills/__init__.py`, `ui/krx_page.py`, `tests/macro_acceptance.py`, `tests/macro_m8_pipeline.py`, `tests/macro_ui_components.py` and `docs/ARCHITECTURE_REVIEW.md` are LF (and so are `core/skills/pipeline.py` and `macro_daily.yaml`, which Task 2 now also edits). Only `tests/acceptance.py` is converted to CRLF; the bare-LF check is replaced by a per-file comparison of the working copy's EOL with HEAD's (`git ls-files --eol` `i/` vs `w/`), used in every task.
3. **Task 4 per-group rule (major): correct, applied.** A3 is one commit (Step 17) after a full run and an identity comparison against Task 3's committed run (Step 16, read with `git show HEAD:` before committing, which is the same file the review asked to save). The numstat check is over `HEAD~1`.
4. **README ficc row (major): correct, applied** as the seventh edit of Task 5 Step 17 (57 PASS).
5. **README L6 "recommends" (minor): correct, applied** in Task 5 Step 5 (A4 owns the intro), and pinned by the A4 test (`"ranks outcomes, and recommends" not in readme`).
6. **T-LEDGER-01 in a worktree (minor): correct, applied.** `repo_anchor()` (gate_ledger.py L122-131) reads `<root>/.git/HEAD` and a loose ref file, so the new assertion compares with `(REPO_ROOT / ".git" / "HEAD").is_file()` rather than Appendix B's `.git` `.exists()`; same intent, right in a worktree. Packed refs would also read UNVERSIONED; the test then fails on purpose, because new ledger rows would be unanchored (the comment says so; `gate_ledger.py` is pinned and is not changed). The temp directory is a `TemporaryDirectory`.
7. **Global Constraints (minor): applied**, verbatim, plus four plan-wide lines (EOL table and check, count ledger, the 2026-11-04 deadline, no app during full runs and flush-left code blocks).
8. **Dangling text (minor): correct, applied.** The ARCHITECTURE_REVIEW note lists all eleven modules; `pipeline.py` L12-13 and L73-74 and `macro_daily.yaml` L2 now say the legacy parser moved to TRADEGEN. No test hashes or matches these texts (`macro_m8` loads the YAML with `safe_load`; the T-RO-01 YAML scan finds no forbidden token).
9. **Primer L616 (minor): correct, applied** as a dated comment above the regime paragraph; the PDF is not rebuilt.
10. **Weekly label (minor): correct, applied rather than deferred,** because the owner asked for an academic weekly note: `ui/macro_page.py` L6 and L51, `core/ficc/macro.py` L2 and README L14-15 and L57-59 now say "Weekly rates and FX note"; the kind key `weekly_fi_fx_strategy` is unchanged, and the new ficc test pins the label.

Drafters' open questions, resolved from the code: Task 1 does edit `tests/run_all.py` (L49-50, L64-65, L111), so Task 2's three `run_all.py` edits quote the post-Task-1 text (Edit 3 quotes the whole help line, which ends in `grokteam or guard`). Task 2 runs before Task 4, so Task 4's guard step runs against suite `safety` (its direct imports work either way). Task 2's starting count is 853 (`guard` 5 included). The README L6 sentence belongs to Task 5 (item 5).

Spec gaps found by the review, and what this plan does with them:
- **3.1(d) warn-only branch.** The spec says clause (d) "only warns when a pinned venv is recorded instead" but names no place where that record lives, so the branch cannot be built yet. Task 1 builds the fail branch, the stricter reading, and its docstring says the warn branch is missing. When the owner sets up the pinned readout venv, record it in a tracked file (for example its interpreter path and `pip freeze` in `qa/readout_venv.txt`) and add the warn branch then.
- **Ledger anchoring in a worktree (3.1 point 2).** In a `git worktree`, `.git` is a file, so the pinned `repo_anchor()` returns UNVERSIONED and any ledger row a readout writes there is unanchored. This is a readout-runbook matter, not Plan A code. Two fixes that leave `gate_ledger.py` untouched: run the readouts in a local clone checked out at the tag (`git clone --branch studies-of-record-2026-10-23 <repo> ..\QUANTGEN-studies`: a clone has a `.git` directory and a detached HEAD holding the commit sha, so `repo_anchor()` returns `git:eacd57d…`), or anchor the rows to `external:studies-of-record-2026-10-23`. A clone is still a working tree at the tag, so section 3.1's intent holds; the owner should pick one before 2026-11-04.
- **3.4 order-path scans for `tools/` and `papers/`.** Not in this plan: neither folder exists yet, so there is nothing to scan and no failing test can be written without writing into the repo during a test. It belongs to Plan B's first task, before any `tools/` or `papers/` file lands: add both folders to `tests/macro_m0_harness.py::_scan_files()`, add `papers/` to `ORDERS_IMPORTERS_ALLOWED`, and make the allow-check treat entries ending in `/` as prefixes (today only `ORDERS_IMPORTERS_ALLOWED[0]` is matched as a prefix, at L149).
- **Other narratives with position words.** `narrate_carry` ("top-N long/short carry basket", "Latest basket: long X; short Y") and `narrate_fx_forward` ("Being long EUR earns") are outside A3, which names only `narrate_weekly_strategy`, and the owner's request was for the weekly note. They describe a defined portfolio and a forward's carry rather than recommend a trade, so they are left as they are; the owner can widen D3 to them later, and the weekly-note test would be the model.
- **A4 and README L6:** handled (item 5).
- **File mtimes (found in the dry run, not in the review).** `macro_daily` treats a cache file's mtime as the data's retrieval instant, so any whole-tree `git checkout`, `reset --hard`, `stash` or `clean` that rewrites `docs/asset_expansion/cache/*.csv` makes `test_dry_run_end_to_end_on_the_local_cache` fail. Global Constraints now forbid whole-tree restores; every recovery step in this plan restores single edited files only. Neither `paper_live/` nor `grokteam/` reads an mtime, so a fresh clone or worktree at the tag does not affect the readouts.
- **5A phone alerts.** Checked on 2026-10-23: `h2-holdout-ready-alert` (fires 2026-11-04T00:00Z, 09:00 KST) and `h2-readout-deadline-warning` (fires 2026-12-05T00:00Z) both exist and are enabled. Both read the two `verdict.json` files read-only and tell the owner to read out from the tag, so Task 1 must land before the first one fires. The deadline warning pushes only while H2 is `pending`; an `incomplete` or `invalid` status would send nothing. Widening its condition to "not `confirmed` and not `not confirmed`" is an edit to the scheduled task (not a repo file) for the owner to approve.
