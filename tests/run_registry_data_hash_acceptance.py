"""Synthetic acceptance of only the R3 section-5.4 data MD5 recipe."""
import ast
import copy
import hashlib
from pathlib import Path
import socket
import struct
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from core.quant.run_registry_data_hash import DataHashError, data_md5


ROOT = Path(__file__).resolve().parents[1]
DATES = ["2000-01-03", "2000-01-04"]
SYMBOLS = ["SYN:A", "한글"]
# Literal preimages/digests prepared independently using stdlib struct/hashlib,
# without importing NumPy or this helper. No file header, shape or trailing LF.
STANDARD_RAW = bytes.fromhex("000000000000f03f0000000000000080000000000000044000000000000008c0")
STANDARD_PREIMAGE = bytes.fromhex(
    "323030302d30312d30330a323030302d30312d30340053594e3a410aed959ceab88000"
    "000000000000f03f0000000000000080000000000000044000000000000008c0")
STANDARD_MD5 = "cda04f03c4f0dfcbb95ab4ad29ba45e0"
IEEE_WORDS = (0, 0x8000000000000000, 0x7ff0000000000000,
              0xfff0000000000000, 0x7ff8000000000001, 0x7ff0000000000042)
IEEE_RAW = bytes.fromhex(
    "00000000000000000000000000000080000000000000f07f"
    "000000000000f0ff010000000000f87f420000000000f07f")
IEEE_PREIMAGE = bytes.fromhex(
    "323032342d30322d32380a323032342d30322d323900410a420a4300"
    "00000000000000000000000000000080000000000000f07f"
    "000000000000f0ff010000000000f87f420000000000f07f")
IEEE_MD5 = "4bba95653084fdb645ab603e29fa1a2e"


def standard():
    return np.frombuffer(STANDARD_RAW, dtype="<f8").reshape(2, 2).copy()


def ieee(endian="<"):
    # Construct uint64 words directly; never cast floating NaNs or quiet sNaNs.
    return np.array(IEEE_WORDS, dtype=endian + "u8").view(endian + "f8").reshape(2, 3)


def reference_md5(dates, symbols, raw):
    """Independent preimage composition for mutation cases only."""
    return hashlib.md5(("\n".join(dates) + "\0" + "\n".join(symbols) + "\0").encode("utf-8")
                       + raw, usedforsecurity=False).hexdigest()


