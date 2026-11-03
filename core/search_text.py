"""Shared, dependency-free matching for search boxes (guide terms, instrument names).

Korean and English names match regardless of the interface language. Text is
NFC-normalized, case-folded and stripped of separators; Hangul syllables can
also be matched by their initial consonants (e.g. 'ㅇㅍ' for 애플).
"""
from __future__ import annotations

import re
import unicodedata

SEPARATORS = re.compile(r"[\s·\-–_/().,&+~:']")
INITIALS = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'


def normal(text):
    return SEPARATORS.sub('', unicodedata.normalize('NFC', str(text)).casefold())


def initials(text):
    out = []
    for char in text:
        code = ord(char) - 0xAC00
        out.append(INITIALS[code // 588] if 0 <= code < 11172 else char)
    return ''.join(out)


def is_initials(wanted):
    return bool(wanted) and all(char in INITIALS for char in wanted)


def name_score(wanted, candidate, *, jamo=None):
    """0 exact, 1 prefix (or initials prefix), 2 substring, 3 initials substring; None for no match.

    `wanted` must already be normalized with `normal()`.
    """
    jamo = is_initials(wanted) if jamo is None else jamo
    text = normal(candidate)
    if text == wanted:
        return 0
    if text.startswith(wanted) or (jamo and initials(text).startswith(wanted)):
        return 1
    if len(wanted) >= 2 and wanted in text:
        return 2
    if jamo and len(wanted) >= 2 and wanted in initials(text):
        return 3
    return None


def best_score(wanted, candidates):
    jamo = is_initials(wanted)
    scores = [s for s in (name_score(wanted, c, jamo=jamo) for c in candidates) if s is not None]
    return min(scores) if scores else None
