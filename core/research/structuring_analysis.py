"""Native structured-note terms. Existing core pricers and hedge conventions only."""
from dataclasses import dataclass, replace
import math


@dataclass(frozen=True)
class StructuringRequest:
    tool: str = 'ppn'
    source: str = 'auto'
    maturity: str = '3y'
    notional: float = 1_000_000
    underlying: str = 'FX'
    futures_dv01: float | None = None
    spot: float = 1.10
    vol: float = .08
    r_for: float = .02
    protection: float = 1
    issue: float = 100
    margin: float = 1
    strike_pct: float = .95
    coupon: float | None = None
    base_ccy: str = 'USD'
    quote_ccy: str = 'KRW'
    strike: float = 1300
    leverage: float = 4
    floor: float = 0
    cap: float | None = None
    frequency: int = 1

    def validate(self):
        from core.ficc.common import parse_tenor
        if self.tool not in {'ppn','rc','dcd','steep'} or self.source not in {'auto','fred','synthetic'}:
            raise ValueError('Unknown product/source')
        if parse_tenor(self.maturity) <= 0 or not math.isfinite(self.notional) or self.notional <= 0:
            raise ValueError('Positive maturity and notional required')
        if self.futures_dv01 is not None and (not math.isfinite(self.futures_dv01) or self.futures_dv01 <= 0):
            raise ValueError('Futures DV01 must be positive')
        keys = {'ppn':('spot','vol','r_for','protection','issue','margin'),
                'rc':('spot','vol','r_for','strike_pct','coupon','issue','margin'),
                'dcd':('spot','vol','r_for','strike','margin'),
                'steep':('leverage','floor','cap','issue')}[self.tool]
        for key in keys:
            value=getattr(self,key)
            if value is not None and not math.isfinite(value):raise ValueError('Non-finite input')
        if self.tool != 'steep' and (self.spot <= 0 or self.vol < 0):raise ValueError('Invalid spot or volatility')
        if self.tool in ('ppn','rc') and self.underlying not in {'FX','EQ'}:raise ValueError('Unknown underlying')
        if self.tool == 'dcd' and (self.strike<=0 or len(self.base_ccy)!=3 or len(self.quote_ccy)!=3 or self.base_ccy==self.quote_ccy):
            raise ValueError('Invalid currency pair or strike')
        if self.tool == 'steep' and (type(self.frequency) is not int or self.frequency < 1):raise ValueError('Invalid frequency')


@dataclass(frozen=True)
class StructuringOutput:
    request: StructuringRequest
    panel: object
    curve: object
    report: object
    narrative: str


def execute_structuring(request, *, curve_loader=None):
    request.validate()
    from core.ficc import structured, insights
    from core.ficc.common import parse_tenor
    from core.ficc.curves import curve_from_snapshot
    if curve_loader is None:
        from core.ficc.data import load_treasury_curve
        curve_loader=load_treasury_curve
    q=request
    panel=curve_loader(source=q.source)
    curve=curve_from_snapshot(panel.latest())
    shared=dict(maturity=parse_tenor(q.maturity),notional=q.notional)
    if q.tool=='ppn':
        report=structured.principal_protected_note(curve,spot=q.spot,vol=q.vol,r_for_or_div=q.r_for,
            protection=q.protection,issue_price=q.issue,underlying=q.underlying,margin=q.margin,**shared)
    elif q.tool=='rc':
        report=structured.reverse_convertible(curve,spot=q.spot,vol=q.vol,r_for_or_div=q.r_for,
            strike_pct=q.strike_pct,coupon=q.coupon,issue_price=q.issue,margin=q.margin,underlying=q.underlying,**shared)
    elif q.tool=='dcd':
        report=structured.dual_currency_deposit(curve,spot=q.spot,vol=q.vol,r_for=q.r_for,strike=q.strike,
            base_ccy=q.base_ccy,quote_ccy=q.quote_ccy,margin=q.margin,**shared)
    else:
        report=structured.steepener_note(curve,leverage=q.leverage,floor=q.floor,cap=q.cap,
                                        freq=q.frequency,issue_price=q.issue,**shared)
    if q.futures_dv01 is not None:
        report=replace(report,hedge=structured.hedge_sheet(report,curve=curve,futures_dv01_per_contract=q.futures_dv01))
    return StructuringOutput(q,panel,curve,report,insights.narrate_structured(report))
