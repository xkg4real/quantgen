"""Envelope qgpt-env-v1."""
import copy
import unittest

import _path  # noqa: F401

from quantgpt import envelope as E
from quantgpt.checks.schema import SchemaError
from quantgpt.contracts.tasks import CONTRACTS

HASH = E.request_sha256("T-EXPLAIN", "tool", {"report": {"sharpe": 0.42}, "language": "ko"}, "fake-0", None, "p1")
OK = {
    "envelope_version": "qgpt-env-v1", "task": "T-EXPLAIN", "mode": "tool", "status": "ok",
    "body": {"summary": "샤프 비율은 0.42입니다.", "points": ["변동성은 15.3%입니다."]},
    "numbers": [{"text": "0.42", "found_in_payload": True}, {"text": "15.3%", "found_in_payload": True}],
    "citations": [{"source_id": "card:S_E1_trend_krx", "as_of": "2026-09-27"}],
    "policy": {"violations": [], "rules_version": "pf-0"},
    "model": {"id": "fake-0", "adapter": None, "prompt_version": "p1"},
    "label_ko": "AI 해설 · 검증 안 됨", "latency_ms": 12, "request_sha256": HASH,
}
COMMON = dict(request_hash=HASH, model_id="fake-0", adapter=None, prompt_version="p1", rules_version="pf-0",
              label_ko="AI 해설 · 검증 안 됨")


def changed(**kwargs):
    env = copy.deepcopy(OK)
    env.update(kwargs)
    return env


class EnvelopeTests(unittest.TestCase):
    def test_valid_envelopes(self):
        E.validate_envelope(OK, CONTRACTS["T-EXPLAIN"].output)
        E.validate_envelope(changed(numbers=[], citations=[]))
        E.validate_envelope(changed(mode="owner", policy={"violations": ["PF-1"], "rules_version": "pf-0"}))
        E.validate_envelope(changed(mode="owner", numbers=[{"text": "9.99", "found_in_payload": False}]))
        E.validate_envelope(changed(status="abstain", body=None, reason_code="number_not_in_payload",
                                    numbers=[{"text": "9.99", "found_in_payload": False}]))
        E.validate_envelope(changed(status="blocked", body=None, reason_code="policy",
                                    policy={"violations": ["PF-1", "PF-4"], "rules_version": "pf-0"}))
        E.validate_envelope(changed(status="error", body=None))
        self.assertEqual(E.display_body(OK), OK["body"])

    def test_rejected_envelopes(self):
        bad = [
            changed(status="done"), changed(task="T-CHAT"), changed(mode="admin"), changed(body=None),
            changed(envelope_version="qgpt-env-v2"), changed(request_sha256="abc"), changed(latency_ms=-1),
            changed(latency_ms=1.5), changed(label_ko=""), changed(order={"side": "buy"}),
            changed(policy={"violations": ["PF-9"], "rules_version": "pf-0"}),
            changed(policy={"violations": ["PF-1", "PF-1"], "rules_version": "pf-0"}),
            changed(policy={"violations": ["PF-1"], "rules_version": "pf-0"}),             # tool + ok + violation
            changed(numbers=[{"text": "9.99", "found_in_payload": False}]),                # tool + ok + not found
            changed(citations=[{"source_id": "card:x", "as_of": "last week"}]),
            changed(model={"id": "", "adapter": None, "prompt_version": "p1"}),
            changed(reason_code="policy"),                                                 # ok carries no reason
            changed(status="blocked", reason_code="policy"),                               # body must be null
            changed(status="abstain", body=None, reason_code="policy"),                    # reason of another status
            changed(status="error", body=None, reason_code="made_up"),
            changed(task="T-RESEARCH"),                                                    # owner-only task in tool
            {k: v for k, v in OK.items() if k != "numbers"},
            "ok",
        ]
        for i, env in enumerate(bad):
            with self.subTest(i=i), self.assertRaises(SchemaError):
                E.validate_envelope(env)

    def test_the_body_contract_is_applied_to_an_ok_body_only(self):
        with self.assertRaises(SchemaError):
            E.validate_envelope(changed(body={"summary": "s", "points": ["p"], "action": "buy"}),
                                CONTRACTS["T-EXPLAIN"].output)
        E.validate_envelope(changed(status="error", body=None, reason_code="invalid_output"),
                            CONTRACTS["T-EXPLAIN"].output)

    def test_only_an_ok_envelope_has_a_displayable_body(self):
        for status in ("abstain", "blocked", "error"):
            self.assertIsNone(E.display_body(changed(status=status, body=None)))
        self.assertIsNone(E.display_body(changed(status="blocked")))       # invalid: blocked with a body
        self.assertIsNone(E.display_body(changed(policy={"violations": ["PF-1"], "rules_version": "pf-0"})))
        self.assertIsNone(E.display_body({"status": "ok", "body": {"summary": "s"}}))

    def test_refusals(self):
        env = E.refusal("T-QA", "tool", "abstain", "no_evidence", **COMMON)
        self.assertEqual((env["status"], env["body"], env["reason_code"]), ("abstain", None, "no_evidence"))
        env = E.refusal("T-PORT", "tool", "blocked", "policy", violations=("PF-1",), **COMMON)
        self.assertEqual(env["policy"]["violations"], ["PF-1"])
        E.refusal("T-RESEARCH", "tool", "blocked", "task_not_allowed", **COMMON)
        with self.assertRaises(SchemaError):
            E.refusal("T-QA", "tool", "ok", "no_evidence", **COMMON)
        with self.assertRaises(SchemaError):
            E.refusal("T-QA", "tool", "abstain", "backend", **COMMON)

    def test_request_hash_is_stable_and_sensitive(self):
        payload = {"language": "ko", "report": {"sharpe": 0.42}}
        self.assertEqual(E.request_sha256("T-EXPLAIN", "tool", payload, "fake-0", None, "p1"), HASH)
        for other in (E.request_sha256("T-PORT", "tool", payload, "fake-0", None, "p1"),
                      E.request_sha256("T-EXPLAIN", "owner", payload, "fake-0", None, "p1"),
                      E.request_sha256("T-EXPLAIN", "tool", payload, "fake-1", None, "p1"),
                      E.request_sha256("T-EXPLAIN", "tool", payload, "fake-0", "lora-a", "p1"),
                      E.request_sha256("T-EXPLAIN", "tool", payload, "fake-0", None, "p2"),
                      E.request_sha256("T-EXPLAIN", "tool", {**payload, "language": "en"}, "fake-0", None, "p1")):
            self.assertNotEqual(other, HASH)
        with self.assertRaises(ValueError):
            E.request_sha256("T-EXPLAIN", "tool", {"x": float("nan")}, "fake-0", None, "p1")


if __name__ == "__main__":
    unittest.main()
