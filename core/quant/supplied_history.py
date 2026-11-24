"""Price observations supplied by a caller. Contains no loaders or provider configuration."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

TRADING_DAYS = 252


@dataclass(frozen=True)
class SuppliedHistory:
    symbol: str
    source: str                       # "FMP" | "KIS" | "YFINANCE" | "UPBIT" | "BINANCE" | "SYNTHETIC"
    dates: tuple[str, ...]            # ISO dates, ascending
    closes: tuple[float, ...]
    note: str = ""
    # "total" = adjusted for splits AND dividends (a total-return series);
    # "split" = adjusted for splits only (a price-return series);
    # ""      = not applicable (index, FX, futures, crypto, synthetic) or unknown.
    adjustment: str = ""
    # M1 provenance (appended with a default so positional construction keeps working):
    # "provisional_intraday" = fetched while the market may have been trading, the last bar is a running price;
    # ""                     = no status claimed (a History is a display shape; acting reads use core.ficc.pit).
    status: str = ""

    def __len__(self) -> int:
        return len(self.closes)

    @property
    def last(self) -> float:
        return self.closes[-1]

    @property
    def first_date(self) -> str:
        return self.dates[0] if self.dates else ""

    @property
    def last_date(self) -> str:
        return self.dates[-1] if self.dates else ""

    def prices(self) -> np.ndarray:
        return np.asarray(self.closes, dtype=float)

    def log_returns(self) -> np.ndarray:
        px = self.prices()
        return np.diff(np.log(px))

    def simple_returns(self) -> np.ndarray:
        px = self.prices()
        return px[1:] / px[:-1] - 1.0

