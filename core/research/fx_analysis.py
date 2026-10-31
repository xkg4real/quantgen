"""Native FX request adapter preserving the existing Flet workflow conventions."""
from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class FXRequest:
    tool: str = "forward"
    source: str = "auto"
    pair: str = "EURUSD"
    domestic_rate: float | None = None
    foreign_rate: float | None = None
    tenor: str = "3m"
    market_forward: float | None = None
    strike: str = "ATM"
    call: bool = True
    atm: float = .08
    rr: float = .005
    bf: float = .003
    top_n: int = 3
    cost_bps: float = 5
    rebalance_days: int = 21
    days: int = 504

    def validate(self):
        from core.ficc.common import parse_tenor
        if self.tool not in {"forward", "option", "carry"} or self.source not in {"auto", "yfinance", "synthetic"}:
            raise ValueError("Unknown FX tool/source")
        if self.tool == "carry":
            for v, lo, hi in ((self.top_n,1,10000),(self.days,60,10000),(self.rebalance_days,1,10000)):
                if type(v) is not int or not lo <= v <= hi: raise ValueError("Invalid carry input")
            if not math.isfinite(self.cost_bps) or self.cost_bps < 0: raise ValueError("Invalid cost")
            return
        pair = self.pair.upper().replace("/", "").replace("=X", "")
        if not re.fullmatch(r"[A-Z]{6}", pair) or pair[:3] == pair[3:]: raise ValueError("Invalid FX pair")
        if parse_tenor(self.tenor) <= 0: raise ValueError("Invalid tenor")
        for v in (self.domestic_rate, self.foreign_rate):
            if v is not None and not math.isfinite(v): raise ValueError("Invalid rate")
        if self.tool == "forward":
            if self.market_forward is not None and (not math.isfinite(self.market_forward) or self.market_forward <= 0):
                raise ValueError("Invalid market forward")
        else:
            if not all(math.isfinite(v) for v in (self.atm, self.rr, self.bf)) or self.atm <= 0:
                raise ValueError("Invalid smile quote")
            s = self.strike.strip().lower()
            if s and s != "atm":
                m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*d", s)
                v = float(m.group(1)) if m else float(s)
                if not math.isfinite(v) or v <= 0 or (m and v >= 100): raise ValueError("Invalid strike")


@dataclass(frozen=True)
class FXOutput:
    request: FXRequest
    data: dict
    sources: tuple
    narrative: str


def execute_fx(request, *, spot_loader=None, rate_loader=None, policy_loader=None):
    request.validate()
    import numpy as np
    from core.ficc import fx, insights
    from core.ficc.common import parse_tenor
    from core.ficc.data import load_fx_spot, load_short_rate, load_policy_rates, G10_KRW
    spot_loader = spot_loader or load_fx_spot
    rate_loader = rate_loader or load_short_rate
    policy_loader = policy_loader or load_policy_rates
    rate_source = "synthetic" if request.source == "synthetic" else "auto"
    if request.tool == "carry":
        pairs = ["USD"+c if c in ("JPY", "KRW", "CAD", "CHF") else c+"USD" for c in G10_KRW if c != "USD"]
        spots = {p:spot_loader(p, source=request.source, days=request.days) for p in pairs}
        rates = policy_loader(list(G10_KRW), days=request.days, source=rate_source)
        rows = fx.carry_table(spots, rates)
        bt = fx.carry_backtest(spots, rates, top_n=request.top_n, cost_bps=request.cost_bps,
                               rebalance_days=request.rebalance_days)
        return FXOutput(request, {"rows":rows, "backtest":bt}, tuple(spots.values())+tuple(rates.values()),
                        insights.narrate_carry(rows, bt))
    spot = spot_loader(request.pair, source=request.source)
    pair = spot.id[:6]
    base, quote = pair[:3], pair[3:]
    sources = [spot]
    def rate(typed, currency):
        if typed is not None: return typed
        series = rate_loader(currency, source=rate_source)
        sources.append(series)
        return float(series.last)
    rd, rf = rate(request.domestic_rate, quote), rate(request.foreign_rate, base)
    S, T = float(spot.last), parse_tenor(request.tenor)
    F = fx.forward(S, rd, rf, T)
    data = dict(spot=spot, pair=pair, base=base, quote=quote, S=S, T=T, rd=rd, rf=rf, forward=F)
    if request.tool == "forward":
        pts, carry = fx.forward_points(S, F), fx.carry(rd, rf)
        basis = None if request.market_forward is None else fx.implied_basis(S, request.market_forward, rd, rf, T)
        curve = {parse_tenor(t):fx.forward(S, rd, rf, parse_tenor(t)) for t in ("1m", "3m", "6m", "1y", "2y")}
        curve[T] = F
        data.update(points=pts, carry=carry, basis=basis, curve=sorted(curve.items()))
        narrative = insights.narrate_fx_forward(pair, S, F, pts, carry, basis)
    else:
        points = fx.smile_from_quotes(fx.SmileQuote(T, request.atm, request.rr, request.bf), S, rd, rf)
        fit = fx.calibrate_sabr(F, T, [p.strike for p in points], [p.vol for p in points], beta=1)
        strike = request.strike.strip().lower()
        if not strike or strike == "atm": K = F * math.exp(.5*request.atm**2*T)
        elif re.fullmatch(r"(\d+(?:\.\d+)?)\s*d", strike):
            K = fx.strike_from_delta(float(strike[:-1])/100, S, T, rd, rf, request.atm, call=request.call)
        else: K = float(strike)
        vol = float(fx.smile_curve(fit, F, T, np.array([K]))[0])
        report = fx.garman_kohlhagen(S, K, T, rd, rf, vol, request.call)
        grid = np.linspace(min(points[0].strike, K)*.98, max(points[-1].strike, K)*1.02, 80)
        data.update(points=points, fit=fit, report=report, grid=grid, vols=fx.smile_curve(fit, F, T, grid))
        from core.ficc.sabr_diagnostics import fit_diagnostics
        data['sabr_diagnostics'] = fit_diagnostics(fit, F, T, points, pricing_strike=K)
        narrative = insights.narrate_fx_option(report, points, fit, diagnostics=data['sabr_diagnostics'])
    return FXOutput(request, data, tuple(sources), narrative)
