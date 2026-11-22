"""Mobile entry/staging boundaries. Uses synthetic repositories and controls, never a live app server."""
from __future__ import annotations

import ast
import builtins
from contextlib import ExitStack
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.packaging.stage import allowed, stage


class MobileStageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.repo = self.base / "source"
        self.repo.mkdir()
        files = {
            "main.py": "# Desktop entry sentinel; never executed.\n",
            "pyproject.toml": '[project]\nname="desktop-fixture"\n',
            "core/theme.py": "LIGHT = 'fixture-palette'\n",
            "ui/page.py": "from quantgen_desktop.language import TEXT\n",
            "quantgen_desktop/__init__.py": "",
            "quantgen_desktop/language.py": "TEXT = 'fixture'\n",
            "quantgen_desktop/window.py": "import PySide6\n",
            "assets/fonts/qg-interface.otf": "synthetic-font-fixture",
        }
        for name, content in files.items():
            self.write(name, content)
        self.git("init", "-q")
        self.git("add", "--", *files)
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-q", "-m", "Synthetic packaging fixture")
        self.head = self.git("rev-parse", "HEAD")
        # Deliberately untracked: explicit mobile overrides are not discovered by git ls-files.
        self.write("mobile/main.py", "# Mobile entry sentinel; never executed.\n")
        self.write("mobile/pyproject.toml", '[project]\nname="mobile-fixture"\n')

    def write(self, name, content):
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True).strip()

    def manifest(self, output):
        return json.loads((output / "STAGE_MANIFEST.json").read_text(encoding="utf-8"))

    def test_mobile_uses_explicit_untracked_entry_and_honest_manifest(self):
        self.assertNotIn("mobile/main.py", self.git("ls-files").splitlines())
        output = self.base / "mobile-stage"
        count = stage(self.repo, output, "mobile")
        manifest = self.manifest(output)
        self.assertEqual((output / "main.py").read_bytes(), (self.repo / "mobile/main.py").read_bytes())
        self.assertEqual((output / "pyproject.toml").read_bytes(),
                         (self.repo / "mobile/pyproject.toml").read_bytes())
        self.assertNotIn("main.py", manifest)
        self.assertNotIn("pyproject.toml", manifest)
        self.assertEqual(manifest.count("mobile/main.py -> main.py"), 1)
        self.assertEqual(manifest.count("mobile/pyproject.toml -> pyproject.toml"), 1)
        targets = [entry.split(" -> ")[-1] for entry in manifest]
        actual = sorted(p.relative_to(output).as_posix() for p in output.rglob("*")
                        if p.is_file() and p.name != "STAGE_MANIFEST.json")
        self.assertEqual(sorted(targets), actual)
        self.assertEqual(len(targets), len(set(targets)))
        self.assertEqual(count, len(actual))
        self.assertFalse((output / "quantgen_desktop/window.py").exists())
        self.assertTrue((output / "quantgen_desktop/language.py").is_file())
        self.assertTrue((output / "assets/fonts/qg-interface.otf").is_file())
        self.assertEqual(self.git("rev-parse", "HEAD"), self.head)

    def test_desktop_default_keeps_existing_entry_selection_and_bytes(self):
        output = self.base / "desktop-stage"
        tracked = self.git("ls-files").splitlines()
        count = stage(self.repo, output)
        self.assertEqual(self.manifest(output), [name for name in tracked if allowed(name)])
        self.assertEqual(count, len(self.manifest(output)))
        for name in ("main.py", "pyproject.toml"):
            self.assertEqual((output / name).read_bytes(), (self.repo / name).read_bytes())
        self.assertTrue((output / "quantgen_desktop/window.py").is_file())
        self.assertEqual(self.git("rev-parse", "HEAD"), self.head)

    def test_missing_mobile_entry_fails_before_creating_stage(self):
        (self.repo / "mobile/main.py").unlink()
        output = self.base / "absent-stage"
        with self.assertRaisesRegex(ValueError, "mobile/main.py"):
            stage(self.repo, output, "mobile")
        self.assertFalse(output.exists())

    def test_missing_mobile_project_fails_before_creating_stage(self):
        (self.repo / "mobile/pyproject.toml").unlink()
        output = self.base / "absent-project-stage"
        with self.assertRaisesRegex(ValueError, "mobile/pyproject.toml"):
            stage(self.repo, output, "mobile")
        self.assertFalse(output.exists())

    def test_symlinked_mobile_override_is_refused_before_copy(self):
        original = self.repo / "mobile/main.py"
        original.unlink()
        try:
            original.symlink_to(self.repo / "main.py")
        except OSError:
            self.skipTest("This host cannot create symlinks")
        output = self.base / "symlink-stage"
        with self.assertRaisesRegex(ValueError, "mobile/main.py"):
            stage(self.repo, output, "mobile")
        self.assertFalse(output.exists())

    def test_existing_destination_is_never_reused(self):
        output = self.base / "existing"
        output.mkdir()
        marker = output / "marker.txt"
        marker.write_text("existing contents", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            stage(self.repo, output, "mobile")
        self.assertEqual(marker.read_text(encoding="utf-8"), "existing contents")


class MobileEntryTests(unittest.TestCase):
    def test_entry_imports_only_flet_and_static_theme(self):
        tree = ast.parse((ROOT / "mobile/main.py").read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertEqual(imports, {"__future__", "flet", "core.theme"})

    def test_real_flet_controls_without_imports_network_environment_or_writes(self):
        try:
            import flet as ft
        except ImportError:
            self.skipTest("Install the pinned Flet 0.85.2 to run the real-control construction check")
        self.assertEqual(version("flet"), "0.85.2")
        spec = importlib.util.spec_from_file_location("quantgen_mobile_preview_acceptance", ROOT / "mobile/main.py")
        module = importlib.util.module_from_spec(spec)
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            root = name.split(".")[0]
            if root in {"scipy", "matplotlib", "PyQt6", "PySide6", "shiboken6", "sip",
                        "dotenv", "keyring", "data", "ui", "quantgen_desktop", "config"}:
                raise AssertionError("Disallowed mobile startup import: " + name)
            if root == "core" and name not in {"core", "core.theme"}:
                raise AssertionError("Disallowed mobile startup import: " + name)
            return original_import(name, *args, **kwargs)

        def forbidden(*args, **kwargs):
            raise AssertionError("Mobile control construction attempted an external side effect")

        class FakePage:
            def __init__(self):
                self.controls = []

            def add(self, *controls):
                self.controls.extend(controls)

        page = FakePage()
        with ExitStack() as stack:
            stack.enter_context(patch("builtins.__import__", guarded_import))
            for target in ("builtins.open", "os.getenv", "os.open", "os.mkdir", "os.makedirs", "os.remove",
                           "os.unlink", "os.rename", "os.replace", "os.system", "subprocess.Popen",
                           "socket.create_connection", "socket.socket.connect", "socket.socket.connect_ex"):
                stack.enter_context(patch(target, forbidden))
            stack.enter_context(patch.object(type(os.environ), "__getitem__", forbidden))
            stack.enter_context(patch.object(Path, "open", forbidden))
            stack.enter_context(patch.object(ft, "run", forbidden))
            spec.loader.exec_module(module)
            module.main(page)

        self.assertEqual(page.title, "QUANTGEN")
        self.assertEqual(page.fonts, {"QG Interface": "fonts/qg-interface.otf"})
        self.assertEqual(page.theme.font_family, "QG Interface")
        self.assertEqual(len(page.controls), 1)
        self.assertFalse(hasattr(page, "window"), "The mobile shell must not require desktop window APIs")
        pending, labels, scrolling = list(page.controls), [], False
        while pending:
            control = pending.pop()
            if isinstance(control, ft.Text):
                labels.append(control.value)
            scrolling |= getattr(control, "scroll", None) == ft.ScrollMode.AUTO
            pending.extend(getattr(control, "controls", []) or [])
            child = getattr(control, "content", None)
            if child is not None:
                pending.append(child)
        content = "\n".join(labels)
        self.assertIn("Quant Lab · Monte Carlo", content)
        self.assertIn("미제공 · 계산 및 결과 대조 미실시", content)
        self.assertIn("미제공 · 실제 데이터 미연결", content)
        self.assertIn("미제공 · 계정 연결 없음", content)
        self.assertTrue(scrolling)


if __name__ == "__main__":
    unittest.main()
