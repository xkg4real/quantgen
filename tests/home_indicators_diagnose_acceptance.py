"""OA-09: `python -m core.research.markets` prints six safe lines. Offline fakes only."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from core.research import markets
from tests.home_indicators_acceptance import TODAY, Calls, btc_ok, good_batch, kospi_ok

ROOT = Path(__file__).resolve().parents[1]


class Lines(unittest.TestCase):
    def test_six_lines_no_values(self):
        lines = markets.diagnose(series_loader=Calls(), btc_live=btc_ok, kospi_live=kospi_ok,
                                 kis_ready=lambda: False, today=TODAY)
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], "^GSPC OBSERVED reason=- live=-")
        self.assertEqual(lines[1], "^KS11 OBSERVED reason=- live=KEY_NEEDED/connection_not_configured")
        self.assertEqual(lines[5], "BTC-USD OBSERVED reason=- live=LIVE")
        joined = "\n".join(lines)
        for value in ("139", "131000000", "2650"):
            self.assertNotIn(value, joined)

    def test_failure_reasons(self):
        def boom(ids, source, days):
            raise ConnectionError("https://example/?api_key=SECRET")
        lines = markets.diagnose(series_loader=Calls(boom), btc_live=btc_ok, kis_ready=lambda: False, today=TODAY)
        self.assertTrue(all(" UNAVAILABLE reason=network_error " in line for line in lines))
        self.assertNotIn("SECRET", "\n".join(lines))

    def test_whole_call_failure_still_six_lines(self):
        def bad(**kwargs):
            raise ImportError("no gateway")
        orig = markets.load_home_indicators
        markets.load_home_indicators = bad
        try:
            lines = markets.diagnose()
        finally:
            markets.load_home_indicators = orig
        self.assertEqual(len(lines), 6)
        self.assertTrue(all("reason=dependency_missing" in line for line in lines))


class YahooLogHint(unittest.TestCase):
    def _run_with_log(self, message, empty=("^GSPC", "^KS11", "BTC-USD")):
        """Empty the given rows and log ``message`` on the yfinance logger; returns (lines, stderr text)."""
        import contextlib
        import io
        import logging

        def batch(ids, source, days):
            logging.getLogger("yfinance").error(message)
            out = good_batch(ids, source, days)
            for sym in empty:
                if sym in out:
                    s = out[sym]
                    out[sym] = type(s)(source=s.source, dates=(), values=(), note="")
            return out
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            lines = markets.diagnose(series_loader=Calls(batch), btc_live=btc_ok, kis_ready=lambda: False,
                                     today=TODAY)
        return lines, err.getvalue()

    def test_network_block_named(self):
        lines, _ = self._run_with_log("Failed to get ticker '^GSPC' reason: curl: (7) CONNECT tunnel failed, response 403")
        self.assertTrue(lines[0].endswith("reason=no_observations live=- via=network_error"), lines[0])

    def test_empty_fred_row_gets_no_hint(self):
        """The via= hint is for Yahoo rows only, also when a FRED row is empty in the same run (DS-5)."""
        lines, _ = self._run_with_log("curl: (6) Could not resolve host: query2.finance.yahoo.com",
                                      empty=("^GSPC", "DGS10"))
        self.assertIn("via=network_error", lines[0])
        fred = next(l for l in lines if l.startswith("DGS10 "))
        self.assertIn("reason=no_observations", fred)
        self.assertNotIn("via=", fred)

    def test_provider_text_not_on_console(self):
        """Nothing reaches stderr or a console handler the app may have put on the root logger (DS-5)."""
        import io
        import logging
        message = "Failed to get ticker '^GSPC' reason: curl: (6) Could not resolve host: query2.finance.yahoo.com See https://curl.se/libcurl/c/libcurl-errors.html"
        console = io.StringIO()
        root_handler = logging.StreamHandler(console)
        logging.getLogger().addHandler(root_handler)
        self.addCleanup(logging.getLogger().removeHandler, root_handler)
        lines, err = self._run_with_log(message)
        self.assertEqual((err, console.getvalue()), ("", ""))
        for text in ("curl", "http", "Failed to get ticker"):
            self.assertNotIn(text, "\n".join(lines))

    def test_reason_order(self):
        cases = {
            "YFRateLimitError: Too Many Requests": "rate_limited",
            "SSLError: CERTIFICATE_VERIFY_FAILED self-signed certificate": "certificate_error",
            "curl: (60) SSL certificate problem: unable to get local issuer certificate": "certificate_error",
            "(SSLError) ConnectionResetError(104, 'Connection reset by peer')": "network_error",
            "curl: (28) Operation timed out after 10000 milliseconds": "network_timeout",
            "NameResolutionError: Failed to resolve 'query2.finance.yahoo.com'": "network_error",
            "SSLError: something": "certificate_error",
        }
        for message, code in cases.items():
            with self.subTest(message=message):
                self.assertIn(f"via={code}", self._run_with_log(message)[0][0])

    def test_logger_restored(self):
        """Start from a non-default state so a leak from an earlier diagnose() in this process cannot hide (DS-4)."""
        import logging
        logger = logging.getLogger("yfinance")
        saved = (logger.propagate, logger.level)
        self.addCleanup(lambda: (setattr(logger, "propagate", saved[0]), logger.setLevel(saved[1])))
        logger.propagate = True
        logger.setLevel(logging.WARNING)
        before = (logger.propagate, logger.level, list(logger.handlers))
        self._run_with_log("x")
        self.assertEqual((logger.propagate, logger.level, list(logger.handlers)), before)


DEAD_PROXY = "http://127.0.0.1:9"
PROXY_NAMES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
# Runs ``python -m core.research.markets`` (runpy, same as -m) after: no .env (dotenv and the credential
# store's development loader are no-ops), no OS credential store, and a socket guard that refuses and counts
# every Python-level DNS lookup or connection other than the dead proxy 127.0.0.1:9. The counts go to a file,
# not stderr, so the test can also require an empty stderr. yfinance's curl_cffi transport is C code below
# this guard; it is kept on the dead proxy by the lower- and upper-case proxy variables (no NO_PROXY).
BOOTSTRAP = r"""
import json, os, runpy, socket, sys
blocked = {"dns": [], "connect": []}
LOCAL = ("127.0.0.1", "::1", "localhost")
_gai = socket.getaddrinfo
def getaddrinfo(host, *a, **k):
    if host not in LOCAL:
        blocked["dns"].append(str(host)[:80])
        raise socket.gaierror(-2, "blocked by test")
    return _gai(host, *a, **k)
