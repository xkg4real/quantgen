"""Bounded adjusted-history scores for a curated list; no new provider routes.

Owner A4, 2026-11-12: visible in the development app; commercial publication review remains unresolved.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from core.market.models import ChartRequest
from core.research.qscore import compute_q_score

ENABLED = True  # Single switch for the future commercial-product decision.
CANDIDATES = 20
FAILURE_RETRY_SECONDS = 300


class ScoreCache:
    """One serial worker owns this cache. Successful histories refresh once per market date, failures after 5 min."""
    def __init__(self, load=None):
        self.load = load
        self.entries = {}

    def run(self, records, cancelled=lambda: False, now=None):
        now = now or datetime.now(timezone.utc)
        # Bounded, explicit universe: highest available trading value; missing values last, ties by code.
        candidates = sorted(records, key=lambda r: (r.trading_value is None, -(r.trading_value or 0), r.member.code))[:CANDIDATES]
        results = {}
        for row in candidates:
            if cancelled():
                break
            instrument = row.member.instrument
            if instrument is None:
                continue
            zone = 'America/New_York' if instrument.asset == 'overseas_stock' else 'Asia/Seoul'
            key = (instrument.asset, instrument.exchange, instrument.code)
            day = now.astimezone(ZoneInfo(zone)).date()
            cached = self.entries.get(key)
            if cached and cached[0] == day and (cached[2].get('status') == 'ready' or
                    (now - cached[1]).total_seconds() < FAILURE_RETRY_SECONDS):
                results[key] = cached[2]
                continue
            try:
                if self.load is None:
                    from data.kis_workspace import MarketDataService
                    self.load = MarketDataService().load
                snapshot = self.load(ChartRequest(instrument, '1d', 260, adjusted=True))
                result = compute_q_score(snapshot, now=now)
            except Exception:
                result = {'status': 'unavailable', 'reason': 'history_unavailable', 'score': None, 'stars': None}
            if cancelled():
                break
            self.entries[key] = day, now, result
            results[key] = result
        return results
