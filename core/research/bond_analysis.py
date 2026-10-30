"""Native Bonds input adapter. Pricing, scenarios and hedge math stay in core.ficc."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BondRequest:
    coupon: float = .045
    maturity: float = 10
    frequency: int = 2
    notional: float = 1_000_000
    price: float | None = None
    yield_rate: float | None = .045
    source: str = "auto"
    tool: str = "calc"
    position_dv01: float | None = None
    ctd_dv01: float = 65
    conversion_factor: float = .8

    def validate(self):
        if self.source not in {"auto","fred","synthetic"} or self.tool not in {"calc","scenarios","hedge"}:
            raise ValueError("Unknown source/tool")
        if (self.price is None) == (self.yield_rate is None):
            raise ValueError("Enter exactly one of price or yield")
        for key in ('coupon','maturity','notional','price','yield_rate','position_dv01','ctd_dv01','conversion_factor'):
            value=getattr(self,key)
            if value is not None and not math.isfinite(value):raise ValueError('Non-finite input')
        if self.frequency not in (1,2,4) or self.coupon<0 or self.maturity<=0 or self.notional<=0:
            raise ValueError("Invalid bond terms")
        if self.tool=='hedge' and (self.ctd_dv01<=0 or self.conversion_factor<=0):
            raise ValueError('Positive CTD DV01 and conversion factor required')


@dataclass(frozen=True)
class BondOutput:
    request: BondRequest
    panel: object
    curve: object
    analytics: object
    scenarios: tuple
    hedge: tuple | None
    yield_axis: tuple
    price_curve: tuple
    duration_tangent: tuple
    narrative: str


def execute_bond(request, *, curve_loader=None):
    request.validate()
    import numpy as np
    from core.ficc.bonds import Bond, analyze_bond, scenario_pnl, futures_hedge_ratio, price_from_yield
    from core.ficc.curves import curve_from_snapshot
    from core.ficc.insights import narrate_bond
    if curve_loader is None:
        from core.ficc.data import load_treasury_curve
        curve_loader=load_treasury_curve
    bond=Bond(coupon=request.coupon,maturity=request.maturity,freq=request.frequency,notional=request.notional)
    panel=curve_loader(source=request.source)
    curve=curve_from_snapshot(panel.latest())
    a=analyze_bond(bond,price=request.price,ytm=request.yield_rate,curve=curve)
    scenarios=tuple(scenario_pnl(bond,curve,a.price)) if request.tool=='scenarios' else ()
    hedge=None
    if request.tool=='hedge':
        pos=request.position_dv01 if request.position_dv01 is not None else a.dv01
        hedge=(pos,request.ctd_dv01,request.conversion_factor,
               futures_hedge_ratio(pos,request.ctd_dv01,request.conversion_factor))
    # Same display sampling and duration tangent as ui.fcharts.price_yield_chart.
    ys=np.linspace(a.ytm-.03,a.ytm+.03,121);ys=ys[1+ys/bond.freq>0]
    prices=tuple(float(price_from_yield(bond,y)) for y in ys)
    tangent=tuple(float(a.price*(1-a.modified*(y-a.ytm))) for y in ys)
    return BondOutput(request,panel,curve,a,scenarios,hedge,tuple(float(y*100) for y in ys),prices,tangent,
                      narrate_bond(a,list(scenarios) if scenarios else None))
