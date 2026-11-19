"""Data-source gateway: the one place the app reaches data providers (KEY-3; owner decision D7-G, 2026-11-18;
design docs/commercial/GATEWAY_DESIGN.md, owner approval 2026-11-19 "Key-3 승인").

The app calls only:
- ``client(source)``: the client for a source on its active route (a local client, or a company-route proxy);
- ``ready(source)``: one of ``key_needed``, ``login_needed``, ``plan_needed``, ``ready``, ``off``;
- ``status()``: one row per source for the key and connection screens (KEY-5 draws these rows as they are);
- ``stream(source)``: the streaming client of a source (KIS realtime today);
- ``answer(source, data, ...)``: wraps a result with source, route, delay and display right (D7-G rule 4).

How core/ and main.py reach the existing local clients (KEY-4; GATEWAY_DESIGN.md section 7a). Each refuses a source
that is ``blocked()``: off, or on the company route (served only through ``client()``; the user's own key is never
used while the screens say "company"). Fixed-local sources (kis_quote, kis_account, upbit_account) never read
routes.json.
- ``provider(module, source=None)``: a provider module (``data.kis_markets``, ``data.fmp.quote_client``,
  ``gs_quant.session``...) for code that builds the client itself; checked against every non-fixed source the module
  reaches, or only ``source=`` (the caller's own statement of which one it uses: a declaration, not a gate over the
  rest of the module). Looked up at call time, so whatever the provider module holds then (a test's patch included)
  is what the caller gets, as before;
- ``krx_gateway()``: the KRX screen's KRXGateway, with the KRX Open API / OpenDART sub-clients replaced by an
  OffClient when blocked; its answers carry the OffClient's reason, and every gateway it built is set up again after
  a route reload or a key change (KEY-5/a);
- ``ficc()``: the FRED/Yahoo loaders of core/ficc/data.py, each call checked against the ``fred`` and ``yahoo``
  routes of the providers it would use;
- ``keys_ready(source)``, ``local_key(source, part)``: the same config.py functions as before (``config.kis_ready``,
  ``config.fmp_key``...), looked up at call time; ``suspend_key`` (single-threaded self-checks) and ``status_loaders``
  likewise;
- ``endpoint(source)``: a provider URL core needs (the Anthropic messages URL).
Five names are bound once at import, not at call time (all fixed-local or source-less): core/gateway/feed.py
``QuoteFeed``'s base (the S4-frozen engine feed; main.py imports that subclass), gsq ``gs_quant``, history
``_requests`` (data.net session), risk ``_gts`` and quant insights ``_API_URL``.
``on_change(listener)``: called after ``reload()`` and after a key is set or deleted (core/gateway/feed.py uses it).

Which route serves a source comes from ``routes.json`` and the active profile (``core.app_identity.GATEWAY_PROFILE``;
``personal`` today). The company route stays closed until ``core.app_identity.company_data_server_configured()``.
"""
from __future__ import annotations

import contextlib
import dataclasses
import importlib
import json
import threading
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from core.gateway import local as _local
from core.gateway import remote as _remote_mod
from core.gateway.routes import PROFILES, RouteError, load_routes
from core.gateway.sources import SOURCES

__all__ = ["client", "ready", "status", "stream", "answer", "route_of", "profile", "reload", "GatewayAnswer",
           "GatewayOff", "RouteError", "SOURCES", "provider", "ficc", "keys_ready", "local_key", "suspend_key",
           "status_loaders", "endpoint", "PROVIDER_MODULES", "blocked", "krx_gateway", "OffClient", "on_change"]


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
    """The route that serves `source` now: the first route in its order that is available. A fixed-local source is
    ``local_key`` without reading routes.json (rule 1 allows nothing else), so a broken routes file leaves KIS and the
    Upbit account working, as the core paths that reach them do."""
    if source in SOURCES and SOURCES[source].fixed_local:
        return "local_key"
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


_listeners: list = []


def on_change(listener) -> None:
    """Call ``listener(name)`` after ``reload()`` (name: the source, or "" for all) and after a key is set or deleted
    (name: the key). A listener that fails does not stop the others."""
    if listener not in _listeners:
        _listeners.append(listener)


def _changed(name: str) -> None:
    for listener in list(_listeners):
        try:
            listener(name)
        except Exception:
            pass


def reload(source: Optional[str] = None) -> None:
    """Rebuild clients (all, or one). Routes are read again too."""
    global _routes, _route_error
    with _lock:
        if source is None:
            _routes, _route_error = None, None
        LOCAL.reload(source)
    _changed(source or "")


def _on_key_change(name: str) -> None:
    """D7-G rule 6: a key set or deleted in the app rebuilds the clients that use it."""
    for sid, src in SOURCES.items():
        if name in src.keys:
            held = LOCAL.held(sid)
            LOCAL.reload(sid)                        # the next client() builds a fresh one
            for old in held:                         # every caller still holding an earlier client sees it too,
                reload_credentials = getattr(old, "reload_credentials", None)   # on every change, not just once
                if callable(reload_credentials):
                    try:
                        reload_credentials()
                    except Exception:
                        pass                         # a client that cannot reload must not break saving a key
    _changed(name)


