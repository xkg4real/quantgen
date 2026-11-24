"""DIDM-7: similarity, origin clustering and rule-based entity linking. Synthetic headlines and a
synthetic alias dictionary only: no real article, no model, no network, no clock. With no gold set,
these tests fix the behaviour; linking precision and recall on real articles are not measured yet."""
from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from core.didm import novelty
from core.didm.entities import cluster, linker
from core.didm.entities import similarity as sim
from core.didm.eval import metrics
from core.didm.llm import schema as s

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
T0 = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
WIRE = "Synthetic Bank holds its policy rate at 3.5% as inflation cools, governor signals patience on cuts"
REPOST = "Synthetic Bank holds its policy rate at 3.5% as inflation cools; governor signals patience on rate cuts"
OTHER = "Synthetic Chipmaker beats quarterly profit forecasts on strong server demand"


class Similarity(unittest.TestCase):
    def test_normalisation_ignores_case_punctuation_and_width(self):
        self.assertEqual(sim.normalise("  Rate-Cut:  3.5 %!! "), "rate cut 3 5")
        self.assertEqual(sim.normalise("ＡＢＣ １２３"), "abc 123")                 # full-width forms
        self.assertEqual(sim.normalise("삼성전자, 실적 발표"), "삼성전자 실적 발표")
        self.assertEqual(sim.normalise("…"), "")
        with self.assertRaises(sim.SimilarityError):
            sim.normalise(None)

    def test_jaccard_by_hand_and_edges(self):
        self.assertEqual(sim.shingles("abcdefg"), frozenset({"abcde", "bcdef", "cdefg"}))
        self.assertEqual(sim.shingles("abc"), frozenset({"abc"}))
        self.assertAlmostEqual(sim.jaccard(sim.shingles("abcdefg"), sim.shingles("abcdefh")), 2 / 4)
        self.assertEqual(sim.text_similarity(WIRE, WIRE), 1.0)
        self.assertEqual(sim.text_similarity("", ""), 0.0)                    # nothing to compare is not "same"
        self.assertEqual(sim.text_similarity(WIRE, ""), 0.0)
        self.assertGreater(sim.text_similarity(WIRE, REPOST), 0.85)
        self.assertLess(sim.text_similarity(WIRE, OTHER), 0.10)
        self.assertEqual(sim.text_similarity(WIRE, REPOST), sim.text_similarity(REPOST, WIRE))

    def test_korean_text(self):
        a = "가상전자 3분기 영업이익 10조원 돌파, 반도체 회복"
        b = "가상전자, 3분기 영업이익 10조원 돌파… 반도체 회복"
        self.assertEqual(sim.text_similarity(a, b), 1.0)
        self.assertLess(sim.text_similarity(a, "가상은행 기준금리 동결 결정"), 0.1)

    def test_minhash_estimates_jaccard_and_is_stable_across_processes(self):
        a, b = sim.shingles(WIRE), sim.shingles(REPOST)
        exact = sim.jaccard(a, b)
        estimate = sim.signature_similarity(sim.minhash(a), sim.minhash(b))
        self.assertAlmostEqual(estimate, exact, delta=0.10)                   # 128 hashes: s.e. about 0.03
        self.assertEqual(sim.signature_similarity(sim.minhash(a), sim.minhash(a)), 1.0)
        self.assertLess(sim.signature_similarity(sim.minhash(a), sim.minhash(sim.shingles(OTHER))), 0.10)
        self.assertEqual(len(sim.minhash(a)), sim.SIGNATURE_SIZE)
        code = ("from core.didm.entities import similarity as s; "
                f"print(s.minhash(s.shingles({WIRE!r}))[:4])")
        runs = {subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True, text=True,
                               env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"}).stdout for seed in ("1", "2")}
        self.assertEqual(runs, {str(sim.minhash(a)[:4]) + "\n"})              # not Python's salted hash()
        with self.assertRaises(sim.SimilarityError):
            sim.minhash(frozenset())
        with self.assertRaises(sim.SimilarityError):
            sim.signature_similarity((1, 2), (1,))

    def test_callback_for_the_novelty_features(self):
        def art(i, minutes):
            return novelty.Article(f"a{i}", T0 + timedelta(minutes=minutes), "E:1", s.EventType.MONETARY_POLICY,
                                   f"src{i}", 2)
        articles = [art(0, 0), art(1, 30), art(2, 60)]
        callback = sim.article_similarity({"a0": WIRE, "a1": REPOST, "a2": OTHER})
        self.assertGreater(callback(articles[1], articles[0]), 0.85)
        self.assertLess(callback(articles[2], articles[0]), 0.10)
        features = novelty.build_features(articles, callback)
        col = novelty.FEATURES.index("max_sim_24h")
        self.assertEqual(features.shape, (3, len(novelty.FEATURES)))
        self.assertEqual(features[0, col], 0.0)                               # nothing received before it
        self.assertGreater(features[1, col], 0.85)
        with self.assertRaises(sim.SimilarityError):
            sim.article_similarity({})(articles[0], articles[1])


def item(i, minutes, text):
    return cluster.Item(f"art-{i:03d}", T0 + timedelta(minutes=minutes), text)


class OriginClusters(unittest.TestCase):
    def setUp(self):
        self.items = [item(0, 0, WIRE), item(1, 5, OTHER), item(2, 9, REPOST), item(3, 30, WIRE.upper()),
                      item(4, 45, "Synthetic Retailer names a new chief executive after a boardroom dispute")]

    def test_reposts_share_the_origin_and_rank_counts_up(self):
        out = {a.article_id: a for a in cluster.assign(self.items)}
        self.assertEqual({out[k].origin_article_id for k in ("art-000", "art-002", "art-003")}, {"art-000"})
        self.assertEqual([out[k].rank_in_cluster for k in ("art-000", "art-002", "art-003")], [1, 2, 3])
        self.assertEqual(len({a.origin_cluster_id for a in out.values()}), 3)
        self.assertEqual(out["art-001"].rank_in_cluster, 1)
        self.assertEqual(out["art-003"].similarity_to_origin, 1.0)
        for a in out.values():
            self.assertTrue(s._ID.fullmatch(a.origin_cluster_id), a.origin_cluster_id)      # a valid record identifier
            self.assertNotIn(a.article_id, a.origin_cluster_id)

    def test_later_articles_never_change_earlier_assignments(self):
        first = cluster.assign(self.items[:3])
        again = cluster.assign(self.items)[:3]
        self.assertEqual(first, again)
        shuffled = cluster.assign(list(reversed(self.items)))
        self.assertEqual(shuffled, cluster.assign(self.items))                # order of the input does not matter

    def test_the_first_received_is_the_origin_even_if_listed_last(self):
        late_first = [item(9, 100, WIRE), item(8, 0, REPOST)]
        out = {a.article_id: a for a in cluster.assign(late_first)}
        self.assertEqual((out["art-008"].rank_in_cluster, out["art-009"].rank_in_cluster), (1, 2))
        self.assertEqual(out["art-009"].origin_article_id, "art-008")

    def test_lookback_window_and_threshold(self):
        far = [item(0, 0, WIRE), item(1, 8 * 24 * 60, REPOST)]                # eight days later
        self.assertEqual([a.rank_in_cluster for a in cluster.assign(far)], [1, 1])
        near = [item(0, 0, WIRE), item(1, 6 * 24 * 60, REPOST)]
        self.assertEqual([a.rank_in_cluster for a in cluster.assign(near)], [1, 2])
        self.assertEqual(cluster.NEAR_DUPLICATE, novelty.SIM_THRESHOLD)
        self.assertEqual(cluster.LOOKBACK, timedelta(days=7))
        loose = "Synthetic Bank holds its policy rate at 3.5% while markets expected a cut, shares fall"
        score = sim.text_similarity(WIRE, loose)
        self.assertTrue(0.3 < score < 0.8, score)                             # related story, not a repost
        self.assertEqual([a.rank_in_cluster for a in cluster.assign([item(0, 0, WIRE), item(1, 5, loose)])], [1, 1])
        self.assertEqual([a.rank_in_cluster for a in
                          cluster.assign([item(0, 0, WIRE), item(1, 5, loose)], threshold=0.3)], [1, 2])

    def test_chain_of_reposts_keeps_the_first_origin(self):
        a = "Synthetic Bank holds its policy rate at 3.5% as inflation cools, governor signals patience on cuts"
        b = a + " today"
        c = b + " in Seoul"
        out = cluster.assign([item(0, 0, a), item(1, 5, b), item(2, 10, c)])
        self.assertEqual({x.origin_article_id for x in out}, {"art-000"})

    def test_a_repost_of_a_repost_still_belongs_to_the_first_origin(self):
        """c repeats b closely but has drifted from a (below the threshold): it joins b's cluster, whose
        origin is a."""
        a = "Synthetic Bank holds its policy rate at 3.5% as inflation cools, governor signals patience on cuts ahead"
        b = a + " of the winter meeting"
        c = b + " and markets take note"
        self.assertGreaterEqual(sim.text_similarity(b, a), 0.80)
        self.assertGreaterEqual(sim.text_similarity(c, b), 0.80)
        self.assertLess(sim.text_similarity(c, a), 0.80)
        out = cluster.assign([item(0, 0, a), item(1, 5, b), item(2, 10, c)])
        self.assertEqual([x.origin_article_id for x in out], ["art-000"] * 3)
        self.assertEqual([x.rank_in_cluster for x in out], [1, 2, 3])
        self.assertEqual(len({x.origin_cluster_id for x in out}), 1)

    def test_minhash_mode_agrees_on_clear_cases(self):
        exact = [(a.article_id, a.origin_article_id) for a in cluster.assign(self.items)]
        approx = [(a.article_id, a.origin_article_id) for a in cluster.assign(self.items, exact=False)]
        self.assertEqual(exact, approx)

    def test_empty_text_is_its_own_cluster_and_bad_input_is_refused(self):
        out = cluster.assign([item(0, 0, ""), item(1, 1, "")])
        self.assertEqual([a.rank_in_cluster for a in out], [1, 1])
        with self.assertRaises(cluster.ClusterError):
            cluster.assign([item(0, 0, WIRE), item(0, 1, WIRE)])
        with self.assertRaises(cluster.ClusterError):
            cluster.assign([cluster.Item("a", datetime(2026, 11, 2, 9, 0), WIRE)])
        with self.assertRaises(cluster.ClusterError):
            cluster.assign(self.items, threshold=0.0)


FIRM, MACRO = s.TargetKind.FIRM, s.TargetKind.MACRO
DICTIONARY = [
    linker.Alias("Synthetic Motors", "US:SYNM", FIRM, date(2010, 1, 1)),
    linker.Alias("SYNM", "US:SYNM", FIRM, date(2010, 1, 1)),
    linker.Alias("가상전자", "KR:900001", FIRM, date(2000, 1, 1)),
    linker.Alias("Gasang Electronics", "KR:900001", FIRM, date(2000, 1, 1)),
    linker.Alias("policy rate", "US.FFR", MACRO, date(1990, 1, 1)),
    linker.Alias("Oldname Corp", "US:NEWN", FIRM, date(2005, 1, 1), date(2024, 6, 30)),
    linker.Alias("Newname Inc", "US:NEWN", FIRM, date(2024, 7, 1)),
    linker.Alias("ACME", "US:ACME1", FIRM, date(2000, 1, 1), date(2019, 12, 31)),       # ticker recycled
    linker.Alias("ACME", "US:ACME2", FIRM, date(2021, 1, 1)),
    linker.Alias("Apex", "US:APXA", FIRM, date(2015, 1, 1)),                             # same name, two firms
    linker.Alias("Apex", "US:APXB", FIRM, date(2018, 1, 1)),
    linker.Alias("IT", "US:ITCO", FIRM, date(2015, 1, 1)),                               # ticker that is a word
]
DAY = date(2026, 11, 2)


def links(title, lead=None, body=None, tags=(), day=DAY, article_id="art-1"):
    return linker.Linker(DICTIONARY).link(article_id=article_id, as_of=day, title=title, lead=lead, body=body, tags=tags)


def ids(found):
    return [link.entity_id for link in found]


class EntityLinking(unittest.TestCase):
    def test_mention_position_gives_the_registered_value(self):
        self.assertEqual(linker.MENTION_SCORE, {"title": 100, "lead": 80, "body": 40, "tag": 20})
        prereg = (ROOT / "docs" / "didm" / "PREREG_V0.md").read_text(encoding="utf-8")
        self.assertIn("제목 언급 100, 첫 문단 80, 본문 40, 태그만 20", prereg)
        for kwargs, where, score in ((dict(title="Synthetic Motors recalls cars"), "title", 100),
                                     (dict(title="Recall widens", lead="Synthetic Motors said"), "lead", 80),
                                     (dict(title="Recall widens", body="... Synthetic Motors ..."), "body", 40),
                                     (dict(title="Recall widens", tags=["Synthetic Motors"]), "tag", 20)):
            found = links(**kwargs)
            self.assertEqual([(x.entity_id, x.where, x.mention_score) for x in found], [("US:SYNM", where, score)])
        best = links("Synthetic Motors recalls cars", body="SYNM shares fell. Synthetic Motors declined to comment.")
        self.assertEqual((best[0].where, best[0].mentions), ("title", 3))

    def test_best_position_over_all_aliases_of_one_entity(self):
        """The name is only in the body, the ticker is in the headline: the entity counts as a headline mention."""
        found = links("SYNM slides after recall", body="Synthetic Motors said it would fix the fault.")
        self.assertEqual([(x.entity_id, x.where, x.mention_score, x.mentions) for x in found],
                         [("US:SYNM", "title", 100, 2)])

    def test_word_boundaries_and_case(self):
        self.assertEqual(ids(links("Shares of SYNM rise")), ["US:SYNM"])
        self.assertEqual(ids(links("(SYNM) and $SYNM both appear")), ["US:SYNM"])
        self.assertEqual(ids(links("SYNMX fund launches")), [])                # inside a longer token
        self.assertEqual(ids(links("synm in lower case")), [])                 # a ticker matches case exactly
        self.assertEqual(ids(links("SYNTHETIC MOTORS RECALLS CARS")), ["US:SYNM"])     # a long name ignores case
        self.assertEqual(ids(links("Synthetic Motorsport event")), [])
        self.assertEqual(ids(links("Why it matters for investors")), [])       # "it" is not the ticker IT
        self.assertEqual(ids(links("IT posts record revenue")), ["US:ITCO"])
        self.assertEqual(ids(links("Bank keeps policy rate unchanged")), ["US.FFR"])
        self.assertIs(links("Bank keeps policy rate unchanged")[0].target_kind, MACRO)

    def test_korean_aliases(self):
        self.assertEqual(ids(links("가상전자는 3분기 실적을 발표했다")), ["KR:900001"])     # a particle may follow
        self.assertEqual(ids(links("[속보] 가상전자, 감산 결정")), ["KR:900001"])
        self.assertEqual(ids(links("신가상전자 설립")), [])                               # tail of a longer word
        self.assertEqual(ids(links("가상전기 주가 상승")), [])
        self.assertEqual(ids(links("Gasang Electronics to cut output")), ["KR:900001"])

    def test_dictionary_is_read_as_of_the_article_day(self):
        self.assertEqual(ids(links("Oldname Corp wins contract", day=date(2023, 5, 1))), ["US:NEWN"])
        self.assertEqual(ids(links("Oldname Corp wins contract", day=date(2024, 6, 30))), ["US:NEWN"])     # end day included
        self.assertEqual(ids(links("Oldname Corp wins contract", day=date(2024, 7, 1))), [])
        self.assertEqual(ids(links("Newname Inc wins contract", day=date(2024, 6, 30))), [])
        self.assertEqual(ids(links("Newname Inc wins contract", day=date(2024, 7, 1))), ["US:NEWN"])
        self.assertEqual(ids(links("ACME expands", day=date(2019, 6, 1))), ["US:ACME1"])
        self.assertEqual(ids(links("ACME expands", day=date(2020, 6, 1))), [])            # nobody held the ticker
        self.assertEqual(ids(links("ACME expands", day=date(2022, 6, 1))), ["US:ACME2"])

    def test_an_ambiguous_alias_links_to_neither(self):
        self.assertEqual(ids(links("Apex shares jump", day=date(2016, 1, 1))), ["US:APXA"])      # one owner then
        self.assertEqual(ids(links("Apex shares jump", day=date(2020, 1, 1))), [])               # two owners: no link

    def test_several_entities_and_no_entity(self):
        found = links("Synthetic Motors and 가상전자 sign supply deal", body="The policy rate was not discussed.")
        self.assertEqual(ids(found), ["KR:900001", "US.FFR", "US:SYNM"])
        self.assertEqual(links("Markets drift ahead of holiday"), [])

    def test_bad_dictionary_entries_are_refused(self):
        for kwargs in (dict(alias="A"), dict(alias="  "), dict(valid_to=date(1999, 1, 1)),
                       dict(target_kind=s.TargetKind.NONE)):
            base = dict(alias="Good Name", entity_id="US:GOOD", target_kind=FIRM, valid_from=date(2000, 1, 1))
            with self.subTest(kwargs=kwargs), self.assertRaises(linker.LinkError):
                linker.Alias(**dict(base, **kwargs))
        with self.assertRaises(linker.LinkError):
            linker.Linker(["Synthetic Motors"])
        with self.assertRaises(linker.LinkError):
            links("x", day="2026-11-02")

    def test_scored_with_the_stage1_linking_metric(self):
        """Wiring only: synthetic articles and synthetic answers, so these two numbers say nothing about
        real articles. The registered gate (precision >= 0.95, recall >= 0.80) needs the gold set."""
        cases = [("a1", "Synthetic Motors recalls cars", {"US:SYNM"}),
                 ("a2", "가상전자는 감산을 결정했다", {"KR:900001"}),
                 ("a3", "Apex shares jump", {"US:APXA"}),                      # ambiguous today: missed, not mislinked
                 ("a4", "Bank keeps policy rate unchanged", {"US.FFR"}),
                 ("a5", "Smith Motors unit of Synthetic Motors expands", {"US:SMTH"})]   # not in the dictionary
        engine = linker.Linker(DICTIONARY)
        predicted, gold = set(), set()
        for article_id, title, answer in cases:
            predicted |= linker.link_pairs(engine.link(article_id=article_id, as_of=DAY, title=title))
            gold |= {(article_id, e) for e in answer}
        score = metrics.linking_scores(gold, predicted)
        self.assertEqual((score.true_links, score.predicted_links, score.gold_links), (3, 4, 5))
        self.assertEqual((score.precision, score.recall), (0.75, 0.6))


class Boundaries(unittest.TestCase):
    ALLOWED = {
        "core/didm/entities/similarity.py": ("__future__", "hashlib", "unicodedata", "typing"),
        "core/didm/entities/cluster.py": ("__future__", "hashlib", "dataclasses", "datetime", "typing",
                                          "core.didm.entities"),
        "core/didm/entities/linker.py": ("__future__", "re", "unicodedata", "dataclasses", "datetime", "typing",
                                         "core.didm.llm.schema"),
    }

    def test_no_model_network_file_or_clock(self):
        for rel, allowed in self.ALLOWED.items():
            for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertIn(a.name, allowed, f"{rel} imports {a.name}")
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, allowed, f"{rel} imports {node.module}")
                elif isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ("now", "today", "utcnow", "import_module"), rel)
                elif isinstance(node, ast.Name):
                    self.assertNotIn(node.id, ("open", "hash", "__import__", "exec", "eval"), rel)


if __name__ == "__main__":
    unittest.main()
