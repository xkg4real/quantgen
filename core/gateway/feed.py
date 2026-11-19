"""The engine quote feed with its FMP client built through core/gateway (KEY-4 in main.py; moved here by KEY-5/a G3
so every screen that runs the engine uses the same class).

core/engine/feed.py stays byte-for-byte as frozen by the S4 owner ruling (T-RO-01, T-CAP-02); this subclass only
replaces where the FMP client comes from. Still built on first use, so a missing key never blocks startup. When FMP
is blocked (off, or served by the company route) there is no FMP client, ``fmp_blocked`` says why, and that reason is
what the feed reports (provider status rows and the engine's per-symbol error) instead of "FMP client unavailable"
(PR #133 review 3, A1R3-4). After a route reload or an FMP key change a feed that has no client looks again (D7-G
rule 6), so a source switched back on is picked up without restarting the app.

Imported only by code that runs the engine (main.py, the desktop paper screen); importing core.gateway alone does
not import the engine.
"""
from __future__ import annotations

import weakref

from core import gateway as _gateway
from core.engine.feed import QuoteFeed as _EngineQuoteFeed

__all__ = ["QuoteFeed"]

_FEEDS: "weakref.WeakSet[QuoteFeed]" = weakref.WeakSet()


class QuoteFeed(_EngineQuoteFeed):
    """The frozen engine feed, FMP through ``gateway.provider("data.fmp")``."""

    fmp_blocked = ""

    def __init__(self, krx_gateway=None, fmp_client=None):
        super().__init__(krx_gateway, fmp_client)
        _FEEDS.add(self)

    @property
    def fmp(self):
        if not self._fmp_resolved:
            with self._lock:
                if not self._fmp_resolved:
                    self.fmp_blocked = ""
                    try:
                        self._fmp = _gateway.provider("data.fmp").FMPQuoteClient()
                    except _gateway.GatewayOff as exc:
                        self._fmp, self.fmp_blocked = None, str(exc)
                    except Exception:
                        self._fmp = None
                    self._fmp_resolved = True
        return self._fmp

    def look_again(self) -> None:
        """Forget a missing FMP client so the next use resolves it again (route or key changed). A working client
        is kept: the gateway's own key-change hook already refreshes it."""
        with self._lock:
            if self._fmp_resolved and self._fmp is None:
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
        if pairs and self.fmp is None and self.fmp_blocked:
            reason = self.fmp_blocked
            return {symbol: self._fail_none(symbol, reason, permanent=True) for symbol, _ in pairs}
        return super()._from_fmp(pairs)


def _look_again(*_ignored) -> None:
    for feed in list(_FEEDS):
        feed.look_again()


_gateway.on_change(_look_again)
