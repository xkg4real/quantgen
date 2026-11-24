"""Replay with the fake backend: the same request gives the same envelope; cut-off and failed runs are errors."""
import copy
import itertools
import unittest

import _path  # noqa: F401

from quantgpt import envelope as E
from quantgpt import pipeline
from quantgpt.backends.fake import FakeBackend
from quantgpt.policy import SEED_RULES

REPORT = {"as_of": "2026-11-03", "sharpe": 0.42, "ann_vol": 0.153}
EXPLAIN = {"task": "T-EXPLAIN", "mode": "tool", "input": {"report": REPORT, "language": "ko"}}
QA = {"task": "T-QA", "mode": "tool", "input": {"question": "샤프 비율이 무엇인가요?", "as_of": "2026-11-24",
                                                "language": "ko"}}
EVIDENCE = {"doc:sharpe": "2025-01-10", "doc:late": "2026-12-01"}
SCRIPT = {
    "T-EXPLAIN": {"body": {"summary": "샤프 비율은 0.42입니다.", "points": ["연 변동성은 15.3%입니다."]}},
    "T-QA": {"body": {"answer": "초과수익을 변동성으로 나눈 값입니다."},
             "citations": [{"source_id": "doc:sharpe", "as_of": "2025-01-10"}]},
}


def settings(**changes):
    ticks = itertools.count()
    base = dict(rules=SEED_RULES, evidence=EVIDENCE, clock=lambda: next(ticks) * 0.25)
    base.update(changes)
    return pipeline.Settings(**base)


def answer(request, script=None, **changes):
    backend = FakeBackend(SCRIPT if script is None else script)
    return pipeline.run(request, backend, settings(**changes)), backend


class ReplayTests(unittest.TestCase):
    def test_the_same_request_gives_the_same_envelope(self):
        for request in (EXPLAIN, QA):
            first, backend = answer(request)
            second, _ = answer(copy.deepcopy(request))
            self.assertEqual(first["status"], "ok")
            self.assertEqual(E.canonical_json(first), E.canonical_json(second))
            self.assertEqual(first["request_sha256"], backend.calls[0])
            self.assertEqual(first["latency_ms"], 250)
            E.validate_envelope(first, pipeline.CONTRACTS[request["task"]].output)

    def test_key_order_does_not_change_the_request_hash_but_content_does(self):
        reordered = {"mode": "tool", "input": {"language": "ko", "report": dict(reversed(list(REPORT.items())))},
                     "task": "T-EXPLAIN"}
        base, _ = answer(EXPLAIN)
        self.assertEqual(answer(reordered)[0]["request_sha256"], base["request_sha256"])
        changed = copy.deepcopy(EXPLAIN); changed["input"]["report"]["sharpe"] = 0.43
        self.assertNotEqual(answer(changed)[0]["request_sha256"], base["request_sha256"])
        other_prompt, _ = answer(EXPLAIN, prompt_version="p1")
        self.assertNotEqual(other_prompt["request_sha256"], base["request_sha256"])
        other_model = pipeline.run(EXPLAIN, FakeBackend(SCRIPT, model_id="fake-1"), settings())
        self.assertNotEqual(other_model["request_sha256"], base["request_sha256"])
        with_adapter = pipeline.run(EXPLAIN, FakeBackend(SCRIPT, adapter="lora-a"), settings())
        self.assertNotEqual(with_adapter["request_sha256"], base["request_sha256"])
        self.assertEqual(with_adapter["model"], {"id": "fake-0", "adapter": "lora-a", "prompt_version": "p0"})

    def test_the_model_cannot_write_the_envelope_fields(self):
        forged = {"body": SCRIPT["T-EXPLAIN"]["body"], "numbers": [], "policy": {"violations": []}, "status": "ok"}
        env, _ = answer(EXPLAIN, {"T-EXPLAIN": forged})
        self.assertEqual((env["status"], env["reason_code"], env["body"]), ("error", "invalid_output", None))


