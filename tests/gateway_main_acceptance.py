"""KEY-4 (PR #133 review 2, A1 and B1): the Flet app (main.py) starts whatever routes.json says, and reaches FMP,
the KRX Open API and OpenDART only through core/gateway.

- ``import main`` and ``main.main(page)`` work with a broken routes file, with krx_open_api or opendart off, and with
  them on the company route (as main 9f76b07 did in every case).
- KIS (fixed-local, rule 1) stays the real client in every case; a blocked KRX Open API / OpenDART sub-client is an
  OffClient that answers like an unconfigured client and never reaches the provider.
- main.QuoteFeed is the gateway subclass of the S4-frozen core/engine/feed.py QuoteFeed, and main() hands one to the
  engine.
- Review 3 A1: every requests call is recorded (method, url) and refused. With dummy KRX_API_KEY / OPENDART_API_KEY set,
  quote, market_snapshot, indices, filings and financials are called on the gateway main() built: a blocked KRX Open API
  leaves no request to the KRX hosts (config.KRX_BASE_URL, KRX_OTP_URL, KRX_DOWNLOAD_URL), a blocked OpenDART none to
  config.OPENDART_BASE_URL, and on the personal route both hosts are asked (so the watch itself is shown to work; the
  provider clients turn a refused request into an empty answer, which is why the answers alone cannot tell).

- KEY-5/a (PR #133 review 3 C): the engine feed main() builds holds the very KRXGateway main() built (F7); a blocked
  KRX Open API / OpenDART answer says why (the OffClient's reason, "served by the company route" for company) instead of
  "Set KRX_API_KEY" / "need OPENDART_API_KEY" (A1R3-1); after a route reload or a key change that gateway gets fresh
  sub-clients and the blocks again, in place (A1R3-5); a blocked FMP shows its reason in the feed's status row and in
  the engine's per-symbol error, and the feed looks again once FMP is back (A1R3-4).

Offline: no network (requests is refused and recorded), no real key (dummy values only), no `.env`, no ~/.nextgen
(the OpenDART corp-code cache is pointed into a temporary folder).
"""
from __future__ import annotations

import copy
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    import config
    import core.gateway as gw
    import core.skills.macro_daily as macro_daily
    from core import markets
    import main
    from core.credentials import names
    from core.engine.feed import QuoteFeed as EngineQuoteFeed
    from core.gateway import remote, routes
    from core.rules.store import RuleStore
    from data.fmp.quote_client import FMPQuoteClient
    from data.krx import kis_client, opendart_client
    from tests.research_home_acceptance import Page


def _no_keys():
    return patch.dict(os.environ, {n: "" for n in list(names.SECRETS) + list(names.RESEARCH)})


DUMMY_KEYS = {"KRX_API_KEY": "dummy-krx-test-value", "OPENDART_API_KEY": "dummy-dart-test-value"}


def _host(url) -> str:
    return (urlsplit(str(url)).hostname or "").lower()


KRX_HOSTS = {_host(config.KRX_BASE_URL), _host(config.KRX_OTP_URL), _host(config.KRX_DOWNLOAD_URL)}
DART_HOSTS = {_host(config.OPENDART_BASE_URL)}


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

    def _start(self, probe=None):
        """import main again and run main(page) with the engine and the stores kept offline; the gateway and the
        quote feed are main's own (not patched). Every requests call is recorded in built["asked"] as (method, url)
        and refused; `probe(module, built)` runs inside the same patches (dummy keys set)."""
        with patch.object(dotenv, "load_dotenv", return_value=False):
            module = importlib.reload(main)
        built = {"asked": []}

        def network(*a, **k):
            method = k.get("method", a[0] if a else "")
            url = k.get("url", a[1] if len(a) > 1 else "")
            built["asked"].append((str(method).upper(), str(url)))
            raise AssertionError("network")

        def engine(store, feed, *a, **k):
            built["feed"] = feed
            return type("Engine", (), {"__getattr__": lambda self, name: (lambda *a, **k: None)})()

        real_krx = module.KRXGateway

        def krx():
            built["krx"] = real_krx()
            built.setdefault("every_krx", []).append(built["krx"])
            return built["krx"]

        with tempfile.TemporaryDirectory() as folder, _no_keys(), patch.dict(os.environ, DUMMY_KEYS), \
                patch.object(opendart_client, "_CACHE_PATH", Path(folder) / "dart_corp_codes.json"), \
                patch.object(module, "RuleStore", return_value=RuleStore(Path(folder) / "rules.json")), \
                patch.object(module, "EngineRuntime", side_effect=engine), \
                patch.object(module, "KRXGateway", side_effect=krx), \
                patch.object(macro_daily, "on_app_start"), \
                patch("ui.strategy_lab_page.load_cards", return_value=[]), \
                patch("requests.sessions.Session.request", side_effect=network):
            module.main(Page())
            built["started"] = len(built["asked"])
            if probe is not None:
                probe(module, built)
        return module, built


