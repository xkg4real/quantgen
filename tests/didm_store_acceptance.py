"""DS-4a: point-in-time store -- same 'as of' query gives the same records. No network."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.didm.store import PointInTimeStore, StoreError


def row(item, received, value, published="2026-11-05T19:00:00Z"):
    return dict(source_id="s", item_id=item, kind="k", published_at=published,
                received_at=received, payload={"v": value})


class Store(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PointInTimeStore(Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_same_as_of_same_answer(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        self.store.append(**row("b", "2026-11-05T19:30:00Z", 2))
        first = self.store.as_of("2026-11-05T20:00:00Z")
        second = self.store.as_of("2026-11-05T20:00:00Z")
        self.assertEqual(first, second)
        self.assertEqual([i.item_id for i in first], ["a", "b"])

    def test_later_rows_do_not_change_past_answer(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        before = self.store.as_of("2026-11-05T20:00:00Z")
        self.store.append(**row("a", "2026-11-06T09:00:00Z", 99))   # correction
        self.store.append(**row("c", "2026-11-06T09:00:00Z", 3))
        self.assertEqual(self.store.as_of("2026-11-05T20:00:00Z"), before)
        latest = {i.item_id: i.payload["v"] for i in self.store.as_of("2026-11-07T00:00:00Z")}
        self.assertEqual(latest, {"a": 99, "c": 3})

    def test_corrections_appended_not_overwritten(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        self.store.append(**row("a", "2026-11-06T09:00:00Z", 2))
        self.assertEqual([h.payload["v"] for h in self.store.history("s", "a")], [1, 2])

    def test_duplicate_is_ignored(self):
        self.assertTrue(self.store.append(**row("a", "2026-11-05T19:15:00Z", 1)))
        self.assertFalse(self.store.append(**row("a", "2026-11-05T19:15:00Z", 1)))

    def test_conflicting_version_metadata_is_refused_without_changing_history(self):
        original = row("a", "2026-11-05T19:15:00Z", 1)
        self.store.append(**original)
        before = self.store.history("s", "a")
        old_answer = self.store.as_of("2026-11-05T20:00:00Z")
        for changed in ({"kind": "different-kind"},
                        {"published_at": "2026-11-04T19:00:00Z"},
                        {"valid_at": "2026-11-04T19:00:00Z"}):
            with self.subTest(field=next(iter(changed))):
                with self.assertRaisesRegex(StoreError, "conflicting metadata"):
                    self.store.append(**{**original, **changed})
                self.assertEqual(self.store.history("s", "a"), before)
                self.assertEqual(self.store.as_of("2026-11-05T20:00:00Z"), old_answer)
                self.assertFalse(self.store.append(**original))

    def test_duplicate_normalizes_equivalent_timezones(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        equivalent = row("a", "2026-11-06T04:15:00+09:00", 1,
                         published="2026-11-06T04:00:00+09:00")
        equivalent["valid_at"] = "2026-11-06T04:00:00+09:00"
        self.assertFalse(self.store.append(**equivalent))
        self.assertEqual(len(self.store.history("s", "a")), 1)

    def test_later_receipt_can_correct_metadata_without_changing_past_answer(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        before = self.store.as_of("2026-11-05T20:00:00Z")
        corrected = row("a", "2026-11-06T09:00:00Z", 1,
                        published="2026-11-04T19:00:00Z")
        corrected.update(kind="corrected-kind", valid_at="2026-11-04T18:00:00Z")
        self.assertTrue(self.store.append(**corrected))
        self.assertEqual(self.store.as_of("2026-11-05T20:00:00Z"), before)
        history = self.store.history("s", "a")
        self.assertEqual(len(history), 2)
        latest = self.store.as_of("2026-11-07T00:00:00Z")[0]
        self.assertEqual((latest.kind, latest.published_at, latest.valid_at),
                         ("corrected-kind", "2026-11-04T19:00:00.000000+00:00",
                          "2026-11-04T18:00:00.000000+00:00"))

    def test_ingested_metadata_conflict_is_not_reported_as_an_identical_version(self):
        from datetime import datetime, timezone
        from core.didm.ingest.filings import edgar_rows
        received = datetime(2026, 11, 18, 1, 0, tzinfo=timezone.utc)
        submission = {"cik": "123", "name": "Fixture", "tickers": ["TEST"],
                      "filings": {"recent": {
                          "accessionNumber": ["fixture-1"], "form": ["8-K"],
                          "filingDate": ["2026-11-14"],
                          "acceptanceDateTime": ["2026-11-14T16:05:12Z"],
                          "primaryDocument": ["fixture.htm"], "items": ["2.02"],
                      }}}
        first = edgar_rows(submission, received)[0]
        submission["filings"]["recent"]["acceptanceDateTime"] = ["2026-11-14T16:06:12Z"]
        changed = edgar_rows(submission, received)[0]
        self.assertEqual(first["payload"], changed["payload"])
        self.assertNotEqual(first["published_at"], changed["published_at"])
        self.assertTrue(self.store.append(**first))
        with self.assertRaisesRegex(StoreError, "conflicting metadata"):
            self.store.append(**changed)
        self.assertEqual(len(self.store.history(first["source_id"], first["item_id"])), 1)

    def test_conflicting_metadata_is_detected_after_reopen(self):
        original = row("a", "2026-11-05T19:15:00Z", 1)
        self.store.append(**original)
        self.store.close()
        self.store = PointInTimeStore(Path(self.tmp.name) / "t.sqlite")
        with self.assertRaisesRegex(StoreError, "conflicting metadata"):
            self.store.append(**{**original, "kind": "other-kind"})
        self.assertFalse(self.store.append(**original))
        self.assertEqual(len(self.store.history("s", "a")), 1)

    def test_before_receipt_is_empty(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        self.assertEqual(self.store.as_of("2026-11-05T19:14:59Z"), [])

    def test_every_row_has_both_times(self):
        self.store.append(**row("a", "2026-11-05T19:15:00+09:00", 1))
        item = self.store.as_of("2026-11-06T00:00:00Z")[0]
        self.assertTrue(item.published_at.endswith("+00:00"))
        self.assertEqual(item.received_at, "2026-11-05T10:15:00.000000+00:00")

    def test_rejects_missing_or_naive_times(self):
        with self.assertRaises(StoreError):
            self.store.append(**row("a", None, 1))
        with self.assertRaises(StoreError):
            self.store.append(**row("a", "2026-11-05T19:15:00", 1))
        with self.assertRaises(StoreError):
            self.store.append(**row("a", "2026-11-05T19:15:00Z", 1, published=None))

    def test_persists_across_reopen(self):
        self.store.append(**row("a", "2026-11-05T19:15:00Z", 1))
        before = self.store.as_of("2026-11-06T00:00:00Z")
        self.store.close()
        self.store = PointInTimeStore(Path(self.tmp.name) / "t.sqlite")
        self.assertEqual(self.store.as_of("2026-11-06T00:00:00Z"), before)


if __name__ == "__main__":
    unittest.main()
