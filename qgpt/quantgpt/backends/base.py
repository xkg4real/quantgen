"""Backend interface: text in, text out, with the reason generation stopped."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

FINISH_REASONS = ("stop", "length")


@dataclass(frozen=True)
class Generation:
    text: str
    finish_reason: str          # "stop": the model ended its answer; "length": the token limit cut it off


class BackendError(RuntimeError):
    """The backend failed or timed out."""


class Backend(Protocol):
    model_id: str
    adapter: str | None

    def generate(self, task: str, mode: str, payload: Any, *, prompt_version: str,
                 max_tokens: int) -> Generation: ...