class StartsWhateverRoutesSay(Base):
    def _check(self, krx_off: bool, dart_off: bool):
        def probe(module, built):
            gateway = built["krx"]
            built["answers"] = {"quote": gateway.quote("005930"), "snapshot": gateway.market_snapshot("ALL"),
                                "indices": gateway.indices(), "filings": gateway.filings("005930"),
                                "financials": gateway.financials("005930")}

        module, built = self._start(probe)
        hosts = {_host(url) for _method, url in built["asked"]}
        if krx_off:
            self.assertFalse(hosts & KRX_HOSTS, built["asked"])               # A1: no request to a blocked KRX
        else:
            self.assertTrue(hosts & KRX_HOSTS, built["asked"])                # the watch works (positive control)
        if dart_off:
            self.assertFalse(hosts & DART_HOSTS, built["asked"])
        else:
            self.assertTrue(hosts & DART_HOSTS, built["asked"])
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
        self.assertEqual(len(built["every_krx"]), 1)                         # F7: main() builds one gateway and the
        self.assertIs(built["feed"].krx, krx)                                # engine feed holds that very one
        self._check_reasons(krx, built["answers"], krx_off, dart_off)
        return module, built

    def _check_reasons(self, krx, answers: dict, krx_off: bool, dart_off: bool):
        """A1R3-1: the answers (taken inside the network watch) say the source is blocked, not that a key is
        missing; with nothing blocked they are the provider clients' own answers, as before."""
        for answer in answers.values():
            self.assertFalse(answer.ok)                                      # no network: nothing answers
        if krx_off:
            self.assertEqual(answers["snapshot"].reason, krx.krx.reason)
            self.assertNotIn("KRX_API_KEY", answers["snapshot"].reason)
            self.assertIn(krx.krx.reason, answers["indices"].reason)
            self.assertIn(krx.krx.reason, answers["quote"].reason)
        else:
            self.assertIn("KRX_API_KEY", answers["snapshot"].reason)         # unchanged when nothing is blocked
            self.assertEqual(answers["indices"].reason, "no index provider responded")
        for name in ("filings", "financials"):
            if dart_off:
                self.assertEqual(answers[name].reason, krx.dart.reason)
                self.assertNotIn("OPENDART_API_KEY", answers[name].reason)
            else:
                self.assertNotIn("profile", answers[name].reason)

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
        self.assertIn("served by the company route", built["krx"].krx.reason)
        self.assertIn("served by the company route", built["krx"].dart.reason)
        self.assertEqual(built["krx"].market_snapshot().reason, built["krx"].krx.reason)


class RouteOrKeyChange(Base):
    """A1R3-5: main() builds the KRXGateway once; a route reload or a key change sets it up again, in place, so the
    KRX screen and the engine feed (which hold that one object) follow."""

    def _table(self, **personal):
        table = copy.deepcopy(gw._table())
        for sid, order in personal.items():
            table["profiles"]["personal"][sid] = order
        return routes.check_routes(table)

    def test_reload_applies_a_new_route_to_the_gateway_main_built(self):
        module, built = self._start()
        krx, feed = built["krx"], built["feed"]
        self.assertNotIsInstance(krx.krx, gw.OffClient)
        with patch.object(gw, "load_routes", return_value=self._table(krx_open_api=["off"], opendart=["off"])):
            gw.reload()
            self.assertIsInstance(krx.krx, gw.OffClient)
            self.assertIsInstance(krx.dart, gw.OffClient)
            self.assertIs(feed.krx, krx)
            with _no_keys():
                self.assertEqual(krx.market_snapshot().reason, krx.krx.reason)
        gw.reload()                                                          # routes.json again: back on
        self.assertNotIsInstance(krx.krx, gw.OffClient)
        self.assertNotIsInstance(krx.dart, gw.OffClient)
        self.assertIsInstance(krx.kis, kis_client.KISClient)

    def test_key_change_gives_fresh_sub_clients(self):
        module, built = self._start()
        krx = built["krx"]
        before = (krx.kis, krx.krx, krx.dart)
        gw._on_key_change("KRX_API_KEY")
        self.assertTrue(all(a is not b for a, b in zip(before, (krx.kis, krx.krx, krx.dart))))
        unrelated = (krx.kis, krx.krx, krx.dart)
        gw._on_key_change("FMP_API_KEY")                                     # not one of its sources: left alone
        self.assertTrue(all(a is b for a, b in zip(unrelated, (krx.kis, krx.krx, krx.dart))))


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

    def test_the_blocked_reason_reaches_status_and_engine(self):
        """A1R3-4: fmp_blocked is what the feed reports, and the feed looks again once FMP is back."""
        market = next(code for code in ("NASDAQ", "NYSE", "US", "AMEX")
                      if markets.provider_for(code) == markets.FMP)
        gw._profile_override = "commercial"
        with _no_keys():
            feed = main.QuoteFeed(None)
            row = next(r for r in feed.provider_status() if r.get("provider") == "FMP")
            self.assertFalse(row["ready"])
            self.assertEqual(row["reason"], feed.fmp_blocked)
            self.assertIsNone(feed.fetch("AAPL", market))
            self.assertEqual(feed.last_error("AAPL"), feed.fmp_blocked)
            self.assertTrue(feed.is_permanent("AAPL"))
            gw._profile_override = None
            gw.reload()                                                      # route back: look again
            self.assertIsInstance(feed.fmp, FMPQuoteClient)
            self.assertEqual(feed.fmp_blocked, "")


if __name__ == "__main__":
    unittest.main()
