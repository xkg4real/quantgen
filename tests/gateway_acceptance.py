"""KEY-3 gateway: routes, the six D7-G rules and the status rows (GATEWAY_DESIGN.md sections 2-3).

Offline. Never reads `.env` or `~/.nextgen`: `dotenv.load_dotenv` is patched before import, and keys come only from
a patched environment or an in-memory keyring backend. All values are fake."""
from __future__ import annotations

import copy
import json
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    import core.gateway as gw
    from core import credentials
    from core.credentials import names
    from core.gateway import local, remote, routes
    from core.gateway.sources import SOURCES

ROOT = Path(__file__).resolve().parents[1]
FAKE = "fake-value-for-gateway-test-1"


class MemoryBackend:
    priority = 1

    def __init__(self):
        self.store = {}

    def get_password(self, service, user):
        return self.store.get((service, user))

    def set_password(self, service, user, password):
        self.store[(service, user)] = password

    def delete_password(self, service, user):
        del self.store[(service, user)]


def _no_keys():
    return patch.dict(os.environ, {n: "" for n in list(names.SECRETS) + list(names.RESEARCH)})


def _valid():
    return json.loads(routes.ROUTES_FILE.read_text(encoding="utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        credentials.set_backend(MemoryBackend())
        credentials.record_dotenv(set())
        gw.reload()

    def tearDown(self):
        gw._profile_override = None
        gw._remote_override = None
        for sid in SOURCES:
            gw.LOCAL.override(sid, None)
        credentials.set_backend(None)
        gw.reload()


class RoutesFileTest(unittest.TestCase):
    def test_shipped_file_is_valid_and_covers_every_source(self):
        data = routes.load_routes()
        for profile in routes.PROFILES:
            self.assertEqual(set(data["profiles"][profile]), set(SOURCES))

    def test_rule1_fixed_local_cannot_move(self):
        for sid in ("kis_quote", "kis_account", "upbit_account"):
            bad = _valid()
            bad["profiles"]["commercial"][sid] = ["company"]
            with self.assertRaises(routes.RouteError):
                routes.check_routes(bad)

    def test_rule2_key_shaped_text_refused(self):
        raw = routes.ROUTES_FILE.read_text(encoding="utf-8").replace('"schema": 1',
                                                                      '"note": "abcdefghijklmnopqrstuvwxyz0123456789", "schema": 1')
        with self.assertRaises(routes.RouteError):
            routes.check_routes(json.loads(raw), raw)

    def test_unknown_or_missing_sources_and_routes_refused(self):
        bad = _valid()
        bad["profiles"]["personal"]["new_vendor"] = ["local_key"]
        with self.assertRaises(routes.RouteError):
            routes.check_routes(bad)
        bad = _valid()
        del bad["profiles"]["personal"]["fmp"]
        with self.assertRaises(routes.RouteError):
            routes.check_routes(bad)
        bad = _valid()
        bad["profiles"]["personal"]["fmp"] = ["teleport"]
        with self.assertRaises(routes.RouteError):
            routes.check_routes(bad)
        bad = _valid()
        bad["profiles"]["personal"]["fred"] = ["local_key"]          # keyless source cannot use a key route
        with self.assertRaises(routes.RouteError):
            routes.check_routes(bad)

    def test_no_company_key_or_address_in_gateway_sources(self):
        """Rule 2: nothing key-shaped and no server address under core/gateway."""
        for path in (ROOT / "core" / "gateway").glob("*"):
            if path.suffix not in (".py", ".json"):
                continue
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{8,}", text), path.name)
            self.assertNotIn("quantgeneration.com", text, path.name)


class RuleTest(Base):
    def test_rule1_remote_refuses_fixed_local_before_sending(self):
        sent = []
        route = remote.RemoteRoute(lambda req: sent.append(req) or {"ok": True, "result": None})
        for sid in ("kis_quote", "kis_account", "upbit_account"):
            with self.assertRaises(remote.RemoteRefused):
                route.call(sid, "quote", "005930")
        self.assertEqual(sent, [])

    def test_rule1_dispatch_refuses_fixed_local(self):
        from core.gateway.dispatch import dispatch
        self.assertEqual(dispatch({"source": "kis_quote", "fn": "quote", "args": ["005930"]}, gw.LOCAL)["error"],
                         "fixed_local")
        self.assertEqual(dispatch({"source": "fmp", "fn": "__init__"}, gw.LOCAL)["error"], "function_not_allowed")

    def test_rule3_gateway_never_reads_dotenv_itself(self):
        for path in (ROOT / "core" / "gateway").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("load_dotenv", text, path.name)
            self.assertNotIn("dotenv_values", text, path.name)
            self.assertNotIn("os.environ", text, path.name)
            self.assertNotIn("getenv", text, path.name)

    def test_rule4_answer_carries_source_route_delay_right(self):
        a = gw.answer("yahoo", [1, 2])
        self.assertEqual((a.source, a.route, a.delay), ("yahoo", "keyless", "delayed"))
        self.assertEqual(a.display_right, "rights_replace")
        self.assertTrue(a)
        self.assertEqual(gw.answer("opendart", None, ok=False, reason="no key").display_right, "not_market_data")

    def test_rule5_status_rows_have_no_values(self):
        with _no_keys():
            credentials.set("FMP_API_KEY", FAKE)
            rows = gw.status()
        self.assertEqual({r["source"] for r in rows}, set(SOURCES))
        for row in rows:
            self.assertEqual(set(row), {"source", "label_key", "route", "state", "needs", "key_sources", "delay",
                                        "display_right", "error"})
            self.assertTrue(row["label_key"].startswith("gateway.source."))
        self.assertNotIn(FAKE, repr(rows))
        fmp = next(r for r in rows if r["source"] == "fmp")
        self.assertEqual((fmp["state"], fmp["needs"], fmp["key_sources"]), ("ready", [], {"FMP_API_KEY": "keyring"}))

    def test_rule6_key_change_rebuilds_without_restart(self):
        with _no_keys():
            self.assertEqual(gw.ready("kis_quote"), "key_needed")
            first = gw.client("kis_quote")
            self.assertFalse(first.ready)
            credentials.set("KIS_APP_KEY", FAKE)
            credentials.set("KIS_APP_SECRET", FAKE + "2")
            self.assertEqual(gw.ready("kis_quote"), "ready")
            second = gw.client("kis_quote")
            self.assertIsNot(first, second)
            self.assertEqual(second.ready, gw.LOCAL.client("kis_quote").ready)
            from data.krx import kis_client
            self.assertEqual(second.ready, kis_client.requests is not None)


class ProfileTest(Base):
    def test_commercial_draft_turns_yahoo_and_fmp_off(self):
        gw._profile_override = "commercial"
        self.assertEqual(gw.ready("yahoo"), "off")
        with self.assertRaises(gw.GatewayOff):
            gw.client("fmp")
        self.assertEqual(gw.route_of("kis_quote"), "local_key")

    def test_company_route_closed_until_server_configured(self):
        table = copy.deepcopy(gw._table())
        table["profiles"]["personal"]["fmp"] = ["company", "local_key"]
        gw._routes = routes.check_routes(table)
        self.assertEqual(gw.route_of("fmp"), "local_key")          # no company server: falls through
        gw._remote_override = remote.RemoteRoute(lambda req: {"ok": True, "result": None})
        self.assertEqual(gw.route_of("fmp"), "company")
        self.assertIsInstance(gw.client("fmp"), remote.RemoteProxy)

    def test_broken_routes_file_turns_everything_off(self):
        gw._routes, gw._route_error = None, "broken"
        self.assertTrue(all(r["state"] == "off" for r in gw.status()))


class LocalTest(Base):
    def test_local_clients_are_cached_and_overridable(self):
        gw.LOCAL.override("crypto_public", lambda: "fake-crypto")
        self.assertEqual(gw.client("crypto_public"), "fake-crypto")
        self.assertIs(gw.client("crypto_public"), gw.client("crypto_public"))

    def test_ficc_exposes_only_listed_loaders(self):
        ficc = local.FiccData()
        self.assertTrue(callable(ficc.load_series))
        with self.assertRaises(AttributeError):
            ficc.synthetic_series


if __name__ == "__main__":
    unittest.main()
