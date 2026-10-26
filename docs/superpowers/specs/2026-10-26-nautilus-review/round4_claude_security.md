# Round 4 referee report: Claude, security-engineer lens

Scope of this lens: the order path and isolation. Can any path in Revision 4 send a real order, load credentials or
open a socket (the Rust core included), and can the T-RO-01 allow-list widen unnoticed? This round confirms that my
round-3 issues are resolved, re-checks the sandbox skeleton and the allow-list pins against Revision 4, and looks for
blockers or majors that Revision 4 introduced.

I read my reports for rounds 1 to 3, the three rulings files, and all 1,772 lines of Revision 4: the Status block, the
Owner context, sections 1 to 13 and Appendices A and B. Spec line numbers below ("spec L<n>") refer to Revision 4 in
the working tree. `file:line` is QUANTGEN at HEAD `4f5f18b`. `nt:` is `nautilus_trader` 1.231.0 in `scratch:ntvenv`.
`scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probes are in `scratch:referee4_security/`. They read no price data. Every probe that ran Nautilus or pip ran inside
`unshare -rn`, so it had no network. I installed nothing, wrote no ledger row, and edited no file in the repository
except this report. `qa/acceptance_results.json` is unchanged (md5 `16c9baa5a1777853521d485d5078e456`, equal to HEAD).

## Verdict

AGREE.

Both of my round-3 issues are resolved, and every earlier issue from rounds 1 and 2 stays resolved; nothing regressed.
Revision 4 adds nothing that weakens the isolation design:
- The 5.2.9 skeleton gives no hit under two independent scans: mine, which I wrote from the 5.6 prose, and the
  author's `scan4.py`.
- Every 8.5 control I re-ran gives exactly the multiset the spec states.
- Both SHA-256 pins recompute from the Revision-4 constants to the values the spec commits to.

I found three new issues, all minor. None of them opens an order or network path, because the mandatory egress layer
(4.4, R-14) stays the real boundary and each issue fails closed:
- SECURITY-R4-1: an overstated sentence about rule F. The gap behind it predates Revision 4, and my own round-3 report
  repeated the overstatement.
- SECURITY-R4-2: a Step 7A re-entry path that the new firewall rule blocks.
- SECURITY-R4-3: two unstated details of the egress record and the firewall rule on re-entry.

## Sections reviewed

I read the whole revision. These are the parts I checked most closely from this lens, with the check I ran and why
each guard is sufficient.

- **5.2.9 skeleton (spec L493-645) against 5.6 (spec L865-966).**
  - What changed in Revision 4: `plain_mean`, the `C-12:` reason prefix, and the `if __name__ == "__main__":` guard
    (spec L643-644).
  - Check: I copied the block verbatim into `skeleton_r4.py` and scanned it in sandbox mode with my own `scan_mine.py`
    (carried over from round 3). Result: NO HITS. The author's rules (`scratch:rev4_probe/scan4.py`, run through
    `author_probe.py`) also give no hits.
  - Why the guard is sufficient: `__name__` is an `ast.Name`, so F3, which inspects only `Attribute` nodes, does not
    apply. `__name__` is not in `SANDBOX_BANNED_NAMES`, so F2 does not apply. The string `"__main__"` contains no denied
    prefix or name, so E does not apply.
- **8.5 controls (spec L1380-1406), Revision 4 wording.** Revision 4 now inserts each control's code "before its
  `if __name__` guard".
  - Check: `controls_r4.py` reproduces every multiset I re-ran: the sandbox positive control (none); verbs
    {A, CALL x8, TEXT}; receiver {A, CALL x2, TEXT}; bare reference and string {A, CALL, TEXT}; bare import {C3};
    denied name {C1, C3}; `sys.modules` {C3, E, F1}; module chain {F4}; `__dict__` {F3}; getattr and open {F2}; path
    {F5}; os call and `platform.system()` {F6}; importlib {C3, F1}; all 14 banned-module controls {C3, F1}; and all 12
    banned-name controls {F2}.
  - I skipped "sandbox relative". As in round 3, my tool double-counts C3 on that control, against the spec's rule of
    at most one hit per node.
- **5.6 pins (spec L953-963).** `pins.py` hashes the constants block as extracted verbatim from Revision 4
  (`constants_r4.py`) and gives:
  - allow-list `2792ad4af44c6af599092f81594a34d1f7d013cd17abf5882c8c6f72a042e49f`;
  - rule-F lists `70bcf50fbce5637a1854413618b6b9827c04dc10a59a0a25d274b4be1941da6c`.

  Both equal the committed values. The constants differ from Revision 3 only in comments, so the "widen unnoticed"
  guard is unchanged.
- **4.3, 4.4, 3.12, R-14 (spec L222-225, L259-303, L1190).**
  - Every child still starts through `run_child`, and the POSIX argv still begins with `unshare -rn`.
  - A rehearsal `--child-cmd` replaces only the items from `<venv python>` to the script path, so it cannot drop the
    prefix.
  - Of-record mode refuses every seam during argument validation (R-11).
  - The one widening is the hand-off report's second control connect. It is deliberate and documented as the only
    other network call (spec L300-301, L670).
- **New parent-side code (spec L667-676, L765-769).**
  - `ctypes.windll.kernel32.SetThreadExecutionState`, `netsh advfirewall firewall show rule` and the control connect
    all live in the runner, never in the sandbox.
  - A runner snippet containing all three (`runner_snip.py`) gives no hit under my scan and no hit under the real
    `tests/macro_m0_harness.py::_offences`.
  - `ctypes` is absent from `FORBIDDEN_IMPORTS` (`tests/macro_m0_harness.py:38-42`), and no `FORBIDDEN_TEXT_CI` token
    occurs (`:28-34`).
- **Isolation of tests and data (spec L138-143, L198-203, L658, L1340).**
  - The per-test `QUANTGEN_MACRO_DIR` works because `config.macro_dir()` re-reads the variable on every call
    (`config.py:176-178`, through `_clean` at `:32-39`).
  - The child cannot inherit that variable: its environment is explicit, and C-10 asserts the exact keys.
  - The rehearsal `prices_file` must resolve under the temp dir by `normcase(realpath)`. A symlink into
    `docs/asset_expansion/cache/` therefore resolves out of the temp dir and is refused, and a hard link or byte copy
    still meets the md5 refusal.
- **6.6 `code_sha256` (spec L1112-1120).** It now also covers `HARNESS_SOURCES` (`core/quant/gate_package.py:36-38`),
  the study and `config.py`. The sandbox stays inside the digest (`tools/nautilus/**/*.py`), so an of-record run cannot
  launch a sandbox that differs from the one the owner confirmed (L1-19 plants a sandbox byte).
  - Importing `core.quant.gate_package` in the parent only binds definitions. Its imports at `:17-29` define helpers
    and write nothing at import time.
- **5.2.7 and 7 (spec L452-482, L1171-1219).** The parent now re-derives C-01 to C-04 and C-15 from the manifest
  (QA-R3-2), so the parent no longer trusts the child's own `valid` flag. This strengthens the trust boundary between
  parent and child.
- **Step 7A (spec L1434-1500), sections 11 and 12 (spec L1583-1608).**
  - The new firewall re-entry line and `--egress-record` re-runs give SECURITY-R4-2 and SECURITY-R4-3.
  - Section 12 still lists only "a Python audit hook" as out of scope.
  - Risk 2's wording gives SECURITY-R4-1.

## Earlier issues

Round 3:
- **SECURITY-R3-1 (minor): resolved.**
  - `exit(main())` now sits under `if __name__ == "__main__":` (spec L643-644).
  - Re-verified with both scanners, as described under Sections reviewed.
- **SECURITY-R3-2 (minor): resolved as ruled (no rule change, one sentence).**
  - Spec L946-947: "Rule E is fail-closed against the sandbox's own text: maintainers keep its diagnostics free of
    every denied prefix and name".
  - The Revision-4 skeleton's new string `"C-12: bar ... differs from bars.csv"` contains no denied token.

Rounds 1 and 2, re-checked for regressions in Revision 4 (none found):
- **SECURITY-1 (blocker): resolved.** Egress is mandatory and in scope (spec L222-225, L280-303), and the scan is one
  layer of three (spec L73-74).
- **SECURITY-2 (major): resolved.** The census is "drift detection, not a use guard" (spec L472), and O13 says the
  same.
- **SECURITY-3 (major): resolved.** `inside()` plus F2 and F5 (spec L484-491). L2-5b remains the `.env` link control.
- **SECURITY-4 (major): resolved.** Section 12 lists only the audit hook (spec L1607).
- **SECURITY-5 (major): resolved.** Both pins recomputed above.
- **SECURITY-6 (minor): resolved.** Spec L897-903.
- **SECURITY-7 (minor): resolved.** Rule A is node-based (spec L933), and the verbs, receiver, bare-reference and
  string controls reproduce.
- **SECURITY-R2-1 (minor): resolved.** F4 wording (spec L942, L365-366); the module-chain control gives {F4}.
- **SECURITY-R2-2 (minor): resolved.** `data/fmp/quote_client.py:110, 115` (spec L902, L929).

## New issues

### SECURITY-R4-1 (minor): rule F does not "ban the reach"; attribute chains reach `sys.modules`

- **Section:** 11 risk 2 (spec L1587), 5.2.2 (spec L361-370), 5.6 rule F (spec L939-944).
- **Problem.**
  - Risk 2 says "Rule F bans the reach (`sys.modules`, dunders, module subscripts, dynamic calls)". That is broader
    than the rules deliver.
  - F4 fires only on a `Subscript` whose chain is rooted at an `ast.Import` alias. Nothing flags a non-dunder
    attribute chain that reaches the `sys` module and then calls `.get`, or one rooted at a `from`-imported name.
  - These lines pass every rule A to F and reach `nautilus_pyo3.network.http_get`:
    - `platform.sys.modules.get('nautilus_trader.core.' + 'nautilus_' + 'pyo3')`
    - `argparse._sys.modules.get(...)`
    - `Path.parser.sys.modules[...]`, where `Path` is bound by `from pathlib import Path`, so it is not a module alias.
  - The split string keeps rule E silent: no piece contains a denied prefix or name.
- **This gap predates Revision 4.** It was already in Revisions 2 and 3. My round-3 report overstated the scan
  ("the split-string variant has no mechanism to reach `sys.modules`"), and I correct that here.
- **It is not a boundary failure.** The spec already says "The static scan cannot bind the Rust core ...; the OS does"
  (spec L282), and O2's cost column relies on egress. Under `unshare -rn` or the Windows rule, any socket the Rust core
  opens still fails.
- **Evidence.**
  - Scans: `controls_r4.py` (my scanner) and `author_probe.py` (the author's `scan4.py` rules) give NO HITS for all
    three lines, inserted into the Revision-4 skeleton before its guard.
  - Runtime: `reach_probe.py`, run under `unshare -rn` with `scratch:ntvenv/bin/python -I`, prints `module=True
    network=True http_get_callable=True` for each route. It never calls `http_get`.
  - Code behind the routes:
    - `nt:core/nautilus_pyo3.pyi:5486` (`http_get`) and `:5492` (`http_post`).
    - `/usr/lib/python3.13/platform.py:119` (`import sys`).
    - `/usr/lib/python3.13/argparse.py:90` (`import sys as _sys`).
    - `/usr/lib/python3.13/pathlib/_local.py:104` (`parser = os.path`, a module that holds `sys`).
- **Proposed fix.**
  - Required (wording): risk 2 and 5.2.2 should say "Rule F rejects the direct spellings (`import sys`, module-alias
    subscripts, dunders, dynamic calls); an attribute path through a loaded module can still reach `sys.modules`, which
    the scan cannot fully close; the egress layer bounds any use".
  - Optional (cheap hardening, no pin change): in the sandbox, widen F3 to any `Attribute` whose name starts with `_`,
    and flag any `Attribute` named `modules` or named as an entry of `SANDBOX_BANNED_MODULES`. Add three 8.5 controls,
    one for each line above.
    - `f7_probe.py` shows this flags all three routes plus `platform.os.environ`.
    - It leaves both the Revision-4 skeleton and the author's filled `scratch:rev4_probe/sandbox_r4.py` clean.
    - It touches rule code, not a pinned constant.

### SECURITY-R4-2 (minor): Step 7A re-entry runs `pip download` through the firewalled interpreter

- **Section:** Step 7A.2 re-entry (spec L1441-1443, L1461, L1465). Revision 4 introduced this (OPS-R3-2).
- **Problem.**
  - When `$q\py313\python.exe` exists from an earlier attempt, the owner "skips from the registry line to the
    `pip download` line".
  - If that attempt got past the firewall line, the rule `QUANTGEN-nautilus-block-out` already blocks
    `py313\python.exe`, the interpreter that runs this `pip download`. pip contacts the index even when every wheel is
    already in `-d`, so the line fails and throws "download".
  - The attempts most likely to fail all come after the firewall line: `--check-env`, `--egress-record`, `--fixtures`
    and the suite, which hold the UNVERIFIED Windows facts of 13.1. So every re-entry after such a failure stops at
    the same line.
  - This is fail-closed: no route opens, and the owner falls through to `--handoff-report`. It costs one owner round
    trip per attempt, not safety.
- **Evidence.** Linux, pip 26.2.2 in `scratch:ntvenv`, under `unshare -rn`, with all 16 Linux wheels from
  `scratch:closure/linux/` copied into the `-d` folder:
  - Command: `python -m pip download --require-hashes --only-binary=:all: --no-deps -r
    requirements-nautilus.body.txt -d <that folder>`.
  - Result: exit 1, "No matching distribution found for click==8.5.0".
  - On Windows this is UNVERIFIED, but pip resolves the same way.
- **Proposed fix.** On re-entry, skip from the registry line to the `venv` line when `$q\wheels` already exists.
  - The install line (5.1) is offline with `--require-hashes`, so it re-checks every wheel's hash, and re-downloading
    adds nothing.
  - Alternatively, run the `pip download` line only while `Get-NetFirewallRule -DisplayName
    QUANTGEN-nautilus-block-out` returns nothing.

### SECURITY-R4-3 (minor): the egress proof on re-entry, with a stale rule and an unstated exit code

- **Section:** 4.4 and 5.3.1 (spec L297-303, L662, L674-676), Step 7A.2 (spec L1465, L1468), R-14 (spec L1190).
- **Problem 1: a wrong rule is never corrected.** Revision 4 creates the rule "only when absent", matched by display
  name. If an earlier attempt created the rule wrongly (a mistyped `<printed path>`, a disabled rule, or a narrower
  profile), re-entry keeps it.
  - The probe then connects, R-14 refuses, and nothing in the runbook or in R-14's Remedy says how to replace the
    rule. Today the Remedy only diagnoses, with `Get-NetFirewallApplicationFilter`.
- **Problem 2: the exit code of `--egress-record` on a failed proof is unstated.** Revision 4 also lets
  `--egress-record` overwrite its record, but no section says what it exits when `probe.blocked` is false or
  `control_connect.ok` is false. So it is unclear whether the 7A.2 line `if ($LASTEXITCODE) { throw "egress" }` stops
  there or lets later lines run on a failed proof.
- **Both fail closed.** Of-record mode re-reads the record's content (R-14), and the per-run probe runs in both modes.
  So no pilot can run without a blocked route; the cost is owner time and a confusing hand-off.
- **Evidence.**
  - Spec L1465 creates the rule under `if (-not (Get-NetFirewallRule -DisplayName ...))`, which matches by name and
    nothing else.
  - Spec L662 says only "`--egress-record` writes 4.4's record".
  - Spec L776-778 defines exit 0 as "a mode's success" without saying what success means for this mode.
- **Proposed fix.**
  - State the exit code: "`--egress-record` writes the record, then exits 2 (R-14) unless `probe.blocked` and
    `control_connect.ok` are both true."
  - Add one Remedy line to R-14 for Windows: "if the filter's `Program` is not `<q>\py313\python.exe`, or the rule is
    disabled or not `-Profile Any`: in an elevated window `Remove-NetFirewallRule -DisplayName
    QUANTGEN-nautilus-block-out`, then the creation line of 7A.2 again."

## Why I agree or not

I agree, and I confirm the AGREE I gave in rounds 2 and 3 after reading all of Revision 4. From the isolation lens an
engineering team can build it. Four reasons:

1. **The one order-placing file passes its own scan.**
   - Two independent scanners give zero hits on the Revision-4 skeleton.
   - Every 8.5 control I re-ran gives its stated multiset, and both hash pins recompute exactly.
   - Rule A still allows exactly one `self.submit_order` call in a method. The seven other verbs are forbidden in every
     file, and a widened allow-list or rule-F list changes a pinned digest and fails Step 4.
2. **The real boundary is unchanged and still fails closed.**
   - Every child, including the probe, the self-tests and the stubs, still starts through one launch contract: under
     `unshare -rn` on Linux, under the firewalled dedicated interpreter on Windows.
   - Every run, in either mode, runs the probe.
   - Of-record mode also needs a matching Step 7A record (R-14), and every seam is refused during argument validation
     (R-11).
   - SECURITY-R4-1 shows again that the scan alone cannot confine Python, which the spec already concedes (spec L282).
     It is a wording correction plus optional hardening, not a hole in the boundary.
3. **Revision 4's new parent code stays outside the sandbox and scans clean.** That code is `ctypes` for sleep,
   `netsh show`, the second control connect and the `gate_package` import. The parent now distrusts the child more
   (QA-R3-2), and `code_sha256` binds the approved sandbox bytes to each of-record run.
4. **What remains is minor.** SECURITY-R4-2 and SECURITY-R4-3 concern the re-entry rules Revision 4 added to Step 7A.
   Both fail closed and cost owner time, not isolation. Two facts remain UNVERIFIED by construction, since this session
   has no Windows host:
   - Does the firewall rule bind the interpreter the redirector starts?
   - Does pip on Windows behave as measured on Linux?

   Both are gated correctly by the Step 7A probe and record.

Moderator-rejected points: none in rounds 1 to 3 ("Rejected: None" in all three rulings), so I re-raise nothing. The
growth to 1,772 lines (+6.6 percent, C-6) is within budget.

Probe files, all in `scratch:referee4_security/`:
- `skeleton_r4.py` and `constants_r4.py`: verbatim extracts of Revision 4.
- `scan_mine.py`: my rules, carried over from round 3.
- `controls_r4.py`, `pins.py`, `author_probe.py`, `reach_probe.py` and `f7_probe.py`.
- `runner_snip.py`: the runner snippet with `ctypes`, `netsh` and the control connect.
