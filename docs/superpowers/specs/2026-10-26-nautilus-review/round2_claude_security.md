# Round 2 referee report — Claude, security-engineer lens

Scope of this lens: the order path and isolation. Can any path still send a real order, load credentials, or open a
socket (including from the Rust core), and can the T-RO-01 allow-list widen unnoticed? This round checks whether
Revision 2 applied the round-1 rulings, and looks for new problems the revision introduced.

All probes were read-only, in `scratch:referee2_security/`. No real SPY/BTC data was read. The one network operation I
ran was a TCP connect **inside `unshare -rn`**, which fails by construction (no route), so no egress left the machine.
QUANTGEN is at HEAD `a14954f` (spec commit on `6f7c610`'s line base); `nt:` is `nautilus_trader` 1.231.0 in
`scratch:ntvenv`.

## Verdict

AGREE.

From the isolation lens an engineering team can start building today. My round-1 blocker (SECURITY-1) is resolved the
right way: the design no longer leans on the static scan as the security boundary. OS-level egress control is now in
scope and **mandatory** for every of-record run (§3.12, §4.4), gated by a per-run probe (R-14) and a Step 7A record,
and I verified the Linux layer binds (`unshare -rn` blocks a connect with errno 101, matching §4.4). The scan is
demoted to one of three defence-in-depth layers (§1), the sandbox language restriction (rule F) closes my original
`sys.modules` spelling, path containment (§5.2.8) closes the `.env`-file read, the allow-list is hash-pinned (§5.6),
and the Rust-reachable client classes now trip the deny-list. The two new issues I found are both minor drafting
defects that the test controls or an obvious correction resolve during implementation; neither blocks building.

## Sections reviewed

- §4.4 egress layer (Linux `unshare -rn`, Windows firewalled dedicated interpreter, the probe, the Step 7A record) and
  §3.12; the launch contract §4.3. Verified `unshare -rn true` exits 0 and that a TCP connect under it fails with
  errno 101 (ENETUNREACH), as §4.4 asserts.
- §5.6 the amended T-RO-01 scan: constants, rules A–F, the two pin tests, and every control in §8.5. Checked against
  `tests/macro_m0_harness.py:28-120` (`_offences`, `FORBIDDEN_CALLS`, `FORBIDDEN_IMPORTS`) and `tests/acceptance.py:33-47`
  (`_code_only`), `runtime_py()` (`tests/acceptance.py:50-58`).
- §5.2.2 sandbox imports/language and §5.2.8 path containment; §5.2.5 the BACKTEST guard as a layer.
- §5.2.7 the import census as drift detection; §6.7 venv/wheel identity; §2 O3/O13; §11 risks 1–3, 6, 21; §12.
- Allow-list drift: the two SHA-256 pin tests in §5.6 and the §8.5 control multisets; false-positive sweep of the new
  rule-D regex and denied names across the real tree (0 hits, matching §5.6 rule D "0 hits over 154 files").

## Round-1 issues

- **SECURITY-1 (blocker): resolved.** Egress control is now in scope and mandatory (§3.12, §4.4): Linux `unshare -rn`
  (verified: connect fails errno 101), Windows firewall on a dedicated base interpreter; per-run probe refuses an open
  route (R-14) and of-record also matches the Step 7A record (§4.4, Step 7A done-when). Rule F bans `import sys`,
  module-alias subscripts (F4), dunders (F3) and dynamic calls (F2/F6), closing my `sys.modules[...]` spelling at the
  scan too. The scan is explicitly one of three layers (§1), not the boundary.
- **SECURITY-2 (major): resolved.** §5.2.7 states plainly "the census is drift detection, not a use guard: it cannot
  see use of a module already loaded"; O13 and §11 risks 2–3 now cite the egress layer and rule F for the guarantee.
- **SECURITY-3 (major): resolved.** §5.2.8 `inside()` resolves every opened path and exits 20 if its parent is not the
  temp dir; `open` is banned (F2); file methods only via `inside()` (F5); negative control L2-5 links `input.json` to
  the repo `.env` and expects exit 20. Egress makes any key that is read inert (O3).
- **SECURITY-4 (major): resolved.** Folded into SECURITY-1; "a firewall rule" left §12 (§12 now lists only a Python
  audit hook as out of scope); the Windows firewall rule + Step 7A probe are required contract.
- **SECURITY-5 (major): resolved.** `test_t_ro_01_nautilus_allowlist_pinned` hash-pins `{NAUTILUS_SANDBOX,
  NAUTILUS_ALLOWED_FROM, NAUTILUS_DENIED_PREFIXES, NAUTILUS_DENIED_NAMES, SANDBOX_STDLIB}` and a second dict of the
  rule-F lists. `NAUTILUS_SANDBOX` is a single pinned string and rule C2 exempts only it, so "exactly one exempt file"
  is pinned. Minor residual: the augmentation of `FORBIDDEN_CALLS` by the 7 verbs is not itself hash-pinned, only
  covered by the behavioural control "verbs" in §8.5 — acceptable, since that control fails if the verbs are dropped.
- **SECURITY-6 (minor): resolved.** `NAUTILUS_DENIED_NAME_RE = \w+(Http|WebSocket|Socket|Execution|Data)Client\b`
  plus `api_key`/`api_secret`/`TradingNode`/`LiveNode` were added. The concrete per-venue client classes now match the
  regex. The `nautilus_pyo3.network` `http_*` free functions are still not listed, but are unreachable in the sandbox
  (reaching them needs the `nautilus_pyo3` token → rule D, or an import → C, or `sys.modules` → banned) and inert under
  egress; adequate as defence-in-depth.
- **SECURITY-7 (minor): resolved.** Rule A is now AST-node based (collect every identifier/string containing
  `submit_order`; exempt only the single `Attribute(attr="submit_order")` on `Name("self")` that is a call's `func`
  inside a method), replacing the brittle substring count. Fail-closed on any other occurrence, as the §8.5
  "sandbox string / sandbox receiver / sandbox bare reference" controls require.

## New issues

### SECURITY-R2-1 — minor — §5.6 rule F4, §8.5

Problem. Rule F4 reads "any Subscript whose value is a Name bound by an `import` statement in the file, or an Attribute
chain rooted at one." Read literally, "bound by an import statement" includes `from m import name` (`ImportFrom`)
bindings. Under that reading the sandbox's own `argv[2]` subscript (the §8.5 sandbox-positive control uses
`IN = Path(argv[2])`, and `argv` is bound by `from sys import argv, exit`) becomes an F4 offence, and so does the
`modules[...]` subscript in the "sandbox sys.modules" control. Both contradict the stated control multisets
(sandbox-positive → none; sandbox sys.modules → `C3, E, F1`, with no F4). Only the narrow reading — F4 fires on a
subscript rooted at an `import m` module alias (e.g. `argparse._sys.modules['x']` → F4, as the "sandbox module chain"
control expects) — is consistent with all of §8.5.

