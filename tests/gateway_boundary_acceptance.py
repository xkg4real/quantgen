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
  with `package=`;
- a config key function or provider status function (`config.kis_ready()`, `config.krx_provider_status()`),
  called or used as a value (`f = config.fmp_key`, `getattr(config, "fmp_key")`), also through an alias
  (`import config as QC`) or a direct import (`from config import kis_ready`);
- the Anthropic API URL as a string literal (`https://api.anthropic.com...`; a host name inside a message does
  not count).

Provider modules themselves are allowed: core/gateway/ and core/ficc/data.py (the FRED/Yahoo client the gateway
wraps). tests/fixtures/gateway/known_direct_calls.json lists today's findings per file, by content (not line
number). Any finding not in the list fails; any listed finding that is gone fails too, so the list cannot go
stale. A file that cannot be read or parsed fails the test. KEY-4 emptied the core/ and main.py entries
(2026-11-19); KEY-5 (UI session) empties the screen entries.

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
             "data.net", "data.didm", "yfinance", "gs_quant")
FICC = "core.ficc.data"
# The network-reaching names of core/ficc/data.py: its loaders and the per-provider fetchers behind them
# (type-only names such as Series and pure helpers such as _period_for do not count).
FICC_LOADERS = {"load_many", "load_series", "load_treasury_curve", "load_fx_spot", "load_short_rate",
                "load_policy_rates", "fred_ready", "yfinance_ready", "probe", "_yf_fetch", "_fred_fetch",
                "_provider_rows"}
KEY_FUNCTIONS = {"kis_ready", "kis_credentials", "fmp_key", "fmp_ready", "opendart_key", "opendart_ready", "krx_key",
                 "krx_ready", "anthropic_key", "ai_ready", "gs_client_id", "gs_client_secret", "upbit_ready",
                 "upbit_keys", "krx_provider_status", "quant_provider_status", "crypto_provider_status",
                 "ficc_provider_status"}
ANTHROPIC_URL = ("https://api.anthropic.com", "http://api.anthropic.com")
DYNAMIC = {"importlib.import_module", "builtins.__import__", "__import__"}


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
    if dotted.startswith(FICC + ".") and dotted[len(FICC) + 1:].split(".")[0] in FICC_LOADERS:
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


def findings(source: str, module: str = "", is_package: bool = False) -> list[str]:
    """Every direct way to a provider in one file. ``module`` is the file's dotted name (for relative imports).
    Raises SyntaxError for a file Python cannot parse, so such a file fails the test instead of being skipped."""
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
                    if _provider(base) or base == FICC or _parent_package(base):
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
                elif base == FICC and alias.name in FICC_LOADERS:
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
        if isinstance(node, ast.Call):
            func = node.func
            parts = _dotted(func)
            target = ".".join([bound.get(parts[0], parts[0])] + parts[1:]) if parts else ""
            if target in DYNAMIC or (parts and parts[-1] == "import_module" and len(parts) == 1
                                     and bound.get(parts[0], "") == "importlib.import_module"):
                name = _literal(node.args[0]) if node.args else ""
                package = ""
                for kw in node.keywords:
                    if kw.arg == "name":
                        name = _literal(kw.value)
                    elif kw.arg == "package":
                        package = _literal(kw.value)
                if len(node.args) > 1 and not package:
                    package = _literal(node.args[1])
                if name.startswith(".") and package:
                    level = len(name) - len(name.lstrip("."))
                    pkg = package.split(".")
                    pkg = pkg[:len(pkg) - (level - 1)] if level > 1 else pkg
                    name = ".".join(pkg + ([name.lstrip(".")] if name.lstrip(".") else []))
                if name and (_provider(name) or name == FICC or _covered(name)):
                    found.append(f"dynamic:{name}")
            if parts and len(parts) == 2 and parts[0] in config_names and parts[1] in KEY_FUNCTIONS:
                found.append(f"call:config.{parts[1]}")
            if parts and len(parts) == 1 and parts[0] == "getattr" and len(node.args) >= 2:
                obj = node.args[0]
                attr = _literal(node.args[1])
                if isinstance(obj, ast.Name) and obj.id in config_names and attr in KEY_FUNCTIONS:
                    found.append(f"ref:config.{attr}")
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
            items = findings(path.read_text(encoding="utf-8"), module, is_package)
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
        """KEY-4 done: no core/ file and not main.py may reach a provider directly; only screens remain (KEY-5)."""
        left = [f for f in known() if f.startswith("core/") or f == "main.py"]
        self.assertEqual(left, [])

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
