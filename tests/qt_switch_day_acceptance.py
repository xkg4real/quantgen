"""tools/qt_port/switch_day.py (OS-F1 non-Python edits) on a temporary copy of the files it edits. Offline."""
import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.qt_port import switch_day  # noqa: E402


class SwitchDayTests(unittest.TestCase):
    def copy(self):
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp)
        for path in {e[0] for e in switch_day.EDITS}:
            (tmp / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, tmp / path)
        return tmp

    def run_tool(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return switch_day.main(list(args))

    def test_every_edit_matches_the_current_files(self):
        for path, old, new, _ in switch_day.EDITS:
            with self.subTest(path=path, old=old):
                self.assertEqual(switch_day.state(ROOT, path, old, new), "to do")

    def test_apply_then_check_is_clean_and_idempotent(self):
        root = self.copy()
        self.assertEqual(self.run_tool("--check", str(root)), 1)
        self.assertEqual(self.run_tool("--apply", str(root)), 0)
        once = {p: (root / p).read_text(encoding="utf-8") for p in {e[0] for e in switch_day.EDITS}}
        self.assertEqual(self.run_tool("--apply", str(root)), 0)
        self.assertEqual(self.run_tool("--check", str(root)), 0)
        for p, text in once.items():
            self.assertEqual((root / p).read_text(encoding="utf-8"), text)
        self.assertIn(switch_day.NEW, (root / "pyproject.toml").read_text(encoding="utf-8"))

    def test_a_file_that_changed_is_reported_not_edited(self):
        root = self.copy()
        (root / "README.md").write_text("rewritten\n", encoding="utf-8")
        self.assertEqual(self.run_tool("--apply", str(root)), 2)
        self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "rewritten\n")


if __name__ == "__main__":
    unittest.main()
