"""DS-4b news feeds (Alpha Vantage, Tiingo, CryptoPanic) and the DIDM key lookup. No network."""
from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from unittest import mock

from core.didm.ingest import news
from data.didm import keys

RECEIVED = datetime(2026, 11, 19, 6, 0, tzinfo=timezone.utc)

AV = {"items": "1", "feed": [{
    "title": "Fed holds", "url": "https://example.com/a", "time_published": "20261118T190000",
    "source": "Example", "summary": "not stored",
    "topics": [{"topic": "Economy - Monetary", "relevance_score": "0.99"}],
    "overall_sentiment_score": -0.21, "overall_sentiment_label": "Somewhat-Bearish",
    "ticker_sentiment": [{"ticker": "SPY", "relevance_score": "0.81", "ticker_sentiment_score": "-0.30",
                          "ticker_sentiment_label": "Somewhat-Bearish"}],
}]}
TIINGO = [{"id": 101, "title": "Chip maker beats", "url": "https://example.com/t", "description": "not stored",
           "publishedDate": "2026-11-18T13:00:00Z", "crawlDate": "2026-11-18T13:05:00Z",
           "source": "example.com", "tickers": ["nvda"], "tags": ["Earnings"]},
          {"id": 102, "title": "Old story", "url": "https://example.com/o",
           "publishedDate": "2026-10-01T00:00:00Z", "crawlDate": "2026-11-18T00:00:00Z", "tickers": []}]
CP = {"results": [{"id": 9, "title": "ETF inflows", "url": "https://example.com/c", "kind": "news",
                   "published_at": "2026-11-18T12:00:00Z", "source": {"domain": "example.com"},
                   "currencies": [{"code": "BTC"}], "votes": {"positive": 6, "negative": 2, "important": 1}},
                  {"id": 10, "title": "No votes", "published_at": "2026-11-18T12:30:00Z"}]}


class AlphaVantage(unittest.TestCase):
    def test_rows(self):
        r = news.alphavantage_rows(AV, RECEIVED)[0]
        self.assertEqual(r["published_at"], datetime(2026, 11, 18, 19, tzinfo=timezone.utc))
        self.assertTrue(r["payload"]["has_relevance_field"])
        self.assertEqual(r["payload"]["tickers"][0]["relevance_score"], 0.81)
        self.assertNotIn("summary", r["payload"])
        self.assertEqual(r["payload"]["tz_assumed"], "UTC")

    def test_rate_limit_reply(self):
        with self.assertRaises(news.NewsError) as cm:
            news.alphavantage_rows({"Information": "limit text"}, RECEIVED)
        self.assertIn("Information", str(cm.exception))
        self.assertNotIn("limit text", str(cm.exception))


class Tiingo(unittest.TestCase):
    def test_rows(self):
        rows = news.tiingo_rows(TIINGO, RECEIVED)
        self.assertEqual(rows[0]["payload"]["tags"], ["Earnings"])
        self.assertFalse(rows[0]["payload"]["backfilled"])
        self.assertTrue(rows[1]["payload"]["backfilled"])
        self.assertFalse(rows[1]["payload"]["has_tags_field"])
        self.assertNotIn("description", rows[0]["payload"])

    def test_error_reply(self):
        with self.assertRaises(news.NewsError):
            news.tiingo_rows({"detail": "Not authorized"}, RECEIVED)


class CryptoPanic(unittest.TestCase):
    def test_rows(self):
        rows = news.cryptopanic_rows(CP, RECEIVED)
        self.assertAlmostEqual(rows[0]["payload"]["vote_balance"], 0.5)
        self.assertEqual(rows[0]["payload"]["currencies"], ["BTC"])
        self.assertIsNone(rows[1]["payload"]["votes"])
        self.assertIsNone(rows[1]["payload"]["vote_balance"])

    def test_naive_received(self):
        with self.assertRaises(news.NewsError):
            news.cryptopanic_rows(CP, datetime(2026, 11, 19))


class KeyLookup(unittest.TestCase):
    def test_env_fallback_before_store_knows_the_name(self):
        with mock.patch.object(keys, "in_store", return_value=False), \
                mock.patch.dict(os.environ, {"ECOS_API_KEY": " v1 "}):
            self.assertEqual(keys.get_key("ECOS_API_KEY"), "v1")
            st = keys.key_status("ECOS_API_KEY")
            self.assertEqual(st, {"name": "ECOS_API_KEY", "present": True, "source": "env", "in_store": False})

    def test_store_used_once_name_is_known(self):
        with mock.patch.object(keys, "in_store", return_value=True), \
                mock.patch.object(keys.credentials, "get", return_value="from-store") as get, \
                mock.patch.object(keys.credentials, "status",
                                  return_value={"name": "ECOS_API_KEY", "kind": "research",
                                                "present": True, "source": "keyring"}):
            self.assertEqual(keys.get_key("ECOS_API_KEY"), "from-store")
            get.assert_called_once_with("ECOS_API_KEY")
            self.assertEqual(keys.key_status("ECOS_API_KEY")["source"], "keyring")

    def test_require_names_key_not_value(self):
        with mock.patch.object(keys, "in_store", return_value=False), mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(keys.MissingKey) as cm:
                keys.require("TIINGO_API_KEY")
            self.assertIn("TIINGO_API_KEY", str(cm.exception))

    def test_save_refused_before_store_knows_the_name(self):
        with mock.patch.object(keys, "in_store", return_value=False):
            with self.assertRaises(keys.MissingKey):
                keys.save_key("ECOS_API_KEY", "x")
        with self.assertRaises(keys.MissingKey):
            keys.save_key("NOT_A_DIDM_KEY", "x")

    def test_status_never_contains_value(self):
        with mock.patch.object(keys, "in_store", return_value=False), \
                mock.patch.dict(os.environ, {"FRED_API_KEY": "secret-123"}):
            self.assertNotIn("secret-123", repr(keys.key_status("FRED_API_KEY")))


class RealStoreRoundTrip(unittest.TestCase):
    """Against core.credentials itself (KEY-2/KEY-3 on main), with its in-memory test backend."""

    class _Mem:
        def __init__(self):
            self.d = {}

        def get_password(self, service, user):
            return self.d.get((service, user))

        def set_password(self, service, user, password):
            self.d[(service, user)] = password

        def delete_password(self, service, user):
            self.d.pop((service, user))

    def setUp(self):
        self.mem = self._Mem()
        keys.credentials.set_backend(self.mem)
        self.addCleanup(keys.credentials.reset_backend)

    def test_every_research_name_is_in_the_store(self):
        for name in keys.RESEARCH_KEYS:
            self.assertTrue(keys.in_store(name), name)
            self.assertEqual(keys.credentials.names.kind(name), "research")

    def test_save_then_read_from_keyring(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            keys.save_key("ECOS_API_KEY", "  stored-value ")
            self.assertEqual(keys.get_key("ECOS_API_KEY"), "stored-value")
            st = keys.key_status("ECOS_API_KEY")
            self.assertEqual((st["present"], st["source"], st["in_store"]), (True, "keyring", True))
            self.assertNotIn("stored-value", repr(st))

    def test_environment_wins_over_keyring(self):
        self.mem.set_password(keys.credentials.SERVICE, "TIINGO_API_KEY", "from-keyring")
        with mock.patch.dict(os.environ, {"TIINGO_API_KEY": "from-env"}, clear=True):
            self.assertEqual(keys.get_key("TIINGO_API_KEY"), "from-env")
            self.assertEqual(keys.key_status("TIINGO_API_KEY")["source"], "env")


if __name__ == "__main__":
    unittest.main()
