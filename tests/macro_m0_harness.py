"""M0 harness tests: T-RO-01 static read-only scan, the test registry, the fixture manifest loader and the
NOT_RUN status (TASK-M0-01, M0-02, M0-03; spec P0, section 9, section 9.5; section 10 item 21).

Every test is a zero-argument callable; `tests/macro_acceptance.py` discovers and wraps them. Tests that
implement a spec test carry `test_ids`.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import tempfile
from pathlib import Path

from tests.acceptance import _code_only, runtime_py
from tests.notrun import MANIFEST, MANIFEST_COLUMNS, NotRun, load_manifest, md5_of, require_fixture, unlisted

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "macro_registry.csv"
SPEC = ROOT / "QUANTGEN_Quant_Council_2026-10-03" / "claude_code" / "QUANTGEN_MACRO_INTEGRATION.md"
TEST_ID = re.compile(r"\b(?:T-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+[a-z]?|I-\d+[a-z]?|G-[A-Z0-9]+-[A-Z0-9]*\d[a-z]?)\b")

# --------------------------------------------------------------------------- #
# T-RO-01: the forbidden surface, listed here (spec L5605; constitution B.7)
# --------------------------------------------------------------------------- #
# Case-insensitive substrings of the executable surface (docstrings and comments stripped).
FORBIDDEN_TEXT_CI = (
    "order_cash", "order-cash", "place_order", "submit_order",        # KIS order endpoints and verbs
    "tttc0802u", "tttc0801u", "vttc0802u",                           # KIS order TR ids
    "/v1/orders", "/v1/withdraws", "/v1/deposits/generate_coin_address",   # Upbit
    "/api/v3/order", "/sapi/v1/capital/withdraw", "/sapi/v1/capital/deposit",  # Binance
    "private_key", "seed_phrase",
)
FORBIDDEN_TEXT_CS = ("KIS_ACCOUNT", "CANO", "ACNT_PRDT_CD")           # an account number implies an order path
FORBIDDEN_PATH_RE = re.compile(r"/uapi/[^\s'\"]*/trading/")           # every KIS trading domain
# Top-level modules of order-submission clients; an import anywhere fails.
FORBIDDEN_IMPORTS = frozenset({
    "ccxt", "web3", "pyupbit", "binance", "python_binance", "ib_insync", "alpaca", "alpaca_trade_api",
    "mojito", "pykis", "kiwoom", "okx", "bybit", "kucoin", "coinbase", "cbpro", "MetaTrader5", "oandapyV20",
    "eth_account", "bitcoinlib", "bitcoin",
})
# Call names of order, cancel, withdrawal, deposit-address and transfer paths (attribute or bare calls).
FORBIDDEN_CALLS = frozenset({
    "place_order", "submit_order", "create_order", "send_order", "new_order", "order_cash", "cancel_order",
    "create_market_order", "create_limit_order", "buy_market_order", "sell_market_order",
    "buy_limit_order", "sell_limit_order", "withdraw", "withdraw_coin", "withdraw_krw", "create_withdrawal",
    "transfer", "transfer_funds", "deposit_address", "get_deposit_address", "create_deposit_address",
    "fetch_deposit_address", "generate_coin_address", "sign_transaction", "send_transaction", "send_raw_transaction",
})
MUTATING_HTTP = frozenset({"post", "put", "delete", "patch"})
MUTATING_URL_WORDS = ("order", "withdraw", "transfer", "deposit")
# The simulated order book API (core/engine/orders.py) and its UI handlers are the only legitimate
# order-shaped names: OrderBook.place/fill/cancel/reject/cancel_all_open, Evaluator.sweep_cancellations,
# and the bare `fill_order` / `cancel_order` handlers of ui/trading_page.py that call `runtime.book`.
ALLOWED_BARE_CALLS = {"ui/trading_page.py": {"fill_order", "cancel_order"}}
# T-RO-01 amendment for the NautilusTrader bridge (spec 2026-10-26 section 5.6, owner ruling O2; outside the branch it
# takes effect only after the owner's sign-off sentence). The rules A to F live in `_nautilus_offences` below.
NAUTILUS_SANDBOX = "tools/nautilus/sandbox.py"   # the one file that may place simulated orders (spec 2026-10-26 §5.6)
NAUTILUS_ALLOWED_FROM = {                          # sandbox only: module -> the names it may import
    "nautilus_trader.backtest.engine": frozenset({"BacktestEngine"}),
    "nautilus_trader.backtest.models": frozenset({"FeeModel", "FillModel"}),
    "nautilus_trader.common": frozenset({"Environment"}),
    "nautilus_trader.common.component": frozenset({"LiveClock", "TestClock", "is_backtest_force_stop"}),
    "nautilus_trader.config": frozenset({"BacktestEngineConfig", "LoggingConfig", "StrategyConfig"}),
    "nautilus_trader.model.currencies": frozenset({"BTC", "USD"}),
    "nautilus_trader.model.data": frozenset({"Bar", "BarType"}),
    "nautilus_trader.model.enums": frozenset({"AccountType", "OmsType", "OrderSide", "TimeInForce"}),
    "nautilus_trader.model.identifiers": frozenset({"InstrumentId", "Symbol", "TraderId", "Venue"}),
    "nautilus_trader.model.instruments": frozenset({"CurrencyPair", "Equity"}),
    "nautilus_trader.model.objects": frozenset({"FIXED_PRECISION", "HIGH_PRECISION", "Money", "PRICE_MAX", "Price",
                                                "QUANTITY_MAX", "Quantity"}),
    "nautilus_trader.trading.strategy": frozenset({"Strategy"}),
}
NAUTILUS_DENIED_PREFIXES = ("nautilus_trader.live", "nautilus_trader.adapters", "nautilus_trader.network",
                            "nautilus_trader.core.nautilus_pyo3", "nautilus_trader.backtest.node", "nautilus_pyo3")
NAUTILUS_DENIED_NAMES = frozenset({
    "TradingNode", "TradingNodeBuilder", "TradingNodeConfig", "LiveNode", "LiveExecClientConfig",
    "LiveDataClientConfig", "SandboxExecutionClient", "get_env_key", "get_env_key_or", "HttpClient",
    "WebSocketClient", "SocketClient", "nautilus_pyo3", "api_key", "api_secret"})
NAUTILUS_BRIDGE_ONLY_NAMES = frozenset({"api_key", "api_secret"})   # denied under tools/nautilus/ only:
                                                                     # data/fmp/quote_client.py:110, 115 use api_key
NAUTILUS_DENIED_NAME_RE = re.compile(r"\w+(Http|WebSocket|Socket|Execution|Data)Client\b")
NAUTILUS_ORDER_VERBS = frozenset({"modify_order", "cancel_orders", "cancel_all_orders", "close_position",
                                  "close_all_positions", "market_exit", "submit_order_list"})
IMPORT_MACHINERY = frozenset({"import_module", "__import__", "find_spec", "spec_from_file_location",
                              "module_from_spec", "run_module", "run_path", "resolve_name", "get_loader",
                              "find_loader", "reload"})
SANDBOX_STDLIB = {"argparse": None, "csv": None, "hashlib": None, "json": None, "math": None, "platform": None,
                  "decimal": frozenset({"Decimal", "ROUND_FLOOR"}), "pathlib": frozenset({"Path"}),
                  "sys": frozenset({"argv", "exit"})}           # None: `import m`; a set: `from m import <names>`
SANDBOX_BANNED_MODULES = frozenset({"asyncio", "builtins", "ctypes", "gc", "http", "importlib", "inspect", "os",
                                    "socket", "ssl", "subprocess", "sys", "types", "urllib"})
SANDBOX_BANNED_NAMES = frozenset({"getattr", "setattr", "delattr", "vars", "globals", "locals", "eval", "exec",
                                  "compile", "__import__", "breakpoint", "open"})
SANDBOX_FILE_METHODS = frozenset({"open", "read_text", "read_bytes", "write_text", "write_bytes", "touch", "mkdir",
                                  "unlink", "rmdir", "rename", "replace", "symlink_to", "hardlink_to", "iterdir",
                                  "glob", "rglob", "chmod"})
SANDBOX_OS_CALLS = frozenset({"system", "popen", "startfile", "fork", "kill", "execl", "execv", "execve", "execvp",
                              "spawnl", "spawnlp", "spawnv", "spawnve", "posix_spawn", "posix_spawnp", "Popen",
                              "check_call", "check_output", "create_connection", "urlopen"})
FORBIDDEN_CALLS = FORBIDDEN_CALLS | NAUTILUS_ORDER_VERBS   # rule B: the 7 verbs are forbidden in every file, sandbox too
# Only the engine package (and the macro engine feed named in the rulings) may import the book itself, plus the
# paper studies under papers/, which may read the simulated fill model (spec 2026-10-23 section 3.4). An entry ending
# in "/" is a folder, the others are single files; `rel.startswith(ORDERS_IMPORTERS_ALLOWED)` covers both.
ORDERS_IMPORTERS_ALLOWED = ("core/engine/", "core/skills/macro_daily.py", "core/skills/pipeline.py", "papers/")
ORDERS_NAMES = {"OrderBook", "SimulatedOrder", "OrderStatus", "order_id"}
WORKFLOW_YAML = ROOT / "core" / "skills" / "macro_workflows"
SCAN_TREES = ("tools", "papers")          # the paper pipeline and the paper studies (spec 2026-10-23 section 3.4)


def _scan_files(root: Path = ROOT) -> list[Path]:
    files = runtime_py() + sorted(p for p in (root / "docs").glob("*.py"))
    for top in SCAN_TREES:
        files += sorted(p for p in (root / top).rglob("*.py") if "__pycache__" not in p.parts)
    return [p for p in files if p.is_file()]


def _strings_in(node: ast.AST) -> list[str]:
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append(sub.value)
    return out


def _offences(path: Path, root: Path = ROOT) -> list[str]:
    rel = path.relative_to(root).as_posix()
    code = _code_only(path)
    low = code.lower()
    hits = [f"{rel}: {n!r}" for n in FORBIDDEN_TEXT_CI if n in low]
    hits += [f"{rel}: {n!r}" for n in FORBIDDEN_TEXT_CS if n in code]
    hits += [f"{rel}: {m.group(0)!r}" for m in FORBIDDEN_PATH_RE.finditer(code)]
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    hits.append(f"{rel}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                hits.append(f"{rel}:{node.lineno}: from {node.module} import ...")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                if func.attr in FORBIDDEN_CALLS:
                    hits.append(f"{rel}:{node.lineno}: .{func.attr}()")
                if func.attr in MUTATING_HTTP:
                    urls = " ".join(_strings_in(node)).lower()
                    if any(w in urls for w in MUTATING_URL_WORDS):
                        hits.append(f"{rel}:{node.lineno}: .{func.attr}() on an order/withdraw/transfer/deposit URL")
            elif isinstance(func, ast.Name) and func.id in FORBIDDEN_CALLS:
                if func.id not in ALLOWED_BARE_CALLS.get(rel, set()):
                    hits.append(f"{rel}:{node.lineno}: {func.id}()")
    return _nautilus_offences(tree, rel, hits)


# --------------------------------------------------------------------------- #
# T-RO-01 amendment: rules A to F for the NautilusTrader bridge (spec 2026-10-26 section 5.6)
# --------------------------------------------------------------------------- #
def _import_names(node: ast.Import | ast.ImportFrom, rel: str) -> list[str]:
    """Full dotted names (spec 2026-10-26 section 5.6): `import a.b.c` names a.b.c; `from m import n` names m and m.n;
    a relative import resolves against the file's package."""
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    module = node.module or ""
    if node.level:
        package = rel.split("/")[:-1]
        package = package[:max(len(package) - (node.level - 1), 0)]
        module = ".".join(package + ([module] if module else []))
    return [module] + [f"{module}.{a.name}" for a in node.names]


