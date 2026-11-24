"""DIDM-2: the scorer contract. One judgement shape for every scorer, records assembled by DIDM,
JSON Schema files generated from the code, and conformance examples. No network, no model calls."""
from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

from core.didm.llm import judgement as j
from core.didm.llm import schema as s
from core.didm.llm import scorer as sc
from tools.didm import export_schema

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "tests" / "fixtures" / "didm" / "conformance"
SCHEMA_DIR = ROOT / "docs" / "didm" / "schema"


def load(folder: str) -> list[tuple[str, dict]]:
    return [(p.name, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((CONFORMANCE / folder).glob("*.json"))]


def assemble(case: dict) -> sc.Assembled:
    request = j.validate_request(case["request"])
    judgement = j.validate_judgement(case["judgement"], request)
    return sc.assemble_record(judgement, sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"]))


def json_schema_errors(schema: dict, value, path: str = "$") -> list[str]:
    """The subset of JSON Schema 2020-12 that export_schema emits. Standard library only."""
    out: list[str] = []
    kinds = {"object": dict, "array": list, "string": str, "null": type(None)}
    if "type" in schema:
        wanted = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        ok = False
        for kind in wanted:
            if kind == "number":
                ok = ok or (isinstance(value, (int, float)) and not isinstance(value, bool))
            else:
                ok = ok or isinstance(value, kinds[kind])
        if not ok:
            return [f"{path}: type"]
    if "const" in schema and value != schema["const"]:
        out.append(f"{path}: const")
    if "enum" in schema and value not in schema["enum"]:
        out.append(f"{path}: enum")
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        out.append(f"{path}: pattern")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            out.append(f"{path}: minimum")
        if "maximum" in schema and value > schema["maximum"]:
            out.append(f"{path}: maximum")
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                out.append(f"{path}: required {name}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            out += [f"{path}: additional {name}" for name in value if name not in props]
        for name, sub in props.items():
            if name in value:
                out += json_schema_errors(sub, value[name], f"{path}.{name}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            out.append(f"{path}: length")
        for i, sub in enumerate(schema.get("prefixItems", [])[: len(value)]):
            out += json_schema_errors(sub, value[i], f"{path}[{i}]")
    for sub in schema.get("allOf", []):
        out += json_schema_errors(sub, value, path)
    if "if" in schema:
        branch = "then" if not json_schema_errors(schema["if"], value, path) else "else"
        if branch in schema:
            out += json_schema_errors(schema[branch], value, path)
    return out


class ConformanceExamples(unittest.TestCase):
    def test_there_are_examples_of_both_kinds_on_both_sides(self):
        for folder in ("accept", "reject"):
            kinds = {case["kind"] for _, case in load(folder)}
            self.assertEqual(kinds, {"record", "judgement"}, folder)

    def test_every_accept_example_yields_a_valid_record(self):
        for name, case in load("accept"):
            with self.subTest(name):
                if case["kind"] == "record":
                    record = s.validate_record(case["record"])
                else:
                    record = assemble(case).record
                self.assertEqual(s.validate_record(record.as_dict()), record)

    def test_every_assembled_record_equals_the_expected_record_field_by_field(self):
        """The expected records were written out by hand (plain arithmetic), so a field taken from the
        wrong place in assemble_record shows up here."""
        seen = 0
        for name, case in load("accept"):
            if case["kind"] != "judgement":
                continue
            with self.subTest(name):
                got, want = assemble(case).record.as_dict(), case["expected_record"]
                self.assertEqual(set(got), set(want))
                for field in want:
                    if field in ("ess_like_0_100", "uncertainty_entropy"):
                        self.assertAlmostEqual(got[field], want[field], places=12, msg=field)
                    else:
                        self.assertEqual(got[field], want[field], field)
                seen += 1
        self.assertGreaterEqual(seen, 5)

    def test_examples_use_distinct_non_trivial_values(self):
        """Fixtures where every case shares one value cannot tell where a field came from."""
        cases = [case for _, case in load("accept") if case["kind"] == "judgement"]
        hashes = {case["scorer_info"]["prompt_sha256"] for case in cases}
        self.assertGreaterEqual(len(hashes), 2)
        self.assertNotIn("0" * 64, hashes)
        for field in ("event_type", "target_kind", "entity_id", "origin_cluster_id", "relevance_0_100",
                      "model_version", "market_confirmation"):
            self.assertGreaterEqual(len({str(case["expected_record"][field]) for case in cases}), 2, field)
        with_target = [case for case in cases if case["judgement"]["target_kind"] != "none"]
        self.assertGreaterEqual(len(with_target), 3)
        for case in with_target:
            self.assertNotEqual(case["expected_record"]["relevance_0_100"], 100 * case["judgement"]["p_subject"])
        for case in cases:
            self.assertNotEqual(case["expected_record"]["origin_cluster_id"], case["judgement"]["article_id"])

    def test_every_reject_example_raises_schema_error_with_the_stated_reason(self):
        for name, case in load("reject"):
            with self.subTest(name):
                with self.assertRaises(s.SchemaError) as caught:
                    if case["kind"] == "record":
                        s.validate_record(case["record"])
                    else:
                        j.validate_judgement(case["judgement"], j.validate_request(case["request"]))
                self.assertIn(case["expect"], str(caught.exception))

    def test_reject_examples_cover_many_distinct_reasons(self):
        reasons = [case["expect"] for _, case in load("reject")]
        self.assertGreaterEqual(len(set(reasons)), 30)

    def test_example_article_text_is_short_and_marked_synthetic(self):
        for folder in ("accept", "reject"):
            for name, case in load(folder):
                request = case.get("request") or {}
                for key in ("title", "body"):
                    text = request.get(key) or ""
                    self.assertLess(len(text), 120, name)
                    self.assertTrue(not text or "합성" in text or "Synthetic" in text, name)


class JsonSchemaFiles(unittest.TestCase):
    def test_files_match_the_code(self):
        self.assertEqual(export_schema.check(), [])
        self.assertEqual(export_schema.main(["--check"]), 0)

    def test_check_reports_a_stale_file(self):
        path = SCHEMA_DIR / "didm-score-v0.schema.json"
        original = export_schema.targets
        try:
            export_schema.targets = lambda: {path: original()[path] + " "}
            self.assertTrue(any("differs from the code" in line for line in export_schema.check()))
        finally:
            export_schema.targets = original

    def test_score_schema_lists_the_enum_and_required_fields_of_the_code(self):
        data = json.loads((SCHEMA_DIR / "didm-score-v0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(data["properties"]["event_type"]["enum"], [e.value for e in s.EventType])
        self.assertEqual(len(data["properties"]["event_type"]["enum"]), 15)
        self.assertEqual(tuple(data["required"]), s.REQUIRED)
        self.assertEqual(set(data["properties"]), set(s.REQUIRED) | {"schema_version"})
        self.assertEqual(data["properties"]["schema_version"]["const"], s.SCHEMA_VERSION)
        self.assertEqual(data["properties"]["market_confirmation"]["enum"], [e.value for e in s.MarketConfirmation])

    def test_judgement_schema_lists_the_fields_of_the_code(self):
        data = json.loads((SCHEMA_DIR / "didm-judgement-v0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(tuple(data["required"]), j.JUDGEMENT_REQUIRED)
        self.assertEqual(data["properties"]["event_type"]["enum"], [e.value for e in s.EventType])
        self.assertEqual(data["properties"]["event_type_probs"]["required"], [e.value for e in s.EventType])
        self.assertEqual(data["properties"]["claim_status"]["enum"], list(j.CLAIM_STATUSES))

    def test_json_schema_agrees_with_the_python_validators_on_the_examples(self):
        schemas = {
            "record": json.loads((SCHEMA_DIR / "didm-score-v0.schema.json").read_text(encoding="utf-8")),
            "judgement": json.loads((SCHEMA_DIR / "didm-judgement-v0.schema.json").read_text(encoding="utf-8")),
        }
        for name, case in load("accept"):
            with self.subTest(name):
                self.assertEqual(json_schema_errors(schemas[case["kind"]], case[case["kind"]]), [])
                if case["kind"] == "judgement":
                    self.assertEqual(json_schema_errors(schemas["record"], assemble(case).record.as_dict()), [])
        detected = 0
        for name, case in load("reject"):
            with self.subTest(name):
                errors = json_schema_errors(schemas[case["kind"]], case[case["kind"]])
                self.assertEqual(bool(errors), case["json_schema_detects"], errors)
                detected += bool(errors)
        self.assertGreaterEqual(detected, 20)


class FieldSplit(unittest.TestCase):
    def test_every_record_field_has_exactly_one_origin(self):
        origins = sc.ASSEMBLY_FIELDS + sc.DERIVED_FIELDS + sc.JUDGEMENT_TO_RECORD + sc.SCORER_INFO_FIELDS
        self.assertEqual(len(origins), len(set(origins)))
        self.assertEqual(set(origins), set(s.REQUIRED))

    def test_a_judgement_carries_no_didm_side_field(self):
        model_made = set(j.JUDGEMENT_REQUIRED)
        self.assertFalse(model_made & set(sc.ASSEMBLY_FIELDS))
        self.assertFalse(model_made & set(sc.DERIVED_FIELDS))
        self.assertFalse(model_made & set(sc.SCORER_INFO_FIELDS))
        for name in ("novelty_0_100", "origin_cluster_id", "p_credibility", "market_confirmation", "received_at"):
            self.assertIn(name, sc.ASSEMBLY_FIELDS)

    def test_judgement_round_trip(self):
        for name, case in load("accept"):
            if case["kind"] == "judgement":
                with self.subTest(name):
                    request = j.validate_request(case["request"])
                    judgement = j.validate_judgement(case["judgement"], request)
                    self.assertEqual(j.validate_judgement(judgement.as_dict(), request), judgement)

    def test_judgement_error_is_a_schema_error(self):
        self.assertTrue(issubclass(j.JudgementError, s.SchemaError))


def a_case() -> dict:
    return dict(load("accept"))["judgement-macro.json"]


class Assembly(unittest.TestCase):
    def test_derived_fields_follow_the_direction_probabilities(self):
        out = assemble(a_case())
        self.assertAlmostEqual(out.record.ess_like_0_100, 50 + 50 * (0.1 - 0.7))
        self.assertAlmostEqual(out.record.uncertainty_entropy, s.entropy([0.1, 0.7, 0.2]))
        self.assertEqual(out.calibration_version, sc.UNCALIBRATED)
        self.assertEqual(out.record.novelty_0_100, 97.5)
        self.assertEqual(out.record.model_version, "fixture-model-0")
        self.assertEqual(out.p_subject_raw, 0.92)
        self.assertEqual(out.claim_status, "confirmed")

    def test_calibrator_changes_the_record_and_keeps_the_raw_values(self):
        case = a_case()
        request = j.validate_request(case["request"])
        judgement = j.validate_judgement(case["judgement"], request)
        out = sc.assemble_record(judgement, sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"]),
                                 calibrate_direction=lambda p: (0.2, 0.5, 0.3), calibration_version="cal-fixture-1")
        self.assertEqual(out.record.direction_probs, (0.2, 0.5, 0.3))
        self.assertAlmostEqual(out.record.ess_like_0_100, 35.0)
        self.assertEqual(out.raw_direction_probs, (0.1, 0.7, 0.2))
        self.assertEqual(out.calibration_version, "cal-fixture-1")

    def test_calibrator_and_version_come_together(self):
        case = a_case()
        judgement = j.validate_judgement(case["judgement"], j.validate_request(case["request"]))
        info, asm = sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"])
        with self.assertRaises(j.JudgementError):
            sc.assemble_record(judgement, info, asm, calibrate_direction=lambda p: p)
        with self.assertRaises(j.JudgementError):
            sc.assemble_record(judgement, info, asm, calibration_version="cal-fixture-1")

    def test_bad_calibrator_output_is_rejected(self):
        case = a_case()
        judgement = j.validate_judgement(case["judgement"], j.validate_request(case["request"]))
        info, asm = sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"])
        for bad in ((0.5, 0.5, 0.5), (1.2, -0.2, 0.0), (0.5, 0.5), "abc", (float("nan"), 0.5, 0.5),
                    (10 ** 400, 0.0, 0.0), (0.5000004, 0.5000004, 0.0)):
            with self.subTest(bad=bad), self.assertRaises(s.SchemaError):
                sc.assemble_record(judgement, info, asm, calibrate_direction=lambda p, bad=bad: bad,
                                   calibration_version="cal-fixture-1")

    def test_bad_didm_side_values_are_rejected_by_the_record_schema(self):
        case = a_case()
        judgement = j.validate_judgement(case["judgement"], j.validate_request(case["request"]))
        info = sc.ScorerInfo(**case["scorer_info"])
        for field, bad in (("novelty_0_100", 120.0), ("received_at", "2026-11-05T19:15:00"),
                           ("market_confirmation", "MAYBE"), ("p_credibility", -0.1), ("record_id", ""),
                           ("relevance_0_100", 10 ** 400), ("record_id", "conf-j-0001\n")):
            with self.subTest(field=field), self.assertRaises(s.SchemaError):
                sc.assemble_record(judgement, info, sc.Assembly(**dict(case["assembly"], **{field: bad})))

    def test_model_output_never_changes_a_didm_side_field(self):
        """Whatever the model says, the nine ASSEMBLY_FIELDS of the record are the Assembly's."""
        case = a_case()
        request = j.validate_request(case["request"])
        info, asm = sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"])
        base = sc.assemble_record(j.validate_judgement(case["judgement"], request), info, asm).record.as_dict()
        flat = {t.value: 1 / 15 for t in s.EventType}
        variants = (dict(p_subject=0.0), dict(p_subject=1.0), dict(claim_status="reported"),
                    dict(direction_probs=[0.9, 0.05, 0.05]), dict(event_type="none", event_type_probs=flat),
                    dict(event_type="earnings", event_type_probs=flat))
        for change in variants:
            with self.subTest(change=sorted(change)):
                raw = dict(case["judgement"], **change)
                got = sc.assemble_record(j.validate_judgement(raw, request), info, asm).record.as_dict()
                for field in sc.ASSEMBLY_FIELDS:
                    self.assertEqual(got[field], base[field], field)
                self.assertEqual((got["model_version"], got["prompt_sha256"]),
                                 (info.model_version, info.prompt_sha256))
                self.assertEqual(got["event_type"], raw["event_type"])
                self.assertEqual(got["direction_probs"], raw["direction_probs"])
        self.assertEqual(len(sc.ASSEMBLY_FIELDS), 9)

    def test_scorer_info_reaches_the_record(self):
        case = a_case()
        judgement = j.validate_judgement(case["judgement"], j.validate_request(case["request"]))
        info = sc.ScorerInfo("another-model-7", "5" * 64)
        record = sc.assemble_record(judgement, info, sc.Assembly(**case["assembly"])).record
        self.assertEqual((record.model_version, record.prompt_sha256), ("another-model-7", "5" * 64))

    def test_assembly_for_another_article_or_target_is_refused(self):
        """A judgement cannot be joined to DIDM-side values computed for something else."""
        cases = dict(load("accept"))
        macro, firm = cases["judgement-macro.json"], cases["judgement-firm-ko.json"]
        judgement = j.validate_judgement(firm["judgement"], j.validate_request(firm["request"]))
        info = sc.ScorerInfo(**firm["scorer_info"])
        with self.assertRaisesRegex(j.JudgementError, "another article"):
            sc.assemble_record(judgement, info, sc.Assembly(**macro["assembly"]))
        for change, reason in ((dict(entity_id="KR:000660"), "another target"),
                               (dict(target_kind="macro"), "another target"),
                               (dict(target_kind="company"), "target_kind must be"),
                               (dict(article_id="art-0002x"), "another article")):
            with self.subTest(change=change), self.assertRaisesRegex(j.JudgementError, reason):
                sc.assemble_record(judgement, info, sc.Assembly(**dict(firm["assembly"], **change)))
        self.assertEqual(sc.ASSEMBLY_KEYS, ("article_id", "target_kind", "entity_id"))

    def test_a_judgement_needs_its_request(self):
        case = a_case()
        with self.assertRaises(TypeError):
            j.validate_judgement(case["judgement"])
        with self.assertRaises(j.JudgementError):
            j.validate_judgement(case["judgement"], None)
        with self.assertRaises(j.JudgementError):
            j.validate_judgement(case["judgement"], case["request"])      # a raw mapping is not a ScoreRequest

    def test_unvalidated_judgement_is_refused(self):
        case = a_case()
        with self.assertRaises(j.JudgementError):
            sc.assemble_record(case["judgement"], sc.ScorerInfo(**case["scorer_info"]),
                               sc.Assembly(**case["assembly"]))


class ScorerInfoRules(unittest.TestCase):
    def test_temperature_must_be_zero(self):
        for bad in (0.7, 1, True, "0", None):
            with self.subTest(bad=bad), self.assertRaises(j.JudgementError):
                sc.ScorerInfo("m", "0" * 64, bad)
        self.assertEqual(sc.ScorerInfo("m", "0" * 64, 0).temperature, 0)

    def test_model_version_and_hash(self):
        for version, sha in (("", "0" * 64), ("  ", "0" * 64), ("m", "0" * 63), ("m", "G" * 64), (None, "0" * 64)):
            with self.subTest(version=version, sha=sha), self.assertRaises(j.JudgementError):
                sc.ScorerInfo(version, sha)


class FakeScorer:
    """Stands in for any scorer: returns canned mappings, calls nothing."""
    def __init__(self, answers: dict):
        self.info = sc.ScorerInfo("fixture-model-0", "0" * 64)
        self.answers = answers
        self.calls: list[str] = []

    def judge(self, request):
        self.calls.append(request.article_id)
        answer = self.answers[request.article_id]
        if isinstance(answer, Exception):
            raise answer
        return answer


class RunScorer(unittest.TestCase):
    def setUp(self):
        case = a_case()
        self.request = j.validate_request(case["request"])
        self.good = case["judgement"]

    def test_valid_judgements_are_kept_and_bad_ones_counted_once(self):
        r2 = j.validate_request(dict(a_case()["request"], article_id="art-0002x"))
        r3 = j.validate_request(dict(a_case()["request"], article_id="art-0003x"))
        scorer = FakeScorer({"art-0001": self.good,
                             "art-0002x": dict(self.good, article_id="art-0002x", rationale="text"),
                             "art-0003x": "not json"})
        batch = sc.run_scorer(scorer, [self.request, r2, r3])
        self.assertEqual([req.article_id for req, _ in batch.judgements], ["art-0001"])
        self.assertEqual([a for a, _ in batch.rejected], ["art-0002x", "art-0003x"])
        self.assertEqual(sum(batch.reject_counts.values()), 2)
        self.assertEqual(scorer.calls, ["art-0001", "art-0002x", "art-0003x"])   # one call each, no retry

    def test_a_judgement_for_another_article_is_not_attached(self):
        scorer = FakeScorer({"art-0001": dict(self.good, article_id="art-7777")})
        batch = sc.run_scorer(scorer, [self.request])
        self.assertEqual(batch.judgements, ())
        self.assertIn("article_id does not match", batch.rejected[0][1])

    def test_scorer_failures_other_than_schema_errors_are_not_swallowed(self):
        scorer = FakeScorer({"art-0001": RuntimeError("backend down")})
        with self.assertRaises(RuntimeError):
            sc.run_scorer(scorer, [self.request])

    def test_reject_reasons_never_carry_model_output(self):
        leak = "FULL ARTICLE TEXT " * 40
        requests, answers = [], {}
        bad_outputs = (dict(self.good, event_type=leak), dict(self.good, claim_status=leak),
                       dict(self.good, target_kind=leak), {**self.good, leak: 1},
                       dict(self.good, event_type_probs={**self.good["event_type_probs"], leak: 0.0}),
                       dict(self.good, entity_id=leak), dict(self.good, article_id=leak),
                       dict(self.good, judgement_version=leak), dict(self.good, p_subject=leak),
                       dict(self.good, direction_probs=[leak, 0.5, 0.5]), leak, [leak])
        for i, output in enumerate(bad_outputs):
            request = j.validate_request(dict(a_case()["request"], article_id=f"art-leak-{i}"))
            requests.append(request)
            answers[request.article_id] = (dict(output, article_id=request.article_id)
                                           if isinstance(output, dict) and output.get("article_id") != leak
                                           else output)
        batch = sc.run_scorer(FakeScorer(answers), requests)
        self.assertEqual(len(batch.rejected), len(bad_outputs))
        for article_id, reason in batch.rejected:
            self.assertNotIn("FULL ARTICLE", reason, article_id)
            self.assertLess(len(reason), 90, reason)
        # one key per rule, not one per offending value
        two = sc.run_scorer(FakeScorer({"art-leak-0": dict(self.good, article_id="art-leak-0", event_type="aaa"),
                                        "art-leak-1": dict(self.good, article_id="art-leak-1", event_type="bbb")}),
                            requests[:2])
        self.assertEqual(two.reject_counts, {"unknown event_type": 2})

    def test_a_huge_integer_is_a_counted_rejection_not_a_crash(self):
        for field, value in (("p_subject", 10 ** 400), ("direction_probs", [10 ** 400, 0.0, 0.0]),
                             ("event_type_probs", dict(self.good["event_type_probs"], none=10 ** 400))):
            with self.subTest(field=field):
                scorer = FakeScorer({"art-0001": dict(self.good, **{field: value})})
                batch = sc.run_scorer(scorer, [self.request])
                self.assertEqual(batch.judgements, ())
                self.assertIn("must be finite", batch.rejected[0][1])

    def test_a_kept_judgement_can_always_be_assembled(self):
        """What run_scorer keeps, assemble_record accepts: P(+1) + P(-1) above 1 is rejected up front."""
        scorer = FakeScorer({"art-0001": dict(self.good, direction_probs=[0.5000004, 0.5000004, 0.0])})
        batch = sc.run_scorer(scorer, [self.request])
        self.assertEqual(batch.judgements, ())
        self.assertEqual(batch.reject_counts, {"p_positive + p_negative exceeds 1": 1})

    def test_object_without_info_is_not_a_scorer(self):
        class NoInfo:
            def judge(self, request):
                return {}
        with self.assertRaises(j.JudgementError):
            sc.run_scorer(NoInfo(), [self.request])

    def test_fake_scorer_satisfies_the_protocol(self):
        self.assertIsInstance(FakeScorer({}), sc.Scorer)


class RequestRules(unittest.TestCase):
    def test_request_rejections(self):
        base = a_case()["request"]
        cases = ((dict(base, language="fr"), "language must be"), (dict(base, title=" "), "title must be"),
                 (dict(base, body=5), "body must be"), (dict(base, entity_name=None), "entity_name must be a non-empty"),
                 (dict(base, target_kind="none"), "entity_id must be null"), (dict(base, extra=1), "unknown request fields"),
                 (dict(base, target_kind="none", entity_id=None), "entity_name must be null"),
                 (dict(base, target_kind="firm", entity_id=None), "entity_id must be an identifier"),
                 ({k: v for k, v in base.items() if k != "body"}, "missing request field: body"))
        for raw, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(j.JudgementError, reason):
                j.validate_request(raw)
        none = j.validate_request(dict(base, target_kind="none", entity_id=None, entity_name=None))
        self.assertIsNone(none.entity_name)


class Tolerances(unittest.TestCase):
    def test_sum_tolerance_is_1e_6_and_the_schema_text_follows_the_code(self):
        self.assertEqual(j.SUM_TOLERANCE, 1e-6)
        rules = export_schema.judgement_schema()["x-didm-cross-field-rules"]
        self.assertIn("event_type_probs sums to 1 within 1e-06", rules)
        self.assertIn("direction_probs sums to 1 within 1e-06", rules)
        original = j.SUM_TOLERANCE
        try:
            j.SUM_TOLERANCE = 1e-3
            import importlib
            importlib.reload(export_schema)
            self.assertTrue(any("differs from the code" in line for line in export_schema.check()))
        finally:
            j.SUM_TOLERANCE = original
            importlib.reload(export_schema)
        self.assertEqual(export_schema.check(), [])

    def test_boundary_examples_exist_on_both_sides(self):
        accept, reject = dict(load("accept")), dict(load("reject"))
        inside = accept["judgement-sums-inside-tolerance.json"]["judgement"]
        self.assertAlmostEqual(abs(sum(inside["direction_probs"]) - 1), 5e-7, places=9)
        self.assertAlmostEqual(abs(sum(inside["event_type_probs"].values()) - 1), 5e-7, places=9)
        for name in ("judgement-direction-sum-just-outside.json", "judgement-type-probs-sum-just-outside.json"):
            raw = reject[name]["judgement"]
            total = sum(raw["direction_probs"]) if "direction" in name else sum(raw["event_type_probs"].values())
            self.assertAlmostEqual(abs(total - 1), 2e-6, places=9)

    def test_exported_patterns_refuse_a_trailing_newline_under_search(self):
        import re
        for pattern, good in ((export_schema.ID_PATTERN, "conf-0001"), (export_schema.SHA_PATTERN, "a" * 64)):
            self.assertTrue(re.search(pattern, good))
            self.assertFalse(re.search(pattern, good + "\n"))
            self.assertFalse(re.search(pattern, good + "\n\n"))


class Boundaries(unittest.TestCase):
    FILES = ("core/didm/llm/judgement.py", "core/didm/llm/scorer.py", "core/didm/llm/cutoffs.py",
             "tools/didm/export_schema.py")
    BANNED = ("data", "requests", "urllib", "http", "socket", "ssl", "ftplib", "smtplib", "jsonschema", "pydantic",
              "time", "anthropic", "openai", "transformers", "torch", "subprocess")
    CLOCK_CALLS = ("now", "today", "utcnow", "fromtimestamp", "time", "monotonic", "perf_counter")

    @staticmethod
    def imported(tree: ast.AST) -> list[str]:
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names.append(module)
                names += [f"{module}.{a.name}" if module else a.name for a in node.names]
        return names

    def problems(self, source: str) -> list[str]:
        tree = ast.parse(source)
        found = [f"import {name}" for name in self.imported(tree) if name.split(".")[0] in self.BANNED]
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name in self.CLOCK_CALLS:
                    found.append(f"call {name}()")
        return found

    def test_no_provider_network_clock_or_validator_library(self):
        for rel in self.FILES:
            with self.subTest(rel):
                self.assertEqual(self.problems((ROOT / rel).read_text(encoding="utf-8")), [])

    def test_the_check_sees_ordinary_import_and_clock_forms(self):
        for line in ("from urllib.request import urlopen", "import http.client", "from data import didm",
                     "import data.didm.keys as k", "import socket", "from time import sleep",
                     "from datetime import datetime\nx = datetime.now()", "import datetime\nx = datetime.date.today()",
                     "from datetime import datetime, timezone\n_STARTED = datetime.now(timezone.utc)",
                     "from datetime import datetime\nx = datetime.utcnow()"):
            with self.subTest(line=line):
                self.assertNotEqual(self.problems(line), [])
        self.assertEqual(self.problems("from datetime import date, datetime, timezone\nx = date(2026, 1, 1)"), [])

    def test_schema_py_still_has_the_v0_surface(self):
        self.assertEqual(s.SCHEMA_VERSION, "didm-score-v0")
        self.assertEqual(len(s.REQUIRED), 17)
        self.assertEqual(len(s.EventType), 15)


if __name__ == "__main__":
    unittest.main()
