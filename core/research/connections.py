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
            import config
            status_loaders = (config.quant_provider_status, config.krx_provider_status,
                              config.ficc_provider_status, config.crypto_provider_status)
        rows = {}
        for loader in status_loaders:
            for entry in loader():
                key = str(entry['id'])
                rows[key] = (safe_detail(entry.get('label', key)),
                    'CONFIGURED' if entry.get('ready') else 'NOT_CONFIGURED',
                    safe_detail(' · '.join(entry.get('vars', ()))), safe_detail(entry.get('note', '')))
        return ConnectionOutput(request, tuple(rows.values()))
    if probe_loaders is None:
        if request.tool == 'krx':
            from data.krx.krx_market_client import KRXMarketClient
            probe = KRXMarketClient().probe
        elif request.tool == 'ficc':
            from core.ficc.data import probe
        elif request.tool == 'kis':
            from data.kis_markets import KISMarkets
            probe = KISMarkets().probe
        else:
            from data.crypto.crypto_client import probe
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
