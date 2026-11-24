"""Policy filter: a few synthetic sentences per rule; tool mode blocks, owner mode records."""
import unittest

import _path  # noqa: F401

from quantgpt import policy
from quantgpt.checks.schema import SchemaError
from quantgpt.envelope import POLICY_RULES

HIT = {
    "PF-1": ["이 종목은 매수하세요.", "You should sell before the close.", "보유를 권합니다."],
    "PF-2": ["지금 005930 사야 합니다.", "Today is a good time to buy AAA."],
    "PF-3": ["QUANTGEN의 권장 값은 20일입니다.", "Our recommended setting is 126 sessions."],
    "PF-4": ["다음 달에는 오를 것입니다.", "The price will rise to 100 by March.", "목표가는 10만 원입니다."],
    "PF-5": ["원금을 보장합니다.", "A guaranteed return of 10%.", "무조건 수익이 납니다."],
}
CLEAN = [
    "샤프 비율은 0.42이고 최대 낙폭은 18.8%입니다.",
    "이 규칙은 126일 이동평균 위에서만 보유하는 규칙입니다.",
    "과거 표본에서 변동성이 높은 구간의 성과가 더 좋았습니다.",
    "The backtest shows a deflated Sharpe ratio of 0.84 after 12 trials.",
    "매수와 매도 비용은 각각 3bp로 가정했습니다.",
    "This card was rejected by the validation gate.",
]


class FilterTests(unittest.TestCase):
    def test_rule_ids_match_the_envelope(self):
        self.assertEqual(policy.ALL_RULES, POLICY_RULES)
        self.assertEqual(policy.SEED_RULES.version, "pf-seed-0")
        self.assertLessEqual(policy.SEED_RULES.count(), 15)

    def test_each_rule_fires_on_its_examples(self):
        for rule, sentences in HIT.items():
            for sentence in sentences:
                with self.subTest(rule=rule, sentence=sentence):
                    self.assertIn(rule, policy.scan(sentence, policy.SEED_RULES))

    def test_descriptive_sentences_pass(self):
        for sentence in CLEAN:
            with self.subTest(sentence=sentence):
                self.assertEqual(policy.scan(sentence, policy.SEED_RULES), ())
        self.assertEqual(policy.scan("", policy.SEED_RULES), ())
        self.assertEqual(policy.scan(None, policy.SEED_RULES), ())

    def test_tool_mode_blocks_and_owner_mode_only_records(self):
        text = "매수하세요. 원금을 보장합니다."
        tool, owner = policy.decide(text, "tool", policy.SEED_RULES), policy.decide(text, "owner", policy.SEED_RULES)
        self.assertEqual(tool.violations, ("PF-1", "PF-5"))
        self.assertEqual(owner.violations, tool.violations)
        self.assertEqual((tool.blocked, owner.blocked), (True, False))
        self.assertEqual(tool.as_envelope(), {"violations": ["PF-1", "PF-5"], "rules_version": "pf-seed-0"})
        clean = policy.decide(CLEAN[0], "tool", policy.SEED_RULES)
        self.assertEqual((clean.violations, clean.blocked), ((), False))
        with self.assertRaises(ValueError):
            policy.decide(text, "admin", policy.SEED_RULES)

    def test_free_chat_is_pf6_and_blocked(self):
        decision = policy.free_chat(policy.SEED_RULES)
        self.assertEqual((decision.violations, decision.blocked), (("PF-6",), True))

    def test_rule_files(self):
        good = {"version": "pf-test-1", "rules": {rule: ["x" + rule[-1]] for rule in policy.filter.TEXT_RULES}}
        rules = policy.load_rules(good)
        self.assertEqual(policy.scan("abc x4 def", rules), ("PF-4",))
        bad = [
            {**good, "version": ""},
            {"version": "v", "rules": {k: v for k, v in good["rules"].items() if k != "PF-3"}},   # a rule dropped
            {"version": "v", "rules": {**good["rules"], "PF-2": []}},
            {"version": "v", "rules": {**good["rules"], "PF-6": ["chat"]}},                        # not a text rule
            {"version": "v", "rules": {**good["rules"], "PF-9": ["x"]}},
            {"version": "v", "rules": {**good["rules"], "PF-1": ["(unclosed"]}},
            {"version": "v", "rules": {**good["rules"], "PF-1": ["a*"]}},                          # matches nothing
            {"version": "v", "rules": {**good["rules"], "PF-1": ["x" * 401]}},
            {"version": "v"}, [],
        ]
        for i, data in enumerate(bad):
            with self.subTest(i=i), self.assertRaises(SchemaError):
                policy.load_rules(data)


if __name__ == "__main__":
    unittest.main()