def _subscribe() -> None:
    from core import credentials
    credentials.subscribe(_on_key_change)


_subscribe()


# -- KEY-4: the ways core/ reaches the existing local clients ----------------------------------------------------
# Provider module -> every source it can reach. provider() checks each one that is not fixed-local; a caller that
# uses only one of them names it (provider(module, source=...)). An empty tuple: an offline library or shared
# plumbing that reaches no provider by itself (gs_quant's timeseries maths, the shared HTTP session).
PROVIDER_MODULES: dict[str, tuple[str, ...]] = {
    "data.krx": ("kis_quote", "krx_open_api", "opendart"),   # KRXGateway: KIS first, then KRX Open API and OpenDART
    "data.krx.kis_client": ("kis_quote",),
    "data.kis_markets": ("kis_quote",),
    "data.kis_workspace": ("kis_quote",),            # pure values too (availability_note...): never blocked (rule 1)
    "data.kis_stream": ("kis_quote",),               # subscription_for: the KIS realtime subscription (KEY-5/a G1)
    "data.krx.krx_market_client": ("krx_open_api",),
    "data.fmp": ("fmp",),
    "data.fmp.quote_client": ("fmp",),
    "data.crypto.crypto_client": ("crypto_public", "upbit_account"),   # UpbitAccount: source="upbit_account"
    "data.net": (),
    "gs_quant": (),
    "gs_quant.timeseries": (),
    "gs_quant.session": ("gs_marquee",),
    "gs_quant.instrument": ("gs_marquee",),
}

# Source -> the config.py function behind each part. Looked up on the config module at call time.
_CONFIG_FUNCTIONS: dict[str, dict[str, str]] = {
    "kis_quote": {"ready": "kis_ready"},
    "upbit_account": {"ready": "upbit_ready"},
    "fmp": {"ready": "fmp_ready", "key": "fmp_key"},
    "anthropic": {"ready": "ai_ready", "key": "anthropic_key"},
    "gs_marquee": {"id": "gs_client_id", "secret": "gs_client_secret"},
}
_STATUS_LOADERS = ("quant_provider_status", "krx_provider_status", "ficc_provider_status", "crypto_provider_status")


def _config():
    import config
    return config


def blocked(source: str) -> str:
    """Why core may not reach ``source`` on this PC: "off", "company" (served only through ``client(source)``,
    never by core's local entry points: the user's own key must not be used while the screens say "company"), or
    "" when the local route serves it. A fixed-local source (D7-G rule 1: kis_quote, kis_account, upbit_account)
    is ``local_key`` in every valid profile, so routes.json is not read for it."""
    if SOURCES[source].fixed_local:
        return ""
    route = route_of(source)
    return route if route in ("off", "company") else ""


def _refuse(source: str) -> None:
    why = blocked(source)
    if why == "off":
        raise GatewayOff(f"{source} is off in profile {profile()}")
    if why == "company":
        raise GatewayOff(f"{source} is served by the company route in profile {profile()}: only through client()")


def provider(module: str, source: Optional[str] = None) -> Any:
    """The provider module ``module`` (a key of PROVIDER_MODULES). GatewayOff when a source it reaches is off or on
    the company route (only ``source`` when the caller names the one it uses); ImportError as before when the
    package is not installed."""
    if module not in PROVIDER_MODULES:
        raise KeyError(f"not a provider module: {module}")
    sources = PROVIDER_MODULES[module]
    if source is not None and source not in sources:
        raise KeyError(f"{module} does not serve {source}")
    for sid in (source,) if source is not None else sources:
        _refuse(sid)
    return importlib.import_module(module)


def ficc() -> Any:
    """The FRED/Yahoo loaders (core/ficc/data.py through local.FiccData); each call is checked against the routes
    of the providers it would use, so ``yahoo: off`` stops a Yahoo ticker and leaves a FRED id alone."""
    return LOCAL.client("fred")


def keys_ready(source: str) -> bool:
    """``config.kis_ready()`` and the like, for a source with a "ready" function; False when the source is off or
    on the company route."""
    if blocked(source):
        return False
    return bool(getattr(_config(), _CONFIG_FUNCTIONS[source]["ready"])())


def local_key(source: str, part: str = "key") -> str:
    """The user's own key for a source on the local route (``config.fmp_key()`` and the like); "" when off or on
    the company route. Only for code on this PC that sends the key to the provider itself, as before."""
    if blocked(source):
        return ""
    return getattr(_config(), _CONFIG_FUNCTIONS[source][part])()


@contextlib.contextmanager
def suspend_key(source: str, part: str = "key"):
    """Make the key read as absent while the block runs (self-checks that must not reach the network). Same swap
    of the config function as the code it replaces, restored on exit. Single-threaded use only: it replaces the
    module-level config function, so another thread reading the key meanwhile also sees it absent."""
    cfg = _config()
    name = _CONFIG_FUNCTIONS[source][part]
    saved = getattr(cfg, name)
    setattr(cfg, name, lambda: "")
    try:
        yield
    finally:
        setattr(cfg, name, saved)


