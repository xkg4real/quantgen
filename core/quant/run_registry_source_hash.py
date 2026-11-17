"""Raw and CRLF-to-LF SHA-256 for supplied source content (R3 section 3.3).

These helpers do not collect source, inspect functions, read files or discover
git/config/environment state. A digest of supplied content does not establish
its origin, complete strategy code identity, authenticity or semantic equality.
"""
import hashlib


class SourceHashError(ValueError):
    """Input is outside the explicit plain-str/plain-bytes domain."""


def source_bytes_hashes(source: bytes) -> dict[str, str]:
    """Return a fresh ``{lf, raw}`` dictionary for exact supplied bytes.

    Bytes are opaque: no decoding, encoding detection or BOM removal occurs.
    Replace each original CRLF pair once with LF; preserve lone CR, indentation,
    whitespace and final-newline presence. In particular CRCRLF becomes CRLF,
    not LF: replacement is one pass, not repeated until stable. Empty is valid.
    Bytearray, memoryview, subclasses and file-like objects are not coerced.
    """
    if type(source) is not bytes:
        raise SourceHashError("source must be plain bytes")
    return {"lf": hashlib.sha256(source.replace(b"\r\n", b"\n")).hexdigest(),
            "raw": hashlib.sha256(source).hexdigest()}


def source_text_hashes(source: str) -> dict[str, str]:
    """Return raw/LF digests of plain source text encoded as strict UTF-8.

    Unicode codepoints, BOM, indentation and final-newline presence are retained;
    only the single-pass CRLF conversion differs between the two hashes. No
    stripping, dedenting, Unicode/AST normalization or source inspection occurs.
    Empty is valid. Unpaired surrogates and non-plain strings are refused.
    """
    if type(source) is not str:
        raise SourceHashError("source must be a plain string")
    try:
        encoded = source.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise SourceHashError("source must encode as strict UTF-8") from exc
    return source_bytes_hashes(encoded)
