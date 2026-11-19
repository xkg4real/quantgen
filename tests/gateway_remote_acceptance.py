"""KEY-3 fake company server: switching a source from `personal` (this PC) to a company route through a fake
server gives the same answer (GATEWAY_DESIGN.md section 3). In-process only: no network, no real provider."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    import core.gateway as gw
    from core import credentials
    from core.gateway import codec, local, remote, routes
    from core.gateway.dispatch import dispatch
    from core.gateway.sources import SOURCES
    from data.fmp.quote_client import FMPQuote
    from data.krx.gateway import Answer


class FakeFMP:
    """Stands in for FMPQuoteClient; same method names, fixed data."""

    def quotes(self, symbols):
        return {s: self.quote(s) for s in symbols}

    def quote(self, symbol):
        return FMPQuote(symbol=symbol, name=f"{symbol} Inc", price=101.5, change=1.5, change_pct=1.5,
                        volume=1000.0, market_cap=None, high=102.0, low=99.0, open=100.0, previous_close=100.0,
                        exchange="NASDAQ", as_of="2026-11-19T00:00:00Z")

    def status(self):
        return {"ok": True, "note": "fake"}


class FakeDart:
    def filings(self, ticker, *, days=90, limit=50):
        return [{"rcept_no": "1", "ticker": ticker, "days": days, "limit": limit}]


class FakeServerTest(unittest.TestCase):
    def setUp(self):
        credentials.set_backend(None)
        gw.reload()
        gw.LOCAL.override("fmp", FakeFMP)
        gw.LOCAL.override("opendart", FakeDart)
        # The "company server": the same dispatch code over its own local route with the same fake clients.
        self.server_local = local.LocalRoute({sid: s.factory for sid, s in SOURCES.items()})
        self.server_local.override("fmp", FakeFMP)
        self.server_local.override("opendart", FakeDart)
        self.sent = []

        def transport(request):
            self.sent.append(request)
            wire = codec.decode(codec.encode(request))          # what a JSON round trip would carry
            return dispatch(wire, self.server_local)

        self.route = remote.RemoteRoute(transport)

    def tearDown(self):
        gw._remote_override = None
        gw._profile_override = None
        for sid in SOURCES:
            gw.LOCAL.override(sid, None)
        gw.reload()

    def _company(self, *sources):
        table = copy.deepcopy(gw._table())
        for sid in sources:
            table["profiles"]["commercial"][sid] = ["company"]
        gw._routes = routes.check_routes(table)
        gw._profile_override = "commercial"
        gw._remote_override = self.route

    def test_same_answer_personal_and_company(self):
        gw._profile_override = "personal"
        here_quotes = gw.client("fmp").quotes(["AAPL", "MSFT"])
        here_one = gw.client("fmp").quote("AAPL")
        here_filings = gw.client("opendart").filings("005930", days=30)
        self._company("fmp", "opendart")
        self.assertEqual(gw.route_of("fmp"), "company")
        there = gw.client("fmp")
        self.assertIsInstance(there, remote.RemoteProxy)
        self.assertEqual(there.quotes(["AAPL", "MSFT"]), here_quotes)
        self.assertEqual(there.quote("AAPL"), here_one)
        self.assertEqual(gw.client("opendart").filings("005930", days=30), here_filings)
        self.assertEqual(len(self.sent), 3)
        self.assertTrue(all(set(r) == {"source", "fn", "args", "kwargs", "client_version"} for r in self.sent))

    def test_proxy_exposes_only_allowed_functions(self):
        self._company("fmp")
        proxy = gw.client("fmp")
        with self.assertRaises(AttributeError):
            proxy.error_for
        with self.assertRaises(AttributeError):
            proxy._send

    def test_server_errors_do_not_echo_provider_messages(self):
        class Broken(FakeFMP):
            def quote(self, symbol):
                raise RuntimeError(f"provider said something about {symbol} and a key")

        self.server_local.override("fmp", Broken)
        self._company("fmp")
        with self.assertRaises(remote.RemoteFailed) as ctx:
            gw.client("fmp").quote("AAPL")
        self.assertEqual(str(ctx.exception), "RuntimeError")

    def test_codec_round_trip_and_refusal(self):
        answer = Answer(data=[1, 2], source="KIS", ok=True, reason="")
        self.assertEqual(codec.decode(codec.encode(answer)), answer)
        with self.assertRaises(codec.CodecError):
            codec.encode(object())
        with self.assertRaises(codec.CodecError):
            codec.decode({"__kind__": "os.system", "fields": {}})


if __name__ == "__main__":
    unittest.main()
