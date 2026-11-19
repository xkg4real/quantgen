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

    def test_bad_requests_and_answers(self):
        """Review items 9 and 10: malformed input never raises past dispatch or remote."""
        self.assertEqual(dispatch({"source": "fmp", "fn": "quote", "args": {"__kind__": "nope"}}, self.server_local),
                         {"ok": False, "error": "bad_request"})
        self.assertEqual(dispatch({"source": "fmp", "fn": "quote", "args": "AAPL"}, self.server_local),
                         {"ok": False, "error": "bad_request"})
        for answer in (None, "text", ["list"]):
            route = remote.RemoteRoute(lambda req, a=answer: a)
            with self.assertRaises(remote.RemoteFailed) as ctx:
                route.call("fmp", "quote", "AAPL")
            self.assertEqual(str(ctx.exception), "bad_answer")

    def test_every_forwardable_function_returns_an_encodable_type(self):
        """Review item 11 and KEY-4 item 8: each allowlisted function's return type is resolved (typing.get_type_hints)
        and walked down to its elements: list[X], dict[str, X], tuple, Optional/Union, and the fields of every
        dataclass it returns, which must be registered in the codec. A bare dict or list is JSON-shaped; the codec
        still refuses an unknown object inside one at encode time (the server answers result_not_encodable)."""
        import dataclasses
        import datetime as dt
        import importlib
        import types
        import typing

        registered = {codec._cls(spec) for spec in codec.REGISTERED.values()}
        leaves = {dict, list, tuple, str, int, float, bool, type(None), dt.date, dt.datetime}

        def check(tp, where, seen):
            origin = typing.get_origin(tp)
            if origin in (typing.Union, types.UnionType):
                for arg in typing.get_args(tp):
                    check(arg, where, seen)
                return
            if origin in (list, tuple, dict):
                args = [a for a in typing.get_args(tp) if a is not Ellipsis]
                if origin is dict and args:
                    self.assertIs(args[0], str, f"{where}: only string keys cross the wire")
                for arg in args[1:] if origin is dict else args:
                    check(arg, where, seen)
                return
            if tp is typing.Any:
                self.fail(f"{where}: Any is not a carried type")
            if dataclasses.is_dataclass(tp):
                self.assertIn(tp, registered, f"{where}: {tp.__name__} is not registered in the codec")
                if tp in seen:
                    return
                seen.add(tp)
                for name, field_tp in typing.get_type_hints(tp).items():
                    check(field_tp, f"{where} -> {tp.__name__}.{name}", seen)
                return
            self.assertIn(tp, leaves, f"{where}: {tp!r} is not carried")

        checked = 0
        for sid, src in SOURCES.items():
            if not src.functions:
                continue
            module, _, attr = src.factory.partition(":")
            cls = getattr(importlib.import_module(module), attr)
            for fn in src.functions:
                hints = typing.get_type_hints(getattr(cls, fn))
                self.assertIn("return", hints, f"{sid}.{fn} has no return annotation")
                check(hints["return"], f"{sid}.{fn}", set())
                checked += 1
        self.assertGreater(checked, 0)

    def test_remote_wraps_every_broken_answer(self):
        """KEY-4 item 7: a transport that raises, an `ok` that is not a bool, ok=true with a result the codec
        cannot read, and an error that is not a plain code all become RemoteFailed, with no provider text."""
        def raising(request):
            raise ConnectionError("host said something with a key in it")

        cases = {
            "transport_ConnectionError": raising,
            "bad_answer": lambda req: {"ok": "yes", "result": 1},
            "bad_answer ": lambda req: {"ok": 1, "result": 1},
            "bad_answer  ": lambda req: {"ok": True, "result": {"__kind__": "os.system", "fields": {}}},
            "bad_answer   ": lambda req: {"ok": True, "result": {"__kind__": "datetime", "value": "not a date"}},
            "bad_answer    ": lambda req: {"ok": False, "error": "provider said: key abc is wrong"},
            "no_answer": lambda req: {"ok": False},
            "bad_answer     ": lambda req: {"ok": False, "error": "sk_live_" + "a1b2c3d4e5f6a7b8c9d0e1f2a3"},
            "http_503": lambda req: {"ok": False, "error": "http_503"},
        }
        for expected, transport in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaises(remote.RemoteFailed) as ctx:
                    remote.RemoteRoute(transport).call("fmp", "quote", "AAPL")
                self.assertEqual(str(ctx.exception), expected.strip())
                self.assertIsNone(ctx.exception.__cause__)
                self.assertIsNone(ctx.exception.__context__)        # the original message is not carried along

    def test_dispatch_refuses_a_request_that_is_not_a_dict(self):
        """KEY-4 item 7: the server handler never raises on a malformed request."""
        for request in (None, "fmp", ["fmp", "quote"], 3, {"source": "fmp", "fn": ["quote"]}):
            with self.subTest(request=request):
                answer = dispatch(request, self.server_local)
                self.assertFalse(answer["ok"])
                self.assertIn(answer["error"], ("bad_request", "function_not_allowed"))

    def test_codec_round_trip_and_refusal(self):
        answer = Answer(data=[1, 2], source="KIS", ok=True, reason="")
        self.assertEqual(codec.decode(codec.encode(answer)), answer)
        with self.assertRaises(codec.CodecError):
            codec.encode(object())
        with self.assertRaises(codec.CodecError):
            codec.decode({"__kind__": "os.system", "fields": {}})


if __name__ == "__main__":
    unittest.main()
