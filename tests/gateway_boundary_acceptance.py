"""KEY-3 boundary test (GATEWAY_DESIGN.md sections 3 and 6): app code reaches data providers only through
core/gateway.

Python's own parser (ast) reads every .py file in core/, quantgen_desktop/, ui/ and main.py and records, per
file, each direct way to a provider:
- an import of a provider module, in any form (`import data.krx.x`, `from data import kis_markets`,
  `from data.fmp.quote_client import FMPQuoteClient`, `import yfinance`, `import gs_quant...`, `from data import *`),
  relative imports resolved against the file's package, including the FRED/Yahoo client core/ficc/data.py (its
  loaders and per-provider fetchers, or the module itself; type-only names such as Series and pure helpers such
  as _period_for do not count);
- a package imported and then followed by attributes (`import data; data.kis_markets.KISMarkets()`);
- `importlib.import_module(...)` or `__import__(...)` with a literal name, also aliased, by keyword, or relative
  with `package=`; a relative name or `__import__` level it cannot resolve (a variable) counts (fails closed);
- the S4-frozen core/engine/feed.py QuoteFeed built without an FMP client (`QuoteFeed(g)`, `QuoteFeed(g, None)`,
  `fmp_client=None`), or subclassed without its own `fmp` (main.py's subclass builds the client through the gateway);
- a config key function or provider status function (`config.kis_ready()`, `config.krx_provider_status()`),
  called or used as a value (`f = config.fmp_key`, `getattr(config, "fmp_key")`), also through an alias
  (`import config as QC`) or a direct import (`from config import kis_ready`);
- the Anthropic API URL as a string literal (`https://api.anthropic.com...`; a host name inside a message does
  not count).

Provider modules themselves are allowed: core/gateway/ and core/ficc/data.py (the FRED/Yahoo client the gateway
wraps). tests/fixtures/gateway/known_direct_calls.json lists today's findings per file, by content (not line
number). Any finding not in the list fails; any listed finding that is gone fails too, so the list cannot go
stale. A file that cannot be read or parsed fails the test. KEY-4 emptied the core/ and main.py entries except
the one FROZEN line of the S4-frozen core/engine/feed.py (2026-11-19); KEY-5 (UI session) empties the screen entries
(SCREEN_CEILING caps them meanwhile).

This test also runs in the Compliance workflow, which runs on every pull request (no path filter).
"""
from __future__ import annotations

import ast
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_FILE = ROOT / "tests" / "fixtures" / "gateway" / "known_direct_calls.json"
SCAN = ("core", "quantgen_desktop", "ui")
ALLOWED = ("core/gateway/", "core/ficc/data.py")
PROVIDERS = ("data.krx", "data.fmp", "data.crypto", "data.kis_markets", "data.kis_stream", "data.kis_workspace",
             "data.net", "data.didm", "yfinance", "gs_quant", "pandas_datareader", "fredapi", "pykrx")
FICC = "core.ficc.data"
LOCAL_FILE = ROOT / "core" / "gateway" / "local.py"


def _ficc_constants() -> frozenset[str]:
    """The names of core/ficc/data.py that reach no provider: ``FiccData.CONSTANTS`` in core/gateway/local.py, read
    with ast so this test stays standard-library only and shares one list with the gateway. Any other name of the
    module (a loader, a fetcher, the ``_yf``/``_pdr``/``_requests`` handles, ``_fetch``...) is a finding."""
    tree = ast.parse(LOCAL_FILE.read_bytes())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "FiccData":
            for item in node.body:
                if isinstance(item, ast.Assign) and any(getattr(t, "id", "") == "CONSTANTS" for t in item.targets):
                    return frozenset(ast.literal_eval(item.value))
    raise AssertionError("FiccData.CONSTANTS not found in core/gateway/local.py")


