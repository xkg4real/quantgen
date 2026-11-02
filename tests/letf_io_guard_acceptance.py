"""Prove LETF-only audit protection does not leak into other test modules.

Each child emits audit events directly; it never opens a protected path or
creates/connects a socket. A separate process isolates permanent audit hooks
from any outer test harness and tests the real sys.addaudithook registration.
"""
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


_PRELUDE = """
import sys
import unittest
sys.dont_write_bytecode = True
from tests import letf_assumptions_acceptance as guarded

def emit_protected_events():
    sys.audit('socket.connect', None, ('127.0.0.1', 0))
    sys.audit('open', 'cache/LETF_AUDIT_PROBE', 'r', 0)

# Import/discovery must not block another module's Windows asyncio loopback.
emit_protected_events()
assert not guarded._private_io_guard_active
"""


class LETFIoGuardTests(unittest.TestCase):
    def run_probe(self, body):
        result = subprocess.run(
            [sys.executable, '-c', textwrap.dedent(_PRELUDE) + textwrap.dedent(body)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True,
            text=True, encoding='utf-8', timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_active_module_blocks_providers_and_protected_inputs_then_releases(self):
        self.run_probe("""
        class Probe(unittest.TestCase):
            __module__ = guarded.__name__
            def test_guard(self):
                self.assertTrue(guarded._private_io_guard_active)
                with self.assertRaisesRegex(AssertionError, 'No providers'):
                    sys.audit('socket.connect', None, ('127.0.0.1', 0))
                for path in ('.env', 'cache/LETF_AUDIT_PROBE', 'paper_live/probe',
                             'grokteam/probe', 'cards/probe', '_backup/probe'):
                    with self.subTest(path=path), self.assertRaisesRegex(AssertionError, 'Protected input'):
                        sys.audit('open', path, 'r', 0)
                sys.audit('open', 'synthetic-fixture.txt', 'r', 0)
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(Probe).run(result)
        assert result.testsRun == 1 and result.wasSuccessful(), (result.errors, result.failures)
        assert not guarded._private_io_guard_active
        emit_protected_events()
        """)

    def test_failed_module_test_still_releases_guard_for_next_suite(self):
        self.run_probe("""
        class Probe(unittest.TestCase):
            __module__ = guarded.__name__
            def test_failure(self):
                self.assertTrue(guarded._private_io_guard_active)
                raise RuntimeError('Expected fixture failure')
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(Probe).run(result)
        assert result.testsRun == 1 and len(result.errors) == 1
        assert 'Expected fixture failure' in result.errors[0][1]
        assert not guarded._private_io_guard_active
        emit_protected_events()
        """)


if __name__ == '__main__':
    unittest.main()
