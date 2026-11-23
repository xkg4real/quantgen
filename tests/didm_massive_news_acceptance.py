"""Supplied ticker-news metadata only. No documents, dates, or values from a real article."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import unittest

from core.didm.ingest.massive_news import MassiveNewsError, NewsArticle, NewsPage, TickerInsight
from data.didm.massive_news import parse_page


RECEIVED = datetime(2024, 4, 5, 12, tzinfo=timezone.utc)
ARTICLE = {
    "id": "fixture-1",
    "title": "Synthetic fixture",
    "author": "Author",
    "publisher": {"name": "Sample Publisher"},
    "article_url": "https://publisher.invalid/articles/one",
    "published_utc": "2024-04-05T10:30:00Z",
    "tickers": ["QGA"],
}
NEXT = "https://api.massive.com:443/v2/reference/news"
SECRET = "PRIVATE_FIXTURE_MARKER"


def page(*articles, **fields):
    return {"results": list(articles), **fields}


class MassiveNewsTests(unittest.TestCase):
    def test_publication_and_receipt_have_different_origins(self):
        local = RECEIVED.astimezone(timezone(timedelta(hours=9)))
        result = parse_page(page(ARTICLE), local)
        self.assertIsInstance(result, NewsPage)
        obj = result.articles[0]
        self.assertIsInstance(obj, NewsArticle)
        self.assertEqual(obj.published_utc_raw, ARTICLE["published_utc"])
        self.assertEqual(obj.published_at_utc, RECEIVED - timedelta(minutes=90))
        self.assertEqual(obj.received_at_utc, RECEIVED)
        self.assertEqual(obj.tickers, ("QGA",))
        self.assertEqual(obj.publisher_name, "Sample Publisher")

    def test_preserves_explicit_offset_and_submicrosecond_source_precision(self):
        timestamp = "2024-04-05T19:30:00.123456789+09:00"
        row = parse_page(page(dict(ARTICLE, published_utc=timestamp)), RECEIVED).articles[0]
        self.assertEqual(row.published_utc_raw, timestamp)
        self.assertEqual(row.published_at_utc, datetime(2024, 4, 5, 10, 30, 0, 123456, tzinfo=timezone.utc))

    def test_exact_clock_relation_and_bad_timestamps(self):
        for stamp in ("2024-04-05", "2024-04-05T12:00:00", "2024-04-05T12:00:00-00:00",
                      "2024-04-05T12:00:00+05:60", "2024-04-31T00:00:00Z",
                      "2024-04-05T12:00:00.000000001Z", "0001-01-01T00:00:00+01:00", None):
            with self.subTest(stamp=stamp), self.assertRaises(MassiveNewsError):
                parse_page(page(dict(ARTICLE, published_utc=stamp)), RECEIVED)
        self.assertEqual(parse_page(page(dict(ARTICLE, published_utc="2024-04-05T12:00:00.000000000Z")),
                                    RECEIVED).articles[0].published_at_utc, RECEIVED)

    def test_received_time_is_required_even_for_empty_pages(self):
        for value in (None, "2024-04-05", RECEIVED.replace(tzinfo=None)):
            with self.subTest(value=value), self.assertRaises(MassiveNewsError):
                parse_page(page(), value)

    def test_missing_results_is_not_a_confirmed_empty_page(self):
        for bad in ({}, {"status": "OK"}, {"results": None}, {"results": {}}, []):
            with self.subTest(bad=bad), self.assertRaises(MassiveNewsError):
                parse_page(bad, RECEIVED)
        self.assertEqual(parse_page(page(status="OK", count=0), RECEIVED).articles, ())
        self.assertEqual(parse_page(page(), RECEIVED).articles, ())

    def test_error_and_unknown_statuses_do_not_become_valid_pages(self):
        for fields in ({"status": "ERROR"}, {"status": "unexpected"}, {"status": None},
                       {"error": SECRET}, {"errors": [SECRET]}, {"message": SECRET}):
            with self.subTest(fields=fields), self.assertRaises(MassiveNewsError) as caught:
                parse_page(page(**fields), RECEIVED)
            self.assertNotIn(SECRET, str(caught.exception))

    def test_article_shape_and_optional_publisher_information(self):
        for name in ARTICLE:
            partial = {k: v for k, v in ARTICLE.items() if k != name}
            with self.subTest(name=name), self.assertRaises(MassiveNewsError):
                parse_page(page(partial), RECEIVED)
        for key, bad in (("publisher", []), ("id", " "), ("id", 1), ("author", False),
                         ("tickers", "QGA"), ("tickers", ["QGA", None])):
            with self.subTest(key=key), self.assertRaises(MassiveNewsError):
                parse_page(page(dict(ARTICLE, **{key: bad})), RECEIVED)
        row = parse_page(page(dict(ARTICLE, publisher={}, tickers=[], author="")), RECEIVED).articles[0]
        self.assertIsNone(row.publisher_name)
        self.assertEqual(row.tickers, ())

    def test_optional_insights_and_unknown_label_are_distinct(self):
        rows = [ARTICLE, dict(ARTICLE, insights=[]), dict(ARTICLE, insights=[
            {"ticker": "QGA", "sentiment": "neutral"}, {"ticker": "QGB", "sentiment": "positive"},
            {"ticker": "QGC", "sentiment": "negative"}, {"ticker": "QGD", "sentiment": "new category"},
            {"ticker": "QGE"}, {}])]
        a, b, c = parse_page(page(*rows), RECEIVED).articles
        self.assertIsNone(a.insights)
        self.assertEqual(b.insights, ())
        self.assertEqual(c.insights, (TickerInsight("QGA", "neutral"), TickerInsight("QGB", "positive"),
                                     TickerInsight("QGC", "negative"), TickerInsight("QGD", "new category"),
                                     TickerInsight("QGE", None), TickerInsight(None, None)))

    def test_invalid_insights_fail_without_leaking_input(self):
        for invalid in ({}, SECRET, [SECRET], [{"sentiment": [SECRET]}], [{"ticker": [SECRET]}]):
            with self.subTest(invalid=invalid), self.assertRaises(MassiveNewsError) as caught:
                parse_page(page(dict(ARTICLE, insights=invalid)), RECEIVED)
            self.assertNotIn(SECRET, str(caught.exception))

    def test_discards_body_summary_sentiment_reason_and_sensitive_url_parts(self):
        article = dict(ARTICLE, description=SECRET, content=SECRET, body=SECRET,
                       image_url=SECRET, unknown=SECRET,
                       article_url=f"https://publisher.invalid/one?apiKey={SECRET}#{SECRET}",
                       publisher={"name": "Wire", "homepage_url": SECRET},
                       insights=[{"ticker": "QGA", "sentiment": "positive", "sentiment_reasoning": SECRET}])
        parsed = parse_page(page(article, request_id=SECRET, next_url=f"{NEXT}?apiKey={SECRET}&cursor=step2"),
                            RECEIVED)
        self.assertNotIn(SECRET, repr(asdict(parsed)))
        self.assertIsNone(parsed.articles[0].article_url)
        self.assertEqual(parsed.next_cursor, "step2")
        self.assertNotIn("step2", repr(parsed))

    def test_page_cursor_is_independent_of_count_and_results_length(self):
        parsed = parse_page(page(count=0, next_url=NEXT + "?cursor=step%2B2%2F3%3D&sort=published_utc"), RECEIVED)
        self.assertEqual(parsed.articles, ())
        self.assertEqual(parsed.next_cursor, "step+2/3=")
        self.assertIsNone(parse_page(page(ARTICLE, count=999), RECEIVED).next_cursor)
        self.assertIsNone(parse_page(page(next_url=None), RECEIVED).next_cursor)
        self.assertEqual(parse_page(page(next_url=NEXT.replace(":443", "") + "?cursor=step2"), RECEIVED).next_cursor,
                         "step2")

    def test_opaque_cursor_preserves_encoded_punctuation(self):
        url = NEXT + "?cursor=part%3A2%3Bkind%3Dnews%26offset%3D1%25done&apiKey=" + SECRET
        parsed = parse_page(page(next_url=url), RECEIVED)
        self.assertEqual(parsed.next_cursor, "part:2;kind=news&offset=1%done")
        self.assertNotIn(SECRET, repr(asdict(parsed)))

    def test_deeply_nested_cursor_escaping_fails_closed(self):
        url = NEXT + "?cursor=part%252525253Aend&apiKey=" + SECRET
        with self.assertRaisesRegex(MassiveNewsError, "^next_url: excessive nested escaping$"):
            parse_page(page(next_url=url), RECEIVED)

    def test_bad_links_and_cursor_credentials_never_appear_in_exceptions(self):
        for url in (NEXT + f"?apiKey={SECRET}", NEXT + f"?cursor=&apiKey={SECRET}",
                    NEXT + f"?cursor=one&cursor=two&apiKey={SECRET}", NEXT + f"?cursor=apiKey%3D{SECRET}",
                    NEXT + f"?cursor=x%26apiKey%3D{SECRET}", NEXT + f"?cursor={SECRET}&apiKey={SECRET}",
                    NEXT + f"?cursor=a%2526apiKey%253D{SECRET}", NEXT + f"?cursor=%FF&apiKey={SECRET}",
                    NEXT + f"?cursor=abc%0D%0A&apiKey={SECRET}", NEXT + f"?cursor=https%3A%2F%2Fpub.invalid%2F{SECRET}",
                    NEXT + f"?cursor=ok#{SECRET}", NEXT.replace("https", "http") + f"?cursor={SECRET}",
                    NEXT.replace("massive.com", "massive.com.invalid") + f"?cursor={SECRET}",
                    NEXT.replace(":443", ":invalid") + f"?cursor={SECRET}",
                    NEXT.replace("api.massive.com", f"{SECRET}@api.massive.com") + "?cursor=ok",
                    NEXT.replace("/news", "/different") + f"?cursor={SECRET}"):
            with self.subTest(url=url), self.assertRaises(MassiveNewsError) as caught:
                parse_page(page(next_url=url), RECEIVED)
            self.assertNotIn(SECRET, str(caught.exception))

    def test_article_link_must_be_public_http_or_https(self):
        for url in (f"file:///{SECRET}", f"https://name:{SECRET}@publisher.invalid/x",
                    f"https://[not-an-address]/{SECRET}", "https://publisher.invalid:100000/x"):
            with self.subTest(url=url), self.assertRaises(MassiveNewsError) as caught:
                parse_page(page(dict(ARTICLE, article_url=url)), RECEIVED)
            self.assertNotIn(SECRET, str(caught.exception))

    def test_query_or_fragment_dependent_article_links_are_withheld_in_full(self):
        urls = ["https://publisher.invalid/news?id=101", "https://publisher.invalid/news?id=202",
                "https://publisher.invalid/news#article", "https://Publisher.Invalid/articles/one"]
        rows = parse_page(page(*(dict(ARTICLE, article_url=url) for url in urls)), RECEIVED).articles
        self.assertEqual([r.article_url for r in rows], [None, None, None, urls[-1]])

    def test_cursor_cycle_is_rejected(self):
        with self.assertRaises(MassiveNewsError):
            parse_page(page(next_url=NEXT + "?cursor=two"), RECEIVED, seen_cursors=("one", "two"))
        self.assertEqual(parse_page(page(next_url=NEXT + "?cursor=two"), RECEIVED,
                                    seen_cursors=deque(["one"])).next_cursor, "two")
        for malformed in ("two", b"", {}, [None]):
            with self.subTest(malformed=malformed), self.assertRaises(MassiveNewsError):
                parse_page(page(), RECEIVED, seen_cursors=malformed)

    def test_same_id_observations_preserve_revisions_order_and_receipt(self):
        updated = dict(ARTICLE, title="Synthetic editorial revision",
                       insights=[{"ticker": "QGA", "sentiment": "positive"}])
        page1 = parse_page(page(ARTICLE, updated, ARTICLE), RECEIVED)
        page2 = parse_page(page(updated), RECEIVED + timedelta(hours=1))
        self.assertEqual([a.title for a in page1.articles], [ARTICLE["title"], updated["title"], ARTICLE["title"]])
        self.assertTrue(all(a.article_id == "fixture-1" for a in (*page1.articles, *page2.articles)))
        self.assertIsNone(page1.articles[0].insights)
        self.assertEqual(page2.articles[0].published_at_utc, page1.articles[0].published_at_utc)
        self.assertGreater(page2.articles[0].received_at_utc, page1.articles[0].received_at_utc)


if __name__ == "__main__":
    unittest.main()
