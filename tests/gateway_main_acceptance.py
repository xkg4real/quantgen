"""KEY-4 (PR #133 review 2, A1 and B1): the Flet app (main.py) starts whatever routes.json says, and reaches FMP,
the KRX Open API and OpenDART only through core/gateway.

- ``import main`` and ``main.main(page)`` work with a broken routes file, with krx_open_api or opendart off, and with
  them on the company route (as main 9f76b07 did in every case).
- KIS (fixed-local, rule 1) stays the real client in every case; a blocked KRX Open API / OpenDART sub-client is an
  OffClient that answers like an unconfigured client and never reaches the provider.
- main.QuoteFeed is the gateway subclass of the S4-frozen core/engine/feed.py QuoteFeed, and main() hands one to the
  engine.

Offline: no network (requests is refused), no key, no `.env`.
"""
from __future__ import annotations

import copy
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    import core.gateway as gw
    import core.skills.macro_daily as macro_daily
    import main
    from core.credentials import names
    from core.engine.feed import QuoteFeed as EngineQuoteFeed
    from core.gateway import remote, routes
    from core.rules.store import RuleStore
    from data.fmp.quote_client import FMPQuoteClient
    from data.krx import kis_client
    from tests.research_home_acceptance import Page


def _no_keys():
    return patch.dict(os.environ, {n: "" for n in list(names.SECRETS) + list(names.RESEARCH)})


class Base(unittest.TestCase):
    def setUp(self):
        gw.reload()

    def tearDown(self):
        gw._profile_override = None
        gw._remote_override = None
        gw.reload()
        importlib.reload(main)

    def _routes(self, **personal):
        table = copy.deepcopy(gw._table())
        for sid, order in personal.items():
            table["profiles"]["personal"][sid] = order
        gw._routes = routes.check_routes(table)

    def _start(self):
        """import main again and run main(page) with the engine and the stores kept offline; the gateway and the
        quote feed are main's own (not patched)."""
        with patch.object(dotenv, "load_dotenv", return_value=False):
            module = importlib.reload(main)
        built = {}

        def engine(store, feed, *a, **k):
            built["feed"] = feed
            return type("Engine", (), {"__getattr__": lambda self, name: (lambda *a, **k: None)})()

        real_krx = module.KRXGateway

        def krx():
            built["krx"] = real_krx()
            return built["krx"]

        with tempfile.TemporaryDirectory() as folder, _no_keys(), \
                patch.object(module, "RuleStore", return_value=RuleStore(Path(folder) / "rules.json")), \
                patch.object(module, "EngineRuntime", side_effect=engine), \
                patch.object(module, "KRXGateway", side_effect=krx), \
                patch.object(macro_daily, "on_app_start"), \
                patch("ui.strategy_lab_page.load_cards", return_value=[]), \
                patch("requests.sessions.Session.request", side_effect=AssertionError("network")):
            module.main(Page())
        return module, built


class StartsWhateverRoutesSay(Base):
    def _check(self, krx_off: bool, dart_off: bool):
        module, built = self._start()
        krx = built["krx"]
        self.assertIsInstance(krx.kis, kis_client.KISClient)                 # KIS: always the real client
        self.assertEqual(isinstance(krx.krx, gw.OffClient), krx_off)
        self.assertEqual(isinstance(krx.dart, gw.OffClient), dart_off)
        if krx_off:
            self.assertEqual(krx.market_snapshot().ok, False)               # answered without the provider
            self.assertEqual(krx.krx.all_quotes("ALL"), [])
            with self.assertRaises(gw.GatewayOff):
                krx.krx.daily_trade("x")
        if dart_off:
            self.assertFalse(krx.filings("005930").ok)
            self.assertIn("off" if "off" in krx.dart.reason else "company", krx.dart.reason)
        self.assertIsInstance(built["feed"], module.QuoteFeed)               # B1: the gateway feed reaches the engine
        return module, built

    def test_personal(self):
        self._check(False, False)

    def test_broken_routes_file(self):
        gw._routes, gw._route_error = None, "broken"
        self._check(True, True)

    def test_krx_open_api_off(self):
        self._routes(krx_open_api=["off"])
        self._check(True, False)

    def test_opendart_off(self):
        self._routes(opendart=["off"])
        self._check(False, True)

    def test_company_route(self):
        self._routes(krx_open_api=["company"], opendart=["company"])
        gw._remote_override = remote.RemoteRoute(lambda req: {"ok": True, "result": None})
        module, built = self._check(True, True)
        self.assertIn("company", built["krx"].krx.reason)


class GatewayQuoteFeed(Base):
    def test_is_the_gateway_subclass_of_the_frozen_feed(self):
        self.assertTrue(issubclass(main.QuoteFeed, EngineQuoteFeed))
        self.assertIsNot(main.QuoteFeed, EngineQuoteFeed)

    def test_fmp_client_comes_through_the_gateway(self):
        asked = []
        real = gw.provider

        def recording(module, source=None):
            asked.append(module)
            return real(module, source)

        with _no_keys(), patch.object(gw, "provider", side_effect=recording):
            feed = main.QuoteFeed(None)
            self.assertIsInstance(feed.fmp, FMPQuoteClient)
        self.assertEqual(asked, ["data.fmp"])

    def test_fmp_blocked_gives_no_client_and_says_why(self):
        gw._profile_override = "commercial"                              # fmp off in the commercial draft
        with _no_keys():
            feed = main.QuoteFeed(None)
            self.assertIsNone(feed.fmp)
        self.assertIn("fmp is off", feed.fmp_blocked)


if __name__ == "__main__":
    unittest.main()
