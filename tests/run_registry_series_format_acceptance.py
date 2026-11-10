"""Synthetic in-memory NPY format acceptance; no actual files or ledgers."""
import ast
import hashlib
from io import BytesIO
import os
from pathlib import Path
import socket
import struct
import time
import unittest
from unittest.mock import patch

import numpy as np

from core.quant import run_registry_series_format as F
from core.quant.run_registry_series_format import SeriesFormatError, decode_series, encode_series
from core.quant.run_registry_series_hash import series_sha256


ROOT = Path(__file__).resolve().parents[1]
# Frozen before implementation by a stdlib-only fixture preparation. No NumPy
# encoder or product framing generated these literal headers, words or hashes.
LITERALS = (
    ('standard_2x2', (2, 2), '0000000000000000000000000000f03f00000000000000400000000000000080', '934e554d5059010076007b276465736372273a20273c6638272c2027666f727472616e5f6f72646572273a2046616c73652c20277368617065273a2028322c2032292c207d202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020200a0000000000000000000000000000f03f00000000000000400000000000000080', 'abf927edfb95165217dee8cd05cbadf02a17de9edd271ae637dacc968041929d', '428709959da4b04f950606cf66e0d52f48ba4296b605b6d28ecae3135bb0809c'),
    ('ieee_2x4', (2, 4), '00000000000000000000000000000080000000000000f07f000000000000f0ff010000000000f87f020000000000f87f420000000000f07f420000000000f87f', '934e554d5059010076007b276465736372273a20273c6638272c2027666f727472616e5f6f72646572273a2046616c73652c20277368617065273a2028322c2034292c207d202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020200a00000000000000000000000000000080000000000000f07f000000000000f0ff010000000000f87f020000000000f87f420000000000f07f420000000000f87f', 'e8f13f5f09a9aee40da8d10aa73e09a123f50dfec96e49505462f3fd91722f8c', '25df772c8ef891aa366ecdf60d09f49b2bc1da21fb1a383b3f106b64b84c529f'),
    ('empty_0x3', (0, 3), '', '934e554d5059010076007b276465736372273a20273c6638272c2027666f727472616e5f6f72646572273a2046616c73652c20277368617065273a2028302c2033292c207d202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020200a', '4aa7aa40d1bbd6bba4570a87b12a7a2be0c4643337cc363349524c7c66ef8fd0', 'c72c4c4469e482ae3475aac28d33bf83cc19f50eb397a0e7c7d07401c0e08b7c'),
    ('alternate_header_2x2', (2, 2), '0000000000000000000000000000f03f00000000000000400000000000000080', '934e554d5059010076007b2027736861706527203a2028322c2032292c2027666f727472616e5f6f7264657227203a2046616c73652c2027646573637227203a20273c663827207d202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020200a0000000000000000000000000000f03f00000000000000400000000000000080', '9f3cb0fcf2eb286a565ff157e8a21407d491e3a518f076c876fb6a56bc543d84', '428709959da4b04f950606cf66e0d52f48ba4296b605b6d28ecae3135bb0809c'),
)
FIXTURES = {name: (shape, bytes.fromhex(raw), bytes.fromhex(payload), payload_hash, content_hash)
            for name, shape, raw, payload, payload_hash, content_hash in LITERALS}
SHAPE, RAW, PAYLOAD, _, CONTENT_SHA = FIXTURES["standard_2x2"]
IEEE_SHAPE, IEEE_RAW, IEEE_PAYLOAD, _, IEEE_SHA = FIXTURES["ieee_2x4"]
MAGIC = b"\x93NUMPY\x01\x00"
INTP_MAX = int(np.iinfo(np.intp).max)
AXIS_MAX = INTP_MAX // 8


def npy(header, raw=RAW, *, alignment=16):
    """Independent stdlib framing for malformed/alternate header probes."""
    text = header.encode("latin1")
    padding = (-(10 + len(text) + 1)) % alignment
    encoded = text + b" " * padding + b"\n"
    return MAGIC + struct.pack("<H", len(encoded)) + encoded + raw


