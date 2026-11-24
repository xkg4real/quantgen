"""DS-4c (D9): FedWatch end-of-day format, checks, times, store rows, owner-file path. No network.

Test plan T1-T10 of docs/didm/DS4C_FEDWATCH_DESIGN_2026-11-24.md; T9 (HTTP client) waits for the
owner's OA-31 answer and the official API documents.
"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

from core.didm.ingest import fedwatch as fw
from core.didm.store import PointInTimeStore

RECEIVED = datetime(2026, 11, 24, 12, tzinfo=timezone.utc)
HEADER = "trade_date,meeting_date,lower_bp,upper_bp,probability,published_at,current_lower_bp,current_upper_bp\n"


def line(trade="2026-11-20", meeting="2026-12-16", lo=425, hi=450, p="0.7", pub="", clo="425", chi="450"):
    return f"{trade},{meeting},{lo},{hi},{p},{pub},{clo},{chi}\n"


GOOD = HEADER + "".join([
    line(lo=400, hi=425, p="0.2"), line(p="0.7"), line(lo=450, hi=475, p="0.1"),
    line(meeting="2027-01-27", lo=400, hi=425, p="0.5"), line(meeting="2027-01-27", p="0.5"),
])


def one(text):
    days, refused = fw.read_csv(text)
    return days, refused


class Format(unittest.TestCase):
    def test_t1_rows_ids_and_times(self):
        days, refused = one(GOOD)
        self.assertEqual((len(days), refused), (1, []))
        rows = fw.rows(days[0], RECEIVED)
        self.assertEqual([r["item_id"] for r in rows], ["2026-12-16@2026-11-20", "2027-01-27@2026-11-20"])
        r = rows[0]
        self.assertEqual((r["source_id"], r["kind"]), ("cme-fedwatch", "fedwatch_meeting_dist"))
        self.assertEqual(r["valid_at"], datetime(2026, 11, 20, tzinfo=timezone.utc))
        self.assertEqual(r["payload"]["buckets"], [[400, 425, 0.2], [425, 450, 0.7], [450, 475, 0.1]])
        self.assertEqual(r["payload"]["parser"], fw.PARSER)

    def test_t2_percent_scaled(self):
        text = HEADER + line(lo=400, hi=425, p="20%") + line(p="70") + line(lo=450, hi=475, p="10")
        days, refused = one(text)
        self.assertEqual(refused, [])
        self.assertEqual([p for _, _, p in days[0].meetings[0].buckets], [0.2, 0.7, 0.1])

    def test_t3_bad_probabilities_refused(self):
        for bad in (line(p="0.5"), line(p="-0.1") + line(lo=400, hi=425, p="1.1"), line(p="1.5")):
            with self.subTest(bad=bad):
                days, refused = one(HEADER + bad)
                self.assertEqual((days, len(refused)), ([], 1))

    def test_t4_bad_ranges_refused(self):
        cases = {
            "width": line(lo=425, hi=475, p="1"),
            "overlap": line(lo=400, hi=425, p="0.5") + line(lo=410, hi=435, p="0.5"),
        }
        for name, bad in cases.items():
            with self.subTest(name):
                days, refused = one(HEADER + bad)
                self.assertEqual(days, [])
                self.assertIn("25 bp" if name == "width" else "overlap", refused[0][1])

    def test_t5_past_meeting_refused(self):
        days, refused = one(HEADER + line(meeting="2026-11-20", p="1"))
        self.assertIn("not after", refused[0][1])

    def test_t6_published_at_rules(self):
        days, _ = one(HEADER + line(p="1"))
        self.assertEqual(days[0].published_at, datetime(2026, 11, 21, tzinfo=timezone.utc))
        days, _ = one(HEADER + line(p="1", pub="2026-11-20T22:15:00Z"))
        self.assertEqual(days[0].published_at, datetime(2026, 11, 20, 22, 15, tzinfo=timezone.utc))
        _, refused = one(HEADER + line(p="1", pub="2026-11-20T22:15:00"))
        self.assertIn("timezone", refused[0][1])
        _, refused = one(HEADER + line(p="1", pub="2026-11-19T22:15:00Z"))
        self.assertIn("precedes", refused[0][1])

    def test_t7_derived(self):
        days, _ = one(GOOD)
        p = fw.rows(days[0], RECEIVED)[0]["payload"]
        self.assertEqual((p["p_cut"], p["p_hold"], p["p_hike"]), (0.2, 0.7, 0.1))
        self.assertAlmostEqual(p["expected_mid_bp"], 0.2 * 412.5 + 0.7 * 437.5 + 0.1 * 462.5)
        days, _ = one(HEADER + line(p="1", clo="", chi=""))
        q = fw.rows(days[0], RECEIVED)[0]["payload"]
        self.assertEqual((q["p_hike"], q["current_range"]), (None, None))

    def test_good_day_kept_when_another_refused(self):
        days, refused = one(GOOD + line(trade="2026-11-21", p="0.3"))
        self.assertEqual(([d.trade_date for d in days], [t for t, _ in refused]),
                         ([date(2026, 11, 20)], ["2026-11-21"]))

    def test_missing_columns(self):
        with self.assertRaises(fw.FedWatchError):
            fw.read_csv("trade_date,meeting_date,probability\n2026-11-20,2026-12-16,1\n")


class Store(unittest.TestCase):
    def test_t8_correction_kept_as_new_version(self):
        days1, _ = one(GOOD)
        corrected = GOOD.replace(",0.7,", ",0.6,", 1).replace(",450,475,0.1,", ",450,475,0.2,", 1)
        days2, refused = one(corrected)
        self.assertEqual(refused, [])
        later = datetime(2026, 11, 25, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st:
            st.append_many(fw.rows(days1[0], RECEIVED))
            st.append_many(fw.rows(days2[0], later))
            self.assertEqual(len(st.history("cme-fedwatch", "2026-12-16@2026-11-20")), 2)
            old = st.as_of("2026-11-24T23:00:00Z", source_id="cme-fedwatch")[0]
            new = st.as_of("2026-11-25T01:00:00Z", source_id="cme-fedwatch")[0]
        self.assertEqual(old.payload["p_hold"], 0.7)
        self.assertEqual(new.payload["p_hold"], 0.6)


class Collector(unittest.TestCase):
    def test_t10_owner_file(self):
        from tools.didm import collect_daily as cd
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st, \
                mock.patch("builtins.print") as pr:
            f = Path(tmp) / "fedwatch.csv"
            f.write_text("﻿" + GOOD + line(trade="2026-11-21", p="0.3"), encoding="utf-8")
            out = cd.collect_fedwatch_file(st, str(f))
            again = cd.collect_fedwatch_file(st, str(f))
        self.assertEqual((out["days"], out["rows"], out["refused"], out["added"]), (1, 2, 1, 2))
        self.assertEqual(again["refused"], 1)
        lines = [c.args[0] for c in pr.call_args_list]
        self.assertIn("trade days 1 (2026-11-20..2026-11-20), meeting rows 2, refused days 1", lines[0])
        self.assertTrue(lines[1].startswith("FedWatch refused 2026-11-21:"))


if __name__ == "__main__":
    unittest.main()