FICC_SAFE = _ficc_constants()
# core/engine/feed.py is frozen byte-for-byte by the S4 owner ruling (T-RO-01, T-CAP-02; tests/macro_m5_integration.py
# UNTOUCHED list). Its own FMP import stays; the app builds the feed's FMP client through the gateway in main.py.
FROZEN = {"core/engine/feed.py": ["import:data.fmp.FMPQuoteClient"]}
# KEY-5 (UI session) lowers this; a regenerated list may never grow past it.
# 22 / 44 since the PR #133 second review added quantgen_desktop/paper.py (it builds the frozen QuoteFeed without an
# FMP client, so the feed reaches FMP itself; KEY-5 passes a gateway client or reuses main.py's subclass).
SCREEN_CEILING = {"files": 22, "sites": 44}
SCREEN_FILES = (
    "quantgen_desktop/app.py",
    "quantgen_desktop/home_view.py",
    "quantgen_desktop/market_chart.py",
    "quantgen_desktop/market_rankings.py",
    "quantgen_desktop/market_summary.py",
    "quantgen_desktop/market_tools.py",
    "quantgen_desktop/paper.py",
    "quantgen_desktop/qscore.py",
    "quantgen_desktop/watchlist_live.py",
    "ui/bonds_page.py",
    "ui/crypto_page.py",
    "ui/derivatives_page.py",
    "ui/fcharts.py",
    "ui/fx_page.py",
    "ui/krx_page.py",
    "ui/macro_page.py",
    "ui/macro_state_panel.py",
    "ui/market_chart_page.py",
    "ui/quant_lab_page.py",
    "ui/rates_page.py",
    "ui/settings_page.py",
    "ui/structuring_page.py",
)
# The S4-frozen engine feed builds its own FMPQuoteClient when it is given none (core/engine/feed.py, FROZEN below).
# Building one without fmp_client is a direct FMP access; main.py uses its gateway subclass instead.
FROZEN_FEED = "core.engine.feed.QuoteFeed"
KEY_FUNCTIONS = {"kis_ready", "kis_credentials", "fmp_key", "fmp_ready", "opendart_key", "opendart_ready", "krx_key",
                 "krx_ready", "anthropic_key", "ai_ready", "gs_client_id", "gs_client_secret", "upbit_ready",
                 "upbit_keys", "krx_provider_status", "quant_provider_status", "crypto_provider_status",
                 "ficc_provider_status"}
ANTHROPIC_URL = ("https://api.anthropic.com", "http://api.anthropic.com")
DYNAMIC = {"importlib.import_module", "importlib.__import__", "builtins.__import__", "__import__"}


def _provider(name: str) -> bool:
    return any(name == p or name.startswith(p + ".") for p in PROVIDERS)


def _parent_package(name: str) -> bool:
    """A package that holds a provider module or the FICC client (``data``, ``core``, ``core.ficc``)."""
    return any(p.startswith(name + ".") for p in PROVIDERS + (FICC,))


def _covered(dotted: str) -> str:
    """The provider or FICC name reached by a dotted path, or "" (``core.ficc.data.Series`` reaches nothing)."""
    if _provider(dotted):
        parts = dotted.split(".")
        for i in range(1, len(parts) + 1):
            if _provider(".".join(parts[:i])):
                return ".".join(parts[:i])
    if dotted == FICC:
        return FICC
    if dotted.startswith(FICC + ".") and dotted[len(FICC) + 1:].split(".")[0] not in FICC_SAFE:
        return FICC
    return ""


def _module_name(rel: str) -> tuple[str, bool]:
    """``core/ficc/insights.py`` -> (``core.ficc.insights``, False); ``core/ficc/__init__.py`` -> (``core.ficc``, True)."""
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


def _absolute(node: ast.ImportFrom, module: str, is_package: bool) -> str:
    """The absolute module of a ``from`` import; relative ones (``from .data import x``) are resolved."""
    if not node.level:
        return node.module or ""
    package = module.split(".") if is_package else module.split(".")[:-1]
    keep = len(package) - (node.level - 1)
    if keep < 0:
        return node.module or ""
    base = package[:keep]
    return ".".join(base + ([node.module] if node.module else []))


def _dotted(node: ast.AST) -> list[str]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return []


def _literal(node: ast.AST) -> str:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ""


