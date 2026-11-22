"""Supplied synthetic economic rows only; no client, key, network or store calls."""
from __future__ import annotations

import copy
import json
import math
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone, tzinfo

from core.didm.ingest.eodhd import (
    DateWindow, EconomicEventError, ForecastProvenance, PartitionExhausted,
    assess_page, parse_event, partition_dates, split_window,
)


RECEIVED = datetime(2026, 11, 20, 15, tzinfo=timezone.utc)


def supplied(**changes):
    row = {"type": "SYNTHETIC release", "country": "US", "comparison": "mom",
           "period": "Oct", "date": "2026-11-20 13:30:00", "actual": 0,
           "previous": -0.1, "estimate": None, "change": 0,
           "change_percentage": None, "vendor_extension": {"unit": "%", "tag": "TEST_ONLY"}}
    row.update(changes)
    return row


def reviewed_provenance(**changes):
    values = {"published_at": datetime(2026, 11, 20, 12, tzinfo=timezone.utc),
              "publication_basis": "archived_forecast_publication",
              "publication_verified": True, "version_id": "SYNTHETIC-FIXED-V1",
              "version_verified": True, "evidence_reference": "SYNTHETIC-ARCHIVE-RECEIPT"}
    values.update(changes)
    return ForecastProvenance(**values)


class EventInputContracts(unittest.TestCase):
    def test_zero_null_negative_values_and_original_fields_remain_distinct(self):
        raw = supplied(estimate=0, change_percentage=-25.0)
        record = parse_event(raw, RECEIVED)
        self.assertEqual((record.actual, record.previous, record.estimate, record.change,
                          record.change_percentage), (0, -0.1, 0, 0, -25.0))
        self.assertEqual(json.loads(record.raw_payload_json), raw)
        missing = parse_event(supplied(actual=None, estimate=None), RECEIVED)
        self.assertIsNone(missing.actual)
        self.assertIsNone(missing.estimate)
        self.assertIn("missing_estimate", missing.historical_ineligibility_reasons)
        self.assertFalse(missing.historical_forecast_eligible)

    def test_nonfinite_boolean_string_and_overflow_numbers_are_rejected(self):
        for field in ("actual", "previous", "estimate", "change", "change_percentage"):
            for value in (True, False, math.nan, math.inf, -math.inf, "0", [], 10**1000):
                with self.subTest(field=field, kind=type(value).__name__):
                    with self.assertRaises(EconomicEventError):
                        parse_event(supplied(**{field: value}), RECEIVED)

    def test_missing_or_malformed_source_fields_are_rejected(self):
        for patch in ({"type": " "}, {"country": "us"}, {"country": "USA"},
                      {"comparison": "m/m"}, {"period": 2026},
                      {"date": "2026-11-20"}, {"date": "2026-02-30 13:30:00"},
                      {"date": "2026-11-20 25:00:00"}):
            with self.subTest(patch=patch):
                with self.assertRaises(EconomicEventError):
                    parse_event(supplied(**patch), RECEIVED)
        for raw in (None, [], "not a response object"):
            with self.assertRaises(EconomicEventError):
                parse_event(raw, RECEIVED)

    def test_snapshot_is_immutable_and_input_mutation_does_not_change_it(self):
        raw = supplied()
        original = copy.deepcopy(raw)
        record = parse_event(raw, RECEIVED)
        self.assertEqual(raw, original)
        raw["vendor_extension"]["tag"] = "CHANGED AFTER PARSE"
        self.assertEqual(json.loads(record.raw_payload_json), original)
        with self.assertRaises(FrozenInstanceError):
            record.actual = 99
        with self.assertRaises(FrozenInstanceError):
            record.forecast_provenance.version_verified = True

    def test_naive_unknown_and_supplied_offsets_are_labelled_without_UTC_guess(self):
        unknown = parse_event(supplied(), RECEIVED)
        self.assertIsNone(unknown.event_at_utc)
        self.assertEqual(unknown.timezone_basis, "unknown")
        guessed = parse_event(supplied(), RECEIVED, event_utc_offset="+09:00")
        self.assertEqual(guessed.event_at_utc, datetime(2026, 11, 20, 4, 30, tzinfo=timezone.utc))
        self.assertEqual(guessed.timezone_basis, "unverified_supplied_offset")
        self.assertFalse(guessed.historical_forecast_eligible)
        explicit = parse_event(supplied(date="2026-11-20T22:30:00+09:00"), RECEIVED)
        self.assertEqual(explicit.event_at_utc, datetime(2026, 11, 20, 13, 30, tzinfo=timezone.utc))
        self.assertEqual(explicit.timezone_basis, "payload_explicit_offset")
        for raw in ("2026-11-20T13:30:00-00:00",):
            record = parse_event(supplied(date=raw), RECEIVED)
            self.assertIsNone(record.event_at_utc)
            self.assertFalse(record.historical_forecast_eligible)

    def test_bad_offsets_and_conflicting_time_evidence_are_rejected(self):
        for offset in ("UTC", "+24:00", "+00:60", "+9:00", "+01:00:30", True):
            with self.subTest(offset=offset):
                with self.assertRaises(EconomicEventError):
                    parse_event(supplied(), RECEIVED, event_utc_offset=offset)
        for stamp in ("2026-11-20T13:30:00+24:00", "2026-11-20T13:30:00+00:60"):
            with self.assertRaises(EconomicEventError):
                parse_event(supplied(date=stamp), RECEIVED)
        with self.assertRaises(EconomicEventError):
            parse_event(supplied(date="2026-11-20T13:30:00Z"), RECEIVED, event_utc_offset="+09:00")


