"""UI-neutral portfolio workflow; existing estimators/solvers remain unchanged."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PortfolioRequest:
    symbols: tuple[str, ...]
    source: str = "auto"
    objective: str = "max_sharpe"
    max_weight: float = 1.0
    rf_rate: float = .03

    def validate(self):
        if not 2 <= len(self.symbols) <= 15 or len(set(self.symbols)) != len(self.symbols):
            raise ValueError("Choose 2–15 distinct symbols")
        if any(not s.strip() or len(s)>120 for s in self.symbols):
            raise ValueError("Invalid symbol")
        if self.source not in {"auto", "fmp", "kis", "yfinance", "synthetic"}:
            raise ValueError("Unknown source")
        if self.objective not in {"max_sharpe", "min_vol", "risk_parity", "equal_weight"}:
            raise ValueError("Unknown objective")
        if not math.isfinite(self.rf_rate) or not 0 < self.max_weight <= 1:
            raise ValueError("Invalid rate/weight")


@dataclass(frozen=True)
class PortfolioOutput:
    request: PortfolioRequest
    histories: tuple
    stats: object
    portfolios: dict
    frontier: object
    narrative: str
    convention_warning: str


def execute_portfolio(request, *, history_loader=None):
    request.validate()
    from core.quant.history import load_history, convention_warning
    from core.quant.risk import align_histories
    from core.quant.optimize import OBJECTIVES, optimize_portfolio, efficient_frontier
    from core.quant.insights import narrate_portfolio
    loader = history_loader or load_history
    histories = tuple(loader(s, source=request.source) for s in request.symbols)
    stats = align_histories(histories)
    portfolios = {o: optimize_portfolio(stats, objective=o, rf_rate=request.rf_rate,
        max_weight=request.max_weight if o == request.objective else 1.0) for o in OBJECTIVES}
    frontier = efficient_frontier(stats, rf_rate=request.rf_rate)
    return PortfolioOutput(request, histories, stats, portfolios, frontier,
        narrate_portfolio(portfolios[request.objective]), convention_warning(histories))
