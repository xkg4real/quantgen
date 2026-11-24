"""Evidence index: FTS5 search with an as_of filter that no query can get around."""
import json
import unittest

from _path import CARDS

from quantgpt.checks.citations import check_citations
from quantgpt.checks.schema import SchemaError
from quantgpt.contracts import qss
from quantgpt.rag import EvidenceIndex, card_document, pieces

DOCS = [
    {"source_id": "doc:sharpe", "as_of": "2025-01-10", "kind": "doc", "title": "샤프 비율",
     "text": "샤프 비율은 초과수익을 변동성으로 나눈 값입니다."},
    {"source_id": "doc:pbo", "as_of": "2025-03-02", "kind": "doc", "title": "Probability of backtest overfitting",
     "text": "PBO is the share of splits where the in-sample winner ranks below the median out of sample."},
    {"source_id": "doc:dsr", "as_of": "2026-11-24", "kind": "doc", "title": "DSR",
     "text": "The deflated Sharpe ratio discounts the best of many trials."},
    {"source_id": "doc:future", "as_of": "2026-12-10", "kind": "doc", "title": "샤프 비율 개정",
     "text": "샤프 비율 샤프 비율 샤프 비율: 12월 개정 내용입니다."},
    {"source_id": "doc:stamp", "as_of": "2026-11-24T23:30:00+09:00", "kind": "doc", "title": "Late note",
     "text": "A note about the Sharpe ratio stamped late in the day."},
]


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.index = EvidenceIndex()
        self.addCleanup(self.index.close)
        self.index.add_all(DOCS)

    def ids(self, query, as_of="2026-11-24", **kwargs):
        return [h.source_id for h in self.index.search(query, as_of=as_of, **kwargs)]

    def test_pieces(self):
        self.assertEqual(pieces("샤프 비율은 0.42"), ["샤프", "비율", "율은", "0.42"])
        self.assertEqual(pieces("Deflated SHARPE-ratio"), ["deflated", "sharpe", "ratio"])
        self.assertEqual(pieces("값"), ["값"])
        self.assertEqual(pieces(" ·!? "), [])

    def test_korean_two_syllable_terms_and_english_words_match(self):
        self.assertEqual(self.ids("샤프", as_of="2025-12-31"), ["doc:sharpe"])
        self.assertEqual(self.ids("변동성이 뭔가요", as_of="2025-12-31"), ["doc:sharpe"])
        self.assertEqual(self.ids("overfitting"), ["doc:pbo"])
        self.assertEqual(self.ids("deflated sharpe ratio")[0], "doc:dsr")
        self.assertEqual(self.ids("없는낱말xyz"), [])
        self.assertEqual(self.ids(""), [])

    def test_nothing_later_than_as_of_is_returned(self):
        for query in ("샤프 비율", "샤프 비율 개정 12월", "sharpe", "doc:future"):
            for as_of in ("2024-12-31", "2025-01-10", "2026-11-24", "2026-12-09"):
                with self.subTest(query=query, as_of=as_of):
                    hits = self.index.search(query, as_of=as_of, k=50)
                    self.assertTrue(all(h.as_of[:10] <= as_of for h in hits))
                    self.assertNotIn("doc:future", [h.source_id for h in hits])
        self.assertEqual(self.ids("샤프", as_of="2024-12-31"), [])
        self.assertEqual(self.ids("샤프 비율 개정", as_of="2026-12-10")[0], "doc:future")   # the same day is available

    def test_a_timestamp_as_of_is_compared_to_the_second(self):
        self.assertNotIn("doc:stamp", self.ids("late note", as_of="2026-11-24T14:00:00Z"))
        self.assertIn("doc:stamp", self.ids("late note", as_of="2026-11-24T15:00:00Z"))      # 23:30 KST = 14:30 UTC
        self.assertIn("doc:stamp", self.ids("late note", as_of="2026-11-24"))                # end of the day

    def test_query_text_cannot_carry_search_syntax(self):
        for query in ('샤프" OR source_id:doc', "sharpe NOT ratio", "sharpe*", "body: sharpe", "NEAR(sharpe ratio)",
                      "'; drop table docs; --", "sharpe) OR (as_of_key > '0'", '"""'):
            with self.subTest(query=query):
                hits = self.index.search(query, as_of="2025-12-31", k=50)
                self.assertTrue(all(h.as_of <= "2025-12-31" for h in hits))
        self.assertEqual(len(self.index), 5)

    def test_order_is_stable_and_k_and_kind_are_checked(self):
        first = self.ids("sharpe ratio", k=3)
        self.assertEqual(first, self.ids("sharpe ratio", k=3))
        self.assertEqual(self.ids("ratio sharpe", k=3), first)
        self.assertEqual(self.ids("sharpe", kind="card"), [])
        for bad in ({"k": 0}, {"k": 51}, {"k": True}, {"kind": "order"}):
            with self.assertRaises(SchemaError):
                self.index.search("sharpe", as_of="2026-11-24", **bad)
        with self.assertRaises(SchemaError):
            self.index.search("sharpe", as_of="someday")

    def test_evidence_is_written_once(self):
        version = self.index.version()
        self.index.add(DOCS[0])                                          # the same content again: no change
        self.assertEqual((len(self.index), self.index.version()), (5, version))
        for change in ({"text": "다른 내용"}, {"as_of": "2024-01-01"}, {"title": "다른 제목"}):
            with self.assertRaises(SchemaError):
                self.index.add({**DOCS[0], **change})
        for bad in ({**DOCS[0], "source_id": "has space"}, {**DOCS[0], "kind": "order"},
                    {**DOCS[0], "as_of": "soon"}, {k: v for k, v in DOCS[0].items() if k != "text"},
                    {**DOCS[0], "source_id": "doc:x", "account": "1"}):
            with self.assertRaises(SchemaError):
                self.index.add(bad)
        other = EvidenceIndex(); other.add_all(reversed(DOCS))
        self.assertEqual(other.version(), version)
        other.close()

    def test_hits_feed_the_citation_check(self):
        hits = self.index.search("샤프 비율", as_of="2026-11-24")
        evidence = self.index.evidence_map(hits)
        self.assertTrue(check_citations([hits[0].citation()], evidence, as_of="2026-11-24", required=True).ok)
        made_up = [{"source_id": "doc:future", "as_of": "2026-12-10"}]
        self.assertEqual(check_citations(made_up, evidence, as_of="2026-11-24").reason_code, "citation_unknown")


@unittest.skipUnless(CARDS.is_dir(), "stored research cards are not present")
class CardIndexTests(unittest.TestCase):
    def test_all_34_cards_are_indexed_and_found_by_their_words(self):
        index = EvidenceIndex()
        self.addCleanup(index.close)
        docs = [card_document(qss.card_to_qss(json.loads(p.read_text(encoding="utf-8"))))
                for p in sorted(CARDS.glob("*.json"))]
        self.assertEqual(index.add_all(docs), 34)
        self.assertEqual(len(index), 34)
        created = {d["as_of"] for d in docs}
        self.assertEqual(index.search("deflated sharpe", as_of="2020-01-01", k=50), [])
        hits = index.search("Faber SMA trend switch ETF sleeves", as_of=max(created), k=5, kind="card")
        self.assertIn("card:S_E1_trend_krx", [h.source_id for h in hits[:2]])
        self.assertTrue(all(h.kind == "card" for h in hits))


if __name__ == "__main__":
    unittest.main()
