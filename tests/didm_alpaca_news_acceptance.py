"""Synthetic supplied Alpaca metadata contracts; no clients, keys or actual news."""
from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, asdict
from datetime import datetime, timedelta, timezone, tzinfo
import math
import unittest

from core.didm.ingest.alpaca_news import (
    AlpacaNewsError, locally_available_as_of, parse_article, parse_page,
)

RECEIVED = datetime(2026, 11, 23, 1, tzinfo=timezone.utc)


def supplied(**changes):
    row = {
        "id": 0, "headline": "SYNTHETIC metadata contract", "author": "",
        "created_at": "2026-11-22T23:00:00Z", "updated_at": "2026-11-23T00:00:00Z",
        "summary": "SYNTHETIC SUMMARY NOT RETAINED", "content": "SYNTHETIC BODY NOT RETAINED",
        "images": [], "symbols": ["TEST", "TEST"], "source": "SYNTHETIC_ONLY",
        "url": "https://example.invalid/synthetic-news",
    }
    row.update(changes)
    return row


class ArticleContracts(unittest.TestCase):
    def test_int64_ids_include_zero_without_boolean_or_float_coercion(self):
        for value in (0, -(2**63), 2**63 - 1):
            with self.subTest(value=value):
                self.assertEqual(parse_article(supplied(id=value), RECEIVED).article_id, value)
        for value in (True, False, "0", 0.0, math.nan, math.inf, -(2**63) - 1, 2**63):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(AlpacaNewsError):
                    parse_article(supplied(id=value), RECEIVED)

    def test_documented_required_fields_cannot_be_replaced_by_defaults(self):
        for field in ("id", "headline", "author", "created_at", "updated_at", "summary",
                      "content", "images", "symbols", "source"):
            raw = supplied()
            del raw[field]
            with self.subTest(field=field):
                with self.assertRaises(AlpacaNewsError):
                    parse_article(raw, RECEIVED)
        for raw in (None, [], "not an object"):
            with self.assertRaises(AlpacaNewsError):
                parse_article(raw, RECEIVED)

    def test_optional_url_absence_null_and_string_are_distinct(self):
        raw = supplied()
        del raw["url"]
        missing = parse_article(raw, RECEIVED)
        null = parse_article(supplied(url=None), RECEIVED)
        empty = parse_article(supplied(url=""), RECEIVED)
        self.assertEqual((missing.url, missing.url_present), (None, False))
        self.assertEqual((null.url, null.url_present), (None, True))
        self.assertEqual((empty.url, empty.url_present), ("", True))
        for value in (False, 0, [], {}):
            with self.assertRaises(AlpacaNewsError):
                parse_article(supplied(url=value), RECEIVED)

    def test_string_fields_preserve_documented_empty_author_and_body(self):
        record = parse_article(supplied(author="", summary="", content=""), RECEIVED)
        self.assertEqual(record.author, "")
        for field in ("headline", "source"):
            with self.assertRaises(AlpacaNewsError):
                parse_article(supplied(**{field: ""}), RECEIVED)
        for field in ("headline", "author", "source", "summary", "content"):
            for value in (None, False, 0, []):
                with self.subTest(field=field, kind=type(value).__name__):
                    with self.assertRaises(AlpacaNewsError):
                        parse_article(supplied(**{field: value}), RECEIVED)

    def test_symbols_are_an_immutable_ordered_array_without_deduplication(self):
        raw = supplied(symbols=["TEST", "", "TEST"])
        record = parse_article(raw, RECEIVED)
        self.assertEqual(record.symbols, ("TEST", "", "TEST"))
        raw["symbols"].append("LATER")
        self.assertEqual(record.symbols, ("TEST", "", "TEST"))
        self.assertEqual(parse_article(supplied(symbols=[]), RECEIVED).symbols, ())
        for value in (None, "TEST", ("TEST",), [None], [1]):
            with self.assertRaises(AlpacaNewsError):
                parse_article(supplied(symbols=value), RECEIVED)

    def test_known_image_shapes_are_checked_without_retaining_image_data(self):
        record = parse_article(supplied(images=[{
            "size": "thumb", "url": "https://example.invalid/SYNTHETIC-IMAGE", "extension": "ignored",
        }]), RECEIVED)
        self.assertNotIn("images", asdict(record))
        for value in (None, {}, [None], [{}], [{"size": "giant", "url": "x"}],
                      [{"size": "small", "url": ""}], [{"size": "small", "url": None}]):
            with self.assertRaises(AlpacaNewsError):
                parse_article(supplied(images=value), RECEIVED)

    def test_bodies_and_unknown_fields_are_tolerated_but_not_retained(self):
        record = parse_article(supplied(unknown={"nested": object()}), RECEIVED)
        output = asdict(record)
        for field in ("content", "summary", "images", "unknown"):
            self.assertNotIn(field, output)
        self.assertNotIn("SYNTHETIC BODY NOT RETAINED", repr(output))
        self.assertNotIn("SYNTHETIC SUMMARY NOT RETAINED", repr(output))
        sentinel = "SYNTHETIC-UNTRUSTED-VALUE"
        with self.assertRaises(AlpacaNewsError) as caught:
            parse_article(supplied(created_at=sentinel), RECEIVED)
        self.assertNotIn(sentinel, str(caught.exception))

    def test_snapshot_is_frozen_and_input_mapping_is_not_mutated(self):
        raw = supplied()
        original = copy.deepcopy(raw)
        record = parse_article(raw, RECEIVED)
        self.assertEqual(raw, original)
        with self.assertRaises(FrozenInstanceError):
            record.headline = "CHANGED"
        with self.assertRaises(FrozenInstanceError):
            record.created.raw = "CHANGED"

    def test_creation_update_and_receipt_clocks_stay_separate(self):
        received_elsewhere = RECEIVED.astimezone(timezone(timedelta(hours=9)))
        record = parse_article(supplied(created_at="2026-11-23T08:00:00+09:00"), received_elsewhere)
        self.assertEqual(record.created.raw, "2026-11-23T08:00:00+09:00")
        self.assertEqual(record.created.utc, datetime(2026, 11, 22, 23, tzinfo=timezone.utc))
        self.assertLess(record.created.utc, record.updated.utc)
        self.assertLess(record.updated.utc, record.received_at_utc)
        self.assertEqual(record.received_at_utc, RECEIVED)

    def test_nanosecond_versions_do_not_collapse_into_microsecond_datetimes(self):
        first = parse_article(supplied(updated_at="2026-11-23T00:00:00.123456001Z"), RECEIVED)
        second = parse_article(supplied(updated_at="2026-11-23T00:00:00.123456999Z"), RECEIVED)
        self.assertEqual(first.updated.utc, second.updated.utc)
        self.assertEqual(second.updated.epoch_nanoseconds - first.updated.epoch_nanoseconds, 998)
        self.assertEqual(first.updated.raw, "2026-11-23T00:00:00.123456001Z")
        close_receipt = datetime(2026, 11, 23, 0, 0, 0, 123456, tzinfo=timezone.utc)
        with self.assertRaises(AlpacaNewsError):
            parse_article(supplied(updated_at="2026-11-23T00:00:00.123456001Z"), close_receipt)

    def test_ambiguous_malformed_and_unsupported_time_inputs_are_not_guessed(self):
        invalid = (None, 0, "2026-11-23", "2026-11-23T00:00:00", "2026-11-23T00:00:00-00:00",
                   "2026-11-23T00:00:00+24:00", "2026-11-23T00:00:00+00:60",
                   "2026-02-30T00:00:00Z", "2026-11-23T00:00:60Z",
                   "2026-11-23T00:00:00.1234567891Z",
                   "2026-11-23T00:00:00.١٢٣٤٥٦٧٨٩Z",
                   "2026-11-23T00:00:00.１２３４５６７８９Z")
        for field in ("created_at", "updated_at"):
            for stamp in invalid:
                with self.subTest(field=field, stamp_type=type(stamp).__name__):
                    with self.assertRaises(AlpacaNewsError):
                        parse_article(supplied(**{field: stamp}), RECEIVED)

    def test_backwards_future_or_unaware_clocks_are_rejected_without_backdating(self):
        for changes in ({"updated_at": "2026-11-22T22:00:00Z"},
                        {"updated_at": "2026-11-23T02:00:00Z"},
                        {"created_at": "2026-11-23T02:00:00Z", "updated_at": "2026-11-23T03:00:00Z"}):
            with self.assertRaises(AlpacaNewsError):
                parse_article(supplied(**changes), RECEIVED)
        class UnknownTimezone(tzinfo):
            def utcoffset(self, value):
                return None
        for receipt in (None, "2026-11-23T01:00:00Z", datetime(2026, 11, 23),
                        datetime(2026, 11, 23, tzinfo=UnknownTimezone())):
            with self.assertRaises(AlpacaNewsError):
                parse_article(supplied(), receipt)

    def test_local_asof_never_exposes_a_late_snapshot_at_its_creation_time(self):
        record = parse_article(supplied(), RECEIVED)
        self.assertFalse(locally_available_as_of(record, record.created.utc))
        self.assertFalse(locally_available_as_of(record, record.updated.utc))
        self.assertFalse(locally_available_as_of(record, RECEIVED - timedelta(microseconds=1)))
        self.assertTrue(locally_available_as_of(record, RECEIVED))
        self.assertTrue(locally_available_as_of(record, RECEIVED.astimezone(timezone(timedelta(hours=9)))))
        with self.assertRaises(AlpacaNewsError):
            locally_available_as_of(record, datetime(2026, 11, 23))
        with self.assertRaises(AlpacaNewsError):
            locally_available_as_of({}, RECEIVED)
        self.assertFalse(hasattr(record, "historical_pit_approved"))