def status_loaders() -> tuple:
    """The presence-only provider status functions of config.py (quant, KRX, FICC, crypto), in that order."""
    cfg = _config()
    return tuple(getattr(cfg, name) for name in _STATUS_LOADERS)


def endpoint(source: str) -> str:
    return _local.ENDPOINTS[source]


class OffClient:
    """Stands in for a sub-client whose source is blocked (off, or on the company route): it answers as an
    unconfigured client does (``ready`` False, a status row with the reason, empty rows where the real client gives
    rows) and never reaches the provider. Any other call raises GatewayOff."""

    def __init__(self, source: str, why: str, empty: tuple = ()):
        self.source = source
        state = "served by the company route" if why == "company" else why
        self.reason = f"{source} is {state} in profile {profile()}"
        self.ready = False
        self.has_key = False
        self._empty = frozenset(empty)

    def status(self) -> dict:
        return {"ready": False, "reason": self.reason}

    def probe(self) -> dict:
        return {"ready": False, "reason": self.reason}

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name in self._empty:
            return lambda *a, **k: []
        reason = self.reason

        def refused(*a, **k):
            raise GatewayOff(reason)
        return refused


_KRX_CLASSES: dict = {}
_KRX_BUILT: "weakref.WeakSet" = weakref.WeakSet()
_KRX_SOURCES = ("kis_quote", "krx_open_api", "opendart")


def _krx_class(base: type) -> type:
    """KRXGateway with the blocked sub-client's reason in its answers (PR #133 review 3, A1R3-1): a blocked KRX Open
    API or OpenDART otherwise reads as "Set KRX_API_KEY" / "need OPENDART_API_KEY", which is not why there is no
    answer. Built on the provider's class at call time (a test that patches data.krx.KRXGateway gets its class)."""
    if base in _KRX_CLASSES:
        return _KRX_CLASSES[base]

    def why(sub) -> str:
        return sub.reason if isinstance(sub, OffClient) else ""

    def explain(answer, reason: str, *, keep: bool):
        if answer.ok or not reason:
            return answer
        return dataclasses.replace(answer, reason=f"{answer.reason} ({reason})" if keep and answer.reason else reason)

    class GatedKRXGateway(base):
        def quote(self, ticker):
            return explain(super().quote(ticker), why(self.krx), keep=True)

        def market_snapshot(self, market="ALL"):
            return explain(super().market_snapshot(market), why(self.krx), keep=False)

        def indices(self):
            return explain(super().indices(), why(self.krx), keep=True)

        def filings(self, ticker, **kwargs):
            return explain(super().filings(ticker, **kwargs), why(self.dart), keep=False)

        def financials(self, ticker, **kwargs):
            return explain(super().financials(ticker, **kwargs), why(self.dart), keep=False)

    GatedKRXGateway.__name__ = GatedKRXGateway.__qualname__ = base.__name__
    _KRX_CLASSES[base] = GatedKRXGateway
    return GatedKRXGateway


def _gate_krx(gateway: Any) -> None:
    """Swap the KRX Open API / OpenDART sub-clients for an OffClient when blocked (KIS is fixed-local)."""
    why = blocked("krx_open_api")
    if why:
        gateway.krx = OffClient("krx_open_api", why, empty=("all_quotes", "indices"))
    why = blocked("opendart")
    if why:
        gateway.dart = OffClient("opendart", why)


def krx_gateway() -> Any:
    """The KRX screen's KRXGateway (data/krx/gateway.py: KIS first, then the KRX Open API and OpenDART), built now.
    KIS is fixed-local (rule 1), so it is always the real client; the KRX Open API and OpenDART sub-clients are
    replaced by an OffClient when their source is blocked, so a blocked provider is never reached and the answers say
    why (the OffClient's reason, not "set the key"). Building it reads routes.json at call time only, never at
    import: a broken routes file does not stop the app (routes.py), it turns the two non-fixed sub-clients off.

    The app builds it once and hands the same object to the KRX screen and the engine feed, so after ``reload()`` or
    a key change for one of its sources every gateway built here gets fresh sub-clients and the blocks again, in
    place (D7-G rule 6; PR #133 review 3, A1R3-5). Construction performs no network request."""
    gateway = _krx_class(importlib.import_module("data.krx").KRXGateway)()
    _gate_krx(gateway)
    _KRX_BUILT.add(gateway)
    return gateway


def _refresh_krx(name: str) -> None:
    if name and name not in _KRX_SOURCES and not any(name in SOURCES[s].keys for s in _KRX_SOURCES):
        return
    for gateway in list(_KRX_BUILT):
        base = type(gateway).__mro__[1]
        base.__init__(gateway)                       # fresh KIS / KRX Open API / OpenDART clients, keys read again
        _gate_krx(gateway)


on_change(_refresh_krx)