class ForecastEvidenceContracts(unittest.TestCase):
    def test_ordinary_vendor_row_never_turns_event_or_receipt_into_publication(self):
        record = parse_event(supplied(estimate=0, date="2026-11-20T13:30:00Z"), RECEIVED)
        self.assertFalse(record.historical_forecast_eligible)
        self.assertIsNone(record.forecast_provenance.published_at)
        self.assertIn("forecast_publication_missing", record.historical_ineligibility_reasons)

    def test_response_invented_trust_flags_are_not_promoted_to_provenance(self):
        record = parse_event(supplied(estimate=0, date="2026-11-20T13:30:00Z",
            forecast_published_at="2026-11-20T12:00:00Z", forecast_verified=True,
            version_verified=True), RECEIVED)
        self.assertFalse(record.historical_forecast_eligible)
        self.assertIsNone(record.forecast_provenance.published_at)
        self.assertTrue(json.loads(record.raw_payload_json)["forecast_verified"])

    def test_observation_and_event_time_bases_never_establish_historical_forecast(self):
        for basis in ("observed_at", "event_time", "unknown", "unregistered_basis"):
            with self.subTest(basis=basis):
                record = parse_event(supplied(estimate=0, date="2026-11-20T13:30:00Z"), RECEIVED,
                    forecast_provenance=reviewed_provenance(publication_basis=basis))
                self.assertFalse(record.historical_forecast_eligible)
                self.assertIn("forecast_publication_basis_not_source", record.historical_ineligibility_reasons)

    def test_verified_archive_can_qualify_without_backdating_own_receipt(self):
        received_elsewhere = RECEIVED.astimezone(timezone(timedelta(hours=9)))
        provenance = reviewed_provenance()
        record = parse_event(supplied(estimate=0), received_elsewhere,
            event_utc_offset="Z", event_timezone_verified=True,
            event_timezone_evidence="SYNTHETIC VERIFIED PROVIDER TIMEZONE",
            forecast_provenance=provenance)
        self.assertTrue(record.historical_forecast_eligible)
        self.assertEqual(record.historical_ineligibility_reasons, ())
        self.assertEqual(record.received_at_utc, RECEIVED)
        self.assertEqual(record.forecast_provenance.published_at, provenance.published_at)
        self.assertGreater(record.received_at_utc, record.event_at_utc)

    def test_each_missing_or_untrusted_evidence_component_keeps_row_ineligible(self):
        cases = ({"published_at": None}, {"publication_verified": False},
                 {"version_id": None}, {"version_verified": False}, {"evidence_reference": None})
        for patch in cases:
            with self.subTest(patch=patch):
                record = parse_event(supplied(estimate=0, date="2026-11-20T13:30:00Z"), RECEIVED,
                                     forecast_provenance=reviewed_provenance(**patch))
                self.assertFalse(record.historical_forecast_eligible)
        record = parse_event(supplied(estimate=0), RECEIVED, event_utc_offset="Z",
            forecast_provenance=reviewed_provenance())
        self.assertFalse(record.historical_forecast_eligible)
        self.assertIn("event_timezone_unverified", record.historical_ineligibility_reasons)

    def test_publication_must_precede_event_and_not_follow_own_receipt(self):
        for publication, event in (
            ("2026-11-20T13:30:00+00:00", "2026-11-20T13:30:00Z"),
            ("2026-11-20T14:00:00+00:00", "2026-11-20T13:30:00Z"),
            ("2026-11-20T16:00:00+00:00", "2026-11-21T13:30:00Z"),
        ):
            with self.subTest(publication=publication, event=event):
                record = parse_event(supplied(estimate=0, date=event), RECEIVED,
                    forecast_provenance=reviewed_provenance(published_at=datetime.fromisoformat(publication)))
                self.assertFalse(record.historical_forecast_eligible)

    def test_naive_or_non_datetime_receipt_and_publication_are_invalid(self):
        class UnknownTimezone(tzinfo):
            def utcoffset(self, value):
                return None
        for stamp in (datetime(2026, 11, 20), datetime(2026, 11, 20, tzinfo=UnknownTimezone()),
                      "2026-11-20T15:00:00Z"):
            with self.subTest(stamp_type=type(stamp).__name__):
                with self.assertRaises(EconomicEventError):
                    parse_event(supplied(), stamp)
                with self.assertRaises(EconomicEventError):
                    parse_event(supplied(), RECEIVED,
                        forecast_provenance=reviewed_provenance(published_at=stamp))
        for p in (replace(reviewed_provenance(), publication_verified=1),
                  replace(reviewed_provenance(), version_verified="yes")):
            with self.assertRaises(EconomicEventError):
                parse_event(supplied(), RECEIVED, forecast_provenance=p)