class StopAndLengthTests(unittest.TestCase):
    def test_a_cut_off_answer_is_an_error_even_when_the_cut_text_parses(self):
        env, _ = answer(EXPLAIN, max_tokens=40)
        self.assertEqual((env["status"], env["reason_code"], env["body"]), ("error", "truncated", None))
        whole = '{"body": {"summary": "s", "points": ["p"]}}'
        env, _ = answer(EXPLAIN, {"T-EXPLAIN": whole + " " * 50}, max_tokens=len(whole))
        self.assertEqual((env["status"], env["reason_code"]), ("error", "truncated"))
        env, _ = answer(EXPLAIN, {"T-EXPLAIN": whole}, max_tokens=len(whole))
        self.assertEqual(env["status"], "ok")

    def test_backend_failures_and_unknown_stop_reasons(self):
        env = pipeline.run(EXPLAIN, FakeBackend(SCRIPT, fail="timeout"), settings())
        self.assertEqual((env["status"], env["reason_code"]), ("error", "backend"))

        class Odd(FakeBackend):
            def generate(self, *args, **kwargs):
                from quantgpt.backends.base import Generation
                return Generation("{}", "content_filter")
        env = pipeline.run(EXPLAIN, Odd(SCRIPT), settings())
        self.assertEqual((env["status"], env["reason_code"]), ("error", "backend"))

    def test_malformed_output(self):
        outputs = ["", "not json", "[1, 2]", '{"body": {"summary": "s"}}', '{"body": {"summary": "s", "points": '
                   '["p"]}, "order": {"side": "buy"}}', '{"body": {"summary": "s", "points": ["p"], "x": NaN}}',
                   '{"body": {"summary": "s", "points": ["p"]}} trailing', '{"answer": "a"}']
        for text in outputs:
            with self.subTest(text=text[:30]):
                env, _ = answer(EXPLAIN, {"T-EXPLAIN": text})
                self.assertEqual((env["status"], env["reason_code"], env["body"]), ("error", "invalid_output", None))


