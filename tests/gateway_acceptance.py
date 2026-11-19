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


class KeyChangeTest(Base):
    def test_old_client_is_told_and_next_one_is_fresh(self):
        """Review item 8: a caller holding the old client sees the change; client() builds a new one."""
        calls = []

        class Holder:
            def reload_credentials(self):
                calls.append("reloaded")

        gw.LOCAL.override("fmp", Holder)
        old = gw.client("fmp")
        with _no_keys():
            credentials.set("FMP_API_KEY", FAKE)
        self.assertEqual(calls, ["reloaded"])
        self.assertIsNot(gw.client("fmp"), old)

    def test_every_held_client_is_told_on_every_change(self):
        """KEY-4 item 6: two keys set one after the other; a caller holding the first client still sees both
        changes, and so does a caller holding the second one."""
        seen = []

        class Holder:
            def __init__(self):
                self.n = len(seen)
                seen.append([])

            def reload_credentials(self):
                seen[self.n].append("reloaded")

        gw.LOCAL.override("kis_quote", Holder)
        first = gw.client("kis_quote")
        with _no_keys():
            credentials.set("KIS_APP_KEY", FAKE)
            second = gw.client("kis_quote")
            credentials.set("KIS_APP_SECRET", FAKE + "2")
        self.assertIsNot(first, second)
        self.assertEqual(seen, [["reloaded", "reloaded"], ["reloaded"]])
        del first, second
        import gc
        gc.collect()
        self.assertEqual(gw.LOCAL.held("kis_quote"), [])            # dropped holders are not kept alive

    def test_a_failing_reload_does_not_break_saving_a_key(self):
        class Broken:
            def reload_credentials(self):
                raise RuntimeError("cannot")

        gw.LOCAL.override("fmp", Broken)
        held = gw.client("fmp")
        with _no_keys():
            credentials.set("FMP_API_KEY", FAKE)
            self.assertEqual(gw.ready("fmp"), "ready")
        self.assertIsNotNone(held)


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
        """A broken routes.json turns every source off, except the fixed-local ones (rule 1): they are local_key in
        every valid profile, so KIS and the Upbit account keep working and report their key state, as the core paths
        that reach them do (PR #133 review C6)."""
        gw._routes, gw._route_error = None, "broken"
        with _no_keys():
            rows = {r["source"]: r for r in gw.status()}
        fixed = {sid for sid, s in SOURCES.items() if s.fixed_local}
        self.assertEqual(fixed, {"kis_quote", "kis_account", "upbit_account"})
        self.assertTrue(all(r["state"] == "off" for sid, r in rows.items() if sid not in fixed))
        self.assertTrue(all(r["route"] == "local_key" and r["state"] == "key_needed"
                            for sid, r in rows.items() if sid in fixed))


class LocalTest(Base):
    def test_local_clients_are_cached_and_overridable(self):
        gw.LOCAL.override("crypto_public", lambda: "fake-crypto")
        self.assertEqual(gw.client("crypto_public"), "fake-crypto")
        self.assertIs(gw.client("crypto_public"), gw.client("crypto_public"))

    def test_ficc_constants_and_loaders_do_not_overlap(self):
        """C2: a name is either a checked loader (EXPOSED) or a pure value (CONSTANTS), never both: a CONSTANTS name
        is handed out without any route check."""
        self.assertEqual(set(local.FiccData.CONSTANTS) & set(local.FiccData.EXPOSED), set())

    def test_ficc_constants_at_run_time_are_the_pinned_eight(self):
        """Review 3 F4: the boundary test reads CONSTANTS from local.py's source (the first assignment); a second
        assignment in the class body (CONSTANTS += ("_provider_rows",)) would hand out a fetcher unchecked while
        that reading stays the same. The value the app runs with is pinned here."""
        self.assertEqual(set(local.FiccData.CONSTANTS),
                         {"G10_KRW", "Series", "CurvePanel", "CurveSnapshot", "_period_for", "synthetic_series",
                          "synthetic_curve_panel", "synthetic_fx"})
        self.assertEqual(len(local.FiccData.CONSTANTS), 8)

    def test_ficc_exposes_only_listed_loaders(self):
        ficc = local.FiccData()
        self.assertTrue(callable(ficc.load_series))
        self.assertTrue(callable(ficc.synthetic_series))             # a pure helper (KEY-4 CONSTANTS)
        for hidden in ("_fetch", "_cache_put", "_route", "_yf"):
            with self.assertRaises(AttributeError):
                getattr(ficc, hidden)