socket.getaddrinfo = getaddrinfo
_connect, _connect_ex = socket.socket.connect, socket.socket.connect_ex
def _ok(addr):
    return isinstance(addr, tuple) and addr[0] in LOCAL and addr[1] == 9
def connect(self, addr):
    if not _ok(addr):
        blocked["connect"].append(repr(addr)[:80])
        raise ConnectionRefusedError("blocked by test")
    return _connect(self, addr)
def connect_ex(self, addr):
    if not _ok(addr):
        blocked["connect"].append(repr(addr)[:80])
        return 111
    return _connect_ex(self, addr)
socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
try:
    import dotenv
    dotenv.load_dotenv = lambda *a, **k: False
except ImportError:
    pass
from core import credentials
credentials.load_dotenv_for_development = lambda: None
credentials.set_backend(None)
try:
    runpy.run_module("core.research.markets", run_name="__main__", alter_sys=True)
finally:
    with open(os.environ["QG_TEST_GUARD_OUT"], "w", encoding="utf-8") as f:
        json.dump(blocked, f)
"""


def offline_env(home: Path) -> dict:
    """The caller's environment minus proxy exceptions and every credential-store secret name; all proxy
    variables (both cases) on the dead proxy; user folders and the FICC cache in ``home``."""
    from core.credentials import names
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("NO_PROXY",) + PROXY_NAMES and not names.is_secret(k)}
    for name in PROXY_NAMES:
        env[name] = env[name.lower()] = DEAD_PROXY
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CACHE_HOME", "XDG_CONFIG_HOME"):
        env[name] = str(home)
    env["NEXTGEN_FICC_CACHE"] = str(home / "ficc_cache")
    env["NEXTGEN_FICC_CACHE_TTL"] = "0"
    env["QG_TEST_GUARD_OUT"] = str(home / "guard.json")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class CommandLine(unittest.TestCase):
    def test_env_has_no_proxy_exception_and_no_secrets(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {
                "NO_PROXY": "*", "no_proxy": "*", "https_proxy": "http://real.example:8080", "KIS_APP_KEY": "x"}):
            env = offline_env(Path(tmp))
        self.assertNotIn("NO_PROXY", env)
        self.assertNotIn("no_proxy", env)
        self.assertNotIn("KIS_APP_KEY", env)
        self.assertEqual({env[n] for n in PROXY_NAMES + tuple(n.lower() for n in PROXY_NAMES)}, {DEAD_PROXY})

    def test_module_runs_offline_exit_0_six_lines(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            proc = subprocess.run([sys.executable, "-c", BOOTSTRAP], cwd=ROOT, env=offline_env(home),
                                  capture_output=True, text=True, timeout=600)
            guard = json.loads((home / "guard.json").read_text(encoding="utf-8"))
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        self.assertEqual(proc.stderr, "")                       # no provider text, URL or traceback reaches it
        self.assertEqual(guard, {"dns": [], "connect": []})    # nothing left the machine through Python sockets
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(len(lines), 6, proc.stdout)
        self.assertEqual([l.split()[0] for l in lines], [s[1] for s in markets.SPECS])
        self.assertTrue(all(" UNAVAILABLE " in l for l in lines), proc.stdout)   # a reached provider would not be


if __name__ == "__main__":
    unittest.main()
