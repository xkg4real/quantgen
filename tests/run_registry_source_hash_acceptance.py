"""Synthetic tests of only the supplied-content R3 section-3.3 digests."""
from contextlib import ExitStack
import hashlib
import inspect
import io
import os
from pathlib import Path
import socket
import subprocess
import time
import unittest
from unittest.mock import patch

from core.quant.run_registry_source_hash import (
    SourceHashError, source_bytes_hashes, source_text_hashes,
)


# These literal preimages/hashes were prepared separately with stdlib hashlib,
# without importing the product helper or deriving expected LF via replace().
UNICODE_TEXT = "\ufeffdef 계산():\r\n\treturn 'é'\r\n"
UNICODE_RAW = bytes.fromhex("efbbbf64656620eab384ec82b028293a0d0a0972657475726e2027c3a9270d0a")
UNICODE_LF = bytes.fromhex("efbbbf64656620eab384ec82b028293a0a0972657475726e2027c3a9270a")
UNICODE_HASHES = {
    "raw": "bd81c4ec2ceb1d3b6c5ccfe4d2d0c23ac7e234f9b765bdd903ea56b27660098b",
    "lf": "c02abdd9a2cffa83c0a9a5504253b561c9aa7f6fd0337cf6e0a3d3eeab61bbfa",
}
OPAQUE_RAW = bytes.fromhex("ff00410d0a420d430a80")
OPAQUE_LF = bytes.fromhex("ff00410a420d430a80")
OPAQUE_HASHES = {
    "raw": "d538d411f26a64f41b755cc1cfa941cb8ce4eb8eaccd2f2ccb924479d57b42a6",
    "lf": "a802f229f4c0e92945f57a5d826beb38ec1c00d7c7de430817ed69522677d6df",
}
EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class RunRegistrySourceHashTests(unittest.TestCase):
    def test_literal_unicode_bom_and_utf8_preimages(self):
        self.assertEqual(UNICODE_TEXT.encode("utf-8"), UNICODE_RAW)
        self.assertEqual(hashlib.sha256(UNICODE_RAW).hexdigest(), UNICODE_HASHES["raw"])
        self.assertEqual(hashlib.sha256(UNICODE_LF).hexdigest(), UNICODE_HASHES["lf"])
        self.assertEqual(source_text_hashes(UNICODE_TEXT), UNICODE_HASHES)
        self.assertEqual(source_bytes_hashes(UNICODE_RAW), UNICODE_HASHES)
        self.assertEqual(source_bytes_hashes(UNICODE_LF),
                         {"lf": UNICODE_HASHES["lf"], "raw": UNICODE_HASHES["lf"]})

    def test_literal_opaque_bytes_include_invalid_utf8_and_nul(self):
        with self.assertRaises(UnicodeDecodeError):
            OPAQUE_RAW.decode("utf-8", errors="strict")
        self.assertEqual(hashlib.sha256(OPAQUE_RAW).hexdigest(), OPAQUE_HASHES["raw"])
        self.assertEqual(hashlib.sha256(OPAQUE_LF).hexdigest(), OPAQUE_HASHES["lf"])
        self.assertEqual(source_bytes_hashes(OPAQUE_RAW), OPAQUE_HASHES)
        self.assertEqual(source_text_hashes("a\0b"), source_bytes_hashes(b"a\0b"))

    def test_overlapping_crcrlf_is_replaced_once_not_until_stable(self):
        expected = {
            "raw": "f08153d16a9490d994a25d5a341ff8acfc405deddabd0d2134ef9af9d46acd54",
            "lf": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
        }
        self.assertEqual(hashlib.sha256(b"\r\r\n").hexdigest(), expected["raw"])
        self.assertEqual(hashlib.sha256(b"\r\n").hexdigest(), expected["lf"])
        self.assertEqual(source_bytes_hashes(b"\r\r\n"), expected)
        self.assertEqual(source_text_hashes("\r\r\n"), expected)
        self.assertNotEqual(expected["lf"], hashlib.sha256(b"\n").hexdigest())

    def test_mixed_newlines_preserve_lone_cr_and_final_newline(self):
        raw = b"A\r\nB\rC\nD\r\r\nE\r"
        explicit_lf = b"A\nB\rC\nD\r\nE\r"
        actual = source_bytes_hashes(raw)
        self.assertEqual(actual, {"raw": hashlib.sha256(raw).hexdigest(),
                                  "lf": hashlib.sha256(explicit_lf).hexdigest()})
        self.assertEqual(source_text_hashes(raw.decode("ascii")), actual)
        for variant in (b"A", b"A\n", b"A\r", b"A ", b"A\t", b"A\v", b"A\f"):
            with self.subTest(variant=variant):
                expected = hashlib.sha256(variant).hexdigest()
                self.assertEqual(source_bytes_hashes(variant), {"lf": expected, "raw": expected})
        self.assertEqual(len({source_bytes_hashes(v)["lf"] for v in
                              (b"A", b"A\n", b"A\r", b"A ", b"A\t", b"A\v", b"A\f")}), 7)

    def test_bom_indentation_unicode_and_whitespace_are_not_normalized(self):
        variants = ("é", "e\u0301", "\ufeffé", " é", "\té", "é ", "é\n", "é\u2028")
        normalized = []
        for text in variants:
            with self.subTest(text=text):
                expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
                self.assertEqual(source_text_hashes(text), {"lf": expected, "raw": expected})
                normalized.append(expected)
        self.assertEqual(len(set(normalized)), len(variants))

    def test_empty_inputs_and_fresh_independent_dictionary(self):
        first = source_text_hashes("")
        second = source_bytes_hashes(b"")
        self.assertEqual(first, {"lf": EMPTY_HASH, "raw": EMPTY_HASH})
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first["lf"] = "caller mutation"
        first["extra"] = "caller metadata"
        self.assertEqual(second, {"lf": EMPTY_HASH, "raw": EMPTY_HASH})
        self.assertEqual(source_text_hashes(""), second)
        for value in second.values():
            self.assertRegex(value, r"\A[0-9a-f]{64}\Z")

    def test_plain_type_boundaries_refuse_without_coercion(self):
        class TextSubclass(str):
            pass

        class BytesSubclass(bytes):
            pass

        class NoCoercion:
            def __str__(self):
                raise AssertionError("str coercion must not run")

            def __bytes__(self):
                raise AssertionError("bytes coercion must not run")

            def read(self):
                raise AssertionError("file-like read must not run")

        self.assertTrue(issubclass(SourceHashError, ValueError))
        common = (None, 0, True, [], {}, NoCoercion(), Path("synthetic.py"))
        with io.StringIO("synthetic") as text_stream, io.BytesIO(b"synthetic") as byte_stream:
            for value in common + (b"text", TextSubclass("text"), text_stream, byte_stream):
                with self.subTest(api="text", input_type=type(value).__name__):
                    with self.assertRaises(SourceHashError):
                        source_text_hashes(value)
            for value in common + ("text", BytesSubclass(b"text"), bytearray(b"text"),
                                   memoryview(b"text"), text_stream, byte_stream):
                with self.subTest(api="bytes", input_type=type(value).__name__):
                    with self.assertRaises(SourceHashError):
                        source_bytes_hashes(value)
        for text in ("\ud800", "a\udfffz", "\ud83d\ude00"):
            with self.subTest(surrogate=repr(text)):
                with self.assertRaises(SourceHashError):
                    source_text_hashes(text)
        self.assertEqual(source_text_hashes("😀"), source_bytes_hashes(b"\xf0\x9f\x98\x80"))

    def test_supplied_inputs_are_unchanged_and_no_io_or_discovery_is_used(self):
        text, raw = UNICODE_TEXT, OPAQUE_RAW
        before = (text, raw)
        targets = ("builtins.open", "io.open", "pathlib.Path.read_bytes", "pathlib.Path.read_text",
                   "socket.socket", "subprocess.run", "subprocess.Popen", "os.getenv",
                   "os.listdir", "inspect.getsource", "inspect.getsourcefile", "time.time")
        with ExitStack() as stack:
            mocks = [stack.enter_context(patch(target, side_effect=AssertionError(target)))
                     for target in targets]
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(source_text_hashes(text), UNICODE_HASHES)
                self.assertEqual(source_bytes_hashes(raw), OPAQUE_HASHES)
            for mock in mocks:
                mock.assert_not_called()
        self.assertEqual((text, raw), before)


if __name__ == "__main__":
    unittest.main()
