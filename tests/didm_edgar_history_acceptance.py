"""D6: EDGAR older submissions files (filings.files) for the 2015-2024 sample. No network."""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

from core.didm.ingest import filings
from core.didm.store import PointInTimeStore
from data.didm import edgar

RECEIVED = datetime(2026, 11, 24, 12, tzinfo=timezone.utc)
NAME1 = "CIK0000320193-submissions-001.json"
NAME2 = "CIK0000320193-submissions-002.json"


def cols(*filings_):
    keys = ("accessionNumber", "filingDate", "acceptanceDateTime", "form", "primaryDocument", "items")
    return {k: [f[i] for f in filings_] for i, k in enumerate(keys)}


SUBS = {
    "cik": "320193", "name": "Example Corp", "tickers": ["EXM"],
    "filings": {
        "recent": cols(("0000320193-25-000001", "2025-02-01", "2025-02-01T21:30:00.000Z", "8-K", "a.htm", "2.02")),
        "files": [
            {"name": NAME1, "filingCount": 3, "filingFrom": "2018-01-01", "filingTo": "2024-12-31"},
            {"name": NAME2, "filingCount": 1, "filingFrom": "2009-01-01", "filingTo": "2014-12-31"},
        ],
    },
}
FILE1 = cols(
    ("0000320193-24-000009", "2024-05-02", "2024-05-02T20:31:00.000Z", "10-Q", "q.htm", ""),
    ("0000320193-18-000002", "2018-02-01", "", "8-K", "b.htm", "9.01"),        # no acceptance time
    ("0000320193-18-000003", "2018-02-02", "2018-02-02T12:00:00.000Z", "4", "f.xml", ""),
)
FILE2 = cols(("0000320193-12-000001", "2012-01-01", "2012-01-01T12:00:00.000Z", "8-K", "c.htm", ""))


class HistoryParser(unittest.TestCase):
    def test_file_selection_by_range(self):
        got = filings.edgar_history_files(SUBS, date(2015, 1, 1), date(2024, 12, 31))
        self.assertEqual([f["name"] for f in got], [NAME1])
        self.assertEqual(len(filings.edgar_history_files(SUBS)), 2)

    def test_foreign_or_odd_names_refused(self):
        for name in ("CIK0000999999-submissions-001.json", "../x.json", "https://evil/x.json"):
            bad = {**SUBS, "filings": {**SUBS["filings"], "files": [{**SUBS["filings"]["files"][0], "name": name}]}}
            with self.assertRaises(filings.FilingError):
                filings.edgar_history_files(bad)

    def test_rows_and_date_precision_fallback(self):
        entry = filings.edgar_history_files(SUBS, date(2015, 1, 1))[0]
        rows = {r["item_id"]: r for r in filings.edgar_history_rows(SUBS, entry, FILE1, RECEIVED)}
        self.assertEqual(set(rows), {"0000320193-24-000009", "0000320193-18-000002"})   # form 4 filtered
        q = rows["0000320193-24-000009"]
        self.assertEqual(q["published_at"], datetime(2024, 5, 2, 20, 31, tzinfo=timezone.utc))
        self.assertEqual(q["payload"]["time_precision"], "second")
        self.assertEqual(q["payload"]["company"], "Example Corp")
        k = rows["0000320193-18-000002"]
        self.assertEqual(k["payload"]["time_precision"], "date")
        self.assertEqual(k["published_at"].astimezone(timezone.utc), datetime(2018, 2, 1, 5, tzinfo=timezone.utc))

    def test_count_mismatch_and_ragged_refused(self):
        entry = filings.edgar_history_files(SUBS, date(2015, 1, 1))[0]
        with self.assertRaises(filings.FilingError):
            filings.edgar_history_rows(SUBS, {**entry, "filing_count": 2}, FILE1, RECEIVED)
        with self.assertRaises(filings.FilingError):
            filings.edgar_history_rows(SUBS, entry, {**FILE1, "form": ["10-Q"]}, RECEIVED)
        with self.assertRaises(filings.FilingError):
            filings.edgar_history_rows(SUBS, {**entry, "filing_count": 1},
                                       cols(("x", "not-a-date", "", "8-K", "", "")), RECEIVED)

    def test_recent_unchanged(self):
        r = filings.edgar_rows(SUBS, RECEIVED)[0]
        self.assertEqual((r["item_id"], r["payload"]["time_precision"]), ("0000320193-25-000001", "second"))


class HistoryClient(unittest.TestCase):
    def test_name_checked_and_user_agent_header(self):
        with self.assertRaises(ValueError):
            edgar.fetch_history_file("../../etc/passwd")
        resp = mock.Mock(status_code=200)
        resp.json.return_value = FILE1
        with mock.patch.dict(os.environ, {"SEC_EDGAR_USER_AGENT": "Org ops@example.invalid"}), \
                mock.patch("data.net.session.get", return_value=resp) as get, mock.patch.object(edgar, "_throttle"):
            self.assertEqual(edgar.fetch_history_file(NAME1), FILE1)
        self.assertEqual(get.call_args.args[0], "https://data.sec.gov/submissions/" + NAME1)
        self.assertEqual(get.call_args.kwargs["headers"]["User-Agent"], "Org ops@example.invalid")


class Collector(unittest.TestCase):
    def run_collect(self, start, end, max_files=10):
        from tools.didm import collect_daily as cd
        asked = []

        def fetch_file(name):
            asked.append(name)
            return {NAME1: FILE1, NAME2: FILE2}[name]
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st, \
                mock.patch("builtins.print") as pr:
            out = cd.collect_edgar_history(st, ["320193"], start, end, max_files,
                                           fetch_submissions=lambda cik: SUBS, fetch_file=fetch_file)
            stored = sorted(i.item_id for i in st.as_of("2100-01-01T00:00:00Z", source_id="sec-edgar"))
        return out[0], asked, stored, pr.call_args.args[0]

    def test_sample_window(self):
        out, asked, stored, line = self.run_collect("2015-01-01", "2024-12-31")
        self.assertEqual(asked, [NAME1])
        self.assertEqual(stored, ["0000320193-18-000002", "0000320193-24-000009"])   # 2025 recent row outside
        self.assertIn("files 1/1 (complete True)", line)
        self.assertIn("first 2018-02-01, last 2024-05-02", line)

    def test_file_cap_reports_incomplete(self):
        out, asked, stored, line = self.run_collect(None, None, max_files=1)
        self.assertEqual((out["files"], out["read"]), (2, 1))
        self.assertIn("complete False", line)
        self.assertIn("0000320193-25-000001", stored)

    def test_reversed_range_refused(self):
        with self.assertRaises(SystemExit):
            self.run_collect("2024-01-01", "2015-01-01")


if __name__ == "__main__":
    unittest.main()
