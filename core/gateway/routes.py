"""Read and check routes.json (KEY-3; GATEWAY_DESIGN.md section 2). A bad file stops the gateway, not the app:
callers get RouteError and the gateway reports every source as off."""
from __future__ import annotations

import json
import re
from pathlib import Path

from core.gateway.sources import ROUTES, SOURCES

ROUTES_FILE = Path(__file__).with_name("routes.json")
PROFILES = ("personal", "commercial")
# D7-G rule 2: no key-shaped text in the route file (long base64/hex runs, common key prefixes).
_KEY_LIKE = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|[A-Za-z0-9+/_-]{32,})")


class RouteError(ValueError):
    """routes.json is missing, malformed or breaks a D7-G rule."""


def check_routes(data: object, raw_text: str = "") -> dict:
    if raw_text and _KEY_LIKE.search(raw_text):
        raise RouteError("routes.json contains key-shaped text (D7-G rule 2)")
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise RouteError("routes.json schema must be 1")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILES):
        raise RouteError(f"routes.json profiles must be exactly {PROFILES}")
    fixed = data.get("fixed_local")
    expected_fixed = sorted(s.id for s in SOURCES.values() if s.fixed_local)
    if not isinstance(fixed, list) or sorted(fixed) != expected_fixed:
        raise RouteError(f"fixed_local must list {expected_fixed}")
    for name, table in profiles.items():
        if not isinstance(table, dict) or set(table) != set(SOURCES):
            missing = sorted(set(SOURCES) - set(table or {}))
            extra = sorted(set(table or {}) - set(SOURCES))
            raise RouteError(f"profile {name}: sources must match core/gateway/sources.py "
                             f"(missing {missing}, unknown {extra})")
        for source, order in table.items():
            if (not isinstance(order, list) or not order or any(r not in ROUTES for r in order)
                    or len(set(order)) != len(order)):
                raise RouteError(f"profile {name}: {source} needs a non-empty list of distinct routes from {ROUTES}")
            if "off" in order and len(order) > 1:
                raise RouteError(f"profile {name}: {source} lists 'off' with other routes")
            if source in fixed and order != ["local_key"]:
                raise RouteError(f"profile {name}: {source} is fixed to local_key (D7-G rule 1)")
            if not SOURCES[source].keys and "local_key" in order:
                raise RouteError(f"profile {name}: {source} has no key; use keyless")
            if SOURCES[source].keys and "keyless" in order:
                raise RouteError(f"profile {name}: {source} needs a key; keyless is not a route for it")
    return data


def load_routes(path: Path = ROUTES_FILE) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise RouteError(f"cannot read {path.name} ({type(exc).__name__})") from None
    return check_routes(data, raw)
