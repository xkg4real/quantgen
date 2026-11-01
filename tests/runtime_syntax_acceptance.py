"""Compile shipped sources using the actual interpreter, without importing them.

Run on Python 3.10/3.11 as well as newer versions: ast.parse(feature_version=...)
on 3.12 does not reject the PEP 701 f-string quoting that broke Flet startup.
"""
from pathlib import Path
import subprocess
import unittest

from tools.packaging.stage import allowed


class RuntimeSyntaxTests(unittest.TestCase):
    def test_all_shipped_python_sources_compile(self):
        root = Path(__file__).resolve().parents[1]
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=root
        ).decode("utf-8").split("\0")
        sources = [name for name in tracked if name.endswith(".py") and allowed(name)]
        self.assertIn("main.py", sources)
        self.assertIn("core/research/crypto_workflow.py", sources)
        for name in sources:
            with self.subTest(source=name):
                compile((root / name).read_bytes(), name, "exec")


if __name__ == "__main__":
    unittest.main()
