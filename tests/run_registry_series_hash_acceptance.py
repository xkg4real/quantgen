"""Synthetic acceptance of the detached R3 series content SHA-256 format v1."""
import ast
import hashlib
import os
from pathlib import Path
import socket
import struct
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

from core.quant.run_registry_series_hash import SeriesHashError, series_sha256


ROOT = Path(__file__).resolve().parents[1]
# Literal preimages and expected SHA256 were prepared before product code with
# stdlib only, without NumPy or the helper. Tests do not read private fixtures.
HEADER = bytes.fromhex("7175616e7467656e2e72332e7365726965732f31003c663800")
VECTORS = (
    ('standard_2x2', (2, 2), '0000000000000000000000000000f03f00000000000000400000000000000080', '7175616e7467656e2e72332e7365726965732f31003c663800020000000000000002000000000000000000000000000000000000000000f03f00000000000000400000000000000080', '428709959da4b04f950606cf66e0d52f48ba4296b605b6d28ecae3135bb0809c'),
    ('standard_1x4', (1, 4), '0000000000000000000000000000f03f00000000000000400000000000000080', '7175616e7467656e2e72332e7365726965732f31003c663800010000000000000004000000000000000000000000000000000000000000f03f00000000000000400000000000000080', '072d7ee6eeb487742625891a1656e22e60511debf7dc4dd9721b568f295787aa'),
    ('standard_4x1', (4, 1), '0000000000000000000000000000f03f00000000000000400000000000000080', '7175616e7467656e2e72332e7365726965732f31003c663800040000000000000001000000000000000000000000000000000000000000f03f00000000000000400000000000000080', '8f4fb38f47039df43dd001bdcda0ba77ec23864fb664b0c6f0a1e29793fe7e11'),
    ('empty_0x0', (0, 0), '', '7175616e7467656e2e72332e7365726965732f31003c66380000000000000000000000000000000000', 'ac93f8f475323865c062dec991879b0089fbb770b75bdd1210fbb68dfa5c6865'),
    ('empty_0x3', (0, 3), '', '7175616e7467656e2e72332e7365726965732f31003c66380000000000000000000300000000000000', 'c72c4c4469e482ae3475aac28d33bf83cc19f50eb397a0e7c7d07401c0e08b7c'),
    ('empty_3x0', (3, 0), '', '7175616e7467656e2e72332e7365726965732f31003c66380003000000000000000000000000000000', '99d2355bdd2391e418f26d4d39bfa9d65999c3aae2ea7d07d56eed5a165290ed'),
    ('all_one_2x2', (2, 2), '000000000000f03f000000000000f03f000000000000f03f000000000000f03f', '7175616e7467656e2e72332e7365726965732f31003c66380002000000000000000200000000000000000000000000f03f000000000000f03f000000000000f03f000000000000f03f', 'ee97285acfa8ae3d111e964f599aa22075e8532c31f2fd15f273a7747d77c510'),
    ('all_zero_2x2', (2, 2), '0000000000000000000000000000000000000000000000000000000000000000', '7175616e7467656e2e72332e7365726965732f31003c663800020000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000', 'e8d28944fc5c3c617abc1be38b8263c991d5c0976c1bdb112a20ed2cc06082de'),
    ('ieee_2x4', (2, 4), '00000000000000000000000000000080000000000000f07f000000000000f0ff010000000000f87f020000000000f87f420000000000f07f420000000000f87f', '7175616e7467656e2e72332e7365726965732f31003c6638000200000000000000040000000000000000000000000000000000000000000080000000000000f07f000000000000f0ff010000000000f87f020000000000f87f420000000000f07f420000000000f87f', '25df772c8ef891aa366ecdf60d09f49b2bc1da21fb1a383b3f106b64b84c529f'),
    ('positive_zero_1x1', (1, 1), '0000000000000000', '7175616e7467656e2e72332e7365726965732f31003c663800010000000000000001000000000000000000000000000000', '58ab755295dec7ca09c729efb799ab102355cfe941310b25cfbb761bc8da7998'),
    ('negative_zero_1x1', (1, 1), '0000000000000080', '7175616e7467656e2e72332e7365726965732f31003c663800010000000000000001000000000000000000000000000080', '49e8d2869e39733eac5f89dd5456ed1d5938c683de53b85d9025a930bc09aa76'),
    ('quiet_nan_1_1x1', (1, 1), '010000000000f87f', '7175616e7467656e2e72332e7365726965732f31003c66380001000000000000000100000000000000010000000000f87f', 'b71fa92f51ea1fc91e57dcfbe40f74c9c2edd87ca6fe7f77f687f164ff9561f2'),
    ('quiet_nan_2_1x1', (1, 1), '020000000000f87f', '7175616e7467656e2e72332e7365726965732f31003c66380001000000000000000100000000000000020000000000f87f', '42a0684aa636202fe09a22b6aa65cba28adcd196878bba946f92f360c4dc035a'),
    ('signalling_nan_42_1x1', (1, 1), '420000000000f07f', '7175616e7467656e2e72332e7365726965732f31003c66380001000000000000000100000000000000420000000000f07f', 'f8032ebfcbb5cb4ede78b81d1f3e891cc4cb8c8b2b5087edb66884df98dc8873'),
    ('quiet_nan_42_1x1', (1, 1), '420000000000f87f', '7175616e7467656e2e72332e7365726965732f31003c66380001000000000000000100000000000000420000000000f87f', '5aa29951094bc6a235f892f9879f7a7c801c09966721ae013ea590731d4130e2'),
)
FIXTURES = {name: (shape, bytes.fromhex(raw), bytes.fromhex(preimage), expected)
            for name, shape, raw, preimage, expected in VECTORS}