Evidence. `scratch:referee2_security/f4_probe.py`: with `from sys import argv, exit; import argparse`, the chain-root of
`argv[2]` is `argv` (ImportFrom-bound) and of `argparse._sys.modules['x']` is `argparse` (Import-bound). Under the broad
reading `argv[2]` is an F4 hit; under the narrow reading it is not, while `argparse._sys.modules['x']` is a hit under
both. The §8.5 controls and the Step 4 done-when ("the real sandbox gives no hit") are satisfiable only by the narrow
reading. A literal implementation would break the sandbox's own argument parsing.

Proposed fix. Reword F4: "any Subscript whose value is a Name bound by an `import <module>` statement (a module alias),
or an Attribute chain rooted at such a Name." The §8.5 controls already force this reading, so the risk is a reader
implementing the prose literally, not a hole; no evasion is opened by the narrow reading (module aliases are the only
names that can index to `sys.modules`-style objects, and `from sys import modules` is already blocked by C3 + F1).

### SECURITY-R2-2 — minor — §5.6 (NAUTILUS_BRIDGE_ONLY_NAMES comment), Appendix B

Problem. The `api_key`/`api_secret` carve-out (denied under `tools/nautilus/` only) is justified by a citation to
`data/fmp/quote_client.py:64-65` "uses `api_key`". That file does use `api_key`, but at lines 110 and 115
(`def __init__(self, *, api_key=None, ...)` and `self._key = api_key ...`); lines 64-65 are `FMPQuote` dataclass fields
(`change_pct`, `volume`). The substance is correct and the carve-out is necessary — `data/` is scanned by
`runtime_py()` (`tests/acceptance.py:50-58`), so denying `api_key` in every file (rule D) would false-positive on
`quote_client.py` — only the line numbers are wrong, in two places (§5.6 constant comment and the Appendix B
SECURITY-6 application note).

Evidence. `grep -n 'api_key' data/fmp/quote_client.py` → lines 110, 115 only. `runtime_py()` scans `core/`, `data/`,
`ui/`, `main.py`, `config.py`; `_scan_files` includes `runtime_py()` (`tests/macro_m0_harness.py:70-74`).

Proposed fix. Cite `data/fmp/quote_client.py:110,115`.

## Notes

- The BACKTEST guard (§5.2.5) is listed in §1 as one of "three independent layers". It is sandbox-author-defeatable:
  the guard tests `isinstance(self.clock, TestClock)`, and `clock` is not a dunder, so a sandbox line
  `self.clock = TestClock()` would not trip rule F (F3 covers only `__`-prefixed attributes) and `TestClock` is an
  allowed import. This is only effective against an accidental live start, not a deliberate one. The spec is candid
  that egress is the real boundary ("The static scan cannot bind the Rust core; the OS does", §4.4), and egress binds
  the live transmit regardless, so this is within the honest-author threat model and not an issue — but the §1 wording
  "keep orders inside the process" leans on egress, not on the guard, and could say so.
- The Windows firewall rule is placed on the dedicated base interpreter `py313\python.exe`, which is correct for a
  redirector venv (the real CPython process image is the base, launched by the Scripts redirector), and the spec marks
  the binding UNVERIFIED until the Step 7A probe and refuses of-record without it (R-14). This is the right structure;
  the only residual is that if the probe fails on the owner's machine the runbook gives no remedy (e.g. also add a rule
  on the venv `Scripts\python.exe`). Step 7A is a human loop, so I leave it as a note.
- The runner's `--egress-record` makes one real outbound connect (`control_connect` to 1.1.1.1:443) from the
  **global** interpreter to prove the firewall blocks the venv but not the host. It is deliberate, single, documented,
  and only in that mode; acceptable.
- The two SHA-256 pin values in §5.6 (`2792ad4a...`, `70bcf50f...`) are self-checking at Step 4 (the test fails if the
  committed constants do not hash to them); I did not recompute them (UNVERIFIED), which is harmless because a mismatch
  fails closed on the first run.
- Rule-D false-positive sweep: the new regex `\w+(...)Client\b` and the new denied names (`TradingNode`,
  `TradingNodeConfig`, `LiveNode`, `SandboxExecutionClient`, `api_secret`, …) produce 0 matches across
  `core/ data/ ui/ tools/ papers/ main.py config.py docs/*.py`, consistent with §5.6 rule D "0 hits".
- The pyo3 fact underlying my round-1 blocker (35 compiled network/venue submodules load with `BacktestEngine`) is
  conceded by the spec (O13) and no longer disputed; the fix is egress, not unloading them, which I verified is sound
  on Linux.
