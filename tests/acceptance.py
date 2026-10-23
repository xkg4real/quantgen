"""Safety acceptance checks, run as the `safety` suite.

The ten checks that stayed when the NEXTGEN skill cockpit, with the 37 tests of
its catalogue, runner, argument reader and workflow gates, moved to TRADEGEN
(2026-10-23). Three groups:

  * **Safety** — the invariants this build promises: no broker order path, no
    account credential requested, no key printed to a screen.
  * **Regression** — the defects found in the previous build's review. All were
    silent failures, so each gets a test that fails loudly.
  * **KRX gateway** — a provider that is missing or declines says why.

`_read`, `_code_only` and `runtime_py` are shared: seven `tests/macro_*` modules
import them.

Every file read here passes `encoding="utf-8"` explicitly. The previous suite
did not, and five of its tests died with `UnicodeDecodeError: 'cp949'` on this
machine — the target machine — because Windows Korean locale picks cp949 as the
default and `main.py` contains an em dash.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _code_only(path: Path) -> str:
    """Source with docstrings and comments stripped.

    Several checks below assert that a token does not appear in the code. The
    same token is discussed in prose in the very files being checked — naming
    the defect is the point of the comment — so scanning raw text produces false
    positives. `ast` gives us the executable surface instead.
    """
    import ast
    tree = ast.parse(_read(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def runtime_py() -> list[Path]:
    files: list[Path] = []
    for base in (ROOT / "core", ROOT / "data", ROOT / "ui"):
        if base.is_dir():
            files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    files.extend([ROOT / "main.py", ROOT / "config.py"])
    return [p for p in files if p.is_file()]


# --------------------------------------------------------------------------- #
# Safety
# --------------------------------------------------------------------------- #
def test_08_no_broker_order_path():
    """KIS is a brokerage API; this build implements quotations only."""
    needles = ["order_cash", "order-cash", "place_order", "submit_order",
               "TTTC0802U", "TTTC0801U", "VTTC0802U"]
    blob = "\n".join(_read(p) for p in runtime_py()).lower()
    hits = [n for n in needles if n.lower() in blob]
    assert not hits, f"broker order surface present: {hits}"


def test_09_no_account_credentials_requested():
    """Order submission needs an account number. Never ask for one."""
    blob = "\n".join(_read(p) for p in runtime_py())
    for name in ("KIS_ACCOUNT", "CANO", "ACNT_PRDT_CD"):
        assert name not in blob, f"{name} implies an order path"


def test_13_settings_page_shows_presence_not_values():
    """No credential value may reach a widget. FMP, shown before the split only
    among the cockpit's skill providers, is a presence row in the quant list."""
    import config
    source = _read(ROOT / "ui" / "settings_page.py")
    assert "kis_credentials()" not in source
    assert "opendart_key()" not in source
    assert "_clean(" not in source
    assert "fmp_key()" not in source and "core.skills" not in source
    fmp = [p for p in config.quant_provider_status() if p["id"] == "fmp"]
    assert len(fmp) == 1 and fmp[0]["vars"] == ("FMP_API_KEY",), fmp
    assert fmp[0]["ready"] == config.fmp_ready()


# --------------------------------------------------------------------------- #
# Regression — defects found reviewing the previous build
# --------------------------------------------------------------------------- #
def test_14_page_resize_handler_matches_the_flet_api():
    """The old build assigned a handler to an attribute Flet 0.85 does not
    define, so the compact layout never ran at any width. Assert against the
    live API and against the assignment in code, not against prose — the
    misspelling is named in comments here and in main.py on purpose."""
    import flet as ft
    assert hasattr(ft.Page, "on_resize"), "Flet renamed the resize event again"
    source = _code_only(ROOT / "main.py")
    assert re.search(r"page\.on_resize\s*=", source), "no resize handler is attached"
    assert not re.search(r"page\.on_resiz(ed|e_d)\s*=", source), \
        "main.py attaches a handler to an attribute Flet does not define"


def test_15_views_are_cached_across_navigation():
    """Rebuilding a view on every nav click discarded live state."""
    source = _read(ROOT / "main.py")
    assert "cache" in source and "cache[name] = build(" in source


def test_16_every_source_file_is_utf8_readable():
    """The previous suite read files with the platform default and died on cp949."""
    for path in runtime_py() + [ROOT / "tests" / "acceptance.py", ROOT / "tests" / "run_all.py"]:
        try:
            _read(path)
        except UnicodeDecodeError as exc:
            raise AssertionError(f"{path} is not valid UTF-8: {exc}") from None


def test_17_tests_never_read_without_an_encoding():
    """Lock the cp949 fix: reading a file with no explicit encoding here is what
    killed five tests in the previous suite."""
    for name in ("acceptance.py", "run_all.py"):
        source = _code_only(ROOT / "tests" / name)
        assert not re.search(r"read_text\(\s*\)", source), \
            f"{name} reads a file without specifying an encoding"


def test_18_eodhd_is_gone_from_the_runtime():
    """No EODHD *usage*. The name still appears in prose that explains what this
    build replaced, which is why this scans code rather than raw text."""
    blob = "\n".join(_code_only(p) for p in runtime_py()).lower()
    for token in ("eodhd", "quartr"):
        assert token not in blob, f"{token} is still used in the runtime surface"


# --------------------------------------------------------------------------- #
# KRX gateway
# --------------------------------------------------------------------------- #
def test_21_krx_gateway_degrades_with_a_reason():
    """No provider configured must yield an actionable reason, never a blank."""
    from data.krx import KRXGateway
    gateway = KRXGateway()
    for answer in (gateway.daily("005930"), gateway.filings("005930")):
        if not answer.ok:
            assert answer.reason.strip(), "a failed answer must explain itself"


def test_22_krx_status_is_reported_per_provider():
    from data.krx import KRXGateway
    providers = {s["provider"] for s in KRXGateway().status()}
    assert providers == {"KIS", "OpenDART", "KRX"}


def tests():
    return sorted((n, v) for n, v in globals().items()
                  if n.startswith("test_") and callable(v))
