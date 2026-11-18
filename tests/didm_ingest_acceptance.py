"""DS-4a: GDELT and ALFRED assembly from fixtures, through injected fetchers. No network."""
from __future__ import annotations

import ast
import hashlib
import io
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from core.didm.ingest import alfred, gdelt
from core.didm.store import PointInTimeStore

ROOT = Path(__file__).resolve().parents[1]
RECEIVED = datetime(2026, 11, 5, 19, 16, tzinfo=timezone.utc)


def events_line(event_id="1100000001"):
    cols = [""] * 61
    cols[0], cols[1], cols[7], cols[17] = event_id, "20261105", "USA", "CHN"
    cols[26], cols[27], cols[28], cols[29] = "0311", "031", "03", "1"
    cols[30], cols[31], cols[32], cols[33], cols[34] = "1.5", "4", "2", "4", "-2.25"
    cols[53], cols[59], cols[60] = "US", "20261105190000", "https://example.com/a"
    return "\t".join(cols)


def gkg_line(record_id="20261105190000-1"):
    cols = [""] * 27
    cols[0], cols[1], cols[2], cols[3] = record_id, "20261105190000", "1", "example.com"
    cols[4], cols[7] = "https://example.com/b", "ECON_INTEREST_RATES;TAX_FNCACT_CENTRAL_BANK;"
    cols[11], cols[13] = "jerome powell;", "federal reserve;"
    cols[15] = "-3.5,1.2,4.7,5.9,20.1,0.5,412"
    cols[26] = "<PAGE_TITLE>Fed holds rates &amp; signals patience</PAGE_TITLE>"
    return "\t".join(cols)


def zipped(name, text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, text)
    return buf.getvalue()


class Gdelt(unittest.TestCase):
    def setUp(self):
        base = "http://data.gdeltproject.org/gdeltv2/"
        self.files = {
            base + "20261105190000.export.CSV.zip": zipped("20261105190000.export.CSV", events_line() + "\n"),
            base + "20261105190000.gkg.csv.zip": zipped("20261105190000.gkg.csv", gkg_line() + "\n"),
            base + "20261105190000.mentions.CSV.zip": zipped("m.CSV", "x\n"),
        }
        self.lastupdate = "\n".join(
            f"{len(b)} {hashlib.md5(b).hexdigest()} {u}" for u, b in self.files.items())  # noqa: S324
        self.calls = []

    def fetch_text(self, url):
        self.calls.append(url)
        return self.lastupdate

    def fetch_bytes(self, url):
        self.calls.append(url)
        return self.files[url]

    def test_ingest_latest(self):
        rows, refs = gdelt.ingest_latest(self.fetch_text, self.fetch_bytes, "LU", RECEIVED)
        self.assertEqual(sorted(r.kind for r in refs), ["events", "gkg"])
        self.assertNotIn("http://data.gdeltproject.org/gdeltv2/20261105190000.mentions.CSV.zip", self.calls)
        ev = next(r for r in rows if r["kind"] == "gdelt_event")
        self.assertEqual(ev["payload"]["event_root_code"], "03")
        self.assertEqual(ev["payload"]["avg_tone"], -2.25)
        gk = next(r for r in rows if r["kind"] == "gdelt_gkg")
        self.assertEqual(gk["payload"]["tone"], -3.5)
        self.assertEqual(gk["payload"]["word_count"], 412)
        self.assertEqual(gk["payload"]["page_title"], "Fed holds rates & signals patience")
        for r in rows:
            self.assertEqual(r["published_at"], datetime(2026, 11, 5, 19, 0, tzinfo=timezone.utc))
            self.assertEqual(r["received_at"], RECEIVED)

    def test_md5_mismatch_rejected(self):
        url = next(iter(self.files))
        blob = bytearray(self.files[url])
        blob[10] ^= 0xFF
        self.files[url] = bytes(blob)
        with self.assertRaises(gdelt.GdeltError):
            gdelt.ingest_latest(self.fetch_text, self.fetch_bytes, "LU", RECEIVED)

    def test_wrong_width_rejected(self):
        with self.assertRaises(gdelt.GdeltError):
            gdelt.parse_gkg("a\tb\tc\n", RECEIVED)

    def test_naive_received_rejected(self):
        with self.assertRaises(gdelt.GdeltError):
            gdelt.ingest_latest(self.fetch_text, self.fetch_bytes, "LU", datetime(2026, 11, 5))

    def test_into_store_as_of(self):
        rows, _ = gdelt.ingest_latest(self.fetch_text, self.fetch_bytes, "LU", RECEIVED)
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st:
            self.assertEqual(st.append_many(rows), 2)
            self.assertEqual(st.append_many(rows), 0)
            a = st.as_of("2026-11-05T20:00:00Z")
            self.assertEqual(a, st.as_of("2026-11-05T20:00:00Z"))
            self.assertEqual(len(a), 2)
            self.assertEqual(st.as_of("2026-11-05T19:15:00Z"), [])

    def test_attribution(self):
        self.assertIn("GDELT Project", gdelt.ATTRIBUTION)
        self.assertIn("https://www.gdeltproject.org/", gdelt.ATTRIBUTION)


