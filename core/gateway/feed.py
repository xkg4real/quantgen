"""The engine quote feed with its FMP client built through core/gateway (KEY-4 in main.py; moved here by KEY-5/a G3
so callers can share it; main.py uses it now, the desktop paper screen moves in KEY-5).

core/engine/feed.py stays byte-for-byte as frozen by the S4 owner ruling (T-RO-01, T-CAP-02); this subclass only
replaces where the FMP client comes from. Still built on first use, so a missing key never blocks startup. When FMP
is blocked (off, or served by the company route) there is no FMP client, ``fmp_blocked`` says why, and that reason is
what the feed reports (provider status rows and the engine's per-symbol error) instead of "FMP client unavailable"
(PR #133 review 3, A1R3-4). After a route reload or an FMP key change every affected feed discards its client (D7-G
rule 6), so deleted/replaced keys and sources switched off are respected without restarting the app.

Imported by main.py today (the desktop paper screen is a separate KEY-5 change); importing core.gateway alone does
not import the engine.
"""
from __future__ import annotations

import threading
import weakref

from core import gateway as _gateway
from core.engine.feed import QuoteFeed as _EngineQuoteFeed

__all__ = ["QuoteFeed"]

_FEEDS: "weakref.WeakSet[QuoteFeed]" = weakref.WeakSet()
_FEEDS_LOCK = threading.RLock()


class QuoteFeed(_EngineQuoteFeed):
    """The frozen engine feed, FMP through ``gateway.provider("data.fmp")``."""

    fmp_blocked = ""

    def __init__(self, krx_gateway=None, fmp_client=None):
        super().__init__(krx_gateway, fmp_client)
        with _FEEDS_LOCK:
            _FEEDS.add(self)

    @property
    def fmp(self):
        with self._lock:
            # A cached client is not authority to bypass a route that has since changed.
            why = _gateway.blocked("fmp")
            if why:
                self._fmp = None
                self._fmp_resolved = True
                self.fmp_blocked = ("FMP market data is turned off. Check data-source settings." if why == "off" else
                                    "FMP market data is provided through the company connection. This device's key is not used.")
                return None
            if not self._fmp_resolved or self.fmp_blocked:
                self.fmp_blocked = ""
                try:
                    self._fmp = _gateway.provider("data.fmp").FMPQuoteClient()
                except _gateway.GatewayOff:
                    self._fmp = None
                    self.fmp_blocked = "FMP market data is unavailable. Check data-source settings."
                except Exception:
                    self._fmp = None
                self._fmp_resolved = True
            return self._fmp

    def look_again(self) -> None:
        """Drop the held client, including a successful one: it captured its key at construction."""
        with self._lock:
            self._fmp = None
            self._fmp_resolved = False
            self.fmp_blocked = ""

    def provider_status(self) -> list[dict]:
        out = super().provider_status()
        if self.fmp is None and self.fmp_blocked:
            for row in out:
                if row.get("scope") == "Global" and row.get("provider") == "FMP":
                    row["reason"] = self.fmp_blocked
        return out

    def _from_fmp(self, pairs):
        # A change callback waits for a fetch already in flight; after it returns no old client is reused.
        with self._lock:
            if pairs and self.fmp is None and self.fmp_blocked:
                reason = self.fmp_blocked
                return {symbol: self._fail_none(symbol, reason, permanent=True) for symbol, _ in pairs}
            return super()._from_fmp(pairs)


def _look_again(name="") -> None:
    if name and name != "fmp" and name not in _gateway.SOURCES["fmp"].keys:
        return
    with _FEEDS_LOCK:
        feeds = list(_FEEDS)
    for feed in feeds:
        feed.look_again()


_gateway.on_change(_look_again)
