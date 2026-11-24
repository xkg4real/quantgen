"""D4: tools.didm.collection_status reads a synthetic store read-only and prints counts and dates only."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
