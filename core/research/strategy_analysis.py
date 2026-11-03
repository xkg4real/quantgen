"""Validated native requests for the existing Strategy Lab and card display."""
from dataclasses import dataclass
import math
import re
from .strategy_workflow import FAMILIES


@dataclass(frozen=True)
class StrategyRequest:
    family: str = 'trend_switch'
    symbols: tuple[str, ...] = ('SPY', 'QQQ', 'TLT', 'GLD')
    source: str = 'synthetic'
    cost_bps: float | None = None
    days: int = 1500
    tool: str = 'run'

    def validate(self):
        if self.tool == 'cards':
            return
        if self.tool != 'run' or self.family not in FAMILIES:
            raise ValueError('Unknown strategy tool/family')
        if self.source not in {'auto', 'kis', 'fmp', 'yfinance', 'crypto', 'synthetic'}:
            raise ValueError('Unknown history source')
        if not 1 <= len(self.symbols) <= 15 or len(set(self.symbols)) != len(self.symbols):
            raise ValueError('Choose distinct symbols')
        if any(not re.fullmatch(r'[A-Z0-9.^=-]{1,40}', s) for s in self.symbols):
            raise ValueError('Invalid symbol')
        if self.family == 'pairs' and len(self.symbols) != 2:
            raise ValueError('Pairs requires exactly two symbols in y,x order')
        if self.cost_bps is not None and (not math.isfinite(self.cost_bps) or self.cost_bps < 0):
            raise ValueError('Invalid transaction cost')
        if type(self.days) is not int or not 900 <= self.days <= 10000:
            raise ValueError('History must cover at least the existing walk-forward window')


@dataclass(frozen=True)
class StrategyOutput:
    request: StrategyRequest
    data: dict


def execute_strategy(request, *, runner=None, cards_loader=None):
    request.validate()
    from .strategy_workflow import run_family, load_cards
    if request.tool == 'cards':
        return StrategyOutput(request, {'cards': (cards_loader or load_cards)()})
    data = (runner or run_family)(request.family, list(request.symbols), source=request.source,
                                 cost_bps=request.cost_bps, days=request.days)
    return StrategyOutput(request, data)
