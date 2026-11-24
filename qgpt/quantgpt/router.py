"""Task router: a request is a task code plus a payload, never free text.

``admit`` decides whether a request may reach a model at all. It returns
``None`` when the request is admitted, or the status and reason of the refusal.
There is no path from a request without a task code to a model.
"""
from __future__ import annotations

from typing import Any

from .checks.schema import SchemaError
from .contracts.tasks import CONTRACTS, validate_input
from .envelope import MODES


def admit(request: Any, *, enabled: bool = True) -> tuple[str, str] | None:
    """Return None to admit, else ``(status, reason_code)``."""
    if not isinstance(request, dict):
        return ("blocked", "no_task_code")
    task, mode = request.get("task"), request.get("mode")
    if not isinstance(task, str) or task not in CONTRACTS:
        return ("blocked", "no_task_code")
    if mode not in MODES:
        return ("error", "invalid_input")
    if not enabled:
        return ("blocked", "disabled")
    if mode not in CONTRACTS[task].modes:
        return ("blocked", "task_not_allowed")
    if set(request) - {"task", "mode", "input"}:
        return ("error", "invalid_input")
    try:
        validate_input(task, request.get("input"))
    except SchemaError:
        return ("error", "invalid_input")
    return None
