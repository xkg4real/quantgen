"""Put the package on sys.path and locate optional host files (read only)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HOST = ROOT.parent                      # the host repository, when this directory still lives inside it
CARDS = HOST / "docs" / "asset_expansion" / "cards"
