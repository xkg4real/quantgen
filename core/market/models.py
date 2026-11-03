"""Provider-independent market data contracts. No credentials reach a view."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import math
import re

ASSETS = ("domestic_stock", "overseas_stock", "domestic_future", "overseas_future", "bond")
TICK_INTERVALS = ("1tick", "10tick", "100tick")
SECOND_INTERVALS = ("1s", "5s", "10s", "30s")
LIVE_INTERVALS = TICK_INTERVALS + SECOND_INTERVALS
HISTORY_INTERVALS = ("1m", "3m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
INTERVALS = LIVE_INTERVALS + HISTORY_INTERVALS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Instrument:
    asset: str = "domestic_stock"
    code: str = "005930"
    exchange: str = ""

    def __post_init__(self):
        if self.asset not in ASSETS:
            raise ValueError("Unsupported asset")
        code, exchange = self.code.strip().upper(), self.exchange.strip().upper()
        if not re.fullmatch(r"[A-Z0-9.@_-]{1,32}", code):
            raise ValueError("Invalid instrument code")
        if exchange and not re.fullmatch(r"[A-Z0-9]{1,8}", exchange):
            raise ValueError("Invalid exchange")
        if self.asset == "domestic_stock" and not re.fullmatch(r"\d{6}", code):
            raise ValueError("Use a six-digit KRX stock code")
        if self.asset == "overseas_stock" and exchange not in (
                "NAS", "NYS", "AMS", "HKS", "TSE", "SHS", "SZS", "HSX", "HNX"):
            raise ValueError("Select a KIS overseas stock exchange")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "exchange", exchange)

    @property
    def symbol(self) -> str:
        return f"{self.exchange}:{self.code}" if self.exchange else self.code


@dataclass(frozen=True)
class ChartRequest:
    instrument: Instrument = Instrument()
    interval: str = "1d"
    limit: int = 120
    adjusted: bool = False

    def __post_init__(self):
        if self.interval not in INTERVALS:
            raise ValueError("Unsupported chart interval")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or not 20 <= self.limit <= 500:
            raise ValueError("Chart size must be between 20 and 500 bars")


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

    # Preserve actual exchange timestamps even when distinct received bars
    # start within the same second; never invent a finer time resolution.
    sequence: int | None = None
    trade_count: int | None = None

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.open, self.high, self.low, self.close)):
            raise ValueError("Non-finite OHLC price")
        if self.high < max(self.open, self.close, self.low) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC range")
        if self.volume is not None and (not math.isfinite(self.volume) or self.volume < 0):
            raise ValueError("Invalid bar volume")
        for value in (self.sequence, self.trade_count):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
                raise ValueError("Live bar sequence and trade count must be positive integers")


@dataclass(frozen=True)
class MarketQuote:
    instrument: Instrument
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    volume: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    currency: str = "KRW"
    market_time: str = ""
    received_at: str = ""
    source: str = "KIS"
    note: str = ""


@dataclass(frozen=True)
class MarketSnapshot:
    request: ChartRequest
    candles: tuple[Candle, ...]
    quote: MarketQuote | None = None
    fetched_at: str = ""
    source: str = "KIS"
    note: str = ""
    last_tick_at: str = ""
    last_cumulative_volume: float | None = None


@dataclass(frozen=True)
class MarketTick:
    instrument: Instrument
    timestamp: str
    price: float
    volume: float | None = None
    cumulative_volume: float | None = None
    change: float | None = None
    change_pct: float | None = None
    received_at: str = ""
    source: str = "KIS WebSocket"


def with_quote(snapshot: MarketSnapshot, quote: MarketQuote) -> MarketSnapshot:
    return replace(snapshot, quote=quote)
