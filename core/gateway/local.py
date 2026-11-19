"""The local routes: `local_key` (the user's key on this PC) and `keyless` (public sources), served by the existing
clients in data/ and core/ficc/data.py (KEY-3; GATEWAY_DESIGN.md section 1). Clients are built lazily, kept, and
rebuilt when a key they depend on changes (D7-G rule 6)."""
from __future__ import annotations

import importlib
import threading
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

    def client(self, source: str) -> Any:
        with self._lock:
            if source not in self._clients:
                make = self._overrides.get(source) or _resolve(self._factories[source])
                self._clients[source] = make()
            return self._clients[source]

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
    """FRED and Yahoo series through core/ficc/data.py (keyless). Only the listed loaders are exposed."""

    EXPOSED = ("load_series", "load_many", "load_treasury_curve", "load_short_rate", "load_policy_rates",
               "load_fx_spot")

    def __init__(self):
        from core.ficc import data
        self._data = data

    def __getattr__(self, name: str):
        if name in FiccData.EXPOSED:
            return getattr(self._data, name)
        raise AttributeError(name)


class _KeyedFeature:
    keys: tuple[str, ...] = ()

    def ready(self) -> bool:
        from core import credentials
        return all(credentials.status(k)["present"] for k in self.keys)


class AnthropicKey(_KeyedFeature):
    """Placeholder until KEY-4 moves core/quant/insights.py behind the gateway; tells whether the key is set."""
    keys = ("ANTHROPIC_API_KEY",)


class GsMarquee(_KeyedFeature):
    """Placeholder until KEY-4 moves core/quant/gsq.py behind the gateway."""
    keys = ("GS_CLIENT_ID", "GS_CLIENT_SECRET")
