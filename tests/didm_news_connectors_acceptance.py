"""DS-5b/5c: Alpaca News and Massive news HTTP clients, store rows and collector paging. No network."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.didm.ingest import alpaca_news, news_store
from core.didm.store import PointInTimeStore
from data.didm import alpaca_news as alpaca_http
from data.didm import keys
from data.didm import massive_news as massive
from tests.didm_alpaca_news_acceptance import supplied
from tests.didm_massive_news_acceptance import ARTICLE, page

ENV = {"ALPACA_API_KEY_ID": "AKID123", "ALPACA_API_SECRET_KEY": "SECRET456", "MASSIVE_API_KEY": "MKEY789"}


def response(status=200, body=None):
    r = mock.Mock(status_code=status)
    r.json.return_value = body if body is not None else {}
    return r


class AlpacaClient(unittest.TestCase):
    def test_keys_in_headers_not_url(self):
        with mock.patch.dict(os.environ, ENV), mock.patch("data.net.session.get",
                                                         return_value=response(body={"news": [], "next_page_token": None})) as get:
            alpaca_http.fetch_page(["AAPL"], start="2015-01-01", limit=50, page_token="tok")
        url, kw = get.call_args.args[0], get.call_args.kwargs
        self.assertEqual(url, alpaca_http.NEWS_URL)
        self.assertEqual(kw["headers"], {"APCA-API-KEY-ID": "AKID123", "APCA-API-SECRET-KEY": "SECRET456"})
        self.assertEqual(kw["params"]["include_content"], "false")
        self.assertEqual((kw["params"]["symbols"], kw["params"]["page_token"], kw["params"]["sort"]), ("AAPL", "tok", "asc"))
        self.assertNotIn("SECRET456", repr(kw["params"]))

    def test_refusal_message_masked(self):
        body = {"message": "subscription does not permit querying news for AKID123"}
        with mock.patch.dict(os.environ, ENV), mock.patch("data.net.session.get", return_value=response(403, body)):
            with self.assertRaises(keys.SourceError) as cm:
                alpaca_http.fetch_page(["AAPL"])
        self.assertIn("HTTP 403", str(cm.exception))
        self.assertIn("does not permit querying news", str(cm.exception))
        self.assertNotIn("AKID123", str(cm.exception))

    def test_missing_keys(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(keys, "in_store", return_value=False):
            with self.assertRaises(keys.MissingKey):
                alpaca_http.fetch_page(["AAPL"])

    def test_bounds(self):
        with mock.patch.dict(os.environ, ENV):
            for bad in ({"limit": 0}, {"limit": 51}):
                with self.assertRaises(ValueError):
                    alpaca_http.fetch_page(["AAPL"], **bad)
            with self.assertRaises(ValueError):
                alpaca_http.fetch_page(["aapl;drop"])


class KeyNames(unittest.TestCase):
    def test_env_only_names_read_from_environment(self):
        self.assertFalse(set(keys.ENV_ONLY_KEYS) & set(keys.RESEARCH_KEYS))
        with mock.patch.dict(os.environ, ENV):
            for name in keys.ENV_ONLY_KEYS:
                if not keys.in_store(name):
                    st = keys.key_status(name)
                    self.assertEqual((st["present"], st["source"]), (True, "env"))
                    self.assertNotIn(ENV[name], repr(st))


class MassiveClient(unittest.TestCase):
    def setUp(self):
        massive._last_call[0] = 0.0

    def test_bearer_header_and_spacing(self):
        sleeps, now = [], [100.0]
        with mock.patch.dict(os.environ, ENV), mock.patch("data.net.session.get",
                                                         return_value=response(body=page())) as get:
            massive.fetch_page("AAPL", published_gte="2024-01-01", sleep=sleeps.append, clock=lambda: now[0])
            now[0] = 103.0
            massive.fetch_page("AAPL", cursor="c1", sleep=sleeps.append, clock=lambda: now[0])
        kw = get.call_args.kwargs
        self.assertEqual(kw["headers"], {"Authorization": "Bearer MKEY789"})
        self.assertNotIn("apiKey", kw["params"])
        self.assertEqual(kw["params"]["cursor"], "c1")
        self.assertEqual(sleeps, [massive.MIN_INTERVAL_S - 3.0])

    def test_refusal_masked(self):
        with mock.patch.dict(os.environ, ENV), mock.patch("data.net.session.get",
                                                         return_value=response(403, {"message": "plan lacks news MKEY789"})):
            with self.assertRaises(keys.SourceError) as cm:
                massive.fetch_page("AAPL", sleep=lambda s: None)
        self.assertIn("HTTP 403", str(cm.exception))
        self.assertNotIn("MKEY789", str(cm.exception))


class ConnectionOnly(unittest.TestCase):
    def test_cli_uses_single_request_transport_and_leaves_existing_store_untouched(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from tools.didm import collect_daily as cd
        replies = [response(body={"news": [], "next_page_token": "keep-private"}),
                   response(body={"results": [], "next_url": "https://example.invalid/next"})]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, ENV), \
                mock.patch.object(massive, "_last_call", [0.0]), \
                mock.patch("requests.get", side_effect=replies) as get, \
                mock.patch("data.net.session.get", side_effect=AssertionError("unexpected retrying transport")):
            path = Path(tmp) / "didm_store.sqlite"
            with PointInTimeStore(path) as store:
                store.append(source_id="alpaca-news", item_id="prior", kind="news",
                             published_at="2024-01-01T00:00:00Z", received_at="2024-01-02T00:00:00Z",
                             payload={"fixture": "preexisting"})
            before = path.read_bytes()
            with redirect_stdout(StringIO()):
                self.assertEqual(cd.main(["--data-dir", tmp, "--no-gdelt", "--alpaca-news", "AAPL",
                                          "--massive-news", "AAPL", "--news-max-pages", "50"]), 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([c.args[0] for c in get.call_args_list], [alpaca_http.NEWS_URL, massive.NEWS_URL])
            for call in get.call_args_list:
                self.assertEqual(call.kwargs["params"]["limit"], 1)
                self.assertIs(call.kwargs["allow_redirects"], False)


class StoreRows(unittest.TestCase):
    def test_alpaca_rows_and_revisions(self):
        from datetime import datetime, timezone
        got = []
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st:
            for upd, rec in (("2026-11-23T00:00:00Z", datetime(2026, 11, 23, 1, tzinfo=timezone.utc)),
                             ("2026-11-23T02:00:00Z", datetime(2026, 11, 23, 3, tzinfo=timezone.utc))):
                art = alpaca_news.parse_article(supplied(updated_at=upd), rec)
                rows = news_store.alpaca_rows([art])
                got.append(rows[0])
                st.append_many(rows)
            self.assertEqual(len(st.history("alpaca-news", "0")), 2)
            self.assertEqual(st.as_of("2026-11-23T02:00:00Z")[0].payload["updated_at_raw"], "2026-11-23T00:00:00Z")
        payload = got[0]["payload"]
        self.assertNotIn("summary", payload)
        self.assertNotIn("content", payload)
        self.assertEqual(got[0]["published_at"].isoformat(), "2026-11-22T23:00:00+00:00")

    def test_massive_rows_insights(self):
        from datetime import datetime, timezone
        row = dict(ARTICLE, insights=[{"ticker": "QGA", "sentiment": "positive", "sentiment_reasoning": "x"}])
        parsed = massive.parse_page(page(row, ARTICLE), datetime(2024, 4, 5, 12, tzinfo=timezone.utc))
        rows = news_store.massive_rows(parsed.articles)
        self.assertEqual(rows[0]["payload"]["insights"], [{"ticker": "QGA", "sentiment": "positive"}])
        self.assertTrue(rows[0]["payload"]["has_insights"])
        self.assertFalse(rows[1]["payload"]["has_insights"])


class CollectorPaging(unittest.TestCase):
    def test_replay_requires_explicit_fetch(self):
        from tools.didm import collect_daily as cd
        for fn, args in ((cd.collect_alpaca_news, (None, ["TEST"], None, None, 1)),
                         (cd.collect_massive_news, (None, "TEST", None, 1))):
            with self.subTest(function=fn.__name__), self.assertRaises(TypeError):
                fn(*args)

    def test_alpaca_follows_tokens_to_the_end(self):
        from tools.didm import collect_daily as cd
        pages = {None: {"news": [supplied(id=1)], "next_page_token": "t1"},
                 "t1": {"news": [supplied(id=2)], "next_page_token": None}}
        calls = []

        def fetch(symbols, *, start, end, limit, page_token):
            calls.append(page_token)
            return pages[page_token]
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st, \
                mock.patch("builtins.print"):
            out = cd.collect_alpaca_news(st, ["TEST"], "2026-11-01", None, 2, fetch)
        self.assertEqual(calls, [None, "t1"])
        self.assertEqual((out["pages"], out["articles"], out["added"]), (2, 2, 2))

    def test_alpaca_page_cap(self):
        from tools.didm import collect_daily as cd

        def fetch(symbols, *, start, end, limit, page_token):
            n = int(page_token[1:]) + 1 if page_token else 1
            return {"news": [supplied(id=n)], "next_page_token": f"t{n}"}
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st, \
                mock.patch("builtins.print") as pr:
            out = cd.collect_alpaca_news(st, [], None, None, max_pages=3, fetch=fetch)
        self.assertEqual(out["pages"], 3)
        self.assertIn("complete False", pr.call_args.args[0])

    def test_massive_follows_cursor(self):
        from tools.didm import collect_daily as cd
        second = dict(ARTICLE, id="fixture-2")
        pages = {None: page(ARTICLE, next_url="https://api.massive.com/v2/reference/news?cursor=c1"),
                 "c1": page(second)}
        calls = []

        def fetch(ticker, *, published_gte, cursor):
            calls.append(cursor)
            return pages[cursor]
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st, \
                mock.patch("builtins.print") as pr:
            out = cd.collect_massive_news(st, "QGA", "2024-01-01", 5, fetch)
        self.assertEqual(calls, [None, "c1"])
        self.assertEqual((out["articles"], out["added"]), (2, 2))
        self.assertIn("complete True", pr.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
