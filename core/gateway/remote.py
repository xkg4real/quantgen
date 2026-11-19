"""The company route (KEY-3; GATEWAY_DESIGN.md section 5). Off today: it opens only when
core.app_identity.company_data_server_configured() is true. Tests use an in-process fake transport.

The route forwards (source, fn, args) as JSON with the account token, never a provider key, and refuses
fixed-local sources before anything is sent (D7-G rule 1)."""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

import re

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
        failed = ""
        try:
            answer = self._send(request)
        except Exception as exc:                     # network or transport failure: the class name only
            failed = "transport_" + re.sub(r"[^A-Za-z0-9_]", "", type(exc).__name__)[:40]   # a class name, ours
        if failed:                                   # raised outside the except: no __context__ carries the
            raise RemoteFailed(failed)               # original message (a URL, a token) along
        if not isinstance(answer, dict) or not isinstance(answer.get("ok"), bool):
            raise RemoteFailed("bad_answer")
        if not answer["ok"]:
            raise RemoteFailed(_code(answer.get("error", "no_answer")))
        decoded, ok = None, True
        try:
            decoded = codec.decode(answer.get("result"))
        except Exception:
            ok = False
        if not ok:
            raise RemoteFailed("bad_answer")
        return decoded

    def proxy(self, source_id: str) -> "RemoteProxy":
        return RemoteProxy(self, source_id)


_CODE = re.compile(r"[A-Za-z0-9_]{1,48}")


def _code(error: object) -> str:
    """A server error code fit for a message: ASCII letters, digits and "_" (a code such as ``http_503`` or an
    exception class name), at most 48 characters, and not key-shaped: no run of 24 or more letters and digits, and
    nothing routes.py would call key-like (32 or more key characters, underscores included). Anything else is
    "bad_answer"."""
    from core.gateway.routes import _KEY_LIKE
    text = error if isinstance(error, str) else ""
    if not _CODE.fullmatch(text) or re.search(r"[A-Za-z0-9]{24,}", text) or _KEY_LIKE.search(text):
        return "bad_answer"
    return text


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
