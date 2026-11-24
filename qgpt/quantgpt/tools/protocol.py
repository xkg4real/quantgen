"""Host tool protocol: the three things a model may ask the host for.

``run_calc``   run a calculation the host's engine already offers, by name
``get_card``   read one stored research card
``list_cards`` list stored research cards

The model emits a tool call as data; ``dispatch`` validates it against this
closed list and hands it to the host's implementation. There is no order,
account, balance, position, transfer, key or credential function here, and a
call to any name outside the list is refused before the host sees it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from ..checks import schema as S
from ..checks.schema import SchemaError

_NAME = r"[a-z][a-z0-9_]{0,63}"
_CARD_ID = r"[A-Za-z][A-Za-z0-9_]{1,63}"
MAX_RESULT_BYTES = 200_000


@runtime_checkable
class HostTools(Protocol):
    """What the host application implements. Read and calculate only."""

    def run_calc(self, name: str, params: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def get_card(self, card_id: str) -> Mapping[str, Any]: ...

    def list_cards(self, kind: str | None = None) -> list[Mapping[str, Any]]: ...


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    arguments: S.Spec
    json_schema: Mapping[str, Any]      # the form a model backend is shown


TOOLS: dict[str, ToolSpec] = {t.name: t for t in (
    ToolSpec(
        "run_calc", "Run one calculation of the host engine by name and return its numbers.",
        S.obj({"name": S.string(pattern=_NAME), "params": S.json_object(max_depth=6)}),
        {"type": "object", "additionalProperties": False, "required": ["name", "params"],
         "properties": {"name": {"type": "string"}, "params": {"type": "object"}}},
    ),
    ToolSpec(
        "get_card", "Read one stored research card by its id.",
        S.obj({"card_id": S.string(pattern=_CARD_ID)}),
        {"type": "object", "additionalProperties": False, "required": ["card_id"],
         "properties": {"card_id": {"type": "string"}}},
    ),
    ToolSpec(
        "list_cards", "List the ids, kinds and decisions of stored research cards.",
        S.obj({}, {"kind": S.string(enum=("strategy", "distribution", "model"))}),
        {"type": "object", "additionalProperties": False,
         "properties": {"kind": {"type": "string", "enum": ["strategy", "distribution", "model"]}}},
    ),
)}
_CALL = S.obj({"tool": S.string(max_len=64), "arguments": S.json_object(max_depth=8)})


class ToolRefused(ValueError):
    """The call is outside the protocol; the host was not asked."""


def tool_definitions() -> list[dict]:
    """The closed list, in the shape a chat backend takes."""
    return [{"name": t.name, "description": t.description, "input_schema": dict(t.json_schema)}
            for t in TOOLS.values()]


def validate_call(call: Any, *, allowed_calcs: frozenset[str] | set[str]) -> tuple[str, dict]:
    try:
        _CALL(call, "$")
    except SchemaError as exc:
        raise ToolRefused(str(exc)) from None
    name, arguments = call["tool"], call["arguments"]
    if name not in TOOLS:
        raise ToolRefused(f"{name!r} is not a tool of this protocol")
    try:
        TOOLS[name].arguments(arguments, "$.arguments")
    except SchemaError as exc:
        raise ToolRefused(str(exc)) from None
    if name == "run_calc" and arguments["name"] not in allowed_calcs:
        raise ToolRefused(f"calculation {arguments['name']!r} is not on the allowed list")
    return name, arguments


def dispatch(host: HostTools, call: Any, *, allowed_calcs: frozenset[str] | set[str]) -> dict:
    """Validate one model tool call, run it on the host, and return a strict-JSON result."""
    name, arguments = validate_call(call, allowed_calcs=allowed_calcs)
    if name == "run_calc":
        result: Any = host.run_calc(arguments["name"], arguments["params"])
    elif name == "get_card":
        result = host.get_card(arguments["card_id"])
    else:
        result = host.list_cards(arguments.get("kind"))
    try:
        S.json_value()(result, "$result")
    except SchemaError as exc:
        raise ToolRefused(f"the host result is not strict JSON: {exc}") from None
    from ..envelope import canonical_json
    if len(canonical_json(result).encode("utf-8")) > MAX_RESULT_BYTES:
        raise ToolRefused("the host result is too large to hand to a model")
    return {"tool": name, "result": result}
