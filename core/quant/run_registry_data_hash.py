"""Pure supplied-panel data MD5 from R3 revision 2, section 5.4.

This hashes the supplied dates, literal symbols and float64 bits. It does not
load or align data, validate prices or providers, infer a holdout, record a run,
or authenticate evidence. No I/O, configuration lookup or clock is used.
"""
from __future__ import annotations

from datetime import date
import hashlib
import re

import numpy as np


_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class DataHashError(ValueError):
    """Input is outside this helper's explicit supported domain."""


def _labels(values, name: str) -> bytes:
    if type(values) not in (list, tuple) or not values:
        raise DataHashError(f"{name} must be a nonempty plain list or tuple")
    for value in values:
        if type(value) is not str or not value or "\n" in value or "\0" in value:
            raise DataHashError(f"{name} must contain nonempty plain strings without LF or NUL")
        if name == "dates":
            if _DATE.fullmatch(value) is None:
                raise DataHashError("dates must use ASCII YYYY-MM-DD")
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise DataHashError("dates must be valid calendar dates") from exc
    try:
        return "\n".join(values).encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise DataHashError(f"{name} must be valid UTF-8 text") from exc


def data_md5(dates: list[str] | tuple[str, ...], symbols: list[str] | tuple[str, ...],
             closes: np.ndarray) -> str:
    """Hash LF-joined dates, NUL, LF-joined symbols, NUL, then ``<f8`` C bytes.

    The supported domain is deliberately narrow: nonempty plain string lists or
    tuples, valid ASCII calendar dates, and an exact two-dimensional ``ndarray``
    of IEEE float64 with shape ``(len(dates), len(symbols))``. Other dtypes,
    ndarray subclasses, masked arrays and memmaps are refused rather than cast.
    Symbols retain case, whitespace, CR and Unicode codepoints; LF/NUL, empty
    tokens and unencodable text are refused. Dates are neither sorted nor deduped.

    Either endian, any strides and read-only arrays are supported. Float64 bits,
    including signed zero, infinities and NaN payloads, are preserved by integer
    byte-order conversion only. No finite-value cleanup or semantic normalization
    occurs. Inputs are not mutated and must remain stable during the call; there
    is no concurrent-mutation snapshot guarantee. MD5 is not authentication.
    """
    date_bytes = _labels(dates, "dates")
    symbol_bytes = _labels(symbols, "symbols")
    if type(closes) is not np.ndarray:
        raise DataHashError("closes must be an exact numpy.ndarray")
    if closes.ndim != 2 or closes.shape != (len(dates), len(symbols)):
        raise DataHashError("closes must have shape (number of dates, number of symbols)")
    if closes.dtype.kind != "f" or closes.dtype.itemsize != 8:
        raise DataHashError("closes must already be float64")

    # Viewing the original endian as unsigned words avoids any floating-point
    # conversion that could quiet signalling NaNs or alter their payload bits.
    words = closes.view(np.dtype("u8").newbyteorder(closes.dtype.byteorder))
    raw = words.astype(np.dtype("<u8"), copy=False).tobytes(order="C")
    digest = hashlib.md5(usedforsecurity=False)
    digest.update(date_bytes)
    digest.update(b"\0")
    digest.update(symbol_bytes)
    digest.update(b"\0")
    digest.update(raw)
    return digest.hexdigest()
