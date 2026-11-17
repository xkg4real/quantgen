"""Polymarket connector frame for DIDM -- DISABLED.

Held until a lawyer confirms that using Polymarket data from Korea is lawful
(Korea Communications Standards Commission blocking decision reported 2026-08-18;
owner question 4 in sessions/06_DATA_SOURCE_DIDM.md). Not legal advice.

Nothing here makes a network call. Enabling it is a code change reviewed against
the owner's answer, not a setting.
"""
from __future__ import annotations

ENABLED = False
HOLD_REASON = "held: lawyer check on Korean access pending (owner question 4)"


class ConnectorHeld(RuntimeError):
    pass


def fetch_market_history(market_id: str) -> dict:
    raise ConnectorHeld(HOLD_REASON)
