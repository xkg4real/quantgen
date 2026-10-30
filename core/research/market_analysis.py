"""Validated native requests for the existing equity/crypto workflows.

No study store or account is opened implicitly. Callers may supply already-read
study cards; missing cards remain NOT_LOADED, never a successful study verdict.
"""
from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class DerivativesRequest:
    source: str = 'kis'
    expiry: str = ''
    rate_pct: float | None = None
    engine: str = 'gbm'
    n_paths: int = 3000
    horizon_days: int | None = None

    def validate(self):
        if self.source not in {'kis', 'synthetic'} or self.engine not in {'gbm', 'garch_t'}:
            raise ValueError('Unknown board source/engine')
        if self.expiry and not re.fullmatch(r'[0-9-]{6,10}', self.expiry):
            raise ValueError('Invalid expiry')
        if self.rate_pct is not None and not math.isfinite(self.rate_pct):
            raise ValueError('Invalid rate')
        if type(self.n_paths) is not int or not 100 <= self.n_paths <= 100000:
            raise ValueError('Invalid paths')
        if self.horizon_days is not None and (type(self.horizon_days) is not int or not 1 <= self.horizon_days <= 1260):
            raise ValueError('Invalid horizon')


@dataclass(frozen=True)
class ETFRequest:
    source: str = 'auto'
    code: str = '069500'
    days: int = 504

    def validate(self):
        if self.source not in {'auto', 'kis', 'fmp', 'yfinance', 'synthetic'}:
            raise ValueError('Unknown ETF source')
        if not re.fullmatch(r'[A-Za-z0-9.^=-]{1,40}', self.code.strip()):
            raise ValueError('Invalid ETF code')
        if type(self.days) is not int or not 30 <= self.days <= 10000:
            raise ValueError('Invalid history size')


@dataclass(frozen=True)
class CryptoRequest:
    source: str = 'live'
    days: int = 730
    include_balances: bool = False

    def validate(self):
        if self.source not in {'live', 'synthetic'} or type(self.include_balances) is not bool:
            raise ValueError('Unknown crypto request')
        if type(self.days) is not int or not 200 <= self.days <= 1500:
            raise ValueError('Crypto history must contain 200–1500 days')


@dataclass(frozen=True)
class MarketOutput:
    request: object
    data: dict
    narrative: str
    study_status: str = 'NOT_LOADED'


def execute_derivatives(request, *, snapshot_loader=None):
    request.validate()
    from dataclasses import asdict
    from .derivatives_workflow import snapshot, narrative
    data = (snapshot_loader or snapshot)(**asdict(request))
    return MarketOutput(request, data, narrative(data), 'NOT_APPLICABLE')


def execute_etf(request, *, analyze_fn=None, study_cards=None):
    request.validate()
    from .etf_workflow import analyze, narrative
    data = (analyze_fn or analyze)(request.code.strip().upper(), days=request.days, source=request.source,
                                  card_loader=lambda path: tuple(study_cards or ()))
    return MarketOutput(request, data, narrative(data), 'PROVIDED' if study_cards is not None else 'NOT_LOADED')


def execute_crypto(request, *, analyze_fn=None, study_cards=None):
    request.validate()
    from .crypto_workflow import analyze, narrative
    data = (analyze_fn or analyze)(days=request.days, source=request.source,
        include_balances=request.include_balances, card_loader=lambda path: tuple(study_cards or ()))
    return MarketOutput(request, data, narrative(data), 'PROVIDED' if study_cards is not None else 'NOT_LOADED')


@dataclass(frozen=True)
class KRXRequest:
    tool: str = 'quote'
    code: str = '005930'

    def validate(self):
        if self.tool not in {'quote', 'daily', 'filings', 'financials', 'snapshot', 'indices'}:
            raise ValueError('Unknown KRX dataset')
        if self.tool not in {'snapshot', 'indices'} and not re.fullmatch(r'\d{6}', self.code):
            raise ValueError('Six digit KRX code required')


@dataclass(frozen=True)
class KRXOutput:
    request: KRXRequest
    answer: object


def execute_krx(request, *, gateway=None):
    request.validate()
    if gateway is None:
        from data.krx import KRXGateway
        gateway = KRXGateway()
    if request.tool == 'snapshot':
        answer = gateway.market_snapshot()
    elif request.tool == 'indices':
        answer = gateway.indices()
    else:
        answer = getattr(gateway, request.tool)(request.code)
    return KRXOutput(request, answer)
