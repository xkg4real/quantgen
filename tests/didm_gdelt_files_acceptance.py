"""DS-10: owner-downloaded GDELT 2.0 files and event-window selection. Synthetic files only. Offline."""
from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.didm.ingest import gdelt, gdelt_files as gf
from core.didm.store import PointInTimeStore
from tests.didm_ingest_acceptance import events_line, gkg_line, zipped

RECEIVED = datetime(2026, 11, 24, 12, tzinfo=timezone.utc)
STAMP = "20261105190000"
T = datetime(2026, 11, 5, 19, tzinfo=timezone.utc)


def gkg(record_id, orgs="", title=""):
    cols = gkg_line(record_id).split("\t")
    cols[13] = orgs
    cols[26] = f"<PAGE_TITLE>{title}</PAGE_TITLE>" if title else ""
    return "\t".join(cols)


class Reading(unittest.TestCase):
    def test_zip_and_plain(self):
        z = zipped(f"{STAMP}.gkg.csv", gkg_line() + "\n")
        rows = gf.read_file(f"{STAMP}.gkg.csv.zip", z, RECEIVED)
        plain = gf.read_file(f"{STAMP}.export.CSV", (events_line() + "\n").encode(), RECEIVED)
        self.assertEqual((rows[0]["source_id"], plain[0]["source_id"]), (gdelt.SOURCE_GKG, gdelt.SOURCE_EVENTS))
        p = rows[0]["payload"]
        self.assertEqual((p["citation"], p["file_stamp"], p["md5_verified"]), (gf.CITATION, STAMP, False))
        self.assertEqual(p["page_title"], "Fed holds rates & signals patience")
        self.assertEqual(gf.available_at(rows[0]), T)
        for key in ("body", "text", "content"):
            self.assertNotIn(key, p)

    def test_md5(self):
        z = zipped(f"{STAMP}.export.CSV", events_line() + "\n")
        rows = gf.read_file(f"{STAMP}.export.CSV.zip", z, RECEIVED, md5=hashlib.md5(z).hexdigest())  # noqa: S324
        self.assertTrue(rows[0]["payload"]["md5_verified"])
        with self.assertRaises(gdelt.GdeltError):
            gf.read_file(f"{STAMP}.export.CSV.zip", z, RECEIVED, md5="0" * 32)

    def test_names_refused(self):
        for name in (f"{STAMP}.mentions.CSV.zip", "lastupdate.txt", "2026110519.gkg.csv", f"{STAMP}.gkg.csv.zip.exe",
                     "../" + f"{STAMP}.gkg.csv"):
            with self.subTest(name=name), self.assertRaises(gdelt.GdeltError):
                gf.read_file(name, b"", RECEIVED)
        with self.assertRaises(gdelt.GdeltError):
            gf.read_file(f"{STAMP}.gkg.csv", gkg_line().encode(), datetime(2026, 11, 24))

    def test_bad_columns_refused(self):
        with self.assertRaises(gdelt.GdeltError):
            gf.read_file(f"{STAMP}.gkg.csv", b"a\tb\tc\n", RECEIVED)


class Selecting(unittest.TestCase):
    def setUp(self):
        text = "\n".join([gkg("r1", orgs="apple inc;federal reserve;", title="Apple beats estimates"),
                          gkg("r2", orgs="", title="Pineapple prices rise"),
                          gkg("r3", orgs="", title="Markets: APPLE   Inc. shares fall"),
                          gkg("r4", orgs="", title="Snapple Inc expands")]) + "\n"
        self.gkg = gf.read_file(f"{STAMP}.gkg.csv", text.encode(), RECEIVED)
        self.events = gf.read_file(f"{STAMP}.export.CSV", (events_line() + "\n").encode(), RECEIVED)
        self.aliases = {"Apple Inc": "ENT-1", "Federal Reserve": "MACRO-FED"}

    def test_alias_tags(self):
        got = {s.row["item_id"]: s.entity_ids for s in gf.select(self.gkg, T, T, aliases=self.aliases)}
        self.assertEqual(got, {"r1": ("ENT-1", "MACRO-FED"), "r2": (), "r3": ("ENT-1",), "r4": ()})
        kept = [s.row["item_id"] for s in gf.select(self.gkg, T, T, aliases=self.aliases, require_entity=True)]
        self.assertEqual(kept, ["r1", "r3"])                     # "Snapple Inc" is not "Apple Inc"

    def test_window(self):
        self.assertEqual(gf.select(self.gkg, T + timedelta(minutes=1), T + timedelta(hours=1)), [])
        self.assertEqual(len(gf.select(self.gkg, T - timedelta(days=1), T)), 4)
        with self.assertRaises(gdelt.GdeltError):
            gf.select(self.gkg, T, T - timedelta(seconds=1))
        with self.assertRaises(gdelt.GdeltError):
            gf.select(self.gkg, T, T, aliases={"ab": "X"})

    def test_events_by_country(self):
        self.assertEqual(len(gf.select(self.events, T, T, countries=["chn"])), 1)
        self.assertEqual(gf.select(self.events, T, T, countries=["KOR"]), [])
        self.assertEqual(gf.select(self.events, T, T, countries=["CHN"])[0].entity_ids, ())


class Collector(unittest.TestCase):
    def test_gdelt_file_option(self):
        from tools.didm import collect_daily as cd
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as data:
            f = Path(tmp) / f"{STAMP}.gkg.csv.zip"
            f.write_bytes(zipped(f"{STAMP}.gkg.csv", gkg_line() + "\n"))
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cd.main(["--data-dir", data, "--no-gdelt", "--gdelt-file", str(f)]), 0)
            with PointInTimeStore(Path(data) / "didm_store.sqlite") as st:
                rows = st.as_of("2100-01-01T00:00:00Z", source_id=gdelt.SOURCE_GKG)
        self.assertIn(f"GDELT file {STAMP}.gkg.csv.zip: rows 1, new 1", out.getvalue())
        self.assertIn(gdelt.ATTRIBUTION, out.getvalue())
        self.assertEqual(rows[0].payload["citation"], gf.CITATION)


if __name__ == "__main__":
    unittest.main()
