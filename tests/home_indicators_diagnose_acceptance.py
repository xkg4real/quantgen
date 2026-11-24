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
            "curl: (28) Connection timeout after 10002 ms": "network_timeout",
            "curl: (60) SSL peer cert or SSH remote key was not OK": "certificate_error",
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


PROXY_NAMES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
# Runs ``python -m core.research.markets`` (runpy, same as -m) after: no .env (dotenv and the credential
# store's development loader are no-ops), no OS credential store, and a socket guard. The guard refuses and
# records Python-level name lookups (getaddrinfo, gethostbyname, gethostbyname_ex, gethostbyaddr) of any host
# but loopback and connections/sendto to any address but the test's own proxy sink (review DSF-8: functions not
# listed here, e.g. raw ``_socket``, are not wrapped). The record goes to a file, not stderr, so the test can
# also require an empty stderr. yfinance's curl_cffi transport is C code below this guard; it is kept on the
# sink by the lower- and upper-case proxy variables (no NO_PROXY). ``deps`` says which provider libraries the
# child could import, so the test can require each library's own dead-proxy mark (review DSF-1).
BOOTSTRAP = r"""
import errno, importlib.util, json, os, runpy, socket, sys
PORT = int(os.environ["QG_TEST_PROXY_PORT"])
LOCAL = ("127.0.0.1", "::1", "localhost")
blocked = {"dns": [], "connect": []}
deps = {name: importlib.util.find_spec(name) is not None for name in ("requests", "pandas_datareader", "yfinance")}
def _dns(fn):
    def wrapped(host, *a, **k):
        if host not in LOCAL:
            blocked["dns"].append(str(host)[:80])
            raise socket.gaierror(-2, "blocked by test")
        return fn(host, *a, **k)
    return wrapped
for _name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
    setattr(socket, _name, _dns(getattr(socket, _name)))
_connect, _connect_ex, _sendto = socket.socket.connect, socket.socket.connect_ex, socket.socket.sendto
def _ok(addr):
    return isinstance(addr, tuple) and addr[0] in LOCAL and addr[1] == PORT
def connect(self, addr):
    if not _ok(addr):
        blocked["connect"].append(repr(addr)[:80])
        raise ConnectionRefusedError(errno.ECONNREFUSED, "blocked by test")
    return _connect(self, addr)
def connect_ex(self, addr):
    if not _ok(addr):
        blocked["connect"].append(repr(addr)[:80])
        return errno.ECONNREFUSED
    return _connect_ex(self, addr)
def sendto(self, data, *rest):
    addr = rest[-1]
    if not _ok(addr):
        blocked["connect"].append("sendto " + repr(addr)[:80])
        raise ConnectionRefusedError(errno.ECONNREFUSED, "blocked by test")
    return _sendto(self, data, *rest)
socket.socket.connect, socket.socket.connect_ex, socket.socket.sendto = connect, connect_ex, sendto
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
        json.dump({"blocked": blocked, "deps": deps}, f)
"""


class ProxySink:
    """A loopback port the test owns (review DSF-7): bound to a free port and closed again, so every proxy
    attempt is refused at once (a closed port, not the well-known port 9 that a discard service or a filter
    could hold open). An accept-and-close listener was tried first: it made requests report the proxy as
    "remote end closed" (provider_unavailable on this branch) and took longer, so a refused port is used."""

    def __init__(self):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            self.port = probe.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


