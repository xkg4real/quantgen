"""DS-5b/2: sources whose terms keep them out of research samples. Offline."""
from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from core.didm.ingest import news_store, terms
from core.didm.store import PointInTimeStore
from tools.didm import collect_daily as cd
from tools.didm import collection_status as cs

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("docs/didm/OWNER_FIRST_RUN_2026-11-24.md", "docs/didm/NEW_SOURCES_PLAN_2026-11-24.md",
        "docs/didm/COLLECTION_STATUS_GUIDE_2026-11-24.md")


class List(unittest.TestCase):
    def test_news_sources_on_the_list(self):
        self.assertTrue(terms.is_research_excluded(news_store.SOURCE_ALPACA))
        self.assertTrue(terms.is_research_excluded(news_store.SOURCE_MASSIVE))
        for allowed in ("gdelt-gkg2", "gdelt-events2", "sec-edgar", "opendart", "alfred", "ecos", "kalshi"):
            self.assertFalse(terms.is_research_excluded(allowed), allowed)

    def test_documents_carry_the_same_list(self):
        for doc in DOCS:
            with self.subTest(doc=doc):
                text = (ROOT / doc).read_text(encoding="utf-8")
                lines = [l for l in text.splitlines() if terms.DOC_LINE_PREFIX in l]
                self.assertTrue(lines, f"{doc} has no '{terms.DOC_LINE_PREFIX}' line")
                for line in lines:
                    ids = set(re.findall(r"`([a-z0-9-]+)`", line.split(terms.DOC_LINE_PREFIX, 1)[1].split("—")[0]))
                    self.assertEqual(ids, terms.excluded_sources(), line)
                    self.assertIn(terms.NOTICE, line)

    def test_research_rows_filter(self):
        rows = [{"source_id": "alpaca-news"}, {"source_id": "sec-edgar"}, SimpleNamespace(source_id="massive-news"),
                SimpleNamespace(source_id="gdelt-gkg2"), {"no": "source"}]
        kept = terms.research_rows(rows)
        self.assertEqual([terms._source(r) for r in kept], ["sec-edgar", "gdelt-gkg2"])


class Collector(unittest.TestCase):
    def test_names_required(self):
        for flag in ("--alpaca-news", "--massive-news"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as tmp, \
                    redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cd.main(["--data-dir", tmp, "--no-gdelt", flag])

    def test_notice_printed_when_run(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cd, "collect_alpaca_news") as a, \
                mock.patch.object(cd, "collect_massive_news") as m:
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cd.main(["--data-dir", tmp, "--no-gdelt", "--alpaca-news", "AAPL",
                                          "--massive-news", "AAPL"]), 0)
        self.assertIn(terms.NOTICE, out.getvalue())
        a.assert_called_once()
        self.assertEqual(m.call_args.args[1], "AAPL")

    def test_not_in_default_run(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cd, "collect_alpaca_news") as a, \
                mock.patch.object(cd, "collect_massive_news") as m, mock.patch.object(cd, "collect_gdelt",
                                                                                    return_value=(0, [])):
            out = io.StringIO()
            with redirect_stdout(out):
                cd.main(["--data-dir", tmp])
        a.assert_not_called()
        m.assert_not_called()
        self.assertNotIn(terms.NOTICE, out.getvalue())


class Status(unittest.TestCase):
    def test_rows_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            with PointInTimeStore(Path(tmp) / cs.STORE_FILE) as st:
                for src, payload in (("massive-news", {"tickers": ["AAPL"]}), ("sec-edgar", {"cik": "1"})):
                    st.append(source_id=src, item_id="x", kind="news" if "news" in src else "filing",
                              published_at="2024-01-01T00:00:00Z", received_at="2026-11-24T00:00:00Z", payload=payload)
            text, js = io.StringIO(), io.StringIO()
            with redirect_stdout(text):
                cs.main(["--data-dir", tmp, "--by-entity"])
            with redirect_stdout(js):
                cs.main(["--data-dir", tmp, "--by-entity", "--json"])
        lines = text.getvalue().splitlines()
        self.assertTrue(any(l.startswith("massive-news") and "[EXCLUDED from research" in l for l in lines))
        self.assertFalse(any(l.startswith("sec-edgar") and "EXCLUDED" in l for l in lines))
        self.assertTrue(any(l.startswith("by entity massive-news") and "[EXCLUDED from research]" in l for l in lines))
        data = json.loads(js.getvalue())
        flags = {s["source_id"]: s["research_excluded"] for s in data["sources"]}
        self.assertEqual(flags, {"massive-news": True, "sec-edgar": False})
        self.assertEqual({g["source_id"]: g["research_excluded"] for g in data["by_entity"]},
                         {"massive-news": True, "sec-edgar": False})


if __name__ == "__main__":
    unittest.main()