STANDARD_RAW = FIXTURES["standard_2x2"][1]
STANDARD_SHA = FIXTURES["standard_2x2"][3]
IEEE_RAW = FIXTURES["ieee_2x4"][1]
IEEE_SHA = FIXTURES["ieee_2x4"][3]
IEEE_WORDS = (0, 0x8000000000000000, 0x7ff0000000000000, 0xfff0000000000000,
              0x7ff8000000000001, 0x7ff8000000000002,
              0x7ff0000000000042, 0x7ff8000000000042)


def standard():
    return np.frombuffer(STANDARD_RAW, dtype="<f8").reshape(2, 2).copy()


def ieee(endian="<"):
    # Construct words directly, without casting or comparing floating NaNs.
    return np.array(IEEE_WORDS, dtype=endian + "u8").view(endian + "f8").reshape(2, 4)


def snapshot(array):
    return (array.tobytes(order="C"), array.dtype, array.shape, array.strides,
            array.flags.writeable, array.flags.aligned)


def independent_sha(shape, raw):
    """Stdlib-only oracle for perturbations, separate from literal goldens."""
    return hashlib.sha256(HEADER + struct.pack("<QQ", *shape) + raw).hexdigest()


class RunRegistrySeriesHashTests(unittest.TestCase):
    def test_literal_preimages_and_expected_digests(self):
        self.assertEqual(HEADER, b"quantgen.r3.series/1\x00<f8\x00")
        self.assertEqual(len(HEADER), 25)
        for name, (shape, raw, preimage, expected) in FIXTURES.items():
            with self.subTest(fixture=name):
                self.assertEqual(preimage, HEADER + struct.pack("<QQ", *shape) + raw)
                self.assertEqual(len(preimage), 41 + 8 * shape[0] * shape[1])
                self.assertEqual(hashlib.sha256(preimage).hexdigest(), expected)
                array = np.frombuffer(raw, dtype="<f8").reshape(shape)
                result = series_sha256(array)
                self.assertEqual(result, expected)
                self.assertRegex(result, r"\A[0-9a-f]{64}\Z")
                self.assertNotEqual(hashlib.sha256(preimage + b"\n").hexdigest(), result)

    def test_shape_distinguishes_identical_flat_bits(self):
        results = []
        for name in ("standard_2x2", "standard_1x4", "standard_4x1"):
            shape, raw, _, expected = FIXTURES[name]
            self.assertEqual(raw, STANDARD_RAW)
            result = series_sha256(standard().reshape(shape))
            self.assertEqual(result, expected)
            results.append(result)
        self.assertEqual(len(set(results)), 3)

    def test_zero_axes_have_identity_without_storage_validation(self):
        results = []
        for name in ("empty_0x0", "empty_0x3", "empty_3x0"):
            shape, raw, _, expected = FIXTURES[name]
            self.assertEqual(raw, b"")
            for endian in ("<", ">", "="):
                values = np.empty(shape, dtype=endian + "f8")
                self.assertEqual(series_sha256(values), expected)
            results.append(expected)
        self.assertEqual(len(set(results)), 3)

    def test_ieee_literal_words_survive_both_endians(self):
        self.assertEqual(IEEE_RAW, struct.pack("<8Q", *IEEE_WORDS))
        with np.errstate(all="raise"):
            for endian in ("<", ">", "="):
                with self.subTest(endian=endian):
                    self.assertEqual(series_sha256(ieee(endian)), IEEE_SHA)

    def test_signed_zero_and_nan_payloads_have_distinct_literal_hashes(self):
        names = ("positive_zero", "negative_zero", "quiet_nan_1", "quiet_nan_2",
                 "signalling_nan_42", "quiet_nan_42")
        results = []
        for name in names:
            shape, raw, _, expected = FIXTURES[name + "_1x1"]
            word = struct.unpack("<Q", raw)[0]
            for endian in ("<", ">"):
                values = np.array([word], dtype=endian + "u8").view(endian + "f8").reshape(shape)
                with np.errstate(all="raise"):
                    self.assertEqual(series_sha256(values), expected)
            results.append(expected)
        self.assertEqual(len(set(results)), len(names))

    def test_c_fortran_readonly_and_endian_inputs_are_unchanged(self):
        for endian in ("<", ">", "="):
            words = np.frombuffer(STANDARD_RAW, dtype="<u8").astype(endian + "u8").reshape(2, 2)
            for order in ("C", "F"):
                for readonly in (False, True):
                    values = np.array(words, order=order).view(endian + "f8")
                    if readonly:
                        values.setflags(write=False)
                    before = snapshot(values)
                    with self.subTest(endian=endian, order=order, readonly=readonly):
                        self.assertEqual(series_sha256(values), STANDARD_SHA)
                        self.assertEqual(snapshot(values), before)

    def test_negative_and_nonunit_strides_keep_logical_words(self):
        for endian in ("<", ">"):
            words = np.array(IEEE_WORDS, dtype=endian + "u8").reshape(2, 4)
            reverse_backing = words[::-1, ::-1].copy()
            reverse = reverse_backing[::-1, ::-1].view(endian + "f8")
            padded = np.zeros((4, 8), dtype=endian + "u8")
            padded[::2, ::2] = words
            stride = padded[::2, ::2].view(endian + "f8")
            for values in (reverse, stride):
                before = snapshot(values)
                with np.errstate(all="raise"):
                    self.assertEqual(series_sha256(values), IEEE_SHA)
                self.assertEqual(snapshot(values), before)

    def test_zero_stride_broadcast_matches_literal_matrix(self):
        for word, name in ((0x3ff0000000000000, "all_one_2x2"), (0, "all_zero_2x2")):
            for endian in ("<", ">"):
                base = np.array([[word]], dtype=endian + "u8").view(endian + "f8")
                values = np.broadcast_to(base, (2, 2))
                before = snapshot(values)
                self.assertIn(0, values.strides)
                self.assertEqual(series_sha256(values), FIXTURES[name][3])
                self.assertEqual(snapshot(values), before)

    def test_valid_unaligned_buffers_preserve_bytes(self):
        for endian in ("<", ">"):
            word_format = endian + "4Q"
            words = struct.unpack("<4Q", STANDARD_RAW)
            raw = bytearray(b"x" + struct.pack(word_format, *words) + b"y")
            before = bytes(raw)
            values = np.ndarray((2, 2), dtype=endian + "f8", buffer=raw, offset=1)
            self.assertFalse(values.flags.aligned)
            self.assertEqual(series_sha256(values), STANDARD_SHA)
            self.assertEqual(bytes(raw), before)

    def test_bit_and_order_changes_match_independent_preimages(self):
        changed = standard()
        changed.view("<u8")[0, 0] ^= np.uint64(1)
        for values in (changed, standard()[::-1], standard()[:, ::-1], standard().T):
            raw = values.tobytes(order="C")
            self.assertEqual(series_sha256(values), independent_sha(values.shape, raw))
            self.assertNotEqual(series_sha256(values), STANDARD_SHA)

    def test_wrong_rank_and_dtype_are_refused_without_cast(self):
        for shape in ((), (4,), (2, 2, 1), (0,), (1, 0, 2)):
            with self.subTest(shape=shape), self.assertRaises(SeriesHashError):
                series_sha256(np.empty(shape, dtype="f8"))
        for dtype in ("f4", "i8", "u8", "b1", "c16", "O", "U1", "V8",
                      [("value", "f8")], "datetime64[D]"):
            with self.subTest(dtype=str(dtype)), self.assertRaises(SeriesHashError):
                series_sha256(np.zeros((2, 2), dtype=dtype))

    def test_dtype_metadata_is_refused_without_inspecting_values(self):
        class Opaque:
            def __repr__(self):
                raise AssertionError("metadata value inspected")
            def __bool__(self):
                raise AssertionError("metadata value inspected")
        for label, metadata in (("empty", {}), ("opaque", {"unit": Opaque()})):
            values = np.zeros((2, 2), dtype=np.dtype("f8", metadata=metadata))
            self.assertIsNotNone(values.dtype.metadata)
            with self.subTest(metadata=label), self.assertRaises(SeriesHashError):
                series_sha256(values)

    def test_coercion_objects_and_array_subclasses_are_refused_before_hooks(self):
        class Coercible:
            def __array__(self, *args, **kwargs):
                raise AssertionError("coercion must not run")
            def __iter__(self):
                raise AssertionError("iteration must not run")
        class ArraySubclass(np.ndarray):
            @property
            def dtype(self):
                raise AssertionError("subclass property must not run")
            @property
            def ndim(self):
                raise AssertionError("subclass property must not run")
        variants = (None, 1.0, [[1.0]], b"array", Coercible(),
                    standard().view(ArraySubclass), np.ma.array(standard()),
                    memoryview(STANDARD_RAW))
        for values in variants:
            with self.subTest(type=type(values).__name__), self.assertRaises(SeriesHashError):
                series_sha256(values)

    def test_memmap_object_is_refused_in_an_explicit_temporary_directory(self):
        with tempfile.TemporaryDirectory(prefix="qg-serieshash-synthetic-") as directory:
            values = np.memmap(Path(directory) / "synthetic.bin", dtype="f8", mode="w+", shape=(2, 2))
            try:
                with self.assertRaises(SeriesHashError):
                    series_sha256(values)
            finally:
                values._mmap.close()

    def test_no_io_clock_configuration_or_other_product_imports(self):
        values = standard()
        fail = AssertionError("discovery or I/O forbidden")
        with patch("builtins.open", side_effect=fail), \
                patch.object(Path, "open", side_effect=fail), \
                patch.object(socket.socket, "connect", side_effect=fail), \
                patch.object(os, "getenv", side_effect=fail), \
                patch.object(time, "time", side_effect=fail), \
                patch.object(time, "monotonic", side_effect=fail):
            self.assertEqual(series_sha256(values), STANDARD_SHA)
        tree = ast.parse((ROOT / "core" / "quant" / "run_registry_series_hash.py").read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names]
        self.assertEqual(set(imports), {"__future__", "hashlib", "numpy"})
        forbidden = {"now", "utcnow", "today", "time", "monotonic", "getenv", "open", "read_text", "read_bytes"}
        calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute)]
        self.assertFalse(forbidden.intersection(calls))


if __name__ == "__main__":
    unittest.main()
