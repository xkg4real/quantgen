"""A scripted backend for tests: the same request always gives the same text. No model, no network."""
from __future__ import annotations

import json
from typing import Any, Callable

from ..envelope import request_sha256
from .base import BackendError, Generation


class FakeBackend:
    """Answers from a script keyed by task, or by a function of the request.

    ``max_tokens`` is honoured by cutting the text at ``max_tokens`` characters
    and reporting ``length``, so truncation handling can be tested.
    """

    def __init__(self, script: dict[str, Any] | Callable[[str, str, Any], Any], *, model_id: str = "fake-0",
                 adapter: str | None = None, fail: str | None = None) -> None:
        self._script = script
        self.model_id = model_id
        self.adapter = adapter
        self._fail = fail
        self.calls: list[str] = []

    def generate(self, task: str, mode: str, payload: Any, *, prompt_version: str, max_tokens: int) -> Generation:
        self.calls.append(request_sha256(task, mode, payload, self.model_id, self.adapter, prompt_version))
        if self._fail:
            raise BackendError(self._fail)
        answer = self._script(task, mode, payload) if callable(self._script) else self._script[task]
        text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False, sort_keys=True)
        if len(text) > max_tokens:
            return Generation(text[:max_tokens], "length")
        return Generation(text, "stop")
