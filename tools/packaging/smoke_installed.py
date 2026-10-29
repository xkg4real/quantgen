"""Verify installed imports/resources offline, outside the source checkout.

Never starts the application engine or loads its actual research stores.
"""
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


def guard(event, args):
    if event == "socket.connect":
        raise AssertionError("Installed smoke must be offline")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        parts = Path(os.fsdecode(args[0])).parts
        if any(p.startswith(".env") or p in ("holdout", "frozen", "paper_live", "grokteam", ".nextgen") for p in parts):
            raise AssertionError("Protected path refused")
        if "asset_expansion" in parts and "cache" in parts:
            raise AssertionError("Protected cache refused")
        if str(args[0]).endswith(".jsonl"):
            raise AssertionError("Actual ledgers excluded")


sys.addaudithook(guard)
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    import main
    import statsmodels.api
    from core.app_paths import application_root, assets_directory
    from ui.research_home import build_home_page, recorded_status
    import core.calendars.store as calendars

if "site-packages" not in Path(main.__file__).parts:
    raise AssertionError("Smoke imported source checkout instead of installed wheel")
status, error = recorded_status()
assert status is not None and not error, error
assets = Path(assets_directory())
for name in ("branding/f1-symbol.svg", "branding/f1-wordmark.svg", "fonts/qg-interface.otf", "fonts/OFL.txt"):
    assert (assets / name).is_file(), name
assert (calendars.DATA_DIR / "MANIFEST.yaml").is_file()
assert len(list(calendars.DATA_DIR.glob("*.yaml"))) >= 18
assert any(r.startswith("statsmodels") for r in importlib.metadata.requires("quantgen"))
assert build_home_page(SimpleNamespace(), navigate=lambda _: None) is not None
print(json.dumps({"status": "PASS", "platform": sys.platform, "scope": "installed imports, Home, recorded status, assets and calendar payload presence", "version": importlib.metadata.version("quantgen"), "live_providers": "NOT_RUN", "engine_start": "NOT_RUN"}))