class RunRegistryDataHashTests(unittest.TestCase):
    def test_literal_utf8_preimage_and_digest(self):
        self.assertEqual(STANDARD_RAW, struct.pack("<4d", 1.0, -0.0, 2.5, -3.0))
        self.assertEqual(STANDARD_PREIMAGE,
                         "2000-01-03\n2000-01-04\0SYN:A\n한글\0".encode("utf-8") + STANDARD_RAW)
        self.assertEqual(hashlib.md5(STANDARD_PREIMAGE, usedforsecurity=False).hexdigest(), STANDARD_MD5)
        self.assertEqual(data_md5(DATES, SYMBOLS, standard()), STANDARD_MD5)
        self.assertNotEqual(hashlib.md5(STANDARD_PREIMAGE + b"\n", usedforsecurity=False).hexdigest(), STANDARD_MD5)

    def test_ieee_literal_bits_including_signalling_nan(self):
        self.assertEqual(IEEE_RAW, struct.pack("<6Q", *IEEE_WORDS))
        self.assertEqual(IEEE_PREIMAGE, b"2024-02-28\n2024-02-29\0A\nB\nC\0" + IEEE_RAW)
        self.assertEqual(hashlib.md5(IEEE_PREIMAGE, usedforsecurity=False).hexdigest(), IEEE_MD5)
        with np.errstate(all="raise"):
            for endian in ("<", ">"):
                with self.subTest(endian=endian):
                    self.assertEqual(data_md5(["2024-02-28", "2024-02-29"], ["A", "B", "C"], ieee(endian)), IEEE_MD5)

    def test_c_fortran_and_readonly_endian_inputs(self):
        for endian in ("<", ">"):
            words = np.frombuffer(STANDARD_RAW, dtype="<u8").astype(endian + "u8").reshape(2, 2)
            for order in ("C", "F"):
                values = np.array(words, order=order).view(endian + "f8")
                values.setflags(write=False)
                before = (values.tobytes(), values.dtype.str, values.strides, values.flags.writeable)
                with self.subTest(endian=endian, order=order):
                    self.assertEqual(data_md5(tuple(DATES), tuple(SYMBOLS), values), STANDARD_MD5)
                    self.assertEqual((values.tobytes(), values.dtype.str, values.strides, values.flags.writeable), before)

    def test_negative_and_nonunit_strides_preserve_logical_raw_bits(self):
        for endian in ("<", ">"):
            words = np.array(IEEE_WORDS, dtype=endian + "u8").reshape(2, 3)
            reverse_backing = words[::-1, ::-1].copy()
            reverse_view = reverse_backing[::-1, ::-1].view(endian + "f8")
            padded = np.zeros((4, 6), dtype=endian + "u8")
            padded[::2, ::2] = words
            strided = padded[::2, ::2].view(endian + "f8")
            for values in (reverse_view, strided):
                before = values.tobytes(order="C")
                with np.errstate(all="raise"):
                    self.assertEqual(data_md5(["2024-02-28", "2024-02-29"], ["A", "B", "C"], values), IEEE_MD5)
                self.assertEqual(values.tobytes(order="C"), before)

    def test_zero_stride_view_has_same_bytes_as_contiguous_copy(self):
        values = np.broadcast_to(standard()[:1, :1], (2, 2))
        self.assertIn(0, values.strides)
        self.assertEqual(data_md5(DATES, SYMBOLS, values),
                         reference_md5(DATES, SYMBOLS, struct.pack("<4d", 1.0, 1.0, 1.0, 1.0)))
        self.assertEqual(data_md5(DATES, SYMBOLS, values), data_md5(DATES, SYMBOLS, values.copy()))

    def test_signed_zero_and_distinct_nan_payloads_remain_distinct(self):
        digests = []
        for word in (0, 0x8000000000000000, 0x7ff8000000000001, 0x7ff8000000000002,
                     0x7ff0000000000042, 0x7ff8000000000042):
            value = np.array([word], dtype="<u8").view("<f8").reshape(1, 1)
            with np.errstate(all="raise"):
                actual = data_md5(["2024-02-29"], ["A"], value)
            self.assertEqual(actual, reference_md5(["2024-02-29"], ["A"], struct.pack("<Q", word)))
            digests.append(actual)
        self.assertEqual(len(set(digests)), len(digests))

    def test_literal_date_and_symbol_order_duplicates_case_space_unicode(self):
        variants = [(DATES[::-1], SYMBOLS), (DATES, SYMBOLS[::-1]),
                    ([DATES[0], DATES[0]], SYMBOLS), (DATES, [SYMBOLS[0], SYMBOLS[0]]),
                    (DATES, ["syn:a", "한글"]), (DATES, [" SYN:A ", "한글"]),
                    (DATES, ["SYN:A\r", "한글"]), (DATES, ["SYN:A", "한글"])]
        for dates, symbols in variants:
            with self.subTest(dates=dates, symbols=symbols):
                actual = data_md5(dates, symbols, standard())
                self.assertEqual(actual, reference_md5(dates, symbols, STANDARD_RAW))
                self.assertNotEqual(actual, STANDARD_MD5)
        self.assertEqual(data_md5(["0001-01-01", "9999-12-31"], SYMBOLS, standard()),
                         reference_md5(["0001-01-01", "9999-12-31"], SYMBOLS, STANDARD_RAW))

    def test_one_matrix_bit_change_changes_the_fixture_hash(self):
        values = standard()
        values.view("<u8")[0, 0] ^= np.uint64(1)
        self.assertNotEqual(data_md5(DATES, SYMBOLS, values), STANDARD_MD5)

    def test_plain_container_and_string_types_are_required(self):
        class ListSubclass(list):
            pass
        class StringSubclass(str):
            pass
        for dates, symbols in [(iter(DATES), SYMBOLS), (ListSubclass(DATES), SYMBOLS),
                               (np.array(DATES), SYMBOLS), (DATES, "A"),
                               ([StringSubclass(DATES[0]), DATES[1]], SYMBOLS),
                               (DATES, [StringSubclass("A"), "B"]),
                               (DATES, [1, "B"]), (DATES, [b"A", "B"])]:
            with self.subTest(dates_type=type(dates).__name__, symbols_type=type(symbols).__name__), self.assertRaises(DataHashError):
                data_md5(dates, symbols, standard())

    def test_invalid_ascii_calendar_dates_are_refused_without_normalization(self):
        for date_label in ("2023-02-29", "2024-02-30", "0000-01-01", "2024-13-01",
                           "20240229", "2024-2-29", "２０２４-02-29", "2024-02-29Z",
                           " 2024-02-29", "2024-02-29 ", "2024-02-29\r"):
            with self.subTest(date=date_label), self.assertRaises(DataHashError):
                data_md5([date_label, DATES[1]], SYMBOLS, standard())

    def test_empty_axes_tokens_delimiters_and_surrogates_are_refused(self):
        for dates, symbols, values in [([], [], np.empty((0, 0))),
                                      ([], ["A"], np.empty((0, 1))),
                                      ([DATES[0]], [], np.empty((1, 0)))]:
            with self.subTest(shape=values.shape), self.assertRaises(DataHashError):
                data_md5(dates, symbols, values)
        for token in ("", "A\nB", "A\0B", "\ud800"):
            with self.subTest(token=repr(token)), self.assertRaises(DataHashError):
                data_md5(DATES, [token, "B"], standard())
        for token in ("", "2000-01-03\n2000-01-04", "2000-01-03\0"):
            with self.assertRaises(DataHashError):
                data_md5([token, DATES[1]], SYMBOLS, standard())

    def test_wrong_shape_rank_and_dtypes_are_refused_instead_of_cast(self):
        for shape in ((4,), (1, 4), (2, 2, 1), (1, 2), (2, 3)):
            with self.subTest(shape=shape), self.assertRaises(DataHashError):
                data_md5(DATES, SYMBOLS, np.zeros(shape, dtype="f8"))
        for dtype in ("f4", "i8", "u8", "b1", "c16", "O", "U1", "V8",
                      [("price", "f8")], "datetime64[D]"):
            with self.subTest(dtype=str(dtype)), self.assertRaises(DataHashError):
                data_md5(DATES, SYMBOLS, np.zeros((2, 2), dtype=dtype))
        with self.assertRaises(DataHashError):
            data_md5(DATES, SYMBOLS, [[1.0, 2.0], [3.0, 4.0]])

    def test_array_subclasses_masked_arrays_and_memmaps_are_refused(self):
        class ArraySubclass(np.ndarray):
            pass
        for values in (standard().view(ArraySubclass), np.ma.array(standard())):
            with self.subTest(type=type(values).__name__), self.assertRaises(DataHashError):
                data_md5(DATES, SYMBOLS, values)
        with tempfile.TemporaryDirectory(prefix="qg-datahash-memmap-") as directory:
            values = np.memmap(Path(directory) / "synthetic.bin", dtype="f8", mode="w+", shape=(2, 2))
            try:
                with self.assertRaises(DataHashError):
                    data_md5(DATES, SYMBOLS, values)
            finally:
                values._mmap.close()

    def test_inputs_and_array_flags_are_unchanged(self):
        values = ieee(">")
        values.setflags(write=False)
        before = (values.tobytes(), values.dtype.str, values.shape, values.strides, values.flags.writeable)
        source_dates, source_symbols = ["2024-02-28", "2024-02-29"], ["A", "B", "C"]
        original = copy.deepcopy((source_dates, source_symbols))
        self.assertEqual(data_md5(source_dates, source_symbols, values), IEEE_MD5)
        self.assertEqual((source_dates, source_symbols), original)
        self.assertEqual((values.tobytes(), values.dtype.str, values.shape, values.strides, values.flags.writeable), before)

    def test_no_io_clock_or_other_product_imports(self):
        values = standard()
        with patch("builtins.open", side_effect=AssertionError("file I/O forbidden")), \
                patch.object(Path, "open", side_effect=AssertionError("path I/O forbidden")), \
                patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
            self.assertEqual(data_md5(DATES, SYMBOLS, values), STANDARD_MD5)
        tree = ast.parse((ROOT / "core" / "quant" / "run_registry_data_hash.py").read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertEqual(set(imports), {"__future__", "datetime", "hashlib", "re", "numpy"})
        forbidden = {"now", "utcnow", "today", "time", "getenv", "open", "read_text", "read_bytes"}
        calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute)]
        self.assertFalse(forbidden.intersection(calls))


if __name__ == "__main__":
    unittest.main()
