"""The local routes: `local_key` (the user's key on this PC) and `keyless` (public sources), served by the existing
clients in data/ and core/ficc/data.py (KEY-3; GATEWAY_DESIGN.md section 1). Clients are built lazily, kept, and
rebuilt when a key they depend on changes (D7-G rule 6)."""
from __future__ import annotations

import importlib
import threading
import weakref
from typing import Any, Callable


def _resolve(spec: str) -> Callable[[], Any]:
    module, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module), attr)


class LocalRoute:
    def __init__(self, factories: dict[str, str]):
        self._factories = dict(factories)
        self._clients: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._overrides: dict[str, Callable[[], Any]] = {}
        self._handed: dict[str, list[weakref.ref]] = {}   # every client given out, weakly (D7-G rule 6)

    def client(self, source: str) -> Any:
        with self._lock:
            if source not in self._clients:
                make = self._overrides.get(source) or _resolve(self._factories[source])
                made = make()
                self._clients[source] = made
                try:
                    self._handed.setdefault(source, []).append(weakref.ref(made))
                except TypeError:
                    pass                               # not weak-referenceable: only the cached one is updated
            return self._clients[source]

    def held(self, source: str) -> list[Any]:
        """Clients of ``source`` given out earlier and still alive somewhere (a screen or a model holding one).
        Dead references are dropped here."""
        with self._lock:
            refs = [r for r in self._handed.get(source, []) if r() is not None]
            self._handed[source] = refs
            alive = [r() for r in refs]
            current = self._clients.get(source)
        if current is not None and all(c is not current for c in alive):
            alive.append(current)
        return [c for c in alive if c is not None]

    def reload(self, source: str | None = None) -> None:
        with self._lock:
            if source is None:
                self._clients.clear()
            else:
                self._clients.pop(source, None)

    def override(self, source: str, factory: Callable[[], Any] | None) -> None:
        """Tests and the fake server: serve `source` from `factory` instead of the real client."""
        with self._lock:
            if factory is None:
                self._overrides.pop(source, None)
            else:
                self._overrides[source] = factory
            self._clients.pop(source, None)


class CryptoPublic:
    """Keyless crypto prices: Upbit and Binance public endpoints and CoinGecko, under one client."""

    def __init__(self):
        from data.crypto import crypto_client as cc
        self._cc = cc
        self._upbit = cc.UpbitPublic()
        self._binance = cc.BinancePublic()

    def upbit_daily(self, market: str = "KRW-BTC", *, days: int = 504):
        return self._upbit.daily(market, days=days)

    def upbit_ticker(self, markets="KRW-BTC") -> list[dict]:
        return self._upbit.ticker(markets)

    def binance_daily(self, symbol: str = "BTCUSDT", **kwargs):
        return self._binance.daily(symbol, **kwargs)

    def binance_funding(self, symbol: str = "BTCUSDT", *, days: int = 730):
        return self._binance.funding(symbol, days=days)

    def binance_premium_index(self, symbol: str = "BTCUSDT") -> dict:
        return self._binance.premium_index(symbol)

    def binance_open_interest_hist(self, symbol: str = "BTCUSDT", **kwargs) -> list[dict]:
        return self._binance.open_interest_hist(symbol, **kwargs)

    def coingecko_top(self, n: int = 20) -> list[dict]:
        return self._cc.coingecko_top(n)


class FiccData:
    """FRED and Yahoo series through core/ficc/data.py (keyless). Only the listed names are exposed, each looked up
    on the module at call time (a test's patch of core.ficc.data is honoured, as with a direct import inside a
    function). Every call is checked against the routes of the providers it would use (KEY-4): ``yahoo: off``
    refuses a Yahoo ticker, ``fred: off`` a FRED id; synthetic requests need neither."""

    EXPOSED = ("load_series", "load_many", "load_treasury_curve", "load_short_rate", "load_policy_rates",
               "load_fx_spot", "_yf_fetch", "_fred_fetch", "probe", "fred_ready", "yfinance_ready")
    # values and pure helpers that reach no provider
    CONSTANTS = ("G10_KRW", "Series", "CurvePanel", "_period_for", "synthetic_series", "synthetic_curve_panel",
                 "synthetic_fx")

    def __init__(self):
        from core.ficc import data
        self._data = data

    @property
    def yfinance(self):
        """The module's yfinance handle (None when not installed); Yahoo only."""
        _need("yahoo")
        return self._data._yf

    def __getattr__(self, name: str):
        if name in FiccData.CONSTANTS:
            return getattr(self._data, name)
        if name not in FiccData.EXPOSED:
            raise AttributeError(name)
        data = self._data

        def call(*args, **kwargs):
            for source in _ficc_sources(data, name, args, kwargs):
                _need(source)
            return getattr(data, name)(*args, **kwargs)
        call.__name__ = name
        return call


_FRED_ONLY = {"load_treasury_curve", "load_short_rate", "load_policy_rates", "_fred_fetch", "fred_ready"}
_YAHOO_ONLY = {"load_fx_spot", "_yf_fetch", "yfinance_ready"}


def _ficc_sources(data, name: str, args: tuple, kwargs: dict) -> set[str]:
    """The gateway sources a FICC call would reach (pure: no provider is called here)."""
    source = str(kwargs.get("source", "auto") or "auto").lower()
    if source == "synthetic":
        return set()
    if name == "probe":
        return set()                                 # a connection check reports each provider; it is not data
    if name in _FRED_ONLY:
        return {"fred"}
    if name in _YAHOO_ONLY:
        return {"yahoo"}
    if source == "fred":
        return {"fred"}
    if source == "yfinance":
        return {"yahoo"}
    ids = args[0] if args else kwargs.get("ids", kwargs.get("id", ()))
    ids = [ids] if isinstance(ids, str) else list(ids or ())
    out = set()
    for i in ids:
        try:
            out.add("yahoo" if data._route((i or "").strip()) == "YFINANCE" else "fred")
        except Exception:
            pass                                     # the loader raises its own error for a bad id, as before
    return out


def _need(source: str) -> None:
    from core import gateway
    if gateway.route_of(source) == "off":
        raise gateway.GatewayOff(f"{source} is off in profile {gateway.profile()}")


# Provider URLs core needs (KEY-4). Not keys; routes.py's key-shape check does not apply to URLs.
ENDPOINTS = {"anthropic": "https://api.anthropic.com/v1/messages"}


class _KeyedFeature:
    keys: tuple[str, ...] = ()

    def ready(self) -> bool:
        from core import credentials
        return all(credentials.status(k)["present"] for k in self.keys)


class AnthropicKey(_KeyedFeature):
    """Whether the Anthropic key is set. core/quant/insights.py sends its request itself with
    ``gateway.local_key("anthropic")`` and ``gateway.endpoint("anthropic")`` (KEY-4)."""
    keys = ("ANTHROPIC_API_KEY",)


class GsMarquee(_KeyedFeature):
    """Whether the GS Marquee keys are set. core/quant/gsq.py opens its session itself through
    ``gateway.provider("gs_quant.session")`` and ``gateway.local_key("gs_marquee", "id"/"secret")`` (KEY-4)."""
    keys = ("GS_CLIENT_ID", "GS_CLIENT_SECRET")