def _denied_module(name: str) -> bool:
    return any(name == p or name.startswith(p + ".") for p in NAUTILUS_DENIED_PREFIXES)


def _denied_name(name: str | None, bridge: bool) -> bool:
    """In NAUTILUS_DENIED_NAMES (NAUTILUS_BRIDGE_ONLY_NAMES only under tools/nautilus/), or matching the client pattern."""
    if not name:
        return False
    if name in NAUTILUS_BRIDGE_ONLY_NAMES:
        return bridge
    return name in NAUTILUS_DENIED_NAMES or NAUTILUS_DENIED_NAME_RE.search(name) is not None


def _identifiers(node: ast.AST) -> tuple[str | None, ...]:
    """What rule A reads on one node: a Name, Attribute, function or class name, arg, keyword, import alias or string."""
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (node.attr,)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return (node.name,)
    if isinstance(node, (ast.arg, ast.keyword)):
        return (node.arg,)
    if isinstance(node, ast.alias):
        return (node.name, node.asname)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    return ()


def _rule_a(tree: ast.AST, rel: str, hits: list[str]) -> list[str]:
    """Rule A (SECURITY-7), sandbox only. No node names submit_order: no hit (ruling T1 CI 7). Exactly one, and it is
    `self.submit_order` called with a method (a def directly in a class body) as its nearest enclosing def or lambda:
    its text hit and its call hit are dropped. Otherwise every hit stands, plus one A hit."""
    found = [n for n in ast.walk(tree) if any("submit_order" in (s or "").lower() for s in _identifiers(n))]
    if not found:
        return hits
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    node, call = found[0], parents.get(found[0])
    method = call
    while method is not None and not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        method = parents.get(method)
    if (len(found) == 1 and isinstance(node, ast.Attribute) and node.attr == "submit_order"
            and isinstance(node.value, ast.Name) and node.value.id == "self"
            and isinstance(call, ast.Call) and call.func is node
            and method is not None and isinstance(parents.get(method), ast.ClassDef)):
        return [h for h in hits if h not in (f"{rel}: 'submit_order'", f"{rel}:{call.lineno}: .submit_order()")]
    return hits + [f"[nautilus:A] {rel}:{getattr(node, 'lineno', 0)}: {len(found)} node(s) name submit_order; only one "
                   "self.submit_order call in one method is exempt"]


