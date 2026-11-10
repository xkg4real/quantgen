"""Headed sentence bullets for the Analysis panel, in the page's language (owner UI review, 2026-11-10).

The owner reads the app in Korean (`LocaleContext('ko_KR')`) and found every Analysis panel to be one
English paragraph. The native app already has reviewed Korean twins of the local narratives
(`quantgen_desktop/*_narrative*.py`, `*_narrative_language.py`: pure Python, no Qt imports). A page
whose narrative has such a twin passes `sections=localized(english, korean_text)` to
`ui.ai_panel.analysis_panel`: in Korean the panel shows the Korean text, in any other language the
English text, both cut into sentence bullets under the same short headings.

Presentation only:
  * The English narrative stays the panel's `narrative` argument, unchanged: the payload, the deep
    analysis and the tests read it, and it stays available as the full paragraph under the bullets.
  * The Korean text is exactly what the native function returns. This module adds headings; it never
    writes a number or a statement, and it never reorders sentences (headings are inserted between
    them in reading order).
  * When the native function cannot read a result (returns None or raises), the page passes no
    sections and the panel keeps its own English bullets instead of a half-translated read.
"""
from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Callable, Optional, Sequence, Union

from ui.ai_panel import split_sentences

Sections = list[tuple[str, list[str]]]
Body = Union[str, Sequence[str]]
# An extra part: ((Korean heading, English heading), Korean body or None when there is none, English body).
Extra = tuple[tuple[str, str], Optional[Body], Body]

HEADINGS = {
    "summary": ("요약", "Summary"),
    "figures": ("핵심 수치", "Key figures"),
    "limits": ("해석과 한계", "Interpretation and limits"),
}
SHORT = 4            # a narrative of this many sentences or fewer reads under one heading

# The trailing run of sentences without a figure (or that state the data status) is the read's
# interpretation, conventions and caveats; a sentence with a digit carries figures.
_DIGIT = re.compile(r"\d")
_STATUS = re.compile(r"SYNTHETIC|NOT_RUN|합성")
# A Korean sentence ends in "다." even when the next one opens with a lower-case model note or a sign
# ("... 반영합니다. nelson-siegel 적합의 ...", "... 입니다. +1bp ..."), which split_sentences keeps together.
_KO_END = re.compile(r"(?<=다\.)\s+(?=\S)")


def _ko(language: str) -> bool:
    return language == "ko"


def sentences(text: str, language: str) -> list[str]:
    """`ui.ai_panel.split_sentences`, plus the Korean "다." ending; joined with spaces they give the text back."""
    parts = split_sentences(text)
    if not _ko(language):
        return parts
    return [s for part in parts for s in (x.strip() for x in _KO_END.split(part)) if s]


def _limit_like(sentence: str) -> bool:
    return not _DIGIT.search(sentence) or bool(_STATUS.search(sentence))


def organise(text: str, language: str) -> Sections:
    """One narrative as sentence bullets under short headings, in reading order.

    Up to SHORT sentences: one heading (Summary). Longer: the first sentence is the summary, the
    trailing run of sentences without figures is "Interpretation and limits", the rest "Key figures"."""
    parts = sentences(text, language)
    if not parts:
        return []
    side = 0 if _ko(language) else 1
    if len(parts) <= SHORT:
        return [(HEADINGS["summary"][side], parts)]
    cut = len(parts)
    while cut > 1 and _limit_like(parts[cut - 1]):
        cut -= 1
    out: Sections = [(HEADINGS["summary"][side], parts[:1])]
    if parts[1:cut]:
        out.append((HEADINGS["figures"][side], parts[1:cut]))
    if parts[cut:]:
        out.append((HEADINGS["limits"][side], parts[cut:]))
    return out


def _lines(body: Body, language: str) -> list[str]:
    if isinstance(body, str):
        return sentences(body, language)
    return [str(x).strip() for x in body if str(x).strip()]


def korean(fn: Callable[..., Optional[str]], *args, **kwargs) -> Optional[str]:
    """The native Korean text for a result, or None when the reviewed function cannot read it."""
    try:
        text = fn(*args, **kwargs)
    except Exception:            # display only: a failed translation must not take the results down
        return None
    return text if isinstance(text, str) and text.strip() else None


def localized(english: str, korean_text: Optional[str], *,
              extra: Sequence[Extra] = ()) -> Optional[Callable[[object], Sections]]:
    """`sections=` for `analysis_panel`: `korean_text` organised in Korean, `english` in any other
    language, each followed by the `extra` parts under their own headings. None (the panel's own English
    bullets) when the Korean text, or the Korean body of an extra part, is missing: the two languages
    always show the same parts."""
    if not korean_text or any(body_ko is None for _, body_ko, _ in extra):
        return None

    def sections(ctx) -> Sections:
        ko = getattr(ctx, "language", "en") == "ko"
        out = organise(korean_text if ko else english, "ko" if ko else "en")
        for (heading_ko, heading_en), body_ko, body_en in extra:
            lines = _lines(body_ko if ko else body_en, "ko" if ko else "en")
            if lines:
                out.append((heading_ko if ko else heading_en, lines))
        return out
    return sections


# --------------------------------------------------------------------------- #
# Adapters for native functions that read the native workflow's output object
# --------------------------------------------------------------------------- #
def fx_text(tool: str, data: dict) -> Optional[str]:
    """`quantgen_desktop.fx_narrative.fx_korean` reads `out.request.tool` and `out.data` (the dict
    `core.research.fx_analysis.execute_fx` builds); the page passes the same keys it computed."""
    from quantgen_desktop.fx_narrative import fx_korean
    return korean(fx_korean, SimpleNamespace(request=SimpleNamespace(tool=tool), data=data))


def macro_text(sheet, tool: str, narrative: str) -> Optional[str]:
    """`quantgen_desktop.macro_narrative_language.macro_korean` reads `out.sheet`, `out.request.tool`
    ('sheet' | 'daily' | 'weekly') and `out.narrative`, and returns None unless the narrative is the
    current locally generated one."""
    from quantgen_desktop.macro_narrative_language import macro_korean
    return korean(macro_korean, SimpleNamespace(sheet=sheet, request=SimpleNamespace(tool=tool),
                                                narrative=narrative))
