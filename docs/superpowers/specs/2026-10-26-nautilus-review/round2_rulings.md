# Round 2: Claude's own critique and the ruling on every referee issue

Date: 2026-10-26. Spec revision 2. Referees: the same five Claude personas. GPT and Gemini: still not run (no CLI or
key in the container); the review stays REVIEW_INCOMPLETE for them.

Tally: security AGREE (2 minor). Quant, QA, ops and governance ACCEPT WITH CHANGES. No blocker. 12 major, 26 minor
new issues. Still open from round 1: QA-1, QA-7, OPS-8, GOVERNANCE-5.

## 1. Claude's own critique

Fact checked for these rulings: after `git fetch origin main`, `origin/main` is `716bf77` ("Upload project
structure"), and it is an ancestor of the feature branch (`git merge-base --is-ancestor`). The stale local `main`
ref in the cloud clone (`d330054`, an older upload) misled GOVERNANCE-R2-5. The merge target is therefore
`origin/main`, through a merge commit made by the owner.

C-5 (minor). The architect's rule-F changes (no `super().__init__`, a closure fee model, the parent parsing
`-X importtime`) are sound, but every one of them must be shown in the sandbox skeleton in section 5.2, so the
implementer does not re-derive them. Revision 3 adds a short code skeleton of the sandbox (imports, config classes,
fee closure, port class, `run` and `--check-env`), marked as normative for structure, not for every line.

C-6 (minor). The spec is 1,500 lines. Revision 3 must not grow it by more than about 10 percent; prefer replacing
prose with tables.

## 2. Rulings

All new issues are ACCEPTED as proposed by their referee, with these specifics:

### Security
- SECURITY-R2-1 ACCEPT: F4 reads "a Subscript or Attribute chain rooted at a name bound by `ast.Import` (a module
  alias), never one bound by `from ... import`".
- SECURITY-R2-2 ACCEPT: cite `data/fmp/quote_client.py:110, 115`.

### Quant
- QUANT-R2-1 ACCEPT: `rf = DGS3MO.dropna().reindex(dates, method="ffill") / 100 / 252`, read as
  `docs/asset_expansion_study.py:94-104, 150` does; R-06 refuses only a NaN left after the fill; L1-7 gains a blank
  mid-series control.
- QUANT-R2-2 ACCEPT: `parity.gate_predicates(score, gate)` recomputes exactly the predicates `_decide_strategy` reads
  (`core/quant/validate.py:536-622`), including the `n_configs < 8` PBO rule and `flat`. Agreement means equal
  decision and equal predicates. N8 is rebuilt on that list.
- QUANT-R2-3 ACCEPT: P7's expectation uses the table's `cost_bps` and the leg's nominal stress from the runner's loop;
  N7 gains a 2x leg whose `input.json` says stress 1; the rounding rule is the measured one (QA-R2-7).
- QUANT-R2-4 ACCEPT: the two claim labels as proposed.
- QUANT-R2-5 ACCEPT: (a) L1-29 checks embargo, cost, grid, domain and benchmark against the study's calls;
  (b) G-08: for pilot 2, `sc_qg` must reproduce the stored card's fields exactly, or the run is WITHHELD
  "reference drift".
- QUANT-R2-6 ACCEPT: F1r (constant rf 0.0001 per session) with hand values; N6 and L2-7 get a stepped synthetic rf.
- QUANT-R2-7 ACCEPT: `closes = np.round(raw, 9)` is the one rounding; bars are written with `f"{y:.9f}"`; the
  runner asserts the round trip.

### QA
- QA-1 and QA-7 (open from round 1) and QA-R2-1 ACCEPT: steps 0-2 become pure functions with explicit roots
  (`take_lock`, `check_table`, `check_tree`, `check_egress_record`), tested on temp roots; seams are refused during
  argument validation, before any file is written; in rehearsal the git state is recorded, never refused.
- QA-R2-2 ACCEPT: a specified layer-1 stub child (port rule, fee-inclusive Decimal sizing, Money rounding, valid
  outputs and echoes; flags select failure modes); `timeout`, `register_fn` and `score_fn` keywords, refused in
  of-record mode.
