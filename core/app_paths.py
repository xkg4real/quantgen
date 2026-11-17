"""Read-only shipped resources in a source checkout, an installed wheel or a packaged app, and the
per-user data folder (OS-P0-c).

Nothing here creates, opens or lists a folder; the functions only compute paths. Callers that write
(config.py, data/krx/kis_client.py, data/krx/opendart_client.py) switch to user_data_dir() in OS-F2,
after the payments/account session's KEY-2; until then they keep their own ~/.nextgen paths.
"""
import os
from pathlib import Path
import sys
import sysconfig

LEGACY_DATA_DIRNAME = ".nextgen"      # used by every build so far (config.py, kis_client.py, opendart_client.py)
DATA_DIRNAME = "QUANTGEN"             # new installs; shown to the user in Explorer/Finder
DATA_DIR_ENV = "QUANTGEN_DATA_DIR"    # explicit override (tests, portable runs); name from the Notion platform plan F2
FLET_STORAGE_ENV = "FLET_APP_STORAGE_DATA"  # set by a packaged Flet (mobile) app: its private storage folder


def is_frozen() -> bool:
    """True inside a packaged app (PyInstaller sets sys.frozen and unpacks into sys._MEIPASS)."""
    return bool(getattr(sys, "frozen", False))


def application_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    source = Path(__file__).resolve().parents[1]
    if (source / "assets/branding/f1-symbol.svg").is_file() and (source / "README.md").is_file():
        return source
    return Path(sysconfig.get_path("data")) / "share" / "quantgen"


def assets_directory() -> str:
    return str(application_root() / "assets")


def _platform_data_dir(home: Path, env, platform: str) -> Path:
    if platform == "win32":
        base = env.get("LOCALAPPDATA") or env.get("APPDATA")
        return Path(base) / DATA_DIRNAME if base else home / "AppData" / "Local" / DATA_DIRNAME
    if platform == "darwin":
        return home / "Library" / "Application Support" / DATA_DIRNAME
    base = env.get("XDG_DATA_HOME")
    return (Path(base) if base else home / ".local" / "share") / DATA_DIRNAME.lower()


def user_data_dir(*, home=None, env=None, platform=None) -> Path:
    """Where per-user state lives (tokens, caches, trading state). The existing ~/.nextgen wins when it
    is there, so no user loses a token or cache; otherwise the platform's per-user application folder.
    Order: QUANTGEN_DATA_DIR, FLET_APP_STORAGE_DATA (packaged Flet app), existing ~/.nextgen, platform folder.
    The arguments exist for tests; callers pass nothing."""
    env = os.environ if env is None else env
    for name in (DATA_DIR_ENV, FLET_STORAGE_ENV):
        if env.get(name):
            return Path(env[name])
    home = Path.home() if home is None else Path(home)
    legacy = home / LEGACY_DATA_DIRNAME
    if legacy.is_dir():
        return legacy
    return _platform_data_dir(home, env, sys.platform if platform is None else platform)
