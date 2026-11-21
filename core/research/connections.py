"""Read-only provider presence and explicit probes, without credential values."""
from dataclasses import dataclass
from .presentation import safe_detail


@dataclass(frozen=True)
class ConnectionRequest:
    tool: str = 'presence'

    def validate(self):
        if self.tool not in {'presence', 'krx', 'ficc', 'kis', 'crypto'}:
            raise ValueError('Unknown connection check')


@dataclass(frozen=True)
class ConnectionOutput:
    request: ConnectionRequest
    rows: tuple


def execute_connections(request, *, status_loaders=None, probe_loaders=None):
    request.validate()
    if request.tool == 'presence':
        if status_loaders is None:
            from core import gateway
            status_loaders = gateway.status_loaders()   # config's quant, KRX, FICC, crypto rows
        rows = {}
        for loader in status_loaders:
            for entry in loader():
                key = str(entry['id'])
                rows[key] = (safe_detail(entry.get('label', key)),
                    'CONFIGURED' if entry.get('ready') else 'NOT_CONFIGURED',
                    safe_detail(' · '.join(entry.get('vars', ()))), safe_detail(entry.get('note', '')))
        return ConnectionOutput(request, tuple(rows.values()))
    if probe_loaders is None:
        from core import gateway
        if request.tool == 'krx':
            probe = gateway.provider('data.krx.krx_market_client').KRXMarketClient().probe
        elif request.tool == 'ficc':
            probe = gateway.ficc().probe
        elif request.tool == 'kis':
            probe = gateway.provider('data.kis_markets').KISMarkets().probe
        else:
            probe = gateway.provider('data.crypto.crypto_client').probe
    else:
        probe = probe_loaders[request.tool]
    try:
        result = probe()
    except Exception as exc:
        return ConnectionOutput(request, ((request.tool, 'UNAVAILABLE', type(exc).__name__, ''),))
    if request.tool == 'krx':
        rows = [('KRX', 'REACHABLE' if result.get('ready') else 'UNAVAILABLE',
                 safe_detail(result.get('path', '')), safe_detail(result.get('reason', '')))]
    else:
        rows = [(safe_detail(k), 'REACHABLE' if v.get('ok') else 'UNAVAILABLE', '',
                 safe_detail(v.get('detail', ''))) for k, v in result.items()]
    return ConnectionOutput(request, tuple(rows))