def _import_rules(node: ast.Import | ast.ImportFrom, rel: str, sandbox: bool, bridge: bool) -> list[str]:
    """Rules C1, C2, C3 and F1 on one import statement."""
    where, names = f"{rel}:{node.lineno}", _import_names(node, rel)
    aliases = [n for a in node.names for n in (a.name, a.asname) if n]
    out = []
    if any(_denied_module(n) for n in names) or any(_denied_name(a, bridge) for a in aliases):
        out.append(f"[nautilus:C1] {where}: denied module or name in {names}")
    if not sandbox:
        if any(n == "nautilus_trader" or n.startswith("nautilus_trader.") for n in names):
            out.append(f"[nautilus:C2] {where}: nautilus_trader imported outside {NAUTILUS_SANDBOX}")
        return out
    if isinstance(node, ast.Import):
        allowed = all(a.name in SANDBOX_STDLIB and SANDBOX_STDLIB[a.name] is None and not a.asname for a in node.names)
        tops = {a.name.split(".")[0] for a in node.names}
    else:
        pool = NAUTILUS_ALLOWED_FROM.get(node.module) or SANDBOX_STDLIB.get(node.module) or frozenset()
        allowed = not node.level and all(a.name in pool and not a.asname for a in node.names)
        tops = set() if node.level else {(node.module or "").split(".")[0]}
    if not allowed:
        out.append(f"[nautilus:C3] {where}: sandbox import outside the allow-list: {names}")
    from_sys = (isinstance(node, ast.ImportFrom) and node.module == "sys"
                and all(a.name in SANDBOX_STDLIB["sys"] for a in node.names))
    if tops & SANDBOX_BANNED_MODULES and not from_sys:
        out.append(f"[nautilus:F1] {where}: banned module {sorted(tops & SANDBOX_BANNED_MODULES)}")
    return out


def _node_rules(node: ast.AST, rel: str, sandbox: bool, bridge: bool, modules: set[str]) -> list[str]:
    """Rules D, E and F2 to F6 on one AST node; `modules` are the names the file binds with `import m`."""
    where, out = f"{rel}:{getattr(node, 'lineno', 0)}", []
    ident = (node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute)
             else node.arg if isinstance(node, (ast.arg, ast.keyword)) else None)
    if _denied_name(ident, bridge):
        out.append(f"[nautilus:D] {where}: denied name {ident}")
    if isinstance(node, ast.Call):
        func = node.func
        callee = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if callee in IMPORT_MACHINERY and (sandbox or any("nautilus" in s for s in _strings_in(node))):
            out.append(f"[nautilus:E] {where}: import machinery {callee}()")
        if sandbox and isinstance(func, ast.Attribute) and func.attr in SANDBOX_FILE_METHODS and not (
                isinstance(func.value, ast.Call) and isinstance(func.value.func, ast.Name)
                and func.value.func.id == "inside"):
            out.append(f"[nautilus:F5] {where}: .{func.attr}() on a path that inside() did not build")
        if sandbox and callee in SANDBOX_OS_CALLS:
            out.append(f"[nautilus:F6] {where}: process or socket call {callee}()")
    if not sandbox:
        return out
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and any(
            entry in node.value for entry in (*NAUTILUS_DENIED_PREFIXES, *NAUTILUS_DENIED_NAMES)):
        out.append(f"[nautilus:E] {where}: denied module or name in a string")
    if isinstance(node, ast.Name) and node.id in SANDBOX_BANNED_NAMES:
        out.append(f"[nautilus:F2] {where}: {node.id}")
    if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
        out.append(f"[nautilus:F3] {where}: .{node.attr}")
    if isinstance(node, ast.Subscript):
        value = node.value
        while isinstance(value, ast.Attribute):
            value = value.value
        if isinstance(value, ast.Name) and value.id in modules:
            out.append(f"[nautilus:F4] {where}: subscript on the module {value.id}")
    return out


