"""Read-only shipped resources in a source checkout, an installed wheel or a packaged app, and the
per-user data folder (OS-P0-c).

Nothing here opens or lists a folder. Folders are created only by ensure_user_data_dir() (for a writer) and
migrate_legacy_data() (only with the user's explicit consent); user_data_dir() may add the marker file to a
platform folder that already exists. The writers (config.py trading/macro/ficc caches, data/krx/kis_client.py token file,
data/krx/opendart_client.py corp-code cache) take their folder from user_data_dir() since OS-F2 (2026-11-20).
"""
from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import shutil
import sys
import sysconfig

LEGACY_DATA_DIRNAME = ".nextgen"      # used by every build so far (config.py, kis_client.py, opendart_client.py)
DATA_DIRNAME = "QUANTGEN"             # new installs; shown to the user in Explorer/Finder
DATA_DIR_ENV = "QUANTGEN_DATA_DIR"    # explicit override (tests, portable runs); name from the Notion platform plan F2
FLET_STORAGE_ENV = "FLET_APP_STORAGE_DATA"  # set by a packaged Flet (mobile) app: its private storage folder
DATA_MARKER = ".quantgen-data-dir"    # in the platform folder: QUANTGEN made it (date and format only)
DATA_MARKER_FORMAT = 1


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


def _is_marked(folder: Path) -> bool:
    return (folder / DATA_MARKER).is_file()


def _stamp(folder: Path) -> None:
    """Write the marker that says QUANTGEN made this folder (creation date and marker format only)."""
    marker = folder / DATA_MARKER
    if not marker.exists():
        marker.write_text(json.dumps({"app": DATA_DIRNAME, "created": date.today().isoformat(),
                                      "format": DATA_MARKER_FORMAT}) + "\n", encoding="utf-8")


def _resolve(home: Path, env, platform: str):
    """(folder, source) for user_data_dir() and data_location(); never creates or writes anything."""
    for name, source in ((DATA_DIR_ENV, "override"), (FLET_STORAGE_ENV, "flet")):
        if env.get(name):
            return Path(env[name]), source
    target = _platform_data_dir(home, env, platform)
    if target.is_dir() and _is_marked(target):
        return target, "platform"
    legacy = home / LEGACY_DATA_DIRNAME
    if legacy.is_dir():
        return legacy, "legacy"
    return target, "platform"


def user_data_dir(*, home=None, env=None, platform=None) -> Path:
    """Where per-user state lives (tokens, caches, trading state). Order (main decision 2026-11-20):
    QUANTGEN_DATA_DIR, FLET_APP_STORAGE_DATA (packaged Flet app), the platform folder when QUANTGEN's marker is in it,
    an existing ~/.nextgen (so no earlier user loses a token or cache), else the platform folder.

    The marker keeps a new user in the platform folder even if another app (TRADEGEN) creates ~/.nextgen later, and
    keeps QUANTGEN out of an empty folder some other tool made. Nothing is created here; the only write is the marker,
    added when the platform folder is chosen and already exists without one (a writer made it with mkdir).
    The arguments exist for tests; callers pass nothing."""
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    folder, source = _resolve(home, env, sys.platform if platform is None else platform)
    if source == "platform" and folder.is_dir() and not _is_marked(folder):
        try:
            _stamp(folder)
        except OSError:
            pass
    return folder


def ensure_user_data_dir() -> Path:
    """Create user_data_dir() (0o700) for a writer, with the marker when it is the platform folder."""
    env, home = os.environ, Path.home()
    folder, source = _resolve(home, env, sys.platform)
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    if source == "platform":
        _stamp(folder)
    return folder


def user_data_path(*parts: str) -> Path:
    """A path inside user_data_dir() (nothing is created)."""
    return user_data_dir().joinpath(*parts)


@dataclass(frozen=True)
class DataLocation:
    """Where per-user state lives now, and what a move to the platform folder would do (OS-F2)."""
    path: Path                 # user_data_dir() today
    source: str                # "override", "flet", "legacy" or "platform"
    legacy: Path               # ~/.nextgen
    platform_path: Path        # the platform folder new installs use
    can_migrate: bool          # legacy in use, platform folder absent: migrate_legacy_data() may move it


def data_location(*, home=None, env=None, platform=None) -> DataLocation:
    """Describe the data folder for a settings screen or a one-time notice. Checks only whether folders and the
    marker exist; never lists, opens, writes or moves anything."""
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    plat = sys.platform if platform is None else platform
    current, source = _resolve(home, env, plat)
    legacy = home / LEGACY_DATA_DIRNAME
    target = _platform_data_dir(home, env, plat)
    return DataLocation(current, source, legacy, target,
                        source == "legacy" and not target.exists())


class MigrationRefused(RuntimeError):
    pass


def migrate_legacy_data(*, confirmed: bool, home=None, env=None, platform=None) -> Path:
    """Move ~/.nextgen to the platform folder, once, after the user agreed in the app (confirmed=True).

    Refuses (MigrationRefused) without consent, when an override decides the folder, when ~/.nextgen is not in use,
    or when the platform folder already exists (nothing is merged or overwritten). TRADEGEN reads the shared KIS token
    at ~/.nextgen/kis_token.json, so the consent text must say that sharing ends. Returns the new folder."""
    if confirmed is not True:
        raise MigrationRefused("the user has not agreed to move the data folder")
    where = data_location(home=home, env=env, platform=platform)
    if where.source != "legacy":
        raise MigrationRefused(f"the data folder is not ~/.nextgen ({where.source})")
    if where.platform_path.exists():
        raise MigrationRefused(f"{where.platform_path} already exists; nothing is merged or overwritten")
    where.platform_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    shutil.move(str(where.legacy), str(where.platform_path))
    _stamp(where.platform_path)
    return where.platform_path
