"""Text similarity for near-duplicate detection: character shingles, Jaccard and MinHash.

Language-neutral on purpose (English and Korean in one code path): text is NFKC-normalised,
lower-cased and stripped to letters and digits with single spaces, then cut into overlapping
5-character shingles. MinHash signatures use hashlib (never Python's built-in hash, which changes
between runs), so a signature is the same on every machine and every run.

No model, no network, no clock. Article text is used in memory only and never stored here.
"""
from __future__ import annotations

import hashlib
import unicodedata
from typing import Callable, Mapping

SHINGLE = 5
SIGNATURE_SIZE = 128
_MASK = (1 << 64) - 1


class SimilarityError(ValueError):
    pass


def normalise(text: str) -> str:
    if not isinstance(text, str):
        raise SimilarityError("text must be a string")
    out, space = [], True
    for ch in unicodedata.normalize("NFKC", text).lower():
        if ch.isalnum():
            out.append(ch)
            space = False
        elif not space:
            out.append(" ")
            space = True
    return "".join(out).strip()


def shingles(text: str, size: int = SHINGLE) -> frozenset[str]:
    """Overlapping character shingles of the normalised text; a text shorter than one shingle is itself."""
    clean = normalise(text)
    if not clean:
        return frozenset()
    if len(clean) <= size:
        return frozenset({clean})
    return frozenset(clean[i: i + size] for i in range(len(clean) - size + 1))


def jaccard(a: frozenset, b: frozenset) -> float:
    """|A and B| / |A or B|; two empty sets have similarity 0 (nothing to compare is not "the same")."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def text_similarity(a: str, b: str) -> float:
    return jaccard(shingles(a), shingles(b))


def _hash64(data: bytes, salt: int) -> int:
    return int.from_bytes(hashlib.blake2b(data, digest_size=8, salt=salt.to_bytes(8, "big")).digest(), "big")


def minhash(items: frozenset[str], size: int = SIGNATURE_SIZE) -> tuple[int, ...]:
    """MinHash signature: for each of ``size`` salted hash functions, the smallest hash over the items."""
    if not items:
        raise SimilarityError("cannot sign an empty shingle set")
    base = [_hash64(item.encode("utf-8"), 0) for item in items]
    out = []
    for k in range(size):
        # one strong hash per item, then a cheap salted mix per function (deterministic, 64-bit)
        a, b = _hash64(b"a", k + 1) | 1, _hash64(b"b", k + 1)
        out.append(min((a * h + b) & _MASK for h in base))
    return tuple(out)


def signature_similarity(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    """Share of equal positions: an estimate of the Jaccard similarity (standard error about sqrt(s(1-s)/size))."""
    if len(a) != len(b) or not a:
        raise SimilarityError("signatures must have the same non-zero length")
    return sum(x == y for x, y in zip(a, b)) / len(a)


def article_similarity(texts: Mapping[str, str]) -> Callable[[object, object], float]:
    """A similarity callback for core/didm/novelty.py build_features: ``texts`` maps article_id to the
    text to compare (headline, or headline plus lead). Shingle sets are computed once per article."""
    cache: dict[str, frozenset[str]] = {}

    def lookup(article) -> frozenset[str]:
        key = article.article_id
        if key not in cache:
            if key not in texts:
                raise SimilarityError("no text for an article")
            cache[key] = shingles(texts[key])
        return cache[key]

    return lambda a, b: jaccard(lookup(a), lookup(b))
