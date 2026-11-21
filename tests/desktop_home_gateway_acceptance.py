"""KEY-5 request sites 3/12: native Home/Summary through the FICC gateway.

Only temporary storage and synthetic series are used. The provider fake binds to
the real provider signature; no data-source request or OS credential backend runs.
"""
from __future__ import annotations

from contextlib import ExitStack
from datetime import date
import inspect
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch


def _denied(*args, **kwargs):
    raise AssertionError("external I/O is forbidden in this fixture")


def setUpModule():
    global hv, ms, fd, gw, local, SERIES_SIGNATURE
    stack = ExitStack()
    unittest.addModuleCleanup(stack.close)
    home = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="qg-home-gateway-")))
    stack.enter_context(patch.object(Path, "home", return_value=home))
    stack.enter_context(patch.dict(os.environ, {
        "QT_QPA_PLATFORM": "offscreen", "LOCALAPPDATA": str(home / "Local"),
        "APPDATA": str(home / "Roaming"), "XDG_DATA_HOME": str(home / "data"),
        "XDG_CONFIG_HOME": str(home / "config"), "XDG_CACHE_HOME": str(home / "cache"),
        "QUANTGEN_DATA_DIR": str(home / "quantgen"), "FLET_APP_STORAGE_DATA": "",
    }))
    import dotenv
    stack.enter_context(patch.object(dotenv, "load_dotenv", return_value=False))
    stack.enter_context(patch.object(socket, "create_connection", side_effect=_denied))
    stack.enter_context(patch.object(socket.socket, "connect", side_effect=_denied))
    stack.enter_context(patch.object(socket.socket, "connect_ex", side_effect=_denied))
    from core import credentials
    from core.credentials import names
    stack.enter_context(patch.dict(os.environ, {name: "" for name in (*names.SECRETS, *names.RESEARCH)}))
    stack.enter_context(patch.object(credentials, "_lookup", return_value=("", None)))
    for name in ("_kr_get", "_kr_set", "_kr_delete"):
        stack.enter_context(patch.object(credentials, name, side_effect=_denied))
    from core.ficc import data as fd
    from core import gateway as gw
    from core.gateway import local
    from quantgen_desktop import home_view as hv, market_summary as ms
    SERIES_SIGNATURE = inspect.signature(fd.load_series)


class HomeGatewayTests(unittest.TestCase):
    def patched(self, *args, **kwargs):
        pending = patch.object(*args, **kwargs)
        self.addCleanup(pending.stop)
        return pending.start()

    def setUp(self):
        self.calls = []
        self.answer = fd.Series("DGS10", "SYNTHETIC fixture", "FRED",
                                ("2026-11-19", "2026-11-20"), (4.1, 4.2), "SYNTHETIC fixture")
        self.error = None

        def provider(*args, **kwargs):
            bound = SERIES_SIGNATURE.bind(*args, **kwargs)
            bound.apply_defaults()
            self.calls.append(dict(bound.arguments))
            if self.error is not None:
                raise self.error
            return self.answer

        self.leaf = self.patched(fd, "load_series", side_effect=provider)
        self.gateway = self.patched(gw, "ficc", return_value=local.FiccData())
        self.blocked = self.patched(gw, "blocked", return_value="")
        self.patched(gw, "profile", return_value="personal")

    def test_home_default_passes_explicit_provider_and_days_through_gateway(self):
        for symbol, source in (("DGS10", "fred"), ("BTC-USD", "yfinance")):
            with self.subTest(source=source):
                self.calls.clear()
                self.gateway.reset_mock()
                self.answer = fd.Series(symbol, "SYNTHETIC fixture", source.upper(),
                                        ("2026-11-19", "2026-11-20"), (4.1, 4.2), "SYNTHETIC fixture")
                history = hv.load_market_history(hv.MarketInfo(symbol, source, "USD"),
                                                 days=34, today=date(2026, 11, 21))
                self.gateway.assert_called_once_with()
                self.assertEqual(self.calls, [{"id": symbol, "source": source, "days": 34, "label": ""}])
                self.assertTrue(history.ok)
                self.assertEqual((history.symbol, history.source, history.dates, history.values),
                                 (symbol, source.upper(), ("2026-11-19", "2026-11-20"), (4.1, 4.2)))

    def test_injected_home_loader_never_resolves_gateway(self):
        supplied = []

        def injected(symbol, *, source, days):
            supplied.append((symbol, source, days))
            return self.answer

        history = hv.load_market_history(hv.MarketInfo("DGS10", "fred", "%"), loader=injected,
                                         days=35, today=date(2026, 11, 21))
        self.assertTrue(history.ok)
        self.assertEqual(supplied, [("DGS10", "fred", 35)])
        self.gateway.assert_not_called()
        self.assertEqual(self.calls, [])

    def test_summary_returns_same_object_and_preserves_source_days_and_label(self):
        answer = ms.production_series("DGS10", source="fred", days=36, label="SYNTHETIC label")
        self.assertIs(answer, self.answer)
        self.gateway.assert_called_once_with()
        self.assertEqual(self.calls, [{"id": "DGS10", "source": "fred", "days": 36,
                                      "label": "SYNTHETIC label"}])

    def test_summary_preserves_type_error_before_any_provider_request(self):
        with self.assertRaises(TypeError):
            ms.production_series("DGS10", source="fred", unknown_argument=True)
        self.assertEqual(self.calls, [])

    def test_home_hides_provider_message_but_summary_propagates_same_exception(self):
        self.error = TimeoutError("SYNTHETIC_PRIVATE_TOKEN https://example.invalid/?key=fixture")
        history = hv.load_market_history(hv.MarketInfo("DGS10", "fred", "%"))
        self.assertEqual(history.reason, "network_timeout")
        self.assertEqual(history.values, ())
        self.assertNotIn("SYNTHETIC_PRIVATE_TOKEN", repr(history))
        self.assertNotIn("example.invalid", repr(history))
        with self.assertRaises(TimeoutError) as caught:
            ms.production_series("DGS10", source="fred")
        self.assertIs(caught.exception, self.error)

    def test_blocked_explicit_provider_never_reaches_leaf(self):
        self.blocked.return_value = "off"
        history = hv.load_market_history(hv.MarketInfo("DGS10", "fred", "%"))
        self.assertFalse(history.ok)
        self.assertTrue(history.reason)
        with self.assertRaises(gw.GatewayOff):
            ms.production_series("BTC-USD", source="yfinance", days=40)
        self.assertEqual(self.calls, [])

    def test_gateway_resolution_failure_keeps_home_sanitization_and_summary_exception(self):
        error = RuntimeError("SYNTHETIC_GATEWAY_PRIVATE_MESSAGE")
        self.gateway.side_effect = error
        history = hv.load_market_history(hv.MarketInfo("DGS10", "fred", "%"))
        self.assertFalse(history.ok)
        self.assertNotIn("SYNTHETIC_GATEWAY_PRIVATE_MESSAGE", repr(history))
        with self.assertRaises(RuntimeError) as caught:
            ms.production_series("DGS10", source="fred")
        self.assertIs(caught.exception, error)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