class RangeAndPaginationContracts(unittest.TestCase):
    def test_inclusive_windows_cover_leap_day_once_without_gaps_or_overlap(self):
        windows = partition_dates("2024-02-28", "2024-03-03", max_days=2)
        actual = [w.start + timedelta(days=n) for w in windows
                  for n in range((w.end - w.start).days + 1)]
        expected = [date(2024, 2, 28) + timedelta(days=n) for n in range(5)]
        self.assertEqual(actual, expected)
        self.assertTrue(all((w.end - w.start).days < 2 for w in windows))

    def test_extreme_last_date_and_large_local_window_do_not_overflow(self):
        self.assertEqual(partition_dates(date.max, date.max, max_days=10**100),
                         (DateWindow(date.max, date.max),))
        with self.assertRaises(FrozenInstanceError):
            DateWindow(date(2026, 1, 1), date(2026, 1, 2)).start = date(2020, 1, 1)

    def test_full_last_allowed_page_requires_split_not_false_completion(self):
        self.assertEqual(assess_page(offset=0, limit=1000, returned=1000).next_offset, 1000)
        full_last = assess_page(offset=1000, limit=1000, returned=1000)
        self.assertEqual((full_last.action, full_last.next_offset), ("split_range", None))
        terminal = assess_page(offset=1000, limit=1000, returned=999)
        self.assertEqual((terminal.action, terminal.next_offset), ("end_page", None))
        self.assertEqual(assess_page(offset=0, limit=1, returned=0).action, "end_page")
        self.assertFalse(hasattr(terminal, "whole_range_complete"))

    def test_splits_are_inclusive_and_single_date_saturation_remains_incomplete(self):
        original = DateWindow(date(2026, 1, 1), date(2026, 1, 8))
        left, right = split_window(original)
        self.assertEqual((left.start, right.end), (original.start, original.end))
        self.assertEqual(left.end + timedelta(days=1), right.start)
        with self.assertRaises(PartitionExhausted):
            split_window(DateWindow(date(2026, 1, 1), date(2026, 1, 1)))

    def test_page_bounds_and_invalid_date_windows_are_rejected(self):
        for params in ({"offset": 1001, "limit": 1000, "returned": 1},
                       {"offset": -1, "limit": 1, "returned": 0},
                       {"offset": 0, "limit": 0, "returned": 0},
                       {"offset": 0, "limit": 1001, "returned": 1},
                       {"offset": 0, "limit": 1, "returned": 2},
                       {"offset": False, "limit": 1, "returned": 0}):
            with self.subTest(params=params):
                with self.assertRaises(EconomicEventError):
                    assess_page(**params)
        for lo, hi, maximum in (("2026-02-30", "2026-03-01", 1),
                                ("2026-03-02", "2026-03-01", 1),
                                ("2026-03-01", "2026-03-02", 0),
                                ("2026-03-01", "2026-03-02", True),
                                (datetime(2026, 3, 1), date(2026, 3, 2), 1)):
            with self.assertRaises(EconomicEventError):
                partition_dates(lo, hi, max_days=maximum)


if __name__ == "__main__":
    unittest.main()
