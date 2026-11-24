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

    def test_every_reject_example_raises_schema_error_with_the_stated_reason(self):
        for name, case in load("reject"):
            with self.subTest(name):
                with self.assertRaises(s.SchemaError) as caught:
                    if case["kind"] == "record":
                        s.validate_record(case["record"])
                    else:
                        j.validate_judgement(case["judgement"], j.validate_request(case["request"]))
                self.assertIn(case["expect"], str(caught.exception))

    def test_reject_examples_fail_for_one_reason_only(self):
        """Each reject example is an accept example with one thing wrong, so the reason is the one tested."""
        reasons = [case["expect"] for _, case in load("reject")]
        self.assertGreaterEqual(len(set(reasons)), 25)

    def test_examples_contain_no_secret_looking_or_long_text(self):
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
        judgement = j.validate_judgement(case["judgement"])
        info, asm = sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"])
        with self.assertRaises(j.JudgementError):
            sc.assemble_record(judgement, info, asm, calibrate_direction=lambda p: p)
        with self.assertRaises(j.JudgementError):
            sc.assemble_record(judgement, info, asm, calibration_version="cal-fixture-1")

    def test_bad_calibrator_output_is_rejected(self):
        case = a_case()
        judgement = j.validate_judgement(case["judgement"])
        info, asm = sc.ScorerInfo(**case["scorer_info"]), sc.Assembly(**case["assembly"])
        for bad in ((0.5, 0.5, 0.5), (1.2, -0.2, 0.0), (0.5, 0.5), "abc", (float("nan"), 0.5, 0.5)):
            with self.subTest(bad=bad), self.assertRaises(s.SchemaError):
                sc.assemble_record(judgement, info, asm, calibrate_direction=lambda p, bad=bad: bad,
                                   calibration_version="cal-fixture-1")

    def test_bad_didm_side_values_are_rejected_by_the_record_schema(self):
        case = a_case()
        judgement = j.validate_judgement(case["judgement"])
        info = sc.ScorerInfo(**case["scorer_info"])
        for field, bad in (("novelty_0_100", 120.0), ("received_at", "2026-11-05T19:15:00"),
                           ("market_confirmation", "MAYBE"), ("p_credibility", -0.1), ("record_id", "")):
            with self.subTest(field=field), self.assertRaises(s.SchemaError):
                sc.assemble_record(judgement, info, sc.Assembly(**dict(case["assembly"], **{field: bad})))

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
        cases = (dict(base, language="fr"), dict(base, title=" "), dict(base, body=5), dict(base, entity_name=None),
                 dict(base, target_kind="none"), dict(base, extra=1),
                 {k: v for k, v in base.items() if k != "body"})
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(j.JudgementError):
                j.validate_request(raw)


class Boundaries(unittest.TestCase):
    FILES = ("core/didm/llm/judgement.py", "core/didm/llm/scorer.py", "tools/didm/export_schema.py")
    BANNED = ("data", "requests", "urllib", "http", "socket", "jsonschema", "pydantic", "time", "anthropic", "openai",
              "transformers", "torch")

    def test_no_provider_network_clock_or_validator_library_imports(self):
        for rel in self.FILES:
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    self.assertNotIn(name.split(".")[0], self.BANNED, f"{rel} imports {name}")

    def test_schema_py_still_has_the_v0_surface(self):
        self.assertEqual(s.SCHEMA_VERSION, "didm-score-v0")
        self.assertEqual(len(s.REQUIRED), 17)
        self.assertEqual(len(s.EventType), 15)


if __name__ == "__main__":
    unittest.main()
