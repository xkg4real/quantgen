"""D4: tools.didm.collection_status reads a synthetic store read-only and prints counts and dates only."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from datetime import date
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from core.didm.store import PointInTimeStore
from tools.didm import collection_status as cs

TITLE = "PAYLOAD-TEXT-MUST-NOT-PRINT"


def build(folder: Path) -> Path:
    path = folder / cs.STORE_FILE
    with PointInTimeStore(path) as st:
        for day in ("2026-11-17", "2026-11-18", "2026-11-20"):            # 11-19 missing
            st.append(source_id="gdelt-gkg2", item_id=f"g{day}", kind="gdelt_gkg",
                      published_at=f"{day}T10:00:00Z", received_at=f"{day}T10:05:00Z", payload={"title": TITLE})
        for year, obs in ((2015, "2015-01-01"), (2015, "2015-02-01"), (2020, "2020-03-01")):
            for rec in ("2026-11-18T00:00:00Z", "2026-11-20T00:00:00Z"):    # same item fetched twice
                st.append(source_id="alfred", item_id=f"CPI:{obs}", kind="alfred_vintage",
                          published_at=obs + "T00:00:00Z", received_at=rec, valid_at=obs + "T00:00:00Z",
                          payload={"value": year, "rec": rec})
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Summary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.path = build(self.dir)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cs.main(["--data-dir", str(self.dir), *args])
        return code, out.getvalue(), err.getvalue()

    def by_source(self, summary):
        return {s["source_id"]: s for s in summary["sources"]}

    def test_counts_spans_gaps(self):
        db = cs.open_read_only(self.path)
        try:
            s = self.by_source(cs.summarize(db))
        finally:
            db.close()
        g, a = s["gdelt-gkg2"], s["alfred"]
        self.assertEqual((g["items"], g["versions"], g["receive_days"]), (3, 3, 3))
        self.assertEqual((g["missing_receive_days"], g["missing_examples"]), (1, ["2026-11-19"]))
        self.assertEqual((a["items"], a["versions"]), (3, 6))
        self.assertEqual((a["valid_from"], a["valid_to"]), ("2015-01-01", "2020-03-01"))
        self.assertEqual((a["missing_receive_days"], a["missing_examples"]), (1, ["2026-11-19"]))
        self.assertEqual(a["sample_years"]["2015"], 2)
        self.assertEqual(a["sample_years"]["2020"], 1)
        self.assertEqual(a["sample_years"]["2024"], 0)
        self.assertEqual(sum(g["sample_years"].values()), 0)

    def test_since_limits_gap_window(self):
        db = cs.open_read_only(self.path)
        try:
            s = self.by_source(cs.summarize(db, since=cs.date(2026, 11, 20)))
        finally:
            db.close()
        self.assertEqual(s["gdelt-gkg2"]["missing_receive_days"], 0)

    def test_cli_text_has_no_payload_and_store_unchanged(self):
        before = digest(self.path)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("gdelt-gkg2 / gdelt_gkg: items 3 (versions 3)", out)
        self.assertIn("missing 1 days (e.g. 2026-11-19)", out)
        self.assertIn("sample years with data 2/10", out)
        self.assertNotIn(TITLE, out)
        self.assertEqual(digest(self.path), before)

    def test_cli_json(self):
        code, out, _ = self.run_cli("--json", "--sample", "2019", "2020")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(self.by_source(data)["alfred"]["sample_years"], {"2019": 0, "2020": 1})
        self.assertNotIn(TITLE, out)

    def test_read_only_connection_refuses_writes(self):
        db = cs.open_read_only(self.path)
        try:
            with self.assertRaises(cs.sqlite3.OperationalError):
                db.execute("DELETE FROM items")
        finally:
            db.close()

    def test_missing_store_is_not_created(self):
        with tempfile.TemporaryDirectory() as empty:
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = cs.main(["--data-dir", empty])
            self.assertEqual(code, 1)
            self.assertIn("no store", err.getvalue())
            self.assertEqual(list(Path(empty).iterdir()), [])

    def test_empty_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            PointInTimeStore(Path(tmp) / cs.STORE_FILE).close()
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cs.main(["--data-dir", tmp]), 0)
            self.assertEqual(out.getvalue().strip(), "store is empty")


class ByEntity(unittest.TestCase):
    """D13: items per company/series identifier, identifiers only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        with PointInTimeStore(self.dir / cs.STORE_FILE) as st:
            for i, (cik, day) in enumerate((("320193", "2015-03-01"), ("320193", "2017-03-01"),
                                            ("320193", "2019-03-01"), ("1000", "2020-06-01"))):
                st.append(source_id="sec-edgar", item_id=f"acc{i}", kind="filing", published_at=day + "T12:00:00Z",
                          received_at="2026-11-24T00:00:00Z", payload={"cik": cik, "company": TITLE})
            # a correction of acc3 moves it to another cik: only the latest version counts
            st.append(source_id="sec-edgar", item_id="acc3", kind="filing", published_at="2020-06-01T12:00:00Z",
                      received_at="2026-11-25T00:00:00Z", payload={"cik": "2000", "company": TITLE})
            st.append(source_id="alpaca-news", item_id="n1", kind="news", published_at="2024-01-02T00:00:00Z",
                      received_at="2026-11-24T00:00:00Z", payload={"symbols": ["AAPL", "MSFT"], "headline": TITLE})
            st.append(source_id="alpaca-news", item_id="n2", kind="news", published_at="2024-01-03T00:00:00Z",
                      received_at="2026-11-24T00:00:00Z", payload={"symbols": [], "headline": TITLE})
            st.append(source_id="gdelt-gkg2", item_id="g1", kind="gdelt_gkg", published_at="2024-01-03T00:00:00Z",
                      received_at="2026-11-24T00:00:00Z", payload={"title": TITLE})

    def run_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cs.main(["--data-dir", str(self.dir), *args]), 0)
        return out.getvalue()

    def test_counts_latest_version_and_multi_tags(self):
        db = cs.open_read_only(self.dir / cs.STORE_FILE)
        try:
            groups = {g["source_id"]: g for g in cs.by_entity(db)}
        finally:
            db.close()
        self.assertNotIn("gdelt-gkg2", groups)
        edgar = groups["sec-edgar"]
        per = {e["entity"]: e for e in edgar["per_entity"]}
        self.assertEqual({k: v["items"] for k, v in per.items()}, {"320193": 3, "2000": 1})
        self.assertEqual((per["320193"]["first"], per["320193"]["last"]), ("2015-03-01", "2019-03-01"))
        self.assertAlmostEqual(per["320193"]["items_per_year"], round(3 / ((date(2019, 3, 1) - date(2015, 3, 1)).days / 365.25), 3))
        self.assertEqual(per["2000"]["items_per_year"], 1.0)          # one-day span counts as one year
        self.assertEqual(edgar["items_per_entity"], {"min": 1, "median": 2.0, "max": 3})
        news = groups["alpaca-news"]
        self.assertEqual((news["entities"], news["untagged_items"]), (2, 1))

    def test_text_and_json_hold_identifiers_only(self):
        text = self.run_cli("--by-entity")
        self.assertIn("by entity sec-edgar / filing: entities 2, untagged items 0, items per entity min 1 median 2 max 3",
                      text)
        self.assertIn("  320193: items 3, 2015-03-01..2019-03-01", text)
        data = json.loads(self.run_cli("--by-entity", "--json"))
        self.assertEqual({g["source_id"] for g in data["by_entity"]}, {"sec-edgar", "alpaca-news"})
        for out in (text, json.dumps(data)):
            self.assertNotIn(TITLE, out)

    def test_off_by_default(self):
        self.assertNotIn("by entity", self.run_cli())
        self.assertNotIn("by_entity", json.loads(self.run_cli("--json")))

    def test_long_list_trimmed_in_text(self):
        with PointInTimeStore(self.dir / cs.STORE_FILE) as st:
            for i in range(15):
                st.append(source_id="kalshi", item_id=f"k{i}", kind="kalshi_candle", published_at="2024-01-01T00:00:00Z",
                          received_at="2026-11-24T00:00:00Z", payload={"ticker": f"T{i:02d}"})
        text = self.run_cli("--by-entity")
        self.assertIn("(5 more in --json)", text)
        self.assertEqual(len(json.loads(self.run_cli("--by-entity", "--json"))["by_entity"][1]["per_entity"]), 15)


if __name__ == "__main__":
    unittest.main()
