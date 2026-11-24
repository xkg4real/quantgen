"""DIDM-9/e2e: the Version 0 pieces joined end to end on a synthetic newsroom. A wiring check: it shows
that links, judgements, clusters, events, credibility, records and shocks fit together, keep the
point-in-time rule and give back the answers built into the synthetic world. It is not a registered
run, prints no verdict and says nothing about any real market, article or model."""
from __future__ import annotations

import ast
import math
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from core.didm.credibility import events
from core.didm.credibility import state as cred
from core.didm.entities.linker import Linker
from core.didm.llm import cutoffs
from core.didm.llm import schema as s
from core.didm.llm import scorer as sc
from core.didm.models import har_x, lp
from core.didm.sim import newsroom as nr
from core.didm.sim import pipeline as pl

ROOT = Path(__file__).resolve().parents[1]
TYPES = [e.value for e in s.EventType]
MODEL = "toy-llm-1"


class WorldScorer:
    """A calibrated stand-in scorer: it reports the probabilities the synthetic world used. ``broken``
    article ids get an invalid answer instead."""

    def __init__(self, world: nr.World, broken=(), model_version: str = MODEL):
        self.info = sc.ScorerInfo(model_version, "ab" * 32)
        self.claim_of = {a.article_id: a.claim for a in world.articles}
        self.claims = {c.index: c for c in world.claims}
        self.broken = set(broken)

    def judge(self, request):
        index = self.claim_of[request.article_id]
        etype, probs, p_subject = "none", [0.0, 0.0, 1.0], 0.1
        if index is not None:
            claim = self.claims[index]
            etype, probs, p_subject = claim.event_type, list(claim.probs), 0.9
        answer = {"judgement_version": "didm-judgement-v0", "article_id": request.article_id,
                  "target_kind": request.target_kind.value, "entity_id": request.entity_id, "p_subject": p_subject,
                  "event_type": etype, "event_type_probs": {t: (1.0 if t == etype else 0.0) for t in TYPES},
                  "direction_probs": probs, "claim_status": "reported"}
        if request.article_id in self.broken:
            answer["rationale"] = "free text the contract does not allow"
        return answer


def decisions(world: nr.World, upto: int | None = None):
    days = world.n_days if upto is None else upto + 1
    return [nr.START + timedelta(days=d) for d in range(days + 1)]


def run(world: nr.World, **kw):
    scorer = kw.pop("scorer", None) or WorldScorer(world)
    return pl.run(kw.pop("articles", world.articles), linker=Linker(world.aliases), scorer=scorer,
                  decisions=kw.pop("decisions", decisions(world)), **kw)


def logistic(x):
    return 1 / (1 + math.exp(-x))


