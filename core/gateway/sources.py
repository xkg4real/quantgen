"""The data sources the gateway knows (KEY-3; docs/commercial/GATEWAY_DESIGN.md section 4).

Each source names the keys it needs (core/credentials/names.py), the local client that serves it today, the
functions the company route may forward (an allowlist; empty means "not forwardable yet"), its delay class and
its display-rights policy (core/research/display_rights.json). No values live here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    id: str
    keys: tuple[str, ...]
    factory: str                     # "module:attribute" of the local client (a class, called with no arguments)
    functions: tuple[str, ...]       # forwardable through the company route (remote.py, dispatch.py). Each one's
                                     # return annotation must be a type the codec carries (tests.gateway_remote_acceptance)
    delay: str                       # "realtime" | "delayed" | "daily" | "on_demand"
    display_policy: str | None       # key in display_rights.json["policies"]; None = not market data
    fixed_local: bool = False        # D7-G rule 1: user brokerage/exchange keys never leave this PC
    stream: str | None = None        # "module:attribute" of a streaming client, if any


SOURCES: dict[str, Source] = {s.id: s for s in (
    Source("kis_quote", ("KIS_APP_KEY", "KIS_APP_SECRET"), "data.krx.kis_client:KISClient",
           ("quote", "daily", "index", "status"), "realtime", "kis_krx", fixed_local=True,
           stream="data.kis_stream:KISStream"),
    Source("kis_account", ("KIS_APP_KEY", "KIS_APP_SECRET"), "data.krx.kis_client:KISClient",
           (), "realtime", None, fixed_local=True),
    Source("upbit_account", ("UPBIT_ACCESS_KEY", "UPBIT_SECRET_KEY"), "data.crypto.crypto_client:UpbitAccount",
           (), "on_demand", None, fixed_local=True),
    Source("crypto_public", (), "core.gateway.local:CryptoPublic",
           ("upbit_ticker", "binance_premium_index", "binance_open_interest_hist", "coingecko_top"), "delayed",
           "Upbit"),
    # Series and CurvePanel results are not on the wire yet (codec.REGISTERED): nothing forwardable until they are.
    Source("fred", (), "core.gateway.local:FiccData", (), "daily", "fred_other"),
    Source("yahoo", (), "core.gateway.local:FiccData", (), "delayed", "yahoo"),
    Source("fmp", ("FMP_API_KEY",), "data.fmp.quote_client:FMPQuoteClient", ("quotes", "quote", "status"),
           "delayed", "fmp"),
    Source("krx_open_api", ("KRX_API_KEY",), "data.krx.krx_market_client:KRXMarketClient",
           ("all_quotes", "indices", "status"), "daily", "kis_krx"),
    Source("opendart", ("OPENDART_API_KEY",), "data.krx.opendart_client:OpenDARTClient",
           ("resolve", "filings", "financials", "status"), "on_demand", None),
    Source("anthropic", ("ANTHROPIC_API_KEY",), "core.gateway.local:AnthropicKey", (), "on_demand", None),
    Source("gs_marquee", ("GS_CLIENT_ID", "GS_CLIENT_SECRET"), "core.gateway.local:GsMarquee", (), "on_demand",
           None),
)}

ROUTES = ("local_key", "keyless", "company", "off")
STATES = ("key_needed", "login_needed", "plan_needed", "ready", "off")


def get(source: str) -> Source:
    try:
        return SOURCES[source]
    except KeyError:
        raise KeyError(f"unknown data source: {source}") from None
