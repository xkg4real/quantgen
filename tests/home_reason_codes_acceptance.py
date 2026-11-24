"""D11: provider_failure_reason sorts wrapped transport failures (urllib3/requests text inside another
library's message) into network_timeout / network_error. Offline: exceptions are built locally."""
from __future__ import annotations

import unittest

from core.research.markets import FAILURE_REASONS, _note_reason, provider_failure_reason


class RemoteDataError(OSError):
    """Stands in for pandas_datareader's wrapper (name and text only)."""


POOL = "HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Max retries exceeded with url: /graph (Caused by "

TIMEOUT = {
    "linux connect timeout": POOL + "ConnectTimeoutError(<urllib3.connection.HTTPSConnection object>, "
                                    "'Connection to fred.stlouisfed.org timed out. (connect timeout=12.0)'))",
    "read timeout": "Read timed out. (read timeout=12.0)",
    "urllib3 read": POOL + "ReadTimeoutError(\"HTTPSConnectionPool(host='x', port=443): Read timed out.\"))",
    "curl": "curl: (28) Operation timed out after 12001 milliseconds with 0 bytes received",
    "windows 10060": POOL + "NewConnectionError('<...>: Failed to establish a new connection: [WinError 10060] "
                            "A connection attempt failed because the connected party did not properly respond'))",
}
NETWORK = {
    "linux dns": POOL + "NameResolutionError(\"<...>: Failed to resolve 'fred.stlouisfed.org' "
                        "([Errno -3] Temporary failure in name resolution)\"))",
    "linux dns 2": "[Errno -2] Name or service not known",
    "mac dns": "[Errno 8] nodename nor servname provided, or not known",
    "windows dns": POOL + "NameResolutionError(\"<...>: Failed to resolve 'fred.stlouisfed.org' "
                          "([Errno 11001] getaddrinfo failed)\"))",
    "linux refused": POOL + "NewConnectionError('<...>: Failed to establish a new connection: "
                            "[Errno 111] Connection refused'))",
    "windows refused": POOL + "NewConnectionError('<...>: Failed to establish a new connection: [WinError 10061] "
                              "No connection could be made because the target machine actively refused it'))",
    "reset": "('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))",
    "windows reset": "('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly "
                     "closed by the remote host', None, 10054, None))",
    "unreachable": "[Errno 101] Network is unreachable",
}
PROVIDER = {
    "5xx retries": POOL + "ResponseError('too many 500 error responses'))",
    "plain": "something else went wrong",
    "max retries alone": "Max retries exceeded with url: /graph",
}


class WrappedTransport(unittest.TestCase):
    def check(self, cases, expected):
        for name, text in cases.items():
            with self.subTest(case=name):
                self.assertEqual(provider_failure_reason(RemoteDataError(text)), expected)
                self.assertEqual(_note_reason(text), expected)

    def test_timeouts(self):
        self.check(TIMEOUT, "network_timeout")

    def test_network_errors(self):
        self.check(NETWORK, "network_error")

    def test_provider_failures_unchanged(self):
        self.check(PROVIDER, "provider_unavailable")

    def test_earlier_rules_keep_priority(self):
        self.assertEqual(provider_failure_reason(RuntimeError("HTTP 429 Connection reset")), "rate_limited")
        self.assertEqual(provider_failure_reason(RuntimeError("HTTP 403 timed out")), "access_denied")
        self.assertEqual(provider_failure_reason(RuntimeError("SSLError: CERTIFICATE_VERIFY_FAILED")),
                         "certificate_error")

    def test_no_new_codes(self):
        self.assertEqual(FAILURE_REASONS, frozenset({
            "dependency_missing", "dependency_incompatible", "connection_not_configured",
            "rate_limited", "network_timeout", "network_error", "certificate_error",
            "access_denied", "no_observations", "insufficient_observations",
            "invalid_response", "provider_unavailable"}))


if __name__ == "__main__":
    unittest.main()