class FullWorld(unittest.TestCase):
    """40 firms, 400 days, about 1,200 claims and 8,800 articles."""

    @classmethod
    def setUpClass(cls):
        cls.world = nr.build()
        cls.stages = run(cls.world)
        cls.panel = pl.panel(cls.stages, cls.world.entity_ids, cls.world.n_days + 1)
        cls.oracle = nr.oracle_shocks(cls.world)

    def test_1_shocks_equal_the_worlds_own_answer(self):
        got = self.panel["shock"][1:]                       # decision index d + 1 closes world day d
        want = self.oracle["shock"]
        self.assertGreater(int((want != 0).sum()), 1000)
        np.testing.assert_allclose(got, want, rtol=0, atol=1e-12)
        self.assertEqual(float(np.abs(self.panel["shock"][0]).max()), 0.0)

    def test_1b_every_stage_matches_the_worlds_structure(self):
        true_origin = {a.article_id: a.origin for a in self.world.articles}
        self.assertEqual(self.stages.origin_of, true_origin)                     # clustering found every re-publication
        claim_of = {a.article_id: a.claim for a in self.world.articles}
        by_event: dict[str, set] = {}
        for rid, event in self.stages.event_of.items():
            claim = claim_of[self.stages.record_article[rid]]
            if claim is not None:
                by_event.setdefault(event, set()).add(claim)
        self.assertTrue(all(len(v) == 1 for v in by_event.values()))            # one event = one claim ...
        self.assertEqual(len(by_event), len(self.world.claims))                 # ... and one claim = one event
        for record in self.stages.records[:200]:
            self.assertEqual(s.validate_record(record.as_dict()), record)
        self.assertEqual(self.stages.rejected_judgements, {})
        self.assertEqual(self.stages.rejected_assembly, {})
        self.assertRegex(self.stages.weights_version, "^cred-placeholder-")

    def test_2_estimators_recover_the_built_in_effects(self):
        shock, abs_shock = self.panel["shock"][1:], self.panel["abs_shock"][1:]
        fit = lp.fit_lp(self.world.returns, shock[:, :, None], ("shock",), horizons=(0,))
        self.assertAlmostEqual(fit.coef("shock", 0) / self.world.theta0, 1.0, delta=0.15)
        vol = har_x.fit_har_x(self.world.log_rv, abs_shock[:, :, None], ("gamma",))
        self.assertAlmostEqual(vol.value("gamma") / self.world.gamma, 1.0, delta=0.15)
        lo, hi = fit.interval("shock", 0, lp.Z95)
        self.assertGreater(lo, 0.0)

    def test_4_a_reposted_story_counts_once(self):
        by_claim: dict[int, list] = {}
        for a in self.world.articles:
            if a.claim is not None:
                by_claim.setdefault(a.claim, []).append(a)
        claim = max((c for c in self.world.claims if c.kind == "rumour"), key=lambda c: len(by_claim[c.index]))
        copies = len(by_claim[claim.index])
        self.assertGreaterEqual(copies, 25)                                     # one post and many re-posts
        cell = self.stages.cells[(claim.day + 1, self.world.entity_ids[claim.firm], claim.event_type)]
        self.assertEqual(cell.n_records, 1)
        self.assertAlmostEqual(cell.shock, logistic(0.3) * (claim.probs[0] - claim.probs[1]))   # one tier-3 report
        self.assertGreater(self.stages.dropped["repeated_origin"], 5000)

    def test_5_a_denied_rumour(self):
        denied_later = [c for c in self.world.claims if c.kind == "rumour_denied_later"]
        denied_same_day = [c for c in self.world.claims if c.kind == "rumour_denied_same_day"]
        self.assertGreater(len(denied_later), 20)
        self.assertGreater(len(denied_same_day), 20)
        denial_day = {a.claim: (a.received_at - nr.START).days for a in self.world.articles if a.official}
        for claim in denied_later[:20]:
            entity = self.world.entity_ids[claim.firm]
            before = self.stages.cells[(claim.day + 1, entity, claim.event_type)]
            self.assertAlmostEqual(before.shock, logistic(0.3) * (claim.probs[0] - claim.probs[1]))   # believed 0.57
            after = self.stages.cells[(denial_day[claim.index] + 1, entity, claim.event_type)]
            self.assertEqual(after.shock, 0.0)                                  # the denial itself adds nothing
        for claim in denied_same_day[:20]:
            cell = self.stages.cells[(claim.day + 1, self.world.entity_ids[claim.firm], claim.event_type)]
            self.assertEqual(cell.shock, 0.0)                                   # denied before the decision
            # (c) the records carry the credibility of their own receipt time (above 0 for the rumour post);
            # the shock used the credibility at the decision (0), not the records' values
            in_cell = [r for r in self.stages.records if r.record_id in cell.record_ids]
            self.assertTrue(any(r.p_credibility > 0.5 for r in in_cell), claim.index)

    def test_8_planted_articles_reach_no_shock(self):
        used = {rid for cell in self.stages.cells.values() for rid in cell.record_ids}
        used_articles = {self.stages.record_article[rid] for rid in used}
        recorded = set(self.stages.record_article.values())
        for kind in ("expired_alias", "ambiguous_alias"):
            self.assertGreater(len(self.world.planted[kind]), 10)
            self.assertFalse(set(self.world.planted[kind]) & recorded, kind)    # never linked, so never a record
        self.assertEqual(self.stages.unlinked_articles,
                         len(self.world.planted["expired_alias"]) + len(self.world.planted["ambiguous_alias"]))
        passing = set(self.world.planted["passing"])
        self.assertTrue(passing <= recorded)                                    # linked from the body ...
        self.assertFalse(passing & used_articles)                               # ... but never a signal
        self.assertEqual(self.stages.dropped["no_type_or_target"], len(passing))
        relevance = {r.record_id.split("/")[0]: r.relevance_0_100 for r in self.stages.records}
        self.assertEqual({relevance[a] for a in passing}, {40.0})

    def test_8b_a_renamed_firm_is_linked_by_the_name_valid_on_the_articles_day(self):
        rename = self.world.planted["rename_day"]
        firm3 = [c for c in self.world.claims if c.firm == 3]
        before = [c for c in firm3 if c.day <= rename]
        after = [c for c in firm3 if c.day > rename]
        self.assertGreater(len(before), 5)
        self.assertGreater(len(after), 5)
        entity = self.world.entity_ids[3]
        for claim in before + after:
            self.assertIn((claim.day + 1, entity, claim.event_type), self.stages.cells)
        titles = {a.claim: a.title for a in self.world.articles if a.claim is not None}
        self.assertTrue(all("Novaquill Partners" in titles[c.index] for c in after))
        self.assertFalse(any("Novaquill Partners" in titles[c.index] for c in before))

    def test_11_market_confirmation_side_record_is_point_in_time(self):
        """DIDM-8/a: verdicts are appended beside the records; a reader at a decision sees what the
        registered rule could know then, and nothing that became known later."""
        from core.didm.llm.schema import MarketConfirmation as MC
        from core.didm.models import confirmation as cf
        from core.didm.models import confirmation_log as cl
        w, dec = self.world, decisions(self.world)
        log = pl.confirmation_entries(self.stages, returns=w.returns, market=w.market, entity_ids=w.entity_ids,
                                      decisions=dec)
        self.assertGreater(len(log), len(self.stages.records))                # PENDING for all, later verdicts for some
        final = {e.status for e in log}
        self.assertIn(MC.PENDING, final)
        self.assertTrue(final & {MC.CONFIRMED, MC.CONTRADICTED, MC.ALREADY_PRICED})
        self.assertTrue(all(r.market_confirmation is MC.PENDING for r in self.stages.records))   # records untouched
        column = {e: i for i, e in enumerate(w.entity_ids)}
        changed = [e for e in log if e.status is not MC.PENDING][:150]
        self.assertGreater(len(changed), 20)
        records = {r.record_id: r for r in self.stages.records}
        for e in changed:
            record = records[e.record_id]
            k = dec.index(e.known_at)
            day = next(i for i in range(1, len(dec)) if dec[i - 1] < record.received_at <= dec[i]) - 1
            sign = record.direction_probs[0] - record.direction_probs[1]
            direction = 1 if sign > 0 else -1
            # what the rule says with returns cut at the day before that decision ...
            cut_returns = w.returns[:k, column[record.entity_id]]
            now = cf.confirm_daily(cut_returns, w.market[:k], event_index=day, last_known_index=k - 1,
                                   predicted_direction=direction)
            self.assertIs(now.status, e.status)
            # ... and one decision earlier the reader did not see it yet
            self.assertIsNot(cl.status_as_of(log, e.record_id, dec[k - 1]), e.status)
            self.assertIs(cl.status_as_of(log, e.record_id, dec[k]), e.status)
            self.assertEqual(e.judgement_sha256, self.stages.judgement_seal[e.record_id])
        # nothing in the log is dated after the last decision, and the shocks do not depend on the log
        self.assertLessEqual(max(e.known_at for e in log), dec[-1])
        np.testing.assert_allclose(self.panel["shock"][1:], self.oracle["shock"], rtol=0, atol=1e-12)

    def test_6_training_cutoff_rule_applies_to_the_records(self):
        def registry(cutoff):
            return cutoffs.REGISTRY.with_card(cutoffs.ModelCard(
                key=MODEL, family="toy", rule=cutoffs.Rule.CUTOFF, snapshot_id="toy@1", cutoff=cutoff,
                source_url="https://example.org/toy-model-card", checked_on=date(2026, 11, 24)))
        n = len(self.stages.records)
        self.assertEqual(pl.eligibility_summary(self.stages.records, registry(date(2026, 6, 30))),
                         {"eligible": n, "not_eligible": 0})                    # eligible from 2026-09-30
        late = pl.eligibility_summary(self.stages.records, registry(date(2028, 1, 31)))
        self.assertEqual(late, {"eligible": 0, "not_eligible": n})              # trained past every article
        mid = pl.eligibility_summary(self.stages.records, registry(date(2026, 12, 31)))   # eligible from 2027-03-31
        first_ok = sum(r.received_at.date() >= date(2027, 3, 31) and r.published_at.date() >= date(2027, 3, 31)
                       for r in self.stages.records)
        self.assertEqual(mid["eligible"], first_ok)
        self.assertTrue(0 < mid["eligible"] < n)
        self.assertEqual(pl.eligibility_summary(self.stages.records, cutoffs.REGISTRY),
                         {"eligible": 0, "not_eligible": n})                    # a model outside the registry