def _nautilus_offences(tree: ast.AST, rel: str, hits: list[str]) -> list[str]:
    """Rules A to F of spec 2026-10-26 section 5.6 on one parsed file. `hits` are the file's existing T-RO-01 hits,
    which keep their form (rule A may drop its two exempt ones); every new hit starts with `[nautilus:<rule>]`, and
    each rule adds at most one hit per AST node it inspects."""
    sandbox, bridge = rel == NAUTILUS_SANDBOX, rel.startswith("tools/nautilus/")
    if sandbox:
        hits = _rule_a(tree, rel, hits)
    modules = {a.asname or a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    out = list(hits)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out += _import_rules(node, rel, sandbox, bridge)
        out += _node_rules(node, rel, sandbox, bridge, modules)
    return out


def _yaml_offences(path: Path) -> list[str]:
    import yaml
    rel = path.relative_to(ROOT).as_posix()
    hits = []

    def walk(value):
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
        elif isinstance(value, str):
            low = value.lower()
            hits.extend(f"{rel}: {n!r}" for n in FORBIDDEN_TEXT_CI if n in low)
            hits.extend(f"{rel}: {n!r}" for n in FORBIDDEN_TEXT_CS if n in value)
            hits.extend(f"{rel}: {m.group(0)!r}" for m in FORBIDDEN_PATH_RE.finditer(value))
            words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", value))
            hits.extend(f"{rel}: {w}" for w in sorted(words & (FORBIDDEN_CALLS | FORBIDDEN_IMPORTS)))

    walk(yaml.safe_load(path.read_text(encoding="utf-8")))
    return hits


def test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path():
    """Static scan of core/, data/, ui/, config.py, main.py, docs/*.py, tools/, papers/ and the macro workflow YAML."""
    files = _scan_files()
    assert len(files) > 50, "scan scope collapsed"
    hits = [h for p in files for h in _offences(p)]
    if WORKFLOW_YAML.is_dir():
        hits += [h for p in sorted(WORKFLOW_YAML.glob("*.yaml")) for h in _yaml_offences(p)]
    assert not hits, "order path surface present:\n  " + "\n  ".join(hits)


test_t_ro_01_no_order_cancel_withdrawal_or_transfer_path.test_ids = ["T-RO-01"]


def test_t_ro_01_orders_module_reached_only_through_the_engine():
    """`core/engine/orders` is imported only inside the engine package (plus the macro engine feed and the paper
    studies under papers/)."""
    offenders = []
    for path in _scan_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(ORDERS_IMPORTERS_ALLOWED):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(a.name == "core.engine.orders" for a in node.names):
                offenders.append(f"{rel}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "core.engine.orders" or (
                        node.module == "core.engine" and {a.name for a in node.names} & ORDERS_NAMES):
                    offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, f"core.engine.orders imported outside the engine: {offenders}"
    api = ast.parse((ROOT / "core/engine/orders.py").read_text(encoding="utf-8"))
    book = next(n for n in api.body if isinstance(n, ast.ClassDef) and n.name == "OrderBook")
    methods = {n.name for n in book.body if isinstance(n, ast.FunctionDef)}
    assert {"place", "fill", "cancel", "reject", "cancel_all_open"} <= methods, methods


test_t_ro_01_orders_module_reached_only_through_the_engine.test_ids = ["T-RO-01"]


def test_t_ro_01_scan_reaches_tools_and_papers():
    """The order-path scan covers the paper pipeline (tools/) and the paper studies (papers/), and papers/ is the only
    new allowed importer of the simulated book (spec 2026-10-23 section 3.4)."""
    probes = {"tools/paper/probe.py": "def f(client):\n    return client.place_order(1)\n",
              "papers/2026-01-01-probe/study/run.py": "import ccxt\n",
              "papers/2026-01-01-probe/study/__pycache__/stale.py": "import ccxt\n"}
    with tempfile.TemporaryDirectory() as name:
        tmp = Path(name)
        for rel, text in probes.items():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text(text, encoding="utf-8")
        scanned = sorted(p.relative_to(tmp).as_posix() for p in _scan_files(tmp) if tmp in p.parents)
        assert scanned == ["papers/2026-01-01-probe/study/run.py", "tools/paper/probe.py"], scanned
        hits = [h for rel in scanned for h in _offences(tmp / rel, tmp)]
    assert any(".place_order()" in h for h in hits) and any("import ccxt" in h for h in hits), hits
    assert "papers/2026-01-01-probe/study/run.py".startswith(ORDERS_IMPORTERS_ALLOWED)
    assert not "tools/paper/study.py".startswith(ORDERS_IMPORTERS_ALLOWED)
    assert any(p.relative_to(ROOT).as_posix().startswith("tools/") for p in _scan_files()), "the real tools/ tree is not scanned"


# The 5.2.9 skeleton of tools/nautilus/sandbox.py, verbatim from spec 2026-10-26: the sandbox positive control of 8.5
# and the base of every "sandbox +" control (measured with scratch:rev4_probe/scan4.py).
_SANDBOX_SKELETON = '''import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy

VENUE = Venue("SIM")
class Refused(Exception): pass                     # input refused before the engine is built: exit 20
def inside(root, name):                             # 5.2.8: builds every path the sandbox opens
    p = (root / name).resolve()
    if p.parent != root:
        raise Refused(name)
    return p
def plain_mean(xs):                                 # 5.2.5, both ports: a left-to-right loop, never sum()
    total = 0.0
    for x in xs:
        total += x
    return total / len(xs)
def require_backtest_environment(env):              # 5.2.5 (C-2)
    if env is not Environment.BACKTEST:
        raise RuntimeError(f"kernel environment {env.name}, not BACKTEST")
def require_backtest_clock(clock):
    if not isinstance(clock, TestClock):
        raise RuntimeError("the strategy clock is not a TestClock")
def make_fee_model(cost_bps, stress):               # 5.2.3: a closure, so no __init__ and no super()
    if Decimal(stress) < 1:
        raise ValueError("stress below 1")
    rate = Decimal(cost_bps) * Decimal(stress) / Decimal(10000)
    class BpFeeModel(FeeModel):
        def get_commission(self, order, fill_qty, fill_px, instrument):
            return Money(fill_qty.as_decimal() * fill_px.as_decimal() * instrument.multiplier.as_decimal() * rate,
                         instrument.quote_currency)
    return BpFeeModel()
def build_engine():                                 # 5.2.3, rows Engine and Kernel check
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId("QGBRIDGE-001"), run_analysis=False,
                                                 logging=LoggingConfig(log_level="ERROR", log_colors=False)))
    require_backtest_environment(engine.kernel.environment)
    return engine
class PortConfig(StrategyConfig, frozen=True):      # every parameter lives here, never in an __init__ (rule F3)
    instrument_id: str; bar_type: str; cost_bps: str; stress: str
    closes: list; ts: list                          # the close strings of bars.csv and their ts_ns
class TrendSwitchConfig(PortConfig, frozen=True):
    rule: str; lookback: int; step: int
class CryptoTrendConfig(PortConfig, frozen=True):
    hysteresis: float; lookbacks: list; mas: list
class Port(Strategy):                               # no __init__: Strategy's own stores the config
    def on_start(self):
        require_backtest_clock(self.clock)          # first statement (C-15)
        self.iid = InstrumentId.from_str(self.config.instrument_id)
        self.inst = self.cache.instrument(self.iid)
        self.px = [float(c) for c in self.config.closes]
        self.i, self.held, self.fills, self.decisions, self.equity, self.invalid_reasons = -1, 0, [], [], [], []
        self.denied = self.rejected = 0
        self.subscribe_bars(BarType.from_str(self.config.bar_type))
        self.strategy_started = True                # last statement (C-15)
    def on_bar(self, bar):                          # never raises: Nautilus re-raises, which ends the child
        self.i += 1
        if bar.ts_event != self.config.ts[self.i] or bar.close != Price.from_str(self.config.closes[self.i]):
            self.invalid_reasons.append(f"C-12: bar {self.i} differs from bars.csv")   # id first (QA-R3-8)
            return
        ...                                         # one onbar_equity row; decision, margin = self.decide(self.i)
        ...                                         # in-flight check (C-13); side and fee-inclusive Decimal q (5.2.5)
        self.place(self.order_factory.market(self.iid, side, Quantity(q, self.inst.size_precision),
                                             time_in_force=TimeInForce.GTC))
    def place(self, order):                         # the one exempt call (5.6 rule A)
        self.submit_order(order)
    def on_order_filled(self, ev):                  # one fills.csv row (5.2.6)
        ...
    def on_order_denied(self, ev): self.denied += 1
    def on_order_rejected(self, ev): self.rejected += 1
class TrendSwitchPort(Port):
    def decide(self, i):                            # -> (decision or None, margin), the table of 5.2.5
        ...
class CryptoTrendPort(Port):
    def decide(self, i):
        ...
def run(root):                                      # exit 0, 10 or 20 (5.2.1)
    inp = json.loads(inside(root, "input.json").read_text(encoding="utf-8"))
    ...                                             # every rule of 6.1, one by one (L2-5a): raise Refused
    engine = build_engine()
    engine.add_venue(..., fee_model=make_fee_model(inp["cost_bps"], inp["stress"]), allow_cash_borrowing=False)
    ...                                             # add_instrument; add_data (5.2.4); port.strategy_started = False;
    engine.run()                                    # add_strategy(TrendSwitchPort(TrendSwitchConfig(...))) or crypto
    ...                                             # 5.2.7 checks as "C-nn: ..." reasons; 5.2.6's files; dispose
    return 0 if valid else 10
def check_env():                                    # --check-env: one JSON line, no file (5.2.1)
    engine = build_engine()
    u = platform.uname()                            # not platform.system(): rule F6 flags any call named system
    print(json.dumps({"schema": "nautilus-bridge-check-env/1", "python": platform.python_version(),
                      "system": u.system, "machine": u.machine, "environment": engine.kernel.environment.name,
                      "precision": {"HIGH_PRECISION": HIGH_PRECISION, "FIXED_PRECISION": FIXED_PRECISION,
                                    "QUANTITY_MAX": QUANTITY_MAX, "PRICE_MAX": PRICE_MAX}}))
    engine.dispose()
    return 0
def guard_selftest():                               # --guard-selftest: exit 0, or 30 on a wrong outcome (5.2.1)
    out = {}
    env, clock = require_backtest_environment, require_backtest_clock
    for name, fn, arg in (("sandbox", env, Environment.SANDBOX), ("live", env, Environment.LIVE),
                          ("live_clock", clock, LiveClock()), ("backtest", env, Environment.BACKTEST),
                          ("test_clock", clock, TestClock())):
        try:
            fn(arg)
            out[name] = "passed"
        except RuntimeError:
            out[name] = "raised"
    print(json.dumps(out, sort_keys=True))
    return 0 if list(out.values()) == ["raised"] * 3 + ["passed"] * 2 else 30
def main():
    ap = argparse.ArgumentParser(prog="sandbox.py")
    ap.add_argument("--check-env", action="store_true"); ap.add_argument("--guard-selftest", action="store_true")
    ap.add_argument("mode", nargs="?", choices=["run"])
    ap.add_argument("--in", dest="in_dir", default="")
    a = ap.parse_args(argv[1:])
    if a.check_env or a.guard_selftest:
        return check_env() if a.check_env else guard_selftest()
    root = Path(a.in_dir)
    if a.mode != "run" or not root.is_absolute() or root != root.resolve():
        return 20
    try:
        return run(root)
    except Refused:
        return 20
if __name__ == "__main__":                          # SECURITY-R3-1: __name__ is a Name, not an Attribute (F3)
    exit(main())
'''


def _with(code: str) -> str:
    """The skeleton plus `code`, inserted before its `if __name__` guard (spec 8.5, "sandbox +")."""
    guard = '\nif __name__ == "__main__":'
    assert _SANDBOX_SKELETON.count(guard) == 1
    return _SANDBOX_SKELETON.replace(guard, "\n" + code + guard, 1)


def _tag(hit: str) -> str:
    """A hit's tag in spec 8.5: the rule of a `[nautilus:<rule>]` hit, TEXT for a FORBIDDEN_TEXT_CI hit, CALL for a
    FORBIDDEN_CALLS hit; any other hit is its own text, so a comparison that fails shows it."""
    rule = re.match(r"\[nautilus:(\w+)\] ", hit)
    if rule:
        return rule.group(1)
    if any(hit.endswith(f": {n!r}") for n in FORBIDDEN_TEXT_CI):
        return "TEXT"
    call = re.search(r":\d+: \.?(\w+)\(\)$", hit)
    return "CALL" if call and call.group(1) in FORBIDDEN_CALLS else hit


def _nautilus_controls() -> list[tuple[str, str, str, dict[str, int]]]:
    """(label, path, content, expected tags) for each of the 51 controls of spec 8.5."""
    sb = NAUTILUS_SANDBOX
    verbs = "def verbs(self):\n" + "".join(f"    self.{v}(1)\n" for v in sorted(NAUTILUS_ORDER_VERBS))
    probe = (ROOT / "tools" / "nautilus" / "egress_probe.py").read_text(encoding="utf-8")
    controls = [
        ("sandbox positive", sb, _SANDBOX_SKELETON, {}),
        ("runner positive", "tools/nautilus/runner.py",
         "def bad(name):\n    return name.startswith('nautilus_trader.adapters')\n", {}),
        ("egress probe", "tools/nautilus/egress_probe.py", probe, {}),
        ("key outside the bridge", "data/fmp/probe_key.py", "def f(api_key):\n    return api_key\n", {}),
        ("live leak", "tools/nautilus/live_leak.py",
         "from nautilus_trader.live.node import TradingNode\nimport nautilus_trader.adapters.binance\n"
         "from nautilus_trader.core import nautilus_pyo3\nnode = TradingNode(cfg)\nnode.run()\n",
         {"C1": 3, "C2": 3, "D": 1}),
        ("dynamic", "tools/nautilus/dynamic.py",
         "import importlib\nimportlib.import_module('nautilus_trader.adapters.betfair')\n", {"E": 1}),
        ("outside import", "core/quant/nt_runner.py", "from nautilus_trader.backtest.engine import BacktestEngine\n",
         {"C2": 1}),
        ("outside submit", "tools/nautilus/other_submit.py", "def f(s, o):\n    s.submit_order(o)\n",
         {"TEXT": 1, "CALL": 1}),
        ("Rust client name", "tools/nautilus/client.py",
         "def f(m):\n    return m.BybitHttpClient(api_key='x', api_secret='y')\n", {"D": 3}),
        ("verbs", sb, _with(verbs), {"A": 1, "CALL": 8, "TEXT": 1}),
        ("sandbox receiver", sb, _with("def other_call(other, o):\n    other.submit_order(o)\n"),
         {"A": 1, "CALL": 2, "TEXT": 1}),
        ("sandbox bare reference", sb, _with("def ref(self):\n    f = self.submit_order\n    return f\n"),
         {"A": 1, "CALL": 1, "TEXT": 1}),
        ("sandbox string", sb, _with("NAME = 'submit_order'\n"), {"A": 1, "CALL": 1, "TEXT": 1}),
        ("sandbox bare import", sb, _with("import nautilus_trader\n"), {"C3": 1}),
        ("sandbox denied name", sb, _with("from nautilus_trader.config import TradingNodeConfig\n"),
         {"C1": 1, "C3": 1}),
        ("sandbox relative", sb, _with("from . import runner\n"), {"C3": 1}),
        ("sandbox sys.modules", sb,
         _with("from sys import modules\nnet = modules['nautilus_trader.core.' + 'nautilus_pyo3']\n"),
         {"C3": 1, "E": 1, "F1": 1}),
        ("sandbox module chain", sb, _with("net = argparse._sys.modules['x']\n"), {"F4": 1}),
        ("sandbox __dict__", sb, _with("d = Port.__dict__\n"), {"F3": 1}),
        ("sandbox getattr", sb, _with("def g(self, o):\n    getattr(self, 'sub' + 'mit_order')(o)\n"), {"F2": 1}),
        ("sandbox open", sb, _with("def leak():\n    return open('/repo/.env').read()\n"), {"F2": 1}),
        ("sandbox path", sb, _with("def leak():\n    return Path('/repo/.env').read_text()\n"), {"F5": 1}),
        ("sandbox os call", sb, _with("def run_os():\n    platform.os.system('x')\n"), {"F6": 1}),
        ("sandbox platform.system()", sb, _with("x = platform.system()\n"), {"F6": 1}),
        ("sandbox importlib", sb, _with("import importlib.metadata\n"), {"C3": 1, "F1": 1}),
    ]
    controls += [(f"banned module {m}", sb, _with(f"import {m}\n"), {"C3": 1, "F1": 1})
                 for m in sorted(SANDBOX_BANNED_MODULES)]
    controls += [(f"banned name {n}", sb, _with(f"x = {n}\n"), {"F2": 1}) for n in sorted(SANDBOX_BANNED_NAMES)]
    return controls


def test_t_ro_01_nautilus_confined_to_the_sandbox():
    """Spec 2026-10-26 section 5.6, T-RO-01 amendment (owner ruling O2): "orders in a Nautilus backtest fill against a
    simulated exchange inside one process, as QUANTGEN's paper fills pass through `OrderBook.fill`
    (`core/engine/orders.py:90, 169, 253-257`). The amendment lets exactly one file place such orders, through exactly
    one call, and closes two holes of today's scan: it compares only the first dotted component of an import
    (`tests/macro_m0_harness.py:90-96`), and it misses seven Nautilus order verbs (map04 §3.2). It is the first
    exemption for a forbidden token or call in T-RO-01's history (GOVERNANCE-10): the 2026-10-23 spec widened the scan
    to `tools/` and `papers/` and allowed one importer, but exempted no forbidden token
    (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:177-181`). After it, a T-RO-01 PASS
    means 'no order path outside the one sandbox call'. The council spec is not edited."

    Every control of spec 8.5 gives exactly its multiset of tags in a temp tree, and the real sandbox exists and gives
    no hit (QA-12)."""
    from collections import Counter
    controls = _nautilus_controls()
    assert len(controls) == 51, len(controls)
    wrong = []
    with tempfile.TemporaryDirectory() as name:
        tmp = Path(name)
        for label, rel, text, want in controls:
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            got = dict(Counter(_tag(h) for h in _offences(path, tmp)))
            if got != want:
                wrong.append(f"{label}: {got} != {want}")
            path.unlink()
    assert not wrong, "scan controls off:\n  " + "\n  ".join(wrong)
    sandbox = ROOT / NAUTILUS_SANDBOX
    assert sandbox.is_file(), f"{NAUTILUS_SANDBOX} is missing"
    assert _offences(sandbox) == [], _offences(sandbox)


test_t_ro_01_nautilus_confined_to_the_sandbox.test_ids = ["T-RO-01"]


def _canon(x):
    """Spec 5.6: a dict maps to a dict of canonical values; a set, frozenset, tuple or list to the sorted list of its
    canonical items; any other value stays."""
    if isinstance(x, dict):
        return {k: _canon(v) for k, v in x.items()}
    if isinstance(x, (set, frozenset, tuple, list)):
        return sorted(_canon(v) for v in x)
    return x


def _pin(obj: dict) -> str:
    return hashlib.sha256(json.dumps(_canon(obj), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_t_ro_01_nautilus_allowlist_pinned():
    """Spec 2026-10-26 section 5.6, T-RO-01 amendment (owner ruling O2): "orders in a Nautilus backtest fill against a
    simulated exchange inside one process, as QUANTGEN's paper fills pass through `OrderBook.fill`
    (`core/engine/orders.py:90, 169, 253-257`). The amendment lets exactly one file place such orders, through exactly
    one call, and closes two holes of today's scan: it compares only the first dotted component of an import
    (`tests/macro_m0_harness.py:90-96`), and it misses seven Nautilus order verbs (map04 §3.2). It is the first
    exemption for a forbidden token or call in T-RO-01's history (GOVERNANCE-10): the 2026-10-23 spec widened the scan
    to `tools/` and `papers/` and allowed one importer, but exempted no forbidden token
    (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:177-181`). After it, a T-RO-01 PASS
    means 'no order path outside the one sandbox call'. The council spec is not edited."

    SECURITY-5: the allow-list and the rule lists are pinned by hash, so neither widens without an owner ruling; the
    seven order verbs are forbidden in every file, the sandbox included (rule B)."""
    allow = {"NAUTILUS_SANDBOX": NAUTILUS_SANDBOX, "NAUTILUS_ALLOWED_FROM": NAUTILUS_ALLOWED_FROM,
             "NAUTILUS_DENIED_PREFIXES": NAUTILUS_DENIED_PREFIXES, "NAUTILUS_DENIED_NAMES": NAUTILUS_DENIED_NAMES,
             "SANDBOX_STDLIB": SANDBOX_STDLIB}
    rules = {"NAUTILUS_BRIDGE_ONLY_NAMES": NAUTILUS_BRIDGE_ONLY_NAMES,
             "NAUTILUS_DENIED_NAME_RE": NAUTILUS_DENIED_NAME_RE.pattern, "NAUTILUS_ORDER_VERBS": NAUTILUS_ORDER_VERBS,
             "IMPORT_MACHINERY": IMPORT_MACHINERY, "SANDBOX_BANNED_MODULES": SANDBOX_BANNED_MODULES,
             "SANDBOX_BANNED_NAMES": SANDBOX_BANNED_NAMES, "SANDBOX_FILE_METHODS": SANDBOX_FILE_METHODS,
             "SANDBOX_OS_CALLS": SANDBOX_OS_CALLS}
    # a change needs an owner ruling recorded in spec 2026-10-26 §5.6
    assert _pin(allow) == "2792ad4af44c6af599092f81594a34d1f7d013cd17abf5882c8c6f72a042e49f", _pin(allow)
    # a change needs an owner ruling recorded in spec 2026-10-26 §5.6
    assert _pin(rules) == "70bcf50fbce5637a1854413618b6b9827c04dc10a59a0a25d274b4be1941da6c", _pin(rules)
    assert NAUTILUS_ORDER_VERBS <= FORBIDDEN_CALLS, sorted(NAUTILUS_ORDER_VERBS - FORBIDDEN_CALLS)


test_t_ro_01_nautilus_allowlist_pinned.test_ids = ["T-RO-01"]


def test_t_ro_01_artifact_writers_stamp_read_only():
    """Every artifact carries `read_only: true` (spec L3508): the provenance builder sets it and every shipped
    macro JSON store carries it."""
    stores = [p for p in (ROOT / "data" / "macro").glob("*.json")] if (ROOT / "data" / "macro").is_dir() else []
    for path in stores:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "version" in payload:
            assert payload.get("read_only") is True, f"{path.name} lacks read_only: true"
    src = ROOT / "core" / "ficc" / "macro_artifacts.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    stamped = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "read_only"
                        and isinstance(v, ast.Constant) and v.value is True):
                    stamped = True
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and node.value.value is True:
            for target in node.targets:
                if (isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)
                        and target.slice.value == "read_only"):
                    stamped = True
        elif isinstance(node, ast.keyword) and node.arg == "read_only":
            if isinstance(node.value, ast.Constant) and node.value.value is True:
                stamped = True
    assert stamped, "core/ficc/macro_artifacts.py never sets read_only: True"


test_t_ro_01_artifact_writers_stamp_read_only.test_ids = ["T-RO-01"]


# --------------------------------------------------------------------------- #
# Registry (spec section 9.0a / 9.0b)
# --------------------------------------------------------------------------- #
def _registry() -> list[dict[str, str]]:
    with REGISTRY.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == ["test_id", "tier", "runs_from", "modules", "clause", "deferred_to",
                                     "feasibility", "implemented_in"], reader.fieldnames
        return list(reader)


def test_registry_has_unique_ids_and_valid_columns():
    rows = _registry()
    ids = [r["test_id"] for r in rows]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    assert not dups, f"duplicate registry ids: {dups}"
    for r in rows:
        assert TEST_ID.fullmatch(r["test_id"]), r["test_id"]
        assert r["tier"] in ("fast", "golden", "freeze"), r
        assert re.fullmatch(r"M(10|[0-9])", r["runs_from"]), r
        assert r["feasibility"] in ("SYNTH", "REFDATA", "OWNER"), r
        assert re.fullmatch(r"R-\d\d(;R-\d\d)*", r["modules"]), r
        clauses = [c for c in r["clause"].split(" | ") if c]
        deferred = [d for d in r["deferred_to"].split(" | ") if d]
        assert len(clauses) == len(deferred), f"{r['test_id']}: clause/deferred_to misaligned"
        assert all(re.fullmatch(r"M(10|[0-9])", d) for d in deferred), r
    assert len(rows) >= 200, len(rows)


test_registry_has_unique_ids_and_valid_columns.test_ids = ["T-HERM-01"]


def test_registry_covers_every_id_of_the_spec_exit_table():
    """Every fully spelled id of section 9.0a (the authoritative exit list) has a registry row with that milestone."""
    lines = SPEC.read_text(encoding="utf-8").split("\n")
    rows = _registry()
    table = {r["test_id"]: r["runs_from"] for r in rows}
    deferred = {r["test_id"]: r["deferred_to"].split(" | ") for r in rows}
    start = next(i for i, l in enumerate(lines) if l.startswith("### 9.0a"))
    end = next(i for i, l in enumerate(lines) if l.startswith("### 9.0b"))
    missing, wrong = [], []
    for line in lines[start:end]:
        m = re.match(r"\|\s*M(\d+)\b[^|]*\|(.*)\|", line)
        if not m:
            continue
        milestone, cell = f"M{m.group(1)}", m.group(2)
        for tid in set(TEST_ID.findall(cell)):
            if tid not in table:
                missing.append(tid)
                continue
            # A row names an id either as its runs_from, as a clause deferred to that row, or with "from M<k>".
            if table[tid] == milestone or milestone in deferred[tid] or f"from {table[tid]}" in cell[cell.index(tid):]:
                continue
            wrong.append(f"{tid}: registry {table[tid]} vs spec row {milestone}")
    assert not missing and not wrong, f"missing {missing}; milestone mismatch {wrong}"


test_registry_covers_every_id_of_the_spec_exit_table.test_ids = ["T-HERM-01"]


def test_registry_implemented_in_matches_test_ids():
    """`implemented_in` equals the `test_ids` the macro modules carry; every id a test names is registered."""
    from tests.macro_acceptance import implemented_in
    impl = implemented_in()
    rows = _registry()
    stale = [f"{r['test_id']}: {r['implemented_in']!r} != {impl.get(r['test_id'], '')!r}"
             for r in rows if r["implemented_in"] != impl.get(r["test_id"], "")]
    assert not stale, "registry out of sync (python -m tests.macro_acceptance resyncs it): " + "; ".join(stale)
    unknown = sorted(set(impl) - {r["test_id"] for r in rows})
    assert not unknown, f"test_ids not in the registry: {unknown}"


test_registry_implemented_in_matches_test_ids.test_ids = ["T-HERM-01"]


# --------------------------------------------------------------------------- #
# Fixture manifest (spec section 9.5)
# --------------------------------------------------------------------------- #
def test_manifest_lists_every_fixture_with_a_matching_md5():
    rows = load_manifest()
    assert tuple(MANIFEST_COLUMNS) == ("file", "source", "series", "span", "retrieved_at_utc",
                                       "value_status_rule", "md5", "licence", "owner", "tests")
    assert not unlisted(), f"fixtures not listed in MANIFEST.csv (python -m tests.notrun prints rows): {unlisted()}"
    stale = [f"{n}: {md5_of(MANIFEST.parent / n)} != {r['md5']}" for n, r in rows.items()
             if (MANIFEST.parent / n).is_file() and md5_of(MANIFEST.parent / n) != r["md5"].lower()]
    absent = [n for n in rows if not (MANIFEST.parent / n).is_file()]
    assert not stale and not absent, f"stale md5 {stale}; listed but absent {absent}"
    for name in rows:
        require_fixture(name)


test_manifest_lists_every_fixture_with_a_matching_md5.test_ids = ["T-HERM-01"]


def test_manifest_loader_refuses_unlisted_absent_changed_and_unlicensed():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "ok.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp / "drift.csv").write_text("a,b\n1,3\n", encoding="utf-8")
    header = ",".join(MANIFEST_COLUMNS)
    rows = [f"ok.csv,synthetic(seed=11),A,2026-01-01..2026-01-02,2026-10-02T07:00:00Z,official_close,{md5_of(tmp / 'ok.csv')},CC0,harness,T-HERM-01",
            f"gone.csv,synthetic(seed=11),A,,2026-10-02T07:00:00Z,official_close,{'0' * 32},CC0,harness,T-HERM-01",
            f"drift.csv,synthetic(seed=11),A,,2026-10-02T07:00:00Z,official_close,{'0' * 32},CC0,harness,T-HERM-01"]
    manifest = tmp / "MANIFEST.csv"
    manifest.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    assert require_fixture("ok.csv", manifest=manifest) == tmp / "ok.csv"
    for name, needle in (("unlisted.csv", "not in"), ("gone.csv", "absent"), ("drift.csv", "md5")):
        try:
            require_fixture(name, manifest=manifest)
        except NotRun as exc:
            assert exc.reason.startswith("REFDATA: ") and needle in exc.reason, exc.reason
        else:
            raise AssertionError(f"{name} was not refused")
    assert unlisted(manifest) == []
    (tmp / "extra.csv").write_bytes(b"x")
    assert [n for n, _ in unlisted(manifest)] == ["extra.csv"]
    for bad in (rows[0].replace("CC0", ""), rows[0].replace("harness", ""), rows[0].replace(md5_of(tmp / "ok.csv"), "")):
        manifest.write_text(header + "\n" + bad + "\n", encoding="utf-8")
        try:
            load_manifest(manifest)
        except ValueError as exc:
            assert "not a fixture" in str(exc)
        else:
            raise AssertionError("a row without licence, owner and md5 was accepted")
    manifest.write_text("file,md5\nok.csv,x\n", encoding="utf-8")
    try:
        load_manifest(manifest)
    except ValueError as exc:
        assert "header" in str(exc)
    else:
        raise AssertionError("a wrong header was accepted")


test_manifest_loader_refuses_unlisted_absent_changed_and_unlicensed.test_ids = ["T-HERM-01"]


# --------------------------------------------------------------------------- #
# Runner: NOT_RUN is a third status; the GATE leak is closed
# --------------------------------------------------------------------------- #
def test_runner_records_not_run_as_a_third_status():
    import io
    from contextlib import redirect_stderr, redirect_stdout
    from tests import run_all

    def skipped():
        raise NotRun("REFDATA: probe fixture")

    def failing():
        raise ValueError("boom")

    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        rows = run_all.run([("probe/skipped", skipped), ("probe/ok", lambda: None), ("probe/fail", failing)])
    assert [r["status"] for r in rows] == ["NOT_RUN", "PASS", "FAIL"]
    assert rows[0]["reason"] == "REFDATA: probe fixture" and rows[0]["detail"] == ""
    assert "reason" not in rows[1] and rows[2]["detail"].startswith("ValueError")
    ok = lambda: None                                                  # noqa: E731
    ok.test_ids = ["T-RO-01"]
    later = lambda: None                                               # noqa: E731
    later.test_ids = ["T-CRYPTO-01"]
    clause = lambda: None                                              # noqa: E731
    clause.test_ids = ["T-CAP-01"]           # runs_from M0; its "overlay cannot emit 0" clause is deferred to M2
    entries = [("macro/a", ok), ("macro/b", later), ("macro/macro_m2_risk/test_cap", clause), ("engine/c", lambda: None)]
    assert [n for n, _ in run_all.select(entries, milestone="M0")] == ["macro/a"]
    assert [n for n, _ in run_all.select(entries, milestone="M2")] == ["macro/a", "macro/macro_m2_risk/test_cap"]
    assert [n for n, _ in run_all.select(entries, milestone="M10")] == ["macro/a", "macro/b", "macro/macro_m2_risk/test_cap"]
    assert [n for n, _ in run_all.select(entries, suite="engine")] == ["engine/c"]


test_runner_records_not_run_as_a_third_status.test_ids = ["T-HERM-01"]


def test_every_macro_module_runs_alone_under_the_guard():
    """`python -m tests.<module>` (the single-module run) arms the hermetic guard and exits 1 on a FAIL or on no tests:
    every macro module ends with the shared `run_module` main, never an unguarded loop or nothing at all."""
    import io
    from contextlib import redirect_stderr, redirect_stdout
    from tests import macro_acceptance as MA
    tail = ['if __name__ == "__main__":', "    from tests.macro_acceptance import run_module",
            "    raise SystemExit(run_module(globals()))"]
    bad = [p.name for p in sorted((ROOT / "tests").glob("macro_*.py"))
           if p.name != "macro_acceptance.py" and p.read_text(encoding="utf-8").rstrip().splitlines()[-3:] != tail]
    assert not bad, f"modules without the guarded main: {bad}"

    def test_armed():
        assert MA._DEPTH > 0, "guard not armed"

    def test_skipped():
        raise NotRun("REFDATA: probe")

    def test_broken():
        raise ValueError("boom")

    with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
        codes = [MA.run_module({"test_armed": test_armed, "test_skipped": test_skipped}),
                 MA.run_module({"test_armed": test_armed, "test_broken": test_broken}), MA.run_module({"helper": test_armed})]
    assert codes == [0, 1, 1], (codes, out.getvalue())
    assert "PASS test_armed" in out.getvalue() and "NOT_RUN test_skipped REFDATA: probe" in out.getvalue()


test_every_macro_module_runs_alone_under_the_guard.test_ids = ["T-HERM-01"]


def test_gate_bootstrap_b_is_not_leaked_by_the_expansion_suite():
    """expansion/gate_noise_vs_edge sets GATE['bootstrap_B'] = 300; it must be restored before any later suite."""
    from core.quant import validate as V
    assert V.GATE["bootstrap_B"] == 2000, V.GATE["bootstrap_B"]
    src = (ROOT / "tests" / "expansion_acceptance.py").read_text(encoding="utf-8")
    assert re.search(r"finally:\s*\n\s*V\.GATE\[\"bootstrap_B\"\] = saved_b", src), "GATE restore missing"


if __name__ == "__main__":
    from tests.macro_acceptance import run_module
    raise SystemExit(run_module(globals()))
