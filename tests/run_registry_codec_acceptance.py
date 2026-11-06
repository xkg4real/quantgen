"""Synthetic acceptance for R3 codec/IDs only, not the full registry/store suite."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import sys
import unittest

from core.quant import run_registry_codec as C


RUN = "LAB-20261106T080910Z-FAM-0123abcd"
STAMP = "2026-11-06T08:09:10.123456Z"
# Independent literal bytes, not the codec's serializer or exported constants.
BODY = (b'{"event":"STARTED","recorded_utc":"2026-11-06T08:09:10.123456Z",'
        b'"run_id":"LAB-20261106T080910Z-FAM-0123abcd","schema":"qg-run-registry/1",'
        b'"writer":"ui/strategy_lab_page.py"}')
ROW = hashlib.md5(BODY, usedforsecurity=False).hexdigest().encode("ascii")
GOLDEN = (b'{"event":"STARTED","prev_row_md5":null,'
          b'"recorded_utc":"2026-11-06T08:09:10.123456Z","row_md5":"' + ROW +
          b'","run_id":"LAB-20261106T080910Z-FAM-0123abcd",'
          b'"schema":"qg-run-registry/1","writer":"ui/strategy_lab_page.py"}\n')


def event(kind="STARTED", **extra):
    result = {"schema": "qg-run-registry/1", "event": kind, "run_id": RUN,
              "recorded_utc": STAMP, "writer": "ui/strategy_lab_page.py"}
    result.update(extra)
    return result


def wire(obj):
    """Independent test writer to construct intentionally invalid or valid input."""
    body = {k: v for k, v in obj.items() if k not in ("row_md5", "prev_row_md5")}
    encode = lambda v: json.dumps(v, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False, allow_nan=False).encode("utf-8")
    full = dict(obj, row_md5=hashlib.md5(encode(body), usedforsecurity=False).hexdigest())
    full.setdefault("prev_row_md5", None)
    return encode(full) + b"\n"


class RunRegistryCodecTests(unittest.TestCase):
    def test_literal_golden_bytes_and_independent_row_hash(self):
        source = json.loads(BODY)
        self.assertEqual(C.encode_event_line(source), GOLDEN)
        self.assertEqual(C.decode_event_line(GOLDEN)["row_md5"], ROW.decode("ascii"))
        self.assertEqual(C.encode_event_line(dict(reversed(list(source.items())))), GOLDEN)
        self.assertNotIn("row_md5", source)
        self.assertNotIn("prev_row_md5", source)

    def test_previous_hash_includes_exact_lf(self):
        second = C.encode_event_line(event("PROGRESS", stage="PNL_COMPUTED"), previous_line=GOLDEN)
        decoded = C.decode_event_line(second)
        full_hash = hashlib.md5(GOLDEN, usedforsecurity=False).hexdigest()
        self.assertEqual(decoded["prev_row_md5"], full_hash)
        self.assertNotEqual(full_hash, hashlib.md5(GOLDEN[:-1], usedforsecurity=False).hexdigest())
        self.assertEqual(len(C.verify_event_lines([GOLDEN, second])), 2)
        self.assertEqual(C.verify_event_lines([second], previous_line=GOLDEN), (decoded,))
        with self.assertRaises(C.CodecError):
            C.verify_event_lines([second])
        with self.assertRaises(C.CodecError):
            C.encode_event_line(event(), previous_line=GOLDEN[:-1])

    def test_row_hash_excludes_both_chain_fields(self):
        standalone = C.encode_event_line(event("FINISHED", status="COMPLETED"))
        linked = C.encode_event_line(event("FINISHED", status="COMPLETED"), previous_line=GOLDEN)
        a, b = C.decode_event_line(standalone), C.decode_event_line(linked)
        self.assertEqual(a["row_md5"], b["row_md5"])
        self.assertNotEqual(a["prev_row_md5"], b["prev_row_md5"])

    def test_chain_mutation_drop_reorder_and_torn_record_refused(self):
        second = C.encode_event_line(event("PROGRESS", stage="PNL_COMPUTED"), previous_line=GOLDEN)
        third = C.encode_event_line(event("FINISHED", status="COMPLETED"), previous_line=second)
        streams = ([GOLDEN, third], [second, GOLDEN, third], [GOLDEN, third, second],
                   [GOLDEN, second[:-1]], [GOLDEN, second.replace(b"PNL_COMPUTED", b"DATA_LOADED")])
        for stream in streams:
            with self.subTest(stream=stream):
                with self.assertRaises(C.CodecError):
                    C.verify_event_lines(stream)
        # Consistent suffix removal is unknowable without an independent tail anchor.
        self.assertEqual(len(C.verify_event_lines([GOLDEN, second])), 2)
        self.assertEqual(len(C.verify_event_lines([GOLDEN, second, third])), 3)
        self.assertEqual(C.verify_event_lines([]), ())

    def test_rehashed_wrong_link_is_refused_by_stream_not_single_line(self):
        changed = json.loads(GOLDEN)
        changed["prev_row_md5"] = "0" * 32
        wrong_link = wire(changed)
        self.assertEqual(C.decode_event_line(wrong_link)["prev_row_md5"], "0" * 32)
        with self.assertRaises(C.CodecError):
            C.verify_event_lines([wrong_link])

    def test_nonfinite_paths_escape_keys_arrays_and_preserve_input(self):
        stats = {"a/b~c": [1.25, float("nan"), {"": float("inf")}],
                 "": {"0": -float("inf")}, "null": None, "문구": "한글\n원문"}
        source = event("PROGRESS", stats=stats)
        decoded = C.decode_event_line(C.encode_event_line(source))
        self.assertEqual(decoded["nonfinite"],
                         ["/stats//0", "/stats/a~1b~0c/1", "/stats/a~1b~0c/2/"])
        self.assertEqual(decoded["stats"]["a/b~c"], [1.25, None, {"": None}])
        self.assertIsNone(decoded["stats"]["null"])
        self.assertNotIn("/stats/null", decoded["nonfinite"])
        self.assertEqual(decoded["stats"]["문구"], "한글\n원문")
        self.assertTrue(math.isnan(stats["a/b~c"][1]))
        self.assertEqual(stats["a/b~c"][2][""], float("inf"))
        self.assertNotIn("nonfinite", source)
        self.assertNotIn("row_md5", source)

    def test_existing_nonfinite_markers_merge_without_inventing_origin(self):
        source = event("PROGRESS", stats={"a": None, "b": float("nan")}, nonfinite=["/stats/a"])
        decoded = C.decode_event_line(C.encode_event_line(source))
        self.assertEqual(decoded["nonfinite"], ["/stats/a", "/stats/b"])
        self.assertEqual(source["nonfinite"], ["/stats/a"])
        # Supplied markers only attest structurally to null, not to its historic origin.
        self.assertEqual(C.decode_event_line(wire(event("PROGRESS", stats={"a": None},
                                                       nonfinite=["/stats/a"])))['stats'], {"a": None})

    def test_invalid_nonfinite_markers_refused(self):
        base = event("PROGRESS", stats={"a": None, "b": [None], "c": 1.0})
        markers = (None, "a", [1], ["stats/a"], ["/stats/a", "/stats/a"],
                   ["/stats/b/0", "/stats/a"], ["/stats/b/00"], ["/stats/b/-1"],
                   ["/stats/b/١"], ["/stats/b/2"], ["/stats/missing"], ["/stats/c"],
                   ["/stats/a~2"], ["/nonfinite/0"], ["/prev_row_md5"])
        for value in markers:
            with self.subTest(markers=value):
                with self.assertRaises(C.CodecError):
                    C.encode_event_line(dict(base, nonfinite=value))
                with self.assertRaises(C.CodecError):
                    C.decode_event_line(wire(dict(base, nonfinite=value)))

    def test_unknown_schema_events_and_cross_event_fields_refused(self):
        variants = (dict(event(), schema="qg-run-registry/2"), dict(event(), event="FUTURE"),
                    dict(event(), event=[]), dict(event(), status="COMPLETED"),
                    event("FINISHED", grid=[]), dict(event(), unknown=None),
                    dict(event(), row_md5="0" * 32), dict(event(), prev_row_md5=None))
        for source in variants:
            with self.subTest(source=source):
                with self.assertRaises(C.CodecError):
                    C.encode_event_line(source)
        for source in variants[:6]:
            with self.assertRaises(C.CodecError):
                C.decode_event_line(wire(source))

    def test_event_types_and_envelope_only_boundary(self):
        for kind in ("STARTED", "PROGRESS", "FINISHED", "FINGERPRINT", "SHADOW"):
            with self.subTest(kind=kind):
                self.assertEqual(C.decode_event_line(C.encode_event_line(event(kind)))["event"], kind)
        # Omitted required-by-full-design request/results fields are outside envelope validation.
        self.assertEqual(C.decode_event_line(C.encode_event_line(event("STARTED")))["event"], "STARTED")
        for kind in ("SUPERSEDED", "DECLARATION", "ANNOTATION", "BACKFILL"):
            source = event(kind, writer="tools/r3/annotate.py", person=None, owner_ruling=None)
            self.assertIsNone(C.decode_event_line(C.encode_event_line(source))["owner_ruling"])
            del source["person"]
            with self.assertRaises(C.CodecError):
                C.encode_event_line(source)
        segment = event("SEGMENT_START")
        del segment["run_id"]
        self.assertEqual(C.decode_event_line(C.encode_event_line(segment))["event"], "SEGMENT_START")
        with self.assertRaises(C.CodecError):
            C.encode_event_line(dict(segment, previous_segment="invented-key.jsonl"))
        with self.assertRaises(C.CodecError):
            C.encode_event_line(dict(segment, writer="tools/r3/registry_segment.py"))

    def test_basic_envelope_types_dates_and_optional_ids(self):
        for name, value in (("recorded_utc", None), ("writer", ""), ("writer", 1),
                            ("person", False), ("run_id", None), ("parent_run_id", "bad"),
                            ("recorded_utc", "2026-11-06T08:09:10Z"),
                            ("recorded_utc", "2026-11-06T08:09:10.123456+00:00"),
                            ("recorded_utc", "2026-02-30T08:09:10.123456Z"),
                            ("recorded_utc", "２０２６-11-06T08:09:10.123456Z")):
            with self.subTest(name=name, value=value):
                with self.assertRaises(C.CodecError):
                    C.encode_event_line(dict(event(), **{name: value}))
        for name in ("schema", "event", "recorded_utc", "writer", "run_id"):
            source = event()
            del source[name]
            with self.assertRaises(C.CodecError):
                C.encode_event_line(source)
        for kind in ("DECLARATION", "BACKFILL"):
            source = event(kind, person="synthetic")
            del source["run_id"]
            C.encode_event_line(source)

    def test_malformed_encoding_duplicates_noncanonical_and_nonfinite_wire(self):
        duplicate = GOLDEN.replace(b'"event":"STARTED",', b'"event":"STARTED","event":"STARTED",')
        variants = [b"\xff\n", GOLDEN[:-1], GOLDEN + b"\n", GOLDEN.replace(b"\n", b"\r\n"),
                    b"\xef\xbb\xbf" + GOLDEN, GOLDEN.replace(b":", b": ", 1), duplicate,
                    b"[]\n", b"null\n", b"{}\n", b"{\n", GOLDEN.decode("utf-8")]
        progress = wire(event("PROGRESS", stats={"x": 1.0}))
        variants += [progress.replace(b'"x":1.0', b'"x":1.0,"x":1.0'),
                     progress.replace(b'"x":1.0', b'"x":NaN'),
                     progress.replace(b'"x":1.0', b'"x":Infinity'),
                     progress.replace(b'"x":1.0', b'"x":1e309'),
                     progress.replace(b'"x":1.0', b'"x":"\\ud800"'),
                     progress.replace(b'"x":1.0', b'"x":1.00')]
        for line in variants:
            with self.subTest(line=line):
                with self.assertRaises(C.CodecError):
                    C.decode_event_line(line)

    def test_bad_hashes_or_missing_chain_fields_refused(self):
        original = json.loads(GOLDEN)
        for name, value in (("row_md5", "0" * 32), ("row_md5", "A" * 32),
                            ("row_md5", None), ("prev_row_md5", "z" * 32),
                            ("prev_row_md5", 0)):
            changed = dict(original, **{name: value})
            line = (json.dumps(changed, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with self.assertRaises(C.CodecError):
                C.decode_event_line(line)
        for name in ("row_md5", "prev_row_md5"):
            changed = dict(original)
            del changed[name]
            with self.assertRaises(C.CodecError):
                C.decode_event_line((json.dumps(changed) + "\n").encode())

    def test_non_json_keys_values_cycles_and_detached_return(self):
        for stats in ({1: "one", "1": "string"}, {"x": object()}, {"x": (1, 2)}, {"x": "\ud800"}):
            with self.subTest(stats=repr(stats)):
                with self.assertRaises(C.CodecError):
                    C.encode_event_line(event("PROGRESS", stats=stats))
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaises(C.CodecError):
            C.encode_event_line(event("PROGRESS", stats={"x": cyclic}))
        stats = {"x": [1, 2]}
        source = event("PROGRESS", stats=stats)
        snapshot = copy.deepcopy(source)
        decoded = C.decode_event_line(C.encode_event_line(source))
        decoded["stats"]["x"].append(3)
        self.assertEqual(source, snapshot)

    def test_integer_conversion_limit_is_controlled_without_changing_it(self):
        limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if limit:
            with self.assertRaises(C.CodecError):
                C.encode_event_line(event("PROGRESS", stats={"x": 10 ** limit}))
        else:
            # Python 3.10 or a caller-disabled conversion limit: retain exact JSON integer.
            value = 10 ** 5000
            decoded = C.decode_event_line(C.encode_event_line(event("PROGRESS", stats={"x": value})))
            self.assertEqual(decoded["stats"]["x"], value)

    def test_lab_id_supplied_utc_token_and_early_year(self):
        calls = []
        def token():
            calls.append(True)
            return "0123abcd"
        self.assertEqual(C.make_run_id("FAM", at=datetime(2026, 11, 6, 8, 9, 10, 999999,
                                                          tzinfo=timezone.utc), token_source=token), RUN)
        self.assertEqual(calls, [True])
        self.assertEqual(C.make_run_id("A", at=datetime(1, 1, 1, tzinfo=timezone.utc),
                                      token_source=lambda: "00000000"),
                         "LAB-00010101T000000Z-A-00000000")
        self.assertEqual(C.validate_run_id("LAB-20240229T235959Z-A-00000000"),
                         "LAB-20240229T235959Z-A-00000000")

    def test_invalid_id_family_calendar_token_and_timezone(self):
        for value in (None, RUN + "\n", RUN.replace("2026", "２０２６"),
                      RUN.replace("20261106", "20260229"), RUN.replace("080910", "246010"),
                      RUN.replace("FAM", "A" * 33), RUN.replace("FAM", "-A"),
                      RUN.replace("FAM", "a"), RUN.replace("abcd", "ABCD")):
            with self.subTest(value=value):
                with self.assertRaises(C.CodecError):
                    C.validate_run_id(value)
        utc = datetime(2026, 11, 6, tzinfo=timezone.utc)
        for family in ("", "lower", "_A", "A" * 33, "한", 1):
            with self.assertRaises(C.CodecError):
                C.make_run_id(family, at=utc, token_source=lambda: "0123abcd")
        for token in ("0" * 7, "0" * 9, "ABCDEF00", "gggggggg", 1):
            with self.assertRaises(C.CodecError):
                C.make_run_id("A", at=utc, token_source=lambda: token)
        for at in (datetime(2026, 11, 6), datetime(2026, 11, 6, tzinfo=timezone(timedelta(hours=9))),
                   "2026-11-06T00:00:00Z"):
            with self.assertRaises(C.CodecError):
                C.make_run_id("A", at=at, token_source=lambda: "0123abcd")


if __name__ == "__main__":
    unittest.main()
