"""Exclude known private structured fields from optional AI commentary.

Market calculations and official verdicts are preserved. This is a field-name
boundary, not a claim to detect private details in arbitrary free-form text.
"""
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, is_dataclass

PRIVATE_WORDS = ("account", "balance", "holding", "credential", "secret",
                 "api_key", "token", "authorization", "owner_decision")


def private_field(name):
    name = str(name).lower().replace("-", "_")
    return any(word in name for word in PRIVATE_WORDS)


def filter_analysis_fields(value):
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {key: filter_analysis_fields(item) for key, item in value.items()
                if not private_field(key)}
    if isinstance(value, (list, tuple)):
        return [filter_analysis_fields(item) for item in value]
    return deepcopy(value)
