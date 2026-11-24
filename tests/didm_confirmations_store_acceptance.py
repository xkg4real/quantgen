"""DS-8: tools.didm.confirmations stores didm-confirmation-v0 lines in a second point-in-time store. Offline."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.didm.llm.schema import MarketConfirmation as MC
from core.didm.models import confirmation as cf
from core.didm.models import confirmation_log as cl
from core.didm.store import PointInTimeStore
from tools.didm import confirmations as c

T0 = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
PUB = datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc)
SHA = "a" * 64
OTHER_RULE = cf.ConfirmationConfig(already_priced="after_event_window")


def entry(status=MC.PENDING, known_at=T0, sha=SHA, record="rec-1", config=cf.DEFAULT_CONFIG):
    return cl.make_entry(record_id=record, judgement_sha256=sha, status=status, known_at=known_at, config=config)


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = Clock(T0)
        self.cs = c.ConfirmationStore.open(self.tmp.name, clock=self.clock)
        self.addCleanup(self.cs.close)


class Writing(Base):
    def test_row_shape(self):
        self.assertTrue(self.cs.append(entry(), record_published_at=PUB))
        self.assertTrue((Path(self.tmp.name) / "didm_derived.sqlite").is_file())
        self.assertFalse((Path(self.tmp.name) / "didm_store.sqlite").exists())
        rows = self.cs.store.as_of(c.FAR_FUTURE, source_id="didm-confirmation-v0")
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r.kind, r.item_id), ("market_confirmation", f"rec-1@{cl.rule_version()}"))
        self.assertEqual((r.published_at, r.valid_at, r.received_at),
                         (T0.isoformat(timespec="microseconds"), PUB.isoformat(timespec="microseconds"),
                          T0.isoformat(timespec="microseconds")))
        self.assertEqual(cl.loads(r.payload["line"]), entry())

    def test_known_at_not_in_the_past(self):
        with self.assertRaises(c.ConfirmationStoreError):
            self.cs.append(entry(known_at=T0 - timedelta(days=3)), record_published_at=PUB)
        with self.assertRaises(c.ConfirmationStoreError):
            self.cs.append(entry(known_at=T0 + timedelta(hours=1)), record_published_at=PUB)
        self.assertTrue(self.cs.append(entry(known_at=T0 - timedelta(minutes=4)), record_published_at=PUB))

    def test_replay_is_separate(self):
        with c.ConfirmationStore(self.cs.store, replay=True, clock=self.clock) as replay:
            self.assertTrue(replay.append(entry(known_at=datetime(2019, 1, 2, tzinfo=timezone.utc)),
                                          record_published_at=PUB))
            self.assertEqual(len(replay.entries()), 1)
            self.assertEqual(self.cs.entries(), [])
            self.assertIsNone(self.cs.as_of("rec-1", T0))
            self.assertEqual(replay.source_id, "didm-confirmation-v0-replay")

    def test_same_key_different_line_refused_same_line_noop(self):
        self.assertTrue(self.cs.append(entry(MC.PENDING), record_published_at=PUB))
        self.assertFalse(self.cs.append(entry(MC.PENDING), record_published_at=PUB))
        with self.assertRaises(c.ConfirmationStoreError):
            self.cs.append(entry(MC.CONFIRMED), record_published_at=PUB)
        self.assertEqual(len(self.cs.entries("rec-1")), 1)

    def test_didm_dev_rules_applied_to_history(self):
        self.cs.append(entry(MC.CONFIRMED), record_published_at=PUB)
        self.clock.t = T0 + timedelta(days=1)
        with self.assertRaises(cl.ConfirmationLogError):           # final verdict changes under one rule
            self.cs.append(entry(MC.CONTRADICTED, known_at=self.clock.t), record_published_at=PUB)
        with self.assertRaises(cl.ConfirmationLogError):           # another judgement of the same record
            self.cs.append(entry(MC.CONFIRMED, known_at=self.clock.t, sha="b" * 64), record_published_at=PUB)
        self.assertTrue(self.cs.append(entry(MC.CONTRADICTED, known_at=self.clock.t, config=OTHER_RULE),
                                       record_published_at=PUB))   # a new rule version may re-evaluate


class Reading(Base):
    def test_pending_then_confirmed(self):
        self.cs.append(entry(MC.PENDING), record_published_at=PUB)
        self.clock.t = T0 + timedelta(days=2)
        self.cs.append(entry(MC.CONFIRMED, known_at=self.clock.t), record_published_at=PUB)
        self.assertEqual(self.cs.status_as_of("rec-1", T0 - timedelta(seconds=1)), MC.PENDING)  # nothing known
        self.assertIsNone(self.cs.as_of("rec-1", T0 - timedelta(seconds=1)))
        self.assertEqual(self.cs.status_as_of("rec-1", T0 + timedelta(days=1)), MC.PENDING)
        self.assertEqual(self.cs.status_as_of("rec-1", T0 + timedelta(days=2)), MC.CONFIRMED)
        with self.assertRaises(c.ConfirmationStoreError):
            self.cs.visible(datetime(2026, 11, 25))

    def test_later_of_known_at_and_receipt(self):
        """known_at and the store's receipt differ (within the allowed skew): the later one decides."""
        self.clock.t = T0 + timedelta(minutes=3)                   # stored 3 minutes after known_at
        self.cs.append(entry(MC.PENDING, known_at=T0), record_published_at=PUB)
        self.assertIsNone(self.cs.as_of("rec-1", T0 + timedelta(minutes=1)))    # known, not yet stored
        self.assertIsNotNone(self.cs.as_of("rec-1", T0 + timedelta(minutes=3)))
        self.clock.t = T0 + timedelta(days=1)                      # stored before its known_at
        k = self.clock.t + timedelta(minutes=2)
        self.cs.append(entry(MC.CONFIRMED, known_at=k), record_published_at=PUB)
        self.assertEqual(self.cs.status_as_of("rec-1", self.clock.t + timedelta(minutes=1)), MC.PENDING)
        self.assertEqual(self.cs.status_as_of("rec-1", k), MC.CONFIRMED)

    def test_rule_filter_and_record_scoping(self):
        self.cs.append(entry(MC.CONFIRMED), record_published_at=PUB)
        self.cs.append(entry(MC.CONTRADICTED, config=OTHER_RULE), record_published_at=PUB)
        self.cs.append(entry(MC.PENDING, record="rec-10", sha="c" * 64), record_published_at=PUB)
        self.assertEqual(self.cs.as_of("rec-1", T0, rule=cl.rule_version()).status, MC.CONFIRMED)
        self.assertEqual(self.cs.as_of("rec-1", T0, rule=cl.rule_version(OTHER_RULE)).status, MC.CONTRADICTED)
        self.assertEqual({e.record_id for e in self.cs.entries("rec-1")}, {"rec-1"})
        self.assertEqual(len(self.cs.entries()), 3)

    def test_reopen_reads_same(self):
        self.cs.append(entry(MC.CONFIRMED), record_published_at=PUB)
        self.cs.close()
        with c.ConfirmationStore.open(self.tmp.name, clock=self.clock) as again:
            self.assertEqual(again.status_as_of("rec-1", T0), MC.CONFIRMED)
        self.cs = c.ConfirmationStore(PointInTimeStore(Path(self.tmp.name) / c.DERIVED_FILE), clock=self.clock)


if __name__ == "__main__":
    unittest.main()