def _int_literal(node: ast.AST):
    """The int a literal level is, or None for anything else (a name, an expression)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value
    return None


def _no_fmp_client(node: ast.Call) -> bool:
    """QuoteFeed(g), QuoteFeed(g, None), QuoteFeed(g, fmp_client=None): the frozen feed then builds its own client."""
    def is_none(value):
        return isinstance(value, ast.Constant) and value.value is None
    given = [kw.value for kw in node.keywords if kw.arg == "fmp_client"] + node.args[1:2]
    return not given or all(is_none(v) for v in given)


def _defines_fmp(cls: ast.ClassDef) -> bool:
    for item in cls.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "fmp":
            return True
        targets = item.targets if isinstance(item, ast.Assign) else [item.target] if isinstance(
            item, (ast.AnnAssign, ast.AugAssign)) else []
        if any(isinstance(t, ast.Name) and t.id == "fmp" for t in targets):
            return True
    return False


def _dynamic_name(node: ast.Call, module: str, is_package: bool) -> list[str]:
    """The absolute module names an ``import_module``/``__import__`` call reaches: the literal name (positional or
    ``name=``), resolved against ``package=`` (a literal, or ``__package__``/``__name__`` of the scanned file), plus
    each ``fromlist`` item under it."""
    package_of_file = module if is_package else module.rpartition(".")[0]

    def package_value(value: ast.AST) -> str:
        if isinstance(value, ast.Name) and value.id == "__package__":
            return package_of_file
        if isinstance(value, ast.Name) and value.id == "__name__":
            return module
        if _dotted(value) == ["__spec__", "parent"]:
            return package_of_file
        return _literal(value)

    name = _literal(node.args[0]) if node.args else ""
    package, fromlist, level = "", [], 0
    is_import = len(node.args) > 2 or any(kw.arg in ("globals", "locals", "fromlist", "level") for kw in node.keywords)
    for kw in node.keywords:
        if kw.arg == "name":
            name = _literal(kw.value)
        elif kw.arg == "package":
            package = package_value(kw.value)
        elif kw.arg == "fromlist" and isinstance(kw.value, (ast.List, ast.Tuple)):
            fromlist = [_literal(e) for e in kw.value.elts]
        elif kw.arg == "level":
            level = _int_literal(kw.value)
    if len(node.args) > 1 and not package and not is_import:
        package = package_value(node.args[1])
    if len(node.args) > 3 and isinstance(node.args[3], (ast.List, ast.Tuple)):   # __import__(n, g, l, fromlist)
        fromlist = [_literal(e) for e in node.args[3].elts]
    if len(node.args) > 4:
        level = _int_literal(node.args[4])                                      # __import__(n, g, l, f, level)
    if level is None:                                                           # review 3 F3: a level that is not an
        return ["." + (name or "?")]                                            # int literal: unresolved, fails closed
    if level > 0:                                                               # __import__ relative: as "." * level
        name, package = "." * level + name, package_of_file
    if name.startswith(".") and not package:
        return [name] + [f"{name}.{item}" for item in fromlist if item]       # unresolved relative: kept, fails closed
    if name.startswith(".") and package:
        level = len(name) - len(name.lstrip("."))
        pkg = package.split(".")
        pkg = pkg[:len(pkg) - (level - 1)] if level > 1 else pkg
        name = ".".join(pkg + ([name.lstrip(".")] if name.lstrip(".") else []))
    return [name] + [f"{name}.{item}" for item in fromlist if item] if name else []


def findings(source: "str | bytes", module: str = "", is_package: bool = False) -> list[str]:
    """Every direct way to a provider in one file. ``module`` is the file's dotted name (for relative imports).
    Give the file's bytes so a PEP 263 coding cookie is honoured as Python would. Raises SyntaxError for a file
    Python cannot parse, so such a file fails the test instead of being skipped."""
    tree = ast.parse(source)
    found: list[str] = []
    bound: dict[str, str] = {"__import__": "__import__"}   # local name -> absolute dotted target
    counted: set[str] = set()                               # names whose import was already a finding
    covered_imports: list[str] = []                         # ``import data.krx.x``: uses of data.krx.x... counted
    config_names = {"config"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _provider(alias.name) or alias.name == FICC
                if hit:
                    found.append(f"import:{alias.name}")
                    covered_imports.append(alias.name)
                local = alias.asname or alias.name.split(".")[0]
                bound[local] = alias.name if alias.asname else alias.name.split(".")[0]
                if hit and alias.asname:
                    counted.add(local)
                if alias.name == "config":
                    config_names.add(local)
        elif isinstance(node, ast.ImportFrom):
            base = _absolute(node, module, is_package)
            for alias in node.names:
                if alias.name == "*":
                    if _provider(base) or base == FICC or _parent_package(base) or base == "config":
                        found.append(f"import:{base}.*")
                    continue
                full = f"{base}.{alias.name}"
                local = alias.asname or alias.name
                bound[local] = full
                hit = False
                if _provider(base) or _provider(full):
                    hit = True
                elif full == FICC:
                    hit = True
                elif base == FICC and alias.name not in FICC_SAFE:
                    hit = True
                elif base == "config" and alias.name in KEY_FUNCTIONS:
                    hit = True
                if hit:
                    found.append(f"import:{full}")
                    counted.add(local)
                if full == "config":
                    config_names.add(local)
    parents: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not _defines_fmp(node):
            for base in node.bases:                       # review 3 F1: the frozen feed subclassed without fmp
                chain = _dotted(base)
                if chain and ".".join([bound.get(chain[0], chain[0])] + chain[1:]) == FROZEN_FEED:
                    found.append(f"subclass:{FROZEN_FEED}(no fmp)")
        if isinstance(node, ast.Call):
            func = node.func
            parts = _dotted(func)
            target = ".".join([bound.get(parts[0], parts[0])] + parts[1:]) if parts else ""
            if target in DYNAMIC or (parts and parts[-1] == "import_module" and len(parts) == 1
                                     and bound.get(parts[0], "") == "importlib.import_module"):
                for name in _dynamic_name(node, module, is_package):
                    if _provider(name) or name == FICC or _covered(name) or _parent_package(name) \
                            or name.startswith("."):                          # a relative name it cannot resolve
                        found.append(f"dynamic:{name}")
                        break
            if parts and len(parts) == 2 and parts[0] in config_names and parts[1] in KEY_FUNCTIONS:
                found.append(f"call:config.{parts[1]}")
            if target == FROZEN_FEED and _no_fmp_client(node):
                found.append(f"call:{FROZEN_FEED}(no fmp_client)")       # its own FMP path, outside the gateway
            if parts and len(parts) == 1 and parts[0] == "getattr" and len(node.args) >= 2:
                obj = node.args[0]
                attr = _literal(node.args[1])
                if isinstance(obj, ast.Name) and obj.id in config_names and attr in KEY_FUNCTIONS:
                    found.append(f"ref:config.{attr}")
                elif attr and _dotted(obj) and _dotted(obj)[0] in bound and _dotted(obj)[0] not in counted \
                        and not _covered(".".join([bound[_dotted(obj)[0]]] + _dotted(obj)[1:])):
                    chain = _dotted(obj)                                        # (an obj already counted as attr: once)
                    reached = _covered(".".join([bound[chain[0]]] + chain[1:] + [attr]))
                    if reached:                                                 # getattr(<imported package>, "x")
                        found.append(f"attr:{reached}")
        elif isinstance(node, ast.Attribute):
            parent = parents.get(id(node))
            if isinstance(parent, ast.Attribute):
                continue                                   # only the outermost attribute of a chain
            parts = _dotted(node)
            if not parts:
                continue
            if len(parts) == 2 and parts[0] in config_names and parts[1] in KEY_FUNCTIONS:
                if not (isinstance(parent, ast.Call) and parent.func is node):
                    found.append(f"ref:config.{parts[1]}")
                continue
            root = parts[0]
            if root not in bound or root in counted:
                continue
            dotted = ".".join([bound[root]] + parts[1:])
            reached = _covered(dotted)
            if not reached:
                continue
            if any(dotted == m or dotted.startswith(m + ".") for m in covered_imports):
                continue
            found.append(f"attr:{reached}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and any(u in node.value for u in ANTHROPIC_URL):
            found.append("url:api.anthropic.com")
    return sorted(found)


def scan() -> tuple[dict[str, list[str]], list[str]]:
    """(findings per file, files that could not be read or parsed)."""
    files = [ROOT / "main.py"]
    for top in SCAN:
        files.extend(sorted((ROOT / top).rglob("*.py")))
    result, errors = {}, []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in rel or any(rel == a or (a.endswith("/") and rel.startswith(a)) for a in ALLOWED):
            continue
        module, is_package = _module_name(rel)
        try:
            items = findings(path.read_bytes(), module, is_package)
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
            errors.append(f"{rel}: {type(exc).__name__}")
            continue
        if items:
            result[rel] = items
    return result, errors


def known() -> dict[str, list[str]]:
    return json.loads(KNOWN_FILE.read_text(encoding="utf-8"))["files"]


class BoundaryTest(unittest.TestCase):
    def test_no_new_direct_provider_calls(self):
        now, listed = scan()[0], known()
        new = {f: sorted((Counter(items) - Counter(listed.get(f, []))).elements()) for f, items in now.items()}
        new = {f: v for f, v in new.items() if v}
        self.assertEqual(new, {}, "new direct provider access; go through core.gateway")

    def test_known_list_is_not_stale(self):
        now, listed = scan()[0], known()
        gone = {f: sorted((Counter(items) - Counter(now.get(f, []))).elements()) for f, items in listed.items()}
        gone = {f: v for f, v in gone.items() if v}
        self.assertEqual(gone, {}, "listed direct access is gone; remove it from known_direct_calls.json")

    def test_core_and_main_go_through_the_gateway(self):
        """KEY-4 done: no core/ file and not main.py may reach a provider directly, except the S4-frozen feed.py
        (FROZEN); only screens remain (KEY-5)."""
        left = {f: v for f, v in known().items() if f.startswith("core/") or f == "main.py"}
        self.assertEqual(left, FROZEN)

    def test_screen_list_stays_under_the_ceiling(self):
        """A regenerated list (--write-known) cannot quietly grow: files and sites stay at or under SCREEN_CEILING,
        and no screen file outside today's list may appear."""
        screens = {f: v for f, v in known().items() if f.startswith(("quantgen_desktop/", "ui/"))}
        self.assertLessEqual(len(screens), SCREEN_CEILING["files"])
        self.assertLessEqual(sum(len(v) for v in screens.values()), SCREEN_CEILING["sites"])
        self.assertLessEqual(set(screens), set(SCREEN_FILES))

    def test_known_totals_match_the_design(self):
        data = json.loads(KNOWN_FILE.read_text(encoding="utf-8"))
        files = data["files"]
        core = sum(len(v) for f, v in files.items() if f.startswith("core/") or f == "main.py")
        screens = sum(len(v) for f, v in files.items() if f.startswith(("quantgen_desktop/", "ui/")))
        self.assertEqual({"files": len(files), "core_and_main": core, "screens": screens}, data["totals"])

    def test_detector_catches_each_form(self):
        sample = (
            "import data.krx.kis_client\nfrom data import kis_markets\nfrom data.fmp.quote_client import X\n"
            "import yfinance as yf\nimport gs_quant.session\nfrom core.ficc.data import load_series, Series\n"
            "from core.ficc import data\nimport importlib\nimportlib.import_module('data.net')\n"
            "import config as QC\nQC.kis_ready()\nimport config\nconfig.fmp_key()\nfrom config import ai_ready\n"
            "URL = 'https://api.anthropic.com/v1/messages'\nMSG = 'check api.anthropic.com'\n")
        self.assertEqual(findings(sample), sorted([
            "import:data.krx.kis_client", "import:data.kis_markets", "import:data.fmp.quote_client.X",
            "import:yfinance", "import:gs_quant.session", "import:core.ficc.data.load_series",
            "import:core.ficc.data", "dynamic:data.net", "call:config.kis_ready", "call:config.fmp_key",
            "import:config.ai_ready", "url:api.anthropic.com"]))


    def test_detector_catches_the_key4_forms(self):
        """Forms the KEY-3 review found missing (main session, 2026-11-19, items 1-5 and 8)."""
        cases = {
            # 1: the per-provider fetchers and star imports of the FICC client
            "from core.ficc.data import _yf_fetch, _period_for\n": ["import:core.ficc.data._yf_fetch"],
            "from core.ficc.data import *\n": ["import:core.ficc.data.*"],
            # 2: relative imports, resolved against the file's own package
            "from .data import load_series\n": ["import:core.ficc.data.load_series"],
            "from ..ficc.data import load_many\n": ["import:core.ficc.data.load_many"],
            "from ...data import kis_markets\n": ["import:data.kis_markets"],
            # 4: config key functions used as values, and the provider status rows
            "import config\nf = config.fmp_key\n": ["ref:config.fmp_key"],
            "import config\nf = getattr(config, 'anthropic_key')\n": ["ref:config.anthropic_key"],
            "import config\nrows = config.krx_provider_status()\n": ["call:config.krx_provider_status"],
            # 5: aliased import_module, keyword and relative names, package-then-attribute, star from the package
            "from importlib import import_module as im\nim('data.net')\n": ["dynamic:data.net"],
            "import importlib as il\nil.import_module(name='data.fmp')\n": ["dynamic:data.fmp"],
            "import importlib\nimportlib.import_module('.kis_markets', package='data')\n":
                ["dynamic:data.kis_markets"],
            "import data\ndata.kis_markets.KISMarkets()\n": ["attr:data.kis_markets"],
            "from core import ficc\nficc.data.load_series('x')\n": ["attr:core.ficc.data"],
            "import core.ficc\ncore.ficc.data.load_many([])\n": ["attr:core.ficc.data"],
            "from data import *\n": ["import:data.*"],
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(findings(source, "core.ficc.insights"), sorted(expected))
        # not findings: type-only names, pure helpers, a module already counted at its import, other settings
        for source in ("from core.ficc.data import Series, _period_for\n",
                       "from core import ficc\nx = ficc.data.Series\n",
                       "import data.krx.kis_client\ndata.krx.kis_client.KISClient()\n",
                       "import config\nx = config.HTTP_TIMEOUT_SECONDS\n"):
            with self.subTest(source=source):
                self.assertEqual(findings(source, "core.ficc.insights"),
                                 ["import:data.krx.kis_client"] if "kis_client" in source else [])

    def test_detector_catches_the_pr133_review_forms(self):
        """Forms the PR #133 review found missing (main session, 2026-11-19, A2 and B1-B4)."""
        cases = {
            # A2: every name of core.ficc.data outside FiccData.CONSTANTS (the _yf/_pdr/_requests handles, _fetch...)
            "from core.ficc.data import _yf\n": ["import:core.ficc.data._yf"],
            "from .data import _yf\n": ["import:core.ficc.data._yf"],
            "from core.ficc.data import _pdr, _requests, _fetch, _treasury_from_fred\n":
                ["import:core.ficc.data._fetch", "import:core.ficc.data._pdr", "import:core.ficc.data._requests",
                 "import:core.ficc.data._treasury_from_fred"],
            "import core.ficc\ncore.ficc.data._yf.download('SPY')\n": ["attr:core.ficc.data"],
            "from core import ficc\nficc.data._yf.Ticker('SPY')\n": ["attr:core.ficc.data"],
            # B1: dynamic import of a parent package, then attributes, getattr or fromlist
            "__import__('data', fromlist=['krx']).krx.KRXGateway()\n": ["dynamic:data"],
            "import importlib\nimportlib.import_module('data').krx.KRXGateway()\n": ["dynamic:data"],
            "import importlib\ngetattr(importlib.import_module('data'), 'krx')\n": ["dynamic:data"],
            "import importlib\nimportlib.import_module('core.ficc').data.load_series('DGS10')\n": ["dynamic:core.ficc"],
            "import importlib\nimportlib.import_module('.data', package=__package__)\n": ["dynamic:core.ficc.data"],
            "__import__('core.ficc', globals(), locals(), ['data'])\n": ["dynamic:core.ficc"],
            # B2: the FRED library and the other provider libraries
            "import pandas_datareader.data as web\nweb.DataReader('DGS10', 'fred')\n":
                ["import:pandas_datareader.data"],
            "import fredapi\nimport pykrx\n": ["import:fredapi", "import:pykrx"],
            # B4: config star import
            "from config import *\nfmp_key()\n": ["import:config.*"],
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(findings(source, "core.ficc.insights"), sorted(expected))

    def test_detector_catches_the_second_review_forms(self):
        """PR #133 second review (B2, C2, C3)."""
        cases = {
            "from core.engine.feed import QuoteFeed\nQuoteFeed()\n": ["call:core.engine.feed.QuoteFeed(no fmp_client)"],
            "import importlib\nimportlib.__import__('data.krx')\n": ["dynamic:data.krx"],
            "import data\ngetattr(data, 'kis_markets').KISMarkets()\n": ["attr:data.kis_markets"],
            "from core import ficc\ngetattr(ficc.data, '_yf')\n": ["attr:core.ficc.data"],
            "import importlib\nimportlib.import_module('.data', package=__spec__.parent)\n": ["dynamic:core.ficc.data"],
            "__import__('data', globals(), locals(), ['krx'], 3)\n": ["dynamic:data"],
            "import importlib\nimportlib.import_module('.x', package=pkg)\n": ["dynamic:.x"],   # fails closed
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(findings(source, "core.ficc.insights"), sorted(expected))
        for source in ("from core.engine.feed import QuoteFeed\nQuoteFeed(g, fmp_client=c)\n",
                       "from core.engine.feed import QuoteFeed\nQuoteFeed(g, c)\n",
                       "from core.engine.feed import QuoteFeed as F\nclass Q(F):\n    @property\n"
                       "    def fmp(self):\n        return None\n"):
            with self.subTest(source=source):
                self.assertEqual(findings(source, "main"), [])

    def test_detector_catches_the_third_review_forms(self):
        """PR #133 third review: F1 (the frozen feed without an FMP client, given as None or subclassed without its
        own fmp) and F3 (an __import__ level that is not an int literal fails closed)."""
        no_client = ["call:core.engine.feed.QuoteFeed(no fmp_client)"]
        cases = {
            "from core.engine.feed import QuoteFeed\nQuoteFeed(g, None)\n": no_client,
            "from core.engine.feed import QuoteFeed\nQuoteFeed(g, fmp_client=None)\n": no_client,
            "from core.engine import feed\nfeed.QuoteFeed(g)\n": no_client,
            "from core.engine.feed import QuoteFeed as F\nclass Q(F):\n    pass\n":
                ["subclass:core.engine.feed.QuoteFeed(no fmp)"],
            "from core.engine import feed\nclass Q(feed.QuoteFeed):\n    x = 1\n":
                ["subclass:core.engine.feed.QuoteFeed(no fmp)"],
            "n = 1\n__import__('data', globals(), locals(), ['krx'], n)\n": ["dynamic:.data"],
            "__import__('data', level=lvl)\n": ["dynamic:.data"],
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(findings(source, "core.ficc.insights"), sorted(expected))

    def test_ficc_allowlist_is_pinned(self):
        """C2: the names of core.ficc.data the boundary lets through are exactly these pure values and helpers; adding
        a fetcher (_fred_fetch, _provider_rows, _cache_get...) to FiccData.CONSTANTS fails here first."""
        self.assertEqual(FICC_SAFE, frozenset({"G10_KRW", "Series", "CurvePanel", "CurveSnapshot", "_period_for",
                                               "synthetic_series", "synthetic_curve_panel", "synthetic_fx"}))

    def test_coding_cookie_is_honoured(self):
        """B3: the scan gives ast the file's bytes, so code hidden behind a PEP 263 cookie is seen as Python runs it."""
        hidden = "# -*- coding: utf-7 -*-\n+AGk-mport data.krx.kis+AF8-client\n".encode("ascii")
        self.assertEqual(findings(hidden), ["import:data.krx.kis_client"])

    def test_unparsable_file_fails(self):
        """3: a file Python cannot parse or decode is an error, not a skipped file."""
        with self.assertRaises(SyntaxError):
            findings("def broken(:\n")
        self.assertEqual(scan()[1], [], "files the boundary test could not read")

if __name__ == "__main__":
    if "--write-known" in sys.argv:                 # maintenance: regenerate the fixture from the tree
        files, errors = scan()
        if errors:
            sys.exit("cannot parse: " + ", ".join(errors))
        core = sum(len(v) for f, v in files.items() if f.startswith("core/") or f == "main.py")
        screens = sum(len(v) for f, v in files.items() if f.startswith(("quantgen_desktop/", "ui/")))
        KNOWN_FILE.write_text(json.dumps({"files": files, "totals": {"files": len(files), "core_and_main": core,
                                                                      "screens": screens}},
                                         indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"files": len(files), "core_and_main": core, "screens": screens}))
    else:
        unittest.main()
