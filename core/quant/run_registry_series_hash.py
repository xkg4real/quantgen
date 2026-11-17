"""Pure supplied-array content SHA-256 for the detached R3 series format v1.

This identifies supplied float64 bits and shape. It does not store or load a
series, validate dates/PnL, construct series_ref, or authenticate research data.
"""
from __future__ import annotations

import hashlib

import numpy as np


_HEADER = b"quantgen.r3.series/1\x00<f8\x00"


class SeriesHashError(ValueError):
    """The supplied array is outside the explicit v1 supported domain."""


def series_sha256(array: np.ndarray) -> str:
    """Hash the v1 header, two uint64-LE dimensions, then ``<f8`` C-order bits.

    Accept only an exact two-dimensional ndarray with float64 dtype and no
    dtype metadata. Empty axes are valid for identity, not necessarily storage.
    Subclasses, memmap objects and coercible values are refused without casting.

    Either endian, arbitrary valid strides and read-only arrays are supported.
    Integer word conversion preserves signed zeros, infinities and NaN payloads,
    including signalling NaNs, without floating-point normalization. The input
    is not mutated and must remain stable during the call. No concurrent-write
    snapshot, backing-buffer provenance or hostile-memory guarantee is made.
    This helper performs no I/O, clock, configuration or environment lookup.
    """
    if type(array) is not np.ndarray:
        raise SeriesHashError("array must be an exact numpy.ndarray")
    if array.ndim != 2:
        raise SeriesHashError("array must have exactly two dimensions")
    if array.dtype.kind != "f" or array.dtype.itemsize != 8:
        raise SeriesHashError("array must already have float64 dtype")
    if array.dtype.metadata is not None:
        raise SeriesHashError("array dtype must not have metadata")

    # An integer view avoids float casts that could quiet signalling NaNs or
    # change payload bits. Conversion changes byte order only, not word values.
    words = array.view(np.dtype("u8").newbyteorder(array.dtype.byteorder))
    raw = words.astype(np.dtype("<u8"), copy=False).tobytes(order="C")
    digest = hashlib.sha256()
    digest.update(_HEADER)
    for dimension in array.shape:
        digest.update(dimension.to_bytes(8, "little", signed=False))
    digest.update(raw)
    return digest.hexdigest()
