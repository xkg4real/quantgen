# Round 1: Claude's own critique and the ruling on every referee issue

Date: 2026-10-26. Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, revision 1.
Referees: five independent Claude personas (security, quant, qa, ops, governance). Their reports are the
`round1_claude_<persona>.md` files in this folder. GPT (Codex CLI) and Gemini (Antigravity CLI) are **not run**:
neither CLI exists in the Linux container, and no API key is set. Their rounds are pending on the owner's machine
(Codex quota back 2026-10-30 14:40). Until they run, or the owner records a substitute, the review is
REVIEW_INCOMPLETE.

Tally: 1 REJECT (security), 4 ACCEPT WITH CHANGES. 1 blocker, 35 major, 31 minor.

## 1. Claude's own critique (the moderator is a participant)

Facts checked for these rulings (2026-10-26, HEAD `6f7c610`):
- `core/quant/validate.py`, `strategies.py`, `gate_ledger.py`, `costed.py` are gate-package harness sources
  (`core/quant/gate_package.py:36-38`). The bridge must not edit any of them. Any helper it needs lives in
  `tools/nautilus/`.
- `walk_forward` takes no injected selection (`core/quant/validate.py:345-381`). `WalkForward` is a frozen dataclass
  whose fields can be built directly (`:333-343`). A selection-matched OOS series is therefore a small helper that
  re-slices `[o + embargo, min(o + embargo + w_oos, T))` for QUANTGEN's `chosen`. It must reproduce `wf_qg.pnl` bit
  for bit when applied to QUANTGEN's own matrix, and that equality is its test.
- `unshare -rn true` works in the Linux container. A child can run with no network namespace at all.
- `tools/debate.py:64-79` already kills a process tree (`taskkill /T /F` on Windows).
- The global interpreter here has neither `pyarrow` nor `nautilus_trader`.

C-1 (major). **Scope is too wide for one build.** Revision 1 carries a realism leg, 30 fail-closed conditions and a
cross-engine module baseline. The realism leg adds ledger rows that raise the parity verdict's trial count (K11a),
needs its own sizing rule (A-5) and its own fixtures (N3), and mixes three effects in one delta (QUANT-8). It was the
synthesis's addition, not the owner's: the owner's plan had parity and the gate only. Ruling: **defer the realism leg**
to a later, separately specified step. No latency code, no `timing_lag` rows, no N3, no K11b exemption in this build.

