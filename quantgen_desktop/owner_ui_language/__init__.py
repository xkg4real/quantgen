"""Korean display text for the owner UI port (UI-D1/UI-D2, 2026-11-10), one module per screen area.

Each area module exposes `PAIRS = {english source text: Korean display text}`; a pair with '{name}'
fields is also a template in both directions. `quantgen_desktop.translations` merges them after its own
catalogue, so an area may correct an earlier display string. Two areas must not give the same English
text different Korean: `pairs()` refuses that instead of letting import order decide.

Display only: widgets keep their English source text, combo data and export payloads are unchanged.
"""
from importlib import import_module

AREAS = ("common", "strategy", "charts", "macro", "ficc", "market", "home", "risk", "stock")


def pairs():
    merged, owner = {}, {}
    for area in AREAS:
        module = import_module(f"{__name__}.{area}")
        for en, ko in module.PAIRS.items():
            if en in merged and merged[en] != ko:
                raise ValueError(f"{area} and {owner[en]} give {en!r} different Korean text")
            merged[en], owner[en] = ko, area
    return merged