class SmallWorld(unittest.TestCase):
    """12 firms, 80 days: small enough to run the pipeline several times."""

    @classmethod
    def setUpClass(cls):
        cls.world = nr.build(n_firms=12, n_days=80, seed=11, event_rate=0.15)
        cls.stages = run(cls.world)

    def test_3_point_in_time(self):
        """Cut the article stream at a decision: everything up to that decision is exactly as in the full run."""
        cut_day = 40
        cut = self.world.decision(cut_day)
        early = [a for a in self.world.articles if a.received_at <= cut]
        self.assertLess(len(early), len(self.world.articles))
        partial = run(self.world, articles=early, decisions=decisions(self.world, upto=cut_day))
        full_records = {r.record_id: r for r in self.stages.records if r.received_at <= cut}
        self.assertEqual({r.record_id: r for r in partial.records}, full_records)        # p_credibility included
        self.assertEqual(partial.origin_of, {k: v for k, v in self.stages.origin_of.items() if k in partial.origin_of})
        self.assertEqual(partial.event_of, {k: v for k, v in self.stages.event_of.items() if k in partial.event_of})
        full_cells = {k: v for k, v in self.stages.cells.items() if k[0] <= cut_day + 1}
        self.assertEqual(partial.cells, full_cells)
        self.assertGreater(len(full_cells), 50)

    def test_3b_an_article_received_after_the_decision_is_not_in_that_days_shock(self):
        claim = next(c for c in self.world.claims if c.kind == "reports" and 5 < c.day < 70)
        entity, key_day = self.world.entity_ids[claim.firm], claim.day + 1
        base = self.stages.cells[(key_day, entity, claim.event_type)]
        moved = [replace(a, received_at=self.world.decision(claim.day) + timedelta(minutes=1),
                         published_at=self.world.decision(claim.day)) if a.claim == claim.index else a
                 for a in self.world.articles]
        late = run(self.world, articles=moved)
        self.assertNotIn((key_day, entity, claim.event_type), late.cells)                # one minute too late
        self.assertAlmostEqual(late.cells[(key_day + 1, entity, claim.event_type)].shock, base.shock)

    def test_7_broken_judgements_are_counted_and_never_become_records(self):
        reposts = [a.article_id for a in self.world.articles if a.claim is not None and a.origin != a.article_id][:40]
        broken = run(self.world, scorer=WorldScorer(self.world, broken=reposts))
        self.assertEqual(broken.rejected_judgements, {"unknown judgement fields": 40})
        self.assertFalse(set(reposts) & set(broken.record_article.values()))
        self.assertEqual(len(broken.records), len(self.stages.records) - 40)
        self.assertEqual({k: v.shock for k, v in broken.cells.items()},
                         {k: v.shock for k, v in self.stages.cells.items()})             # a copy lost changes nothing
        self.assertEqual(broken.rejected_assembly, {})                                   # everything kept assembled

    def test_9_same_seed_same_result(self):
        again = run(nr.build(n_firms=12, n_days=80, seed=11, event_rate=0.15))
        self.assertEqual(again.records, self.stages.records)
        self.assertEqual(again.cells, self.stages.cells)
        other = nr.build(n_firms=12, n_days=80, seed=12, event_rate=0.15)
        self.assertNotEqual([a.title for a in other.articles[:5]], [a.title for a in self.world.articles[:5]])

    def test_10b_event_key_reading_changes_credibility_in_the_pipeline(self):
        with_origin = run(self.world, event_key=events.EventKeyConfig(mode="with_origin"))
        multi = [c for c in self.world.claims if c.kind == "reports"
                 and len({a.origin for a in self.world.articles if a.claim == c.index}) >= 2]
        self.assertGreater(len(multi), 20)
        bigger = 0
        for claim in multi:
            key = (claim.day + 1, self.world.entity_ids[claim.firm], claim.event_type)
            bigger += abs(self.stages.cells[key].shock) > abs(with_origin.cells[key].shock) + 1e-12
        self.assertEqual(bigger, sum(abs(c.probs[0] - c.probs[1]) > 1e-12 for c in multi))   # independent reports add up