class PageContracts(unittest.TestCase):
    def test_only_null_token_is_terminal_regardless_of_page_length(self):
        empty = parse_page({"news": [], "next_page_token": ""}, RECEIVED, limit=1)
        self.assertEqual(empty.next_page_token, "")
        short = parse_page({"news": [], "next_page_token": "NEXT"}, RECEIVED, limit=50)
        self.assertEqual(short.next_page_token, "NEXT")
        terminal = parse_page({"news": [supplied()], "next_page_token": None}, RECEIVED, limit=1)
        self.assertIsNone(terminal.next_page_token)
        self.assertFalse(hasattr(terminal, "whole_range_complete"))
        with self.assertRaises(FrozenInstanceError):
            terminal.next_page_token = "CHANGED"

    def test_response_envelope_requires_news_and_explicit_nullable_token(self):
        for payload in (None, [], {}, {"news": []}, {"next_page_token": None},
                        {"news": None, "next_page_token": None},
                        {"news": {}, "next_page_token": None}):
            with self.assertRaises(AlpacaNewsError):
                parse_page(payload, RECEIVED, limit=10)
        page = parse_page({"news": [], "next_page_token": None, "unknown": object()}, RECEIVED, limit=10)
        self.assertEqual(page.articles, ())

    def test_limits_and_row_count_obey_documented_bounds(self):
        for limit in (True, False, 0, 51, 1.0, "1"):
            with self.assertRaises(AlpacaNewsError):
                parse_page({"news": [], "next_page_token": None}, RECEIVED, limit=limit)
        for limit in (1, 50):
            self.assertEqual(parse_page({"news": [], "next_page_token": None}, RECEIVED, limit=limit).articles, ())
        with self.assertRaises(AlpacaNewsError):
            parse_page({"news": [supplied(), supplied()], "next_page_token": None}, RECEIVED, limit=1)

    def test_tokens_stay_opaque_and_are_not_echoed_in_errors(self):
        token = "SYNTHETIC-OPAQUE-TOKEN +/=\n"
        page = parse_page({"news": [], "next_page_token": token}, RECEIVED, limit=1)
        self.assertEqual(page.next_page_token, token)
        for value in (True, 0, [], {}):
            with self.assertRaises(AlpacaNewsError):
                parse_page({"news": [], "next_page_token": value}, RECEIVED, limit=1)
        with self.assertRaises(AlpacaNewsError) as caught:
            parse_page({"news": [], "next_page_token": token}, RECEIVED, limit=1, current_token=token)
        self.assertNotIn(token, str(caught.exception))

    def test_current_and_seen_token_cycles_are_refused_including_empty_token(self):
        for current, seen, following in (("NEXT", (), "NEXT"), (None, ("OLD",), "OLD"), ("", (), "")):
            with self.assertRaises(AlpacaNewsError):
                parse_page({"news": [], "next_page_token": following}, RECEIVED, limit=1,
                           current_token=current, seen_tokens=seen)
        for current, seen in ((False, ()), (None, ["OLD"]), (None, (None,))):
            with self.assertRaises(AlpacaNewsError):
                parse_page({"news": [], "next_page_token": None}, RECEIVED, limit=1,
                           current_token=current, seen_tokens=seen)

    def test_duplicate_ids_revised_rows_and_original_order_are_preserved(self):
        rows = [supplied(id=7), supplied(id=7, headline="SYNTHETIC revision", updated_at="2026-11-23T00:30:00Z"),
                supplied(id=7)]
        page = parse_page({"news": rows, "next_page_token": "NEXT"}, RECEIVED, limit=3)
        self.assertEqual([a.article_id for a in page.articles], [7, 7, 7])
        self.assertEqual([a.headline for a in page.articles], [r["headline"] for r in rows])
        self.assertEqual(page.articles[0], page.articles[2])
        self.assertNotEqual(page.articles[0].updated, page.articles[1].updated)

    def test_bad_later_row_causes_no_partial_result_or_input_mutation(self):
        payload = {"news": [supplied(), supplied(id=True)], "next_page_token": "NEXT"}
        original = copy.deepcopy(payload)
        with self.assertRaises(AlpacaNewsError):
            parse_page(payload, RECEIVED, limit=2)
        self.assertEqual(payload, original)
        with self.assertRaises(AlpacaNewsError):
            parse_page({"news": [], "next_page_token": None}, datetime(2026, 11, 23), limit=1)


if __name__ == "__main__":
    unittest.main()
