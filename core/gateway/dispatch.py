"""Server-side handler (KEY-3; GATEWAY_DESIGN.md sections 1 and 5): run (source, fn, args) on the local route and
return a JSON-safe answer. The company data server runs this same code with the company's keys; today only the
fake server in the tests does. It refuses fixed-local sources (D7-G rule 1) and functions outside the allowlist."""
from __future__ import annotations

from typing import Any

from core.gateway import codec
from core.gateway.sources import SOURCES


def dispatch(request: dict, local) -> dict:
    source_id = request.get("source")
    fn = request.get("fn")
    source = SOURCES.get(source_id) if isinstance(source_id, str) else None
    if source is None:
        return {"ok": False, "error": "unknown_source"}
    if source.fixed_local:
        return {"ok": False, "error": "fixed_local"}
    if fn not in source.functions:
        return {"ok": False, "error": "function_not_allowed"}
    args = codec.decode(request.get("args") or [])
    kwargs = codec.decode(request.get("kwargs") or {})
    try:
        result: Any = getattr(local.client(source_id), fn)(*args, **kwargs)
        return {"ok": True, "result": codec.encode(result)}
    except codec.CodecError:
        return {"ok": False, "error": "result_not_encodable"}
    except Exception as exc:                        # provider messages are not forwarded: they may echo input
        return {"ok": False, "error": type(exc).__name__}
