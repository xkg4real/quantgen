"""KEY-3 boundary test (GATEWAY_DESIGN.md sections 3 and 6): app code reaches data providers only through
core/gateway.

Python's own parser (ast) reads every .py file in core/, quantgen_desktop/, ui/ and main.py and records, per
file, each direct way to a provider:
- an import of a provider module, in any form (`import data.krx.x`, `from data import kis_markets`,
  `from data.fmp.quote_client import FMPQuoteClient`, `import yfinance`, `import gs_quant...`), including the
  FRED/Yahoo client core/ficc/data.py (its loaders, or the module itself; type-only names such as Series do not
  count);
- `importlib.import_module("<provider module>")` or `__import__(...)` with a literal name;
- a call to a config key function (`config.kis_ready()` etc.), also through an alias (`import config as QC`) or
  a direct import (`from config import kis_ready`);
- the Anthropic API URL as a string literal (`https://api.anthropic.com...`; a host name inside a message does
  not count).

Provider modules themselves are allowed: core/gateway/ and core/ficc/data.py (the FRED/Yahoo client the gateway
wraps). tests/fixtures/gateway/known_direct_calls.json lists today's findings per file, by content (not line
number). Any finding not in the list fails; any listed finding that is gone fails too, so the list cannot go
stale. KEY-4 empties the core/ and main.py entries, KEY-5 (UI session) the screen entries.

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
FICC_LOADERS = {"load_many", "load_series", "load_treasury_curve", "load_fx_spot", "load_short_rate",
                "load_policy_rates", "fred_ready", "yfinance_ready", "probe"}
KEY_FUNCTIONS = {"kis_ready", "kis_credentials", "fmp_key", "fmp_ready", "opendart_key", "opendart_ready", "krx_key",
                 "krx_ready", "anthropic_key", "ai_ready", "gs_client_id", "gs_client_secret", "upbit_ready",
                 "upbit_keys"}
ANTHROPIC_URL = ("https://api.anthropic.com", "http://api.anthropic.com")


def _provider(name: str) -> bool:
    return any(name == p or name.startswith(p + ".") for p in PROVIDERS)


def findings(source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    config_names = {"config"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _provider(alias.name) or alias.name == FICC:
                    found.append(f"import:{alias.name}")
                if alias.name == "config" and alias.asname:
                    config_names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                full = f"{node.module}.{alias.name}"
                if _provider(node.module) or _provider(full):
                    found.append(f"import:{full}")
                elif full == FICC:
                    found.append(f"import:{FICC}")
                elif node.module == FICC and alias.name in FICC_LOADERS:
                    found.append(f"import:{full}")
                elif node.module == "config" and alias.name in KEY_FUNCTIONS:
                    found.append(f"import:{full}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
            if name in ("import_module", "__import__") and node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                target = node.args[0].value
                if _provider(target) or target == FICC:
                    found.append(f"dynamic:{target}")
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) \
                    and func.value.id in config_names and func.attr in KEY_FUNCTIONS:
                found.append(f"call:config.{func.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and any(u in node.value for u in ANTHROPIC_URL):
            found.append("url:api.anthropic.com")
    return sorted(found)


def scan() -> dict[str, list[str]]:
    files = [ROOT / "main.py"]
    for top in SCAN:
        files.extend(sorted((ROOT / top).rglob("*.py")))
    result = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in rel or any(rel == a or (a.endswith("/") and rel.startswith(a)) for a in ALLOWED):
            continue
        try:
            items = findings(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        if items:
            result[rel] = items
    return result


def known() -> dict[str, list[str]]:
    return json.loads(KNOWN_FILE.read_text(encoding="utf-8"))["files"]


class BoundaryTest(unittest.TestCase):
    def test_no_new_direct_provider_calls(self):
        now, listed = scan(), known()
        new = {f: sorted((Counter(items) - Counter(listed.get(f, []))).elements()) for f, items in now.items()}
        new = {f: v for f, v in new.items() if v}
        self.assertEqual(new, {}, "new direct provider access; go through core.gateway")

    def test_known_list_is_not_stale(self):
        now, listed = scan(), known()
        gone = {f: sorted((Counter(items) - Counter(now.get(f, []))).elements()) for f, items in listed.items()}
        gone = {f: v for f, v in gone.items() if v}
        self.assertEqual(gone, {}, "listed direct access is gone; remove it from known_direct_calls.json")

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


if __name__ == "__main__":
    if "--write-known" in sys.argv:                 # maintenance: regenerate the fixture from the tree
        files = scan()
        core = sum(len(v) for f, v in files.items() if f.startswith("core/") or f == "main.py")
        screens = sum(len(v) for f, v in files.items() if f.startswith(("quantgen_desktop/", "ui/")))
        KNOWN_FILE.write_text(json.dumps({"files": files, "totals": {"files": len(files), "core_and_main": core,
                                                                      "screens": screens}},
                                         indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"files": len(files), "core_and_main": core, "screens": screens}))
    else:
        unittest.main()
