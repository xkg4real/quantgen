"""Detached in-memory NPY1 encoding and content-checked decoding for R3.

Only supplied arrays/bytes are used. No file store, paths, recorder, Lab,
research validity, dates/configuration metadata or owner decisions are involved.
"""
from __future__ import annotations

import ast
from io import BytesIO
import re

import numpy as np

from core.quant.run_registry_series_hash import series_sha256


_MAGIC = b"\x93NUMPY\x01\x00"
_HEADER_LIMIT = 10_000
_INTP_MAX = int(np.iinfo(np.intp).max)
_AXIS_MAX = min(_INTP_MAX // 8, 2**64 - 1)
_DIGEST = re.compile(r"[0-9a-f]{64}")


class SeriesFormatError(ValueError):
    """Input or serialization is outside the explicit bounded NPY1 profile."""


class _BoundedBytesIO(BytesIO):
    def __init__(self, limit: int):
        super().__init__()
        self._limit = limit

    def write(self, data):
        # A multidimensional memoryview's len is its first axis, not bytes.
        view = memoryview(data)
        if self.tell() + view.nbytes > self._limit:
            raise SeriesFormatError("serialized series exceeds max_bytes")
        return super().write(view)


def _budget(max_bytes: int) -> int:
    if type(max_bytes) is not int or not 0 < max_bytes <= _INTP_MAX:
        raise SeriesFormatError("max_bytes must be a plain positive int within np.intp")
    return max_bytes


def _shape(shape) -> tuple[int, int]:
    if type(shape) is not tuple or len(shape) != 2:
        raise SeriesFormatError("shape must be a tuple of two dimensions")
    if any(type(d) is not int or not 0 <= d <= _AXIS_MAX for d in shape):
        raise SeriesFormatError("dimensions must be plain nonnegative ints within the axis bound")
    return shape


def _header(payload: bytes) -> tuple[int, tuple[int, int]]:
    """Validate the bounded stored header and raw length before any array load."""
    if len(payload) < 10 or payload[:8] != _MAGIC:
        raise SeriesFormatError("payload must be a complete NPY version 1.0 header")
    length = int.from_bytes(payload[8:10], "little")
    end = 10 + length
    if length > _HEADER_LIMIT or end > len(payload):
        raise SeriesFormatError("NPY header is oversized or truncated")
    if length == 0 or payload[end - 1:end] != b"\n" or end % 16:
        raise SeriesFormatError("NPY header must end in LF at a 16-byte-aligned offset")
    try:
        expression = ast.parse(payload[10:end].decode("latin1").strip(), mode="eval")
        node = expression.body
        if not isinstance(node, ast.Dict) or len(node.keys) != 3:
            raise SeriesFormatError("NPY header must have exactly three literal keys")
        if any(not isinstance(key, ast.Constant) or type(key.value) is not str
               for key in node.keys):
            raise SeriesFormatError("NPY header keys must be literal strings")
        keys = [key.value for key in node.keys]
        if len(set(keys)) != 3 or set(keys) != {"descr", "fortran_order", "shape"}:
            raise SeriesFormatError("NPY header keys are missing, duplicated or unsupported")
        header = ast.literal_eval(expression)
    except (SyntaxError, TypeError, ValueError, RecursionError) as exc:
        if isinstance(exc, SeriesFormatError):
            raise
        raise SeriesFormatError("NPY header must be a supported literal dictionary") from exc
    if type(header["descr"]) is not str or header["descr"] != "<f8":
        raise SeriesFormatError("stored dtype must be exactly <f8")
    if header["fortran_order"] is not False:
        raise SeriesFormatError("stored order must be C order")
    shape = _shape(header["shape"])
    # Python integer arithmetic precedes NumPy's fixed-width count/allocation.
    if shape[0] * shape[1] * 8 != len(payload) - end:
        raise SeriesFormatError("raw data length differs from shape, or trailing bytes exist")
    return end, shape


def encode_series(array: np.ndarray, *, max_bytes: int) -> bytes:
    """Return bounded NPY1 bytes with canonical LE/C float64 words.

    The caller supplies a stable exact 2-D float64 ndarray without dtype
    metadata. Empty axes identify content only, not valid research/storage.
    The byte ceiling bounds serialized output, not peak memory or CPU. No
    float arithmetic, input mutation or content/source discovery occurs.
    """
    limit = _budget(max_bytes)
    if type(array) is not np.ndarray or array.ndim != 2:
        raise SeriesFormatError("array must be an exact two-dimensional numpy.ndarray")
    if array.dtype.kind != "f" or array.dtype.itemsize != 8 or array.dtype.metadata is not None:
        raise SeriesFormatError("array must already be float64 without dtype metadata")
    shape = _shape(array.shape)
    size = shape[0] * shape[1] * 8
    if size > limit:
        raise SeriesFormatError("array bytes exceed max_bytes before serialization")
    # Header-only preparation precedes a potentially large endian/layout copy.
    with _BoundedBytesIO(min(limit, _HEADER_LIMIT + 10)) as preview:
        np.lib.format.write_array_header_1_0(
            preview, {"descr": "<f8", "fortran_order": False, "shape": shape})
        header_size = preview.tell()
    if header_size + size > limit:
        raise SeriesFormatError("NPY header and array bytes exceed max_bytes")

    words = array.view(np.dtype("u8").newbyteorder(array.dtype.byteorder))
    canonical = words.astype(np.dtype("<u8"), order="C", copy=False).view("<f8")
    with _BoundedBytesIO(limit) as output:
        np.save(output, canonical, allow_pickle=False)
        payload = output.getvalue()
    if len(payload) > limit:
        raise SeriesFormatError("serialized series exceeds max_bytes")
    # Refuse a future writer changing the supported version/layout, rather
    # than silently emitting a format this decoder does not promise to read.
    _header(payload)
    return payload


def decode_series(payload: bytes, expected_sha256: str, *, max_bytes: int) -> np.ndarray:
    """Validate an NPY1 payload and supplied content SHA before returning it.

    Header/shape/raw-size checks precede np.load with allow_pickle=False.
    The returned array is read-only for convenience, not tamper-proof. The
    expected hash is caller evidence, not an authenticity/authority anchor.
    MemoryError propagates; parser recursion is a typed format refusal. No
    partial or fabricated array is returned.
    """
    limit = _budget(max_bytes)
    if type(payload) is not bytes:
        raise SeriesFormatError("payload must be exact bytes")
    if type(expected_sha256) is not str or _DIGEST.fullmatch(expected_sha256) is None:
        raise SeriesFormatError("expected_sha256 must be a plain lowercase 64-hex string")
    if len(payload) > limit:
        raise SeriesFormatError("payload exceeds max_bytes")
    _, shape = _header(payload)
    try:
        with BytesIO(payload) as source:
            array = np.load(source, allow_pickle=False, max_header_size=_HEADER_LIMIT)
            if source.tell() != len(payload):
                raise SeriesFormatError("NPY reader left trailing bytes")
    except (ValueError, EOFError, TypeError) as exc:
        if isinstance(exc, SeriesFormatError):
            raise
        raise SeriesFormatError("NPY array could not be decoded in the supported profile") from exc
    if (type(array) is not np.ndarray or array.shape != shape
            or array.dtype != np.dtype("<f8") or array.dtype.metadata is not None
            or not array.flags.c_contiguous):
        raise SeriesFormatError("decoded array differs from the validated profile")
    if series_sha256(array) != expected_sha256:
        raise SeriesFormatError("series content SHA-256 mismatch")
    array.setflags(write=False)
    return array
