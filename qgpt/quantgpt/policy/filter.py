"""Policy filter PF-1 .. PF-6.

PF-1  a direction instruction (buy, sell, hold, and the like)
PF-2  a judgment about a named instrument at a named time
PF-3  a default or recommended value presented as the company's
PF-4  a future price stated as fact
PF-5  a guaranteed or exaggerated return
PF-6  free conversation: a request that carries no task code

PF-1 .. PF-5 are text rules applied to the model's output. PF-6 is structural
and is decided by the router. In ``tool`` mode any violation blocks the answer;
in ``owner`` mode violations are recorded in the envelope and nothing is
blocked.

The rule patterns are data, not code. ``SEED_RULES`` is a small illustrative
set, enough to exercise the filter; the reviewed list is loaded with
``load_rules`` from a file that is kept outside this repository.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from ..checks import schema as S
from ..checks.schema import SchemaError

TEXT_RULES = ("PF-1", "PF-2", "PF-3", "PF-4", "PF-5")
STRUCTURAL_RULES = ("PF-6",)
ALL_RULES = TEXT_RULES + STRUCTURAL_RULES
MAX_PATTERNS_PER_RULE = 500
MAX_PATTERN_LENGTH = 400

_RULES_FILE = S.obj({
    "version": S.string(max_len=64, pattern=r"[A-Za-z0-9][A-Za-z0-9_.\-]*"),
    "rules": S.obj({}, {rule: S.array(S.string(max_len=MAX_PATTERN_LENGTH), max_len=MAX_PATTERNS_PER_RULE)
                        for rule in TEXT_RULES}),
})


@dataclass(frozen=True)
class Rules:
    version: str
    patterns: Mapping[str, tuple]       # rule id -> compiled patterns

    def count(self) -> int:
        return sum(len(p) for p in self.patterns.values())


@dataclass(frozen=True)
class PolicyDecision:
    violations: tuple        # rule ids, in rule order, each once
    blocked: bool            # true only in tool mode
    rules_version: str

    def as_envelope(self) -> dict:
        return {"violations": list(self.violations), "rules_version": self.rules_version}


def load_rules(data: Any) -> Rules:
    """Build a rule set from ``{"version": ..., "rules": {"PF-1": [regex, ...], ...}}``.

    Every text rule must be present with at least one pattern, so a file that
    silently drops a rule is refused rather than loaded as a weaker filter.
    """
    _RULES_FILE(data, "$")
    compiled = {}
    for rule in TEXT_RULES:
        sources = data["rules"].get(rule)
        if not sources:
            raise SchemaError(f"$.rules.{rule}: needs at least one pattern")
        try:
            compiled[rule] = tuple(re.compile(source, re.IGNORECASE) for source in sources)
        except re.error as exc:
            raise SchemaError(f"$.rules.{rule}: bad pattern ({exc})") from None
        for pattern in compiled[rule]:
            if pattern.search(""):
                raise SchemaError(f"$.rules.{rule}: a pattern matches empty text")
    return Rules(data["version"], compiled)


def scan(text: str, rules: Rules) -> tuple:
    """Rule ids whose patterns occur in ``text``."""
    text = text or ""
    return tuple(rule for rule in TEXT_RULES if any(p.search(text) for p in rules.patterns[rule]))


def decide(text: str, mode: str, rules: Rules) -> PolicyDecision:
    if mode not in ("tool", "owner"):
        raise ValueError("mode must be tool or owner")
    violations = scan(text, rules)
    return PolicyDecision(violations, bool(violations) and mode == "tool", rules.version)


def free_chat(rules: Rules) -> PolicyDecision:
    """The decision for a request without a task code: PF-6, blocked in every mode."""
    return PolicyDecision(("PF-6",), True, rules.version)


# A small illustrative set (two or three patterns per rule). Not the reviewed list.
SEED_RULES = load_rules({
    "version": "pf-seed-0",
    "rules": {
        "PF-1": [r"(매수|매도|보유|손절|익절)\s*(하세요|하십시오|하시기 바랍니다|를 권합니다|를 추천)",
                 r"\byou should (buy|sell|hold)\b", r"\b(buy|sell) (it |this |them )?now\b"],
        "PF-2": [r"(지금|오늘|이번 주|내일)[^.\n]{0,30}(\d{6}|[A-Z]{2,5}\b)[^.\n]{0,30}(사야|팔아야|들어갈 때|매수 적기|매도 적기)",
                 r"\b(now|today|this week) is (a good|the right) time to (buy|sell) [A-Z]{2,5}\b"],
        "PF-3": [r"(당사|저희|QUANTGEN)(가|는|의)?\s*(권장|추천)\s*(값|설정|비중)",
                 r"\bour recommended (value|setting|allocation)\b"],
        "PF-4": [r"(오를|상승할|하락할|내릴|도달할) 것(입니다|이 확실)", r"\bwill (rise|fall|reach|hit)\b[^.\n]{0,40}\b(by|to)\b",
                 r"목표가"],
        "PF-5": [r"(수익|원금)(을|이)?\s*보장", r"\bguaranteed (return|profit)s?\b", r"무조건 (수익|오릅니다)"],
    },
})
