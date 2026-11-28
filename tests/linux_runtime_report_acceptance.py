"""tools/packaging/linux_runtime_report.py (OS-F3): glibc floor and Qt platform plugin gaps of a Linux build."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.packaging import linux_runtime_report as lr


class ParseTests(unittest.TestCase):
    def test_newest_glibc(self):
        text = ("0000 DF *UND* 0000 (GLIBC_2.2.5) memcpy\n0000 DF *UND* 0000 (GLIBC_2.38) __isoc23_strtol\n"
                "0000 DF *UND* 0000 (GLIBC_2.14) memcpy\n")
        self.assertEqual(lr.newest_glibc(text), (2, 38, 0))
        self.assertEqual(lr._glibc_name((2, 38, 0)), "GLIBC_2.38")
        self.assertEqual(lr._glibc_name((2, 2, 5)), "GLIBC_2.2.5")
        self.assertIsNone(lr.newest_glibc("no versions"))

    def test_missing_libraries(self):
        out = ("\tlinux-vdso.so.1 (0x00007ffd)\n\tlibxcb-cursor.so.0 => not found\n"
               "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f)\n\tlibxcb-cursor.so.0 => not found\n"
               "\tlibxkbcommon-x11.so.0 => not found\n")
        self.assertEqual(lr.missing_libraries(out), ["libxcb-cursor.so.0", "libxkbcommon-x11.so.0"])


class ReportTests(unittest.TestCase):
    def test_checked_and_unchecked_plugin_reports(self):
        cases = (
            (subprocess.CompletedProcess([], 0, "libc.so => /lib/libc.so", ""), [], None),
            (subprocess.CompletedProcess([], 0, "linux-vdso.so.1", "libxcb.so => not found"), ["libxcb.so"], None),
            (subprocess.CompletedProcess([], 1, "", "inspection failed"), None, "exit 1"),
            (subprocess.CompletedProcess([], 0, "", "inspection warning"), None, "no standard output"),
            (subprocess.TimeoutExpired("ldd", 60), None, "timed out"),
            (FileNotFoundError(), None, "tool unavailable"),
            (PermissionError(), None, "could not start tool"),
        )
        name = "libqxcb.so"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / name).write_bytes(b"\x7fELFfixture")
            with patch.object(shutil, "which", side_effect=lambda tool: "/test/ldd" if tool == "ldd" else None):
                for response, missing, error in cases:
                    with self.subTest(response=response), patch.object(subprocess, "run", side_effect=[response]):
                        result = lr.report(Path(d))
                        self.assertEqual(result["qt_platform_plugins_missing"], {name: missing} if not error else {})
                        self.assertEqual(result["qt_platform_plugins_unchecked"], {name: error} if error else {})
            with patch.object(shutil, "which", return_value=None), patch.object(subprocess, "run") as run:
                result = lr.report(Path(d))
                run.assert_not_called()
                self.assertEqual(result["qt_platform_plugins_missing"], {})
                self.assertEqual(result["qt_platform_plugins_unchecked"], {name: "tool unavailable"})

    def test_folder_without_libraries(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "README.txt").write_text("x", encoding="utf-8")
            r = lr.report(Path(d))
        self.assertEqual((r["elf_files"], r["glibc_required"], r["qt_platform_plugins_missing"]), (0, None, {}))

    @unittest.skipUnless(shutil.which("objdump") and Path("/bin/true").is_file(), "needs objdump and /bin/true")
    def test_a_real_elf_file_has_a_glibc_floor(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy("/bin/true", Path(d) / "true")
            r = lr.report(Path(d))
        self.assertEqual(r["elf_files"], 1)
        self.assertTrue(r["glibc_required"].startswith("GLIBC_2."), r)
        self.assertEqual(r["glibc_holders"], ["true"])


if __name__ == "__main__":
    unittest.main()