class GdeltStamps(unittest.TestCase):
    def test_day_has_96_stamps(self):
        from datetime import date
        st = gdelt.stamps_for_day(date(2026, 11, 18))
        self.assertEqual(len(st), 96)
        self.assertEqual((st[0], st[-1]), ("20261118000000", "20261118234500"))
        self.assertEqual(gdelt.previous_stamp("20261118000000"), "20261117234500")

    def test_ingest_stamps_skips_unpublished(self):
        good = zipped("x.export.CSV", events_line() + "\n")
        def fetch(url):
            return good if "20261118000000" in url else None
        rows, fetched, missing = gdelt.ingest_stamps(fetch, ["20261118000000", "20261118001500"], RECEIVED)
        self.assertEqual(fetched, ["20261118000000.export.CSV.zip"])
        self.assertEqual(missing, ["20261118001500.export.CSV.zip"])
        self.assertFalse(rows[0]["payload"]["md5_verified"])

    def test_crc_error_rejected(self):
        blob = bytearray(zipped("x.export.CSV", events_line() * 50 + "\n"))
        blob[40] ^= 0xFF
        with self.assertRaises(Exception):
            gdelt.ingest_stamps(lambda u: bytes(blob), ["20261118000000"], RECEIVED)


class Alfred(unittest.TestCase):
    API = {"observations": [
        {"realtime_start": "2026-10-15", "realtime_end": "2026-11-12", "date": "2026-09-01", "value": "100.0"},
        {"realtime_start": "2026-11-13", "realtime_end": "9999-12-31", "date": "2026-09-01", "value": "100.4"},
        {"realtime_start": "2026-11-13", "realtime_end": "9999-12-31", "date": "2026-10-01", "value": "."},
    ]}

    def test_api_rows(self):
        rows = alfred.rows_from_api("CPIAUCSL", self.API, RECEIVED)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["item_id"], "CPIAUCSL:2026-09-01:2026-10-15")
        self.assertIsNone(rows[2]["payload"]["value"])
        self.assertEqual(alfred.value_as_known_on(rows, "2026-09-01", "2026-11-01"), 100.0)
        self.assertEqual(alfred.value_as_known_on(rows, "2026-09-01", "2026-11-14"), 100.4)
        self.assertIsNone(alfred.value_as_known_on(rows, "2026-09-01", "2026-10-01"))

    def test_manual_rows_match_api(self):
        manual = [(datetime(2026, 9, 1), 100.0, datetime(2026, 10, 15), datetime(2026, 11, 12)),
                  (None, None, None, None)]
        rows = alfred.rows_from_manual("CPIAUCSL", manual, RECEIVED)
        self.assertEqual(rows[0]["item_id"], alfred.rows_from_api("CPIAUCSL", self.API, RECEIVED)[0]["item_id"])
        self.assertEqual(len(rows), 1)

    def test_bad_inputs(self):
        with self.assertRaises(alfred.AlfredError):
            alfred.rows_from_api("bad id!", self.API, RECEIVED)
        with self.assertRaises(alfred.AlfredError):
            alfred.rows_from_api("CPIAUCSL", {}, RECEIVED)
        with self.assertRaises(alfred.AlfredError):
            alfred.rows_from_api("CPIAUCSL", self.API, datetime(2026, 11, 5))

    def test_into_store(self):
        rows = alfred.rows_from_api("CPIAUCSL", self.API, RECEIVED)
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st:
            st.append_many(rows)
            got = st.as_of("2026-11-06T00:00:00Z", kind="alfred_vintage")
            self.assertEqual(len(got), 3)
            self.assertTrue(all(i.published_at and i.received_at for i in got))


class Boundaries(unittest.TestCase):
    NETWORK = {"requests", "urllib", "urllib3", "http", "socket", "httpx", "aiohttp", "data"}

    def test_core_didm_has_no_network_or_vendor_imports(self):
        for path in sorted((ROOT / "core" / "didm").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for n in names:
                    self.assertNotIn(n.split(".")[0], self.NETWORK, f"{path}: imports {n}")

    def test_polymarket_held(self):
        from data.didm import polymarket
        self.assertFalse(polymarket.ENABLED)
        with self.assertRaises(polymarket.ConnectorHeld):
            polymarket.fetch_market_history("x")


if __name__ == "__main__":
    unittest.main()