C-2 (major). **The sandbox strategy must refuse to run outside a backtest.** The owner's QuantConnect plan had "a
template that refuses to start in live mode". Nautilus strategies run unchanged under a `TradingNode`, so the same
guard is needed: `on_start` checks the kernel environment and stops the strategy unless it is BACKTEST. A test runs
the check against a non-backtest environment value. (This also answers GOVERNANCE-2's "nothing to switch on".)

C-3 (minor). **The decision on a card must not depend on one engine.** See QUANT-2 below.

C-4 (minor). **README counts.** The README test table is updated only from the owner's Windows full run (Step 10).
The cloud build adds the `nautilus` row text without changing the Total row.

## 2. Rulings on the referee issues

Format: id, ruling (ACCEPT / ACCEPT-MODIFIED / REJECT), and the change to make in revision 2.

### Security

- **SECURITY-1 (blocker) ACCEPT.** The static scan cannot bind the Rust core. Revision 2 adds two layers, and keeps
  the scan:
  1. *OS egress control, in scope and mandatory for every of-record run.* Linux: the parent launches the child as
     `unshare -rn <venv python> ...`; the runner refuses an of-record run if `unshare` is absent. Windows: the venv is
     created from a **dedicated base interpreter** installed only for it (for example `uv python install 3.13` or a
     python.org per-user install into `%LOCALAPPDATA%\quantgen\py313`), and a Windows Firewall rule blocks outbound
     traffic for that interpreter's `python.exe` (the venv redirector starts it). The global interpreter is a different
     file, so QUANTGEN's own data fetches are unaffected. Step 7A records an egress probe:
     `tools/nautilus/egress_probe.py` tries `socket.create_connection(("1.1.1.1", 443), timeout=3)` under the child's
     launch contract and must fail; the run record stores the probe result, and an of-record run refuses without a
     passing probe for the same interpreter path and firewall rule name. Rehearsals on Linux also use `unshare -rn`.
  2. *Sandbox language restriction.* Rule F grows: in the sandbox, no `import sys` (only `from sys import argv, exit`),
     no `importlib`, `builtins`, `ctypes`, `socket`, `ssl`, `http`, `urllib`, `asyncio`, `subprocess`, `os` (use
     `pathlib`), `gc`, `inspect`, `types`; no attribute whose name starts with `__`; no `getattr`, `setattr`,
     `delattr`, `vars`, `globals`, `locals`, `eval`, `exec`, `compile`, `__import__`, `breakpoint`; no subscript on a
     name bound to a module. Positive and negative controls for each.
- **SECURITY-2 ACCEPT.** The `sys.modules` baseline is reworded as drift detection, not a use guard. Risks 2 and 3
  cite the egress layer and rule F instead.
- **SECURITY-3 ACCEPT-MODIFIED.** The sandbox resolves every path it opens and refuses any path outside its argv
  temp dir; a negative control opens the repo `.env`. The parent copies every input into the temp dir. The egress
  layer makes any key that is read useless outside the machine; O3 states this.
- **SECURITY-4 ACCEPT.** Folded into SECURITY-1. "Firewall rule" leaves section 12.
- **SECURITY-5 ACCEPT.** A new test pins the allow-list: the sha256 of the canonical JSON of
  `{NAUTILUS_SANDBOX, NAUTILUS_ALLOWED_FROM, NAUTILUS_DENIED_PREFIXES, NAUTILUS_DENIED_NAMES, SANDBOX_STDLIB}` equals a
  constant in the test, with the comment that a change needs an owner ruling recorded in the spec.
- **SECURITY-6 ACCEPT.** Add the regex `\w+(Http|WebSocket|Socket|Execution|Data)Client\b` and the names
  `api_key`, `api_secret`, `TradingNode`, `LiveNode` to the deny-list.
- **SECURITY-7 ACCEPT-MODIFIED.** Rule A counts AST nodes only: `ast.Attribute` with attr `submit_order` and
  `ast.Name` `submit_order`, plus string constants containing `submit_order`. Exactly one call node `self.submit_order`
  in one method is allowed; any other node fails.

### Quant

- **QUANT-1 ACCEPT.** Add P0 (hard), input provenance: the runner's price, date, rf and benchmark arrays equal those
  the study's own loader builds (`docs/asset_expansion_study.py:138-153`), byte for byte after the shared rounding;
  md5 pins for SPY, BTC and DGS3MO. The card says parity validates the engine, not the data.
- **QUANT-2 ACCEPT.** Both matrices are always scored, with QUANTGEN's selection (QUANT-3). The card's decision is
  written only if both decisions and every gate flag agree; otherwise WITHHELD "decision mismatch". The card shows
  both.
- **QUANT-3 ACCEPT.** The Nautilus walk-forward reuses `wf_qg.origins` and `wf_qg.chosen` through the
  selection-matched helper (section 1 above). P11, the Nautilus-own selection, becomes a reported diagnostic and never
  withholds. The exempt-flip machinery of K3 is removed.
- **QUANT-4 ACCEPT.** `n_trials = N_raw(family, after registration) + U`, where `U` counts the study's documented
  configurations whose `config_id` is absent from the family ledger. The runner computes `U` from the study's grid.
  Both terms are printed.
- **QUANT-5 ACCEPT.** P7 becomes hard: the parent recomputes every commission as `qty × price × c × s / 1e4` from the
  fills and the leg's declared stress, independently of the child's commission column; total within 1e-6 relative,
  and per fill within $0.01. A 2x leg must read s = 2.
- **QUANT-6 ACCEPT.** Cards carry `claim_label`. Pilot 2: "engine replication of stored card C3 on the same data; not
  new evidence about the rule". Pilot 1: "engine replication of QUANTGEN's SPY trend grid".
- **QUANT-7 ACCEPT.** Pilot 1's expected verdicts list INSUFFICIENT_DATA first.
- **QUANT-8 ACCEPT.** Moot: realism leg deferred (C-1).
- **QUANT-9 ACCEPT.** P10 bound becomes `(c/(1+c) + P/E)(|r| + c) + rf_day + 1e-9`.
- **QUANT-10 ACCEPT.** Add synthetic fixture N6: price near $650, ±10% days, entries on large-move days; P2 and P3
  must hold with their margins. Real pilot-window margins stay UNVERIFIED until the registered run.
- **QUANT-11 ACCEPT.** The card's engine field says "per-column event-driven replication; walk-forward column switches
  are not executed in either engine".

### QA

- **QA-1 ACCEPT.** The runner takes `--ledger-dir` and `--out-dir`; rehearsal requires both under the system temp dir.
  Every nautilus-suite test hashes `~/.nextgen/macro/ledgers` and the repo's `docs/nautilus_bridge/` before and after,
  and fails on any change.
- **QA-2 ACCEPT.** Golden format defined: JSON with `status`, `bars_seen`, `fills` (date, side, qty, price,
  commission), `final_cash`; integers and strings exact, money within 0.005, prices exact at the instrument precision.
  Goldens are produced from the fixture input files the spec defines.
- **QA-3 ACCEPT.** Moot for the realism parts (C-1). N3 is removed.
- **QA-4 ACCEPT.** `input.json` has a schema with ranges. The child accepts any in-range value. The runner's of-record
  table enforces the pilot values (capital, precision, volume).
- **QA-5 ACCEPT.** The registration table has a field schema with `start` and `end`. The data step filters both ends.
- **QA-6 ACCEPT.** Ordering evidence: the ledger hash after registration is written into every child's `input.json`
  and echoed in its manifest; a child launched before registration cannot carry it. Timestamps are UTC with
  microseconds; `bridge_run_id` = UTC microseconds plus 8 hex of the table's sha256.
- **QA-7 ACCEPT.** Test seams: `--child-cmd` (rehearsal only) injects a stub child; `anchor_fn` is a runner parameter
  in tests; test 6 is NotRun without git.
- **QA-8 ACCEPT.** Every fail-closed condition gets a negative control or a written reason why it cannot be reached.
- **QA-9 ACCEPT.** The run record stores the card's md5; the card stores the run id only.
- **QA-10 ACCEPT.** Wheel identity = sha256 over the sorted `path,sha256` entries of the installed `RECORD` that the
  wheel itself ships (excluding `INSTALLER`, `REQUESTED`, `direct_url.json`, `RECORD` and `__pycache__`). These
  entries equal the wheel's own `RECORD`, so the expected value for both platform wheels is computed offline now.
- **QA-11 ACCEPT-MODIFIED.** The baseline is recorded from F1 and F2 only (no realism path); stdlib differences
  between 3.13.x patch levels are allowed by a written rule.
- **QA-12 ACCEPT.** Each named test gets a case that would fail.
- **QA-13 ACCEPT.** Rationale corrected; C-04 removed or given a trigger.
- **QA-14 ACCEPT.** Controls use `QUANTITY_MAX + 1` read at runtime, and one for `price_precision > FIXED_PRECISION`.
- **QA-15 ACCEPT.** Controls list exact tags; add `sys.modules` and `__dict__` controls (SECURITY-1 rule F).
- **QA-16 ACCEPT.** `csv.writer(..., lineterminator="\n")`; test 16 covers both env branches by parameter; the parent
  creates `<tempdir>/home` and `<tempdir>/tmp`.
- **QA-17 ACCEPT.** Refusal by content (md5 and date range), not by name; containment compares resolved paths.
- **QA-18 ACCEPT.** `git status --porcelain=v1 -z --untracked-files=all`; a re-run never overwrites a card (new
  run id folder).
- **QA-19 ACCEPT.** P1's margin uses QUANTGEN's own decision margin, computed in the parent.
- **QA-20 ACCEPT.** Moot after QUANT-3.
- **QA-21 ACCEPT.** Folder path fixed; Step 2's dry run is the plan's own RED/GREEN steps on a scratch clone.

### Ops

- **OPS-1 ACCEPT.** `Popen` with a new process group; on timeout, kill the tree (`taskkill /T /F` on Windows, `killpg`
  on Linux), as `tools/debate.py:64-79` does.
- **OPS-2 ACCEPT.** The runner reconfigures stdout and stderr to UTF-8 with `errors="replace"`, as
  `tests/run_all.py` does.
- **OPS-3 ACCEPT.** When `repo_anchor()` is UNVERSIONED but `git rev-parse HEAD` succeeds, the refusal says the refs
  are packed and that a new commit (the hand-off commit) writes the loose ref.
- **OPS-4 ACCEPT.** The runner expands `%VAR%` and `~`, rejects control characters, and requires an existing file
  ending in `python.exe` or `python`; `.env.example` shows a single-quoted, forward-slash value.
- **OPS-5 ACCEPT.** New suite test: the global interpreter has no `nautilus_trader` (FAIL if present). The
  requirements header gives cmd and PowerShell forms and says "never with the global python".
- **OPS-6 ACCEPT.** The run record is written right after registration with status IN_PROGRESS and updated per child;
  `KeyboardInterrupt` writes ABORTED; a rerun of the same table reports the earlier IN_PROGRESS record.
- **OPS-7 ACCEPT.** Windows wheel identity computed offline from the wheel (QA-10). The Windows module baseline is
  recorded at Step 7A; the allowed diff is a written list of platform modules; Claude reviews the diff in the next
  session before any pilot.
- **OPS-8 ACCEPT.** A PowerShell runbook, `docs/nautilus_bridge/RUNBOOK_windows.md`, with every command.
- **OPS-9 to OPS-15 ACCEPT.** As proposed (temp subdirs created; `rmtree` retries then records; porcelain v1 -z; BOM
  tolerated with `utf-8-sig` on the owner-edited table only; the card written with `newline="\n"` by the bridge, not
  `ModelCard.save`; dedicated interpreter named; facts corrected; a lock file per table under the out dir).

### Governance

- **GOVERNANCE-1 ACCEPT.** The authority statement is narrowed. The owner's words decide two things: the engine is
  NautilusTrader, and Claude continues without stopping. Everything else is a default taken on the owner's behalf and
  listed with its cost if wrong. Branch work is reversible. Merging, any of-record run and the T-RO-01 exemption take
  effect only after the owner's explicit sign-off sentence at Step 7A, recorded verbatim in the spec.
- **GOVERNANCE-2 ACCEPT.** O3 is restated with both halves of DO-NOT-BUILD item 21 and rule 01: the venv holds
  `TradingNode` and every adapter; the bridge never constructs them; the strategy refuses non-backtest environments
  (C-2); the egress layer (SECURITY-1) makes a switch-on fail.
- **GOVERNANCE-3 ACCEPT.** Of-record mode requires `--of-record`, an existing non-empty family ledger whose chain
  verifies, the egress probe record, and a host fingerprint (sha256 of `socket.gethostname()` plus the ledger file's
  first-row hash) written into the table by the owner at Step 7A.
- **GOVERNANCE-4 ACCEPT.** Content-based refusal (QA-17); rehearsal end date at most 2004-11-30 for SPY; BTC
  rehearsal uses synthetic series only.
- **GOVERNANCE-5 ACCEPT.** Step 7's rehearsal uses synthetic data only. Map 03's pre-2004 probe is cited as evidence
  and recorded in the data-access history, never repeated.
- **GOVERNANCE-6 ACCEPT.** Same as QUANT-2.
- **GOVERNANCE-7 ACCEPT.** OPS-5's test covers `nautilus_trader`. `pyarrow` in the global interpreter is reported,
  not failed, because other owner packages may bring it; the coordinator ruling binds the bridge's own code.
- **GOVERNANCE-8 ACCEPT.** Pilot 2's table and FAIL-vs-NotRun on a venv mismatch return as owner rulings.
- **GOVERNANCE-9 ACCEPT.** Constraint: never run a pilot while the H2 readout runs; the runner refuses while a
  paper_live lock or a fresh C3 write (under 10 minutes old) is seen.
- **GOVERNANCE-10 ACCEPT.** The text says this is the first exemption for a forbidden token in T-RO-01's history.
- **GOVERNANCE-11 ACCEPT.** The merge is the owner's act, after the sign-off sentence.
- **GOVERNANCE-12 ACCEPT.** Folder path fixed; Appendix B says round 1 ran in the repo clone, which holds no `.env`.
- **GOVERNANCE-13 ACCEPT.** Step 2's Global Constraints copy all of section 3.

## 3. Rejected

None. Every issue was accepted, accepted with modification, or made moot by C-1.