def offline_env(home: Path, proxy_port: int) -> dict:
    """The caller's environment minus proxy exceptions and every credential-store secret name; all proxy
    variables (both cases) on the test's sink; user folders and the FICC cache in ``home``."""
    from core.credentials import names
    proxy = f"http://127.0.0.1:{proxy_port}"
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("NO_PROXY",) + PROXY_NAMES and not names.is_secret(k)
           and k not in ("QUANTGEN_DATA_DIR", "FLET_APP_STORAGE_DATA", "XDG_DATA_HOME")}
    for name in PROXY_NAMES:
        env[name] = env[name.lower()] = proxy
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CACHE_HOME", "XDG_CONFIG_HOME",
                 "WIN_PD_OVERRIDE_LOCAL_APPDATA", "WIN_PD_OVERRIDE_APPDATA"):   # platformdirs on Windows (DSF-12)
        env[name] = str(home)
    for name in names.SECRETS:          # set empty, so even a .env loader that slipped through adds no KIS key (PD-1)
        env[name] = ""
    env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"
    env["NEXTGEN_FICC_CACHE"] = str(home / "ficc_cache")
    env["NEXTGEN_FICC_CACHE_TTL"] = "0"
    env["QG_TEST_GUARD_OUT"] = str(home / "guard.json")
    env["QG_TEST_PROXY_PORT"] = str(proxy_port)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_offline(home: Path, env_changes=None):
    """(CompletedProcess, guard record) of the command under the bootstrap, proxies on a fresh sink."""
    import json
    with ProxySink() as sink:
        env = offline_env(home, sink.port)
        for key, value in (env_changes or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        proc = subprocess.run([sys.executable, "-c", BOOTSTRAP], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=600)
    out = home / "guard.json"
    record = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else None
    return proc, record, env


class CommandLine(unittest.TestCase):
    def test_env_has_no_proxy_exception_and_no_secrets(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {
                "NO_PROXY": "*", "no_proxy": "*", "https_proxy": "http://real.example:8080", "KIS_APP_KEY": "x"}):
            env = offline_env(Path(tmp), 4321)
        self.assertNotIn("NO_PROXY", env)
        self.assertNotIn("no_proxy", env)
        self.assertEqual(env["KIS_APP_KEY"], "")
        self.assertEqual(env["PYTHON_KEYRING_BACKEND"], "keyring.backends.null.Keyring")
        self.assertNotIn("QUANTGEN_DATA_DIR", env)
        self.assertEqual(env["WIN_PD_OVERRIDE_LOCAL_APPDATA"], tmp)
        self.assertEqual({env[n] for n in PROXY_NAMES + tuple(n.lower() for n in PROXY_NAMES)},
                         {"http://127.0.0.1:4321"})

    def test_module_runs_offline_exit_0_six_lines(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            proc, record, _ = run_offline(Path(tmp))
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])           # before the record (DSF-8)
        self.assertIsNotNone(record, "child wrote no guard record: " + proc.stderr[-500:])
        self.assertEqual(proc.stderr, "")                       # no provider text, URL or traceback reaches it
        self.assertEqual(record["blocked"], {"dns": [], "connect": []})   # nothing left through Python sockets
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(len(lines), 6, proc.stdout)
        self.assertEqual([l.split()[0] for l in lines], [s[1] for s in markets.SPECS])
        row = {l.split()[0]: l for l in lines}
        deps = record["deps"]
        # DSF-1: UNAVAILABLE alone would also pass a broken import; require each library's mark of the sink.
        if not (deps["requests"] or deps["pandas_datareader"] or deps["yfinance"]):
            self.skipTest(f"child imports no provider library ({deps}); only dependency_missing is possible")
        if deps["requests"] or deps["pandas_datareader"]:
            for sym in ("DEXKOUS", "DGS10", "VIXCLS"):
                self.assertIn(" UNAVAILABLE reason=network_error ", row[sym])
        if deps["requests"]:
            self.assertIn("live=UNAVAILABLE/network_error", row["BTC-USD"])
        if deps["yfinance"]:
            for sym in ("^GSPC", "^KS11", "BTC-USD"):
                self.assertTrue(row[sym].endswith("via=network_error"), row[sym])
        self.assertNotIn("dependency_missing", proc.stdout)

    @unittest.skipIf(sys.platform == "win32", "POSIX folder mode")
    def test_command_prepares_data_folder_first(self):
        """PD-3: with no ~/.nextgen and no QUANTGEN folder the command creates the platform folder 0700 with
        the QUANTGEN marker (core.app_paths.ensure_user_data_dir), not a bare default-mode cache folder."""
        import stat
        import tempfile
        from core import app_paths
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            proc, _, env = run_offline(home, {"NEXTGEN_FICC_CACHE": None})
            folder = app_paths.user_data_dir(home=home, env=env, platform=sys.platform)
            self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
            self.assertTrue(folder.is_dir(), folder)
            self.assertEqual(stat.S_IMODE(folder.stat().st_mode), 0o700)
            self.assertTrue((folder / app_paths.DATA_MARKER).is_file())

    def test_refused_folder_gives_six_lines_and_no_provider_call(self):
        called = []

        def refuse():
            raise PermissionError(13, "denied")
        lines = markets.main(ensure_data_dir=refuse, run=lambda: called.append(1) or [])
        self.assertEqual(called, [])
        self.assertEqual(len(lines), 6)
        self.assertTrue(all(l.endswith("UNAVAILABLE reason=data_dir_unavailable live=-") for l in lines))
        self.assertEqual([l.split()[0] for l in lines], [s[1] for s in markets.SPECS])

    def test_folder_prepared_before_diagnosis(self):
        order = []
        markets.main(ensure_data_dir=lambda: order.append("ensure"), run=lambda: order.append("run") or [])
        self.assertEqual(order, ["ensure", "run"])


if __name__ == "__main__":
    unittest.main()
