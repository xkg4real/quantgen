"""Hand-written structural validator (no jsonschema, no pydantic).

A spec is a function ``check(value, path) -> None`` that raises ``SchemaError``
naming the path and the first problem. Validation rejects; it never repairs.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Callable, Mapping

Spec = Callable[[Any, str], None]

MAX_DEPTH = 12


class SchemaError(ValueError):
    """A value does not satisfy its contract."""


def _fail(path: str, message: str) -> None:
    raise SchemaError(f"{path or '$'}: {message}")


def string(*, min_len: int = 1, max_len: int = 20000, pattern: str | None = None,
           enum: tuple[str, ...] | None = None) -> Spec:
    compiled = re.compile(pattern) if pattern else None

    def check(value: Any, path: str) -> None:
        if not isinstance(value, str):
            _fail(path, "must be a string")
        if enum is not None and value not in enum:
            _fail(path, f"must be one of {list(enum)}")
        if not min_len <= len(value) <= max_len:
            _fail(path, f"length must be {min_len}..{max_len}")
        if min_len and not value.strip():
            _fail(path, "must not be blank")
        if compiled and not compiled.fullmatch(value):
            _fail(path, "has the wrong format")
    return check


def integer(*, lo: int | None = None, hi: int | None = None) -> Spec:
    def check(value: Any, path: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            _fail(path, "must be an integer")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            _fail(path, f"must be in [{lo}, {hi}]")
    return check


def number(*, lo: float | None = None, hi: float | None = None) -> Spec:
    def check(value: Any, path: str) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _fail(path, "must be a number")
        if not math.isfinite(value):
            _fail(path, "must be finite")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            _fail(path, f"must be in [{lo}, {hi}]")
    return check


def boolean() -> Spec:
    def check(value: Any, path: str) -> None:
        if not isinstance(value, bool):
            _fail(path, "must be true or false")
    return check


def const(expected: Any) -> Spec:
    def check(value: Any, path: str) -> None:
        if type(value) is not type(expected) or value != expected:
            _fail(path, f"must be {expected!r}")
    return check


def nullable(spec: Spec) -> Spec:
    def check(value: Any, path: str) -> None:
        if value is not None:
            spec(value, path)
    return check


def array(item: Spec, *, min_len: int = 0, max_len: int = 1000, unique: bool = False) -> Spec:
    def check(value: Any, path: str) -> None:
        if not isinstance(value, list):
            _fail(path, "must be an array")
        if not min_len <= len(value) <= max_len:
            _fail(path, f"must hold {min_len}..{max_len} items")
        for i, element in enumerate(value):
            item(element, f"{path}[{i}]")
        if unique and len({repr(v) for v in value}) != len(value):
            _fail(path, "items must be unique")
    return check


def obj(required: Mapping[str, Spec] | None = None, optional: Mapping[str, Spec] | None = None,
        *, extra: Spec | None = None) -> Spec:
    """An object. Unknown keys are rejected unless ``extra`` gives a spec for them."""
    required = dict(required or {})
    optional = dict(optional or {})

    def check(value: Any, path: str) -> None:
        if not isinstance(value, dict):
            _fail(path, "must be an object")
        for name in required:
            if name not in value:
                _fail(f"{path}.{name}", "is missing")
        for name, element in value.items():
            if not isinstance(name, str):
                _fail(path, "keys must be strings")
            spec = required.get(name) or optional.get(name) or extra
            if spec is None:
                _fail(f"{path}.{name}", "is not an allowed field")
            spec(element, f"{path}.{name}")
    return check


def json_value(*, max_depth: int = MAX_DEPTH, max_string: int = 20000) -> Spec:
    """Any strict-JSON value: finite numbers, string keys, bounded depth."""
    def check(value: Any, path: str, depth: int = 0) -> None:
        if depth > max_depth:
            _fail(path, "is nested too deeply")
        if value is None or isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            if not math.isfinite(value):
                _fail(path, "must be finite")
            return
        if isinstance(value, str):
            if len(value) > max_string:
                _fail(path, "string is too long")
            return
        if isinstance(value, list):
            for i, element in enumerate(value):
                check(element, f"{path}[{i}]", depth + 1)
            return
        if isinstance(value, dict):
            for name, element in value.items():
                if not isinstance(name, str):
                    _fail(path, "keys must be strings")
                check(element, f"{path}.{name}", depth + 1)
            return
        _fail(path, "is not a JSON value")
    return check


def json_object(**kwargs: Any) -> Spec:
    inner = json_value(**kwargs)

    def check(value: Any, path: str) -> None:
        if not isinstance(value, dict):
            _fail(path, "must be an object")
        inner(value, path)
    return check


def iso_date() -> Spec:
    def check(value: Any, path: str) -> None:
        if not isinstance(value, str):
            _fail(path, "must be an ISO date string")
        parse_as_of(value, path)
    return check


def parse_as_of(value: str, path: str = "as_of") -> datetime:
    """Parse YYYY-MM-DD or an ISO 8601 timestamp into a naive-UTC-comparable datetime.

    A bare date means the end of that day, so a document dated the same day is
    not later than the as_of date.
    """
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            d = date.fromisoformat(value)
            return datetime(d.year, d.month, d.day, 23, 59, 59)
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise SchemaError(f"{path}: is not an ISO 8601 date") from None
    if ts.tzinfo is not None:
        ts = (ts - ts.utcoffset()).replace(tzinfo=None)
    return ts


def validate(spec: Spec, value: Any, path: str = "$") -> Any:
    spec(value, path)
    return value


def is_valid(spec: Spec, value: Any) -> bool:
    try:
        spec(value, "$")
    except SchemaError:
        return False
    return True
