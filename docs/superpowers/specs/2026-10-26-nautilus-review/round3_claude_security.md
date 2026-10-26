# Round 3 referee report — Claude, security-engineer lens

Scope of this lens: the order path and isolation. Can any path in Revision 3 send a real order, load credentials, or
open a socket (including from the Rust core), and can the T-RO-01 allow-list widen unnoticed? This round confirms the
round-2 rulings held, re-verifies the new section 5.2.9 sandbox skeleton against its own scan, and hunts for problems
Revision 3 introduced.

PRESS CHECK: I read the ENTIRE Revision 3 (sections 1 to 13, Appendices A and B, all 1,663 lines), not only the
changed parts — the owner context and rulings, architecture and launch contract, every component (5.1 to 5.8), the data
model (6.1 to 6.8), error table (section 7), testing (8.1 to 8.6), steps and pilots (9, 10), risks, out-of-scope, open
questions, and both appendices. I re-verified the section 5.2.9 skeleton with my own scan built from the section 5.6
prose (not the author's `scan3.py`), recomputed both allow-list hash-pins, and reproduced the section 8.5 control
multisets independently.

All probes were read-only, in `scratch:referee3_security/`. No real SPY or BTC price was read; no SPY row on or after
2004-12-01. I made no network call (the only connect in the design, the egress probe, I did not run; my checks were
pure AST and hashing). QUANTGEN is at HEAD `7112351`; `nt:` is `nautilus_trader` 1.231.0 in `scratch:ntvenv`.

## Verdict

AGREE.

From the isolation lens an engineering team can build Revision 3 today. Every round-1 and round-2 issue I raised is
resolved and stays resolved. The central press-check demand — "a skeleton that violates its own scan is a blocker" — I
checked with an independent scan: the section 5.2.9 skeleton gives **zero hits** against rules A to F and C1 to C3, D,
E, and my scan reproduces 16 of the 17 section 8.5 controls exactly (the 17th is a double-count in *my* tool, not a
spec defect). Both SHA-256 allow-list pins recompute to the committed values. The three-layer boundary (static scan,
BACKTEST guard, OS egress) is intact and, crucially, the real boundary against the Rust core — OS egress — is mandatory
and gated by a fail-closed probe (R-14) with a new diagnostic remedy. The two round-2 minors are fixed. I found no new
blocker or major; the two items under New issues are non-blocking observations that do not change the verdict.

## Sections reviewed

I read the whole revision; the sections I re-checked most closely from this lens, and why each guard is sufficient:

- **Section 5.2.9 (sandbox skeleton) against section 5.6 rules A to F.** Re-checked because it is new in Revision 3
  (moderator item C-5) and is the one file that may place an order. I extracted the skeleton verbatim from the spec
  (`scratch:referee3_security/skeleton_spec.py`) and ran my own `scan_mine.py` (rules transcribed from the 5.6 prose,
  constants copied verbatim from 5.6 lines 838-881). Result: NO HITS. Sufficient because the single `self.submit_order`
  is the only order emitter (rule A exempts exactly one `Attribute(attr="submit_order")` on `Name("self")` that is a
  call's `func` inside a method; code-only count of the token is 1), and every reach to the Rust network core is closed
  three ways: F1 bans `import sys`/`importlib`/`socket`/etc., F4 bans a subscript on an `ast.Import` module alias, E
  flags any sandbox string containing a denied prefix/name, and D plus the client-name regex deny the concrete client
  classes.

- **Section 5.6 (T-RO-01 amendment) and 8.5 (controls).** Re-checked the rule table, the two pin tests, and every
  control multiset. My scan reproduced: sandbox positive = none; verbs = {A, CALL x8, TEXT}; sandbox receiver = {A,
  CALL x2, TEXT}; sandbox bare reference / sandbox string = {A, CALL, TEXT}; bare import = {C3}; denied name = {C1, C3};
  sys.modules = {C3, E, F1}; module chain = {F4}; `__dict__` = {F3}; getattr / open = {F2}; path = {F5}; os call /
  `platform.system()` = {F6}; importlib = {C3, F1}. Sufficient because the multisets match the spec and the
  security-critical reaches (sys.modules, module-alias subscript, dunder, dynamic call, file I/O, OS call) each trip a
  distinct F rule. The one mismatch (`from . import runner`: my tool emits C3 twice, spec expects C3 once) is my tool
  violating the spec's own "each rule adds at most one hit per AST node" rule — the spec is right, my tool double-counts.

- **Sections 4.3, 4.4, 3.12 (launch contract and egress).** Re-checked that every child — sandbox, egress probe,
  `--check-env`, `--guard-selftest`, test stub — is wrapped by `unshare -rn` (POSIX) or the firewalled dedicated
  interpreter (Windows), that a rehearsal `--child-cmd` cannot strip the `unshare` prefix (the builder prepends it; the
  seam only replaces the items from `<venv python>` to the script path), and that of-record refuses every seam in
  argument validation (R-11). Sufficient because egress is mandatory and fail-closed (R-14), it binds the Rust core the
  scan cannot, and the probe plus the Step 7A record must both pass for an of-record run.

- **Sections 5.2.5 (BACKTEST guard), 5.2.8 (path containment), 6.7 (venv/wheel identity), 5.3.2 step 3.** Re-checked the
  guard (clock-class proxy, re-raised on-start), `inside()` (resolve + parent-equals-root, so a symlink out is refused),
  and that the parent uses `importlib.metadata.distribution` — not `find_spec` — so the "nautilus-trader" string does
  not trip rule E.

- **Section 12 (out of scope), section 7 (R-14), section 11 (risks 2, 3, 6, 21).** Re-checked that "a firewall rule"
  has left section 12 (it now lists only "a Python audit hook, which cannot see Rust sockets") and that R-14 gained a
  Windows diagnostic remedy. Also read, outside the deepest re-check but in full: owner rulings O1 to O15; data model
  6.1 to 6.8; parity 5.4; gate hand-off 5.5; fixtures 8.2; steps 1a to 10 and Step 7A; pilots 10.1 to 10.4; appendices.

## Earlier issues

Round 1:
- SECURITY-1 (blocker): **resolved.** Egress mandatory and in scope (3.12, 4.4); rule F closes the `sys.modules`
  spelling; scan is explicitly one of three layers. Re-verified: skeleton passes rule F; the split-string evasion is
  closed by F1/F4 (no mechanism) regardless of E.
- SECURITY-2 (major): **resolved.** 5.2.7 states the census is drift detection, not a use guard; O13 and risks 2-3 cite
  egress and rule F.
- SECURITY-3 (major): **resolved.** 5.2.8 `inside()` plus F2 (no `open`) and F5; control "sandbox path" = {F5},
  "sandbox open" = {F2}, L2-5b links input.json to `.env` and expects exit 20. Re-verified both controls.
- SECURITY-4 (major): **resolved.** "A firewall rule" left section 12; the Windows firewall and Step 7A probe are
  required contract.
- SECURITY-5 (major): **resolved and strengthened.** I recomputed both pins from the 5.6 constants with the spec's
  `_canon`: allow-list = `2792ad4af44c6af599092f81594a34d1f7d013cd17abf5882c8c6f72a042e49f`, rule-F lists =
  `70bcf50fbce5637a1854413618b6b9827c04dc10a59a0a25d274b4be1941da6c` — both match exactly, so Step 4 is reachable.
- SECURITY-6 (minor): **resolved.** `NAUTILUS_DENIED_NAME_RE` plus the concrete denied names; the regex matches
  `\w+XxxClient` forms.
- SECURITY-7 (minor): **resolved.** Rule A is AST-node based; controls verbs/receiver/bare-reference/string reproduce
  the {A, CALL, TEXT} multisets.

Round 2:
- SECURITY-R2-1 (minor, F4 wording): **resolved.** 5.6 rule F4 and 5.2.2 both read "a Name bound by `ast.Import` (a
  module alias) ... never a name bound by `from ... import`". Re-verified: the skeleton's `argv[1:]` and
  `self.config.closes[self.i]` give no F4; the "sandbox module chain" control (`argparse._sys.modules['x']`) gives F4.
- SECURITY-R2-2 (minor, citation): **resolved.** 5.6 and Appendix B cite `data/fmp/quote_client.py:110, 115`; I
  confirmed both lines use `api_key`, and the `NAUTILUS_BRIDGE_ONLY_NAMES` carve-out keeps that file (under `data/`)
  from tripping rule D.

## New issues

Two non-blocking observations about the new section 5.2.9 skeleton. Neither changes the verdict; both fail safe.

- **SECURITY-R3-1 — minor — 5.2.9.** The skeleton runs `exit(main())` at module scope, not under
  `if __name__ == "__main__":`. From the isolation lens this is inert: the parent never imports the sandbox (rule C2
  forbids the parent importing `nautilus_trader`, which the sandbox requires, so an import attempt would itself fail the
  scan), and every test launches it as a subprocess, so no code path imports it. Evidence: skeleton line `exit(main())`
  (spec L621); 4.1 ("never imports `nautilus_trader`, rule C2"); 8.1 (layer-1 has "no `nautilus_trader`"). Proposed fix
  (optional, defensive): guard with `if __name__ == "__main__":`. Non-blocking.
- **SECURITY-R3-2 — minor — 5.6 rule E.** Rule E flags any string constant in the sandbox containing a
  `NAUTILUS_DENIED_PREFIXES` or `NAUTILUS_DENIED_NAMES` entry. This is fail-closed and the skeleton avoids it (its only
  nautilus-ish string is `"nautilus-bridge-check-env/1"`, which matches no denied prefix), but a future legitimate
  diagnostic message that names a forbidden module verbatim (for example an error string containing `nautilus_pyo3`)
  would itself trip the scan. Evidence: 5.6 rule E; `scratch:referee3_security` string sweep found 0 skeleton strings
  containing a denied prefix/name. Proposed fix: none required; the implementer should keep sandbox diagnostics free of
  the forbidden tokens (fail-closed is the safe direction). Non-blocking.

## Why I agree or not

I said AGREE in round 2 and I confirm it after reading the entire Revision 3. The isolation design is complete from my
lens because each guard is sufficient for the surface it defends, and no layer was weakened between revisions:

1. **The scan confines the Python order surface.** Rule A pins exactly one `self.submit_order` call; the other seven
   order/position verbs join `FORBIDDEN_CALLS` for every file; the allow-list and rule-F lists are hash-pinned (I
   recomputed both). A future edit that widens the allow-list, repoints `NAUTILUS_SANDBOX`, or drops a denied entry
   changes a pinned digest and fails Step 4, or fails a section 8.5 control. This closes the "widen unnoticed" case.
2. **Rule F closes the reach to the loaded Rust clients** that my round-1 blocker exploited: no `sys`/`importlib`, no
   module-alias subscript, no dunder, no dynamic call, file I/O only through `inside()`. I verified the skeleton obeys
   all of these and that the split-string variant has no mechanism to reach `sys.modules`.
3. **OS egress is the real boundary and it is mandatory, not optional.** The static scan cannot bind the Rust core and
   the spec says so plainly (4.4); `unshare -rn` on Linux and the firewalled dedicated interpreter on Windows do, the
   per-run probe refuses an open route (R-14), and an of-record run also needs a matching Step 7A record. "A firewall
   rule" has correctly left section 12.
4. **The skeleton passes its own scan.** This was the explicit press-check gate. My independent scan — not the author's
   `scan3.py` — returns zero hits on the section 5.2.9 skeleton and reproduces the section 8.5 controls, so the one
   order-placing file does not itself open the order or network path.

Remaining concerns, all minor and non-blocking: the two New-issue observations above; and the genuinely UNVERIFIABLE
Windows facts (does the firewall rule bind the redirector-started interpreter; are F1/F2 identical in standard
precision). The latter are UNVERIFIED by construction (no Windows host in this session) and are gated correctly: R-14
fails closed without a passing and recorded probe, and Revision 3 now gives the owner a diagnostic remedy for a failed
probe. None of these blocks building on the branch.

## Notes

- My scan, controls harness, pin recomputation and string sweep are in `scratch:referee3_security/`
  (`scan_mine.py`, `controls.py`, `pins.py`, `skeleton_spec.py`). `scan_mine.py` is my own transcription of the 5.6
  prose; the one control it misses (`from . import runner` counted as C3 twice) is a double-count in my tool against the
  spec's "at most one hit per AST node" rule, i.e. the spec is correct and my tool is slightly wrong — I did not treat
  it as a spec defect.
- The parent's choice of `importlib.metadata.distribution("nautilus-trader")` over `find_spec` (5.3.2 step 3) is sound:
  `distribution` is not in `IMPORT_MACHINERY`, so the "nautilus-trader" string does not trip rule E, while `find_spec`
  would. The "runner positive" control (`name.startswith('nautilus_trader.adapters')` = none) holds for the same reason.
- The egress probe (`scratch:rev2_probe/egress_probe.py`) imports only `json` and `socket`; `socket` is not in
  `FORBIDDEN_IMPORTS` and `create_connection` is sandbox-only under rule F6, so the probe scans clean as a non-sandbox
  file, matching the section 8.5 "egress probe" control.
- I did not recompute the `RECORD` wheel digests or re-measure the import census this round (round 2 did; they are
  conceded facts). The Windows wheel identity and standard-precision equality remain UNVERIFIED until Step 7A, as the
  spec marks them.
- Moderator-rejected points: none were rejected in rounds 1 or 2 (both rulings say "Rejected: None"), so I re-raised
  nothing. The line growth to 1,663 (+10.9 percent, moderator item C-6) is within the stated budget and the added bulk
  is the skeleton, the Step 7A commands and the synth code that C-5, OPS-R2-1 and QA-R2-12 required.
