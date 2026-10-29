"""Read-only shipped resources in a source checkout or an installed wheel."""
from pathlib import Path
import sysconfig


def application_root() -> Path:
    source = Path(__file__).resolve().parents[1]
    if (source / "assets/branding/f1-symbol.svg").is_file() and (source / "README.md").is_file():
        return source
    return Path(sysconfig.get_path("data")) / "share" / "quantgen"


def assets_directory() -> str:
    return str(application_root() / "assets")
