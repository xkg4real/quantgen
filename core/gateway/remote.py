"""The company route (KEY-3; GATEWAY_DESIGN.md section 5). Off today: it opens only when
core.app_identity.company_data_server_configured() is true. Tests use an in-process fake transport.

The route forwards (source, fn, args) as JSON with the account token, never a provider key, and refuses
fixed-local sources before anything is sent (D7-G rule 1)."""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from core.gateway import codec
from core.gateway.sources import SOURCES


class RemoteRefused(RuntimeError):
    """The company route will not carry this request (fixed-local source, function not allowed, route off)."""


class RemoteFailed(RuntimeError):
    """The company server answered with an error. The message is the server's error code only."""


Transport = Callable[[dict], dict]


def http_transport(base_url: str, token_getter: Callable[[], str], timeout_s: float = 15.0) -> Transport:
    """POST {base_url}/v1/call with the account token. Not used until the company server exists."""
    def send(request: dict) -> dict:
        import requests
        headers = {"Content-Type": "application/json"}
        token = token_getter() or ""
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.post(base_url.rstrip("/") + "/v1/call", data=json.dumps(request), headers=headers,
                             timeout=timeout_s)
        if resp.status_code != 200:
            return {"ok": False, "error": f"http_{resp.status_code}"}
        try:
            return resp.json()
        except ValueError:
            return {"ok": False, "error": "bad_answer"}
    return send


class RemoteRoute:
    def __init__(self, transport: Transport, client_version: str = ""):
        self._send = transport
        self._version = client_version

    def call(self, source_id: str, fn: str, *args: Any, **kwargs: Any) -> Any:
        source = SOURCES.get(source_id)
        if source is None:
            raise RemoteRefused("unknown source")
        if source.fixed_local:
            raise RemoteRefused(f"{source_id} stays on this PC (D7-G rule 1)")
        if fn not in source.functions:
            raise RemoteRefused(f"{source_id}.{fn} is not forwardable")
        request = {"source": source_id, "fn": fn, "args": codec.encode(list(args)),
                   "kwargs": codec.encode(kwargs), "client_version": self._version}
        try:
            answer = self._send(request)
        except Exception as exc:                     # network or transport failure: the name only, no message
            raise RemoteFailed(f"transport_{type(exc).__name__}") from None
        if not isinstance(answer, dict) or not isinstance(answer.get("ok"), bool):
            raise RemoteFailed("bad_answer")
        if not answer["ok"]:
            error = answer.get("error", "no_answer")
            raise RemoteFailed(error if isinstance(error, str) and error.isidentifier() else "bad_answer")
        try:
            return codec.decode(answer.get("result"))
        except Exception:
            raise RemoteFailed("bad_answer") from None

    def proxy(self, source_id: str) -> "RemoteProxy":
        return RemoteProxy(self, source_id)


class RemoteProxy:
    """Looks like the local client for the allowed functions only."""

    def __init__(self, route: RemoteRoute, source_id: str):
        self._route = route
        self._source = source_id

    def __getattr__(self, name: str):
        if name.startswith("_") or name not in SOURCES[self._source].functions:
            raise AttributeError(name)
        return lambda *a, **k: self._route.call(self._source, name, *a, **k)


def default_route() -> Optional[RemoteRoute]:
    """The real route when the company server is configured (core/app_identity.py), else None."""
    try:
        from core import app_identity
    except ImportError:
        return None
    if not app_identity.company_data_server_configured():
        return None
    return RemoteRoute(http_transport(app_identity.DATA_API_BASE, _account_token), client_version="")


def _account_token() -> str:
    return ""                                        # PAY-1 (core/account) fills this; empty means "login needed"
