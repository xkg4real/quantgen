"""Data-source gateway: the one place the app reaches data providers (KEY-3; owner decision D7-G, 2026-11-18;
design docs/commercial/GATEWAY_DESIGN.md, owner approval 2026-11-19 "Key-3 승인").

The app calls only:
- ``client(source)``: the client for a source on its active route (a local client, or a company-route proxy);
- ``ready(source)``: one of ``key_needed``, ``login_needed``, ``plan_needed``, ``ready``, ``off``;
- ``status()``: one row per source for the key and connection screens (KEY-5 draws these rows as they are);
- ``stream(source)``: the streaming client of a source (KIS realtime today);
- ``answer(source, data, ...)``: wraps a result with source, route, delay and display right (D7-G rule 4).

Which route serves a source comes from ``routes.json`` and the active profile (``core.app_identity.GATEWAY_PROFILE``;
``personal`` today). The company route stays closed until ``core.app_identity.company_data_server_configured()``.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from core.gateway import local as _local
from core.gateway import remote as _remote_mod
from core.gateway.routes import PROFILES, RouteError, load_routes
from core.gateway.sources import SOURCES

__all__ = ["client", "ready", "status", "stream", "answer", "route_of", "profile", "reload", "GatewayAnswer",
           "GatewayOff", "RouteError", "SOURCES"]


class GatewayOff(RuntimeError):
    """The source is off in the active profile (or routes.json is broken)."""


@dataclass(frozen=True)
class GatewayAnswer:
    """A result plus what the screen must show next to it."""
    data: Any
    source: str
    route: str
    delay: str
    display_right: str
    ok: bool = True
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


_lock = threading.RLock()
_routes: Optional[dict] = None
_route_error: Optional[str] = None
_profile_override: Optional[str] = None
_remote_override: Any = None                      # tests: a RemoteRoute over a fake transport
LOCAL = _local.LocalRoute({sid: s.factory for sid, s in SOURCES.items()})


def _table() -> Optional[dict]:
    global _routes, _route_error
    with _lock:
        if _routes is None and _route_error is None:
            try:
                _routes = load_routes()
            except RouteError as exc:
                _route_error = str(exc)
        return _routes


def profile() -> str:
    if _profile_override in PROFILES:
        return _profile_override
    try:
        from core import app_identity
        chosen = getattr(app_identity, "GATEWAY_PROFILE", "personal")
    except ImportError:
        chosen = "personal"
    return chosen if chosen in PROFILES else "personal"


def _remote() -> Optional[_remote_mod.RemoteRoute]:
    return _remote_override if _remote_override is not None else _remote_mod.default_route()


def _order(source: str) -> list[str]:
    if source not in SOURCES:
        raise KeyError(f"unknown data source: {source}")
    table = _table()
    if table is None:
        return ["off"]
    return list(table["profiles"][profile()][source])


def route_of(source: str) -> str:
    """The route that serves `source` now: the first route in its order that is available."""
    for route in _order(source):
        if route == "off":
            return "off"
        if route == "company":
            if _remote() is not None:
                return "company"
            continue
        return route
    return "off"


def client(source: str) -> Any:
    route = route_of(source)
    if route == "off":
        raise GatewayOff(f"{source} is off in profile {profile()}")
    if route == "company":
        return _remote().proxy(source)
    return LOCAL.client(source)


def stream(source: str) -> Any:
    spec = SOURCES[source].stream if source in SOURCES else None
    if spec is None:
        raise GatewayOff(f"{source} has no stream")
    if route_of(source) not in ("local_key", "keyless"):
        raise GatewayOff(f"{source} streams only on this PC today")
    return _local._resolve(spec)()


def _key_state(source: str) -> tuple[list[str], dict]:
    from core import credentials
    keys = SOURCES[source].keys
    found = {k: credentials.status(k)["source"] for k in keys}
    return [k for k in keys if not found[k]], found


def ready(source: str) -> str:
    route = route_of(source)
    if route == "off":
        return "off"
    if route == "company":
        return "ready" if _remote_logged_in() else "login_needed"
    if route == "keyless":
        return "ready"
    missing, _ = _key_state(source)
    return "key_needed" if missing else "ready"


def _remote_logged_in() -> bool:
    return bool(_remote_mod._account_token()) or _remote_override is not None


def _display_policies() -> dict:
    try:
        path = Path(__file__).resolve().parents[1] / "research" / "display_rights.json"
        return {k: v.get("outcome", "unknown") for k, v in json.loads(path.read_text(encoding="utf-8"))
                ["policies"].items()}
    except Exception:
        return {}


def display_right(source: str) -> str:
    policy = SOURCES[source].display_policy
    if policy is None:
        return "not_market_data"
    return _display_policies().get(policy, "unknown")


def answer(source: str, data: Any, *, ok: bool = True, reason: str = "") -> GatewayAnswer:
    return GatewayAnswer(data=data, source=source, route=route_of(source), delay=SOURCES[source].delay,
                         display_right=display_right(source), ok=ok, reason=reason)


def status() -> list[dict]:
    """One row per source, no values: what the key and connection screens draw (D7-G rule 5)."""
    rows = []
    rights = _display_policies()
    for sid, src in SOURCES.items():
        missing, found = _key_state(sid)
        policy = src.display_policy
        rows.append({
            "source": sid, "label_key": f"gateway.source.{sid}", "route": route_of(sid), "state": ready(sid),
            "needs": missing, "key_sources": found, "delay": src.delay,
            "display_right": "not_market_data" if policy is None else rights.get(policy, "unknown"),
            "error": _route_error,
        })
    return rows


def reload(source: Optional[str] = None) -> None:
    """Rebuild clients (all, or one). Routes are read again too."""
    global _routes, _route_error
    with _lock:
        if source is None:
            _routes, _route_error = None, None
        LOCAL.reload(source)


def _on_key_change(name: str) -> None:
    """D7-G rule 6: a key set or deleted in the app rebuilds the clients that use it."""
    for sid, src in SOURCES.items():
        if name in src.keys:
            LOCAL.reload(sid)
            built = LOCAL._clients.get(sid)
            if built is not None and hasattr(built, "reload_credentials"):
                built.reload_credentials()


def _subscribe() -> None:
    from core import credentials
    credentials.subscribe(_on_key_change)


_subscribe()