- QA-R2-3 ACCEPT: L1-5 moves the ledger mtime back 601 s with `os.utime`; L1-25 adds the 601-second pass case.
- QA-R2-4 ACCEPT: same fix as QUANT-R2-1.
- QA-R2-5 ACCEPT: `tools/nautilus/launch.py` (launch builder, venv and identity reads, census parser) lands at
  Step 3; tests move to the step whose code they need.
- QA-R2-6 to QA-R2-14 ACCEPT as proposed (`--write-goldens` Linux-only and non-overwriting; money as
  `f"{balance.as_decimal():.2f}"`; `final_qty` and `invalid_reasons` in goldens; HALF_UP tie rule with the 0.125
  control; capital bounded by `PRICE_MAX`; F4 wording; `--guard-selftest` launched at step 3; the measured on_bar
  re-raise behaviour; generator code given in the spec; production ledger path resolved through `config.macro_dir()`
  and both paths digested; both wheels' RECORD files committed under `tests/fixtures/nautilus/` with md5s; L1-15
  exempts binary modes).

### Ops
- OPS-8 (open from round 1) ACCEPT: `runner --handoff-report` writes
  `docs/nautilus_bridge/handoff/<platform>.json`, run last in Step 7A whatever failed; the owner commits and pushes it.
- OPS-R2-1 ACCEPT: the Step 7A PowerShell block is one checked command per line; existing Python 3.13 registrations
  are listed first; the installer's Authenticode signature is checked; `Start-Process -Wait -PassThru` with a log
  and ExitCode 0; wheels downloaded with the dedicated interpreter's pip.
- OPS-R2-2 ACCEPT: O9 and 4.4 state that the owner's global interpreter is the Microsoft Store Python 3.13
  (UNVERIFIED until 7A prints `sys.executable`); R-03 refuses a venv whose base lives under `WindowsApps` or
  `\Packages\PythonSoftwareFoundation.`.
- OPS-R2-3 ACCEPT: `write_record` with mkstemp, fsync and `os.replace` retried up to 10 times over 5 s;
  intermediate writes best effort; final write falls back to `run.final.<pid>.json`.
- OPS-R2-4 to OPS-R2-8 ACCEPT as proposed (`except BaseException` kills the tree; L2-5 split into 5a and 5b; a
  Remedy column in section 7; the re-run policy with `--rerun-of <id> --reason` and `supersedes`; paths compared as
  `normcase(realpath(p))`, PATH built from `os.environ["SYSTEMROOT"]`).

### Governance
- GOVERNANCE-5 (open from round 1) and GOVERNANCE-R2-3 ACCEPT: rehearsal mode refuses any prices file whose md5 is a
  pinned real file (SPY, BTC, DGS3MO is allowed only as a cash series), whatever its end date. L1-9 plants the SPY
  md5 with end 2004-11-30 and expects R-10.
- GOVERNANCE-R2-1 ACCEPT: Step 1 is split. 1a: Claude rounds ruled and applied; Steps 2 to 7 may start on the
  branch with synthetic data and temp ledgers (this is what the owner's instruction to continue without stopping
  covers). 1b: GPT and Gemini rounds run (or a substitute is recorded) and the owner signs off; required before
  Step 7A. The Status block, Step 1, O8 and the Owner context say the same thing.
- GOVERNANCE-R2-2 ACCEPT: the 7A.1 sentence releases the merge and the T-RO-01 exemption only. Of-record runs are
  approved through `owner_confirmed`, written at 7A.3 after the Windows evidence exists; `--fingerprint` prints the
  `table_sha256`, which `owner_confirmed` quotes.
- GOVERNANCE-R2-4 ACCEPT: the pure-function split (as QA-R2-1); the constraint reads "Claude never runs of-record
  mode".
- GOVERNANCE-R2-5 ACCEPT-MODIFIED: the merge target is `origin/main`, which is `716bf77`, the base of this branch
  (verified above; the referee read a stale local ref). A merge commit made by the owner; no squash or rebase; keep
  the branch ref so every ledger anchor stays reachable. 7A.5 as proposed (fast-forward pull of Claude's review
  commit before Step 8).
- GOVERNANCE-R2-6 ACCEPT: the four citations corrected.

## 3. Rejected

None.