def array_from(raw=RAW, shape=SHAPE, endian="<"):
    words = np.frombuffer(raw, dtype="<u8").astype(endian + "u8")
    return words.view(endian + "f8").reshape(shape)


def snapshot(array):
    return array.tobytes(order="C"), array.dtype, array.shape, array.strides, array.flags.writeable


class RunRegistrySeriesFormatTests(unittest.TestCase):
    def assert_preload_refusal(self, payload, *, digest=CONTENT_SHA, budget=None):
        if budget is None:
            budget = max(1, len(payload))
        with patch.object(F.np, "load", side_effect=AssertionError("array load must not run")) as load:
            with self.assertRaises(SeriesFormatError):
                decode_series(payload, digest, max_bytes=budget)
            load.assert_not_called()

    def test_independent_literal_payloads_decode_raw_bits_and_content_hash(self):
        for name, (shape, raw, payload, payload_hash, content_hash) in FIXTURES.items():
            with self.subTest(fixture=name), np.errstate(all="raise"):
                self.assertEqual(hashlib.sha256(payload).hexdigest(), payload_hash)
                before = bytes(payload)
                result = decode_series(payload, content_hash, max_bytes=len(payload))
                self.assertIs(type(result), np.ndarray)
                self.assertEqual(result.shape, shape)
                self.assertEqual(result.dtype, np.dtype("<f8"))
                self.assertTrue(result.flags.c_contiguous)
                self.assertFalse(result.flags.writeable)
                self.assertEqual(result.tobytes(order="C"), raw)
                self.assertEqual(series_sha256(result), content_hash)
                self.assertEqual(payload, before)

    def test_header_order_padding_and_16_not_64_alignment_are_nonsemantic(self):
        header = "{'shape': (2,2), 'descr': '<f8', 'fortran_order': False}"
        payload = npy(header)
        offset = 10 + int.from_bytes(payload[8:10], "little")
        self.assertEqual(offset % 16, 0)
        self.assertNotEqual(offset % 64, 0)
        self.assertNotEqual(payload, PAYLOAD)
        self.assertEqual(decode_series(payload, CONTENT_SHA, max_bytes=len(payload)).tobytes(), RAW)
        for name in ("standard_2x2", "alternate_header_2x2"):
            self.assertEqual(FIXTURES[name][4], CONTENT_SHA)
        self.assertNotEqual(FIXTURES["standard_2x2"][3], FIXTURES["alternate_header_2x2"][3])

    def test_large_but_bounded_padding_header_is_accepted(self):
        text = b"{'descr':'<f8','fortran_order':False,'shape':(2,2)}"
        header = text + b" " * (9989 - len(text)) + b"\n"
        payload = MAGIC + struct.pack("<H", len(header)) + header + RAW
        self.assertEqual((10 + len(header)) % 16, 0)
        result = decode_series(payload, CONTENT_SHA, max_bytes=len(payload))
        self.assertEqual(result.tobytes(), RAW)

    def test_encode_decode_endian_layout_and_ieee_inputs_without_mutation(self):
        for endian in ("<", ">", "="):
            words = np.frombuffer(IEEE_RAW, dtype="<u8").astype(endian + "u8").reshape(IEEE_SHAPE)
            for order in ("C", "F"):
                values = np.array(words, order=order).view(endian + "f8")
                values.setflags(write=False)
                before = snapshot(values)
                with self.subTest(endian=endian, order=order), np.errstate(all="raise"):
                    encoded = encode_series(values, max_bytes=4096)
                    self.assertEqual(encoded[:8], MAGIC)
                    offset = 10 + int.from_bytes(encoded[8:10], "little")
                    header = ast.literal_eval(encoded[10:offset].decode("latin1"))
                    self.assertEqual(header, {"descr": "<f8", "fortran_order": False, "shape": IEEE_SHAPE})
                    self.assertEqual(encoded[offset:], IEEE_RAW)
                    result = decode_series(encoded, IEEE_SHA, max_bytes=len(encoded))
                    self.assertEqual(result.tobytes(), IEEE_RAW)
                    self.assertEqual(snapshot(values), before)

    def test_strides_broadcast_and_unaligned_inputs_roundtrip(self):
        for endian in ("<", ">"):
            words = np.frombuffer(RAW, dtype="<u8").astype(endian + "u8").reshape(SHAPE)
            reverse_backing = words[::-1, ::-1].copy()
            reversed_view = reverse_backing[::-1, ::-1].view(endian + "f8")
            padding = np.zeros((4, 4), dtype=endian + "u8")
            padding[::2, ::2] = words
            stride_view = padding[::2, ::2].view(endian + "f8")
            buffer = bytearray(b"x" + struct.pack(endian + "4Q", *struct.unpack("<4Q", RAW)))
            unaligned = np.ndarray(SHAPE, dtype=endian + "f8", buffer=buffer, offset=1)
            for values in (reversed_view, stride_view, unaligned):
                before = snapshot(values)
                payload = encode_series(values, max_bytes=4096)
                self.assertEqual(decode_series(payload, CONTENT_SHA, max_bytes=len(payload)).tobytes(), RAW)
                self.assertEqual(snapshot(values), before)
        values = np.broadcast_to(np.array([[1.0]], dtype="<f8"), SHAPE)
        expected = "ee97285acfa8ae3d111e964f599aa22075e8532c31f2fd15f273a7747d77c510"
        payload = encode_series(values, max_bytes=4096)
        self.assertEqual(decode_series(payload, expected, max_bytes=len(payload)).tobytes(), struct.pack("<4d", 1, 1, 1, 1))

    def test_zero_axes_roundtrip_with_distinct_content_identity(self):
        cases = [((0, 0), "ac93f8f475323865c062dec991879b0089fbb770b75bdd1210fbb68dfa5c6865"),
                 ((0, 3), "c72c4c4469e482ae3475aac28d33bf83cc19f50eb397a0e7c7d07401c0e08b7c"),
                 ((3, 0), "99d2355bdd2391e418f26d4d39bfa9d65999c3aae2ea7d07d56eed5a165290ed")]
        for shape, expected in cases:
            for endian in ("<", ">"):
                encoded = encode_series(np.empty(shape, dtype=endian + "f8"), max_bytes=512)
                result = decode_series(encoded, expected, max_bytes=len(encoded))
                self.assertEqual(result.shape, shape)
                self.assertEqual(result.nbytes, 0)

    def test_exact_serialized_budget_and_one_byte_under(self):
        values = array_from()
        encoded = encode_series(values, max_bytes=4096)
        self.assertEqual(encode_series(values, max_bytes=len(encoded)), encoded)
        self.assertEqual(decode_series(encoded, CONTENT_SHA, max_bytes=len(encoded)).tobytes(), RAW)
        with patch.object(F.np, "save", side_effect=AssertionError("precopy budget must refuse")) as save:
            with self.assertRaises(SeriesFormatError):
                encode_series(values, max_bytes=len(encoded) - 1)
            save.assert_not_called()
        self.assert_preload_refusal(encoded, budget=len(encoded) - 1)

    def test_oversized_virtual_array_refuses_before_copy_save_or_hash(self):
        values = np.broadcast_to(np.array([[1.0]]), (10000, 10000))
        with patch.object(F.np, "dtype", side_effect=AssertionError("copy path must not run")), \
                patch.object(F.np, "save", side_effect=AssertionError("save must not run")), \
                patch.object(F, "series_sha256", side_effect=AssertionError("hash must not run")):
            with self.assertRaises(SeriesFormatError):
                encode_series(values, max_bytes=256)

    def test_bounded_output_refuses_writer_overrun_before_growth(self):
        observations = []
        def oversized(output, array, *, allow_pickle):
            self.assertIs(allow_pickle, False)
            view = memoryview(np.zeros((2, 81), dtype="u1"))
            self.assertEqual(len(view), 2)
            self.assertEqual(view.nbytes, 162)
            with self.assertRaises(SeriesFormatError):
                output.write(view)
            self.assertEqual(output.tell(), 0)
            output.write(b"x" * 160)
            with self.assertRaises(SeriesFormatError):
                output.write(b"y")
            observations.append(output.tell())
            raise SeriesFormatError("writer refused after bounded check")
        with patch.object(F.np, "save", side_effect=oversized), self.assertRaises(SeriesFormatError):
            encode_series(array_from(), max_bytes=160)
        self.assertEqual(observations, [160])

    def test_numpy_calls_keep_pickle_disabled_and_decode_bound(self):
        save, load = np.save, np.load
        with patch.object(F.np, "save", wraps=save) as save_spy:
            encoded = encode_series(array_from(), max_bytes=4096)
            self.assertIs(save_spy.call_args.kwargs["allow_pickle"], False)
        with patch.object(F.np, "load", wraps=load) as load_spy:
            decode_series(encoded, CONTENT_SHA, max_bytes=len(encoded))
            self.assertIs(load_spy.call_args.kwargs["allow_pickle"], False)
            self.assertEqual(load_spy.call_args.kwargs["max_header_size"], 10000)

    def test_budget_payload_digest_types_are_exact_and_bounded(self):
        class IntSubclass(int):
            pass
        class BytesSubclass(bytes):
            pass
        class StrSubclass(str):
            pass
        for budget in (None, False, True, 0, -1, 1.0, np.int64(160), IntSubclass(160), INTP_MAX + 1):
            with self.subTest(budget_type=type(budget).__name__):
                with self.assertRaises(SeriesFormatError):
                    encode_series(array_from(), max_bytes=budget)
                with self.assertRaises(SeriesFormatError):
                    decode_series(PAYLOAD, CONTENT_SHA, max_bytes=budget)
        for payload in (bytearray(PAYLOAD), memoryview(PAYLOAD), BytesSubclass(PAYLOAD), "NPY", BytesIO(PAYLOAD)):
            with self.assertRaises(SeriesFormatError):
                decode_series(payload, CONTENT_SHA, max_bytes=4096)
        for digest in (None, b"0" * 64, StrSubclass(CONTENT_SHA), CONTENT_SHA.upper(),
                       "0" * 63, "g" * 64, CONTENT_SHA + "\n", " " + CONTENT_SHA):
            self.assert_preload_refusal(PAYLOAD, digest=digest)

    def test_encoder_refuses_unsupported_array_types_dtypes_and_ranks(self):
        class Coercible:
            def __array__(self, *args, **kwargs):
                raise AssertionError("coercion forbidden")
        class ArraySubclass(np.ndarray):
            @property
            def ndim(self):
                raise AssertionError("subclass access forbidden")
        variants = (None, [[1.0]], Coercible(), array_from().view(ArraySubclass),
                    np.ma.array(array_from()), np.zeros((4,)), np.zeros((1, 2, 2)),
                    np.zeros((2, 2), dtype=np.dtype("f8", metadata={})))
        for value in variants:
            with self.assertRaises(SeriesFormatError):
                encode_series(value, max_bytes=4096)
        for dtype in ("f4", "i8", "u8", "O", "c16", [("value", "f8")]):
            with self.subTest(dtype=str(dtype)), self.assertRaises(SeriesFormatError):
                encode_series(np.zeros(SHAPE, dtype=dtype), max_bytes=4096)

    def test_magic_version_header_length_and_alignment_refuse_before_load(self):
        variants = [b"", b"\x93NUMPY\x01\x00", b"\x80\x04N.", b"PK\x03\x04" + PAYLOAD,
                    PAYLOAD[:6] + b"\x02\x00" + PAYLOAD[8:],
                    PAYLOAD[:6] + b"\x03\x00" + PAYLOAD[8:],
                    MAGIC + b"\x76\x00" + b"short", MAGIC + b"\x00\x00" + RAW,
                    PAYLOAD[:127] + b" " + PAYLOAD[128:]]
        header = b"{'descr':'<f8','fortran_order':False,'shape':(2,2)}\n"
        self.assertNotEqual((10 + len(header)) % 16, 0)
        variants.append(MAGIC + struct.pack("<H", len(header)) + header + RAW)
        for payload in variants:
            with self.subTest(length=len(payload)):
                self.assert_preload_refusal(payload)
        oversized_header = MAGIC + struct.pack("<H", 10006) + b" " * 10005 + b"\n"
        with patch.object(F.ast, "parse", side_effect=AssertionError("oversized header must not parse")):
            self.assert_preload_refusal(oversized_header)

    def test_header_duplicate_missing_extra_and_nonliteral_keys_refuse_before_load(self):
        headers = ["{'descr':'<f8','fortran_order':False,'shape':(2,2),'shape':(2,2)}",
                   "{'descr':'<f8','descr':'<f8','shape':(2,2)}",
                   "{'descr':'<f8','shape':(2,2)}",
                   "{'descr':'<f8','fortran_order':False,'shape':(2,2),'metadata':{}}",
                   "{**{'descr':'<f8'},'fortran_order':False,'shape':(2,2)}",
                   "{b'descr':'<f8','fortran_order':False,'shape':(2,2)}",
                   "[('descr','<f8'),('fortran_order',False),('shape',(2,2))]",
                   "{'descr':'<f8','fortran_order':False,'shape':tuple([2,2])}",
                   "{'descr':'<f8','fortran_order':False,'shape':(1+1,2)}"]
        for header in headers:
            with self.subTest(header=header):
                self.assert_preload_refusal(npy(header))

    def test_header_dtype_order_and_shape_types_refuse_before_load(self):
        descriptors = ["'>f8'", "'=f8'", "'float64'", "'|O'", "'<f4'", "b'<f8'",
                       "[('value','<f8')]", "{'descr':'<f8','metadata':{}}"]
        for descriptor in descriptors:
            self.assert_preload_refusal(npy("{'descr':" + descriptor + ",'fortran_order':False,'shape':(2,2)}"))
        for order in ("True", "0", "None", "'False'"):
            self.assert_preload_refusal(npy("{'descr':'<f8','fortran_order':" + order + ",'shape':(2,2)}"))
        for shape in ("[2,2]", "(True,2)", "(-1,2)", "(2.0,2)", "(2,)", "(2,2,1)", "2"):
            self.assert_preload_refusal(npy("{'descr':'<f8','fortran_order':False,'shape':" + shape + "}"))

    def test_huge_axes_and_python_integer_products_refuse_before_load(self):
        for shape in ((0, AXIS_MAX + 1), (AXIS_MAX + 1, 0), (2**64, 0), (2**32, 2**32)):
            payload = npy("{'descr':'<f8','fortran_order':False,'shape':" + repr(shape) + "}", b"")
            self.assert_preload_refusal(payload)
        # NumPy itself refuses an ndarray above this representable byte span.
        # Check the accepted empty boundary separately; no data buffer grows.
        virtual = np.lib.stride_tricks.as_strided(np.empty((0,)), shape=(0, AXIS_MAX), strides=(0, 0))
        encoded = encode_series(virtual, max_bytes=512)
        preimage = b"quantgen.r3.series/1\x00<f8\x00" + struct.pack("<QQ", 0, AXIS_MAX)
        expected = hashlib.sha256(preimage).hexdigest()
        result = decode_series(encoded, expected, max_bytes=len(encoded))
        self.assertEqual(result.shape, (0, AXIS_MAX))
        self.assertEqual(result.nbytes, 0)

    def test_bounded_unary_header_never_loads_and_recursion_is_typed(self):
        header = "{'descr':'<f8','fortran_order':False,'shape':(" + "+" * 3500 + "2,2)}"
        payload = npy(header)
        self.assertLess(int.from_bytes(payload[8:10], "little"), 10000)
        # Parser resource thresholds vary across supported interpreters. Either
        # documented failure must occur before NumPy can load an array.
        with patch.object(F.np, "load", side_effect=AssertionError("array load forbidden")) as load:
            with self.assertRaises((SeriesFormatError, MemoryError)):
                decode_series(payload, CONTENT_SHA, max_bytes=len(payload))
            load.assert_not_called()
        # Parser recursion behavior varies by interpreter. Inject its documented
        # boundary separately; the literal above is not claimed to reproduce it.
        with patch.object(F.ast, "parse", side_effect=RecursionError("synthetic parser boundary")):
            self.assert_preload_refusal(PAYLOAD)

    def test_truncation_trailing_and_concatenation_refuse_before_load(self):
        for payload in (PAYLOAD[:-1], PAYLOAD + b"\0", PAYLOAD + PAYLOAD, PAYLOAD[:128]):
            self.assert_preload_refusal(payload)

    def test_wrong_content_hash_and_corrupted_raw_data_refuse(self):
        for payload, digest in ((PAYLOAD, "0" * 64), (PAYLOAD[:-1] + bytes([PAYLOAD[-1] ^ 1]), CONTENT_SHA)):
            with self.assertRaisesRegex(SeriesFormatError, "SHA-256 mismatch"):
                decode_series(payload, digest, max_bytes=len(payload))

    def test_readonly_is_convenience_and_each_decode_is_independent(self):
        result = decode_series(PAYLOAD, CONTENT_SHA, max_bytes=len(PAYLOAD))
        with self.assertRaises(ValueError):
            result[0, 0] = 10
        result.setflags(write=True)
        result[0, 0] = 10
        second = decode_series(PAYLOAD, CONTENT_SHA, max_bytes=len(PAYLOAD))
        self.assertEqual(second.tobytes(), RAW)
        self.assertFalse(second.flags.writeable)

    def test_resource_errors_propagate_and_numpy_errors_are_typed_refusals(self):
        with patch.object(F.ast, "parse", side_effect=MemoryError("synthetic parser resource failure")), self.assertRaises(MemoryError):
            decode_series(PAYLOAD, CONTENT_SHA, max_bytes=len(PAYLOAD))
        with patch.object(F.np, "save", side_effect=MemoryError("synthetic resource failure")), self.assertRaises(MemoryError):
            encode_series(array_from(), max_bytes=4096)
        with patch.object(F.np, "load", side_effect=MemoryError("synthetic resource failure")), self.assertRaises(MemoryError):
            decode_series(PAYLOAD, CONTENT_SHA, max_bytes=len(PAYLOAD))
        with patch.object(F.np, "load", side_effect=ValueError("synthetic format failure")), self.assertRaises(SeriesFormatError):
            decode_series(PAYLOAD, CONTENT_SHA, max_bytes=len(PAYLOAD))

    def test_functions_use_memory_only_without_discovery_or_global_audit_hooks(self):
        values = array_from()
        fail = AssertionError("I/O/discovery forbidden")
        with patch("builtins.open", side_effect=fail), \
                patch.object(Path, "open", side_effect=fail), \
                patch.object(socket.socket, "connect", side_effect=fail), \
                patch.object(os, "getenv", side_effect=fail), \
                patch.object(time, "time", side_effect=fail):
            encoded = encode_series(values, max_bytes=4096)
            self.assertEqual(decode_series(encoded, CONTENT_SHA, max_bytes=len(encoded)).tobytes(), RAW)
        tree = ast.parse((ROOT / "core/quant/run_registry_series_format.py").read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertEqual(set(imports), {"__future__", "ast", "io", "re", "numpy", "core.quant.run_registry_series_hash"})
        calls = [node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertNotIn("eval", calls)


if __name__ == "__main__":
    unittest.main()