class EventKeyRule(unittest.TestCase):
    """Condition 10: three independent reports raise credibility three times; a report after the window is a new event."""
    T0 = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)

    def mentions(self, offsets):
        return [events.Mention(f"a{i}", "SYN:001", "earnings", self.T0 + off, f"cl-{i}") for i, off in enumerate(offsets)]

    def reports(self, mentions, tiers, key):
        return [cred.Report(m.article_id, key[(m.article_id, m.entity_id)], m.received_at, tier, m.origin_cluster_id, 1)
                for m, tier in zip(mentions, tiers)]

    def test_independent_reports_accumulate_under_the_decided_key(self):
        ms = self.mentions([timedelta(0), timedelta(hours=2), timedelta(hours=5)])
        key = events.assign(ms)
        self.assertEqual(len(set(key.values())), 1)
        path = cred.path(self.reports(ms, (2, 2, 3), key), next(iter(key.values())))
        self.assertEqual([round(x.pi_after, 3) for x in path], [0.731, 0.881, 0.909])       # three rises
        alt = events.assign(ms, config=events.EventKeyConfig(mode="with_origin"))
        self.assertEqual(len(set(alt.values())), 3)
        alone = [cred.path(self.reports(ms, (2, 2, 3), alt), e)[-1].pi_after for e in sorted(set(alt.values()))]
        self.assertEqual(sorted(round(x, 3) for x in alone), [0.574, 0.731, 0.731])         # each stands alone

    def test_window_is_seven_days_from_the_first_report(self):
        self.assertEqual(events.EVENT_WINDOW, timedelta(days=7))
        self.assertEqual(events.EventKeyConfig().mode, "first_report_window")
        ms = self.mentions([timedelta(0), timedelta(days=6, hours=23), timedelta(days=7), timedelta(days=7, minutes=1),
                            timedelta(days=8), timedelta(days=14, minutes=2)])
        key = events.assign(ms)
        ids = [key[(m.article_id, m.entity_id)] for m in ms]
        self.assertEqual(len({ids[0], ids[1], ids[2]}), 1)                 # up to and including day 7
        self.assertNotEqual(ids[3], ids[0])                                # day 8 starts a new event
        self.assertEqual(ids[4], ids[3])                                   # measured from the new event's first report
        self.assertNotEqual(ids[5], ids[3])
        same_claim = self.mentions([timedelta(0), timedelta(hours=20)])      # 09:00 and 05:00 the next day
        self.assertEqual(len(set(events.assign(same_claim).values())), 1)
        by_day = events.assign(same_claim, config=events.EventKeyConfig(mode="calendar_day"))
        self.assertEqual(len(set(by_day.values())), 2)                     # the day-unit alternative splits them

    def test_other_targets_and_types_are_other_events_and_order_does_not_matter(self):
        ms = self.mentions([timedelta(0), timedelta(hours=1)])
        other = [events.Mention("b0", "SYN:002", "earnings", self.T0, "x"),
                 events.Mention("b1", "SYN:001", "management", self.T0, "y")]
        key = events.assign(ms + other)
        self.assertEqual(len(set(key.values())), 3)
        self.assertEqual(events.assign(list(reversed(ms + other))), key)
        with self.assertRaises(events.EventError):
            events.assign(ms + ms)
        with self.assertRaises(events.EventError):
            events.EventKeyConfig(mode="per_article")


class Boundaries(unittest.TestCase):
    FILES = ("core/didm/sim/newsroom.py", "core/didm/sim/pipeline.py", "core/didm/credibility/events.py")

    def test_no_data_source_network_file_or_clock(self):
        for rel in self.FILES:
            for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding="utf-8"))):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    top = name.split(".")[0]
                    self.assertTrue(top in ("__future__", "math", "hashlib", "dataclasses", "datetime", "typing", "numpy")
                                    or name == "core.didm" or name.startswith("core.didm."), f"{rel} imports {name}")
                    self.assertFalse(name.startswith(("core.didm.store", "core.didm.ingest")), f"{rel} imports {name}")
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ("now", "today", "utcnow", "import_module"), rel)
                elif isinstance(node, ast.Name):
                    self.assertNotIn(node.id, ("open", "__import__", "exec", "eval"), rel)


if __name__ == "__main__":
    unittest.main()
