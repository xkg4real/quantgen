"""Read-only shipped resources in a source checkout, an installed wheel or a packaged app, and the
per-user data folder (OS-P0-c).

Path getters never create or write anything. The application prepares its mutable storage with
ensure_user_data_dir() before constructing stores; standalone writers must do the same. KIS and OpenDART's
file writers prepare their default folder themselves. migrate_legacy_data() requires explicit consent.
The writers (config.py trading/macro/ficc caches, data/krx/kis_client.py token file,
data/krx/opendart_client.py corp-code cache) use this selection since OS-F2 (2026-11-20).
"""
from dataclasses import dataclass
from datetime import date
import ctypes
import errno
import json
import os
from pathlib import Path
import stat
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
    marker = folder / DATA_MARKER
    return not marker.is_symlink() and marker.is_file()


def _stamp(folder: Path) -> None:
    """Create a marker without replacing an existing entry, or validate the existing regular marker.

    Refuse directories, links, malformed data and unsupported formats before a writer uses the folder.
    A failed/partial marker write is left for inspection, never silently overwritten or treated as valid.
    """
    marker = folder / DATA_MARKER
    try:
        with marker.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps({"app": DATA_DIRNAME, "created": date.today().isoformat(),
                                     "format": DATA_MARKER_FORMAT}) + "\n")
        return
    except FileExistsError:
        pass
    if marker.is_symlink():
        raise OSError(errno.EINVAL, "the data-folder marker is a symbolic link", str(marker))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(marker, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.EINVAL, "the data-folder marker is not a regular file", str(marker))
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = None
            payload = json.load(handle)
        if (not isinstance(payload, dict) or set(payload) != {"app", "created", "format"}
                or payload["app"] != DATA_DIRNAME or type(payload["format"]) is not int
                or payload["format"] != DATA_MARKER_FORMAT or not isinstance(payload["created"], str)):
            raise ValueError("invalid data-folder marker")
        date.fromisoformat(payload["created"])
    except (ValueError, UnicodeError) as exc:
        raise OSError(errno.EINVAL, "the data-folder marker is malformed or unsupported", str(marker)) from exc
    finally:
        if fd is not None:
            os.close(fd)


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

    The marker keeps a prepared new user in the platform folder even if another app (TRADEGEN) creates ~/.nextgen
    later. This getter neither creates nor writes anything: application startup and standalone writers must call
    ensure_user_data_dir() before constructing mutable stores or writing default paths.
    The arguments exist for tests; callers pass nothing."""
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    return _resolve(home, env, sys.platform if platform is None else platform)[0]


def ensure_user_data_dir() -> Path:
    """Prepare the selected folder before creating stores/writing (0o700 for a new folder on POSIX).

    Pin one selection for this call: another app creating ~/.nextgen during mkdir does not redirect the write.
    A platform marker must be created or validated before returning. A refusal propagates before data is written.
    Existing legacy folders and explicit overrides retain their selection and do not receive a marker.
    """
    env, home = os.environ, Path.home()
    folder, source = _resolve(home, env, sys.platform)
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    if source == "platform":
        _stamp(folder)
    return folder


def user_data_path(*parts: str) -> Path:
    """A path inside user_data_dir() (nothing is created)."""
    return user_data_dir().joinpath(*parts)


def ensure_user_data_path(*parts: str) -> Path:
    """Prepare the default root for a standalone writer, then return its path inside that root."""
    return ensure_user_data_dir().joinpath(*parts)


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
                        source == "legacy" and not legacy.is_symlink() and not target.exists()
                        and not target.is_symlink())


class MigrationRefused(RuntimeError):
    pass


def _rename_no_replace(source: Path, target: Path) -> None:
    """Rename a directory without replacing even an empty destination; never copy/delete on failure.

    POSIX os.rename() can replace an empty directory, and shutil.move() can nest the source inside an
    existing destination. Use the native exclusive operation instead. Unsupported kernels/filesystems
    and cross-filesystem moves fail closed; a separate user-guided migration would be needed there.
    """
    if os.name == "nt":
        os.rename(source, target)  # Windows refuses an existing destination.
        return
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        if sys.platform.startswith("linux"):
            rename = libc.renameat2
            rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            result = rename(-100, os.fsencode(source), -100, os.fsencode(target), 1)  # AT_FDCWD, RENAME_NOREPLACE
        elif sys.platform == "darwin":
            rename = libc.renamex_np
            rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            result = rename(os.fsencode(source), os.fsencode(target), 4)  # RENAME_EXCL
        else:
            raise OSError(errno.ENOSYS, "exclusive directory rename is unavailable")
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, "exclusive directory rename is unavailable") from exc
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def migrate_legacy_data(*, confirmed: bool, home=None, env=None, platform=None) -> Path:
    """Move ~/.nextgen to the platform folder, once, after the user agreed in the app (confirmed=True).

    Refuses (MigrationRefused) without consent, when an override decides the folder, when ~/.nextgen is not in use,
    or when the platform folder already exists (nothing is merged, overwritten or nested). Only an exclusive native
    rename on the same filesystem is allowed. The marker is written before moving; a refused rename may leave that
    marker in the legacy folder, which stays selected with its data intact. This is not a crash-durability guarantee.
    TRADEGEN reads the shared KIS token at ~/.nextgen/kis_token.json, so the consent text must say that sharing ends.
    Returns the new folder."""
    if confirmed is not True:
        raise MigrationRefused("the user has not agreed to move the data folder")
    where = data_location(home=home, env=env, platform=platform)
    if where.source != "legacy":
        raise MigrationRefused(f"the data folder is not ~/.nextgen ({where.source})")
    if where.legacy.is_symlink():
        raise MigrationRefused("the legacy data folder is a symbolic link; it is not moved")
    if where.platform_path.exists():
        raise MigrationRefused(f"{where.platform_path} already exists; nothing is merged or overwritten")
    where.platform_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        _stamp(where.legacy)  # If writing fails, the source has not moved.
        _rename_no_replace(where.legacy, where.platform_path)
    except OSError as exc:
        raise MigrationRefused("the data folder could not be moved exclusively; no copy/delete fallback was used") from exc
    return where.platform_path
