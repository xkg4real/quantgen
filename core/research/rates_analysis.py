"""Immutable native Rates requests; all pricing remains in core.ficc.

Rates are decimals here. The UI alone converts percent and normal-volatility bp.
No provider call is made until the selected tool's input has been validated.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RatesRequest:
    tool: str = "curve"
    source: str = "auto"
    method: str = "bootstrap"
    lookback: int = 20
    tenor: str = "10y"
    fixed_rate: float | None = None
    notional: float = 1_000_000
    pay_fixed: bool = True
    kind: str = "swaption"
    expiry: str = "1y"
    strike: float | None = None
    option_model: str = "bachelier"
    vol: float = .008
    model: str = "vasicek"
    horizon: float = 1
    n_paths: int = 5000
    threshold: float | None = None
    instrument: str = "none"
    coupon: float = .04

    def validate(self):
        from core.ficc.common import FICCError, parse_forward_tenor, parse_tenor
        if self.tool not in {"curve", "swap", "option", "sim"} or self.source not in {"auto", "fred", "synthetic"}:
            raise ValueError("Unknown Rates tool/source")
        if self.tool == "curve":
            if self.method not in {"bootstrap", "nelson_siegel", "svensson"}:
                raise ValueError("Unknown curve method")
            if type(self.lookback) is not int or self.lookback < 1:
                raise ValueError("Lookback must be a positive integer")
        if self.tool in {"swap", "option"}:
            for x in (self.notional, self.fixed_rate if self.tool == 'swap' else self.strike):
                if x is not None and not math.isfinite(x): raise ValueError("Non-finite input")
            if self.notional <= 0: raise ValueError("Notional must be positive")
            if self.tool == "swap":
                try: start, tenor = parse_forward_tenor(self.tenor)
                except FICCError: start, tenor = 0, parse_tenor(self.tenor)
                if start < 0 or tenor <= 0: raise ValueError("Invalid swap tenor")
            else:
                if self.kind not in {"swaption", "cap", "floor"} or self.option_model not in {"bachelier", "black"}:
                    raise ValueError("Unknown option kind/model")
                if not math.isfinite(self.vol) or self.vol <= 0: raise ValueError("Volatility must be positive")
                if parse_tenor(self.tenor) <= 0: raise ValueError("Invalid tenor")
                if self.kind == "swaption" and parse_tenor(self.expiry) <= 0: raise ValueError("Invalid expiry")
        if self.tool == "sim":
            if self.model not in {"vasicek", "cir", "hull_white"} or self.instrument not in {"none", "bond", "swap"}:
                raise ValueError("Unknown simulation model/instrument")
            if not math.isfinite(self.horizon) or not 0 < self.horizon <= 30:
                raise ValueError("Horizon must be in (0, 30] years")
            if type(self.n_paths) is not int or not 100 <= self.n_paths <= 100000:
                raise ValueError("Paths must be an integer in [100, 100000]")
            if self.threshold is not None and not math.isfinite(self.threshold): raise ValueError("Invalid threshold")
            if self.instrument != "none" and parse_tenor(self.tenor) <= self.horizon:
                raise ValueError("Instrument must mature after the simulation horizon")
            if self.instrument == "bond" and (not math.isfinite(self.coupon) or self.coupon < 0):
                raise ValueError("Invalid coupon")


@dataclass(frozen=True)
class RatesOutput:
    request: RatesRequest
    panel: object
    curve: object
    report: object
    narrative: str
    pca: object = None
    series: object = None
    horizon_pv: object = None


def execute_rates(request, *, curve_loader=None, rate_loader=None):
    request.validate()
    from core.ficc import insights
    from core.ficc.common import FICCError, parse_tenor, parse_forward_tenor
    from core.ficc.curves import analyze_curve, curve_from_snapshot, curve_pca
    from core.ficc.swaps import Swap, Swaption, analyze_swap, price_swaption, price_cap_floor
    if curve_loader is None:
        from core.ficc.data import load_treasury_curve
        curve_loader = load_treasury_curve
    panel = curve_loader(source=request.source)
    if request.tool == "curve":
        report = analyze_curve(panel, method=request.method, lookback=request.lookback)
        try: pca = curve_pca(panel)
        except FICCError: pca = None
        return RatesOutput(request, panel, report.curve, report, insights.narrate_curve(report, pca), pca=pca)
    curve = curve_from_snapshot(panel.latest())
    if request.tool == "swap":
        try: start, tenor = parse_forward_tenor(request.tenor)
        except FICCError: start, tenor = 0, parse_tenor(request.tenor)
        report = analyze_swap(Swap(tenor, fixed_rate=request.fixed_rate, notional=request.notional,
                                  pay_fixed=request.pay_fixed, start=start), curve)
        return RatesOutput(request, panel, curve, report, insights.narrate_swap(report))
    if request.tool == "option":
        if request.kind == "swaption":
            option = Swaption(parse_tenor(request.expiry), parse_tenor(request.tenor),
                              strike=request.strike, payer=request.pay_fixed, notional=request.notional)
            report = price_swaption(option, curve, vol=request.vol, model=request.option_model)
            narrative = insights.narrate_swaption(report)
        else:
            report = price_cap_floor(curve, parse_tenor(request.tenor), request.strike,
                                    vol=request.vol, model=request.option_model, cap=request.kind == "cap",
                                    notional=request.notional)
            narrative = insights.narrate_cap_floor(report)
        return RatesOutput(request, panel, curve, report, narrative)
    from core.ficc.ratesim import calibrate, simulate, horizon_pv_distribution
    from core.ficc.bonds import Bond
    if rate_loader is None:
        from core.ficc.data import load_short_rate
        rate_loader = load_short_rate
    series = rate_loader("USD", source=request.source)
    params = calibrate(series, model=request.model)
    report = simulate(params, horizon=request.horizon, n_paths=request.n_paths,
                      threshold=request.threshold, curve=curve, seed=7)
    hpv = None
    if request.instrument == "bond":
        hpv = horizon_pv_distribution(params, report, kind="bond", curve=curve,
                                     bond=Bond(coupon=request.coupon, maturity=parse_tenor(request.tenor)))
    elif request.instrument == "swap":
        hpv = horizon_pv_distribution(params, report, kind="swap", curve=curve,
                                     swap=Swap(tenor=parse_tenor(request.tenor)))
    return RatesOutput(request, panel, curve, report, insights.narrate_ratesim(report, hpv),
                       series=series, horizon_pv=hpv)
