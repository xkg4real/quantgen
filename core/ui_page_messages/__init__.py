"""Page-level English→Korean display captions for the Flet workspace (owner UI review, 2026-11-10).

One module per page group so captions can be authored without editing the shared
legacy catalogue. `core.ui_legacy_messages` merges `PAGE_EN_TO_KO` after its own
reviewed entries with `setdefault`, so an existing reviewed caption always wins.
Keys are exact English source strings as they appear in the page code; values are
the Korean captions. Inputs, identifiers, ticker symbols and verdict codes are not
translated.
"""
from . import strategy_lab, charts, rates, market_chart, ficc_pages, build_pages

PAGE_EN_TO_KO: dict[str, str] = {}
for _module in (strategy_lab, charts, rates, market_chart, ficc_pages, build_pages):
    for _english, _korean in _module.EN_TO_KO.items():
        PAGE_EN_TO_KO.setdefault(_english, _korean)