class CoreAccessTest(Base):
    """KEY-4: the ways core/ reaches providers through the gateway, and what an "off" route does to them."""

    def _rows(self, provider, ids, days, **kwargs):
        self.asked.append((provider, tuple(ids)))
        return {i: [(f"2026-01-{n + 1:02d}", 1.0 + n) for n in range(28)] for i in ids}, {}

    def setUp(self):
        super().setUp()
        self.asked = []
        from core.ficc import data
        self.data = data

    def test_yahoo_off_stops_yahoo_tickers_only(self):
        """Review item 1 and PR #133 review B5: with the commercial draft (yahoo off, fred keyless) a Yahoo ticker is
        never asked for. Under source="auto" it comes back SYNTHETIC with the reason (as a provider failure does) while
        the FRED ids of the same batch are still read; an explicit Yahoo request and the Yahoo-only calls raise."""
        gw._profile_override = "commercial"
        with patch.object(self.data, "_provider_rows", self._rows):
            sheet = gw.ficc().load_many(iter(["DGS10", "ZN=F", "DGS2", "GC=F"]), days=28)   # C4: an iterator
            self.assertEqual(list(sheet), ["DGS10", "ZN=F", "DGS2", "GC=F"])
            self.assertEqual({k: v.source for k, v in sheet.items()},
                             {"DGS10": "FRED", "DGS2": "FRED", "ZN=F": "SYNTHETIC", "GC=F": "SYNTHETIC"})
            self.assertIn("yahoo is off in profile commercial", sheet["ZN=F"].note)
            self.assertEqual(sheet["DGS10"].values, tuple(1.0 + n for n in range(28)))
            one = gw.ficc().load_series("^GSPC", days=60, label="S&P")
            self.assertEqual((one.source, one.label), ("SYNTHETIC", "S&P"))
            for call in (lambda: gw.ficc().load_series("^GSPC", source="yfinance", days=28),
                         lambda: gw.ficc().load_many(["DGS10", "KRW=X"], source="yfinance", days=28),
                         lambda: gw.ficc().load_fx_spot("USDKRW", days=28),
                         lambda: gw.ficc()._yf_fetch(["SPY"], "1y"),
                         lambda: gw.ficc().yfinance):
                with self.assertRaises(gw.GatewayOff):
                    call()
            self.assertEqual(gw.ficc().load_series("^GSPC", source="synthetic", days=60).source, "SYNTHETIC")
        self.assertEqual(self.asked, [("FRED", ("DGS10", "DGS2"))])

    def test_probe_does_not_call_a_blocked_provider(self):
        """PR #133 review B6: the connection check reports a blocked provider instead of calling it."""
        gw._profile_override = "commercial"
        calls = []
        with patch.object(self.data, "_yf_fetch", lambda *a: calls.append("yahoo") or {}), \
                patch.object(self.data, "_fred_fetch", lambda *a: calls.append("fred") or {"DGS10": [("2026-01-02", 4.0)]}), \
                patch.object(self.data, "fred_ready", lambda: True), patch.object(self.data, "yfinance_ready", lambda: True):
            result = gw.ficc().probe()
        self.assertEqual(calls, ["fred"])
        self.assertEqual(result["yfinance"], {"ok": False, "detail": "off in profile commercial"})
        self.assertTrue(result["fred"]["ok"])

    def test_company_route_refuses_the_local_entry_points(self):
        """PR #133 review B7: a source moved to the company route is served only through client(); core's local
        entry points refuse it rather than use the user's own key while the screens say "company"."""
        table = copy.deepcopy(gw._table())
        for sid in ("fmp", "yahoo"):
            table["profiles"]["personal"][sid] = ["company"]
        gw._routes = routes.check_routes(table)
        gw._remote_override = remote.RemoteRoute(lambda req: {"ok": True, "result": None})
        self.assertEqual(gw.route_of("fmp"), "company")
        with self.assertRaises(gw.GatewayOff):
            gw.provider("data.fmp.quote_client")
        with self.assertRaises(gw.GatewayOff):
            gw.ficc()._yf_fetch(["SPY"], "1y")
        with _no_keys():
            credentials.set("FMP_API_KEY", FAKE)
            self.assertEqual(gw.local_key("fmp"), "")
            self.assertFalse(gw.keys_ready("fmp"))
        self.assertIsInstance(gw.client("fmp"), remote.RemoteProxy)

    def test_history_cache_does_not_answer_for_a_blocked_source(self):
        """PR #133 review B8: a Yahoo or crypto series cached on disk is not served while the source is blocked."""
        from core.quant import history
        self.assertTrue(history._READY["YFINANCE"]() and history._READY["CRYPTO"]())
        gw._profile_override = "commercial"
        self.assertFalse(history._READY["YFINANCE"]())
        import config
        with patch.object(config, "FICC_CACHE_TTL_SECONDS", 3600), \
                patch.object(history, "yf_history", side_effect=history.HistoryError("asked")) as fetch, \
                patch("pathlib.Path.read_text", side_effect=AssertionError("cache file read")):
            with self.assertRaises(history.HistoryError):
                history.load_history("SPY", source="yfinance", days=60)
        fetch.assert_called_once()

    def test_modules_with_several_sources(self):
        """PR #133 review B9: data.krx reaches the KRX Open API and OpenDART too; the crypto module serves the fixed-
        local Upbit account and the public prices, and a caller names the one it uses."""
        table = copy.deepcopy(gw._table())
        table["profiles"]["personal"]["opendart"] = ["off"]
        table["profiles"]["personal"]["crypto_public"] = ["off"]
        gw._routes = routes.check_routes(table)
        with self.assertRaises(gw.GatewayOff):
            gw.provider("data.krx")
        with self.assertRaises(gw.GatewayOff):
            gw.provider("data.crypto.crypto_client")
        self.assertEqual(gw.provider("data.crypto.crypto_client", source="upbit_account").__name__,
                         "data.crypto.crypto_client")
        with self.assertRaises(KeyError):
            gw.provider("data.fmp", source="kis_quote")

    def test_personal_profile_serves_both(self):
        with patch.object(self.data, "_provider_rows", self._rows):
            self.assertEqual(gw.ficc().load_series("^GSPC", days=28).source, "YFINANCE")
            self.assertEqual(gw.ficc().load_series("DGS10", days=28).source, "FRED")

    def test_ficc_calls_see_a_patch_of_the_provider_module(self):
        """Looked up at call time, as the inside-function imports it replaces were."""
        with patch.object(self.data, "load_short_rate", return_value="patched"):
            self.assertEqual(gw.ficc().load_short_rate("USD"), "patched")

    def test_provider_modules_and_off_routes(self):
        import data.kis_markets as km
        self.assertIs(gw.provider("data.kis_markets"), km)
        with self.assertRaises(KeyError):
            gw.provider("os")
        gw._profile_override = "commercial"                          # fmp and gs_marquee off in the draft
        with self.assertRaises(gw.GatewayOff):
            gw.provider("data.fmp.quote_client")
        with self.assertRaises(gw.GatewayOff):
            gw.provider("gs_quant.session")
        with _no_keys():
            credentials.set("FMP_API_KEY", FAKE)
            self.assertFalse(gw.keys_ready("fmp"))
            self.assertEqual(gw.local_key("fmp"), "")
            gw._profile_override = "personal"
            self.assertTrue(gw.keys_ready("fmp"))
            self.assertEqual(gw.local_key("fmp"), FAKE)

    def test_fixed_local_sources_never_read_routes(self):
        """KIS and the Upbit account are local_key in every valid profile (rule 1): reaching them opens no file,
        so the in-memory KIS master download stays file-free."""
        gw.reload()
        with patch("builtins.open", side_effect=AssertionError("no file")), \
                patch("pathlib.Path.read_text", side_effect=AssertionError("no file")):
            self.assertEqual(gw.provider("data.kis_markets").__name__, "data.kis_markets")
            with _no_keys():
                self.assertFalse(gw.keys_ready("kis_quote"))
                self.assertFalse(gw.keys_ready("upbit_account"))

    def test_config_functions_are_read_at_call_time(self):
        import config
        with patch.object(config, "anthropic_key", return_value="patched-fixture"):
            self.assertEqual(gw.local_key("anthropic"), "patched-fixture")
            with gw.suspend_key("anthropic"):
                self.assertEqual(gw.local_key("anthropic"), "")
                self.assertEqual(config.anthropic_key(), "")
            self.assertEqual(gw.local_key("anthropic"), "patched-fixture")
        self.assertEqual([f.__name__ for f in gw.status_loaders()],
                         ["quant_provider_status", "krx_provider_status", "ficc_provider_status",
                          "crypto_provider_status"])
        self.assertEqual(gw.endpoint("anthropic"), "https://api.anthropic.com/v1/messages")


if __name__ == "__main__":
    unittest.main()
