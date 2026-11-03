"""QUANTGEN brand palette for the common C chart design. Existing semantic tokens and dark/system modes remain."""
from __future__ import annotations
from dataclasses import dataclass

RADII = {"sm": 8, "md": 12, "lg": 16, "pill": 999}
BREAKPOINTS = {"compact": 700, "medium": 1200}
TRANSITION_MS = 180
MODES = ("dark", "light", "system")
DEFAULT_MODE = "system"

@dataclass(frozen=True)
class Palette:
    bg: str
    surface: str
    surface_2: str
    border: str
    text: str
    muted: str
    accent: str
    accent_soft: str
    success: str
    error: str
    on_accent: str
    warning: str = "#d9a441"      # last, with a default: positional constructors keep working (02_ui_design 3)

DARK = Palette("#101915", "#17231D", "#1E2D25", "#34483C", "#EAF1E9", "#A7B8AC", "#91C5AC", "#284437", "#9AC47D", "#E79A83", "#0C2118", "#E5BE74")
LIGHT = Palette("#F7F5F0", "#FFFEFB", "#F1F2EB", "#E2E3DB", "#202823", "#646E68", "#194C40", "#E5EEE8", "#16745F", "#AA543C", "#FFFFFF", "#8a5a00")
_state = {"mode": DEFAULT_MODE, "palette": DARK}

def palette_for(mode: str, *, system_is_dark: bool = True) -> Palette:
    mode = (mode or DEFAULT_MODE).lower()
    if mode == "light": return LIGHT
    if mode == "dark": return DARK
    return DARK if system_is_dark else LIGHT

def set_mode(mode: str, *, system_is_dark: bool = True) -> Palette:
    p = palette_for(mode, system_is_dark=system_is_dark)
    _state.update(mode=mode if mode in MODES else DEFAULT_MODE, palette=p)
    return p

def active() -> Palette: return _state["palette"]
def active_mode() -> str: return _state["mode"]
def token_names() -> tuple[str, ...]: return tuple(Palette.__dataclass_fields__)