class OutcomeTests(unittest.TestCase):
    def script(self, task, body, citations=None):
        produced = {"body": body}
        if citations is not None:
            produced["citations"] = citations
        return {task: produced}

    def test_policy_blocks_in_tool_mode_and_is_recorded_in_owner_mode(self):
        body = {"summary": "샤프 비율은 0.42입니다. 매수하세요.", "points": ["변동성은 15.3%입니다."]}
        env, _ = answer(EXPLAIN, self.script("T-EXPLAIN", body))
        self.assertEqual((env["status"], env["reason_code"], env["body"]), ("blocked", "policy", None))
        self.assertEqual(env["policy"]["violations"], ["PF-1"])
        owner, _ = answer({**EXPLAIN, "mode": "owner"}, self.script("T-EXPLAIN", body))
        self.assertEqual((owner["status"], owner["policy"]["violations"]), ("ok", ["PF-1"]))
        self.assertEqual(E.display_body(owner), body)

    def test_an_invented_number_is_an_abstention_in_tool_mode(self):
        body = {"summary": "샤프 비율은 1.37입니다.", "points": ["변동성은 15.3%입니다."]}
        env, _ = answer(EXPLAIN, self.script("T-EXPLAIN", body))
        self.assertEqual((env["status"], env["reason_code"], env["body"]), ("abstain", "number_not_in_payload", None))
        # The fake backend writes keys in sorted order, so "points" is read before "summary".
        self.assertEqual(env["numbers"], [{"text": "15.3%", "found_in_payload": True},
                                          {"text": "1.37", "found_in_payload": False}])
        owner, _ = answer({**EXPLAIN, "mode": "owner"}, self.script("T-EXPLAIN", body))
        self.assertEqual(owner["status"], "ok")
        self.assertEqual(owner["numbers"][1], {"text": "1.37", "found_in_payload": False})

    def test_blocked_comes_before_abstain(self):
        body = {"summary": "샤프 비율은 1.37입니다. 매수하세요.", "points": ["p"]}
        env, _ = answer(EXPLAIN, self.script("T-EXPLAIN", body))
        self.assertEqual((env["status"], env["reason_code"]), ("blocked", "policy"))

    def test_question_answers_need_known_evidence_dated_up_to_as_of(self):
        body = {"answer": "초과수익을 변동성으로 나눈 값입니다."}
        cases = [(None, "no_evidence"), ([], "no_evidence"),
                 ([{"source_id": "doc:made_up", "as_of": "2025-01-10"}], "citation_unknown"),
                 ([{"source_id": "doc:sharpe", "as_of": "2025-02-10"}], "citation_unknown"),
                 ([{"source_id": "doc:late", "as_of": "2026-12-01"}], "after_as_of")]
        for citations, reason in cases:
            for mode in ("tool", "owner"):
                with self.subTest(reason=reason, citations=citations, mode=mode):
                    env, _ = answer({**QA, "mode": mode}, self.script("T-QA", body, citations))
                    self.assertEqual((env["status"], env["reason_code"], env["body"]), ("abstain", reason, None))

    def test_text_about_a_later_date_is_an_abstention(self):
        good = [{"source_id": "doc:sharpe", "as_of": "2025-01-10"}]
        env, _ = answer(QA, self.script("T-QA", {"answer": "2026년 12월 10일 회의에서 정해졌습니다."}, good))
        self.assertEqual((env["status"], env["reason_code"]), ("abstain", "after_as_of"))
        events = [{"name": "12월 금리 결정", "date": "2026-12-10"}]
        env, _ = answer(QA, self.script("T-QA", {"answer": "12월 금리 결정 이후 달라졌습니다."}, good), events=events)
        self.assertEqual((env["status"], env["reason_code"]), ("abstain", "after_as_of"))

    def test_requests_that_never_reach_the_backend(self):
        research = {"task": "T-RESEARCH", "mode": "tool",
                    "input": {"topic": "t", "as_of": "2026-11-24", "language": "ko"}}
        cases = [("오늘 뭐 살까?", "blocked", "no_task_code", None, ["PF-6"]),
                 ({"mode": "tool", "input": {"text": "hello"}}, "blocked", "no_task_code", None, ["PF-6"]),
                 ({"task": "T-CHAT", "mode": "tool", "input": {}}, "blocked", "no_task_code", None, ["PF-6"]),
                 (research, "blocked", "task_not_allowed", "T-RESEARCH", []),
                 ({**EXPLAIN, "input": {"report": REPORT}}, "error", "invalid_input", "T-EXPLAIN", []),
                 ({**EXPLAIN, "mode": "root"}, "error", "invalid_input", "T-EXPLAIN", [])]
        for request, status, reason, task, violations in cases:
            with self.subTest(reason=reason, request=str(request)[:30]):
                env, backend = answer(request)
                self.assertEqual((env["status"], env["reason_code"], env["task"], env["policy"]["violations"]),
                                 (status, reason, task, violations))
                self.assertEqual(backend.calls, [])
                self.assertIsNone(E.display_body(env))
        env, backend = answer(EXPLAIN, enabled=False)
        self.assertEqual((env["status"], env["reason_code"], backend.calls), ("blocked", "disabled", []))

    def test_a_null_task_is_valid_only_for_free_chat(self):
        env, _ = answer("hello")
        E.validate_envelope(env)
        with self.assertRaises(E.SchemaError):
            E.validate_envelope({**env, "reason_code": "policy"})
        with self.assertRaises(E.SchemaError):
            E.validate_envelope({**env, "status": "error", "reason_code": "backend"})

    def test_every_outcome_is_a_valid_envelope_with_the_label(self):
        bodies = [SCRIPT, {"T-EXPLAIN": "junk"}, {"T-EXPLAIN": {"body": {"summary": "매수하세요", "points": ["p"]}}}]
        for script in bodies:
            for mode in ("tool", "owner"):
                env, _ = answer({**EXPLAIN, "mode": mode}, script)
                E.validate_envelope(env)
                self.assertIn("검증 안 됨", env["label_ko"])
                self.assertNotIn("Claude", env["label_ko"])


if __name__ == "__main__":
    unittest.main()
