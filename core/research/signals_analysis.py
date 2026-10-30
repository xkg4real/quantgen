"""Descriptive signals and the existing costed single-strategy backtest."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SignalsRequest:
    tool: str = 'ma_cross'
    symbol: str = 'AAPL'
    source: str = 'auto'
    fast: int = 20
    slow: float = 50
    cost_bps: float = 10

    def validate(self):
        if self.tool not in {'ma_cross','momentum','rsi_revert'} or self.source not in {'auto','fmp','kis','synthetic'}:
            raise ValueError('Unknown strategy/source')
        if not self.symbol.strip() or type(self.fast) is not int or self.fast<1:
            raise ValueError('Invalid symbol or lookback')
        if not math.isfinite(self.cost_bps) or self.cost_bps<0:raise ValueError('Invalid cost')
        if self.tool=='ma_cross' and (not math.isfinite(self.slow) or not float(self.slow).is_integer() or self.slow<=self.fast):
            raise ValueError('Slow must be an integer greater than fast')
        if self.tool=='rsi_revert' and (not math.isfinite(self.slow) or not 30<self.slow<=100):
            raise ValueError('RSI exit must be in (30,100]')

    def parameters(self):
        self.validate()
        if self.tool=='ma_cross':return dict(fast=self.fast,slow=int(self.slow))
        if self.tool=='momentum':return dict(lookback=self.fast)
        return dict(period=self.fast,buy_below=30.,exit_above=self.slow)


@dataclass(frozen=True)
class SignalsOutput:
    request: SignalsRequest
    history: object
    report: object
    backtest: object
    narrative: str


def execute_signals(request, *, history_loader=None):
    parameters=request.parameters()
    from core.quant.signals import compute_signals
    from core.quant.backtest import run_backtest
    from core.quant import insights
    if history_loader is None:
        from core.quant.history import load_history
        history_loader=load_history
    history=history_loader(request.symbol.strip(),source=request.source)
    report=compute_signals(history)
    backtest=run_backtest(history,strategy=request.tool,params=parameters,cost_bps=request.cost_bps)
    return SignalsOutput(request,history,report,backtest,insights.narrate_signals(report)+' '+insights.narrate_backtest(backtest))
