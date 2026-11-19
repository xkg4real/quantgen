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
    # values and pure helpers that reach no provider. tests/gateway_boundary_acceptance.py reads this tuple (ast):
    # every other name of core.ficc.data counts as a direct provider access there.
    CONSTANTS = ("G10_KRW", "Series", "CurvePanel", "CurveSnapshot", "_period_for", "synthetic_series",
                 "synthetic_curve_panel", "synthetic_fx")

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
        if name == "probe":
            return lambda: _probe(data)
        if name in ("load_many", "load_series"):
            return _batch_loader(data, name)

        def call(*args, **kwargs):
            for source in _ficc_sources(data, name, args, kwargs):
                _need(source)
            return getattr(data, name)(*args, **kwargs)
        call.__name__ = name
        return call


_FRED_ONLY = {"load_treasury_curve", "load_short_rate", "load_policy_rates", "_fred_fetch", "fred_ready"}
_YAHOO_ONLY = {"load_fx_spot", "_yf_fetch", "yfinance_ready"}
_PROVIDER_SOURCE = {"FRED": "fred", "YFINANCE": "yahoo"}


def _ficc_sources(data, name: str, args: tuple, kwargs: dict) -> set[str]:
    """The gateway sources a single-provider FICC call would reach (pure: no provider is called here)."""
    source = str(kwargs.get("source", "auto") or "auto").lower()
    if source == "synthetic":
        return set()
    if name in _FRED_ONLY:
        return {"fred"}
    if name in _YAHOO_ONLY:
        return {"yahoo"}
    return set()


def _id_source(data, raw, source: str) -> str:
    """"fred", "yahoo" or "" (synthetic, or an id the loader will reject itself) for one id of a series request."""
    if source == "synthetic":
        return ""
    if source in ("fred", "yfinance"):
        return "fred" if source == "fred" else "yahoo"
    try:
        return _PROVIDER_SOURCE.get(data._route((raw or "").strip()), "")
    except Exception:
        return ""                                    # the loader raises its own error for a bad id, as before


def _batch_loader(data, name: str):
    """load_many / load_series through the gateway. With nothing blocked this is the module's own loader, unchanged.
    With a provider blocked (off, or on the company route): an explicit ``source=`` for it raises GatewayOff;
    under ``source="auto"`` each blocked id comes back SYNTHETIC with the reason in ``note`` (as load_many treats a
    provider failure) and the other ids are still read, so a FRED+Yahoo sheet keeps its FRED rows."""
    from core import gateway

    def blocked_ids(ids, source):
        mode = str(source or "auto").lower()
        reasons = {}
        for raw in ids:
            sid = _id_source(data, raw, mode)
            if sid and gateway.blocked(sid):
                if mode != "auto":
                    _need(sid)
                reasons[raw] = (sid, gateway.blocked(sid))
        return reasons

    def load_many(ids, *, source: str = "auto", days: int = 756):
        ids = list(ids)                              # an iterator is read once, here
        reasons = blocked_ids(ids, source)
        if not reasons:
            return data.load_many(ids, source=source, days=days)
        allowed = [raw for raw in ids if raw not in reasons]
        got = data.load_many(allowed, source=source, days=days) if allowed else {}
        out = {}
        for raw in ids:
            key = (raw or "").strip()
            if raw in reasons:
                sid, why = reasons[raw]
                provider = "YFINANCE" if sid == "yahoo" else "FRED"
                out[key] = data._degraded(data.synthetic_series(key, days=days, kind=data._synthetic_kind(key)),
                                          provider, f"{sid} is {why} in profile {gateway.profile()}")
            elif key in got:
                out[key] = got[key]
        return out

    if name == "load_many":
        return load_many

    def load_series(id, *, source: str = "auto", days: int = 756, label: str = ""):
        if not blocked_ids([id], source):
            return data.load_series(id, source=source, days=days, label=label)
        from dataclasses import replace
        s = load_many([id], source=source, days=days)[id.strip()]
        return replace(s, label=label) if label else s
    return load_series


def _probe(data) -> dict:
    """core.ficc.data.probe(), unchanged when FRED and Yahoo are both served locally. A blocked provider is not
    called: its row says why (a connection check must not reach a provider the active profile turned off)."""
    from core import gateway
    if not gateway.blocked("fred") and not gateway.blocked("yahoo"):
        return data.probe()
    out = {}
    for name, sid, ready, call in (
            ("fred", "fred", data.fred_ready,
             lambda: data._fred_fetch(["DGS10"], data._start_for(20)).get("DGS10", [])),
            ("yfinance", "yahoo", data.yfinance_ready,
             lambda: data._yf_fetch(["EURUSD=X"], "5d").get("EURUSD=X", []))):
        why = gateway.blocked(sid)
        if why:
            out[name] = {"ok": False, "detail": f"{why} in profile {gateway.profile()}"}
            continue
        if not ready():
            out[name] = {"ok": False, "detail": "library not installed"}
            continue
        try:
            rows = call()
            out[name] = ({"ok": True, "detail": f"{len(rows)} obs, last {rows[-1][0]}"} if rows
                         else {"ok": False, "detail": "no observations returned"})
        except Exception as exc:
            out[name] = {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}
    return out


def _need(source: str) -> None:
    from core import gateway
    gateway._refuse(source)


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
