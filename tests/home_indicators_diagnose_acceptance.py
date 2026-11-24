"""OA-09: `python -m core.research.markets` prints six safe lines. Offline fakes only."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

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
    def _run_with_log(self, message):
        import logging

        def empty_yahoo(ids, source, days):
            logging.getLogger("yfinance").error(message)
            out = good_batch(ids, source, days)
            for sym in ("^GSPC", "^KS11", "BTC-USD"):
                s = out[sym]
                out[sym] = type(s)(source=s.source, dates=(), values=(), note="")
            return out
        return markets.diagnose(series_loader=Calls(empty_yahoo), btc_live=btc_ok, kis_ready=lambda: False,
                                today=TODAY)

    def test_network_block_named(self):
        lines = self._run_with_log("Failed to get ticker '^GSPC' reason: curl: (7) CONNECT tunnel failed, response 403")
        self.assertTrue(lines[0].endswith("reason=no_observations live=- via=network_error"), lines[0])
        self.assertNotIn("via=", lines[2])          # FRED row untouched

    def test_rate_limit_and_tls(self):
        self.assertIn("via=rate_limited", self._run_with_log("YFRateLimitError: Too Many Requests")[0])
        self.assertIn("via=certificate_error",
                      self._run_with_log("SSLError: CERTIFICATE_VERIFY_FAILED self-signed certificate")[0])

    def test_logger_restored(self):
        import logging
        logger = logging.getLogger("yfinance")
        before = (logger.propagate, logger.level, list(logger.handlers))
        self._run_with_log("x")
        self.assertEqual((logger.propagate, logger.level, list(logger.handlers)), before)


class CommandLine(unittest.TestCase):
    def test_module_runs_exit_0_six_lines(self):
        env = dict(os.environ, NO_PROXY="*", no_proxy="*", HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9")
        proc = subprocess.run([sys.executable, "-m", "core.research.markets"], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=600)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        self.assertNotIn("Traceback", proc.stderr)
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(len(lines), 6, proc.stdout)
        self.assertEqual([l.split()[0] for l in lines], [s[1] for s in markets.SPECS])


if __name__ == "__main__":
    unittest.main()
